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
#define AREA "cattura"

/* ⛔ The SAME clock as `figlio.c` (`ora_monotona_us`) and `codificatore.c`
 *    (`adesso_us`): the phase 8 segments are subtracted across different files,
 *    and two different clocks would give differences that mean nothing. */
static uint64_t adesso_us(void)
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
 * ⚠ It used to be `ATTESA_AVVIO_S`, ten seconds, and those ten seconds WERE the
 *   tail of the login times: see the box where it is used.  ⛔ The old
 *   constant was REMOVED, not left there unused: a constant that no longer
 *   controls anything is a trap for the reader. */
#define ATTESA_AGGANCIO_MS 10000

/* How many damaged regions we carry at most.  Beyond that, we declare that the
 * whole frame counts: it is the safe case. */
#define REGIONI_MAX 16

#define FD_MAX 8

/*
 * ⭐⭐ HOW OFTEN WE LOOK AT THE PIXELS — the biggest cure of phase 8 on the
 *     `capture → first byte` segment, and it lives in a constant.
 *
 * ⛔ THE FACT, `[M]` 22 August 2026, test machine (i5-13500T), 2 450
 *    frames at 1920x1080 with hardware HEVC:
 *
 *      the whole segment                      **21.61 ms**
 *      of which `misura_i_pixel()`            **5.34 ms — 25 %**
 *
 *    and `[M]` on pure CPU (bench `08-c-scansione.c`) the same scan costs
 *    **5.36 ms** at 1920x1080 and **8.89** at 2560x1440: it grows with pixels, so
 *    on a large canvas it would be **worse**.
 *
 * ⛔⛔ AND WHAT IT WAS FOR, counted line by line: in the product those three values
 *      (`nero`, `uniforme`, the range) end up in **ONE** log line,
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
#ifndef MISURA_PIXEL_OGNI_MS
#define MISURA_PIXEL_OGNI_MS 500
#endif

/*
 * How many bytes the cursor metadata must have to carry a bitmap of
 * `w x h`.  ⛔ It is the same formula as Mutter's (`CURSOR_META_SIZE`,
 * `meta-screen-cast-stream-src.c:63`) and it lives here because it is a quantity of the
 * PipeWire NEGOTIATION, not of the wire: the wire's ceiling is 256 and lives in
 * `cursore.h`.
 */
#define CURSORE_META_BYTE(l, a)                                                                    \
	((int) (sizeof(struct spa_meta_cursor) + sizeof(struct spa_meta_bitmap) + (l) * (a) * 4))

struct Cattura
{
	/*
	 * ⭐⭐ PHASE 13 — THE SECOND SOURCE, and it sits AT THE TOP on purpose.
	 *
	 * When this field is set, the `Cattura` is not a PipeWire stream: it is a
	 * Wayland client that PULLS the frames (`wlroots.h`).  ⛔ All the fields
	 * below stay zero and are not touched, and every public function
	 * hands over at the top — so the GNOME and KDE code stays
	 * textually what it was before.
	 */
	WlrPalco *wlr;
	WlrFotogramma wlr_ultimo;
	gboolean wlr_ultimo_noto;
	gboolean wlr_detto_il_testimone, wlr_detto_y;
	gboolean wlr_detto_ripiego;      /* «card requested, memory arrived» */
	gboolean wlr_guardato_il_primo;  /* the first card frame, mapped */
	/* ⭐ The true shape on labwc (the probe, `wlroots.h`): the last one DELIVERED,
	 *    so as not to resend the same image under two names (`default` and
	 *    `left_ptr` are the same drawing), and the serial that `forma.h` leaves to
	 *    whoever delivers. */
	CursoreForma wlr_forma;
	gboolean wlr_forma_data;
	guint64 wlr_forme_mandate, wlr_forme_uguali;

	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;
	struct pw_stream *flusso;
	struct spa_hook gancio;

	struct spa_video_info_raw formato;
	gboolean formato_noto;

	CatturaFotogramma su_fotogramma;
	CatturaFine su_fine;
	gpointer dati;

	enum pw_stream_state stato;
	char *guasto;
	gboolean fine_segnalata;
	gboolean detto_il_tipo;

	CatturaStrada strada;
	CatturaColore colore;
	uint32_t chiesta_larghezza, chiesta_altezza;
	/* ⛔ The rate REQUESTED at startup, kept because `cattura_ridimensiona()`
	 *    repeats the same proposal: putting a hand-written one in there
	 *    would mean that after a resize the stream runs at a rate
	 *    different from the one it was born with — and no line would say so. */
	uint32_t chiesti_al_secondo;
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
	 *     `cattura_ridimensiona()`**: the `Format` of the FIRST comes back
	 *     when `chiesta_*` already carries the SECOND.  Measured **43 times out of 480
	 *     chains** (three sweeps of 160), with most hits between **200 and 800
	 *     us** apart between the two calls and tails down to 0 and up to 3200 us — and the
	 *     line said *«requested 1602x1020, granted 1202x806»*,
	 *     that is «granted» was **the previous request**, not a different
	 *     grant by the producer.  ⇒ In that scene the field is a **false
	 *     alarm**, and it turns itself off at the next `Format`.
	 *   · `[M]` The opposite scene — the producer IMPOSING a size of its own — does not
	 *     exist: `proposta()` declares a FIXED rectangle, so
	 *     the intersection is either that value or the empty set (case 5: the stage
	 *     demands 1600x900, the stream goes to `error`, no divergence).
	 *
	 * ⇒ ⛔ Exporting it would mean giving the caller a `TRUE` that in the only
	 *   measured scene is **wrong**.  And it would not help: `cattura.h` already
	 *   exposes `cattura_misura_chiesta()` and `cattura_misura_negoziata()`, and the
	 *   divergence is their inequality (case 6).  ⭐ The real verdict is
	 *   given by the FRAME, in `figlio.c`, and it is the rule that §5.0-sexies had
	 *   already written: *«the truth is told by the frame, not by the outcome of the
	 *   request»*. */
	gboolean misura_divergente;

	/* --- the counters, which run on the real-time thread ---------------- *
	 * ⚠ THEY ARE COUNTED, NOT PRINTED: one log line per frame
	 *   would distort the very thing being watched.  The first is said, and then a
	 *   summary every three hundred. */
	CatturaConteggi conto;
	int fd_visti[FD_MAX];
	uint32_t primo_tipo_grezzo; /* the SPA value, for whoever wants the bare number */

	/* --- the slot of whoever waits for a frame -------------------------- *
	 * ⛔ The slot exists only while someone waits: a frame that arrives
	 *    when nobody wants it is just counted.  Copying 8 MB for nobody
	 *    would be work inside the real-time callback, done for nothing. */
	GMutex lucchetto;
	GCond novita;
	gboolean qualcuno_aspetta;
	CatturaFermo posto;
	gboolean posto_pieno;
	/* ⭐ The capacity of the slot's buffer: it is REUSED instead of remade at every
	 *    frame.  ⛔ It is needed because now we ALWAYS copy (see below), and
	 *    a `g_malloc`/`g_free` of 8 MB sixty times per second inside the
	 *    real-time callback would be a cure worse than the disease. */
	size_t posto_capienza;
	/* ⛔ How many times a frame not yet consumed was replaced by
	 *    a more recent one.  ⚠ It is NOT a fault — it is the intended behaviour,
	 *    «the newest wins» — but it is also the number that says how often the
	 *    consumer is late, and before 15 August 2026 those frames
	 *    were LOST instead of replaced. */
	uint64_t sovrascritti;

