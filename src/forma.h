/*
 * forma.h — LA FORMA VERA DEL PUNTATORE, dove il compositore non la dice:
 *           un TEMA CODIFICATO e un DIZIONARIO.
 *
 * ⭐ DECISIONE DELL'UTENTE, 24 settembre 2026: la forma vera del puntatore (la
 *    freccia doppia sul bordo, la I sul testo, la mano sui collegamenti) deve
 *    arrivare al browser su GNOME, KDE, XFCE e LXQt.  Fino a oggi arrivava solo
 *    su GNOME, dove Mutter la manda nel metadato (`cursor-mode=2`, `mutter.c`).
 *
 * ⛔ IL FATTO DA CUI SI PARTE `[M]`: su KDE e su labwc la sessione gira con un
 *    tema del cursore NOSTRO (`remotix-invisibile`), perche' quei compositori
 *    disegnano il puntatore DENTRO l'immagine catturata e chi guarda ne
 *    vedrebbe due.  Fino a oggi quel tema era fatto di immagini 1x1 ad alfa
 *    zero: il compositore disegnava un nulla, ⛔ e nel metadato arrivava lo
 *    stesso nulla — la forma si perdeva.
 *
 * ⭐ LA CURA (progetto «TEMA CODIFICATO + DIZIONARIO», approvato):
 *    ogni forma del tema e' ancora un'immagine 1x1, ma OPACA e di un colore che
 *    e' solo suo.  ⇒ Il colore che arriva nel metadato (`cursore.c`, KDE) o nel
 *    cursore del compositore (`wlroots.c`, labwc — incremento successivo) dice
 *    QUALE forma l'applicazione ha chiesto.  Il dizionario traduce il colore
 *    nell'indice, e l'indice nell'immagine vera presa da un tema REALE su disco
 *    (Adwaita, o `breeze_cursors` se Adwaita manca).
 *
 * ⚠ IL PREZZO, dichiarato: il compositore ora disegna nell'immagine UN pixel
 *   colorato sotto il punto attivo.  Il puntatore del browser gli sta sopra, e
 *   il codificatore lo sbava; che non si veda e' `[?]` finche' non lo guarda
 *   l'utente.
 *
 * ===========================================================================
 * ⛔⛔ L'API QUI SOTTO E' STABILE — la usera' `wlroots.c` per labwc, scritta da
 *      un altro dopo di questa.  Chi la cambia cambia DUE cuciture: lo dice
 *      prima, e non la aggira.
 *
 *   FORMA_TEMA             il nome del tema; ⛔ lo stesso di sempre, cosi'
 *                          l'ambiente delle sessioni (`XCURSOR_THEME`) non
 *                          cambia di una lettera.
 *   FORMA_MISURA           la misura nominale che si chiede al tema reale.
 *   FORMA_QUANTE           quante forme ha il tema (68).
 *
 *   forma_tema_scrivi()    scrive il tema codificato in
 *                          `<runtime>/remotix/icons/remotix-invisibile/`.
 *                          La cartella da mettere in `XCURSOR_PATH` e'
 *                          `<runtime>/remotix/icons`.  FALSE = non scritto
 *                          (gia' detto nel registro).
 *   forma_da_pixel()       un pixel (b, g, r, a — l'ordine dei byte BGRA)
 *                          ⇒ l'indice della forma, o -1 se quel colore non e'
 *                          uno dei nostri.  ⛔ Esatto al byte: niente
 *                          tolleranza, perche' due vicini differiscono di 1.
 *   forma_nome()           l'indice ⇒ il nome della forma (per il registro).
 *   forma_immagine()       l'indice ⇒ l'immagine VERA, BGRA premoltiplicato,
 *                          al massimo 256x256 (RCP §7.2), punto attivo dentro.
 *                          `out->immagine` vive per tutto il processo: chi la
 *                          consegna non la deve copiare, chi la modifica si.
 *                          `out->serie` NON si tocca: e' di chi consegna.
 *                          FALSE = il tema reale non c'e' o non si legge (detto
 *                          nel registro UNA volta): chi chiama tiene quel che
 *                          faceva prima — il cliente tiene la sua freccia.
 * ===========================================================================
 */
#ifndef REMOTIX_FORMA_H
#define REMOTIX_FORMA_H

#include "cursore.h"

#include <glib.h>
#include <stdint.h>

#define FORMA_TEMA "remotix-invisibile"

/*
 * ⚠ 24 e' la misura che l'ambiente gia' dichiara (`XCURSOR_SIZE=24`,
 *   `sessione.c`) e quella predefinita di GNOME a scala 1 — `[?]` che sia
 *   anche quella che Mutter manda oggi: non misurato qui.  Se i temi reali non
 *   hanno il 24, si prende la misura nominale piu' vicina.
 */
#define FORMA_MISURA 24

#define FORMA_QUANTE 68

gboolean forma_tema_scrivi(const char *runtime);

int forma_da_pixel(uint8_t b, uint8_t g, uint8_t r, uint8_t a);

const char *forma_nome(int indice);

gboolean forma_immagine(int indice, CursoreForma *out);

/*
 * ⚠ PER I BANCHI SOLTANTO: da dove prendere i temi reali invece di
 *   `/usr/share/icons`, e dimenticare quel che si era caricato.  Il prodotto
 *   non la chiama mai.
 */
void forma_prova_cartella_temi(const char *cartella);

#endif /* REMOTIX_FORMA_H */
