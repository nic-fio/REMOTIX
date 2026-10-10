/*
 * misura.c — STUDY bench F4-IN-8: which size Mutter accepts for a virtual
 * monitor of `RecordVirtual`, and what happens if we ask for a strange one.
 *
 * ⛔ It does not touch `src/`: it is a file of its own, it compiles by itself.
 *
 *   gauge <L> <A> [<L2> <A2>] [seconds]
 *
 * Runs the sequence of `src/mutter.c` (RemoteDesktop + ScreenCast + RecordVirtual),
 * then opens a PipeWire stream asking for the EXACT size <L>x<A> (fixed
 * rectangle, not a range), and PRINTS:
 *
 *   - the size PipeWire agreed (the real one of the pixels);
 *   - the monitor state according to Mutter (DisplayConfig.GetCurrentState):
 *     current mode and SCALE of the logical monitor;
 *   - if <L2> <A2> are given: redoes `pw_stream_update_params` with the session
 *     open and measures the HOLE between the last old frame and the first new one.
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

#define REMOTE_NAME "org.gnome.Mutter.RemoteDesktop"
#define PATH_REMOTE "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_REMOTE_SESSION "org.gnome.Mutter.RemoteDesktop.Session"
#define SCREENCAST_NAME "org.gnome.Mutter.ScreenCast"
#define PATH_SCREENCAST "/org/gnome/Mutter/ScreenCast"
#define IFACE_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define IFACE_SC_SESSION "org.gnome.Mutter.ScreenCast.Session"
#define IFACE_SC_STREAM "org.gnome.Mutter.ScreenCast.Stream"
#define DISPLAY_NAME "org.gnome.Mutter.DisplayConfig"
#define PATH_DISPLAY "/org/gnome/Mutter/DisplayConfig"
#define IFACE_DISPLAY "org.gnome.Mutter.DisplayConfig"

static GDBusConnection *bus;
static char *p_check, *p_capture, *p_stream;
static uint32_t node;

static gint64 now(void) { return g_get_monotonic_time(); }

static GVariant *call(const char *label_name, const char *fpath, const char *iface,
                        const char *meth, GVariant *args, const GVariantType *result)
{
	GError *e = NULL;
	GVariant *r = g_dbus_connection_call_sync(bus, label_name, fpath, iface, meth, args, result,
	                                          G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &e);
	if (!r) {
		fprintf(stderr, "⛔ %s.%s: %s\n", iface, meth, e->message);
		g_clear_error(&e);
	}
	return r;
}

static void on_node(GDBusConnection *b, const char *m, const char *p, const char *i,
                    const char *s, GVariant *par, gpointer d)
{
	if (g_variant_is_of_type(par, G_VARIANT_TYPE("(u)")))
		g_variant_get(par, "(u)", (uint32_t *) d);
}
static gboolean wake(gpointer d) { return G_SOURCE_CONTINUE; }

/* ---- the state of the monitors according to Mutter ------------------- */
static void print_state(const char *when)
{
	GVariant *r = call(DISPLAY_NAME, PATH_DISPLAY, IFACE_DISPLAY, "GetCurrentState",
	                     NULL, NULL);
	GVariant *monitors, *logicals;
	GVariantIter it;
	if (!r) return;

	printf("\n== monitor state (%s) ==\n", when);
	monitors = g_variant_get_child_value(r, 1);
	logicals = g_variant_get_child_value(r, 2);

	{
		GVariant *m;
		g_variant_iter_init(&it, monitors);
		while ((m = g_variant_iter_next_value(&it))) {
			GVariant *spec = g_variant_get_child_value(m, 0);
			GVariant *modes = g_variant_get_child_value(m, 1);
			const char *conn = NULL, *ven = NULL, *pro = NULL, *ser = NULL;
			GVariantIter mi;
			GVariant *mo;
			g_variant_get(spec, "(&s&s&s&s)", &conn, &ven, &pro, &ser);
			g_variant_iter_init(&mi, modes);
			while ((mo = g_variant_iter_next_value(&mi))) {
				const char *id;
				int w, h;
				double rr, pref;
				GVariant *scale_supp, *props;
				gboolean current = FALSE, preferred = FALSE;
				GVariant *v;
				g_variant_get(mo, "(&siidd@ad@a{sv})", &id, &w, &h, &rr, &pref,
				              &scale_supp, &props);
				v = g_variant_lookup_value(props, "is-current", G_VARIANT_TYPE_BOOLEAN);
				if (v) { current = g_variant_get_boolean(v); g_variant_unref(v); }
				v = g_variant_lookup_value(props, "is-preferred", G_VARIANT_TYPE_BOOLEAN);
				if (v) { preferred = g_variant_get_boolean(v); g_variant_unref(v); }
				if (current) {
					gsize n = 0;
					const gdouble *ss = g_variant_get_fixed_array(scale_supp, &n,
					                                              sizeof(gdouble));
					printf("  monitor %-10s «%s» mode %s  %dx%d @%.2f  pref=%d  "
					       "allowed scales:", conn, pro, id, w, h, rr, preferred);
					for (gsize k = 0; k < n; k++) printf(" %.4f", ss[k]);
					printf("\n");
				}
				g_variant_unref(scale_supp);
				g_variant_unref(props);
				g_variant_unref(mo);
			}
			g_variant_unref(spec);
			g_variant_unref(modes);
			g_variant_unref(m);
		}
	}
	{
		GVariant *l;
		g_variant_iter_init(&it, logicals);
		while ((l = g_variant_iter_next_value(&it))) {
			int x, y;
			double scale_v;
			guint transform;
			gboolean primary;
			GVariant *mons, *props;
			GVariantIter mi;
			GVariant *ms;
			g_variant_get(l, "(iidub@a(ssss)@a{sv})", &x, &y, &scale_v, &transform, &primary,
			              &mons, &props);
			printf("  LOGICAL  at (%d,%d)  SCALE %.6f  transf %u  primary %d  ->", x, y,
			       scale_v, transform, primary);
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

/* ---- the PipeWire stream ---------------------------------------------- */
struct bench {
	struct pw_main_loop *loop;
	struct pw_stream *flow;
	struct spa_hook listen;
	struct spa_video_info_raw schema;
	uint32_t requested_w, requested_h;
	uint32_t new_w, new_h;
	gint64 t0;
	gint64 t_request_2;   /* when I asked for the new size */
	gint64 t_last_old;
	int frames;
	int frames_after;
	int phase;               /* 0 = first size, 1 = I asked for the second */
	int seconds;
};
static struct bench B;

static const struct spa_pod *proposal(struct spa_pod_builder *b, uint32_t l, uint32_t a)
{
	struct spa_rectangle gauge = SPA_RECTANGLE(l, a);
	struct spa_fraction cad = SPA_FRACTION(0, 1);
	struct spa_fraction cmin = SPA_FRACTION(1, 1);
	struct spa_fraction cmax = SPA_FRACTION(60, 1);
	return spa_pod_builder_add_object(
	    b, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat, SPA_FORMAT_mediaType,
	    SPA_POD_Id(SPA_MEDIA_TYPE_video), SPA_FORMAT_mediaSubtype,
	    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), SPA_FORMAT_VIDEO_format,
	    SPA_POD_Id(SPA_VIDEO_FORMAT_BGRx), SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&gauge),
	    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cad), SPA_FORMAT_VIDEO_maxFramerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&cmax, &cmin, &cmax));
}