	/* ⭐ The rate of the pass over the pixels — see `MISURA_PIXEL_OGNI_MS`.  ⛔ They live
	 *    on the CALLER's thread (`cattura_prendi`), not on the real-time
	 *    one: no lock is needed, and adding one would suggest that
	 *    one is needed. */
	uint64_t misura_ultima_us;
	guint64 misura_fatte, misura_saltate;
	/* ⚠ On the card the pixels are looked at only if the buffer can be mapped: it is
	 *   said once if it could not be, and then we stay quiet. */
	gboolean detta_misura_impossibile;

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
	 *   not four (`parametri_di_consumo`).
	 *
	 * ⛔ And the buffer is given back with the PipeWire loop lock held,
	 *    because whoever returns it is on ANOTHER thread (the consumer's) —
	 *    while `su_processo` runs on the real-time one, which already has
	 *    the lock.  The order is always `loop → lock`, never the reverse.
	 */
	guint64 ritenuti;      /* how many buffers have been held in total         */
	guint64 ritenuti_resi; /* how many came back: the difference is how many   */
	                       /* we hold right now                                */
	/* ⛔ It changes every time PipeWire allocates or frees the buffers.  ⚠ Whoever
	 *    caches the import of an `fd` must watch it: descriptor numbers
	 *    are recycled, and a blind cache would point to a dead buffer
	 *    without any error. */
	uint64_t generazione_buffer;

	/* --- ⭐ THE CURSOR CHANNEL ------------------------------------------- *
	 *
	 * ⛔ `cattura.c` does NOT know the wire: it reads the raw metadata and passes it to
	 *    `cursore.c`, which is the only place where the shape becomes a
	 *    `CursoreForma` (see `cursore.h`).
	 *
	 * ⚠ The module always exists, even if nobody listens: that way the counters
	 *   say whether the metadata REALLY arrives, regardless of whether
	 *   someone consumes it.  The listener registers later, with
	 *   `cattura_cursore`, and the two fields are read under the lock because
	 *   whoever registers is on another thread. */
	Cursore *cursore;
	CursoreArrivata cursore_fn;
	void *cursore_chi;
	gboolean detto_il_cursore; /* the first metadata is said once */
};

/* ------------------------------------------------------------------ *
 *  The names — a single place, so that whoever writes a manifest does not reinvent them
 * ------------------------------------------------------------------ */

const char *cattura_buffer_nome(CatturaBuffer buffer)
{
	switch (buffer)
	{
	case CATTURA_BUFFER_MEMFD: return "MemFd";
	case CATTURA_BUFFER_MEMPTR: return "MemPtr";
	case CATTURA_BUFFER_MEMID: return "MemId";
	case CATTURA_BUFFER_DMABUF: return "DMA-BUF";
	default: return "UNKNOWN";
	}
}

static CatturaBuffer buffer_da_spa(uint32_t tipo)
{
	switch (tipo)
	{
	case SPA_DATA_MemFd: return CATTURA_BUFFER_MEMFD;
	case SPA_DATA_MemPtr: return CATTURA_BUFFER_MEMPTR;
	case SPA_DATA_MemId: return CATTURA_BUFFER_MEMID;
	case SPA_DATA_DmaBuf: return CATTURA_BUFFER_DMABUF;
	default: return CATTURA_BUFFER_IGNOTO;
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
static uint32_t drm_da_spa(uint32_t formato_spa)
{
	switch (formato_spa)
	{
	case SPA_VIDEO_FORMAT_BGRx: return DRM_FORMAT_XRGB8888;
	case SPA_VIDEO_FORMAT_BGRA: return DRM_FORMAT_ARGB8888;
	case SPA_VIDEO_FORMAT_RGBx: return DRM_FORMAT_XBGR8888;
	case SPA_VIDEO_FORMAT_RGBA: return DRM_FORMAT_ABGR8888;
	default: return 0;
	}
}

const char *cattura_colore_nome(uint32_t formato_grezzo)
{
	switch (formato_grezzo)
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

const char *cattura_fonte_nome(CatturaFonte fonte)
{
	switch (fonte)
	{
	case CATTURA_FONTE_PRODUTTORE: return "requested from the producer (SPA_PARAM_Format)";
	case CATTURA_FONTE_FORMATO: return "follows from the negotiated format";
	case CATTURA_FONTE_MISURATA: return "[M] measured by us on the delivered pixels";
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
const char *cattura_range_nome(uint32_t grezzo)
{
	switch (grezzo)
	{
	case 1: return "FULL (0-255)";
	case 2: return "LIMITED (16-235)";
	default: return "NOT DECLARED by the producer";
	}
}

const char *cattura_matrice_nome(uint32_t grezzo)
{
	switch (grezzo)
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

const char *cattura_trasferimento_nome(uint32_t grezzo)
{
	switch (grezzo)
	{
	case 1: return "gamma 1.0 (linear)";
	case 4: return "gamma 2.2";
	case 5: return "BT.709";
	case 7: return "sRGB";
	case 11: return "BT.2020 12 bit";
	default: return "NOT DECLARED by the producer";
	}
}

const char *cattura_primari_nome(uint32_t grezzo)
{
	switch (grezzo)
	{
	case 1: return "BT.709";
	case 4: return "SMPTE170M";
	case 7: return "BT.2020";
	default: return "NOT DECLARED by the producer";
	}
}

const char *cattura_range_misurato_nome(CatturaRangeMisurato misurato)
{
	switch (misurato)
	{
	case CATTURA_RANGE_COMPATIBILE_PIENO:
		return "[M] the pixels reach 0 and 255: compatible with FULL";
	case CATTURA_RANGE_NON_CONCLUSIVO:
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
static int bit_per_canale(uint32_t formato)
{
	switch (formato)
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
static gboolean posizioni_rgb(uint32_t formato, int *r, int *g, int *b)
{
	switch (formato)
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

static void su_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *errore)
{
	Cattura *cattura = dati;

	registro_dettaglio(AREA, "stream state: %s → %s%s%s", pw_stream_state_as_string(vecchio),
	                   pw_stream_state_as_string(nuovo), errore ? " — " : "", errore ? errore : "");
	cattura->stato = nuovo;
	if (errore)
	{
		g_free(cattura->guasto);
		cattura->guasto = g_strdup(errore);
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
	if ((vecchio == PW_STREAM_STATE_PAUSED || vecchio == PW_STREAM_STATE_STREAMING) &&
	    nuovo == PW_STREAM_STATE_UNCONNECTED && !cattura->fine_segnalata)
	{
		cattura->fine_segnalata = TRUE;
		registro_dice(AREA, "the capture stream has detached");
		if (cattura->su_fine)
			cattura->su_fine(cattura->dati);
	}

	/* Whoever waits for a frame must wake up also when the stream dies, or
	 * they would wait the whole timeout for a frame that can no longer arrive. */
	g_mutex_lock(&cattura->lucchetto);
	g_cond_broadcast(&cattura->novita);
	g_mutex_unlock(&cattura->lucchetto);

	pw_thread_loop_signal(cattura->ciclo, false);
}

/*
 * ⛔ THE BOUNCE TOWARDS THE LISTENER, and it is not a convenience: `cursore_apri` wants
 *    the recipient at opening time, but the stream starts before
 *    anyone registers.  Without the bounce the first shape — the one that arrives
 *    with the first pointer movement — would have nowhere to go.
 *
 * ⚠ It runs on PipeWire's real-time thread: whoever registers here must not
 *   wait for anything (`cattura.h`, the box on the loop).
 */
static int cursore_rimbalzo(void *chi, const CursoreForma *forma)
{
	Cattura *cattura = chi;
	CursoreArrivata fn;
	void *dove;

	g_mutex_lock(&cattura->lucchetto);
	fn = cattura->cursore_fn;
	dove = cattura->cursore_chi;
	g_mutex_unlock(&cattura->lucchetto);

	/* ⛔ Nobody listening is NOT an error: the shape has been counted anyway, and
	 *    it is precisely the case in which the bench measures the source without the
	 *    wire. */
	if (!fn)
		return 0;
	return fn(dove, forma);
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
static uint32_t parametri_di_consumo(Cattura *cattura, struct spa_pod_builder *costruttore,
                                     const struct spa_pod *parametri[4])
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
	int tipi = (1 << SPA_DATA_MemFd) | (1 << SPA_DATA_MemPtr);
	if (cattura->strada == CATTURA_STRADA_SCHEDA)
		tipi = (1 << SPA_DATA_DmaBuf);

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
	 *    `buffer_distinti` — which is counted, not assumed. */
	int quanti = cattura->strada == CATTURA_STRADA_SCHEDA ? 6 : 4;
	int minimo = cattura->strada == CATTURA_STRADA_SCHEDA ? 4 : 2;

	parametri[0] = spa_pod_builder_add_object(
	    costruttore, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
	    SPA_POD_CHOICE_RANGE_Int(quanti, minimo, 8), SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int(tipi));

	/*
	 * ⛔ METADATA ARE REQUESTED, OR THEY DO NOT ARRIVE — and without them the producer
	 *    has no way to tell us anything about the frame: neither which one it is (`seq`), nor
	 *    how much of it was repainted (`VideoDamage`).
	 *
	 * ⚠ Requesting a metadata does NOT oblige the producer to give it: the reader must
	 *   cope with its absence, and that is why every read checks the pointer
	 *   and counts the absences instead of taking them as zero.
	 */
	parametri[1] = spa_pod_builder_add_object(
	    costruttore, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_Header), SPA_PARAM_META_size,
	    SPA_POD_Int(sizeof(struct spa_meta_header)));
	parametri[2] = spa_pod_builder_add_object(
	    costruttore, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
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
	parametri[3] = spa_pod_builder_add_object(
	    costruttore, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_Cursor), SPA_PARAM_META_size,
	    SPA_POD_CHOICE_RANGE_Int(CURSORE_META_BYTE(384, 384), CURSORE_META_BYTE(1, 1),
	                             CURSORE_META_BYTE(384, 384)));
	return 4;
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	Cattura *cattura = dati;
	uint32_t tipo, sottotipo;
	uint8_t spazio[1024];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[4];

	if (!param || id != SPA_PARAM_Format)
		return;
	if (spa_format_parse(param, &tipo, &sottotipo) < 0)
		return;
	if (tipo != SPA_MEDIA_TYPE_video || sottotipo != SPA_MEDIA_SUBTYPE_raw)
		return;
	if (spa_format_video_raw_parse(param, &cattura->formato) < 0)
	{
		registro_dice(AREA, "⚠ capture format cannot be interpreted");
		return;
	}

	cattura->formato_noto = TRUE;
	registro_dice(AREA, "negotiated format: %ux%u %s (%d bits per channel), modifier 0x%" G_GINT64_MODIFIER "x",
	              cattura->formato.size.width, cattura->formato.size.height,
	              cattura_colore_nome(cattura->formato.format),
	              bit_per_canale(cattura->formato.format), (guint64) cattura->formato.modifier);

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
	 *   caller, which knows whether it can still serve the client (`CODER.md` §4.2 — a
	 *   silent fallback produces two behaviours under the same label).
	 *
	 * ---------------------------------------------------------------------
	 * ⛔⛔ 22 AUGUST 2026 — THE LINE IS REACHED, AND WHAT IT SAID WAS FALSE
	 *
	 * `fasi/06` §7.2 kept this line among the *«code never exercised»*, and
	 * `banchi/06-b40` had concluded that the branch **cannot be reached
	 * from outside**: with the FIXED rectangle of `proposta()` the intersection is either
	 * the requested value or the empty set, so every `Format` that arrives
	 * necessarily carries the requested size.
	 *
	 * ⭐ `[M]` `banchi/06-b5-esiti-cattura.c` case 4: **it is reached**, 43 times
	 *    out of 480, and the door is not the producer — it is TIME.  Two
	 *    chained `cattura_ridimensiona()` (the user DRAGGING the edge
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
	if (cattura->chiesta_larghezza && cattura->chiesta_altezza
	    && (cattura->formato.size.width != cattura->chiesta_larghezza
	        || cattura->formato.size.height != cattura->chiesta_altezza))
	{
		if (!cattura->misura_divergente)
			registro_dice(AREA,
			              "⛔ DIVERGENT SIZE: requested %ux%u, granted %ux%u.  ⚠ Two "
			              "motives, and from here they cannot be told apart: either the compositor "
			              "granted something else (§4.5 allows it, and then the coordinate "
			              "conversion would be born wrong), or this is the "
			              "answer to a SUPERSEDED request — `[M]` two "
			              "chained resizes, bench 06-b5 case 4.  ⭐ The "
			              "verdict is given by the FRAME (`DECISIONI.md` §5.0-sexies), "
			              "not by this line",
			              cattura->chiesta_larghezza, cattura->chiesta_altezza,
			              cattura->formato.size.width, cattura->formato.size.height);
		cattura->misura_divergente = TRUE;
	}
	else
		cattura->misura_divergente = FALSE;

	/* ⛔ And the four consumption parameters are written by `parametri_di_consumo()`, in
	 *    a single place: `cattura_ridimensiona()` repeats them too, and two lists
	 *    that must stay equal are two lists that diverge. */
	pw_stream_update_params(cattura->flusso, parametri,
	                        parametri_di_consumo(cattura, &costruttore, parametri));
	pw_thread_loop_signal(cattura->ciclo, false);
}

/*
 * ⭐ The cursor metadata, read and handed to `cursore.c`.
 *
 * ⛔ IT IS READ BEFORE ANY `goto restituisci`, and the reason was already written
 *    in the box of `su_processo`: a buffer marked `CORRUPTED` is a buffer
 *    WITHOUT a frame, sent **precisely because** the cursor moved.  Whoever
 *    read the cursor after the discard would lose exactly the buffers that
 *    carry the cursor.
 *
 * ⚠ And we look at `spa_meta` and not `spa_buffer_find_meta_data`: we need the
 *   real SIZE of the metadata, or the checks in `cursore.c` have no
 *   limit against which to measure the bitmap pixels.
 */
static void guarda_cursore(Cattura *cattura, struct pw_buffer *pacco)
{
	struct spa_meta *meta;

	if (!cattura->cursore)
		return;

	meta = spa_buffer_find_meta(pacco->buffer, SPA_META_Cursor);
	if (!meta || !meta->data)
	{
		/* ⛔ «Not received» is NOT «hidden»: it is counted, and nothing is sent
		 *    on the wire.  Whoever reads zero `CURSORE_FORMA` later must
		 *    be able to tell «the pointer was not there» from «we did not request the metadata,
		 *    or the producer did not give it». */
		cattura->conto.cursore_assente++;
		return;
	}

	cattura->conto.cursore_metadati++;
	if (!cattura->detto_il_cursore)
	{
		cattura->detto_il_cursore = TRUE;
		registro_dice(AREA, "⭐ the cursor metadata ARRIVES: %u bytes per buffer", meta->size);
	}

	if (cursore_metadato(cattura->cursore, meta->data, meta->size) < 0)
		cattura->conto.cursore_malformati++;
}

/* The damage: looked at, counted, and delivered as INFORMATION. */
static gboolean guarda_danno(Cattura *cattura, struct pw_buffer *pacco, CatturaRegione *regioni,
                             guint *quante, gboolean *copre_tutto)
{
	struct spa_meta *meta = spa_buffer_find_meta(pacco->buffer, SPA_META_VideoDamage);
	struct spa_meta_region *regione;
	gboolean vista = FALSE;

	*quante = 0;
	*copre_tutto = FALSE;

	if (!meta)
	{
		cattura->conto.danno_assente++;
		return FALSE;
	}
	spa_meta_for_each(regione, meta)
	{
		if (!spa_meta_region_is_valid(regione))
			break;
		vista = TRUE;
		if (regione->region.position.x == 0 && regione->region.position.y == 0 &&
		    regione->region.size.width >= cattura->formato.size.width &&
		    regione->region.size.height >= cattura->formato.size.height)
			*copre_tutto = TRUE;
		if (*quante < REGIONI_MAX)
		{
			regioni[*quante].x = (uint32_t) MAX(0, regione->region.position.x);
			regioni[*quante].y = (uint32_t) MAX(0, regione->region.position.y);
			regioni[*quante].larghezza = regione->region.size.width;
			regioni[*quante].altezza = regione->region.size.height;
			(*quante)++;
		}
		else
		{
			/* We err on the safe side: more regions than we carry
			 * ⇒ we declare «everything counts» instead of delivering part of them. */
			*quante = 0;
			*copre_tutto = TRUE;
			break;
		}
	}
	if (!vista)
	{
		cattura->conto.danno_assente++;
		return FALSE;
	}
	if (*copre_tutto)
		cattura->conto.danno_pieno++;
	else
		cattura->conto.danno_parziale++;
	return TRUE;
}

static void su_processo(void *dati)
{
	Cattura *cattura = dati;
	struct pw_buffer *pacco;
	struct spa_data *piano;
	struct spa_meta_header *intestazione;
	CatturaRegione regioni[REGIONI_MAX];
	CatturaFotogrammaInfo info = { 0 };
	CatturaConsegna consegna;
	guint quante = 0;
	gboolean copre_tutto = FALSE, danno_dichiarato;
	uint32_t passo, offset;
	guint64 disponibili, byte;
	guint i;
	gboolean noto;
	/* ⭐ The RETENTION: when this becomes TRUE the buffer does NOT go back to PipeWire
	 *    at the end of the function — it will be returned by `cattura_fermo_libera()`, that is by
	 *    the consumer, when it has finished reading it.  See the box at the top. */
	gboolean trattenuto = FALSE;

	pacco = pw_stream_dequeue_buffer(cattura->flusso);
	if (!pacco)
		return;

	/* ⛔ BEFORE ANY DISCARD: see the box of `guarda_cursore`. */
	guarda_cursore(cattura, pacco);

	if (pacco->buffer->n_datas == 0)
		goto restituisci;
	piano = &pacco->buffer->datas[0];
	cattura->conto.arrivati++;

	/* How many distinct buffers the producer recycles: Mutter uses four, and
	 * knowing it helps read the rest. */
	noto = FALSE;
	for (i = 0; i < cattura->conto.buffer_distinti; i++)
		if (cattura->fd_visti[i] == (int) piano->fd)
			noto = TRUE;
	if (!noto && cattura->conto.buffer_distinti < FD_MAX)
		cattura->fd_visti[cattura->conto.buffer_distinti++] = (int) piano->fd;

	/* ⛔ THE TYPES ARE ALL COLLECTED, not just the last one: if the
	 *    producer changed route midway, a single line would state one
	 *    route for two different populations — which is form E2. */
	noto = FALSE;
	for (i = 0; i < cattura->conto.quanti_tipi; i++)
		if (cattura->conto.tipi_visti[i] == buffer_da_spa(piano->type))
			noto = TRUE;
	if (!noto && cattura->conto.quanti_tipi < G_N_ELEMENTS(cattura->conto.tipi_visti))
	{
		if (cattura->conto.quanti_tipi == 0)
			cattura->primo_tipo_grezzo = piano->type;
		cattura->conto.tipi_visti[cattura->conto.quanti_tipi++] = buffer_da_spa(piano->type);
	}

	if (!cattura->detto_il_tipo)
	{
		cattura->detto_il_tipo = TRUE;
		/* ⛔ Said ONCE and in full, with next to it what it does NOT prove. */
		registro_dice(AREA,
		              "the frames arrive as %s (%u planes) — ⚠ and this does NOT say where "
		              "Mutter renders: it is the answer to what we asked for (E1)",
		              cattura_buffer_nome(buffer_da_spa(piano->type)), pacco->buffer->n_datas);
	}

	if (!piano->chunk)
	{
		cattura->conto.senza_pixel++;
		goto restituisci;
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
		cattura->conto.solo_cursore++;
		goto restituisci;
	}
	intestazione = spa_buffer_find_meta_data(pacco->buffer, SPA_META_Header, sizeof *intestazione);
	if (!intestazione)
		cattura->conto.senza_intestazione++;
	else if (intestazione->flags & SPA_META_HEADER_FLAG_CORRUPTED)
	{
		cattura->conto.solo_cursore++;
		goto restituisci;
	}

	danno_dichiarato = guarda_danno(cattura, pacco, regioni, &quante, &copre_tutto);

	/* ⛔ The authoritative stride is this one, and if it is missing none is computed. */
	passo = (uint32_t) MAX(0, piano->chunk->stride);
	if (passo == 0)
	{
		cattura->conto.stride_zero++;
		goto restituisci;
	}
	offset = (uint32_t) piano->chunk->offset;

	/* --- the four facts, frozen for this frame -------------------------- */
	memset(&consegna, 0, sizeof consegna);
	consegna.noto = cattura->formato_noto;
	consegna.strada_chiesta = cattura->strada;
	consegna.buffer_chiesto =
	    cattura->strada == CATTURA_STRADA_SCHEDA ? CATTURA_BUFFER_DMABUF : CATTURA_BUFFER_MEMFD;
	consegna.buffer_dichiarato = buffer_da_spa(piano->type);
	consegna.buffer_dichiarato_grezzo = piano->type;
	consegna.buffer_distinti = cattura->conto.buffer_distinti;
	consegna.formato_grezzo = cattura->formato.format;
	consegna.formato = cattura_colore_nome(cattura->formato.format);
	consegna.bit_per_canale = bit_per_canale(cattura->formato.format);
	consegna.fonte_bit = consegna.bit_per_canale > 0 ? CATTURA_FONTE_FORMATO
	                                                 : CATTURA_FONTE_NON_DICHIARATA;
	consegna.larghezza = cattura->formato.size.width;
	consegna.altezza = cattura->formato.size.height;
	consegna.stride = passo;
	consegna.stride_letto = TRUE;
	consegna.byte = (guint64) passo * cattura->formato.size.height;
	consegna.modificatore = cattura->formato.modifier;
	consegna.range_grezzo = cattura->formato.color_range;
	consegna.matrice_grezza = cattura->formato.color_matrix;
	consegna.trasferimento_grezzo = cattura->formato.transfer_function;
	consegna.primari_grezzi = cattura->formato.color_primaries;
	consegna.fonte_range =
	    cattura->formato.color_range ? CATTURA_FONTE_PRODUTTORE : CATTURA_FONTE_NON_DICHIARATA;
	consegna.fonte_matrice =
	    cattura->formato.color_matrix ? CATTURA_FONTE_PRODUTTORE : CATTURA_FONTE_NON_DICHIARATA;

	/* --- how many bytes there really are -------------------------------- */
	disponibili = piano->maxsize > offset ? (guint64) piano->maxsize - offset : 0;
	byte = piano->chunk->size > 0 ? (guint64) piano->chunk->size : disponibili;
	if (byte > disponibili)
		byte = disponibili;

	/* ⛔⛔ THE DECLARED GEOMETRY MUST FIT INSIDE THE DELIVERED BYTES — the
	 *     guard born while refuting, on the night of 15 August 2026, and before that it
	 *     served no purpose.
	 *
	 * ⚠ The size comes from the negotiated FORMAT (`cattura->formato`), the stride and the
	 *   bytes come from the CHUNK of the real buffer: two sources, and between a
	 *   renegotiation and the new buffers they can belong to two different
	 *   generations.  ⛔ With a fixed canvas they could not diverge;
	 *   `cattura_ridimensiona()` makes it possible.
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
	if (cattura->strada == CATTURA_STRADA_MEMORIA
	    && (cattura->formato.size.width == 0 || cattura->formato.size.height == 0
	        || passo < cattura->formato.size.width * 4u
	        || byte < (guint64) passo * cattura->formato.size.height))
	{
		cattura->conto.geometria_incoerente++;
		if (cattura->conto.geometria_incoerente == 1)
			registro_dice(AREA,
			              "⛔ frame DISCARDED: the format declares %ux%u but the buffer "
			              "carries stride %u and %" G_GUINT64_FORMAT " bytes (%"
			              G_GUINT64_FORMAT " would be needed).  ⚠ It is the window between a renegotiation and "
			              "the new buffers: the reader would go beyond the delivered memory",
			              cattura->formato.size.width, cattura->formato.size.height, passo,
			              byte, (guint64) passo * cattura->formato.size.height);
		goto restituisci;
	}

	info.pixel = NULL;
	info.byte = byte;
	info.fd = piano->fd >= 0 ? (int) piano->fd : -1;
	info.offset = offset;
	info.stride = passo;
	info.seq = intestazione ? (uint64_t) intestazione->seq : 0;
	info.pts = intestazione ? (int64_t) intestazione->pts : 0;
	info.seq_nota = intestazione != NULL;
	info.danno = quante ? regioni : NULL;
	info.quante_regioni = quante;
	info.danno_dichiarato = danno_dichiarato;
	info.danno_copre_tutto = copre_tutto;
	info.indice = cattura->conto.arrivati;
	info.consegna = &consegna;

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
			cattura->conto.senza_pixel++;
			goto restituisci;
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
	else if (info.fd < 0 || drm_da_spa(cattura->formato.format) == 0
	         || pacco->buffer->n_datas != 1)
	{
		cattura->conto.senza_pixel++;
		if (cattura->conto.senza_pixel == 1)
			registro_dice(AREA,
			              "⛔ DMA-BUF DISCARDED: fd %d, format «%s» (%u), %u planes.  On the "
			              "card route we need a descriptor, a format that can be "
			              "NAMED in DRM, and a single plane — ⚠ and this is NOT «the "
			              "producer does not deliver»: it is «I cannot describe it»",
			              info.fd, cattura_colore_nome(cattura->formato.format),
			              cattura->formato.format, pacco->buffer->n_datas);
		goto restituisci;
	}

	if (cattura->su_fotogramma)
		cattura->su_fotogramma(&info, cattura->dati);

	/* --- the slot of the LAST frame --------------------------------------- *
	 *
	 * ⛔⛔⛔ AND UNTIL 15 AUGUST 2026 HERE THERE WAS `if (qualcuno_aspetta && !posto_pieno)`,
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
	 *   `qualcuno_aspetta == FALSE` and **are thrown away**, including **the last one** —
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
	 *   more: the buffer is REUSED (`posto_capienza`), so the real-time
	 *   callback does a `memcpy` and no longer a `g_free`+`g_malloc` of 8 MB.
	 */
	g_mutex_lock(&cattura->lucchetto);
	{
		CatturaFermo *f = &cattura->posto;

		if (cattura->posto_pieno)
			cattura->sovrascritti++;

		/* ⛔⭐ AND THE BUFFER THAT WAS IN THE SLOT IS GIVEN BACK **NOW**, before
		 *     overwriting it: it is a buffer nobody consumed — the most
		 *     recent wins — and if it did not go back the producer would
		 *     lose one at every skipped frame.  ⚠ We are already on the real-time
		 *     thread, which holds the loop for us: here we call the bare
		 *     `pw_stream_queue_buffer` and not `rendi_ritenuta`, which
		 *     would take again a lock that is already ours. */
		if (f->ritenuta)
		{
			pw_stream_queue_buffer(cattura->flusso, (struct pw_buffer *) f->ritenuta);
			cattura->ritenuti_resi++;
			f->ritenuta = NULL;
			f->padrone = NULL;
		}

		f->byte = info.pixel ? byte : 0;
		f->us_allocazione = 0;
		f->us_copia = 0;
		f->us_nel_posto = 0;
		f->us_misura = 0;
		f->sulla_scheda = FALSE;
		f->fd = -1;
		f->offset = 0;
		f->formato_drm = 0;
		f->modificatore = 0;
		f->generazione = cattura->generazione_buffer;

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
		if (cattura->strada == CATTURA_STRADA_SCHEDA)
		{
			f->sulla_scheda = TRUE;
			f->fd = info.fd;
			f->offset = offset;
			f->formato_drm = drm_da_spa(cattura->formato.format);
			f->modificatore = cattura->formato.modifier;
			f->byte = (guint64) passo * cattura->formato.size.height;
			f->ritenuta = pacco;
			f->padrone = cattura;
			trattenuto = TRUE;
			cattura->ritenuti++;
		}
		else if (info.pixel)
		{
			/* ⛔ WE COPY, WE DO NOT KEEP THE POINTER: on the next round the producer
			 *    writes into it again, and the delivered frame would be a different one
			 *    from the one whose damage and sequence we report — two measurements
			 *    under the same label.
			 * ⭐ But the allocation is REUSED when it is enough: it is the same size for
			 *    the whole session, except at a canvas change. */
			if (!f->pixel || cattura->posto_capienza < byte)
			{
				/* ⛔ The `g_malloc` is TIMED, and it is not pedantry: when the
				 *    slot is emptied at every take (see `cattura_prendi`) this
				 *    line reallocates **at every frame**, and a new 10 MB
				 *    mapping is paid in page faults the first time it is
				 *    touched — that is inside the `memcpy` below. */
				uint64_t ta = adesso_us();
				g_free(f->pixel);
				f->pixel = g_malloc(byte);
				cattura->posto_capienza = byte;
				f->us_allocazione = adesso_us() - ta;
			}
			{
				uint64_t tc = adesso_us();
				memcpy(f->pixel, info.pixel, byte);
				f->us_copia = adesso_us() - tc;
			}
		}
		else if (f->pixel)
		{
			g_free(f->pixel);
			f->pixel = NULL;
			cattura->posto_capienza = 0;
		}
		f->stride = passo;
		f->larghezza = consegna.larghezza;
		f->altezza = consegna.altezza;
		f->seq = info.seq;
		f->pts = info.pts;
		f->seq_nota = info.seq_nota;
		f->danno_dichiarato = danno_dichiarato;
		f->danno_copre_tutto = copre_tutto;
		f->indice = info.indice;
		f->consegna = consegna;
		/* ⛔ The instant is taken HERE, after the copy: from this moment the
		 *    frame is ready and whoever takes it takes it aged by
		 *    whatever passes from now on. */
		f->us_arrivo = adesso_us();
		cattura->posto_pieno = TRUE;
		g_cond_broadcast(&cattura->novita);
	}
	g_mutex_unlock(&cattura->lucchetto);

	if (cattura->conto.arrivati % 300 == 0)
		registro_dettaglio(AREA,
		                   "over %" G_GUINT64_FORMAT " frames: %u distinct buffers, damage "
		                   "full %" G_GUINT64_FORMAT " partial %" G_GUINT64_FORMAT " absent %"
		                   G_GUINT64_FORMAT ", without header %" G_GUINT64_FORMAT
		                   ", cursor-only %" G_GUINT64_FORMAT
		                   ", ⭐ replaced in the slot %" G_GUINT64_FORMAT
		                   " (before 15 Aug they were LOST)",
		                   cattura->conto.arrivati, cattura->conto.buffer_distinti,
		                   cattura->conto.danno_pieno, cattura->conto.danno_parziale,
		                   cattura->conto.danno_assente, cattura->conto.senza_intestazione,
		                   cattura->conto.solo_cursore, cattura->sovrascritti);

restituisci:
	/* ⛔ AND HERE IS THE RELEASE CURE, in one line: a HELD buffer does not
	 *    go back to the producer now.  ⚠ Without this guard the DMA-BUF
	 *    would go back to Mutter at the very instant we hand it to the
	 *    reader, and it would be **exactly** the defect of the two alternating
	 *    screens (`LEZIONI.md` §8) — with the difference that this time we
	 *    would have written it ourselves. */
	if (!trattenuto)
		pw_stream_queue_buffer(cattura->flusso, pacco);
}

/*
 * ⭐⭐ WHEN THE PRODUCER REMAKES THE BUFFERS — and the number that comes out is needed
 *     downstream, not here.
 *
 * ⛔ THE FACT that makes them exist: a DMA-BUF `fd` is a descriptor
 *    number, and descriptor numbers **are recycled**.  After a
 *    renegotiation (`cattura_ridimensiona`) or a wake-up
 *    (`cattura_risveglia`) PipeWire frees the old buffers and allocates
 *    new ones: the kernel can reassign the **same numbers**.  ⇒ Whoever
 *    caches «fd 42 → VA-API surface» would end up with a surface pointing
 *    to memory of another generation, and the symptom would be **an old
 *    image**, without any error.
 *
 * ⇒ Here we only count, and the number travels in the `CatturaFermo`.  ⚠ We do not
 *   try to invalidate anything from this side: the importing module is the one
 *   that knows what it imported, and an invalidation done from here would be a
 *   decision taken where the facts are not.
 */
/*
 * ⛔⛔ THE GENERATION BELONGS TO THE PROCESS, NOT TO THE CAPTURE — 22 Sep 2026, the
 *      user's test on KDE: the screen FLICKERED between three images (the desktop,
 *      the log-out screen of the PREVIOUS session, and black).
 *
 * `[M]` The counter lived in the `Cattura` and restarted from 0 at every `g_new0`.
 *   After «Log Out» and a new login the session is reborn IN THE SAME child: the
 *   capture is new, the encoder is not.  Six `add_buffer` gave 6 to the
 *   old one and 6 to the new one ⇒ `importa_dmabuf` saw no change, did not
 *   drop the cache, and the descriptors recycled with the previous numbers
 *   found again the surfaces of the dead session.  Log of the `kde`
 *   box: at the two good rebirths «dropping the 4 imported surfaces», at the two
 *   bad ones no line.
 * ⇒ A single counter for the whole process: two captures can no longer
 *   have the same generation, whatever happens in between.
 */
static uint64_t generazione_nuova(void)
{
	static uint64_t ultima;

	return __atomic_add_fetch(&ultima, 1, __ATOMIC_RELAXED);
}

static void su_buffer_aggiunto(void *dati, struct pw_buffer *pacco)
{
	Cattura *cattura = dati;
	(void) pacco;
	cattura->generazione_buffer = generazione_nuova();
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
 *      `CatturaFermo` carries the **generation** it was born with, and
 *      `cattura_fermo_libera()` compares: if it is no longer that one, the buffer is not
 *      given back, because it no longer exists.  ⛔ Giving it back would be writing into
 *      a freed `pw_buffer` — a defect that shows up at
 *      resize, that is in the place where nobody looks.
 */
static void su_buffer_tolto(void *dati, struct pw_buffer *pacco)
{
	Cattura *cattura = dati;

	g_mutex_lock(&cattura->lucchetto);
	if (cattura->posto.ritenuta == pacco)
	{
		cattura->posto.ritenuta = NULL;
		cattura->posto.padrone = NULL;
		cattura->posto_pieno = FALSE;
		cattura->ritenuti_resi++;
	}
	cattura->generazione_buffer = generazione_nuova();
	g_mutex_unlock(&cattura->lucchetto);
}

/*
 * Gives back a held buffer.  ⛔ It runs on the CONSUMER's thread, not on the
 * real-time one: that is why it takes the PipeWire loop lock.
 *
 * ⚠ The order of the two locks is always `loop → lock`, never the reverse:
 *   `su_processo` and `su_buffer_tolto` run with the loop already held and take the
 *   lock inside.  Reversing it here would be a deadlock that
 *   shows up once in a while, under load.
 */
static void rendi_ritenuta(Cattura *cattura, struct pw_buffer *pacco, uint64_t generazione)
{
	if (!cattura || !pacco || !cattura->ciclo || !cattura->flusso)
		return;
	pw_thread_loop_lock(cattura->ciclo);
	/* ⛔ The comparison is the point: if the producer remade the buffers, this
	 *    `pw_buffer` no longer exists and giving it back would write into freed memory. */
	if (cattura->generazione_buffer == generazione)
		pw_stream_queue_buffer(cattura->flusso, pacco);
	cattura->ritenuti_resi++;
	pw_thread_loop_unlock(cattura->ciclo);
}

static const struct pw_stream_events eventi = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	/* ⭐ The two that count the buffer GENERATION: without them, a downstream import
	 *    cache would point to dead buffers after every
	 *    renegotiation.  See the box above `su_buffer_tolto`. */
	.add_buffer = su_buffer_aggiunto,
	.remove_buffer = su_buffer_tolto,
	.process = su_processo,
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
 * ⛔ And `CATTURA_COLORE_10BIT` proposes **only** the ten-bit formats.
 *    Putting BGRx in the same list would negotiate BGRx and we would
 *    learn nothing: the question «do ten bits exist from this source?» has
 *    an answer only if the refusal is a refusal.
 */
static uint32_t quanti_colori(CatturaColore colore, uint32_t elenco[8])
{
	switch (colore)
	{
	case CATTURA_COLORE_BGRA:
		elenco[0] = SPA_VIDEO_FORMAT_BGRA;
		elenco[1] = SPA_VIDEO_FORMAT_BGRx;
		return 2;
	case CATTURA_COLORE_10BIT:
		elenco[0] = SPA_VIDEO_FORMAT_xBGR_210LE;
		elenco[1] = SPA_VIDEO_FORMAT_xRGB_210LE;
		elenco[2] = SPA_VIDEO_FORMAT_ABGR_210LE;
		elenco[3] = SPA_VIDEO_FORMAT_ARGB_210LE;
		return 4;
	default:
		elenco[0] = SPA_VIDEO_FORMAT_BGRx;
		elenco[1] = SPA_VIDEO_FORMAT_BGRA;
		return 2;
	}
}

static uint64_t mod_scheda[16];
static int mod_scheda_quanti;

void cattura_modificatori_scheda(const uint64_t *modificatori, int quanti)
{
	mod_scheda_quanti = 0;
	for (int i = 0; modificatori && i < quanti && i < (int)G_N_ELEMENTS(mod_scheda); i++)
		mod_scheda[mod_scheda_quanti++] = modificatori[i];
}

static const struct spa_pod *proposta(struct spa_pod_builder *costruttore, uint32_t larghezza,
                                      uint32_t altezza, uint32_t fotogrammi_al_secondo,
                                      CatturaColore colore, gboolean con_modificatori)
{
	struct spa_rectangle misura = SPA_RECTANGLE(larghezza, altezza);
	struct spa_fraction cadenza = SPA_FRACTION(0, 1);
	struct spa_fraction cadenza_minima = SPA_FRACTION(1, 1);
	struct spa_fraction cadenza_massima = SPA_FRACTION(MAX(1u, fotogrammi_al_secondo), 1);
	struct spa_pod_frame cornice[3];
	uint32_t elenco[8];
	uint32_t quanti = quanti_colori(colore, elenco);
	uint32_t i;

	spa_pod_builder_push_object(costruttore, &cornice[0], SPA_TYPE_OBJECT_Format,
	                            SPA_PARAM_EnumFormat);
	spa_pod_builder_add(costruttore, SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
	                    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), 0);

	/* The colours as a choice: the first value is the preferred one, and it must be repeated —
	 * it is the form of `SPA_POD_CHOICE_ENUM_Id`, built by hand because the
	 * number of entries changes. */
	spa_pod_builder_prop(costruttore, SPA_FORMAT_VIDEO_format, 0);
	spa_pod_builder_push_choice(costruttore, &cornice[1], SPA_CHOICE_Enum, 0);
	spa_pod_builder_id(costruttore, elenco[0]);
	for (i = 0; i < quanti; i++)
		spa_pod_builder_id(costruttore, elenco[i]);
	spa_pod_builder_pop(costruttore, &cornice[1]);

	if (con_modificatori)
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
		spa_pod_builder_prop(costruttore, SPA_FORMAT_VIDEO_modifier,
		                     SPA_POD_PROP_FLAG_MANDATORY | SPA_POD_PROP_FLAG_DONT_FIXATE);
		spa_pod_builder_push_choice(costruttore, &cornice[2], SPA_CHOICE_Enum, 0);
		spa_pod_builder_long(costruttore, DRM_FORMAT_MOD_LINEAR);
		spa_pod_builder_long(costruttore, DRM_FORMAT_MOD_LINEAR);
		/* ⭐ 6 Oct 2026: only where the card refuses linear — see
		 *    `cattura_modificatori_scheda()` in cattura.h. */
		for (i = 0; i < (uint32_t)mod_scheda_quanti; i++)
			spa_pod_builder_long(costruttore, mod_scheda[i]);
		spa_pod_builder_long(costruttore, DRM_FORMAT_MOD_INVALID);
		spa_pod_builder_pop(costruttore, &cornice[2]);
	}

	/* ⛔ The size as a FIXED rectangle: an open range would let
	 *    Mutter choose, and it chooses 1280×720 and nobody notices until
	 *    they look at the pixels. */
	spa_pod_builder_add(costruttore, SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura),
	                    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cadenza),
	                    SPA_FORMAT_VIDEO_maxFramerate,
	                    SPA_POD_CHOICE_RANGE_Fraction(&cadenza_massima, &cadenza_minima,
	                                                  &cadenza_massima),
	                    0);
	return spa_pod_builder_pop(costruttore, &cornice[0]);
}

/* ------------------------------------------------------------------ *
 *  Life cycle
 * ------------------------------------------------------------------ */

/* ------------------------------------------------------------------ *
 *  ⭐⭐ THE SECOND SOURCE — wlroots, the pull direction.  `cattura.h`.
 * ------------------------------------------------------------------ */

Cattura *cattura_avvia_wlr(uint32_t larghezza, uint32_t altezza,
                           uint32_t fotogrammi_al_secondo, CatturaStrada strada,
                           CatturaColore colore, GError **sbaglio)
{
	Cattura *c = g_new0(Cattura, 1);
	uint32_t uscita_l = 0, uscita_a = 0;

	c->wlr = wlr_apri(sbaglio);
	if (!c->wlr) {
		g_free(c);
		return NULL;
	}
	c->strada = strada;
	c->colore = colore;
	c->chiesta_larghezza = larghezza;
	c->chiesta_altezza = altezza;
	c->chiesti_al_secondo = fotogrammi_al_secondo;

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
	wlr_misura(c->wlr, &uscita_l, &uscita_a);
	if (uscita_l != larghezza || uscita_a != altezza) {
		g_autoptr(GError) misura_sbaglio = NULL;
		WlrMisuraEsito e;

		registro_dice(AREA,
		              "wlroots: the requested canvas is %ux%u and the output is %ux%u — "
		              "asking the compositor for it (on this family the size does not "
		              "enter the birth: it is given afterwards, with the output protocol)",
		              larghezza, altezza, uscita_l, uscita_a);
		e = wlr_misura_chiedi(c->wlr, larghezza, altezza, 2.0, &misura_sbaglio);
		wlr_misura(c->wlr, &uscita_l, &uscita_a);
		/*
		 * ⛔⛔ AND THE JUDGEMENT IS GIVEN BY THE SIZE READ BACK, NOT BY THE OUTCOME.
		 *
		 * `DECISIONI.md` §5.0-sexies: asking for the size the output already has
		 * answers «succeeded» without sending anything, and an old serial
		 * answers «cancelled» without doing anything.  ⇒ We look at the output.
		 */
		if (uscita_l == larghezza && uscita_a == altezza)
			registro_dice(AREA,
			              "⭐ wlroots: the output is NOW %ux%u, the size requested by the "
			              "client — and I do not say so because the request succeeded, "
			              "I say so because I read it back",
			              uscita_l, uscita_a);
		else
			registro_dice(AREA,
			              "⛔ wlroots: I asked for %ux%u and the output stayed %ux%u "
			              "(outcome of the request: %s%s%s).  ⚠ The frames will be "
			              "%ux%u, and it is NOT an encoder fault: it is this "
			              "line",
			              larghezza, altezza, uscita_l, uscita_a,
			              e == WLR_MISURA_CHIESTA      ? "accepted but without effect"
			              : e == WLR_MISURA_GIA_COSI   ? "already so (and it was not)"
			              : e == WLR_MISURA_RIFIUTATA  ? "refused"
			              : e == WLR_MISURA_ANNULLATA  ? "cancelled (old serial)"
			                                           : "the compositor cannot change it",
			              misura_sbaglio ? " — " : "",
			              misura_sbaglio ? misura_sbaglio->message : "",
			              uscita_l, uscita_a);
	}

	/*
	 * ⭐⭐ THE CARD ROUTE — `wlroots.c`, the box at the top.
	 *
	 * ⛔ The «no» does NOT make the birth fail: memory works, and it is the
	 *    fallback.  But it is SAID, with the reason — and `c->strada` stays the
	 *    requested one, so `cattura_consegna()` shows the pair «CARD requested,
	 *    MEMORY arrived» instead of rewriting the question to make it add up.
	 */
	if (strada == CATTURA_STRADA_SCHEDA) {
		g_autoptr(GError) perche = NULL;

		if (!wlr_chiedi_la_scheda(c->wlr, &perche))
			registro_dice(AREA,
			              "⛔ wlroots: the CARD route was requested and it is NOT "
			              "possible — %s.  ⇒ DECLARED FALLBACK: the pixels go through "
			              "MEMORY, and the segment numbers include the copy",
			              perche ? perche->message : "with no reason");
	}

	registro_dice(AREA,
	              "⭐ wlroots: PULL source opened on output «%s» — one frame "
	              "per request, no PipeWire node.  The pace is decided by our "
	              "loop, not by the compositor",
	              wlr_uscita_nome(c->wlr));
	return c;
}

Cattura *cattura_avvia(uint32_t nodo, uint32_t larghezza, uint32_t altezza,
                       uint32_t fotogrammi_al_secondo, CatturaStrada strada, CatturaColore colore,
                       CatturaFotogramma su_fotogramma, CatturaFine su_fine, gpointer dati,
                       GError **sbaglio)
{
	static gsize inizializzato = 0;
	Cattura *cattura = g_new0(Cattura, 1);
	uint8_t spazio[2048];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[1];
	gint64 scadenza;

	if (g_once_init_enter(&inizializzato))
	{
		pw_init(NULL, NULL);
		g_once_init_leave(&inizializzato, 1);
	}

	cattura->su_fotogramma = su_fotogramma;
	cattura->su_fine = su_fine;
	cattura->dati = dati;
	cattura->strada = strada;
	cattura->colore = colore;
	cattura->chiesta_larghezza = larghezza;
	cattura->chiesta_altezza = altezza;
	cattura->chiesti_al_secondo = fotogrammi_al_secondo;
	g_mutex_init(&cattura->lucchetto);
	g_cond_init(&cattura->novita);

	/* ⭐ The cursor module is ALWAYS born, even if nobody listens: that way the
	 *    counters answer «does the metadata arrive?» without depending on who
	 *    consumes it.  ⚠ If it is not born we do not fail: the pixels are worth more than the
	 *    pointer (`CODER.md` §4.2), but the fallback is SAID. */
	cattura->cursore = cursore_apri(cursore_rimbalzo, cattura);
	if (!cattura->cursore)
		registro_dice(AREA, "⛔ FALLBACK: the cursor module did not open — the pointer "
		                    "shape will not be sent (the frames will, all of them)");

	cattura->ciclo = pw_thread_loop_new("remotix-cattura", NULL);
	if (!cattura->ciclo)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "PipeWire loop not created");
		goto guasto;
	}
	cattura->contesto = pw_context_new(pw_thread_loop_get_loop(cattura->ciclo), NULL, 0);
	if (!cattura->contesto)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "PipeWire context not created");
		goto guasto;
	}

	pw_thread_loop_lock(cattura->ciclo);
	if (pw_thread_loop_start(cattura->ciclo) < 0)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "PipeWire thread not started");
		goto guasto;
	}
	cattura->nucleo = pw_context_connect(cattura->contesto, NULL, 0);
	if (!cattura->nucleo)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "connection to PipeWire failed");
		goto guasto;
	}
	cattura->flusso = pw_stream_new(cattura->nucleo, "remotix-cattura",
	                                pw_properties_new(PW_KEY_MEDIA_TYPE, "Video",
	                                                  PW_KEY_MEDIA_CATEGORY, "Capture",
	                                                  PW_KEY_MEDIA_ROLE, "Screen", NULL));
	if (!cattura->flusso)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "PipeWire stream not created");
		goto guasto;
	}
	pw_stream_add_listener(cattura->flusso, &cattura->gancio, &eventi, cattura);

	/* ⛔ ONE proposal only, and declared.  Offering two — one with modifiers
	 *    and one without — means «I take the card, but if it is missing memory
	 *    is fine»: it is a fallback, and a silent fallback produces two
	 *    behaviours under the same label (`CODER.md` §4.2).  Whoever wants the
	 *    fallback asks twice, and knows which of the two they got. */
	parametri[0] = proposta(&costruttore, larghezza, altezza, fotogrammi_al_secondo, colore,
	                        strada == CATTURA_STRADA_SCHEDA);

	if (pw_stream_connect(cattura->flusso, PW_DIRECTION_INPUT, nodo,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parametri, 1) < 0)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "attaching to node %u failed", nodo);
		goto guasto;
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
	scadenza = g_get_monotonic_time() + (gint64)(ATTESA_AGGANCIO_MS * 1000);
	while (cattura->stato != PW_STREAM_STATE_PAUSED &&
	       cattura->stato != PW_STREAM_STATE_STREAMING &&
	       cattura->stato != PW_STREAM_STATE_ERROR && g_get_monotonic_time() < scadenza)
		pw_thread_loop_timed_wait(cattura->ciclo, 1);
	pw_thread_loop_unlock(cattura->ciclo);
	{
		/* ⭐ And we DECLARE how much it cost, if it cost: it was the last
		 *    region of the mount without a stopwatch, and that is why
		 *    it took five diagnoses. */
		gint64 speso_ms = (g_get_monotonic_time() -
		                   (scadenza - (gint64)(ATTESA_AGGANCIO_MS * 1000))) / 1000;

		if (speso_ms >= 250)
			registro_dice(AREA,
			              "⏱ attaching the PipeWire stream cost %lld ms "
			              "(state %d, ceiling %d ms) — ⚠ when the compositor is "
			              "ready it costs about ten milliseconds: this means "
			              "it was not ready",
			              (long long)speso_ms, (int)cattura->stato,
			              ATTESA_AGGANCIO_MS);
	}

	if (cattura->stato == PW_STREAM_STATE_ERROR)
	{
		/* ⭐ PHASE 17 — the code says WHAT went wrong, not only that
		 *    it went wrong: `G_IO_ERROR_NOT_SUPPORTED` when no format was
		 *    ever agreed (`cattura_formato_rifiutato()`), so the
		 *    caller tells «the requested route does not exist here» from any
		 *    fault without reading PipeWire's text. */
		g_set_error(sbaglio, G_IO_ERROR,
		            cattura->formato_noto ? G_IO_ERROR_FAILED : G_IO_ERROR_NOT_SUPPORTED,
		            "the compositor refused what was requested (%s, route %s): %s",
		            colore == CATTURA_COLORE_10BIT   ? "10 bit"
		            : colore == CATTURA_COLORE_BGRA ? "BGRA"
		                                            : "BGRx",
		            strada == CATTURA_STRADA_SCHEDA ? "card" : "memory",
		            cattura->guasto ? cattura->guasto : "without explanation");
		goto guasto;
	}
	if (cattura->stato != PW_STREAM_STATE_PAUSED && cattura->stato != PW_STREAM_STATE_STREAMING)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "the capture did not attach within %d ms: ⚠ it does NOT mean "
		            "«broken», it means «the compositor is not ready yet» — and "
		            "the caller retries shortly",
		            ATTESA_AGGANCIO_MS);
		goto guasto;
	}

	registro_dice(AREA, "capture started on node %u: requested %ux%u, route %s", nodo, larghezza,
	              altezza, strada == CATTURA_STRADA_SCHEDA ? "card (DMA-BUF)" : "memory");
	return cattura;

