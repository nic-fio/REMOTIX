/* audio.c — il codificatore del suono.  Le ragioni stanno in `audio.h`. */

#include "audio.h"

#include "registro.h"

#include <libavcodec/avcodec.h>
#include <libavutil/channel_layout.h>
#include <libavutil/opt.h>
#include <stdlib.h>
#include <string.h>

#define REG_AUDIO "audio"

/*
 * ⛔ Il bitrate di Opus, e il numero e' 🔸 DERIVATO — non deciso dall'utente.
 *
 * 96 kbit/s in stereo e' la banda a cui Opus e' trasparente per la musica
 * secondo la sua stessa documentazione `[S]`.  ⚠ Sulla sonda del 17 agosto un
 * blocco da 20 ms a questo bitrate misura **241-376 byte** su Chrome e
 * **309-439** su Firefox `[M]`: sta nel datagram con un margine largo, che e'
 * la ragione per cui non si e' scelto piu' alto.
 *
 * ⏳ Va messo a verbale in `DECISIONI.md` il giorno in cui l'utente lo sente:
 *    `SPECIFICHE.md` §10 il bitrate non lo nomina, e un numero senza una voce
 *    e' una decisione presa a meta' (`LEZIONI.md` §2.3-quater).
 */
#define AUDIO_OPUS_BITRATE 96000

struct audio_cod {
	uint8_t codec; /* 1 = Opus, 2 = PCM */
	uint32_t blocco;
	uint64_t entrati, usciti;

	/* solo per Opus */
	AVCodecContext *ctx;
	AVFrame *frame;
	AVPacket *pkt;
	int64_t pts;
	bool eagain_detto;
};

static bool opus_apri(audio_cod *c)
{
	const AVCodec *cod;
	int e;

	/* ⛔ Si chiede l'encoder PER NOME, e non si accetta un sostituto.
	 *    `CODER.md` §3.9: «un componente che sceglie in autonomia produce due
	 *    misure diverse sotto la stessa etichetta».  ⚠ `avcodec_find_encoder`
	 *    con `AV_CODEC_ID_OPUS` potrebbe restituire l'encoder NATIVO di
	 *    FFmpeg, che e' dichiarato **sperimentale** e non e' quel che la sonda
	 *    ha misurato. */
	cod = avcodec_find_encoder_by_name("libopus");
	if (!cod) {
		registro_dice(REG_AUDIO,
		              "⛔ l'encoder «libopus» non c'e' in questa libavcodec.  "
		              "⚠ Non si ripiega su PCM da qui: il codec e' negoziato "
		              "(§4.3), e spedire PCM a chi aspetta Opus produce RUMORE "
		              "invece di un errore");
		return false;
	}

	c->ctx = avcodec_alloc_context3(cod);
	if (!c->ctx)
		return false;

	c->ctx->sample_rate = AUDIO_FREQUENZA;
	c->ctx->sample_fmt = AV_SAMPLE_FMT_S16;
	c->ctx->bit_rate = AUDIO_OPUS_BITRATE;
	av_channel_layout_default(&c->ctx->ch_layout, AUDIO_CANALI);
	/* 20 ms per pacchetto, che e' quel che §5.3 impone e non quel che
	 * l'encoder sceglierebbe se nessuno glielo dicesse. */
	av_opt_set(c->ctx->priv_data, "frame_duration", "20", 0);
	av_opt_set(c->ctx->priv_data, "application", "audio", 0);

	e = avcodec_open2(c->ctx, cod, NULL);
	if (e < 0) {
		char m[128];
		av_strerror(e, m, sizeof m);
		registro_dice(REG_AUDIO, "⛔ avcodec_open2(libopus): %s", m);
		return false;
	}

	/* ⛔ E si VERIFICA che abbia obbedito, invece di crederci.  Se l'encoder
	 *    scegliesse un `frame_size` diverso dai 960 di §5.3, i blocchi che gli
	 *    diamo sarebbero della misura sbagliata e il suono uscirebbe storto
	 *    **senza un errore da nessuna parte**. */
	if (c->ctx->frame_size != AUDIO_BLOCCO_OPUS) {
		registro_dice(REG_AUDIO,
		              "⛔ libopus ha scelto blocchi da %d fotogrammi, e §5.3 ne "
		              "vuole %d (20 ms).  Non si adatta in silenzio: si dichiara",
		              c->ctx->frame_size, AUDIO_BLOCCO_OPUS);
		return false;
	}

	c->frame = av_frame_alloc();
	c->pkt = av_packet_alloc();
	if (!c->frame || !c->pkt)
		return false;
	c->frame->format = AV_SAMPLE_FMT_S16;
	c->frame->sample_rate = AUDIO_FREQUENZA;
	c->frame->nb_samples = AUDIO_BLOCCO_OPUS;
	av_channel_layout_default(&c->frame->ch_layout, AUDIO_CANALI);
	if (av_frame_get_buffer(c->frame, 0) < 0)
		return false;

	registro_dice(REG_AUDIO,
	              "⭐ Opus aperto: 48 000 Hz, 2 canali, blocchi da %d fotogrammi "
	              "(20 ms), %d bit/s — encoder «libopus» di libavcodec",
	              c->ctx->frame_size, (int)AUDIO_OPUS_BITRATE);
	return true;
}

