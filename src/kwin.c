/*
 * kwin — vedi `kwin.h`.  Riportato da `fondamenta/remotix-c/src/kwin.c` di v1:
 * i commenti che citano `kde.md` rimandano allo studio del codice di KWin, oggi
 * in `STUDI.md` (da riga ~1233, numerazione dei § invariata).
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

/* Quanto si aspetta che KWin risponda `created` o `failed`.  Serve un tetto:
 * `failed` e' spedito in modo SINCRONO dentro il gestore della richiesta
 * (`screencastmanager.cpp:82`), quindi chi lo perde aspetta per sempre. */
#define ATTESA_NODO_MS 5000

/* Il modo del cursore, dall'enum del protocollo: 1 nascosto, 2 disegnato nel
 * buffer, 4 come metadato.
 *
 * ⛔ SI DECIDE UNA VOLTA SOLA e non e' cambiabile a flusso vivo
 *    (`screencaststream.cpp:915-918`).  METADATO come su Mutter (`cursor-mode=2`
 *    di `mutter.c`): il cursore lo disegna la pagina.
 * ⛔ IL PREZZO E' IN `cattura.c`: ogni movimento del puntatore produce un
 *    buffer senza pixel nuovi marcato `SPA_CHUNK_FLAG_CORRUPTED` (`kde.md`
 *    §4.7), e `cattura.c` li scarta gia'. */
#define PUNTATORE_METADATO 4

#define USCITE_MAX 8

/* Il percorso del permesso: di sistema, perche' lo scrive il server per tutti
 * gli utenti, e KWin cerca in `XDG_DATA_DIRS` (che contiene `/usr/share`). */
#define PERMESSO_DESKTOP "/usr/share/applications/org.kde.remotix.desktop"

typedef struct
{
	struct wl_output *oggetto;
	uint32_t nome_globale;
	uint32_t versione;
	char *nome; /* «Virtual-0» con `--virtual` */
	uint32_t larghezza, altezza; /* del modo CORRENTE, in pixel */
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

	/* ⛔ IL CICLO CHE TIENE VIVA LA CONNESSIONE NON E' UN LUSSO: il flusso vive
	 *    quanto la connessione Wayland (`screencast_v1.cpp:28-35`), e una
	 *    connessione che nessuno serve non consegna `closed`. */
	GThread *pompa;
	int sveglia[2];

	/* Il canale di input: il descrittore e il gettone di `connectToEIS`. */
	int eis;
	gint gettone_eis;
	bool gettone_noto;
};

/* ------------------------------------------------------------------ *
 * Il registry
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
	/* La scala non tocca i pixel del buffer (`core/output.cpp:457-459`), ma
	 * sposta lo spazio delle coordinate dell'input: si scrive. */
	if (scala != 1)
		registro_dice(AREA, "⚠ l'uscita di KWin ha scala %d: il desktop logico e' piu' "
		                    "piccolo del buffer catturato", scala);
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
		/* KWin 6.3.6 annuncia la 5; il clamp perche' un KWin piu' nuovo ne
		 * annuncerebbe una che il nostro XML non descrive. */
		sessione->versione_screencast = MIN(versione, 5u);
		sessione->screencast =
		    wl_registry_bind(registro, nome, &zkde_screencast_unstable_v1_interface,
		                     sessione->versione_screencast);
	} else if (!strcmp(interfaccia, wl_output_interface.name)) {
		Uscita *uscita;

		if (sessione->quante_uscite >= USCITE_MAX) {
			registro_dice(AREA, "⚠ piu' di %d uscite: le altre non si guardano",
			              USCITE_MAX);
			return;
		}
		uscita = &sessione->uscite[sessione->quante_uscite++];
		uscita->nome_globale = nome;
		/* Versione 4: e' quella che porta l'evento `name`. */
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
			registro_dice(AREA, "⚠ l'uscita «%s» e' sparita dal compositore",
			              sessione->uscite[i].nome ? sessione->uscite[i].nome
			                                       : "senza nome");
}

static const struct wl_registry_listener ascolto_registro = { su_globale, su_globale_via };

/* ------------------------------------------------------------------ *
 * Il flusso
 * ------------------------------------------------------------------ */
static void su_flusso_chiuso(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso)
{
	KwinSessione *sessione = dati;

	/* Si segna e basta: il palco se ne accorge per la sua strada, perche' il
	 * nodo PipeWire sparisce e la cattura passa a `UNCONNECTED`. */
	sessione->chiuso = true;
	registro_dice(AREA, "KWin ha chiuso il flusso di cattura");
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
 * Il ciclo
 * ------------------------------------------------------------------ */
/* Un giro di eventi con scadenza: `wl_display_dispatch` da solo bloccherebbe
 * senza tetto.  false se la connessione e' caduta o se ci hanno fermati. */
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
	registro_dettaglio(AREA, "la connessione Wayland a KWin si e' chiusa");
	return NULL;
}

