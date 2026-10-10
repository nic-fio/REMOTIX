/* audio.c — the sound encoder.  The reasons are in `audio.h`. */

#include "audio.h"

#include "registro.h"

#include <libavcodec/avcodec.h>
#include <libavutil/channel_layout.h>
#include <libavutil/opt.h>
#include <stdlib.h>
#include <string.h>

#define REG_AUDIO "audio"

/*
 * ⛔ The Opus bitrate, and the number is 🔸 DERIVED — not decided by the user.
 *
 * 96 kbit/s in stereo is the bandwidth at which Opus is transparent for music
 * according to its own documentation `[S]`.  ⚠ On the 17 August probe a
 * 20 ms block at this bitrate measures **241-376 bytes** on Chrome and
 * **309-439** on Firefox `[M]`: it fits in the datagram with a wide margin, which
 * is the reason a higher one was not chosen.
 *
 * ⏳ It must be put on record in `DECISIONI.md` the day the user hears it:
 *    `SPECIFICHE.md` §10 does not name the bitrate, and a number without an
 *    entry is a decision half taken (`LEZIONI.md` §2.3-quater).
 */
#define AUDIO_OPUS_BITRATE 96000

/*
 * ⛔⭐⭐ SILENCE IS NOT SENT — cure of phase 9, and since 24 August 2026 it is
 *       BORN **ON** (the user's decision; until the 23rd it was born off for
 *       invariant I6).
 *
 * `[M]` 24 August 2026, `banchi/09-b84-audio-silenzio.py`, port 7972, binary
 * `b484d699…`: a session with **Opus** negotiated and the desktop STILL delivers
 *
 *     50 datagrams per second · **3 bytes of payload each** · PEAK 0 of 32767
 *
 * that is **1.2 kbit/s** of real sound.  ⛔ And on the wire those 50 datagrams cost
 * **589 kbit/s**, because each one takes a WHOLE 1444-byte packet
 * (`webtransport.c`, `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING`).  ⇒ **99.8 %** of
 * that traffic is padding, and it pays the same congestion window as the
 * video.
 *
 * ⭐ And there is nothing to invent to remove it.  `RCP.md` §6.3 puts the
 *    `istante` inside every datagram and the receiver puts the blocks back in
 *    their ABSOLUTE place.  ⇒ **A block not sent is a gap, and a gap is
 *    silence** — which is exactly what that block contained.  Nothing is
 *    approximated: we stop sending the zero.
 *
 * ⛔ AND THERE IS NO THRESHOLD, ON PURPOSE.  Only **digital** silence is muted —
 *    all samples exactly `0` — because that is not a judgement: it is
 *    the only case in which "sent" and "not sent" sound IDENTICAL.  A
 *    threshold ("below -60 dB") would be a decision about the user's sound taken
 *    by the code, that is precisely the thing I6 wants behind a switch
 *    and that this phase has not measured.
 *
 * ⚠ THE PRICE, DECLARED — two items, and they are the reason the switch
 *   exists instead of being obvious:
 *     1. on Opus the first block after a stretch of silence restarts with the
 *        encoder state left BEFORE the stretch (here the `pts` does not
 *        advance, on purpose, or libavcodec would see a jump).  It is what
 *        Opus's DTX has always done; `[?]` inaudible, and from here NOT measured;
 *     2. the receiver sees a jump in `istante` and its counters count it
 *        as **`mancato`** — that is, a number that today means "lost"
 *        would start to also mean "there was nothing to send".
 *        ⛔ The bench measures it paired on purpose, and declares it.
 *
 * ⛔⛔⭐ AND THE SWITCH IS NO LONGER A BUILD ONE — 24 August 2026.
 *
 *      Until 23 August it was `-DAUDIO_SILENZIO_PREDEFINITO=1`, and it was not a
 *      choice of convenience: the encoder lives in the **child**, which is an
 *      `execve` with an environment **built from scratch** (`figlio.c`, the box
 *      of the two cures of phase 9) — a `REMOTIX_...` does not reach it, and would
 *      not even leave a line saying it did not arrive.  The only channel
 *      that crosses the `exec` is the tail of `argv`.
 *
 *      ⇒ Now the way exists, and it is that of `--parlantina`:
 *        · `main.c`   recognises `--niente-audio-silenzio` and keeps a `bool`;
 *        · `figlio.c` puts it at the end of `argv` (`diventa_ed_esegui()`) and
 *                     reads it back **by name** in `figlio_vive()`, calling
 *                     `audio_silenzio_taci()`;
 *        · here       nothing changes: `audio_silenzio_taci()` was already there.
 *
 * ⛔⛔ AND THE `-D` WAS REMOVED, not left beside it: two ways to switch on
 *      the same cure are two numbers that can diverge — the same reason
 *      the environment bridge of `wt_sgombra_soglia()` was removed on
 *      23 August.  ⚠ Whoever rebuilds `09-b84-audio-silenzio.py` must know
 *      that its arm B is no longer made with a `-D`, but with the command
 *      line: the OFF arm is now `--niente-audio-silenzio`.
 *
 * ⭐⭐⭐ AND IT IS BORN ON since 24 August 2026 — the user's decision, after having
 *      looked (§19.6, §20.3).  ⚠ `[M]` 24 Aug 2026, bench `09-b84`: **102.1
 *      times** less traffic with the screen still (557.6 → 5.5 kbit/s), pure test
 *      tone **1.000**, coverage **0.9996**, **1 248 blocks muted of 1 248**.
 *      ⚠ The price, declared: the client's `mancati` rise by **2 in
 *      5 000** — a WANTED gap leaves the same jump in `istante` as a lost
 *      one, and a number that meant "lost" starts to also mean
 *      "there was nothing to send".
 */
