/*
 * 19-confronto.c — the SAME desktop sequence (the generator of bench 18)
 * encoded by TWO engines on the SAME card:
 *
 *   --motore vaapi    the PRODUCT's encoder (`src/codificatore.c` +
 *                     `src/vadiretta.c`) with the VA-API path requested by name
 *                     (`h264_vaapi`), memory path or card path;
 *   --motore vulkan   the new module `src/vulkanvideo.c`, on its own: from
 *                     memory (`vulkanvideo_encode_memory`) or from DMA-BUF
 *                     (`vulkanvideo_encode_dmabuf`, zero copy via GBM);
 *   --motore gpu_card   ⭐ the INTEGRATED PRODUCT (since the graft, 1 Oct 2026):
 *                     `h264_card`/`hevc_card`, the path chosen by
 *                     capability — on the Radeon it is Vulkan inside codificatore.c,
 *                     with all the cures downstream of the bytes (cap, frame,
 *                     shape).  The JSON says which path came out.
 *
 * The shell is that of `banchi/18-scheda/18-confronto.c`: fake but
 * realistic desktop (text, windows, scrolling, dragging, cursor), one CSV
 * line per frame, at the end one JSON line with the confession.  In addition:
 *   --quality-at N:QP   the HOT quality change at frame N
 *   --capabilities NODE    the discovery of the node's Vulkan capabilities, in JSON
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
static uint32_t seed = 0x9E3779B9u;
static uint32_t case_v(void)
{
	seed ^= seed << 13;
	seed ^= seed >> 17;
	seed ^= seed << 5;
	return seed;
}

/* A "stable" 5x7 glyph: it depends only on (row, column) of the text, so the
 * text does not change from one frame to the next unless it scrolls. */
static uint32_t glyph(uint32_t row, uint32_t column)
{
	uint32_t h = row * 2654435761u ^ column * 40503u ^ 0xA5A5A5A5u;
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
		uint8_t *row = t->pixel + (size_t) y * t->step;
		for (int x = x0; x < x0 + l; x++) {
			if (x < 0 || x >= (int) t->l)
				continue;
			row[x * 4 + 0] = b;
			row[x * 4 + 1] = g;
			row[x * 4 + 2] = r;
			row[x * 4 + 3] = 0;
		}
	}
}

/* Lines of text: 5x7 glyphs in cells of (scale·6)x(scale·10), from pixel
 * `scroll` downwards (to make the terminal scroll). */
static void body_text(Canvas *t, int x0, int y0, int l, int a, int scale_v, uint32_t first_row,
                  int scroll, uint8_t b, uint8_t g, uint8_t r)
{
	int cell_w = 6 * scale_v, cell_h = 10 * scale_v;
	int columns = l / cell_w;
	for (int y = 0; y < a; y++) {
		int yy = y + scroll;
		int text_line = yy / cell_h, inside_y = (yy % cell_h) / scale_v;
		if (inside_y >= 7)
			continue;
		int py = y0 + y;
		if (py < 0 || py >= (int) t->a)
			continue;
		uint8_t *row = t->pixel + (size_t) py * t->step;
		for (int c = 0; c < columns; c++) {
			uint32_t gl = glyph(first_row + (uint32_t) text_line, (uint32_t) c);
			if ((gl & 7) == 0)
				continue; /* one space every eight */
			for (int right = 0; right < 5 * scale_v; right++) {
				int bitx = right / scale_v;
				if (!((gl >> (inside_y * 5 + bitx + 3)) & 1u))
					continue;
				int px = x0 + c * cell_w + right;
				if (px < 0 || px >= (int) t->l)
					continue;
				row[px * 4 + 0] = b;
				row[px * 4 + 1] = g;
				row[px * 4 + 2] = r;
			}
		}
	}
}

