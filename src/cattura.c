/*
 * cattura.c — see cattura.h for the mandate and for the three rules.
 */
#include "cattura.h"

#include <gio/gio.h> /* only for the G_IO_ERROR error domain: no bus talk here */
#include <pipewire/pipewire.h>
#include <spa/buffer/meta.h>
#include <spa/param/video/format-utils.h>
#include <spa/utils/result.h>
#include <drm_fourcc.h>
#include <string.h>
#include <sys/mman.h>
#include <time.h>

#include "cursore.h"
#include "forma.h"
#include "registro.h"


#include "wlroots.h"
#define AREA "capture_v"

/* ⛔ The SAME clock as `figlio.c` (`now_monotonic_us`) and `codificatore.c`
 *    (`current_us`): the phase 8 segments are subtracted across different files,
 *    and two different clocks would give differences that mean nothing. */
static uint64_t current_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t) t.tv_sec * 1000000u + (uint64_t) t.tv_nsec / 1000u;
}

/* How long we wait for the stream to reach `paused`: it is the moment the
 * format negotiation has happened and we know whether the compositor accepted
 * what we asked for.  ⛔ Without this wait a refusal — «no more input
 * formats» — would be silent, and would show up much later as a black
 * screen. */
/* ⛔⭐ How long we wait for the PipeWire stream to ATTACH, in one attempt.
 *
 * ⚠ It used to be `WAIT_STARTUP_S`, ten seconds, and those ten seconds WERE the
 *   tail of the login times: see the box where it is used.  ⛔ The old
 *   constant was REMOVED, not left there unused: a constant that no longer
 *   controls anything is a trap for the reader. */
#define WAIT_LATCH_MS 10000

/* How many damaged regions we carry at most.  Beyond that, we declare that the
 * whole frame counts: it is the safe case. */
#define MAX_REGIONS 16

#define FD_MAX 8

/*
 * ⭐⭐ HOW OFTEN WE LOOK AT THE PIXELS — the biggest cure of phase 8 on the
 *     `capture → first byte` segment, and it lives in a constant.
 *
 * ⛔ THE FACT, `[M]` 22 August 2026, test machine (i5-13500T), 2 450
 *    frames at 1920x1080 with hardware HEVC:
 *
 *      the whole segment                      **21.61 ms**
 *      of which `measure_pixels()`            **5.34 ms — 25 %**
 *
 *    and `[M]` on pure CPU (bench `08-c-scansione.c`) the same scan costs
 *    **5.36 ms** at 1920x1080 and **8.89** at 2560x1440: it grows with pixels, so
 *    on a large canvas it would be **worse**.
 *
 * ⛔⛔ AND WHAT IT WAS FOR, counted line by line: in the product those three values
 *      (`nero`, `uniform`, the range) end up in **ONE** log line,
 *      written **ONCE**, when the stage is mounted (`figlio.c`, «frame
 *      captured AS …, ⛔ BLACK / not black»), plus the two lines below.
 *      ⇒ Thirty to sixty scans per second at 5.34 ms **for a single line**.
 *
 * ⚠ AND THE DIAGNOSIS IS NOT LOST, which was the only reason it was worth
 *   paying for: the FIRST frame is always looked at — and it is the one of the line —
 *   and then we keep looking, but at this rate.  ⛔ A desktop that
 *   turns black mid-session is still seen, at most half a second later.
 *
 * ⛔ AND WHAT WAS **NOT** DONE, and was measured before discarding it:
 *    looking at **one pixel in eight** would cost `[M]` **0.10 ms** instead of
 *    5.36 — even better.  ⇒ Discarded anyway, and the reason is that it
 *    would change the MEANING: a frame that is black except for a skipped region
 *    would be declared **BLACK**, and a log line that accuses black
 *    when there is no black sends the hunt the wrong way — which costs
 *    more than 5 ms.  ⭐ Here instead the answer stays **exact**: only
 *    how often it is given changes.
 */
/* ⭐ It can be overridden from the compile line (`-DMISURA_PIXEL_OGNI_MS=0`), and
 *    it serves ONE purpose only: rebuilding the **before** with the same source as
 *    the after, for the A/B comparison.  ⛔ `0` means «on every frame», that is
 *    the behaviour until 22 August 2026.  ⚠ It is not a product
 *    switch and does not become one: the product has a single value, the one
 *    below (`CODER.md` invariant I7). */
#ifndef PIXEL_MEASURE_EVERY_MS
#define PIXEL_MEASURE_EVERY_MS 500
#endif

/*
 * How many bytes the cursor metadata must have to carry a bitmap of
 * `w x h`.  ⛔ It is the same formula as Mutter's (`CURSOR_META_SIZE`,
 * `meta-screen-cast-stream-src.c:63`) and it lives here because it is a quantity of the
 * PipeWire NEGOTIATION, not of the wire: the wire's ceiling is 256 and lives in
 * `cursore.h`.
 */
#define CURSOR_META_BYTE(l, a)                                                                    \
	((int) (sizeof(struct spa_meta_cursor) + sizeof(struct spa_meta_bitmap) + (l) * (a) * 4))

struct Capture
{
	/*
	 * ⭐⭐ PHASE 13 — THE SECOND SOURCE, and it sits AT THE TOP on purpose.
	 *
	 * When this field is set, the `Capture` is not a PipeWire stream: it is a
	 * Wayland client that PULLS the frames (`wlroots.h`).  ⛔ All the fields
	 * below stay zero and are not touched, and every public function
	 * hands over at the top — so the GNOME and KDE code stays
	 * textually what it was before.
	 */
	WlrStage *wlr;
	WlrFrame wlr_last;
	gboolean wlr_last_known;
	gboolean wlr_witness_logged, wlr_y_logged;
	gboolean wlr_fallback_logged;      /* «card requested, memory arrived» */
	gboolean wlr_watched_first;  /* the first card frame, mapped */
	/* ⭐ The true shape on labwc (the probe, `wlroots.h`): the last one DELIVERED,
	 *    so as not to resend the same image under two names (`default` and
	 *    `left_ptr` are the same drawing), and the serial that `forma.h` leaves to
	 *    whoever delivers. */
	CursorShape wlr_shape;
	gboolean wlr_shape_data;
	guint64 wlr_shapes_sent, wlr_shapes_equal;

	struct pw_thread_loop *cycle;
	struct pw_context *context;
	struct pw_core *core;
	struct pw_stream *flow;
	struct spa_hook hook;

	struct spa_video_info_raw schema;
	gboolean known_format;

	CaptureFrame on_frame;
	CaptureEnd su_fine;
	gpointer data_v;

	enum pw_stream_state state;
	char *fault;
	gboolean end_reported;
	gboolean type_logged;

	CaptureRoute route;
	CaptureColor color;
	uint32_t requested_width, requested_height;
	/* ⛔ The rate REQUESTED at startup, kept because `capture_resize()`
	 *    repeats the same proposal: putting a hand-written one in there
	 *    would mean that after a resize the stream runs at a rate
	 *    different from the one it was born with — and no line would say so. */
	uint32_t requested_per_second;
	/* ⛔ Whether the NEGOTIATED size differs from the REQUESTED one.  It is said
	 *    only once and kept, because the format callback runs several times.
	 * ⚠ It exists because the canvas is about to stop being a constant
	 *   (`DECISIONI.md` §5.0-sexies): as long as 1920x1080 was always requested a
	 *   divergence could not happen, and indeed nobody looked at it.
	 *
	 * ⛔⛔ AND THERE IS NO ACCESSOR, AND IT IS A MEASURED CHOICE — 22 August 2026,
	 *     bench `banchi/06-b5-esiti-cattura.c` case 4 and case 6.
	 *
	 *   · `[M]` The only scene that turns this field on is **two chained
	 *     `capture_resize()`**: the `Format` of the FIRST comes back
	 *     when `chiesta_*` already carries the SECOND.  Measured **43 times out of 480
	 *     chains** (three sweeps of 160), with most hits between **200 and 800
	 *     us** apart between the two calls and tails down to 0 and up to 3200 us — and the
	 *     line said *«requested 1602x1020, granted 1202x806»*,
	 *     that is «granted» was **the previous request**, not a different
	 *     grant by the producer.  ⇒ In that scene the field is a **false
	 *     alarm**, and it turns itself off at the next `Format`.
	 *   · `[M]` The opposite scene — the producer IMPOSING a size of its own — does not
	 *     exist: `proposal()` declares a FIXED rectangle, so
	 *     the intersection is either that value or the empty set (case 5: the stage
	 *     demands 1600x900, the stream goes to `error`, no divergence).
	 *
	 * ⇒ ⛔ Exporting it would mean giving the caller a `TRUE` that in the only
	 *   measured scene is **wrong**.  And it would not help: `cattura.h` already
	 *   exposes `capture_measure_requested()` and `capture_measure_negotiated()`, and the
	 *   divergence is their inequality (case 6).  ⭐ The real verdict is
	 *   given by the FRAME, in `figlio.c`, and it is the rule that §5.0-sexies had
	 *   already written: *«the truth is told by the frame, not by the outcome of the
	 *   request»*. */
	gboolean measure_divergent;

	/* --- the counters, which run on the real-time thread ---------------- *
	 * ⚠ THEY ARE COUNTED, NOT PRINTED: one log line per frame
	 *   would distort the very thing being watched.  The first is said, and then a
	 *   summary every three hundred. */
	CaptureCounts count;
	int fd_seen[FD_MAX];
	uint32_t first_raw_type; /* the SPA value, for whoever wants the bare number */

	/* --- the slot of whoever waits for a frame -------------------------- *
	 * ⛔ The slot exists only while someone waits: a frame that arrives
	 *    when nobody wants it is just counted.  Copying 8 MB for nobody
	 *    would be work inside the real-time callback, done for nothing. */
	GMutex lock;
	GCond news;
	gboolean someone_waiting;
	CaptureStopped slot;
	gboolean slot_full;
	/* ⭐ The capacity of the slot's buffer: it is REUSED instead of remade at every
	 *    frame.  ⛔ It is needed because now we ALWAYS copy (see below), and
	 *    a `g_malloc`/`g_free` of 8 MB sixty times per second inside the
	 *    real-time callback would be a cure worse than the disease. */
	size_t slot_capacity;
	/* ⛔ How many times a frame not yet consumed was replaced by
	 *    a more recent one.  ⚠ It is NOT a fault — it is the intended behaviour,
	 *    «the newest wins» — but it is also the number that says how often the
	 *    consumer is late, and before 15 August 2026 those frames
	 *    were LOST instead of replaced. */
	uint64_t overwritten;

