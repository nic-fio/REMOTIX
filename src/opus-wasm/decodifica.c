/*
 * Il decodificatore Opus della pagina (D-006, 25 set 2026): libopus 1.5.2
 * compilato in WebAssembly, SOLO decodifica.  Lo usa `src/pagina.html`
 * (sezione AUDIO) al posto di `AudioDecoder` di WebCodecs, su tutti i browser.
 *
 * ⭐ Niente malloc, niente libc da importare: lo stato del decodificatore e i
 *   due buffer (pacchetto in ingresso, campioni in uscita) sono STATICI, e la
 *   pagina li raggiunge con gli indirizzi che queste funzioni le danno.  Il
 *   modulo non importa niente ⇒ si istanzia con `{}`.
 *
 * Il formato e' quello di `src/audio.c` e di RCP §5.3: 48 000 Hz, 2 canali,
 * un pacchetto ogni 20 ms (960 fotogrammi).  Il buffer d'uscita tiene il
 * massimo che Opus puo' dare (120 ms = 5760 fotogrammi), cosi' un server che
 * cambiasse durata non scriverebbe fuori.
 */
#include <opus.h>

#define FREQ 48000
#define CANALI 2
#define MAX_FOTOGRAMMI 5760           /* 120 ms a 48 kHz: il massimo di Opus */
#define MAX_PACCHETTO 4000            /* un datagram sta ben sotto */

static unsigned char stato[64 * 1024] __attribute__((aligned(16)));
static unsigned char pacchetto[MAX_PACCHETTO];
static float uscita[MAX_FOTOGRAMMI * CANALI];
static int pronto;

/* 0 = pronto; <0 = errore di libopus; -1000 = lo stato non ci sta. */
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

/* Decodifica gli `n` byte gia' copiati in `pacchetto`.  Torna i fotogrammi
 * (per canale) scritti in `uscita`, interlacciati, o un errore < 0. */
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
