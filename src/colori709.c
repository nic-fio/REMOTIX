/*
 * colori709.c — the BGRx → YUV 4:2:0 BT.709 limited conversion, without
 *               libswscale.  The why and the rules are in `colori709.h`.
 *
 * ---------------------------------------------------------------------------
 * ⭐ THE COEFFICIENTS, and where they come from
 *
 * BT.709: Kr = 0.2126 · Kg = 0.7152 · Kb = 0.0722.  From full-range RGB (0-255):
 *
 *   Y  = 16  + 219/255 · (Kr R + Kg G + Kb B)
 *   Cb = 128 + 224/255 · (B − Y') / (2 (1 − Kb))
 *   Cr = 128 + 224/255 · (R − Y') / (2 (1 − Kr))
 *
 * in 15-bit fixed point (`SCALA`: 15 and not 16 because each coefficient
 * must fit in an `int16` — the instruction is `pmaddwd`), rounded to
 * nearest.  ⛔ And two lines are NOT plain rounding, on purpose:
 *   - `VG` is 13072 and not 13073: with pure rounding the three of Cr
 *     sum to +1, and a grey would come out with a tint nobody asked
 *     for.  This way each chroma triple sums to 0 and grey is exactly 128,
 *     `[M]` for all 256 greys;
 *   - luma sums to 28142 = 219/255 · 32768: white gives 235 and black 16,
 *     `[M]` identical to swscale together with the three primaries.
 *
 * ---------------------------------------------------------------------------
 * ⭐ THE SHAPE: one row at a time — luma at once, and the horizontal pair
 *    sums into a ring of four rows from which chroma comes out (the filter is
 *    swscale's: see `croma()`).
 *
 * ⭐ THE SPEED: SSE2, which on x86-64 is ALWAYS there (it is in the ABI), so no
 *    run-time choice and no branch that a machine never takes.  Elsewhere
 *    (aarch64, …) the same computation in plain C, with the SAME coefficients
 *    and the same roundings: the bytes come out equal.
 *    ⛔ At -O2 GCC 14 did NOT vectorise the plain C: `[M]` 30 Sep 2026 at
 *       3840x2160 the C took 13.7 ms against 13.1 for sws_scale — and the
 *       conversion is CPU work before every frame.
 */
#include "colori709.h"

#include <stddef.h>
#include <stdlib.h>
#include <string.h>

#if defined(__SSE2__) && !defined(COLORI709_SENZA_SIMD) /* the second: for the bench */
#include <emmintrin.h>
#define COLORI709_SSE2 1
#endif

#define SCALA 15

/* Y — the sum is 28142: white → 235. */
#define YR 5983
#define YG 20127
#define YB 2032
/* Cb — sum 0. */
#define UR (-3298)
#define UG (-11094)
#define UB 14392
/* Cr — sum 0 (⛔ see above: VG corrected by one). */
#define VR 14392
#define VG (-13072)
#define VB (-1320)

/* The three coefficients placed at the bytes' positions: position 0, 1, 2, 3 of the pixel. */
typedef struct {
	int16_t y[4], u[4], v[4];
} Coeff;

static Coeff coefficienti(Colori709Ordine ordine)
{
	Coeff c;
	const int ir = ordine == COLORI709_RGBX ? 0 : 2;
	const int ib = ordine == COLORI709_RGBX ? 2 : 0;
	memset(&c, 0, sizeof c);
	c.y[ir] = YR; c.y[1] = YG; c.y[ib] = YB;
	c.u[ir] = UR; c.u[1] = UG; c.u[ib] = UB;
	c.v[ir] = VR; c.v[1] = VG; c.v[ib] = VB;
	return c;
}

/*
 * ⭐ THE ROW: luma (written at once) and, for each pair of pixels, the
 *    byte-by-byte sum of the two (0-510, four `int16` per chroma sample, the
 *    fourth is the x byte and weighs zero).
 *
 *   Y = (k · Σ c·byte + (16k << 15) + ½) >> 15,   k = 1 at 8 bits, 4 at 10 bits
 *   ⚠ at 10 bits the matrix is computed at 10 bits (219·4 = 876 levels), not 8
 *     bits shifted by two: it is what swscale did towards `yuv420p10le`.
 */