	/* ⭐ The rate of the pass over the pixels — see `PIXEL_MEASURE_EVERY_MS`.  ⛔ They live
	 *    on the CALLER's thread (`capture_take`), not on the real-time
	 *    one: no lock is needed, and adding one would suggest that
	 *    one is needed. */
	uint64_t last_measure_us;
	guint64 measures_done, measures_skipped;
	/* ⚠ On the card the pixels are looked at only if the buffer can be mapped: it is
	 *   said once if it could not be, and then we stay quiet. */
	gboolean logged_measure_impossible;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ THE RETENTION — the cure for the RELEASE problem of `LEZIONI.md` §8
	 * ------------------------------------------------------------------ *
	 *
	 * ⛔ THE FACT: `can_reuse_pw_buffer` (inside Mutter) gives up when
	 *    `SPA_META_SyncTimeline` is missing, and then the producer **reuses the buffer
	 *    while VA-API is still reading it** `[R]`.  The symptom is not an
	 *    error: it is **two screens alternating**, and it is the defect from
	 *    which the phase 8 hunt had started off in the wrong direction.
	 *
	 * ⭐ THE CURE CHOSEN, and the reason is written down because there were two routes:
	 *    we **hold the `pw_buffer`** until reading is finished, and we do **not**
	 *    ask for the timeline.  Holding is **ours** and works on every
	 *    producer — Mutter, KWin, wlroots — without asking anyone for anything
	 *    (`LEZIONI.md` §1.25: *a cure is sought wherever it applies*); the timeline
	 *    depends on what the producer offers, and when it is missing **there is
	 *    no error**: there is the alternating screen.  ⇒ It would be a cure
	 *    that disappears silently, that is `LEZIONI.md` §1.8.
	 *
	 * ⚠ THE PRICE, and it is counted instead of hoped small: **two fewer buffers**
	 *   than those the producer recycles — one held in the slot and one in the hands
	 *   of the reader.  That is why on the card route we ask for SIX and
	 *   not four (`consumer_parameters`).
	 *
	 * ⛔ And the buffer is given back with the PipeWire loop lock held,
	 *    because whoever returns it is on ANOTHER thread (the consumer's) —
	 *    while `on_process` runs on the real-time one, which already has
	 *    the lock.  The order is always `loop → lock`, never the reverse.
	 */
	guint64 held_count;      /* how many buffers have been held in total         */
	guint64 held_returned; /* how many came back: the difference is how many   */
	                       /* we hold right now                                */
	/* ⛔ It changes every time PipeWire allocates or frees the buffers.  ⚠ Whoever
	 *    caches the import of an `fd` must watch it: descriptor numbers
	 *    are recycled, and a blind cache would point to a dead buffer
	 *    without any error. */
	uint64_t buffer_generation;

	/* --- ⭐ THE CURSOR CHANNEL ------------------------------------------- *
	 *
	 * ⛔ `cattura.c` does NOT know the wire: it reads the raw metadata and passes it to
	 *    `cursore.c`, which is the only place where the shape becomes a
	 *    `CursorShape` (see `cursore.h`).
	 *
	 * ⚠ The module always exists, even if nobody listens: that way the counters
	 *   say whether the metadata REALLY arrives, regardless of whether
	 *   someone consumes it.  The listener registers later, with
	 *   `capture_cursor`, and the two fields are read under the lock because
	 *   whoever registers is on another thread. */
	Cursor *pointer_shape;
	CursorArrived cursor_fn;
	void *cursor_who;
	gboolean logged_cursor; /* the first metadata is said once */
};

/* ------------------------------------------------------------------ *
 *  The names — a single place, so that whoever writes a manifest does not reinvent them
 * ------------------------------------------------------------------ */

const char *capture_buffer_name(CaptureBuffer buffer)
{
	switch (buffer)
	{
	case CAPTURE_BUFFER_MEMFD: return "MemFd";
	case CAPTURE_BUFFER_MEMPTR: return "MemPtr";
	case CAPTURE_BUFFER_MEMID: return "MemId";
	case CAPTURE_BUFFER_DMABUF: return "DMA-BUF";
	default: return "UNKNOWN";
	}
}

static CaptureBuffer buffer_da_spa(uint32_t kind)
{
	switch (kind)
	{
	case SPA_DATA_MemFd: return CAPTURE_BUFFER_MEMFD;
	case SPA_DATA_MemPtr: return CAPTURE_BUFFER_MEMPTR;
	case SPA_DATA_MemId: return CAPTURE_BUFFER_MEMID;
	case SPA_DATA_DmaBuf: return CAPTURE_BUFFER_DMABUF;
	default: return CAPTURE_BUFFER_UNKNOWN;
	}
}

/*
 * ⭐ The DRM fourcc that matches the SPA format — and it is needed **only** on the
 *    card route, because a DMA-BUF is imported by naming the format in
 *    that vocabulary and not in this one.
 *
 * ⛔ AND THE MAPPING IS WRITTEN OUT IN FULL, instead of saying «they are just
 *    four bytes anyway»: SPA names the formats **in the order of the bytes in memory**
 *    (`BGRx` = B, G, R, ignored) and DRM names them as a **little
 *    endian** integer (`XRGB8888` = 0xXXRRGGBB, which in memory is B, G, R, X).  ⇒ The two
 *    names are **reversed with respect to each other**, and whoever pairs them «by
 *    eye» swaps red and blue without any error — the image is there, and it is
 *    wrong.
 *
 * ⚠ Only the four that this module can negotiate are declared: a zero
 *   return means **«I cannot name this format»**, and the caller
 *   discards the frame instead of passing VA-API an invented fourcc.
 */
static uint32_t drm_da_spa(uint32_t spa_format)
{
	switch (spa_format)
	{
	case SPA_VIDEO_FORMAT_BGRx: return DRM_FORMAT_XRGB8888;
	case SPA_VIDEO_FORMAT_BGRA: return DRM_FORMAT_ARGB8888;
	case SPA_VIDEO_FORMAT_RGBx: return DRM_FORMAT_XBGR8888;
	case SPA_VIDEO_FORMAT_RGBA: return DRM_FORMAT_ABGR8888;
	default: return 0;
	}
}

const char *capture_color_name(uint32_t raw_format)
{
	switch (raw_format)
	{
	case SPA_VIDEO_FORMAT_BGRx: return "BGRx";
	case SPA_VIDEO_FORMAT_BGRA: return "BGRA";
	case SPA_VIDEO_FORMAT_RGBx: return "RGBx";
	case SPA_VIDEO_FORMAT_RGBA: return "RGBA";
	case SPA_VIDEO_FORMAT_xRGB: return "xRGB";
	case SPA_VIDEO_FORMAT_ARGB: return "ARGB";
	case SPA_VIDEO_FORMAT_xRGB_210LE: return "xRGB_210LE";
	case SPA_VIDEO_FORMAT_xBGR_210LE: return "xBGR_210LE";
	case SPA_VIDEO_FORMAT_ARGB_210LE: return "ARGB_210LE";
	case SPA_VIDEO_FORMAT_ABGR_210LE: return "ABGR_210LE";
	default: return "OTHER";
	}
}

const char *capture_source_name(CaptureSource source)
{
	switch (source)
	{
	case CAPTURE_SOURCE_PRODUCER: return "requested from the producer (SPA_PARAM_Format)";
	case CAPTURE_SOURCE_FORMAT: return "follows from the negotiated format";
	case CAPTURE_SOURCE_MEASURED: return "[M] measured by us on the delivered pixels";
	default: return "NOT DECLARED by the producer";
	}
}

/*
 * ⛔ SPA'S FOUR `UNKNOWN`s ARE AN ANSWER, NOT A SILENCE TO BE FILLED.
 *
 * `[M]` 12 August 2026: on Mutter 48.7 the capture stream delivers **zero** in
 * all four fields (`color_range`, `color_matrix`, `transfer_function`,
 * `color_primaries`).  Whoever filled them with what they expect would be
 * deducing, and that is form E8.
 */
const char *capture_range_name(uint32_t raw)
{
	switch (raw)
	{
	case 1: return "FULL (0-255)";
	case 2: return "LIMITED (16-235)";
	default: return "NOT DECLARED by the producer";
	}
}

const char *capture_matrix_name(uint32_t raw)
{
	switch (raw)
	{
	case 1: return "RGB (no conversion: the pixels are RGB)";
	case 2: return "FCC";
	case 3: return "BT.709";
	case 4: return "BT.601";
	case 5: return "SMPTE240M";
	case 6: return "BT.2020";
	default: return "NOT DECLARED by the producer";
	}
}

const char *capture_transfer_name(uint32_t raw)
{
	switch (raw)
	{
	case 1: return "gamma 1.0 (linear)";
	case 4: return "gamma 2.2";
	case 5: return "BT.709";
	case 7: return "sRGB";
	case 11: return "BT.2020 12 bit";
	default: return "NOT DECLARED by the producer";
	}
}

const char *capture_primaries_name(uint32_t raw)
{
	switch (raw)
	{
	case 1: return "BT.709";
	case 4: return "SMPTE170M";
	case 7: return "BT.2020";
	default: return "NOT DECLARED by the producer";
	}
}

const char *capture_range_measured_name(CaptureRangeMeasured measured)
{
	switch (measured)
	{
	case CAPTURE_RANGE_COMPATIBLE_FULL:
		return "[M] the pixels reach 0 and 255: compatible with FULL";
	case CAPTURE_RANGE_INCONCLUSIVE:
		return "[M] the pixels do not reach the extremes: NOT CONCLUSIVE — it depends on the scene, "
		       "and does not prove a limited range";
	default:
		return "not measured";
	}
}

/*
 * The bits per channel are derived from the FORMAT, which is a fact of the producer.
 *
 * ⛔ And if a format we do not know arrived we answer 0 and declare it:
 *    an invented number here would become «ten real bits» in an
 *    F2.3 table, and nobody would trace it back here.
 */
static int bit_per_channel(uint32_t schema)
{
	switch (schema)
	{
	case SPA_VIDEO_FORMAT_BGRx:
	case SPA_VIDEO_FORMAT_BGRA:
	case SPA_VIDEO_FORMAT_RGBx:
	case SPA_VIDEO_FORMAT_RGBA:
	case SPA_VIDEO_FORMAT_xRGB:
	case SPA_VIDEO_FORMAT_ARGB:
		return 8;
	case SPA_VIDEO_FORMAT_xRGB_210LE:
	case SPA_VIDEO_FORMAT_xBGR_210LE:
	case SPA_VIDEO_FORMAT_ARGB_210LE:
	case SPA_VIDEO_FORMAT_ABGR_210LE:
	case SPA_VIDEO_FORMAT_RGBx_102LE:
	case SPA_VIDEO_FORMAT_BGRx_102LE:
	case SPA_VIDEO_FORMAT_RGBA_102LE:
	case SPA_VIDEO_FORMAT_BGRA_102LE:
		return 10;
	default:
		return 0;
	}
}

/* The byte order, to know where R, G and B are when measuring the range.
 * ⛔ Valid only for 8-bit formats with four bytes per pixel: on the others we
 *    answer FALSE and the measurement is NOT done, instead of doing it on the wrong bytes. */
static gboolean rgb_positions(uint32_t schema, int *r, int *g, int *b)
{
	switch (schema)
	{
	case SPA_VIDEO_FORMAT_BGRx:
	case SPA_VIDEO_FORMAT_BGRA:
		*b = 0; *g = 1; *r = 2; return TRUE;
	case SPA_VIDEO_FORMAT_RGBx:
	case SPA_VIDEO_FORMAT_RGBA:
		*r = 0; *g = 1; *b = 2; return TRUE;
	case SPA_VIDEO_FORMAT_xRGB:
	case SPA_VIDEO_FORMAT_ARGB:
		*r = 1; *g = 2; *b = 3; return TRUE;
	default:
		return FALSE;
	}
}

/* ------------------------------------------------------------------ *
 *  The PipeWire callbacks
 * ------------------------------------------------------------------ */

static void on_state(void *data_v, enum pw_stream_state prior, enum pw_stream_state fresh,
                     const char *failure)
{
	Capture *capture_v = data_v;

	log_detail(AREA, "stream state: %s → %s%s%s", pw_stream_state_as_string(prior),
	                   pw_stream_state_as_string(fresh), failure ? " — " : "", failure ? failure : "");
	capture_v->state = fresh;
	if (failure)
	{
		g_free(capture_v->fault);
		capture_v->fault = g_strdup(failure);
	}

	/*
	 * The consumer must notice by itself when the stream detaches, and the
	 * condition on the OLD state is not a detail: at startup we start from
	 * `unconnected`, and signalling the end there would be ending before starting.
	 *
	 * Without this, a «Log Out» from the system menu would leave the client attached
	 * to a frozen image: whoever watches could not tell «desktop idle» from
	 * «there is nothing left to capture».
	 */
	if ((prior == PW_STREAM_STATE_PAUSED || prior == PW_STREAM_STATE_STREAMING) &&
	    fresh == PW_STREAM_STATE_UNCONNECTED && !capture_v->end_reported)
	{
		capture_v->end_reported = TRUE;
		log_says(AREA, "the capture stream has detached");
		if (capture_v->su_fine)
			capture_v->su_fine(capture_v->data_v);
	}

	/* Whoever waits for a frame must wake up also when the stream dies, or
	 * they would wait the whole timeout for a frame that can no longer arrive. */
	g_mutex_lock(&capture_v->lock);
	g_cond_broadcast(&capture_v->news);
	g_mutex_unlock(&capture_v->lock);

	pw_thread_loop_signal(capture_v->cycle, false);
}

/*
 * ⛔ THE BOUNCE TOWARDS THE LISTENER, and it is not a convenience: `cursor_open` wants
 *    the recipient at opening time, but the stream starts before
 *    anyone registers.  Without the bounce the first shape — the one that arrives
 *    with the first pointer movement — would have nowhere to go.
 *
 * ⚠ It runs on PipeWire's real-time thread: whoever registers here must not
 *   wait for anything (`cattura.h`, the box on the loop).
 */
static int cursor_bounce(void *chi, const CursorShape *shape)
{
	Capture *capture_v = chi;
	CursorArrived fn;
	void *dove;

	g_mutex_lock(&capture_v->lock);
	fn = capture_v->cursor_fn;
	dove = capture_v->cursor_who;
	g_mutex_unlock(&capture_v->lock);

	/* ⛔ Nobody listening is NOT an error: the shape has been counted anyway, and
	 *    it is precisely the case in which the bench measures the source without the
	 *    wire. */
	if (!fn)
		return 0;
	return fn(dove, shape);
}

/*
 * ⛔⭐ THE FOUR CONSUMPTION PARAMETERS — IN A SINGLE PLACE, and the reason is a
 *     defect found while refuting, on 15 August 2026.
 *
 * `pw_stream_update_params()` does NOT add: **it replaces the whole list**.  ⇒
 * Whoever renegotiates the format passing only `EnumFormat` erases `ParamBuffers`
 * and the three `ParamMeta` — among them the CURSOR one, added on 14 August
 * precisely because without it «`CURSORE_FORMA` was a channel with no source».
 *
 * ⚠ In the healthy case the format callback puts them back right away.  ⛔ But the case
 *   that `cattura.h` documents as measured — «the compositor answers
 *   *succeeded* and sends no event» — does not run that callback,
 *   and the declaration would stay empty.  ⇒ ALL of them are repeated, always, from a
 *   single place: two lists that must stay equal are two lists that
 *   diverge.
 */
static uint32_t consumer_parameters(Capture *capture_v, struct spa_pod_builder *builder,
                                     const struct spa_pod *parameters[4])
{
	/*
	 * ⛔ THE DATA TYPE IS AGREED HERE, not in the format: whoever stays silent gets the
	 *    default, which is ordinary memory.  It is the second half of
	 *    rule 2 of `cattura.h` — declaring only one makes the
	 *    negotiation succeed with the opposite of what was wanted inside.
	 *
	 * ⛔ And the DMA-BUF bit is turned on ONLY if that is the requested route.
	 *    Leaving it on «just in case» would mean leaving the compositor
	 *    free to deliver descriptors that nobody looks at in memory:
	 *    every frame silently discarded, and no error.
	 */
	int types = (1 << SPA_DATA_MemFd) | (1 << SPA_DATA_MemPtr);
	if (capture_v->route == CAPTURE_ROUTE_CARD)
		types = (1 << SPA_DATA_DmaBuf);

	/* ⛔⭐ SIX BUFFERS ON THE CARD AND FOUR IN MEMORY, and the difference is the
	 *     PRICE OF THE RETENTION, counted instead of hoped small.
	 *
	 * On the card route we **hold** the buffers until VA-API has
	 * finished reading them (see the RETENTION box): at most TWO
	 * at a time — one held in the slot and one in the hands of the reader.  ⇒ With four
	 * the producer would have two, and on a burst it would stop to wait for us.
	 * ⚠ In memory instead we copy and give back at once: four are enough, and they are
	 *   the ones Mutter uses by itself (`DECISIONI.md` §2.3-ter).
	 * ⛔ And the number is a requested MINIMUM, not an order: the producer answers
	 *    what it can, and how many it really gave is said by
	 *    `distinct_buffers` — which is counted, not assumed. */
	int how_many = capture_v->route == CAPTURE_ROUTE_CARD ? 6 : 4;
	int minimum = capture_v->route == CAPTURE_ROUTE_CARD ? 4 : 2;

	parameters[0] = spa_pod_builder_add_object(
	    builder, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
	    SPA_POD_CHOICE_RANGE_Int(how_many, minimum, 8), SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int(types));

	/*
	 * ⛔ METADATA ARE REQUESTED, OR THEY DO NOT ARRIVE — and without them the producer
	 *    has no way to tell us anything about the frame: neither which one it is (`seq`), nor
	 *    how much of it was repainted (`VideoDamage`).
	 *
	 * ⚠ Requesting a metadata does NOT oblige the producer to give it: the reader must
	 *   cope with its absence, and that is why every read checks the pointer
	 *   and counts the absences instead of taking them as zero.
	 */
	parameters[1] = spa_pod_builder_add_object(
	    builder, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_Header), SPA_PARAM_META_size,
	    SPA_POD_Int(sizeof(struct spa_meta_header)));
	parameters[2] = spa_pod_builder_add_object(
	    builder, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_VideoDamage), SPA_PARAM_META_size,
	    /*
	     * ⛔⭐ SIXTEEN REGIONS, NOT FOUR — 15 August 2026, and the number is not
	     *     by eye: it is the one Mutter counts.
	     *
	     * `[M]` In the session log there were warnings like
	     *     «Not enough buffers (4) to accommodate damaged regions (6)».
	     * ⚠ And they are NOT about PipeWire buffers, as it seems: reading
	     *   `meta-screen-cast-stream-src.c:891` they are the **region slots** inside
	     *   THIS metadata.  When the damaged regions are more than the slots
	     *   we requested, Mutter gives up on fine damage and declares
	     *   **the whole frame damaged**.
	     *
	     * ⇒ Requesting the bare minimum made exactly the case where
	     *   damage helps degenerate: the scene that changes in many small spots —
	     *   a window opening, a terminal scrolling.
	     *
	     * ⚠ The cost of requesting more is a few tens of bytes per buffer:
	     *   `spa_meta_region` is 16 bytes.  The ceiling goes up to 32 because whoever
	     *   accepts 16 has no reason to refuse 32, and the choice stays with the
	     *   producer.
	     */
	    SPA_POD_CHOICE_RANGE_Int(sizeof(struct spa_meta_region) * 16,
	                             sizeof(struct spa_meta_region) * 1,
	                             sizeof(struct spa_meta_region) * 32));

	/*
	 * ⭐⭐ THE CURSOR METADATA — and until 14 August 2026 it was not requested.
	 *
	 * ⛔ The defect this request cures, `STUDI.md` §gnome §1.1 point 6 and §5.2:
	 *    from `RecordVirtual` we ask `cursor-mode = 2` (`src/mutter.c:439`), that is
	 *    «give me the cursor as METADATA instead of in the pixels» — and Mutter
	 *    obeys in both directions: it removes the pointer from the image
	 *    (`inhibit_cursor_overlay`) **and** puts it in the metadata.  ⛔ But the
	 *    metadata, like every metadata, arrives only to whoever requests it: without this
	 *    line we got the FIRST direction and not the second, that is no cursor
	 *    anywhere.
	 *
	 * ⚠ THE SIZE IS A RANGE, and the three numbers are those of Mutter's test
	 *   client (`src/tests/remote-desktop-utils.c:218-225`): the metadata
	 *   must be able to hold `spa_meta_cursor` + `spa_meta_bitmap` + the pixels, and
	 *   requesting a FIXED one that is too small the producer would cut the
	 *   bitmap.  Mutter offers 384x384 (`CURSOR_META_SIZE(384, 384)`).
	 *
	 * ⛔ And 384 > 256, which is the ceiling of `RCP.md` §7.2: the cut is made by
	 *    `cursore.c`, DECLARING it, because the place where the wire's limits are
	 *    enforced is a single one.
	 */
	parameters[3] = spa_pod_builder_add_object(
	    builder, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_Cursor), SPA_PARAM_META_size,
	    SPA_POD_CHOICE_RANGE_Int(CURSOR_META_BYTE(384, 384), CURSOR_META_BYTE(1, 1),
	                             CURSOR_META_BYTE(384, 384)));
	return 4;
}

static void on_parameters(void *data_v, uint32_t id, const struct spa_pod *param)
{
	Capture *capture_v = data_v;
	uint32_t kind, subtype;
	uint8_t space[1024];
	struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(space, sizeof space);
	const struct spa_pod *parameters[4];

	if (!param || id != SPA_PARAM_Format)
		return;
	if (spa_format_parse(param, &kind, &subtype) < 0)
		return;
	if (kind != SPA_MEDIA_TYPE_video || subtype != SPA_MEDIA_SUBTYPE_raw)
		return;
	if (spa_format_video_raw_parse(param, &capture_v->schema) < 0)
	{
		log_says(AREA, "⚠ capture format cannot be interpreted");
		return;
	}

	capture_v->known_format = TRUE;
	log_says(AREA, "negotiated format: %ux%u %s (%d bits per channel), modifier 0x%" G_GINT64_MODIFIER "x",
	              capture_v->schema.size.width, capture_v->schema.size.height,
	              capture_color_name(capture_v->schema.format),
	              bit_per_channel(capture_v->schema.format), (guint64) capture_v->schema.modifier);

	/* ⛔⛔ THE GUARD: requested versus granted.
	 *
	 * ⚠ Until 14 August 2026 this line did not exist, and the log line
	 *   above stated the negotiated size **without comparing it with anything**: whoever
	 *   read it saw a number and had no way to know whether it was the one
	 *   requested.  ⛔ With the canvas fixed at 1920x1080 the divergence could not
	 *   happen; `DECISIONI.md` §5.0-sexies makes it POSSIBLE, and that is
	 *   why the guard is born together with that decision and not after.
	 *
	 * ⛔ And the damage it prevents is not a skewed image: it is the pointer
	 *   ending up ELSEWHERE.  If the compositor grants a different size and nobody
	 *   says so, the coordinate conversion is born wrong and the symptom —
	 *   measured for two days on Samsung DeX — is «the mouse has problems with the
	 *   coordinates of the elements».  ⇒ A defect that declares itself costs a
	 *   minute; one that stays silent cost a week.
	 *
	 * ⚠ It is SAID and the session is not closed: who chooses what to do with it is the
	 *   caller, which knows whether it can still needs the client (`CODER.md` §4.2 — a
	 *   silent fallback produces two behaviours under the same label).
	 *
	 * ---------------------------------------------------------------------
	 * ⛔⛔ 22 AUGUST 2026 — THE LINE IS REACHED, AND WHAT IT SAID WAS FALSE
	 *
	 * `fasi/06` §7.2 kept this line among the *«code never exercised»*, and
	 * `banchi/06-b40` had concluded that the branch **cannot be reached
	 * from outside**: with the FIXED rectangle of `proposal()` the intersection is either
	 * the requested value or the empty set, so every `Format` that arrives
	 * necessarily carries the requested size.
	 *
	 * ⭐ `[M]` `banchi/06-b5-esiti-cattura.c` case 4: **it is reached**, 43 times
	 *    out of 480, and the door is not the producer — it is TIME.  Two
	 *    chained `capture_resize()` (the user DRAGGING the edge
	 *    of the window, the scene that §5.0-sexies names) and the `Format` of the
	 *    FIRST comes back when `chiesta_*` already carries the SECOND.  ⚠ It is a RACE —
	 *    43 hits out of 480 chains, not one in one — but a race **that a bench
	 *    can program**: the distance between the two calls is swept and the window
	 *    is found (mostly between 200 and 800 us).  ⭐ 3 sweeps out of 3 turned it
	 *    on.
	 *
	 * ⛔ ⇒ And so «granted» here does NOT mean «the compositor granted
	 *    something else»: in the only measured scene it means **«this is the answer
	 *    to the previous request»** — the line seen was *«requested 1602x1020,
	 *    granted 1202x806»*, and 1202x806 was exactly the previous
	 *    request.  The stream is healthy and catches up by itself at the next
	 *    `Format`.
	 *
	 * ⛔⛔ The previous line said *«the coordinate conversion is born
	 *     wrong and the pointer will go elsewhere»*: in that scene it is FALSE, and
	 *     a log that attributes a wrong cause costs more than a
	 *     silent log — it is the defect that `LEZIONI.md` §1.9 calls by name.
	 *     ⇒ Now the line states the FACT and the two possible motives, and points to the
	 *     place where the verdict is really given.
	 *
	 * ⚠ And we do not try to tell the two motives apart HERE: it was tried with a
	 *   counter («how many renegotiations I asked, how many I saw
	 *   come back») and ⛔ `[M]` it does not hold — a chain of two `update_params`
	 *   produces **a single** `Format`, so the two counts diverge forever and
	 *   the guard would turn off forever.  ⭐ The place that can tell them apart is
	 *   the one that sees the PIXELS. */
	if (capture_v->requested_width && capture_v->requested_height
	    && (capture_v->schema.size.width != capture_v->requested_width
	        || capture_v->schema.size.height != capture_v->requested_height))
	{
		if (!capture_v->measure_divergent)
			log_says(AREA,
			              "⛔ DIVERGENT SIZE: requested %ux%u, granted %ux%u.  ⚠ Two "
			              "motives, and from here they cannot be told apart: either the compositor "
			              "granted something else (§4.5 allows it, and then the coordinate "
			              "conversion would be born wrong), or this is the "
			              "answer to a SUPERSEDED request — `[M]` two "
			              "chained resizes, bench 06-b5 case 4.  ⭐ The "
			              "verdict is given by the FRAME (`DECISIONI.md` §5.0-sexies), "
			              "not by this line",
			              capture_v->requested_width, capture_v->requested_height,
			              capture_v->schema.size.width, capture_v->schema.size.height);
		capture_v->measure_divergent = TRUE;
	}
	else
		capture_v->measure_divergent = FALSE;

	/* ⛔ And the four consumption parameters are written by `consumer_parameters()`, in
	 *    a single place: `capture_resize()` repeats them too, and two lists
	 *    that must stay equal are two lists that diverge. */
	pw_stream_update_params(capture_v->flow, parameters,
	                        consumer_parameters(capture_v, &builder, parameters));
	pw_thread_loop_signal(capture_v->cycle, false);
}

