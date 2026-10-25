/*
 * test.c — the cap of Stateless Resets PER ADDRESS (src/resetcap.h, used by send_stateless_reset() in src/transport.c), audit R9 (25 Oct 2026).
 * transport.c answers a packet for a connection that does not exist with a Stateless Reset, at most 100 a second FOR EVERYBODY: one address that
 * sends short packets for unknown connection ids used the whole cap, and the clients that had really lost their connection (a restarted server)
 * got no Reset and waited out their 30 s of idle time.  Now one address may have 5 of the 100, and what it is refused is not counted globally.
 *
 * What is checked, on the REAL header (nothing copied):
 *   1. one address, 10000 attempts in one second: exactly 5 are allowed; the next second, 5 again;
 *   2. the others are not touched: that flood followed by 50 other addresses, one packet each, all allowed, and the global count (what the
 *      caller adds up from the allowed ones) is 5 + 50, not 100;
 *   3. the mutant (the old code: no per-address limit, per_address = 1000000): the same flood is allowed 10000 times;
 *   4. FIXED MEMORY: 100000 different addresses never use more than 64 entries; declared limit: an attacker with more addresses than entries
 *      gets 5 for each (the global cap of 100 a second still bounds the total);
 *   5. by reading src/transport.c (argv[1], optional): send_stateless_reset() asks reset_addr_take() before the global count and returns
 *      before `reset_count++` when it refuses; the per-address limit is not a bare constant but `t->reset_per_address` (0 = the default);
 *   5b. (rilettura M1) a SIGNED id gets at most 1 Reset a second: send_stateless_reset() asks `reset_addr_take(&t->reset_id, ..., 1)` for it
 *      before the budgets and counts what it refuses in `reset_id_refused`, written by refusals_report() like the others;
 *   6. (rilettura B4) the count of the Resets refused to an address is not zeroed every second: `refusals_report()` writes it and zeroes it,
 *      and it counts for the early return of that function and for the wake-up of `transport_wait_ns()`.
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *        -I/albero/src /albero/benches/unit/reset-cap/test.c -o test && ./test /albero/src/transport.c'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "resetcap.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

static void addr(uint8_t key[16], unsigned n)
{
	memset(key, 0, 16);
	key[10] = key[11] = 0xff;
	key[12] = 10;
	key[13] = (uint8_t)(n >> 16);
	key[14] = (uint8_t)(n >> 8);
	key[15] = (uint8_t)n;
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
	struct reset_addr *t = calloc(1, sizeof *t);
	uint8_t a[16];
	unsigned ok, global = 0;

	if (!t)
		return 2;
	/* 1 */
	addr(a, 1);
	ok = 0;
	for (int i = 0; i < 10000; i++)
		ok += reset_addr_take(t, a, 100, RESET_PER_ADDRESS);
	CHECK(ok == RESET_PER_ADDRESS, "1. one address, 10000 attempts in a second: exactly 5 allowed");
	ok = 0;
	for (int i = 0; i < 10000; i++)
		ok += reset_addr_take(t, a, 101, RESET_PER_ADDRESS);
	CHECK(ok == RESET_PER_ADDRESS, "1b. the next second, 5 again");

	/* 2 */
	free(t);
	t = calloc(1, sizeof *t);
	addr(a, 1);
	for (int i = 0; i < 10000; i++)
		global += reset_addr_take(t, a, 200, RESET_PER_ADDRESS);   /* the caller counts only what it allows */
	ok = 0;
	for (unsigned n = 2; n < 52; n++) {
		addr(a, n);
		ok += reset_addr_take(t, a, 200, RESET_PER_ADDRESS);
	}
	global += ok;
	CHECK(ok == 50 && global == RESET_PER_ADDRESS + 50, "2. after the flood, 50 other addresses are all allowed; the global count is 5 + 50");

	/* 3 */
	free(t);
	t = calloc(1, sizeof *t);
	addr(a, 1);
	ok = 0;
	for (int i = 0; i < 10000; i++)
		ok += reset_addr_take(t, a, 300, 1000000u);
	CHECK(ok == 10000, "3. mutant (no per-address limit, the old code): the flood is allowed 10000 times");

	/* 4 */
	free(t);
	t = calloc(1, sizeof *t);
	ok = 0;
	for (unsigned n = 0; n < 100000; n++) {
		addr(a, n);
		ok += reset_addr_take(t, a, 400 + n / 1000, RESET_PER_ADDRESS);
	}
	unsigned used = 0;
	for (int i = 0; i < RESET_ADDR_SLOTS; i++)
		used += t->e[i].used;
	CHECK(used <= RESET_ADDR_SLOTS && ok == 100000, "4. 100000 addresses: at most 64 entries (fixed); each address gets its first Reset (declared limit)");
	free(t);

	/* 5 */
	if (argc > 1) {
		char *s = slurp(argv[1]);

		CHECK(s != NULL, "5. transport.c can be read");
		if (s) {
			char *fn = strstr(s, "static void send_stateless_reset(");
			char *take = fn ? strstr(fn, "reset_addr_take(&t->reset_addr") : NULL;
			char *glob = fn ? strstr(fn, "if (*count >= cap)") : NULL;
			char *inc = fn ? strstr(fn, "(*count)++;") : NULL;
			CHECK(take && glob && inc && take < glob && glob < inc, "5b. the per-address check comes before the global cap and the global count");
			CHECK(take && strstr(take, "t->reset_per_address ? t->reset_per_address : RESET_PER_ADDRESS"),
			      "5c. the limit is t->reset_per_address (0 = the default), so the fuzz harness can raise it");
			if (take && glob)
				CHECK(memmem(take, (size_t)(glob - take), "return;", 7) != NULL, "5d. a refusal returns before the global count");
			if (fn) {
				char *g = strstr(fn, "if (verified) {");
				char *idt = g ? strstr(g, "reset_addr_take(&t->reset_id, idkey, second, 1)") : NULL;
				char *cnt = fn ? strstr(fn, "if (*count >= cap)") : NULL;
				CHECK(idt && cnt && idt < cnt && strstr(idt, "t->reset_id_refused++;"),
				      "5e. only for a signed id, a Reset a second per id, before the budgets, and the refusals are counted");
			}
			{
				char *rr = strstr(s, "static void refusals_report(");
				char *wk = strstr(s, "int64_t transport_wait_ns(");
				char *sr = fn;
				CHECK(rr && strstr(rr, "!t->aged && !t->token_replayed && !t->token_forgotten && !t->reset_addr_refused && !t->reset_id_refused"),
				      "6a. refusals_report() does not return early while Resets are counted as refused");
				CHECK(rr && strstr(rr, "t->reset_addr_refused,\n\t              RESET_PER_ADDRESS, t->reset_id_refused)") && strstr(rr, "\tt->reset_addr_refused = t->reset_id_refused = 0;\n"),
				      "6b. ...writes the count in the line and zeroes it after");
				CHECK(wk && strstr(wk, "t->token_forgotten || t->reset_addr_refused || t->reset_id_refused"), "6c. transport_wait_ns() wakes for it");
				char *end = sr ? strstr(sr, "\n}\n") : NULL;
				CHECK(sr && end && !memmem(sr, (size_t)(end - sr), "t->reset_addr_refused = 0;", 26),
				      "6d. the per-second rollover of send_stateless_reset() no longer zeroes it");
			}
			free(s);
		}
	}

	printf("%d checks, %d bad\n", checks, bad);
	return bad ? 1 : 0;
}
