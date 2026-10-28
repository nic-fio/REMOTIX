/*
 * wlroots.c — capture on demand.  The reason is in `wlroots.h`.
 *
 * ⛔⛔ THE FIRST DRAFT TOOK THE PIXELS FROM MEMORY (`wl_shm`), NOT FROM THE
 *     CARD — and it was a declared choice: first prove that the pixels
 *     arrive and are the right ones, then remove the copy.  ⭐ Since 21
 *     Sep 2026 the card is there (the second box below), and memory stays
 *     as the default route and as an ALWAYS DECLARED FALLBACK.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ REWRITTEN ON 21 SEP 2026, after the ADVERSARIAL REVIEWER.
 *
 * The first draft had seven defects, and no test said so: C1 was green and
 * 530 frames went through.  A reading sent on purpose to refute it found
 * them.  The ones that changed the shape of the file, and why:
 *
 *   1. ⛔ THE FORMAT.  The `buffer` event arrives ONLY ONCE per frame, and
 *      carries the `wl_shm` numbering (ARGB8888 = 0, XRGB8888 = 1, the rest
 *      is the fourcc).  The first draft believed it could CHOOSE among
 *      several offered formats, and compared against the DRM fourccs: the
 *      branch could never fire, and labwc gives only `XBGR8888` — that is
 *      `R G B x`.  ⇒ Here we TRANSLATE (wl_shm → DRM) and deliver; `child.c`
 *      reads the order and tells the encoder (`CODIFICATORE_PIXEL_RGBX`).
 *   2. ⛔ THE COPY THROWN AWAY AT EVERY TIMEOUT.  The child's loop waits 8 ms
 *      (`MOTION_WAIT_S`) and the whole round costs 9-15: almost every
 *      call timed out AFTER `copy`, threw away the frame already in progress
 *      and reallocated 8 MB.  ⇒ Now the frame is PENDING: if the wait ends,
 *      the request stays alive and the next call resumes it.
 *   3. ⛔ THREE `wl_display_roundtrip` WITHOUT A CEILING: a stuck compositor
 *      stopped the child forever.  ⇒ `cur_round()`, with a deadline.
 *   4. ⛔ `failed` AND `cancelled` IN THE SAME BRANCH — the exact mistake that
 *      `DECISIONS.md` §5.0-sexies blames on wayvnc.  ⇒ Three separate outcomes.
 *   5. the output's head was found only if the names arrived in a precise
 *      order ⇒ all are kept, and the choice is made at request time;
 *   6. the configuration enabled a single head: with two outputs the
 *      protocol dies (`unconfigured_head`) ⇒ the others are reconfirmed as
 *      they are;
 *   7. the object leaks in `wlr_close`.
 *
 * ===========================================================================
 * ⭐⭐ THE CARD ROUTE — 21 Sep 2026, behind `CAPTURE_ROUTE_CARD`
 * ===========================================================================
 *
 * ⚠ Written first on the old draft (commit `d5d7129`) and CARRIED by hand
 *   onto this one: none of the seven defects above comes back in with it.
 *   The card speaks ITS OWN numbering (defect 1), lives inside the pending
 *   frame (defect 2) and never waits without a ceiling (defect 3).
 *
 * ⛔ Memory stays: it is the FALLBACK, and a DECLARED fallback.  If the card
 *    is asked for and memory arrives, the log says so with the reason, and
 *    every frame carries `on_card` — it is never deduced from the route
 *    asked for.
 *
 * ---------------------------------------------------------------------------
 * THE TWO ROUTES THERE WERE, AND WHY THE FIRST IS TAKEN
 *
 *   `[M]` labwc announces both `zwlr_screencopy_manager_v1` v3 (with the
 *   `linux_dmabuf` event) and `zwlr_export_dmabuf_manager_v1` v1.
 *
 *   A · `copy` into a DMA-BUF OF OURS
 *     who owns the buffer      ⭐ WE DO: we allocate it, keep it until the
 *                              encoder has finished, name it in a `copy`
 *                              only when it is free
 *     what it costs            a blit on the GPU (`wlr_screencopy_v1.c`
 *                              0.18.2, `frame_dma_copy`): one copy, but on
 *                              the card — no `glReadPixels`, which BLOCKS
 *                              the compositor's loop (`STUDIES.md` §xfce §4.4)
 *     new dependencies         ⚠ `gbm` to allocate, and the `linux-dmabuf` XML
 *
 *   B · `zwlr_export_dmabuf_manager_v1`
 *     who owns the buffer      ⛔ THE COMPOSITOR: the buffers of its chain,
 *                              reused every round, and `TRANSIENT` ALWAYS
 *                              (`wlr_export_dmabuf_v1.c:75`): the GNOME R29
 *                              trap in pure form, with no lever at all
 *
 *   ⇒ ⭐ A.  The cost of one dependency (`gbm`, which is already present at
 *     run time wherever labwc runs) buys a buffer that is OURS.
 *
 * ---------------------------------------------------------------------------
 * THE SLABS — the card's buffer, and the three rules
 *
 *   A «slab» is a `gbm` buffer on the compositor's `renderD*` node, its
 *   DMA-BUF `fd`, and the `wl_buffer` that names it.  Three states: FREE, IN
 *   FLIGHT (named in the `copy` of the frame in progress), IN HAND (delivered
 *   downstream, until it comes back with `wlr_release()`).
 *
 *   1. ⛔ ONLY A FREE SLAB IS NAMED IN A `copy`.  A slab in hand becomes free
 *      again only with `wlr_release()` — in the product from
 *      `capture_stopped_free()`, which the loop calls AFTER
 *      `codificatore_comprimi_scheda()`, where `vaSyncSurface` says the GPU
 *      has FINISHED reading.  ⇒ «labwc copies into it again while the
 *      encoder reads it» is not avoided with a timing: it is impossible by
 *      construction.  If they are all in hand the frame stops, SAYING SO;
 *      none is recycled (`LESSONS.md` §8).
 *   2. ⛔ A SLAB ABANDONED AFTER `copy` WITHOUT DELIVERY (dropped wire,
 *      `failed`) IS DIRTY: it is thrown away and another one is made.
 *   3. ⛔ EVERY SLAB THAT IS BORN OR DIES CHANGES THE GENERATION.  The
 *      encoder caches the import by `fd`, and descriptor numbers get
 *      recycled: a new slab with the number of a dead one would give VA-API
 *      the old surface — an earlier image, with no error.
 *
 *   ⚠ Three and not one: the loop keeps one in hand and one in flight; the
 *     third is cheap insurance (8 MB at 1080p).
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ THE SLAB AND THE PENDING FRAME — the reviewer's questions
 *
 *   · «Does the wait time out while the copy onto the slab is in flight, and
 *     the next round resume another one?»  ⇒ No: the next round resumes THE
 *     SAME frame (`stage->frame` is alive) with THE SAME slab
 *     (`round_slab` is kept).  A new `capture_output` starts only
 *     when `frame` is NULL, and `frame` goes back to NULL only when its slab
 *     is delivered or thrown away.  ⛔ And on timeout the slab does NOT get
 *     dirty: the old draft threw it away, and that was defect 2 in card form.
 *   · «A slab returned twice?»  ⇒ `wlr_release()` acts only on a slab IN HAND
 *     and brings it to FREE: a second call finds it FREE (or IN FLIGHT, if
 *     it has left again in the meantime) and does nothing; and
 *     `capture_stopped_free()` zeroes the hold after returning it.  ⚠ `[R]`
 *     The only uncovered case is a COPY of the hold kept by someone after
 *     the release: in `child.c` the hold is a local variable passed by
 *     address, and nobody copies it.
 *   · «Does the encoder read a slab while labwc copies into it again?»  ⇒
 *     Rule 1: a slab in hand is never named in a `copy`.
 *   · And the fence that does not fire in time after `ready`: the frame stays
 *     PENDING with `ready` already true, the slab stays IN FLIGHT, and the
 *     next call waits again on the same fence — no delivery of a half blit,
 *     no slab lost.
 *
 * ---------------------------------------------------------------------------
 * THE MODIFIER: LINEAR, and it is declared
 *
 *   ⛔ The `linux_dmabuf` event carries format and size, NOT the modifiers.
 *      ⇒ LINEAR: everyone can write and read it, even across two cards.
 *   ⚠ `[?]` The price: linear blit and reads are a little slower than in
 *     tiling.  Measure before buying anything else.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ SYNCHRONISATION, WITHOUT EXPLICIT FENCES — when can we read?
 *
 *   `[R]` wlroots 0.18.2, `render/gles2/pass.c`: the blit ends with
 *   `glFlush()`, not `glFinish()`, and right after `ready` goes out.  ⇒ When
 *   `ready` arrives the blit is SUBMITTED to the GPU, not FINISHED.  `[M]`
 *   `wp_linux_drm_syncobj_manager_v1` is not there: no fence is given to us.
 *   ⇒ ⭐ After `ready` we EXTRACT it from the DMA-BUF (`DMA_BUF_IOCTL_EXPORT_SYNC_FILE`
 *     with `DMA_BUF_SYNC_READ`) and wait with `poll()` for it to fire.
 *   ⚠ It costs: it is `gpu_wait_us`, and it sits INSIDE the frame time.
 *   ⛔ If the ioctl is missing (kernel < 5.20) it is said once: from then on
 *      we rely on implicit synchronisation alone, and the line names it.
 *
 * ---------------------------------------------------------------------------
 * ⚠ THE TWO FORMAT NUMBERINGS — they do not mix (defect 1)
 *
 *   The `buffer` event speaks `wl_shm.format` (0 and 1 special) → `f_shm`, and
 *   is translated with `shm_a_drm()` ONLY for whoever is downstream.  The
 *   `linux_dmabuf` event speaks the true DRM fourcc → `o_card_format`, and
 *   does NOT go through `shm_a_drm()`.  The slab is allocated EXACTLY in the
 *   format and size of that event: `[R]` wlroots, a different format or size
 *   is `invalid buffer` — a PROTOCOL ERROR, and the connection dies.
 *   ⭐ `[M]` labwc on the card gives `XRGB8888` (B G R x in memory): the order
 *     the encoder already reads.  If another one arrived, the card is
 *     skipped for that frame, saying so.
 */
#include "wlroots.h"
#include "card_pick.h"
#include "vulkanvideo.h"

#include "shape.h"
#include "log.h"

#include "linux-dmabuf-unstable-v1-client-protocol.h"
#include "wlr-output-management-unstable-v1-client-protocol.h"
#include "wlr-screencopy-unstable-v1-client-protocol.h"

#include <drm_fourcc.h>
#include <errno.h>
#include <fcntl.h>
#include <gbm.h>
#include <gio/gio.h>
#include <linux/dma-buf.h>
#include <poll.h>
#include <string.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/stat.h>
#include <sys/sysmacros.h>
#include <unistd.h>
#include <wayland-client.h>

/* ⚠ The same area as `capture.c` and `kwin.c`: whoever reads the log looks for
 *   the pixels under a single word, not under the name of the module that took them. */
#define AREA "capture"

#define FOURCC(a, b, c, d) ((uint32_t)(a) | ((uint32_t)(b) << 8) | ((uint32_t)(c) << 16) | \
                            ((uint32_t)(d) << 24))
#define DRM_XRGB8888 FOURCC('X', 'R', '2', '4')
#define DRM_ARGB8888 FOURCC('A', 'R', '2', '4')

/* ⛔ The two formats that `wl_shm` numbers 0 and 1 instead of with the fourcc.
 *    It is the only difference between the two numberings — and it was enough
 *    to blind a whole branch (defect 1 of the box at the top). */
static uint32_t shm_a_drm(uint32_t shm)
{
	if (shm == WL_SHM_FORMAT_ARGB8888)
		return DRM_ARGB8888;
	if (shm == WL_SHM_FORMAT_XRGB8888)
		return DRM_XRGB8888;
	return shm;
}

typedef struct {
	struct zwlr_output_head_v1 *proxy;
	char *name;
	bool enabled;
} Head;

static void widen_24(WlrStage *p, WlrFrame *report);

/* ⭐ How many slabs — see the box at the top, «the three rules». */
#define WLR_SLABS 3

/* ⛔ How many `failed` IN A ROW on the card before turning it off: one can be
 *    the output changing under the round; three are a route that does not work. */
#define WLR_CARD_FAILED_MAX 3

/* ⚠ The ceiling for the birth of a slab (the answer to `create`).  ⛔ Not
 *   the frame wait: the child calls with 8 ms, and a slab that is not born
 *   within 8 ms the first time would turn the card off forever over a
 *   delay.  It happens three times per session (and at every size change). */
#define WLR_SLAB_BIRTH_S 1.0

