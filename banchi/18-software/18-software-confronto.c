/*
 * 18-software-confronto.c — phase 18, V-software line: the OLD software
 * fallback (libavcodec libx264/libsvtav1 + sws_scale, with the options of
 * `codificatore.c`) against the NEW one (`src/ripiego.c`: OpenH264, SVT-AV1 direct,
 * `src/colori709.c`), on the SAME sequence of desktop images.
 *
 * Modes:
 *   colors   L A DIR N              ours against sws_scale (time and gap), and
 *                                   libyuv ARGBToI420 (BT.601) for reference
 *   source L A DIR N output.raw    writes the sequence in bgr0 (for ffmpeg)
 *   encode CODEC STRADA L A DIR N output [CHIAVE_A]
 *            CODEC = h264|av1 · STRADA = old|new
 *            writes uscita (.h264 Annex B / .obu) and uscita.csv (one frame
 *            per line: n, byte, key, us_conversione, us_codifica)
 *   events   CODEC STRADA L A DIR output
 *            key on request, quality change on the fly, size change:
 *            the time of each one and the stream for ffmpeg to decode
 *   refusals                          what the new one does NOT do, stated
 *
 * The scene (in 1080p units, scaled by L/1920): the real LXQt wallpaper
 * (`l1.png` of the test machine), an editor window with real code
 * that SCROLLS (frames 0-59, one line per frame), then the window
 * DRAGGED (60-89, 12 px per frame), then TYPING (90-119: one character
 * per frame and the blinking cursor).
 */
#include "../../src/colori709.h"
/* ⛔ Phase 19: `src/ripiego.h` has left the product.  The bench stays as
 *    history: `18-software-confronto.sh` extracts `ripiego.c/.h` from commit
 *    6bacca7 and passes them with `-I`. */
#include "ripiego.h"

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

static uint64_t now_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t) t.tv_sec * 1000000u + (uint64_t) t.tv_nsec / 1000u;
}

/* the route name for the output lines: old · fixed · new */
static const char *route = "?";

