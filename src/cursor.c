/*
 * cursor.c — from `struct spa_meta_cursor` (PipeWire) to `CursorShape` (RCP §7.2).
 *
 * ⛔ The contract is in `cursor.h`, which belongs to the coordinator: here it is
 *    IMPLEMENTED, the seam is not changed.  Whoever finds the contract wrong SAYS so
 *    and stops — does not work around it.
 *
 * ===========================================================================
 * ⛔ THE WORK THAT LIVES HERE AND NEITHER IN `capture.c` NOR IN `rcp.c`
 *
 * 1. **telling apart three states that the metadata merges into one**:
 *
 *      NOT RECEIVED    the metadata is not there at all ⇒ this function is not
 *                      even called, and `capture.c` COUNTS it.  Nothing leaves
 *                      on the wire: the client keeps its own pointer.
 *      HIDDEN          the pointer is there and must not be seen ⇒ `CURSOR_SHAPE`
 *                      with 0x0 and hotspot 0,0 (RCP §5.5).
 *      UNCHANGED       the metadata arrives with EVERY buffer, and is almost always
 *                      the same as before ⇒ nothing is sent.
 *
 * 2. enforcing the limits of RCP §7.2 **on this side**: beyond 256 nothing is
 *    sent, or the receiver closes the session with `PROTOCOL_ERROR` — that is,
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
#include "cursor.h"

#include "shape.h"
#include "log.h"

#include <spa/buffer/meta.h>
#include <spa/param/video/raw.h>

#include <inttypes.h>
#include <stdlib.h>
#include <string.h>

#define AREA "cursor"

/* The most bytes an image delivered on the wire can take. */
#define BYTE_MAX ((size_t) CURSOR_MAX_SIDE * (size_t) CURSOR_MAX_SIDE * 4u)

/* ⚠ A sanity ceiling BEFORE multiplying: an absurd size read from someone
 *   else's memory must not turn into a multiplication that overflows.  It is
 *   not the wire's limit (which is 256): it is the limit beyond which one declares
 *   "malformed" instead of "cut". */
#define ABSURD_SIDE 8192u

struct cursor
{
	CursorArrived when_changes;
	void *chi;

	uint32_t serial;

	int delivered; /* has anything been delivered yet?            */
	int hidden;   /* the last one delivered was 0x0               */
	int never_hide; /* §kde: the theme is invisible, see cursor.h  */
	int logged_never;      /* the log line is written only once           */

	/*
	 * The last known VISIBLE shape.  ⛔ It survives hiding on
	 * purpose: Mutter turns the pointer back on without resending the bitmap.
	 */
	int has_shape;
	uint16_t width, height;
	int16_t active_x, active_y;
	uint8_t *bitmap; /* the DELIVERED one: lives until the next call */
	uint8_t *scratch;  /* where the new one is turned around, so it can be COMPARED */
	size_t byte;

	/* The counts: they tell "has not changed" from "has not arrived"
	 * six hours later, and they are the number the bench compares with its own. */
	struct
	{
		uint64_t seen_items;        /* calls to cursor_metadata              */
		uint64_t id_zero;      /* the producer says "no cursor"          */
		uint64_t without_bitmap; /* id != 0 but bitmap_offset == 0         */
		uint64_t con_bitmap;   /* a bitmap was there                     */
		uint64_t blanks;        /* bitmap that means "hidden"             */
		uint64_t equal;       /* bitmap identical to the previous one   */
		uint64_t changes;        /* CursorShape delivered                 */
		uint64_t cut;     /* larger than 256: ⛔ fallback          */
		uint64_t hotspot_outside;  /* hotspot outside the image             */
		uint64_t malformed;
		uint64_t unknown_shape; /* visible, but we have never seen the shape */
		uint64_t refused;    /* the receiver said no                   */
		uint64_t encoded;   /* a colour of the encoded theme (shape.h) */
	} tally;

	int last_index;     /* the last encoded shape seen, for the log */