static bool audio_taci_silenzio = true;

void audio_silenzio_taci(bool si)
{
	audio_taci_silenzio = si;
}

bool audio_silenzio_acceso(void)
{
	return audio_taci_silenzio;
}

struct audio_cod {
	uint8_t codec; /* 1 = Opus, 2 = PCM */
	uint32_t blocco;
	uint64_t entrati, usciti;
	uint64_t taciuti; /* blocks of digital silence NOT sent */

	/* Opus only */
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

	/* ⛔ The encoder is asked for BY NAME, and no substitute is accepted.
	 *    `CODER.md` §3.9: "a component that chooses on its own produces two
	 *    different measurements under the same label".  ⚠ `avcodec_find_encoder`
	 *    with `AV_CODEC_ID_OPUS` could return FFmpeg's NATIVE encoder,
	 *    which is declared **experimental** and is not what the probe
	 *    measured. */
	cod = avcodec_find_encoder_by_name("libopus");
	if (!cod) {
		registro_dice(REG_AUDIO,
		              "⛔ the «libopus» encoder is not in this libavcodec.  "
		              "⚠ No fallback to PCM from here: the codec is negotiated "
		              "(§4.3), and sending PCM to someone expecting Opus produces NOISE "
		              "instead of an error");
		return false;
	}

	c->ctx = avcodec_alloc_context3(cod);
	if (!c->ctx)
		return false;

	c->ctx->sample_rate = AUDIO_FREQUENZA;
	c->ctx->sample_fmt = AV_SAMPLE_FMT_S16;
	c->ctx->bit_rate = AUDIO_OPUS_BITRATE;
	av_channel_layout_default(&c->ctx->ch_layout, AUDIO_CANALI);
	/* 20 ms per packet, which is what §5.3 imposes and not what
	 * the encoder would choose if nobody told it. */
	av_opt_set(c->ctx->priv_data, "frame_duration", "20", 0);
	av_opt_set(c->ctx->priv_data, "application", "audio", 0);

	e = avcodec_open2(c->ctx, cod, NULL);
	if (e < 0) {
		char m[128];
		av_strerror(e, m, sizeof m);
		registro_dice(REG_AUDIO, "⛔ avcodec_open2(libopus): %s", m);
		return false;
	}