/*
 * ⛔⛔ PHASE 19 — THE SLAB IS BORN AT THE MAXIMUM CANVAS AND DOES NOT DIE ON A
 *      SIZE CHANGE (1 Oct 2026, the Radeon GPU hang on the Vulkan route).
 *
 *   Resizing is done by changing the `wl_buffer` (the size declared to the
 *   compositor), NOT the BO: the GBM slab is born `WLR_SLAB_W x
 *   WLR_SLAB_H` (= `RCP_TELA_L/A_MASSIMA` of `rcp.h`, the largest canvas
 *   the product accepts) and serves every size that fits inside it, with its
 *   own stride.  It dies only with the stage, with the card being turned off,
 *   or if a size does not fit (it does not happen: the canvas shrinks first, §4.5).
 *
 *   ⛔ Why: GBM (radeonsi) and Vulkan (RADV) in the SAME process, on the SAME
 *     card, share a single libdrm `amdgpu_device` — one DRM file, one card
 *     VM, one address space (`[M]`: the three slabs sit in the
 *     `drm-client-id` of RADV's BOs, 87 MB «shared»).
 *     Throwing away a GBM BO and right after creating the Vulkan encoder at
 *     the new size ⇒ the card finds UNMAPPED an image that RADV has just
 *     bound (`VK_EXT_device_address_binding_report`: BIND and no UNBIND; the
 *     page fault falls inside the new input image) ⇒ page fault,
 *     `VK_ERROR_DEVICE_LOST`, MODE1 reset that wipes the card for everyone.
 *     It is the driver (amdgpu kernel / Mesa 25.0.7 winsys), not the use of
 *     the API, but it is avoided here: `[M]` 1 Oct 2026, F-018 on lxqt
 *     Radeon/Vulkan, 10 faults in 14 runs with the slabs thrown away on the
 *     change, 0 in 5 with the slabs kept (and 0 in 5 on the memory route).
 *   ⚠ The price: 3 x 4096x2304x4 = 113 MB of slabs per session, even at
 *     1080p (they were 3 x the canvas).  ⇒ ONLY when the child's encoding is
 *     Vulkan (`wlr_slabs_at_max_canvas()`, decided in `child.c` before
 *     the stage): with VA-API the slabs of the right size stay.
 */
#define WLR_SLAB_W 4096u
#define WLR_SLAB_H 2304u

/* The default is FALSE: with VA-API (the Intel, where radeonsi/iHD are alone
 * in the process) the defect is not there, and 113 MB per session on an
 * integrated GPU are system RAM spent for nothing. */
static bool max_slabs = false;

void wlr_slabs_at_max_canvas(bool yes)
{
	max_slabs = yes;
}

typedef enum {
	SLAB_FREE = 0,
	SLAB_IN_FLIGHT, /* named in the `copy` of the frame in progress    */
	SLAB_IN_HAND  /* delivered: until it comes back with `wlr_release()` */
} SlabState;

typedef struct {
	struct gbm_bo *bo;
	struct wl_buffer *buffer;
	int fd;
	uint32_t width, height, stride, offset, fmt; /* fmt: DRM fourcc */
	uint32_t bo_width, bo_height; /* the BO: the birth size (WLR_LASTRA_*) */
	uint64_t modifier;
	SlabState state;
	bool dirty;
} WlrSlab;

typedef enum {
	CONF_IN_PROGRESS = 0,
	CONF_SUCCEEDED,
	CONF_FAILED,  /* `failed`: the compositor said NO               */
	CONF_CANCELLED /* `cancelled`: the serial was old, try again     */
} ConfOutcome;

struct WlrStage {
	struct wl_display *display;
	struct wl_registry *registry;
	struct wl_shm *shm;
	struct zwlr_screencopy_manager_v1 *manager;
	struct wl_output *output;
	char *output_name;

	/* the geometry the output declares — ⛔ the one it HAS, not the one wanted */
	uint32_t width, height;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ THE OUTPUT SIZE — `zwlr_output_manager_v1`.
	 *
	 * ⛔ On this family the canvas is NOT negotiated with the stream: there is
	 *    no stream.  The size of the OUTPUT is changed, and then the frames
	 *    arrive that way.  ⇒ It is the thing that could not be done on KDE.
	 * ------------------------------------------------------------------ */
	struct zwlr_output_manager_v1 *handler;
	GPtrArray *heads; /* of `Testa *` — ALL of them, not just ours (defect 5) */
	uint32_t serial;
	bool known_serial;
	ConfOutcome conf;

	/* the shared buffer, reused from one frame to the next */
	struct wl_buffer *buffer;
	void *pixel;
	gsize byte;
	int fd;
	uint32_t b_width, b_height, b_stride, b_format;
	/*
	 * ⛔⛔ THE DIRTY BUFFER.  If a frame is abandoned AFTER sending `copy`
	 *     and without waiting for its outcome (dropped wire), the compositor
	 *     may write into it later: reusing it would give an old frame among
	 *     the new ones — not an error, a flicker (`LESSONS.md` §8).
	 *  ⚠ With the PENDING frame (defect 2) the timeout no longer dirties it:
	 *    the copy stays ours and we wait.  It remains only for the dropped wire.
	 */
	bool buffer_dirty;

	/* ------------------------------------------------------------------ *
	 * THE FRAME IN PROGRESS — ⭐ and it can survive a call.
	 * ------------------------------------------------------------------ */
	struct zwlr_screencopy_frame_v1 *frame;
	bool seen_buffer, seen_buffer_done, ready, has_failed, copy_started, y_inverted;
	uint32_t f_shm; /* the format as wl_shm says it: needed by the buffer */
	uint32_t f_width, f_height, f_stride;
	uint64_t f_seconds;
	uint32_t f_nanoseconds;

	bool format_logged;
	/*
	 * ⭐ 24-BIT PIXELS — 5 Oct 2026, NVIDIA (RTX 4090, driver 595).
	 *   `[M]` labwc on the NVIDIA offers in memory ONLY `BG24` (3 bytes per
	 *   pixel, stride 3·width), and downstream everyone reads 4 bytes per
	 *   pixel: every frame was DISCARDED («stride >= 4·width needed») and the
	 *   session stayed black.  ⇒ Here they are widened to 32 bits, one row
	 *   at a time, in a copy of ours: `BG24` (R G B in memory) → `XB24`
	 *   (R G B x), `RG24` (B G R) → `XR24` (B G R x), two formats that
	 *   already exist downstream.  ⚠ The price, declared: one more pass over
	 *   the pixels, only on this fallback route.
	 */
	uint8_t *largo;
	gsize largo_byte;
	/* ⭐ The modifiers the encoder can import (see `slab_prepare`):
	 *    for the format `mod_format`, asked once. */
	uint32_t mod_format;
	uint64_t mod_allowed[16];
	int mod_count;
	/*
	 * ⭐⭐ THE DAMAGE — 21 Sep 2026, and the safety net found it.
	 *
	 * `[M]` The first draft asked for `copy`: the compositor copies the output
	 * AT ONCE, changed or not.  ⇒ With the desktop still the child produced **~60
	 * identical frames per second** (247 in the first 5 s, before the scene
	 * started), encoded them and sent them.  On GNOME and KDE the product
	 * delivers only when something changes; here it burned bandwidth and card
	 * for nothing — and mesh C3 no longer saw its «encoder stopped» fault,
	 * because before the stop a thousand frames of motionless desktop had
	 * already gone through.
	 * ⇒ `copy_with_damage` (screencopy v2+): the compositor answers only
	 *   when the output has CHANGED.  It is the same contract as the push.
	 * ⚠ But a KEYFRAME is sometimes needed at once even on a still desktop (a
	 *   client attaching, a §5.2 request): `force_full` makes the NEXT round
	 *   use `copy`, and `wlr_force_full()` sets it.  The very first round is
	 *   full too: whoever attaches must see at once.
	 */
	bool force_full, logged_damage;
	bool duplicate_with_damage; /* the copy in flight is `copy_with_damage` */
	/* ⭐ The damage DECLARED by the compositor, per frame (witness only,
	 *    with `--verbose`): `[M]` 5 Oct 2026, NVIDIA + zero copy, the
	 *    compositor answers at 60/s on a still desktop — and the question is
	 *    whether it declares it changed everywhere or in a corner. */
	uint64_t frame_damage_area, damage_area_sum;
	uint32_t frame_damage_rects, damage_rect_sum, damage_frames, whole_damage;
	uint32_t damage_x, damage_y, damage_w, damage_h; /* the last rectangle */
	WlrCounts counts;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ THE CARD ROUTE — the box at the top.
	 *
	 * ⛔ Everything below is valid ONLY if `card_born`: before
	 *    `wlr_ask_card()` the fields are the zeros of `g_new0`, and
	 *    zero for a descriptor means standard input — hence the flag.
	 * ------------------------------------------------------------------ */
	struct zwp_linux_dmabuf_v1 *dmabuf;
	uint32_t dmabuf_version;
	bool card_born; /* node open, `gbm` created, slabs initialised */
	bool card;      /* ⭐ in force NOW                               */
	int drm_fd;
	struct gbm_device *gbm;
	char *node;
	/* the feedback's `main_device`: the node the compositor draws on */
	dev_t main;
	bool main_known, feedback_finished;
	/* the card offer in THIS frame — ⛔ DRM fourcc, NOT wl_shm */
	bool card_offered;
	uint32_t o_card_format, o_card_w, o_card_h;
	WlrSlab slabs[WLR_SLABS];
	unsigned upcoming;
	/* ⭐ -1: the frame in progress goes (or will go) to memory.  ⛔ It survives
	 *    the timeout together with `frame`: it is the slab IN FLIGHT of THAT
	 *    frame, and the next call finds it again. */
	int round_slab;
	uint64_t generation;
	unsigned failed_in_a_row;
	/* the creation of the `wl_buffer` (`zwp_linux_buffer_params_v1`) */
	struct wl_buffer *created;
	bool params_finished, params_failed;
	/* ⚠ the lines said only once */
	bool logged_no_offer, logged_card_format, logged_implicit_sync;
	bool card_format_logged;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ THE POINTER PROBE — the box above `wlr_probe_pointer`.
	 *
	 * ⛔ All its own: a frame, a buffer, a descriptor that are NOT those of
	 *    the stream.  The main stream does not know the probe exists.
	 * ------------------------------------------------------------------ */
	struct zwlr_screencopy_frame_v1 *s_frame; /* ONLY ONE in flight      */
	bool s_seen_buffer, s_copy_started;
	uint32_t s_f_shm, s_f_l, s_f_a, s_f_stride;
	struct wl_buffer *s_buffer;
	void *s_pixel;
	int s_fd;
	gsize s_byte;
	uint32_t s_b_l, s_b_a, s_b_stride, s_b_shm;
	/* the position of the request IN FLIGHT, and the one to relaunch */
	int32_t s_x, s_y;
	bool s_pending; /* ⭐ coalescing: only the LAST position is remembered */
	int32_t s_wait_x, s_wait_y;
	/* ⭐ the «tail» probe: one more, with the hand still — see the box */
	gint64 s_tail_at;
	bool s_queue_done;
	gint64 s_last_started; /* for the thinning */
	int s_shape;             /* the last recognised shape, -1 = none     */
	int s_new;             /* to deliver to `wlr_probe_shape`, or -1     */
	bool s_off;           /* the format cannot be read: said, and that's it */
	bool s_format_logged, s_unknown_logged, s_failed_logged;
	WlrProbeCounts s_count;
};

/* ------------------------------------------------------------------------- */
/* The pump, with a deadline. */

/*
 * One round of the pump, with a deadline.
 *
 * ⛔ `wl_display_dispatch()` BLOCKS without a ceiling: a mute compositor
 *    would stop the child forever — and the symptom would not be an error,
 *    it would be «it is slow», which is the form of error this project has
 *    already paid for three times.  ⇒ We wait on the descriptor with a real ceiling.
 */
static bool pump(WlrStage *p, gint64 expiry, GError **mistake)
{
	struct pollfd pfd;
	gint64 stays;
	int r;

	while (wl_display_prepare_read(p->display) != 0) {
		if (wl_display_dispatch_pending(p->display) < 0) {
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
			            "the wire to the compositor dropped (dispatch_pending)");
			return false;
		}
	}
	if (wl_display_flush(p->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(p->display);
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "the wire to the compositor dropped (flush): %s", g_strerror(errno));
		return false;
	}

	stays = (expiry - g_get_monotonic_time()) / 1000;
	if (stays < 0)
		stays = 0;
	pfd.fd = wl_display_get_fd(p->display);
	pfd.events = POLLIN;
	r = poll(&pfd, 1, (int)stays);
	if (r <= 0) {
		wl_display_cancel_read(p->display);
		if (r == 0)
			return true; /* timed out: the caller looks at the clock */
		g_set_error(mistake, G_IO_ERROR, g_io_error_from_errno(errno), "poll: %s",
		            g_strerror(errno));
		return false;
	}
	if (wl_display_read_events(p->display) < 0) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "the wire to the compositor dropped (read_events)");
		return false;
	}
	if (wl_display_dispatch_pending(p->display) < 0) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "the wire to the compositor dropped (dispatch)");
		return false;
	}
	return true;
}

static void round_done(void *data, struct wl_callback *cb, uint32_t t)
{
	*(bool *)data = true;
}

static const struct wl_callback_listener ROUND_LISTENER = { .done = round_done };

/*
 * ⭐ A round trip WITH A CEILING — in place of `wl_display_roundtrip()`.
 *
 * ⛔ Defect 3 of the box at the top: `wl_display_roundtrip()` has no ceiling,
 *    and it ran three times inside the child.  This does the same thing (a
 *    `sync` and we wait for its `done`: everything the compositor sent before
 *    has arrived) and stops at the deadline.
 */
static bool cur_round(WlrStage *p, double wait_s, GError **mistake)
{
	bool completed = false;
	struct wl_callback *cb = wl_display_sync(p->display);
	gint64 expiry = g_get_monotonic_time() + (gint64)(wait_s * 1e6);

	wl_callback_add_listener(cb, &ROUND_LISTENER, &completed);
	while (!completed) {
		if (!pump(p, expiry, mistake)) {
			wl_callback_destroy(cb);
			return false;
		}
		if (!completed && g_get_monotonic_time() >= expiry) {
			wl_callback_destroy(cb);
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "the compositor did not answer a round trip "
			            "within %.1f s",
			            wait_s);
			return false;
		}
	}
	wl_callback_destroy(cb);
	return true;
}

/* ------------------------------------------------------------------------- */
/* The output (wl_output). */

static void output_geometry(void *data, struct wl_output *o, int32_t x, int32_t y, int32_t lf,
                             int32_t af, int32_t sub, const char *make, const char *model,
                             int32_t xform)
{
}

