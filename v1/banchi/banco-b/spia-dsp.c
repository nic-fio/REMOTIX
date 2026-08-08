/*
 * spia-dsp — che cosa fa `freerdp_dsp_encode` a del PCM a 16 bit.
 *
 * E' l'ultimo anello non misurato della questione n.10 di REFERENCE.md: fra i
 * campioni che consegniamo a `SendSamples` — puliti, verificati byte per byte —
 * e i PDU sul filo ci sono soltanto `freerdp_dsp_encode` e l'involucro WAVE2.
 * Qui si guarda il primo, da solo, senza client, senza rete e senza cattura:
 * entra un seno noto, si guarda che cosa esce.
 *
 *   gcc spia-dsp.c $(pkg-config --cflags --libs freerdp3 winpr3) -o spia-dsp
 */
#include <freerdp/codec/audio.h>
#include <freerdp/codec/dsp.h>
#include <winpr/stream.h>

#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#define FREQUENZA 44100u
#define CANALI 2u
#define FOTOGRAMMI 4410u /* un decimo di secondo */
#define AMPIEZZA 3000

static void misura(const char *chi, const int16_t *v, size_t quanti)
{
	int picco = 0;
	double somma = 0.0;

	for (size_t i = 0; i < quanti; i++)
	{
		int x = v[i];

		if (abs(x) > picco)
			picco = abs(x);
		somma += (double) x * (double) x;
	}
	printf("   %-12s picco %6d   rms %6.0f   primi campioni: %6d %6d %6d %6d\n", chi, picco,
	       sqrt(somma / (double) quanti), v[0], v[1], v[2], v[3]);
}

int main(void)
{
	int16_t ingresso[FOTOGRAMMI * CANALI];
	AUDIO_FORMAT formato = { 0 };
	FREERDP_DSP_CONTEXT *dsp;
	wStream *fuori;
	size_t uscite;
	const int16_t *usciti;
	size_t diversi = 0, ribaltati = 0;

	for (unsigned i = 0; i < FOTOGRAMMI; i++)
	{
		int16_t v = (int16_t) (AMPIEZZA * sin(2.0 * M_PI * 440.0 * i / FREQUENZA));

		ingresso[i * CANALI] = v;
		ingresso[i * CANALI + 1] = v;
	}

	/* Il formato di destinazione E' quello di partenza: e' il caso di REMOTIX,
	 * che dichiara come sorgente lo stesso formato PCM scelto dal client.
	 * Quindi qui non c'e' NIENTE da convertire: quel che esce deve essere
	 * identico a quel che entra. */
	formato.wFormatTag = WAVE_FORMAT_PCM;
	formato.nChannels = CANALI;
	formato.nSamplesPerSec = FREQUENZA;
	formato.wBitsPerSample = 16;
	formato.nBlockAlign = 4;
	formato.nAvgBytesPerSec = FREQUENZA * 4;

	dsp = freerdp_dsp_context_new(TRUE);
	if (!dsp)
	{
		printf("   NO  contesto DSP non creato\n");
		return 1;
	}
	if (!freerdp_dsp_context_reset(dsp, &formato, 0))
	{
		printf("   NO  freerdp_dsp_context_reset rifiutata\n");
		return 1;
	}

	fuori = Stream_New(NULL, sizeof ingresso + 4096);
	if (!fuori)
		return 1;

	if (!freerdp_dsp_encode(dsp, &formato, (const BYTE *) ingresso, sizeof ingresso, fuori))
	{
		printf("   NO  freerdp_dsp_encode fallita\n");
		return 1;
	}

	uscite = Stream_GetPosition(fuori) / sizeof(int16_t);
	usciti = (const int16_t *) Stream_Buffer(fuori);

	printf("   byte dentro %zu, byte fuori %zu\n", sizeof ingresso,
	       Stream_GetPosition(fuori));
	misura("dentro", ingresso, FOTOGRAMMI * CANALI);
	misura("fuori", usciti, uscite);

	for (size_t i = 0; i < uscite && i < FOTOGRAMMI * CANALI; i++)
	{
		if (usciti[i] != ingresso[i])
			diversi++;
		/* L'ipotesi: il bit di segno ribaltato, cioe' `+ 0x8000`, che e' quel
		 * che fa il codificatore `pcm_u16le` di FFmpeg. */
		if ((uint16_t) usciti[i] == (uint16_t) (ingresso[i] ^ 0x8000))
			ribaltati++;
	}
	printf("   campioni confrontati %zu — diversi %zu, e di questi %zu sono l'originale\n"
	       "   con il BIT DI SEGNO RIBALTATO (x ^ 0x8000)\n",
	       uscite < FOTOGRAMMI * CANALI ? uscite : (size_t) FOTOGRAMMI * CANALI, diversi,
	       ribaltati);

	if (diversi == 0)
		printf("\n   ESITO: il DSP e' innocente, i campioni passano intatti.\n");
	else if (ribaltati == diversi)
		printf("\n   ESITO: IL DSP RIBALTA IL SEGNO DI OGNI CAMPIONE.\n"
		       "          Il PCM a 16 bit di RDP e' CON SEGNO; FreeRDP lo codifica\n"
		       "          con `AV_CODEC_ID_PCM_U16LE`, cioe' SENZA segno.\n");
	else
		printf("\n   ESITO: il DSP cambia i campioni, ma non solo di segno.\n");

	Stream_Free(fuori, TRUE);
	freerdp_dsp_context_free(dsp);
	return 0;
}
