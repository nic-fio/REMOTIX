/*
 * 19-compare.c — the SAME desktop sequence (the generator of bench 18)
 * encoded by TWO engines on the SAME card:
 *
 *   --engine vaapi    the PRODUCT's encoder (`src/encoder.c` +
 *                     `src/vadirect.c`) with the VA-API path requested by name
 *                     (`h264_vaapi`), memory path or card path;
 *   --engine vulkan   the new module `src/vulkanvideo.c`, on its own: from
 *                     memory (`vulkanvideo_encode_memory`) or from DMA-BUF
 *                     (`vulkanvideo_encode_dmabuf`, zero copy via GBM);
 *   --engine card   ⭐ the INTEGRATED PRODUCT (since the graft, 1 Oct 2026):
 *                     `h264_card`/`hevc_card`, the path chosen by
 *                     capability — on the Radeon it is Vulkan inside encoder.c,
 *                     with all the cures downstream of the bytes (cap, frame,
 *                     shape).  The JSON says which path came out.
 *
 * The shell is that of `18-confronto.c` (retired, DECISIONI §10.44): fake but
 * realistic desktop (text, windows, scrolling, dragging, cursor), one CSV
 * line per frame, at the end one JSON line with the confession.  In addition:
 *   --quality-at N:QP   the HOT quality change at frame N
 *   --capabilities NODE    the discovery of the node's Vulkan capabilities, in JSON
 *
 * The judgement is in `19-compare.sh` (ffmpeg as measuring tool, ffprobe,
 * PSNR/SSIM) and in `19-decode-chrome.sh` (real Chrome, WebCodecs).
 */
#include "../../src/encoder.h"
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
static uint32_t seed = 0x9E3779B9u;
static uint32_t test_case(void)
{
	seed ^= seed << 13;
	seed ^= seed >> 17;
	seed ^= seed << 5;
	return seed;
}

/* A "stable" 5x7 glyph: it depends only on (row, column) of the text, so the
 * text does not change from one frame to the next unless it scrolls. */
static uint32_t glyph(uint32_t line, uint32_t column)
{
	uint32_t h = line * 2654435761u ^ column * 40503u ^ 0xA5A5A5A5u;
	h ^= h >> 15;
	h *= 2246822519u;
	h ^= h >> 13;
	return h;
}

typedef struct {
	uint8_t *pixel;
	uint32_t l, a, step;
} Canvas;

static void rectangle(Canvas *t, int x0, int y0, int l, int a, uint8_t b, uint8_t g, uint8_t r)
{
	for (int y = y0; y < y0 + a; y++) {
		if (y < 0 || y >= (int) t->a)
			continue;
		uint8_t *line = t->pixel + (size_t) y * t->step;
		for (int x = x0; x < x0 + l; x++) {
			if (x < 0 || x >= (int) t->l)
				continue;
			line[x * 4 + 0] = b;
			line[x * 4 + 1] = g;
			line[x * 4 + 2] = r;
			line[x * 4 + 3] = 0;
		}
	}
}

/* Lines of text: 5x7 glyphs in cells of (scale·6)x(scale·10), from pixel
 * `scroll` downwards (to make the terminal scroll). */
static void text(Canvas *t, int x0, int y0, int l, int a, int scale_factor, uint32_t first_row,
                  int scroll, uint8_t b, uint8_t g, uint8_t r)
{
	int cell_w = 6 * scale_factor, cell_h = 10 * scale_factor;
	int columns = l / cell_w;
	for (int y = 0; y < a; y++) {
		int yy = y + scroll;
		int text_line = yy / cell_h, inside_y = (yy % cell_h) / scale_factor;
		if (inside_y >= 7)
			continue;
		int py = y0 + y;
		if (py < 0 || py >= (int) t->a)
			continue;
		uint8_t *line = t->pixel + (size_t) py * t->step;
		for (int c = 0; c < columns; c++) {
			uint32_t gl = glyph(first_row + (uint32_t) text_line, (uint32_t) c);
			if ((gl & 7) == 0)
				continue; /* one space every eight */
			for (int dx = 0; dx < 5 * scale_factor; dx++) {
				int bitx = dx / scale_factor;
				if (!((gl >> (inside_y * 5 + bitx + 3)) & 1u))
					continue;
				int px = x0 + c * cell_w + dx;
				if (px < 0 || px >= (int) t->l)
					continue;
				line[px * 4 + 0] = b;
				line[px * 4 + 1] = g;
				line[px * 4 + 2] = r;
			}
		}
	}
}

