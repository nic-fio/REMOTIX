/*
 * 18-a1 — Opus without ffmpeg: is the stream that comes out the same as before?
 *
 * ⛔ THE QUESTION (phase 18, line A; `DECISIONI.md` §10.25): `src/audio.c` was
 *    rewritten on 30 September 2026 from libavcodec to `libopus` directly, and
 *    the condition is that the receiver must NOT be able to tell before from after.
 *    ⇒ We do not judge "sounds good": we judge **equal**.
 *
 * ⭐ How: the TWO real `audio.c`, linked in the same program —
 *      · the old one is `audio-vecchio.c`, a literal copy of `src/audio.c`
 *        at commit 545ec55 (the last one with libavcodec), with the public symbols
 *        renamed `vecchio_*` from the compile line (see `costruisci.sh`);
 *      · the new one is `../../src/audio.c` as it is in the tree.
 *    Same signal to both, block by block, through the SAME
 *    function the product calls (`audio_enc_pass()`), with the silence
 *    cure on (the default) and then off.
 *
 * The signal, 48 kHz stereo s16, in blocks of 960 (20 ms):
 *   A  synthetic speech       glottal pulses 90-220 Hz in three resonators that
 *                             change every syllable, hiss pauses at -60 dB
 *   B  music                  chords with different harmonics left and
 *                             right, noise hits
 *   C  DIGITAL silence        all zero: the cure mutes it
 *   D  jumps                  full-scale tone that comes in abruptly, half
 *                             block at zero, square wave at ±32767 and -32768
 *   E  one-block gaps         one block at zero every five, inside the music
 *   F  near silence           ±1 LSB (NOT zero: it gets encoded)
 *   G  loud white noise       the biggest packet
 *   H  pure tone 440/660 Hz   at -6 dB: the POSITIVE check of the alignment
 *                             (if the `pre-skip` were wrong, it shows here)
 *
 * What is compared:  packets out and muted; byte by byte; sizes
 * (min/mean/max); the TOC (configuration, stereo, frame code); the
 * 1-2 byte packets (Opus's DTX, which must not be there); the decoding
 * with `libopus` (the same as `opusdec`) and the error against the source,
 * per stretch, aligned on the `pre-skip`.  ⛔ And PCM (codec 2) for completeness.
 *
 * Exit: 0 GREEN if every packet is identical, 1 RED otherwise.
 */
#include "audio.h"

#include <math.h>
#include <opus.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* The old one's symbols, renamed by `costruisci.sh`. */
audio_cod *old_enc_open(uint8_t codec);
void old_enc_close(audio_cod *c);
bool old_enc_pass(audio_cod *c, const int16_t *samples, uint8_t *report,
                       size_t *amount);
void old_silence_hush(bool yes);
uint64_t old_enc_silenced(const audio_cod *c);

/* ⚠ The real log is not needed: the lines are printed, indented, because
 *   the opening ones ARE one of the things to compare. */
void log_says_in(const char *file, int text_line, const char *area,
                      const char *fmt, ...)
{
	va_list ap;
	(void)text_line;
	printf("      [%s %s] ", area, strstr(file, "vecchio") ? "old" : "new");
	va_start(ap, fmt);
	vprintf(fmt, ap);
	va_end(ap);
	printf("\n");
}

#define FQ 48000
#define BL 960
#define DELAY 312 /* pre-skip, `[M]` 17 Aug 2026 and read again below */

enum { T_A, T_B, T_C, T_D, T_E, T_F, T_G, T_H, T_N };
static const char *segment_name[T_N] = {
	"A speech", "B music", "C digital silence", "D jumps",
	"E one-block gaps", "F near silence", "G loud noise",
	"H pure tone",
};
/* blocks per stretch: 10 s, 10 s, 4 s, 2 s, 4 s, 4 s, 4 s, 4 s */
static const int blocks_stretch[T_N] = { 500, 500, 200, 100, 200, 200, 200, 200 };

