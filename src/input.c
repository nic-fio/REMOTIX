/*
 * input.c — l'input arriva DAVVERO al desktop: `input.h` attuato su `libei`.
 *
 * ⛔ Il contratto sta in `input.h`, che e' del coordinatore: qui si ATTUA, non
 *    si cambia la cucitura.  Chi trova il contratto sbagliato lo DICE e si
 *    ferma — non lo aggira.  *(I due punti in cui e' stato detto stanno in
 *    `fasi/rapporti/F4-A4-iniezione.md` §5.)*
 *
 * ⛔ RIPORTATO da `v1/remotix-c/src/input.c` (906 righe), e non ricopiato.  Di
 *    v1 resta ⭐ **la meccanica di libei** — il ciclo `poll`/`ei_dispatch`, la
 *    presa dei dispositivi, `start_emulating`, `ei_device_frame` dopo ogni
 *    evento — che e' il patrimonio vero.  ⛔ Cade tutto il contorno RDP
 *    (`freerdp/input.h`, i `PTR_FLAGS_*`, i `KBD_FLAGS_*`), che qui non
 *    esiste: sul filo c'e' `RCP.md` §7.3, e i codici sono gia' evdev.
 *
 * ⛔⛔ E CADONO DUE COSE DI v1 CHE ERANO **SBAGLIATE**, non solo inutili — e
 *      sono la meta' del lavoro di questo file:
 *
 *   1. `compositore_mapping_id`: v1 cercava la regione con l'UUID **dichiarato
 *      da noi** a `RecordVirtual`.  Mutter quella proprieta' la ignora, e
 *      l'UUID vero lo genera lui: v1 non trovava **mai** la regione per chiave
 *      e cadeva ogni volta sul ripiego «prendo la prima» — verde con uno
 *      schermo, storto con due (`mutter.h`, `gnome.md` §9);
 *   2. `ei_device_scroll_discrete`: Mutter ne fa una **divisione intera per
 *      120** (`meta-eis-client.c:554`), e i mezzi scatti spariscono.  Qui si
 *      va di `scroll_delta`, dove Mutter forza `SOURCE_WHEEL`, salta
 *      l'accumulatore, e la soglia vera di uno scatto e' **60**.
 *
 * ---------------------------------------------------------------------------
 * ⛔ UN THREAD SOLO, ED E' QUELLO DI CHI CHIAMA
 *
 * v1 aveva un thread suo e una coda, perche' il ciclo di FreeRDP non era suo.
 * Qui no: `input_gira()` esiste apposta nel contratto perche' il ciclo del
 * figlio chiami questo modulo a ogni giro.  ⇒ **Nessun lucchetto, nessuna
 * coda, nessun thread** — e nessuna attesa dentro il ciclo asincrono
 * (`CODER.md` §4.4).
 *
 * ⛔ Il prezzo, e va detto al coordinatore invece che scoperto: **tutte** le
 *    funzioni di `input.h` vanno chiamate dallo STESSO thread che chiama
 *    `input_gira()`.  `libei` non e' rientrante, e due thread su un `struct ei`
 *    sono un difetto che non da' errore.
 *
 * ---------------------------------------------------------------------------
 * ⛔⛔ IL CONTO DI QUEL CHE E' PREMUTO — `RCP.md` §11
 *
 * *«la regola col rapporto danno/costo piu' alto del documento»*: un Ctrl
 * rimasto giu' in una sessione che sopravvive al client rende il desktop
 * inservibile al riattacco, e nessuno collega le due cose.
 *
 * ⇒ Ogni tasto e ogni pulsante che si preme si SEGNA, e ogni rilascio si
 *   cancella.  Due mappe di bit, e `input_rilascia_tutto()` le svuota
 *   ritornando quanti ne ha rilasciati — perche' il banco possa contarli.
 *
 * ⚠ E Mutter fa da rete di sicurezza **solo su libei**: `drop_device`
 *   (`meta-eis-client.c:144-168`) rilascia tutto quando il client EIS cade.
 *   ⛔ Non e' una ragione per non contare: la rete scatta quando il canale si
 *   chiude, e il distacco di un client **non** chiude la sessione (invariante
 *   I4 — il palco sopravvive al distacco).
 */
#include "input.h"

#include <errno.h>
#include <gio/gio.h>
#include <libei.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "mutter.h"
#include "registro.h"
#include "tastiera.h"

#define AREA "input"

/*
 * ⛔ I due tetti di Mutter, letti nel codice (`meta-eis-client.c:30-31` `[R]`):
 *    oltre, l'evento si scarta **in silenzio**.  Le mappe di bit li coprono per
 *    intero: cosi' «l'ho segnato» e «l'ho mandato» non possono divergere.
 */
#define MAX_TASTO 0x300u
#define MAX_BOTTONE 0x300u
#define BIT_BYTE(n) (((n) + 7u) / 8u)

/*
 * ⛔ 120 unita' di `RCP.md` §7.3 = uno scatto = **10.0** di `ei_device_scroll_delta`
 *    su Mutter, cioe' un fattore 12.
 *
 * `[R]` `meta-virtual-input-device-native.c:752-756`: con `SOURCE_WHEEL` Mutter
 * fa `dy * (120.0 / 10.0)` e ottiene il `v120`; `meta-seat-impl.c:1239` emette
 * uno scatto discreto quando l'accumulatore supera **60**, cioe' mezzo scatto.
 *
 * ⇒ 60 unita' (mezzo scatto) diventano `5.0`, che diventano `v120 = 60`, che
 *   **producono uno scatto**.  Con `ei_device_scroll_discrete` sarebbero
 *   diventate `60 / 120 = 0` e non avrebbero prodotto niente.
 *
 * ⚠ E il 12 e' di MUTTER, non del protocollo: su KWin `scroll_delta` non
 *   produce nessuno scatto (`kde.md` §7.2) e la strada e' `scroll_discrete`.
 *   Il giorno che si scrive `kwin.c` questa costante NON si porta dietro.
 */
