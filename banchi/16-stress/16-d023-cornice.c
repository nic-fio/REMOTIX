/*
 * 16-d023-cornice.c — the test of D-023: the stream declares the size of the CANVAS.
 *
 * `[M]` 27 Sep 2026, Radeon RX 6800 (radeonsi 25.0.7): `hevc_vaapi` at 2544x1344
 * declared 2560x1344 — the multiple of 64, without a conformance window — and
 * the sessions with Chrome (HEVC, canvases never multiples of 64) stayed black.
 *
 * The program is a shell around `src/codificatore.c` and contains no
 * encoding logic: it encodes N BGRx frames of the requested size, with two
 * keyframes (the crop window must be written on EVERY SPS, not only on the first), and writes the
 * stream.  The judgement is given by `ffprobe` (the declared size) and by the PSNR
 * against the source (the image inside is that one, 1:1): `16-d023-cornice.sh`.
 *
 *   16-d023-cornice --codec hevc|h264 --size LxA --node /dev/dri/renderD128 \
 *       --source F.bgrx --output F [--frames N]
 */
#include "../../src/codificatore.h"

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

int main(int argc, char **argv)
{
	const char *source = NULL, *output = NULL, *node = "/dev/dri/renderD128";
	CodecVideo codec = CODIFICATORE_HEVC;
	uint32_t l = 0, a = 0, n = 10;

	for (int i = 1; i + 1 < argc; i += 2) {
		const char *k = argv[i], *v = argv[i + 1];
		if (!strcmp(k, "--codec"))
			codec = strcmp(v, "h264") == 0 ? CODIFICATORE_H264 : CODIFICATORE_HEVC;
		else if (!strcmp(k, "--size"))
			sscanf(v, "%ux%u", &l, &a);
		else if (!strcmp(k, "--node"))
			node = v;
		else if (!strcmp(k, "--source"))
			source = v;
		else if (!strcmp(k, "--output"))
			output = v;
		else if (!strcmp(k, "--frames"))
			n = (uint32_t) strtoul(v, NULL, 10);
	}
	if (!source || !output || !l || !a) {
		fprintf(stderr, "usage: 16-d023-cornice --codec hevc|h264 --size LxA "
		                "--source F.bgrx --output F [--node N] [--frames N]\n");
		return 2;
	}

	size_t byte = (size_t) l * a * 4;
	uint8_t *pixel = malloc(byte);
	FILE *f = fopen(source, "rb");
	if (!pixel || !f || fread(pixel, 1, byte, f) != byte) {
		fprintf(stderr, "⛔ %s: there are not %zu bytes of BGRx %ux%u\n", source, byte, l, a);
		return 2;
	}
	fclose(f);

	CodificatoreRichiesta r = {
		.codec = codec,
		.componente = codec == CODIFICATORE_H264 ? "h264_vaapi" : "hevc_vaapi",
		.nodo_rendering = node,
		.power = ENCODER_POWER_DECLARED,
		.width = l,
		.height = a,
		.fotogrammi_al_secondo = 30,
		.mode = CODIFICATORE_QUALITA_QP,
		.quality = 26,
		.depth = 8,
		.fmt = ENCODER_PIXEL_BGRX,
	};
	char error[512] = { 0 };
	Encoder *cod = codificatore_nuovo(&r, error, sizeof(error));
	if (!cod) {
		fprintf(stderr, "⛔ the encoder did not open: %s\n", error);
		return 1;
	}
	FILE *u = fopen(output, "wb");
	if (!u)
		return 2;
	uint32_t shipped = 0, keys = 0;
	for (uint32_t k = 0; k < n; k++) {
		if (k == n / 2)
			codificatore_chiedi_chiave(cod);
		EncoderFrame fg;
		if (!codificatore_comprimi(cod, pixel, l * 4, &fg)) {
			fprintf(stderr, "⛔ frame %u not produced (see the log)\n", k);
			break;
		}
		fwrite(fg.data, 1, fg.byte, u);
		shipped++;
		keys += fg.key;
		codificatore_rilascia(cod);
	}
	fclose(u);
	printf("%s %ux%u: %u frames of %u, %u keyframes · %s\n",
	       codec == CODIFICATORE_H264 ? "h264" : "hevc", l, a, shipped, n, keys,
	       encoder_name(cod));
	codificatore_libera(cod);
	free(pixel);
	return shipped == n ? 0 : 1;
}
