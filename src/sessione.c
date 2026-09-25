/*
 * sessione.c — la sessione GNOME headless nasce, e nasce CON un monitor.
 *
 * Il perche' di ogni scelta sta in `sessione.h`, che si legge per primo: qui ci
 * sono le ragioni che riguardano la RIGA, non il modulo.
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COSA E' STATO PORTATO DA v1, E CHE COSA E' STATO LASCIATO LI'
 *
 * Portato (`fondamenta/remotix-c/src/sessione.c`, 797 righe vere):
 *   · `sessione_bus()`            — la connessione nostra, senza «exit-on-close»
 *   · `componi_ambiente()`        — l'ambiente da zero, ramo GNOME (408-540)
 *   · `locale_utf8()`             — la locale che dev'ESISTERE, non solo dirsi
 *   · la forma di `scrivi_dropin()` (569-623) — cartella `user.control`, file,
 *     `daemon-reload`, e la regola «il drop-in PRIMA del comando»
 *   · `avvia()` con `setsid --fork` e il registro della sessione
 *   · `esci_gnome()` con `Logout(2)` (699-711)
 *
 * Lasciato li', perche' e' apparato che in V2 non esiste o non serve a GNOME:
 *   · tutto il ramo KWin: `nome_occupato()`, `esci_kde_ordinato()`,
 *     `esci_kde_a_forza()`, `SESSIONE_COMANDO_KDE`, `TipoCompositore` e
 *     `compositore.h` (in V2 quel file non c'e', e crearlo sarebbe apparato per
 *     un compositore che questa fase non serve);
 *   · `scrivi_tema_cursore()` + `scrivi_cursore_vuoto()` + `cartella_cursori()`
 *     — 120 righe di formato Xcursor a mano: e' la cura del doppio puntatore di
 *     KWin, e su GNOME **non serve** (`STUDI.md` §gnome §5.2: la' il cursore non sta
 *     dentro l'immagine catturata);
 *   · `scrivi_regole_menu()` + `cartella_regole()` — il KIOSK di KDE.  Su GNOME
 *     l'equivalente e' il **lockdown di dconf** (`STUDI.md` §gnome §5.1), che e' un
 *     lavoro suo e non di questo anello;
 *   · `ksmserverrc`, `XDG_MENU_PREFIX`, `XCURSOR_*`, `XDG_CONFIG_DIRS` — tutte
 *     leve di Plasma;
 *   · il parametro `comando` di `sessione_assicura()`: nessuno gli passava mai
 *     niente di diverso dal predefinito, ed era una leva che moltiplicava le
 *     scene senza che nessuno la usasse.
 *
 * ⚠ E una cosa portata da un BANCO e non dal prodotto: l'attesa di `inactive`
 *   invece di «diverso da active» (`banchi/02-sessione-lancia.sh`,
 *   `ferma_e_aspetta`).  v1 aspettava solo che il processo sparisse, e qui
 *   serve di piu' perche' subito dopo si fa RINASCERE la sessione: ripartire
 *   durante `deactivating` e' un'altra prima esecuzione.
 */
#include "sessione.h"

#include "forma.h"
#include "registro.h"

#include <errno.h>
#include <fcntl.h>
#include <locale.h>
#include <signal.h>
#include <string.h>
/* ⚠ `g_stat`, `g_open`, `g_close`: la famiglia di GLib, non quella di POSIX —
 *   è quella che `nodo_della_scheda()` e `processi_miei()` usano. */
#include <glib/gstdio.h>

/* Su questa macchina, senza accelerazione, la sessione ci mette una decina di
 * secondi: il margine e' per le macchine piu' lente. */
#define ATTESA_AVVIO_MS 40000
#define CADENZA_CONTROLLO_MS 500
#define ATTESA_RISPOSTA_MS 5000
/* ⚠ Al bus si chiede solo se un nome ha un padrone: risponde il bus stesso, e
 *   se ci mette piu' di mezzo secondo il problema non e' la sessione grafica. */
#define ATTESA_NOME_MS 500

/*
 * ⛔⭐⭐ IL TETTO DEL SONDAGGIO, e questo numero e' la cura dei «molti secondi»
 *       che l'utente ha visto — quella vera, dopo due diagnosi sbagliate.
 *
 * ⛔ `GetCurrentState` qui non serve per la RISPOSTA: serve per sapere **se il
 *    compositore risponde**.  E il commento di `sessione_viva()` spiega perche'
 *    dev'essere una chiamata vera e non `NameHasOwner`: `org.gnome.Shell`
 *    prende il nome **prima** di `meta_context_start()`, quindi il nome c'e'
 *    quando la Shell non e' ancora buona a niente.
 *
 * ⛔⛔ MA CON `ATTESA_RISPOSTA_MS` (5 s) QUEL SONDAGGIO DIVENTA UN'ATTESA.  Il
 *     nome ha un padrone, la chiamata parte, e la Shell che sta ancora
 *     nascendo non risponde: si resta li' cinque secondi buoni.  `[M]` 16
 *     agosto 2026, giro numero 4 di dodici: fra «IL BUS DI SESSIONE E' MIO» e
 *     la riga dopo passano **diciassette secondi**, e in mezzo il registro non
 *     ha **una sola riga** — tre sondaggi da cinque secondi in fila.
 *
 * ⇒ ⚠ E in quei diciassette secondi il figlio non riprova, non risponde al
 *   padre e non consegna un fotogramma.  E' **lo stesso difetto** che il
 *   riquadro qui sotto dichiara curato: la cura copriva il caso «il nome non
 *   c'e'», non il caso «il nome c'e' e chi lo tiene non risponde ancora».
 *
 * ⭐ Un compositore vivo risponde a `GetCurrentState` in un millisecondo.  Se
 *    non risponde entro 400 ms **non e' pronto**, e quella e' gia' la risposta
 *    che ci serve: si torna al ciclo, si dice «ATTENDI» al padre, e si riprova
 *    fra 200 ms (`PALCO_NASCITA_RIPROVA_MS` in `figlio.c`).
 *
 * ⚠ E i due numeri lavorano INSIEME: senza questo tetto il ciclo non torna mai
 *   indietro, e il ri-tentativo fitto non puo' scattare — `[M]` infatti non e'
 *   scattato nemmeno una volta in ventidue giri.  Senza il ri-tentativo fitto
 *   questo tetto scoprirebbe la prontezza fino a un secondo dopo.
 */
#define ATTESA_SONDAGGIO_MS 400
#define ATTESA_USCITA_MS 10000

/*
 * ⚠ LA GRAZIA — quanto si aspetta il MONITOR dopo che il compositore risponde.
 *
 * `[R]` Il monitor virtuale chiesto con `--virtual-monitor` lo crea
 * `meta-context-main.c:592-597` alla partenza del contesto, cioe' **prima** che
 * `DisplayConfig` risponda a chiunque: se `GetCurrentState` risponde e dice
 * zero monitor, il monitor non arrivera' piu'.  ⇒ Questa attesa e' prudenza
 * sopra un fatto che gia' basterebbe, e serve a una cosa sola: che una macchina
 * lenta non si prenda un «NERA» che non merita.
 *
 * ⛔ E il verso in cui sbaglia e' dichiarato: troppo corta direbbe «nera» a una
 *    sessione sana (falso rosso, si vede subito); troppo lunga farebbe aspettare
 *    e basta.  Si sbaglia dalla parte che si vede.
 */
#define GRAZIA_MONITOR_MS 5000

/*
 * La forma della risposta di `GetCurrentState`, che qui si LEGGE.
 *
 *   (u serial,
 *    a((ssss) a(siiddada{sv}) a{sv})   monitor: (connettore, fornitore,
 *                                                prodotto, seriale), modi, prop
 *    a(iiduba(ssss)a{sv})              monitor logici
 *    a{sv})                            proprieta'
 *
 * e ogni modo e' (id, larghezza, altezza, refresh, scala preferita, scale
 * supportate, proprieta'), col modo IN USO che porta `is-current`.
 *
 * ⛔ E NON si dichiara alla chiamata: si chiede senza tipo e si CONTROLLA dopo.
 *    Dichiararlo vorrebbe dire che, il giorno in cui Mutter aggiunge un campo,
 *    la risposta diventa un errore D-Bus indistinguibile da «il bus non
 *    risponde» — cioe' una sessione viva data per morta, che e' esattamente il
 *    difetto che `sessione.h` racconta.  Cosi' invece si distingue: forma che
 *    non so leggere ⇒ **5, non ho potuto leggere**, e mai «zero monitor».
 */
#define TIPO_STATO "(ua((ssss)a(siiddada{sv})a{sv})a(iiduba(ssss)a{sv})a{sv})"

const char *sessione_marca(SessioneStato stato)
{
	switch (stato) {
	case SESSIONE_SANA:
		return "SANA";
	case SESSIONE_NERA:
		return "NERA: ZERO MONITOR";
	case SESSIONE_MISURA_ALTRA:
		return "MISURA SBAGLIATA";
	case SESSIONE_SCELTO_DA_SE:
		return "MONITOR SCELTO DA SE";
	case SESSIONE_MORTA:
		return "SESSIONE MORTA";
	case SESSIONE_NON_LETTA:
		return "LETTURA IGNOTA";
	}
	return "STATO IGNOTO";
}

/* ------------------------------------------------------------------------- */
static GMutex lucchetto_bus;
static GDBusConnection *bus_di_sessione;

GDBusConnection *sessione_bus(GError **sbaglio)
{
	GDBusConnection *nostro = NULL;

	g_mutex_lock(&lucchetto_bus);

	/* Il bus dell'utente muore col logout e rinasce subito dopo, sullo stesso
	 * socket ma come demone nuovo.  La connessione vecchia resta li', chiusa:
	 * chi continuasse a usarla non riceverebbe un errore chiaro, riceverebbe
	 * silenzio — nessuna sessione, nessun Mutter, schermo nero al secondo
	 * accesso.  Quindi la si butta e se ne apre un'altra. */
	if (bus_di_sessione && g_dbus_connection_is_closed(bus_di_sessione)) {
		registro_dice(REG_SESSIONE, "il bus di sessione si e' chiuso: ne apro un altro");
		g_clear_object(&bus_di_sessione);
	}

	if (!bus_di_sessione) {
		g_autofree char *indirizzo =
			g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, sbaglio);

		/*
		 * Connessione NOSTRA, non quella condivisa di `g_bus_get_sync`: la
		 * condivisa e' un oggetto unico per tutto il processo, che GIO tiene in
		 * cache e a cui accende «exit-on-close».  Aprendola noi, l'interruttore
		 * nasce spento (vedi il riquadro in `sessione.h`).
		 */
		if (indirizzo)
			bus_di_sessione = g_dbus_connection_new_for_address_sync(
				indirizzo,
				G_DBUS_CONNECTION_FLAGS_AUTHENTICATION_CLIENT |
					G_DBUS_CONNECTION_FLAGS_MESSAGE_BUS_CONNECTION,
				NULL, NULL, sbaglio);
		if (bus_di_sessione)
			g_dbus_connection_set_exit_on_close(bus_di_sessione, FALSE);
	}

	if (bus_di_sessione)
		nostro = g_object_ref(bus_di_sessione);
	g_mutex_unlock(&lucchetto_bus);
	return nostro;
}

/*
 * ⛔⭐⭐ NON SI FA UNA DOMANDA A CHI NON C'E' — 16 agosto 2026, e questa riga
 *      chiude il difetto che ha fatto provare cinque volte all'utente.
 *
 * `[M]` Il figlio, mentre la sessione grafica NASCE, restava **trenta secondi**
 * dentro una chiamata sincrona a `GetCurrentState`, e finiva con
 * *«NoReply: Message recipient disconnected»*.  ⛔ In quei trenta secondi non
 * riprovava, non rispondeva al padre e non consegnava un fotogramma: il client
 * si stancava e se ne andava.  ⇒ Il sintomo per l'utente era «il desktop non
 * compare» oppure «si e' rotto tutto», una volta su tre.
 *
 * ⚠ E NON basta accorciare l'attesa: un secondo dentro una chiamata inutile e'
 *   comunque un secondo in cui questo processo non fa il suo mestiere.  ⭐ La
 *   domanda giusta e' un'altra, e costa niente: **quel nome ha un padrone?**
 *   `NameHasOwner` risponde SEMPRE subito, perche' risponde il bus e non un
 *   servizio che sta nascendo.
 *
 * ⇒ Se il padrone non c'e', la risposta e' «la sessione non c'e'» — che e'
 *   esattamente quel che il chiamante voleva sapere, avuta in un millisecondo
 *   invece che in trenta secondi.
 */
static gboolean nome_ha_padrone(GDBusConnection *bus, const char *nome)
{
	g_autoptr(GVariant) risposta = NULL;
	gboolean c_e = FALSE;

	if (!bus || !nome)
		return FALSE;
	risposta = g_dbus_connection_call_sync(
		bus, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
		"NameHasOwner", g_variant_new("(s)", nome), G_VARIANT_TYPE("(b)"),
		G_DBUS_CALL_FLAGS_NO_AUTO_START, ATTESA_NOME_MS, NULL, NULL);
	if (!risposta)
		return FALSE;
	g_variant_get(risposta, "(b)", &c_e);
	return c_e;
}

/* Una chiamata a Mutter, senza dichiarare il tipo della risposta. */
static GVariant *chiedi_a_mutter(GDBusConnection *bus, const char *nome, const char *oggetto,
                                 const char *interfaccia, const char *metodo, GError **sbaglio)
{
	if (!nome_ha_padrone(bus, nome)) {
		/* ⛔⭐ E L'ERRORE E' `NAME_HAS_NO_OWNER`, non uno qualunque: la
		 *     distinzione fra «non c'e'» (4) e «non ho potuto guardare» (5) esiste
		 *     gia' in `sessione_stato()`, e si riconosce PROPRIO da questo codice.
		 *     ⚠ La prima stesura metteva `G_IO_ERROR_NOT_FOUND`, che non combacia:
		 *     ⛔ e allora ogni sessione risultava «LETTURA IGNOTA», il figlio non
		 *     la faceva nascere — «gli stati diversi da morta non si toccano» — e
		 *     `[M]` quattro giri di banco su quattro erano rossi.  Un errore
		 *     giusto col nome sbagliato e' un errore sbagliato. */
		g_set_error(sbaglio, G_DBUS_ERROR, G_DBUS_ERROR_NAME_HAS_NO_OWNER,
		            "«%s» non ha un padrone sul bus: la sessione grafica non c'e' "
		            "(o sta ancora nascendo).  ⛔ Non si CHIEDE a chi non c'e': la "
		            "chiamata resterebbe in coda fino al tetto, e questo processo "
		            "smetterebbe di rispondere per tutto quel tempo",
		            nome);
		return NULL;
	}
	/* ⛔ `ATTESA_SONDAGGIO_MS`, non `ATTESA_RISPOSTA_MS`: qui si SONDA, e un
	 *    sondaggio che aspetta cinque secondi non e' un sondaggio, e' un'attesa
	 *    — vedi il riquadro sulla costante. */
	return g_dbus_connection_call_sync(bus, nome, oggetto, interfaccia, metodo, NULL, NULL,
	                                   G_DBUS_CALL_FLAGS_NO_AUTO_START, ATTESA_SONDAGGIO_MS,
	                                   NULL, sbaglio);
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐ FASE 12 — QUALE DESKTOP.  Il criterio e il perche' stanno in `sessione.h`.
 *
 * ⚠ Si guarda il PATH del processo: il figlio lo ha fisso
 *   (`/usr/local/bin:/usr/bin:/bin`), quindi padre e figlio danno la stessa
 *   risposta senza doversela passare.
 */
static SessioneDesktop desktop_scelto;
static const char *desktop_spiegato;

static void riconosci_desktop(void)
{
	static gsize fatto;

	if (g_once_init_enter(&fatto)) {
		g_autofree char *gnome = g_find_program_in_path("gnome-session");
		g_autofree char *plasma = g_find_program_in_path("startplasma-wayland");
		g_autofree char *xfce = g_find_program_in_path("xfce4-session");
		g_autofree char *labwc = g_find_program_in_path(SESSIONE_PROCESSO_XFCE);
		/* ⭐ FASE 14 — si cerca sempre, ma decide solo DOPO XFCE: vedi il ramo. */
		g_autofree char *lxqt = g_find_program_in_path(SESSIONE_MARCATORE_LXQT);

		if (plasma && !gnome) {
			desktop_scelto = SESSIONE_DESKTOP_KDE;
			desktop_spiegato = "KDE Plasma (c'e' startplasma-wayland, non c'e' "
			                   "gnome-session)";
		} else if (plasma && gnome) {
			desktop_scelto = SESSIONE_DESKTOP_GNOME;
			desktop_spiegato = "GNOME — ⚠ AMBIGUO: su questa macchina ci sono GNOME e "
			                   "KDE, e vince GNOME.  La scelta fra piu' desktop non c'e' "
			                   "ancora (DECISIONI.md §4.6-duodetricies, MASTERPLAN.md M5)";
		} else if (gnome) {
			desktop_scelto = SESSIONE_DESKTOP_GNOME;
			desktop_spiegato = "GNOME (c'e' gnome-session)";
		} else if (xfce) {
			/* ⭐ FASE 13.  Il marcatore è `xfce4-session`, non `labwc`: vedi
			 *    `sessione.h`.  `labwc` è una PRECONDIZIONE, e la sua assenza
			 *    si dice subito invece di farla scoprire a un `exec` fallito. */
			desktop_scelto = SESSIONE_DESKTOP_XFCE;
			desktop_spiegato =
				labwc ? "XFCE (c'e' xfce4-session, e labwc per farlo girare)"
				      : "XFCE (c'e' xfce4-session) — ⛔ ma NON c'e' labwc, e XFCE "
				        "su Wayland non porta un compositore suo: la sessione non "
				        "potra' nascere finche' non lo si installa";
			/* ⭐ FASE 14 — XFCE e LXQt insieme: AMBIGUO, come GNOME+KDE.  Si
			 *    sceglie XFCE, cioe' quel che la macchina faceva ieri, e si DICE:
			 *    la scelta cambia solo la spiegazione, mai il desktop. */
			if (lxqt)
				desktop_spiegato =
					"XFCE — ⚠ AMBIGUO: su questa macchina ci sono XFCE e LXQt "
					"(xfce4-session e lxqt-session), e vince XFCE.  La scelta fra "
					"piu' desktop non c'e' ancora (DECISIONI.md "
					"§4.6-duodetricies, MASTERPLAN.md M5)";
		} else if (lxqt) {
			/* ⭐ FASE 14.  Stessa disciplina di XFCE: il marcatore è la
			 *    SESSIONE, `labwc` la precondizione, detta subito. */
			desktop_scelto = SESSIONE_DESKTOP_LXQT;
			desktop_spiegato =
				labwc ? "LXQt (c'e' lxqt-session, e labwc per farlo girare)"
				      : "LXQt (c'e' lxqt-session) — ⛔ ma NON c'e' labwc, e LXQt "
				        "su Wayland non porta un compositore suo: la sessione non "
				        "potra' nascere finche' non lo si installa";
		} else {
			/*
			 * ⛔⛔ QUI C'ERA IL RIPIEGO SU GNOME, ed è stato TOLTO — fase 13,
			 *     incremento 1.  La ragione per esteso sta in `sessione.h`,
			 *     sul quarto valore dell'enum; in una riga: dichiararsi GNOME
			 *     su una macchina che GNOME non ce l'ha faceva accusare due
			 *     innocenti — un drop-in altrui e Mutter — mentre la causa
			 *     vera era scritta una volta sola, dove nessuno la leggeva.
			 * ⚠ È un cambiamento di comportamento, ed è voluto: su una
			 *   macchina senza desktop prima si provava e si falliva male,
			 *   adesso non si prova e si dice perche'.
			 */
			desktop_scelto = SESSIONE_DESKTOP_NESSUNO;
			desktop_spiegato = "⛔ NESSUN DESKTOP RICONOSCIUTO — non trovo "
			                   "gnome-session, ne' startplasma-wayland, ne' "
			                   "xfce4-session, ne' lxqt-session: nessuna sessione "
			                   "grafica potra' "
			                   "nascere, e non ne provo nessuna";
		}
		g_once_init_leave(&fatto, 1);
	}
}

SessioneDesktop sessione_desktop(void)
{
	riconosci_desktop();
	return desktop_scelto;
}

const char *sessione_desktop_spiega(void)
{
	riconosci_desktop();
	return desktop_spiegato;
}

static gboolean e_kde(void)
{
	return sessione_desktop() == SESSIONE_DESKTOP_KDE;
}

/*
 * ⛔⛔ PERCHE' TRE PREDICATI E NON UN `!e_kde()` — fase 13.
 *
 * In questo file non esiste nemmeno un `!e_kde()` scritto per esteso: la
 * negazione è sempre un `else` o una **caduta in fondo** — sette punti, e li
 * si legge come «GNOME».  ⚠ Aggiungere un terzo valore all'enum li trasforma
 * TUTTI INSIEME in «GNOME **o** XFCE», e il compilatore non dice niente.
 *
 * ⇒ Percio' ogni punto guadagna un `if (e_xfce())` **davanti** al blocco di
 *   GNOME, che resta testualmente quello di prima e torna con `goto`/`return`.
 *   Chi aggiunge il quarto desktop rifaccia lo stesso giro: la lista dei punti
 *   sta in `fasi/13-xfce.md`, incremento 1.
 */
/*
 * Il nodo di rendering da dare a wlroots — ⛔ CERCATO, non inchiodato.
 *
 * ⚠ `renderD128` e `renderD129` si scambiano fra due avvii (`provisiona.sh`
 *   §5), e sulla macchina vera il secondo nodo è una scheda **esclusa apposta**.
 *   ⇒ Si prende il primo `renderD*` che si riesce ad APRIRE: aprire è la
 *     domanda giusta, perche' è esattamente quel che farà wlroots.
 *
 * ⛔⛔ E questo non è zelo: se l'apertura fallisce, wlroots **non dice niente**
 *     e ripiega su pixman, cioe' sul software.  Il sintomo per l'utente è «è
 *     lento», e nessuna riga lo spiega — la stessa forma del codificatore che
 *     ripiegava in software, con l'aggravante che lì almeno lo dichiarava.
 *
 * Torna NULL se non ce n'è nessuno: chi chiama lo dice nel registro.
 */
static char *nodo_della_scheda(void)
{
	g_autoptr(GDir) dri = g_dir_open("/dev/dri", 0, NULL);
	const char *voce;
	g_autofree char *primo = NULL;

	if (!dri)
		return NULL;
	while ((voce = g_dir_read_name(dri))) {
		g_autofree char *percorso = NULL;
		int fd;

		if (!g_str_has_prefix(voce, "renderD"))
			continue;
		percorso = g_build_filename("/dev/dri", voce, NULL);
		fd = g_open(percorso, O_RDWR | O_CLOEXEC, 0);
		if (fd < 0)
			continue;
		g_close(fd, NULL);
		/* ⚠ Il primo in ordine di nome, per avere una risposta STABILE fra due
		 *   avvii invece di quella che l'ordine del filesystem regala. */
		if (!primo || g_strcmp0(voce, primo) < 0) {
			g_free(primo);
			primo = g_strdup(voce);
		}
	}
	return primo ? g_build_filename("/dev/dri", primo, NULL) : NULL;
}

static gboolean e_xfce(void)
{
	return sessione_desktop() == SESSIONE_DESKTOP_XFCE;
}

static gboolean e_nessuno(void)
{
	return sessione_desktop() == SESSIONE_DESKTOP_NESSUNO;
}

/*
 * ⭐ FASE 14 — il quarto predicato, e il giro del riquadro «PERCHE' TRE
 *    PREDICATI» rifatto: ogni punto che aveva un `if (e_xfce())` davanti al
 *    blocco di GNOME ha adesso anche un ramo LXQt ESPLICITO — fuso con quello
 *    di XFCE dove il fatto è di labwc (famiglia), separato dove è della
 *    sessione.  ⛔ Nessun punto lascia cadere LXQt nel blocco di GNOME.
 */
static gboolean e_lxqt(void)
{
	return sessione_desktop() == SESSIONE_DESKTOP_LXQT;
}

bool sessione_su_wlroots(void)
{
	return e_xfce() || e_lxqt();
}

/*
 * Il nome corto del desktop, per le righe di registro che ne nominavano UNO.
 *
 * ⚠ `LEZIONI.md` §1.9, quinta regola: *una riga scritta quando esisteva un solo
 *   chiamante diventa falsa al secondo, e nessun compilatore lo dice*.  `[M]` 20
 *   set 2026, prima prova di XFCE: il tema del cursore — scritto per KWin e
 *   riusato da labwc — annunciava «⭐ **Plasma**: tema remotix-invisibile» dentro
 *   una sessione XFCE.  ⇒ La riga non si duplica: si fa dire il nome giusto.
 */
static const char *nome_desktop(void)
{
	switch (sessione_desktop()) {
	case SESSIONE_DESKTOP_KDE:
		return "Plasma";
	case SESSIONE_DESKTOP_XFCE:
		return "XFCE";
	case SESSIONE_DESKTOP_LXQT:
		return "LXQt";
	case SESSIONE_DESKTOP_NESSUNO:
		return "nessun desktop";
	default:
		return "GNOME";
	}
}

/*
 * Quanti processi di QUESTO utente si chiamano cosi'.
 *
 * ⛔ Serve perche' su XFCE il compositore non è un'unita' systemd: la domanda
 *    «la sessione di prima è finita?» non si puo' fare a systemd, e la risposta
 *    che systemd darebbe — `inactive` per un'unita' che non esiste — sarebbe
 *    un **sì** (`[M]` 20 set 2026, dentro `rete11-xfce`: codice 4, «inactive»).
 *    ⇒ La guardia non fallirebbe: sparirebbe.  Qui si guarda un fatto.
 * ⚠ Si legge `/proc` invece di chiamare `pgrep`: un attrezzo in meno da avere
 *   installato, e nessuna riga di comando da citare male.
 */
static int processi_miei(const char *nome)
{
	g_autoptr(GDir) proc = g_dir_open("/proc", 0, NULL);
	const char *voce;
	uid_t mio = getuid();
	int quanti = 0;

	if (!proc)
		return -1;
	while ((voce = g_dir_read_name(proc))) {
		g_autofree char *comm = NULL;
		g_autofree char *percorso = NULL;
		GStatBuf st;

		if (!g_ascii_isdigit(voce[0]))
			continue;
		percorso = g_build_filename("/proc", voce, "comm", NULL);
		if (g_stat(percorso, &st) != 0 || st.st_uid != mio)
			continue;
		if (!g_file_get_contents(percorso, &comm, NULL, NULL))
			continue;
		g_strstrip(comm);
		if (g_strcmp0(comm, nome) == 0)
			quanti++;
	}
	return quanti;
}

bool sessione_viva(void)
{
	g_autoptr(GDBusConnection) bus = NULL;
	g_autoptr(GVariant) risposta = NULL;

	bus = sessione_bus(NULL);
	if (!bus)
		return false;

	/* ⭐ Su Plasma la domanda debole e' il nome di KWin: non e' attivabile (lo
	 *    prende il compositore quando parte), e la debolezza e' la stessa
	 *    dichiarata in `sessione.h` — «viva» non vuol dire «pronta». */
	if (e_kde())
		return nome_ha_padrone(bus, "org.kde.KWin");

	/* ⭐ FASE 13 — su XFCE la domanda debole è il nome del gestore di sessione.
	 *    `[M]` 20 set 2026: compare sul bus D'UTENTE, perche' `labwc` lo
	 *    avviamo noi senza `dbus-run-session` — cioe' proprio il bus che
	 *    `sessione_bus()` già apre.  ⚠ E la debolezza è la stessa dichiarata per
	 *    gli altri due, con un margine piu' largo: fra il nome e la sessione
	 *    USABILE ci sono fino a 8 s per gruppo di priorità, e sono strutturali
	 *    (`STARTUP_TIMEOUT_WAYLAND`, `STUDI.md` §xfce §9.4). */
	if (e_xfce())
		return nome_ha_padrone(bus, SESSIONE_BUS_XFCE);

	/* ⭐ FASE 14 — su LXQt, la stessa domanda debole: il nome di `lxqt-session`
	 *    sul bus d'utente (labwc parte senza `dbus-run-session`, come su XFCE).
	 * ⚠ E la debolezza è dichiarata a monte (`STUDI.md` §lxqt §3.4): il nome
	 *   compare nel COSTRUTTORE, prima dei moduli.  La prontezza vera sarebbe
	 *   il segnale `moduleStateChanged("lxqt-panel.desktop", true)`, ma il figlio
	 *   non ha un ciclo GLib per ascoltarlo.  [?] Da misurare sulla scatola:
	 *   quanto passa fra il nome e il pannello, e se in quel mezzo la cattura
	 *   su labwc fallisce e riprova (come su XFCE) o fa altro. */
	if (e_lxqt())
		return nome_ha_padrone(bus, SESSIONE_BUS_LXQT);

	/*
	 * ⛔ NON BASTA CHE IL NOME SIA OCCUPATO, per due ragioni diverse e tutte e
	 *    due pagate: il nome di Mutter e' ATTIVABILE e chiederlo lo fa nascere;
	 *    e `org.gnome.Shell` la Shell **lo prende prima di
	 *    `meta_context_start()`** (`STUDI.md` §gnome §3.2), quindi non e' un indicatore
	 *    di prontezza.  Si chiama un metodo vero e si guarda che la risposta
	 *    ARRIVI — senza interpretarla: qui interessa una cosa sola.
	 */
	risposta = chiedi_a_mutter(bus, "org.gnome.Mutter.DisplayConfig",
	                           "/org/gnome/Mutter/DisplayConfig",
	                           "org.gnome.Mutter.DisplayConfig", "GetCurrentState", NULL);
	return risposta != NULL;
}

/* ------------------------------------------------------------------------- */
static void copia_in(char *dove, gsize quanto, const char *cosa)
{
	g_strlcpy(dove, cosa ? cosa : "", quanto);
}

/*
 * Dalla risposta di `GetCurrentState` a uno dei sei numeri.
 *
 * ⛔ E i tre esiti sono TRE, non due (`REVIEWER.md` §1 punto 4): «un monitor»,
 *    «zero monitor» e «non ho potuto guardare» — e il terzo non si travestera'
 *    mai da secondo.
 */
static SessioneStato leggi_monitor(GVariant *risposta, uint32_t larghezza, uint32_t altezza,
                                   SessioneMonitor *scelto)
{
	g_autoptr(GVariant) monitor = NULL;
	g_autoptr(GVariant) proprieta = NULL;
	g_autoptr(GVariant) layout = NULL;
	gsize quanti, i;
	SessioneStato verdetto;

	/* ⛔ Il primo controllo e' sulla FORMA, e il suo esito e' 5. */
	if (!g_variant_is_of_type(risposta, G_VARIANT_TYPE(TIPO_STATO))) {
		registro_dice(REG_SESSIONE,
		              "⛔ GetCurrentState ha risposto con una forma che non so "
		              "leggere («%s» invece di «%s»): e' rotto il PARSER, non la "
		              "sessione — e questo non e' «zero monitor» (E8)",
		              g_variant_get_type_string(risposta), TIPO_STATO);
		return SESSIONE_NON_LETTA;
	}

	monitor = g_variant_get_child_value(risposta, 1);
	proprieta = g_variant_get_child_value(risposta, 3);

	/*
	 * ⭐ IL CONTROLLO POSITIVO — «questo lettore sa trovare qualcosa che c'e' di
	 *    sicuro?» (`CODER.md` §3.10).  `layout-mode` sta sempre fra le proprieta'
	 *    di `GetCurrentState`; se non lo trovo, quel che e' rotto e' la mia
	 *    lettura, e allora non ho il diritto di dire «zero monitor».
	 *
	 * ⚠ Si guarda che ci SIA, non che valga qualcosa: il tipo di quel campo non
	 *   e' affar nostro, e legarcisi sarebbe rifare l'errore di sopra in piccolo.
	 */
	layout = g_variant_lookup_value(proprieta, "layout-mode", NULL);
	if (!layout) {
		registro_dice(REG_SESSIONE,
		              "⛔ nella risposta di GetCurrentState non c'e' «layout-mode», "
		              "che c'e' sempre: non ho letto bene, e non dico «zero monitor»");
		return SESSIONE_NON_LETTA;
	}

	quanti = g_variant_n_children(monitor);
	if (scelto) {
		memset(scelto, 0, sizeof *scelto);
		scelto->quanti = (unsigned) quanti;
	}

	if (quanti == 0) {
		registro_dice(REG_SESSIONE,
		              "⛔ ZERO MONITOR, e la sessione e' viva: e' la sessione «viva, "
		              "completa e NERA» di STUDI.md §gnome §3.1 — non c'e' niente da catturare");
		return SESSIONE_NERA;
	}

	/*
	 * ⛔ E se sono piu' d'uno, si NOMINANO TUTTI.
	 *
	 * Il 12 agosto 2026 il banco stampo' «2 monitor: ne era stato chiesto uno
	 * solo» senza nominarli, e il nome — l'unica cosa che li distingueva, visto
	 * che la misura era identica — lo salvo' solo la riga di registro.  Qui il
	 * registro e' l'unico posto che c'e': se non li nomina, non li nomina
	 * nessuno.
	 */
	verdetto = (quanti == 1) ? SESSIONE_SANA : SESSIONE_SCELTO_DA_SE;
	if (quanti > 1)
		registro_dice(REG_SESSIONE,
		              "⛔ %zu monitor, e ne era stato chiesto UNO: li elenco tutti, "
		              "perche' sulla misura possono essere identici (E2)",
		              quanti);

	for (i = 0; i < quanti; i++) {
		g_autoptr(GVariant) m = g_variant_get_child_value(monitor, i);
		g_autoptr(GVariant) nomi = g_variant_get_child_value(m, 0);
		g_autoptr(GVariant) modi = g_variant_get_child_value(m, 1);
		const char *connettore = NULL, *fornitore = NULL, *prodotto = NULL, *seriale = NULL;
		gsize quanti_modi, k;
		gboolean trovato_modo = FALSE;
		gint32 ml = 0, ma = 0;
		gdouble refresh = 0;

		g_variant_get(nomi, "(&s&s&s&s)", &connettore, &fornitore, &prodotto, &seriale);

		quanti_modi = g_variant_n_children(modi);
		for (k = 0; k < quanti_modi; k++) {
			g_autoptr(GVariant) modo = g_variant_get_child_value(modi, k);
			g_autoptr(GVariant) mprop = g_variant_get_child_value(modo, 6);
			gboolean corrente = FALSE;

			if (!g_variant_lookup(mprop, "is-current", "b", &corrente) || !corrente)
				continue;
			g_variant_get_child(modo, 1, "i", &ml);
			g_variant_get_child(modo, 2, "i", &ma);
			g_variant_get_child(modo, 3, "d", &refresh);
			trovato_modo = TRUE;
			break;
		}

		registro_dice(REG_SESSIONE,
		              "monitor %zu/%zu: connettore «%s» fornitore «%s» prodotto «%s» "
		              "seriale «%s» modo %s%dx%d@%.3f",
		              i + 1, quanti, connettore, fornitore, prodotto, seriale,
		              trovato_modo ? "" : "(nessuno in uso) ", ml, ma, refresh);

		if (i == 0 && scelto) {
			copia_in(scelto->connettore, sizeof scelto->connettore, connettore);
			copia_in(scelto->fornitore, sizeof scelto->fornitore, fornitore);
			copia_in(scelto->prodotto, sizeof scelto->prodotto, prodotto);
			copia_in(scelto->seriale, sizeof scelto->seriale, seriale);
			scelto->larghezza = (uint32_t) ml;
			scelto->altezza = (uint32_t) ma;
			scelto->refresh = refresh;
		}

		if (verdetto != SESSIONE_SANA)
			continue;

		/*
		 * ⛔ IL NOME PRIMA DELLA MISURA, e l'ordine e' la lezione del 12 agosto:
		 *    i due monitor virtuali visti insieme erano **entrambi
		 *    1920x1080@60**, e chi avesse guardato la risoluzione non avrebbe
		 *    distinto niente.
		 */
		if (g_strcmp0(prodotto, SESSIONE_PRODOTTO_CHIESTO) != 0) {
			registro_dice(REG_SESSIONE,
			              "⛔ il monitor si chiama «%s» e non «%s»: non e' quello "
			              "che ho chiesto io — se lo e' scelto qualcun altro (E2)",
			              prodotto, SESSIONE_PRODOTTO_CHIESTO);
			verdetto = SESSIONE_SCELTO_DA_SE;
		} else if (!trovato_modo) {
			registro_dice(REG_SESSIONE,
			              "⛔ «%s» non ha nessun modo IN USO: c'e' un monitor e non "
			              "ha misura, quindi non ha la misura chiesta",
			              connettore);
			verdetto = SESSIONE_MISURA_ALTRA;
		} else if ((uint32_t) ml != larghezza || (uint32_t) ma != altezza) {
			registro_dice(REG_SESSIONE,
			              "⛔ il monitor e' %dx%d e ne avevo chiesto uno %ux%u",
			              ml, ma, larghezza, altezza);
			verdetto = SESSIONE_MISURA_ALTRA;
		}
	}

	if (verdetto == SESSIONE_SANA)
		registro_dice(REG_SESSIONE, "⭐ un monitor «%s» «%s», %ux%u: c'e' che cosa catturare",
		              scelto ? scelto->connettore : "?", SESSIONE_PRODOTTO_CHIESTO, larghezza,
		              altezza);
	return verdetto;
}

SessioneStato sessione_stato(uint32_t larghezza, uint32_t altezza, SessioneMonitor *scelto)
{
	g_autoptr(GDBusConnection) bus = NULL;
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GError) sbaglio = NULL;

	if (scelto)
		memset(scelto, 0, sizeof *scelto);

	bus = sessione_bus(&sbaglio);
	if (!bus) {
		registro_dice(REG_SESSIONE,
		              "⛔ non ho nemmeno il bus di sessione (%s): non e' «non c'e' "
		              "la sessione», e' «non ho potuto guardare»",
		              sbaglio ? sbaglio->message : "senza motivo");
		return SESSIONE_NON_LETTA;
	}

	/*
	 * ⭐ FASE 12 — su Plasma.  KWin col backend `--virtual` nasce con
	 *    **un'uscita sola, della misura scritta nel drop-in** (`STUDI.md` §kde
	 *    §5.2; `[M]` 18 set 2026: `Virtual-0` 1600x900, una sola `wl_output`) —
	 *    e `scrivi_dropin()` ha gia' riletto quella riga IN VIGORE prima della
	 *    nascita.  ⇒ Nome presente = SANA.
	 * ⚠ E si dichiara quel che NON si guarda: l'uscita non la rileggo dal
	 *   compositore (serve un cliente Wayland, e arriva con la cattura).
	 */
	if (e_kde()) {
		if (!nome_ha_padrone(bus, "org.kde.KWin")) {
			registro_dice(REG_SESSIONE,
			              "nessun KWin sul bus: la sessione Plasma non c'e'");
			return SESSIONE_MORTA;
		}
		registro_dettaglio(REG_SESSIONE,
		                   "KWin c'e' sul bus: la sessione Plasma e' viva, con l'uscita "
		                   "del drop-in (verificato alla nascita, non riletto qui)");
		return SESSIONE_SANA;
	}

	/*
	 * ⭐ FASE 13 — su XFCE, stessa disciplina di KDE e una dichiarazione in piu'.
	 *
	 * ⛔ Qui l'uscita NON è della misura chiesta, e non lo sarà alla nascita:
	 *    `[M]` 20 set 2026 nasce `HEADLESS-1 1280x720` cablata, e la misura si
	 *    dà dopo col protocollo (`zwlr_output_manager_v1`).  ⇒ «sana» qui vuol
	 *    dire «c'è», non «della misura giusta», e chi legge deve saperlo.
	 */
	if (e_xfce()) {
		if (!nome_ha_padrone(bus, SESSIONE_BUS_XFCE)) {
			registro_dice(REG_SESSIONE,
			              "nessun " SESSIONE_BUS_XFCE " sul bus: la sessione XFCE "
			              "non c'e'");
			return SESSIONE_MORTA;
		}
		registro_dettaglio(REG_SESSIONE,
		                   "il gestore di sessione XFCE c'e' sul bus: la sessione e' "
		                   "viva — ⚠ e la sua uscita NON è della misura chiesta: su "
		                   "wlroots nasce cablata e si ridimensiona dopo");
		return SESSIONE_SANA;
	}

	/* ⭐ FASE 14 — su LXQt, la disciplina di XFCE parola per parola: stesso
	 *    compositore, stessa uscita cablata; cambia solo il nome sul bus.
	 * ⚠ «Sana» qui vuol dire «lxqt-session c'è», e il nome precede i moduli
	 *   (vedi `sessione_viva()`).  [?] Se la scatola mostra che la cattura
	 *   parte troppo presto, la domanda giusta è `listModules()` o il segnale
	 *   del pannello — non un'attesa a tempo. */
	if (e_lxqt()) {
		if (!nome_ha_padrone(bus, SESSIONE_BUS_LXQT)) {
			registro_dice(REG_SESSIONE,
			              "nessun " SESSIONE_BUS_LXQT " sul bus: la sessione LXQt "
			              "non c'e'");
			return SESSIONE_MORTA;
		}
		registro_dettaglio(REG_SESSIONE,
		                   "lxqt-session c'e' sul bus: la sessione e' viva — ⚠ e la "
		                   "sua uscita NON è della misura chiesta: su wlroots nasce "
		                   "cablata e si ridimensiona dopo");
		return SESSIONE_SANA;
	}

	risposta = chiedi_a_mutter(bus, "org.gnome.Mutter.DisplayConfig",
	                           "/org/gnome/Mutter/DisplayConfig",
	                           "org.gnome.Mutter.DisplayConfig", "GetCurrentState", &sbaglio);
	if (!risposta) {
		/*
		 * ⛔ E QUI I DUE CASI SI SEPARANO, che e' tutto il punto.
		 *
		 *   nessuno serve quel nome        → la sessione non c'e'      (4)
		 *   qualunque altro errore         → non ho potuto guardare    (5)
		 *
		 * Metterli insieme vorrebbe dire dare per morta una sessione che c'e'
		 * ma non risponde a NOI — un permesso negato, un bus saturo — ed e' la
		 * forma d'errore E8 nel punto in cui costa di piu'.
		 */
		if (g_error_matches(sbaglio, G_DBUS_ERROR, G_DBUS_ERROR_SERVICE_UNKNOWN) ||
		    g_error_matches(sbaglio, G_DBUS_ERROR, G_DBUS_ERROR_NAME_HAS_NO_OWNER)) {
			registro_dice(REG_SESSIONE, "nessun compositore sul bus: la sessione non c'e'");
			return SESSIONE_MORTA;
		}
		registro_dice(REG_SESSIONE,
		              "⛔ GetCurrentState non ha risposto (%s): non ho potuto guardare, "
		              "e questo NON e' «la sessione non c'e'»",
		              sbaglio ? sbaglio->message : "senza motivo");
		return SESSIONE_NON_LETTA;
	}

	return leggi_monitor(risposta, larghezza, altezza, scelto);
}