static void output_mode(void *data, struct wl_output *o, uint32_t flag, int32_t l, int32_t a,
                        int32_t refresh)
{
	WlrStage *p = data;

	/* ⛔ ONLY the CURRENT mode: an output may announce many. */
	if (flag & WL_OUTPUT_MODE_CURRENT) {
		p->width = (uint32_t)l;
		p->height = (uint32_t)a;
	}
}

static void output_end(void *data, struct wl_output *o) {}
static void output_scale(void *data, struct wl_output *o, int32_t scale_factor) {}

static void output_name(void *data, struct wl_output *o, const char *name)
{
	WlrStage *p = data;

	g_free(p->output_name);
	p->output_name = g_strdup(name);
}

static void output_description(void *data, struct wl_output *o, const char *d) {}

static const struct wl_output_listener OUTPUT_LISTENER = {
	.geometry = output_geometry,
	.mode = output_mode,
	.done = output_end,
	.scale = output_scale,
	.name = output_name,
	.description = output_description,
};

/* ------------------------------------------------------------------------- */
/* The output manager and its heads. */

/*
 * ⛔⛔ THE SERIAL, AND WHY THE LATEST IS ALWAYS KEPT.  A configuration created
 *     with an old serial is CANCELLED — and `cancelled` is not `failed`:
 *     it means «reality changed underneath», not «no».
 */
static void head_handler(void *data, struct zwlr_output_manager_v1 *m,
                          struct zwlr_output_head_v1 *head);

static void end_handler(void *data, struct zwlr_output_manager_v1 *m, uint32_t serial)
{
	WlrStage *p = data;

	p->serial = serial;
	p->known_serial = true;
}

static void handler_finished(void *data, struct zwlr_output_manager_v1 *m)
{
	WlrStage *p = data;

	zwlr_output_manager_v1_destroy(m);
	p->handler = NULL;
}

static const struct zwlr_output_manager_v1_listener MANAGER_LISTENER = {
	.head = head_handler,
	.done = end_handler,
	.finished = handler_finished,
};

static Head *head_of(WlrStage *p, struct zwlr_output_head_v1 *proxy)
{
	for (guint i = 0; p->heads && i < p->heads->len; i++) {
		Head *t = g_ptr_array_index(p->heads, i);

		if (t->proxy == proxy)
			return t;
	}
	return NULL;
}

static void head_name(void *data, struct zwlr_output_head_v1 *proxy, const char *name)
{
	Head *t = head_of(data, proxy);

	/* ⭐ Defect 5: the name is KEPT, and the right head is chosen when it is
	 *    needed.  Before, it was compared here with the name of the `wl_output`,
	 *    and if that had not arrived yet the head was never found. */
	if (t) {
		g_free(t->name);
		t->name = g_strdup(name);
	}
}

static void head_enabled(void *data, struct zwlr_output_head_v1 *proxy, int32_t enabled)
{
	Head *t = head_of(data, proxy);

	if (t)
		t->enabled = enabled != 0;
}

static void head_finished(void *data, struct zwlr_output_head_v1 *proxy)
{
	WlrStage *p = data;
	Head *t = head_of(p, proxy);

	if (t)
		g_ptr_array_remove(p->heads, t); /* `free_head` frees it */
}

