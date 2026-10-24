/*
 * 04-b31-canvas.c — THE BENCH OF THE CHANGING CANVAS, `RCP.md` §7.1 and §6.2.
 *
 *   04-b31-canvas            runs all the cases
 *   04-b31-canvas <n>        runs only case n
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS, AND WHY IT IS NOT A NETWORK BENCH
 *
 * `CODER.md` §3.6: *«when the chain is already narrowed down, do not run another
 * round of benches: write the minimal program that calls only the suspect
 * function on a known input.  It costs less and closes sooner.»*
 *
 * The new chain of 15 Aug 2026 — `FIT_CANVAS` → `children_recanvas()` →
 * `capture_resize()` → the frame that comes back — crosses **two
 * processes, a compositor and a graphics card**.  ⛔ Testing all of it needs the
 * test machine with the graphical session alive; ⭐ but the HALF that decides —
 * the state machine of `rcp.c` — needs none of this: it receives bytes, returns
 * bytes, and asks whoever hosts it to act.
 *
 * ⇒ Here `rcp.c` is mounted BARE, with test hooks in place of the stage.  The
 *   «stage» is a variable of this file: it can be made to answer late, grant a
 *   size different from the one asked, or not answer at all.
 *
 * ⛔ AND WHAT THIS BENCH DOES NOT TEST, declared instead of discovered:
 *   · **it does not test that the compositor resizes**: that is `[M]` of
 *     `benches/04-in8-measure.c` (Mutter 41.6 ms, labwc 5.1 ms);
 *   · **it does not test that the pixels are right**: there is not a pixel here;
 *   · **it does not test the page**: `src/page.html` has its own counters
 *     (§6.2), and those are watched from the browser.
 *   ⇒ It tests the one thing that sits in between, and it is the one no bench
 *     was watching: **that every `FIT_CANVAS` gets exactly one `CANVAS` back, and
 *     that the canvas in force never takes a value nobody granted.**
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE EXPECTATION IS DECLARED FIRST (rule B0.4 of `LESSONS.md`): every case
 *    below carries its «expected» line, and the bench compares against it.  A
 *    bench that prints what happened and calls it a result measures nothing.
 */
#include "../src/rcp.h"

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ------------------------------------------------------------------ *
 *  The wire, in bytes — §6.0/§6.1: network order (big-endian), no padding
 * ------------------------------------------------------------------ */

static uint8_t report[4096];
static size_t out_n;

static void mette(uint8_t **p, uint8_t v) { *(*p)++ = v; }
static void mette16(uint8_t **p, uint16_t v)
{
	mette(p, (uint8_t)(v >> 8));
	mette(p, (uint8_t)v);
}
static void mette32(uint8_t **p, uint32_t v)
{
	mette16(p, (uint16_t)(v >> 16));
	mette16(p, (uint16_t)v);
}
static void putstr(uint8_t **p, const char *s)
{
	size_t n = strlen(s);
	mette16(p, (uint16_t)n);
	memcpy(*p, s, n);
	*p += n;
}

/* A CLIENT message: header (u16 type, u32 length) + body. */
static size_t frame_message(uint8_t *buf, uint16_t kind, const uint8_t *body,
                         size_t len)
{
	uint8_t *p = buf;
	mette16(&p, kind);
	mette32(&p, (uint32_t)len);
	memcpy(p, body, len);
	return 6 + len;
}

/* ------------------------------------------------------------------ *
 *  The fake stage — and its three ways of behaving
 * ------------------------------------------------------------------ */

static struct {
	/* what it has been asked */
	uint32_t requested_w, requested_h;
	int how_many_requests;
	/* how it answers */
	bool accept;        /* does the `recanvas` hook return true?             */
	bool grants_other;  /* grants a size DIFFERENT from the one asked      */
	uint32_t other_w, other_h;
	/* what size it has now, for the `stage_canvas` hook */
	bool size_known;
	uint32_t size_w, size_h;
} stage;

/* ⛔⛔⭐ THE BIRTH REQUEST — 16 Aug 2026, and it kept this bench
 *      RED FOR A WHOLE DAY without anybody noticing.
 *
 *      On 15 August the cure for the tail of the access times (commit `477d708`)
 *      did one extra, declared thing: the session, as soon as it attaches,
 *      **tells the stage at what size it must be born** instead of letting it be
 *      born at a size of its own and then changing it.  The log writes it at
 *      every access: *«§4.5: I tell the stage that the canvas of this session is
 *      NxM — so it is born that way instead of being born at a size of its own
 *      and having to change it (and the change is a race)»*.
 *
 *      ⇒ Since then `open_session()` leaves **one** request to the stage behind
 *      it, and seven cases out of eighteen were still counting from zero.  ⛔ All
 *      seven with the SAME gap — one request — and four of them also showed
 *      «CANVAS sent 0», which was not a second defect: they are written
 *      `all_ok = …; if (all_ok) { … }`, and once the first condition failed the
 *      second half was never executed.  One defect only, seven faces.
 *
 * ⭐ AND THE CURE IS NOT ADDING ONE.  If this bench merely expected a bigger
 *    number, it would become **blind precisely to the thing that turned it
 *    red**: the day the birth request disappeared — that is, the seventeen
 *    seconds of tail came back — the counts would add up all the same.
 *    ⇒ TWO things are done:
 *
 *      1. the cases count **from after the birth**, with `after_birth()`,
 *         which tells the reader that the birth exists and is another matter;
 *      2. ⭐ **case 19** tests the birth on its own: if it disappears, it is IT
 *         that turns red, and with a message that names the defect. */