static void win(Canvas *t, int x, int y, int l, int a, int scale_v, uint32_t id,
                     int scroll, bool dark)
{
	int bar = 28 * scale_v;
	rectangle(t, x - 1, y - 1, l + 2, a + 2, 60, 60, 60);           /* border */
	rectangle(t, x, y, l, bar, 0x3a, 0x4a, 0x5e);                 /* title bar */
	rectangle(t, x + 10 * scale_v, y + 8 * scale_v, 12 * scale_v, 12 * scale_v, 0x38, 0x38, 0xe0); /* button */
	rectangle(t, x + 26 * scale_v, y + 8 * scale_v, 12 * scale_v, 12 * scale_v, 0x38, 0xc0, 0xe0);
	body_text(t, x + 50 * scale_v, y + 8 * scale_v, l / 2, 14 * scale_v, scale_v, id * 1000u, 0, 240, 240, 240);
	if (dark) {
		rectangle(t, x, y + bar, l, a - bar, 0x1e, 0x1e, 0x1e);
		body_text(t, x + 8 * scale_v, y + bar + 4 * scale_v, l - 16 * scale_v, a - bar - 8 * scale_v, scale_v,
		      id * 7919u, scroll, 0x60, 0xe0, 0x90);
	} else {
		rectangle(t, x, y + bar, l, a - bar, 0xf4, 0xf4, 0xf4);
		body_text(t, x + 12 * scale_v, y + bar + 10 * scale_v, l - 24 * scale_v, a - bar - 20 * scale_v, scale_v,
		      id * 104729u, scroll, 0x20, 0x20, 0x20);
	}
}

static void draw(Canvas *t, uint32_t n)
{
	int scale_v = (t->l >= 3000) ? 2 : 1;
	/* background: diagonal gradient with a "wallpaper" band */
	for (uint32_t y = 0; y < t->a; y++) {
		uint8_t *row = t->pixel + (size_t) y * t->step;
		for (uint32_t x = 0; x < t->l; x++) {
			uint32_t v = (x * 96 / t->l) + (y * 96 / t->a);
			row[x * 4 + 0] = (uint8_t) (60 + v);
			row[x * 4 + 1] = (uint8_t) (30 + v / 2);
			row[x * 4 + 2] = (uint8_t) (20 + v / 3);
			row[x * 4 + 3] = 0;
		}
	}
	/* the bottom bar (panel) with "icons" */
	rectangle(t, 0, (int) t->a - 40 * scale_v, (int) t->l, 40 * scale_v, 0x28, 0x28, 0x28);
	for (int i = 0; i < 12; i++)
		rectangle(t, 12 * scale_v + i * 48 * scale_v, (int) t->a - 34 * scale_v, 28 * scale_v, 28 * scale_v,
		           (uint8_t) (80 + i * 13), (uint8_t) (120 + i * 9), (uint8_t) (200 - i * 11));
	int L = (int) t->l, A = (int) t->a;
	/* window 1: a light editor, still */
	win(t, L / 20, A / 12, L * 9 / 20, A * 6 / 10, scale_v, 1, 0, false);
	/* window 2: a dark terminal that SCROLLS by 3 px per frame */
	win(t, L * 11 / 20, A / 8, L * 8 / 20, A * 5 / 10, scale_v, 2, (int) n * 3 * scale_v, true);
	/* window 3: small, DRAGGED between frames 30 and 90 */
	int right = 0, dy = 0;
	if (n >= 30 && n < 90) {
		right = (int) (n - 30) * (L / 240);
		dy = (int) (n - 30) * (A / 480);
	} else if (n >= 90) {
		right = 60 * (L / 240);
		dy = 60 * (A / 480);
	}
	win(t, L / 8 + right, A * 6 / 10 + dy, L * 3 / 10, A * 3 / 10, scale_v, 3, 0, false);
	/* the cursor: a little arrow going round */
	double ang = n * 0.11;
	int cx = L / 2 + (int) (L / 3 * __builtin_cos(ang));
	int cy = A / 2 + (int) (A / 3 * __builtin_sin(ang * 1.3));
	for (int i = 0; i < 16 * scale_v; i++)
		rectangle(t, cx, cy + i, (16 * scale_v - i) / 2 + 1, 1, 0xff, 0xff, 0xff);
	for (int i = 0; i < 16 * scale_v; i++)
		rectangle(t, cx - 1, cy + i, 1, 1, 0, 0, 0);
	(void) case_v;
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
	return c == ENCODER_H264 ? "h264" : "hevc";
}

/* The string the browser passes to `VideoDecoder.configure()`, read from the bytes
 * of the Vulkan stream with the product's READER: is a product encoder
 * opened?  No — re-reading the SPS with the same module that does it in the product
 * is not exposed; here the profile/level read with ffprobe in the .sh is enough, and the
 * string is composed from the level the module DECLARES (the Chrome bench
 * verifies it: if Chrome refuses it, it is a real red). */
