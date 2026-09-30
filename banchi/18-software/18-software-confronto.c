/*
 * 18-software-confronto.c — fase 18, linea V-software: il ripiego in software
 * VECCHIO (libavcodec libx264/libsvtav1 + sws_scale, con le opzioni di
 * `codificatore.c`) contro il NUOVO (`src/ripiego.c`: OpenH264, SVT-AV1 diretta,
 * `src/colori709.c`), sulla STESSA sequenza di immagini di desktop.
 *
 * Modi:
 *   colori   L A DIR N              nostro contro sws_scale (tempo e scarto), e
 *                                   libyuv ARGBToI420 (BT.601) per riferimento
 *   sorgente L A DIR N uscita.raw    scrive la sequenza in bgr0 (per ffmpeg)
 *   codifica CODEC STRADA L A DIR N uscita [CHIAVE_A]
 *            CODEC = h264|av1 · STRADA = vecchia|nuova
 *            scrive uscita (.h264 Annex B / .obu) e uscita.csv (un fotogramma
 *            per riga: n, byte, chiave, us_conversione, us_codifica)
 *   eventi   CODEC STRADA L A DIR uscita
 *            chiave su richiesta, cambio di qualita' a caldo, cambio di misura:
 *            i tempi di ognuno e il flusso da far decodificare a ffmpeg
 *   rifiuti                          quel che il nuovo NON fa, detto
 *
 * La scena (in unita' 1080p, scalata per L/1920): lo sfondo vero di LXQt
 * (`l1.png` della macchina di prova), una finestra d'editor con codice vero
 * che SCORRE (fotogrammi 0-59, una riga per fotogramma), poi la finestra
 * TRASCINATA (60-89, 12 px per fotogramma), poi si SCRIVE (90-119: un carattere
 * per fotogramma e il cursore che lampeggia).
 */
#include "../../src/colori709.h"
#include "../../src/ripiego.h"

#include <inttypes.h>
#include <limits.h>
#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <libavcodec/avcodec.h>
#include <libavutil/opt.h>
#include <libswscale/swscale.h>
#include <libyuv/convert_from_argb.h>

static uint64_t ora_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t) t.tv_sec * 1000000u + (uint64_t) t.tv_nsec / 1000u;
}

/* il nome della strada per le righe: vecchia · corretta · nuova */
static const char *strada = "?";

