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
 *    function the product calls (`audio_cod_passa()`), with the silence
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
 * Exit: 0 VERDE if every packet is identical, 1 ROSSO otherwise.
 */
#include "audio.h"

#include <math.h>
#include <opus.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* The old one's symbols, renamed by `costruisci.sh`. */
audio_cod *vecchio_cod_apri(uint8_t codec);
void vecchio_cod_chiudi(audio_cod *c);
bool vecchio_cod_passa(audio_cod *c, const int16_t *campioni, uint8_t *fuori,
                       size_t *quanti);
void vecchio_silenzio_taci(bool si);
uint64_t vecchio_cod_taciuti(const audio_cod *c);

/* ⚠ The real log is not needed: the lines are printed, indented, because
 *   the opening ones ARE one of the things to compare. */
void registro_dice_in(const char *file, int linea, const char *area,
                      const char *fmt, ...)
{
	va_list ap;
	(void)linea;
	printf("      [%s %s] ", area, strstr(file, "vecchio") ? "old" : "new");
	va_start(ap, fmt);
	vprintf(fmt, ap);
	va_end(ap);
	printf("\n");
}

#define FQ 48000
#define BL 960
#define RITARDO 312 /* pre-skip, `[M]` 17 Aug 2026 and read again below */

enum { T_A, T_B, T_C, T_D, T_E, T_F, T_G, T_H, T_N };
static const char *nome_tratto[T_N] = {
	"A speech", "B music", "C digital silence", "D jumps",
	"E one-block gaps", "F near silence", "G loud noise",
	"H pure tone",
};
/* blocks per stretch: 10 s, 10 s, 4 s, 2 s, 4 s, 4 s, 4 s, 4 s */
static const int blocchi_tratto[T_N] = { 500, 500, 200, 100, 200, 200, 200, 200 };

