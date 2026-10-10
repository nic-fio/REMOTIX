/*
 * kwin — see `kwin.h`.  Carried over from v1's `fondamenta/remotix-c/src/kwin.c`:
 * the comments citing `kde.md` refer to the study of KWin's code, today
 * in `STUDI.md` (from line ~1233, § numbering unchanged).
 */
#include "kwin.h"

#include <errno.h>
#include <fcntl.h>
#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include <glib-unix.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <wayland-client.h>

#include "zkde-screencast-unstable-v1-client-protocol.h"

#include "registro.h"
#include "sessione.h"

#define AREA "capture_v"

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
 * ⛔ THE PRICE IS IN `cattura.c`: every pointer movement produces a
 *    buffer with no new pixels marked `SPA_CHUNK_FLAG_CORRUPTED` (`kde.md`
 *    §4.7), and `cattura.c` already discards them. */
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
	uint32_t version_v;
	char *label_name; /* "Virtual-0" with `--virtual` */
	uint32_t width_px, height_px; /* of the CURRENT mode, in pixels */
} Output;

struct KwinSession
{
	struct wl_display *display;
	struct wl_registry *logbook;
	struct zkde_screencast_unstable_v1 *screencast;
	struct zkde_screencast_stream_unstable_v1 *flow;
	uint32_t screencast_version;

	Output outputs[MAX_OUTPUTS];
	unsigned how_many_outputs;
	const Output *choice;

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
};

/* ------------------------------------------------------------------ *
 * The registry
 * ------------------------------------------------------------------ */
static void on_output_geometry(void *data_v, struct wl_output *out_dir, int32_t x, int32_t y,
                                int32_t width_mm, int32_t height_mm, int32_t subpixel,
                                const char *builder, const char *model,
                                int32_t transform)
{
}

static void on_output_mode(void *data_v, struct wl_output *object, uint32_t flag,
                           int32_t width_px, int32_t height_px, int32_t update)
{
	Output *out_dir = data_v;

	if (!(flag & WL_OUTPUT_MODE_CURRENT))
		return;
	out_dir->width_px = (uint32_t)MAX(0, width_px);
	out_dir->height_px = (uint32_t)MAX(0, height_px);
}

static void on_output_end(void *data_v, struct wl_output *object)
{
}

static void on_output_scale(void *data_v, struct wl_output *object, int32_t scale_v)
{
	/* The scale does not touch the buffer's pixels (`core/output.cpp:457-459`), but
	 * it shifts the input coordinate space: it is logged. */
	if (scale_v != 1)
		log_says(AREA, "⚠ KWin's output has scale %d: the logical desktop is "
		                    "smaller than the captured buffer", scale_v);
}

static void on_output_name(void *data_v, struct wl_output *object, const char *label_name)
{
	Output *out_dir = data_v;

	g_free(out_dir->label_name);
	out_dir->label_name = g_strdup(label_name);
}

static void on_output_description(void *data_v, struct wl_output *object,
                                  const char *description)
{
}

static const struct wl_output_listener kwin_output_listener = {
	on_output_geometry, on_output_mode, on_output_end,
	on_output_scale,     on_output_name, on_output_description,
};

static void on_global(void *data_v, struct wl_registry *logbook, uint32_t label_name,
                       const char *interfaccia, uint32_t version_v)
{
	KwinSession *session_v = data_v;

	if (!strcmp(interfaccia, zkde_screencast_unstable_v1_interface.name)) {
		/* KWin 6.3.6 announces 5; the clamp because a newer KWin would
		 * announce one our XML does not describe. */
		session_v->screencast_version = MIN(version_v, 5u);
		session_v->screencast =
		    wl_registry_bind(logbook, label_name, &zkde_screencast_unstable_v1_interface,
		                     session_v->screencast_version);
	} else if (!strcmp(interfaccia, wl_output_interface.name)) {
		Output *out_dir;

		if (session_v->how_many_outputs >= MAX_OUTPUTS) {
			log_says(AREA, "⚠ more than %d outputs: the others are ignored",
			              MAX_OUTPUTS);
			return;
		}
		out_dir = &session_v->outputs[session_v->how_many_outputs++];
		out_dir->global_name = label_name;
		/* Version 4: the one that carries the `name` event. */
		out_dir->version_v = MIN(version_v, 4u);
		out_dir->object =
		    wl_registry_bind(logbook, label_name, &wl_output_interface, out_dir->version_v);
		wl_output_add_listener(out_dir->object, &kwin_output_listener, out_dir);
	}
}

