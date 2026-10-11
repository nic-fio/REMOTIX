/*
 * The page's Opus decoder (D-006, 25 Sep 2026): libopus 1.5.2
 * compiled to WebAssembly, decoding ONLY.  Used by `src/page.html`
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
#define CHANNELS 2
#define MAX_FRAMES 5760           /* 120 ms at 48 kHz: Opus's maximum */
#define MAX_PACKET 4000            /* a datagram is well below */

static unsigned char state[64 * 1024] __attribute__((aligned(16)));
static unsigned char packet[MAX_PACKET];
static float output[MAX_FRAMES * CHANNELS];
static int ready;

/* 0 = ready; <0 = libopus error; -1000 = the state does not fit. */
__attribute__((export_name("rx_open")))
int rx_open(void)
{
	int n = opus_decoder_get_size(CHANNELS);
	if (n <= 0 || n > (int)sizeof state)
		return -1000;
	int e = opus_decoder_init((OpusDecoder *)state, FREQ, CHANNELS);
	ready = (e == OPUS_OK);
	return e;
}

__attribute__((export_name("rx_packet")))
unsigned char *rx_packet(void) { return packet; }

__attribute__((export_name("rx_pacchetto_max")))
int rx_pacchetto_max(void) { return MAX_PACKET; }

__attribute__((export_name("rx_output")))
float *rx_output(void) { return output; }

/* Decodes the `n` bytes already copied into `packet`.  Returns the frames
 * (per channel) written into `output`, interleaved, or an error < 0. */
__attribute__((export_name("rx_decode")))
int rx_decode(int n)
{
	if (!ready)
		return OPUS_INVALID_STATE;
	if (n <= 0 || n > MAX_PACKET)
		return OPUS_BAD_ARG;
	return opus_decode_float((OpusDecoder *)state, packet, n, output,
	                         MAX_FRAMES, 0);
}
