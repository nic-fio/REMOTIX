/*
 * capture_v — the pixels, read from the PipeWire node Mutter opened.
 *
 * ⛔ THE MANDATE OF THIS FILE, IN ONE LINE: **a frame delivered in
 *    memory with the buffer type DECLARED, not deduced.**
 *
 * ⛔ CARRIED OVER from `fondamenta/remotix-c/src/cattura.c` (1060 lines) and NOT copied.
 *    That file carried the RDP apparatus that does not exist in V2 — the road
 *    switched with capture live because AVC420 wants the GPU and RemoteFX the CPU,
 *    the negotiable size for KWin 6.8, the phase 6 resizing — and
 *    none of that is here.  What survives are the three rules that were
 *    the real value of that file, and they are in the three boxes below.
 *
 * ===========================================================================
 * ⛔ 1. THE STRIDE IS READ FROM THE BUFFER'S CHUNK, NEVER COMPUTED
 *
 * The producer aligns rows as it sees fit, and deducing `width × 4`
 * produces skewed images.  ⚠ `[M]` 12 August 2026: at 1920×1080 the measured stride
 * is **7680**, that is exactly `width × 4` — ⛔ **and that is precisely why
 * the rule must be written**: today it coincides, and whoever gets used to computing it will not
 * notice the day it no longer coincides.  Whoever is downstream reads
 * `stride` from here, and does not redo it.
 *
 * ⇒ If the producer delivered `stride == 0` this module **discards the
 *   frame and counts it**, instead of computing one: a skewed frame
 *   gives no error, and comes out well enough not to be noticed.
 *
 * ===========================================================================
 * ⛔ 2. THE BUFFER TYPE IS REQUESTED IN TWO PLACES, AND IT IS DECLARED
 *
 * DMA-BUF is requested in the `modifier` field of the FORMAT (with
 * `MANDATORY | DONT_FIXATE`) **and** with the `SPA_DATA_DmaBuf` bit in
 * `SPA_PARAM_Buffers`.  Declaring only one, negotiation succeeds anyway
 * and buffers keep arriving in memory: no error, no log
 * line, and zero copy is simply not there (`[M]` 6 August 2026).
 *
 * ⛔ AND WHAT THE TYPE DOES **NOT** SAY — form E1 of `REVIEWER.md` §2, already paid
 *    for TWICE (`LEZIONI.md` §1.11):
 *
 *      "delivers MemFd  ⇒ Mutter renders in software"   ⛔ FALSE
 *      "it opened a render node ⇒ renders on the GPU"   ⛔ FALSE
 *
 *    The type that arrives is the answer to what **we asked for**, not
 *    a discovery about the compositor.  That is why `CaptureDelivery` carries the
 *    **requested** type and the **declared** type in two different fields, and next to them who
 *    says so: they are three facts, not one.
 *
 * ===========================================================================
 * ⛔ 3. THE CADENCE IS DECLARED AT ZERO, with a maximum as interval
 *
 * `framerate = 0/1` plus `maxFramerate` means "send me a frame when
 * something changes, not at a fixed rate" — which is the behaviour a
 * remote desktop needs.  ⛔ It follows that **on a still desktop nothing arrives**:
 * it is wanted behaviour, not a fault (`LEZIONI.md` §4 trap 8), and it is
 * the reason why `capture_take` tells **zero from failure** apart with
 * two different return values (`CODER.md` §3.10).
 *
 * ===========================================================================
 * ⛔ DAMAGE IS INFORMATION ABOUT HOW MUCH HAS CHANGED — NOT THE CONDITION FOR
 *    WHICH THE BUFFER CAN BE READ
 *
 * ⚠ `fondamenta/remotix-c/src/cattura.h` said the opposite, and measurement
 *   refuted it.  It said: *"in zero-copy Mutter recycles its own buffers and
 *   repaints inside them ONLY the changed part; outside those regions are the
 *   pixels of the frame that had used that buffer before"* (7 August 2026).
 *
 * `[M]` 12 August 2026, F2.2 — NIC-OS, Mutter 48.7 headless, MEMORY road,
 * 1920×1080 virtual monitor, "flag" scene: damage is **partial on all
 * 410 frames**, the first included, and the seven SMPTE bars read
 * **whole** in the steady-state frame.  ⇒ **the buffer is whole even when
 * damage is partial.**
 *
 * `[R]` `STUDI.md` §gnome §8.1, Mutter reread line by line, already said so: blit
 * of the WHOLE framebuffer, clip stack deliberately emptied, virtual
 * view as a persistent `CoglOffscreen`.  The two roads agree.
 *
 * ⛔ AND THE CONSEQUENCE STILL ALIVE IN THE INHERITED CODE: in
 *    `fondamenta/remotix-c/src/palco.c:598-628` zero copy is born **off on GNOME**
 *    for this reason, and this reason **is dead**.  ⚠ Which does NOT say that
 *    zero copy on GNOME works: it says that the reason it was off is
 *    gone, and that the decision must be taken up again **on a measurement** instead of on
 *    that comment.  Here the road is chosen by the caller (`CaptureRoute`), and
 *    phase 2 asks for memory for a reason of its own, declared: **it wants readable
 *    pixels**.
 *
 * ⚠ What damage is for, then: to know HOW MUCH was repainted —
 *   that is, how much is worth re-encoding — and to tell "the producer does not
 *   declare damage" from "the damage covered everything".  We keep asking for it,
 *   because not asking for it means not receiving it.
 *
 * ===========================================================================
 * ⚠ THE PIPEWIRE LOOP LIVES ON A THREAD OF ITS OWN (`pw_thread_loop`).  The
 *   callbacks below are called FROM THAT THREAD, which is real-time:
 *   whoever writes them must not wait for anything inside them, and in particular must not
 *   call `capture_stop` from inside `CaptureEnd`.
 *
 *   ⛔ And the pixels live ONLY for the duration of the call: as soon as it returns, the
 *      buffer goes back to PipeWire.  Whoever wants them copies them — or uses
 *      `capture_take`, which makes the copy itself.
 */