static void riga(const uint8_t *restrict px, uint32_t l, const Coeff *c, int prof10, int semi,
                 void *restrict yv, int16_t *restrict somme)
{
	const int32_t k = prof10 ? 4 : 1;
	const int32_t off = ((16 * k) << SCALA) + (1 << (SCALA - 1));
	const int sp = prof10 && semi ? 6 : 0; /* P010: the ten bits at the TOP */
	uint32_t x = 0;
#ifdef COLORI709_SSE2
	const __m128i zero = _mm_setzero_si128();
	const __m128i cy = _mm_setr_epi16(c->y[0], c->y[1], c->y[2], c->y[3], c->y[0], c->y[1],
	                                  c->y[2], c->y[3]);
	const __m128i voff = _mm_set1_epi32(off);
	for (; x + 16 <= l; x += 16) {
		__m128i y32[4];
		for (int j = 0; j < 4; j++) {
			__m128i p = _mm_loadu_si128((const __m128i *) (px + 4 * (x + 4 * j)));
			__m128i lo = _mm_unpacklo_epi8(p, zero); /* pixels 0,1 in 16 bits */
			__m128i hi = _mm_unpackhi_epi8(p, zero); /* pixel 2,3 */
			__m128i ml = _mm_madd_epi16(lo, cy);     /* [0bg, 0rx, 1bg, 1rx] */
			__m128i mh = _mm_madd_epi16(hi, cy);
			__m128 a = _mm_castsi128_ps(ml), b = _mm_castsi128_ps(mh);
			__m128i pari = _mm_castps_si128(_mm_shuffle_ps(a, b, _MM_SHUFFLE(2, 0, 2, 0)));
			__m128i disp = _mm_castps_si128(_mm_shuffle_ps(a, b, _MM_SHUFFLE(3, 1, 3, 1)));
			__m128i s = _mm_add_epi32(pari, disp);
			if (prof10)
				s = _mm_slli_epi32(s, 2);
			y32[j] = _mm_srai_epi32(_mm_add_epi32(s, voff), SCALA);
			/* the pair sums: low half + high half of each `lo`/`hi` */
			__m128i sl = _mm_add_epi16(lo, _mm_srli_si128(lo, 8));
			__m128i sh = _mm_add_epi16(hi, _mm_srli_si128(hi, 8));
			_mm_storeu_si128((__m128i *) (somme + 4 * ((x + 4 * j) / 2)),
			                 _mm_unpacklo_epi64(sl, sh));
		}
		__m128i y16a = _mm_packs_epi32(y32[0], y32[1]);
		__m128i y16b = _mm_packs_epi32(y32[2], y32[3]);
		if (prof10) {
			uint16_t *y = (uint16_t *) yv + x;
			_mm_storeu_si128((__m128i *) y, _mm_slli_epi16(y16a, sp));
			_mm_storeu_si128((__m128i *) (y + 8), _mm_slli_epi16(y16b, sp));
		} else {
			_mm_storeu_si128((__m128i *) ((uint8_t *) yv + x), _mm_packus_epi16(y16a, y16b));
		}
	}
#endif
	for (; x < l; x += 2) {
		const uint8_t *p = px + 4 * x;
		int32_t y0 = c->y[0] * p[0] + c->y[1] * p[1] + c->y[2] * p[2];
		int32_t y1 = c->y[0] * p[4] + c->y[1] * p[5] + c->y[2] * p[6];
		y0 = (k * y0 + off) >> SCALA;
		y1 = (k * y1 + off) >> SCALA;
		if (prof10) {
			((uint16_t *) yv)[x] = (uint16_t) (y0 << sp);
			((uint16_t *) yv)[x + 1] = (uint16_t) (y1 << sp);
		} else {
			((uint8_t *) yv)[x] = (uint8_t) y0;
			((uint8_t *) yv)[x + 1] = (uint8_t) y1;
		}
		for (int j = 0; j < 4; j++)
			somme[4 * (x / 2) + j] = (int16_t) (p[j] + p[4 + j]);
	}
}

/*
 * ⭐ THE CHROMA: the same shape as swscale, measured with an impulse (`[M]` 30 Sep
 *    2026, ffmpeg 7.1.5, `SWS_BILINEAR`, same size):
 *      - horizontally the average of TWO pixels (a single column → 1/2);
 *      - vertically a tent over FOUR rows, weights 1-3-3-1 / 8, with the
 *        rows outside the image taken equal to the first/last (an impulse
 *        on row 0 gives 4/8 to chroma 0, on row 1 gives 3/8 and 1/8).
 *    Here: pair sums (x2) times 1-3-3-1 (x8) ⇒ the whole weighs 16, that is
 *    four more bits of scale.
 * ⛔ With the 2x2 average instead of the tent the gap against swscale was `[M]`
 *    up to 10 chroma levels on 5 % of the samples (the edges of text): the
 *    matrix was right and the filter was not, and «the colours match» means
 *    both.  With the tent: at most 1 level (roundings), `[M]` in the bench.
 */
