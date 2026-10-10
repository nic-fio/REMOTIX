/*
 * 14-f1-forma.c — ⭐ THE ENCODED THEME AND THE DICTIONARY, without a desktop.
 *
 *   bash banchi/14-f1-forma.sh
 *
 * Phase 14, pointer shape, steps 1 and 2 (`src/forma.h`).  It compiles the
 * SAME sources as the product (`forma.c`, `cursore.c`, `registro.c`) and
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
 * The tests, each with its verdict (VERDE/ROSSO), and a ROSSO sets the exit:
 *   T1  the written theme: FORMA_QUANTE files, each a 1x1 opaque Xcursor, read back
 *       from disk and decoded by `forma_da_pixel` into its index;
 *   T2  the FORMA_QUANTE colours: distinct, far from black and white, and over all
 *       16 777 216 opaque colours the dictionary recognises EXACTLY that many;
 *   T3  the real theme: "ew-resize" and "sb_h_double_arrow" with the size and
 *       hotspot the Python parser reports;
 *   T3b the theme walk: with a `breeze_cursors` that HAS `size_hor` (Adwaita
 *       does not), "size_hor" must come from the ADWAITA alias (`ew-resize`) —
 *       `[M]` 24 Sep 2026 on the KDE box Breeze's one arrived instead;
 *   T4  the seam in `cursore.c`: a 1x1 metadata of the colour of "ew-resize"
 *       (and a 32x32 one of the same colour, "scaled") ⇒ delivers the REAL
 *       image; a real (non-uniform) bitmap passes as it is — the GNOME case;
 *   G1  fault: corrupted `index.theme` ⇒ `forma_immagine` FALSE, and the
 *       seam does NOT deliver the coloured pixel;
 *   G2  fault: empty themes folder ⇒ FALSE.
 */
#include "cursore.h"
#include "forma.h"

#include <spa/buffer/meta.h>
#include <spa/param/video/raw.h>

#include <glib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static int rossi;

static void verdetto(const char *prova, int buono, const char *cosa)
{
	printf("%-3s %s  %s\n", prova, buono ? "VERDE" : "ROSSO", cosa);
	if (!buono)
		rossi++;
}

static int indice_di(const char *nome)
{
	for (int i = 0; i < FORMA_QUANTE; i++)
		if (strcmp(forma_nome(i), nome) == 0)
			return i;
	return -1;
}

/* --- what the seam delivers --------------------------------------------- */
static int consegnate;
static CursoreForma ultima;
static uint8_t ultima_img[CURSORE_MAX_LATO * CURSORE_MAX_LATO * 4];

static int ricevi(void *chi, const CursoreForma *f)
{
	(void) chi;
	consegnate++;
	ultima = *f;
	if (f->immagine)
		memcpy(ultima_img, f->immagine, (size_t) f->larghezza * f->altezza * 4u);
	return 0;
}

/* A PipeWire metadata with a w x h bitmap all of one colour (BGRA). */
static size_t metadato(uint8_t *buf, uint32_t l, uint32_t a, const uint8_t *pixel_bgra,
                       const uint8_t *immagine)
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
		memcpy(px + k * 4, immagine ? immagine + k * 4 : pixel_bgra, 4);
	return sizeof *m + sizeof *b + (size_t) l * a * 4;
}

static void colore_di(int i, uint8_t bgra[4], const char *cartella_tema)
{
	g_autofree char *p = g_build_filename(cartella_tema, "cursors", forma_nome(i), NULL);
	g_autofree char *d = NULL;
	gsize n = 0;

	memset(bgra, 0, 4);
	if (g_file_get_contents(p, &d, &n, NULL) && n == 68)
		memcpy(bgra, d + 64, 4); /* the only pixel, ARGB little-endian = B G R A */
}