static void muori(const char *m)
{
	fprintf(stderr, "⛔ %s\n", m);
	exit(1);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * LA SCENA
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct {
	uint32_t l, a;
	uint8_t *sfondo;      /* l x a bgr0 */
	uint8_t *doc;         /* dl x da bgr0 */
	uint32_t dl, da;
	uint8_t *quadro;      /* il fotogramma composto */
} Scena;

static uint8_t *leggi(const char *percorso, size_t attesi)
{
	FILE *f = fopen(percorso, "rb");
	if (!f) {
		fprintf(stderr, "⛔ non apro %s\n", percorso);
		exit(1);
	}
	uint8_t *p = malloc(attesi);
	if (!p || fread(p, 1, attesi, f) != attesi) {
		fprintf(stderr, "⛔ %s: non ci sono %zu byte\n", percorso, attesi);
		exit(1);
	}
	fclose(f);
	return p;
}

static void scena_apri(Scena *s, uint32_t l, uint32_t a, const char *dir)
{
	char p[512];
	s->l = l;
	s->a = a;
	double k = l / 1920.0;
	s->dl = (uint32_t) (1092 * k) & ~1u;
	s->da = (uint32_t) ((780 + 18 * 70) * k) & ~1u;
	snprintf(p, sizeof p, "%s/sfondo_%ux%u.bgr0", dir, l, a);
	s->sfondo = leggi(p, (size_t) l * a * 4);
	snprintf(p, sizeof p, "%s/doc_%ux%u.bgr0", dir, s->dl, s->da);
	s->doc = leggi(p, (size_t) s->dl * s->da * 4);
	s->quadro = aligned_alloc(64, (size_t) l * a * 4);
}

static void riempi(Scena *s, int x, int y, int w, int h, uint32_t colore)
{
	for (int r = y; r < y + h; r++) {
		if (r < 0 || r >= (int) s->a)
			continue;
		uint32_t *q = (uint32_t *) (s->quadro + (size_t) r * s->l * 4);
		for (int c = x; c < x + w; c++)
			if (c >= 0 && c < (int) s->l)
				q[c] = colore;
	}
}

static void scena_fotogramma(Scena *s, int n)
{
	const double k = s->l / 1920.0;
	memcpy(s->quadro, s->sfondo, (size_t) s->l * s->a * 4);

	int scorri = n < 60 ? n : 59;
	int sposta = n < 60 ? 0 : n < 90 ? n - 59 : 30;
	int wx = (int) ((120 + 12 * sposta) * k), wy = (int) (90 * k);
	int ww = (int) (1100 * k), wh = (int) (820 * k), barra = (int) (32 * k);

	/* la finestra: bordo, barra del titolo, tre bottoni */
	riempi(s, wx - 1, wy - 1, ww + 2, wh + 2, 0x00303840);
	riempi(s, wx, wy, ww, barra, 0x00e4e4e4);
	riempi(s, wx, wy + barra - 1, ww, 1, 0x00b0b0b0);
	for (int b = 0; b < 3; b++)
		riempi(s, wx + ww - (int) ((30 + 28 * b) * k), wy + (int) (10 * k),
		       (int) (12 * k), (int) (12 * k), b == 0 ? 0x003040e0 : 0x00808080);
	/* il contenuto: il documento dallo scorrimento in giu' */
	int cx = wx + (int) (4 * k), cy = wy + barra;
	int cw = (int) s->dl, ch = wh - barra - (int) (4 * k);
	int off = (int) (18 * k) * scorri;
	for (int r = 0; r < ch; r++) {
		int yy = cy + r;
		if (yy < 0 || yy >= (int) s->a || off + r >= (int) s->da)
			continue;
		int x0 = cx < 0 ? 0 : cx;
		int x1 = cx + cw > (int) s->l ? (int) s->l : cx + cw;
		if (x1 <= x0)
			continue;
		memcpy(s->quadro + ((size_t) yy * s->l + x0) * 4,
		       s->doc + ((size_t) (off + r) * s->dl + (x0 - cx)) * 4, (size_t) (x1 - x0) * 4);
	}
	/* si scrive: un carattere per fotogramma su una riga vuota in basso,
	 * e il cursore che lampeggia ogni 8 fotogrammi */
	if (n >= 90) {
		int ry = cy + ch - (int) (60 * k);
		riempi(s, cx, ry - (int) (4 * k), cw, (int) (22 * k), 0x00fffff0);
		int quanti = n - 89;
		for (int c = 0; c < quanti; c++)
			riempi(s, cx + (int) ((10 + 9 * c) * k), ry + (int) ((c % 3) * k),
			       (int) (7 * k), (int) ((12 - c % 4) * k), 0x00202020 + (uint32_t) (c * 0x030201));
		if ((n / 8) % 2 == 0)
			riempi(s, cx + (int) ((10 + 9 * quanti) * k), ry, (int) (2 * k),
			       (int) (15 * k), 0x00000000);
	}
}

/* ═══════════════════════════════════════════════════════════════════════════
 * LA STRADA VECCHIA — le opzioni di `codificatore.c` (fase 17), copiate
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct {
	CodecVideo codec;
	uint32_t l, a;
	int profondita, qualita, livello_x10;
	const AVCodec *comp;
	AVCodecContext *ctx;
	AVFrame *f;
	AVPacket *pk;
	struct SwsContext *sws;
	int64_t numero;
	int trattenuti, riaperture;
} Vecchia;

static int vecchia_contesto(Vecchia *v)
{
	v->ctx = avcodec_alloc_context3(v->comp);
	v->ctx->width = (int) v->l;
	v->ctx->height = (int) v->a;
	v->ctx->pix_fmt = v->profondita == 10 ? AV_PIX_FMT_YUV420P10LE : AV_PIX_FMT_YUV420P;
	v->ctx->time_base = (AVRational){ 1, 60 };
	v->ctx->framerate = (AVRational){ 60, 1 };
	v->ctx->max_b_frames = 0;
	v->ctx->gop_size = INT_MAX;
	v->ctx->profile = v->codec == CODIFICATORE_H264 ? AV_PROFILE_H264_HIGH : AV_PROFILE_AV1_MAIN;
	v->ctx->colorspace = AVCOL_SPC_BT709;
	v->ctx->color_primaries = AVCOL_PRI_BT709;
	v->ctx->color_trc = AVCOL_TRC_BT709;
	v->ctx->color_range = AVCOL_RANGE_MPEG;
	v->ctx->flags &= ~(unsigned) AV_CODEC_FLAG_GLOBAL_HEADER;
	if (v->codec == CODIFICATORE_H264) {
		char par[512];
		snprintf(par, sizeof par,
		         "crf=%d:bframes=0:open-gop=0:repeat-headers=1:"
		         "rc-lookahead=0:threads=1:sliced-threads=0:keyint=-1:min-keyint=-1:"
		         "log-level=error%s", v->qualita,
		         /* ⚠ SOLO per il banco: la «vecchia corretta», cioe' la riga
		          *   che avrebbe tolto il fotogramma trattenuto */
		         getenv("VECCHIA_X264_EXTRA") ? getenv("VECCHIA_X264_EXTRA") : "");
		if (av_opt_set(v->ctx->priv_data, "x264-params", par, 0) < 0)
			return -1;
		if (v->livello_x10 > 0) {
			char liv[16];
			snprintf(liv, sizeof liv, "%d.%d", v->livello_x10 / 10, v->livello_x10 % 10);
			v->ctx->level = v->livello_x10;
			av_opt_set(v->ctx->priv_data, "level", liv, 0);
		}
	} else {
		av_opt_set_int(v->ctx->priv_data, "crf", v->qualita, 0);
		av_opt_set_int(v->ctx->priv_data, "preset", 10, 0);
		av_opt_set(v->ctx->priv_data, "svtav1-params", "pred-struct=1", 0);
		if (v->livello_x10 > 0) /* ⚠ `livello_imposto()`: seq_level_idx */
			v->ctx->level = (v->livello_x10 / 10 - 2) * 4 + v->livello_x10 % 10;
	}
	int e = avcodec_open2(v->ctx, v->comp, NULL);
	if (e < 0) {
		char t[128];
		av_strerror(e, t, sizeof t);
		fprintf(stderr, "⛔ avcodec_open2: %s\n", t);
		return -1;
	}
	v->pk = av_packet_alloc();
	v->f = av_frame_alloc();
	v->f->format = v->ctx->pix_fmt;
	v->f->width = (int) v->l;
	v->f->height = (int) v->a;
	v->f->colorspace = AVCOL_SPC_BT709;
	v->f->color_range = AVCOL_RANGE_MPEG;
	av_frame_get_buffer(v->f, 0);
	return 0;
}

