#include "sessione.h"

#include <gio/gio.h>
#include <string.h>
#include <locale.h>

#include "registro.h"

/* Su questa VM, senza accelerazione grafica, la sessione ci mette una decina di
 * secondi: il margine e' per le macchine piu' lente. */
#define ATTESA_AVVIO_MS 40000
#define CADENZA_CONTROLLO_MS 500
#define ATTESA_RISPOSTA_MS 5000

/* Il perche' di questa funzione sta in sessione.h, ed e' una diagnosi costata
 * mezza fase: si legge prima di aggirarla. */
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
	if (bus_di_sessione && g_dbus_connection_is_closed(bus_di_sessione))
	{
		diagnostica("il bus di sessione si e' chiuso: se ne apre uno nuovo");
		g_clear_object(&bus_di_sessione);
	}

	if (!bus_di_sessione)
	{
		g_autofree char *indirizzo =
		    g_dbus_address_get_for_bus_sync(G_BUS_TYPE_SESSION, NULL, sbaglio);

		/*
		 * Connessione NOSTRA, non quella condivisa di `g_bus_get_sync`.
		 *
		 * Sono due cose diverse, e la differenza si paga: la condivisa e' un
		 * oggetto unico per tutto il processo, che GIO tiene in una cache e a cui
		 * accende «exit-on-close».  Aprendola noi, l'interruttore nasce spento e
		 * il ricambio dopo il logout dipende solo da questa funzione, non da come
		 * GIO gestisce la propria cache.
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

/* C'e' qualcuno con questo nome sul bus di sessione? */
static gboolean nome_occupato(GDBusConnection *bus, const char *nome)
{
	g_autoptr(GVariant) risposta = g_dbus_connection_call_sync(
	    bus, "org.freedesktop.DBus", "/org/freedesktop/DBus", "org.freedesktop.DBus",
	    "NameHasOwner", g_variant_new("(s)", nome), G_VARIANT_TYPE("(b)"), G_DBUS_CALL_FLAGS_NONE,
	    ATTESA_RISPOSTA_MS, NULL, NULL);
	gboolean c_e = FALSE;

	if (risposta)
		g_variant_get(risposta, "(b)", &c_e);
	return c_e;
}

gboolean sessione_viva(void)
{
	g_autoptr(GDBusConnection) bus = NULL;
	g_autoptr(GVariant) risposta = NULL;

	bus = sessione_bus(NULL);
	if (!bus)
		return FALSE;

	/*
	 * ⛔ NON BASTA CHE IL NOME SIA OCCUPATO: il nome di Mutter e' ATTIVABILE, e
	 *    chiederlo lo fa nascere.  Si chiama un metodo vero, e si guarda che la
	 *    risposta arrivi.
	 *
	 * Il tipo della risposta e' dichiarato NULL apposta: `GetCurrentState`
	 * restituisce l'intera configurazione degli schermi, una struttura annidata
	 * che cambia forma fra le versioni di Mutter.  Dichiararla significherebbe
	 * che un domani la vitalita' della sessione dipende dall'esattezza di quella
	 * dichiarazione — ed e' esattamente cosi' che la prima stesura dava per morta
	 * una sessione partita benissimo.  Qui interessa una cosa sola: che la
	 * risposta arrivi.
	 */
	risposta = g_dbus_connection_call_sync(
	    bus, "org.gnome.Mutter.DisplayConfig", "/org/gnome/Mutter/DisplayConfig",
	    "org.gnome.Mutter.DisplayConfig", "GetCurrentState", NULL, NULL, G_DBUS_CALL_FLAGS_NONE,
	    ATTESA_RISPOSTA_MS, NULL, NULL);
	if (risposta)
		return TRUE;

	/*
	 * E se non e' GNOME, e' KDE.
	 *
	 * ⛔ QUI IL NOME SI GUARDA E BASTA, e la differenza conta: `org.kde.KWin` NON
	 *    e' attivabile — non c'e' nessun file di servizio D-Bus che lo faccia
	 *    nascere — quindi «occupato» significa «il compositore e' vivo», che e'
	 *    esattamente la domanda.  Chiamare un metodo costerebbe di piu' e non
	 *    direbbe di piu'.
	 */
	return nome_occupato(bus, "org.kde.KWin");
}

/*
 * Una locale UTF-8, sempre.
 *
 * Non e' pignoleria: `gnome-terminal-server` si rifiuta di partire con una
 * locale non UTF-8 («Non UTF-8 locale (ANSI_X3.4-1968) is not supported!»,
 * uscita 8), e l'utente si ritrova un desktop in cui i programmi semplicemente
 * non si aprono, senza un errore da nessuna parte.
 */
/*
 * ⛔ E NON BASTA CHE IL NOME DICA UTF-8: QUELLA LOCALE DEVE ESISTERE.
 *    [M, 7 agosto 2026, e l'ha trovato l'utente: «il terminale non funziona»]
 *
 *    Il server porta `LANG=it_IT.UTF-8`, che di nome e' UTF-8 e passava il
 *    controllo qui sotto.  Ma sul ferro le locale GENERATE sono due — `C` e
 *    `C.utf8` — e `it_IT.UTF-8` non c'e': glibc ripiega in silenzio sulla `C`,
 *    che non e' UTF-8, e `gnome-terminal-server` si rifiuta di partire.  Il
 *    desktop resta in piedi e i programmi non si aprono, che e' esattamente il
 *    guasto che questa funzione esiste per evitare — passato dalla porta di
 *    servizio.
 *
 *    Il rootfs vive in RAM, quindi «basta generarla una volta» non basta: la
 *    verifica va fatta a ogni avvio, e la fa la libreria invece del nome.
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
	/* Debian genera `C.utf8`; glibc accetta anche la forma con il trattino, ma
	 * non su tutte le versioni: si provano tutte e due invece di scommettere. */
	static const char *RIPIEGHI[] = { "C.UTF-8", "C.utf8" };
	const char *lingua = g_getenv("LANG");
	gsize i;

	if (lingua && *lingua)
	{
		g_autofree char *maiuscolo = g_ascii_strup(lingua, -1);

		if (strstr(maiuscolo, "UTF-8") || strstr(maiuscolo, "UTF8"))
		{
			if (locale_esiste(lingua))
				return lingua;
			avviso("la locale «%s» e' UTF-8 di nome ma NON e' generata su questa macchina: "
			       "senza ripiego i programmi della sessione non si aprirebbero",
			       lingua);
		}
		else
		{
			avviso("la locale dell'ambiente («%s») non e' UTF-8", lingua);
		}
	}

	for (i = 0; i < G_N_ELEMENTS(RIPIEGHI); i++)
		if (locale_esiste(RIPIEGHI[i]))
		{
			informazione("la sessione partira' con la locale «%s»", RIPIEGHI[i]);
			return RIPIEGHI[i];
		}

	/* Nessuna locale UTF-8 sulla macchina: si dichiara, perche' da qui in poi
	 * il terminale non partira' e nessun altro lo spieghera'. */
	avviso("nessuna locale UTF-8 disponibile su questa macchina: il terminale della sessione "
	       "non partira' (si genera con «locale-gen C.UTF-8»)");
	return "C.UTF-8";
}

