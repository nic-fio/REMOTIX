#include "uscita.h"

#include <gio/gio.h>

#include "registro.h"
#include "sessione.h"

#define NOME_GESTORE "org.gnome.SessionManager"
#define PERCORSO_GESTORE "/org/gnome/SessionManager"
#define IFACE_GESTORE "org.gnome.SessionManager"
#define IFACE_CLIENTE "org.gnome.SessionManager.ClientPrivate"

/* Il nome con cui ci presentiamo a gnome-session. */
#define NOME_CLIENTE "remotix"

/* Ogni quanto si riprova a registrarsi, e ogni quanto si controlla che la
 * sessione a cui siamo registrati esista ancora. */
#define CADENZA_MS 500
#define GIRI_PER_CONTROLLO 10 /* cioe' ogni 5 secondi */

struct Uscita
{
	GThread *thread;
	GMainContext *contesto;
	GMainLoop *ciclo;

	UscitaAnnuncio su_uscita;
	gpointer dati;

	GDBusConnection *bus;
	char *cliente; /* percorso dell'oggetto che ci rappresenta */
	guint sottoscrizioni[3];
	guint giri;
	/* Il guasto della registrazione si dice una volta: il battito riprova due
	 * volte al secondo, e su un compositore che non e' GNOME non riuscira' mai. */
	gboolean detto_il_guasto;

	TipoCompositore tipo;
	/* Su KDE non ci si registra: si GUARDA.  Vedi `sorveglia_kde`. */
	guint spia_kde;
	gboolean uscita_annunciata;
};

/*
 * Riscontra all'istante, e non aspetta la risposta.
 *
 * ⛔ Asincrona di proposito: questo e' il percorso su cui pende l'uscita
 *    dell'utente, e una chiamata che attende puo' trattenerlo.  Se il riscontro
 *    non parte non c'e' niente di utile da fare se non dirlo FORTE nel
 *    registro: e' il difetto che lascerebbe l'utente senza la possibilita' di
 *    sloggarsi, e chi legge deve poterlo riconoscere subito.
 */
static void su_riscontro(GObject *sorgente, GAsyncResult *esito, gpointer dati)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta =
	    g_dbus_connection_call_finish(G_DBUS_CONNECTION(sorgente), esito, &sbaglio);

	if (!risposta)
		avviso("riscontro a gnome-session fallito (%s): l'uscita dell'utente potrebbe "
		       "restare BLOCCATA",
		       sbaglio->message);
	else
		traccia("riscontrato a gnome-session: per noi si puo' uscire");
}

static void riscontra(Uscita *uscita)
{
	if (!uscita->cliente)
		return;
	g_dbus_connection_call(uscita->bus, NOME_GESTORE, uscita->cliente, IFACE_CLIENTE,
	                       "EndSessionResponse", g_variant_new("(bs)", TRUE, ""), NULL,
	                       G_DBUS_CALL_FLAGS_NONE, 2000, NULL, su_riscontro, NULL);
}

/*
 * Ci si toglie dall'elenco dei client di gnome-session.
 *
 * ⛔ Registrarsi ha un prezzo che va pagato per intero: da quel momento il
 *    gestore di sessione ci considera **suoi**, e alla fine della sessione fa
 *    con noi quel che fa con le applicazioni — ci dice `Stop` e si aspetta che
 *    ce ne andiamo.  Ma REMOTIX non deve andarsene: deve restare in ascolto e
 *    riavviare la sessione alla connessione successiva (§5.9-bis di
 *    SPECIFICA.md), altrimenti dopo un «Esci» l'utente si ritrova un server
 *    morto e nessun desktop.
 *
 *    Quindi appena si sa che la sessione sta finendo ci si sfila.
 */
static void disiscrivi(Uscita *uscita)
{
	if (!uscita->bus || !uscita->cliente)
		return;
	g_dbus_connection_call(uscita->bus, NOME_GESTORE, PERCORSO_GESTORE, IFACE_GESTORE,
	                       "UnregisterClient", g_variant_new("(o)", uscita->cliente), NULL,
	                       G_DBUS_CALL_FLAGS_NONE, 2000, NULL, NULL, NULL);
	diagnostica("disiscritti da gnome-session: la nostra vita torna nostra");
}

