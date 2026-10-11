/*
 * 14-f1-shape.c — ⭐ THE ENCODED THEME AND THE DICTIONARY, without a desktop.
 *
 *   bash benches/14-f1-shape.sh
 *
 * Phase 14, pointer shape, steps 1 and 2 (`src/shape.h`).  It compiles the
 * SAME sources as the product (`shape.c`, `cursor.c`, `log.c`) and
 * drives them from outside.  ⚠ It runs where Adwaita is (the laptop, the four
 * boxes): it measures the module, NOT that KWin really sends the colour in the
 * metadata — that is the measurement on the box.
 *
 * ⛔ THE EXPECTED VALUES OF THE REAL THEME ARE NOT COMPUTED BY THIS FILE: the
 *    `.sh` reads them with its own Python parser and passes them as arguments.
 *    A parser that checks itself would always say yes.
 *
 *   arguments: <working folder> <themes folder> <w> <h> <x> <y>
 *              <FAULTY themes folder: corrupted index> <EMPTY folder>
 *              <MIXED folder: Adwaita + a fake breeze_cursors with `size_hor`>
 *
 * The tests, each with its verdict (GREEN/RED), and a RED sets the exit:
 *   T1  the written theme: SHAPE_COUNT files, each a 1x1 opaque Xcursor, read back
 *       from disk and decoded by `shape_from_pixel` into its index;
 *   T2  the SHAPE_COUNT colours: distinct, far from black and white, and over all
 *       16 777 216 opaque colours the dictionary recognises EXACTLY that many;
 *   T3  the real theme: "ew-resize" and "sb_h_double_arrow" with the size and
 *       hotspot the Python parser reports;
 *   T3b the theme walk: with a `breeze_cursors` that HAS `size_hor` (Adwaita
 *       does not), "size_hor" must come from the ADWAITA alias (`ew-resize`) —
 *       `[M]` 24 Sep 2026 on the KDE box Breeze's one arrived instead;
 *   T4  the seam in `cursor.c`: a 1x1 metadata of the colour of "ew-resize"
 *       (and a 32x32 one of the same colour, "scaled") ⇒ delivers the REAL
 *       image; a real (non-uniform) bitmap passes as it is — the GNOME case;
 *   G1  fault: corrupted `index.theme` ⇒ `shape_image` FALSE, and the
 *       seam does NOT deliver the coloured pixel;
 *   G2  fault: empty themes folder ⇒ FALSE.
 */
#include "cursor.h"
#include "shape.h"

#include <spa/buffer/meta.h>
#include <spa/param/video/raw.h>

#include <glib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int rossi;

static void verdict(const char *prova, int good, const char *what)
{
	printf("%-3s %s  %s\n", prova, good ? "GREEN" : "RED", what);
	if (!good)
		rossi++;
}

static int index_of(const char *name)
{
	for (int i = 0; i < SHAPE_COUNT; i++)
		if (strcmp(shape_name(i), name) == 0)
			return i;
	return -1;
}

/* --- what the seam delivers --------------------------------------------- */
static int delivered;
static CursorShape latest;
static uint8_t last_img[CURSOR_MAX_SIDE * CURSOR_MAX_SIDE * 4];

static int receive(void *chi, const CursorShape *f)
{
	(void) chi;
	delivered++;
	latest = *f;
	if (f->bitmap)
		memcpy(last_img, f->bitmap, (size_t) f->width * f->height * 4u);
	return 0;
}

/* A PipeWire metadata with a w x h bitmap all of one colour (BGRA). */
static size_t metadata(uint8_t *buf, uint32_t l, uint32_t a, const uint8_t *pixel_bgra,
                       const uint8_t *bitmap)
{
	struct spa_meta_cursor *m = (void *) buf;
	struct spa_meta_bitmap *b = (void *) (buf + sizeof *m);
	uint8_t *px = buf + sizeof *m + sizeof *b;

	memset(buf, 0, sizeof *m + sizeof *b);
	m->id = 1;
	m->bitmap_offset = sizeof *m;
	b->format = SPA_VIDEO_FORMAT_BGRA;
	b->size.width = l;
	b->size.height = a;
	b->stride = (int32_t) (l * 4);
	b->offset = sizeof *b;
	for (uint32_t k = 0; k < l * a; k++)
		memcpy(px + k * 4, bitmap ? bitmap + k * 4 : pixel_bgra, 4);
	return sizeof *m + sizeof *b + (size_t) l * a * 4;
}

static void color_of(int i, uint8_t bgra[4], const char *theme_dir)
{
	g_autofree char *p = g_build_filename(theme_dir, "cursors", shape_name(i), NULL);
	g_autofree char *d = NULL;
	gsize n = 0;

	memset(bgra, 0, 4);
	if (g_file_get_contents(p, &d, &n, NULL) && n == 68)
		memcpy(bgra, d + 64, 4); /* the only pixel, ARGB little-endian = B G R A */
}

