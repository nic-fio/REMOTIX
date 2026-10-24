/*
 * kwin — see `kwin.h`.  Carried over from v1's `fondamenta/remotix-c/src/kwin.c`:
 * the comments citing `kde.md` refer to the study of KWin's code, today
 * in `STUDIES.md` (from line ~1233, § numbering unchanged).
 */
#include "kwin.h"

#include <errno.h>
#include <fcntl.h>
#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include <glib-unix.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <sys/prctl.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>
#include <wayland-client.h>

#include "wlr-layer-shell-unstable-v1-client-protocol.h"
#include "zkde-screencast-unstable-v1-client-protocol.h"

#include "log.h"
#include "session.h"
#include "wlroots.h"

#define AREA "capture"

/* How long to wait for KWin to answer `created` or `failed`.  A ceiling is needed:
 * `failed` is sent SYNCHRONOUSLY inside the request handler
 * (`screencastmanager.cpp:82`), so whoever misses it waits forever. */
#define WAIT_NODE_MS 5000

/* The cursor mode, from the protocol's enum: 1 hidden, 2 drawn into the
 * buffer, 4 as metadata.
 *
 * ⛔ IT IS DECIDED ONCE ONLY and cannot be changed on a live stream
 *    (`screencaststream.cpp:915-918`).  METADATA as on Mutter (`cursor-mode=2`
 *    in `mutter.c`): the page draws the cursor.
 * ⛔ THE PRICE IS IN `capture.c`: every pointer movement produces a
 *    buffer with no new pixels marked `SPA_CHUNK_FLAG_CORRUPTED` (`kde.md`
 *    §4.7), and `capture.c` already discards them. */
#define POINTER_METADATA 4

#define MAX_OUTPUTS 8

/* The path of the permission: system-wide, because it applies to every user, and
 * KWin looks in `XDG_DATA_DIRS` (which contains `/usr/share`).  Since phase 17 the
 * package ships it and REMOTIX only checks it (`kwin_check_permission`). */
#define PERMISSION_DESKTOP_FILE "/usr/share/applications/org.kde.remotix.desktop"

typedef struct
{
	struct wl_output *object;
	uint32_t global_name;
	uint32_t version;
	char *name; /* "WL-0" nested (`[M]` 11 Oct 2026), "Virtual-0" with `--virtual` */
	uint32_t width, height; /* of the CURRENT mode, in pixels */
} OutDir;

struct KwinSession
{
	struct wl_display *display;
	struct wl_registry *registry;
	struct zkde_screencast_unstable_v1 *screencast;
	struct zkde_screencast_stream_unstable_v1 *stream;
	uint32_t screencast_version;

	OutDir outputs[MAX_OUTPUTS];
	unsigned how_many_outputs;
	const OutDir *choice;

	uint32_t node;
	bool node_arrived;
	bool refused;
	char *refusal_reason;
	volatile bool closed;

	/* ⛔ THE LOOP THAT KEEPS THE CONNECTION ALIVE IS NOT A LUXURY: the stream lives
	 *    as long as the Wayland connection (`screencast_v1.cpp:28-35`), and a
	 *    connection nobody serves does not deliver `closed`. */
	GThread *pump;
	int wake[2];

	/* The input channel: the descriptor and the token of `connectToEIS`. */
	int eis;
	gint eis_token;
	bool known_token;

	/* The pixel that keeps full-screen windows composited (`put_pixel()`). */
	struct wl_compositor *compositor;
	struct wl_shm *shm;
	struct zwlr_layer_shell_v1 *layers;
	struct wl_surface *pixel_surface;
	struct zwlr_layer_surface_v1 *pixel_layer;
	struct wl_buffer *pixel_buf;
	bool pixel_configured;
};

/* ------------------------------------------------------------------ *
 * The registry
 * ------------------------------------------------------------------ */
static void on_output_geometry(void *data, struct wl_output *output, int32_t x, int32_t y,
                                int32_t width_mm, int32_t height_mm, int32_t subpixel,
                                const char *builder, const char *model,
                                int32_t transform)
{
}

static void on_output_mode(void *data, struct wl_output *object, uint32_t flag,
                           int32_t width, int32_t height, int32_t update)
{
	OutDir *output = data;

	if (!(flag & WL_OUTPUT_MODE_CURRENT))
		return;
	output->width = (uint32_t)MAX(0, width);
	output->height = (uint32_t)MAX(0, height);
}

static void on_output_end(void *data, struct wl_output *object)
{
}

static void on_output_scale(void *data, struct wl_output *object, int32_t scale_factor)
{
	/* The scale does not touch the buffer's pixels (`core/output.cpp:457-459`), but
	 * it shifts the input coordinate space: it is logged. */
	if (scale_factor != 1)
		registro_dice(AREA, "⚠ KWin's output has scale %d: the logical desktop is "
		                    "smaller than the captured buffer", scale_factor);
}

static void on_output_name(void *data, struct wl_output *object, const char *name)
{
	OutDir *output = data;

	g_free(output->name);
	output->name = g_strdup(name);
}

static void on_output_description(void *data, struct wl_output *object,
                                  const char *description)
{
}

static const struct wl_output_listener kwin_output_listener = {
	on_output_geometry, on_output_mode, on_output_end,
	on_output_scale,     on_output_name, on_output_description,
};

static void on_global(void *data, struct wl_registry *registry, uint32_t name,
                       const char *interfaccia, uint32_t version)
{
	KwinSession *session = data;

	if (!strcmp(interfaccia, zkde_screencast_unstable_v1_interface.name)) {
		/* KWin 6.3.6 announces 5; the clamp because a newer KWin would
		 * announce one our XML does not describe. */
		session->screencast_version = MIN(version, 5u);
		session->screencast =
		    wl_registry_bind(registry, name, &zkde_screencast_unstable_v1_interface,
		                     session->screencast_version);
	} else if (!strcmp(interfaccia, wl_compositor_interface.name)) {
		session->compositor = wl_registry_bind(registry, name, &wl_compositor_interface,
		                                        MIN(version, 4u));
	} else if (!strcmp(interfaccia, wl_shm_interface.name)) {
		session->shm = wl_registry_bind(registry, name, &wl_shm_interface, 1);
	} else if (!strcmp(interfaccia, zwlr_layer_shell_v1_interface.name)) {
		session->layers = wl_registry_bind(registry, name, &zwlr_layer_shell_v1_interface,
		                                    MIN(version, 1u));
	} else if (!strcmp(interfaccia, wl_output_interface.name)) {
		OutDir *output;

		if (session->how_many_outputs >= MAX_OUTPUTS) {
			registro_dice(AREA, "⚠ more than %d outputs: the others are ignored",
			              MAX_OUTPUTS);
			return;
		}
		output = &session->outputs[session->how_many_outputs++];
		output->global_name = name;
		/* Version 4: the one that carries the `name` event. */
		output->version = MIN(version, 4u);
		output->object =
		    wl_registry_bind(registry, name, &wl_output_interface, output->version);
		wl_output_add_listener(output->object, &kwin_output_listener, output);
	}
}

static void on_global_away(void *data, struct wl_registry *registry, uint32_t name)
{
	KwinSession *session = data;

	for (unsigned i = 0; i < session->how_many_outputs; i++)
		if (session->outputs[i].global_name == name)
			registro_dice(AREA, "⚠ output «%s» has disappeared from the compositor",
			              session->outputs[i].name ? session->outputs[i].name
			                                       : "unnamed");
}

static const struct wl_registry_listener registry_listener = { on_global, on_global_away };

/* ------------------------------------------------------------------ *
 * The stream
 * ------------------------------------------------------------------ */
static void on_stream_closed(void *data, struct zkde_screencast_stream_unstable_v1 *stream)
{
	KwinSession *session = data;

	/* Just mark it: the stage notices on its own, because the
	 * PipeWire node disappears and the capture goes to `UNCONNECTED`. */
	session->closed = true;
	registro_dice(AREA, "KWin closed the capture stream");
}

static void on_stream_created(void *data, struct zkde_screencast_stream_unstable_v1 *stream,
                             uint32_t node)
{
	KwinSession *session = data;

	session->node = node;
	session->node_arrived = true;
}

static void on_stream_fault(void *data, struct zkde_screencast_stream_unstable_v1 *stream,
                             const char *error)
{
	KwinSession *session = data;

	session->refused = true;
	g_free(session->refusal_reason);
	session->refusal_reason = g_strdup(error);
}

static const struct zkde_screencast_stream_unstable_v1_listener screencast_listener = {
	on_stream_closed, on_stream_created, on_stream_fault
};

/* ------------------------------------------------------------------ *
 * The loop
 * ------------------------------------------------------------------ */
