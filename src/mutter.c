/*
 * mutter.c — vedi mutter.h per la sequenza e per le ragioni.
 */
#include "mutter.h"

#include <gio/gio.h>
#include <string.h>

#include "registro.h"

#define AREA "cattura"

#define NOME_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define PERCORSO_REMOTE "/org/gnome/Mutter/RemoteDesktop"
#define IFACE_REMOTE "org.gnome.Mutter.RemoteDesktop"
#define IFACE_REMOTE_SESSIONE "org.gnome.Mutter.RemoteDesktop.Session"

#define NOME_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define PERCORSO_SCREENCAST "/org/gnome/Mutter/ScreenCast"
#define IFACE_SCREENCAST "org.gnome.Mutter.ScreenCast"
#define IFACE_SC_SESSIONE "org.gnome.Mutter.ScreenCast.Session"
#define IFACE_SC_FLUSSO "org.gnome.Mutter.ScreenCast.Stream"

#define NOME_DISPLAY "org.gnome.Mutter.DisplayConfig"
#define PERCORSO_DISPLAY "/org/gnome/Mutter/DisplayConfig"
#define IFACE_DISPLAY "org.gnome.Mutter.DisplayConfig"

/*
 * `MetaScreenCastCursorMode`: 0 nascosto, 1 incorporato nell'immagine, 2 come
 * metadato.  Si sceglie il METADATO, e sono due ragioni:
 *
 *  - incorporarlo costa un fotogramma intero per ogni movimento del mouse (in
 *    v1 era la ragione principale per cui lo scorrimento sembrava quello di
 *    xrdp);
 *  - ⛔ e alla fase 2 il cursore nell'immagine sarebbe un difetto misurabile:
 *    il banco della fase 4 guarda un fotogramma e pretende che il puntatore del
 *    desktop NON ci sia (`SPECIFICHE.md` §7.1).  Qui non lo si legge ancora.
 */
#define CURSORE_METADATO 2u

#define ATTESA_CHIAMATA_MS 15000
#define ATTESA_NODO_MS 10000

#define MONITOR_MAX 16

struct MutterSessione
{
	GDBusConnection *bus;
	char *controllo; /* percorso della sessione RemoteDesktop */
	char *cattura;   /* percorso della sessione ScreenCast    */
	char *flusso;    /* percorso dello Stream                 */
	uint32_t nodo;
	char *mapping_id;

	/* ⛔ Il nostro schermo: due strade indipendenti, e se non concordano NULL. */
	char *monitor;
	char *monitor_prodotto;
	char *prima[MONITOR_MAX]; /* i connettori che c'erano PRIMA di RecordVirtual */
	guint monitor_prima;
	guint monitor_dopo;
};

/* ------------------------------------------------------------------ *
 *  Il bus, e perche' non e' quello condiviso di GLib
 * ------------------------------------------------------------------ */

/*
 * ⛔ MAI `g_bus_get_sync` SUL BUS DI SESSIONE: GIO vi tiene acceso
 *    `exit-on-close`, e al logout la connessione che cade porta via il PROCESSO
 *    invece di darci un errore.  Un server che sparisce quando l'utente esce
 *    dalla sessione grafica e' `LEZIONI.md` §5, e il sintomo — «il server muore
 *    e nessuno sa chi l'ha ucciso» — e' la forma E6 (il mittente dedotto invece
 *    che chiesto).
 */
static GDBusConnection *bus_di_sessione(GError **sbaglio)
{
	g_autofree char *indirizzo =
	    g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, sbaglio);
	GDBusConnection *bus;

	if (!indirizzo)
		return NULL;
	bus = g_dbus_connection_new_for_address_sync(
	    indirizzo,
	    G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
	        G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
	    NULL, NULL, sbaglio);
	if (bus)
		g_dbus_connection_set_exit_on_close(bus, FALSE);
	return bus;
}

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

/* ------------------------------------------------------------------ *
 *  I monitor — chiesti a DisplayConfig, che non fa male a nessuno
 * ------------------------------------------------------------------ */

