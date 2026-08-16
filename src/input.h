/*
 * input.h — LA CUCITURA del canale di input: dal filo al desktop.
 *
 * ⛔ QUESTO FILE E' DEL COORDINATORE, non dell'anello che lo attua.  La ragione
 *    e' scritta in `fasi/rapporti/F5-desktop-vero.md`: il difetto della fase 3
 *    non era DENTRO un pezzo, era FRA due pezzi «ciascuno corretto per conto
 *    suo» — e le cuciture, non avendo un proprietario, non le guardava nessun
 *    banco.  Qui il proprietario ce l'hanno.
 *
 * Chi legge questo file:
 *   · `input.c` — attua queste funzioni su `libei`, sulla sessione di
 *                 `mutter.c`.  ⛔ NON conosce ne' QUIC ne' il formato dei
 *                 messaggi;
 *   · `figlio.c`— ⭐ **cuce i due**: e' lui che include questo file, scrive i
 *                 sei adattatori e li appende ai ganci di `rcp_ganci`.
 *
 * ⛔⛔ E QUI C'ERA UNA RIGA SBAGLIATA, corretta il 14 agosto 2026 su rilievo
 *      dell'anello che attuava il filo — che l'ha provata invece di crederla.
 *
 * Diceva: *«`rcp.c` decodifica i messaggi di §7.3 e **chiama queste
 * funzioni**»*.  ⛔ **Il costruttore lo rende impossibile**, e non e' una
 * preferenza di stile: `rcp.c` vive in DUE cartelle che il `Makefile`
 * (`GEMELLATI`) pretende identiche byte per byte, e la seconda copia
 * `banchi/01-b3-rcp-innesta.py` la infila dentro `examples/` di ngtcp2, dove
 * `input.h` **non c'e'**.  Un `#include "input.h"` in `rcp.c` non compila
 * l'innesto ⇒ **spegne B3, B5, B6, B8 e B11 in un colpo solo**.
 *
 * ⇒ La forma giusta e' quella che `rcp.h` usa gia' per PAM e per gli stream:
 *   **sei ganci in `rcp_ganci`**, con le firme di questo file campo per campo.
 *   ⛔ Si collegano **tutti e sei o nessuno**: un canale che sapesse muovere il
 *   puntatore e non sapesse rilasciare un pulsante lascerebbe il desktop
 *   **peggio di come l'ha trovato**.
 *
 * ⛔⛔ IL CONTRATTO DEL THREAD, e sta scritto perche' e' un difetto che NON DA'
 *      ERRORE — chiesto dall'anello che ha attuato questo file, 14 ago 2026.
 *
 *      **`libei` non e' rientrante.**  TUTTE le funzioni di questo file vanno
 *      chiamate dallo **stesso thread** che chiama `input_gira()`.  Due thread
 *      su uno `struct ei` non danno un errore: danno un programma che a un
 *      certo punto si comporta male, e nessuno collega le due cose.
 * ⚠ Nel prodotto e' il ciclo del figlio (`figlio.c`), che e' a un filo solo.
 *
 * ⛔ La regola che governa i tipi qui sotto: i codici sono quelli di **evdev**
 *    (`linux/input-event-codes.h`), perche' `libei` lavora in evdev e ogni
 *    altra convenzione aggiungerebbe una tabella che sbaglia in silenzio
 *    (`RCP.md` §7.3).
 */
#ifndef REMOTIX_INPUT_H
#define REMOTIX_INPUT_H

#include <stdint.h>
#include <stddef.h>

typedef struct input Input;

/*
 * Apre il canale verso il compositore.  `sessione_controllo` e' il percorso
 * D-Bus della sessione `RemoteDesktop` gia' avviata da `mutter.c`, da cui si
 * chiede `ConnectToEIS` (vedi il commento di `src/mutter.c:402`).
 *
 * `tela_l`/`tela_a` sono la TELA di `RCP.md` §4.5 — non la vista.  Servono a
 * mappare la regione del puntatore assoluto.
 *
 * ⛔ Ritorna NULL e riempie `*errore` (da liberare con free) se non si apre.
 *    Non si ripiega in silenzio: `CODER.md` §4.2.
 */
Input *input_apri(void *sessione_mutter, uint32_t tela_l, uint32_t tela_a,
                  char **errore);

