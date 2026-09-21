/*
 * 13-w1 — il primo fotogramma tirato da wlroots, e la prova che sono i pixel
 *          giusti.
 *
 * ⛔ Si esegue DENTRO la sessione XFCE, come l'inquilino che la possiede: la
 *    cattura non ha cancelli su questa famiglia, ma l'uid sì
 *    (`/run/user/<uid>` è `drwx------`).
 *
 *   13-w1 [quanti] [attesa_s] [larghezza altezza]
 *   W1_STRADA=scheda 13-w1 …     ⭐ la strada della SCHEDA (21 set 2026)
 *
 * ⭐ Con `W1_STRADA=scheda` il fotogramma si prende in una lastra DMA-BUF nostra
 *    (`wlroots.c`, il riquadro della scheda), e il tempo per fotogramma è quello
 *    da mettere contro gli 8,8-14,9 ms della memoria (`fasi/13-xfce.md`).  ⛔ Il
 *    CONTENUTO si guarda lo stesso, mappando la lastra: un tempo bello su un
 *    fotogramma nero è il difetto che questo banco esiste per non dare verde.
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
#include <sys/mman.h>

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

/*
 * ⭐ La lastra della scheda, prestata alla CPU per guardarla.  ⛔ Col SYNC del
 *    DMA-BUF attorno (`wlr_lettura_cpu`), e la mappa si smonta con
 *    `presta_fine()`: il fotogramma `f` torna a non avere `pixel`.
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
	/* ⭐ Le due prove «a smentire» del porting sul fotogramma PENDENTE:
	 *   W1_RIPRENDI=1  una scadenza NON è un fotogramma perso: si richiama e
	 *                  si riprende lo stesso (è il ciclo del figlio con 8 ms);
	 *   W1_TIENI=1     la lastra di prima si tiene IN MANO mentre si prende la
	 *                  dopo, come il codificatore che non ha ancora finito, e
	 *                  si controlla che la dopo sia un'ALTRA lastra — più una
	 *                  resa doppia, che deve restare senza effetto. */
	bool riprendi = g_strcmp0(g_getenv("W1_RIPRENDI"), "1") == 0;
	bool tieni = g_strcmp0(g_getenv("W1_TIENI"), "1") == 0;
	int riprese = 0, stessa_lastra = 0;
	gint64 inizio_fotogramma = 0;

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
	if (scheda) {
		if (wlr_chiedi_la_scheda(palco, &sbaglio))
			printf("   ⭐ strada della SCHEDA accesa\n");
		else
			printf("   ⛔ strada della SCHEDA NEGATA: %s — si misura la MEMORIA, "
			       "e questa riga lo dice\n",
			       sbaglio->message);
		g_clear_error(&sbaglio);
	}

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
		gint64 prima;
		WlrEsito e;
		double ms;

		/* ⛔ La lastra di prima si RENDE prima di chiedere la dopo: è quel che
		 *    fa il prodotto (`cattura_fermo_libera()`), e un banco che le
		 *    tenesse tutte finirebbe le lastre e misurerebbe il suo difetto. */
		WlrFotogramma tenuto = f;

		if (ultima_in_mano && !tieni) {
			wlr_rendi(palco, f.lastra);
			ultima_in_mano = false;
		}
		prima = g_get_monotonic_time();
		if (!inizio_fotogramma)
			inizio_fotogramma = prima;
		e = wlr_fotogramma(palco, attesa, &f, &sbaglio);
		/* ⚠ Con la ripresa il tempo di un fotogramma è dalla PRIMA chiamata,
		 *   non dall'ultima: le scadenze sono dentro. */
		ms = (g_get_monotonic_time() - inizio_fotogramma) / 1000.0;

		/* ⚠ Con un tetto: un compositore muto non deve fermare il banco. */
		if (e == WLR_FOTOGRAMMA_SCADUTO && riprendi && riprese < quanti * 1000) {
			riprese++;
			g_clear_error(&sbaglio);
			i--;
			continue;
		}
		inizio_fotogramma = 0;
		if (tieni && ultima_in_mano) {
			/* ⛔ La lastra tenuta non deve essere quella appena riempita:
			 *    vorrebbe dire che labwc ci ha copiato dentro mentre era «in
			 *    mano».  Poi si rende DUE volte: la seconda non fa niente. */
			if (e == WLR_FOTOGRAMMA_PRESO && f.sulla_scheda && f.lastra == tenuto.lastra)
				stessa_lastra++;
			wlr_rendi(palco, tenuto.lastra);
			wlr_rendi(palco, tenuto.lastra);
			ultima_in_mano = false;
		}

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
			printf("   primo fotogramma: %ux%u stride %u formato %s%s — %s\n",
			       f.larghezza, f.altezza, f.stride, nome_formato(f.formato),
			       f.y_invertita ? " ⚠ Y INVERTITA" : "",
			       f.sulla_scheda ? (f.attesa_esplicita
			                             ? "sulla SCHEDA (lastra lineare, fence estratta)"
			                             : "sulla SCHEDA (⚠ senza fence: implicita)")
			                      : "in MEMORIA");
			printf("   ⭐ il CONTENUTO: %u colori distinti, %.1f%% dei campioni non "
			       "è nero\n",
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
	/* ⛔ La strada si dice ACCANTO al numero: un tempo senza la sua strada è
	 *    un tempo che mentirà. */
	printf("   strada: %d sulla SCHEDA, %d in MEMORIA", sulla_scheda, presi - sulla_scheda);
	if (sulla_scheda)
		printf(" — attesa della GPU dopo `ready` %.2f ms in media", attesa_gpu / sulla_scheda);
	printf("\n");
	if (riprendi)
		printf("   riprese dopo una scadenza: %d (il fotogramma PENDENTE)\n", riprese);
	if (tieni)
		printf("   lastra tenuta in mano e riempita di nuovo: %d %s\n", stessa_lastra,
		       stessa_lastra ? "⛔⛔ labwc ha scritto in una lastra IN MANO" : "⭐");

	wlr_chiudi(palco);

	if (stessa_lastra) {
		printf("\n  ⛔⛔ ROSSO — una lastra in mano è stata riusata %d volte\n", stessa_lastra);
		return 1;
	}
	if (presi != quanti) {
		printf("\n  ⛔⛔ ROSSO — %d fotogrammi su %d\n", presi, quanti);
		return 1;
	}
	printf("\n  ⭐ VERDE — %d fotogrammi su %d, tirati uno per uno\n", presi, quanti);
	return 0;
}
