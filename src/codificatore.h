/*
 * codificatore.h — from the captured frame to the bytes a browser decodes.
 *
 * ---------------------------------------------------------------------------
 * ⛔ WHAT IT IS, AND WHAT IT IS NOT
 *
 * It is the third link of phase 2 (`FASI.md` §02-primo-fotogramma): it takes
 * the pixels that capture delivers and produces **a stream that F2.4 puts on
 * the wire and F2.5 gives to `VideoDecoder`**.
 *
 * ⛔ **In software until 13 Aug 2026, and the line below read:**
 *    *«In software, on purpose.  Acceleration is phase 8, and putting it
 *    earlier would mean not knowing which of the two pieces is wrong.»*
 *
 * ⭐⭐ **ACCELERATION WAS BROUGHT FORWARD INTO PHASE 3, by the user's
 *      decision**, and the reason is measured at both ends:
 *
 *      the cost   `[M]` 13 Aug 2026, 1920×1080 at 10 bits, 120 frames,
 *                 all at 20 Mbit/s and with the output frames COUNTED:
 *                 `hevc_vaapi` **3.16-3.24 ms** against tens of milliseconds
 *                 for the software fallback on the real scene: the software
 *                 encoder is the big piece of the encoding stretch.
 *      the target ⛔ and **it is not AV1**: `av1_vaapi` **appears** in
 *                 ffmpeg's list and on use exits **218** — *«No usable encoding
 *                 profile found»*, 3 runs out of 3.  `vainfo` gives AV1 as
 *                 decode-only on both nodes.  ⇒ **staying on AV1 means staying
 *                 in software forever** on this machine.
 *
 * ⇒ From here: **HEVC in hardware is there and AV1 is not**, and it is the exact
 *   reverse of the table of `DECISIONI.md` §1.13 below — which spoke of the
 *   CLIENT, not of the server.  The two do not contradict each other and must
 *   be read together.
 *
 * ⛔ **What was NOT brought forward**: **zero copy** (the frame going from
 *    capture to the GPU without passing through system memory) stays in
 *    phase 8.  Here the pixels are converted in software and UPLOADED to the
 *    GPU, and the cost of the upload is measured separately — see
 *    `us_caricamento` in `CodificatoreFotogramma`.
 *
 * ⭐⭐ **PHASE 18 (30 Sep 2026, `DECISIONI.md` §10.25): the card NO LONGER goes
 *      through libavcodec.**  `h264_vaapi` and `hevc_vaapi` remain the NAMES of
 *      the card route, but underneath there is `src/vadiretta.c` — libva used
 *      directly, with the stream headers written by REMOTIX
 *      (`src/scrittore_bit.c`).  The stream is of the same kind as before:
 *      `[M]` on zero copy old and new give the same bytes and the same
 *      PSNR (`fasi/18-senza-ffmpeg.md` §4).  The «from memory» route
 *      converts on the CPU with `src/colori709.c` (BT.709 limited, as
 *      yesterday) and uploads the NV12/P010 planes: no libswscale, and ⛔ no
 *      VPP from memory, which measured worse.  No line of the product goes
 *      through ffmpeg any more.  ⛔ PHASE 19 (1 Oct 2026, `DECISIONI.md`
 *      §10.27): the SOFTWARE fallback (`src/ripiego.c`: OpenH264, SVT-AV1) has
 *      left — *«no cpu without a card»*, the user's words.  Without a capable
 *      card the server declares it at startup and offers no codec.
 *
 * ⛔ **And this file is NOT v1's `codificatore.c` brought back.**  That one is
 *    an H.264/AVC420 encoder for RDP: 889 lines, **77** name H.264/AVC,
 *    **47** name RDP/FreeRDP, and *HEVC*, *265*, *10 bit* appear **zero**
 *    times (`[M]`, `fasi/rapporti/F2-3-codifica.md` §4.1).  Of that file
 *    **the shape** survives — the component asked for by name, the ban on
 *    silent fallback, the timing account, the ban on `GLOBAL_HEADER` — and
 *    almost no line.  It is decision **D5** of `FASI.md` §02-primo-fotogramma.
 *
 * ---------------------------------------------------------------------------
 * ⛔⭐ THERE ARE TWO CODECS, AND THERE ARE TWO BY THE USER'S DECISION
 *
 * `DECISIONI.md` §1.13, 12 Aug 2026, taken in front of the measurement:
 *
 *     | `[M]` F2.5     | Chrome, GPU | Chrome, no GPU    | Firefox |
 *     |----------------|-------------|-------------------|---------|
 *     | **HEVC Main10**| 8 cells / 8 | ⛔ zero            | ⛔ zero  |
 *     | **AV1 8 and 10**| 8 / 8      | ⭐ 8 / 8           | ⭐ 8 / 8 |
 *
 * ⇒ HEVC **does not reach the pixel on Firefox**, and on Chrome exists **only
 *   via VA-API** (with `prefer-software` Chrome says `Unsupported`).  AV1 paints
 *   in all four boxes **even in software**.
 *
 * ⛔ Hence: **no requirement is declared** *«Chrome with VA-API needed»*.  The
 *    codec **is negotiated** (`RCP.md` §4.3, capability `video.codec`) and **the
 *    fallback is declared** (`CODER.md` §4.2).  The order of preference stays
 *    **`hevc,av1`**: HEVC is still first, because it is the one the phone
 *    decodes in hardware.
 *
 * ⛔ The number that ends up in the frame header (`RCP.md` §6.2, field
 *    `codec`) is **1 = HEVC, 2 = AV1**, and it is exactly the value of
 *    `CodecVideo` below: an enumeration that does not match the protocol
 *    forces a conversion table, and a conversion table is a place to go
 *    wrong silently.
 *
 * ---------------------------------------------------------------------------
 * ⛔ THE SHAPE OF THE BYTES, WHICH IS A DECISION AND NOT A DETAIL
 *
 * Decision **D1** (`FASI.md` §02-primo-fotogramma, four reasons read in
 * `F2-3-codifica.md` §3.2): **pure Annex-B, and NO `description`**.
 *
 *     [00 00 00 01] VPS (32)
 *     [00 00 00 01] SPS (33)      ← profile 2 = Main10, bit_depth = 10
 *     [00 00 00 01] PPS (34)
 *     [00 00 01]    PREFIX_SEI (39)
 *     [00 00 01]    IDR_N_LP (20) ← the first frame is ALWAYS a keyframe
 *
 * ⛔ In practice, and in this file: **`AV_CODEC_FLAG_GLOBAL_HEADER` is never
 *    turned on** — and we do not trust ourselves not to have turned it on:
 *    `codificatore_nuovo()` **checks** that it is off after opening, and
 *    `codificatore_comprimi()` checks **on the bytes** that the parameter sets
 *    are in front of every keyframe.  It is the same ban v1 had already paid
 *    for (`fondamenta/remotix-c/src/codificatore.c:268-272`, *«on RDP the
 *    sequence parameters must travel IN the stream, in front of the IDR»*):
 *    there the reason was RDP, here it is `VideoDecoder`, and the **symptom is
 *    identical** — black screen with the frames arriving.
 *
 * ⚠ For **AV1** the question does not arise: there is no `hvcC`, and the OBU
 *   temporal units are sent as they are (`DECISIONI.md` §1.13: *«no
 *   description: one seam less»*).  What is checked is the analogue:
 *   the **sequence header OBU** in front of every keyframe.
 *
 * ---------------------------------------------------------------------------
 * ⚠ AND THE THING TO SAY BEFORE ALL THE REST: EIGHT BITS, NOT TEN
 *
 * `[M]` 12 Aug 2026, F2.2: **Mutter delivers only BGRx/BGRA**, that is **8 bits
 * per channel** (255/256/255 distinct levels, multiples of 4 at 0.259/0.259/0.249
 * — eight real bits, all eight).
 *
 * ⇒ ⛔ **Main10 from this route is eight bits PROMOTED to ten**, and the stream's
 *   label keeps saying «10 bit» along the whole chain — which is exactly the
 *   fault **F2.3-A** that the bench reproduces.  `SPECIFICHE.md` §3.1 puts
 *   10 bits in the **desired**, and from this source it **cannot be reached**.
 *
 * ⛔ Hence `confessione.promozione_8_a_10`: the promotion **is declared**, and
 *    ends up in the log at the first encode.  `DECISIONI.md` §2.7 line 2 —
 *    *«a silent fallback remains forbidden even when the fault is not
 *    ours»*.  An encoder that kept quiet would produce two measurements under
 *    the same label, which is form **E2** of `REVIEWER.md` §2.
 *
 * ---------------------------------------------------------------------------
 * ⛔ E2 — THE COMPONENT THAT DECIDES BY ITSELF: ASK FOR IT BY NAME, AND VERIFY
 *
 * `CODER.md` §3.9.  And the line v1 had written after paying for it
 * (`fondamenta/remotix-c/src/codificatore.c:550-566`):
 *
 *     ⛔ *«ASKED FOR BY NAME, NO FALLBACK.  Whoever names an encoder is
 *        measuring: falling back on another would give two different
 *        measurements with the same label, which is worse than not measuring.»*
 *
 * Here the rule counts **twice**, because the ways of disobeying measured on
 * 12 Aug 2026 are two and neither of them shouts:
 *
 *   ⛔ `-c:v hevc` instead of `libx265` lets libavcodec choose, and it has
 *      five HEVC encoders loaded — and four are in hardware, that is
 *      phase 8 sneaking into phase 2;
 *   ⛔ `[M]` **libsvtav1 ignores an option it does not know and carries on**:
 *      `-svtav1-params pippo=1` prints *«Error parsing option»* and **exits 0**.
 *      An option asked for and not applied looks the same as an option
 *      applied.
 *
 * ⇒ Hence the **two witnesses** of `codificatore_confessione()`, and the second
 *   does not depend on the first:
 *
 *     the context  what the encoder says it opened (component name, pixel
 *                  format, profile, B frames)
 *     ⭐ THE BYTES  what is written **in the stream**: the HEVC SPS and the
 *                  AV1 sequence header OBU are read and compared with what
 *                  was asked for.  It is not a deduction: it is the product
 *                  reading itself back.
 *
 * ⭐ And from the bytes also comes **the level**, which is needed and is not
 *    guessed: `RCP.md` §4.3 says the server **MUST** emit a stream of a level
 *    no higher than the one declared by the client, and ⛔ `[M]` F2.5 measured
 *    that **the browser does not check it** (Chrome accepts `L30` on a level
 *    3.0 stream and paints anyway) ⇒ decision **D4**: *the level check
 *    belongs on the server side*.  Here.
 *
 * ---------------------------------------------------------------------------
 * ⛔ LATENCY, AND THE TWO DEFAULTS NOBODY HAD ASKED FOR
 *
 * `SPECIFICHE.md` §3.2: **50 ms ceiling**, and `CODER.md` §1-bis — *«latency
 * weighs more than frames»*.  `[M]` 12 Aug 2026, read in the confession of the
 * two encoders:
 *
 *     x265        `bframes=4` and `open-gop`   — nobody had asked for them
 *     SVT-AV1     `pred struct: random access` — likewise
 *
 * Both buy compression **by selling responsiveness**: a frame that waits for
 * the next one is one more frame of latency.  ⛔ They must be **decided, not
 * inherited** — and here `bframes=0`, `open-gop=0`, `pred-struct=1` are
 * decided, with the reason next to each in `codificatore.c`.
 *
 * ⭐ And the check is not the option: it is **`dts == pts` on every packet**.
 *    An encoder that reorders declares it there, whatever it did with the
 *    options we passed it — and it is a witness that holds identically for
 *    both codecs.
 */
