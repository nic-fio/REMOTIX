#include "kwin.h"

#include <errno.h>
#include <fcntl.h>
#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include <glib-unix.h>
#include <glib/gstdio.h>
#include <poll.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <wayland-client.h>

#include "keystate-client-protocol.h"
#include "zkde-screencast-unstable-v1-client-protocol.h"

#include "registro.h"
#include "sessione.h"

/* Quanto si aspetta che KWin risponda `created` o `failed`.  Serve un tetto:
 * `failed` e' spedito in modo SINCRONO dentro il gestore della richiesta
 * (`screencastmanager.cpp:82`), quindi chi lo perde aspetta per sempre — e chi
 * non ha il permesso non riceve nemmeno quello, perche' il global non e'
 * annunciato affatto (`kde.md` §4.4). */
#define ATTESA_NODO_MS 5000

/* Il modo del cursore, dall'enum del protocollo: 1 nascosto, 2 disegnato nel
 * buffer, 4 come metadato.
 *
 * ⛔ SI DECIDE UNA VOLTA SOLA, prima di `init()`, e non e' cambiabile a flusso
 *    vivo (`setCursorMode`, `screencaststream.cpp:915-918`).
 *
 * Si sceglie METADATO perche' RDP ha un canale puntatore proprio: cosi' il
 * cursore non costa una ricodifica e si muove alla latenza della rete invece
 * che a quella del codificatore.  E' la stessa scelta di KRdp
 * (`PortalSession.cpp:285`) e la stessa che facciamo su Mutter.
 *
 * ⛔ IL PREZZO E' IN `cattura.c`: in questo modo OGNI MOVIMENTO DEL PUNTATORE
 *    produce un buffer senza pixel nuovi, marcato `SPA_CHUNK_FLAG_CORRUPTED`,
 *    che contiene i pixel stantii di due-quattro fotogrammi prima.  Un
 *    consumatore che ignora quel flag mostra un fotogramma vecchio a ogni
 *    movimento del mouse (`kde.md` §4.7).
 */
#define PUNTATORE_METADATO 4

/* Quante uscite si tengono da parte.  Con `--virtual` ce n'e' una; il margine
 * serve solo a non troncare in silenzio un elenco piu' lungo. */
#define USCITE_MAX 8

typedef struct
{
	struct wl_output *oggetto;
	uint32_t nome_globale;
	uint32_t versione;
	char *nome;        /* «Virtual-…» su un output virtuale, «DP-1»… su uno vero */
	char *descrizione;
	uint32_t larghezza, altezza; /* del modo CORRENTE, in pixel */
} Uscita;

struct KwinSessione
{
	struct wl_display *display;
	struct wl_registry *registro;
	struct zkde_screencast_unstable_v1 *screencast;
	struct zkde_screencast_stream_unstable_v1 *flusso;
	uint32_t versione_screencast;

	/* Lo stato dei tasti a scatto: un protocollo a parte, perche' libei su KWin
	 * non lo consegna (vedi `kwin.h`). */
	struct org_kde_kwin_keystate *keystate;
	KwinLucchetti su_lucchetti;
	gpointer dati_lucchetti;
	gboolean maiusc, num;

	/* Il gettone che `connectToEIS` restituisce, per chiudere ordinatamente. */
	gint cookie_eis;
	gboolean cookie_noto;

	Uscita uscite[USCITE_MAX];
	guint quante_uscite;
	const Uscita *scelta;

	uint32_t nodo;
	gboolean nodo_arrivato;
	gboolean rifiutato;
	char *motivo_rifiuto;
	volatile gboolean chiuso;

	/* Il ciclo che tiene viva la connessione.  ⛔ NON E' UN LUSSO: il flusso
	 * vive quanto la connessione Wayland del client, e una connessione che
	 * nessuno serve non consegna gli eventi — compreso `closed`, che e' l'unico
	 * modo di sapere che KWin ha smontato la cattura. */
	GThread *pompa;
	int sveglia[2]; /* la pipe con cui si ferma la pompa */
};

/* ------------------------------------------------------------------ *
 * Il registry: chi c'e' su questo compositore
 * ------------------------------------------------------------------ */
