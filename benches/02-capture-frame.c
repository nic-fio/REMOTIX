/*
 * 02-capture-frame — ONE frame taken from the GNOME session, delivered
 * in memory with the buffer type DECLARED.  Bench of sub-phase F2.2.
 *
 * ⛔ WHY IT EXISTS, GIVEN THAT `misura-cattura` IS ALREADY THERE
 *
 * The phase 0 tool (`fondamenta/banchi/banco-compositori/misura-cattura.c`) is
 * certified, reproduces Mutter's 36 ± 2 frames, and stays the historical positive
 * control of the whole project.  ⛔ But it **never** looks inside the
 * buffer: it counts the frames, reads the data type, the damage, the fence and the
 * intervals — and it does not touch the pixels.  Line by line: `on_process` takes
 * `datas[0]`, reads its `type`, `fd`, `chunk->stride`, and puts the buffer back in
 * the queue with `pw_stream_queue_buffer`.  No read of `piano->data`.
 *
 * ⇒ **A completely BLACK frame would pass phase 0 with full
 *   marks**: 36 per second, partial damage, four recycled buffers, zero sequence
 *   skips.  All green, and on the screen nothing.
 *
 * ⛔ And black is not a textbook case: `STUDIES.md` §gnome §3.1 says that in headless mode
 *   `needs_outputs=false`, so **without `--virtual-monitor` the session starts
 *   alive, complete and black**, and it is the broken test M9 of the measurement plan of
 *   `STUDIES.md` §gnome §13.  The phase 2 plan (`PLAN.md`) writes it in
 *   full: *«a black and perfectly alive session is the thing that gets mistaken
 *   for a capture defect, and you search for half a day on the wrong
 *   side»*.  The BLACK AND VALID frame is the worst fault of this
 *   sub-phase, and a tool that can see it is needed.
 *
 * This program therefore does the thing the other does not, and **only that**:
 * it takes a frame, writes it to disk byte by byte, and next to it puts a
 * manifest with everything needed to judge it without having to deduce it.  Whoever
 * judges is another program (`02-capture-judge.py`), and the separation is
 * intended: it is the only way of injecting a fault into the PIXELS — a black frame
 * instead of the real one — without touching either the producer or the judge.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT THIS PROGRAM DOES **NOT** PROVE — written here because it is
 *    error form E1 of `REVIEWER.md` §2, and this is exactly the point where
 *    it has already been paid for twice (`LESSONS.md` §1.11):
 *
 *   | What is read in the manifest    | What it does NOT prove                |
 *   |---------------------------------|---------------------------------------|
 *   | `kind = MemFd`                  | ⛔ **nothing about the compositor**: it|
 *   |                                 | depends on what the CLIENT asked for.  |
 *   |                                 | Here the client asks for memory        |
 *   |                                 | on purpose — readable pixels are       |
 *   |                                 | needed — so MemFd is the ANSWER TO A   |
 *   |                                 | QUESTION OF OURS, not a discovery      |
 *   | `kind = DMA-BUF`                | does not prove Mutter renders on GPU:  |
 *   |                                 | an open render node is necessary,      |
 *   |                                 | not sufficient (KWin opens one even    |
 *   |                                 | when it then renders in QPainter)      |
 *
 *   That is why the manifest carries THREE separate fields and not one: `requested`,
 *   `dichiarato_dal_produttore` and `chi_lo_dice`.  ⭐ The buffer type **is
 *   asked for and declared**, not deduced — and it is the mandate of F2.2.
 *
 * ---------------------------------------------------------------------------
 * ⛔ ZERO, FAILED AND FAULT ARE THREE DIFFERENT THINGS (`REVIEWER.md` §1 point 4)
 *
 *   exit 0  a frame is there and it was written
 *   exit 3  ⭐ ZERO frames, but the stream WAS active for the whole
 *           measurement: it is a **legitimate** zero — a still desktop delivers
 *           nothing (`LESSONS.md` §4 trap 8), and it is a result, not a
 *           fault.  No `.raw` is written, and the manifest says so
 *   exit 2  FAULT: the stream never became active, or it dropped
 *           during the measurement, or one road was asked for and another
 *           arrived.  There is no number to read
 *   exit 1  the environment: the virtual monitor does not mount, PipeWire does not
 *           answer, the file cannot be written
 *
 * The three exit-2 guards are the same that phase 0 had to add
 * to `misura-cattura` AFTER having believed it (items 1 and 8 of «What did NOT
 * work» in `PHASES.md` §00-ambiente): here they are born together with the program.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE ORDER: FIRST THE MONITOR, THEN THE SCENE — and the program says it, not whoever
 *    launches it.
 *
 * Phase 0's `banco.sh` switches the scene on 2.5 seconds AFTER the meter, with
 * the reason written next to it: *«without a screen there is nowhere to open»*.  Here
 * a timed wait is not enough, because this program must then know WHICH
 * frames arrived before the scene and which after.  So the program
 * writes a file (`--ready`) at the instant the stream becomes active, and
 * whoever launches it switches the scene on only then.  ⭐ It is not a wait: it is an event
 * (`LESSONS.md` §4 trap 9 — «you do not wait for a silence, you wait for an
 * event»).
 *
 * ⚠ And the same form bites phase 2 from another side, already measured: in a
 *   GNOME session without input devices, a client opened BEFORE the
 *   `libei` virtual pointer exists receives nothing (`PLAN.md`, box
 *   «A question phase 1 found and that bites HERE», `[M]` 10 Aug).
 *   Here no device is created — it is not F2.2's area — but the order is
 *   the same, and whoever mounts input will have to slip it between `--ready` and the
 *   scene.
 *
 * ---------------------------------------------------------------------------
 * ⛔ TWO FRAMES, NOT ONE, AND THE REASON IS `CODER.md` §3.5 (form E9)
 *
 * *A sample taken at start-up says nothing about the steady state.*  For a still
 * image the rule does not disappear: it changes form.
 *
 *   `first`   the first frame after the stream became active, before
 *             the scene exists.  It is the **full redraw**: on it the
 *             damage is `full`, and it is the frame the user would see
 *             connecting to a just-mounted desktop
 *   `regime`  a frame taken after `--post-scene` seconds of live scene,
 *             skipping `--discard`.  On Mutter in steady state the damage is
 *             **partial** in 98 % of cases (`PHASES.md` §00-ambiente: full 15,
 *             partial 929)
 *
 * ⭐ And the comparison between the two answers a question the documents today
 *    contradict each other on:
 *
 *   - `fondamenta/remotix-c/src/cattura.h` says: *«in zero-copy Mutter recycles its own
 *     buffers and repaints in them ONLY the part that changed; outside those
 *     regions are the pixels of the frame that had used that buffer
 *     before»*;
 *   - `STUDIES.md` §gnome §8.1, which reread Mutter's code, says the opposite:
 *     *«⛔ false: blit of the whole framebuffer, clip stack emptied
 *     deliberately»*.
 *
 *   One of the two is old.  A `regime` frame with **partial** damage that
 *   nevertheless contains the WHOLE scene settles the matter, and settles it with a
 *   measurement instead of a rereading.  ⚠ And the decision matters: if
 *   `capture.h` were right, phase 2 would deliver half a desktop and half an old
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
 * a question nobody asked, and it is item 8 of `PHASES.md` §00-ambiente.
 *
 * ---------------------------------------------------------------------------
 * usage:
 *   02-capture-frame --output PREFISSO --ready FILE
 *        [--width W] [--height H] [--fps N] [--bgra] [--dmabuf]
 *        [--post-scene S] [--discard N] [--duration S] [--label T]
 *        [--node N]
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

#define WAIT_CALL_MS 15000
#define WAIT_NODE_MS 10000
#define WAIT_STARTUP_S 10
#define FD_MAX 16
#define MAX_TYPES 8

/* ------------------------------------------------------------------ *
 *  The held frame
 * ------------------------------------------------------------------ */