	/* ⛔ And we CHECK that it obeyed, instead of believing it.  If the encoder
	 *    chose a `frame_size` different from the 960 of §5.3, the blocks we
	 *    give it would be the wrong size and the sound would come out crooked
	 *    **without an error anywhere**. */
	if (c->ctx->frame_size != AUDIO_BLOCCO_OPUS) {
		registro_dice(REG_AUDIO,
		              "⛔ libopus chose blocks of %d frames, and §5.3 "
		              "wants %d (20 ms).  It does not adapt silently: it is declared",
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
	              "⭐ Opus opened: 48 000 Hz, 2 channels, blocks of %d frames "
	              "(20 ms), %d bit/s — libavcodec's «libopus» encoder",
	              c->ctx->frame_size, (int)AUDIO_OPUS_BITRATE);
	return true;
}

audio_cod *audio_cod_apri(uint8_t codec)
{
	audio_cod *c = calloc(1, sizeof *c);
	if (!c)
		return NULL;
	c->codec = codec;

	/* ⛔ The switch is DECLARED even when it is off: "the cure is not there"
	 *    and "the cure is there and did nothing" must have two different lines
	 *    (`CODER.md` §3.10).  ⚠ It is the line on which the paired bench checks
	 *    that it really switched on two different arms. */
	registro_dice(REG_AUDIO,
	              "digital silence cure: %s",
	              audio_taci_silenzio
	                  ? "⭐ ON — blocks that are all zero are not sent.  "
	                    "It is the DEFAULT since 24 August 2026 (the user's "
	                    "decision).  `[M]` 09-b84: 102.1 times less traffic with "
	                    "the screen still (557.6 → 5.5 kbit/s), 1 248 blocks muted "
	                    "of 1 248.  ⚠ The price: the client's «mancati» rise "
	                    "by 2 in 5 000.  ⛔ Switched off with `--niente-audio-silenzio`"
	                  : "⛔ OFF by hand (`--niente-audio-silenzio`) — "
	                    "silence is sent too, that is the product until 23 "
	                    "August 2026.  ⚠ And it is NOT the default: since 24 August "
	                    "it is born ON");

	if (codec == 2) {
		c->blocco = AUDIO_BLOCCO_PCM;
		registro_dice(REG_AUDIO,
		              "⭐ PCM opened: 48 000 Hz, 2 channels, s16 little-endian, "
		              "blocks of %u frames (5 ms) = %u bytes (§5.3)",
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
	              "⛔ unknown audio codec %u: RCP/1 defines two, "
	              "1 = Opus and 2 = PCM (§6.3)",
	              codec);
	free(c);
	return NULL;
}

void audio_cod_chiudi(audio_cod *c)
{
	if (!c)
		return;
	/* ⛔⭐ THE CURE'S COUNT IS WRITTEN AT CLOSING, AND IT IS THE ONLY MOMENT
	 *     IT IS COMPLETE (`CODER.md` §3.10).  ⚠ The inner line comes out on
	 *     the first and then one every thousand: whoever reads only that can say
	 *     "at least N", not "N" — and a bench that confused the two would write a
	 *     number that looks measured.  ⭐ And it is written **with the zeros in**:
	 *     "the cure was off" and "the cure was on and muted nothing"
	 *     are two different facts, and it is the difference the tone scene is
	 *     judged on. */
	registro_dice(REG_AUDIO,
	              "silence cure count (%s): %llu blocks muted "
	              "of %llu in, %llu out on the wire — codec %u",
	              audio_taci_silenzio
	                  ? "ON, and it is the default since 24 Aug 2026"
	                  : "OFF by hand, --niente-audio-silenzio",
	              (unsigned long long)c->taciuti,
	              (unsigned long long)c->entrati,
	              (unsigned long long)c->usciti, c->codec);
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

/* ⛔ PCM is written LITTLE-endian by hand, not with a `memcpy`.
 *
 *    A `memcpy` would give machine order: right on x86, silently
 *    wrong on a big-endian ARM — and the symptom is not an error, it is
 *    full-scale noise.  ⚠ It costs two lines and removes a defect that would
 *    show only on the one machine where nobody tests it. */
static void pcm_scrivi(const int16_t *campioni, uint32_t fotogrammi, uint8_t *fuori)
{
	uint32_t n = fotogrammi * AUDIO_CANALI;
	for (uint32_t i = 0; i < n; i++) {
		uint16_t v = (uint16_t)campioni[i];
		fuori[i * 2] = (uint8_t)(v & 0xFF);
		fuori[i * 2 + 1] = (uint8_t)(v >> 8);
	}
}

/* ⛔ DIGITAL silence: all samples exactly zero, no thresholds.  ⚠ The
 *    loop costs `blocco * 2` integer comparisons — 480 for a PCM block, 1920
 *    for an Opus one, fifty times a second — and it is less work than the
 *    `memcpy` the encoder does right after.  ⭐ And it exits at the FIRST
 *    non-zero sample: on real sound the cost is one read. */
static bool tutto_zero(const int16_t *campioni, uint32_t fotogrammi)
{
	uint32_t n = fotogrammi * AUDIO_CANALI;
	for (uint32_t i = 0; i < n; i++)
		if (campioni[i] != 0)
			return false;
	return true;
}

bool audio_cod_passa(audio_cod *c, const int16_t *campioni, uint8_t *fuori,
                     size_t *quanti)
{
	int e;

	if (!c || !campioni || !fuori || !quanti)
		return false;
	c->entrati++;

	/* ⛔⭐ THE SILENCE CURE — off by itself, and the box is at the top.
	 *
	 * ⚠ It returns `false` **before** the encoder, and that is what
	 *   `audio.h` already promises: *"Returns `false` when there is nothing to
	 *   send.  The caller sends nothing and goes on"*.  ⇒ No
	 *   caller changes, and the `istante` of §6.3 keeps advancing by itself
	 *   in `figlio.c` — which is what makes the gap a silence in the right
	 *   place instead of a shift of everything that follows.
	 *
	 * ⛔ And the Opus `pts` does NOT move: libavcodec would see a jump, and a
	 *    jump is something we have not measured.  Here the encoder
	 *    simply does not see those blocks. */
	if (audio_taci_silenzio && tutto_zero(campioni, c->blocco)) {
		c->taciuti++;
		/* ⚠ With a floor, or a mute desktop would fill the log instead of
		 *   telling about it: the first and then one every thousand (20 s of Opus, 5 of PCM). */
		if (c->taciuti == 1 || c->taciuti % 1000 == 0)
			registro_dice(REG_AUDIO,
			              "⭐ DIGITAL silence: %llu blocks not sent of "
			              "%llu in (I6, cure on).  ⚠ The receiver will see "
			              "a jump in `istante` and will count it among the «mancati»: "
			              "it is a WANTED gap, not a loss",
			              (unsigned long long)c->taciuti,
			              (unsigned long long)c->entrati);
		return false;
	}

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
		/* ⛔ BRANCH MEASURED AND NEVER TAKEN — `[M]` 17 August 2026,
		 *    `banchi/07-b44`: 1000 blocks in, 1000 packets out, zero
		 *    EAGAIN.  ⚠ It stays because the API allows it, ⭐ but now IT SHOWS
		 *    if it is taken: before, it returned `false` silently, and then
		 *    "Opus is accumulating" would have been indistinguishable from "the block
		 *    did not arrive".  And if one day it were taken, the `istante` of §6.3
		 *    would no longer belong to the block that leaves. */
		if (!c->eagain_detto) {
			c->eagain_detto = true;
			registro_dice(REG_AUDIO,
			              "⛔ libopus held back a block (EAGAIN) — and "
			              "`banchi/07-b44` says it never happens.  ⚠ From here "
			              "on the `istante` of §6.3 may not be that "
			              "of the block sent");
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
		/* ⛔ An Opus packet is not truncated: a maimed packet is not a worse
		 *    sound, it is a packet the decoder refuses. */
		registro_dice(REG_AUDIO,
		              "⛔ Opus packet of %d bytes, over the ceiling of %d — "
		              "dropped instead of truncated",
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

/* ⛔ The third number is kept apart and NOT inside `audio_cod_conti()`: that
 *    function already has a caller (`webtransport.c:6891`) and changing its
 *    signature would mean touching a file that is not this module's. */
uint64_t audio_cod_taciuti(const audio_cod *c)
{
	return c ? c->taciuti : 0;
}