/* One round of events with a deadline: `wl_display_dispatch` alone would block
 * without a ceiling.  false if the connection dropped or we were stopped. */
static bool runs(KwinSession *session, int wait_ms)
{
	struct pollfd probe[2];
	int amount = 1;

	while (wl_display_prepare_read(session->display) != 0)
		if (wl_display_dispatch_pending(session->display) < 0)
			return false;
	if (wl_display_flush(session->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(session->display);
		return false;
	}

	probe[0].fd = wl_display_get_fd(session->display);
	probe[0].events = POLLIN;
	probe[0].revents = 0;
	if (session->wake[0] >= 0) {
		probe[1].fd = session->wake[0];
		probe[1].events = POLLIN;
		probe[1].revents = 0;
		amount = 2;
	}

	if (poll(probe, (nfds_t)amount, wait_ms) <= 0) {
		wl_display_cancel_read(session->display);
		return true;
	}
	if (amount == 2 && (probe[1].revents & POLLIN)) {
		wl_display_cancel_read(session->display);
		return false;
	}
	if (!(probe[0].revents & POLLIN)) {
		wl_display_cancel_read(session->display);
		return !(probe[0].revents & (POLLERR | POLLHUP));
	}

	if (wl_display_read_events(session->display) < 0)
		return false;
	return wl_display_dispatch_pending(session->display) >= 0;
}

static gpointer thread_pump(gpointer data)
{
	KwinSession *session = data;

	while (runs(session, -1))
		;
	/* ⛔ AND IT IS MARKED — `[M]` 19 Sep 2026, the user's logout on KDE: KWin
	 *    dies with the session WITHOUT closing the stream gracefully, so
	 *    `on_stream_closed` does not arrive; and the PipeWire node disappearing does NOT
	 *    put the capture in error — the grab returns "zero" forever, like
	 *    a still scene.  ⇒ The connection dropping is the only sign, and
	 *    the child reads it with `kwin_closed()`. */
	session->closed = true;
	registro_dice(AREA, "the Wayland connection to KWin has closed: the compositor "
	                    "is gone");
	return NULL;
}

/* ------------------------------------------------------------------ *
 * Opening
 * ------------------------------------------------------------------ */
/* ⛔ The socket cannot be remembered: it is the first free `wayland-N`, and the
 *    child is born with an environment built from scratch (`WAYLAND_DISPLAY` is absent).
 *    ⇒ They are tried in order inside `XDG_RUNTIME_DIR`. */
struct wl_display *kwin_display_open(char *which, size_t how_much)
{
	const char *claimed = getenv("WAYLAND_DISPLAY");
	const char *runtime = getenv("XDG_RUNTIME_DIR");

	if (claimed && *claimed) {
		struct wl_display *display = wl_display_connect(claimed);

		if (display) {
			snprintf(which, how_much, "%s", claimed);
			return display;
		}
	}
	for (int i = 0; i < 10; i++) {
		char name[32], fpath[512];
		struct wl_display *display;

		snprintf(name, sizeof name, "wayland-%d", i);
		if (runtime) {
			snprintf(fpath, sizeof fpath, "%s/%s", runtime, name);
			if (access(fpath, F_OK) != 0)
				continue;
		}
		display = wl_display_connect(name);
		if (display) {
			snprintf(which, how_much, "%s", name);
			return display;
		}
	}
	return NULL;
}

/* There is a single output (nested or `--virtual`); the first that has a mode is taken. */
static const OutDir *choose_output(const KwinSession *session)
{
	for (unsigned i = 0; i < session->how_many_outputs; i++)
		if (session->outputs[i].width && session->outputs[i].height)
			return &session->outputs[i];
	return NULL;
}

/* The gate is closed: say WHY, because the symptom does not say it.  The
 * missing global has two causes with opposite cures, and KWin tells them apart only in
 * its own log (`QT_LOGGING_RULES='KWIN_UTILS.debug=true'`). */
static void explain_gate(GError **mistake)
{
	g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_PERMISSION_DENIED,
	            "KWin does not announce zkde_screencast_unstable_v1: the capture permission "
	            "is denied, it is not the protocol that is missing. Our .desktop %s (%s). And "
	            "KWin's environment must have XDG_MENU_PREFIX=plasma-, or the service "
	            "index is built empty. KWin gives the exact cause with "
	            "QT_LOGGING_RULES='KWIN_UTILS.debug=true'",
	            access(PERMISSION_DESKTOP_FILE, F_OK) == 0 ? "is there" : "is NOT there", PERMISSION_DESKTOP_FILE);
}

/*
 * ⛔⭐ THE PIXEL ON TOP — `[M]` 11 Oct 2026, nested KWin 6.3.6: F-008 BLOCKED twice
 *     (the letters reached the session's kiosk Firefox, the photo stayed
 *     still), green with `--virtual`.  `[R]` `compositor_wayland.cpp:403-421`: a
 *     FULL-SCREEN window with the pointer hidden (an application that hides it
 *     while typing, or a video player) is handed to the host as it is (direct
 *     scanout); KWin then composites nothing, and the stream is built from
 *     `textureForOutput()`, which in the nested backend is the LAST COMPOSITED
 *     frame (`wayland_egl_backend.cpp`, `texture()` = the swapchain's buffer)
 *     ⇒ the picture freezes while the application lives.  `--virtual` never
 *     scans out, so it never had this.
 * ⇒ `[R]` `workspacescene.cpp:200-230`: there is no scanout if, above the
 *    full-screen window, there is ANY visible window that is not full screen.
 *    One transparent pixel in KWin's overlay layer, with no input, is that
 *    window: KWin composites as with `--virtual`, and nothing is seen.  It lives
 *    on the capture's own connection — it is needed exactly while we capture.
 */
static void pixel_configure(void *d, struct zwlr_layer_surface_v1 *s, uint32_t serial,
                            uint32_t l, uint32_t a)
{
	KwinSession *session = d;

	zwlr_layer_surface_v1_ack_configure(s, serial);
	if (!session->pixel_configured && session->pixel_buf) {
		wl_surface_attach(session->pixel_surface, session->pixel_buf, 0, 0);
		wl_surface_damage_buffer(session->pixel_surface, 0, 0, 1, 1);
	}
	wl_surface_commit(session->pixel_surface);
	session->pixel_configured = true;
}
static void pixel_closed(void *d, struct zwlr_layer_surface_v1 *s)
{
	registro_dice(AREA, "⚠ KWin closed our pixel on top: full-screen windows may be "
	                    "scanned out again, and their picture freeze");
}
static const struct zwlr_layer_surface_v1_listener PIXEL_LISTENER = { pixel_configure,
	                                                              pixel_closed };

static void put_pixel(KwinSession *session)
{
	struct wl_shm_pool *pool;
	struct wl_region *blank;
	int fd;

	if (!session->compositor || !session->shm || !session->layers) {
		registro_dice(AREA, "⚠ KWin does not announce %s: no pixel on top — a "
		                    "full-screen window with the pointer hidden may freeze",
		              !session->layers ? "zwlr_layer_shell_v1" : "wl_compositor/wl_shm");
		return;
	}
	fd = memfd_create("remotix-pixel", MFD_CLOEXEC);
	if (fd < 0 || ftruncate(fd, 4) != 0) {
		if (fd >= 0)
			close(fd);
		return;
	}
	pool = wl_shm_create_pool(session->shm, fd, 4);
	session->pixel_buf = wl_shm_pool_create_buffer(pool, 0, 1, 1, 4, WL_SHM_FORMAT_ARGB8888);
	wl_shm_pool_destroy(pool);
	close(fd);
	session->pixel_surface = wl_compositor_create_surface(session->compositor);
	blank = wl_compositor_create_region(session->compositor);
	wl_surface_set_input_region(session->pixel_surface, blank);
	wl_region_destroy(blank);
	session->pixel_layer = zwlr_layer_shell_v1_get_layer_surface(
	    session->layers, session->pixel_surface, NULL, ZWLR_LAYER_SHELL_V1_LAYER_OVERLAY,
	    "remotix-pixel");
	zwlr_layer_surface_v1_add_listener(session->pixel_layer, &PIXEL_LISTENER, session);
	zwlr_layer_surface_v1_set_size(session->pixel_layer, 1, 1);
	zwlr_layer_surface_v1_set_anchor(session->pixel_layer, ZWLR_LAYER_SURFACE_V1_ANCHOR_TOP |
	                                                             ZWLR_LAYER_SURFACE_V1_ANCHOR_LEFT);
	zwlr_layer_surface_v1_set_exclusive_zone(session->pixel_layer, -1);
	wl_surface_commit(session->pixel_surface);
}

