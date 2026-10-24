/*
 * unchanged.h — the frame that changes nothing, recognised from its damage.
 *
 * ⭐ 15 Oct 2026.  `[M]` stress climb `fix-kde-20261015/fix-kde-intel-4k`, level-01,
 *    short check (KDE, Firefox client, 3776x2016): while the F-003 test page is
 *    open — a counter that changes every 200 ms, that is FIVE real changes per
 *    second — KWin delivers **~50 buffers per second**, all with PARTIAL damage
 *    (`damage full 499 partial 1891` over 2400 frames).  The encoded sizes say
 *    what they carry: 593/597 bytes, alternating, for ~45 of every 50 (a P-frame
 *    with nothing in it at 4K), and 880–1740 bytes for the five a second where
 *    the counter moved.  GNOME, same page, same client: **5/s**, every one
 *    880–1580 bytes.  ⇒ ~90 % of KDE's frames are the same picture again, and a
 *    Firefox client cannot decode 50 4K frames a second: decoder queue ≥ 5, the
 *    photo of F-003 1.4–5 s old.
 * ⚠ WHY KWin damages without changing is NOT proven here (`[R]` KWin 6.3.6
 *   `outputscreencastsource.cpp`: a frame for every output repaint with a
 *   non-empty damage; who repaints at the output rate while that page is open
 *   was not measured).  What is measured is the effect, and this is the cure
 *   on OUR side: a frame whose damaged rectangles hold the same bytes as the
 *   last frame we delivered is not encoded.
 *
 * ⛔ WHY IT IS SAFE, and the one hole:
 *    · KWin's buffers are WHOLE frames (`STUDIES.md` §kde §4.6) and its damage
 *      says where they differ from the previous recorded one ⇒ a frame whose
 *      damage is contained in rectangles we kept, and holds the same bytes
 *      there, IS the frame already delivered.
 *    · ⚠ The hole: KWin drops a frame's damage when it has no free buffer
 *      (`screencaststream.cpp`, `record()` returns without keeping it).  A
 *      change lost that way would ride on the next frame, and if that one is
 *      dropped as «unchanged» it would wait.  ⇒ The caller re-delivers at
 *      least every `UC_REFRESH_MS` while frames keep coming.
 *
 * Pure functions, no I/O: the caller maps the buffer and decides.  4 bytes per
 * pixel (the four formats `capture.c` can negotiate).
 */
#ifndef REMOTIX_UNCHANGED_H
#define REMOTIX_UNCHANGED_H

#include <glib.h>
#include <stdint.h>
#include <string.h>

#define UC_MAX_RECTS 16
/* Above this damaged area the bytes are not kept nor compared: the frame
 * goes out as always.  ⚠ A quarter of 4K: the phantom repaint, if it is a
 * whole window, stays inside; a full-screen change does not pay a read. */
#define UC_MAX_PIXELS (3840u * 2160u / 4u)
/* The ceiling on how long a frame may be held back as «unchanged». */
#define UC_REFRESH_MS 250

typedef struct
{
	uint32_t x, y, width, height;
} UcRect;

typedef struct
{
	gboolean valid;
	uint32_t width, height, stride;
	guint n;
	UcRect rects[UC_MAX_RECTS];
	uint8_t *pixels; /* the rows of each rect, one after the other */
	size_t capacity;
} Unchanged;

/* Clips `r` to the frame; FALSE if nothing is left. */
static inline gboolean uc_clip(UcRect *r, uint32_t width, uint32_t height)
{
	if (r->x >= width || r->y >= height || r->width == 0 || r->height == 0)
		return FALSE;
	if (r->width > width - r->x)
		r->width = width - r->x;
	if (r->height > height - r->y)
		r->height = height - r->y;
	return TRUE;
}

static inline guint64 uc_area(const UcRect *r, guint n)
{
	guint64 a = 0;

	for (guint i = 0; i < n; i++)
		a += (guint64)r[i].width * r[i].height;
	return a;
}

/* Index of a kept rect that contains `r` whole, or -1. */
static inline int uc_holder(const Unchanged *u, const UcRect *r)
{
	for (guint i = 0; i < u->n; i++) {
		const UcRect *s = &u->rects[i];

		if (r->x >= s->x && r->y >= s->y && r->x + r->width <= s->x + s->width &&
		    r->y + r->height <= s->y + s->height)
			return (int)i;
	}
	return -1;
}

static inline void uc_forget(Unchanged *u)
{
	u->valid = FALSE;
	u->n = 0;
}

static inline void uc_free(Unchanged *u)
{
	g_free(u->pixels);
	memset(u, 0, sizeof *u);
}

/* Offset in `u->pixels` of kept rect `k`. */
static inline size_t uc_offset(const Unchanged *u, guint k)
{
	size_t o = 0;

	for (guint i = 0; i < k; i++)
		o += (size_t)u->rects[i].width * u->rects[i].height * 4u;
	return o;
}

/*
 * TRUE only when every rect of `r` lies inside a kept rect AND holds the same
 * bytes.  `base` is the first byte of row 0 of the frame.  ⛔ Any doubt —
 * nothing kept, other geometry, a rect not contained — is FALSE: «changed»
 * is the answer that cannot hurt.
 */
static inline gboolean uc_same(const Unchanged *u, const uint8_t *base, uint32_t width,
                               uint32_t height, uint32_t stride, const UcRect *r, guint n)
{
	if (!u->valid || n == 0 || u->width != width || u->height != height ||
	    u->stride != stride)
		return FALSE;
	for (guint i = 0; i < n; i++) {
		int k = uc_holder(u, &r[i]);
		const UcRect *s;
		const uint8_t *kept;

		if (k < 0)
			return FALSE;
		s = &u->rects[k];
		kept = u->pixels + uc_offset(u, (guint)k);
		for (uint32_t y = 0; y < r[i].height; y++) {
			const uint8_t *now = base + (size_t)(r[i].y + y) * stride + (size_t)r[i].x * 4u;
			const uint8_t *then = kept + ((size_t)(r[i].y - s->y + y) * s->width +
			                              (r[i].x - s->x)) * 4u;

			if (memcmp(now, then, (size_t)r[i].width * 4u) != 0)
				return FALSE;
		}
	}
	return TRUE;
}

/* Keeps the bytes of `r` as the new reference.  Too many pixels, or no rect:
 * nothing is kept (and the next frame will be «changed»). */
static inline void uc_keep(Unchanged *u, const uint8_t *base, uint32_t width, uint32_t height,
                           uint32_t stride, const UcRect *r, guint n)
{
	guint64 area = uc_area(r, n);
	size_t o = 0;

	uc_forget(u);
	if (n == 0 || n > UC_MAX_RECTS || area == 0 || area > UC_MAX_PIXELS)
		return;
	if (u->capacity < area * 4u) {
		g_free(u->pixels);
		u->pixels = g_malloc(area * 4u);
		u->capacity = area * 4u;
	}
	for (guint i = 0; i < n; i++) {
		u->rects[i] = r[i];
		for (uint32_t y = 0; y < r[i].height; y++) {
			memcpy(u->pixels + o, base + (size_t)(r[i].y + y) * stride + (size_t)r[i].x * 4u,
			       (size_t)r[i].width * 4u);
			o += (size_t)r[i].width * 4u;
		}
	}
	u->n = n;
	u->width = width;
	u->height = height;
	u->stride = stride;
	u->valid = TRUE;
}

#endif
