/*
 * 20-unchanged-test.c — desk test of the pure half of the «unchanged» filter
 * (`src/unchanged.h`, 15 Oct 2026).  No box, no PipeWire: synthetic frames.
 *
 * Build and run:  make -C src bench-unchanged && ./benches/20-unchanged-test
 * Exit 0 = every case passed; otherwise the failing case is named.
 *
 * Also the three decisions moved into `unchanged.h` after the review of
 * 1849a57d: the held frame due when the scene goes still (`uc_pending_*`),
 * the cost re-checked by windows and weighed against what it holds back
 * (`uc_cost_*`), the switch-off re-armed by a renegotiation or, for cost, by
 * `UC_REARM_MS`, and hard after `UC_STRIKES_MAX` (`uc_switch_*`); and after
 * the review of 845f4d19 the stale restart at most once per episode
 * (`uc_gate_*`) and the wait cut short when a keyframe is due.
 *
 * ⚠ What it does NOT cover: the merge of the damage in the slot
 *   (`on_process`, capture.c), the keeping/sending of the held frame and the
 *   restart on the card (`capture_take`, child.c), which need a stream.
 */
#include "../src/unchanged.h"

#include <stdio.h>
#include <stdlib.h>

static int failures;

#define CHECK(cond, what)                                                      \
	do {                                                                   \
		if (!(cond)) {                                                 \
			fprintf(stderr, "FAIL line %d: %s\n", __LINE__, what); \
			failures++;                                            \
		}                                                              \
	} while (0)

static uint8_t *frame(uint32_t h, uint32_t stride, uint8_t seed)
{
	uint8_t *p = malloc((size_t)stride * h);

	for (size_t i = 0; i < (size_t)stride * h; i++)
		p[i] = (uint8_t)(i * 31u + seed);
	return p;
}

static void put(uint8_t *f, uint32_t stride, uint32_t x, uint32_t y, uint8_t v)
{
	f[(size_t)y * stride + (size_t)x * 4u + 1u] = v;
}