#define UNITA_PER_DELTA 12.0

struct input
{
	MutterSessione *sessione;
	struct ei *ei;

	/* La TELA di `RCP.md` §4.5, cioe' l'intervallo in cui `rcp.c` ha gia'
	 * verificato che stiano le coordinate che arrivano. */
	uint32_t tela_l, tela_a;

	/* ⛔ Il dispositivo ASSOLUTO, e non «il primo che sa scorrere»: Mutter ne
	 *    offre due, e quello relativo NON ha regioni — col relativo il puntatore
	 *    finisce dove capita (`banchi/01-s7-rotella.c`, `[M]` 10 agosto 2026). */
	struct ei_device *puntatore;
	struct ei_device *tastiera_dev;
	gboolean puntatore_attivo;
	gboolean tastiera_attiva;
	uint32_t sequenza;

	/* La regione su cui il puntatore si muove, in coordinate globali logiche. */
	gboolean regione_nota;
	gboolean regione_scalata_lamentata;
	double reg_x, reg_y, reg_l, reg_a;
	char *reg_per; /* «chiave», «geometria», «unica»: come l'abbiamo scelta */

	Tastiera *disposizione;
	char *keymap_nome; /* il nome che libei pubblica, per VEDERE un ricambio */

	/* ⛔⛔ IL CONTO.  Vedi il riquadro in testa al file. */
	uint8_t tasti[BIT_BYTE(MAX_TASTO)];
	uint8_t bottoni[BIT_BYTE(MAX_BOTTONE)];
	unsigned quanti_tasti;
	unsigned quanti_bottoni;

	/* I ricambi silenziosi, contati: il banco li legge invece di dedurli. */
	unsigned ricambi_puntatore;
	unsigned ricambi_tastiera;

	gboolean caduto; /* il compositore ha chiuso il canale */
};

/* ------------------------------------------------------------------ *
 *  Le mappe di bit — «segnato» e «mandato» non devono poter divergere
 * ------------------------------------------------------------------ */
static gboolean bit_leggi(const uint8_t *mappa, uint32_t n)
{
	return (mappa[n / 8u] & (uint8_t) (1u << (n % 8u))) != 0;
}

static void bit_scrivi(uint8_t *mappa, uint32_t n, gboolean acceso)
{
	if (acceso)
		mappa[n / 8u] |= (uint8_t) (1u << (n % 8u));
	else
		mappa[n / 8u] &= (uint8_t) ~(1u << (n % 8u));
}

/* ------------------------------------------------------------------ *
 *  L'invio
 * ------------------------------------------------------------------ */

/*
 * ⛔ `ei_device_frame` DOPO OGNI evento, e non a gruppi.
 *
 * Su Mutter non serve a niente — il `FRAME` e' ignorato, con accanto un FIXME
 * che dice «we should be accumulating the above events» (`meta-eis-client.c:1033`
 * `[R]`).  ⛔ Su KWin e su wlroots e' **obbligatorio**: senza, l'evento non
 * esce affatto.  Mandarlo qui e' gratis, ed e' l'unica forma portabile.
 */
static void batti_cornice(Input *in, struct ei_device *dispositivo)
{
	ei_device_frame(dispositivo, ei_now(in->ei));
}

static int manda_tasto(Input *in, uint16_t codice, int premuto)
{
	if (codice >= MAX_TASTO)
	{
		registro_dice(AREA, "⚠ codice di tasto 0x%X fuori dal massimo di Mutter (0x%X): Mutter lo "
		                    "scarterebbe in SILENZIO, quindi lo rifiuto io e lo dico",
		              codice, MAX_TASTO - 1);
		return -1;
	}
	if (!in->tastiera_dev || !in->tastiera_attiva)
		return -1;

	ei_device_keyboard_key(in->tastiera_dev, codice, premuto != 0);
	batti_cornice(in, in->tastiera_dev);

	/* ⛔ Il conto si tiene DOPO l'invio: segnare un tasto che non e' partito
	 *    farebbe rilasciare al distacco qualcosa che nessuno ha premuto. */
	if ((premuto != 0) != bit_leggi(in->tasti, codice))
	{
		bit_scrivi(in->tasti, codice, premuto != 0);
		if (premuto)
			in->quanti_tasti++;
		else if (in->quanti_tasti)
			in->quanti_tasti--;
	}
	return 0;
}

static int manda_bottone(Input *in, uint16_t codice, int premuto)
{
	if (codice >= MAX_BOTTONE)
	{
		registro_dice(AREA, "⚠ codice di pulsante 0x%X fuori dal massimo: rifiutato", codice);
		return -1;
	}
	if (!in->puntatore || !in->puntatore_attivo)
		return -1;

	ei_device_button_button(in->puntatore, codice, premuto != 0);
	batti_cornice(in, in->puntatore);

	if ((premuto != 0) != bit_leggi(in->bottoni, codice))
	{
		bit_scrivi(in->bottoni, codice, premuto != 0);
		if (premuto)
			in->quanti_bottoni++;
		else if (in->quanti_bottoni)
			in->quanti_bottoni--;
	}
	return 0;
}

/* ------------------------------------------------------------------ *
 *  La regione: quale schermo e' il nostro
 * ------------------------------------------------------------------ */