/*
 * ⭐ The cursor metadata, read and handed to `cursore.c`.
 *
 * ⛔ IT IS READ BEFORE ANY `goto give_back`, and the reason was already written
 *    in the box of `on_process`: a buffer marked `CORRUPTED` is a buffer
 *    WITHOUT a frame, sent **precisely because** the cursor moved.  Whoever
 *    read the cursor after the discard would lose exactly the buffers that
 *    carry the cursor.
 *
 * ⚠ And we look at `spa_meta` and not `spa_buffer_find_meta_data`: we need the
 *   real SIZE of the metadata, or the checks in `cursore.c` have no
 *   limit against which to measure the bitmap pixels.
 */
static void look_cursor(Capture *capture_v, struct pw_buffer *bundle)
{
	struct spa_meta *meta;

	if (!capture_v->pointer_shape)
		return;

	meta = spa_buffer_find_meta(bundle->buffer, SPA_META_Cursor);
	if (!meta || !meta->data)
	{
		/* ⛔ «Not received» is NOT «hidden»: it is counted, and nothing is sent
		 *    on the wire.  Whoever reads zero `CURSOR_SHAPE` later must
		 *    be able to tell «the pointer was not there» from «we did not request the metadata,
		 *    or the producer did not give it». */
		capture_v->count.cursor_absent++;
		return;
	}

	capture_v->count.cursor_meta_seen++;
	if (!capture_v->logged_cursor)
	{
		capture_v->logged_cursor = TRUE;
		log_says(AREA, "⭐ the cursor metadata ARRIVES: %u bytes per buffer", meta->size);
	}

	if (cursor_metadata(capture_v->pointer_shape, meta->data, meta->size) < 0)
		capture_v->count.malformed_cursors++;
}

/* The damage: looked at, counted, and delivered as INFORMATION. */
static gboolean look_damage(Capture *capture_v, struct pw_buffer *bundle, CaptureRegion *regions,
                             guint *how_many_n, gboolean *covers_all)
{
	struct spa_meta *meta = spa_buffer_find_meta(bundle->buffer, SPA_META_VideoDamage);
	struct spa_meta_region *region;
	gboolean vista = FALSE;

	*how_many_n = 0;
	*covers_all = FALSE;

	if (!meta)
	{
		capture_v->count.missing_damage++;
		return FALSE;
	}
	spa_meta_for_each(region, meta)
	{
		if (!spa_meta_region_is_valid(region))
			break;
		vista = TRUE;
		if (region->region.position.x == 0 && region->region.position.y == 0 &&
		    region->region.size.width >= capture_v->schema.size.width &&
		    region->region.size.height >= capture_v->schema.size.height)
			*covers_all = TRUE;
		if (*how_many_n < MAX_REGIONS)
		{
			regions[*how_many_n].x = (uint32_t) MAX(0, region->region.position.x);
			regions[*how_many_n].y = (uint32_t) MAX(0, region->region.position.y);
			regions[*how_many_n].width_px = region->region.size.width;
			regions[*how_many_n].height_px = region->region.size.height;
			(*how_many_n)++;
		}
		else
		{
			/* We err on the safe side: more regions than we carry
			 * ⇒ we declare «everything counts» instead of delivering part of them. */
			*how_many_n = 0;
			*covers_all = TRUE;
			break;
		}
	}
	if (!vista)
	{
		capture_v->count.missing_damage++;
		return FALSE;
	}
	if (*covers_all)
		capture_v->count.full_damage++;
	else
		capture_v->count.partial_damage++;
	return TRUE;
}

static void on_process(void *data_v)
{
	Capture *capture_v = data_v;
	struct pw_buffer *bundle;
	struct spa_data *piano;
	struct spa_meta_header *header;
	CaptureRegion regions[MAX_REGIONS];
	CaptureFrameInfo info = { 0 };
	CaptureDelivery delivery;
	guint how_many_n = 0;
	gboolean covers_all = FALSE, declared_damage;
	uint32_t step, offset;
	guint64 available, byte;
	guint i;
	gboolean known;
	/* ⭐ The RETENTION: when this becomes TRUE the buffer does NOT go back to PipeWire
	 *    at the end of the function — it will be returned by `capture_stopped_free()`, that is by
	 *    the consumer, when it has finished reading it.  See the box at the top. */
	gboolean held = FALSE;

	bundle = pw_stream_dequeue_buffer(capture_v->flow);
	if (!bundle)
		return;

	/* ⛔ BEFORE ANY DISCARD: see the box of `look_cursor`. */
	look_cursor(capture_v, bundle);

	if (bundle->buffer->n_datas == 0)
		goto give_back;
	piano = &bundle->buffer->datas[0];
	capture_v->count.arrived++;

	/* How many distinct buffers the producer recycles: Mutter uses four, and
	 * knowing it helps read the rest. */
	known = FALSE;
	for (i = 0; i < capture_v->count.distinct_buffers; i++)
		if (capture_v->fd_seen[i] == (int) piano->fd)
			known = TRUE;
	if (!known && capture_v->count.distinct_buffers < FD_MAX)
		capture_v->fd_seen[capture_v->count.distinct_buffers++] = (int) piano->fd;

	/* ⛔ THE TYPES ARE ALL COLLECTED, not just the last one: if the
	 *    producer changed route midway, a single line would state one
	 *    route for two different populations — which is form E2. */
	known = FALSE;
	for (i = 0; i < capture_v->count.how_many_types; i++)
		if (capture_v->count.seen_types[i] == buffer_da_spa(piano->type))
			known = TRUE;
	if (!known && capture_v->count.how_many_types < G_N_ELEMENTS(capture_v->count.seen_types))
	{
		if (capture_v->count.how_many_types == 0)
			capture_v->first_raw_type = piano->type;
		capture_v->count.seen_types[capture_v->count.how_many_types++] = buffer_da_spa(piano->type);
	}

	if (!capture_v->type_logged)
	{
		capture_v->type_logged = TRUE;
		/* ⛔ Said ONCE and in full, with next to it what it does NOT prove. */
		log_says(AREA,
		              "the frames arrive as %s (%u planes) — ⚠ and this does NOT say where "
		              "Mutter renders: it is the answer to what we asked for (E1)",
		              capture_buffer_name(buffer_da_spa(piano->type)), bundle->buffer->n_datas);
	}

	if (!piano->chunk)
	{
		capture_v->count.without_pixel++;
		goto give_back;
	}

	/*
	 * ⛔ THE BUFFER MAY NOT CONTAIN A FRAME, AND A SINGLE BIT SAYS SO.
	 *
	 *    With the cursor in METADATA mode — which is the right mode, because the
	 *    pointer has a channel of its own — a mouse movement produces a buffer
	 *    with no drawing: inside are the stale pixels of two to four frames
	 *    earlier, and the only indication is `SPA_CHUNK_FLAG_CORRUPTED`, which there
	 *    means «do not look at the content».  ⛔ `STUDI.md` §gnome §8.3: stale
	 *    cursor-only buffers **exist on Mutter too**.
	 *
	 * ⚠ We discard the FRAME, not the buffer: the cursor metadata that
	 *   travels with it stays valid, and is indeed the only thing that buffer
	 *   was sent for.  When the pointer channel exists, it will be read
	 *   here.
	 */
	if (piano->chunk->flags & SPA_CHUNK_FLAG_CORRUPTED)
	{
		capture_v->count.cursor_only++;
		goto give_back;
	}
	header = spa_buffer_find_meta_data(bundle->buffer, SPA_META_Header, sizeof *header);
	if (!header)
		capture_v->count.without_header++;
	else if (header->flags & SPA_META_HEADER_FLAG_CORRUPTED)
	{
		capture_v->count.cursor_only++;
		goto give_back;
	}

	declared_damage = look_damage(capture_v, bundle, regions, &how_many_n, &covers_all);

	/* ⛔ The authoritative stride is this one, and if it is missing none is computed. */
	step = (uint32_t) MAX(0, piano->chunk->stride);
	if (step == 0)
	{
		capture_v->count.stride_zero++;
		goto give_back;
	}
	offset = (uint32_t) piano->chunk->offset;

	/* --- the four facts, frozen for this frame -------------------------- */
	memset(&delivery, 0, sizeof delivery);
	delivery.known = capture_v->known_format;
	delivery.requested_route = capture_v->route;
	delivery.buffer_requested =
	    capture_v->route == CAPTURE_ROUTE_CARD ? CAPTURE_BUFFER_DMABUF : CAPTURE_BUFFER_MEMFD;
	delivery.buffer_declared = buffer_da_spa(piano->type);
	delivery.buffer_declared_raw = piano->type;
	delivery.distinct_buffers = capture_v->count.distinct_buffers;
	delivery.raw_format = capture_v->schema.format;
	delivery.schema = capture_color_name(capture_v->schema.format);
	delivery.bit_per_channel = bit_per_channel(capture_v->schema.format);
	delivery.source_bit = delivery.bit_per_channel > 0 ? CAPTURE_SOURCE_FORMAT
	                                                 : CAPTURE_SOURCE_UNDECLARED;
	delivery.width_px = capture_v->schema.size.width;
	delivery.height_px = capture_v->schema.size.height;
	delivery.stride = step;
	delivery.stride_read = TRUE;
	delivery.byte = (guint64) step * capture_v->schema.size.height;
	delivery.modifier = capture_v->schema.modifier;
	delivery.raw_range = capture_v->schema.color_range;
	delivery.raw_matrix = capture_v->schema.color_matrix;
	delivery.raw_transfer = capture_v->schema.transfer_function;
	delivery.raw_primaries = capture_v->schema.color_primaries;
	delivery.source_range =
	    capture_v->schema.color_range ? CAPTURE_SOURCE_PRODUCER : CAPTURE_SOURCE_UNDECLARED;
	delivery.source_matrix =
	    capture_v->schema.color_matrix ? CAPTURE_SOURCE_PRODUCER : CAPTURE_SOURCE_UNDECLARED;

	/* --- how many bytes there really are -------------------------------- */
	available = piano->maxsize > offset ? (guint64) piano->maxsize - offset : 0;
	byte = piano->chunk->size > 0 ? (guint64) piano->chunk->size : available;
	if (byte > available)
		byte = available;

	/* ⛔⛔ THE DECLARED GEOMETRY MUST FIT INSIDE THE DELIVERED BYTES — the
	 *     guard born while refuting, on the night of 15 August 2026, and before that it
	 *     served no purpose.
	 *
	 * ⚠ The size comes from the negotiated FORMAT (`capture_v->schema`), the stride and the
	 *   bytes come from the CHUNK of the real buffer: two sources, and between a
	 *   renegotiation and the new buffers they can belong to two different
	 *   generations.  ⛔ With a fixed canvas they could not diverge;
	 *   `capture_resize()` makes it possible.
	 *
	 * ⛔ And the damage is not a skewed image: the consumer reads
	 *   `width x 4` bytes per row, for `height` rows.  If the stride is
	 *   shorter than the declared width — that is in the «the canvas GROWS» direction —
	 *   the last row ends **beyond the copied memory**, and the child dies
	 *   taking a user's stage with it.
	 *
	 * ⇒ It is discarded and COUNTED, which is the same rule as `stride == 0`: one
	 *   frame fewer costs 16 ms, an out-of-bounds read costs the
	 *   process. */
	/* ⚠ Only on the MEMORY route: on DMA-BUF the pixels are not here — there is
	 *   a descriptor that lives on the card — and `chunk->size` describes
	 *   no copy to read.  Applying the guard there too would discard
	 *   every card frame silently, which is the opposite defect. */
	if (capture_v->route == CAPTURE_ROUTE_MEMORY
	    && (capture_v->schema.size.width == 0 || capture_v->schema.size.height == 0
	        || step < capture_v->schema.size.width * 4u
	        || byte < (guint64) step * capture_v->schema.size.height))
	{
		capture_v->count.inconsistent_geometry++;
		if (capture_v->count.inconsistent_geometry == 1)
			log_says(AREA,
			              "⛔ frame DISCARDED: the format declares %ux%u but the buffer "
			              "carries stride %u and %" G_GUINT64_FORMAT " bytes (%"
			              G_GUINT64_FORMAT " would be needed).  ⚠ It is the window between a renegotiation and "
			              "the new buffers: the reader would go beyond the delivered memory",
			              capture_v->schema.size.width, capture_v->schema.size.height, step,
			              byte, (guint64) step * capture_v->schema.size.height);
		goto give_back;
	}

	info.pixel = NULL;
	info.byte = byte;
	info.fd = piano->fd >= 0 ? (int) piano->fd : -1;
	info.offset = offset;
	info.stride = step;
	info.seq = header ? (uint64_t) header->seq : 0;
	info.pts = header ? (int64_t) header->pts : 0;
	info.seq_valid = header != NULL;
	info.damage = how_many_n ? regions : NULL;
	info.how_many_regions = how_many_n;
	info.declared_damage = declared_damage;
	info.damage_covers_all = covers_all;
	info.idx = capture_v->count.arrived;
	info.delivery = &delivery;

	/*
	 * ⛔ AND HERE WE LOOK AT THE TYPE **BEFORE** THE POINTER.  A DMA-BUF has no
	 *    `data`: it is a descriptor that lives on the card, and the pointer stays
	 *    NULL.  The check «no pointer, no frame» — right for
	 *    memory — would here discard everything silently.
	 */
	if (piano->type != SPA_DATA_DmaBuf)
	{
		if (!piano->data || byte == 0)
		{
			capture_v->count.without_pixel++;
			goto give_back;
		}
		info.pixel = (const uint8_t *) piano->data + offset;
	}
	/* ⛔ AND ON THE CARD THE TWO FACTS NEEDED ARE THE DESCRIPTOR AND THE NAME
	 *    OF THE FORMAT: without the first there is nothing to import, without the second we
	 *    would pass VA-API an invented fourcc — and VA-API accepts and gets it wrong
	 *    (`LEZIONI.md` §1.8).  ⇒ It is discarded and COUNTED, as for `stride == 0`.
	 * ⚠ A single plane: Mutter's DMA-BUF is LINEAR and BGRx `[M]`, that is one
	 *   plane.  If one day two arrived, this module cannot
	 *   describe them and must say so instead of delivering half of it. */
	else if (info.fd < 0 || drm_da_spa(capture_v->schema.format) == 0
	         || bundle->buffer->n_datas != 1)
	{
		capture_v->count.without_pixel++;
		if (capture_v->count.without_pixel == 1)
			log_says(AREA,
			              "⛔ DMA-BUF DISCARDED: fd %d, format «%s» (%u), %u planes.  On the "
			              "card route we need a descriptor, a format that can be "
			              "NAMED in DRM, and a single plane — ⚠ and this is NOT «the "
			              "producer does not deliver»: it is «I cannot describe it»",
			              info.fd, capture_color_name(capture_v->schema.format),
			              capture_v->schema.format, bundle->buffer->n_datas);
		goto give_back;
	}

	if (capture_v->on_frame)
		capture_v->on_frame(&info, capture_v->data_v);

	/* --- the slot of the LAST frame --------------------------------------- *
	 *
	 * ⛔⛔⛔ AND UNTIL 15 AUGUST 2026 HERE THERE WAS `if (someone_waiting && !slot_full)`,
	 *      that is **the frame was thrown away if nobody was waiting for it at
	 *      that instant**.  The comment that justified it said: «copying 8 MB
	 *      for nobody would be work inside the real-time callback, done
	 *      for nothing».  ⛔ The reasoning holds for the steady state and **gets
	 *      wrong the case the user sees**.
	 *
	 * ⭐ THE SYMPTOM, reported by the user on 15 August: *«I type the `exit` command and
	 *    the terminal seems frozen: as soon as I move the mouse it closes
	 *    properly»*.
	 *
	 * ⇒ THE MECHANISM: the closing window produces a BURST of
	 *   frames.  We take the first and spend ~20 ms converting and
	 *   compressing it; ⛔ all those that arrive in those 20 ms find
	 *   `someone_waiting == FALSE` and **are thrown away**, including **the last one** —
	 *   the one with the window already gone.  Then the scene is still, Mutter
	 *   sends nothing more (rate 0/1: «a frame when something changes»),
	 *   and the user is left looking at the FIRST frame of the burst.  The
	 *   mouse movement produces a new frame, and the screen catches up.
	 *
	 * ⭐ THE CURE: the last one is ALWAYS kept.  A single slot, and the most
	 *    recent wins — which is also the right policy for a remote desktop: an
	 *    old frame is of no use to anyone.
	 *
	 * ⚠ And the cost the old comment feared is paid LESS than before, not
	 *   more: the buffer is REUSED (`slot_capacity`), so the real-time
	 *   callback does a `memcpy` and no longer a `g_free`+`g_malloc` of 8 MB.
	 */
	g_mutex_lock(&capture_v->lock);
	{
		CaptureStopped *f = &capture_v->slot;

		if (capture_v->slot_full)
			capture_v->overwritten++;

		/* ⛔⭐ AND THE BUFFER THAT WAS IN THE SLOT IS GIVEN BACK **NOW**, before
		 *     overwriting it: it is a buffer nobody consumed — the most
		 *     recent wins — and if it did not go back the producer would
		 *     lose one at every skipped frame.  ⚠ We are already on the real-time
		 *     thread, which holds the loop for us: here we call the bare
		 *     `pw_stream_queue_buffer` and not `release_withheld`, which
		 *     would take again a lock that is already ours. */
		if (f->held_buffer)
		{
			pw_stream_queue_buffer(capture_v->flow, (struct pw_buffer *) f->held_buffer);
			capture_v->held_returned++;
			f->held_buffer = NULL;
			f->owner = NULL;
		}

		f->byte = info.pixel ? byte : 0;
		f->alloc_us = 0;
		f->copy_us = 0;
		f->in_slot_us = 0;
		f->measure_us = 0;
		f->on_card = FALSE;
		f->fd = -1;
		f->offset = 0;
		f->format_drm = 0;
		f->modifier = 0;
		f->generation = capture_v->buffer_generation;

		/* ═══════════════════════════════════════════════════════════════════
		 * ⭐⭐⭐ ZERO COPY — and here NOTHING is done, which is the point.
		 *
		 * On the card route the frame **is already where it is needed**: on the
		 * GPU.  ⛔ There is no `memcpy`, no `g_malloc`, and the two entries of the
		 * segment stay zero — a zero that means **«this work does not
		 * exist»**, not «it is free», and whoever reads the table must know it.
		 *
		 * ⇒ The `pw_buffer` is held and the DESCRIPTOR is delivered.  The
		 *   descriptor is not a copy: it is an `fd` pointing to the card's
		 *   memory, and as long as we hold it the producer does not repaint
		 *   inside it.
		 * ═══════════════════════════════════════════════════════════════════ */
		if (capture_v->route == CAPTURE_ROUTE_CARD)
		{
			f->on_card = TRUE;
			f->fd = info.fd;
			f->offset = offset;
			f->format_drm = drm_da_spa(capture_v->schema.format);
			f->modifier = capture_v->schema.modifier;
			f->byte = (guint64) step * capture_v->schema.size.height;
			f->held_buffer = bundle;
			f->owner = capture_v;
			held = TRUE;
			capture_v->held_count++;
		}
		else if (info.pixel)
		{
			/* ⛔ WE COPY, WE DO NOT KEEP THE POINTER: on the next round the producer
			 *    writes into it again, and the delivered frame would be a different one
			 *    from the one whose damage and sequence we report — two measurements
			 *    under the same label.
			 * ⭐ But the allocation is REUSED when it is enough: it is the same size for
			 *    the whole session, except at a canvas change. */
			if (!f->pixel || capture_v->slot_capacity < byte)
			{
				/* ⛔ The `g_malloc` is TIMED, and it is not pedantry: when the
				 *    slot is emptied at every take (see `capture_take`) this
				 *    line reallocates **at every frame**, and a new 10 MB
				 *    mapping is paid in page faults the first time it is
				 *    touched — that is inside the `memcpy` below. */
				uint64_t ta = current_us();
				g_free(f->pixel);
				f->pixel = g_malloc(byte);
				capture_v->slot_capacity = byte;
				f->alloc_us = current_us() - ta;
			}
			{
				uint64_t tc = current_us();
				memcpy(f->pixel, info.pixel, byte);
				f->copy_us = current_us() - tc;
			}
		}
		else if (f->pixel)
		{
			g_free(f->pixel);
			f->pixel = NULL;
			capture_v->slot_capacity = 0;
		}
		f->stride = step;
		f->width_px = delivery.width_px;
		f->height_px = delivery.height_px;
		f->seq = info.seq;
		f->pts = info.pts;
		f->seq_valid = info.seq_valid;
		f->declared_damage = declared_damage;
		f->damage_covers_all = covers_all;
		f->idx = info.idx;
		f->delivery = delivery;
		/* ⛔ The instant is taken HERE, after the copy: from this moment the
		 *    frame is ready and whoever takes it takes it aged by
		 *    whatever passes from now on. */
		f->arrival_us = current_us();
		capture_v->slot_full = TRUE;
		g_cond_broadcast(&capture_v->news);
	}
	g_mutex_unlock(&capture_v->lock);

	if (capture_v->count.arrived % 300 == 0)
		log_detail(AREA,
		                   "over %" G_GUINT64_FORMAT " frames: %u distinct buffers, damage "
		                   "full %" G_GUINT64_FORMAT " partial %" G_GUINT64_FORMAT " absent %"
		                   G_GUINT64_FORMAT ", without header %" G_GUINT64_FORMAT
		                   ", cursor-only %" G_GUINT64_FORMAT
		                   ", ⭐ replaced in the slot %" G_GUINT64_FORMAT
		                   " (before 15 Aug they were LOST)",
		                   capture_v->count.arrived, capture_v->count.distinct_buffers,
		                   capture_v->count.full_damage, capture_v->count.partial_damage,
		                   capture_v->count.missing_damage, capture_v->count.without_header,
		                   capture_v->count.cursor_only, capture_v->overwritten);

give_back:
	/* ⛔ AND HERE IS THE RELEASE CURE, in one line: a HELD buffer does not
	 *    go back to the producer now.  ⚠ Without this guard the DMA-BUF
	 *    would go back to Mutter at the very instant we hand it to the
	 *    reader, and it would be **exactly** the defect of the two alternating
	 *    screens (`LEZIONI.md` §8) — with the difference that this time we
	 *    would have written it ourselves. */
	if (!held)
		pw_stream_queue_buffer(capture_v->flow, bundle);
}