#ifndef REMOTIX_CAPTURE_H
#define REMOTIX_CAPTURE_H

#include <glib.h>
#include <stdint.h>

#include "cursore.h"

typedef struct Capture Capture;

/* ------------------------------------------------------------------ *
 *  The buffer type — requested and declared
 * ------------------------------------------------------------------ */

typedef enum
{
	CAPTURE_BUFFER_UNKNOWN = 0,
	CAPTURE_BUFFER_MEMFD,
	CAPTURE_BUFFER_MEMPTR,
	CAPTURE_BUFFER_MEMID,
	CAPTURE_BUFFER_DMABUF
} CaptureBuffer;

/* The road that is REQUESTED.  ⛔ It is not the same thing as the type that arrives, and the
 * two are in two different fields on purpose: if the card is requested and memory
 * arrives, `capture_start` FAILS declaring it instead of falling back
 * silently (`LEZIONI.md` §1.8, corollary). */
typedef enum
{
	CAPTURE_ROUTE_MEMORY = 0, /* MemFd/MemPtr: the pixels can be read        */
	CAPTURE_ROUTE_CARD       /* DMA-BUF: the pixels are NOT here, an fd is  */
} CaptureRoute;

/*
 * The colour that is REQUESTED.
 *
 * ⛔ And `CAPTURE_COLOR_10BIT` is not a hope: it is **the question**, put to the
 *    producer instead of deduced.  `STUDI.md` §gnome §8.3 `[R]`, Mutter 48.7 reread
 *    line by line (`meta-screen-cast-stream-src.c`, `supported_formats[]`):
 *    **only two entries, BGRx and BGRA**, both at 8 bits per channel.  ⇒ From this
 *    source real ten bits do not come out.
 *
 *    Asking for the 10-bit format and receiving a refusal turns that reading
 *    into a **measurement**, and the refusal must be written instead of deduced: it is the only
 *    way to close the `[?]` without deduction (`LEZIONI.md` §1.11).
 */
typedef enum
{
	CAPTURE_COLOR_BGRX = 0,
	CAPTURE_COLOR_BGRA,
	CAPTURE_COLOR_10BIT
} CaptureColor;

/* Where a value comes from.  ⛔ "Not declared" IS AN ANSWER, and not a field
 * to fill with what we expect: silence mistaken for a value is
 * form E8. */
typedef enum
{
	CAPTURE_SOURCE_UNDECLARED = 0, /* the producer is silent (SPA UNKNOWN)  */
	CAPTURE_SOURCE_PRODUCER,         /* SPA_PARAM_Format, asked of it         */
	CAPTURE_SOURCE_FORMAT,            /* follows from the negotiated format    */
	CAPTURE_SOURCE_MEASURED            /* [M] counted by us on the pixels       */
} CaptureSource;

/* The outcome of the range measurement made on the delivered pixels.  ⛔ There is no
 * "LIMITED" value: a scene that does not reach 255 does not prove a limited
 * range — it only proves that that scene does not reach it.  The two honest answers
 * are "compatible with full" and "inconclusive". */
typedef enum
{
	CAPTURE_RANGE_UNMEASURED = 0,
	CAPTURE_RANGE_COMPATIBLE_FULL, /* the pixels touch 0 and 255            */
	CAPTURE_RANGE_INCONCLUSIVE     /* they do not: it depends on the SCENE  */
} CaptureRangeMeasured;

/* ------------------------------------------------------------------ *
 *  ⛔ THE FOUR FACTS DECLARED DOWNSTREAM
 * ------------------------------------------------------------------ *
 *
 *   1. the BUFFER TYPE     requested and declared, with who says so
 *   2. the BITS PER CHANNEL from the negotiated format, never invented
 *   3. the GEOMETRY        size, stride READ, bytes per frame
 *   4. the COLOUR          range · matrix · transfer · primaries, as the
 *                          producer declares them — "not declared" included
 *
 * ⛔ Whoever is downstream reads these fields.  They do not deduce them, do not recompute them, and in
 *    particular do not recompute the stride.
 */