const char *sessione_comando_predefinito(TipoCompositore tipo)
{
	return tipo == COMPOSITORE_KWIN ? SESSIONE_COMANDO_KDE : SESSIONE_COMANDO_GNOME;
}

/*
 * La cartella da cui KDE legge le regole che gli imponiamo noi.
 *
 * Sta sotto `XDG_RUNTIME_DIR` e non sotto `~/.config` di proposito: quel che
 * scriviamo vale per la sessione che serviamo, e non deve sopravvivere alla
 * macchina ne' cambiare la configurazione che l'utente si e' scelto.  Si entra
 * in gioco appendendola a `XDG_CONFIG_DIRS`, dove KConfig la legge come
 * configurazione di SISTEMA — cioe' sotto quella dell'utente, e per questo le
 * voci si marcano immutabili.
 */
static char *cartella_regole(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	return runtime && *runtime ? g_build_filename(runtime, "remotix", "xdg", NULL) : NULL;
}

/* Dove mettiamo il tema del cursore, con la stessa regola di sopra. */
static char *cartella_cursori(void)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");

	return runtime && *runtime ? g_build_filename(runtime, "remotix", "icons", NULL) : NULL;
}

#define TEMA_CURSORE "remotix-invisibile"

/*
 * Un cursore che esiste ed e' trasparente — il formato Xcursor a mano.
 *
 * Un'immagine 1x1 con alfa zero.  Il formato e' semplicissimo e non merita una
 * dipendenza: intestazione di 16 byte, un indice di 12, e un blocco immagine di
 * 36 piu' i pixel.  Tutto little-endian, che e' quel che il formato prescrive.
 */