#ifndef REMOTIX_CODIFICATORE_H
#define REMOTIX_CODIFICATORE_H

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* ⛔ The values are those of `RCP.md` §6.2, field `codec`: they are not converted. */
typedef enum {
	CODIFICATORE_HEVC = 1,
	CODIFICATORE_AV1 = 2,
	/* ⭐⭐ H.264 — came in on 20 Aug 2026, `DECISIONI.md` §1.13-ter.
	 *
	 * ⛔ And the number 3 IS ADDED, not reused: 2 stays AV1 forever,
	 *    because an old client that said «2» and received H.264 would not
	 *    notice — it would paint garbage without an error.
	 *
	 * The reason, and it is the user's: **Firefox for Android has neither HEVC
	 * nor AV1**, so for that browser the product did not exist.  And the
	 * measurement says the rest: H.264 is the only codec in HARDWARE at both
	 * ends — 3.11 ms on the server (the fastest of the four) and in hardware
	 * on the tablet. */
	CODIFICATORE_H264 = 3,
} CodecVideo;

/*
 * The input pixel format.
 *
 * ⚠ There are two because the project's REAL inputs are two, and not for
 *   generality: `BGRX` is what GNOME's capture delivers (F2.2, `[M]`
 *   8-bit BGRx, stride 7680 read from the manifest), `YUV420P10LE` is what
 *   the bench delivers — a known image already in YCbCr, which allows
 *   measuring the encoder **without** measuring the colour conversion too.
 */
