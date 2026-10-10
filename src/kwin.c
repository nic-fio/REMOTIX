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

#define USCITE_MAX 8

/* The path of the permission: system-wide, because it applies to every user, and
 * KWin looks in `XDG_DATA_DIRS` (which contains `/usr/share`).  Since phase 17 the
 * package ships it and REMOTIX only checks it (`kwin_verifica_permesso`). */
#define PERMESSO_DESKTOP "/usr/share/applications/org.kde.remotix.desktop"

typedef struct
{
	struct wl_output *oggetto;
	uint32_t nome_globale;
	uint32_t versione;
	char *nome; /* "Virtual-0" with `--virtual` */
	uint32_t larghezza, altezza; /* of the CURRENT mode, in pixels */
} Uscita;

struct KwinSessione
{
	struct wl_display *display;
	struct wl_registry *registro;
	struct zkde_screencast_unstable_v1 *screencast;
	struct zkde_screencast_stream_unstable_v1 *flusso;
	uint32_t versione_screencast;

	Uscita uscite[USCITE_MAX];
	unsigned quante_uscite;
	const Uscita *scelta;

	uint32_t nodo;
	bool nodo_arrivato;
	bool rifiutato;
	char *motivo_rifiuto;
	volatile bool chiuso;

	/* ⛔ THE LOOP THAT KEEPS THE CONNECTION ALIVE IS NOT A LUXURY: the stream lives
	 *    as long as the Wayland connection (`screencast_v1.cpp:28-35`), and a
	 *    connection nobody serves does not deliver `closed`. */
	GThread *pompa;
	int sveglia[2];

	/* The input channel: the descriptor and the token of `connectToEIS`. */
	int eis;
	gint gettone_eis;
	bool gettone_noto;
};

/* ------------------------------------------------------------------ *
 * The registry
 * ------------------------------------------------------------------ */
static void su_uscita_geometria(void *dati, struct wl_output *uscita, int32_t x, int32_t y,
                                int32_t larghezza_mm, int32_t altezza_mm, int32_t sottopixel,
                                const char *costruttore, const char *modello,
                                int32_t trasformazione)
{
}

static void su_uscita_modo(void *dati, struct wl_output *oggetto, uint32_t flag,
                           int32_t larghezza, int32_t altezza, int32_t aggiornamento)
{
	Uscita *uscita = dati;

	if (!(flag & WL_OUTPUT_MODE_CURRENT))
		return;
	uscita->larghezza = (uint32_t)MAX(0, larghezza);
	uscita->altezza = (uint32_t)MAX(0, altezza);
}

static void su_uscita_fine(void *dati, struct wl_output *oggetto)
{
}

static void su_uscita_scala(void *dati, struct wl_output *oggetto, int32_t scala)
{
	/* The scale does not touch the buffer's pixels (`core/output.cpp:457-459`), but
	 * it shifts the input coordinate space: it is logged. */
	if (scala != 1)
		registro_dice(AREA, "⚠ KWin's output has scale %d: the logical desktop is "
		                    "smaller than the captured buffer", scala);
}

static void su_uscita_nome(void *dati, struct wl_output *oggetto, const char *nome)
{
	Uscita *uscita = dati;

	g_free(uscita->nome);
	uscita->nome = g_strdup(nome);
}

static void su_uscita_descrizione(void *dati, struct wl_output *oggetto,
                                  const char *descrizione)
{
}

static const struct wl_output_listener ascolto_uscita = {
	su_uscita_geometria, su_uscita_modo, su_uscita_fine,
	su_uscita_scala,     su_uscita_nome, su_uscita_descrizione,
};