guasto:
	cattura_ferma(cattura);
	return NULL;
}

/* ------------------------------------------------------------------ *
 *  ⭐⭐ THE HOT SIZE CHANGE — see `cattura.h`
 * ------------------------------------------------------------------ */

CatturaRitela cattura_ridimensiona(Cattura *cattura, uint32_t larghezza, uint32_t altezza)
{
	/* ⛔ PHASE 13 — on wlroots the size is NOT changed on the stream: it is changed
	 *    on the output, with another protocol (`zwlr_output_manager_v1`, `[M]`
	 *    v4 on labwc).  ⇒ Here we say no **by saying so**, instead of returning
	 *    an outcome that would make the caller believe it obtained something. */
	if (cattura && cattura->wlr) {
		g_autoptr(GError) sbaglio = NULL;
		uint32_t l = 0, a = 0;
		WlrMisuraEsito e;

		/* ⭐ On this family the size is changed on the OUTPUT, not on the stream —
		 *    and it is the thing that could not be done on KDE.  ⛔ And the real outcome is
		 *    given by reading it back, not by the answer to the request. */
		e = wlr_misura_chiedi(cattura->wlr, larghezza, altezza, 2.0, &sbaglio);
		cattura->chiesta_larghezza = larghezza;
		cattura->chiesta_altezza = altezza;
		wlr_misura(cattura->wlr, &l, &a);
		if (l == larghezza && a == altezza) {
			registro_dice(AREA,
			              "⭐ wlroots: the output is now %ux%u — read back, not "
			              "believed", l, a);
			return CATTURA_RITELA_CHIESTA;
		}
		if (e == WLR_MISURA_GIA_COSI)
			return CATTURA_RITELA_GIA_COSI;
		registro_dice(AREA,
		              "⛔ wlroots: requested %ux%u, the output is %ux%u%s%s",
		              larghezza, altezza, l, a, sbaglio ? " — " : "",
		              sbaglio ? sbaglio->message : "");
		return CATTURA_RITELA_GUASTO;
	}
	uint8_t spazio[2048];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[5];
	uint32_t quanti;
	int esito;

	if (!cattura || !cattura->flusso || !cattura->ciclo)
		return CATTURA_RITELA_GUASTO;
	/* ⛔ Zero is not «out of bounds»: it is a request with no content, and
	 *    passing it to the producer would mean asking it for a monitor of zero
	 *    area.  ⚠ The rest of the rule — 200..8192 and evenness — lives in
	 *    `rcp_misura_ammessa()`, in a single place. */
	if (!larghezza || !altezza)
	{
		registro_dice(AREA, "⛔ resize to %ux%u: an empty size is not requested",
		              larghezza, altezza);
		return CATTURA_RITELA_GUASTO;
	}

	pw_thread_loop_lock(cattura->ciclo);

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
	if (cattura->formato_noto ? (larghezza == cattura->formato.size.width
	                             && altezza == cattura->formato.size.height)
	                          : (larghezza == cattura->chiesta_larghezza
	                             && altezza == cattura->chiesta_altezza))
	{
		pw_thread_loop_unlock(cattura->ciclo);
		registro_dettaglio(AREA,
		                   "resize to %ux%u: it is the size the stream ALREADY "
		                   "HAS, NOT renegotiating (STUDI.md §kde §8.2-bis)",
		                   larghezza, altezza);
		return CATTURA_RITELA_GIA_COSI;
	}

	/* ⛔ A dead stream is not renegotiated, and «dead» is ASKED of the state instead
	 *    of deduced from silence: on a stream in error `update_params`
	 *    would succeed and a frame would never arrive — that is the silent
	 *    fallback that `CODER.md` §4.2 forbids. */
	if (cattura->stato != PW_STREAM_STATE_PAUSED && cattura->stato != PW_STREAM_STATE_STREAMING)
	{
		enum pw_stream_state stato = cattura->stato;
		/* ⛔ THE FAULT IS COPIED BEFORE RELEASING THE LOCK — defect found
		 *    while refuting: `su_stato()` runs on the loop thread and does
		 *    `g_free(guasto); guasto = g_strdup(...)`, so between the `g_free` and
		 *    the assignment the field is a dangling pointer.  ⚠ And this branch
		 *    is taken **precisely while** the stream is dying, that is
		 *    at the instant `su_stato` is running: reading it after the unlock is
		 *    reading freed memory, and for a log line. */
		char *guasto = cattura->guasto ? g_strdup(cattura->guasto) : NULL;
		pw_thread_loop_unlock(cattura->ciclo);
		registro_dice(AREA,
		              "⛔ resize to %ux%u NOT requested: the stream is «%s»%s%s",
		              larghezza, altezza, pw_stream_state_as_string(stato),
		              guasto ? " — " : "", guasto ? guasto : "");
		g_free(guasto);
		return CATTURA_RITELA_GUASTO;
	}

	/* ⛔ The REQUESTED size is updated BEFORE the request, and under the loop
	 *    lock: `su_parametri` runs on the PipeWire thread and compares it
	 *    against the negotiated format (the «requested versus granted» guard).
	 *    Updating it afterwards would mean comparing the new answer with the
	 *    old question, that is declaring a divergence that does not exist. */
	cattura->chiesta_larghezza = larghezza;
	cattura->chiesta_altezza = altezza;
	/* ⚠ And the divergence is reset: it is a fact of the negotiation that is about to be
	 *   redone, not a scar of the previous one. */
	cattura->misura_divergente = FALSE;

	/* ⛔ The same `proposta()` as at startup, with the same colour and route: a
	 *    proposal written by hand here would be a second rule on the format, and the
	 *    day one of the two changed the stream would reopen with a
	 *    colour different from the negotiated one — without any error. */
	parametri[0] = proposta(&costruttore, larghezza, altezza, cattura->chiesti_al_secondo,
	                        cattura->colore, cattura->strada == CATTURA_STRADA_SCHEDA);
	/* ⛔⭐ AND WITH IT THE FOUR CONSUMPTION PARAMETERS — defect found while refuting:
	 *     `pw_stream_update_params()` does NOT add, **it replaces the whole
	 *     list**.  Passing only `EnumFormat` would erase
	 *     `ParamBuffers` and the three `ParamMeta`, among them the CURSOR one.  ⚠ In the
	 *     healthy case the format callback puts them back; ⛔ but in the case that
	 *     `cattura.h` documents — the compositor answering «succeeded» and
	 *     sending no event — that callback does not run, and the pointer
	 *     channel would stay without a source without anybody saying so. */
	quanti = 1 + parametri_di_consumo(cattura, &costruttore, parametri + 1);
	esito = pw_stream_update_params(cattura->flusso, parametri, quanti);
	pw_thread_loop_unlock(cattura->ciclo);

	if (esito < 0)
	{
		registro_dice(AREA, "⛔ `pw_stream_update_params()` at %ux%u answered %d (%s)",
		              larghezza, altezza, esito, spa_strerror(esito));
		return CATTURA_RITELA_GUASTO;
	}
	registro_dice(AREA,
	              "⭐ canvas REQUESTED from the producer: %ux%u (`pw_stream_update_params`).  ⚠ It is the "
	              "request, not the outcome: the truth is told by the frame (DECISIONI.md "
	              "§5.0-sexies)",
	              larghezza, altezza);
	return CATTURA_RITELA_CHIESTA;
}