int main(int argc, char **argv)
{
	const char *work, *themes, *faults, *blank, *mixed;
	int want_w, want_h, want_x, want_y;
	static uint8_t buf[sizeof(struct spa_meta_cursor) + sizeof(struct spa_meta_bitmap) +
	                   64 * 64 * 4];

	if (argc != 10) {
		fprintf(stderr, "usage: %s work themes w h x y faulty-themes empty-themes mixed-themes\n",
		        argv[0]);
		return 2;
	}
	work = argv[1];
	themes = argv[2];
	want_w = atoi(argv[3]);
	want_h = atoi(argv[4]);
	want_x = atoi(argv[5]);
	want_y = atoi(argv[6]);
	faults = argv[7];
	blank = argv[8];
	mixed = argv[9];

	/* --- T1 ------------------------------------------------------------ */
	{
		g_autofree char *theme = g_build_filename(work, "remotix", "icons", SHAPE_THEME, NULL);
		int n_written = shape_theme_write(work), correct = 0;

		for (int i = 0; i < SHAPE_COUNT; i++) {
			uint8_t p[4];

			color_of(i, p, theme);
			if (shape_from_pixel(p[0], p[1], p[2], p[3]) == i)
				correct++;
			else
				printf("    ⛔ «%s»: pixel %02x%02x%02x%02x decoded %d\n", shape_name(i),
				       p[3], p[2], p[1], p[0], shape_from_pixel(p[0], p[1], p[2], p[3]));
		}
		{
			char line[128];

			snprintf(line, sizeof line, "theme written (%s), %d files of %d read back and decoded",
			         n_written ? "yes" : "NO", correct, SHAPE_COUNT);
			verdict("T1", n_written && correct == SHAPE_COUNT, line);
		}
	}

	/* --- T2 ------------------------------------------------------------ */
	{
		long recognized = 0;
		int near = 0, distinct = 1, far = 255;
		uint32_t seen_items[SHAPE_COUNT];
		g_autofree char *theme = g_build_filename(work, "remotix", "icons", SHAPE_THEME, NULL);

		for (int i = 0; i < SHAPE_COUNT; i++) {
			uint8_t p[4];
			int dn, db;

			color_of(i, p, theme);
			seen_items[i] = (uint32_t) p[0] | (uint32_t) p[1] << 8 | (uint32_t) p[2] << 16;
			for (int k = 0; k < i; k++)
				if (seen_items[k] == seen_items[i])
					distinct = 0;
			/* the (Chebyshev) distance from black and from white */
			dn = MAX(MAX(p[0], p[1]), p[2]);
			db = MAX(MAX(255 - p[0], 255 - p[1]), 255 - p[2]);
			far = MIN(far, MIN(dn, db));
		}
		if (far < 0x40)
			near = 1;
		for (uint32_t c = 0; c < 0x1000000u; c++)
			if (shape_from_pixel(c & 0xFF, (c >> 8) & 0xFF, c >> 16, 0xFF) >= 0)
				recognized++;
		for (int a = 0; a < 255; a++) /* ⛔ and with non-full alpha, NONE */
			if (shape_from_pixel(seen_items[0] & 0xFF, (seen_items[0] >> 8) & 0xFF, seen_items[0] >> 16,
			                   (uint8_t) a) >= 0)
				recognized += 1000;
		{
			char line[160];

			snprintf(line, sizeof line,
			         "distinct colours %s, minimum distance from black/white 0x%02x, recognised "
			         "%ld of 16M opaque (expected %d)",
			         distinct ? "yes" : "NO", far, recognized, SHAPE_COUNT);
			verdict("T2", distinct && !near && recognized == SHAPE_COUNT, line);
		}
	}

	/* --- T3 ------------------------------------------------------------ */
	shape_test_themes_folder(themes);
	{
		const char *names[] = { "ew-resize", "sb_h_double_arrow" };

		for (int k = 0; k < 2; k++) {
			CursorShape f;
			int ok, uniform = 1, transparent = 0, opaque = 0;
			char line[200];

			memset(&f, 0, sizeof f);
			ok = shape_image(index_of(names[k]), &f);
			for (int p = 0; ok && p < f.width * f.height; p++) {
				if (memcmp(f.bitmap + p * 4, f.bitmap, 4))
					uniform = 0;
				transparent += f.bitmap[p * 4 + 3] == 0;
				opaque += f.bitmap[p * 4 + 3] == 0xFF;
			}
			snprintf(line, sizeof line,
			         "«%s» from the real theme: %s, %ux%u hotspot %d,%d (expected %dx%d, %d,%d), "
			         "%d transparent pixels and %d opaque",
			         names[k], ok ? "loaded" : "NOT loaded", f.width, f.height,
			         f.active_x, f.active_y, want_w, want_h, want_x, want_y,
			         transparent, opaque);
			verdict("T3", ok && f.width == want_w && f.height == want_h &&
			                   f.active_x == want_x && f.active_y == want_y && !uniform &&
			                   transparent > 0 && opaque > 0,
			         line);
		}
	}

	/* --- T3b ----------------------------------------------------------- */
	shape_test_themes_folder(mixed);
	{
		CursorShape sh, ew;
		int ok;

		memset(&sh, 0, sizeof sh);
		memset(&ew, 0, sizeof ew);
		ok = shape_image(index_of("size_hor"), &sh) &&
		     shape_image(index_of("ew-resize"), &ew) && sh.width == ew.width &&
		     sh.height == ew.height &&
		     memcmp(sh.bitmap, ew.bitmap, (size_t) ew.width * ew.height * 4) == 0;
		verdict("T3b", ok, "«size_hor» with a breeze_cursors that has it ⇒ the Adwaita "
		                    "alias (ew-resize), not the other theme's drawing");
	}
	shape_test_themes_folder(themes);

	/* --- T4 ------------------------------------------------------------ */
	{
		Cursor *c = cursor_open(receive, NULL);
		int ew = index_of("ew-resize"), tx = index_of("text");
		uint8_t p[4];
		g_autofree char *theme = g_build_filename(work, "remotix", "icons", SHAPE_THEME, NULL);
		CursorShape real;
		size_t n;
		int r, outcome;
		char line[200];

		cursor_never_hide(c, "bench 14-f1: as on KDE");
		memset(&real, 0, sizeof real);
		shape_image(ew, &real);

		color_of(ew, p, theme);
		n = metadata(buf, 1, 1, p, NULL);
		r = cursor_metadata(c, buf, n);
		outcome = r == 1 && delivered == 1 && latest.width == real.width &&
		        latest.height == real.height && latest.active_x == real.active_x &&
		        memcmp(last_img, real.bitmap, (size_t) real.width * real.height * 4) == 0;
		snprintf(line, sizeof line, "1x1 of the colour of «ew-resize» ⇒ delivered %ux%u hotspot %d,%d",
		         latest.width, latest.height, latest.active_x, latest.active_y);
		verdict("T4", outcome, line);

		/* the same colour in the next buffer: UNCHANGED, nothing new */
		r = cursor_metadata(c, buf, n);
		verdict("T4", r == 0 && delivered == 1, "same colour in the next buffer ⇒ nothing sent");

		/* "scaled": 32x32 of the same colour ⇒ the same shape, nothing sent */
		n = metadata(buf, 32, 32, p, NULL);
		r = cursor_metadata(c, buf, n);
		verdict("T4", r == 0 && delivered == 1, "uniform 32x32 of the same colour ⇒ unchanged");

		/* another encoded shape: the text I-beam */
		color_of(tx, p, theme);
		n = metadata(buf, 1, 1, p, NULL);
		r = cursor_metadata(c, buf, n);
		snprintf(line, sizeof line, "1x1 of the colour of «text» ⇒ delivered %ux%u hotspot %d,%d",
		         latest.width, latest.height, latest.active_x, latest.active_y);
		verdict("T4", r == 1 && delivered == 2 && latest.width > 1, line);

		/* GNOME: a real bitmap passes as it is (they are Adwaita's own pixels) */
		n = metadata(buf, real.width, real.height, NULL, real.bitmap);
		r = cursor_metadata(c, buf, n);
		verdict("T4", r == 1 && delivered == 3 &&
		                   memcmp(last_img, real.bitmap,
		                          (size_t) real.width * real.height * 4) == 0,
		         "real bitmap (the GNOME case) ⇒ delivered as it is, the dictionary does not trigger");
		cursor_close(c);
	}

	/* --- G1 and G2 ------------------------------------------------------ */
	{
		const char *dirs[] = { faults, blank };
		const char *names[] = { "G1", "G2" };
		const char *what[] = { "corrupted index.theme", "themes absent" };

		for (int k = 0; k < 2; k++) {
			CursorShape f;
			Cursor *c;
			uint8_t p[4];
			int loaded = 0, r;
			g_autofree char *theme =
				g_build_filename(work, "remotix", "icons", SHAPE_THEME, NULL);
			char line[200];

			shape_test_themes_folder(dirs[k]);
			for (int i = 0; i < SHAPE_COUNT; i++) {
				memset(&f, 0, sizeof f);
				loaded += shape_image(i, &f);
			}
			delivered = 0;
			c = cursor_open(receive, NULL);
			cursor_never_hide(c, "bench 14-f1: fault");
			color_of(index_of("ew-resize"), p, theme);
			r = cursor_metadata(c, buf, metadata(buf, 1, 1, p, NULL));
			snprintf(line, sizeof line,
			         "fault «%s»: shapes loaded %d (expected 0), delivered by the seam %d "
			         "(expected 0: the client keeps its arrow)",
			         what[k], loaded, delivered);
			verdict(names[k], loaded == 0 && delivered == 0 && r == 0, line);
			cursor_close(c);
		}
	}

	printf("%s — %d red\n", rossi ? "⛔ ROSSO" : "⭐ VERDE", rossi);
	return rossi ? 1 : 0;
}
