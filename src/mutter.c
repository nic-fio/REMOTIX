/*
 * mutter.c — vedi mutter.h per la sequenza e per le ragioni.
 */
#include "mutter.h"

#include <gio/gio.h>
#include <gio/gunixfdlist.h>
#include <string.h>
#include <unistd.h>

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
	char *mapping_id;           /* quello che DICHIARIAMO noi a RecordVirtual */
	char *mapping_id_pubblicato; /* ⛔ quello che Mutter GENERA e ci dice     */

	/* Il canale di input, aperto da `ConnectToEIS` al punto giusto della
	 * sequenza.  -1 = non aperto, e chi lo riceve lo DICHIARA. */
	int eis;

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

/* ⛔⛔ LA GUARDIA SULLA SCALA — e previene il difetto che NON si vede.
 *
 * `[M]` 14 agosto 2026: con `org.gnome.desktop.interface scaling-factor = 2` i
 * pixel del flusso restano quelli chiesti, ma il monitor LOGICO prende scala
 * **2,0** anche quando l'unica scala ammessa per quel modo e' 1,0
 * (`meta-monitor.c:1988` scavalca la propria lista).  Il layout diventa allora
 * `roundf(2133/2) = 1067`, e **1067x2 = 2134 != 2133**.
 *
 * ⇒ ⛔ E' lo spazio delle coordinate dell'INPUT: il puntatore finisce altrove, e
 *   NESSUNA riga di registro lo dice.  E' esattamente il sintomo che l'utente ha
 *   descritto per due giorni sul Samsung DeX — «il mouse ha sempre problemi con
 *   le coordinate degli elementi».
 *
 * ⚠ Qui si LEGGE e si DICE; non si spegne niente.  Chi decide che farne e' il
 *   chiamante: con la tela a misura fissa il danno era teorico, con la tela alla
 *   misura del client (`DECISIONI.md` §5.0-sexies) e' concreto.
 *
 * Ritorna la scala peggiore trovata, o -1 se non si e' potuta leggere. */
static double scala_dei_monitor_logici(GDBusConnection *bus)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) logici = NULL;
	GVariantIter iter;
	GVariant *voce;
	double peggiore = 1.0;
	gboolean vista = FALSE;

	risposta = g_dbus_connection_call_sync(bus, NOME_DISPLAY, PERCORSO_DISPLAY, IFACE_DISPLAY,
	                                       "GetCurrentState", NULL, NULL, G_DBUS_CALL_FLAGS_NONE,
	                                       ATTESA_CHIAMATA_MS, NULL, &sbaglio);
	if (!risposta)
		return -1.0;
	/* ⚠ Il figlio 2 e' l'elenco dei monitor LOGICI — `(iiduba(ssss)a{sv})` — e
	 *   la scala e' il terzo campo.  Il figlio 1, che legge `elenca_monitor`,
	 *   e' un'altra cosa: i monitor FISICI, che la scala non ce l'hanno. */
	logici = g_variant_get_child_value(risposta, 2);
	g_variant_iter_init(&iter, logici);
	while ((voce = g_variant_iter_next_value(&iter)))
	{
		g_autoptr(GVariant) v = voce;
		g_autoptr(GVariant) s = g_variant_get_child_value(v, 2);

		if (!g_variant_is_of_type(s, G_VARIANT_TYPE_DOUBLE))
			continue;
		vista = TRUE;
		if (g_variant_get_double(s) > peggiore)
			peggiore = g_variant_get_double(s);
	}
	return vista ? peggiore : -1.0;
}

/*
 * ⛔⭐⭐ LA SCALA DEL **NOSTRO** MONITOR, e non la peggiore della macchina.
 *
 * ⛔ E LA DIFFERENZA E' LA RAGIONE PER CUI QUESTA FUNZIONE ESISTE.  La guardia
 *    di §5.0-sexies dice di **fallire** se la scala non e' 1,0, e farlo sulla
 *    «peggiore fra tutti i monitor logici» spegnerebbe il servizio su una
 *    macchina sanissima: un portatile con lo schermo interno a 2,0 e il nostro
 *    monitor virtuale a 1,0 non ha nessun difetto, e la peggiore direbbe 2,0.
 *    ⇒ Si guarda il monitor logico che contiene il NOSTRO connettore, e basta.
 *
 * ⚠ Il monitor logico e' `(iiduba(ssss)a{sv})`: la scala e' il terzo campo, e il
 *   sesto e' l'elenco dei monitor fisici che ci stanno sopra — di ciascuno il
 *   primo campo e' il connettore.
 *
 * Ritorna -1 se non si e' potuta leggere, o se il nostro connettore non compare
 * in nessun monitor logico.  ⛔ «Non lo so» non e' «1,0».
 */