static int birth_requests;

static int after_birth(void)
{
	return stage.how_many_requests - birth_requests;
}

static void collect(void); /* reads what the server has sent, and empties it */

static bool g_recanvas(void *ctx, uint32_t l, uint32_t a)
{
	(void)ctx;
	stage.how_many_requests++;
	stage.requested_w = l;
	stage.requested_h = a;
	return stage.accept;
}

static bool g_stage_canvas(void *ctx, uint32_t *l, uint32_t *a)
{
	(void)ctx;
	if (!stage.size_known)
		return false;
	*l = stage.size_w;
	*a = stage.size_h;
	return true;
}

/* ⭐⭐ THE STAGE ANSWERS — and it is the road the first draft did NOT have: there
 *     the parent guessed from the frames «if one of a different size arrives then
 *     the stage has obeyed», and with two chained requests it guessed wrong.
 *
 * `voluta_*` = which request it answers.  ⛔ It is what makes the recognition
 * a FACT instead of a deduction. */
static void stage_replies(rcp_session *s, uint32_t intended_w, uint32_t intended_h,
                           uint64_t now)
{
	uint32_t l = intended_w, a = intended_h;
	if (stage.grants_other) {
		l = stage.other_w;
		a = stage.other_h;
	}
	stage.size_known = true;
	stage.size_w = l;
	stage.size_h = a;
	rcp_canvas_from_stage(s, intended_w, intended_h, l, a, now);
	collect();
}

/* The stage answers the LAST request it received. */
static void stage_delivery(rcp_session *s, uint64_t now)
{
	stage_replies(s, stage.requested_w, stage.requested_h, now);
}

/* ⛔ «I didn't make it»: `0x0`, which is NOT a size. */
static void stage_gives_up(rcp_session *s, uint64_t now)
{
	rcp_canvas_from_stage(s, stage.requested_w, stage.requested_h, 0, 0, now);
	collect();
}

/* ------------------------------------------------------------------ *
 *  The hooks
 * ------------------------------------------------------------------ */

static bool closed;
static uint8_t close_reason;
static bool verbose;

static void g_send(void *ctx, const uint8_t *data, size_t len)
{
	(void)ctx;
	if (out_n + len > sizeof report)
		return;
	memcpy(report + out_n, data, len);
	out_n += len;
}
static void g_on_close(void *ctx, uint8_t reason)
{
	(void)ctx;
	closed = true;
	close_reason = reason;
}
static void g_on_log(void *ctx, const char *line)
{
	(void)ctx;
	if (verbose)
		printf("      | %s\n", line);
}
/* D4b: the synchronous `verify` hook is gone — the bench logs in the way the server does: the check is ASKED (`ask_verify`)
 * and its outcome comes back through `rcp_verdict()` (see `open_session()`). */
static bool g_credentials_ok;
static bool g_ask(void *ctx, const char *user, const char *password, uint64_t *ticket)
{
	(void)ctx;
	g_credentials_ok = strcmp(user, "prova") == 0 && strcmp(password, "prova2026") == 0;
	*ticket = 1;
	return true;
}

/* ⛔ THE FOUR VIDEO HOOKS — 11 Oct 2026.  Since `0b84a5b` (22 Sep 2026,
 *    `RCP.md` §7.1) the server ADOPTS the stage's size when the stage is
 *    elsewhere and NO frame has gone out yet (the KDE stage that outlives a
 *    server restart).  ⇒ Cases 9 and 18 were written for a session that has
 *    already sent video, and they must SAY so: without a frame they were
 *    testing the new branch with the old expectation, and the bench stayed
 *    red, 17 of 19, from 22 Sep to 11 Oct.  The stream goes nowhere: only
 *    `video_sent` matters here. */
static int64_t next_stream = 3;
static bool g_video_open(void *ctx, int64_t *stream, uint64_t *remain)
{
	(void)ctx;
	*stream = next_stream;
	next_stream += 4;
	*remain = 100;
	return true;
}
static bool g_video_write(void *ctx, int64_t stream, const uint8_t *data,
                           size_t len)
{
	(void)ctx;
	(void)stream;
	(void)data;
	(void)len;
	return true;
}
static void g_video_fin(void *ctx, int64_t stream)
{
	(void)ctx;
	(void)stream;
}
static void g_video_reset(void *ctx, int64_t stream)
{
	(void)ctx;
	(void)stream;
}

/* One complete keyframe, at the canvas in force: after it, §7.1 forbids
 * adopting a stage that goes its own way. */
static bool a_frame(rcp_session *s, uint64_t now)
{
	static const uint8_t data[4] = { 0, 0, 0, 1 };
	return rcp_video_open(s, true, sizeof data, now * 1000, 0, now)
	           == RCP_VIDEO_SENT
	    && rcp_video_piece(s, data, sizeof data) == RCP_VIDEO_SENT
	    && rcp_video_finish(s) == RCP_VIDEO_SENT;
}

/* ------------------------------------------------------------------ *
 *  Reading what the server has sent
 * ------------------------------------------------------------------ */

