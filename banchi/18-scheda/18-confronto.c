/*
 * 18-confronto.c — the SAME desktop sequence, encoded by the PRODUCT's
 * encoder (`src/codificatore.c`): old path (libavcodec, the starting
 * commit of phase 18) against new (direct libva, `src/vadiretta.c`).
 *
 * The program is a shell: it contains no encoding logic.  It is
 * compiled TWICE, once with yesterday's `codificatore.c` and once with today's
 * (`18-confronto.sh`), and the two binaries do the same thing:
 *
 *   1. they draw N frames of a fake but realistic DESKTOP — gradient
 *      background, three windows with title bar and lines of «text» (glyphs
 *      pseudo-random but STABLE line by line), a scrolling terminal, a
 *      moving cursor, a dragged window.  ⛔ Not a flat
 *      colour: «the counters do not see the picture» (project memory), and
 *      a real desktop has text, borders and scrolling;
 *   2. they give them to the encoder along one of the product's two PATHS:
 *        --route mem_buf   `encoder_compress()` with the BGRx pixels;
 *        --route gpu_card    `encoder_compress_card()` with a DMA-BUF
 *                           created with GBM on the same node — zero copy;
 *   3. they write the stream (Annex-B) to --out_dir, one CSV line per frame
 *      on stdout (number, key, bytes, µs of conversion/upload/encoding)
 *      and at the end one JSON line with the confession (codec string,
 *      level read from the SPS, size, encoder name);
 *   4. on request, in the middle of the sequence: a KEY frame on request
 *      (--key-at N), a CANVAS change (--resize-at N:LxA), the bandwidth
 *      cap on from the start (--ceiling MBIT: QVBR) or the software fallback
 *      (--software).
 *
 * The judgement is not here: it is in `18-confronto.sh`, with ffmpeg decoding
 * every frame, PSNR/SSIM against the source, and ffprobe on the two streams.
 *
 *   18-confronto --codec h264|hevc --bit_depth 8|10 --gauge LxA
 *       --node /dev/dri/renderD128 --route mem_buf|gpu_card --out_dir F
 *       [--frames N] [--fps N] [--qp N] [--key-at N]
 *       [--resize-at N:LxA] [--ceiling MBIT] [--software]
 *       [--source-out F.bgrx]   (also writes the source frames, for the PSNR)
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

/* ─── a deterministic generator: xorshift32 ──────────────────────────────── */
static uint32_t seed = 0x9E3779B9u;
static uint32_t case_v(void)
{
	seed ^= seed << 13;
	seed ^= seed >> 17;
	seed ^= seed << 5;
	return seed;
}

/* A «stable» 5x7 glyph: it depends only on (row, column) of the text, so the
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
	/* background: diagonal gradient with a «wallpaper» band */
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
	/* the bottom bar (panel) with «icons» */
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
} Buffer;

#define BUFFER_COUNT 4

static const char *codec_name_arg(CodecVideo c)
{
	return c == ENCODER_H264 ? "h264" : "hevc";
}

