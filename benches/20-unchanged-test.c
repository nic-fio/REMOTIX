/*
 * 20-unchanged-test.c — desk test of the pure half of the «unchanged» filter
 * (`src/unchanged.h`, 15 Oct 2026).  No box, no PipeWire: synthetic frames.
 *
 * Build and run:  make -C src bench-unchanged && ./benches/20-unchanged-test
 * Exit 0 = every case passed; otherwise the failing case is named.
 *
 * ⚠ What it does NOT cover: the merge of the damage in the slot
 *   (`on_process`, capture.c) and the 250 ms / bypass / cost guards
 *   (`unchanged_judge`), which live in capture.c and need a stream.
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