static double scala_del_nostro(GDBusConnection *bus, const char *connettore)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) logici = NULL;
	GVariantIter iter;
	GVariant *voce;

	if (!bus || !connettore || !connettore[0])
		return -1.0;
	risposta = g_dbus_connection_call_sync(bus, NOME_DISPLAY, PERCORSO_DISPLAY, IFACE_DISPLAY,
	                                       "GetCurrentState", NULL, NULL, G_DBUS_CALL_FLAGS_NONE,
	                                       ATTESA_CHIAMATA_MS, NULL, &sbaglio);
	if (!risposta)
		return -1.0;
	logici = g_variant_get_child_value(risposta, 2);
	g_variant_iter_init(&iter, logici);
	while ((voce = g_variant_iter_next_value(&iter)))
	{
		g_autoptr(GVariant) v = voce;
		g_autoptr(GVariant) s = g_variant_get_child_value(v, 2);
		g_autoptr(GVariant) miei = g_variant_get_child_value(v, 5);
		GVariantIter mi;
		GVariant *m;

		if (!g_variant_is_of_type(s, G_VARIANT_TYPE_DOUBLE))
			continue;
		g_variant_iter_init(&mi, miei);
		while ((m = g_variant_iter_next_value(&mi)))
		{
			g_autoptr(GVariant) mm = m;
			const char *c = NULL, *ven = NULL, *pro = NULL, *ser = NULL;

			if (!g_variant_is_of_type(mm, G_VARIANT_TYPE("(ssss)")))
				continue;
			g_variant_get(mm, "(&s&s&s&s)", &c, &ven, &pro, &ser);
			if (c && !strcmp(c, connettore))
				return g_variant_get_double(s);
		}
	}
	return -1.0;
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

	/* ⛔⛔⭐ UN MONITOR C'ERA GIA', E L'UTENTE VEDREBBE SOLO LO SFONDO.
	 *
	 * `[M]` 20 agosto 2026, e sono costati un'ora: sulla sessione di «prova»
	 * c'erano DUE figli di due server nostri (le porte 7700 e 7730), ognuno col
	 * suo monitor virtuale — `Meta-1` 2544x926 **primario** e `Meta-0` 2532x840,
	 * il nostro.
	 *
	 * ⛔ E su GNOME **barra e dock stanno solo sul monitor PRIMARIO**: il
	 *    secondario porta lo sfondo e basta.  ⇒ Il desktop arrivava, i contatori
	 *    erano tutti verdi (`dipinti == consegnati`, zero buchi, zero errori) e
	 *    l'utente diceva «mancano gli elementi della shell».  **Nessuna riga di
	 *    nessun registro lo raccontava.**
	 *
	 * ⚠ Non si FALLISCE, e la ragione e' che questo non e' sempre un difetto: un
	 *   monitor che c'era gia' puo' essere legittimo (una sessione con uno
	 *   schermo vero).  ⛔ Ma si DICE, forte, con la cura accanto — perche' il
	 *   sintomo che produce non ha nessun altro modo di essere diagnosticato
	 *   (`CODER.md` §4.2, e `LEZIONI.md` §1.16: gli strumenti erano tutti verdi).
	 */
	if (quanti_prima > 0)
	{
		GString *elenco = g_string_new(NULL);
		guint j;

		for (j = 0; j < quanti_prima && j < MONITOR_MAX; j++)
			g_string_append_printf(elenco, "%s%s", j ? ", " : "",
			                       sessione->prima[j] ? sessione->prima[j] : "?");
		registro_dice(AREA,
		              "⛔ C'ERANO GIA' %u monitor su questa sessione (%s) e il nostro si "
		              "aggiunge: su GNOME la barra e il dock stanno SOLO sul monitor "
		              "PRIMARIO, che resta il loro ⇒ l'utente vedra' il nostro, cioe' "
		              "SOLO LO SFONDO, con tutti i contatori verdi.  ⚠ Quasi sempre e' "
		              "un ALTRO server nostro attaccato alla stessa sessione: si spegne "
		              "quello, oppure ogni server usa un utente suo",
		              quanti_prima, elenco->str);
		g_string_free(elenco, TRUE);
	}

	/* ⛔ La scala si guarda QUI, una volta, appena il monitor virtuale esiste: e'
	 *    il primo istante in cui c'e' qualcosa da guardare, ed e' prima che una
	 *    sola coordinata sia stata convertita. */
	{
		double scala = scala_dei_monitor_logici(sessione->bus);

		if (scala < 0)
			registro_dice(AREA, "⚠ la scala dei monitor logici non si e' potuta leggere: "
			                    "non dico 1,0 per abitudine");
		else if (scala != 1.0)
			registro_dice(AREA,
			              "⛔ SCALA %.3f invece di 1,0 — lo spazio delle coordinate "
			              "dell'input NON coincide con i pixel del flusso, e il puntatore "
			              "andra' altrove senza che nulla lo dica.  Cura: "
			              "`gsettings set org.gnome.desktop.interface scaling-factor 0` "
			              "(`DECISIONI.md` §5.0-sexies, guardia 2)",
			              scala);
	}

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

	/* ⛔ PRIMA di qualunque `goto guasto`: con `g_new0` varrebbe **0**, e la
	 *    chiusura chiuderebbe il descrittore 0 — cioe' lo standard input di chi
	 *    ci ospita.  «Non aperto» si scrive -1, non si lascia allo zero. */
	sessione->eis = -1;

	sessione->bus = bus_di_sessione(sbaglio);
	if (!sessione->bus)
		goto guasto;

	/* --- 0. i monitor PRIMA: il nostro sara' quello che compare dopo ------- */
	quanti_prima = elenca_monitor(sessione->bus, sessione->prima, NULL, MONITOR_MAX);
	sessione->monitor_prima = quanti_prima > 0 ? (guint) quanti_prima : 0;
	if (quanti_prima == 0)
	{
		/* ⛔ E ZERO MONITOR E' LA SESSIONE NERA, non un dettaglio: `STUDI.md` §gnome
		 *    §3.1 — in headless `needs_outputs=false`, e senza monitor la
		 *    sessione e' viva, completa e nera.  Non si fallisce (il nostro
		 *    `RecordVirtual` ne monta uno suo), ma si DICHIARA: chi legge zero
		 *    fotogrammi piu' tardi deve avere questa riga sotto gli occhi. */
		registro_dice(AREA, "⚠ la sessione grafica non ha NESSUN monitor: e' la sessione "
		                    "«viva, completa e nera» di STUDI.md §gnome §3.1");
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
	 * ⭐ LA FASE 4 E' ARRIVATA, e `ConnectToEIS` sta QUI — nel punto che il
	 *    commento della fase 2 aveva marcato.  *Innestato il 14 agosto 2026.*
	 *
	 * Il riferimento lo chiama subito dopo `CreateSession` e PRIMA di `Start`, e
	 * non e' una preferenza: il compositore ha davanti una sessione non ancora
	 * avviata, ed e' li' che accetta di aprire il canale.
	 *
	 * ⚠ E poi si e' letto il codice (`reference-gnome/rapporti/06-mutter-input.md`
	 *   §1.2, `[R]`): `handle_connect_to_eis` (`meta-remote-desktop-session.c:1929`)
	 *   ⛔ **non chiama ne' `check_permission` ne' `check_can_notify`**, e
	 *   `initialize_viewports` e' chiamata da `Start` se l'EIS esiste gia' e da
	 *   `ConnectToEIS` se la sessione e' gia' avviata: **tutt'e due gli ordini
	 *   reggono**.  Resta qui perche' e' l'ordine del riferimento, non perche'
	 *   l'altro rompa.
	 *
	 * ⛔ E NON SI FALLISCE SE NON SI APRE: `CODER.md` §4.2.  Senza input la
	 *    cattura funziona lo stesso — l'utente GUARDA e non comanda — e far
	 *    cadere l'intera apertura per il canale di input sarebbe togliere la
	 *    sessione a chi voleva solo vedere.  ⇒ Si dichiara, e `input_apri`
	 *    fallira' con un errore che dice PERCHE'.
	 */
	{
		g_autoptr(GError) sbaglio_eis = NULL;
		g_autoptr(GUnixFDList) descrittori = NULL;
		g_autoptr(GVariant) risposta = NULL;
		GVariantBuilder senza_opzioni;
		gint32 indice = -1;

		sessione->eis = -1;
		/*
		 * ⛔ Nessuna opzione: `device-types` assente vuol dire «accendi tutto»
		 *    — tastiera | puntatore | touchscreen (`meta-remote-desktop-session.c:1957-1959`
		 *    `[R]`).  ⚠ E la `MetaEis` si crea UNA VOLTA SOLA per sessione: una
		 *    seconda `ConnectToEIS` riuserebbe la stessa e **ignorerebbe** le
		 *    opzioni nuove.  Chiedere tutto adesso e' l'unico modo di non
		 *    scoprirlo alla fase 6.
		 */
		g_variant_builder_init(&senza_opzioni, G_VARIANT_TYPE("a{sv}"));
		risposta = g_dbus_connection_call_with_unix_fd_list_sync(
		    sessione->bus, NOME_REMOTE, sessione->controllo, IFACE_REMOTE_SESSIONE, "ConnectToEIS",
		    g_variant_new("(a{sv})", &senza_opzioni), G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE,
		    ATTESA_CHIAMATA_MS, NULL, &descrittori, NULL, &sbaglio_eis);
		if (!risposta)
		{
			registro_dice(AREA,
			              "⚠ ConnectToEIS rifiutata (%s): la sessione si apre lo stesso, ma "
			              "NESSUN input arrivera' al desktop",
			              sbaglio_eis->message);
		}
		else
		{
			g_variant_get(risposta, "(h)", &indice);
			sessione->eis = g_unix_fd_list_get(descrittori, indice, &sbaglio_eis);
			if (sessione->eis < 0)
				registro_dice(AREA, "⚠ ConnectToEIS ha risposto ma il descrittore non si legge "
				                    "(%s): nessun input arrivera' al desktop",
				              sbaglio_eis->message);
			else
				registro_dice(AREA, "canale di input aperto: descrittore EIS %d", sessione->eis);
		}
	}

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

	/* ⛔⭐ E LA RIGA DICE QUEL CHE C'E', NON QUEL CHE CI SARA' — 27 agosto
	 *     2026.  Qui c'era scritto «monitor virtuale montato», due righe sotto
	 *     il commento che dichiara che **il monitor non esiste ancora**: due
	 *     affermazioni opposte a distanza di due righe, e quella che si legge
	 *     nel registro era la falsa.  ⚠ Un messaggio che afferma un fatto che
	 *     non e' vero e' peggio del silenzio: manda fuori strada chi legge, e
	 *     il silenzio almeno non lo fa.  ⇒ Adesso dice il fatto vero — la
	 *     sessione e' avviata e il flusso ha il suo nodo — e nomina quel che
	 *     manca ancora. */
	registro_dice(AREA,
	              "sessione di cattura AVVIATA: nodo PipeWire %u, flusso %s.  ⚠ Il monitor "
	              "virtuale NON e' ancora comparso: lo cerca `mutter_monitor_cerca()` quando "
	              "il flusso consegna (vedi il riquadro qui sopra)",
	              sessione->nodo, sessione->flusso);
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

