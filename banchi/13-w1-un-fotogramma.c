/*
 * 13-w1 — il primo fotogramma tirato da wlroots, e la prova che sono i pixel
 *          giusti.
 *
 * ⛔ Si esegue DENTRO la sessione XFCE, come l'inquilino che la possiede: la
 *    cattura non ha cancelli su questa famiglia, ma l'uid sì
 *    (`/run/user/<uid>` è `drwx------`).
 *
 *   13-w1 [quanti] [attesa_s]
 *
 * Scrive l'ultimo fotogramma in `/tmp/13-w1.ppm` — ⚠ PPM e non PNG di
 * proposito: nessuna libreria in mezzo fra i byte del compositore e il file che
 * si guarda. Chi vuole un PNG lo fa con `ffmpeg`, fuori da qui, e se
 * l'immagine fosse sbagliata saprebbe che non è stata questa conversione.
 *
 * ⛔⛔ E IL GIUDIZIO NON È «il programma non è esploso».
 *
 *    Un fotogramma **nero** e un fotogramma **mai arrivato** hanno lo stesso
 *    aspetto in un conteggio, ed è la forma d'errore che questo progetto ha
 *    pagato più volte. ⇒ Qui si misura il CONTENUTO: quanti byte non sono
 *    zero, e quanti colori distinti ci sono. Uno schermo vero ne ha molti;
 *    uno schermo spento ne ha uno.
 */
#include "../src/wlroots.h"

