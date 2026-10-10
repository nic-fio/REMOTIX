/*
 * 13-w1 — the first frame pulled from wlroots, and the proof that they are the
 *          right pixels.
 *
 * ⛔ It runs INSIDE the XFCE session, as the tenant who owns it: capture has
 *    no gates on this family, but the uid does
 *    (`/run/user/<uid>` is `drwx------`).
 *
 *   13-w1 [count] [wait_s] [width height]
 *   W1_STRADA=scheda 13-w1 …     ⭐ the CARD route (21 Sep 2026)
 *
 * ⭐ With `W1_STRADA=scheda` the frame is taken into a DMA-BUF slab of ours
 *    (`wlroots.c`, the card section), and the time per frame is the one to set
 *    against the 8.8-14.9 ms of the memory route (`fasi/13-xfce.md`).  ⛔ The
 *    CONTENT is checked all the same, by mapping the slab: a nice time on a
 *    black frame is the defect this bench exists not to give green.
 *
 * It writes the last frame to `/tmp/13-w1.ppm` — ⚠ PPM and not PNG on
 * purpose: no library between the compositor's bytes and the file one looks
 * at. Whoever wants a PNG makes it with `ffmpeg`, outside of here, and if the
 * image were wrong they would know it was not this conversion.
 *
 * ⛔⛔ AND THE JUDGEMENT IS NOT "the program did not blow up".
 *
 *    A **black** frame and a frame that **never arrived** look the same in a
 *    count, and it is the error form this project has paid for several
 *    times. ⇒ Here the CONTENT is measured: how many bytes are not zero,
 *    and how many distinct colours there are. A real screen has many;
 *    a screen that is off has one.
 */
#include "../src/wlroots.h"

#include <glib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>

/* ⚠ The two formats that wl_shm numbers 0 and 1 instead of with the fourcc. */
#define WL_SHM_ARGB8888 0
#define WL_SHM_XRGB8888 1

#define FOURCC(a, b, c, d) ((uint32_t)(a) | ((uint32_t)(b) << 8) | ((uint32_t)(c) << 16) | \
                            ((uint32_t)(d) << 24))
#define DRM_XBGR8888 FOURCC('X', 'B', '2', '4')
#define DRM_ABGR8888 FOURCC('A', 'B', '2', '4')

static const char *nome_formato(uint32_t f)
{
	static char buf[8];

	if (f == WL_SHM_ARGB8888)
		return "ARGB8888";
	if (f == WL_SHM_XRGB8888)
		return "XRGB8888";
	memcpy(buf, &f, 4);
	buf[4] = 0;
	return buf;
}

/*
 * How many distinct colours, and how many bytes other than zero.
 *
 * ⛔ The colours are counted by sampling (one pixel every 37, which is prime
 *    and divides no round width): counting them all at 1080p costs more than
 *    the capture being measured, and would skew the times this bench
 *    reports.
 */
static void guarda_i_pixel(const WlrFotogramma *f, guint *colori, double *non_zero)
{
	GHashTable *visti = g_hash_table_new(g_direct_hash, g_direct_equal);
	gsize pixel_totali = (gsize)f->larghezza * f->altezza;
	gsize diversi = 0, guardati = 0;

	for (gsize y = 0; y < f->altezza; y++) {
		const uint8_t *riga = f->pixel + (gsize)y * f->stride;

		for (gsize x = 0; x < f->larghezza; x += 37) {
			uint32_t c = ((uint32_t)riga[x * 4 + 0]) | ((uint32_t)riga[x * 4 + 1] << 8) |
			             ((uint32_t)riga[x * 4 + 2] << 16);

			g_hash_table_add(visti, GUINT_TO_POINTER(c));
			if (c)
				diversi++;
			guardati++;
		}
	}
	*colori = g_hash_table_size(visti);
	*non_zero = guardati ? (double)diversi * 100.0 / guardati : 0.0;
	g_hash_table_destroy(visti);
	(void)pixel_totali;
}