static void su_uscita_geometria(void *dati, struct wl_output *uscita, int32_t x, int32_t y,
                                int32_t larghezza_mm, int32_t altezza_mm, int32_t sottopixel,
                                const char *costruttore, const char *modello, int32_t trasformazione)
{
}

static void su_uscita_modo(void *dati, struct wl_output *oggetto, uint32_t flag, int32_t larghezza,
                           int32_t altezza, int32_t aggiornamento)
{
	Uscita *uscita = dati;

	/* Solo il modo CORRENTE: un output ne annuncia quanti ne ha, e quello che
	 * descrive il buffer che ci arrivera' e' uno solo. */
	if (!(flag & WL_OUTPUT_MODE_CURRENT))
		return;
	uscita->larghezza = (uint32_t) MAX(0, larghezza);
	uscita->altezza = (uint32_t) MAX(0, altezza);
}

static void su_uscita_fine(void *dati, struct wl_output *oggetto)
{
}

static void su_uscita_scala(void *dati, struct wl_output *oggetto, int32_t scala)
{
	/*
	 * La scala NON tocca la misura in pixel del buffer: `Output::geometry()` la
	 * usa solo per la geometria logica (`core/output.cpp:457-459`).  Si legge
	 * per il registro, perche' una sessione a scala 2 ha un desktop logico meta'
	 * di quel che catturiamo — e quel disallineamento, se un giorno comparisse,
	 * si spiega solo avendolo scritto.
	 */
	if (scala != 1)
		avviso("l'uscita ha scala %d: il desktop logico e' piu' piccolo del buffer catturato",
		       scala);
}

static void su_uscita_nome(void *dati, struct wl_output *oggetto, const char *nome)
{
	Uscita *uscita = dati;

	g_free(uscita->nome);
	uscita->nome = g_strdup(nome);
}

static void su_uscita_descrizione(void *dati, struct wl_output *oggetto, const char *descrizione)
{
	Uscita *uscita = dati;

	g_free(uscita->descrizione);
	uscita->descrizione = g_strdup(descrizione);
}

static const struct wl_output_listener ascolto_uscita = {
	su_uscita_geometria, su_uscita_modo,        su_uscita_fine,
	su_uscita_scala,     su_uscita_nome,        su_uscita_descrizione,
};

static void su_globale(void *dati, struct wl_registry *registro, uint32_t nome,
                       const char *interfaccia, uint32_t versione)
{
	KwinSessione *sessione = dati;

	if (!strcmp(interfaccia, zkde_screencast_unstable_v1_interface.name))
	{
		/* KWin 6.3.6 annuncia la 5 (`screencast_v1.cpp:18`); il clamp serve
		 * perche' un compositore piu' nuovo ne annuncerebbe una che il nostro XML
		 * non descrive. */
		sessione->versione_screencast = MIN(versione, 5u);
		sessione->screencast =
		    wl_registry_bind(registro, nome, &zkde_screencast_unstable_v1_interface,
		                     sessione->versione_screencast);
	}
	else if (!strcmp(interfaccia, org_kde_kwin_keystate_interface.name))
	{
		/*
		 * Anche questo e' in lista nera (`wayland_server.cpp:129-136`): lo stesso
		 * `.desktop` che apre la cattura lo dichiara, quindi o si legano tutti e
		 * due o nessuno.  Se manca non si fallisce: la sessione perde le sole
		 * spie dei lucchetti, che e' molto meno di perdere l'input.
		 */
		sessione->keystate = wl_registry_bind(registro, nome, &org_kde_kwin_keystate_interface,
		                                     MIN(versione, 5u));
	}
	else if (!strcmp(interfaccia, wl_output_interface.name))
	{
		Uscita *uscita;

		if (sessione->quante_uscite >= USCITE_MAX)
		{
			avviso("piu' di %d uscite: le altre non si guardano", USCITE_MAX);
			return;
		}
		uscita = &sessione->uscite[sessione->quante_uscite++];
		uscita->nome_globale = nome;
		/*
		 * Versione 4, e serve: e' quella che porta l'evento `name`, cioe' l'unico
		 * modo di riconoscere un'uscita fra le altre.  Il banco legava la 1
		 * (`nodo-kwin.c:52`) e con essa il nome non arriva affatto.
		 */
		uscita->versione = MIN(versione, 4u);
		uscita->oggetto =
		    wl_registry_bind(registro, nome, &wl_output_interface, uscita->versione);
		wl_output_add_listener(uscita->oggetto, &ascolto_uscita, uscita);
	}
}

