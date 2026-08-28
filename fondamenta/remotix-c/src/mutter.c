#include "mutter.h"

#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include <unistd.h>

#include "registro.h"
#include "sessione.h"

#define NOME_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define PERCORSO_REMOTE "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_REMOTE_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"

#define NOME_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define PERCORSO_SCREENCAST "/org/gnome/Mutter/ScreenCast"
#define IFACE_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define IFACE_SC_SESSIONE "org.gnome.Mutter.ScreenCast.Session"
#define IFACE_SC_FLUSSO "org.gnome.Mutter.ScreenCast.Stream"

/* `MetaScreenCastCursorMode`: 0 nascosto, 1 incorporato nell'immagine, 2 come
 * metadato.  Si sceglie il METADATO: incorporarlo costerebbe un fotogramma
 * intero per ogni movimento del mouse — e' stata la ragione principale per cui
 * lo scorrimento sembrava quello di xrdp — mentre come metadato il video cambia
 * solo quando cambia il desktop e il puntatore lo disegna il client.  In fase 3
 * non lo si legge ancora: il client mostra la propria freccia. */
#define CURSORE_METADATO 2u

#define ATTESA_CHIAMATA_MS 15000
#define ATTESA_NODO_MS 10000

struct MutterSessione
{
	GDBusConnection *bus;
	char *controllo; /* percorso della sessione RemoteDesktop */
	char *cattura;   /* percorso della sessione ScreenCast    */
	char *flusso;    /* percorso dello Stream                 */
	uint32_t nodo;
	char *mapping_id;
	int fd_eis;
};

static GVariant *chiama(GDBusConnection *bus, const char *nome, const char *percorso,
                        const char *interfaccia, const char *metodo, GVariant *argomenti,
                        const GVariantType *tipo_risposta, GError **sbaglio)
{
	return g_dbus_connection_call_sync(bus, nome, percorso, interfaccia, metodo, argomenti,
	                                   tipo_risposta, G_DBUS_CALL_FLAGS_NONE, ATTESA_CHIAMATA_MS,
	                                   NULL, sbaglio);
}

/* Legge una proprieta' senza costruire un GDBusProxy: un proxy porterebbe con
 * se' una cache e un ciclo di vita che qui non servono. */
static char *proprieta_stringa(GDBusConnection *bus, const char *nome, const char *percorso,
                               const char *interfaccia, const char *proprieta, GError **sbaglio)
{
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) valore = NULL;

	risposta = chiama(bus, nome, percorso, "org.freedesktop.DBus.Properties", "Get",
	                  g_variant_new("(ss)", interfaccia, proprieta), G_VARIANT_TYPE("(v)"),
	                  sbaglio);
	if (!risposta)
		return NULL;
	g_variant_get(risposta, "(v)", &valore);
	if (!g_variant_is_of_type(valore, G_VARIANT_TYPE_STRING))
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED, "%s non e' una stringa", proprieta);
		return NULL;
	}
	return g_variant_dup_string(valore, NULL);
}

static void su_nodo_annunciato(GDBusConnection *bus, const char *mittente, const char *percorso,
                               const char *interfaccia, const char *segnale, GVariant *parametri,
                               gpointer dati)
{
	uint32_t *nodo = dati;

	if (g_variant_is_of_type(parametri, G_VARIANT_TYPE("(u)")))
		g_variant_get(parametri, "(u)", nodo);
}

static gboolean sveglia(gpointer dati)
{
	return G_SOURCE_CONTINUE;
}

/*
 * Aspetta l'annuncio del nodo, e lo fa mettendosi in ascolto PRIMA di avviare
 * il flusso.
 *
 * Il contesto privato serve perche' GDBus consegna i segnali al contesto
 * predefinito del thread AL MOMENTO DELLA SOTTOSCRIZIONE, e questo codice gira
 * sul thread della connessione RDP, che non fa girare alcun ciclo GLib: senza
 * un contesto da far girare qui, il segnale arriverebbe e non verrebbe mai
 * consegnato.
 */