gboolean cattura_risveglia(Cattura *cattura)
{
	/* ⭐ On the pull direction waking up means asking for the next WHOLE frame.
	 *    ⛔ Until 21 Sep 2026 nothing was done here, because every round was
	 *    already a whole copy; since frames are requested WITH DAMAGE
	 *    (`wlroots.c`, `forza_intero`), on an idle desktop none would
	 *    arrive — exactly when a keyframe is needed. */
	if (cattura && cattura->wlr) {
		wlr_forza_intero(cattura->wlr);
		return TRUE;
	}
	uint8_t spazio[2048];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[5];
	uint32_t l, a, quanti;
	int esito;

	if (!cattura || !cattura->flusso || !cattura->ciclo)
		return FALSE;

	pw_thread_loop_lock(cattura->ciclo);
	if (cattura->stato != PW_STREAM_STATE_PAUSED && cattura->stato != PW_STREAM_STATE_STREAMING)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		return FALSE;
	}
	/* ⛔ The size is the NEGOTIATED one, not the requested one: nothing is being
	 *    changed here — the same question is being repeated to restart
	 *    the stream.  ⚠ Redoing the proposal with the REQUESTED size, at a time when
	 *    the compositor has granted another one (§4.5), would be a
	 *    resize disguised as a wake-up. */
	l = cattura->formato_noto ? cattura->formato.size.width : cattura->chiesta_larghezza;
	a = cattura->formato_noto ? cattura->formato.size.height : cattura->chiesta_altezza;
	if (!l || !a)
	{
		pw_thread_loop_unlock(cattura->ciclo);
		return FALSE;
	}
	parametri[0] = proposta(&costruttore, l, a, cattura->chiesti_al_secondo, cattura->colore,
	                        cattura->strada == CATTURA_STRADA_SCHEDA);
	quanti = 1 + parametri_di_consumo(cattura, &costruttore, parametri + 1);
	esito = pw_stream_update_params(cattura->flusso, parametri, quanti);
	pw_thread_loop_unlock(cattura->ciclo);

	if (esito < 0)
	{
		registro_dice(AREA, "⛔ stream wake-up at %ux%u: %s", l, a, spa_strerror(esito));
		return FALSE;
	}
	registro_dice(AREA,
	              "⭐ stream RESTARTED at the same size (%ux%u) to get a "
	              "frame delivered: on Wayland one cannot ask «repaint», and this is the "
	              "only lever we have (`cattura.h`)",
	              l, a);
	return TRUE;
}

