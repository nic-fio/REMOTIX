/*
 * test.c — the RATE of new handshakes (src/hsrate.h, audit R4 / conto-handshake.md, 25 Oct 2026).  The caps of transport.c bound how many
 * connections are open, not how fast they come: a client that closes at once frees its place and starts again, so one address could make
 * 200-800 handshakes a second and a /48 could saturate the thread that also carries the video.  Three token buckets (per address 4/s burst 16,
 * per /48 16/s burst 32, global 200/s burst 32) are taken together after the Retry token is verified and before accept_conn().
 *
 * What is checked, on the REAL header (nothing copied):
 *   1. one address: a burst of 16, then refused («over address»); a quarter of a second later one more; sustained 1000 attempts a second for
 *      10 s let through about 16 + 4 × 10;
 *   2. a refused attempt charges NO bucket (10000 refusals from one address leave the /48 and the global buckets as they were);
 *   3. one /48 with many addresses: the /48 bucket (burst 32, 16/s) stops them, not the address buckets;
 *   4. the global bucket: 40 different /48s at the same instant, 32 pass; sustained, a new /48 every millisecond for 10 s lets through
 *      about 32 + 200 × 10;
 *   5. FIXED MEMORY and LRU: 200000 different addresses go through without the tables growing (sizeof is constant, at most
 *      HS_ADDR_SLOTS / HS_NET_SLOTS entries in use), and an address that keeps coming is NOT evicted while thousands of others pass
 *      (it stays limited, it does not get a fresh bucket);
 *   6. a clock that goes back does not crash nor give tokens;
 *   6c. the fractions of a token are kept: asked every 300 µs, a bucket of 4 a second refills 40 tokens in 10 s, not about 33 (the time that
 *      does not make a whole thousandth is not thrown away);
 *   7. by reading src/transport.c (argv[1], optional): rate_ok() is called after token_used() and before room_for() and accept_conn(),
 *      the token is kept only after accept_conn(), and the refusal is a stateless CONNECTION_REFUSED.
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *        -I/albero/src /albero/benches/unit/hs-rate/test.c -o test && ./test /albero/src/transport.c'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "hsrate.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

#define MS 1000000ull
#define SEC 1000000000ull

static const struct hs_limits LIM = HS_LIMITS_DEFAULT;

/* key of the IPv4 address a.b.c.d as address_key() writes it (::ffff:a.b.c.d); key48 = key */
static void v4(uint8_t key[16], uint8_t key48[16], int a, int b, int c, int d)
{
	memset(key, 0, 16);
	key[10] = key[11] = 0xff;
	key[12] = (uint8_t)a; key[13] = (uint8_t)b; key[14] = (uint8_t)c; key[15] = (uint8_t)d;
	memcpy(key48, key, 16);
}

/* an IPv6 /64 `net`:`sub` (key = the first 8 bytes) inside the /48 `net` (key48 = the first 6 bytes) */
static void v6(uint8_t key[16], uint8_t key48[16], unsigned net, unsigned sub)
{
	memset(key, 0, 16);
	key[0] = 0x20; key[1] = 0x01; key[2] = (uint8_t)(net >> 8); key[3] = (uint8_t)net; key[4] = (uint8_t)(net >> 16);
	key[5] = (uint8_t)(net >> 24);
	key[6] = (uint8_t)(sub >> 8); key[7] = (uint8_t)sub;
	memcpy(key48, key, 16);
	memset(key48 + 6, 0, 10);
}

static struct hs_rate *fresh(void)
{
	struct hs_rate *h = calloc(1, sizeof *h);
	if (!h)
		exit(2);
	return h;
}

static char *slurp(const char *path)
{
	FILE *f = fopen(path, "r");
	long n;
	char *b;

	if (!f)
		return NULL;
	fseek(f, 0, SEEK_END);
	n = ftell(f);
	rewind(f);
	b = calloc(1, (size_t)n + 1);
	if (b && fread(b, 1, (size_t)n, f) != (size_t)n)
		b[0] = 0;
	fclose(f);
	return b;
}