/* ------------------------------------------------------------------------- */
/*
 * Una locale UTF-8, sempre — ed e' la trappola trovata dall'utente il 7 agosto
 * 2026 con la frase «il terminale non funziona».
 *
 * `gnome-terminal-server` si rifiuta di partire con una locale non UTF-8
 * («Non UTF-8 locale (ANSI_X3.4-1968) is not supported!», uscita 8), e l'utente
 * si ritrova un desktop in cui i programmi non si aprono, senza un errore da
 * nessuna parte.
 *
 * ⛔ E NON BASTA CHE IL NOME DICA UTF-8: QUELLA LOCALE DEVE ESISTERE.  Il server
 *    porta `LANG=it_IT.UTF-8`, che di nome e' UTF-8; sul ferro le locale
 *    GENERATE sono due — `C` e `C.utf8` — e glibc ripiega in silenzio sulla `C`,
 *    che UTF-8 non e'.  Il rootfs vive in RAM, quindi «basta generarla una
 *    volta» non basta: si verifica a ogni avvio, e lo chiede alla LIBRERIA
 *    invece che al nome.
 */
static gboolean locale_esiste(const char *nome)
{
	locale_t prova = newlocale(LC_ALL_MASK, nome, (locale_t) 0);

	if (!prova)
		return FALSE;
	freelocale(prova);
	return TRUE;
}

static const char *locale_utf8(void)
{
	/* Debian genera `C.utf8`; glibc accetta anche la forma col trattino, ma non
	 * su tutte le versioni: si provano tutt'e due invece di scommettere. */
	static const char *RIPIEGHI[] = { "C.UTF-8", "C.utf8" };
	const char *lingua = g_getenv("LANG");
	gsize i;

	if (lingua && *lingua) {
		g_autofree char *maiuscolo = g_ascii_strup(lingua, -1);

		if (strstr(maiuscolo, "UTF-8") || strstr(maiuscolo, "UTF8")) {
			if (locale_esiste(lingua))
				return lingua;
			registro_dice(REG_SESSIONE,
			              "⚠ la locale «%s» e' UTF-8 di nome ma NON e' generata su "
			              "questa macchina: senza ripiego i programmi della sessione "
			              "non si aprirebbero",
			              lingua);
		} else {
			registro_dice(REG_SESSIONE, "⚠ la locale dell'ambiente («%s») non e' UTF-8",
			              lingua);
		}
	}

	for (i = 0; i < G_N_ELEMENTS(RIPIEGHI); i++)
		if (locale_esiste(RIPIEGHI[i])) {
			registro_dice(REG_SESSIONE,
			              "ripiego dichiarato: la sessione partira' con la locale «%s»",
			              RIPIEGHI[i]);
			return RIPIEGHI[i];
		}

	/* Nessuna locale UTF-8 sulla macchina: si dichiara, perche' da qui in poi il
	 * terminale non partira' e nessun altro lo spieghera'. */
	registro_dice(REG_SESSIONE,
	              "⛔ nessuna locale UTF-8 su questa macchina: il terminale della "
	              "sessione non partira' (si genera con «locale-gen C.UTF-8»)");
	return "C.UTF-8";
}

/*
 * ⭐⭐ FASE 12 — LA CURA DEL DOPPIO PUNTATORE: IL CURSORE DI KDE DIVENTA
 *      TRASPARENTE.  ⛔ Riportata da v1 (`fondamenta/remotix-c/src/sessione.c`,
 *      `scrivi_tema_cursore` + `scrivi_cursore_vuoto`), misurata l'8 agosto
 *      2026 (`STUDI.md` §kde) e rimasta fuori dal passaggio a v2: `[M]` 19 set
 *      2026, la prova dell'utente — «la coda del puntatore».
 *
 * ⛔ IL FATTO: con il backend `--virtual` KWin disegna il cursore DENTRO
 *    l'immagine catturata, e non c'e' leva per impedirglielo.  ⇒ Chi guarda ne
 *    vede DUE: quello del browser, immediato, e quello del desktop, che arriva
 *    col video e insegue — la «coda».
 * ⭐ E la cura non e' impedirglielo: basta che quel che disegna NON SI VEDA.
 *    KWin legge `XCURSOR_THEME` **solo se c'e' anche `XCURSOR_SIZE`**
 *    (`cursor.cpp:134-145`), e l'ambiente della sessione lo componiamo noi.
 * ⚠ IL TEMA DEVE CARICARSI DAVVERO: se il tema risulta vuoto KWin ripiega su
 *   quello predefinito (`pointer_input.cpp:1183-1196`), cioe' RIMETTE il
 *   cursore visibile.  Per questo le forme si scrivono tutte, non solo
 *   `left_ptr`, e niente `Inherits=` nell'indice.
 * ⚠ E il prezzo, com'era fino al 24 set 2026: si perdeva il CAMBIO di forma
 *   (la I sul testo, le frecce di ridimensionamento) — ⭐ curato qui sotto.
 */
/*
 * ⭐⭐ FASE 14 — E IL TEMA NON E' PIU' INVISIBILE: E' CODIFICATO (24 set 2026,
 *      decisione dell'utente: la forma vera del puntatore su tutti e quattro i
 *      desktop).  Ogni forma e' ancora un'immagine 1x1, ma OPACA e di un colore
 *      solo suo: il colore torna nel metadato e dice QUALE forma l'applicazione
 *      ha chiesto.  ⛔ Il tema lo scrive `forma.c`, che tiene anche il
 *      dizionario colore ⇒ forma: le due meta' non devono poter divergere.
 * ⚠ Il NOME resta `remotix-invisibile`: e' quello che l'ambiente qui sotto
 *   dichiara da sempre, e cambiarlo non cura niente.
 */
#define TEMA_CURSORE FORMA_TEMA

/* Torna la cartella da mettere in `XCURSOR_PATH`, o NULL (detto nel registro). */
static char *scrivi_tema_cursore(const char *runtime)
{
	if (!forma_tema_scrivi(runtime)) {
		registro_dice(REG_SESSIONE,
		              "⚠ %s: tema del cursore NON scritto: il compositore ripieghera' "
		              "sul tema visibile, e chi guardera' vedra' DUE puntatori",
		              nome_desktop());
		return NULL;
	}
	registro_dice(REG_SESSIONE,
	              "⭐ %s: tema «%s» codificato — il cursore del compositore e' un pixel, "
	              "e la sua forma vera la disegna chi guarda",
	              nome_desktop(), TEMA_CURSORE);
	return g_build_filename(runtime, "remotix", "icons", NULL);
}

/*
 * ⭐ FASE 12 — «BLOCCA» E «CAMBIA UTENTE» TOLTI DAL MENU DI PLASMA.
 *
 * ⛔ Riportato da v1 (`fondamenta/remotix-c/src/sessione.c`,
 *    `scrivi_regole_menu`), chiesto dall'utente l'8 agosto 2026 e rimasto
 *    fuori dal passaggio a v2: `[M]` 19 set 2026, la prova dell'utente su KDE,
 *    le due voci c'erano.  In una sessione servita da REMOTIX non funzionano, ed
 *    e' GIUSTO: il blocco e' nostro (`DECISIONI.md` §4.3, e KWin parte con
 *    `--no-lockscreen`), e cambiare utente vorrebbe un display manager che qui
 *    non c'e'.  ⛔ Ma una voce che non fa niente e' peggio di una che manca.
 *
 * La leva e' KIOSK (`KAuthorized`), coi nomi che Plasma interroga davvero:
 *   `SessionManagement::canLock()`       → `lock_screen`
 *   `SessionManagement::canSwitchUser()` → `start_new_session`
 *   `SessionsModel::canSwitchUser()`     → `switch_user`
 * ⚠ `switch_user` e `start_new_session` servono tutti e due (l'elenco e il
 *   pulsante), e `[$i]` impedisce al `kdeglobals` dell'utente di rimetterle.
 * ⛔ `logout` NON si tocca: e' l'unica porta per chiudere la sessione (§4.1-ter).
 * ⭐ Sotto `XDG_RUNTIME_DIR` e non in `~/.config`: vale per la sessione che
 *    serviamo, sparisce con lei, e non tocca la configurazione dell'utente ne'
 *    chi siede davanti alla macchina.
 *
 * Torna la cartella da mettere in `XDG_CONFIG_DIRS`, o NULL (detto nel registro).
 */
char *sessione_cartella_kde(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (!runtime || !*runtime)
		return NULL;
	return g_build_filename(runtime, "remotix", "xdg", NULL);
}