/*
 * ⭐⭐ WHEN THE PRODUCER REMAKES THE BUFFERS — and the number that comes out is needed
 *     downstream, not here.
 *
 * ⛔ THE FACT that makes them exist: a DMA-BUF `fd` is a descriptor
 *    number, and descriptor numbers **are recycled**.  After a
 *    renegotiation (`capture_resize`) or a wake-up
 *    (`capture_wake`) PipeWire frees the old buffers and allocates
 *    new ones: the kernel can reassign the **same numbers**.  ⇒ Whoever
 *    caches «fd 42 → VA-API surface» would end up with a surface pointing
 *    to memory of another generation, and the symptom would be **an old
 *    image**, without any error.
 *
 * ⇒ Here we only count, and the number travels in the `CaptureStopped`.  ⚠ We do not
 *   try to invalidate anything from this side: the importing module is the one
 *   that knows what it imported, and an invalidation done from here would be a
 *   decision taken where the facts are not.
 */
/*
 * ⛔⛔ THE GENERATION BELONGS TO THE PROCESS, NOT TO THE CAPTURE — 22 Sep 2026, the
 *      user's test on KDE: the screen FLICKERED between three images (the desktop,
 *      the log-out screen of the PREVIOUS session, and black).
 *
 * `[M]` The counter lived in the `Capture` and restarted from 0 at every `g_new0`.
 *   After «Log Out» and a new login the session is reborn IN THE SAME child: the
 *   capture is new, the encoder is not.  Six `add_buffer` gave 6 to the
 *   old one and 6 to the new one ⇒ `import_dmabuf` saw no change, did not
 *   drop the cache, and the descriptors recycled with the previous numbers
 *   found again the surfaces of the dead session.  Log of the `kde`
 *   box: at the two good rebirths «dropping the 4 imported surfaces», at the two
 *   bad ones no line.
 * ⇒ A single counter for the whole process: two captures can no longer
 *   have the same generation, whatever happens in between.
 */
static uint64_t new_generation(void)
{
	static uint64_t latest;

	return __atomic_add_fetch(&latest, 1, __ATOMIC_RELAXED);
}

static void on_buffer_added(void *data_v, struct pw_buffer *bundle)
{
	Capture *capture_v = data_v;
	(void) bundle;
	capture_v->buffer_generation = new_generation();
}

/*
 * ⛔⛔ AND THIS IS THE OTHER HALF OF THE RETENTION, and it is the one that without a
 *      box nobody would put back: **PipeWire frees the buffers even when
 *      we are the ones holding them.**  `remove_buffer` does not ask permission.
 *
 * ⇒ Two things, and they are in two places because the held buffers can be
 *   two (one held in the slot, one in the hands of the reader):
 *
 *   1. the one IN THE SLOT is let go here, under the lock: the pointer
 *      lives in a structure we own, so it is zeroed;
 *   2. the one IN THE HANDS OF THE READER cannot be reached from here — and it need not be.  The
 *      `CaptureStopped` carries the **generation** it was born with, and
 *      `capture_stopped_free()` compares: if it is no longer that one, the buffer is not
 *      given back, because it no longer exists.  ⛔ Giving it back would be writing into
 *      a freed `pw_buffer` — a defect that shows up at
 *      resize, that is in the place where nobody looks.
 */
static void on_buffer_removed(void *data_v, struct pw_buffer *bundle)
{
	Capture *capture_v = data_v;

	g_mutex_lock(&capture_v->lock);
	if (capture_v->slot.held_buffer == bundle)
	{
		capture_v->slot.held_buffer = NULL;
		capture_v->slot.owner = NULL;
		capture_v->slot_full = FALSE;
		capture_v->held_returned++;
	}
	capture_v->buffer_generation = new_generation();
	g_mutex_unlock(&capture_v->lock);
}

/*
 * Gives back a held buffer.  ⛔ It runs on the CONSUMER's thread, not on the
 * real-time one: that is why it takes the PipeWire loop lock.
 *
 * ⚠ The order of the two locks is always `loop → lock`, never the reverse:
 *   `on_process` and `on_buffer_removed` run with the loop already held and take the
 *   lock inside.  Reversing it here would be a deadlock that
 *   shows up once in a while, under load.
 */
static void release_withheld(Capture *capture_v, struct pw_buffer *bundle, uint64_t generation)
{
	if (!capture_v || !bundle || !capture_v->cycle || !capture_v->flow)
		return;
	pw_thread_loop_lock(capture_v->cycle);
	/* ⛔ The comparison is the point: if the producer remade the buffers, this
	 *    `pw_buffer` no longer exists and giving it back would write into freed memory. */
	if (capture_v->buffer_generation == generation)
		pw_stream_queue_buffer(capture_v->flow, bundle);
	capture_v->held_returned++;
	pw_thread_loop_unlock(capture_v->cycle);
}

static const struct pw_stream_events events = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = on_state,
	.param_changed = on_parameters,
	/* ⭐ The two that count the buffer GENERATION: without them, a downstream import
	 *    cache would point to dead buffers after every
	 *    renegotiation.  See the box above `on_buffer_removed`. */
	.add_buffer = on_buffer_added,
	.remove_buffer = on_buffer_removed,
	.process = on_process,
};

/* ------------------------------------------------------------------ *
 *  The format proposal
 * ------------------------------------------------------------------ */

/*
 * ⛔ WE LIST ONLY WHAT WE CAN READ, and in a declared order.
 *
 * Listing formats the rest of the chain does not handle would be a silent
 * defect: no point downstream looks at the format actually negotiated, so
 * if the compositor chose an RGB variant, red and blue would come out
 * swapped without any error.
 *
 * ⛔ And `CAPTURE_COLOR_10BIT` proposes **only** the ten-bit formats.
 *    Putting BGRx in the same list would negotiate BGRx and we would
 *    learn nothing: the question «do ten bits exist from this source?» has
 *    an answer only if the refusal is a refusal.
 */
static uint32_t how_many_colors(CaptureColor color, uint32_t listing[8])
{
	switch (color)
	{
	case CAPTURE_COLOR_BGRA:
		listing[0] = SPA_VIDEO_FORMAT_BGRA;
		listing[1] = SPA_VIDEO_FORMAT_BGRx;
		return 2;
	case CAPTURE_COLOR_10BIT:
		listing[0] = SPA_VIDEO_FORMAT_xBGR_210LE;
		listing[1] = SPA_VIDEO_FORMAT_xRGB_210LE;
		listing[2] = SPA_VIDEO_FORMAT_ABGR_210LE;
		listing[3] = SPA_VIDEO_FORMAT_ARGB_210LE;
		return 4;
	default:
		listing[0] = SPA_VIDEO_FORMAT_BGRx;
		listing[1] = SPA_VIDEO_FORMAT_BGRA;
		return 2;
	}
}

static uint64_t mod_card[16];
static int mod_card_count;

void capture_modifiers_card(const uint64_t *modifiers, int how_many)
{
	mod_card_count = 0;
	for (int i = 0; modifiers && i < how_many && i < (int)G_N_ELEMENTS(mod_card); i++)
		mod_card[mod_card_count++] = modifiers[i];
}

static const struct spa_pod *proposal(struct spa_pod_builder *builder, uint32_t width_px,
                                      uint32_t height_px, uint32_t frames_per_second,
                                      CaptureColor color, gboolean with_modifiers)
{
	struct spa_rectangle gauge = SPA_RECTANGLE(width_px, height_px);
	struct spa_fraction cadence = SPA_FRACTION(0, 1);
	struct spa_fraction min_cadence = SPA_FRACTION(1, 1);
	struct spa_fraction max_cadence = SPA_FRACTION(MAX(1u, frames_per_second), 1);
	struct spa_pod_frame border[3];
	uint32_t listing[8];
	uint32_t how_many = how_many_colors(color, listing);
	uint32_t i;

	spa_pod_builder_push_object(builder, &border[0], SPA_TYPE_OBJECT_Format,
	                            SPA_PARAM_EnumFormat);
	spa_pod_builder_add(builder, SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
	                    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), 0);

	/* The colours as a choice: the first value is the preferred one, and it must be repeated —
	 * it is the form of `SPA_POD_CHOICE_ENUM_Id`, built by hand because the
	 * number of entries changes. */
	spa_pod_builder_prop(builder, SPA_FORMAT_VIDEO_format, 0);
	spa_pod_builder_push_choice(builder, &border[1], SPA_CHOICE_Enum, 0);
	spa_pod_builder_id(builder, listing[0]);
	for (i = 0; i < how_many; i++)
		spa_pod_builder_id(builder, listing[i]);
	spa_pod_builder_pop(builder, &border[1]);

	if (with_modifiers)
	{
		/*
		 * ⛔ THE MODIFIER MUST BE DECLARED `MANDATORY | DONT_FIXATE`, or the value
		 *    is chosen by PipeWire instead of being agreed with the allocator.
		 *
		 * `DRM_FORMAT_MOD_LINEAR` first, and it is a gift from kpipewire: RadeonSI
		 * REFUSES buffers with DCC and iHD — the driver of the card Mutter picks
		 * here — ACCEPTS them and then forces LINEAR internally, that is it accepts and gets it wrong
		 * silently.  `DRM_FORMAT_MOD_INVALID` stays as second choice:
		 * it means «you decide the layout and tell me».
		 *
		 * ⚠ And `[R]` Mutter offers a proposal with modifiers **only if it has some for
		 *   that format** (`meta-screen-cast-stream-src.c`: if
		 *   `meta_screen_cast_query_modifiers` returns empty, that format enters only
		 *   the list without modifiers).  ⇒ If the card gives none, the card
		 *   route does not exist, and there is no error saying so: it is said by
		 *   the type of buffer that arrives, and that is why it is verified.
		 */
		spa_pod_builder_prop(builder, SPA_FORMAT_VIDEO_modifier,
		                     SPA_POD_PROP_FLAG_MANDATORY | SPA_POD_PROP_FLAG_DONT_FIXATE);
		spa_pod_builder_push_choice(builder, &border[2], SPA_CHOICE_Enum, 0);
		spa_pod_builder_long(builder, DRM_FORMAT_MOD_LINEAR);
		spa_pod_builder_long(builder, DRM_FORMAT_MOD_LINEAR);
		/* ⭐ 6 Oct 2026: only where the card refuses linear — see
		 *    `capture_modifiers_card()` in cattura.h. */
		for (i = 0; i < (uint32_t)mod_card_count; i++)
			spa_pod_builder_long(builder, mod_card[i]);
		spa_pod_builder_long(builder, DRM_FORMAT_MOD_INVALID);
		spa_pod_builder_pop(builder, &border[2]);
	}

	/* ⛔ The size as a FIXED rectangle: an open range would let
	 *    Mutter choose, and it chooses 1280×720 and nobody notices until
	 *    they look at the pixels. */
	spa_pod_builder_add(builder, SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&gauge),
	                    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cadence),
	                    SPA_FORMAT_VIDEO_maxFramerate,
	                    SPA_POD_CHOICE_RANGE_Fraction(&max_cadence, &min_cadence,
	                                                  &max_cadence),
	                    0);
	return spa_pod_builder_pop(builder, &border[0]);
}

/* ------------------------------------------------------------------ *
 *  Life cycle
 * ------------------------------------------------------------------ */

/* ------------------------------------------------------------------ *
 *  ⭐⭐ THE SECOND SOURCE — wlroots, the pull direction.  `cattura.h`.
 * ------------------------------------------------------------------ */

