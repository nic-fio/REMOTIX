/*
 * 18-confronto.c — la STESSA sequenza di desktop, codificata dal codificatore
 * del PRODOTTO (`src/codificatore.c`): vecchia strada (libavcodec, il commit di
 * partenza della fase 18) contro nuova (libva diretta, `src/vadiretta.c`).
 *
 * Il programma e' un guscio: non contiene nessuna logica di codifica.  Si
 * compila DUE volte, una col `codificatore.c` di ieri e una con quello di oggi
 * (`18-confronto.sh`), e i due binari fanno la stessa cosa:
 *
 *   1. disegnano N fotogrammi di un DESKTOP finto ma realistico — sfondo a
 *      gradiente, tre finestre con barra del titolo e righe di «testo» (glifi
 *      pseudo-casuali ma STABILI riga per riga), un terminale che scorre, un
 *      cursore che si muove, una finestra trascinata.  ⛔ Non un colore
 *      piatto: «i contatori non vedono l'immagine» (memoria di progetto), e
 *      un desktop vero ha testo, bordi e scorrimento;
 *   2. li danno al codificatore per una delle due STRADE del prodotto:
 *        --strada memoria   `codificatore_comprimi()` coi pixel BGRx;
 *        --strada scheda    `codificatore_comprimi_scheda()` con un DMA-BUF
 *                           creato con GBM sullo stesso nodo — la copia zero;
 *   3. scrivono il flusso (Annex-B) su --uscita, una riga CSV per fotogramma
 *      su stdout (numero, chiave, byte, µs di conversione/caricamento/codifica)
 *      e in fondo una riga JSON con la confessione (stringa del codec,
 *      livello letto dall'SPS, misura, nome del codificatore);
 *   4. a richiesta, in mezzo alla sequenza: una CHIAVE a richiesta
 *      (--chiave-a N), un cambio di TELA (--ridimensiona-a N:LxA), il tetto di
 *      banda acceso dall'inizio (--tetto MBIT: QVBR) o il ripiego in software
 *      (--software).
 *
 * Il giudizio non e' qui: e' in `18-confronto.sh`, con ffmpeg che decodifica
 * ogni fotogramma, PSNR/SSIM contro la sorgente, e ffprobe sui due flussi.
 *
 *   18-confronto --codec h264|hevc --profondita 8|10 --misura LxA
 *       --nodo /dev/dri/renderD128 --strada memoria|scheda --uscita F
 *       [--fotogrammi N] [--fps N] [--qp N] [--chiave-a N]
 *       [--ridimensiona-a N:LxA] [--tetto MBIT] [--software]
 *       [--sorgente-out F.bgrx]   (scrive anche i fotogrammi sorgente, per il PSNR)
 */
#include "../../src/codificatore.h"

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include <drm_fourcc.h>
#include <gbm.h>

/* ─── un generatore deterministico: xorshift32 ──────────────────────────── */
static uint32_t seme = 0x9E3779B9u;
static uint32_t caso(void)
{
	seme ^= seme << 13;
	seme ^= seme >> 17;
	seme ^= seme << 5;
	return seme;
}

/* Un glifo 5x7 «stabile»: dipende solo da (riga, colonna) del testo, cosi' il
 * testo non cambia da un fotogramma all'altro se non scorre. */
static uint32_t glifo(uint32_t riga, uint32_t colonna)
{
	uint32_t h = riga * 2654435761u ^ colonna * 40503u ^ 0xA5A5A5A5u;
	h ^= h >> 15;
	h *= 2246822519u;
	h ^= h >> 13;
	return h;
}

typedef struct {
	uint8_t *pixel;
	uint32_t l, a, passo;
} Tela;

static void rettangolo(Tela *t, int x0, int y0, int l, int a, uint8_t b, uint8_t g, uint8_t r)
{
	for (int y = y0; y < y0 + a; y++) {
		if (y < 0 || y >= (int) t->a)
			continue;
		uint8_t *riga = t->pixel + (size_t) y * t->passo;
		for (int x = x0; x < x0 + l; x++) {
			if (x < 0 || x >= (int) t->l)
				continue;
			riga[x * 4 + 0] = b;
			riga[x * 4 + 1] = g;
			riga[x * 4 + 2] = r;
			riga[x * 4 + 3] = 0;
		}
	}
}