#define T_SESSION 0x0007u
#define T_CANVAS 0x000Eu
#define T_FIT_CANVAS 0x000Bu
#define T_HELLO 0x0001u
#define T_CREDENTIALS 0x0003u
#define T_ATTACH 0x0006u

struct seen_canvas {
	uint8_t outcome, reason;
	uint32_t l, a;
};

static int canvas_count;
static struct seen_canvas last_canvas;
static uint32_t session_w, session_h;

/* Reads all the accumulated messages and counts the `CANVAS`s.  ⛔ It EMPTIES: the
 * count that matters is «how many have gone out since I last looked», not the
 * total. */
static void collect(void)
{
	size_t i = 0;
	canvas_count = 0;
	while (i + 6 <= out_n) {
		uint16_t kind = (uint16_t)((report[i] << 8) | report[i + 1]);
		uint32_t len = ((uint32_t)report[i + 2] << 24)
		             | ((uint32_t)report[i + 3] << 16)
		             | ((uint32_t)report[i + 4] << 8) | report[i + 5];
		const uint8_t *c = report + i + 6;
		if (i + 6 + len > out_n)
			break;
		if (kind == T_CANVAS && len >= 10) {
			canvas_count++;
			last_canvas.outcome = c[0];
			last_canvas.reason = c[1];
			last_canvas.l = ((uint32_t)c[2] << 24) | ((uint32_t)c[3] << 16)
			              | ((uint32_t)c[4] << 8) | c[5];
			last_canvas.a = ((uint32_t)c[6] << 24) | ((uint32_t)c[7] << 16)
			              | ((uint32_t)c[8] << 8) | c[9];
		}
		if (kind == T_SESSION && len >= 9) {
			session_w = ((uint32_t)c[1] << 24) | ((uint32_t)c[2] << 16)
			           | ((uint32_t)c[3] << 8) | c[4];
			session_h = ((uint32_t)c[5] << 24) | ((uint32_t)c[6] << 16)
			           | ((uint32_t)c[7] << 8) | c[8];
		}
		i += 6 + len;
	}
	out_n = 0;
}

/* ------------------------------------------------------------------ *
 *  The handshake, up to `SESSION`
 * ------------------------------------------------------------------ */

static uint64_t clock;

/* ⛔ Where the next session comes from: case 18 needs it, as it wants TWO —
 *    and the slot of §8.2 is per USER, not per address, so two different
 *    origins of the same user compete for the same slot. */
static const char *next_provenance = "10.0.0.9:5000";

static rcp_session *open_session(uint32_t canvas_w, uint32_t canvas_h,
                                   const char *max_measure, bool with_hooks)
{
	rcp_hooks g;
	rcp_session *s;
	uint8_t body[512], envelope[600];
	uint8_t *p;
	size_t n;

	memset(&g, 0, sizeof g);
	g.send_msg = g_send;
	g.close = g_on_close;
	g.record = g_on_log;
	g.ask_verify = g_ask;
	if (with_hooks) {
		g.recanvas = g_recanvas;
		g.stage_canvas = g_stage_canvas;
		g.video_open = g_video_open;
		g.video_write = g_video_write;
		g.video_fin = g_video_fin;
		g.video_reset = g_video_reset;
	}

	closed = false;
	out_n = 0;
	clock = 1000;
	s = rcp_open(&g, next_provenance, clock);
	if (!s)
		return NULL;

	/* HELLO: version + capabilities (§4.3).
	 * ⛔ `audio.codec=pcm` is NOT decoration: §4.3 demands it, and without it the
	 *    server says farewell with `NOTHING_IN_COMMON` — something this bench
	 *    discovered on its first run, with all cases red and zero `SESSION`.
	 *    It is `CODER.md` §3.3: the bench is certified BEFORE pointing it at the
	 *    unknown, or a red does not tell «the unknown does not work» from
	 *    «the bench did not work». */
	p = body;
	mette16(&p, 1);                      /* version */
	mette16(&p, max_measure ? 4 : 3);     /* how many capabilities */
	putstr(&p, "video.codec");
	putstr(&p, "hevc");
	putstr(&p, "video.depth");
	putstr(&p, "8,10");
	putstr(&p, "audio.codec");
	putstr(&p, "pcm");
	if (max_measure) {
		putstr(&p, "video.max_size");
		putstr(&p, max_measure);
	}
	n = frame_message(envelope, T_HELLO, body, (size_t)(p - body));
	rcp_receive(s, envelope, n, clock);

	/* CREDENTIALS */
	p = body;
	putstr(&p, "prova");
	putstr(&p, "prova2026");
	n = frame_message(envelope, T_CREDENTIALS, body, (size_t)(p - body));
	rcp_receive(s, envelope, n, clock);
	(void)rcp_verdict(s, 1, g_credentials_ok, clock);
	/* ⛔ §4.4-bis: the fixed second.  Time is made to flow, which is what the
	 *    server's `poll` loop would do. */
	clock += 1500;
	rcp_time(s, clock);

	/* ATTACH */
	p = body;
	mette32(&p, canvas_w);
	mette32(&p, canvas_h);
	mette32(&p, canvas_w); /* view: it does not matter here */
	mette32(&p, canvas_h);
	putstr(&p, "it");
	n = frame_message(envelope, T_ATTACH, body, (size_t)(p - body));
	rcp_receive(s, envelope, n, clock);
	collect();
	/* ⛔ Here the session has already told the stage at what size to be born
	 *    (§4.5): what the attach left behind is noted, so the cases can count
	 *    from after it.  ⚠ The long reason is at `birth_requests`. */
	birth_requests = stage.how_many_requests;
	return s;
}