static void codec_string(CodecVideo codec, int bit_depth, int lvl_idc, char *outside, size_t n)
{
	if (codec == ENCODER_H264)
		snprintf(outside, n, "avc1.6400%02x", lvl_idc);
	else
		snprintf(outside, n, "hev1.%d.%s.L%d.B0", bit_depth == 10 ? 2 : 1, bit_depth == 10 ? "4" : "6", lvl_idc);
}

static int capabilities(const char *node)
{
	VulkanVideoCapabilities c;
	char failure[256] = { 0 };
	const struct { const char *label_name; const VulkanVideoProfileCapabilities *p; } tre[3] = {
		{ "h264", &c.h264 }, { "hevc", &c.hevc }, { "hevc10", &c.hevc10 } };

	vulkanvideo_capabilities(node, &c, failure, sizeof failure);
	printf("{\"node\":\"%s\",\"vulkan\":%s,\"reason_text\":\"%s\",\"gpu_card\":\"%s\",\"driver\":\"%s\","
	       "\"api\":\"%u.%u.%u\",\"dmabuf\":%s",
	       node, c.vulkan_c_e ? "true" : "false", c.vulkan_c_e ? "" : c.reason_text, c.card_name, c.driver,
	       VK_API_VERSION_MAJOR(c.api_version), VK_API_VERSION_MINOR(c.api_version),
	       VK_API_VERSION_PATCH(c.api_version), c.dmabuf ? "true" : "false");
	for (int i = 0; i < 3; i++) {
		const VulkanVideoProfileCapabilities *p = tre[i].p;
		printf(",\"%s\":{\"encoding\":%s", tre[i].label_name, p->encoding ? "true" : "false");
		if (p->encoding)
			printf(",\"max_size\":\"%ux%u\",\"misura_minima\":\"%ux%u\",\"bitrate_modes\":%u,"
			       "\"qp\":[%d,%d],\"livello_massimo\":%d,\"slot_dpb\":%u,\"references\":%u,"
			       "\"quality_levels\":%u,\"granularita\":\"%ux%u\",\"schema\":\"%s\",\"shader_diretto\":%s,"
			       "\"syntax\":\"0x%x\",\"cabac\":%s,\"transform_8x8\":%s",
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
	const char *out_dir = NULL, *node = "/dev/dri/renderD128", *route = "mem_buf", *motore = "vulkan";
	const char *source_out = NULL;
	CodecVideo codec = ENCODER_H264;
	uint32_t l = 1920, a = 1080, n = 120, fps = 60, qp = 26, ceiling = 0;
	int bit_depth = 8;
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
		else if (!strcmp(k, "--codec")) { codec = strcmp(v, "h264") == 0 ? ENCODER_H264 : ENCODER_HEVC; i++; }
		else if (!strcmp(k, "--bit_depth")) { bit_depth = atoi(v); i++; }
		else if (!strcmp(k, "--gauge")) { sscanf(v, "%ux%u", &l, &a); i++; }
		else if (!strcmp(k, "--node")) { node = v; i++; }
		else if (!strcmp(k, "--route")) { route = v; i++; }
		else if (!strcmp(k, "--motore")) { motore = v; i++; }
		else if (!strcmp(k, "--out_dir")) { out_dir = v; i++; }
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
		else if (!strcmp(k, "--ceiling")) { ceiling = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--source-out")) { source_out = v; i++; }
		else { fprintf(stderr, "unknown argument: %s\n", k); return 2; }
	}
	if (!out_dir || !l || !a) {
		fprintf(stderr, "usage: 19-confronto --motore vulkan|vaapi|gpu_card --codec h264|hevc --gauge LxA --out_dir F [...]\n"
		                "     19-confronto --capabilities /dev/dri/renderDNNN\n");
		return 2;
	}
	bool gpu_card = strcmp(route, "gpu_card") == 0;
	bool vulkan = strcmp(motore, "vulkan") == 0;
	char failure[512] = { 0 };

	/* ── the engine: the PRODUCT (codificatore.c + vadiretta) or the Vulkan module ── */
	Encoder *cod = NULL;
	VulkanVideoDevice *vd = NULL;
	VulkanVideo *vv = NULL;
	int vulkan_level = 0;
	if (vulkan) {
		VulkanVideoRequest r = {
			.codec = codec == ENCODER_H264 ? VULKANVIDEO_H264 : VULKANVIDEO_HEVC,
			.bit_depth = bit_depth,
			.width_px = l, .height_px = a,
			.frames_per_second = fps,
			.qp = (int) qp,
			.keys_every = 0,
		};
		if (ceiling) {
			/* the same three numbers as `encoder_bandwidth_cap()`: wire 80 %,
			 * target 75 % of the wire, reservoir 40 ms */
			r.bandwidth_wire = (int64_t) ceiling * 1000000 * 80 / 100;
			r.bandwidth_point = r.bandwidth_wire * 75 / 100;
			r.reservoir_bit = (int) (r.bandwidth_wire * 40 / 1000);
		}
		vd = vulkanvideo_open_device(node, failure, sizeof failure);
		if (!vd) {
			fprintf(stderr, "⛔ the Vulkan device did not open: %s\n", failure);
			printf("{\"outcome\":\"non is_opened\",\"failure\":\"%s\"}\n", failure);
			return 1;
		}
		vv = vulkanvideo_open(vd, &r, failure, sizeof failure);
		if (!vv) {
			fprintf(stderr, "⛔ the Vulkan encoder did not open: %s\n", failure);
			printf("{\"outcome\":\"non is_opened\",\"failure\":\"%s\"}\n", failure);
			return 1;
		}
		vulkan_level = vulkanvideo_declaration(vv)->lvl_idc;
	} else {
		if (ceiling)
			encoder_bandwidth_cap(ceiling);
		EncoderRequest r = {
			.codec = codec,
			.component = strcmp(motore, "gpu_card") == 0
			                  ? (codec == ENCODER_H264 ? "h264_card" : "hevc_card")
			                  : (codec == ENCODER_H264 ? "h264_vaapi" : "hevc_vaapi"),
			.render_node = node,
			.power = ENCODER_POWER_DECLARED,
			.width_px = l, .height_px = a,
			.frames_per_second = fps,
			.manner = ENCODER_QUALITY_QP,
			.quality = (int) qp,
			.bit_depth = bit_depth,
			.schema = ENCODER_PIXEL_BGRX,
			.keys_every = 0,
		};
		cod = encoder_new(&r, failure, sizeof failure);
		if (!cod) {
			fprintf(stderr, "⛔ the encoder did not open: %s\n", failure);
			printf("{\"outcome\":\"non is_opened\",\"failure\":\"%s\"}\n", failure);
			return 1;
		}
		if (gpu_card && !encoder_in_hardware(cod)) {
			fprintf(stderr, "⛔ card path requested, but the encoder is in software\n");
			return 1;
		}
	}

	FILE *fu = fopen(out_dir, "wb");
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
	if (gpu_card) {
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
	printf("n,key_id,byte,convert_us,upload_us,encode_us,reencodes\n");
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
				buffer[b].fd = gbm_bo_get_fd(buffer[b].bo);
				buffer[b].stride = gbm_bo_get_stride(buffer[b].bo);
			}
		}
		if (resize_at >= 0 && (int) i == resize_at) {
			bool ok = vulkan ? vulkanvideo_resize(vv, resize_w, resize_h, failure, sizeof failure)
			                 : encoder_resize(cod, resize_w, resize_h, failure, sizeof failure);
			if (!ok) {
				fprintf(stderr, "⛔ resize: %s\n", failure);
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
				if (!vulkanvideo_quality(vv, quality_qp, failure, sizeof failure)) {
					fprintf(stderr, "⛔ quality: %s\n", failure);
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
				encoder_ask_key(cod);
		}

		draw(&t, i);
		if (fs)
			fwrite(t.pixel, 1, (size_t) t.step * t.a, fs);

		EncoderFrame fg;
		memset(&fg, 0, sizeof fg);
		bool ok;
		EncoderSurface s;
		memset(&s, 0, sizeof s);
		if (gpu_card) {
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
				.width_px = current_width, .height_px = current_height,
				.format_drm = DRM_FORMAT_XRGB8888, .modifier = b->modifier,
				.generation = generation,
			};
		}
		if (vulkan) {
			VulkanVideoTimings times;
			const uint8_t *data_v = NULL;
			size_t byte = 0;
			if (gpu_card) {
				VulkanVideoSurface vs = { .fd = s.fd, .offset = s.offset, .stride = s.stride,
					                         .width_px = s.width_px, .height_px = s.height_px,
					                         .format_drm = s.format_drm, .modifier = s.modifier,
					                         .generation = s.generation };
				ok = vulkanvideo_encode_dmabuf(vv, &vs, next_key, &data_v, &byte, &times, failure, sizeof failure);
			} else {
				ok = vulkanvideo_encode_memory(vv, t.pixel, t.step, VULKANVIDEO_BGRX, next_key, &data_v, &byte,
				                                  &times, failure, sizeof failure);
			}
			if (ok) {
				fg.data_v = data_v;
				fg.byte = byte;
				fg.key_id = next_key;
				fg.convert_us = times.convert_us;
				fg.upload_us = times.upload_us;
				fg.encode_us = times.encode_us;
				next_key = false;
			} else {
				fprintf(stderr, "⛔ frame %u: %s\n", i, failure);
			}
		} else if (gpu_card) {
			ok = encoder_compress_card(cod, &s, &fg);
		} else {
			ok = encoder_compress(cod, t.pixel, t.step, &fg);
		}
		if (!ok) {
			failed++;
			printf("%u,-,0,0,0,0,0\n", i);
			continue;
		}
		fwrite(fg.data_v, 1, fg.byte, fu);
		total_bytes += fg.byte;
		if (fg.key_id)
			keys++;
		printf("%u,%d,%zu,%llu,%llu,%llu,%u\n", i, fg.key_id ? 1 : 0, fg.byte,
		       (unsigned long long) fg.convert_us, (unsigned long long) fg.upload_us,
		       (unsigned long long) fg.encode_us, fg.reencodes);
		if (!vulkan)
			encoder_release(cod);
	}
	fclose(fu);
	if (fs)
		fclose(fs);

	if (vulkan) {
		const VulkanVideoDeclaration *d = vulkanvideo_declaration(vv);
		char sc[64];
		codec_string(codec, bit_depth, d->lvl_idc, sc, sizeof sc);
		printf("{\"outcome\":\"%s\",\"codec\":\"%s\",\"route\":\"%s\",\"encoder\":\"vulkanvideo\","
		       "\"in_hardware\":true,\"codec_string\":\"%s\",\"stream_depth\":%d,"
		       "\"stream_profile\":%d,\"stream_level\":%d,\"misura_flusso\":\"%ux%u\","
		       "\"low_power\":false,\"bitrate_mode\":%d,\"frames\":%u,\"keys\":%u,"
		       "\"failed\":%u,\"byte\":%llu,\"gpu_card\":\"%s\",\"driver\":\"%s\",\"codificata\":\"%ux%u\","
		       "\"direct_conversion\":%s,\"driver_has_changed_parameters\":%s,\"low_latency\":%s,"
		       "\"headers_byte\":%zu,\"input_format\":\"%s\"}\n",
		       failed ? "con fallimenti" : "ok", codec_name_arg(codec), route, sc, bit_depth,
		       codec == ENCODER_H264 ? 100 : (bit_depth == 10 ? 2 : 1), d->lvl_idc, l, a,
		       d->manner_rc == VULKANVIDEO_RC_CQP ? 1 : 2, n, keys, failed, (unsigned long long) total_bytes,
		       vulkanvideo_card_name(vd), vulkanvideo_driver_name(vd), d->encoded_width, d->encoded_height,
		       d->direct_conversion ? "true" : "false", d->driver_has_changed_parameters ? "true" : "false",
		       d->low_latency_requested ? "true" : "false", d->headers_byte, d->input_format);
		(void) vulkan_level;
		vulkanvideo_close(vv);
		vulkanvideo_close_device(vd);
	} else {
		const EncoderConfession *c = encoder_confession(cod);
		printf("{\"outcome\":\"%s\",\"codec\":\"%s\",\"route\":\"%s\",\"encoder\":\"%s\","
		       "\"strada_scheda\":\"%s\","
		       "\"in_hardware\":%s,\"codec_string\":\"%s\",\"stream_depth\":%d,"
		       "\"stream_profile\":%d,\"stream_level\":%d,\"misura_flusso\":\"%ux%u\","
		       "\"low_power\":%s,\"bitrate_mode\":%d,\"frames\":%u,\"keys\":%u,"
		       "\"failed\":%u,\"byte\":%llu}\n",
		       failed ? "con fallimenti" : "ok", codec_name_arg(codec), route,
		       c && c->component ? c->component : "", encoder_route(cod),
		       encoder_in_hardware(cod) ? "true" : "false",
		       c ? c->codec_string : "", c ? c->stream_depth : 0, c ? c->stream_profile : 0,
		       c ? c->stream_level : 0, c ? c->stream_width : 0, c ? c->stream_height : 0,
		       c && c->low_power ? "true" : "false", c ? c->bitrate_mode : 0, n, keys, failed,
		       (unsigned long long) total_bytes);
		encoder_free(cod);
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