/* Righe di testo: glifi 5x7 in celle da (scala·6)x(scala·10), dal pixel
 * `scorrimento` in giu' (per far scorrere il terminale). */
static void testo(Tela *t, int x0, int y0, int l, int a, int scala, uint32_t prima_riga,
                  int scorrimento, uint8_t b, uint8_t g, uint8_t r)
{
	int cella_l = 6 * scala, cella_a = 10 * scala;
	int colonne = l / cella_l;
	for (int y = 0; y < a; y++) {
		int yy = y + scorrimento;
		int riga_testo = yy / cella_a, dentro_y = (yy % cella_a) / scala;
		if (dentro_y >= 7)
			continue;
		int py = y0 + y;
		if (py < 0 || py >= (int) t->a)
			continue;
		uint8_t *riga = t->pixel + (size_t) py * t->passo;
		for (int c = 0; c < colonne; c++) {
			uint32_t gl = glifo(prima_riga + (uint32_t) riga_testo, (uint32_t) c);
			if ((gl & 7) == 0)
				continue; /* uno spazio ogni otto */
			for (int dx = 0; dx < 5 * scala; dx++) {
				int bitx = dx / scala;
				if (!((gl >> (dentro_y * 5 + bitx + 3)) & 1u))
					continue;
				int px = x0 + c * cella_l + dx;
				if (px < 0 || px >= (int) t->l)
					continue;
				riga[px * 4 + 0] = b;
				riga[px * 4 + 1] = g;
				riga[px * 4 + 2] = r;
			}
		}
	}
}

static void finestra(Tela *t, int x, int y, int l, int a, int scala, uint32_t id,
                     int scorrimento, bool scura)
{
	int barra = 28 * scala;
	rettangolo(t, x - 1, y - 1, l + 2, a + 2, 60, 60, 60);           /* bordo */
	rettangolo(t, x, y, l, barra, 0x3a, 0x4a, 0x5e);                 /* barra del titolo */
	rettangolo(t, x + 10 * scala, y + 8 * scala, 12 * scala, 12 * scala, 0x38, 0x38, 0xe0); /* bottone */
	rettangolo(t, x + 26 * scala, y + 8 * scala, 12 * scala, 12 * scala, 0x38, 0xc0, 0xe0);
	testo(t, x + 50 * scala, y + 8 * scala, l / 2, 14 * scala, scala, id * 1000u, 0, 240, 240, 240);
	if (scura) {
		rettangolo(t, x, y + barra, l, a - barra, 0x1e, 0x1e, 0x1e);
		testo(t, x + 8 * scala, y + barra + 4 * scala, l - 16 * scala, a - barra - 8 * scala, scala,
		      id * 7919u, scorrimento, 0x60, 0xe0, 0x90);
	} else {
		rettangolo(t, x, y + barra, l, a - barra, 0xf4, 0xf4, 0xf4);
		testo(t, x + 12 * scala, y + barra + 10 * scala, l - 24 * scala, a - barra - 20 * scala, scala,
		      id * 104729u, scorrimento, 0x20, 0x20, 0x20);
	}
}