static char *scrivi_regole_menu_kde(const char *runtime)
{
	g_autofree char *cartella = g_build_filename(runtime, "remotix", "xdg", NULL);
	g_autofree char *percorso = g_build_filename(cartella, "kdeglobals", NULL);
	g_autoptr(GError) sbaglio = NULL;

	if (g_mkdir_with_parents(cartella, 0700) != 0 ||
	    !g_file_set_contents(percorso,
	                         "[KDE Action Restrictions][$i]\n"
	                         "action/lock_screen=false\n"
	                         "action/start_new_session=false\n"
	                         "action/switch_user=false\n",
	                         -1, &sbaglio)) {
		registro_dice(REG_SESSIONE,
		              "⚠ Plasma: regole del menu NON scritte in %s (%s): «Blocca» e "
		              "«Cambia utente» resteranno nel menu",
		              cartella, sbaglio ? sbaglio->message : g_strerror(errno));
		return NULL;
	}
	registro_dice(REG_SESSIONE,
	              "⭐ Plasma: regole del menu in %s — niente «Blocca», niente «Cambia "
	              "utente» (KIOSK); «Esci» resta",
	              percorso);

	/*
	 * ⭐ E NELLA STESSA CARTELLA, IL BORDO DELLE FINESTRE — 20 set 2026, la
	 *    prova dell'utente: «in KDE non si riescono a ridimensionare le
	 *    finestre».  `[M]` Plasma nasce con `BorderSizeAuto`, che con Breeze
	 *    vuol dire bordi laterali di pochi pixel: al monitor si prendono perche'
	 *    il cursore cambia forma, ⛔ in una sessione remota no — il cursore del
	 *    desktop e' invisibile apposta (vedi sopra), quindi il bordo non si
	 *    annuncia e non si aggancia.
	 * ⚠ E si scrive SENZA `[$i]`, al contrario delle regole del menu: e' un
	 *   PUNTO DI PARTENZA, non un divieto — il `kwinrc` dell'utente sta piu' in
	 *   alto e vince, cioe' da Impostazioni di sistema si cambia e resta.
	 */
	g_autofree char *kwinrc = g_build_filename(cartella, "kwinrc", NULL);

	if (g_file_set_contents(kwinrc,
	                        "[org.kde.kdecoration2]\n"
	                        "BorderSize=Normal\n"
	                        "BorderSizeAuto=false\n",
	                        -1, NULL))
		registro_dice(REG_SESSIONE,
		              "⭐ Plasma: bordo delle finestre «Normal» come partenza (%s): in "
		              "una sessione remota il bordo va AGGANCIATO, e quello automatico "
		              "di Breeze e' troppo sottile.  ⚠ L'utente lo puo' cambiare",
		              kwinrc);
	else
		registro_dice(REG_SESSIONE,
		              "⚠ Plasma: bordo delle finestre non scritto (%s): resta quello "
		              "automatico, e ridimensionare col mouse sara' difficile",
		              kwinrc);

	/*
	 * ⭐ FASE 15, D-005 — E LA SESSIONE NASCE VUOTA.  `[M]` giro 1, 15-f021 su
	 *    KDE 4 volte su 4: dopo «Esci» il nuovo accesso riapriva il programma
	 *    che era aperto.  ⛔ Non e' nostro: e' il ripristino di Plasma 6.3,
	 *    `plasma-fallback-session-save` all'uscita e
	 *    `plasma-fallback-session-restore` (autostart) all'entrata.
	 * `[R]` plasma-workspace 6.3.6: tutt'e due leggono `ksmserverrc`
	 *    `[General] loginMode` — `restore.cpp:30-33` esce subito con
	 *    `emptySession`; `shutdown.cpp:87` salva solo con
	 *    `restorePreviousLogout`; `ksmserver/main.cpp:187` (le finestre X11)
	 *    idem.  ⇒ Una chiave sola ferma le tre strade, ⭐ e all'uscita non si
	 *    salva nemmeno: la sessione remota non sovrascrive quella che
	 *    l'utente ha salvato al monitor.
	 * ⚠ SENZA `[$i]`, come il bordo: e' la partenza.  Un `loginMode` scritto
	 *   dall'utente in `~/.config/ksmserverrc` (Impostazioni → Sessione
	 *   desktop, «ripristina sessione salvata a mano») sta piu' in alto e vince.
	 *   `[R]` il valore predefinito non si scrive (KConfigSkeleton), quindi
	 *   chi non ha mai toccato quella voce prende il nostro.
	 */
	g_autofree char *ksmserverrc = g_build_filename(cartella, "ksmserverrc", NULL);

	if (g_file_set_contents(ksmserverrc,
	                        "[General]\n"
	                        "loginMode=emptySession\n",
	                        -1, NULL))
		registro_dice(REG_SESSIONE,
		              "⭐ Plasma: la sessione nasce VUOTA (%s, loginMode=emptySession): "
		              "dopo «Esci» chi rientra non si ritrova i programmi di prima",
		              ksmserverrc);
	else
		registro_dice(REG_SESSIONE,
		              "⚠ Plasma: loginMode non scritto (%s): Plasma riaprira' i "
		              "programmi della sessione precedente",
		              ksmserverrc);
	return g_steal_pointer(&cartella);
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ FASE 15, D-015 — IL DCONF DELLA SESSIONE: LE IMPOSTAZIONI DELL'UTENTE
 *      NON SI TOCCANO (decisione dell'utente del 25 set 2026, su tutti i
 *      desktop).
 *
 * ⛔ IL DIFETTO: su GNOME la disposizione negoziata col browser si scriveva
 *    in `org.gnome.desktop.input-sources` del dconf DELL'UTENTE
 *    (`~/.config/dconf/user`), e ci restava: chi poi entrava al monitor si
 *    trovava la tastiera cambiata.  E con lei le chiavi di
 *    `sessione_impostazioni()` (blocco, inattivita', «Esci», Ctrl+Alt+F*).
 *
 * ⭐ LA CURA: un PROFILO dconf della sessione, `$XDG_RUNTIME_DIR/remotix/
 *    dconf/profilo`, con in cima un database SCRIVIBILE che vive in memoria:
 *
 *        service-db:shm/remotix     ← qui finisce OGNI scrittura
 *        user-db:user               ← quello dell'utente, SOTTO: solo letto
 *        (le altre righe del profilo di sistema, se c'e')
 *
 *   `[R]` dconf 0.40 (Debian 13): con piu' sorgenti **si scrive solo nella
 *   prima** (`dconf-engine-profile.c`: «If the first source is a "user-db:"
 *   or "service-db:" then the resulting profile will be writable»), si legge
 *   dall'alto in basso, e i segnali di cambio si ascoltano su TUTTE
 *   (`dconf_engine_watch_fast`).  ⇒ La sessione vede le impostazioni
 *   dell'utente con sopra le nostre; l'utente non vede niente.
 *   `[R]` `shm` e' uno scrittore di `dconf-service` (`dconf-shm-writer.c`)
 *   che tiene il database in `$XDG_RUNTIME_DIR/dconf-service/shm/` — tmpfs,
 *   mai in `~/.config`.  ⚠ Il nome `remotix` senza trattini: finisce in un
 *   percorso D-Bus (`/ca/desrt/dconf/shm/remotix`), che li rifiuta.
 *
 * ⭐ COME ARRIVA A GNOME: `DCONF_PROFILE` nell'ambiente di `gnome-session`
 *    (`componi_ambiente()`), che lo ESPORTA al gestore d'utente
 *    (`[R]` gnome-session `gsm_util_export_user_environment`: tutto l'ambiente
 *    tranne quattro variabili) — la stessa strada per cui `XDG_SESSION_TYPE`
 *    arriva all'unita' della Shell.  ⇒ `gnome-shell` (che applica
 *    `input-sources`: `keyboard.js`, `InputSourceManager`), i `gsd-*` e ogni
 *    programma della sessione leggono attraverso il profilo.  Nel FIGLIO lo
 *    mette `sessione_dconf_prepara()`, prima di qualunque `GSettings`.
 *
 * ⛔ PERCHE' NON «SCRIVO E POI RIMETTO COM'ERA»: e' la strada fragile.  Se il
 *    figlio muore male, o la macchina si spegne a sessione aperta, il valore
 *    nostro resta nel file dell'utente PER SEMPRE, e nessuno lo rimette.  Qui
 *    non c'e' niente da rimettere: nel file dell'utente non si scrive mai.
 *
 * ⚠ I PREZZI, dichiarati:
 *   · anche quel che l'UTENTE cambia dal desktop remoto (lo sfondo, una
 *     scorciatoia) finisce nel database della sessione, e si perde quando la
 *     sessione rinasce (`sessione_dconf_azzera()`) o la macchina si riavvia;
 *   · il profilo OBBLIGATORIO (`/run/dconf/user/<uid>`) vince su
 *     `DCONF_PROFILE`: se c'e', la cura non puo' valere, e lo si dice;
 *   · la variabile resta nell'ambiente del gestore d'utente finche' lui vive
 *     (e il file del profilo con lei: stanno tutt'e due in `XDG_RUNTIME_DIR`).
 *     Un accesso al monitor che condividesse QUEL gestore la erediterebbe —
 *     come eredita gia' il drop-in `--headless` di `scrivi_dropin()`.
 */
#define DCONF_SESSIONE_SORGENTE "service-db:shm/remotix"
#define DCONF_SESSIONE_OGGETTO "/ca/desrt/dconf/shm/remotix"

static char *dconf_profilo_percorso(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	if (!runtime || !*runtime)
		return NULL;
	return g_build_filename(runtime, "remotix", "dconf", "profilo", NULL);
}

static gboolean dconf_in_vigore;

/* Il profilo che dconf userebbe SENZA di noi, nell'ordine di
 * `dconf_engine_profile_open()`: `DCONF_PROFILE` (se non e' il nostro), quello
 * di runtime, `user` in `/etc` e nelle `XDG_DATA_DIRS`.  NULL = nessuno, cioe'
 * il predefinito di dconf, «user-db:user». */
static char *dconf_profilo_di_base(const char *nostro)
{
	const char *amb = g_getenv("DCONF_PROFILE");
	g_autoptr(GPtrArray) candidati = g_ptr_array_new_with_free_func(g_free);
	const char *const *dati = g_get_system_data_dirs();

	if (amb && *amb && g_strcmp0(amb, nostro) != 0) {
		if (amb[0] == '/')
			g_ptr_array_add(candidati, g_strdup(amb));
		else {
			g_ptr_array_add(candidati, g_build_filename("/etc/dconf/profile", amb, NULL));
			for (int i = 0; dati[i]; i++)
				g_ptr_array_add(candidati,
				                g_build_filename(dati[i], "dconf", "profile", amb, NULL));
		}
	} else {
		g_ptr_array_add(candidati, g_build_filename(g_get_user_runtime_dir(), "dconf",
		                                            "profile", NULL));
		g_ptr_array_add(candidati, g_strdup("/etc/dconf/profile/user"));
		for (int i = 0; dati[i]; i++)
			g_ptr_array_add(candidati,
			                g_build_filename(dati[i], "dconf", "profile", "user", NULL));
	}
	for (guint i = 0; i < candidati->len; i++) {
		char *testo = NULL;

		if (g_file_get_contents(g_ptr_array_index(candidati, i), &testo, NULL, NULL))
			return testo;
	}
	return NULL;
}

bool sessione_dconf_prepara(void)
{
	g_autofree char *percorso = dconf_profilo_percorso();
	g_autofree char *cartella = NULL;
	g_autofree char *obbligatorio = NULL;
	g_autofree char *base = NULL;
	g_autoptr(GString) profilo = g_string_new(NULL);
	g_autoptr(GError) sbaglio = NULL;
	g_auto(GStrv) righe = NULL;
	int sorgenti = 0;

	/* ⚠ Solo GNOME: gli altri desktop non leggono le loro impostazioni da
	 *   dconf, e la disposizione la mettono per altre strade (kxkbrc della
	 *   sessione su KDE, la keymap della tastiera virtuale su wlroots). */
	if (sessione_desktop() != SESSIONE_DESKTOP_GNOME)
		return false;
	if (!percorso) {
		registro_dice(REG_SESSIONE,
		              "⛔ D-015: XDG_RUNTIME_DIR non impostata — niente dconf della "
		              "sessione, e allora la disposizione negoziata NON si scrive");
		return false;
	}
	obbligatorio = g_strdup_printf("/run/dconf/user/%u", (unsigned) getuid());
	if (g_file_test(obbligatorio, G_FILE_TEST_EXISTS)) {
		registro_dice(REG_SESSIONE,
		              "⛔ D-015: c'e' un profilo dconf OBBLIGATORIO (%s), e vince su "
		              "DCONF_PROFILE: il dconf della sessione non puo' valere, e la "
		              "disposizione negoziata NON si scrive",
		              obbligatorio);
		return false;
	}

	g_string_append(profilo,
	                "# REMOTIX (D-015): il dconf della sessione remota.  In cima un\n"
	                "# database in memoria che prende OGNI scrittura; sotto, in sola\n"
	                "# lettura, quello dell'utente e i database di sistema.\n"
	                DCONF_SESSIONE_SORGENTE "\n");
	base = dconf_profilo_di_base(percorso);
	righe = g_strsplit(base ? base : "", "\n", -1);
	for (int i = 0; righe[i]; i++) {
		const char *r = g_strstrip(righe[i]);

		if (!*r || r[0] == '#' || g_strcmp0(r, DCONF_SESSIONE_SORGENTE) == 0)
			continue;
		if (g_str_has_prefix(r, "user-db:") || g_str_has_prefix(r, "system-db:") ||
		    g_str_has_prefix(r, "service-db:") || g_str_has_prefix(r, "file-db:")) {
			g_string_append_printf(profilo, "%s\n", r);
			sorgenti++;
		}
	}
	if (!sorgenti)
		g_string_append(profilo, "user-db:user\n");

	cartella = g_path_get_dirname(percorso);
	if (g_mkdir_with_parents(cartella, 0700) != 0 ||
	    !g_file_set_contents(percorso, profilo->str, -1, &sbaglio)) {
		registro_dice(REG_SESSIONE,
		              "⛔ D-015: il profilo dconf della sessione non si scrive (%s): %s — "
		              "e allora la disposizione negoziata NON si scrive",
		              percorso, sbaglio ? sbaglio->message : g_strerror(errno));
		return false;
	}
	/* ⛔ Prima di qualunque `GSettings` del figlio: il motore di dconf legge
	 *    `DCONF_PROFILE` una volta sola, quando nasce. */
	g_setenv("DCONF_PROFILE", percorso, TRUE);
	dconf_in_vigore = TRUE;
	registro_dice(REG_SESSIONE,
	              "⭐ D-015: dconf della SESSIONE in %s (" DCONF_SESSIONE_SORGENTE
	              " in cima, %s sotto in sola lettura): quel che la sessione scrive "
	              "NON tocca le impostazioni dell'utente",
	              percorso, sorgenti ? "il profilo di sistema" : "user-db:user");
	return true;
}

bool sessione_dconf_di_sessione(void)
{
	g_autofree char *percorso = dconf_profilo_percorso();

	return dconf_in_vigore && percorso &&
	       g_strcmp0(g_getenv("DCONF_PROFILE"), percorso) == 0 &&
	       g_file_test(percorso, G_FILE_TEST_EXISTS);
}

/*
 * Una scrittura diretta a uno scrittore di `dconf-service` — `oggetto` e'
 * `/ca/desrt/dconf/shm/remotix` (la sessione) o `/ca/desrt/dconf/Writer/user`
 * (l'UTENTE) — senza passare dal motore del processo, che ha il profilo della
 * sessione.  `valore` NULL = togli (`percorso` che finisce con `/`: tutta la
 * cartella).
 * `[R]` dconf 0.40: `ca.desrt.dconf.Writer.Change` vuole i byte di un
 *    `a{smv}` (`dconf_changeset_serialise`); lo scrittore avvisa i lettori
 *    (`Notify`), quindi la Shell e i `gsd-*` vedono il cambio subito.
 */
static gboolean dconf_cambia(const char *oggetto, const char *percorso, GVariant *valore,
                             GError **sbaglio)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(sbaglio);
	g_autoptr(GVariant) insieme = NULL;
	g_autoptr(GVariant) risposta = NULL;
	GVariantBuilder b;

	if (!bus)
		return FALSE;
	g_variant_builder_init(&b, G_VARIANT_TYPE("a{smv}"));
	g_variant_builder_add(&b, "{smv}", percorso, valore);
	insieme = g_variant_ref_sink(g_variant_builder_end(&b));
	risposta = g_dbus_connection_call_sync(
		bus, "ca.desrt.dconf", oggetto, "ca.desrt.dconf.Writer", "Change",
		g_variant_new("(@ay)",
		              g_variant_new_fixed_array(G_VARIANT_TYPE_BYTE,
		                                        g_variant_get_data(insieme),
		                                        g_variant_get_size(insieme), 1)),
		G_VARIANT_TYPE("(s)"), G_DBUS_CALL_FLAGS_NONE, 5000, NULL, sbaglio);
	return risposta != NULL;
}

/*
 * ⭐ Alla nascita il database della sessione si SVUOTA: la sessione nuova
 *    parte dalle impostazioni dell'utente di adesso, piu' le nostre — non da
 *    quel che la sessione di prima (o il suo cliente) ci aveva lasciato.
 *    E' `dconf reset -f /` detto a mano, per non dipendere da `dconf-cli`.
 */
static void sessione_dconf_azzera(void)
{
	g_autoptr(GError) sbaglio = NULL;

	if (!sessione_dconf_di_sessione())
		return;
	if (dconf_cambia(DCONF_SESSIONE_OGGETTO, "/", NULL, &sbaglio))
		registro_dice(REG_SESSIONE,
		              "⭐ D-015: dconf della sessione SVUOTATO — la sessione nasce dalle "
		              "impostazioni dell'utente di adesso, piu' le nostre");
	else
		registro_dice(REG_SESSIONE,
		              "⚠ D-015: il dconf della sessione non si svuota (%s): la sessione "
		              "nuova eredita quel che aveva la precedente — l'utente resta "
		              "intatto comunque",
		              sbaglio ? sbaglio->message : "senza motivo");
}

/*
 * ⭐ FASE 15, D-018 — le due cartelle della SESSIONE LXQt, in testa a
 *    `XDG_CONFIG_DIRS` e a `XDG_DATA_DIRS` (`componi_ambiente()`): quel che
 *    la sessione deve avere e che non e' blocco, riavvio, sospensione o
 *    stand-by sta qui, e non nei file dell'utente.  NULL senza
 *    `XDG_RUNTIME_DIR`.
 */
static char *lxqt_cartella_config_sessione(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	return runtime && *runtime ? g_build_filename(runtime, "remotix", "xdg-lxqt", NULL) : NULL;
}

static char *lxqt_cartella_dati_sessione(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	return runtime && *runtime ? g_build_filename(runtime, "remotix", "dati-lxqt", NULL)
	                           : NULL;
}

/*
 * ⭐ FASE 15, D-007 — IL PEZZO DI CONFIGURAZIONE DI labwc PER XFCE: solo la
 *    scorciatoia che riporta dentro le finestre (`SESSIONE_LABWC_TASTIERA`).
 *
 * ⛔ Su XFCE la configurazione di labwc e' dell'UTENTE (`~/.config/labwc`), e
 *    resta sua: questo file sta in una cartella NOSTRA messa in testa a
 *    `XDG_CONFIG_DIRS`, e labwc parte con `-m` (`SESSIONE_RIGA_XFCE`), che
 *    legge e SOMMA gli `rc.xml` di tutte le cartelle — prima i nostri, poi
 *    quelli dell'utente, che vincono dove dicono la stessa cosa (`[R]` labwc
 *    0.8.3 `src/config/rcxml.c:1898-1937`).
 * ⚠ Con `<default/>`: se l'utente non ha scorciatoie sue, le sue di serie
 *   restano (con UNA `<keybind>` labwc non le caricherebbe piu').
 *
 * Torna la cartella da mettere in `XDG_CONFIG_DIRS`, o NULL (detto: la
 * sessione nasce lo stesso, senza la cura).
 */
static char *scrivi_config_labwc_xfce(const char *runtime)
{
	g_autofree char *cartella = NULL;
	g_autofree char *sotto = NULL;
	g_autofree char *rc = NULL;
	g_autoptr(GError) sbaglio = NULL;

	if (!runtime || !*runtime)
		return NULL;
	cartella = g_build_filename(runtime, "remotix", "labwc-xfce", NULL);
	sotto = g_build_filename(cartella, "labwc", NULL);
	rc = g_build_filename(sotto, "rc.xml", NULL);
	if (g_mkdir_with_parents(sotto, 0700) != 0 ||
	    !g_file_set_contents(rc,
	                         "<?xml version=\"1.0\"?>\n"
	                         "<!-- REMOTIX (D-007): scritto a ogni nascita della sessione "
	                         "XFCE, non modificare.\n"
	                         "     labwc parte con -m: questo si SOMMA al rc.xml "
	                         "dell'utente.  " SESSIONE_LABWC_TASTO " riporta dentro "
	                         "le finestre\n     quando lo schermo remoto si "
	                         "rimpicciolisce. -->\n"
	                         "<labwc_config>\n" SESSIONE_LABWC_TASTIERA
	                         "</labwc_config>\n",
	                         -1, &sbaglio)) {
		registro_dice(REG_SESSIONE,
		              "⛔ XFCE, D-007: la configurazione di labwc NON e' scritta in %s "
		              "(%s) — la sessione nasce lo stesso, ma riattaccandosi con una "
		              "finestra piu' piccola le finestre grandi resteranno in parte "
		              "FUORI dallo schermo",
		              rc, sbaglio ? sbaglio->message : g_strerror(errno));
		return NULL;
	}
	registro_dice(REG_SESSIONE,
	              "⭐ XFCE, D-007: scorciatoia «riporta dentro» (%s) per labwc in %s, "
	              "sommata alla configurazione dell'utente (-m)",
	              SESSIONE_LABWC_TASTO, rc);
	return g_steal_pointer(&cartella);
}

/*
 * L'ambiente della sessione, composto da zero: quel che non serve non passa.
 * Dieci variabili, una per volta (`CODER.md` §4.5).
 */
static char **componi_ambiente(void)
{
	GPtrArray *ambiente = g_ptr_array_new_with_free_func(g_free);
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	const char *bus = g_getenv("DBUS_SESSION_BUS_ADDRESS");
	g_autofree char *bus_dedotto = NULL;

	if (!runtime || !*runtime) {
		registro_dice(REG_SESSIONE,
		              "⛔ XDG_RUNTIME_DIR non impostata: non so dove vive la sessione");
		g_ptr_array_free(ambiente, TRUE);
		return NULL;
	}
	if (!bus || !*bus) {
		/* Il bus di sessione sta convenzionalmente li' dentro; dedurlo e' meglio
		 * che rinunciare, perche' un ambiente da cui la variabile manca — un'unita'
		 * systemd, per esempio — e' del tutto normale. */
		bus_dedotto = g_strdup_printf("unix:path=%s/bus", runtime);
		bus = bus_dedotto;
		registro_dice(REG_SESSIONE, "DBUS_SESSION_BUS_ADDRESS assente: uso %s", bus);
	}

	g_ptr_array_add(ambiente, g_strdup_printf("XDG_RUNTIME_DIR=%s", runtime));
	g_ptr_array_add(ambiente, g_strdup_printf("DBUS_SESSION_BUS_ADDRESS=%s", bus));

	/*
	 * ⭐ FASE 12 — su Plasma il mezzo dell'ambiente e' un altro, e piu' corto
	 *    (`STUDI.md` §kde §6.1, la ricetta di v1 `[M]` 7-8 agosto 2026):
	 *
	 *   · `XDG_MENU_PREFIX=plasma-` — ⛔ senza, `kbuildsycoca6` costruisce un
	 *     indice VUOTO e KWin nega la cattura senza dire perche' (§3.3-bis).
	 *     `startplasma` la mette da se', ma un processo che ricostruisce
	 *     l'indice prima di lui lo sovrascrive: si mette qui, per tutto l'albero;
	 *   · ⛔ NIENTE `XDG_CURRENT_DESKTOP`, `XDG_SESSION_TYPE`, `DISPLAY`,
	 *     `WAYLAND_DISPLAY`, `QT_QPA_PLATFORM`: con una di queste KWin sceglie il
	 *     backend ANNIDATO invece di `--virtual` (`main_wayland.cpp:452-463`),
	 *     e Plasma le mette da se' (`startplasma.cpp:353-414`);
	 *   · ⛔ niente `SHELL=`: la trappola della shell di login e' di
	 *     `gnome-session`, e `startplasma-wayland` non la ha.
	 */
	if (e_kde()) {
		g_autofree char *regole = scrivi_regole_menu_kde(runtime);
		g_autofree char *icone = scrivi_tema_cursore(runtime);

		g_ptr_array_add(ambiente, g_strdup("XDG_MENU_PREFIX=plasma-"));
		/* ⚠ DAVANTI a `/etc/xdg`, non al suo posto: da li' viene
		 *   `menus/plasma-applications.menu`, il file che il prefisso qui sopra
		 *   va a cercare — sostituirlo spegnerebbe la cattura (§3.3-bis). */
		if (regole)
			g_ptr_array_add(ambiente,
			                g_strdup_printf("XDG_CONFIG_DIRS=%s:%s", regole,
			                                g_getenv("XDG_CONFIG_DIRS") ?: "/etc/xdg"));
		/* ⛔ LE TRE VARIABILI VANNO INSIEME: `XCURSOR_THEME` da sola non basta
		 *    (KWin la guarda solo con `XCURSOR_SIZE`), e `XCURSOR_PATH` serve
		 *    perche' il tema sta in `XDG_RUNTIME_DIR`, che nessuna ricerca
		 *    predefinita guarda — con le cartelle di sistema in coda, per non
		 *    togliere i temi veri a chi li cerca per altro. */
		if (icone) {
			g_ptr_array_add(ambiente, g_strdup("XCURSOR_THEME=" TEMA_CURSORE));
			g_ptr_array_add(ambiente, g_strdup("XCURSOR_SIZE=24"));
			g_ptr_array_add(ambiente,
			                g_strdup_printf("XCURSOR_PATH=%s:%s", icone,
			                                "/usr/share/icons:/usr/local/share/icons"));
		}
		goto la_coda;
	}

	/*
	 * ⭐⭐ FASE 13 — L'AMBIENTE DI XFCE, e ogni riga ha pagato il suo posto
	 *      (`STUDI.md` §xfce §9.3, §10.1; `[M]` provato dentro `rete11-xfce` il
	 *      20 set 2026: sessione intera viva, pannello e scrivania compresi).
	 *
	 * ⭐ La colonna «da togliere» è già gratis: `componi_ambiente()` costruisce
	 *   da zero e non eredita niente tranne `PATH` — `DISPLAY`,
	 *   `WAYLAND_DISPLAY`, `SESSION_MANAGER` non ci sono per costruzione.  ⛔ Il
	 *   pericolo è solo quel che si AGGIUNGE, ed è il blocco di GNOME qui sotto
	 *   in cui XFCE cadrebbe senza questo `if`.
	 */
	/*
	 * ⭐⭐ FASE 14 — E L'AMBIENTE DI LXQt STA NELLO STESSO BLOCCO, perche' metà
	 *      delle righe sono di LABWC e non del desktop: `WLR_*`, la scheda,
	 *      `LABWC_UPDATE_ACTIVATION_ENV`, il cursore.  ⛔ Scriverle due volte
	 *      vorrebbe dire poterle far divergere.  Le righe del DESKTOP stanno
	 *      in due rami separati, e il ramo di XFCE è quello di prima.
	 */
	if (e_xfce() || e_lxqt()) {
		g_autofree char *icone = scrivi_tema_cursore(runtime);

		if (e_xfce()) {
			/* ⛔ SECCO e maiuscolo, senza suffissi: labwc ci metterebbe
			 *    `labwc:wlroots`, e garcon non spezza sui `:` — con un suffisso le
			 *    voci `OnlyShowIn=XFCE;` **spariscono** dal menu. */
			g_ptr_array_add(ambiente, g_strdup("XDG_CURRENT_DESKTOP=XFCE"));
			g_ptr_array_add(ambiente, g_strdup("XDG_SESSION_DESKTOP=xfce"));
			g_ptr_array_add(ambiente, g_strdup("XDG_SESSION_TYPE=wayland"));
			/* ⚠ Non perche' manchi — garcon ha un ripiego — ma per non EREDITARNE
			 *   una sbagliata: il controllo là dentro è `prefix != NULL`. */
			g_ptr_array_add(ambiente, g_strdup("XDG_MENU_PREFIX=xfce-"));
			/* ⭐ FASE 15, D-007 — la cartella con la scorciatoia di labwc, DAVANTI
			 *    alle cartelle di sistema (non al loro posto): dentro c'e' solo
			 *    `labwc/rc.xml`, quindi per ogni altro programma non cambia
			 *    niente. */
			{
				g_autofree char *labwc_cfg = scrivi_config_labwc_xfce(runtime);
				const char *prima = g_getenv("XDG_CONFIG_DIRS");

				if (labwc_cfg)
					g_ptr_array_add(ambiente,
					                g_strdup_printf("XDG_CONFIG_DIRS=%s:%s", labwc_cfg,
					                                prima && *prima ? prima : "/etc/xdg"));
			}
		} else {
			/*
			 * ⭐ FASE 14 — LE RIGHE DI LXQt (`STUDI.md` §lxqt §3.2), e ogni valore
			 *    è quello del lanciatore upstream coetaneo, ramo `labwc`:
			 *    `[R]` lxqt-wayland-session 0.1.1 `startlxqtwayland.in`.
			 *
			 * ⛔⛔ `XDG_CURRENT_DESKTOP` NON SECCA, al contrario di XFCE: il
			 *     pannello sceglie il backend delle finestre **dai token** (`wlroots`
			 *     il più forte), e con `LXQt` secco casca sul backend `dummy` —
			 *     taskbar vuota, tutto inerte, un solo `qWarning`.  E i moduli hanno
			 *     `OnlyShowIn=LXQt;`: senza `LXQt` la sessione è viva e NERA.
			 * ⭐ `LXQt:labwc:wlroots` e non `LXQt:wlroots`: è la forma che lo script
			 *    upstream dà a chi HA configurato labwc (`"LXQt:$COMPOSITOR:wlroots"`);
			 *    `LXQt:wlroots` la usa solo per il primo avvio, quello che apre il
			 *    wizard.  Tutt'e due portano `LXQt` e `wlroots`; `STUDI.md` §lxqt §3.2
			 *    sceglie la prima, e qui la si tiene.
			 * ⚠ labwc la mette solo se manca (`setenv(…, 0)`, `[R]` labwc 0.8.3
			 *   `src/config/session.c:256`): la nostra resta. */
			g_ptr_array_add(ambiente, g_strdup("XDG_CURRENT_DESKTOP=LXQt:labwc:wlroots"));
			g_ptr_array_add(ambiente, g_strdup("XDG_SESSION_DESKTOP=lxqt"));
			/* ⛔ Non cosmetica: il pannello sceglie il backend da QUESTA, non da
			 *    `platformName()` (`STUDI.md` §lxqt §3.2). */
			g_ptr_array_add(ambiente, g_strdup("XDG_SESSION_TYPE=wayland"));
			/* ⛔ Nessun ripiego cablato in libqtxdg: senza, il menu non c'è. */
			g_ptr_array_add(ambiente, g_strdup("XDG_MENU_PREFIX=lxqt-"));
			/* ⛔ Deve contenere `/usr/share`: i default di LXQt stanno in
			 *    `/usr/share/lxqt/<modulo>.conf`, e senza spariscono IN SILENZIO.  Il
			 *    valore è quello dello script upstream, parola per parola, con
			 *    `/etc/xdg` (il ritocco di Debian, `lxqt-branding-debian`) davanti a
			 *    `/usr/share`.  [?] Quale dei due vinca davvero è la misura M6. */
			/* ⭐ FASE 15, D-018 — e DAVANTI a tutte, la cartella della
			 *    SESSIONE (`pannello_lxqt()`): quel che la sessione deve avere
			 *    sta li', non nei file dell'utente.  ⚠ Resta prima di lei
			 *    solo `~/.config`, cioe' l'utente — che vince, e va bene. */
			{
				g_autofree char *cfg = lxqt_cartella_config_sessione();
				g_autofree char *dati = lxqt_cartella_dati_sessione();
				const char *dati_prima = g_getenv("XDG_DATA_DIRS");

				g_ptr_array_add(ambiente,
				                g_strdup_printf("XDG_CONFIG_DIRS=%s%s/etc:/etc/xdg:/usr/share",
				                                cfg ? cfg : "", cfg ? ":" : ""));
				/* e i DATI: le voci pericolose del menu nascoste
				 * (`impostazioni_lxqt()`), in testa a quelle di sistema */
				if (dati)
					g_ptr_array_add(ambiente,
					                g_strdup_printf("XDG_DATA_DIRS=%s:%s", dati,
					                                dati_prima && *dati_prima
					                                        ? dati_prima
					                                        : "/usr/local/share:/usr/share"));
			}
			/* ⛔ SECCO (`STUDI.md` §lxqt §3.2, `LEZIONI.md` §1.8): con xcb
			 *    `lxqt-session` diventa un'altra sessione — un secondo window
			 *    manager, un dialogo modale, un secondo comandante della
			 *    risoluzione.  ⚠ Lo script upstream NON la mette: è una scelta
			 *    nostra, e il prezzo è dichiarato — un'applicazione Qt senza il
			 *    plugin wayland muore (`qFatal`) invece di ripiegare su Xwayland.
			 *    [?] Da guardare sulla scatola: chi muore così (qlipper è Qt5). */
			g_ptr_array_add(ambiente, g_strdup("QT_QPA_PLATFORM=wayland"));
			/* Il tema Qt di LXQt (`lxqt-qtplugin`): icone, stile e font del
			 * desktop.  Lo mette lo script upstream; senza, il desktop parte con
			 * l'aspetto nudo di Qt. */
			g_ptr_array_add(ambiente, g_strdup("QT_QPA_PLATFORMTHEME=lxqt"));
		}
		/* ⛔ Il «senza schermo» di questa famiglia.  Con `headless` non nasce
		 *    nessuna `wlr_session` e libseat non viene sfiorato: il muro su cui
		 *    KWin moriva qui non esiste. */
		g_ptr_array_add(ambiente, g_strdup("WLR_BACKENDS=headless"));
		g_ptr_array_add(ambiente, g_strdup("WLR_LIBINPUT_NO_DEVICES=1"));
		/* ⛔⛔ SENZA RIPIEGO: se questo nodo non si apre, wlroots ripiega su
		 *     pixman — **software, in silenzio**.  È la stessa forma del
		 *     codificatore che ripiega e lo dichiara, ma qui non lo dichiara
		 *     nessuno: l'unico modo di accorgersene è che i numeri crollino. */
		{
			g_autofree char *nodo = nodo_della_scheda();

			if (nodo) {
				g_ptr_array_add(ambiente,
				                g_strdup_printf("WLR_RENDER_DRM_DEVICE=%s", nodo));
				registro_dice(REG_SESSIONE,
				              "⭐ %s: la scheda che do a wlroots è %s (aperta, non "
				              "dedotta)", nome_desktop(), nodo);
			} else {
				registro_dice(REG_SESSIONE,
				              "⛔ %s: nessun nodo /dev/dri/renderD* apribile — NON "
				              "passo WLR_RENDER_DRM_DEVICE, e wlroots sceglierà da sé. "
				              "⚠ Se ripiega su pixman lo fa IN SILENZIO: i numeri "
				              "crolleranno e questa è l'unica riga che lo spiega",
				              nome_desktop());
			}
		}
		/* ⛔ OBBLIGATORIA: senza, su headless labwc **non propaga**
		 *    `WAYLAND_DISPLAY` al bus e a systemd, e lo fa in silenzio ⇒ le
		 *    applicazioni della sessione non trovano il compositore. */
		g_ptr_array_add(ambiente, g_strdup("LABWC_UPDATE_ACTIVATION_ENV=1"));
		/*
		 * ⭐ FASE 14 — le due righe qui sotto sono di XFCE e restano SOLO sue:
		 *   · `GDK_BACKEND` secco cura il salvaschermo di XFCE su Xwayland, che
		 *     in LXQt non c'è; lo script upstream di LXQt non la mette, e GTK
		 *     prende da sé wayland per primo.  [?] Da guardare se
		 *     un'applicazione GTK finisce su Xwayland dentro LXQt;
		 *   · `XFCE4_SESSION_COMPOSITOR` la legge solo `xfce4-session`: su LXQt
		 *     la trappola del `loginctl terminate-session` non esiste
		 *     (`STUDI.md` §lxqt §3.3, `[✗]`).
		 */
		if (e_xfce()) {
			/* ⛔ SECCO: `wayland,x11` fa risorgere il salvaschermo su Xwayland e
			 *    riaccende XSETTINGS e i grab — due comportamenti sotto una sola
			 *    etichetta, che è quel che rende una misura incomparabile. */
			g_ptr_array_add(ambiente, g_strdup("GDK_BACKEND=wayland"));
			/*
			 * ⛔⛔ LA CINTURA DEL LOGOUT, e non è una variabile decorativa.
			 *
			 * `xfce4-session` legge QUESTA, non quel che abbiamo eseguito
			 * davvero, e se non ci trova **sia** `labwc` **sia** `--session` al
			 * logout esegue `loginctl terminate-session ''` — cioe' ammazza la
			 * sessione logind di REMOTIX (`STUDI.md` §xfce §9.2).  ⇒ Ci si mette
			 *   la riga ESATTA che si esegue, togliendo l'`exec` davanti che qui
			 *   non c'entra.
			 */
			g_ptr_array_add(ambiente,
			                g_strdup("XFCE4_SESSION_COMPOSITOR=" SESSIONE_RIGA_XFCE));
		}
		/* Il cursore: la stessa cura di KDE (tema 1x1 ad alfa zero), con un
		 * vincolo in meno — `XCURSOR_SIZE` qui non è obbligatoria.  ⛔ Ma il
		 * tema deve ESSERCI: con un tema vuoto wlroots ripiega su uno
		 * incorporato e VISIBILE, che è il contrario di quel che si voleva. */
		if (icone) {
			g_ptr_array_add(ambiente, g_strdup("XCURSOR_THEME=" TEMA_CURSORE));
			g_ptr_array_add(ambiente, g_strdup("XCURSOR_SIZE=24"));
			g_ptr_array_add(ambiente,
			                g_strdup_printf("XCURSOR_PATH=%s:%s", icone,
			                                "/usr/share/icons:/usr/local/share/icons"));
		}
		goto la_coda;
	}

	/* La sessione deve DICHIARARSI, o le applicazioni di GNOME non si
	 * riconoscono a casa propria e si fermano da sole. */
	g_ptr_array_add(ambiente, g_strdup("XDG_CURRENT_DESKTOP=GNOME"));
	g_ptr_array_add(ambiente, g_strdup("XDG_SESSION_DESKTOP=gnome"));
	/*
	 * ⛔ `XDG_SESSION_TYPE=wayland` SERVE, e non e' una bugia: l'unita' della
	 *    Shell porta `ConditionEnvironment=XDG_SESSION_TYPE=wayland` (verificato
	 *    nel file installato su NIC-OS il 12 ago 2026), e senza il compositore
	 *    non viene avviato AFFATTO — sessione monca, e nessuna riga che dica
	 *    perche'.
	 */
	g_ptr_array_add(ambiente, g_strdup("XDG_SESSION_TYPE=wayland"));
	/*
	 * ⛔ `SHELL` VUOTA, ed e' la trappola di `STUDI.md` §gnome §3.1: `gnome-session.in:3-14`
	 *    si ri-esegue dentro una shell di LOGIN se `$SHELL` non e' vuota e sta in
	 *    `/etc/shells` — cioe' si riporta dentro `~/.profile`, che e' `CODER.md`
	 *    §4.5 in agguato dopo che l'ambiente e' stato composto con cura.
	 *
	 * ⚠ Il controllo vero e' `[ -n "$SHELL" ]`, quindi ASSENTE e VUOTA vanno
	 *   tutt'e due bene — e v1 la lasciava assente, per costruzione, senza
	 *   saperlo.  Qui la si mette VUOTA di proposito: assente e vuota sono la
	 *   stessa cosa per `gnome-session` e **due cose diverse per chi misura**,
	 *   perche' vuota si vede in `/proc/<gnome-session-binary>/environ` e assente
	 *   si confonde con «non ho letto l'ambiente».
	 */
	g_ptr_array_add(ambiente, g_strdup("SHELL="));
	/* ⭐ FASE 15, D-015 — il dconf della sessione: `gnome-session` lo esporta
	 *    al gestore d'utente, e la Shell e i `gsd-*` lo ereditano (il riquadro
	 *    sopra `sessione_dconf_prepara()`). */
	if (sessione_dconf_di_sessione()) {
		g_autofree char *profilo = dconf_profilo_percorso();

		g_ptr_array_add(ambiente, g_strdup_printf("DCONF_PROFILE=%s", profilo));
	} else
		registro_dice(REG_SESSIONE,
		              "⛔ D-015: la sessione GNOME nasce SENZA il dconf della sessione "
		              "— quel che scrivera' la sessione finira' nelle impostazioni "
		              "dell'utente");
	/*
	 * ⚠ E `XDG_SESSION_ID` NON si passa, di proposito.  `STUDI.md` §gnome §3.1 avverte
	 *   che senza di essa Mutter puo' agganciare la sessione logind sbagliata —
	 *   ma quella che erediteremmo noi e' la sessione di CHI CI HA AVVIATI (un
	 *   ssh, cioe' `tty`), e regalargliela sarebbe mandarlo sulla sessione
	 *   sbagliata **con la nostra firma sopra**.  ⭐ La scena misurata sana il 12
	 *   agosto 2026 non la porta.  Resta `[?]` che cosa succeda quando REMOTIX
	 *   gira come unita' di sistema.
	 */
la_coda:
	g_ptr_array_add(ambiente, g_strdup_printf("LANG=%s", locale_utf8()));
	g_ptr_array_add(ambiente, g_strdup_printf("HOME=%s", g_get_home_dir()));
	g_ptr_array_add(ambiente, g_strdup_printf("USER=%s", g_get_user_name()));
	g_ptr_array_add(ambiente, g_strdup_printf("PATH=%s", g_getenv("PATH") ?: "/usr/bin:/bin"));
	g_ptr_array_add(ambiente, NULL);

	return (char **) g_ptr_array_free(ambiente, FALSE);
}

/* ------------------------------------------------------------------------- */
/*
 * Un comando, con la sua uscita.
 *
 * ⛔ Due funzioni e non una, e la differenza e' `REVIEWER.md` §1 punto 4: per
 *    `daemon-reload` lo stato d'uscita E' la risposta e si guarda; per
 *    `is-active` lo stato d'uscita e' 3 quando la risposta e' «inactive», cioe'
 *    il caso normale — guardarlo li' vorrebbe dire chiamare fallimento una
 *    risposta.  Chi le confonde ottiene un banco che si ferma quando tutto va
 *    bene, o peggio uno che non si ferma mai.
 */
static gboolean esegui(char **argv)
{
	g_autoptr(GError) sbaglio = NULL;
	int stato = 0;

	if (!g_spawn_sync(NULL, argv, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL, NULL, &stato,
	                  &sbaglio) ||
	    !g_spawn_check_wait_status(stato, &sbaglio)) {
		registro_dice(REG_SESSIONE, "⛔ «%s …» non e' andato: %s", argv[0],
		              sbaglio ? sbaglio->message : "senza motivo");
		return FALSE;
	}
	return TRUE;
}

/* Lo standard output di un comando, qualunque sia il suo stato d'uscita.
 * NULL solo se non l'ho potuto ESEGUIRE — che e' un fatto diverso. */
static char *chiedi(char **argv)
{
	g_autoptr(GError) sbaglio = NULL;
	char *uscita = NULL;
	int stato = 0;

	if (!g_spawn_sync(NULL, argv, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, &uscita, NULL, &stato,
	                  &sbaglio)) {
		registro_dice(REG_SESSIONE, "⛔ non ho potuto eseguire «%s»: %s", argv[0],
		              sbaglio ? sbaglio->message : "senza motivo");
		return NULL;
	}
	return uscita;
}

/*
 * ⛔⭐ IL DROP-IN — LA RIGA CHE IN v1 SI SCRIVEVA SOLO PER KWIN.
 *
 * `gnome-session` non lancia `gnome-shell`: fa partire l'unita' d'utente
 * `org.gnome.Shell@wayland.service`, il cui `ExecStart` e' fisso.  Per chiedere
 * il monitor virtuale serve un drop-in, e la ricetta — copia in `user.control`
 * piu' `daemon-reload` — e' la stessa che v1 usa per `plasma-kwin_wayland`.
 *
 * ⛔ E QUI SI SCRIVE SEMPRE, non «se il compositore e' KWin».  Il difetto che
 *    questa funzione cura e' `sessione.c:671` di v1, dove la condizione
 *    `tipo == COMPOSITORE_KWIN &&` faceva saltare la chiamata per corto circuito
 *    e la misura del desktop si perdeva in silenzio.  ⚠ Il giorno in cui KWin
 *    torna in V2, quel che cambia sono **il nome dell'unita' e la riga**, non
 *    **se** scriverla: la scrittura non torna dietro a un `if` sul compositore.
 *
 * Dove: `$XDG_RUNTIME_DIR/systemd/user.control/…`, per tre ragioni:
 *   1. non serve root — l'unita' e' d'UTENTE;
 *   2. sparisce da se' al riavvio, e riscriverla e' compito di questa funzione
 *      a ogni nascita: e' proprio cosi' che la protezione sta nel programma (I7)
 *      invece che in un file che qualcuno deve ricordarsi di rimettere;
 *   3. ⛔ il nome comincia per `zz-` **apposta**: i drop-in di tutte le cartelle
 *      si applicano in ordine di NOME FILE, e in `/etc/systemd/user` ce n'e' gia'
 *      uno che si chiama `remotix-headless.conf`.  `zz-…` viene dopo, quindi
 *      vince — e la vittoria si VERIFICA, non si spera.
 */
static gboolean scrivi_dropin(uint32_t larghezza, uint32_t altezza)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	g_autofree char *cartella = NULL;
	g_autofree char *percorso = NULL;
	g_autofree char *contenuto = NULL;
	g_autofree char *shell = NULL;
	g_autofree char *atteso = NULL;
	g_autofree char *vigore = NULL;
	g_autoptr(GError) sbaglio = NULL;
	/* ⭐ FASE 12: cambiano l'unita' e la riga, NON se scriverla — il riquadro qui
	 *    sopra lo chiedeva, e il ramo Plasma e' qui sotto, dopo la cartella. */
	const gboolean kde = e_kde();
	const char *unita = kde ? SESSIONE_UNITA_KWIN : SESSIONE_UNITA_SHELL;
	char *ricarica[] = { "systemctl", "--user", "daemon-reload", NULL };
	char *mostra[] = { "systemctl",   "--user", "show", "-p", "ExecStart",
		           "--value", (char *) unita, NULL };

	/*
	 * ⛔⛔ FASE 13 — SU XFCE QUESTA FUNZIONE NON HA OGGETTO, e non è un ramo in
	 *     meno: è un presupposto che cade.
	 *
	 * Questa funzione esiste perche' su GNOME e su KDE **il compositore è
	 * un'unità systemd d'utente** di cui si riscrive l'`ExecStart` — ed è li'
	 * che la misura entra nella nascita.  Su XFCE il compositore lo lanciamo
	 * noi, unità non ce n'è, e `[M]` 20 set 2026 l'uscita nasce comunque
	 * `1280x720` cablata: **la misura non può entrare nella nascita**, per
	 * nessuna strada.
	 *
	 * ⚠ E si DICE, invece di tornare `TRUE` in silenzio: una funzione che
 *   ha ricevuto una misura e non ne ha fatto niente, senza una riga, è il
	 *   modo in cui due numeri si perdono e nessuno se ne accorge.
	 */
	/* ⭐ FASE 14 — su LXQt vale la stessa cosa, e per la stessa ragione: il
	 *    compositore è lo stesso labwc, lanciato da noi. */
	if (e_xfce() || e_lxqt()) {
		registro_dice(REG_SESSIONE,
		              "%s: nessun drop-in da scrivere — il compositore non è "
		              "un'unità di systemd, lo avvio io.  ⛔ E la tela chiesta "
		              "(%ux%u) NON entra nella nascita: su wlroots l'uscita nasce "
		              "cablata e si ridimensiona dopo, col protocollo",
		              nome_desktop(), larghezza, altezza);
		return TRUE;
	}

	if (!runtime || !*runtime) {
		registro_dice(REG_SESSIONE,
		              "⛔ XDG_RUNTIME_DIR non impostata: non so dove scrivere il drop-in");
		return FALSE;
	}

	cartella = g_build_filename(runtime, "systemd", "user.control",
	                            kde ? SESSIONE_UNITA_KWIN ".d" : SESSIONE_UNITA_SHELL ".d",
	                            NULL);
	percorso = g_build_filename(cartella, "zz-remotix-monitor.conf", NULL);

	/*
	 * ⭐ FASE 12 — LA RIGA DI PLASMA, e qui la misura ENTRA davvero.
	 *
	 * ⛔ KWin su una macchina senza seat parte solo col backend `--virtual`
	 *    (`STUDI.md` §kde §5.2, `[M]` M2: `--drm` esce con stato 1), e con quel
	 *    backend l'uscita la decide **la riga di avvio**, una e della misura
	 *    data: `stream_virtual_output` risponde «Could not find output» a ogni
	 *    misura.  ⇒ Il disegno «zero monitor propri» di GNOME qui non esiste —
	 *    l'uscita nasce con la sessione, della misura del cliente che la fa
	 *    nascere.  `[M]` 18 set 2026, rete11-kde: `Virtual-0` 1600x900, una sola.
	 *   · `--xwayland`: obbligatorio, ksmserver forza xcb (`STUDI.md` §kde §6.4);
	 *   · `--no-lockscreen`: il blocco e' di REMOTIX (§4.3), non del desktop.
	 */
	if (kde) {
		g_autofree char *involucro = g_find_program_in_path("kwin_wayland_wrapper");

		if (!involucro) {
			involucro = g_strdup("/usr/bin/kwin_wayland_wrapper");
			registro_dice(REG_SESSIONE,
			              "⚠ «kwin_wayland_wrapper» non e' nel PATH: ripiego "
			              "dichiarato su %s, e se non e' li' l'unita' non partira'",
			              involucro);
		}
		contenuto = g_strdup_printf("[Service]\n"
		                            "ExecStart=\n"
		                            "ExecStart=%s --xwayland --virtual --width %u "
		                            "--height %u --no-lockscreen\n",
		                            involucro, larghezza, altezza);
		atteso = g_strdup_printf("--virtual --width %u --height %u", larghezza, altezza);
		goto scrivi;
	}

	/* ⚠ Un ripiego, e si dichiara (`CODER.md` §4.2): il percorso della Shell si
	 *   chiede al PATH, e solo se non c'e' si scommette su quello di Debian. */
	shell = g_find_program_in_path("gnome-shell");
	if (!shell) {
		shell = g_strdup("/usr/bin/gnome-shell");
		registro_dice(REG_SESSIONE,
		              "⚠ «gnome-shell» non e' nel PATH: ripiego dichiarato su %s, e se "
		              "non e' li' l'unita' non partira'",
		              shell);
	}

	/*
	 * ⚠ `--no-x11` c'e' e non si toglie a cuor leggero: e' la riga che la
	 *   macchina misurata sana il 12 agosto 2026 aveva davvero, e cambiarla
	 *   insieme al monitor vorrebbe dire cambiare due cose per volta.  Chi
	 *   vorra' le applicazioni X11 dentro la sessione la togliera' **da sola**,
	 *   e misurera' quella.
	 */
	/*
	 * ⛔⛔ E `--virtual-monitor` NON C'E' PIU' — 14 agosto 2026, fase 4, A1.
	 *
	 *     Fino a stamattina questa riga chiedeva `--virtual-monitor %ux%u`, e
	 *     la sessione nasceva con **un monitor suo**.  ⇒ Poi `mutter.c:450`
	 *     cattura con `RecordVirtual`, che **ne monta un SECONDO**, e registra
	 *     quello: GNOME lascia barra, dock e finestre sul primo, ci mette solo
	 *     lo sfondo sul secondo, e ⛔ **l'utente guarda uno schermo vuoto**.
	 *
	 * ⭐ MISURATO, non dedotto — `[M]` 14 agosto 2026, banco `04-b20`:
	 *    con la riga di prima, il fotogramma preso dalla cattura e' il solo
	 *    sfondo Debian (bordo della barra 0,01 contro la soglia 4; zero fronti
	 *    di testo), e al client in 40 s non arriva **nessun** fotogramma —
	 *    perche' su uno schermo dove non c'e' niente non cambia mai niente.
	 *
	 * ⇒ ⭐ IL DISEGNO E': la sessione **non ha monitor propri**, e l'unico
	 *      monitor e' quello che monta la nostra cattura.  E' quel che
	 *      `mutter.c:376` dichiarava gia' — *«il nostro `RecordVirtual` ne
	 *      monta uno suo»* — e che questa riga tradiva.
	 *
	 * ⚠ IL PREZZO, E SI DICHIARA: prima del primo client la sessione e'
	 *   **nera** (zero monitor).  Per una sessione **solo remota** va bene —
	 *   nessuno la guarda — ⛔ ma non va bene per una sessione che deve vivere
	 *   senza nessuno che la catturi, ed e' per questo che `PIANO.md:399` e
	 *   `STUDI.md` §gnome §108 («`--virtual-monitor` non e' opzionale») vanno
	 *   riscritti: vedi `fasi/rapporti/F4-A1-desktop-vero.md`.
	 *
	 * ⚠ `larghezza` e `altezza` non entrano piu' in questa riga: adesso la
	 *   misura la decide la negoziazione PipeWire della cattura
	 *   (`meta-screen-cast-virtual-stream-src.c:601-606` `[R]`, che crea il
	 *   monitor con `video_format->size`).  Restano nella firma perche' con
	 *   loro si CONTROLLA quel che si e' ottenuto — vedi `sessione_assicura`.
	 */
	contenuto = g_strdup_printf("[Service]\n"
	                            "ExecStart=\n"
	                            "ExecStart=%s --headless --no-x11\n",
	                            shell);
	(void) larghezza;
	(void) altezza;
	atteso = g_strdup_printf("--headless --no-x11");

scrivi:
	g_mkdir_with_parents(cartella, 0700);
	if (!g_file_set_contents(percorso, contenuto, -1, &sbaglio)) {
		registro_dice(REG_SESSIONE, "⛔ drop-in non scritto (%s): %s", percorso,
		              sbaglio->message);
		return FALSE;
	}

	if (!esegui(ricarica))
		return FALSE;

	/*
	 * ⛔ SCRITTO NON E' IN VIGORE — forma d'errore E1, «necessario scambiato per
	 *    sufficiente».  Si rilegge dal gestore, e se un altro drop-in vince ci
	 *    si ferma qui invece di scoprirlo dal nero sullo schermo dell'utente.
	 */
	/*
	 * ⛔⭐ E L'ATTESO E' CAMBIATO CON LA RIGA — forma d'errore E1, «il controllo
	 *     e' giusto, l'atteso no».  Fino a stamattina qui si PRETENDEVA
	 *     `--virtual-monitor %ux%u`: tolta la bandiera, questo controllo
	 *     avrebbe fatto fallire il prodotto curato.
	 *
	 * ⛔⛔ E ADESSO SI GUARDA ANCHE UN'ASSENZA, che e' la meta' che conta.
	 *
	 *     `[M]` 14 agosto 2026: su questa macchina `--virtual-monitor` non lo
	 *     chiedeva il prodotto — lo chiedeva
	 *     `/etc/systemd/user/org.gnome.Shell@wayland.service.d/remotix-headless.conf`,
	 *     cioe' un drop-in **di sistema** valido per QUALUNQUE utente.  ⇒ Quella
	 *     e' precisamente «una riga di configurazione che si puo' perdere»
	 *     dell'invariante **I7**, e qui vale al contrario: non basta che il
	 *     nostro drop-in ci sia, deve **vincere**.  Se il gestore dice ancora
	 *     `--virtual-monitor`, la sessione nascerebbe col difetto e ci si ferma
	 *     qui invece di scoprirlo dallo schermo vuoto dell'utente.
	 */
	vigore = chiedi(mostra);
	if (!vigore) {
		registro_dice(REG_SESSIONE,
		              "⛔ non ho potuto rileggere l'ExecStart in vigore: scritto non e' "
		              "in vigore, e senza la rilettura non lo so");
		return FALSE;
	}
	g_strstrip(vigore);
	if (!strstr(vigore, atteso)) {
		registro_dice(REG_SESSIONE,
		              "⛔ ho scritto «%s» e il gestore dice un'altra cosa: un altro "
		              "drop-in vince sul mio.  ExecStart in vigore: %s",
		              atteso, vigore);
		return FALSE;
	}
	if (strstr(vigore, "--virtual-monitor")) {
		registro_dice(REG_SESSIONE,
		              "⛔ l'ExecStart in vigore chiede ANCORA «--virtual-monitor», e non "
		              "sono io: c'e' un drop-in che vince sul mio (di solito "
		              "/etc/systemd/user/%s.d/, che vale per tutti gli utenti).  ⚠ Cosi' "
		              "la sessione nascerebbe con un monitor SUO, la cattura ne "
		              "monterebbe un secondo, e l'utente guarderebbe uno schermo VUOTO.  "
		              "ExecStart in vigore: %s",
		              unita, vigore);
		return FALSE;
	}

	if (kde) {
		registro_dice(REG_SESSIONE,
		              "⭐ la sessione Plasma nascera' con UN'uscita sola, %ux%u, e lo "
		              "chiede il PROGRAMMA (%s).  ⚠ Con `--virtual` la misura non "
		              "cambiera' piu' finche' la sessione vive.  ExecStart in vigore: %s",
		              larghezza, altezza, percorso, vigore);
		return TRUE;
	}

	registro_dice(REG_SESSIONE,
	              "⭐ la sessione nascera' SENZA monitor propri, e lo chiede il PROGRAMMA "
	              "(%s): l'unico monitor sara' quello che monta la nostra cattura, ed e' "
	              "li' che GNOME mette la barra e la dock.  ExecStart in vigore: %s",
	              percorso, vigore);
	return TRUE;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ FASE 14 — LA CARTELLA DI labwc PER LXQt: NOSTRA, e riscritta a ogni
 *      nascita (I7: la protezione sta nel programma, non in un file che si
 *      può perdere o che qualcuno ha già scritto male).
 *
 * ⛔ PERCHE' NON `~/.config/labwc`: lo script upstream ci COPIA, una volta
 *    sola (`if [ ! -d … ]`), un `autostart` che lancia
 *    `swayidle -w timeout 300 "wlopm --off *"` — l'uscita spenta a 5 minuti,
 *    cioè la cattura che riceve `failed` (`STUDI.md` §lxqt §6.2).  E l'`rc.xml`
 *    che propone lega `W-l` a `lxqt-leave --lockscreen` (§5): labwc mangerebbe
 *    il tasto.  ⇒ Una cartella che non scriviamo noi non la controlliamo.
 * ⭐ Con `-C` labwc guarda SOLO questa cartella (`[R]` labwc 0.8.3
 *    `src/common/dir.c:151-157`): quel che l'utente ha in `~/.config/labwc` e
 *    in `/etc/xdg/labwc` non entra.
 *
 * I due file, e perché sono così corti:
 *   · `rc.xml` — solo `<decoration>server</decoration>`, che è quel che LXQt
 *     spedisce e che `STUDI.md` §lxqt §7 dice di non toccare (una barra sola,
 *     nessun lampo).  ⭐ Le scorciatoie di serie di labwc (`<default/>`,
 *     `[R]` `src/config/rcxml.c:1013`, `include/config/default-bindings.h`),
 *     e fra quelle **non c'è** nessun blocco schermo — `W-l` resta
 *     dell'utente; ⭐ FASE 15, D-007: PIU' la scorciatoia che riporta dentro
 *     le finestre (`SESSIONE_LABWC_TASTIERA`).  ⛔ Il `<default/>` e'
 *     obbligatorio: con UNA sola `<keybind>` labwc non carica piu' quelle
 *     di serie (`rcxml.c:1685-1687`);
 *   · `autostart` — VUOTO di proposito, con la ragione scritta dentro:
 *     `lxqt-session` avvia da sé i suoi moduli da `/etc/xdg/autostart`, e
 *     quel che LXQt ci metterebbe (swayidle, swaybg) o spegne l'uscita o non
 *     serve.
 *
 * Torna la cartella, o NULL (detto nel registro).
 */
static char *scrivi_config_labwc_lxqt(const char *runtime)
{
	g_autofree char *cartella = NULL;
	g_autofree char *rc = NULL;
	g_autofree char *autostart = NULL;
	g_autoptr(GError) sbaglio = NULL;

	if (!runtime || !*runtime) {
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: XDG_RUNTIME_DIR non impostata — non so dove scrivere "
		              "la configurazione di labwc");
		return NULL;
	}
	cartella = g_build_filename(runtime, "remotix", "labwc-lxqt", NULL);
	rc = g_build_filename(cartella, "rc.xml", NULL);
	autostart = g_build_filename(cartella, "autostart", NULL);

	if (g_mkdir_with_parents(cartella, 0700) != 0 ||
	    !g_file_set_contents(rc,
	                         "<?xml version=\"1.0\"?>\n"
	                         "<!-- REMOTIX: scritto a ogni nascita della sessione "
	                         "LXQt, non modificare.\n"
	                         "     <keyboard>: le scorciatoie di serie di labwc "
	                         "(<default/>, senza blocco schermo) piu' "
	                         SESSIONE_LABWC_TASTO " (riporta dentro le finestre). -->\n"
	                         "<labwc_config>\n"
	                         "  <core>\n"
	                         "    <decoration>server</decoration>\n"
	                         "  </core>\n"
	                         /* ⭐ FASE 15, D-007: le scorciatoie di serie
	                          *    (`<default/>`) PIU' la nostra — vedi
	                          *    `SESSIONE_LABWC_TASTIERA`. */
	                         SESSIONE_LABWC_TASTIERA
	                         "</labwc_config>\n",
	                         -1, &sbaglio) ||
	    !g_file_set_contents(autostart,
	                         "# REMOTIX: scritto a ogni nascita della sessione LXQt, "
	                         "non modificare.\n"
	                         "# VUOTO DI PROPOSITO: niente swayidle/wlopm (spegnerebbero "
	                         "l'uscita\n"
	                         "# catturata); i moduli li avvia lxqt-session da "
	                         "/etc/xdg/autostart.\n",
	                         -1, &sbaglio)) {
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: configurazione di labwc NON scritta in %s (%s) — non "
		              "faccio nascere la sessione: senza la NOSTRA cartella labwc "
		              "leggerebbe quella dell'utente, dove lo script di LXQt mette "
		              "swayidle a spegnere l'uscita dopo 5 minuti",
		              cartella, sbaglio ? sbaglio->message : g_strerror(errno));
		return NULL;
	}
	registro_dice(REG_SESSIONE,
	              "⭐ LXQt: configurazione di labwc in %s — rc.xml senza blocco "
	              "schermo, autostart vuoto (niente swayidle/wlopm)",
	              cartella);
	return g_steal_pointer(&cartella);
}

