/*
 * test.c — the budget of log lines per time window (src/linebudget.h), audit of 25 Oct 2026, R8 and R12.
 * A stranger can provoke some log lines before any login, at the rate of his packets, and journald answers a flood by dropping lines,
 * the legitimate ones too: the «packet … NOT sent» line of send_from() had no limit (one source against a full socket buffer = one line
 * per failed reply), and the per-address budgets of prelogin_may_log() give a fresh budget to every new address.  The global budgets
 * are the same idea as BIRTH_LINES / closes_report(): the first `burst` lines of a window are written, the rest are counted, and
 * the end of the window says how many.
 *
 * What is checked, on the REAL header (nothing copied):
 *   1. a flood of 100000 lines in one window: exactly `burst` are written, the rest counted;
 *   2. the end of the window gives the count once (hidden, written, the value left in `err`) and the next window starts again;
 *   3. a quiet window gives no summary; an exact-burst window gives none either (nothing hidden);
 *   4. a periodic flush with no line asking closes a window that has ended (the summary does not wait for the next line);
 *   5. the bound: 1,000,000 lines spread over 100 windows are at most 100 × burst written;
 *   6. a clock that goes back starts a new window and does not crash, a counter that would overflow stops at the maximum;
 *   7. the units are the caller's: the same logic in nanoseconds (transport.c) and milliseconds (webtransport.c);
 *   8. by reading the sources (argv[1] = src/transport.c, argv[2] = src/webtransport.c, optional): send_from() writes the «NOT sent»
 *      line only through line_budget_take(); prelogin_may_log() takes from the global budget before it allows a line, and the
 *      evicted keys' summaries go through it too.
 *
 * BUILD AND RUN (a second; nothing under /media/REMOTIX-15 is written; run from the root of the tree):
 *   nice -n 19 ionice -c3 podman run --rm --network=none --cpus=1 --memory=512m -v "$PWD:/albero:ro" localhost/remotix-fuzz sh -c '
 *     cd /tmp && clang -g -O1 -fsanitize=address,undefined -fno-sanitize-recover=undefined -std=gnu11 -D_GNU_SOURCE -Wall -Wextra \
 *        -I/albero/src /albero/benches/unit/line-budget/test.c -o test && ./test /albero/src/transport.c /albero/src/webtransport.c'
 * Exit code 0 = every check passed, 1 = a check failed.
 */