typedef struct
{
	gboolean known; /* FALSE until the format has been negotiated */

	/* --- 1. the buffer type --------------------------------------------- */
	CaptureRoute requested_route;
	CaptureBuffer buffer_requested;
	CaptureBuffer buffer_declared; /* CAPTURE_BUFFER_UNKNOWN until the 1st frame */
	uint32_t buffer_declared_raw;
	guint distinct_buffers; /* how many different buffers the producer recycles */

	/* --- 2. the format and the bits ------------------------------------- */
	uint32_t raw_format;
	const char *schema; /* "BGRx", "BGRA", … — never an invented word */
	int bit_per_channel;  /* 8; ⛔ 0 = unknown format, and 0 is written    */
	CaptureSource source_bit;

	/* --- 3. the geometry ------------------------------------------------ */
	uint32_t width_px, height_px;
	uint32_t stride;         /* ⛔ READ from the chunk. 0 = no frame yet         */
	gboolean stride_read;   /* FALSE ⇒ `stride` is not a fact, it is a blank   */
	guint64 byte;            /* stride × height                                 */
	uint64_t modifier;

	/* --- 4. the colour, as the producer declares it --------------------- */
	uint32_t raw_range, raw_matrix, raw_transfer, raw_primaries;
	CaptureSource source_range, source_matrix;

	/* --- and the measurement WE make, because the producer is silent ---- */
	uint8_t minimum[3], maximum[3]; /* R, G, B */
	CaptureRangeMeasured measured_range;
	gboolean nero;    /* ⛔ all pixels at zero: the worst fault of F2.2      */
	gboolean uniform; /* all pixels equal to each other (black included)    */
	/* ⛔⛔ AND THIS FIELD IS THE REASON WHY THE THREE ABOVE CAN
	 *     STILL BE READ — `LEZIONI.md` §1.9, "empty" and "forbidden" look
	 *     the same.
	 *
	 * Since 22 August 2026 the pass over the pixels **is not done on every frame**: `[M]`
	 * it cost **5.34 ms** within a span of **21.6**, that is **25 %**, to
	 * fill a log line that is written **only once**
	 * (`figlio.c`, the mounting of the stage).  ⇒ Now it is done on the FIRST frame
	 * and then at most once every `PIXEL_MEASURE_EVERY_MS`.
	 *
	 * ⛔ On an unmeasured frame `nero` and `uniform` are `FALSE` — and
	 *    `FALSE` here would mean **"it is not black"**, which is a LIE: it means
	 *    "I did not look".  Whoever reads those three fields **must** look at this one
	 *    first, exactly as `stride_read` sits next to `stride`.
	 * ⚠ `measured_range` can already say so by itself (`CAPTURE_RANGE_UNMEASURED`);
	 *   `nero` and `uniform` cannot, and this field exists for them. */
	gboolean measured_pixels;
} CaptureDelivery;

/* ------------------------------------------------------------------ *
 *  The frame
 * ------------------------------------------------------------------ */

/* A changed region (`SPA_META_VideoDamage`).  ⛔ Information, not
 * condition: see the box at the top. */
typedef struct
{
	uint32_t x, y, width_px, height_px;
} CaptureRegion;

typedef struct
{
	/* ⛔ `pixel` is NULL on the card road: there is no pointer there,
	 *    there is a descriptor living on the GPU.  Whoever checks "no pointer
	 *    ⇒ no frame" without first looking at the type discards every DMA-BUF
	 *    silently — measured on 6 August 2026, and it cost a round of tests. */
	const uint8_t *pixel;
	guint64 byte;
	int fd; /* -1 if absent */
	uint32_t offset;
	uint32_t stride; /* ⛔ read from the chunk */

	uint64_t seq;
	int64_t pts;
	gboolean seq_valid;

	const CaptureRegion *damage;
	guint how_many_regions;
	gboolean declared_damage;
	gboolean damage_covers_all;

	guint64 idx; /* which frame it was, counted from the first that arrived */
	const CaptureDelivery *delivery;
} CaptureFrameInfo;

typedef void (*CaptureFrame)(const CaptureFrameInfo *frame, gpointer data_v);

/* The stream has come off: either the graphical session is over, or Mutter
 * stopped it on its own. */
typedef void (*CaptureEnd)(gpointer data_v);

/* ------------------------------------------------------------------ *
 *  The STILL frame — the deliverable of phase 2
 * ------------------------------------------------------------------ */

/*
 * A copy of our own of the frame, which lives until it is freed.
 *
 * ⭐ It is the product of F2.2: *a still image*, taken from the session and put
 *    in memory, with next to it everything needed to judge it without deducing
 *    anything.
 */