static void on_global_away(void *data_v, struct wl_registry *logbook, uint32_t label_name)
{
	KwinSession *session_v = data_v;

	for (unsigned i = 0; i < session_v->how_many_outputs; i++)
		if (session_v->outputs[i].global_name == label_name)
			log_says(AREA, "⚠ output «%s» has disappeared from the compositor",
			              session_v->outputs[i].label_name ? session_v->outputs[i].label_name
			                                       : "unnamed");
}

static const struct wl_registry_listener registry_listener = { on_global, on_global_away };

/* ------------------------------------------------------------------ *
 * The stream
 * ------------------------------------------------------------------ */
static void on_stream_closed(void *data_v, struct zkde_screencast_stream_unstable_v1 *flow)
{
	KwinSession *session_v = data_v;

	/* Just mark it: the stage notices on its own, because the
	 * PipeWire node disappears and the capture goes to `UNCONNECTED`. */
	session_v->closed = true;
	log_says(AREA, "KWin closed the capture stream");
}

static void on_stream_created(void *data_v, struct zkde_screencast_stream_unstable_v1 *flow,
                             uint32_t node)
{
	KwinSession *session_v = data_v;

	session_v->node = node;
	session_v->node_arrived = true;
}

static void on_stream_fault(void *data_v, struct zkde_screencast_stream_unstable_v1 *flow,
                             const char *failure)
{
	KwinSession *session_v = data_v;

	session_v->refused = true;
	g_free(session_v->refusal_reason);
	session_v->refusal_reason = g_strdup(failure);
}

static const struct zkde_screencast_stream_unstable_v1_listener stream_listener = {
	on_stream_closed, on_stream_created, on_stream_fault
};

/* ------------------------------------------------------------------ *
 * The loop
 * ------------------------------------------------------------------ */
/* One round of events with a deadline: `wl_display_dispatch` alone would block
 * without a ceiling.  false if the connection dropped or we were stopped. */
