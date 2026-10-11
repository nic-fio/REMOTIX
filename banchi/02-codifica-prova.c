/*
 * 02-codifica-prova.c — ⛔ the way the F2.3 BENCH points at the PRODUCT.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHY IT EXISTS
 *
 * The F2.3 bench was born before the product and measured `ffmpeg` from the
 * command line: it was the only thing that existed.  ⚠ A bench that stays pointed there
 * certifies **ffmpeg**, not our encoder — and it would be form E10 of
 * `REVIEWER.md` §2, *«a green test on the wrong client»*, with the wrong
 * defendant.
 *
 * ⇒ This program is a thin shell around `src/codificatore.c`:
 *   it reads a file of pixels, calls **the same three functions `main.c`
 *   will call**, writes the stream to disk and the confession as JSON.  From here
 *   on `02-codifica-lancia.sh ENCODER=product` measures the product with
 *   the **same** expectations it measured ffmpeg with.
 *
 * ⛔ And it contains no encoding logic: if it had any, it would measure
 *    itself.  Every decision — profile, bframes, Annex-B, the 16 MiB ceiling —
 *    sits in `codificatore.c` and is not repeated here.
 *
 *   banchi/02-codifica-prova --codec hevc|av1 --source F --output F \
 *       [--format yuv420p10le|bgrx] [--size 1920x1080] [--frames N] \
 *       [--lossless | --crf N] [--component NAME] [--depth 8|10] \
 *       [--key-interval N] [--confession F.json] [--resize LxA]
 *
 * ⚠ `--frames N` rereads the same frame N times: it is the way the
 *   bench requires **three groups of parameter sets on three keyframes**, which is the
 *   half that gets forgotten (a single frame has them necessarily).
 */
#include "../src/codificatore.h"

#include <inttypes.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void usage(void)
{
	fprintf(stderr,
	        "usage: 02-codifica-prova --codec hevc|av1 --source F --output F\n"
	        "     [--format yuv420p10le|bgrx] [--size LxA] [--frames N]\n"
	        "     [--lossless|--crf N] [--component NOME] [--depth 8|10]\n"
	        "     [--key-interval N] [--confession F] [--resize LxA]\n");
}