/*
 * ⛔ SI RILEGGE A OGNI `DEVICE_ADDED`, non una volta all'avvio.
 *
 * `[R]` `meta-eis-client.c:1048-1062`: qualunque cambio di geometria fa
 * `remove_viewport_devices` + ricrea.  Dal nostro lato: `DEVICE_REMOVED` →
 * `DEVICE_ADDED` → `DEVICE_RESUMED`, e ⛔ **il puntatore al dispositivo vecchio
 * smette di funzionare SENZA ERRORE**.  Un banco che legge la regione una volta
 * sola resta VERDE mentre il difetto e' vivo (`CODER.md` §3.4).
 *
 * Tre criteri in ordine, e ciascuno si DICHIARA:
 *
 *   per CHIAVE     il `mapping-id` che **Mutter** pubblica nei `Parameters`
 *                  del flusso.  E' un'identita', e non si sbaglia.
 *   per GEOMETRIA  la regione grande come la tela.  E' l'unico criterio che
 *                  esista quando le regioni sono anonime — i viewport «monitor
 *                  logico» hanno `mapping_id == NULL` (`[R]` §7.1), e su KWin
 *                  `eis_region_set_mapping_id` non e' chiamato mai.
 *   UNICA          se la regione e' una sola, e' quella.  ⛔ «La prima» quando
 *                  sono due non si sceglie: si dichiara di non sapere, perche'
 *                  sbagliare regione manda il puntatore su un altro schermo
 *                  **senza errore** (`meta-eis-client.c:470-472`).
 */
static void leggi_regione(Input *in, struct ei_device *dispositivo)
{
	const char *chiave = mutter_mapping_id_pubblicato(in->sessione);
	struct ei_region *per_chiave = NULL, *per_geometria = NULL, *unica = NULL;
	size_t quante = 0;
	struct ei_region *scelta = NULL;
	const char *per = NULL;

	in->regione_nota = FALSE;
	g_clear_pointer(&in->reg_per, g_free);

	for (size_t i = 0;; i++)
	{
		struct ei_region *regione = ei_device_get_region(dispositivo, i);
		const char *id;

		if (!regione)
			break;
		quante++;
		unica = regione;
		id = ei_region_get_mapping_id(regione);

		/* ⛔ I getter tornano `uint32_t`, non `double`: passarli a un `%.0f`
		 *    stampa spazzatura che si legge come una diagnosi vera («la regione
		 *    e' 0x0») mentre la regione e' 1920x1080.  `[M]` 10 agosto 2026. */
		registro_dettaglio(AREA, "regione %zu: %u,%u %ux%u (mapping-id «%s»)", i,
		                   ei_region_get_x(regione), ei_region_get_y(regione),
		                   ei_region_get_width(regione), ei_region_get_height(regione),
		                   id ?: "assente");

		if (!per_chiave && chiave && id && g_strcmp0(id, chiave) == 0)
			per_chiave = regione;
		if (!per_geometria && in->tela_l && in->tela_a &&
		    ei_region_get_width(regione) == in->tela_l &&
		    ei_region_get_height(regione) == in->tela_a)
			per_geometria = regione;
	}

	if (per_chiave)
	{
		scelta = per_chiave;
		per = "chiave";
	}
	else if (per_geometria)
	{
		scelta = per_geometria;
		per = "geometria";
	}
	else if (quante == 1)
	{
		scelta = unica;
		per = "unica";
	}

	if (!scelta)
	{
		registro_dice(AREA,
		              "⛔ NESSUNA regione riconosciuta fra le %zu annunciate (chiave «%s», tela "
		              "%ux%u): il puntatore NON si muove, e non tiro a indovinare quale sia",
		              quante, chiave ?: "ignota", in->tela_l, in->tela_a);
		return;
	}

	in->reg_x = ei_region_get_x(scelta);
	in->reg_y = ei_region_get_y(scelta);
	in->reg_l = ei_region_get_width(scelta);
	in->reg_a = ei_region_get_height(scelta);
	in->regione_nota = in->reg_l > 0 && in->reg_a > 0;
	in->reg_per = g_strdup(per);

	registro_dice(AREA, "regione del puntatore per %s: %.0f,%.0f %.0fx%.0f (di %zu, mapping-id «%s»)",
	              per, in->reg_x, in->reg_y, in->reg_l, in->reg_a, quante,
	              ei_region_get_mapping_id(scelta) ?: "assente");
}

/* ------------------------------------------------------------------ *
 *  La disposizione della tastiera
 * ------------------------------------------------------------------ */

/*
 * ⛔⛔ LA DISPOSIZIONE ARRIVA DA `libei`, E SI RIAPRE A OGNI `DEVICE_ADDED`.
 *
 * ⭐ Il verso e' questo, e non l'altro: **non scegliamo noi** la disposizione
 *    della sessione — la sceglie GNOME, e `libei` ce la consegna col
 *    dispositivo tastiera, come testo XKB su un descrittore.  *(Il contratto
 *    diceva «`tastiera_apri("it")`»; l'anello A5 ha rifiutato quel pezzo e
 *    aveva ragione — `input.h`/`tastiera.h`, 14 agosto 2026.)*
 *
 * ⛔ E A OGNI `DEVICE_ADDED`, non una volta all'avvio: `on_keymap_changed`
 *    (`meta-eis-client.c:761-781` `[R]`) fa `eis_device_remove` +
 *    `add_device` con la keymap nuova, col commento *«Changing the keymap
 *    means we have to remove our device and recreate it»*.  Chi apre la
 *    disposizione una volta sola resta con quella vecchia dopo un cambio, e
 *    ⛔ **le lettere escono diverse senza che niente dia errore**.
 */