/* ------------------------------------------------------------------ *
 * Apertura
 * ------------------------------------------------------------------ */
/* ⛔ Il socket non si puo' ricordare: e' il primo `wayland-N` libero, e il
 *    figlio nasce con l'ambiente composto da zero (`WAYLAND_DISPLAY` non c'e').
 *    ⇒ Si prova in ordine dentro `XDG_RUNTIME_DIR`. */
static struct wl_display *apri_il_display(char *quale, size_t quanto)
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

/* Con `--virtual` c'e' una sola uscita; si prende la prima che ha un modo. */
static const Uscita *scegli_uscita(const KwinSessione *sessione)
{
	for (unsigned i = 0; i < sessione->quante_uscite; i++)
		if (sessione->uscite[i].larghezza && sessione->uscite[i].altezza)
			return &sessione->uscite[i];
	return NULL;
}

/* Il cancello e' chiuso: si dice PERCHE', perche' il sintomo non lo dice.  Il
 * global mancante ha due cause con cure opposte, e KWin le distingue solo nel
 * proprio registro (`QT_LOGGING_RULES='KWIN_UTILS.debug=true'`). */
static void spiega_il_cancello(GError **sbaglio)
{
	g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_PERMISSION_DENIED,
	            "KWin non annuncia zkde_screencast_unstable_v1: il permesso della cattura "
	            "e' negato, non e' il protocollo a mancare. Il nostro .desktop %s (%s). E "
	            "l'ambiente di KWin deve avere XDG_MENU_PREFIX=plasma-, o l'indice dei "
	            "servizi si costruisce vuoto. La causa esatta la dice KWin con "
	            "QT_LOGGING_RULES='KWIN_UTILS.debug=true'",
	            access(PERMESSO_DESKTOP, F_OK) == 0 ? "c'e'" : "NON c'e'", PERMESSO_DESKTOP);
}

KwinSessione *kwin_apri(GError **sbaglio)
{
	KwinSessione *sessione = g_new0(KwinSessione, 1);
	char socket[64] = "";
	gint64 scadenza;

	sessione->sveglia[0] = sessione->sveglia[1] = -1;
	sessione->eis = -1;

	sessione->display = apri_il_display(socket, sizeof socket);
	if (!sessione->display) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "nessun compositore Wayland raggiungibile in XDG_RUNTIME_DIR=%s",
		            getenv("XDG_RUNTIME_DIR") ? getenv("XDG_RUNTIME_DIR") : "(non impostata)");
		goto guasto;
	}

	sessione->registro = wl_display_get_registry(sessione->display);
	wl_registry_add_listener(sessione->registro, &ascolto_registro, sessione);
	/* Due giri: i global, poi gli eventi dei global appena legati (modo, nome). */
	wl_display_roundtrip(sessione->display);
	wl_display_roundtrip(sessione->display);

	if (!sessione->screencast) {
		spiega_il_cancello(sbaglio);
		goto guasto;
	}

	sessione->scelta = scegli_uscita(sessione);
	if (!sessione->scelta) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "KWin non ha nessuna uscita con un modo (%u annunciate): senza uno "
		            "schermo virtuale KWin inghiotte anche l'input (kde.md §10.3)",
		            sessione->quante_uscite);
		goto guasto;
	}

	/* ⛔ IL LISTENER SUBITO DOPO LA RICHIESTA E PRIMA DI QUALUNQUE GIRO: `failed`
	 *    parte in modo sincrono, e chi non ascolta lo perde (`kde.md` §4.4). */
	sessione->flusso = zkde_screencast_unstable_v1_stream_output(
	    sessione->screencast, sessione->scelta->oggetto, PUNTATORE_METADATO);
	if (!sessione->flusso) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "richiesta di cattura a KWin non creata");
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
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "KWin ha rifiutato la cattura: %s",
		            sessione->motivo_rifiuto ? sessione->motivo_rifiuto : "senza spiegazione");
		goto guasto;
	}
	if (!sessione->nodo_arrivato) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "KWin non ha annunciato il nodo PipeWire entro %d ms", ATTESA_NODO_MS);
		goto guasto;
	}

	if (!g_unix_open_pipe(sessione->sveglia, O_CLOEXEC, NULL)) {
		sessione->sveglia[0] = sessione->sveglia[1] = -1;
		registro_dice(AREA, "⚠ pipe di risveglio non creata: la chiusura della cattura "
		                    "sara' meno pulita");
	}
	sessione->pompa = g_thread_new("remotix-kwin", thread_pompa, sessione);

	registro_dice(AREA,
	              "⭐ KWin: zkde_screencast v%u sul socket «%s», uscita «%s» %ux%u (%u in "
	              "tutto), nodo PipeWire %u",
	              sessione->versione_screencast, socket,
	              sessione->scelta->nome ? sessione->scelta->nome : "senza nome",
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
 * Il canale di input
 * ------------------------------------------------------------------ */
/* Tastiera 1, puntatore 2, tocco 4 — la maschera del portale xdg
 * (`xdg-desktop-portal-kde/src/remotedesktop.cpp:457-460`). */
#define EIS_CAPACITA 7

static void stacca_eis(KwinSessione *sessione)
{
	/* ⛔ Col gettone: KWin lega il contesto EIS alla vita del NOME D-Bus del
	 *    chiamante, quindi lasciarlo funziona solo finche' il processo vive — e
	 *    in una guarigione il processo resta vivo, con un dispositivo in piu'. */
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
	/* ⛔ IL DESCRITTORE VIAGGIA IN UNA LISTA A PARTE: `h` e' un INDICE in
	 *    quella lista, e lo zero letto dal corpo sarebbe lo standard input. */
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
	registro_dice(AREA, "⭐ KWin ha concesso il canale di input (connectToEIS, gettone %d, "
	                    "descrittore %d)", sessione->gettone_eis, sessione->eis);
	return sessione->eis;
}

int kwin_eis_fd(KwinSessione *sessione, GError **sbaglio)
{
	if (!sessione) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "nessun palco KWin");
		return -1;
	}
	if (sessione->eis >= 0)
		return sessione->eis;
	return chiedi_eis(sessione, sbaglio);
}

