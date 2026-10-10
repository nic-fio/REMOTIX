/*
 * cursore.c — from `struct spa_meta_cursor` (PipeWire) to `CursoreForma` (RCP §7.2).
 *
 * ⛔ The contract is in `cursore.h`, which belongs to the coordinator: here it is
 *    IMPLEMENTED, the seam is not changed.  Whoever finds the contract wrong SAYS so
 *    and stops — does not work around it.
 *
 * ===========================================================================
 * ⛔ THE WORK THAT LIVES HERE AND NEITHER IN `cattura.c` NOR IN `rcp.c`
 *
 * 1. **telling apart three states that the metadata merges into one**:
 *
 *      NOT RECEIVED    the metadata is not there at all ⇒ this function is not
 *                      even called, and `cattura.c` COUNTS it.  Nothing leaves
 *                      on the wire: the client keeps its own pointer.
 *      HIDDEN          the pointer is there and must not be seen ⇒ `CURSORE_FORMA`
 *                      with 0x0 and hotspot 0,0 (RCP §5.5).
 *      UNCHANGED       the metadata arrives with EVERY buffer, and is almost always
 *                      the same as before ⇒ nothing is sent.
 *
 * 2. enforcing the limits of RCP §7.2 **on this side**: beyond 256 nothing is
 *    sent, or the receiver closes the session with `ERRORE_PROTOCOLLO` — that is,
 *    an error of ours here drops the client's session;
 *
 * 3. turning the bytes around: Mutter delivers **premultiplied RGBA**, the wire wants
 *    **premultiplied BGRA**.
 *
 * ===========================================================================
 * ⛔ HOW MUTTER FILLS THE METADATA — `[R]` 14 August 2026, read line by line
 *    in `reference-gnome/mutter/src/backends/meta-screen-cast-stream-src.c` and
 *    `meta-screen-cast-virtual-stream-src.c` (our case: `RecordVirtual`).
 *
 *   | when                                          | what arrives                   |
 *   |-----------------------------------------------|--------------------------------|
 *   | pointer not visible, or outside the stream     | `id = 0`  (`unset_cursor_…`)   |
 *   | the bitmap has NOT changed                     | `id = 1`, `bitmap_offset = 0`  |
 *   | the bitmap has changed, and there is a texture | `RGBA` bitmap with the pixels  |
 *   | the bitmap has changed, and there is NO texture| ZEROED bitmap (`set_empty…`)   |
 *
 *   ⛔ `set_empty_cursor_sprite_metadata()` writes `format = RGBA`, then
 *      `*spa_meta_bitmap = (struct spa_meta_bitmap) { 0 };` — that is, it zeroes
 *      everything it had just written.  ⇒ a bitmap arrives with `format = 0`,
 *      `0x0`, `stride = 0`, `offset = 0`.  Mutter's INTENTION is "cursor
 *      without an image", that is HIDDEN; the letter of `spa/buffer/meta.h` says
 *      instead that `format = 0` must be treated as "no new information".
 *      ⇒ Here **the intention** is followed, because it is the only way an
 *      invisible cursor can arrive on Mutter, and because `offset = 0` confirms it:
 *      the same header says *"an offset of 0 means no image data
 *      (invisible)"*.  ⚠ The choice is DECLARED here because on another
 *      compositor it could mean the other thing: it is `[R]` on Mutter, `[?]`
 *      elsewhere.
 *
 *   ⛔ AND THE TRAP OF COMING BACK ON: `bitmap_offset = 0` means "the shape
 *      has not changed", but after an `id = 0` the client has nothing left to
 *      draw.  If only the position arrived when the pointer returns, the
 *      cursor would stay gone **without any error**.  ⇒ the last VISIBLE
 *      shape is kept, and SENT AGAIN when the pointer returns.
 *
 * ⚠ AND THE SIZE MUTTER CAN SEND IS LARGER THAN THE WIRE: the metadata is
 *   allocated for **384x384** (`CURSOR_META_SIZE(384, 384)`), RCP §7.2 stops at
 *   **256**.  Cutting is a fallback, and as such it is DECLARED in the log.
 */