GDBusConnection *mutter_bus(const MutterSessione *sessione)
{
	return sessione ? sessione->bus : NULL;
}

const char *mutter_mapping_id(const MutterSessione *sessione)
{
	return sessione ? sessione->mapping_id : NULL;
}

int mutter_eis_fd(const MutterSessione *sessione)
{
	return sessione ? sessione->eis : -1;
}

/*
 * ⛔⛔⛔ LA CURA «C» — si rifa' il canale EIS lasciando in piedi TUTTO il resto.
 *       Aggiunta il 21 agosto 2026, e il documento di fase la chiama «C».
 *       🔸 DERIVATA: la decisione e' del coordinatore, non dell'utente.
 *
 * IL DANNO CHE CURA, `[M]` 21 agosto 2026 (`banchi/06-b33-risveglio.sh`): quando
 * Mutter ricrea i dispositivi assoluti mentre un pulsante e' premuto, quel
 * pulsante resta giu' **nel posto** e da li' in poi **il desktop non prende piu'
 * un clic** — per sempre, e senza un errore da nessuna parte.
 *
 * ⛔ E dal lato del cliente non si recupera: `handle_button`
 *    (`meta-eis-client.c:612-621`) guarda `device->button_state`, che sul
 *    dispositivo NUOVO e' pulito, e ingoia il rilascio **prima** che il posto lo
 *    veda.  `[M]` press+release sul nuovo fa `count` 1→2→1 (giornale di Mutter
 *    con `MUTTER_DEBUG=input`: *«Dropping repeated press … count 2»* e
 *    *«Dropping repeated release … count 1»*).
 *
 * ⭐ L'UNICO codice che riporta il conto a zero e' `drop_device()`
 *    (`meta-eis-client.c:144-168`), e il suo unico chiamante e'
 *    `meta_eis_client_disconnect()` (`:1075`) — cioe' **la caduta del canale
 *    EIS**.  `[M]` Nel giornale si vedono le sei righe *«Releasing pressed
 *    buttons while destroying virtual input device»* proprio li'.
 *
 * ⛔⛔ E PERCHE' QUESTA FUNZIONE STA IN `mutter.c` E NON IN `input.c` — e la
 *      ragione NON e' quella che avevo scritto il 21 agosto la prima volta.
 *
 *      Avevo scritto: *«chiudere il `dup` di libei non basta, perche' il socket
 *      ha ancora aperto il descrittore di `mutter.c`»*.  ⛔ `[M]` **Smentita**
 *      dal guasto innestato `RG3`: togliendo il `close()` la guarigione
 *      funziona lo stesso.  Il distacco lo manda `ei_disconnect()` come
 *      messaggio di protocollo (`[M]`, guasto `RG4`).
 *
 *      ⭐ La ragione vera, che regge: **dopo il distacco il descrittore messo
 *        da parte e' morto**, e per averne uno NUOVO serve una `ConnectToEIS`
 *        — cioe' il bus, il nome e il percorso della sessione.  `input.c` non
 *        li ha e non li deve avere: conosce `libei`, non D-Bus.
 *
 * ⭐ E che una seconda `ConnectToEIS` sia lecita non e' una speranza: `[R]`
 *    `meta-remote-desktop-session.c:1943-1969` — `session->eis` si **riusa** se
 *    c'e' gia', e ogni chiamata aggiunge un cliente col suo socket.  ⇒ La
 *    sessione `RemoteDesktop`, il monitor virtuale e il flusso PipeWire **non si
 *    toccano**: e' questa la differenza fra la cura e «riaccendere il server».
 *
 * ⚠ E le opzioni restano assenti come alla prima chiamata: la `MetaEis` esiste
 *   gia' e le ignorerebbe (vedi il riquadro dentro `mutter_apri`).  Metterle
 *   qui darebbe l'impressione di poter cambiare le capacita' a caldo.
 *
 *   ritorna  il descrittore NUOVO (>= 0), gia' messo da parte in questa
 *            sessione: chi lo usa ne fa un `dup`, come sempre;
 *   ritorna  -1 e riempie `sbaglio`: ⛔ e allora il canale EIS **non c'e'
 *            piu'** — il vecchio e' stato chiuso comunque, perche' e' quella
 *            chiusura a guarire il posto.  Chi chiama lo deve dichiarare.
 */