/*
 * ⛔ I ricambi silenziosi di `libei`, che `STUDI.md` §gnome §9 misura: un cambio di
 *    keymap distrugge e ricrea il dispositivo tastiera, un cambio di geometria
 *    tutti i dispositivi assoluti — e il puntatore al dispositivo vecchio
 *    smette di funzionare SENZA ERRORE.  ⇒ Questa va chiamata dal ciclo del
 *    figlio a ogni giro: dentro rilegge keymap e regioni a ogni `DEVICE_ADDED`.
 *    Ritorna il numero di eventi serviti, o -1.
 */
int input_gira(Input *);

/*
 * ⛔⭐ IL DESCRITTORE DA METTERE NEL `poll()`, e non e' una comodita': e'
 *     millisecondi sul percorso dell'input.
 *
 *     Senza, l'unica strada e' chiamare `input_gira()` a intervalli — cioe'
 *     **latenza aggiunta proprio dove il terzo numero di `CODER.md` §1-bis la
 *     conta** (tetto 50 ms).  ⚠ Un banco che sonda ogni 50 ms misura benissimo;
 *     un prodotto che lo fa regala fino a 50 ms all'utente su ogni gesto.
 *
 * Ritorna -1 se il canale non e' aperto: ⛔ e -1 vuol dire «niente da mettere
 * nel poll», non «errore» — chi chiama lo distingue guardando se `Input` c'e'.
 */
int input_descrittore(Input *);

/*
 * Le cinque azioni di `RCP.md` §7.3.  Tutte ritornano 0 se l'azione e' stata
 * consegnata al compositore, -1 se no.
 *
 * ⛔ `x`/`y` sono INDICI DI PIXEL SULLA TELA: `0 <= x < tela_l`.  Chi chiama ha
 *    gia' rifiutato le coordinate fuori intervallo (e' `rcp.c`): qui non si
 *    applica NESSUNA trasformazione.
 */
int input_puntatore(Input *, uint32_t x, uint32_t y);

/*
 * ⛔ LA TELA IN VIGORE E' CAMBIATA (`RCP.md` §7.1, `TELA(ADATTATA)`).  Rimappa
 *    la regione del puntatore assoluto.  0 se fatto, -1 se no.
 *
 * ⚠ Aggiunta il 14 agosto 2026, e la ragione e' un difetto *fra* due pezzi —
 *   la stessa forma che la fase 3 ha gia' pagato.  `input_apri()` prende la
 *   tela **una volta sola**; dopo un `TELA(ADATTATA)` `rcp.c` satura le
 *   coordinate alla tela NUOVA mentre `input.c` resta mappato sulla VECCHIA:
 *   ⛔ due lati con due verita', e nessun errore da nessuna parte.
 *
 * ⚠ `[?]` Forse `input_gira()` basterebbe gia', perche' rilegge le regioni a
 *   ogni `DEVICE_ADDED` — ⛔ ma **non e' misurato**, e il momento del
 *   `DEVICE_ADDED` non e' il momento del `TELA`.  Finche' resta `[?]`, la
 *   chiamata esplicita e' la strada.
 */
int input_ritela(Input *, uint32_t tela_l, uint32_t tela_a);

/*
 * ⛔⭐⭐ LA DISPOSIZIONE NEGOZIATA ENTRA NELLA SESSIONE — `DECISIONI.md`
 *      §5-bis.7, decisa dall'utente l'8 agosto 2026 e CONFERMATA il 16.
 *
 * ⛔ E il verso e' QUESTO, non l'altro.  La strada corta sarebbe stata: tenere
 *    la sessione com'e' e tradurre la lettera con una keymap NOSTRA, quella che
 *    il client ha chiesto.  ⛔ `tastiera.h` spiega perche' e' sbagliata e
 *    `tastiera.c` la misura: con la nostra keymap e la loro sessione escono
 *    **caratteri diversi** — mandiamo il tasto 26 per la `[` di `us` e sullo
 *    schermo, su una sessione `it`, compare una `è`.  Cioe' esattamente cio'
 *    che `RCP.md` §7.3 vieta.
 *
 * ⇒ Si cambia la disposizione **della sessione**, e poi la si RILEGGE da
 *   `libei` come si e' sempre fatto.  ⭐ Che quel giro regga non e' una
 *   speranza: `[M]` 16 agosto 2026, banco `06-b34` caso 2s — cambiata la
 *   disposizione della sessione, Mutter distrugge e ricrea il dispositivo
 *   tastiera, `leggi_keymap()` rilegge, e al testimone dentro la sessione
 *   arriva il carattere GIUSTO.
 *
 * ⛔⛔ E IL DANNO CHE QUESTA FUNZIONE CURA NON E' LA COMODITA' DI DUE ACCENTI.
 *     `SPECIFICHE.md` §7.3: le lettere viaggiano come **lettere**, ma le
 *     scorciatoie viaggiano come **posizioni** — e le posizioni combaciano solo
 *     se le due disposizioni sono la stessa.  Su una tastiera tedesca la `Z`
 *     sta dove sulla nostra sta la `Y` (evdev 21 contro 44): senza rinegoziare,
 *     **`Ctrl+Z` arriva come `Ctrl+Y`**, cioe' «rifai» invece di «annulla».
 *     ⚠ Il sintomo che l'utente descrive e' «l'annulla non funziona», e nessuno
 *       lo collega alla disposizione.
 *
 * `nome` e' la stringa di `RCP.md` §4.5: `it`, `us`, `de(neo)`.
 *
 *   ritorna  0  la richiesta e' PARTITA.  ⚠ NON «e' in vigore»: il compositore
 *               ci mette il suo tempo, e chi lo constata e' la riga di
 *               `leggi_keymap()` al `DEVICE_ADDED` che segue;
 *   ritorna -1  non e' partita, ed e' gia' dichiarato nel registro.
 */