void cattura_misura_chiesta(Cattura *cattura, uint32_t *larghezza, uint32_t *altezza)
{
	if (larghezza)
		*larghezza = cattura ? cattura->chiesta_larghezza : 0;
	if (altezza)
		*altezza = cattura ? cattura->chiesta_altezza : 0;
}

gboolean cattura_misura_negoziata(Cattura *cattura, uint32_t *larghezza, uint32_t *altezza)
{
	/* On wlroots the «negotiated» size is the output's, and it is known at once. */
	if (cattura && cattura->wlr) {
		uint32_t l = 0, a = 0;

		wlr_misura(cattura->wlr, &l, &a);
		if (!l || !a)
			return FALSE;
		if (larghezza)
			*larghezza = l;
		if (altezza)
			*altezza = a;
		return TRUE;
	}
	if (!cattura || !cattura->formato_noto)
		return FALSE; /* ⛔ «it has not been negotiated», not «it is 0x0» */
	if (larghezza)
		*larghezza = cattura->formato.size.width;
	if (altezza)
		*altezza = cattura->formato.size.height;
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
static void misura_i_pixel(CatturaFermo *fermo)
{
	CatturaConsegna *c = &fermo->consegna;
	int r = 0, g = 1, b = 2;
	guint64 riga, colonna;
	const uint8_t *base = fermo->pixel;
	uint8_t primo[4] = { 0, 0, 0, 0 };
	gboolean uniforme = TRUE;

	c->range_misurato = CATTURA_RANGE_NON_MISURATO;
	if (!fermo->pixel || fermo->byte == 0)
		return;
	if (c->bit_per_canale != 8 || !posizioni_rgb(c->formato_grezzo, &r, &g, &b))
	{
		/* ⛔ We do not measure on the wrong bytes: a number taken from a layout
		 *    we do not know would be worse than no number. */
		return;
	}

	c->minimo[0] = c->minimo[1] = c->minimo[2] = 255;
	c->massimo[0] = c->massimo[1] = c->massimo[2] = 0;
	memcpy(primo, base, 4);

	for (riga = 0; riga < fermo->altezza; riga++)
	{
		const uint8_t *p = base + riga * (guint64) fermo->stride;

		if ((riga + 1) * (guint64) fermo->stride > fermo->byte)
			break;
		for (colonna = 0; colonna < fermo->larghezza; colonna++, p += 4)
		{
			uint8_t v[3] = { p[r], p[g], p[b] };
			int i;

			for (i = 0; i < 3; i++)
			{
				if (v[i] < c->minimo[i])
					c->minimo[i] = v[i];
				if (v[i] > c->massimo[i])
					c->massimo[i] = v[i];
			}
			if (uniforme && (p[0] != primo[0] || p[1] != primo[1] || p[2] != primo[2]))
				uniforme = FALSE;
		}
	}

	c->uniforme = uniforme;
	c->nero = (c->massimo[0] == 0 && c->massimo[1] == 0 && c->massimo[2] == 0);
	if (c->minimo[0] == 0 && c->minimo[1] == 0 && c->minimo[2] == 0 && c->massimo[0] == 255 &&
	    c->massimo[1] == 255 && c->massimo[2] == 255)
		c->range_misurato = CATTURA_RANGE_COMPATIBILE_PIENO;
	else
		c->range_misurato = CATTURA_RANGE_NON_CONCLUSIVO;
}

/*
 * ⭐⭐ THE JUDGEMENT ON THE SLAB IS MADE BY SAMPLING, NOT ON ALL THE BYTES.
 *
 * ⛔ THE FACT THAT MADE IT NECESSARY — `[M]` phase 16, Radeon RX 6800,
 *    XFCE/labwc box (wlroots-dmabuf route, LINEAR gbm slabs): the full
 *    pass of `misura_i_pixel` over the mapping of the 4K slab took
 *    **63 673 ms** (GPU wait 0.59 ms), and for all that time the loop
 *    delivered nothing and the birth of the session failed.  On a
 *    DISCRETE card the slab lives in VRAM and the CPU reads it through the
 *    UNCACHED PCIe BAR: every read is a bus transaction, and the full
 *    pass makes several per pixel over eight million pixels.  ⚠ On the integrated
 *    Intel (system memory) the same pass is instantaneous: that is why
 *    it had not been seen until the Radeon.
 *
 * ⭐ THE «BLACK / NOT BLACK» JUDGEMENT DOES NOT NEED 30 MB: a grid of
 *    `CAMPIONE_LATO` x `CAMPIONE_LATO` points, at the CENTRE of each cell (on 4K
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
 * ⛔ THE TIME CEILING (`CAMPIONE_TETTO_US`), checked at every row of the
 *    grid: if it expires, what was seen counts only if it proves «not black»
 *    (one lit sample and two different ones).  A «black» or a «uniform» on a
 *    half grid is NOT declared: `pixel_misurati` stays FALSE, «I did not
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
#define CAMPIONE_LATO 64u
#define CAMPIONE_TETTO_US 250000u

static guint misura_i_pixel_a_campione(CatturaFermo *fermo, gboolean *tetto)
{
	CatturaConsegna *c = &fermo->consegna;
	int r = 0, g = 1, b = 2;
	const uint8_t *base = fermo->pixel;
	uint8_t primo[4] = { 0, 0, 0, 0 };
	gboolean uniforme = TRUE;
	guint guardati = 0, i, j;
	uint64_t inizio = adesso_us();

	*tetto = FALSE;
	c->range_misurato = CATTURA_RANGE_NON_MISURATO;
	if (!fermo->pixel || fermo->byte == 0 || fermo->larghezza == 0 || fermo->altezza == 0)
		return 0;
	/* ⛔ Like the full pass: on the bytes of a layout we do not
	 *    know we do not measure. */
	if (c->bit_per_canale != 8 || !posizioni_rgb(c->formato_grezzo, &r, &g, &b))
		return 0;

	c->minimo[0] = c->minimo[1] = c->minimo[2] = 255;
	c->massimo[0] = c->massimo[1] = c->massimo[2] = 0;

	for (i = 0; i < CAMPIONE_LATO; i++)
	{
		guint64 riga = ((2u * (guint64) i + 1u) * fermo->altezza) / (2u * CAMPIONE_LATO);
		const uint8_t *p_riga = base + riga * (guint64) fermo->stride;

		if ((riga + 1) * (guint64) fermo->stride > fermo->byte)
			break;
		if (i > 0 && adesso_us() - inizio > CAMPIONE_TETTO_US)
		{
			*tetto = TRUE;
			break;
		}
		for (j = 0; j < CAMPIONE_LATO; j++)
		{
			guint64 colonna =
			    ((2u * (guint64) j + 1u) * fermo->larghezza) / (2u * CAMPIONE_LATO);
			uint8_t px[4];
			uint8_t v[3];
			int k;

			/* ⭐ ONE 4-byte read, then we work on the local copy. */
			memcpy(px, p_riga + colonna * 4u, 4);
			if (guardati == 0)
				memcpy(primo, px, 4);
			v[0] = px[r];
			v[1] = px[g];
			v[2] = px[b];
			for (k = 0; k < 3; k++)
			{
				if (v[k] < c->minimo[k])
					c->minimo[k] = v[k];
				if (v[k] > c->massimo[k])
					c->massimo[k] = v[k];
			}
			if (uniforme && (px[0] != primo[0] || px[1] != primo[1] || px[2] != primo[2]))
				uniforme = FALSE;
			guardati++;
		}
	}
	if (guardati == 0)
		return 0;

	c->uniforme = uniforme;
	c->nero = (c->massimo[0] == 0 && c->massimo[1] == 0 && c->massimo[2] == 0);
	if (c->minimo[0] == 0 && c->minimo[1] == 0 && c->minimo[2] == 0 && c->massimo[0] == 255 &&
	    c->massimo[1] == 255 && c->massimo[2] == 255)
		c->range_misurato = CATTURA_RANGE_COMPATIBILE_PIENO;
	else
		c->range_misurato = CATTURA_RANGE_NON_CONCLUSIVO;
	return guardati;
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
 * ⛔ AND ON THE FOLLOWING FRAMES `pixel_misurati` STAYS FALSE, which means
 *    «I did not look» and **not** «it is not black» — the same rule as the field, and
 *    the same reason (`LEZIONI.md` §1.9).  ⚠ What is lost compared with
 *    memory is continuous surveillance: a desktop that turned black
 *    mid-session, on this route, no longer has anyone to say so.  It is declared
 *    here instead of discovered later.
 *
 * ⛔⛔ AND IT IS NOT READ IN FULL: it is read by sampling (`misura_i_pixel_a_campione`,
 *     the box above), because on a discrete card the full pass
 *     took 63.7 s.  It returns how many pixels it looked at; `*tetto` says whether the
 *     time expired before the end of the grid.
 */
static guint guarda_i_pixel_del_dmabuf(Cattura *cattura, CatturaFermo *fermo, gboolean *tetto)
{
	void *mappa;
	size_t quanti;
	guint guardati;

	*tetto = FALSE;
	if (fermo->fd < 0 || fermo->byte == 0)
		return 0;
	quanti = (size_t) fermo->offset + (size_t) fermo->byte;
	mappa = mmap(NULL, quanti, PROT_READ, MAP_SHARED, fermo->fd, 0);
	if (mappa == MAP_FAILED)
	{
		/* ⛔ It is NOT «the frame is not black»: it is «I could not look», and
		 *    it is said once instead of leaving a silence that looks like a
		 *    green.  ⚠ It happens for example with a non-linear modifier: there
		 *    the bytes in memory are not the rows of the image, and reading them
		 *    would give a wrong answer instead of no answer. */
		if (!cattura->detta_misura_impossibile)
		{
			cattura->detta_misura_impossibile = TRUE;
			registro_dice(AREA,
			              "⚠ the DMA-BUF could not be mapped (fd %d, %zu bytes, "
			              "modifier 0x%" G_GINT64_MODIFIER "x): ⛔ we do NOT conclude that "
			              "the frame is not black — we conclude that I DID NOT "
			              "LOOK, and `pixel_misurati` stays FALSE",
			              fermo->fd, quanti, (guint64) fermo->modificatore);
		}
		return 0;
	}
	/* ⚠ `misura_i_pixel` reads from `fermo->pixel`: it is lent for the duration
	 *   of the measurement and taken away right after.  ⛔ Leaving it there would
	 *   mean handing downstream a pointer to a mapping we are about to
	 *   tear down — and downstream nobody expects it, because `sulla_scheda` says
	 *   the opposite. */
	fermo->pixel = (uint8_t *) mappa + fermo->offset;
	guardati = misura_i_pixel_a_campione(fermo, tetto);
	/* ⛔ Zero looked at = «I did not look» (unknown format, slab
	 *    shorter than the first row).  And with the ceiling expired a «black» or a
	 *    «uniform» on half a grid is not declared: only «not black» counts,
	 *    which one lit sample proves by itself. */
	fermo->consegna.pixel_misurati =
	    guardati > 0 && !(*tetto && (fermo->consegna.nero || fermo->consegna.uniforme));
	if (!fermo->consegna.pixel_misurati) {
		fermo->consegna.nero = FALSE;
		fermo->consegna.uniforme = FALSE;
		fermo->consegna.range_misurato = CATTURA_RANGE_NON_MISURATO;
	}
	fermo->pixel = NULL;
	munmap(mappa, quanti);
	return guardati;
}

/*
 * ⭐⭐ THE TRUE SHAPE ON LABWC — the probe (`wlroots.h`) has seen under the
 *      pointer the colour of a shape: here it becomes the TRUE image of the
 *      real theme (`forma_immagine`) and leaves along the SAME road as GNOME and
 *      KDE — `cursore_rimbalzo`, and from there whoever registered with
 *      `cattura_cursore` (the child: `cursore_al_padre`).
 *
 * ⛔ It runs on the thread of whoever calls `cattura_prendi` (the child's loop), not
 *    on PipeWire's: there is no PipeWire here.  ⇒ The receiver can do
 *    what it always does, send on the socket, and nothing more.
 * ⚠ Hidden does not exist here: the probe either recognises a colour or keeps the
 *   previous shape.  ⇒ An application that hides the pointer does not
 *   hide it from whoever watches — as on KDE (`cursore_mai_nascondere`).
 */
static void wlr_forma_consegna(Cattura *cattura)
{
	int indice = wlr_sonda_forma(cattura->wlr);
	CursoreForma f;

	if (indice < 0)
		return;
	memset(&f, 0, sizeof f);
	if (!forma_immagine(indice, &f))
		return; /* ⛔ real theme missing: already said by `forma.c`, the client
		         *    keeps its arrow */
	if (cattura->wlr_forma_data && f.larghezza == cattura->wlr_forma.larghezza &&
	    f.altezza == cattura->wlr_forma.altezza &&
	    f.attivo_x == cattura->wlr_forma.attivo_x &&
	    f.attivo_y == cattura->wlr_forma.attivo_y &&
	    memcmp(f.immagine, cattura->wlr_forma.immagine,
	           (gsize)f.larghezza * f.altezza * 4u) == 0) {
		cattura->wlr_forme_uguali++;
		return;
	}
	f.serie = cattura->wlr_forma.serie + 1;
	/* ⚠ One line per shape CHANGE, as on KDE (`cursore.c`): it is the pace
	 *   of the hand, and the proof that the probe is working is read here. */
	registro_dice(AREA, "encoded shape %d «%s» ⇒ %ux%u, hotspot %d,%d (wlroots probe)",
	              indice, forma_nome(indice), (unsigned)f.larghezza, (unsigned)f.altezza,
	              (int)f.attivo_x, (int)f.attivo_y);
	cattura->wlr_forma = f;
	cattura->wlr_forma_data = TRUE;
	cattura->wlr_forme_mandate++;
	cursore_rimbalzo(cattura, &f);
}

void cattura_sonda_puntatore(Cattura *cattura, uint32_t x, uint32_t y)
{
	uint32_t l = 0, a = 0;

	if (!cattura || !cattura->wlr)
		return;
	/* ⚠ The pointer's canvas is the frame's (`input_ritela` resets
	 *   it at every size change, `figlio.c`), and on this family the
	 *   frame is the whole output: ⇒ the output size is the yardstick.
	 *   For the frame straddling a size change the point may be
	 *   scaled wrong ONCE: the next probe puts it right. */
	wlr_misura(cattura->wlr, &l, &a);
	wlr_sonda_puntatore(cattura->wlr, x, y, l, a);
}

CatturaPresa cattura_prendi(Cattura *cattura, double attesa_s, CatturaFermo *fuori,
                            GError **sbaglio)
{
	gint64 scadenza;
	gboolean preso = FALSE;

	g_return_val_if_fail(cattura != NULL && fuori != NULL, CATTURA_PRESA_GUASTO);
	memset(fuori, 0, sizeof *fuori);

	/*
	 * ⭐⭐ PHASE 13 — THE PULL DIRECTION: here we do not WAIT for a frame, we
	 *      ASK for it.  ⚠ Two routes: on MEMORY the copy exists, and the
	 *      microseconds are in `us_copia` as on every other route — a
	 *      segment without its cost is a segment that will lie; on the CARD
	 *      (since 21 Sep 2026) the pixels stay in a slab and the frame
	 *      comes out as `PIXEL_ALTROVE`, further below.
	 */
	if (cattura->wlr) {
		WlrFotogramma w;
		gint64 prima = g_get_monotonic_time(), dopo;
		WlrEsito e = wlr_fotogramma(cattura->wlr, attesa_s, &w, sbaglio);

		/* ⭐ The pointer probe: its events have just been pumped by
		 *    `wlr_fotogramma`.  ⛔ BEFORE the `switch`, which has three exits:
		 *    on an idle desktop the frame almost always times out, and the shape
		 *    must arrive all the same. */
		wlr_forma_consegna(cattura);

		switch (e) {
		case WLR_FOTOGRAMMA_SCADUTO:
			/* ⛔ «nothing arrived» on a pull source is a legitimate
			 *    ZERO, not a fault: the desktop may be idle, and the
			 *    compositor answers all the same.  ⚠ But the error stays written. */
			return CATTURA_PRESA_ZERO;
		case WLR_FOTOGRAMMA_FALLITO:
		case WLR_FOTOGRAMMA_ROTTO:
			return CATTURA_PRESA_GUASTO;
		case WLR_FOTOGRAMMA_PRESO:
			break;
		}

		fuori->us_arrivo = (uint64_t)prima;
		fuori->larghezza = w.larghezza;
		fuori->altezza = w.altezza;
		fuori->stride = w.stride;
		fuori->byte = w.byte;
		fuori->pts = (int64_t)(w.secondi * 1000000000ull + w.nanosecondi);
		fuori->seq_nota = FALSE;
		fuori->formato_drm = w.formato;
		if (w.sulla_scheda) {
			/*
			 * ⭐⭐ THE CARD: no copy of ours, and the slab stays HELD.
			 *
			 * ⛔ `ritenuta` + `padrone` are the same two fields as the
			 *    PipeWire retention: `cattura_fermo_libera()` sees them, and its
			 *    `wlr` preamble gives the slab back to `wlroots.c` — AFTER
			 *    `codificatore_comprimi_scheda()`, when the GPU has finished
			 *    reading.  ⇒ The compositor does not write into it before then
			 *    (`LEZIONI.md` §8).
			 * ⚠ `us_copia` here is the WHOLE round — request, blit on the
			 *   compositor's GPU, wait for the fence — as on memory it is the
			 *   whole round plus the `memcpy`: the same quantity on both routes.
			 */
			fuori->sulla_scheda = TRUE;
			fuori->pixel = NULL;
			fuori->fd = w.fd;
			fuori->offset = w.offset;
			fuori->modificatore = w.modificatore;
			fuori->generazione = w.generazione;
			fuori->ritenuta = w.lastra;
			fuori->padrone = cattura;
		} else {
			/* ⛔ Card requested and memory arrived: it is SAID, once. */
			if (cattura->strada == CATTURA_STRADA_SCHEDA && !cattura->wlr_detto_ripiego) {
				cattura->wlr_detto_ripiego = TRUE;
				registro_dice(AREA,
				              "⛔ wlroots: CARD requested, and this frame "
				              "arrived in MEMORY — DECLARED FALLBACK (the reason is "
				              "in the `wlroots:` lines above).  The line is not "
				              "repeated; the closing counters say how many per "
				              "route");
			}
			fuori->sulla_scheda = FALSE;
			fuori->pixel = g_malloc(w.byte);
			memcpy(fuori->pixel, w.pixel, w.byte);
		}
		dopo = g_get_monotonic_time();
		fuori->us_copia = (uint64_t)(dopo - prima);

		cattura->wlr_ultimo = w;
		cattura->wlr_ultimo_noto = TRUE;
		cattura->formato_noto = TRUE;

		/*
		 * ⛔⛔ THE WITNESS IS WRITTEN HERE, AT THE FIRST REAL FRAME — and not
		 *     at opening, where it was until 21 September 2026.
		 *
		 * «`negotiated format: WxH`» is the line C1 reads to say that the
		 * monitor was born.  The first draft wrote it in `cattura_avvia_wlr`,
		 * BEFORE any `capture_output`, with format, bits and modifier
		 * hard-coded in the text.  ⇒ The adversarial reviewer called it by
		 * name: *an XFCE session in which screencopy always fails came out
		 * GREEN* — the line proved only that labwc was alive.
		 * ⭐ Here instead there is a frame in hand: size, stride and format
		 *   are those of the `buffer` event, and C1's green again means
		 *   what it says.
		 */
		if (!cattura->wlr_detto_il_testimone) {
			char nome[5];

			cattura->wlr_detto_il_testimone = TRUE;
			memcpy(nome, &w.formato, 4);
			nome[4] = 0;
			registro_dice(AREA,
			              "negotiated format: %ux%u %s (8 bits per channel), modifier "
			              "0x%" G_GINT64_MODIFIER "x — ⭐ wlroots: said at the FIRST "
			              "frame taken, with the size and format the "
			              "compositor really gave, %s",
			              w.larghezza, w.altezza, nome,
			              (guint64)(w.sulla_scheda ? w.modificatore : 0),
			              w.sulla_scheda ? "on the CARD (wlroots-dmabuf)"
			                             : "in MEMORY (wlroots-shm)");
		}

		/* ⚠ `y_invertita`: if the compositor says the rows must be read from the
		 *   bottom and nobody honours it, the image comes out upside down — a fault that
		 *   looks like an encoder fault.  ⛔ Here it is DECLARED and not
		 *   flipped: flipping 8 MB at every frame would cost more than the capture, and
		 *   the right place is the encoder, which can do it without copying.
		 *   `[M]` 21 Sep 2026 on headless labwc the flag never turned on. */
		/* ⚠ ONCE only: inside the branch of every take it would be sixty
		 *   lines per second, the form that already produced the 30.8 GB of
		 *   log (the reviewer, 21 Sep 2026). */
		if (w.y_invertita && !cattura->wlr_detto_y && (cattura->wlr_detto_y = TRUE))
			registro_dice(AREA,
			              "⛔ wlroots: the compositor declares Y INVERTED and this "
			              "draft does not flip it — the image will come out upside down, and the "
			              "cause is this line, not the encoder");

		cattura_consegna(cattura, &fuori->consegna);
		if (!w.sulla_scheda)
			return CATTURA_PRESA_FATTA;

		/* ⭐ The FIRST card frame is looked at, by mapping the slab —
		 *    the same rule as the card on PipeWire: only once, and the
		 *    others carry `pixel_misurati` FALSE («I did not look»).  ⚠ With the
		 *    DMA-BUF SYNC around it: the bytes the CPU sees must be
		 *    those written by the GPU. */
		/* ⛔⛔ AND THE NUMBERING, found re-reading the port: `misura_i_pixel`
		 *     reads the channel order from `formato_grezzo` with SPA
		 *     numbers, and here `formato_grezzo` is a DRM fourcc.  Passed as is, the
		 *     measurement exits AT ONCE without looking at anything — and
		 *     `guarda_i_pixel_del_dmabuf` writes `pixel_misurati =
		 *     TRUE` all the same: a «not black» on a frame never looked at, that is the
		 *     false green of `LEZIONI.md` §1.9.  ⇒ For the duration of the measurement
		 *     we lend the SPA number that states the same order; if there
		 *     is none, we do NOT look, and we say so. */
		if (!cattura->wlr_guardato_il_primo) {
			uint64_t tm = adesso_us();
			guint guardati = 0;
			gboolean tetto = FALSE;
			uint32_t grezzo = fuori->consegna.formato_grezzo;
			uint32_t spa = (w.formato == DRM_FORMAT_XRGB8888) ? SPA_VIDEO_FORMAT_BGRx
			               : (w.formato == DRM_FORMAT_ARGB8888) ? SPA_VIDEO_FORMAT_BGRA
			               : (w.formato == DRM_FORMAT_XBGR8888) ? SPA_VIDEO_FORMAT_RGBx
			               : (w.formato == DRM_FORMAT_ABGR8888) ? SPA_VIDEO_FORMAT_RGBA
			                                                   : SPA_VIDEO_FORMAT_UNKNOWN;

			cattura->wlr_guardato_il_primo = TRUE;
			if (spa != SPA_VIDEO_FORMAT_UNKNOWN) {
				fuori->consegna.formato_grezzo = spa;
				wlr_lettura_cpu(fuori->fd, TRUE);
				guardati = guarda_i_pixel_del_dmabuf(cattura, fuori, &tetto);
				wlr_lettura_cpu(fuori->fd, FALSE);
				fuori->consegna.formato_grezzo = grezzo;
			} else {
				registro_dice(AREA,
				              "⚠ wlroots: the first CARD frame was NOT "
				              "looked at — fourcc 0x%08x has no channel "
				              "order the measurement knows.  `pixel_misurati` "
				              "stays FALSE: «I did not look», not «it is not black»",
				              w.formato);
			}
			fuori->us_misura = adesso_us() - tm;
			if (fuori->consegna.pixel_misurati)
				registro_dice(AREA,
				              "⭐ wlroots: the FIRST CARD frame looked at "
				              "by mapping the slab: %s — %u sampled pixels over "
				              "%ux%u%s (%.2f ms, GPU wait %.2f ms, %s)",
				              fuori->consegna.nero       ? "⛔ BLACK"
				              : fuori->consegna.uniforme ? "⚠ UNIFORM"
				                                         : "not black",
				              guardati, fuori->larghezza, fuori->altezza,
				              tetto ? ", ⚠ time CEILING expired with the grid incomplete" : "",
				              fuori->us_misura / 1000.0, w.us_attesa_gpu / 1000.0,
				              w.attesa_esplicita
				                  ? "fence extracted from the DMA-BUF"
				                  : "⚠ no fence: implicit synchronisation");
			else if (tetto)
				registro_dice(AREA,
				              "⚠ wlroots: the FIRST CARD frame was NOT "
				              "judged — CEILING of %u ms expired after %u "
				              "sampled pixels all dark or equal (%.2f ms): «I did not look», "
				              "not «it is not black», and `pixel_misurati` stays FALSE",
				              CAMPIONE_TETTO_US / 1000u, guardati,
				              fuori->us_misura / 1000.0);
		}
		return CATTURA_PRESA_PIXEL_ALTROVE;
	}

	if (cattura->stato != PW_STREAM_STATE_STREAMING && cattura->stato != PW_STREAM_STATE_PAUSED)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "the stream is not active (state %s%s%s): there is no frame to "
		            "wait for, and this is NOT a zero",
		            pw_stream_state_as_string(cattura->stato), cattura->guasto ? ", fault: " : "",
		            cattura->guasto ? cattura->guasto : "");
		return CATTURA_PRESA_GUASTO;
	}

	g_mutex_lock(&cattura->lucchetto);
	cattura->qualcuno_aspetta = TRUE;
	/* ⛔⛔ AND HERE THERE WAS `cattura->posto_pieno = FALSE;` — the second half of the
	 *     same defect of 15 August 2026: whoever came to take a
	 *     frame **threw away the one already ready** and started
	 *     waiting for another.  ⇒ With the scene still that other one never
	 *     arrived, and the last frame of the change stayed in the slot,
	 *     undelivered, until the next movement.
	 * ⭐ Now: if it is there, it is taken. */
	scadenza = g_get_monotonic_time() + (gint64) (attesa_s * G_USEC_PER_SEC);
	/* ⭐ PHASE 17 — and a stream in ERROR will deliver nothing more: we exit
	 *    at once instead of waiting the whole timeout.  `[M]` 29 Sep 2026, VM without
	 *    3D: the negotiation refusal arrived in milliseconds and the take
	 *    said so five seconds later, at every login.  ⚠ `su_stato` writes the
	 *    state BEFORE taking the lock and waking up: here, with the lock
	 *    in hand, the state read is the one of the wake-up. */
	while (!cattura->posto_pieno && cattura->stato != PW_STREAM_STATE_ERROR)
	{
		if (!g_cond_wait_until(&cattura->novita, &cattura->lucchetto, scadenza))
			break;
	}
	if (cattura->posto_pieno)
	{
		/* ⛔ The buffer PASSES to the consumer — who will free it with
		 *    `cattura_fermo_libera()` — so the slot stays without one, and the
		 *    capacity goes back to zero: on the next round a new one is allocated.
		 * ⚠ It is the honest price of reuse: we reuse as long as nobody consumes
		 *   (the burst), and reallocate when someone really consumes. */
		*fuori = cattura->posto;
		/* ⭐⭐ AND HERE WE READ THE AGE OF THE FRAME — the segment entry that
		 *     nobody looked at.  ⛔ It is not work: it is the time the
		 *     frame sat still waiting for the loop to come back and
		 *     ask for it, and it ages the frame without anybody
		 *     noticing.  `[M]` phase 4: the empty waits are **0.00/s**, that is
		 *     **there was always something ready already** — which said the other way round
		 *     means that the frame was waiting for US. */
		fuori->us_nel_posto = adesso_us() - fuori->us_arrivo;
		memset(&cattura->posto, 0, sizeof cattura->posto);
		cattura->posto_capienza = 0;
		cattura->posto_pieno = FALSE;
		preso = TRUE;
	}
	cattura->qualcuno_aspetta = FALSE;
	g_mutex_unlock(&cattura->lucchetto);

	/* ⛔ «It WAS active» is not «it still is»: death in the middle of a take. */
	if (cattura->stato != PW_STREAM_STATE_STREAMING && cattura->stato != PW_STREAM_STATE_PAUSED)
	{
		cattura_fermo_libera(fuori);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "the stream was alive and fell during the take (state %s%s%s)",
		            pw_stream_state_as_string(cattura->stato), cattura->guasto ? ", fault: " : "",
		            cattura->guasto ? cattura->guasto : "");
		return CATTURA_PRESA_GUASTO;
	}

	if (!preso)
	{
		/* ⭐ LEGITIMATE ZERO: the stream was active for the whole wait and nothing
		 *    arrived.  On Mutter it is the idle desktop — the rate is 0/1,
		 *    «send me a frame when something changes» — and it is a result,
		 *    not a fault. */
		return CATTURA_PRESA_ZERO;
	}

	/* ⛔ THE ROUTE IS VERIFIED, NOT TAKEN AS REQUESTED (`LEZIONI.md` §1.8). */
	if (cattura->strada == CATTURA_STRADA_SCHEDA &&
	    fuori->consegna.buffer_dichiarato != CATTURA_BUFFER_DMABUF)
	{
		CatturaBuffer arrivato = fuori->consegna.buffer_dichiarato;

		cattura_fermo_libera(fuori);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "the card (DMA-BUF) was requested and the producer delivered %s: no "
		            "silent fallback",
		            cattura_buffer_nome(arrivato));
		return CATTURA_PRESA_GUASTO;
	}
	if (cattura->strada == CATTURA_STRADA_MEMORIA &&
	    fuori->consegna.buffer_dichiarato == CATTURA_BUFFER_DMABUF)
	{
		cattura_fermo_libera(fuori);
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "memory was requested and DMA-BUFs arrived: the pixels are not here");
		return CATTURA_PRESA_GUASTO;
	}

	if (!fuori->pixel)
	{
		/* Card route: the type is declared, the pixels live elsewhere.
		 * ⛔ It is not a fault and not a zero, and it is the third exit.
		 *
		 * ⭐ But BEFORE returning we look **only once** inside the buffer:
		 *    see `guarda_i_pixel_del_dmabuf`. */
		if (fuori->sulla_scheda && cattura->misura_ultima_us == 0)
		{
			uint64_t tm = adesso_us();
			gboolean tetto = FALSE;
			guint guardati = guarda_i_pixel_del_dmabuf(cattura, fuori, &tetto);
			cattura->misura_ultima_us = tm;
			fuori->us_misura = adesso_us() - tm;
			if (fuori->consegna.pixel_misurati)
			{
				cattura->misura_fatte++;
				registro_dice(AREA,
				              "⭐ the FIRST card frame was looked at "
				              "by mapping the DMA-BUF: %s — %u sampled pixels over "
				              "%ux%u%s (%.2f ms).  ⛔ It is the ONLY one "
				              "looked at on this route — see the box: the following ones "
				              "carry `pixel_misurati` FALSE, which means «I did not "
				              "look» and NOT «it is not black»",
				              fuori->consegna.nero ? "⛔ BLACK"
				                                   : (fuori->consegna.uniforme
				                                          ? "⚠ UNIFORM"
				                                          : "not black"),
				              guardati, fuori->larghezza, fuori->altezza,
				              tetto ? ", ⚠ time CEILING expired with the grid incomplete" : "",
				              fuori->us_misura / 1000.0);
			}
			else if (tetto)
				registro_dice(AREA,
				              "⚠ the FIRST card frame was NOT "
				              "judged — CEILING of %u ms expired after %u sampled "
				              "pixels all dark or equal (%.2f ms): «I did not "
				              "look», not «it is not black»",
				              CAMPIONE_TETTO_US / 1000u, guardati,
				              fuori->us_misura / 1000.0);
		}
		return CATTURA_PRESA_PIXEL_ALTROVE;
	}

	/* ⭐⭐ THE PASS OVER THE PIXELS, AT A RATE — see `MISURA_PIXEL_OGNI_MS`.
	 *
	 * ⛔ The FIRST is always looked at (`misura_ultima_us == 0`): it is the one whose
	 *    line «⛔ BLACK / not black» `figlio.c` writes, and it is also the only
	 *    frame the bench `banchi/02-cattura-prodotto.c` can count on
	 *    for sure. */
	{
		uint64_t tm = adesso_us();

		if (cattura->misura_ultima_us == 0 ||
		    tm - cattura->misura_ultima_us >= (uint64_t) MISURA_PIXEL_OGNI_MS * 1000u)
		{
			misura_i_pixel(fuori);
			fuori->consegna.pixel_misurati = TRUE;
			cattura->misura_ultima_us = tm;
			cattura->misura_fatte++;
			fuori->us_misura = adesso_us() - tm;

			if (fuori->consegna.nero)
				registro_dice(AREA,
				              "⛔ the delivered frame is BLACK (maximum 0 on all "
				              "three channels): it is what a session without a "
				              "virtual monitor delivers — STUDI.md §gnome §3.1, fault M9");
			else if (fuori->consegna.uniforme)
				registro_dice(AREA,
				              "⚠ the delivered frame is UNIFORM: all pixels "
				              "equal, and this is not black — it is a buffer never painted");
		}
		else
		{
			/* ⛔ AND HERE THE PREVIOUS ANSWER IS NOT COPIED: `nero` and `uniforme`
			 *    stay `FALSE` and `pixel_misurati` stays `FALSE`, which together
			 *    say **«I did not look»**.  ⚠ Writing the last
			 *    known value into them would be worse than silence: the reader would believe
			 *    that those three facts concern THIS frame, while there
			 *    they concern another one (`LEZIONI.md` §1.11, two measurements under the
			 *    same label). */
			cattura->misura_saltate++;
			if (cattura->misura_saltate == 1)
				registro_dice(AREA,
				              "⭐ from here on the pass over the pixels is done at most every %d ms and no "
				              "longer on every frame: `[M]` it cost 5.34 ms on a segment "
				              "of 21.6 (25 %%) to fill ONE log line.  ⚠ On the "
				              "skipped frames `pixel_misurati` is FALSE, and «not black» "
				              "is NOT deduced from `nero == FALSE`",
				              MISURA_PIXEL_OGNI_MS);
		}
	}
	return CATTURA_PRESA_FATTA;
}

