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
 *      `R G B x`.  ⇒ Here we TRANSLATE (wl_shm → DRM) and deliver; `figlio.c`
 *      reads the order and tells the encoder (`CODIFICATORE_PIXEL_RGBX`).
 *   2. ⛔ THE COPY THROWN AWAY AT EVERY TIMEOUT.  The child's loop waits 8 ms
 *      (`MOVIMENTO_ATTESA_S`) and the whole round costs 9-15: almost every
 *      call timed out AFTER `copy`, threw away the frame already in progress
 *      and reallocated 8 MB.  ⇒ Now the frame is PENDING: if the wait ends,
 *      the request stays alive and the next call resumes it.
 *   3. ⛔ THREE `wl_display_roundtrip` WITHOUT A CEILING: a stuck compositor
 *      stopped the child forever.  ⇒ `giro()`, with a deadline.
 *   4. ⛔ `failed` AND `cancelled` IN THE SAME BRANCH — the exact mistake that
 *      `DECISIONI.md` §5.0-sexies blames on wayvnc.  ⇒ Three separate outcomes.
 *   5. the output's head was found only if the names arrived in a precise
 *      order ⇒ all are kept, and the choice is made at request time;
 *   6. the configuration enabled a single head: with two outputs the
 *      protocol dies (`unconfigured_head`) ⇒ the others are reconfirmed as
 *      they are;
 *   7. the object leaks in `wlr_chiudi`.
 *
 * ===========================================================================
 * ⭐⭐ THE CARD ROUTE — 21 Sep 2026, behind `CATTURA_STRADA_SCHEDA`
 * ===========================================================================
 *
 * ⚠ Written first on the old draft (commit `d5d7129`) and CARRIED by hand
 *   onto this one: none of the seven defects above comes back in with it.
 *   The card speaks ITS OWN numbering (defect 1), lives inside the pending
 *   frame (defect 2) and never waits without a ceiling (defect 3).
 *
 * ⛔ Memory stays: it is the FALLBACK, and a DECLARED fallback.  If the card
 *    is asked for and memory arrives, the log says so with the reason, and
 *    every frame carries `sulla_scheda` — it is never deduced from the route
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
 *                              the compositor's loop (`STUDI.md` §xfce §4.4)
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
 *   downstream, until it comes back with `wlr_rendi()`).
 *
 *   1. ⛔ ONLY A FREE SLAB IS NAMED IN A `copy`.  A slab in hand becomes free
 *      again only with `wlr_rendi()` — in the product from
 *      `cattura_fermo_libera()`, which the loop calls AFTER
 *      `codificatore_comprimi_scheda()`, where `vaSyncSurface` says the GPU
 *      has FINISHED reading.  ⇒ «labwc copies into it again while the
 *      encoder reads it» is not avoided with a timing: it is impossible by
 *      construction.  If they are all in hand the frame stops, SAYING SO;
 *      none is recycled (`LEZIONI.md` §8).
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
 *     SAME frame (`palco->frame` is alive) with THE SAME slab
 *     (`lastra_del_giro` is kept).  A new `capture_output` starts only
 *     when `frame` is NULL, and `frame` goes back to NULL only when its slab
 *     is delivered or thrown away.  ⛔ And on timeout the slab does NOT get
 *     dirty: the old draft threw it away, and that was defect 2 in card form.
 *   · «A slab returned twice?»  ⇒ `wlr_rendi()` acts only on a slab IN HAND
 *     and brings it to FREE: a second call finds it FREE (or IN FLIGHT, if
 *     it has left again in the meantime) and does nothing; and
 *     `cattura_fermo_libera()` zeroes the hold after returning it.  ⚠ `[R]`
 *     The only uncovered case is a COPY of the hold kept by someone after
 *     the release: in `figlio.c` the hold is a local variable passed by
 *     address, and nobody copies it.
 *   · «Does the encoder read a slab while labwc copies into it again?»  ⇒
 *     Rule 1: a slab in hand is never named in a `copy`.
 *   · And the fence that does not fire in time after `ready`: the frame stays
 *     PENDING with `pronto` already true, the slab stays IN FLIGHT, and the
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
 *   ⚠ It costs: it is `us_attesa_gpu`, and it sits INSIDE the frame time.
 *   ⛔ If the ioctl is missing (kernel < 5.20) it is said once: from then on
 *      we rely on implicit synchronisation alone, and the line names it.
 *
 * ---------------------------------------------------------------------------
 * ⚠ THE TWO FORMAT NUMBERINGS — they do not mix (defect 1)
 *
 *   The `buffer` event speaks `wl_shm.format` (0 and 1 special) → `f_shm`, and
 *   is translated with `shm_a_drm()` ONLY for whoever is downstream.  The
 *   `linux_dmabuf` event speaks the true DRM fourcc → `o_scheda_formato`, and
 *   does NOT go through `shm_a_drm()`.  The slab is allocated EXACTLY in the
 *   format and size of that event: `[R]` wlroots, a different format or size
 *   is `invalid buffer` — a PROTOCOL ERROR, and the connection dies.
 *   ⭐ `[M]` labwc on the card gives `XRGB8888` (B G R x in memory): the order
 *     the encoder already reads.  If another one arrived, the card is
 *     skipped for that frame, saying so.
 */
#include "wlroots.h"
#include "vulkanvideo.h"

#include "forma.h"
#include "registro.h"

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

/* ⚠ The same area as `cattura.c` and `kwin.c`: whoever reads the log looks for
 *   the pixels under a single word, not under the name of the module that took them. */
#define AREA "cattura"

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
	char *nome;
	bool accesa;
} Testa;

static void allarga_24(WlrPalco *p, WlrFotogramma *fuori);

/* ⭐ How many slabs — see the box at the top, «the three rules». */
#define WLR_LASTRE 3

/* ⛔ How many `failed` IN A ROW on the card before turning it off: one can be
 *    the output changing under the round; three are a route that does not work. */
#define WLR_SCHEDA_FALLITI_MAX 3

/* ⚠ The ceiling for the birth of a slab (the answer to `create`).  ⛔ Not
 *   the frame wait: the child calls with 8 ms, and a slab that is not born
 *   within 8 ms the first time would turn the card off forever over a
 *   delay.  It happens three times per session (and at every size change). */
#define WLR_LASTRA_NASCITA_S 1.0

/*
 * ⛔⛔ PHASE 19 — THE SLAB IS BORN AT THE MAXIMUM CANVAS AND DOES NOT DIE ON A
 *      SIZE CHANGE (1 Oct 2026, the Radeon GPU hang on the Vulkan route).
 *
 *   Resizing is done by changing the `wl_buffer` (the size declared to the
 *   compositor), NOT the BO: the GBM slab is born `WLR_LASTRA_L x
 *   WLR_LASTRA_A` (= `RCP_TELA_L/A_MASSIMA` of `rcp.h`, the largest canvas
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
 *     Vulkan (`wlr_lastre_alla_tela_massima()`, decided in `figlio.c` before
 *     the stage): with VA-API the slabs of the right size stay.
 */
#define WLR_LASTRA_L 4096u
#define WLR_LASTRA_A 2304u

/* The default is FALSE: with VA-API (the Intel, where radeonsi/iHD are alone
 * in the process) the defect is not there, and 113 MB per session on an
 * integrated GPU are system RAM spent for nothing. */
static bool lastre_massime = false;

void wlr_lastre_alla_tela_massima(bool si)
{
	lastre_massime = si;
}

typedef enum {
	LASTRA_LIBERA = 0,
	LASTRA_IN_VOLO, /* named in the `copy` of the frame in progress    */
	LASTRA_IN_MANO  /* delivered: until it comes back with `wlr_rendi()` */
} LastraStato;

typedef struct {
	struct gbm_bo *bo;
	struct wl_buffer *buffer;
	int fd;
	uint32_t larghezza, altezza, stride, offset, formato; /* formato: DRM fourcc */
	uint32_t bo_larghezza, bo_altezza; /* the BO: the birth size (WLR_LASTRA_*) */
	uint64_t modificatore;
	LastraStato stato;
	bool sporca;
} WlrLastra;

typedef enum {
	CONF_IN_CORSO = 0,
	CONF_RIUSCITA,
	CONF_FALLITA,  /* `failed`: the compositor said NO               */
	CONF_ANNULLATA /* `cancelled`: the serial was old, try again     */
} ConfEsito;

struct WlrPalco {
	struct wl_display *display;
	struct wl_registry *registry;
	struct wl_shm *shm;
	struct zwlr_screencopy_manager_v1 *manager;
	struct wl_output *uscita;
	char *uscita_nome;

	/* the geometry the output declares — ⛔ the one it HAS, not the one wanted */
	uint32_t larghezza, altezza;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ THE OUTPUT SIZE — `zwlr_output_manager_v1`.
	 *
	 * ⛔ On this family the canvas is NOT negotiated with the stream: there is
	 *    no stream.  The size of the OUTPUT is changed, and then the frames
	 *    arrive that way.  ⇒ It is the thing that could not be done on KDE.
	 * ------------------------------------------------------------------ */
	struct zwlr_output_manager_v1 *gestore;
	GPtrArray *teste; /* of `Testa *` — ALL of them, not just ours (defect 5) */
	uint32_t serial;
	bool serial_noto;
	ConfEsito conf;

	/* the shared buffer, reused from one frame to the next */
	struct wl_buffer *buffer;
	void *pixel;
	gsize byte;
	int fd;
	uint32_t b_larghezza, b_altezza, b_stride, b_formato;
	/*
	 * ⛔⛔ THE DIRTY BUFFER.  If a frame is abandoned AFTER sending `copy`
	 *     and without waiting for its outcome (dropped wire), the compositor
	 *     may write into it later: reusing it would give an old frame among
	 *     the new ones — not an error, a flicker (`LEZIONI.md` §8).
	 *  ⚠ With the PENDING frame (defect 2) the timeout no longer dirties it:
	 *    the copy stays ours and we wait.  It remains only for the dropped wire.
	 */
	bool buffer_sporco;

	/* ------------------------------------------------------------------ *
	 * THE FRAME IN PROGRESS — ⭐ and it can survive a call.
	 * ------------------------------------------------------------------ */
	struct zwlr_screencopy_frame_v1 *frame;
	bool visto_buffer, visto_buffer_done, pronto, fallito, copia_partita, y_invertita;
	uint32_t f_shm; /* the format as wl_shm says it: needed by the buffer */
	uint32_t f_larghezza, f_altezza, f_stride;
	uint64_t f_secondi;
	uint32_t f_nanosecondi;

