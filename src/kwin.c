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

#include "registro.h"
#include "sessione.h"
#include "wlroots.h"

#define AREA "cattura"

/* How long to wait for KWin to answer `created` or `failed`.  A ceiling is needed:
 * `failed` is sent SYNCHRONOUSLY inside the request handler
 * (`screencastmanager.cpp:82`), so whoever misses it waits forever. */
#define ATTESA_NODO_MS 5000

/* The cursor mode, from the protocol's enum: 1 hidden, 2 drawn into the
 * buffer, 4 as metadata.
 *
 * ⛔ IT IS DECIDED ONCE ONLY and cannot be changed on a live stream
 *    (`screencaststream.cpp:915-918`).  METADATA as on Mutter (`cursor-mode=2`
 *    in `mutter.c`): the page draws the cursor.
 * ⛔ THE PRICE IS IN `cattura.c`: every pointer movement produces a
 *    buffer with no new pixels marked `SPA_CHUNK_FLAG_CORRUPTED` (`kde.md`
 *    §4.7), and `cattura.c` already discards them. */
#define PUNTATORE_METADATO 4

#define MAX_OUTPUTS 8

/* The path of the permission: system-wide, because it applies to every user, and
 * KWin looks in `XDG_DATA_DIRS` (which contains `/usr/share`).  Since phase 17 the
 * package ships it and REMOTIX only checks it (`kwin_verifica_permesso`). */
#define PERMISSION_DESKTOP_FILE "/usr/share/applications/org.kde.remotix.desktop"

typedef struct
{
	struct wl_output *oggetto;
	uint32_t global_name;
	uint32_t versione;
	char *nome; /* "WL-0" nested (`[M]` 11 Oct 2026), "Virtual-0" with `--virtual` */
	uint32_t larghezza, altezza; /* of the CURRENT mode, in pixels */
} OutDir;

struct KwinSessione
{
	struct wl_display *display;
	struct wl_registry *registro;
	struct zkde_screencast_unstable_v1 *screencast;
	struct zkde_screencast_stream_unstable_v1 *flusso;
	uint32_t screencast_version;

	OutDir uscite[MAX_OUTPUTS];
	unsigned how_many_outputs;
	const OutDir *scelta;

	uint32_t nodo;
	bool node_arrived;
	bool rifiutato;
	char *refusal_reason;
	volatile bool chiuso;

	/* ⛔ THE LOOP THAT KEEPS THE CONNECTION ALIVE IS NOT A LUXURY: the stream lives
	 *    as long as the Wayland connection (`screencast_v1.cpp:28-35`), and a
	 *    connection nobody serves does not deliver `closed`. */
	GThread *pompa;
	int sveglia[2];

	/* The input channel: the descriptor and the token of `connectToEIS`. */
	int eis;
	gint eis_token;
	bool known_token;

	/* The pixel that keeps full-screen windows composited (`metti_il_pixel()`). */
	struct wl_compositor *compositor;
	struct wl_shm *shm;
	struct zwlr_layer_shell_v1 *strati;
	struct wl_surface *pixel_sup;
	struct zwlr_layer_surface_v1 *pixel_strato;
	struct wl_buffer *pixel_buf;
	bool pixel_configurato;
};

/* ------------------------------------------------------------------ *
 * The registry
 * ------------------------------------------------------------------ */
static void on_output_geometry(void *dati, struct wl_output *uscita, int32_t x, int32_t y,
                                int32_t width_mm, int32_t height_mm, int32_t subpixel,
                                const char *costruttore, const char *modello,
                                int32_t trasformazione)
{
}

static void on_output_mode(void *dati, struct wl_output *oggetto, uint32_t flag,
                           int32_t larghezza, int32_t altezza, int32_t aggiornamento)
{
	OutDir *uscita = dati;

	if (!(flag & WL_OUTPUT_MODE_CURRENT))
		return;
	uscita->larghezza = (uint32_t)MAX(0, larghezza);
	uscita->altezza = (uint32_t)MAX(0, altezza);
}

static void on_output_end(void *dati, struct wl_output *oggetto)
{
}

static void on_output_scale(void *dati, struct wl_output *oggetto, int32_t scala)
{
	/* The scale does not touch the buffer's pixels (`core/output.cpp:457-459`), but
	 * it shifts the input coordinate space: it is logged. */
	if (scala != 1)
		registro_dice(AREA, "⚠ KWin's output has scale %d: the logical desktop is "
		                    "smaller than the captured buffer", scala);
}

static void on_output_name(void *dati, struct wl_output *oggetto, const char *nome)
{
	OutDir *uscita = dati;

	g_free(uscita->nome);
	uscita->nome = g_strdup(nome);
}

static void on_output_description(void *dati, struct wl_output *oggetto,
                                  const char *descrizione)
{
}

static const struct wl_output_listener kwin_output_listener = {
	on_output_geometry, on_output_mode, on_output_end,
	on_output_scale,     on_output_name, on_output_description,
};

static void on_global(void *dati, struct wl_registry *registro, uint32_t nome,
                       const char *interfaccia, uint32_t versione)
{
	KwinSessione *sessione = dati;

	if (!strcmp(interfaccia, zkde_screencast_unstable_v1_interface.name)) {
		/* KWin 6.3.6 announces 5; the clamp because a newer KWin would
		 * announce one our XML does not describe. */
		sessione->screencast_version = MIN(versione, 5u);
		sessione->screencast =
		    wl_registry_bind(registro, nome, &zkde_screencast_unstable_v1_interface,
		                     sessione->screencast_version);
	} else if (!strcmp(interfaccia, wl_compositor_interface.name)) {
		sessione->compositor = wl_registry_bind(registro, nome, &wl_compositor_interface,
		                                        MIN(versione, 4u));
	} else if (!strcmp(interfaccia, wl_shm_interface.name)) {
		sessione->shm = wl_registry_bind(registro, nome, &wl_shm_interface, 1);
	} else if (!strcmp(interfaccia, zwlr_layer_shell_v1_interface.name)) {
		sessione->strati = wl_registry_bind(registro, nome, &zwlr_layer_shell_v1_interface,
		                                    MIN(versione, 1u));
	} else if (!strcmp(interfaccia, wl_output_interface.name)) {
		OutDir *uscita;

		if (sessione->how_many_outputs >= MAX_OUTPUTS) {
			registro_dice(AREA, "⚠ more than %d outputs: the others are ignored",
			              MAX_OUTPUTS);
			return;
		}
		uscita = &sessione->uscite[sessione->how_many_outputs++];
		uscita->global_name = nome;
		/* Version 4: the one that carries the `name` event. */
		uscita->versione = MIN(versione, 4u);
		uscita->oggetto =
		    wl_registry_bind(registro, nome, &wl_output_interface, uscita->versione);
		wl_output_add_listener(uscita->oggetto, &kwin_output_listener, uscita);
	}
}