static void leggi_keymap(Input *in, struct ei_device *dispositivo)
{
	struct ei_keymap *keymap = ei_device_keyboard_get_keymap(dispositivo);
	g_autofree char *testo = NULL;
	g_autofree char *impronta = NULL;
	g_autofree char *sbaglio = NULL;
	Tastiera *nuova;
	int fd;
	size_t misura;

	if (!keymap)
	{
		/* ⛔ Il dispositivo esiste, la keymap no: `configure_keyboard` esce
		 *    DOPO aver dichiarato la capacita' tastiera se
		 *    `meta_backend_get_keymap` da' NULL (`:242-246` `[R]`).  Va retto,
		 *    e si dichiara invece di ripiegare in silenzio. */
		registro_dice(AREA, "⚠ il dispositivo tastiera non porta nessuna keymap: le LETTERE "
		                    "restano spente (le POSIZIONI no)");
		g_clear_pointer(&in->disposizione, tastiera_chiudi);
		g_clear_pointer(&in->keymap_nome, g_free);
		return;
	}
	if (ei_keymap_get_type(keymap) != EI_KEYMAP_TYPE_XKB)
	{
		registro_dice(AREA, "⚠ keymap di tipo sconosciuto (%d): ignorata",
		              (int) ei_keymap_get_type(keymap));
		return;
	}

	fd = ei_keymap_get_fd(keymap);
	misura = ei_keymap_get_size(keymap);
	if (fd < 0 || misura == 0)
		return;

	/* ⛔ `pread` e non `read`: il descrittore della keymap e' condiviso, e
	 *    consumarne la posizione lo romperebbe per chi lo rilegge dopo. */
	testo = g_malloc0(misura + 1);
	if (pread(fd, testo, misura, 0) < 0)
	{
		registro_dice(AREA, "⚠ la keymap non si legge: %s", g_strerror(errno));
		return;
	}

	/*
	 * L'IMPRONTA della keymap, e non il suo nome.
	 *
	 * ⛔ `[M]` 14 agosto 2026, sulla macchina di prova: la keymap che Mutter
	 *    serializza porta `xkb_symbols "(unnamed)"` — **il nome non c'e'**.  Un
	 *    banco che cercasse un cambio di NOME vedrebbe «(unnamed)» prima e
	 *    dopo, cioe' resterebbe verde mentre la disposizione e' cambiata: e'
	 *    `CODER.md` §3.4 in atto.  ⇒ Misura in byte piu' una somma di
	 *    controllo, che cambiano per forza se la disposizione cambia.
	 */
	impronta = g_strdup_printf("%zu byte, impronta %08x", misura, (unsigned) g_str_hash(testo));

	/*
	 * ⛔ La disposizione si RIAPRE, non si aggiorna: `tastiera.h` non ha un
	 *    modo di cambiare la keymap sotto una `Tastiera` viva, ed e' giusto
	 *    cosi' — un oggetto che cambia identita' sotto chi lo tiene e' il
	 *    difetto che stiamo misurando, non la cura.
	 *
	 * ⚠ E la vecchia si chiude SOLO se la nuova si apre: se la keymap nuova
	 *   non si compila, restare con quella di prima e' meglio che restare senza
	 *   — e la riga lo dice, cosi' il ripiego non e' silenzioso.
	 */
	/*
	 * ⚠ `negoziata` e' **NULL, e per adesso e' giusto** — ma va detto, perche'
	 *   ha una conseguenza che si legge come un difetto:
	 *
	 *   `tastiera.c` confronta la disposizione dichiarata dal client in
	 *   `ATTACCA` (`RCP.md` §4.5) con quella vera della sessione, e se non
	 *   combaciano usa quella della SESSIONE scrivendo `RIPIEGO DICHIARATO`.
	 *   ⛔ Con `NULL` quel confronto **non si fa mai**, quindi quella riga non
	 *   uscira' mai: chi la cercasse nel registro concluderebbe «combaciano
	 *   sempre», che e' una cosa diversa da «non ho guardato».
	 *
	 * ⇒ Il giorno che la disposizione negoziata arriva fin qui (oggi `input.h`
	 *   non la porta: `input_apri` non la prende, ed e' una scelta del
	 *   coordinatore), si passa **quella** al posto di questo NULL e non serve
	 *   altro.  *(Riga lasciata da A5, 14 agosto 2026.)*
	 */
	nuova = tastiera_apri_da_keymap(testo, misura, NULL, &sbaglio);
	if (!nuova)
	{
		registro_dice(AREA, "⚠ la keymap consegnata da libei non si apre (%s): %s",
		              sbaglio ?: "senza motivo dichiarato",
		              in->disposizione ? "tengo quella di prima" : "le LETTERE restano spente");
	}
	else
	{
		g_clear_pointer(&in->disposizione, tastiera_chiudi);
		in->disposizione = nuova;
	}

	if (g_strcmp0(impronta, in->keymap_nome) != 0)
	{
		registro_dice(AREA, "KEYMAP CAMBIATA: %s (era: %s) → disposizione «%s»", impronta,
		              in->keymap_nome ?: "nessuna",
		              in->disposizione ? tastiera_disposizione(in->disposizione) : "nessuna");
		g_free(in->keymap_nome);
		in->keymap_nome = g_steal_pointer(&impronta);
	}
	else
		registro_dettaglio(AREA, "keymap invariata: %s", impronta);
}

/* ------------------------------------------------------------------ *
 *  Gli eventi di libei
 * ------------------------------------------------------------------ */
