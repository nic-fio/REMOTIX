/*
 * 02-cattura-fotogramma — ONE frame taken from the GNOME session, delivered
 * in memory with the buffer type DECLARED.  Bench of sub-phase F2.2.
 *
 * ⛔ WHY IT EXISTS, GIVEN THAT `misura-cattura` IS ALREADY THERE
 *
 * The phase 0 tool (`fondamenta/banchi/banco-compositori/misura-cattura.c`) is
 * certified, reproduces Mutter's 36 ± 2 frames, and stays the historical positive
 * control of the whole project.  ⛔ But it **never** looks inside the
 * buffer: it counts the frames, reads the data type, the damage, the fence and the
 * intervals — and it does not touch the pixels.  Line by line: `su_processo` takes
 * `datas[0]`, reads its `type`, `fd`, `chunk->stride`, and puts the buffer back in
 * the queue with `pw_stream_queue_buffer`.  No read of `piano->data`.
 *
 * ⇒ **A completely BLACK frame would pass phase 0 with full
 *   marks**: 36 per second, partial damage, four recycled buffers, zero sequence
 *   skips.  All green, and on the screen nothing.
 *
 * ⛔ And black is not a textbook case: `STUDI.md` §gnome §3.1 says that in headless mode
 *   `needs_outputs=false`, so **without `--virtual-monitor` the session starts
 *   alive, complete and black**, and it is the broken test M9 of the measurement plan of
 *   `STUDI.md` §gnome §13.  The phase 2 plan (`PIANO.md`) writes it in
 *   full: *«a black and perfectly alive session is the thing that gets mistaken
 *   for a capture defect, and you search for half a day on the wrong
 *   side»*.  The BLACK AND VALID frame is the worst fault of this
 *   sub-phase, and a tool that can see it is needed.
 *
 * This program therefore does the thing the other does not, and **only that**:
 * it takes a frame, writes it to disk byte by byte, and next to it puts a
 * manifest with everything needed to judge it without having to deduce it.  Whoever
 * judges is another program (`02-cattura-giudica.py`), and the separation is
 * intended: it is the only way of injecting a fault into the PIXELS — a black frame
 * instead of the real one — without touching either the producer or the judge.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT THIS PROGRAM DOES **NOT** PROVE — written here because it is
 *    error form E1 of `REVIEWER.md` §2, and this is exactly the point where
 *    it has already been paid for twice (`LEZIONI.md` §1.11):
 *
 *   | What is read in the manifest    | What it does NOT prove                |
 *   |---------------------------------|---------------------------------------|
 *   | `tipo = MemFd`                  | ⛔ **nothing about the compositor**: it|
 *   |                                 | depends on what the CLIENT asked for.  |
 *   |                                 | Here the client asks for memory        |
 *   |                                 | on purpose — readable pixels are       |
 *   |                                 | needed — so MemFd is the ANSWER TO A   |
 *   |                                 | QUESTION OF OURS, not a discovery      |
 *   | `tipo = DMA-BUF`                | does not prove Mutter renders on GPU:  |
 *   |                                 | an open render node is necessary,      |
 *   |                                 | not sufficient (KWin opens one even    |
 *   |                                 | when it then renders in QPainter)      |
 *
 *   That is why the manifest carries THREE separate fields and not one: `chiesto`,
 *   `dichiarato_dal_produttore` and `chi_lo_dice`.  ⭐ The buffer type **is
 *   asked for and declared**, not deduced — and it is the mandate of F2.2.
 *
 * ---------------------------------------------------------------------------
 * ⛔ ZERO, FAILED AND FAULT ARE THREE DIFFERENT THINGS (`REVIEWER.md` §1 point 4)
 *
 *   exit 0  a frame is there and it was written
 *   exit 3  ⭐ ZERO frames, but the stream WAS active for the whole
 *           measurement: it is a **legitimate** zero — a still desktop delivers
 *           nothing (`LEZIONI.md` §4 trap 8), and it is a result, not a
 *           fault.  No `.raw` is written, and the manifest says so
 *   exit 2  FAULT: the stream never became active, or it dropped
 *           during the measurement, or one road was asked for and another
 *           arrived.  There is no number to read
 *   exit 1  the environment: the virtual monitor does not mount, PipeWire does not
 *           answer, the file cannot be written
 *
 * The three exit-2 guards are the same that phase 0 had to add
 * to `misura-cattura` AFTER having believed it (items 1 and 8 of «What did NOT
 * work» in `FASI.md` §00-ambiente): here they are born together with the program.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE ORDER: FIRST THE MONITOR, THEN THE SCENE — and the program says it, not whoever
 *    launches it.
 *
 * Phase 0's `banco.sh` switches the scene on 2.5 seconds AFTER the meter, with
 * the reason written next to it: *«without a screen there is nowhere to open»*.  Here
 * a timed wait is not enough, because this program must then know WHICH
 * frames arrived before the scene and which after.  So the program
 * writes a file (`--pronto`) at the instant the stream becomes active, and
 * whoever launches it switches the scene on only then.  ⭐ It is not a wait: it is an event
 * (`LEZIONI.md` §4 trap 9 — «you do not wait for a silence, you wait for an
 * event»).
 *
 * ⚠ And the same form bites phase 2 from another side, already measured: in a
 *   GNOME session without input devices, a client opened BEFORE the
 *   `libei` virtual pointer exists receives nothing (`PIANO.md`, box
 *   «A question phase 1 found and that bites HERE», `[M]` 10 Aug).
 *   Here no device is created — it is not F2.2's area — but the order is
 *   the same, and whoever mounts input will have to slip it between `--pronto` and the
 *   scene.
 *
 * ---------------------------------------------------------------------------
 * ⛔ TWO FRAMES, NOT ONE, AND THE REASON IS `CODER.md` §3.5 (form E9)
 *
 * *A sample taken at start-up says nothing about the steady state.*  For a still
 * image the rule does not disappear: it changes form.
 *
 *   `primo`   the first frame after the stream became active, before
 *             the scene exists.  It is the **full redraw**: on it the
 *             damage is `pieno`, and it is the frame the user would see
 *             connecting to a just-mounted desktop
 *   `regime`  a frame taken after `--dopo-scena` seconds of live scene,
 *             skipping `--scarta`.  On Mutter in steady state the damage is
 *             **partial** in 98 % of cases (`FASI.md` §00-ambiente: full 15,
 *             partial 929)
 *
 * ⭐ And the comparison between the two answers a question the documents today
 *    contradict each other on:
 *
 *   - `fondamenta/remotix-c/src/cattura.h` says: *«in zero-copy Mutter recycles its own
 *     buffers and repaints in them ONLY the part that changed; outside those
 *     regions are the pixels of the frame that had used that buffer
 *     before»*;
 *   - `STUDI.md` §gnome §8.1, which reread Mutter's code, says the opposite:
 *     *«⛔ false: blit of the whole framebuffer, clip stack emptied
 *     deliberately»*.
 *
 *   One of the two is old.  A `regime` frame with **partial** damage that
 *   nevertheless contains the WHOLE scene settles the matter, and settles it with a
 *   measurement instead of a rereading.  ⚠ And the decision matters: if
 *   `cattura.h` were right, phase 2 would deliver half a desktop and half an old
 *   screen, without an error anywhere.
 *
 * ---------------------------------------------------------------------------
 * ⚠ THIS PROGRAM DOES NOT MEASURE RATE, AND MUST NOT.
 *
 * It copies two 8 MB frames inside the `process` callback, which runs on
 * PipeWire's real-time thread.  `misura-cattura` writes, rightly, that
 * whoever slows that loop skews its own measurement — so here frames per
 * second **are not printed at all**: rate belongs to phase 0 (36 ± 2) and
 * phase 3.  A rate number that came out of here would be a right number for
 * a question nobody asked, and it is item 8 of `FASI.md` §00-ambiente.
 *
 * ---------------------------------------------------------------------------
 * usage:
 *   02-cattura-fotogramma --uscita PREFISSO --pronto FILE
 *        [--larghezza W] [--altezza H] [--fps N] [--bgra] [--dmabuf]
 *        [--dopo-scena S] [--scarta N] [--durata S] [--etichetta T]
 *        [--nodo N]
 *
 * Writes: PREFISSO-primo.raw, PREFISSO-regime.raw, PREFISSO.json
 */

