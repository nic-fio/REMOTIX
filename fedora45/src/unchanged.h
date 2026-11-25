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
 *      least every `UC_REFRESH_MS` while frames keep coming, AND when they
 *      stop (the «pending» frame, `uc_pending_due` below).
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

/* ------------------------------------------------------------------ *
 * ⭐ 15 Oct 2026 (review of 1849a57d) — THE FRAME HELD BACK WHEN THE SCENE
 *    GOES STILL.  The 250 ms rule above only fires when a LATER frame
 *    arrives: if the last frame before a still scene is held back while it
 *    hides a real change (KWin lost a damage), nothing would ever send it.
 *    ⇒ A held frame is «pending»; if no other frame arrives by
 *    `last_out + UC_REFRESH_MS` (or a keyframe is due), it is flushed:
 *    on memory the copy we already own goes out; on the card the buffer
 *    went back to KWin at once, so the stream is asked for a fresh frame.
 * ------------------------------------------------------------------ */

typedef enum
{
	UC_PENDING_NONE,  /* nothing held back since the last frame out */
	UC_PENDING_WAIT,  /* held back, still inside the window */
	UC_PENDING_FLUSH, /* held back and the window is over: send it now */
} UcPending;

static inline UcPending uc_pending_due(gboolean pending, gboolean bypass, uint64_t last_out_us,
                                       uint64_t now_us)
{
	if (!pending)
		return UC_PENDING_NONE;
	if (bypass || last_out_us == 0 || now_us < last_out_us ||
	    now_us - last_out_us >= (uint64_t)UC_REFRESH_MS * 1000u)
		return UC_PENDING_FLUSH;
	return UC_PENDING_WAIT;
}

/* How long (µs) a wait may last before the pending frame is due; `cap_us`
 * when nothing is pending.  ⛔ Never more than `cap_us`.  `bypass` (a
 * keyframe is due) makes a pending frame due NOW, as in `uc_pending_due`. */
static inline uint64_t uc_pending_wait_us(gboolean pending, gboolean bypass, uint64_t last_out_us,
                                          uint64_t now_us, uint64_t cap_us)
{
	uint64_t due;

	if (!pending)
		return cap_us;
	if (bypass || last_out_us == 0)
		return 0;
	due = last_out_us + (uint64_t)UC_REFRESH_MS * 1000u;
	if (now_us >= due)
		return 0;
	return due - now_us < cap_us ? due - now_us : cap_us;
}

/* Two stream restarts asked by a stale card frame are at least this far apart. */
#define UC_WAKE_GAP_MS 2000u

/* ------------------------------------------------------------------ *
 * ⭐ 15 Oct 2026 (review of 845f4d19) — ONE RESTART PER EPISODE.  On the
 *    card, with the user typing or clicking now and then, the last frame
 *    before each pause is often a held-back «same» one: every pause became
 *    a stale flag and a stream restart (a pause of ~42 ms, a buffer
 *    renegotiation, a log line) about every `UC_WAKE_GAP_MS`.
 *    ⇒ Once raised, the stale flag is NOT raised again until:
 *       · a frame that REALLY changed went out (`uc_gate_frame`, changed:
 *         the filter looked at the bytes against a reference and they
 *         were not the same — not a refresh, not a frame sent whole for
 *         lack of a reference), or
 *       · the buffers were renegotiated (another generation) by something
 *         that is not our own restart (`uc_gate_restarted`).
 *    ⛔ Our own restart renegotiates too: its generation is absorbed — the
 *       first frame of a NEW generation after it becomes the episode's
 *       generation.  A frame still of the generation of the moment of the
 *       restart does not close that window (it was already on its way).
 *    ⚠ The price, said: while our restart has delivered nothing yet, a real
 *      renegotiation in that window is absorbed as ours.  The next real
 *      change re-arms all the same: never a loop, at worst one restart less.
 * ------------------------------------------------------------------ */
typedef struct
{
	gboolean spent;        /* raised once in this episode */
	gboolean own_restart;  /* our restart is under way: its renegotiation is ours */
	uint64_t generation;   /* the buffers the episode belongs to */
	uint64_t restart_generation; /* the buffers at the moment of our restart */
} UcStaleGate;

/* A stale flag is wanted with the buffers at `generation`.  TRUE ⇒ raise it
 * (and the episode is spent); FALSE ⇒ already raised in this episode. */
static inline gboolean uc_gate_may_raise(UcStaleGate *g, uint64_t generation)
{
	if (g->spent && !g->own_restart && generation != g->generation)
		g->spent = FALSE; /* a real renegotiation: a new episode */
	if (g->spent)
		return FALSE;
	g->spent = TRUE;
	g->own_restart = FALSE;
	g->generation = generation;
	return TRUE;
}

/* The stream was restarted to answer the stale flag; `generation` = the
 * buffers at that moment. */
static inline void uc_gate_restarted(UcStaleGate *g, uint64_t generation)
{
	if (!g->spent)
		return;
	g->own_restart = TRUE;
	g->restart_generation = generation;
}

/* A frame went out of the filter, of buffers `generation`; `changed` ⇒ its
 * bytes were compared and were not the same. */
static inline void uc_gate_frame(UcStaleGate *g, uint64_t generation, gboolean changed)
{
	if (g->own_restart && generation != g->restart_generation) {
		g->own_restart = FALSE;
		g->generation = generation;
	}
	if (changed) {
		g->spent = FALSE;
		g->own_restart = FALSE;
	}
}

