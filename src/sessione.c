/*
 * sessione.c — la sessione GNOME headless nasce, e nasce CON un monitor.
 *
 * Il perche' di ogni scelta sta in `sessione.h`, che si legge per primo: qui ci
 * sono le ragioni che riguardano la RIGA, non il modulo.
 *
 * ---------------------------------------------------------------------------
 * ⛔ CHE COSA E' STATO PORTATO DA v1, E CHE COSA E' STATO LASCIATO LI'
 *
 * Portato (`v1/remotix-c/src/sessione.c`, 797 righe vere):
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
 *     KWin, e su GNOME **non serve** (`gnome.md` §5.2: la' il cursore non sta
 *     dentro l'immagine catturata);
 *   · `scrivi_regole_menu()` + `cartella_regole()` — il KIOSK di KDE.  Su GNOME
 *     l'equivalente e' il **lockdown di dconf** (`gnome.md` §5.1), che e' un
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

#include "registro.h"

#include <locale.h>
#include <string.h>

/* Su questa macchina, senza accelerazione, la sessione ci mette una decina di
 * secondi: il margine e' per le macchine piu' lente. */
#define ATTESA_AVVIO_MS 40000
#define CADENZA_CONTROLLO_MS 500
#define ATTESA_RISPOSTA_MS 5000
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

/* Una chiamata a Mutter, senza dichiarare il tipo della risposta. */
static GVariant *chiedi_a_mutter(GDBusConnection *bus, const char *nome, const char *oggetto,
                                 const char *interfaccia, const char *metodo, GError **sbaglio)
{
	return g_dbus_connection_call_sync(bus, nome, oggetto, interfaccia, metodo, NULL, NULL,
	                                   G_DBUS_CALL_FLAGS_NONE, ATTESA_RISPOSTA_MS, NULL,
	                                   sbaglio);
}

