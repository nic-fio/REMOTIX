/*
 * parita.c — the second half of the F4-IN-8 question: Mutter accepts an
 * odd size, but does the ENCODER accept it?  The three of `codificatore.c`:
 * libx265, libsvtav1, hevc_vaapi.
 *
 *   parita <L> <A>
 */
#include <libavcodec/avcodec.h>
#include <libavutil/opt.h>
#include <libavutil/pixdesc.h>
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

static void prova(const char *nome, int l, int a, enum AVPixelFormat pf)
{
	const AVCodec *c = avcodec_find_encoder_by_name(nome);
	AVCodecContext *ctx;
	AVFrame *f;
	AVPacket *p;
	int e;

	if (!c) { printf("  %-12s  NOT THERE\n", nome); return; }
	ctx = avcodec_alloc_context3(c);
	ctx->width = l;
	ctx->height = a;
	ctx->pix_fmt = pf;
	ctx->time_base = (AVRational){1, 60};
	ctx->framerate = (AVRational){60, 1};
	e = avcodec_open2(ctx, c, NULL);
	if (e < 0) {
		char b[256];
		av_strerror(e, b, sizeof b);
		printf("  %-12s  %dx%d %-12s  ⛔ OPEN REFUSED: %s\n", nome, l, a,
		       av_get_pix_fmt_name(pf), b);
		avcodec_free_context(&ctx);
		return;
	}
	/* ⛔ Opening is not enough: an encoder can open and then refuse the
	 *    frame.  A real frame is pushed and the outcome is looked at. */
	f = av_frame_alloc();
	f->format = pf;
	f->width = l;
	f->height = a;
	if (av_frame_get_buffer(f, 0) < 0) {
		printf("  %-12s  %dx%d  ⛔ the frame cannot be allocated\n", nome, l, a);
		goto fine;
	}
	memset(f->data[0], 32, (size_t) f->linesize[0] * a);
	f->pts = 0;
	e = avcodec_send_frame(ctx, f);
	if (e < 0) {
		char b[256];
		av_strerror(e, b, sizeof b);
		printf("  %-12s  %dx%d %-12s  ⚠ opened, but the FRAME is refused: %s\n", nome,
		       l, a, av_get_pix_fmt_name(pf), b);
		goto fine;
	}
	avcodec_send_frame(ctx, NULL);
	p = av_packet_alloc();
	e = avcodec_receive_packet(ctx, p);
	printf("  %-12s  %dx%d %-12s  ⭐ OPENED (coded %dx%d), first packet: %s (%d bytes)\n",
	       nome, l, a, av_get_pix_fmt_name(pf), ctx->width, ctx->height,
	       e >= 0 ? "YES" : (e == AVERROR(EAGAIN) ? "pending" : "NO"), e >= 0 ? p->size : 0);
	av_packet_free(&p);
fine:
	av_frame_free(&f);
	avcodec_free_context(&ctx);
}

int main(int argc, char **argv)
{
	int l = argc > 1 ? atoi(argv[1]) : 2133;
	int a = argc > 2 ? atoi(argv[2]) : 772;

	av_log_set_level(AV_LOG_ERROR);
	printf("== %dx%d ==\n", l, a);
	prova("libx265", l, a, AV_PIX_FMT_YUV420P10LE);
	prova("libsvtav1", l, a, AV_PIX_FMT_YUV420P10LE);
	prova("hevc_vaapi", l, a, AV_PIX_FMT_VAAPI);
	return 0;
}
