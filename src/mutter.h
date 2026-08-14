/*
 * mutter — la sequenza obbligata che apre un monitor virtuale e il suo flusso.
 *
 * ⛔ RIPORTATO DA `v1/remotix-c/src/mutter.c` (353 righe), e non ricopiato:
 *    quel file portava dentro `sessione.h` e il registro di v1, e chiamava
 *    `ConnectToEIS` per l'input — che in fase 2 non esiste ancora.  Qui resta
 *    ⭐ **la sequenza D-Bus**, che e' il pezzo prezioso, e le due punizioni
 *    scritte accanto a ogni passo.
 *
 * Si parla alle interfacce DIRETTE del compositore, non a `xdg-desktop-portal`:
 * il portale chiede il permesso a un utente seduto davanti allo schermo, e in
 * una sessione senza monitor quell'interazione non puo' avvenire (`CODER.md`
 * §4.3).  E' anche la via del riferimento (`gnome-remote-desktop.md` §5).
 *
 * ---------------------------------------------------------------------------
 * ⛔ L'ORDINE NON AMMETTE PERMUTE, e ogni permuta la punisce con un errore
 *    DIVERSO che non dice «hai sbagliato l'ordine» (`LEZIONI.md` §4 trappola 1;
 *    la sequenza e' stata ricopiata e riprovata sul ferro dal banco di F2.2):
 *
 *      1. RemoteDesktop.CreateSession      → percorso, e se ne legge SessionId
 *                                            SENZA avviarla
 *      2. ScreenCast.CreateSession         dichiarando `remote-desktop-session-id`
 *      3. RemoteDesktop.Session.Start      ← ADESSO, non prima
 *      4. ScreenCast.Session.RecordVirtual → percorso del flusso
 *      5. Stream.Start                     ← il FLUSSO, non la sessione
 *
 *    - avviare il controllo prima del punto 2 →
 *      «Remote desktop session already started»;
 *    - avviare la cattura con `Session.Start` →
 *      «Must be started from remote desktop session».
 *
 *    E in chiusura vale all'inverso: `ScreenCast.Session.Stop` su una cattura
 *    associata risponde «Must be stopped from remote desktop session».  ⇒ Si
 *    chiude fermando il CONTROLLO, e la cattura lo segue.
 *
 * ⛔ IL NODO PIPEWIRE ARRIVA CON UN SEGNALE EMESSO **DURANTE** `Stream.Start`:
 *    ci si iscrive PRIMA di chiamarlo, o si aspetta per sempre un annuncio gia'
 *    passato (`LEZIONI.md` §4 trappola 2).
 *
 * ---------------------------------------------------------------------------
 * ⛔ IL MONITOR VIRTUALE LO MONTA IL PROGRAMMA, ED E' L'INVARIANTE I7
 *
 * `v1/remotix-c/src/sessione.c:671` e' `if (tipo == COMPOSITORE_KWIN && …)`: sul
 * ramo GNOME larghezza e altezza **entravano nella funzione e si perdevano**, e
 * il monitor virtuale finiva in una riga di `provision-server.sh` — cioe' in una
 * configurazione che si puo' perdere.  ⛔ E si e' persa: `[M]` 12 agosto 2026,
 * la sessione di NIC-OS ha girato **due giorni viva, completa e NERA**.
 *
 * ⇒ Qui `RecordVirtual` monta il monitor **dentro il programma**, a ogni
 *   apertura.  Non e' una comodita': e' la protezione di un difetto noto messa
 *   dove per toglierla bisogna volerlo.
 *
 * ---------------------------------------------------------------------------
 * ⛔ E IL MONITOR SI SA PER NOME, MAI PER INDICE E MAI PER MISURA — forma E2
 *
 * `[M]` 12 agosto 2026: sul server ci sono DUE monitor virtuali — `Meta-0` /
 * «MetaVirtualMonitor» (quello della sessione) e `Meta-1` / «Virtual remote
 * monitor» (quello di `RecordVirtual`, cioe' il nostro) — ed ⛔ **entrambi sono
 * 1920×1080@60**.  A distinguerli c'e' solo il nome del prodotto.
 *
 * Il banco di F2.2 ha pagato questo difetto in faccia: `mpv --fs` andava a
 * schermo intero sul PRIMO monitor, la scena era viva, e la cattura riceveva
 * **zero fotogrammi** — con il banco VERDE.  ⇒ `mutter_monitor_nostro` esiste
 * perche' chi apre una finestra su questo schermo possa dichiararlo per nome
 * (`CODER.md` §3.9: digli cosa fare, e verifica che abbia obbedito).
 *
 * ⛔ E se dopo il montaggio non compare **esattamente un** monitor nuovo, non si
 *    tira a indovinare: si risponde NULL e chi ha chiamato lo dichiara.
 */
#ifndef REMOTIX_MUTTER_H
#define REMOTIX_MUTTER_H

#include <glib.h>
#include <stdint.h>

typedef struct MutterSessione MutterSessione;

/*
 * Esegue la sequenza per intero e restituisce la sessione pronta, con il nodo
 * PipeWire gia' annunciato.
 *
 * ⚠ LA MISURA NON SI DICHIARA QUI: `RecordVirtual` non la prende.  Il monitor si
 *   chiede, e la risoluzione si concorda nella negoziazione PipeWire — vedi
 *   `cattura.h`.  Chi cercasse qui una larghezza sta cercando nel posto
 *   sbagliato, ed e' il motivo per cui questa riga esiste.
 */
MutterSessione *mutter_apri(GError **sbaglio);