#include "cursore.h"

#include "forma.h"
#include "registro.h"

#include <spa/buffer/meta.h>
#include <spa/param/video/raw.h>

#include <inttypes.h>
#include <stdlib.h>
#include <string.h>

#define AREA "cursore"

/* The most bytes an image delivered on the wire can take. */
#define BYTE_MAX ((size_t) CURSORE_MAX_LATO * (size_t) CURSORE_MAX_LATO * 4u)

/* ⚠ A sanity ceiling BEFORE multiplying: an absurd size read from someone
 *   else's memory must not turn into a multiplication that overflows.  It is
 *   not the wire's limit (which is 256): it is the limit beyond which one declares
 *   "malformed" instead of "cut". */
#define LATO_ASSURDO 8192u

struct cursore
{
	CursoreArrivata quando_cambia;
	void *chi;

	uint32_t serie;

	int consegnata; /* has anything been delivered yet?            */
	int nascosto;   /* the last one delivered was 0x0               */
	int mai_nascondere; /* §kde: the theme is invisible, see cursore.h  */
	int detto_mai;      /* the log line is written only once           */

	/*
	 * The last known VISIBLE shape.  ⛔ It survives hiding on
	 * purpose: Mutter turns the pointer back on without resending the bitmap.
	 */
	int ha_forma;
	uint16_t larghezza, altezza;
	int16_t attivo_x, attivo_y;
	uint8_t *immagine; /* the DELIVERED one: lives until the next call */
	uint8_t *scratch;  /* where the new one is turned around, so it can be COMPARED */
	size_t byte;

	/* The counts: they tell "has not changed" from "has not arrived"
	 * six hours later, and they are the number the bench compares with its own. */
	struct
	{
		uint64_t visti;        /* calls to cursore_metadato              */
		uint64_t id_zero;      /* the producer says "no cursor"          */
		uint64_t senza_bitmap; /* id != 0 but bitmap_offset == 0         */
		uint64_t con_bitmap;   /* a bitmap was there                     */
		uint64_t vuote;        /* bitmap that means "hidden"             */
		uint64_t uguali;       /* bitmap identical to the previous one   */
		uint64_t cambi;        /* CursoreForma delivered                 */
		uint64_t tagliate;     /* larger than 256: ⛔ fallback          */
		uint64_t punto_fuori;  /* hotspot outside the image             */
		uint64_t malformate;
		uint64_t forma_ignota; /* visible, but we have never seen the shape */
		uint64_t rifiutate;    /* the receiver said no                   */
		uint64_t codificate;   /* a colour of the encoded theme (forma.h) */
	} conto;

	int ultimo_indice;     /* the last encoded shape seen, for the log */

	/* The troubles said ONCE and not on every frame. */
	int detto_formato;
	uint32_t formato_visto;
	int detto_taglio;
	int detto_punto;
	int detto_ignota;
};

/* ------------------------------------------------------------------ *
 *  Delivery
 * ------------------------------------------------------------------ */

static int consegna(Cursore *c, const CursoreForma *forma)
{
	int esito;

	c->conto.cambi++;
	c->consegnata = 1;
	if (!c->quando_cambia)
		return 1;
	esito = c->quando_cambia(c->chi, forma);
	if (esito < 0)
	{
		c->conto.rifiutate++;
		registro_dice(AREA, "⛔ the receiver REFUSED shape %ux%u (series %u): it was not sent",
		              (unsigned) forma->larghezza, (unsigned) forma->altezza,
		              (unsigned) forma->serie);
		return -1;
	}
	return 1;
}

/*
 * ⛔ HIDDEN IS A STATE, NOT AN ABSENCE: 0x0 with hotspot 0,0 is sent
 *    (RCP §5.5), and sent ONCE only — not on every buffer in which the
 *    pointer is still not there.
 */