void cattura_fermo_libera(CatturaFermo *fermo)
{
	if (!fermo)
		return;
	/* ⭐ PHASE 13 — the wlroots card slab goes back to `wlroots.c`.
	 *    ⚠ Before the PipeWire branch, and zeroing `ritenuta`: that branch must
	 *    not see a pointer that is not a `pw_buffer`.  ⛔ It triggers ONLY
	 *    with `->wlr`: for GNOME and KDE `padrone->wlr` is NULL and the release
	 *    below stays what it was, word for word. */
	if (fermo->ritenuta && fermo->padrone && ((Cattura *) fermo->padrone)->wlr)
	{
		wlr_rendi(((Cattura *) fermo->padrone)->wlr, fermo->ritenuta);
		fermo->ritenuta = NULL;
	}
	/* ⭐⭐ THE RELEASE — and it lives here because this is the only place where we know that
	 *     the reader has finished.  ⛔ Before this line the `pw_buffer` is
	 *     ours and Mutter does not repaint inside it; after, it is its own.
	 * ⚠ And it is given back BEFORE zeroing the held frame, because zeroing erases
	 *   precisely the two fields that say whom to give it back to. */
	if (fermo->ritenuta && fermo->padrone)
		rendi_ritenuta((Cattura *) fermo->padrone, (struct pw_buffer *) fermo->ritenuta,
		               fermo->generazione);
	g_free(fermo->pixel);
	memset(fermo, 0, sizeof *fermo);
}

