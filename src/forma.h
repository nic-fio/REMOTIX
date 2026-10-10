/*
 * forma.h — THE TRUE SHAPE OF THE POINTER, where the compositor does not tell it:
 *           an ENCODED THEME and a DICTIONARY.
 *
 * ⭐ USER'S DECISION, 24 September 2026: the true shape of the pointer (the
 *    double arrow on the border, the I-beam on text, the hand on links) must
 *    reach the browser on GNOME, KDE, XFCE and LXQt.  Until today it reached it only
 *    on GNOME, where Mutter sends it in the metadata (`cursor-mode=2`, `mutter.c`).
 *
 * ⛔ THE FACT WE START FROM `[M]`: on KDE and on labwc the session runs with a
 *    cursor theme of OUR OWN (`remotix-invisibile`), because those compositors
 *    draw the pointer INSIDE the captured image and the viewer would
 *    see two.  Until today that theme was made of 1x1 images with zero
 *    alpha: the compositor drew a nothing, ⛔ and the same nothing arrived in the
 *    metadata — the shape was lost.
 *
 * ⭐ THE CURE ("ENCODED THEME + DICTIONARY" design, approved):
 *    every shape of the theme is still a 1x1 image, but OPAQUE and of a colour
 *    that is its alone.  ⇒ The colour arriving in the metadata (`cursore.c`, KDE) or in
 *    the compositor's cursor (`wlroots.c`, labwc — next increment) tells
 *    WHICH shape the application asked for.  The dictionary translates the colour
 *    into the index, and the index into the true image taken from a REAL theme on disk
 *    (Adwaita, or `breeze_cursors` if Adwaita is missing).
 *
 * ⚠ THE PRICE, declared: the compositor now draws ONE coloured pixel into the
 *   image under the hotspot.  The browser's pointer sits on top of it, and
 *   the encoder smears it; that it is not visible is `[?]` until the user
 *   looks at it.
 *
 * ===========================================================================
 * ⛔⛔ THE API BELOW IS STABLE — `wlroots.c` will use it for labwc, written by
 *      someone else after this one.  Whoever changes it changes TWO seams: say
 *      so first, and do not work around it.
 *
 *   FORMA_TEMA             the theme name; ⛔ the same as always, so that
 *                          the sessions' environment (`XCURSOR_THEME`) does not
 *                          change by a single letter.
 *   FORMA_MISURA           the nominal size requested from the real theme.
 *   FORMA_QUANTE           how many shapes the theme has (78; it can only grow).
 *
 *   forma_tema_scrivi()    writes the encoded theme to
 *                          `<runtime>/remotix/icons/remotix-invisibile/`.
 *                          The folder to put in `XCURSOR_PATH` is
 *                          `<runtime>/remotix/icons`.  FALSE = not written
 *                          (already said in the log).
 *   forma_da_pixel()       a pixel (b, g, r, a — the BGRA byte order)
 *                          ⇒ the shape index, or -1 if that colour is not
 *                          one of ours.  ⛔ Exact to the byte: no
 *                          tolerance, because two neighbours differ by 1.
 *   forma_nome()           the index ⇒ the shape name (for the log).
 *   forma_immagine()       the index ⇒ the TRUE image, premultiplied BGRA,
 *                          at most 256x256 (RCP §7.2), hotspot inside.
 *                          `out->immagine` lives for the whole process: whoever
 *                          delivers it need not copy it, whoever modifies it must.
 *                          `out->serie` is NOT touched: it belongs to the deliverer.
 *                          FALSE = the real theme is missing or unreadable (said
 *                          in the log ONCE): the caller keeps what it
 *                          did before — the client keeps its arrow.
 * ===========================================================================
 */
#ifndef REMOTIX_FORMA_H
#define REMOTIX_FORMA_H

#include "cursore.h"

#include <glib.h>
#include <stdint.h>

#define FORMA_TEMA "remotix-invisibile"

/*
 * ⚠ 24 is the size the environment already declares (`XCURSOR_SIZE=24`,
 *   `sessione.c`) and GNOME's default at scale 1 — `[?]` that it is
 *   also the one Mutter sends today: not measured here.  If the real themes do not
 *   have 24, the nearest nominal size is taken.
 */
#define FORMA_MISURA 24

/* ⚠ 68 until 24 Sep 2026; 78 since labwc asked for the CSS names of its
 *   borders (`n-resize`… `w-resize`, see `forma.c`).  It grows at the END. */
#define FORMA_QUANTE 78

gboolean forma_tema_scrivi(const char *runtime);

int forma_da_pixel(uint8_t b, uint8_t g, uint8_t r, uint8_t a);

const char *forma_nome(int indice);

gboolean forma_immagine(int indice, CursoreForma *out);

/*
 * ⚠ FOR THE BENCHES ONLY: where to take the real themes from instead of
 *   `/usr/share/icons`, and forget what had been loaded.  The product
 *   never calls it.
 */
void forma_prova_cartella_temi(const char *cartella);

#endif /* REMOTIX_FORMA_H */