static void sgancia(Uscita *uscita)
{
	disiscrivi(uscita);
	for (gsize i = 0; i < G_N_ELEMENTS(uscita->sottoscrizioni); i++)
	{
		if (uscita->sottoscrizioni[i])
			g_dbus_connection_signal_unsubscribe(uscita->bus, uscita->sottoscrizioni[i]);
		uscita->sottoscrizioni[i] = 0;
	}
	g_clear_pointer(&uscita->cliente, g_free);
}

static void su_segnale(GDBusConnection *bus, const char *mittente, const char *percorso,
                       const char *interfaccia, const char *segnale, GVariant *parametri,
                       gpointer dati)
{
	Uscita *uscita = dati;

	if (g_strcmp0(segnale, "QueryEndSession") == 0)
	{
		/* La DOMANDA.  Si risponde di no-non-mi-oppongo e non si fa altro: chi
		 * si aggancia qui butta fuori l'utente per un logout che
		 * un'applicazione puo' ancora annullare. */
		diagnostica("gnome-session chiede se si puo' uscire");
		riscontra(uscita);
		return;
	}

	if (g_strcmp0(segnale, "EndSession") == 0)
	{
		/* La DECISIONE.  Prima si risponde — la regola dell'ostaggio — e POI si
		 * avvisa chi sta servendo la connessione. */
		riscontra(uscita);
		informazione("la sessione grafica sta uscendo: lo si sa subito, non fra cinque secondi");
		if (uscita->su_uscita)
			uscita->su_uscita(uscita->dati);
		/* E ci si sfila SUBITO: da qui in poi gnome-session non deve piu'
		 * considerarci uno dei suoi.  Il `battito` ci riregistrera' quando
		 * nascera' la sessione successiva. */
		sgancia(uscita);
		return;
	}

	if (g_strcmp0(segnale, "Stop") == 0)
	{
		diagnostica("gnome-session ci dice di fermarci");
		sgancia(uscita);
	}
}

static void sottoscrivi(Uscita *uscita)
{
	static const char *segnali[] = { "QueryEndSession", "EndSession", "Stop" };

	for (gsize i = 0; i < G_N_ELEMENTS(segnali); i++)
		uscita->sottoscrizioni[i] = g_dbus_connection_signal_subscribe(
		    uscita->bus, NOME_GESTORE, IFACE_CLIENTE, segnali[i], uscita->cliente, NULL,
		    G_DBUS_SIGNAL_FLAGS_NONE, su_segnale, uscita, NULL);
}

static gboolean registra(Uscita *uscita)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta = NULL;

	/* Dopo un logout il bus dell'utente e' un altro: quello che tenevamo qui e'
	 * chiuso, e riregistrarsi su una connessione chiusa non fallisce con un
	 * errore — non fa proprio niente. */
	if (uscita->bus && g_dbus_connection_is_closed(uscita->bus))
		g_clear_object(&uscita->bus);

	if (!uscita->bus)
	{
		uscita->bus = sessione_bus(&sbaglio);   /* mai g_bus_get_sync: vedi sessione.h */
		if (!uscita->bus)
			return FALSE;
	}

	/* Il secondo argomento e' l'identificatore di avvio, che serve a riagganciare
	 * un'applicazione ripristinata da una sessione salvata.  Non e' il nostro
	 * caso: si manda vuoto, come qualunque programma avviato a mano. */
	risposta = g_dbus_connection_call_sync(
	    uscita->bus, NOME_GESTORE, PERCORSO_GESTORE, IFACE_GESTORE, "RegisterClient",
	    g_variant_new("(ss)", NOME_CLIENTE, ""), G_VARIANT_TYPE("(o)"), G_DBUS_CALL_FLAGS_NONE,
	    5000, NULL, &sbaglio);
	if (!risposta)
	{
		/*
		 * ⛔ SI DICE UNA VOLTA SOLA, e non e' pignoleria di stile.
		 *
		 *    Il battito riprova ogni mezzo secondo finche' una sessione c'e': su
		 *    un compositore che non e' GNOME `org.gnome.SessionManager` non
		 *    esistera' mai, e questa riga usciva DUE VOLTE AL SECONDO per tutta la
		 *    durata del servizio.  Un registro cosi' non e' rumoroso: e' inservibile
		 *    — la riga che spiega il guasto vero ci finisce sepolta dentro, ed e'
		 *    esattamente quel che e' successo alla prima prova su KDE, dove il
		 *    motivo per cui il server moriva stava fra due schermate di questa.
		 *
		 * ⏸ Su KDE la sentinella dell'uscita e' un'altra: due sottoscrizioni
		 *    passive a `org.kde.Shutdown` e `org.kde.KWinWrapper` (`kde.md` §6.5),
		 *    che non mettono in gioco la sessione dell'utente.  E' la VOCE 3 del
		 *    piano di fase 11.
		 */
		if (!uscita->detto_il_guasto)
		{
			uscita->detto_il_guasto = TRUE;
			avviso("registrazione con gnome-session fallita (%s): dell'uscita ci si accorgera' "
			       "tardi, alla morte della cattura — e non lo ripeto piu'",
			       sbaglio->message);
		}
		return FALSE;
	}

	g_variant_get(risposta, "(o)", &uscita->cliente);
	sottoscrivi(uscita);
	informazione("registrati con gnome-session (%s): l'uscita si sapra' subito", uscita->cliente);
	return TRUE;
}