typedef struct
{
	uint8_t *pixel;
	guint64 byte;
	uint32_t stride, width_px, height_px;
	uint64_t seq;
	int64_t pts;
	gboolean seq_valid;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ ZERO COPY — the frame that was NOT copied
	 * ------------------------------------------------------------------ *
	 *
	 * ⛔ On the CARD road `pixel` stays **NULL** and these fields are
	 *    the only way to reach the image: it is not a pointer, it is a
	 *    descriptor living on the GPU.  Whoever reads must look at
	 *    `on_card` BEFORE `pixel`, or will discard every card
	 *    frame silently (`[M]` 6 August 2026, and it cost a round of
	 *    tests).
	 *
	 * ⛔⛔ AND THE BUFFER IS **HELD** UNTIL
	 *      `capture_stopped_free()` IS CALLED — see the HOLD box in
	 *      `cattura.c`.  Whoever keeps this `CaptureStopped` longer than
	 *      necessary takes a buffer away from the producer; whoever frees it before
	 *      finishing reading gets the image rewritten under their eyes
	 *      (`LEZIONI.md` §8: the two alternating screens were not an
	 *      *acquire* problem, they were a *release* one).
	 */
	gboolean on_card;
	int fd;              /* ⛔ NOT ours: PipeWire owns it, do not close        */
	uint32_t offset;
	uint32_t format_drm; /* `DRM_FORMAT_XRGB8888` … — what VA-API wants      */
	uint64_t modifier;
	/* ⛔ The GENERATION of the producer's buffers: it changes every time
	 *    PipeWire reallocates them (a renegotiation, a wake-up).  ⚠ It serves
	 *    whoever caches the import of an `fd`: **descriptor numbers
	 *    are recycled**, and a cache that looked at the `fd` alone
	 *    would give VA-API a surface pointing to a freed buffer — that is
	 *    an earlier image, or worse.  Two measurements under the same label,
	 *    in the form that gives no error. */
	uint64_t generation;
	/* ⛔ Opaque: the held `pw_buffer` and whoever will give it back.  They are not
	 *    read from outside — they exist so that `capture_stopped_free()` knows to
	 *    whom to give the buffer back without the caller having to keep the
	 *    `Capture` next to the frame. */
	void *held_buffer;
	void *owner;
	gboolean declared_damage, damage_covers_all;
	guint64 idx;          /* which frame it was among those arrived */
	CaptureDelivery delivery; /* the four facts, frozen with it        */

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ THE SPANS OF THE GRAB — the phase 8 instrumentation
	 * ------------------------------------------------------------------ *
	 *
	 * ⛔ THE FACT THAT GIVES BIRTH TO THEM: `[M]` phase 4, the span `capture → first
	 *    byte` is **30.37 ms** and the three times the encoder already
	 *    declared — conversion 5.6 · upload 2.9 · encoding 5.3 — explain
	 *    **13.8** of it.  ⇒ **~16 ms had no owner**, and a
	 *    nameless margin is not cured: it is instrumented first.
	 *
	 * ⛔ AND THESE FOUR ARE THE PIECE OF SPAN THAT LIES **BEFORE** THE
	 *    ENCODER, that is the only one nobody looked at.  They are microseconds, and
	 *    they are four because they answer four different questions:
	 *
	 *      `arrival_us`      the instant (CLOCK_MONOTONIC) at which the frame was
	 *                       put in the slot.  ⛔ It is not a cost: it is the
	 *                       reference the others are subtracted from, and
	 *                       next to Mutter's `pts` it says how long the
	 *                       producer takes to get to us;
	 *      `copy_us`       the `memcpy` inside the real-time callback;
	 *      `alloc_us` the `g_malloc` of the slot — ⛔ **0 when the buffer
	 *                       was reused**, and it is precisely the number that says
	 *                       whether the reuse of `slot_capacity` is working or whether
	 *                       it reallocates at every turn;
	 *      `in_slot_us`   ⭐ **how long the frame stayed STILL in the slot**
	 *                       before someone took it.  ⛔ It is time in which
	 *                       nobody works and the frame ages: it is not
	 *                       work to optimise, it is **waiting**, and it is the only
	 *                       item of the span that drops if the loop gets shorter;
	 *      `measure_us`      the pass of `measure_pixels()` — ⛔ DIAGNOSTIC
	 *                       work, not product work: it reads every pixel of the
	 *                       frame on the caller's thread.
	 *
	 * ⚠ `in_slot_us` and `measure_us` are filled in `capture_take()`; the
	 *   other two in the real-time callback.  ⛔ A frame delivered
	 *   to `on_frame` (the copy-less road) does NOT carry them: there is
	 *   no slot and no copy there. */
	uint64_t arrival_us;
	uint64_t copy_us;
	uint64_t alloc_us;
	uint64_t in_slot_us;
	uint64_t measure_us;
} CaptureStopped;

/*
 * ⛔ ZERO AND FAILURE ARE TWO DIFFERENT THINGS, and here they are four.
 *    (`CODER.md` §3.10, `REVIEWER.md` §1 point 4.)
 */
typedef enum
{
	CAPTURE_TAKE_DONE = 0,
	/* ⭐ LEGITIMATE zero: the stream was active for the whole wait and nothing
	 *    arrived.  On Mutter it is the still desktop, and it is a result. */
	CAPTURE_TAKE_ZERO,
	/* ⛔ The stream was never active, or it dropped: there is no number
	 *    to read, and no zero to write in a table. */
	CAPTURE_TAKE_FAULT,
	/* ⛔ Card road: the buffer type is DECLARED, but the pixels are not
	 *    here.  It is not a fault and it is not a zero.
	 *
	 * ⭐⭐ AND SINCE 22 AUGUST 2026 THIS IS **A DELIVERED FRAME**, not a
	 *     nothing-done: inside `CaptureStopped` are `fd`, `offset`,
	 *     `stride`, `modifier` and `format_drm`, and the `pw_buffer` is
	 *     HELD until `capture_stopped_free()`.  ⇒ The caller treats it
	 *     like `DONE` **switching read road**, and does not throw it away.
	 * ⚠ And it remained a separate outcome instead of becoming `DONE` precisely
	 *   because the read road IS different: a caller that does not know about the
	 *   card must trip here, not read a NULL `pixel`. */
	CAPTURE_TAKE_PIXEL_ELSEWHERE
} CaptureTake;

/* ------------------------------------------------------------------ *
 *  The calls
 * ------------------------------------------------------------------ */