int main(int argc, char **argv)
{
	const char *out_dir = NULL, *node = "/dev/dri/renderD128", *route = "mem_buf";
	const char *source_out = NULL;
	CodecVideo codec = ENCODER_H264;
	uint32_t l = 1920, a = 1080, n = 120, fps = 60, qp = 26, ceiling = 0;
	int bit_depth = 8;
	int key_at = -1, resize_at = -1;
	uint32_t resize_w = 0, resize_h = 0;
	bool software = false;

	for (int i = 1; i < argc; i++) {
		const char *k = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : "";
		if (!strcmp(k, "--codec")) { codec = strcmp(v, "h264") == 0 ? ENCODER_H264 : ENCODER_HEVC; i++; }
		else if (!strcmp(k, "--bit_depth")) { bit_depth = atoi(v); i++; }
		else if (!strcmp(k, "--gauge")) { sscanf(v, "%ux%u", &l, &a); i++; }
		else if (!strcmp(k, "--node")) { node = v; i++; }
		else if (!strcmp(k, "--route")) { route = v; i++; }
		else if (!strcmp(k, "--out_dir")) { out_dir = v; i++; }
		else if (!strcmp(k, "--frames")) { n = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--fps")) { fps = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--qp")) { qp = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--key-at")) { key_at = atoi(v); i++; }
		else if (!strcmp(k, "--resize-at")) { sscanf(v, "%d:%ux%u", &resize_at, &resize_w, &resize_h); i++; }
		else if (!strcmp(k, "--ceiling")) { ceiling = (uint32_t) atoi(v); i++; }
		else if (!strcmp(k, "--source-out")) { source_out = v; i++; }
		else if (!strcmp(k, "--software")) { software = true; }
		else { fprintf(stderr, "unknown argument: %s\n", k); return 2; }
	}
	if (!out_dir || !l || !a) {
		fprintf(stderr, "usage: 18-confronto --codec h264|hevc --gauge LxA --out_dir F [...]\n");
		return 2;
	}
	bool gpu_card = strcmp(route, "gpu_card") == 0;

	if (ceiling)
		encoder_bandwidth_cap(ceiling);

	EncoderRequest r = {
		.codec = codec,
		.component = software ? NULL : (codec == ENCODER_H264 ? "h264_vaapi" : "hevc_vaapi"),
		.render_node = node,
		.power = ENCODER_POWER_DECLARED,
		.width_px = l,
		.height_px = a,
		.frames_per_second = fps,
		.manner = software ? ENCODER_QUALITY_CRF : ENCODER_QUALITY_QP,
		.quality = software ? 20 : (int) qp,
		.bit_depth = bit_depth,
		.schema = ENCODER_PIXEL_BGRX,
		.keys_every = 0,
	};
	char failure[512] = { 0 };
	Encoder *cod = encoder_new(&r, failure, sizeof failure);
	if (!cod) {
		fprintf(stderr, "⛔ the encoder did not open: %s\n", failure);
		printf("{\"outcome\":\"non is_opened\",\"failure\":\"%s\"}\n", failure);
		return 1;
	}
	if (gpu_card && !encoder_in_hardware(cod)) {
		fprintf(stderr, "⛔ card path requested, but the encoder is in software\n");
		return 1;
	}

	FILE *fu = fopen(out_dir, "wb");
	FILE *fs = source_out ? fopen(source_out, "wb") : NULL;
	if (!fu || (source_out && !fs)) {
		fprintf(stderr, "⛔ cannot open the output files\n");
		return 1;
	}

	/* the canvas in memory (memory path), or the GBM buffers (card) */
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
	/* ⛔ The GENERATION of the buffers: when the canvas changes the BOs are remade, and the
	 *    descriptor numbers are recycled — without changing it the encoder
	 *    would reuse a surface imported from a buffer that no longer exists
	 *    (`EncoderSurface.generation`). */
	uint64_t generation = 1;
	printf("n,key_id,byte,convert_us,upload_us,encode_us,reencodes\n");
	for (uint32_t i = 0; i < n; i++) {
		if (resize_at >= 0 && (int) i == resize_at) {
			if (!encoder_resize(cod, resize_w, resize_h, failure, sizeof failure)) {
				fprintf(stderr, "⛔ resize: %s\n", failure);
				return 1;
			}
			current_width = resize_w;
			current_height = resize_h;
			t.l = resize_w;
			t.a = resize_h;
			t.step = resize_w * 4;
			free(t.pixel);
			t.pixel = malloc((size_t) t.step * resize_h);
			for (int b = 0; b < BUFFER_COUNT; b++)
				if (buffer[b].bo) {
					close(buffer[b].fd);
					gbm_bo_destroy(buffer[b].bo);
					buffer[b].bo = NULL;
				}
			generation++;
		}
		if (key_at >= 0 && (int) i == key_at)
			encoder_ask_key(cod);

		draw(&t, i);
		if (fs)
			fwrite(t.pixel, 1, (size_t) t.step * t.a, fs);

		EncoderFrame fg;
		bool ok;
		if (gpu_card) {
			Buffer *b = &buffer[i % BUFFER_COUNT];
			if (!b->bo) {
				b->bo = gbm_bo_create(gbm, current_width, current_height, GBM_FORMAT_XRGB8888,
				                      GBM_BO_USE_LINEAR | GBM_BO_USE_RENDERING);
				if (!b->bo) {
					fprintf(stderr, "⛔ gbm_bo_create\n");
					return 1;
				}
				b->fd = gbm_bo_get_fd(b->bo);
				b->stride = gbm_bo_get_stride(b->bo);
			}
			/* the pixels inside the DMA-BUF: the «capture» */
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
			EncoderSurface s = {
				.fd = b->fd,
				.offset = 0,
				.stride = b->stride,
				.width_px = current_width,
				.height_px = current_height,
				.format_drm = DRM_FORMAT_XRGB8888,
				.modifier = DRM_FORMAT_MOD_LINEAR,
				.generation = generation,
			};
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
		encoder_release(cod);
	}
	fclose(fu);
	if (fs)
		fclose(fs);

	const EncoderConfession *c = encoder_confession(cod);
	printf("{\"outcome\":\"%s\",\"codec\":\"%s\",\"route\":\"%s\",\"encoder\":\"%s\","
	       "\"in_hardware\":%s,\"codec_string\":\"%s\",\"stream_depth\":%d,"
	       "\"stream_profile\":%d,\"stream_level\":%d,\"misura_flusso\":\"%ux%u\","
	       "\"low_power\":%s,\"bitrate_mode\":%d,\"frames\":%u,\"keys\":%u,"
	       "\"failed\":%u,\"byte\":%llu}\n",
	       failed ? "con fallimenti" : "ok", codec_name_arg(codec), route,
	       c && c->component ? c->component : "", encoder_in_hardware(cod) ? "true" : "false",
	       c ? c->codec_string : "", c ? c->stream_depth : 0, c ? c->stream_profile : 0,
	       c ? c->stream_level : 0, c ? c->stream_width : 0, c ? c->stream_height : 0,
	       c && c->low_power ? "true" : "false", c ? c->bitrate_mode : 0, n, keys, failed,
	       (unsigned long long) total_bytes);
	encoder_free(cod);
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