static void su_globale_via(void *dati, struct wl_registry *registro, uint32_t nome)
{
	KwinSessione *sessione = dati;

	/* Un'uscita che sparisce mentre la catturiamo: KWin chiude il flusso da se'
	 * (`outputscreencastsource.cpp:27-32`), quindi qui basta dirlo. */
	for (guint i = 0; i < sessione->quante_uscite; i++)
		if (sessione->uscite[i].nome_globale == nome)
			avviso("l'uscita «%s» e' sparita dal compositore",
			       sessione->uscite[i].nome ?: "senza nome");
}

static const struct wl_registry_listener ascolto_registro = { su_globale, su_globale_via };

/* ------------------------------------------------------------------ *
 * Il flusso
 * ------------------------------------------------------------------ */
static void su_flusso_chiuso(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso)
{
	KwinSessione *sessione = dati;

	/*
	 * KWin ha smontato la cattura.  Succede quando l'uscita viene disabilitata,
	 * quando PipeWire cade, e quando la sessione finisce.
	 *
	 * Qui si segna e basta: chi se ne deve accorgere e' il palco, e se ne accorge
	 * comunque per la sua strada — il nodo PipeWire sparisce e la cattura passa a
	 * `UNCONNECTED`, che e' l'evento su cui la fase 5 ha costruito il congedo.
	 */
	sessione->chiuso = TRUE;
	informazione("KWin ha chiuso il flusso di cattura");
}

static void su_flusso_creato(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso,
                             uint32_t nodo)
{
	KwinSessione *sessione = dati;

	sessione->nodo = nodo;
	sessione->nodo_arrivato = TRUE;
}

static void su_flusso_guasto(void *dati, struct zkde_screencast_stream_unstable_v1 *flusso,
                             const char *errore)
{
	KwinSessione *sessione = dati;

	sessione->rifiutato = TRUE;
	g_free(sessione->motivo_rifiuto);
	sessione->motivo_rifiuto = g_strdup(errore);
}

static const struct zkde_screencast_stream_unstable_v1_listener ascolto_flusso = {
	su_flusso_chiuso, su_flusso_creato, su_flusso_guasto
};

/* ------------------------------------------------------------------ *
 * I tasti a scatto
 * ------------------------------------------------------------------ */
static void su_stato_tasto(void *dati, struct org_kde_kwin_keystate *keystate, uint32_t tasto,
                           uint32_t stato)
{
	KwinSessione *sessione = dati;
	/* `locked` vale 2; `latched` (1) e' il modificatore tenuto per un colpo solo,
	 * che non e' un lucchetto e non va confuso con lui. */
	gboolean acceso = (stato == ORG_KDE_KWIN_KEYSTATE_STATE_LOCKED);

	switch (tasto)
	{
		case ORG_KDE_KWIN_KEYSTATE_KEY_CAPSLOCK:
			sessione->maiusc = acceso;
			break;
		case ORG_KDE_KWIN_KEYSTATE_KEY_NUMLOCK:
			sessione->num = acceso;
			break;
		default:
			return; /* ScrollLock e i modificatori non ci servono */
	}
	traccia("lucchetti secondo KWin: BlocMaiusc %s, BlocNum %s",
	        sessione->maiusc ? "acceso" : "spento", sessione->num ? "acceso" : "spento");
	if (sessione->su_lucchetti)
		sessione->su_lucchetti(sessione->maiusc, sessione->num, sessione->dati_lucchetti);
}

static const struct org_kde_kwin_keystate_listener ascolto_keystate = { su_stato_tasto };