Capture *capture_start_wlr(uint32_t width_px, uint32_t height_px,
                           uint32_t frames_per_second, CaptureRoute route,
                           CaptureColor color, GError **mistake)
{
	Capture *c = g_new0(Capture, 1);
	uint32_t output_w = 0, output_h = 0;

	c->wlr = wlr_open(mistake);
	if (!c->wlr) {
		g_free(c);
		return NULL;
	}
	c->route = route;
	c->color = color;
	c->requested_width = width_px;
	c->requested_height = height_px;
	c->requested_per_second = frames_per_second;

	/*
	 * ⛔⛔ AND THE DIVERGENCE IS DECLARED AT ONCE, not when the screen of the
	 *     wrong size is seen.
	 *
	 * `[M]` 20 Sep 2026: a labwc headless output is born **1280×720**
	 * hard-wired, and no protocol creates one of the wanted size.  ⇒ If the
	 * client asked for another one, the pixels that will arrive **are not of
	 * that size** — and whoever reads the log must know it from the first line,
	 * not deduce it from an image that does not add up.
	 */
	wlr_measure(c->wlr, &output_w, &output_h);
	if (output_w != width_px || output_h != height_px) {
		g_autoptr(GError) size_error = NULL;
		WlrSizeOutcome e;

		log_says(AREA,
		              "wlroots: the requested canvas is %ux%u and the output is %ux%u — "
		              "asking the compositor for it (on this family the size does not "
		              "enter the birth: it is given afterwards, with the output protocol)",
		              width_px, height_px, output_w, output_h);
		e = wlr_ask_size(c->wlr, width_px, height_px, 2.0, &size_error);
		wlr_measure(c->wlr, &output_w, &output_h);
		/*
		 * ⛔⛔ AND THE JUDGEMENT IS GIVEN BY THE SIZE READ BACK, NOT BY THE OUTCOME.
		 *
		 * `DECISIONI.md` §5.0-sexies: asking for the size the output already has
		 * answers «succeeded» without sending anything, and an old serial
		 * answers «cancelled» without doing anything.  ⇒ We look at the output.
		 */
		if (output_w == width_px && output_h == height_px)
			log_says(AREA,
			              "⭐ wlroots: the output is NOW %ux%u, the size requested by the "
			              "client — and I do not say so because the request succeeded, "
			              "I say so because I read it back",
			              output_w, output_h);
		else
			log_says(AREA,
			              "⛔ wlroots: I asked for %ux%u and the output stayed %ux%u "
			              "(outcome of the request: %s%s%s).  ⚠ The frames will be "
			              "%ux%u, and it is NOT an encoder fault: it is this "
			              "line",
			              width_px, height_px, output_w, output_h,
			              e == WLR_SIZE_REQUESTED      ? "accepted but without effect"
			              : e == WLR_SIZE_UNCHANGED   ? "already so (and it was not)"
			              : e == WLR_SIZE_REFUSED  ? "refused"
			              : e == WLR_SIZE_CANCELLED  ? "cancelled (old serial)"
			                                           : "the compositor cannot change it",
			              size_error ? " — " : "",
			              size_error ? size_error->message : "",
			              output_w, output_h);
	}

	/*
	 * ⭐⭐ THE CARD ROUTE — `wlroots.c`, the box at the top.
	 *
	 * ⛔ The «no» does NOT make the birth fail: memory works, and it is the
	 *    fallback.  But it is SAID, with the reason — and `c->route` stays the
	 *    requested one, so `capture_delivery()` shows the pair «CARD requested,
	 *    MEMORY arrived» instead of rewriting the question to make it add up.
	 */
	if (route == CAPTURE_ROUTE_CARD) {
		g_autoptr(GError) reason_text = NULL;

		if (!wlr_ask_card(c->wlr, &reason_text))
			log_says(AREA,
			              "⛔ wlroots: the CARD route was requested and it is NOT "
			              "possible — %s.  ⇒ DECLARED FALLBACK: the pixels go through "
			              "MEMORY, and the segment numbers include the copy",
			              reason_text ? reason_text->message : "with no reason");
	}

	log_says(AREA,
	              "⭐ wlroots: PULL source opened on output «%s» — one frame "
	              "per request, no PipeWire node.  The pace is decided by our "
	              "loop, not by the compositor",
	              wlr_output_name(c->wlr));
	return c;
}

Capture *capture_start(uint32_t node, uint32_t width_px, uint32_t height_px,
                       uint32_t frames_per_second, CaptureRoute route, CaptureColor color,
                       CaptureFrame on_frame, CaptureEnd su_fine, gpointer data_v,
                       GError **mistake)
{
	static gsize initialized = 0;
	Capture *capture_v = g_new0(Capture, 1);
	uint8_t space[2048];
	struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(space, sizeof space);
	const struct spa_pod *parameters[1];
	gint64 expiry;

	if (g_once_init_enter(&initialized))
	{
		pw_init(NULL, NULL);
		g_once_init_leave(&initialized, 1);
	}

	capture_v->on_frame = on_frame;
	capture_v->su_fine = su_fine;
	capture_v->data_v = data_v;
	capture_v->route = route;
	capture_v->color = color;
	capture_v->requested_width = width_px;
	capture_v->requested_height = height_px;
	capture_v->requested_per_second = frames_per_second;
	g_mutex_init(&capture_v->lock);
	g_cond_init(&capture_v->news);

	/* ⭐ The cursor module is ALWAYS born, even if nobody listens: that way the
	 *    counters answer «does the metadata arrive?» without depending on who
	 *    consumes it.  ⚠ If it is not born we do not fail: the pixels are worth more than the
	 *    pointer (`CODER.md` §4.2), but the fallback is SAID. */
	capture_v->pointer_shape = cursor_open(cursor_bounce, capture_v);
	if (!capture_v->pointer_shape)
		log_says(AREA, "⛔ FALLBACK: the cursor module did not open — the pointer "
		                    "shape will not be sent (the frames will, all of them)");

	capture_v->cycle = pw_thread_loop_new("remotix-cattura", NULL);
	if (!capture_v->cycle)
	{
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED, "PipeWire loop not created");
		goto fault;
	}
	capture_v->context = pw_context_new(pw_thread_loop_get_loop(capture_v->cycle), NULL, 0);
	if (!capture_v->context)
	{
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED, "PipeWire context not created");
		goto fault;
	}

	pw_thread_loop_lock(capture_v->cycle);
	if (pw_thread_loop_start(capture_v->cycle) < 0)
	{
		pw_thread_loop_unlock(capture_v->cycle);
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED, "PipeWire thread not started");
		goto fault;
	}
	capture_v->core = pw_context_connect(capture_v->context, NULL, 0);
	if (!capture_v->core)
	{
		pw_thread_loop_unlock(capture_v->cycle);
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED, "connection to PipeWire failed");
		goto fault;
	}
	capture_v->flow = pw_stream_new(capture_v->core, "remotix-cattura",
	                                pw_properties_new(PW_KEY_MEDIA_TYPE, "Video",
	                                                  PW_KEY_MEDIA_CATEGORY, "Capture",
	                                                  PW_KEY_MEDIA_ROLE, "Screen", NULL));
	if (!capture_v->flow)
	{
		pw_thread_loop_unlock(capture_v->cycle);
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED, "PipeWire stream not created");
		goto fault;
	}
	pw_stream_add_listener(capture_v->flow, &capture_v->hook, &events, capture_v);

	/* ⛔ ONE proposal only, and declared.  Offering two — one with modifiers
	 *    and one without — means «I take the card, but if it is missing memory
	 *    is fine»: it is a fallback, and a silent fallback produces two
	 *    behaviours under the same label (`CODER.md` §4.2).  Whoever wants the
	 *    fallback asks twice, and knows which of the two they got. */
	parameters[0] = proposal(&builder, width_px, height_px, frames_per_second, color,
	                        route == CAPTURE_ROUTE_CARD);

	if (pw_stream_connect(capture_v->flow, PW_DIRECTION_INPUT, node,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parameters, 1) < 0)
	{
		pw_thread_loop_unlock(capture_v->cycle);
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED, "attaching to node %u failed", node);
		goto fault;
	}

	/*
	 * ⛔⭐⭐⭐ AND HERE WERE THE TEN SECONDS — 16 August 2026, and it is the tail that
	 *        resisted five diagnoses.
	 *
	 * `[M]` The slow runs of the bench gave **12854** and **12866 ms**: twelve
	 * milliseconds of difference between two different runs.  ⇒ ⚠ A CONSTANT number
	 * is not a variation, it is a **ceiling** — and 12.86 s is exactly 2.86 s
	 * (`gnome-session` getting up) **plus ten round seconds**, that is this
	 * wait expiring.  The 24.8 s runs are the same ceiling **twice**.
	 *
	 * ⭐ And the comparison that decides: when the compositor is ready, this
	 *    attach costs `[M]` **sixteen milliseconds**.  ⇒ Waiting ten thousand
	 *    is not prudence, it is an attempt that refuses to fail.
	 *
	 * ⛔⛔ AND THEN THE MEASUREMENT SAID NO — 16 August 2026, and this is the part
	 *     that must be written instead of erased.
	 *
	 * I had shortened this ceiling to 1500 ms reasoning like this: «the caller
	 * retries every 200 ms, so a long attempt adds no chance,
	 * it only adds the time in which no others are made».  ⭐ The reasoning
	 * still holds.  ⛔ But the fact does not: with the short ceiling **the tail of the times
	 * did not change**, and this stopwatch line — which is written as soon as
	 * the attach exceeds 250 ms — **did not appear even once**.
	 *
	 * ⇒ ⚠ If the stopwatch is silent, the seconds are not here.  ⭐ So the ceiling
	 *   goes back to ten seconds: we do not ship a change whose motive the
	 *   measurement has refuted, however good the reasoning seems.
	 *   A change without evidence to back it is a debt, not a cure.
	 *
	 * ⭐ The STOPWATCH stays, and that is pure gain: now, if one day the
	 *    seconds are here, it will be seen instead of having to be deduced.
	 */
	expiry = g_get_monotonic_time() + (gint64)(WAIT_LATCH_MS * 1000);
	while (capture_v->state != PW_STREAM_STATE_PAUSED &&
	       capture_v->state != PW_STREAM_STATE_STREAMING &&
	       capture_v->state != PW_STREAM_STATE_ERROR && g_get_monotonic_time() < expiry)
		pw_thread_loop_timed_wait(capture_v->cycle, 1);
	pw_thread_loop_unlock(capture_v->cycle);
	{
		/* ⭐ And we DECLARE how much it cost, if it cost: it was the last
		 *    region of the mount without a stopwatch, and that is why
		 *    it took five diagnoses. */
		gint64 spent_ms = (g_get_monotonic_time() -
		                   (expiry - (gint64)(WAIT_LATCH_MS * 1000))) / 1000;

		if (spent_ms >= 250)
			log_says(AREA,
			              "⏱ attaching the PipeWire stream cost %lld ms "
			              "(state %d, ceiling %d ms) — ⚠ when the compositor is "
			              "ready it costs about ten milliseconds: this means "
			              "it was not ready",
			              (long long)spent_ms, (int)capture_v->state,
			              WAIT_LATCH_MS);
	}

	if (capture_v->state == PW_STREAM_STATE_ERROR)
	{
		/* ⭐ PHASE 17 — the code says WHAT went wrong, not only that
		 *    it went wrong: `G_IO_ERROR_NOT_SUPPORTED` when no format was
		 *    ever agreed (`capture_format_refused()`), so the
		 *    caller tells «the requested route does not exist here» from any
		 *    fault without reading PipeWire's text. */
		g_set_error(mistake, G_IO_ERROR,
		            capture_v->known_format ? G_IO_ERROR_FAILED : G_IO_ERROR_NOT_SUPPORTED,
		            "the compositor refused what was requested (%s, route %s): %s",
		            color == CAPTURE_COLOR_10BIT   ? "10 bit"
		            : color == CAPTURE_COLOR_BGRA ? "BGRA"
		                                            : "BGRx",
		            route == CAPTURE_ROUTE_CARD ? "card" : "memory",
		            capture_v->fault ? capture_v->fault : "without explanation");
		goto fault;
	}
	if (capture_v->state != PW_STREAM_STATE_PAUSED && capture_v->state != PW_STREAM_STATE_STREAMING)
	{
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "the capture did not attach within %d ms: ⚠ it does NOT mean "
		            "«broken», it means «the compositor is not ready yet» — and "
		            "the caller retries shortly",
		            WAIT_LATCH_MS);
		goto fault;
	}

	log_says(AREA, "capture started on node %u: requested %ux%u, route %s", node, width_px,
	              height_px, route == CAPTURE_ROUTE_CARD ? "card (DMA-BUF)" : "memory");
	return capture_v;

fault:
	capture_stop(capture_v);
	return NULL;
}

/* ------------------------------------------------------------------ *
 *  ⭐⭐ THE HOT SIZE CHANGE — see `cattura.h`
 * ------------------------------------------------------------------ */

CaptureRecanvas capture_resize(Capture *capture_v, uint32_t width_px, uint32_t height_px)
{
	/* ⛔ PHASE 13 — on wlroots the size is NOT changed on the stream: it is changed
	 *    on the output, with another protocol (`zwlr_output_manager_v1`, `[M]`
	 *    v4 on labwc).  ⇒ Here we say no **by saying so**, instead of returning
	 *    an outcome that would make the caller believe it obtained something. */
	if (capture_v && capture_v->wlr) {
		g_autoptr(GError) mistake = NULL;
		uint32_t l = 0, a = 0;
		WlrSizeOutcome e;

		/* ⭐ On this family the size is changed on the OUTPUT, not on the stream —
		 *    and it is the thing that could not be done on KDE.  ⛔ And the real outcome is
		 *    given by reading it back, not by the answer to the request. */
		e = wlr_ask_size(capture_v->wlr, width_px, height_px, 2.0, &mistake);
		capture_v->requested_width = width_px;
		capture_v->requested_height = height_px;
		wlr_measure(capture_v->wlr, &l, &a);
		if (l == width_px && a == height_px) {
			log_says(AREA,
			              "⭐ wlroots: the output is now %ux%u — read back, not "
			              "believed", l, a);
			return CAPTURE_RECANVAS_REQUESTED;
		}
		if (e == WLR_SIZE_UNCHANGED)
			return CAPTURE_RECANVAS_UNCHANGED;
		log_says(AREA,
		              "⛔ wlroots: requested %ux%u, the output is %ux%u%s%s",
		              width_px, height_px, l, a, mistake ? " — " : "",
		              mistake ? mistake->message : "");
		return CAPTURE_RECANVAS_FAULT;
	}
	uint8_t space[2048];
	struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(space, sizeof space);
	const struct spa_pod *parameters[5];
	uint32_t how_many;
	int outcome;

	if (!capture_v || !capture_v->flow || !capture_v->cycle)
		return CAPTURE_RECANVAS_FAULT;
	/* ⛔ Zero is not «out of bounds»: it is a request with no content, and
	 *    passing it to the producer would mean asking it for a monitor of zero
	 *    area.  ⚠ The rest of the rule — 200..8192 and evenness — lives in
	 *    `rcp_size_allowed()`, in a single place. */
	if (!width_px || !height_px)
	{
		log_says(AREA, "⛔ resize to %ux%u: an empty size is not requested",
		              width_px, height_px);
		return CAPTURE_RECANVAS_FAULT;
	}

	pw_thread_loop_lock(capture_v->cycle);

	/* ⛔⭐ THE MANDATORY GUARD — `STUDI.md` §kde §8.2-bis: «without it, the renegotiation
	 *     bites its own tail», and the defect does NOT show on Trixie.
	 *
	 * ⛔⛔ AND WE COMPARE WITH THE SIZE THE STREAM **HAS**, NOT WITH THE ONE IT
	 *     WAS ASKED FOR — defect found while refuting, on the night of 15
	 *     August 2026, and the first draft got exactly this wrong.
	 *
	 *     `STUDI.md` §kde §8.2-bis writes the guard as `misura_attuale ==
	 *     misura_richiesta`, and **current** is not **requested**: §4.5 declares
	 *     it normal for the compositor to grant a size different from the one
	 *     requested.  ⇒ Comparing with the requested one, this sequence turned the
	 *     function off forever:
	 *
	 *       1920x1080 is requested, the compositor does not obey (or grants something else)
	 *       ⇒ `chiesta_*` = 1920x1080, the stream stayed where it was
	 *       ⇒ the user retries the SAME size
	 *       ⇒ «already requested»: no request leaves, EVER AGAIN.
	 *
	 *     And the log would have blamed the right guard for the wrong defect.
	 *
	 * ⚠ As long as the format is not known there is no «current»: then we look at the
	 *   requested one, which is the only thing there is — and it is declared here instead of
	 *   leaving it to be deduced. */
	if (capture_v->known_format ? (width_px == capture_v->schema.size.width
	                             && height_px == capture_v->schema.size.height)
	                          : (width_px == capture_v->requested_width
	                             && height_px == capture_v->requested_height))
	{
		pw_thread_loop_unlock(capture_v->cycle);
		log_detail(AREA,
		                   "resize to %ux%u: it is the size the stream ALREADY "
		                   "HAS, NOT renegotiating (STUDI.md §kde §8.2-bis)",
		                   width_px, height_px);
		return CAPTURE_RECANVAS_UNCHANGED;
	}

	/* ⛔ A dead stream is not renegotiated, and «dead» is ASKED of the state instead
	 *    of deduced from silence: on a stream in error `update_params`
	 *    would succeed and a frame would never arrive — that is the silent
	 *    fallback that `CODER.md` §4.2 forbids. */
	if (capture_v->state != PW_STREAM_STATE_PAUSED && capture_v->state != PW_STREAM_STATE_STREAMING)
	{
		enum pw_stream_state state = capture_v->state;
		/* ⛔ THE FAULT IS COPIED BEFORE RELEASING THE LOCK — defect found
		 *    while refuting: `on_state()` runs on the loop thread and does
		 *    `g_free(fault); fault = g_strdup(...)`, so between the `g_free` and
		 *    the assignment the field is a dangling pointer.  ⚠ And this branch
		 *    is taken **precisely while** the stream is dying, that is
		 *    at the instant `on_state` is running: reading it after the unlock is
		 *    reading freed memory, and for a log line. */
		char *fault = capture_v->fault ? g_strdup(capture_v->fault) : NULL;
		pw_thread_loop_unlock(capture_v->cycle);
		log_says(AREA,
		              "⛔ resize to %ux%u NOT requested: the stream is «%s»%s%s",
		              width_px, height_px, pw_stream_state_as_string(state),
		              fault ? " — " : "", fault ? fault : "");
		g_free(fault);
		return CAPTURE_RECANVAS_FAULT;
	}

	/* ⛔ The REQUESTED size is updated BEFORE the request, and under the loop
	 *    lock: `on_parameters` runs on the PipeWire thread and compares it
	 *    against the negotiated format (the «requested versus granted» guard).
	 *    Updating it afterwards would mean comparing the new answer with the
	 *    old question, that is declaring a divergence that does not exist. */
	capture_v->requested_width = width_px;
	capture_v->requested_height = height_px;
	/* ⚠ And the divergence is reset: it is a fact of the negotiation that is about to be
	 *   redone, not a scar of the previous one. */
	capture_v->measure_divergent = FALSE;

	/* ⛔ The same `proposal()` as at startup, with the same colour and route: a
	 *    proposal written by hand here would be a second rule on the format, and the
	 *    day one of the two changed the stream would reopen with a
	 *    colour different from the negotiated one — without any error. */
	parameters[0] = proposal(&builder, width_px, height_px, capture_v->requested_per_second,
	                        capture_v->color, capture_v->route == CAPTURE_ROUTE_CARD);
	/* ⛔⭐ AND WITH IT THE FOUR CONSUMPTION PARAMETERS — defect found while refuting:
	 *     `pw_stream_update_params()` does NOT add, **it replaces the whole
	 *     list**.  Passing only `EnumFormat` would erase
	 *     `ParamBuffers` and the three `ParamMeta`, among them the CURSOR one.  ⚠ In the
	 *     healthy case the format callback puts them back; ⛔ but in the case that
	 *     `cattura.h` documents — the compositor answering «succeeded» and
	 *     sending no event — that callback does not run, and the pointer
	 *     channel would stay without a source without anybody saying so. */
	how_many = 1 + consumer_parameters(capture_v, &builder, parameters + 1);
	outcome = pw_stream_update_params(capture_v->flow, parameters, how_many);
	pw_thread_loop_unlock(capture_v->cycle);

	if (outcome < 0)
	{
		log_says(AREA, "⛔ `pw_stream_update_params()` at %ux%u answered %d (%s)",
		              width_px, height_px, outcome, spa_strerror(outcome));
		return CAPTURE_RECANVAS_FAULT;
	}
	log_says(AREA,
	              "⭐ canvas REQUESTED from the producer: %ux%u (`pw_stream_update_params`).  ⚠ It is the "
	              "request, not the outcome: the truth is told by the frame (DECISIONI.md "
	              "§5.0-sexies)",
	              width_px, height_px);
	return CAPTURE_RECANVAS_REQUESTED;
}

