/*
 * test.c — the backoff after an encoder DIED (src/encbackoff.h), audit of 25 Oct 2026, E-R1, review.
 * A fake encoder that dies at its first frame every time it is made (the permanent cause) is run through the same bookkeeping child.c does
 * (a death counter per codec; reset only by a frame really sent) and the time between two creations is recorded.  What is checked:
 *   1. the waits double 500, 1000, 2000, 4000, 8000 and stop at 10000 ms; never above the maximum, however many deaths;
 *   2. in 1000 simulated seconds a permanently dying encoder is made at most ~105 times (was 2000: every 500 ms) and the interval reaches 10 s;
 *   3. a frame sent resets the count: the next death waits the minimum again; a creation that does not send a frame does NOT reset it;
 *   4. two codecs have separate counters;
 *   5. the arithmetic does not overflow for an absurd number of deaths;
 *   6. by reading src/child.c (argv[1], optional): encoder_drop_if_dead() uses enc_death_wait_ms() and a per-codec counter that is cleared only
 *      after a frame was sent (the old doubling of enc_wait_ms is gone from it).
 *
 * BUILD AND RUN (a second; run from the root of the tree):
 *   gcc -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *      -Isrc benches/unit/enc-backoff/test.c -o /tmp/enc-backoff && /tmp/enc-backoff src/child.c
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "encbackoff.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MIN_MS 500u
#define MAX_MS 10000u

static int failures, passed;

static void check(int cond, const char *what)
{
	printf("    %s  %s\n", cond ? "OK" : "NO", what);
	if (cond)
		passed++;
	else
		failures++;
}

/* the fake: what child.c does around encoder_of() / a failed frame / a sent frame, for 2 codecs */
static unsigned deaths[2];
static uint64_t retry_ms[2];

static void drop_dead(int nr, uint64_t now)
{
	deaths[nr]++;
	retry_ms[nr] = now + enc_death_wait_ms(deaths[nr], MIN_MS, MAX_MS);
}

int main(int argc, char **argv)
{
	uint64_t expect[] = { 500, 1000, 2000, 4000, 8000, 10000, 10000 };
	int ok = 1;
	unsigned n_made = 0;
	uint64_t now, last_made = 0, max_gap = 0;

	for (unsigned i = 0; i < 7; i++)
		ok &= enc_death_wait_ms(i + 1, MIN_MS, MAX_MS) == expect[i];
	check(ok, "waits: 500, 1000, 2000, 4000, 8000, then 10000 and 10000");
	check(enc_death_wait_ms(1000000, MIN_MS, MAX_MS) == MAX_MS && enc_death_wait_ms(0, MIN_MS, MAX_MS) == MIN_MS, "an absurd count stays at the maximum, zero at the minimum");

	/* permanent cause: made, dies at its first frame, again... */
	memset(deaths, 0, sizeof deaths);
	memset(retry_ms, 0, sizeof retry_ms);
	for (now = 0; now < 1000 * 1000; now += 10) {
		if (now < retry_ms[0])
			continue; /* encoder_of() says no */
		n_made++; /* made … and the first frame fails: dead */
		if (last_made && now - last_made > max_gap)
			max_gap = now - last_made;
		last_made = now;
		drop_dead(0, now);
	}
	printf("    (made %u times in 1000 s, longest gap %llu ms)\n", n_made, (unsigned long long)max_gap);
	check(n_made <= 110 && n_made >= 95, "a permanently dying encoder is made ~105 times in 1000 s, not 2000 (every 500 ms)");
	check(max_gap >= MAX_MS && max_gap <= MAX_MS + 10, "the gap between creations reaches 10 s");

	/* a creation without a frame sent does not reset; a frame sent does */
	memset(deaths, 0, sizeof deaths);
	drop_dead(0, 0);
	drop_dead(0, 1000);
	drop_dead(0, 3000);
	check(deaths[0] == 3 && retry_ms[0] == 3000 + 2000, "three deaths in a row: the third waits 2000 ms (count 3 → 2000)");
	deaths[0] = 0; /* a frame was sent */
	drop_dead(0, 100000);
	check(retry_ms[0] == 100000 + MIN_MS, "after a frame sent the next death waits the minimum again");

	memset(deaths, 0, sizeof deaths);
	drop_dead(0, 0);
	drop_dead(0, 0);
	drop_dead(1, 0);
	check(retry_ms[0] == 1000 && retry_ms[1] == 500, "two codecs have separate counters");

	if (argc > 1) {
		FILE *f = fopen(argv[1], "rb");
		long n;
		char *b, *a, *e;

		if (!f) {
			printf("    --  (cannot read %s: source check skipped)\n", argv[1]);
		} else {
			fseek(f, 0, SEEK_END);
			n = ftell(f);
			fseek(f, 0, SEEK_SET);
			b = calloc(1, (size_t)n + 1);
			if (b && fread(b, 1, (size_t)n, f) == (size_t)n) {
				a = strstr(b, "static void encoder_drop_if_dead(");
				e = a ? strstr(a, "\n}\n") : NULL;
				check(a && e, "child.c has encoder_drop_if_dead()");
				if (a && e) {
					*e = 0;
					check(strstr(a, "enc_death_wait_ms(") != NULL && strstr(a, "enc_death[nr]++") != NULL,
					      "it uses enc_death_wait_ms() and a per-codec death counter");
					check(strstr(a, "enc_wait_ms[nr] * 2") == NULL, "it no longer doubles enc_wait_ms (reset by every successful creation)");
					*e = '\n';
				}
				check(strstr(b, "enc_death[nr] = 0;") != NULL, "the counter is cleared in one place (after a frame was sent)");
			}
			free(b);
			fclose(f);
		}
	}
	printf("\n  %d passed, %d failed\n", passed, failures);
	return failures ? 1 : 0;
}