void kwin_lucchetti_ascolta(KwinSessione *sessione, KwinLucchetti su_cambio, gpointer dati)
{
	if (!sessione)
		return;
	sessione->su_lucchetti = su_cambio;
	sessione->dati_lucchetti = dati;

	if (!sessione->keystate)
	{
		avviso("org_kde_kwin_keystate non e' stato concesso: lo stato di BlocMaiusc e BlocNum "
		       "sara' quello che dichiara il client, non quello vero");
		return;
	}
	org_kde_kwin_keystate_add_listener(sessione->keystate, &ascolto_keystate, sessione);
	/* Lo stato di adesso: senza questa richiesta si saprebbe solo al primo
	 * cambiamento, cioe' si partirebbe da un'ipotesi invece che da un fatto. */
	org_kde_kwin_keystate_fetchStates(sessione->keystate);
	wl_display_flush(sessione->display);
	informazione("stato dei tasti a scatto: lo legge KWin, non lo indoviniamo noi");
}

/* ------------------------------------------------------------------ *
 * Il canale di input
 * ------------------------------------------------------------------ */
/* Tastiera 1, puntatore 2, tocco 4 — la maschera del portale xdg
 * (`xdg-desktop-portal-kde/src/remotedesktop.cpp:457-460`). */
#define EIS_CAPACITA 7

int kwin_prendi_fd_eis(KwinSessione *sessione)
{
	g_autoptr(GDBusConnection) bus = NULL;
	g_autoptr(GUnixFDList) descrittori = NULL;
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GError) sbaglio = NULL;
	gint indice = -1;
	gint fd;

	if (!sessione)
		return -1;

	bus = sessione_bus(&sbaglio);
	if (!bus)
	{
		avviso("nessun bus di sessione per chiedere il canale di input: %s", sbaglio->message);
		return -1;
	}

	/*
	 * ⛔ IL DESCRITTORE VIAGGIA IN UNA LISTA A PARTE, non nel corpo del messaggio.
	 *    Il tipo `h` porta solo un INDICE dentro la lista dei descrittori che
	 *    accompagna il messaggio: chi legge il corpo e basta si ritrova in mano
	 *    uno zero e crede che sia un fd — e lo zero e' lo standard input, cioe'
	 *    un descrittore validissimo che punta alla cosa sbagliata.
	 */
	risposta = g_dbus_connection_call_with_unix_fd_list_sync(
	    bus, "org.kde.KWin", "/org/kde/KWin/EIS/RemoteDesktop", "org.kde.KWin.EIS.RemoteDesktop",
	    "connectToEIS", g_variant_new("(i)", EIS_CAPACITA), G_VARIANT_TYPE("(hi)"),
	    G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &descrittori, NULL, &sbaglio);
	if (!risposta)
	{
		avviso("KWin non ha concesso il canale di input (%s): la sessione sara' di sola visione",
		       sbaglio->message);
		return -1;
	}

	g_variant_get(risposta, "(hi)", &indice, &sessione->cookie_eis);
	fd = g_unix_fd_list_get(descrittori, indice, &sbaglio);
	if (fd < 0)
	{
		avviso("il descrittore di connectToEIS non si e' potuto prendere: %s", sbaglio->message);
		return -1;
	}
	sessione->cookie_noto = TRUE;
	informazione("canale di input concesso da KWin (gettone %d)", sessione->cookie_eis);
	return fd;
}

/* ------------------------------------------------------------------ *
 * Il ciclo
 * ------------------------------------------------------------------ */
/*
 * Un giro di eventi, con scadenza.
 *
 * Si spinge quel che c'e' da spedire, si aspetta con `poll`, e solo se c'e'
 * qualcosa da leggere si chiama `wl_display_dispatch` — che altrimenti
 * bloccherebbe senza tetto.
 *
 * Ritorna FALSE se la connessione e' caduta.
 */