gboolean capture_wake(Capture *capture_v)
{
	/* ⭐ On the pull direction waking up means asking for the next WHOLE frame.
	 *    ⛔ Until 21 Sep 2026 nothing was done here, because every round was
	 *    already a whole copy; since frames are requested WITH DAMAGE
	 *    (`wlroots.c`, `force_full`), on an idle desktop none would
	 *    arrive — exactly when a keyframe is needed. */
	if (capture_v && capture_v->wlr) {
		wlr_force_full(capture_v->wlr);
		return TRUE;
	}
	uint8_t space[2048];
	struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(space, sizeof space);
	const struct spa_pod *parameters[5];
	uint32_t l, a, how_many;
	int outcome;

	if (!capture_v || !capture_v->flow || !capture_v->cycle)
		return FALSE;

	pw_thread_loop_lock(capture_v->cycle);
	if (capture_v->state != PW_STREAM_STATE_PAUSED && capture_v->state != PW_STREAM_STATE_STREAMING)
	{
		pw_thread_loop_unlock(capture_v->cycle);
		return FALSE;
	}
	/* ⛔ The size is the NEGOTIATED one, not the requested one: nothing is being
	 *    changed here — the same question is being repeated to restart
	 *    the stream.  ⚠ Redoing the proposal with the REQUESTED size, at a time when
	 *    the compositor has granted another one (§4.5), would be a
	 *    resize disguised as a wake-up. */
	l = capture_v->known_format ? capture_v->schema.size.width : capture_v->requested_width;
	a = capture_v->known_format ? capture_v->schema.size.height : capture_v->requested_height;
	if (!l || !a)
	{
		pw_thread_loop_unlock(capture_v->cycle);
		return FALSE;
	}
	parameters[0] = proposal(&builder, l, a, capture_v->requested_per_second, capture_v->color,
	                        capture_v->route == CAPTURE_ROUTE_CARD);
	how_many = 1 + consumer_parameters(capture_v, &builder, parameters + 1);
	outcome = pw_stream_update_params(capture_v->flow, parameters, how_many);
	pw_thread_loop_unlock(capture_v->cycle);

	if (outcome < 0)
	{
		log_says(AREA, "⛔ stream wake-up at %ux%u: %s", l, a, spa_strerror(outcome));
		return FALSE;
	}
	log_says(AREA,
	              "⭐ stream RESTARTED at the same size (%ux%u) to get a "
	              "frame delivered: on Wayland one cannot ask «repaint», and this is the "
	              "only lever we have (`cattura.h`)",
	              l, a);
	return TRUE;
}

void capture_measure_requested(Capture *capture_v, uint32_t *width_px, uint32_t *height_px)
{
	if (width_px)
		*width_px = capture_v ? capture_v->requested_width : 0;
	if (height_px)
		*height_px = capture_v ? capture_v->requested_height : 0;
}

gboolean capture_measure_negotiated(Capture *capture_v, uint32_t *width_px, uint32_t *height_px)
{
	/* On wlroots the «negotiated» size is the output's, and it is known at once. */
	if (capture_v && capture_v->wlr) {
		uint32_t l = 0, a = 0;

		wlr_measure(capture_v->wlr, &l, &a);
		if (!l || !a)
			return FALSE;
		if (width_px)
			*width_px = l;
		if (height_px)
			*height_px = a;
		return TRUE;
	}
	if (!capture_v || !capture_v->known_format)
		return FALSE; /* ⛔ «it has not been negotiated», not «it is 0x0» */
	if (width_px)
		*width_px = capture_v->schema.size.width;
	if (height_px)
		*height_px = capture_v->schema.size.height;
	return TRUE;
}

/* ------------------------------------------------------------------ *
 *  Taking a frame
 * ------------------------------------------------------------------ */

/*
 * ⛔ THE RANGE MEASUREMENT IS DONE HERE, NOT INSIDE THE CALLBACK.
 *
 * Mutter does not declare the range (`[M]` 12 August 2026: `color_range` is 0, that is
 * UNKNOWN), and whoever took it as full would be deducing.  ⇒ It is **measured** on the
 * pixels it delivered, and we write that it is our own measurement.
 *
 * ⚠ And the measurement depends on the SCENE: a desktop that has neither full black nor
 *   full white does not reach the extremes, and that does NOT prove a limited range.
 *   That is why the outcome has two values and not three.
 *
 * ⭐ And the same pass answers the worst question of this phase: is the
 *    frame BLACK?  A black and valid frame — right size, right stride,
 *    right damage, and nothing inside — is what a session
 *    without a virtual monitor delivers, and every other tool of the project would
 *    promote it.  ⛔ Here it is not refused: it is DECLARED.  A desktop can
 *    legitimately be black, and refusing it would be deciding on behalf
 *    of the user; staying silent would be delivering nothing without a line.
 */
static void measure_pixels(CaptureStopped *stopped)
{
	CaptureDelivery *c = &stopped->delivery;
	int r = 0, g = 1, b = 2;
	guint64 row, column;
	const uint8_t *base = stopped->pixel;
	uint8_t first[4] = { 0, 0, 0, 0 };
	gboolean uniform = TRUE;

	c->measured_range = CAPTURE_RANGE_UNMEASURED;
	if (!stopped->pixel || stopped->byte == 0)
		return;
	if (c->bit_per_channel != 8 || !rgb_positions(c->raw_format, &r, &g, &b))
	{
		/* ⛔ We do not measure on the wrong bytes: a number taken from a layout
		 *    we do not know would be worse than no number. */
		return;
	}

	c->minimum[0] = c->minimum[1] = c->minimum[2] = 255;
	c->maximum[0] = c->maximum[1] = c->maximum[2] = 0;
	memcpy(first, base, 4);

	for (row = 0; row < stopped->height_px; row++)
	{
		const uint8_t *p = base + row * (guint64) stopped->stride;

		if ((row + 1) * (guint64) stopped->stride > stopped->byte)
			break;
		for (column = 0; column < stopped->width_px; column++, p += 4)
		{
			uint8_t v[3] = { p[r], p[g], p[b] };
			int i;

			for (i = 0; i < 3; i++)
			{
				if (v[i] < c->minimum[i])
					c->minimum[i] = v[i];
				if (v[i] > c->maximum[i])
					c->maximum[i] = v[i];
			}
			if (uniform && (p[0] != first[0] || p[1] != first[1] || p[2] != first[2]))
				uniform = FALSE;
		}
	}

	c->uniform = uniform;
	c->nero = (c->maximum[0] == 0 && c->maximum[1] == 0 && c->maximum[2] == 0);
	if (c->minimum[0] == 0 && c->minimum[1] == 0 && c->minimum[2] == 0 && c->maximum[0] == 255 &&
	    c->maximum[1] == 255 && c->maximum[2] == 255)
		c->measured_range = CAPTURE_RANGE_COMPATIBLE_FULL;
	else
		c->measured_range = CAPTURE_RANGE_INCONCLUSIVE;
}

/*
 * ⭐⭐ THE JUDGEMENT ON THE SLAB IS MADE BY SAMPLING, NOT ON ALL THE BYTES.
 *
 * ⛔ THE FACT THAT MADE IT NECESSARY — `[M]` phase 16, Radeon RX 6800,
 *    XFCE/labwc box (wlroots-dmabuf route, LINEAR gbm slabs): the full
 *    pass of `measure_pixels` over the mapping of the 4K slab took
 *    **63 673 ms** (GPU wait 0.59 ms), and for all that time the loop
 *    delivered nothing and the birth of the session failed.  On a
 *    DISCRETE card the slab lives in VRAM and the CPU reads it through the
 *    UNCACHED PCIe BAR: every read is a bus transaction, and the full
 *    pass makes several per pixel over eight million pixels.  ⚠ On the integrated
 *    Intel (system memory) the same pass is instantaneous: that is why
 *    it had not been seen until the Radeon.
 *
 * ⭐ THE «BLACK / NOT BLACK» JUDGEMENT DOES NOT NEED 30 MB: a grid of
 *    `SAMPLE_SIDE` x `SAMPLE_SIDE` points, at the CENTRE of each cell (on 4K
 *    a cell is 60x34 pixels), each read with ONE 4-byte read
 *    (`memcpy` into a local variable: a single bus transaction, not
 *    three to six as in the full pass), touching only the pages needed.
 *
 * ⚠ AND THE POSSIBLE ERROR LIES ON ONE SIDE ONLY, and it is the harmless side:
 *    - «not black» is CERTAIN: one lit sample is enough to prove it;
 *    - «black» / «uniform» can be FALSE only if everything that is
 *      lit falls BETWEEN the grid points (a black scene with something
 *      smaller than a cell in every direction inside);
 *    - the range: «compatible full» is CERTAIN if the samples see it,
 *      otherwise «not conclusive» comes out, which is already the «I do not know» value.
 *    ⇒ On a normal scene (background, panel) the outcome is that of the full
 *      pass; the milliseconds change.
 *
 * ⛔ THE TIME CEILING (`SAMPLE_CAP_US`), checked at every row of the
 *    grid: if it expires, what was seen counts only if it proves «not black»
 *    (one lit sample and two different ones).  A «black» or a «uniform» on a
 *    half grid is NOT declared: `measured_pixels` stays FALSE, «I did not
 *    look» (`LEZIONI.md` §1.9), and the caller's line says so.
 *
 * ⚠ The modifier: this function reads the slab as if it were LINEAR,
 *   like the full pass before it — on the wlroots route the slabs are
 *   LINEAR by construction (`wlroots.c`, `lastra_nuova`).  On a
 *   tiled slab the points read are REAL pixels in different places, and the
 *   black/uniform judgement holds all the same; on a COMPRESSED slab
 *   (DCC/CCS) the bytes are not pixels, exactly as for the full pass:
 *   it gets no worse, and no better.
 */
#define SAMPLE_SIDE 64u
#define SAMPLE_CAP_US 250000u

static guint measure_pixels_sampled(CaptureStopped *stopped, gboolean *ceiling)
{
	CaptureDelivery *c = &stopped->delivery;
	int r = 0, g = 1, b = 2;
	const uint8_t *base = stopped->pixel;
	uint8_t first[4] = { 0, 0, 0, 0 };
	gboolean uniform = TRUE;
	guint watched = 0, i, j;
	uint64_t start = current_us();

	*ceiling = FALSE;
	c->measured_range = CAPTURE_RANGE_UNMEASURED;
	if (!stopped->pixel || stopped->byte == 0 || stopped->width_px == 0 || stopped->height_px == 0)
		return 0;
	/* ⛔ Like the full pass: on the bytes of a layout we do not
	 *    know we do not measure. */
	if (c->bit_per_channel != 8 || !rgb_positions(c->raw_format, &r, &g, &b))
		return 0;

	c->minimum[0] = c->minimum[1] = c->minimum[2] = 255;
	c->maximum[0] = c->maximum[1] = c->maximum[2] = 0;

	for (i = 0; i < SAMPLE_SIDE; i++)
	{
		guint64 row = ((2u * (guint64) i + 1u) * stopped->height_px) / (2u * SAMPLE_SIDE);
		const uint8_t *p_line = base + row * (guint64) stopped->stride;

		if ((row + 1) * (guint64) stopped->stride > stopped->byte)
			break;
		if (i > 0 && current_us() - start > SAMPLE_CAP_US)
		{
			*ceiling = TRUE;
			break;
		}
		for (j = 0; j < SAMPLE_SIDE; j++)
		{
			guint64 column =
			    ((2u * (guint64) j + 1u) * stopped->width_px) / (2u * SAMPLE_SIDE);
			uint8_t px[4];
			uint8_t v[3];
			int k;

			/* ⭐ ONE 4-byte read, then we work on the local copy. */
			memcpy(px, p_line + column * 4u, 4);
			if (watched == 0)
				memcpy(first, px, 4);
			v[0] = px[r];
			v[1] = px[g];
			v[2] = px[b];
			for (k = 0; k < 3; k++)
			{
				if (v[k] < c->minimum[k])
					c->minimum[k] = v[k];
				if (v[k] > c->maximum[k])
					c->maximum[k] = v[k];
			}
			if (uniform && (px[0] != first[0] || px[1] != first[1] || px[2] != first[2]))
				uniform = FALSE;
			watched++;
		}
	}
	if (watched == 0)
		return 0;

	c->uniform = uniform;
	c->nero = (c->maximum[0] == 0 && c->maximum[1] == 0 && c->maximum[2] == 0);
	if (c->minimum[0] == 0 && c->minimum[1] == 0 && c->minimum[2] == 0 && c->maximum[0] == 255 &&
	    c->maximum[1] == 255 && c->maximum[2] == 255)
		c->measured_range = CAPTURE_RANGE_COMPATIBLE_FULL;
	else
		c->measured_range = CAPTURE_RANGE_INCONCLUSIVE;
	return watched;
}

/*
 * ⭐⭐ THE CARD FRAME LOOKED AT **ONLY ONCE**, and the reason it is
 *     only once is a cost, not laziness.
 *
 * ⛔ THE FACT THAT MAKES IT NECESSARY: the line «⛔ the delivered frame is
 *    BLACK» is the witness of `STUDI.md` §gnome §3.1 fault M9 — *a session
 *    without a virtual monitor delivers valid, black frames*.  On the memory
 *    route it is read from the copied pixels; on the card the copied pixels do not
 *    exist.  ⇒ Either the DMA-BUF is mapped, or that diagnosis **disappears without
 *    any line saying so**, which is the worst form of all.
 *
 * ⚠ AND WHY NOT AT A RATE, as in memory: the mapping of a DMA-BUF is not
 *   system memory — it is read through the card's bus, and reading
 *   eight megabytes from it **does not cost as much as a `memcpy`**.  ⛔ How much it costs is not
 *   deduced: the line that accompanies this call **prints it**, and whoever reads
 *   the log sees the real number of this machine.  ⇒ It is paid once,
 *   on the first frame, which is exactly the one whose stage line `figlio.c`
 *   writes.
 *
 * ⛔ AND ON THE FOLLOWING FRAMES `measured_pixels` STAYS FALSE, which means
 *    «I did not look» and **not** «it is not black» — the same rule as the field, and
 *    the same reason (`LEZIONI.md` §1.9).  ⚠ What is lost compared with
 *    memory is continuous surveillance: a desktop that turned black
 *    mid-session, on this route, no longer has anyone to say so.  It is declared
 *    here instead of discovered later.
 *
 * ⛔⛔ AND IT IS NOT READ IN FULL: it is read by sampling (`measure_pixels_sampled`,
 *     the box above), because on a discrete card the full pass
 *     took 63.7 s.  It returns how many pixels it looked at; `*ceiling` says whether the
 *     time expired before the end of the grid.
 */
static guint look_dmabuf_pixels(Capture *capture_v, CaptureStopped *stopped, gboolean *ceiling)
{
	void *map;
	size_t how_many;
	guint watched;

	*ceiling = FALSE;
	if (stopped->fd < 0 || stopped->byte == 0)
		return 0;
	how_many = (size_t) stopped->offset + (size_t) stopped->byte;
	map = mmap(NULL, how_many, PROT_READ, MAP_SHARED, stopped->fd, 0);
	if (map == MAP_FAILED)
	{
		/* ⛔ It is NOT «the frame is not black»: it is «I could not look», and
		 *    it is said once instead of leaving a silence that looks like a
		 *    green.  ⚠ It happens for example with a non-linear modifier: there
		 *    the bytes in memory are not the rows of the image, and reading them
		 *    would give a wrong answer instead of no answer. */
		if (!capture_v->logged_measure_impossible)
		{
			capture_v->logged_measure_impossible = TRUE;
			log_says(AREA,
			              "⚠ the DMA-BUF could not be mapped (fd %d, %zu bytes, "
			              "modifier 0x%" G_GINT64_MODIFIER "x): ⛔ we do NOT conclude that "
			              "the frame is not black — we conclude that I DID NOT "
			              "LOOK, and `measured_pixels` stays FALSE",
			              stopped->fd, how_many, (guint64) stopped->modifier);
		}
		return 0;
	}
	/* ⚠ `measure_pixels` reads from `stopped->pixel`: it is lent for the duration
	 *   of the measurement and taken away right after.  ⛔ Leaving it there would
	 *   mean handing downstream a pointer to a mapping we are about to
	 *   tear down — and downstream nobody expects it, because `on_card` says
	 *   the opposite. */
	stopped->pixel = (uint8_t *) map + stopped->offset;
	watched = measure_pixels_sampled(stopped, ceiling);
	/* ⛔ Zero looked at = «I did not look» (unknown format, slab
	 *    shorter than the first row).  And with the ceiling expired a «black» or a
	 *    «uniform» on half a grid is not declared: only «not black» counts,
	 *    which one lit sample proves by itself. */
	stopped->delivery.measured_pixels =
	    watched > 0 && !(*ceiling && (stopped->delivery.nero || stopped->delivery.uniform));
	if (!stopped->delivery.measured_pixels) {
		stopped->delivery.nero = FALSE;
		stopped->delivery.uniform = FALSE;
		stopped->delivery.measured_range = CAPTURE_RANGE_UNMEASURED;
	}
	stopped->pixel = NULL;
	munmap(map, how_many);
	return watched;
}