static void on_global_away(void *dati, struct wl_registry *registro, uint32_t nome)
{
	KwinSessione *sessione = dati;

	for (unsigned i = 0; i < sessione->how_many_outputs; i++)
		if (sessione->uscite[i].global_name == nome)
			registro_dice(AREA, "⚠ output «%s» has disappeared from the compositor",
			              sessione->uscite[i].nome ? sessione->uscite[i].nome
			                                       : "unnamed");
}

static const struct wl_registry_listener registry_listener = { on_global, on_global_away };

/* ------------------------------------------------------------------ *
 * The stream
 * ------------------------------------------------------------------ */
static void on_stream_closed(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso)
{
	KwinSessione *sessione = dati;

	/* Just mark it: the stage notices on its own, because the
	 * PipeWire node disappears and the capture goes to `UNCONNECTED`. */
	sessione->chiuso = true;
	registro_dice(AREA, "KWin closed the capture stream");
}

static void on_stream_created(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso,
                             uint32_t nodo)
{
	KwinSessione *sessione = dati;

	sessione->nodo = nodo;
	sessione->node_arrived = true;
}

static void on_stream_fault(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso,
                             const char *errore)
{
	KwinSessione *sessione = dati;

	sessione->rifiutato = true;
	g_free(sessione->refusal_reason);
	sessione->refusal_reason = g_strdup(errore);
}

static const struct zkde_screencast_stream_unstable_v1_listener ascolto_flusso = {
	on_stream_closed, on_stream_created, on_stream_fault
};

/* ------------------------------------------------------------------ *
 * The loop
 * ------------------------------------------------------------------ */
/* One round of events with a deadline: `wl_display_dispatch` alone would block
 * without a ceiling.  false if the connection dropped or we were stopped. */
static bool gira(KwinSessione *sessione, int attesa_ms)
{
	struct pollfd sonda[2];
	int quanti = 1;

	while (wl_display_prepare_read(sessione->display) != 0)
		if (wl_display_dispatch_pending(sessione->display) < 0)
			return false;
	if (wl_display_flush(sessione->display) < 0 && errno != EAGAIN) {
		wl_display_cancel_read(sessione->display);
		return false;
	}

	sonda[0].fd = wl_display_get_fd(sessione->display);
	sonda[0].events = POLLIN;
	sonda[0].revents = 0;
	if (sessione->sveglia[0] >= 0) {
		sonda[1].fd = sessione->sveglia[0];
		sonda[1].events = POLLIN;
		sonda[1].revents = 0;
		quanti = 2;
	}

	if (poll(sonda, (nfds_t)quanti, attesa_ms) <= 0) {
		wl_display_cancel_read(sessione->display);
		return true;
	}
	if (quanti == 2 && (sonda[1].revents & POLLIN)) {
		wl_display_cancel_read(sessione->display);
		return false;
	}
	if (!(sonda[0].revents & POLLIN)) {
		wl_display_cancel_read(sessione->display);
		return !(sonda[0].revents & (POLLERR | POLLHUP));
	}

	if (wl_display_read_events(sessione->display) < 0)
		return false;
	return wl_display_dispatch_pending(sessione->display) >= 0;
}