	bool detto_il_formato;
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
	/* ⭐ The modifiers the encoder can import (see `lastra_prepara`):
	 *    for the format `mod_formato`, asked once. */
	uint32_t mod_formato;
	uint64_t mod_ammessi[16];
	int mod_quanti;
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
	 *   client attaching, a §5.2 request): `forza_intero` makes the NEXT round
	 *   use `copy`, and `wlr_forza_intero()` sets it.  The very first round is
	 *   full too: whoever attaches must see at once.
	 */
	bool forza_intero, detto_il_danno;
	bool copia_col_danno; /* the copy in flight is `copy_with_damage` */
	/* ⭐ The damage DECLARED by the compositor, per frame (witness only,
	 *    with `--parlantina`): `[M]` 5 Oct 2026, NVIDIA + zero copy, the
	 *    compositor answers at 60/s on a still desktop — and the question is
	 *    whether it declares it changed everywhere or in a corner. */
	uint64_t danno_area_fotogramma, danno_area_somma;
	uint32_t danno_rett_fotogramma, danno_rett_somma, danno_fotogrammi, danno_interi;
	uint32_t danno_x, danno_y, danno_l, danno_a; /* the last rectangle */
	WlrConteggi conteggi;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ THE CARD ROUTE — the box at the top.
	 *
	 * ⛔ Everything below is valid ONLY if `scheda_nata`: before
	 *    `wlr_chiedi_la_scheda()` the fields are the zeros of `g_new0`, and
	 *    zero for a descriptor means standard input — hence the flag.
	 * ------------------------------------------------------------------ */
	struct zwp_linux_dmabuf_v1 *dmabuf;
	uint32_t dmabuf_versione;
	bool scheda_nata; /* node open, `gbm` created, slabs initialised */
	bool scheda;      /* ⭐ in force NOW                               */
	int drm_fd;
	struct gbm_device *gbm;
	char *nodo;
	/* the feedback's `main_device`: the node the compositor draws on */
	dev_t principale;
	bool principale_noto, feedback_finito;
	/* the card offer in THIS frame — ⛔ DRM fourcc, NOT wl_shm */
	bool offerto_scheda;
	uint32_t o_scheda_formato, o_scheda_l, o_scheda_a;
	WlrLastra lastre[WLR_LASTRE];
	unsigned prossima;
	/* ⭐ -1: the frame in progress goes (or will go) to memory.  ⛔ It survives
	 *    the timeout together with `frame`: it is the slab IN FLIGHT of THAT
	 *    frame, and the next call finds it again. */
	int lastra_del_giro;
	uint64_t generazione;
	unsigned falliti_di_fila;
	/* the creation of the `wl_buffer` (`zwp_linux_buffer_params_v1`) */
	struct wl_buffer *creato;
	bool params_finito, params_fallito;
	/* ⚠ the lines said only once */
	bool detto_senza_offerta, detto_formato_scheda, detta_sync_implicita;
	bool detto_il_formato_scheda;

	/* ------------------------------------------------------------------ *
	 * ⭐⭐ THE POINTER PROBE — the box above `wlr_sonda_puntatore`.
	 *
	 * ⛔ All its own: a frame, a buffer, a descriptor that are NOT those of
	 *    the stream.  The main stream does not know the probe exists.
	 * ------------------------------------------------------------------ */
	struct zwlr_screencopy_frame_v1 *s_frame; /* ONLY ONE in flight      */
	bool s_visto_buffer, s_copia_partita;
	uint32_t s_f_shm, s_f_l, s_f_a, s_f_stride;
	struct wl_buffer *s_buffer;
	void *s_pixel;
	int s_fd;
	gsize s_byte;
	uint32_t s_b_l, s_b_a, s_b_stride, s_b_shm;
	/* the position of the request IN FLIGHT, and the one to relaunch */
	int32_t s_x, s_y;
	bool s_in_attesa; /* ⭐ coalescing: only the LAST position is remembered */
	int32_t s_attesa_x, s_attesa_y;
	/* ⭐ the «tail» probe: one more, with the hand still — see the box */
	gint64 s_coda_a;
	bool s_coda_fatta;
	gint64 s_ultima_partita; /* for the thinning */
	int s_forma;             /* the last recognised shape, -1 = none     */
	int s_nuova;             /* to deliver to `wlr_sonda_forma`, or -1     */
	bool s_spenta;           /* the format cannot be read: said, and that's it */
	bool s_detto_formato, s_detta_ignota, s_detto_fallito;
	WlrSondaConteggi s_conto;
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
static bool pompa(WlrPalco *p, gint64 scadenza, GError **sbaglio)
{
	struct pollfd pfd;
	gint64 resta;
	int r;

	while (wl_display_prepare_read(p->display) != 0) {
		if (wl_display_dispatch_pending(p->display) < 0) {
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
			            "the wire to the compositor dropped (dispatch_pending)");
			return false;
		}
	}
	if (wl_display_flush(p->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(p->display);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "the wire to the compositor dropped (flush): %s", g_strerror(errno));
		return false;
	}

	resta = (scadenza - g_get_monotonic_time()) / 1000;
	if (resta < 0)
		resta = 0;
	pfd.fd = wl_display_get_fd(p->display);
	pfd.events = POLLIN;
	r = poll(&pfd, 1, (int)resta);
	if (r <= 0) {
		wl_display_cancel_read(p->display);
		if (r == 0)
			return true; /* timed out: the caller looks at the clock */
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno), "poll: %s",
		            g_strerror(errno));
		return false;
	}
	if (wl_display_read_events(p->display) < 0) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "the wire to the compositor dropped (read_events)");
		return false;
	}
	if (wl_display_dispatch_pending(p->display) < 0) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BROKEN_PIPE,
		            "the wire to the compositor dropped (dispatch)");
		return false;
	}
	return true;
}

static void giro_fatto(void *dati, struct wl_callback *cb, uint32_t t)
{
	*(bool *)dati = true;
}

static const struct wl_callback_listener ASCOLTO_GIRO = { .done = giro_fatto };

/*
 * ⭐ A round trip WITH A CEILING — in place of `wl_display_roundtrip()`.
 *
 * ⛔ Defect 3 of the box at the top: `wl_display_roundtrip()` has no ceiling,
 *    and it ran three times inside the child.  This does the same thing (a
 *    `sync` and we wait for its `done`: everything the compositor sent before
 *    has arrived) and stops at the deadline.
 */
static bool giro(WlrPalco *p, double attesa_s, GError **sbaglio)
{
	bool fatto = false;
	struct wl_callback *cb = wl_display_sync(p->display);
	gint64 scadenza = g_get_monotonic_time() + (gint64)(attesa_s * 1e6);

	wl_callback_add_listener(cb, &ASCOLTO_GIRO, &fatto);
	while (!fatto) {
		if (!pompa(p, scadenza, sbaglio)) {
			wl_callback_destroy(cb);
			return false;
		}
		if (!fatto && g_get_monotonic_time() >= scadenza) {
			wl_callback_destroy(cb);
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "the compositor did not answer a round trip "
			            "within %.1f s",
			            attesa_s);
			return false;
		}
	}
	wl_callback_destroy(cb);
	return true;
}

/* ------------------------------------------------------------------------- */
/* The output (wl_output). */

static void uscita_geometria(void *dati, struct wl_output *o, int32_t x, int32_t y, int32_t lf,
                             int32_t af, int32_t sub, const char *make, const char *model,
                             int32_t trasf)
{
}

static void uscita_modo(void *dati, struct wl_output *o, uint32_t flag, int32_t l, int32_t a,
                        int32_t refresh)
{
	WlrPalco *p = dati;

	/* ⛔ ONLY the CURRENT mode: an output may announce many. */
	if (flag & WL_OUTPUT_MODE_CURRENT) {
		p->larghezza = (uint32_t)l;
		p->altezza = (uint32_t)a;
	}
}

static void uscita_fine(void *dati, struct wl_output *o) {}
static void uscita_scala(void *dati, struct wl_output *o, int32_t scala) {}

static void uscita_nome(void *dati, struct wl_output *o, const char *nome)
{
	WlrPalco *p = dati;

	g_free(p->uscita_nome);
	p->uscita_nome = g_strdup(nome);
}

static void uscita_descrizione(void *dati, struct wl_output *o, const char *d) {}

static const struct wl_output_listener ASCOLTO_USCITA = {
	.geometry = uscita_geometria,
	.mode = uscita_modo,
	.done = uscita_fine,
	.scale = uscita_scala,
	.name = uscita_nome,
	.description = uscita_descrizione,
};

/* ------------------------------------------------------------------------- */
/* The output manager and its heads. */

/*
 * ⛔⛔ THE SERIAL, AND WHY THE LATEST IS ALWAYS KEPT.  A configuration created
 *     with an old serial is CANCELLED — and `cancelled` is not `failed`:
 *     it means «reality changed underneath», not «no».
 */
static void gestore_testa(void *dati, struct zwlr_output_manager_v1 *m,
                          struct zwlr_output_head_v1 *testa);

static void gestore_fine(void *dati, struct zwlr_output_manager_v1 *m, uint32_t serial)
{
	WlrPalco *p = dati;

	p->serial = serial;
	p->serial_noto = true;
}

static void gestore_finito(void *dati, struct zwlr_output_manager_v1 *m)
{
	WlrPalco *p = dati;

	zwlr_output_manager_v1_destroy(m);
	p->gestore = NULL;
}

static const struct zwlr_output_manager_v1_listener ASCOLTO_GESTORE = {
	.head = gestore_testa,
	.done = gestore_fine,
	.finished = gestore_finito,
};

static Testa *testa_di(WlrPalco *p, struct zwlr_output_head_v1 *proxy)
{
	for (guint i = 0; p->teste && i < p->teste->len; i++) {
		Testa *t = g_ptr_array_index(p->teste, i);

		if (t->proxy == proxy)
			return t;
	}
	return NULL;
}

static void testa_nome(void *dati, struct zwlr_output_head_v1 *proxy, const char *nome)
{
	Testa *t = testa_di(dati, proxy);

	/* ⭐ Defect 5: the name is KEPT, and the right head is chosen when it is
	 *    needed.  Before, it was compared here with the name of the `wl_output`,
	 *    and if that had not arrived yet the head was never found. */
	if (t) {
		g_free(t->nome);
		t->nome = g_strdup(nome);
	}
}

static void testa_accesa(void *dati, struct zwlr_output_head_v1 *proxy, int32_t accesa)
{
	Testa *t = testa_di(dati, proxy);

	if (t)
		t->accesa = accesa != 0;
}

static void testa_finita(void *dati, struct zwlr_output_head_v1 *proxy)
{
	WlrPalco *p = dati;
	Testa *t = testa_di(p, proxy);

	if (t)
		g_ptr_array_remove(p->teste, t); /* `libera_testa` frees it */
}