/*
 * ⭐⭐ THE TRUE SHAPE ON LABWC — the probe (`wlroots.h`) has seen under the
 *      pointer the colour of a shape: here it becomes the TRUE image of the
 *      real theme (`shape_image`) and leaves along the SAME road as GNOME and
 *      KDE — `cursor_bounce`, and from there whoever registered with
 *      `capture_cursor` (the child: `cursor_to_parent`).
 *
 * ⛔ It runs on the thread of whoever calls `capture_take` (the child's loop), not
 *    on PipeWire's: there is no PipeWire here.  ⇒ The receiver can do
 *    what it always does, send on the socket, and nothing more.
 * ⚠ Hidden does not exist here: the probe either recognises a colour or keeps the
 *   previous shape.  ⇒ An application that hides the pointer does not
 *   hide it from whoever watches — as on KDE (`cursor_never_hide`).
 */
static void wlr_shape_delivery(Capture *capture_v)
{
	int idx = wlr_probe_shape(capture_v->wlr);
	CursorShape f;

	if (idx < 0)
		return;
	memset(&f, 0, sizeof f);
	if (!shape_image(idx, &f))
		return; /* ⛔ real theme missing: already said by `forma.c`, the client
		         *    keeps its arrow */
	if (capture_v->wlr_shape_data && f.width_px == capture_v->wlr_shape.width_px &&
	    f.height_px == capture_v->wlr_shape.height_px &&
	    f.active_x == capture_v->wlr_shape.active_x &&
	    f.active_y == capture_v->wlr_shape.active_y &&
	    memcmp(f.bitmap, capture_v->wlr_shape.bitmap,
	           (gsize)f.width_px * f.height_px * 4u) == 0) {
		capture_v->wlr_shapes_equal++;
		return;
	}
	f.series = capture_v->wlr_shape.series + 1;
	/* ⚠ One line per shape CHANGE, as on KDE (`cursore.c`): it is the pace
	 *   of the hand, and the proof that the probe is working is read here. */
	log_says(AREA, "encoded shape %d «%s» ⇒ %ux%u, hotspot %d,%d (wlroots probe)",
	              idx, shape_name(idx), (unsigned)f.width_px, (unsigned)f.height_px,
	              (int)f.active_x, (int)f.active_y);
	capture_v->wlr_shape = f;
	capture_v->wlr_shape_data = TRUE;
	capture_v->wlr_shapes_sent++;
	cursor_bounce(capture_v, &f);
}

void capture_probe_pointer(Capture *capture_v, uint32_t x, uint32_t y)
{
	uint32_t l = 0, a = 0;

	if (!capture_v || !capture_v->wlr)
		return;
	/* ⚠ The pointer's canvas is the frame's (`input_recanvas` resets
	 *   it at every size change, `figlio.c`), and on this family the
	 *   frame is the whole output: ⇒ the output size is the yardstick.
	 *   For the frame straddling a size change the point may be
	 *   scaled wrong ONCE: the next probe puts it right. */
	wlr_measure(capture_v->wlr, &l, &a);
	wlr_probe_pointer(capture_v->wlr, x, y, l, a);
}

CaptureTake capture_take(Capture *capture_v, double wait_s, CaptureStopped *outside,
                            GError **mistake)
{
	gint64 expiry;
	gboolean taken = FALSE;

	g_return_val_if_fail(capture_v != NULL && outside != NULL, CAPTURE_TAKE_FAULT);
	memset(outside, 0, sizeof *outside);

	/*
	 * ⭐⭐ PHASE 13 — THE PULL DIRECTION: here we do not WAIT for a frame, we
	 *      ASK for it.  ⚠ Two routes: on MEMORY the copy exists, and the
	 *      microseconds are in `copy_us` as on every other route — a
	 *      segment without its cost is a segment that will lie; on the CARD
	 *      (since 21 Sep 2026) the pixels stay in a slab and the frame
	 *      comes out as `PIXEL_ALTROVE`, further below.
	 */
	if (capture_v->wlr) {
		WlrFrame w;
		gint64 before = g_get_monotonic_time(), after;
		WlrOutcome e = wlr_frame(capture_v->wlr, wait_s, &w, mistake);

		/* ⭐ The pointer probe: its events have just been pumped by
		 *    `wlr_frame`.  ⛔ BEFORE the `switch`, which has three exits:
		 *    on an idle desktop the frame almost always times out, and the shape
		 *    must arrive all the same. */
		wlr_shape_delivery(capture_v);

		switch (e) {
		case WLR_FRAME_EXPIRED:
			/* ⛔ «nothing arrived» on a pull source is a legitimate
			 *    ZERO, not a fault: the desktop may be idle, and the
			 *    compositor answers all the same.  ⚠ But the error stays written. */
			return CAPTURE_TAKE_ZERO;
		case WLR_FRAME_FAILED:
		case WLR_FRAME_BROKEN:
			return CAPTURE_TAKE_FAULT;
		case WLR_FRAME_TAKEN:
			break;
		}

		outside->arrival_us = (uint64_t)before;
		outside->width_px = w.width_px;
		outside->height_px = w.height_px;
		outside->stride = w.stride;
		outside->byte = w.byte;
		outside->pts = (int64_t)(w.seconds * 1000000000ull + w.nanoseconds);
		outside->seq_valid = FALSE;
		outside->format_drm = w.schema;
		if (w.on_card) {
			/*
			 * ⭐⭐ THE CARD: no copy of ours, and the slab stays HELD.
			 *
			 * ⛔ `held_buffer` + `owner` are the same two fields as the
			 *    PipeWire retention: `capture_stopped_free()` sees them, and its
			 *    `wlr` preamble gives the slab back to `wlroots.c` — AFTER
			 *    `encoder_compress_card()`, when the GPU has finished
			 *    reading.  ⇒ The compositor does not write into it before then
			 *    (`LEZIONI.md` §8).
			 * ⚠ `copy_us` here is the WHOLE round — request, blit on the
			 *   compositor's GPU, wait for the fence — as on memory it is the
			 *   whole round plus the `memcpy`: the same quantity on both routes.
			 */
			outside->on_card = TRUE;
			outside->pixel = NULL;
			outside->fd = w.fd;
			outside->offset = w.offset;
			outside->modifier = w.modifier;
			outside->generation = w.generation;
			outside->held_buffer = w.slab;
			outside->owner = capture_v;
		} else {
			/* ⛔ Card requested and memory arrived: it is SAID, once. */
			if (capture_v->route == CAPTURE_ROUTE_CARD && !capture_v->wlr_fallback_logged) {
				capture_v->wlr_fallback_logged = TRUE;
				log_says(AREA,
				              "⛔ wlroots: CARD requested, and this frame "
				              "arrived in MEMORY — DECLARED FALLBACK (the reason is "
				              "in the `wlroots:` lines above).  The line is not "
				              "repeated; the closing counters say how many per "
				              "route");
			}
			outside->on_card = FALSE;
			outside->pixel = g_malloc(w.byte);
			memcpy(outside->pixel, w.pixel, w.byte);
		}
		after = g_get_monotonic_time();
		outside->copy_us = (uint64_t)(after - before);

		capture_v->wlr_last = w;
		capture_v->wlr_last_known = TRUE;
		capture_v->known_format = TRUE;

		/*
		 * ⛔⛔ THE WITNESS IS WRITTEN HERE, AT THE FIRST REAL FRAME — and not
		 *     at opening, where it was until 21 September 2026.
		 *
		 * «`negotiated format: WxH`» is the line C1 reads to say that the
		 * monitor was born.  The first draft wrote it in `capture_start_wlr`,
		 * BEFORE any `capture_output`, with format, bits and modifier
		 * hard-coded in the text.  ⇒ The adversarial reviewer called it by
		 * name: *an XFCE session in which screencopy always fails came out
		 * GREEN* — the line proved only that labwc was alive.
		 * ⭐ Here instead there is a frame in hand: size, stride and format
		 *   are those of the `buffer` event, and C1's green again means
		 *   what it says.
		 */
		if (!capture_v->wlr_witness_logged) {
			char label_name[5];

			capture_v->wlr_witness_logged = TRUE;
			memcpy(label_name, &w.schema, 4);
			label_name[4] = 0;
			log_says(AREA,
			              "negotiated format: %ux%u %s (8 bits per channel), modifier "
			              "0x%" G_GINT64_MODIFIER "x — ⭐ wlroots: said at the FIRST "
			              "frame taken, with the size and format the "
			              "compositor really gave, %s",
			              w.width_px, w.height_px, label_name,
			              (guint64)(w.on_card ? w.modifier : 0),
			              w.on_card ? "on the CARD (wlroots-dmabuf)"
			                             : "in MEMORY (wlroots-shm)");
		}

		/* ⚠ `y_inverted`: if the compositor says the rows must be read from the
		 *   bottom and nobody honours it, the image comes out upside down — a fault that
		 *   looks like an encoder fault.  ⛔ Here it is DECLARED and not
		 *   flipped: flipping 8 MB at every frame would cost more than the capture, and
		 *   the right place is the encoder, which can do it without copying.
		 *   `[M]` 21 Sep 2026 on headless labwc the flag never turned on. */
		/* ⚠ ONCE only: inside the branch of every take it would be sixty
		 *   lines per second, the form that already produced the 30.8 GB of
		 *   log (the reviewer, 21 Sep 2026). */
		if (w.y_inverted && !capture_v->wlr_y_logged && (capture_v->wlr_y_logged = TRUE))
			log_says(AREA,
			              "⛔ wlroots: the compositor declares Y INVERTED and this "
			              "draft does not flip it — the image will come out upside down, and the "
			              "cause is this line, not the encoder");

		capture_delivery(capture_v, &outside->delivery);
		if (!w.on_card)
			return CAPTURE_TAKE_DONE;

		/* ⭐ The FIRST card frame is looked at, by mapping the slab —
		 *    the same rule as the card on PipeWire: only once, and the
		 *    others carry `measured_pixels` FALSE («I did not look»).  ⚠ With the
		 *    DMA-BUF SYNC around it: the bytes the CPU sees must be
		 *    those written by the GPU. */
		/* ⛔⛔ AND THE NUMBERING, found re-reading the port: `measure_pixels`
		 *     reads the channel order from `raw_format` with SPA
		 *     numbers, and here `raw_format` is a DRM fourcc.  Passed as is, the
		 *     measurement exits AT ONCE without looking at anything — and
		 *     `look_dmabuf_pixels` writes `measured_pixels =
		 *     TRUE` all the same: a «not black» on a frame never looked at, that is the
		 *     false green of `LEZIONI.md` §1.9.  ⇒ For the duration of the measurement
		 *     we lend the SPA number that states the same order; if there
		 *     is none, we do NOT look, and we say so. */
		if (!capture_v->wlr_watched_first) {
			uint64_t tm = current_us();
			guint watched = 0;
			gboolean ceiling = FALSE;
			uint32_t raw = outside->delivery.raw_format;
			uint32_t spa = (w.schema == DRM_FORMAT_XRGB8888) ? SPA_VIDEO_FORMAT_BGRx
			               : (w.schema == DRM_FORMAT_ARGB8888) ? SPA_VIDEO_FORMAT_BGRA
			               : (w.schema == DRM_FORMAT_XBGR8888) ? SPA_VIDEO_FORMAT_RGBx
			               : (w.schema == DRM_FORMAT_ABGR8888) ? SPA_VIDEO_FORMAT_RGBA
			                                                   : SPA_VIDEO_FORMAT_UNKNOWN;

			capture_v->wlr_watched_first = TRUE;
			if (spa != SPA_VIDEO_FORMAT_UNKNOWN) {
				outside->delivery.raw_format = spa;
				wlr_cpu_read(outside->fd, TRUE);
				watched = look_dmabuf_pixels(capture_v, outside, &ceiling);
				wlr_cpu_read(outside->fd, FALSE);
				outside->delivery.raw_format = raw;
			} else {
				log_says(AREA,
				              "⚠ wlroots: the first CARD frame was NOT "
				              "looked at — fourcc 0x%08x has no channel "
				              "order the measurement knows.  `measured_pixels` "
				              "stays FALSE: «I did not look», not «it is not black»",
				              w.schema);
			}
			outside->measure_us = current_us() - tm;
			if (outside->delivery.measured_pixels)
				log_says(AREA,
				              "⭐ wlroots: the FIRST CARD frame looked at "
				              "by mapping the slab: %s — %u sampled pixels over "
				              "%ux%u%s (%.2f ms, GPU wait %.2f ms, %s)",
				              outside->delivery.nero       ? "⛔ BLACK"
				              : outside->delivery.uniform ? "⚠ UNIFORM"
				                                         : "not black",
				              watched, outside->width_px, outside->height_px,
				              ceiling ? ", ⚠ time CEILING expired with the grid incomplete" : "",
				              outside->measure_us / 1000.0, w.gpu_wait_us / 1000.0,
				              w.explicit_wait
				                  ? "fence extracted from the DMA-BUF"
				                  : "⚠ no fence: implicit synchronisation");
			else if (ceiling)
				log_says(AREA,
				              "⚠ wlroots: the FIRST CARD frame was NOT "
				              "judged — CEILING of %u ms expired after %u "
				              "sampled pixels all dark or equal (%.2f ms): «I did not look», "
				              "not «it is not black», and `measured_pixels` stays FALSE",
				              SAMPLE_CAP_US / 1000u, watched,
				              outside->measure_us / 1000.0);
		}
		return CAPTURE_TAKE_PIXEL_ELSEWHERE;
	}

	if (capture_v->state != PW_STREAM_STATE_STREAMING && capture_v->state != PW_STREAM_STATE_PAUSED)
	{
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "the stream is not active (state %s%s%s): there is no frame to "
		            "wait for, and this is NOT a zero",
		            pw_stream_state_as_string(capture_v->state), capture_v->fault ? ", fault: " : "",
		            capture_v->fault ? capture_v->fault : "");
		return CAPTURE_TAKE_FAULT;
	}

	g_mutex_lock(&capture_v->lock);
	capture_v->someone_waiting = TRUE;
	/* ⛔⛔ AND HERE THERE WAS `capture_v->slot_full = FALSE;` — the second half of the
	 *     same defect of 15 August 2026: whoever came to take a
	 *     frame **threw away the one already ready** and started
	 *     waiting for another.  ⇒ With the scene still that other one never
	 *     arrived, and the last frame of the change stayed in the slot,
	 *     undelivered, until the next movement.
	 * ⭐ Now: if it is there, it is taken. */
	expiry = g_get_monotonic_time() + (gint64) (wait_s * G_USEC_PER_SEC);
	/* ⭐ PHASE 17 — and a stream in ERROR will deliver nothing more: we exit
	 *    at once instead of waiting the whole timeout.  `[M]` 29 Sep 2026, VM without
	 *    3D: the negotiation refusal arrived in milliseconds and the take
	 *    said so five seconds later, at every login.  ⚠ `on_state` writes the
	 *    state BEFORE taking the lock and waking up: here, with the lock
	 *    in hand, the state read is the one of the wake-up. */
	while (!capture_v->slot_full && capture_v->state != PW_STREAM_STATE_ERROR)
	{
		if (!g_cond_wait_until(&capture_v->news, &capture_v->lock, expiry))
			break;
	}
	if (capture_v->slot_full)
	{
		/* ⛔ The buffer PASSES to the consumer — who will free it with
		 *    `capture_stopped_free()` — so the slot stays without one, and the
		 *    capacity goes back to zero: on the next round a new one is allocated.
		 * ⚠ It is the honest price of reuse: we reuse as long as nobody consumes
		 *   (the burst), and reallocate when someone really consumes. */
		*outside = capture_v->slot;
		/* ⭐⭐ AND HERE WE READ THE AGE OF THE FRAME — the segment entry that
		 *     nobody looked at.  ⛔ It is not work: it is the time the
		 *     frame sat still waiting for the loop to come back and
		 *     ask for it, and it ages the frame without anybody
		 *     noticing.  `[M]` phase 4: the empty waits are **0.00/s**, that is
		 *     **there was always something ready already** — which said the other way round
		 *     means that the frame was waiting for US. */
		outside->in_slot_us = current_us() - outside->arrival_us;
		memset(&capture_v->slot, 0, sizeof capture_v->slot);
		capture_v->slot_capacity = 0;
		capture_v->slot_full = FALSE;
		taken = TRUE;
	}
	capture_v->someone_waiting = FALSE;
	g_mutex_unlock(&capture_v->lock);

	/* ⛔ «It WAS active» is not «it still is»: death in the middle of a take. */
	if (capture_v->state != PW_STREAM_STATE_STREAMING && capture_v->state != PW_STREAM_STATE_PAUSED)
	{
		capture_stopped_free(outside);
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "the stream was alive and fell during the take (state %s%s%s)",
		            pw_stream_state_as_string(capture_v->state), capture_v->fault ? ", fault: " : "",
		            capture_v->fault ? capture_v->fault : "");
		return CAPTURE_TAKE_FAULT;
	}

	if (!taken)
	{
		/* ⭐ LEGITIMATE ZERO: the stream was active for the whole wait and nothing
		 *    arrived.  On Mutter it is the idle desktop — the rate is 0/1,
		 *    «send me a frame when something changes» — and it is a result,
		 *    not a fault. */
		return CAPTURE_TAKE_ZERO;
	}

	/* ⛔ THE ROUTE IS VERIFIED, NOT TAKEN AS REQUESTED (`LEZIONI.md` §1.8). */
	if (capture_v->route == CAPTURE_ROUTE_CARD &&
	    outside->delivery.buffer_declared != CAPTURE_BUFFER_DMABUF)
	{
		CaptureBuffer landed = outside->delivery.buffer_declared;

		capture_stopped_free(outside);
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "the card (DMA-BUF) was requested and the producer delivered %s: no "
		            "silent fallback",
		            capture_buffer_name(landed));
		return CAPTURE_TAKE_FAULT;
	}
	if (capture_v->route == CAPTURE_ROUTE_MEMORY &&
	    outside->delivery.buffer_declared == CAPTURE_BUFFER_DMABUF)
	{
		capture_stopped_free(outside);
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "memory was requested and DMA-BUFs arrived: the pixels are not here");
		return CAPTURE_TAKE_FAULT;
	}

	if (!outside->pixel)
	{
		/* Card route: the type is declared, the pixels live elsewhere.
		 * ⛔ It is not a fault and not a zero, and it is the third exit.
		 *
		 * ⭐ But BEFORE returning we look **only once** inside the buffer:
		 *    see `look_dmabuf_pixels`. */
		if (outside->on_card && capture_v->last_measure_us == 0)
		{
			uint64_t tm = current_us();
			gboolean ceiling = FALSE;
			guint watched = look_dmabuf_pixels(capture_v, outside, &ceiling);
			capture_v->last_measure_us = tm;
			outside->measure_us = current_us() - tm;
			if (outside->delivery.measured_pixels)
			{
				capture_v->measures_done++;
				log_says(AREA,
				              "⭐ the FIRST card frame was looked at "
				              "by mapping the DMA-BUF: %s — %u sampled pixels over "
				              "%ux%u%s (%.2f ms).  ⛔ It is the ONLY one "
				              "looked at on this route — see the box: the following ones "
				              "carry `measured_pixels` FALSE, which means «I did not "
				              "look» and NOT «it is not black»",
				              outside->delivery.nero ? "⛔ BLACK"
				                                   : (outside->delivery.uniform
				                                          ? "⚠ UNIFORM"
				                                          : "not black"),
				              watched, outside->width_px, outside->height_px,
				              ceiling ? ", ⚠ time CEILING expired with the grid incomplete" : "",
				              outside->measure_us / 1000.0);
			}
			else if (ceiling)
				log_says(AREA,
				              "⚠ the FIRST card frame was NOT "
				              "judged — CEILING of %u ms expired after %u sampled "
				              "pixels all dark or equal (%.2f ms): «I did not "
				              "look», not «it is not black»",
				              SAMPLE_CAP_US / 1000u, watched,
				              outside->measure_us / 1000.0);
		}
		return CAPTURE_TAKE_PIXEL_ELSEWHERE;
	}

	/* ⭐⭐ THE PASS OVER THE PIXELS, AT A RATE — see `PIXEL_MEASURE_EVERY_MS`.
	 *
	 * ⛔ The FIRST is always looked at (`last_measure_us == 0`): it is the one whose
	 *    line «⛔ BLACK / not black» `figlio.c` writes, and it is also the only
	 *    frame the bench `banchi/02-cattura-prodotto.c` can count on
	 *    for sure. */
	{
		uint64_t tm = current_us();

		if (capture_v->last_measure_us == 0 ||
		    tm - capture_v->last_measure_us >= (uint64_t) PIXEL_MEASURE_EVERY_MS * 1000u)
		{
			measure_pixels(outside);
			outside->delivery.measured_pixels = TRUE;
			capture_v->last_measure_us = tm;
			capture_v->measures_done++;
			outside->measure_us = current_us() - tm;

			if (outside->delivery.nero)
				log_says(AREA,
				              "⛔ the delivered frame is BLACK (maximum 0 on all "
				              "three channels): it is what a session without a "
				              "virtual monitor delivers — STUDI.md §gnome §3.1, fault M9");
			else if (outside->delivery.uniform)
				log_says(AREA,
				              "⚠ the delivered frame is UNIFORM: all pixels "
				              "equal, and this is not black — it is a buffer never painted");
		}
		else
		{
			/* ⛔ AND HERE THE PREVIOUS ANSWER IS NOT COPIED: `nero` and `uniform`
			 *    stay `FALSE` and `measured_pixels` stays `FALSE`, which together
			 *    say **«I did not look»**.  ⚠ Writing the last
			 *    known value into them would be worse than silence: the reader would believe
			 *    that those three facts concern THIS frame, while there
			 *    they concern another one (`LEZIONI.md` §1.11, two measurements under the
			 *    same label). */
			capture_v->measures_skipped++;
			if (capture_v->measures_skipped == 1)
				log_says(AREA,
				              "⭐ from here on the pass over the pixels is done at most every %d ms and no "
				              "longer on every frame: `[M]` it cost 5.34 ms on a segment "
				              "of 21.6 (25 %%) to fill ONE log line.  ⚠ On the "
				              "skipped frames `measured_pixels` is FALSE, and «not black» "
				              "is NOT deduced from `nero == FALSE`",
				              PIXEL_MEASURE_EVERY_MS);
		}
	}
	return CAPTURE_TAKE_DONE;
}