/*
 * Il battito che tiene viva la registrazione.
 *
 * `RegisterClient` vale per la sessione in cui lo si chiama: dopo un «Esci» ne
 * nasce una nuova, con un gestore nuovo che di noi non sa niente.  Quindi ci si
 * riregistra, e lo si fa solo quando una sessione c'e' davvero.
 */
/*
 * La sentinella dell'uscita su KDE, e perche' e' PASSIVA.
 *
 * ⛔ SU KDE NON ESISTE UN `RegisterClient`, e la cosa che gli somiglia e'
 *    peggio del problema.  L'equivalente vero e' XSMP su ICE — serve `libSM`,
 *    `libICE` e un `DISPLAY` — e `org.kde.KSMServerInterface` non ha alcun
 *    segnale «la sessione sta finendo» [✗].  Chi si registrasse presso ksmserver
 *    erediterebbe la regola dell'ostaggio nella sua forma peggiore: un client
 *    che non risponde FRENA IL LOGOUT DELL'UTENTE DI QUINDICI SECONDI
 *    (`ksmserver/logout.cpp:293-303`).
 *
 *    Si guarda invece un nome sul bus: `org.kde.Shutdown` e' **attivabile**, cioe'
 *    non esiste finche' il logout non comincia — e compare esattamente allora
 *    (`plasma-shutdown/shutdown.cpp:20-23`).  E' la stessa cosa che fa
 *    `startplasma` per sapere di dover uscire (`startplasma.cpp:673-689`).
 *    Costa una sottoscrizione e non mette in gioco la sessione dell'utente.
 *
 * ⚠ Con una differenza rispetto a GNOME che va detta, perche' cambia i tempi:
 *   li' `EndSession` e' una DECISIONE che si riscontra, e riscontrarla per primi
 *   accorcia l'uscita.  Qui non c'e' niente da riscontrare: si sa che sta
 *   succedendo, e basta.  Il client cade lo stesso subito, perche' quel che
 *   conta e' saperlo presto — ed e' quel che questa spia da'.
 */
static void su_nome_cambiato(GDBusConnection *bus, const char *mittente, const char *percorso,
                             const char *interfaccia, const char *segnale, GVariant *parametri,
                             gpointer dati)
{
	Uscita *uscita = dati;
	const char *nome = NULL, *prima = NULL, *dopo = NULL;

	g_variant_get(parametri, "(&s&s&s)", &nome, &prima, &dopo);
	/* Compare un proprietario: il logout e' cominciato ADESSO. */
	if (!dopo || !*dopo || uscita->uscita_annunciata)
		return;

	uscita->uscita_annunciata = TRUE;
	informazione("la sessione di KDE sta uscendo: lo si sa subito, non alla morte della cattura");
	if (uscita->su_uscita)
		uscita->su_uscita(uscita->dati);
}

