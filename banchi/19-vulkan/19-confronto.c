/*
 * 19-confronto.c — the SAME desktop sequence (the generator of bench 18)
 * encoded by TWO engines on the SAME card:
 *
 *   --motore vaapi    the PRODUCT's encoder (`src/codificatore.c` +
 *                     `src/vadiretta.c`) with the VA-API path requested by name
 *                     (`h264_vaapi`), memory path or card path;
 *   --motore vulkan   the new module `src/vulkanvideo.c`, on its own: from
 *                     memory (`vulkanvideo_codifica_memoria`) or from DMA-BUF
 *                     (`vulkanvideo_codifica_dmabuf`, zero copy via GBM);
 *   --motore scheda   ⭐ the INTEGRATED PRODUCT (since the graft, 1 Oct 2026):
 *                     `h264_scheda`/`hevc_scheda`, the path chosen by
 *                     capability — on the Radeon it is Vulkan inside codificatore.c,
 *                     with all the cures downstream of the bytes (cap, frame,
 *                     shape).  The JSON says which path came out.
 *
 * The shell is that of `banchi/18-scheda/18-confronto.c`: fake but
 * realistic desktop (text, windows, scrolling, dragging, cursor), one CSV
 * line per frame, at the end one JSON line with the confession.  In addition:
 *   --qualita-a N:QP   the HOT quality change at frame N
 *   --capacita NODO    the discovery of the node's Vulkan capabilities, in JSON
 *
 * The judgement is in `19-confronto.sh` (ffmpeg as measuring tool, ffprobe,
 * PSNR/SSIM) and in `19-decodifica-chrome.sh` (real Chrome, WebCodecs).
 */
#include "../../src/codificatore.h"
#include "../../src/vulkanvideo.h"

#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <unistd.h>

#include <drm_fourcc.h>
#include <gbm.h>
#include <vulkan/vulkan.h>

/* ─── a deterministic generator: xorshift32 ──────────────────────────────── */
static uint32_t seme = 0x9E3779B9u;
static uint32_t caso(void)
{
	seme ^= seme << 13;
	seme ^= seme >> 17;
	seme ^= seme << 5;
	return seme;
}

/* A "stable" 5x7 glyph: it depends only on (row, column) of the text, so the
 * text does not change from one frame to the next unless it scrolls. */
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

/* Lines of text: 5x7 glyphs in cells of (scale·6)x(scale·10), from pixel
 * `scorrimento` downwards (to make the terminal scroll). */
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
				continue; /* one space every eight */
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
	rettangolo(t, x - 1, y - 1, l + 2, a + 2, 60, 60, 60);           /* border */
	rettangolo(t, x, y, l, barra, 0x3a, 0x4a, 0x5e);                 /* title bar */
	rettangolo(t, x + 10 * scala, y + 8 * scala, 12 * scala, 12 * scala, 0x38, 0x38, 0xe0); /* button */
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
	/* background: diagonal gradient with a "wallpaper" band */
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
	/* the bottom bar (panel) with "icons" */
	rettangolo(t, 0, (int) t->a - 40 * scala, (int) t->l, 40 * scala, 0x28, 0x28, 0x28);
	for (int i = 0; i < 12; i++)
		rettangolo(t, 12 * scala + i * 48 * scala, (int) t->a - 34 * scala, 28 * scala, 28 * scala,
		           (uint8_t) (80 + i * 13), (uint8_t) (120 + i * 9), (uint8_t) (200 - i * 11));
	int L = (int) t->l, A = (int) t->a;
	/* window 1: a light editor, still */
	finestra(t, L / 20, A / 12, L * 9 / 20, A * 6 / 10, scala, 1, 0, false);
	/* window 2: a dark terminal that SCROLLS by 3 px per frame */
	finestra(t, L * 11 / 20, A / 8, L * 8 / 20, A * 5 / 10, scala, 2, (int) n * 3 * scala, true);
	/* window 3: small, DRAGGED between frames 30 and 90 */
	int dx = 0, dy = 0;
	if (n >= 30 && n < 90) {
		dx = (int) (n - 30) * (L / 240);
		dy = (int) (n - 30) * (A / 480);
	} else if (n >= 90) {
		dx = 60 * (L / 240);
		dy = 60 * (A / 480);
	}
	finestra(t, L / 8 + dx, A * 6 / 10 + dy, L * 3 / 10, A * 3 / 10, scala, 3, 0, false);
	/* the cursor: a little arrow going round */
	double ang = n * 0.11;
	int cx = L / 2 + (int) (L / 3 * __builtin_cos(ang));
	int cy = A / 2 + (int) (A / 3 * __builtin_sin(ang * 1.3));
	for (int i = 0; i < 16 * scala; i++)
		rettangolo(t, cx, cy + i, (16 * scala - i) / 2 + 1, 1, 0xff, 0xff, 0xff);
	for (int i = 0; i < 16 * scala; i++)
		rettangolo(t, cx - 1, cy + i, 1, 1, 0, 0, 0);
	(void) caso;
}