#include <gio/gio.h>
#include <pipewire/pipewire.h>
#include <spa/buffer/meta.h>
#include <spa/param/video/format-utils.h>
#include <spa/utils/result.h>
#include <drm_fourcc.h>
#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define ATTESA_CHIAMATA_MS 15000
#define ATTESA_NODO_MS 10000
#define ATTESA_AVVIO_S 10
#define FD_MAX 16
#define TIPI_MAX 8

/* ------------------------------------------------------------------ *
 *  The held frame
 * ------------------------------------------------------------------ */

typedef struct
{
	gboolean preso;
	uint8_t *pixel;      /* our copy: PipeWire's buffer goes back at once  */
	size_t byte;
	uint32_t stride;
	uint32_t offset;
	uint32_t dimensione_chunk;
	uint32_t tipo_dati;
	int64_t seq;
	int64_t pts;
	gboolean seq_noto;
	const char *danno;   /* "pieno" | "parziale" | "assente"                */
	guint64 indice;      /* which frame it was, counted from the first arrived */
	gint64 quando;
} Fermo;

typedef struct
{
	struct pw_thread_loop *ciclo;
	struct pw_context *contesto;
	struct pw_core *nucleo;
	struct pw_stream *flusso;
	struct spa_hook gancio;

	struct spa_video_info_raw formato;
	gboolean formato_noto;
	enum pw_stream_state stato;
	char *guasto;
	gboolean vuole_dmabuf;

	guint64 arrivati;
	guint64 prima_della_scena;
	guint64 dopo_la_scena;
	guint64 danno_pieno, danno_parziale, danno_assente;
	guint64 senza_header;

	int fd_visti[FD_MAX];
	guint quanti_fd;
	uint32_t tipi_visti[TIPI_MAX];
	guint quanti_tipi;

	/* ⛔ The scene is declared alive with a variable written by WHOEVER LAUNCHES,
	 *    not with a clock: the program must know which frames
	 *    arrived before and which after, and a timed wait does not tell them apart. */
	volatile gboolean scena_viva;
	gint64 t_scena;      /* when the scene was declared alive               */
	gint64 t_regime;     /* from when the steady-state frame may be taken   */
	guint64 salta_ancora;

	Fermo primo;
	Fermo regime;

	gint64 t_inizio;
} Presa;

/* ------------------------------------------------------------------ *
 *  The damage — copied from phase 0 because the question is the same
 * ------------------------------------------------------------------ */

static const char *guarda_danno(Presa *p, struct pw_buffer *pacco)
{
	struct spa_meta *meta = spa_buffer_find_meta(pacco->buffer, SPA_META_VideoDamage);
	struct spa_meta_region *regione;
	gboolean copre_tutto = FALSE;
	gboolean vista = FALSE;

	if (!meta)
	{
		p->danno_assente++;
		return "assente";
	}
	spa_meta_for_each(regione, meta)
	{
		if (!spa_meta_region_is_valid(regione))
			break;
		vista = TRUE;
		if (regione->region.position.x == 0 && regione->region.position.y == 0 &&
		    regione->region.size.width >= p->formato.size.width &&
		    regione->region.size.height >= p->formato.size.height)
			copre_tutto = TRUE;
	}
	if (!vista)
	{
		p->danno_assente++;
		return "assente";
	}
	if (copre_tutto)
	{
		p->danno_pieno++;
		return "pieno";
	}
	p->danno_parziale++;
	return "parziale";
}

/*
 * ⛔ IT IS COPIED, THE POINTER IS NOT KEPT.
 *
 * v1's `cattura.h` writes it at the top: *«the pixels live only for the duration
 * of the call: whoever wants them copies them»*.  A kept pointer would be
 * rewritten by the producer at the next round, and the frame written to disk
 * would be a frame different from the one whose damage and sequence the manifest tells
 * about: two measurements under the same label, which is form E2.
 */
static void trattieni(Fermo *f, struct spa_data *piano, struct spa_meta_header *intestazione,
                      const char *danno, guint64 indice, gint64 adesso)
{
	uint32_t dimensione;
	uint32_t offset = piano->chunk ? piano->chunk->offset : 0;

	dimensione = piano->chunk && piano->chunk->size > 0 ? piano->chunk->size : piano->maxsize;
	if (offset + dimensione > piano->maxsize)
		dimensione = piano->maxsize > offset ? piano->maxsize - offset : 0;
	if (!piano->data || dimensione == 0)
		return;

	g_free(f->pixel);
	f->pixel = g_malloc(dimensione);
	memcpy(f->pixel, (const uint8_t *) piano->data + offset, dimensione);
	f->byte = dimensione;
	f->stride = piano->chunk ? (uint32_t) piano->chunk->stride : 0;
	f->offset = offset;
	f->dimensione_chunk = piano->chunk ? piano->chunk->size : 0;
	f->tipo_dati = piano->type;
	f->danno = danno;
	f->indice = indice;
	f->quando = adesso;
	if (intestazione)
	{
		f->seq = (int64_t) intestazione->seq;
		f->pts = (int64_t) intestazione->pts;
		f->seq_noto = TRUE;
	}
	f->preso = TRUE;
}

static void su_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *errore)
{
	Presa *p = dati;

	p->stato = nuovo;
	if (errore)
	{
		g_free(p->guasto);
		p->guasto = g_strdup(errore);
	}
	if (nuovo == PW_STREAM_STATE_STREAMING && p->t_inizio == 0)
	{
		p->t_inizio = g_get_monotonic_time();
		fprintf(stderr, "  stream active\n");
	}
	pw_thread_loop_signal(p->ciclo, false);
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	Presa *p = dati;
	uint32_t tipo, sottotipo;
	uint8_t spazio[1024];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[3];
	int tipi = (1 << SPA_DATA_MemFd) | (1 << SPA_DATA_MemPtr);

	if (!param || id != SPA_PARAM_Format)
		return;
	if (spa_format_parse(param, &tipo, &sottotipo) < 0)
		return;
	if (tipo != SPA_MEDIA_TYPE_video || sottotipo != SPA_MEDIA_SUBTYPE_raw)
		return;
	if (spa_format_video_raw_parse(param, &p->formato) < 0)
		return;

	p->formato_noto = TRUE;
	fprintf(stderr, "  negotiated format: %ux%u %s, modifier 0x%" PRIx64 "\n",
	        p->formato.size.width, p->formato.size.height,
	        p->formato.format == SPA_VIDEO_FORMAT_BGRx ? "BGRx"
	        : p->formato.format == SPA_VIDEO_FORMAT_BGRA ? "BGRA"
	                                                     : "OTHER",
	        (uint64_t) p->formato.modifier);

	/* The data type is agreed HERE, not in the format: whoever stays silent leaves the
	 * default.  `LEZIONI.md` §4 trap 4 — the buffer type is asked for in
	 * TWO places, and declaring only one makes the negotiation succeed with inside
	 * the opposite of what was wanted. */
	if (p->vuole_dmabuf)
		tipi |= (1 << SPA_DATA_DmaBuf);

	parametri[0] = spa_pod_builder_add_object(
	    &costruttore, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
	    SPA_POD_CHOICE_RANGE_Int(4, 2, 8), SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int(tipi));
	parametri[1] = spa_pod_builder_add_object(
	    &costruttore, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_Header), SPA_PARAM_META_size,
	    SPA_POD_Int(sizeof(struct spa_meta_header)));
	parametri[2] = spa_pod_builder_add_object(
	    &costruttore, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_VideoDamage), SPA_PARAM_META_size,
	    SPA_POD_CHOICE_RANGE_Int(sizeof(struct spa_meta_region) * 4,
	                             sizeof(struct spa_meta_region) * 1,
	                             sizeof(struct spa_meta_region) * 16));
	pw_stream_update_params(p->flusso, parametri, 3);
	pw_thread_loop_signal(p->ciclo, false);
}