audio_cod *audio_cod_apri(uint8_t codec)
{
	audio_cod *c = calloc(1, sizeof *c);
	if (!c)
		return NULL;
	c->codec = codec;

	if (codec == 2) {
		c->blocco = AUDIO_BLOCCO_PCM;
		registro_dice(REG_AUDIO,
		              "⭐ PCM aperto: 48 000 Hz, 2 canali, s16 little-endian, "
		              "blocchi da %u fotogrammi (5 ms) = %u byte (§5.3)",
		              c->blocco, c->blocco * AUDIO_CANALI * 2u);
		return c;
	}
	if (codec == 1) {
		c->blocco = AUDIO_BLOCCO_OPUS;
		if (!opus_apri(c)) {
			audio_cod_chiudi(c);
			return NULL;
		}
		return c;
	}

	registro_dice(REG_AUDIO,
	              "⛔ codec audio %u sconosciuto: RCP/1 ne definisce due, "
	              "1 = Opus e 2 = PCM (§6.3)",
	              codec);
	free(c);
	return NULL;
}

void audio_cod_chiudi(audio_cod *c)
{
	if (!c)
		return;
	if (c->pkt)
		av_packet_free(&c->pkt);
	if (c->frame)
		av_frame_free(&c->frame);
	if (c->ctx)
		avcodec_free_context(&c->ctx);
	free(c);
}

uint32_t audio_cod_blocco(const audio_cod *c)
{
	return c ? c->blocco : 0;
}

/* ⛔ Il PCM si scrive LITTLE-endian a mano, non con una `memcpy`.
 *
 *    Una `memcpy` darebbe l'ordine della macchina: giusto su x86, silenziosamente
 *    sbagliato su un ARM big-endian — e il sintomo non e' un errore, e' rumore a
 *    fondo scala.  ⚠ Costa due righe e toglie di mezzo un difetto che si
 *    manifesterebbe solo sull'unica macchina dove nessuno lo prova. */
static void pcm_scrivi(const int16_t *campioni, uint32_t fotogrammi, uint8_t *fuori)
{
	uint32_t n = fotogrammi * AUDIO_CANALI;
	for (uint32_t i = 0; i < n; i++) {
		uint16_t v = (uint16_t)campioni[i];
		fuori[i * 2] = (uint8_t)(v & 0xFF);
		fuori[i * 2 + 1] = (uint8_t)(v >> 8);
	}
}

bool audio_cod_passa(audio_cod *c, const int16_t *campioni, uint8_t *fuori,
                     size_t *quanti)
{
	int e;

	if (!c || !campioni || !fuori || !quanti)
		return false;
	c->entrati++;

	if (c->codec == 2) {
		size_t n = (size_t)c->blocco * AUDIO_CANALI * 2;
		if (n > AUDIO_FUORI_MAX)
			return false;
		pcm_scrivi(campioni, c->blocco, fuori);
		*quanti = n;
		c->usciti++;
		return true;
	}

	if (av_frame_make_writable(c->frame) < 0)
		return false;
	memcpy(c->frame->data[0], campioni,
	       (size_t)AUDIO_BLOCCO_OPUS * AUDIO_CANALI * sizeof(int16_t));
	c->frame->pts = c->pts;
	c->pts += AUDIO_BLOCCO_OPUS;

	e = avcodec_send_frame(c->ctx, c->frame);
	if (e < 0) {
		char m[128];
		av_strerror(e, m, sizeof m);
		registro_dice(REG_AUDIO, "⛔ avcodec_send_frame: %s", m);
		return false;
	}

	e = avcodec_receive_packet(c->ctx, c->pkt);
	if (e == AVERROR(EAGAIN)) {
		/* ⛔ RAMO MISURATO E MAI PERCORSO — `[M]` 17 agosto 2026,
		 *    `banchi/07-b44`: 1000 blocchi dentro, 1000 pacchetti fuori, zero
		 *    EAGAIN.  ⚠ Resta perche' l'API lo ammette, ⭐ ma adesso SI VEDE
		 *    se si percorre: prima tornava `false` in silenzio, e allora
		 *    «Opus accumula» sarebbe stato indistinguibile da «il blocco non
		 *    e' arrivato».  E se un giorno si percorresse, l'`istante` di §6.3
		 *    non apparterrebbe piu' al blocco che parte. */
		if (!c->eagain_detto) {
			c->eagain_detto = true;
			registro_dice(REG_AUDIO,
			              "⛔ libopus ha trattenuto un blocco (EAGAIN) — e "
			              "`banchi/07-b44` dice che non succede mai.  ⚠ Da qui "
			              "in poi l'`istante` di §6.3 puo' non essere quello "
			              "del blocco spedito");
		}
		return false;
	}
	if (e < 0) {
		char m[128];
		av_strerror(e, m, sizeof m);
		registro_dice(REG_AUDIO, "⛔ avcodec_receive_packet: %s", m);
		return false;
	}

	if ((size_t)c->pkt->size > AUDIO_FUORI_MAX) {
		/* ⛔ Non si tronca un pacchetto Opus: un pacchetto monco non e' un
		 *    suono peggiore, e' un pacchetto che il decodificatore rifiuta. */
		registro_dice(REG_AUDIO,
		              "⛔ pacchetto Opus di %d byte, oltre il tetto di %d — "
		              "buttato invece che troncato",
		              c->pkt->size, AUDIO_FUORI_MAX);
		av_packet_unref(c->pkt);
		return false;
	}
	memcpy(fuori, c->pkt->data, (size_t)c->pkt->size);
	*quanti = (size_t)c->pkt->size;
	av_packet_unref(c->pkt);
	c->usciti++;
	return true;
}

void audio_cod_conti(const audio_cod *c, uint64_t *entrati, uint64_t *usciti)
{
	if (entrati)
		*entrati = c ? c->entrati : 0;
	if (usciti)
		*usciti = c ? c->usciti : 0;
}