static gboolean attendi_nodo(MutterSessione *sessione, GError **sbaglio)
{
	GMainContext *contesto = g_main_context_new();
	GSource *battito = NULL;
	guint sottoscrizione;
	gint64 scadenza;
	gboolean esito = FALSE;

	g_main_context_push_thread_default(contesto);

	/* Il mittente si lascia NULL di proposito.  Filtrando su un nome noto,
	 * GDBus deve prima risolverne il proprietario, e fra la sottoscrizione e la
	 * risoluzione c'e' una finestra in cui il segnale verrebbe scartato.  Il
	 * percorso dell'oggetto e' unico per questo flusso, quindi filtra gia'
	 * abbastanza. */
	sottoscrizione = g_dbus_connection_signal_subscribe(
	    sessione->bus, NULL, IFACE_SC_FLUSSO, "PipeWireStreamAdded", sessione->flusso, NULL,
	    G_DBUS_SIGNAL_FLAGS_NONE, su_nodo_annunciato, &sessione->nodo, NULL);

	/* Solo ADESSO si avvia il flusso: non la sessione di cattura, che una
	 * cattura associata rifiuta di avviare da sola. */
	{
		g_autoptr(GVariant) risposta =
		    chiama(sessione->bus, NOME_SCREENCAST, sessione->flusso, IFACE_SC_FLUSSO, "Start",
		           NULL, NULL, sbaglio);
		if (!risposta)
			goto fine;
	}

	battito = g_timeout_source_new(50);
	g_source_set_callback(battito, sveglia, NULL, NULL);
	g_source_attach(battito, contesto);

	scadenza = g_get_monotonic_time() + (gint64) ATTESA_NODO_MS * 1000;
	while (sessione->nodo == 0 && g_get_monotonic_time() < scadenza)
		g_main_context_iteration(contesto, TRUE);

	if (sessione->nodo == 0)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
		            "Mutter non ha annunciato il nodo PipeWire entro %d secondi",
		            ATTESA_NODO_MS / 1000);
		goto fine;
	}
	esito = TRUE;

fine:
	if (battito)
	{
		g_source_destroy(battito);
		g_source_unref(battito);
	}
	g_dbus_connection_signal_unsubscribe(sessione->bus, sottoscrizione);
	g_main_context_pop_thread_default(contesto);
	g_main_context_unref(contesto);
	return esito;
}

MutterSessione *mutter_apri(GError **sbaglio)
{
	MutterSessione *sessione = g_new0(MutterSessione, 1);
	g_autofree char *id_controllo = NULL;
	GVariantBuilder proprieta;

	sessione->fd_eis = -1;

	sessione->bus = sessione_bus(sbaglio);   /* mai g_bus_get_sync: vedi sessione.h */
	if (!sessione->bus)
		goto guasto;

	/* --- 1. il controllo, creato e NON avviato ---------------------------- */
	{
		g_autoptr(GVariant) risposta =
		    chiama(sessione->bus, NOME_REMOTE, PERCORSO_REMOTE, IFACE_REMOTE, "CreateSession",
		           NULL, G_VARIANT_TYPE("(o)"), sbaglio);
		if (!risposta)
		{
			g_prefix_error(sbaglio, "Mutter non espone RemoteDesktop (la sessione grafica e' "
			                        "avviata?): ");
			goto guasto;
		}
		g_variant_get(risposta, "(o)", &sessione->controllo);
	}

	id_controllo = proprieta_stringa(sessione->bus, NOME_REMOTE, sessione->controllo,
	                                 IFACE_REMOTE_SESSIONE, "SessionId", sbaglio);
	if (!id_controllo)
		goto guasto;

	/*
	 * --- 1-bis. il canale di input, chiesto QUI e non dopo -----------------
	 *
	 * Come il riferimento, che chiama `ConnectToEIS` subito dopo `CreateSession`
	 * e prima di `Start`.  Non e' una preferenza estetica: il compositore ha una
	 * sessione non ancora avviata davanti, ed e' li' che accetta di aprire il
	 * canale.
	 *
	 * Se lo nega, NON si fallisce: la sessione resta di sola visione.  Guardare
	 * senza comandare e' meno di quel che si voleva, ma e' molto piu' di niente
	 * — ed e' la regola «degradare, non fallire» di §2 di SPECIFICA.md.
	 */
	{
		g_autoptr(GError) sbaglio_eis = NULL;
		g_autoptr(GUnixFDList) descrittori = NULL;
		g_autoptr(GVariant) risposta = NULL;
		GVariantBuilder vuote;

		g_variant_builder_init(&vuote, G_VARIANT_TYPE("a{sv}"));
		risposta = g_dbus_connection_call_with_unix_fd_list_sync(
		    sessione->bus, NOME_REMOTE, sessione->controllo, IFACE_REMOTE_SESSIONE,
		    "ConnectToEIS", g_variant_new("(a{sv})", &vuote), G_VARIANT_TYPE("(h)"),
		    G_DBUS_CALL_FLAGS_NONE, ATTESA_CHIAMATA_MS, NULL, &descrittori, NULL, &sbaglio_eis);

		if (!risposta)
		{
			avviso("ConnectToEIS rifiutata (%s): la sessione sara' di sola visione",
			       sbaglio_eis->message);
		}
		else
		{
			gint32 indice = -1;

			g_variant_get(risposta, "(h)", &indice);
			sessione->fd_eis = g_unix_fd_list_get(descrittori, indice, &sbaglio_eis);
			if (sessione->fd_eis < 0)
				avviso("il descrittore di ConnectToEIS non e' arrivato (%s)",
				       sbaglio_eis->message);
			else
				diagnostica("canale EIS aperto (descrittore %d)", sessione->fd_eis);
		}
	}

	/* --- 2. la cattura, che si registra sul controllo non ancora avviato --- */
	g_variant_builder_init(&proprieta, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&proprieta, "{sv}", "remote-desktop-session-id",
	                      g_variant_new_string(id_controllo));
	/* Una riga presa dal riferimento: le animazioni di GNOME su un collegamento
	 * remoto costano banda e non aggiungono nulla. */
	g_variant_builder_add(&proprieta, "{sv}", "disable-animations", g_variant_new_boolean(TRUE));
	{
		g_autoptr(GVariant) risposta = chiama(sessione->bus, NOME_SCREENCAST, PERCORSO_SCREENCAST,
		                                      IFACE_SCREENCAST, "CreateSession",
		                                      g_variant_new("(a{sv})", &proprieta),
		                                      G_VARIANT_TYPE("(o)"), sbaglio);
		if (!risposta)
			goto guasto;
		g_variant_get(risposta, "(o)", &sessione->cattura);
	}

	/* --- 3. ADESSO si avvia il controllo ---------------------------------- */
	{
		g_autoptr(GVariant) risposta =
		    chiama(sessione->bus, NOME_REMOTE, sessione->controllo, IFACE_REMOTE_SESSIONE, "Start",
		           NULL, NULL, sbaglio);
		if (!risposta)
			goto guasto;
	}

	/* --- 4. il monitor virtuale ------------------------------------------- */
	g_variant_builder_init(&proprieta, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&proprieta, "{sv}", "cursor-mode",
	                      g_variant_new_uint32(CURSORE_METADATO));
	/* Dichiara che il monitor virtuale e' «di piattaforma», cioe' trattato come
	 * uno schermo vero dal punto di vista della configurazione monitor.  Lo fa
	 * anche il riferimento, ed e' una delle tre spiegazioni possibili della
	 * divergenza sul rettangolo PipeWire (§11.1 di gnome-remote-desktop.md). */
	g_variant_builder_add(&proprieta, "{sv}", "is-platform", g_variant_new_boolean(TRUE));
	/* Il nome con cui ritroveremo questo schermo fra le regioni che libei
	 * annuncia: e' cosi' che il puntatore si mette d'accordo con l'immagine. */
	sessione->mapping_id = g_uuid_string_random();
	g_variant_builder_add(&proprieta, "{sv}", "mapping-id",
	                      g_variant_new_string(sessione->mapping_id));
	{
		g_autoptr(GVariant) risposta = chiama(sessione->bus, NOME_SCREENCAST, sessione->cattura,
		                                      IFACE_SC_SESSIONE, "RecordVirtual",
		                                      g_variant_new("(a{sv})", &proprieta),
		                                      G_VARIANT_TYPE("(o)"), sbaglio);
		if (!risposta)
			goto guasto;
		g_variant_get(risposta, "(o)", &sessione->flusso);
	}

	/* --- 5. l'ascolto, e poi l'avvio del flusso --------------------------- */
	if (!attendi_nodo(sessione, sbaglio))
		goto guasto;

	informazione("monitor virtuale montato: nodo PipeWire %u, flusso %s", sessione->nodo,
	             sessione->flusso);
	return sessione;

guasto:
	mutter_chiudi(sessione);
	return NULL;
}

