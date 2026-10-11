/*
 * wlroots — the stage of the third family: labwc, and so XFCE and LXQt.
 *
 * ⛔⛔ AND IT IS NOT "kwin.h with another protocol": it is the other DIRECTION.
 *
 *    `mutter.h` and `kwin.h` do the same thing — they ask the compositor for a
 *    stream and receive **the number of a PipeWire node**. From there on the
 *    frames **arrive on their own**, pushed, and `cattura.c` collects them.
 *
 *    On wlroots a PipeWire node does not exist. There is a Wayland protocol,
 *    `zwlr_screencopy_manager_v1`, and for every frame the whole round is made:
 *
 *        capture_output → buffer → copy → ready
 *
 *    ⇒ A frame **is asked for**. The rate is not a property of the
 *      compositor: it is our loop. ⭐ And that is precisely what the
 *      user's decision of 20 September 2026 bought — "we ask for them
 *      ourselves" — together with control over the cursor and the size.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THERE IS NO GATE, and it must be said because it is news.
 *
 * On GNOME capture goes through a portal; on KDE a `.desktop` is needed that
 * declares `X-KDE-Wayland-Interfaces`, and without it the global does not appear.
 * `[M]` 20 September 2026, inside `rete11-xfce`: a bare client sees **47
 * globals** and among them `zwlr_screencopy_manager_v1` **v3**. No file,
 * no dialog, no portal. The only gate is the uid: `/run/user/<uid>`
 * is `drwx------`.
 *
 * ---------------------------------------------------------------------------
 * ⚠ THE PROTOCOL IS DEPRECATED UPSTREAM, and this has been known from day one.
 *
 * The XML carries at its top *«This protocol is deprecated … the
 * ext-image-copy-capture-v1 protocol should be used instead»*. ⛔ But `[M]` 20
 * September 2026 labwc on Debian Trixie **does not expose**
 * `ext_image_copy_capture_manager_v1`: there is nothing to use in its place.
 * ⇒ We write against screencopy, and we write so that the successor can
 *   come in **beside** it — not in its place: the interface of this file names
 *   frames and sizes, not protocol messages.
 *
 * ---------------------------------------------------------------------------
 * ⭐ WHY THIS FILE EXISTS, instead of a branch inside `cattura.c`
 *
 * `cattura.c` is 2,348 lines built on the push direction, and `figlio.c`
 * uses it in **35 places**. ⛔ Redoing them two-way would mean touching in
 * thirty-five places the code GNOME and KDE depend on — that is, putting at
 * risk the protected baseline to needs the new desktop, which is exactly what
 * the phase 13 rule forbids.
 *
 * ⇒ The chosen form has a precedent in the house, and it is copied from there: the **clipboard**
 *   (`src/appunti.c:594-603`) has **two constructors** — `clipboard_open()` and
 *   `clipboard_open_kde()` — and the public functions hand over at the top.
 *   Same here: `capture_start()` stays intact for GNOME and KDE, and this file
 *   gives the source of the other direction.
 *
 * ⚠ And the functions that do NOT map onto the other direction are two, counted:
 *   · **the cursor**: screencopy has no channel for the pointer shape —
 *     there is only `overlay_cursor`, a yes/no that draws it INSIDE the image.
 *     ⇒ Whoever registers is accepted and never called back, and the line
 *       says so: "on this desktop the pointer is in the pixels".
 *   · **resizing**: here one does not renegotiate a stream, one changes the
 *     size of the **output** (`zwlr_output_manager_v1`, `[M]` v4 on labwc).
 *     ⇒ It is not in this file: it is the increment that brings the size.
 */
#pragma once

#include <glib.h>
#include <stdbool.h>
#include <stdint.h>

typedef struct WlrStage WlrStage;