int mutter_eis_riattacca(MutterSessione *sessione, GError **sbaglio)
{
	g_autoptr(GUnixFDList) descrittori = NULL;
	g_autoptr(GVariant) risposta = NULL;
	GVariantBuilder senza_opzioni;
	gint32 indice = -1;

	if (!sessione || !sessione->bus || !sessione->controllo)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "nessuna sessione RemoteDesktap aperta: non c'e' nessun canale EIS da rifare");
		return -1;
	}

	/*
	 * ⛔⛔ E QUI C'ERA UNA SPIEGAZIONE SBAGLIATA, SMENTITA DALLA MISURA — 21
	 *      agosto 2026, guasto innestato `RG3` di
	 *      `banchi/06-b33-risveglio-guasti.py`.
	 *
	 * Diceva: *«si chiude prima e si chiede dopo, e l'ordine E' la cura: finche'
	 * questo descrittore e' aperto il socket resta connesso e Mutter non vede
	 * nessun distacco»*.  ⛔ `[M]` **Falso**: tolto questo `close()`, la
	 * guarigione funziona **esattamente come prima** e nessun caso del banco
	 * cambia colore.
	 *
	 * ⭐ Il distacco lo manda `ei_disconnect()` (in `input.c`) come **messaggio
	 *   di protocollo**: Mutter esegue `meta_eis_client_disconnect()` — e quindi
	 *   `drop_device()` — senza aspettare l'EOF del socket.  `[M]` Lo prova il
	 *   guasto `RG4`, che toglie proprio quella riga e rompe la guarigione.
	 *
	 * ⚠ E il `close()` resta, per una ragione piu' modesta e vera: **senza, si
	 *   perde un descrittore a ogni guarigione**.  ⛔ Un difetto che non fa
	 *   rumore per ore e poi esaurisce la tavola dei descrittori.
	 *
	 * ⚠ Questa funzione resta comunque necessaria, e non e' cambiato: dopo il
	 *   distacco il descrittore messo da parte e' morto, e uno NUOVO lo puo'
	 *   chiedere solo chi ha il bus e il percorso della sessione — cioe' qui.
	 */
	if (sessione->eis >= 0)
	{
		close(sessione->eis);
		registro_dice(AREA,
		              "⭐ canale EIS vecchio chiuso (descrittore %d).  ⚠ Non e' QUESTA la cosa "
		              "che guarisce il posto — `[M]` 21 ago 2026, guasto RG3: togliendo la "
		              "chiusura la guarigione funziona lo stesso.  Il distacco lo manda "
		              "`ei_disconnect()`; questa riga serve a non perdere un descrittore a "
		              "ogni guarigione",
		              sessione->eis);
		sessione->eis = -1;
	}

	g_variant_builder_init(&senza_opzioni, G_VARIANT_TYPE("a{sv}"));
	risposta = g_dbus_connection_call_with_unix_fd_list_sync(
	    sessione->bus, NOME_REMOTE, sessione->controllo, IFACE_REMOTE_SESSIONE, "ConnectToEIS",
	    g_variant_new("(a{sv})", &senza_opzioni), G_VARIANT_TYPE("(h)"), G_DBUS_CALL_FLAGS_NONE,
	    ATTESA_CHIAMATA_MS, NULL, &descrittori, NULL, sbaglio);
	if (!risposta)
	{
		registro_dice(AREA,
		              "⛔ la seconda ConnectToEIS e' stata rifiutata: da adesso NESSUN input "
		              "arriva al desktop, e la sessione resta viva solo per guardare");
		return -1;
	}
	g_variant_get(risposta, "(h)", &indice);
	sessione->eis = g_unix_fd_list_get(descrittori, indice, sbaglio);
	if (sessione->eis < 0)
	{
		registro_dice(AREA, "⛔ ConnectToEIS ha risposto ma il descrittore non si legge: da "
		                    "adesso NESSUN input arriva al desktop");
		return -1;
	}
	registro_dice(AREA, "⭐ canale EIS RIAPERTO: descrittore %d.  ⚠ La sessione, il monitor e il "
	                    "flusso NON sono stati toccati",
	              sessione->eis);
	return sessione->eis;
}

