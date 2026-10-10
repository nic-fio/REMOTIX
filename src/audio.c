/* audio.c — the sound encoder.  The reasons are in `audio.h`. */

#include "audio.h"

#include "registro.h"

#include <opus.h>
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
 *        encoder state left BEFORE the stretch (the encoder simply never sees
 *        those blocks: since 30 September 2026 there is not even a `pts` to
 *        hold still, see `opus_apri()`).
 *        It is what Opus's DTX has always done; `[?]` inaudible, and from here
 *        NOT measured;
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

/*
 * ⛔ The space offered to `opus_encode()`, and it is libavcodec's to the
 *    letter: `(1275 * 6 + 7) * stream_count` (`[R]` FFmpeg 7.1,
 *    `libavcodec/libopusenc.c`, `libopus_encode()`), that is 7 657 bytes for
 *    our single stream.
 *
 * ⛔ And NOT `AUDIO_FUORI_MAX`, on purpose: with the ceiling passed as the space,
 *    libopus in VBR **would shrink** the packet to make it fit, instead
 *    of letting it out and having it dropped by the check below.  ⇒ It would be
 *    a behaviour DIFFERENT from the one measured, even if at 96 kbit/s it does
 *    not show (241-439 bytes, bitrate box).  It costs 7.6 KB per session.
 */
#define AUDIO_OPUS_SPAZIO (1275 * 6 + 7)

struct audio_cod {
	uint8_t codec; /* 1 = Opus, 2 = PCM */
	uint32_t blocco;
	uint64_t entrati, usciti;
	uint64_t taciuti; /* blocks of digital silence NOT sent */

	/* Opus only */
	OpusEncoder *enc;
	/* ⚠ The packet is born HERE and not in `fuori`: `opus_encode()` gets the
	 *   same space libavcodec gave it (see `AUDIO_OPUS_SPAZIO`), and the
	 *   `AUDIO_FUORI_MAX` ceiling stays a check AFTERWARDS, as it was. */
	uint8_t pacchetto[AUDIO_OPUS_SPAZIO];
};

/*
 * ⛔⭐ OPUS TALKS TO `libopus` DIRECTLY — phase 18, 30 September 2026
 *      (`DECISIONI.md` §10.22 and §10.25: ffmpeg leaves the product).
 *
 * Until 29 September it went through libavcodec, which called the SAME
 * `libopus.so.0` with its wrapper `libopusenc.c`.  ⇒ Removing the wrapper
 * does not change the encoder: it only changes who dictates its parameters.  So
 * the parameters are dictated **all of them**, even those that match libopus's
 * default, because the default that counted was libavcodec's, and
 * two of them do NOT match libopus's:
 *
 *   parameter              libavcodec 7.1 (`[R]` libopusenc.c)   libopus 1.5.2
 *   ---------------------  -----------------------------------  -------------
 *   application            `audio` (we asked for it)            to be chosen
 *   frame duration         20 ms (we asked for it)              to be chosen
 *   bitrate                96 000 (we asked for it)             automatic
 *   ⛔ complexity          **10** (`compression_level` = 10)    9
 *   VBR                    on (`vbr` = on)                      on
 *   ⛔ constrained VBR     **NO** (`vbr == 2` false)            **YES**
 *   expected loss          0 %                                  0 %
 *   in-band FEC            off                                  off
 *   phase inversion        allowed (`apply_phase_inv`)          allowed
 *   Opus DTX               never touched (7.1 lacks the option) off
 *   maximum bandwidth      never touched (`cutoff` = 0)         full
 *
 * ⚠ And the form: libavcodec opened a **multistream** encoder with one coupled
 *   stream (`opus_multistream_encoder_create(…, 1, 1, {0, 1}, …)`), here there
 *   is a plain one.  `[M]` 30 Sep 2026, inside `remotix-costruzione`
 *   (libopus 1.5.2, libavcodec 61 of FFmpeg 7.1.5): the two, and libavcodec's,
 *   on the same 1 500 blocks (speech, music, full-scale square
 *   wave) give **1 500 packets of 1 500 identical byte for byte**,
 *   439 216 bytes each.  ⇒ The multistream is not carried over: it is a
 *   wrapper that with a single stream adds nothing.
 *
 * ⭐ And the bench that keeps it true is `banchi/18-a1/`: the old `audio.c`
 *    (545ec55) and this one, linked together, on the same 42 s signal
 *    (speech, music, digital silence, full-scale jumps, one-block gaps,
 *    ±1 LSB, loud noise, pure tone).  `[M]` 30 Sep 2026 on the server
 *    (`devroot`, libopus 1.5.2): cure ON 1 860 packets + 240 muted,
 *    519 998 bytes; OFF 2 100 packets, 549 180 bytes — in both
 *    **every packet identical byte for byte**, 0 decoded samples
 *    different out of 4 032 000; all full-band CELT (config 31), stereo,
 *    code 0; no 1-2 byte packet (Opus's DTX stays off); the
 *    silence sent with the cure off weighs 3 bytes, as in `09-b84`.
 *
 * ⭐ And the question of `banchi/07-b44` falls by itself (does the encoder hold
 *    back a block?): `opus_encode()` is SYNCHRONOUS, one block in and one packet
 *    out by construction.  ⇒ The `EAGAIN` branch no longer exists, instead of
 *    staying written and never taken.
 */
static bool opus_ctl_o_di(int e, const char *che)
{
	if (e == OPUS_OK)
		return true;
	registro_dice(REG_AUDIO, "⛔ opus_encoder_ctl(%s): %s", che,
	              opus_strerror(e));
	return false;
}