static bool run(KwinSession *session_v, int wait_ms)
{
	struct pollfd probe[2];
	int how_many = 1;

	while (wl_display_prepare_read(session_v->display) != 0)
		if (wl_display_dispatch_pending(session_v->display) < 0)
			return false;
	if (wl_display_flush(session_v->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(session_v->display);
		return false;
	}

	probe[0].fd = wl_display_get_fd(session_v->display);
	probe[0].events = POLLIN;
	probe[0].revents = 0;
	if (session_v->wake[0] >= 0) {
		probe[1].fd = session_v->wake[0];
		probe[1].events = POLLIN;
		probe[1].revents = 0;
		how_many = 2;
	}

	if (poll(probe, (nfds_t)how_many, wait_ms) <= 0) {
		wl_display_cancel_read(session_v->display);
		return true;
	}
	if (how_many == 2 && (probe[1].revents & POLLIN)) {
		wl_display_cancel_read(session_v->display);
		return false;
	}
	if (!(probe[0].revents & POLLIN)) {
		wl_display_cancel_read(session_v->display);
		return !(probe[0].revents & (POLLERR | POLLHUP));
	}

	if (wl_display_read_events(session_v->display) < 0)
		return false;
	return wl_display_dispatch_pending(session_v->display) >= 0;
}

static gpointer thread_pump(gpointer data_v)
{
	KwinSession *session_v = data_v;

	while (run(session_v, -1))
		;
	/* ⛔ AND IT IS MARKED — `[M]` 19 Sep 2026, the user's logout on KDE: KWin
	 *    dies with the session WITHOUT closing the stream gracefully, so
	 *    `on_stream_closed` does not arrive; and the PipeWire node disappearing does NOT
	 *    put the capture in error — the grab returns "zero" forever, like
	 *    a still scene.  ⇒ The connection dropping is the only sign, and
	 *    the child reads it with `kwin_closed()`. */
	session_v->closed = true;
	log_says(AREA, "the Wayland connection to KWin has closed: the compositor "
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
		char label_name[32], fpath[512];
		struct wl_display *display;

		snprintf(label_name, sizeof label_name, "wayland-%d", i);
		if (runtime) {
			snprintf(fpath, sizeof fpath, "%s/%s", runtime, label_name);
			if (access(fpath, F_OK) != 0)
				continue;
		}
		display = wl_display_connect(label_name);
		if (display) {
			snprintf(which, how_much, "%s", label_name);
			return display;
		}
	}
	return NULL;
}

/* With `--virtual` there is a single output; the first that has a mode is taken. */
static const Output *choose_output(const KwinSession *session_v)
{
	for (unsigned i = 0; i < session_v->how_many_outputs; i++)
		if (session_v->outputs[i].width_px && session_v->outputs[i].height_px)
			return &session_v->outputs[i];
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

KwinSession *kwin_open(GError **mistake)
{
	KwinSession *session_v = g_new0(KwinSession, 1);
	char socket[64] = "";
	gint64 expiry;

	session_v->wake[0] = session_v->wake[1] = -1;
	session_v->eis = -1;

	session_v->display = kwin_display_open(socket, sizeof socket);
	if (!session_v->display) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no Wayland compositor reachable in XDG_RUNTIME_DIR=%s",
		            getenv("XDG_RUNTIME_DIR") ? getenv("XDG_RUNTIME_DIR") : "(not set)");
		goto fault;
	}

	session_v->logbook = wl_display_get_registry(session_v->display);
	wl_registry_add_listener(session_v->logbook, &registry_listener, session_v);
	/* Two rounds: the globals, then the events of the globals just bound (mode, name). */
	wl_display_roundtrip(session_v->display);
	wl_display_roundtrip(session_v->display);

	if (!session_v->screencast) {
		explain_gate(mistake);
		goto fault;
	}

	session_v->choice = choose_output(session_v);
	if (!session_v->choice) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "KWin has no output with a mode (%u announced): without a "
		            "virtual screen KWin swallows the input too (kde.md §10.3)",
		            session_v->how_many_outputs);
		goto fault;
	}

	/* ⛔ THE LISTENER RIGHT AFTER THE REQUEST AND BEFORE ANY ROUND: `failed`
	 *    is sent synchronously, and whoever is not listening misses it (`kde.md` §4.4). */
	session_v->flow = zkde_screencast_unstable_v1_stream_output(
	    session_v->screencast, session_v->choice->object, POINTER_METADATA);
	if (!session_v->flow) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "capture request to KWin not created");
		goto fault;
	}
	zkde_screencast_stream_unstable_v1_add_listener(session_v->flow, &stream_listener,
	                                                session_v);

	expiry = g_get_monotonic_time() + (gint64)WAIT_NODE_MS * 1000;
	while (!session_v->node_arrived && !session_v->refused && !session_v->closed) {
		gint64 stays = (expiry - g_get_monotonic_time()) / 1000;

		if (stays <= 0)
			break;
		if (!run(session_v, (int)stays))
			break;
	}

	if (session_v->refused) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_FAILED, "KWin refused the capture: %s",
		            session_v->refusal_reason ? session_v->refusal_reason : "no explanation");
		goto fault;
	}
	if (!session_v->node_arrived) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "KWin did not announce the PipeWire node within %d ms", WAIT_NODE_MS);
		goto fault;
	}

	if (!g_unix_open_pipe(session_v->wake, O_CLOEXEC, NULL)) {
		session_v->wake[0] = session_v->wake[1] = -1;
		log_says(AREA, "⚠ wake-up pipe not created: closing the capture "
		                    "will be less clean");
	}
	session_v->pump = g_thread_new("remotix-kwin", thread_pump, session_v);

	log_says(AREA,
	              "⭐ KWin: zkde_screencast v%u on socket «%s», output «%s» %ux%u (%u in "
	              "all), PipeWire node %u",
	              session_v->screencast_version, socket,
	              session_v->choice->label_name ? session_v->choice->label_name : "unnamed",
	              session_v->choice->width_px, session_v->choice->height_px,
	              session_v->how_many_outputs, session_v->node);
	return session_v;