static gboolean scrivi_cursore_vuoto(const char *percorso)
{
	guint32 dati[] = {
		/* intestazione */
		GUINT32_TO_LE(0x72756358u), /* «Xcur» */
		GUINT32_TO_LE(16u),         /* quanto e' lunga l'intestazione */
		GUINT32_TO_LE(0x00010000u), /* versione 1.0 */
		GUINT32_TO_LE(1u),          /* un solo elemento nell'indice */
		/* indice: tipo immagine, misura nominale, dove sta */
		GUINT32_TO_LE(0xfffd0002u), GUINT32_TO_LE(24u), GUINT32_TO_LE(28u),
		/* blocco immagine */
		GUINT32_TO_LE(36u),         /* lunghezza dell'intestazione del blocco */
		GUINT32_TO_LE(0xfffd0002u), /* tipo: immagine */
		GUINT32_TO_LE(24u),         /* misura nominale */
		GUINT32_TO_LE(1u),          /* versione del blocco */
		GUINT32_TO_LE(1u),          /* larghezza */
		GUINT32_TO_LE(1u),          /* altezza */
		GUINT32_TO_LE(0u),          /* punto caldo x */
		GUINT32_TO_LE(0u),          /* punto caldo y */
		GUINT32_TO_LE(0u),          /* ritardo, per le animazioni */
		GUINT32_TO_LE(0u),          /* l'unico pixel: ARGB tutto zero */
	};

	return g_file_set_contents(percorso, (const char *) dati, sizeof dati, NULL);
}

/*
 * ⛔ LA CURA VERA DEL DOPPIO PUNTATORE: IL CURSORE DI KDE DIVENTA TRASPARENTE.
 *
 * *[8 agosto 2026, dopo che `SYSPTR_NULL` aveva funzionato su xfreerdp e NON su
 *   RDM: la' il secondo puntatore e' il *touch pointer* dell'applicazione, che
 *   vive fuori dal protocollo e nessun server puo' togliere.]*
 *
 * Il ragionamento di prima era giusto e la conclusione era corta.  Vero che con
 * `--virtual` KWin disegna il cursore DENTRO l'immagine e che non esiste leva
 * per impedirglielo; ma non serve impedirglielo — basta che quel che disegna
 * non si veda.  KWin prende il tema da `XCURSOR_THEME` **se c'e' anche
 * `XCURSOR_SIZE`** (`cursor.cpp:134-145`), e l'ambiente della sessione lo
 * componiamo noi.
 *
 * Da cui: un tema con un cursore 1x1 trasparente, e il puntatore torna a essere
 * quello che il client disegna da se' — **come su GNOME**, alla latenza della
 * rete invece che del video, e uno solo su tutti i client, compresi quelli che
 * il puntatore se lo disegnano per conto proprio.
 *
 * ⚠ IL TEMA DEVE CARICARSI DAVVERO.  Se `CursorTheme` risulta vuoto KWin
 *   ripiega sul tema predefinito (`pointer_input.cpp:1183-1196`), cioe' sul
 *   cursore visibile: un tema con zero forme non nasconde niente, lo rimette.
 *   Per questo le forme si scrivono tutte, e non solo `left_ptr`.
 *
 * ⚠ E le forme che NON scriviamo restano invisibili lo stesso, il che qui e'
 *   l'esito voluto: si perde il cambio di forma (la I sul testo, le frecce di
 *   ridimensionamento), esattamente come su GNOME oggi.  Restituirlo vuol dire
 *   mandare la forma vera sul canale puntatore di RDP, prendendola dai metadati
 *   PipeWire che gia' chiediamo — ed e' un lavoro a se'.
 */
static void scrivi_tema_cursore(void)
{
	/* I nomi che i programmi chiedono davvero.  Non e' l'elenco completo — non
	 * esiste — ma copre i temi di Breeze e Adwaita, e quel che manca resta
	 * invisibile, che e' dove volevamo arrivare. */
	static const char *forme[] = {
		"left_ptr", "default", "arrow", "top_left_arrow", "pointer", "hand", "hand1", "hand2",
		"pointing_hand", "text", "xterm", "ibeam", "wait", "watch", "progress", "left_ptr_watch",
		"crosshair", "cross", "tcross", "help", "question_arrow", "whats_this", "not-allowed",
		"forbidden", "crossed_circle", "no-drop", "dnd-none", "dnd-copy", "dnd-move", "dnd-link",
		"copy", "move", "link", "alias", "grab", "grabbing", "openhand", "closedhand", "all-scroll",
		"fleur", "size_hor", "size_ver", "size_fdiag", "size_bdiag", "col-resize", "row-resize",
		"ew-resize", "ns-resize", "nesw-resize", "nwse-resize", "sb_h_double_arrow",
		"sb_v_double_arrow", "top_side", "bottom_side", "left_side", "right_side", "top_left_corner",
		"top_right_corner", "bottom_left_corner", "bottom_right_corner", "zoom-in", "zoom-out",
		"cell", "context-menu", "vertical-text", "up_arrow", "center_ptr", "X_cursor",
	};
	g_autofree char *base = cartella_cursori();
	g_autofree char *tema = NULL;
	g_autofree char *cursori = NULL;
	g_autofree char *indice = NULL;
	guint scritte = 0;

	if (!base)
		return;

	tema = g_build_filename(base, TEMA_CURSORE, NULL);
	cursori = g_build_filename(tema, "cursors", NULL);
	indice = g_build_filename(tema, "index.theme", NULL);
	g_mkdir_with_parents(cursori, 0700);

	/* ⚠ Niente `Inherits=`: ereditare da un tema vero rimetterebbe in campo i
	 * cursori visibili per ogni forma che qui non c'e'. */
	if (!g_file_set_contents(indice,
	                         "[Icon Theme]\n"
	                         "Name=REMOTIX (invisibile)\n"
	                         "Comment=Cursore vuoto: su KWin --virtual il cursore sta dentro "
	                         "l'immagine catturata, e il client disegna il suo\n",
	                         -1, NULL))
	{
		avviso("tema del cursore non scritto: resteranno due puntatori");
		return;
	}

	for (guint i = 0; i < G_N_ELEMENTS(forme); i++)
	{
		g_autofree char *percorso = g_build_filename(cursori, forme[i], NULL);

		if (scrivi_cursore_vuoto(percorso))
			scritte++;
	}

	if (scritte == 0)
	{
		avviso("nessuna forma di cursore scritta: KWin ripieghera' sul tema visibile");
		return;
	}
	diagnostica("tema del cursore «%s»: %u forme trasparenti in %s", TEMA_CURSORE, scritte,
	            cursori);
}