static void disegna(Tela *t, uint32_t n)
{
	int scala = (t->l >= 3000) ? 2 : 1;
	/* sfondo: gradiente diagonale con una banda «wallpaper» */
	for (uint32_t y = 0; y < t->a; y++) {
		uint8_t *riga = t->pixel + (size_t) y * t->passo;
		for (uint32_t x = 0; x < t->l; x++) {
			uint32_t v = (x * 96 / t->l) + (y * 96 / t->a);
			riga[x * 4 + 0] = (uint8_t) (60 + v);
			riga[x * 4 + 1] = (uint8_t) (30 + v / 2);
			riga[x * 4 + 2] = (uint8_t) (20 + v / 3);
			riga[x * 4 + 3] = 0;
		}
	}
	/* la barra in basso (pannello) con «icone» */
	rettangolo(t, 0, (int) t->a - 40 * scala, (int) t->l, 40 * scala, 0x28, 0x28, 0x28);
	for (int i = 0; i < 12; i++)
		rettangolo(t, 12 * scala + i * 48 * scala, (int) t->a - 34 * scala, 28 * scala, 28 * scala,
		           (uint8_t) (80 + i * 13), (uint8_t) (120 + i * 9), (uint8_t) (200 - i * 11));
	int L = (int) t->l, A = (int) t->a;
	/* finestra 1: un editor chiaro, fermo */
	finestra(t, L / 20, A / 12, L * 9 / 20, A * 6 / 10, scala, 1, 0, false);
	/* finestra 2: un terminale scuro che SCORRE di 3 px per fotogramma */
	finestra(t, L * 11 / 20, A / 8, L * 8 / 20, A * 5 / 10, scala, 2, (int) n * 3 * scala, true);
	/* finestra 3: piccola, TRASCINATA fra i fotogrammi 30 e 90 */
	int dx = 0, dy = 0;
	if (n >= 30 && n < 90) {
		dx = (int) (n - 30) * (L / 240);
		dy = (int) (n - 30) * (A / 480);
	} else if (n >= 90) {
		dx = 60 * (L / 240);
		dy = 60 * (A / 480);
	}
	finestra(t, L / 8 + dx, A * 6 / 10 + dy, L * 3 / 10, A * 3 / 10, scala, 3, 0, false);
	/* il cursore: una freccetta che gira */
	double ang = n * 0.11;
	int cx = L / 2 + (int) (L / 3 * __builtin_cos(ang));
	int cy = A / 2 + (int) (A / 3 * __builtin_sin(ang * 1.3));
	for (int i = 0; i < 16 * scala; i++)
		rettangolo(t, cx, cy + i, (16 * scala - i) / 2 + 1, 1, 0xff, 0xff, 0xff);
	for (int i = 0; i < 16 * scala; i++)
		rettangolo(t, cx - 1, cy + i, 1, 1, 0, 0, 0);
	(void) caso;
}

/* ─── il DMA-BUF con GBM, per la strada della scheda ────────────────────── */
typedef struct {
	struct gbm_bo *bo;
	int fd;
	uint32_t stride;
} Buffer;

#define BUFFER_QUANTI 4

static const char *nome_codec_arg(CodecVideo c)
{
	return c == CODIFICATORE_H264 ? "h264" : "hevc";
}

