/*
 * 18-a1 — Opus senza ffmpeg: il flusso che esce e' lo stesso di prima?
 *
 * ⛔ LA DOMANDA (fase 18, linea A; `DECISIONI.md` §10.25): `src/audio.c` e'
 *    stato riscritto il 30 settembre 2026 da libavcodec a `libopus` diretta, e
 *    la condizione e' che chi riceve NON possa distinguere il prima dal dopo.
 *    ⇒ Non si giudica «suona bene»: si giudica **uguale**.
 *
 * ⭐ Come: i DUE `audio.c` veri, collegati nello stesso programma —
 *      · il vecchio e' `audio-vecchio.c`, copia alla lettera di `src/audio.c`
 *        al commit 545ec55 (l'ultimo con libavcodec), coi simboli pubblici
 *        rinominati `vecchio_*` dalla riga di compilazione (vedi `costruisci.sh`);
 *      · il nuovo e' `../../src/audio.c` com'e' nell'albero.
 *    Stesso segnale a tutt'e due, blocco per blocco, attraverso la STESSA
 *    funzione che chiama il prodotto (`audio_cod_passa()`), con la cura del
 *    silenzio accesa (il predefinito) e poi spenta.
 *
 * Il segnale, 48 kHz stereo s16, a blocchi da 960 (20 ms):
 *   A  parlato sintetico      impulsi glottali 90-220 Hz in tre risonatori che
 *                             cambiano ogni sillaba, pause di fruscio a -60 dB
 *   B  musica                 accordi con armoniche diversi a sinistra e a
 *                             destra, colpi di rumore
 *   C  silenzio DIGITALE      tutti zero: la cura lo tace
 *   D  salti                  tono a fondo scala che entra di colpo, meta'
 *                             blocco a zero, onda quadra a ±32767 e -32768
 *   E  buchi di un blocco     un blocco a zero ogni cinque, dentro la musica
 *   F  quasi silenzio         ±1 LSB (NON e' zero: si codifica)
 *   G  rumore bianco forte    il pacchetto piu' grosso
 *   H  tono puro 440/660 Hz   a -6 dB: il controllo POSITIVO dell'allineamento
 *                             (se il `pre-skip` fosse sbagliato, qui si vede)
 *
 * Cosa si confronta:  pacchetti usciti e taciuti; byte per byte; dimensioni
 * (min/media/max); il TOC (configurazione, stereo, codice di trama); i
 * pacchetti da 1-2 byte (la DTX di Opus, che non deve esserci); la decodifica
 * con `libopus` (la stessa di `opusdec`) e l'errore rispetto alla sorgente,
 * per tratto, allineata sul `pre-skip`.  ⛔ E il PCM (codec 2) per completezza.
 *
 * Uscita: 0 VERDE se ogni pacchetto e' identico, 1 ROSSO altrimenti.
 */
#include "audio.h"

#include <math.h>
#include <opus.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

/* I simboli del vecchio, rinominati da `costruisci.sh`. */
audio_cod *vecchio_cod_apri(uint8_t codec);
void vecchio_cod_chiudi(audio_cod *c);
bool vecchio_cod_passa(audio_cod *c, const int16_t *campioni, uint8_t *fuori,
                       size_t *quanti);
void vecchio_silenzio_taci(bool si);
uint64_t vecchio_cod_taciuti(const audio_cod *c);

/* ⚠ Il registro vero non serve: le righe si stampano, rientrate, perche'
 *   quelle dell'apertura SONO una delle cose da confrontare. */
void registro_dice_in(const char *file, int linea, const char *area,
                      const char *fmt, ...)
{
	va_list ap;
	(void)linea;
	printf("      [%s %s] ", area, strstr(file, "vecchio") ? "vecchio" : "nuovo");
	va_start(ap, fmt);
	vprintf(fmt, ap);
	va_end(ap);
	printf("\n");
}

#define FQ 48000
#define BL 960
#define RITARDO 312 /* pre-skip, `[M]` 17 ago 2026 e letto di nuovo sotto */

enum { T_A, T_B, T_C, T_D, T_E, T_F, T_G, T_H, T_N };
static const char *nome_tratto[T_N] = {
	"A parlato", "B musica", "C silenzio digitale", "D salti",
	"E buchi di un blocco", "F quasi silenzio", "G rumore forte",
	"H tono puro",
};
/* blocchi per tratto: 10 s, 10 s, 4 s, 2 s, 4 s, 4 s, 4 s, 4 s */
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

/* Risonatore a due poli, uno per canale per formante. */
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

/* Genera tutto il segnale una volta: si ridà identico a ogni braccio. */
static int16_t *segnale;
/* `--scrivi DIR`: il braccio Opus a cura accesa lascia i suoi pacchetti per
 * `chrome.py` — due byte di lunghezza little-endian e il pacchetto, 0 = blocco
 * taciuto — e la decodifica NATIVA in float del nuovo, per il paragone. */
static const char *scrivi_in;
static int *tratto_di; /* per blocco */
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
					/* ±1 LSB, mai tutto zero in un blocco */
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
	return cfg < 12 ? "SILK" : cfg < 16 ? "ibrido" : "CELT";
}