static void su_globale(void *dati, struct wl_registry *registro, uint32_t nome,
                       const char *interfaccia, uint32_t versione)
{
	KwinSessione *sessione = dati;

	if (!strcmp(interfaccia, zkde_screencast_unstable_v1_interface.name)) {
		/* KWin 6.3.6 announces 5; the clamp because a newer KWin would
		 * announce one our XML does not describe. */
		sessione->versione_screencast = MIN(versione, 5u);
		sessione->screencast =
		    wl_registry_bind(registro, nome, &zkde_screencast_unstable_v1_interface,
		                     sessione->versione_screencast);
	} else if (!strcmp(interfaccia, wl_output_interface.name)) {
		Uscita *uscita;

		if (sessione->quante_uscite >= USCITE_MAX) {
			registro_dice(AREA, "⚠ more than %d outputs: the others are ignored",
			              USCITE_MAX);
			return;
		}
		uscita = &sessione->uscite[sessione->quante_uscite++];
		uscita->nome_globale = nome;
		/* Version 4: the one that carries the `name` event. */
		uscita->versione = MIN(versione, 4u);
		uscita->oggetto =
		    wl_registry_bind(registro, nome, &wl_output_interface, uscita->versione);
		wl_output_add_listener(uscita->oggetto, &ascolto_uscita, uscita);
	}
}

static void su_globale_via(void *dati, struct wl_registry *registro, uint32_t nome)
{
	KwinSessione *sessione = dati;

	for (unsigned i = 0; i < sessione->quante_uscite; i++)
		if (sessione->uscite[i].nome_globale == nome)
			registro_dice(AREA, "⚠ output «%s» has disappeared from the compositor",
			              sessione->uscite[i].nome ? sessione->uscite[i].nome
			                                       : "unnamed");
}

static const struct wl_registry_listener ascolto_registro = { su_globale, su_globale_via };

/* ------------------------------------------------------------------ *
 * The stream
 * ------------------------------------------------------------------ */
static void su_flusso_chiuso(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso)
{
	KwinSessione *sessione = dati;

	/* Just mark it: the stage notices on its own, because the
	 * PipeWire node disappears and the capture goes to `UNCONNECTED`. */
	sessione->chiuso = true;
	registro_dice(AREA, "KWin closed the capture stream");
}

static void su_flusso_creato(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso,
                             uint32_t nodo)
{
	KwinSessione *sessione = dati;

	sessione->nodo = nodo;
	sessione->nodo_arrivato = true;
}

static void su_flusso_guasto(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso,
                             const char *errore)
{
	KwinSessione *sessione = dati;

	sessione->rifiutato = true;
	g_free(sessione->motivo_rifiuto);
	sessione->motivo_rifiuto = g_strdup(errore);
}