	/* The troubles said ONCE and not on every frame. */
	int logged_format;
	uint32_t seen_format;
	int logged_cut;
	int logged_point;
	int logged_unknown;
};

/* ------------------------------------------------------------------ *
 *  Delivery
 * ------------------------------------------------------------------ */

static int delivery(Cursor *c, const CursorShape *shape)
{
	int outcome;

	c->tally.changes++;
	c->delivered = 1;
	if (!c->when_changes)
		return 1;
	outcome = c->when_changes(c->chi, shape);
	if (outcome < 0)
	{
		c->tally.refused++;
		registro_dice(AREA, "⛔ the receiver REFUSED shape %ux%u (series %u): it was not sent",
		              (unsigned) shape->width, (unsigned) shape->height,
		              (unsigned) shape->serial);
		return -1;
	}
	return 1;
}

/*
 * ⛔ HIDDEN IS A STATE, NOT AN ABSENCE: 0x0 with hotspot 0,0 is sent
 *    (RCP §5.5), and sent ONCE only — not on every buffer in which the
 *    pointer is still not there.
 */
static int delivery_hidden(Cursor *c, const char *reason)
{
	CursorShape shape;

	if (c->never_hide) {
		if (!c->logged_never) {
			c->logged_never = 1;
			registro_dice(AREA,
			              "the pointer would be HIDDEN (%s) and I do NOT deliver it: on "
			              "this desktop the cursor theme is invisible on purpose, and "
			              "the viewer must keep their own pointer (cursor.h)",
			              reason);
		}
		return 0;
	}
	if (c->delivered && c->hidden)
		return 0;

	c->serial++;
	c->hidden = 1;

	memset(&shape, 0, sizeof shape);
	shape.serial = c->serial;
	shape.bitmap = NULL;

	registro_dice(AREA, "the pointer HIDES (%s) — CURSOR_SHAPE 0x0, series %u", reason,
	              (unsigned) c->serial);
	return delivery(c, &shape);
}