fault:
	kwin_close(session_v);
	return NULL;
}

uint32_t kwin_node(const KwinSession *session_v)
{
	return session_v ? session_v->node : 0;
}

void kwin_measure(const KwinSession *session_v, uint32_t *width_px, uint32_t *height_px)
{
	*width_px = (session_v && session_v->choice) ? session_v->choice->width_px : 0;
	*height_px = (session_v && session_v->choice) ? session_v->choice->height_px : 0;
}

const char *kwin_output_name(const KwinSession *session_v)
{
	if (!session_v || !session_v->choice)
		return NULL;
	return session_v->choice->label_name;
}

unsigned kwin_output_count(const KwinSession *session_v)
{
	unsigned n = 0;

	if (!session_v)
		return 0;
	for (unsigned i = 0; i < session_v->how_many_outputs; i++)
		if (session_v->outputs[i].width_px && session_v->outputs[i].height_px)
			n++;
	return n;
}

bool kwin_closed(const KwinSession *session_v)
{
	return session_v ? session_v->closed : true;
}

/* ------------------------------------------------------------------ *
 * The input channel
 * ------------------------------------------------------------------ */
/* Keyboard 1, pointer 2, touch 4 — the xdg portal's mask
 * (`xdg-desktop-portal-kde/src/remotedesktop.cpp:457-460`). */
#define EIS_CAPABILITIES 7

static void detach_eis(KwinSession *session_v)
{
	/* ⛔ With the token: KWin ties the EIS context to the life of the caller's D-Bus
	 *    NAME, so letting it go only works while the process lives — and
	 *    in a recovery the process stays alive, with one device too many. */
	if (session_v->known_token) {
		GDBusConnection *bus = session_bus(NULL);

		if (bus) {
			GVariant *r = g_dbus_connection_call_sync(
			    bus, "org.kde.KWin", "/org/kde/KWin/EIS/RemoteDesktop",
			    "org.kde.KWin.EIS.RemoteDesktop", "disconnect",
			    g_variant_new("(i)", session_v->eis_token), NULL,
			    G_DBUS_CALL_FLAGS_NONE, 2000, NULL, NULL);
			if (r)
				g_variant_unref(r);
			g_object_unref(bus);
		}
		session_v->known_token = false;
	}
	if (session_v->eis >= 0) {
		close(session_v->eis);
		session_v->eis = -1;
	}
}

static int ask_eis(KwinSession *session_v, GError **mistake)
{
	GDBusConnection *bus;
	GUnixFDList *descriptors = NULL;
	GVariant *response;
	gint idx = -1;

	bus = session_bus(mistake);
	if (!bus)
		return -1;
	/* ⛔ THE DESCRIPTOR TRAVELS IN A SEPARATE LIST: `h` is an INDEX into
	 *    that list, and the zero read from the body would be standard input. */
	response = g_dbus_connection_call_with_unix_fd_list_sync(
	    bus, "org.kde.KWin", "/org/kde/KWin/EIS/RemoteDesktop",
	    "org.kde.KWin.EIS.RemoteDesktop", "connectToEIS", g_variant_new("(i)", EIS_CAPABILITIES),
	    G_VARIANT_TYPE("(hi)"), G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &descriptors, NULL,
	    mistake);
	g_object_unref(bus);
	if (!response)
		return -1;
	g_variant_get(response, "(hi)", &idx, &session_v->eis_token);
	g_variant_unref(response);
	session_v->eis = g_unix_fd_list_get(descriptors, idx, mistake);
	g_object_unref(descriptors);
	if (session_v->eis < 0)
		return -1;
	session_v->known_token = true;
	log_says(AREA, "⭐ KWin granted the input channel (connectToEIS, token %d, "
	                    "descriptor %d)", session_v->eis_token, session_v->eis);
	return session_v->eis;
}

int kwin_eis_fd(KwinSession *session_v, GError **mistake)
{
	if (!session_v) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "no KWin stage");
		return -1;
	}
	if (session_v->eis >= 0)
		return session_v->eis;
	return ask_eis(session_v, mistake);
}