static void testa_descrizione(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void testa_misura_fisica(void *d, struct zwlr_output_head_v1 *t, int32_t l, int32_t a) {}
static void testa_modo(void *d, struct zwlr_output_head_v1 *t, struct zwlr_output_mode_v1 *m) {}
static void testa_modo_corrente(void *d, struct zwlr_output_head_v1 *t,
                                struct zwlr_output_mode_v1 *m) {}
static void testa_posizione(void *d, struct zwlr_output_head_v1 *t, int32_t x, int32_t y) {}
static void testa_trasformazione(void *d, struct zwlr_output_head_v1 *t, int32_t x) {}
static void testa_scala(void *d, struct zwlr_output_head_v1 *t, wl_fixed_t s) {}
static void testa_marca(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void testa_modello(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void testa_matricola(void *d, struct zwlr_output_head_v1 *t, const char *x) {}
static void testa_sincronia(void *d, struct zwlr_output_head_v1 *t, uint32_t x) {}

static const struct zwlr_output_head_v1_listener ASCOLTO_TESTA = {
	.name = testa_nome,
	.description = testa_descrizione,
	.physical_size = testa_misura_fisica,
	.mode = testa_modo,
	.enabled = testa_accesa,
	.current_mode = testa_modo_corrente,
	.position = testa_posizione,
	.transform = testa_trasformazione,
	.scale = testa_scala,
	.finished = testa_finita,
	.make = testa_marca,
	.model = testa_modello,
	.serial_number = testa_matricola,
	.adaptive_sync = testa_sincronia,
};

static void libera_testa(gpointer dati)
{
	Testa *t = dati;

	if (t->proxy)
		zwlr_output_head_v1_destroy(t->proxy);
	g_free(t->nome);
	g_free(t);
}

static void gestore_testa(void *dati, struct zwlr_output_manager_v1 *m,
                          struct zwlr_output_head_v1 *proxy)
{
	WlrPalco *p = dati;
	Testa *t = g_new0(Testa, 1);

	t->proxy = proxy;
	g_ptr_array_add(p->teste, t);
	zwlr_output_head_v1_add_listener(proxy, &ASCOLTO_TESTA, p);
}

static void conf_riuscita(void *dati, struct zwlr_output_configuration_v1 *c)
{
	((WlrPalco *)dati)->conf = CONF_RIUSCITA;
}

static void conf_fallita(void *dati, struct zwlr_output_configuration_v1 *c)
{
	((WlrPalco *)dati)->conf = CONF_FALLITA;
}

static void conf_annullata(void *dati, struct zwlr_output_configuration_v1 *c)
{
	((WlrPalco *)dati)->conf = CONF_ANNULLATA;
}

static const struct zwlr_output_configuration_v1_listener ASCOLTO_CONF = {
	.succeeded = conf_riuscita,
	.failed = conf_fallita,
	.cancelled = conf_annullata,
};

/* ------------------------------------------------------------------------- */
/* The registry of globals. */

/* ⚠ Below v4 the global sends `format` and `modifier` as soon as it is bound:
 *   they are listened to and dropped — the modifier is decided by us
 *   (LINEAR, the box at the top), not by the list. */
static void dmabuf_formato(void *d, struct zwp_linux_dmabuf_v1 *m, uint32_t f) {}
static void dmabuf_modificatore(void *d, struct zwp_linux_dmabuf_v1 *m, uint32_t f,
                                uint32_t alto, uint32_t basso) {}

static const struct zwp_linux_dmabuf_v1_listener ASCOLTO_DMABUF = {
	.format = dmabuf_formato,
	.modifier = dmabuf_modificatore,
};

static void registro_global(void *dati, struct wl_registry *reg, uint32_t nome,
                            const char *interfaccia, uint32_t versione)
{
	WlrPalco *p = dati;

	if (g_strcmp0(interfaccia, wl_shm_interface.name) == 0) {
		p->shm = wl_registry_bind(reg, nome, &wl_shm_interface, 1);
	} else if (g_strcmp0(interfaccia, zwlr_screencopy_manager_v1_interface.name) == 0) {
		uint32_t v = versione < 3 ? versione : 3;

		p->manager = wl_registry_bind(reg, nome, &zwlr_screencopy_manager_v1_interface, v);
	} else if (g_strcmp0(interfaccia, zwp_linux_dmabuf_v1_interface.name) == 0 &&
	           !p->dmabuf) {
		/* ⭐ The card route.  ⚠ At most v4 (`[M]` labwc gives it): it is the
		 *   one with `main_device`, that is the node the compositor draws on.
		 *   ⛔ It is always bound, even if the card is not asked for: binding
		 *   costs nothing and changes nothing. */
		p->dmabuf_versione = versione < 4 ? versione : 4;
		p->dmabuf = wl_registry_bind(reg, nome, &zwp_linux_dmabuf_v1_interface,
		                             p->dmabuf_versione);
		zwp_linux_dmabuf_v1_add_listener(p->dmabuf, &ASCOLTO_DMABUF, p);
	} else if (g_strcmp0(interfaccia, zwlr_output_manager_v1_interface.name) == 0) {
		uint32_t v = versione < 4 ? versione : 4;

		p->gestore = wl_registry_bind(reg, nome, &zwlr_output_manager_v1_interface, v);
		zwlr_output_manager_v1_add_listener(p->gestore, &ASCOLTO_GESTORE, p);
	} else if (g_strcmp0(interfaccia, wl_output_interface.name) == 0) {
		if (!p->uscita) {
			uint32_t v = versione < 4 ? versione : 4;

			p->uscita = wl_registry_bind(reg, nome, &wl_output_interface, v);
			wl_output_add_listener(p->uscita, &ASCOLTO_USCITA, p);
		} else {
			registro_dice(AREA,
			              "⚠ wlroots: the compositor announces more than one output — "
			              "I look at the first, and this line exists so that on that "
			              "day it is not a silent choice");
		}
	}
}

static void registro_via(void *dati, struct wl_registry *reg, uint32_t nome) {}

static const struct wl_registry_listener ASCOLTO_REGISTRO = {
	.global = registro_global,
	.global_remove = registro_via,
};

/* ------------------------------------------------------------------------- */
/* The frame. */

static void frame_buffer(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t formato,
                         uint32_t larghezza, uint32_t altezza, uint32_t stride)
{
	WlrPalco *p = dati;

	/* ⛔ ONCE per frame (defect 1): there is nothing to choose.
	 *    The format is in the wl_shm numbering, and is kept THAT WAY to create
	 *    the buffer; the translation to DRM is done only for whoever is downstream. */
	p->visto_buffer = true;
	p->f_shm = formato;
	p->f_larghezza = larghezza;
	p->f_altezza = altezza;
	p->f_stride = stride;

	if (!p->detto_il_formato) {
		uint32_t drm = shm_a_drm(formato);
		char nome[5];

		p->detto_il_formato = true;
		memcpy(nome, &drm, 4);
		nome[4] = 0;
		registro_dice(AREA,
		              "wlroots: the compositor gives the pixels in «%s» (%ux%u stride %u) — %s",
		              nome, larghezza, altezza, stride,
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

static void frame_flags(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t flags)
{
	((WlrPalco *)dati)->y_invertita = (flags & ZWLR_SCREENCOPY_FRAME_V1_FLAGS_Y_INVERT) != 0;
}

static void frame_pronto(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t sec_alto,
                         uint32_t sec_basso, uint32_t nsec)
{
	WlrPalco *p = dati;

	p->f_secondi = ((uint64_t)sec_alto << 32) | sec_basso;
	p->f_nanosecondi = nsec;
	p->pronto = true;
	if (p->copia_col_danno && registro_parla_molto()) {
		uint64_t uscita = (uint64_t)p->larghezza * p->altezza;

		p->danno_fotogrammi++;
		p->danno_area_somma += p->danno_area_fotogramma;
		p->danno_rett_somma += p->danno_rett_fotogramma;
		if (uscita && p->danno_area_fotogramma >= uscita)
			p->danno_interi++;
		if (p->danno_fotogrammi == 120) {
			registro_dettaglio(AREA,
			                   "wlroots: the declared damage, last 120 frames with damage: "
			                   "mean area %.1f%% of the output %ux%u, %u full, %.1f "
			                   "rectangles per frame (the last: %ux%u at %u,%u)",
			                   uscita ? 100.0 * (double)p->danno_area_somma / 120.0 / (double)uscita : 0.0,
			                   p->larghezza, p->altezza, p->danno_interi,
			                   p->danno_rett_somma / 120.0, p->danno_l, p->danno_a,
			                   p->danno_x, p->danno_y);
			p->danno_fotogrammi = p->danno_interi = p->danno_rett_somma = 0;
			p->danno_area_somma = 0;
		}
	}
	p->danno_area_fotogramma = 0;
	p->danno_rett_fotogramma = 0;
}

static void frame_fallito(void *dati, struct zwlr_screencopy_frame_v1 *f)
{
	((WlrPalco *)dati)->fallito = true;
}

static void frame_danno(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t x, uint32_t y,
                        uint32_t l, uint32_t a)
{
	WlrPalco *p = dati;

	/* ⚠ It arrives only with `copy_with_damage`, before `ready`. */
	p->danno_area_fotogramma += (uint64_t)l * a;
	p->danno_rett_fotogramma++;
	p->danno_x = x;
	p->danno_y = y;
	p->danno_l = l;
	p->danno_a = a;
}

static void frame_dmabuf(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t formato,
                         uint32_t larghezza, uint32_t altezza)
{
	WlrPalco *p = dati;

	/* ⭐ The card route: the offer is NOTED, and the choice is made by
	 *    `scheda_destinazione()` once the list is closed.  ⛔ And here the
	 *    format is a TRUE DRM fourcc — a different numbering from that of
	 *    `buffer`, in a field of its own, and it does NOT go through
	 *    `shm_a_drm()` (defect 1). */
	p->offerto_scheda = true;
	p->o_scheda_formato = formato;
	p->o_scheda_l = larghezza;
	p->o_scheda_a = altezza;
}

static void frame_buffer_done(void *dati, struct zwlr_screencopy_frame_v1 *f)
{
	((WlrPalco *)dati)->visto_buffer_done = true;
}

/* ⭐ «Is the list of offers closed?» — on v3 `buffer_done` says so, and only
 *    then do we know whether the card was offered.  ⚠ Below v3
 *    `buffer_done` does not exist: there `buffer` is enough, and it is also the only offer. */
static bool elenco_chiuso(const WlrPalco *p)
{
	if (p->visto_buffer_done)
		return true;
	return p->visto_buffer && zwlr_screencopy_frame_v1_get_version(p->frame) < 3;
}

static const struct zwlr_screencopy_frame_v1_listener ASCOLTO_FRAME = {
	.buffer = frame_buffer,
	.flags = frame_flags,
	.ready = frame_pronto,
	.failed = frame_fallito,
	.damage = frame_danno,
	.linux_dmabuf = frame_dmabuf,
	.buffer_done = frame_buffer_done,
};

static bool prepara_buffer(WlrPalco *p, GError **sbaglio)
{
	struct wl_shm_pool *pool;
	gsize byte = (gsize)p->f_stride * p->f_altezza;

	if (!p->buffer_sporco && p->buffer && p->b_larghezza == p->f_larghezza &&
	    p->b_altezza == p->f_altezza && p->b_stride == p->f_stride &&
	    p->b_formato == p->f_shm)
		return true; /* the previous one is fine */
	p->buffer_sporco = false;

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
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_DATA,
		            "the compositor declared a buffer of 0 bytes (%ux%u stride %u)",
		            p->f_larghezza, p->f_altezza, p->f_stride);
		return false;
	}

	p->fd = memfd_create("remotix-wlr", MFD_CLOEXEC);
	if (p->fd < 0) {
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno),
		            "memfd_create: %s", g_strerror(errno));
		return false;
	}
	if (ftruncate(p->fd, (off_t)byte) != 0) {
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno), "ftruncate(%zu): %s",
		            (size_t)byte, g_strerror(errno));
		return false;
	}
	p->pixel = mmap(NULL, byte, PROT_READ | PROT_WRITE, MAP_SHARED, p->fd, 0);
	if (p->pixel == MAP_FAILED) {
		p->pixel = NULL;
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno), "mmap: %s",
		            g_strerror(errno));
		return false;
	}
	p->byte = byte;

	pool = wl_shm_create_pool(p->shm, p->fd, (int32_t)byte);
	/* ⛔ The wl_shm format, NOT the translated one: the buffer is read by the
	 *    compositor, which speaks the wl_shm numbering. */
	p->buffer = wl_shm_pool_create_buffer(pool, 0, (int32_t)p->f_larghezza,
	                                      (int32_t)p->f_altezza, (int32_t)p->f_stride,
	                                      p->f_shm);
	wl_shm_pool_destroy(pool);
	p->b_larghezza = p->f_larghezza;
	p->b_altezza = p->f_altezza;
	p->b_stride = p->f_stride;
	p->b_formato = p->f_shm;
	return true;
}

/* ========================================================================= */
/* ⭐⭐ THE CARD ROUTE — the box at the top of the file.                      */
/*                                                                           */
/* ⛔ Everything that follows lives in functions OF ITS OWN: `wlr_fotogramma()`*/
/*    calls them in three places (the target of the `copy`, the delivery, the */
/*    closing of the frame), and the memory round stays as it was.           */
/* ========================================================================= */

/* --- the feedback: the node the compositor draws on ---------------------- */

static void feedback_fine(void *dati, struct zwp_linux_dmabuf_feedback_v1 *f)
{
	((WlrPalco *)dati)->feedback_finito = true;
}

static void feedback_tabella(void *dati, struct zwp_linux_dmabuf_feedback_v1 *f, int32_t fd,
                             uint32_t quanti)
{
	/* ⛔ The descriptor is OURS as soon as it arrives, and it is closed: the
	 *    format table is not needed (the modifier is LINEAR, decided), and an
	 *    `fd` kept for nothing is an `fd` lost at every session. */
	close(fd);
}

static void feedback_principale(void *dati, struct zwp_linux_dmabuf_feedback_v1 *f,
                                struct wl_array *dispositivo)
{
	WlrPalco *p = dati;

	/* ⚠ The protocol gives it as a `dev_t` in an array: if the size does not
	 *   match we do not guess, we leave it «not known» and fall back, saying so. */
	if (dispositivo->size == sizeof(dev_t)) {
		memcpy(&p->principale, dispositivo->data, sizeof(dev_t));
		p->principale_noto = true;
	}
}

