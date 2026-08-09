/*
 * misura-cattura — quanti fotogrammi al secondo consegna un compositore Wayland.
 *
 * Sta FUORI dal prodotto di proposito.  La domanda posta dall'utente il 7 agosto
 * 2026 — «misuriamo le performance che Mutter e' in grado di erogare alle varie
 * risoluzioni e profondita' di colore» — richiede di misurare LA SOLA CATTURA,
 * con RDP e il codificatore fuori dai piedi (terzo punto del compito).  Un banco
 * dentro REMOTIX misurerebbe REMOTIX.
 *
 * Che cosa fa, in una riga: apre un flusso PipeWire, conta i fotogrammi che
 * arrivano per N secondi, e dice quanti al secondo — piu' tutto quel che serve a
 * capire SE quel numero e' un tetto del compositore o un tetto nostro.
 *
 * Due modi di procurarsi il flusso:
 *
 *   --mutter    fa la sequenza obbligata di §7.3 di REFERENCE.md e monta un
 *               monitor virtuale della misura chiesta.  E' l'unico modo di
 *               variare la risoluzione senza uno schermo fisico.
 *   --nodo N    si aggancia a un nodo PipeWire gia' esistente.  Serve agli altri
 *               compositori, che il nodo lo annunciano per strade loro.
 *
 * Le tre trappole gia' pagate, e qui rispettate:
 *
 *   1. il DMA-BUF si chiede in DUE posti (formato + SPA_PARAM_Buffers), o la
 *      negoziazione riesce e i buffer arrivano lo stesso in memoria — R29;
 *   2. i metadati si chiedono, o non arrivano: senza `SPA_META_Header` non si sa
 *      quale fotogramma sia, senza `SPA_META_VideoDamage` non si sa quanta parte
 *      sia stata ridipinta davvero — ed e' la differenza fra «il compositore non
 *      da'» e «il compositore da' un diff»;
 *   3. non si stampa una riga per fotogramma: si conta e si riassume.  Il ciclo
 *      di PipeWire e' di tempo reale, e chi lo rallenta falsa la sua misura.
 */

#include <gio/gio.h>
#include <pipewire/pipewire.h>
#include <spa/buffer/meta.h>
#include <spa/param/video/format-utils.h>
#include <spa/utils/result.h>
#include <drm_fourcc.h>
#include <inttypes.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define ATTESA_CHIAMATA_MS 15000
#define ATTESA_NODO_MS 10000
#define ATTESA_AVVIO_S 10
#define FD_MAX 16
#define INTERVALLI_MAX 200000

/* ------------------------------------------------------------------ *
 *  Il contatore
 * ------------------------------------------------------------------ */

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

	/* conteggi, tutti aggiornati dal thread di PipeWire */
	guint64 arrivati;         /* fotogrammi consegnati, dal primo istante   */
	guint64 contati;          /* quelli dopo lo scarto iniziale             */
	guint64 danno_assente;    /* senza il metadato del danno                */
	guint64 danno_pieno;      /* danno che copre tutta la superficie        */
	guint64 danno_parziale;   /* danno che copre solo una parte             */
	guint64 senza_header;     /* senza SPA_META_Header                      */
	guint64 fence_non_pronta; /* DMA-BUF ancora in scrittura all'arrivo     */
	guint64 salti_seq;        /* buchi nella numerazione del produttore     */
	guint64 ultimo_seq;
	gboolean seq_noto;

	int fd_visti[FD_MAX];
	guint quanti_fd;

	uint32_t tipo_dati; /* SPA_DATA_* dell'ultimo fotogramma               */
	uint32_t stride;

	gint64 t_inizio;    /* quando il flusso e' diventato attivo             */
	gint64 t_scarto;    /* fine del riscaldamento                           */
	gint64 t_primo;     /* primo fotogramma contato                         */
	gint64 t_ultimo;    /* ultimo fotogramma contato                        */
	gint64 fine;        /* quando smettere                                  */
	gboolean conta;

	gint32 *intervalli; /* microsecondi fra un fotogramma e il precedente   */
	guint n_intervalli;
} Misura;

/* Il DMA-BUF si puo' interrogare: la sincronizzazione implicita del kernel lo
 * rende leggibile solo quando chi disegna ha finito.  Con timeout zero e' una
 * domanda, non un'attesa, e costa abbastanza poco da stare sul thread di tempo
 * reale.  Ritorna 1 pronto, 0 non ancora, -1 non si sa. */
static int fence_pronta(int fd)
{
	struct pollfd sonda = { .fd = fd, .events = POLLIN };
	int esito = poll(&sonda, 1, 0);

	if (esito < 0)
		return -1;
	return esito > 0 ? 1 : 0;
}