int main(int argc, char **argv)
{
	uint8_t k[16], k48[16], o[16], o48[16];
	struct hs_rate *h;
	unsigned ok;
	uint64_t t0 = 100 * SEC;

	/* 1 */
	h = fresh();
	v4(k, k48, 192, 0, 2, 10);
	ok = 0;
	for (int i = 0; i < HS_ADDR_BURST; i++)
		ok += hs_take(h, &LIM, k, k48, t0) == HS_OK;
	CHECK(ok == HS_ADDR_BURST, "1. a burst of 16 from one address goes through");
	CHECK(hs_take(h, &LIM, k, k48, t0) == HS_OVER_ADDRESS, "1b. the 17th is refused (over address)");
	CHECK(hs_take(h, &LIM, k, k48, t0 + 100 * MS) == HS_OVER_ADDRESS, "1c. 100 ms later still not (0.4 of a token)");
	CHECK(hs_take(h, &LIM, k, k48, t0 + 260 * MS) == HS_OK, "1d. 260 ms later one more passes (4 a second)");
	free(h);
	h = fresh();
	ok = 0;
	for (int i = 0; i < 10000; i++)
		ok += hs_take(h, &LIM, k, k48, t0 + (uint64_t)i * 1 * MS) == HS_OK;
	CHECK(ok >= HS_ADDR_BURST + 4 * 10 - 2 && ok <= HS_ADDR_BURST + 4 * 10 + 2, "1e. 1000 attempts a second for 10 s: about 16 + 40 pass");
	free(h);

	/* 2 */
	h = fresh();
	for (int i = 0; i < HS_ADDR_BURST; i++)
		hs_take(h, &LIM, k, k48, t0);
	for (int i = 0; i < 10000; i++)
		hs_take(h, &LIM, k, k48, t0);
	CHECK(h->all.milli == (uint64_t)(HS_ALL_BURST - HS_ADDR_BURST) * 1000u, "2. 10000 refusals left the global bucket at 32 - 16 tokens");
	free(h);

	/* 3: one /48, 6 different /64s, each asking for 8 */
	h = fresh();
	ok = 0;
	unsigned over_net = 0;
	for (unsigned sub = 0; sub < 6; sub++) {
		v6(o, o48, 0x0db8, sub);
		for (int i = 0; i < HS_ADDR_BURST; i++) {
			int r = hs_take(h, &LIM, o, o48, t0);
			ok += r == HS_OK;
			over_net += r == HS_OVER_NET;
		}
	}
	CHECK(ok == HS_NET_BURST && over_net == 6 * HS_ADDR_BURST - HS_NET_BURST, "3. one /48 with 6 addresses: the /48 bucket lets 32 through, no more");
	free(h);

	/* 4 */
	h = fresh();
	ok = 0;
	unsigned over_all = 0;
	for (unsigned i = 0; i < 40; i++) {
		v6(o, o48, 0x1000 + i, 0);
		int r = hs_take(h, &LIM, o, o48, t0);
		ok += r == HS_OK;
		over_all += r == HS_OVER_ALL;
	}
	CHECK(ok == HS_ALL_BURST && over_all == 40 - HS_ALL_BURST, "4. 40 different /48s at one instant: the global bucket lets 32 through");
	free(h);
	h = fresh();
	ok = 0;
	for (unsigned i = 0; i < 10000; i++) {
		v6(o, o48, 0x2000 + i, 0);
		ok += hs_take(h, &LIM, o, o48, t0 + (uint64_t)i * MS) == HS_OK;
	}
	CHECK(ok >= 32 + HS_ALL_RATE * 10 - 3 && ok <= 32 + HS_ALL_RATE * 10 + 3, "4b. a new /48 every ms for 10 s: about 32 + 2000 pass");
	free(h);

	/* 5 */
	h = fresh();
	v4(k, k48, 192, 0, 2, 99);
	for (int i = 0; i < HS_ADDR_BURST; i++)
		hs_take(h, &LIM, k, k48, t0);
	unsigned refused_after = 0, calls = 0;
	for (unsigned i = 0; i < 200000; i++) {
		v6(o, o48, 0x3000 + i, i & 0xffff);
		hs_take(h, &LIM, o, o48, t0);
		if (i % 50 == 0) {   /* the address that keeps coming */
			calls++;
			refused_after += hs_take(h, &LIM, k, k48, t0) == HS_OVER_ADDRESS;
		}
	}
	CHECK(refused_after == calls, "5. an address that keeps coming is not evicted by 200000 others: it stays limited");
	unsigned used_a = 0, used_n = 0;
	for (int i = 0; i < HS_ADDR_SLOTS; i++)
		used_a += h->addr[i].used;
	for (int i = 0; i < HS_NET_SLOTS; i++)
		used_n += h->net[i].used;
	CHECK(used_a <= HS_ADDR_SLOTS && used_n <= HS_NET_SLOTS && sizeof *h < 32 * 1024,
	      "5b. the tables are fixed (256 + 128 slots, under 32 KB), nothing grew");
	free(h);

	/* 6 */
	h = fresh();
	v4(k, k48, 192, 0, 2, 7);
	for (int i = 0; i < HS_ADDR_BURST; i++)
		hs_take(h, &LIM, k, k48, t0);
	CHECK(hs_take(h, &LIM, k, k48, t0 - 5 * SEC) == HS_OVER_ADDRESS, "6. a clock that goes back gives no tokens");
	CHECK(hs_take(h, &LIM, k, k48, t0 - 5 * SEC + 300 * MS) == HS_OK, "6b. and from the new instant the bucket fills again");
	free(h);
	/* 6c: the fractions of a token are not thrown away */
	{
		struct hs_limits lone = { 4, 16, 1000, 1000, 100000, 1000 };   /* only the address bucket matters */
		uint64_t t = 500 * SEC;
		unsigned n = 0, drain = 0;

		h = fresh();
		v4(k, k48, 192, 0, 2, 33);
		while (hs_take(h, &lone, k, k48, t) == HS_OK)
			drain++;
		for (int i = 1; i <= 33333; i++)   /* every 300 us for about 10 s */
			n += hs_take(h, &lone, k, k48, t + (uint64_t)i * 300000u) == HS_OK;
		CHECK(drain == 16 && n >= 38 && n <= 41, "6c. asked every 300 us for 10 s, a bucket of 4 a second refills about 40 tokens (not about 33)");
		free(h);
	}

	/* 7 */
	if (argc > 1) {
		char *t = slurp(argv[1]);
		if (!t) {
			CHECK(0, "7. transport.c can be read");
		} else {
			char *used = strstr(t, "token_used(t, token, now_ns())");
			char *rate = strstr(t, "if (!rate_ok(t, &hd, remote, remotelen))");
			char *room = strstr(t, "if (!room_for(t, &hd, remote, remotelen, &victim))");
			char *acc = strstr(t, "c = accept_conn(t, &hd, &odcid, local, localelen, remote, remotelen);");
			char *keep = strstr(t, "token_keep(t, token, c->born);");
			CHECK(used && rate && room && acc && keep && used < rate && rate < room && room < acc && acc < keep,
			      "7. rate_ok() runs after token_used(), before room_for() and accept_conn(); the token is kept only after accept_conn()");
			char *fn = strstr(t, "static bool rate_ok(");
			CHECK(fn && strstr(fn, "NGTCP2_CONNECTION_REFUSED") && strstr(fn, "hs_take(&t->hs, &t->hs_lim"),
			      "7b. the refusal is a stateless CONNECTION_REFUSED, decided by hs_take() with the transport's own limits");
			CHECK(strstr(t, "t->hs_over_address, t->hs_lim.addr_rate, t->hs_over_net, t->hs_lim.net_rate, t->hs_over_all"),
			      "7c. the HANDSHAKE RATE line gives the count first and then the rate, for each of the three");
			CHECK(strstr(t, "t->hs_lim = (struct hs_limits)HS_LIMITS_DEFAULT;"), "7d. the limits start at the product's defaults");
			free(t);
		}
	}

	printf("%d checks, %d bad\n", checks, bad);
	return bad ? 1 : 0;
}