static void vecchia_chiudi_contesto(Vecchia *v)
{
	av_packet_free(&v->pk);
	av_frame_free(&v->f);
	avcodec_free_context(&v->ctx);
}

static int vecchia_apri(Vecchia *v, CodecVideo codec, uint32_t l, uint32_t a, int prof,
                        int qualita, int livello_x10)
{
	memset(v, 0, sizeof *v);
	v->codec = codec;
	v->l = l;
	v->a = a;
	v->profondita = prof;
	v->qualita = qualita;
	v->livello_x10 = livello_x10;
	v->comp = avcodec_find_encoder_by_name(codec == CODIFICATORE_H264 ? "libx264" : "libsvtav1");
	if (!v->comp)
		return -1;
	enum AVPixelFormat dest = prof == 10 ? AV_PIX_FMT_YUV420P10LE : AV_PIX_FMT_YUV420P;
	v->sws = sws_getContext((int) l, (int) a, AV_PIX_FMT_BGR0, (int) l, (int) a, dest,
	                        SWS_BILINEAR, NULL, NULL, NULL);
	const int *t = sws_getCoefficients(SWS_CS_ITU709);
	sws_setColorspaceDetails(v->sws, t, 1, t, 0, 0, 1 << 16, 1 << 16);
	return vecchia_contesto(v);
}

/* Come `comprimi_comune()`: un fotogramma dentro, un pacchetto fuori; se il
 * codificatore lo trattiene (EAGAIN) si svuota e si RIAPRE, e il prossimo e'
 * una chiave — esattamente la strada del prodotto. */
static bool vecchia_codifica(Vecchia *v, const uint8_t *px, bool chiave, uint64_t *us_conv,
                             uint64_t *us_cod, bool *e_chiave, uint8_t **dati, size_t *byte,
                             bool *riaperto)
{
	static bool prossimo_chiave_forzato;
	*riaperto = false;
	uint64_t t0 = ora_us();
	av_frame_make_writable(v->f);
	const uint8_t *piani[4] = { px, NULL, NULL, NULL };
	int passi[4] = { (int) v->l * 4, 0, 0, 0 };
	sws_scale(v->sws, piani, passi, 0, (int) v->a, v->f->data, v->f->linesize);
	*us_conv = ora_us() - t0;
	chiave = chiave || prossimo_chiave_forzato;
	prossimo_chiave_forzato = false;
	v->f->pts = v->numero++;
	v->f->pict_type = chiave ? AV_PICTURE_TYPE_I : AV_PICTURE_TYPE_NONE;
	if (chiave)
		v->f->flags |= AV_FRAME_FLAG_KEY;
	else
		v->f->flags &= ~(unsigned) AV_FRAME_FLAG_KEY;
	uint64_t t1 = ora_us();
	if (avcodec_send_frame(v->ctx, v->f) < 0)
		return false;
	int e = avcodec_receive_packet(v->ctx, v->pk);
	if (e == AVERROR(EAGAIN)) {
		v->trattenuti++;
		avcodec_send_frame(v->ctx, NULL);
		e = avcodec_receive_packet(v->ctx, v->pk);
		*riaperto = true;
	}
	if (e < 0)
		return false;
	*us_cod = ora_us() - t1;
	*e_chiave = (v->pk->flags & AV_PKT_FLAG_KEY) != 0;
	*dati = malloc((size_t) v->pk->size);
	memcpy(*dati, v->pk->data, (size_t) v->pk->size);
	*byte = (size_t) v->pk->size;
	av_packet_unref(v->pk);
	if (*riaperto) {
		/* la riapertura del prodotto, e il suo costo sta nel tempo */
		uint64_t t2 = ora_us();
		vecchia_chiudi_contesto(v);
		vecchia_contesto(v);
		v->riaperture++;
		prossimo_chiave_forzato = true;
		*us_cod += ora_us() - t2;
	}
	return true;
}