static gboolean gira(KwinSessione *sessione, int attesa_ms)
{
	struct pollfd sonda[2];
	int quanti = 1;

	while (wl_display_prepare_read(sessione->display) != 0)
		if (wl_display_dispatch_pending(sessione->display) < 0)
			return FALSE;
	if (wl_display_flush(sessione->display) < 0 && errno != EAGAIN)
	{
		wl_display_cancel_read(sessione->display);
		return FALSE;
	}

	sonda[0].fd = wl_display_get_fd(sessione->display);
	sonda[0].events = POLLIN;
	sonda[0].revents = 0;
	if (sessione->sveglia[0] >= 0)
	{
		sonda[1].fd = sessione->sveglia[0];
		sonda[1].events = POLLIN;
		sonda[1].revents = 0;
		quanti = 2;
	}

	if (poll(sonda, (nfds_t) quanti, attesa_ms) <= 0)
	{
		wl_display_cancel_read(sessione->display);
		return TRUE; /* scaduta o interrotta: non e' un guasto */
	}
	if (quanti == 2 && (sonda[1].revents & POLLIN))
	{
		wl_display_cancel_read(sessione->display);
		return FALSE; /* qualcuno ci ha detto di smettere */
	}
	if (!(sonda[0].revents & POLLIN))
	{
		wl_display_cancel_read(sessione->display);
		return !(sonda[0].revents & (POLLERR | POLLHUP));
	}

	if (wl_display_read_events(sessione->display) < 0)
		return FALSE;
	return wl_display_dispatch_pending(sessione->display) >= 0;
}

static gpointer thread_pompa(gpointer dati)
{
	KwinSessione *sessione = dati;

	while (gira(sessione, -1))
		;
	diagnostica("la connessione Wayland a KWin si e' chiusa");
	return NULL;
}

/* ------------------------------------------------------------------ *
 * Apertura
 * ------------------------------------------------------------------ */
/*
 * Il socket su cui vive il compositore.
 *
 * ⛔ NON SI PUO' RICORDARE: al riavvio della sessione il numero CAMBIA — il
 *    socket e' il primo `wayland-N` libero — ed e' scritto anche in `kde.md`
 *    §6.6 come misura.  Quindi: si prende `WAYLAND_DISPLAY` se c'e', altrimenti
 *    si prova ad aprirli in ordine, perche' un servizio avviato da systemd o da
 *    una shell SSH quella variabile non ce l'ha.
 */
struct wl_display *kwin_display_apri(char **quale)
{
	const char *dichiarato = g_getenv("WAYLAND_DISPLAY");
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (dichiarato && *dichiarato)
	{
		struct wl_display *display = wl_display_connect(dichiarato);

		if (display)
		{
			*quale = g_strdup(dichiarato);
			return display;
		}
		avviso("WAYLAND_DISPLAY dice «%s» ma quel socket non risponde: provo gli altri",
		       dichiarato);
	}

	for (int i = 0; i < 10; i++)
	{
		g_autofree char *nome = g_strdup_printf("wayland-%d", i);
		g_autofree char *percorso =
		    runtime ? g_build_filename(runtime, nome, NULL) : NULL;
		struct wl_display *display;

		if (percorso && !g_file_test(percorso, G_FILE_TEST_EXISTS))
			continue;
		display = wl_display_connect(nome);
		if (display)
		{
			*quale = g_steal_pointer(&nome);
			return display;
		}
	}
	return NULL;
}

/*
 * Quale uscita catturare.
 *
 * Con `--virtual` ce n'e' una sola e la scelta e' vuota.  Il nome si puo'
 * comunque imporre — serve il giorno in cui il compositore ne avra' due, e
 * serve al banco.
 */
static const Uscita *scegli_uscita(KwinSessione *sessione)
{
	const char *voluta = g_getenv("REMOTIX_USCITA");
	const Uscita *prima_valida = NULL;

	for (guint i = 0; i < sessione->quante_uscite; i++)
	{
		const Uscita *uscita = &sessione->uscite[i];

		if (uscita->larghezza == 0 || uscita->altezza == 0)
			continue;
		if (voluta && *voluta && g_strcmp0(uscita->nome, voluta))
			continue;
		if (!prima_valida)
			prima_valida = uscita;
	}
	if (voluta && *voluta && !prima_valida)
		errore("nessuna uscita si chiama «%s»: catturo quel che c'e'", voluta);
	if (!prima_valida)
		for (guint i = 0; i < sessione->quante_uscite; i++)
			if (sessione->uscite[i].larghezza && sessione->uscite[i].altezza)
				return &sessione->uscite[i];
	return prima_valida;
}