/*
 * Le voci che in una sessione remota non hanno senso, tolte dal menu.
 *
 * «Blocca» e «Cambia utente» in una sessione servita da REMOTIX non funzionano,
 * ed e' il comportamento GIUSTO: il locker lo spegniamo noi con `--no-lockscreen`
 * perche' a blocco attivo powerdevil ignora le inibizioni (`kde.md` §10.2), e
 * cambiare utente vorrebbe dire un display manager che qui non c'e'.  Ma una
 * voce che non fa niente e' peggio di una voce che manca: chi la preme conclude
 * che il server e' rotto.  [chiesto dall'utente, 8 agosto 2026]
 *
 * La leva e' KIOSK, cioe' `KAuthorized`.  I nomi delle azioni non sono a
 * indovinare, sono quelli che Plasma interroga davvero:
 *
 *   `SessionManagement::canLock()`       -> `lock_screen`
 *   `SessionManagement::canSwitchUser()` -> `start_new_session`
 *                                           (`libkworkspace/sessionmanagement.cpp:121-129`)
 *   `SessionsModel::canSwitchUser()`     -> `switch_user`
 *                                           (`components/sessionsprivate/sessionsmodel.cpp:45`)
 *
 * ⚠ `switch_user` E `start_new_session` SERVONO TUTTI E DUE: il primo governa
 *   l'elenco delle sessioni, il secondo il pulsante.  Toglierne uno solo lascia
 *   meta' interfaccia.
 *
 * ⚠ `[$i]` non e' decorativo: senza, il `kdeglobals` dell'utente — che sta piu'
 *   in alto — rimetterebbe le voci al loro posto.
 *
 * ⛔ E `logout` NON SI TOCCA.  E' la strada con cui si chiude la sessione, ed e'
 *    quella su cui poggia la sentinella di uscita (`uscita.c`).
 */
static void scrivi_regole_menu(void)
{
	g_autofree char *cartella = cartella_regole();
	g_autofree char *percorso = NULL;
	g_autoptr(GError) sbaglio = NULL;

	if (!cartella)
		return;

	percorso = g_build_filename(cartella, "kdeglobals", NULL);
	g_mkdir_with_parents(cartella, 0700);
	if (!g_file_set_contents(percorso,
	                         "[KDE Action Restrictions][$i]\n"
	                         "action/lock_screen=false\n"
	                         "action/start_new_session=false\n"
	                         "action/switch_user=false\n",
	                         -1, &sbaglio))
	{
		/* Non e' un guasto da fermare la sessione: si perde la pulizia del menu,
		 * non il desktop. */
		avviso("regole del menu non scritte (%s): «Blocca» e «Cambia utente» resteranno",
		       sbaglio->message);
		return;
	}
	diagnostica("regole del menu in %s: niente blocco schermo, niente cambio utente", percorso);
}