/*
 * ⭐⭐ FASE 14, incremento 3 — LO SFONDO DI LXQt NASCE DELLA MISURA DEL CLIENTE.
 *
 * `[M]` 24 set 2026: `labwc` headless nasce con `HEADLESS-1 1280x720`, e la
 * misura del cliente gliela dà `wlr_misura_chiedi()` (cattura.c) ~200 ms dopo;
 * ma `pcmanfm-qt --desktop` parte ~160 ms dopo labwc ⇒ GARA: ~1 nascita su 13
 * lo sfondo resta 1280x720 e il resto dello schermo è NERO.
 * `[R]` pcmanfm-qt 2.1.0: la finestra del desktop è ancorata ai quattro lati
 * (`desktopwindow.cpp:202-212`), lo sfondo si fa da `screen->size()` (`:705`)
 * e si rifà SOLO su `resizeEvent` (`:490`; `application.cpp:1050`) ⇒ se la
 * misura arriva nel buco giusto, nessuno lo ridisegna.
 *
 * ⭐ La cura: `lxqt-session` (e quindi pcmanfm-qt) nasce DOPO che l'uscita ha
 *    la misura.  Il client primario di labwc (`-S`) diventa un `sh` che prima
 *    chiama `wlr-randr --custom-mode` e poi fa `exec lxqt-session` — stesso
 *    pid, quindi «morto il primario, labwc esce» resta vero.
 * ⛔ `;` e NON `&&`: se `wlr-randr` fallisce la sessione nasce lo stesso, e
 *    resta la richiesta tardiva di sempre (`wlr_misura_chiedi()`, invariata).
 * ⭐ Il nome dell'uscita NON si assume: `wlr-randr` 0.4.1 VUOLE `--output`
 *    per cambiare un modo (`[R]` wlr-randr(1): «This option must be set when
 *    making changes»), e senza argomenti elenca le uscite con il nome come
 *    prima parola della prima riga (`HEADLESS-1 "Headless output 1"`).  ⇒ Si
 *    prende quello; se è vuoto, niente `wlr-randr`.
 * ⚠ Misura 0 (non nota) ⇒ la riga di oggi, senza `sh` davanti.
 * ⚠ Due livelli di citazione: il nostro `sh -c` (quello di `avvia()`) e
 *   `g_shell_parse_argv()` di labwc sul `-S`.  ⇒ `g_shell_quote()` due volte,
 *   e nessuna citazione scritta a mano.
 */
static char *primario_lxqt(uint32_t larghezza, uint32_t altezza)
{
	g_autofree char *copione = NULL;
	g_autofree char *interno = NULL;

	if (larghezza == 0 || altezza == 0) {
		registro_dice(REG_SESSIONE,
		              "⚠ LXQt: misura del cliente non nota (%ux%u) — lxqt-session "
		              "nasce SENZA la misura data prima; resta la richiesta tardiva",
		              larghezza, altezza);
		return g_strdup(SESSIONE_PRIMARIO_LXQT);
	}
	copione = g_strdup_printf(
		"u=$(wlr-randr 2>/dev/null | sed -n '1s/ .*//p'); "
		"if [ -n \"$u\" ]; then "
		"echo \"remotix: uscita $u portata a %ux%u PRIMA di lxqt-session\"; "
		"wlr-randr --output \"$u\" --custom-mode %ux%u; "
		"else echo \"remotix: nessuna uscita da wlr-randr, lxqt-session nasce "
		"senza la misura\"; fi; "
		"exec " SESSIONE_PRIMARIO_LXQT,
		larghezza, altezza, larghezza, altezza);
	interno = g_shell_quote(copione);
	registro_dice(REG_SESSIONE,
	              "⭐ LXQt: la misura del cliente %ux%u si dà all'uscita PRIMA della "
	              "nascita di lxqt-session (wlr-randr nel client primario di labwc)",
	              larghezza, altezza);
	return g_strdup_printf("sh -c %s", interno);
}

/* ⭐ `larghezza`/`altezza`: la tela del cliente.  ⚠ Le usa SOLO il ramo LXQt
 *   (`primario_lxqt()`): GNOME e KDE la misura la prendono dal drop-in, XFCE
 *   dalla richiesta tardiva — identici a prima. */
static gboolean avvia(uint32_t larghezza, uint32_t altezza)
{
	g_auto(GStrv) ambiente = NULL;
	g_autofree char *registro = NULL;
	g_autofree char *riga = NULL;
	g_autoptr(GError) sbaglio = NULL;
	/* `setsid --fork` stacca la sessione dal nostro gruppo di processi: se
	 * REMOTIX viene riavviato, il desktop dell'utente non se ne accorge. */
	char *argv[] = { "setsid", "--fork", "sh", "-c", NULL, NULL };
	int stato = 0;
	/* ⚠ A TRE VIE, e non un ternario annidato: chi aggiunge il quarto desktop
	 *   deve vedere l'elenco, non doverlo districare. */
	const char *comando = SESSIONE_COMANDO_GNOME;
	/* ⭐ FASE 14 — la riga di LXQt si compone (la cartella di `-C` sta sotto
	 *    `XDG_RUNTIME_DIR`): vive qui, e `comando` la punta. */
	g_autofree char *comando_lxqt = NULL;

	if (e_kde())
		comando = SESSIONE_COMANDO_KDE;
	else if (e_xfce())
		comando = SESSIONE_COMANDO_XFCE;
	else if (e_lxqt()) {
		g_autofree char *cartella = scrivi_config_labwc_lxqt(g_getenv("XDG_RUNTIME_DIR"));

		if (!cartella)
			return FALSE;
		/* ⚠ `SESSIONE_PROCESSO_XFCE` è `labwc`: il compositore di FAMIGLIA,
		 *   lo stesso eseguibile — il nome della costante è della fase 13. */
		g_autofree char *primario = primario_lxqt(larghezza, altezza);
		g_autofree char *primario_citato = g_shell_quote(primario);

		comando_lxqt = g_strdup_printf("exec " SESSIONE_PROCESSO_XFCE " -C '%s' -S %s",
		                               cartella, primario_citato);
		comando = comando_lxqt;
	}

	ambiente = componi_ambiente();
	if (!ambiente)
		return FALSE;

	/*
	 * ⛔⭐ IL REGISTRO DELLA SESSIONE NON PUO' STARE IN `XDG_RUNTIME_DIR` — 16
	 *     agosto 2026, e la ragione e' che quella cartella **muore con la
	 *     sessione**: quando il gestore d'utente si spegne, logind la porta via.
	 *
	 * ⇒ Il caso in cui quel registro serve di piu' — *«la sessione e' partita e
	 *   e' morta subito, perche'?»* — e' esattamente il caso in cui non c'e'
	 *   piu'.  `[M]` Cercandolo dopo un avvio fallito si trovava un file vuoto o
	 *   nessun file.
	 *
	 * ⚠ `/tmp` e' del sistema e non dell'utente: sopravvive al gestore, e il
	 *   nome porta l'uid perche' due utenti non si sovrascrivano a vicenda.
	 */
	registro = g_strdup_printf("/tmp/remotix-sessione-%ld.log", (long)getuid());
	riga = g_strdup_printf("exec >>'%s' 2>&1; %s", registro, comando);
	argv[4] = riga;

	registro_dice(REG_SESSIONE, "avvio la sessione grafica: %s (il suo registro va in %s)",
	              comando, registro);
	if (!g_spawn_sync(g_get_home_dir(), argv, ambiente, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL,
	                  NULL, &stato, &sbaglio) ||
	    !g_spawn_check_wait_status(stato, &sbaglio)) {
		registro_dice(REG_SESSIONE, "⛔ la sessione non e' partita: %s",
		              sbaglio ? sbaglio->message : "senza motivo");
		return FALSE;
	}
	return TRUE;
}

/* `org.gnome.SessionManager.Logout`: 0 chiede conferma, 1 no, 2 forza. */
static gboolean esci_gnome(guint32 modo)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(NULL);
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GError) sbaglio = NULL;

	if (!bus)
		return FALSE;
	risposta = g_dbus_connection_call_sync(
		bus, "org.gnome.SessionManager", "/org/gnome/SessionManager",
		"org.gnome.SessionManager", "Logout", g_variant_new("(u)", modo), NULL,
		G_DBUS_CALL_FLAGS_NONE, ATTESA_RISPOSTA_MS, NULL, &sbaglio);
	if (!risposta)
		registro_dice(REG_SESSIONE, "⛔ Logout(%u) non e' passato: %s", modo,
		              sbaglio ? sbaglio->message : "senza motivo");
	return risposta != NULL;
}

/*
 * ⛔ «Inattiva» e non «non piu' attiva»: `is-active` passa per `deactivating`, e
 *    ripartire li' dentro e' un'altra prima esecuzione (`FASI.md` §00-ambiente,
 *    difetto 4 della fase 0).  E si guardano DUE cose — l'unita' e il processo —
 *    perche' `Logout` puo' lasciare il gestore vivo.
 */
static gboolean unita_ferma(const char *unita)
{
	char *argv[] = { "systemctl", "--user", "is-active", (char *)unita, NULL };
	g_autofree char *stato = chiedi(argv);

	if (!stato)
		return FALSE;
	g_strstrip(stato);
	return g_strcmp0(stato, "inactive") == 0 || g_strcmp0(stato, "failed") == 0 ||
	       g_strcmp0(stato, "unknown") == 0;
}

static gboolean unita_inattiva(void)
{
	/*
	 * ⛔⭐⭐ DUE UNITA', NON UNA — 16 agosto 2026, e la seconda l'ha nominata il
	 *      giornale dell'utente dopo mezza giornata di ipotesi:
	 *
	 *        «Started gnome-session-restart-dbus.service —
	 *         **Restart DBus after GNOME Session shutdown**»
	 *
	 * ⇒ Quando una sessione GNOME finisce, GNOME **riavvia il bus di sessione**.
	 *   Una sessione nuova avviata in quella finestra nasce su un bus che sta per
	 *   essere sostituito, e muore senza scrivere una riga: `[M]` il suo registro
	 *   e' rimasto **vuoto, zero byte**, ed e' il motivo per cui la causa e'
	 *   costata tanto — il difetto cancellava le proprie tracce.
	 *
	 * ⚠ E' la stessa forma di `SESSIONE_UNITA_GESTORE` qui sotto — «inattiva» e
	 *   non «non piu' attiva» — applicata a un secondo pezzo che nessuno aveva
	 *   guardato perche' nessuno sapeva che esistesse.
	 */
	/* ⭐ FASE 12 — su Plasma le due unita' sono il compositore e il target della
	 *    sessione.  ⛔ E serve gia' alla NASCITA, non solo all'uscita: e' la
	 *    guardia contro una seconda Plasma quando KWin ci mette piu' della
	 *    briglia del figlio a farsi vedere sul bus. */
	if (e_kde())
		return unita_ferma(SESSIONE_UNITA_KWIN) && unita_ferma(SESSIONE_UNITA_PLASMA);

	/*
	 * ⛔⛔ FASE 13 — SU XFCE QUESTA GUARDIA NON FALLIREBBE: SPARIREBBE.
	 *
	 * `[M]` 20 set 2026, dentro `rete11-xfce`: `systemctl --user is-active` su
	 * un'unità **che non esiste** risponde **`inactive`**, codice 4.  E
	 * `unita_ferma()` qui sopra accetta `inactive` ⇒ su XFCE, dove unità non
	 * ce n'è nessuna, la domanda risponderebbe **sì sempre**: la protezione
	 * contro una seconda sessione — pagata il 16 agosto 2026 — non darebbe un
	 * rosso, non darebbe una riga, semplicemente non ci sarebbe piu'.
	 *
	 * ⇒ Si guarda un FATTO, e ce ne vogliono due perche' nessuno dei due basta:
	 *   il nome sul bus può essere già sparito mentre il compositore sta ancora
	 *   morendo, e un `labwc` può esistere un istante prima di prendere il nome.
	 */
	/* ⭐ FASE 14 — su LXQt il fatto è lo stesso processo, `labwc`: unità non ce
	 *    n'è, e la trappola dell'`inactive` per un'unità inesistente è identica.
	 * ⚠ Una sola cosa: un `labwc` mio conta anche se è di un altro desktop —
	 *   ma «un desktop per macchina» (§0.6) lo esclude. */
	if (e_xfce() || e_lxqt()) {
		int quanti = processi_miei(SESSIONE_PROCESSO_XFCE);

		if (quanti < 0) {
			/* ⛔ «non ho potuto guardare» non è «è libero»: si dice di no,
			 *    e chi chiama riprova. */
			registro_dice(REG_SESSIONE,
			              "⛔ %s: non riesco a leggere /proc, quindi non so se "
			              "c'è ancora un " SESSIONE_PROCESSO_XFCE " mio — e «non "
			              "lo so» qui vale «no»",
			              nome_desktop());
			return FALSE;
		}
		if (quanti > 0) {
			registro_dice(REG_SESSIONE,
			              "%s: ci sono ancora %d " SESSIONE_PROCESSO_XFCE
			              " miei: la sessione di prima non è finita",
			              nome_desktop(), quanti);
			return FALSE;
		}
		return TRUE;
	}

	return unita_ferma(SESSIONE_UNITA_GESTORE) && unita_ferma(SESSIONE_UNITA_DBUS);
}

static gboolean aspetta_che_finisca(void)
{
	gint64 scadenza = g_get_monotonic_time() + (gint64) ATTESA_USCITA_MS * 1000;

	while (g_get_monotonic_time() < scadenza) {
		g_usleep(CADENZA_CONTROLLO_MS * 1000);
		if (!sessione_viva() && unita_inattiva()) {
			char *pulisci[] = { "systemctl", "--user", "reset-failed", NULL };

			esegui(pulisci);
			return TRUE;
		}
	}
	return FALSE;
}

/*
 * ⭐ FASE 12 — l'uscita di Plasma, portata da v1 (`fondamenta/remotix-c/src/sessione.c`
 * 725-770) e misurata la' l'8 agosto 2026 (`STUDI.md` §kde §6.5, M9).
 *
 *   ordinata   `org.kde.Shutdown.logout()` — ⛔ non `LogoutPrompt`, che chiede
 *              una conferma che in una sessione non presidiata nessuno da'
 *   a forza    `StopUnit("plasma-workspace.target", "fail")` — ⛔ `Logout(2)`
 *              su KDE non esiste; e' quel che fa `plasma-shutdown` alla fine
 */
static gboolean esci_kde(gboolean a_forza)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(NULL);
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GError) sbaglio = NULL;

	if (!bus)
		return FALSE;
	if (a_forza)
		risposta = g_dbus_connection_call_sync(
			bus, "org.freedesktop.systemd1", "/org/freedesktop/systemd1",
			"org.freedesktop.systemd1.Manager", "StopUnit",
			g_variant_new("(ss)", SESSIONE_UNITA_PLASMA, "fail"), NULL,
			G_DBUS_CALL_FLAGS_NONE, ATTESA_RISPOSTA_MS, NULL, &sbaglio);
	else
		risposta = g_dbus_connection_call_sync(
			bus, "org.kde.Shutdown", "/Shutdown", "org.kde.Shutdown", "logout", NULL,
			NULL, G_DBUS_CALL_FLAGS_NONE, ATTESA_RISPOSTA_MS, NULL, &sbaglio);
	if (!risposta)
		registro_dice(REG_SESSIONE, "⛔ l'uscita di Plasma (%s) non e' passata: %s",
		              a_forza ? "StopUnit a forza" : "Shutdown.logout",
		              sbaglio ? sbaglio->message : "senza motivo");
	return risposta != NULL;
}

/*
 * ⭐ FASE 13 — L'USCITA DI XFCE.  Due mosse, e la seconda non è `StopUnit`.
 *
 * ⛔ Su GNOME e su KDE la forza è systemd, che ferma un'unità.  Qui unità non
 *    ce n'è: la forza è un segnale al processo del compositore.
 * ⭐ E basta quello, perche' la riga di avvio porta `--session`: `xfce4-session`
 *   è il client primario di labwc ⇒ morto labwc, la sessione va con lui, e
 *   morto `xfce4-session`, labwc esce da sé.  `[M]` 20 set 2026, provato dentro
 *   `rete11-xfce`: ucciso `labwc`, di `xfce4-session`, del pannello e della
 *   scrivania non è rimasto niente.
 * ⚠ Il nome sul bus è `org.xfce.SessionManager`, l'interfaccia è
 *   `org.xfce.Session.Manager` — con un punto in piu'.  Confonderli dà
 *   «metodo sconosciuto», che somiglia a «la sessione non risponde».
 */
static gboolean esci_xfce(void)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(NULL);
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GError) sbaglio = NULL;

	if (!bus)
		return FALSE;
	/* (show_dialog, allow_save) — tutt'e due falsi: nessuno può rispondere a un
	 * dialogo dentro una sessione remota che stiamo chiudendo. */
	risposta = g_dbus_connection_call_sync(
		bus, SESSIONE_BUS_XFCE, "/org/xfce/SessionManager",
		"org.xfce.Session.Manager", "Logout", g_variant_new("(bb)", FALSE, FALSE),
		NULL, G_DBUS_CALL_FLAGS_NO_AUTO_START, ATTESA_RISPOSTA_MS, NULL, &sbaglio);
	if (!risposta) {
		registro_dice(REG_SESSIONE,
		              "⚠ XFCE: Logout non è passato (%s)",
		              sbaglio ? sbaglio->message : "senza motivo");
		return FALSE;
	}
	return TRUE;
}