typedef enum {
	CODIFICATORE_PIXEL_BGRX,        /* 4 bytes per pixel, B G R x */
	CODIFICATORE_PIXEL_YUV420P10LE, /* three planes, 2 bytes per sample */
	/*
	 * ⭐ PHASE 13 — the third real input: **R G B x**, what labwc delivers
	 *    (`[M]` 21 Sep 2026: `XBGR8888`, the only format offered).
	 *
	 * ⛔⛔ AND IT IS AT THE END ON PURPOSE, and it is not generality: it is the
	 *     cure for a defect found by the adversarial reviewer.  The first draft
	 *     believed it could CHOOSE among the offered formats; but screencopy's
	 *     `buffer` event arrives **only once** per frame, and labwc offers only
	 *     `R G B x`.  ⇒ Without this value the encoder read those bytes as
	 *     `B G R x` and the user saw **red and blue swapped**, without an
	 *     error anywhere.
	 * ⭐ And it costs nothing: the conversion to the encoder's format is
	 *   there anyway, and only how the source is read changes.
	 */
	CODIFICATORE_PIXEL_RGBX         /* 4 bytes per pixel, R G B x */
} FormatoPixel;

/* A single-plane input, four bytes per pixel, in FULL range: it is the
 * question the encoder used to ask with `== BGRX`, and which since RGBX exists
 * has TWO true answers.  ⛔ Asking it with `== BGRX` in even one place
 * would mean treating RGBX as if it were YUV — that is, a broken image. */
#define FORMATO_PIXEL_IMPACCHETTATO(f) \
	((f) == CODIFICATORE_PIXEL_BGRX || (f) == CODIFICATORE_PIXEL_RGBX)

/*
 * How quality is asked for.
 *
 * ⛔ `LOSSLESS` is not a whim: it is the only regime in which **real 10 bits**
 *    can be told apart from declared 10 bits.  At a realistic bitrate HEVC
 *    destroys a 1 LSB ramp **by construction**, and a low count would not
 *    distinguish *«the chain is 8-bit»* from *«the bitrate was low»*: two
 *    opposite diagnoses under the same label (`F2-3-codifica.md` §2.4).
 */
typedef enum {
	CODIFICATORE_QUALITA_LOSSLESS, /* ⚠ HEVC yes; AV1 see the note in .c */
	CODIFICATORE_QUALITA_CRF,      /* constant quality, `valore` = CRF */
	/*
	 * ⛔⭐ CONSTANT QP — and it is a SEPARATE mode, not «CRF on hardware».
	 *
	 * `[M]` 13 Aug 2026: `hevc_vaapi` **has no** `crf` option; it has `qp`
	 * (`rc_mode=CQP`).  CRF and QP are not the same quantity — CRF is a
	 * constant *perceived* quality, with the quantiser moving; QP is the
	 * quantiser, fixed.  ⛔ Translating «CRF 20» into «QP 20» and still
	 * calling it CRF would be two measurements under the same label, that is
	 * form E2 (`CODER.md` §3.9): QP is asked for, and QP is written.
	 */
	CODIFICATORE_QUALITA_QP,
} ModoQualita;

/*
 * ⛔⭐ THE ENTRYPOINT POWER — THREE OUTCOMES, NOT TWO.
 *
 * `EncSliceLP` is «low power» encoding: fast, but with its own limits on
 * quality and features, and it **is not equivalent** to full power.  ⛔ Hence:
 * `libavcodec`'s default (`low_power=false`) is not inherited and not guessed.
 * Whoever opens a hardware encoder **declares which of the two it wants**, and
 * `NON_DICHIARATA` — which is zero, that is what you get without writing it —
 * **fails saying so**.
 *
 * ⚠ And the reason the three outcomes are needed is measured: on the test
 *   machine the two render nodes do NOT have the same entrypoint (`[M]`
 *   13 Aug 2026 — see `nodo_rendering` below), so «low power» and «full» are
 *   not a preference: they are two different machines.
 */
/*
 * ⭐ `LA_DICHIARATA` (phase 16, Radeon campaign) is the third question, and it
 *    is not «you decide»: it is **a written rule** — *`EncSliceLP` if the
 *    driver DECLARES it for that profile, otherwise full `EncSlice` if the
 *    driver declares that, otherwise fail* (and the caller drops to the
 *    software fallback, saying so).  ⛔ The choice is made on the CAPABILITY
 *    read with `vaQueryConfigEntrypoints`, not on the card's name nor on an
 *    environment variable (`no exceptions per card`): on Intel iHD there is
 *    `EncSliceLP` and the result is identical to `BASSA`; on the RX 6800
 *    (radeonsi) `[M]` 13 Aug 2026 there is only `EncSlice`, and without this
 *    rule the session encoded in SOFTWARE.
 * ⚠ And the fallback to the other entrypoint here is NOT silent: which of the
 *   two was taken, and why, is written by `codificatore.c` to the log, and
 *   `codificatore_nome()` carries the ACTUAL entrypoint inside the name.
 *   `BASSA` and `PIENA` stay rigid, for the benches that compare the two.
 */