/*
 * Starts reading from the given node, requesting size, colour and road.
 *
 * The size is declared because a VIRTUAL MONITOR is being captured: there
 * is no screen to deduce it from, and it is the consumer who says how big
 * it wants it.  ⛔ And it is declared as a FIXED rectangle, not as a range: an
 * open range would let Mutter choose, and it chooses 1280×720.
 *
 * `on_frame` can be NULL: then frames are only counted, and
 * are taken with `capture_take`.
 *
 * ⛔ It fails — declaring it — if the compositor refuses the requested format.
 *    It is the only point where a refusal is seen at once instead of becoming a
 *    black screen much later.
 */
/*
 * ⭐ 6 Oct 2026 — the EXTRA modifiers of the card road (Mutter and KWin).
 * `[M]` NVIDIA + GNOME 50: the offer proposed LINEAR and "you decide" (INVALID);
 * Mutter agreed on INVALID, could not allocate it, dropped it — and
 * the intersection stayed empty ("no more input formats"): BLACK session.
 * ⇒ Whoever knows the card refuses linear (figlio.c) gives here the modifiers
 *   the encoder imports, and the offer puts them between LINEAR and INVALID.
 * ⛔ Only there: where linear succeeds (Intel, Radeon) the offer stays the one
 *    of always — with more modifiers Mutter would pick a tiling of its own.
 */
void capture_modifiers_card(const uint64_t *modifiers, int how_many);

Capture *capture_start(uint32_t node, uint32_t width_px, uint32_t height_px,
                       uint32_t frames_per_second, CaptureRoute route, CaptureColor color,
                       CaptureFrame on_frame, CaptureEnd su_fine, gpointer data_v,
                       GError **mistake);

/*
 * ⭐⭐ PHASE 13 — THE SECOND SOURCE: wlroots, that is XFCE and LXQt.
 *
 * ⛔⛔ AND IT IS NOT A SECOND `capture_start` WITH ONE MORE PARAMETER: it is the other
 *     DIRECTION.  From PipeWire frames **arrive**; from `zwlr_screencopy` they are
 *     **asked for**, one by one.  Everything downstream of this door —
 *     `capture_take`, `capture_delivery`, the counts — does not see the
 *     difference, and that is exactly the point: `figlio.c` uses this interface
 *     in **thirty-five places**, and redoing them two-way would mean putting
 *     GNOME and KDE at risk to needs the new desktop.
 *
 * ⭐ The form has a precedent in the house, and it is copied from there: the **clipboard** has
 *   two constructors (`clipboard_open()` and `clipboard_open_kde()`) and the public
 *   functions hand over at the top.  Same here.
 *
 * ⚠ Two things do NOT map onto the other direction, and they are not faked:
 *   · **the cursor**: screencopy has no channel for the pointer shape.
 *     The pointer is INSIDE the image, and whoever registers receives a line that
 *     says so instead of a silence;
 *   · **resizing**: here one does not renegotiate a stream, one changes the
 *     size of the **output** — another protocol, and another increment.
 *
 * ⛔ `node` is absent because it does not exist: on this family there is no PipeWire
 *    node anywhere.
 */
Capture *capture_start_wlr(uint32_t width_px, uint32_t height_px,
                           uint32_t frames_per_second, CaptureRoute route,
                           CaptureColor color, GError **mistake);

/* The name of the output being watched, or NULL if this source has none
 * to tell (on PipeWire the name is known by the producer, not by us). */
const char *capture_output_name(Capture *capture_v);

/* ------------------------------------------------------------------ *
 *  ⭐⭐ THE HOT SIZE CHANGE — `DECISIONI.md` §5.0-sexies
 * ------------------------------------------------------------------ */

/*
 * The outcome of the REQUEST, which ⛔ is not the outcome of the change.
 *
 * ⛔⭐ "THE TRUTH IS TOLD BY THE FRAME, NOT BY THE OUTCOME OF THE REQUEST" — the
 *     form rule stolen from neatvnc, `DECISIONI.md` §5.0-sexies.  `[M]` 14
 *     August 2026: asking labwc for the size the output ALREADY HAS answers
 *     "succeeded" and sends no event; an old serial answers
 *     "cancelled" and does nothing.  ⛔ `wayvnc` treats *succeeded*, *failed* and
 *     *cancelled* in the same branch — not to be copied.
 *
 * ⇒ Here we only say whether the REQUEST left.  That the compositor
 *   obeyed will be told by the negotiated format (`capture_delivery`) and, even
 *   before, by the first frame at the new size.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ AND "LEFT" INCLUDES "AND MAY HAVE KILLED THE STREAM" — `[M]` 22 August
 *      2026, bench `banchi/06-b5-esiti-cattura.c` case 2, PipeWire 1.4.2
 *
 * Asking for a size the producer cannot handle, `capture_resize()`
 * returns `CHIESTA` and **two milliseconds later** the stream goes to
 * `paused → error — no more input formats`: the failed negotiation does not leave the
 * stream "stuck at the old size", it **kills** it.
 *
 * ⭐ AND NO NEW OUTCOME IS NEEDED TO KNOW IT, because the road is already there and it is
 *    the one the caller walks anyway: `capture_take()` looks at the
 *    state **before** waiting, so it returns `CAPTURE_TAKE_FAULT` **without
 *    spending the wait**, and the `GError` names the state and the producer's
 *    fault.  `[M]` with the child's loop (`MOTION_WAIT_S 0.008`) the
 *    fault arrives at **8.1 ms**, in **one** single turn and with **zero** ZEROs in
 *    between — that is one turn of the loop, not a timeout.
 *
 * ⛔ A "DEAD" outcome returned from here would instead be **green by
 *    construction**: death arrives 2 ms AFTER the return, so reading it
 *    at once would mean reading it before it happens, and half the time it
 *    would say "alive".
 *
 * ⚠ `[?]` And this scene, on the real product, is not measured: `[M]`
 *   (§5.0-sexies) Mutter granted 30 requests out of 30 from 1x1 to 7680x4320, and
 *   `rcp_size_allowed()` cut exactly at 7680x4320 (since 1 October 2026 it
 *   cuts at 4096x2304).  ⇒ Here we declare what
 *   happens IF it happens, not how often it happens.
 */
