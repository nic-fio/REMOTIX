/*
 * 14-f1-forma.c — ⭐ IL TEMA CODIFICATO E IL DIZIONARIO, senza desktop.
 *
 *   bash banchi/14-f1-forma.sh
 *
 * Fase 14, forma del puntatore, passi 1 e 2 (`src/forma.h`).  Compila gli
 * STESSI sorgenti del prodotto (`forma.c`, `cursore.c`, `registro.c`) e li
 * guida da fuori.  ⚠ Gira dove c'e' Adwaita (il portatile, le quattro scatole):
 * misura il modulo, NON che KWin mandi davvero il colore nel metadato — quello
 * e' la misura sulla scatola.
 *
 * ⛔ I VALORI ATTESI DEL TEMA REALE NON LI CALCOLA QUESTO FILE: li legge lo
 *    `.sh` con un parser Python suo e li passa in argomento.  Un parser che
 *    controlla se stesso direbbe sempre di si'.
 *
 *   argomenti: <cartella di lavoro> <cartella dei temi> <l> <a> <x> <y>
 *              <cartella dei temi GUASTA: indice corrotto> <cartella VUOTA>
 *              <cartella MISTA: Adwaita + un breeze_cursors finto con `size_hor`>
 *
 * Le prove, ognuna con il suo verdetto (VERDE/ROSSO), ed e' ROSSO l'uscita:
 *   T1  il tema scritto: FORMA_QUANTE file, ciascuno Xcursor 1x1 opaco, riletto dal
 *       disco e decodificato da `forma_da_pixel` nel suo indice;
 *   T2  i FORMA_QUANTE colori: distinti, lontani dal nero e dal bianco, e su tutti i
 *       16 777 216 colori opachi il dizionario ne riconosce ESATTAMENTE tanti;
 *   T3  il tema reale: «ew-resize» e «sb_h_double_arrow» con la misura e il
 *       punto attivo che dice il parser Python;
 *   T3b il giro dei temi: con un `breeze_cursors` che HA `size_hor` (Adwaita
 *       no), «size_hor» deve venire dall'alias di ADWAITA (`ew-resize`) —
 *       `[M]` 24 set 2026 sulla scatola KDE arrivava invece quella di Breeze;
 *   T4  la cucitura in `cursore.c`: un metadato 1x1 del colore di «ew-resize»
 *       (e uno 32x32 dello stesso colore, «scalato») ⇒ consegna l'immagine
 *       VERA; una bitmap vera (non uniforme) passa com'e' — il caso di GNOME;
 *   G1  guasto: `index.theme` corrotto ⇒ `forma_immagine` FALSE, e la
 *       cucitura NON consegna il pixel colorato;
 *   G2  guasto: cartella dei temi vuota ⇒ FALSE.
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

/* --- quel che la cucitura consegna -------------------------------------- */
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

/* Un metadato PipeWire con una bitmap l x a tutta di un colore (BGRA). */
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
		memcpy(bgra, d + 64, 4); /* l'unico pixel, ARGB little-endian = B G R A */
}

