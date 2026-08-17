/*
 * 07-b44 — libopus ritarda i pacchetti, sì o no?
 *
 * ⛔ LA DOMANDA, e non è accademica: `RCP.md` §6.3 dice che l'`istante` di un
 *    datagram è quello del **primo campione del blocco**, e `src/audio.h`
 *    dichiara per iscritto che Opus «può non produrre un pacchetto per ogni
 *    blocco offerto».  ⚠ Se tutt'e due fossero vere, il pacchetto che esce
 *    porterebbe l'istante di un blocco DIVERSO da quello che contiene — e lo
 *    scarto resterebbe per sempre, di 20 ms.
 *
 *    ⇒ Una delle due è falsa, e il rilievo 7 della revisione avversariale del
 *    17 agosto 2026 dice di misurarla invece di discuterla.
 *
 * ⭐ È `CODER.md` §3.6 alla lettera: «quando la catena è già ristretta a due
 *    anelli, non fare un altro giro di banco — scrivi il programma minimo che
 *    chiama la sola funzione sospetta su un ingresso noto».
 *
 * E il controllo positivo: si guarda anche il `pts` che libavcodec mette sul
 * pacchetto, che è il numero che direbbe **a quale** blocco appartiene.  Se
 * combacia con il conto dei blocchi entrati, non c'è ritardo; se resta
 * indietro, c'è ed è misurato.
 *
 * Costruzione (dentro il contenitore):
 *   cc -O2 -std=gnu11 -Wall -Wextra -o /tmp/07-b44 07-b44-ritardo-opus.c \
 *      $(pkg-config --cflags --libs libavcodec libavutil) -lm
 */
#include <libavcodec/avcodec.h>
#include <libavutil/channel_layout.h>
#include <libavutil/opt.h>
#include <math.h>
#include <stdbool.h>
#include <stdio.h>
#include <string.h>

#define FREQUENZA 48000
#define CANALI 2
#define BLOCCO 960 /* 20 ms, RCP.md §5.3 */
#define QUANTI 1000