uint32_t mutter_nodo(const MutterSessione *sessione)
{
	return sessione->nodo;
}

const char *mutter_percorso_flusso(const MutterSessione *sessione)
{
	return sessione->flusso;
}

const char *mutter_percorso_controllo(const MutterSessione *sessione)
{
	return sessione->controllo;
}

int mutter_prendi_fd_eis(MutterSessione *sessione)
{
	int fd = sessione->fd_eis;

	sessione->fd_eis = -1;
	return fd;
}

const char *mutter_mapping_id(const MutterSessione *sessione)
{
	return sessione->mapping_id;
}

void mutter_chiudi(MutterSessione *sessione)
{
	if (!sessione)
		return;

	/* Si ferma il CONTROLLO, e la cattura lo segue: fermare direttamente una
	 * cattura associata Mutter lo rifiuta. */
	if (sessione->bus && sessione->controllo)
	{
		g_autoptr(GError) sbaglio = NULL;
		/* Attesa CORTA: quasi sempre si arriva qui perche' la sessione grafica
		 * se n'e' gia' andata, e aspettare quindici secondi una risposta che non
		 * puo' arrivare terrebbe fermo chi sta smontando. */
		g_autoptr(GVariant) risposta = g_dbus_connection_call_sync(
		    sessione->bus, NOME_REMOTE, sessione->controllo, IFACE_REMOTE_SESSIONE, "Stop", NULL,
		    NULL, G_DBUS_CALL_FLAGS_NONE, 2000, NULL, &sbaglio);

		if (!risposta)
			diagnostica("chiusura della sessione di controllo: %s", sbaglio->message);
	}

	g_clear_object(&sessione->bus);
	/* Il descrittore di EIS lo chiude libei se e' arrivato fin la'; qui si
	 * chiude solo quello che non e' mai stato consegnato a nessuno. */
	if (sessione->fd_eis >= 0)
		close(sessione->fd_eis);
	g_free(sessione->controllo);
	g_free(sessione->cattura);
	g_free(sessione->flusso);
	g_free(sessione->mapping_id);
	g_free(sessione);
}