static void racconta_le_uscite(const KwinSessione *sessione)
{
	for (guint i = 0; i < sessione->quante_uscite; i++)
		diagnostica("  uscita «%s» (%s): %ux%u", sessione->uscite[i].nome ?: "senza nome",
		            sessione->uscite[i].descrizione ?: "senza descrizione",
		            sessione->uscite[i].larghezza, sessione->uscite[i].altezza);
}

/*
 * Il cancello e' chiuso: si dice PERCHE', perche' il sintomo non lo dice.
 *
 * ⛔ E' la lezione §1.10 di LEZIONI.md messa nel codice.  Il global mancante ha
 *    due cause con cure opposte — «non ho trovato il tuo .desktop» e «l'ho
 *    trovato e il campo e' vuoto» — e KWin le distingue in una parola, ma nel
 *    proprio registro (`QT_LOGGING_RULES='KWIN_UTILS.debug=true'`, categoria
 *    `KWIN_UTILS`, non `kwin_core`).  Da qui non si vede nulla: si puo' pero'
 *    dire dove guardare, invece di lasciare a chi legge la frase inutile
 *    «questo compositore non ha il protocollo».
 */
static void spiega_il_cancello(GError **sbaglio)
{
	g_autofree char *desktop =
	    g_build_filename(g_get_user_data_dir(), "applications", "org.kde.remotix.desktop", NULL);
	gboolean c_e = g_file_test(desktop, G_FILE_TEST_EXISTS);

	g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_PERMISSION_DENIED,
	            "KWin non annuncia zkde_screencast_unstable_v1: il permesso della cattura e' "
	            "negato, non e' il protocollo a mancare. %s "
	            "E l'ambiente di KWin deve avere XDG_MENU_PREFIX=plasma-, o l'indice dei "
	            "servizi si costruisce vuoto e nessun .desktop viene trovato. La causa esatta "
	            "la dice KWin con QT_LOGGING_RULES='KWIN_UTILS.debug=true'",
	            c_e ? "Il nostro .desktop c'e'." : "Il nostro .desktop NON c'e': «remotix "
	                                               "--installa-desktop».");
}

KwinSessione *kwin_apri(GError **sbaglio)
{
	KwinSessione *sessione = g_new0(KwinSessione, 1);
	g_autofree char *socket = NULL;
	gint64 scadenza;

	sessione->sveglia[0] = sessione->sveglia[1] = -1;

	sessione->display = kwin_display_apri(&socket);
	if (!sessione->display)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "nessun compositore Wayland raggiungibile (WAYLAND_DISPLAY non e' impostata "
		            "e in XDG_RUNTIME_DIR non c'e' un socket che risponda)");
		goto guasto;
	}
	diagnostica("connesso al compositore sul socket «%s»", socket);

	sessione->registro = wl_display_get_registry(sessione->display);
	wl_registry_add_listener(sessione->registro, &ascolto_registro, sessione);
	/* Due giri: il primo porta i global, il secondo gli eventi che i global
	 * appena legati hanno spedito — fra cui il modo e il nome delle uscite. */
	wl_display_roundtrip(sessione->display);
	wl_display_roundtrip(sessione->display);

	if (!sessione->screencast)
	{
		spiega_il_cancello(sbaglio);
		goto guasto;
	}
	informazione("zkde_screencast_unstable_v1 versione %u: il permesso della cattura c'e'",
	             sessione->versione_screencast);
	racconta_le_uscite(sessione);

	sessione->scelta = scegli_uscita(sessione);
	if (!sessione->scelta)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NOT_FOUND,
		            "il compositore non ha nessuna uscita con un modo: senza uno schermo "
		            "virtuale KWin inghiotte anche l'input (kde.md §10.3)");
		goto guasto;
	}

	/*
	 * ⛔ IL LISTENER PRIMA DEL DISPATCH, e non e' cerimonia: `failed` viene
	 *    spedito in modo SINCRONO dentro il gestore della richiesta, e chi non
	 *    ha il listener attivo lo perde e aspetta per sempre (`kde.md` §4.4).
	 *    Qui si registra subito dopo la richiesta e prima di qualunque giro.
	 */
	sessione->flusso = zkde_screencast_unstable_v1_stream_output(
	    sessione->screencast, sessione->scelta->oggetto, PUNTATORE_METADATO);
	if (!sessione->flusso)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "richiesta di cattura non creata");
		goto guasto;
	}
	zkde_screencast_stream_unstable_v1_add_listener(sessione->flusso, &ascolto_flusso, sessione);

	scadenza = g_get_monotonic_time() + (gint64) ATTESA_NODO_MS * 1000;
	while (!sessione->nodo_arrivato && !sessione->rifiutato && !sessione->chiuso)
	{
		gint64 resta = (scadenza - g_get_monotonic_time()) / 1000;

		if (resta <= 0)
			break;
		if (!gira(sessione, (int) resta))
			break;
	}

	if (sessione->rifiutato)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "KWin ha rifiutato la cattura: %s",
		            sessione->motivo_rifiuto ?: "senza spiegazione");
		goto guasto;
	}
	if (!sessione->nodo_arrivato)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "KWin non ha annunciato il nodo PipeWire entro %d ms", ATTESA_NODO_MS);
		goto guasto;
	}

	/*
	 * La connessione va servita per tutta la vita del flusso: e' lei a tenerlo
	 * in piedi (`screencast_v1.cpp:28-35`: la distruzione della risorsa chiude
	 * lo stream), e senza qualcuno che faccia dispatch gli eventi restano nella
	 * coda — compreso `closed`.
	 */
	if (!g_unix_open_pipe(sessione->sveglia, O_CLOEXEC, NULL))
	{
		sessione->sveglia[0] = sessione->sveglia[1] = -1;
		avviso("pipe di risveglio non creata: la chiusura della cattura sara' meno pulita");
	}
	sessione->pompa = g_thread_new("remotix-kwin", thread_pompa, sessione);

	informazione("cattura KDE avviata sull'uscita «%s» (%ux%u), nodo PipeWire %u",
	             sessione->scelta->nome ?: "senza nome", sessione->scelta->larghezza,
	             sessione->scelta->altezza, sessione->nodo);
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