static void head_description(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void head_physical_size(void *d, struct zwlr_output_head_v1 *t, int32_t l, int32_t a) {}
static void head_mode(void *d, struct zwlr_output_head_v1 *t, struct zwlr_output_mode_v1 *m) {}
static void head_current_mode(void *d, struct zwlr_output_head_v1 *t,
                                struct zwlr_output_mode_v1 *m) {}
static void head_position(void *d, struct zwlr_output_head_v1 *t, int32_t x, int32_t y) {}
static void head_transform(void *d, struct zwlr_output_head_v1 *t, int32_t x) {}
static void head_scale(void *d, struct zwlr_output_head_v1 *t, wl_fixed_t s) {}
static void head_make(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void head_model(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void head_serial(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void head_sync(void *d, struct zwlr_output_head_v1 *t, uint32_t x) {}

static const struct zwlr_output_head_v1_listener HEAD_LISTENER = {
	.name = head_name,
	.description = head_description,
	.physical_size = head_physical_size,
	.mode = head_mode,
	.enabled = head_enabled,
	.current_mode = head_current_mode,
	.position = head_position,
	.transform = head_transform,
	.scale = head_scale,
	.finished = head_finished,
	.make = head_make,
	.model = head_model,
	.serial_number = head_serial,
	.adaptive_sync = head_sync,
};

static void free_head(gpointer data)
{
	Head *t = data;

	if (t->proxy)
		zwlr_output_head_v1_destroy(t->proxy);
	g_free(t->name);
	g_free(t);
}

static void head_handler(void *data, struct zwlr_output_manager_v1 *m,
                          struct zwlr_output_head_v1 *proxy)
{
	WlrStage *p = data;
	Head *t = g_new0(Head, 1);

	t->proxy = proxy;
	g_ptr_array_add(p->heads, t);
	zwlr_output_head_v1_add_listener(proxy, &HEAD_LISTENER, p);
}

static void conf_succeeded(void *data, struct zwlr_output_configuration_v1 *c)
{
	((WlrStage *)data)->conf = CONF_SUCCEEDED;
}

static void conf_failed(void *data, struct zwlr_output_configuration_v1 *c)
{
	((WlrStage *)data)->conf = CONF_FAILED;
}

static void conf_cancelled(void *data, struct zwlr_output_configuration_v1 *c)
{
	((WlrStage *)data)->conf = CONF_CANCELLED;
}

static const struct zwlr_output_configuration_v1_listener CONF_LISTENER = {
	.succeeded = conf_succeeded,
	.failed = conf_failed,
	.cancelled = conf_cancelled,
};

/* ------------------------------------------------------------------------- */
/* The registry of globals. */

/* ⚠ Below v4 the global sends `format` and `modifier` as soon as it is bound:
 *   they are listened to and dropped — the modifier is decided by us
 *   (LINEAR, the box at the top), not by the list. */
static void dmabuf_format(void *d, struct zwp_linux_dmabuf_v1 *m, uint32_t f) {}
static void dmabuf_modifier(void *d, struct zwp_linux_dmabuf_v1 *m, uint32_t f,
                                uint32_t alto, uint32_t low) {}

static const struct zwp_linux_dmabuf_v1_listener DMABUF_LISTENER = {
	.format = dmabuf_format,
	.modifier = dmabuf_modifier,
};

static void registry_global(void *data, struct wl_registry *reg, uint32_t name,
                            const char *interfaccia, uint32_t version)
{
	WlrStage *p = data;

	if (g_strcmp0(interfaccia, wl_shm_interface.name) == 0) {
		p->shm = wl_registry_bind(reg, name, &wl_shm_interface, 1);
	} else if (g_strcmp0(interfaccia, zwlr_screencopy_manager_v1_interface.name) == 0) {
		uint32_t v = version < 3 ? version : 3;

		p->manager = wl_registry_bind(reg, name, &zwlr_screencopy_manager_v1_interface, v);
	} else if (g_strcmp0(interfaccia, zwp_linux_dmabuf_v1_interface.name) == 0 &&
	           !p->dmabuf) {
		/* ⭐ The card route.  ⚠ At most v4 (`[M]` labwc gives it): it is the
		 *   one with `main_device`, that is the node the compositor draws on.
		 *   ⛔ It is always bound, even if the card is not asked for: binding
		 *   costs nothing and changes nothing. */
		p->dmabuf_version = version < 4 ? version : 4;
		p->dmabuf = wl_registry_bind(reg, name, &zwp_linux_dmabuf_v1_interface,
		                             p->dmabuf_version);
		zwp_linux_dmabuf_v1_add_listener(p->dmabuf, &DMABUF_LISTENER, p);
	} else if (g_strcmp0(interfaccia, zwlr_output_manager_v1_interface.name) == 0) {
		uint32_t v = version < 4 ? version : 4;

		p->handler = wl_registry_bind(reg, name, &zwlr_output_manager_v1_interface, v);
		zwlr_output_manager_v1_add_listener(p->handler, &MANAGER_LISTENER, p);
	} else if (g_strcmp0(interfaccia, wl_output_interface.name) == 0) {
		if (!p->output) {
			uint32_t v = version < 4 ? version : 4;

			p->output = wl_registry_bind(reg, name, &wl_output_interface, v);
			wl_output_add_listener(p->output, &OUTPUT_LISTENER, p);
		} else {
			registro_dice(AREA,
			              "⚠ wlroots: the compositor announces more than one output — "
			              "I look at the first, and this line exists so that on that "
			              "day it is not a silent choice");
		}
	}
}

static void registry_remove(void *data, struct wl_registry *reg, uint32_t name) {}

static const struct wl_registry_listener REGISTRY_LISTENER = {
	.global = registry_global,
	.global_remove = registry_remove,
};

/* ------------------------------------------------------------------------- */
/* The frame. */

static void frame_buffer(void *data, struct zwlr_screencopy_frame_v1 *f, uint32_t fmt,
                         uint32_t width, uint32_t height, uint32_t stride)
{
	WlrStage *p = data;

	/* ⛔ ONCE per frame (defect 1): there is nothing to choose.
	 *    The format is in the wl_shm numbering, and is kept THAT WAY to create
	 *    the buffer; the translation to DRM is done only for whoever is downstream. */
	p->seen_buffer = true;
	p->f_shm = fmt;
	p->f_width = width;
	p->f_height = height;
	p->f_stride = stride;

	if (!p->format_logged) {
		uint32_t drm = shm_a_drm(fmt);
		char name[5];

		p->format_logged = true;
		memcpy(name, &drm, 4);
		name[4] = 0;
		registro_dice(AREA,
		              "wlroots: the compositor gives the pixels in «%s» (%ux%u stride %u) — %s",
		              name, width, height, stride,
		              (drm == FOURCC('B', 'G', '2', '4') || drm == FOURCC('R', 'G', '2', '4'))
		                  ? "⚠ 3 BYTES PER PIXEL: I widen them to 4 myself (x at the end) before "
		                    "delivering them — one more pass, only on this route"
		              : (drm == FOURCC('X', 'B', '2', '4') || drm == FOURCC('A', 'B', '2', '4'))
		                  ? "that is R G B x in memory: whoever consumes the frame tells the "
		                    "encoder the order"
		                  : "that is B G R x in memory, the order the encoder "
		                    "already read");
	}
}

static void frame_flags(void *data, struct zwlr_screencopy_frame_v1 *f, uint32_t flags)
{
	((WlrStage *)data)->y_inverted = (flags & ZWLR_SCREENCOPY_FRAME_V1_FLAGS_Y_INVERT) != 0;
}

static void frame_ready(void *data, struct zwlr_screencopy_frame_v1 *f, uint32_t sec_alto,
                         uint32_t sec_low, uint32_t nsec)
{
	WlrStage *p = data;

	p->f_seconds = ((uint64_t)sec_alto << 32) | sec_low;
	p->f_nanoseconds = nsec;
	p->ready = true;
	if (p->duplicate_with_damage && log_verbose()) {
		uint64_t output = (uint64_t)p->width * p->height;

		p->damage_frames++;
		p->damage_area_sum += p->frame_damage_area;
		p->damage_rect_sum += p->frame_damage_rects;
		if (output && p->frame_damage_area >= output)
			p->whole_damage++;
		if (p->damage_frames == 120) {
			log_detail(AREA,
			                   "wlroots: the declared damage, last 120 frames with damage: "
			                   "mean area %.1f%% of the output %ux%u, %u full, %.1f "
			                   "rectangles per frame (the last: %ux%u at %u,%u)",
			                   output ? 100.0 * (double)p->damage_area_sum / 120.0 / (double)output : 0.0,
			                   p->width, p->height, p->whole_damage,
			                   p->damage_rect_sum / 120.0, p->damage_w, p->damage_h,
			                   p->damage_x, p->damage_y);
			p->damage_frames = p->whole_damage = p->damage_rect_sum = 0;
			p->damage_area_sum = 0;
		}
	}
	p->frame_damage_area = 0;
	p->frame_damage_rects = 0;
}

static void frame_failed(void *data, struct zwlr_screencopy_frame_v1 *f)
{
	((WlrStage *)data)->has_failed = true;
}

static void frame_damage(void *data, struct zwlr_screencopy_frame_v1 *f, uint32_t x, uint32_t y,
                        uint32_t l, uint32_t a)
{
	WlrStage *p = data;

	/* ⚠ It arrives only with `copy_with_damage`, before `ready`. */
	p->frame_damage_area += (uint64_t)l * a;
	p->frame_damage_rects++;
	p->damage_x = x;
	p->damage_y = y;
	p->damage_w = l;
	p->damage_h = a;
}

static void frame_dmabuf(void *data, struct zwlr_screencopy_frame_v1 *f, uint32_t fmt,
                         uint32_t width, uint32_t height)
{
	WlrStage *p = data;

	/* ⭐ The card route: the offer is NOTED, and the choice is made by
	 *    `card_destination()` once the list is closed.  ⛔ And here the
	 *    format is a TRUE DRM fourcc — a different numbering from that of
	 *    `buffer`, in a field of its own, and it does NOT go through
	 *    `shm_a_drm()` (defect 1). */
	p->card_offered = true;
	p->o_card_format = fmt;
	p->o_card_w = width;
	p->o_card_h = height;
}

static void frame_buffer_done(void *data, struct zwlr_screencopy_frame_v1 *f)
{
	((WlrStage *)data)->seen_buffer_done = true;
}

/* ⭐ «Is the list of offers closed?» — on v3 `buffer_done` says so, and only
 *    then do we know whether the card was offered.  ⚠ Below v3
 *    `buffer_done` does not exist: there `buffer` is enough, and it is also the only offer. */
static bool list_closed(const WlrStage *p)
{
	if (p->seen_buffer_done)
		return true;
	return p->seen_buffer && zwlr_screencopy_frame_v1_get_version(p->frame) < 3;
}

static const struct zwlr_screencopy_frame_v1_listener FRAME_LISTENER = {
	.buffer = frame_buffer,
	.flags = frame_flags,
	.ready = frame_ready,
	.failed = frame_failed,
	.damage = frame_damage,
	.linux_dmabuf = frame_dmabuf,
	.buffer_done = frame_buffer_done,
};

static bool prepare_buffer(WlrStage *p, GError **mistake)
{
	struct wl_shm_pool *pool;
	gsize byte = (gsize)p->f_stride * p->f_height;

	if (!p->buffer_dirty && p->buffer && p->b_width == p->f_width &&
	    p->b_height == p->f_height && p->b_stride == p->f_stride &&
	    p->b_format == p->f_shm)
		return true; /* the previous one is fine */
	p->buffer_dirty = false;

	if (p->buffer) {
		wl_buffer_destroy(p->buffer);
		p->buffer = NULL;
	}
	if (p->pixel) {
		munmap(p->pixel, p->byte);
		p->pixel = NULL;
	}
	if (p->fd >= 0) {
		close(p->fd);
		p->fd = -1;
	}
	if (!byte) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_DATA,
		            "the compositor declared a buffer of 0 bytes (%ux%u stride %u)",
		            p->f_width, p->f_height, p->f_stride);
		return false;
	}

	p->fd = memfd_create("remotix-wlr", MFD_CLOEXEC);
	if (p->fd < 0) {
		g_set_error(mistake, G_IO_ERROR, g_io_error_from_errno(errno),
		            "memfd_create: %s", g_strerror(errno));
		return false;
	}
	if (ftruncate(p->fd, (off_t)byte) != 0) {
		g_set_error(mistake, G_IO_ERROR, g_io_error_from_errno(errno), "ftruncate(%zu): %s",
		            (size_t)byte, g_strerror(errno));
		return false;
	}
	p->pixel = mmap(NULL, byte, PROT_READ | PROT_WRITE, MAP_SHARED, p->fd, 0);
	if (p->pixel == MAP_FAILED) {
		p->pixel = NULL;
		g_set_error(mistake, G_IO_ERROR, g_io_error_from_errno(errno), "mmap: %s",
		            g_strerror(errno));
		return false;
	}
	p->byte = byte;

	pool = wl_shm_create_pool(p->shm, p->fd, (int32_t)byte);
	/* ⛔ The wl_shm format, NOT the translated one: the buffer is read by the
	 *    compositor, which speaks the wl_shm numbering. */
	p->buffer = wl_shm_pool_create_buffer(pool, 0, (int32_t)p->f_width,
	                                      (int32_t)p->f_height, (int32_t)p->f_stride,
	                                      p->f_shm);
	wl_shm_pool_destroy(pool);
	p->b_width = p->f_width;
	p->b_height = p->f_height;
	p->b_stride = p->f_stride;
	p->b_format = p->f_shm;
	return true;
}

/* ========================================================================= */
/* ⭐⭐ THE CARD ROUTE — the box at the top of the file.                      */
/*                                                                           */
/* ⛔ Everything that follows lives in functions OF ITS OWN: `wlr_frame()`*/
/*    calls them in three places (the target of the `copy`, the delivery, the */
/*    closing of the frame), and the memory round stays as it was.           */
/* ========================================================================= */

/* --- the feedback: the node the compositor draws on ---------------------- */

static void feedback_fine(void *data, struct zwp_linux_dmabuf_feedback_v1 *f)
{
	((WlrStage *)data)->feedback_finished = true;
}

static void feedback_table(void *data, struct zwp_linux_dmabuf_feedback_v1 *f, int32_t fd,
                             uint32_t amount)
{
	/* ⛔ The descriptor is OURS as soon as it arrives, and it is closed: the
	 *    format table is not needed (the modifier is LINEAR, decided), and an
	 *    `fd` kept for nothing is an `fd` lost at every session. */
	close(fd);
}

static void feedback_main(void *data, struct zwp_linux_dmabuf_feedback_v1 *f,
                                struct wl_array *device)
{
	WlrStage *p = data;

	/* ⚠ The protocol gives it as a `dev_t` in an array: if the size does not
	 *   match we do not guess, we leave it «not known» and fall back, saying so. */
	if (device->size == sizeof(dev_t)) {
		memcpy(&p->main, device->data, sizeof(dev_t));
		p->main_known = true;
	}
}

static void feedback_tranche_fine(void *d, struct zwp_linux_dmabuf_feedback_v1 *f) {}
static void feedback_tranche_avail(void *d, struct zwp_linux_dmabuf_feedback_v1 *f,
                                  struct wl_array *a) {}
static void feedback_tranche_formats(void *d, struct zwp_linux_dmabuf_feedback_v1 *f,
                                     struct wl_array *a) {}
static void feedback_tranche_flags(void *d, struct zwp_linux_dmabuf_feedback_v1 *f,
                                      uint32_t b) {}

static const struct zwp_linux_dmabuf_feedback_v1_listener FEEDBACK_LISTENER = {
	.done = feedback_fine,
	.format_table = feedback_table,
	.main_device = feedback_main,
	.tranche_done = feedback_tranche_fine,
	.tranche_target_device = feedback_tranche_avail,
	.tranche_formats = feedback_tranche_formats,
	.tranche_flags = feedback_tranche_flags,
};

/*
 * From the `dev_t` to the `renderD*` node of the same card.
 *
 * ⚠ The `main_device` can be the primary node (`card0`) or the render one:
 *   the sysfs folder `/sys/dev/char/M:m/device/drm/` lists BOTH of them in
 *   either case, and the `renderD*` is taken from there.  ⛔ No `libdrm` to
 *   link for this: one more library for one line of sysfs.
 */
static char *node_from_device(dev_t d)
{
	g_autofree char *folder =
	    g_strdup_printf("/sys/dev/char/%u:%u/device/drm", major(d), minor(d));
	g_autoptr(GDir) dir = g_dir_open(folder, 0, NULL);
	const char *entry;

	if (!dir)
		return NULL;
	while ((entry = g_dir_read_name(dir)))
		if (g_str_has_prefix(entry, "renderD"))
			return g_build_filename("/dev/dri", entry, NULL);
	return NULL;
}

/*
 * ⚠ THE FALLBACK, when the compositor does not say its node (v < 4): the SAME
 *   rule with which `session.c` chooses `WLR_RENDER_DRM_DEVICE` — one function,
 *   `card_pick_desktop()` (`card_pick.h`): the BIOS primary card if it can draw,
 *   else the capable card with the lowest PCI address.  ⛔ A different rule here
 *   would mean allocating on the other card exactly on the day the nodes swap.
 *   If NO card can draw (labwc is on pixman) the node is still needed for the
 *   buffer: the first openable one in the same order, without the drawing test.
 */
static char *node_as_session(void)
{
	card_pick_how how;
	g_autofree char *story = NULL;
	char *n = card_pick_desktop(&how, &story);

	if (n)
		return n;
	return card_pick("/dev/dri", "/sys/class/drm", NULL, &how, &story);
}

/* --- the slabs ------------------------------------------------------------ */

/*
 * ⛔⛔ THE GENERATION BELONGS TO THE PROCESS, NOT TO THE STAGE — 22 Sep 2026: on
 *      KDE the counter restarted from 0 with every new capture, and after
 *      «Log out» and a new login the encoder (which stays) found the surfaces
 *      of the dead session again in its cache: the screen flashed.  See
 *      `new_generation()` in `capture.c`.  ⇒ The same here, because a new
 *      stage is born at every rebirth of the XFCE session.
 * ⚠ It starts from 2^62, and not from 0: `capture.c` has its own counter (this
 *   file is also linked into bench 13-w1, without `capture.o`), and the two
 *   ranges never touch.
 */
static uint64_t new_generation(void)
{
	static uint64_t latest = UINT64_C(1) << 62;

	return __atomic_add_fetch(&latest, 1, __ATOMIC_RELAXED);
}

/* ⛔ «Is the frame in progress on the card?» — and the flag before the
 *    index: before `wlr_ask_card()` the index is the zero of
 *    `g_new0`, that is a slab that does not exist. */
static bool card_in_round(const WlrStage *p)
{
	return p->card_born && p->round_slab >= 0;
}

static void slab_drop(WlrStage *p, WlrSlab *l)
{
	bool had_buffer = l->bo || l->buffer;

	if (l->buffer)
		wl_buffer_destroy(l->buffer);
	if (l->bo)
		gbm_bo_destroy(l->bo);
	if (l->fd >= 0)
		close(l->fd);
	memset(l, 0, sizeof *l);
	l->fd = -1;
	/* ⛔ Rule 3: a slab that dies changes the generation. */
	if (had_buffer)
		p->generation = new_generation();
}

/*
 * ⭐ A slab becomes FREE again — the only place that does it, besides `wlr_release()`.
 *
 * ⚠ If the card has been turned off in the meantime, the slab is no longer
 *   needed: it is thrown away now, which is the first moment it can be.
 */
static void slab_returns_free(WlrStage *p, WlrSlab *l, bool dirty)
{
	l->state = SLAB_FREE;
	if (dirty)
		l->dirty = true;
	if (!p->card)
		slab_drop(p, l);
}

static void params_created(void *data, struct zwp_linux_buffer_params_v1 *pr,
                          struct wl_buffer *buffer)
{
	WlrStage *p = data;

	p->created = buffer;
	p->params_finished = true;
}

static void params_failed(void *data, struct zwp_linux_buffer_params_v1 *pr)
{
	WlrStage *p = data;

	p->params_failed = true;
	p->params_finished = true;
}

static const struct zwp_linux_buffer_params_v1_listener PARAMS_LISTENER = {
	.created = params_created,
	.failed = params_failed,
};

/*
 * Creates (or keeps) the slab for the format and size of THIS frame.
 *
 * ⛔ `create` and not `create_immed`: with the latter a refusal by the
 *    compositor can be a PROTOCOL error, that is the connection dying.  With
 *    the former it is a `failed` event, and we fall back, saying so.
 * ⛔ And we wait with a ceiling OF ITS OWN (`WLR_SLAB_BIRTH_S`), not with
 *    the frame's: see the definition.
 */
static bool slab_prepare(WlrStage *p, WlrSlab *l, uint32_t fmt, uint32_t width,
                           uint32_t height, GError **mistake)
{
	uint64_t linear = DRM_FORMAT_MOD_LINEAR;
	struct zwp_linux_buffer_params_v1 *params;
	gint64 expiry;

	if (l->buffer && !l->dirty && l->width == width && l->height == height &&
	    l->fmt == fmt)
		return true; /* the previous one is fine */
	if (max_slabs && l->bo && l->fmt == fmt && width <= l->bo_width &&
	    height <= l->bo_height) {
		/* ⛔ PHASE 19: the BO stays (see WLR_SLAB_W), only the `wl_buffer`
		 *    changes.  ⛔ Rule 3: the size has changed, so the generation
		 *    changes — the encoder must not find in its cache the import
		 *    with the old size. */
		if (l->buffer)
			wl_buffer_destroy(l->buffer);
		l->buffer = NULL;
		l->width = width;
		l->height = height;
		p->generation = new_generation();
		goto il_buffer;
	}
	slab_drop(p, l);
	if (max_slabs && (width > WLR_SLAB_W || height > WLR_SLAB_H))
		registro_dice(AREA,
		              "⚠ wlroots: a %ux%u canvas beyond the maximum slab %ux%u — the "
		              "slab is born at the requested size, and on a size change it WILL DIE "
		              "(PHASE 19: on the Radeon with Vulkan this is the GPU hang case)",
		              width, height, WLR_SLAB_W, WLR_SLAB_H);

	/* ⭐ LINEAR, asked for by name.  ⚠ If the driver does not accept the
	 *   modifier list we retry with the LINEAR flag, which says the same
	 *   thing in the old dialect. */
	l->bo_width = (max_slabs && width < WLR_SLAB_W) ? WLR_SLAB_W : width;
	l->bo_height = (max_slabs && height < WLR_SLAB_H) ? WLR_SLAB_H : height;
	l->bo = gbm_bo_create_with_modifiers2(p->gbm, l->bo_width, l->bo_height, fmt,
	                                      &linear, 1, GBM_BO_USE_RENDERING);
	if (!l->bo)
		l->bo = gbm_bo_create(p->gbm, l->bo_width, l->bo_height, fmt,
		                      GBM_BO_USE_RENDERING | GBM_BO_USE_LINEAR);
	/*
	 * ⭐ 5 Oct 2026, NVIDIA (RTX 4090, driver 595): `[M]` the NVIDIA GBM
	 *   refuses LINEAR + RENDERING (`Invalid argument`, with both dialects)
	 *   and accepts RENDERING with ITS OWN modifier
	 *   (`0x300000000e08014`).  ⇒ Only if linear was refused, the driver
	 *   chooses the slab, and the modifier travels with the frame: Vulkan
	 *   imports it by name (`VK_EXT_image_drm_format_modifier`), and if it
	 *   could not, it would say so at import.  ⛔ Intel and Radeon do not
	 *   pass through here: linear works for them.
	 */
	bool driver_choice = false;
	if (!l->bo) {
		/* ⛔ Not «whatever the driver wants»: `[M]` on the 4090 it picks a
		 *    modifier Vulkan does not import.  Only those the encoder
		 *    declares (`vulkanvideo_modifiers`), asked once per stage and
		 *    format. */
		int linear_errno = errno;
		if (p->mod_format != fmt) {
			p->mod_format = fmt;
			p->mod_count = vulkanvideo_modifiers(p->node, fmt, p->mod_allowed,
			                                         (int)G_N_ELEMENTS(p->mod_allowed));
		}
		if (p->mod_count > 0)
			l->bo = gbm_bo_create_with_modifiers2(p->gbm, l->bo_width, l->bo_height,
			                                      fmt, p->mod_allowed,
			                                      (unsigned)p->mod_count, GBM_BO_USE_RENDERING);
		if (!l->bo)
			errno = linear_errno;
		else
			driver_choice = true;
	}
	if (!l->bo) {
		g_set_error(mistake, G_IO_ERROR, g_io_error_from_errno(errno),
		            "gbm does not allocate %ux%u fourcc 0x%08x on %s, neither linear nor with one of "
		            "the %d modifiers the encoder imports: %s",
		            l->bo_width, l->bo_height, fmt, p->node, p->mod_count,
		            g_strerror(errno));
		return false;
	}
	if (gbm_bo_get_plane_count(l->bo) != 1) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "gbm gave a slab with %d planes: the encoder can read one",
		            gbm_bo_get_plane_count(l->bo));
		slab_drop(p, l);
		return false;
	}
	l->modifier = gbm_bo_get_modifier(l->bo);
	/* ⚠ With the old dialect the modifier can come back INVALID: the LINEAR
	 *   flag however fixed it, and it is written down for what it is. */
	if (l->modifier == DRM_FORMAT_MOD_INVALID && !driver_choice)
		l->modifier = DRM_FORMAT_MOD_LINEAR;
	if (driver_choice) {
		static bool said = false;
		if (l->modifier == DRM_FORMAT_MOD_INVALID) {
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
			            "gbm refused linear, and the driver's slab does not say "
			            "its modifier: nobody could import it");
			slab_drop(p, l);
			return false;
		}
		if (!said) {
			said = true;
			registro_dice(AREA,
			              "⭐ wlroots: the driver refuses the LINEAR slab (NVIDIA): the "
			              "slab is born with modifier 0x%" G_GINT64_MODIFIER "x, chosen "
			              "among the %d the Vulkan encoder declares it can import",
			              (guint64)l->modifier, p->mod_count);
		}
	} else if (l->modifier != DRM_FORMAT_MOD_LINEAR) {
		/* ⛔ LINEAR was asked for: a tiling nobody chose is an import
		 *    nobody has tried. */
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "gbm gave modifier 0x%" G_GINT64_MODIFIER "x instead of the "
		            "LINEAR asked for",
		            (guint64)l->modifier);
		slab_drop(p, l);
		return false;
	}
	l->fd = gbm_bo_get_fd(l->bo);
	l->stride = gbm_bo_get_stride_for_plane(l->bo, 0);
	l->offset = gbm_bo_get_offset(l->bo, 0);
	l->width = width;
	l->height = height;
	l->fmt = fmt;
	if (l->fd < 0) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "gbm_bo_get_fd: the slab has no DMA-BUF descriptor");
		slab_drop(p, l);
		return false;
	}
	/* ⛔ The slab is already born here, even if the `wl_buffer` is not there
	 *    yet: the generation changes NOW (rule 3). */
	p->generation = new_generation();