/* ─── the DMA-BUF with GBM, for the card path ───────────────────────────── */
typedef struct {
	struct gbm_bo *bo;
	int fd;
	uint32_t stride;
	uint64_t modificatore;
} Buffer;

/* ⭐ 5 Oct 2026, NVIDIA: its GBM refuses LINEAR + RENDERING. */
static struct gbm_bo *bo_come_il_prodotto(struct gbm_device *g, uint32_t l, uint32_t a, uint64_t *mod)
{
	struct gbm_bo *bo = gbm_bo_create(g, l, a, GBM_FORMAT_XRGB8888, GBM_BO_USE_LINEAR | GBM_BO_USE_RENDERING);
	*mod = DRM_FORMAT_MOD_LINEAR;
	if (!bo) {
		/* ⚠ The bench writes the pixels with the CPU (`gbm_bo_map`), and NVIDIA does not
		 *    map its tiled slabs: here we fall back to LINEAR without
		 *    RENDERING, which Vulkan imports just the same.  The product's tiled slab
		 *    is tested by the suite (the compositor really draws into it). */
		bo = gbm_bo_create(g, l, a, GBM_FORMAT_XRGB8888, GBM_BO_USE_LINEAR);
		if (bo)
			fprintf(stderr, "⚠ LINEAR+RENDERING refused: LINEAR slab without RENDERING\n");
	}
	return bo;
}

#define BUFFER_QUANTI 4

static const char *nome_codec_arg(CodecVideo c)
{
	return c == CODIFICATORE_H264 ? "h264" : "hevc";
}

/* The string the browser passes to `VideoDecoder.configure()`, read from the bytes
 * of the Vulkan stream with the product's READER: is a product encoder
 * opened?  No — re-reading the SPS with the same module that does it in the product
 * is not exposed; here the profile/level read with ffprobe in the .sh is enough, and the
 * string is composed from the level the module DECLARES (the Chrome bench
 * verifies it: if Chrome refuses it, it is a real red). */
static void stringa_codec(CodecVideo codec, int profondita, int livello_idc, char *fuori, size_t n)
{
	if (codec == CODIFICATORE_H264)
		snprintf(fuori, n, "avc1.6400%02x", livello_idc);
	else
		snprintf(fuori, n, "hev1.%d.%s.L%d.B0", profondita == 10 ? 2 : 1, profondita == 10 ? "4" : "6", livello_idc);
}

static int capacita(const char *nodo)
{
	VulkanVideoCapacita c;
	char errore[256] = { 0 };
	const struct { const char *nome; const VulkanVideoProfiloCapacita *p; } tre[3] = {
		{ "h264", &c.h264 }, { "hevc", &c.hevc }, { "hevc10", &c.hevc10 } };

	vulkanvideo_capacita(nodo, &c, errore, sizeof errore);
	printf("{\"nodo\":\"%s\",\"vulkan\":%s,\"perche\":\"%s\",\"scheda\":\"%s\",\"driver\":\"%s\","
	       "\"api\":\"%u.%u.%u\",\"dmabuf\":%s",
	       nodo, c.vulkan_c_e ? "true" : "false", c.vulkan_c_e ? "" : c.perche, c.nome_scheda, c.driver,
	       VK_API_VERSION_MAJOR(c.versione_api), VK_API_VERSION_MINOR(c.versione_api),
	       VK_API_VERSION_PATCH(c.versione_api), c.dmabuf ? "true" : "false");
	for (int i = 0; i < 3; i++) {
		const VulkanVideoProfiloCapacita *p = tre[i].p;
		printf(",\"%s\":{\"codifica\":%s", tre[i].nome, p->codifica ? "true" : "false");
		if (p->codifica)
			printf(",\"misura_massima\":\"%ux%u\",\"misura_minima\":\"%ux%u\",\"modi_bitrate\":%u,"
			       "\"qp\":[%d,%d],\"livello_massimo\":%d,\"slot_dpb\":%u,\"riferimenti\":%u,"
			       "\"livelli_qualita\":%u,\"granularita\":\"%ux%u\",\"formato\":\"%s\",\"shader_diretto\":%s,"
			       "\"sintassi\":\"0x%x\",\"cabac\":%s,\"transform_8x8\":%s",
			       p->misura_massima_l, p->misura_massima_a, p->misura_minima_l, p->misura_minima_a,
			       p->modi_bitrate, p->qp_minimo, p->qp_massimo, p->livello_massimo_idc, p->slot_dpb,
			       p->riferimenti_attivi, p->livelli_qualita, p->granularita_l, p->granularita_a,
			       p->formato_ingresso, p->ingresso_scrivibile_dallo_shader ? "true" : "false",
			       p->sintassi, p->cabac ? "true" : "false", p->transform_8x8 ? "true" : "false");
		printf("}");
	}
	printf("}\n");
	return c.vulkan_c_e ? 0 : 1;
}