/*
 * ⛔⛔ IL `mapping-id` VIENE DA MUTTER, NON DA NOI — e il verso conta.
 *
 * `reference-gnome/rapporti/06-mutter-input.md` §7.2 `[≠]`, riletto nel codice
 * il 14 agosto 2026:
 *
 *   - `handle_record_virtual` (`meta-screen-cast-session.c:747-765`) legge
 *     **`cursor-mode` e `is-platform` e basta**: la nostra proprieta'
 *     `mapping-id` viene **ignorata in silenzio**, senza un errore;
 *   - `meta_screen_cast_stream_initable_init` (`meta-screen-cast-stream.c:445-458`)
 *     chiama `meta_remote_desktop_session_acquire_mapping_id`, che genera un
 *     **UUID casuale** (`:558-575`), e lo pubblica nella proprieta'
 *     `Parameters` del flusso.
 *
 * ⇒ Cercare la regione di `libei` con l'UUID che abbiamo dichiarato NOI vuol
 *   dire non trovarla mai, e cadere sul ripiego «prendo la prima» — che con
 *   uno schermo solo funziona, e smette di funzionare esattamente il giorno in
 *   cui gli schermi sono due.  E' il difetto che `input.c` non deve avere.
 *
 * ⚠ Si legge PIGRAMENTE, la prima volta che serve: la sequenza di
 *   `mutter_apri` non si tocca (ci lavorano altri anelli), e questa lettura non
 *   ha ragione di stare li' dentro.
 */