gboolean kwin_chiuso(const KwinSessione *sessione)
{
	return sessione ? sessione->chiuso : TRUE;
}

void kwin_chiudi(KwinSessione *sessione)
{
	if (!sessione)
		return;

	/* Prima si ferma la pompa, poi si tocca il display: sono lo stesso oggetto
	 * visto da due thread, e distruggerlo sotto chi lo sta leggendo e' un
	 * segfault lontano dalla causa. */
	if (sessione->pompa)
	{
		if (sessione->sveglia[1] >= 0)
		{
			ssize_t ignoto = write(sessione->sveglia[1], "x", 1);

			(void) ignoto;
		}
		g_thread_join(sessione->pompa);
		sessione->pompa = NULL;
	}
	if (sessione->sveglia[0] >= 0)
		close(sessione->sveglia[0]);
	if (sessione->sveglia[1] >= 0)
		close(sessione->sveglia[1]);

	/*
	 * Il canale di input si chiude col gettone, e non e' cerimonia: KWin lega il
	 * contesto EIS alla vita del NOME D-Bus del chiamante, quindi lasciarlo
	 * aperto funziona — ma solo finche' il processo vive.  Dirlo esplicitamente
	 * fa sparire i dispositivi virtuali subito, invece che al prossimo giro.
	 */
	if (sessione->cookie_noto)
	{
		g_autoptr(GDBusConnection) bus = sessione_bus(NULL);

		if (bus)
			g_dbus_connection_call(bus, "org.kde.KWin", "/org/kde/KWin/EIS/RemoteDesktop",
			                       "org.kde.KWin.EIS.RemoteDesktop", "disconnect",
			                       g_variant_new("(i)", sessione->cookie_eis), NULL,
			                       G_DBUS_CALL_FLAGS_NONE, 2000, NULL, NULL, NULL);
		sessione->cookie_noto = FALSE;
	}
	if (sessione->keystate)
		org_kde_kwin_keystate_destroy(sessione->keystate);
	if (sessione->flusso)
		zkde_screencast_stream_unstable_v1_close(sessione->flusso);
	if (sessione->screencast)
		zkde_screencast_unstable_v1_destroy(sessione->screencast);
	for (guint i = 0; i < sessione->quante_uscite; i++)
	{
		if (sessione->uscite[i].oggetto)
		{
			/* `release` esiste dalla versione 3: chiamarlo su una piu' vecchia
			 * sarebbe una richiesta che il server non conosce, cioe' un errore di
			 * protocollo che chiude la connessione. */
			if (sessione->uscite[i].versione >= 3)
				wl_output_release(sessione->uscite[i].oggetto);
			else
				wl_output_destroy(sessione->uscite[i].oggetto);
		}
		g_free(sessione->uscite[i].nome);
		g_free(sessione->uscite[i].descrizione);
	}
	if (sessione->registro)
		wl_registry_destroy(sessione->registro);
	if (sessione->display)
	{
		wl_display_flush(sessione->display);
		wl_display_disconnect(sessione->display);
	}

	g_free(sessione->motivo_rifiuto);
	g_free(sessione);
}