typedef enum {
	CODIFICATORE_POTENZA_NON_DICHIARATA = 0,
	CODIFICATORE_POTENZA_PIENA,  /* VAEntrypointEncSlice   */
	CODIFICATORE_POTENZA_BASSA,  /* VAEntrypointEncSliceLP */
	CODIFICATORE_POTENZA_LA_DICHIARATA, /* LP if the driver declares it, otherwise full */
} PotenzaEntrypoint;

typedef struct {
	CodecVideo codec;
	/*
	 * ⛔ The component is asked for BY NAME and there is no fallback.
	 * ⛔ Phase 19: only the card names; NULL or another name and
	 *    `codificatore_nuovo()` refuses saying so — the software fallback
	 *    (OpenH264, SVT-AV1) has left.  ⭐ And the names are SIX, two per route
	 *    plus two «by capability» (1 Oct 2026, `DECISIONI.md` §10.27):
	 *
	 *      `h264_scheda`  `hevc_scheda`   THE ROUTE IS CHOSEN BY CAPABILITY:
	 *                                     Vulkan Video if the card offers it
	 *                                     for that codec (`vulkanvideo_capacita`),
	 *                                     otherwise VA-API — it is what the
	 *                                     product asks for;
	 *      `h264_vulkan`  `hevc_vulkan`   Vulkan Video, and nothing else: if it
	 *                                     is not there, fail saying so (benches,
	 *                                     diagnosis, `--codifica vulkan`);
	 *      `h264_vaapi`   `hevc_vaapi`    VA-API (`vadiretta.c`), and nothing else
	 *                                     (`--codifica vaapi`, and benches 18/19
	 *                                     that measure THAT route).
	 *
	 *    ⛔ The chosen route ends up in the confession (`strada`) and in the name
	 *       of the opened component (`componente`), not in the requested name:
	 *       whoever asks for `h264_scheda` reads back `h264_vulkan` or `h264_vaapi`.
	 */
	const char *componente;
	/*
	 * ⛔⭐ THE RENDER NODE — it is established and DECLARED, not guessed.
	 *
	 * Needed only when `componente` is a hardware encoder
	 * (`h264_vaapi` / `hevc_vaapi`).  ⛔ `NULL` does not mean «the good one»:
	 * it means **fail saying so**.
	 *
	 * ⚠ And the reason it cannot be guessed is `[M]` 13 Aug 2026 on the test
	 *   machine, and it is bigger than «two equal nodes»:
	 *
	 *     /dev/dri/renderD128   0000:00:02.0  i915   Intel (8086:4680)
	 *                           VA driver: Intel iHD 25.2.3
	 *                           VAProfileHEVCMain10 : VAEntrypointEncSliceLP
	 *     /dev/dri/renderD129   0000:03:00.0  amdgpu AMD Radeon RX 6800 (navi21)
	 *                           VA driver: Mesa Gallium 25.0.7 (radeonsi)
	 *                           VAProfileHEVCMain10 : VAEntrypointEncSlice
	 *
	 *   ⇒ They are **two different vendors** and **two different entrypoints**.
	 *     A number taken on one does not hold for the other, and code that
	 *     opened «the first one around» would measure a random machine.
	 */
	const char *nodo_rendering;
	/* ⛔ See `PotenzaEntrypoint`: zero fails, and it does so on purpose. */
	PotenzaEntrypoint potenza;
	uint32_t larghezza, altezza;
	uint32_t fotogrammi_al_secondo;
	ModoQualita modo;
	int qualita;                 /* CRF (software) or QP (hardware) */
	int profondita;              /* 8 or 10 — what is ASKED of the encoder */
	/*
	 * ⛔⭐⭐ THE LEVEL CEILING OF `RCP.md` §4.3 (line 701), IN TENTHS:
	 *      `5.1` ⇒ **51**.  `0` = no ceiling, the component chooses.
	 *
	 * ⛔ And it is ASKED FOR instead of discovered afterwards: `[M]` 23 Aug 2026,
	 *    canvas 3840x2160, H.264 — the client declared `video.livello=5.1` and
	 *    this module produced a level **5.2** stream, because nobody had ever
	 *    told it what the ceiling was.  §4.3 is a MUST, and the symptom of an
	 *    exceeded level is not an error: it is the browser's decoder refusing
	 *    the configuration.
	 *
	 * ⚠ The translation into each codec's alphabet lives in `livello_imposto()`
	 *   and nowhere else: H.264 uses the tenths as they are (`level_idc`),
	 *   HEVC triples them (`general_level_idc`).  ⛔ And obedience is NOT
	 *   presumed: it is read back in `livello_flusso` from the SPS bytes.
	 */
	int livello_x10;
	FormatoPixel formato;
	/*
	 * Periodic keyframes every N frames; **0 = on request only**.
	 * ⚠ Zero is the choice of phase 2 and the reason is in `RCP.md` §5.2:
	 *   keyframes are requested (`RICHIEDI_CHIAVE`), and sending them by the
	 *   clock on a bad line is *«the spiral»* that paragraph forbids.  The
	 *   operating point belongs to phase 9.
	 */
	uint32_t chiavi_ogni;
} CodificatoreRichiesta;

/*
 * ⭐ THE CONFESSION — what the encoder REALLY did.
 *
 * ⛔ The `*_flusso` fields are read **from the bytes produced**, not from the
 *    arguments we passed it: they are the second witness of E2, and the only
 *    one that survives a component that ignores an option without saying so.
 */