/*
 * Connects to the user's compositor and prepares the capture of the output.
 *
 * ⚠ `WAYLAND_DISPLAY` if present; otherwise `wayland-0`…`wayland-9` are tried in
 *   `XDG_RUNTIME_DIR` — the same search `kwin_display_open()` already does, and
 *   for the same reason: the child does not inherit the variable from the compositor
 *   it has just started.
 *
 * ⛔ It does NOT capture anything yet: here it is only established that the compositor is there,
 *    that it announces the manager, and WHICH output will be watched. An `do_open` that
 *    captured would make "the compositor is not there" and "the first
 *    frame does not arrive" indistinguishable, and they are two different diagnoses.
 *
 * NULL with `mistake` set.
 */
WlrStage *wlr_open(GError **mistake);

/* ⭐ The same, on a NAMED display (a socket name or an absolute path), with no
 *    search: it is the road of the labwc that hosts KWin (`kwin.h`, the nested
 *    KWin), which lives in a folder of its own and must never be mistaken for
 *    the session's compositor.  NULL = the search of `wlr_open()`. */
WlrStage *wlr_open_on(const char *display, GError **mistake);

/*
 * ⛔ PHASE 19 — SLABS AT THE MAXIMUM CANVAS, only if encoding is Vulkan.
 *    True ⇒ every GBM slab is born 4096x2304 and on a size change only the
 *    `wl_buffer` is redone (the BO does not die while the stage lives).  False (the
 *    default) ⇒ slabs of the right size, redone on change.  The why
 *    is in the box of `WLR_SLAB_W` in `wlroots.c`.  ⚠ Per PROCESS, not
 *    per stage: the encoding route is one per child, and it is stated before the
 *    first stage.
 */
void wlr_slabs_at_max_canvas(bool yes);

/* The size the output has NOW — ⛔ not the one we would like.
 *
 * `[M]` 20 September 2026: a labwc headless output is born **1280×720**
 * hard-wired, and no protocol creates one of the wanted size. ⇒ Whoever asks for
 * 1920×1080 must know it, and this function is the place where they find out. */
void wlr_measure(const WlrStage *stage, uint32_t *width, uint32_t *height);

/* The name of the output, for log lines (`HEADLESS-1` and the like). */
const char *wlr_output_name(const WlrStage *stage);

/*
 * ⭐ ONE FRAME, ASKED FOR AND WAITED ON — the whole round of the pull direction.
 *
 * ⛔ And the outcomes are THREE, not two, for the same reason as the whole
 *    project: "the compositor said no" and "I could not ask" are not
 *    the same thing, and lumping them together makes us blame the compositor for a
 *    fault of ours.
 */
typedef enum {
	WLR_FRAME_TAKEN = 0,  /* the pixels are there                         */
	WLR_FRAME_FAILED,    /* the compositor sent `failed`                 */
	WLR_FRAME_EXPIRED,    /* the wait is over: I could not look           */
	WLR_FRAME_BROKEN       /* the line to the compositor has dropped       */
} WlrOutcome;