static void su_stato(void *dati, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *errore)
{
	Misura *m = dati;

	m->stato = nuovo;
	if (errore)
	{
		g_free(m->guasto);
		m->guasto = g_strdup(errore);
	}
	if (nuovo == PW_STREAM_STATE_STREAMING && m->t_inizio == 0)
	{
		m->t_inizio = g_get_monotonic_time();
		fprintf(stderr, "  flusso attivo\n");
	}
	pw_thread_loop_signal(m->ciclo, false);
}

static void su_parametri(void *dati, uint32_t id, const struct spa_pod *param)
{
	Misura *m = dati;
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
	if (spa_format_video_raw_parse(param, &m->formato) < 0)
		return;

	m->formato_noto = TRUE;
	fprintf(stderr, "  formato negoziato: %ux%u %s, modificatore 0x%" PRIx64 "\n",
	        m->formato.size.width, m->formato.size.height,
	        m->formato.format == SPA_VIDEO_FORMAT_BGRx ? "BGRx" : "BGRA",
	        (uint64_t) m->formato.modifier);

	/* Il tipo dei dati si concorda QUI, non nel formato: chi tace lascia il
	 * predefinito, che e' la memoria ordinaria.  R29, primo punto. */
	if (m->vuole_dmabuf)
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
	pw_stream_update_params(m->flusso, parametri, 3);
	pw_thread_loop_signal(m->ciclo, false);
}

static void guarda_danno(Misura *m, struct pw_buffer *pacco)
{
	struct spa_meta *meta = spa_buffer_find_meta(pacco->buffer, SPA_META_VideoDamage);
	struct spa_meta_region *regione;
	gboolean copre_tutto = FALSE;
	gboolean vista = FALSE;

	if (!meta)
	{
		m->danno_assente++;
		return;
	}
	spa_meta_for_each(regione, meta)
	{
		if (!spa_meta_region_is_valid(regione))
			break;
		vista = TRUE;
		if (regione->region.position.x == 0 && regione->region.position.y == 0 &&
		    regione->region.size.width >= m->formato.size.width &&
		    regione->region.size.height >= m->formato.size.height)
			copre_tutto = TRUE;
	}
	if (!vista)
		m->danno_assente++;
	else if (copre_tutto)
		m->danno_pieno++;
	else
		m->danno_parziale++;
}

static void su_processo(void *dati)
{
	Misura *m = dati;
	struct pw_buffer *pacco;
	struct spa_data *piano;
	struct spa_meta_header *intestazione;
	gint64 adesso;

	pacco = pw_stream_dequeue_buffer(m->flusso);
	if (!pacco)
		return;

	adesso = g_get_monotonic_time();
	piano = &pacco->buffer->datas[0];
	m->arrivati++;
	m->tipo_dati = piano->type;
	m->stride = piano->chunk ? (uint32_t) piano->chunk->stride : 0;

	/* Quanti buffer distinti ricicla il produttore.  Mutter ne usa quattro
	 * (R29), e saperlo serve a leggere il resto. */
	{
		int chiave = piano->fd >= 0 ? (int) piano->fd : -1;
		gboolean noto = FALSE;
		guint i;

		for (i = 0; i < m->quanti_fd; i++)
			if (m->fd_visti[i] == chiave)
				noto = TRUE;
		if (!noto && m->quanti_fd < FD_MAX)
			m->fd_visti[m->quanti_fd++] = chiave;
	}

	intestazione = spa_buffer_find_meta_data(pacco->buffer, SPA_META_Header, sizeof *intestazione);
	if (!intestazione)
		m->senza_header++;
	else
	{
		if (m->seq_noto && intestazione->seq > m->ultimo_seq + 1)
			m->salti_seq += intestazione->seq - m->ultimo_seq - 1;
		m->ultimo_seq = intestazione->seq;
		m->seq_noto = TRUE;
	}

	guarda_danno(m, pacco);

	if (piano->type == SPA_DATA_DmaBuf && piano->fd >= 0 && fence_pronta(piano->fd) == 0)
		m->fence_non_pronta++;

	/* Il riscaldamento non si conta: i primi fotogrammi dopo il montaggio del
	 * monitor virtuale sono il ridisegno, non il regime (R10, e la lezione di
	 * R29 sul campione preso all'avvio). */
	if (!m->conta && adesso >= m->t_scarto)
	{
		m->conta = TRUE;
		m->t_primo = adesso;
	}
	if (m->conta)
	{
		if (m->contati > 0 && m->n_intervalli < INTERVALLI_MAX)
			m->intervalli[m->n_intervalli++] = (gint32) (adesso - m->t_ultimo);
		m->contati++;
		m->t_ultimo = adesso;
	}

	pw_stream_queue_buffer(m->flusso, pacco);
}