int kwin_eis_reattach(KwinSession *session_v, GError **mistake)
{
	if (!session_v) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "no KWin stage");
		return -1;
	}
	detach_eis(session_v);
	return ask_eis(session_v, mistake);
}

void kwin_close(KwinSession *session_v)
{
	if (!session_v)
		return;

	/* First stop the pump, then touch the display: they are the same object
	 * seen from two threads. */
	if (session_v->pump) {
		if (session_v->wake[1] >= 0) {
			ssize_t unknown = write(session_v->wake[1], "x", 1);

			(void)unknown;
		}
		g_thread_join(session_v->pump);
		session_v->pump = NULL;
	}
	if (session_v->wake[0] >= 0)
		close(session_v->wake[0]);
	if (session_v->wake[1] >= 0)
		close(session_v->wake[1]);

	detach_eis(session_v);
	if (session_v->flow)
		zkde_screencast_stream_unstable_v1_close(session_v->flow);
	if (session_v->screencast)
		zkde_screencast_unstable_v1_destroy(session_v->screencast);
	for (unsigned i = 0; i < session_v->how_many_outputs; i++) {
		if (session_v->outputs[i].object) {
			/* `release` exists since version 3. */
			if (session_v->outputs[i].version_v >= 3)
				wl_output_release(session_v->outputs[i].object);
			else
				wl_output_destroy(session_v->outputs[i].object);
		}
		g_free(session_v->outputs[i].label_name);
	}
	if (session_v->logbook)
		wl_registry_destroy(session_v->logbook);
	if (session_v->display) {
		wl_display_flush(session_v->display);
		wl_display_disconnect(session_v->display);
	}
	g_free(session_v->refusal_reason);
	g_free(session_v);
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
static bool exec_leads_to(const char *exec, const char *canonical, char **seen_v)
{
	char **argv = NULL;
	char *real;
	bool eq_sign;

	if (!g_shell_parse_argv(exec, NULL, &argv, NULL) || !argv || !argv[0]) {
		g_strfreev(argv);
		*seen_v = g_strdup(exec);
		return false;
	}
	*seen_v = g_strdup(argv[0]);
	/* CANONICAL paths on both sides, as KWin does: a link
	 * leading to the binary counts as much as the binary. */
	real = realpath(argv[0], NULL);
	eq_sign = real && strcmp(real, canonical) == 0;
	free(real);
	g_strfreev(argv);
	return eq_sign;
}

bool kwin_check_permission(char *reason_text, size_t how_much)
{
	char *canonical = realpath("/proc/self/exe", NULL);
	GKeyFile *keys = g_key_file_new();
	GError *mistake = NULL;
	char *exec = NULL, *interfaces = NULL, *seen_v = NULL;
	bool va = false;

	if (!canonical) {
		snprintf(reason_text, how_much, "I do not know which binary I am running: %s", strerror(errno));
		goto fine;
	}
	if (!g_key_file_load_from_file(keys, PERMISSION_DESKTOP_FILE, G_KEY_FILE_NONE, &mistake)) {
		snprintf(reason_text, how_much,
		         "RX-KDE-001: %s %s (%s). Remedy: reinstall REMOTIX with the installer",
		         PERMISSION_DESKTOP_FILE,
		         g_error_matches(mistake, G_FILE_ERROR, G_FILE_ERROR_NOENT) ? "is missing"
		                                                                  : "cannot be read",
		         mistake->message);
		goto fine;
	}
	exec = g_key_file_get_string(keys, "Desktop Entry", "Exec", NULL);
	if (!exec || !exec_leads_to(exec, canonical, &seen_v)) {
		snprintf(reason_text, how_much,
		         "RX-KDE-002: in %s Exec=%s, but the running binary is %s. Remedy: "
		         "reinstall REMOTIX with the installer",
		         PERMISSION_DESKTOP_FILE, seen_v ? seen_v : "(missing)", canonical);
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
		snprintf(reason_text, how_much,
		         "RX-KDE-003: in %s X-KDE-Wayland-Interfaces=%s, without "
		         "zkde_screencast_unstable_v1. Remedy: reinstall REMOTIX with the installer",
		         PERMISSION_DESKTOP_FILE, interfaces ? interfaces : "(missing)");
		goto fine;
	}
	snprintf(reason_text, how_much, "%s checked (it belongs to the package: I do not write it), Exec=%s",
	         PERMISSION_DESKTOP_FILE, canonical);
fine:
	g_clear_error(&mistake);
	g_key_file_unref(keys);
	g_free(exec);
	g_free(interfaces);
	g_free(seen_v);
	free(canonical);
	return va;
}

/* ------------------------------------------------------------------ *
 * The keyboard layout — the KWin twin of `input-sources`
 * ------------------------------------------------------------------ */

/*
 * ⭐ PHASE 15, D-008 — `[M]` round 1, 15-f009 on KDE: with the browser in Italian
 *    "è à ò ù é ç ° §" did not come out, the session stayed "English (US)".
 *    `input_disposizione()` had the GNOME road and the wlroots one, for
 *    KWin none (`STUDI.md` §kde §6.7 listed it, nobody had written it).
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
 *     ⇒ `leggi_keymap()` in `input.c` rereads it and writes "KEYMAP CAMBIATA",
 *     as on GNOME.  "In force" is said by that line, not this one.
 *   ⛔ Road 1 (`XKB_DEFAULT_*` at KWin start) only applies to the first
 *     login; road 2 (`setLayout`) only chooses among the loaded layouts.
 *
 * ⭐ WHERE: in the session folder (`sessione_cartella_kde()`, already at the
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

int kwin_layout(const char *label_name, GError **mistake)
{
	g_autofree char *folder = session_folder_kde();
	g_autofree char *arrangement = NULL;
	g_autofree char *variant = NULL;
	g_autofree char *fpath = NULL;
	g_autofree char *body_text = NULL;
	g_autoptr(GDBusConnection) bus = NULL;
	const char *par = label_name ? strchr(label_name, '(') : NULL;

	if (!label_name || !*label_name) {
		g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "no name");
		return -1;
	}
	/* `RCP.md` §4.5: `de(neo)` ⇒ LayoutList=de, VariantList=neo.
	 * ⛔ The name ends up inside an INI file: no newline, no `[`. */
	if (par) {
		const char *is_closed = strchr(par + 1, ')');

		if (!is_closed || is_closed[1] != '\0' ||
		    !clean_xkb_name(label_name, (size_t) (par - label_name)) ||
		    !clean_xkb_name(par + 1, (size_t) (is_closed - par - 1))) {
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
			            "invalid name «%s»", label_name);
			return -1;
		}
		arrangement = g_strndup(label_name, (size_t) (par - label_name));
		variant = g_strndup(par + 1, (size_t) (is_closed - par - 1));
	} else {
		if (!clean_xkb_name(label_name, strlen(label_name))) {
			g_set_error(mistake, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
			            "invalid name «%s»", label_name);
			return -1;
		}
		arrangement = g_strdup(label_name);
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
	body_text = g_strdup_printf("[Layout]\n"
	                        "LayoutList[$i]=%s\n"
	                        "VariantList[$i]=%s\n",
	                        arrangement, variant);
	if (!g_file_set_contents(fpath, body_text, -1, mistake))
		return -1;

	bus = session_bus(mistake);
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
		GVariantBuilder group_list;
		const char *keys[] = { "LayoutList", "VariantList" };
		GVariantBuilder names;

		g_variant_builder_init(&names, G_VARIANT_TYPE("aay"));
		for (size_t i = 0; i < G_N_ELEMENTS(keys); i++)
			g_variant_builder_add_value(&names, g_variant_new_bytestring(keys[i]));
		g_variant_builder_init(&group_list, G_VARIANT_TYPE("a{saay}"));
		g_variant_builder_add(&group_list, "{saay}", "Layout", &names);
		if (!g_dbus_connection_emit_signal(bus, NULL, "/kxkbrc", "org.kde.kconfig.notify",
		                                   "ConfigChanged",
		                                   g_variant_new("(a{saay})", &group_list), mistake))
			return -1;
	}
	/* ⚠ The signal has no reply: the queue is flushed so it leaves NOW. */
	g_dbus_connection_flush_sync(bus, NULL, NULL);
	return 0;
}