static void dispositivo_aggiunto(Input *in, struct ei_device *dispositivo)
{
	gboolean assoluto = ei_device_has_capability(dispositivo, EI_DEVICE_CAP_POINTER_ABSOLUTE);
	gboolean tasti = ei_device_has_capability(dispositivo, EI_DEVICE_CAP_KEYBOARD);

	registro_dettaglio(AREA, "dispositivo «%s»: assoluto=%d scorrimento=%d bottoni=%d tastiera=%d",
	                   ei_device_get_name(dispositivo) ?: "?", assoluto,
	                   ei_device_has_capability(dispositivo, EI_DEVICE_CAP_SCROLL),
	                   ei_device_has_capability(dispositivo, EI_DEVICE_CAP_BUTTON), tasti);

	/*
	 * ⛔ SI PRENDE SEMPRE L'ULTIMO ARRIVATO, e non «il primo che va bene».
	 *
	 * E' la differenza fra reggere un ricambio e non reggerlo: dopo un cambio
	 * di geometria Mutter manda `DEVICE_REMOVED` + `DEVICE_ADDED`, e chi tiene
	 * il primo resta attaccato a un oggetto morto **che non da' errore**.
	 */
	if (assoluto)
	{
		/* ⚠ Qui NON si conta il ricambio: lo conta `dispositivo_tolto`, che
		 *   arriva prima.  Contarlo in tutt'e due i posti lo raddoppierebbe. */
		if (in->puntatore)
			ei_device_unref(in->puntatore);
		in->puntatore = ei_device_ref(dispositivo);
		in->puntatore_attivo = FALSE;
		leggi_regione(in, dispositivo);
	}
	if (tasti)
	{
		if (in->tastiera_dev)
			ei_device_unref(in->tastiera_dev);
		in->tastiera_dev = ei_device_ref(dispositivo);
		in->tastiera_attiva = FALSE;
		leggi_keymap(in, dispositivo);
	}
}

static void dispositivo_tolto(Input *in, struct ei_device *dispositivo)
{
	if (in->puntatore == dispositivo)
	{
		/* ⛔ E il conto di quel che era premuto NON si azzera: il dispositivo se
		 *    n'e' andato, i tasti dell'utente no.  Al ricambio si rilascia sul
		 *    dispositivo nuovo, che e' l'unico posto dove il rilascio arriva. */
		ei_device_unref(in->puntatore);
		in->puntatore = NULL;
		in->puntatore_attivo = FALSE;
		in->regione_nota = FALSE;
		/* ⛔ IL RICAMBIO SI CONTA QUI, NON SOLO SULL'AGGIUNTA — `[M]` 14 agosto
		 *    2026, e il banco l'ha pagato: Mutter manda `DEVICE_REMOVED` **e
		 *    poi** `DEVICE_ADDED`, quindi al momento dell'aggiunta il vecchio
		 *    e' gia' NULL e un contatore che guarda solo li' resta a **zero**.
		 *    ⚠ Il banco stampava «il ricambio NON e' stato riprodotto» mentre il
		 *    testimone vedeva il posto perdere tastiera e puntatore: uno
		 *    strumento cieco proprio nel caso che deve vedere (`CODER.md` §3.4). */
		in->ricambi_puntatore++;
		registro_dice(AREA, "il puntatore e' stato TOLTO dal compositore (ricambio n. %u)",
		              in->ricambi_puntatore);
	}
	if (in->tastiera_dev == dispositivo)
	{
		ei_device_unref(in->tastiera_dev);
		in->tastiera_dev = NULL;
		in->tastiera_attiva = FALSE;
		in->ricambi_tastiera++;
		registro_dice(AREA, "la tastiera e' stata TOLTA dal compositore (ricambio n. %u)",
		              in->ricambi_tastiera);
	}
}

static void tratta_evento(Input *in, struct ei_event *evento)
{
	enum ei_event_type tipo = ei_event_get_type(evento);
	struct ei_device *dispositivo = ei_event_get_device(evento);

	switch (tipo)
	{
		case EI_EVENT_SEAT_ADDED:
			/*
			 * ⛔ Si CHIEDONO le capacita', e i dispositivi li crea il
			 *    compositore.  ⚠ `POINTER` (relativo) si chiede lo stesso pur
			 *    non usandolo: senza, Mutter non crea nemmeno l'assoluto?  No —
			 *    `[R]` `meta-eis-client.c:1108-1114` li lega separatamente.  Si
			 *    chiede perche' `RCP.md` §7.3 tiene aperto il puntatore
			 *    relativo per il `Pointer Lock` della pagina (fase 4, anello A7),
			 *    e la `MetaEis` si crea **una volta sola per sessione**: quel
			 *    che non si chiede adesso non si puo' chiedere piu'.
			 */
			ei_seat_bind_capabilities(ei_event_get_seat(evento), EI_DEVICE_CAP_POINTER,
			                          EI_DEVICE_CAP_POINTER_ABSOLUTE, EI_DEVICE_CAP_BUTTON,
			                          EI_DEVICE_CAP_SCROLL, EI_DEVICE_CAP_KEYBOARD, NULL);
			registro_dettaglio(AREA, "posto «%s»: capacita' chieste",
			                   ei_seat_get_name(ei_event_get_seat(evento)) ?: "?");
			break;

		case EI_EVENT_DEVICE_ADDED:
			dispositivo_aggiunto(in, dispositivo);
			break;

		case EI_EVENT_DEVICE_REMOVED:
			dispositivo_tolto(in, dispositivo);
			break;

		case EI_EVENT_DEVICE_RESUMED:
			ei_device_start_emulating(dispositivo, ++in->sequenza);
			if (dispositivo == in->puntatore)
			{
				in->puntatore_attivo = TRUE;
				/* ⛔ E si rilegge ANCHE qui: fra `DEVICE_ADDED` e la ripresa il
				 *    compositore puo' aver rifatto i viewport. */
				leggi_regione(in, dispositivo);
			}
			if (dispositivo == in->tastiera_dev)
				in->tastiera_attiva = TRUE;
			registro_dettaglio(AREA, "dispositivo «%s» pronto (sequenza %u)",
			                   ei_device_get_name(dispositivo) ?: "?", in->sequenza);
			break;

		case EI_EVENT_DEVICE_PAUSED:
			if (dispositivo == in->puntatore)
				in->puntatore_attivo = FALSE;
			if (dispositivo == in->tastiera_dev)
				in->tastiera_attiva = FALSE;
			break;

		case EI_EVENT_DISCONNECT:
			registro_dice(AREA, "⛔ il compositore ha CHIUSO il canale di input");
			in->caduto = TRUE;
			break;

		default:
			break;
	}
}