/* ------------------------------------------------------------------ *
 *  What is declared downstream
 * ------------------------------------------------------------------ */

gboolean cattura_consegna(Cattura *cattura, CatturaConsegna *fuori)
{
	g_return_val_if_fail(cattura != NULL && fuori != NULL, FALSE);

	memset(fuori, 0, sizeof *fuori);

	if (cattura->wlr) {
		const WlrFotogramma *w = &cattura->wlr_ultimo;

		if (!cattura->wlr_ultimo_noto)
			return FALSE; /* no frame yet: «I do not know» */
		fuori->noto = TRUE;
		fuori->strada_chiesta = cattura->strada;
		/* ⛔ The buffer is a `wl_shm` we created ourselves: the type is not
		 *    «declared», it is KNOWN.  ⚠ And MEMFD is not written by analogy with
		 *    PipeWire: it is the same thing (a shared memfd), and calling it by the
		 *    name the reader already knows is worth more than a new name. */
		/* ⭐ And since 21 Sep 2026 there are two routes: the type is told by the
		 *    FRAME (`sulla_scheda`), the question by `strada`. */
		fuori->buffer_chiesto = cattura->strada == CATTURA_STRADA_SCHEDA
		                            ? CATTURA_BUFFER_DMABUF
		                            : CATTURA_BUFFER_MEMFD;
		fuori->buffer_dichiarato =
		    w->sulla_scheda ? CATTURA_BUFFER_DMABUF : CATTURA_BUFFER_MEMFD;
		fuori->buffer_dichiarato_grezzo = 0;
		fuori->buffer_distinti = 1;
		fuori->formato_grezzo = w->formato;
		fuori->formato = cattura_colore_nome(w->formato);
		fuori->bit_per_canale = 8;
		fuori->fonte_bit = CATTURA_FONTE_FORMATO;
		fuori->larghezza = w->larghezza;
		fuori->altezza = w->altezza;
		fuori->stride = w->stride;
		fuori->stride_letto = TRUE;
		fuori->byte = w->byte;
		fuori->modificatore = w->sulla_scheda ? w->modificatore : 0;
		/* ⛔ The colour: the compositor declares neither range nor matrix, and
		 *    here we do NOT invent.  `pixel_misurati` stays FALSE: whoever reads
		 *    `nero`/`uniforme` must find them not looked at, not false. */
		fuori->fonte_range = CATTURA_FONTE_NON_DICHIARATA;
		fuori->fonte_matrice = CATTURA_FONTE_NON_DICHIARATA;
		fuori->range_misurato = CATTURA_RANGE_NON_MISURATO;
		fuori->pixel_misurati = FALSE;
		return TRUE;
	}

	if (!cattura->formato_noto)
		return FALSE; /* ⛔ «I do not know yet», and not «it is all zero» */

	fuori->noto = TRUE;
	fuori->strada_chiesta = cattura->strada;
	fuori->buffer_chiesto =
	    cattura->strada == CATTURA_STRADA_SCHEDA ? CATTURA_BUFFER_DMABUF : CATTURA_BUFFER_MEMFD;
	fuori->buffer_dichiarato =
	    cattura->conto.quanti_tipi > 0 ? cattura->conto.tipi_visti[0] : CATTURA_BUFFER_IGNOTO;
	fuori->buffer_dichiarato_grezzo = cattura->primo_tipo_grezzo;
	fuori->buffer_distinti = cattura->conto.buffer_distinti;
	fuori->formato_grezzo = cattura->formato.format;
	fuori->formato = cattura_colore_nome(cattura->formato.format);
	fuori->bit_per_canale = bit_per_canale(cattura->formato.format);
	fuori->fonte_bit =
	    fuori->bit_per_canale > 0 ? CATTURA_FONTE_FORMATO : CATTURA_FONTE_NON_DICHIARATA;
	fuori->larghezza = cattura->formato.size.width;
	fuori->altezza = cattura->formato.size.height;
	fuori->modificatore = cattura->formato.modifier;
	fuori->range_grezzo = cattura->formato.color_range;
	fuori->matrice_grezza = cattura->formato.color_matrix;
	fuori->trasferimento_grezzo = cattura->formato.transfer_function;
	fuori->primari_grezzi = cattura->formato.color_primaries;
	fuori->fonte_range =
	    cattura->formato.color_range ? CATTURA_FONTE_PRODUTTORE : CATTURA_FONTE_NON_DICHIARATA;
	fuori->fonte_matrice =
	    cattura->formato.color_matrix ? CATTURA_FONTE_PRODUTTORE : CATTURA_FONTE_NON_DICHIARATA;
	/* ⛔ The stride is NOT put here: until a frame has arrived it is not
	 *    a fact, and it is the field that must not be recomputed downstream.  The
	 *    frame carries it. */
	fuori->stride = 0;
	fuori->stride_letto = FALSE;
	fuori->byte = 0;
	return TRUE;
}