static void feedback_tranche_fine(void *d, struct zwp_linux_dmabuf_feedback_v1 *f) {}
static void feedback_tranche_disp(void *d, struct zwp_linux_dmabuf_feedback_v1 *f,
                                  struct wl_array *a) {}
static void feedback_tranche_formati(void *d, struct zwp_linux_dmabuf_feedback_v1 *f,
                                     struct wl_array *a) {}
static void feedback_tranche_bandiere(void *d, struct zwp_linux_dmabuf_feedback_v1 *f,
                                      uint32_t b) {}

static const struct zwp_linux_dmabuf_feedback_v1_listener ASCOLTO_FEEDBACK = {
	.done = feedback_fine,
	.format_table = feedback_tabella,
	.main_device = feedback_principale,
	.tranche_done = feedback_tranche_fine,
	.tranche_target_device = feedback_tranche_disp,
	.tranche_formats = feedback_tranche_formati,
	.tranche_flags = feedback_tranche_bandiere,
};

/*
 * From the `dev_t` to the `renderD*` node of the same card.
 *
 * ⚠ The `main_device` can be the primary node (`card0`) or the render one:
 *   the sysfs folder `/sys/dev/char/M:m/device/drm/` lists BOTH of them in
 *   either case, and the `renderD*` is taken from there.  ⛔ No `libdrm` to
 *   link for this: one more library for one line of sysfs.
 */
static char *nodo_da_dispositivo(dev_t d)
{
	g_autofree char *cartella =
	    g_strdup_printf("/sys/dev/char/%u:%u/device/drm", major(d), minor(d));
	g_autoptr(GDir) dir = g_dir_open(cartella, 0, NULL);
	const char *voce;

	if (!dir)
		return NULL;
	while ((voce = g_dir_read_name(dir)))
		if (g_str_has_prefix(voce, "renderD"))
			return g_build_filename("/dev/dri", voce, NULL);
	return NULL;
}

/*
 * ⚠ THE FALLBACK, when the compositor does not say its node (v < 4): the SAME
 *   rule with which `sessione.c` chooses `WLR_RENDER_DRM_DEVICE` — the first
 *   openable `renderD*`, in name order.  ⛔ A different rule here would mean
 *   allocating on the other card exactly on the day the nodes swap.
 */
static char *nodo_come_sessione(void)
{
	g_autoptr(GDir) dri = g_dir_open("/dev/dri", 0, NULL);
	const char *voce;
	g_autofree char *primo = NULL;

	if (!dri)
		return NULL;
	while ((voce = g_dir_read_name(dri))) {
		g_autofree char *percorso = NULL;
		int fd;

		if (!g_str_has_prefix(voce, "renderD"))
			continue;
		percorso = g_build_filename("/dev/dri", voce, NULL);
		fd = open(percorso, O_RDWR | O_CLOEXEC);
		if (fd < 0)
			continue;
		close(fd);
		if (!primo || g_strcmp0(voce, primo) < 0) {
			g_free(primo);
			primo = g_strdup(voce);
		}
	}
	return primo ? g_build_filename("/dev/dri", primo, NULL) : NULL;
}

/* --- the slabs ------------------------------------------------------------ */

/*
 * ⛔⛔ THE GENERATION BELONGS TO THE PROCESS, NOT TO THE STAGE — 22 Sep 2026: on
 *      KDE the counter restarted from 0 with every new capture, and after
 *      «Log out» and a new login the encoder (which stays) found the surfaces
 *      of the dead session again in its cache: the screen flashed.  See
 *      `generazione_nuova()` in `cattura.c`.  ⇒ The same here, because a new
 *      stage is born at every rebirth of the XFCE session.
 * ⚠ It starts from 2^62, and not from 0: `cattura.c` has its own counter (this
 *   file is also linked into bench 13-w1, without `cattura.o`), and the two
 *   ranges never touch.
 */
static uint64_t generazione_nuova(void)
{
	static uint64_t ultima = UINT64_C(1) << 62;

	return __atomic_add_fetch(&ultima, 1, __ATOMIC_RELAXED);
}

/* ⛔ «Is the frame in progress on the card?» — and the flag before the
 *    index: before `wlr_chiedi_la_scheda()` the index is the zero of
 *    `g_new0`, that is a slab that does not exist. */
static bool scheda_nel_giro(const WlrPalco *p)
{
	return p->scheda_nata && p->lastra_del_giro >= 0;
}

static void lastra_butta(WlrPalco *p, WlrLastra *l)
{
	bool cera = l->bo || l->buffer;

	if (l->buffer)
		wl_buffer_destroy(l->buffer);
	if (l->bo)
		gbm_bo_destroy(l->bo);
	if (l->fd >= 0)
		close(l->fd);
	memset(l, 0, sizeof *l);
	l->fd = -1;
	/* ⛔ Rule 3: a slab that dies changes the generation. */
	if (cera)
		p->generazione = generazione_nuova();
}

/*
 * ⭐ A slab becomes FREE again — the only place that does it, besides `wlr_rendi()`.
 *
 * ⚠ If the card has been turned off in the meantime, the slab is no longer
 *   needed: it is thrown away now, which is the first moment it can be.
 */
static void lastra_torna_libera(WlrPalco *p, WlrLastra *l, bool sporca)
{
	l->stato = LASTRA_LIBERA;
	if (sporca)
		l->sporca = true;
	if (!p->scheda)
		lastra_butta(p, l);
}

static void params_creato(void *dati, struct zwp_linux_buffer_params_v1 *pr,
                          struct wl_buffer *buffer)
{
	WlrPalco *p = dati;

	p->creato = buffer;
	p->params_finito = true;
}

static void params_fallito(void *dati, struct zwp_linux_buffer_params_v1 *pr)
{
	WlrPalco *p = dati;

	p->params_fallito = true;
	p->params_finito = true;
}

static const struct zwp_linux_buffer_params_v1_listener ASCOLTO_PARAMS = {
	.created = params_creato,
	.failed = params_fallito,
};

/*
 * Creates (or keeps) the slab for the format and size of THIS frame.
 *
 * ⛔ `create` and not `create_immed`: with the latter a refusal by the
 *    compositor can be a PROTOCOL error, that is the connection dying.  With
 *    the former it is a `failed` event, and we fall back, saying so.
 * ⛔ And we wait with a ceiling OF ITS OWN (`WLR_LASTRA_NASCITA_S`), not with
 *    the frame's: see the definition.
 */
static bool lastra_prepara(WlrPalco *p, WlrLastra *l, uint32_t formato, uint32_t larghezza,
                           uint32_t altezza, GError **sbaglio)
{
	uint64_t lineare = DRM_FORMAT_MOD_LINEAR;
	struct zwp_linux_buffer_params_v1 *params;
	gint64 scadenza;

	if (l->buffer && !l->sporca && l->larghezza == larghezza && l->altezza == altezza &&
	    l->formato == formato)
		return true; /* the previous one is fine */
	if (lastre_massime && l->bo && l->formato == formato && larghezza <= l->bo_larghezza &&
	    altezza <= l->bo_altezza) {
		/* ⛔ PHASE 19: the BO stays (see WLR_LASTRA_L), only the `wl_buffer`
		 *    changes.  ⛔ Rule 3: the size has changed, so the generation
		 *    changes — the encoder must not find in its cache the import
		 *    with the old size. */
		if (l->buffer)
			wl_buffer_destroy(l->buffer);
		l->buffer = NULL;
		l->larghezza = larghezza;
		l->altezza = altezza;
		p->generazione = generazione_nuova();
		goto il_buffer;
	}
	lastra_butta(p, l);
	if (lastre_massime && (larghezza > WLR_LASTRA_L || altezza > WLR_LASTRA_A))
		registro_dice(AREA,
		              "⚠ wlroots: a %ux%u canvas beyond the maximum slab %ux%u — the "
		              "slab is born at the requested size, and on a size change it WILL DIE "
		              "(PHASE 19: on the Radeon with Vulkan this is the GPU hang case)",
		              larghezza, altezza, WLR_LASTRA_L, WLR_LASTRA_A);

	/* ⭐ LINEAR, asked for by name.  ⚠ If the driver does not accept the
	 *   modifier list we retry with the LINEAR flag, which says the same
	 *   thing in the old dialect. */
	l->bo_larghezza = (lastre_massime && larghezza < WLR_LASTRA_L) ? WLR_LASTRA_L : larghezza;
	l->bo_altezza = (lastre_massime && altezza < WLR_LASTRA_A) ? WLR_LASTRA_A : altezza;
	l->bo = gbm_bo_create_with_modifiers2(p->gbm, l->bo_larghezza, l->bo_altezza, formato,
	                                      &lineare, 1, GBM_BO_USE_RENDERING);
	if (!l->bo)
		l->bo = gbm_bo_create(p->gbm, l->bo_larghezza, l->bo_altezza, formato,
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
	bool scelta_del_driver = false;
	if (!l->bo) {
		/* ⛔ Not «whatever the driver wants»: `[M]` on the 4090 it picks a
		 *    modifier Vulkan does not import.  Only those the encoder
		 *    declares (`vulkanvideo_modificatori`), asked once per stage and
		 *    format. */
		int lineare_errno = errno;
		if (p->mod_formato != formato) {
			p->mod_formato = formato;
			p->mod_quanti = vulkanvideo_modificatori(p->nodo, formato, p->mod_ammessi,
			                                         (int)G_N_ELEMENTS(p->mod_ammessi));
		}
		if (p->mod_quanti > 0)
			l->bo = gbm_bo_create_with_modifiers2(p->gbm, l->bo_larghezza, l->bo_altezza,
			                                      formato, p->mod_ammessi,
			                                      (unsigned)p->mod_quanti, GBM_BO_USE_RENDERING);
		if (!l->bo)
			errno = lineare_errno;
		else
			scelta_del_driver = true;
	}
	if (!l->bo) {
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno),
		            "gbm does not allocate %ux%u fourcc 0x%08x on %s, neither linear nor with one of "
		            "the %d modifiers the encoder imports: %s",
		            l->bo_larghezza, l->bo_altezza, formato, p->nodo, p->mod_quanti,
		            g_strerror(errno));
		return false;
	}
	if (gbm_bo_get_plane_count(l->bo) != 1) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "gbm gave a slab with %d planes: the encoder can read one",
		            gbm_bo_get_plane_count(l->bo));
		lastra_butta(p, l);
		return false;
	}
	l->modificatore = gbm_bo_get_modifier(l->bo);
	/* ⚠ With the old dialect the modifier can come back INVALID: the LINEAR
	 *   flag however fixed it, and it is written down for what it is. */
	if (l->modificatore == DRM_FORMAT_MOD_INVALID && !scelta_del_driver)
		l->modificatore = DRM_FORMAT_MOD_LINEAR;
	if (scelta_del_driver) {
		static bool detto = false;
		if (l->modificatore == DRM_FORMAT_MOD_INVALID) {
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
			            "gbm refused linear, and the driver's slab does not say "
			            "its modifier: nobody could import it");
			lastra_butta(p, l);
			return false;
		}
		if (!detto) {
			detto = true;
			registro_dice(AREA,
			              "⭐ wlroots: the driver refuses the LINEAR slab (NVIDIA): the "
			              "slab is born with modifier 0x%" G_GINT64_MODIFIER "x, chosen "
			              "among the %d the Vulkan encoder declares it can import",
			              (guint64)l->modificatore, p->mod_quanti);
		}
	} else if (l->modificatore != DRM_FORMAT_MOD_LINEAR) {
		/* ⛔ LINEAR was asked for: a tiling nobody chose is an import
		 *    nobody has tried. */
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "gbm gave modifier 0x%" G_GINT64_MODIFIER "x instead of the "
		            "LINEAR asked for",
		            (guint64)l->modificatore);
		lastra_butta(p, l);
		return false;
	}
	l->fd = gbm_bo_get_fd(l->bo);
	l->stride = gbm_bo_get_stride_for_plane(l->bo, 0);
	l->offset = gbm_bo_get_offset(l->bo, 0);
	l->larghezza = larghezza;
	l->altezza = altezza;
	l->formato = formato;
	if (l->fd < 0) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "gbm_bo_get_fd: the slab has no DMA-BUF descriptor");
		lastra_butta(p, l);
		return false;
	}
	/* ⛔ The slab is already born here, even if the `wl_buffer` is not there
	 *    yet: the generation changes NOW (rule 3). */
	p->generazione = generazione_nuova();