il_buffer:
	p->created = NULL;
	p->params_finished = p->params_failed = false;
	params = zwp_linux_dmabuf_v1_create_params(p->dmabuf);
	zwp_linux_buffer_params_v1_add_listener(params, &PARAMS_LISTENER, p);
	zwp_linux_buffer_params_v1_add(params, l->fd, 0, l->offset, l->stride,
	                               (uint32_t)(l->modifier >> 32),
	                               (uint32_t)(l->modifier & 0xffffffffu));
	zwp_linux_buffer_params_v1_create(params, (int32_t)width, (int32_t)height, fmt, 0);
	expiry = g_get_monotonic_time() + (gint64)(WLR_SLAB_BIRTH_S * G_USEC_PER_SEC);
	while (!p->params_finished) {
		if (!pump(p, expiry, mistake)) {
			zwp_linux_buffer_params_v1_destroy(params);
			slab_drop(p, l);
			return false;
		}
		if (!p->params_finished && g_get_monotonic_time() >= expiry)
			break;
	}
	zwp_linux_buffer_params_v1_destroy(params);
	if (!p->params_finished || p->params_failed || !p->created) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "the compositor %s the %ux%u DMA-BUF (modifier 0x%" G_GINT64_MODIFIER
		            "x, stride %u)",
		            p->params_finished ? "REFUSED" : "did not answer in time for",
		            width, height, (guint64)l->modifier, l->stride);
		/* ⚠ If `created` arrived after the ceiling the `wl_buffer` would be left
		 *   orphaned: one lost object, once, against a live connection. */
		slab_drop(p, l);
		return false;
	}
	l->buffer = p->created;
	p->created = NULL;
	l->dirty = false;
	return true;
}

/* ⛔ Rule 1: ONLY a FREE slab is chosen, in rotation. */
static int slab_choose(WlrStage *p)
{
	for (unsigned i = 0; i < WLR_SLABS; i++) {
		unsigned k = (p->upcoming + i) % WLR_SLABS;

		if (p->slabs[k].state == SLAB_FREE) {
			p->upcoming = (k + 1) % WLR_SLABS;
			return (int)k;
		}
	}
	return -1;
}

/*
 * ⛔ The card is TURNED OFF, and the reason is said.  From here every frame
 *    goes to memory, and the counters show it.
 * ⚠ Only the FREE ones are thrown away: one IN HAND is thrown away by
 *   `wlr_release()` when it comes back, one IN FLIGHT by the closing of its
 *   frame (`slab_returns_free`).  ⛔ Throwing away a slab in flight would
 *   mean destroying a `wl_buffer` named in a `copy` still open.
 */
static void card_turn_off(WlrStage *p, const char *why)
{
	if (!p->card)
		return;
	p->card = false;
	for (unsigned i = 0; i < WLR_SLABS; i++)
		if (p->slabs[i].state == SLAB_FREE)
			slab_drop(p, &p->slabs[i]);
	registro_dice(AREA,
	              "⛔⛔ wlroots: the CARD route is TURNED OFF — %s.  ⇒ DECLARED "
	              "FALLBACK: from here the pixels go through MEMORY (`glReadPixels` "
	              "in the compositor + our copy), and the numbers of this link are "
	              "those of the other route",
	              why);
}

/*
 * ⭐ THE TARGET OF THIS FRAME'S `copy` — the card, or NULL for memory.  It is
 *    called once the list is closed (`list_closed()`), ONCE per frame:
 *    after that, the answer is in `round_slab`.
 *
 * ⛔ It returns NULL also with `*broken` true: all the slabs are in hand
 *    downstream.  There the frame STOPS; a slab in hand is not recycled and
 *    there is no silent fallback to memory (rule 1).
 */
static struct wl_buffer *card_destination(WlrStage *p, bool *broken, GError **mistake)
{
	g_autoptr(GError) why = NULL;
	WlrSlab *l;
	int k;

	*broken = false;
	p->round_slab = -1;
	if (!p->card)
		return NULL;
	if (!p->card_offered) {
		/* ⚠ `[R]` wlroots sends `linux_dmabuf` only if the output's allocator
		 *   can do DMA-BUF: without it, the compositor is in SOFTWARE
		 *   (pixman, `STUDIES.md` §xfce §5.2).  It is a diagnosis, and it is written. */
		if (!p->logged_no_offer) {
			p->logged_no_offer = true;
			registro_dice(AREA,
			              "⛔ wlroots: the compositor does NOT offer DMA-BUF for this "
			              "frame — it usually means it draws in SOFTWARE "
			              "(pixman, `STUDIES.md` §xfce §5.2).  DECLARED FALLBACK: the "
			              "frame goes to MEMORY; the line is not repeated");
		}
		return NULL;
	}
	if (p->o_card_format != DRM_FORMAT_XRGB8888 &&
	    p->o_card_format != DRM_FORMAT_ARGB8888) {
		if (!p->logged_card_format) {
			char name[5];

			p->logged_card_format = true;
			memcpy(name, &p->o_card_format, 4);
			name[4] = 0;
			registro_dice(AREA,
			              "⛔ wlroots: the card offers «%s», and the encoder imports "
			              "only XRGB8888 and ARGB8888 — ⚠ a fourcc is NOT guessed (a "
			              "swapped channel gives no error, it gives a blue desktop).  "
			              "DECLARED FALLBACK: the frame goes to MEMORY",
			              name);
		}
		return NULL;
	}

	k = slab_choose(p);
	if (k < 0) {
		*broken = true;
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_BUSY,
		            "all %d of the card's slabs are IN HAND downstream: someone "
		            "did not call `wlr_release()` (that is `capture_stopped_free()`).  ⛔ "
		            "None is recycled: it would mean rewriting an image while the "
		            "encoder reads it",
		            WLR_SLABS);
		return NULL;
	}
	l = &p->slabs[k];
	if (!slab_prepare(p, l, p->o_card_format, p->o_card_w, p->o_card_h, &why)) {
		g_autofree char *reason =
		    g_strdup_printf("the slab was not born (%s)", why ? why->message : "?");

		card_turn_off(p, reason);
		return NULL;
	}
	l->state = SLAB_IN_FLIGHT;
	p->round_slab = k;
	return l->buffer;
}

/*
 * ⛔⛔ THE GPU WAIT AFTER `ready` — the synchronisation box.
 *
 * It returns false only if the fence was there and did NOT fire before the
 * deadline: then the slab is not delivered (whoever read it would see a half
 * blit), and the frame stays PENDING — the next call waits again.
 */
static bool card_wait_gpu(WlrStage *p, WlrSlab *l, gint64 expiry,
                                  WlrFrame *report, GError **mistake)
{
	struct dma_buf_export_sync_file sf = { .flags = DMA_BUF_SYNC_READ, .fd = -1 };
	gint64 before = g_get_monotonic_time();
	struct pollfd pfd;
	gint64 stays;
	int r;

	report->gpu_wait_us = 0;
	report->explicit_wait = false;
	if (ioctl(l->fd, DMA_BUF_IOCTL_EXPORT_SYNC_FILE, &sf) != 0) {
		/* ⚠ Kernel without the ioctl (< 5.20), or a driver that does not support
		 *   it: we rely on IMPLICIT synchronisation, and say so once. */
		if (!p->logged_implicit_sync) {
			p->logged_implicit_sync = true;
			registro_dice(AREA,
			              "⚠ wlroots: the fence inside the DMA-BUF cannot be extracted "
			              "(DMA_BUF_IOCTL_EXPORT_SYNC_FILE: %s) — from here we rely "
			              "on IMPLICIT synchronisation alone between compositor and "
			              "encoder.  `[?]` If the desktop shows half-drawn rows, "
			              "it is THIS line",
			              g_strerror(errno));
		}
		return true;
	}
	report->explicit_wait = true;
	stays = (expiry - before) / 1000;
	pfd.fd = sf.fd;
	pfd.events = POLLIN;
	do {
		r = poll(&pfd, 1, stays > 0 ? (int)stays : 0);
	} while (r < 0 && errno == EINTR);
	close(sf.fd);
	report->gpu_wait_us = (uint64_t)(g_get_monotonic_time() - before);
	if (r <= 0) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "the compositor said «ready» but the blit on the GPU did not finish "
		            "before the deadline (%.1f ms waiting for the fence) — the frame "
		            "stays in progress",
		            report->gpu_wait_us / 1000.0);
		return false;
	}
	return true;
}

/* ⭐ The delivery of a card frame: the slab goes IN HAND. */
static void card_delivery(WlrStage *p, WlrFrame *report)
{
	WlrSlab *l = &p->slabs[p->round_slab];

	p->failed_in_a_row = 0;
	l->state = SLAB_IN_HAND;
	p->round_slab = -1;

	report->on_card = true;
	report->pixel = NULL;
	report->width = l->width;
	report->height = l->height;
	report->stride = l->stride;
	/* ⛔ The DRM fourcc of the `linux_dmabuf` event, as it is: it does NOT go
	 *    through `shm_a_drm()` (defect 1). */
	report->fmt = l->fmt;
	report->byte = (gsize)l->stride * l->height;
	report->fd = l->fd;
	report->offset = l->offset;
	report->modifier = l->modifier;
	report->generation = p->generation;
	report->slab = l;
	report->seconds = p->f_seconds;
	report->nanoseconds = p->f_nanoseconds;
	/* ⚠ `[R]` On the card the compositor sends `flags 0`: the blit already
	 *   writes upright.  What it said is delivered anyway. */
	report->y_inverted = p->y_inverted;

	if (!p->card_format_logged) {
		char name[5];

		p->card_format_logged = true;
		memcpy(name, &l->fmt, 4);
		name[4] = 0;
		registro_dice(AREA,
		              "⭐ wlroots: the FIRST frame from the CARD — «%s» %ux%u stride "
		              "%u, linear slab, %s",
		              name, l->width, l->height, l->stride,
		              report->explicit_wait
		                  ? "fence extracted from the DMA-BUF and waited on"
		                  : "⚠ without a fence: implicit synchronisation");
	}
}

static void card_close(WlrStage *p)
{
	if (!p->card_born)
		return;
	for (unsigned i = 0; i < WLR_SLABS; i++)
		slab_drop(p, &p->slabs[i]);
	if (p->gbm)
		gbm_device_destroy(p->gbm);
	if (p->drm_fd >= 0)
		close(p->drm_fd);
	g_free(p->node);
	p->node = NULL;
	p->card_born = p->card = false;
}

/*
 * Closes the frame in progress.  `copy_alive` = the copy had started and
 * neither `ready` nor `failed` has arrived: the buffer is not reused.
 *
 * ⭐ And the frame's slab, if there was one and it was NOT delivered (dropped
 *    wire, `failed`): rule 2, it is dirty.  ⚠ A delivered slab already has
 *    `round_slab = -1`, and is not touched here.
 */