static uint32_t seme = 12345;
static double rumore(void)
{
	seme = seme * 1664525u + 1013904223u;
	return ((double)(seme >> 8) / 16777216.0) * 2.0 - 1.0;
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
typedef struct { double a1, a2, g, y1, y2; } riso;
static void riso_metti(riso *r, double f, double banda)
{
	double rr = exp(-M_PI * banda / FQ);
	r->a1 = 2.0 * rr * cos(2.0 * M_PI * f / FQ);
	r->a2 = -rr * rr;
	r->g = 1.0 - rr;
}
static double riso_passa(riso *r, double x)
{
	double y = r->g * x + r->a1 * r->y1 + r->a2 * r->y2;
	r->y2 = r->y1;
	r->y1 = y;
	return y;
}

/* Generates the whole signal once: it is given again, identical, to every arm. */
static int16_t *segnale;
/* `--scrivi DIR`: the Opus arm with the cure on leaves its packets for
 * `chrome.py` — two bytes of little-endian length and the packet, 0 = muted
 * block — and the NATIVE float decoding of the new one, for the comparison. */
static const char *scrivi_in;
static int *tratto_di; /* per block */
static int blocchi_tot;

static void genera(void)
{
	static const double formanti[5][3] = {
		{ 700, 1220, 2600 }, { 300, 2300, 3000 }, { 500, 900, 2400 },
		{ 350, 800, 2250 },  { 600, 1700, 2600 },
	};
	riso f[3];
	double fase_gl = 0, t;
	long n = 0;

	blocchi_tot = 0;
	for (int i = 0; i < T_N; i++)
		blocchi_tot += blocchi_tratto[i];
	segnale = calloc((size_t)blocchi_tot * BL * 2, sizeof(int16_t));
	tratto_di = calloc((size_t)blocchi_tot, sizeof(int));
	memset(f, 0, sizeof f);

	int b = 0;
	for (int tr = 0; tr < T_N; tr++) {
		for (int k = 0; k < blocchi_tratto[tr]; k++, b++) {
			tratto_di[b] = tr;
			int16_t *d = segnale + (size_t)b * BL * 2;
			for (int i = 0; i < BL; i++, n++) {
				double l = 0, r = 0;
				t = (double)n / FQ;
				switch (tr) {
				case T_A: {
					int sill = (int)(t / 0.2);
					bool pausa = (sill % 7) == 6;
					if (i == 0 && k % 10 == 0)
						for (int q = 0; q < 3; q++)
							riso_metti(&f[q], formanti[sill % 5][q], 80 + 40 * q);
					double f0 = 90 + 130 * (0.5 + 0.5 * sin(2 * M_PI * 0.7 * t));
					fase_gl += f0 / FQ;
					double imp = 0;
					if (fase_gl >= 1.0) {
						fase_gl -= 1.0;
						imp = 1.0;
					}
					double x = pausa ? 0.0 : imp * 6.0 + 0.02 * rumore();
					double y = riso_passa(&f[0], x) + 0.6 * riso_passa(&f[1], x) +
					           0.3 * riso_passa(&f[2], x);
					l = r = pausa ? 0.001 * rumore() : y;
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
					double colpo = exp(-fmod(t, 0.5) * 30.0);
					l += 0.3 * colpo * rumore();
					r += 0.2 * colpo * rumore();
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
						l = 0.3 * sin(2 * M_PI * 523.25 * t) + 0.1 * rumore();
						r = 0.3 * sin(2 * M_PI * 659.25 * t) + 0.1 * rumore();
					}
					break;
				case T_F:
					/* ±1 LSB, never all zero in a block */
					d[i * 2] = (int16_t)((i & 1) ? 1 : -1);
					d[i * 2 + 1] = (int16_t)((rumore() > 0) ? 1 : -1);
					continue;
				case T_G:
					l = 0.9 * rumore();
					r = 0.9 * rumore();
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
	uint64_t usciti, taciuti, byte;
	int min, max;
	uint64_t piccoli; /* 1-2 byte: DTX */
	uint64_t config[32], stereo, codice[4];
	int16_t *decodificato;
} conto;

static void conta(conto *c, const uint8_t *p, size_t n)
{
	c->usciti++;
	c->byte += n;
	if (c->min == 0 || (int)n < c->min)
		c->min = (int)n;
	if ((int)n > c->max)
		c->max = (int)n;
	if (n <= 2)
		c->piccoli++;
	c->config[p[0] >> 3]++;
	c->stereo += (p[0] >> 2) & 1;
	c->codice[p[0] & 3]++;
}

static const char *modo(int cfg)
{
	return cfg < 12 ? "SILK" : cfg < 16 ? "hybrid" : "CELT";
}

/* SNR per stretch, decoded against the source shifted by RITARDO.
 * ⚠ It is a WAVEFORM error, and Opus does not preserve the waveform (it
 *   rebuilds noise per band): the low numbers of A, B, G belong to the codec, not
 *   to the comparison, and they matter only BECAUSE THEY ARE EQUAL between old
 *   and new.  The pure tone H is the check that the alignment is right.  ⚠ And at
 *   the borders between stretches the 312 tail samples end up in the next
 *   stretch: hence the "decoded" energy in silence C. */
static void errore_per_tratto(const int16_t *dec, const char *chi)
{
	printf("   error against the source, %s (SNR per stretch, pre-skip %d):\n",
	       chi, RITARDO);
	long inizio = 0;
	for (int tr = 0; tr < T_N; tr++) {
		long fine = inizio + (long)blocchi_tratto[tr] * BL;
		double es = 0, ee = 0;
		for (long i = inizio; i < fine; i++)
			for (int c = 0; c < 2; c++) {
				long j = i + RITARDO;
				if (j >= (long)blocchi_tot * BL)
					continue;
				double s = segnale[i * 2 + c];
				double e = s - dec[j * 2 + c];
				es += s * s;
				ee += e * e;
			}
		if (es == 0)
			printf("      %-22s source at zero; decoded energy %.0f\n",
			       nome_tratto[tr], ee);
		else
			printf("      %-22s %6.2f dB\n", nome_tratto[tr],
			       10 * log10(es / (ee > 0 ? ee : 1e-9)));
		inizio = fine;
	}
}

static int braccio(uint8_t codec, bool cura)
{
	audio_cod *v, *nu;
	OpusDecoder *dv = NULL, *dn = NULL;
	conto cv, cn;
	int diversi = 0, primo_diverso = -1, e, rifiutati = 0;
	static uint8_t pv[AUDIO_FUORI_MAX], pn[AUDIO_FUORI_MAX];

	memset(&cv, 0, sizeof cv);
	memset(&cn, 0, sizeof cn);
	printf("\n== arm: codec %u (%s), silence cure %s\n", codec,
	       codec == 1 ? "Opus" : "PCM", cura ? "ON" : "OFF");
	vecchio_silenzio_taci(cura);
	audio_silenzio_taci(cura);
	printf("   -- opening the old one:\n");
	v = vecchio_cod_apri(codec);
	printf("   -- opening the new one:\n");
	nu = audio_cod_apri(codec);
	if (!v || !nu) {
		printf("⛔ NOTHING TO JUDGE: an encoder does not open\n");
		return 2;
	}
	uint32_t bl = audio_cod_blocco(nu);
	if (codec == 1) {
		dv = opus_decoder_create(FQ, 2, &e);
		dn = opus_decoder_create(FQ, 2, &e);
		cv.decodificato = calloc((size_t)blocchi_tot * BL * 2, sizeof(int16_t));
		cn.decodificato = calloc((size_t)blocchi_tot * BL * 2, sizeof(int16_t));
	}

	FILE *fv = NULL, *fn = NULL, *ff = NULL;
	OpusDecoder *dfl = NULL;
	if (scrivi_in && codec == 1 && cura) {
		char nome[512];
		snprintf(nome, sizeof nome, "%s/vecchio.pkt", scrivi_in);
		fv = fopen(nome, "wb");
		snprintf(nome, sizeof nome, "%s/nuovo.pkt", scrivi_in);
		fn = fopen(nome, "wb");
		snprintf(nome, sizeof nome, "%s/nuovo.f32", scrivi_in);
		ff = fopen(nome, "wb");
		dfl = opus_decoder_create(FQ, 2, &e);
		if (!fv || !fn || !ff || !dfl) {
			printf("⛔ cannot write in %s\n", scrivi_in);
			return 2;
		}
	}

	uint32_t passi = (uint32_t)blocchi_tot * BL / bl;
	for (uint32_t b = 0; b < passi; b++) {
		const int16_t *s = segnale + (size_t)b * bl * 2;
		size_t qv = 0, qn = 0;
		bool ov = vecchio_cod_passa(v, s, pv, &qv);
		bool on = audio_cod_passa(nu, s, pn, &qn);
		if (ov)
			conta(&cv, pv, qv);
		if (on)
			conta(&cn, pn, qn);
		if (ov != on || qv != qn || (ov && memcmp(pv, pn, qv))) {
			diversi++;
			if (primo_diverso < 0)
				primo_diverso = (int)b;
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
			                      cv.decodificato + (size_t)b * BL * 2,
			                      BL, 0) != BL)
				rifiutati++;
			if (on && opus_decode(dn, pn, (opus_int32)qn,
			                      cn.decodificato + (size_t)b * BL * 2,
			                      BL, 0) != BL)
				rifiutati++;
		}
	}
	if (fv) {
		fclose(fv);
		fclose(fn);
		fclose(ff);
		opus_decoder_destroy(dfl);
		printf("   ⭐ packets and native decoding written in %s\n", scrivi_in);
	}
	cv.taciuti = vecchio_cod_taciuti(v);
	cn.taciuti = audio_cod_taciuti(nu);
	printf("   -- closing:\n");
	vecchio_cod_chiudi(v);
	audio_cod_chiudi(nu);

	printf("   blocks in                 %u\n", passi);
	printf("   %-26s %10s %10s\n", "", "OLD", "NEW");
	printf("   %-26s %10llu %10llu\n", "packets out",
	       (unsigned long long)cv.usciti, (unsigned long long)cn.usciti);
	printf("   %-26s %10llu %10llu\n", "blocks muted",
	       (unsigned long long)cv.taciuti, (unsigned long long)cn.taciuti);
	printf("   %-26s %10llu %10llu\n", "bytes in all",
	       (unsigned long long)cv.byte, (unsigned long long)cn.byte);
	printf("   %-26s %10d %10d\n", "smallest packet", cv.min, cn.min);
	printf("   %-26s %10.1f %10.1f\n", "mean packet",
	       cv.usciti ? (double)cv.byte / cv.usciti : 0,
	       cn.usciti ? (double)cn.byte / cn.usciti : 0);
	printf("   %-26s %10d %10d\n", "biggest packet", cv.max, cn.max);
	if (codec == 1) {
		printf("   %-26s %10llu %10llu\n", "1-2 byte packets (DTX)",
		       (unsigned long long)cv.piccoli, (unsigned long long)cn.piccoli);
		printf("   %-26s %10llu %10llu\n", "TOC stereo",
		       (unsigned long long)cv.stereo, (unsigned long long)cn.stereo);
		for (int k = 0; k < 4; k++)
			if (cv.codice[k] || cn.codice[k])
				printf("   TOC code %d                 %10llu %10llu\n", k,
				       (unsigned long long)cv.codice[k],
				       (unsigned long long)cn.codice[k]);
		for (int k = 0; k < 32; k++)
			if (cv.config[k] || cn.config[k])
				printf("   TOC config %2d (%-6s)     %10llu %10llu\n", k,
				       modo(k), (unsigned long long)cv.config[k],
				       (unsigned long long)cn.config[k]);
		long dd = 0;
		for (size_t i = 0; i < (size_t)blocchi_tot * BL * 2; i++)
			if (cv.decodificato[i] != cn.decodificato[i])
				dd++;
		printf("   packets the decoder refuses: %d\n", rifiutati);
		printf("   decoded samples different between old and new: %ld of %ld\n",
		       dd, (long)blocchi_tot * BL * 2);
		errore_per_tratto(cv.decodificato, "old");
		errore_per_tratto(cn.decodificato, "new");
		opus_decoder_destroy(dv);
		opus_decoder_destroy(dn);
		free(cv.decodificato);
		free(cn.decodificato);
	}
	if (diversi)
		printf("   ⛔ ROSSO: %d blocks with a different outcome, the first at block %d\n",
		       diversi, primo_diverso);
	else
		printf("   ⭐ VERDE: %u blocks, every outcome and every packet IDENTICAL "
		       "byte for byte\n", passi);
	return (diversi || rifiutati) ? 1 : 0;
}

int main(int argc, char **argv)
{
	int esito = 0;
	if (argc == 3 && strcmp(argv[1], "--scrivi") == 0)
		scrivi_in = argv[2];
	genera();
	printf("== 18-a1 · Opus without ffmpeg · %d blocks of 20 ms (%.0f s) · %s\n",
	       blocchi_tot, blocchi_tot * 0.02, opus_get_version_string());
	esito |= braccio(1, true);
	esito |= braccio(1, false);
	esito |= braccio(2, true);
	esito |= braccio(2, false);
	printf("\n%s\n", esito == 0 ? "⭐ VERDE — the new one is indistinguishable from the old one"
	                            : "⛔ ROSSO — see the arms above");
	return esito;
}