/* Il nodo PipeWire da cui leggere i fotogrammi. */
uint32_t mutter_nodo(const MutterSessione *sessione);

/* Il percorso D-Bus del flusso e quello del controllo: sono gli indirizzi a cui
 * la fase 4 parlera' per muovere il puntatore. */
const char *mutter_percorso_flusso(const MutterSessione *sessione);
const char *mutter_percorso_controllo(const MutterSessione *sessione);

/*
 * L'identificativo dichiarato a `RecordVirtual`.
 *
 * ⛔⛔ E NON SERVE A NIENTE — `[M]` 14 agosto 2026, e la riga qui sotto diceva
 *      il contrario: *«e' la chiave con cui si riconosce, fra le regioni che
 *      libei annuncia, quella del nostro monitor»*.
 *
 *      `handle_record_virtual` legge **`cursor-mode` e `is-platform` e basta**:
 *      la nostra proprieta' `mapping-id` e' ignorata **in silenzio**.  La
 *      chiave vera la genera Mutter (UUID) e la pubblica nei `Parameters` del
 *      flusso: si legge con `mutter_mapping_id_pubblicato`, e il verso e'
 *      **Mutter → noi**.  (`gnome.md` §9, `reference-gnome/rapporti/06-mutter-input.md`
 *      §7.2.)
 *
 * ⚠ Resta esposto perche' il banco confronta i due valori: e' il modo di
 *   MOSTRARE che sono diversi, invece di scriverlo soltanto.
 */
const char *mutter_mapping_id(const MutterSessione *sessione);

/*
 * ⭐ La chiave VERA della regione del puntatore: l'UUID che Mutter genera e
 *    pubblica nei `Parameters` del flusso.
 *
 * ⛔ NULL vuol dire «non lo so», e sono DUE casi che il registro separa: la
 *    lettura della proprieta' e' fallita, oppure i `Parameters` non portano la
 *    chiave.  Chi lo riceve riconosce la regione per geometria e lo DICHIARA.
 *
 * Si puo' chiamare solo dopo `mutter_apri` (serve il percorso del flusso).
 */
const char *mutter_mapping_id_pubblicato(MutterSessione *sessione);

/*
 * ⭐ Il descrittore del canale EIS, aperto da `ConnectToEIS` dentro
 *    `mutter_apri` — nel punto della sequenza che il riferimento impone.
 *
 * ⛔ -1 vuol dire che il canale NON si e' aperto, e il registro dice perche'.
 *    La sessione e' viva lo stesso (si guarda, non si comanda): e' la
 *    degradazione dichiarata di `CODER.md` §4.2, non un guasto.
 *
 * ⚠ Il descrittore resta di questa sessione, che lo chiude in `mutter_chiudi`.
 *   Chi lo da' a `libei` — che se ne appropria — ne passa un `dup`.
 */
int mutter_eis_fd(const MutterSessione *sessione);

/*
 * ⭐ Cerca il monitor che abbiamo montato noi, e dice se l'ha trovato.
 *
 * ⛔ VA CHIAMATA QUANDO LA CATTURA E' GIA' ATTIVA, e la ragione e' misurata —
 *    `[M]` 12 agosto 2026, e me l'ha trovata il banco al primo giro contro
 *    questo codice, non una rilettura:
 *
 *      dopo `RecordVirtual`     ⛔ il monitor NON c'e' ancora
 *      dopo `Stream.Start`      ⛔ non c'e' NEMMENO ADESSO, nemmeno aspettando
 *                                  tre secondi
 *      quando il CONSUMATORE si e' agganciato e il flusso e' attivo  ⭐ c'e'
 *
 *    ⇒ Mutter crea il monitor virtuale quando qualcuno comincia davvero a
 *      leggere, non quando glielo si chiede.  Chi cercasse il nome subito dopo
 *      la sequenza D-Bus leggerebbe «non e' comparso nessun monitor» su una
 *      sessione perfettamente sana — che e' un rosso su un banco sano.
 *
 * ⚠ E il momento in cui il nome SERVE e' esattamente questo: la scena (o
 *   l'applicazione dell'utente) si apre dopo che la cattura e' viva, e va
 *   mandata su QUESTO schermo per nome.
 *
 * Ritorna TRUE se il nome e' noto (anche se lo era gia'), FALSE se non lo sa.
 */
gboolean mutter_monitor_cerca(MutterSessione *sessione);

/*
 * Il connettore del monitor che ABBIAMO montato noi (`Meta-1`, …) e il nome del
 * prodotto che Mutter gli da' («Virtual remote monitor»).
 *
 * Vale NULL se le due strade non concordano — il diff prima/dopo e il nome del
 * prodotto — o se i monitor nuovi non sono esattamente uno.  ⛔ NULL vuol dire
 * «non lo so», e non «non c'e'»: chi lo riceve lo dichiara invece di scegliere
 * il piu' comodo.
 */
const char *mutter_monitor_nostro(const MutterSessione *sessione);
const char *mutter_monitor_prodotto(const MutterSessione *sessione);

/*
 * Quanti monitor c'erano PRIMA del montaggio e quanti DOPO.  Sono due numeri e
 * non uno: `dopo - prima != 1` e' precisamente il caso in cui il nome del nostro
 * schermo non si puo' sapere, e va scritto invece che dedotto.
 */
void mutter_monitor_conteggi(const MutterSessione *sessione, guint *prima, guint *dopo);

/* Ferma il CONTROLLO — e con lui la cattura — e libera tutto.  ⛔ Ogni monitor
 * virtuale non smontato resta attaccato a Mutter. */
void mutter_chiudi(MutterSessione *sessione);

#endif
