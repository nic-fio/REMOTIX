/* linebudget.h — a BUDGET OF LOG LINES per time window, one counter for the whole process (audit of 25 Oct 2026, R8 and R12).
 *
 * ⛔ Why: some lines can be provoked by a stranger BEFORE any login, at the rate of his packets, and journald answers a flood
 *    by dropping lines — the legitimate ones too.  The per-address budgets (`prelogin_may_log()`: 20 lines every 10 s for each of 128
 *    addresses) do not bound that: an attacker with many addresses, or a /48 of IPv6 /64 keys, gets a fresh budget for each, and the
 *    «NOT sent» line of send_from() had no budget at all (one source flooding Initials against a full socket buffer wrote one line per
 *    failed reply: the packet rate).  This is the same idea as BIRTH_LINES / closes_report() of transport.c: the first `burst`
 *    lines of every window are written, the rest are COUNTED, and when the window ends ONE line says how many were not.
 *
 * It is a header with static inline functions and no dependency (no log, no clock): the caller passes `now` in whatever unit its
 * window is in (transport.c: nanoseconds, webtransport.c: milliseconds), so `benches/unit/line-budget` tests the logic alone.
 *
 * Use: `ok = line_budget_take(&b, now, window, burst, &closed)`; write the line if `ok`; if `closed.hidden` is not zero, the window
 * that has just ended hid that many lines (`closed.written` were written, `closed.err` is the value the caller left in `b->err` for the
 * last hidden one): write the summary.  `line_budget_flush()` does only the second part, for a periodic call when no line is asking. */
#ifndef REMOTIX_LINEBUDGET_H
#define REMOTIX_LINEBUDGET_H

#include <stdbool.h>
#include <stdint.h>

struct line_budget {
	uint64_t start;   /* start of the current window */
	unsigned written; /* lines written in it */
	unsigned hidden;  /* lines counted and not written in it */
	int err;          /* free for the caller: e.g. the errno of the last hidden line */
};

struct line_budget_closed {
	unsigned written, hidden;
	int err;
};

/* Closes the window if `now` is past it (or the clock went back): the old counters go to `closed`, the budget starts again. */
static inline void line_budget_flush(struct line_budget *b, uint64_t now, uint64_t window, struct line_budget_closed *closed)
{
	closed->written = closed->hidden = 0;
	closed->err = 0;
	if (now < b->start || now - b->start >= window) {
		closed->written = b->written;
		closed->hidden = b->hidden;
		closed->err = b->err;
		b->start = now;
		b->written = 0;
		b->hidden = 0;
	}
}

/* A line wants to be written at `now`.  true = write it; false = it is counted (and must not be written). */
static inline bool line_budget_take(struct line_budget *b, uint64_t now, uint64_t window, unsigned burst,
                                    struct line_budget_closed *closed)
{
	line_budget_flush(b, now, window, closed);
	if (b->written < burst) {
		b->written++;
		return true;
	}
	if (b->hidden != ~0u)
		b->hidden++;
	return false;
}

#endif
