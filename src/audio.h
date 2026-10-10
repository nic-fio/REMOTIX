/*
 * audio — the sound encoder: Opus, with PCM as the baseline.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE FORMAT IS NOT NEGOTIATED, AND IT IS NOT AN OPINION OF THIS FILE
 *
 * `RCP.md` §5.3 fixes it, and the reason is written there: "'Opus, with PCM
 * as the baseline' names the codec and not the format, and two
 * implementations that choose two different rates produce a noise that looks
 * like a network defect".
 *
 *   rate        48 000 Hz, always, for both codecs
 *   channels    2, interleaved
 *   Opus        one packet per datagram, 20 ms blocks         (960 frames)
 *   PCM         s16 LITTLE-endian, 5 ms per datagram          (240 frames)
 *
 * ⛔ The 5 ms of PCM are not a choice of convenience: they are `RCP.md` §5.3
 *    after finding R1.1, "the most serious of the 9 August review".  At 20 ms
 *    PCM would make 3852 bytes, and a QUIC datagram cannot be fragmented.
 *    ⭐ `[M]` 17 August 2026 (`banchi/07-b40`): the real datagram is **1024
 *    bytes on Chrome 151**, so the 972 of PCM fit by 52 bytes — and at
 *    20 ms they would not fit by a factor of four.
 *
 * ⛔ And PCM's little-endian is the only exception to the network order of §6,
 *    declared: it is a payload, like the HEVC bytes, not a protocol field.
 *    ⚠ A bench that read it big-endian sees no error: it sees FULL-SCALE
 *    NOISE, which is the defect of v1 (`LEZIONI.md` §2.2), and
 *    `banchi/07-b40` grafts it on purpose as a positive control.
 *
 * ---------------------------------------------------------------------------
 * ⭐ OPUS GOES THROUGH `libopus` DIRECTLY — since 30 September 2026 (phase 18,
 *    `DECISIONI.md` §10.22 and §10.25: ffmpeg leaves the product for licensing).
 *
 * ⛔ Until 29 September it went through `libavcodec`, and the reason was written
 *    here: `[M]` 17 August 2026, `libavcodec` 61.19.101 was already linked to
 *    `libopus.so.0`, and so no package was added to two build
 *    environments.  ⇒ With libavcodec gone, that reason turns around: `libopus`
 *    is the dependency, and `opus.pc` is in both (`[M]` 30 Sep 2026:
 *    `remotix-costruzione` and the server's `devroot`, libopus 1.5.2).
 *
 * ⭐ The encoder is THE SAME (`libopus.so.0` was there before too, under the
 *    wrapper), and the parameters are those the wrapper dictated, all
 *    written in `audio.c` — ⚠ two do not match libopus's default
 *    (complexity 10, unconstrained VBR).  `[M]` 30 Sep 2026,
 *    `banchi/18-a1-opus-senza-ffmpeg.c`: packets **identical byte for byte**
 *    to those of libavcodec.  And the per-block `AVPacket` is gone.
 */
#pragma once

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* §5.3, and they hold for both codecs. */
#define AUDIO_FREQUENZA 48000
#define AUDIO_CANALI 2

/* How many frames (samples per channel) fit in a block, per codec. */
#define AUDIO_BLOCCO_OPUS 960 /* 20 ms */
#define AUDIO_BLOCCO_PCM 240  /*  5 ms */

typedef struct audio_cod audio_cod;

/*
 * Opens the encoder for the NEGOTIATED codec.
 *
 * `codec` 1 = Opus, 2 = PCM — the numbers of `RCP.md` §6.3, not the video ones.
 *
 * ⛔ Returns NULL and writes to the log if the codec is missing: `CODER.md` §4.2 —
 *    a fallback is declared.  ⚠ And it does NOT fall back to PCM on its own: the
 *    codec choice belongs to the negotiation (§4.3), and a server that sent PCM
 *    where the client expects Opus would produce noise instead of an error.
 */
audio_cod *audio_cod_apri(uint8_t codec);
void audio_cod_chiudi(audio_cod *c);

/* How many frames a block of this encoder wants. */
uint32_t audio_cod_blocco(const audio_cod *c);