/* ------------------------------------------------------------------ *
 *  Il contratto
 * ------------------------------------------------------------------ */
Input *input_apri(void *sessione_mutter, uint32_t tela_l, uint32_t tela_a, char **errore)
{
	MutterSessione *sessione = sessione_mutter;
	Input *in;
	int fd;

	if (errore)
		*errore = NULL;
	if (!sessione)
	{
		if (errore)
			*errore = g_strdup("nessuna sessione di Mutter: il canale di input non ha a chi parlare");
		return NULL;
	}
	if (tela_l == 0 || tela_a == 0)
	{
		if (errore)
			*errore = g_strdup_printf("tela degenere %ux%u: le coordinate assolute non avrebbero "
			                          "un intervallo",
			                          tela_l, tela_a);
		return NULL;
	}

	fd = mutter_eis_fd(sessione);
	if (fd < 0)
	{
		/* ⛔ E si dice PERCHE', non «non si apre»: la riga di `mutter.c` che
		 *    dichiara il rifiuto di `ConnectToEIS` e' gia' nel registro, e
		 *    questa la richiama invece di aggiungere un secondo mistero. */
		if (errore)
			*errore = g_strdup("ConnectToEIS non ha dato un descrittore (il registro dell'area "
			                   "«cattura» dice perche'): nessun input puo' arrivare al desktop");
		return NULL;
	}

	in = g_new0(Input, 1);
	in->sessione = sessione;
	in->tela_l = tela_l;
	in->tela_a = tela_a;

	in->ei = ei_new_sender(in);
	if (!in->ei)
	{
		if (errore)
			*errore = g_strdup("contesto libei non creato");
		g_free(in);
		return NULL;
	}
	/* Il nome si vede nei dispositivi che Mutter crea («remotix virtual
	 * keyboard», …) e nel suo registro: e' il modo di riconoscersi da fuori. */
	ei_configure_name(in->ei, "remotix");

	/*
	 * ⛔ Un `dup`, e non il descrittore di `mutter.c`: `ei_setup_backend_fd` se
	 *    ne APPROPRIA, e chiuderlo in due posti e' un difetto che si manifesta
	 *    a distanza — un descrittore riciclato da un'altra `open`.
	 */
	fd = dup(fd);
	if (fd < 0 || ei_setup_backend_fd(in->ei, fd) != 0)
	{
		if (errore)
			*errore = g_strdup("il descrittore di ConnectToEIS non e' stato accettato da libei");
		if (fd >= 0)
			close(fd);
		ei_unref(in->ei);
		g_free(in);
		return NULL;
	}

	/*
	 * ⛔ QUI NON SI APRE NESSUNA DISPOSIZIONE, ed e' voluto.
	 *
	 * La keymap non e' una cosa che sappiamo all'apertura: arriva da `libei`
	 * col dispositivo tastiera, e cambia sotto di noi.  ⇒ La apre
	 * `leggi_keymap`, al primo `DEVICE_ADDED` e a ogni ricambio.  Fino a
	 * quel momento `input_lettera` risponde -1, e lo dice.
	 */
	registro_dice(AREA, "canale di input aperto verso il compositore (libei), tela %ux%u", tela_l,
	              tela_a);
	return in;
}

/*
 * ⛔⭐ IL DESCRITTORE PER IL `poll()` DEL FIGLIO — vedi `input.h`.
 *
 * ⚠ E' un descrittore da SORVEGLIARE, non da leggere: chi lo mette nel `poll()`
 *   non ci fa `read()` sopra.  Quando diventa leggibile chiama `input_gira()`,
 *   che e' l'unico posto dove `ei_dispatch()` puo' stare — `libei` non e'
 *   rientrante, e il byte tolto a mano da sotto i piedi della libreria sarebbe
 *   un difetto che non da' errore.
 *
 * ⛔ -1 vuol dire «niente da mettere nel poll», non «errore».
 */
int input_descrittore(Input *in)
{
	if (!in || !in->ei)
		return -1;
	return ei_get_fd(in->ei);
}

int input_gira(Input *in)
{
	struct ei_event *evento;
	int quanti = 0;

	if (!in)
		return -1;
	if (in->caduto)
		return -1;

	ei_dispatch(in->ei);
	while ((evento = ei_get_event(in->ei)) != NULL)
	{
		tratta_evento(in, evento);
		ei_event_unref(evento);
		quanti++;
	}
	return in->caduto ? -1 : quanti;
}

int input_puntatore(Input *in, uint32_t x, uint32_t y)
{
	double fx, fy;

	if (!in || !in->puntatore || !in->puntatore_attivo)
		return -1;
	if (!in->regione_nota)
		return -1;

	/*
	 * ⛔ NESSUNA TRASFORMAZIONE quando la regione e' grande come la tela — che
	 *    e' il caso normale, e allora questa e' una SOMMA e non una scala:
	 *    l'origine della regione e' dove sta il nostro schermo nello spazio
	 *    globale del compositore, e senza di lei il puntatore finirebbe
	 *    sull'altro monitor.  `RCP.md` §7.3 vieta di **trasformare le
	 *    coordinate ricevute**, non di sapere dove sta lo schermo.
	 *
	 * ⚠ E se la regione NON e' grande come la tela, si scala **e lo si dice**:
	 *   e' la domanda aperta n.1 della fase 4 — chi decide la misura del
	 *   monitor ora che non la da' piu' la sessione (`RCP.md` §4.5).  Un
	 *   ridimensionamento silenzioso qui sarebbe la risposta sbagliata data da
	 *   chi non ha l'autorita' per darla.
	 */
	if (in->reg_l == (double) in->tela_l && in->reg_a == (double) in->tela_a)
	{
		fx = in->reg_x + (double) x;
		fy = in->reg_y + (double) y;
	}
	else
	{
		if (!in->regione_scalata_lamentata)
		{
			in->regione_scalata_lamentata = TRUE;
			registro_dice(AREA,
			              "⚠ la regione (%.0fx%.0f) NON e' grande come la tela (%ux%u): scalo le "
			              "coordinate, ed e' una decisione che questo modulo non dovrebbe "
			              "prendere — RCP.md §4.5, la tela concessa",
			              in->reg_l, in->reg_a, in->tela_l, in->tela_a);
		}
		fx = in->reg_x + (double) x * in->reg_l / (double) in->tela_l;
		fy = in->reg_y + (double) y * in->reg_a / (double) in->tela_a;
	}

	ei_device_pointer_motion_absolute(in->puntatore, fx, fy);
	batti_cornice(in, in->puntatore);
	return 0;
}