bool sessione_viva(void)
{
	g_autoptr(GDBusConnection) bus = NULL;
	g_autoptr(GVariant) risposta = NULL;

	bus = sessione_bus(NULL);
	if (!bus)
		return false;

	/*
	 * ⛔ NON BASTA CHE IL NOME SIA OCCUPATO, per due ragioni diverse e tutte e
	 *    due pagate: il nome di Mutter e' ATTIVABILE e chiederlo lo fa nascere;
	 *    e `org.gnome.Shell` la Shell **lo prende prima di
	 *    `meta_context_start()`** (`gnome.md` §3.2), quindi non e' un indicatore
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
		              "completa e NERA» di gnome.md §3.1 — non c'e' niente da catturare");
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
	 * ⛔ `SHELL` VUOTA, ed e' la trappola di `gnome.md` §3.1: `gnome-session.in:3-14`
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
	/*
	 * ⚠ E `XDG_SESSION_ID` NON si passa, di proposito.  `gnome.md` §3.1 avverte
	 *   che senza di essa Mutter puo' agganciare la sessione logind sbagliata —
	 *   ma quella che erediteremmo noi e' la sessione di CHI CI HA AVVIATI (un
	 *   ssh, cioe' `tty`), e regalargliela sarebbe mandarlo sulla sessione
	 *   sbagliata **con la nostra firma sopra**.  ⭐ La scena misurata sana il 12
	 *   agosto 2026 non la porta.  Resta `[?]` che cosa succeda quando REMOTIX
	 *   gira come unita' di sistema.
	 */
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
	char *ricarica[] = { "systemctl", "--user", "daemon-reload", NULL };
	char *mostra[] = { "systemctl",   "--user", "show", "-p", "ExecStart",
		           "--value", (char *) SESSIONE_UNITA_SHELL, NULL };

	if (!runtime || !*runtime) {
		registro_dice(REG_SESSIONE,
		              "⛔ XDG_RUNTIME_DIR non impostata: non so dove scrivere il drop-in");
		return FALSE;
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

	cartella = g_build_filename(runtime, "systemd", "user.control",
	                            SESSIONE_UNITA_SHELL ".d", NULL);
	percorso = g_build_filename(cartella, "zz-remotix-monitor.conf", NULL);
	/*
	 * ⚠ `--no-x11` c'e' e non si toglie a cuor leggero: e' la riga che la
	 *   macchina misurata sana il 12 agosto 2026 aveva davvero, e cambiarla
	 *   insieme al monitor vorrebbe dire cambiare due cose per volta.  Chi
	 *   vorra' le applicazioni X11 dentro la sessione la togliera' **da sola**,
	 *   e misurera' quella.
	 */
	contenuto = g_strdup_printf("[Service]\n"
	                            "ExecStart=\n"
	                            "ExecStart=%s --headless --no-x11 --virtual-monitor %ux%u\n",
	                            shell, larghezza, altezza);

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
	atteso = g_strdup_printf("--virtual-monitor %ux%u", larghezza, altezza);
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

	registro_dice(REG_SESSIONE,
	              "⭐ il monitor virtuale %ux%u lo chiede il PROGRAMMA (%s), e "
	              "l'ExecStart in vigore lo conferma: %s",
	              larghezza, altezza, percorso, vigore);
	return TRUE;
}

/* ------------------------------------------------------------------------- */
static gboolean avvia(void)
{
	g_auto(GStrv) ambiente = NULL;
	g_autofree char *registro = NULL;
	g_autofree char *riga = NULL;
	g_autoptr(GError) sbaglio = NULL;
	/* `setsid --fork` stacca la sessione dal nostro gruppo di processi: se
	 * REMOTIX viene riavviato, il desktop dell'utente non se ne accorge. */
	char *argv[] = { "setsid", "--fork", "sh", "-c", NULL, NULL };
	int stato = 0;

	ambiente = componi_ambiente();
	if (!ambiente)
		return FALSE;

	registro = g_build_filename(g_getenv("XDG_RUNTIME_DIR"), "remotix-sessione.log", NULL);
	riga = g_strdup_printf("exec >>'%s' 2>&1; %s", registro, SESSIONE_COMANDO_GNOME);
	argv[4] = riga;

	registro_dice(REG_SESSIONE, "avvio la sessione grafica: %s (il suo registro va in %s)",
	              SESSIONE_COMANDO_GNOME, registro);
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
 *    ripartire li' dentro e' un'altra prima esecuzione (`fasi/00-ambiente.md`,
 *    difetto 4 della fase 0).  E si guardano DUE cose — l'unita' e il processo —
 *    perche' `Logout` puo' lasciare il gestore vivo.
 */
static gboolean unita_inattiva(void)
{
	char *argv[] = { "systemctl", "--user", "is-active", (char *) SESSIONE_UNITA_GESTORE,
		         NULL };
	g_autofree char *stato = chiedi(argv);

	if (!stato)
		return FALSE;
	g_strstrip(stato);
	return g_strcmp0(stato, "inactive") == 0 || g_strcmp0(stato, "failed") == 0 ||
	       g_strcmp0(stato, "unknown") == 0;
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

bool sessione_termina(void)
{
	if (!sessione_viva()) {
		registro_dice(REG_SESSIONE, "non c'era nessuna sessione da fermare");
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
		registro_dice(REG_SESSIONE,
		              "la sessione grafica c'e' gia' e ha il monitor chiesto: non la "
		              "tocco (il palco appartiene alla sessione, I4)");
		return SESSIONE_SANA;
	case SESSIONE_NON_LETTA:
		registro_dice(REG_SESSIONE,
		              "⛔ non ho potuto leggere lo stato della sessione: NON tocco "
		              "niente.  «Non ho potuto guardare» non e' «non c'e'» (E8), e una "
		              "sessione buttata giu' per una lettura fallita e' un danno fatto "
		              "per un'ipotesi");
		return SESSIONE_NON_LETTA;
	case SESSIONE_MISURA_ALTRA:
		registro_dice(REG_SESSIONE,
		              "⚠ la sessione c'e' e il suo monitor e' %ux%u invece di %ux%u: "
		              "PROSEGUO con questa, perche' c'e' che cosa catturare e la misura "
		              "di una sessione gia' viva non si cambia a caldo (gnome.md §8.2). "
		              "Chi la vuole diversa la fa rinascere di proposito",
		              scelto.larghezza, scelto.altezza, larghezza, altezza);
		return SESSIONE_MISURA_ALTRA;
	case SESSIONE_SCELTO_DA_SE:
		registro_dice(REG_SESSIONE,
		              "⚠ la sessione c'e' ma il monitor non e' quello che ho chiesto io "
		              "(%u monitor, il primo e' «%s»): PROSEGUO e lo dichiaro — "
		              "rifarla nascere non curerebbe niente, perche' il monitor di "
		              "troppo lo crea uno ScreenCast di qualcun altro",
		              scelto.quanti, scelto.prodotto);
		return SESSIONE_SCELTO_DA_SE;
	case SESSIONE_NERA:
		registro_dice(REG_SESSIONE,
		              "⛔ LA SESSIONE C'E' ED E' NERA (zero monitor).  E' la forma esatta "
		              "del difetto vissuto due giorni su questa macchina: viva, completa "
		              "e senza niente da catturare.  La faccio RINASCERE, e lo scrivo "
		              "qui perche' una sessione che sparisce senza una riga e' peggio di "
		              "una sessione nera");
		break;
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
	 * ⛔ E PRIMA DI BUTTARE GIU' QUELLA NERA: se il drop-in non si puo' mettere
	 *    in vigore, farla rinascere darebbe un'altra sessione nera, e in piu'
	 *    avremmo portato via all'utente quella che c'era.
	 */
	if (!scrivi_dropin(larghezza, altezza)) {
		registro_dice(REG_SESSIONE,
		              "⛔ senza il drop-in in vigore la sessione nascerebbe NERA: non la "
		              "faccio nascere affatto, e lo stato resta «%s»",
		              sessione_marca(stato));
		return stato;
	}

	if (stato == SESSIONE_NERA && !sessione_termina()) {
		registro_dice(REG_SESSIONE,
		              "⛔ la sessione nera non se n'e' andata: non ne avvio una seconda "
		              "(una sessione grafica per utente, I2)");
		return sessione_stato(larghezza, altezza, NULL);
	}

	if (!avvia())
		return sessione_stato(larghezza, altezza, NULL);

	/*
	 * ⛔⭐ E QUI SI ASPETTA IL MONITOR, NON LA VITALITA'.
	 *
	 * v1 aspettava `sessione_viva()` e dichiarava «sessione grafica pronta»: e'
	 * esattamente la domanda che ha risposto di si' per due giorni su una
	 * macchina nera.  «E' viva» e «ha un monitor» sono due domande diverse, e
	 * qui si fa la seconda.
	 */
	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_MS * 1000;
	while (g_get_monotonic_time() < scadenza) {
		g_usleep(CADENZA_CONTROLLO_MS * 1000);
		if (!sessione_viva())
			continue;
		if (viva_da == 0) {
			viva_da = g_get_monotonic_time();
			registro_dice(REG_SESSIONE,
			              "il compositore risponde; aspetto il MONITOR (grazia %d ms)",
			              GRAZIA_MONITOR_MS);
			continue;
		}
		if (g_get_monotonic_time() - viva_da < (gint64) GRAZIA_MONITOR_MS * 1000)
			continue;

		stato = sessione_stato(larghezza, altezza, &scelto);
		if (stato == SESSIONE_SANA) {
			if (avviata)
				*avviata = true;
			registro_dice(REG_SESSIONE,
			              "⭐ sessione grafica pronta E con un monitor: «%s» «%s» "
			              "%ux%u@%.3f",
			              scelto.connettore, scelto.prodotto, scelto.larghezza,
			              scelto.altezza, scelto.refresh);
			return SESSIONE_SANA;
		}
		if (stato != SESSIONE_MORTA && stato != SESSIONE_NON_LETTA) {
			/* E' nata, e non e' quel che avevo chiesto: aspettare di piu' non
			 * cambierebbe niente, e il numero da dare e' questo. */
			if (avviata)
				*avviata = true;
			registro_dice(REG_SESSIONE, "⛔ la sessione e' nata, ed e' «%s»",
			              sessione_marca(stato));
			return stato;
		}
	}

	stato = sessione_stato(larghezza, altezza, NULL);
	registro_dice(REG_SESSIONE,
	              "⛔ la sessione grafica non ha dato un monitor entro %d secondi: resta "
	              "«%s»",
	              ATTESA_AVVIO_MS / 1000, sessione_marca(stato));
	return stato;
}