il_buffer:
	p->creato = NULL;
	p->params_finito = p->params_fallito = false;
	params = zwp_linux_dmabuf_v1_create_params(p->dmabuf);
	zwp_linux_buffer_params_v1_add_listener(params, &ASCOLTO_PARAMS, p);
	zwp_linux_buffer_params_v1_add(params, l->fd, 0, l->offset, l->stride,
	                               (uint32_t)(l->modificatore >> 32),
	                               (uint32_t)(l->modificatore & 0xffffffffu));
	zwp_linux_buffer_params_v1_create(params, (int32_t)larghezza, (int32_t)altezza, formato, 0);
	scadenza = g_get_monotonic_time() + (gint64)(WLR_LASTRA_NASCITA_S * G_USEC_PER_SEC);
	while (!p->params_finito) {
		if (!pompa(p, scadenza, sbaglio)) {
			zwp_linux_buffer_params_v1_destroy(params);
			lastra_butta(p, l);
			return false;
		}
		if (!p->params_finito && g_get_monotonic_time() >= scadenza)
			break;
	}
	zwp_linux_buffer_params_v1_destroy(params);
	if (!p->params_finito || p->params_fallito || !p->creato) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "the compositor %s the %ux%u DMA-BUF (modifier 0x%" G_GINT64_MODIFIER
		            "x, stride %u)",
		            p->params_finito ? "REFUSED" : "did not answer in time for",
		            larghezza, altezza, (guint64)l->modificatore, l->stride);
		/* ⚠ If `created` arrived after the ceiling the `wl_buffer` would be left
		 *   orphaned: one lost object, once, against a live connection. */
		lastra_butta(p, l);
		return false;
	}
	l->buffer = p->creato;
	p->creato = NULL;
	l->sporca = false;
	return true;
}

/* ⛔ Rule 1: ONLY a FREE slab is chosen, in rotation. */
static int lastra_scegli(WlrPalco *p)
{
	for (unsigned i = 0; i < WLR_LASTRE; i++) {
		unsigned k = (p->prossima + i) % WLR_LASTRE;

		if (p->lastre[k].stato == LASTRA_LIBERA) {
			p->prossima = (k + 1) % WLR_LASTRE;
			return (int)k;
		}
	}
	return -1;
}

/*
 * ⛔ The card is TURNED OFF, and the reason is said.  From here every frame
 *    goes to memory, and the counters show it.
 * ⚠ Only the FREE ones are thrown away: one IN HAND is thrown away by
 *   `wlr_rendi()` when it comes back, one IN FLIGHT by the closing of its
 *   frame (`lastra_torna_libera`).  ⛔ Throwing away a slab in flight would
 *   mean destroying a `wl_buffer` named in a `copy` still open.
 */
static void scheda_spegni(WlrPalco *p, const char *perche)
{
	if (!p->scheda)
		return;
	p->scheda = false;
	for (unsigned i = 0; i < WLR_LASTRE; i++)
		if (p->lastre[i].stato == LASTRA_LIBERA)
			lastra_butta(p, &p->lastre[i]);
	registro_dice(AREA,
	              "⛔⛔ wlroots: the CARD route is TURNED OFF — %s.  ⇒ DECLARED "
	              "FALLBACK: from here the pixels go through MEMORY (`glReadPixels` "
	              "in the compositor + our copy), and the numbers of this link are "
	              "those of the other route",
	              perche);
}

/*
 * ⭐ THE TARGET OF THIS FRAME'S `copy` — the card, or NULL for memory.  It is
 *    called once the list is closed (`elenco_chiuso()`), ONCE per frame:
 *    after that, the answer is in `lastra_del_giro`.
 *
 * ⛔ It returns NULL also with `*rotto` true: all the slabs are in hand
 *    downstream.  There the frame STOPS; a slab in hand is not recycled and
 *    there is no silent fallback to memory (rule 1).
 */
static struct wl_buffer *scheda_destinazione(WlrPalco *p, bool *rotto, GError **sbaglio)
{
	g_autoptr(GError) perche = NULL;
	WlrLastra *l;
	int k;

	*rotto = false;
	p->lastra_del_giro = -1;
	if (!p->scheda)
		return NULL;
	if (!p->offerto_scheda) {
		/* ⚠ `[R]` wlroots sends `linux_dmabuf` only if the output's allocator
		 *   can do DMA-BUF: without it, the compositor is in SOFTWARE
		 *   (pixman, `STUDI.md` §xfce §5.2).  It is a diagnosis, and it is written. */
		if (!p->detto_senza_offerta) {
			p->detto_senza_offerta = true;
			registro_dice(AREA,
			              "⛔ wlroots: the compositor does NOT offer DMA-BUF for this "
			              "frame — it usually means it draws in SOFTWARE "
			              "(pixman, `STUDI.md` §xfce §5.2).  DECLARED FALLBACK: the "
			              "frame goes to MEMORY; the line is not repeated");
		}
		return NULL;
	}
	if (p->o_scheda_formato != DRM_FORMAT_XRGB8888 &&
	    p->o_scheda_formato != DRM_FORMAT_ARGB8888) {
		if (!p->detto_formato_scheda) {
			char nome[5];

			p->detto_formato_scheda = true;
			memcpy(nome, &p->o_scheda_formato, 4);
			nome[4] = 0;
			registro_dice(AREA,
			              "⛔ wlroots: the card offers «%s», and the encoder imports "
			              "only XRGB8888 and ARGB8888 — ⚠ a fourcc is NOT guessed (a "
			              "swapped channel gives no error, it gives a blue desktop).  "
			              "DECLARED FALLBACK: the frame goes to MEMORY",
			              nome);
		}
		return NULL;
	}

	k = lastra_scegli(p);
	if (k < 0) {
		*rotto = true;
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_BUSY,
		            "all %d of the card's slabs are IN HAND downstream: someone "
		            "did not call `wlr_rendi()` (that is `cattura_fermo_libera()`).  ⛔ "
		            "None is recycled: it would mean rewriting an image while the "
		            "encoder reads it",
		            WLR_LASTRE);
		return NULL;
	}
	l = &p->lastre[k];
	if (!lastra_prepara(p, l, p->o_scheda_formato, p->o_scheda_l, p->o_scheda_a, &perche)) {
		g_autofree char *motivo =
		    g_strdup_printf("the slab was not born (%s)", perche ? perche->message : "?");

		scheda_spegni(p, motivo);
		return NULL;
	}
	l->stato = LASTRA_IN_VOLO;
	p->lastra_del_giro = k;
	return l->buffer;
}

/*
 * ⛔⛔ THE GPU WAIT AFTER `ready` — the synchronisation box.
 *
 * It returns false only if the fence was there and did NOT fire before the
 * deadline: then the slab is not delivered (whoever read it would see a half
 * blit), and the frame stays PENDING — the next call waits again.
 */
static bool scheda_aspetta_la_gpu(WlrPalco *p, WlrLastra *l, gint64 scadenza,
                                  WlrFotogramma *fuori, GError **sbaglio)
{
	struct dma_buf_export_sync_file sf = { .flags = DMA_BUF_SYNC_READ, .fd = -1 };
	gint64 prima = g_get_monotonic_time();
	struct pollfd pfd;
	gint64 resta;
	int r;

	fuori->us_attesa_gpu = 0;
	fuori->attesa_esplicita = false;
	if (ioctl(l->fd, DMA_BUF_IOCTL_EXPORT_SYNC_FILE, &sf) != 0) {
		/* ⚠ Kernel without the ioctl (< 5.20), or a driver that does not support
		 *   it: we rely on IMPLICIT synchronisation, and say so once. */
		if (!p->detta_sync_implicita) {
			p->detta_sync_implicita = true;
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
	fuori->attesa_esplicita = true;
	resta = (scadenza - prima) / 1000;
	pfd.fd = sf.fd;
	pfd.events = POLLIN;
	do {
		r = poll(&pfd, 1, resta > 0 ? (int)resta : 0);
	} while (r < 0 && errno == EINTR);
	close(sf.fd);
	fuori->us_attesa_gpu = (uint64_t)(g_get_monotonic_time() - prima);
	if (r <= 0) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "the compositor said «ready» but the blit on the GPU did not finish "
		            "before the deadline (%.1f ms waiting for the fence) — the frame "
		            "stays in progress",
		            fuori->us_attesa_gpu / 1000.0);
		return false;
	}
	return true;
}

/* ⭐ The delivery of a card frame: the slab goes IN HAND. */
static void scheda_consegna(WlrPalco *p, WlrFotogramma *fuori)
{
	WlrLastra *l = &p->lastre[p->lastra_del_giro];

	p->falliti_di_fila = 0;
	l->stato = LASTRA_IN_MANO;
	p->lastra_del_giro = -1;

	fuori->sulla_scheda = true;
	fuori->pixel = NULL;
	fuori->larghezza = l->larghezza;
	fuori->altezza = l->altezza;
	fuori->stride = l->stride;
	/* ⛔ The DRM fourcc of the `linux_dmabuf` event, as it is: it does NOT go
	 *    through `shm_a_drm()` (defect 1). */
	fuori->formato = l->formato;
	fuori->byte = (gsize)l->stride * l->altezza;
	fuori->fd = l->fd;
	fuori->offset = l->offset;
	fuori->modificatore = l->modificatore;
	fuori->generazione = p->generazione;
	fuori->lastra = l;
	fuori->secondi = p->f_secondi;
	fuori->nanosecondi = p->f_nanosecondi;
	/* ⚠ `[R]` On the card the compositor sends `flags 0`: the blit already
	 *   writes upright.  What it said is delivered anyway. */
	fuori->y_invertita = p->y_invertita;

	if (!p->detto_il_formato_scheda) {
		char nome[5];

		p->detto_il_formato_scheda = true;
		memcpy(nome, &l->formato, 4);
		nome[4] = 0;
		registro_dice(AREA,
		              "⭐ wlroots: the FIRST frame from the CARD — «%s» %ux%u stride "
		              "%u, linear slab, %s",
		              nome, l->larghezza, l->altezza, l->stride,
		              fuori->attesa_esplicita
		                  ? "fence extracted from the DMA-BUF and waited on"
		                  : "⚠ without a fence: implicit synchronisation");
	}
}

static void scheda_chiudi(WlrPalco *p)
{
	if (!p->scheda_nata)
		return;
	for (unsigned i = 0; i < WLR_LASTRE; i++)
		lastra_butta(p, &p->lastre[i]);
	if (p->gbm)
		gbm_device_destroy(p->gbm);
	if (p->drm_fd >= 0)
		close(p->drm_fd);
	g_free(p->nodo);
	p->nodo = NULL;
	p->scheda_nata = p->scheda = false;
}

/*
 * Closes the frame in progress.  `copia_viva` = the copy had started and
 * neither `ready` nor `failed` has arrived: the buffer is not reused.
 *
 * ⭐ And the frame's slab, if there was one and it was NOT delivered (dropped
 *    wire, `failed`): rule 2, it is dirty.  ⚠ A delivered slab already has
 *    `lastra_del_giro = -1`, and is not touched here.
 */
static void chiudi_frame(WlrPalco *p, bool copia_viva)
{
	if (p->frame)
		zwlr_screencopy_frame_v1_destroy(p->frame);
	p->frame = NULL;
	if (scheda_nel_giro(p)) {
		lastra_torna_libera(p, &p->lastre[p->lastra_del_giro], true);
		p->lastra_del_giro = -1;
	} else if (copia_viva) {
		p->buffer_sporco = true;
	}
	p->copia_partita = false;
	p->copia_col_danno = false;
}