typedef struct
{
	gboolean taken;
	uint8_t *pixel;      /* our copy: PipeWire's buffer goes back at once  */
	size_t byte;
	uint32_t stride;
	uint32_t offset;
	uint32_t chunk_size;
	uint32_t data_type;
	int64_t seq;
	int64_t pts;
	gboolean seq_known;
	const char *damage;   /* "full" | "partial" | "assente"                */
	guint64 idx;      /* which frame it was, counted from the first arrived */
	gint64 when;
} Stopped;

typedef struct
{
	struct pw_thread_loop *cycle;
	struct pw_context *context;
	struct pw_core *core;
	struct pw_stream *stream;
	struct spa_hook hook;

	struct spa_video_info_raw fmt;
	gboolean known_format;
	enum pw_stream_state state;
	char *fault;
	gboolean wants_dmabuf;

	guint64 incoming;
	guint64 before_scene;
	guint64 after_scene;
	guint64 full_damage, partial_damage, missing_damage;
	guint64 without_header;

	int fd_seen[FD_MAX];
	guint how_many_fd;
	uint32_t seen_types[MAX_TYPES];
	guint how_many_types;

	/* ⛔ The scene is declared alive with a variable written by WHOEVER LAUNCHES,
	 *    not with a clock: the program must know which frames
	 *    arrived before and which after, and a timed wait does not tell them apart. */
	volatile gboolean scene_alive;
	gint64 t_scene;      /* when the scene was declared alive               */
	gint64 t_regime;     /* from when the steady-state frame may be taken   */
	guint64 skip_left;

	Stopped first;
	Stopped regime;

	gint64 t_start;
} Take;

/* ------------------------------------------------------------------ *
 *  The damage — copied from phase 0 because the question is the same
 * ------------------------------------------------------------------ */

static const char *look_damage(Take *p, struct pw_buffer *bundle)
{
	struct spa_meta *meta = spa_buffer_find_meta(bundle->buffer, SPA_META_VideoDamage);
	struct spa_meta_region *region;
	gboolean covers_all = FALSE;
	gboolean vista = FALSE;

	if (!meta)
	{
		p->missing_damage++;
		return "assente";
	}
	spa_meta_for_each(region, meta)
	{
		if (!spa_meta_region_is_valid(region))
			break;
		vista = TRUE;
		if (region->region.position.x == 0 && region->region.position.y == 0 &&
		    region->region.size.width >= p->fmt.size.width &&
		    region->region.size.height >= p->fmt.size.height)
			covers_all = TRUE;
	}
	if (!vista)
	{
		p->missing_damage++;
		return "assente";
	}
	if (covers_all)
	{
		p->full_damage++;
		return "pieno";
	}
	p->partial_damage++;
	return "partial";
}

/*
 * ⛔ IT IS COPIED, THE POINTER IS NOT KEPT.
 *
 * v1's `capture.h` writes it at the top: *«the pixels live only for the duration
 * of the call: whoever wants them copies them»*.  A kept pointer would be
 * rewritten by the producer at the next round, and the frame written to disk
 * would be a frame different from the one whose damage and sequence the manifest tells
 * about: two measurements under the same label, which is form E2.
 */
static void hold(Stopped *f, struct spa_data *piano, struct spa_meta_header *header,
                      const char *damage, guint64 idx, gint64 t_now)
{
	uint32_t size;
	uint32_t offset = piano->chunk ? piano->chunk->offset : 0;

	size = piano->chunk && piano->chunk->size > 0 ? piano->chunk->size : piano->maxsize;
	if (offset + size > piano->maxsize)
		size = piano->maxsize > offset ? piano->maxsize - offset : 0;
	if (!piano->data || size == 0)
		return;

	g_free(f->pixel);
	f->pixel = g_malloc(size);
	memcpy(f->pixel, (const uint8_t *) piano->data + offset, size);
	f->byte = size;
	f->stride = piano->chunk ? (uint32_t) piano->chunk->stride : 0;
	f->offset = offset;
	f->chunk_size = piano->chunk ? piano->chunk->size : 0;
	f->data_type = piano->type;
	f->damage = damage;
	f->idx = idx;
	f->when = t_now;
	if (header)
	{
		f->seq = (int64_t) header->seq;
		f->pts = (int64_t) header->pts;
		f->seq_known = TRUE;
	}
	f->taken = TRUE;
}

static void on_state(void *data, enum pw_stream_state old, enum pw_stream_state fresh,
                     const char *error)
{
	Take *p = data;

	p->state = fresh;
	if (error)
	{
		g_free(p->fault);
		p->fault = g_strdup(error);
	}
	if (fresh == PW_STREAM_STATE_STREAMING && p->t_start == 0)
	{
		p->t_start = g_get_monotonic_time();
		fprintf(stderr, "  stream active\n");
	}
	pw_thread_loop_signal(p->cycle, false);
}