int main(int argc, char **argv)
{
	const char *uscita = NULL, *nodo = "/dev/dri/renderD128", *strada = "memoria";
	const char *sorgente_out = NULL;
	CodecVideo codec = CODIFICATORE_H264;
	uint32_t l = 1920, a = 1080, n = 120, fps = 60, qp = 26, tetto = 0;
	int profondita = 8;
	int chiave_a = -1, ridimensiona_a = -1;
	uint32_t ridim_l = 0, ridim_a = 0;
	bool software = false;

	for (int i = 1; i < argc; i++) {
		const char *k = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : "";
		if (!strcmp(k, "--codec")) { codec = strcmp(v, "h264") == 0 ? CODIFICATORE_H264 : CODIFICATORE_HEVC; i++; }
		else if (!strcmp(k, "--profondita")) { profondita = atoi(v); i++; }
		else if (!strcmp(k, "--misura")) { sscanf(v, "%ux%u", &l, &a); i++; }
		else if (!strcmp(k, "--nodo")) { nodo = v; i++; }
		else if (!strcmp(k, "--strada")) { strada = v; i++; }
		else if (!strcmp(k, "--uscita")) { uscita = v; i++; }
		else if (!strcmp(k, "--fotogrammi")) { n = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--fps")) { fps = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--qp")) { qp = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--chiave-a")) { chiave_a = atoi(v); i++; }
		else if (!strcmp(k, "--ridimensiona-a")) { sscanf(v, "%d:%ux%u", &ridimensiona_a, &ridim_l, &ridim_a); i++; }
		else if (!strcmp(k, "--tetto")) { tetto = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--sorgente-out")) { sorgente_out = v; i++; }
		else if (!strcmp(k, "--software")) { software = true; }
		else { fprintf(stderr, "argomento ignoto: %s\n", k); return 2; }
	}
	if (!uscita || !l || !a) {
		fprintf(stderr, "uso: 18-confronto --codec h264|hevc --misura LxA --uscita F [...]\n");
		return 2;
	}
	bool scheda = strcmp(strada, "scheda") == 0;

	if (tetto)
		codificatore_tetto_banda(tetto);

	CodificatoreRichiesta r = {
		.codec = codec,
		.componente = software ? NULL : (codec == CODIFICATORE_H264 ? "h264_vaapi" : "hevc_vaapi"),
		.nodo_rendering = nodo,
		.potenza = CODIFICATORE_POTENZA_LA_DICHIARATA,
		.larghezza = l,
		.altezza = a,
		.fotogrammi_al_secondo = fps,
		.modo = software ? CODIFICATORE_QUALITA_CRF : CODIFICATORE_QUALITA_QP,
		.qualita = software ? 20 : (int) qp,
		.profondita = profondita,
		.formato = CODIFICATORE_PIXEL_BGRX,
		.chiavi_ogni = 0,
	};
	char errore[512] = { 0 };
	Codificatore *cod = codificatore_nuovo(&r, errore, sizeof errore);
	if (!cod) {
		fprintf(stderr, "⛔ il codificatore non si e' aperto: %s\n", errore);
		printf("{\"esito\":\"non aperto\",\"errore\":\"%s\"}\n", errore);
		return 1;
	}
	if (scheda && !codificatore_in_hardware(cod)) {
		fprintf(stderr, "⛔ strada della scheda chiesta, ma il codificatore e' in software\n");
		return 1;
	}

	FILE *fu = fopen(uscita, "wb");
	FILE *fs = sorgente_out ? fopen(sorgente_out, "wb") : NULL;
	if (!fu || (sorgente_out && !fs)) {
		fprintf(stderr, "⛔ non apro i file d'uscita\n");
		return 1;
	}

	/* la tela in memoria (strada della memoria), o i buffer GBM (scheda) */
	Tela t = { .l = l, .a = a, .passo = l * 4 };
	t.pixel = malloc((size_t) t.passo * a);
	struct gbm_device *gbm = NULL;
	Buffer buffer[BUFFER_QUANTI];
	int drm_fd = -1;
	memset(buffer, 0, sizeof buffer);
	if (scheda) {
		drm_fd = open(nodo, O_RDWR | O_CLOEXEC);
		gbm = drm_fd >= 0 ? gbm_create_device(drm_fd) : NULL;
		if (!gbm) {
			fprintf(stderr, "⛔ GBM non si apre su %s\n", nodo);
			return 1;
		}
	}

	uint64_t byte_totali = 0;
	uint32_t chiavi = 0, falliti = 0;
	uint32_t larghezza_corrente = l, altezza_corrente = a;
	/* ⛔ La GENERAZIONE dei buffer: quando la tela cambia i BO si rifanno, e i
	 *    numeri di descrittore si riciclano — senza cambiarla il codificatore
	 *    riuserebbe una superficie importata da un buffer che non c'e' piu'
	 *    (`CodificatoreSuperficie.generazione`). */
	uint64_t generazione = 1;
	printf("n,chiave,byte,us_conversione,us_caricamento,us_codifica,ricodifiche\n");
	for (uint32_t i = 0; i < n; i++) {
		if (ridimensiona_a >= 0 && (int) i == ridimensiona_a) {
			if (!codificatore_ridimensiona(cod, ridim_l, ridim_a, errore, sizeof errore)) {
				fprintf(stderr, "⛔ ridimensiona: %s\n", errore);
				return 1;
			}
			larghezza_corrente = ridim_l;
			altezza_corrente = ridim_a;
			t.l = ridim_l;
			t.a = ridim_a;
			t.passo = ridim_l * 4;
			free(t.pixel);
			t.pixel = malloc((size_t) t.passo * ridim_a);
			for (int b = 0; b < BUFFER_QUANTI; b++)
				if (buffer[b].bo) {
					close(buffer[b].fd);
					gbm_bo_destroy(buffer[b].bo);
					buffer[b].bo = NULL;
				}
			generazione++;
		}
		if (chiave_a >= 0 && (int) i == chiave_a)
			codificatore_chiedi_chiave(cod);

		disegna(&t, i);
		if (fs)
			fwrite(t.pixel, 1, (size_t) t.passo * t.a, fs);

		CodificatoreFotogramma fg;
		bool ok;
		if (scheda) {
			Buffer *b = &buffer[i % BUFFER_QUANTI];
			if (!b->bo) {
				b->bo = gbm_bo_create(gbm, larghezza_corrente, altezza_corrente, GBM_FORMAT_XRGB8888,
				                      GBM_BO_USE_LINEAR | GBM_BO_USE_RENDERING);
				if (!b->bo) {
					fprintf(stderr, "⛔ gbm_bo_create\n");
					return 1;
				}
				b->fd = gbm_bo_get_fd(b->bo);
				b->stride = gbm_bo_get_stride(b->bo);
			}
			/* i pixel dentro il DMA-BUF: la «cattura» */
			uint32_t stride_mappa = 0;
			void *mappa_dati = NULL;
			void *mappa = gbm_bo_map(b->bo, 0, 0, larghezza_corrente, altezza_corrente,
			                         GBM_BO_TRANSFER_WRITE, &stride_mappa, &mappa_dati);
			if (!mappa) {
				fprintf(stderr, "⛔ gbm_bo_map\n");
				return 1;
			}
			for (uint32_t y = 0; y < altezza_corrente; y++)
				memcpy((uint8_t *) mappa + (size_t) y * stride_mappa, t.pixel + (size_t) y * t.passo,
				       (size_t) larghezza_corrente * 4);
			gbm_bo_unmap(b->bo, mappa_dati);
			CodificatoreSuperficie s = {
				.fd = b->fd,
				.offset = 0,
				.stride = b->stride,
				.larghezza = larghezza_corrente,
				.altezza = altezza_corrente,
				.formato_drm = DRM_FORMAT_XRGB8888,
				.modificatore = DRM_FORMAT_MOD_LINEAR,
				.generazione = generazione,
			};
			ok = codificatore_comprimi_scheda(cod, &s, &fg);
		} else {
			ok = codificatore_comprimi(cod, t.pixel, t.passo, &fg);
		}
		if (!ok) {
			falliti++;
			printf("%u,-,0,0,0,0,0\n", i);
			continue;
		}
		fwrite(fg.dati, 1, fg.byte, fu);
		byte_totali += fg.byte;
		if (fg.chiave)
			chiavi++;
		printf("%u,%d,%zu,%llu,%llu,%llu,%u\n", i, fg.chiave ? 1 : 0, fg.byte,
		       (unsigned long long) fg.us_conversione, (unsigned long long) fg.us_caricamento,
		       (unsigned long long) fg.us_codifica, fg.ricodifiche);
		codificatore_rilascia(cod);
	}
	fclose(fu);
	if (fs)
		fclose(fs);

	const CodificatoreConfessione *c = codificatore_confessione(cod);
	printf("{\"esito\":\"%s\",\"codec\":\"%s\",\"strada\":\"%s\",\"codificatore\":\"%s\","
	       "\"in_hardware\":%s,\"stringa_codec\":\"%s\",\"profondita_flusso\":%d,"
	       "\"profilo_flusso\":%d,\"livello_flusso\":%d,\"misura_flusso\":\"%ux%u\","
	       "\"bassa_potenza\":%s,\"modo_bitrate\":%d,\"fotogrammi\":%u,\"chiavi\":%u,"
	       "\"falliti\":%u,\"byte\":%llu}\n",
	       falliti ? "con fallimenti" : "ok", nome_codec_arg(codec), strada,
	       c && c->componente ? c->componente : "", codificatore_in_hardware(cod) ? "true" : "false",
	       c ? c->stringa_codec : "", c ? c->profondita_flusso : 0, c ? c->profilo_flusso : 0,
	       c ? c->livello_flusso : 0, c ? c->larghezza_flusso : 0, c ? c->altezza_flusso : 0,
	       c && c->bassa_potenza ? "true" : "false", c ? c->modo_bitrate : 0, n, chiavi, falliti,
	       (unsigned long long) byte_totali);
	codificatore_libera(cod);
	for (int b = 0; b < BUFFER_QUANTI; b++)
		if (buffer[b].bo) {
			close(buffer[b].fd);
			gbm_bo_destroy(buffer[b].bo);
		}
	if (gbm)
		gbm_device_destroy(gbm);
	if (drm_fd >= 0)
		close(drm_fd);
	free(t.pixel);
	return falliti ? 1 : 0;
}