static gpointer thread_pump(gpointer dati)
{
	KwinSessione *sessione = dati;

	while (gira(sessione, -1))
		;
	/* ⛔ AND IT IS MARKED — `[M]` 19 Sep 2026, the user's logout on KDE: KWin
	 *    dies with the session WITHOUT closing the stream gracefully, so
	 *    `on_stream_closed` does not arrive; and the PipeWire node disappearing does NOT
	 *    put the capture in error — the grab returns "zero" forever, like
	 *    a still scene.  ⇒ The connection dropping is the only sign, and
	 *    the child reads it with `kwin_chiuso()`. */
	sessione->chiuso = true;
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
struct wl_display *kwin_display_apri(char *quale, size_t quanto)
{
	const char *dichiarato = getenv("WAYLAND_DISPLAY");
	const char *runtime = getenv("XDG_RUNTIME_DIR");

	if (dichiarato && *dichiarato) {
		struct wl_display *display = wl_display_connect(dichiarato);

		if (display) {
			snprintf(quale, quanto, "%s", dichiarato);
			return display;
		}
	}
	for (int i = 0; i < 10; i++) {
		char nome[32], percorso[512];
		struct wl_display *display;

		snprintf(nome, sizeof nome, "wayland-%d", i);
		if (runtime) {
			snprintf(percorso, sizeof percorso, "%s/%s", runtime, nome);
			if (access(percorso, F_OK) != 0)
				continue;
		}
		display = wl_display_connect(nome);
		if (display) {
			snprintf(quale, quanto, "%s", nome);
			return display;
		}
	}
	return NULL;
}

/* There is a single output (nested or `--virtual`); the first that has a mode is taken. */
static const OutDir *choose_output(const KwinSessione *sessione)
{
	for (unsigned i = 0; i < sessione->how_many_outputs; i++)
		if (sessione->uscite[i].larghezza && sessione->uscite[i].altezza)
			return &sessione->uscite[i];
	return NULL;
}

/* The gate is closed: say WHY, because the symptom does not say it.  The
 * missing global has two causes with opposite cures, and KWin tells them apart only in
 * its own log (`QT_LOGGING_RULES='KWIN_UTILS.debug=true'`). */
static void explain_gate(GError **sbaglio)
{
	g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_PERMISSION_DENIED,
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
	KwinSessione *sessione = d;

	zwlr_layer_surface_v1_ack_configure(s, serial);
	if (!sessione->pixel_configurato && sessione->pixel_buf) {
		wl_surface_attach(sessione->pixel_sup, sessione->pixel_buf, 0, 0);
		wl_surface_damage_buffer(sessione->pixel_sup, 0, 0, 1, 1);
	}
	wl_surface_commit(sessione->pixel_sup);
	sessione->pixel_configurato = true;
}
static void pixel_closed(void *d, struct zwlr_layer_surface_v1 *s)
{
	registro_dice(AREA, "⚠ KWin closed our pixel on top: full-screen windows may be "
	                    "scanned out again, and their picture freeze");
}
static const struct zwlr_layer_surface_v1_listener PIXEL_LISTENER = { pixel_configure,
	                                                              pixel_closed };

static void metti_il_pixel(KwinSessione *sessione)
{
	struct wl_shm_pool *pool;
	struct wl_region *vuota;
	int fd;

	if (!sessione->compositor || !sessione->shm || !sessione->strati) {
		registro_dice(AREA, "⚠ KWin does not announce %s: no pixel on top — a "
		                    "full-screen window with the pointer hidden may freeze",
		              !sessione->strati ? "zwlr_layer_shell_v1" : "wl_compositor/wl_shm");
		return;
	}
	fd = memfd_create("remotix-pixel", MFD_CLOEXEC);
	if (fd < 0 || ftruncate(fd, 4) != 0) {
		if (fd >= 0)
			close(fd);
		return;
	}
	pool = wl_shm_create_pool(sessione->shm, fd, 4);
	sessione->pixel_buf = wl_shm_pool_create_buffer(pool, 0, 1, 1, 4, WL_SHM_FORMAT_ARGB8888);
	wl_shm_pool_destroy(pool);
	close(fd);
	sessione->pixel_sup = wl_compositor_create_surface(sessione->compositor);
	vuota = wl_compositor_create_region(sessione->compositor);
	wl_surface_set_input_region(sessione->pixel_sup, vuota);
	wl_region_destroy(vuota);
	sessione->pixel_strato = zwlr_layer_shell_v1_get_layer_surface(
	    sessione->strati, sessione->pixel_sup, NULL, ZWLR_LAYER_SHELL_V1_LAYER_OVERLAY,
	    "remotix-pixel");
	zwlr_layer_surface_v1_add_listener(sessione->pixel_strato, &PIXEL_LISTENER, sessione);
	zwlr_layer_surface_v1_set_size(sessione->pixel_strato, 1, 1);
	zwlr_layer_surface_v1_set_anchor(sessione->pixel_strato, ZWLR_LAYER_SURFACE_V1_ANCHOR_TOP |
	                                                             ZWLR_LAYER_SURFACE_V1_ANCHOR_LEFT);
	zwlr_layer_surface_v1_set_exclusive_zone(sessione->pixel_strato, -1);
	wl_surface_commit(sessione->pixel_sup);
}

KwinSessione *kwin_apri(GError **sbaglio)
{
	KwinSessione *sessione = g_new0(KwinSessione, 1);
	char socket[64] = "";
	gint64 scadenza;

	sessione->sveglia[0] = sessione->sveglia[1] = -1;
	sessione->eis = -1;

	sessione->display = kwin_display_apri(socket, sizeof socket);
	if (!sessione->display) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no Wayland compositor reachable in XDG_RUNTIME_DIR=%s",
		            getenv("XDG_RUNTIME_DIR") ? getenv("XDG_RUNTIME_DIR") : "(not set)");
		goto guasto;
	}

	sessione->registro = wl_display_get_registry(sessione->display);
	wl_registry_add_listener(sessione->registro, &registry_listener, sessione);
	/* Two rounds: the globals, then the events of the globals just bound (mode, name). */
	wl_display_roundtrip(sessione->display);
	wl_display_roundtrip(sessione->display);

	if (!sessione->screencast) {
		explain_gate(sbaglio);
		goto guasto;
	}

	sessione->scelta = choose_output(sessione);
	if (!sessione->scelta) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "KWin has no output with a mode (%u announced): without a "
		            "virtual screen KWin swallows the input too (kde.md §10.3)",
		            sessione->how_many_outputs);
		goto guasto;
	}

	/* ⛔ THE LISTENER RIGHT AFTER THE REQUEST AND BEFORE ANY ROUND: `failed`
	 *    is sent synchronously, and whoever is not listening misses it (`kde.md` §4.4). */
	sessione->flusso = zkde_screencast_unstable_v1_stream_output(
	    sessione->screencast, sessione->scelta->oggetto, PUNTATORE_METADATO);
	if (!sessione->flusso) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "capture request to KWin not created");
		goto guasto;
	}
	zkde_screencast_stream_unstable_v1_add_listener(sessione->flusso, &ascolto_flusso,
	                                                sessione);

	scadenza = g_get_monotonic_time() + (gint64)ATTESA_NODO_MS * 1000;
	while (!sessione->node_arrived && !sessione->rifiutato && !sessione->chiuso) {
		gint64 resta = (scadenza - g_get_monotonic_time()) / 1000;

		if (resta <= 0)
			break;
		if (!gira(sessione, (int)resta))
			break;
	}

	if (sessione->rifiutato) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "KWin refused the capture: %s",
		            sessione->refusal_reason ? sessione->refusal_reason : "no explanation");
		goto guasto;
	}
	if (!sessione->node_arrived) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "KWin did not announce the PipeWire node within %d ms", ATTESA_NODO_MS);
		goto guasto;
	}

	metti_il_pixel(sessione);
	{
		gint64 fine = g_get_monotonic_time() + 1000 * 1000;

		while (sessione->pixel_strato && !sessione->pixel_configurato &&
		       g_get_monotonic_time() < fine)
			if (!gira(sessione, 100))
				break;
	}
	if (!g_unix_open_pipe(sessione->sveglia, O_CLOEXEC, NULL)) {
		sessione->sveglia[0] = sessione->sveglia[1] = -1;
		registro_dice(AREA, "⚠ wake-up pipe not created: closing the capture "
		                    "will be less clean");
	}
	sessione->pompa = g_thread_new("remotix-kwin", thread_pump, sessione);

	registro_dice(AREA,
	              "⭐ KWin: zkde_screencast v%u on socket «%s», output «%s» %ux%u (%u in "
	              "all), PipeWire node %u; pixel on top %s",
	              sessione->screencast_version, socket,
	              sessione->scelta->nome ? sessione->scelta->nome : "unnamed",
	              sessione->scelta->larghezza, sessione->scelta->altezza,
	              sessione->how_many_outputs, sessione->nodo,
	              sessione->pixel_configurato ? "ON" : "⛔ NOT there");
	return sessione;

guasto:
	kwin_close(sessione);
	return NULL;
}

uint32_t kwin_node(const KwinSessione *sessione)
{
	return sessione ? sessione->nodo : 0;
}