static void window(Canvas *t, int x, int y, int l, int a, int scale_factor, uint32_t id,
                     int scroll, bool dark)
{
	int bar = 28 * scale_factor;
	rectangle(t, x - 1, y - 1, l + 2, a + 2, 60, 60, 60);           /* border */
	rectangle(t, x, y, l, bar, 0x3a, 0x4a, 0x5e);                 /* title bar */
	rectangle(t, x + 10 * scale_factor, y + 8 * scale_factor, 12 * scale_factor, 12 * scale_factor, 0x38, 0x38, 0xe0); /* button */
	rectangle(t, x + 26 * scale_factor, y + 8 * scale_factor, 12 * scale_factor, 12 * scale_factor, 0x38, 0xc0, 0xe0);
	text(t, x + 50 * scale_factor, y + 8 * scale_factor, l / 2, 14 * scale_factor, scale_factor, id * 1000u, 0, 240, 240, 240);
	if (dark) {
		rectangle(t, x, y + bar, l, a - bar, 0x1e, 0x1e, 0x1e);
		text(t, x + 8 * scale_factor, y + bar + 4 * scale_factor, l - 16 * scale_factor, a - bar - 8 * scale_factor, scale_factor,
		      id * 7919u, scroll, 0x60, 0xe0, 0x90);
	} else {
		rectangle(t, x, y + bar, l, a - bar, 0xf4, 0xf4, 0xf4);
		text(t, x + 12 * scale_factor, y + bar + 10 * scale_factor, l - 24 * scale_factor, a - bar - 20 * scale_factor, scale_factor,
		      id * 104729u, scroll, 0x20, 0x20, 0x20);
	}
}

static void draw(Canvas *t, uint32_t n)
{
	int scale_factor = (t->l >= 3000) ? 2 : 1;
	/* background: diagonal gradient with a "wallpaper" band */
	for (uint32_t y = 0; y < t->a; y++) {
		uint8_t *line = t->pixel + (size_t) y * t->step;
		for (uint32_t x = 0; x < t->l; x++) {
			uint32_t v = (x * 96 / t->l) + (y * 96 / t->a);
			line[x * 4 + 0] = (uint8_t) (60 + v);
			line[x * 4 + 1] = (uint8_t) (30 + v / 2);
			line[x * 4 + 2] = (uint8_t) (20 + v / 3);
			line[x * 4 + 3] = 0;
		}
	}
	/* the bottom bar (panel) with "icons" */
	rectangle(t, 0, (int) t->a - 40 * scale_factor, (int) t->l, 40 * scale_factor, 0x28, 0x28, 0x28);
	for (int i = 0; i < 12; i++)
		rectangle(t, 12 * scale_factor + i * 48 * scale_factor, (int) t->a - 34 * scale_factor, 28 * scale_factor, 28 * scale_factor,
		           (uint8_t) (80 + i * 13), (uint8_t) (120 + i * 9), (uint8_t) (200 - i * 11));
	int L = (int) t->l, A = (int) t->a;
	/* window 1: a light editor, still */
	window(t, L / 20, A / 12, L * 9 / 20, A * 6 / 10, scale_factor, 1, 0, false);
	/* window 2: a dark terminal that SCROLLS by 3 px per frame */
	window(t, L * 11 / 20, A / 8, L * 8 / 20, A * 5 / 10, scale_factor, 2, (int) n * 3 * scale_factor, true);
	/* window 3: small, DRAGGED between frames 30 and 90 */
	int dx = 0, dy = 0;
	if (n >= 30 && n < 90) {
		dx = (int) (n - 30) * (L / 240);
		dy = (int) (n - 30) * (A / 480);
	} else if (n >= 90) {
		dx = 60 * (L / 240);
		dy = 60 * (A / 480);
	}
	window(t, L / 8 + dx, A * 6 / 10 + dy, L * 3 / 10, A * 3 / 10, scale_factor, 3, 0, false);
	/* the cursor: a little arrow going round */
	double ang = n * 0.11;
	int cx = L / 2 + (int) (L / 3 * __builtin_cos(ang));
	int cy = A / 2 + (int) (A / 3 * __builtin_sin(ang * 1.3));
	for (int i = 0; i < 16 * scale_factor; i++)
		rectangle(t, cx, cy + i, (16 * scale_factor - i) / 2 + 1, 1, 0xff, 0xff, 0xff);
	for (int i = 0; i < 16 * scale_factor; i++)
		rectangle(t, cx - 1, cy + i, 1, 1, 0, 0, 0);
	(void) test_case;
}