static void su_processo(void *dati)
{
	Presa *p = dati;
	struct pw_buffer *pacco;
	struct spa_data *piano;
	struct spa_meta_header *intestazione;
	const char *danno;
	gint64 adesso;
	guint i;
	gboolean noto;

	pacco = pw_stream_dequeue_buffer(p->flusso);
	if (!pacco)
		return;

	adesso = g_get_monotonic_time();
	piano = &pacco->buffer->datas[0];
	p->arrivati++;

	/* How many distinct buffers the producer recycles: Mutter uses four, and
	 * knowing it serves to read the rest (R29). */
	noto = FALSE;
	for (i = 0; i < p->quanti_fd; i++)
		if (p->fd_visti[i] == (piano->fd >= 0 ? (int) piano->fd : -1))
			noto = TRUE;
	if (!noto && p->quanti_fd < FD_MAX)
		p->fd_visti[p->quanti_fd++] = piano->fd >= 0 ? (int) piano->fd : -1;

	/* ⛔ THE TYPES ARE ALL COLLECTED, not only the last one kept.
	 *    `misura-cattura` prints `m->tipo_dati` of the LAST frame: if the
	 *    producer changed road midway through the measurement, the line would say one road
	 *    only for two different populations.  It has never been seen happening,
	 *    but «it has never been seen» is not «it cannot», and it costs eight integers. */
	noto = FALSE;
	for (i = 0; i < p->quanti_tipi; i++)
		if (p->tipi_visti[i] == piano->type)
			noto = TRUE;
	if (!noto && p->quanti_tipi < TIPI_MAX)
		p->tipi_visti[p->quanti_tipi++] = piano->type;

	intestazione = spa_buffer_find_meta_data(pacco->buffer, SPA_META_Header, sizeof *intestazione);
	if (!intestazione)
		p->senza_header++;
	danno = guarda_danno(p, pacco);

	if (!p->scena_viva)
	{
		p->prima_della_scena++;
		/* The VERY FIRST: the full redraw, and the frame that
		 * whoever connects to a just-mounted desktop would see. */
		if (!p->primo.preso)
			trattieni(&p->primo, piano, intestazione, danno, p->arrivati, adesso);
	}
	else
	{
		p->dopo_la_scena++;
		if (p->t_regime == 0)
			p->t_regime = p->t_scena;
		if (adesso >= p->t_regime)
		{
			if (p->salta_ancora > 0)
				p->salta_ancora--;
			else
				/* It is rewritten at every round: the steady-state frame of
				 * interest is the LAST of the window, not the first — so
				 * the damage it carries is the steady-state one and not that of the
				 * first redraw after switching the scene on. */
				trattieni(&p->regime, piano, intestazione, danno, p->arrivati, adesso);
		}
	}

	pw_stream_queue_buffer(p->flusso, pacco);
}

static const struct pw_stream_events eventi = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	.process = su_processo,
};

/* ------------------------------------------------------------------ *
 *  The format proposal — identical to that of phase 0
 * ------------------------------------------------------------------ */

static const struct spa_pod *formato_memoria(struct spa_pod_builder *c, uint32_t w, uint32_t h,
                                             uint32_t fps, uint32_t colore)
{
	struct spa_rectangle misura = SPA_RECTANGLE(w, h);
	struct spa_fraction cadenza = SPA_FRACTION(0, 1);
	struct spa_fraction minima = SPA_FRACTION(1, 1);
	struct spa_fraction massima = SPA_FRACTION(fps > 0 ? fps : 1, 1);

	return spa_pod_builder_add_object(
	    c, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat, SPA_FORMAT_mediaType,
	    SPA_POD_Id(SPA_MEDIA_TYPE_video), SPA_FORMAT_mediaSubtype,
	    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), SPA_FORMAT_VIDEO_format, SPA_POD_Id(colore),
	    SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura), SPA_FORMAT_VIDEO_framerate,
	    SPA_POD_Fraction(&cadenza), SPA_FORMAT_VIDEO_maxFramerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&massima, &minima, &massima));
}

static const struct spa_pod *formato_dmabuf(struct spa_pod_builder *c, uint32_t w, uint32_t h,
                                            uint32_t fps, uint32_t colore)
{
	struct spa_rectangle misura = SPA_RECTANGLE(w, h);
	struct spa_fraction cadenza = SPA_FRACTION(0, 1);
	struct spa_fraction minima = SPA_FRACTION(1, 1);
	struct spa_fraction massima = SPA_FRACTION(fps > 0 ? fps : 1, 1);
	struct spa_pod_frame cornice[2];

	spa_pod_builder_push_object(c, &cornice[0], SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat);
	spa_pod_builder_add(c, SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
	                    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
	                    SPA_FORMAT_VIDEO_format, SPA_POD_Id(colore), 0);
	spa_pod_builder_prop(c, SPA_FORMAT_VIDEO_modifier,
	                     SPA_POD_PROP_FLAG_MANDATORY | SPA_POD_PROP_FLAG_DONT_FIXATE);
	spa_pod_builder_push_choice(c, &cornice[1], SPA_CHOICE_Enum, 0);
	spa_pod_builder_long(c, DRM_FORMAT_MOD_INVALID);
	spa_pod_builder_long(c, DRM_FORMAT_MOD_INVALID);
	spa_pod_builder_long(c, DRM_FORMAT_MOD_LINEAR);
	spa_pod_builder_pop(c, &cornice[1]);
	spa_pod_builder_add(c, SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura),
	                    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cadenza),
	                    SPA_FORMAT_VIDEO_maxFramerate,
	                    SPA_POD_CHOICE_RANGE_Fraction(&massima, &minima, &massima), 0);
	return spa_pod_builder_pop(c, &cornice[0]);
}

/* ------------------------------------------------------------------ *
 *  Mutter's virtual monitor — the sequence that admits no permutations
 * ------------------------------------------------------------------ */

#define NOME_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define PERCORSO_REMOTE "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_REMOTE_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"
#define NOME_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define PERCORSO_SCREENCAST "/org/gnome/Mutter/ScreenCast"
#define IFACE_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define IFACE_SC_SESSIONE "org.gnome.Mutter.ScreenCast.Session"
#define IFACE_SC_FLUSSO "org.gnome.Mutter.ScreenCast.Stream"

typedef struct
{
	GDBusConnection *bus;
	char *controllo;
	char *cattura;
	char *flusso;
	uint32_t nodo;
} Palco;

static void su_nodo(GDBusConnection *bus, const char *mittente, const char *percorso,
                    const char *interfaccia, const char *segnale, GVariant *parametri, gpointer d)
{
	if (g_variant_is_of_type(parametri, G_VARIANT_TYPE("(u)")))
		g_variant_get(parametri, "(u)", (uint32_t *) d);
}

static gboolean sveglia(gpointer d)
{
	return G_SOURCE_CONTINUE;
}

/* g_bus_get_sync is never used on the session bus: GIO keeps
 * `exit-on-close` on there and kills us at logout (`LEZIONI.md` §5, «the session
 * bus»). */
