#include "appunti_mutter.h"

#include <gio/gunixfdlist.h>
#include <glib-unix.h>
#include <unistd.h>

#include "registro.h"

#define NOME_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"

#define ATTESA_CHIAMATA_MS 5000

/*
 * Il tetto di quel che si copia, e ce ne vuole uno.
 *
 * Dall'altra parte del descrittore c'e' un'applicazione qualunque, e niente le
 * impedisce di offrire un flusso che non finisce mai.  Sedici megabyte tengono
 * dentro un'immagine grande e una pagina di testo lunghissima; oltre, e' molto
 * piu' probabile che sia un guasto che un appunto.
 */
#define TETTO_BYTE (16 * 1024 * 1024)

/* Quanto si aspetta un blocco dal descrittore prima di dichiararlo perso: chi
 * scrive dall'altro capo puo' essere lento, ma non muto. */
#define ATTESA_LETTURA_MS 5000

struct AppuntiMutter
{
	GDBusConnection *bus;
	char *controllo;

	GMainContext *contesto;
	GMainLoop *ciclo;
	GThread *thread;

	/* L'ultimo annuncio della sessione, tenuto qui perche' deve sopravvivere
	 * alla connessione: chi si ricollega non riceve un segnale nuovo. */
	GStrv ultimi_tipi;
	guint sottoscrizione_offerta;
	guint sottoscrizione_richiesta;

	/* Le richiamate e il loro proprietario.  Il lucchetto e' preso mentre una
	 * richiamata gira, cosi' `appunti_mutter_ascolta(NULL, NULL, NULL)` aspetta chi e'
	 * a meta' strada invece di liberargli il contesto sotto i piedi. */
	GMutex lucchetto;
	AppuntiSuOfferta su_offerta;
	AppuntiSuRichiesta su_richiesta;
	gpointer dati;
};

static GVariant *chiama(AppuntiMutter *appunti, const char *metodo, GVariant *argomenti,
                        const GVariantType *tipo, GError **sbaglio)
{
	return g_dbus_connection_call_sync(appunti->bus, NOME_REMOTE, appunti->controllo,
	                                   IFACE_SESSIONE, metodo, argomenti, tipo,
	                                   G_DBUS_CALL_FLAGS_NONE, ATTESA_CHIAMATA_MS, NULL, sbaglio);
}

/* Come sopra, ma la risposta porta un descrittore. */
static int chiama_per_descrittore(AppuntiMutter *appunti, const char *metodo, GVariant *argomenti,
                                  GError **sbaglio)
{
	g_autoptr(GUnixFDList) elenco = NULL;
	g_autoptr(GVariant) risposta = NULL;
	gint32 indice = -1;

	risposta = g_dbus_connection_call_with_unix_fd_list_sync(
	    appunti->bus, NOME_REMOTE, appunti->controllo, IFACE_SESSIONE, metodo, argomenti,
	    G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE, ATTESA_CHIAMATA_MS, NULL, &elenco, NULL,
	    sbaglio);
	if (!risposta)
		return -1;

	g_variant_get(risposta, "(h)", &indice);
	return g_unix_fd_list_get(elenco, indice, sbaglio);
}

/* ------------------------------------------------------------------ *
 * I due segnali
 * ------------------------------------------------------------------ */