/* ------------------------------------------------------------------ *
 * ⭐ THE COST OF LOOKING, re-checked: the mean over a window of looks — the
 *    first window short (a card that is slow from the start is caught in
 *    `UC_COST_FIRST` looks), then every `UC_COST_EVERY`.
 *
 * ⛔ 15 Oct 2026 — THE CEILING ALONE SWITCHED THE FILTER OFF WHERE IT WAS
 *    NEEDED.  `[M]` a KDE test box, run functional/20261015-090731, F-003
 *    kde/firefox (09:08): 19 switch-offs for cost in 50 minutes of the box's
 *    log (08:43–09:34), means 4.3–9.3 ms against the 3 ms ceiling, most at the
 *    FIRST window — while windows held back 25 of 30 frames (c16002u99,
 *    strikes 2 and 3) and the F-003 one 12 of 30 (it fell on Firefox opening).  Off until a
 *    renegotiation that F-003 never makes: KWin's ~49 frames/s all went to the
 *    encoder (`video bandwidth … 493 frames` in 10 s), the Firefox page painted
 *    ~6.5 of them a second, and every photo was 1.1–3.8 s old (3 runs out of 3).
 *    ⚠ The cost is NOT the bytes compared: a look at ONE damaged pixel took
 *      4.65, 7.07, 11.76, 12.20 ms in the same log (map + DMA-BUF sync of the
 *      whole 30 MB buffer), and the encoding it replaces is ~10 ms on the
 *      server plus a 4K decode on a client that cannot keep up.
 *    ⇒ The verdict weighs what the look buys:
 *      · mean > `UC_COST_HARD_US` ⇒ off whatever it holds back (a look plus
 *        an encoding no longer fit in one interval at 50 frames/s);
 *      · mean > `UC_COST_MAX_US` ⇒ off only if the window held back fewer than
 *        1/`UC_YIELD_DIV` of its looks (costly AND sparing little);
 *      · otherwise on.
 * ------------------------------------------------------------------ */
#define UC_COST_MAX_US 3000u
#define UC_COST_HARD_US 10000u
#define UC_YIELD_DIV 4u
#define UC_COST_FIRST 30u
#define UC_COST_EVERY 300u

typedef struct
{
	guint64 sum_us;
	guint n;
	guint held; /* looks of the open window whose bytes were the same */
	guint windows;
	double last_mean_us;
	guint last_held, last_n; /* the window that closed last */
} UcCost;

/* The verdict on one closed window: TRUE ⇒ switch off. */
static inline gboolean uc_cost_over(double mean_us, guint held, guint n)
{
	if (mean_us > UC_COST_HARD_US)
		return TRUE;
	return mean_us > UC_COST_MAX_US && (guint64)held * UC_YIELD_DIV < n;
}

/* Adds one look; `same` ⇒ its bytes were those already delivered.  TRUE ⇒ a
 * window just closed and `uc_cost_over` says off (`last_*` say why). */
static inline gboolean uc_cost_add(UcCost *c, uint64_t cost_us, gboolean same)
{
	guint size = c->windows == 0 ? UC_COST_FIRST : UC_COST_EVERY;

	c->sum_us += cost_us;
	if (same)
		c->held++;
	if (++c->n < size)
		return FALSE;
	c->last_mean_us = (double)c->sum_us / c->n;
	c->last_held = c->held;
	c->last_n = c->n;
	c->sum_us = 0;
	c->n = 0;
	c->held = 0;
	c->windows++;
	return uc_cost_over(c->last_mean_us, c->last_held, c->last_n);
}

static inline void uc_cost_reset(UcCost *c)
{
	memset(c, 0, sizeof *c);
}

/* ------------------------------------------------------------------ *
 * ⭐ THE SWITCH: a switch-off (card buffer not LINEAR, not mappable, too
 *    costly) is a STRIKE and holds for the buffers of that negotiation; a
 *    new generation re-arms the filter.  ⛔ After `UC_STRIKES_MAX` strikes
 *    it is off for the whole capture.
 * ⭐ 15 Oct 2026: a switch-off for COST also re-arms after `UC_REARM_MS`.
 *    `[M]` F-003 kde/firefox: the first window of 30 looks fell on Firefox
 *    opening, and the stream never renegotiated afterwards ⇒ the measurement
 *    of one burst held for the whole test.  The strikes still count: at most
 *    `UC_STRIKES_MAX` windows are spent in all.  A switch-off for the buffer
 *    (not LINEAR, not mappable) does not change with time: renegotiation only.
 * ------------------------------------------------------------------ */
#define UC_STRIKES_MAX 3u
#define UC_REARM_MS 5000u

typedef struct
{
	gboolean off, hard, timed;
	guint strikes;
	uint64_t off_generation;
	uint64_t off_us;
} UcSwitch;

/* A strike at `now_us`; `timed` ⇒ it may also re-arm after `UC_REARM_MS`. */
static inline void uc_switch_strike(UcSwitch *s, uint64_t generation, uint64_t now_us,
                                    gboolean timed)
{
	s->off = TRUE;
	s->timed = timed;
	s->off_generation = generation;
	s->off_us = now_us;
	if (++s->strikes >= UC_STRIKES_MAX)
		s->hard = TRUE;
}

/* TRUE ⇒ the filter may look at a frame of `generation` at `now_us`.
 * `*rearmed` is set TRUE when this call lifted a soft switch-off. */
static inline gboolean uc_switch_allows(UcSwitch *s, uint64_t generation, uint64_t now_us,
                                        gboolean *rearmed)
{
	if (rearmed)
		*rearmed = FALSE;
	if (s->hard)
		return FALSE;
	if (s->off && (generation != s->off_generation ||
	               (s->timed && now_us >= s->off_us &&
	                now_us - s->off_us >= (uint64_t)UC_REARM_MS * 1000u))) {
		s->off = FALSE;
		if (rearmed)
			*rearmed = TRUE;
	}
	return !s->off;
}

#endif