static const struct zkde_screencast_stream_unstable_v1_listener ascolto_flusso = {
	su_flusso_chiuso, su_flusso_creato, su_flusso_guasto
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

static gpointer thread_pompa(gpointer dati)
{
	KwinSessione *sessione = dati;

	while (gira(sessione, -1))
		;
	/* ⛔ AND IT IS MARKED — `[M]` 19 Sep 2026, the user's logout on KDE: KWin
	 *    dies with the session WITHOUT closing the stream gracefully, so
	 *    `su_flusso_chiuso` does not arrive; and the PipeWire node disappearing does NOT
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

/* With `--virtual` there is a single output; the first that has a mode is taken. */
static const Uscita *scegli_uscita(const KwinSessione *sessione)
{
	for (unsigned i = 0; i < sessione->quante_uscite; i++)
		if (sessione->uscite[i].larghezza && sessione->uscite[i].altezza)
			return &sessione->uscite[i];
	return NULL;
}

/* The gate is closed: say WHY, because the symptom does not say it.  The
 * missing global has two causes with opposite cures, and KWin tells them apart only in
 * its own log (`QT_LOGGING_RULES='KWIN_UTILS.debug=true'`). */
static void spiega_il_cancello(GError **sbaglio)
{
	g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_PERMISSION_DENIED,
	            "KWin does not announce zkde_screencast_unstable_v1: the capture permission "
	            "is denied, it is not the protocol that is missing. Our .desktop %s (%s). And "
	            "KWin's environment must have XDG_MENU_PREFIX=plasma-, or the service "
	            "index is built empty. KWin gives the exact cause with "
	            "QT_LOGGING_RULES='KWIN_UTILS.debug=true'",
	            access(PERMESSO_DESKTOP, F_OK) == 0 ? "is there" : "is NOT there", PERMESSO_DESKTOP);
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
	wl_registry_add_listener(sessione->registro, &ascolto_registro, sessione);
	/* Two rounds: the globals, then the events of the globals just bound (mode, name). */
	wl_display_roundtrip(sessione->display);
	wl_display_roundtrip(sessione->display);

	if (!sessione->screencast) {
		spiega_il_cancello(sbaglio);
		goto guasto;
	}

	sessione->scelta = scegli_uscita(sessione);
	if (!sessione->scelta) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "KWin has no output with a mode (%u announced): without a "
		            "virtual screen KWin swallows the input too (kde.md §10.3)",
		            sessione->quante_uscite);
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
	while (!sessione->nodo_arrivato && !sessione->rifiutato && !sessione->chiuso) {
		gint64 resta = (scadenza - g_get_monotonic_time()) / 1000;

		if (resta <= 0)
			break;
		if (!gira(sessione, (int)resta))
			break;
	}

	if (sessione->rifiutato) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "KWin refused the capture: %s",
		            sessione->motivo_rifiuto ? sessione->motivo_rifiuto : "no explanation");
		goto guasto;
	}
	if (!sessione->nodo_arrivato) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "KWin did not announce the PipeWire node within %d ms", ATTESA_NODO_MS);
		goto guasto;
	}

	if (!g_unix_open_pipe(sessione->sveglia, O_CLOEXEC, NULL)) {
		sessione->sveglia[0] = sessione->sveglia[1] = -1;
		registro_dice(AREA, "⚠ wake-up pipe not created: closing the capture "
		                    "will be less clean");
	}
	sessione->pompa = g_thread_new("remotix-kwin", thread_pompa, sessione);

	registro_dice(AREA,
	              "⭐ KWin: zkde_screencast v%u on socket «%s», output «%s» %ux%u (%u in "
	              "all), PipeWire node %u",
	              sessione->versione_screencast, socket,
	              sessione->scelta->nome ? sessione->scelta->nome : "unnamed",
	              sessione->scelta->larghezza, sessione->scelta->altezza,
	              sessione->quante_uscite, sessione->nodo);
	return sessione;

guasto:
	kwin_chiudi(sessione);
	return NULL;
}

uint32_t kwin_nodo(const KwinSessione *sessione)
{
	return sessione ? sessione->nodo : 0;
}

void kwin_misura(const KwinSessione *sessione, uint32_t *larghezza, uint32_t *altezza)
{
	*larghezza = (sessione && sessione->scelta) ? sessione->scelta->larghezza : 0;
	*altezza = (sessione && sessione->scelta) ? sessione->scelta->altezza : 0;
}

const char *kwin_nome_uscita(const KwinSessione *sessione)
{
	if (!sessione || !sessione->scelta)
		return NULL;
	return sessione->scelta->nome;
}