static uint32_t seed = 12345;
static double noise(void)
{
	seed = seed * 1664525u + 1013904223u;
	return ((double)(seed >> 8) / 16777216.0) * 2.0 - 1.0;
}

static int16_t sat(double v)
{
	v = v * 32767.0;
	if (v > 32767.0)
		return 32767;
	if (v < -32768.0)
		return -32768;
	return (int16_t)lrint(v);
}

/* Two-pole resonator, one per channel per formant. */
typedef struct { double a1, a2, g, y1, y2; } resonator;
static void resonator_set(resonator *r, double f, double bandwidth)
{
	double rr = exp(-M_PI * bandwidth / FQ);
	r->a1 = 2.0 * rr * cos(2.0 * M_PI * f / FQ);
	r->a2 = -rr * rr;
	r->g = 1.0 - rr;
}
static double resonator_step(resonator *r, double x)
{
	double y = r->g * x + r->a1 * r->y1 + r->a2 * r->y2;
	r->y2 = r->y1;
	r->y1 = y;
	return y;
}

/* Generates the whole signal once: it is given again, identical, to every arm. */
static int16_t *send_signal;
/* `--write DIR`: the Opus arm with the cure on leaves its packets for
 * `chrome.py` — two bytes of little-endian length and the packet, 0 = muted
 * block — and the NATIVE float decoding of the new one, for the comparison. */
static const char *write_dir;
static int *stretch_of; /* per block */
static int blocks_total;

static void generate(void)
{
	static const double formants[5][3] = {
		{ 700, 1220, 2600 }, { 300, 2300, 3000 }, { 500, 900, 2400 },
		{ 350, 800, 2250 },  { 600, 1700, 2600 },
	};
	resonator f[3];
	double phase_gl = 0, t;
	long n = 0;

	blocks_total = 0;
	for (int i = 0; i < T_N; i++)
		blocks_total += blocks_stretch[i];
	send_signal = calloc((size_t)blocks_total * BL * 2, sizeof(int16_t));
	stretch_of = calloc((size_t)blocks_total, sizeof(int));
	memset(f, 0, sizeof f);

	int b = 0;
	for (int tr = 0; tr < T_N; tr++) {
		for (int k = 0; k < blocks_stretch[tr]; k++, b++) {
			stretch_of[b] = tr;
			int16_t *d = send_signal + (size_t)b * BL * 2;
			for (int i = 0; i < BL; i++, n++) {
				double l = 0, r = 0;
				t = (double)n / FQ;
				switch (tr) {
				case T_A: {
					int syl = (int)(t / 0.2);
					bool delay = (syl % 7) == 6;
					if (i == 0 && k % 10 == 0)
						for (int q = 0; q < 3; q++)
							resonator_set(&f[q], formants[syl % 5][q], 80 + 40 * q);
					double f0 = 90 + 130 * (0.5 + 0.5 * sin(2 * M_PI * 0.7 * t));
					phase_gl += f0 / FQ;
					double imp = 0;
					if (phase_gl >= 1.0) {
						phase_gl -= 1.0;
						imp = 1.0;
					}
					double x = delay ? 0.0 : imp * 6.0 + 0.02 * noise();
					double y = resonator_step(&f[0], x) + 0.6 * resonator_step(&f[1], x) +
					           0.3 * resonator_step(&f[2], x);
					l = r = delay ? 0.001 * noise() : y;
					break;
				}
				case T_B: {
					double fl[3] = { 261.63, 329.63, 392.0 };
					double fr[3] = { 220.0, 277.18, 349.23 };
					for (int q = 0; q < 3; q++)
						for (int h = 1; h <= 4; h++) {
							l += 0.07 / h * sin(2 * M_PI * fl[q] * h * t);
							r += 0.07 / h * sin(2 * M_PI * fr[q] * h * t + 0.3 * h);
						}
					double shot = exp(-fmod(t, 0.5) * 30.0);
					l += 0.3 * shot * noise();
					r += 0.2 * shot * noise();
					break;
				}
				case T_C:
					break;
				case T_D: {
					int q = k / 25;
					if (q == 0)
						l = r = 1.0 * sin(2 * M_PI * 1000 * t);
					else if (q == 1)
						l = r = (i < BL / 2) ? 0.8 * sin(2 * M_PI * 440 * t) : 0.0;
					else if (q == 2)
						l = r = (fmod(t * 200, 1.0) < 0.5) ? 1.0 : -1.0;
					else {
						l = (fmod(t * 50, 1.0) < 0.5) ? 1.5 : -1.5;
						r = -l;
					}
					break;
				}
				case T_E:
					if (k % 5 != 4) {
						l = 0.3 * sin(2 * M_PI * 523.25 * t) + 0.1 * noise();
						r = 0.3 * sin(2 * M_PI * 659.25 * t) + 0.1 * noise();
					}
					break;
				case T_F:
					/* ±1 LSB, never all zero in a block */
					d[i * 2] = (int16_t)((i & 1) ? 1 : -1);
					d[i * 2 + 1] = (int16_t)((noise() > 0) ? 1 : -1);
					continue;
				case T_G:
					l = 0.9 * noise();
					r = 0.9 * noise();
					break;
				case T_H:
					l = 0.5 * sin(2 * M_PI * 440 * t);
					r = 0.5 * sin(2 * M_PI * 660 * t);
					break;
				}
				d[i * 2] = sat(l);
				d[i * 2 + 1] = sat(r);
			}
		}
	}
}