#include <glib.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* ⚠ I due formati che wl_shm numera 0 e 1 invece che col fourcc. */
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
 * Quanti colori distinti, e quanti byte diversi da zero.
 *
 * ⛔ I colori si contano a campione (un pixel ogni 37, che è primo e non
 *    divide nessuna larghezza tonda): contarli tutti a 1080p costa più della
 *    cattura che si sta misurando, e falserebbe i tempi che questo banco
 *    riporta.
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
 * ⛔⛔ L'ORDINE DEI CANALI SI LEGGE DAL FOURCC, E NON SI GUARDA A OCCHIO.
 *
 * `[M]` 21 settembre 2026, e è costato un giro: la prima stesura scriveva
 * sempre `B G R` (l'ordine di XRGB8888), l'immagine è uscita con cartelle
 * **arancioni** e sembrava giusta — ⛔ ma labwc dichiara **XB24**, cioè
 * `XBGR8888`, che in memoria è `R G B X`. Le cartelle vere di Adwaita sono
 * **blu**: quel che sembrava conferma era lo scambio.
 *
 * ⇒ È la lezione di `LEZIONI.md` §1.9 nella sua forma peggiore: un controllo
 *   che dà un risultato **plausibile** non è un controllo. Qui il fatto si
 *   chiede al formato, che lo dice, invece di dedurlo da come appare.
 */
static void canali(uint32_t formato, int *ir, int *ig, int *ib)
{
	if (formato == DRM_XBGR8888 || formato == DRM_ABGR8888) {
		*ir = 0; *ig = 1; *ib = 2;   /* R G B X in memoria */
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
		/* ⛔ `y_invertita`: se il compositore dice che le righe vanno lette dal
		 *    basso, e non lo si fa, l'immagine esce capovolta — un guasto che
		 *    somiglia a un guasto del codificatore. */
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

int main(int argc, char **argv)
{
	int quanti = argc > 1 ? atoi(argv[1]) : 10;
	double attesa = argc > 2 ? atof(argv[2]) : 2.0;
	g_autoptr(GError) sbaglio = NULL;
	WlrPalco *palco;
	WlrFotogramma f;
	uint32_t l = 0, a = 0;
	gint64 primo_us = 0;
	int presi = 0;
	double peggiore = 0, totale = 0;

	printf("== 13-w1 — il primo fotogramma tirato da wlroots ==\n");
	printf("   %d fotogrammi, attesa %.1f s ciascuno\n\n", quanti, attesa);

	palco = wlr_apri(&sbaglio);
	if (!palco) {
		printf("  ⛔ non ho potuto aprire la cattura: %s\n", sbaglio->message);
		printf("\n  ⛔⛔ ROSSO\n");
		return 1;
	}
	wlr_misura(palco, &l, &a);
	printf("   uscita «%s», %ux%u\n", wlr_uscita_nome(palco), l, a);

	/*
	 * ⭐ LA MISURA, SE È STATA CHIESTA — e il giudizio lo dà la RILETTURA.
	 *
	 * ⛔ `DECISIONI.md` §5.0-sexies: chiedere la misura che l'uscita ha già
	 *    risponde «riuscito» senza mandare niente, e un serial vecchio risponde
	 *    «annullato» senza fare niente. ⇒ Qui non si guarda l'esito: si
	 *    richiede la misura e si confronta.
	 */
	if (argc > 4) {
		uint32_t vl = (uint32_t)atoi(argv[3]), va = (uint32_t)atoi(argv[4]);
		uint32_t dopo_l = 0, dopo_a = 0;
		WlrMisuraEsito e = wlr_misura_chiedi(palco, vl, va, 3.0, &sbaglio);

		wlr_misura(palco, &dopo_l, &dopo_a);
		printf("   misura chiesta %ux%u — esito della RICHIESTA: %s\n", vl, va,
		       e == WLR_MISURA_CHIESTA       ? "accettata"
		       : e == WLR_MISURA_GIA_COSI    ? "era già così"
		       : e == WLR_MISURA_RIFIUTATA   ? "rifiutata"
		       : e == WLR_MISURA_ANNULLATA   ? "annullata (serial vecchio)"
		                                     : "il compositore non sa cambiarla");
		g_clear_error(&sbaglio);
		if (dopo_l == vl && dopo_a == va)
			printf("   ⭐ e l'uscita RILETTA è %ux%u: la misura è cambiata davvero\n",
			       dopo_l, dopo_a);
		else
			printf("   ⛔ ma l'uscita RILETTA è %ux%u: NON è cambiata\n", dopo_l,
			       dopo_a);
		l = dopo_l;
		a = dopo_a;
	}

	for (int i = 0; i < quanti; i++) {
		gint64 prima = g_get_monotonic_time();
		WlrEsito e = wlr_fotogramma(palco, attesa, &f, &sbaglio);
		double ms = (g_get_monotonic_time() - prima) / 1000.0;

		if (e != WLR_FOTOGRAMMA_PRESO) {
			printf("  ⛔ fotogramma %d: %s — %s\n", i + 1,
			       e == WLR_FOTOGRAMMA_FALLITO  ? "il compositore ha detto NO"
			       : e == WLR_FOTOGRAMMA_SCADUTO ? "scaduto"
			                                     : "il filo è caduto",
			       sbaglio ? sbaglio->message : "senza motivo");
			g_clear_error(&sbaglio);
			continue;
		}
		presi++;
		totale += ms;
		if (ms > peggiore)
			peggiore = ms;
		if (i == 0) {
			guint colori = 0;
			double non_zero = 0;

			primo_us = g_get_monotonic_time();
			guarda_i_pixel(&f, &colori, &non_zero);
			printf("   primo fotogramma: %ux%u stride %u formato %s%s\n", f.larghezza,
			       f.altezza, f.stride, nome_formato(f.formato),
			       f.y_invertita ? " ⚠ Y INVERTITA" : "");
			printf("   ⭐ il CONTENUTO: %u colori distinti, %.1f%% dei campioni non "
			       "è nero\n",
			       colori, non_zero);
			(void)primo_us;
		}
	}

	if (presi) {
		guint colori = 0;
		double non_zero = 0;

		guarda_i_pixel(&f, &colori, &non_zero);
		scrivi_ppm(&f, "/tmp/13-w1.ppm");
		printf("\n   ultimo fotogramma: %u colori distinti, %.1f%% non nero "
		       "⇒ /tmp/13-w1.ppm\n",
		       colori, non_zero);
	}

	WlrConteggi c;

	wlr_conteggi(palco, &c);
	printf("\n   chiesti %" G_GUINT64_FORMAT " · presi %" G_GUINT64_FORMAT
	       " · falliti %" G_GUINT64_FORMAT " · scaduti %" G_GUINT64_FORMAT "\n",
	       c.chiesti, c.presi, c.falliti, c.scaduti);
	if (presi)
		printf("   tempo per fotogramma: %.1f ms in media, %.1f ms il peggiore\n",
		       totale / presi, peggiore);

	wlr_chiudi(palco);

	if (presi != quanti) {
		printf("\n  ⛔⛔ ROSSO — %d fotogrammi su %d\n", presi, quanti);
		return 1;
	}
	printf("\n  ⭐ VERDE — %d fotogrammi su %d, tirati uno per uno\n", presi, quanti);
	return 0;
}