static void on_parameters(void *data, uint32_t id, const struct spa_pod *param)
{
	Take *p = data;
	uint32_t kind, subtype;
	uint8_t space[1024];
	struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(space, sizeof space);
	const struct spa_pod *parameters[3];
	int types = (1 << SPA_DATA_MemFd) | (1 << SPA_DATA_MemPtr);

	if (!param || id != SPA_PARAM_Format)
		return;
	if (spa_format_parse(param, &kind, &subtype) < 0)
		return;
	if (kind != SPA_MEDIA_TYPE_video || subtype != SPA_MEDIA_SUBTYPE_raw)
		return;
	if (spa_format_video_raw_parse(param, &p->fmt) < 0)
		return;

	p->known_format = TRUE;
	fprintf(stderr, "  negotiated format: %ux%u %s, modifier 0x%" PRIx64 "\n",
	        p->fmt.size.width, p->fmt.size.height,
	        p->fmt.format == SPA_VIDEO_FORMAT_BGRx ? "BGRx"
	        : p->fmt.format == SPA_VIDEO_FORMAT_BGRA ? "BGRA"
	                                                     : "OTHER",
	        (uint64_t) p->fmt.modifier);

	/* The data type is agreed HERE, not in the format: whoever stays silent leaves the
	 * default.  `LESSONS.md` §4 trap 4 — the buffer type is asked for in
	 * TWO places, and declaring only one makes the negotiation succeed with inside
	 * the opposite of what was wanted. */
	if (p->wants_dmabuf)
		types |= (1 << SPA_DATA_DmaBuf);

	parameters[0] = spa_pod_builder_add_object(
	    &builder, SPA_TYPE_OBJECT_ParamBuffers, SPA_PARAM_Buffers, SPA_PARAM_BUFFERS_buffers,
	    SPA_POD_CHOICE_RANGE_Int(4, 2, 8), SPA_PARAM_BUFFERS_dataType,
	    SPA_POD_CHOICE_FLAGS_Int(types));
	parameters[1] = spa_pod_builder_add_object(
	    &builder, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_Header), SPA_PARAM_META_size,
	    SPA_POD_Int(sizeof(struct spa_meta_header)));
	parameters[2] = spa_pod_builder_add_object(
	    &builder, SPA_TYPE_OBJECT_ParamMeta, SPA_PARAM_Meta, SPA_PARAM_META_type,
	    SPA_POD_Id(SPA_META_VideoDamage), SPA_PARAM_META_size,
	    SPA_POD_CHOICE_RANGE_Int(sizeof(struct spa_meta_region) * 4,
	                             sizeof(struct spa_meta_region) * 1,
	                             sizeof(struct spa_meta_region) * 16));
	pw_stream_update_params(p->stream, parameters, 3);
	pw_thread_loop_signal(p->cycle, false);
}

static void on_process(void *data)
{
	Take *p = data;
	struct pw_buffer *bundle;
	struct spa_data *piano;
	struct spa_meta_header *header;
	const char *damage;
	gint64 t_now;
	guint i;
	gboolean known;

	bundle = pw_stream_dequeue_buffer(p->stream);
	if (!bundle)
		return;

	t_now = g_get_monotonic_time();
	piano = &bundle->buffer->datas[0];
	p->incoming++;

	/* How many distinct buffers the producer recycles: Mutter uses four, and
	 * knowing it serves to read the rest (R29). */
	known = FALSE;
	for (i = 0; i < p->how_many_fd; i++)
		if (p->fd_seen[i] == (piano->fd >= 0 ? (int) piano->fd : -1))
			known = TRUE;
	if (!known && p->how_many_fd < FD_MAX)
		p->fd_seen[p->how_many_fd++] = piano->fd >= 0 ? (int) piano->fd : -1;

	/* ⛔ THE TYPES ARE ALL COLLECTED, not only the last one kept.
	 *    `misura-cattura` prints `m->data_type` of the LAST frame: if the
	 *    producer changed road midway through the measurement, the line would say one road
	 *    only for two different populations.  It has never been seen happening,
	 *    but «it has never been seen» is not «it cannot», and it costs eight integers. */
	known = FALSE;
	for (i = 0; i < p->how_many_types; i++)
		if (p->seen_types[i] == piano->type)
			known = TRUE;
	if (!known && p->how_many_types < MAX_TYPES)
		p->seen_types[p->how_many_types++] = piano->type;

	header = spa_buffer_find_meta_data(bundle->buffer, SPA_META_Header, sizeof *header);
	if (!header)
		p->without_header++;
	damage = look_damage(p, bundle);

	if (!p->scene_alive)
	{
		p->before_scene++;
		/* The VERY FIRST: the full redraw, and the frame that
		 * whoever connects to a just-mounted desktop would see. */
		if (!p->first.taken)
			hold(&p->first, piano, header, damage, p->incoming, t_now);
	}
	else
	{
		p->after_scene++;
		if (p->t_regime == 0)
			p->t_regime = p->t_scene;
		if (t_now >= p->t_regime)
		{
			if (p->skip_left > 0)
				p->skip_left--;
			else
				/* It is rewritten at every round: the steady-state frame of
				 * interest is the LAST of the window, not the first — so
				 * the damage it carries is the steady-state one and not that of the
				 * first redraw after switching the scene on. */
				hold(&p->regime, piano, header, damage, p->incoming, t_now);
		}
	}

	pw_stream_queue_buffer(p->stream, bundle);
}

static const struct pw_stream_events events = {
	PW_VERSION_STREAM_EVENTS,
	.state_changed = on_state,
	.param_changed = on_parameters,
	.process = on_process,
};

/* ------------------------------------------------------------------ *
 *  The format proposal — identical to that of phase 0
 * ------------------------------------------------------------------ */

static const struct spa_pod *shm_format(struct spa_pod_builder *c, uint32_t w, uint32_t h,
                                             uint32_t fps, uint32_t color)
{
	struct spa_rectangle measure = SPA_RECTANGLE(w, h);
	struct spa_fraction cadence = SPA_FRACTION(0, 1);
	struct spa_fraction lowest = SPA_FRACTION(1, 1);
	struct spa_fraction max_dims = SPA_FRACTION(fps > 0 ? fps : 1, 1);

	return spa_pod_builder_add_object(
	    c, SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat, SPA_FORMAT_mediaType,
	    SPA_POD_Id(SPA_MEDIA_TYPE_video), SPA_FORMAT_mediaSubtype,
	    SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw), SPA_FORMAT_VIDEO_format, SPA_POD_Id(color),
	    SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&measure), SPA_FORMAT_VIDEO_framerate,
	    SPA_POD_Fraction(&cadence), SPA_FORMAT_VIDEO_maxFramerate,
	    SPA_POD_CHOICE_RANGE_Fraction(&max_dims, &lowest, &max_dims));
}

static const struct spa_pod *format_dmabuf(struct spa_pod_builder *c, uint32_t w, uint32_t h,
                                            uint32_t fps, uint32_t color)
{
	struct spa_rectangle measure = SPA_RECTANGLE(w, h);
	struct spa_fraction cadence = SPA_FRACTION(0, 1);
	struct spa_fraction lowest = SPA_FRACTION(1, 1);
	struct spa_fraction max_dims = SPA_FRACTION(fps > 0 ? fps : 1, 1);
	struct spa_pod_frame border[2];

	spa_pod_builder_push_object(c, &border[0], SPA_TYPE_OBJECT_Format, SPA_PARAM_EnumFormat);
	spa_pod_builder_add(c, SPA_FORMAT_mediaType, SPA_POD_Id(SPA_MEDIA_TYPE_video),
	                    SPA_FORMAT_mediaSubtype, SPA_POD_Id(SPA_MEDIA_SUBTYPE_raw),
	                    SPA_FORMAT_VIDEO_format, SPA_POD_Id(color), 0);
	spa_pod_builder_prop(c, SPA_FORMAT_VIDEO_modifier,
	                     SPA_POD_PROP_FLAG_MANDATORY | SPA_POD_PROP_FLAG_DONT_FIXATE);
	spa_pod_builder_push_choice(c, &border[1], SPA_CHOICE_Enum, 0);
	spa_pod_builder_long(c, DRM_FORMAT_MOD_INVALID);
	spa_pod_builder_long(c, DRM_FORMAT_MOD_INVALID);
	spa_pod_builder_long(c, DRM_FORMAT_MOD_LINEAR);
	spa_pod_builder_pop(c, &border[1]);
	spa_pod_builder_add(c, SPA_FORMAT_VIDEO_size, SPA_POD_Rectangle(&measure),
	                    SPA_FORMAT_VIDEO_framerate, SPA_POD_Fraction(&cadence),
	                    SPA_FORMAT_VIDEO_maxFramerate,
	                    SPA_POD_CHOICE_RANGE_Fraction(&max_dims, &lowest, &max_dims), 0);
	return spa_pod_builder_pop(c, &border[0]);
}

