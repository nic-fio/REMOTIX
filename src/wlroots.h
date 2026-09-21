/*
 * wlroots — il palco della terza famiglia: labwc, e quindi XFCE e LXQt.
 *
 * ⛔⛔ E NON È «kwin.h con un altro protocollo»: è l'altro VERSO.
 *
 *    `mutter.h` e `kwin.h` fanno la stessa cosa — chiedono al compositore un
 *    flusso e ne ricevono **il numero di un nodo PipeWire**. Da lì in poi i
 *    fotogrammi **arrivano da soli**, spinti, e `cattura.c` li raccoglie.
 *
 *    Su wlroots un nodo PipeWire non esiste. C'è un protocollo Wayland,
 *    `zwlr_screencopy_manager_v1`, e per ogni fotogramma si fa il giro intero:
 *
 *        capture_output → buffer → copy → ready
 *
 *    ⇒ Un fotogramma **si chiede**. Il ritmo non è una proprietà del
 *      compositore: è il nostro ciclo. ⭐ Ed è precisamente quel che la
 *      decisione dell'utente del 20 settembre 2026 ha comprato — «li chiediamo
 *      noi» — insieme al governo del cursore e della misura.
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL CANCELLO NON C'È, e va detto perché è una notizia.
 *
 * Su GNOME la cattura passa da un portale; su KDE serve un `.desktop` che
 * dichiari `X-KDE-Wayland-Interfaces`, e senza quello il global non compare.
 * `[M]` 20 settembre 2026, dentro `rete11-xfce`: un client nudo vede **47
 * global** e fra questi `zwlr_screencopy_manager_v1` **v3**. Nessun file,
 * nessun dialogo, nessun portale. L'unico cancello è l'uid: `/run/user/<uid>`
 * è `drwx------`.
 *
 * ---------------------------------------------------------------------------
 * ⚠ IL PROTOCOLLO È DEPRECATO A MONTE, e lo si sa dal primo giorno.
 *
 * L'XML porta in testa *«This protocol is deprecated … the
 * ext-image-copy-capture-v1 protocol should be used instead»*. ⛔ Ma `[M]` 20
 * settembre 2026 labwc su Debian Trixie **non espone**
 * `ext_image_copy_capture_manager_v1`: non c'è niente da usare al suo posto.
 * ⇒ Si scrive contro screencopy, e si scrive in modo che il successore possa
 *   entrare **accanto** — non al suo posto: la porta di questo file nomina
 *   fotogrammi e misure, non messaggi del protocollo.
 *
 * ---------------------------------------------------------------------------
 * ⭐ PERCHÉ QUESTO FILE ESISTE, invece di un ramo dentro `cattura.c`
 *
 * `cattura.c` sono 2 348 righe costruite sul verso della spinta, e `figlio.c`
 * la usa in **35 punti**. ⛔ Rifarle a due vie vorrebbe dire toccare in
 * trentacinque posti il codice da cui GNOME e KDE dipendono — cioè mettere a
 * rischio il baseline protetto per servire il desktop nuovo, che è proprio quel
 * che la regola della fase 13 vieta.
 *
 * ⇒ La forma scelta ha un precedente in casa, e si copia da lì: gli **appunti**
 *   (`src/appunti.c:594-603`) hanno **due costruttori** — `appunti_apri()` e
 *   `appunti_apri_kde()` — e le funzioni pubbliche passano la mano in cima.
 *   Qui uguale: `cattura_avvia()` resta intatta per GNOME e KDE, e questo file
 *   dà la sorgente dell'altro verso.
 *
 * ⚠ E le due funzioni che NON mappano sull'altro verso sono due, contate:
 *   · **il cursore**: screencopy non ha un canale per la forma del puntatore —
 *     c'è solo `overlay_cursor`, un sì/no che lo disegna DENTRO l'immagine.
 *     ⇒ Chi si registra viene accettato e non richiamato mai, e la riga lo
 *       dice: «su questo desktop il puntatore è nei pixel».
 *   · **il ridimensionamento**: qui non si rinegozia un flusso, si cambia la
 *     misura dell'**uscita** (`zwlr_output_manager_v1`, `[M]` v4 su labwc).
 *     ⇒ Non sta in questo file: è l'incremento che porta la misura.
 */
#pragma once

#include <glib.h>
#include <stdbool.h>
#include <stdint.h>

typedef struct WlrPalco WlrPalco;

/*
 * Si collega al compositore dell'utente e prepara la cattura dell'uscita.
 *
 * ⚠ `WAYLAND_DISPLAY` se c'è; altrimenti si prova `wayland-0`…`wayland-9` in
 *   `XDG_RUNTIME_DIR` — la stessa ricerca che `kwin_display_apri()` fa già, e
 *   per la stessa ragione: il figlio non eredita la variabile dal compositore
 *   che ha appena avviato.
 *
 * ⛔ NON cattura ancora niente: qui si stabilisce solo che il compositore c'è,
 *    che annuncia il manager, e QUALE uscita si guarderà. Un `apri` che
 *    catturasse renderebbe indistinguibili «il compositore non c'è» e «il primo
 *    fotogramma non arriva», che sono due diagnosi diverse.
 *
 * NULL con `sbaglio` scritto.
 */