static void sorveglia_kde(Uscita *uscita)
{
	g_autoptr(GError) sbaglio = NULL;

	if (uscita->spia_kde)
		return;
	if (!uscita->bus)
	{
		uscita->bus = sessione_bus(&sbaglio);
		if (!uscita->bus)
		{
			if (!uscita->detto_il_guasto)
			{
				uscita->detto_il_guasto = TRUE;
				avviso("nessun bus di sessione (%s): dell'uscita ci si accorgera' tardi",
				       sbaglio->message);
			}
			return;
		}
	}

	uscita->spia_kde = g_dbus_connection_signal_subscribe(
	    uscita->bus, "org.freedesktop.DBus", "org.freedesktop.DBus", "NameOwnerChanged",
	    "/org/freedesktop/DBus", "org.kde.Shutdown", G_DBUS_SIGNAL_FLAGS_NONE, su_nome_cambiato,
	    uscita, NULL);
	informazione("sentinella dell'uscita: sorveglio org.kde.Shutdown");
}

static gboolean battito(gpointer dati)
{
	Uscita *uscita = dati;

	if (uscita->tipo == COMPOSITORE_KWIN)
	{
		sorveglia_kde(uscita);
		/*
		 * L'annuncio si riarma quando la sessione se n'e' andata davvero: dopo un
		 * «Esci» ne nascera' un'altra, e di quella si dovra' sapere l'uscita
		 * altrettanto presto.
		 */
		if (uscita->uscita_annunciata && !sessione_viva())
			uscita->uscita_annunciata = FALSE;
		return G_SOURCE_CONTINUE;
	}

	if (!uscita->cliente)
	{
		if (sessione_viva())
			registra(uscita);
		return G_SOURCE_CONTINUE;
	}

	/* Registrati: i segnali fanno il lavoro.  Si controlla comunque ogni tanto
	 * che la sessione ci sia ancora, perche' una sessione che muore male non
	 * manda alcuno `Stop` e resteremmo agganciati a un gestore che non c'e'. */
	if (++uscita->giri >= GIRI_PER_CONTROLLO)
	{
		uscita->giri = 0;
		if (!sessione_viva())
		{
			diagnostica("la sessione a cui eravamo registrati non c'e' piu'");
			sgancia(uscita);
		}
	}
	return G_SOURCE_CONTINUE;
}

static gpointer thread_uscita(gpointer dati)
{
	Uscita *uscita = dati;
	GSource *tic;

	g_main_context_push_thread_default(uscita->contesto);

	tic = g_timeout_source_new(CADENZA_MS);
	g_source_set_callback(tic, battito, uscita, NULL);
	g_source_attach(tic, uscita->contesto);

	g_main_loop_run(uscita->ciclo);

	g_source_destroy(tic);
	g_source_unref(tic);
	if (uscita->spia_kde && uscita->bus)
	{
		g_dbus_connection_signal_unsubscribe(uscita->bus, uscita->spia_kde);
		uscita->spia_kde = 0;
	}
	sgancia(uscita);
	g_main_context_pop_thread_default(uscita->contesto);
	return NULL;
}

Uscita *uscita_avvia(UscitaAnnuncio su_uscita, gpointer dati, TipoCompositore tipo)
{
	Uscita *uscita = g_new0(Uscita, 1);

	uscita->su_uscita = su_uscita;
	uscita->dati = dati;
	uscita->tipo = tipo;
	uscita->contesto = g_main_context_new();
	uscita->ciclo = g_main_loop_new(uscita->contesto, FALSE);
	uscita->thread = g_thread_new("remotix-uscita", thread_uscita, uscita);
	return uscita;
}

void uscita_ferma(Uscita *uscita)
{
	if (!uscita)
		return;
	if (uscita->ciclo)
		g_main_loop_quit(uscita->ciclo);
	if (uscita->thread)
		g_thread_join(uscita->thread);
	g_clear_pointer(&uscita->ciclo, g_main_loop_unref);
	g_clear_pointer(&uscita->contesto, g_main_context_unref);
	g_clear_object(&uscita->bus);
	g_free(uscita->cliente);
	g_free(uscita);
}
