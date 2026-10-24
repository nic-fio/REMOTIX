/*
 * 23-colors709-edge-test.c — desk test of the LAST rows of the RGB → 4:2:0
 * conversion (`src/colors709.c`), and the arithmetic of F-011's green last row.
 * (15 Oct 2026.)  No box, no card: synthetic frames.
 *
 * Build and run:  make -C src test-colors709
 *                 (twice: SSE2, and the plain C with COLORS709_NO_SIMD)
 * Exit 0 = every case passed; otherwise the failing case is named.
 *
 * ⭐ THE QUESTION.  F-011: on Chrome (all four desktops) the LAST row of the
 *    remote picture keeps its luma and has U,V pulled toward ZERO by a quarter
 *    (gnome dark → (0,57,0)).  Is it the server's conversion — a padding row of
 *    zeros read or averaged into the last chroma row?
 *
 * ⭐ THE ANSWER: NO, and the proof does not even need a stream.
 *   1. In 4:2:0 the last TWO luma rows (2062 and 2063 of a 2064-row picture)
 *      share ONE chroma sample (row 1031).  `[M]` the Chrome photos of run
 *      20261014-194821 (3824x2064, a multiple of 16: no padding, no crop in
 *      the SPS): row 2062 is clean on all four desktops, row 2063 is pulled.
 *      ⇒ No 4:2:0 stream can carry that picture: if the encoder's last chroma
 *      row were wrong, row 2062 would be wrong too.  The bleed is made AFTER
 *      the decoder, where 4:2:0 chroma is upsampled to the luma rows.
 *   2. The size of the pull is EXACTLY a vertical bilinear tap: luma row 2k+1
 *      takes 3/4 of chroma k and 1/4 of chroma k+1; for the last row chroma
 *      k+1 is BELOW the picture, and reading it as 0 (instead of clamping to
 *      the edge) gives c·3/4.  `model()` below rebuilds the four photo colours
 *      from the clean row above with that formula: within ±4 levels on every
 *      channel, and gnome (0,57,0) and xfce (0,24,0) to the unit.
 *   3. The server's CPU conversion (this file's cases 1-3) gives the right
 *      last chroma row: greys stay 128 to the last sample, flat colours are
 *      flat to the last sample, and the last chroma row is the tent over rows
 *      a-3, a-2, a-1 with the edge CLAMPED (no zero row).  The GPU route
 *      (`convert_on_gpu`) is excluded by point 1 alone, whatever it does.
 *
 * ⚠ What it does NOT cover: Chrome itself (the bleed is in its YUV → RGB of
 *   `texImage2D(VideoFrame)`; the page's own texture has CLAMP_TO_EDGE), and
 *   the VA-API VPP, which needs a card.
 *
 * ⚠ AND THE CURES OF THE PAGE (24 Oct 2026, `DECISIONS-11.md` §11.41, cures (a) (b) (c)
 *   of `page.html`) DO NOT CONTRADICT THIS TEST: they live in the browser's side, they
 *   clamp the row the renderer reads, and this file proves exactly that the stream is
 *   clean and that the bleed is the renderer's tap.  A green `chroma_bleed` of F-011 on
 *   Chrome is the page's merit; a red one here would be the server's.
 */
#include "../src/colors709.h"

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int failures;

#define CHECK(cond, ...)                                                       \
	do {                                                                   \
		if (!(cond)) {                                                 \
			fprintf(stderr, "FAIL line %d: ", __LINE__);           \
			fprintf(stderr, __VA_ARGS__);                          \
			fputc('\n', stderr);                                   \
			failures++;                                            \
		}                                                              \
	} while (0)

typedef struct {
	uint32_t l, a;
	uint8_t *px, *y, *uv;
} Frame;

static Frame open_frame(uint32_t l, uint32_t a)
{
	Frame f = { l, a, malloc((size_t)l * a * 4), malloc((size_t)l * a),
	            malloc((size_t)l * a / 2) };
	if (!f.px || !f.y || !f.uv) {
		fprintf(stderr, "no memory for %ux%u\n", l, a);
		exit(2);
	}
	return f;
}

static void close_frame(Frame *f)
{
	free(f->px);
	free(f->y);
	free(f->uv);
}

static void put(Frame *f, uint32_t x, uint32_t r, const uint8_t rgb[3], Colori709Ordine o)
{
	uint8_t *p = f->px + ((size_t)r * f->l + x) * 4;
	p[o == COLORI709_RGBX ? 0 : 2] = rgb[0];
	p[1] = rgb[1];
	p[o == COLORI709_RGBX ? 2 : 0] = rgb[2];
	p[3] = 0xff;
}

static bool convert(Frame *f, Colori709Ordine o)
{
	return colors709_to_nv12(f->px, f->l * 4, f->l, f->a, o, f->y, f->l, f->uv, f->l);
}