typedef enum
{
	CAPTURE_RECANVAS_REQUESTED = 0, /* the request left: wait for the frame */
	/* ⭐ The requested size is already the one in force: NO renegotiation.
	 * ⛔ The guard is mandatory — `STUDI.md` §kde §8.2-bis: without it,
	 *    "the renegotiation bites its own tail". */
	CAPTURE_RECANVAS_UNCHANGED,
	CAPTURE_RECANVAS_FAULT /* no stream, dead stream, or empty size */
} CaptureRecanvas;

/*
 * Asks the producer for a NEW size on the ALREADY OPEN stream.
 *
 * ⛔ It does NOT redo the session and does not touch the virtual monitor: it redoes the format
 *    offer and calls `pw_stream_update_params()`, which is the way
 *    gnome-remote-desktop resizes (`F4-IN-2`) and is what the bench
 *    `banchi/04-in8-misura.c` measured on 14 August 2026:
 *
 *      Mutter  `[M]` first new frame at **41.6 ms**, no black, session
 *              and EIS intact; **20 resizes in 2 s, 20 exact**
 *      labwc   `[M]` **5.1 ms**, **0 frames lost out of 25**
 *      KWin    ⛔ only on `master` — the fallback of `DECISIONI.md` §5.0-bis applies
 *
 * ⭐⭐ AND THERE IS A SECOND EFFECT, MEASURED, NOT VISIBLE FROM THE NAME: **restarting
 *     the stream makes a frame arrive**.  `[M]` 14 August 2026, log
 *     of 21:32:55: between login and the first frame **4.4
 *     seconds** of keyframe requests every 200 ms and **659 "empty waits"** went by,
 *     because on Wayland the compositor delivers only when the scene changes and
 *     a freshly started desktop is still.  ⛔ Xpra solves it with
 *     `buffer_refresh` ("repaint now") and we do not need it: here the lever is
 *     this one, and the cure of the delay is a side effect of the cure of the
 *     bands.
 *
 * ⚠ It does NOT wait: it returns at once.  Waiting here would stop the child's loop,
 *   which is the only one it has (`CODER.md` §4.4).
 *
 * ⛔ AND THE ALLOWED SIZE IS NOT CHECKED HERE: the rule ("200..8192, and
 *    both EVEN") lives in `rcp_size_allowed()` and is applied by whoever reads
 *    `FIT_CANVAS` from the wire — see the box at the bottom of this file.  Here only
 *    ZERO is refused, which is a different fact: an empty size is not
 *    "out of bounds", it is a request with no content.
 */
CaptureRecanvas capture_resize(Capture *capture_v, uint32_t width_px, uint32_t height_px);

/*
 * ⭐⭐ "DELIVER ME A FRAME NOW" — and on Wayland it cannot be asked.
 *
 * ⛔ THE FACT, measured: a Wayland compositor delivers a frame **only
 *    when something changes** (`cattura.h`, rule 3), and a freshly started
 *    desktop is still.  `[M]` 14 August 2026, server log: between login and
 *    the first frame **4.4 seconds** went by, with a keyframe
 *    request every 200 ms and **659 "empty waits"** — and in those 4.4 seconds
 *    the user looks at a white page.
 *
 * ⛔ Xpra solves it with `buffer_refresh` ("repaint now") and we do not
 *    need it: on Wayland a compositor cannot be ordered to repaint.
 * ⭐ But the lever exists and it is the same as resizing: **restarting the stream
 *    makes a buffer arrive**, and that is precisely what
 *    `pw_stream_update_params()` IS.  Here the same parameters are redone, with
 *    the same size: nothing changes, and the frame arrives.
 *
 * ⚠ `[?]` And the mark is this, not `[M]`: that the renegotiation delivers a
 *   buffer **on a still scene** is deduced from the mechanism (the stream restarts,
 *   and restarting means reallocating the buffers and repainting the first), not
 *   measured.  The proof is a session in which the time between login and the first
 *   frame drops below one second, and it must be done on the test machine.
 *
 * ⛔ The caller must PUT A FLOOR UNDER IT: calling it at every turn would
 *    renegotiate sixty times a second — and every renegotiation costs the
 *    frame one is trying to get.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔⛔ AND THE HIDDEN PRICE, which the name does not let one suspect — `[M]` 21
 *       August 2026, bench `banchi/06-b33-risveglio.*`
 *
 * **THIS CALL DESTROYS AND RECREATES THE INPUT DEVICES.**  It is not a
 * small side effect: it is the **second door** of the *dying click*
 * (`fasi/06-la-tela-e-la-vista.md` §4.6 and §7.1).
 *
 * `[M]` Three wake-ups on a still scene, **zero** `FIT_CANVAS`: three pointer
 * replacements (delta 1, 1, 1, read from `input_count()`).
 *
 * `[R]` The chain, all inside Mutter 48.7:
 *   `pw_stream_update_params()` → the producer renegotiates →
 *   `meta_screen_cast_virtual_stream_src_enable()`
 *   (`meta-screen-cast-virtual-stream-src.c:283`) calls
 *   `meta_eis_viewport_notify_changed()` → `viewports-changed` →
 *   `update_viewports()` → `remove_viewport_devices()`, which ⛔ **does not go through
 *   `drop_device()`** and therefore releases nothing.
 *
 * ⇒ ⛔⛔ **If a button is pressed when this function starts, the desktop
 *   no longer takes a click for the whole session** — `[M]`, and it heals only
 *   by dropping the EIS channel.  ⚠ The moment at which `figlio.c:6365`
 *   calls it is *"the scene is still and a keyframe is owed"*, that is **exactly
 *   the moment when the user may be holding the mouse down on a still desktop**.
 *
 * ⇒ The caller must **check whether anything is pressed** before
 *   waking up.  ⛔ The cure of `figlio.c:3964` — releasing before
 *   `capture_resize()` — **does not cover this road**.
 *
 * `FALSE` = it could not be asked (no stream, or stream not active).
 */