KwinSession *kwin_open(GError **mistake)
{
	KwinSession *session = g_new0(KwinSession, 1);
	char socket[64] = "";
	gint64 expiry;

	session->wake[0] = session->wake[1] = -1;
	session->eis = -1;

	session->display = kwin_display_open(socket, sizeof socket);
	if (!session->display) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no Wayland compositor reachable in XDG_RUNTIME_DIR=%s",
		            getenv("XDG_RUNTIME_DIR") ? getenv("XDG_RUNTIME_DIR") : "(not set)");
		goto fault;
	}

	session->registry = wl_display_get_registry(session->display);
	wl_registry_add_listener(session->registry, &registry_listener, session);
	/* Two rounds: the globals, then the events of the globals just bound (mode, name). */
	wl_display_roundtrip(session->display);
	wl_display_roundtrip(session->display);

	if (!session->screencast) {
		explain_gate(mistake);
		goto fault;
	}

	session->choice = choose_output(session);
	if (!session->choice) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "KWin has no output with a mode (%u announced): without a "
		            "virtual screen KWin swallows the input too (kde.md §10.3)",
		            session->how_many_outputs);
		goto fault;
	}

	/* ⛔ THE LISTENER RIGHT AFTER THE REQUEST AND BEFORE ANY ROUND: `failed`
	 *    is sent synchronously, and whoever is not listening misses it (`kde.md` §4.4). */
	session->stream = zkde_screencast_unstable_v1_stream_output(
	    session->screencast, session->choice->object, POINTER_METADATA);
	if (!session->stream) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "capture request to KWin not created");
		goto fault;
	}
	zkde_screencast_stream_unstable_v1_add_listener(session->stream, &screencast_listener,
	                                                session);

	expiry = g_get_monotonic_time() + (gint64)WAIT_NODE_MS * 1000;
	while (!session->node_arrived && !session->refused && !session->closed) {
		gint64 stays = (expiry - g_get_monotonic_time()) / 1000;

		if (stays <= 0)
			break;
		if (!runs(session, (int)stays))
			break;
	}

	if (session->refused) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED, "KWin refused the capture: %s",
		            session->refusal_reason ? session->refusal_reason : "no explanation");
		goto fault;
	}
	if (!session->node_arrived) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "KWin did not announce the PipeWire node within %d ms", WAIT_NODE_MS);
		goto fault;
	}

	put_pixel(session);
	{
		gint64 deadline = g_get_monotonic_time() + 1000 * 1000;

		while (session->pixel_layer && !session->pixel_configured &&
		       g_get_monotonic_time() < deadline)
			if (!runs(session, 100))
				break;
	}
	if (!g_unix_open_pipe(session->wake, O_CLOEXEC, NULL)) {
		session->wake[0] = session->wake[1] = -1;
		registro_dice(AREA, "⚠ wake-up pipe not created: closing the capture "
		                    "will be less clean");
	}
	session->pump = g_thread_new("remotix-kwin", thread_pump, session);

	registro_dice(AREA,
	              "⭐ KWin: zkde_screencast v%u on socket «%s», output «%s» %ux%u (%u in "
	              "all), PipeWire node %u; pixel on top %s",
	              session->screencast_version, socket,
	              session->choice->name ? session->choice->name : "unnamed",
	              session->choice->width, session->choice->height,
	              session->how_many_outputs, session->node,
	              session->pixel_configured ? "ON" : "⛔ NOT there");
	return session;

fault:
	kwin_close(session);
	return NULL;
}

uint32_t kwin_node(const KwinSession *session)
{
	return session ? session->node : 0;
}

void kwin_measure(const KwinSession *session, uint32_t *width, uint32_t *height)
{
	*width = (session && session->choice) ? session->choice->width : 0;
	*height = (session && session->choice) ? session->choice->height : 0;
}

const char *kwin_output_name(const KwinSession *session)
{
	if (!session || !session->choice)
		return NULL;
	return session->choice->name;
}

unsigned kwin_output_count(const KwinSession *session)
{
	unsigned n = 0;

	if (!session)
		return 0;
	for (unsigned i = 0; i < session->how_many_outputs; i++)
		if (session->outputs[i].width && session->outputs[i].height)
			n++;
	return n;
}

bool kwin_closed(const KwinSession *session)
{
	return session ? session->closed : true;
}

/* ------------------------------------------------------------------ *
 * The input channel
 * ------------------------------------------------------------------ */
/* Keyboard 1, pointer 2, touch 4 — the xdg portal's mask
 * (`xdg-desktop-portal-kde/src/remotedesktop.cpp:457-460`). */
#define KWIN_EIS_CAPABILITIES 7

static void detach_eis(KwinSession *session)
{
	/* ⛔ With the token: KWin ties the EIS context to the life of the caller's D-Bus
	 *    NAME, so letting it go only works while the process lives — and
	 *    in a recovery the process stays alive, with one device too many. */
	if (session->known_token) {
		GDBusConnection *bus = sess_bus(NULL);

		if (bus) {
			GVariant *r = g_dbus_connection_call_sync(
			    bus, "org.kde.KWin", "/org/kde/KWin/EIS/RemoteDesktop",
			    "org.kde.KWin.EIS.RemoteDesktop", "disconnect",
			    g_variant_new("(i)", session->eis_token), NULL,
			    G_DBUS_CALL_FLAGS_NONE, 2000, NULL, NULL);
			if (r)
				g_variant_unref(r);
			g_object_unref(bus);
		}
		session->known_token = false;
	}
	if (session->eis >= 0) {
		close(session->eis);
		session->eis = -1;
	}
}

static int ask_eis(KwinSession *session, GError **mistake)
{
	GDBusConnection *bus;
	GUnixFDList *descriptors = NULL;
	GVariant *response;
	gint idx = -1;

	bus = sess_bus(mistake);
	if (!bus)
		return -1;
	/* ⛔ THE DESCRIPTOR TRAVELS IN A SEPARATE LIST: `h` is an INDEX into
	 *    that list, and the zero read from the body would be standard input. */
	response = g_dbus_connection_call_with_unix_fd_list_sync(
	    bus, "org.kde.KWin", "/org/kde/KWin/EIS/RemoteDesktop",
	    "org.kde.KWin.EIS.RemoteDesktop", "connectToEIS", g_variant_new("(i)", KWIN_EIS_CAPABILITIES),
	    G_VARIANT_TYPE("(hi)"), G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &descriptors, NULL,
	    mistake);
	g_object_unref(bus);
	if (!response)
		return -1;
	g_variant_get(response, "(hi)", &idx, &session->eis_token);
	g_variant_unref(response);
	session->eis = g_unix_fd_list_get(descriptors, idx, mistake);
	g_object_unref(descriptors);
	if (session->eis < 0)
		return -1;
	session->known_token = true;
	registro_dice(AREA, "⭐ KWin granted the input channel (connectToEIS, token %d, "
	                    "descriptor %d)", session->eis_token, session->eis);
	return session->eis;
}

int kwin_eis_fd(KwinSession *session, GError **mistake)
{
	if (!session) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "no KWin stage");
		return -1;
	}
	if (session->eis >= 0)
		return session->eis;
	return ask_eis(session, mistake);
}

int kwin_eis_reattach(KwinSession *session, GError **mistake)
{
	if (!session) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "no KWin stage");
		return -1;
	}
	detach_eis(session);
	return ask_eis(session, mistake);
}

void kwin_close(KwinSession *session)
{
	if (!session)
		return;

	/* First stop the pump, then touch the display: they are the same object
	 * seen from two threads. */
	if (session->pump) {
		if (session->wake[1] >= 0) {
			ssize_t unknown = write(session->wake[1], "x", 1);

			(void)unknown;
		}
		g_thread_join(session->pump);
		session->pump = NULL;
	}
	if (session->wake[0] >= 0)
		close(session->wake[0]);
	if (session->wake[1] >= 0)
		close(session->wake[1]);

	detach_eis(session);
	if (session->pixel_layer)
		zwlr_layer_surface_v1_destroy(session->pixel_layer);
	if (session->pixel_surface)
		wl_surface_destroy(session->pixel_surface);
	if (session->pixel_buf)
		wl_buffer_destroy(session->pixel_buf);
	if (session->layers)
		zwlr_layer_shell_v1_destroy(session->layers);
	if (session->shm)
		wl_shm_destroy(session->shm);
	if (session->compositor)
		wl_compositor_destroy(session->compositor);
	if (session->stream)
		zkde_screencast_stream_unstable_v1_close(session->stream);
	if (session->screencast)
		zkde_screencast_unstable_v1_destroy(session->screencast);
	for (unsigned i = 0; i < session->how_many_outputs; i++) {
		if (session->outputs[i].object) {
			/* `release` exists since version 3. */
			if (session->outputs[i].version >= 3)
				wl_output_release(session->outputs[i].object);
			else
				wl_output_destroy(session->outputs[i].object);
		}
		g_free(session->outputs[i].name);
	}
	if (session->registry)
		wl_registry_destroy(session->registry);
	if (session->display) {
		wl_display_flush(session->display);
		wl_display_disconnect(session->display);
	}
	g_free(session->refusal_reason);
	g_free(session);
}