static gboolean uccidi_xfce(void)
{
	g_autoptr(GDir) proc = g_dir_open("/proc", 0, NULL);
	const char *voce;
	uid_t mio = getuid();
	int colpiti = 0;

	if (!proc)
		return FALSE;
	while ((voce = g_dir_read_name(proc))) {
		g_autofree char *comm = NULL;
		g_autofree char *percorso = NULL;
		GStatBuf st;

		if (!g_ascii_isdigit(voce[0]))
			continue;
		percorso = g_build_filename("/proc", voce, "comm", NULL);
		if (g_stat(percorso, &st) != 0 || st.st_uid != mio)
			continue;
		if (!g_file_get_contents(percorso, &comm, NULL, NULL))
			continue;
		g_strstrip(comm);
		if (g_strcmp0(comm, SESSIONE_PROCESSO_XFCE) != 0)
			continue;
		/* ⚠ SIGTERM, non SIGKILL: labwc chiude i suoi client, e un SIGKILL
		 *   lascerebbe dietro proprio quel che C7 va a cercare. */
		if (kill((pid_t) g_ascii_strtoll(voce, NULL, 10), SIGTERM) == 0)
			colpiti++;
	}
	registro_dice(REG_SESSIONE,
	              "%s: mandato SIGTERM a %d " SESSIONE_PROCESSO_XFCE " miei", nome_desktop(),
	              colpiti);
	return colpiti > 0;
}

/*
 * ⭐ FASE 14 — L'USCITA DI LXQt.  Le stesse due mosse di XFCE, con un altro
 *    bersaglio D-Bus per la prima (`STUDI.md` §lxqt §3.4).
 *
 *   ordinata   `org.lxqt.session.logout()` su `/LXQtSession` — ⛔ mai
 *              `lxqt-leave --logout`, che apre una conferma modale.
 *              ✅ Il logout di LXQt non consulta inibitori, non mostra niente,
 *              non si annulla (`STUDI.md` §lxqt §3.3, `[✗]`)
 *   a forza    SIGTERM a labwc (`uccidi_xfce`): con `-S` `lxqt-session` è il
 *              client primario, e morto labwc va via con lui
 *
 * ⛔⛔ E SI MANDA SENZA ASPETTARE RISPOSTA, perche' risposta non ne arriva:
 *     `logout()` è `Q_NOREPLY` (`[R]` lxqt-session 2.1.1
 *     `sessiondbusadaptor.h`).  Una chiamata sincrona resterebbe appesa fino
 *     al tetto e direbbe «non è passata» a un logout riuscito — la forma E8
 *     rovesciata.  ⇒ Messaggio con `NO_REPLY_EXPECTED`, e il verdetto lo dà
 *     `aspetta_che_finisca()`, cioe' un fatto.
 * [?] Che `logout()` porti davvero `lxqt-session` all'uscita (e quindi labwc)
 *     entro i 10 s di `ATTESA_USCITA_MS` è da misurare: se no si cade nella
 *     forza, e il registro lo dice.
 */
static gboolean esci_lxqt(void)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(NULL);
	g_autoptr(GDBusMessage) messaggio = NULL;
	g_autoptr(GError) sbaglio = NULL;

	if (!bus)
		return FALSE;
	messaggio = g_dbus_message_new_method_call(SESSIONE_BUS_LXQT, "/LXQtSession",
	                                           SESSIONE_BUS_LXQT, "logout");
	g_dbus_message_set_flags(messaggio, G_DBUS_MESSAGE_FLAGS_NO_REPLY_EXPECTED |
	                                            G_DBUS_MESSAGE_FLAGS_NO_AUTO_START);
	if (!g_dbus_connection_send_message(bus, messaggio, G_DBUS_SEND_MESSAGE_FLAGS_NONE, NULL,
	                                    &sbaglio) ||
	    !g_dbus_connection_flush_sync(bus, NULL, &sbaglio)) {
		registro_dice(REG_SESSIONE, "⚠ LXQt: logout() non è partito (%s)",
		              sbaglio ? sbaglio->message : "senza motivo");
		return FALSE;
	}
	return TRUE;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ FASE 15, D-015/D-017 (R1, R2) — DOPO LA SESSIONE REMOTA, IL GESTORE
 *      D'UTENTE TORNA COM'ERA.
 *
 * ⛔ IL BUCO, trovato dalla revisione della bonifica: quel che il prodotto
 *    mette nel GESTORE D'UTENTE di systemd non se ne andava mai —
 *    · i drop-in in `$XDG_RUNTIME_DIR/systemd/user.control/` (la Shell
 *      `--headless`, KWin `--virtual`, `xfconfd` con la cartella della
 *      sessione);
 *    · le variabili che `gnome-session`/`startplasma`/labwc esportano nel
 *      gestore dall'ambiente che componiamo noi (`DCONF_PROFILE`,
 *      `XDG_CONFIG_DIRS`, `XCURSOR_THEME`=il tema invisibile, …).
 *    E col linger acceso (`provisiona.sh`) il gestore sopravvive alla
 *    sessione: l'utente che poi entra AL MONITOR ereditava tutto — su XFCE un
 *    «Esci» che non esce (`WaylandLogoutCommand=/bin/true` bloccata), su GNOME
 *    il dconf in memoria al posto del suo.
 *
 * ⭐ LA CURA, in due gesti:
 *   · `sessione_fotografa_gestore()`, alla nascita e PRIMA di toccare
 *     qualunque cosa: il valore di prima di ognuna delle NOSTRE variabili
 *     (`VARIABILI_NOSTRE`) si scrive in `$XDG_RUNTIME_DIR/remotix/
 *     gestore-prima` (c'e' finche' c'e' il gestore);
 *   · `sessione_sgombera_gestore()`, quando la sessione remota e' finita (fine
 *     vista dal figlio, `sessione_termina`, uscita del figlio) e anche
 *     all'avvio del figlio e alla nascita (per quel che un crash ha lasciato):
 *     via i nostri drop-in + `daemon-reload`; le nostre variabili rimesse come
 *     erano (o tolte, se non c'erano) con `UnsetAndSetEnvironment`; e
 *     `xfconfd` fatto ripartire se aveva la cartella della sessione.
 *   ⛔ SOLO a sessione MORTA: con la sessione viva si porterebbe via il
 *      terreno a un desktop che lavora.
 *   ⚠ Senza la fotografia (un gestore nato con un prodotto di prima) si
 *     tolgono solo le variabili che portano il nostro segno (`remotix` nel
 *     valore): si dice, ed e' il ripiego.
 *
 * ⚠ Quel che resta, dichiarato: se il figlio non torna mai (la macchina resta
 *   senza client e l'utente entra al monitor dopo un crash del figlio), lo
 *   sgombero lo fara' il prossimo figlio: il server da root non parla al
 *   gestore d'utente.
 */
static const char *const VARIABILI_NOSTRE[] = {
	"DCONF_PROFILE", "XDG_CONFIG_DIRS", "XDG_DATA_DIRS", "XDG_MENU_PREFIX",
	"XCURSOR_THEME", "XCURSOR_SIZE", "XCURSOR_PATH", "XDG_CURRENT_DESKTOP",
	"XDG_SESSION_DESKTOP", "XDG_SESSION_TYPE", "SHELL", "LANG", "PATH",
	"QT_QPA_PLATFORM", "QT_QPA_PLATFORMTHEME", "GDK_BACKEND", "XFCE4_SESSION_COMPOSITOR",
	"WLR_BACKENDS", "WLR_LIBINPUT_NO_DEVICES", "WLR_RENDER_DRM_DEVICE",
	"LABWC_UPDATE_ACTIVATION_ENV", "WAYLAND_DISPLAY", "DISPLAY", NULL
};

/* { cartella del drop-in, nome } — tutti e soli i nostri */
static const char *const DROPIN_NOSTRI[][2] = {
	{ SESSIONE_UNITA_SHELL ".d", "zz-remotix-monitor.conf" },
	{ SESSIONE_UNITA_KWIN ".d", "zz-remotix-monitor.conf" },
	{ "xfconfd.service.d", "zz-remotix-sessione.conf" },
};

static char *gestore_prima_percorso(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	return runtime && *runtime ? g_build_filename(runtime, "remotix", "gestore-prima", NULL)
	                           : NULL;
}

/* L'ambiente del gestore, {nome: valore}, chiesto a lui (proprieta'
 * `Environment` di `org.freedesktop.systemd1.Manager`: stringhe crude, senza
 * le virgolette di `show-environment`).  NULL se non risponde. */
static GHashTable *ambiente_del_gestore(GDBusConnection *bus)
{
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GVariant) dentro = NULL;
	g_autofree const char **voci = NULL;
	GHashTable *amb;

	risposta = g_dbus_connection_call_sync(
		bus, "org.freedesktop.systemd1", "/org/freedesktop/systemd1",
		"org.freedesktop.DBus.Properties", "Get",
		g_variant_new("(ss)", "org.freedesktop.systemd1.Manager", "Environment"),
		G_VARIANT_TYPE("(v)"), G_DBUS_CALL_FLAGS_NONE, 5000, NULL, NULL);
	if (!risposta)
		return NULL;
	g_variant_get(risposta, "(v)", &dentro);
	if (!g_variant_is_of_type(dentro, G_VARIANT_TYPE_STRING_ARRAY))
		return NULL;
	amb = g_hash_table_new_full(g_str_hash, g_str_equal, g_free, g_free);
	voci = g_variant_get_strv(dentro, NULL);
	for (int i = 0; voci[i]; i++) {
		const char *uguale = strchr(voci[i], '=');

		if (uguale)
			g_hash_table_insert(amb, g_strndup(voci[i], uguale - voci[i]),
			                    g_strdup(uguale + 1));
	}
	return amb;
}

void sessione_fotografa_gestore(void)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(NULL);
	g_autoptr(GHashTable) amb = NULL;
	g_autoptr(GKeyFile) foto = g_key_file_new();
	g_autofree char *percorso = gestore_prima_percorso();
	g_autofree char *cartella = NULL;
	g_autoptr(GError) sbaglio = NULL;

	if (!bus || !percorso || !(amb = ambiente_del_gestore(bus))) {
		registro_dice(REG_SESSIONE,
		              "⚠ R1/R2: non ho potuto fotografare l'ambiente del gestore d'utente — "
		              "alla fine della sessione togliero' solo le variabili col nostro segno");
		return;
	}
	for (int i = 0; VARIABILI_NOSTRE[i]; i++) {
		const char *v = g_hash_table_lookup(amb, VARIABILI_NOSTRE[i]);

		if (v)
			g_key_file_set_string(foto, "prima", VARIABILI_NOSTRE[i], v);
		else
			g_key_file_set_boolean(foto, "assenti", VARIABILI_NOSTRE[i], TRUE);
	}
	cartella = g_path_get_dirname(percorso);
	if (g_mkdir_with_parents(cartella, 0700) != 0 ||
	    !g_key_file_save_to_file(foto, percorso, &sbaglio))
		registro_dice(REG_SESSIONE, "⚠ R1/R2: fotografia del gestore NON scritta (%s): %s",
		              percorso, sbaglio ? sbaglio->message : g_strerror(errno));
	else
		registro_dice(REG_SESSIONE,
		              "⭐ R1/R2: fotografato l'ambiente del gestore d'utente PRIMA della "
		              "sessione (%s): alla fine lo rimetto com'era",
		              percorso);
}

void sessione_sgombera_gestore(const char *perche)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	g_autoptr(GDBusConnection) bus = NULL;
	g_autoptr(GHashTable) amb = NULL;
	g_autoptr(GKeyFile) foto = g_key_file_new();
	g_autofree char *percorso = gestore_prima_percorso();
	g_autoptr(GPtrArray) togli = g_ptr_array_new_with_free_func(g_free);
	g_autoptr(GPtrArray) metti = g_ptr_array_new_with_free_func(g_free);
	g_autoptr(GString) detto = g_string_new(NULL);
	gboolean con_foto;
	int drop = 0;
	gboolean xfconfd = FALSE;
	char *ricarica[] = { "systemctl", "--user", "daemon-reload", NULL };
	char *riparti[] = { "systemctl", "--user", "try-restart", "xfconfd.service", NULL };

	if (!runtime || !*runtime)
		return;
	if (sessione_viva()) {
		registro_dettaglio(REG_SESSIONE,
		                   "R1/R2 (%s): la sessione e' VIVA — non sgombero il gestore "
		                   "d'utente sotto un desktop che lavora",
		                   perche);
		return;
	}

	/* 1. i drop-in: tutti e soli i nostri */
	for (guint i = 0; i < G_N_ELEMENTS(DROPIN_NOSTRI); i++) {
		g_autofree char *cartella = g_build_filename(runtime, "systemd", "user.control",
		                                             DROPIN_NOSTRI[i][0], NULL);
		g_autofree char *file = g_build_filename(cartella, DROPIN_NOSTRI[i][1], NULL);

		if (g_unlink(file) == 0) {
			drop++;
			xfconfd |= g_str_has_prefix(DROPIN_NOSTRI[i][0], "xfconfd");
			g_string_append_printf(detto, " %s/%s", DROPIN_NOSTRI[i][0],
			                       DROPIN_NOSTRI[i][1]);
			g_rmdir(cartella); /* solo se vuota */
		}
	}
	if (drop)
		esegui(ricarica);
	if (xfconfd)
		esegui(riparti);

	/* 2. le variabili: com'erano, o col solo nostro segno senza fotografia */
	bus = sessione_bus(NULL);
	amb = bus ? ambiente_del_gestore(bus) : NULL;
	con_foto = percorso && g_key_file_load_from_file(foto, percorso, G_KEY_FILE_NONE, NULL);
	for (int i = 0; amb && VARIABILI_NOSTRE[i]; i++) {
		const char *nome = VARIABILI_NOSTRE[i];
		const char *ora = g_hash_table_lookup(amb, nome);
		g_autofree char *prima = con_foto ? g_key_file_get_string(foto, "prima", nome, NULL)
		                                  : NULL;
		gboolean era_assente = con_foto && g_key_file_get_boolean(foto, "assenti", nome, NULL);

		if (con_foto) {
			if (prima && g_strcmp0(prima, ora) != 0)
				g_ptr_array_add(metti, g_strdup_printf("%s=%s", nome, prima));
			else if (era_assente && ora)
				g_ptr_array_add(togli, g_strdup(nome));
		} else if (ora && strstr(ora, "remotix")) {
			g_ptr_array_add(togli, g_strdup(nome));
		}
	}
	if (togli->len || metti->len) {
		g_autoptr(GVariant) r = NULL;
		g_autoptr(GError) sbaglio = NULL;

		g_ptr_array_add(togli, NULL);
		g_ptr_array_add(metti, NULL);
		r = g_dbus_connection_call_sync(
			bus, "org.freedesktop.systemd1", "/org/freedesktop/systemd1",
			"org.freedesktop.systemd1.Manager", "UnsetAndSetEnvironment",
			g_variant_new("(^as^as)", (char **) togli->pdata, (char **) metti->pdata),
			NULL, G_DBUS_CALL_FLAGS_NONE, 5000, NULL, &sbaglio);
		if (r) {
			for (guint i = 0; i + 1 < togli->len; i++)
				g_string_append_printf(detto, " -%s", (char *) g_ptr_array_index(togli, i));
			for (guint i = 0; i + 1 < metti->len; i++) {
				const char *m = g_ptr_array_index(metti, i);

				g_string_append_printf(detto, " ~%.*s", (int) (strchr(m, '=') - m), m);
			}
		} else {
			registro_dice(REG_SESSIONE,
			              "⛔ R1/R2 (%s): le variabili del gestore d'utente NON si "
			              "rimettono (%s) — l'utente al monitor erediterebbe le nostre",
			              perche, sbaglio ? sbaglio->message : "senza motivo");
		}
	}
	if (con_foto && amb)
		g_unlink(percorso); /* consumata: la prossima nascita ne fa un'altra */

	if (detto->len)
		registro_dice(REG_SESSIONE,
		              "⭐ R1/R2 (%s): il gestore d'utente torna com'era —%s%s%s",
		              perche, detto->str, xfconfd ? " · xfconfd ripartito" : "",
		              con_foto ? "" : " (⚠ senza fotografia: tolte solo le variabili col "
		                              "nostro segno)");
	else
		registro_dettaglio(REG_SESSIONE,
		                   "R1/R2 (%s): nel gestore d'utente non c'era niente di nostro",
		                   perche);
}

static bool termina_davvero(void);

/* ⭐ R1/R2: una sessione chiusa da noi lascia il gestore d'utente com'era. */
bool sessione_termina(void)
{
	bool uscita = termina_davvero();

	if (uscita)
		sessione_sgombera_gestore("sessione terminata dal prodotto");
	return uscita;
}