gboolean capture_wake(Capture *capture_v);

/* The size REQUESTED from the producer now — ⛔ not the granted one: that is in
 * `CaptureDelivery.width_px/height_px` and holds only after negotiation.  ⚠ The two
 * are compared, and whoever confuses them rewrites the defect that the "requested
 * versus granted" guard exists to see.
 *
 * ⛔⛔ AND THESE TWO ARE **ALL** THAT IS EXPORTED ABOUT DIVERGENCE: there
 *     is no — and none is to be added — `cattura_divergente()`.  The reason is
 *     measured and sits next to the `measure_divergent` field in `cattura.c`: `[M]`
 *     (bench `06-b5` case 4) the only scene that turns it on is **two
 *     chained resizes**, where the value is a **false alarm** that
 *     turns itself off; and `[M]` (case 6) the real divergence is rebuilt from
 *     these two accessors, which also tell "not yet negotiated" apart —
 *     something a `gboolean` could not do (`CODER.md` §3.10). */
void capture_measure_requested(Capture *capture_v, uint32_t *width_px, uint32_t *height_px);

/* The NEGOTIATED size, that is the one the pixels really have.  ⛔ `FALSE` = the
 * format has not been negotiated yet, which is NOT "it is 0x0" (`CODER.md` §3.10).
 *
 * ⚠ It serves to answer "I already have the canvas you ask for" without waiting for a
 *   frame that would not arrive: it is the only case in which the request can be
 *   closed without seeing the pixels, because the viewer already has the pixels of that size
 *   in front of them. */
gboolean capture_measure_negotiated(Capture *capture_v, uint32_t *width_px, uint32_t *height_px);

/*
 * Waits for the NEXT frame and delivers a copy of it.
 *
 * ⛔ The copy is made inside the real-time callback — there is no other way,
 *    the pixels live only there — and the MEASUREMENT on the pixels (range, black, uniform) is
 *    made here, on the caller's thread: slowing down the PipeWire loop
 *    would falsify the thing being watched.
 *
 * ⚠ Frames that arrive when nobody is waiting are only counted:
 *   no 8 MB copies that nobody asked for are piled up.
 */
CaptureTake capture_take(Capture *capture_v, double wait_s, CaptureStopped *outside,
                            GError **mistake);

/*
 * Gives the frame back.
 *
 * ⛔⛔ AND ON THE CARD ROAD THIS CALL IS **THE RELEASE**, that is the
 *      cure of `LEZIONI.md` §8: until it is called, the `pw_buffer` is
 *      ours and the producer cannot repaint into it.  ⇒ It is called
 *      **after** the last reader has finished — after the conversion on the GPU,
 *      not after ordering it — and **not before**.
 * ⚠ Calling it twice is harmless (the still frame is zeroed); not calling it at all
 *   takes a buffer away from the producer forever.
 */
void capture_stopped_free(CaptureStopped *stopped);

/* The four facts, when they are known.  FALSE ⇒ the format has not been
 * negotiated yet, and there is nothing to declare (not "it is all zero"). */
gboolean capture_delivery(Capture *capture_v, CaptureDelivery *outside);

/* The counts of the run.  They needs whoever writes a manifest or a log
 * line, and they are separate from the facts on purpose: a count is not a
 * declaration about the format. */
typedef struct
{
	guint64 arrived;
	guint64 full_damage, partial_damage, missing_damage;
	guint64 without_header;
	guint64 cursor_only;   /* buffers marked CORRUPTED: stale pixels  */
	guint64 stride_zero;    /* ⛔ discarded instead of computed        */
	guint64 without_pixel;    /* mapping absent or empty chunk           */
	/* ⛔⭐ The geometry declared by the FORMAT does not fit in the bytes of the CHUNK:
	 *     discarded, because whoever consumes them would read past the copy.  ⚠ It is the
	 *     window between a renegotiation and the new buffers, and before
	 *     `capture_resize()` it could not exist. */
	guint64 inconsistent_geometry;
	/* ⭐ The cursor channel.  ⛔ The first two are TWO and not one, and it is the
	 *    same rule as zero and failure: "the metadata was not there" and
	 *    "the metadata was there" are the two facts that tell an absent
	 *    pointer from a channel without a source (`STUDI.md` §gnome §1.1 point 6). */
	guint64 cursor_absent;
	guint64 cursor_meta_seen;
	guint64 malformed_cursors;
	guint distinct_buffers;
	CaptureBuffer seen_types[4]; /* ⛔ ALL the types seen, not only the last */
	guint how_many_types;
} CaptureCounts;