/* ------------------------------------------------------------------ *
 * The file that opens the gate
 * ------------------------------------------------------------------ */
/*
 * ⭐ PHASE 17 (§6.5-bis) — the PACKAGE ships the file, REMOTIX CHECKS it.
 *    Until phase 16 the server wrote it as root at every start; now it is a
 *    package file (`packaging/{debian,rpm,arch}`, identical byte for
 *    byte), and a program that rewrites a package file creates TWO truths
 *    about what is installed (`dpkg -V`, `rpm -V` would flag it).
 *    ⇒ Here it is only looked at, and if it is wrong the code and the remedy are given.
 *
 * The model of the file is still `org.kde.krdpserver.desktop` (KDE's RDP server):
 * `Exec=` on the CANONICAL binary, because KWin compares `/proc/<pid>/exe`
 * (`executable_path_proc.cpp:11-14`).  Three checks, one code each:
 *   RX-KDE-001  the file is missing or cannot be read;
 *   RX-KDE-002  `Exec=` does not lead to the running binary (the real path:
 *               `/usr/libexec/remotix/remotix` on deb and rpm,
 *               `/usr/lib/remotix/remotix` on Arch, something else in a bench);
 *   RX-KDE-003  `zkde_screencast_unstable_v1` is missing from X-KDE-Wayland-Interfaces.
 */
static bool exec_leads_to(const char *exec, const char *canonical, char **seen)
{
	char **argv = NULL;
	char *real;
	bool eq_sign;

	if (!g_shell_parse_argv(exec, NULL, &argv, NULL) || !argv || !argv[0]) {
		g_strfreev(argv);
		*seen = g_strdup(exec);
		return false;
	}
	*seen = g_strdup(argv[0]);
	/* CANONICAL paths on both sides, as KWin does: a link
	 * leading to the binary counts as much as the binary. */
	real = realpath(argv[0], NULL);
	eq_sign = real && strcmp(real, canonical) == 0;
	free(real);
	g_strfreev(argv);
	return eq_sign;
}

bool kwin_check_permission(char *why, size_t how_much)
{
	char *canonical = realpath("/proc/self/exe", NULL);
	GKeyFile *keys = g_key_file_new();
	GError *mistake = NULL;
	char *exec = NULL, *interfaces = NULL, *seen = NULL;
	bool va = false;

	if (!canonical) {
		snprintf(why, how_much, "I do not know which binary I am running: %s", strerror(errno));
		goto fine;
	}
	if (!g_key_file_load_from_file(keys, PERMISSION_DESKTOP_FILE, G_KEY_FILE_NONE, &mistake)) {
		snprintf(why, how_much,
		         "RX-KDE-001: %s %s (%s). Remedy: reinstall REMOTIX with the installer",
		         PERMISSION_DESKTOP_FILE,
		         g_error_matches(mistake, G_FILE_ERROR, G_FILE_ERROR_NOENT) ? "is missing"
		                                                                  : "cannot be read",
		         mistake->message);
		goto fine;
	}
	exec = g_key_file_get_string(keys, "Desktop Entry", "Exec", NULL);
	if (!exec || !exec_leads_to(exec, canonical, &seen)) {
		snprintf(why, how_much,
		         "RX-KDE-002: in %s Exec=%s, but the running binary is %s. Remedy: "
		         "reinstall REMOTIX with the installer",
		         PERMISSION_DESKTOP_FILE, seen ? seen : "(missing)", canonical);
		goto fine;
	}
	interfaces = g_key_file_get_string(keys, "Desktop Entry", "X-KDE-Wayland-Interfaces",
	                                   NULL);
	if (interfaces) {
		char **entries = g_strsplit_set(interfaces, ",; \t", -1);

		for (char **v = entries; *v; v++)
			if (strcmp(*v, "zkde_screencast_unstable_v1") == 0)
				va = true;
		g_strfreev(entries);
	}
	if (!va) {
		snprintf(why, how_much,
		         "RX-KDE-003: in %s X-KDE-Wayland-Interfaces=%s, without "
		         "zkde_screencast_unstable_v1. Remedy: reinstall REMOTIX with the installer",
		         PERMISSION_DESKTOP_FILE, interfaces ? interfaces : "(missing)");
		goto fine;
	}
	snprintf(why, how_much, "%s checked (it belongs to the package: I do not write it), Exec=%s",
	         PERMISSION_DESKTOP_FILE, canonical);
fine:
	g_clear_error(&mistake);
	g_key_file_unref(keys);
	g_free(exec);
	g_free(interfaces);
	g_free(seen);
	free(canonical);
	return va;
}

/* ------------------------------------------------------------------ *
 * The keyboard layout — the KWin twin of `input-sources`
 * ------------------------------------------------------------------ */

/*
 * ⭐ PHASE 15, D-008 — `[M]` round 1, 15-f009 on KDE: with the browser in Italian
 *    "è à ò ù é ç ° §" did not come out, the session stayed "English (US)".
 *    `input_layout()` had the GNOME road and the wlroots one, for
 *    KWin none (`STUDIES.md` §kde §6.7 listed it, nobody had written it).
 *
 * `[R]` KWin 6.3.6 — road 3 of §6.7, the only one that REALLY changes the
 *    layout in a live session:
 *   · the keymap comes from `kxkbrc [Layout] LayoutList/VariantList`
 *     (`xkb.cpp:577-603`), opened with `KConfig::NoGlobals`, that is WITH the
 *     `XDG_CONFIG_DIRS` cascade (`main.cpp:138`);
 *   · the signal `org.kde.keyboard /Layouts reloadConfig` (the same one the
 *     Keyboard module of System Settings sends) does `reparseConfiguration()` +
 *     `Xkb::reconfigure()` (`keyboard_layout.cpp:62-68,112-125`);
 *   · and `layoutsReconfigured` rebuilds the EIS keyboard device with the new
 *     keymap (`plugins/eis/eisbackend.cpp:58-67`, `eiscontext.cpp:95-101`)
 *     ⇒ `read_keymap()` in `input.c` rereads it and writes "KEYMAP CAMBIATA",
 *     as on GNOME.  "In force" is said by that line, not this one.
 *   ⛔ Road 1 (`XKB_DEFAULT_*` at KWin start) only applies to the first
 *     login; road 2 (`setLayout`) only chooses among the loaded layouts.
 *
 * ⭐ WHERE: in the session folder (`session_folder_kde()`, already at the
 *    head of `XDG_CONFIG_DIRS`), not in `~/.config/kxkbrc`: it applies to the
 *    remote session and disappears with it, and ⛔ it does not change the keyboard
 *    of whoever sits at the monitor with the same user.
 * ⛔ The two keys with `[$i]`: the user's `kxkbrc` (anyone who has ever
 *    opened the Keyboard module has one) sits higher and would otherwise WIN — the
 *    negotiated layout would not apply precisely to whoever configured their own.  Only
 *    those two: model and options stay theirs.
 */
static bool clean_xkb_name(const char *s, size_t n)
{
	if (n == 0)
		return false;
	for (size_t i = 0; i < n; i++)
		if (!g_ascii_isalnum(s[i]) && s[i] != '_' && s[i] != '-')
			return false;
	return true;
}

