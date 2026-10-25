/*
 * test.c — the accept buckets of the page listener (src/pagebucket.h, used by src/page.c), audit R-5 (25 Oct 2026).
 * The keys are the IPv4 address / IPv6 /64 (`rcp_key_address()`) and the /48 has its own table; with ROTATING IPv6 addresses an attacker who
 * kept all 256 buckets of a table busy pushed every new address — the legitimate visitors — onto the ONE shared overflow bucket, which his own
 * further keys drained: «503 busy» for everybody.  Now the BUSY buckets of one IPv6 /32 are at most PAGE_KEYS_PER_32 (32) in a table.
 *
 * What is checked, on the REAL header (nothing copied):
 *   1. a bucket: the burst (32), then 8 a second, for an IPv4 key (nothing changed);
 *   2. 400 /64s of ONE /32 at one instant: at most 32 buckets of that /32 are in the table, the attacker's further keys share the overflow bucket,
 *      and a visitor from ANOTHER /32 still gets a bucket of its own with its full burst;
 *   3. the mutant (cap disabled = the old behaviour, bucket_of_cap with cap32 = PAGE_RATE_KEYS): the same visitor is pushed onto the overflow
 *      bucket: the test would have failed before the fix;
 *   4. the buckets the attacker stops using are idle after burst/rate seconds and are recycled: the same /32 gets a bucket of its own again;
 *   5. the residual limit, declared: 8 /32s × 32 keys fill the 256 places, and a 9th /32 then shares the overflow bucket;
 *   6. IPv4 has no group: 300 keys of one 10.1.0.0/16 fill the table as before (no cap), the 257th shares the overflow bucket;
 *   8. one overflow bucket PER FAMILY (audit R-5, line 51): with the table full, an IPv6 flood drains the IPv6 overflow bucket and the IPv4 one
 *      stays whole (a visitor on IPv4 is admitted with its burst), and the other way round;
 *   7. key_g32(): «[2001:db8:1:2::]» and «2001:0db8:0001::/48» give 20 01 0d b8; IPv4, loopback, IPv4-mapped, NAT64 and text that is not an
 *      address give none; a zone («fe80::1%eth0») is cut.
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *        -I/albero/src /albero/benches/unit/page-bucket/test.c -o test && ./test'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include <arpa/inet.h>
#include <netinet/in.h>
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define PAGE_ACCEPT_RATE 8   /* 1.5: the values of src/page.c (it was 4 / 8); `otto-utenti-nat` reads them from the source */
#define PAGE_ACCEPT_BURST 32
#define PAGE_RATE_KEYS 256
#define PAGE_KEYS_PER_32 32
#include "pagebucket.h"

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

static struct bucket tab[PAGE_RATE_KEYS], over[2];

static void reset(void)
{
	memset(tab, 0, sizeof tab);
	memset(over, 0, sizeof over);
}

static unsigned with_prefix(const char *p)
{
	unsigned n = 0;
	for (int i = 0; i < PAGE_RATE_KEYS; i++)
		n += tab[i].key[0] && strncmp(tab[i].key, p, strlen(p)) == 0;
	return n;
}

/* one connection from `key`: a token, as rate_take() does for it (the bucket and its tokens) */
static struct bucket *touch(const char *key, uint64_t now, unsigned cap32)
{
	struct bucket *b = bucket_of_cap(tab, over, key, now, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST, cap32);
	if (b->milli >= 1000u)
		b->milli -= 1000u;
	return b;
}