unsigned kwin_quante_uscite(const KwinSessione *sessione)
{
	unsigned n = 0;

	if (!sessione)
		return 0;
	for (unsigned i = 0; i < sessione->quante_uscite; i++)
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

static void stacca_eis(KwinSessione *sessione)
{
	/* ⛔ With the token: KWin ties the EIS context to the life of the caller's D-Bus
	 *    NAME, so letting it go only works while the process lives — and
	 *    in a recovery the process stays alive, with one device too many. */
	if (sessione->gettone_noto) {
		GDBusConnection *bus = sessione_bus(NULL);

		if (bus) {
			GVariant *r = g_dbus_connection_call_sync(
			    bus, "org.kde.KWin", "/org/kde/KWin/EIS/RemoteDesktop",
			    "org.kde.KWin.EIS.RemoteDesktop", "disconnect",
			    g_variant_new("(i)", sessione->gettone_eis), NULL,
			    G_DBUS_CALL_FLAGS_NONE, 2000, NULL, NULL);
			if (r)
				g_variant_unref(r);
			g_object_unref(bus);
		}
		sessione->gettone_noto = false;
	}
	if (sessione->eis >= 0) {
		close(sessione->eis);
		sessione->eis = -1;
	}
}

static int chiedi_eis(KwinSessione *sessione, GError **sbaglio)
{
	GDBusConnection *bus;
	GUnixFDList *descrittori = NULL;
	GVariant *risposta;
	gint indice = -1;

	bus = sessione_bus(sbaglio);
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
	g_variant_get(risposta, "(hi)", &indice, &sessione->gettone_eis);
	g_variant_unref(risposta);
	sessione->eis = g_unix_fd_list_get(descrittori, indice, sbaglio);
	g_object_unref(descrittori);
	if (sessione->eis < 0)
		return -1;
	sessione->gettone_noto = true;
	registro_dice(AREA, "⭐ KWin granted the input channel (connectToEIS, token %d, "
	                    "descriptor %d)", sessione->gettone_eis, sessione->eis);
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
	return chiedi_eis(sessione, sbaglio);
}

int kwin_eis_riattacca(KwinSessione *sessione, GError **sbaglio)
{
	if (!sessione) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "no KWin stage");
		return -1;
	}
	stacca_eis(sessione);
	return chiedi_eis(sessione, sbaglio);
}

void kwin_chiudi(KwinSessione *sessione)
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

	stacca_eis(sessione);
	if (sessione->flusso)
		zkde_screencast_stream_unstable_v1_close(sessione->flusso);
	if (sessione->screencast)
		zkde_screencast_unstable_v1_destroy(sessione->screencast);
	for (unsigned i = 0; i < sessione->quante_uscite; i++) {
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
	g_free(sessione->motivo_rifiuto);
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
static bool exec_porta_a(const char *exec, const char *canonico, char **visto)
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
	if (!g_key_file_load_from_file(chiavi, PERMESSO_DESKTOP, G_KEY_FILE_NONE, &sbaglio)) {
		snprintf(perche, quanto,
		         "RX-KDE-001: %s %s (%s). Remedy: reinstall REMOTIX with the installer",
		         PERMESSO_DESKTOP,
		         g_error_matches(sbaglio, G_FILE_ERROR, G_FILE_ERROR_NOENT) ? "is missing"
		                                                                  : "cannot be read",
		         sbaglio->message);
		goto fine;
	}
	exec = g_key_file_get_string(chiavi, "Desktop Entry", "Exec", NULL);
	if (!exec || !exec_porta_a(exec, canonico, &visto)) {
		snprintf(perche, quanto,
		         "RX-KDE-002: in %s Exec=%s, but the running binary is %s. Remedy: "
		         "reinstall REMOTIX with the installer",
		         PERMESSO_DESKTOP, visto ? visto : "(missing)", canonico);
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
		         PERMESSO_DESKTOP, interfacce ? interfacce : "(missing)");
		goto fine;
	}
	snprintf(perche, quanto, "%s checked (it belongs to the package: I do not write it), Exec=%s",
	         PERMESSO_DESKTOP, canonico);
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
static bool nome_xkb_pulito(const char *s, size_t n)
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
		    !nome_xkb_pulito(nome, (size_t) (par - nome)) ||
		    !nome_xkb_pulito(par + 1, (size_t) (chiusa - par - 1))) {
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT,
			            "invalid name «%s»", nome);
			return -1;
		}
		disposizione = g_strndup(nome, (size_t) (par - nome));
		variante = g_strndup(par + 1, (size_t) (chiusa - par - 1));
	} else {
		if (!nome_xkb_pulito(nome, strlen(nome))) {
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

	bus = sessione_bus(sbaglio);
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