typedef struct {
	CodecVideo codec;
	const char *componente;       /* the name of the component really opened */
	bool ha_obbedito;             /* ⛔ false ⇒ nothing is sent */
	char perche_no[256];          /* the reason, when it did not obey */

	/* from the context */
	int profondita_chiesta;
	int fotogrammi_b;
	bool global_header;           /* ⛔ must be false, always */

	/* ⭐ from the stream's BYTES */
	bool letto_dal_flusso;
	int profondita_flusso;        /* bits per sample, from the SPS / seq header */
	int profilo_flusso;           /* HEVC: profile_idc · AV1: seq_profile */
	int livello_flusso;           /* HEVC: general_level_idc · AV1: seq_level_idx */
	bool tier_alto;               /* HEVC: general_tier_flag · AV1: seq_tier */
	uint32_t larghezza_flusso, altezza_flusso;
	/*
	 * ⭐ What the stream ENCODES, which is not always what it SHOWS.
	 * ⛔ `[M]` 13 Aug 2026: `hevc_vaapi` on AMD (radeonsi, navi21) encodes
	 *    1920×**1088** and crops to 1080 with the conformance window; on Intel
	 *    (iHD) it encodes a round 1080.  The two sizes are kept separate because
	 *    the second is the one the decoder shows and the first is the one that
	 *    costs bandwidth — and for a whole day the SPS reader confused one with
	 *    the other and refused EVERY frame from that card.
	 */
	uint32_t larghezza_codificata, altezza_codificata;
	int croma_flusso;             /* 1 = 4:2:0 */
	/*
	 * The string the browser passes to the decoder: `hev1.2.4.L93.B0` /
	 * `avc1.640033` / `av01.0.04M.10`.
	 *
	 * ⛔⭐ AND UNDER H.264 THIS FIELD STAYED EMPTY until 23 Aug 2026:
	 *     `leggi_sps_hevc()` and `leggi_sps_av1()` composed it, `leggi_sps_
	 *     h264()` did not — it read profile and level and never wrote them together.
	 *     ⚠ The log said *«string for the decoder «»»* and nobody
	 *     read a defect in it, because an empty string looks like a field that
	 *     is not needed.  ⛔ It is needed: it is the only place where the SERVER
	 *     declares what the client should pass to `configure()`, and it is
	 *     the witness that says whether the page and the stream agree.
	 */
	char stringa_codec[64];       /* `hev1.2.4.L93.B0` / `avc1.640033` */

	/* ⚠ the promotion, declared instead of suffered */
	bool promozione_8_a_10;

	/* ───────────────────────────────────────────────────────────────────────
	 * ⭐ THE HARDWARE, AND IT IS DECLARED NEXT TO THE NUMBER — not «at the end
	 *    of the report».  A 3 ms rate without these five lines next to it is a
	 *    number that holds for a machine nobody knows.
	 */
	bool in_hardware;             /* the card (vadiretta or vulkanvideo), not the fallback */
	char nodo[64];                /* the REQUESTED node, e.g. /dev/dri/renderD128 */
	/*
	 * ⭐ PHASE 19 — THE ROUTE that answered: `vaapi` (`vadiretta.c`) or
	 *    `vulkan` (`vulkanvideo.c`).  It is chosen by CAPABILITY at opening
	 *    (`h264_scheda`/`hevc_scheda`) or by name, and here one reads which of
	 *    the two really opened.  ⚠ `modi_bitrate` below is in the route's
	 *    alphabet: `VA_RC_*` for vaapi, `VULKANVIDEO_RC_*` for vulkan.
	 */
	char strada[16];
	/*
	 * ⭐ The vendor that ANSWERED, asked of `vaQueryVendorString()` on the
	 *    opened display — not deduced from the node name.  It is the witness
	 *    that says whether «renderD128» is the Intel one believed or another
	 *    card: on the test machine the two nodes are from two different vendors `[M]`.
	 *    ⭐ On the Vulkan route it is `deviceName` + `driverName`/`driverInfo`
	 *    of the card chosen BY THE NODE (`VK_EXT_physical_device_drm`).
	 */
	char fornitore_va[256];
	/*
	 * ⛔ The entrypoint: `false` = full (`VAEntrypointEncSlice`), `true` = low
	 *    power (`VAEntrypointEncSliceLP`).  ⚠ `bassa_potenza_verificata` says
	 *    that the (profile, entrypoint) pair was **read from the driver** with
	 *    `vaQueryConfigEntrypoints`, not just asked of libavcodec: without that
	 *    check «I asked for it» and «it did it» look the same.
	 *    ⚠ On the Vulkan route the entrypoint DOES NOT EXIST: both stay
	 *    `false`, and a false `bassa_potenza_verificata` there means «the
	 *    question does not exist», not «I did not look».
	 */
	bool bassa_potenza;
	bool bassa_potenza_verificata;
	/*
	 * ⭐ The maximum size the DRIVER declares for (profile, entrypoint),
	 *    read with `vaGetConfigAttributes` before opening.
	 *
	 * ⛔ It is needed because the limit is NOT the same across codecs: `[M]` 22 Aug
	 *    2026 `h264_vaapi` on `EncSliceLP` accepts **32-4096 px per side**
	 *    (4096x2160 yes, 4112x2160 no), while `hevc_vaapi` handles 16384x4320 —
	 *    and the legal canvas of `RCP.md` §4.5 went up to **7680x4320**.  ⇒ Beyond
	 *    4096 px H.264 on that card was not there.  ⭐ Since 1 Oct 2026 the canvas
	 *    stops at **4096x2304** (the user's decision) and the case no longer
	 *    arises from the protocol; the check stays, because the ceiling is the
	 *    DRIVER's and another card may declare a lower one.
	 *
	 * ⚠ `misura_massima_letta == false` means **«I could not ask for it»**,
	 *   which is NOT «there is no limit»: the two values then mean nothing and
	 *   are not read (`LEZIONI.md` §1.9).
	 */
	uint32_t misura_massima_l, misura_massima_a;
	bool misura_massima_letta;
	/*
	 * ⛔ How many frames the hardware encoder is ALLOWED to hold in the
	 *    pipeline: `async_depth`.  ⚠ `[M]` 13 Aug 2026 the default of
	 *    `hevc_vaapi` is **2**, and nobody had asked for it — it is the same
	 *    unrequested default as `bframes=4` on x265, in another guise.  It is
	 *    read by READING BACK the option after opening.
	 */
	int profondita_asincrona;

	/*
	 * ⭐⭐ BITRATE CONTROL — and these are TWO witnesses out of three, because
	 *     the third is not a field: it is the bytes that come out (the
	 *     «video bandwidth» line in the log, every 10 s).
	 *
	 * ⛔ Why three are needed is told by **R31**, the project's most expensive
	 *    lesson: in v1 the first two would have been **both green** —
	 *    `bit_rate` and `rc_max_rate` were exactly the numbers asked for, and
	 *    nobody had asked for CBR.  CBR was **the name the driver gave that
	 *    pair of numbers**, and only the bill said so.
	 *
	 * `modi_bitrate` is the `VA_RC_*` mask **declared by the driver** for the
	 * (profile, entrypoint) pair, read with `vaGetConfigAttributes` **before**
	 * opening.  ⚠ `modi_bitrate_letti == false` means **«I could not ask for
	 * it»** or **«the driver does not declare it»**, which is NOT «there is
	 * only CQP»: it is exactly the deduction libavcodec makes silently
	 * (*«assuming CQP only»*) and that is not copied (`LEZIONI.md` §1.9).
	 *
	 * ⚠ `banda_*` hold only with the ceiling on; with the ceiling off they are
	 *   zeros, and zero there means **«not asked for»**, not «no limit».
	 */
	uint32_t modi_bitrate;
	bool modi_bitrate_letti;
	int modo_bitrate;             /* `rc_mode` READ BACK: 1 = CQP · 5 = QVBR · 3 = VBR (Vulkan) */
	int64_t banda_punto;          /* `bit_rate`, bit/s — the operating point */
	int64_t banda_filo;           /* `rc_max_rate`, bit/s — ⛔ NEVER equal to the point */
	int banda_serbatoio;          /* `rc_buffer_size`, in **bits** */
	/*
	 * ⛔ The same buffer in MILLISECONDS, and this is the number that
	 *    `CODER.md` §1-bis judges: in bits one does not see that v1 had
	 *    **five hundred** (`rc_buffer_size = bit_rate/2` is not «half», it is
	 *    half a second) against a ceiling of **50** for the whole of our piece.
	 */
	uint32_t banda_serbatoio_ms;

	/* ⚠ latency, measured instead of deduced */
	bool riordina;                /* a packet with dts != pts */
	uint32_t fotogrammi_in_volo;  /* how many it held back before the first */
} CodificatoreConfessione;