/* ========================================================================= */
/* ⭐⭐ THE POINTER PROBE — the true shape on labwc (XFCE and LXQt).          */
/* ========================================================================= */

/*
 * ⛔ THE FACT `[M]`: headless labwc has no cursor plane — it draws the pointer
 *    in software INSIDE the output buffer, and screencopy has no channel for
 *    its shape.  ⭐ But the encoded theme (`forma.h`) makes sure that under
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
 *      ⇒ With the hand still, SONDA_CODA_US after the last one, one more is
 *      sent, only once.  Without it, whoever stops on an edge with the first
 *      gesture would keep the arrow.
 *
 * ⛔ THE THREAD: everything runs on the thread of the child's loop — the
 *    request starts from `wlr_sonda_puntatore` (after the gesture injection),
 *    the events are pumped by `wlr_fotogramma` (the same pump as the stream),
 *    and the shape is collected by `wlr_sonda_forma` (from `cattura_prendi`).
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
 *       no probe         labwc 4.9-5.1%   figlio 11.2%   painted 55.1-55.3/s
 *       probe at 60 Hz   labwc 6.3-6.4%   figlio 11.6-11.8%   55.0-55.2/s
 *       probe at 30 Hz   labwc 5.7%       figlio 11.6-11.7%   55.1-55.3/s
 *   ⇒ +1.4 points of labwc CPU (+0.5 for the child), frames unchanged:
 *     below the 2-point threshold, and the thinning stays OFF.  If one day
 *     it were needed: SONDA_MINIMO_US 33333 is the 30 Hz measured above.
 */

/* ⭐ How long after the last probe the tail probe is sent. */
#define SONDA_CODA_US (120 * 1000)
/* ⚠ The thinning: 0 = one per gesture (coalescing).  See the cost, above. */
#define SONDA_MINIMO_US 0

static void sonda_lancia(WlrPalco *p, int32_t x, int32_t y);

static void sonda_chiudi_frame(WlrPalco *p)
{
	if (p->s_frame)
		zwlr_screencopy_frame_v1_destroy(p->s_frame);
	p->s_frame = NULL;
	p->s_visto_buffer = p->s_copia_partita = false;
}

/*
 * The bytes of a probe pixel, according to the format; 0 = it cannot be read.
 * ⛔ `[M]` 6 Oct 2026, NVIDIA (labwc 0.9.3, Ubuntu 26.04): for the 3x3 region
 *    labwc offers a **3-byte** format (stride 9) — the «stride ≥ w×4» ceiling
 *    refused it, the probe stayed without a buffer and the pointer shape never
 *    changed (F-005 red on LXQt).  On Intel and Radeon it offers XRGB8888.
 */
static unsigned sonda_bpp(uint32_t shm)
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
static bool sonda_buffer(WlrPalco *p)
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
	if (byte == 0 || byte > 4096 || sonda_bpp(p->s_f_shm) == 0 ||
	    p->s_f_stride < p->s_f_l * sonda_bpp(p->s_f_shm))
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
static void sonda_prossima(WlrPalco *p)
{
	sonda_chiudi_frame(p);
	if (p->s_in_attesa && g_get_monotonic_time() - p->s_ultima_partita >= SONDA_MINIMO_US) {
		p->s_in_attesa = false;
		sonda_lancia(p, p->s_attesa_x, p->s_attesa_y);
	}
}

static void sonda_parti(WlrPalco *p)
{
	if (p->s_copia_partita)
		return;
	if (!sonda_buffer(p)) {
		if (!p->s_detto_fallito) {
			p->s_detto_fallito = true;
			registro_dice(AREA, "⚠ wlroots: the pointer probe has no buffer "
			                    "(%ux%u stride %u): the shape is not looked at, and the client "
			                    "keeps its arrow",
			              p->s_f_l, p->s_f_a, p->s_f_stride);
			registro_dice(AREA, "   (wl_shm format of the probe: 0x%08x)", p->s_f_shm);
		}
		p->s_conto.fallite++;
		sonda_prossima(p);
		return;
	}
	zwlr_screencopy_frame_v1_copy(p->s_frame, p->s_buffer);
	p->s_copia_partita = true;
}

static void sonda_buffer_ev(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t formato,
                            uint32_t l, uint32_t a, uint32_t stride)
{
	WlrPalco *p = dati;

	p->s_visto_buffer = true;
	p->s_f_shm = formato;
	p->s_f_l = l;
	p->s_f_a = a;
	p->s_f_stride = stride;
	/* ⚠ Below v3 `buffer_done` does not exist: this is the only offer. */
	if (zwlr_screencopy_frame_v1_get_version(f) < 3)
		sonda_parti(p);
}

static void sonda_buffer_done(void *dati, struct zwlr_screencopy_frame_v1 *f)
{
	WlrPalco *p = dati;

	if (p->s_visto_buffer)
		sonda_parti(p);
}

/*
 * A probe pixel ⇒ B G R, according to the declared format.  FALSE = a
 * format that is not read here (said once, and the probe turns off).
 */
static bool sonda_bgr(uint32_t shm, const uint8_t *q, uint8_t *b, uint8_t *g, uint8_t *r)
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

static void sonda_pronta(void *dati, struct zwlr_screencopy_frame_v1 *f, uint32_t sa,
                         uint32_t sb, uint32_t ns)
{
	WlrPalco *p = dati;
	const uint8_t *px = p->s_pixel;
	/* ⭐ The centre of the region, in buffer pixels: at the edge of the output
	 *    the region is cut, and the centre moves with it. */
	int32_t cx = p->s_x - MAX(p->s_x - 1, 0), cy = p->s_y - MAX(p->s_y - 1, 0);
	int trovata = -1;
	uint8_t b = 0, g = 0, r = 0;

	p->s_conto.tornate++;
	if (!px) {
		sonda_prossima(p);
		return;
	}
	if (!sonda_bgr(p->s_f_shm, px, &b, &g, &r)) {
		if (!p->s_detto_formato) {
			p->s_detto_formato = true;
			registro_dice(AREA,
			              "⛔ wlroots: the pointer probe receives wl_shm format "
			              "0x%08x, which is not read here: the probe TURNS OFF, and the "
			              "client keeps its arrow",
			              p->s_f_shm);
		}
		p->s_spenta = true;
		sonda_chiudi_frame(p);
		return;
	}
	/* ⭐ First the centre, then the neighbours — `forma_da_pixel` is exact to
	 *    the byte, and a neighbour of another colour is never one of our shapes. */
	for (int giro = 0; giro < 2 && trovata < 0; giro++)
		for (uint32_t y = 0; y < p->s_f_a && trovata < 0; y++)
			for (uint32_t x = 0; x < p->s_f_l && trovata < 0; x++) {
				bool centro = (int32_t)x == cx && (int32_t)y == cy;

				if (centro != (giro == 0))
					continue;
				sonda_bgr(p->s_f_shm,
				          px + (gsize)y * p->s_f_stride + x * sonda_bpp(p->s_f_shm), &b,
				          &g, &r);
				trovata = forma_da_pixel(b, g, r, 0xFF);
				if (trovata >= 0 && !centro)
					p->s_conto.dai_vicini++;
			}
	if (trovata < 0) {
		/* ⚠ None of our colours: an application that hides the pointer, or
		 *   that draws a surface of its own.  The previous shape is kept. */
		p->s_conto.ignote++;
		if (!p->s_detta_ignota) {
			p->s_detta_ignota = true;
			registro_dice(AREA,
			              "⚠ wlroots: under the pointer (%d,%d) no colour of the encoded "
			              "theme: the previous shape is kept.  The line is not "
			              "repeated; the count is in the closing line",
			              p->s_x, p->s_y);
		}
	} else if (trovata != p->s_forma) {
		p->s_forma = trovata;
		p->s_nuova = trovata;
		p->s_conto.cambi++;
	}
	sonda_prossima(p);
}

static void sonda_fallita(void *dati, struct zwlr_screencopy_frame_v1 *f)
{
	WlrPalco *p = dati;

	p->s_conto.fallite++;
	sonda_prossima(p);
}

static void sonda_flags(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t flags) {}
static void sonda_danno(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t x, uint32_t y,
                        uint32_t l, uint32_t a) {}
static void sonda_dmabuf(void *d, struct zwlr_screencopy_frame_v1 *f, uint32_t formato,
                         uint32_t l, uint32_t a) {}

/* ⛔ ALL the events have a function: `libwayland` calls without looking,
 *    and a hole here is a jump to NULL at the first version that sends it. */
static const struct zwlr_screencopy_frame_v1_listener ASCOLTO_SONDA = {
	.buffer = sonda_buffer_ev,
	.flags = sonda_flags,
	.ready = sonda_pronta,
	.failed = sonda_fallita,
	.damage = sonda_danno,
	.linux_dmabuf = sonda_dmabuf,
	.buffer_done = sonda_buffer_done,
};

static void sonda_lancia(WlrPalco *p, int32_t x, int32_t y)
{
	int32_t rx = MAX(x - 1, 0), ry = MAX(y - 1, 0);
	int32_t rl = MIN(x + 2, (int32_t)p->larghezza) - rx;
	int32_t ra = MIN(y + 2, (int32_t)p->altezza) - ry;

	if (rl <= 0 || ra <= 0)
		return;
	p->s_x = x;
	p->s_y = y;
	p->s_visto_buffer = p->s_copia_partita = false;
	p->s_frame = zwlr_screencopy_manager_v1_capture_output_region(p->manager, 1, p->uscita,
	                                                             rx, ry, rl, ra);
	if (!p->s_frame) {
		p->s_conto.fallite++;
		return;
	}
	zwlr_screencopy_frame_v1_add_listener(p->s_frame, &ASCOLTO_SONDA, p);
	p->s_conto.lanciate++;
	p->s_ultima_partita = g_get_monotonic_time();
	p->s_coda_a = p->s_ultima_partita + SONDA_CODA_US;
	/* ⭐ Straight onto the wire: the stream's pump runs within 8 ms, and the
	 *    shape arrives sooner if the request leaves now.  ⚠ EAGAIN is not a
	 *    fault: it leaves with the pump's next `flush`. */
	wl_display_flush(p->display);
}

void wlr_sonda_puntatore(WlrPalco *p, uint32_t x, uint32_t y, uint32_t l, uint32_t a)
{
	int32_t ux, uy;

	if (!p || p->s_spenta || !p->manager || !p->uscita || !p->shm || l == 0 || a == 0 ||
	    p->larghezza == 0 || p->altezza == 0)
		return;
	/* ⭐ From the canvas to the output, as wlroots does with the virtual pointer. */
	if (x >= l)
		x = l - 1;
	if (y >= a)
		y = a - 1;
	ux = (int32_t)((uint64_t)x * p->larghezza / l);
	uy = (int32_t)((uint64_t)y * p->altezza / a);
	p->s_conto.chieste++;
	p->s_coda_fatta = false;
	if (p->s_frame || (SONDA_MINIMO_US > 0 &&
	                   g_get_monotonic_time() - p->s_ultima_partita < SONDA_MINIMO_US)) {
		/* ⭐ coalescing: only the LAST position is remembered */
		p->s_in_attesa = true;
		p->s_attesa_x = ux;
		p->s_attesa_y = uy;
		return;
	}
	sonda_lancia(p, ux, uy);
}

int wlr_sonda_forma(WlrPalco *p)
{
	int nuova;

	if (!p || p->s_spenta)
		return -1;
	/* ⭐ the tail probe (rule 3), and the one left behind by the thinning:
	 *    they start from here, which the child's loop always calls */
	if (!p->s_frame) {
		gint64 ora = g_get_monotonic_time();

		if (p->s_in_attesa && ora - p->s_ultima_partita >= SONDA_MINIMO_US) {
			p->s_in_attesa = false;
			sonda_lancia(p, p->s_attesa_x, p->s_attesa_y);
		} else if (!p->s_in_attesa && !p->s_coda_fatta && p->s_conto.lanciate > 0 &&
		           ora >= p->s_coda_a) {
			p->s_coda_fatta = true;
			p->s_conto.di_coda++;
			sonda_lancia(p, p->s_x, p->s_y);
		}
	}
	nuova = p->s_nuova;
	p->s_nuova = -1;
	return nuova;
}