/*
 * ⛔ NON con `org.gnome.Shell.Screenshot`.  Su una sessione a zero monitor
 *    Mutter tenta una texture 0×0, gnome-shell muore, e con
 *    `OnFailure=gnome-session-shutdown.target` se ne va **tutta la sessione**
 *    `[M]` 12 agosto 2026 — provato involontariamente.  ⇒ Il controllo
 *    distruggerebbe la cosa che controlla, e solo nel caso guasto.
 *
 * ⭐ `GetCurrentState` risponde con i monitor uno per uno.  La forma e'
 *    `(ua((ssss)a(siiddada{sv})a{sv})a(iiduba(ssss)a{sv})a{sv})`: qui interessa
 *    il primo elemento della terna del monitor, cioe' `(connettore, venditore,
 *    prodotto, seriale)`.
 *
 * ⛔ E una lettura NEGATA non e' «zero monitor»: se la chiamata fallisce si
 *    ritorna -1 e chi ha chiamato lo dichiara (forma E8).
 */
static int elenca_monitor(GDBusConnection *bus, char **nomi, char **prodotti, guint quanti_max)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) monitor = NULL;
	GVariantIter iter;
	GVariant *voce;
	guint quanti = 0;

	risposta = g_dbus_connection_call_sync(bus, NOME_DISPLAY, PERCORSO_DISPLAY, IFACE_DISPLAY,
	                                       "GetCurrentState", NULL, NULL, G_DBUS_CALL_FLAGS_NONE,
	                                       ATTESA_CHIAMATA_MS, NULL, &sbaglio);
	if (!risposta)
	{
		registro_dice(AREA, "⚠ DisplayConfig non risponde (%s): non so quanti monitor ci sono, "
		                    "e non dico zero",
		              sbaglio->message);
		return -1;
	}
	monitor = g_variant_get_child_value(risposta, 1);
	g_variant_iter_init(&iter, monitor);
	while ((voce = g_variant_iter_next_value(&iter)))
	{
		g_autoptr(GVariant) v = voce;
		g_autoptr(GVariant) chiave = g_variant_get_child_value(v, 0);
		const char *connettore = NULL, *venditore = NULL, *prodotto = NULL, *seriale = NULL;

		g_variant_get(chiave, "(&s&s&s&s)", &connettore, &venditore, &prodotto, &seriale);
		if (quanti < quanti_max)
		{
			if (nomi)
				nomi[quanti] = g_strdup(connettore);
			if (prodotti)
				prodotti[quanti] = g_strdup(prodotto);
		}
		quanti++;
	}
	return (int) quanti;
}

static gboolean fra(char **elenco, guint quanti, const char *nome)
{
	guint i;

	for (i = 0; i < quanti; i++)
		if (elenco[i] && !strcmp(elenco[i], nome))
			return TRUE;
	return FALSE;
}

/*
 * ⛔ IL NOSTRO SCHERMO SI RICONOSCE CON DUE STRADE, E DEVONO CONCORDARE.
 *
 *   1. il diff dei connettori prima/dopo `RecordVirtual`: il nuovo e' nostro;
 *   2. il nome del PRODOTTO, che Mutter mette a «Virtual remote monitor» per i
 *      monitor di `RecordVirtual` e a «MetaVirtualMonitor» per quello della
 *      sessione.
 *
 * Se non concordano — o se i nuovi non sono esattamente uno — si lascia NULL.
 * ⛔ Scegliere «il primo» o «quello a 1080p» e' la forma E2: sul server i due
 *    monitor sono ENTRAMBI 1920×1080@60 `[M]`, e sotto quell'etichetta ci sono
 *    due schermi diversi.
 */