static void su_padrone_cambiato(GDBusConnection *bus, const char *mittente, const char *percorso,
                                const char *interfaccia, const char *segnale, GVariant *parametri,
                                gpointer dati)
{
	AppuntiMutter *appunti = dati;
	g_autoptr(GVariant) opzioni = NULL;
	g_autoptr(GVariant) tipi = NULL;
	g_autofree const char **mime = NULL;
	gboolean nostro = FALSE;

	g_variant_get(parametri, "(@a{sv})", &opzioni);

	/*
	 * ⛔ IL RITORNO SI RICONOSCE QUI, ed e' la prima cosa da guardare.
	 *
	 * Mutter emette questo segnale anche dopo una NOSTRA `SetSelection`, con
	 * `session-is-owner` a vero: se lo si trattasse come una copia nuova, si
	 * annuncerebbe al client quel che il client ci ha appena annunciato, e i due
	 * lati si rincorrerebbero senza fine.
	 */
	if (g_variant_lookup(opzioni, "session-is-owner", "b", &nostro) && nostro)
	{
		traccia("appunti: e' il ritorno della nostra offerta, non una copia nuova");
		return;
	}

	/*
	 * ⛔ NEL SEGNALE I TIPI STANNO DENTRO UNA TUPLA, e nei metodi no.
	 *
	 *    `SetSelection` vuole `mime-types` come `as`; `SelectionOwnerChanged` lo
	 *    consegna come `(as)`.  Chi legge `as` non trova niente e TORNA IN
	 *    SILENZIO: gli appunti funzionano in un verso solo, e nel registro non
	 *    compare nulla che lo spieghi.  Costato una prova, il 5 agosto 2026 —
	 *    ed e' un'asimmetria del compositore, non nostra: la aggira anche il
	 *    riferimento (`grd-session.c`, che cerca `(as)` e ne prende il figlio 0).
	 *
	 *    Si accettano entrambe le forme, perche' quale delle due arrivi dipende
	 *    dalla versione di Mutter, e sbagliare costa un verso degli appunti.
	 */
	tipi = g_variant_lookup_value(opzioni, "mime-types", G_VARIANT_TYPE_STRING_ARRAY);
	if (!tipi)
	{
		g_autoptr(GVariant) tupla =
		    g_variant_lookup_value(opzioni, "mime-types", G_VARIANT_TYPE("(as)"));

		if (tupla)
			tipi = g_variant_get_child_value(tupla, 0);
	}
	if (!tipi)
	{
		diagnostica("appunti: la sessione ha annunciato una copia senza tipi leggibili");
		return;
	}
	mime = g_variant_get_strv(tipi, NULL);

	g_mutex_lock(&appunti->lucchetto);
	g_clear_pointer(&appunti->ultimi_tipi, g_strfreev);
	appunti->ultimi_tipi = g_strdupv((GStrv) mime);
	if (appunti->su_offerta)
		appunti->su_offerta(mime, appunti->dati);
	g_mutex_unlock(&appunti->lucchetto);
}

static void su_trasferimento(GDBusConnection *bus, const char *mittente, const char *percorso,
                             const char *interfaccia, const char *segnale, GVariant *parametri,
                             gpointer dati)
{
	AppuntiMutter *appunti = dati;
	const char *mime = NULL;
	guint32 serial = 0;

	g_variant_get(parametri, "(&su)", &mime, &serial);
	diagnostica("appunti: la sessione vuole incollare «%s» (richiesta %u)", mime, serial);

	g_mutex_lock(&appunti->lucchetto);
	if (appunti->su_richiesta)
	{
		appunti->su_richiesta(mime, serial, appunti->dati);
		g_mutex_unlock(&appunti->lucchetto);
		return;
	}
	g_mutex_unlock(&appunti->lucchetto);

	/* Nessuno ascolta: si risponde comunque di no.  Una richiesta senza
	 * risposta lascia l'applicazione che incolla in attesa a tempo
	 * indeterminato, e quel che l'utente vede e' un desktop piantato. */
	appunti_mutter_rispondi(appunti, serial, NULL);
}

/* ------------------------------------------------------------------ *
 * Il thread che fa girare il contesto
 * ------------------------------------------------------------------ */
static gpointer thread_appunti(gpointer dati)
{
	AppuntiMutter *appunti = dati;

	g_main_context_push_thread_default(appunti->contesto);
	g_main_loop_run(appunti->ciclo);
	g_main_context_pop_thread_default(appunti->contesto);
	return NULL;
}