/* The pointer returns and Mutter does not resend the bitmap: the last known one is resent. */
static int delivery_shape_kept(Cursor *c)
{
	CursorShape shape;

	c->serial++;
	c->hidden = 0;

	memset(&shape, 0, sizeof shape);
	shape.width = c->width;
	shape.height = c->height;
	shape.active_x = c->active_x;
	shape.active_y = c->active_y;
	shape.serial = c->serial;
	shape.bitmap = c->bitmap;

	registro_dice(AREA,
	              "the pointer RETURNS and Mutter does not resend the shape: the last known one "
	              "is resent (%ux%u, series %u)",
	              (unsigned) c->width, (unsigned) c->height, (unsigned) c->serial);
	return delivery(c, &shape);
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
static int cursor_byte_order(uint32_t fmt, int *alpha_full)
{
	*alpha_full = 0;
	switch (fmt)
	{
	case SPA_VIDEO_FORMAT_RGBA:
		return 1;
	case SPA_VIDEO_FORMAT_BGRA:
		return 0;
	case SPA_VIDEO_FORMAT_RGBx:
		*alpha_full = 1;
		return 1;
	case SPA_VIDEO_FORMAT_BGRx:
		*alpha_full = 1;
		return 0;
	default:
		return -1;
	}
}

/* ------------------------------------------------------------------ *
 *  The calls
 * ------------------------------------------------------------------ */

Cursor *cursor_open(CursorArrived when_changes, void *chi)
{
	Cursor *c = calloc(1, sizeof *c);

	if (!c)
		return NULL;
	c->bitmap = malloc(BYTE_MAX);
	c->scratch = malloc(BYTE_MAX);
	if (!c->bitmap || !c->scratch)
	{
		free(c->bitmap);
		free(c->scratch);
		free(c);
		return NULL;
	}
	c->when_changes = when_changes;
	c->chi = chi;
	c->last_index = -1;
	return c;
}

int cursor_metadata(Cursor *c, const void *spa_meta_cursor, size_t size)
{
	const struct spa_meta_cursor *m = spa_meta_cursor;
	const struct spa_meta_bitmap *b;
	const uint8_t *base = spa_meta_cursor;
	size_t pixel_start, needed, byte;
	uint32_t source_w, source_h;
	uint16_t width, height;
	int16_t active_x, active_y;
	int invert, alpha_full;
	uint32_t y;
	uint8_t *swap;
	CursorShape shape;

	if (!c)
		return -1;
	c->tally.seen_items++;

	/*
	 * ⛔ "Too short" is NOT "hidden": it is metadata that cannot be
	 *    read, and it is declared instead of producing a cursor made of someone
	 *    else's memory — which is exactly the defect RCP §7.2 names.
	 */
	if (!m || size < sizeof *m)
	{
		c->tally.malformed++;
		registro_dice(AREA, "⛔ cursor metadata too short: %zu bytes, %zu needed",
		              size, sizeof *m);
		return -1;
	}

	/* --- 1. the producer says "no cursor" ------------------------------ */
	if (!spa_meta_cursor_is_valid(m))
	{
		c->tally.id_zero++;
		return delivery_hidden(c, "id = 0");
	}

	/* --- 2. the shape has not changed ----------------------------------- */
	if (m->bitmap_offset == 0)
	{
		c->tally.without_bitmap++;
		if (!c->hidden && c->delivered)
			return 0;
		if (c->has_shape)
			return delivery_shape_kept(c);
		/*
		 * ⛔ The pointer is there and we have NEVER seen its shape: it is not
		 *    "hidden" and not "unchanged".  Nothing is invented — it is
		 *    declared and the first bitmap is awaited.
		 */
		c->tally.unknown_shape++;
		if (!c->logged_unknown)
		{
			c->logged_unknown = 1;
			registro_dice(AREA,
			              "⚠ the pointer is visible but its shape has not arrived yet "
			              "(position only): nothing to send, waiting");
		}
		return 0;
	}

	/* --- 3. there is a bitmap: first check that it fits ---------------- */
	if (m->bitmap_offset < sizeof *m || m->bitmap_offset > size ||
	    size - m->bitmap_offset < sizeof *b)
	{
		c->tally.malformed++;
		registro_dice(AREA, "⛔ bitmap_offset %u outside the metadata (%zu bytes): discarded",
		              (unsigned) m->bitmap_offset, size);
		return -1;
	}
	b = (const struct spa_meta_bitmap *) (base + m->bitmap_offset);
	c->tally.con_bitmap++;

	/*
	 * --- 4. the bitmap that means "hidden" ------------------------------
	 * See the box at the top: on Mutter it is `set_empty_cursor_sprite_metadata`,
	 * which zeroes everything.  `offset == 0` is the same thing said by
	 * `spa/buffer/meta.h`: "no image data (invisible)".
	 */
	if (b->format == 0 || b->offset == 0 || b->size.width == 0 || b->size.height == 0)
	{
		c->tally.blanks++;
		return delivery_hidden(c, "empty bitmap (the pointer has no image)");
	}

	source_w = b->size.width;
	source_h = b->size.height;
	if (source_w > ABSURD_SIDE || source_h > ABSURD_SIDE || b->stride <= 0 ||
	    (uint32_t) b->stride < source_w * 4u || b->offset < sizeof *b)
	{
		c->tally.malformed++;
		registro_dice(AREA, "⛔ bitmap cannot be interpreted: %ux%u, stride %d, offset %u",
		              (unsigned) source_w, (unsigned) source_h, (int) b->stride,
		              (unsigned) b->offset);
		return -1;
	}

	pixel_start = (size_t) m->bitmap_offset + (size_t) b->offset;
	needed = (size_t) b->stride * (size_t) (source_h - 1) + (size_t) source_w * 4u;
	if (pixel_start > size || size - pixel_start < needed)
	{
		c->tally.malformed++;
		registro_dice(AREA,
		              "⛔ the cursor pixels do not fit: %zu bytes needed from %zu, the metadata "
		              "has %zu",
		              needed, pixel_start, size);
		return -1;
	}

	invert = cursor_byte_order(b->format, &alpha_full);
	if (invert < 0)
	{
		c->tally.malformed++;
		if (!c->logged_format || c->seen_format != b->format)
		{
			c->logged_format = 1;
			c->seen_format = b->format;
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
	 * Beyond 256 the receiver closes the session with `PROTOCOL_ERROR`: it is
	 * our defect that drops the client.  ⇒ It is CUT (the verb is
	 * `cursor.h`'s), and ⛔ the fallback is DECLARED — `CODER.md` §4.2.
	 *
	 * ⚠ The cut keeps the top-left corner, which is where every cursor's drawing
	 *   is and where the hotspot is.  Whether it is the right choice is
	 *   `[?]`: it has never been seen to trigger (Mutter allocates the metadata for
	 *   384x384, but GNOME themes go up to 64-96).  If one day it really
	 *   triggered, the thing to measure is whether **downsampling** is better instead.
	 */
	width = source_w > CURSOR_MAX_SIDE ? (uint16_t) CURSOR_MAX_SIDE : (uint16_t) source_w;
	height = source_h > CURSOR_MAX_SIDE ? (uint16_t) CURSOR_MAX_SIDE : (uint16_t) source_h;
	if (width != source_w || height != source_h)
	{
		c->tally.cut++;
		if (!c->logged_cut)
		{
			c->logged_cut = 1;
			registro_dice(AREA,
			              "⛔ FALLBACK: the cursor is %ux%u, the wire stops at %u (RCP §7.2) — "
			              "sending the %ux%u corner",
			              (unsigned) source_w, (unsigned) source_h,
			              (unsigned) CURSOR_MAX_SIDE, (unsigned) width, (unsigned) height);
		}
	}

	/*
	 * ⛔ AND THE HOTSPOT MUST LIE INSIDE THE IMAGE (RCP §5.5), or the
	 *    receiver closes.  If outside it is brought back inside, and declared.
	 */
	if (m->hotspot.x < 0 || m->hotspot.x >= (int32_t) width || m->hotspot.y < 0 ||
	    m->hotspot.y >= (int32_t) height)
	{
		c->tally.hotspot_outside++;
		if (!c->logged_point)
		{
			c->logged_point = 1;
			registro_dice(AREA,
			              "⛔ FALLBACK: hotspot %d,%d outside %ux%u — brought back inside "
			              "(RCP §5.5)",
			              (int) m->hotspot.x, (int) m->hotspot.y, (unsigned) width,
			              (unsigned) height);
		}
		active_x = m->hotspot.x < 0
		               ? 0
		               : (m->hotspot.x >= (int32_t) width ? (int16_t) (width - 1)
		                                                      : (int16_t) m->hotspot.x);
		active_y = m->hotspot.y < 0
		               ? 0
		               : (m->hotspot.y >= (int32_t) height ? (int16_t) (height - 1)
		                                                    : (int16_t) m->hotspot.y);
	}
	else
	{
		active_x = (int16_t) m->hotspot.x;
		active_y = (int16_t) m->hotspot.y;
	}

	/* --- 6. the bytes, turned around row by row in the work buffer ------ */
	byte = (size_t) width * (size_t) height * 4u;
	for (y = 0; y < height; y++)
	{
		const uint8_t *line = base + pixel_start + (size_t) y * (size_t) b->stride;
		uint8_t *report = c->scratch + (size_t) y * (size_t) width * 4u;
		uint32_t x;

		if (!invert && !alpha_full)
		{
			memcpy(report, line, (size_t) width * 4u);
			continue;
		}
		for (x = 0; x < width; x++)
		{
			uint8_t r0 = line[x * 4 + 0], r1 = line[x * 4 + 1];
			uint8_t r2 = line[x * 4 + 2], r3 = line[x * 4 + 3];

			report[x * 4 + 0] = invert ? r2 : r0;
			report[x * 4 + 1] = r1;
			report[x * 4 + 2] = invert ? r0 : r2;
			report[x * 4 + 3] = alpha_full ? 0xFF : r3;
		}
	}

	/*
	 * --- 6-bis. ⛔⭐ ALL TRANSPARENT MEANS "HIDDEN" — 20 Sep 2026.
	 *
	 * ⛔ `[M]` The user's test on KDE: to remove the cursor KWin draws
	 *    INSIDE the image (`--virtual` backend) the session starts with
	 *    a theme of 1x1 shapes with zero alpha (`session.c`,
	 *    `scrivi_tema_cursore_kde`).  ⇒ That theme also arrives HERE, in the
	 *    metadata, and the client dressed itself in an invisible shape: **no
	 *    pointer**, which is worse than two.
	 * ⭐ An image in which no pixel is visible is NOT a shape: it is the same
	 *    fact §5.5 calls "hidden", said with more bytes.  ⇒ `0x0` is
	 *    delivered, and the client puts up ITS OWN pointer (`page.html`,
	 *    `forma_vuota`).
	 * ⚠ And the work buffer is checked AFTER the conversion: `alpha_full`
	 *   fills the alpha, and a bitmap without an alpha channel is not transparent.
	 *
	 * ⭐⭐ PHASE 14, 24 Sep 2026 — FIRST OF ALL, THE ENCODED THEME (`shape.h`).
	 *      The session theme is no longer transparent: every shape is an
	 *      OPAQUE pixel of its own colour.  ⇒ If the WHOLE bitmap is of a single
	 *      colour and the dictionary recognises it (1x1, or scaled by the compositor:
	 *      a single colour stays a single colour), that is not the shape to
	 *      send — it is the NAME of the shape.  The REAL image taken from the real
	 *      theme is put into the work buffer, and we go on to the comparison
	 *      of step 7 as for any bitmap.
	 * ⛔ If the real theme is missing (`shape_image` FALSE, already said in the
	 *    log) we fall through to the check below, which on an opaque pixel does NOT
	 *    trigger: the client would receive the coloured pixel.  ⇒ In that case it
	 *    is treated like the invisible theme of before — "hidden", that is, with
	 *    `never_hide` the client keeps ITS OWN arrow, as until yesterday.
	 * ⭐ `[R]` GNOME DOES NOT COME THIS WAY: in the GNOME branch `session.c` sets
	 *    no `XCURSOR_*`, and Mutter sends the bitmap of its theme (Adwaita),
	 *    made of black, white and shades — never all of one colour, and the
	 *    red of ours (0x40-0x83) with exact green and blue is not an Adwaita
	 *    colour.  Only KDE (KWin, zkde metadata, mode 4) reads our theme
	 *    and then arrives here; labwc has its own road (`wlroots.c`).
	 */
	{
		size_t i;
		int idx = shape_from_pixel(c->scratch[0], c->scratch[1], c->scratch[2],
		                            c->scratch[3]);

		for (i = 4; idx >= 0 && i < byte; i += 4)
			if (memcmp(c->scratch + i, c->scratch, 4) != 0)
				idx = -1;
		if (idx >= 0) {
			CursorShape real;

			c->tally.encoded++;
			memset(&real, 0, sizeof real);
			if (!shape_image(idx, &real)) {
				c->tally.blanks++;
				return delivery_hidden(c, "encoded shape but real theme missing");
			}
			width = real.width;
			height = real.height;
			active_x = real.active_x;
			active_y = real.active_y;
			byte = (size_t) width * (size_t) height * 4u;
			memcpy(c->scratch, real.bitmap, byte);
			if (idx != c->last_index) {
				c->last_index = idx;
				/* ⚠ One line per shape CHANGE, not per buffer: it is the pace of
				 *   the hand of whoever uses the desktop, and the proof that the
				 *   dictionary works can only be read here. */
				registro_dice(AREA, "encoded shape %d «%s» ⇒ %ux%u, hotspot %d,%d",
				              idx, shape_name(idx), (unsigned) width,
				              (unsigned) height, (int) active_x, (int) active_y);
			}
			goto comparison;
		}
	}
	{
		size_t i;
		int is_visible = 0;

		for (i = 3; i < byte; i += 4)
			if (c->scratch[i]) {
				is_visible = 1;
				break;
			}
		if (!is_visible) {
			c->tally.blanks++;
			return delivery_hidden(c, "all pixels transparent (the cursor "
			                            "theme is invisible: the client draws it)");
		}
	}

comparison:
	/*
	 * --- 7. ⛔ HAS IT REALLY CHANGED? -----------------------------------
	 *
	 * The metadata arrives with EVERY buffer.  Without this comparison the same
	 * image would be resent a thousand times — which is the reason this module
	 * exists (`cursor.h`).  ⇒ the new bytes are turned around in the work buffer,
	 * COMPARED with the delivered ones, and only if they differ are the two
	 * buckets swapped (so the delivered image stays valid until the next
	 * call, as `cursor.h` promises).
	 *
	 * ⚠ And the comparison is with the last **delivered** one: after a hide the
	 *   client has nothing left to draw, so the same shape must be
	 *   resent even if identical.
	 */
	if (!c->hidden && c->delivered && c->has_shape && c->width == width &&
	    c->height == height && c->active_x == active_x && c->active_y == active_y &&
	    c->byte == byte && memcmp(c->bitmap, c->scratch, byte) == 0)
	{
		c->tally.equal++;
		return 0;
	}

	swap = c->bitmap;
	c->bitmap = c->scratch;
	c->scratch = swap;

	c->width = width;
	c->height = height;
	c->active_x = active_x;
	c->active_y = active_y;
	c->byte = byte;
	c->has_shape = 1;
	c->hidden = 0;
	c->serial++;

	memset(&shape, 0, sizeof shape);
	shape.width = width;
	shape.height = height;
	shape.active_x = active_x;
	shape.active_y = active_y;
	shape.serial = c->serial;
	shape.bitmap = c->bitmap;

	return delivery(c, &shape);
}

void cursor_never_hide(Cursor *c, const char *why)
{
	if (!c || c->never_hide)
		return;
	c->never_hide = 1;
	registro_dice(AREA, "pointer hiding will NOT be delivered any more: %s",
	              why ? why : "no reason given");
	/* ⭐ PHASE 14 — and the dictionary is loaded NOW, outside the PipeWire
	 *    thread: it is 68 files of the real theme read from disk, and doing it at
	 *    the first encoded shape would mean doing it on the real-time thread
	 *    of the capture.  ⚠ It is called only on KDE (the one using the encoded theme
	 *    with the metadata), so GNOME does not pay for this read. */
	{
		CursorShape before;

		memset(&before, 0, sizeof before);
		(void) shape_image(0, &before);
	}
}

void cursor_close(Cursor *c)
{
	if (!c)
		return;
	registro_dice(AREA,
	              "metadata %" PRIu64 ": id=0 %" PRIu64 ", position only %" PRIu64
	              ", with bitmap %" PRIu64 " (identical %" PRIu64 ", empty %" PRIu64
	              ") ⇒ CURSOR_SHAPE delivered %" PRIu64 "; cut %" PRIu64
	              ", hotspot outside %" PRIu64 ", malformed %" PRIu64 ", refused %" PRIu64
	              ", unknown shape %" PRIu64 ", encoded %" PRIu64,
	              c->tally.seen_items, c->tally.id_zero, c->tally.without_bitmap, c->tally.con_bitmap,
	              c->tally.equal, c->tally.blanks, c->tally.changes, c->tally.cut,
	              c->tally.hotspot_outside, c->tally.malformed, c->tally.refused,
	              c->tally.unknown_shape, c->tally.encoded);
	free(c->bitmap);
	free(c->scratch);
	free(c);
}