typedef struct {
	uint32_t width, height, stride;
	/* ⚠ Always a DRM fourcc, but from two different numberings: in memory it is the
	 *   `wl_shm` format TRANSLATED (`[M]` labwc: XB24, that is R G B x); on the
	 *   card it is the one from the `linux_dmabuf` event, already DRM (`[M]` XR24, that is
	 *   B G R x).  ⛔ Whoever reads the channel order reads it from here, per
	 *   frame: the two roads do not give the same. */
	uint32_t fmt;
	const uint8_t *pixel; /* ⛔ alive until the next frame is asked for     */
	gsize byte;
	/* ⭐ The two the pull direction gives for free, and that on push are estimated:
	 *    the instant at which the compositor says presentation happened. */
	uint64_t seconds;
	uint32_t nanoseconds;
	/* ⚠ `y_inverted`: the `flags` event may say that the rows are to be read from the
	 *   bottom. ⛔ Ignoring it gives an upside-down image, which is a fault that
	 *   looks like an encoder fault. */
	bool y_inverted;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ THE CARD ROAD — see the box at the top of `wlroots.c`.
	 *
	 * ⛔ When `on_card` is true `pixel` is **NULL**: the image is in a
	 *    DMA-BUF of ours (a "slab"), and the pixels are reached through `fd`.  It is the
	 *    same rule as `CaptureStopped`: whoever reads looks at `on_card`
	 *    BEFORE `pixel`.
	 * ⛔⛔ AND THE SLAB IS HELD BY WHOEVER RECEIVED THE FRAME until they
	 *      give it back with `wlr_release()`.  Until then the compositor does NOT
	 *      write into it again — no `copy` names it.  ⚠ Whoever does not give it back
	 *      runs out of slabs, and the next frame stops SAYING SO: a slab
	 *      in hand is never recycled (`LEZIONI.md` §8).
	 * ------------------------------------------------------------------ */
	bool on_card;
	int fd;                /* ⛔ owned by `wlroots.c`: do not close         */
	uint32_t offset;
	uint64_t modifier; /* `[R]` always LINEAR: see `wlroots.c`           */
	/* ⛔ It changes every time a slab is born or dies: descriptor numbers
	 *    are recycled, and whoever caches the import of an
	 *    `fd` (the encoder) must throw it away — `cattura.h`, `generation`. */
	uint64_t generation;
	void *slab;          /* ⛔ opaque: passed to `wlr_release()` and nothing else */
	/* ⭐ How long the compositor's GPU was waited on after `ready`, and whether
	 *    the wait was REAL (the fence extracted from the DMA-BUF) or it could
	 *    not be done and implicit synchronisation is relied upon. */
	uint64_t gpu_wait_us;
	bool explicit_wait;
} WlrFrame;

/*
 * Asks for a frame and waits at most `wait_s`.
 *
 * ⚠ The delivered pixels live until the next call: whoever wants to
 *   keep them copies them. ⛔ It is the same rule as `cattura.h`, and it is here because
 *   it is the rule that gets forgotten first.
 */
WlrOutcome wlr_frame(WlrStage *stage, double wait_s, WlrFrame *report,
                        GError **mistake);

/*
 * ⭐⭐ TURNS ON THE CARD ROAD — and says no, in writing, if it cannot.
 *
 * ⛔ It is deliberately not an option of `wlr_open()`: "the compositor is there" and "the
 *    card is there" are two diagnoses, and an `do_open` that failed on the second
 *    would also take away the first road, which works.
 *
 * True: from here every frame is tried on the card, and each one
 * says in `on_card` where it REALLY ended up.  False with `mistake` set:
 * the road stays memory, and the caller MUST write it in the log.
 */
bool wlr_ask_card(WlrStage *stage, GError **mistake);

/* The road in force NOW.  ⚠ It can become false on its own: three `failed`
 * in a row on the card turn it off, and `wlroots.c` writes so. */
bool wlr_on_card(const WlrStage *stage);

/* ⛔ Gives back the slab of a card frame: from here the compositor can
 *    write into it again.  Call it ONLY when whoever was reading has FINISHED (for the
 *    encoder: when `codificatore_comprimi_scheda()` has returned).
 * ⚠ `slab` NULL does nothing: it is the memory frame. */
void wlr_release(WlrStage *stage, void *slab);

/* ⚠ To be put around a CPU read inside the slab (`mmap`):
 *   `DMA_BUF_IOCTL_SYNC`, so that the bytes seen by the CPU are those written
 *   by the GPU.  Only one place uses it — the first frame looked at. */
void wlr_cpu_read(int fd, bool start);

/*
 * ⭐⭐ THE OUTPUT SIZE — and on this family it can be done, unlike KDE.
 *
 * ⛔⛔ AND "THE TRUTH IS TOLD BY THE FRAME, NOT BY THE OUTCOME OF THE REQUEST"
 *     (`DECISIONI.md` §5.0-sexies, the rule stolen from neatvnc).
 *
 *     `[M]` 14 August 2026: asking labwc for the size the output **already has**
 *     answers "succeeded" and sends no event; an old serial
 *     answers "cancelled" and does nothing. ⛔ `wayvnc` treats *succeeded*,
 *     *failed* and *cancelled* in the same branch — not to be copied.
 *
 * ⇒ This function only says **whether the request was accepted**. That
 *   the output changed will be told by `wlr_measure()` after the following frame,
 *   and it is the only witness that counts.
 */
