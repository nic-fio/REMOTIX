/*
 * wlr_input — il TRASPORTO dell'input sulla terza famiglia: labwc, e quindi XFCE.
 *
 * ⛔⛔ E NON È UN SECONDO `input.c`: è il pezzo che su GNOME e KDE fa `libei`,
 *     e basta quello.
 *
 *     `[✗]` libei su wlroots **non esiste** (`STUDI.md` §xfce §7, cercato in
 *     wlroots, labwc, sway, wayfire, weston, xdpw e wayvnc: zero).  ⇒ La strada
 *     sono due protocolli Wayland, entrambi `[M]` annunciati da labwc:
 *
 *        `zwp_virtual_keyboard_manager_v1`  v1   — la tastiera
 *        `zwlr_virtual_pointer_manager_v1`  v2   — il puntatore
 *
 *     e nessun permesso: wlroots non filtra, labwc filtra solo i client chiusi
 *     in una sandbox (§7).  L'unico cancello è l'uid, come per la cattura.
 *
 * ⭐ LA DIVISIONE DEL LAVORO, e perché sta così.
 *
 *   `input.c` tiene **la contabilità** — che cosa è premuto, gli orfani, il
 *   rilascio al distacco, la disposizione negoziata, le lettere — ed è la
 *   parte che GNOME e KDE hanno già pagato e misurato.  ⛔ Riscriverla qui
 *   vorrebbe dire due contabilità che un giorno divergono.
 *
 *   Qui c'è **quel che su wlroots non ha un equivalente in libei**:
 *     · la connessione Wayland, i global, i due dispositivi;
 *     · ⛔ la KEYMAP, che qui la presentiamo NOI (`no_keymap` altrimenti);
 *     · ⛔⛔ i MODIFICATORI, che con libei non esistevano (§7.2 trappola 4);
 *     · la rotella in scatti interi e il `frame` dopo ogni gesto (§7.2 1-3);
 *     · il doppione di pressione, che qui nessuno filtra per noi.
 *
 * ⛔ UN THREAD SOLO, come `input.h`: tutte le funzioni dal thread che chiama
 *    `wlr_input_gira()`.  `libwayland-client` reggerebbe più thread, ma solo
 *    con un protocollo di code che qui non c'è — e non serve.
 *
 * ⚠ UNA CONNESSIONE SUA, e non quella della cattura (`wlroots.c`).  §7.1
 *   suggeriva di condividerla; ⛔ qui si sceglie di no, dichiarandolo: la
 *   cattura pompa il filo **dentro** `wlr_fotogramma()` con le sue scadenze, e
 *   un errore di protocollo su una connessione la ammazza **intera** (è
 *   `wl_display` a morire, non l'oggetto).  ⇒ Separate, un nostro errore
 *   sull'input lascia vivo il video, e viceversa.  Il prezzo è un socket in
 *   più verso labwc.
 */
#pragma once

#include <glib.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

typedef struct WlrInput WlrInput;

/*
 * Si collega al compositore dell'utente, lega il seat e i due manager, crea la
 * tastiera e il puntatore virtuali, e ⛔ **manda subito una keymap** — senza,
 * il primo tasto è un errore di protocollo `no_keymap` che chiude l'intera
 * connessione (`wlr_virtual_keyboard_v1.c:83-88`, `STUDI.md` §xfce §7.4).
 *
 * La keymap iniziale: quella della SESSIONE, copiata dal filo
 * (`wl_seat.get_keyboard`, §7.4) se il compositore la consegna; altrimenti
 * quella che `xkbcommon` compone dall'ambiente — ⚠ e la riga di registro dice
 * quale delle due, perché sono due verità diverse.
 * ⛔ `[M]` 21 set 2026, portatile, labwc 0.8.3 headless: la sessione **non** la
 *    consegna — senza una tastiera vera il seat dichiara capacità 0, e la spia
 *    non nasce.  ⇒ Su una sessione remota la strada vera è l'AMBIENTE, e la
 *    disposizione giusta arriva un attimo dopo, con quella negoziata
 *    (`figlio.c` la applica all'apertura del canale).
 *
 * NULL con `sbaglio` scritto.
 */
WlrInput *wlr_input_apri(GError **sbaglio);

/* Il descrittore da mettere nel `poll()`; -1 se il filo è caduto. */
int wlr_input_descrittore(WlrInput *w);