/* The four colours of the row ABOVE the green one, and the green one, `[M]` medians
 * of the Chrome photos 01-tela-0.png of run 20261014-194821 (3824x2064). */
static const struct {
	const char *desk;
	uint8_t above[3], photo[3];
} PHOTO[] = {
	{ "gnome", { 34, 33, 38 }, { 0, 57, 0 } },
	{ "kde", { 199, 95, 136 }, { 121, 125, 68 } },
	{ "lxqt", { 236, 236, 236 }, { 179, 255, 169 } },
	{ "xfce", { 0, 0, 2 }, { 0, 24, 0 } },
};

static const uint32_t SIZES[][2] = {
	{ 3824, 2064 }, /* the Chrome canvas of the photos */
	{ 3776, 2016 }, /* the Firefox one */
	{ 1920, 1080 }, /* not a multiple of 16: the card pads to 1088 */
	{ 66, 34 },     /* tail of the SIMD loop + odd count of chroma rows */
	{ 2, 2 },
};

/* 1. Flat colours: every chroma sample, the last row included, is the same. */
static void case_flat(Colori709Ordine o)
{
	for (size_t s = 0; s < sizeof SIZES / sizeof SIZES[0]; s++) {
		Frame f = open_frame(SIZES[s][0], SIZES[s][1]);
		for (size_t k = 0; k < sizeof PHOTO / sizeof PHOTO[0]; k++) {
			for (uint32_t r = 0; r < f.a; r++)
				for (uint32_t x = 0; x < f.l; x++)
					put(&f, x, r, PHOTO[k].above, o);
			CHECK(convert(&f, o), "convert %ux%u", f.l, f.a);
			const uint8_t u0 = f.uv[0], v0 = f.uv[1], y0 = f.y[0];
			uint32_t bad = 0;
			for (uint32_t r = 0; r < f.a / 2; r++)
				for (uint32_t x = 0; x < f.l / 2; x++) {
					const uint8_t *c = f.uv + (size_t)r * f.l + 2 * x;
					bad += c[0] != u0 || c[1] != v0;
				}
			for (size_t i = 0; i < (size_t)f.l * f.a; i++)
				bad += f.y[i] != y0;
			CHECK(!bad, "%s flat %ux%u order %d: %u samples differ from the first",
			      PHOTO[k].desk, f.l, f.a, (int)o, bad);
		}
		close_frame(&f);
	}
}

/* 2. Greys, a DIFFERENT grey on every row: U and V must be exactly 128
 *    everywhere.  A zero row read below the picture (the F-011 suspicion)
 *    would pull the last chroma row under 128. */
static void case_greys(Colori709Ordine o)
{
	for (size_t s = 0; s < sizeof SIZES / sizeof SIZES[0]; s++) {
		Frame f = open_frame(SIZES[s][0], SIZES[s][1]);
		for (uint32_t r = 0; r < f.a; r++) {
			uint8_t g = (uint8_t)(r * 97u + 13u), rgb[3] = { g, g, g };
			for (uint32_t x = 0; x < f.l; x++)
				put(&f, x, r, rgb, o);
		}
		CHECK(convert(&f, o), "convert %ux%u", f.l, f.a);
		uint32_t bad = 0;
		for (uint32_t r = 0; r < f.a / 2; r++)
			for (uint32_t x = 0; x < f.l; x++)
				bad += f.uv[(size_t)r * f.l + x] != 128;
		CHECK(!bad, "greys %ux%u order %d: %u chroma bytes are not 128", f.l, f.a,
		      (int)o, bad);
		close_frame(&f);
	}
}

/* 3. A bar on the last row only: the last chroma row is the tent 1-3-3-1 over
 *    rows a-3, a-2, a-1, and a-1 again (the edge CLAMPED) ⇒ weights 1/8 the
 *    background, 3/8 the background, 4/8 the bar.  With a zero row in place
 *    of the clamp it would be 3/8 the bar and 1/8 zero. */
