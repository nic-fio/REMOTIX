/* msgrate.h — a TOKEN BUCKET per client and per kind of message, for what a LOGGED-IN client can send as often as it likes
 * (audit of 25 Oct 2026, parts P/Q: «no frequency ceiling on valid messages»).
 *
 * ⛔ Why: after login every message that passes the checks does work in the ONE thread of the main loop, shared by all the users, and
 *    most of them also write a log line.  A client with a valid password (or a modified page) could send them as fast as the link
 *    carries them: the per-address limits of the pre-login phase do not apply any more, and the credit of the flow control reopens at
 *    once.  Nothing here changes what a person at a keyboard can do: the rates are WIDE (see `msg_class_rate()`), a message over them is
 *    DROPPED (consumed, not executed) and COUNTED, and ONE line per 10 s window says how many were dropped and how many log lines were
 *    not written, instead of one line per message.
 *
 * ⚠ Only for messages that can be dropped without leaving the protocol in a state the client does not expect: the five input types
 *    (the id of an input only has to GROW, so a gap is legitimate, RCP.md §7.3) and the control requests REQUEST_KEY, PACE, VIEW,
 *    LAYOUT, and FIT_CANVAS (this one is ANSWERED NOT_NOW instead of dropped: §7.1 wants a CANVAS for each).  NOT the clipboard (a lost ANNOUNCE would make the next ASK a violation) and NOT the handshake.
 *
 * A header with static inline functions and no dependency (no log, no clock): the caller passes `now_ms`, so that
 * `benches/unit/msg-rate` tests the logic alone. */
#ifndef REMOTIX_MSGRATE_H
#define REMOTIX_MSGRATE_H

#include <stdbool.h>
#include <stdint.h>

/* The kinds that have a bucket. */
enum msg_class {
	MC_POINTER,
	MC_BUTTON,
	MC_WHEEL,
	MC_LETTER,
	MC_KEY_POSITION,
	MC_REQUEST_KEY,
	MC_PACE,
	MC_VIEW,
	MC_LAYOUT,
	MC_FIT_CANVAS,
	MC_COUNT
};

#define MSG_WINDOW_MS 10000u /* the window of the summary line and of the per-window log lines */
#define MSG_LINES_PER_WINDOW 10u /* log lines of ONE kind written per window; the rest are counted */

struct msg_gate {
	bool started;
	uint64_t refilled_ms; /* last refill */
	uint64_t tokens;      /* thousandths of a message */
	uint64_t window_ms;   /* start of the current window */
	unsigned lines;       /* log lines written in it */
	unsigned hidden;      /* log lines not written in it */
	unsigned dropped;     /* messages refused in it */
};

struct msg_gate_closed {
	unsigned dropped, hidden;
};

/* Sustained rate (per second) and burst (messages) of each kind.  WIDE on purpose: far above what a hand can do (a gaming mouse at
 * 1000 Hz is 1000 events a second, a key held down repeats 30 times a second), so no person ever meets them.  LAYOUT: a keyboard
 * layout is changed by a shortcut a few times in a row at most; every accepted one replaces a keymap in the compositor. */
static inline void msg_class_rate(enum msg_class c, unsigned *per_s, unsigned *burst)
{
	switch (c) {
	case MC_POINTER:      *per_s = 2000; *burst = 4000; break;
	case MC_BUTTON:       *per_s = 200;  *burst = 400;  break;
	case MC_WHEEL:        *per_s = 1000; *burst = 2000; break;
	case MC_LETTER:       *per_s = 400;  *burst = 800;  break;
	case MC_KEY_POSITION: *per_s = 400;  *burst = 800;  break;
	case MC_REQUEST_KEY:  *per_s = 50;   *burst = 100;  break;
	case MC_PACE:         *per_s = 100;  *burst = 200;  break;
	case MC_VIEW:         *per_s = 100;  *burst = 200;  break;
	case MC_LAYOUT:       *per_s = 5;    *burst = 20;   break;
	case MC_FIT_CANVAS:   *per_s = 60;   *burst = 180;  break;
	default:              *per_s = 100;  *burst = 200;  break;
	}
}

/* Closes the window if `now_ms` is past it (or the clock went back): the counters go to `closed`, the window starts again. */
static inline void msg_gate_flush(struct msg_gate *g, uint64_t now_ms, struct msg_gate_closed *closed)
{
	closed->dropped = closed->hidden = 0;
	if (!g->started || now_ms < g->window_ms || now_ms - g->window_ms >= MSG_WINDOW_MS) {
		closed->dropped = g->dropped;
		closed->hidden = g->hidden;
		g->window_ms = now_ms;
		g->lines = g->hidden = g->dropped = 0;
	}
}

/* A message of this kind arrived at `now_ms`.  true = go on and do it; false = over the rate: it is counted and must be consumed
 * without effect.  `closed` is filled when the call closed a window (write the summary if it is not empty). */
static inline bool msg_gate_admit(struct msg_gate *g, uint64_t now_ms, unsigned per_s, unsigned burst,
                                  struct msg_gate_closed *closed)
{
	uint64_t cap = (uint64_t)burst * 1000u;

	msg_gate_flush(g, now_ms, closed);
	if (!g->started) {
		g->started = true;
		g->tokens = cap; /* a new session starts with a full bucket */
		g->refilled_ms = now_ms;
	} else if (now_ms < g->refilled_ms) {
		g->refilled_ms = now_ms; /* the clock went back: no credit, no debt */
	} else {
		uint64_t add = (now_ms - g->refilled_ms) * per_s; /* thousandths of a message */

		g->tokens = g->tokens + add > cap ? cap : g->tokens + add;
		g->refilled_ms = now_ms;
	}
	if (g->tokens >= 1000u) {
		g->tokens -= 1000u;
		return true;
	}
	if (g->dropped != ~0u)
		g->dropped++;
	return false;
}

/* The message that was admitted wants to write a log line: true = write it (at most MSG_LINES_PER_WINDOW per window and kind). */
static inline bool msg_gate_line(struct msg_gate *g)
{
	if (g->lines < MSG_LINES_PER_WINDOW) {
		g->lines++;
		return true;
	}
	if (g->hidden != ~0u)
		g->hidden++;
	return false;
}

#endif