int main(int argc, char **argv)
{
	const char *lavoro, *temi, *guasti, *vuota, *misti;
	int attesa_l, attesa_a, attesa_x, attesa_y;
	static uint8_t buf[sizeof(struct spa_meta_cursor) + sizeof(struct spa_meta_bitmap) +
	                   64 * 64 * 4];

	if (argc != 10) {
		fprintf(stderr, "uso: %s lavoro temi l a x y temi-guasti temi-vuoti temi-misti\n",
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
				printf("    ⛔ «%s»: pixel %02x%02x%02x%02x decodificato %d\n", forma_nome(i),
				       p[3], p[2], p[1], p[0], forma_da_pixel(p[0], p[1], p[2], p[3]));
		}
		{
			char riga[128];

			snprintf(riga, sizeof riga, "tema scritto (%s), %d file su %d riletti e decodificati",
			         scritto ? "si'" : "NO", giusti, FORMA_QUANTE);
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
			/* la distanza (Chebyshev) dal nero e dal bianco */
			dn = MAX(MAX(p[0], p[1]), p[2]);
			db = MAX(MAX(255 - p[0], 255 - p[1]), 255 - p[2]);
			lontano = MIN(lontano, MIN(dn, db));
		}
		if (lontano < 0x40)
			vicino = 1;
		for (uint32_t c = 0; c < 0x1000000u; c++)
			if (forma_da_pixel(c & 0xFF, (c >> 8) & 0xFF, c >> 16, 0xFF) >= 0)
				riconosciuti++;
		for (int a = 0; a < 255; a++) /* ⛔ e con alfa non piena, NESSUNO */
			if (forma_da_pixel(visti[0] & 0xFF, (visti[0] >> 8) & 0xFF, visti[0] >> 16,
			                   (uint8_t) a) >= 0)
				riconosciuti += 1000;
		{
			char riga[160];

			snprintf(riga, sizeof riga,
			         "colori distinti %s, distanza minima da nero/bianco 0x%02x, riconosciuti "
			         "%ld su 16M opachi (attesi %d)",
			         distinti ? "si'" : "NO", lontano, riconosciuti, FORMA_QUANTE);
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
			         "«%s» dal tema reale: %s, %ux%u punto %d,%d (attesi %dx%d, %d,%d), "
			         "%d pixel trasparenti e %d opachi",
			         nomi[k], ok ? "caricata" : "NON caricata", f.larghezza, f.altezza,
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
		verdetto("T3b", ok, "«size_hor» con un breeze_cursors che ce l'ha ⇒ l'alias di "
		                    "Adwaita (ew-resize), non il disegno dell'altro tema");
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

		cursore_mai_nascondere(c, "banco 14-f1: come su KDE");
		memset(&vera, 0, sizeof vera);
		forma_immagine(ew, &vera);

		colore_di(ew, p, tema);
		n = metadato(buf, 1, 1, p, NULL);
		r = cursore_metadato(c, buf, n);
		esito = r == 1 && consegnate == 1 && ultima.larghezza == vera.larghezza &&
		        ultima.altezza == vera.altezza && ultima.attivo_x == vera.attivo_x &&
		        memcmp(ultima_img, vera.immagine, (size_t) vera.larghezza * vera.altezza * 4) == 0;
		snprintf(riga, sizeof riga, "1x1 del colore di «ew-resize» ⇒ consegnata %ux%u punto %d,%d",
		         ultima.larghezza, ultima.altezza, ultima.attivo_x, ultima.attivo_y);
		verdetto("T4", esito, riga);

		/* lo stesso colore al buffer dopo: INVARIATO, niente di nuovo */
		r = cursore_metadato(c, buf, n);
		verdetto("T4", r == 0 && consegnate == 1, "stesso colore al buffer dopo ⇒ nessun invio");

		/* «scalato»: 32x32 dello stesso colore ⇒ la stessa forma, nessun invio */
		n = metadato(buf, 32, 32, p, NULL);
		r = cursore_metadato(c, buf, n);
		verdetto("T4", r == 0 && consegnate == 1, "32x32 uniforme dello stesso colore ⇒ invariato");

		/* un'altra forma codificata: la I del testo */
		colore_di(tx, p, tema);
		n = metadato(buf, 1, 1, p, NULL);
		r = cursore_metadato(c, buf, n);
		snprintf(riga, sizeof riga, "1x1 del colore di «text» ⇒ consegnata %ux%u punto %d,%d",
		         ultima.larghezza, ultima.altezza, ultima.attivo_x, ultima.attivo_y);
		verdetto("T4", r == 1 && consegnate == 2 && ultima.larghezza > 1, riga);

		/* GNOME: una bitmap vera passa com'e' (sono i pixel di Adwaita stessi) */
		n = metadato(buf, vera.larghezza, vera.altezza, NULL, vera.immagine);
		r = cursore_metadato(c, buf, n);
		verdetto("T4", r == 1 && consegnate == 3 &&
		                   memcmp(ultima_img, vera.immagine,
		                          (size_t) vera.larghezza * vera.altezza * 4) == 0,
		         "bitmap vera (il caso di GNOME) ⇒ consegnata com'e', il dizionario non scatta");
		cursore_chiudi(c);
	}

	/* --- G1 e G2 -------------------------------------------------------- */
	{
		const char *cartelle[] = { guasti, vuota };
		const char *nomi[] = { "G1", "G2" };
		const char *cosa[] = { "index.theme corrotto", "temi assenti" };

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
			cursore_mai_nascondere(c, "banco 14-f1: guasto");
			colore_di(indice_di("ew-resize"), p, tema);
			r = cursore_metadato(c, buf, metadato(buf, 1, 1, p, NULL));
			snprintf(riga, sizeof riga,
			         "guasto «%s»: forme caricate %d (attese 0), consegnate dalla cucitura %d "
			         "(attese 0: il client tiene la sua freccia)",
			         cosa[k], caricate, consegnate);
			verdetto(nomi[k], caricate == 0 && consegnate == 0 && r == 0, riga);
			cursore_chiudi(c);
		}
	}

	printf("%s — %d rossi\n", rossi ? "⛔ ROSSO" : "⭐ VERDE", rossi);
	return rossi ? 1 : 0;
}
