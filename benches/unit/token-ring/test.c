/*
 * test.c — the ring of used Retry tokens against the RATE of new handshakes (src/lookup.h `lk_ring`, src/hsrate.h; transport.c TOKENS_KEPT),
 * audit R6 (25 Oct 2026): «the ring is a FIFO and forgets tokens that have not expired».  A token is remembered for RETRY_TOKEN_TIMEOUT (10 s)
 * after the connection it made; past TOKENS_KEPT (4096) connections in 10 s the oldest is forgotten early and its token could make a second
 * connection.  Since the rate of new handshakes is limited (hsrate.h) at most HS_ALL_BURST + HS_ALL_RATE × 10 = 2032 connections are born in
 * any 10 s: the ring cannot overflow with live tokens.  (A hash table with an expiry would hold the same 4096 live tokens at the limit: the
 * cure is the rate.)
 *
 * What is checked, on the REAL headers (nothing copied):
 *   1. the arithmetic: HS_ALL_BURST + HS_ALL_RATE × 10 < LK_TOKENS (what the _Static_assert of transport.c says);
 *   2. 120 simulated seconds of an attacker with a NEW address and /48 for every attempt, 10000 attempts a second: hs_take() admits them at
 *      the global rate, each admitted birth keeps its token in the ring for 10 s — NO keep() reports a live token forgotten, and in no 10 s window
 *      are there more births than the ring holds;
 *   3. a token kept is "used" for its 10 s and not a moment after (so the replay is refused while it counts, and an honest retry later is not);
 *   4. the other side, declared: with the limits raised to 1,000,000 a second (the fuzz harness does it, ops 12 and 14) 5000 births in 10 s DO
 *      make the ring forget live tokens — the branch that counts them (token_forgotten) stays reachable and covered;
 *   5. by reading src/transport.c (argv[1], optional): the _Static_assert that ties TOKENS_KEPT to the handshake rate is there.
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *        -I/albero/src /albero/benches/unit/token-ring/test.c -o test && ./test /albero/src/transport.c'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "lookup.h"
#include "hsrate.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

#define SEC 1000000000ull
#define TIMEOUT (10 * SEC)

_Static_assert(HS_ALL_BURST + HS_ALL_RATE * 10 < LK_TOKENS, "the handshake rate leaves room in the ring of used Retry tokens");

static void v6(uint8_t key[16], uint8_t key48[16], unsigned n)
{
	memset(key, 0, 16);
	key[0] = 0x20; key[1] = 0x01;
	key[2] = (uint8_t)(n >> 24); key[3] = (uint8_t)(n >> 16); key[4] = (uint8_t)(n >> 8); key[5] = (uint8_t)n;
	key[6] = (uint8_t)(n >> 12); key[7] = (uint8_t)n;
	memcpy(key48, key, 16);
	memset(key48 + 6, 0, 10);
}

static uint64_t tokhash(unsigned n)
{
	uint64_t h = 0x9e3779b97f4a7c15ull * (n + 1u);
	h ^= h >> 29;
	return h * 0xbf58476d1ce4e5b9ull;
}

/* the births an attacker can make over `seconds` simulated seconds, with the limits `l`; returns how many keep() reported a LIVE token forgotten */
static unsigned run(const struct hs_limits *l, unsigned seconds, unsigned per_second, unsigned *born_total, unsigned *max_in_10s)
{
	lk_ring *g = calloc(1, sizeof *g);
	struct hs_rate *h = calloc(1, sizeof *h);
	unsigned forgot = 0, n = 0, born = 0, cnt[600] = {0};
	uint64_t step = SEC / per_second;
	uint8_t key[16], key48[16];

	if (!g || !h)
		exit(2);
	*max_in_10s = 0;
	for (unsigned s = 0; s < seconds; s++)
		for (unsigned k = 0; k < per_second; k++) {
			uint64_t now = 1000 * SEC + (uint64_t)s * SEC + k * step;
			v6(key, key48, n++);
			if (hs_take(h, l, key, key48, now) != HS_OK)
				continue;
			born++;
			cnt[s]++;
			forgot += lk_tok_keep(g, tokhash(born), now, now + TIMEOUT);
		}
	for (unsigned s = 0; s + 10 <= seconds; s++) {
		unsigned w = 0;
		for (unsigned i = 0; i < 10; i++)
			w += cnt[s + i];
		if (w > *max_in_10s)
			*max_in_10s = w;
	}
	*born_total = born;
	free(g);
	free(h);
	return forgot;
}

int main(int argc, char **argv)
{
	struct hs_limits def = HS_LIMITS_DEFAULT, up = { 1000000, 1000000, 1000000, 1000000, 1000000, 1000000 };
	unsigned born, win, forgot;

	CHECK(HS_ALL_BURST + HS_ALL_RATE * 10 < LK_TOKENS, "1. burst + rate × 10 s is less than the ring");

	forgot = run(&def, 120, 10000, &born, &win);
	CHECK(forgot == 0, "2. 120 s of an attacker with a new address every attempt: no live token forgotten");
	CHECK(win <= HS_ALL_BURST + HS_ALL_RATE * 10 + 2 && win > HS_ALL_RATE * 9, "2b. at most about 2032 births in any 10 s, and the limit is really used");

	{
		lk_ring *g = calloc(1, sizeof *g);
		uint64_t t = 5000 * SEC;
		if (!g)
			return 2;
		lk_tok_keep(g, 0xabcdef0123456789ull, t, t + TIMEOUT);
		CHECK(lk_tok_used(g, 0xabcdef0123456789ull, t + TIMEOUT - 1), "3. a kept token is used for its 10 s");
		CHECK(!lk_tok_used(g, 0xabcdef0123456789ull, t + TIMEOUT + 1), "3b. and not a moment after");
		free(g);
	}

	forgot = run(&up, 10, 10000, &born, &win);
	CHECK(forgot > 0 && born > LK_TOKENS, "4. declared: with the limits raised, 4096+ births in 10 s DO make the ring forget live tokens");

	if (argc > 1) {
		FILE *f = fopen(argv[1], "r");
		long n;
		char *b = NULL;

		if (f) {
			fseek(f, 0, SEEK_END);
			n = ftell(f);
			rewind(f);
			b = calloc(1, (size_t)n + 1);
			if (b && fread(b, 1, (size_t)n, f) != (size_t)n)
				b[0] = 0;
			fclose(f);
		}
		CHECK(b && strstr(b, "_Static_assert(HS_ALL_BURST + HS_ALL_RATE * (RETRY_TOKEN_TIMEOUT / NGTCP2_SECONDS) < TOKENS_KEPT"),
		      "5. transport.c ties TOKENS_KEPT to the handshake rate with a _Static_assert");
		free(b);
	}

	printf("%d checks, %d bad\n", checks, bad);
	return bad ? 1 : 0;
}