static GDBusConnection *bus_di_sessione(GError **sbaglio)
{
	g_autofree char *indirizzo = g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, sbaglio);
	GDBusConnection *bus;

	if (!indirizzo)
		return NULL;
	bus = g_dbus_connection_new_for_address_sync(
	    indirizzo,
	    G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
	        G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
	    NULL, NULL, sbaglio);
	if (bus)
		g_dbus_connection_set_exit_on_close(bus, FALSE);
	return bus;
}

static GVariant *chiama(GDBusConnection *bus, const char *nome, const char *percorso,
                        const char *iface, const char *metodo, GVariant *arg,
                        const GVariantType *risposta, GError **sbaglio)
{
	return g_dbus_connection_call_sync(bus, nome, percorso, iface, metodo, arg, risposta,
	                                   G_DBUS_CALL_FLAGS_NONE, ATTESA_CHIAMATA_MS, NULL, sbaglio);
}

/*
 * ⛔ THE ORDER IS THAT OF `mutter.h`, and every permutation is punished with a
 *    different error that does not say «you got the order wrong» (`LEZIONI.md` §4 trap 1):
 *
 *      1. RemoteDesktop.CreateSession      → SessionId is read WITHOUT starting it
 *      2. ScreenCast.CreateSession         declaring remote-desktop-session-id
 *      3. RemoteDesktop.Session.Start      ← NOW, not before
 *      4. ScreenCast.Session.RecordVirtual → the stream
 *      5. Stream.Start                     ← the STREAM, not the session
 *
 * ⛔ And one subscribes to `PipeWireStreamAdded` BEFORE `Stream.Start`: the announcement
 *    arrives DURING the call, and whoever subscribes afterwards waits forever
 *    for something already gone (trap 2).
 *
 * ⚠ And the session is closed by stopping the CONTROL, not the capture: a
 *   `ScreenCast.Session.Stop` on an associated capture answers «Must be stopped
 *   from remote desktop session», and every virtual monitor not dismounted stays
 *   attached to Mutter.  On the server two other rounds are on: a monitor
 *   forgotten by this bench would be a defect the others pay for.
 */
static Palco *palco_monta(uint32_t larghezza, uint32_t altezza, GError **sbaglio)
{
	Palco *p = g_new0(Palco, 1);
	g_autofree char *id = NULL;
	GVariantBuilder prop;
	guint sottoscrizione;
	GMainContext *contesto;
	GSource *battito;
	gint64 scadenza;

	p->bus = bus_di_sessione(sbaglio);
	if (!p->bus)
		goto guasto;

	{
		g_autoptr(GVariant) r = chiama(p->bus, NOME_REMOTE, PERCORSO_REMOTE, IFACE_REMOTE,
		                               "CreateSession", NULL, G_VARIANT_TYPE("(o)"), sbaglio);
		if (!r)
		{
			g_prefix_error(sbaglio, "Mutter does not expose RemoteDesktop (is there a session?): ");
			goto guasto;
		}
		g_variant_get(r, "(o)", &p->controllo);
	}
	{
		g_autoptr(GVariant) r =
		    chiama(p->bus, NOME_REMOTE, p->controllo, "org.freedesktop.DBus.Properties", "Get",
		           g_variant_new("(ss)", IFACE_REMOTE_SESSIONE, "SessionId"),
		           G_VARIANT_TYPE("(v)"), sbaglio);
		g_autoptr(GVariant) v = NULL;
		if (!r)
			goto guasto;
		g_variant_get(r, "(v)", &v);
		id = g_variant_dup_string(v, NULL);
	}

	g_variant_builder_init(&prop, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&prop, "{sv}", "remote-desktop-session-id", g_variant_new_string(id));
	g_variant_builder_add(&prop, "{sv}", "disable-animations", g_variant_new_boolean(TRUE));
	{
		g_autoptr(GVariant) r =
		    chiama(p->bus, NOME_SCREENCAST, PERCORSO_SCREENCAST, IFACE_SCREENCAST, "CreateSession",
		           g_variant_new("(a{sv})", &prop), G_VARIANT_TYPE("(o)"), sbaglio);
		if (!r)
			goto guasto;
		g_variant_get(r, "(o)", &p->cattura);
	}
	{
		g_autoptr(GVariant) r = chiama(p->bus, NOME_REMOTE, p->controllo, IFACE_REMOTE_SESSIONE,
		                               "Start", NULL, NULL, sbaglio);
		if (!r)
			goto guasto;
	}

	g_variant_builder_init(&prop, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&prop, "{sv}", "cursor-mode", g_variant_new_uint32(2));
	g_variant_builder_add(&prop, "{sv}", "is-platform", g_variant_new_boolean(TRUE));
	{
		g_autofree char *mapping = g_uuid_string_random();
		g_autoptr(GVariant) r = NULL;

		g_variant_builder_add(&prop, "{sv}", "mapping-id", g_variant_new_string(mapping));
		r = chiama(p->bus, NOME_SCREENCAST, p->cattura, IFACE_SC_SESSIONE, "RecordVirtual",
		           g_variant_new("(a{sv})", &prop), G_VARIANT_TYPE("(o)"), sbaglio);
		if (!r)
			goto guasto;
		g_variant_get(r, "(o)", &p->flusso);
	}

	contesto = g_main_context_new();
	g_main_context_push_thread_default(contesto);
	sottoscrizione = g_dbus_connection_signal_subscribe(p->bus, NULL, IFACE_SC_FLUSSO,
	                                                    "PipeWireStreamAdded", p->flusso, NULL,
	                                                    G_DBUS_SIGNAL_FLAGS_NONE, su_nodo, &p->nodo,
	                                                    NULL);
	{
		g_autoptr(GVariant) r =
		    chiama(p->bus, NOME_SCREENCAST, p->flusso, IFACE_SC_FLUSSO, "Start", NULL, NULL, sbaglio);
		if (!r)
		{
			g_dbus_connection_signal_unsubscribe(p->bus, sottoscrizione);
			g_main_context_pop_thread_default(contesto);
			g_main_context_unref(contesto);
			goto guasto;
		}
	}
	battito = g_timeout_source_new(50);
	g_source_set_callback(battito, sveglia, NULL, NULL);
	g_source_attach(battito, contesto);
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_NODO_MS * 1000;
	while (p->nodo == 0 && g_get_monotonic_time() < scadenza)
		g_main_context_iteration(contesto, TRUE);
	g_source_destroy(battito);
	g_source_unref(battito);
	g_dbus_connection_signal_unsubscribe(p->bus, sottoscrizione);
	g_main_context_pop_thread_default(contesto);
	g_main_context_unref(contesto);

	if (p->nodo == 0)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT, "no PipeWire node announced");
		goto guasto;
	}
	fprintf(stderr, "  virtual monitor %ux%u requested, PipeWire node %u\n", larghezza, altezza,
	        p->nodo);
	return p;

guasto:
	if (p->bus && p->controllo)
	{
		g_autoptr(GError) x = NULL;
		g_autoptr(GVariant) r = g_dbus_connection_call_sync(
		    p->bus, NOME_REMOTE, p->controllo, IFACE_REMOTE_SESSIONE, "Stop", NULL, NULL,
		    G_DBUS_CALL_FLAGS_NONE, 2000, NULL, &x);
	}
	g_clear_object(&p->bus);
	g_free(p->controllo);
	g_free(p->cattura);
	g_free(p->flusso);
	g_free(p);
	return NULL;
}