void wlr_sonda_conteggi(const WlrPalco *p, WlrSondaConteggi *fuori)
{
	if (fuori)
		*fuori = p ? p->s_conto : (WlrSondaConteggi){ 0 };
}

/* ------------------------------------------------------------------------- */

WlrPalco *wlr_apri(GError **sbaglio)
{
	WlrPalco *p = g_new0(WlrPalco, 1);
	const char *nome = g_getenv("WAYLAND_DISPLAY");

	p->fd = -1;
	p->s_fd = -1;
	p->s_forma = p->s_nuova = -1;
	p->forza_intero = true; /* the first round: whoever attaches must see at once */
	/* ⛔ The card's descriptors at -1 AT ONCE: the zero of `g_new0` is
	 *    standard input, and a mistaken close would close it. */
	p->drm_fd = -1;
	p->lastra_del_giro = -1;
	for (unsigned i = 0; i < WLR_LASTRE; i++)
		p->lastre[i].fd = -1;
	p->teste = g_ptr_array_new_with_free_func(libera_testa);
	p->display = wl_display_connect(nome);
	if (!p->display && !nome) {
		for (int i = 0; i < 10 && !p->display; i++) {
			g_autofree char *tenta = g_strdup_printf("wayland-%d", i);

			p->display = wl_display_connect(tenta);
			if (p->display)
				registro_dice(AREA,
				              "wlroots: WAYLAND_DISPLAY was not set, found «%s» "
				              "in XDG_RUNTIME_DIR", tenta);
		}
	}
	if (!p->display) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no Wayland compositor reachable in XDG_RUNTIME_DIR=%s",
		            g_getenv("XDG_RUNTIME_DIR") ?: "(not set)");
		wlr_chiudi(p);
		return NULL;
	}

	p->registry = wl_display_get_registry(p->display);
	wl_registry_add_listener(p->registry, &ASCOLTO_REGISTRO, p);
	/* ⚠ TWO rounds, not one: the first brings the globals, the second the
	 *   events the globals send as soon as they are bound.  ⛔ And with a
	 *   ceiling (defect 3). */
	if (!giro(p, 2.0, sbaglio) || !giro(p, 2.0, sbaglio)) {
		wlr_chiudi(p);
		return NULL;
	}

	if (!p->manager) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "the compositor does not announce zwlr_screencopy_manager_v1: on this "
		            "desktop capture does not go through here");
		wlr_chiudi(p);
		return NULL;
	}
	if (!p->shm) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "the compositor does not announce wl_shm: I have nowhere to have the "
		            "pixels written");
		wlr_chiudi(p);
		return NULL;
	}
	if (!p->uscita) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "the compositor announces no wl_output: there is nothing to "
		            "capture (the session is alive but without a screen?)");
		wlr_chiudi(p);
		return NULL;
	}

	registro_dice(AREA,
	              "⭐ wlroots: capture ready on output «%s», %ux%u — ⚠ and the size is "
	              "the one the output HAS, not the one asked for",
	              p->uscita_nome ?: "unnamed", p->larghezza, p->altezza);
	return p;
}

void wlr_misura(const WlrPalco *palco, uint32_t *larghezza, uint32_t *altezza)
{
	if (larghezza)
		*larghezza = palco ? palco->larghezza : 0;
	if (altezza)
		*altezza = palco ? palco->altezza : 0;
}

const char *wlr_uscita_nome(const WlrPalco *palco)
{
	return palco && palco->uscita_nome ? palco->uscita_nome : "";
}

void wlr_forza_intero(WlrPalco *palco)
{
	if (palco)
		palco->forza_intero = true;
}

void wlr_conteggi(const WlrPalco *palco, WlrConteggi *fuori)
{
	if (fuori)
		*fuori = palco ? palco->conteggi : (WlrConteggi){ 0 };
}

WlrMisuraEsito wlr_misura_chiedi(WlrPalco *palco, uint32_t larghezza, uint32_t altezza,
                                 double attesa_s, GError **sbaglio)
{
	struct zwlr_output_configuration_v1 *conf;
	struct zwlr_output_configuration_head_v1 *ct;
	Testa *nostra = NULL;
	gint64 scadenza;

	g_return_val_if_fail(palco != NULL, WLR_MISURA_IMPOSSIBILE);

	for (guint i = 0; palco->teste && i < palco->teste->len; i++) {
		Testa *t = g_ptr_array_index(palco->teste, i);

		if (palco->uscita_nome && g_strcmp0(t->nome, palco->uscita_nome) == 0)
			nostra = t;
	}
	if (!palco->gestore || !nostra || !palco->serial_noto) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED, "%s",
		            !palco->gestore ? "the compositor does not announce "
		                              "zwlr_output_manager_v1: the size cannot be "
		                              "changed"
		            : !nostra ? "no head of the output manager has the name "
		                        "of the output being captured"
		                      : "the output manager has not yet sent its "
		                        "serial");
		return WLR_MISURA_IMPOSSIBILE;
	}
	if (palco->larghezza == larghezza && palco->altezza == altezza)
		return WLR_MISURA_GIA_COSI;

	palco->conf = CONF_IN_CORSO;
	conf = zwlr_output_manager_v1_create_configuration(palco->gestore, palco->serial);
	zwlr_output_configuration_v1_add_listener(conf, &ASCOLTO_CONF, palco);

	/*
	 * ⛔ Defect 6: EVERY head must be configured, or the compositor closes the
	 *    wire with `unconfigured_head`.  ⇒ Ours takes the new size; the others
	 *    are reconfirmed exactly as they are — enabled ones stay enabled,
	 *    disabled ones stay disabled.  ⚠ Never disable one to simplify: on a
	 *    real machine it would be someone's screen.
	 */
	for (guint i = 0; i < palco->teste->len; i++) {
		Testa *t = g_ptr_array_index(palco->teste, i);

		if (t == nostra) {
			ct = zwlr_output_configuration_v1_enable_head(conf, t->proxy);
			/* ⚠ `refresh = 0`: on an output without a screen the refresh rate is
			 *   a fiction, and zero means «you choose». */
			zwlr_output_configuration_head_v1_set_custom_mode(ct, (int32_t)larghezza,
			                                                  (int32_t)altezza, 0);
		} else if (t->accesa) {
			zwlr_output_configuration_v1_enable_head(conf, t->proxy);
		} else {
			zwlr_output_configuration_v1_disable_head(conf, t->proxy);
		}
	}
	zwlr_output_configuration_v1_apply(conf);

	scadenza = g_get_monotonic_time() + (gint64)(attesa_s * 1e6);
	while (palco->conf == CONF_IN_CORSO) {
		if (!pompa(palco, scadenza, sbaglio)) {
			zwlr_output_configuration_v1_destroy(conf);
			return WLR_MISURA_RIFIUTATA;
		}
		if (palco->conf == CONF_IN_CORSO && g_get_monotonic_time() >= scadenza) {
			zwlr_output_configuration_v1_destroy(conf);
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "the compositor did not answer the size request within %.1f s "
			            "— and it is NOT a «no»: I do not know",
			            attesa_s);
			return WLR_MISURA_RIFIUTATA;
		}
	}
	zwlr_output_configuration_v1_destroy(conf);

	/* ⛔ Defect 4: three outcomes, three branches. */
	if (palco->conf == CONF_FALLITA)
		return WLR_MISURA_RIFIUTATA;
	if (palco->conf == CONF_ANNULLATA)
		return WLR_MISURA_ANNULLATA;

	/*
	 * ⛔⛔ AND HERE `palco->larghezza = larghezza` IS NOT WRITTEN: the compositor
	 *     said yes to the REQUEST, and that the output has changed will be said
	 *     by the `mode` event of the `wl_output` (`DECISIONI.md` §5.0-sexies).
	 *     One round, with a ceiling, to let it arrive.
	 */
	(void)giro(palco, attesa_s, NULL);
	return WLR_MISURA_CHIESTA;
}

/* ------------------------------------------------------------------------- */
/* ⭐⭐ The card: the public functions. */

bool wlr_chiedi_la_scheda(WlrPalco *p, GError **sbaglio)
{
	const char *come = NULL;
	gint64 scadenza;

	g_return_val_if_fail(p != NULL, false);
	if (p->scheda)
		return true;
	if (p->scheda_nata) {
		/* ⛔ It was born and turned off: it is not turned back on at every
		 *    request, or a compositor that refuses DMA-BUFs would make it
		 *    turn off and on again at every round. */
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "the card route had already turned off in this session");
		return false;
	}
	if (!p->dmabuf) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "the compositor does not announce zwp_linux_dmabuf_v1: I have no way "
		            "to give it a card buffer");
		return false;
	}
	if (zwlr_screencopy_manager_v1_get_version(p->manager) < 3) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_SUPPORTED,
		            "zwlr_screencopy_manager_v1 v%u: the `linux_dmabuf` event arrives "
		            "from v3",
		            zwlr_screencopy_manager_v1_get_version(p->manager));
		return false;
	}

	/* 1 · the node the compositor draws on — asked of it (v4).
	 *     ⛔ With a ceiling (defect 3): a feedback that does not close does not
	 *     stop the child, it only makes it take the node fallback, saying so. */
	if (p->dmabuf_versione >= 4) {
		struct zwp_linux_dmabuf_feedback_v1 *fb =
		    zwp_linux_dmabuf_v1_get_default_feedback(p->dmabuf);

		zwp_linux_dmabuf_feedback_v1_add_listener(fb, &ASCOLTO_FEEDBACK, p);
		scadenza = g_get_monotonic_time() + 2 * G_USEC_PER_SEC;
		while (!p->feedback_finito) {
			if (!pompa(p, scadenza, sbaglio)) {
				zwp_linux_dmabuf_feedback_v1_destroy(fb);
				return false;
			}
			if (!p->feedback_finito && g_get_monotonic_time() >= scadenza)
				break;
		}
		zwp_linux_dmabuf_feedback_v1_destroy(fb);
	}
	if (p->principale_noto) {
		p->nodo = nodo_da_dispositivo(p->principale);
		come = "stated by the compositor (`main_device`)";
	}
	if (!p->nodo) {
		p->nodo = nodo_come_sessione();
		come = "⚠ NOT stated by the compositor: taken with the rule of `sessione.c` "
		       "(the first openable renderD*), the same as WLR_RENDER_DRM_DEVICE";
	}
	if (!p->nodo) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no /dev/dri/renderD* node on which to allocate the card buffer");
		return false;
	}

	/* 2 · the node opens and `gbm` is born */
	p->drm_fd = open(p->nodo, O_RDWR | O_CLOEXEC);
	if (p->drm_fd < 0) {
		g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno), "%s: %s", p->nodo,
		            g_strerror(errno));
		g_clear_pointer(&p->nodo, g_free);
		return false;
	}
	p->gbm = gbm_create_device(p->drm_fd);
	if (!p->gbm) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "gbm_create_device on %s did not succeed", p->nodo);
		close(p->drm_fd);
		p->drm_fd = -1;
		g_clear_pointer(&p->nodo, g_free);
		return false;
	}
	for (unsigned i = 0; i < WLR_LASTRE; i++) {
		memset(&p->lastre[i], 0, sizeof p->lastre[i]);
		p->lastre[i].fd = -1;
	}
	/* ⚠ If there is already a pending frame, its `copy` (if started) goes to
	 *   memory: `lastra_del_giro` stays -1 and the card starts from the next one. */
	p->lastra_del_giro = -1;
	p->scheda_nata = true;
	p->scheda = true;
	registro_dice(AREA,
	              "⭐ wlroots: CARD route on — the slabs (%d, LINEAR "
	              "DMA-BUFs) are allocated on %s, %s; gbm backend «%s».  ⚠ Every "
	              "frame says by itself where it ended up: the route asked for is not the "
	              "route taken",
	              WLR_LASTRE, p->nodo, come, gbm_device_get_backend_name(p->gbm));
	return true;
}