/*
 * ⛔ LA TELA CAMBIA IN CORSA — `TELA(ADATTATA)` di `RCP.md` §7.1.
 *
 * Il difetto che questa funzione esiste per non avere: `rcp.c` satura le
 * coordinate sulla tela NUOVA mentre `input.c` resta mappato sulla VECCHIA.
 * Due lati con due verita', e ⛔ **nessun errore da nessuna parte** — la stessa
 * forma che la fase 3 ha gia' pagato con la stringa del codec.
 *
 * ⛔ E si RILEGGE la regione subito, invece di aspettare il prossimo
 *    `DEVICE_ADDED`: il momento del `TELA` non e' il momento del `DEVICE_ADDED`,
 *    e fra i due ci sarebbe una finestra in cui il puntatore va altrove.
 *
 * ⚠ Chi cambia la tela, pero', **non e' chi cambia il monitor**: se la regione
 *   di `libei` resta grande com'era, questa funzione la trovera' diversa dalla
 *   tela e lo dira' (vedi `input_puntatore`).  E' la domanda aperta n.1 della
 *   fase 4 — chi decide la misura del monitor (`RCP.md` §4.5) — e questo
 *   modulo la DICHIARA invece di rispondervi da solo.
 */
int input_ritela(Input *in, uint32_t tela_l, uint32_t tela_a)
{
	if (!in)
		return -1;
	if (tela_l == 0 || tela_a == 0)
	{
		registro_dice(AREA, "⛔ tela degenere %ux%u rifiutata: tengo %ux%u", tela_l, tela_a,
		              in->tela_l, in->tela_a);
		return -1;
	}
	if (tela_l == in->tela_l && tela_a == in->tela_a)
		return 0;

	registro_dice(AREA, "la tela cambia: %ux%u → %ux%u", in->tela_l, in->tela_a, tela_l, tela_a);
	in->tela_l = tela_l;
	in->tela_a = tela_a;
	/* ⛔ E il lamento sulla scala si riarma: la regione di prima poteva essere
	 *    grande come la tela di prima, e non esserlo piu'. */
	in->regione_scalata_lamentata = FALSE;
	if (in->puntatore)
		leggi_regione(in, in->puntatore);
	return 0;
}

int input_pulsante(Input *in, uint16_t codice, int premuto)
{
	if (!in)
		return -1;
	return manda_bottone(in, codice, premuto);
}

int input_rotella(Input *in, int32_t asse_x, int32_t asse_y)
{
	if (!in || !in->puntatore || !in->puntatore_attivo)
		return -1;

	/*
	 * ⛔⛔ IL SEGNO DELL'ASSE VERTICALE SI INVERTE QUI, UNA VOLTA SOLA.
	 *
	 * `[M]` 10 agosto 2026 (`RCP.md` §7.3, riquadro «Il segno della rotella»):
	 * iniettando `+120` la pagina remota **scende** — `deltaY = +114`, cioe' il
	 * contenuto va verso la fine del documento.  E `RCP.md` §7.3 fissa l'altra
	 * meta': il client manda `+120` quando l'utente gira la rotella **in su**.
	 * ⇒ Le due convenzioni sono OPPOSTE.  Senza questo meno, lo schermo remoto
	 *   scorrerebbe al contrario per **ogni** utente.
	 *
	 * ⚠ E l'orizzontale NON si tocca: `+120` = «verso destra» da tutt'e due le
	 *   parti.  Non e' una simmetria dedotta — e' misurato dal banco
	 *   `04-b24-iniezione` nei due versi, come il verticale.
	 */
	ei_device_scroll_delta(in->puntatore, (double) asse_x / UNITA_PER_DELTA,
	                       (double) -asse_y / UNITA_PER_DELTA);
	batti_cornice(in, in->puntatore);
	return 0;
}