void kwin_misura(const KwinSessione *sessione, uint32_t *larghezza, uint32_t *altezza)
{
	*larghezza = (sessione && sessione->scelta) ? sessione->scelta->larghezza : 0;
	*altezza = (sessione && sessione->scelta) ? sessione->scelta->altezza : 0;
}

const char *kwin_output_name(const KwinSessione *sessione)
{
	if (!sessione || !sessione->scelta)
		return NULL;
	return sessione->scelta->nome;
}

unsigned kwin_output_count(const KwinSessione *sessione)
{
	unsigned n = 0;

	if (!sessione)
		return 0;
	for (unsigned i = 0; i < sessione->how_many_outputs; i++)
		if (sessione->uscite[i].larghezza && sessione->uscite[i].altezza)
			n++;
	return n;
}

bool kwin_chiuso(const KwinSessione *sessione)
{
	return sessione ? sessione->chiuso : true;
}

/* ------------------------------------------------------------------ *
 * The input channel
 * ------------------------------------------------------------------ */
/* Keyboard 1, pointer 2, touch 4 — the xdg portal's mask
 * (`xdg-desktop-portal-kde/src/remotedesktop.cpp:457-460`). */
#define EIS_CAPACITA 7

static void detach_eis(KwinSessione *sessione)
{
	/* ⛔ With the token: KWin ties the EIS context to the life of the caller's D-Bus
	 *    NAME, so letting it go only works while the process lives — and
	 *    in a recovery the process stays alive, with one device too many. */
	if (sessione->known_token) {
		GDBusConnection *bus = sess_bus(NULL);

		if (bus) {
			GVariant *r = g_dbus_connection_call_sync(
			    bus, "org.kde.KWin", "/org/kde/KWin/EIS/RemoteDesktop",
			    "org.kde.KWin.EIS.RemoteDesktop", "disconnect",
			    g_variant_new("(i)", sessione->eis_token), NULL,
			    G_DBUS_CALL_FLAGS_NONE, 2000, NULL, NULL);
			if (r)
				g_variant_unref(r);
			g_object_unref(bus);
		}
		sessione->known_token = false;
	}
	if (sessione->eis >= 0) {
		close(sessione->eis);
		sessione->eis = -1;
	}
}

static int ask_eis(KwinSessione *sessione, GError **sbaglio)
{
	GDBusConnection *bus;
	GUnixFDList *descrittori = NULL;
	GVariant *risposta;
	gint indice = -1;

	bus = sess_bus(sbaglio);
	if (!bus)
		return -1;
	/* ⛔ THE DESCRIPTOR TRAVELS IN A SEPARATE LIST: `h` is an INDEX into
	 *    that list, and the zero read from the body would be standard input. */
	risposta = g_dbus_connection_call_with_unix_fd_list_sync(
	    bus, "org.kde.KWin", "/org/kde/KWin/EIS/RemoteDesktop",
	    "org.kde.KWin.EIS.RemoteDesktop", "connectToEIS", g_variant_new("(i)", EIS_CAPACITA),
	    G_VARIANT_TYPE("(hi)"), G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &descrittori, NULL,
	    sbaglio);
	g_object_unref(bus);
	if (!risposta)
		return -1;
	g_variant_get(risposta, "(hi)", &indice, &sessione->eis_token);
	g_variant_unref(risposta);
	sessione->eis = g_unix_fd_list_get(descrittori, indice, sbaglio);
	g_object_unref(descrittori);
	if (sessione->eis < 0)
		return -1;
	sessione->known_token = true;
	registro_dice(AREA, "⭐ KWin granted the input channel (connectToEIS, token %d, "
	                    "descriptor %d)", sessione->eis_token, sessione->eis);
	return sessione->eis;
}

int kwin_eis_fd(KwinSessione *sessione, GError **sbaglio)
{
	if (!sessione) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "no KWin stage");
		return -1;
	}
	if (sessione->eis >= 0)
		return sessione->eis;
	return ask_eis(sessione, sbaglio);
}

int kwin_eis_riattacca(KwinSessione *sessione, GError **sbaglio)
{
	if (!sessione) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "no KWin stage");
		return -1;
	}
	detach_eis(sessione);
	return ask_eis(sessione, sbaglio);
}