static bool opus_apri(audio_cod *c)
{
	int e = OPUS_OK;
	opus_int32 v = 0;

	c->enc = opus_encoder_create(AUDIO_FREQUENZA, AUDIO_CANALI,
	                             OPUS_APPLICATION_AUDIO, &e);
	if (!c->enc || e != OPUS_OK) {
		registro_dice(REG_AUDIO,
		              "⛔ opus_encoder_create: %s.  ⚠ No fallback to PCM "
		              "from here: the codec is negotiated (§4.3), and sending PCM to "
		              "someone expecting Opus produces NOISE instead of an error",
		              opus_strerror(e));
		return false;
	}

	/* ⛔ In libavcodec's order (`libopus_configure_encoder()`), and each one
	 *    checked: a `ctl` refused and kept quiet would be a parameter we
	 *    believe we have set. */
	if (!opus_ctl_o_di(opus_encoder_ctl(c->enc, OPUS_SET_BITRATE(AUDIO_OPUS_BITRATE)), "BITRATE") ||
	    !opus_ctl_o_di(opus_encoder_ctl(c->enc, OPUS_SET_COMPLEXITY(10)), "COMPLEXITY") ||
	    !opus_ctl_o_di(opus_encoder_ctl(c->enc, OPUS_SET_VBR(1)), "VBR") ||
	    !opus_ctl_o_di(opus_encoder_ctl(c->enc, OPUS_SET_VBR_CONSTRAINT(0)), "VBR_CONSTRAINT") ||
	    !opus_ctl_o_di(opus_encoder_ctl(c->enc, OPUS_SET_PACKET_LOSS_PERC(0)), "PACKET_LOSS_PERC") ||
	    !opus_ctl_o_di(opus_encoder_ctl(c->enc, OPUS_SET_INBAND_FEC(0)), "INBAND_FEC") ||
	    !opus_ctl_o_di(opus_encoder_ctl(c->enc, OPUS_SET_PHASE_INVERSION_DISABLED(0)), "PHASE_INVERSION_DISABLED"))
		return false;

	/* ⛔ And we CHECK that it obeyed, instead of believing it — as before
	 *    libavcodec's `frame_size` was checked.  ⚠ The frame duration here is
	 *    not a setting: it is the 960 frames that `opus_encode()` gets at
	 *    every call (§5.3), and a number libopus does not accept is an error
	 *    at the call, not a crooked sound.
	 *    ⇒ The bitrate is read back, which is the number the probe measured. */
	if (!opus_ctl_o_di(opus_encoder_ctl(c->enc, OPUS_GET_BITRATE(&v)), "GET_BITRATE"))
		return false;
	if (v != AUDIO_OPUS_BITRATE) {
		registro_dice(REG_AUDIO,
		              "⛔ libopus holds %d bit/s, and we asked for %d.  "
		              "It does not adapt silently: it is declared",
		              (int)v, (int)AUDIO_OPUS_BITRATE);
		return false;
	}
	/* ⚠ The `pre-skip` (`audio.h`, `[M]` 312 samples = 6.50 ms) is DECLARED
	 *   even now that no `pts` carries it: it is the same quantity, and whoever
	 *   one day synchronises audio and video will look for it here. */
	if (opus_encoder_ctl(c->enc, OPUS_GET_LOOKAHEAD(&v)) != OPUS_OK)
		v = -1;

	registro_dice(REG_AUDIO,
	              "⭐ Opus opened: 48 000 Hz, 2 channels, blocks of %d frames "
	              "(20 ms), %d bit/s free VBR, complexity 10, pre-skip %d "
	              "samples — «libopus» %s directly, without libavcodec",
	              AUDIO_BLOCCO_OPUS, (int)AUDIO_OPUS_BITRATE, (int)v,
	              opus_get_version_string());
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
	if (c->enc)
		opus_encoder_destroy(c->enc);
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
	 * ⛔ And the encoder simply DOES NOT SEE those blocks: its
	 *    state stays that of the last block played.  ⚠ Until 29 Sep
	 *    2026 libavcodec's `pts` was also held still here (it would have
	 *    seen a jump); with `opus_encode()` time does not enter the
	 *    call, and the behaviour is the same by construction: `[M]` 30
	 *    Sep 2026, `banchi/18-a1`, the packets AFTER a muted stretch come out
	 *    identical byte for byte to libavcodec's. */
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

	/* ⛔ One call, one packet: `opus_encode()` is synchronous, and it reads the
	 *    samples where they are (s16 interleaved in machine order, which is
	 *    what it wants) — no copy into an intermediate frame, and no
	 *    allocation per block (before there were an `AVPacket` and its payload,
	 *    50 times a second). */
	e = opus_encode(c->enc, campioni, AUDIO_BLOCCO_OPUS, c->pacchetto,
	                AUDIO_OPUS_SPAZIO);
	if (e < 0) {
		registro_dice(REG_AUDIO, "⛔ opus_encode: %s", opus_strerror(e));
		return false;
	}

	if ((size_t)e > AUDIO_FUORI_MAX) {
		/* ⛔ An Opus packet is not truncated: a maimed packet is not a worse
		 *    sound, it is a packet the decoder refuses. */
		registro_dice(REG_AUDIO,
		              "⛔ Opus packet of %d bytes, over the ceiling of %d — "
		              "dropped instead of truncated",
		              e, AUDIO_FUORI_MAX);
		return false;
	}
	memcpy(fuori, c->pacchetto, (size_t)e);
	*quanti = (size_t)e;
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