typedef struct {
	uint64_t exited, silenced, byte;
	int min, max;
	uint64_t small; /* 1-2 byte: DTX */
	uint64_t config[32], stereo, code[4];
	int16_t *decoded;
} tally;

static void count(tally *c, const uint8_t *p, size_t n)
{
	c->exited++;
	c->byte += n;
	if (c->min == 0 || (int)n < c->min)
		c->min = (int)n;
	if ((int)n > c->max)
		c->max = (int)n;
	if (n <= 2)
		c->small++;
	c->config[p[0] >> 3]++;
	c->stereo += (p[0] >> 2) & 1;
	c->code[p[0] & 3]++;
}

static const char *mode(int cfg)
{
	return cfg < 12 ? "SILK" : cfg < 16 ? "hybrid" : "CELT";
}

/* SNR per stretch, decoded against the source shifted by DELAY.
 * ⚠ It is a WAVEFORM error, and Opus does not preserve the waveform (it
 *   rebuilds noise per band): the low numbers of A, B, G belong to the codec, not
 *   to the comparison, and they matter only BECAUSE THEY ARE EQUAL between old
 *   and new.  The pure tone H is the check that the alignment is right.  ⚠ And at
 *   the borders between stretches the 312 tail samples end up in the next
 *   stretch: hence the "decoded" energy in silence C. */
static void error_per_stretch(const int16_t *dec, const char *chi)
{
	printf("   error against the source, %s (SNR per stretch, pre-skip %d):\n",
	       chi, DELAY);
	long start = 0;
	for (int tr = 0; tr < T_N; tr++) {
		long fine = start + (long)blocks_stretch[tr] * BL;
		double es = 0, ee = 0;
		for (long i = start; i < fine; i++)
			for (int c = 0; c < 2; c++) {
				long j = i + DELAY;
				if (j >= (long)blocks_total * BL)
					continue;
				double s = send_signal[i * 2 + c];
				double e = s - dec[j * 2 + c];
				es += s * s;
				ee += e * e;
			}
		if (es == 0)
			printf("      %-22s source at zero; decoded energy %.0f\n",
			       segment_name[tr], ee);
		else
			printf("      %-22s %6.2f dB\n", segment_name[tr],
			       10 * log10(es / (ee > 0 ? ee : 1e-9)));
		start = fine;
	}
}