void kwin_close(KwinSessione *sessione)
{
	if (!sessione)
		return;

	/* First stop the pump, then touch the display: they are the same object
	 * seen from two threads. */
	if (sessione->pompa) {
		if (sessione->sveglia[1] >= 0) {
			ssize_t ignoto = write(sessione->sveglia[1], "x", 1);

			(void)ignoto;
		}
		g_thread_join(sessione->pompa);
		sessione->pompa = NULL;
	}
	if (sessione->sveglia[0] >= 0)
		close(sessione->sveglia[0]);
	if (sessione->sveglia[1] >= 0)
		close(sessione->sveglia[1]);

	detach_eis(sessione);
	if (sessione->pixel_strato)
		zwlr_layer_surface_v1_destroy(sessione->pixel_strato);
	if (sessione->pixel_sup)
		wl_surface_destroy(sessione->pixel_sup);
	if (sessione->pixel_buf)
		wl_buffer_destroy(sessione->pixel_buf);
	if (sessione->strati)
		zwlr_layer_shell_v1_destroy(sessione->strati);
	if (sessione->shm)
		wl_shm_destroy(sessione->shm);
	if (sessione->compositor)
		wl_compositor_destroy(sessione->compositor);
	if (sessione->flusso)
		zkde_screencast_stream_unstable_v1_close(sessione->flusso);
	if (sessione->screencast)
		zkde_screencast_unstable_v1_destroy(sessione->screencast);
	for (unsigned i = 0; i < sessione->how_many_outputs; i++) {
		if (sessione->uscite[i].oggetto) {
			/* `release` exists since version 3. */
			if (sessione->uscite[i].versione >= 3)
				wl_output_release(sessione->uscite[i].oggetto);
			else
				wl_output_destroy(sessione->uscite[i].oggetto);
		}
		g_free(sessione->uscite[i].nome);
	}
	if (sessione->registro)
		wl_registry_destroy(sessione->registro);
	if (sessione->display) {
		wl_display_flush(sessione->display);
		wl_display_disconnect(sessione->display);
	}
	g_free(sessione->refusal_reason);
	g_free(sessione);
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
static bool exec_leads_to(const char *exec, const char *canonico, char **visto)
{
	char **argv = NULL;
	char *vero;
	bool uguale;

	if (!g_shell_parse_argv(exec, NULL, &argv, NULL) || !argv || !argv[0]) {
		g_strfreev(argv);
		*visto = g_strdup(exec);
		return false;
	}
	*visto = g_strdup(argv[0]);
	/* CANONICAL paths on both sides, as KWin does: a link
	 * leading to the binary counts as much as the binary. */
	vero = realpath(argv[0], NULL);
	uguale = vero && strcmp(vero, canonico) == 0;
	free(vero);
	g_strfreev(argv);
	return uguale;
}

bool kwin_verifica_permesso(char *perche, size_t quanto)
{
	char *canonico = realpath("/proc/self/exe", NULL);
	GKeyFile *chiavi = g_key_file_new();
	GError *sbaglio = NULL;
	char *exec = NULL, *interfacce = NULL, *visto = NULL;
	bool va = false;

	if (!canonico) {
		snprintf(perche, quanto, "I do not know which binary I am running: %s", strerror(errno));
		goto fine;
	}
	if (!g_key_file_load_from_file(chiavi, PERMISSION_DESKTOP_FILE, G_KEY_FILE_NONE, &sbaglio)) {
		snprintf(perche, quanto,
		         "RX-KDE-001: %s %s (%s). Remedy: reinstall REMOTIX with the installer",
		         PERMISSION_DESKTOP_FILE,
		         g_error_matches(sbaglio, G_FILE_ERROR, G_FILE_ERROR_NOENT) ? "is missing"
		                                                                  : "cannot be read",
		         sbaglio->message);
		goto fine;
	}
	exec = g_key_file_get_string(chiavi, "Desktop Entry", "Exec", NULL);
	if (!exec || !exec_leads_to(exec, canonico, &visto)) {
		snprintf(perche, quanto,
		         "RX-KDE-002: in %s Exec=%s, but the running binary is %s. Remedy: "
		         "reinstall REMOTIX with the installer",
		         PERMISSION_DESKTOP_FILE, visto ? visto : "(missing)", canonico);
		goto fine;
	}
	interfacce = g_key_file_get_string(chiavi, "Desktop Entry", "X-KDE-Wayland-Interfaces",
	                                   NULL);
	if (interfacce) {
		char **voci = g_strsplit_set(interfacce, ",; \t", -1);

		for (char **v = voci; *v; v++)
			if (strcmp(*v, "zkde_screencast_unstable_v1") == 0)
				va = true;
		g_strfreev(voci);
	}
	if (!va) {
		snprintf(perche, quanto,
		         "RX-KDE-003: in %s X-KDE-Wayland-Interfaces=%s, without "
		         "zkde_screencast_unstable_v1. Remedy: reinstall REMOTIX with the installer",
		         PERMISSION_DESKTOP_FILE, interfacce ? interfacce : "(missing)");
		goto fine;
	}
	snprintf(perche, quanto, "%s checked (it belongs to the package: I do not write it), Exec=%s",
	         PERMISSION_DESKTOP_FILE, canonico);
fine:
	g_clear_error(&sbaglio);
	g_key_file_unref(chiavi);
	g_free(exec);
	g_free(interfacce);
	g_free(visto);
	free(canonico);
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

int kwin_disposizione(const char *nome, GError **sbaglio)
{
	g_autofree char *cartella = sessione_cartella_kde();
	g_autofree char *disposizione = NULL;
	g_autofree char *variante = NULL;
	g_autofree char *percorso = NULL;
	g_autofree char *testo = NULL;
	g_autoptr(GDBusConnection) bus = NULL;
	const char *par = nome ? strchr(nome, '(') : NULL;

	if (!nome || !*nome) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "no name");
		return -1;
	}
	/* `RCP.md` §4.5: `de(neo)` ⇒ LayoutList=de, VariantList=neo.
	 * ⛔ The name ends up inside an INI file: no newline, no `[`. */
	if (par) {
		const char *chiusa = strchr(par + 1, ')');

		if (!chiusa || chiusa[1] != '\0' ||
		    !clean_xkb_name(nome, (size_t) (par - nome)) ||
		    !clean_xkb_name(par + 1, (size_t) (chiusa - par - 1))) {
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
			            "invalid name «%s»", nome);
			return -1;
		}
		disposizione = g_strndup(nome, (size_t) (par - nome));
		variante = g_strndup(par + 1, (size_t) (chiusa - par - 1));
	} else {
		if (!clean_xkb_name(nome, strlen(nome))) {
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
			            "invalid name «%s»", nome);
			return -1;
		}
		disposizione = g_strdup(nome);
		variante = g_strdup("");
	}

	/* ⛔ Only if the folder is there: `componi_ambiente()` creates it and
	 *    puts it in `XDG_CONFIG_DIRS`.  If it is not there, KWin does not read it — and
	 *    writing into it would be a false "fact". */
	if (!cartella || !g_file_test(cartella, G_FILE_TEST_IS_DIR)) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "the session's configuration folder (%s) is missing: KWin "
		            "does not look at it",
		            cartella ? cartella : "XDG_RUNTIME_DIR missing");
		return -1;
	}
	percorso = g_build_filename(cartella, "kxkbrc", NULL);
	testo = g_strdup_printf("[Layout]\n"
	                        "LayoutList[$i]=%s\n"
	                        "VariantList[$i]=%s\n",
	                        disposizione, variante);
	if (!g_file_set_contents(percorso, testo, -1, sbaglio))
		return -1;

	bus = sess_bus(sbaglio);
	if (!bus)
		return -1;
	if (!g_dbus_connection_emit_signal(bus, NULL, "/Layouts", "org.kde.keyboard",
	                                   "reloadConfig", NULL, sbaglio))
		return -1;
	/* ⛔ `[M]` 6 Oct 2026, KWin 6.6.6 (Ubuntu 26.04): nobody listens to
	 *    `reloadConfig` ANY MORE — `KeyboardLayout::init()` watches kxkbrc with a
	 *    `KConfigWatcher`, that is the signal `org.kde.kconfig.notify
	 *    ConfigChanged` on the path `/kxkbrc`, and rebuilds the keymap if among the
	 *    changed groups there is "Layout" (`handleXkbConfigChanged`).  Without it, the
	 *    session stayed `English (US)` (F-009 red).  Both are sent:
	 *    the old one for KWin up to 6.3, this one for the newer ones. */
	{
		GVariantBuilder gruppi;
		const char *chiavi[] = { "LayoutList", "VariantList" };
		GVariantBuilder nomi;

		g_variant_builder_init(&nomi, G_VARIANT_TYPE("aay"));
		for (size_t i = 0; i < G_N_ELEMENTS(chiavi); i++)
			g_variant_builder_add_value(&nomi, g_variant_new_bytestring(chiavi[i]));
		g_variant_builder_init(&gruppi, G_VARIANT_TYPE("a{saay}"));
		g_variant_builder_add(&gruppi, "{saay}", "Layout", &nomi);
		if (!g_dbus_connection_emit_signal(bus, NULL, "/kxkbrc", "org.kde.kconfig.notify",
		                                   "ConfigChanged",
		                                   g_variant_new("(a{saay})", &gruppi), sbaglio))
			return -1;
	}
	/* ⚠ The signal has no reply: the queue is flushed so it leaves NOW. */
	g_dbus_connection_flush_sync(bus, NULL, NULL);
	return 0;
}

