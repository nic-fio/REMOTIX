/*
 * The test of the wasm decoder against NATIVE libopus (D-006).
 *
 *   cc -O2 riferimento.c -lopus -lm -o riferimento
 *   ./riferimento pacchetti.bin attesi.f32
 *
 * Encodes 12 s of stereo signal at 48 kHz, 20 ms per packet, with Opus's three
 * modes (CELT at 96 kbit/s like `src/audio.c`, hybrid at 32, SILK at 12)
 * and different signals (tones, sweep, noise, silence, fake voice), then
 * decodes it with native libopus in float.  Writes:
 *   pacchetti.bin  [u16 LE length][packet bytes] ...
 *   attesi.f32     the interleaved float samples the native one gave
 * `confronta.mjs` decodes the same packets with the wasm and compares them.
 */
#include <math.h>
#include <opus.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

#define FREQ 48000
#define N 960
#define SECONDI 12

static uint32_t seme = 12345;
static float caso(void)
{
	seme = seme * 1664525u + 1013904223u;
	return ((float)(seme >> 8) / 16777216.0f) * 2.0f - 1.0f;
}

int main(int argc, char **argv)
{
	if (argc != 3)
		return 2;
	int e;
	OpusEncoder *enc = opus_encoder_create(FREQ, 2, OPUS_APPLICATION_AUDIO, &e);
	OpusDecoder *dec = opus_decoder_create(FREQ, 2, &e);
	if (!enc || !dec)
		return 1;
	FILE *fp = fopen(argv[1], "wb"), *fa = fopen(argv[2], "wb");
	opus_int16 pcm[N * 2];
	unsigned char pk[4000];
	float out[5760 * 2];
	double t = 0;
	int blocchi = SECONDI * FREQ / N;
	for (int b = 0; b < blocchi; b++) {
		int seg = b / 100;                   /* one segment every 2 s */
		int br = (seg % 3 == 0) ? 96000 : (seg % 3 == 1) ? 32000 : 12000;
		opus_encoder_ctl(enc, OPUS_SET_BITRATE(br));
		opus_encoder_ctl(enc, OPUS_SET_SIGNAL(seg == 2 ? OPUS_SIGNAL_VOICE : OPUS_AUTO));
		for (int i = 0; i < N; i++, t += 1.0 / FREQ) {
			float l, r;
			switch (seg % 4) {
			case 0: l = 0.5f * sinf(2 * M_PI * 440 * t); r = 0.4f * sinf(2 * M_PI * 660 * t); break;
			case 1: { float f = 100 + 8000 * fmod(t, 2.0) / 2.0;
			          l = r = 0.3f * sinf(2 * M_PI * f * t); } break;
			case 2: l = 0.2f * caso(); r = 0.2f * caso(); break;
			default: l = (b % 50 < 10) ? 0 : 0.6f * sinf(2 * M_PI * 200 * t) * sinf(2 * M_PI * 3 * t);
			         r = l * 0.5f + 0.05f * caso(); break;
			}
			pcm[2 * i] = (opus_int16)lrintf(l * 32767);
			pcm[2 * i + 1] = (opus_int16)lrintf(r * 32767);
		}
		int n = opus_encode(enc, pcm, N, pk, sizeof pk);
		if (n < 0)
			return 1;
		uint16_t le = (uint16_t)n;
		unsigned char h[2] = { le & 255, le >> 8 };
		fwrite(h, 1, 2, fp);
		fwrite(pk, 1, n, fp);
		int m = opus_decode_float(dec, pk, n, out, 5760, 0);
		if (m != N)
			return 1;
		fwrite(out, sizeof(float), m * 2, fa);
	}
	fclose(fp);
	fclose(fa);
	fprintf(stderr, "%d packets, libopus %s\n", blocchi, opus_get_version_string());
	return 0;
}