AppuntiMutter *appunti_mutter_apri(GDBusConnection *bus, const char *percorso_controllo, GError **sbaglio)
{
	AppuntiMutter *appunti = g_new0(AppuntiMutter, 1);

	appunti->bus = g_object_ref(bus);
	appunti->controllo = g_strdup(percorso_controllo);
	g_mutex_init(&appunti->lucchetto);

	/*
	 * Il contesto si crea e si SOTTOSCRIVE qui, sul thread chiamante, con il
	 * contesto messo come predefinito: GDBus lega la consegna al contesto
	 * predefinito del thread che sottoscrive, non a quello che poi lo fa
	 * girare.  Sottoscrivere dentro il thread nuovo sarebbe la strada
	 * apparentemente ovvia, e lascerebbe una finestra in cui i segnali
	 * arriverebbero prima che il thread sia pronto.
	 */
	appunti->contesto = g_main_context_new();
	g_main_context_push_thread_default(appunti->contesto);

	appunti->sottoscrizione_offerta = g_dbus_connection_signal_subscribe(
	    bus, NULL, IFACE_SESSIONE, "SelectionOwnerChanged", percorso_controllo, NULL,
	    G_DBUS_SIGNAL_FLAGS_NONE, su_padrone_cambiato, appunti, NULL);
	appunti->sottoscrizione_richiesta = g_dbus_connection_signal_subscribe(
	    bus, NULL, IFACE_SESSIONE, "SelectionTransfer", percorso_controllo, NULL,
	    G_DBUS_SIGNAL_FLAGS_NONE, su_trasferimento, appunti, NULL);

	g_main_context_pop_thread_default(appunti->contesto);

	{
		GVariantBuilder vuote;
		g_autoptr(GVariant) risposta = NULL;

		/*
		 * Senza `mime-types`: cosi' Mutter non ci fa proprietari di niente e ci
		 * racconta invece chi lo e' adesso, con un `SelectionOwnerChanged` che
		 * arriva subito.
		 */
		g_variant_builder_init(&vuote, G_VARIANT_TYPE("a{sv}"));
		risposta = chiama(appunti, "EnableClipboard", g_variant_new("(a{sv})", &vuote), NULL,
		                  sbaglio);
		if (!risposta)
		{
			g_prefix_error(sbaglio, "Mutter non concede la clipboard: ");
			appunti_mutter_chiudi(appunti);
			return NULL;
		}
	}

	appunti->ciclo = g_main_loop_new(appunti->contesto, FALSE);
	appunti->thread = g_thread_new("remotix-appunti", thread_appunti, appunti);

	informazione("appunti della sessione accesi");
	return appunti;
}

GStrv appunti_mutter_ultimi_tipi(AppuntiMutter *appunti)
{
	GStrv copia;

	if (!appunti)
		return NULL;
	g_mutex_lock(&appunti->lucchetto);
	copia = appunti->ultimi_tipi ? g_strdupv(appunti->ultimi_tipi) : NULL;
	g_mutex_unlock(&appunti->lucchetto);
	return copia;
}

void appunti_mutter_ascolta(AppuntiMutter *appunti, AppuntiSuOfferta su_offerta, AppuntiSuRichiesta su_richiesta,
                     gpointer dati)
{
	if (!appunti)
		return;
	g_mutex_lock(&appunti->lucchetto);
	appunti->su_offerta = su_offerta;
	appunti->su_richiesta = su_richiesta;
	appunti->dati = dati;
	g_mutex_unlock(&appunti->lucchetto);
}

void appunti_mutter_chiudi(AppuntiMutter *appunti)
{
	if (!appunti)
		return;

	/* Prima si smette di ascoltare — e la chiamata aspetta chi e' a meta'
	 * strada — poi si spegne il ciclo, poi si tolgono le sottoscrizioni. */
	appunti_mutter_ascolta(appunti, NULL, NULL, NULL);

	/*
	 * ⛔ NIENTE `DisableClipboard`, mai — nemmeno qui.  Vedi l'intestazione: in
	 *    Mutter 48.7 quella chiamata lascia la clipboard accesa a meta', e da
	 *    li' in poi nessuno la puo' piu' riaccendere.  Chiudendo la sessione di
	 *    controllo se ne va tutto insieme, che e' il modo pulito.
	 */

	if (appunti->ciclo)
		g_main_loop_quit(appunti->ciclo);
	if (appunti->thread)
		g_thread_join(appunti->thread);
	g_clear_pointer(&appunti->ciclo, g_main_loop_unref);

	if (appunti->bus)
	{
		if (appunti->sottoscrizione_offerta)
			g_dbus_connection_signal_unsubscribe(appunti->bus, appunti->sottoscrizione_offerta);
		if (appunti->sottoscrizione_richiesta)
			g_dbus_connection_signal_unsubscribe(appunti->bus, appunti->sottoscrizione_richiesta);

	}

	g_clear_pointer(&appunti->contesto, g_main_context_unref);
	g_strfreev(appunti->ultimi_tipi);
	g_clear_object(&appunti->bus);
	g_mutex_clear(&appunti->lucchetto);
	g_free(appunti->controllo);
	g_free(appunti);
}

/* ------------------------------------------------------------------ *
 * I trasferimenti
 * ------------------------------------------------------------------ */
gboolean appunti_mutter_offri(AppuntiMutter *appunti, const char *const *mime, GError **sbaglio)
{
	GVariantBuilder opzioni;
	g_autoptr(GVariant) risposta = NULL;

	if (!appunti)
		return FALSE;

	g_variant_builder_init(&opzioni, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&opzioni, "{sv}", "mime-types", g_variant_new_strv(mime, -1));

	risposta = chiama(appunti, "SetSelection", g_variant_new("(a{sv})", &opzioni), NULL, sbaglio);
	return risposta != NULL;
}