static int consegna_nascosto(Cursore *c, const char *motivo)
{
	CursoreForma forma;

	if (c->mai_nascondere) {
		if (!c->detto_mai) {
			c->detto_mai = 1;
			registro_dice(AREA,
			              "the pointer would be HIDDEN (%s) and I do NOT deliver it: on "
			              "this desktop the cursor theme is invisible on purpose, and "
			              "the viewer must keep their own pointer (cursore.h)",
			              motivo);
		}
		return 0;
	}
	if (c->consegnata && c->nascosto)
		return 0;

	c->serie++;
	c->nascosto = 1;

	memset(&forma, 0, sizeof forma);
	forma.serie = c->serie;
	forma.immagine = NULL;

	registro_dice(AREA, "the pointer HIDES (%s) — CURSORE_FORMA 0x0, series %u", motivo,
	              (unsigned) c->serie);
	return consegna(c, &forma);
}

/* The pointer returns and Mutter does not resend the bitmap: the last known one is resent. */
static int consegna_forma_conservata(Cursore *c)
{
	CursoreForma forma;

	c->serie++;
	c->nascosto = 0;

	memset(&forma, 0, sizeof forma);
	forma.larghezza = c->larghezza;
	forma.altezza = c->altezza;
	forma.attivo_x = c->attivo_x;
	forma.attivo_y = c->attivo_y;
	forma.serie = c->serie;
	forma.immagine = c->immagine;

	registro_dice(AREA,
	              "the pointer RETURNS and Mutter does not resend the shape: the last known one "
	              "is resent (%ux%u, series %u)",
	              (unsigned) c->larghezza, (unsigned) c->altezza, (unsigned) c->serie);
	return consegna(c, &forma);
}

/* ------------------------------------------------------------------ *
 *  The bytes: from premultiplied RGBA/BGRA to premultiplied BGRA
 * ------------------------------------------------------------------ */

/*
 * ⛔ The format is checked, not taken for granted.  Mutter sends
 *    `SPA_VIDEO_FORMAT_RGBA` — that is `COGL_PIXEL_FORMAT_RGBA_8888_PRE`, which is
 *    **premultiplied** `[R]` — and the wire wants premultiplied BGRA: only the
 *    order changes, not the alpha.
 *
 * ⚠ The variants without alpha (`RGBx`, `BGRx`) are accepted with full alpha: they are
 *   opaque by definition, and an opaque shape is better than no shape.
 *
 * Returns 1 if red and blue must be swapped, 0 if copied straight, -1 if the
 * format cannot be read.
 */
static int verso_dei_byte(uint32_t formato, int *alfa_piena)
{
	*alfa_piena = 0;
	switch (formato)
	{
	case SPA_VIDEO_FORMAT_RGBA:
		return 1;
	case SPA_VIDEO_FORMAT_BGRA:
		return 0;
	case SPA_VIDEO_FORMAT_RGBx:
		*alfa_piena = 1;
		return 1;
	case SPA_VIDEO_FORMAT_BGRx:
		*alfa_piena = 1;
		return 0;
	default:
		return -1;
	}
}

/* ------------------------------------------------------------------ *
 *  The calls
 * ------------------------------------------------------------------ */

Cursore *cursore_apri(CursoreArrivata quando_cambia, void *chi)
{
	Cursore *c = calloc(1, sizeof *c);

	if (!c)
		return NULL;
	c->immagine = malloc(BYTE_MAX);
	c->scratch = malloc(BYTE_MAX);
	if (!c->immagine || !c->scratch)
	{
		free(c->immagine);
		free(c->scratch);
		free(c);
		return NULL;
	}
	c->quando_cambia = quando_cambia;
	c->chi = chi;
	c->ultimo_indice = -1;
	return c;
}