static int arm(uint8_t codec, bool fix)
{
	audio_cod *v, *nu;
	OpusDecoder *dv = NULL, *dn = NULL;
	tally cv, cn;
	int different = 0, first_different = -1, e, refused = 0;
	static uint8_t pv[AUDIO_OUT_MAX], pn[AUDIO_OUT_MAX];

	memset(&cv, 0, sizeof cv);
	memset(&cn, 0, sizeof cn);
	printf("\n== arm: codec %u (%s), silence cure %s\n", codec,
	       codec == 1 ? "Opus" : "PCM", fix ? "ON" : "OFF");
	old_silence_hush(fix);
	audio_silence_hush(fix);
	printf("   -- opening the old one:\n");
	v = old_enc_open(codec);
	printf("   -- opening the new one:\n");
	nu = audio_enc_open(codec);
	if (!v || !nu) {
		printf("⛔ NOTHING TO JUDGE: an encoder does not open\n");
		return 2;
	}
	uint32_t bl = audio_enc_block(nu);
	if (codec == 1) {
		dv = opus_decoder_create(FQ, 2, &e);
		dn = opus_decoder_create(FQ, 2, &e);
		cv.decoded = calloc((size_t)blocks_total * BL * 2, sizeof(int16_t));
		cn.decoded = calloc((size_t)blocks_total * BL * 2, sizeof(int16_t));
	}

	FILE *fv = NULL, *fn = NULL, *ff = NULL;
	OpusDecoder *dfl = NULL;
	if (write_dir && codec == 1 && fix) {
		char name[512];
		snprintf(name, sizeof name, "%s/vecchio.pkt", write_dir);
		fv = fopen(name, "wb");
		snprintf(name, sizeof name, "%s/nuovo.pkt", write_dir);
		fn = fopen(name, "wb");
		snprintf(name, sizeof name, "%s/nuovo.f32", write_dir);
		ff = fopen(name, "wb");
		dfl = opus_decoder_create(FQ, 2, &e);
		if (!fv || !fn || !ff || !dfl) {
			printf("⛔ cannot write in %s\n", write_dir);
			return 2;
		}
	}

	uint32_t steps = (uint32_t)blocks_total * BL / bl;
	for (uint32_t b = 0; b < steps; b++) {
		const int16_t *s = send_signal + (size_t)b * bl * 2;
		size_t qv = 0, qn = 0;
		bool ov = old_enc_pass(v, s, pv, &qv);
		bool on = audio_enc_pass(nu, s, pn, &qn);
		if (ov)
			count(&cv, pv, qv);
		if (on)
			count(&cn, pn, qn);
		if (ov != on || qv != qn || (ov && memcmp(pv, pn, qv))) {
			different++;
			if (first_different < 0)
				first_different = (int)b;
		}
		if (fv) {
			uint8_t l2[2] = { (uint8_t)(qv & 0xFF), (uint8_t)(qv >> 8) };
			uint8_t n2[2] = { (uint8_t)(qn & 0xFF), (uint8_t)(qn >> 8) };
			if (!ov)
				l2[0] = l2[1] = 0;
			if (!on)
				n2[0] = n2[1] = 0;
			fwrite(l2, 1, 2, fv);
			if (ov)
				fwrite(pv, 1, qv, fv);
			fwrite(n2, 1, 2, fn);
			if (on) {
				static float fl[BL * 2];
				fwrite(pn, 1, qn, fn);
				if (opus_decode_float(dfl, pn, (opus_int32)qn, fl, BL, 0) == BL)
					fwrite(fl, sizeof(float), BL * 2, ff);
			}
		}
		/* ⭐ The receiver puts the block at its instant; a muted block
		 *   is a gap, that is zero (the decoder does not see it). */
		if (codec == 1) {
			if (ov && opus_decode(dv, pv, (opus_int32)qv,
			                      cv.decoded + (size_t)b * BL * 2,
			                      BL, 0) != BL)
				refused++;
			if (on && opus_decode(dn, pn, (opus_int32)qn,
			                      cn.decoded + (size_t)b * BL * 2,
			                      BL, 0) != BL)
				refused++;
		}
	}
	if (fv) {
		fclose(fv);
		fclose(fn);
		fclose(ff);
		opus_decoder_destroy(dfl);
		printf("   ⭐ packets and native decoding written in %s\n", write_dir);
	}
	cv.silenced = old_enc_silenced(v);
	cn.silenced = audio_enc_silenced(nu);
	printf("   -- closing:\n");
	old_enc_close(v);
	audio_enc_close(nu);

	printf("   blocks in                 %u\n", steps);
	printf("   %-26s %10s %10s\n", "", "OLD", "NEW");
	printf("   %-26s %10llu %10llu\n", "packets out",
	       (unsigned long long)cv.exited, (unsigned long long)cn.exited);
	printf("   %-26s %10llu %10llu\n", "blocks muted",
	       (unsigned long long)cv.silenced, (unsigned long long)cn.silenced);
	printf("   %-26s %10llu %10llu\n", "bytes in all",
	       (unsigned long long)cv.byte, (unsigned long long)cn.byte);
	printf("   %-26s %10d %10d\n", "smallest packet", cv.min, cn.min);
	printf("   %-26s %10.1f %10.1f\n", "mean packet",
	       cv.exited ? (double)cv.byte / cv.exited : 0,
	       cn.exited ? (double)cn.byte / cn.exited : 0);
	printf("   %-26s %10d %10d\n", "biggest packet", cv.max, cn.max);
	if (codec == 1) {
		printf("   %-26s %10llu %10llu\n", "1-2 byte packets (DTX)",
		       (unsigned long long)cv.small, (unsigned long long)cn.small);
		printf("   %-26s %10llu %10llu\n", "TOC stereo",
		       (unsigned long long)cv.stereo, (unsigned long long)cn.stereo);
		for (int k = 0; k < 4; k++)
			if (cv.code[k] || cn.code[k])
				printf("   TOC code %d                 %10llu %10llu\n", k,
				       (unsigned long long)cv.code[k],
				       (unsigned long long)cn.code[k]);
		for (int k = 0; k < 32; k++)
			if (cv.config[k] || cn.config[k])
				printf("   TOC config %2d (%-6s)     %10llu %10llu\n", k,
				       mode(k), (unsigned long long)cv.config[k],
				       (unsigned long long)cn.config[k]);
		long dd = 0;
		for (size_t i = 0; i < (size_t)blocks_total * BL * 2; i++)
			if (cv.decoded[i] != cn.decoded[i])
				dd++;
		printf("   packets the decoder refuses: %d\n", refused);
		printf("   decoded samples different between old and new: %ld of %ld\n",
		       dd, (long)blocks_total * BL * 2);
		error_per_stretch(cv.decoded, "old");
		error_per_stretch(cn.decoded, "new");
		opus_decoder_destroy(dv);
		opus_decoder_destroy(dn);
		free(cv.decoded);
		free(cn.decoded);
	}
	if (different)
		printf("   ⛔ ROSSO: %d blocks with a different outcome, the first at block %d\n",
		       different, first_different);
	else
		printf("   ⭐ VERDE: %u blocks, every outcome and every packet IDENTICAL "
		       "byte for byte\n", steps);
	return (different || refused) ? 1 : 0;
}

int main(int argc, char **argv)
{
	int outcome = 0;
	if (argc == 3 && strcmp(argv[1], "--write") == 0)
		write_dir = argv[2];
	generate();
	printf("== 18-a1 · Opus without ffmpeg · %d blocks of 20 ms (%.0f s) · %s\n",
	       blocks_total, blocks_total * 0.02, opus_get_version_string());
	outcome |= arm(1, true);
	outcome |= arm(1, false);
	outcome |= arm(2, true);
	outcome |= arm(2, false);
	printf("\n%s\n", outcome == 0 ? "⭐ VERDE — the new one is indistinguishable from the old one"
	                            : "⛔ ROSSO — see the arms above");
	return outcome;
}