static void palco_smonta(Palco *p)
{
	if (!p)
		return;
	if (p->bus && p->controllo)
	{
		g_autoptr(GError) x = NULL;
		g_autoptr(GVariant) r = g_dbus_connection_call_sync(
		    p->bus, NOME_REMOTE, p->controllo, IFACE_REMOTE_SESSIONE, "Stop", NULL, NULL,
		    G_DBUS_CALL_FLAGS_NONE, 2000, NULL, &x);
	}
	g_clear_object(&p->bus);
	g_free(p->controllo);
	g_free(p->cattura);
	g_free(p->flusso);
	g_free(p);
}

/* ------------------------------------------------------------------ *
 *  The manifest
 * ------------------------------------------------------------------ */

static const char *nome_tipo(uint32_t t)
{
	return t == SPA_DATA_DmaBuf   ? "DMA-BUF"
	       : t == SPA_DATA_MemFd  ? "MemFd"
	       : t == SPA_DATA_MemPtr ? "MemPtr"
	       : t == SPA_DATA_MemId  ? "MemId"
	                              : "UNKNOWN";
}

static const char *nome_colore(uint32_t c)
{
	return c == SPA_VIDEO_FORMAT_BGRx   ? "BGRx"
	       : c == SPA_VIDEO_FORMAT_BGRA ? "BGRA"
	                                    : "OTHER";
}

/*
 * ===========================================================================
 * ⛔ THE THREE THINGS F2.3 (ENCODING) ASKS TO BE DECLARED, NOT DEDUCED
 * ===========================================================================
 *
 * The real bit depth, the RANGE (limited or full) and the MATRIX (601 or
 * 709).  ⛔ And the reason for the third is that *a pixel comparison made with the
 * wrong matrix measures the matrix* — and F2.6 will compare pixels.  Without
 * these three declarations the red of phase 2 would have no defendant.
 *
 * ⭐ AND THEY ARE NOT DEDUCED: SPA carries them.  `struct spa_video_info_raw` has
 *    `color_range`, `color_matrix`, `transfer_function` and `color_primaries`,
 *    and `spa_format_video_raw_parse` fills them.  They are ASKED of the producer
 *    (`CODER.md` §3.7 — the sender is not deduced, it is asked) and what it
 *    answers is written, **including «I do not declare it»**: an `UNKNOWN` is an
 *    answer, and it must be written as such instead of being filled with what we
 *    expect.  Silence mistaken for a value is form E8.
 *
 * ⛔ AND THE FIRST OF THE THREE ALREADY HAS AN ANSWER THAT WEIGHS ON THE WHOLE OF PHASE 2:
 *
 *    `STUDI.md` §gnome §8.3 `[R]`, read line by line in the code of Mutter 48.7:
 *    **«Only BGRx and BGRA»**.  They are formats at **8 bits per channel**.
 *
 *    ⇒ From this capture ten real bits CANNOT come out.  An HEVC Main10
 *      fed from here carries 8 bits promoted to 10, and the label keeps
 *      saying Main10 while the image comes out fine anyway: it is the fault
 *      F2.3 calls **F2.3-A**, and ⛔ **the defendant is here, not in the encoder**.
 *      That is why the number is measured already at capture.
 */
static const char *nome_range(uint32_t r)
{
	switch (r)
	{
	case 1: return "FULL (0-255)";
	case 2: return "LIMITED (16-235)";
	default: return "NOT DECLARED by the producer";
	}
}