/* L'ambiente della sessione, costruito da zero: quel che non serve non passa. */
static char **componi_ambiente(TipoCompositore tipo, GError **sbaglio)
{
	GPtrArray *ambiente = g_ptr_array_new_with_free_func(g_free);
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	const char *bus = g_getenv("DBUS_SESSION_BUS_ADDRESS");
	g_autofree char *bus_dedotto = NULL;

	if (!runtime || !*runtime)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "XDG_RUNTIME_DIR non impostata: non so dove vive la sessione");
		g_ptr_array_free(ambiente, TRUE);
		return NULL;
	}
	if (!bus || !*bus)
	{
		/* Il bus di sessione sta convenzionalmente li' dentro; dedurlo e'
		 * meglio che rinunciare, perche' un ambiente da cui la variabile manca
		 * — un'unita' systemd, per esempio — e' del tutto normale. */
		bus_dedotto = g_strdup_printf("unix:path=%s/bus", runtime);
		bus = bus_dedotto;
		diagnostica("DBUS_SESSION_BUS_ADDRESS assente: uso %s", bus);
	}

	/*
	 * Le due obbligatorie, e lo sono su tutti e due i compositori.
	 *
	 * ⛔ Senza `XDG_RUNTIME_DIR` il wrapper di KWin fa `qFatal` — `wl_socket_create()`
	 *    torna NULL — e senza `DBUS_SESSION_BUS_ADDRESS` `startplasma-wayland`
	 *    esce con 1 (`kde.md` §6.1).  Su GNOME valgono per le stesse ragioni.
	 */
	g_ptr_array_add(ambiente, g_strdup_printf("XDG_RUNTIME_DIR=%s", runtime));
	g_ptr_array_add(ambiente, g_strdup_printf("DBUS_SESSION_BUS_ADDRESS=%s", bus));

	if (tipo == COMPOSITORE_KWIN)
	{
		/*
		 * ⛔ `XDG_MENU_PREFIX` — LA VARIABILE CHE NESSUNO DOCUMENTA, E SENZA LA
		 *    QUALE LA CATTURA NON SI AUTORIZZA.
		 *
		 *    L'indice dei servizi di KDE si costruisce a partire da
		 *    `${XDG_MENU_PREFIX}applications.menu`, e Debian NON installa
		 *    `applications.menu`: installa `plasma-applications.menu`.  Senza il
		 *    prefisso `kbuildsycoca6` esce con stato ZERO e non indicizza NIENTE —
		 *    nemmeno le 133 applicazioni di sistema — e KWin, cercando il nostro
		 *    `.desktop`, dice «Could not find the desktop file».  Il sintomo e'
		 *    «questo compositore non espone il protocollo».
		 *
		 *    In una sessione Plasma vera la mette `startplasma`
		 *    (`startplasma.cpp:366`).  Qui l'ambiente lo componiamo noi, quindi
		 *    tocca a noi.  Cinque prove per trovarla, il 7 agosto 2026
		 *    (`kde.md` §3.3-bis, `LEZIONI.md` §1.10).
		 */
		g_ptr_array_add(ambiente, g_strdup("XDG_MENU_PREFIX=plasma-"));

		/*
		 * E la cartella delle nostre regole, DAVANTI a quella di sistema.
		 *
		 * ⚠ `/etc/xdg` va tenuto, e non per abitudine: da li' viene
		 *   `menus/plasma-applications.menu`, cioe' proprio il file che il
		 *   prefisso qui sopra va a cercare.  Sostituirlo invece che precederlo
		 *   spegnerebbe la cattura per la strada di §3.3-bis.
		 */
		{
			g_autofree char *regole = cartella_regole();

			if (regole)
				g_ptr_array_add(ambiente,
				                g_strdup_printf("XDG_CONFIG_DIRS=%s:%s", regole,
				                                g_getenv("XDG_CONFIG_DIRS") ?: "/etc/xdg"));
		}

		/*
		 * E il tema del cursore trasparente.
		 *
		 * ⛔ LE TRE VARIABILI VANNO INSIEME.  `XCURSOR_THEME` da sola non basta:
		 *    KWin la guarda **solo se c'e' anche `XCURSOR_SIZE`**
		 *    (`cursor.cpp:139` — `if (!themeName.isEmpty() && ok)`), altrimenti
		 *    ricade sul file di configurazione e il nostro tema non lo vede
		 *    nessuno.  E `XCURSOR_PATH` serve perche' il tema sta in
		 *    `XDG_RUNTIME_DIR`, che nessuna ricerca predefinita guarda — con le
		 *    cartelle di sistema in coda, per non togliere i temi veri a chi li
		 *    cerca per altro.
		 */
		{
			g_autofree char *icone = cartella_cursori();

			if (icone)
			{
				g_ptr_array_add(ambiente, g_strdup("XCURSOR_THEME=" TEMA_CURSORE));
				g_ptr_array_add(ambiente, g_strdup("XCURSOR_SIZE=24"));
				g_ptr_array_add(ambiente,
				                g_strdup_printf("XCURSOR_PATH=%s:%s", icone,
				                                "/usr/share/icons:/usr/local/share/icons"));
			}
		}
		/*
		 * ⛔ E NON SI DICHIARA NIENT'ALTRO.  `XDG_CURRENT_DESKTOP`,
		 *    `XDG_SESSION_TYPE`, `KDE_FULL_SESSION` e le altre le mette Plasma da
		 *    se' (`startplasma.cpp:353-414`); `DISPLAY`, `WAYLAND_DISPLAY` e
		 *    `QT_QPA_PLATFORM` **vanno lasciate fuori**, perche' con una di quelle
		 *    impostata KWin sceglie il backend ANNIDATO invece di `--virtual`
		 *    (`main_wayland.cpp:452-463`) e ksmserver forza `xcb`.
		 */
	}
	else
	{
		/* La sessione deve DICHIARARSI, o le applicazioni di GNOME non si
		 * riconoscono a casa propria e si fermano da sole (§5.6). */
		g_ptr_array_add(ambiente, g_strdup("XDG_CURRENT_DESKTOP=GNOME"));
		g_ptr_array_add(ambiente, g_strdup("XDG_SESSION_DESKTOP=gnome"));
		/*
		 * Qui XDG_SESSION_TYPE=wayland SERVE, e non e' la bugia punita in §5.6.
		 * L'unita' della Shell porta `ConditionEnvironment=XDG_SESSION_TYPE=wayland`:
		 * senza, il compositore non viene avviato affatto e la sessione parte monca
		 * senza che nessuno spieghi perche'.  La differenza con il caso punito e'
		 * che li' la si dichiarava AL POSTO di una sessione, qui DENTRO una
		 * sessione che esiste davvero e che la esporta ai propri servizi.
		 *
		 * ⚠ Su KDE non esiste alcun `ConditionEnvironment=` in nessuna unita' —
		 *   cercato in tutti e sette i repository (`kde.md` §6.1): il difetto
		 *   silenzioso che questa riga cura non ha un equivalente li'.
		 */
		g_ptr_array_add(ambiente, g_strdup("XDG_SESSION_TYPE=wayland"));
	}
	g_ptr_array_add(ambiente, g_strdup_printf("LANG=%s", locale_utf8()));
	g_ptr_array_add(ambiente, g_strdup_printf("HOME=%s", g_get_home_dir()));
	g_ptr_array_add(ambiente, g_strdup_printf("USER=%s", g_get_user_name()));
	g_ptr_array_add(ambiente, g_strdup_printf("PATH=%s", g_getenv("PATH") ?: "/usr/bin:/bin"));
	g_ptr_array_add(ambiente, NULL);

	return (char **) g_ptr_array_free(ambiente, FALSE);
}