static void send_fit(rcp_session *s, uint32_t l, uint32_t a)
{
	uint8_t body[8], envelope[32];
	uint8_t *p = body;
	size_t n;
	mette32(&p, l);
	mette32(&p, a);
	n = frame_message(envelope, T_FIT_CANVAS, body, 8);
	rcp_receive(s, envelope, n, clock);
	collect();
}

/* ------------------------------------------------------------------ *
 *  The cases
 * ------------------------------------------------------------------ */

static int failed, passed;

static void outcome(const char *test_case, bool all_ok, const char *expected,
                  const char *seen)
{
	if (all_ok) {
		passed++;
		printf("  \033[1;32mOK\033[0m  %-34s %s\n", test_case, seen);
	} else {
		failed++;
		printf("  \033[1;31mNO\033[0m  %-34s\n        expected: %s\n        seen:     %s\n",
		       test_case, expected, seen);
	}
}

static char said[256];
static const char *report_it(void)
{
	snprintf(said, sizeof said,
	         "CANVAS sent %d (outcome %u reason %u -> %ux%u), requests to the stage "
	         "%d (of which %d at birth, §4.5), canvas in force %ux%u",
	         canvas_count, last_canvas.outcome, last_canvas.reason, last_canvas.l,
	         last_canvas.a, stage.how_many_requests, birth_requests,
	         last_canvas.l, last_canvas.a);
	return said;
}

static void reset_stage(void)
{
	memset(&stage, 0, sizeof stage);
	stage.accept = true;
	memset(&last_canvas, 0, sizeof last_canvas);
	canvas_count = 0;
}

/* 1 — the good road: it is asked, the stage delivers, ONE `CANVAS` goes out. */
static void case1(void)
{
	rcp_session *s;
	uint32_t l = 0, a = 0;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	/* ⛔ EXPECTED: no `CANVAS` yet — the answer is the frame. */
	all_ok = canvas_count == 0 && after_birth() == 1
	    && stage.requested_w == 1600 && stage.requested_h == 900;
	if (all_ok) {
		stage_delivery(s, clock);
		rcp_canvas_in_effect(s, &l, &a);
		all_ok = canvas_count == 1 && last_canvas.outcome == 1
		    && last_canvas.l == 1600 && last_canvas.a == 900 && l == 1600
		    && a == 900 && !closed;
	}
	outcome("1 the good road", all_ok,
	      "no CANVAS before the frame, then only ONE with 1600x900",
	      report_it());
	rcp_free(s);
}

/* 2 — the size that is already there: answer AT ONCE and do not touch the stage. */
static void case2(void)
{
	rcp_session *s;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1920, 1080);
	all_ok = canvas_count == 1 && last_canvas.outcome == 1 && last_canvas.reason == 0
	    && last_canvas.l == 1920 && last_canvas.a == 1080
	    && after_birth() == 0 && !closed;
	outcome("2 the size already there", all_ok,
	      "ONE CANVAS(FITTED 1920x1080) at once, ZERO requests to the stage",
	      report_it());
	rcp_free(s);
}

/* 3 — two `FIT_CANVAS` in a row: TWO `CANVAS`s, or the client's count never gets
 *     back to zero and the page holds back frames forever (§6.2). */
static void case3(void)
{
	rcp_session *s;
	int first, seconds;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	first = canvas_count;
	send_fit(s, 1280, 720);
	seconds = canvas_count;
	/* ⛔ EXPECTED: the second request sends out the `CANVAS` that answers the
	 *    FIRST (NOT_NOW), and then the frame sends out the one of the second. */
	all_ok = first == 0 && seconds == 1 && last_canvas.outcome == 2
	    && last_canvas.reason == 3;
	if (all_ok) {
		stage_delivery(s, clock);
		all_ok = canvas_count == 1 && last_canvas.outcome == 1
		    && last_canvas.l == 1280 && last_canvas.a == 720 && !closed;
	}
	outcome("3 two FIT_CANVAS in a row", all_ok,
	      "two CANVAS in all: NOT_NOW to the first, FITTED 1280x720 to the second",
	      report_it());
	rcp_free(s);
}

/* 4 — the stage does not deliver: after the deadline the answer is `NOT_NOW`
 *     (§7.1: «a silence leaves the client waiting forever»). */
static void case4(void)
{
	rcp_session *s;
	uint32_t l = 0, a = 0;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	/* one clock tick BEFORE the deadline: nothing must go out */
	clock += RCP_CANVAS_WAIT_MS - 1;
	rcp_time(s, clock);
	collect();
	all_ok = canvas_count == 0;
	if (all_ok) {
		clock += 2;
		rcp_time(s, clock);
		collect();
		rcp_canvas_in_effect(s, &l, &a);
		all_ok = canvas_count == 1 && last_canvas.outcome == 2
		    && last_canvas.reason == 3 && l == 1920 && a == 1080 && !closed;
	}
	outcome("4 the stage does not deliver", all_ok,
	      "nothing before the deadline, then ONE CANVAS(REFUSED, NOT_NOW), canvas 1920x1080",
	      report_it());
	rcp_free(s);
}