/* ------------------------------------------------------------------ *
 * ⭐⭐ THE NESTED KWIN — see `kwin.h`
 * ------------------------------------------------------------------ */

#define OSPITE_CARTELLA "remotix-kwin-ospite"
/* How long the helper waits for labwc's socket.  `[M]` labwc is up in about
 * a tenth of a second on the test machine: the ceiling is for a loaded
 * machine, not a guess at the normal case. */
#define OSPITE_NASCITA_MS 10000
/* The refresh of labwc's screenless output.  KWin nested draws its next frame
 * only when labwc says the previous one was presented, and labwc presents on
 * ITS clock: at 60 Hz the two clocks drift and frames are lost — `[M]` 11 Oct
 * 2026, 60 fps animation at 3824x2064: 59 fps with KWin --virtual, 52-55
 * nested at 60 Hz.  A faster host clock answers sooner; KWin keeps its own
 * 60 (the host reports no refresh, `wayland_output.cpp` falls back to 60). */
#ifndef OSPITE_MHZ
#define OSPITE_MHZ 240000
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
 */
static const char OSPITE_RC[] =
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
    "</labwc_config>\n";

static char *ospite_cartella(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (!runtime || !*runtime)
		return NULL;
	return g_build_filename(runtime, OSPITE_CARTELLA, NULL);
}

char *kwin_ospite_display(void)
{
	g_autofree char *cartella = ospite_cartella();

	return cartella ? g_build_filename(cartella, "wayland-0", NULL) : NULL;
}

bool kwin_ospite_c_e(void)
{
	g_autofree char *display = kwin_ospite_display();
	struct wl_display *d;

	if (!display || access(display, F_OK) != 0)
		return false;
	d = wl_display_connect(display);
	if (!d)
		return false;
	wl_display_disconnect(d);
	return true;
}

/* ⛔ The size is read back from labwc, not believed from the answer
 *    (`wlroots.h`: «the truth is told by the frame»). */
static bool ospite_chiedi(const char *display, uint32_t larghezza, uint32_t altezza,
                          GError **sbaglio)
{
	WlrPalco *ospite = wlr_apri_su(display, sbaglio);
	uint32_t l = 0, a = 0;
	WlrSizeOutcome e;

	if (!ospite)
		return false;
	e = wlr_misura_chiedi_hz(ospite, larghezza, altezza, OSPITE_MHZ, 2.0, sbaglio);
	if (e == WLR_MISURA_ANNULLATA) {
		/* an old serial: one more try, as `wlroots.h` allows */
		g_clear_error(sbaglio);
		e = wlr_misura_chiedi_hz(ospite, larghezza, altezza, OSPITE_MHZ, 2.0, sbaglio);
	}
	wlr_measure(ospite, &l, &a);
	wlr_close(ospite);
	if (l == larghezza && a == altezza)
		return true;
	if (sbaglio && !*sbaglio)
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "labwc (KWin's host) was asked for %ux%u and its output is %ux%u "
		            "(outcome %d)",
		            larghezza, altezza, l, a, (int)e);
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
	struct zwlr_layer_shell_v1 *strati;
	bool configurata, chiusa;
} Ticker;

static void ticker_global(void *d, struct wl_registry *r, uint32_t nome, const char *iface,
                          uint32_t v)
{
	Ticker *t = d;

	if (strcmp(iface, wl_compositor_interface.name) == 0)
		t->compositor = wl_registry_bind(r, nome, &wl_compositor_interface, MIN(v, 4u));
	else if (strcmp(iface, wl_shm_interface.name) == 0)
		t->shm = wl_registry_bind(r, nome, &wl_shm_interface, 1);
	else if (strcmp(iface, zwlr_layer_shell_v1_interface.name) == 0)
		t->strati = wl_registry_bind(r, nome, &zwlr_layer_shell_v1_interface, MIN(v, 1u));
}
static void ticker_global_away(void *d, struct wl_registry *r, uint32_t n) {}
static const struct wl_registry_listener TICKER_REGISTRY = { ticker_global, ticker_global_away };

static void ticker_configure(void *d, struct zwlr_layer_surface_v1 *s, uint32_t serial,
                             uint32_t l, uint32_t a)
{
	Ticker *t = d;

	zwlr_layer_surface_v1_ack_configure(s, serial);
	t->configurata = true;
}
static void ticker_closed(void *d, struct zwlr_layer_surface_v1 *s)
{
	((Ticker *)d)->chiusa = true;
}
static const struct zwlr_layer_surface_v1_listener TICKER_LAYER = { ticker_configure,
	                                                            ticker_closed };

/* It runs in its own process, child of the start-line helper: it ends when
 * labwc ends (the connection drops) or when its parent — which has become
 * the KWin wrapper — dies. */