/* ------------------------------------------------------------------ *
 *  Mutter's virtual monitor — the sequence that admits no permutations
 * ------------------------------------------------------------------ */

#define REMOTE_NAME "org.gnome.Mutter.RemoteDesktop"
#define REMOTE_PATH "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_REMOTE_SESSION "org.gnome.Mutter.RemoteDesktop.Session"
#define SCREENCAST_NAME "org.gnome.Mutter.ScreenCast"
#define SCREENCAST_PATH "/org/gnome/Mutter/ScreenCast"
#define IFACE_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define IFACE_SC_SESSION "org.gnome.Mutter.ScreenCast.Session"
#define IFACE_SC_STREAM "org.gnome.Mutter.ScreenCast.Stream"

typedef struct
{
	GDBusConnection *bus;
	char *check;
	char *capture;
	char *stream;
	uint32_t node;
} StageV;

static void on_node(GDBusConnection *bus, const char *sender, const char *fpath,
                    const char *interfaccia, const char *send_signal, GVariant *parameters, gpointer d)
{
	if (g_variant_is_of_type(parameters, G_VARIANT_TYPE("(u)")))
		g_variant_get(parameters, "(u)", (uint32_t *) d);
}

static gboolean wake(gpointer d)
{
	return G_SOURCE_CONTINUE;
}

/* g_bus_get_sync is never used on the session bus: GIO keeps
 * `exit-on-close` on there and kills us at logout (`LESSONS.md` §5, «the session
 * bus»). */
static GDBusConnection *session_dbus(GError **mistake)
{
	g_autofree char *address = g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, mistake);
	GDBusConnection *bus;

	if (!address)
		return NULL;
	bus = g_dbus_connection_new_for_address_sync(
	    address,
	    G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
	        G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
	    NULL, NULL, mistake);
	if (bus)
		g_dbus_connection_set_exit_on_close(bus, FALSE);
	return bus;
}

static GVariant *call(GDBusConnection *bus, const char *name, const char *fpath,
                        const char *iface, const char *method, GVariant *arg,
                        const GVariantType *response, GError **mistake)
{
	return g_dbus_connection_call_sync(bus, name, fpath, iface, method, arg, response,
	                                   G_DBUS_CALL_FLAGS_NONE, WAIT_CALL_MS, NULL, mistake);
}

/*
 * ⛔ THE ORDER IS THAT OF `mutter.h`, and every permutation is punished with a
 *    different error that does not say «you got the order wrong» (`LESSONS.md` §4 trap 1):
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
static StageV *stage_mount(uint32_t width, uint32_t height, GError **mistake)
{
	StageV *p = g_new0(StageV, 1);
	g_autofree char *id = NULL;
	GVariantBuilder prop;
	guint subscription;
	GMainContext *context;
	GSource *heartbeat;
	gint64 expiry;

	p->bus = session_dbus(mistake);
	if (!p->bus)
		goto fault;

	{
		g_autoptr(GVariant) r = call(p->bus, REMOTE_NAME, REMOTE_PATH, IFACE_REMOTE,
		                               "CreateSession", NULL, G_VARIANT_TYPE("(o)"), mistake);
		if (!r)
		{
			g_prefix_error(mistake, "Mutter does not expose RemoteDesktop (is there a session?): ");
			goto fault;
		}
		g_variant_get(r, "(o)", &p->check);
	}
	{
		g_autoptr(GVariant) r =
		    call(p->bus, REMOTE_NAME, p->check, "org.freedesktop.DBus.Properties", "Get",
		           g_variant_new("(ss)", IFACE_REMOTE_SESSION, "SessionId"),
		           G_VARIANT_TYPE("(v)"), mistake);
		g_autoptr(GVariant) v = NULL;
		if (!r)
			goto fault;
		g_variant_get(r, "(v)", &v);
		id = g_variant_dup_string(v, NULL);
	}

	g_variant_builder_init(&prop, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&prop, "{sv}", "remote-desktop-session-id", g_variant_new_string(id));
	g_variant_builder_add(&prop, "{sv}", "disable-animations", g_variant_new_boolean(TRUE));
	{
		g_autoptr(GVariant) r =
		    call(p->bus, SCREENCAST_NAME, SCREENCAST_PATH, IFACE_SCREENCAST, "CreateSession",
		           g_variant_new("(a{sv})", &prop), G_VARIANT_TYPE("(o)"), mistake);
		if (!r)
			goto fault;
		g_variant_get(r, "(o)", &p->capture);
	}
	{
		g_autoptr(GVariant) r = call(p->bus, REMOTE_NAME, p->check, IFACE_REMOTE_SESSION,
		                               "Start", NULL, NULL, mistake);
		if (!r)
			goto fault;
	}

	g_variant_builder_init(&prop, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&prop, "{sv}", "cursor-mode", g_variant_new_uint32(2));
	g_variant_builder_add(&prop, "{sv}", "is-platform", g_variant_new_boolean(TRUE));
	{
		g_autofree char *mapping = g_uuid_string_random();
		g_autoptr(GVariant) r = NULL;

		g_variant_builder_add(&prop, "{sv}", "mapping-id", g_variant_new_string(mapping));
		r = call(p->bus, SCREENCAST_NAME, p->capture, IFACE_SC_SESSION, "RecordVirtual",
		           g_variant_new("(a{sv})", &prop), G_VARIANT_TYPE("(o)"), mistake);
		if (!r)
			goto fault;
		g_variant_get(r, "(o)", &p->stream);
	}

	context = g_main_context_new();
	g_main_context_push_thread_default(context);
	subscription = g_dbus_connection_signal_subscribe(p->bus, NULL, IFACE_SC_STREAM,
	                                                    "PipeWireStreamAdded", p->stream, NULL,
	                                                    G_DBUS_SIGNAL_FLAGS_NONE, on_node, &p->node,
	                                                    NULL);
	{
		g_autoptr(GVariant) r =
		    call(p->bus, SCREENCAST_NAME, p->stream, IFACE_SC_STREAM, "Start", NULL, NULL, mistake);
		if (!r)
		{
			g_dbus_connection_signal_unsubscribe(p->bus, subscription);
			g_main_context_pop_thread_default(context);
			g_main_context_unref(context);
			goto fault;
		}
	}
	heartbeat = g_timeout_source_new(50);
	g_source_set_callback(heartbeat, wake, NULL, NULL);
	g_source_attach(heartbeat, context);
	expiry = g_get_monotonic_time() + (gint64) WAIT_NODE_MS * 1000;
	while (p->node == 0 && g_get_monotonic_time() < expiry)
		g_main_context_iteration(context, TRUE);
	g_source_destroy(heartbeat);
	g_source_unref(heartbeat);
	g_dbus_connection_signal_unsubscribe(p->bus, subscription);
	g_main_context_pop_thread_default(context);
	g_main_context_unref(context);

	if (p->node == 0)
	{
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT, "no PipeWire node announced");
		goto fault;
	}
	fprintf(stderr, "  virtual monitor %ux%u requested, PipeWire node %u\n", width, height,
	        p->node);
	return p;

fault:
	if (p->bus && p->check)
	{
		g_autoptr(GError) x = NULL;
		g_autoptr(GVariant) r = g_dbus_connection_call_sync(
		    p->bus, REMOTE_NAME, p->check, IFACE_REMOTE_SESSION, "Stop", NULL, NULL,
		    G_DBUS_CALL_FLAGS_NONE, 2000, NULL, &x);
	}
	g_clear_object(&p->bus);
	g_free(p->check);
	g_free(p->capture);
	g_free(p->stream);
	g_free(p);
	return NULL;
}

static void stage_unmount(StageV *p)
{
	if (!p)
		return;
	if (p->bus && p->check)
	{
		g_autoptr(GError) x = NULL;
		g_autoptr(GVariant) r = g_dbus_connection_call_sync(
		    p->bus, REMOTE_NAME, p->check, IFACE_REMOTE_SESSION, "Stop", NULL, NULL,
		    G_DBUS_CALL_FLAGS_NONE, 2000, NULL, &x);
	}
	g_clear_object(&p->bus);
	g_free(p->check);
	g_free(p->capture);
	g_free(p->stream);
	g_free(p);
}

/* ------------------------------------------------------------------ *
 *  The manifest
 * ------------------------------------------------------------------ */