static void close_frame(WlrStage *p, bool copy_alive)
{
	if (p->frame)
		zwlr_screencopy_frame_v1_destroy(p->frame);
	p->frame = NULL;
	if (card_in_round(p)) {
		slab_returns_free(p, &p->slabs[p->round_slab], true);
		p->round_slab = -1;
	} else if (copy_alive) {
		p->buffer_dirty = true;
	}
	p->copy_started = false;
	p->duplicate_with_damage = false;
}

/* ========================================================================= */
/* ⭐⭐ THE POINTER PROBE — the true shape on labwc (XFCE and LXQt).          */
/* ========================================================================= */

/*
 * ⛔ THE FACT `[M]`: headless labwc has no cursor plane — it draws the pointer
 *    in software INSIDE the output buffer, and screencopy has no channel for
 *    its shape.  ⭐ But the encoded theme (`shape.h`) makes sure that under
 *    the hotspot there is ONE opaque pixel of a colour that belongs only to
 *    that shape.  ⇒ Looking at it is enough.
 *
 * ⭐ HOW IT IS LOOKED AT: `capture_output_region` of 3x3 around the point, in
 *    a 36-byte `wl_shm`, after every pointer gesture.  3x3 and not 1x1
 *    because the point in output coordinates is fractional (the virtual
 *    pointer is normalised) and `[?]` how wlroots brings it to the pixel I
 *    have not read: with three pixels per side it does not matter.  The
 *    CENTRE is looked at, then the neighbours.
 *
 * ⛔ THE THREE RULES:
 *   1. ONLY ONE in flight.  If the pointer moves while one is in flight, only
 *      the LAST position is remembered, and it is relaunched when the first
 *      comes back (coalescing): at a 60 Hz hand, 60 probes do not queue up.
 *   2. The copy is `copy`, never `copy_with_damage`: wlroots serves it at the
 *      next commit of the output, and the pointer movement causes one anyway
 *      (the software cursor is damage).
 *   3. ⭐ THE TAIL PROBE.  `[R]` the client changes shape AFTER receiving the
 *      `enter` — that is AFTER the movement that caused it — and the probe of
 *      that movement can come back before the client has answered.
 *      ⇒ With the hand still, PROBE_TAIL_US after the last one, one more is
 *      sent, only once.  Without it, whoever stops on an edge with the first
 *      gesture would keep the arrow.
 *
 * ⛔ THE THREAD: everything runs on the thread of the child's loop — the
 *    request starts from `wlr_probe_pointer` (after the gesture injection),
 *    the events are pumped by `wlr_frame` (the same pump as the stream),
 *    and the shape is collected by `wlr_probe_shape` (from `capture_take`).
 *    ⇒ No lock, and no delivery from inside a `libwayland` callback.
 *
 * ⚠ THE SPACE: the region is in OUTPUT coordinates; the child passes the
 *   coordinates of its canvas, and they are scaled as wlroots does with the
 *   virtual pointer (`motion_absolute` is normalised).  `[?]` scale 1:
 *   `wl_output` says the scale, it is not read here, and in the boxes it is 1.
 * ⚠ THE PIXELS: the format is given by the `buffer` event (wl_shm numbering).
 *   `[M]` labwc gives `XBGR8888`, that is R G B x in memory; ARGB/XRGB are
 *   B G R A.  The alpha of the output buffer means nothing (the output is
 *   opaque): 0xFF is passed, and the check is done by exact green and blue.
 * ⚠ THE COST: every probe is a 3x3 read from the compositor's renderer.
 *   `[M]` 24 Sep 2026, rete14-lxqt (Intel UHD 770, canvas 1344x870), pointer
 *   moved at ~55 Hz for 30 s over qterminal, two rounds per case:
 *       no probe         labwc 4.9-5.1%   child 11.2%   painted 55.1-55.3/s
 *       probe at 60 Hz   labwc 6.3-6.4%   child 11.6-11.8%   55.0-55.2/s
 *       probe at 30 Hz   labwc 5.7%       child 11.6-11.7%   55.1-55.3/s
 *   ⇒ +1.4 points of labwc CPU (+0.5 for the child), frames unchanged:
 *     below the 2-point threshold, and the thinning stays OFF.  If one day
 *     it were needed: MIN_PROBE_US 33333 is the 30 Hz measured above.
 */

/* ⭐ How long after the last probe the tail probe is sent. */
#define PROBE_TAIL_US (120 * 1000)
/* ⚠ The thinning: 0 = one per gesture (coalescing).  See the cost, above. */
#define MIN_PROBE_US 0

static void probe_launch(WlrStage *p, int32_t x, int32_t y);

static void probe_close_frame(WlrStage *p)
{
	if (p->s_frame)
		zwlr_screencopy_frame_v1_destroy(p->s_frame);
	p->s_frame = NULL;
	p->s_seen_buffer = p->s_copy_started = false;
}

/*
 * The bytes of a probe pixel, according to the format; 0 = it cannot be read.
 * ⛔ `[M]` 6 Oct 2026, NVIDIA (labwc 0.9.3, Ubuntu 26.04): for the 3x3 region
 *    labwc offers a **3-byte** format (stride 9) — the «stride ≥ w×4» ceiling
 *    refused it, the probe stayed without a buffer and the pointer shape never
 *    changed (F-005 red on LXQt).  On Intel and Radeon it offers XRGB8888.
 */
static unsigned probe_bpp(uint32_t shm)
{
	switch (shm) {
	case WL_SHM_FORMAT_ARGB8888:
	case WL_SHM_FORMAT_XRGB8888:
	case WL_SHM_FORMAT_ABGR8888:
	case WL_SHM_FORMAT_XBGR8888:
		return 4;
	case WL_SHM_FORMAT_RGB888:
	case WL_SHM_FORMAT_BGR888:
		return 3;
	default:
		return 0;
	}
}

/* The probe's buffer: it is remade only if the compositor asks for another one. */
static bool probe_buffer(WlrStage *p)
{
	struct wl_shm_pool *pool;
	gsize byte = (gsize)p->s_f_stride * p->s_f_a;

	if (p->s_buffer && p->s_b_l == p->s_f_l && p->s_b_a == p->s_f_a &&
	    p->s_b_stride == p->s_f_stride && p->s_b_shm == p->s_f_shm)
		return true;
	if (p->s_buffer)
		wl_buffer_destroy(p->s_buffer);
	p->s_buffer = NULL;
	if (p->s_pixel)
		munmap(p->s_pixel, p->s_byte);
	p->s_pixel = NULL;
	if (p->s_fd >= 0)
		close(p->s_fd);
	p->s_fd = -1;
	/* ⛔ A ceiling: the region is 3x3, and a compositor that asks for more is
	 *    not answering this question. */
	if (byte == 0 || byte > 4096 || probe_bpp(p->s_f_shm) == 0 ||
	    p->s_f_stride < p->s_f_l * probe_bpp(p->s_f_shm))
		return false;
	p->s_fd = memfd_create("remotix-sonda", MFD_CLOEXEC);
	if (p->s_fd < 0 || ftruncate(p->s_fd, (off_t)byte) != 0)
		return false;
	p->s_pixel = mmap(NULL, byte, PROT_READ | PROT_WRITE, MAP_SHARED, p->s_fd, 0);
	if (p->s_pixel == MAP_FAILED) {
		p->s_pixel = NULL;
		return false;
	}
	p->s_byte = byte;
	pool = wl_shm_create_pool(p->shm, p->s_fd, (int32_t)byte);
	p->s_buffer = wl_shm_pool_create_buffer(pool, 0, (int32_t)p->s_f_l, (int32_t)p->s_f_a,
	                                        (int32_t)p->s_f_stride, p->s_f_shm);
	wl_shm_pool_destroy(pool);
	p->s_b_l = p->s_f_l;
	p->s_b_a = p->s_f_a;
	p->s_b_stride = p->s_f_stride;
	p->s_b_shm = p->s_f_shm;
	return true;
}

/* The end of a probe (returned or failed): if one is waiting, it starts. */
static void probe_next(WlrStage *p)
{
	probe_close_frame(p);
	if (p->s_pending && g_get_monotonic_time() - p->s_last_started >= MIN_PROBE_US) {
		p->s_pending = false;
		probe_launch(p, p->s_wait_x, p->s_wait_y);
	}
}

static void probe_start(WlrStage *p)
{
	if (p->s_copy_started)
		return;
	if (!probe_buffer(p)) {
		if (!p->s_failed_logged) {
			p->s_failed_logged = true;
			registro_dice(AREA, "⚠ wlroots: the pointer probe has no buffer "
			                    "(%ux%u stride %u): the shape is not looked at, and the client "
			                    "keeps its arrow",
			              p->s_f_l, p->s_f_a, p->s_f_stride);
			registro_dice(AREA, "   (wl_shm format of the probe: 0x%08x)", p->s_f_shm);
		}
		p->s_count.failures++;
		probe_next(p);
		return;
	}
	zwlr_screencopy_frame_v1_copy(p->s_frame, p->s_buffer);
	p->s_copy_started = true;
}

static void probe_buffer_ev(void *data, struct zwlr_screencopy_frame_v1 *f, uint32_t fmt,
                            uint32_t l, uint32_t a, uint32_t stride)
{
	WlrStage *p = data;

	p->s_seen_buffer = true;
	p->s_f_shm = fmt;
	p->s_f_l = l;
	p->s_f_a = a;
	p->s_f_stride = stride;
	/* ⚠ Below v3 `buffer_done` does not exist: this is the only offer. */
	if (zwlr_screencopy_frame_v1_get_version(f) < 3)
		probe_start(p);
}

static void probe_buffer_done(void *data, struct zwlr_screencopy_frame_v1 *f)
{
	WlrStage *p = data;

	if (p->s_seen_buffer)
		probe_start(p);
}

/*
 * A probe pixel ⇒ B G R, according to the declared format.  FALSE = a
 * format that is not read here (said once, and the probe turns off).
 */
static bool probe_bgr(uint32_t shm, const uint8_t *q, uint8_t *b, uint8_t *g, uint8_t *r)
{
	switch (shm) {
	case WL_SHM_FORMAT_ARGB8888:
	case WL_SHM_FORMAT_XRGB8888:
		*b = q[0], *g = q[1], *r = q[2];
		return true;
	case WL_SHM_FORMAT_ABGR8888:
	case WL_SHM_FORMAT_XBGR8888:
		*r = q[0], *g = q[1], *b = q[2];
		return true;
	/* DRM: RGB888 = [23:0] R:G:B little endian ⇒ in memory B, G, R */
	case WL_SHM_FORMAT_RGB888:
		*b = q[0], *g = q[1], *r = q[2];
		return true;
	case WL_SHM_FORMAT_BGR888:
		*r = q[0], *g = q[1], *b = q[2];
		return true;
	default:
		return false;
	}
}

static void probe_ready(void *data, struct zwlr_screencopy_frame_v1 *f, uint32_t sa,
                         uint32_t sb, uint32_t ns)
{
	WlrStage *p = data;
	const uint8_t *px = p->s_pixel;
	/* ⭐ The centre of the region, in buffer pixels: at the edge of the output
	 *    the region is cut, and the centre moves with it. */
	int32_t cx = p->s_x - MAX(p->s_x - 1, 0), cy = p->s_y - MAX(p->s_y - 1, 0);
	int found_at = -1;
	uint8_t b = 0, g = 0, r = 0;

	p->s_count.returned++;
	if (!px) {
		probe_next(p);
		return;
	}
	if (!probe_bgr(p->s_f_shm, px, &b, &g, &r)) {
		if (!p->s_format_logged) {
			p->s_format_logged = true;
			registro_dice(AREA,
			              "⛔ wlroots: the pointer probe receives wl_shm format "
			              "0x%08x, which is not read here: the probe TURNS OFF, and the "
			              "client keeps its arrow",
			              p->s_f_shm);
		}
		p->s_off = true;
		probe_close_frame(p);
		return;
	}
	/* ⭐ First the centre, then the neighbours — `shape_from_pixel` is exact to
	 *    the byte, and a neighbour of another colour is never one of our shapes. */
	for (int cur_round = 0; cur_round < 2 && found_at < 0; cur_round++)
		for (uint32_t y = 0; y < p->s_f_a && found_at < 0; y++)
			for (uint32_t x = 0; x < p->s_f_l && found_at < 0; x++) {
				bool center = (int32_t)x == cx && (int32_t)y == cy;

				if (center != (cur_round == 0))
					continue;
				probe_bgr(p->s_f_shm,
				          px + (gsize)y * p->s_f_stride + x * probe_bpp(p->s_f_shm), &b,
				          &g, &r);
				found_at = shape_from_pixel(b, g, r, 0xFF);
				if (found_at >= 0 && !center)
					p->s_count.from_neighbors++;
			}
	if (found_at < 0) {
		/* ⚠ None of our colours: an application that hides the pointer, or
		 *   that draws a surface of its own.  The previous shape is kept. */
		p->s_count.ignote++;
		if (!p->s_unknown_logged) {
			p->s_unknown_logged = true;
			registro_dice(AREA,
			              "⚠ wlroots: under the pointer (%d,%d) no colour of the encoded "
			              "theme: the previous shape is kept.  The line is not "
			              "repeated; the count is in the closing line",
			              p->s_x, p->s_y);
		}
	} else if (found_at != p->s_shape) {
		p->s_shape = found_at;
		p->s_new = found_at;
		p->s_count.changes++;
	}
	probe_next(p);
}

static void probe_failed(void *data, struct zwlr_screencopy_frame_v1 *f)
{
	WlrStage *p = data;

	p->s_count.failures++;
	probe_next(p);
}