/*
 * La sovrascrittura dell'unita' del compositore, che su KDE e' l'unica leva.
 *
 * `startplasma-wayland` NON lancia KWin: fa `StartUnit("plasma-workspace-wayland.target")`
 * (`startplasma.cpp:726`), e l'unita' del compositore ha un `ExecStart` fisso.
 * Il wrapper pero' rigira tutti i propri argomenti a `kwin_wayland`
 * (`kwin_wrapper.cpp:128-130`), quindi basta riscrivere quella riga.  La ricetta
 * — copia in `user.control` piu' `daemon-reload` — e' di KDE stessa
 * (`login-sessions/startplasma-dev.sh.cmake:8-13`).
 *
 * ⛔ E NON CI SI METTE DENTRO NIENTE CHE IMPLICHI UN MOUNT NAMESPACE.
 *    `InaccessiblePaths=` — la via ovvia per far scegliere a KWin la scheda
 *    giusta — CHIUDE IL CANCELLO DELLA CATTURA: 0 righe di registro sulla query
 *    dei permessi contro 13 nello stesso ambiente senza quella riga.  Misurato
 *    l'8 agosto 2026, e non e' la visibilita' dei file: dentro il namespace il
 *    `.desktop` e la cache si vedono benissimo (`kde.md` §3.3-bis e §5.6).
 *    La GPU si sceglie con i **permessi del nodo**, cioe' fuori di qui.
 *
 * ⚠ `--xwayland` c'e' e non si toglie senza averlo verificato: KWin non ne ha
 *   bisogno, **Plasma si** — `ksmserver` forza `QT_QPA_PLATFORM=xcb` e
 *   dereferenzia il display X11 senza controlli, ed e' `Requires=` della catena
 *   di sessione (`kde.md` §6.4).
 *
 * ⚠ `--no-lockscreen` non e' una comodita': a blocco attivo powerdevil IGNORA
 *   le inibizioni (`powerdevilpolicyagent.cpp:509`), quindi spegnere il locker
 *   e' una **dipendenza** di `energia.c`, non un di piu' (`kde.md` §10.2).
 */