/* 5 — the size ABOVE THE MAXIMUM: since 1 Oct 2026 (`RCP.md` §4.5, canvas at
 *     most 4096x2304, user decision) it is NOT refused: it is REDUCED to the
 *     maximum — the side that overflows to the maximum, the other as it is — and
 *     passed to the stage like any size, with the «DECLARED FALLBACK» line in
 *     the log.  ⛔ And the session stays alive, as before: 100000x100000 was the
 *     number «capable of killing the compositor», and here it becomes 4096x2304
 *     BEFORE reaching the stage.  (Until 30 Sep it was `CANVAS(REFUSED,
 *     SIZE_OUT_OF_RANGE)`; the refusal stays BELOW the minimum: case 17.) */
static void case5(void)
{
	rcp_session *s;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 100000, 100000);
	all_ok = canvas_count == 0 && after_birth() == 1
	    && stage.requested_w == RCP_CANVAS_MAX_W
	    && stage.requested_h == RCP_CANVAS_MAX_H && !closed;
	outcome("5 size above the maximum: reduced", all_ok,
	      "no CANVAS at once, ONE request to the stage at 4096x2304 (the maximum of "
	      "§4.5), session ALIVE",
	      report_it());
	rcp_free(s);
}

/* 6 — the odd size is truncated down and IT IS SAID (§5.0-sexies: «a pixel
 *     stated is worth more than a pixel hidden in a scale»). */
static void case6(void)
{
	rcp_session *s;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 2133, 1201);
	all_ok = after_birth() == 1 && stage.requested_w == 2132
	    && stage.requested_h == 1200;
	if (all_ok) {
		stage_delivery(s, clock);
		all_ok = canvas_count == 1 && last_canvas.l == 2132
		    && last_canvas.a == 1200;
	}
	outcome("6 the odd size, truncated", all_ok,
	      "to the stage 2132x1200 (truncated to even), and the CANVAS carries that",
	      report_it());
	rcp_free(s);
}

/* 7 — §4.5: the stage grants a size DIFFERENT from the one asked.  The `CANVAS`
 *     must carry the REAL one, not the one asked. */
static void case7(void)
{
	rcp_session *s;
	uint32_t l = 0, a = 0;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	stage.grants_other = true;
	stage.other_w = 1366;
	stage.other_h = 768;
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	stage_delivery(s, clock);
	rcp_canvas_in_effect(s, &l, &a);
	all_ok = canvas_count == 1 && last_canvas.outcome == 1 && last_canvas.l == 1366
	    && last_canvas.a == 768 && l == 1366 && a == 768 && !closed;
	outcome("7 the stage grants other (§4.5)", all_ok,
	      "ONE CANVAS(FITTED 1366x768), and the canvas in force is the REAL one",
	      report_it());
	rcp_free(s);
}

/* 8 — ⭐ THE RE-ATTACH: the stage already has 1912x1044, the page asks 1920x1080.
 *     `SESSION` must grant the STAGE's, or not a pixel arrives. */
static void case8(void)
{
	rcp_session *s;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	stage.size_known = true;
	stage.size_w = 1912;
	stage.size_h = 1044;
	s = open_session(1920, 1080, NULL, true);
	all_ok = session_w == 1912 && session_h == 1044 && !closed;
	snprintf(said, sizeof said, "SESSION grants %ux%u", session_w,
	         session_h);
	outcome("8 the re-attach", all_ok,
	      "SESSION grants 1912x1044 (the stage's, §4.5), not 1920x1080",
	      said);
	rcp_free(s);
}

/* 9 — ⭐⭐ THE STAGE GOES ITS OWN WAY — and here the first draft got the
 *      SEVERITY wrong: it adopted the stage's size and sent a `CANVAS` nobody had
 *      asked for.  ⛔ §6.2 says the client holds back a never-announced size
 *      **only while it has an unanswered `FIT_CANVAS`**: without one, it is
 *      `PROTOCOL_ERROR` — and the frame, which travels on a stream of its
 *      own, arrives before the `CANVAS` half of the time.  ⇒ The server would have
 *      made a session close in which nobody had made a mistake.
 *
 *      ⇒ EXPECTED NOW: **no `CANVAS`, ever**, and the stage CALLED BACK to the
 *      canvas in force with a growing wait.
 *
 *      ⚠ AFTER THE FIRST FRAME (`RCP.md` §7.1, 22 Sep 2026): before it the
 *      server adopts the stage instead, and that is case 20. */
static void case9(void)
{
	rcp_session *s;
	uint32_t l = 0, a = 0;
	int first;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	all_ok = a_frame(s, clock);
	/* the stage says it is at 1280x720 without anybody having asked */
	rcp_canvas_from_stage(s, 0, 0, 1280, 720, clock);
	collect();
	first = after_birth();
	all_ok = all_ok && canvas_count == 0 && first == 1 && stage.requested_w == 1920
	    && stage.requested_h == 1080;
	if (all_ok) {
		/* it insists: and the call-back repeats, but not at every message */
		rcp_canvas_from_stage(s, 0, 0, 1280, 720, clock);
		collect();
		all_ok = canvas_count == 0 && after_birth() == 1;
	}
	if (all_ok) {
		clock += RCP_CANVAS_RETRY_MS + 1;
		rcp_canvas_from_stage(s, 0, 0, 1280, 720, clock);
		collect();
		rcp_canvas_in_effect(s, &l, &a);
		all_ok = canvas_count == 0 && after_birth() == 2 && l == 1920
		    && a == 1080 && !closed;
	}
	outcome("9 the stage goes its own way", all_ok,
	      "after one frame: ZERO CANVAS (an unrequested one would make the client close), the stage "
	      "called back to 1920x1080 with the growing wait",
	      report_it());
	rcp_free(s);
}