/*
 * One block of samples goes in, one block ready for the datagram comes out.
 *
 * `campioni`  exactly `audio_cod_blocco()` frames, interleaved, s16
 *             in machine order.
 * `fuori`     at least `AUDIO_FUORI_MAX` bytes.
 *
 * ⛔⛔ THIS PARAGRAPH WAS REWRITTEN ON A MEASUREMENT — 17 August 2026,
 *      finding 7 of the adversarial review, closed by `banchi/07-b44`.
 *
 *      It said: *"Returns `false` when there is nothing to send, and it is NOT
 *      an error: Opus may not produce a packet for every block offered"*.
 *      ⛔ **IT IS FALSE for our configuration**, and the falsehood was not
 *      harmless: `RCP.md` §6.3 wants in `istante` the time of the **first
 *      sample of the block**, and if the encoder really accumulated, the
 *      packet coming out would carry the instant of a block DIFFERENT from the
 *      one it contains — wrong by 20 ms, forever.
 *
 *      `[M]` 1000 blocks in, **1000 packets out**, **zero EAGAIN**:
 *      `libopus` at a fixed 20 ms is ONE FOR ONE.  ⇒ The `istante` belongs to
 *      the block that leaves, and the `EAGAIN` branch **was never taken**.
 *      ⭐ Since 30 September 2026 the branch is not even there: `opus_encode()`
 *      is synchronous, one block in and one packet out by construction.
 *
 * ⚠⚠ AND THE MEASUREMENT FOUND ANOTHER THING, which nobody had declared: Opus's
 *     `pre-skip`.  `[M]` `initial_padding = 312 samples`, and the packets'
 *     `pts` comes out **shifted by -312 samples = -6.50 ms**, CONSTANT across
 *     all thousand.  ⚠ Without libavcodec there is no `pts` any more, but the
 *     quantity remains: `OPUS_GET_LOOKAHEAD`, `[M]` 30 Sep 2026 still **312**,
 *     and `audio.c` writes it to the log on opening.
 *     ⭐ It is not a defect and it does not drift: it is the lead the algorithm
 *     takes, and the **decoder removes it by itself** — end to end it
 *     cancels out.  And it does not touch the ordering of §6.3, which compares
 *     instants with each other and not with an external clock.
 *     ⛔ But it must be written down: an implementation that one day used these
 *     instants to synchronise audio with video would find 6.5 ms that no
 *     document explains — and that is the form of error this project pays for
 *     most (`LEZIONI.md` §2.2).
 *
 * ⛔ Returns `false` when there is nothing to send.  The caller sends
 *    nothing and goes on — an empty block sent is a block the client
 *    counts and does not hear.
 */
#define AUDIO_FUORI_MAX 1200
bool audio_cod_passa(audio_cod *c, const int16_t *campioni, uint8_t *fuori,
                     size_t *quanti);

/* The encoder's two numbers, for the log: blocks in and out. */
void audio_cod_conti(const audio_cod *c, uint64_t *entrati, uint64_t *usciti);

/*
 * ⛔⭐ THE DIGITAL SILENCE CURE — phase 9, and since 24 August 2026 it is BORN
 *     **ON** (the user's decision; until the 23rd it was born off for I6).
 *
 * On, a block in which **all** samples are exactly zero does not
 * become a datagram: `audio_cod_passa()` returns `false`, the caller sends
 * nothing, and the receiver — which places blocks at their absolute `istante`
 * (§6.3) — finds a gap.  ⭐ A gap is silence, that is what the block
 * contained: it is not an approximation, it is not sending the zero.
 *
 * `[M]` 24 August 2026, `banchi/09-b84`: with the desktop still and Opus
 * negotiated there are **50 datagrams per second of 3 bytes** that take
 * **589 kbit/s** of padded packets, that is 99.8 % padding — and the same
 * congestion window as the video.
 *
 * ⚠ The price, and the reason for the switch, are in the box at the top of
 *   `audio.c`.  ⛔⭐ And the switch is NO longer a build one: the `-D`
 *   `AUDIO_SILENZIO_PREDEFINITO` **was removed** on 24 August 2026, and the only
 *   way is `--niente-audio-silenzio` on the server's command line, which
 *   `figlio.c` copies to the end of the child's `argv` (where the
 *   encoder lives) as it already does with `--parlantina`.  ⚠ Two ways to the
 *   same cure are two numbers that diverge.
 *
 * ⛔ AND IT HOLDS FOR TWO PROCESSES: the real encoder is in the child, but the
 *    test tone of `--audio-prova` opens an `audio_cod` in the SERVER (`webtransport.c`).
 *    ⇒ `main.c` calls this function for itself **and** passes the option to the
 *    children: if it called only one, the tone bench and the real-session bench
 *    would measure two different products.
 */
void audio_silenzio_taci(bool si);
bool audio_silenzio_acceso(void);

/* How many blocks the cure has silenced.  ⛔ It is kept apart from `audio_cod_conti()`:
 *    that one already has a caller and its signature is not this module's. */
uint64_t audio_cod_taciuti(const audio_cod *c);