static int burst_count, bursts_done, bursts_matched;

static void on_parameters(void *d, uint32_t id, const struct spa_pod *param)
{
	uint8_t sp[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(sp, sizeof sp);
	const struct spa_pod *par[2];

	if (!param || id != SPA_PARAM_Format) return;
	if (spa_format_video_raw_parse(param, &B.schema) < 0) return;

	printf("[%6.3f s] AGREED FORMAT: %ux%u  (asked %ux%u)  %s\n",
	       (now() - B.t0) / 1e6, B.schema.size.width, B.schema.size.height,
	       B.phase == 0 ? B.requested_w : B.new_w, B.phase == 0 ? B.requested_h : B.new_h,
	       (B.schema.size.width == (B.phase == 0 ? B.requested_w : B.new_w) &&
	        B.schema.size.height == (B.phase == 0 ? B.requested_h : B.new_h))
	           ? "⭐ EXACT"
	           : "⛔ DIFFERENT — rounded silently");
	if (B.phase == 1 && B.schema.size.width == B.new_w && B.schema.size.height == B.new_h)
		bursts_matched++;
	fflush(stdout);

	par[0] = spa_pod_builder_add_object(
	    &b, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
	    SPA_POD_CHOICE_RANGE_Int(4, 2, 8), SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int(1 << SPA_DATA_MemFd));
	par[1] = spa_pod_builder_add_object(&b, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta,
	                                    SPA_PARAM_META_type, SPA_POD_Id(SPA_META_Header),
	                                    SPA_PARAM_META_size,
	                                    SPA_POD_Int(sizeof(struct spa_meta_header)));
	pw_stream_update_params(B.flow, par, 2);
}

static void on_state(void *d, enum pw_stream_state prior, enum pw_stream_state fresh,
                     const char *failure)
{
	printf("[%6.3f s] state: %s -> %s%s%s\n", (now() - B.t0) / 1e6,
	       pw_stream_state_as_string(prior), pw_stream_state_as_string(fresh),
	       failure ? "  error: " : "", failure ? failure : "");
	fflush(stdout);
	if (fresh == PW_STREAM_STATE_ERROR) pw_main_loop_quit(B.loop);
}

/*
 * ⭐ THE REAL QUESTION: does the desktop paint the WHOLE strange surface, or
 *    does it paint a piece and leave black bands?  We look at an 8x4 grid of
 *    mean luminance, plus the LAST column and the LAST row separately — which are
 *    the place where a black band would show.
 */
static void grid(const uint8_t *data_v, uint32_t l, uint32_t a, int step)
{
	const int GX = 8, GY = 4;
	uint64_t total_sum[4][8];
	uint64_t tally[4][8];
	uint64_t last_col = 0, last_row = 0, non_black = 0, total = 0;
	uint32_t x, y;
	int i, j;

	memset(total_sum, 0, sizeof total_sum);
	memset(tally, 0, sizeof tally);
	for (y = 0; y < a; y++) {
		const uint8_t *r = data_v + (size_t) y * step;
		for (x = 0; x < l; x++) {
			const uint8_t *p = r + (size_t) x * 4;
			unsigned v = (p[0] + p[1] + p[2]) / 3;
			int gy = (int) ((uint64_t) y * GY / a), gx = (int) ((uint64_t) x * GX / l);
			total_sum[gy][gx] += v;
			tally[gy][gx]++;
			total++;
			if (v > 8) non_black++;
			if (x >= l - 4) last_col += v;
			if (y >= a - 4) last_row += v;
		}
	}
	printf("  non-black pixels: %.2f%%   last 4 columns: mean luminance %.1f   "
	       "last 4 rows: %.1f\n",
	       100.0 * non_black / (double) total, last_col / (double) (4.0 * a),
	       last_row / (double) (4.0 * l));
	for (i = 0; i < GY; i++) {
		printf("  grid:");
		for (j = 0; j < GX; j++)
			printf(" %5.1f", tally[i][j] ? total_sum[i][j] / (double) tally[i][j] : -1.0);
		printf("\n");
	}
}

static void on_process(void *d)
{
	struct pw_buffer *b = pw_stream_dequeue_buffer(B.flow);
	if (!b) return;
	if (b->buffer->datas[0].chunk->size > 0 && b->buffer->datas[0].data &&
	    ((B.phase == 0 && B.frames == 0) || (B.phase == 1 && B.frames_after == 0)))
		grid((const uint8_t *) b->buffer->datas[0].data, B.schema.size.width,
		        B.schema.size.height, b->buffer->datas[0].chunk->stride);
	if (b->buffer->datas[0].chunk->size > 0) {
		if (B.phase == 0) {
			B.frames++;
			B.t_last_old = now();
			if (B.frames <= 3)
				printf("[%6.3f s] frame %d: %u bytes, stride %d\n",
				       (now() - B.t0) / 1e6, B.frames,
				       b->buffer->datas[0].chunk->size,
				       b->buffer->datas[0].chunk->stride);
		} else {
			B.frames_after++;
			if (B.frames_after <= 3)
				printf("[%6.3f s] NEW frame %d: %u bytes, stride %d  "
				       "(hole since the request: %.1f ms; since the last old one: %.1f ms)\n",
				       (now() - B.t0) / 1e6, B.frames_after,
				       b->buffer->datas[0].chunk->size,
				       b->buffer->datas[0].chunk->stride,
				       (now() - B.t_request_2) / 1000.0,
				       (now() - B.t_last_old) / 1000.0);
		}
	}
	pw_stream_queue_buffer(B.flow, b);
	fflush(stdout);
}

static const struct pw_stream_events events = {
    PW_VERSION_STREAM_EVENTS,
    .state_changed = on_state,
    .param_changed = on_parameters,
    .process = on_process,
};

/* ⭐ THE BURST: twenty different sizes in two seconds, as a dragged browser
 *    window would do.  Question: does Mutter hold up, or does it get lost on the way? */
static void on_burst(void *d, uint64_t expirations)
{
	uint8_t sp[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(sp, sizeof sp);
	const struct spa_pod *par[1];
	uint32_t l, a;

	if (bursts_done >= burst_count) return;
	l = 1201 + (uint32_t) bursts_done * 37;
	a = 801 + (uint32_t) bursts_done * 13;
	B.new_w = l;
	B.new_h = a;
	B.phase = 1;
	bursts_done++;
	par[0] = proposal(&b, l, a);
	pw_stream_update_params(B.flow, par, 1);
}

static void on_timer(void *d, uint64_t expirations)
{
	static int step = 0;
	uint8_t sp[1024];
	struct spa_pod_builder b = SPA_POD_BUILDER_INIT(sp, sizeof sp);
	const struct spa_pod *par[1];

	step++;
	if (step == 1) {
		printf("\n[%6.3f s] === after %d s: %d frames at the first size ===\n",
		       (now() - B.t0) / 1e6, B.seconds, B.frames);
		print_state("first size");
		if (burst_count > 0) {
			printf("[%6.3f s] burst: %d asked, %d agreed EXACT\n",
			       (now() - B.t0) / 1e6, bursts_done, bursts_matched);
			return;
		}
		if (B.new_w == 0) { pw_main_loop_quit(B.loop); return; }
		printf("\n[%6.3f s] === HOT CHANGE: asking %ux%u ===\n", (now() - B.t0) / 1e6,
		       B.new_w, B.new_h);
		B.phase = 1;
		B.t_request_2 = now();
		par[0] = proposal(&b, B.new_w, B.new_h);
		pw_stream_update_params(B.flow, par, 1);
	} else if (step == 2) {
		printf("\n[%6.3f s] === after the change: %d new frames ===\n",
		       (now() - B.t0) / 1e6, B.frames_after);
		if (burst_count > 0)
			printf("[%6.3f s] FINAL burst: %d asked, %d agreed EXACT\n",
			       (now() - B.t0) / 1e6, bursts_done, bursts_matched);
		print_state("second size");
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
	struct spa_source *time_limit;
	struct timespec when, interval;
	char node_s[32];

	if (argc < 3) {
		fprintf(stderr, "usage: %s <L> <A> [<L2> <A2>] [seconds]\n", argv[0]);
		return 2;
	}
	B.requested_w = (uint32_t) atoi(argv[1]);
	B.requested_h = (uint32_t) atoi(argv[2]);
	if (argc >= 5 && strcmp(argv[3], "raffica") == 0) {
		burst_count = atoi(argv[4]);
	} else if (argc >= 5) {
		B.new_w = (uint32_t) atoi(argv[3]);
		B.new_h = (uint32_t) atoi(argv[4]);
	}
	B.seconds = (argc >= 6) ? atoi(argv[5]) : (argc == 4 ? atoi(argv[3]) : 4);
	if (B.seconds <= 0) B.seconds = 4;
	B.t0 = now();

	bus = g_bus_get_sync(G_BUS_TYPE_SESSION, NULL, &e);
	if (!bus) { fprintf(stderr, "⛔ bus: %s\n", e->message); return 3; }

	print_state("BEFORE everything");

	r = call(REMOTE_NAME, PATH_REMOTE, IFACE_REMOTE, "CreateSession", NULL,
	           G_VARIANT_TYPE("(o)"));
	if (!r) return 4;
	g_variant_get(r, "(o)", &p_check);
	g_variant_unref(r);

	g_variant_builder_init(&pr, G_VARIANT_TYPE("a{sv}"));
	{
		GVariant *idv = call(REMOTE_NAME, p_check, "org.freedesktop.DBus.Properties",
		                       "Get",
		                       g_variant_new("(ss)", IFACE_REMOTE_SESSION, "SessionId"),
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
	r = call(SCREENCAST_NAME, PATH_SCREENCAST, IFACE_SCREENCAST, "CreateSession",
	           g_variant_new("(a{sv})", &pr), G_VARIANT_TYPE("(o)"));
	if (!r) return 6;
	g_variant_get(r, "(o)", &p_capture);
	g_variant_unref(r);

	r = call(REMOTE_NAME, p_check, IFACE_REMOTE_SESSION, "Start", NULL, NULL);
	if (!r) return 7;
	g_variant_unref(r);

	g_variant_builder_init(&pr, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&pr, "{sv}", "cursor-mode", g_variant_new_uint32(2));
	g_variant_builder_add(&pr, "{sv}", "is-platform", g_variant_new_boolean(TRUE));
	r = call(SCREENCAST_NAME, p_capture, IFACE_SC_SESSION, "RecordVirtual",
	           g_variant_new("(a{sv})", &pr), G_VARIANT_TYPE("(o)"));
	if (!r) return 8;
	g_variant_get(r, "(o)", &p_stream);
	g_variant_unref(r);
	printf("stream: %s\n", p_stream);

	{
		GMainContext *c = g_main_context_new();
		GSource *bat;
		gint64 sc;
		g_main_context_push_thread_default(c);
		g_dbus_connection_signal_subscribe(bus, NULL, IFACE_SC_STREAM,
		                                   "PipeWireStreamAdded", p_stream, NULL,
		                                   G_DBUS_SIGNAL_FLAGS_NONE, on_node, &node, NULL);
		r = call(SCREENCAST_NAME, p_stream, IFACE_SC_STREAM, "Start", NULL, NULL);
		if (!r) return 9;
		g_variant_unref(r);
		bat = g_timeout_source_new(50);
		g_source_set_callback(bat, wake, NULL, NULL);
		g_source_attach(bat, c);
		sc = now() + 5000000;
		while (node == 0 && now() < sc) g_main_context_iteration(c, TRUE);
		g_main_context_pop_thread_default(c);
	}
	if (!node) { fprintf(stderr, "⛔ no node\n"); return 10; }
	printf("PipeWire node: %u\n", node);
	fflush(stdout);

	pw_init(NULL, NULL);
	B.loop = pw_main_loop_new(NULL);
	ctx = pw_context_new(pw_main_loop_get_loop(B.loop), NULL, 0);
	core = pw_context_connect(ctx, NULL, 0);
	if (!core) { fprintf(stderr, "⛔ PipeWire does not answer\n"); return 11; }

	snprintf(node_s, sizeof node_s, "%u", node);
	B.flow = pw_stream_new(core, "misura-f4in8",
	                         pw_properties_new(PW_KEY_MEDIA_TYPE, "Video", PW_KEY_MEDIA_CATEGORY,
	                                           "Capture", PW_KEY_MEDIA_ROLE, "Screen", NULL));
	pw_stream_add_listener(B.flow, &B.listen, &events, NULL);
	par[0] = proposal(&b, B.requested_w, B.requested_h);
	if (pw_stream_connect(B.flow, PW_DIRECTION_INPUT, node,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS, par, 1) < 0) {
		fprintf(stderr, "⛔ pw_stream_connect\n");
		return 12;
	}

	if (burst_count > 0) {
		struct spa_source *t2 = pw_loop_add_timer(pw_main_loop_get_loop(B.loop),
		                                          on_burst, NULL);
		struct timespec q = {0, 300000000}, iv = {0, 100000000};
		pw_loop_update_timer(pw_main_loop_get_loop(B.loop), t2, &q, &iv, false);
	}
	time_limit = pw_loop_add_timer(pw_main_loop_get_loop(B.loop), on_timer, NULL);
	when.tv_sec = B.seconds;
	when.tv_nsec = 0;
	interval.tv_sec = B.seconds;
	interval.tv_nsec = 0;
	pw_loop_update_timer(pw_main_loop_get_loop(B.loop), time_limit, &when, &interval, false);

	pw_main_loop_run(B.loop);

	printf("\n== summary ==\n  asked %ux%u -> got %ux%u, %d frames\n",
	       B.requested_w, B.requested_h, B.schema.size.width, B.schema.size.height, B.frames);
	if (B.new_w)
		printf("  then asked %ux%u -> %d new frames\n", B.new_w, B.new_h,
		       B.frames_after);
	pw_stream_destroy(B.flow);
	pw_context_destroy(ctx);
	pw_main_loop_destroy(B.loop);

	call(SCREENCAST_NAME, p_capture, IFACE_SC_SESSION, "Stop", NULL, NULL);
	call(REMOTE_NAME, p_check, IFACE_REMOTE_SESSION, "Stop", NULL, NULL);
	return 0;
}