void capture_counts(Capture *capture_v, CaptureCounts *outside);

/*
 * ⭐⭐ THE CURSOR SEAM — whoever wants the pointer SHAPE registers here.
 *
 * ⛔ This is the ONLY line the cursor channel adds to the capture
 *    interface, and it is here for a precise reason: `cattura.c` reads
 *    PipeWire's raw metadata but **does not know the wire**, and `cursore.h` wants
 *    the recipient at opening time — which happens inside
 *    `capture_start`, that is before anyone can register.
 *
 * ⚠ `when_changes` is called FROM PipeWire's REAL-TIME THREAD, and the
 *   box at the top of this file applies: nothing is waited on in there, and
 *   the image lives only for the duration of the call (`cursore.h`).
 *
 * ⚠ It can be called at any moment, even with capture live: the shapes that
 *   arrive before registration are counted and not sent — ⛔ which is NOT
 *   "they did not arrive".  Whoever registers after the first pointer
 *   movement receives the next shape anyway.
 *
 * ⛔ And the cut at 256, the "hidden" and the "has not changed" are NOT here: they are
 *    in `cursore.c`, which is the place `cursore.h` assigns them.
 */
void capture_cursor(Capture *capture_v, CursorArrived when_changes, void *chi);

/*
 * ⭐ THE POINTER PROBE — only on the wlroots family (labwc), and elsewhere
 *    it does nothing.  The child calls it AFTER every injected pointer
 *    gesture, with the coordinates of its canvas (those given to
 *    `input_pointer`; for a button, the last ones); the shape, if it has changed,
 *    comes back through `when_changes` of `capture_cursor` inside a
 *    later `capture_take`, on the thread of whoever calls it.  The why in
 *    `wlroots.h`.
 */
void capture_probe_pointer(Capture *capture_v, uint32_t x, uint32_t y);

/* Is the stream active NOW?  ⛔ "It WAS active" is not "it still is": a
 * death halfway through a measurement has already produced a table row with five
 * seconds inside under the label of twenty. */
gboolean capture_active(Capture *capture_v);

/* The fault declared by the producer, or NULL. */
const char *capture_fault(Capture *capture_v);

/*
 * ⭐ PHASE 17 — negotiation FAILED: the stream is in error and no
 *    format was ever agreed.  It is the case of "no more input formats"
 *    (`[M]` 29 Sep 2026, 7 VMs out of 7): the CARD road was requested from a
 *    compositor that has no DMA-BUF buffers to offer (no 3D
 *    acceleration: `virtio-vga` without virgl, a server without a card), and the intersection
 *    of the offers is empty.
 *
 * ⛔ It does not look at the TEXT of the fault: it looks at the two facts that produce it.  And
 *    `capture_start()`, if the refusal arrives before it returns, says so with the
 *    code `G_IO_ERROR_NOT_SUPPORTED` instead of `G_IO_ERROR_FAILED`.
 *
 * ⚠ What to do with it is decided by the caller (`figlio.c`, `falls_back_if_refused`):
 *   here we only answer the question.
 */
gboolean capture_format_refused(Capture *capture_v);

/* ⭐ Flips the `cursor_never_hide()` switch on this capture's
 *    cursor: the child asks for it on Plasma, where the theme is invisible. */
void capture_cursor_never_hide(Capture *capture_v, const char *reason_text);

void capture_stop(Capture *capture_v);

/* --- the allowed size: it is NOT here, and the reason must be told ---- *
 *
 * ⛔ The rule ("200..8192, and width and height EVEN") lives in `rcp.h`, as
 *    `rcp_size_allowed()`, and NOT here — even though the reason the ceiling
 *    exists belongs wholly to this level: `[M]` 14 August 2026, beyond **16384**
 *    per side `gnome-shell` dies, and on labwc `32768x32768` kills the
 *    compositor **with zero log lines**.
 *
 * ⚠ It is over there because whoever must apply it is whoever reads `FIT_CANVAS` from the wire,
 *   and `rcp.h` is **deliberately self-sufficient** — it includes only `stdbool`,
 *   `stddef` and `stdint` — so that its twin copy compiles inside
 *   `bsslserver` without the rest of the tree.  ⇒ Putting the rule here
 *   would force `rcp.c` to include this file, that is to break that
 *   property.
 * ⛔ And having it in TWO places would be worse than both: the day one
 *   changes, the server accepts a size the compositor cannot handle, and the
 *   session of whoever hosts us dies silently. */

/* --- the names, so that whoever writes a manifest does not reinvent them --- */
const char *capture_buffer_name(CaptureBuffer buffer);
const char *capture_color_name(uint32_t raw_format);
const char *capture_source_name(CaptureSource source);
const char *capture_range_name(uint32_t raw);
const char *capture_matrix_name(uint32_t raw);
const char *capture_transfer_name(uint32_t raw);
const char *capture_primaries_name(uint32_t raw);
const char *capture_range_measured_name(CaptureRangeMeasured measured);

#endif
