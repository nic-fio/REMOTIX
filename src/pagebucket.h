/* pagebucket.h — the accept buckets of the page listener (page.c), apart so that benches/unit/page-bucket tests them alone.
 *
 * ⚠ Included by page.c AFTER its constants: the caller defines PAGE_RATE_KEYS (the size of each table) and PAGE_KEYS_PER_32 (R-5: at most this
 *   many BUSY buckets for one IPv6 /32 in a table).  Header only; needs <stdint.h>, <stdbool.h>, <string.h>, <stdio.h>, <arpa/inet.h>,
 *   <netinet/in.h>. */
#ifndef REMOTIX_PAGEBUCKET_H
#define REMOTIX_PAGEBUCKET_H

/* ⭐ R-5: the shared overflow bucket is one per FAMILY, `over[0]` for IPv4 keys and `over[1]` for IPv6 ones (a key with a colon), so an IPv6 flood cannot
 * use up the overflow of the IPv4 visitors, and the other way round (audit R-5, line 51: «un secchio condiviso per famiglia»). */
#define BUCKET_IS_OVER(over, b) ((b) == &(over)[0] || (b) == &(over)[1])

/* One token bucket: `milli` thousandths of a token at the instant `at`. */
struct bucket {
	char key[64];
	uint64_t at;
	unsigned milli;
	/* R-5: the IPv6 /32 of the key (`has32` false for IPv4 and for what is not a global IPv6 address) */
	unsigned char g32[4];
	bool has32;
};

/* R-5: the IPv6 /32 of a bucket key: «[2001:db8:1:2::]» (a /64) or «2001:0db8:0001::/48».  False for IPv4, loopback, IPv4-mapped / NAT64 and
 * anything that does not parse: those have no group. */
static bool key_g32(const char *key, unsigned char g32[4])
{
	char tmp[64];
	const char *s = key;
	size_t n;
	struct in6_addr a;
	static const unsigned char nat64[12] = {0, 0x64, 0xff, 0x9b};

	if (*s == '[')
		s++;
	n = strcspn(s, "]/%");
	if (n == 0 || n >= sizeof tmp)
		return false;
	memcpy(tmp, s, n);
	tmp[n] = 0;
	if (inet_pton(AF_INET6, tmp, &a) != 1 || IN6_IS_ADDR_V4MAPPED(&a) || IN6_IS_ADDR_LOOPBACK(&a) ||
	    memcmp(a.s6_addr, nat64, sizeof nat64) == 0)
		return false;
	memcpy(g32, a.s6_addr, 4);
	return true;
}

/* A bucket that can be forgotten: unused, or refilled to its burst (forgetting it forgets nothing). */
static bool bucket_idle(const struct bucket *x, uint64_t now, unsigned cap, unsigned rate)
{
	return !x->key[0] || (now >= x->at && (now - x->at >= (uint64_t)cap / rate ||
	                                       x->milli + (now - x->at) * rate >= cap));
}

/* The bucket of `key` in `t`, refilled to `now` (`rate` per second up to a
 * burst of `burst`).  A key without one gets a bucket only if some bucket is
 * FULL (refilled to the burst: forgetting it forgets nothing) or empty;
 * otherwise it is charged to `over`, ONE bucket shared by every such key —
 * so rotating more addresses than buckets buys no fresh bursts. */
static struct bucket *bucket_of_cap(struct bucket *t, struct bucket *over2,
                                    const char *key, uint64_t now, unsigned rate,
                                    unsigned burst, unsigned cap32)
{
	struct bucket *b = NULL, *free_one = NULL;
	unsigned cap = burst * 1000u, busy32 = 0;
	unsigned char g32[4];
	bool has32 = key_g32(key, g32);

	for (size_t i = 0; i < PAGE_RATE_KEYS; i++) {
		struct bucket *x = &t[i];
		if (x->key[0] && strcmp(x->key, key) == 0) {
			b = x;
			break;
		}
		if (bucket_idle(x, now, cap, rate)) {
			if (!free_one)
				free_one = x;
		} else if (has32 && x->has32 && memcmp(x->g32, g32, 4) == 0) {
			busy32++;
		}
	}
	/* ⭐ R-5: a /32 that already holds PAGE_KEYS_PER_32 busy buckets gets no more: its next keys share the overflow bucket */
	if (!b && free_one && has32 && busy32 >= cap32)
		free_one = NULL;
	if (!b && free_one) {
		b = free_one;
		snprintf(b->key, sizeof b->key, "%s", key);
		b->milli = cap;
		b->at = now;
		b->has32 = has32;
		if (has32)
			memcpy(b->g32, g32, 4);
	}
	if (!b) {
		struct bucket *over = &over2[strchr(key, ':') ? 1 : 0];

		b = over;
		if (!b->key[0]) {
			snprintf(b->key, sizeof b->key, "*");
			b->milli = cap;
			b->at = now;
		}
	}
	if (now > b->at) {
		/* ⚠ only forward: a clock that went back refills nothing */
		uint64_t d = now - b->at;
		uint64_t m = d >= (uint64_t)cap / rate ? cap : (uint64_t)b->milli + d * rate;
		b->milli = m > cap ? cap : (unsigned)m;
		b->at = now;
	}
	return b;
}

static struct bucket *bucket_of(struct bucket *t, struct bucket *over2, const char *key, uint64_t now,
                                unsigned rate, unsigned burst)
{
	return bucket_of_cap(t, over2, key, now, rate, burst, PAGE_KEYS_PER_32);
}

#endif