static bool termina_davvero(void)
{
	if (!sessione_viva()) {
		registro_dice(REG_SESSIONE, "non c'era nessuna sessione da fermare");
		return false;
	}

	if (e_xfce()) {
		registro_dice(REG_SESSIONE,
		              "chiedo alla sessione XFCE di uscire "
		              "(org.xfce.Session.Manager.Logout)");
		if (esci_xfce() && aspetta_che_finisca()) {
			registro_dice(REG_SESSIONE, "la sessione grafica e' uscita");
			return true;
		}
		registro_dice(REG_SESSIONE,
		              "⚠ la sessione non esce: la chiudo a forza (SIGTERM a "
		              SESSIONE_PROCESSO_XFCE "), cio' che non e' stato salvato va "
		              "perduto — ⛔ e qui la forza non è systemd: su XFCE il "
		              "compositore non è un'unità");
		if (uccidi_xfce() && aspetta_che_finisca()) {
			registro_dice(REG_SESSIONE, "la sessione grafica e' uscita, a forza");
			return true;
		}
		registro_dice(REG_SESSIONE, "⛔ la sessione grafica non e' uscita nemmeno a forza");
		return false;
	}

	/* ⭐ FASE 14 — LXQt: la forma di XFCE, col bersaglio di LXQt davanti. */
	if (e_lxqt()) {
		registro_dice(REG_SESSIONE,
		              "chiedo alla sessione LXQt di uscire (org.lxqt.session.logout, "
		              "senza attendere risposta: è Q_NOREPLY)");
		if (esci_lxqt() && aspetta_che_finisca()) {
			registro_dice(REG_SESSIONE, "la sessione grafica e' uscita");
			return true;
		}
		registro_dice(REG_SESSIONE,
		              "⚠ la sessione non esce: la chiudo a forza (SIGTERM a "
		              SESSIONE_PROCESSO_XFCE "), cio' che non e' stato salvato va "
		              "perduto — ⛔ e qui la forza non è systemd: su LXQt il "
		              "compositore non è un'unità");
		if (uccidi_xfce() && aspetta_che_finisca()) {
			registro_dice(REG_SESSIONE, "la sessione grafica e' uscita, a forza");
			return true;
		}
		registro_dice(REG_SESSIONE, "⛔ la sessione grafica non e' uscita nemmeno a forza");
		return false;
	}

	if (e_kde()) {
		registro_dice(REG_SESSIONE,
		              "chiedo alla sessione Plasma di uscire (org.kde.Shutdown.logout)");
		if (esci_kde(FALSE) && aspetta_che_finisca()) {
			registro_dice(REG_SESSIONE, "la sessione grafica e' uscita");
			return true;
		}
		registro_dice(REG_SESSIONE,
		              "⚠ la sessione non esce: la chiudo a forza (StopUnit %s), cio' "
		              "che non e' stato salvato va perduto",
		              SESSIONE_UNITA_PLASMA);
		if (esci_kde(TRUE) && aspetta_che_finisca()) {
			registro_dice(REG_SESSIONE, "la sessione grafica e' uscita, a forza");
			return true;
		}
		registro_dice(REG_SESSIONE, "⛔ la sessione grafica non e' uscita nemmeno a forza");
		return false;
	}

	registro_dice(REG_SESSIONE, "chiedo alla sessione grafica di uscire (Logout 1)");
	if (esci_gnome(1) && aspetta_che_finisca()) {
		registro_dice(REG_SESSIONE, "la sessione grafica e' uscita");
		return true;
	}

	registro_dice(REG_SESSIONE,
	              "⚠ la sessione non esce: la chiudo a forza (Logout 2), cio' che non "
	              "e' stato salvato va perduto");
	if (esci_gnome(2) && aspetta_che_finisca()) {
		registro_dice(REG_SESSIONE, "la sessione grafica e' uscita, a forza");
		return true;
	}

	registro_dice(REG_SESSIONE, "⛔ la sessione grafica non e' uscita nemmeno a forza");
	return false;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ LE IMPOSTAZIONI CHE LA SESSIONE DEVE AVERE PRIMA DI NASCERE — fase 5.
 *
 * ⛔ PERCHE' LE METTIAMO NOI, e non stanno in un file di provisioning: e'
 *    l'invariante **I7**.  Una protezione che vive in una riga di
 *    configurazione che qualcuno puo' non applicare non e' una protezione — e
 *    `[M]` il 15 agosto 2026 il provisioning di v1, rieseguito dopo un riavvio,
 *    ha rimesso in piedi lo stato SBAGLIATO e ci e' costato una serata.
 *
 * ⛔⛔ E `g_settings_new()` SU UNO SCHEMA CHE NON C'E' ABORTISCE IL PROCESSO —
 *     non ritorna NULL: chiama `g_error()`.  ⇒ Ogni schema si CERCA prima, e se
 *     manca si scrive una riga e si va avanti.  Un desktop senza
 *     `org.gnome.shell` e' un desktop che non e' GNOME, non un guasto nostro.
 */
struct impostazione {
	const char *schema;
	const char *chiave;
	const char *perche;
};

/* ⛔ Le dodici che Mutter INGOIA e che in headless non servono a niente.
 *
 * `[R]` `org.gnome.mutter.wayland` lega `<Primary><Alt>F1…F12` a
 * `switch-to-session-1…12`, e `keybindings.c` le registra come
 * **`META_KEY_BINDING_NON_MASKABLE`**: nessuna applicazione puo' prenderle,
 * nemmeno chiedendo.  ⚠ In una sessione headless non c'e' NESSUNA console
 * virtuale a cui passare: Mutter le intercetta, prova, fallisce e scrive un
 * avviso.  ⇒ Dodici combinazioni tolte all'utente per niente. */
static const char *SCORCIATOIE_VT[] = { "switch-to-session-1",  "switch-to-session-2",
	                                "switch-to-session-3",  "switch-to-session-4",
	                                "switch-to-session-5",  "switch-to-session-6",
	                                "switch-to-session-7",  "switch-to-session-8",
	                                "switch-to-session-9",  "switch-to-session-10",
	                                "switch-to-session-11", "switch-to-session-12",
	                                NULL };

/*
 * ⛔⛔ E NON BASTA CERCARE LO SCHEMA: VA CERCATA ANCHE LA CHIAVE.
 *
 * `[M]` 15 agosto 2026, e il prezzo e' stato un figlio morto di **segnale 5**
 * (`SIGTRAP`) subito dopo aver scritto il drop-in: GLib, davanti a una chiave
 * che nel suo schema non esiste, chiama `g_error()` — che **aborte il
 * processo**, non ritorna un errore.  ⇒ Una chiave rinominata a monte fra due
 * versioni di GNOME fa morire il figlio, e il sintomo che l'utente vede e'
 * «il desktop non parte», senza nessun rapporto con la chiave.
 *
 * ⚠ Il commento sopra questa funzione lo diceva gia' per gli SCHEMI, e l'ho
 *   scritto io: la lezione e' che una trappola conosciuta a meta' e' una
 *   trappola.  ⇒ Qui si controllano tutte e due, e una chiave che manca e'
 *   una riga di registro, non una morte.
 */
struct schema_aperto {
	GSettings *impostazioni;
	GSettingsSchema *schema;
};

static struct schema_aperto apri_schema(const char *nome)
{
	struct schema_aperto a = { NULL, NULL };
	GSettingsSchemaSource *sorgente = g_settings_schema_source_get_default();

	if (!sorgente)
		return a;
	a.schema = g_settings_schema_source_lookup(sorgente, nome, TRUE);
	if (!a.schema) {
		registro_dice(REG_SESSIONE,
		              "⚠ lo schema «%s» non esiste su questa macchina: non lo tocco "
		              "(e questo NON e' un guasto: e' un desktop diverso)",
		              nome);
		return a;
	}
	a.impostazioni = g_settings_new_full(a.schema, NULL, NULL);
	return a;
}

static void chiudi_schema(struct schema_aperto *a)
{
	g_clear_object(&a->impostazioni);
	g_clear_pointer(&a->schema, g_settings_schema_unref);
}

/* ⛔ Il guardiano: la chiave c'e'?  Se no si dice e si va avanti. */
static gboolean c_e_la_chiave(const struct schema_aperto *a, const char *chiave,
                              const char *schema)
{
	if (!a->impostazioni || !a->schema)
		return FALSE;
	if (g_settings_schema_has_key(a->schema, chiave))
		return TRUE;
	registro_dice(REG_SESSIONE,
	              "⚠ la chiave «%s» non esiste nello schema «%s» di questa "
	              "macchina: non la tocco.  ⛔ E non e' una svista da ignorare — "
	              "senza questo controllo GLib chiamerebbe `g_error()` e il "
	              "processo MORIREBBE (segnale 5), col sintomo «il desktop non "
	              "parte» e nessun rapporto con la chiave",
	              chiave, schema);
	return FALSE;
}

/*
 * ⭐ FASE 15, D-015 — UNA CHIAVE PERMESSA, nel dconf DELL'UTENTE (blocco,
 *    riavvio, sospensione, stand-by: la decisione del 25 set 2026).
 *
 * ⛔ Non con `g_settings_set_*`: il motore di questo processo ha il profilo
 *    della SESSIONE, e scriverebbe nel database in memoria.  Si scrive allo
 *    scrittore dell'utente (`/ca/desrt/dconf/Writer/user`), al percorso che lo
 *    schema dichiara; poi SI RILEGGE con GSettings — cioe' attraverso il
 *    profilo della sessione, cioe' come la leggeranno la Shell e i `gsd-*`:
 *    scritto non e' in vigore finche' non lo si rilegge.
 * ⚠ `valore` puo' essere flottante: lo si prende sempre.
 */
static gboolean gnome_metti_utente(const struct schema_aperto *a, const char *schema,
                                   const char *chiave, GVariant *valore)
{
	g_autoptr(GVariant) v = g_variant_ref_sink(valore);
	g_autoptr(GVariant) riletto = NULL;
	g_autoptr(GError) sbaglio = NULL;
	g_autofree char *percorso = NULL;
	const char *base;

	if (!c_e_la_chiave(a, chiave, schema))
		return FALSE;
	base = g_settings_schema_get_path(a->schema);
	if (!base) {
		registro_dice(REG_SESSIONE, "⛔ lo schema «%s» non ha un percorso: «%s» NON scritta",
		              schema, chiave);
		return FALSE;
	}
	percorso = g_strconcat(base, chiave, NULL);
	if (!dconf_cambia("/ca/desrt/dconf/Writer/user", percorso, v, &sbaglio)) {
		registro_dice(REG_SESSIONE,
		              "⛔ D-015: %s NON scritta nel dconf dell'utente (%s)", percorso,
		              sbaglio ? sbaglio->message : "senza motivo");
		return FALSE;
	}
	riletto = g_settings_get_value(a->impostazioni, chiave);
	if (!riletto || !g_variant_equal(riletto, v)) {
		g_autofree char *atteso = g_variant_print(v, FALSE);
		g_autofree char *letto = riletto ? g_variant_print(riletto, FALSE) : NULL;

		registro_dice(REG_SESSIONE,
		              "⛔ D-015: %s scritta nell'utente (%s) ma la sessione rilegge %s — "
		              "NON e' in vigore",
		              percorso, atteso, letto ? letto : "niente");
		return FALSE;
	}
	{
		g_autofree char *scritto = g_variant_print(v, FALSE);

		registro_dice(REG_SESSIONE,
		              "⭐ D-015: %s = %s nel dconf dell'UTENTE (permessa: blocco, "
		              "riavvio, sospensione, stand-by), RILETTA dalla sessione",
		              percorso, scritto);
	}
	return TRUE;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ FASE 13 — LE LEVE DI XFCE: SCRIVI, RILEGGI, DI' SE È IN VIGORE.
 *
 * È lo schema della cintura del logout (`WaylandLogoutCommand`, qui sotto in
 * `sessione_impostazioni()`) fatto funzione, perché le chiavi adesso sono otto
 * e non una.
 *
 * ⛔⛔ E SI RILEGGE SEMPRE: `xfconf-query` esce con **zero anche quando il
 *     demone rifiuta** — l'API è asincrona, la cache locale risponde per prima
 *     e il valore vecchio torna dopo (`STUDI.md` §xfce §10.6).  ⇒ Lo stato
 *     d'uscita di chi scrive non dice niente: dice il vero solo la rilettura.
 *
 * ⭐ E SCRIVERE PRIMA CHE LA SESSIONE NASCA FUNZIONA — la domanda che questa
 *    funzione doveva superare: `xfconfd` **ha** l'attivazione D-Bus (§10.6), e
 *    `xfconf-query` parla al bus d'utente, che è lo stesso della sessione
 *    (`sessione_viva()`: `labwc` parte senza `dbus-run-session`).  ⇒ La
 *    scrittura sveglia il demone che la sessione troverà già vivo.  `[M]` 20 set
 *    2026: la cintura del logout, scritta prima di `avvia()`, si RILEGGE.
 * ⚠ E vale anche DOPO: le tre componenti toccate qui (`xfce4-session`,
 *   `xfce4-power-manager`, libxfce4ui) sono legate a xfconf e reagiscono alla
 *   modifica a caldo `[R]` (`xfpm-dpms.c` `settings_changed`,
 *   `xfce-screensaver.c:342-346`, il dialogo di logout legge alla creazione).
 *
 * Torna TRUE se la rilettura dà esattamente il valore scritto.
 */
static gboolean xfconf_metti(const char *canale, const char *chiave, const char *tipo,
                             const char *valore, const char *perche)
{
	char *scrivi[] = { "xfconf-query", "-c",       (char *) canale, "-p",
		           (char *) chiave, "-n",       "-t",            (char *) tipo,
		           "-s",            (char *) valore, NULL };
	char *rileggi[] = { "xfconf-query", "-c", (char *) canale, "-p", (char *) chiave, NULL };
	g_autofree char *letto = NULL;

	esegui(scrivi);
	letto = chiedi(rileggi);
	if (letto)
		g_strstrip(letto);
	if (g_strcmp0(letto, valore) == 0) {
		registro_dice(REG_SESSIONE, "⭐ XFCE: %s %s = %s, RILETTA — %s", canale, chiave,
		              valore, perche);
		return TRUE;
	}
	registro_dice(REG_SESSIONE,
	              "⛔ XFCE: %s %s NON è in vigore (scritto «%s», rileggo «%s») — "
	              "quindi NON vale: %s",
	              canale, chiave, valore, letto ? letto : "non lo so", perche);
	return FALSE;
}

/*
 * ⭐ LE VOCI DEL PULSANTE D'AZIONE DEL PANNELLO — decisione dell'utente, 21 set
 *   2026: *«anche in XFCE vanno disabilitate le voci di standby, lockscreen,
 *   reset e spegnimento»*.
 *
 * `[R]` `xfce4-panel` 4.20.4, `plugins/actions/actions.c`: il plugin legge
 * `/plugins/plugin-<N>/items`, un array di stringhe con `+`/`-` davanti; una
 * voce col `-` **non viene creata affatto** (`:1318`, `:1518`), mentre una col
 * `+` non permessa resta **visibile e grigia** (`:1347`).  ⇒ In XFCE non
 * esiste un KIOSK che le tolga (`STUDI.md` §xfce §10.4): si tolgono QUI.
 *
 * ⛔ Si tolgono SOLO le quattro famiglie nominate: il blocco, la sospensione
 *    (con ibernazione e sonno ibrido, che sono la stessa famiglia), il riavvio
 *    e lo spegnimento.  «Esci» (`logout`, `logout-dialog`) RESTA — §4.1-ter, è
 *    l'unica porta.
 * ⭐ E dal 21 set 2026, sera, anche «Cambia utente» (`switch-user`) — decisione
 *    dell'utente: *«togli anche Cambia utente per rendere omogeneo il
 *    comportamento tra tutti i DE: l'unica voce che deve rimanere è logout»*.
 *    KDE la toglie dalla fase 12 (KIOSK), GNOME col lockdown di dconf.
 */
static const char *AZIONI_DA_TOGLIERE[] = { "lock-screen", "switch-user", "suspend",
	                                    "hibernate",   "hybrid-sleep", "restart",
	                                    "shutdown",    NULL };

/* ⚠ Il default di serie, `actions_plugin_default_array()` (`actions.c:1437`):
 *   serve quando la proprietà `items` non c'è ancora — ed è il caso normale
 *   del pannello appena nato, perché `default.xml` non la scrive. */
static const char *AZIONI_DI_SERIE[] = { "+lock-screen", "+switch-user",  "+separator",
	                                 "+suspend",     "-hibernate",    "-hybrid-sleep",
	                                 "-separator",   "+shutdown",     "-restart",
	                                 "+separator",   "+logout",       NULL };

/* Le voci di un array come le stampa `xfconf-query`: una riga di intestazione
 * (tradotta, quindi NON si legge), una riga vuota, poi una voce per riga.  ⇒ Si
 * prende quel che segue la prima riga vuota.  NULL se non è un array. */
static char **voci_di_array(const char *uscita)
{
	const char *dopo = uscita ? strstr(uscita, "\n\n") : NULL;
	g_autoptr(GPtrArray) voci = NULL;
	g_auto(GStrv) righe = NULL;

	if (!dopo)
		return NULL;
	voci = g_ptr_array_new_with_free_func(g_free);
	righe = g_strsplit(dopo + 2, "\n", -1);
	for (int i = 0; righe[i]; i++)
		if (righe[i][0])
			g_ptr_array_add(voci, g_strdup(righe[i]));
	g_ptr_array_add(voci, NULL);
	return (char **) g_ptr_array_free(g_steal_pointer(&voci), FALSE);
}

static gboolean da_togliere(const char *voce)
{
	return voce[0] == '+' && g_strv_contains(AZIONI_DA_TOGLIERE, voce + 1);
}

/* Un plugin «actions»: le voci da togliere passano da `+` a `-`, le altre
 * restano identiche e nel loro ordine.  Scritto e RILETTO. */
/* ⭐ FASE 15, D-017 — PERMESSA: le voci tolte sono blocco, sospensione,
 *    riavvio e spegnimento, cioe' le quattro specie che la decisione
 *    dell'utente del 25 set 2026 lascia scrivere nel canale DELL'UTENTE
 *    («pericolose per altri utenti presenti sulla macchina»).  ⚠ Resta nel
 *    canale dell'utente: il numero del plugin e' suo, e un blocco di sessione
 *    per `plugin-N` non si puo' scrivere prima che il pannello nasca. */
static gboolean sistema_azioni_del_pannello(const char *base)
{
	g_autofree char *chiave = g_strdup_printf("%s/items", base);
	char *leggi[] = { "xfconf-query", "-c", "xfce4-panel", "-p", chiave, NULL };
	g_autofree char *prima = chiedi(leggi);
	g_auto(GStrv) vecchie = voci_di_array(prima);
	g_autoptr(GPtrArray) scrivi = g_ptr_array_new_with_free_func(g_free);
	g_autoptr(GPtrArray) nuove = g_ptr_array_new_with_free_func(g_free);
	g_autofree char *riletto = NULL;
	g_auto(GStrv) rilette = NULL;
	const char *const *da = vecchie ? (const char *const *) vecchie
	                                : (const char *const *) AZIONI_DI_SERIE;
	int tolte = 0;
	gboolean uguali;

	for (int i = 0; da[i]; i++) {
		if (da_togliere(da[i])) {
			g_ptr_array_add(nuove, g_strdup_printf("-%s", da[i] + 1));
			tolte++;
		} else {
			g_ptr_array_add(nuove, g_strdup(da[i]));
		}
	}
	g_ptr_array_add(nuove, NULL);
	if (tolte == 0) {
		registro_dice(REG_SESSIONE,
		              "⭐ XFCE: %s — nessuna voce da togliere, erano già tolte",
		              chiave);
		return TRUE;
	}

	/* ⚠ `--set=-lock-screen` e non `-s -lock-screen`: un valore che comincia
	 *   col trattino, scritto staccato, si legge come un'opzione. */
	g_ptr_array_add(scrivi, g_strdup("xfconf-query"));
	g_ptr_array_add(scrivi, g_strdup("-c"));
	g_ptr_array_add(scrivi, g_strdup("xfce4-panel"));
	g_ptr_array_add(scrivi, g_strdup("-p"));
	g_ptr_array_add(scrivi, g_strdup(chiave));
	g_ptr_array_add(scrivi, g_strdup("-n"));
	g_ptr_array_add(scrivi, g_strdup("-a"));
	for (guint i = 0; i + 1 < nuove->len; i++) {
		g_ptr_array_add(scrivi, g_strdup("--type=string"));
		g_ptr_array_add(scrivi,
		                g_strdup_printf("--set=%s", (char *) g_ptr_array_index(nuove, i)));
	}
	g_ptr_array_add(scrivi, NULL);
	esegui((char **) scrivi->pdata);

	riletto = chiedi(leggi);
	rilette = voci_di_array(riletto);
	uguali = rilette && g_strv_equal((const char *const *) rilette,
	                                 (const char *const *) nuove->pdata);
	if (uguali)
		registro_dice(REG_SESSIONE,
		              "⭐ XFCE: %s RILETTA — %d voci tolte dal pulsante d'azione "
		              "(blocco, sospensione, riavvio, spegnimento); «Esci» e «Cambia "
		              "utente» restano come erano",
		              chiave, tolte);
	else
		registro_dice(REG_SESSIONE,
		              "⛔ XFCE: %s NON è in vigore (la rilettura non coincide): le voci "
		              "di blocco, sospensione, riavvio e spegnimento restano nel "
		              "pulsante d'azione.  ⚠ Riavvio e spegnimento restano GRIGI "
		              "(polkit dice no), la sospensione no: la toglie sleep.conf",
		              chiave);
	return uguali;
}

/*
 * ⛔⛔ PERCHE' UN FILO, e non una scrittura prima della nascita — ed è la
 *     domanda «prova a smentirti» che qui ha risposto SÌ.
 *
 * Le chiavi di `xfce4-session` e `xfce4-power-manager` hanno un nome fisso, e
 * si scrivono prima (`xfconf_metti`).  Queste NO: il plugin si chiama
 * `plugin-<N>`, e `N` lo sa solo il canale `xfce4-panel` — che per un utente
 * che non ha mai aperto XFCE **è vuoto finché il pannello non parte** e non vi
 * migra la disposizione di serie (`migrate/main.c`).  ⇒ Scritte prima, per un
 * utente nuovo, non avrebbero un bersaglio: non «perse», peggio — **mai
 * scritte**, e senza una riga che lo dica.
 *
 * ⇒ Si guarda il canale ogni 2 s finché compare un plugin `actions`, e lo si
 *   sistema.  ⭐ Il pannello lega `items` a xfconf (`panel_properties_bind`) e
 *   sulla modifica rifà i pulsanti (`actions.c:428-434`): vale a caldo.
 * ⚠ Per l'utente che ha già un pannello il plugin c'è subito, e il primo giro
 *   lo sistema — di solito prima ancora che il pannello lo mostri.
 * ⚠ Dichiarato quel che NON copre: un plugin `actions` aggiunto a mano DOPO,
 *   dentro la sessione, resta col suo default.  Riavvio e spegnimento restano
 *   comunque grigi (polkit), la sospensione non c'è (sleep.conf), e il blocco
 *   non blocca (`LockCommand`).
 */
#define PANNELLO_XFCE_PASSO_US (2 * G_USEC_PER_SEC)
#define PANNELLO_XFCE_PAZIENZA_S 120

static gpointer guardia_del_pannello_xfce(gpointer dati)
{
	const gint64 partito = g_get_monotonic_time();

	(void) dati;
	for (;;) {
		char *elenca[] = { "xfconf-query", "-c", "xfce4-panel", "-l", "-v", NULL };
		g_autofree char *elenco = chiedi(elenca);
		g_auto(GStrv) righe = g_strsplit(elenco ? elenco : "", "\n", -1);
		int trovati = 0, sistemati = 0;

		/* Una riga di `-l -v` è «proprietà  valore», allineata con spazi. */
		for (int i = 0; righe[i]; i++) {
			g_auto(GStrv) parti = g_strsplit_set(g_strstrip(righe[i]), " \t", 2);
			const char *numero;

			if (!parti[0] || !parti[1] ||
			    !g_str_has_prefix(parti[0], "/plugins/plugin-"))
				continue;
			numero = parti[0] + strlen("/plugins/plugin-");
			if (!*numero || strspn(numero, "0123456789") != strlen(numero))
				continue;
			if (g_strcmp0(g_strstrip(parti[1]), "actions") != 0)
				continue;
			trovati++;
			if (sistema_azioni_del_pannello(parti[0]))
				sistemati++;
		}
		if (trovati) {
			registro_dice(REG_SESSIONE,
			              "%s XFCE: pulsanti d'azione del pannello: %d trovati, %d "
			              "sistemati e riletti",
			              sistemati == trovati ? "⭐" : "⛔", trovati, sistemati);
			return NULL;
		}
		if (g_get_monotonic_time() - partito > PANNELLO_XFCE_PAZIENZA_S * G_USEC_PER_SEC) {
			registro_dice(REG_SESSIONE,
			              "⚠ XFCE: in %d s nessun pulsante d'azione nel canale "
			              "xfce4-panel — non tolgo niente, perché non c'è niente da "
			              "togliere (o il pannello non è partito).  Smetto di guardare",
			              PANNELLO_XFCE_PAZIENZA_S);
			return NULL;
		}
		g_usleep(PANNELLO_XFCE_PASSO_US);
	}
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ FASE 14, INCREMENTO 4 — SU LXQt NON C'È PIÙ NESSUN «Lock screen».
 *     `DECISIONI.md` §4.7: via blocco, sospensione, riavvio e spegnimento;
 *     ⛔ «Esci» RESTA (§4.1-ter).  L'utente, dopo l'incremento 2: «l'icona
 *     del lockscreen sembra ancora attiva e visibile».
 *
 * `[M]`/`[R]` DOVE STAVA: nella finestra di `lxqt-leave`, che apre il
 * pulsante «Leave» FISSO in fondo al fancymenu (lxqt-panel 2.1.4
 * `plugin-fancymenu/lxqtfancymenuwindow.cpp:165-169, 315-318`) — codice, non
 * una voce di menu, e nessuna chiave lo toglie.  ⛔ E cliccato era PEGGIO che
 * inerte: `lxqt-leave` restava appeso (vedi i residui in
 * `impostazioni_lxqt()`).
 *
 * Due cure, ognuna con la sua lettura e la sua rilettura:
 *   A) `pannello_lxqt()` — il pannello usa `mainmenu` invece di `fancymenu`:
 *      il menu classico NON ha pulsanti fissi, e legge lo stesso
 *      `lxqt-applications.menu`, quindi le sei voci nascoste
 *      dall'incremento 2 restano nascoste e «Leave» contiene solo «Logout»;
 *   B) `blocco_lxqt()` — la rete di riserva: `lock_command_wayland=true`,
 *      per chi lancia `lxqt-leave` a mano (o da una scorciatoia).
 */

/*
 * ⚠ I FILE DI QSettings NON SONO SEMPRE KEY FILE: `QSettings` scrive le
 *   chiavi di primo livello PRIMA di ogni gruppo (`[M]` il
 *   `/usr/share/lxqt/panel.conf` di Trixie comincia con `panels=panel1`), e
 *   GKeyFile quel file lo rifiuta.  ⇒ Si mette davanti un `[General]`, che è
 *   il nome che QSettings dà a quel gruppo; se il file ha già un `[General]`,
 *   GKeyFile unisce i due.
 */
static gboolean leggi_ini_qt(GKeyFile *chiavi, const char *file, GError **sbaglio)
{
	g_autofree char *dentro = NULL;
	g_autofree char *con_testa = NULL;

	if (!g_file_get_contents(file, &dentro, NULL, sbaglio))
		return FALSE;
	con_testa = g_strconcat("[General]\n", dentro, NULL);
	return g_key_file_load_from_data(chiavi, con_testa, -1,
	                                 G_KEY_FILE_KEEP_COMMENTS |
	                                         G_KEY_FILE_KEEP_TRANSLATIONS,
	                                 sbaglio);
}

/*
 * ⭐ SCRIVI UNA CHIAVE E RILEGGILA — la regola comune a tutte le chiavi LXQt:
 *   il file si legge, si cambia SOLO quella chiave, le altre restano; se c'è
 *   e non si sa leggere NON si riscrive.  Torna il valore RILETTO dal file
 *   (NULL se non si rilegge), e in `*perche` il motivo, se non ha scritto.
 */
static char *scrivi_chiave_qt(const char *file, const char *gruppo, const char *chiave,
                              const char *valore, char **perche)
{
	g_autofree char *cartella = g_path_get_dirname(file);
	g_autoptr(GKeyFile) chiavi = g_key_file_new();
	g_autoptr(GKeyFile) riletto = g_key_file_new();
	g_autoptr(GError) sbaglio = NULL;

	if (g_file_test(file, G_FILE_TEST_EXISTS) && !leggi_ini_qt(chiavi, file, &sbaglio)) {
		*perche = g_strdup_printf("c'è ma non lo so leggere (%s) — NON lo riscrivo, "
		                          "per non buttare le chiavi dell'utente",
		                          sbaglio->message);
		return NULL;
	}
	g_key_file_set_value(chiavi, gruppo, chiave, valore);
	g_clear_error(&sbaglio);
	if (g_mkdir_with_parents(cartella, 0700) != 0 ||
	    !g_key_file_save_to_file(chiavi, file, &sbaglio)) {
		*perche = g_strdup_printf("NON scritto (%s)",
		                          sbaglio ? sbaglio->message : g_strerror(errno));
		return NULL;
	}
	/* ⛔ E SI RILEGGE: scritto non è in vigore finché non lo si rilegge. */
	if (!leggi_ini_qt(riletto, file, NULL))
		return NULL;
	return g_key_file_get_value(riletto, gruppo, chiave, NULL);
}

/*
 * I file di SISTEMA di un modulo LXQt, nell'ordine in cui QSettings li cerca:
 * `XDG_CONFIG_DIRS=/etc:/etc/xdg:/usr/share`, che mettiamo noi al lancio.
 */
static GPtrArray *file_di_sistema(const char *modulo)
{
	static const char *const CARTELLE[] = { "/etc", "/etc/xdg", "/usr/share", NULL };
	GPtrArray *sistema = g_ptr_array_new_with_free_func((GDestroyNotify) g_key_file_unref);

	for (int i = 0; CARTELLE[i]; i++) {
		g_autofree char *nome = g_strconcat(modulo, ".conf", NULL);
		g_autofree char *file = g_build_filename(CARTELLE[i], "lxqt", nome, NULL);
		GKeyFile *uno = g_key_file_new();

		if (g_file_test(file, G_FILE_TEST_EXISTS) && leggi_ini_qt(uno, file, NULL))
			g_ptr_array_add(sistema, uno);
		else
			g_key_file_unref(uno);
	}
	return sistema;
}

/*
 * ⭐ IL VALORE CHE QSettings VEDE DAVVERO: quello dell'utente se c'è, se no il
 *   primo dei file di sistema, nell'ordine di `XDG_CONFIG_DIRS`.  ⚠ `[R]` i
 *   file dell'utente di LXQt sono SPARSI: `LXQt::Settings` crea il file con il
 *   solo `__userfile__=true` (liblxqt 2.1.0 `lxqtsettings.cpp:53-59`), e il
 *   resto arriva dal sistema.  ⇒ Guardare il solo file dell'utente
 *   direbbe «nessun fancymenu» a un utente che ce l'ha.
 */
static char *valore_effettivo(GKeyFile *utente, GPtrArray *sistema, const char *gruppo,
                              const char *chiave)
{
	char *valore = g_key_file_get_value(utente, gruppo, chiave, NULL);

	for (guint i = 0; !valore && i < sistema->len; i++)
		valore = g_key_file_get_value(g_ptr_array_index(sistema, i), gruppo, chiave, NULL);
	return valore;
}

/*
 * I NOMI dei plugin del pannello che, visti come li vede lxqt-panel, sono di
 * tipo `tipo`.
 * `[R]` lxqt-panel 2.1.4: `panels` è la lista dei pannelli, `<pannello>/plugins`
 * la lista dei NOMI DI GRUPPO dei plugin, e `<nome>/type` il tipo
 * (`panelpluginsmodel.cpp:229`).  ⇒ Il nome del gruppo resta `fancymenu`:
 * conta solo `type`.
 * ⚠ `panels` vuota — o `@Invalid()`, che è come QSettings scrive una lista
 *   vuota — vale `panel1` (`lxqtpanelapplication.cpp:381-383`).  ⛔ Ed è la
 *   chiave dell'utente che conta anche quando è `@Invalid()`: QSettings la
 *   trova lì e non guarda il sistema.
 */
static GPtrArray *plugin_di_tipo(GKeyFile *utente, GPtrArray *sistema, const char *tipo)
{
	g_autofree char *pannelli = valore_effettivo(utente, sistema, "General", "panels");
	gboolean vuota = !pannelli || !*g_strstrip(pannelli) ||
	                 g_strcmp0(pannelli, "@Invalid()") == 0;
	g_auto(GStrv) quali = g_strsplit(vuota ? "panel1" : pannelli, ",", -1);
	GPtrArray *nomi_trovati = g_ptr_array_new_with_free_func(g_free);

	for (int p = 0; quali[p]; p++) {
		g_autofree char *elenco = valore_effettivo(utente, sistema, g_strstrip(quali[p]),
		                                           "plugins");
		g_auto(GStrv) nomi = g_strsplit(elenco ? elenco : "", ",", -1);

		for (int n = 0; nomi[n]; n++) {
			const char *nome = g_strstrip(nomi[n]);
			g_autofree char *e = *nome ? valore_effettivo(utente, sistema, nome, "type")
			                           : NULL;

			if (g_strcmp0(e, tipo) == 0)
				g_ptr_array_add(nomi_trovati, g_strdup(nome));
		}
	}
	return nomi_trovati;
}

/*
 * A) IL PANNELLO: `fancymenu` → `mainmenu`.
 *
 * ⛔⛔ FASE 15, D-018 — NEL FILE DELLA SESSIONE, e il pannello non tocca
 *     quello dell'utente: le impostazioni dell'utente non si toccano
 *     (decisione del 25 set 2026), e un menu non e' blocco, riavvio,
 *     sospensione o stand-by.
 *
 * ⛔ LA PRIMA STESURA NON BASTAVA — `[M]` 25 set 2026, 15-f031b su
 *    rete11-lxqt: un `lxqt/panel.conf` della sessione in testa a
 *    `XDG_CONFIG_DIRS` lo legge, si', ma `lxqt-panel` all'avvio RISCRIVE
 *    tutta la configurazione che vede nel file DELL'UTENTE
 *    (`~/.config/lxqt/panel.conf`: `type`, `alignment`, `[panel1]` intero) —
 *    e il nostro `type=mainmenu` ci finiva dentro.  ⚠ La riscrittura e' del
 *    desktop (`alignment`, `iconSize`… non li scriviamo noi): il guaio era
 *    solo che la leggeva da noi.
 *
 * ⭐ LA CURA: il pannello della sessione usa un SUO file.
 *    `[R]` lxqt-panel 2.1.4 `lxqtpanelapplication.cpp`: `-c/--configfile`
 *    ⇒ `LXQt::Settings(configFile, QSettings::IniFormat)` — legge e SCRIVE
 *    quel file, e nient'altro (niente cartelle di sistema: il file deve
 *    essere COMPLETO).  E `lxqt-panel` lo lancia `lxqt-session` come modulo
 *    dall'autostart (`[R]` lxqt-session 2.1.1 `lxqtmodman.cpp`:
 *    `XdgAutoStart::desktopFileList()`, `X-LXQt-Module`, `expandExecString`),
 *    che cerca per NOME di file in `~/.config/autostart` e poi in
 *    `XDG_CONFIG_DIRS`, e vince il primo.  ⇒ Due file nella SESSIONE:
 *    · `$XDG_RUNTIME_DIR/remotix/lxqt-pannello.conf` — il pannello
 *      dell'utente COM'E' (i file di sistema fusi, con sopra il suo file
 *      sparso) e `type=mainmenu` al posto del fancymenu;
 *    · `$XDG_RUNTIME_DIR/remotix/xdg-lxqt/autostart/lxqt-panel.desktop` —
 *      lo stesso modulo di sistema, con `--configfile` quel file.
 *
 * ⚠ I prezzi: quel che l'utente cambia nel pannello DAL REMOTO vale per la
 *   sessione e si perde alla nascita successiva (come su GNOME); e un
 *   `~/.config/autostart/lxqt-panel.desktop` dell'utente viene prima del
 *   nostro — si dice, e allora resta il suo pannello (col fancymenu, e la
 *   rete di riserva B sotto).
 */
static void pannello_lxqt(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	g_autofree char *file = g_build_filename(g_get_home_dir(), ".config", "lxqt", "panel.conf",
	                                         NULL);
	g_autofree char *suo_avvio = g_build_filename(g_get_home_dir(), ".config", "autostart",
	                                              "lxqt-panel.desktop", NULL);
	g_autofree char *cfg = lxqt_cartella_config_sessione();
	g_autofree char *nostro = NULL;
	g_autofree char *avvio = NULL;
	g_autofree char *cartella_avvio = NULL;
	g_autofree char *vecchio = NULL;
	g_autofree char *riga_avvio = NULL;
	g_autoptr(GKeyFile) utente = g_key_file_new();
	g_autoptr(GKeyFile) fuso = g_key_file_new();
	g_autoptr(GKeyFile) riletto = g_key_file_new();
	g_autoptr(GPtrArray) sistema = file_di_sistema("panel");
	g_autoptr(GPtrArray) solo_nostro = NULL;
	g_autoptr(GPtrArray) strati = g_ptr_array_new();
	g_autoptr(GPtrArray) fancy = NULL;
	g_autoptr(GPtrArray) restano = NULL;
	g_autoptr(GError) sbaglio = NULL;
	guint cambiati = 0;

	if (!runtime || !*runtime || !cfg) {
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: senza XDG_RUNTIME_DIR non c'e' la cartella della sessione — "
		              "il pannello resta col fancymenu, e col suo pulsante «Leave»");
		return;
	}
	nostro = g_build_filename(runtime, "remotix", "lxqt-pannello.conf", NULL);
	cartella_avvio = g_build_filename(cfg, "autostart", NULL);
	avvio = g_build_filename(cartella_avvio, "lxqt-panel.desktop", NULL);
	/* ⛔ l'avanzo della prima stesura: letto da lxqt-panel, finiva nell'utente */
	vecchio = g_build_filename(cfg, "lxqt", "panel.conf", NULL);
	g_unlink(vecchio);

	if (g_file_test(file, G_FILE_TEST_EXISTS) && !leggi_ini_qt(utente, file, &sbaglio)) {
		registro_dice(REG_SESSIONE,
		              "⚠ LXQt: %s c'è ma non lo so leggere (%s) — il pannello della "
		              "sessione parte dal solo sistema (e il file non lo tocco)",
		              file, sbaglio->message);
		g_clear_error(&sbaglio);
	}

	/* il pannello com'e': sistema dal meno forte al piu' forte, poi l'utente */
	for (guint i = sistema->len; i > 0; i--)
		g_ptr_array_add(strati, g_ptr_array_index(sistema, i - 1));
	g_ptr_array_add(strati, utente);
	for (guint i = 0; i < strati->len; i++) {
		GKeyFile *uno = g_ptr_array_index(strati, i);
		g_auto(GStrv) gruppi = g_key_file_get_groups(uno, NULL);

		for (int g = 0; gruppi[g]; g++) {
			g_auto(GStrv) chiavi = g_key_file_get_keys(uno, gruppi[g], NULL, NULL);

			for (int k = 0; chiavi && chiavi[k]; k++) {
				g_autofree char *v = g_key_file_get_value(uno, gruppi[g], chiavi[k], NULL);

				if (v)
					g_key_file_set_value(fuso, gruppi[g], chiavi[k], v);
			}
		}
	}
	fancy = plugin_di_tipo(utente, sistema, "fancymenu");
	for (guint i = 0; i < fancy->len; i++)
		g_key_file_set_value(fuso, g_ptr_array_index(fancy, i), "type", "mainmenu");
	if (g_mkdir_with_parents(cartella_avvio, 0700) != 0 ||
	    !g_key_file_save_to_file(fuso, nostro, &sbaglio)) {
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: %s NON scritto (%s): il pannello resta col fancymenu, "
		              "e col suo pulsante «Leave»",
		              nostro, sbaglio ? sbaglio->message : g_strerror(errno));
		return;
	}
	riga_avvio = g_strdup_printf("[Desktop Entry]\n"
	                             "Type=Application\n"
	                             "Name=Panel\n"
	                             "TryExec=lxqt-panel\n"
	                             "Exec=lxqt-panel --configfile %s\n"
	                             "OnlyShowIn=LXQt;\n"
	                             "X-LXQt-Module=true\n"
	                             "X-REMOTIX=il pannello della sessione (D-018)\n",
	                             nostro);
	if (!g_file_set_contents(avvio, riga_avvio, -1, &sbaglio)) {
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: %s NON scritto (%s): il pannello partira' col file "
		              "dell'utente, e col fancymenu",
		              avvio, sbaglio->message);
		return;
	}

	/* ⛔ E SI RILEGGE: il file della sessione, da solo (e' tutto quel che il
	 *    pannello leggera'), e chi vince nell'autostart. */
	if (!leggi_ini_qt(riletto, nostro, NULL)) {
		registro_dice(REG_SESSIONE, "⛔ LXQt: %s scritto ma NON si rilegge", nostro);
		return;
	}
	solo_nostro = g_ptr_array_new();
	for (guint i = 0; i < fancy->len; i++) {
		g_autofree char *e = g_key_file_get_value(riletto, g_ptr_array_index(fancy, i),
		                                          "type", NULL);

		cambiati += g_strcmp0(e, "mainmenu") == 0;
	}
	restano = plugin_di_tipo(riletto, solo_nostro, "fancymenu");
	if (g_file_test(suo_avvio, G_FILE_TEST_EXISTS))
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: %s c'è ed è dell'utente: viene PRIMA del nostro, e il "
		              "pannello partira' come dice lui (col suo file, e col fancymenu se "
		              "ce l'ha) — non lo tocco",
		              suo_avvio);
	else if (restano->len == 0 && cambiati == fancy->len)
		registro_dice(REG_SESSIONE,
		              "⭐ LXQt: il pannello della SESSIONE è %s (%u fancymenu→mainmenu, "
		              "RILETTO), lanciato con --configfile da %s — il pannello dell'utente "
		              "(%s) non lo legge e non lo scrive",
		              nostro, cambiati, avvio, file);
	else
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: fancymenu→mainmenu NON in vigore nel file della sessione "
		              "(rileggo %u mainmenu su %u, e %u fancymenu ancora lì)",
		              cambiati, fancy->len, restano->len);
}

/*
 * B) LA RETE DI RISERVA: il comando di blocco a `true`.
 *
 * `[R]` liblxqt 2.1.0 `lxqtscreensaver.cpp:153-161`, su Wayland:
 *   1. vince `lock_command_wayland` di PRIMO LIVELLO in `session.conf` (o nel
 *      modulo `$LXQT_SESSION_CONFIG`: il nostro lanciatore fa `exec
 *      lxqt-session` senza `-c`, quindi è `session`);
 *   2. se lì non c'è, `[Screensaver] lock_command_wayland` di `lxqt.conf`,
 *      SENZA default — nessun file spedito la mette.
 * ⛔⛔ Scrivere solo il 2 e rileggere solo il 2 MENTIREBBE a un utente che ha
 *     `lock_command_wayland=swaylock` in `session.conf`: il registro direbbe
 *     «in vigore» e varrebbe swaylock.  ⇒ Il valore si calcola con la stessa
 *     precedenza di liblxqt, e se `session.conf` ne porta uno che non è
 *     `true` — anche vuoto, che vince comunque e lascia appeso — lo si porta
 *     a `true` anche lì, dicendo che cosa c'era.
 * Con `true`: il processo esce con 0 ⇒ `activated` e `done` (`:196-207`) ⇒
 * `lxqt-leave` si chiude, e NESSUNA finestra d'errore.  ⛔ Vuoto lo lasciava
 * appeso; `/bin/false` aprirebbe la modale «Screen Saver Error».
 * ⚠ «Lock screen» dice «fatto» e non blocca: è una bugia, ma il blocco è di
 *   REMOTIX (§4.3), e la cura vera è A, che quel pulsante non lo mostra più.
 * ⚠ Il prezzo, dichiarato: sono `lxqt.conf` e (se serve) `session.conf`
 *   DELL'UTENTE.
 */
static void blocco_lxqt(void)
{
	static const char *const CHIAVE = "lock_command_wayland";
	g_autofree char *cartella = g_build_filename(g_get_home_dir(), ".config", "lxqt", NULL);
	g_autofree char *lxqt = g_build_filename(cartella, "lxqt.conf", NULL);
	g_autofree char *sessione = g_build_filename(cartella, "session.conf", NULL);
	g_autoptr(GPtrArray) sistema_lxqt = file_di_sistema("lxqt");
	g_autoptr(GPtrArray) sistema_sessione = file_di_sistema("session");
	g_autoptr(GKeyFile) utente_sessione = g_key_file_new();
	g_autoptr(GKeyFile) sessione_riletta = g_key_file_new();
	g_autoptr(GKeyFile) utente_lxqt = g_key_file_new();
	g_autofree char *perche = NULL;
	g_autofree char *nel_lxqt = NULL;
	g_autofree char *era = NULL;
	g_autofree char *effettivo = NULL;

	/* il 2, sempre: è quello che vale se il 1 non c'è */
	nel_lxqt = scrivi_chiave_qt(lxqt, "Screensaver", CHIAVE, "true", &perche);
	if (perche)
		registro_dice(REG_SESSIONE, "⛔ LXQt: %s %s", lxqt, perche);
	g_clear_pointer(&perche, g_free);

	/* il 1, solo se c'è e non è `true` */
	if (g_file_test(sessione, G_FILE_TEST_EXISTS) &&
	    !leggi_ini_qt(utente_sessione, sessione, NULL)) {
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: %s c'è ma non lo so leggere — NON lo riscrivo, e non "
		              "so quale comando di blocco vale",
		              sessione);
		return;
	}
	era = valore_effettivo(utente_sessione, sistema_sessione, "General", CHIAVE);
	if (era && g_strcmp0(era, "true") != 0) {
		g_autofree char *riletto = scrivi_chiave_qt(sessione, "General", CHIAVE, "true",
		                                            &perche);

		registro_dice(REG_SESSIONE,
		              "%s LXQt: %s portava %s=«%s», che VINCE su lxqt.conf: %s",
		              perche ? "⛔" : "⚠", sessione, CHIAVE, era,
		              perche ? perche : "portato a «true» anche lì");
		g_clear_pointer(&perche, g_free);
	}

	/* ⛔ E SI RILEGGE IL VALORE EFFETTIVO, con la precedenza di liblxqt. */
	if (g_file_test(sessione, G_FILE_TEST_EXISTS))
		leggi_ini_qt(sessione_riletta, sessione, NULL);
	if (g_file_test(lxqt, G_FILE_TEST_EXISTS))
		leggi_ini_qt(utente_lxqt, lxqt, NULL);
	effettivo = valore_effettivo(sessione_riletta, sistema_sessione, "General", CHIAVE);
	if (!effettivo)
		effettivo = valore_effettivo(utente_lxqt, sistema_lxqt, "Screensaver", CHIAVE);
	if (g_strcmp0(effettivo, "true") == 0)
		registro_dice(REG_SESSIONE,
		              "⭐ LXQt: %s effettivo = true, RILETTO (session.conf, poi "
		              "lxqt.conf [Screensaver]: %s) — «Lock screen» chiude "
		              "lxqt-leave senza bloccare e senza finestre d'errore",
		              CHIAVE, nel_lxqt ? nel_lxqt : "non lo so");
	else
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: %s effettivo NON è true (rileggo «%s»)", CHIAVE,
		              effettivo ? effettivo : "niente: resta vuoto, e lxqt-leave si "
		                                      "appende");
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ FASE 14 — LE IMPOSTAZIONI DI LXQt: SCRIVI, RILEGGI, DI' SE È IN VIGORE.
 *
 * ⛔⛔ L'INATTIVITÀ, e la trappola è `LEZIONI.md` §1.9 in forma pura: scrivere
 *     `enableIdlenessWatcher=false` NON BASTA.  `[R]` lxqt-powermanagement
 *     2.1.0 `src/powermanagementd.cpp`: se `runCheckLevel` < 1 il demone
 *     esegue `performRunCheck()`, che fa `setIdlenessWatcherEnabled(true)` —
 *     cioè **riscrive a vero** la nostra chiave al primo avvio (e mostra una
 *     notifica «primo avvio»).  ⇒ Si scrivono TUTT'E DUE: `runCheckLevel=1`
 *     (= `CURRENT_RUNCHECK_LEVEL`) spegne il controllo, e la chiave resta.
 *     https://raw.githubusercontent.com/lxqt/lxqt-powermanagement/2.1.0/src/powermanagementd.cpp
 * ⚠ Le chiavi sono di primo livello in `LXQt::Settings("lxqt-powermanagement")`
 *   (`config/powermanagementsettings.cpp`), cioè `[General]` nel formato INI di
 *   QSettings, nel file dell'utente `~/.config/lxqt/lxqt-powermanagement.conf`.
 *   ⭐ `~/.config` e non `g_get_user_config_dir()`: l'ambiente della sessione
 *   non porta `XDG_CONFIG_HOME`, quindi LXQt guarda lì.
 * ⚠ Il prezzo, dichiarato come su XFCE: è il file DELL'UTENTE.  Se lo stesso
 *   utente apre LXQt davanti alla macchina, il sorvegliante di inattività
 *   resta spento.  ⭐ FASE 15, D-018 — PERMESSA (stand-by), come il comando
 *   di blocco di `blocco_lxqt()` (blocco): la decisione del 25 set 2026.
 *   Il pannello e le voci del menu, invece, vanno nella SESSIONE.
 * ⚠ Si tocca SOLO quel che si deve: il file si legge, si cambiano due chiavi,
 *   le altre restano.  Se non si riesce a leggerlo (formato che GKeyFile non
 *   capisce) NON lo si riscrive: si dice, e si va avanti con meno.
 *
 * E le tre cose che NON si scrivono:
 *   · `compositor=` in `session.conf` — ⛔ `[R]` il wizard di `compositor`
 *     vuoto lo lancia LO SCRIPT upstream (`labwc -S lxqt-config-session`),
 *     non `lxqt-session`, che in 2.1.1 quella chiave non la legge
 *     (`lxqtmodman.cpp`).  Col nostro lanciatore la chiave non ha lettori;
 *   · il blocco a `/bin/false` — ⛔ aprirebbe una finestra MODALE («Screen
 *     Saver Error»): non si scrive.  ⚠ Il blocco SI scrive, ma a `true`
 *     (incremento 4, `blocco_lxqt()` più sotto): vuoto NON era inerte.
 *   · l'inibizione D-Bus — non esiste (`sessione_inibisci()`).
 */