static void probe_flags(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t flags) {}
static void probe_damage(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t x, uint32_t y,
                        uint32_t l, uint32_t a) {}
static void probe_dmabuf(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t fmt,
                         uint32_t l, uint32_t a) {}

/* ⛔ ALL the events have a function: `libwayland` calls without looking,
 *    and a hole here is a jump to NULL at the first version that sends it. */
static const struct zwlr_screencopy_frame_v1_listener PROBE_LISTENER = {
	.buffer = probe_buffer_ev,
	.flags = probe_flags,
	.ready = probe_ready,
	.failed = probe_failed,
	.damage = probe_damage,
	.linux_dmabuf = probe_dmabuf,
	.buffer_done = probe_buffer_done,
};

static void probe_launch(WlrStage *p, int32_t x, int32_t y)
{
	int32_t rx = MAX(x - 1, 0), ry = MAX(y - 1, 0);
	int32_t rl = MIN(x + 2, (int32_t)p->width) - rx;
	int32_t ra = MIN(y + 2, (int32_t)p->height) - ry;

	if (rl <= 0 || ra <= 0)
		return;
	p->s_x = x;
	p->s_y = y;
	p->s_seen_buffer = p->s_copy_started = false;
	p->s_frame = zwlr_screencopy_manager_v1_capture_output_region(p->manager, 1, p->output,
	                                                             rx, ry, rl, ra);
	if (!p->s_frame) {
		p->s_count.failures++;
		return;
	}
	zwlr_screencopy_frame_v1_add_listener(p->s_frame, &PROBE_LISTENER, p);
	p->s_count.launched++;
	p->s_last_started = g_get_monotonic_time();
	p->s_tail_at = p->s_last_started + PROBE_TAIL_US;
	/* ⭐ Straight onto the wire: the stream's pump runs within 8 ms, and the
	 *    shape arrives sooner if the request leaves now.  ⚠ EAGAIN is not a
	 *    fault: it leaves with the pump's next `flush`. */
	wl_display_flush(p->display);
}

void wlr_probe_pointer(WlrStage *p, uint32_t x, uint32_t y, uint32_t l, uint32_t a)
{
	int32_t ux, uy;

	if (!p || p->s_off || !p->manager || !p->output || !p->shm || l == 0 || a == 0 ||
	    p->width == 0 || p->height == 0)
		return;
	/* ⭐ From the canvas to the output, as wlroots does with the virtual pointer. */
	if (x >= l)
		x = l - 1;
	if (y >= a)
		y = a - 1;
	ux = (int32_t)((uint64_t)x * p->width / l);
	uy = (int32_t)((uint64_t)y * p->height / a);
	p->s_count.asked++;
	p->s_queue_done = false;
	if (p->s_frame || (MIN_PROBE_US > 0 &&
	                   g_get_monotonic_time() - p->s_last_started < MIN_PROBE_US)) {
		/* ⭐ coalescing: only the LAST position is remembered */
		p->s_pending = true;
		p->s_wait_x = ux;
		p->s_wait_y = uy;
		return;
	}
	probe_launch(p, ux, uy);
}

int wlr_probe_shape(WlrStage *p)
{
	int new_one;

	if (!p || p->s_off)
		return -1;
	/* ⭐ the tail probe (rule 3), and the one left behind by the thinning:
	 *    they start from here, which the child's loop always calls */
	if (!p->s_frame) {
		gint64 now = g_get_monotonic_time();

		if (p->s_pending && now - p->s_last_started >= MIN_PROBE_US) {
			p->s_pending = false;
			probe_launch(p, p->s_wait_x, p->s_wait_y);
		} else if (!p->s_pending && !p->s_queue_done && p->s_count.launched > 0 &&
		           now >= p->s_tail_at) {
			p->s_queue_done = true;
			p->s_count.of_queue++;
			probe_launch(p, p->s_x, p->s_y);
		}
	}
	new_one = p->s_new;
	p->s_new = -1;
	return new_one;
}

void wlr_probe_counts(const WlrStage *p, WlrProbeCounts *report)
{
	if (report)
		*report = p ? p->s_count : (WlrProbeCounts){ 0 };
}

/* ------------------------------------------------------------------------- */

WlrStage *wlr_open(GError **mistake)
{
	return wlr_open_on(g_getenv("WAYLAND_DISPLAY"), mistake);
}

WlrStage *wlr_open_on(const char *name, GError **mistake)
{
	WlrStage *p = g_new0(WlrStage, 1);

	p->fd = -1;
	p->s_fd = -1;
	p->s_shape = p->s_new = -1;
	p->force_full = true; /* the first round: whoever attaches must see at once */
	/* ⛔ The card's descriptors at -1 AT ONCE: the zero of `g_new0` is
	 *    standard input, and a mistaken close would close it. */
	p->drm_fd = -1;
	p->round_slab = -1;
	for (unsigned i = 0; i < WLR_SLABS; i++)
		p->slabs[i].fd = -1;
	p->heads = g_ptr_array_new_with_free_func(free_head);
	p->display = wl_display_connect(name);
	if (!p->display && !name) {
		for (int i = 0; i < 10 && !p->display; i++) {
			g_autofree char *try_login = g_strdup_printf("wayland-%d", i);

			p->display = wl_display_connect(try_login);
			if (p->display)
				registro_dice(AREA,
				              "wlroots: WAYLAND_DISPLAY was not set, found «%s» "
				              "in XDG_RUNTIME_DIR", try_login);
		}
	}
	if (!p->display) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no Wayland compositor reachable in XDG_RUNTIME_DIR=%s",
		            g_getenv("XDG_RUNTIME_DIR") ?: "(not set)");
		wlr_close(p);
		return NULL;
	}

	p->registry = wl_display_get_registry(p->display);
	wl_registry_add_listener(p->registry, &REGISTRY_LISTENER, p);
	/* ⚠ TWO rounds, not one: the first brings the globals, the second the
	 *   events the globals send as soon as they are bound.  ⛔ And with a
	 *   ceiling (defect 3). */
	if (!cur_round(p, 2.0, mistake) || !cur_round(p, 2.0, mistake)) {
		wlr_close(p);
		return NULL;
	}

	if (!p->manager) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "the compositor does not announce zwlr_screencopy_manager_v1: on this "
		            "desktop capture does not go through here");
		wlr_close(p);
		return NULL;
	}
	if (!p->shm) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "the compositor does not announce wl_shm: I have nowhere to have the "
		            "pixels written");
		wlr_close(p);
		return NULL;
	}
	if (!p->output) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "the compositor announces no wl_output: there is nothing to "
		            "capture (the session is alive but without a screen?)");
		wlr_close(p);
		return NULL;
	}

	registro_dice(AREA,
	              "⭐ wlroots: capture ready on output «%s», %ux%u — ⚠ and the size is "
	              "the one the output HAS, not the one asked for",
	              p->output_name ?: "unnamed", p->width, p->height);
	return p;
}

void wlr_measure(const WlrStage *stage, uint32_t *width, uint32_t *height)
{
	if (width)
		*width = stage ? stage->width : 0;
	if (height)
		*height = stage ? stage->height : 0;
}

const char *wlr_output_name(const WlrStage *stage)
{
	return stage && stage->output_name ? stage->output_name : "";
}

void wlr_force_full(WlrStage *stage)
{
	if (stage)
		stage->force_full = true;
}

void wlr_counts(const WlrStage *stage, WlrCounts *report)
{
	if (report)
		*report = stage ? stage->counts : (WlrCounts){ 0 };
}

WlrSizeOutcome wlr_ask_size(WlrStage *stage, uint32_t width, uint32_t height,
                                 double wait_s, GError **mistake)
{
	return wlr_ask_size_hz(stage, width, height, 0, wait_s, mistake);
}

WlrSizeOutcome wlr_ask_size_hz(WlrStage *stage, uint32_t width, uint32_t height,
                                    int32_t millihertz, double wait_s, GError **mistake)
{
	struct zwlr_output_configuration_v1 *conf;
	struct zwlr_output_configuration_head_v1 *ct;
	Head *our = NULL;
	gint64 expiry;

	g_return_val_if_fail(stage != NULL, WLR_SIZE_IMPOSSIBLE);

	for (guint i = 0; stage->heads && i < stage->heads->len; i++) {
		Head *t = g_ptr_array_index(stage->heads, i);

		if (stage->output_name && g_strcmp0(t->name, stage->output_name) == 0)
			our = t;
	}
	if (!stage->handler || !our || !stage->known_serial) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED, "%s",
		            !stage->handler ? "the compositor does not announce "
		                              "zwlr_output_manager_v1: the size cannot be "
		                              "changed"
		            : !our ? "no head of the output manager has the name "
		                        "of the output being captured"
		                      : "the output manager has not yet sent its "
		                        "serial");
		return WLR_SIZE_IMPOSSIBLE;
	}
	if (stage->width == width && stage->height == height)
		return WLR_SIZE_UNCHANGED;

	stage->conf = CONF_IN_PROGRESS;
	conf = zwlr_output_manager_v1_create_configuration(stage->handler, stage->serial);
	zwlr_output_configuration_v1_add_listener(conf, &CONF_LISTENER, stage);

	/*
	 * ⛔ Defect 6: EVERY head must be configured, or the compositor closes the
	 *    wire with `unconfigured_head`.  ⇒ Ours takes the new size; the others
	 *    are reconfirmed exactly as they are — enabled ones stay enabled,
	 *    disabled ones stay disabled.  ⚠ Never disable one to simplify: on a
	 *    real machine it would be someone's screen.
	 */
	for (guint i = 0; i < stage->heads->len; i++) {
		Head *t = g_ptr_array_index(stage->heads, i);

		if (t == our) {
			ct = zwlr_output_configuration_v1_enable_head(conf, t->proxy);
			/* ⚠ `refresh = 0`: on an output without a screen the refresh rate is
			 *   a fiction, and zero means «you choose». */
			zwlr_output_configuration_head_v1_set_custom_mode(ct, (int32_t)width,
			                                                  (int32_t)height, millihertz);
		} else if (t->enabled) {
			zwlr_output_configuration_v1_enable_head(conf, t->proxy);
		} else {
			zwlr_output_configuration_v1_disable_head(conf, t->proxy);
		}
	}
	zwlr_output_configuration_v1_apply(conf);

	expiry = g_get_monotonic_time() + (gint64)(wait_s * 1e6);
	while (stage->conf == CONF_IN_PROGRESS) {
		if (!pump(stage, expiry, mistake)) {
			zwlr_output_configuration_v1_destroy(conf);
			return WLR_SIZE_REFUSED;
		}
		if (stage->conf == CONF_IN_PROGRESS && g_get_monotonic_time() >= expiry) {
			zwlr_output_configuration_v1_destroy(conf);
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "the compositor did not answer the size request within %.1f s "
			            "— and it is NOT a «no»: I do not know",
			            wait_s);
			return WLR_SIZE_REFUSED;
		}
	}
	zwlr_output_configuration_v1_destroy(conf);

	/* ⛔ Defect 4: three outcomes, three branches. */
	if (stage->conf == CONF_FAILED)
		return WLR_SIZE_REFUSED;
	if (stage->conf == CONF_CANCELLED)
		return WLR_SIZE_CANCELLED;

	/*
	 * ⛔⛔ AND HERE `stage->width = width` IS NOT WRITTEN: the compositor
	 *     said yes to the REQUEST, and that the output has changed will be said
	 *     by the `mode` event of the `wl_output` (`DECISIONS.md` §5.0-sexies).
	 *     One round, with a ceiling, to let it arrive.
	 */
	(void)cur_round(stage, wait_s, NULL);
	return WLR_SIZE_REQUESTED;
}

/* ------------------------------------------------------------------------- */
/* ⭐⭐ The card: the public functions. */

bool wlr_ask_card(WlrStage *p, GError **mistake)
{
	const char *come = NULL;
	gint64 expiry;

	g_return_val_if_fail(p != NULL, false);
	if (p->card)
		return true;
	if (p->card_born) {
		/* ⛔ It was born and turned off: it is not turned back on at every
		 *    request, or a compositor that refuses DMA-BUFs would make it
		 *    turn off and on again at every round. */
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "the card route had already turned off in this session");
		return false;
	}
	if (!p->dmabuf) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "the compositor does not announce zwp_linux_dmabuf_v1: I have no way "
		            "to give it a card buffer");
		return false;
	}
	if (zwlr_screencopy_manager_v1_get_version(p->manager) < 3) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "zwlr_screencopy_manager_v1 v%u: the `linux_dmabuf` event arrives "
		            "from v3",
		            zwlr_screencopy_manager_v1_get_version(p->manager));
		return false;
	}

	/* 1 · the node the compositor draws on — asked of it (v4).
	 *     ⛔ With a ceiling (defect 3): a feedback that does not close does not
	 *     stop the child, it only makes it take the node fallback, saying so. */
	if (p->dmabuf_version >= 4) {
		struct zwp_linux_dmabuf_feedback_v1 *fb =
		    zwp_linux_dmabuf_v1_get_default_feedback(p->dmabuf);

		zwp_linux_dmabuf_feedback_v1_add_listener(fb, &FEEDBACK_LISTENER, p);
		expiry = g_get_monotonic_time() + 2 * G_USEC_PER_SEC;
		while (!p->feedback_finished) {
			if (!pump(p, expiry, mistake)) {
				zwp_linux_dmabuf_feedback_v1_destroy(fb);
				return false;
			}
			if (!p->feedback_finished && g_get_monotonic_time() >= expiry)
				break;
		}
		zwp_linux_dmabuf_feedback_v1_destroy(fb);
	}
	if (p->main_known) {
		p->node = node_from_device(p->main);
		come = "stated by the compositor (`main_device`)";
	}
	if (!p->node) {
		p->node = node_as_session();
		come = "⚠ NOT stated by the compositor: taken with the rule of `session.c` "
		       "(BIOS primary card, else lowest PCI address), the same as WLR_RENDER_DRM_DEVICE";
	}
	if (!p->node) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no /dev/dri/renderD* node on which to allocate the card buffer");
		return false;
	}

	/* 2 · the node opens and `gbm` is born */
	p->drm_fd = open(p->node, O_RDWR | O_CLOEXEC);
	if (p->drm_fd < 0) {
		g_set_error(mistake, G_IO_ERROR, g_io_error_from_errno(errno), "%s: %s", p->node,
		            g_strerror(errno));
		g_clear_pointer(&p->node, g_free);
		return false;
	}
	p->gbm = gbm_create_device(p->drm_fd);
	if (!p->gbm) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "gbm_create_device on %s did not succeed", p->node);
		close(p->drm_fd);
		p->drm_fd = -1;
		g_clear_pointer(&p->node, g_free);
		return false;
	}
	for (unsigned i = 0; i < WLR_SLABS; i++) {
		memset(&p->slabs[i], 0, sizeof p->slabs[i]);
		p->slabs[i].fd = -1;
	}
	/* ⚠ If there is already a pending frame, its `copy` (if started) goes to
	 *   memory: `round_slab` stays -1 and the card starts from the next one. */
	p->round_slab = -1;
	p->card_born = true;
	p->card = true;
	registro_dice(AREA,
	              "⭐ wlroots: CARD route on — the slabs (%d, LINEAR "
	              "DMA-BUFs) are allocated on %s, %s; gbm backend «%s».  ⚠ Every "
	              "frame says by itself where it ended up: the route asked for is not the "
	              "route taken",
	              WLR_SLABS, p->node, come, gbm_device_get_backend_name(p->gbm));
	return true;
}