static void ticker_vive(const char *display)
{
	Ticker t = { 0 };
	struct wl_display *d;
	struct wl_registry *reg;
	struct wl_surface *sup;
	struct zwlr_layer_surface_v1 *strato;
	struct wl_region *vuota;
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
	if (!t.compositor || !t.shm || !t.strati) {
		g_printerr("remotix --kwin-annidato: ⛔ ticker: labwc lacks %s\n",
		           !t.strati ? "zwlr_layer_shell_v1" : "wl_compositor/wl_shm");
		_exit(1);
	}
	fd = memfd_create("remotix-ticker", MFD_CLOEXEC);
	if (fd < 0 || ftruncate(fd, 4) != 0)
		_exit(1);
	pool = wl_shm_create_pool(t.shm, fd, 4);
	/* one ARGB pixel, all zero: fully transparent */
	pixel = wl_shm_pool_create_buffer(pool, 0, 1, 1, 4, WL_SHM_FORMAT_ARGB8888);
	sup = wl_compositor_create_surface(t.compositor);
	vuota = wl_compositor_create_region(t.compositor);
	wl_surface_set_input_region(sup, vuota); /* no pointer, ever */
	strato = zwlr_layer_shell_v1_get_layer_surface(t.strati, sup, NULL,
	                                                ZWLR_LAYER_SHELL_V1_LAYER_OVERLAY,
	                                                "remotix-ticker");
	zwlr_layer_surface_v1_add_listener(strato, &TICKER_LAYER, &t);
	zwlr_layer_surface_v1_set_size(strato, 1, 1);
	zwlr_layer_surface_v1_set_anchor(strato, ZWLR_LAYER_SURFACE_V1_ANCHOR_TOP |
	                                             ZWLR_LAYER_SURFACE_V1_ANCHOR_LEFT);
	zwlr_layer_surface_v1_set_exclusive_zone(strato, -1);
	wl_surface_commit(sup);
	while (!t.configurata && !t.chiusa)
		if (wl_display_dispatch(d) < 0)
			_exit(0);
	/* ⛔ The tick is a CLOCK, not «after every event»: labwc answers each
	 *    commit (release, frame), and a loop that commits again on the answer
	 *    makes labwc repaint as fast as it can — `[M]` the first draft: labwc
	 *    at 85 % of a core, the ticker at 17 %. */
	for (gint64 prossimo = g_get_monotonic_time(); !t.chiusa;) {
		gint64 ora = g_get_monotonic_time();
		struct pollfd p = { wl_display_get_fd(d), POLLIN, 0 };

		if (ora >= prossimo) {
			wl_surface_attach(sup, pixel, 0, 0);
			wl_surface_damage_buffer(sup, 0, 0, 1, 1);
			wl_surface_commit(sup);
			prossimo += (gint64)TICKER_MS * 1000;
			if (prossimo < ora)
				prossimo = ora + (gint64)TICKER_MS * 1000;
		}
		if (wl_display_flush(d) < 0 || wl_display_dispatch_pending(d) < 0)
			break;
		if (poll(&p, 1, (int)MAX(1, (prossimo - g_get_monotonic_time()) / 1000)) > 0) {
			if (p.revents & (POLLERR | POLLHUP))
				break;
			if (wl_display_dispatch(d) < 0)
				break;
		}
	}
	_exit(0);
}