const char *mutter_mapping_id_pubblicato(MutterSessione *sessione)
{
	g_autoptr(GError) sbaglio = NULL;
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) valore = NULL;
	char *letto = NULL;

	if (!sessione || !sessione->bus || !sessione->flusso)
		return NULL;
	if (sessione->mapping_id_pubblicato)
		return sessione->mapping_id_pubblicato;

	risposta = chiama(sessione->bus, NOME_SCREENCAST, sessione->flusso,
	                  "org.freedesktop.DBus.Properties", "Get",
	                  g_variant_new("(ss)", IFACE_SC_FLUSSO, "Parameters"), G_VARIANT_TYPE("(v)"),
	                  &sbaglio);
	if (!risposta)
	{
		/* ⛔ Lettura NEGATA, non «non c'e'»: chi legge questa riga deve poter
		 *    distinguere i due casi (`CODER.md` §3.10). */
		registro_dice(AREA, "⚠ i Parameters del flusso non si leggono (%s): il mapping-id di "
		                    "Mutter resta ignoto, NON dico che manchi",
		              sbaglio->message);
		return NULL;
	}
	g_variant_get(risposta, "(v)", &valore);
	if (!g_variant_lookup(valore, "mapping-id", "s", &letto) || !letto || !*letto)
	{
		g_free(letto);
		registro_dice(AREA, "⚠ i Parameters del flusso NON portano un mapping-id: la regione del "
		                    "puntatore si dovra' riconoscere per geometria");
		return NULL;
	}

	sessione->mapping_id_pubblicato = letto;
	registro_dice(AREA, "mapping-id pubblicato da Mutter: «%s»%s", letto,
	              g_strcmp0(letto, sessione->mapping_id) == 0
	                  ? ""
	                  : "  ⛔ DIVERSO da quello che avevamo dichiarato noi a RecordVirtual");
	return sessione->mapping_id_pubblicato;
}