/* A frame ready to send.  The bytes belong to the encoder until
 * `codificatore_rilascia()`. */
typedef struct {
	const uint8_t *dati;
	size_t byte;
	bool chiave;                  /* `RCP.md` §6.2: 0x0301 keyframe, 0x0302 delta */
	uint64_t us_conversione;      /* ⭐ the three times kept apart: without them, */
	uint64_t us_codifica;         /*    «the rate dropped» cannot be pinned on anything */
	/*
	 * ⭐ THE FOURTH TIME, and it is born with the hardware: how much it costs to
	 *    BRING the frame from system memory to the GPU (`vadiretta_carica_*`).
	 *    ⛔ It is kept separate on purpose: it is exactly the stretch that
	 *    phase 8's **zero copy** exists to remove, and adding it to the
	 *    encoding would make invisible how much that work is worth.  ⚠ In
	 *    software it is always 0, and zero there means «this stretch is not
	 *    there», not «it is free».
	 */
	uint64_t us_caricamento;
	uint32_t ricodifiche;         /* ⛔ >0 ⇒ the 16 MiB ceiling has bitten */
	bool trattenuto;              /* ⚠ the encoder did not deliver it at once */
} CodificatoreFotogramma;

typedef struct Codificatore Codificatore;

/*
 * Opens the encoder, or **fails saying why**.
 *
 * ⛔ It never falls back: not to another component, not to another profile,
 *    not to 8 bits.  A silent fallback would give two measurements under the
 *    same label (`CODER.md` §3.9, §4.2 second half).
 */
Codificatore *codificatore_nuovo(const CodificatoreRichiesta *richiesta,
                                 char *errore, size_t errore_byte);
void codificatore_libera(Codificatore *cod);

/* For the log: «HEVC 10 bit via hevc_vaapi (in HARDWARE, /dev/dri/renderD128, low
 * power)».  ⛔ The node and the power are INSIDE the name, not beside it: it
 * is the line that ends up in the log next to every number. */
const char *codificatore_nome(const Codificatore *cod);

/* ⭐ PHASE 19: the route really opened — "vaapi" or "vulkan" (see
 *    `CodificatoreConfessione.strada`); "" on NULL. */
const char *codificatore_strada(const Codificatore *cod);

/* ⭐ PHASE 19: will the «card» route on this node be Vulkan?  True if Vulkan
 *    Video encodes H.264 or HEVC on the node (`vulkanvideo_capacita`), that is
 *    if `h264_scheda`/`hevc_scheda` would open Vulkan there.  ⚠ It is the answer
 *    from BEFORE opening: a request Vulkan cannot serve (size, bitrate) falls
 *    back to VA-API anyway.  It serves whoever must get ready before the
 *    encoder (the slabs of `wlroots.c`). */
bool codificatore_vulkan_sul_nodo(const char *nodo);

/* ⛔ PHASE 19 (1 Oct 2026, `DECISIONI.md` §10.27): here there were
 *    `codificatore_ripiego_software()`, `codificatore_software_pronto()` and
 *    `codificatore_software_rimedio()` — the software fallback (OpenH264,
 *    SVT-AV1) and the line with the package to install.  They left with it:
 *    without a capable card REMOTIX does not encode, and declares it. */