/*
 * ⛔⛔ THE CHANNEL ORDER IS READ FROM THE FOURCC, AND NOT JUDGED BY EYE.
 *
 * `[M]` 21 Sep 2026, and it cost a round: the first draft always wrote
 * `B G R` (the order of XRGB8888), the image came out with **orange**
 * folders and looked right — ⛔ but labwc declares **XB24**, that is
 * `XBGR8888`, which in memory is `R G B X`. Adwaita's real folders are
 * **blue**: what looked like confirmation was the swap.
 *
 * ⇒ It is the lesson of `LEZIONI.md` §1.9 in its worst form: a check that
 *   gives a **plausible** result is not a check. Here the fact is asked of
 *   the format, which states it, instead of deduced from how it looks.
 */
static void canali(uint32_t formato, int *ir, int *ig, int *ib)
{
	if (formato == DRM_XBGR8888 || formato == DRM_ABGR8888) {
		*ir = 0; *ig = 1; *ib = 2;   /* R G B X in memory */
	} else {
		*ir = 2; *ig = 1; *ib = 0;   /* B G R X — XRGB/ARGB8888 */
	}
}

static bool scrivi_ppm(const WlrFotogramma *f, const char *dove)
{
	FILE *out = fopen(dove, "wb");
	int ir, ig, ib;

	canali(f->formato, &ir, &ig, &ib);
	if (!out)
		return false;
	fprintf(out, "P6\n%u %u\n255\n", f->larghezza, f->altezza);
	for (uint32_t y = 0; y < f->altezza; y++) {
		/* ⛔ `y_invertita`: if the compositor says the rows are to be read from
		 *    the bottom, and that is not done, the image comes out upside down —
		 *    a fault that looks like an encoder fault. */
		uint32_t vera = f->y_invertita ? (f->altezza - 1 - y) : y;
		const uint8_t *riga = f->pixel + (gsize)vera * f->stride;

		for (uint32_t x = 0; x < f->larghezza; x++) {
			fputc(riga[x * 4 + ir], out);
			fputc(riga[x * 4 + ig], out);
			fputc(riga[x * 4 + ib], out);
		}
	}
	fclose(out);
	return true;
}

/*
 * ⭐ The card slab, lent to the CPU to look at it.  ⛔ With the DMA-BUF SYNC
 *    around it (`wlr_lettura_cpu`), and the mapping is taken down with
 *    `presta_fine()`: frame `f` goes back to having no `pixel`.
 */
static void *presta_inizio(WlrFotogramma *f)
{
	void *m;

	if (!f->sulla_scheda)
		return NULL;
	m = mmap(NULL, f->offset + f->byte, PROT_READ, MAP_SHARED, f->fd, 0);
	if (m == MAP_FAILED)
		return NULL;
	wlr_lettura_cpu(f->fd, true);
	f->pixel = (const uint8_t *)m + f->offset;
	return m;
}

static void presta_fine(WlrFotogramma *f, void *m)
{
	if (!m)
		return;
	wlr_lettura_cpu(f->fd, false);
	munmap(m, f->offset + f->byte);
	f->pixel = NULL;
}