bool wlr_sulla_scheda(const WlrPalco *p)
{
	return p && p->scheda;
}

void wlr_rendi(WlrPalco *p, void *lastra)
{
	WlrLastra *l = lastra;

	if (!p || !l)
		return;
	/* ⛔ The pointer is CHECKED: it must be one of our slabs.  A hold from
	 *    another stage touches nothing here. */
	if (l < &p->lastre[0] || l >= &p->lastre[WLR_LASTRE])
		return;
	/* ⛔ Only a slab IN HAND becomes free again: one returned twice is found
	 *    FREE (or IN FLIGHT, if it has already left again) and nothing happens.
	 *    ⚠ Never one IN FLIGHT: that one is closed by its frame. */
	if (l->stato != LASTRA_IN_MANO)
		return;
	lastra_torna_libera(p, l, false);
}

void wlr_lettura_cpu(int fd, bool inizio)
{
	struct dma_buf_sync s = {
		.flags = (inizio ? DMA_BUF_SYNC_START : DMA_BUF_SYNC_END) | DMA_BUF_SYNC_READ,
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

WlrEsito wlr_fotogramma(WlrPalco *palco, double attesa_s, WlrFotogramma *fuori, GError **sbaglio)
{
	gint64 scadenza;

	g_return_val_if_fail(palco != NULL, WLR_FOTOGRAMMA_ROTTO);
	g_return_val_if_fail(fuori != NULL, WLR_FOTOGRAMMA_ROTTO);

	scadenza = g_get_monotonic_time() + (gint64)(attesa_s * 1e6);

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
	 * `wlr_forza_intero()` raises the flag for the copy that STARTS; but if a
	 * damage copy is already in flight, on a still screen it never comes
	 * back, and the full copy never starts: the client attaching waits for a
	 * frame that does not arrive (C4: *«the after did not let itself be
	 * looked at: no frame in 8 s»*).  ⇒ The waiting one is abandoned — with
	 * the buffer marked, because the copy had started — and a full one is opened.
	 */
	if (palco->frame && palco->forza_intero && palco->copia_col_danno)
		chiudi_frame(palco, true);

	if (!palco->frame) {
		palco->visto_buffer = palco->visto_buffer_done = false;
		palco->pronto = palco->fallito = false;
		palco->copia_partita = palco->y_invertita = false;
		/* ⭐ the card: the offer belongs to THIS frame, and so does the slab */
		palco->offerto_scheda = false;
		palco->lastra_del_giro = -1;
		palco->conteggi.chiesti++;
		/* ⭐ `overlay_cursor = 1`: on this family the pointer is INSIDE the
		 *    image, and there is no channel for its shape. */
		palco->frame = zwlr_screencopy_manager_v1_capture_output(palco->manager, 1,
		                                                         palco->uscita);
		if (!palco->frame) {
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
			            "capture_output did not produce a frame");
			return WLR_FOTOGRAMMA_ROTTO;
		}
		zwlr_screencopy_frame_v1_add_listener(palco->frame, &ASCOLTO_FRAME, palco);
	}

	for (;;) {
		if (palco->fallito) {
			bool sulla_scheda = scheda_nel_giro(palco);

			/* ⚠ First it is closed (the slab becomes free, dirty), THEN it is
			 *   counted: if the count turns the card off, the slab is already
			 *   free and `scheda_spegni` throws it away with the others. */
			chiudi_frame(palco, false);
			palco->conteggi.falliti++;
			if (sulla_scheda && ++palco->falliti_di_fila >= WLR_SCHEDA_FALLITI_MAX)
				scheda_spegni(palco, "three `failed` in a row from the compositor on DMA-BUFs");
			return WLR_FOTOGRAMMA_FALLITO;
		}
		if (palco->pronto)
			break;
		/*
		 * The list of offers is closed and the copy has not started yet: the
		 * target is chosen and it starts.  ⭐ Only once per frame —
		 * `copia_partita` survives the timeout together with `frame` and
		 * `lastra_del_giro`, so the call that resumes a pending frame does
		 * NOT choose another slab.
		 */
		if (elenco_chiuso(palco) && !palco->copia_partita) {
			bool rotto = false;
			struct wl_buffer *dove = scheda_destinazione(palco, &rotto, sbaglio);

			if (rotto) {
				/* ⛔ No `copy` has started: closing the frame here leaves
				 *    nothing dirty. */
				chiudi_frame(palco, false);
				return WLR_FOTOGRAMMA_ROTTO;
			}
			if (!dove) {
				/* MEMORY: by default, or a fallback already declared */
				if (!prepara_buffer(palco, sbaglio)) {
					chiudi_frame(palco, false);
					return WLR_FOTOGRAMMA_ROTTO;
				}
				dove = palco->buffer;
			}
			/* ⭐ With damage, if the compositor can do it and nobody has asked
			 *    for a full frame: see `forza_intero` in the structure. */
			if (!palco->forza_intero &&
			    zwlr_screencopy_frame_v1_get_version(palco->frame) >= 2) {
				zwlr_screencopy_frame_v1_copy_with_damage(palco->frame, dove);
				palco->copia_col_danno = true;
				if (!palco->detto_il_danno) {
					palco->detto_il_danno = true;
					registro_dice(AREA,
					              "⭐ wlroots: from here frames are asked WITH "
					              "DAMAGE — the compositor answers only when the "
					              "screen has changed, as with the GNOME and KDE push");
				}
			} else {
				zwlr_screencopy_frame_v1_copy(palco->frame, dove);
				palco->forza_intero = false;
			}
			palco->copia_partita = true;
		}
		if (g_get_monotonic_time() >= scadenza) {
			/* ⭐ Timed out, but the frame STAYS pending: the next call resumes
			 *    it.  It is not a fault and not a failure.
			 * ⛔ And the slab in flight STAYS in flight: it does not get dirty,
			 *    is not freed, another one is not chosen (the box at the top). */
			palco->conteggi.scaduti++;
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "the frame is not ready yet after %.3f s — it stays in progress",
			            attesa_s);
			return WLR_FOTOGRAMMA_SCADUTO;
		}
		if (!pompa(palco, scadenza, sbaglio)) {
			/* ⛔ The wire dropped: if the copy had started, the buffer (or the
			 *    slab) is not reused. */
			chiudi_frame(palco, palco->copia_partita);
			return WLR_FOTOGRAMMA_ROTTO;
		}
	}

	/*
	 * ⭐ THE CARD DELIVERY: the fence, then the slab goes IN HAND.
	 *
	 * ⛔ If the fence does not fire in time the frame is NOT closed: it stays
	 *    pending with `pronto` true and the slab IN FLIGHT, and the next call
	 *    re-enters the loop above, finds `pronto`, and waits again on the
	 *    same fence.  No half blit delivered, no slab lost.
	 */
	if (scheda_nel_giro(palco)) {
		if (!scheda_aspetta_la_gpu(palco, &palco->lastre[palco->lastra_del_giro], scadenza,
		                           fuori, sbaglio)) {
			palco->conteggi.scaduti++;
			return WLR_FOTOGRAMMA_SCADUTO;
		}
		scheda_consegna(palco, fuori); /* ⚠ resets `lastra_del_giro` */
		chiudi_frame(palco, false);
		palco->conteggi.presi++;
		palco->conteggi.sulla_scheda++;
		return WLR_FOTOGRAMMA_PRESO;
	}

	chiudi_frame(palco, false);
	palco->conteggi.presi++;
	palco->conteggi.in_memoria++;
	/* ⛔ The card fields are written here too, empty: `fuori` may come from
	 *    a round on the card, and an `fd` left there would be a slab that does
	 *    not belong to this frame. */
	fuori->sulla_scheda = false;
	fuori->fd = -1;
	fuori->offset = 0;
	fuori->modificatore = DRM_FORMAT_MOD_LINEAR;
	fuori->generazione = 0;
	fuori->lastra = NULL;
	fuori->us_attesa_gpu = 0;
	fuori->attesa_esplicita = false;
	fuori->larghezza = palco->f_larghezza;
	fuori->altezza = palco->f_altezza;
	fuori->stride = palco->f_stride;
	/* ⭐ Translated to DRM for whoever is downstream (defect 1). */
	fuori->formato = shm_a_drm(palco->f_shm);
	fuori->pixel = palco->pixel;
	fuori->byte = palco->byte;
	if (fuori->formato == FOURCC('B', 'G', '2', '4') || fuori->formato == FOURCC('R', 'G', '2', '4'))
		allarga_24(palco, fuori);
	fuori->secondi = palco->f_secondi;
	fuori->nanosecondi = palco->f_nanosecondi;
	fuori->y_invertita = palco->y_invertita;
	return WLR_FOTOGRAMMA_PRESO;
}

/* ⭐ 24-bit pixels widened to 32 (see `largo` in the stage).  The extra
 *    byte is 0xff; the order of the three stays, and only the name changes:
 *    `BG24` → `XB24`, `RG24` → `XR24`. */
static void allarga_24(WlrPalco *p, WlrFotogramma *fuori)
{
	const uint32_t l = fuori->larghezza, a = fuori->altezza;
	const gsize passo = (gsize)l * 4u, serve = passo * a;

	if (fuori->stride < l * 3u || (gsize)fuori->stride * a > fuori->byte)
		return; /* ⚠ a shape that does not add up: whoever is downstream reports the discard */
	if (p->largo_byte < serve) {
		g_free(p->largo);
		p->largo = g_malloc(serve);
		p->largo_byte = serve;
	}
	for (uint32_t y = 0; y < a; y++) {
		const uint8_t *q = (const uint8_t *)fuori->pixel + (gsize)y * fuori->stride;
		uint8_t *d = p->largo + (gsize)y * passo;
		for (uint32_t x = 0; x < l; x++, q += 3, d += 4) {
			d[0] = q[0];
			d[1] = q[1];
			d[2] = q[2];
			d[3] = 0xff;
		}
	}
	fuori->formato = fuori->formato == FOURCC('B', 'G', '2', '4') ? FOURCC('X', 'B', '2', '4')
	                                                              : FOURCC('X', 'R', '2', '4');
	fuori->pixel = p->largo;
	fuori->byte = serve;
	fuori->stride = (uint32_t)passo;
}

void wlr_chiudi(WlrPalco *palco)
{
	if (!palco)
		return;
	/* ⛔ Defect 7: everything that was created is destroyed. */
	if (palco->frame)
		zwlr_screencopy_frame_v1_destroy(palco->frame);
	/* ⭐ the probe: its frame before its buffer, like the stream */
	sonda_chiudi_frame(palco);
	if (palco->s_buffer)
		wl_buffer_destroy(palco->s_buffer);
	if (palco->s_pixel)
		munmap(palco->s_pixel, palco->s_byte);
	if (palco->s_fd >= 0)
		close(palco->s_fd);
	if (palco->buffer)
		wl_buffer_destroy(palco->buffer);
	if (palco->pixel)
		munmap(palco->pixel, palco->byte);
	g_free(palco->largo);
	if (palco->fd >= 0)
		close(palco->fd);
	/* ⭐ the slabs, `gbm`, the node — AFTER the frame, which could name one
	 *    in a `copy` */
	scheda_chiudi(palco);
	if (palco->dmabuf)
		zwp_linux_dmabuf_v1_destroy(palco->dmabuf);
	if (palco->teste)
		g_ptr_array_free(palco->teste, TRUE);
	if (palco->gestore)
		zwlr_output_manager_v1_destroy(palco->gestore);
	if (palco->manager)
		zwlr_screencopy_manager_v1_destroy(palco->manager);
	if (palco->uscita)
		wl_output_destroy(palco->uscita);
	if (palco->shm)
		wl_shm_destroy(palco->shm);
	if (palco->registry)
		wl_registry_destroy(palco->registry);
	if (palco->display)
		wl_display_disconnect(palco->display);
	g_free(palco->uscita_nome);
	g_free(palco);
}