int cursore_metadato(Cursore *c, const void *spa_meta_cursor, size_t dimensione)
{
	const struct spa_meta_cursor *m = spa_meta_cursor;
	const struct spa_meta_bitmap *b;
	const uint8_t *base = spa_meta_cursor;
	size_t inizio_pixel, servono, byte;
	uint32_t sorgente_l, sorgente_a;
	uint16_t larghezza, altezza;
	int16_t attivo_x, attivo_y;
	int inverti, alfa_piena;
	uint32_t y;
	uint8_t *scambio;
	CursoreForma forma;

	if (!c)
		return -1;
	c->conto.visti++;

	/*
	 * ⛔ "Too short" is NOT "hidden": it is metadata that cannot be
	 *    read, and it is declared instead of producing a cursor made of someone
	 *    else's memory — which is exactly the defect RCP §7.2 names.
	 */
	if (!m || dimensione < sizeof *m)
	{
		c->conto.malformate++;
		registro_dice(AREA, "⛔ cursor metadata too short: %zu bytes, %zu needed",
		              dimensione, sizeof *m);
		return -1;
	}

	/* --- 1. the producer says "no cursor" ------------------------------ */
	if (!spa_meta_cursor_is_valid(m))
	{
		c->conto.id_zero++;
		return consegna_nascosto(c, "id = 0");
	}

	/* --- 2. the shape has not changed ----------------------------------- */
	if (m->bitmap_offset == 0)
	{
		c->conto.senza_bitmap++;
		if (!c->nascosto && c->consegnata)
			return 0;
		if (c->ha_forma)
			return consegna_forma_conservata(c);
		/*
		 * ⛔ The pointer is there and we have NEVER seen its shape: it is not
		 *    "hidden" and not "unchanged".  Nothing is invented — it is
		 *    declared and the first bitmap is awaited.
		 */
		c->conto.forma_ignota++;
		if (!c->detto_ignota)
		{
			c->detto_ignota = 1;
			registro_dice(AREA,
			              "⚠ the pointer is visible but its shape has not arrived yet "
			              "(position only): nothing to send, waiting");
		}
		return 0;
	}

	/* --- 3. there is a bitmap: first check that it fits ---------------- */
	if (m->bitmap_offset < sizeof *m || m->bitmap_offset > dimensione ||
	    dimensione - m->bitmap_offset < sizeof *b)
	{
		c->conto.malformate++;
		registro_dice(AREA, "⛔ bitmap_offset %u outside the metadata (%zu bytes): discarded",
		              (unsigned) m->bitmap_offset, dimensione);
		return -1;
	}
	b = (const struct spa_meta_bitmap *) (base + m->bitmap_offset);
	c->conto.con_bitmap++;

	/*
	 * --- 4. the bitmap that means "hidden" ------------------------------
	 * See the box at the top: on Mutter it is `set_empty_cursor_sprite_metadata`,
	 * which zeroes everything.  `offset == 0` is the same thing said by
	 * `spa/buffer/meta.h`: "no image data (invisible)".
	 */
	if (b->format == 0 || b->offset == 0 || b->size.width == 0 || b->size.height == 0)
	{
		c->conto.vuote++;
		return consegna_nascosto(c, "empty bitmap (the pointer has no image)");
	}

	sorgente_l = b->size.width;
	sorgente_a = b->size.height;
	if (sorgente_l > LATO_ASSURDO || sorgente_a > LATO_ASSURDO || b->stride <= 0 ||
	    (uint32_t) b->stride < sorgente_l * 4u || b->offset < sizeof *b)
	{
		c->conto.malformate++;
		registro_dice(AREA, "⛔ bitmap cannot be interpreted: %ux%u, stride %d, offset %u",
		              (unsigned) sorgente_l, (unsigned) sorgente_a, (int) b->stride,
		              (unsigned) b->offset);
		return -1;
	}

	inizio_pixel = (size_t) m->bitmap_offset + (size_t) b->offset;
	servono = (size_t) b->stride * (size_t) (sorgente_a - 1) + (size_t) sorgente_l * 4u;
	if (inizio_pixel > dimensione || dimensione - inizio_pixel < servono)
	{
		c->conto.malformate++;
		registro_dice(AREA,
		              "⛔ the cursor pixels do not fit: %zu bytes needed from %zu, the metadata "
		              "has %zu",
		              servono, inizio_pixel, dimensione);
		return -1;
	}

	inverti = verso_dei_byte(b->format, &alfa_piena);
	if (inverti < 0)
	{
		c->conto.malformate++;
		if (!c->detto_formato || c->formato_visto != b->format)
		{
			c->detto_formato = 1;
			c->formato_visto = b->format;
			registro_dice(AREA,
			              "⛔ cursor format not handled (SPA %u): nothing is sent "
			              "rather than sending swapped colours",
			              (unsigned) b->format);
		}
		return -1;
	}

	/*
	 * --- 5. ⛔ THE LIMIT OF RCP §7.2 IS ENFORCED HERE --------------------
	 *
	 * Beyond 256 the receiver closes the session with `ERRORE_PROTOCOLLO`: it is
	 * our defect that drops the client.  ⇒ It is CUT (the verb is
	 * `cursore.h`'s), and ⛔ the fallback is DECLARED — `CODER.md` §4.2.
	 *
	 * ⚠ The cut keeps the top-left corner, which is where every cursor's drawing
	 *   is and where the hotspot is.  Whether it is the right choice is
	 *   `[?]`: it has never been seen to trigger (Mutter allocates the metadata for
	 *   384x384, but GNOME themes go up to 64-96).  If one day it really
	 *   triggered, the thing to measure is whether **downsampling** is better instead.
	 */
	larghezza = sorgente_l > CURSORE_MAX_LATO ? (uint16_t) CURSORE_MAX_LATO : (uint16_t) sorgente_l;
	altezza = sorgente_a > CURSORE_MAX_LATO ? (uint16_t) CURSORE_MAX_LATO : (uint16_t) sorgente_a;
	if (larghezza != sorgente_l || altezza != sorgente_a)
	{
		c->conto.tagliate++;
		if (!c->detto_taglio)
		{
			c->detto_taglio = 1;
			registro_dice(AREA,
			              "⛔ FALLBACK: the cursor is %ux%u, the wire stops at %u (RCP §7.2) — "
			              "sending the %ux%u corner",
			              (unsigned) sorgente_l, (unsigned) sorgente_a,
			              (unsigned) CURSORE_MAX_LATO, (unsigned) larghezza, (unsigned) altezza);
		}
	}

	/*
	 * ⛔ AND THE HOTSPOT MUST LIE INSIDE THE IMAGE (RCP §5.5), or the
	 *    receiver closes.  If outside it is brought back inside, and declared.
	 */
	if (m->hotspot.x < 0 || m->hotspot.x >= (int32_t) larghezza || m->hotspot.y < 0 ||
	    m->hotspot.y >= (int32_t) altezza)
	{
		c->conto.punto_fuori++;
		if (!c->detto_punto)
		{
			c->detto_punto = 1;
			registro_dice(AREA,
			              "⛔ FALLBACK: hotspot %d,%d outside %ux%u — brought back inside "
			              "(RCP §5.5)",
			              (int) m->hotspot.x, (int) m->hotspot.y, (unsigned) larghezza,
			              (unsigned) altezza);
		}
		attivo_x = m->hotspot.x < 0
		               ? 0
		               : (m->hotspot.x >= (int32_t) larghezza ? (int16_t) (larghezza - 1)
		                                                      : (int16_t) m->hotspot.x);
		attivo_y = m->hotspot.y < 0
		               ? 0
		               : (m->hotspot.y >= (int32_t) altezza ? (int16_t) (altezza - 1)
		                                                    : (int16_t) m->hotspot.y);
	}
	else
	{
		attivo_x = (int16_t) m->hotspot.x;
		attivo_y = (int16_t) m->hotspot.y;
	}

	/* --- 6. the bytes, turned around row by row in the work buffer ------ */
	byte = (size_t) larghezza * (size_t) altezza * 4u;
	for (y = 0; y < altezza; y++)
	{
		const uint8_t *riga = base + inizio_pixel + (size_t) y * (size_t) b->stride;
		uint8_t *fuori = c->scratch + (size_t) y * (size_t) larghezza * 4u;
		uint32_t x;

		if (!inverti && !alfa_piena)
		{
			memcpy(fuori, riga, (size_t) larghezza * 4u);
			continue;
		}
		for (x = 0; x < larghezza; x++)
		{
			uint8_t r0 = riga[x * 4 + 0], r1 = riga[x * 4 + 1];
			uint8_t r2 = riga[x * 4 + 2], r3 = riga[x * 4 + 3];

			fuori[x * 4 + 0] = inverti ? r2 : r0;
			fuori[x * 4 + 1] = r1;
			fuori[x * 4 + 2] = inverti ? r0 : r2;
			fuori[x * 4 + 3] = alfa_piena ? 0xFF : r3;
		}
	}

	/*
	 * --- 6-bis. ⛔⭐ ALL TRANSPARENT MEANS "HIDDEN" — 20 Sep 2026.
	 *
	 * ⛔ `[M]` The user's test on KDE: to remove the cursor KWin draws
	 *    INSIDE the image (`--virtual` backend) the session starts with
	 *    a theme of 1x1 shapes with zero alpha (`sessione.c`,
	 *    `scrivi_tema_cursore_kde`).  ⇒ That theme also arrives HERE, in the
	 *    metadata, and the client dressed itself in an invisible shape: **no
	 *    pointer**, which is worse than two.
	 * ⭐ An image in which no pixel is visible is NOT a shape: it is the same
	 *    fact §5.5 calls "hidden", said with more bytes.  ⇒ `0x0` is
	 *    delivered, and the client puts up ITS OWN pointer (`pagina.html`,
	 *    `forma_vuota`).
	 * ⚠ And the work buffer is checked AFTER the conversion: `alfa_piena`
	 *   fills the alpha, and a bitmap without an alpha channel is not transparent.
	 *
	 * ⭐⭐ PHASE 14, 24 Sep 2026 — FIRST OF ALL, THE ENCODED THEME (`forma.h`).
	 *      The session theme is no longer transparent: every shape is an
	 *      OPAQUE pixel of its own colour.  ⇒ If the WHOLE bitmap is of a single
	 *      colour and the dictionary recognises it (1x1, or scaled by the compositor:
	 *      a single colour stays a single colour), that is not the shape to
	 *      send — it is the NAME of the shape.  The REAL image taken from the real
	 *      theme is put into the work buffer, and we go on to the comparison
	 *      of step 7 as for any bitmap.
	 * ⛔ If the real theme is missing (`forma_immagine` FALSE, already said in the
	 *    log) we fall through to the check below, which on an opaque pixel does NOT
	 *    trigger: the client would receive the coloured pixel.  ⇒ In that case it
	 *    is treated like the invisible theme of before — "hidden", that is, with
	 *    `mai_nascondere` the client keeps ITS OWN arrow, as until yesterday.
	 * ⭐ `[R]` GNOME DOES NOT COME THIS WAY: in the GNOME branch `sessione.c` sets
	 *    no `XCURSOR_*`, and Mutter sends the bitmap of its theme (Adwaita),
	 *    made of black, white and shades — never all of one colour, and the
	 *    red of ours (0x40-0x83) with exact green and blue is not an Adwaita
	 *    colour.  Only KDE (KWin, zkde metadata, mode 4) reads our theme
	 *    and then arrives here; labwc has its own road (`wlroots.c`).
	 */
	{
		size_t i;
		int indice = forma_da_pixel(c->scratch[0], c->scratch[1], c->scratch[2],
		                            c->scratch[3]);

		for (i = 4; indice >= 0 && i < byte; i += 4)
			if (memcmp(c->scratch + i, c->scratch, 4) != 0)
				indice = -1;
		if (indice >= 0) {
			CursoreForma vera;

			c->conto.codificate++;
			memset(&vera, 0, sizeof vera);
			if (!forma_immagine(indice, &vera)) {
				c->conto.vuote++;
				return consegna_nascosto(c, "encoded shape but real theme missing");
			}
			larghezza = vera.larghezza;
			altezza = vera.altezza;
			attivo_x = vera.attivo_x;
			attivo_y = vera.attivo_y;
			byte = (size_t) larghezza * (size_t) altezza * 4u;
			memcpy(c->scratch, vera.immagine, byte);
			if (indice != c->ultimo_indice) {
				c->ultimo_indice = indice;
				/* ⚠ One line per shape CHANGE, not per buffer: it is the pace of
				 *   the hand of whoever uses the desktop, and the proof that the
				 *   dictionary works can only be read here. */
				registro_dice(AREA, "encoded shape %d «%s» ⇒ %ux%u, hotspot %d,%d",
				              indice, forma_nome(indice), (unsigned) larghezza,
				              (unsigned) altezza, (int) attivo_x, (int) attivo_y);
			}
			goto confronto;
		}
	}
	{
		size_t i;
		int si_vede = 0;

		for (i = 3; i < byte; i += 4)
			if (c->scratch[i]) {
				si_vede = 1;
				break;
			}
		if (!si_vede) {
			c->conto.vuote++;
			return consegna_nascosto(c, "all pixels transparent (the cursor "
			                            "theme is invisible: the client draws it)");
		}
	}

confronto:
	/*
	 * --- 7. ⛔ HAS IT REALLY CHANGED? -----------------------------------
	 *
	 * The metadata arrives with EVERY buffer.  Without this comparison the same
	 * image would be resent a thousand times — which is the reason this module
	 * exists (`cursore.h`).  ⇒ the new bytes are turned around in the work buffer,
	 * COMPARED with the delivered ones, and only if they differ are the two
	 * buckets swapped (so the delivered image stays valid until the next
	 * call, as `cursore.h` promises).
	 *
	 * ⚠ And the comparison is with the last **delivered** one: after a hide the
	 *   client has nothing left to draw, so the same shape must be
	 *   resent even if identical.
	 */
	if (!c->nascosto && c->consegnata && c->ha_forma && c->larghezza == larghezza &&
	    c->altezza == altezza && c->attivo_x == attivo_x && c->attivo_y == attivo_y &&
	    c->byte == byte && memcmp(c->immagine, c->scratch, byte) == 0)
	{
		c->conto.uguali++;
		return 0;
	}

	scambio = c->immagine;
	c->immagine = c->scratch;
	c->scratch = scambio;

	c->larghezza = larghezza;
	c->altezza = altezza;
	c->attivo_x = attivo_x;
	c->attivo_y = attivo_y;
	c->byte = byte;
	c->ha_forma = 1;
	c->nascosto = 0;
	c->serie++;

	memset(&forma, 0, sizeof forma);
	forma.larghezza = larghezza;
	forma.altezza = altezza;
	forma.attivo_x = attivo_x;
	forma.attivo_y = attivo_y;
	forma.serie = c->serie;
	forma.immagine = c->immagine;

	return consegna(c, &forma);
}