int main(int argc, char **argv)
{
	const char *lavoro, *temi, *guasti, *vuota, *misti;
	int attesa_l, attesa_a, attesa_x, attesa_y;
	static uint8_t buf[sizeof(struct spa_meta_cursor) + sizeof(struct spa_meta_bitmap) +
	                   64 * 64 * 4];

	if (argc != 10) {
		fprintf(stderr, "usage: %s work themes w h x y faulty-themes empty-themes mixed-themes\n",
		        argv[0]);
		return 2;
	}
	lavoro = argv[1];
	temi = argv[2];
	attesa_l = atoi(argv[3]);
	attesa_a = atoi(argv[4]);
	attesa_x = atoi(argv[5]);
	attesa_y = atoi(argv[6]);
	guasti = argv[7];
	vuota = argv[8];
	misti = argv[9];

	/* --- T1 ------------------------------------------------------------ */
	{
		g_autofree char *tema = g_build_filename(lavoro, "remotix", "icons", FORMA_TEMA, NULL);
		int scritto = forma_tema_scrivi(lavoro), giusti = 0;

		for (int i = 0; i < FORMA_QUANTE; i++) {
			uint8_t p[4];

			colore_di(i, p, tema);
			if (forma_da_pixel(p[0], p[1], p[2], p[3]) == i)
				giusti++;
			else
				printf("    ⛔ «%s»: pixel %02x%02x%02x%02x decoded %d\n", forma_nome(i),
				       p[3], p[2], p[1], p[0], forma_da_pixel(p[0], p[1], p[2], p[3]));
		}
		{
			char riga[128];

			snprintf(riga, sizeof riga, "theme written (%s), %d files of %d read back and decoded",
			         scritto ? "yes" : "NO", giusti, FORMA_QUANTE);
			verdetto("T1", scritto && giusti == FORMA_QUANTE, riga);
		}
	}

	/* --- T2 ------------------------------------------------------------ */
	{
		long riconosciuti = 0;
		int vicino = 0, distinti = 1, lontano = 255;
		uint32_t visti[FORMA_QUANTE];
		g_autofree char *tema = g_build_filename(lavoro, "remotix", "icons", FORMA_TEMA, NULL);

		for (int i = 0; i < FORMA_QUANTE; i++) {
			uint8_t p[4];
			int dn, db;

			colore_di(i, p, tema);
			visti[i] = (uint32_t) p[0] | (uint32_t) p[1] << 8 | (uint32_t) p[2] << 16;
			for (int k = 0; k < i; k++)
				if (visti[k] == visti[i])
					distinti = 0;
			/* the (Chebyshev) distance from black and from white */
			dn = MAX(MAX(p[0], p[1]), p[2]);
			db = MAX(MAX(255 - p[0], 255 - p[1]), 255 - p[2]);
			lontano = MIN(lontano, MIN(dn, db));
		}
		if (lontano < 0x40)
			vicino = 1;
		for (uint32_t c = 0; c < 0x1000000u; c++)
			if (forma_da_pixel(c & 0xFF, (c >> 8) & 0xFF, c >> 16, 0xFF) >= 0)
				riconosciuti++;
		for (int a = 0; a < 255; a++) /* ⛔ and with non-full alpha, NONE */
			if (forma_da_pixel(visti[0] & 0xFF, (visti[0] >> 8) & 0xFF, visti[0] >> 16,
			                   (uint8_t) a) >= 0)
				riconosciuti += 1000;
		{
			char riga[160];

			snprintf(riga, sizeof riga,
			         "distinct colours %s, minimum distance from black/white 0x%02x, recognised "
			         "%ld of 16M opaque (expected %d)",
			         distinti ? "yes" : "NO", lontano, riconosciuti, FORMA_QUANTE);
			verdetto("T2", distinti && !vicino && riconosciuti == FORMA_QUANTE, riga);
		}
	}

	/* --- T3 ------------------------------------------------------------ */
	forma_prova_cartella_temi(temi);
	{
		const char *nomi[] = { "ew-resize", "sb_h_double_arrow" };

		for (int k = 0; k < 2; k++) {
			CursoreForma f;
			int ok, uniforme = 1, trasparenti = 0, opachi = 0;
			char riga[200];

			memset(&f, 0, sizeof f);
			ok = forma_immagine(indice_di(nomi[k]), &f);
			for (int p = 0; ok && p < f.larghezza * f.altezza; p++) {
				if (memcmp(f.immagine + p * 4, f.immagine, 4))
					uniforme = 0;
				trasparenti += f.immagine[p * 4 + 3] == 0;
				opachi += f.immagine[p * 4 + 3] == 0xFF;
			}
			snprintf(riga, sizeof riga,
			         "«%s» from the real theme: %s, %ux%u hotspot %d,%d (expected %dx%d, %d,%d), "
			         "%d transparent pixels and %d opaque",
			         nomi[k], ok ? "loaded" : "NOT loaded", f.larghezza, f.altezza,
			         f.attivo_x, f.attivo_y, attesa_l, attesa_a, attesa_x, attesa_y,
			         trasparenti, opachi);
			verdetto("T3", ok && f.larghezza == attesa_l && f.altezza == attesa_a &&
			                   f.attivo_x == attesa_x && f.attivo_y == attesa_y && !uniforme &&
			                   trasparenti > 0 && opachi > 0,
			         riga);
		}
	}

	/* --- T3b ----------------------------------------------------------- */
	forma_prova_cartella_temi(misti);
	{
		CursoreForma sh, ew;
		int ok;

		memset(&sh, 0, sizeof sh);
		memset(&ew, 0, sizeof ew);
		ok = forma_immagine(indice_di("size_hor"), &sh) &&
		     forma_immagine(indice_di("ew-resize"), &ew) && sh.larghezza == ew.larghezza &&
		     sh.altezza == ew.altezza &&
		     memcmp(sh.immagine, ew.immagine, (size_t) ew.larghezza * ew.altezza * 4) == 0;
		verdetto("T3b", ok, "«size_hor» with a breeze_cursors that has it ⇒ the Adwaita "
		                    "alias (ew-resize), not the other theme's drawing");
	}
	forma_prova_cartella_temi(temi);

	/* --- T4 ------------------------------------------------------------ */
	{
		Cursore *c = cursore_apri(ricevi, NULL);
		int ew = indice_di("ew-resize"), tx = indice_di("text");
		uint8_t p[4];
		g_autofree char *tema = g_build_filename(lavoro, "remotix", "icons", FORMA_TEMA, NULL);
		CursoreForma vera;
		size_t n;
		int r, esito;
		char riga[200];

		cursore_mai_nascondere(c, "bench 14-f1: as on KDE");
		memset(&vera, 0, sizeof vera);
		forma_immagine(ew, &vera);

		colore_di(ew, p, tema);
		n = metadato(buf, 1, 1, p, NULL);
		r = cursore_metadato(c, buf, n);
		esito = r == 1 && consegnate == 1 && ultima.larghezza == vera.larghezza &&
		        ultima.altezza == vera.altezza && ultima.attivo_x == vera.attivo_x &&
		        memcmp(ultima_img, vera.immagine, (size_t) vera.larghezza * vera.altezza * 4) == 0;
		snprintf(riga, sizeof riga, "1x1 of the colour of «ew-resize» ⇒ delivered %ux%u hotspot %d,%d",
		         ultima.larghezza, ultima.altezza, ultima.attivo_x, ultima.attivo_y);
		verdetto("T4", esito, riga);

		/* the same colour in the next buffer: UNCHANGED, nothing new */
		r = cursore_metadato(c, buf, n);
		verdetto("T4", r == 0 && consegnate == 1, "same colour in the next buffer ⇒ nothing sent");

		/* "scaled": 32x32 of the same colour ⇒ the same shape, nothing sent */
		n = metadato(buf, 32, 32, p, NULL);
		r = cursore_metadato(c, buf, n);
		verdetto("T4", r == 0 && consegnate == 1, "uniform 32x32 of the same colour ⇒ unchanged");

		/* another encoded shape: the text I-beam */
		colore_di(tx, p, tema);
		n = metadato(buf, 1, 1, p, NULL);
		r = cursore_metadato(c, buf, n);
		snprintf(riga, sizeof riga, "1x1 of the colour of «text» ⇒ delivered %ux%u hotspot %d,%d",
		         ultima.larghezza, ultima.altezza, ultima.attivo_x, ultima.attivo_y);
		verdetto("T4", r == 1 && consegnate == 2 && ultima.larghezza > 1, riga);

		/* GNOME: a real bitmap passes as it is (they are Adwaita's own pixels) */
		n = metadato(buf, vera.larghezza, vera.altezza, NULL, vera.immagine);
		r = cursore_metadato(c, buf, n);
		verdetto("T4", r == 1 && consegnate == 3 &&
		                   memcmp(ultima_img, vera.immagine,
		                          (size_t) vera.larghezza * vera.altezza * 4) == 0,
		         "real bitmap (the GNOME case) ⇒ delivered as it is, the dictionary does not trigger");
		cursore_chiudi(c);
	}

	/* --- G1 and G2 ------------------------------------------------------ */
	{
		const char *cartelle[] = { guasti, vuota };
		const char *nomi[] = { "G1", "G2" };
		const char *cosa[] = { "corrupted index.theme", "themes absent" };

		for (int k = 0; k < 2; k++) {
			CursoreForma f;
			Cursore *c;
			uint8_t p[4];
			int caricate = 0, r;
			g_autofree char *tema =
				g_build_filename(lavoro, "remotix", "icons", FORMA_TEMA, NULL);
			char riga[200];

			forma_prova_cartella_temi(cartelle[k]);
			for (int i = 0; i < FORMA_QUANTE; i++) {
				memset(&f, 0, sizeof f);
				caricate += forma_immagine(i, &f);
			}
			consegnate = 0;
			c = cursore_apri(ricevi, NULL);
			cursore_mai_nascondere(c, "bench 14-f1: fault");
			colore_di(indice_di("ew-resize"), p, tema);
			r = cursore_metadato(c, buf, metadato(buf, 1, 1, p, NULL));
			snprintf(riga, sizeof riga,
			         "fault «%s»: shapes loaded %d (expected 0), delivered by the seam %d "
			         "(expected 0: the client keeps its arrow)",
			         cosa[k], caricate, consegnate);
			verdetto(nomi[k], caricate == 0 && consegnate == 0 && r == 0, riga);
			cursore_chiudi(c);
		}
	}

	printf("%s — %d red\n", rossi ? "⛔ ROSSO" : "⭐ VERDE", rossi);
	return rossi ? 1 : 0;
}