/* Legge un descrittore fino alla fine, con un tetto e senza restare appesa. */
static GBytes *bevi_tutto(int fd, GError **sbaglio)
{
	GByteArray *raccolto = g_byte_array_new();
	guint8 pezzo[16384];

	while (TRUE)
	{
		GPollFD sonda = { .fd = fd, .events = G_IO_IN | G_IO_HUP | G_IO_ERR };
		gssize letti;

		if (g_poll(&sonda, 1, ATTESA_LETTURA_MS) <= 0)
		{
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
			            "chi doveva consegnare gli appunti non ha scritto niente per %d ms",
			            ATTESA_LETTURA_MS);
			g_byte_array_free(raccolto, TRUE);
			return NULL;
		}

		letti = read(fd, pezzo, sizeof pezzo);
		if (letti == 0)
			break; /* fine */
		if (letti < 0)
		{
			if (errno == EINTR)
				continue;
			g_set_error(sbaglio, G_IO_ERROR, g_io_error_from_errno(errno),
			            "lettura degli appunti fallita: %s", g_strerror(errno));
			g_byte_array_free(raccolto, TRUE);
			return NULL;
		}

		if (raccolto->len + letti > TETTO_BYTE)
		{
			g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_NO_SPACE,
			            "appunti piu' grandi del tetto di %d MB: lasciati dove sono",
			            TETTO_BYTE / (1024 * 1024));
			g_byte_array_free(raccolto, TRUE);
			return NULL;
		}
		g_byte_array_append(raccolto, pezzo, (guint) letti);
	}

	return g_byte_array_free_to_bytes(raccolto);
}

GBytes *appunti_mutter_leggi(AppuntiMutter *appunti, const char *mime, GError **sbaglio)
{
	int fd;
	GBytes *dati;

	if (!appunti)
		return NULL;

	fd = chiama_per_descrittore(appunti, "SelectionRead", g_variant_new("(s)", mime), sbaglio);
	if (fd < 0)
		return NULL;

	dati = bevi_tutto(fd, sbaglio);
	close(fd);

	if (dati)
		diagnostica("appunti: letti %" G_GSIZE_FORMAT " byte di «%s» dalla sessione",
		            g_bytes_get_size(dati), mime);
	return dati;
}

void appunti_mutter_rispondi(AppuntiMutter *appunti, guint32 serial, GBytes *dati)
{
	g_autoptr(GError) sbaglio = NULL;
	gboolean riuscito = FALSE;
	int fd;

	if (!appunti)
		return;

	if (!dati)
	{
		/* Niente da consegnare, e lo si dice: e' comunque una risposta, ed e'
		 * quel che sblocca chi sta incollando. */
		g_autoptr(GVariant) risposta =
		    chiama(appunti, "SelectionWriteDone", g_variant_new("(ub)", serial, FALSE), NULL,
		           &sbaglio);
		if (!risposta)
			diagnostica("SelectionWriteDone(no) non riuscita: %s", sbaglio->message);
		return;
	}

	fd = chiama_per_descrittore(appunti, "SelectionWrite", g_variant_new("(u)", serial), &sbaglio);
	if (fd < 0)
	{
		avviso("appunti: SelectionWrite rifiutata (%s)", sbaglio->message);
		return;
	}

	{
		gsize quanti = 0;
		const guint8 *inizio = g_bytes_get_data(dati, &quanti);
		gsize scritti = 0;

		riuscito = TRUE;
		while (scritti < quanti)
		{
			gssize adesso = write(fd, inizio + scritti, quanti - scritti);

			if (adesso < 0)
			{
				if (errno == EINTR)
					continue;
				avviso("appunti: scrittura verso la sessione fallita: %s", g_strerror(errno));
				riuscito = FALSE;
				break;
			}
			scritti += (gsize) adesso;
		}
		if (riuscito)
			diagnostica("appunti: consegnati %" G_GSIZE_FORMAT " byte alla sessione", quanti);
	}

	/* Si chiude PRIMA di dichiarare fatto: chi legge dall'altro capo aspetta la
	 * fine del flusso, e un descrittore ancora aperto la fine non la fa mai. */
	close(fd);

	{
		g_autoptr(GVariant) risposta = chiama(
		    appunti, "SelectionWriteDone", g_variant_new("(ub)", serial, riuscito), NULL, &sbaglio);
		if (!risposta)
			diagnostica("SelectionWriteDone non riuscita: %s", sbaglio->message);
	}
}