static void croma(const int16_t *const s[4], uint32_t lc, const Coeff *c, int prof10, int semi,
                  void *restrict uv, void *restrict vv)
{
	const int32_t k = prof10 ? 4 : 1;
	const int sh = SCALA + 4;
	const int32_t off = ((128 * k) << sh) + (1 << (sh - 1));
	const int16_t *a = s[0], *b = s[1], *cc = s[2], *d = s[3];
	uint32_t i = 0;
#ifdef COLORI709_SSE2
	const __m128i cu = _mm_setr_epi16(c->u[0], c->u[1], c->u[2], c->u[3], c->u[0], c->u[1],
	                                  c->u[2], c->u[3]);
	const __m128i cv = _mm_setr_epi16(c->v[0], c->v[1], c->v[2], c->v[3], c->v[0], c->v[1],
	                                  c->v[2], c->v[3]);
	const __m128i voff = _mm_set1_epi32(off);
	for (; i + 8 <= lc; i += 8) {
		__m128i u32[2], v32[2];
		for (int h = 0; h < 2; h++) {
			__m128i mu[2], mv[2];
			for (int j = 0; j < 2; j++) {
				size_t o = 4 * (i + 4 * h + 2 * j);
				__m128i w = _mm_add_epi16(
				    _mm_add_epi16(_mm_loadu_si128((const __m128i *) (a + o)),
				                  _mm_loadu_si128((const __m128i *) (d + o))),
				    _mm_mullo_epi16(_mm_set1_epi16(3),
				                    _mm_add_epi16(_mm_loadu_si128((const __m128i *) (b + o)),
				                                  _mm_loadu_si128((const __m128i *) (cc + o)))));
				mu[j] = _mm_madd_epi16(w, cu);
				mv[j] = _mm_madd_epi16(w, cv);
			}
			__m128 ua = _mm_castsi128_ps(mu[0]), ub = _mm_castsi128_ps(mu[1]);
			__m128 va = _mm_castsi128_ps(mv[0]), vb = _mm_castsi128_ps(mv[1]);
			__m128i us = _mm_add_epi32(_mm_castps_si128(_mm_shuffle_ps(ua, ub, _MM_SHUFFLE(2, 0, 2, 0))),
			                           _mm_castps_si128(_mm_shuffle_ps(ua, ub, _MM_SHUFFLE(3, 1, 3, 1))));
			__m128i vs = _mm_add_epi32(_mm_castps_si128(_mm_shuffle_ps(va, vb, _MM_SHUFFLE(2, 0, 2, 0))),
			                           _mm_castps_si128(_mm_shuffle_ps(va, vb, _MM_SHUFFLE(3, 1, 3, 1))));
			if (prof10) {
				us = _mm_slli_epi32(us, 2);
				vs = _mm_slli_epi32(vs, 2);
			}
			u32[h] = _mm_srai_epi32(_mm_add_epi32(us, voff), sh);
			v32[h] = _mm_srai_epi32(_mm_add_epi32(vs, voff), sh);
		}
		__m128i u16 = _mm_packs_epi32(u32[0], u32[1]); /* 8 samples */
		__m128i v16 = _mm_packs_epi32(v32[0], v32[1]);
		if (prof10 && semi) {
			uint16_t *o = (uint16_t *) uv + 2 * i;
			_mm_storeu_si128((__m128i *) o, _mm_slli_epi16(_mm_unpacklo_epi16(u16, v16), 6));
			_mm_storeu_si128((__m128i *) (o + 8), _mm_slli_epi16(_mm_unpackhi_epi16(u16, v16), 6));
		} else if (prof10) {
			_mm_storeu_si128((__m128i *) ((uint16_t *) uv + i), u16);
			_mm_storeu_si128((__m128i *) ((uint16_t *) vv + i), v16);
		} else if (semi) {
			__m128i u8 = _mm_packus_epi16(u16, u16), v8 = _mm_packus_epi16(v16, v16);
			_mm_storeu_si128((__m128i *) ((uint8_t *) uv + 2 * i), _mm_unpacklo_epi8(u8, v8));
		} else {
			_mm_storel_epi64((__m128i *) ((uint8_t *) uv + i), _mm_packus_epi16(u16, u16));
			_mm_storel_epi64((__m128i *) ((uint8_t *) vv + i), _mm_packus_epi16(v16, v16));
		}
	}
#endif
	for (; i < lc; i++) {
		int32_t U = 0, V = 0;
		for (int j = 0; j < 4; j++) {
			int32_t w = a[4 * i + j] + 3 * (b[4 * i + j] + cc[4 * i + j]) + d[4 * i + j];
			U += c->u[j] * w;
			V += c->v[j] * w;
		}
		U = (k * U + off) >> sh;
		V = (k * V + off) >> sh;
		if (prof10 && semi) {
			((uint16_t *) uv)[2 * i] = (uint16_t) (U << 6);
			((uint16_t *) uv)[2 * i + 1] = (uint16_t) (V << 6);
		} else if (prof10) {
			((uint16_t *) uv)[i] = (uint16_t) U;
			((uint16_t *) vv)[i] = (uint16_t) V;
		} else if (semi) {
			((uint8_t *) uv)[2 * i] = (uint8_t) U;
			((uint8_t *) uv)[2 * i + 1] = (uint8_t) V;
		} else {
			((uint8_t *) uv)[i] = (uint8_t) U;
			((uint8_t *) vv)[i] = (uint8_t) V;
		}
	}
}