int main(void)
{
	const AVCodec *cod;
	AVCodecContext *ctx;
	AVFrame *fr;
	AVPacket *pk;
	int64_t pts = 0;
	unsigned entrati = 0, usciti = 0, eagain = 0;
	int64_t scarto_primo = 0;
	bool scarto_varia = false;
	int64_t primo_pts = 0, scarto_massimo = 0;
	/* ⛔ Un `bool` e non una sentinella a `-1`: `[M]` 17 agosto 2026, il
	 *    primo giro di questo banco ha letto «primo pts = 648» dove il
	 *    valore vero era **-312**, perche' `primo_pts < 0` significava
	 *    «non ancora letto» E un pts legittimo insieme.  ⚠ E' la forma di
	 *    `CODER.md` §3.10 — «vuoto» e un valore vero con la stessa faccia —
	 *    dentro il banco scritto per applicarla. */
	bool primo_visto = false;
	int e;

	cod = avcodec_find_encoder_by_name("libopus");
	if (!cod) {
		printf("⛔ NIENTE DA GIUDICARE: l'encoder «libopus» non c'e'.\n");
		return 2;
	}
	ctx = avcodec_alloc_context3(cod);
	ctx->sample_rate = FREQUENZA;
	ctx->sample_fmt = AV_SAMPLE_FMT_S16;
	ctx->bit_rate = 96000;
	av_channel_layout_default(&ctx->ch_layout, CANALI);
	av_opt_set(ctx->priv_data, "frame_duration", "20", 0);
	av_opt_set(ctx->priv_data, "application", "audio", 0);
	if ((e = avcodec_open2(ctx, cod, NULL)) < 0) {
		char m[128];
		av_strerror(e, m, sizeof m);
		printf("⛔ avcodec_open2: %s\n", m);
		return 2;
	}
	printf("== 07-b44 · libopus · frame_size dichiarato: %d "
	       "(§5.3 ne vuole %d)\n", ctx->frame_size, BLOCCO);
	printf("   initial_padding: %d campioni\n", ctx->initial_padding);
	printf("   delay: %d\n", ctx->delay);

	fr = av_frame_alloc();
	pk = av_packet_alloc();
	fr->format = AV_SAMPLE_FMT_S16;
	fr->sample_rate = FREQUENZA;
	fr->nb_samples = BLOCCO;
	av_channel_layout_default(&fr->ch_layout, CANALI);
	av_frame_get_buffer(fr, 0);

	for (unsigned b = 0; b < QUANTI; b++) {
		int16_t *d;
		av_frame_make_writable(fr);
		d = (int16_t *)fr->data[0];
		for (int i = 0; i < BLOCCO; i++) {
			double t = (double)(b * BLOCCO + i) / FREQUENZA;
			int16_t v = (int16_t)(0.5 * sin(2.0 * M_PI * 440.0 * t) * 32767.0);
			d[i * CANALI] = v;
			d[i * CANALI + 1] = v;
		}
		fr->pts = pts;
		pts += BLOCCO;
		if (avcodec_send_frame(ctx, fr) < 0)
			break;
		entrati++;

		e = avcodec_receive_packet(ctx, pk);
		if (e == AVERROR(EAGAIN)) {
			eagain++;
			continue;
		}
		if (e < 0)
			break;
		usciti++;
		if (!primo_visto) {
			primo_visto = true;
			primo_pts = pk->pts;
		}
		/* ⛔ IL NUMERO CHE DECIDE: quanti blocchi c'e' di scarto fra quel che
		 *    ho appena dato e quel che e' appena uscito. */
		{
			/* Lo scarto e' fra il pts del pacchetto e quello del blocco che
			 * gli abbiamo appena dato.  ⭐ Se e' COSTANTE non e' un ritardo:
			 * e' il `pre-skip` di Opus, che il decodificatore toglie da se'. */
			int64_t atteso = (int64_t)(entrati - 1) * BLOCCO;
			int64_t scarto = pk->pts - atteso;
			if (scarto != scarto_primo && usciti > 1)
				scarto_varia = true;
			if (usciti == 1)
				scarto_primo = scarto;
			if (scarto < 0)
				scarto = -scarto;
			if (scarto > scarto_massimo)
				scarto_massimo = scarto;
		}
		av_packet_unref(pk);
	}

	printf("\n   blocchi entrati: %u\n", entrati);
	printf("   pacchetti usciti: %u\n", usciti);
	printf("   EAGAIN (nessun pacchetto per quel blocco): %u\n", eagain);
	printf("   primo pts uscito: %lld (atteso 0)\n", (long long)primo_pts);
	printf("   scarto fra blocco dato e pacchetto uscito: %lld campioni "
	       "(%.2f ms), e %s\n",
	       (long long)scarto_primo, (double)scarto_primo * 1000.0 / FREQUENZA,
	       scarto_varia ? "⛔ VARIA" : "⭐ COSTANTE");
	printf("   initial_padding dichiarato: %d campioni (%.2f ms)\n",
	       ctx->initial_padding,
	       (double)ctx->initial_padding * 1000.0 / FREQUENZA);

	printf("\n");
	if (entrati == usciti && eagain == 0 && !scarto_varia) {
		printf("⭐ VERDE — UNO PER UNO: %u blocchi entrati, %u pacchetti "
		       "usciti, zero EAGAIN.\n", entrati, usciti);
		printf("   ⇒ Il codificatore NON accumula, quindi l'`istante` di §6.3 "
		       "appartiene al blocco che parte.\n");
		printf("   ⛔ E allora il commento di `audio.h` — «puo' non produrre un "
		       "pacchetto per ogni blocco offerto» — e' la giustificazione "
		       "scritta di un ramo che non si percorre: va corretto.\n");
		if (scarto_primo)
			printf("   ⚠ Resta uno scarto COSTANTE di %lld campioni (%.2f ms): "
			       "e' il `pre-skip` di Opus, che il decodificatore toglie da "
			       "se'.  Non deriva e non tocca l'ordinamento di §6.3 — ma "
			       "va DICHIARATO, non taciuto.\n",
			       (long long)scarto_primo,
			       (double)scarto_primo * 1000.0 / FREQUENZA);
	} else {
		printf("⛔ ROSSO — libopus non e' uno-per-uno: %u entrati, %u usciti, "
		       "%u EAGAIN, scarto %s.\n", entrati, usciti, eagain,
		       scarto_varia ? "VARIABILE" : "costante");
		printf("   ⇒ L'`istante` scritto sul filo NON e' quello del blocco "
		       "spedito, e va portato attraverso con il `pts` del pacchetto.\n");
	}

	av_packet_free(&pk);
	av_frame_free(&fr);
	avcodec_free_context(&ctx);
	(void)scarto_massimo;
	return (entrati == usciti && eagain == 0 && !scarto_varia) ? 0 : 1;
}
