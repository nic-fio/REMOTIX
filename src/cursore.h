/*
 * cursore.h — THE SEAM of the cursor shape: from PipeWire to the wire.
 *
 * ⛔ THIS FILE BELONGS TO THE COORDINATOR (see `input.h`, same reason).
 *
 * The defect this module exists to cure — `STUDI.md` §gnome §1.1 point 6 and
 * §5.2, and it is `[R]`: we ask Mutter for `cursor-mode=2`, that is "give me the
 * cursor as METADATA instead of in the pixels", ⛔ but we do NOT ask for
 * `SPA_META_Cursor` ⇒ shape, position and hotspot do not arrive at all, and
 * `CURSORE_FORMA` (`RCP.md` §7.2) is a channel without a source.
 *
 * ⭐ And the direction is the right one for us: clean pixels in the image (so
 *    two are not seen, `SPECIFICHE.md` §7.1) AND the shape in a side band, which
 *    is exactly what the pointer drawn by the client needs.
 */
#ifndef REMOTIX_CURSORE_H
#define REMOTIX_CURSORE_H

#include <stdint.h>
#include <stddef.h>

/*
 * A cursor shape, as it arrives from PipeWire metadata and as it leaves on the
 * wire.  ⛔ The limits are those of `RCP.md` §5.5 and §7.2, and they are enforced HERE:
 * whoever sends a cursor larger than 256 brings the session down on the other
 * side with `ERRORE_PROTOCOLLO`.
 */
#define CURSORE_MAX_LATO 256

typedef struct {
	uint16_t larghezza;   /* 0 with height 0 = HIDDEN cursor (§5.5)       */
	uint16_t altezza;
	int16_t  attivo_x;    /* the point that "points" ⛔ 0 if hidden        */
	int16_t  attivo_y;
	uint32_t serie;       /* grows at every shape change; so as not to resend
	                       * the same image a thousand times              */
	const uint8_t *immagine;  /* width x height x 4, PREMULTIPLIED BGRA.
	                           * Lives until the next callback: whoever wants
	                           * to keep it copies it.  NULL if hidden.    */
} CursoreForma;

/*
 * The call `cattura.c` makes when the cursor metadata changes inside
 * a PipeWire buffer.  ⛔ `cattura.c` does NOT know the wire: it goes through here.
 * Returns 0 if the shape was accepted, -1 if it is malformed (and then it is
 * DECLARED in the log, nothing is sent).
 */
typedef int (*CursoreArrivata)(void *chi, const CursoreForma *);

/*
 * ⛔ Why there is a module and not a direct call: between PipeWire and the
 *    wire there is work that belongs to neither — recognising that the
 *    shape has NOT changed (the metadata arrives with every buffer), cutting to 256,
 *    and telling "hidden" apart from "not received".  Without a place of its own, that
 *    work ends up half in `cattura.c` and half in `rcp.c`, which is the shape
 *    of the phase 3 defect.
 */
typedef struct cursore Cursore;

Cursore *cursore_apri(CursoreArrivata quando_cambia, void *chi);

/*
 * To be called with PipeWire's raw metadata (`struct spa_meta_cursor`).
 * Returns 1 if the shape CHANGED (and then `quando_cambia` has already been
 * called), 0 if it is the same as before, -1 if it is malformed.
 */
int cursore_metadato(Cursore *, const void *spa_meta_cursor, size_t dimensione);

/*
 * ⛔⭐ "NEVER HIDE HERE" — phase 12, 20 September 2026, on Plasma.
 *
 * On KWin `--virtual` the cursor is drawn by the compositor INSIDE the image, and
 * the session deliberately starts with a theme of transparent shapes
 * (`sessione.c`, `scrivi_tema_cursore_kde`).  ⇒ From then on the metadata always
 * says "no image", which by §5.5 means HIDDEN — and the page, with the
 * cursor hidden, removes the browser's too: `[M]` the user's
 * test, "the pointer is not visible any more", which is worse than seeing two.
 * ⇒ With this switch hiding is NOT delivered: the viewer keeps
 *   their system's pointer, which is v1's design.
 * ⚠ And the price, declared: on Plasma an application that hides the cursor
 *   (a game, a full-screen player) does not hide it from the viewer — it
 *   cannot be told apart from our invisible theme, which is always in force.
 */
void cursore_mai_nascondere(Cursore *, const char *perche);

void cursore_chiudi(Cursore *);

#endif /* REMOTIX_CURSORE_H */