int input_disposizione(Input *, const char *nome);

/* `codice` e' evdev: `BTN_LEFT` = 0x110.  `premuto` 1 o 0. */
int input_pulsante(Input *, uint16_t codice, int premuto);

/*
 * ⛔ Unita' da 120 per scatto, e IL SEGNO DELL'ASSE VERTICALE SI INVERTE QUI
 *    DENTRO — una volta sola, in un posto solo.  E' `[M]` 10 agosto 2026
 *    (`RCP.md` §7.3, riquadro «Il segno della rotella»): il client manda +120
 *    quando l'utente gira in su, e le due convenzioni sono opposte.
 * ⚠ E i mezzi scatti esistono: 60 NON si arrotonda a zero.  `STUDI.md` §gnome §9 dice
 *   che `ei_device_scroll_discrete` fa una divisione intera per 120 e se li
 *   mangia: la strada e' `scroll_delta`, dove la soglia vera e' 60.
 */
int input_rotella(Input *, int32_t asse_x, int32_t asse_y);

/*
 * Una lettera, come valore scalare Unicode.  Passa da `tastiera.h`.
 * ⛔ Se il carattere NON e' producibile nella disposizione della sessione:
 *    ritorna 1 (non 0 e non -1).  ⛔ MAI una lettera diversa, MAI il silenzio
 *    (`RCP.md` §7.3, `SPECIFICHE.md` §7.3).
 *
 * ⚠ CORRETTO IL 14 AGOSTO 2026 — qui c'era scritto «e chi chiama lo scrive nel
 *   registro», ed era la meta' sbagliata della cucitura: **la riga la scrive
 *   gia' `tastiera.c`**, e ci mette dentro **quale disposizione** — che e'
 *   l'unica cosa utile a chi legge il registro sei ore dopo, e che `rcp.c` non
 *   sa.  ⛔ Da cui: **`rcp.c` NON DEVE duplicarla**, o si contano due volte gli
 *   stessi caratteri.
 *
 * ⚠ E per la stessa ragione `input_apri()` NON prende la disposizione: la
 *   keymap arriva da `libei` dentro `input.c`, a ogni `DEVICE_ADDED`
 *   (`tastiera_apri_da_keymap()`).  Non e' una dimenticanza: e' il verso
 *   giusto.
 */
int input_lettera(Input *, uint32_t carattere);

/* Una posizione di tasto, in evdev: `KEY_A` = 30.  `premuto` 1 o 0. */
int input_posizione(Input *, uint16_t codice, int premuto);

/*
 * ⛔⛔ IL RILASCIO AL DISTACCO — `RCP.md` §11 la chiama «la regola col rapporto
 *      danno/costo piu' alto del documento».  Rilascia OGNI tasto e OGNI
 *      pulsante che risultano premuti.  Un Ctrl rimasto giu' in una sessione
 *      che sopravvive al client rende il desktop inservibile al riattacco, e
 *      nessuno collega le due cose.
 * ⇒ Da cui l'obbligo, per chi attua: si TIENE il conto di cosa e' premuto.
 *   Ritorna quanti ne ha rilasciati, perche' il banco possa contarli.
 */
int input_rilascia_tutto(Input *);

void input_chiudi(Input *);

#endif /* REMOTIX_INPUT_H */