/* 10 — the client's decoder ceiling (§4.5): `FIT_CANVAS` beyond
 *      `video.max_size` is REDUCED in proportion, as in `ATTACH`. */
static void case10(void)
{
	rcp_session *s;
	uint32_t l = 0, a = 0;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	/* ⚠ The ceiling is 2560x1440 and not 1920x1080 on purpose: with the latter
	 *   the reduction would give **exactly the canvas in force**, and the case
	 *   would end up in the «the size that is already there» branch — which is
	 *   right, but does not test the reduction.  (The first draft of this case
	 *   fell for it: the expectation was wrong, not the code.) */
	s = open_session(1920, 1080, "2560x1440", true);
	/* the hi-dpi client asks for the size of its window in PHYSICAL pixels */
	send_fit(s, 3840, 2160);
	all_ok = after_birth() == 1 && stage.requested_w == 2560
	    && stage.requested_h == 1440;
	if (all_ok) {
		stage_delivery(s, clock);
		rcp_canvas_in_effect(s, &l, &a);
		all_ok = canvas_count == 1 && last_canvas.outcome == 1 && l == 2560
		    && a == 1440 && !closed;
	}
	outcome("10 beyond the client's ceiling", all_ok,
	      "reduced to 2560x1440 (proportions kept) and granted, NEVER 3840x2160",
	      report_it());
	rcp_free(s);
}

/* 11 — no hook (the host has no stage): `COMPOSITOR_UNABLE`, which is the
 *      true answer and does not close the session (§7.1). */
static void case11(void)
{
	rcp_session *s;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, false);
	send_fit(s, 1600, 900);
	all_ok = canvas_count == 1 && last_canvas.outcome == 2 && last_canvas.reason == 1
	    && last_canvas.l == 1920 && last_canvas.a == 1080 && !closed;
	outcome("11 host without a stage", all_ok,
	      "ONE CANVAS(REFUSED, COMPOSITOR_UNABLE), session alive", report_it());
	rcp_free(s);
}

/* 12 — the request that does not leave: `NOT_NOW` at once, and nothing hangs. */
static void case12(void)
{
	rcp_session *s;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	stage.accept = false;
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	all_ok = canvas_count == 1 && last_canvas.outcome == 2 && last_canvas.reason == 3
	    && last_canvas.l == 1920 && last_canvas.a == 1080 && !closed;
	outcome("12 the request does not leave", all_ok,
	      "ONE CANVAS(REFUSED, NOT_NOW) at once", report_it());
	rcp_free(s);
}

/* 13 — ⛔ THE OLD FRAME that arrives while a request is in flight: the
 *      stage is still delivering the previous size.  It must NOT close the
 *      request, or the client would receive `CANVAS(FITTED, the old size)`
 *      as the answer to a request that was about to succeed. */
static void case13(void)
{
	rcp_session *s;
	uint32_t l = 0, a = 0;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	/* the stage still states the previous size: it is renegotiating */
	rcp_canvas_from_stage(s, 0, 0, 1920, 1080, clock);
	collect();
	all_ok = canvas_count == 0;
	if (all_ok) {
		stage_delivery(s, clock);
		rcp_canvas_in_effect(s, &l, &a);
		all_ok = canvas_count == 1 && last_canvas.l == 1600
		    && last_canvas.a == 900 && l == 1600 && a == 900;
	}
	outcome("13 the old frame in flight", all_ok,
	      "the OLD size does not close the request; then CANVAS(1600x900)",
	      report_it());
	rcp_free(s);
}

/* 14 — ⭐⭐ TWO CHAINED REQUESTS, and the answer to the FIRST arriving later:
 *      it is the gesture of someone dragging the edge of the window.  ⛔ The first
 *      draft took the frame of the first request for the answer to the
 *      second — and the desktop settled on the wrong size **with the message
 *      counts in order**, that is without anything saying so. */
static void case14(void)
{
	rcp_session *s;
	uint32_t l = 0, a = 0;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);      /* first */
	send_fit(s, 1280, 720);      /* second: NOT_NOW to the first */
	all_ok = canvas_count == 1 && last_canvas.outcome == 2 && last_canvas.reason == 3;
	if (all_ok) {
		/* ⛔ the answer to the FIRST request arrives, late */
		stage_replies(s, 1600, 900, clock);
		rcp_canvas_in_effect(s, &l, &a);
		all_ok = canvas_count == 0 && l == 1920 && a == 1080;
	}
	if (all_ok) {
		/* and then the one to the second, which is the only one that counts */
		stage_replies(s, 1280, 720, clock);
		rcp_canvas_in_effect(s, &l, &a);
		all_ok = canvas_count == 1 && last_canvas.outcome == 1
		    && last_canvas.l == 1280 && last_canvas.a == 720 && l == 1280
		    && a == 720 && !closed;
	}
	outcome("14 two chained requests", all_ok,
	      "the answer to the FIRST does not close the SECOND: the canvas ends at "
	      "1280x720, the one the user asked for last",
	      report_it());
	rcp_free(s);
}