WlrPalco *wlr_apri(GError **sbaglio);

/* La misura che l'uscita ha ADESSO — ⛔ non quella che si vorrebbe.
 *
 * `[M]` 20 settembre 2026: un'uscita headless di labwc nasce **1280×720**
 * cablata, e nessun protocollo ne crea una della misura voluta. ⇒ Chi chiede
 * 1920×1080 deve saperlo, e questa funzione è il posto in cui lo scopre. */
void wlr_misura(const WlrPalco *palco, uint32_t *larghezza, uint32_t *altezza);

/* Il nome dell'uscita, per le righe di registro (`HEADLESS-1` e simili). */
const char *wlr_uscita_nome(const WlrPalco *palco);

/*
 * ⭐ UN FOTOGRAMMA, CHIESTO E ASPETTATO — il giro intero del verso a tiro.
 *
 * ⛔ E le tre uscite sono TRE, non due, per la stessa ragione di tutto il
 *    progetto: «il compositore ha detto di no» e «non ho potuto chiedere» non
 *    sono la stessa cosa, e metterle insieme fa accusare il compositore per un
 *    guasto nostro.
 */
typedef enum {
	WLR_FOTOGRAMMA_PRESO = 0,  /* i pixel ci sono                              */
	WLR_FOTOGRAMMA_FALLITO,    /* il compositore ha mandato `failed`           */
	WLR_FOTOGRAMMA_SCADUTO,    /* l'attesa è finita: non ho potuto guardare    */
	WLR_FOTOGRAMMA_ROTTO       /* il filo con il compositore è caduto          */
} WlrEsito;

typedef struct {
	uint32_t larghezza, altezza, stride;
	uint32_t formato;   /* il fourcc di `wl_shm` tradotto in DRM */
	const uint8_t *pixel; /* ⛔ vivi finché non si chiede il fotogramma dopo */
	gsize byte;
	/* ⭐ I due che il verso a tiro regala, e che sulla spinta si stimano:
	 *    l'istante in cui il compositore dice che la presentazione è avvenuta. */
	uint64_t secondi;
	uint32_t nanosecondi;
	/* ⚠ `y_invertita`: l'evento `flags` può dire che le righe vanno lette dal
	 *   basso. ⛔ Ignorarlo dà un'immagine capovolta, che è un guasto che
	 *   somiglia a un guasto del codificatore. */
	bool y_invertita;
} WlrFotogramma;

/*
 * Chiede un fotogramma e aspetta al massimo `attesa_s`.
 *
 * ⚠ I pixel consegnati vivono fino alla chiamata successiva: chi li vuole
 *   tenere se li copia. ⛔ È la stessa regola di `cattura.h`, e sta qui perché
 *   è la regola che viene dimenticata per prima.
 */
WlrEsito wlr_fotogramma(WlrPalco *palco, double attesa_s, WlrFotogramma *fuori,
                        GError **sbaglio);

/*
 * ⭐⭐ LA MISURA DELL'USCITA — e su questa famiglia si può, a differenza di KDE.
 *
 * ⛔⛔ E «LA VERITÀ LA DICE IL FOTOGRAMMA, NON L'ESITO DELLA RICHIESTA»
 *     (`DECISIONI.md` §5.0-sexies, la regola rubata a neatvnc).
 *
 *     `[M]` 14 agosto 2026: chiedere a labwc la misura che l'uscita **ha già**
 *     risponde «riuscito» e non manda nessun evento; un serial vecchio
 *     risponde «annullato» e non fa niente. ⛔ `wayvnc` tratta *riuscito*,
 *     *fallito* e *annullato* nello stesso ramo — da non copiare.
 *
 * ⇒ Questa funzione dice soltanto **se la richiesta è stata accettata**. Che
 *   l'uscita sia cambiata lo dirà `wlr_misura()` dopo il fotogramma seguente,
 *   ed è l'unico testimone che conta.
 */
typedef enum {
	WLR_MISURA_CHIESTA = 0, /* la richiesta è partita e il compositore ha detto sì */
	WLR_MISURA_GIA_COSI,    /* l'uscita è già di quella misura: niente da chiedere */
	WLR_MISURA_RIFIUTATA,   /* `failed`: il compositore ha detto no                */
	WLR_MISURA_ANNULLATA,   /* `cancelled`: il serial era vecchio — si può riprovare */
	WLR_MISURA_IMPOSSIBILE  /* il compositore non annuncia il gestore delle uscite */
} WlrMisuraEsito;

WlrMisuraEsito wlr_misura_chiedi(WlrPalco *palco, uint32_t larghezza, uint32_t altezza,
                                 double attesa_s, GError **sbaglio);

/* Quanti fotogrammi sono stati chiesti, presi, falliti. Per le righe di
 * registro e per il manifesto: ⛔ un conteggio non è una dichiarazione. */
typedef struct {
	guint64 chiesti, presi, falliti, scaduti;
} WlrConteggi;

void wlr_conteggi(const WlrPalco *palco, WlrConteggi *fuori);

void wlr_chiudi(WlrPalco *palco);