static void vecchia_chiudi(Vecchia *v)
{
	vecchia_chiudi_contesto(v);
	sws_freeContext(v->sws);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * I MODI
 * ═══════════════════════════════════════════════════════════════════════════ */
static int confronta(const uint8_t *a, const uint8_t *b, size_t n, int *massimo,
                     double *media, size_t *diversi)
{
	uint64_t s = 0;
	*massimo = 0;
	*diversi = 0;
	for (size_t i = 0; i < n; i++) {
		int d = abs((int) a[i] - (int) b[i]);
		if (d > *massimo)
			*massimo = d;
		s += (uint64_t) d;
		if (d)
			(*diversi)++;
	}
	*media = (double) s / (double) n;
	return 0;
}

static double psnr8(const uint8_t *a, const uint8_t *b, size_t n)
{
	double s = 0;
	for (size_t i = 0; i < n; i++) {
		double d = (double) a[i] - (double) b[i];
		s += d * d;
	}
	if (s == 0)
		return INFINITY;
	return 10.0 * log10(255.0 * 255.0 * (double) n / s);
}

static int mediana_u64(const void *x, const void *y)
{
	uint64_t a = *(const uint64_t *) x, b = *(const uint64_t *) y;
	return a < b ? -1 : a > b;
}

static int modo_colori(uint32_t l, uint32_t a, const char *dir, int n)
{
	Scena s;
	scena_apri(&s, l, a, dir);
	size_t ny = (size_t) l * a, nc = ny / 4;
	uint8_t *nostro = aligned_alloc(64, ny * 3 / 2 + 64);
	uint8_t *suo = aligned_alloc(64, ny * 3 / 2 + 64);
	uint8_t *yuv = aligned_alloc(64, ny * 3 / 2 + 64);
	uint16_t *n10 = aligned_alloc(64, ny * 3 + 64);
	uint16_t *s10 = aligned_alloc(64, ny * 3 + 64);
	uint64_t *t_n = calloc((size_t) n, 8), *t_s = calloc((size_t) n, 8),
	         *t_y = calloc((size_t) n, 8), *t_n10 = calloc((size_t) n, 8),
	         *t_s10 = calloc((size_t) n, 8);
	struct SwsContext *sws = sws_getContext((int) l, (int) a, AV_PIX_FMT_BGR0, (int) l, (int) a,
	                                        AV_PIX_FMT_YUV420P, SWS_BILINEAR, NULL, NULL, NULL);
	struct SwsContext *sws10 = sws_getContext((int) l, (int) a, AV_PIX_FMT_BGR0, (int) l,
	                                          (int) a, AV_PIX_FMT_YUV420P10LE, SWS_BILINEAR,
	                                          NULL, NULL, NULL);
	const int *t = sws_getCoefficients(SWS_CS_ITU709);
	sws_setColorspaceDetails(sws, t, 1, t, 0, 0, 1 << 16, 1 << 16);
	sws_setColorspaceDetails(sws10, t, 1, t, 0, 0, 1 << 16, 1 << 16);

	int mY = 0, mU = 0, mV = 0, m10 = 0;
	double pY = 1e9, pU = 1e9, pV = 1e9, py601 = 1e9, pu601 = 1e9;
	size_t dY = 0, dC = 0;
	for (int i = 0; i < n; i++) {
		scena_fotogramma(&s, i * (120 / n));
		uint64_t t0 = ora_us();
		colori709_a_i420(s.quadro, l * 4, l, a, COLORI709_BGRX, nostro, l, nostro + ny, l / 2,
		                 nostro + ny + nc, l / 2);
		t_n[i] = ora_us() - t0;
		const uint8_t *pi[4] = { s.quadro };
		int pa[4] = { (int) l * 4 };
		uint8_t *po[4] = { suo, suo + ny, suo + ny + nc };
		int ps[4] = { (int) l, (int) l / 2, (int) l / 2 };
		t0 = ora_us();
		sws_scale(sws, pi, pa, 0, (int) a, po, ps);
		t_s[i] = ora_us() - t0;
		t0 = ora_us();
		ARGBToI420(s.quadro, (int) l * 4, yuv, (int) l, yuv + ny, (int) l / 2, yuv + ny + nc,
		           (int) l / 2, (int) l, (int) a);
		t_y[i] = ora_us() - t0;
		t0 = ora_us();
		colori709_a_i420_10(s.quadro, l * 4, l, a, COLORI709_BGRX, n10, l * 2, n10 + ny,
		                    l, n10 + ny + nc, l);
		t_n10[i] = ora_us() - t0;
		uint8_t *po10[4] = { (uint8_t *) s10, (uint8_t *) (s10 + ny), (uint8_t *) (s10 + ny + nc) };
		int ps10[4] = { (int) l * 2, (int) l, (int) l };
		t0 = ora_us();
		sws_scale(sws10, pi, pa, 0, (int) a, po10, ps10);
		t_s10[i] = ora_us() - t0;

		if (i == 0) {
			/* l'impronta dell'uscita: la strada SSE2 e quella in C semplice
			 * devono dare gli STESSI byte (il banco si compila due volte) */
			uint64_t h = 1469598103934665603u, h10 = h;
			for (size_t q = 0; q < ny * 3 / 2; q++)
				h = (h ^ nostro[q]) * 1099511628211u;
			for (size_t q = 0; q < ny * 3 / 2; q++)
				h10 = (h10 ^ n10[q]) * 1099511628211u;
			printf("  impronta dell'uscita (fotogramma 0): 8 bit %016" PRIx64 " · 10 bit %016" PRIx64 "\n", h, h10);
		}
		int m;
		double med;
		size_t d;
		confronta(nostro, suo, ny, &m, &med, &d);
		if (m > mY)
			mY = m;
		dY += d;
		confronta(nostro + ny, suo + ny, nc, &m, &med, &d);
		if (m > mU)
			mU = m;
		dC += d;
		confronta(nostro + ny + nc, suo + ny + nc, nc, &m, &med, &d);
		if (m > mV)
			mV = m;
		dC += d;
		double q = psnr8(nostro, suo, ny);
		if (q < pY)
			pY = q;
		q = psnr8(nostro + ny, suo + ny, nc);
		if (q < pU)
			pU = q;
		q = psnr8(nostro + ny + nc, suo + ny + nc, nc);
		if (q < pV)
			pV = q;
		q = psnr8(yuv, suo, ny);
		if (q < py601)
			py601 = q;
		q = psnr8(yuv + ny, suo + ny, nc);
		if (q < pu601)
			pu601 = q;
		for (size_t k = 0; k < ny * 3 / 2; k++) {
			int dd = abs((int) n10[k] - (int) s10[k]);
			if (dd > m10)
				m10 = dd;
		}
	}
	qsort(t_n, (size_t) n, 8, mediana_u64);
	qsort(t_s, (size_t) n, 8, mediana_u64);
	qsort(t_y, (size_t) n, 8, mediana_u64);
	qsort(t_n10, (size_t) n, 8, mediana_u64);
	qsort(t_s10, (size_t) n, 8, mediana_u64);
	printf("colori %ux%u, %d fotogrammi, mediane:\n", l, a, n);
	printf("  tempo 8 bit : nostro %.2f ms · sws_scale %.2f ms · libyuv ARGBToI420 (BT.601!) %.2f ms\n",
	       t_n[n / 2] / 1000.0, t_s[n / 2] / 1000.0, t_y[n / 2] / 1000.0);
	printf("  tempo 10 bit: nostro %.2f ms · sws_scale %.2f ms\n", t_n10[n / 2] / 1000.0,
	       t_s10[n / 2] / 1000.0);
	printf("  scarto nostro/sws 8 bit: Y max %d (%.4f%% dei campioni diversi) · U max %d · V max %d "
	       "(croma diverso %.4f%%) · PSNR minimo Y %.2f U %.2f V %.2f dB\n",
	       mY, 100.0 * (double) dY / ((double) ny * n), mU, mV,
	       100.0 * (double) dC / (2.0 * nc * n), pY, pU, pV);
	printf("  scarto nostro/sws 10 bit: max %d livelli su 1023\n", m10);
	printf("  libyuv (BT.601) contro sws (BT.709): PSNR minimo Y %.2f U %.2f dB  ⛔ matrice sbagliata\n",
	       py601, pu601);
	/* i grigi e i primari, a mano */
	uint8_t px[4 * 4 * 2];
	const uint32_t prove[] = { 0x00000000, 0x00ffffff, 0x00808080, 0x00ff0000, 0x0000ff00,
	                           0x000000ff };
	for (size_t i = 0; i < sizeof prove / sizeof *prove; i++) {
		for (int k = 0; k < 8; k++)
			memcpy(px + 4 * k, &prove[i], 4);
		uint8_t y[8], u[2], v[2];
		colori709_a_i420(px, 16, 4, 2, COLORI709_BGRX, y, 4, u, 2, v, 2);
		uint8_t ys[8], us[2], vs[2];
		struct SwsContext *p = sws_getContext(4, 2, AV_PIX_FMT_BGR0, 4, 2, AV_PIX_FMT_YUV420P,
		                                      SWS_BILINEAR, NULL, NULL, NULL);
		sws_setColorspaceDetails(p, t, 1, t, 0, 0, 1 << 16, 1 << 16);
		const uint8_t *pi[4] = { px };
		int pa[4] = { 16 };
		uint8_t *po[4] = { ys, us, vs };
		int ps[4] = { 4, 2, 2 };
		sws_scale(p, pi, pa, 0, 2, po, ps);
		sws_freeContext(p);
		printf("  BGRx %06x → nostro Y %3u U %3u V %3u · sws Y %3u U %3u V %3u\n", prove[i], y[0],
		       u[0], v[0], ys[0], us[0], vs[0]);
	}
	int grigi_male = 0;
	for (int g = 0; g < 256; g++) {
		for (int k = 0; k < 8; k++) {
			px[4 * k] = px[4 * k + 1] = px[4 * k + 2] = (uint8_t) g;
			px[4 * k + 3] = 0;
		}
		uint8_t y[8], u[2], v[2];
		colori709_a_i420(px, 16, 4, 2, COLORI709_BGRX, y, 4, u, 2, v, 2);
		if (u[0] != 128 || v[0] != 128)
			grigi_male++;
	}
	printf("  grigi con croma diverso da 128: %d su 256\n", grigi_male);

	/* ⭐ NV12 e P010: la strada della scheda quando i pixel arrivano dalla
	 *    memoria (la linea scheda, 30 set: la VPP li' e' peggio di swscale).
	 *    Stesso confronto, contro sws_scale verso NV12 / P010LE. */
	{
		struct SwsContext *s12 = sws_getContext((int) l, (int) a, AV_PIX_FMT_BGR0, (int) l,
		                                        (int) a, AV_PIX_FMT_NV12, SWS_BILINEAR, NULL,
		                                        NULL, NULL);
		struct SwsContext *s010 = sws_getContext((int) l, (int) a, AV_PIX_FMT_BGR0, (int) l,
		                                         (int) a, AV_PIX_FMT_P010LE, SWS_BILINEAR,
		                                         NULL, NULL, NULL);
		sws_setColorspaceDetails(s12, t, 1, t, 0, 0, 1 << 16, 1 << 16);
		sws_setColorspaceDetails(s010, t, 1, t, 0, 0, 1 << 16, 1 << 16);
		uint64_t tn = 0, ts = 0, tn10 = 0, ts10 = 0;
		int m12 = 0, m010 = 0;
		double p12 = 1e9;
		int giri = n < 8 ? n : 8;
		for (int i = 0; i < giri; i++) {
			scena_fotogramma(&s, i * (120 / giri));
			const uint8_t *pi[4] = { s.quadro };
			int pa[4] = { (int) l * 4 };
			uint64_t t0 = ora_us();
			colori709_a_nv12(s.quadro, l * 4, l, a, COLORI709_BGRX, nostro, l, nostro + ny, l);
			tn += ora_us() - t0;
			uint8_t *po[4] = { suo, suo + ny };
			int ps[4] = { (int) l, (int) l };
			t0 = ora_us();
			sws_scale(s12, pi, pa, 0, (int) a, po, ps);
			ts += ora_us() - t0;
			for (size_t k = 0; k < ny * 3 / 2; k++) {
				int dd = abs((int) nostro[k] - (int) suo[k]);
				if (dd > m12)
					m12 = dd;
			}
			double q = psnr8(nostro, suo, ny * 3 / 2);
			if (q < p12)
				p12 = q;
			t0 = ora_us();
			colori709_a_p010(s.quadro, l * 4, l, a, COLORI709_BGRX, n10, l * 2, n10 + ny, l * 2);
			tn10 += ora_us() - t0;
			uint8_t *po10[4] = { (uint8_t *) s10, (uint8_t *) (s10 + ny) };
			int ps10[4] = { (int) l * 2, (int) l * 2 };
			t0 = ora_us();
			sws_scale(s010, pi, pa, 0, (int) a, po10, ps10);
			ts10 += ora_us() - t0;
			for (size_t k = 0; k < ny * 3 / 2; k++) {
				int dd = abs((int) (n10[k] >> 6) - (int) (s10[k] >> 6));
				if (dd > m010)
					m010 = dd;
			}
		}
		printf("  NV12: nostro %.2f ms · sws %.2f ms (medie) · scarto max %d · PSNR minimo %.2f dB\n",
		       tn / 1000.0 / giri, ts / 1000.0 / giri, m12, p12);
		printf("  P010: nostro %.2f ms · sws %.2f ms (medie) · scarto max %d livelli su 1023\n",
		       tn10 / 1000.0 / giri, ts10 / 1000.0 / giri, m010);
		sws_freeContext(s12);
		sws_freeContext(s010);
	}
	/* RGBx (labwc): lo stesso fotogramma coi byte R e B scambiati deve dare
	 * GLI STESSI byte YUV che BGRx sull'originale. */
	{
		scena_fotogramma(&s, 30);
		colori709_a_i420(s.quadro, l * 4, l, a, COLORI709_BGRX, nostro, l, nostro + ny, l / 2,
		                 nostro + ny + nc, l / 2);
		for (size_t k = 0; k < ny; k++) {
			uint8_t tmp = s.quadro[4 * k];
			s.quadro[4 * k] = s.quadro[4 * k + 2];
			s.quadro[4 * k + 2] = tmp;
		}
		colori709_a_i420(s.quadro, l * 4, l, a, COLORI709_RGBX, suo, l, suo + ny, l / 2,
		                 suo + ny + nc, l / 2);
		printf("  RGBx scambiato contro BGRx: %s\n",
		       memcmp(nostro, suo, ny * 3 / 2) ? "⛔ DIVERSI" : "byte identici");
	}
	return 0;
}

static int modo_sorgente(uint32_t l, uint32_t a, const char *dir, int n, const char *uscita)
{
	Scena s;
	scena_apri(&s, l, a, dir);
	FILE *f = fopen(uscita, "wb");
	for (int i = 0; i < n; i++) {
		scena_fotogramma(&s, i);
		fwrite(s.quadro, 1, (size_t) l * a * 4, f);
	}
	fclose(f);
	return 0;
}

static CodecVideo codec_di(const char *s)
{
	if (!strcmp(s, "h264"))
		return CODIFICATORE_H264;
	if (!strcmp(s, "av1"))
		return CODIFICATORE_AV1;
	if (!strcmp(s, "hevc"))
		return CODIFICATORE_HEVC;
	muori("codec: h264, av1 o hevc");
	return 0;
}

static CodificatoreRichiesta richiesta(CodecVideo codec, uint32_t l, uint32_t a)
{
	CodificatoreRichiesta r;
	memset(&r, 0, sizeof r);
	r.codec = codec;
	r.larghezza = l;
	r.altezza = a;
	r.fotogrammi_al_secondo = 60;
	r.modo = CODIFICATORE_QUALITA_CRF;
	const char *q = getenv("QUALITA");
	r.qualita = q ? atoi(q) : 20; /* ⭐ CRF_SOFTWARE di `figlio.c` */
	const char *p = getenv("PROFONDITA");
	r.profondita = p ? atoi(p) : 8;
	const char *lv = getenv("LIVELLO");
	r.livello_x10 = lv ? atoi(lv) : 0;
	r.formato = CODIFICATORE_PIXEL_BGRX;
	return r;
}

static int modo_codifica(CodecVideo codec, bool nuova, uint32_t l, uint32_t a, const char *dir,
                         int n, const char *uscita, int chiave_a)
{
	Scena s;
	scena_apri(&s, l, a, dir);
	CodificatoreRichiesta r = richiesta(codec, l, a);
	char err[512] = "";
	char csv[600];
	snprintf(csv, sizeof csv, "%s.csv", uscita);
	FILE *fo = fopen(uscita, "wb"), *fc = fopen(csv, "w");
	fprintf(fc, "n,byte,chiave,us_conv,us_cod,chiesta\n");
	Ripiego *rp = NULL;
	Vecchia v;
	uint64_t t0 = ora_us();
	if (nuova) {
		rp = ripiego_apri(&r, err, sizeof err);
		if (!rp) {
			fprintf(stderr, "⛔ ripiego_apri: %s\n", err);
			return 1;
		}
		fprintf(stderr, "aperto: %s\n", ripiego_nome(rp));
	} else if (vecchia_apri(&v, codec, l, a, r.profondita, r.qualita, r.livello_x10) < 0) {
		muori("vecchia strada non aperta");
	}
	uint64_t us_apri = ora_us() - t0;
	uint64_t tot_conv = 0, tot_cod = 0, tot_byte = 0;
	int chiavi = 0, chiave_mancata = 0, riaperture = 0;
	for (int i = 0; i < n; i++) {
		scena_fotogramma(&s, i);
		bool chiedi = (i == chiave_a);
		uint64_t uc = 0, ue = 0;
		bool k = false;
		const uint8_t *d;
		size_t b;
		uint8_t *dv = NULL;
		if (nuova) {
			RipiegoUscita u;
			if (!ripiego_codifica(rp, s.quadro, l * 4, chiedi, &u)) {
				fprintf(stderr, "⛔ fotogramma %d non codificato\n", i);
				return 1;
			}
			uc = u.us_conversione;
			ue = u.us_codifica;
			k = u.chiave;
			d = u.dati;
			b = u.byte;
		} else {
			bool rip;
			if (!vecchia_codifica(&v, s.quadro, chiedi, &uc, &ue, &k, &dv, &b, &rip)) {
				fprintf(stderr, "⛔ fotogramma %d non codificato (vecchia)\n", i);
				return 1;
			}
			d = dv;
			riaperture += rip;
		}
		fwrite(d, 1, b, fo);
		fprintf(fc, "%d,%zu,%d,%" PRIu64 ",%" PRIu64 ",%d\n", i, b, k, uc, ue, chiedi);
		tot_conv += uc;
		tot_cod += ue;
		tot_byte += b;
		chiavi += k;
		if (chiedi && !k)
			chiave_mancata++;
		free(dv);
	}
	fclose(fo);
	fclose(fc);
	printf("%s %s %ux%u: %d fotogrammi · apertura %.1f ms · conversione media %.2f ms · "
	       "codifica media %.2f ms · %.1f KiB/fotogramma · chiavi %d · chiave chiesta al %d %s · "
	       "riaperture per EAGAIN %d\n",
	       codec == CODIFICATORE_H264 ? "H.264" : "AV1", strada, l, a, n,
	       us_apri / 1000.0, tot_conv / 1000.0 / n, tot_cod / 1000.0 / n,
	       tot_byte / 1024.0 / n, chiavi, chiave_a,
	       chiave_a < 0 ? "-" : chiave_mancata ? "⛔ NON USCITA" : "uscita",
	       nuova ? 0 : v.riaperture);
	if (nuova)
		ripiego_chiudi(rp);
	else
		vecchia_chiudi(&v);
	return 0;
}

/* chiave su richiesta, qualita' a caldo, misura nuova: tempi e flusso */
static int modo_eventi(CodecVideo codec, bool nuova, uint32_t l, uint32_t a, const char *dir,
                       const char *uscita)
{
	Scena s, s2;
	scena_apri(&s, l, a, dir);
	uint32_t l2 = l == 3840 ? 1920 : 3840, a2 = l == 3840 ? 1080 : 2160;
	scena_apri(&s2, l2, a2, dir);
	CodificatoreRichiesta r = richiesta(codec, l, a);
	char err[512] = "";
	FILE *fo = fopen(uscita, "wb");
	Ripiego *rp = NULL;
	Vecchia v;
	if (nuova) {
		rp = ripiego_apri(&r, err, sizeof err);
		if (!rp) {
			fprintf(stderr, "⛔ %s\n", err);
			return 1;
		}
	} else {
		vecchia_apri(&v, codec, l, a, r.profondita, r.qualita, r.livello_x10);
	}
	/* 0-9 misura 1 (chiave chiesta al 5), 10: qualita' +9 (la discesa di
	 * `abbassa_qualita()`), 15: qualita' di nuovo giu', 20-29 misura 2 */
	for (int i = 0; i < 30; i++) {
		Scena *sc = i < 20 ? &s : &s2;
		uint32_t ll = i < 20 ? l : l2, aa = i < 20 ? a : a2;
		const char *evento = "";
		uint64_t us_ev = 0;
		bool chiedi = (i == 5);
		if (i == 10 || i == 15 || i == 20) {
			uint64_t t0 = ora_us();
			int q = i == 10 ? r.qualita + 9 : r.qualita;
			if (nuova) {
				bool ok = i == 20 ? ripiego_ridimensiona(rp, l2, a2, err, sizeof err)
				                  : ripiego_qualita(rp, r.modo, q, err, sizeof err);
				if (!ok) {
					fprintf(stderr, "⛔ evento %d: %s\n", i, err);
					return 1;
				}
			} else {
				vecchia_chiudi(&v);
				vecchia_apri(&v, codec, ll, aa, r.profondita, q, r.livello_x10);
			}
			us_ev = ora_us() - t0;
			evento = i == 10 ? "qualita' +9 (riapertura)" : i == 15 ? "qualita' -9 (riapertura)"
			                                                        : "misura nuova (riapertura)";
			chiedi = true;
		}
		scena_fotogramma(sc, i * 3);
		uint64_t uc = 0, ue = 0;
		bool k = false;
		const uint8_t *d;
		size_t b;
		uint8_t *dv = NULL;
		if (nuova) {
			RipiegoUscita u;
			if (!ripiego_codifica(rp, sc->quadro, ll * 4, chiedi, &u)) {
				fprintf(stderr, "⛔ fotogramma %d\n", i);
				return 1;
			}
			ue = u.us_codifica;
			uc = u.us_conversione;
			k = u.chiave;
			d = u.dati;
			b = u.byte;
		} else {
			bool rip;
			if (!vecchia_codifica(&v, sc->quadro, chiedi, &uc, &ue, &k, &dv, &b, &rip))
				return 1;
			d = dv;
		}
		fwrite(d, 1, b, fo);
		if (*evento || chiedi || i == 0 || i == 21)
			printf("  %s %s fotogramma %2d %ux%u: %s%s%.1f ms di evento · codifica %.1f ms · "
			       "%zu byte · %s%s\n",
			       codec == CODIFICATORE_H264 ? "H.264" : "AV1", strada, i,
			       ll, aa, evento, *evento ? " " : "", us_ev / 1000.0, ue / 1000.0, b,
			       k ? "CHIAVE" : "delta", chiedi && !k ? " ⛔ chiesta e non uscita" : "");
		free(dv);
	}
	fclose(fo);
	if (nuova)
		ripiego_chiudi(rp);
	else
		vecchia_chiudi(&v);
	return 0;
}

static int modo_rifiuti(void)
{
	struct {
		const char *cosa;
		CodecVideo codec;
		uint32_t l, a;
		int prof;
		ModoQualita modo;
	} casi[] = {
		{ "HEVC 1080p", CODIFICATORE_HEVC, 1920, 1080, 8, CODIFICATORE_QUALITA_CRF },
		{ "H.264 10 bit", CODIFICATORE_H264, 1920, 1080, 10, CODIFICATORE_QUALITA_CRF },
		{ "H.264 senza perdita", CODIFICATORE_H264, 1920, 1080, 8, CODIFICATORE_QUALITA_LOSSLESS },
		{ "H.264 4096x2304", CODIFICATORE_H264, 4096, 2304, 8, CODIFICATORE_QUALITA_CRF },
		{ "H.264 5120x2880", CODIFICATORE_H264, 5120, 2880, 8, CODIFICATORE_QUALITA_CRF },
		{ "H.264 7680x4320", CODIFICATORE_H264, 7680, 4320, 8, CODIFICATORE_QUALITA_CRF },
		{ "H.264 5120x1440", CODIFICATORE_H264, 5120, 1440, 8, CODIFICATORE_QUALITA_CRF },
		{ "AV1 7680x4320", CODIFICATORE_AV1, 7680, 4320, 8, CODIFICATORE_QUALITA_CRF },
		{ "AV1 senza perdita", CODIFICATORE_AV1, 1920, 1080, 8, CODIFICATORE_QUALITA_LOSSLESS },
		{ "AV1 10 bit 1080p", CODIFICATORE_AV1, 1920, 1080, 10, CODIFICATORE_QUALITA_CRF },
	};
	for (size_t i = 0; i < sizeof casi / sizeof *casi; i++) {
		CodificatoreRichiesta r = richiesta(casi[i].codec, casi[i].l, casi[i].a);
		r.profondita = casi[i].prof;
		r.modo = casi[i].modo;
		char perche[512] = "";
		uint64_t t0 = ora_us();
		Ripiego *rp = ripiego_apri(&r, perche, sizeof perche);
		double ms = (ora_us() - t0) / 1000.0;
		if (rp) {
			/* e un fotogramma vero, se si e' aperto: grigio con una sfumatura */
			size_t np = (size_t) r.larghezza * r.altezza * 4;
			uint8_t *px = malloc(np);
			for (size_t k = 0; k < np; k++)
				px[k] = (uint8_t) (k / 4 % r.larghezza * 255 / r.larghezza);
			RipiegoUscita u;
			bool ok = ripiego_codifica(rp, px, r.larghezza * 4, true, &u);
			printf("  %-22s si apre (%.0f ms) · %s · primo fotogramma %s, %zu byte\n", casi[i].cosa,
			       ms, ripiego_nome(rp), ok ? "USCITO" : "⛔ NON uscito", ok ? u.byte : 0);
			if (ok && getenv("SCRIVI")) {
				char nome[128];
				snprintf(nome, sizeof nome, "%s/rifiuto-%zu.%s", getenv("SCRIVI"), i,
				         casi[i].codec == CODIFICATORE_H264 ? "h264" : "obu");
				FILE *f = fopen(nome, "wb");
				fwrite(u.dati, 1, u.byte, f);
				fclose(f);
			}
			free(px);
			ripiego_chiudi(rp);
		} else {
			printf("  %-22s RIFIUTATO: %s\n", casi[i].cosa, perche);
		}
	}
	return 0;
}

int main(int argc, char **argv)
{
	if (argc >= 4) {
		strada = argv[3];
		/* ⭐ La «corretta» e' la vecchia con le DUE righe che le mancavano
		 *    (`[M]` 30 set 2026, questo banco): `keyint=-1` x264 lo porta a 1,
		 *    cioe' OGNI fotogramma e' una IDR; e senza `force-cfr` x264 tiene
		 *    un fotogramma in canna (`b_vfr_input`), cioe' EAGAIN e riapertura
		 *    a ogni giro.  E' il miglior x264 che il prodotto potesse avere. */
		if (!strcmp(strada, "corretta"))
			setenv("VECCHIA_X264_EXTRA", ":force-cfr=1:keyint=infinite", 1);
	}
	if (argc < 2)
		muori("modo: colori | sorgente | codifica | eventi | rifiuti");
	const char *m = argv[1];
	if (!strcmp(m, "colori") && argc >= 6)
		return modo_colori((uint32_t) atoi(argv[2]), (uint32_t) atoi(argv[3]), argv[4],
		                   atoi(argv[5]));
	if (!strcmp(m, "sorgente") && argc >= 7)
		return modo_sorgente((uint32_t) atoi(argv[2]), (uint32_t) atoi(argv[3]), argv[4],
		                     atoi(argv[5]), argv[6]);
	if (!strcmp(m, "codifica") && argc >= 9)
		return modo_codifica(codec_di(argv[2]), !strcmp(argv[3], "nuova"),
		                     (uint32_t) atoi(argv[4]), (uint32_t) atoi(argv[5]), argv[6],
		                     atoi(argv[7]), argv[8], argc >= 10 ? atoi(argv[9]) : -1);
	if (!strcmp(m, "eventi") && argc >= 8)
		return modo_eventi(codec_di(argv[2]), !strcmp(argv[3], "nuova"),
		                   (uint32_t) atoi(argv[4]), (uint32_t) atoi(argv[5]), argv[6], argv[7]);
	if (!strcmp(m, "rifiuti"))
		return modo_rifiuti();
	muori("argomenti sbagliati");
	return 1;
}