int kwin_layout(const char *name, GError **mistake)
{
	g_autofree char *folder = session_folder_kde();
	g_autofree char *kb_layout = NULL;
	g_autofree char *variant = NULL;
	g_autofree char *fpath = NULL;
	g_autofree char *text = NULL;
	g_autoptr(GDBusConnection) bus = NULL;
	const char *par = name ? strchr(name, '(') : NULL;

	if (!name || !*name) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "no name");
		return -1;
	}
	/* `RCP.md` §4.5: `de(neo)` ⇒ LayoutList=de, VariantList=neo.
	 * ⛔ The name ends up inside an INI file: no newline, no `[`. */
	if (par) {
		const char *is_closed = strchr(par + 1, ')');

		if (!is_closed || is_closed[1] != '\0' ||
		    !clean_xkb_name(name, (size_t) (par - name)) ||
		    !clean_xkb_name(par + 1, (size_t) (is_closed - par - 1))) {
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
			            "invalid name «%s»", name);
			return -1;
		}
		kb_layout = g_strndup(name, (size_t) (par - name));
		variant = g_strndup(par + 1, (size_t) (is_closed - par - 1));
	} else {
		if (!clean_xkb_name(name, strlen(name))) {
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
			            "invalid name «%s»", name);
			return -1;
		}
		kb_layout = g_strdup(name);
		variant = g_strdup("");
	}

	/* ⛔ Only if the folder is there: `compose_environment()` creates it and
	 *    puts it in `XDG_CONFIG_DIRS`.  If it is not there, KWin does not read it — and
	 *    writing into it would be a false "fact". */
	if (!folder || !g_file_test(folder, G_FILE_TEST_IS_DIR)) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "the session's configuration folder (%s) is missing: KWin "
		            "does not look at it",
		            folder ? folder : "XDG_RUNTIME_DIR missing");
		return -1;
	}
	fpath = g_build_filename(folder, "kxkbrc", NULL);
	text = g_strdup_printf("[Layout]\n"
	                        "LayoutList[$i]=%s\n"
	                        "VariantList[$i]=%s\n",
	                        kb_layout, variant);
	if (!g_file_set_contents(fpath, text, -1, mistake))
		return -1;

	bus = sess_bus(mistake);
	if (!bus)
		return -1;
	if (!g_dbus_connection_emit_signal(bus, NULL, "/Layouts", "org.kde.keyboard",
	                                   "reloadConfig", NULL, mistake))
		return -1;
	/* ⛔ `[M]` 6 Oct 2026, KWin 6.6.6 (Ubuntu 26.04): nobody listens to
	 *    `reloadConfig` ANY MORE — `KeyboardLayout::init()` watches kxkbrc with a
	 *    `KConfigWatcher`, that is the signal `org.kde.kconfig.notify
	 *    ConfigChanged` on the path `/kxkbrc`, and rebuilds the keymap if among the
	 *    changed groups there is "Layout" (`handleXkbConfigChanged`).  Without it, the
	 *    session stayed `English (US)` (F-009 red).  Both are sent:
	 *    the old one for KWin up to 6.3, this one for the newer ones. */
	{
		GVariantBuilder groups;
		const char *keys[] = { "LayoutList", "VariantList" };
		GVariantBuilder names;

		g_variant_builder_init(&names, G_VARIANT_TYPE("aay"));
		for (size_t i = 0; i < G_N_ELEMENTS(keys); i++)
			g_variant_builder_add_value(&names, g_variant_new_bytestring(keys[i]));
		g_variant_builder_init(&groups, G_VARIANT_TYPE("a{saay}"));
		g_variant_builder_add(&groups, "{saay}", "Layout", &names);
		if (!g_dbus_connection_emit_signal(bus, NULL, "/kxkbrc", "org.kde.kconfig.notify",
		                                   "ConfigChanged",
		                                   g_variant_new("(a{saay})", &groups), mistake))
			return -1;
	}
	/* ⚠ The signal has no reply: the queue is flushed so it leaves NOW. */
	g_dbus_connection_flush_sync(bus, NULL, NULL);
	return 0;
}

/* ------------------------------------------------------------------ *
 * ⭐⭐ THE NESTED KWIN — see `kwin.h`
 * ------------------------------------------------------------------ */

#define HOST_FOLDER "remotix-kwin-host"
/* How long the helper waits for labwc's socket.  `[M]` labwc is up in about
 * a tenth of a second on the test machine: the ceiling is for a loaded
 * machine, not a guess at the normal case. */
#define HOST_BIRTH_MS 10000
/* The refresh of labwc's screenless output.  KWin nested draws its next frame
 * only when labwc says the previous one was presented, and labwc presents on
 * ITS clock: at 60 Hz the two clocks drift and frames are lost — `[M]` 11 Oct
 * 2026, 60 fps animation at 3824x2064: 59 fps with KWin --virtual, 52-55
 * nested at 60 Hz.  A faster host clock answers sooner; KWin keeps its own
 * 60 (the host reports no refresh, `wayland_output.cpp` falls back to 60). */
#ifndef HOST_MHZ
#define HOST_MHZ 240000
#endif

/*
 * labwc's whole configuration, and it is ours: `-C` makes labwc look ONLY in
 * this folder, so a user's `~/.config/labwc` (an XFCE/LXQt user has one) is
 * never read here.
 *   · every window FULL SCREEN — there is exactly one, KWin, and its size
 *     must be the output's: that is the whole mechanism.  ⛔ Matched on the
 *     TITLE, not on `identifier`: `[M]` 11 Oct 2026, Leap 16 (labwc 0.8.1,
 *     KWin 6.4.2) the `identifier="*"` rule never fired — KWin's window stayed
 *     floating, 2 px narrower and 28 px shorter than the output, and the
 *     capture fell back to memory; with `title="*"` it is full screen on both
 *     boxes.  (One rule only: the action TOGGLES, two would undo each other.)  ⛔ A window smaller
 *     or larger than the output would not do: labwc repaints only what is
 *     on its output, and KWin draws only when labwc has repainted;
 *   · no decoration, ⛔ from the very first configure (`decoration` client in
 *     `core`, not only the rule): `[M]` 11 Oct 2026, Leap 16 (labwc 0.8.1),
 *     KWin's window was first configured 3822x2036 on a 3824x2064 output —
 *     the title bar's pixels taken away before the rule made it full screen —
 *     and a capture mounted in that instant asked for the wrong size.
 *   · ⛔ NO BINDINGS AT ALL, keys or mouse (DECISIONI §10.43): an `rc.xml`
 *     without `<keybind>` makes labwc load its DEFAULT ones, which start
 *     programs (W-Return a terminal, the volume keys `amixer`), and any
 *     program of the user could press them through the virtual-keyboard
 *     protocol.  One binding each with the single action `None`: labwc decides
 *     «defaults or not» on the bindings it has READ (one), then removes every
 *     binding whose action list is empty — `[M]` 11 Oct 2026, labwc 0.8.3, 0.8.4
 *     and 0.9.8 (`-d`): no «load default key/mouse bindings», «Cleared 1
 *     keybinds», «Cleared 1 mousebinds», and W-Return sent through the
 *     virtual keyboard starts nothing (with the old file it started the
 *     terminal).  Same order in every labwc 0.8.0-0.9.8 (`rcxml.c`,
 *     `post_processing()`: the defaults test, then `deduplicate_*()`).
 *     ⛔ The key must be a VALID keysym: an unknown one creates no binding,
 *     and the defaults come back.
 */
static const char HOST_RC[] =
    "<?xml version=\"1.0\"?>\n"
    "<!-- REMOTIX: the screenless labwc that hosts KWin (kwin.c, «nested KWin»).\n"
    "     Rewritten at every birth: do not edit. -->\n"
    "<labwc_config>\n"
    "  <core><decoration>client</decoration><gap>0</gap></core>\n"
    "  <windowRules>\n"
    "    <windowRule title=\"*\" serverDecoration=\"no\">\n"
    "      <action name=\"ToggleFullscreen\"/>\n"
    "    </windowRule>\n"
    "  </windowRules>\n"
    "  <keyboard><keybind key=\"W-Return\"><action name=\"None\"/></keybind></keyboard>\n"
    "  <mouse><context name=\"Root\"><mousebind button=\"Left\" action=\"Press\">"
    "<action name=\"None\"/></mousebind></context></mouse>\n"
    "</labwc_config>\n";

static char *host_folder(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (!runtime || !*runtime)
		return NULL;
	return g_build_filename(runtime, HOST_FOLDER, NULL);
}

char *kwin_host_display(void)
{
	g_autofree char *folder = host_folder();

	return folder ? g_build_filename(folder, "wayland-0", NULL) : NULL;
}

bool kwin_host_exists(void)
{
	g_autofree char *display = kwin_host_display();
	struct wl_display *d;

	if (!display || access(display, F_OK) != 0)
		return false;
	d = wl_display_connect(display);
	if (!d)
		return false;
	wl_display_disconnect(d);
	return true;
}

/* ------------------------------------------------------------------ *
 * ⛔⭐ THE WANTED SIZE — one small file next to labwc's socket
 *      (`<host folder>/wanted`, «W H»).
 *
 * `[M]` 14-15 Oct 2026, rete11-kde: three births out of ~20 came out at
 * 1280x720 — labwc's hard-wired size — although `--kwin-nested` had put
 * labwc at the client's size and READ IT BACK before starting KWin
 * (journal: «labwc … at 3824x2064 … now KWin», then «asked 3824x2064,
 * OBTAINED 1280x720»; run functional/20261014-223248 F-018b, and 05:13:54,
 * 06:13:02 on 15 Oct).  Seen a few hundred ms later, at the first mount,
 * KWin's output was 1280x720 and `kwin_host_settle()` accepted it: it
 * only waited for KWin to match WHATEVER labwc had, so a labwc that had
 * gone back to 1280x720 was «settled».  A later reattach at another size
 * did resize (F-018b B and C were right): the road works, it was simply
 * never asked again at birth.
 * ⭐ So the size the host MUST have is written down — by the birth and by
 *    every reattach that asks for one — and the first mount brings labwc
 *    back to it instead of believing the size it finds.
 * ------------------------------------------------------------------ */