int main(int argc, char **argv)
{
	int quanti = argc > 1 ? atoi(argv[1]) : 10;
	double attesa = argc > 2 ? atof(argv[2]) : 2.0;
	g_autoptr(GError) sbaglio = NULL;
	WlrPalco *palco;
	WlrFotogramma f;
	uint32_t l = 0, a = 0;
	gint64 primo_us = 0;
	int presi = 0, sulla_scheda = 0;
	double peggiore = 0, totale = 0, attesa_gpu = 0;
	bool scheda = g_strcmp0(g_getenv("W1_STRADA"), "scheda") == 0;
	bool ultima_in_mano = false;
	/* ⭐ The two "refute it" tests of the port onto the PENDING frame:
	 *   W1_RIPRENDI=1  a timeout is NOT a lost frame: it is called again and
	 *                  the same one is resumed (it is the child's loop at 8 ms);
	 *   W1_TIENI=1     the previous slab is kept IN HAND while the next is
	 *                  taken, like the encoder that has not finished yet, and
	 *                  it is checked that the next is ANOTHER slab — plus a
	 *                  double return, which must stay without effect. */
	bool riprendi = g_strcmp0(g_getenv("W1_RIPRENDI"), "1") == 0;
	bool tieni = g_strcmp0(g_getenv("W1_TIENI"), "1") == 0;
	int riprese = 0, stessa_lastra = 0;
	gint64 inizio_fotogramma = 0;

	printf("== 13-w1 — the first frame pulled from wlroots ==\n");
	printf("   %d frames, wait %.1f s each\n\n", quanti, attesa);

	palco = wlr_apri(&sbaglio);
	if (!palco) {
		printf("  ⛔ could not open the capture: %s\n", sbaglio->message);
		printf("\n  ⛔⛔ ROSSO\n");
		return 1;
	}
	wlr_misura(palco, &l, &a);
	printf("   output «%s», %ux%u\n", wlr_uscita_nome(palco), l, a);
	if (scheda) {
		if (wlr_chiedi_la_scheda(palco, &sbaglio))
			printf("   ⭐ CARD route on\n");
		else
			printf("   ⛔ CARD route DENIED: %s — the MEMORY route is measured, "
			       "and this line says so\n",
			       sbaglio->message);
		g_clear_error(&sbaglio);
	}

	/*
	 * ⭐ THE SIZE, IF IT WAS ASKED FOR — and the judgement comes from READING IT BACK.
	 *
	 * ⛔ `DECISIONI.md` §5.0-sexies: asking for the size the output already has
	 *    answers "succeeded" without sending anything, and an old serial answers
	 *    "cancelled" without doing anything. ⇒ Here the outcome is not looked at:
	 *    the size is asked for again and compared.
	 */
	if (argc > 4) {
		uint32_t vl = (uint32_t)atoi(argv[3]), va = (uint32_t)atoi(argv[4]);
		uint32_t dopo_l = 0, dopo_a = 0;
		WlrMisuraEsito e = wlr_misura_chiedi(palco, vl, va, 3.0, &sbaglio);

		wlr_misura(palco, &dopo_l, &dopo_a);
		printf("   size asked %ux%u — outcome of the REQUEST: %s\n", vl, va,
		       e == WLR_MISURA_CHIESTA       ? "accepted"
		       : e == WLR_MISURA_GIA_COSI    ? "it already was"
		       : e == WLR_MISURA_RIFIUTATA   ? "refused"
		       : e == WLR_MISURA_ANNULLATA   ? "cancelled (old serial)"
		                                     : "the compositor cannot change it");
		g_clear_error(&sbaglio);
		if (dopo_l == vl && dopo_a == va)
			printf("   ⭐ and the output READ BACK is %ux%u: the size really changed\n",
			       dopo_l, dopo_a);
		else
			printf("   ⛔ but the output READ BACK is %ux%u: it did NOT change\n", dopo_l,
			       dopo_a);
		l = dopo_l;
		a = dopo_a;
	}

	for (int i = 0; i < quanti; i++) {
		gint64 prima;
		WlrEsito e;
		double ms;

		/* ⛔ The previous slab is RETURNED before asking for the next: it is what
		 *    the product does (`cattura_fermo_libera()`), and a bench that kept
		 *    them all would run out of slabs and measure its own defect. */
		WlrFotogramma tenuto = f;

		if (ultima_in_mano && !tieni) {
			wlr_rendi(palco, f.lastra);
			ultima_in_mano = false;
		}
		prima = g_get_monotonic_time();
		if (!inizio_fotogramma)
			inizio_fotogramma = prima;
		e = wlr_fotogramma(palco, attesa, &f, &sbaglio);
		/* ⚠ With resuming, the time of a frame is from the FIRST call,
		 *   not from the last: the timeouts are inside it. */
		ms = (g_get_monotonic_time() - inizio_fotogramma) / 1000.0;

		/* ⚠ With a ceiling: a mute compositor must not stop the bench. */
		if (e == WLR_FOTOGRAMMA_SCADUTO && riprendi && riprese < quanti * 1000) {
			riprese++;
			g_clear_error(&sbaglio);
			i--;
			continue;
		}
		inizio_fotogramma = 0;
		if (tieni && ultima_in_mano) {
			/* ⛔ The slab kept must not be the one just filled: it would
			 *    mean labwc copied into it while it was "in hand".  Then it is
			 *    returned TWICE: the second does nothing. */
			if (e == WLR_FOTOGRAMMA_PRESO && f.sulla_scheda && f.lastra == tenuto.lastra)
				stessa_lastra++;
			wlr_rendi(palco, tenuto.lastra);
			wlr_rendi(palco, tenuto.lastra);
			ultima_in_mano = false;
		}

		if (e != WLR_FOTOGRAMMA_PRESO) {
			printf("  ⛔ frame %d: %s — %s\n", i + 1,
			       e == WLR_FOTOGRAMMA_FALLITO  ? "the compositor said NO"
			       : e == WLR_FOTOGRAMMA_SCADUTO ? "timed out"
			                                     : "the wire dropped",
			       sbaglio ? sbaglio->message : "no reason");
			g_clear_error(&sbaglio);
			continue;
		}
		presi++;
		if (f.sulla_scheda) {
			sulla_scheda++;
			attesa_gpu += f.us_attesa_gpu / 1000.0;
			ultima_in_mano = true;
		}
		totale += ms;
		if (ms > peggiore)
			peggiore = ms;
		if (i == 0) {
			guint colori = 0;
			double non_zero = 0;

			void *m = presta_inizio(&f);

			primo_us = g_get_monotonic_time();
			if (f.pixel)
				guarda_i_pixel(&f, &colori, &non_zero);
			presta_fine(&f, m);
			printf("   first frame: %ux%u stride %u format %s%s — %s\n",
			       f.larghezza, f.altezza, f.stride, nome_formato(f.formato),
			       f.y_invertita ? " ⚠ Y INVERTED" : "",
			       f.sulla_scheda ? (f.attesa_esplicita
			                             ? "on the CARD (linear slab, fence extracted)"
			                             : "on the CARD (⚠ no fence: implicit)")
			                      : "in MEMORY");
			printf("   ⭐ the CONTENT: %u distinct colours, %.1f%% of the samples are not "
			       "black\n",
			       colori, non_zero);
			(void)primo_us;
		}
	}

	if (presi && (!f.sulla_scheda || ultima_in_mano)) {
		guint colori = 0;
		double non_zero = 0;
		void *m = presta_inizio(&f);

		if (f.pixel) {
			guarda_i_pixel(&f, &colori, &non_zero);
			scrivi_ppm(&f, "/tmp/13-w1.ppm");
		}
		presta_fine(&f, m);
		if (ultima_in_mano) {
			wlr_rendi(palco, f.lastra);
			ultima_in_mano = false;
		}
		printf("\n   last frame: %u distinct colours, %.1f%% not black "
		       "⇒ /tmp/13-w1.ppm\n",
		       colori, non_zero);
	}

	WlrConteggi c;

	wlr_conteggi(palco, &c);
	printf("\n   asked %" G_GUINT64_FORMAT " · taken %" G_GUINT64_FORMAT
	       " · failed %" G_GUINT64_FORMAT " · timed out %" G_GUINT64_FORMAT "\n",
	       c.chiesti, c.presi, c.falliti, c.scaduti);
	if (presi)
		printf("   time per frame: %.1f ms on average, %.1f ms the worst\n",
		       totale / presi, peggiore);
	/* ⛔ The route is stated NEXT TO the number: a time without its route is
	 *    a time that will lie. */
	printf("   route: %d on the CARD, %d in MEMORY", sulla_scheda, presi - sulla_scheda);
	if (sulla_scheda)
		printf(" — GPU wait after `ready` %.2f ms on average", attesa_gpu / sulla_scheda);
	printf("\n");
	if (riprendi)
		printf("   resumed after a timeout: %d (the PENDING frame)\n", riprese);
	if (tieni)
		printf("   slab kept in hand and filled again: %d %s\n", stessa_lastra,
		       stessa_lastra ? "⛔⛔ labwc wrote into a slab IN HAND" : "⭐");

	wlr_chiudi(palco);

	if (stessa_lastra) {
		printf("\n  ⛔⛔ ROSSO — a slab in hand was reused %d times\n", stessa_lastra);
		return 1;
	}
	if (presi != quanti) {
		printf("\n  ⛔⛔ ROSSO — %d frames of %d\n", presi, quanti);
		return 1;
	}
	printf("\n  ⭐ VERDE — %d frames of %d, pulled one by one\n", presi, quanti);
	return 0;
}