int kwin_annidato_vive(int argc, char **argv)
{
	g_autofree char *cartella = ospite_cartella();
	g_autofree char *config = NULL;
	g_autofree char *rc = NULL;
	g_autofree char *display = NULL;
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GPtrArray) riga = NULL;
	g_autofree char *labwc_c_e = NULL;
	unsigned long larghezza, altezza;
	const char *nodo;
	pid_t labwc;
	gint64 t0 = g_get_monotonic_time(), scadenza;
	bool pronto = false;

	/* argv: remotix --kwin-annidato W H NODE -- wrapper args… */
	if (argc < 7 || strcmp(argv[5], "--") != 0) {
		g_printerr("remotix --kwin-annidato W H NODE -- <kwin_wayland_wrapper> [args]\n");
		return 2;
	}
	larghezza = strtoul(argv[2], NULL, 10);
	altezza = strtoul(argv[3], NULL, 10);
	nodo = argv[4];
	if (larghezza < 200 || altezza < 200 || larghezza > 8192 || altezza > 8192) {
		g_printerr("remotix --kwin-annidato: size %lux%lu out of range\n", larghezza,
		           altezza);
		return 2;
	}
	if (!cartella) {
		g_printerr("remotix --kwin-annidato: XDG_RUNTIME_DIR is not set\n");
		return 1;
	}
	/* ⛔ Without labwc the session must still be born: KWin `--virtual`, as
	 *    before 11 Oct 2026, and SAID — the desktop keeps the size it is born
	 *    with (the page centres it).  `[R]` it is the case of RHEL/Alma 10,
	 *    where EPEL has no labwc (`packaging/rpm/remotix.spec`). */
	labwc_c_e = g_find_program_in_path("labwc");
	if (!labwc_c_e) {
		riga = g_ptr_array_new();
		for (int i = 6; i < argc; i++)
			g_ptr_array_add(riga, argv[i]);
		g_ptr_array_add(riga, (char *)"--virtual");
		g_ptr_array_add(riga, NULL);
		g_printerr("remotix --kwin-annidato: ⛔ labwc is not installed: KWin --virtual, "
		           "and the desktop will NOT take the window's size at reattach "
		           "(DECLARED FALLBACK)\n");
		execvp(argv[6], (char **)riga->pdata);
		g_printerr("remotix --kwin-annidato: %s does not start: %s\n", argv[6],
		           strerror(errno));
		return 1;
	}
	config = g_build_filename(cartella, "labwc", NULL);
	rc = g_build_filename(config, "rc.xml", NULL);
	display = g_build_filename(cartella, "wayland-0", NULL);
	g_mkdir_with_parents(config, 0700);
	if (!g_file_set_contents(rc, OSPITE_RC, -1, &sbaglio)) {
		g_printerr("remotix --kwin-annidato: %s\n", sbaglio->message);
		return 1;
	}

	labwc = fork();
	if (labwc < 0) {
		g_printerr("remotix --kwin-annidato: fork: %s\n", strerror(errno));
		return 1;
	}
	if (labwc == 0) {
		/* ⛔ labwc gets a RUNTIME FOLDER OF ITS OWN: its socket is then
		 *    `<runtime>/remotix-kwin-ospite/wayland-0`, and KWin's `wayland-N`
		 *    stays the only one in `XDG_RUNTIME_DIR` — whoever scans it
		 *    (`kwin_display_apri()`, the clipboard) can never land on the
		 *    host by mistake. */
		g_setenv("XDG_RUNTIME_DIR", cartella, TRUE);
		g_unsetenv("WAYLAND_DISPLAY");
		g_unsetenv("WAYLAND_SOCKET");
		g_unsetenv("DISPLAY");
		/* ⛔ Never: it would publish the HOST's display to the bus and to
		 *    systemd, and the session's programs would open on a screen
		 *    nobody sees. */
		g_unsetenv("LABWC_UPDATE_ACTIVATION_ENV");
		g_setenv("WLR_BACKENDS", "headless", TRUE);
		g_setenv("WLR_LIBINPUT_NO_DEVICES", "1", TRUE);
		if (strcmp(nodo, "pixman") == 0)
			g_setenv("WLR_RENDERER", "pixman", TRUE);
		else if (strcmp(nodo, "-") != 0)
			g_setenv("WLR_RENDER_DRM_DEVICE", nodo, TRUE);
		execlp("labwc", "labwc", "-C", config, (char *)NULL);
		g_printerr("remotix --kwin-annidato: labwc does not start: %s\n", strerror(errno));
		_exit(127);
	}

	scadenza = t0 + (gint64)OSPITE_NASCITA_MS * 1000;
	while (g_get_monotonic_time() < scadenza) {
		int stato;

		if (waitpid(labwc, &stato, WNOHANG) == labwc) {
			g_printerr("remotix --kwin-annidato: ⛔ labwc (KWin's host) exited at "
			           "birth (status %d)\n",
			           stato);
			return 1;
		}
		if (access(display, F_OK) == 0) {
			struct wl_display *d = wl_display_connect(display);

			if (d) {
				wl_display_disconnect(d);
				pronto = true;
				break;
			}
		}
		g_usleep(20000);
	}
	if (!pronto) {
		g_printerr("remotix --kwin-annidato: ⛔ labwc's socket %s did not appear "
		           "within %d ms\n",
		           display, OSPITE_NASCITA_MS);
		kill(labwc, SIGTERM);
		return 1;
	}
	/* labwc's headless output is born 1280x720 hard-wired (`wlroots.h`): it is
	 * brought to the client's size BEFORE KWin opens its window, so the
	 * desktop is born at the right size and is not resized at birth. */
	if (!ospite_chiedi(display, (uint32_t)larghezza, (uint32_t)altezza, &sbaglio)) {
		g_printerr("remotix --kwin-annidato: ⛔ %s\n",
		           sbaglio ? sbaglio->message : "the host's size was not set");
		kill(labwc, SIGTERM);
		return 1;
	}
	{
		pid_t ticker = fork();

		if (ticker == 0)
			ticker_vive(display);
		if (ticker < 0)
			g_printerr("remotix --kwin-annidato: ⛔ the ticker did not start (%s): KWin "
			           "may freeze on a frame without damage\n", strerror(errno));
	}
	g_printerr("remotix --kwin-annidato: ⭐ labwc (pid %d, node %s) at %lux%lu on %s in "
	           "%lld ms; now KWin, nested in it\n",
	           (int)labwc, nodo, larghezza, altezza, display,
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
	riga = g_ptr_array_new();
	for (int i = 6; i < argc; i++)
		g_ptr_array_add(riga, argv[i]);
	g_ptr_array_add(riga, (char *)"--wayland-display");
	g_ptr_array_add(riga, display);
	g_ptr_array_add(riga, NULL);
	execvp(argv[6], (char **)riga->pdata);
	g_printerr("remotix --kwin-annidato: %s does not start: %s\n", argv[6], strerror(errno));
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

static void mode_global(void *d, struct wl_registry *r, uint32_t nome, const char *iface,
                        uint32_t v)
{
	struct wl_output **o = d;

	/* version 2: `done` and `scale`, and no `name`/`description` to listen to */
	if (!*o && strcmp(iface, wl_output_interface.name) == 0)
		*o = wl_registry_bind(r, nome, &wl_output_interface, MIN(v, 2u));
}
static void mode_global_away(void *d, struct wl_registry *r, uint32_t nome) {}
static const struct wl_registry_listener MODE_REGISTRY = { mode_global, mode_global_away };

bool kwin_ospite_misura(uint32_t larghezza, uint32_t altezza, double attesa_s,
                        GError **sbaglio)
{
	g_autofree char *display = kwin_ospite_display();
	struct wl_display *kwin;
	struct wl_registry *reg;
	struct wl_output *uscita = NULL;
	Mode m = { 0, 0 };
	char socket[64];
	gint64 t0 = g_get_monotonic_time(), scadenza;

	if (!kwin_ospite_c_e()) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "no host for KWin (%s): this Plasma session was born with KWin "
		            "--virtual, which cannot change size",
		            display ? display : "XDG_RUNTIME_DIR missing");
		return false;
	}
	if (!ospite_chiedi(display, larghezza, altezza, sbaglio))
		return false;

	kwin = kwin_display_apri(socket, sizeof socket);
	if (!kwin) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "the host is at %ux%u but KWin cannot be reached to read it back",
		            larghezza, altezza);
		return false;
	}
	reg = wl_display_get_registry(kwin);
	wl_registry_add_listener(reg, &MODE_REGISTRY, &uscita);
	wl_display_roundtrip(kwin);
	if (uscita)
		wl_output_add_listener(uscita, &MODE_LISTENER, &m);
	/* ⚠ KWin throttles the host's configure by one refresh period
	 *   (`wayland_output.cpp`, `m_configureThrottleTimer`): the new mode
	 *   arrives a few milliseconds after labwc's, and it is waited for. */
	scadenza = t0 + (gint64)(attesa_s * 1e6);
	while (uscita && wl_display_roundtrip(kwin) >= 0) {
		if (m.l == larghezza && m.a == altezza)
			break;
		if (g_get_monotonic_time() >= scadenza)
			break;
		g_usleep(5000);
	}
	if (uscita)
		wl_output_destroy(uscita);
	wl_registry_destroy(reg);
	wl_display_disconnect(kwin);
	if (m.l != larghezza || m.a != altezza) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "the host is at %ux%u but KWin's output is %ux%u after %.1f s",
		            larghezza, altezza, m.l, m.a, attesa_s);
		return false;
	}
	registro_dice(AREA,
	              "⭐ nested KWin: the host and KWin's output are at %ux%u after %lld ms "
	              "(read back from KWin on «%s», not believed)",
	              larghezza, altezza, (long long)((g_get_monotonic_time() - t0) / 1000),
	              socket);
	return true;
}


bool kwin_ospite_assesta(double attesa_s, GError **sbaglio)
{
	g_autofree char *display = kwin_ospite_display();
	WlrPalco *ospite;
	uint32_t l = 0, a = 0;

	if (!kwin_ospite_c_e())
		return true; /* no host: nothing to wait for */
	ospite = wlr_apri_su(display, sbaglio);
	if (!ospite)
		return false;
	wlr_measure(ospite, &l, &a);
	wlr_close(ospite);
	/* same size ⇒ no request leaves (`wlr_misura_chiedi`: GIA_COSI); only the wait */
	return kwin_ospite_misura(l, a, attesa_s, sbaglio);
}