static char *host_wanted_path(void)
{
	g_autofree char *folder = host_folder();

	return folder ? g_build_filename(folder, "wanted", NULL) : NULL;
}

/* ⚠ The caller says the failure, on ITS channel: `--kwin-nested` is a process
 *   of its own whose voice is `g_printerr` (the journal), not `registro_dice`. */
static bool host_wanted_write(uint32_t width, uint32_t height, GError **mistake)
{
	g_autofree char *fpath = host_wanted_path();
	g_autofree char *text = NULL;

	if (!fpath) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "XDG_RUNTIME_DIR missing");
		return false;
	}
	text = g_strdup_printf("%u %u\n", width, height);
	return g_file_set_contents(fpath, text, -1, mistake);
}

static bool host_wanted_read(uint32_t *width, uint32_t *height)
{
	g_autofree char *fpath = host_wanted_path();
	g_autofree char *text = NULL;
	unsigned w = 0, h = 0;

	if (!fpath || !g_file_get_contents(fpath, &text, NULL, NULL))
		return false;
	if (sscanf(text, "%u %u", &w, &h) != 2 || w < 200 || h < 200 || w > 8192 ||
	    h > 8192)
		return false;
	*width = w;
	*height = h;
	return true;
}

/* ⛔ The size is read back from labwc, not believed from the answer
 *    (`wlroots.h`: «the truth is told by the frame»). */
static bool host_ask_size(const char *display, uint32_t width, uint32_t height,
                          GError **mistake)
{
	WlrStage *host = wlr_open_on(display, mistake);
	uint32_t l = 0, a = 0;
	WlrSizeOutcome e;

	if (!host)
		return false;
	e = wlr_ask_size_hz(host, width, height, HOST_MHZ, 2.0, mistake);
	if (e == WLR_SIZE_CANCELLED) {
		/* an old serial: one more try, as `wlroots.h` allows */
		g_clear_error(mistake);
		e = wlr_ask_size_hz(host, width, height, HOST_MHZ, 2.0, mistake);
	}
	wlr_measure(host, &l, &a);
	wlr_close(host);
	if (l == width && a == height)
		return true;
	if (mistake && !*mistake)
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "labwc (KWin's host) was asked for %ux%u and its output is %ux%u "
		            "(outcome %d)",
		            width, height, l, a, (int)e);
	return false;
}

/* ------------------------------------------------------------------ *
 * ⛔⭐ THE TICKER — the nested KWin must never wait for a frame that the
 *      host will not draw.
 *
 * `[M]` 11 Oct 2026, rete11-kde, KWin 6.3.6 nested in labwc 0.8.3 (wlroots
 * 0.18), `WAYLAND_DEBUG=client` on KWin: 614 commits of KWin's window, 612
 * `wp_presentation_feedback.presented` — and the commit left without an
 * answer was one of the two WITHOUT DAMAGE.  KWin (`wayland_output.cpp`,
 * `present()`) waits for `presented`/`discarded` before drawing the next
 * frame; wlroots answers only when it renders the output, and a commit with
 * no damage does not make it render.  ⇒ KWin stays still FOREVER, and with
 * it every window of the session (the scene's Firefox stayed at «New Tab»
 * for minutes, its page alive).  It cures by itself as soon as anything else
 * makes labwc draw — the size request did, which is why «same size» woke
 * it up on 10 Oct.
 * ⭐ The cure: a 1x1 transparent surface in labwc's overlay layer, damaged
 *    TICKER_MS apart: labwc draws one pixel, presents, and with it the
 *    pending frame of KWin.  Nobody sees labwc's screen: we capture KWin's.
 *    ⚠ The price: one 1-pixel repaint of a screen nobody looks at every
 *      TICKER_MS, and in the rare frame without damage KWin waits up to
 *      TICKER_MS instead of forever.
 * ------------------------------------------------------------------ */
#define TICKER_MS 16

typedef struct
{
	struct wl_compositor *compositor;
	struct wl_shm *shm;
	struct zwlr_layer_shell_v1 *layers;
	bool configured, is_closed;
} Ticker;

static void ticker_global(void *d, struct wl_registry *r, uint32_t name, const char *iface,
                          uint32_t v)
{
	Ticker *t = d;

	if (strcmp(iface, wl_compositor_interface.name) == 0)
		t->compositor = wl_registry_bind(r, name, &wl_compositor_interface, MIN(v, 4u));
	else if (strcmp(iface, wl_shm_interface.name) == 0)
		t->shm = wl_registry_bind(r, name, &wl_shm_interface, 1);
	else if (strcmp(iface, zwlr_layer_shell_v1_interface.name) == 0)
		t->layers = wl_registry_bind(r, name, &zwlr_layer_shell_v1_interface, MIN(v, 1u));
}
static void ticker_global_away(void *d, struct wl_registry *r, uint32_t n) {}
static const struct wl_registry_listener TICKER_REGISTRY = { ticker_global, ticker_global_away };

static void ticker_configure(void *d, struct zwlr_layer_surface_v1 *s, uint32_t serial,
                             uint32_t l, uint32_t a)
{
	Ticker *t = d;

	zwlr_layer_surface_v1_ack_configure(s, serial);
	t->configured = true;
}
static void ticker_closed(void *d, struct zwlr_layer_surface_v1 *s)
{
	((Ticker *)d)->is_closed = true;
}
static const struct zwlr_layer_surface_v1_listener TICKER_LAYER = { ticker_configure,
	                                                            ticker_closed };

/* It runs in its own process, child of the start-line helper: it ends when
 * labwc ends (the connection drops) or when its parent — which has become
 * the KWin wrapper — dies. */
static void ticker_alive(const char *display)
{
	Ticker t = { 0 };
	struct wl_display *d;
	struct wl_registry *reg;
	struct wl_surface *surface;
	struct zwlr_layer_surface_v1 *layer;
	struct wl_region *blank;
	struct wl_shm_pool *pool;
	struct wl_buffer *pixel;
	int fd;

	prctl(PR_SET_PDEATHSIG, SIGTERM);
	d = wl_display_connect(display);
	if (!d)
		_exit(1);
	reg = wl_display_get_registry(d);
	wl_registry_add_listener(reg, &TICKER_REGISTRY, &t);
	wl_display_roundtrip(d);
	if (!t.compositor || !t.shm || !t.layers) {
		g_printerr("remotix --kwin-nested: ⛔ ticker: labwc lacks %s\n",
		           !t.layers ? "zwlr_layer_shell_v1" : "wl_compositor/wl_shm");
		_exit(1);
	}
	fd = memfd_create("remotix-ticker", MFD_CLOEXEC);
	if (fd < 0 || ftruncate(fd, 4) != 0)
		_exit(1);
	pool = wl_shm_create_pool(t.shm, fd, 4);
	/* one ARGB pixel, all zero: fully transparent */
	pixel = wl_shm_pool_create_buffer(pool, 0, 1, 1, 4, WL_SHM_FORMAT_ARGB8888);
	surface = wl_compositor_create_surface(t.compositor);
	blank = wl_compositor_create_region(t.compositor);
	wl_surface_set_input_region(surface, blank); /* no pointer, ever */
	layer = zwlr_layer_shell_v1_get_layer_surface(t.layers, surface, NULL,
	                                                ZWLR_LAYER_SHELL_V1_LAYER_OVERLAY,
	                                                "remotix-ticker");
	zwlr_layer_surface_v1_add_listener(layer, &TICKER_LAYER, &t);
	zwlr_layer_surface_v1_set_size(layer, 1, 1);
	zwlr_layer_surface_v1_set_anchor(layer, ZWLR_LAYER_SURFACE_V1_ANCHOR_TOP |
	                                             ZWLR_LAYER_SURFACE_V1_ANCHOR_LEFT);
	zwlr_layer_surface_v1_set_exclusive_zone(layer, -1);
	wl_surface_commit(surface);
	while (!t.configured && !t.is_closed)
		if (wl_display_dispatch(d) < 0)
			_exit(0);
	/* ⛔ The tick is a CLOCK, not «after every event»: labwc answers each
	 *    commit (release, frame), and a loop that commits again on the answer
	 *    makes labwc repaint as fast as it can — `[M]` the first draft: labwc
	 *    at 85 % of a core, the ticker at 17 %. */
	for (gint64 upcoming = g_get_monotonic_time(); !t.is_closed;) {
		gint64 now = g_get_monotonic_time();
		struct pollfd p = { wl_display_get_fd(d), POLLIN, 0 };

		if (now >= upcoming) {
			wl_surface_attach(surface, pixel, 0, 0);
			wl_surface_damage_buffer(surface, 0, 0, 1, 1);
			wl_surface_commit(surface);
			upcoming += (gint64)TICKER_MS * 1000;
			if (upcoming < now)
				upcoming = now + (gint64)TICKER_MS * 1000;
		}
		if (wl_display_flush(d) < 0 || wl_display_dispatch_pending(d) < 0)
			break;
		if (poll(&p, 1, (int)MAX(1, (upcoming - g_get_monotonic_time()) / 1000)) > 0) {
			if (p.revents & (POLLERR | POLLHUP))
				break;
			if (wl_display_dispatch(d) < 0)
				break;
		}
	}
	_exit(0);
}