static void impostazioni_lxqt(void)
{
	g_autofree char *file = g_build_filename(g_get_home_dir(), ".config", "lxqt",
	                                         "lxqt-powermanagement.conf", NULL);
	g_autofree char *perche = NULL;
	g_autofree char *attivo = NULL;
	g_autofree char *livello = NULL;

	/* ⚠ Se il file non si legge, `scrivi_chiave_qt()` NON lo riscrive, e le
	 *   voci pericolose del menu qui sotto si nascondono lo stesso. */
	attivo = scrivi_chiave_qt(file, "General", "enableIdlenessWatcher", "false", &perche);
	if (!perche)
		livello = scrivi_chiave_qt(file, "General", "runCheckLevel", "1", &perche);
	if (perche)
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: %s %s.  ⚠ Il sorvegliante di inattività resta com'è",
		              file, perche);
	else if (g_strcmp0(attivo, "false") == 0 && g_strcmp0(livello, "1") == 0)
		registro_dice(REG_SESSIONE,
		              "⭐ LXQt: %s [General] enableIdlenessWatcher=false e "
		              "runCheckLevel=1, RILETTE — il sorvegliante di inattività è "
		              "spento, e il demone non lo riaccende al primo avvio",
		              file);
	else
		registro_dice(REG_SESSIONE,
		              "⛔ LXQt: %s NON è in vigore (rileggo enableIdlenessWatcher=«%s», "
		              "runCheckLevel=«%s»)",
		              file, attivo ? attivo : "non lo so", livello ? livello : "non lo so");
	registro_dice(REG_SESSIONE,
	              "LXQt: non scrivo «compositor=» (col nostro lanciatore non ha "
	              "lettori); il comando di blocco lo scrivo più sotto a «true», "
	              "perché /bin/false aprirebbe una finestra modale");

	/*
	 * ⭐⭐ FASE 14, incremento 2 — LE VOCI PERICOLOSE DEL MENU SI NASCONDONO.
	 *     `DECISIONI.md` §4.7 (commit af9a19e): via sospensione, blocco,
	 *     riavvio, spegnimento.  ⛔ «Esci» RESTA (§4.1-ter): `lxqt-logout`
	 *     NON è nella lista, apposta.
	 *
	 * ⭐ COME: un `.desktop` con lo STESSO NOME, con `Hidden=true` e
	 *   `NoDisplay=true`, in una cartella che viene PRIMA di quelle di sistema.
	 *   `[R]` libqtxdg 4.1.0:
	 *   · `xdgmenureader.cpp:320-325` — le `AppDir` sono la cartella
	 *     dell'utente e poi `XDG_DATA_DIRS` nell'ordine;
	 *   · `xdgmenuapplinkprocessor.cpp:156-167` — per ogni id vince il primo
	 *     trovato, e le voci scartate non entrano nel menu;
	 *   · `xdgdesktopfile.cpp:1346-1373` — `NoDisplay` e `Hidden` veri ⇒ la
	 *     voce è scartata.
	 *   `[R]` lxqt-menu-data 2.1.0 `lxqt-applications.menu:206-223`: è la
	 *   cartella «Leave» del menu, dove stanno queste sei.
	 * ⛔⛔ FASE 15, D-018 — NON PIU' in `~/.local/share/applications`: le
	 *     impostazioni dell'utente non si toccano (decisione del 25 set 2026),
	 *     e un menu non e' blocco, riavvio, sospensione o stand-by.  ⇒ Le voci
	 *     stanno nella cartella dei DATI DELLA SESSIONE
	 *     (`$XDG_RUNTIME_DIR/remotix/dati-lxqt`), in testa a `XDG_DATA_DIRS`
	 *     (`componi_ambiente()`): valgono per la sessione che serviamo, e
	 *     l'utente al monitor ha il suo menu intero.
	 * ⚠ Il prezzo: un file dell'utente con lo stesso id in
	 *   `~/.local/share/applications` viene PRIMA e vince.  Si guarda e si
	 *   dice (la voce resta).  Uno con `X-REMOTIX` e' un avanzo delle versioni
	 *   di prima: nasconde lo stesso, e non si tocca.
	 *
	 * ⛔ I DUE RESIDUI CHE QUESTE SEI NON CURANO — curati dall'incremento 4,
	 *    `pannello_lxqt()` e `blocco_lxqt()` in fondo a questa funzione:
	 *   1. il pulsante «Leave» dentro il fancymenu è CODICE FISSO, non una
	 *      voce di menu (`[R]` lxqt-panel 2.1.4 `lxqtfancymenuwindow.cpp:
	 *      165-169, 315-318`, e nessuna chiave lo toglie): apre `lxqt-leave`,
	 *      dove Spegni/Riavvia/Sospendi/Iberna sono GRIGI perché polkit/logind
	 *      dicono di no (cintura 1 di §4.7, come su XFCE);
	 *   2. ⛔⛔ lì dentro «Lock screen» è SEMPRE attivo (`[R]` lxqt-session
	 *      2.1.1 `lxqt-leave/leavedialog.cpp:76-78`), e NON era «inerte» come
	 *      diceva questo commento: con `lock_command_wayland` vuoto
	 *      `lockScreen()` esce SENZA emettere `done` (`[R]` liblxqt 2.1.0
	 *      `lxqtscreensaver.cpp:281-292`), e `lxqt-leave` resta APPESO nel suo
	 *      `loop.exec()` (`leavedialog.cpp:113-118`) — `[M]` ancora vivo 34 s
	 *      dopo il clic.
	 */
	{
		static const char *const PERICOLOSE[] = {
			"lxqt-leave", "lxqt-lockscreen", "lxqt-suspend",
			"lxqt-hibernate", "lxqt-shutdown", "lxqt-reboot", NULL
		};
		const int quante = G_N_ELEMENTS(PERICOLOSE) - 1;
		g_autofree char *dati = lxqt_cartella_dati_sessione();
		g_autofree char *applicazioni = dati ? g_build_filename(dati, "applications", NULL)
		                                     : NULL;
		g_autofree char *dell_utente = g_build_filename(g_get_home_dir(), ".local", "share",
		                                                "applications", NULL);
		int nascoste = 0;

		if (!applicazioni || g_mkdir_with_parents(applicazioni, 0700) != 0) {
			registro_dice(REG_SESSIONE,
			              "⛔ LXQt: la cartella dei dati della sessione (%s) non si crea "
			              "(%s): 0/%d voci nascoste — sospensione, blocco, riavvio e "
			              "spegnimento restano nel menu (grigi per polkit, ma visibili)",
			              applicazioni ? applicazioni : "senza XDG_RUNTIME_DIR",
			              g_strerror(errno), quante);
			/* ⚠ `goto` e non `return`: il pannello e il blocco si curano
			 *   anche se le voci non si sono potute nascondere. */
			goto pannello;
		}
		for (int i = 0; PERICOLOSE[i]; i++) {
			g_autofree char *nome = g_strconcat(PERICOLOSE[i], ".desktop", NULL);
			g_autofree char *voce = g_build_filename(applicazioni, nome, NULL);
			g_autofree char *sua = g_build_filename(dell_utente, nome, NULL);
			g_autofree char *contenuto = NULL;
			g_autoptr(GKeyFile) rilegge = g_key_file_new();
			g_autoptr(GError) guasto = NULL;
			const char *vince = voce;

			contenuto = g_strdup_printf("[Desktop Entry]\n"
			                            "Type=Application\n"
			                            "Name=%s\n"
			                            "Hidden=true\n"
			                            "NoDisplay=true\n"
			                            "X-REMOTIX=nascosta da REMOTIX nella sessione "
			                            "(DECISIONI.md §4.7, D-018)\n",
			                            PERICOLOSE[i]);
			if (!g_file_set_contents(voce, contenuto, -1, &guasto))
				registro_dice(REG_SESSIONE, "⛔ LXQt: %s NON scritto (%s)", voce,
				              guasto->message);

			/* ⛔ E SI RILEGGE QUEL CHE VINCE: il file dell'utente, se c'è,
			 *    viene prima del nostro. */
			if (g_file_test(sua, G_FILE_TEST_EXISTS)) {
				vince = sua;
				registro_dice(REG_SESSIONE,
				              "⚠ LXQt: %s c'è nella cartella dell'utente e vince sulla "
				              "nostra: conta il suo Hidden (non lo tocco)",
				              sua);
			}
			if (g_key_file_load_from_file(rilegge, vince, G_KEY_FILE_NONE, NULL) &&
			    g_key_file_get_boolean(rilegge, "Desktop Entry", "Hidden", NULL))
				nascoste++;
		}
		if (nascoste == quante)
			registro_dice(REG_SESSIONE,
			              "⭐ LXQt: %d/%d voci nascoste NELLA SESSIONE (%s), RILETTE; "
			              "resta \"Esci\"",
			              nascoste, quante, applicazioni);
		else
			registro_dice(REG_SESSIONE,
			              "⛔ LXQt: %d/%d voci nascoste, RILETTE — ne mancano %d, "
			              "e restano nel menu (grigie per polkit, ma visibili); "
			              "resta \"Esci\"",
			              nascoste, quante, quante - nascoste);
	}