static const struct pw_stream_events eventi = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = su_stato,
	.param_changed = su_parametri,
	.process = su_processo,
};

/* ------------------------------------------------------------------ *
 *  La proposta di formato
 * ------------------------------------------------------------------ */

/* Con `--fissa` la cadenza si dichiara PIENA invece che a zero.  Zero significa
 * «mandami un fotogramma quando cambia qualcosa» ed e' quel che serve a un
 * desktop remoto (§7.3 di REFERENCE.md); il dubbio da sciogliere e' se sia
 * anche quel che tiene la consegna sotto il ridisegno del compositore. */
static gboolean cadenza_fissa = FALSE;

static const struct spa_pod *formato_memoria(struct spa_pod_builder *c, uint32_t w, uint32_t h,
                                             uint32_t fps, uint32_t colore)
{
	struct spa_rectangle misura = SPA_RECTANGLE(w, h);
	struct spa_fraction cadenza = SPA_FRACTION(cadenza_fissa ? (fps > 0 ? fps : 1) : 0, 1);
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
	struct spa_fraction cadenza = SPA_FRACTION(cadenza_fissa ? (fps > 0 ? fps : 1) : 0, 1);
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
 *  Il monitor virtuale di Mutter — §7.3 di REFERENCE.md, senza permute
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

/* Non si usa mai g_bus_get_sync sul bus di sessione: GIO vi tiene acceso
 * `exit-on-close` e ci ammazza al logout.  §7.4 di REFERENCE.md. */
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
			g_prefix_error(sbaglio, "Mutter non espone RemoteDesktop (c'e' una sessione?): ");
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

	/* La cattura si registra sul controllo NON ancora avviato. */
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

	/* Ci si mette in ascolto PRIMA di Start: l'annuncio del nodo arriva
	 * durante la chiamata, e chi si iscrive dopo aspetta per sempre. */
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
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT, "nessun nodo PipeWire annunciato");
		goto guasto;
	}
	fprintf(stderr, "  monitor virtuale %ux%u montato, nodo PipeWire %u\n", larghezza, altezza,
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
 *  Il programma
 * ------------------------------------------------------------------ */

static int confronta_int(const void *a, const void *b)
{
	gint32 x = *(const gint32 *) a, y = *(const gint32 *) b;

	return x < y ? -1 : x > y ? 1 : 0;
}

int main(int argc, char **argv)
{
	uint32_t larghezza = 1920, altezza = 1080, fps = 60, nodo = 0;
	double durata = 20.0, scarto = 4.0;
	gboolean vuole_dmabuf = FALSE, usa_mutter = FALSE;
	uint32_t colore = SPA_VIDEO_FORMAT_BGRx;
	const char *etichetta = "senza-nome";
	Misura m = { 0 };
	Palco *palco = NULL;
	uint8_t spazio[2048];
	struct spa_pod_builder costruttore = SPA_POD_BUILDER_INIT(spazio, sizeof spazio);
	const struct spa_pod *parametri[2];
	uint32_t n_parametri = 0;
	g_autoptr(GError) sbaglio = NULL;
	gint64 scadenza;
	double secondi, fps_misurati;
	const char *nome_tipo;
	int i;

	for (i = 1; i < argc; i++)
	{
		if (!strcmp(argv[i], "--mutter"))
			usa_mutter = TRUE;
		else if (!strcmp(argv[i], "--nodo") && i + 1 < argc)
			nodo = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--larghezza") && i + 1 < argc)
			larghezza = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--altezza") && i + 1 < argc)
			altezza = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--fps") && i + 1 < argc)
			fps = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--durata") && i + 1 < argc)
			durata = atof(argv[++i]);
		else if (!strcmp(argv[i], "--scarto") && i + 1 < argc)
			scarto = atof(argv[++i]);
		else if (!strcmp(argv[i], "--dmabuf"))
			vuole_dmabuf = TRUE;
		else if (!strcmp(argv[i], "--bgra"))
			colore = SPA_VIDEO_FORMAT_BGRA;
		else if (!strcmp(argv[i], "--fissa"))
			cadenza_fissa = TRUE;
		else if (!strcmp(argv[i], "--etichetta") && i + 1 < argc)
			etichetta = argv[++i];
		else
		{
			fprintf(stderr,
			        "uso: %s [--mutter | --nodo N] [--larghezza W] [--altezza H] [--fps N]\n"
			        "        [--durata S] [--scarto S] [--dmabuf] [--bgra] [--etichetta T]\n",
			        argv[0]);
			return 2;
		}
	}
	if (!usa_mutter && nodo == 0)
	{
		fprintf(stderr, "serve --mutter oppure --nodo N\n");
		return 2;
	}

	m.vuole_dmabuf = vuole_dmabuf;
	m.intervalli = g_new0(gint32, INTERVALLI_MAX);

	fprintf(stderr, "== %s: %ux%u, %s, tetto dichiarato %u fps, %s ==\n", etichetta, larghezza,
	        altezza, colore == SPA_VIDEO_FORMAT_BGRx ? "BGRx" : "BGRA", fps,
	        vuole_dmabuf ? "DMA-BUF" : "memoria");

	if (usa_mutter)
	{
		palco = palco_monta(larghezza, altezza, &sbaglio);
		if (!palco)
		{
			fprintf(stderr, "monitor virtuale non montato: %s\n", sbaglio->message);
			return 1;
		}
		nodo = palco->nodo;
	}

	pw_init(NULL, NULL);
	m.ciclo = pw_thread_loop_new("misura", NULL);
	m.contesto = pw_context_new(pw_thread_loop_get_loop(m.ciclo), NULL, 0);
	pw_thread_loop_lock(m.ciclo);
	if (pw_thread_loop_start(m.ciclo) < 0)
	{
		fprintf(stderr, "thread PipeWire non avviato\n");
		return 1;
	}
	m.nucleo = pw_context_connect(m.contesto, NULL, 0);
	if (!m.nucleo)
	{
		pw_thread_loop_unlock(m.ciclo);
		fprintf(stderr, "connessione a PipeWire fallita\n");
		return 1;
	}
	m.flusso = pw_stream_new(m.nucleo, "misura-cattura",
	                         pw_properties_new(PW_KEY_MEDIA_TYPE, "Video", PW_KEY_MEDIA_CATEGORY,
	                                           "Capture", PW_KEY_MEDIA_ROLE, "Screen", NULL));
	pw_stream_add_listener(m.flusso, &m.gancio, &eventi, &m);

	if (vuole_dmabuf)
		parametri[n_parametri++] = formato_dmabuf(&costruttore, larghezza, altezza, fps, colore);
	parametri[n_parametri++] = formato_memoria(&costruttore, larghezza, altezza, fps, colore);

	if (pw_stream_connect(m.flusso, PW_DIRECTION_INPUT, nodo,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parametri, n_parametri) < 0)
	{
		pw_thread_loop_unlock(m.ciclo);
		fprintf(stderr, "aggancio al nodo %u fallito\n", nodo);
		return 1;
	}
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_S * G_USEC_PER_SEC;
	while (m.stato != PW_STREAM_STATE_PAUSED && m.stato != PW_STREAM_STATE_STREAMING &&
	       m.stato != PW_STREAM_STATE_ERROR && g_get_monotonic_time() < scadenza)
		pw_thread_loop_timed_wait(m.ciclo, 1);
	pw_thread_loop_unlock(m.ciclo);

	if (m.stato == PW_STREAM_STATE_ERROR)
	{
		fprintf(stderr, "cattura rifiutata: %s\n", m.guasto ? m.guasto : "senza spiegazione");
		palco_smonta(palco);
		return 1;
	}

	m.t_scarto = g_get_monotonic_time() + (gint64) (scarto * G_USEC_PER_SEC);
	m.fine = m.t_scarto + (gint64) (durata * G_USEC_PER_SEC);
	while (g_get_monotonic_time() < m.fine)
		g_usleep(50000);

	/*
	 * ⛔ ZERO FOTOGRAMMI NON E' LA STESSA COSA DI «NON HO MAI GUARDATO».
	 *
	 * Aggiunto il 9 agosto 2026, alla certificazione del banco della fase 0, e
	 * il difetto e' stato trovato dal controllo C3: puntando questo programma su
	 * un nodo che NON ESISTE rispondeva
	 *
	 *     fotogrammi 0 in 0.00 s  →  0.00 al secondo        (uscita 0)
	 *
	 * cioe' esattamente quel che risponde una scena ferma, che e' un risultato
	 * legittimo.  Due cose opposte sotto la stessa faccia: `LEZIONI.md` §1.9,
	 * «una misura che puo' dire zero deve poter distinguere lo zero dal
	 * fallimento», e la domanda 4 che `REVIEWER.md` §1 fa a ogni banco.
	 *
	 * ⚠ E il difetto era nello strumento che deve certificare tutti gli altri:
	 *   un solo giro andato storto — un nodo sbagliato, un permesso negato, il
	 *   compositore non ancora in piedi — sarebbe entrato in una tabella come
	 *   «il compositore non consegna niente».
	 *
	 * Il discrimine e' `t_inizio`, che si scrive quando il flusso diventa
	 * ATTIVO: la scena ferma ci arriva e consegna zero; il nodo inesistente non
	 * ci arriva mai.  In quel caso non si stampa nessuna RIGA — una riga di
	 * misura che non e' una misura e' peggio di nessuna riga — ma un GUASTO, e
	 * si esce con 2.
	 */
	if (m.t_inizio == 0)
	{
		printf("GUASTO\t%s\tflusso mai attivo\n", etichetta);
		fprintf(stderr,
		        "⛔ FALLITO (non «zero»): il flusso non e' mai diventato attivo.\n"
		        "   stato finale: %d%s%s\n"
		        "   Non c'e' nessun numero da leggere qui: la cattura non e' mai\n"
		        "   cominciata.  Zero fotogrammi si dichiara solo se il flusso e'\n"
		        "   stato attivo davvero (LEZIONI.md §1.9).\n",
		        (int) m.stato, m.guasto ? ", guasto: " : "", m.guasto ? m.guasto : "");
		palco_smonta(palco);
		return 2;
	}

	/* --- il conto ---------------------------------------------------- */
	secondi = m.contati > 1 ? (double) (m.t_ultimo - m.t_primo) / G_USEC_PER_SEC : 0.0;
	fps_misurati = secondi > 0.1 ? (double) (m.contati - 1) / secondi : 0.0;
	nome_tipo = m.tipo_dati == SPA_DATA_DmaBuf    ? "DMA-BUF"
	            : m.tipo_dati == SPA_DATA_MemFd   ? "MemFd"
	            : m.tipo_dati == SPA_DATA_MemPtr  ? "MemPtr"
	                                              : "?";

	{
		gint32 p50 = 0, p95 = 0, massimo = 0, minimo = 0;

		if (m.n_intervalli > 0)
		{
			qsort(m.intervalli, m.n_intervalli, sizeof(gint32), confronta_int);
			minimo = m.intervalli[0];
			p50 = m.intervalli[m.n_intervalli / 2];
			p95 = m.intervalli[(m.n_intervalli * 95) / 100];
			massimo = m.intervalli[m.n_intervalli - 1];
		}

		printf("RIGA\t%s\t%ux%u\t%s\t%u\t%s\t%s\t%.2f\t%" PRIu64 "\t%.2f\t%u\t%" PRIu64
		       "\t%" PRIu64 "\t%" PRIu64 "\t%" PRIu64 "\t%" PRIu64 "\t%.1f\t%.1f\t%.1f\t%.1f\n",
		       etichetta, larghezza, altezza,
		       colore == SPA_VIDEO_FORMAT_BGRx ? "BGRx" : "BGRA", fps,
		       vuole_dmabuf ? "dmabuf" : "memoria", nome_tipo, fps_misurati, m.contati, secondi,
		       m.quanti_fd, m.danno_pieno, m.danno_parziale, m.danno_assente, m.salti_seq,
		       m.fence_non_pronta, minimo / 1000.0, p50 / 1000.0, p95 / 1000.0, massimo / 1000.0);

		fprintf(stderr,
		        "  fotogrammi %" PRIu64 " in %.2f s  →  %.2f al secondo\n"
		        "  buffer: %s, %u distinti, stride %u\n"
		        "  danno: pieno %" PRIu64 ", parziale %" PRIu64 ", assente %" PRIu64 "\n"
		        "  salti di sequenza %" PRIu64 ", disegno non finito %" PRIu64 "\n"
		        "  intervalli ms: min %.1f  mediana %.1f  p95 %.1f  max %.1f\n",
		        m.contati, secondi, fps_misurati, nome_tipo, m.quanti_fd, m.stride, m.danno_pieno,
		        m.danno_parziale, m.danno_assente, m.salti_seq, m.fence_non_pronta, minimo / 1000.0,
		        p50 / 1000.0, p95 / 1000.0, massimo / 1000.0);
	}

	pw_thread_loop_lock(m.ciclo);
	pw_stream_disconnect(m.flusso);
	pw_stream_destroy(m.flusso);
	pw_thread_loop_unlock(m.ciclo);
	pw_thread_loop_stop(m.ciclo);
	pw_core_disconnect(m.nucleo);
	pw_context_destroy(m.contesto);
	pw_thread_loop_destroy(m.ciclo);
	palco_smonta(palco);
	g_free(m.intervalli);
	g_free(m.guasto);
	return 0;
}