int main(int argc, char **argv)
{
	const char *source = NULL, *output = NULL, *confession = NULL;
	const char *componente = NULL;
	const char *resize = NULL;
	CodecVideo codec = CODIFICATORE_HEVC;
	FormatoPixel fmt = CODIFICATORE_PIXEL_YUV420P10LE;
	uint32_t width = 1920, height = 1080, frames = 1, chiavi_ogni = 0;
	int depth = 10, crf = 20;
	ModoQualita mode = CODIFICATORE_QUALITA_LOSSLESS;

	for (int i = 1; i < argc; i++) {
		const char *a = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;
		if (!strcmp(a, "--codec") && v) {
			codec = strcmp(v, "av1") == 0 ? CODIFICATORE_AV1 : CODIFICATORE_HEVC;
			i++;
		} else if (!strcmp(a, "--source") && v) {
			source = v; i++;
		} else if (!strcmp(a, "--output") && v) {
			output = v; i++;
		} else if (!strcmp(a, "--confession") && v) {
			confession = v; i++;
		} else if (!strcmp(a, "--component") && v) {
			componente = v; i++;
		} else if (!strcmp(a, "--format") && v) {
			fmt = strcmp(v, "bgrx") == 0 ? ENCODER_PIXEL_BGRX
			                                 : CODIFICATORE_PIXEL_YUV420P10LE;
			i++;
		} else if (!strcmp(a, "--size") && v) {
			sscanf(v, "%ux%u", &width, &height); i++;
		} else if (!strcmp(a, "--resize") && v) {
			resize = v; i++;
		} else if (!strcmp(a, "--frames") && v) {
			frames = (uint32_t) strtoul(v, NULL, 10); i++;
		} else if (!strcmp(a, "--key-interval") && v) {
			chiavi_ogni = (uint32_t) strtoul(v, NULL, 10); i++;
		} else if (!strcmp(a, "--depth") && v) {
			depth = atoi(v); i++;
		} else if (!strcmp(a, "--crf") && v) {
			mode = CODIFICATORE_QUALITA_CRF; crf = atoi(v); i++;
		} else if (!strcmp(a, "--lossless")) {
			mode = CODIFICATORE_QUALITA_LOSSLESS;
		} else {
			usage();
			return 2;
		}
	}
	if (!source || !output) {
		usage();
		return 2;
	}

	/* The input frame, read entirely into memory: it is the bench, not the
	 * product, and the real capture delivers a pointer to shared memory. */
	FILE *f = fopen(source, "rb");
	if (!f) {
		fprintf(stderr, "⛔ cannot open %s\n", source);
		return 2;
	}
	size_t expected_vals = (fmt == ENCODER_PIXEL_BGRX)
	                    ? (size_t) width * height * 4
	                    : (size_t) width * height * 3; /* 4:2:0 at 2 bytes = 3 per pixel */
	uint8_t *pixel = malloc(expected_vals);
	if (!pixel) {
		fclose(f);
		return 2;
	}
	size_t readings = fread(pixel, 1, expected_vals, f);
	fclose(f);
	if (readings != expected_vals) {
		/* ⛔ Three outcomes, not two: a short file is not «zero pixels», and it is not
		 *    encoded anyway by filling with zeros. */
		fprintf(stderr, "⛔ %s: read %zu bytes out of %zu expected for %ux%u\n", source,
		        readings, expected_vals, width, height);
		free(pixel);
		return 2;
	}

	CodificatoreRichiesta r = {
		.codec = codec,
		.componente = componente,
		.width = width,
		.height = height,
		.fotogrammi_al_secondo = 30,
		.mode = mode,
		.quality = crf,
		.depth = depth,
		.fmt = fmt,
		.chiavi_ogni = chiavi_ogni,
	};
	char error[512] = { 0 };
	Encoder *cod = codificatore_nuovo(&r, error, sizeof(error));
	if (!cod) {
		fprintf(stderr, "⛔ the encoder did not open: %s\n", error);
		free(pixel);
		return 1;
	}

	FILE *u = fopen(output, "wb");
	if (!u) {
		fprintf(stderr, "⛔ cannot write %s\n", output);
		codificatore_libera(cod);
		free(pixel);
		return 2;
	}

	uint32_t step = (fmt == ENCODER_PIXEL_BGRX) ? width * 4 : width * 2;
	uint64_t tot_conv = 0, tot_cod = 0;
	uint32_t keys = 0, shipped = 0;
	int state = 0;
	for (uint32_t k = 0; k < frames; k++) {
		if (chiavi_ogni == 0 && k > 0 && frames > 1)
			codificatore_chiedi_chiave(cod); /* the bench wants N keyframes */
		EncoderFrame fg;
		if (!codificatore_comprimi(cod, pixel, step, &fg)) {
			fprintf(stderr, "⛔ frame %u not produced\n", k);
			state = 1;
			break;
		}
		fwrite(fg.data, 1, fg.byte, u);
		tot_conv += fg.us_conversione;
		tot_cod += fg.us_codifica;
		keys += fg.key ? 1 : 0;
		shipped++;
		codificatore_rilascia(cod);
	}

	/* ⛔ The canvas change, when the bench asks for it: `RCP.md` §5.2 requires
	 *    the first frame at the new size to be a REAL keyframe. */
	if (!state && resize) {
		uint32_t l2 = 0, a2 = 0;
		sscanf(resize, "%ux%u", &l2, &a2);
		if (!codificatore_ridimensiona(cod, l2, a2, error, sizeof(error))) {
			fprintf(stderr, "⛔ resize failed: %s\n", error);
			state = 1;
		} else {
			size_t expected2 = (fmt == ENCODER_PIXEL_BGRX)
			                     ? (size_t) l2 * a2 * 4 : (size_t) l2 * a2 * 3;
			uint8_t *p2 = calloc(1, expected2);
			EncoderFrame fg;
			uint32_t stride2 = (fmt == ENCODER_PIXEL_BGRX) ? l2 * 4 : l2 * 2;
			if (!p2 || !codificatore_comprimi(cod, p2, stride2, &fg)) {
				fprintf(stderr, "⛔ no frame at the new size\n");
				state = 1;
			} else {
				fwrite(fg.data, 1, fg.byte, u);
				keys += fg.key ? 1 : 0;
				shipped++;
				codificatore_rilascia(cod);
			}
			free(p2);
		}
	}
	fclose(u);

	const EncoderConfession *c = codificatore_confessione(cod);
	FILE *j = confession ? fopen(confession, "w") : stdout;
	if (j) {
		fprintf(j,
		        "{\"name\": \"%s\", \"componente\": \"%s\", \"ha_obbedito\": %s,\n"
		        " \"perche_no\": \"%s\", \"profondita_chiesta\": %d, \"fotogrammi_b\": %d,\n"
		        " \"global_header\": %s, \"letto_dal_flusso\": %s, \"profondita_flusso\": %d,\n"
		        " \"profilo_flusso\": %d, \"livello_flusso\": %d, \"tier_alto\": %s,\n"
		        " \"larghezza_flusso\": %u, \"altezza_flusso\": %u, \"croma_flusso\": %d,\n"
		        " \"codec_string\": \"%s\", \"promozione_8_a_10\": %s, \"riordina\": %s,\n"
		        " \"fotogrammi_in_volo\": %u, \"fotogrammi_spediti\": %u, \"chiavi\": %u,\n"
		        " \"us_conversion\": %" PRIu64 ", \"us_encoding\": %" PRIu64 "}\n",
		        encoder_name(cod), c->componente ? c->componente : "?",
		        c->has_obeyed ? "true" : "false", c->why_no,
		        c->requested_depth, c->frames_b,
		        c->global_header ? "true" : "false",
		        c->read_from_stream ? "true" : "false", c->stream_depth,
		        c->stream_profile, c->stream_level, c->tier_alto ? "true" : "false",
		        c->stream_width, c->stream_height, c->stream_chroma,
		        c->codec_string, c->promotion_8_to_10 ? "true" : "false",
		        c->reorders ? "true" : "false", c->frames_in_flight, shipped, keys,
		        tot_conv, tot_cod);
		if (j != stdout)
			fclose(j);
	}
	codificatore_libera(cod);
	free(pixel);
	return state;
}