pannello:
	pannello_lxqt();
	blocco_lxqt();
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ FASE 15, D-017 — IL XFCONF DELLA SESSIONE: le impostazioni dell'utente
 *      non si toccano, tranne blocco, riavvio, sospensione e stand-by
 *      (decisione dell'utente del 25 set 2026).
 *
 * ⛔ Fino a qui `xfconf-query` scriveva nei canali DELL'UTENTE anche quel che
 *    non e' di quelle quattro specie — la cintura del logout, «Cambia
 *    utente» nel dialogo di uscita — e cancellava `~/.cache/sessions`.
 *
 * ⭐ LA STRADA: xfconf ha le proprieta' BLOCCATE.  `[R]` xfconf 4.20
 *    `xfconfd/xfconf-backend-perchannel-xml.c`:
 *    · `load_channel()` legge i file di sistema in ogni cartella di
 *      `XDG_CONFIG_DIRS` (dal meno forte al piu' forte), POI quello
 *      dell'utente;
 *    · una `<property … locked="*">` in un file di SISTEMA vince, e quella
 *      dell'utente con lo stesso nome viene saltata («not system file, prop
 *      already locked, pass on this one»); `set_property` la rifiuta.
 *    ⇒ Un file di canale in una cartella della SESSIONE, in testa a
 *      `XDG_CONFIG_DIRS` di `xfconfd`, vale per la sessione e non scrive
 *      niente nell'utente.
 *
 * ⚠ `xfconfd` NON e' un figlio della sessione: e' un'unita' d'utente
 *   (`xfconfd.service`, attivata dal bus — `[R]` xfconf dal 2015,
 *   `org.xfce.Xfconf.service`: `SystemdService=xfconfd.service`), e il suo
 *   ambiente e' quello del gestore.  ⇒ La cartella gliela da' un drop-in in
 *   `user.control` (la ricetta di `scrivi_dropin()`), e se `xfconfd` gira
 *   gia' lo si fa ripartire: legge i file una volta, all'apertura di un canale.
 *
 * ⭐ E al posto del `rm -rf ~/.cache/sessions` (che portava via anche le
 *   sessioni salvate DALL'UTENTE al monitor): `SessionName=REMOTIX` e
 *   `SaveOnExit=false`, bloccate.  `[R]` xfce4-session 4.20.2
 *   `xfsm-manager.c`: la sessione si cerca per NOME (`/general/SessionName`,
 *   di serie «Default») e, se non c'e', nasce quella di serie; si salva solo
 *   con `SaveOnExit` (`:1278`).  ⇒ La sessione remota non trova mai niente
 *   di salvato, e non salva mai niente.
 *
 * ⚠ I PREZZI, dichiarati:
 *   · il drop-in e la cartella vivono quanto il gestore d'utente (stanno in
 *     `XDG_RUNTIME_DIR`): un XFCE aperto al monitor sullo STESSO gestore
 *     vedrebbe gli stessi blocchi, finche' il gestore vive;
 *   · se `xfconfd` non e' un'unita' di systemd su questa macchina, il
 *     drop-in non conta: lo dice la rilettura, e le chiavi di sessione
 *     restano di serie (la cintura del logout resta `XFCE4_SESSION_COMPOSITOR`).
 */
struct chiave_xfconf {
	const char *gruppo; /* la cartella della proprieta' nel canale */
	const char *nome;
	const char *tipo;
	const char *valore;
};

static const struct chiave_xfconf XFCE_SESSIONE[] = {
	/* la seconda cintura del logout (la prima e' XFCE4_SESSION_COMPOSITOR) */
	{ "general", "WaylandLogoutCommand", "string", "/bin/true" },
	/* la sessione remota non ritrova e non salva sessioni */
	{ "general", "SessionName", "string", "REMOTIX" },
	{ "general", "SaveOnExit", "bool", "false" },
	/* il dialogo di «Esci» (decisione del 21 set 2026): «Cambia utente».
	 * ⚠ Sospendi, Iberna e Sonno ibrido NO: sono sospensione, cioe'
	 *   PERMESSE, e stanno nel canale dell'utente (`sessione_impostazioni()`). */
	{ "shutdown", "ShowSwitchUser", "bool", "false" },
	{ NULL, NULL, NULL, NULL },
};

static void xfce_xfconf_di_sessione(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	g_autofree char *cfg = NULL;
	g_autofree char *canali = NULL;
	g_autofree char *file = NULL;
	g_autofree char *cartella_dropin = NULL;
	g_autofree char *dropin = NULL;
	g_autofree char *riga = NULL;
	g_autofree char *vigore = NULL;
	g_autoptr(GString) xml = g_string_new(NULL);
	g_autoptr(GError) sbaglio = NULL;
	const char *gruppo = NULL;
	char *ricarica[] = { "systemctl", "--user", "daemon-reload", NULL };
	char *riparti[] = { "systemctl", "--user", "try-restart", "xfconfd.service", NULL };
	char *mostra[] = { "systemctl", "--user", "show", "-p", "Environment", "--value",
		           "xfconfd.service", NULL };
	int in_vigore = 0, quante = 0;

	if (!runtime || !*runtime) {
		registro_dice(REG_SESSIONE,
		              "⛔ XFCE, D-017: senza XDG_RUNTIME_DIR niente xfconf della sessione — "
		              "le chiavi di sessione restano di serie");
		return;
	}
	cfg = g_build_filename(runtime, "remotix", "xdg-xfce", NULL);
	canali = g_build_filename(cfg, "xfce4", "xfconf", "xfce-perchannel-xml", NULL);
	file = g_build_filename(canali, "xfce4-session.xml", NULL);

	g_string_append(xml, "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n"
	                     "<!-- REMOTIX (D-017): valgono per la sessione remota, bloccate; "
	                     "il canale dell'utente non si tocca -->\n"
	                     "<channel name=\"xfce4-session\" version=\"1.0\">\n");
	for (int i = 0; XFCE_SESSIONE[i].nome; i++) {
		if (g_strcmp0(gruppo, XFCE_SESSIONE[i].gruppo) != 0) {
			if (gruppo)
				g_string_append(xml, "  </property>\n");
			gruppo = XFCE_SESSIONE[i].gruppo;
			g_string_append_printf(xml, "  <property name=\"%s\" type=\"empty\">\n", gruppo);
		}
		g_string_append_printf(xml,
		                       "    <property name=\"%s\" type=\"%s\" value=\"%s\" "
		                       "locked=\"*\"/>\n",
		                       XFCE_SESSIONE[i].nome, XFCE_SESSIONE[i].tipo,
		                       XFCE_SESSIONE[i].valore);
	}
	g_string_append(xml, "  </property>\n</channel>\n");
	if (g_mkdir_with_parents(canali, 0700) != 0 ||
	    !g_file_set_contents(file, xml->str, -1, &sbaglio)) {
		registro_dice(REG_SESSIONE, "⛔ XFCE, D-017: %s NON scritto (%s)", file,
		              sbaglio ? sbaglio->message : g_strerror(errno));
		return;
	}

	cartella_dropin = g_build_filename(runtime, "systemd", "user.control", "xfconfd.service.d",
	                                   NULL);
	dropin = g_build_filename(cartella_dropin, "zz-remotix-sessione.conf", NULL);
	riga = g_strdup_printf("[Service]\nEnvironment=XDG_CONFIG_DIRS=%s:%s\n", cfg,
	                       g_getenv("XDG_CONFIG_DIRS") && *g_getenv("XDG_CONFIG_DIRS")
	                               ? g_getenv("XDG_CONFIG_DIRS")
	                               : "/etc/xdg");
	g_clear_error(&sbaglio);
	if (g_mkdir_with_parents(cartella_dropin, 0700) != 0 ||
	    !g_file_set_contents(dropin, riga, -1, &sbaglio)) {
		registro_dice(REG_SESSIONE, "⛔ XFCE, D-017: drop-in di xfconfd NON scritto (%s): %s",
		              dropin, sbaglio ? sbaglio->message : g_strerror(errno));
		return;
	}
	esegui(ricarica);
	vigore = chiedi(mostra);
	if (!vigore || !strstr(vigore, cfg))
		registro_dice(REG_SESSIONE,
		              "⚠ XFCE, D-017: il gestore non mostra la cartella della sessione "
		              "nell'ambiente di xfconfd.service («%s») — la rilettura dira' se vale",
		              vigore ? g_strstrip(vigore) : "non lo so");
	/* ⛔ xfconfd legge i file all'apertura di un canale: se gira, riparte. */
	esegui(riparti);

	/* ⛔ E SI RILEGGE, come la leggera' xfce4-session: il valore EFFETTIVO. */
	for (int i = 0; XFCE_SESSIONE[i].nome; i++) {
		g_autofree char *chiave = g_strdup_printf("/%s/%s", XFCE_SESSIONE[i].gruppo,
		                                          XFCE_SESSIONE[i].nome);
		char *rileggi[] = { "xfconf-query", "-c", "xfce4-session", "-p", chiave, NULL };
		g_autofree char *letto = chiedi(rileggi);

		quante++;
		if (letto && g_strcmp0(g_strstrip(letto), XFCE_SESSIONE[i].valore) == 0)
			in_vigore++;
		else
			registro_dice(REG_SESSIONE,
			              "⛔ XFCE, D-017: xfce4-session %s NON e' in vigore (rileggo «%s», "
			              "voluto «%s»)",
			              chiave, letto ? letto : "niente", XFCE_SESSIONE[i].valore);
	}
	if (in_vigore == quante)
		registro_dice(REG_SESSIONE,
		              "⭐ XFCE, D-017: xfconf della SESSIONE in vigore (%s, %d chiavi "
		              "bloccate, RILETTE): cintura del logout, SessionName=REMOTIX, "
		              "SaveOnExit=false, niente «Cambia utente» — il canale dell'utente "
		              "non si tocca",
		              file, quante);
	else
		registro_dice(REG_SESSIONE,
		              "⛔ XFCE, D-017: xfconf della sessione in vigore per %d chiavi su %d.  "
		              "⚠ La cintura del logout resta XFCE4_SESSION_COMPOSITOR; «Cambia "
		              "utente» resta nel dialogo",
		              in_vigore, quante);
}

void sessione_impostazioni(void)
{
	/* ⛔ FASE 12 — prima di aprire uno schema: su Plasma queste chiavi non
	 *    esistono, e le leve di Plasma (blocco, sospensione, menu) sono lavoro
	 *    degli incrementi dopo.  ⚠ Il blocco del desktop e' gia' spento dalla
	 *    riga di avvio (`--no-lockscreen`, `scrivi_dropin`). */
	if (e_kde()) {
		registro_dice(REG_SESSIONE,
		              "⚠ Plasma: le impostazioni della sessione (sospensione, menu) "
		              "non le metto ancora — fase 12, incrementi dopo il primo.  Il "
		              "blocco del desktop e' spento dalla riga di avvio");
		return;
	}
	/*
	 * ⭐ FASE 13 — su XFCE: la cintura del logout, l'energia, il blocco e il
	 *    dialogo di uscita; le voci del pannello le toglie `sessione_inibisci()`.
	 *
	 * ⛔ LA CINTURA DEL LOGOUT, che è l'unica che non può aspettare: se
	 *    `xfce4-session` decide che il compositore non va bene, al logout esegue
	 *    `loginctl terminate-session ''` e **ammazza la sessione logind di
	 *    REMOTIX**.  L'ambiente porta già `XFCE4_SESSION_COMPOSITOR` scritta
	 *    bene; questa è la seconda cintura, e ha la precedenza sulla prima.
	 *
	 * ⛔⛔ E SI RILEGGE.  `xfconf-query` esce con **zero anche quando il demone
	 *     ha rifiutato** e rimesso il valore di prima: l'API è asincrona e la
	 *     cache locale risponde per prima.  ⇒ Una scrittura riuscita non è una
	 *     configurazione applicata (`STUDI.md` §xfce §10.6), ed è
	 *     `LEZIONI.md` §1.9 spostata dalla misura alla configurazione.
	 */
	if (e_xfce()) {
		/* ⭐ FASE 15, D-017 — quel che la sessione deve avere e che NON e'
		 *    blocco, riavvio, sospensione o stand-by: nel xfconf della SESSIONE
		 *    (la cintura del logout, «Cambia utente» nel dialogo di uscita, e la sessione
		 *    salvata al posto del vecchio `rm -rf ~/.cache/sessions`).  Il
		 *    riquadro e' sopra `xfce_xfconf_di_sessione()`. */
		xfce_xfconf_di_sessione();

		/*
		 * ⛔⛔ L'USCITA NON SI SPEGNE — `STUDI.md` §xfce §10.2.
		 *
		 * `[R]` `xfce4-power-manager` 4.20.0 nasce con `dpms-enabled` VERO e
		 * `dpms-on-ac-sleep` = **10 minuti** (`common/xfpm-config.h`), e su
		 * Wayland li traduce in `zwlr_output_power_v1(OFF)`: labwc spegne
		 * l'uscita, e la cattura riceve `failed`.  ⇒ Con `dpms-enabled` falso
		 * `refresh()` (`xfpm-dpms.c`) non arma NESSUN tempo, e la modifica vale
		 * anche a caldo (`settings_changed`).
		 * ⭐ PERCHE' xfconf e non `org.freedesktop.PowerManagement.Inhibit`:
		 *    xfce4-power-manager **non ha attivazione D-Bus** — l'inibizione
		 *    chiesta prima che parta fallirebbe (è il `ServiceUnknown` di
		 *    powerdevil su KDE) e vivrebbe quanto la nostra connessione.  La
		 *    chiave c'è prima che il demone nasca, e lui la legge nascendo.
		 * ⚠ Il prezzo, dichiarato: è scritta nel canale DELL'UTENTE.  Se lo
		 *   stesso utente apre XFCE davanti alla macchina, il suo schermo non
		 *   si spegne più da solo.
		 * ⭐ FASE 15, D-017 — PERMESSE, e restano nell'utente: DPMS e
		 *    inattività (stand-by, sospensione) e, sotto, `LockCommand`
		 *    (blocco) — la decisione dell'utente del 25 set 2026.
		 */
		xfconf_metti("xfce4-power-manager", "/xfce4-power-manager/dpms-enabled", "bool",
		             "false",
		             "lo schermo della sessione non si spegne dopo 10 minuti (DPMS "
		             "di xfce4-power-manager, che su wlroots SPEGNE l'uscita e fa "
		             "fallire la cattura)");
		/* ⚠ Sono già 0 («mai») di serie: si scrivono per non ereditare quel che
		 *   l'utente ha messo lui.  La sospensione la ferma comunque sleep.conf
		 *   (§4.7) — questa toglie la BUGIA, cioè il tentativo che fallisce. */
		xfconf_metti("xfce4-power-manager", "/xfce4-power-manager/inactivity-on-ac", "uint",
		             "0", "nessuna sospensione per inattività, su rete elettrica");
		xfconf_metti("xfce4-power-manager", "/xfce4-power-manager/inactivity-on-battery",
		             "uint", "0", "nessuna sospensione per inattività, a batteria");

		/*
		 * ⛔ IL BLOCCO — `STUDI.md` §xfce §10.3, e decisione dell'utente del 21
		 *    set 2026.  `[R]` libxfce4ui 4.20.1, `xfce_screensaver_lock()`
		 *    (`xfce-screensaver.c:564-596`): se `LockCommand` c'è, lo esegue e
		 *    **torna il suo esito senza provare nient'altro**.  ⇒ Con
		 *    `/bin/false` non blocca `xflock4` (che chiama `Lock` di
		 *    xfce4-session e guarda la risposta), non blocca il metodo D-Bus,
		 *    non blocca il pulsante del pannello, e non blocca prima di una
		 *    sospensione (`lock-screen-suspend-hibernate`).
		 * ⚠ `/bin/false` e non `/bin/true`: chi chiede un blocco deve sentirsi
		 *   dire «non è bloccato», non «fatto».  E NON la stringa vuota: vale
		 *   «non impostata», e la catena D-Bus riprende (`:299-305`).
		 * ✅ Gli altri due bloccatori non partono qui: `xfce4-screensaver` è X11
		 *    puro ed esce se GDK non è X11, e `GDK_BACKEND=wayland` è secco;
		 *    `light-locker` vuole LightDM e X11.
		 */
		xfconf_metti("xfce4-session", "/general/LockCommand", "string", "/bin/false",
		             "il blocco schermo è spento: il blocco è di REMOTIX (§4.3)");

		/*
		 * ⛔ IL DIALOGO DI «ESCI» — decisione dell'utente del 21 set 2026.
		 *
		 * `[R]` xfce4-session 4.20.2, `xfsm-logout-dialog.c:263-374`: Sospendi,
		 * Iberna e Sonno ibrido hanno una chiave che li TOGLIE; ⛔ Riavvia e
		 * Spegni no — restano GRIGI per polkit (cintura 1 di §4.7).
		 * ⭐ FASE 15, D-017 — queste tre sono SOSPENSIONE, cioe' PERMESSE
		 *    (decisione del 25 set 2026): restano nel canale dell'utente.
		 *    «Cambia utente» (`ShowSwitchUser`) invece e' di SESSIONE, in
		 *    `xfce_xfconf_di_sessione()`.
		 */
		xfconf_metti("xfce4-session", "/shutdown/ShowSuspend", "bool", "false",
		             "niente «Sospendi» nel dialogo di uscita");
		xfconf_metti("xfce4-session", "/shutdown/ShowHibernate", "bool", "false",
		             "niente «Iberna» nel dialogo di uscita");
		xfconf_metti("xfce4-session", "/shutdown/ShowHybridSleep", "bool", "false",
		             "niente «Sonno ibrido» nel dialogo di uscita");

		registro_dice(REG_SESSIONE,
		              "XFCE: le voci del pulsante d'azione del pannello le tolgo "
		              "quando il pannello esiste (sessione_inibisci): prima, per un "
		              "utente nuovo, il suo plugin non ha ancora un numero");
		return;
	}
	/*
	 * ⭐ FASE 14 — su LXQt: l'inattività, le voci del menu, il pannello
	 *    (fancymenu→mainmenu) e il comando di blocco a `true`.  E le cose che
	 *    NON si scrivono, ognuna con la sua ragione.
	 */
	if (e_lxqt()) {
		impostazioni_lxqt();
		return;
	}
	struct schema_aperto wayland = apri_schema("org.gnome.mutter.wayland");
	struct schema_aperto shell = apri_schema("org.gnome.shell");
	struct schema_aperto energia = apri_schema("org.gnome.settings-daemon.plugins.power");
	struct schema_aperto sessione = apri_schema("org.gnome.desktop.session");
	struct schema_aperto salvaschermo = apri_schema("org.gnome.desktop.screensaver");
	struct schema_aperto blocchi = apri_schema("org.gnome.desktop.lockdown");
	const char *vuoto[] = { NULL };
	int tolte = 0;
	/*
	 * ⛔⛔ FASE 15, D-015 — LE DUE SPECIE DI CHIAVI (decisione dell'utente del
	 *     25 set 2026: «Le impostazioni dell'utente non si toccano TRANNE
	 *     quelle che riguardano blocco-schermo, riavvio sistema, sospensione e
	 *     stand-by: queste sono impostazioni pericolose per altri utenti
	 *     presenti sulla macchina»).
	 *
	 *   · PERMESSE, scritte nel dconf DELL'UTENTE e persistenti
	 *     (`gnome_metti_utente()`): `sleep-inactive-ac-type`,
	 *     `sleep-inactive-battery-type` (sospensione), `idle-delay`
	 *     (stand-by), `lock-enabled` (blocco);
	 *   · DI SESSIONE, scritte SOLO nel dconf della sessione (GSettings del
	 *     figlio, che ha il profilo di `sessione_dconf_prepara()`): le
	 *     Ctrl+Alt+F1…F12, `always-show-log-out`, `disable-user-switching` (e
	 *     la disposizione, in `input.c`).  ⛔ Senza il dconf della sessione
	 *     NON si scrivono: finirebbero nell'utente.
	 */
	const gboolean di_sessione = sessione_dconf_di_sessione();

	if (!di_sessione)
		registro_dice(REG_SESSIONE,
		              "⛔ D-015: il dconf della sessione NON e' in vigore — le chiavi di "
		              "SESSIONE (Ctrl+Alt+F*, «Esci…» sempre, «Cambia utente») NON le "
		              "scrivo: finirebbero nelle impostazioni dell'utente.  Le permesse "
		              "(blocco, sospensione, stand-by) si scrivono lo stesso");

	for (int i = 0; di_sessione && SCORCIATOIE_VT[i]; i++)
		if (c_e_la_chiave(&wayland, SCORCIATOIE_VT[i], "org.gnome.mutter.wayland") &&
		    g_settings_set_strv(wayland.impostazioni, SCORCIATOIE_VT[i], vuoto))
			tolte++;
	if (tolte)
		registro_dice(REG_SESSIONE,
		              "⭐ tolte %d scorciatoie Ctrl+Alt+F1…F12 su 12, nella SESSIONE: in "
		              "headless non c'e' nessuna console virtuale a cui passare, e Mutter "
		              "le ingoiava senza poterle onorare (sono NON_MASKABLE: nemmeno la "
		              "pagina potrebbe riprendersele)",
		              tolte);

	/*
	 * ⭐ «Esci…» DEVE ESSERCI — `DECISIONI.md` §4.1-ter, deciso dall'utente il 15
	 *    agosto 2026: e' l'unico gesto che termina la sessione.
	 *
	 * `[R]` `systemActions.js:394-410`: la voce compare solo se
	 * `always-show-log-out` **oppure** ci sono piu' utenti **oppure** piu' di una
	 * sessione in `/usr/share/…-sessions`.  ⇒ Su una macchina con un utente e una
	 * sessione sola NON COMPARE, e senza di lei il logout non esiste.
	 * ⭐ D-015: DI SESSIONE.
	 */
	if (di_sessione && c_e_la_chiave(&shell, "always-show-log-out", "org.gnome.shell") &&
	    g_settings_set_boolean(shell.impostazioni, "always-show-log-out", TRUE))
		registro_dice(REG_SESSIONE,
		              "⭐ «Esci…» acceso (always-show-log-out, nella SESSIONE): senza, su "
		              "una macchina con un utente solo la voce NON compare, e il logout "
		              "di §4.1-ter non esisterebbe");

	/*
	 * ⛔ LA SOSPENSIONE AUTOMATICA — `DECISIONI.md` §4.7, terza cintura, ed e' la
	 *    meta' che toglie la BUGIA dallo schermo: polkit e `sleep.conf`
	 *    impediscono il fatto, questa riga impedisce la notifica «Automatic
	 *    Suspend» seguita da un fallimento silenzioso.
	 * ⭐ D-015: PERMESSA — nell'utente, persistente.
	 */
	if (gnome_metti_utente(&energia, "org.gnome.settings-daemon.plugins.power",
	                       "sleep-inactive-ac-type", g_variant_new_string("nothing")) &&
	    gnome_metti_utente(&energia, "org.gnome.settings-daemon.plugins.power",
	                       "sleep-inactive-battery-type", g_variant_new_string("nothing")))
		registro_dice(REG_SESSIONE,
		              "⭐ sospensione automatica spenta (era «suspend» a 900 s, "
		              "upstream e su Debian): la macchina e' di piu' persone, e chi "
		              "la sospende le porta via a tutti");

	/* ⛔ E il blocca-schermo resta SPENTO — §4.3: su GNOME quello del desktop non
	 *    mostra un blocco, ci REVOCA cattura e input.  ⭐ D-015: PERMESSE. */
	if (gnome_metti_utente(&sessione, "org.gnome.desktop.session", "idle-delay",
	                       g_variant_new_uint32(0)))
		registro_dice(REG_SESSIONE, "⭐ inattivita' del desktop spenta (idle-delay 0)");
	if (gnome_metti_utente(&salvaschermo, "org.gnome.desktop.screensaver", "lock-enabled",
	                       g_variant_new_boolean(FALSE)))
		registro_dice(REG_SESSIONE,
		              "⭐ blocca-schermo del desktop spento (§4.3: il blocco e' di "
		              "REMOTIX, e su GNOME quello del desktop ci REVOCA cattura e "
		              "input invece di mostrare un blocco)");

	/*
	 * ⛔ «CAMBIA UTENTE» ESCE — decisione dell'utente del 21 set 2026, sera:
	 *    *«l'unica voce che deve rimanere è logout»*, uguale su tutti i desktop
	 *    (KDE la toglie col KIOSK dalla fase 12, XFCE dal pannello e dal
	 *    dialogo).  Su GNOME la voce compare quando la macchina ha piu' utenti
	 *    e GDM, cioe' proprio sulla macchina condivisa.
	 * ⚠ Solo `disable-user-switching`: `disable-log-out` resta com'e'.
	 * ⭐ D-015: DI SESSIONE.
	 */
	if (di_sessione &&
	    c_e_la_chiave(&blocchi, "disable-user-switching", "org.gnome.desktop.lockdown") &&
	    g_settings_set_boolean(blocchi.impostazioni, "disable-user-switching", TRUE))
		registro_dice(REG_SESSIONE,
		              "⭐ «Cambia utente» tolto (disable-user-switching, nella SESSIONE): "
		              "l'unica voce che resta e' «Esci…»");

	g_settings_sync();
	chiudi_schema(&wayland);
	chiudi_schema(&shell);
	chiudi_schema(&energia);
	chiudi_schema(&sessione);
	chiudi_schema(&salvaschermo);
	chiudi_schema(&blocchi);
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐ FASE 12 — LO SCHERMO DELLA SESSIONE REMOTA DI PLASMA NON SI SPEGNE.
 *
 * Su Plasma il comandante dell'inattivita' e' powerdevil, e `[R]` (`STUDI.md`
 * §kde §10.2) ha **«spegni lo schermo dopo 10 minuti» acceso per difetto**: in
 * una sessione remota vuol dire il desktop che diventa nero a chi guarda.
 * ⇒ `PolicyAgent.AddInhibition(types=4)`: 4 = `ChangeScreenSettings`, che
 * IMPLICA `InterruptSession` (`powerdevilpolicyagent.cpp:737-745`); nessun
 * controllo di permesso, e si rilascia da se' alla caduta del nostro nome.
 * ⚠ NON `org.freedesktop.PowerManagement.Inhibit`: mappa solo
 *   `InterruptSession`, e lo schermo si spegnerebbe lo stesso.
 * ⚠ La sospensione della MACCHINA non e' qui: la fermano le cinture di sistema
 *   di `DECISIONI.md` §4.7 (polkit e `AllowSuspend=no`), per tutti i desktop.
 *
 * ⛔⛔ PERCHE' UN FILO, e non una chiamata sola — `[M]` 19 set 2026, scatola
 *     `kde`, binario `6a41a28e`: chiamato quando il palco e' pronto, powerdevil
 *     **non c'e' ancora** («ServiceUnknown»: e' un'unita' di `plasma-core.target`,
 *     non si attiva dal bus).  E il figlio non ha un ciclo GLib, quindi niente
 *     `g_bus_watch_name`: si guarda chi possiede il nome ogni 2 s, e si chiede
 *     l'inibizione ogni volta che il proprietario CAMBIA — alla prima comparsa
 *     e se powerdevil riparte (l'inibizione vecchia e' morta con lui).
 *     Il filo vive quanto il figlio, cioe' quanto la sessione.
 */
#define POWERDEVIL "org.kde.Solid.PowerManagement"
#define POWERDEVIL_PASSO_US (2 * G_USEC_PER_SEC)
#define POWERDEVIL_PAZIENZA_S 120

static char *proprietario_di(GDBusConnection *bus, const char *nome)
{
	g_autoptr(GVariant) risposta = g_dbus_connection_call_sync(
		bus, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
		"GetNameOwner", g_variant_new("(s)", nome), G_VARIANT_TYPE("(s)"),
		G_DBUS_CALL_FLAGS_NONE, ATTESA_RISPOSTA_MS, NULL, NULL);
	char *chi = NULL;

	if (risposta)
		g_variant_get(risposta, "(s)", &chi);
	return chi;
}

static gpointer guardia_di_powerdevil(gpointer dati)
{
	g_autofree char *ultimo = NULL;
	const gint64 partito = g_get_monotonic_time();
	gboolean detto_assente = FALSE;

	(void) dati;
	for (;;) {
		g_autoptr(GDBusConnection) bus = sessione_bus(NULL);
		g_autofree char *chi = bus ? proprietario_di(bus, POWERDEVIL) : NULL;

		if (!chi && !ultimo && !detto_assente &&
		    g_get_monotonic_time() - partito > POWERDEVIL_PAZIENZA_S * G_USEC_PER_SEC) {
			detto_assente = TRUE;
			registro_dice(REG_SESSIONE,
			              "⚠ Plasma: powerdevil non e' comparso in %d s: nessuno "
			              "spegne lo schermo, e continuo a guardare",
			              POWERDEVIL_PAZIENZA_S);
		}
		if (chi && g_strcmp0(chi, ultimo) != 0) {
			g_autoptr(GVariant) risposta = NULL;
			g_autoptr(GError) sbaglio = NULL;
			guint32 gettone = 0;

			risposta = g_dbus_connection_call_sync(
				bus, POWERDEVIL, "/org/kde/Solid/PowerManagement/PolicyAgent",
				"org.kde.Solid.PowerManagement.PolicyAgent", "AddInhibition",
				g_variant_new("(uss)", 4u, "REMOTIX",
			                      "una sessione remota e' viva: lo schermo non si "
			                      "spegne e la sessione non e' inattiva"),
				G_VARIANT_TYPE("(u)"), G_DBUS_CALL_FLAGS_NONE, ATTESA_RISPOSTA_MS,
				NULL, &sbaglio);
			if (risposta) {
				g_variant_get(risposta, "(u)", &gettone);
				registro_dice(REG_SESSIONE,
				              "⭐ Plasma: schermo e inattivita' INIBITI a powerdevil "
				              "%s (gettone %u, types 4 = ChangeScreenSettings ⊃ "
				              "InterruptSession)%s",
				              chi, gettone, ultimo ? " — powerdevil era ripartito" : "");
				g_free(ultimo);
				ultimo = g_steal_pointer(&chi);
			} else {
				registro_dice(REG_SESSIONE,
				              "⛔ Plasma: l'inibizione a powerdevil %s NON e' passata "
				              "(%s): riprovo fra 2 s",
				              chi, sbaglio ? sbaglio->message : "senza motivo");
			}
		}
		g_usleep(POWERDEVIL_PASSO_US);
	}
	return NULL;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ L'INIBIZIONE DELLA SOSPENSIONE — `DECISIONI.md` §4.7, terza cintura.
 *
 * ⛔ IL FATTO CHE LA RENDE NECESSARIA, misurato: `[M]` 15 agosto 2026, nel
 *    desktop remoto compariva la notifica **«Automatic Suspend — Suspending soon
 *    because of inactivity»**.  `sleep-inactive-ac-type` vale `suspend` a 900 s,
 *    upstream **e** su Debian.
 *
 * ⭐ E' la TERZA cintura e non un doppione delle altre due, perche' agisce a un
 *    livello diverso: polkit e `sleep.conf` impediscono a chiunque di sospendere
 *    la macchina; `sessione_impostazioni()` toglie la voglia a `gsd-power`;
 *    questa dice al gestore di sessione **«c'e' qualcuno che lavora»**, che e'
 *    l'unica delle tre che parla la lingua del desktop.
 *
 * ⛔⛔ I FLAG SONO 12 — `SUSPEND` (4) | `IDLE` (8) — E MAI IL BIT `LOGOUT` (1).
 *     Con `LOGOUT` inibito, il logout dell'utente verrebbe **bloccato da noi**:
 *     `DECISIONI.md` §4.1-ter dice che «Esci» e' l'unico gesto che termina la
 *     sessione, e impedirlo sarebbe togliergli l'unica porta.
 *
 * Restituisce il gettone (0 se non e' andata).  ⚠ Non si rilascia mai: vale
 * quanto la sessione, e muore con lei.
 */
guint32 sessione_inibisci(void)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(NULL);
	g_autoptr(GVariant) risposta = NULL;
	g_autoptr(GError) sbaglio = NULL;
	guint32 gettone = 0;

	if (!bus)
		return 0;

	/* ⭐ FASE 12 — su Plasma il gestore di sessione non e' questo: lo schermo
	 *    lo tiene acceso un filo che aspetta powerdevil
	 *    (`guardia_di_powerdevil`, qui sopra). */
	if (e_kde()) {
		g_thread_unref(g_thread_new("powerdevil", guardia_di_powerdevil, NULL));
		registro_dice(REG_SESSIONE,
		              "Plasma: l'inibizione dello schermo la chiedo a powerdevil "
		              "appena compare sul bus");
		return 0;
	}
	/*
	 * ⭐ FASE 13 — su XFCE NON si inibisce, ed è una scelta con una misura
	 *    dietro, non una dimenticanza: `xfce4-session` **non consulta
	 *    l'inibitore** quando esegue `Logout` (`STUDI.md` §xfce §9.5), quindi
	 *    chiedere un'inibizione qui darebbe un ⛔ falso nel registro e
	 *    zero protezione.
	 * ⚠ Chi spegne davvero l'output su questo desktop è `xfce4-power-manager`,
	 *   dopo 10 minuti: lo ferma `dpms-enabled=false`, scritta e riletta in
	 *   `sessione_impostazioni()` prima della nascita.
	 * ⭐ E qui, dove il palco c'è, parte il filo che toglie le voci pericolose
	 *    dal pulsante d'azione del pannello (`guardia_del_pannello_xfce`): il
	 *    suo bersaglio esiste solo dopo che il pannello è nato.
	 */
	if (e_xfce()) {
		g_thread_unref(g_thread_new("pannello-xfce", guardia_del_pannello_xfce, NULL));
		registro_dice(REG_SESSIONE,
		              "XFCE: non chiedo nessuna inibizione — xfce4-session non "
		              "consulta l'inibitore, e l'uscita la tiene accesa "
		              "dpms-enabled=false.  Guardo il pannello per togliergli "
		              "blocco, sospensione, riavvio e spegnimento");
		return 0;
	}
	/*
	 * ⭐ FASE 14 — su LXQt NON si inibisce, e qui non c'è nemmeno a chi
	 *    chiederlo: `PowerManagement.Inhibit` in LXQt **non esiste** — né
	 *    esposto né consumato (`STUDI.md` §lxqt §6.2, `[✗]`, zero occorrenze).
	 * ⚠ L'inattività la spegne `impostazioni_lxqt()` prima della nascita; e
	 *   l'uscita su Wayland `lxqt-powermanagement` non la sa spegnere (DPMS solo
	 *   su xcb).  Chi la spegnerebbe è `swayidle` dall'autostart di labwc, che
	 *   la nostra cartella `-C` non ha.
	 * [?] La leva più forte, `zwp_idle_inhibit_manager_v1` di labwc, non è di
	 *     questo incremento: è la misura M5.
	 * ⚠ Le voci pericolose del pannello (`fancymenu`, `lxqt-leave` nel
	 *   quicklaunch di Debian) NON si toccano qui: incrementi dopo.
	 */
	if (e_lxqt()) {
		registro_dice(REG_SESSIONE,
		              "LXQt: non chiedo nessuna inibizione — LXQt non ha "
		              "PowerManagement.Inhibit; l'inattività è spenta dalla "
		              "configurazione, e swayidle non parte (autostart nostro, vuoto)");
		return 0;
	}

	risposta = g_dbus_connection_call_sync(
		bus, "org.gnome.SessionManager", "/org/gnome/SessionManager",
		"org.gnome.SessionManager", "Inhibit",
		g_variant_new("(susu)", "REMOTIX", 0u,
	                      "una sessione remota e' viva: la macchina non deve "
	                      "sospendersi ne' considerarsi inattiva",
	                      (guint32)(4u | 8u)),
		G_VARIANT_TYPE("(u)"), G_DBUS_CALL_FLAGS_NONE, ATTESA_RISPOSTA_MS, NULL,
		&sbaglio);

	if (!risposta) {
		registro_dice(REG_SESSIONE,
		              "⛔ l'inibizione della sospensione NON e' passata (%s): la "
		              "macchina puo' addormentarsi sotto una sessione viva.  ⚠ Le "
		              "altre due cinture (polkit e sleep.conf) reggono lo stesso, ma "
		              "questa e' quella che parla al desktop",
		              sbaglio ? sbaglio->message : "senza motivo");
		return 0;
	}
	g_variant_get(risposta, "(u)", &gettone);
	registro_dice(REG_SESSIONE,
	              "⭐ sospensione e inattivita' INIBITE al gestore di sessione "
	              "(gettone %u, flag 12 = SUSPEND|IDLE — ⛔ mai LOGOUT, o toglieremmo "
	              "all'utente l'unica porta per uscire)",
	              gettone);
	return gettone;
}

/* ------------------------------------------------------------------------- */
/*
 * ⭐⭐ FALLA NASCERE E TORNA SUBITO — 15 agosto 2026, fase 5.
 *
 * ⛔ PERCHE' NON BASTAVA `sessione_assicura()`, che pure fa la stessa cosa:
 *    quella **aspetta** fino a `ATTESA_AVVIO_MS` (40 s), e chi la chiama e' il
 *    figlio, cioe' l'unico processo che in quei 40 s deve continuare a
 *    rispondere al padre.  ⚠ `LEZIONI.md` §6.2-bis: un'attesa che protegge un
 *    anello e' un ritardo per tutti gli altri.
 *
 * ⭐ E l'attesa non serve, perche' esiste gia': il figlio riprova il palco con
 *    un'attesa che raddoppia (1 s → 30 s).  ⇒ Qui si CHIEDE la nascita e si
 *    torna; a scoprire che la sessione c'e' ci pensa il giro dopo.
 *
 * ⚠ Si avvia SOLO da `SESSIONE_MORTA`.  Gli altri stati li governa
 *   `sessione_assicura()`, e rifarli qui vorrebbe dire due regole sullo stesso
 *   fatto — cioe' due regole diverse il giorno in cui una cambia.
 */
bool sessione_fai_nascere(uint32_t larghezza, uint32_t altezza)
{
	SessioneStato stato;

	/*
	 * ⛔⛔ PRIMA DI TUTTO: SE NON C'E' NESSUN DESKTOP, NON SI PROVA — fase 13.
	 *
	 * Fino a ieri qui si arrivava lo stesso, perche' una macchina senza desktop
	 * si dichiarava **GNOME per ripiego**; poi si falliva tre volte accusando
	 * qualcun altro (`[M]` 20 set 2026: «un altro drop-in vince sul mio»,
	 * «Mutter non espone RemoteDesktop»).  ⇒ Adesso si dice qui, dove chi
	 * guarda la fetta di registro di QUESTO inquilino la trova — e non una
	 * volta sola all'avvio del server, dove nessun banco la legge.
	 */
	if (e_nessuno()) {
		registro_dice(REG_SESSIONE,
		              "⛔ non faccio nascere niente: %s.  ⚠ Non è «la sessione è "
		              "nata cieca», è «non c'è nessun desktop da accendere»: sono "
		              "due guasti diversi e qui è il secondo",
		              sessione_desktop_spiega());
		return false;
	}

	stato = sessione_stato(larghezza, altezza, NULL);

	if (stato != SESSIONE_MORTA) {
		registro_dice(REG_SESSIONE,
		              "non la faccio nascere: lo stato e' «%s», non «morta» — e "
		              "gli altri casi li governa sessione_assicura()",
		              sessione_marca(stato));
		return false;
	}

	/* ⭐ R1/R2 — prima di mettere qualunque cosa nel gestore d'utente: via gli
	 *    avanzi di una sessione finita male, e la fotografia di com'e' adesso
	 *    (il riquadro sopra `sessione_sgombera_gestore()`). */
	sessione_sgombera_gestore("nascita: avanzi di prima");
	sessione_fotografa_gestore();

	/* ⛔ Il drop-in PRIMA del comando: la misura del desktop ci sta dentro, e
	 *    `gnome-session` fa partire l'unita' della Shell come prima cosa.
	 *    Scriverlo dopo vorrebbe dire scriverlo per la sessione SUCCESSIVA. */
	if (!scrivi_dropin(larghezza, altezza)) {
		registro_dice(REG_SESSIONE,
		              "⛔ senza il drop-in in vigore non la faccio nascere: "
		              "nascerebbe col monitor di troppo, e l'utente riguarderebbe "
		              "uno schermo vuoto");
		return false;
	}

	/*
	 * ⛔⛔⛔ E PRIMA DI TUTTO: IL GESTORE D'UTENTE STA MORENDO? — 16 agosto 2026,
	 *      ed e' la causa che ha fatto provare cinque volte all'utente.
	 *
	 * `[M]` Dopo un logout, `user@<uid>.service` **si spegne**: nel giornale si
	 * legge *«Finished systemd-exit.service — Exit the Session»*, e con lui se ne
	 * vanno `dbus.socket`, `pipewire.socket`, `session.slice`.  ⛔ Se in quel
	 * momento noi lanciamo `gnome-session`, quello parte **dentro una sessione
	 * che sta morendo** e muore con lei — senza un errore che lo dica.
	 *
	 * ⇒ Il sintomo era questo, e sembravano quattro difetti diversi: il desktop
	 *   che non compare, che compare dopo trenta secondi, che compare «rotto», e
	 *   l'input che non arriva.  `[M]` La sessione veniva avviata due o tre volte
	 *   di fila (06:28:33, :46, :59) e solo l'ultima attecchiva.
	 *
	 * ⭐ La cura non e' aspettare a tempo: e' CHIEDERE.  Il gestore sa dire di se'
	 *    «stopping», e finche' lo dice non si fa nascere niente — si torna
	 *    indietro, e il ciclo dei ri-tentativi riprova fra poco.  ⚠ E' la stessa
	 *    forma dell'«ATTENDI» di §7.1: **non si chiede a chi non c'e', e non si
	 *    nasce dove si sta morendo**.
	 */
	{
		char *argv[] = { "systemctl", "--user", "is-system-running", NULL };
		g_autofree char *stato = chiedi(argv);

		if (stato) {
			g_strstrip(stato);
			if (g_strcmp0(stato, "stopping") == 0) {
				registro_dice(REG_SESSIONE,
				              "⛔ il gestore d'utente sta SPEGNENDOSI "
				              "(«stopping»): NON faccio nascere la sessione "
				              "adesso — nascerebbe dentro una sessione che "
				              "muore, e morirebbe con lei senza dire perche'.  "
				              "⭐ Si riprova fra poco");
				return false;
			}
		}
	}

	/*
	 * ⛔⭐ E LA VECCHIA DEV'ESSERE FINITA DAVVERO, non «quasi».
	 *
	 * `unita_inattiva()` esiste da agosto e porta gia' la lezione giusta nel suo
	 * commento: *«inattiva» e non «non piu' attiva»: `is-active` passa per
	 * `deactivating`, e ripartire li' dentro e' un'altra prima esecuzione*.
	 * ⇒ E' esattamente il nostro caso, visto da un'altra porta: `[M]` 16 agosto,
	 * il primo avvio dopo un logout falliva perche' il gestore della sessione
	 * precedente stava ancora chiudendo.
	 *
	 * ⚠ Non si aspetta qui dentro: si dice di no e si torna: chi ci chiama ha un
	 *   ciclo di ri-tentativi che e' fatto apposta, e un'attesa dentro questa
	 *   funzione sarebbe un figlio che smette di rispondere (`LEZIONI.md`
	 *   §6.2-bis).
	 */
	if (!unita_inattiva()) {
		registro_dice(REG_SESSIONE,
		              "⛔ la sessione grafica PRECEDENTE non e' ancora finita "
		              "(«%s» non e' inattiva): non ne faccio nascere una seconda "
		              "adesso — nascerebbe dentro quella che muore.  ⭐ Si riprova "
		              "fra poco",
		              e_kde()                   ? SESSIONE_UNITA_KWIN
		              : (e_xfce() || e_lxqt()) ? "il processo " SESSIONE_PROCESSO_XFCE
		                                        : SESSIONE_UNITA_GESTORE);
		return false;
	}

	/* ⛔ LE IMPOSTAZIONI PRIMA DEL COMANDO, per la stessa ragione del drop-in:
	 *    `gnome-session` fa partire la Shell come prima cosa, e una chiave
	 *    scritta dopo vale per la sessione SUCCESSIVA — cioe' ha ragione domani. */
	/* ⭐ D-015: prima si svuota il dconf della sessione, poi ci si scrive. */
	if (sessione_desktop() == SESSIONE_DESKTOP_GNOME)
		sessione_dconf_azzera();
	sessione_impostazioni();

	return avvia(larghezza, altezza) ? true : false;
}

SessioneStato sessione_assicura(uint32_t larghezza, uint32_t altezza, bool *avviata)
{
	SessioneMonitor scelto;
	SessioneStato stato;
	gint64 scadenza, viva_da = 0;

	if (avviata)
		*avviata = false;

	stato = sessione_stato(larghezza, altezza, &scelto);
	switch (stato) {
	case SESSIONE_SANA:
		/*
		 * ⛔⛔ E QUESTO NON E' PIU' IL CASO BUONO — 14 agosto 2026, fase 4, A1.
		 *
		 *     `SESSIONE_SANA` vuol dire «un monitor solo, «MetaVirtualMonitor»,
		 *     della misura chiesta»: cioe' una sessione che si e' presa **un
		 *     monitor suo**.  Poi la cattura ne monta un secondo e registra
		 *     quello ⇒ ⛔ l'utente guarda uno schermo vuoto.  `[M]` misurato
		 *     dal banco `04-b20` il 14 agosto 2026.
		 *
		 * ⇒ ⭐ Adesso il caso buono e' `SESSIONE_NERA` — zero monitor propri —
		 *      e questo e' il DIFETTO.  ⛔ La faccio rinascere, e la ragione e'
		 *      la stessa, rovesciata, che `sessione.h` da' per la nera: un
		 *      monitor «MetaVirtualMonitor» esiste **solo** se qualcuno ha
		 *      passato `--virtual-monitor`, cioe' solo in una sessione headless
		 *      — cioe' nostra.  Non si porta via niente a nessuno.
		 *
		 * ⚠ E si rinasce SOLO qui, dove i monitor sono **uno**: se fossero due
		 *   ci sarebbe una cattura viva (`SESSIONE_SCELTO_DA_SE`), e buttare
		 *   giu' la sessione toglierebbe il desktop a un client attaccato.
		 */
		registro_dice(REG_SESSIONE,
		              "⛔ LA SESSIONE HA UN MONITOR SUO («%s» «%s» %ux%u): e' il difetto "
		              "del desktop invisibile — la cattura ne montera' un SECONDO e "
		              "l'utente guardera' quello, vuoto.  La faccio RINASCERE senza "
		              "monitor propri, e lo scrivo qui perche' una sessione che sparisce "
		              "senza una riga e' peggio del difetto",
		              scelto.connettore, scelto.prodotto, scelto.larghezza,
		              scelto.altezza);
		break;
	case SESSIONE_NON_LETTA:
		registro_dice(REG_SESSIONE,
		              "⛔ non ho potuto leggere lo stato della sessione: NON tocco "
		              "niente.  «Non ho potuto guardare» non e' «non c'e'» (E8), e una "
		              "sessione buttata giu' per una lettura fallita e' un danno fatto "
		              "per un'ipotesi");
		return SESSIONE_NON_LETTA;
	case SESSIONE_MISURA_ALTRA:
		/* ⛔ E' lo stesso difetto di sopra con un'altra misura: un monitor
		 *    «MetaVirtualMonitor» che la sessione non doveva avere. */
		registro_dice(REG_SESSIONE,
		              "⛔ la sessione ha un monitor SUO, %ux%u invece dei %ux%u chiesti: "
		              "e' il difetto del desktop invisibile con un'altra misura.  La "
		              "faccio RINASCERE senza monitor propri",
		              scelto.larghezza, scelto.altezza, larghezza, altezza);
		break;
	case SESSIONE_SCELTO_DA_SE:
		/*
		 * ⭐ E QUESTO, DOPO LA CURA, E' SPESSO IL CASO SANO: «Virtual remote
		 *    monitor» e' il nome che Mutter da' al monitor di un `RecordVirtual`
		 *    (`meta-screen-cast-virtual-stream-src.c:606-609` `[R]`), cioe' al
		 *    monitor che monta la NOSTRA cattura quando un client e' attaccato.
		 * ⛔ Non si tocca in nessun caso: rifarla nascere toglierebbe il
		 *    desktop a chi lo sta guardando (I4).
		 */
		registro_dice(REG_SESSIONE,
		              "la sessione c'e' con %u monitor, il primo e' «%s»: NON la tocco.  "
		              "⭐ Dopo la cura del 14 agosto 2026 questo e' spesso il caso sano — "
		              "«Virtual remote monitor» e' il monitor che monta la cattura quando "
		              "un client e' attaccato, e buttarla giu' glielo toglierebbe (I4)",
		              scelto.quanti, scelto.prodotto);
		return SESSIONE_SCELTO_DA_SE;
	case SESSIONE_NERA:
		/*
		 * ⛔⛔ E QUESTO NON E' PIU' UN GUASTO — 14 agosto 2026, fase 4, A1.
		 *
		 *     Fino a stamattina qui si faceva RINASCERE la sessione.  ⇒ Dopo la
		 *     cura quella riga **distruggerebbe la sessione giusta a ogni
		 *     chiamata**, e ne farebbe un'altra identica, all'infinito.
		 *
		 * ⭐ Zero monitor propri E' il fine: l'unico monitor lo monta la nostra
		 *    cattura, e GNOME ci mette sopra la barra e la dock.
		 * ⚠ Il prezzo si dichiara: prima del primo client la sessione e' NERA
		 *    davvero — non ha niente da mostrare, e non deve mostrarlo a
		 *    nessuno.  Per una sessione **solo remota** e' corretto.
		 */
		registro_dice(REG_SESSIONE,
		              "⭐ la sessione c'e' e non ha monitor propri: e' esattamente quel "
		              "che serve, e NON la tocco.  L'unico monitor lo montera' la "
		              "cattura quando arriva il primo client, ed e' li' che GNOME mette "
		              "la barra e la dock.  ⚠ Fino ad allora la sessione e' nera, e va "
		              "bene: e' una sessione SOLO REMOTA");
		return SESSIONE_NERA;
	case SESSIONE_MORTA:
		registro_dice(REG_SESSIONE, "nessuna sessione grafica: la avvio io");
		break;
	}

	/*
	 * ⛔ IL DROP-IN PRIMA DEL COMANDO, e non e' un ordine qualunque: la misura
	 *    del desktop ci sta dentro, e `gnome-session` fa partire l'unita' della
	 *    Shell come prima cosa.  Scriverlo dopo significherebbe scriverlo per la
	 *    sessione SUCCESSIVA — cioe' avere ragione domani.
	 *
	 * ⛔ E PRIMA DI BUTTARE GIU' QUELLA COL MONITOR DI TROPPO: se il drop-in non
	 *    si puo' mettere in vigore, farla rinascere darebbe un'altra sessione
	 *    con lo stesso difetto, e in piu' avremmo portato via all'utente quella
	 *    che c'era.
	 */
	if (!scrivi_dropin(larghezza, altezza)) {
		registro_dice(REG_SESSIONE,
		              "⛔ senza il drop-in in vigore la sessione rinascerebbe con lo "
		              "stesso monitor di troppo, e l'utente riguarderebbe uno schermo "
		              "vuoto: non la faccio nascere affatto, e lo stato resta «%s»",
		              sessione_marca(stato));
		return stato;
	}

	/* ⛔ Si butta giu' solo quella col monitor SUO (uno solo, e nostro): mai la
	 *    nera — che adesso e' quella giusta — e mai quella con due monitor, che
	 *    ha una cattura viva sopra. */
	if ((stato == SESSIONE_SANA || stato == SESSIONE_MISURA_ALTRA) &&
	    !sessione_termina()) {
		registro_dice(REG_SESSIONE,
		              "⛔ la sessione col monitor di troppo non se n'e' andata: non ne "
		              "avvio una seconda (una sessione grafica per utente, I2)");
		return sessione_stato(larghezza, altezza, NULL);
	}

	if (!avvia(larghezza, altezza))
		return sessione_stato(larghezza, altezza, NULL);

	/*
	 * ⛔⭐ E QUI SI ASPETTA LA SESSIONE **SENZA MONITOR PROPRI**, non un monitor.
	 *
	 * ⚠ Fino al 14 agosto 2026 questa attesa finiva su `SESSIONE_SANA` — «c'e'
	 *   un monitor». Era la domanda giusta per il disegno di prima, dove la
	 *   sessione doveva portarsi un monitor suo; ⛔ dopo la cura e' la domanda
	 *   ROVESCIATA, e aspettare `SANA` vorrebbe dire aspettare il difetto.
	 *
	 * ⭐ Resta pero' la lezione di v1, e non si torna a `sessione_viva()`: si
	 *   guarda comunque **quanti monitor ci sono**, perche' e' l'unico modo di
	 *   accorgersi che un drop-in di qualcun altro ha vinto sul nostro.  La
	 *   domanda e' la stessa, e' l'atteso che si e' rovesciato.
	 *
	 * ⚠ La grazia serve ancora, e per la ragione opposta: `--virtual-monitor`
	 *   creerebbe il monitor PRIMA che `DisplayConfig` risponda, quindi se dopo
	 *   la grazia i monitor sono ancora zero, zero resteranno.
	 */
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_MS * 1000;
	while (g_get_monotonic_time() < scadenza) {
		g_usleep(CADENZA_CONTROLLO_MS * 1000);
		if (!sessione_viva())
			continue;
		if (viva_da == 0) {
			viva_da = g_get_monotonic_time();
			registro_dice(REG_SESSIONE,
			              "il compositore risponde; guardo che NON si sia preso un "
			              "monitor suo (grazia %d ms)",
			              GRAZIA_MONITOR_MS);
			continue;
		}
		if (g_get_monotonic_time() - viva_da < (gint64) GRAZIA_MONITOR_MS * 1000)
			continue;

		stato = sessione_stato(larghezza, altezza, &scelto);
		if (stato == SESSIONE_NERA) {
			if (avviata)
				*avviata = true;
			registro_dice(REG_SESSIONE,
			              "⭐ sessione grafica pronta e SENZA monitor propri: e' "
			              "quel che serve.  Il monitor lo montera' la cattura al "
			              "primo client, e la barra e la dock ci andranno sopra");
			return SESSIONE_NERA;
		}
		if (stato != SESSIONE_MORTA && stato != SESSIONE_NON_LETTA) {
			/* E' nata, e si e' presa un monitor: aspettare di piu' non
			 * cambierebbe niente, e il numero da dare e' questo. */
			if (avviata)
				*avviata = true;
			registro_dice(REG_SESSIONE,
			              "⛔ la sessione e' nata E SI E' PRESA UN MONITOR («%s»): "
			              "«%s».  Il mio drop-in non ha vinto, e l'utente "
			              "guardera' uno schermo vuoto",
			              scelto.prodotto, sessione_marca(stato));
			return stato;
		}
	}

	stato = sessione_stato(larghezza, altezza, NULL);
	registro_dice(REG_SESSIONE,
	              "⛔ la sessione grafica non ha risposto entro %d secondi: resta «%s»",
	              ATTESA_AVVIO_MS / 1000, sessione_marca(stato));
	return stato;
}