static const char *type_name(uint32_t t)
{
	return t == SPA_DATA_DmaBuf   ? "DMA-BUF"
	       : t == SPA_DATA_MemFd  ? "MemFd"
	       : t == SPA_DATA_MemPtr ? "MemPtr"
	       : t == SPA_DATA_MemId  ? "MemId"
	                              : "UNKNOWN";
}

static const char *color_name(uint32_t c)
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
 *    `STUDIES.md` §gnome §8.3 `[R]`, read line by line in the code of Mutter 48.7:
 *    **«Only BGRx and BGRA»**.  They are formats at **8 bits per channel**.
 *
 *    ⇒ From this capture ten real bits CANNOT come out.  An HEVC Main10
 *      fed from here carries 8 bits promoted to 10, and the label keeps
 *      saying Main10 while the image comes out fine anyway: it is the fault
 *      F2.3 calls **F2.3-A**, and ⛔ **the defendant is here, not in the encoder**.
 *      That is why the number is measured already at capture.
 */
static const char *range_name(uint32_t r)
{
	switch (r)
	{
	case 1: return "FULL (0-255)";
	case 2: return "LIMITED (16-235)";
	default: return "NOT DECLARED by the producer";
	}
}

static const char *matrix_name(uint32_t m)
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

static const char *transfer_name(uint32_t t)
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

static const char *primaries_name(uint32_t p)
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
static int bit_per_channel(uint32_t c)
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

static gboolean write_raw(const char *fpath, const Stopped *f, GError **mistake)
{
	return g_file_set_contents(fpath, (const char *) f->pixel, (gssize) f->byte, mistake);
}

static void manifest_still(GString *s, const char *key, const Stopped *f, const char *file)
{
	if (!f->taken)
	{
		g_string_append_printf(s, "  \"%s\": null,\n", key);
		return;
	}
	g_string_append_printf(s,
	                       "  \"%s\": {\n"
	                       "    \"file\": \"%s\",\n"
	                       "    \"byte\": %zu,\n"
	                       "    \"stride\": %u,\n"
	                       "    \"offset\": %u,\n"
	                       "    \"dimensione_chunk\": %u,\n"
	                       "    \"type_declared\": \"%s\",\n"
	                       "    \"damage\": \"%s\",\n"
	                       "    \"indice_fra_gli_arrivati\": %" PRIu64 ",\n"
	                       "    \"seq\": %" PRId64 ",\n"
	                       "    \"pts\": %" PRId64 ",\n"
	                       "    \"seq_nota\": %s\n"
	                       "  },\n",
	                       key, file, f->byte, f->stride, f->offset, f->chunk_size,
	                       type_name(f->data_type), f->damage, f->idx, f->seq, f->pts,
	                       f->seq_known ? "true" : "false");
}

/* ------------------------------------------------------------------ *
 *  The program
 * ------------------------------------------------------------------ */