static gboolean scrivi_dropin(uint32_t larghezza, uint32_t altezza, GError **sbaglio)
{
	const char *runtime = g_getenv("XDG_RUNTIME_DIR");
	g_autofree char *cartella = NULL;
	g_autofree char *percorso = NULL;
	g_autofree char *contenuto = NULL;
	g_autofree char *ksmserverrc = NULL;
	int stato = 0;
	char *argv[] = { "systemctl", "--user", "daemon-reload", NULL };

	if (!runtime)
	{
		g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_FAILED,
		            "XDG_RUNTIME_DIR non impostata: non so dove scrivere il drop-in");
		return FALSE;
	}

	cartella = g_build_filename(runtime, "systemd", "user.control",
	                            "plasma-kwin_wayland.service.d", NULL);
	percorso = g_build_filename(cartella, "remotix.conf", NULL);
	contenuto = g_strdup_printf(
	    "[Service]\n"
	    "ExecStart=\n"
	    "ExecStart=/usr/bin/kwin_wayland_wrapper --xwayland --virtual "
	    "--width %u --height %u --no-lockscreen\n",
	    larghezza, altezza);

	g_mkdir_with_parents(cartella, 0700);
	if (!g_file_set_contents(percorso, contenuto, -1, sbaglio))
		return FALSE;

	/*
	 * E la conferma di uscita si spegne: in una sessione non presidiata un
	 * dialogo che chiede «vuoi davvero uscire?» non lo vede nessuno e non gli
	 * risponde nessuno (`sessionmanagementbackend.cpp:49-52`).
	 */
	ksmserverrc = g_build_filename(g_get_user_config_dir(), "ksmserverrc", NULL);
	if (!g_file_test(ksmserverrc, G_FILE_TEST_EXISTS))
		g_file_set_contents(ksmserverrc, "[General]\nconfirmLogout=false\n", -1, NULL);

	/* E le voci di menu che non funzionerebbero, prima che il menu esista. */
	scrivi_regole_menu();
	/* E il cursore trasparente, prima che ci sia un cursore. */
	scrivi_tema_cursore();

	if (!g_spawn_sync(NULL, argv, NULL, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL, NULL, &stato,
	                  sbaglio))
		return FALSE;
	if (!g_spawn_check_wait_status(stato, sbaglio))
		return FALSE;

	informazione("unita' del compositore sovrascritta: desktop %ux%u, senza schermo di blocco",
	             larghezza, altezza);
	return TRUE;
}

static gboolean avvia(const char *comando, TipoCompositore tipo, GError **sbaglio)
{
	g_auto(GStrv) ambiente = NULL;
	g_autofree char *registro = NULL;
	g_autofree char *riga = NULL;
	/* `setsid --fork` stacca la sessione dal nostro gruppo di processi: se
	 * REMOTIX viene riavviato, il desktop dell'utente non se ne accorge. */
	char *argv[] = { "setsid", "--fork", "sh", "-c", NULL, NULL };
	int stato = 0;

	ambiente = componi_ambiente(tipo, sbaglio);
	if (!ambiente)
		return FALSE;

	registro = g_build_filename(g_getenv("XDG_RUNTIME_DIR"), "remotix-sessione.log", NULL);
	riga = g_strdup_printf("exec >>'%s' 2>&1; %s", registro, comando);
	argv[4] = riga;

	informazione("avvio la sessione grafica: %s (registro in %s)", comando, registro);
	if (!g_spawn_sync(g_get_home_dir(), argv, ambiente, G_SPAWN_SEARCH_PATH, NULL, NULL, NULL,
	                  NULL, &stato, sbaglio))
		return FALSE;
	return g_spawn_check_wait_status(stato, sbaglio);
}

gboolean sessione_assicura(const char *comando, TipoCompositore tipo, uint32_t larghezza,
                           uint32_t altezza, gboolean *avviata, GError **sbaglio)
{
	gint64 scadenza;

	if (avviata)
		*avviata = FALSE;

	if (sessione_viva())
	{
		diagnostica("la sessione grafica c'e' gia'");
		return TRUE;
	}

	informazione("nessuna sessione grafica: la avvio");
	/*
	 * ⛔ IL DROP-IN PRIMA DEL COMANDO, e non e' un ordine qualunque: la misura del
	 *    desktop ci sta dentro, e `startplasma-wayland` fa partire l'unita' del
	 *    compositore come prima cosa.  Scriverlo dopo significherebbe scriverlo
	 *    per la sessione SUCCESSIVA.
	 */
	if (tipo == COMPOSITORE_KWIN && !scrivi_dropin(larghezza, altezza, sbaglio))
		return FALSE;
	if (!avvia(comando ?: sessione_comando_predefinito(tipo), tipo, sbaglio))
		return FALSE;

	scadenza = g_get_monotonic_time() + (gint64) ATTESA_AVVIO_MS * 1000;
	while (g_get_monotonic_time() < scadenza)
	{
		g_usleep(CADENZA_CONTROLLO_MS * 1000);
		if (sessione_viva())
		{
			informazione("sessione grafica pronta");
			if (avviata)
				*avviata = TRUE;
			return TRUE;
		}
	}

	g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
	            "la sessione grafica non ha risposto entro %d secondi", ATTESA_AVVIO_MS / 1000);
	return FALSE;
}

