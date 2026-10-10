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
 *   banchi/02-codifica-prova --codec hevc|av1 --source F --out_dir F \
 *       [--schema yuv420p10le|bgrx] [--gauge 1920x1080] [--frames N] \
 *       [--lossless | --crf N] [--component LABEL_NAME] [--bit_depth 8|10] \
 *       [--keys-every N] [--confession F.json] [--resize LxA]
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

static void use(void)
{
	fprintf(stderr,
	        "usage: 02-codifica-prova --codec hevc|av1 --source F --out_dir F\n"
	        "     [--schema yuv420p10le|bgrx] [--gauge LxA] [--frames N]\n"
	        "     [--lossless|--crf N] [--component LABEL_NAME] [--bit_depth 8|10]\n"
	        "     [--keys-every N] [--confession F] [--resize LxA]\n");
}

int main(int argc, char **argv)
{
	const char *source = NULL, *out_dir = NULL, *confession = NULL;
	const char *component = NULL;
	const char *resize = NULL;
	CodecVideo codec = ENCODER_HEVC;
	PixelFormat schema = ENCODER_PIXEL_YUV420P10;
	uint32_t width_px = 1920, height_px = 1080, frames = 1, keys_every = 0;
	int bit_depth = 10, crf = 20;
	QualityMode manner = ENCODER_QUALITY_LOSSLESS;

	for (int i = 1; i < argc; i++) {
		const char *a = argv[i];
		const char *v = (i + 1 < argc) ? argv[i + 1] : NULL;
		if (!strcmp(a, "--codec") && v) {
			codec = strcmp(v, "av1") == 0 ? ENCODER_AV1 : ENCODER_HEVC;
			i++;
		} else if (!strcmp(a, "--source") && v) {
			source = v; i++;
		} else if (!strcmp(a, "--out_dir") && v) {
			out_dir = v; i++;
		} else if (!strcmp(a, "--confession") && v) {
			confession = v; i++;
		} else if (!strcmp(a, "--component") && v) {
			component = v; i++;
		} else if (!strcmp(a, "--schema") && v) {
			schema = strcmp(v, "bgrx") == 0 ? ENCODER_PIXEL_BGRX
			                                 : ENCODER_PIXEL_YUV420P10;
			i++;
		} else if (!strcmp(a, "--gauge") && v) {
			sscanf(v, "%ux%u", &width_px, &height_px); i++;
		} else if (!strcmp(a, "--resize") && v) {
			resize = v; i++;
		} else if (!strcmp(a, "--frames") && v) {
			frames = (uint32_t) strtoul(v, NULL, 10); i++;
		} else if (!strcmp(a, "--keys-every") && v) {
			keys_every = (uint32_t) strtoul(v, NULL, 10); i++;
		} else if (!strcmp(a, "--bit_depth") && v) {
			bit_depth = atoi(v); i++;
		} else if (!strcmp(a, "--crf") && v) {
			manner = ENCODER_QUALITY_CRF; crf = atoi(v); i++;
		} else if (!strcmp(a, "--lossless")) {
			manner = ENCODER_QUALITY_LOSSLESS;
		} else {
			use();
			return 2;
		}
	}
	if (!source || !out_dir) {
		use();
		return 2;
	}

	/* The input frame, read entirely into memory: it is the bench, not the
	 * product, and the real capture delivers a pointer to shared memory. */
	FILE *f = fopen(source, "rb");
	if (!f) {
		fprintf(stderr, "⛔ cannot open %s\n", source);
		return 2;
	}
	size_t expected_vals = (schema == ENCODER_PIXEL_BGRX)
	                    ? (size_t) width_px * height_px * 4
	                    : (size_t) width_px * height_px * 3; /* 4:2:0 at 2 bytes = 3 per pixel */
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
		        readings, expected_vals, width_px, height_px);
		free(pixel);
		return 2;
	}

	EncoderRequest r = {
		.codec = codec,
		.component = component,
		.width_px = width_px,
		.height_px = height_px,
		.frames_per_second = 30,
		.manner = manner,
		.quality = crf,
		.bit_depth = bit_depth,
		.schema = schema,
		.keys_every = keys_every,
	};
	char failure[512] = { 0 };
	Encoder *cod = encoder_new(&r, failure, sizeof(failure));
	if (!cod) {
		fprintf(stderr, "⛔ the encoder did not open: %s\n", failure);
		free(pixel);
		return 1;
	}

	FILE *u = fopen(out_dir, "wb");
	if (!u) {
		fprintf(stderr, "⛔ cannot write %s\n", out_dir);
		encoder_free(cod);
		free(pixel);
		return 2;
	}

	uint32_t step = (schema == ENCODER_PIXEL_BGRX) ? width_px * 4 : width_px * 2;
	uint64_t tot_conv = 0, tot_cod = 0;
	uint32_t keys = 0, shipped = 0;
	int state = 0;
	for (uint32_t k = 0; k < frames; k++) {
		if (keys_every == 0 && k > 0 && frames > 1)
			encoder_ask_key(cod); /* the bench wants N keyframes */
		EncoderFrame fg;
		if (!encoder_compress(cod, pixel, step, &fg)) {
			fprintf(stderr, "⛔ frame %u not produced\n", k);
			state = 1;
			break;
		}
		fwrite(fg.data_v, 1, fg.byte, u);
		tot_conv += fg.convert_us;
		tot_cod += fg.encode_us;
		keys += fg.key_id ? 1 : 0;
		shipped++;
		encoder_release(cod);
	}

	/* ⛔ The canvas change, when the bench asks for it: `RCP.md` §5.2 requires
	 *    the first frame at the new size to be a REAL keyframe. */
	if (!state && resize) {
		uint32_t l2 = 0, a2 = 0;
		sscanf(resize, "%ux%u", &l2, &a2);
		if (!encoder_resize(cod, l2, a2, failure, sizeof(failure))) {
			fprintf(stderr, "⛔ resize failed: %s\n", failure);
			state = 1;
		} else {
			size_t expected2 = (schema == ENCODER_PIXEL_BGRX)
			                     ? (size_t) l2 * a2 * 4 : (size_t) l2 * a2 * 3;
			uint8_t *p2 = calloc(1, expected2);
			EncoderFrame fg;
			uint32_t stride2 = (schema == ENCODER_PIXEL_BGRX) ? l2 * 4 : l2 * 2;
			if (!p2 || !encoder_compress(cod, p2, stride2, &fg)) {
				fprintf(stderr, "⛔ no frame at the new size\n");
				state = 1;
			} else {
				fwrite(fg.data_v, 1, fg.byte, u);
				keys += fg.key_id ? 1 : 0;
				shipped++;
				encoder_release(cod);
			}
			free(p2);
		}
	}
	fclose(u);

	const EncoderConfession *c = encoder_confession(cod);
	FILE *j = confession ? fopen(confession, "w") : stdout;
	if (j) {
		fprintf(j,
		        "{\"label_name\": \"%s\", \"component\": \"%s\", \"has_obeyed\": %s,\n"
		        " \"why_no\": \"%s\", \"requested_depth\": %d, \"frames_b\": %d,\n"
		        " \"global_header\": %s, \"read_from_stream\": %s, \"stream_depth\": %d,\n"
		        " \"stream_profile\": %d, \"stream_level\": %d, \"tier_alto\": %s,\n"
		        " \"stream_width\": %u, \"stream_height\": %u, \"stream_chroma\": %d,\n"
		        " \"codec_string\": \"%s\", \"promotion_8_to_10\": %s, \"reorders\": %s,\n"
		        " \"frames_in_flight\": %u, \"fotogrammi_spediti\": %u, \"keys\": %u,\n"
		        " \"convert_us\": %" PRIu64 ", \"encode_us\": %" PRIu64 "}\n",
		        encoder_name(cod), c->component ? c->component : "?",
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
	encoder_free(cod);
	free(pixel);
	return state;
}