/* ⭐ Valid after the first `codificatore_comprimi()` for the fields read from the bytes. */
const CodificatoreConfessione *codificatore_confessione(const Codificatore *cod);

/*
 * Compresses a frame.
 *
 * `pixel` and `passo` are what capture delivers: ⛔ the stride is passed, not
 * computed as `larghezza × 4` — F2.2 reads it from the PipeWire manifest and
 * says to do the same even when today it coincides.
 *
 * Returns `false` and delivers nothing if the encoder did not obey, if the
 * frame exceeds 16 MiB even after the re-encodes (`RCP.md` §6.2), or if the
 * shape of the bytes is not the one promised to F2.5.
 */
bool codificatore_comprimi(Codificatore *cod, const uint8_t *pixel, uint32_t passo,
                           CodificatoreFotogramma *fuori);

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐⭐ ZERO COPY — the frame that was ALREADY on the GPU
 * ═══════════════════════════════════════════════════════════════════════════
 *
 * ⛔ THE FACT THAT GAVE BIRTH TO IT, `[M]` 22 Aug 2026 (agent C), inside the
 *    product, ten items in a row, remainder 0.02 ms over 2 450 frames:
 *
 *      the copy (`memcpy` into the slot)    1.65 ms
 *      the conversion (`sws_scale`)         8.15 ms
 *      the upload (memory → GPU)            1.16 ms
 *      ────────────────────────────────────────────
 *                                          10.96 ms of 18.86 — 58 % of the stretch
 *
 *    ⇒ The frame **left the GPU, was converted on the CPU and went back up to
 *      the GPU**.  On this route it never leaves.
 *
 * ⛔⛔ AND THAT 10.96 IS A BUDGET, NOT A PROMISE — C paid for the lesson
 *      the same day: removed 7.28 ms and gained 2.33, because `sws_scale`
 *      took back 3.84 ms that the pixel scan used to **warm up in cache**
 *      for it.  ⇒ In this stretch **the items are not independent**, and the
 *      removed stretches do not add up.  Whoever reads this header must not
 *      subtract: measure.
 *
 * ⚠ AND IT IS NOT «zero work»: it is **zero copies in system memory**.  The
 *   conversion from RGB to NV12 is done by the GPU (VA-API VPP), and its cost
 *   ends up in `us_conversione` as before — who does it changes, not the fact
 *   that it must be done.  ⛔ `us_caricamento` instead stays **0**, and there
 *   zero means «this stretch IS NO LONGER THERE», not «it is free».
 */
typedef struct {
	/* ⛔ The descriptor is not ours and is not closed: the producer owns it,
	 *    and whoever closed it would take the image away from itself. */
	int fd;
	uint32_t offset;
	uint32_t stride;              /* ⛔ READ from the chunk, never `larghezza × 4` */
	uint32_t larghezza, altezza;
	uint32_t formato_drm;         /* `DRM_FORMAT_XRGB8888` … */
	uint64_t modificatore;
	/*
	 * ⛔ The GENERATION of the producer's buffers.  ⚠ It is needed **here** and
	 *    not elsewhere: importing an `fd` into VA-API costs, so it is cached —
	 *    and a cache on descriptor numbers alone would give a stale image
	 *    after every renegotiation, because descriptor numbers are recycled.
	 *    When this changes, the cache is thrown away.
	 */
	uint64_t generazione;
} CodificatoreSuperficie;

/*
 * Compresses a frame that is ALREADY on the card.
 *
 * ⛔ It holds **only** in hardware: in software there are no pixels to read,
 *    and this call fails saying so instead of producing an empty image.
 *    The caller checks `codificatore_in_hardware()` **before** asking the
 *    producer for the card route.
 *
 * ⛔⛔ AND THE DESCRIPTOR MUST STAY VALID FOR THE WHOLE CALL, not a
 *      microsecond less: when this function returns, the GPU has **finished**
 *      reading (there is an explicit synchronisation inside), and only then
 *      can whoever captured return the buffer to the producer.  ⚠ Releasing
 *      it earlier is precisely the defect of `LEZIONI.md` §8: two screens
 *      alternating, and no error.
 */
bool codificatore_comprimi_scheda(Codificatore *cod, const CodificatoreSuperficie *superficie,
                                  CodificatoreFotogramma *fuori);

/* ⛔ «Is it in hardware?» — the answer comes from `componente_e_hardware()`,
 *    that is from what the COMPONENT declares it accepts (a surface, not
 *    pixels).  ⚠ Not from the name, and not from «it opened a render node»
 *    (`LEZIONI.md` §1.11).  Whoever chooses the capture route asks here. */
bool codificatore_in_hardware(const Codificatore *cod);

/* ═══════════════════════════════════════════════════════════════════════════
 * ⛔⛔⛔ THE DMA-BUF STRIDE MUST BE A MULTIPLE OF 64 — and without this
 *       guard the defect GIVES NO ERROR: it gives a **blurred desktop sheared
 *       sideways**, and the milliseconds stay beautiful.
 *
 * ⭐⭐ THE FACT, `[M]` 22 Aug 2026, four sizes chosen on purpose on both
 *     sides of the threshold, read with the mark's CERTIFIED READER
 *     (`banchi/03-marca.py`, negative control 0 false out of 3 000):
 *
 *       | canvas    | stride| stride %64| is the mark read?  | contrast  |
 *       |-----------|-------|-----------|--------------------|-----------|
 *       | 1920x1080 |  7680 |     0     | ⭐ YES (pattern 65) |   1.000   |
 *       | 1552x888  |  6208 |     0     | ⭐ YES (pattern 70) |   1.000   |
 *       | 1544x888  |  6176 |    32     | ⛔ NO               |   0.617   |
 *       | 1560x888  |  6240 |    32     | ⛔ NO               |   0.510   |
 *
 *     ⭐ 1552 and 1544 are EIGHT pixels apart and give opposite verdicts: it is
 *        not a threshold chosen after seeing the result, it is a boundary to
 *        the pixel.
 *
 * `[R]` The iHD driver, importing a DMA-BUF, **does not honour a stride that is
 *       not a multiple of 64 bytes**: it reads the rows at a stride of its own,
 *       and the image comes out slanted by a few pixels per row.
 *
 * ⛔ AND COLOUR DOES NOT SEE IT: `[M]` the per-channel statistics of the two
 *    streams matched within **0.17 levels out of 255** while the mark was read
 *    on **0 frames out of 869**.  ⇒ A tool that looks at averages says
 *    green on this defect.  The number to look at is the STRUCTURE.
 *
 * ⚠ And the cure is NOT ours to carry out fully: the stride is decided by the
 *   producer, and the producer makes it equal to `larghezza × 4` `[M]` (4 sizes
 *   out of 4, LINEAR modifier).  ⇒ A canvas multiple of 16 would always have a
 *   good stride, but the canvas rule lives in `rcp_misura_ammessa()`, which
 *   does not belong to this file.  Here **the route is refused and declared**,
 *   which is what `LEZIONI.md` §1.8 demands: better the copy than a silently
 *   wrong image.
 * ═══════════════════════════════════════════════════════════════════════════ */