static const char *nome_matrice(uint32_t m)
{
	switch (m)
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

static const char *nome_trasferimento(uint32_t t)
{
	switch (t)
	{
	case 1: return "gamma 1.0 (linear)";
	case 4: return "gamma 2.2";
	case 5: return "BT.709";
	case 7: return "sRGB";
	case 11: return "BT.2020 12 bits";
	default: return "NOT DECLARED by the producer";
	}
}

static const char *nome_primari(uint32_t p)
{
	switch (p)
	{
	case 1: return "BT.709";
	case 4: return "SMPTE170M";
	case 7: return "BT.2020";
	default: return "NOT DECLARED by the producer";
	}
}

/* The bits per channel are derived from the FORMAT, which is a fact of the producer, not
 * a hypothesis of ours.  ⛔ And if one day a format arrived that we do not
 * know, 0 is answered and it is declared: a value invented here
 * would become «10 real bits» in an F2.3 table. */
static int bit_per_canale(uint32_t c)
{
	switch (c)
	{
	case SPA_VIDEO_FORMAT_BGRx:
	case SPA_VIDEO_FORMAT_BGRA:
	case SPA_VIDEO_FORMAT_RGBx:
	case SPA_VIDEO_FORMAT_RGBA:
	case SPA_VIDEO_FORMAT_xRGB:
	case SPA_VIDEO_FORMAT_ARGB:
		return 8;
	default:
		return 0;
	}
}

static gboolean scrivi_raw(const char *percorso, const Fermo *f, GError **sbaglio)
{
	return g_file_set_contents(percorso, (const char *) f->pixel, (gssize) f->byte, sbaglio);
}

static void manifesto_fermo(GString *s, const char *chiave, const Fermo *f, const char *file)
{
	if (!f->preso)
	{
		g_string_append_printf(s, "  \"%s\": null,\n", chiave);
		return;
	}
	g_string_append_printf(s,
	                       "  \"%s\": {\n"
	                       "    \"file\": \"%s\",\n"
	                       "    \"byte\": %zu,\n"
	                       "    \"stride\": %u,\n"
	                       "    \"offset\": %u,\n"
	                       "    \"dimensione_chunk\": %u,\n"
	                       "    \"tipo_dichiarato\": \"%s\",\n"
	                       "    \"danno\": \"%s\",\n"
	                       "    \"indice_fra_gli_arrivati\": %" PRIu64 ",\n"
	                       "    \"seq\": %" PRId64 ",\n"
	                       "    \"pts\": %" PRId64 ",\n"
	                       "    \"seq_nota\": %s\n"
	                       "  },\n",
	                       chiave, file, f->byte, f->stride, f->offset, f->dimensione_chunk,
	                       nome_tipo(f->tipo_dati), f->danno, f->indice, f->seq, f->pts,
	                       f->seq_noto ? "true" : "false");
}

/* ------------------------------------------------------------------ *
 *  The program
 * ------------------------------------------------------------------ */

int main(int argc, char **argv)
{
	uint32_t larghezza = 1920, altezza = 1080, fps = 60, nodo = 0;
	double dopo_scena = 3.0, durata = 12.0, attesa_scena = 25.0;
	guint64 scarta = 10;
	/* ⛔ How many frames are REQUIRED after the scene was declared
	 *    alive.  One is enough: the question is «does the scene paint on the screen we
	 *    are capturing, yes or no?».  With `0` one declares one wants to measure
	 *    the legitimate zero («fermo» scene). */
	guint64 minimo_dopo_scena = 1;
	gboolean vuole_dmabuf = FALSE;
	uint32_t colore = SPA_VIDEO_FORMAT_BGRx;
	const char *etichetta = "senza-nome";
	const char *uscita = NULL, *pronto = NULL, *segnale_scena = NULL;
	Presa p = { 0 };
	Palco *palco = NULL;
	uint8_t spazio[2048];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[2];
	uint32_t n_parametri = 0;
	g_autoptr(GError) sbaglio = NULL;
	g_autofree char *file_primo = NULL, *file_regime = NULL, *file_json = NULL;
	GString *manifesto;
	gint64 scadenza, fine;
	int codice = 0;
	const char *esito;
	char quando[64];
	time_t adesso_epoch;
	struct tm adesso_tm;
	guint i;

	for (i = 1; (int) i < argc; i++)
	{
		if (!strcmp(argv[i], "--uscita") && (int) i + 1 < argc)
			uscita = argv[++i];
		else if (!strcmp(argv[i], "--pronto") && (int) i + 1 < argc)
			pronto = argv[++i];
		else if (!strcmp(argv[i], "--segnale-scena") && (int) i + 1 < argc)
			segnale_scena = argv[++i];
		else if (!strcmp(argv[i], "--nodo") && (int) i + 1 < argc)
			nodo = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--larghezza") && (int) i + 1 < argc)
			larghezza = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--altezza") && (int) i + 1 < argc)
			altezza = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--fps") && (int) i + 1 < argc)
			fps = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--dopo-scena") && (int) i + 1 < argc)
			dopo_scena = atof(argv[++i]);
		else if (!strcmp(argv[i], "--attesa-scena") && (int) i + 1 < argc)
			attesa_scena = atof(argv[++i]);
		else if (!strcmp(argv[i], "--durata") && (int) i + 1 < argc)
			durata = atof(argv[++i]);
		else if (!strcmp(argv[i], "--scarta") && (int) i + 1 < argc)
			scarta = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--minimo-dopo-scena") && (int) i + 1 < argc)
			minimo_dopo_scena = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--dmabuf"))
			vuole_dmabuf = TRUE;
		else if (!strcmp(argv[i], "--bgra"))
			colore = SPA_VIDEO_FORMAT_BGRA;
		else if (!strcmp(argv[i], "--etichetta") && (int) i + 1 < argc)
			etichetta = argv[++i];
		else
		{
			fprintf(stderr,
			        "usage: %s --uscita PREFISSO --pronto FILE --segnale-scena FILE\n"
			        "        [--larghezza W] [--altezza H] [--fps N] [--bgra] [--dmabuf]\n"
			        "        [--dopo-scena S] [--scarta N] [--durata S] [--attesa-scena S]\n"
			        "        [--minimo-dopo-scena N] [--etichetta T] [--nodo N]\n",
			        argv[0]);
			return 2;
		}
	}
	if (!uscita || !pronto || !segnale_scena)
	{
		fprintf(stderr, "⛔ --uscita, --pronto and --segnale-scena are needed.\n"
		                "   The --pronto file tells whoever launches that the virtual monitor is there and\n"
		                "   that the scene can be switched on; the --segnale-scena file is the\n"
		                "   answer: «the scene is on».  Without these two the order between\n"
		                "   monitor and scene would go back to being a timed wait.\n");
		return 2;
	}

	file_primo = g_strdup_printf("%s-primo.raw", uscita);
	file_regime = g_strdup_printf("%s-regime.raw", uscita);
	file_json = g_strdup_printf("%s.json", uscita);

	adesso_epoch = time(NULL);
	gmtime_r(&adesso_epoch, &adesso_tm);
	strftime(quando, sizeof quando, "%Y-%m-%dT%H:%M:%SZ", &adesso_tm);

	p.vuole_dmabuf = vuole_dmabuf;

	fprintf(stderr, "== %s: requested %ux%u, %s, ceiling %u fps, road %s ==\n", etichetta, larghezza,
	        altezza, nome_colore(colore), fps, vuole_dmabuf ? "DMA-BUF" : "memory");

	if (nodo == 0)
	{
		palco = palco_monta(larghezza, altezza, &sbaglio);
		if (!palco)
		{
			fprintf(stderr, "⛔ virtual monitor not mounted: %s\n", sbaglio->message);
			return 1;
		}
		nodo = palco->nodo;
	}

	pw_init(NULL, NULL);
	p.ciclo = pw_thread_loop_new("presa", NULL);
	p.contesto = pw_context_new(pw_thread_loop_get_loop(p.ciclo), NULL, 0);
	pw_thread_loop_lock(p.ciclo);
	if (pw_thread_loop_start(p.ciclo) < 0)
	{
		pw_thread_loop_unlock(p.ciclo);
		fprintf(stderr, "⛔ PipeWire thread not started\n");
		palco_smonta(palco);
		return 1;
	}
	p.nucleo = pw_context_connect(p.contesto, NULL, 0);
	if (!p.nucleo)
	{
		pw_thread_loop_unlock(p.ciclo);
		fprintf(stderr, "⛔ connection to PipeWire failed\n");
		palco_smonta(palco);
		return 1;
	}
	p.flusso = pw_stream_new(p.nucleo, "02-cattura-fotogramma",
	                         pw_properties_new(PW_KEY_MEDIA_TYPE, "Video", PW_KEY_MEDIA_CATEGORY,
	                                           "Capture", PW_KEY_MEDIA_ROLE, "Screen", NULL));
	pw_stream_add_listener(p.flusso, &p.gancio, &eventi, &p);

	if (vuole_dmabuf)
		parametri[n_parametri++] = formato_dmabuf(&costruttore, larghezza, altezza, fps, colore);
	parametri[n_parametri++] = formato_memoria(&costruttore, larghezza, altezza, fps, colore);

	if (pw_stream_connect(p.flusso, PW_DIRECTION_INPUT, nodo,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parametri, n_parametri) < 0)
	{
		pw_thread_loop_unlock(p.ciclo);
		fprintf(stderr, "⛔ hooking onto node %u failed\n", nodo);
		palco_smonta(palco);
		return 1;
	}
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_S * G_USEC_PER_SEC;
	while (p.stato != PW_STREAM_STATE_PAUSED && p.stato != PW_STREAM_STATE_STREAMING &&
	       p.stato != PW_STREAM_STATE_ERROR && g_get_monotonic_time() < scadenza)
		pw_thread_loop_timed_wait(p.ciclo, 1);
	pw_thread_loop_unlock(p.ciclo);

	if (p.stato == PW_STREAM_STATE_ERROR)
	{
		printf("GUASTO\t%s\tcapture refused\n", etichetta);
		fprintf(stderr, "⛔ FAILED: capture refused: %s\n",
		        p.guasto ? p.guasto : "without explanation");
		palco_smonta(palco);
		return 2;
	}

	/* ⛔ The «pronto» file is written ONLY when the stream is really active.
	 *    Writing it before would mean switching the scene on on a monitor that
	 *    does not exist yet, and the scene would open on nothing — which is precisely
	 *    the order phase 0's `banco.sh` had had to learn. */
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_S * G_USEC_PER_SEC;
	while (p.stato != PW_STREAM_STATE_STREAMING && g_get_monotonic_time() < scadenza)
		g_usleep(20000);
	if (p.stato != PW_STREAM_STATE_STREAMING)
	{
		printf("GUASTO\t%s\tstream never active\n", etichetta);
		fprintf(stderr,
		        "⛔ FAILED (not «zero»): the stream never became active.\n"
		        "   final state %d%s%s.  There is no frame to judge here:\n"
		        "   capture never started (LEZIONI.md §1.9).\n",
		        (int) p.stato, p.guasto ? ", fault: " : "", p.guasto ? p.guasto : "");
		palco_smonta(palco);
		return 2;
	}
	if (!g_file_set_contents(pronto, "pronto\n", -1, &sbaglio))
	{
		fprintf(stderr, "⛔ I cannot write %s: %s\n", pronto, sbaglio->message);
		palco_smonta(palco);
		return 1;
	}
	fprintf(stderr, "  pronto: the scene can be switched on now\n");

	/* Wait for whoever launches to declare the scene on.  ⛔ And if it never arrives
	 * nothing is measured anyway: it is declared.  A scene that does not start and a
	 * silent compositor look the same — item 8 of
	 * `FASI.md` §00-ambiente, and the third face of one same defect. */
	scadenza = g_get_monotonic_time() + (gint64) (attesa_scena * G_USEC_PER_SEC);
	while (!g_file_test(segnale_scena, G_FILE_TEST_EXISTS) && g_get_monotonic_time() < scadenza)
		g_usleep(50000);
	if (!g_file_test(segnale_scena, G_FILE_TEST_EXISTS))
	{
		printf("GUASTO\t%s\tthe scene was never declared on\n", etichetta);
		fprintf(stderr,
		        "⛔ FAILED: after %.1f s nobody declared the scene on (%s).\n"
		        "   A frame taken now would be the empty desktop under\n"
		        "   the scene's label: two different things under the same name.\n",
		        attesa_scena, segnale_scena);
		palco_smonta(palco);
		return 2;
	}
	p.t_scena = g_get_monotonic_time();
	p.t_regime = p.t_scena + (gint64) (dopo_scena * G_USEC_PER_SEC);
	p.salta_ancora = scarta;
	p.scena_viva = TRUE;
	fprintf(stderr, "  scene declared on: the steady state starts in %.1f s\n", dopo_scena);

	fine = p.t_scena + (gint64) (durata * G_USEC_PER_SEC);
	while (g_get_monotonic_time() < fine)
		g_usleep(50000);

	/* ⛔ «It WAS active» is not «it still is»: death midway through the measurement. */
	if (p.stato != PW_STREAM_STATE_STREAMING)
	{
		printf("GUASTO\t%s\tstream dropped during the take\n", etichetta);
		fprintf(stderr,
		        "⛔ FAILED (not «zero»): the stream was active and dropped.\n"
		        "   final state %d%s%s.  Frames arrived before dropping: %" PRIu64 ".\n",
		        (int) p.stato, p.guasto ? ", fault: " : "", p.guasto ? p.guasto : "", p.arrivati);
		palco_smonta(palco);
		return 2;
	}

	/* ⛔ THE ROAD IS CHECKED, IT IS NOT TAKEN AS ASKED FOR — `LEZIONI.md` §1.8. */
	if (vuole_dmabuf && p.quanti_tipi > 0 && p.tipi_visti[0] != SPA_DATA_DmaBuf)
	{
		printf("GUASTO\t%s\tDMA-BUF requested, memory obtained\n", etichetta);
		fprintf(stderr,
		        "⛔ FAILED: DMA-BUF was requested and the producer delivered %s.\n"
		        "   No silent fallback (LEZIONI.md §1.8, corollary).\n",
		        nome_tipo(p.tipi_visti[0]));
		palco_smonta(palco);
		return 2;
	}

	/*
	 * ⛔ A LIVE SCENE AND ZERO FRAMES IS NOT A ZERO: IT IS A FAULT.
	 *
	 * Found on 12 Aug 2026, at the FIRST real round of this bench, and found
	 * because the bench came out **VERDE** while the defect was alive — that is the
	 * worst thing a bench can do (`REVIEWER.md` §1).
	 *
	 * What had happened: the GNOME session ALREADY had a virtual monitor
	 * (`Meta-0`), our `RecordVirtual` added a second one (`Meta-1`),
	 * and `mpv --fs` went full screen on the FIRST — which is not the one we
	 * were capturing.  The scene was alive, painting at 60 frames per
	 * second, `ps` said `Sl`, and our capture received **zero**.
	 *
	 * ⇒ With a scene DECLARED ALIVE AND MOVING, zero frames is not the
	 *   legitimate behaviour of trap 8: it is the proof that we are
	 *   looking at a screen different from the one the scene paints on.  It is the
	 *   check of `LEZIONI.md` §1.1 — *«how much the client draws, counted
	 *   next to how much capture delivers: without it, a ceiling of the scene gets
	 *   attributed to the compositor, and vice versa»*.
	 *
	 * ⚠ Whoever wants to measure the legitimate zero — the still desktop — passes
	 *   `--minimo-dopo-scena 0` and declares it.  It is not obtained by chance.
	 */
	if (p.scena_viva && p.dopo_la_scena < minimo_dopo_scena)
	{
		printf("GUASTO\t%s\tlive scene and %" PRIu64 " frames after\n", etichetta,
		       p.dopo_la_scena);
		fprintf(stderr,
		        "⛔ FAILED (not «zero»): the scene was declared alive and there arrived\n"
		        "   %" PRIu64 " frames after it (minimum required %" PRIu64 ").\n"
		        "   Before the scene %" PRIu64 " had arrived: the stream works.\n"
		        "\n"
		        "   ⇒ It is not the still desktop. It is that the scene paints on a\n"
		        "     DIFFERENT SCREEN from the one we are capturing: if the session already has\n"
		        "     a monitor, a full-screen window goes on that one and not on the\n"
		        "     virtual monitor we have just mounted.\n"
		        "     The screen is declared to the scene (mpv `--fs-screen-name`), and it is\n"
		        "     checked that it obeyed (CODER.md §3.9).\n",
		        p.dopo_la_scena, minimo_dopo_scena, p.prima_della_scena);
		palco_smonta(palco);
		return 2;
	}

	/* --- the writing --------------------------------------------------- */
	if (p.arrivati == 0)
	{
		/* ⭐ LEGITIMATE ZERO, and it is told from failure with exit 3.
		 *    The stream was active for the whole take: if no frame
		 *    arrived, the desktop did not change — which on Mutter is the
		 *    declared behaviour, not a fault (trap 8). */
		esito = "ZERO FOTOGRAMMI";
		codice = 3;
	}
	else if (vuole_dmabuf)
	{
		/* ⛔ WITH DMA-BUF THE PIXELS ARE NOT READ FROM HERE, AND IT IS SAID.
		 *    The descriptor lives on the card: reading it would mean
		 *    importing it, that is half the stage.  This round serves to DECLARE
		 *    the buffer type, not to judge the image, and a `.raw` written
		 *    from here would be empty under the label of a frame. */
		esito = "TIPO DICHIARATO, PIXEL NON LETTI (dmabuf)";
		codice = 0;
	}
	else if (!p.regime.preso && !p.primo.preso)
	{
		printf("GUASTO\t%s\tframes arrived but none copyable\n", etichetta);
		fprintf(stderr,
		        "⛔ FAILED: %" PRIu64 " frames arrived and none had mapped\n"
		        "   pixels (null data or empty chunk).  It is not a zero: it is a buffer\n"
		        "   that could not be read.\n",
		        p.arrivati);
		palco_smonta(palco);
		return 2;
	}
	else
	{
		esito = "UN FOTOGRAMMA";
		codice = 0;
		if (p.primo.preso && !scrivi_raw(file_primo, &p.primo, &sbaglio))
		{
			fprintf(stderr, "⛔ I cannot write %s: %s\n", file_primo, sbaglio->message);
			palco_smonta(palco);
			return 1;
		}
		if (p.regime.preso && !scrivi_raw(file_regime, &p.regime, &sbaglio))
		{
			fprintf(stderr, "⛔ I cannot write %s: %s\n", file_regime, sbaglio->message);
			palco_smonta(palco);
			return 1;
		}
	}

	manifesto = g_string_new("{\n");
	g_string_append_printf(manifesto,
	                       "  \"strumento\": \"02-cattura-fotogramma\",\n"
	                       "  \"etichetta\": \"%s\",\n"
	                       "  \"quando_utc\": \"%s\",\n"
	                       "  \"nodo_pipewire\": %u,\n"
	                       "  \"esito\": \"%s\",\n"
	                       "  \"uscita\": %d,\n",
	                       etichetta, quando, nodo, esito, codice);
	g_string_append_printf(manifesto,
	                       "  \"chiesto\": {\n"
	                       "    \"larghezza\": %u, \"altezza\": %u, \"fps_massimi\": %u,\n"
	                       "    \"colore\": \"%s\", \"strada\": \"%s\",\n"
	                       "    \"cadenza\": \"0/1 with maxFramerate at %u — «send me a frame "
	                       "when something changes»\"\n"
	                       "  },\n",
	                       larghezza, altezza, fps, nome_colore(colore),
	                       vuole_dmabuf ? "dmabuf" : "memoria", fps);
	g_string_append_printf(manifesto,
	                       "  \"negoziato\": {\n"
	                       "    \"noto\": %s,\n"
	                       "    \"larghezza\": %u, \"altezza\": %u,\n"
	                       "    \"colore\": \"%s\",\n"
	                       "    \"modificatore\": \"0x%" PRIx64 "\",\n"
	                       "    \"chi_lo_dice\": \"PipeWire, SPA_PARAM_Format in the param_changed "
	                       "callback — it is not the label we gave it\"\n"
	                       "  },\n",
	                       p.formato_noto ? "true" : "false", p.formato.size.width,
	                       p.formato.size.height, nome_colore(p.formato.format),
	                       (uint64_t) p.formato.modifier);

	/* ⛔ THE THREE THINGS F2.3 ASKS TO BE DECLARED — asked of the producer, not
	 *    deduced, and written as it answers, «I do not declare it» included. */
	g_string_append_printf(
	    manifesto,
	    "  \"consegna_a_F2_3\": {\n"
	    "    \"bit_per_canale\": %d,\n"
	    "    \"bit_per_canale_chi_lo_dice\": \"the negotiated FORMAT (%s). "
	    "STUDI.md §gnome §8.3 [R]: Mutter delivers ONLY BGRx and BGRA, which are 8 bits per "
	    "channel — from this capture ten real bits do NOT come out\",\n"
	    "    \"⛔ F2.3-A\": \"an HEVC Main10 fed from here carries 8 bits promoted to "
	    "10: the label says Main10, the image comes out fine anyway, and the defendant is "
	    "THE CAPTURE, not the encoder\",\n"
	    "    \"range\": \"%s\",\n"
	    "    \"matrice\": \"%s\",\n"
	    "    \"trasferimento\": \"%s\",\n"
	    "    \"primari\": \"%s\",\n"
	    "    \"chi_lo_dice\": \"spa_video_info_raw.color_range / .color_matrix / "
	    ".transfer_function / .color_primaries, filled by "
	    "spa_format_video_raw_parse on the producer's SPA_PARAM_Format\",\n"
	    "    \"⚠ sulla matrice\": \"at capture the pixels are RGB: no "
	    "601/709 matrix was applied by us. The matrix is CHOSEN by F2.3 when converting "
	    "to YCbCr, and F2.6 must compare with the same one — a comparison made with the "
	    "wrong matrix measures the matrix\",\n"
	    "    \"valori_grezzi\": {\"color_range\": %u, \"color_matrix\": %u, "
	    "\"transfer_function\": %u, \"color_primaries\": %u}\n"
	    "  },\n",
	    bit_per_canale(p.formato.format), nome_colore(p.formato.format),
	    nome_range(p.formato.color_range), nome_matrice(p.formato.color_matrix),
	    nome_trasferimento(p.formato.transfer_function),
	    nome_primari(p.formato.color_primaries), p.formato.color_range,
	    p.formato.color_matrix, p.formato.transfer_function, p.formato.color_primaries);

	g_string_append(manifesto, "  \"buffer\": {\n    \"tipi_visti\": [");
	for (i = 0; i < p.quanti_tipi; i++)
		g_string_append_printf(manifesto, "%s\"%s\"", i ? ", " : "", nome_tipo(p.tipi_visti[i]));
	g_string_append_printf(manifesto,
	                       "],\n"
	                       "    \"distinti_riciclati\": %u,\n"
	                       "    \"chi_lo_dice\": \"PipeWire, spa_data.type of plane 0 of every "
	                       "buffer — asked for in two places (format and SPA_PARAM_Buffers)\"\n"
	                       "  },\n",
	                       p.quanti_fd);

	g_string_append_printf(manifesto,
	                       "  \"fotogrammi\": {\n"
	                       "    \"minimo_dopo_la_scena_preteso\": %" PRIu64 ",\n"
	                       "    \"arrivati_in_tutto\": %" PRIu64 ",\n"
	                       "    \"prima_della_scena\": %" PRIu64 ",\n"
	                       "    \"dopo_la_scena\": %" PRIu64 ",\n"
	                       "    \"danno_pieno\": %" PRIu64 ",\n"
	                       "    \"danno_parziale\": %" PRIu64 ",\n"
	                       "    \"danno_assente\": %" PRIu64 ",\n"
	                       "    \"senza_header\": %" PRIu64 "\n"
	                       "  },\n",
	                       minimo_dopo_scena, p.arrivati, p.prima_della_scena, p.dopo_la_scena,
	                       p.danno_pieno, p.danno_parziale, p.danno_assente, p.senza_header);

	manifesto_fermo(manifesto, "primo", &p.primo, file_primo);
	manifesto_fermo(manifesto, "regime", &p.regime, file_regime);

	/*
	 * ⛔ THE WARNINGS SIT IN THE MANIFEST, NOT IN A DOCUMENT.
	 *
	 * Invariant I7: the protection against a known defect lives in the program, not in
	 * a line that can get lost.  Whoever reads this manifest six months from now will not
	 * have read `REVIEWER.md` §2, and the deduction «MemFd therefore software» has
	 * already cost twice.
	 */
	g_string_append(manifesto,
	                "  \"avvertenze\": [\n"
	                "    \"⛔ E1 — the buffer type does NOT say where Mutter renders. A MemFd here is "
	                "the answer to what WE ASKED for (readable pixels are needed), not "
	                "a discovery about the compositor. LEZIONI.md §1.11.\",\n"
	                "    \"⛔ E1 — nor the opposite: a DMA-BUF does not prove rendering on the "
	                "GPU. An open render node is necessary, not sufficient.\",\n"
	                "    \"⚠ this tool does NOT measure rate: it copies two frames inside the "
	                "real-time callback, and a frames-per-second number that came out "
	                "of here would be skewed by us. Rate belongs to phase 0 (36 ± 2) and "
	                "phase 3.\",\n"
	                "    \"⚠ 'negoziato' and 'chiesto' are two different fields on purpose: item "
	                "12-bis of FASI.md §00-ambiente is a label that declared a size that "
	                "the compositor had never honoured.\"\n"
	                "  ]\n}\n");

	if (!g_file_set_contents(file_json, manifesto->str, -1, &sbaglio))
	{
		fprintf(stderr, "⛔ I cannot write %s: %s\n", file_json, sbaglio->message);
		g_string_free(manifesto, TRUE);
		palco_smonta(palco);
		return 1;
	}
	g_string_free(manifesto, TRUE);

	printf("PRESA\t%s\t%s\t%s\t%" PRIu64 "\t%" PRIu64 "\t%s\n", etichetta, esito, file_json,
	       p.arrivati, p.dopo_la_scena,
	       p.quanti_tipi > 0 ? nome_tipo(p.tipi_visti[0]) : "NONE");
	fprintf(stderr,
	        "  outcome: %s\n"
	        "  arrived %" PRIu64 " (before the scene %" PRIu64 ", after %" PRIu64 ")\n"
	        "  damage: full %" PRIu64 ", partial %" PRIu64 ", absent %" PRIu64 "\n"
	        "  distinct recycled buffers: %u\n"
	        "  manifest: %s\n",
	        esito, p.arrivati, p.prima_della_scena, p.dopo_la_scena, p.danno_pieno,
	        p.danno_parziale, p.danno_assente, p.quanti_fd, file_json);

	pw_thread_loop_lock(p.ciclo);
	pw_stream_disconnect(p.flusso);
	pw_stream_destroy(p.flusso);
	pw_thread_loop_unlock(p.ciclo);
	pw_thread_loop_stop(p.ciclo);
	pw_core_disconnect(p.nucleo);
	pw_context_destroy(p.contesto);
	pw_thread_loop_destroy(p.ciclo);
	palco_smonta(palco);
	g_free(p.primo.pixel);
	g_free(p.regime.pixel);
	g_free(p.guasto);
	return codice;
}