const char *mutter_monitor_nostro(const MutterSessione *sessione)
{
	return sessione ? sessione->monitor : NULL;
}

/* ⛔⭐⭐ LA GUARDIA 2 DI §5.0-sexies, CHIUSA — e chiude un difetto che nessuna
 *     riga di registro raccontava.
 *
 * ⚠ Fino al 15 agosto 2026 la scala si LEGGEVA e si DICEVA, e il commento sopra
 *   `scala_dei_monitor_logici()` lo dichiarava: *«con la tela a misura fissa il
 *   danno era teorico, con la tela alla misura del client e' concreto»*.  ⛔ Da
 *   stanotte la tela E' alla misura del client, quindi il danno e' concreto: il
 *   layout del monitor logico e i pixel del flusso non coincidono piu', **e lo
 *   spazio delle coordinate dell'input e' il layout** ⇒ il puntatore va altrove.
 *
 * ⛔ Si chiede a Mutter, e si chiede DEL NOSTRO monitor: la scala peggiore della
 *    macchina direbbe 2,0 su un portatile con lo schermo interno hi-dpi, e
 *    spegnerebbe una sessione che non ha nessun difetto.
 *
 * Ritorna -1 se non si e' potuta leggere: ⛔ e chi chiama NON deve trattarlo
 * come 1,0 — «non lo so» e «va bene» sono due fatti diversi. */
double mutter_scala_nostra(const MutterSessione *sessione)
{
	if (!sessione || !sessione->bus || !sessione->monitor || !sessione->monitor[0])
		return -1.0;
	return scala_del_nostro(sessione->bus, sessione->monitor);
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

	if (sessione->eis >= 0)
		close(sessione->eis);

	g_clear_object(&sessione->bus);
	g_free(sessione->controllo);
	g_free(sessione->cattura);
	g_free(sessione->flusso);
	g_free(sessione->mapping_id);
	g_free(sessione->mapping_id_pubblicato);
	g_free(sessione->monitor);
	g_free(sessione->monitor_prodotto);
	for (guint i = 0; i < MONITOR_MAX; i++)
		g_free(sessione->prima[i]);
	g_free(sessione);
}