/* 15 — ⭐ the stage says «I didn't make it»: `NOT_NOW` AT ONCE, without waiting
 *      the three seconds of the deadline for news that is already there. */
static void case15(void)
{
	rcp_session *s;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	all_ok = canvas_count == 0;
	if (all_ok) {
		stage_gives_up(s, clock);
		all_ok = canvas_count == 1 && last_canvas.outcome == 2
		    && last_canvas.reason == 3 && last_canvas.l == 1920
		    && last_canvas.a == 1080 && !closed;
	}
	outcome("15 the stage gives up", all_ok,
	      "ONE CANVAS(REFUSED, NOT_NOW) at once, not after the deadline", report_it());
	rcp_free(s);
}

/* 16 — ⭐ the stage answers «I already have that size»: the request is closed
 *      with `CANVAS(FITTED)` without waiting for a frame that will not come,
 *      because whoever is watching already has the frames of that size in front of them. */
static void case16(void)
{
	rcp_session *s;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1600, 900);
	/* the stage really changes */
	stage_delivery(s, clock);
	all_ok = canvas_count == 1 && last_canvas.l == 1600;
	if (all_ok) {
		/* now the client asks again for a size the stage ALREADY HAS: the child
		 * answers at once, without any new frame */
		send_fit(s, 1280, 720);
		all_ok = canvas_count == 0;
	}
	if (all_ok) {
		rcp_canvas_from_stage(s, 1280, 720, 1280, 720, clock);
		collect();
		all_ok = canvas_count == 1 && last_canvas.outcome == 1
		    && last_canvas.l == 1280 && last_canvas.a == 720 && !closed;
	}
	outcome("16 the stage already had it", all_ok,
	      "CANVAS(FITTED 1280x720) at the stage's answer, without deadline",
	      report_it());
	rcp_free(s);
}

/* 17 — ⛔ the limits of §4.5 PER SIDE: 1600x230 is out (the height), and must be
 *      refused — or at the re-attach `ATTACH` would refuse a canvas that this
 *      same server had granted. */
static void case17(void)
{
	rcp_session *s;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	send_fit(s, 1600, 230);
	all_ok = canvas_count == 1 && last_canvas.outcome == 2 && last_canvas.reason == 2
	    && last_canvas.l == 1920 && last_canvas.a == 1080
	    && after_birth() == 0 && !closed;
	outcome("17 below the minimum of §4.5", all_ok,
	      "ONE CANVAS(REFUSED, SIZE_OUT_OF_RANGE): 230 < 240", report_it());
	rcp_free(s);
}

/* 18 — ⛔⛔ THE PING-PONG BETWEEN TWO SESSIONS OF THE SAME USER, and it is not a
 *      textbook case: it is the defect the user saw on the morning of 15 Aug
 *      2026, and told me like this — «on Android the mouse no longer takes the
 *      clicks».
 *
 *      `[M]` from the log of his real session:
 *        05:10  the laptop attaches, canvas 2544x926
 *        05:12  silent for thirty seconds ⇒ DETACHED for silence, leaves the slot —
 *               ⛔ but the session stays ALIVE, with the video channel on
 *        05:14  the phone attaches, canvas 2560x926
 *        05:14  **seventeen requests per second**, forever: the laptop
 *               asks 2544, the phone 2560, the laptop 2544 …
 *      ⇒ every round restarts the stream, Mutter recreates the `libei` devices
 *        (`[M]` 640 replacements) and the input region never agrees with the
 *        canvas ⇒ **the clicks land elsewhere**.
 *
 *      ⇒ EXPECTED: whoever does NOT have the slot asks nothing of the stage, and
 *      an `FIT_CANVAS` of theirs is answered with `NOT_NOW` (I2: the stage is
 *      commanded by whoever is attached). */