/* Quanto si aspetta che la sessione se ne vada dopo averglielo chiesto con
 * garbo, prima di insistere. */
#define ATTESA_USCITA_MS 10000

/* `org.gnome.SessionManager.Logout`: 0 chiede conferma, 1 no, 2 forza. */
static gboolean esci_gnome(guint32 modo, GError **sbaglio)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(sbaglio);
	g_autoptr(GVariant) risposta = NULL;

	if (!bus)
		return FALSE;
	risposta = g_dbus_connection_call_sync(
	    bus, "org.gnome.SessionManager", "/org/gnome/SessionManager", "org.gnome.SessionManager",
	    "Logout", g_variant_new("(u)", modo), NULL, G_DBUS_CALL_FLAGS_NONE, ATTESA_RISPOSTA_MS,
	    NULL, sbaglio);
	return risposta != NULL;
}

static gboolean aspetta_che_finisca(void)
{
	gint64 scadenza = g_get_monotonic_time() + (gint64) ATTESA_USCITA_MS * 1000;

	while (g_get_monotonic_time() < scadenza)
	{
		g_usleep(CADENZA_CONTROLLO_MS * 1000);
		if (!sessione_viva())
			return TRUE;
	}
	return FALSE;
}

/*
 * L'uscita ordinata su KDE: `org.kde.Shutdown.logout()`.
 *
 * ⛔ NON E' `org.kde.ksmserver`, e non e' il prompt.  `org.kde.Shutdown` e' il
 *    nome ATTIVABILE che compare quando il logout comincia, ed e' anche quello
 *    che `startplasma` sorveglia per sapere che la sessione sta finendo
 *    (`startplasma.cpp:673-689`).  `org.kde.LogoutPrompt` invece chiede
 *    conferma, cioe' mostra una finestra che in una sessione non presidiata
 *    nessuno chiudera' mai.
 */
static gboolean esci_kde_ordinato(GError **sbaglio)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(sbaglio);
	g_autoptr(GVariant) risposta = NULL;

	if (!bus)
		return FALSE;
	risposta = g_dbus_connection_call_sync(bus, "org.kde.Shutdown", "/Shutdown",
	                                       "org.kde.Shutdown", "logout", NULL, NULL,
	                                       G_DBUS_CALL_FLAGS_NONE, ATTESA_RISPOSTA_MS, NULL,
	                                       sbaglio);
	return risposta != NULL;
}

/*
 * E la forzatura, che su KDE NON e' un `Logout(2)`.
 *
 * ⛔ `Logout(2)` non esiste [✗].  La forzatura e' fermare il target della
 *    sessione, ed e' quel che fa `plasma-shutdown` alla fine
 *    (`shutdown.cpp:151-157`).
 */
static gboolean esci_kde_a_forza(GError **sbaglio)
{
	g_autoptr(GDBusConnection) bus = sessione_bus(sbaglio);
	g_autoptr(GVariant) risposta = NULL;

	if (!bus)
		return FALSE;
	risposta = g_dbus_connection_call_sync(
	    bus, "org.freedesktop.systemd1", "/org/freedesktop/systemd1",
	    "org.freedesktop.systemd1.Manager", "StopUnit",
	    g_variant_new("(ss)", "plasma-workspace.target", "fail"), NULL, G_DBUS_CALL_FLAGS_NONE,
	    ATTESA_RISPOSTA_MS, NULL, sbaglio);
	return risposta != NULL;
}

gboolean sessione_termina(TipoCompositore tipo, GError **sbaglio)
{
	gboolean kde = (tipo == COMPOSITORE_KWIN);

	if (!sessione_viva())
		return FALSE;

	informazione("chiedo alla sessione grafica di uscire");
	if (!(kde ? esci_kde_ordinato(sbaglio) : esci_gnome(1, sbaglio)))
		return FALSE;
	if (aspetta_che_finisca())
	{
		informazione("la sessione grafica e' uscita");
		return TRUE;
	}

	avviso("la sessione non esce: la chiudo a forza, cio' che non e' salvato va perduto");
	if (!(kde ? esci_kde_a_forza(sbaglio) : esci_gnome(2, sbaglio)))
		return FALSE;
	if (aspetta_che_finisca())
		return TRUE;

	g_set_error(sbaglio, G_IO_ERROR, G_IO_ERROR_TIMED_OUT,
	            "la sessione grafica non e' uscita nemmeno a forza");
	return FALSE;
}