int kwin_nested_alive(int argc, char **argv)
{
	g_autofree char *folder = host_folder();
	g_autofree char *config = NULL;
	g_autofree char *rc = NULL;
	g_autofree char *display = NULL;
	g_autoptr(GError) mistake = NULL;
	g_autoptr(GPtrArray) line = NULL;
	g_autofree char *labwc_path = NULL;
	unsigned long width, height;
	const char *node;
	pid_t labwc;
	gint64 t0 = g_get_monotonic_time(), expiry;
	bool ready = false;

	/* argv: remotix --kwin-nested W H NODE -- wrapper args… */
	if (argc < 7 || strcmp(argv[5], "--") != 0) {
		g_printerr("remotix --kwin-nested W H NODE -- <kwin_wayland_wrapper> [args]\n");
		return 2;
	}
	width = strtoul(argv[2], NULL, 10);
	height = strtoul(argv[3], NULL, 10);
	node = argv[4];
	if (width < 200 || height < 200 || width > 8192 || height > 8192) {
		g_printerr("remotix --kwin-nested: size %lux%lu out of range\n", width,
		           height);
		return 2;
	}
	if (!folder) {
		g_printerr("remotix --kwin-nested: XDG_RUNTIME_DIR is not set\n");
		return 1;
	}
	/* ⭐ Which labwc is a BUILD-TIME choice of the package, not a runtime
	 *    switch: the distribution's from PATH, except where the distribution
	 *    has none — RHEL/Alma 10 (EPEL has wlroots 0.18 but no labwc), whose
	 *    package builds OUR labwc and passes its exact path here
	 *    (`make LABWC=/usr/lib/remotix/labwc`, DECISIONI §10.43).
	 * ⛔ Without labwc the session must still be born: KWin `--virtual`, as
	 *    before 11 Oct 2026, and SAID — the desktop keeps the size it is born
	 *    with (the page centres it). */
#ifdef REMOTIX_LABWC
	labwc_path = access(REMOTIX_LABWC, X_OK) == 0 ? g_strdup(REMOTIX_LABWC) : NULL;
#else
	labwc_path = g_find_program_in_path("labwc");
#endif
	if (!labwc_path) {
		line = g_ptr_array_new();
		for (int i = 6; i < argc; i++)
			g_ptr_array_add(line, argv[i]);
		g_ptr_array_add(line, (char *)"--virtual");
		g_ptr_array_add(line, NULL);
		g_printerr("remotix --kwin-nested: ⛔ labwc is not installed: KWin --virtual, "
		           "and the desktop will NOT take the window's size at reattach "
		           "(DECLARED FALLBACK)\n");
		execvp(argv[6], (char **)line->pdata);
		g_printerr("remotix --kwin-nested: %s does not start: %s\n", argv[6],
		           strerror(errno));
		return 1;
	}
	config = g_build_filename(folder, "labwc", NULL);
	rc = g_build_filename(config, "rc.xml", NULL);
	display = g_build_filename(folder, "wayland-0", NULL);
	g_mkdir_with_parents(config, 0700);
	if (!g_file_set_contents(rc, HOST_RC, -1, &mistake)) {
		g_printerr("remotix --kwin-nested: %s\n", mistake->message);
		return 1;
	}
	/* the size the desktop is born at: `kwin_host_settle()` holds labwc to it.
	 * ⭐ Written BEFORE it is obtained: at birth it is the declared intent. */
	if (!host_wanted_write((uint32_t)width, (uint32_t)height, &mistake)) {
		g_printerr("remotix --kwin-nested: ⚠ the wanted size %lux%lu is NOT written "
		           "(%s): a labwc that loses it will not be brought back at the first "
		           "mount\n",
		           width, height, mistake->message);
		g_clear_error(&mistake);
	}

	labwc = fork();
	if (labwc < 0) {
		g_printerr("remotix --kwin-nested: fork: %s\n", strerror(errno));
		return 1;
	}
	if (labwc == 0) {
		/* ⛔ labwc gets a RUNTIME FOLDER OF ITS OWN: its socket is then
		 *    `<runtime>/remotix-kwin-host/wayland-0`, and KWin's `wayland-N`
		 *    stays the only one in `XDG_RUNTIME_DIR` — whoever scans it
		 *    (`kwin_display_open()`, the clipboard) can never land on the
		 *    host by mistake. */
		g_setenv("XDG_RUNTIME_DIR", folder, TRUE);
		g_unsetenv("WAYLAND_DISPLAY");
		g_unsetenv("WAYLAND_SOCKET");
		g_unsetenv("DISPLAY");
		/* ⛔ Never: it would publish the HOST's display to the bus and to
		 *    systemd, and the session's programs would open on a screen
		 *    nobody sees.  Said OFF, not just unset (§10.43): unset leaves
		 *    it to labwc's own rule (today: only with a DRM backend). */
		g_setenv("LABWC_UPDATE_ACTIVATION_ENV", "0", TRUE);
		g_setenv("WLR_BACKENDS", "headless", TRUE);
		g_setenv("WLR_LIBINPUT_NO_DEVICES", "1", TRUE);
		if (strcmp(node, "pixman") == 0)
			g_setenv("WLR_RENDERER", "pixman", TRUE);
		else if (strcmp(node, "-") != 0)
			g_setenv("WLR_RENDER_DRM_DEVICE", node, TRUE);
#ifdef REMOTIX_LABWC
		execl(labwc_path, "labwc", "-C", config, (char *)NULL);
#else
		execlp("labwc", "labwc", "-C", config, (char *)NULL);
#endif
		g_printerr("remotix --kwin-nested: labwc does not start: %s\n", strerror(errno));
		_exit(127);
	}

	expiry = t0 + (gint64)HOST_BIRTH_MS * 1000;
	while (g_get_monotonic_time() < expiry) {
		int status;

		if (waitpid(labwc, &status, WNOHANG) == labwc) {
			g_printerr("remotix --kwin-nested: ⛔ labwc (KWin's host) exited at "
			           "birth (status %d)\n",
			           status);
			return 1;
		}
		if (access(display, F_OK) == 0) {
			struct wl_display *d = wl_display_connect(display);

			if (d) {
				wl_display_disconnect(d);
				ready = true;
				break;
			}
		}
		g_usleep(20000);
	}
	if (!ready) {
		g_printerr("remotix --kwin-nested: ⛔ labwc's socket %s did not appear "
		           "within %d ms\n",
		           display, HOST_BIRTH_MS);
		kill(labwc, SIGTERM);
		return 1;
	}
	/* labwc's headless output is born 1280x720 hard-wired (`wlroots.h`): it is
	 * brought to the client's size BEFORE KWin opens its window, so the
	 * desktop is born at the right size and is not resized at birth. */
	if (!host_ask_size(display, (uint32_t)width, (uint32_t)height, &mistake)) {
		g_printerr("remotix --kwin-nested: ⛔ %s\n",
		           mistake ? mistake->message : "the host's size was not set");
		kill(labwc, SIGTERM);
		return 1;
	}
	{
		pid_t ticker = fork();

		if (ticker == 0)
			ticker_alive(display);
		if (ticker < 0)
			g_printerr("remotix --kwin-nested: ⛔ the ticker did not start (%s): KWin "
			           "may freeze on a frame without damage\n", strerror(errno));
	}
	g_printerr("remotix --kwin-nested: ⭐ labwc (pid %d, node %s) at %lux%lu on %s in "
	           "%lld ms; now KWin, nested in it\n",
	           (int)labwc, node, width, height, display,
	           (long long)((g_get_monotonic_time() - t0) / 1000));

	/*
	 * ⛔ THE CURSOR IN SOFTWARE, as with `--virtual` — `[M]` 11 Oct 2026, nested
	 *    without it: F-005 red (the pointer's shape never changed in the page)
	 *    and F-004 blocked (a full-screen Firefox stayed at its first image).
	 *    `[R]` KWin 6.3.6 `compositor_wayland.cpp`: the nested output HAS a
	 *    cursor layer, so the cursor goes to labwc's screen (nobody sees it) and
	 *    no longer into what the stream describes; and with no software cursor
	 *    layer visible a full-screen window is handed to labwc as it is (direct
	 *    scanout).  `--virtual` had no cursor layer: this puts KWin back on
	 *    that road — the only switch, `KWIN_FORCE_SW_CURSOR`.
	 */
	g_setenv("KWIN_FORCE_SW_CURSOR", "1", TRUE);
	line = g_ptr_array_new();
	for (int i = 6; i < argc; i++)
		g_ptr_array_add(line, argv[i]);
	g_ptr_array_add(line, (char *)"--wayland-display");
	g_ptr_array_add(line, display);
	g_ptr_array_add(line, NULL);
	execvp(argv[6], (char **)line->pdata);
	g_printerr("remotix --kwin-nested: %s does not start: %s\n", argv[6], strerror(errno));
	kill(labwc, SIGTERM);
	return 1;
}