/* SNR per tratto, decodificato contro sorgente spostata di RITARDO.
 * ⚠ E' un errore di FORMA D'ONDA, e Opus non la conserva (il rumore lo
 *   ricostruisce per bande): i numeri bassi di A, B, G sono del codec, non del
 *   confronto, e contano solo PERCHE' UGUALI fra vecchio e nuovo.  Il tono
 *   puro H e' il controllo che l'allineamento sia giusto.  ⚠ E ai confini fra
 *   tratti i 312 campioni di coda finiscono nel tratto dopo: da qui l'energia
 *   «decodificata» nel silenzio C. */
static void errore_per_tratto(const int16_t *dec, const char *chi)
{
	printf("   errore rispetto alla sorgente, %s (SNR per tratto, pre-skip %d):\n",
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
			printf("      %-22s sorgente a zero; energia decodificata %.0f\n",
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
	printf("\n== braccio: codec %u (%s), cura del silenzio %s\n", codec,
	       codec == 1 ? "Opus" : "PCM", cura ? "ACCESA" : "SPENTA");
	vecchio_silenzio_taci(cura);
	audio_silenzio_taci(cura);
	printf("   -- apertura del vecchio:\n");
	v = vecchio_cod_apri(codec);
	printf("   -- apertura del nuovo:\n");
	nu = audio_cod_apri(codec);
	if (!v || !nu) {
		printf("⛔ NIENTE DA GIUDICARE: un codificatore non si apre\n");
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
			printf("⛔ non scrivo in %s\n", scrivi_in);
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
		/* ⭐ Chi riceve mette il blocco al suo istante; un blocco taciuto
		 *   e' un buco, cioe' zero (il decodificatore non lo vede). */
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
		printf("   ⭐ pacchetti e decodifica nativa scritti in %s\n", scrivi_in);
	}
	cv.taciuti = vecchio_cod_taciuti(v);
	cn.taciuti = audio_cod_taciuti(nu);
	printf("   -- chiusura:\n");
	vecchio_cod_chiudi(v);
	audio_cod_chiudi(nu);

	printf("   blocchi entrati           %u\n", passi);
	printf("   %-26s %10s %10s\n", "", "VECCHIO", "NUOVO");
	printf("   %-26s %10llu %10llu\n", "pacchetti usciti",
	       (unsigned long long)cv.usciti, (unsigned long long)cn.usciti);
	printf("   %-26s %10llu %10llu\n", "blocchi taciuti",
	       (unsigned long long)cv.taciuti, (unsigned long long)cn.taciuti);
	printf("   %-26s %10llu %10llu\n", "byte in tutto",
	       (unsigned long long)cv.byte, (unsigned long long)cn.byte);
	printf("   %-26s %10d %10d\n", "pacchetto piu' piccolo", cv.min, cn.min);
	printf("   %-26s %10.1f %10.1f\n", "pacchetto medio",
	       cv.usciti ? (double)cv.byte / cv.usciti : 0,
	       cn.usciti ? (double)cn.byte / cn.usciti : 0);
	printf("   %-26s %10d %10d\n", "pacchetto piu' grosso", cv.max, cn.max);
	if (codec == 1) {
		printf("   %-26s %10llu %10llu\n", "pacchetti da 1-2 byte (DTX)",
		       (unsigned long long)cv.piccoli, (unsigned long long)cn.piccoli);
		printf("   %-26s %10llu %10llu\n", "TOC stereo",
		       (unsigned long long)cv.stereo, (unsigned long long)cn.stereo);
		for (int k = 0; k < 4; k++)
			if (cv.codice[k] || cn.codice[k])
				printf("   TOC codice %d               %10llu %10llu\n", k,
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
		printf("   pacchetti che il decodificatore rifiuta: %d\n", rifiutati);
		printf("   campioni decodificati diversi fra vecchio e nuovo: %ld su %ld\n",
		       dd, (long)blocchi_tot * BL * 2);
		errore_per_tratto(cv.decodificato, "vecchio");
		errore_per_tratto(cn.decodificato, "nuovo");
		opus_decoder_destroy(dv);
		opus_decoder_destroy(dn);
		free(cv.decodificato);
		free(cn.decodificato);
	}
	if (diversi)
		printf("   ⛔ ROSSO: %d blocchi con esito diverso, il primo al blocco %d\n",
		       diversi, primo_diverso);
	else
		printf("   ⭐ VERDE: %u blocchi, ogni esito e ogni pacchetto IDENTICO "
		       "byte per byte\n", passi);
	return (diversi || rifiutati) ? 1 : 0;
}

int main(int argc, char **argv)
{
	int esito = 0;
	if (argc == 3 && strcmp(argv[1], "--scrivi") == 0)
		scrivi_in = argv[2];
	genera();
	printf("== 18-a1 · Opus senza ffmpeg · %d blocchi da 20 ms (%.0f s) · %s\n",
	       blocchi_tot, blocchi_tot * 0.02, opus_get_version_string());
	esito |= braccio(1, true);
	esito |= braccio(1, false);
	esito |= braccio(2, true);
	esito |= braccio(2, false);
	printf("\n%s\n", esito == 0 ? "⭐ VERDE — il nuovo e' indistinguibile dal vecchio"
	                            : "⛔ ROSSO — vedi i bracci qui sopra");
	return esito;
}