bool codificatore_stride_importabile(uint32_t stride);
uint32_t codificatore_allineamento_scheda(void);

void codificatore_rilascia(Codificatore *cod);

/*
 * ⛔ The next encode will be a REAL keyframe — with the parameter sets in front.
 *
 * Needed by `RICHIEDI_CHIAVE` (`RCP.md` §7.1) and by every abandoned delta
 * (§5.2: *«the server MUST send a keyframe as soon as it can, without waiting
 * for the client to ask for it»*).
 */
void codificatore_chiedi_chiave(Codificatore *cod);

/*
 * ⛔ The canvas change: it reopens at the new size, and the first frame after
 *    is a **real keyframe**.
 *
 * `RCP.md` §5.2, a line that came in on the evening of 12 Aug 2026 with the
 * measurement next to it: on HEVC in Chrome a delta at the new size **raises
 * nothing** — the decoder keeps emitting frames at the **old** size and
 * paints a wrecked image, different at every round.  ⇒ The symptom would be
 * *«the desktop tears when I resize the window»*, and it would name neither
 * the protocol nor the canvas.
 */
bool codificatore_ridimensiona(Codificatore *cod, uint32_t larghezza, uint32_t altezza,
                               char *errore, size_t errore_byte);

/*
 * ⭐⭐ QUALITY RECOVERY — and it is BORN OFF (invariant I6).
 *
 * ⛔ THE DEFECT IT CURES: `qualita_corrente` goes down when the frame breaks
 *    the 16 MiB ceiling of `RCP.md` §6.2, and until 23 Aug 2026 it **never
 *    went back up**.  A single exceptional frame — `[M]` the software fallback
 *    of the time at 7680x4320 on grainy footage broke the ceiling
 *    1 time out of 8 —
 *    left the encoder at the bottom of the scale **for the whole session**, and
 *    the user's still desktop came out grainy for hours.  ⚠ It is the *«never
 *    grainy»* of `DECISIONI.md` §3.3 lost through inertia.
 *
 * On: after a certain number of frames **in a row** that came out comfortably
 * under the ceiling it goes back up by **ONE** step, and **never** beyond the
 * quality the caller asked for in `CodificatoreRichiesta.qualita`.  Every step,
 * down and up, ends up in the log with the **measurement** next to the threshold.
 *
 * ⛔ It changes what one SEES ⇒ it is the user who decides that it becomes the
 *    normal behaviour, after judging it on the real desktop.  Off, the
 *    program behaves exactly as before, byte for byte.
 *
 * ⚠ It is a decision of the **server**, not of the single encoder: it holds for
 *   all those opened after the call, and the value in force is written to the
 *   log when each one opens — **on and off**, so that «off» and «never
 *   triggered» do not look the same.
 */
void codificatore_qualita_risale(bool accesa);

/*
 * ⭐⭐⭐ THE BANDWIDTH CEILING — phase 9, 23 Aug 2026.  **Born OFF** (0).
 *
 * ⛔ THE NUMBER THAT FORCES IT: `[M]` test machine, canvas 2560x1080, constant
 *    QP 26 (what the product does today), a **film with grain at full
 *    screen** asks for **58.7 Mbit/s**, that is **293 %** of the floor of 20
 *    declared in `DECISIONI.md` §3.1-bis — and **nobody tells it no**.
 *
 * ⭐ AND THE NUMBER THAT LIMITS ITS REACH, in the same measurement: the user's
 *    **real desktop**, full screen and moving, costs **0.204 Mbit/s
 *    = 1 %**.  ⇒ The ceiling is for the **hard case**.  A ceiling that bit on
 *    normal content would be the error for which v1's phase 10 was wiped, and
 *    the red that would say so is blunt: *«the real desktop, with the ceiling
 *    on, costs less than before»* ⇒ the cure is thrown away.
 *
 * The argument is the **floor in Mbit/s** (20, today), and from it are derived
 * the wire (80 %), the operating point (75 % of the wire — ⛔ **never equal to
 * the wire**: with the two numbers equal the driver deduces **CBR**, which is
 * R31) and the regulator's buffer (**40 ms**, against the 50 that `CODER.md`
 * §1-bis gives to **all** of our piece; v1 took **500** and nobody noticed).
 *
 * ⛔ It changes what one SEES — on the hard case the image gets worse, and that
 *    is its job — hence **I6**: the user turns it on after judging it on the
 *    real desktop.  In v1 this identical change made them say *«we have gone
 *    backwards»*.  Off, the program behaves **exactly** as today.
 *
 * ⚠ It holds only for **hardware** encoding (`h264_vaapi`): the software
 *   fallback stays at its CRF, and the value in force is written to the log
 *   when every encoder opens — **on and off**.
 */
void codificatore_tetto_banda(uint32_t pavimento_mbit);

#endif