typedef enum {
	WLR_SIZE_REQUESTED = 0, /* the request left and the compositor said yes          */
	WLR_SIZE_UNCHANGED,    /* the output already has that size: nothing to ask     */
	WLR_SIZE_REFUSED,   /* `failed`: the compositor said no                     */
	WLR_SIZE_CANCELLED,   /* `cancelled`: the serial was old — can be retried     */
	WLR_SIZE_IMPOSSIBLE  /* the compositor does not announce the output manager  */
} WlrSizeOutcome;

WlrSizeOutcome wlr_ask_size(WlrStage *stage, uint32_t width, uint32_t height,
                                 double wait_s, GError **mistake);

/* The same with the output's refresh, in mHz (0 = «you choose», which is what
 * `wlr_ask_size()` sends).  Only the labwc that hosts KWin asks for one
 * (`kwin.c`, HOST_MHZ). */
WlrSizeOutcome wlr_ask_size_hz(WlrStage *stage, uint32_t width, uint32_t height,
                                    int32_t millihertz, double wait_s, GError **mistake);

/* How many frames were asked for, taken, failed. For log lines
 * and for the manifest: ⛔ a count is not a declaration. */
typedef struct {
	guint64 requested, grabbed, failed, expired;
	/* ⛔ The TWO roads counted separately: a number without its road is a
	 *    number that will lie.  `grabbed == on_card + in_mem`. */
	guint64 on_card, in_mem;
} WlrCounts;

void wlr_counts(const WlrStage *stage, WlrCounts *report);

/*
 * ⭐ The NEXT frame will be whole, even if the screen has not changed.
 *
 * Usually frames are asked for with damage (the compositor answers only
 * when something changes).  ⚠ But a keyframe is sometimes needed at once on a still
 * desktop: it is the wake-up of `cattura.h`, and on this family it is this line.
 */
void wlr_force_full(WlrStage *stage);

/*
 * ⭐⭐ THE POINTER PROBE — 24 September 2026, the true shape on labwc.
 *
 * The why and the three rules are in `wlroots.c`, above `wlr_probe_pointer`.
 * In short: with the encoded theme (`forma.h`) the compositor draws under the
 * hotspot a pixel of the shape's colour; the probe reads it with a 3x3
 * `capture_output_region`, and the dictionary turns it into the name.
 *
 *   wlr_probe_pointer()  after EVERY injected pointer gesture: `x`,`y`
 *                          in the `l`x`a` canvas (the same as
 *                          `wlr_input_absolute`).  Coalescing, ONE in flight.
 *   wlr_probe_shape()      the shape index (`forma.h`) if it has CHANGED
 *                          since last time, otherwise -1.  ⛔ To be called at
 *                          every turn of the loop (`capture_take` calls it):
 *                          it is also the place the "trailing" probe starts from.
 *
 * ⛔ Same thread as `wlr_frame`: it is its pump that carries the events.
 * ⛔ The main stream does NOT change: the probe has its own frame and its own
 *    buffer, and touches neither `force_full` nor the damage.
 */
void wlr_probe_pointer(WlrStage *stage, uint32_t x, uint32_t y, uint32_t l, uint32_t a);
int wlr_probe_shape(WlrStage *stage);

typedef struct {
	guint64 asked;   /* pointer gestures arrived                            */
	guint64 launched;  /* probes really launched (⚠ < asked: coalescing)    */
	guint64 returned, failures;
	guint64 of_queue;   /* the "still hand" probes (rule 3)                    */
	guint64 changes;     /* new shapes recognised                               */
	guint64 ignote;    /* returned without a colour of ours under the pointer */
	guint64 from_neighbors; /* recognised on a neighbour and not on the centre    */
} WlrProbeCounts;

void wlr_probe_counts(const WlrStage *stage, WlrProbeCounts *report);

void wlr_close(WlrStage *stage);
