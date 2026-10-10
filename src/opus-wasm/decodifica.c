/*
 * The page's Opus decoder (D-006, 25 Sep 2026): libopus 1.5.2
 * compiled to WebAssembly, decoding ONLY.  Used by `src/pagina.html`
 * (AUDIO section) in place of WebCodecs' `AudioDecoder`, on all browsers.
 *
 * ⭐ No malloc, no libc to import: the decoder state and the
 *   two buffers (incoming packet, outgoing samples) are STATIC, and the
 *   page reaches them through the addresses these functions give it.  The
 *   module imports nothing ⇒ it is instantiated with `{}`.
 *
 * The format is that of `src/audio.c` and RCP §5.3: 48 000 Hz, 2 channels,
 * one packet every 20 ms (960 frames).  The output buffer holds the
 * maximum Opus can give (120 ms = 5760 frames), so a server that
 * changed duration would not write outside.
 */
#include <opus.h>

#define FREQ 48000
#define CANALI 2
#define MAX_FOTOGRAMMI 5760           /* 120 ms at 48 kHz: Opus's maximum */
#define MAX_PACCHETTO 4000            /* a datagram is well below */

static unsigned char stato[64 * 1024] __attribute__((aligned(16)));
static unsigned char pacchetto[MAX_PACCHETTO];
static float uscita[MAX_FOTOGRAMMI * CANALI];
static int pronto;

/* 0 = ready; <0 = libopus error; -1000 = the state does not fit. */
__attribute__((export_name("rx_apri")))
int rx_apri(void)
{
	int n = opus_decoder_get_size(CANALI);
	if (n <= 0 || n > (int)sizeof stato)
		return -1000;
	int e = opus_decoder_init((OpusDecoder *)stato, FREQ, CANALI);
	pronto = (e == OPUS_OK);
	return e;
}

__attribute__((export_name("rx_pacchetto")))
unsigned char *rx_pacchetto(void) { return pacchetto; }

__attribute__((export_name("rx_pacchetto_max")))
int rx_pacchetto_max(void) { return MAX_PACCHETTO; }

__attribute__((export_name("rx_uscita")))
float *rx_uscita(void) { return uscita; }

/* Decodes the `n` bytes already copied into `pacchetto`.  Returns the frames
 * (per channel) written into `uscita`, interleaved, or an error < 0. */
__attribute__((export_name("rx_decodifica")))
int rx_decodifica(int n)
{
	if (!pronto)
		return OPUS_INVALID_STATE;
	if (n <= 0 || n > MAX_PACCHETTO)
		return OPUS_BAD_ARG;
	return opus_decode_float((OpusDecoder *)stato, pacchetto, n, uscita,
	                         MAX_FOTOGRAMMI, 0);
}