int kwin_eis_riattacca(KwinSessione *sessione, GError **sbaglio)
{
	if (!sessione) {
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_INVALID_ARGUMENT, "nessun palco KWin");
		return -1;
	}
	stacca_eis(sessione);
	return chiedi_eis(sessione, sbaglio);
}

void kwin_chiudi(KwinSessione *sessione)
{
	if (!sessione)
		return;

	/* Prima si ferma la pompa, poi si tocca il display: sono lo stesso oggetto
	 * visto da due thread. */
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
			/* `release` esiste dalla versione 3. */
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
 * Il file che apre il cancello
 * ------------------------------------------------------------------ */
bool kwin_scrivi_permesso(char *perche, size_t quanto)
{
	char *canonico = realpath("/proc/self/exe", NULL);
	char *contenuto, *vecchio = NULL;
	GError *sbaglio = NULL;
	bool fatto;

	if (!canonico) {
		snprintf(perche, quanto, "non so quale binario sto eseguendo: %s", strerror(errno));
		return false;
	}
	/* Il modello e' `org.kde.krdpserver.desktop`, il server RDP di KDE: `NoDisplay`,
	 * `Exec=` sul binario CANONICO (`executable_path_proc.cpp:11-14`).  Solo la
	 * cattura: lo stato dei lucchetti e' dell'incremento 3. */
	contenuto = g_strdup_printf("[Desktop Entry]\n"
	                            "Type=Application\n"
	                            "Name=REMOTIX\n"
	                            "Comment=Il desktop nel browser\n"
	                            "Exec=%s\n"
	                            "NoDisplay=true\n"
	                            "X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1\n",
	                            canonico);
	/* Se c'e' gia' ed e' uguale non si riscrive: una data che cambia fa
	 * ricostruire l'indice dei servizi a ogni sessione viva. */
	if (g_file_get_contents(PERMESSO_DESKTOP, &vecchio, NULL, NULL)
	    && strcmp(vecchio, contenuto) == 0) {
		snprintf(perche, quanto, "%s c'e' gia', Exec=%s", PERMESSO_DESKTOP, canonico);
		fatto = true;
	} else {
		fatto = g_file_set_contents(PERMESSO_DESKTOP, contenuto, -1, &sbaglio);
		if (fatto) {
			chmod(PERMESSO_DESKTOP, 0644);
			snprintf(perche, quanto, "scritto %s, Exec=%s", PERMESSO_DESKTOP, canonico);
		} else {
			snprintf(perche, quanto, "%s non si scrive: %s", PERMESSO_DESKTOP,
			         sbaglio->message);
			g_clear_error(&sbaglio);
		}
	}
	g_free(vecchio);
	g_free(contenuto);
	free(canonico);
	return fatto;
}