static void case_bar(Colori709Ordine o)
{
	static const uint8_t back[3] = { 34, 33, 38 }, bar[3] = { 220, 40, 30 };
	Frame f = open_frame(64, 16);
	Frame g = open_frame(2, 2);
	for (uint32_t r = 0; r < f.a; r++)
		for (uint32_t x = 0; x < f.l; x++)
			put(&f, x, r, r == f.a - 1 ? bar : back, o);
	CHECK(convert(&f, o), "convert bar");
	/* the chroma of the two pure colours, from 2x2 flat frames */
	int cu[2], cv[2];
	for (int k = 0; k < 2; k++) {
		for (uint32_t i = 0; i < 4; i++)
			put(&g, i & 1, i >> 1, k ? bar : back, o);
		CHECK(convert(&g, o), "convert 2x2");
		cu[k] = g.uv[0] - 128;
		cv[k] = g.uv[1] - 128;
	}
	const uint8_t *last = f.uv + (size_t)(f.a / 2 - 1) * f.l;
	const double eu = 128 + (4.0 * cu[0] + 4.0 * cu[1]) / 8.0;
	const double ev = 128 + (4.0 * cv[0] + 4.0 * cv[1]) / 8.0;
	CHECK(fabs(last[0] - eu) <= 1.0 && fabs(last[1] - ev) <= 1.0,
	      "bar order %d: last chroma (%u,%u), expected the clamped tent (%.1f,%.1f)",
	      (int)o, last[0], last[1], eu, ev);
	/* and the chroma row above it does not see the bar: rows a-5 … a-2 */
	const uint8_t *above = last - f.l;
	CHECK(above[0] == 128 + cu[0] && above[1] == 128 + cv[0],
	      "bar order %d: the row above the last chroma row changed (%u,%u)", (int)o,
	      above[0], above[1]);
	close_frame(&f);
	close_frame(&g);
}

/* BT.709 limited → RGB, as a decoder/renderer does it. */
static void to_rgb(double Y, double U, double V, int rgb[3])
{
	const double y = (Y - 16) / 219, u = (U - 128) / 224, v = (V - 128) / 224;
	const double r = y + 1.5748 * v, b = y + 1.8556 * u;
	const double g = (y - 0.2126 * r - 0.0722 * b) / 0.7152;
	const double c[3] = { r, g, b };
	for (int i = 0; i < 3; i++) {
		double t = round(c[i] * 255);
		rgb[i] = t < 0 ? 0 : t > 255 ? 255 : (int)t;
	}
}

/* 4. The model of the bleed: the clean colour, converted by OUR conversion,
 *    upsampled with the bilinear tap 3/4·c[k] + 1/4·c[k+1] and c[k+1] = 0
 *    (stored zero, the row below the picture) → the photo's green row.
 *    And the control: c[k+1] clamped to c[k] → the clean colour again. */
static void case_model(void)
{
	Frame g = open_frame(2, 2);
	for (size_t k = 0; k < sizeof PHOTO / sizeof PHOTO[0]; k++) {
		for (uint32_t i = 0; i < 4; i++)
			put(&g, i & 1, i >> 1, PHOTO[k].above, COLORI709_RGBX);
		CHECK(convert(&g, COLORI709_RGBX), "convert 2x2");
		const double Y = g.y[0], U = g.uv[0], V = g.uv[1];
		int bleed[3], clamp[3], worst = 0, worst_c = 0;
		to_rgb(Y, 0.75 * U + 0.25 * 0, 0.75 * V + 0.25 * 0, bleed);
		to_rgb(Y, 0.75 * U + 0.25 * U, 0.75 * V + 0.25 * V, clamp);
		for (int i = 0; i < 3; i++) {
			int d = abs(bleed[i] - PHOTO[k].photo[i]);
			int e = abs(clamp[i] - PHOTO[k].above[i]);
			worst = d > worst ? d : worst;
			worst_c = e > worst_c ? e : worst_c;
		}
		printf("  model %-5s row above (%3u,%3u,%3u) YUV (%3.0f,%3.0f,%3.0f) → "
		       "tap on a zero row (%3d,%3d,%3d), photo (%3u,%3u,%3u), off by %d; "
		       "clamped (%3d,%3d,%3d)\n",
		       PHOTO[k].desk, PHOTO[k].above[0], PHOTO[k].above[1], PHOTO[k].above[2],
		       Y, U, V, bleed[0], bleed[1], bleed[2], PHOTO[k].photo[0],
		       PHOTO[k].photo[1], PHOTO[k].photo[2], worst, clamp[0], clamp[1],
		       clamp[2]);
		CHECK(worst <= 4, "model %s: the zero-row tap misses the photo by %d",
		      PHOTO[k].desk, worst);
		CHECK(worst_c <= 3, "model %s: the clamped tap is not the clean colour (%d)",
		      PHOTO[k].desk, worst_c);
	}
	close_frame(&g);
}

int main(void)
{
#ifdef COLORS709_NO_SIMD
	printf("23-colors709-edge-test (plain C)\n");
#else
	printf("23-colors709-edge-test\n");
#endif
	for (int o = COLORI709_BGRX; o <= COLORI709_RGBX; o++) {
		case_flat((Colori709Ordine)o);
		case_greys((Colori709Ordine)o);
		case_bar((Colori709Ordine)o);
	}
	case_model();
	if (failures) {
		printf("  ⛔ %d check(s) failed\n", failures);
		return 1;
	}
	printf("  OK: the last chroma row is right (flat, greys, clamped tent), and the "
	       "green row of F-011 is the renderer's tap on a zero row\n");
	return 0;
}