int input_lettera(Input *in, uint32_t carattere)
{
	uint16_t codici[TASTIERA_MAX_POSIZIONI];
	size_t quante = 0;
	int esito;

	if (!in)
		return -1;
	if (!in->disposizione)
	{
		/* ⛔ E NON e' il caso «non producibile»: quello e' 1, e vuol dire che la
		 *    disposizione c'e' e non fa quella lettera.  Qui la disposizione
		 *    non c'e' affatto, ed e' un guasto — confonderli toglierebbe a chi
		 *    legge il registro l'unica differenza che conta. */
		registro_dice(AREA, "⚠ LETTERA U+%04X non mandata: nessuna disposizione (libei non ha "
		                    "ancora consegnato una keymap)",
		              carattere);
		return -1;
	}
	if (!in->tastiera_dev || !in->tastiera_attiva)
		return -1;

	esito = tastiera_posizioni_per(in->disposizione, carattere, codici, &quante);
	if (esito < 0)
		return -1;
	if (esito == 0 || quante == 0)
	{
		/*
		 * ⛔ NON producibile: NON si manda una lettera diversa e NON si tace
		 *    (`RCP.md` §7.3).  Il ritorno e' 1 — ne' 0 ne' -1 — perche' chi
		 *    chiama deve poterlo distinguere da un guasto.
		 *
		 * ⚠ E LA RIGA NON SI SCRIVE QUI: la scrive gia' `tastiera.c`, e ci
		 *   mette dentro QUALE disposizione — l'unica cosa utile a chi legge il
		 *   registro sei ore dopo.  Scriverla anche qui vorrebbe dire contare
		 *   due volte gli stessi caratteri (`input.h`, 14 agosto 2026).
		 */
		return 1;
	}

	/* I modificatori prima, il tasto per ultimo; si rilascia all'incontrario. */
	for (size_t i = 0; i < quante; i++)
		if (manda_tasto(in, codici[i], 1) < 0)
		{
			/* ⛔ A meta' strada si rilascia quel che si e' premuto: un Maiusc
			 *    rimasto giu' per un errore di invio e' lo stesso danno del
			 *    Ctrl rimasto giu' al distacco. */
			for (size_t j = i; j > 0; j--)
				manda_tasto(in, codici[j - 1], 0);
			return -1;
		}
	for (size_t i = quante; i > 0; i--)
		manda_tasto(in, codici[i - 1], 0);
	return 0;
}

int input_posizione(Input *in, uint16_t codice, int premuto)
{
	if (!in)
		return -1;
	return manda_tasto(in, codice, premuto);
}

int input_rilascia_tutto(Input *in)
{
	int quanti = 0;

	if (!in)
		return -1;

	for (uint32_t c = 0; c < MAX_TASTO; c++)
		if (bit_leggi(in->tasti, c))
		{
			/* ⛔ Il bit si spegne ANCHE se l'invio fallisce: se il dispositivo
			 *    non c'e' piu', quel tasto non e' piu' nostro da rilasciare, e
			 *    tenerlo segnato farebbe contare al banco un rilascio che non
			 *    puo' avvenire.  ⚠ E si conta solo quel che e' PARTITO. */
			if (manda_tasto(in, (uint16_t) c, 0) == 0)
				quanti++;
			else
			{
				bit_scrivi(in->tasti, c, FALSE);
				in->quanti_tasti--;
			}
		}
	for (uint32_t c = 0; c < MAX_BOTTONE; c++)
		if (bit_leggi(in->bottoni, c))
		{
			if (manda_bottone(in, (uint16_t) c, 0) == 0)
				quanti++;
			else
			{
				bit_scrivi(in->bottoni, c, FALSE);
				in->quanti_bottoni--;
			}
		}

	/* ⛔ Si scrive SEMPRE, anche quando sono zero: «non c'era niente premuto» e
	 *    «non ho guardato» hanno lo stesso aspetto nel registro, e questa e' la
	 *    regola con il rapporto danno/costo piu' alto di `RCP.md`. */
	registro_dice(AREA, "rilascio al distacco: %d fra tasti e pulsanti (restano segnati %u tasti e "
	                    "%u pulsanti)",
	              quanti, in->quanti_tasti, in->quanti_bottoni);
	return quanti;
}

void input_chiudi(Input *in)
{
	if (!in)
		return;

	/* ⚠ Una rete, non la regola: chi cuce chiama `input_rilascia_tutto()` al
	 *   distacco (e' nel contratto).  Se non l'ha fatto, qui il conto e' ancora
	 *   pieno e la riga del registro lo dice — cioe' il difetto si VEDE. */
	if (in->quanti_tasti || in->quanti_bottoni)
	{
		registro_dice(AREA, "⛔ chiusura con %u tasti e %u pulsanti ANCORA PREMUTI: chi cuce non ha "
		                    "chiamato input_rilascia_tutto()",
		              in->quanti_tasti, in->quanti_bottoni);
		input_rilascia_tutto(in);
	}

	if (in->puntatore)
		ei_device_unref(in->puntatore);
	if (in->tastiera_dev)
		ei_device_unref(in->tastiera_dev);
	if (in->ei)
	{
		ei_disconnect(in->ei);
		ei_unref(in->ei);
	}
	g_clear_pointer(&in->disposizione, tastiera_chiudi);
	g_free(in->keymap_nome);
	g_free(in->reg_per);
	g_free(in);
}

/* ------------------------------------------------------------------ *
 *  ⭐ La finestra del banco — NON e' del contratto, ed e' voluto
 *
 *  `CODER.md` §6: «rendere il codice verificabile: ogni invariante deve avere
 *  un punto in cui il revisore puo' leggere se e' rispettato o violato».  Il
 *  banco `04-b24` legge di qui il conto di quel che e' premuto e il numero dei
 *  ricambi, invece di dedurli dal registro.
 *
 *  ⛔ NON sta in `input.h` di proposito: `input.h` e' del coordinatore ed e' il
 *     contratto del PRODOTTO.  Il banco la dichiara `extern` da se'.
 * ------------------------------------------------------------------ */
void input_conto(const Input *in, unsigned *tasti, unsigned *pulsanti, unsigned *ricambi_puntatore,
                 unsigned *ricambi_tastiera, int *pronto);

void input_conto(const Input *in, unsigned *tasti, unsigned *pulsanti, unsigned *ricambi_puntatore,
                 unsigned *ricambi_tastiera, int *pronto)
{
	if (tasti)
		*tasti = in ? in->quanti_tasti : 0;
	if (pulsanti)
		*pulsanti = in ? in->quanti_bottoni : 0;
	if (ricambi_puntatore)
		*ricambi_puntatore = in ? in->ricambi_puntatore : 0;
	if (ricambi_tastiera)
		*ricambi_tastiera = in ? in->ricambi_tastiera : 0;
	if (pronto)
		*pronto = in && in->puntatore_attivo && in->regione_nota;
}