static void case18(void)
{
	rcp_session *uno, *due;
	int requests_before;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();

	/* The laptop: attaches and takes the canvas. */
	next_provenance = "10.0.0.9:5000";
	uno = open_session(1920, 1080, NULL, true);
	send_fit(uno, 1600, 900);
	stage_delivery(uno, clock);
	/* ⚠ And it has been watching: without a frame gone out, §7.1 would adopt
	 *   the stage's size below (case 20) — not the scene this case is about. */
	all_ok = a_frame(uno, clock);

	/* Silent for thirty seconds: §5.3 takes its slot away, the session stays alive. */
	clock += 31000;
	rcp_time(uno, clock);
	collect();
	all_ok = all_ok && strcmp(rcp_state_name(uno), "detached-by-silence") == 0;

	/* The phone attaches and TAKES the slot, with a window of another
	 * size.  ⚠ `open_session` resets the clock: it is put back where it was, or
	 * the laptop's silence would trigger again. */
	if (all_ok) {
		uint64_t when = clock;
		next_provenance = "10.0.0.24:34583";
		due = open_session(1920, 1080, NULL, true);
		clock = when;
		send_fit(due, 1280, 720);
		stage_delivery(due, clock);
		requests_before = stage.how_many_requests;

		/* The stage is now at 1280x720, and its frames also reach the
		 * LAPTOP, which still has 1600x900 as the canvas in force. */
		rcp_canvas_from_stage(uno, 0, 0, 1280, 720, clock);
		rcp_canvas_from_stage(uno, 0, 0, 1280, 720, clock);
		collect();
		all_ok = stage.how_many_requests == requests_before && canvas_count == 0;

		/* ⭐ And if the laptop speaks again, it is not answered «not now»:
		 *    it is given FAREWELL with §8.2 `0x0F` — «you already have an active
		 *    session elsewhere», and this time it is true.  ⚠ `speak_again()`
		 *    does it at the top of `rcp_receive()`, before the message gets
		 *    anywhere: that is why a guard on the slot in `T_FIT_CANVAS` would
		 *    be dead code.  ⛔ What matters is that the stage is not
		 *    touched. */
		if (all_ok) {
			closed = false;
			send_fit(uno, 1024, 768);
			all_ok = stage.how_many_requests == requests_before && closed
			    && close_reason == 0x0F;
		}
		/* ⭐ And the phone, which does have the slot, commands all right. */
		if (all_ok) {
			closed = false;
			send_fit(due, 1152, 648);
			all_ok = stage.how_many_requests == requests_before + 1
			    && stage.requested_w == 1152 && !closed;
		}
		rcp_free(due);
	}
	outcome("18 two sessions, one stage only", all_ok,
	      "whoever lacks the slot does NOT command (zero requests to the stage, and "
	      "if it speaks again it is 0x0F); whoever has it does",
	      report_it());
	rcp_free(uno);
	next_provenance = "10.0.0.9:5000";
}

/* 19 — ⭐⭐ THE CANVAS IS DECLARED AT BIRTH, and this case exists because without
 *      it the bench would be BLIND precisely where it was red for a day.
 *
 *      `477d708`, 15 Aug 2026: the session that attaches tells the stage at
 *      once at what size to be born, instead of letting it be born at a size of
 *      its own and changing it afterwards.  ⭐ It is the cure that removed
 *      **seventeen seconds** of tail from the access times — «the change is a
 *      race», and the race was lost against a still scene.
 *
 * ⛔ The other cases now count with `after_birth()`, that is they SKIP
 *    this request.  ⇒ If it disappeared, they would all stay green and the tail
 *    would come back silently.  This case is the only one that would notice.
 *
 *    EXPECTED: the attach leaves **one** request to the stage, and it is at the
 *    size the client asked in `ATTACH` — not a fallback one, not zero. */
static void case19(void)
{
	rcp_session *s;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1600, 900, NULL, true);
	all_ok = birth_requests == 1 && stage.requested_w == 1600
	    && stage.requested_h == 900 && canvas_count == 0 && !closed;
	outcome("19 the canvas is declared at birth", all_ok,
	      "ONE request to the stage already with ATTACH, at 1600x900 (§4.5: it is "
	      "born that way instead of having to change it — those are the 17 s of tail)",
	      report_it());
	rcp_free(s);
}

/* 20 — ⭐ THE STAGE THAT WAS ALREADY THERE, `RCP.md` §7.1, `0b84a5b` 22 Sep 2026:
 *      the server restarts, the KDE session outlives it at another size, KWin
 *      `--virtual` does not resize.  ⛔ Before this rule: black screen forever.
 *
 *      EXPECTED: NO frame has gone out yet, so the stage's size is ADOPTED —
 *      one `CANVAS(FITTED)` at 1280x720, canvas in force 1280x720, no new
 *      request to the stage.  (After the first frame it is case 9.) */
static void case20(void)
{
	rcp_session *s;
	uint32_t l = 0, a = 0;
	bool all_ok;

	rcp_reset_session_log();
	reset_stage();
	s = open_session(1920, 1080, NULL, true);
	rcp_canvas_from_stage(s, 0, 0, 1280, 720, clock);
	collect();
	rcp_canvas_in_effect(s, &l, &a);
	all_ok = canvas_count == 1 && last_canvas.outcome == 1 && last_canvas.l == 1280
	    && last_canvas.a == 720 && l == 1280 && a == 720
	    && after_birth() == 0 && !closed;
	outcome("20 the stage that was already there", all_ok,
	      "no frame yet: ONE CANVAS(FITTED 1280x720), canvas in force 1280x720, "
	      "zero new requests (§7.1)",
	      report_it());
	rcp_free(s);
}

int main(int argc, char **argv)
{
	int solo = argc > 1 ? atoi(argv[1]) : 0;
	void (*cases[])(void) = { case1,  case2,  case3,  case4,  case5,  case6,
		                     case7,  case8,  case9,  case10, case11, case12,
		                     case13, case14, case15, case16, case17,
		                     case18, case19, case20 };
	const int amount = (int)(sizeof cases / sizeof cases[0]);

	verbose = getenv("VERBOSE") != NULL;
	printf("\n== 04-b31: the changing canvas (RCP.md §7.1, §6.2) ==\n\n");
	for (int i = 0; i < amount; i++) {
		if (solo && solo != i + 1)
			continue;
		cases[i]();
	}
	printf("\n  passed %d, failed %d\n\n", passed, failed);
	return failed ? 1 : 0;
}