int main(void)
{
	const uint32_t w = 640, h = 480, stride = 640 * 4 + 64; /* padded rows */
	uint8_t *a = frame(h, stride, 7);
	uint8_t *b = malloc((size_t)stride * h);
	Unchanged u = { 0 };
	UcRect r;

	/* --- uc_clip ---------------------------------------------------------- */
	r = (UcRect){ 600, 400, 100, 100 };
	CHECK(uc_clip(&r, w, h) && r.width == 40 && r.height == 80, "clip at the corner");
	r = (UcRect){ 640, 0, 10, 10 };
	CHECK(!uc_clip(&r, w, h), "rect starting at the right edge is empty");
	r = (UcRect){ 0, 0, 0, 10 };
	CHECK(!uc_clip(&r, w, h), "zero width is empty");
	r = (UcRect){ 3000, 2000, UINT32_MAX, UINT32_MAX };
	CHECK(uc_clip(&r, 3840, 2160) && r.width == 840 && r.height == 160,
	      "huge size clipped without overflow (4K)");

	/* --- nothing kept: always «changed» ------------------------------------ */
	r = (UcRect){ 10, 10, 20, 20 };
	CHECK(!uc_same(&u, a, w, h, stride, &r, 1), "empty reference says changed");

	/* --- keep two rects, compare the same bytes --------------------------- */
	{
		UcRect k[2] = { { 10, 10, 20, 20 }, { 100, 50, 64, 33 } };

		uc_keep(&u, a, w, h, stride, k, 2);
		CHECK(u.valid && u.n == 2, "reference kept");
		memcpy(b, a, (size_t)stride * h);
		CHECK(uc_same(&u, b, w, h, stride, k, 2), "same bytes, same rects");

		/* a sub-rect of the SECOND kept rect (tests uc_offset) */
		r = (UcRect){ 120, 60, 10, 5 };
		CHECK(uc_same(&u, b, w, h, stride, &r, 1), "sub-rect of the second kept rect");

		/* one byte changed inside the damage */
		put(b, stride, 125, 62, (uint8_t)(b[(size_t)62 * stride + 125 * 4 + 1] ^ 0xff));
		CHECK(!uc_same(&u, b, w, h, stride, &r, 1), "one byte changed is seen");
		CHECK(!uc_same(&u, b, w, h, stride, k, 2), "one byte changed is seen (both rects)");

		/* the last pixel of the second rect */
		memcpy(b, a, (size_t)stride * h);
		put(b, stride, 100 + 63, 50 + 32, (uint8_t)(b[(size_t)82 * stride + 163 * 4 + 1] ^ 1));
		CHECK(!uc_same(&u, b, w, h, stride, k, 2), "last pixel of a kept rect is compared");

		/* damage that sticks out of every kept rect */
		memcpy(b, a, (size_t)stride * h);
		r = (UcRect){ 25, 25, 10, 10 };
		CHECK(!uc_same(&u, b, w, h, stride, &r, 1), "damage not contained says changed");

		/* other geometry */
		CHECK(!uc_same(&u, b, w, h, stride + 4, k, 2), "other stride says changed");
		CHECK(!uc_same(&u, b, w + 1, h, stride, k, 2), "other width says changed");
		CHECK(!uc_same(&u, b, w, h, stride, k, 0), "no rect says changed");

		/* ⚠ the documented assumption: a change OUTSIDE the damage is not
		 *   looked at (KWin's damage is trusted; the 250 ms refresh covers it). */
		put(b, stride, 300, 300, 0x55);
		CHECK(uc_same(&u, b, w, h, stride, k, 2), "outside the damage is trusted");
	}

	/* --- too large an area keeps nothing ---------------------------------- */
	{
		const uint32_t W = 3840, H = 2160, S = 3840 * 4;
		uint8_t *big = calloc((size_t)S, H);
		UcRect all = { 0, 0, W, H / 2 };
		UcRect quarter = { 0, 0, W, H / 4 };

		uc_keep(&u, big, W, H, S, &all, 1);
		CHECK(!u.valid, "half of 4K is not kept");
		uc_keep(&u, big, W, H, S, &quarter, 1);
		CHECK(u.valid && u.capacity >= (size_t)W * (H / 4) * 4u,
		      "a quarter of 4K is kept, capacity grown");
		/* the bottom-right corner of 4K: offsets near the end of the buffer */
		{
			UcRect c = { W - 8, H - 8, 8, 8 };

			uc_keep(&u, big, W, H, S, &c, 1);
			CHECK(uc_same(&u, big, W, H, S, &c, 1), "bottom-right corner of 4K");
			big[(size_t)(H - 1) * S + (size_t)(W - 1) * 4u] = 9;
			CHECK(!uc_same(&u, big, W, H, S, &c, 1), "last byte of 4K is compared");
		}
		free(big);
	}

	/* --- the held frame when the scene goes still ------------------------- */
	{
		const uint64_t t0 = 1000000, ms = 1000;

		CHECK(uc_pending_due(FALSE, FALSE, t0, t0 + 999 * ms) == UC_PENDING_NONE,
		      "nothing held: nothing due");
		CHECK(uc_pending_due(FALSE, TRUE, t0, t0) == UC_PENDING_NONE,
		      "nothing held, keyframe due: still nothing");
		CHECK(uc_pending_due(TRUE, FALSE, t0, t0 + 10 * ms) == UC_PENDING_WAIT,
		      "held 10 ms after the last out: wait");
		CHECK(uc_pending_due(TRUE, FALSE, t0, t0 + (UC_REFRESH_MS - 1) * ms) ==
		          UC_PENDING_WAIT,
		      "held, 1 ms before the window ends: wait");
		CHECK(uc_pending_due(TRUE, FALSE, t0, t0 + UC_REFRESH_MS * ms) == UC_PENDING_FLUSH,
		      "held, window over: flush");
		CHECK(uc_pending_due(TRUE, FALSE, t0, t0 + 60000 * ms) == UC_PENDING_FLUSH,
		      "held, scene still for a minute: flush");
		CHECK(uc_pending_due(TRUE, TRUE, t0, t0 + 1 * ms) == UC_PENDING_FLUSH,
		      "held, keyframe due: flush at once");
		CHECK(uc_pending_due(TRUE, FALSE, 0, t0) == UC_PENDING_FLUSH,
		      "held with nothing ever out: flush (doubt = send)");
		CHECK(uc_pending_due(TRUE, FALSE, t0, t0 - 1) == UC_PENDING_FLUSH,
		      "clock before the last out: flush (doubt = send)");

		CHECK(uc_pending_wait_us(FALSE, FALSE, t0, t0, 8 * ms) == 8 * ms,
		      "nothing held: the caller's wait");
		CHECK(uc_pending_wait_us(FALSE, TRUE, t0, t0, 8 * ms) == 8 * ms,
		      "nothing held, keyframe due: the caller's wait");
		CHECK(uc_pending_wait_us(TRUE, FALSE, t0, t0 + 100 * ms, 8 * ms) == 8 * ms,
		      "held, far from due: the caller's wait");
		CHECK(uc_pending_wait_us(TRUE, FALSE, t0, t0 + (UC_REFRESH_MS - 3) * ms, 8 * ms) ==
		          3 * ms,
		      "held, due in 3 ms: wait 3 ms");
		CHECK(uc_pending_wait_us(TRUE, FALSE, t0, t0 + UC_REFRESH_MS * ms, 8 * ms) == 0,
		      "held and due: no wait");
		CHECK(uc_pending_wait_us(TRUE, FALSE, 0, t0, 8 * ms) == 0,
		      "held, nothing ever out: no wait");
		CHECK(uc_pending_wait_us(TRUE, TRUE, t0, t0 + 1 * ms, 8 * ms) == 0,
		      "held, keyframe due: no wait (flushed at once)");
	}

	/* --- one stale restart per episode (UcStaleGate) ----------------------- */
	{
		UcStaleGate g = { 0 };
		int i, raised = 0;

		CHECK(uc_gate_may_raise(&g, 10), "first stale of the episode is raised");
		CHECK(!uc_gate_may_raise(&g, 10), "same episode, same buffers: not again");
		/* the review's case: our restart, then typing now and then whose
		 * frames are all held back or sent whole — never a loop */
		uc_gate_restarted(&g, 10);
		uc_gate_frame(&g, 10, FALSE); /* a frame already on its way */
		CHECK(!uc_gate_may_raise(&g, 11), "our own renegotiation is not a new episode");
		uc_gate_frame(&g, 11, FALSE); /* first frame of our restart, sent whole */
		for (i = 0; i < 100; i++) {
			uc_gate_frame(&g, 11, FALSE); /* a refresh, a frame with no reference */
			raised += uc_gate_may_raise(&g, 11);
		}
		CHECK(raised == 0, "idle or same frames for 100 pauses: no restart loop");
		/* a frame that REALLY changed opens a new episode */
		uc_gate_frame(&g, 11, TRUE);
		CHECK(uc_gate_may_raise(&g, 11), "after a real change: raised again, once");
		CHECK(!uc_gate_may_raise(&g, 11), "and only once");
		/* a real renegotiation (not ours) opens a new episode */
		CHECK(uc_gate_may_raise(&g, 12), "real renegotiation: a new episode");
		CHECK(!uc_gate_may_raise(&g, 12), "and only once");
		/* our restart: after its first new frame, a LATER renegotiation is real */
		uc_gate_restarted(&g, 12);
		uc_gate_frame(&g, 13, FALSE);
		CHECK(!uc_gate_may_raise(&g, 13), "our restart's buffers belong to the episode");
		CHECK(uc_gate_may_raise(&g, 14), "a later renegotiation is real");
		/* a restart that nothing raised (another wake-up) is not ours */
		{
			UcStaleGate h = { 0 };

			uc_gate_restarted(&h, 5);
			CHECK(!h.own_restart, "a wake-up with no stale is not our restart");
			CHECK(uc_gate_may_raise(&h, 6), "fresh gate raises");
		}
		/* a real change while our restart is under way closes it too */
		{
			UcStaleGate h = { 0 };

			uc_gate_may_raise(&h, 20);
			uc_gate_restarted(&h, 20);
			uc_gate_frame(&h, 20, TRUE);
			CHECK(!h.own_restart && uc_gate_may_raise(&h, 20),
			      "real change during our restart: a new episode");
		}
	}

	/* --- the cost, re-checked by windows ----------------------------------- */
	{
		UcCost c = { 0 };
		guint i, over = 0;

		/* a window that holds nothing back: the 3 ms ceiling decides */
		for (i = 0; i < UC_COST_FIRST - 1; i++)
			CHECK(!uc_cost_add(&c, 100000, FALSE), "no verdict before the first window closes");
		CHECK(uc_cost_add(&c, 100000, FALSE), "first window slow: over the ceiling");
		uc_cost_reset(&c);
		for (i = 0; i < UC_COST_FIRST; i++)
			over += uc_cost_add(&c, 500, FALSE);
		CHECK(over == 0 && c.windows == 1, "first window cheap: no verdict");
		/* later the card turns slow: caught by the next window, not never */
		for (i = 0; i < UC_COST_EVERY - 1; i++)
			over += uc_cost_add(&c, UC_COST_MAX_US * 2, FALSE);
		CHECK(over == 0, "no verdict before the second window closes");
		CHECK(uc_cost_add(&c, UC_COST_MAX_US * 2, FALSE) && c.windows == 2,
		      "second window slow: over the ceiling");
		CHECK(c.last_mean_us > UC_COST_MAX_US, "the mean is reported");
		CHECK(c.last_held == 0 && c.last_n == UC_COST_EVERY, "the window's yield is reported");
		/* a window whose mean equals the ceiling is not over */
		for (i = 0; i < UC_COST_EVERY; i++)
			over = uc_cost_add(&c, UC_COST_MAX_US, FALSE);
		CHECK(!over, "mean equal to the ceiling is allowed");
		/* one spike in a cheap window does not switch it off */
		for (i = 0; i < UC_COST_EVERY; i++)
			over = uc_cost_add(&c, i == 5 ? 100000 : 500, FALSE);
		CHECK(!over, "one spike of 100 ms in 300 cheap looks is allowed");
	}
	/* --- ⭐ the cost against what it buys (`[M]` rete11-kde, 15 Oct 2026) ---- */
	{
		UcCost c = { 0 };
		guint i, over = 0;

		/* F-003 kde/firefox, 09:08: 7.22 ms mean, 12 of 30 held back ⇒ ON */
		for (i = 0; i < UC_COST_FIRST; i++)
			over += uc_cost_add(&c, 7220, i < 12);
		CHECK(over == 0 && c.last_held == 12, "7.2 ms holding back 12/30: stays on");
		/* c16002u99, strike 3: 9.29 ms, 25 of 30 held back ⇒ ON */
		uc_cost_reset(&c);
		for (i = 0; i < UC_COST_FIRST; i++)
			over += uc_cost_add(&c, 9290, i < 25);
		CHECK(over == 0, "9.3 ms holding back 25/30: stays on");
		/* c16002u2, 09:34: 6.69 ms, 1 held back ⇒ OFF (costly, sparing nothing) */
		uc_cost_reset(&c);
		for (i = 0; i < UC_COST_FIRST; i++)
			over += uc_cost_add(&c, 6690, i < 1);
		CHECK(over == 1, "6.7 ms holding back 1/30: off");
		/* the yield threshold: exactly 1/UC_YIELD_DIV keeps it on, one less does not */
		CHECK(!uc_cost_over(5000.0, UC_COST_EVERY / UC_YIELD_DIV, UC_COST_EVERY),
		      "a quarter held back at 5 ms: on");
		CHECK(uc_cost_over(5000.0, UC_COST_EVERY / UC_YIELD_DIV - 1, UC_COST_EVERY),
		      "just under a quarter at 5 ms: off");
		/* the hard ceiling: everything held back does not save a look of 10+ ms */
		CHECK(uc_cost_over(UC_COST_HARD_US + 1.0, 30, 30), "above the hard ceiling: off");
		CHECK(!uc_cost_over(UC_COST_HARD_US, 30, 30), "at the hard ceiling: on");
		CHECK(!uc_cost_over(UC_COST_MAX_US - 1.0, 0, 30), "cheap and useless: on");
		/* the counter of the open window starts again at each window */
		uc_cost_reset(&c);
		for (i = 0; i < UC_COST_FIRST; i++)
			(void)uc_cost_add(&c, 500, TRUE);
		for (i = 0; i < UC_COST_EVERY; i++)
			over = uc_cost_add(&c, 6000, FALSE);
		CHECK(over && c.last_held == 0, "held of the previous window does not carry over");
	}

	/* --- the switch: soft off until a renegotiation, hard after three ----- */
	{
		UcSwitch sw = { 0 };
		gboolean re;
		const uint64_t T = 1000000000u, S = (uint64_t)UC_REARM_MS * 1000u;

		CHECK(uc_switch_allows(&sw, 1, T, &re) && !re, "fresh switch allows");
		uc_switch_strike(&sw, 1, T, FALSE);
		CHECK(!uc_switch_allows(&sw, 1, T, &re) && !re, "off for the same generation");
		CHECK(!uc_switch_allows(&sw, 1, T + 100 * S, &re) && !re,
		      "a buffer switch-off does not re-arm with time");
		CHECK(uc_switch_allows(&sw, 2, T, &re) && re, "a renegotiation re-arms");
		CHECK(uc_switch_allows(&sw, 2, T, &re) && !re, "re-armed is said once");
		uc_switch_strike(&sw, 2, T, TRUE);
		CHECK(!uc_switch_allows(&sw, 2, T + S - 1, &re) && !re,
		      "a cost switch-off holds until UC_REARM_MS");
		CHECK(!sw.hard && uc_switch_allows(&sw, 2, T + S, &re) && re,
		      "second strike (cost): re-armed by time, same generation");
		CHECK(uc_switch_allows(&sw, 2, T + S, &re) && !re, "re-armed by time is said once");
		uc_switch_strike(&sw, 2, T + S, TRUE);
		CHECK(sw.hard, "third strike is hard");
		CHECK(!uc_switch_allows(&sw, 4, T, &re) && !re, "hard off: a renegotiation does not re-arm");
		CHECK(!uc_switch_allows(&sw, 2, T + 100 * S, &re) && !re, "hard off: time does not re-arm");
		CHECK(!uc_switch_allows(&sw, 99, T, NULL), "hard off, no flag pointer");
		/* a clock that goes backwards does not re-arm */
		{
			UcSwitch b = { 0 };

			uc_switch_strike(&b, 7, T, TRUE);
			CHECK(!uc_switch_allows(&b, 7, T - 1, &re) && !re, "earlier instant: still off");
		}
	}

	/* --- forget ------------------------------------------------------------ */
	uc_forget(&u);
	r = (UcRect){ 10, 10, 20, 20 };
	CHECK(!uc_same(&u, a, w, h, stride, &r, 1), "forgotten reference says changed");

	uc_free(&u);
	free(a);
	free(b);
	if (failures) {
		fprintf(stderr, "unchanged.h: %d case(s) FAILED\n", failures);
		return 1;
	}
	printf("unchanged.h: all cases passed\n");
	return 0;
}