gboolean mutter_monitor_cerca(MutterSessione *sessione)
{
	char *nomi[MONITOR_MAX] = { NULL };
	char *prodotti[MONITOR_MAX] = { NULL };
	guint quanti_prima;
	int quanti_dopo = -1;
	guint i, nuovi = 0;
	int indice_nuovo = -1;

	g_return_val_if_fail(sessione != NULL, FALSE);
	if (sessione->monitor)
		return TRUE; /* gia' saputo: non si richiede al bus per abitudine */
	quanti_prima = sessione->monitor_prima;

	quanti_dopo = elenca_monitor(sessione->bus, nomi, prodotti, MONITOR_MAX);
	if (quanti_dopo < 0)
		return FALSE;
	sessione->monitor_dopo = (guint) quanti_dopo;

	for (i = 0; i < (guint) quanti_dopo && i < MONITOR_MAX; i++)
	{
		if (!fra(sessione->prima, quanti_prima, nomi[i]))
		{
			nuovi++;
			indice_nuovo = (int) i;
		}
	}

	if (nuovi != 1 || indice_nuovo < 0)
	{
		registro_dice(AREA,
		              "⚠ dopo il montaggio sono comparsi %u monitor nuovi invece di 1 "
		              "(%u prima, %d dopo): NON dico quale sia il nostro",
		              nuovi, quanti_prima, quanti_dopo);
	}
	else if (!prodotti[indice_nuovo] || !strstr(prodotti[indice_nuovo], "remote"))
	{
		/* ⛔ Le due strade non concordano: ci si ferma invece di scegliere la
		 *    piu' comoda.  Un nome sbagliato qui manda una finestra a schermo
		 *    intero sull'altro monitor, e la cattura riceve zero fotogrammi
		 *    senza un errore da nessuna parte `[M]` 12 agosto 2026. */
		registro_dice(AREA,
		              "⚠ il monitor comparso (%s) si chiama «%s», e non e' il nome che Mutter "
		              "da' a un monitor di RecordVirtual («Virtual remote monitor»): non lo "
		              "dichiaro nostro",
		              nomi[indice_nuovo], prodotti[indice_nuovo] ? prodotti[indice_nuovo] : "?");
	}
	else
	{
		sessione->monitor = g_strdup(nomi[indice_nuovo]);
		sessione->monitor_prodotto = g_strdup(prodotti[indice_nuovo]);
		registro_dice(AREA, "il nostro monitor e' %s («%s»), %u prima e %d dopo",
		              sessione->monitor, sessione->monitor_prodotto, quanti_prima, quanti_dopo);
	}

	for (i = 0; i < MONITOR_MAX; i++)
	{
		g_free(nomi[i]);
		g_free(prodotti[i]);
	}
	return sessione->monitor != NULL;
}

/* ------------------------------------------------------------------ *
 *  L'annuncio del nodo
 * ------------------------------------------------------------------ */

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
 * Aspetta l'annuncio del nodo, e lo fa mettendosi in ascolto PRIMA di avviare il
 * flusso.
 *
 * Il contesto privato serve perche' GDBus consegna i segnali al contesto
 * predefinito del thread AL MOMENTO DELLA SOTTOSCRIZIONE, e questo codice puo'
 * girare su un thread che non fa girare alcun ciclo GLib: senza un contesto da
 * far girare qui, il segnale arriverebbe e non verrebbe mai consegnato.
 */