/* KWin's output size, read on a connection of our own: the stage's
 * connection is already closed (the reattach dismantles the stage first). */
typedef struct
{
	uint32_t l, a;
} Mode;

static void mode_geometry(void *d, struct wl_output *o, int32_t x, int32_t y, int32_t pw,
                          int32_t ph, int32_t sp, const char *mk, const char *md, int32_t t)
{
}
static void mode_mode(void *d, struct wl_output *o, uint32_t flag, int32_t l, int32_t a,
                      int32_t r)
{
	Mode *m = d;

	if (flag & WL_OUTPUT_MODE_CURRENT) {
		m->l = (uint32_t)MAX(0, l);
		m->a = (uint32_t)MAX(0, a);
	}
}
static void mode_done(void *d, struct wl_output *o) {}
static void mode_scale(void *d, struct wl_output *o, int32_t s) {}
static const struct wl_output_listener MODE_LISTENER = { mode_geometry, mode_mode, mode_done,
	                                                     mode_scale, NULL, NULL };

static void mode_global(void *d, struct wl_registry *r, uint32_t name, const char *iface,
                        uint32_t v)
{
	struct wl_output **o = d;

	/* version 2: `done` and `scale`, and no `name`/`description` to listen to */
	if (!*o && strcmp(iface, wl_output_interface.name) == 0)
		*o = wl_registry_bind(r, name, &wl_output_interface, MIN(v, 2u));
}
static void mode_global_away(void *d, struct wl_registry *r, uint32_t name) {}
static const struct wl_registry_listener MODE_REGISTRY = { mode_global, mode_global_away };

static bool host_resize(uint32_t width, uint32_t height, double wait_s, bool remember,
                        GError **mistake);

bool kwin_host_resize(uint32_t width, uint32_t height, double wait_s,
                        GError **mistake)
{
	/* ⭐ a reattach's size becomes the one the host must keep — once labwc
	 *   has TAKEN it (see `remember`) */
	return host_resize(width, height, wait_s, true, mistake);
}

/* `remember`: write the size down as the wanted one, but only once labwc has
 * been read back at it.  ⛔ Not before: a size labwc cannot reach, written
 * down, would cost every later mount the settle's wait and nudge (~4 s) for
 * nothing.  (The birth writes it before: there it is the declared intent.) */
static bool host_resize(uint32_t width, uint32_t height, double wait_s, bool remember,
                        GError **mistake)
{
	g_autofree char *display = kwin_host_display();
	struct wl_display *kwin;
	struct wl_registry *reg;
	struct wl_output *output = NULL;
	Mode m = { 0, 0 };
	char socket[64];
	bool listening = false;
	gint64 t0 = g_get_monotonic_time(), expiry;

	if (!kwin_host_exists()) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no host for KWin (%s): this Plasma session was born with KWin "
		            "--virtual, which cannot change size",
		            display ? display : "XDG_RUNTIME_DIR missing");
		return false;
	}
	if (!host_ask_size(display, width, height, mistake))
		return false;
	if (remember) {
		g_autoptr(GError) why = NULL;

		if (!host_wanted_write(width, height, &why))
			registro_dice(AREA,
			              "⚠ nested KWin: the wanted size %ux%u is NOT written (%s): a "
			              "labwc that loses it will not be brought back at the next mount",
			              width, height, why->message);
	}

	kwin = kwin_display_open(socket, sizeof socket);
	if (!kwin) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "the host is at %ux%u but KWin cannot be reached to read it back",
		            width, height);
		return false;
	}
	reg = wl_display_get_registry(kwin);
	wl_registry_add_listener(reg, &MODE_REGISTRY, &output);
	/* ⚠ KWin throttles the host's configure by one refresh period
	 *   (`wayland_output.cpp`, `m_configureThrottleTimer`): the new mode
	 *   arrives a few milliseconds after labwc's, and it is waited for.
	 * ⚠ And a KWin just born may not have announced its output yet: that
	 *   too is waited for, within the same limit. */
	expiry = t0 + (gint64)(wait_s * 1e6);
	while (wl_display_roundtrip(kwin) >= 0) {
		if (output && !listening) {
			wl_output_add_listener(output, &MODE_LISTENER, &m);
			listening = true;
			continue; /* the next roundtrip brings its mode */
		}
		if (m.l == width && m.a == height)
			break;
		if (g_get_monotonic_time() >= expiry)
			break;
		g_usleep(5000);
	}
	if (output)
		wl_output_destroy(output);
	wl_registry_destroy(reg);
	wl_display_disconnect(kwin);
	if (!listening) {
		/* ⛔ not TIMED_OUT: a nudge of labwc cannot make KWin announce one */
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_INITIALIZED,
		            "the host is at %ux%u but KWin has announced no output after %.1f s",
		            width, height, (g_get_monotonic_time() - t0) / 1e6);
		return false;
	}
	if (m.l != width || m.a != height) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "the host is at %ux%u but KWin's output is %ux%u after %.1f s",
		            width, height, m.l, m.a, (g_get_monotonic_time() - t0) / 1e6);
		return false;
	}
	registro_dice(AREA,
	              "⭐ nested KWin: the host and KWin's output are at %ux%u after %lld ms "
	              "(read back from KWin on «%s», not believed)",
	              width, height, (long long)((g_get_monotonic_time() - t0) / 1000),
	              socket);
	return true;
}


bool kwin_host_settle(double wait_s, GError **mistake)
{
	g_autofree char *display = kwin_host_display();
	WlrStage *host;
	uint32_t l = 0, a = 0;

	uint32_t wl = 0, wa = 0;
	g_autoptr(GError) why = NULL;

	if (!kwin_host_exists()) {
		log_detail(AREA, "nested KWin: no host at %s (KWin --virtual, or labwc not up "
		                 "yet): nothing to settle",
		           display ? display : "?");
		return true; /* no host: nothing to wait for */
	}
	host = wlr_open_on(display, mistake);
	if (!host)
		return false;
	wlr_measure(host, &l, &a);
	wlr_close(host);
	/* ⭐ the size labwc MUST have, not the one it has (box «THE WANTED SIZE»);
	 *   without the file (a session born before it) the old rule: labwc's own */
	if (!host_wanted_read(&wl, &wa)) {
		wl = l;
		wa = a;
	} else if (wl != l || wa != a)
		registro_dice(AREA,
		              "⛔ nested KWin: labwc's output is %ux%u, and it must be %ux%u (the "
		              "size asked at birth or at the last reattach) — asking for it AGAIN, "
		              "or the desktop would stay at the wrong size",
		              l, a, wl, wa);
	/* same size ⇒ no request leaves (`wlr_ask_size`: UNCHANGED); only the wait */
	if (host_resize(wl, wa, wait_s, false, &why))
		return true;
	/*
	 * ⚠ labwc is at the size but KWin did not follow: labwc sends a configure
	 *   only when its output CHANGES, so asking for the same size again sends
	 *   nothing.  One nudge — 8 rows less, then the size — and the window is
	 *   configured twice.  Nobody watches yet: the stage is not mounted.
	 */
	if (g_error_matches(why, G_IO_ERROR, G_IO_ERROR_TIMED_OUT) && wa > 216) {
		registro_dice(AREA,
		              "⚠ nested KWin: %s — nudging labwc (%ux%u, then %ux%u) so KWin's "
		              "window is configured again",
		              why->message, wl, wa - 8, wl, wa);
		g_clear_error(&why);
		(void)host_resize(wl, wa - 8, 1.0, false, NULL);
		if (host_resize(wl, wa, wait_s, false, &why))
			return true;
	}
	g_propagate_error(mistake, g_steal_pointer(&why));
	return false;
}
