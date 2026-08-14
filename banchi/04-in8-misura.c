/*
 * misura.c — banco di STUDIO F4-IN-8: che misura accetta Mutter per un monitor
 * virtuale di `RecordVirtual`, e che cosa succede se ne chiediamo una strana.
 *
 * ⛔ Non tocca `src/`: e' un file a se', si compila da solo.
 *
 *   misura <L> <A> [<L2> <A2>] [secondi]
 *
 * Fa la sequenza di `src/mutter.c` (RemoteDesktop + ScreenCast + RecordVirtual),
 * poi apre un flusso PipeWire chiedendo la misura ESATTA <L>x<A> (rettangolo
 * fisso, non intervallo), e STAMPA:
 *
 *   - la misura che PipeWire ha concordato (quella vera dei pixel);
 *   - lo stato del monitor secondo Mutter (DisplayConfig.GetCurrentState):
 *     modo corrente e SCALA del monitor logico;
 *   - se sono dati <L2> <A2>: rifa' `pw_stream_update_params` a sessione aperta
 *     e misura il BUCO fra l'ultimo fotogramma vecchio e il primo nuovo.
 */
#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include <pipewire/pipewire.h>
#include <spa/param/video/format-utils.h>
#include <spa/param/props.h>
#include <spa/buffer/meta.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define NOME_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define PERCORSO_REMOTE "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_REMOTE_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"
#define NOME_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define PERCORSO_SCREENCAST "/org/gnome/Mutter/ScreenCast"
#define IFACE_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define IFACE_SC_SESSIONE "org.gnome.Mutter.ScreenCast.Session"
#define IFACE_SC_FLUSSO "org.gnome.Mutter.ScreenCast.Stream"
#define NOME_DISPLAY "org.gnome.Mutter.DisplayConfig"
#define PERCORSO_DISPLAY "/org/gnome/Mutter/DisplayConfig"
#define IFACE_DISPLAY "org.gnome.Mutter.DisplayConfig"

static GDBusConnection *bus;
static char *p_controllo, *p_cattura, *p_flusso;
static uint32_t nodo;

static gint64 ora(void) { return g_get_monotonic_time(); }

static GVariant *chiama(const char *nome, const char *percorso, const char *iface,
                        const char *metodo, GVariant *args, const GVariantType *ris)
{
	GError *e = NULL;
	GVariant *r = g_dbus_connection_call_sync(bus, nome, percorso, iface, metodo, args, ris,
	                                          G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &e);
	if (!r) {
		fprintf(stderr, "⛔ %s.%s: %s\n", iface, metodo, e->message);
		g_clear_error(&e);
	}
	return r;
}

static void su_nodo(GDBusConnection *b, const char *m, const char *p, const char *i,
                    const char *s, GVariant *par, gpointer d)
{
	if (g_variant_is_of_type(par, G_VARIANT_TYPE("(u)")))
		g_variant_get(par, "(u)", (uint32_t *) d);
}
static gboolean sveglia(gpointer d) { return G_SOURCE_CONTINUE; }