int main(int argc, char **argv)
{
	uint32_t width = 1920, height = 1080, fps = 60, node = 0;
	double post_scene = 3.0, duration = 12.0, wait_scene = 25.0;
	guint64 discard = 10;
	/* ⛔ How many frames are REQUIRED after the scene was declared
	 *    alive.  One is enough: the question is «does the scene paint on the screen we
	 *    are capturing, yes or no?».  With `0` one declares one wants to measure
	 *    the legitimate zero («stopped» scene). */
	guint64 min_after_scene = 1;
	gboolean wants_dmabuf = FALSE;
	uint32_t color = SPA_VIDEO_FORMAT_BGRx;
	const char *label = "senza-nome";
	const char *output = NULL, *ready = NULL, *scene_signal = NULL;
	Take p = { 0 };
	StageV *stage = NULL;
	uint8_t space[2048];
	struct spa_pod_builder builder = SPA_POD_BUILDER_INIT(space, sizeof space);
	const struct spa_pod *parameters[2];
	uint32_t n_parameters = 0;
	g_autoptr(GError) mistake = NULL;
	g_autofree char *first_file = NULL, *file_regime = NULL, *file_json = NULL;
	GString *manifesto;
	gint64 expiry, fine;
	int code = 0;
	const char *outcome;
	char when[64];
	time_t now_epoch;
	struct tm now_tm;
	guint i;

	for (i = 1; (int) i < argc; i++)
	{
		if (!strcmp(argv[i], "--output") && (int) i + 1 < argc)
			output = argv[++i];
		else if (!strcmp(argv[i], "--ready") && (int) i + 1 < argc)
			ready = argv[++i];
		else if (!strcmp(argv[i], "--scene-signal") && (int) i + 1 < argc)
			scene_signal = argv[++i];
		else if (!strcmp(argv[i], "--node") && (int) i + 1 < argc)
			node = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--width") && (int) i + 1 < argc)
			width = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--height") && (int) i + 1 < argc)
			height = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--fps") && (int) i + 1 < argc)
			fps = (uint32_t) atoi(argv[++i]);
		else if (!strcmp(argv[i], "--post-scene") && (int) i + 1 < argc)
			post_scene = atof(argv[++i]);
		else if (!strcmp(argv[i], "--wait-scene") && (int) i + 1 < argc)
			wait_scene = atof(argv[++i]);
		else if (!strcmp(argv[i], "--duration") && (int) i + 1 < argc)
			duration = atof(argv[++i]);
		else if (!strcmp(argv[i], "--discard") && (int) i + 1 < argc)
			discard = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--min-after-scene") && (int) i + 1 < argc)
			min_after_scene = (guint64) atoll(argv[++i]);
		else if (!strcmp(argv[i], "--dmabuf"))
			wants_dmabuf = TRUE;
		else if (!strcmp(argv[i], "--bgra"))
			color = SPA_VIDEO_FORMAT_BGRA;
		else if (!strcmp(argv[i], "--label") && (int) i + 1 < argc)
			label = argv[++i];
		else
		{
			fprintf(stderr,
			        "usage: %s --output PREFISSO --ready FILE --scene-signal FILE\n"
			        "        [--width W] [--height H] [--fps N] [--bgra] [--dmabuf]\n"
			        "        [--post-scene S] [--discard N] [--duration S] [--wait-scene S]\n"
			        "        [--min-after-scene N] [--label T] [--node N]\n",
			        argv[0]);
			return 2;
		}
	}
	if (!output || !ready || !scene_signal)
	{
		fprintf(stderr, "⛔ --output, --ready and --scene-signal are needed.\n"
		                "   The --ready file tells whoever launches that the virtual monitor is there and\n"
		                "   that the scene can be switched on; the --scene-signal file is the\n"
		                "   answer: «the scene is on».  Without these two the order between\n"
		                "   monitor and scene would go back to being a timed wait.\n");
		return 2;
	}

	first_file = g_strdup_printf("%s-primo.raw", output);
	file_regime = g_strdup_printf("%s-regime.raw", output);
	file_json = g_strdup_printf("%s.json", output);

	now_epoch = time(NULL);
	gmtime_r(&now_epoch, &now_tm);
	strftime(when, sizeof when, "%Y-%m-%dT%H:%M:%SZ", &now_tm);

	p.wants_dmabuf = wants_dmabuf;

	fprintf(stderr, "== %s: requested %ux%u, %s, ceiling %u fps, road %s ==\n", label, width,
	        height, color_name(color), fps, wants_dmabuf ? "DMA-BUF" : "memory");

	if (node == 0)
	{
		stage = stage_mount(width, height, &mistake);
		if (!stage)
		{
			fprintf(stderr, "⛔ virtual monitor not mounted: %s\n", mistake->message);
			return 1;
		}
		node = stage->node;
	}

	pw_init(NULL, NULL);
	p.cycle = pw_thread_loop_new("presa", NULL);
	p.context = pw_context_new(pw_thread_loop_get_loop(p.cycle), NULL, 0);
	pw_thread_loop_lock(p.cycle);
	if (pw_thread_loop_start(p.cycle) < 0)
	{
		pw_thread_loop_unlock(p.cycle);
		fprintf(stderr, "⛔ PipeWire thread not started\n");
		stage_unmount(stage);
		return 1;
	}
	p.core = pw_context_connect(p.context, NULL, 0);
	if (!p.core)
	{
		pw_thread_loop_unlock(p.cycle);
		fprintf(stderr, "⛔ connection to PipeWire failed\n");
		stage_unmount(stage);
		return 1;
	}
	p.stream = pw_stream_new(p.core, "02-capture-frame",
	                         pw_properties_new(PW_KEY_MEDIA_TYPE, "Video", PW_KEY_MEDIA_CATEGORY,
	                                           "Capture", PW_KEY_MEDIA_ROLE, "Screen", NULL));
	pw_stream_add_listener(p.stream, &p.hook, &events, &p);

	if (wants_dmabuf)
		parameters[n_parameters++] = format_dmabuf(&builder, width, height, fps, color);
	parameters[n_parameters++] = shm_format(&builder, width, height, fps, color);

	if (pw_stream_connect(p.stream, PW_DIRECTION_INPUT, node,
	                      PW_STREAM_FLAG_AUTOCONNECT | PW_STREAM_FLAG_MAP_BUFFERS |
	                          PW_STREAM_FLAG_RT_PROCESS,
	                      parameters, n_parameters) < 0)
	{
		pw_thread_loop_unlock(p.cycle);
		fprintf(stderr, "⛔ hooking onto node %u failed\n", node);
		stage_unmount(stage);
		return 1;
	}
	expiry = g_get_monotonic_time() + (gint64) WAIT_STARTUP_S * G_USEC_PER_SEC;
	while (p.state != PW_STREAM_STATE_PAUSED && p.state != PW_STREAM_STATE_STREAMING &&
	       p.state != PW_STREAM_STATE_ERROR && g_get_monotonic_time() < expiry)
		pw_thread_loop_timed_wait(p.cycle, 1);
	pw_thread_loop_unlock(p.cycle);

	if (p.state == PW_STREAM_STATE_ERROR)
	{
		printf("GUASTO\t%s\tcapture refused\n", label);
		fprintf(stderr, "⛔ FAILED: capture refused: %s\n",
		        p.fault ? p.fault : "without explanation");
		stage_unmount(stage);
		return 2;
	}

	/* ⛔ The «ready» file is written ONLY when the stream is really active.
	 *    Writing it before would mean switching the scene on on a monitor that
	 *    does not exist yet, and the scene would open on nothing — which is precisely
	 *    the order phase 0's `banco.sh` had had to learn. */
	expiry = g_get_monotonic_time() + (gint64) WAIT_STARTUP_S * G_USEC_PER_SEC;
	while (p.state != PW_STREAM_STATE_STREAMING && g_get_monotonic_time() < expiry)
		g_usleep(20000);
	if (p.state != PW_STREAM_STATE_STREAMING)
	{
		printf("GUASTO\t%s\tstream never active\n", label);
		fprintf(stderr,
		        "⛔ FAILED (not «zero»): the stream never became active.\n"
		        "   final state %d%s%s.  There is no frame to judge here:\n"
		        "   capture never started (LESSONS.md §1.9).\n",
		        (int) p.state, p.fault ? ", fault: " : "", p.fault ? p.fault : "");
		stage_unmount(stage);
		return 2;
	}
	if (!g_file_set_contents(ready, "ready\n", -1, &mistake))
	{
		fprintf(stderr, "⛔ I cannot write %s: %s\n", ready, mistake->message);
		stage_unmount(stage);
		return 1;
	}
	fprintf(stderr, "  pronto: the scene can be switched on now\n");

	/* Wait for whoever launches to declare the scene on.  ⛔ And if it never arrives
	 * nothing is measured anyway: it is declared.  A scene that does not start and a
	 * silent compositor look the same — item 8 of
	 * `PHASES.md` §00-ambiente, and the third face of one same defect. */
	expiry = g_get_monotonic_time() + (gint64) (wait_scene * G_USEC_PER_SEC);
	while (!g_file_test(scene_signal, G_FILE_TEST_EXISTS) && g_get_monotonic_time() < expiry)
		g_usleep(50000);
	if (!g_file_test(scene_signal, G_FILE_TEST_EXISTS))
	{
		printf("GUASTO\t%s\tthe scene was never declared on\n", label);
		fprintf(stderr,
		        "⛔ FAILED: after %.1f s nobody declared the scene on (%s).\n"
		        "   A frame taken now would be the empty desktop under\n"
		        "   the scene's label: two different things under the same name.\n",
		        wait_scene, scene_signal);
		stage_unmount(stage);
		return 2;
	}
	p.t_scene = g_get_monotonic_time();
	p.t_regime = p.t_scene + (gint64) (post_scene * G_USEC_PER_SEC);
	p.skip_left = discard;
	p.scene_alive = TRUE;
	fprintf(stderr, "  scene declared on: the steady state starts in %.1f s\n", post_scene);

	fine = p.t_scene + (gint64) (duration * G_USEC_PER_SEC);
	while (g_get_monotonic_time() < fine)
		g_usleep(50000);

	/* ⛔ «It WAS active» is not «it still is»: death midway through the measurement. */
	if (p.state != PW_STREAM_STATE_STREAMING)
	{
		printf("GUASTO\t%s\tstream dropped during the take\n", label);
		fprintf(stderr,
		        "⛔ FAILED (not «zero»): the stream was active and dropped.\n"
		        "   final state %d%s%s.  Frames arrived before dropping: %" PRIu64 ".\n",
		        (int) p.state, p.fault ? ", fault: " : "", p.fault ? p.fault : "", p.incoming);
		stage_unmount(stage);
		return 2;
	}

	/* ⛔ THE ROAD IS CHECKED, IT IS NOT TAKEN AS ASKED FOR — `LESSONS.md` §1.8. */
	if (wants_dmabuf && p.how_many_types > 0 && p.seen_types[0] != SPA_DATA_DmaBuf)
	{
		printf("GUASTO\t%s\tDMA-BUF requested, memory obtained\n", label);
		fprintf(stderr,
		        "⛔ FAILED: DMA-BUF was requested and the producer delivered %s.\n"
		        "   No silent fallback (LESSONS.md §1.8, corollary).\n",
		        type_name(p.seen_types[0]));
		stage_unmount(stage);
		return 2;
	}

	/*
	 * ⛔ A LIVE SCENE AND ZERO FRAMES IS NOT A ZERO: IT IS A FAULT.
	 *
	 * Found on 12 Aug 2026, at the FIRST real round of this bench, and found
	 * because the bench came out **GREEN** while the defect was alive — that is the
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
	 *   check of `LESSONS.md` §1.1 — *«how much the client draws, counted
	 *   next to how much capture delivers: without it, a ceiling of the scene gets
	 *   attributed to the compositor, and vice versa»*.
	 *
	 * ⚠ Whoever wants to measure the legitimate zero — the still desktop — passes
	 *   `--min-after-scene 0` and declares it.  It is not obtained by chance.
	 */
	if (p.scene_alive && p.after_scene < min_after_scene)
	{
		printf("GUASTO\t%s\tlive scene and %" PRIu64 " frames after\n", label,
		       p.after_scene);
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
		        p.after_scene, min_after_scene, p.before_scene);
		stage_unmount(stage);
		return 2;
	}

	/* --- the writing --------------------------------------------------- */
	if (p.incoming == 0)
	{
		/* ⭐ LEGITIMATE ZERO, and it is told from failure with exit 3.
		 *    The stream was active for the whole take: if no frame
		 *    arrived, the desktop did not change — which on Mutter is the
		 *    declared behaviour, not a fault (trap 8). */
		outcome = "ZERO FRAMES";
		code = 3;
	}
	else if (wants_dmabuf)
	{
		/* ⛔ WITH DMA-BUF THE PIXELS ARE NOT READ FROM HERE, AND IT IS SAID.
		 *    The descriptor lives on the card: reading it would mean
		 *    importing it, that is half the stage.  This round serves to DECLARE
		 *    the buffer type, not to judge the image, and a `.raw` written
		 *    from here would be empty under the label of a frame. */
		outcome = "TYPE DECLARED, PIXELS NOT READ (dmabuf)";
		code = 0;
	}
	else if (!p.regime.taken && !p.first.taken)
	{
		printf("GUASTO\t%s\tframes arrived but none copyable\n", label);
		fprintf(stderr,
		        "⛔ FAILED: %" PRIu64 " frames arrived and none had mapped\n"
		        "   pixels (null data or empty chunk).  It is not a zero: it is a buffer\n"
		        "   that could not be read.\n",
		        p.incoming);
		stage_unmount(stage);
		return 2;
	}
	else
	{
		outcome = "ONE FRAME";
		code = 0;
		if (p.first.taken && !write_raw(first_file, &p.first, &mistake))
		{
			fprintf(stderr, "⛔ I cannot write %s: %s\n", first_file, mistake->message);
			stage_unmount(stage);
			return 1;
		}
		if (p.regime.taken && !write_raw(file_regime, &p.regime, &mistake))
		{
			fprintf(stderr, "⛔ I cannot write %s: %s\n", file_regime, mistake->message);
			stage_unmount(stage);
			return 1;
		}
	}

	manifesto = g_string_new("{\n");
	g_string_append_printf(manifesto,
	                       "  \"strumento\": \"02-capture-frame\",\n"
	                       "  \"label\": \"%s\",\n"
	                       "  \"when_utc\": \"%s\",\n"
	                       "  \"nodo_pipewire\": %u,\n"
	                       "  \"outcome\": \"%s\",\n"
	                       "  \"exit\": %d,\n",
	                       label, when, node, outcome, code);
	g_string_append_printf(manifesto,
	                       "  \"requested\": {\n"
	                       "    \"width\": %u, \"height\": %u, \"fps_massimi\": %u,\n"
	                       "    \"color\": \"%s\", \"route\": \"%s\",\n"
	                       "    \"cadenza\": \"0/1 with maxFramerate at %u — «send me a frame "
	                       "when something changes»\"\n"
	                       "  },\n",
	                       width, height, fps, color_name(color),
	                       wants_dmabuf ? "dmabuf" : "memory", fps);
	g_string_append_printf(manifesto,
	                       "  \"negotiated\": {\n"
	                       "    \"known\": %s,\n"
	                       "    \"width\": %u, \"height\": %u,\n"
	                       "    \"color\": \"%s\",\n"
	                       "    \"modifier\": \"0x%" PRIx64 "\",\n"
	                       "    \"claimed_by\": \"PipeWire, SPA_PARAM_Format in the param_changed "
	                       "callback — it is not the label we gave it\"\n"
	                       "  },\n",
	                       p.known_format ? "true" : "false", p.fmt.size.width,
	                       p.fmt.size.height, color_name(p.fmt.format),
	                       (uint64_t) p.fmt.modifier);

	/* ⛔ THE THREE THINGS F2.3 ASKS TO BE DECLARED — asked of the producer, not
	 *    deduced, and written as it answers, «I do not declare it» included. */
	g_string_append_printf(
	    manifesto,
	    "  \"delivery_to_F2_3\": {\n"
	    "    \"bits_per_channel\": %d,\n"
	    "    \"bits_per_channel_claimed_by\": \"the negotiated FORMAT (%s). "
	    "STUDIES.md §gnome §8.3 [R]: Mutter delivers ONLY BGRx and BGRA, which are 8 bits per "
	    "channel — from this capture ten real bits do NOT come out\",\n"
	    "    \"⛔ F2.3-A\": \"an HEVC Main10 fed from here carries 8 bits promoted to "
	    "10: the label says Main10, the image comes out fine anyway, and the defendant is "
	    "THE CAPTURE, not the encoder\",\n"
	    "    \"range\": \"%s\",\n"
	    "    \"matrix\": \"%s\",\n"
	    "    \"transfer\": \"%s\",\n"
	    "    \"primaries\": \"%s\",\n"
	    "    \"claimed_by\": \"spa_video_info_raw.color_range / .color_matrix / "
	    ".transfer_function / .color_primaries, filled by "
	    "spa_format_video_raw_parse on the producer's SPA_PARAM_Format\",\n"
	    "    \"⚠ sulla matrice\": \"at capture the pixels are RGB: no "
	    "601/709 matrix was applied by us. The matrix is CHOSEN by F2.3 when converting "
	    "to YCbCr, and F2.6 must compare with the same one — a comparison made with the "
	    "wrong matrix measures the matrix\",\n"
	    "    \"raw_values\": {\"color_range\": %u, \"color_matrix\": %u, "
	    "\"transfer_function\": %u, \"color_primaries\": %u}\n"
	    "  },\n",
	    bit_per_channel(p.fmt.format), color_name(p.fmt.format),
	    range_name(p.fmt.color_range), matrix_name(p.fmt.color_matrix),
	    transfer_name(p.fmt.transfer_function),
	    primaries_name(p.fmt.color_primaries), p.fmt.color_range,
	    p.fmt.color_matrix, p.fmt.transfer_function, p.fmt.color_primaries);

	g_string_append(manifesto, "  \"buffer\": {\n    \"types_seen\": [");
	for (i = 0; i < p.how_many_types; i++)
		g_string_append_printf(manifesto, "%s\"%s\"", i ? ", " : "", type_name(p.seen_types[i]));
	g_string_append_printf(manifesto,
	                       "],\n"
	                       "    \"distinct_recycled\": %u,\n"
	                       "    \"claimed_by\": \"PipeWire, spa_data.type of plane 0 of every "
	                       "buffer — asked for in two places (format and SPA_PARAM_Buffers)\"\n"
	                       "  },\n",
	                       p.how_many_fd);

	g_string_append_printf(manifesto,
	                       "  \"frames\": {\n"
	                       "    \"required_minimum_after_scene\": %" PRIu64 ",\n"
	                       "    \"arrived_total\": %" PRIu64 ",\n"
	                       "    \"before_scene\": %" PRIu64 ",\n"
	                       "    \"after_scene\": %" PRIu64 ",\n"
	                       "    \"full_damage\": %" PRIu64 ",\n"
	                       "    \"partial_damage\": %" PRIu64 ",\n"
	                       "    \"missing_damage\": %" PRIu64 ",\n"
	                       "    \"without_header\": %" PRIu64 "\n"
	                       "  },\n",
	                       min_after_scene, p.incoming, p.before_scene, p.after_scene,
	                       p.full_damage, p.partial_damage, p.missing_damage, p.without_header);

	manifest_still(manifesto, "first", &p.first, first_file);
	manifest_still(manifesto, "steady", &p.steady, file_regime);

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
	                "a discovery about the compositor. LESSONS.md §1.11.\",\n"
	                "    \"⛔ E1 — nor the opposite: a DMA-BUF does not prove rendering on the "
	                "GPU. An open render node is necessary, not sufficient.\",\n"
	                "    \"⚠ this tool does NOT measure rate: it copies two frames inside the "
	                "real-time callback, and a frames-per-second number that came out "
	                "of here would be skewed by us. Rate belongs to phase 0 (36 ± 2) and "
	                "phase 3.\",\n"
	                "    \"⚠ 'negotiated' and 'requested' are two different fields on purpose: item "
	                "12-bis of PHASES.md §00-ambiente is a label that declared a size that "
	                "the compositor had never honoured.\"\n"
	                "  ]\n}\n");

	if (!g_file_set_contents(file_json, manifesto->str, -1, &mistake))
	{
		fprintf(stderr, "⛔ I cannot write %s: %s\n", file_json, mistake->message);
		g_string_free(manifesto, TRUE);
		stage_unmount(stage);
		return 1;
	}
	g_string_free(manifesto, TRUE);

	printf("PRESA\t%s\t%s\t%s\t%" PRIu64 "\t%" PRIu64 "\t%s\n", label, outcome, file_json,
	       p.incoming, p.after_scene,
	       p.how_many_types > 0 ? type_name(p.seen_types[0]) : "NONE");
	fprintf(stderr,
	        "  outcome: %s\n"
	        "  arrived %" PRIu64 " (before the scene %" PRIu64 ", after %" PRIu64 ")\n"
	        "  damage: full %" PRIu64 ", partial %" PRIu64 ", absent %" PRIu64 "\n"
	        "  distinct recycled buffers: %u\n"
	        "  manifest: %s\n",
	        outcome, p.incoming, p.before_scene, p.after_scene, p.full_damage,
	        p.partial_damage, p.missing_damage, p.how_many_fd, file_json);

	pw_thread_loop_lock(p.cycle);
	pw_stream_disconnect(p.stream);
	pw_stream_destroy(p.stream);
	pw_thread_loop_unlock(p.cycle);
	pw_thread_loop_stop(p.cycle);
	pw_core_disconnect(p.core);
	pw_context_destroy(p.context);
	pw_thread_loop_destroy(p.cycle);
	stage_unmount(stage);
	g_free(p.first.pixel);
	g_free(p.regime.pixel);
	g_free(p.fault);
	return code;
}