void cattura_conteggi(Cattura *cattura, CatturaConteggi *fuori)
{
	if (cattura && cattura->wlr) {
		WlrConteggi w;

		wlr_conteggi(cattura->wlr, &w);
		memset(fuori, 0, sizeof *fuori);
		fuori->arrivati = w.presi;
		/* ⚠ The other fields stay zero, and NOT because they are worth zero: on
		 *   this source they do not exist (the damage book, the cursor
		 *   channel, the PipeWire buffer types).  Whoever reads them finds zero and
		 *   must know it means «this quantity does not exist here». */
		return;
	}
	g_return_if_fail(cattura != NULL && fuori != NULL);
	*fuori = cattura->conto;
}

const char *cattura_uscita_nome(Cattura *cattura)
{
	if (cattura && cattura->wlr)
		return wlr_uscita_nome(cattura->wlr);
	return NULL;
}

gboolean cattura_attiva(Cattura *cattura)
{
	if (cattura && cattura->wlr)
		return TRUE;
	return cattura && cattura->stato == PW_STREAM_STATE_STREAMING;
}

const char *cattura_guasto(Cattura *cattura)
{
	return cattura ? cattura->guasto : NULL;
}

gboolean cattura_formato_rifiutato(Cattura *cattura)
{
	/* ⛔ The two conditions together, and neither is enough on its own:
	 *    `ERROR` without a format is the failed negotiation; `ERROR` AFTER a
	 *    format is a stream that died after being born, and there the requested
	 *    route existed.  ⚠ On wlroots there is no PipeWire negotiation: its
	 *    fallback lives in `cattura_avvia_wlr()`. */
	/* ⭐ 6 Oct 2026, `[M]` NVIDIA + GNOME 50: Mutter AGREES a format (with the
	 *    INVALID modifier), fails to allocate it, withdraws it, and the stream
	 *    goes into error without ever having delivered a buffer.  ⇒ «format
	 *    agreed but no frame arrived» is a refusal too: the requested route
	 *    here never gave anything. */
	return cattura && !cattura->wlr && cattura->stato == PW_STREAM_STATE_ERROR &&
	       (!cattura->formato_noto || cattura->conto.arrivati == 0);
}

void cattura_cursore(Cattura *cattura, CursoreArrivata quando_cambia, void *chi)
{
	/* ⛔ PHASE 13 — on this family a channel for the pointer SHAPE does not
	 *    exist: there is only `overlay_cursor`, and the pointer sits INSIDE
	 *    the image.  Until 24 September 2026 the registration was accepted
	 *    and never called back.
	 * ⭐ Since 24 September the shape is found by the PROBE (`wlroots.h`), and it arrives
	 *    through `cursore_rimbalzo` as on GNOME and KDE (`wlr_forma_consegna`).
	 *    ⇒ The registration counts here too; the line says where it will come from. */
	if (cattura && cattura->wlr)
		registro_dice(AREA,
		              "⭐ wlroots: the pointer shape is found by the PROBE (a 3x3 "
		              "under the point, after every gesture) and the dictionary of the encoded "
		              "theme: whoever registered will be called back at every change");
	if (!cattura)
		return;
	g_mutex_lock(&cattura->lucchetto);
	cattura->cursore_fn = quando_cambia;
	cattura->cursore_chi = chi;
	g_mutex_unlock(&cattura->lucchetto);
}

void cattura_cursore_mai_nascondere(Cattura *cattura, const char *perche)
{
	if (cattura && cattura->wlr)
		return; /* no cursor channel: there is nothing to not hide */
	if (!cattura)
		return;
	g_mutex_lock(&cattura->lucchetto);
	cursore_mai_nascondere(cattura->cursore, perche);
	g_mutex_unlock(&cattura->lucchetto);
}

void cattura_ferma(Cattura *cattura)
{
	if (!cattura)
		return;

	if (cattura->wlr) {
		WlrConteggi w;
		WlrSondaConteggi so;

		wlr_sonda_conteggi(cattura->wlr, &so);
		registro_dice(AREA,
		              "wlroots: pointer probe — gestures %" G_GUINT64_FORMAT
		              ", probes sent %" G_GUINT64_FORMAT " (trailing %" G_GUINT64_FORMAT
		              "), returned %" G_GUINT64_FORMAT ", failed %" G_GUINT64_FORMAT
		              "; new shapes %" G_GUINT64_FORMAT " (from neighbours %" G_GUINT64_FORMAT
		              "), without our colour %" G_GUINT64_FORMAT "; delivered %"
		              G_GUINT64_FORMAT ", same drawing %" G_GUINT64_FORMAT,
		              so.chieste, so.lanciate, so.di_coda, so.tornate, so.fallite, so.cambi,
		              so.dai_vicini, so.ignote, cattura->wlr_forme_mandate,
		              cattura->wlr_forme_uguali);
		wlr_conteggi(cattura->wlr, &w);
		registro_dice(AREA,
		              "wlroots: capture closed — requested %" G_GUINT64_FORMAT
		              ", taken %" G_GUINT64_FORMAT " (on the CARD %" G_GUINT64_FORMAT
		              ", in MEMORY %" G_GUINT64_FORMAT "), failed %" G_GUINT64_FORMAT
		              ", timed out %" G_GUINT64_FORMAT,
		              w.chiesti, w.presi, w.sulla_scheda, w.in_memoria, w.falliti,
		              w.scaduti);
		wlr_chiudi(cattura->wlr);
		g_free(cattura);
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
	 * ⛔⛔ AND THE CALLER MUST HAVE ALREADY FREED ITS `CatturaFermo`: a held frame
	 *      freed AFTER this function gives a buffer back to a `Cattura` that no longer
	 *      exists.  `figlio.c` does it in the right order in all three
	 *      places where it tears down the stage, and this line is the reason why. */
	if (cattura->ciclo && cattura->flusso)
	{
		pw_thread_loop_lock(cattura->ciclo);
		if (cattura->posto.ritenuta)
		{
			pw_stream_queue_buffer(cattura->flusso,
			                       (struct pw_buffer *) cattura->posto.ritenuta);
			cattura->posto.ritenuta = NULL;
			cattura->posto.padrone = NULL;
			cattura->posto_pieno = FALSE;
			cattura->ritenuti_resi++;
		}
		pw_thread_loop_unlock(cattura->ciclo);
	}
	if (cattura->ritenuti)
		registro_dice(AREA,
		              "the retention closes: %" G_GUINT64_FORMAT " buffers held, %"
		              G_GUINT64_FORMAT " given back.  ⛔ The difference (%lld) is how many were "
		              "still in hand, and if it is not zero someone did not free their "
		              "`CatturaFermo`",
		              cattura->ritenuti, cattura->ritenuti_resi,
		              (long long) cattura->ritenuti - (long long) cattura->ritenuti_resi);

	if (cattura->ciclo)
		pw_thread_loop_stop(cattura->ciclo);
	if (cattura->flusso)
		pw_stream_destroy(cattura->flusso);
	if (cattura->nucleo)
		pw_core_disconnect(cattura->nucleo);
	if (cattura->contesto)
		pw_context_destroy(cattura->contesto);
	if (cattura->ciclo)
		pw_thread_loop_destroy(cattura->ciclo);

	/* ⛔ AFTER the thread, not before: `guarda_cursore` runs over there. */
	cursore_chiudi(cattura->cursore);

	g_free(cattura->posto.pixel);
	g_mutex_clear(&cattura->lucchetto);
	g_cond_clear(&cattura->novita);
	g_free(cattura->guasto);
	g_free(cattura);
}