static bool converti(const uint8_t *pixel, uint32_t passo, uint32_t l, uint32_t a,
                     Colori709Ordine ordine, int prof10, int semi,
                     uint8_t *y, uint32_t py, uint8_t *u, uint32_t pu, uint8_t *v, uint32_t pv)
{
	if (!pixel || !y || !u || (!semi && !v) || !l || !a || (l & 1) || (a & 1))
		return false;
	if (!passo)
		passo = l * 4;
	const Coeff c = coefficienti(ordine);
	const uint32_t lc = l / 2;
	/* The ring of sums: four rows, four `int16` per chroma sample
	 * (61 KB at 3840). */
	int16_t *anello = malloc(sizeof(int16_t) * 16u * lc);
	if (!anello)
		return false;
	const int16_t *s[4];

	for (uint32_t r = 0; r < a; r++) {
		riga(pixel + (size_t) r * passo, l, &c, prof10, semi, y + (size_t) r * py,
		     anello + (size_t) (r & 3u) * 4u * lc);
		/* Chroma k wants rows 2k-1 … 2k+2: it is emitted when row 2k+2
		 * arrives, and the last one at the end of the image (row 2k+2 outside
		 * ⇒ the last row).  ⚠ With a = 2 chroma 0 is emitted twice, identical:
		 * harmless. */
		bool ultima = (r == a - 1);
		if ((r >= 2 && !(r & 1u)) || ultima) {
			uint32_t kc = ultima ? a / 2u - 1u : (r - 2u) / 2u;
			for (int j = 0; j < 4; j++) {
				int64_t rr = (int64_t) 2 * kc - 1 + j;
				if (rr < 0)
					rr = 0;
				if (rr > (int64_t) a - 1)
					rr = (int64_t) a - 1;
				s[j] = anello + (size_t) ((uint32_t) rr & 3u) * 4u * lc;
			}
			croma(s, lc, &c, prof10, semi, u + (size_t) kc * pu,
			      semi ? NULL : v + (size_t) kc * pv);
		}
	}
	free(anello);
	return true;
}

bool colori709_a_i420(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                      uint32_t altezza, Colori709Ordine ordine,
                      uint8_t *y, uint32_t passo_y,
                      uint8_t *u, uint32_t passo_u,
                      uint8_t *v, uint32_t passo_v)
{
	return converti(pixel, passo, larghezza, altezza, ordine, 0, 0,
	                y, passo_y, u, passo_u, v, passo_v);
}

bool colori709_a_i420_10(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                         uint32_t altezza, Colori709Ordine ordine,
                         uint16_t *y, uint32_t passo_y,
                         uint16_t *u, uint32_t passo_u,
                         uint16_t *v, uint32_t passo_v)
{
	return converti(pixel, passo, larghezza, altezza, ordine, 1, 0,
	                (uint8_t *) y, passo_y, (uint8_t *) u, passo_u,
	                (uint8_t *) v, passo_v);
}

bool colori709_a_nv12(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                      uint32_t altezza, Colori709Ordine ordine,
                      uint8_t *y, uint32_t passo_y,
                      uint8_t *uv, uint32_t passo_uv)
{
	return converti(pixel, passo, larghezza, altezza, ordine, 0, 1,
	                y, passo_y, uv, passo_uv, NULL, 0);
}

bool colori709_a_p010(const uint8_t *pixel, uint32_t passo, uint32_t larghezza,
                      uint32_t altezza, Colori709Ordine ordine,
                      uint16_t *y, uint32_t passo_y,
                      uint16_t *uv, uint32_t passo_uv)
{
	return converti(pixel, passo, larghezza, altezza, ordine, 1, 1,
	                (uint8_t *) y, passo_y, (uint8_t *) uv, passo_uv, NULL, 0);
}