int main(void)
{
	const uint64_t t0 = 1000000;
	char k[48];
	struct bucket *b;
	unsigned n;
	unsigned char g[4];

	/* 1 */
	reset();
	n = 0;
	for (int i = 0; i < 2 * PAGE_ACCEPT_BURST; i++) {
		b = bucket_of(tab, over, "[10.0.0.1]", t0, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
		if (b->milli >= 1000u) {
			b->milli -= 1000u;
			n++;
		}
	}
	CHECK(n == PAGE_ACCEPT_BURST, "1. a bucket: the burst of 32");
	n = 0;
	for (int i = 0; i < 20; i++) {
		b = bucket_of(tab, over, "[10.0.0.1]", t0 + 1000, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
		if (b->milli >= 1000u) {
			b->milli -= 1000u;
			n++;
		}
	}
	CHECK(n == PAGE_ACCEPT_RATE, "1b. then 8 a second");

	/* 2 */
	reset();
	for (int i = 0; i < 400; i++) {
		snprintf(k, sizeof k, "[2001:db8:%x:%x::]", i / 200, i % 200);
		touch(k, t0, PAGE_KEYS_PER_32);
	}
	CHECK(with_prefix("[2001:db8:") == PAGE_KEYS_PER_32,
	      "2. 400 /64s of ONE /32 at one instant: exactly 32 buckets of that /32 in the table");
	b = bucket_of(tab, over, "[2001:db8:ff:ff::]", t0, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
	CHECK(b == &over[1], "2b. the attacker's further keys share the overflow bucket");
	b = bucket_of(tab, over, "[2001:db9:1:1::]", t0, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
	CHECK(b != &over[1] && b->milli == PAGE_ACCEPT_BURST * 1000u,
	      "2c. a visitor from ANOTHER /32 gets a bucket of its own, with its full burst");

	/* 3: the mutant, the cap disabled = the old behaviour */
	reset();
	for (int i = 0; i < 400; i++) {
		snprintf(k, sizeof k, "[2001:db8:%x:%x::]", i / 200, i % 200);
		touch(k, t0, PAGE_RATE_KEYS);
	}
	b = bucket_of_cap(tab, over, "[2001:db9:1:1::]", t0, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST, PAGE_RATE_KEYS);
	CHECK(b == &over[1], "3. mutant (no cap, the old code): the same visitor lands on the overflow bucket");

	/* 4 */
	reset();
	for (int i = 0; i < 100; i++) {
		snprintf(k, sizeof k, "[2001:db8:1:%x::]", i);
		touch(k, t0, PAGE_KEYS_PER_32);
	}
	b = bucket_of(tab, over, "[2001:db8:2:1::]", t0, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
	CHECK(b == &over[1], "4. (setup) the /32 is at its cap while its buckets are busy");
	b = bucket_of(tab, over, "[2001:db8:2:1::]", t0 + 4500, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
	CHECK(b != &over[1] && b->milli == PAGE_ACCEPT_BURST * 1000u, "4b. 4.5 s later (> burst/rate = 4 s) they are idle: the same /32 gets a bucket of its own again");

	/* 5 */
	reset();
	for (int g32 = 0; g32 < 8; g32++)
		for (int i = 0; i < 32; i++) {
			snprintf(k, sizeof k, "[2001:%x:1:%x::]", 0xdb8 + g32, i);
			touch(k, t0, PAGE_KEYS_PER_32);
		}
	b = bucket_of(tab, over, "[2001:dc0:1:1::]", t0, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
	CHECK(b == &over[1], "5. declared limit: 8 /32s × 32 keys fill the 256 places, a 9th /32 shares the overflow bucket");

	/* 6 */
	reset();
	for (int i = 0; i < 300; i++) {
		snprintf(k, sizeof k, "[10.1.%d.%d]", i / 200, i % 200 + 1);
		touch(k, t0, PAGE_KEYS_PER_32);
	}
	b = bucket_of(tab, over, "[10.1.9.9]", t0, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
	n = 0;
	for (int i = 0; i < PAGE_RATE_KEYS; i++)
		n += tab[i].key[0] != 0;
	CHECK(n == PAGE_RATE_KEYS && b == &over[0], "6. IPv4 has no group: 300 keys of one /16 fill the table, the next shares the overflow bucket");

	/* 7 */
	CHECK(key_g32("[2001:db8:1:2::]", g) && g[0] == 0x20 && g[1] == 0x01 && g[2] == 0x0d && g[3] == 0xb8, "7. a /64 key → 20 01 0d b8");
	CHECK(key_g32("2001:0db8:0001::/48", g) && g[2] == 0x0d && g[3] == 0xb8, "7b. a /48 key → the same /32");
	CHECK(!key_g32("[10.0.0.1]", g) && !key_g32("[::1]", g) && !key_g32("[::ffff:1.2.3.4]", g) && !key_g32("[64:ff9b::1.2.3.4]", g) &&
	      !key_g32("?", g) && !key_g32("", g) && !key_g32("*", g),
	      "7c. IPv4, loopback, IPv4-mapped, NAT64 and not-an-address: no group");
	CHECK(key_g32("[fe80::1%eth0]", g) && g[0] == 0xfe && g[1] == 0x80, "7d. a zone is cut");

	/* 8 */
	reset();
	for (int i = 0; i < PAGE_RATE_KEYS; i++) {
		snprintf(k, sizeof k, "[10.4.%d.%d]", i / 200, i % 200 + 1);
		touch(k, t0, PAGE_KEYS_PER_32);
	}
	for (int i = 0; i < 60; i++) {   /* an IPv6 flood: the table is full of busy IPv4 buckets, so every IPv6 key lands on the IPv6 overflow */
		snprintf(k, sizeof k, "[2001:%x:1:1::]", 0x1000 + i);
		touch(k, t0, PAGE_KEYS_PER_32);
	}
	CHECK(over[1].milli < 1000u, "8. (setup) the IPv6 overflow bucket is used up by the flood");
	b = bucket_of(tab, over, "[10.9.9.9]", t0, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
	CHECK(b == &over[0] && b->milli == PAGE_ACCEPT_BURST * 1000u, "8b. an IPv4 visitor still has the whole IPv4 overflow bucket");
	reset();
	for (int i = 0; i < PAGE_RATE_KEYS; i++) {
		snprintf(k, sizeof k, "[2001:%x:1:1::]", 0x2000 + i);
		touch(k, t0, PAGE_KEYS_PER_32);
	}
	for (int i = 0; i < 60; i++) {
		snprintf(k, sizeof k, "[10.5.%d.%d]", i / 200, i % 200 + 1);
		touch(k, t0, PAGE_KEYS_PER_32);
	}
	b = bucket_of(tab, over, "[2001:dd0:1:1::]", t0, PAGE_ACCEPT_RATE, PAGE_ACCEPT_BURST);
	CHECK(b == &over[1] && b->milli == PAGE_ACCEPT_BURST * 1000u, "8c. and an IPv6 visitor the whole IPv6 one, after an IPv4 flood");

	printf("%d checks, %d bad\n", checks, bad);
	return bad ? 1 : 0;
}