/* Serve il filo SENZA aspettare: legge quel che c'è, spedisce quel che resta.
 * Ritorna gli eventi serviti, o -1 se il filo è caduto (e lo dice una volta). */
int wlr_input_gira(WlrInput *w);

bool wlr_input_caduto(const WlrInput *w);

/*
 * ⛔ LA KEYMAP IN VIGORE sulla nostra tastiera, come testo XKB (senza lo zero
 *    finale in `*lunghezza`).  È **quella** che `input.c` deve dare a
 *    `tastiera_apri_da_keymap()`: le lettere si traducono in posizioni con la
 *    stessa identica keymap con cui il compositore le rileggerà.  Due keymap
 *    «uguali» compilate due volte sono una promessa; lo stesso testo è un fatto.
 */
const char *wlr_input_keymap(const WlrInput *w, size_t *lunghezza);

/* Da dove viene la keymap in vigore: «sessione», «ambiente», o il nome chiesto. */
const char *wlr_input_keymap_origine(const WlrInput *w);

/*
 * ⭐ La disposizione negoziata (`RCP.md` §4.5: `it`, `us`, `de(neo)`) diventa la
 *    keymap della NOSTRA tastiera.  Su questa famiglia è la forma giusta di
 *    `DECISIONI.md` §5-bis.7 e non un ripiego: labwc, a ogni tasto, fa
 *    `wlr_seat_set_keyboard()` con la tastiera che l'ha battuto e manda **la
 *    sua keymap** a tutte le applicazioni (§7.4).  ⇒ Le applicazioni leggono i
 *    nostri tasti con la nostra keymap, e le scorciatoie combaciano.
 *
 * ⚠ Chi chiama rilascia PRIMA quel che è premuto: i modificatori dipendono
 *   dalla keymap, e un Maiusc premuto con la vecchia e rilasciato con la nuova
 *   è il guasto che non dà errore.
 *
 * 0 mandata, -1 no (con `sbaglio`).
 */
int wlr_input_keymap_da_nome(WlrInput *w, const char *nome, GError **sbaglio);

/* Rimanda un testo XKB già noto — serve al riattacco, per rimettere la stessa. */
int wlr_input_keymap_da_testo(WlrInput *w, const char *testo, size_t lunghezza,
                              const char *origine, GError **sbaglio);

/*
 * Un tasto, in evdev (`KEY_A` = 30).  ⛔ Il doppione (premuto due volte senza
 * rilascio, o rilasciato senza essere premuto) NON si manda e torna 0: su
 * wlroots nessuno lo filtra per noi, e un BlocMaiusc tenuto giù che si ripete
 * lo commuterebbe a ogni ripetizione.
 * 0 consegnato (o doppione ignorato), -1 no.
 */
int wlr_input_tasto(WlrInput *w, uint16_t codice, bool premuto);

/* Il puntatore assoluto: `x` in [0, l), `y` in [0, a) — l'estensione è la tela. */
int wlr_input_assoluto(WlrInput *w, uint32_t x, uint32_t y, uint32_t l, uint32_t a);

/* Un pulsante, in evdev (`BTN_LEFT` = 0x110).  ⛔ Anche qui il doppione non si
 * manda: il seat di wlroots CONTA le pressioni, e una pressione doppia vuole
 * due rilasci — col secondo che non arriverà mai. */
int wlr_input_pulsante(WlrInput *w, uint16_t codice, bool premuto);

/*
 * ⛔ Il rilascio che si manda ANCHE SE questo dispositivo non l'ha premuto:
 *    serve solo al riattacco, per chiudere un pulsante rimasto giù sul
 *    dispositivo di una connessione morta (§7.2 trappola 5).  ⚠ `[M]` sul
 *    portatile il seat headless non ne ha avuto bisogno (vedi `riattacca_wlr`
 *    in `input.c`); resta per il caso, `[?]`, di un altro puntatore nel seat.
 */
int wlr_input_rilascia_forzato(WlrInput *w, uint16_t codice);

/*
 * La rotella, in unità da 120 per scatto e ⛔ nella convenzione di WAYLAND
 * (positivo = in giù / a destra): il verso di `RCP.md` lo gira `input.c`, una
 * volta sola.  I mezzi scatti si accumulano (soglia 60, come su GNOME).
 */
int wlr_input_rotella(WlrInput *w, int32_t orizzontale, int32_t verticale);

void wlr_input_chiudi(WlrInput *w);