/* ─── the DMA-BUF with GBM, for the card path ───────────────────────────── */
typedef struct {
	struct gbm_bo *bo;
	int fd;
	uint32_t stride;
	uint64_t modifier;
} Buffer;

/* ⭐ 5 Oct 2026, NVIDIA: its GBM refuses LINEAR + RENDERING. */
static struct gbm_bo *bo_like_product(struct gbm_device *g, uint32_t l, uint32_t a, uint64_t *mod)
{
	if (!g) {
		fprintf(stderr, "⛔ a GBM slab is needed but the GBM device is not open (--route card required)\n");
		exit(1);
	}
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

#define BUFFER_COUNT 4

static const char *codec_name_arg(CodecVideo c)
{
	return c == CODIFICATORE_H264 ? "h264" : "hevc";
}

/* The string the browser passes to `VideoDecoder.configure()`, read from the bytes
 * of the Vulkan stream with the product's READER: is a product encoder
 * opened?  No — re-reading the SPS with the same module that does it in the product
 * is not exposed; here the profile/level read with ffprobe in the .sh is enough, and the
 * string is composed from the level the module DECLARES (the Chrome bench
 * verifies it: if Chrome refuses it, it is a real red). */
static void codec_string(CodecVideo codec, int depth, int level_idc, char *report, size_t n)
{
	if (codec == CODIFICATORE_H264)
		snprintf(report, n, "avc1.6400%02x", level_idc);
	else
		snprintf(report, n, "hev1.%d.%s.L%d.B0", depth == 10 ? 2 : 1, depth == 10 ? "4" : "6", level_idc);
}

static int capabilities(const char *node)
{
	VulkanVideoCapabilities c;
	char error[256] = { 0 };
	const struct { const char *name; const VulkanVideoProfileCapabilities *p; } tre[3] = {
		{ "h264", &c.h264 }, { "hevc", &c.hevc }, { "hevc10", &c.hevc10 } };

	vulkanvideo_capabilities(node, &c, error, sizeof error);
	printf("{\"nodo\":\"%s\",\"vulkan\":%s,\"why\":\"%s\",\"card\":\"%s\",\"driver\":\"%s\","
	       "\"api\":\"%u.%u.%u\",\"dmabuf\":%s",
	       node, c.vulkan_c_e ? "true" : "false", c.vulkan_c_e ? "" : c.why, c.card_name, c.driver,
	       VK_API_VERSION_MAJOR(c.api_version), VK_API_VERSION_MINOR(c.api_version),
	       VK_API_VERSION_PATCH(c.api_version), c.dmabuf ? "true" : "false");
	for (int i = 0; i < 3; i++) {
		const VulkanVideoProfileCapabilities *p = tre[i].p;
		printf(",\"%s\":{\"encode\":%s", tre[i].name, p->encode ? "true" : "false");
		if (p->encode)
			printf(",\"misura_massima\":\"%ux%u\",\"misura_minima\":\"%ux%u\",\"modi_bitrate\":%u,"
			       "\"qp\":[%d,%d],\"livello_massimo\":%d,\"slot_dpb\":%u,\"riferimenti\":%u,"
			       "\"livelli_qualita\":%u,\"granularita\":\"%ux%u\",\"format\":\"%s\",\"shader_diretto\":%s,"
			       "\"sintassi\":\"0x%x\",\"cabac\":%s,\"transform_8x8\":%s",
			       p->max_size_w, p->max_size_h, p->min_size_w, p->min_size_h,
			       p->bitrate_modes, p->qp_min, p->qp_max, p->max_level_idc, p->slot_dpb,
			       p->active_references, p->quality_levels, p->granularity_w, p->granularity_h,
			       p->input_format, p->input_writable_by_shader ? "true" : "false",
			       p->syntax, p->cabac ? "true" : "false", p->transform_8x8 ? "true" : "false");
		printf("}");
	}
	printf("}\n");
	return c.vulkan_c_e ? 0 : 1;
}

int main(int argc, char **argv)
{
	const char *output = NULL, *node = "/dev/dri/renderD128", *route = "memory", *engine = "vulkan";
	const char *source_out = NULL;
	CodecVideo codec = CODIFICATORE_H264;
	uint32_t l = 1920, a = 1080, n = 120, fps = 60, qp = 26, cap = 0;
	int depth = 8;
	int key_at = -1, resize_at = -1, quality_at = -1, quality_qp = 0;
	uint32_t resize_w = 0, resize_h = 0;
	/* ⭐ --cycle K:LxA,LxA,... — every K frames the next size in the
	 *    list (round robin): the repeated canvas change, as F-018 does it in the
	 *    product, but without a browser (the hunt for the GPU hang of 1 Oct 2026) */
	uint32_t cycle_every = 0, cycle_n = 0, cycle_w[16], cycle_h[16], cycle_i = 0;

	for (int i = 1; i < argc; i++) {
		const char *k = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : "";
		if (!strcmp(k, "--capabilities")) { return capabilities(v); }
		else if (!strcmp(k, "--codec")) { codec = strcmp(v, "h264") == 0 ? CODIFICATORE_H264 : CODIFICATORE_HEVC; i++; }
		else if (!strcmp(k, "--depth")) { depth = atoi(v); i++; }
		else if (!strcmp(k, "--size")) { sscanf(v, "%ux%u", &l, &a); i++; }
		else if (!strcmp(k, "--node")) { node = v; i++; }
		else if (!strcmp(k, "--route")) { route = v; i++; }
		else if (!strcmp(k, "--engine")) { engine = v; i++; }
		else if (!strcmp(k, "--output")) { output = v; i++; }
		else if (!strcmp(k, "--frames")) { n = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--fps")) { fps = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--qp")) { qp = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--key-at")) { key_at = atoi(v); i++; }
		else if (!strcmp(k, "--resize-at")) { sscanf(v, "%d:%ux%u", &resize_at, &resize_w, &resize_h); i++; }
		else if (!strcmp(k, "--cycle")) {
			const char *q = strchr(v, ':');
			cycle_every = (uint32_t) atoi(v);
			while (q && cycle_n < 16 && sscanf(q + 1, "%ux%u", &cycle_w[cycle_n], &cycle_h[cycle_n]) == 2) {
				cycle_n++;
				q = strchr(q + 1, ',');
			}
			i++;
		}
		else if (!strcmp(k, "--quality-at")) { sscanf(v, "%d:%d", &quality_at, &quality_qp); i++; }
		else if (!strcmp(k, "--cap")) { cap = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--source-out")) { source_out = v; i++; }
		else { fprintf(stderr, "unknown argument: %s\n", k); return 2; }
	}
	if (!output || !l || !a) {
		fprintf(stderr, "usage: 19-compare --engine vulkan|vaapi|card --codec h264|hevc --size LxA --output F [...]\n"
		                "     19-compare --capabilities /dev/dri/renderDNNN\n");
		return 2;
	}
	bool card = strcmp(route, "card") == 0;
	bool vulkan = strcmp(engine, "vulkan") == 0;
	char error[512] = { 0 };

	/* ── the engine: the PRODUCT (encoder.c + vadiretta) or the Vulkan module ── */
	Encoder *cod = NULL;
	VulkanVideoDevice *vd = NULL;
	VulkanVideo *vv = NULL;
	int vulkan_level = 0;
	if (vulkan) {
		VulkanVideoRequest r = {
			.codec = codec == CODIFICATORE_H264 ? VULKANVIDEO_H264 : VULKANVIDEO_HEVC,
			.depth = depth,
			.width = l, .height = a,
			.fotogrammi_al_secondo = fps,
			.qp = (int) qp,
			.chiavi_ogni = 0,
		};
		if (cap) {
			/* the same three numbers as `codificatore_tetto_banda()`: wire 80 %,
			 * target 75 % of the wire, reservoir 40 ms */
			r.bandwidth_wire = (int64_t) cap * 1000000 * 80 / 100;
			r.bandwidth_point = r.bandwidth_wire * 75 / 100;
			r.reservoir_bit = (int) (r.bandwidth_wire * 40 / 1000);
		}
		vd = vulkanvideo_open_device(node, error, sizeof error);
		if (!vd) {
			fprintf(stderr, "⛔ the Vulkan device did not open: %s\n", error);
			printf("{\"outcome\":\"non aperto\",\"error\":\"%s\"}\n", error);
			return 1;
		}
		vv = vulkanvideo_open(vd, &r, error, sizeof error);
		if (!vv) {
			fprintf(stderr, "⛔ the Vulkan encoder did not open: %s\n", error);
			printf("{\"outcome\":\"non aperto\",\"error\":\"%s\"}\n", error);
			return 1;
		}
		vulkan_level = vulkanvideo_declaration(vv)->level_idc;
	} else {
		if (cap)
			codificatore_tetto_banda(cap);
		CodificatoreRichiesta r = {
			.codec = codec,
			.componente = strcmp(engine, "card") == 0
			                  ? (codec == CODIFICATORE_H264 ? "h264_card" : "hevc_card")
			                  : (codec == CODIFICATORE_H264 ? "h264_vaapi" : "hevc_vaapi"),
			.nodo_rendering = node,
			.power = ENCODER_POWER_DECLARED,
			.width = l, .height = a,
			.fotogrammi_al_secondo = fps,
			.mode = CODIFICATORE_QUALITA_QP,
			.quality = (int) qp,
			.depth = depth,
			.fmt = ENCODER_PIXEL_BGRX,
			.chiavi_ogni = 0,
		};
		cod = codificatore_nuovo(&r, error, sizeof error);
		if (!cod) {
			fprintf(stderr, "⛔ the encoder did not open: %s\n", error);
			printf("{\"outcome\":\"non aperto\",\"error\":\"%s\"}\n", error);
			return 1;
		}
		if (card && !codificatore_in_hardware(cod)) {
			fprintf(stderr, "⛔ card path requested, but the encoder is in software\n");
			return 1;
		}
	}

	FILE *fu = fopen(output, "wb");
	FILE *fs = source_out ? fopen(source_out, "wb") : NULL;
	if (!fu || (source_out && !fs)) {
		fprintf(stderr, "⛔ cannot open the output files\n");
		return 1;
	}

	Canvas t = { .l = l, .a = a, .step = l * 4 };
	t.pixel = malloc((size_t) t.step * a);
	struct gbm_device *gbm = NULL;
	Buffer buffer[BUFFER_COUNT];
	int drm_fd = -1;
	memset(buffer, 0, sizeof buffer);
	if (card) {
		drm_fd = open(node, O_RDWR | O_CLOEXEC);
		gbm = drm_fd >= 0 ? gbm_create_device(drm_fd) : NULL;
		if (!gbm) {
			fprintf(stderr, "⛔ GBM does not open on %s\n", node);
			return 1;
		}
	}

	uint64_t total_bytes = 0;
	uint32_t keys = 0, failed = 0;
	uint32_t current_width = l, current_height = a;
	uint64_t generation = 1;
	bool next_key = true;
	printf("n,chiave,byte,us_conversione,us_caricamento,us_codifica,ricodifiche\n");
	for (uint32_t i = 0; i < n; i++) {
		if (cycle_every && cycle_n && i && i % cycle_every == 0) {
			cycle_i = (cycle_i + 1) % cycle_n;
			resize_at = (int) i;
			resize_w = cycle_w[cycle_i];
			resize_h = cycle_h[cycle_i];
			fprintf(stderr, "⭐ cycle: frame %u, canvas %ux%u\n", i, resize_w, resize_h);
		}
		if (resize_at >= 0 && (int) i == resize_at && getenv("PRODUCT_ORDER")) {
			/* ⭐ the PRODUCT's order: the capture (`wlroots.c`) throws away its
			 *    GBM slabs and makes the new ones BEFORE the encoder reopens */
			for (int b = 0; b < BUFFER_COUNT; b++)
				if (buffer[b].bo) {
					close(buffer[b].fd);
					gbm_bo_destroy(buffer[b].bo);
					buffer[b].bo = NULL;
				}
			for (int b = 0; b < BUFFER_COUNT; b++) {
				buffer[b].bo = bo_like_product(gbm, resize_w, resize_h, &buffer[b].modifier);
				if (!buffer[b].bo) {
					fprintf(stderr, "⛔ gbm_bo_create %ux%u failed\n", resize_w, resize_h);
					return 1;
				}
				buffer[b].fd = gbm_bo_get_fd(buffer[b].bo);
				buffer[b].stride = gbm_bo_get_stride(buffer[b].bo);
			}
		}
		if (resize_at >= 0 && (int) i == resize_at) {
			bool ok = vulkan ? vulkanvideo_resize(vv, resize_w, resize_h, error, sizeof error)
			                 : codificatore_ridimensiona(cod, resize_w, resize_h, error, sizeof error);
			if (!ok) {
				fprintf(stderr, "⛔ ridimensiona: %s\n", error);
				return 1;
			}
			next_key = true;
			current_width = resize_w;
			current_height = resize_h;
			t.l = resize_w;
			t.a = resize_h;
			t.step = resize_w * 4;
			free(t.pixel);
			t.pixel = malloc((size_t) t.step * resize_h);
			if (!getenv("PRODUCT_ORDER"))
				for (int b = 0; b < BUFFER_COUNT; b++)
					if (buffer[b].bo) {
						close(buffer[b].fd);
						gbm_bo_destroy(buffer[b].bo);
						buffer[b].bo = NULL;
					}
			generation++;
		}
		if (quality_at >= 0 && (int) i == quality_at) {
			if (vulkan) {
				if (!vulkanvideo_quality(vv, quality_qp, error, sizeof error)) {
					fprintf(stderr, "⛔ quality: %s\n", error);
					return 1;
				}
				next_key = true; /* as `change_quality()` does in the product */
			} else {
				fprintf(stderr, "⚠ --quality-at applies only to the vulkan engine (in the product it is triggered by the 16 MiB cap)\n");
			}
		}
		if (key_at >= 0 && (int) i == key_at) {
			if (vulkan)
				next_key = true;
			else
				codificatore_chiedi_chiave(cod);
		}

		draw(&t, i);
		if (fs)
			fwrite(t.pixel, 1, (size_t) t.step * t.a, fs);

		EncoderFrame fg;
		memset(&fg, 0, sizeof fg);
		bool ok;
		EncoderSurface s;
		memset(&s, 0, sizeof s);
		if (card) {
			Buffer *b = &buffer[i % BUFFER_COUNT];
			if (!b->bo) {
				b->bo = bo_like_product(gbm, current_width, current_height, &b->modifier);
				if (!b->bo) {
					fprintf(stderr, "⛔ gbm_bo_create\n");
					return 1;
				}
				b->fd = gbm_bo_get_fd(b->bo);
				b->stride = gbm_bo_get_stride(b->bo);
			}
			uint32_t stride_map = 0;
			void *map_data = NULL;
			void *map = gbm_bo_map(b->bo, 0, 0, current_width, current_height,
			                         GBM_BO_TRANSFER_WRITE, &stride_map, &map_data);
			if (!map) {
				fprintf(stderr, "⛔ gbm_bo_map\n");
				return 1;
			}
			for (uint32_t y = 0; y < current_height; y++)
				memcpy((uint8_t *) map + (size_t) y * stride_map, t.pixel + (size_t) y * t.step,
				       (size_t) current_width * 4);
			gbm_bo_unmap(b->bo, map_data);
			s = (EncoderSurface){
				.fd = b->fd, .offset = 0, .stride = b->stride,
				.width = current_width, .height = current_height,
				.formato_drm = DRM_FORMAT_XRGB8888, .modifier = b->modifier,
				.generation = generation,
			};
		}
		if (vulkan) {
			VulkanVideoTimings times;
			const uint8_t *data = NULL;
			size_t byte = 0;
			if (card) {
				VulkanVideoSurface vs = { .fd = s.fd, .offset = s.offset, .stride = s.stride,
					                         .width = s.width, .height = s.height,
					                         .formato_drm = s.formato_drm, .modifier = s.modifier,
					                         .generation = s.generation };
				ok = vulkanvideo_encode_dmabuf(vv, &vs, next_key, &data, &byte, &times, error, sizeof error);
			} else {
				ok = vulkanvideo_encode_memory(vv, t.pixel, t.step, VULKANVIDEO_BGRX, next_key, &data, &byte,
				                                  &times, error, sizeof error);
			}
			if (ok) {
				fg.data = data;
				fg.byte = byte;
				fg.key = next_key;
				fg.us_conversione = times.us_conversione;
				fg.upload_us = times.upload_us;
				fg.us_codifica = times.us_codifica;
				next_key = false;
			} else {
				fprintf(stderr, "⛔ frame %u: %s\n", i, error);
			}
		} else if (card) {
			ok = codificatore_comprimi_scheda(cod, &s, &fg);
		} else {
			ok = codificatore_comprimi(cod, t.pixel, t.step, &fg);
		}
		if (!ok) {
			failed++;
			printf("%u,-,0,0,0,0,0\n", i);
			continue;
		}
		fwrite(fg.data, 1, fg.byte, fu);
		total_bytes += fg.byte;
		if (fg.key)
			keys++;
		printf("%u,%d,%zu,%llu,%llu,%llu,%u\n", i, fg.key ? 1 : 0, fg.byte,
		       (unsigned long long) fg.us_conversione, (unsigned long long) fg.upload_us,
		       (unsigned long long) fg.us_codifica, fg.reencodes);
		if (!vulkan)
			codificatore_rilascia(cod);
	}
	fclose(fu);
	if (fs)
		fclose(fs);

	if (vulkan) {
		const VulkanVideoDeclaration *d = vulkanvideo_declaration(vv);
		char sc[64];
		codec_string(codec, depth, d->level_idc, sc, sizeof sc);
		printf("{\"outcome\":\"%s\",\"codec\":\"%s\",\"route\":\"%s\",\"codificatore\":\"vulkanvideo\","
		       "\"in_hardware\":true,\"codec_string\":\"%s\",\"profondita_flusso\":%d,"
		       "\"profilo_flusso\":%d,\"livello_flusso\":%d,\"misura_flusso\":\"%ux%u\","
		       "\"bassa_potenza\":false,\"modo_bitrate\":%d,\"frames\":%u,\"chiavi\":%u,"
		       "\"falliti\":%u,\"byte\":%llu,\"card\":\"%s\",\"driver\":\"%s\",\"codificata\":\"%ux%u\","
		       "\"conversione_diretta\":%s,\"driver_ha_cambiato_parametri\":%s,\"ritardo_minimo\":%s,"
		       "\"intestazioni_byte\":%zu,\"formato_ingresso\":\"%s\"}\n",
		       failed ? "con fallimenti" : "ok", codec_name_arg(codec), route, sc, depth,
		       codec == CODIFICATORE_H264 ? 100 : (depth == 10 ? 2 : 1), d->level_idc, l, a,
		       d->rate_control == VULKANVIDEO_RC_CQP ? 1 : 2, n, keys, failed, (unsigned long long) total_bytes,
		       vulkanvideo_card_name(vd), vulkanvideo_driver_name(vd), d->encoded_width, d->encoded_height,
		       d->direct_conversion ? "true" : "false", d->driver_has_changed_parameters ? "true" : "false",
		       d->low_latency_requested ? "true" : "false", d->headers_byte, d->input_format);
		(void) vulkan_level;
		vulkanvideo_close(vv);
		vulkanvideo_close_device(vd);
	} else {
		const EncoderConfession *c = codificatore_confessione(cod);
		printf("{\"outcome\":\"%s\",\"codec\":\"%s\",\"route\":\"%s\",\"codificatore\":\"%s\","
		       "\"strada_scheda\":\"%s\","
		       "\"in_hardware\":%s,\"codec_string\":\"%s\",\"profondita_flusso\":%d,"
		       "\"profilo_flusso\":%d,\"livello_flusso\":%d,\"misura_flusso\":\"%ux%u\","
		       "\"bassa_potenza\":%s,\"modo_bitrate\":%d,\"frames\":%u,\"chiavi\":%u,"
		       "\"falliti\":%u,\"byte\":%llu}\n",
		       failed ? "con fallimenti" : "ok", codec_name_arg(codec), route,
		       c && c->componente ? c->componente : "", encoder_route(cod),
		       codificatore_in_hardware(cod) ? "true" : "false",
		       c ? c->codec_string : "", c ? c->stream_depth : 0, c ? c->stream_profile : 0,
		       c ? c->stream_level : 0, c ? c->stream_width : 0, c ? c->stream_height : 0,
		       c && c->low_power ? "true" : "false", c ? c->bitrate_mode : 0, n, keys, failed,
		       (unsigned long long) total_bytes);
		codificatore_libera(cod);
	}
	for (int b = 0; b < BUFFER_COUNT; b++)
		if (buffer[b].bo) {
			close(buffer[b].fd);
			gbm_bo_destroy(buffer[b].bo);
		}
	if (gbm)
		gbm_device_destroy(gbm);
	if (drm_fd >= 0)
		close(drm_fd);
	free(t.pixel);
	return failed ? 1 : 0;
}