/* ---- lo stato dei monitor secondo Mutter ------------------------------ */
static void stampa_stato(const char *quando)
{
	GVariant *r = chiama(NOME_DISPLAY, PERCORSO_DISPLAY, IFACE_DISPLAY, "GetCurrentState",
	                     NULL, NULL);
	GVariant *monitors, *logicals;
	GVariantIter it;
	if (!r) return;

	printf("\n== stato dei monitor (%s) ==\n", quando);
	monitors = g_variant_get_child_value(r, 1);
	logicals = g_variant_get_child_value(r, 2);

	{
		GVariant *m;
		g_variant_iter_init(&it, monitors);
		while ((m = g_variant_iter_next_value(&it))) {
			GVariant *spec = g_variant_get_child_value(m, 0);
			GVariant *modi = g_variant_get_child_value(m, 1);
			const char *conn = NULL, *ven = NULL, *pro = NULL, *ser = NULL;
			GVariantIter mi;
			GVariant *mo;
			g_variant_get(spec, "(&s&s&s&s)", &conn, &ven, &pro, &ser);
			g_variant_iter_init(&mi, modi);
			while ((mo = g_variant_iter_next_value(&mi))) {
				const char *id;
				int w, h;
				double rr, pref;
				GVariant *scale_supp, *props;
				gboolean corrente = FALSE, preferito = FALSE;
				GVariant *v;
				g_variant_get(mo, "(&siidd@ad@a{sv})", &id, &w, &h, &rr, &pref,
				              &scale_supp, &props);
				v = g_variant_lookup_value(props, "is-current", G_VARIANT_TYPE_BOOLEAN);
				if (v) { corrente = g_variant_get_boolean(v); g_variant_unref(v); }
				v = g_variant_lookup_value(props, "is-preferred", G_VARIANT_TYPE_BOOLEAN);
				if (v) { preferito = g_variant_get_boolean(v); g_variant_unref(v); }
				if (corrente) {
					gsize n = 0;
					const gdouble *ss = g_variant_get_fixed_array(scale_supp, &n,
					                                              sizeof(gdouble));
					printf("  monitor %-10s «%s» modo %s  %dx%d @%.2f  pref=%d  "
					       "scale ammesse:", conn, pro, id, w, h, rr, preferito);
					for (gsize k = 0; k < n; k++) printf(" %.4f", ss[k]);
					printf("\n");
				}
				g_variant_unref(scale_supp);
				g_variant_unref(props);
				g_variant_unref(mo);
			}
			g_variant_unref(spec);
			g_variant_unref(modi);
			g_variant_unref(m);
		}
	}
	{
		GVariant *l;
		g_variant_iter_init(&it, logicals);
		while ((l = g_variant_iter_next_value(&it))) {
			int x, y;
			double scala;
			guint trasf;
			gboolean primario;
			GVariant *mons, *props;
			GVariantIter mi;
			GVariant *ms;
			g_variant_get(l, "(iidub@a(ssss)@a{sv})", &x, &y, &scala, &trasf, &primario,
			              &mons, &props);
			printf("  LOGICO  a (%d,%d)  SCALA %.6f  trasf %u  primario %d  ->", x, y,
			       scala, trasf, primario);
			g_variant_iter_init(&mi, mons);
			while ((ms = g_variant_iter_next_value(&mi))) {
				const char *c, *v2, *p2, *s2;
				g_variant_get(ms, "(&s&s&s&s)", &c, &v2, &p2, &s2);
				printf(" %s(«%s»)", c, p2);
				g_variant_unref(ms);
			}
			printf("\n");
			g_variant_unref(mons);
			g_variant_unref(props);
			g_variant_unref(l);
		}
	}
	g_variant_unref(monitors);
	g_variant_unref(logicals);
	g_variant_unref(r);
	fflush(stdout);
}

/* ---- il flusso PipeWire ---------------------------------------------- */
struct banco {
	struct pw_main_loop *loop;
	struct pw_stream *flusso;
	struct spa_hook ascolto;
	struct spa_video_info_raw formato;
	uint32_t chiesta_l, chiesta_a;
	uint32_t nuova_l, nuova_a;
	gint64 t0;
	gint64 t_richiesta_2;   /* quando ho chiesto la misura nuova */
	gint64 t_ultimo_vecchio;
	int fotogrammi;
	int fotogrammi_dopo;
	int fase;               /* 0 = prima misura, 1 = ho chiesto la seconda */
	int secondi;
};
static struct banco B;

static const struct spa_pod *proposta(struct spa_pod_builder *b, uint32_t l, uint32_t a)
{
	struct spa_rectangle misura = SPA_RECTANGLE(l, a);
	struct spa_fraction cad = SPA_FRACTION(0, 1);
	struct spa_fraction cmin = SPA_FRACTION(1, 1);
	struct spa_fraction cmax = SPA_FRACTION(60, 1);
	return spa_pod_builder_add_object(
	    b, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat, SPA_FORMAT_mediaType,
	    SPA_POD_Id(SPA_MEDIA_TYPE_video), SPA_FORMAT_mediaSubtype,
	    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), SPA_FORMAT_VIDEO_format,
	    SPA_POD_Id(SPA_VIDEO_FORMAT_BGRx), SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&misura),
	    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cad), SPA_FORMAT_VIDEO_maxFramerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&cmax, &cmin, &cmax));
}