static gboolean attendi_nodo(MutterSessione *sessione, GError **sbaglio)
{
	GMainContext *contesto = g_main_context_new();
	GSource *battito = NULL;
	guint sottoscrizione;
	gint64 scadenza;
	gboolean esito = FALSE;

	g_main_context_push_thread_default(contesto);

	/* Il mittente si lascia NULL di proposito: filtrando su un nome noto GDBus
	 * deve prima risolverne il proprietario, e fra la sottoscrizione e la
	 * risoluzione c'e' una finestra in cui il segnale verrebbe scartato.  Il
	 * percorso dell'oggetto e' unico per questo flusso, e filtra abbastanza. */
	sottoscrizione = g_dbus_connection_signal_subscribe(
	    sessione->bus, NULL, IFACE_SC_FLUSSO, "PipeWireStreamAdded", sessione->flusso, NULL,
	    G_DBUS_SIGNAL_FLAGS_NONE, su_nodo_annunciato, &sessione->nodo, NULL);

	/* Solo ADESSO si avvia il flusso: non la sessione di cattura, che una
	 * cattura associata rifiuta di avviare da sola. */
	{
		g_autoptr(GVariant) risposta = chiama(sessione->bus, NOME_SCREENCAST, sessione->flusso,
		                                      IFACE_SC_FLUSSO, "Start", NULL, NULL, sbaglio);
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

/* ------------------------------------------------------------------ *
 *  La sequenza
 * ------------------------------------------------------------------ */

MutterSessione *mutter_apri(GError **sbaglio)
{
	MutterSessione *sessione = g_new0(MutterSessione, 1);
	g_autofree char *id_controllo = NULL;
	int quanti_prima;
	GVariantBuilder proprieta;

	sessione->bus = bus_di_sessione(sbaglio);
	if (!sessione->bus)
		goto guasto;

	/* --- 0. i monitor PRIMA: il nostro sara' quello che compare dopo ------- */
	quanti_prima = elenca_monitor(sessione->bus, sessione->prima, NULL, MONITOR_MAX);
	sessione->monitor_prima = quanti_prima > 0 ? (guint) quanti_prima : 0;
	if (quanti_prima == 0)
	{
		/* ⛔ E ZERO MONITOR E' LA SESSIONE NERA, non un dettaglio: `gnome.md`
		 *    §3.1 — in headless `needs_outputs=false`, e senza monitor la
		 *    sessione e' viva, completa e nera.  Non si fallisce (il nostro
		 *    `RecordVirtual` ne monta uno suo), ma si DICHIARA: chi legge zero
		 *    fotogrammi piu' tardi deve avere questa riga sotto gli occhi. */
		registro_dice(AREA, "⚠ la sessione grafica non ha NESSUN monitor: e' la sessione "
		                    "«viva, completa e nera» di gnome.md §3.1");
	}

	/* --- 1. il controllo, creato e NON avviato ---------------------------- */
	{
		g_autoptr(GVariant) risposta =
		    chiama(sessione->bus, NOME_REMOTE, PERCORSO_REMOTE, IFACE_REMOTE, "CreateSession", NULL,
		           G_VARIANT_TYPE("(o)"), sbaglio);
		if (!risposta)
		{
			g_prefix_error(sbaglio,
			               "Mutter non espone RemoteDesktop (la sessione grafica e' avviata?): ");
			goto guasto;
		}
		g_variant_get(risposta, "(o)", &sessione->controllo);
	}

	id_controllo = proprieta_stringa(sessione->bus, NOME_REMOTE, sessione->controllo,
	                                 IFACE_REMOTE_SESSIONE, "SessionId", sbaglio);
	if (!id_controllo)
		goto guasto;

	/*
	 * ⚠ QUI, E NON ALTROVE, VA `ConnectToEIS` QUANDO ARRIVERA' LA FASE 4.
	 *
	 * Il riferimento lo chiama subito dopo `CreateSession` e PRIMA di `Start`, e
	 * non e' una preferenza: il compositore ha davanti una sessione non ancora
	 * avviata, ed e' li' che accetta di aprire il canale.  ⛔ Non lo si scrive
	 * adesso perche' la fase 2 non comanda niente, e un canale aperto che nessuno
	 * legge sarebbe apparato ereditato — la cosa che il mandato di F2.2 vieta.
	 * Chi lo innestera' trova qui il punto esatto.
	 */

	/* --- 2. la cattura, che si registra sul controllo non ancora avviato --- */
	g_variant_builder_init(&proprieta, G_VARIANT_TYPE("a{sv}"));
	g_variant_builder_add(&proprieta, "{sv}", "remote-desktop-session-id",
	                      g_variant_new_string(id_controllo));
	/* Presa dal riferimento: le animazioni di GNOME su un collegamento remoto
	 * costano banda e non aggiungono nulla. */
	g_variant_builder_add(&proprieta, "{sv}", "disable-animations", g_variant_new_boolean(TRUE));
	{
		g_autoptr(GVariant) risposta = chiama(
		    sessione->bus, NOME_SCREENCAST, PERCORSO_SCREENCAST, IFACE_SCREENCAST, "CreateSession",
		    g_variant_new("(a{sv})", &proprieta), G_VARIANT_TYPE("(o)"), sbaglio);
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
	g_variant_builder_add(&proprieta, "{sv}", "cursor-mode", g_variant_new_uint32(CURSORE_METADATO));
	/* Dichiara che il monitor virtuale e' «di piattaforma», cioe' trattato come
	 * uno schermo vero dal punto di vista della configurazione dei monitor: lo fa
	 * anche il riferimento. */
	g_variant_builder_add(&proprieta, "{sv}", "is-platform", g_variant_new_boolean(TRUE));
	sessione->mapping_id = g_uuid_string_random();
	g_variant_builder_add(&proprieta, "{sv}", "mapping-id",
	                      g_variant_new_string(sessione->mapping_id));
	{
		g_autoptr(GVariant) risposta =
		    chiama(sessione->bus, NOME_SCREENCAST, sessione->cattura, IFACE_SC_SESSIONE,
		           "RecordVirtual", g_variant_new("(a{sv})", &proprieta), G_VARIANT_TYPE("(o)"),
		           sbaglio);
		if (!risposta)
			goto guasto;
		g_variant_get(risposta, "(o)", &sessione->flusso);
	}

	/* --- 5. l'ascolto, e poi l'avvio del flusso --------------------------- */
	if (!attendi_nodo(sessione, sbaglio))
		goto guasto;

	/* ⛔ E QUI NON SI CERCA IL NOSTRO MONITOR: a questo punto non esiste ancora,
	 *    ed e' misurato — nemmeno tre secondi dopo `Stream.Start` compare.  Lo
	 *    cerca `mutter_monitor_cerca`, che chi cattura chiama quando il flusso e'
	 *    attivo.  Cercarlo qui vorrebbe dire scrivere «non e' comparso nessun
	 *    monitor» su una sessione sana. */

	registro_dice(AREA, "monitor virtuale montato: nodo PipeWire %u, flusso %s", sessione->nodo,
	              sessione->flusso);
	return sessione;

guasto:
	mutter_chiudi(sessione);
	return NULL;
}

uint32_t mutter_nodo(const MutterSessione *sessione)
{
	return sessione ? sessione->nodo : 0;
}

const char *mutter_percorso_flusso(const MutterSessione *sessione)
{
	return sessione ? sessione->flusso : NULL;
}

const char *mutter_percorso_controllo(const MutterSessione *sessione)
{
	return sessione ? sessione->controllo : NULL;
}

const char *mutter_mapping_id(const MutterSessione *sessione)
{
	return sessione ? sessione->mapping_id : NULL;
}

const char *mutter_monitor_nostro(const MutterSessione *sessione)
{
	return sessione ? sessione->monitor : NULL;
}

const char *mutter_monitor_prodotto(const MutterSessione *sessione)
{
	return sessione ? sessione->monitor_prodotto : NULL;
}

void mutter_monitor_conteggi(const MutterSessione *sessione, guint *prima, guint *dopo)
{
	if (prima)
		*prima = sessione ? sessione->monitor_prima : 0;
	if (dopo)
		*dopo = sessione ? sessione->monitor_dopo : 0;
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
		/* Attesa CORTA: quasi sempre si arriva qui perche' la sessione grafica se
		 * n'e' gia' andata, e aspettare quindici secondi una risposta che non puo'
		 * arrivare terrebbe fermo chi sta smontando. */
		g_autoptr(GVariant) risposta = g_dbus_connection_call_sync(
		    sessione->bus, NOME_REMOTE, sessione->controllo, IFACE_REMOTE_SESSIONE, "Stop", NULL,
		    NULL, G_DBUS_CALL_FLAGS_NONE, 2000, NULL, &sbaglio);

		if (!risposta)
			registro_dettaglio(AREA, "chiusura della sessione di controllo: %s", sbaglio->message);
	}

	g_clear_object(&sessione->bus);
	g_free(sessione->controllo);
	g_free(sessione->cattura);
	g_free(sessione->flusso);
	g_free(sessione->mapping_id);
	g_free(sessione->monitor);
	g_free(sessione->monitor_prodotto);
	for (guint i = 0; i < MONITOR_MAX; i++)
		g_free(sessione->prima[i]);
	g_free(sessione);
}