int main(int argc, char **argv)
{
	const char *uscita = NULL, *nodo = "/dev/dri/renderD128", *strada = "memoria", *motore = "vulkan";
	const char *sorgente_out = NULL;
	CodecVideo codec = CODIFICATORE_H264;
	uint32_t l = 1920, a = 1080, n = 120, fps = 60, qp = 26, tetto = 0;
	int profondita = 8;
	int chiave_a = -1, ridimensiona_a = -1, qualita_a = -1, qualita_qp = 0;
	uint32_t ridim_l = 0, ridim_a = 0;
	/* ⭐ --ciclo K:LxA,LxA,... — every K frames the next size in the
	 *    list (round robin): the repeated canvas change, as F-018 does it in the
	 *    product, but without a browser (the hunt for the GPU hang of 1 Oct 2026) */
	uint32_t ciclo_ogni = 0, ciclo_n = 0, ciclo_l[16], ciclo_a[16], ciclo_i = 0;

	for (int i = 1; i < argc; i++) {
		const char *k = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : "";
		if (!strcmp(k, "--capacita")) { return capacita(v); }
		else if (!strcmp(k, "--codec")) { codec = strcmp(v, "h264") == 0 ? CODIFICATORE_H264 : CODIFICATORE_HEVC; i++; }
		else if (!strcmp(k, "--profondita")) { profondita = atoi(v); i++; }
		else if (!strcmp(k, "--misura")) { sscanf(v, "%ux%u", &l, &a); i++; }
		else if (!strcmp(k, "--nodo")) { nodo = v; i++; }
		else if (!strcmp(k, "--strada")) { strada = v; i++; }
		else if (!strcmp(k, "--motore")) { motore = v; i++; }
		else if (!strcmp(k, "--uscita")) { uscita = v; i++; }
		else if (!strcmp(k, "--fotogrammi")) { n = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--fps")) { fps = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--qp")) { qp = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--chiave-a")) { chiave_a = atoi(v); i++; }
		else if (!strcmp(k, "--ridimensiona-a")) { sscanf(v, "%d:%ux%u", &ridimensiona_a, &ridim_l, &ridim_a); i++; }
		else if (!strcmp(k, "--ciclo")) {
			const char *q = strchr(v, ':');
			ciclo_ogni = (uint32_t) atoi(v);
			while (q && ciclo_n < 16 && sscanf(q + 1, "%ux%u", &ciclo_l[ciclo_n], &ciclo_a[ciclo_n]) == 2) {
				ciclo_n++;
				q = strchr(q + 1, ',');
			}
			i++;
		}
		else if (!strcmp(k, "--qualita-a")) { sscanf(v, "%d:%d", &qualita_a, &qualita_qp); i++; }
		else if (!strcmp(k, "--tetto")) { tetto = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--sorgente-out")) { sorgente_out = v; i++; }
		else { fprintf(stderr, "unknown argument: %s\n", k); return 2; }
	}
	if (!uscita || !l || !a) {
		fprintf(stderr, "usage: 19-confronto --motore vulkan|vaapi|scheda --codec h264|hevc --misura LxA --uscita F [...]\n"
		                "     19-confronto --capacita /dev/dri/renderDNNN\n");
		return 2;
	}
	bool scheda = strcmp(strada, "scheda") == 0;
	bool vulkan = strcmp(motore, "vulkan") == 0;
	char errore[512] = { 0 };

	/* ── the engine: the PRODUCT (codificatore.c + vadiretta) or the Vulkan module ── */
	Codificatore *cod = NULL;
	VulkanVideoDispositivo *vd = NULL;
	VulkanVideo *vv = NULL;
	int livello_vulkan = 0;
	if (vulkan) {
		VulkanVideoRichiesta r = {
			.codec = codec == CODIFICATORE_H264 ? VULKANVIDEO_H264 : VULKANVIDEO_HEVC,
			.profondita = profondita,
			.larghezza = l, .altezza = a,
			.fotogrammi_al_secondo = fps,
			.qp = (int) qp,
			.chiavi_ogni = 0,
		};
		if (tetto) {
			/* the same three numbers as `codificatore_tetto_banda()`: wire 80 %,
			 * target 75 % of the wire, reservoir 40 ms */
			r.banda_filo = (int64_t) tetto * 1000000 * 80 / 100;
			r.banda_punto = r.banda_filo * 75 / 100;
			r.serbatoio_bit = (int) (r.banda_filo * 40 / 1000);
		}
		vd = vulkanvideo_apri_dispositivo(nodo, errore, sizeof errore);
		if (!vd) {
			fprintf(stderr, "⛔ the Vulkan device did not open: %s\n", errore);
			printf("{\"esito\":\"non aperto\",\"errore\":\"%s\"}\n", errore);
			return 1;
		}
		vv = vulkanvideo_apri(vd, &r, errore, sizeof errore);
		if (!vv) {
			fprintf(stderr, "⛔ the Vulkan encoder did not open: %s\n", errore);
			printf("{\"esito\":\"non aperto\",\"errore\":\"%s\"}\n", errore);
			return 1;
		}
		livello_vulkan = vulkanvideo_dichiarazione(vv)->livello_idc;
	} else {
		if (tetto)
			codificatore_tetto_banda(tetto);
		CodificatoreRichiesta r = {
			.codec = codec,
			.componente = strcmp(motore, "scheda") == 0
			                  ? (codec == CODIFICATORE_H264 ? "h264_scheda" : "hevc_scheda")
			                  : (codec == CODIFICATORE_H264 ? "h264_vaapi" : "hevc_vaapi"),
			.nodo_rendering = nodo,
			.potenza = CODIFICATORE_POTENZA_LA_DICHIARATA,
			.larghezza = l, .altezza = a,
			.fotogrammi_al_secondo = fps,
			.modo = CODIFICATORE_QUALITA_QP,
			.qualita = (int) qp,
			.profondita = profondita,
			.formato = CODIFICATORE_PIXEL_BGRX,
			.chiavi_ogni = 0,
		};
		cod = codificatore_nuovo(&r, errore, sizeof errore);
		if (!cod) {
			fprintf(stderr, "⛔ the encoder did not open: %s\n", errore);
			printf("{\"esito\":\"non aperto\",\"errore\":\"%s\"}\n", errore);
			return 1;
		}
		if (scheda && !codificatore_in_hardware(cod)) {
			fprintf(stderr, "⛔ card path requested, but the encoder is in software\n");
			return 1;
		}
	}

	FILE *fu = fopen(uscita, "wb");
	FILE *fs = sorgente_out ? fopen(sorgente_out, "wb") : NULL;
	if (!fu || (sorgente_out && !fs)) {
		fprintf(stderr, "⛔ cannot open the output files\n");
		return 1;
	}

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
			fprintf(stderr, "⛔ GBM does not open on %s\n", nodo);
			return 1;
		}
	}

	uint64_t byte_totali = 0;
	uint32_t chiavi = 0, falliti = 0;
	uint32_t larghezza_corrente = l, altezza_corrente = a;
	uint64_t generazione = 1;
	bool prossima_chiave = true;
	printf("n,chiave,byte,us_conversione,us_caricamento,us_codifica,ricodifiche\n");
	for (uint32_t i = 0; i < n; i++) {
		if (ciclo_ogni && ciclo_n && i && i % ciclo_ogni == 0) {
			ciclo_i = (ciclo_i + 1) % ciclo_n;
			ridimensiona_a = (int) i;
			ridim_l = ciclo_l[ciclo_i];
			ridim_a = ciclo_a[ciclo_i];
			fprintf(stderr, "⭐ cycle: frame %u, canvas %ux%u\n", i, ridim_l, ridim_a);
		}
		if (ridimensiona_a >= 0 && (int) i == ridimensiona_a && getenv("ORDINE_PRODOTTO")) {
			/* ⭐ the PRODUCT's order: the capture (`wlroots.c`) throws away its
			 *    GBM slabs and makes the new ones BEFORE the encoder reopens */
			for (int b = 0; b < BUFFER_QUANTI; b++)
				if (buffer[b].bo) {
					close(buffer[b].fd);
					gbm_bo_destroy(buffer[b].bo);
					buffer[b].bo = NULL;
				}
			for (int b = 0; b < BUFFER_QUANTI; b++) {
				buffer[b].bo = bo_come_il_prodotto(gbm, ridim_l, ridim_a, &buffer[b].modificatore);
				buffer[b].fd = gbm_bo_get_fd(buffer[b].bo);
				buffer[b].stride = gbm_bo_get_stride(buffer[b].bo);
			}
		}
		if (ridimensiona_a >= 0 && (int) i == ridimensiona_a) {
			bool ok = vulkan ? vulkanvideo_ridimensiona(vv, ridim_l, ridim_a, errore, sizeof errore)
			                 : codificatore_ridimensiona(cod, ridim_l, ridim_a, errore, sizeof errore);
			if (!ok) {
				fprintf(stderr, "⛔ ridimensiona: %s\n", errore);
				return 1;
			}
			prossima_chiave = true;
			larghezza_corrente = ridim_l;
			altezza_corrente = ridim_a;
			t.l = ridim_l;
			t.a = ridim_a;
			t.passo = ridim_l * 4;
			free(t.pixel);
			t.pixel = malloc((size_t) t.passo * ridim_a);
			if (!getenv("ORDINE_PRODOTTO"))
				for (int b = 0; b < BUFFER_QUANTI; b++)
					if (buffer[b].bo) {
						close(buffer[b].fd);
						gbm_bo_destroy(buffer[b].bo);
						buffer[b].bo = NULL;
					}
			generazione++;
		}
		if (qualita_a >= 0 && (int) i == qualita_a) {
			if (vulkan) {
				if (!vulkanvideo_qualita(vv, qualita_qp, errore, sizeof errore)) {
					fprintf(stderr, "⛔ quality: %s\n", errore);
					return 1;
				}
				prossima_chiave = true; /* as `cambia_qualita()` does in the product */
			} else {
				fprintf(stderr, "⚠ --qualita-a applies only to the vulkan engine (in the product it is triggered by the 16 MiB cap)\n");
			}
		}
		if (chiave_a >= 0 && (int) i == chiave_a) {
			if (vulkan)
				prossima_chiave = true;
			else
				codificatore_chiedi_chiave(cod);
		}

		disegna(&t, i);
		if (fs)
			fwrite(t.pixel, 1, (size_t) t.passo * t.a, fs);

		CodificatoreFotogramma fg;
		memset(&fg, 0, sizeof fg);
		bool ok;
		CodificatoreSuperficie s;
		memset(&s, 0, sizeof s);
		if (scheda) {
			Buffer *b = &buffer[i % BUFFER_QUANTI];
			if (!b->bo) {
				b->bo = bo_come_il_prodotto(gbm, larghezza_corrente, altezza_corrente, &b->modificatore);
				if (!b->bo) {
					fprintf(stderr, "⛔ gbm_bo_create\n");
					return 1;
				}
				b->fd = gbm_bo_get_fd(b->bo);
				b->stride = gbm_bo_get_stride(b->bo);
			}
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
			s = (CodificatoreSuperficie){
				.fd = b->fd, .offset = 0, .stride = b->stride,
				.larghezza = larghezza_corrente, .altezza = altezza_corrente,
				.formato_drm = DRM_FORMAT_XRGB8888, .modificatore = b->modificatore,
				.generazione = generazione,
			};
		}
		if (vulkan) {
			VulkanVideoTempi tempi;
			const uint8_t *dati = NULL;
			size_t byte = 0;
			if (scheda) {
				VulkanVideoSuperficie vs = { .fd = s.fd, .offset = s.offset, .stride = s.stride,
					                         .larghezza = s.larghezza, .altezza = s.altezza,
					                         .formato_drm = s.formato_drm, .modificatore = s.modificatore,
					                         .generazione = s.generazione };
				ok = vulkanvideo_codifica_dmabuf(vv, &vs, prossima_chiave, &dati, &byte, &tempi, errore, sizeof errore);
			} else {
				ok = vulkanvideo_codifica_memoria(vv, t.pixel, t.passo, VULKANVIDEO_BGRX, prossima_chiave, &dati, &byte,
				                                  &tempi, errore, sizeof errore);
			}
			if (ok) {
				fg.dati = dati;
				fg.byte = byte;
				fg.chiave = prossima_chiave;
				fg.us_conversione = tempi.us_conversione;
				fg.us_caricamento = tempi.us_caricamento;
				fg.us_codifica = tempi.us_codifica;
				prossima_chiave = false;
			} else {
				fprintf(stderr, "⛔ frame %u: %s\n", i, errore);
			}
		} else if (scheda) {
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
		if (!vulkan)
			codificatore_rilascia(cod);
	}
	fclose(fu);
	if (fs)
		fclose(fs);

	if (vulkan) {
		const VulkanVideoDichiarazione *d = vulkanvideo_dichiarazione(vv);
		char sc[64];
		stringa_codec(codec, profondita, d->livello_idc, sc, sizeof sc);
		printf("{\"esito\":\"%s\",\"codec\":\"%s\",\"strada\":\"%s\",\"codificatore\":\"vulkanvideo\","
		       "\"in_hardware\":true,\"stringa_codec\":\"%s\",\"profondita_flusso\":%d,"
		       "\"profilo_flusso\":%d,\"livello_flusso\":%d,\"misura_flusso\":\"%ux%u\","
		       "\"bassa_potenza\":false,\"modo_bitrate\":%d,\"fotogrammi\":%u,\"chiavi\":%u,"
		       "\"falliti\":%u,\"byte\":%llu,\"scheda\":\"%s\",\"driver\":\"%s\",\"codificata\":\"%ux%u\","
		       "\"conversione_diretta\":%s,\"driver_ha_cambiato_parametri\":%s,\"ritardo_minimo\":%s,"
		       "\"intestazioni_byte\":%zu,\"formato_ingresso\":\"%s\"}\n",
		       falliti ? "con fallimenti" : "ok", nome_codec_arg(codec), strada, sc, profondita,
		       codec == CODIFICATORE_H264 ? 100 : (profondita == 10 ? 2 : 1), d->livello_idc, l, a,
		       d->modo_rc == VULKANVIDEO_RC_CQP ? 1 : 2, n, chiavi, falliti, (unsigned long long) byte_totali,
		       vulkanvideo_nome_scheda(vd), vulkanvideo_nome_driver(vd), d->larghezza_codificata, d->altezza_codificata,
		       d->conversione_diretta ? "true" : "false", d->driver_ha_cambiato_parametri ? "true" : "false",
		       d->ritardo_minimo_chiesto ? "true" : "false", d->intestazioni_byte, d->formato_ingresso);
		(void) livello_vulkan;
		vulkanvideo_chiudi(vv);
		vulkanvideo_chiudi_dispositivo(vd);
	} else {
		const CodificatoreConfessione *c = codificatore_confessione(cod);
		printf("{\"esito\":\"%s\",\"codec\":\"%s\",\"strada\":\"%s\",\"codificatore\":\"%s\","
		       "\"strada_scheda\":\"%s\","
		       "\"in_hardware\":%s,\"stringa_codec\":\"%s\",\"profondita_flusso\":%d,"
		       "\"profilo_flusso\":%d,\"livello_flusso\":%d,\"misura_flusso\":\"%ux%u\","
		       "\"bassa_potenza\":%s,\"modo_bitrate\":%d,\"fotogrammi\":%u,\"chiavi\":%u,"
		       "\"falliti\":%u,\"byte\":%llu}\n",
		       falliti ? "con fallimenti" : "ok", nome_codec_arg(codec), strada,
		       c && c->componente ? c->componente : "", codificatore_strada(cod),
		       codificatore_in_hardware(cod) ? "true" : "false",
		       c ? c->stringa_codec : "", c ? c->profondita_flusso : 0, c ? c->profilo_flusso : 0,
		       c ? c->livello_flusso : 0, c ? c->larghezza_flusso : 0, c ? c->altezza_flusso : 0,
		       c && c->bassa_potenza ? "true" : "false", c ? c->modo_bitrate : 0, n, chiavi, falliti,
		       (unsigned long long) byte_totali);
		codificatore_libera(cod);
	}
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