#include "linebudget.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int checks, bad;
#define CHECK(c, what) do { checks++; if (!(c)) { bad++; printf("FAIL: %s\n", what); } } while (0)

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
	const uint64_t W = 10;      /* any unit */
	struct line_budget b;
	struct line_budget_closed c;
	unsigned yes = 0;

	/* 1 */
	memset(&b, 0, sizeof b);
	for (int i = 0; i < 100000; i++)
		yes += line_budget_take(&b, 1000 + (uint64_t)i % 5, W, 5, &c);
	CHECK(yes == 5 && b.written == 5 && b.hidden == 99995, "1. a flood of 100000 lines: 5 written, 99995 counted");
	CHECK(c.hidden == 0, "1b. the first window closed nothing");

	/* 2 */
	b.err = 7;
	CHECK(line_budget_take(&b, 1000 + W + 1, W, 5, &c) && c.hidden == 99995 && c.written == 5 && c.err == 7,
	      "2. the end of the window: one summary with the count, the lines written and the error left by the caller");
	CHECK(b.written == 1 && b.hidden == 0, "2b. the next window starts again (this line is its first)");

	/* 3 */
	memset(&b, 0, sizeof b);
	for (int i = 0; i < 5; i++)
		line_budget_take(&b, 100, W, 5, &c);
	line_budget_take(&b, 100 + W, W, 5, &c);
	CHECK(c.hidden == 0 && c.written == 5, "3. a window of exactly `burst` lines has nothing to report");
	line_budget_take(&b, 100 + 3 * W, W, 5, &c);
	CHECK(c.hidden == 0, "3b. a quiet window has no summary");

	/* 4 */
	memset(&b, 0, sizeof b);
	for (int i = 0; i < 9; i++)
		line_budget_take(&b, 50, W, 5, &c);
	line_budget_flush(&b, 55, W, &c);
	CHECK(c.hidden == 0, "4. a flush inside the window closes nothing");
	line_budget_flush(&b, 50 + W, W, &c);
	CHECK(c.hidden == 4 && c.written == 5, "4b. a flush after the window gives the summary without any line asking");
	line_budget_flush(&b, 50 + W, W, &c);
	CHECK(c.hidden == 0, "4c. and only once");

	/* 5 */
	memset(&b, 0, sizeof b);
	yes = 0;
	for (int i = 0; i < 1000000; i++)
		yes += line_budget_take(&b, 1000 + (uint64_t)(i / 10000) * W, W, 5, &c);
	CHECK(yes <= 100 * 5 && yes >= 99 * 5, "5. 1,000,000 lines over 100 windows: at most 500 written (5 per window)");

	/* 6 */
	memset(&b, 0, sizeof b);
	line_budget_take(&b, 5000, W, 2, &c);
	line_budget_take(&b, 5001, W, 2, &c);
	CHECK(!line_budget_take(&b, 5002, W, 2, &c), "6. (setup) the third line of the window is counted");
	CHECK(line_budget_take(&b, 10, W, 2, &c) && c.hidden == 1, "6b. a clock that goes back starts a new window");
	b.hidden = ~0u;
	line_budget_take(&b, 10, W, 0, &c);
	CHECK(b.hidden == ~0u, "6c. the counter stops at the maximum instead of wrapping");

	/* 7 */
	{
		const uint64_t WN = 10ull * 1000000000ull;      /* 10 s in nanoseconds */
		memset(&b, 0, sizeof b);
		yes = 0;
		for (int i = 0; i < 1000; i++)
			yes += line_budget_take(&b, 3000000000ull + (uint64_t)i * 1000000ull, WN, 5, &c);
		CHECK(yes == 5, "7. nanoseconds: 1000 lines in one second, 5 written");
		CHECK(line_budget_take(&b, 3000000000ull + WN + 1, WN, 5, &c) && c.hidden == 995, "7b. ...and 995 in the summary 10 s later");
	}

	/* 8 */
	if (argc > 1) {
		char *t = slurp(argv[1]);
		const char *p;

		CHECK(t != NULL, "8. transport.c can be read");
		if (t) {
			p = strstr(t, "static void send_from(");
			CHECK(p && strstr(p, "line_budget_take(&t->send_fail"), "8a. send_from() takes from the send_fail budget");
			CHECK(!strstr(t, "registro_dice(REG_QUIC, \"packet of %zu bytes NOT sent: %s\", len,\n\t\t              strerror(err));"),
			      "8b. no bare, unlimited «NOT sent» line is left");
			CHECK(strstr(t, "send_fail_report(t, now);"), "8c. the periodic call that closes the window is in place");
			CHECK(strstr(t, "t->send_fail.hidden && t->send_fail.start + REFUSAL_LOG_S * NGTCP2_SECONDS < before"),
			      "8c2. transport_wait_ns() arms the timer for the send_fail window");
			CHECK(strstr(t, "wt_prelogin_flush(now / 1000000ull);") && strstr(t, "wt_prelogin_expiry_ms()"),
			      "8c3. transport_expired() flushes the pre-login budget and transport_wait_ns() waits for it");
			free(t);
		}
	}
	if (argc > 2) {
		char *w = slurp(argv[2]);
		const char *p;

		CHECK(w != NULL, "8d. webtransport.c can be read");
		if (w) {
			p = strstr(w, "static bool prelogin_may_log(");
			CHECK(p && strstr(p, "prelogin_all_may(now)"), "8e. prelogin_may_log() takes from the global budget");
			p = strstr(w, "static void prelogin_summary(");
			CHECK(p && strstr(p, "prelogin_all_may(now)") && strstr(p, "prelogin_folded"),
			      "8f. the summaries of evicted keys go through the global budget, and are not lost");
			free(w);
		}
	}

	printf("%d checks, %d bad\n", checks, bad);
	return bad ? 1 : 0;
}