bool wlr_on_card(const WlrStage *p)
{
	return p && p->card;
}

void wlr_release(WlrStage *p, void *slab)
{
	WlrSlab *l = slab;

	if (!p || !l)
		return;
	/* ⛔ The pointer is CHECKED: it must be one of our slabs.  A hold from
	 *    another stage touches nothing here. */
	if (l < &p->slabs[0] || l >= &p->slabs[WLR_SLABS])
		return;
	/* ⛔ Only a slab IN HAND becomes free again: one returned twice is found
	 *    FREE (or IN FLIGHT, if it has already left again) and nothing happens.
	 *    ⚠ Never one IN FLIGHT: that one is closed by its frame. */
	if (l->state != SLAB_IN_HAND)
		return;
	slab_returns_free(p, l, false);
}

void wlr_cpu_read(int fd, bool start)
{
	struct dma_buf_sync s = {
		.flags = (start ? DMA_BUF_SYNC_START : DMA_BUF_SYNC_END) | DMA_BUF_SYNC_READ,
	};

	if (fd < 0)
		return;
	/* ⚠ If it fails there is nothing better to do than read anyway: the CPU
	 *   read here is diagnostic (the first frame), not product.  ⛔ And the
	 *   loop has a ceiling: only EINTR/EAGAIN, never anything else. */
	for (int i = 0; i < 100 && ioctl(fd, DMA_BUF_IOCTL_SYNC, &s) != 0 &&
	                (errno == EINTR || errno == EAGAIN);
	     i++)
		;
}

WlrOutcome wlr_frame(WlrStage *stage, double wait_s, WlrFrame *report, GError **mistake)
{
	gint64 expiry;

	g_return_val_if_fail(stage != NULL, WLR_FRAME_BROKEN);
	g_return_val_if_fail(report != NULL, WLR_FRAME_BROKEN);

	expiry = g_get_monotonic_time() + (gint64)(wait_s * 1e6);

	/*
	 * ⭐⭐ THE PENDING FRAME — defect 2 of the box at the top.
	 *
	 * If the previous call timed out, its request is STILL ALIVE: the
	 * compositor is serving it.  ⇒ Another one is not opened — that one is
	 * resumed.  Throwing it away meant discarding an almost ready frame and
	 * reallocating 8 MB, at every timeout, that is almost always.
	 */
	/*
	 * ⛔⛔ A DAMAGE COPY WAITING DOES NOT LET A FULL REQUEST THROUGH —
	 *     21 Sep 2026, `[M]` C4(xfce) «I could not look».
	 *
	 * `wlr_force_full()` raises the flag for the copy that STARTS; but if a
	 * damage copy is already in flight, on a still screen it never comes
	 * back, and the full copy never starts: the client attaching waits for a
	 * frame that does not arrive (C4: *«the after did not let itself be
	 * looked at: no frame in 8 s»*).  ⇒ The waiting one is abandoned — with
	 * the buffer marked, because the copy had started — and a full one is opened.
	 */
	if (stage->frame && stage->force_full && stage->duplicate_with_damage)
		close_frame(stage, true);

	if (!stage->frame) {
		stage->seen_buffer = stage->seen_buffer_done = false;
		stage->ready = stage->has_failed = false;
		stage->copy_started = stage->y_inverted = false;
		/* ⭐ the card: the offer belongs to THIS frame, and so does the slab */
		stage->card_offered = false;
		stage->round_slab = -1;
		stage->counts.requested++;
		/* ⭐ `overlay_cursor = 1`: on this family the pointer is INSIDE the
		 *    image, and there is no channel for its shape. */
		stage->frame = zwlr_screencopy_manager_v1_capture_output(stage->manager, 1,
		                                                         stage->output);
		if (!stage->frame) {
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
			            "capture_output did not produce a frame");
			return WLR_FRAME_BROKEN;
		}
		zwlr_screencopy_frame_v1_add_listener(stage->frame, &FRAME_LISTENER, stage);
	}

	for (;;) {
		if (stage->has_failed) {
			bool on_card = card_in_round(stage);

			/* ⚠ First it is closed (the slab becomes free, dirty), THEN it is
			 *   counted: if the count turns the card off, the slab is already
			 *   free and `card_turn_off` throws it away with the others. */
			close_frame(stage, false);
			stage->counts.failed++;
			if (on_card && ++stage->failed_in_a_row >= WLR_CARD_FAILED_MAX)
				card_turn_off(stage, "three `failed` in a row from the compositor on DMA-BUFs");
			return WLR_FRAME_FAILED;
		}
		if (stage->ready)
			break;
		/*
		 * The list of offers is closed and the copy has not started yet: the
		 * target is chosen and it starts.  ⭐ Only once per frame —
		 * `copy_started` survives the timeout together with `frame` and
		 * `round_slab`, so the call that resumes a pending frame does
		 * NOT choose another slab.
		 */
		if (list_closed(stage) && !stage->copy_started) {
			bool broken = false;
			struct wl_buffer *dove = card_destination(stage, &broken, mistake);

			if (broken) {
				/* ⛔ No `copy` has started: closing the frame here leaves
				 *    nothing dirty. */
				close_frame(stage, false);
				return WLR_FRAME_BROKEN;
			}
			if (!dove) {
				/* MEMORY: by default, or a fallback already declared */
				if (!prepare_buffer(stage, mistake)) {
					close_frame(stage, false);
					return WLR_FRAME_BROKEN;
				}
				dove = stage->buffer;
			}
			/* ⭐ With damage, if the compositor can do it and nobody has asked
			 *    for a full frame: see `force_full` in the structure. */
			if (!stage->force_full &&
			    zwlr_screencopy_frame_v1_get_version(stage->frame) >= 2) {
				zwlr_screencopy_frame_v1_copy_with_damage(stage->frame, dove);
				stage->duplicate_with_damage = true;
				if (!stage->logged_damage) {
					stage->logged_damage = true;
					registro_dice(AREA,
					              "⭐ wlroots: from here frames are asked WITH "
					              "DAMAGE — the compositor answers only when the "
					              "screen has changed, as with the GNOME and KDE push");
				}
			} else {
				zwlr_screencopy_frame_v1_copy(stage->frame, dove);
				stage->force_full = false;
			}
			stage->copy_started = true;
		}
		if (g_get_monotonic_time() >= expiry) {
			/* ⭐ Timed out, but the frame STAYS pending: the next call resumes
			 *    it.  It is not a fault and not a failure.
			 * ⛔ And the slab in flight STAYS in flight: it does not get dirty,
			 *    is not freed, another one is not chosen (the box at the top). */
			stage->counts.expired++;
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "the frame is not ready yet after %.3f s — it stays in progress",
			            wait_s);
			return WLR_FRAME_EXPIRED;
		}
		if (!pump(stage, expiry, mistake)) {
			/* ⛔ The wire dropped: if the copy had started, the buffer (or the
			 *    slab) is not reused. */
			close_frame(stage, stage->copy_started);
			return WLR_FRAME_BROKEN;
		}
	}

	/*
	 * ⭐ THE CARD DELIVERY: the fence, then the slab goes IN HAND.
	 *
	 * ⛔ If the fence does not fire in time the frame is NOT closed: it stays
	 *    pending with `ready` true and the slab IN FLIGHT, and the next call
	 *    re-enters the loop above, finds `ready`, and waits again on the
	 *    same fence.  No half blit delivered, no slab lost.
	 */
	if (card_in_round(stage)) {
		if (!card_wait_gpu(stage, &stage->slabs[stage->round_slab], expiry,
		                           report, mistake)) {
			stage->counts.expired++;
			return WLR_FRAME_EXPIRED;
		}
		card_delivery(stage, report); /* ⚠ resets `round_slab` */
		close_frame(stage, false);
		stage->counts.grabbed++;
		stage->counts.on_card++;
		return WLR_FRAME_TAKEN;
	}

	close_frame(stage, false);
	stage->counts.grabbed++;
	stage->counts.in_mem++;
	/* ⛔ The card fields are written here too, empty: `report` may come from
	 *    a round on the card, and an `fd` left there would be a slab that does
	 *    not belong to this frame. */
	report->on_card = false;
	report->fd = -1;
	report->offset = 0;
	report->modifier = DRM_FORMAT_MOD_LINEAR;
	report->generation = 0;
	report->slab = NULL;
	report->gpu_wait_us = 0;
	report->explicit_wait = false;
	report->width = stage->f_width;
	report->height = stage->f_height;
	report->stride = stage->f_stride;
	/* ⭐ Translated to DRM for whoever is downstream (defect 1). */
	report->fmt = shm_a_drm(stage->f_shm);
	report->pixel = stage->pixel;
	report->byte = stage->byte;
	if (report->fmt == FOURCC('B', 'G', '2', '4') || report->fmt == FOURCC('R', 'G', '2', '4'))
		widen_24(stage, report);
	report->seconds = stage->f_seconds;
	report->nanoseconds = stage->f_nanoseconds;
	report->y_inverted = stage->y_inverted;
	return WLR_FRAME_TAKEN;
}

/* ⭐ 24-bit pixels widened to 32 (see `largo` in the stage).  The extra
 *    byte is 0xff; the order of the three stays, and only the name changes:
 *    `BG24` → `XB24`, `RG24` → `XR24`. */
static void widen_24(WlrStage *p, WlrFrame *report)
{
	const uint32_t l = report->width, a = report->height;
	const gsize step = (gsize)l * 4u, needs = step * a;

	if (report->stride < l * 3u || (gsize)report->stride * a > report->byte)
		return; /* ⚠ a shape that does not add up: whoever is downstream reports the discard */
	if (p->largo_byte < needs) {
		g_free(p->largo);
		p->largo = g_malloc(needs);
		p->largo_byte = needs;
	}
	for (uint32_t y = 0; y < a; y++) {
		const uint8_t *q = (const uint8_t *)report->pixel + (gsize)y * report->stride;
		uint8_t *d = p->largo + (gsize)y * step;
		for (uint32_t x = 0; x < l; x++, q += 3, d += 4) {
			d[0] = q[0];
			d[1] = q[1];
			d[2] = q[2];
			d[3] = 0xff;
		}
	}
	report->fmt = report->fmt == FOURCC('B', 'G', '2', '4') ? FOURCC('X', 'B', '2', '4')
	                                                              : FOURCC('X', 'R', '2', '4');
	report->pixel = p->largo;
	report->byte = needs;
	report->stride = (uint32_t)step;
}

void wlr_close(WlrStage *stage)
{
	if (!stage)
		return;
	/* ⛔ Defect 7: everything that was created is destroyed. */
	if (stage->frame)
		zwlr_screencopy_frame_v1_destroy(stage->frame);
	/* ⭐ the probe: its frame before its buffer, like the stream */
	probe_close_frame(stage);
	if (stage->s_buffer)
		wl_buffer_destroy(stage->s_buffer);
	if (stage->s_pixel)
		munmap(stage->s_pixel, stage->s_byte);
	if (stage->s_fd >= 0)
		close(stage->s_fd);
	if (stage->buffer)
		wl_buffer_destroy(stage->buffer);
	if (stage->pixel)
		munmap(stage->pixel, stage->byte);
	g_free(stage->largo);
	if (stage->fd >= 0)
		close(stage->fd);
	/* ⭐ the slabs, `gbm`, the node — AFTER the frame, which could name one
	 *    in a `copy` */
	card_close(stage);
	if (stage->dmabuf)
		zwp_linux_dmabuf_v1_destroy(stage->dmabuf);
	if (stage->heads)
		g_ptr_array_free(stage->heads, TRUE);
	if (stage->handler)
		zwlr_output_manager_v1_destroy(stage->handler);
	if (stage->manager)
		zwlr_screencopy_manager_v1_destroy(stage->manager);
	if (stage->output)
		wl_output_destroy(stage->output);
	if (stage->shm)
		wl_shm_destroy(stage->shm);
	if (stage->registry)
		wl_registry_destroy(stage->registry);
	if (stage->display)
		wl_display_disconnect(stage->display);
	g_free(stage->output_name);
	g_free(stage);
}