static int raffica_quante, raffica_fatte, raffica_concordate;

static void su_parametri(void *d, uint32_t id, const struct spa_pod *param)
{
	uint8_t sp[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(sp, sizeof sp);
	const struct spa_pod *par[2];

	if (!param || id != SPA_PARAM_Format) return;
	if (spa_format_video_raw_parse(param, &B.formato) < 0) return;

	printf("[%6.3f s] FORMATO CONCORDATO: %ux%u  (chiesto %ux%u)  %s\n",
	       (ora() - B.t0) / 1e6, B.formato.size.width, B.formato.size.height,
	       B.fase == 0 ? B.chiesta_l : B.nuova_l, B.fase == 0 ? B.chiesta_a : B.nuova_a,
	       (B.formato.size.width == (B.fase == 0 ? B.chiesta_l : B.nuova_l) &&
	        B.formato.size.height == (B.fase == 0 ? B.chiesta_a : B.nuova_a))
	           ? "⭐ ESATTO"
	           : "⛔ DIVERSO — arrotondato in silenzio");
	if (B.fase == 1 && B.formato.size.width == B.nuova_l && B.formato.size.height == B.nuova_a)
		raffica_concordate++;
	fflush(stdout);

	par[0] = spa_pod_builder_add_object(
	    &b, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
	    SPA_POD_CHOICE_RANGE_Int(4, 2, 8), SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int(1 << SPA_DATA_MemFd));
	par[1] = spa_pod_builder_add_object(&b, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta,
	                                    SPA_PARAM_META_type, SPA_POD_Id(SPA_META_Header),
	                                    SPA_PARAM_META_size,
	                                    SPA_POD_Int(sizeof(struct spa_meta_header)));
	pw_stream_update_params(B.flusso, par, 2);
}

static void su_stato(void *d, enum pw_stream_state vecchio, enum pw_stream_state nuovo,
                     const char *errore)
{
	printf("[%6.3f s] stato: %s -> %s%s%s\n", (ora() - B.t0) / 1e6,
	       pw_stream_state_as_string(vecchio), pw_stream_state_as_string(nuovo),
	       errore ? "  errore: " : "", errore ? errore : "");
	fflush(stdout);
	if (nuovo == PW_STREAM_STATE_ERROR) pw_main_loop_quit(B.loop);
}

/*
 * ⭐ LA DOMANDA VERA: il desktop dipinge TUTTA la superficie strana, o ne
 *    dipinge un pezzo e lascia bande nere?  Si guarda una griglia 8x4 di
 *    luminanza media, piu' l'ULTIMA colonna e l'ULTIMA riga separate — che sono
 *    il posto dove una banda nera si vedrebbe.
 */
static void griglia(const uint8_t *dati, uint32_t l, uint32_t a, int passo)
{
	const int GX = 8, GY = 4;
	uint64_t somma[4][8];
	uint64_t conta[4][8];
	uint64_t ultima_col = 0, ultima_rig = 0, non_nero = 0, totale = 0;
	uint32_t x, y;
	int i, j;

	memset(somma, 0, sizeof somma);
	memset(conta, 0, sizeof conta);
	for (y = 0; y < a; y++) {
		const uint8_t *r = dati + (size_t) y * passo;
		for (x = 0; x < l; x++) {
			const uint8_t *p = r + (size_t) x * 4;
			unsigned v = (p[0] + p[1] + p[2]) / 3;
			int gy = (int) ((uint64_t) y * GY / a), gx = (int) ((uint64_t) x * GX / l);
			somma[gy][gx] += v;
			conta[gy][gx]++;
			totale++;
			if (v > 8) non_nero++;
			if (x >= l - 4) ultima_col += v;
			if (y >= a - 4) ultima_rig += v;
		}
	}
	printf("  pixel non neri: %.2f%%   ultime 4 colonne: luminanza media %.1f   "
	       "ultime 4 righe: %.1f\n",
	       100.0 * non_nero / (double) totale, ultima_col / (double) (4.0 * a),
	       ultima_rig / (double) (4.0 * l));
	for (i = 0; i < GY; i++) {
		printf("  griglia:");
		for (j = 0; j < GX; j++)
			printf(" %5.1f", conta[i][j] ? somma[i][j] / (double) conta[i][j] : -1.0);
		printf("\n");
	}
}

static void su_processo(void *d)
{
	struct pw_buffer *b = pw_stream_dequeue_buffer(B.flusso);
	if (!b) return;
	if (b->buffer->datas[0].chunk->size > 0 && b->buffer->datas[0].data &&
	    ((B.fase == 0 && B.fotogrammi == 0) || (B.fase == 1 && B.fotogrammi_dopo == 0)))
		griglia((const uint8_t *) b->buffer->datas[0].data, B.formato.size.width,
		        B.formato.size.height, b->buffer->datas[0].chunk->stride);
	if (b->buffer->datas[0].chunk->size > 0) {
		if (B.fase == 0) {
			B.fotogrammi++;
			B.t_ultimo_vecchio = ora();
			if (B.fotogrammi <= 3)
				printf("[%6.3f s] fotogramma %d: %u byte, passo %d\n",
				       (ora() - B.t0) / 1e6, B.fotogrammi,
				       b->buffer->datas[0].chunk->size,
				       b->buffer->datas[0].chunk->stride);
		} else {
			B.fotogrammi_dopo++;
			if (B.fotogrammi_dopo <= 3)
				printf("[%6.3f s] fotogramma NUOVO %d: %u byte, passo %d  "
				       "(buco dalla richiesta: %.1f ms; dall'ultimo vecchio: %.1f ms)\n",
				       (ora() - B.t0) / 1e6, B.fotogrammi_dopo,
				       b->buffer->datas[0].chunk->size,
				       b->buffer->datas[0].chunk->stride,
				       (ora() - B.t_richiesta_2) / 1000.0,
				       (ora() - B.t_ultimo_vecchio) / 1000.0);
		}
	}
	pw_stream_queue_buffer(B.flusso, b);
	fflush(stdout);
}

static const struct pw_stream_events eventi = {
    PW_VERSION_STREAM_EVENTS,
    .state_changed = su_stato,
    .param_changed = su_parametri,
    .process = su_processo,
};

/* ⭐ LA RAFFICA: venti misure diverse in due secondi, come farebbe una finestra
 *    di browser trascinata.  Domanda: Mutter regge, o si perde per strada? */
static void alla_raffica(void *d, uint64_t espirazioni)
{
	uint8_t sp[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(sp, sizeof sp);
	const struct spa_pod *par[1];
	uint32_t l, a;

	if (raffica_fatte >= raffica_quante) return;
	l = 1201 + (uint32_t) raffica_fatte * 37;
	a = 801 + (uint32_t) raffica_fatte * 13;
	B.nuova_l = l;
	B.nuova_a = a;
	B.fase = 1;
	raffica_fatte++;
	par[0] = proposta(&b, l, a);
	pw_stream_update_params(B.flusso, par, 1);
}

static void al_tempo(void *d, uint64_t espirazioni)
{
	static int passo = 0;
	uint8_t sp[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(sp, sizeof sp);
	const struct spa_pod *par[1];

	passo++;
	if (passo == 1) {
		printf("\n[%6.3f s] === dopo %d s: %d fotogrammi alla prima misura ===\n",
		       (ora() - B.t0) / 1e6, B.secondi, B.fotogrammi);
		stampa_stato("prima misura");
		if (raffica_quante > 0) {
			printf("[%6.3f s] raffica: %d chieste, %d concordate ESATTE\n",
			       (ora() - B.t0) / 1e6, raffica_fatte, raffica_concordate);
			return;
		}
		if (B.nuova_l == 0) { pw_main_loop_quit(B.loop); return; }
		printf("\n[%6.3f s] === CAMBIO A CALDO: chiedo %ux%u ===\n", (ora() - B.t0) / 1e6,
		       B.nuova_l, B.nuova_a);
		B.fase = 1;
		B.t_richiesta_2 = ora();
		par[0] = proposta(&b, B.nuova_l, B.nuova_a);
		pw_stream_update_params(B.flusso, par, 1);
	} else if (passo == 2) {
		printf("\n[%6.3f s] === dopo il cambio: %d fotogrammi nuovi ===\n",
		       (ora() - B.t0) / 1e6, B.fotogrammi_dopo);
		if (raffica_quante > 0)
			printf("[%6.3f s] raffica FINALE: %d chieste, %d concordate ESATTE\n",
			       (ora() - B.t0) / 1e6, raffica_fatte, raffica_concordate);
		stampa_stato("seconda misura");
		pw_main_loop_quit(B.loop);
	}
	fflush(stdout);
}

int main(int argc, char **argv)
{
	GError *e = NULL;
	GVariantBuilder pr;
	GVariant *r;
	uint8_t sp[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(sp, sizeof sp);
	const struct spa_pod *par[1];
	struct pw_context *ctx;
	struct pw_core *core;
	struct spa_source *tempo;
	struct timespec quando, intervallo;
	char nodo_s[32];

	if (argc < 3) {
		fprintf(stderr, "uso: %s <L> <A> [<L2> <A2>] [secondi]\n", argv[0]);
		return 2;
	}
	B.chiesta_l = (uint32_t) atoi(argv[1]);
	B.chiesta_a = (uint32_t) atoi(argv[2]);
	if (argc >= 5 && strcmp(argv[3], "raffica") == 0) {
		raffica_quante = atoi(argv[4]);
	} else if (argc >= 5) {
		B.nuova_l = (uint32_t) atoi(argv[3]);
		B.nuova_a = (uint32_t) atoi(argv[4]);
	}
	B.secondi = (argc >= 6) ? atoi(argv[5]) : (argc == 4 ? atoi(argv[3]) : 4);
	if (B.secondi <= 0) B.secondi = 4;
	B.t0 = ora();

	bus = g_bus_get_sync(G_BUS_TYPE_SESSION, NULL, &e);
	if (!bus) { fprintf(stderr, "⛔ bus: %s\n", e->message); return 3; }

	stampa_stato("PRIMA di tutto");

	r = chiama(NOME_REMOTE, PERCORSO_REMOTE, IFACE_REMOTE, "CreateSession", NULL,
	           G_VARIANT_TYPE("(o)"));
	if (!r) return 4;
	g_variant_get(r, "(o)", &p_controllo);
	g_variant_unref(r);

	g_variant_builder_init(&pr, G_VARIANT_TYPE("a{sv}"));
	{
		GVariant *idv = chiama(NOME_REMOTE, p_controllo, "org.freedesktop.DBus.Properties",
		                       "Get",
		                       g_variant_new("(ss)", IFACE_REMOTE_SESSIONE, "SessionId"),
		                       G_VARIANT_TYPE("(v)"));
		GVariant *inner = NULL;
		const char *id = NULL;
		if (!idv) return 5;
		g_variant_get(idv, "(v)", &inner);
		id = g_variant_get_string(inner, NULL);
		g_variant_builder_add(&pr, "{sv}", "remote-desktop-session-id",
		                      g_variant_new_string(id));
		g_variant_unref(inner);
		g_variant_unref(idv);
	}
	g_variant_builder_add(&pr, "{sv}", "disable-animations", g_variant_new_boolean(TRUE));
	r = chiama(NOME_SCREENCAST, PERCORSO_SCREENCAST, IFACE_SCREENCAST, "CreateSession",
	           g_variant_new("(a{sv})", &pr), G_VARIANT_TYPE("(o)"));
	if (!r) return 6;
	g_variant_get(r, "(o)", &p_cattura);
	g_variant_unref(r);

	r = chiama(NOME_REMOTE, p_controllo, IFACE_REMOTE_SESSIONE, "Start", NULL, NULL);
	if (!r) return 7;
	g_variant_unref(r);

	g_variant_builder_init(&pr, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&pr, "{sv}", "cursor-mode", g_variant_new_uint32(2));
	g_variant_builder_add(&pr, "{sv}", "is-platform", g_variant_new_boolean(TRUE));
	r = chiama(NOME_SCREENCAST, p_cattura, IFACE_SC_SESSIONE, "RecordVirtual",
	           g_variant_new("(a{sv})", &pr), G_VARIANT_TYPE("(o)"));
	if (!r) return 8;
	g_variant_get(r, "(o)", &p_flusso);
	g_variant_unref(r);
	printf("flusso: %s\n", p_flusso);

	{
		GMainContext *c = g_main_context_new();
		GSource *bat;
		gint64 sc;
		g_main_context_push_thread_default(c);
		g_dbus_connection_signal_subscribe(bus, NULL, IFACE_SC_FLUSSO,
		                                   "PipeWireStreamAdded", p_flusso, NULL,
		                                   G_DBUS_SIGNAL_FLAGS_NONE, su_nodo, &nodo, NULL);
		r = chiama(NOME_SCREENCAST, p_flusso, IFACE_SC_FLUSSO, "Start", NULL, NULL);
		if (!r) return 9;
		g_variant_unref(r);
		bat = g_timeout_source_new(50);
		g_source_set_callback(bat, sveglia, NULL, NULL);
		g_source_attach(bat, c);
		sc = ora() + 5000000;
		while (nodo == 0 && ora() < sc) g_main_context_iteration(c, TRUE);
		g_main_context_pop_thread_default(c);
	}
	if (!nodo) { fprintf(stderr, "⛔ nessun nodo\n"); return 10; }
	printf("nodo PipeWire: %u\n", nodo);
	fflush(stdout);

	pw_init(NULL, NULL);
	B.loop = pw_main_loop_new(NULL);
	ctx = pw_context_new(pw_main_loop_get_loop(B.loop), NULL, 0);
	core = pw_context_connect(ctx, NULL, 0);
	if (!core) { fprintf(stderr, "⛔ PipeWire non risponde\n"); return 11; }

	snprintf(nodo_s, sizeof nodo_s, "%u", nodo);
	B.flusso = pw_stream_new(core, "misura-f4in8",
	                         pw_properties_new(PW_KEY_MEDIA_TYPE, "Video", PW_KEY_MEDIA_CATEGORY,
	                                           "Capture", PW_KEY_MEDIA_ROLE, "Screen", NULL));
	pw_stream_add_listener(B.flusso, &B.ascolto, &eventi, NULL);
	par[0] = proposta(&b, B.chiesta_l, B.chiesta_a);
	if (pw_stream_connect(B.flusso, PW_DIRECTION_INPUT, nodo,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS, par, 1) < 0) {
		fprintf(stderr, "⛔ pw_stream_connect\n");
		return 12;
	}

	if (raffica_quante > 0) {
		struct spa_source *t2 = pw_loop_add_timer(pw_main_loop_get_loop(B.loop),
		                                          alla_raffica, NULL);
		struct timespec q = {0, 300000000}, iv = {0, 100000000};
		pw_loop_update_timer(pw_main_loop_get_loop(B.loop), t2, &q, &iv, false);
	}
	tempo = pw_loop_add_timer(pw_main_loop_get_loop(B.loop), al_tempo, NULL);
	quando.tv_sec = B.secondi;
	quando.tv_nsec = 0;
	intervallo.tv_sec = B.secondi;
	intervallo.tv_nsec = 0;
	pw_loop_update_timer(pw_main_loop_get_loop(B.loop), tempo, &quando, &intervallo, false);

	pw_main_loop_run(B.loop);

	printf("\n== riepilogo ==\n  chiesti %ux%u -> ottenuti %ux%u, %d fotogrammi\n",
	       B.chiesta_l, B.chiesta_a, B.formato.size.width, B.formato.size.height, B.fotogrammi);
	if (B.nuova_l)
		printf("  poi chiesti %ux%u -> %d fotogrammi nuovi\n", B.nuova_l, B.nuova_a,
		       B.fotogrammi_dopo);
	pw_stream_destroy(B.flusso);
	pw_context_destroy(ctx);
	pw_main_loop_destroy(B.loop);

	chiama(NOME_SCREENCAST, p_cattura, IFACE_SC_SESSIONE, "Stop", NULL, NULL);
	chiama(NOME_REMOTE, p_controllo, IFACE_REMOTE_SESSIONE, "Stop", NULL, NULL);
	return 0;
}