void cursore_mai_nascondere(Cursore *c, const char *perche)
{
	if (!c || c->mai_nascondere)
		return;
	c->mai_nascondere = 1;
	registro_dice(AREA, "pointer hiding will NOT be delivered any more: %s",
	              perche ? perche : "no reason given");
	/* ⭐ PHASE 14 — and the dictionary is loaded NOW, outside the PipeWire
	 *    thread: it is 68 files of the real theme read from disk, and doing it at
	 *    the first encoded shape would mean doing it on the real-time thread
	 *    of the capture.  ⚠ It is called only on KDE (the one using the encoded theme
	 *    with the metadata), so GNOME does not pay for this read. */
	{
		CursoreForma prima;

		memset(&prima, 0, sizeof prima);
		(void) forma_immagine(0, &prima);
	}
}

void cursore_chiudi(Cursore *c)
{
	if (!c)
		return;
	registro_dice(AREA,
	              "metadata %" PRIu64 ": id=0 %" PRIu64 ", position only %" PRIu64
	              ", with bitmap %" PRIu64 " (identical %" PRIu64 ", empty %" PRIu64
	              ") ⇒ CURSORE_FORMA delivered %" PRIu64 "; cut %" PRIu64
	              ", hotspot outside %" PRIu64 ", malformed %" PRIu64 ", refused %" PRIu64
	              ", unknown shape %" PRIu64 ", encoded %" PRIu64,
	              c->conto.visti, c->conto.id_zero, c->conto.senza_bitmap, c->conto.con_bitmap,
	              c->conto.uguali, c->conto.vuote, c->conto.cambi, c->conto.tagliate,
	              c->conto.punto_fuori, c->conto.malformate, c->conto.rifiutate,
	              c->conto.forma_ignota, c->conto.codificate);
	free(c->immagine);
	free(c->scratch);
	free(c);
}