/* ------------------------------------------------------------------ *
 * Il file che apre il cancello
 * ------------------------------------------------------------------ */
gboolean kwin_installa_desktop(GError **sbaglio)
{
	g_autofree char *binario = g_file_read_link("/proc/self/exe", sbaglio);
	g_autofree char *canonico = NULL;
	g_autofree char *cartella =
	    g_build_filename(g_get_user_data_dir(), "applications", NULL);
	g_autofree char *percorso =
	    g_build_filename(cartella, "org.kde.remotix.desktop", NULL);
	g_autofree char *contenuto = NULL;
	char *risolto;

	if (!binario)
		return FALSE;
	/* Il confronto che KWin fa e' sul percorso CANONICO
	 * (`executable_path_proc.cpp:11-14`): un symlink scritto qui dentro non
	 * corrisponderebbe a niente. */
	risolto = realpath(binario, NULL);
	canonico = risolto ? g_strdup(risolto) : g_strdup(binario);
	free(risolto);

	if (geteuid() == 0)
		avviso("questo processo e' root: KWin non riesce a leggere /proc/<pid>/exe di un "
		       "processo di altro uid e NEGA il permesso.  REMOTIX va eseguito come l'utente "
		       "di cui serve la sessione (§3.4 di SPECIFICA.md)");

	/*
	 * Il modello e' `org.kde.krfb.virtualmonitor.desktop` — `NoDisplay=true`,
	 * `Exec=` sul binario vero — ed e' anche la forma di `org.kde.krdpserver.desktop`,
	 * cioe' del server RDP di KDE (`kde.md` §12.0): la via del permesso non e'
	 * una nostra deduzione.
	 *
	 * Le due interfacce sono dichiarate insieme: la cattura, e lo stato dei tasti
	 * a scatto — che su KDE costa solo un nome in piu' qui, perche' la
	 * connessione Wayland c'e' comunque (decisione dell'utente, 8 agosto 2026).
	 */
	contenuto = g_strdup_printf("[Desktop Entry]\n"
	                            "Type=Application\n"
	                            "Name=REMOTIX\n"
	                            "Comment=Server RDP\n"
	                            "Exec=%s\n"
	                            "NoDisplay=true\n"
	                            "X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1,"
	                            "org_kde_kwin_keystate\n",
	                            canonico);

	g_mkdir_with_parents(cartella, 0755);
	if (!g_file_set_contents(percorso, contenuto, -1, sbaglio))
		return FALSE;

	informazione("scritto %s con Exec=%s", percorso, canonico);
	/*
	 * ⛔ E L'INDICE VA RICOSTRUITO CON IL PREFISSO GIUSTO.  `kbuildsycoca6`
	 *    lanciato senza `XDG_MENU_PREFIX` costruisce un indice VUOTO e
	 *    sovrascrive quello buono — il nome del file di cache non dipende dal
	 *    prefisso — chiudendo il cancello a KWin gia' avviato, senza un
	 *    messaggio.  [M, 7 agosto 2026, `kde.md` §3.3-bis]
	 */
	if (!g_getenv("XDG_MENU_PREFIX"))
		avviso("XDG_MENU_PREFIX non e' impostata: NON lanciare kbuildsycoca6 da qui, "
		       "sovrascriverebbe l'indice buono con uno vuoto.  KWin ricostruisce da se' "
		       "entro un secondo e mezzo, dentro il proprio processo");
	return TRUE;
}