void capture_stopped_free(CaptureStopped *stopped)
{
	if (!stopped)
		return;
	/* ⭐ PHASE 13 — the wlroots card slab goes back to `wlroots.c`.
	 *    ⚠ Before the PipeWire branch, and zeroing `held_buffer`: that branch must
	 *    not see a pointer that is not a `pw_buffer`.  ⛔ It triggers ONLY
	 *    with `->wlr`: for GNOME and KDE `owner->wlr` is NULL and the release
	 *    below stays what it was, word for word. */
	if (stopped->held_buffer && stopped->owner && ((Capture *) stopped->owner)->wlr)
	{
		wlr_release(((Capture *) stopped->owner)->wlr, stopped->held_buffer);
		stopped->held_buffer = NULL;
	}
	/* ⭐⭐ THE RELEASE — and it lives here because this is the only place where we know that
	 *     the reader has finished.  ⛔ Before this line the `pw_buffer` is
	 *     ours and Mutter does not repaint inside it; after, it is its own.
	 * ⚠ And it is given back BEFORE zeroing the held frame, because zeroing erases
	 *   precisely the two fields that say whom to give it back to. */
	if (stopped->held_buffer && stopped->owner)
		release_withheld((Capture *) stopped->owner, (struct pw_buffer *) stopped->held_buffer,
		               stopped->generation);
	g_free(stopped->pixel);
	memset(stopped, 0, sizeof *stopped);
}

/* ------------------------------------------------------------------ *
 *  What is declared downstream
 * ------------------------------------------------------------------ */

gboolean capture_delivery(Capture *capture_v, CaptureDelivery *outside)
{
	g_return_val_if_fail(capture_v != NULL && outside != NULL, FALSE);

	memset(outside, 0, sizeof *outside);

	if (capture_v->wlr) {
		const WlrFrame *w = &capture_v->wlr_last;

		if (!capture_v->wlr_last_known)
			return FALSE; /* no frame yet: «I do not know» */
		outside->known = TRUE;
		outside->requested_route = capture_v->route;
		/* ⛔ The buffer is a `wl_shm` we created ourselves: the type is not
		 *    «declared», it is KNOWN.  ⚠ And MEMFD is not written by analogy with
		 *    PipeWire: it is the same thing (a shared memfd), and calling it by the
		 *    name the reader already knows is worth more than a new name. */
		/* ⭐ And since 21 Sep 2026 there are two routes: the type is told by the
		 *    FRAME (`on_card`), the question by `route`. */
		outside->buffer_requested = capture_v->route == CAPTURE_ROUTE_CARD
		                            ? CAPTURE_BUFFER_DMABUF
		                            : CAPTURE_BUFFER_MEMFD;
		outside->buffer_declared =
		    w->on_card ? CAPTURE_BUFFER_DMABUF : CAPTURE_BUFFER_MEMFD;
		outside->buffer_declared_raw = 0;
		outside->distinct_buffers = 1;
		outside->raw_format = w->schema;
		outside->schema = capture_color_name(w->schema);
		outside->bit_per_channel = 8;
		outside->source_bit = CAPTURE_SOURCE_FORMAT;
		outside->width_px = w->width_px;
		outside->height_px = w->height_px;
		outside->stride = w->stride;
		outside->stride_read = TRUE;
		outside->byte = w->byte;
		outside->modifier = w->on_card ? w->modifier : 0;
		/* ⛔ The colour: the compositor declares neither range nor matrix, and
		 *    here we do NOT invent.  `measured_pixels` stays FALSE: whoever reads
		 *    `nero`/`uniform` must find them not looked at, not false. */
		outside->source_range = CAPTURE_SOURCE_UNDECLARED;
		outside->source_matrix = CAPTURE_SOURCE_UNDECLARED;
		outside->measured_range = CAPTURE_RANGE_UNMEASURED;
		outside->measured_pixels = FALSE;
		return TRUE;
	}

	if (!capture_v->known_format)
		return FALSE; /* ⛔ «I do not know yet», and not «it is all zero» */

	outside->known = TRUE;
	outside->requested_route = capture_v->route;
	outside->buffer_requested =
	    capture_v->route == CAPTURE_ROUTE_CARD ? CAPTURE_BUFFER_DMABUF : CAPTURE_BUFFER_MEMFD;
	outside->buffer_declared =
	    capture_v->count.how_many_types > 0 ? capture_v->count.seen_types[0] : CAPTURE_BUFFER_UNKNOWN;
	outside->buffer_declared_raw = capture_v->first_raw_type;
	outside->distinct_buffers = capture_v->count.distinct_buffers;
	outside->raw_format = capture_v->schema.format;
	outside->schema = capture_color_name(capture_v->schema.format);
	outside->bit_per_channel = bit_per_channel(capture_v->schema.format);
	outside->source_bit =
	    outside->bit_per_channel > 0 ? CAPTURE_SOURCE_FORMAT : CAPTURE_SOURCE_UNDECLARED;
	outside->width_px = capture_v->schema.size.width;
	outside->height_px = capture_v->schema.size.height;
	outside->modifier = capture_v->schema.modifier;
	outside->raw_range = capture_v->schema.color_range;
	outside->raw_matrix = capture_v->schema.color_matrix;
	outside->raw_transfer = capture_v->schema.transfer_function;
	outside->raw_primaries = capture_v->schema.color_primaries;
	outside->source_range =
	    capture_v->schema.color_range ? CAPTURE_SOURCE_PRODUCER : CAPTURE_SOURCE_UNDECLARED;
	outside->source_matrix =
	    capture_v->schema.color_matrix ? CAPTURE_SOURCE_PRODUCER : CAPTURE_SOURCE_UNDECLARED;
	/* ⛔ The stride is NOT put here: until a frame has arrived it is not
	 *    a fact, and it is the field that must not be recomputed downstream.  The
	 *    frame carries it. */
	outside->stride = 0;
	outside->stride_read = FALSE;
	outside->byte = 0;
	return TRUE;
}

void capture_counts(Capture *capture_v, CaptureCounts *outside)
{
	if (capture_v && capture_v->wlr) {
		WlrCounts w;

		wlr_counts(capture_v->wlr, &w);
		memset(outside, 0, sizeof *outside);
		outside->arrived = w.grabbed;
		/* ⚠ The other fields stay zero, and NOT because they are worth zero: on
		 *   this source they do not exist (the damage book, the cursor
		 *   channel, the PipeWire buffer types).  Whoever reads them finds zero and
		 *   must know it means «this quantity does not exist here». */
		return;
	}
	g_return_if_fail(capture_v != NULL && outside != NULL);
	*outside = capture_v->count;
}

const char *capture_output_name(Capture *capture_v)
{
	if (capture_v && capture_v->wlr)
		return wlr_output_name(capture_v->wlr);
	return NULL;
}

gboolean capture_active(Capture *capture_v)
{
	if (capture_v && capture_v->wlr)
		return TRUE;
	return capture_v && capture_v->state == PW_STREAM_STATE_STREAMING;
}

const char *capture_fault(Capture *capture_v)
{
	return capture_v ? capture_v->fault : NULL;
}

gboolean capture_format_refused(Capture *capture_v)
{
	/* ⛔ The two conditions together, and neither is enough on its own:
	 *    `ERROR` without a format is the failed negotiation; `ERROR` AFTER a
	 *    format is a stream that died after being born, and there the requested
	 *    route existed.  ⚠ On wlroots there is no PipeWire negotiation: its
	 *    fallback lives in `capture_start_wlr()`. */
	/* ⭐ 6 Oct 2026, `[M]` NVIDIA + GNOME 50: Mutter AGREES a format (with the
	 *    INVALID modifier), fails to allocate it, withdraws it, and the stream
	 *    goes into error without ever having delivered a buffer.  ⇒ «format
	 *    agreed but no frame arrived» is a refusal too: the requested route
	 *    here never gave anything. */
	return capture_v && !capture_v->wlr && capture_v->state == PW_STREAM_STATE_ERROR &&
	       (!capture_v->known_format || capture_v->count.arrived == 0);
}

void capture_cursor(Capture *capture_v, CursorArrived when_changes, void *chi)
{
	/* ⛔ PHASE 13 — on this family a channel for the pointer SHAPE does not
	 *    exist: there is only `overlay_cursor`, and the pointer sits INSIDE
	 *    the image.  Until 24 September 2026 the registration was accepted
	 *    and never called back.
	 * ⭐ Since 24 September the shape is found by the PROBE (`wlroots.h`), and it arrives
	 *    through `cursor_bounce` as on GNOME and KDE (`wlr_shape_delivery`).
	 *    ⇒ The registration counts here too; the line says where it will come from. */
	if (capture_v && capture_v->wlr)
		log_says(AREA,
		              "⭐ wlroots: the pointer shape is found by the PROBE (a 3x3 "
		              "under the point, after every gesture) and the dictionary of the encoded "
		              "theme: whoever registered will be called back at every change");
	if (!capture_v)
		return;
	g_mutex_lock(&capture_v->lock);
	capture_v->cursor_fn = when_changes;
	capture_v->cursor_who = chi;
	g_mutex_unlock(&capture_v->lock);
}

void capture_cursor_never_hide(Capture *capture_v, const char *reason_text)
{
	if (capture_v && capture_v->wlr)
		return; /* no cursor channel: there is nothing to not hide */
	if (!capture_v)
		return;
	g_mutex_lock(&capture_v->lock);
	cursor_never_hide(capture_v->pointer_shape, reason_text);
	g_mutex_unlock(&capture_v->lock);
}

void capture_stop(Capture *capture_v)
{
	if (!capture_v)
		return;

	if (capture_v->wlr) {
		WlrCounts w;
		WlrProbeCounts so;

		wlr_probe_counts(capture_v->wlr, &so);
		log_says(AREA,
		              "wlroots: pointer probe — gestures %" G_GUINT64_FORMAT
		              ", probes sent %" G_GUINT64_FORMAT " (trailing %" G_GUINT64_FORMAT
		              "), returned %" G_GUINT64_FORMAT ", failed %" G_GUINT64_FORMAT
		              "; new shapes %" G_GUINT64_FORMAT " (from neighbours %" G_GUINT64_FORMAT
		              "), without our colour %" G_GUINT64_FORMAT "; delivered %"
		              G_GUINT64_FORMAT ", same drawing %" G_GUINT64_FORMAT,
		              so.asks, so.launched, so.of_queue, so.returned, so.failures, so.changes,
		              so.from_neighbors, so.unrecognized, capture_v->wlr_shapes_sent,
		              capture_v->wlr_shapes_equal);
		wlr_counts(capture_v->wlr, &w);
		log_says(AREA,
		              "wlroots: capture closed — requested %" G_GUINT64_FORMAT
		              ", taken %" G_GUINT64_FORMAT " (on the CARD %" G_GUINT64_FORMAT
		              ", in MEMORY %" G_GUINT64_FORMAT "), failed %" G_GUINT64_FORMAT
		              ", timed out %" G_GUINT64_FORMAT,
		              w.asked, w.grabbed, w.on_card, w.in_memory, w.failed,
		              w.expired);
		wlr_close(capture_v->wlr);
		g_free(capture_v);
		return;
	}

	/*
	 * First the thread is stopped, then the rest is destroyed: stopping it first
	 * there is no longer any need to take the lock to touch the PipeWire objects, and
	 * above all there is no risk of destroying the stream while a callback
	 * is using it.
	 */
	/* ⛔⭐ AND FIRST OF ALL WE GIVE BACK WHAT IS LEFT IN HAND — the buffer
	 *     held in the slot, which nobody consumed.  ⚠ Giving it back after
	 *     `pw_stream_destroy` would be writing into freed memory; not giving it back
	 *     at all is harmless here (the stream dies anyway) but would leave the
	 *     count of held buffers unbalanced, and that count is the only thing that
	 *     says whether the retention loses buffers.
	 *
	 * ⛔⛔ AND THE CALLER MUST HAVE ALREADY FREED ITS `CaptureStopped`: a held frame
	 *      freed AFTER this function gives a buffer back to a `Capture` that no longer
	 *      exists.  `figlio.c` does it in the right order in all three
	 *      places where it tears down the stage, and this line is the reason why. */
	if (capture_v->cycle && capture_v->flow)
	{
		pw_thread_loop_lock(capture_v->cycle);
		if (capture_v->slot.held_buffer)
		{
			pw_stream_queue_buffer(capture_v->flow,
			                       (struct pw_buffer *) capture_v->slot.held_buffer);
			capture_v->slot.held_buffer = NULL;
			capture_v->slot.owner = NULL;
			capture_v->slot_full = FALSE;
			capture_v->held_returned++;
		}
		pw_thread_loop_unlock(capture_v->cycle);
	}
	if (capture_v->held_count)
		log_says(AREA,
		              "the retention closes: %" G_GUINT64_FORMAT " buffers held, %"
		              G_GUINT64_FORMAT " given back.  ⛔ The difference (%lld) is how many were "
		              "still in hand, and if it is not zero someone did not free their "
		              "`CaptureStopped`",
		              capture_v->held_count, capture_v->held_returned,
		              (long long) capture_v->held_count - (long long) capture_v->held_returned);

	if (capture_v->cycle)
		pw_thread_loop_stop(capture_v->cycle);
	if (capture_v->flow)
		pw_stream_destroy(capture_v->flow);
	if (capture_v->core)
		pw_core_disconnect(capture_v->core);
	if (capture_v->context)
		pw_context_destroy(capture_v->context);
	if (capture_v->cycle)
		pw_thread_loop_destroy(capture_v->cycle);

	/* ⛔ AFTER the thread, not before: `look_cursor` runs over there. */
	cursor_close(capture_v->pointer_shape);

	g_free(capture_v->slot.pixel);
	g_mutex_clear(&capture_v->lock);
	g_cond_clear(&capture_v->news);
	g_free(capture_v->fault);
	g_free(capture_v);
}