static void die(const char *m)
{
	fprintf(stderr, "⛔ %s\n", m);
	exit(1);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * THE SCENE
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct {
	uint32_t l, a;
	uint8_t *background;      /* l x a bgr0 */
	uint8_t *doc;         /* dl x da bgr0 */
	uint32_t dl, da;
	uint8_t *frame_buf;      /* the composed frame */
} Scene;

static uint8_t *load(const char *fpath, size_t expected_vals)
{
	FILE *f = fopen(fpath, "rb");
	if (!f) {
		fprintf(stderr, "⛔ cannot open %s\n", fpath);
		exit(1);
	}
	uint8_t *p = malloc(expected_vals);
	if (!p || fread(p, 1, expected_vals, f) != expected_vals) {
		fprintf(stderr, "⛔ %s: %zu bytes are not there\n", fpath, expected_vals);
		exit(1);
	}
	fclose(f);
	return p;
}

static void scene_open(Scene *s, uint32_t l, uint32_t a, const char *dir)
{
	char p[512];
	s->l = l;
	s->a = a;
	double k = l / 1920.0;
	s->dl = (uint32_t) (1092 * k) & ~1u;
	s->da = (uint32_t) ((780 + 18 * 70) * k) & ~1u;
	snprintf(p, sizeof p, "%s/sfondo_%ux%u.bgr0", dir, l, a);
	s->background = load(p, (size_t) l * a * 4);
	snprintf(p, sizeof p, "%s/doc_%ux%u.bgr0", dir, s->dl, s->da);
	s->doc = load(p, (size_t) s->dl * s->da * 4);
	s->frame_buf = aligned_alloc(64, (size_t) l * a * 4);
}

static void fill(Scene *s, int x, int y, int w, int h, uint32_t color)
{
	for (int r = y; r < y + h; r++) {
		if (r < 0 || r >= (int) s->a)
			continue;
		uint32_t *q = (uint32_t *) (s->frame_buf + (size_t) r * s->l * 4);
		for (int c = x; c < x + w; c++)
			if (c >= 0 && c < (int) s->l)
				q[c] = color;
	}
}

static void scene_frame(Scene *s, int n)
{
	const double k = s->l / 1920.0;
	memcpy(s->frame_buf, s->background, (size_t) s->l * s->a * 4);

	int scroll = n < 60 ? n : 59;
	int move = n < 60 ? 0 : n < 90 ? n - 59 : 30;
	int wx = (int) ((120 + 12 * move) * k), wy = (int) (90 * k);
	int ww = (int) (1100 * k), wh = (int) (820 * k), bar = (int) (32 * k);

	/* the window: border, title bar, three buttons */
	fill(s, wx - 1, wy - 1, ww + 2, wh + 2, 0x00303840);
	fill(s, wx, wy, ww, bar, 0x00e4e4e4);
	fill(s, wx, wy + bar - 1, ww, 1, 0x00b0b0b0);
	for (int b = 0; b < 3; b++)
		fill(s, wx + ww - (int) ((30 + 28 * b) * k), wy + (int) (10 * k),
		       (int) (12 * k), (int) (12 * k), b == 0 ? 0x003040e0 : 0x00808080);
	/* the content: the document from the scroll position down */
	int cx = wx + (int) (4 * k), cy = wy + bar;
	int cw = (int) s->dl, ch = wh - bar - (int) (4 * k);
	int off = (int) (18 * k) * scroll;
	for (int r = 0; r < ch; r++) {
		int yy = cy + r;
		if (yy < 0 || yy >= (int) s->a || off + r >= (int) s->da)
			continue;
		int x0 = cx < 0 ? 0 : cx;
		int x1 = cx + cw > (int) s->l ? (int) s->l : cx + cw;
		if (x1 <= x0)
			continue;
		memcpy(s->frame_buf + ((size_t) yy * s->l + x0) * 4,
		       s->doc + ((size_t) (off + r) * s->dl + (x0 - cx)) * 4, (size_t) (x1 - x0) * 4);
	}
	/* typing: one character per frame on an empty line at the bottom,
	 * and the cursor blinking every 8 frames */
	if (n >= 90) {
		int ry = cy + ch - (int) (60 * k);
		fill(s, cx, ry - (int) (4 * k), cw, (int) (22 * k), 0x00fffff0);
		int amount = n - 89;
		for (int c = 0; c < amount; c++)
			fill(s, cx + (int) ((10 + 9 * c) * k), ry + (int) ((c % 3) * k),
			       (int) (7 * k), (int) ((12 - c % 4) * k), 0x00202020 + (uint32_t) (c * 0x030201));
		if ((n / 8) % 2 == 0)
			fill(s, cx + (int) ((10 + 9 * amount) * k), ry, (int) (2 * k),
			       (int) (15 * k), 0x00000000);
	}
}

/* ═══════════════════════════════════════════════════════════════════════════
 * THE OLD ROUTE — the options of `codificatore.c` (phase 17), copied
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct {
	CodecVideo codec;
	uint32_t l, a;
	int depth, quality, livello_x10;
	const AVCodec *comp;
	AVCodecContext *ctx;
	AVFrame *f;
	AVPacket *pk;
	struct SwsContext *sws;
	int64_t nr;
	int held, reopenings;
} Old;

static int old_context(Old *v)
{
	v->ctx = avcodec_alloc_context3(v->comp);
	v->ctx->width = (int) v->l;
	v->ctx->height = (int) v->a;
	v->ctx->pix_fmt = v->depth == 10 ? AV_PIX_FMT_YUV420P10LE : AV_PIX_FMT_YUV420P;
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
		         "log-level=error%s", v->quality,
		         /* ⚠ ONLY for the bench: the "corrected old one", i.e. the line
		          *   that would have removed the held-back frame */
		         getenv("OLD_X264_EXTRA") ? getenv("OLD_X264_EXTRA") : "");
		if (av_opt_set(v->ctx->priv_data, "x264-params", par, 0) < 0)
			return -1;
		if (v->livello_x10 > 0) {
			char liv[16];
			snprintf(liv, sizeof liv, "%d.%d", v->livello_x10 / 10, v->livello_x10 % 10);
			v->ctx->level = v->livello_x10;
			av_opt_set(v->ctx->priv_data, "level", liv, 0);
		}
	} else {
		av_opt_set_int(v->ctx->priv_data, "crf", v->quality, 0);
		av_opt_set_int(v->ctx->priv_data, "preset", 10, 0);
		av_opt_set(v->ctx->priv_data, "svtav1-params", "pred-struct=1", 0);
		if (v->livello_x10 > 0) /* ⚠ `imposed_level()`: seq_level_idx */
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

static void old_close_context(Old *v)
{
	av_packet_free(&v->pk);
	av_frame_free(&v->f);
	avcodec_free_context(&v->ctx);
}

static int old_open(Old *v, CodecVideo codec, uint32_t l, uint32_t a, int prof,
                        int quality, int livello_x10)
{
	memset(v, 0, sizeof *v);
	v->codec = codec;
	v->l = l;
	v->a = a;
	v->depth = prof;
	v->quality = quality;
	v->livello_x10 = livello_x10;
	v->comp = avcodec_find_encoder_by_name(codec == CODIFICATORE_H264 ? "libx264" : "libsvtav1");
	if (!v->comp)
		return -1;
	enum AVPixelFormat dest = prof == 10 ? AV_PIX_FMT_YUV420P10LE : AV_PIX_FMT_YUV420P;
	v->sws = sws_getContext((int) l, (int) a, AV_PIX_FMT_BGR0, (int) l, (int) a, dest,
	                        SWS_BILINEAR, NULL, NULL, NULL);
	const int *t = sws_getCoefficients(SWS_CS_ITU709);
	sws_setColorspaceDetails(v->sws, t, 1, t, 0, 0, 1 << 16, 1 << 16);
	return old_context(v);
}

/* Like `compress_common()`: one frame in, one packet out; if the
 * encoder holds it back (EAGAIN) it is flushed and REOPENED, and the next one
 * is a key — exactly the product's route. */
static bool old_encoding(Old *v, const uint8_t *px, bool key, uint64_t *us_conv,
                             uint64_t *us_cod, bool *is_key, uint8_t **data, size_t *byte,
                             bool *reopened)
{
	static bool force_next_key;
	*reopened = false;
	uint64_t t0 = now_us();
	av_frame_make_writable(v->f);
	const uint8_t *plans[4] = { px, NULL, NULL, NULL };
	int steps[4] = { (int) v->l * 4, 0, 0, 0 };
	sws_scale(v->sws, plans, steps, 0, (int) v->a, v->f->data, v->f->linesize);
	*us_conv = now_us() - t0;
	key = key || force_next_key;
	force_next_key = false;
	v->f->pts = v->nr++;
	v->f->pict_type = key ? AV_PICTURE_TYPE_I : AV_PICTURE_TYPE_NONE;
	if (key)
		v->f->flags |= AV_FRAME_FLAG_KEY;
	else
		v->f->flags &= ~(unsigned) AV_FRAME_FLAG_KEY;
	uint64_t t1 = now_us();
	if (avcodec_send_frame(v->ctx, v->f) < 0)
		return false;
	int e = avcodec_receive_packet(v->ctx, v->pk);
	if (e == AVERROR(EAGAIN)) {
		v->held++;
		avcodec_send_frame(v->ctx, NULL);
		e = avcodec_receive_packet(v->ctx, v->pk);
		*reopened = true;
	}
	if (e < 0)
		return false;
	*us_cod = now_us() - t1;
	*is_key = (v->pk->flags & AV_PKT_FLAG_KEY) != 0;
	*data = malloc((size_t) v->pk->size);
	memcpy(*data, v->pk->data, (size_t) v->pk->size);
	*byte = (size_t) v->pk->size;
	av_packet_unref(v->pk);
	if (*reopened) {
		/* the product's reopening, and its cost goes into the time */
		uint64_t t2 = now_us();
		old_close_context(v);
		old_context(v);
		v->reopenings++;
		force_next_key = true;
		*us_cod += now_us() - t2;
	}
	return true;
}

static void old_close(Old *v)
{
	old_close_context(v);
	sws_freeContext(v->sws);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * THE MODES
 * ═══════════════════════════════════════════════════════════════════════════ */
static int compare(const uint8_t *a, const uint8_t *b, size_t n, int *maximum,
                     double *media, size_t *different)
{
	uint64_t s = 0;
	*maximum = 0;
	*different = 0;
	for (size_t i = 0; i < n; i++) {
		int d = abs((int) a[i] - (int) b[i]);
		if (d > *maximum)
			*maximum = d;
		s += (uint64_t) d;
		if (d)
			(*different)++;
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

static int median_u64(const void *x, const void *y)
{
	uint64_t a = *(const uint64_t *) x, b = *(const uint64_t *) y;
	return a < b ? -1 : a > b;
}

static int color_mode(uint32_t l, uint32_t a, const char *dir, int n)
{
	Scene s;
	scene_open(&s, l, a, dir);
	size_t ny = (size_t) l * a, nc = ny / 4;
	uint8_t *our = aligned_alloc(64, ny * 3 / 2 + 64);
	uint8_t *its = aligned_alloc(64, ny * 3 / 2 + 64);
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
		scene_frame(&s, i * (120 / n));
		uint64_t t0 = now_us();
		colori709_a_i420(s.frame_buf, l * 4, l, a, COLORI709_BGRX, our, l, our + ny, l / 2,
		                 our + ny + nc, l / 2);
		t_n[i] = now_us() - t0;
		const uint8_t *pi[4] = { s.frame_buf };
		int pa[4] = { (int) l * 4 };
		uint8_t *po[4] = { its, its + ny, its + ny + nc };
		int ps[4] = { (int) l, (int) l / 2, (int) l / 2 };
		t0 = now_us();
		sws_scale(sws, pi, pa, 0, (int) a, po, ps);
		t_s[i] = now_us() - t0;
		t0 = now_us();
		ARGBToI420(s.frame_buf, (int) l * 4, yuv, (int) l, yuv + ny, (int) l / 2, yuv + ny + nc,
		           (int) l / 2, (int) l, (int) a);
		t_y[i] = now_us() - t0;
		t0 = now_us();
		colori709_a_i420_10(s.frame_buf, l * 4, l, a, COLORI709_BGRX, n10, l * 2, n10 + ny,
		                    l, n10 + ny + nc, l);
		t_n10[i] = now_us() - t0;
		uint8_t *po10[4] = { (uint8_t *) s10, (uint8_t *) (s10 + ny), (uint8_t *) (s10 + ny + nc) };
		int ps10[4] = { (int) l * 2, (int) l, (int) l };
		t0 = now_us();
		sws_scale(sws10, pi, pa, 0, (int) a, po10, ps10);
		t_s10[i] = now_us() - t0;

		if (i == 0) {
			/* the fingerprint of the output: the SSE2 route and the plain C one
			 * must give the SAME bytes (the bench is compiled twice) */
			uint64_t h = 1469598103934665603u, h10 = h;
			for (size_t q = 0; q < ny * 3 / 2; q++)
				h = (h ^ our[q]) * 1099511628211u;
			for (size_t q = 0; q < ny * 3 / 2; q++)
				h10 = (h10 ^ n10[q]) * 1099511628211u;
			printf("  fingerprint of the output (frame 0): 8 bit %016" PRIx64 " · 10 bit %016" PRIx64 "\n", h, h10);
		}
		int m;
		double med;
		size_t d;
		compare(our, its, ny, &m, &med, &d);
		if (m > mY)
			mY = m;
		dY += d;
		compare(our + ny, its + ny, nc, &m, &med, &d);
		if (m > mU)
			mU = m;
		dC += d;
		compare(our + ny + nc, its + ny + nc, nc, &m, &med, &d);
		if (m > mV)
			mV = m;
		dC += d;
		double q = psnr8(our, its, ny);
		if (q < pY)
			pY = q;
		q = psnr8(our + ny, its + ny, nc);
		if (q < pU)
			pU = q;
		q = psnr8(our + ny + nc, its + ny + nc, nc);
		if (q < pV)
			pV = q;
		q = psnr8(yuv, its, ny);
		if (q < py601)
			py601 = q;
		q = psnr8(yuv + ny, its + ny, nc);
		if (q < pu601)
			pu601 = q;
		for (size_t k = 0; k < ny * 3 / 2; k++) {
			int dd = abs((int) n10[k] - (int) s10[k]);
			if (dd > m10)
				m10 = dd;
		}
	}
	qsort(t_n, (size_t) n, 8, median_u64);
	qsort(t_s, (size_t) n, 8, median_u64);
	qsort(t_y, (size_t) n, 8, median_u64);
	qsort(t_n10, (size_t) n, 8, median_u64);
	qsort(t_s10, (size_t) n, 8, median_u64);
	printf("colours %ux%u, %d frames, medians:\n", l, a, n);
	printf("  time 8 bit : ours %.2f ms · sws_scale %.2f ms · libyuv ARGBToI420 (BT.601!) %.2f ms\n",
	       t_n[n / 2] / 1000.0, t_s[n / 2] / 1000.0, t_y[n / 2] / 1000.0);
	printf("  time 10 bit: ours %.2f ms · sws_scale %.2f ms\n", t_n10[n / 2] / 1000.0,
	       t_s10[n / 2] / 1000.0);
	printf("  gap ours/sws 8 bit: Y max %d (%.4f%% of samples differ) · U max %d · V max %d "
	       "(chroma differs %.4f%%) · minimum PSNR Y %.2f U %.2f V %.2f dB\n",
	       mY, 100.0 * (double) dY / ((double) ny * n), mU, mV,
	       100.0 * (double) dC / (2.0 * nc * n), pY, pU, pV);
	printf("  gap ours/sws 10 bit: max %d levels out of 1023\n", m10);
	printf("  libyuv (BT.601) against sws (BT.709): minimum PSNR Y %.2f U %.2f dB  ⛔ wrong matrix\n",
	       py601, pu601);
	/* the greys and the primaries, by hand */
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
		printf("  BGRx %06x → ours Y %3u U %3u V %3u · sws Y %3u U %3u V %3u\n", prove[i], y[0],
		       u[0], v[0], ys[0], us[0], vs[0]);
	}
	int bad_grays = 0;
	for (int g = 0; g < 256; g++) {
		for (int k = 0; k < 8; k++) {
			px[4 * k] = px[4 * k + 1] = px[4 * k + 2] = (uint8_t) g;
			px[4 * k + 3] = 0;
		}
		uint8_t y[8], u[2], v[2];
		colori709_a_i420(px, 16, 4, 2, COLORI709_BGRX, y, 4, u, 2, v, 2);
		if (u[0] != 128 || v[0] != 128)
			bad_grays++;
	}
	printf("  greys with chroma other than 128: %d out of 256\n", bad_grays);

	/* ⭐ NV12 and P010: the card route when the pixels come from
	 *    memory (the card line, 30 Sep: the VPP there is worse than swscale).
	 *    Same comparison, against sws_scale to NV12 / P010LE. */
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
		int rounds = n < 8 ? n : 8;
		for (int i = 0; i < rounds; i++) {
			scene_frame(&s, i * (120 / rounds));
			const uint8_t *pi[4] = { s.frame_buf };
			int pa[4] = { (int) l * 4 };
			uint64_t t0 = now_us();
			colors709_to_nv12(s.frame_buf, l * 4, l, a, COLORI709_BGRX, our, l, our + ny, l);
			tn += now_us() - t0;
			uint8_t *po[4] = { its, its + ny };
			int ps[4] = { (int) l, (int) l };
			t0 = now_us();
			sws_scale(s12, pi, pa, 0, (int) a, po, ps);
			ts += now_us() - t0;
			for (size_t k = 0; k < ny * 3 / 2; k++) {
				int dd = abs((int) our[k] - (int) its[k]);
				if (dd > m12)
					m12 = dd;
			}
			double q = psnr8(our, its, ny * 3 / 2);
			if (q < p12)
				p12 = q;
			t0 = now_us();
			colors709_to_p010(s.frame_buf, l * 4, l, a, COLORI709_BGRX, n10, l * 2, n10 + ny, l * 2);
			tn10 += now_us() - t0;
			uint8_t *po10[4] = { (uint8_t *) s10, (uint8_t *) (s10 + ny) };
			int ps10[4] = { (int) l * 2, (int) l * 2 };
			t0 = now_us();
			sws_scale(s010, pi, pa, 0, (int) a, po10, ps10);
			ts10 += now_us() - t0;
			for (size_t k = 0; k < ny * 3 / 2; k++) {
				int dd = abs((int) (n10[k] >> 6) - (int) (s10[k] >> 6));
				if (dd > m010)
					m010 = dd;
			}
		}
		printf("  NV12: ours %.2f ms · sws %.2f ms (averages) · max gap %d · minimum PSNR %.2f dB\n",
		       tn / 1000.0 / rounds, ts / 1000.0 / rounds, m12, p12);
		printf("  P010: ours %.2f ms · sws %.2f ms (averages) · max gap %d levels out of 1023\n",
		       tn10 / 1000.0 / rounds, ts10 / 1000.0 / rounds, m010);
		sws_freeContext(s12);
		sws_freeContext(s010);
	}
	/* RGBx (labwc): the same frame with the R and B bytes swapped must give
	 * THE SAME YUV bytes as BGRx on the original. */
	{
		scene_frame(&s, 30);
		colori709_a_i420(s.frame_buf, l * 4, l, a, COLORI709_BGRX, our, l, our + ny, l / 2,
		                 our + ny + nc, l / 2);
		for (size_t k = 0; k < ny; k++) {
			uint8_t tmp = s.frame_buf[4 * k];
			s.frame_buf[4 * k] = s.frame_buf[4 * k + 2];
			s.frame_buf[4 * k + 2] = tmp;
		}
		colori709_a_i420(s.frame_buf, l * 4, l, a, COLORI709_RGBX, its, l, its + ny, l / 2,
		                 its + ny + nc, l / 2);
		printf("  RGBx swapped against BGRx: %s\n",
		       memcmp(our, its, ny * 3 / 2) ? "⛔ DIFFERENT" : "identical bytes");
	}
	return 0;
}

static int source_mode(uint32_t l, uint32_t a, const char *dir, int n, const char *output)
{
	Scene s;
	scene_open(&s, l, a, dir);
	FILE *f = fopen(output, "wb");
	for (int i = 0; i < n; i++) {
		scene_frame(&s, i);
		fwrite(s.frame_buf, 1, (size_t) l * a * 4, f);
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
	die("codec: h264, av1 or hevc");
	return 0;
}

static CodificatoreRichiesta request(CodecVideo codec, uint32_t l, uint32_t a)
{
	CodificatoreRichiesta r;
	memset(&r, 0, sizeof r);
	r.codec = codec;
	r.width = l;
	r.height = a;
	r.fotogrammi_al_secondo = 60;
	r.mode = CODIFICATORE_QUALITA_CRF;
	const char *q = getenv("QUALITY");
	r.quality = q ? atoi(q) : 20; /* ⭐ CRF_SOFTWARE of `figlio.c` */
	const char *p = getenv("DEPTH");
	r.depth = p ? atoi(p) : 8;
	const char *lv = getenv("LEVEL");
	r.livello_x10 = lv ? atoi(lv) : 0;
	r.fmt = ENCODER_PIXEL_BGRX;
	return r;
}

static int encoding_mode(CodecVideo codec, bool new, uint32_t l, uint32_t a, const char *dir,
                         int n, const char *output, int key_at)
{
	Scene s;
	scene_open(&s, l, a, dir);
	CodificatoreRichiesta r = request(codec, l, a);
	char err[512] = "";
	char csv[600];
	snprintf(csv, sizeof csv, "%s.csv", output);
	FILE *fo = fopen(output, "wb"), *fc = fopen(csv, "w");
	fprintf(fc, "n,byte,chiave,us_conv,us_cod,chiesta\n");
	Ripiego *rp = NULL;
	Old v;
	uint64_t t0 = now_us();
	if (new) {
		rp = ripiego_apri(&r, err, sizeof err);
		if (!rp) {
			fprintf(stderr, "⛔ ripiego_apri: %s\n", err);
			return 1;
		}
		fprintf(stderr, "opened: %s\n", ripiego_nome(rp));
	} else if (old_open(&v, codec, l, a, r.depth, r.quality, r.livello_x10) < 0) {
		die("old route not opened");
	}
	uint64_t opening_us = now_us() - t0;
	uint64_t tot_conv = 0, tot_cod = 0, tot_byte = 0;
	int keys = 0, missed_key = 0, reopenings = 0;
	for (int i = 0; i < n; i++) {
		scene_frame(&s, i);
		bool ask = (i == key_at);
		uint64_t uc = 0, ue = 0;
		bool k = false;
		const uint8_t *d;
		size_t b;
		uint8_t *dv = NULL;
		if (new) {
			RipiegoUscita u;
			if (!ripiego_codifica(rp, s.frame_buf, l * 4, ask, &u)) {
				fprintf(stderr, "⛔ frame %d not encoded\n", i);
				return 1;
			}
			uc = u.us_conversione;
			ue = u.us_codifica;
			k = u.key;
			d = u.data;
			b = u.byte;
		} else {
			bool rip;
			if (!old_encoding(&v, s.frame_buf, ask, &uc, &ue, &k, &dv, &b, &rip)) {
				fprintf(stderr, "⛔ frame %d not encoded (old)\n", i);
				return 1;
			}
			d = dv;
			reopenings += rip;
		}
		fwrite(d, 1, b, fo);
		fprintf(fc, "%d,%zu,%d,%" PRIu64 ",%" PRIu64 ",%d\n", i, b, k, uc, ue, ask);
		tot_conv += uc;
		tot_cod += ue;
		tot_byte += b;
		keys += k;
		if (ask && !k)
			missed_key++;
		free(dv);
	}
	fclose(fo);
	fclose(fc);
	printf("%s %s %ux%u: %d frames · opening %.1f ms · average conversion %.2f ms · "
	       "average encoding %.2f ms · %.1f KiB/frame · keys %d · key requested at %d %s · "
	       "reopenings for EAGAIN %d\n",
	       codec == CODIFICATORE_H264 ? "H.264" : "AV1", route, l, a, n,
	       opening_us / 1000.0, tot_conv / 1000.0 / n, tot_cod / 1000.0 / n,
	       tot_byte / 1024.0 / n, keys, key_at,
	       key_at < 0 ? "-" : missed_key ? "⛔ NOT EMITTED" : "emitted",
	       new ? 0 : v.reopenings);
	if (new)
		ripiego_chiudi(rp);
	else
		old_close(&v);
	return 0;
}

/* key on request, quality on the fly, new size: times and stream */
static int events_mode(CodecVideo codec, bool new, uint32_t l, uint32_t a, const char *dir,
                       const char *output)
{
	Scene s, s2;
	scene_open(&s, l, a, dir);
	uint32_t l2 = l == 3840 ? 1920 : 3840, a2 = l == 3840 ? 1080 : 2160;
	scene_open(&s2, l2, a2, dir);
	CodificatoreRichiesta r = request(codec, l, a);
	char err[512] = "";
	FILE *fo = fopen(output, "wb");
	Ripiego *rp = NULL;
	Old v;
	if (new) {
		rp = ripiego_apri(&r, err, sizeof err);
		if (!rp) {
			fprintf(stderr, "⛔ %s\n", err);
			return 1;
		}
	} else {
		old_open(&v, codec, l, a, r.depth, r.quality, r.livello_x10);
	}
	/* 0-9 size 1 (key requested at 5), 10: quality +9 (the drop of
	 * `lower_quality()`), 15: quality back down, 20-29 size 2 */
	for (int i = 0; i < 30; i++) {
		Scene *sc = i < 20 ? &s : &s2;
		uint32_t ll = i < 20 ? l : l2, aa = i < 20 ? a : a2;
		const char *event = "";
		uint64_t us_ev = 0;
		bool ask = (i == 5);
		if (i == 10 || i == 15 || i == 20) {
			uint64_t t0 = now_us();
			int q = i == 10 ? r.quality + 9 : r.quality;
			if (new) {
				bool ok = i == 20 ? ripiego_ridimensiona(rp, l2, a2, err, sizeof err)
				                  : ripiego_qualita(rp, r.mode, q, err, sizeof err);
				if (!ok) {
					fprintf(stderr, "⛔ event %d: %s\n", i, err);
					return 1;
				}
			} else {
				old_close(&v);
				old_open(&v, codec, ll, aa, r.depth, q, r.livello_x10);
			}
			us_ev = now_us() - t0;
			event = i == 10 ? "quality +9 (reopening)" : i == 15 ? "quality -9 (reopening)"
			                                                        : "new size (reopening)";
			ask = true;
		}
		scene_frame(sc, i * 3);
		uint64_t uc = 0, ue = 0;
		bool k = false;
		const uint8_t *d;
		size_t b;
		uint8_t *dv = NULL;
		if (new) {
			RipiegoUscita u;
			if (!ripiego_codifica(rp, sc->frame_buf, ll * 4, ask, &u)) {
				fprintf(stderr, "⛔ frame %d\n", i);
				return 1;
			}
			ue = u.us_codifica;
			uc = u.us_conversione;
			k = u.key;
			d = u.data;
			b = u.byte;
		} else {
			bool rip;
			if (!old_encoding(&v, sc->frame_buf, ask, &uc, &ue, &k, &dv, &b, &rip))
				return 1;
			d = dv;
		}
		fwrite(d, 1, b, fo);
		if (*event || ask || i == 0 || i == 21)
			printf("  %s %s frame %2d %ux%u: %s%s%.1f ms of event · encoding %.1f ms · "
			       "%zu bytes · %s%s\n",
			       codec == CODIFICATORE_H264 ? "H.264" : "AV1", route, i,
			       ll, aa, event, *event ? " " : "", us_ev / 1000.0, ue / 1000.0, b,
			       k ? "KEY" : "delta", ask && !k ? " ⛔ requested and not emitted" : "");
		free(dv);
	}
	fclose(fo);
	if (new)
		ripiego_chiudi(rp);
	else
		old_close(&v);
	return 0;
}

static int refusals_mode(void)
{
	struct {
		const char *what;
		CodecVideo codec;
		uint32_t l, a;
		int prof;
		ModoQualita mode;
	} cases[] = {
		{ "HEVC 1080p", CODIFICATORE_HEVC, 1920, 1080, 8, CODIFICATORE_QUALITA_CRF },
		{ "H.264 10 bit", CODIFICATORE_H264, 1920, 1080, 10, CODIFICATORE_QUALITA_CRF },
		{ "H.264 lossless", CODIFICATORE_H264, 1920, 1080, 8, CODIFICATORE_QUALITA_LOSSLESS },
		{ "H.264 4096x2304", CODIFICATORE_H264, 4096, 2304, 8, CODIFICATORE_QUALITA_CRF },
		{ "H.264 5120x2880", CODIFICATORE_H264, 5120, 2880, 8, CODIFICATORE_QUALITA_CRF },
		{ "H.264 7680x4320", CODIFICATORE_H264, 7680, 4320, 8, CODIFICATORE_QUALITA_CRF },
		{ "H.264 5120x1440", CODIFICATORE_H264, 5120, 1440, 8, CODIFICATORE_QUALITA_CRF },
		{ "AV1 7680x4320", CODIFICATORE_AV1, 7680, 4320, 8, CODIFICATORE_QUALITA_CRF },
		{ "AV1 lossless", CODIFICATORE_AV1, 1920, 1080, 8, CODIFICATORE_QUALITA_LOSSLESS },
		{ "AV1 10 bit 1080p", CODIFICATORE_AV1, 1920, 1080, 10, CODIFICATORE_QUALITA_CRF },
	};
	for (size_t i = 0; i < sizeof cases / sizeof *cases; i++) {
		CodificatoreRichiesta r = request(cases[i].codec, cases[i].l, cases[i].a);
		r.depth = cases[i].prof;
		r.mode = cases[i].mode;
		char why[512] = "";
		uint64_t t0 = now_us();
		Ripiego *rp = ripiego_apri(&r, why, sizeof why);
		double ms = (now_us() - t0) / 1000.0;
		if (rp) {
			/* and a real frame, if it opened: grey with a gradient */
			size_t np = (size_t) r.width * r.height * 4;
			uint8_t *px = malloc(np);
			for (size_t k = 0; k < np; k++)
				px[k] = (uint8_t) (k / 4 % r.width * 255 / r.width);
			RipiegoUscita u;
			bool ok = ripiego_codifica(rp, px, r.width * 4, true, &u);
			printf("  %-22s opens (%.0f ms) · %s · first frame %s, %zu bytes\n", cases[i].what,
			       ms, ripiego_nome(rp), ok ? "EMITTED" : "⛔ NOT emitted", ok ? u.byte : 0);
			if (ok && getenv("DUMP_DIR")) {
				char name[128];
				snprintf(name, sizeof name, "%s/rifiuto-%zu.%s", getenv("DUMP_DIR"), i,
				         cases[i].codec == CODIFICATORE_H264 ? "h264" : "obu");
				FILE *f = fopen(name, "wb");
				fwrite(u.data, 1, u.byte, f);
				fclose(f);
			}
			free(px);
			ripiego_chiudi(rp);
		} else {
			printf("  %-22s REFUSED: %s\n", cases[i].what, why);
		}
	}
	return 0;
}

int main(int argc, char **argv)
{
	if (argc >= 4) {
		route = argv[3];
		/* ⭐ The "fixed" is the old one with the TWO lines it was missing
		 *    (`[M]` 30 Sep 2026, this bench): x264 turns `keyint=-1` into 1,
		 *    i.e. EVERY frame is an IDR; and without `force-cfr` x264 keeps
		 *    one frame in the pipe (`b_vfr_input`), i.e. EAGAIN and reopening
		 *    at every round.  It is the best x264 the product could have had. */
		if (!strcmp(route, "fixed"))
			setenv("OLD_X264_EXTRA", ":force-cfr=1:keyint=infinite", 1);
	}
	if (argc < 2)
		die("mode: colors | source | encode | events | refusals");
	const char *m = argv[1];
	if (!strcmp(m, "colors") && argc >= 6)
		return color_mode((uint32_t) atoi(argv[2]), (uint32_t) atoi(argv[3]), argv[4],
		                   atoi(argv[5]));
	if (!strcmp(m, "source") && argc >= 7)
		return source_mode((uint32_t) atoi(argv[2]), (uint32_t) atoi(argv[3]), argv[4],
		                     atoi(argv[5]), argv[6]);
	if (!strcmp(m, "encode") && argc >= 9)
		return encoding_mode(codec_di(argv[2]), !strcmp(argv[3], "new"),
		                     (uint32_t) atoi(argv[4]), (uint32_t) atoi(argv[5]), argv[6],
		                     atoi(argv[7]), argv[8], argc >= 10 ? atoi(argv[9]) : -1);
	if (!strcmp(m, "events") && argc >= 8)
		return events_mode(codec_di(argv[2]), !strcmp(argv[3], "new"),
		                   (uint32_t) atoi(argv[4]), (uint32_t) atoi(argv[5]), argv[6], argv[7]);
	if (!strcmp(m, "refusals"))
		return refusals_mode();
	die("wrong arguments");
	return 1;
}
