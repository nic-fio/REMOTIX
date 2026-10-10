/*
 * codificatore.c — HEVC Main10 and AV1, in software **or in hardware via VA-API**,
 * with the confession read from the bytes.  The why of every choice is in
 * `codificatore.h`; here is the how, and next to every odd line the measurement
 * that made it necessary.
 *
 * ⭐ The GPU is used since 13 Aug 2026 (phase 3, brought forward by the user's
 *    decision).  ⛔ But **only for encoding**: zero copy — the frame that goes
 *    from capture to the GPU without passing through system memory — stays in
 *    phase 8, and here the upload is paid for and **measured separately**
 *    (`us_caricamento`), so that we can see how much removing it will be worth.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ PHASE 18 (30 Sep 2026, `DECISIONI.md` §10.25) — THE TWO HALVES OF THE FILE
 * From today the file has TWO routes that do not share a line of codec, and
 * ⛔ neither of them goes through ffmpeg:
 *
 *   THE CARD      `vadiretta.c`: libva used directly — parameters, headers
 *                 written by us, coded buffers.  The colour conversion is
 *                 done by the card's VPP on the zero copy; on the "from
 *                 memory" route it is done by `colori709.c` on the CPU
 *                 (NV12/P010) and then the planes are uploaded to the card, as
 *                 before phase 18 — the VPP from memory is measured WORSE
 *                 (see `prepara_fotogramma()`).
 *   ⛔ The software FALLBACK (OpenH264, SVT-AV1: `ripiego.c`) LEFT with
 *                 phase 19 (1 Oct 2026, `DECISIONI.md` §10.27), in the
 *                 user's words: *"no CPU without a card"*.  A name that does
 *                 not belong to the card is refused in `codificatore_nuovo()`,
 *                 with the reason: without a capable card REMOTIX does not encode.
 *
 * What lies OUTSIDE the card route — the 16 MiB ceiling, the degradation
 * ladder and the climb back, the shape of the bytes, the D-023 frame, the
 * third bitrate witness — works on the BYTES, and holds identically for BOTH
 * card routes.
 *
 * ⭐⭐ PHASE 19 (1 Oct 2026, `DECISIONI.md` §10.27) — THE TWO CARD ROUTES,
 *     CHOSEN BY CAPABILITY AND NOT BY BRAND.  The user's words: *"encoding
 *     must happen with standard tools, preferably with Vulkan, which is common
 *     to all 4 architectures"*.
 *
 *   1. VULKAN VIDEO  `vulkanvideo.c`: if `vulkanvideo_capacita()` says the
 *                    node's card encodes THAT codec (today AMD with RADV,
 *                    NVIDIA with the proprietary driver; Intel when Mesa makes
 *                    it stable).  Zero copy from the DMA-BUF and colour
 *                    conversion on the card with the shader; from memory the
 *                    BGRx are uploaded as they are and the same shader converts them.
 *   2. VA-API        `vadiretta.c`, as it was: where Vulkan is missing (today Intel).
 *   —  no processor: without a route the encoder is not born, and it says
 *      so.
 *
 *   The choice is made in `apri_dispositivo()`, ONCE per encoder, and is
 *   written to the log and to the confession (`strada`).  ⛔ It can also be
 *   requested by name (`h264_vulkan`, `h264_vaapi`): then there is NO fallback
 *   to the other — whoever asks by name is measuring (`CODER.md` §3.9).
 *   ⚠ Everything downstream of the bytes (ceiling, ladder, climb, shape,
 *   frame, key on request, resize) is ONE for both routes: the cures are not
 *   duplicated, and a green bench on one holds for the other.
 * ═══════════════════════════════════════════════════════════════════════════
 */
#include "codificatore.h"
#include "colori709.h"
#include "registro.h"
#include "scrittore_bit.h"
#include "vadiretta.h"
#include "vulkanvideo.h"

#include <inttypes.h>
#include <limits.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#include <va/va.h>
/* ⭐ The three that arrive with ZERO COPY: `va_drmcommon.h` brings the descriptor
 *    with which a DMA-BUF is imported (`VADRMPRIMESurfaceDescriptor`), `va_vpp.h`
 *    the colour conversion done by the GPU (`VAProcPipelineParameterBuffer`),
 *    and `drm_fourcc.h` the only two format names this module recognises.
 * ⚠ `drm_fourcc.h` is headers ONLY: no library to link — the same note the
 *   Makefile already has for `cattura.c`. */
#include <drm_fourcc.h>
#include <va/va_drmcommon.h>
#include <va/va_vpp.h>

/* ⚠ An area of its own instead of one of the six in `registro.h`: that file is
 *   not part of this sub-phase and is not touched.  The line to centralise it —
 *   `#define REG_VIDEO "video"` — is in the report, together with the Makefile ones. */
#define REG_CODIFICA "video"

/* `RCP.md` §6.2: "the server MUST NOT produce a frame longer than 16 MiB.  If
 * encoding produced a bigger one, it MUST re-encode it at lower quality and
 * WRITE IT TO THE LOG — never send it." */
#define TETTO_FOTOGRAMMA (16u * 1024u * 1024u)

/* ⛔ How many ENCODINGS a DELTA is granted in total — not how many descents: the
 *    descents are `RICODIFICHE_MASSIME - 1`, because the first encoding is the
 *    one at the requested quality and does not come from any descent.  ⇒ With
 *    3: QP 26, 35, 44, and the ladder stops there.
 * ⛔ And the last rung is NOT applied unless it is tried: the count sits **before**
 *    `abbassa_qualita()`, and the why is in the box inside
 *    `comprimi_comune()`.
 * ⚠ It does not apply to a KEY at all: §5.2 forbids abandoning it, and for a key
 *   the ladder is walked all the way down. */
#define RICODIFICHE_MASSIME 3

/* The first rung when the ceiling bites, and the step of the following ones.
 *
 * ⛔⛔ AND THE STEP WAS 6, THAT IS ONE RUNG SHORT — `[M]` 22 Aug 2026,
 *      measured by agent D at 7680x4320 with nearly incompressible content,
 *      n=8 per row:
 *
 *        the last rung there was      QP 38 → **16.654 MiB**  ⛔ 8 times out of 8
 *                                                                above the ceiling
 *        the one that was NOT there   QP 44 → 11.056 MiB      ⭐ it would have
 *                                                                made it
 *
 *      ⇒ The ceiling is 16 777 216 bytes and **QP 38 sits at 104.1 %: it lost by
 *        4 %**.  Three attempts of 6 reached 38 and stopped there.
 *
 * ⭐ AND THE STEP IS RAISED, NOT THE NUMBER OF ATTEMPTS: `[M]` each attempt at 8K
 *    costs **91-108 ms in hardware** (and 1.8-3.3 s in software), so a wider
 *    step costs **a fraction** of one more attempt.  With 9 the ladder
 *    is 26 → 35 → 44 → 51, and it includes the rung that made it.
 *
 * ⚠ AND THE EXACT VALUE IS NOT DECIDED HERE: how fast to descend is a working
 *   point between quality and bandwidth, that is **phase 9**.  Here we only state
 *   that **3 x 6 was not enough**, with the number that proves it.
 *
 * ⚠ And how reachable it is must be said alongside, or the defect looks bigger
 *   than it is: `[M]` at the user's canvas (2560x1080) the biggest key
 *   over **404 real keys** is **21 433 bytes**, that is **0.13 %** of the ceiling —
 *   a **782x** margin.  ⇒ A real and proven defect, and **not urgent**. */
#define CRF_DI_EMERGENZA 24
#define CRF_PASSO 9

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ AND THE LADDER IS CLIMBED BACK — phase 9, 23 Aug 2026.
 *
 * ⛔ THE DEFECT: until now `qualita_corrente` was monotonic in the worse direction.
 *    Four writes in all (`codificatore_nuovo()` seeds it, and the three
 *    inside `abbassa_qualita()`), **all going down**, and no path that would
 *    bring it back up — not even `codificatore_ridimensiona()`, which closes and
 *    reopens the context **keeping it**.
 *
 *    ⇒ A single exceptional frame — `[M]` the software fallback of the time
 *      at 7680x4320 on grainy footage broke the ceiling 1 time out of
 *      8 — left the
 *      encoder at CRF 47 (or QP 51) **for the whole session**: the user's
 *      still desktop came out grainy **for hours**, and no log line
 *      said why.  ⚠ It is the *"never grainy"* of `DECISIONI.md` §3.3 lost
 *      through inertia instead of by decision.
 *
 * ⛔ AND IT IS NOT SYMMETRIC TO THE DESCENT, ON PURPOSE: we descend several rungs in
 *    a single frame, we climb back **ONE** every `RISALITA_ATTESA` quiet
 *    frames, and never beyond the quality **requested** by the caller.  ⚠ Because
 *    each reopening costs `[M]` 91-108 ms in hardware and 1.8-3.3 s in software:
 *    a climb that bumps into the ceiling and descends again would be **dearer
 *    than the defect it cures**.
 *
 * ⛔⛔ AND HOW MANY "SEVERAL RUNGS" ARE CHANGED ON 23 AUG 2026, so whoever
 *      compares yesterday's numbers with tomorrow's must know it:
 *
 *        before  a DELTA above the ceiling walked the ladder **all the way down**
 *                (from QP 26: 35, 44, 51 — **three** descents), because the
 *                `RICODIFICHE_MASSIME` count was dead code.  ⚠ Meanwhile the
 *                startup line declared that it stopped after three re-encodings.
 *        now     a DELTA makes `RICODIFICHE_MASSIME` encodings, that is **two**
 *                descents (35, 44), both tried.  A KEY does not change
 *                one bit: §5.2 forbids abandoning it, and it walks the whole
 *                ladder as before.
 *
 *      ⇒ THE CLIMB HAS TWO RUNGS TO REDO INSTEAD OF THREE, and the numbers
 *        below **still hold**, for this reason: from QP 44 we go back to 35
 *        after `RISALITA_ATTESA` (120) quiet frames, and from 35 to 26 after
 *        **twice** that (240), because 26 is the rung on which the ceiling bit
 *        (`qualita_fallita`) and we do not set foot there again in a hurry.  Total
 *        **360 frames, ~6 s at 60/s**, against the **480 (~8 s)** that were needed
 *        starting from 51.  ⛔ The change shortens the grainy spell by ~2 s and touches
 *        neither the direction nor the shape of the climb: **there is no written reason
 *        to retune `RISALITA_ATTESA`**, and without a written reason it is not touched.
 *        ⚠ `RISALITA_MARGINE` stays one eighth of the ceiling = 2 MiB, and with two
 *        rungs instead of three the margin is if anything **wider**, not narrower.
 *
 * ⛔⛔ THE CHECK THAT DECIDES — FLAPPING, and it must be written here because it is the
 *      fault that would bring this cure down.  A scene that lives **on the edge
 *      of the ceiling** (`[M]` grain `alls=60` at 7680x4320 in hardware: **94.9 %**)
 *      could make it descend and climb continuously, paying a
 *      reopening and a KEY on every round — and the price would be paid by the
 *      **rate**, that is precisely invariant I1 that this cure claims to serve.
 *
 *      ⭐ It is against that that the two numbers are chosen, and the defence is DOUBLE:
 *
 *        1. `RISALITA_MARGINE` is **one eighth** of the ceiling, not the ceiling.  We
 *           count the frame **comfortably** below, not the frame
 *           "below": a scene at 94.9 % of the ceiling produces **not even one**
 *           quiet frame ⇒ `sotto_margine` stays at zero ⇒ **it never
 *           climbs**, and there is nothing to flap.  For
 *           flapping to happen you would need a scene that alternates **8x** in
 *           size while staying calm for two whole seconds: that is not an
 *           edge, it is a real scene change.
 *        2. `risalita_attesa` **DOUBLES on every relapse** and never comes back
 *           down.  Even in the worst case the frequency of reopenings
 *           halves on every round, and at `RISALITA_ATTESA_MAX` it stops at one every
 *           ~64 s.  ⚠ The direction in which to err is patience.
 *
 *      ⇒ If the bench of `fasi/09-la-qualita-e-la-degradazione.md` §5 (case 2: more than 3
 *        reopenings per minute; case 3: frames/s **with** the cure lower
 *        than those **without**, paired on the same scene) found
 *        flapping anyway, **these three numbers are wrong** — or the cure
 *        must be removed.
 *
 * ⚠ The three numbers are `[?]` **sufficient, not right**, exactly like
 *   `CRF_PASSO` = 9: the working point belongs to this phase, and the one to tune them is the
 *   bench, not this line.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define RISALITA_MARGINE (TETTO_FOTOGRAMMA / 8u) /* 2 MiB: there is room for two rungs */
#define RISALITA_ATTESA 120u                     /* ~2 s at 60/s */
#define RISALITA_ATTESA_MAX 3840u                /* ~64 s: the bottom of the doubling */

/*
 * ⛔ THE SWITCH, AND IT IS BORN OFF — invariant I6: *whatever changes what
 *    is SEEN stays behind a switch that is off until the user looks at it*
 *    (`CODER.md`, the table of invariants).  The climb changes what is
 *    seen — a desktop that
 *    turns sharp again instead of staying grainy — so it does not turn itself on.
 *
 * ⚠ Static and not per encoder: it is a decision of the **server**, not of the
 *   client nor of the single stream.  It is the same shape as `wt_ritmo_adattivo()`.
 */
static bool risalita_accesa;

void codificatore_qualita_risale(bool accesa)
{
	risalita_accesa = accesa;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐⭐ THE BANDWIDTH CEILING — phase 9, 23 Aug 2026, and IT IS BORN OFF
 *
 * ⛔ THE NUMBER THAT FORCES IT, and until this morning it was not there.  `[M]` test
 *    machine, canvas **2560x1080**, `h264_vaapi` `EncSliceLP`, **constant QP 26**
 *    (that is what the product does today), 30 s per point, wide line
 *    (`fasi/09-la-qualita-e-la-degradazione.md` §3.8):
 *
 *      scene                                  fr/s    video      share of 20 Mbit/s
 *      still                                   0.00   0          0 %
 *      ⭐ the user's REAL DESKTOP              23.10   0.204      **1.0 %**
 *      flat-colour bands, full screen          40.57   1.179      5.9 %
 *      DITHERED gradient, full screen          34.93   21.356     ⛔ 106.8 %
 *      ⛔ film with GRAIN, full screen         23.44   58.668     ⛔ **293.3 %**
 *
 * ⇒ ⛔ The hard case asks for **three times the floor** and **nobody tells it
 *   no**: under CQP the quantiser is fixed and the bandwidth is whatever comes out.
 * ⇒ ⭐ But the **real** content costs **1 %**.  A ceiling that bit **there**
 *   would be the mistake for which phase 10 of v1 was reset.
 * ⇒ ⛔⛔ And the regulator **cannot look at how many pixels change**: `pieno` and
 *   `barra` move **the same pixels** and cost **1.2 against 21.4**.  The
 *   right quantity is **the bits**, and the one watching them is the driver's regulator.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * ⭐⭐ WHY **QVBR** AND NOT VBR — and it is not an opinion, it is BYTES
 *
 * `[M]` 23 Aug 2026, **on this laptop** (⚠ not the test machine:
 * same driver **Intel iHD 25.2.3**, different GPU), `h264_vaapi`
 * `VAProfileH264High/EncSliceLP`, 2560x1080, 25 fps, 6 s, `bf 0`,
 * `async_depth 1`, `idr_interval 0`.  Two scenes: **still** (one frame of
 * `testsrc2` repeated) and **hard** (`testsrc2` + `noise=alls=60`):
 *
 *      mode               still scene        hard scene
 *      CQP 26             0.193 Mbit/s       ⛔ **259.9 Mbit/s**
 *      CBR 16M            ⛔ **15.98**        15.99
 *      VBR 12/16M qp=26   0.686              11.13
 *      VBR 12/16M NO qp   0.686              11.13   ⛔ **byte for byte identical**
 *      ⭐ QVBR 12/16M qp=26 **0.218**         **11.14**
 *
 * ⛔⛔ **UNDER VBR THE `qp` IS IGNORED**, and the proof is not a reasoning: it is
 *      that with and without `qp=26` the **very same bytes** come out (8 350 170 and
 *      514 142, twice out of two).  ⇒ With VBR **the whole degradation ladder of
 *      this file** (`abbassa_qualita()`, `CRF_PASSO`) and **the
 *      climb written this morning** would become **silent no-ops**: a
 *      component that ignores an option without saying so, that is the E2 form that
 *      this file exists so as not to suffer.  **VBR is out.**
 *
 * ⭐ **Under QVBR the `qp` is the quality factor and the ladder HOLDS**, `[M]`
 *    still scene: QP 26 → 0.218 · QP 35 → 0.125 · QP 44 → 0.076 Mbit/s.
 *    ⚠ And on a **hard** scene the ladder no longer bites (11.14 · 11.31 · 11.19):
 *    when the ceiling is engaged the quality is decided by **the ceiling**, not the QP.
 *    It must be said, because a bench that looked there for the effect of the QP would not
 *    find it and would conclude wrongly.
 *
 * ⛔ **AND CBR IS UNMASKED ON OUR OWN HARDWARE**: on a still scene it spends
 *    **15.98 Mbit/s against 0.193** for CQP — **83 times** for nothing.  R31 of v1
 *    said 42x at 1440p; here it is worse.  ⇒ The R31 lesson is not history.
 *
 * ⭐ And the fourth red of the study (`fasi/09-la-qualita-e-la-degradazione.md` §5) has
 *   **FALLEN**: declaring 16 Mbit/s ffmpeg prints `Using level 5`, that is 5.0.
 *   The bandwidth does **not** raise `level_idc`, and `avc1.640033` holds.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * ⛔ THE THREE NUMBERS, AND NONE IS WRITTEN BY HAND — they derive from the floor
 *
 * The floor is **20 Mbit/s** (`DECISIONI.md` §3.1-bis, `CODER.md` §1-bis).
 * Next to the video sits everything else, and `[M]` §3.8 **measures** it: on a
 * still scene, with **zero** video, **2.426 Mbit/s** cross the wire (audio, input,
 * clipboard, the cost of QUIC).
 *
 *   `rc_max_rate` = **80 % of the floor** = 16 Mbit/s.  ⇒ 16 + 2.4 measured
 *                   = 18.4, that is **92 %** of the floor: the margin is there and
 *                   has a number under it instead of being caution.
 *   `bit_rate`    = **75 % of the wire** = 12 Mbit/s.  ⛔ **NEVER equal to the wire**:
 *                   it is R31 to the letter — with `rc_max_rate == bit_rate` the
 *                   Intel driver *deduced* **CBR**, without an error, without a
 *                   warning, without a log line, and there was a bill.
 *   `rc_buffer_size` = wire x **40 ms**.  ⛔ AND THIS IS THE NUMBER THAT V1 GOT
 *                   WRONG WITHOUT ANYONE NOTICING:
 *                   `fondamenta/remotix-c/src/codificatore.c:256` set
 *                   `rc_buffer_size = bit_rate / 2`, which **is not "half": it is
 *                   half a SECOND** (a VBV is measured in bits, and `bit_rate/2`
 *                   bits at `bit_rate` bit/s make 500 ms) — **ten times** the
 *                   50 ms ceiling that `CODER.md` §1-bis gives to **all** of
 *                   our part.  ⭐ Here it is **40**, that is the *target* and
 *                   not the *ceiling*: the direction in which to err is the uncomfortable one.
 *                   ⚠ And the number is not deduced, it is **printed by ffmpeg**:
 *                   `[M]` *"RC target: 75 % of 16000000 bps over 40 ms"*.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * ⛔⛔ THE PREDICTION, WRITTEN BEFORE THE MEASUREMENT ON THE TEST MACHINE
 *
 * The five scenes of §3.8, in Mbit/s of **video load**, with the ceiling OFF (that is
 * what has already been measured) and with the ceiling ON at 20:
 *
 *      scene                       off `[M]`      ⇒ on `[?]`
 *      still                       0.000          **0.000**  (no frames)
 *      ⭐ the user's real desktop   0.204          **0.20 – 0.45**
 *      flat-colour bands           1.179          **1.1 – 1.6**
 *      dithered gradient           21.356         ⛔ **11 – 16**, and NEVER above 16
 *      ⛔ film with grain           58.668         ⛔ **11 – 16**, and NEVER above 16
 *
 * The bottom of the two "11" is `[M]`: the laptop's hard scene, with the wire at 16,
 * settled at **11.14**.
 *
 * ⛔ **AND THE REDS THAT WOULD PROVE ME WRONG** — two change the conclusion:
 *
 *   1 ⭐⭐ the **real desktop** with the ceiling on costs **less** than 0.204
 *          ⇒ the ceiling is **saving where it must not**, that is it is v1
 *          repeating itself (*"happy to save"*), and **this cure is thrown away**.
 *          `[M]` on the laptop QVBR spends **13 % more** than CQP on a still
 *          scene (0.218 against 0.193), so the prediction is *"it does not go down"* —
 *          and it is clear-cut.
 *   2 ⭐⭐ the **dithered gradient** with the ceiling on stays **above** 20
 *          ⇒ the driver **did not obey**, and witness 2 was green for
 *          nothing: it is R31 holding **even against the explicit request**.
 *          ⇒ Only the **third** witness catches it, the bytes.
 *   3      `avcodec_open2` fails with *"Driver does not support QVBR RC
 *          mode"* ⇒ the test machine is not the laptop, and we reread the
 *          mask that `apri_dispositivo()` has just written to the log.
 *   4      frames/s **drop** on the easy scenes ⇒ the regulator costs
 *          time where it is not needed, and the price is paid by I1.
 *
 * ⚠ And the number that unmasks CBR is on a **STILL** scene (`[M]` 83x here, 42x
 *   in v1): on a hard scene the regulated modes all sit within 1 % of one
 *   another and a bench that measured only there **would measure nothing**.
 *   ⛔ On the product, though, "still" means **zero frames** (§3.8: 0.00
 *   fr/s), so the scene that acts as control is the second one: the real desktop,
 *   which moves and costs 1 %.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * ⛔ THE SWITCH, AND IT IS BORN OFF — invariant I6.  The ceiling changes what
 *    is SEEN (in the hard case the picture gets uglier: that is its job),
 *    and in v1 **this identical change** made the user say *"we have gone
 *    backwards"*.  Off, the program behaves **exactly** as today:
 *    `rc_mode=CQP`, no `bit_rate`, no buffer.
 *
 * ⚠ What is NOT touched here, and it must be said: `max_frame_size`.  `[M]` ffmpeg
 *   refuses it under CQP (*"Max frame size is invalid in CQP rate control mode"*) and
 *   accepts it under QVBR — it would give **in one pass** what today costs up
 *   to `RICODIFICHE_MASSIME` reopenings of `[M]` 91-108 ms.  ⛔ It is not turned on
 *   today: it is a **second** lever on the same quantity, and two levers on
 *   together in the first round would give two measurements under the same label.  ⭐ And
 *   the 40 ms buffer already does almost all of its work.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define TETTO_VBV_MS 40u        /* the TARGET of CODER.md §1-bis, not the 50 ceiling */
#define TETTO_QUOTA_FILO 80u    /* % of the floor that goes to video: the rest is [M] 2.4 Mbit/s */
#define TETTO_QUOTA_PUNTO 75u   /* % of the wire: the working point.  ⛔ NEVER 100 — that is R31 */

/*
 * ⭐ The window of the third witness.  ⚠ Ten seconds and not one: shorter, it
 *   would measure the single frame (which is already printed elsewhere) instead of the
 *   **bandwidth**, and longer it would arrive after the bench has finished.  ⛔ And it holds
 *   with the ceiling OFF as with the ceiling on: a witness that existed only with the
 *   cure on could not compare anything.
 */
#define BANDA_FINESTRA_US (10u * 1000u * 1000u)

/*
 * 0 = OFF, and it is the value at birth.  Non-zero = the declared **floor**
 * in Mbit/s (20, today), from which the three numbers derive.
 *
 * ⚠ Static and not per encoder: it is a decision of the **server**, like the
 *   climb above and like `wt_ritmo_adattivo()`.
 */
static uint32_t tetto_pavimento_mbit;

void codificatore_tetto_banda(uint32_t pavimento_mbit)
{
	tetto_pavimento_mbit = pavimento_mbit;
}

/*
 * ⛔ The three numbers are COMPUTED in one place only, and whoever prints them in the log
 *    calls these, and does not rewrite the computation: two drafts of the same number are
 *    a place to diverge silently.
 */
static int64_t tetto_filo(void)
{
	return (int64_t) tetto_pavimento_mbit * 1000000 * TETTO_QUOTA_FILO / 100;
}

static int64_t tetto_punto(void)
{
	return tetto_filo() * TETTO_QUOTA_PUNTO / 100;
}

static int tetto_serbatoio_bit(void)
{
	return (int) (tetto_filo() * TETTO_VBV_MS / 1000);
}

/*
 * ⭐⭐ THE BITRATE MODE, ASKED FOR BY NAME — and the two names live here, together
 *     with the bit the driver uses to say it has it.
 *
 * ⛔ R31, the dearest lesson of the project: *"the bitrate control mode
 *    is not chosen: the driver deduces it"*.  ⇒ `rc_mode=auto` is forbidden: `[M]`
 *    ffmpeg on `auto` chooses based on the other options, and in v1 it chose **CBR**
 *    because two numbers were equal.  Asking by name makes
 *    `avcodec_open2` **fail** instead of letting a bill arrive.
 */
typedef struct {
	int rc_mode;        /* the number phase 9 called it by (formerly the libavcodec option) */
	unsigned va_bit;    /* the bit with which the driver DECLARES it */
	const char *nome;
} ModoBitrate;

static ModoBitrate modo_bitrate_voluto(void)
{
	if (tetto_pavimento_mbit)
		return (ModoBitrate){ 5, VA_RC_QVBR, "QVBR" };
	return (ModoBitrate){ 1, VA_RC_CQP, "CQP" };
}

/*
 * The driver's mask, in plain text.  ⚠ All the bits `va.h` knows, not
 * only the four we care about: a bit we cannot name is printed
 * as a number, and does not disappear.
 */
static void nomi_modi_bitrate(unsigned maschera, char *fuori, size_t byte)
{
	static const struct {
		unsigned bit;
		const char *nome;
	} NOTI[] = {
		{ VA_RC_NONE, "NONE" },   { VA_RC_CBR, "CBR" },
		{ VA_RC_VBR, "VBR" },     { VA_RC_VCM, "VCM" },
		{ VA_RC_CQP, "CQP" },     { VA_RC_VBR_CONSTRAINED, "VBR_CONSTRAINED" },
		{ VA_RC_ICQ, "ICQ" },     { VA_RC_MB, "MB" },
		{ VA_RC_CFS, "CFS" },     { VA_RC_PARALLEL, "PARALLEL" },
		{ VA_RC_QVBR, "QVBR" },   { VA_RC_AVBR, "AVBR" },
		{ VA_RC_TCBRC, "TCBRC" },
	};
	if (!fuori || !byte)
		return;
	fuori[0] = 0;
	unsigned restanti = maschera;
	for (size_t i = 0; i < sizeof(NOTI) / sizeof(NOTI[0]); i++) {
		if (!(maschera & NOTI[i].bit))
			continue;
		restanti &= ~NOTI[i].bit;
		char pezzo[32];
		snprintf(pezzo, sizeof(pezzo), "%s%s", fuori[0] ? "|" : "", NOTI[i].nome);
		strncat(fuori, pezzo, byte - strlen(fuori) - 1);
	}
	if (restanti) {
		char pezzo[32];
		snprintf(pezzo, sizeof(pezzo), "%s0x%x(?)", fuori[0] ? "|" : "", restanti);
		strncat(fuori, pezzo, byte - strlen(fuori) - 1);
	}
	if (!fuori[0])
		strncat(fuori, "none", byte - 1);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * THE BIT READER — it serves to reread what we have just produced
 *
 * ⛔ It exists because the second E2 witness must be INDEPENDENT of the
 *    first: `AVCodecContext` says what libavcodec believes it asked for, and
 *    this reader says what is written in the bytes.  If the two diverge, it is
 *    the component that disobeyed — and it really happened, `[M]` 12 Aug
 *    2026: libsvtav1 prints "Error parsing option" on an option it does not know
 *    and **carries on, exiting 0**.
 * ═══════════════════════════════════════════════════════════════════════════ */
typedef struct {
	const uint8_t *dati;
	size_t byte;
	size_t bit;   /* position, in bits */
	bool finito;  /* ⛔ three outcomes, not two: "0" and "I could not read" */
} LettoreBit;

/* ⭐ WHERE THE FRAME SITS in the SPS (D-023, phase 18): the position in bits — in
 *    the RBSP without emulation — of the cropping flag (`frame_cropping_flag` in
 *    H.264, `conformance_window_flag` in HEVC), the four offsets if there were any,
 *    and the bit after.  It lets `cornice_al_suo_posto()` rewrite the head
 *    of the SPS and copy the tail back as it is. */
typedef struct {
	size_t bit_flag;      /* where the flag sits */
	size_t bit_dopo;      /* the first bit after the flag and its offsets */
	bool presente;        /* the flag was 1 */
	uint32_t sx, dx, su, giu; /* the offsets read (0 if the flag was 0) */
} PosizioneCornice;

static void lb_apri(LettoreBit *l, const uint8_t *dati, size_t byte)
{
	l->dati = dati;
	l->byte = byte;
	l->bit = 0;
	l->finito = false;
}

static uint32_t lb_bit(LettoreBit *l, int quanti)
{
	uint32_t v = 0;
	for (int i = 0; i < quanti; i++) {
		size_t indice = l->bit >> 3;
		if (indice >= l->byte) {
			l->finito = true;
			return v;
		}
		int scarto = 7 - (int) (l->bit & 7);
		v = (v << 1) | (uint32_t) ((l->dati[indice] >> scarto) & 1);
		l->bit++;
	}
	return v;
}

/* ⭐ SIGNED Exp-Golomb — needed by the H.264 SPS (the scaling lists and the
 *    picture order count offsets), and HEVC did not need it here.
 * ⛔ The mapping is the standard's (9.1.1): k → (-1)^(k+1) * ceil(k/2). */
static int32_t lb_se(LettoreBit *l);

/* Unsigned Exp-Golomb, the H.265 one. */
static uint32_t lb_ue(LettoreBit *l)
{
	int zeri = 0;
	while (!l->finito && lb_bit(l, 1) == 0 && zeri < 32)
		zeri++;
	if (l->finito || zeri >= 32)
		return 0;
	return ((1u << zeri) - 1) + (zeri ? lb_bit(l, zeri) : 0);
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ANNEX-B — walking the NALs, which is what Chromium does too
 *
 * `[R]` `video_decoder.cc:206-214` calls `media::mp4::HEVC::AnalyzeAnnexB()`
 * after every `configure()`/`flush()` and ⛔ **does not trust our label**:
 * if the chunk marked `key` does not contain an IDR with its parameter sets,
 * it refuses.  ⇒ Here we do the same thing **before sending**, instead of
 * finding out in F2.5 where the symptom would be "the page stays black".
 * ═══════════════════════════════════════════════════════════════════════════ */
#define NAL_IDR_W_RADL 19
#define NAL_IDR_N_LP 20
#define NAL_CRA 21
#define NAL_VPS 32
#define NAL_SPS 33
#define NAL_PPS 34
#define NAL_VCL_MASSIMO 31

typedef struct {
	bool ha_vps, ha_sps, ha_pps;
	bool ha_idr;
	bool parametri_prima_dell_idr; /* ⛔ the half that gets forgotten */
	bool primo_vcl_e_chiave;
	size_t sps_offset, sps_byte;
} FormaAnnexB;

/* Finds the next start code: returns the offset of the first byte of the
 * NAL, or `byte` if there are no more.
 * ⛔ BOTH codes are recognised, `00 00 01` and `00 00 00 01`: a reader
 *    that knew only one would skip half the NALs **without complaining**, and
 *    would say "this stream has no PPS" of a stream that has it.  A false
 *    red costs as much as a false green. */
static size_t annexb_prossimo(const uint8_t *d, size_t byte, size_t da, size_t *inizio_codice)
{
	for (size_t i = da; i + 2 < byte; i++) {
		if (d[i] == 0 && d[i + 1] == 0 && d[i + 2] == 1) {
			if (inizio_codice)
				*inizio_codice = (i >= 1 && d[i - 1] == 0) ? i - 1 : i;
			return i + 3;
		}
	}
	if (inizio_codice)
		*inizio_codice = byte;
	return byte;
}

static void annexb_leggi(const uint8_t *d, size_t byte, FormaAnnexB *f)
{
	memset(f, 0, sizeof(*f));
	bool visto_vcl = false;
	bool p_vps = false, p_sps = false, p_pps = false;
	size_t corpo = annexb_prossimo(d, byte, 0, NULL);
	while (corpo < byte) {
		size_t dove_dopo;
		size_t prossimo = annexb_prossimo(d, byte, corpo, &dove_dopo);
		size_t fine = (prossimo < byte) ? dove_dopo : byte;
		int tipo = (d[corpo] >> 1) & 0x3F;

		if (tipo == NAL_VPS) {
			f->ha_vps = true;
			p_vps = true;
		} else if (tipo == NAL_SPS) {
			f->ha_sps = true;
			p_sps = true;
			if (!f->sps_byte) {
				f->sps_offset = corpo;
				f->sps_byte = fine - corpo;
			}
		} else if (tipo == NAL_PPS) {
			f->ha_pps = true;
			p_pps = true;
		} else if (tipo <= NAL_VCL_MASSIMO) {
			bool chiave = (tipo == NAL_IDR_W_RADL || tipo == NAL_IDR_N_LP || tipo == NAL_CRA);
			if (!visto_vcl) {
				visto_vcl = true;
				f->primo_vcl_e_chiave = chiave;
			}
			if (chiave) {
				f->ha_idr = true;
				/* ⛔ The group must be COMPLETE and come BEFORE this
				 *    IDR, not somewhere in the stream. */
				if (p_vps && p_sps && p_pps)
					f->parametri_prima_dell_idr = true;
			}
			p_vps = p_sps = p_pps = false;
		}
		corpo = prossimo;
	}
}

static int32_t lb_se(LettoreBit *l)
{
	uint32_t k = lb_ue(l);
	return (k & 1) ? (int32_t) ((k + 1) / 2) : -(int32_t) (k / 2);
}

/* Removes the emulation prevention bytes: `00 00 03` → `00 00`.
 * ⛔ Without this step an SPS that contains that sequence is read wrong, and
 *    the number that comes out of it (the bit depth) would be wrong WITHOUT
 *    looking it.  It is the same trap that ISO/IEC 14496-15 puts in the hvcC —
 *    one of the four reasons why D1 chooses Annex-B. */
static size_t togli_emulazione(const uint8_t *dentro, size_t byte, uint8_t *fuori, size_t massimo)
{
	size_t n = 0, zeri = 0;
	for (size_t i = 0; i < byte && n < massimo; i++) {
		if (zeri >= 2 && dentro[i] == 3) {
			zeri = 0;
			continue;
		}
		fuori[n++] = dentro[i];
		zeri = (dentro[i] == 0) ? zeri + 1 : 0;
	}
	return n;
}

static uint32_t rovescia32(uint32_t v)
{
	uint32_t r = 0;
	for (int i = 0; i < 32; i++) {
		r = (r << 1) | (v & 1);
		v >>= 1;
	}
	return r;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ H.264 — THE SAME SHAPE, WITH THE NUMBERS OF ANOTHER STANDARD
 *
 * ⛔ And the numbers differ in a spot you get wrong only once: in HEVC
 *    the NAL type sits in the **six bits** after the first (`(b >> 1) & 0x3F`), in
 *    H.264 in the **five low bits** of the first (`b & 0x1F`).  A reader that
 *    used the wrong formula would read an IDR (5) as a NAL of type 2,
 *    that is it would say "this key is not a key" **of a real key**.
 *
 * ⚠ And H.264 has TWO parameter sets, not three: there is no VPS.  Asking
 *   for it too would refuse every valid key.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define NAL264_NON_IDR 1
#define NAL264_IDR 5
#define NAL264_SPS 7
#define NAL264_PPS 8

typedef struct {
	bool ha_sps, ha_pps, ha_idr;
	bool parametri_prima_dell_idr;
	bool primo_vcl_e_chiave;
	size_t sps_offset, sps_byte;
} FormaAnnexB264;

static void annexb264_leggi(const uint8_t *d, size_t byte, FormaAnnexB264 *f)
{
	bool visto_vcl = false;
	bool p_sps = false, p_pps = false;
	size_t corpo;

	memset(f, 0, sizeof(*f));
	corpo = annexb_prossimo(d, byte, 0, NULL);
	while (corpo < byte) {
		size_t dove_dopo;
		size_t prossimo = annexb_prossimo(d, byte, corpo, &dove_dopo);
		size_t fine = (prossimo < byte) ? dove_dopo : byte;
		int tipo = d[corpo] & 0x1F;

		if (tipo == NAL264_SPS) {
			f->ha_sps = true;
			p_sps = true;
			if (!f->sps_byte) {
				f->sps_offset = corpo;
				f->sps_byte = fine - corpo;
			}
		} else if (tipo == NAL264_PPS) {
			f->ha_pps = true;
			p_pps = true;
		} else if (tipo >= NAL264_NON_IDR && tipo <= NAL264_IDR) {
			bool chiave = (tipo == NAL264_IDR);
			if (!visto_vcl) {
				visto_vcl = true;
				f->primo_vcl_e_chiave = chiave;
			}
			if (chiave) {
				f->ha_idr = true;
				if (p_sps && p_pps)
					f->parametri_prima_dell_idr = true;
			}
			p_sps = p_pps = false;
		}
		corpo = prossimo;
	}
}

/* The SPS scaling lists: their content is not read, they are SKIPPED — but they
 * are skipped by reading them, because they are variable-length and whoever counted them
 * in bytes would throw off everything that comes after (that is the size and the depth).
 */
static void salta_liste_scala(LettoreBit *l, int quante)
{
	for (int i = 0; i < quante && !l->finito; i++) {
		if (!lb_bit(l, 1))
			continue;
		int misura = (i < 6) ? 16 : 64;
		int ultimo = 8, prossimo = 8;
		for (int j = 0; j < misura && !l->finito; j++) {
			if (prossimo)
				prossimo = (ultimo + lb_se(l) + 256) % 256;
			ultimo = prossimo ? prossimo : ultimo;
		}
	}
}

/*
 * ⭐ The H.264 SPS — and it serves the same two purposes as the HEVC SPS: the
 *    REAL depth (the second E2 witness) and the LEVEL, which ends up
 *    in the `avc1.<profile><constraints><level>` string the browser receives.
 *
 * ⛔ And the size is read down to the CROPPING.  Without it, a 1588x914 canvas (not
 *    a multiple of 16) would read as 1600x928 — that is the witness would accuse
 *    a correct stream of the wrong size, which is the false red of `LEZIONI.md`
 *    §1.2.  ⚠ And the cropping units depend on the subsampling: 4:2:0
 *    counts two pixels per unit horizontally and two vertically.
 */
static bool leggi_sps_h264(const uint8_t *nal, size_t byte, CodificatoreConfessione *c,
                           PosizioneCornice *dove)
{
	uint8_t *rbsp;
	size_t n;
	LettoreBit l;
	uint32_t profilo, livello, vincoli, chroma = 1, largh_mb, alt_mapunit;
	uint32_t sotto_l = 2, sotto_a = 2;
	uint32_t taglio_sx = 0, taglio_dx = 0, taglio_su = 0, taglio_giu = 0;
	int solo_fotogrammi;
	size_t bit_flag;

	if (byte < 5)
		return false;
	rbsp = malloc(byte);
	if (!rbsp)
		return false;
	/* ⛔ The NAL header byte is skipped BEFORE removing the emulation:
	 *    it is not part of the RBSP, and counting it would shift every bit by eight. */
	n = togli_emulazione(nal + 1, byte - 1, rbsp, byte);
	lb_apri(&l, rbsp, n);

	profilo = lb_bit(&l, 8);
	/* ⛔⭐ THE CONSTRAINTS ARE NO LONGER THROWN AWAY — 23 Aug 2026.  Here there was a
	 *     `(void)`, and the byte ended up in nothing: it is the **CC** of
	 *     `avc1.PPCCLL`, that is exactly one third of the string the browser
	 *     passes to `configure()`.  ⚠ Throwing it away was the reason why that
	 *     string, under H.264, could not even be composed. */
	vincoli = lb_bit(&l, 8);     /* constraint_set*_flag + the reserved bits */
	livello = lb_bit(&l, 8);
	(void) lb_ue(&l);            /* seq_parameter_set_id */

	/* ⚠ Only the "high" profiles carry the chroma format and the depth: on
	 *   Baseline/Main they are NOT there, and reading them would shift all the rest.  It is
	 *   the standard's list (7.3.2.1.1), written out in full on purpose. */
	if (profilo == 100 || profilo == 110 || profilo == 122 || profilo == 244 || profilo == 44
	    || profilo == 83 || profilo == 86 || profilo == 118 || profilo == 128 || profilo == 138
	    || profilo == 139 || profilo == 134 || profilo == 135) {
		chroma = lb_ue(&l);
		if (chroma == 3)
			(void) lb_bit(&l, 1);          /* separate_colour_plane_flag */
		c->profondita_flusso = 8 + (int) lb_ue(&l);   /* luma */
		(void) lb_ue(&l);                  /* chroma: read and not used */
		(void) lb_bit(&l, 1);              /* qpprime_y_zero_transform_bypass */
		if (lb_bit(&l, 1))
			salta_liste_scala(&l, chroma == 3 ? 12 : 8);
	} else {
		/* ⛔ It is not "8 bits out of habit": on these profiles the standard
		 *    SAYS 8 and 4:2:0, so it is a fact that was read, not a default
		 *    value (`CODER.md` §3.10). */
		c->profondita_flusso = 8;
		chroma = 1;
	}
	if (chroma == 0) { sotto_l = 1; sotto_a = 1; }
	else if (chroma == 2) { sotto_l = 2; sotto_a = 1; }
	else if (chroma == 3) { sotto_l = 1; sotto_a = 1; }

	(void) lb_ue(&l);                      /* log2_max_frame_num_minus4 */
	{
		uint32_t tipo_ordine = lb_ue(&l);
		if (tipo_ordine == 0) {
			(void) lb_ue(&l);
		} else if (tipo_ordine == 1) {
			(void) lb_bit(&l, 1);
			(void) lb_se(&l);
			(void) lb_se(&l);
			uint32_t quanti = lb_ue(&l);
			for (uint32_t i = 0; i < quanti && !l.finito && i < 256; i++)
				(void) lb_se(&l);
		}
	}
	(void) lb_ue(&l);                      /* max_num_ref_frames */
	(void) lb_bit(&l, 1);                  /* gaps_in_frame_num_value_allowed */
	largh_mb = lb_ue(&l) + 1;
	alt_mapunit = lb_ue(&l) + 1;
	solo_fotogrammi = (int) lb_bit(&l, 1);
	if (!solo_fotogrammi)
		(void) lb_bit(&l, 1);              /* mb_adaptive_frame_field_flag */
	(void) lb_bit(&l, 1);                  /* direct_8x8_inference_flag */
	bit_flag = l.bit;
	if (lb_bit(&l, 1)) {                   /* frame_cropping_flag */
		taglio_sx = lb_ue(&l);
		taglio_dx = lb_ue(&l);
		taglio_su = lb_ue(&l);
		taglio_giu = lb_ue(&l);
		if (dove)
			dove->presente = true;
	} else if (dove) {
		dove->presente = false;
	}
	if (dove) {
		dove->bit_flag = bit_flag;
		dove->bit_dopo = l.bit;
		dove->sx = taglio_sx;
		dove->dx = taglio_dx;
		dove->su = taglio_su;
		dove->giu = taglio_giu;
	}
	free(rbsp);
	if (l.finito)
		return false;

	c->profilo_flusso = (int) profilo;
	c->livello_flusso = (int) livello;
	/* ⛔⭐⭐ THE STRING FOR THE DECODER, AND UNTIL 23 AUG 2026 UNDER
	 *      H.264 THIS FIELD STAYED EMPTY.
	 *
	 *      `leggi_sps_hevc()` composed it (`hev1.1.6.L150.B0`), `leggi_sps_
	 *      av1()` too (`av01.0.04M.10`), this function did NOT — it read profile,
	 *      constraints and level and never wrote them together.  ⚠ The log
	 *      said *"string for the decoder «»"* and the line looked like a
	 *      field that is not needed, instead of a defect.
	 *
	 * ⛔ THE FORMAT IS `avc1.PPCCLL`, THREE BYTES IN HEXADECIMAL — and it is not a
	 *    nuance: `PP` = `profile_idc` (100 = High ⇒ `64`), `CC` = the byte
	 *    of the `constraint_set*_flag` (⇒ `00` without constraints), `LL` = `level_idc`
	 *    (51 ⇒ `33`).  ⚠ Writing it in DECIMAL would give `avc1.100051`, which
	 *    no engine accepts — and the symptom would be "H.264 does not reach the
	 *    pixel" on a browser that decodes it perfectly well.
	 *
	 * ⭐ It is the same form that `src/pagina.html` composes on its side
	 *    (`stringhe_codec()`, `avc1.6400` + the level in hexadecimal): the two
	 *    ends line up, and if they diverge it shows here.  `[M]` with
	 *    `LIVELLO_DICHIARATO = "5.1"` the page asks for `avc1.640033`, and this
	 *    reader must say the same thing. */
	/* ⚠ LOWERCASE, and it is not taste: `src/pagina.html` composes its own with
	 *   `toString(16)`, which writes lowercase.  Two strings that must be
	 *   comparable by eye in the log do not differ by the case of
	 *   a letter. */
	snprintf(c->stringa_codec, sizeof(c->stringa_codec), "avc1.%02x%02x%02x",
	         profilo & 0xFFu, vincoli & 0xFFu, livello & 0xFFu);
	{
		uint32_t unita_l = (chroma == 0) ? 1 : sotto_l;
		uint32_t unita_a = (uint32_t) ((chroma == 0 ? 1 : sotto_a) * (2 - solo_fotogrammi));
		uint32_t larghezza = largh_mb * 16;
		uint32_t altezza = alt_mapunit * 16 * (uint32_t) (2 - solo_fotogrammi);
		uint32_t via_l = (taglio_sx + taglio_dx) * unita_l;
		uint32_t via_a = (taglio_su + taglio_giu) * unita_a;

		c->larghezza_flusso = (larghezza > via_l) ? larghezza - via_l : larghezza;
		c->altezza_flusso = (altezza > via_a) ? altezza - via_a : altezza;
	}
	return true;
}

/*
 * ⭐ The HEVC SPS, read in full down to the bit depth.
 *
 * ⛔ Why `ffprobe` is not enough: `ffprobe` is not inside the server.  And
 *    why `ctx->pix_fmt` is not enough: that is what we ASKED for.  The
 *    real depth is written in the SPS, and it is the one the browser's
 *    decoder will read.
 *
 * ⭐ And along the way out comes the **level**, which is needed for `RCP.md` §4.3
 *    (`video.livello`: the server MUST emit a stream of a level no
 *    higher than the one declared by the client, and **does not guess it**) and for the
 *    `hev1.2.4.L93.B0` string of `VideoDecoder.configure()`.
 */
static bool leggi_sps_hevc(const uint8_t *nal, size_t byte, CodificatoreConfessione *c,
                           PosizioneCornice *dove)
{
	if (byte < 4)
		return false;
	uint8_t *rbsp = malloc(byte);
	if (!rbsp)
		return false;
	size_t n = togli_emulazione(nal + 2, byte - 2, rbsp, byte); /* 2 = NAL header */

	LettoreBit l;
	lb_apri(&l, rbsp, n);
	lb_bit(&l, 4);                              /* sps_video_parameter_set_id */
	uint32_t max_sub = lb_bit(&l, 3);           /* sps_max_sub_layers_minus1 */
	lb_bit(&l, 1);                              /* sps_temporal_id_nesting_flag */

	/* profile_tier_level(1, max_sub) */
	uint32_t spazio = lb_bit(&l, 2);
	uint32_t tier = lb_bit(&l, 1);
	uint32_t profilo = lb_bit(&l, 5);
	uint32_t compat = lb_bit(&l, 32);
	uint8_t vincoli[6];
	for (int i = 0; i < 6; i++)
		vincoli[i] = (uint8_t) lb_bit(&l, 8); /* 48 bits: the source flags and the reserved ones */
	uint32_t livello = lb_bit(&l, 8);

	uint32_t prof_presente[8] = { 0 }, liv_presente[8] = { 0 };
	for (uint32_t i = 0; i < max_sub; i++) {
		prof_presente[i] = lb_bit(&l, 1);
		liv_presente[i] = lb_bit(&l, 1);
	}
	if (max_sub > 0)
		for (uint32_t i = max_sub; i < 8; i++)
			lb_bit(&l, 2); /* reserved_zero_2bits */
	for (uint32_t i = 0; i < max_sub; i++) {
		if (prof_presente[i]) {
			lb_bit(&l, 2); lb_bit(&l, 1); lb_bit(&l, 5);
			lb_bit(&l, 32);
			for (int k = 0; k < 6; k++)
				lb_bit(&l, 8);
		}
		if (liv_presente[i])
			lb_bit(&l, 8);
	}

	lb_ue(&l);                                  /* sps_seq_parameter_set_id */
	uint32_t croma = lb_ue(&l);                 /* chroma_format_idc */
	if (croma == 3)
		lb_bit(&l, 1);                          /* separate_colour_plane_flag */
	uint32_t larghezza = lb_ue(&l);
	uint32_t altezza = lb_ue(&l);
	uint32_t codificata_l = larghezza, codificata_a = altezza;
	/*
	 * ⛔⭐ THE CONFORMANCE WINDOW IS APPLIED — and until 13 Aug 2026 this
	 *     read SKIPPED it (four `lb_ue()` thrown away).
	 *
	 * ⚠ It had never been seen because `libx265` at 1920×1080 does not put one: 1080
	 *   is a multiple of 8 and fits without padding.  ⛔ `hevc_vaapi` **on AMD**
	 *   (radeonsi, navi21) encodes **1920×1088** and crops to 1080 with the
	 *   window — and the `forma_va_bene()` check refused EVERY frame
	 *   saying *"the stream declares 1920x1088 and the canvas is 1920x1080"*.
	 *
	 * ⇒ ⭐ The defect was the READER's, not the encoder's, and it was seen only
	 *   because the check was there.  ⚠ The two sizes stay TWO — what is
	 *   encoded and what is shown — and both are written: one day the
	 *   difference will cost bandwidth, and then we will want to know it is there.
	 *
	 * `[S]` H.265 §7.4.3.2: the offsets are in chroma units, that is they must be
	 * multiplied by SubWidthC/SubHeightC.
	 */
	size_t bit_flag = l.bit;
	if (dove) {
		memset(dove, 0, sizeof *dove);
		dove->bit_flag = bit_flag;
	}
	if (lb_bit(&l, 1)) {                        /* conformance_window_flag */
		uint32_t sinistra = lb_ue(&l), destra = lb_ue(&l);
		uint32_t sopra = lb_ue(&l), sotto = lb_ue(&l);
		uint32_t sub_l = (croma == 1 || croma == 2) ? 2 : 1;
		uint32_t sub_a = (croma == 1) ? 2 : 1;
		uint32_t taglio_l = sub_l * (sinistra + destra);
		uint32_t taglio_a = sub_a * (sopra + sotto);
		if (dove) {
			dove->presente = true;
			dove->sx = sinistra;
			dove->dx = destra;
			dove->su = sopra;
			dove->giu = sotto;
		}
		/* ⚠ A crop bigger than the picture is not subtracted: it is left alone and
		 *   the caller will see a size that does not match, which is better than a
		 *   number that goes below zero and becomes huge. */
		if (taglio_l < larghezza)
			larghezza -= taglio_l;
		if (taglio_a < altezza)
			altezza -= taglio_a;
	}
	if (dove)
		dove->bit_dopo = l.bit;
	uint32_t bit_luma = lb_ue(&l) + 8;
	uint32_t bit_croma = lb_ue(&l) + 8;
	free(rbsp);

	if (l.finito)
		return false;

	c->profondita_flusso = (int) (bit_luma < bit_croma ? bit_luma : bit_croma);
	c->profilo_flusso = (int) profilo;
	c->livello_flusso = (int) livello;
	c->tier_alto = tier != 0;
	c->larghezza_flusso = larghezza;
	c->altezza_flusso = altezza;
	c->larghezza_codificata = codificata_l;
	c->altezza_codificata = codificata_a;
	c->croma_flusso = (int) croma;

	/* ⭐ The string for `VideoDecoder.configure()`, built from the real bytes.
	 *   ⛔ `hev1` and not `hvc1`: the parameter sets travel in band.  ⚠ And `[M]`
	 *      F2.5 measured that **the prefix does not matter**: Chromium decides from the
	 *      presence of the `description`, not from the prefix.  `hev1` is written
	 *      anyway, because it is the one that describes the truth of the stream. */
	char vincoli_testo[24] = { 0 };
	int ultimo = -1;
	for (int i = 0; i < 6; i++)
		if (vincoli[i])
			ultimo = i;
	for (int i = 0; i <= ultimo; i++) {
		char pezzo[8];
		snprintf(pezzo, sizeof(pezzo), ".%02X", vincoli[i]);
		strncat(vincoli_testo, pezzo, sizeof(vincoli_testo) - strlen(vincoli_testo) - 1);
	}
	char spazio_testo[2] = { 0 };
	if (spazio > 0)
		spazio_testo[0] = (char) ('A' + spazio - 1);
	snprintf(c->stringa_codec, sizeof(c->stringa_codec), "hev1.%s%u.%X.%c%u%s",
	         spazio_testo, profilo, rovescia32(compat), tier ? 'H' : 'L', livello,
	         vincoli_testo);
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * AV1 — the OBU temporal units
 *
 * ⚠ Here there is no `hvcC` to defend against: AV1 "takes the temporal
 *   units as they are" (`DECISIONI.md` §1.13).  ⛔ But the half that gets
 *   forgotten is identical: the **sequence header OBU** must sit in front of every
 *   keyframe, or a client that connects later receives a bare key —
 *   the same black screen with the frames arriving.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define OBU_SEQUENCE_HEADER 1
#define OBU_TEMPORAL_DELIMITER 2
#define OBU_FRAME_HEADER 3
#define OBU_FRAME 6

typedef struct {
	bool ha_sequenza;
	bool ha_chiave;
	bool sequenza_prima_della_chiave;
	bool primo_fotogramma_e_chiave;
	size_t seq_offset, seq_byte;
} FormaObu;

static uint64_t leggi_leb128(const uint8_t *d, size_t byte, size_t *dove)
{
	uint64_t v = 0;
	for (int i = 0; i < 8 && *dove < byte; i++) {
		uint8_t b = d[(*dove)++];
		v |= (uint64_t) (b & 0x7F) << (i * 7);
		if (!(b & 0x80))
			break;
	}
	return v;
}

static void obu_leggi(const uint8_t *d, size_t byte, FormaObu *f)
{
	memset(f, 0, sizeof(*f));
	bool visto_fotogramma = false, seq_in_corso = false;
	size_t i = 0;
	while (i < byte) {
		size_t inizio = i;
		uint8_t testa = d[i++];
		int tipo = (testa >> 3) & 0xF;
		bool estensione = (testa >> 2) & 1;
		bool ha_taglia = (testa >> 1) & 1;
		if (estensione && i < byte)
			i++;
		uint64_t taglia;
		if (ha_taglia)
			taglia = leggi_leb128(d, byte, &i);
		else
			taglia = byte - i; /* ⚠ without a size field the OBU runs to the end of the buffer */
		if (i + taglia > byte)
			taglia = byte - i;

		if (tipo == OBU_SEQUENCE_HEADER) {
			f->ha_sequenza = true;
			seq_in_corso = true;
			if (!f->seq_byte) {
				f->seq_offset = i;
				f->seq_byte = (size_t) taglia;
			}
		} else if (tipo == OBU_FRAME || tipo == OBU_FRAME_HEADER) {
			LettoreBit l;
			lb_apri(&l, d + i, (size_t) taglia);
			bool chiave = false;
			if (lb_bit(&l, 1) == 0)                 /* show_existing_frame */
				chiave = (lb_bit(&l, 2) == 0);      /* frame_type: 0 = KEY_FRAME */
			if (!visto_fotogramma) {
				visto_fotogramma = true;
				f->primo_fotogramma_e_chiave = chiave;
			}
			if (chiave) {
				f->ha_chiave = true;
				if (seq_in_corso)
					f->sequenza_prima_della_chiave = true;
			}
			seq_in_corso = false;
		}
		i += (size_t) taglia;
		if (i <= inizio)
			break; /* ⛔ a zero-size OBU would stop the loop here instead of never */
	}
}

/* The sequence header OBU, down to the bit depth.  Follows AV1 §5.5. */
static bool leggi_sequenza_av1(const uint8_t *d, size_t byte, CodificatoreConfessione *c)
{
	LettoreBit l;
	lb_apri(&l, d, byte);
	uint32_t profilo = lb_bit(&l, 3);
	lb_bit(&l, 1); /* still_picture */
	uint32_t ridotta = lb_bit(&l, 1);
	uint32_t livello = 0, tier = 0;
	uint32_t modello_decodifica = 0, ritardo_iniziale = 0;

	if (ridotta) {
		livello = lb_bit(&l, 5);
	} else {
		if (lb_bit(&l, 1)) {              /* timing_info_present_flag */
			lb_bit(&l, 32); lb_bit(&l, 32);
			if (lb_bit(&l, 1) == 0) {     /* equal_picture_interval */
				/* uvlc(): nothing to keep */
				int zeri = 0;
				while (!l.finito && lb_bit(&l, 1) == 0 && zeri < 32)
					zeri++;
				if (zeri && zeri < 32)
					lb_bit(&l, zeri);
			}
			modello_decodifica = lb_bit(&l, 1);
			if (modello_decodifica) {
				lb_bit(&l, 5); lb_bit(&l, 32); lb_bit(&l, 5); lb_bit(&l, 5);
			}
		}
		ritardo_iniziale = lb_bit(&l, 1);
		uint32_t quanti = lb_bit(&l, 5);
		for (uint32_t k = 0; k <= quanti; k++) {
			lb_bit(&l, 12);               /* operating_point_idc */
			uint32_t liv = lb_bit(&l, 5);
			uint32_t ti = 0;
			if (liv > 7)
				ti = lb_bit(&l, 1);
			if (k == 0) {
				livello = liv;
				tier = ti;
			}
			if (modello_decodifica && lb_bit(&l, 1)) {
				/* operating_parameters_info: two delays and a flag.  ⚠ The
				 * length depends on buffer_delay_length, which we do not
				 * keep here: if this branch lit up, the read
				 * would become unreliable and the caller sees it from
				 * `letto_dal_flusso = false`. */
				return false;
			}
			if (ritardo_iniziale && lb_bit(&l, 1))
				lb_bit(&l, 4);
		}
	}
	uint32_t bit_l = lb_bit(&l, 4) + 1;
	uint32_t bit_a = lb_bit(&l, 4) + 1;
	uint32_t larghezza = lb_bit(&l, (int) bit_l) + 1;
	uint32_t altezza = lb_bit(&l, (int) bit_a) + 1;

	if (!ridotta && lb_bit(&l, 1)) { /* frame_id_numbers_present_flag */
		lb_bit(&l, 4);
		lb_bit(&l, 3);
	}
	lb_bit(&l, 1); /* use_128x128_superblock */
	lb_bit(&l, 1); /* enable_filter_intra */
	lb_bit(&l, 1); /* enable_intra_edge_filter */
	if (!ridotta) {
		lb_bit(&l, 1); /* enable_interintra_compound */
		lb_bit(&l, 1); /* enable_masked_compound */
		lb_bit(&l, 1); /* enable_warped_motion */
		lb_bit(&l, 1); /* enable_dual_filter */
		uint32_t ordine = lb_bit(&l, 1);
		if (ordine) {
			lb_bit(&l, 1); /* enable_jnt_comp */
			lb_bit(&l, 1); /* enable_ref_frame_mvs */
		}
		uint32_t forza = 2;
		if (lb_bit(&l, 1) == 0)          /* seq_choose_screen_content_tools */
			forza = lb_bit(&l, 1);
		if (forza > 0 && lb_bit(&l, 1) == 0)
			lb_bit(&l, 1);               /* seq_force_integer_mv */
		if (ordine)
			lb_bit(&l, 3);               /* order_hint_bits_minus_1 */
	}
	lb_bit(&l, 1); /* enable_superres */
	lb_bit(&l, 1); /* enable_cdef */
	lb_bit(&l, 1); /* enable_restoration */

	/* color_config() */
	uint32_t alto = lb_bit(&l, 1);
	int profondita;
	if (profilo == 2 && alto)
		profondita = lb_bit(&l, 1) ? 12 : 10;
	else
		profondita = alto ? 10 : 8;

	if (l.finito)
		return false;

	c->profondita_flusso = profondita;
	c->profilo_flusso = (int) profilo;
	c->livello_flusso = (int) livello;
	c->tier_alto = tier != 0;
	c->larghezza_flusso = larghezza;
	c->altezza_flusso = altezza;
	c->croma_flusso = 1; /* ⚠ the two formats SVT-AV1 accepts are 4:2:0 */

	/* ⚠ `seq_level_idx = 4` is NOT "level 4": it is 3.0 — the string takes
	 *   the INDEX (`DECISIONI.md` §1.13). */
	snprintf(c->stringa_codec, sizeof(c->stringa_codec), "av01.%u.%02u%c.%02d",
	         profilo, livello, tier ? 'H' : 'M', profondita);
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════ */

/* ⛔ How many DMA-BUF imports are kept in the cache.  ⚠ The number is not one of
 *    convenience: the producer recycles `[M]` **four** buffers (`DECISIONI.md`
 *    §2.3-ter) and on the card route we ask it for **six**, because
 *    holding back takes two.  Eight covers all cases with margin, and when the
 *    cache is full we start over instead of evicting at random: a
 *    wrong policy on eight entries would cost more lines than it gives back. */
#define IMPORTATE_MAX 8

/* ⛔ How many INPUT surfaces the card's store keeps.  With the wait
 *    on every frame one would be enough; four are kept so as not to
 *    rewrite the one the VPP has just filled while the driver is
 *    still reading it, on a driver that kept one round in the pipe. */
#define SUPERFICI_PRONTE 4


/* ⛔ The number lives in ONE place only, with the measurement next to it in `codificatore.h`.
 *    ⚠ It is not a multiple chosen out of caution: it is the boundary measured to the pixel
 *    between 1552 (which reads) and 1544 (which does not). */
#define ALLINEAMENTO_SCHEDA 64u


/* ⭐ PHASE 19 — the card route.  `NESSUNA` in a request means
 *    "by capability" (`h264_scheda`); in an encoder that was born it is always one
 *    of the two. */
typedef enum { STRADA_NESSUNA = 0, STRADA_VAAPI, STRADA_VULKAN } Strada;

static const char *nome_strada(Strada s)
{
	return s == STRADA_VULKAN ? "vulkan" : s == STRADA_VAAPI ? "vaapi" : "";
}

struct Codificatore {
	CodificatoreRichiesta richiesta;
	/* ⛔ The component name is a REMOTIX LABEL, and it is the one
	 *    OPENED: `h264_vulkan`/`hevc_vulkan` or `h264_vaapi`/`hevc_vaapi`.  Whoever
	 *    asked for `h264_scheda` (by capability) reads here which of the two
	 *    came out.  `figlio.c` and `--prova-codifica` write it to the log and
	 *    to the JSON, and the installer reads the outcome, not the name. */
	char nome_componente[64];
	/* ⭐ The route REQUESTED (NESSUNA = by capability) and the one OPENED. */
	Strada strada_chiesta;
	Strada strada;
	/* ⭐ The STAGING buffer of the from-memory route IN HARDWARE: the frame
	 *    converted on the CPU (NV12 or P010, `colori709.c`) before being uploaded to the
	 *    card.  Empty on the zero copy (the frame is already on the card). */
	uint8_t *appoggio;
	size_t appoggio_byte;
	CodificatoreConfessione conf;
	/* ⭐ The entrypoint CHOSEN in `apri_dispositivo()` after reading it from the
	 *    driver: it is what is asked of vadiretta and what the reread is compared
	 *    against.  ⛔ Not `richiesta.potenza`: with
	 *    `LA_DICHIARATA` the request alone does not say which of the two. */
	bool bassa_potenza_scelta;
	/* ⚠ 400 and not 160: it holds the VA vendor in full — "Intel iHD
	 *   driver for Intel(R) Gen Graphics - 25.2.3 ()" is already 53 bytes.  A name
	 *   truncated in the log removes precisely the piece that says WHICH machine made
	 *   the number. */
	char nome[400];

	/* ───────────────────────────────────────────────────────────────────────
	 * ⭐ THE CARD ROUTE.  ⛔ Since phase 19 `hardware` is always true
	 *    in an encoder that was born: `codificatore_nuovo()` refuses every name that
	 *    does not belong to the card.  The field stays because `codificatore_libera()`
	 *    can run on a half-built encoder (the device not yet
	 *    open), and because the Vulkan route will be grafted alongside.
	 */
	bool hardware;
	VaDispositivo dispositivo;    /* the open node: display and vendor */
	VAProfile profilo_va;         /* the pair chosen and VERIFIED in apri_dispositivo() */
	VAEntrypoint entrypoint_va;
	VaDiretta *va;                /* the encoder on the card */
	VASurfaceID superficie_pronta; /* the input filled by prepara_*, to be encoded */
	/* ⭐ PHASE 19 — the VULKAN VIDEO route: the device (instance, card chosen
	 *    from the node, queues) lives as long as the encoder, like `dispositivo` above;
	 *    the encoder (`vk`) is closed and reopened with the context, like
	 *    `va`.  ⚠ The cache of imported DMA-BUFs sits INSIDE `vk` (one per
	 *    session): on every reopening it is reimported — it costs one import per
	 *    buffer, and the producer recycles four. */
	VulkanVideoDispositivo *vk_dispositivo;
	VulkanVideo *vk;
	VulkanVideoCapacita vk_capacita; /* read in apri_dispositivo(), for the choice */

	/* ───────────────────────────────────────────────────────────────────────
	 * ⭐⭐⭐ ZERO COPY — the three things needed, and nothing else
	 *
	 *   1. the VPP CONTEXT: the RGB → NV12 conversion done by the GPU, which
	 *      takes the place of the CPU conversion **and** of the upload
	 *      together.  ⛔ It lives on the DEVICE and not on the encoder's
	 *      context: `abbassa_qualita()` closes and reopens the encoder
	 *      three times in a row for a key above the ceiling, and redoing the VPP on
	 *      every round would be work done for nothing;
	 *   2. the CACHE of imports: `vaCreateSurfaces` on a DMA-BUF is not
	 *      free, and the producer always recycles the same few buffers.  ⇒ We
	 *      import once per buffer, not once per frame;
	 *   3. the GENERATION the cache was born with.  ⛔ Without it, after a
	 *      renegotiation VA-API would be given a surface pointing to a
	 *      freed buffer: descriptor numbers are recycled, and the symptom
	 *      would be **an old picture** with no error at all.
	 */
	VAConfigID vpp_configurazione;
	VAContextID vpp_contesto;
	bool vpp_aperto;
	uint32_t vpp_l, vpp_a;        /* the size the VPP was opened for */
	struct {
		int fd;
		uint32_t l, a, stride, offset, formato_drm;
		uint64_t modificatore;
		VASurfaceID superficie;
	} importate[IMPORTATE_MAX];
	unsigned quante_importate;
	uint64_t generazione_cache;
	bool cache_nata;
	bool detto_copia_zero;        /* the first-time line, once only */

	bool prossimo_chiave;         /* ⛔ the next one is a REAL key */
	bool prima_codifica_fatta;
	bool svuotato;                /* ⚠ it was put into drain: it must be reopened */
	/* ⭐ THE FRAME (D-023, phase 16): the conformance window rewritten
	 *    in the SPS when the driver does not write it there.  ⭐ Since phase 18
	 *    `cornice_al_suo_posto()` rewrites it with the bits.  It is decided on the first SPS of
	 *    each context. */
	bool cornice_decisa;
	bool cornice_attiva;
	uint32_t cornice_dx, cornice_dy; /* columns and rows to crop on the right and at the bottom */
	/* ⭐ THE BYTES THAT ARE DELIVERED — ours, for both routes.  The
	 *    encoder (card or software) produces them in its buffer; here they are
	 *    copied (`[M]` a 4K key is ~1 MB: tens of µs) so that the
	 *    frame can rewrite them and so that `fuori->dati` does not depend on the
	 *    life of the encoder's buffer — the defect of 23 Aug 2026. */
	uint8_t *uscita;
	size_t uscita_capacita, uscita_byte;
	int qualita_corrente;         /* CRF in force, after any re-encodings */
	ModoQualita modo_corrente;
	/* ⭐ THE CLIMB (phase 9).  ⛔ The floor does NOT live here: it is `richiesta.qualita`,
	 *    which `codificatore_nuovo()` keeps intact.  A second field with the
	 *    same number inside would be the E2 form — two measurements under the same
	 *    label, and the day they diverge no bench notices. */
	int qualita_fallita;          /* the rung on which the ceiling BIT; 0 = never */
	uint32_t sotto_margine;       /* frames in a row comfortably below the ceiling */
	uint32_t risalita_attesa;     /* how many are needed NOW: doubles on every relapse */
	bool risalito_da_poco;        /* to recognise the relapse, and only for that */
	/* ⭐⭐⭐ THE THIRD BITRATE WITNESS — THE BYTES, and it is the only one that would have
	 *      caught R31.  See the bandwidth ceiling box: the first witness
	 *      says the mode **exists**, the second that the driver
	 *      **kept** it, and in v1 they would **both have been green** while
	 *      CBR came out.  ⛔ Only these four fields say it. */
	uint64_t banda_t0_us;         /* when the current window started */
	uint64_t banda_byte;          /* how many came out inside the window */
	uint32_t banda_fotogrammi;
	uint32_t banda_massimo;       /* the biggest: it is the peak, not the average */
	int64_t numero;               /* the pts, which here is the frame counter */
	bool pacchetto_in_mano;       /* `uscita` is in the caller's hands until rilascia() */
};

/* ⚠ Declared here and defined with the rest of the zero copy, much further down:
 *   `codificatore_libera()` sits in between and must call them.  ⛔ Moving their
 *   definition up here would separate the GPU conversion from its
 *   box, which is the place where it is explained. */
static void butta_le_importate(Codificatore *c, const char *perche);
static void chiudi_vpp(Codificatore *c);
/* ⭐ Phase 19: the bytes in `c->uscita` are common to both routes, and the
 *    Vulkan round (`codifica_vulkan`, with the zero copy box) puts them there. */
static bool metti_in_uscita(Codificatore *c, const uint8_t *dati, size_t byte);

static uint64_t adesso_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t) t.tv_sec * 1000000u + (uint64_t) t.tv_nsec / 1000u;
}

static void di(char *dove, size_t quanto, const char *fmt, ...)
{
	if (!dove || !quanto)
		return;
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(dove, quanto, fmt, ap);
	va_end(ap);
}

/* ⛔ The name for the log lives in ONE place only: until 20 Aug 2026 it was
 *    a `? :` repeated on six lines, and with the third codec each would have said
 *    "AV1" of an H.264 stream — six lies to fix one by one. */
static const char *nome_codec(CodecVideo codec)
{
	switch (codec) {
	case CODIFICATORE_HEVC:
		return "HEVC";
	case CODIFICATORE_H264:
		return "H.264";
	case CODIFICATORE_AV1:
		return "AV1";
	default:
		return "unknown codec";
	}
}

/* ⚠ The name of the QUANTITY, not of the value: CRF and QP are not the same thing
 *   (see `ModoQualita`), and a log line that said only the number
 *   would put two different measurements under the same label. */
static const char *nome_modo(ModoQualita modo)
{
	switch (modo) {
	case CODIFICATORE_QUALITA_LOSSLESS:
		return "lossless";
	case CODIFICATORE_QUALITA_QP:
		return "QP";
	case CODIFICATORE_QUALITA_CRF:
		return "CRF";
	default:
		return "unknown mode";
	}
}

/*
 * ⛔ "Is it in hardware?" is ASKED OF THE COMPONENT, not read from the name.
 *
 * ⚠ A `strstr(nome, "_vaapi")` would be the same thing written badly: the day
 *   `hevc_qsv` or `hevc_vulkan` were tried the line would say "software" of
 *   a hardware encoder, and the symptom would be swscale converting
 *   to a format the component does not accept — that is an error that names
 *   neither the GPU nor the name.  ⇒ We look at what it DECLARES: a
 *   hardware encoder accepts a surface format, not a pixel format.
 */
/*
 * ⭐ PHASE 18: the answer is given by the NAMES that REMOTIX reserves for the card.
 *    ⚠ It is not the `strstr(nome, "_vaapi")` that the note above forbade: that one
 *    guessed among the components of another library; these are OUR
 *    labels, and a seventh (`hevc_qsv`) does not exist here and does not open —
 *    it fails saying so.
 * ⭐ PHASE 19: the names are six (`codificatore.h`): `*_scheda` = the route is
 *    chosen by capability, `*_vulkan` and `*_vaapi` = that one and nothing else.
 */
static bool componente_della_scheda(const char *nome, CodecVideo *codec, Strada *strada)
{
	static const struct {
		const char *nome;
		CodecVideo codec;
		Strada strada;
	} nomi[] = {
		{ "h264_scheda", CODIFICATORE_H264, STRADA_NESSUNA },
		{ "hevc_scheda", CODIFICATORE_HEVC, STRADA_NESSUNA },
		{ "h264_vulkan", CODIFICATORE_H264, STRADA_VULKAN },
		{ "hevc_vulkan", CODIFICATORE_HEVC, STRADA_VULKAN },
		{ "h264_vaapi", CODIFICATORE_H264, STRADA_VAAPI },
		{ "hevc_vaapi", CODIFICATORE_HEVC, STRADA_VAAPI },
	};
	for (size_t i = 0; i < sizeof nomi / sizeof nomi[0]; i++)
		if (strcmp(nome, nomi[i].nome) == 0) {
			if (codec)
				*codec = nomi[i].codec;
			if (strada)
				*strada = nomi[i].strada;
			return true;
		}
	return false;
}

/* The Vulkan bitrate modes, by name (the `VULKANVIDEO_RC_*` mask). */
static void nomi_modi_vulkan(unsigned maschera, char *fuori, size_t byte)
{
	snprintf(fuori, byte, "%s%s%s", (maschera & VULKANVIDEO_RC_CQP) ? "CQP " : "",
	         (maschera & VULKANVIDEO_RC_CBR) ? "CBR " : "",
	         (maschera & VULKANVIDEO_RC_VBR) ? "VBR " : "");
	if (!fuori[0])
		snprintf(fuori, byte, "none");
}

/*
 * ⭐⭐ PHASE 19 — IS VULKAN VIDEO SUITABLE FOR THIS REQUEST?  We ask the
 *     node's card (`vulkanvideo_capacita`: it opens and closes everything by itself)
 *     and compare with what the request wants: the codec at that
 *     depth, the canvas within the limits, the bitrate mode the ceiling
 *     asks for, the input format (the shader takes RGB: the bench that comes in
 *     as yuv420p10le stays on VA-API).
 *
 * ⛔ THREE OUTCOMES AND NOT TWO here too: "suitable", "not suitable, and why" (we go to
 *    VA-API if the route is by capability), and "asked for by name and not suitable",
 *    which is a refusal.  ⚠ `perche` is always written: the log line
 *    must say WHY on this machine the other route was taken.
 */
static bool vulkan_adatta(Codificatore *c, char *perche, size_t perche_byte)
{
	const CodificatoreRichiesta *r = &c->richiesta;
	VulkanVideoCapacita *cap = &c->vk_capacita;
	const VulkanVideoProfiloCapacita *p;
	char errore[256] = { 0 };
	const char *profilo;

	if (r->formato == CODIFICATORE_PIXEL_YUV420P10LE) {
		di(perche, perche_byte,
		   "the input is yuv420p10le (the bench): the Vulkan route takes RGB and converts it "
		   "with the shader, not planes already converted");
		return false;
	}
	if (r->codec == CODIFICATORE_H264 && r->profondita != 8) {
		di(perche, perche_byte, "H.264 at %d bits: in Vulkan only High at 8 bits is opened", r->profondita);
		return false;
	}
	if (r->codec != CODIFICATORE_H264 && r->codec != CODIFICATORE_HEVC) {
		di(perche, perche_byte, "the codec %s is not encoded on the card", nome_codec(r->codec));
		return false;
	}
	if (!vulkanvideo_capacita(r->nodo_rendering, cap, errore, sizeof errore)) {
		di(perche, perche_byte, "no Vulkan device with the encode queue on «%s»: %s",
		   r->nodo_rendering, cap->perche[0] ? cap->perche : errore);
		return false;
	}
	if (r->codec == CODIFICATORE_H264) {
		p = &cap->h264;
		profilo = "H.264 High";
	} else if (r->profondita == 10) {
		p = &cap->hevc10;
		profilo = "HEVC Main 10";
	} else {
		p = &cap->hevc;
		profilo = "HEVC Main";
	}
	if (!p->codifica) {
		di(perche, perche_byte, "«%s» (%s) in Vulkan does NOT declare %s encoding", cap->nome_scheda,
		   cap->driver, profilo);
		return false;
	}
	if (r->larghezza > p->misura_massima_l || r->altezza > p->misura_massima_a
	    || r->larghezza < p->misura_minima_l || r->altezza < p->misura_minima_a) {
		di(perche, perche_byte,
		   "«%s» in Vulkan encodes %s between %ux%u and %ux%u, and the canvas is %ux%u", cap->nome_scheda,
		   profilo, p->misura_minima_l, p->misura_minima_a, p->misura_massima_l,
		   p->misura_massima_a, r->larghezza, r->altezza);
		return false;
	}
	/* ⛔ R31 from the Vulkan end: the mode is asked for by name and we check that the
	 *    card DECLARES it — with the ceiling VBR is needed, without it CQP. */
	if (tetto_pavimento_mbit && !(p->modi_bitrate & VULKANVIDEO_RC_VBR)) {
		char modi[48];
		nomi_modi_vulkan(p->modi_bitrate, modi, sizeof modi);
		di(perche, perche_byte, "the bandwidth ceiling wants VBR and «%s» in Vulkan declares [%s]",
		   cap->nome_scheda, modi);
		return false;
	}
	if (!tetto_pavimento_mbit && !(p->modi_bitrate & VULKANVIDEO_RC_CQP)) {
		char modi[48];
		nomi_modi_vulkan(p->modi_bitrate, modi, sizeof modi);
		di(perche, perche_byte, "constant QP wants CQP and «%s» in Vulkan declares [%s]",
		   cap->nome_scheda, modi);
		return false;
	}
	if (p->qp_massimo > 0 && (c->qualita_corrente < p->qp_minimo || c->qualita_corrente > p->qp_massimo)) {
		di(perche, perche_byte, "QP %d outside what «%s» declares in Vulkan (%d..%d)",
		   c->qualita_corrente, cap->nome_scheda, p->qp_minimo, p->qp_massimo);
		return false;
	}
	/* the API version as Vulkan packs it (variant:3, major:7,
	 * minor:10, patch:12): unpacked here so as not to include `vulkan.h` */
	di(perche, perche_byte, "«%s» (%s, API %u.%u) declares %s up to %ux%u, DMA-BUF %s",
	   cap->nome_scheda, cap->driver, (cap->versione_api >> 22) & 0x7fu,
	   (cap->versione_api >> 12) & 0x3ffu, profilo, p->misura_massima_l, p->misura_massima_a,
	   cap->dmabuf ? "yes" : "NO");
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐ THE GPU — AND IT OPENS ON A DECLARED NODE, WITH A DECLARED ENTRYPOINT
 *
 * ⛔ The two things this block does NOT do, and they are the two that would cost:
 *
 *    1. **it does not choose the node**.  `[M]` 13 Aug 2026 the two nodes of the
 *       test machine are from two different vendors (Intel iHD on
 *       `renderD128`, AMD radeonsi on `renderD129`) and with two different
 *       entrypoints.  Code that opened "the first one there is" would measure a
 *       random machine, and the number would not say which;
 *    2. **it does not trust having asked**.  Between "I passed `low_power=1` to
 *       libavcodec" and "the driver has that entrypoint" there is the same distance
 *       as between `-svtav1-params lossless=1` and a lossless stream — that is
 *       an error print and an exit 0 (`[M]` 12 Aug).  ⇒ The pair
 *       (profile, entrypoint) is read from the driver with
 *       `vaQueryConfigEntrypoints` **before** opening.
 * ═══════════════════════════════════════════════════════════════════════════ */

static VAProfile profilo_va(CodecVideo codec, int profondita)
{
	if (codec == CODIFICATORE_HEVC)
		return profondita == 10 ? VAProfileHEVCMain10 : VAProfileHEVCMain;
	/* ⛔ H.264 HERE IS 8 BIT AND THAT IS ALL, and it is declared instead of tried:
	 *    `High10` exists in the standard but `[M]` `vainfo` on this machine
	 *    lists `VAProfileH264High` and not the 10 bit — and whoever asked for 10 bits
	 *    would get `VAProfileNone`, that is the software fallback, with the
	 *    same name and a rate ten times worse (the E2 form). */
	if (codec == CODIFICATORE_H264)
		return profondita == 10 ? VAProfileNone : VAProfileH264High;
	return VAProfileNone;
}

/*
 * ⛔ THREE OUTCOMES, NOT TWO: `it is there`, `it is not there`, `I could not look`.
 * `LEZIONI.md` §1.9 rule 1 — "empty" and "forbidden" look the same.
 */
typedef enum { EP_C_E, EP_NON_C_E, EP_NON_GUARDATO } EsitoEntrypoint;

static EsitoEntrypoint entrypoint_c_e(VADisplay d, VAProfile p, VAEntrypoint voluto,
                                      char *visti, size_t visti_byte)
{
	int massimo = vaMaxNumEntrypoints(d);
	if (massimo <= 0)
		return EP_NON_GUARDATO;
	VAEntrypoint *elenco = calloc((size_t) massimo, sizeof(*elenco));
	if (!elenco)
		return EP_NON_GUARDATO;
	int quanti = 0;
	VAStatus st = vaQueryConfigEntrypoints(d, p, elenco, &quanti);
	if (st != VA_STATUS_SUCCESS) {
		free(elenco);
		return EP_NON_GUARDATO;
	}
	EsitoEntrypoint esito = EP_NON_C_E;
	if (visti && visti_byte)
		visti[0] = 0;
	for (int i = 0; i < quanti; i++) {
		if (visti && visti_byte) {
			char pezzo[24];
			snprintf(pezzo, sizeof(pezzo), "%s%d", i ? "," : "", (int) elenco[i]);
			strncat(visti, pezzo, visti_byte - strlen(visti) - 1);
		}
		if (elenco[i] == voluto)
			esito = EP_C_E;
	}
	free(elenco);
	return esito;
}

/*
 * Opens the VA-API device on the declared node, reads its VENDOR, and
 * checks that (profile, entrypoint) really exists before opening.
 */
static int apri_dispositivo(Codificatore *c, char *errore, size_t errore_byte)
{
	const CodificatoreRichiesta *r = &c->richiesta;

	if (!r->nodo_rendering || !r->nodo_rendering[0]) {
		di(errore, errore_byte,
		   "«%s» is a HARDWARE encoder and no render node "
		   "was declared: ⛔ none is guessed — on this machine the two "
		   "nodes are from two different vendors [M]", c->nome_componente);
		return -1;
	}
	snprintf(c->conf.nodo, sizeof(c->conf.nodo), "%s", r->nodo_rendering);

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⭐⭐ PHASE 19 — VULKAN VIDEO FIRST, IF THE CARD OFFERS IT FOR THIS CODEC
	 *
	 * The route is chosen by CAPABILITY (`DECISIONI.md` §10.27): we ask
	 * the node's card what it can do in Vulkan and, if it can do what
	 * the request wants, we take that.  If not we write WHY and go
	 * to VA-API — unless Vulkan was asked for by name: then we
	 * fail saying so, because whoever asks by name is measuring.
	 * ⚠ `[M]` 1 Oct 2026 on the server: the Radeon RX 6800 (RADV, Mesa 25.0.7)
	 *   offers it for H.264 and HEVC; the Intel UHD 770 (ANV) does not, and stays on VA-API.
	 * ═══════════════════════════════════════════════════════════════════════ */
	if (c->strada_chiesta != STRADA_VAAPI) {
		char perche[512] = { 0 };
		char errore_vk[256] = { 0 };
		bool adatta = vulkan_adatta(c, perche, sizeof perche);

		if (adatta) {
			c->vk_dispositivo = vulkanvideo_apri_dispositivo(r->nodo_rendering, errore_vk,
			                                                 sizeof errore_vk);
			if (!c->vk_dispositivo) {
				adatta = false;
				di(perche, sizeof perche,
				   "the capability is there but the Vulkan device did not open: %s", errore_vk);
			}
		}
		if (adatta) {
			const VulkanVideoProfiloCapacita *p =
			    r->codec == CODIFICATORE_H264 ? &c->vk_capacita.h264
			    : r->profondita == 10        ? &c->vk_capacita.hevc10
			                                 : &c->vk_capacita.hevc;
			char modi[48];

			c->strada = STRADA_VULKAN;
			snprintf(c->nome_componente, sizeof c->nome_componente, "%s_vulkan",
			         r->codec == CODIFICATORE_H264 ? "h264" : "hevc");
			snprintf(c->conf.strada, sizeof c->conf.strada, "vulkan");
			snprintf(c->conf.fornitore_va, sizeof c->conf.fornitore_va, "%s · %s",
			         vulkanvideo_nome_scheda(c->vk_dispositivo),
			         vulkanvideo_nome_driver(c->vk_dispositivo));
			c->conf.bassa_potenza = false;
			c->conf.bassa_potenza_verificata = false;
			c->conf.misura_massima_l = p->misura_massima_l;
			c->conf.misura_massima_a = p->misura_massima_a;
			c->conf.misura_massima_letta = true;
			c->conf.modi_bitrate = p->modi_bitrate;
			c->conf.modi_bitrate_letti = true;
			nomi_modi_vulkan(p->modi_bitrate, modi, sizeof modi);
			registro_dice(REG_CODIFICA,
			              "⭐⭐ PHASE 19: VULKAN VIDEO route on «%s» — %s.  Requested %s.  "
			              "Declared bitrate modes [%s], QP %d..%d, granularity %ux%u, "
			              "headers from the driver %s, direct conversion into the planes %s.  "
			              "⚠ Whether it really encodes is said by the BYTES (forma_va_bene) and the "
			              "third witness, not by this line",
			              r->nodo_rendering, perche,
			              c->strada_chiesta == STRADA_VULKAN ? "BY NAME"
			                                                 : "by CAPABILITY (Vulkan before VA-API)",
			              modi, p->qp_minimo, p->qp_massimo, p->granularita_l, p->granularita_a,
			              p->intestazioni_dal_driver ? "yes" : "NO",
			              p->ingresso_scrivibile_dallo_shader ? "yes" : "no (copy)");
			return 0;
		}
		if (c->strada_chiesta == STRADA_VULKAN) {
			di(errore, errore_byte,
			   "«%s» on «%s»: Vulkan Video does NOT encode %s here — %s.  ⛔ Requested by name: "
			   "no fallback to VA-API, it would be two measurements under the same label",
			   c->nome_componente, r->nodo_rendering, nome_codec(r->codec), perche);
			return -1;
		}
		registro_dice(REG_CODIFICA,
		              "⭐ PHASE 19: route by capability on «%s» — Vulkan Video is NOT "
		              "suitable for %s (%s) ⇒ trying VA-API",
		              r->nodo_rendering, nome_codec(r->codec), perche);
	}
	c->strada = STRADA_VAAPI;
	snprintf(c->nome_componente, sizeof c->nome_componente, "%s_vaapi",
	         r->codec == CODIFICATORE_H264 ? "h264" : "hevc");
	snprintf(c->conf.strada, sizeof c->conf.strada, "vaapi");

	if (r->potenza == CODIFICATORE_POTENZA_NON_DICHIARATA) {
		di(errore, errore_byte,
		   "«%s»: the entrypoint was not declared.  ⛔ `EncSliceLP` (low "
		   "power) and `EncSlice` (full) are NOT equivalent, and a default "
		   "(full) is not inherited: ask for FULL or LOW",
		   c->nome_componente);
		return -1;
	}

	/* ⭐ PHASE 18: the node is opened by `vadiretta.c` (vaGetDisplayDRM + vaInitialize),
	 *    no longer by `av_hwdevice_ctx_create`.  It asks for the vendor itself. */
	if (!vadiretta_apri_dispositivo(r->nodo_rendering, &c->dispositivo, errore, errore_byte))
		return -1;

	VADisplay display = c->dispositivo.display;
	snprintf(c->conf.fornitore_va, sizeof(c->conf.fornitore_va), "%s",
	         c->dispositivo.fornitore);

	VAProfile profilo = profilo_va(r->codec, r->profondita);
	if (profilo == VAProfileNone) {
		di(errore, errore_byte,
		   "in hardware only HEVC can be opened: for AV1, hardware encoding on "
		   "this machine DOES NOT EXIST [M] — `av1_vaapi` exits 218, «No usable "
		   "encoding profile found», 3 runs out of 3");
		return -1;
	}
	VAEntrypoint voluto = (r->potenza == CODIFICATORE_POTENZA_PIENA)
	                          ? VAEntrypointEncSlice
	                          : VAEntrypointEncSliceLP;
	char visti[128] = { 0 };
	EsitoEntrypoint trovato =
	    entrypoint_c_e(display, profilo, voluto, visti, sizeof(visti));

	/* ⭐ THE `LA_DICHIARATA` RULE, and it is written in both branches: the
	 *    line says WHICH entrypoint and WHY, with the driver's list alongside.
	 *    ⛔ We switch to full only on "the driver does NOT declare it" — on "I
	 *    could not look" we fail as for the other two questions. */
	if (r->potenza == CODIFICATORE_POTENZA_LA_DICHIARATA) {
		if (trovato == EP_C_E)
			registro_dice(REG_CODIFICA,
			              "⭐ entrypoint EncSliceLP (low power) on «%s» (%s): the "
			              "driver DECLARES it for profile %d [%s] ⇒ taking "
			              "that one — rule: LP if declared, otherwise full",
			              r->nodo_rendering, c->conf.fornitore_va, (int) profilo,
			              visti);
		else if (trovato == EP_NON_C_E) {
			char visti_lp[128];
			snprintf(visti_lp, sizeof(visti_lp), "%s", visti[0] ? visti : "none");
			voluto = VAEntrypointEncSlice;
			trovato = entrypoint_c_e(display, profilo, voluto, visti,
			                         sizeof(visti));
			if (trovato == EP_C_E)
				registro_dice(REG_CODIFICA,
				              "⭐⚠ entrypoint EncSlice (FULL) on «%s» (%s): the "
				              "driver does NOT declare EncSliceLP for profile %d and "
				              "declares EncSlice [%s] ⇒ taking full — rule: "
				              "LP if declared, otherwise full.  ⚠ They are two different "
				              "encodings: the numbers from here do not hold for LP",
				              r->nodo_rendering, c->conf.fornitore_va, (int) profilo,
				              visti_lp);
		}
	}

	switch (trovato) {
	case EP_C_E:
		c->bassa_potenza_scelta = (voluto == VAEntrypointEncSliceLP);
		c->conf.bassa_potenza = c->bassa_potenza_scelta;
		c->conf.bassa_potenza_verificata = true;
		/* ⭐ The VERIFIED pair is the one `vadiretta_apri()` will use: it does not
		 *    rediscover it, it receives it. */
		c->profilo_va = profilo;
		c->entrypoint_va = voluto;
		break;
	case EP_NON_C_E:
		if (r->potenza == CODIFICATORE_POTENZA_LA_DICHIARATA) {
			di(errore, errore_byte,
			   "on «%s» (%s) profile %d has NEITHER EncSliceLP NOR EncSlice: the "
			   "driver declares [%s].  ⛔ No hardware encoding for "
			   "this profile — and without a card there is no encoding (phase 19: the "
			   "software fallback has left)",
			   r->nodo_rendering, c->conf.fornitore_va, (int) profilo,
			   visti[0] ? visti : "none");
			return -1;
		}
		di(errore, errore_byte,
		   "on «%s» (%s) profile %d does NOT have the entrypoint %s: the driver "
		   "declares [%s].  ⛔ No fallback to the other — they are two different "
		   "encodings, and falling back would give two measurements under the same label",
		   r->nodo_rendering, c->conf.fornitore_va, (int) profilo,
		   voluto == VAEntrypointEncSliceLP ? "EncSliceLP (low power)"
		                                    : "EncSlice (full)",
		   visti[0] ? visti : "none");
		return -1;
	case EP_NON_GUARDATO:
	default:
		di(errore, errore_byte,
		   "on «%s» I could NOT read the entrypoints of profile %d: ⛔ it is not "
		   "\"there are none\", it is \"I did not look\", and we do not encode on a machine "
		   "that could not be queried",
		   r->nodo_rendering, (int) profilo);
		return -1;
	}

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⭐⭐ AND THE MAXIMUM SIZE IS ASKED **OF THE DRIVER**, not of the first frame
	 *
	 * ⛔ THE FACT, `[M]` 22 Aug 2026 (agent D): `h264_vaapi` on `EncSliceLP`
	 *    accepts **32-4096 px per side** — 4096x2160 yes, **4112x2160 no**
	 *    (*"Hardware does not support encoding at size…"*).  `hevc_vaapi` instead holds
	 *    up to 16384x4320.
	 *    ⚠ And the legal canvas of `RCP.md` §4.5 went up to **7680x4320** ⇒ beyond
	 *      4096 px H.264 on this card was NOT there.  ⛔ PHASE 19: and the software
	 *      fallback that used to take its place has left — beyond the driver's
	 *      ceiling we refuse saying so, and that is all.
	 *    ⭐ And from 1 Oct 2026 the canvas stops at **4096x2304** (the user's
	 *      decision, `rcp.h`): on this card the refusal no longer comes
	 *      from the protocol.  ⚠ The question remains: the ceiling is the DRIVER's, and
	 *      another card may declare a lower one.
	 *
	 * ⇒ Without this question the refusal arrives **at the first frame**, that is
	 *   after the stage is mounted and someone is already watching: it is the form
	 *   of `LEZIONI.md` §1.8 — *declare instead of suffer*.  Here instead
	 *   `codificatore_nuovo()` fails **before**, saying the driver's number,
	 *   and `figlio.c` writes the refusal with its line.
	 *
	 * ⛔⛔ AND IT IS ASKED OF THE DRIVER AND NOT OF FFMPEG, which is the same lesson taken
	 *      from the other end: `[M]` **`-low_power 0` on the Intel opens the same
	 *      `EncSliceLP`, and ffmpeg does NOT fail** — it takes what is there.  ⇒ A
	 *      check made through the command line would give two measurements
	 *      under the same label (`LEZIONI.md` §1.11).
	 *
	 * ⚠ THREE OUTCOMES AND NOT TWO, as for the entrypoints: if the driver does not declare
	 *   the attribute (`VA_ATTRIB_NOT_SUPPORTED`) **nothing is concluded** — it is not
	 *   "there is no limit", it is "I could not ask", and we go on
	 *   writing it down.  ⛔ Refusing here would be deciding on a silence.
	 * ═══════════════════════════════════════════════════════════════════════ */
	{
		VAConfigAttrib attr[3] = { { .type = VAConfigAttribMaxPictureWidth },
			                   { .type = VAConfigAttribMaxPictureHeight },
			                   /* ⭐ the third is from phase 9: see the block at the bottom */
			                   { .type = VAConfigAttribRateControl } };
		VAStatus st = vaGetConfigAttributes(display, profilo, voluto, attr, 3);

		if (st != VA_STATUS_SUCCESS) {
			registro_dice(REG_CODIFICA,
			              "⚠ on «%s» I could NOT ask the driver for the maximum size "
			              "(vaGetConfigAttributes: %d): ⛔ it is NOT \"there is no limit\", it is "
			              "\"I did not look\".  If %ux%u were too big it will be "
			              "found out at the first frame",
			              r->nodo_rendering, (int) st, r->larghezza, r->altezza);
		} else if (attr[0].value == VA_ATTRIB_NOT_SUPPORTED ||
		           attr[1].value == VA_ATTRIB_NOT_SUPPORTED) {
			registro_dice(REG_CODIFICA,
			              "⚠ «%s» (%s) does not DECLARE a maximum size for profile %d: "
			              "⛔ we do not conclude that there is none",
			              r->nodo_rendering, c->conf.fornitore_va, (int) profilo);
		} else {
			c->conf.misura_massima_l = attr[0].value;
			c->conf.misura_massima_a = attr[1].value;
			c->conf.misura_massima_letta = true;
			if (r->larghezza > attr[0].value || r->altezza > attr[1].value) {
				di(errore, errore_byte,
				   "«%s» on «%s» (%s) encodes at most %ux%u — requested %ux%u.  ⛔ The "
				   "driver says so BEFORE, and we declare it instead of finding out at the first "
				   "frame (phase 19: without the card there is no encoding, no "
				   "software fallback)",
				   c->nome_componente, r->nodo_rendering, c->conf.fornitore_va,
				   attr[0].value, attr[1].value, r->larghezza, r->altezza);
				return -1;
			}
			registro_dice(REG_CODIFICA,
			              "⭐ the driver declares at most %ux%u for «%s» on %s, and "
			              "%ux%u fits — ASKED of the driver, not deduced from the name",
			              attr[0].value, attr[1].value, c->nome_componente,
			              c->conf.nodo, r->larghezza, r->altezza);
		}

		/* ═══════════════════════════════════════════════════════════════════
		 * ⭐⭐⭐ FIRST BITRATE WITNESS: WHICH MODES THE DRIVER DECLARES
		 *
		 * ⛔ It is **R31**, the dearest lesson of the project, applied from the right
		 *    end: *"the bitrate control mode is not chosen: the
		 *    driver deduces it"*.  In v1 nobody had asked for CBR — the Intel
		 *    driver **deduced** it from `rc_max_rate == bit_rate`, and *"no
		 *    error, no warning, no log line: there was a
		 *    bill"*.
		 *
		 * ⛔⛔ AND THE TRAP IS ARMED INSIDE FFMPEG, `[M]` read in the installed
		 *      library (`libavcodec.so.61`, 7.1.5-0+deb13u1):
		 *
		 *        *"Driver does not report any supported rate control modes:
		 *          assuming CQP only."*
		 *
		 *      ⇒ **If the driver is silent, libavcodec deduces in its place.**  It is
		 *      R31 in new clothes: not "the driver deduces", but "ffmpeg deduces
		 *      on the driver's behalf", **with the same silence**.  ⚠ And that
		 *      line today **would not be seen**: `av_log_set_level` appears
		 *      nowhere in `src/`, and ffmpeg's log stays at
		 *      `AV_LOG_INFO`, on `stderr` instead of in ours.
		 *      ⇒ That is why the question is asked **by us**, to the driver, and the answer
		 *      ends up in **our** log next to the other numbers.
		 *
		 * ⚠ THREE OUTCOMES AND NOT TWO, as for the entrypoints and for the maximum
		 *   size.  The second is the one that deceives: `VA_ATTRIB_NOT_SUPPORTED`
		 *   means *"the driver does not declare it"*, ⛔ **not** *"there is only
		 *   CQP"* — and whoever concluded on it would make the same deduction that
		 *   ffmpeg makes silently two lines further on.
		 *
		 * `[M]` 23 Aug 2026, **on this laptop** (⚠ not the test
		 * machine: same driver **Intel iHD 25.2.3**, different GPU),
		 * `vainfo -a` on `VAProfileH264High/VAEntrypointEncSliceLP`:
		 *
		 *     CBR|VBR|CQP|MB|QVBR|TCBRC   (0x1496)
		 *
		 * ⇒ ⭐ **QVBR is there** — and it is the mode the ceiling asks for.  ⚠ On the
		 *   test machine **it is not verified**, and this log line is
		 *   exactly what will verify it at the first start.
		 * ═══════════════════════════════════════════════════════════════════ */
		ModoBitrate modo = modo_bitrate_voluto();
		char modi[192];
		if (st != VA_STATUS_SUCCESS) {
			registro_dice(REG_CODIFICA,
			              "⚠ on «%s» I could NOT ask the driver for the bitrate "
			              "control modes (vaGetConfigAttributes: %d): ⛔ it is NOT "
			              "\"there is only CQP\", it is \"I did not look\".  %s is asked for by "
			              "name anyway, and if it is not there the opening will fail saying so",
			              r->nodo_rendering, (int) st, modo.nome);
		} else if (attr[2].value == VA_ATTRIB_NOT_SUPPORTED) {
			registro_dice(REG_CODIFICA,
			              "⚠ «%s» (%s), profile %d, %s: the driver DECLARES NO "
			              "bitrate control mode.  ⛔ And we do not conclude that there "
			              "is only one (that was libavcodec's deduction, «assuming CQP "
			              "only», and vadiretta does NOT make it): %s is asked for by name, and if "
			              "the driver refuses it the opening will fail saying so",
			              r->nodo_rendering, c->conf.fornitore_va, (int) profilo,
			              voluto == VAEntrypointEncSliceLP ? "EncSliceLP (low power)"
			                                               : "EncSlice (full)",
			              modo.nome);
		} else {
			c->conf.modi_bitrate = attr[2].value;
			c->conf.modi_bitrate_letti = true;
			nomi_modi_bitrate(attr[2].value, modi, sizeof(modi));
			if (!(attr[2].value & modo.va_bit)) {
				/* ⛔ NO FALLBACK: it would be R31 from the other end — taking "what
				 *    is there" is exactly the gesture that in v1 made CBR come out
				 *    of a choice nobody had made. */
				di(errore, errore_byte,
				   "«%s» on «%s» (%s), profile %d, %s: the bitrate control mode %s (0x%x) "
				   "was requested and the driver DECLARES [%s] (0x%x) — "
				   "⛔ it is NOT there.  No fallback to another mode: it would be R31 from the other "
				   "end, that is a bitrate mode chosen by nobody",
				   c->nome_componente, r->nodo_rendering, c->conf.fornitore_va,
				   (int) profilo,
				   voluto == VAEntrypointEncSliceLP ? "EncSliceLP" : "EncSlice",
				   modo.nome, modo.va_bit, modi, attr[2].value);
				return -1;
			}
			registro_dice(REG_CODIFICA,
			              "⭐ bitrate control on «%s» (%s), profile %d, %s: the "
			              "driver DECLARES [%s] (0x%x) · requested %s (0x%x) · it is there.  "
			              "⚠ Being there does not mean it is applied: the BYTES say that "
			              "(third witness), not this line",
			              r->nodo_rendering, c->conf.fornitore_va, (int) profilo,
			              voluto == VAEntrypointEncSliceLP ? "EncSliceLP (low power)"
			                                               : "EncSlice (full)",
			              modi, attr[2].value, modo.nome, modo.va_bit);
		}
	}
	return 0;
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐⭐ THE LEVEL CEILING OF `RCP.md` §4.3 (line 701), TRANSLATED INTO THE ALPHABET
 *      OF EACH CODEC — 23 Aug 2026, and it comes from a measurement.
 *
 *      `[M]` canvas 3840x2160, H.264: the client declares `video.livello=5.1` and
 *      this module produced a stream of level **5.2**.  ⛔ §4.3 is a
 *      MUST — *"the server MUST emit a stream of a level no higher, and
 *      does not guess it"* — and the symptom of an exceeded level is NOT a network
 *      error: it is the browser's decoder REFUSING the
 *      configuration, that is "nothing shows" without a line saying
 *      why.
 *
 * ⛔ AND THE CURE IS TO ASK BEFORE, not to notice afterwards.  Until tonight the
 *    level was **inherited**: libavcodec computed it from size and cadence and
 *    nobody had ever told it what the ceiling was.  It is the same form as
 *    `opzioni_hevc()` — *"the options that are decided instead of inherited"*.
 *
 * ⚠ THE THREE ALPHABETS, and they are the trap:
 *
 *      H.264   `level_idc`         = major*10 + minor       ⇒ 5.1 is **51**
 *      HEVC    `general_level_idc` = (major*10+minor)*3     ⇒ 5.1 is **153**
 *      AV1     `seq_level_idx`     = (major−2)*4+minor      ⇒ 5.1 is **13**
 *
 *    ⛔ `[M]` read in `ffmpeg -h encoder=h264_vaapi` and `hevc_vaapi`: the
 *       `level` option of `h264_vaapi` wants 51, the one of `hevc_vaapi` wants 153.
 *       Passing one to the other would give a wrong level WITHOUT an error.
 *    ⚠ AV1 has been out of the product since 20 Aug 2026 (`DECISIONI.md` §1.13-ter,
 *      no longer negotiated): the line stays because the codec still exists in the
 *      program, and a `0` here means "I impose nothing", not "zero".
 *
 * ⇒ Returns **0** when there is no ceiling to impose, and the caller does not
 *   ask anything of the component.  ⛔ And the returned value is NOT the proof that
 *   the component obeyed: that is read from the bytes of the SPS
 *   (`livello_flusso`), and it is the second half of R31. */
static int livello_imposto(const Codificatore *c)
{
	int x10 = c->richiesta.livello_x10;

	if (x10 <= 0)
		return 0; /* §4.3 does not oblige the client to declare it: no ceiling */
	switch (c->richiesta.codec) {
	case CODIFICATORE_H264:
		return x10;
	case CODIFICATORE_HEVC:
		return x10 * 3;
	case CODIFICATORE_AV1:
		return (x10 / 10 - 2) * 4 + x10 % 10;
	default:
		return 0;
	}
}

/*
 * ⭐⭐ THE CARD OPENS HERE — phase 18: it was `opzioni_vaapi()`, which passed to
 *     libavcodec `rc_mode`, `qp`, `async_depth`, `low_power`, `idr_interval`,
 *     `profile`, `level`.  Each of those options had a measured reason
 *     and the reason stays: only WHO it is told to changes.
 *
 *   `rc_mode`       → `VaDirettaRichiesta.banda_*`: zeros = CQP, otherwise QVBR
 *                     — asked for BY NAME here too, and `apri_dispositivo()` has
 *                     already read from the driver that the mode exists (R31);
 *   `qp`            → `.qp`: fixed under CQP, quality factor under QVBR
 *                     (`[M]` 23 Aug 2026: under QVBR the QP counts, under
 *                     VBR it does not — and that is the reason the ceiling uses QVBR);
 *   `async_depth=1` → no longer exists as an option: vadiretta WAITS for the end
 *                     of every frame by construction.  ⚠ `[M]` 13 Aug
 *                     2026 libavcodec's default was 2, and nobody had
 *                     asked for it: it is the default that can no longer be
 *                     inherited, because there is no longer anyone to inherit it from;
 *   `low_power`     → `.entrypoint`: the one CHOSEN and VERIFIED in
 *                     `apri_dispositivo()`, with the `LA_DICHIARATA` rule;
 *   `idr_interval=0`→ by construction: every I is an IDR (`vadiretta.c`);
 *   `profile`       → `.profilo` (VAProfileH264High / HEVCMain / HEVCMain10);
 *   `level`         → `.livello_idc` = `livello_imposto()`, 0 = computed
 *                     as ffmpeg computed it.
 *
 * ⛔ THE TWO REFUSALS STAY IDENTICAL: lossless and CRF do not exist on the
 *    card, and they are not faked (`ModoQualita`).
 */
/* ⛔ THE TWO REFUSALS (and the third, on the QP) are the same for both card
 *    routes, and live in one place only. */
static bool qualita_ammessa_sulla_scheda(const Codificatore *c, char *errore, size_t errore_byte)
{
	if (c->modo_corrente == CODIFICATORE_QUALITA_LOSSLESS) {
		/* ⛔ It is not faked, as it is not faked on SVT-AV1: the card has no
		 *    lossless mode, and `qp=0` is NOT one — on VA-API zero is the
		 *    value that means "not requested" (the option's default), which is
		 *    the same implicit sentinel already paid for on `crf=0`. */
		di(errore, errore_byte,
		   "in hardware there is no lossless mode, and it is not faked: "
		   "the card has constant QP, and `qp=0` means \"not requested\", not "
		   "\"lossless\".  ⛔ And since phase 18 it is not there in software either "
		   "(OpenH264 and SVT-AV1 do not have it): ask for a low QP");
		return false;
	}
	if (c->modo_corrente == CODIFICATORE_QUALITA_CRF) {
		/* ⛔ CRF and QP are not the same quantity: see `ModoQualita`. */
		di(errore, errore_byte,
		   "in hardware there is no CRF: the card has constant QP.  ⛔ "
		   "Translating CRF %d into QP %d and still calling it CRF would give two "
		   "measurements under the same label ⇒ ask for CODIFICATORE_QUALITA_QP",
		   c->qualita_corrente, c->qualita_corrente);
		return false;
	}
	if (c->qualita_corrente < 1 || c->qualita_corrente > 51) {
		di(errore, errore_byte,
		   "QP %d out of range: ask between 1 and 51 — ⛔ and ZERO is not \"the "
		   "best\", it is the default value that means \"not requested\"",
		   c->qualita_corrente);
		return false;
	}
	return true;
}

/* The three numbers of the ceiling, with the check that is worth R31 — the same for both
 * routes: with working point == wire the driver (or the regulator) deduces CBR. */
static bool tetto_in_tre_numeri(int64_t *punto, int64_t *filo, int *serbatoio, char *errore,
                                size_t errore_byte)
{
	*punto = tetto_punto();
	*filo = tetto_filo();
	*serbatoio = tetto_serbatoio_bit();
	/* ⛔⛔ THE CHECK THAT IS WORTH R31, and it sits BEFORE the opening: if these
	 *      two numbers were equal the driver would deduce **CBR** — and `[M]`
	 *      CBR on this hardware spends **83 times** what is needed on a still
	 *      scene.  It is not a theoretical possibility: it is what v1 did. */
	if (*punto >= *filo || *serbatoio <= 0) {
		di(errore, errore_byte,
		   "⛔ the ceiling numbers are broken: working point %" PRId64 ", wire "
		   "%" PRId64 ", buffer %d bits.  The working point MUST stay below the wire "
		   "(with wire == working point the driver deduces CBR: that is R31) and the "
		   "buffer MUST be positive",
		   *punto, *filo, *serbatoio);
		return false;
	}
	return true;
}

/* ⛔⛔ THE BUFFER, AND THE NUMBER IS JUDGED IN MILLISECONDS — the defect of
 *      v1 nobody had ever named: `rc_buffer_size = bit_rate/2`
 *      is **500 ms**, ten times the 50 ceiling of `CODER.md` §1-bis.
 *      The same for both routes. */
static bool serbatoio_entro_i_50_ms(Codificatore *c, char *errore, size_t errore_byte)
{
	if (tetto_pavimento_mbit && c->conf.banda_serbatoio_ms > 50) {
		di(c->conf.perche_no, sizeof(c->conf.perche_no),
		   "the regulator's buffer is %u ms (%d bits at %" PRId64 " bit/s): "
		   "CODER.md §1-bis gives 50 ms to ALL of our part, and a regulator cannot "
		   "take them all.  ⚠ In v1 they were 500, and nobody said so",
		   c->conf.banda_serbatoio_ms, c->conf.banda_serbatoio, c->conf.banda_filo);
		c->conf.ha_obbedito = false;
		di(errore, errore_byte, "⛔ E2: %s", c->conf.perche_no);
		return false;
	}
	return true;
}

static int apri_scheda_vaapi(Codificatore *c, char *errore, size_t errore_byte)
{
	const CodificatoreRichiesta *r = &c->richiesta;
	VaDirettaRichiesta v;
	const VaDirettaDichiarazione *d;
	char errore_va[256] = { 0 };

	if (!qualita_ammessa_sulla_scheda(c, errore, errore_byte))
		return -1;

	memset(&v, 0, sizeof v);
	v.codec = (r->codec == CODIFICATORE_H264) ? VADIRETTA_H264 : VADIRETTA_HEVC;
	v.profondita = r->profondita;
	v.larghezza = r->larghezza;
	v.altezza = r->altezza;
	v.fotogrammi_al_secondo = r->fotogrammi_al_secondo ? r->fotogrammi_al_secondo : 30;
	v.profilo = c->profilo_va;
	v.entrypoint = c->entrypoint_va;
	v.qp = c->qualita_corrente;
	v.chiavi_ogni = r->chiavi_ogni;
	v.superfici_ingresso = SUPERFICI_PRONTE;
	if (tetto_pavimento_mbit
	    && !tetto_in_tre_numeri(&v.banda_punto, &v.banda_filo, &v.serbatoio_bit, errore,
	                            errore_byte))
		return -1;
	/* ⛔⭐⭐ AND THE §4.3 LEVEL, ASKED FOR BY NAME — 23 Aug 2026.  A
	 *      failure HERE is a real error and stops the opening: if the card
	 *      refuses the ceiling, opening it anyway would mean producing again
	 *      a stream that overshoots — that is the defect of that evening. */
	v.livello_idc = livello_imposto(c);
	if (v.livello_idc > 0)
		registro_dice(REG_CODIFICA,
		              "⭐ §4.3: level IMPOSED on «%s» — %d.%d, that is %d in "
		              "%s.  ⚠ Requested does not mean obeyed: the verdict "
		              "comes from the SPS",
		              c->nome_componente, r->livello_x10 / 10, r->livello_x10 % 10,
		              v.livello_idc,
		              r->codec == CODIFICATORE_H264 ? "level_idc"
		                                            : "general_level_idc (three times)");

	c->va = vadiretta_apri(&c->dispositivo, &v, errore_va, sizeof errore_va);
	if (!c->va) {
		di(errore, errore_byte, "«%s» did not open: %s", c->nome_componente, errore_va);
		return -1;
	}
	d = vadiretta_dichiarazione(c->va);

	/* ───────────────────────────────────────────────────────────────────────
	 * ⛔ FIRST WITNESS: the confession from the context — which is now OURS, and
	 *    therefore says what we wrote ourselves.  ⚠ It is worth less than yesterday, and it is
	 *    right to say so: yesterday rereading `async_depth` from libavcodec was a
	 *    check on someone else; today the fields are so by construction.  The
	 *    witness that counts has remained the SECOND — the bytes (`forma_va_bene`)
	 *    — and the THIRD, the measured bandwidth.
	 */
	c->conf.codec = r->codec;
	c->conf.componente = c->nome_componente;
	c->conf.profondita_chiesta = r->profondita;
	c->conf.fotogrammi_b = 0;
	c->conf.global_header = false;
	c->conf.in_hardware = true;
	c->conf.ha_obbedito = true;
	c->conf.perche_no[0] = 0;
	c->conf.profondita_asincrona = 1;
	c->conf.bassa_potenza = c->bassa_potenza_scelta;
	/* yesterday's numbers for the mode (1 = CQP, 5 = QVBR) stay, so the log
	 * lines and the benches that read them do not change */
	c->conf.modo_bitrate = (d->modo_va == VA_RC_QVBR) ? 5 : 1;
	c->conf.banda_punto = v.banda_punto;
	c->conf.banda_filo = v.banda_filo;
	c->conf.banda_serbatoio = v.serbatoio_bit;
	c->conf.banda_serbatoio_ms =
	    (v.banda_filo > 0 && v.serbatoio_bit > 0)
	        ? (uint32_t) ((int64_t) v.serbatoio_bit * 1000 / v.banda_filo)
	        : 0;
	if (!serbatoio_entro_i_50_ms(c, errore, errore_byte)) {
		vadiretta_chiudi(c->va);
		c->va = NULL;
		return -1;
	}
	c->prossimo_chiave = true; /* ⛔ after every opening the first is a key */
	return 0;
}

/*
 * ⭐⭐ PHASE 19 — THE CARD OPENS IN VULKAN VIDEO.  The same numbers as
 *     `apri_scheda_vaapi()`, told to `vulkanvideo.c`:
 *
 *   the ceiling   → `banda_*`/`serbatoio_bit`: zeros = CQP, otherwise VBR with
 *                   the requested QP as the regulator's FLOOR (Vulkan does not
 *                   have VA-API's QVBR: `vulkanvideo.h`);
 *   the level     → `livello_idc` = `livello_imposto()`, 0 = computed as
 *                   ffmpeg computed it;
 *   the keys      → `chiavi_ogni` (0 = on request), and every I is an IDR;
 *   the entrypoint → does not exist in Vulkan: nothing to declare.
 *
 * ⛔ The headers (SPS/PPS/VPS) are written by THE DRIVER from our `StdVideo*`
 *    (`vkGetEncodedVideoSessionParametersKHR`); what came out of it is
 *    reread from the bytes in `forma_va_bene()`, exactly as for VA-API.
 */
static int apri_scheda_vulkan(Codificatore *c, char *errore, size_t errore_byte)
{
	const CodificatoreRichiesta *r = &c->richiesta;
	VulkanVideoRichiesta v;
	const VulkanVideoDichiarazione *d;
	char errore_vk[256] = { 0 };

	if (!qualita_ammessa_sulla_scheda(c, errore, errore_byte))
		return -1;

	memset(&v, 0, sizeof v);
	v.codec = (r->codec == CODIFICATORE_H264) ? VULKANVIDEO_H264 : VULKANVIDEO_HEVC;
	v.profondita = r->profondita;
	v.larghezza = r->larghezza;
	v.altezza = r->altezza;
	v.fotogrammi_al_secondo = r->fotogrammi_al_secondo ? r->fotogrammi_al_secondo : 30;
	v.qp = c->qualita_corrente;
	v.chiavi_ogni = r->chiavi_ogni;
	if (tetto_pavimento_mbit
	    && !tetto_in_tre_numeri(&v.banda_punto, &v.banda_filo, &v.serbatoio_bit, errore,
	                            errore_byte))
		return -1;
	v.livello_idc = livello_imposto(c);
	if (v.livello_idc > 0)
		registro_dice(REG_CODIFICA,
		              "⭐ §4.3: level IMPOSED on «%s» — %d.%d, that is %d in "
		              "%s.  ⚠ Requested does not mean obeyed: the verdict "
		              "comes from the SPS",
		              c->nome_componente, r->livello_x10 / 10, r->livello_x10 % 10,
		              v.livello_idc,
		              r->codec == CODIFICATORE_H264 ? "level_idc"
		                                            : "general_level_idc (three times)");

	c->vk = vulkanvideo_apri(c->vk_dispositivo, &v, errore_vk, sizeof errore_vk);
	if (!c->vk) {
		di(errore, errore_byte, "«%s» did not open: %s", c->nome_componente, errore_vk);
		return -1;
	}
	d = vulkanvideo_dichiarazione(c->vk);

	c->conf.codec = r->codec;
	c->conf.componente = c->nome_componente;
	c->conf.profondita_chiesta = r->profondita;
	c->conf.fotogrammi_b = 0;
	c->conf.global_header = false;
	c->conf.in_hardware = true;
	c->conf.ha_obbedito = true;
	c->conf.perche_no[0] = 0;
	c->conf.profondita_asincrona = 1;
	c->conf.bassa_potenza = false;
	/* in yesterday's alphabet: 1 = CQP, 3 = VBR (5 is VA-API's QVBR) */
	c->conf.modo_bitrate = (d->modo_rc == VULKANVIDEO_RC_VBR) ? 3 : 1;
	c->conf.banda_punto = v.banda_punto;
	c->conf.banda_filo = v.banda_filo;
	c->conf.banda_serbatoio = v.serbatoio_bit;
	c->conf.banda_serbatoio_ms =
	    (v.banda_filo > 0 && v.serbatoio_bit > 0)
	        ? (uint32_t) ((int64_t) v.serbatoio_bit * 1000 / v.banda_filo)
	        : 0;
	if (!serbatoio_entro_i_50_ms(c, errore, errore_byte)) {
		vulkanvideo_chiudi(c->vk);
		c->vk = NULL;
		return -1;
	}
	/* ⭐ THE DRIVER'S DECLARATION, written once per opening: it is the
	 *    first witness, and as for VA-API it is worth less than the bytes. */
	registro_dice(REG_CODIFICA,
	              "⭐ Vulkan Video «%s»: encodes %ux%u (block %u) for the canvas %ux%u · "
	              "level %d in the SPS · %s · headers %s%s%s · conversion %s · "
	              "minimum latency %s · input %s · QP %d..%d · %zu bytes of "
	              "headers in front of every key",
	              c->nome_componente, d->larghezza_codificata, d->altezza_codificata, d->blocco,
	              r->larghezza, r->altezza, d->livello_idc,
	              d->modo_rc == VULKANVIDEO_RC_VBR ? "VBR (requested QP = floor)" : "CQP",
	              d->intestazioni_dal_driver ? "from the driver" : "written by us",
	              d->driver_ha_cambiato_parametri ? " (⚠ the driver CHANGED the parameters)"
	                                              : "",
	              d->livello_corretto_nei_byte ? " (⚠ HEVC level corrected in the bytes)" : "",
	              d->conversione_diretta ? "direct into the planes" : "in two images and copy",
	              d->ritardo_minimo_chiesto ? "requested" : "not accepted by the driver",
	              d->formato_ingresso, d->qp_minimo, d->qp_massimo, d->intestazioni_byte);
	c->prossimo_chiave = true; /* ⛔ after every opening the first is a key */
	return 0;
}

/*
 * ⭐ The card's context is closed and opened here, and `abbassa_qualita()`,
 *    `risali_qualita()`, `codificatore_ridimensiona()` call these two.
 *    ⚠ vadiretta's context also carries the input store and the
 *    reconstructed surfaces; vulkanvideo's carries the session, the images and the
 *    DMA-BUF cache.  ⛔ Phase 19: the software fallback branch
 *    (`sw_apri`/`sw_chiudi`, `ripiego.c`) has left — `c->hardware` is true
 *    in every encoder that was born, and the guard stays for the half-born one.
 */
static void chiudi_contesto(Codificatore *c)
{
	if (c->strada == STRADA_VULKAN) {
		vulkanvideo_chiudi(c->vk);
		c->vk = NULL;
	} else if (c->hardware) {
		vadiretta_chiudi(c->va);
		c->va = NULL;
		c->superficie_pronta = VA_INVALID_ID;
	}
	c->cornice_decisa = false;
	c->cornice_attiva = false;
}

static int apri_contesto(Codificatore *c, char *errore, size_t errore_byte)
{
	if (!c->hardware) {
		di(errore, errore_byte, "no card open: without a card there is no encoding (phase 19)");
		return -1;
	}
	return c->strada == STRADA_VULKAN ? apri_scheda_vulkan(c, errore, errore_byte)
	                                  : apri_scheda_vaapi(c, errore, errore_byte);
}

/*
 * ⭐ THE FRAMES AND THE CONVERSION — in one place only, because `codificatore_
 *    nuovo()` and `codificatore_ridimensiona()` did the same thing in two
 *    drafts, and ⛔ the second had already forgotten the declared promotion.
 *    Two drafts of the same thing are a place to diverge silently.
 *
 * ⭐ The input surfaces are kept by vadiretta, and here only the STAGING buffer
 *    of the from-memory route is allocated — NV12 (8 bit) or P010 (10 bit) at the size
 *    of the canvas, which `colori709.c` fills and `vadiretta_carica_*()` uploads.
 *    ⚠ It is redone on every reopening because the size may have changed.
 */
static int apri_fotogrammi(Codificatore *c, char *errore, size_t errore_byte)
{
	const CodificatoreRichiesta *r = &c->richiesta;

	free(c->appoggio);
	c->appoggio = NULL;
	c->appoggio_byte = 0;
	/* ⭐ Phase 19: on the Vulkan route the BGRx are uploaded as they are and
	 *    the shader converts them: no staging buffer. */
	if (c->hardware && c->strada == STRADA_VAAPI && FORMATO_PIXEL_IMPACCHETTATO(r->formato)) {
		size_t campione = r->profondita == 10 ? 2u : 1u;
		/* Y in full, then interleaved UV at half height: 1.5 samples per pixel. */
		c->appoggio_byte = (size_t) r->larghezza * r->altezza * campione * 3u / 2u;
		c->appoggio = malloc(c->appoggio_byte);
		if (!c->appoggio) {
			c->appoggio_byte = 0;
			di(errore, errore_byte, "no memory for the %ux%u staging buffer", r->larghezza,
			   r->altezza);
			return -1;
		}
	}
	/* ⚠ The source has real 8 bits (`[M]` F2.2): the Main10 that comes out is 8 bits
	 *   PROMOTED, and the promotion is declared instead of suffered.  It holds for both
	 *   routes: in hardware the promotion is done by `colori709_a_p010()`. */
	c->conf.promozione_8_a_10 =
	    (FORMATO_PIXEL_IMPACCHETTATO(r->formato) && r->profondita == 10);
	return 0;
}

Codificatore *codificatore_nuovo(const CodificatoreRichiesta *richiesta,
                                 char *errore, size_t errore_byte)
{
	if (!richiesta || richiesta->larghezza == 0 || richiesta->altezza == 0) {
		di(errore, errore_byte, "zero size");
		return NULL;
	}
	if (richiesta->profondita != 8 && richiesta->profondita != 10) {
		di(errore, errore_byte, "depth %d: ask for 8 or 10", richiesta->profondita);
		return NULL;
	}
	/*
	 * ⛔ A 10-bit input inside an 8-bit encoder is not a conversion:
	 *    it is an out-of-bounds read.  ⚠ And the symptom would be **memory
	 *    overrun**, not an ugly picture — that is a defect that names
	 *    neither the colour nor the depth.  Whoever wants 8 bits goes through BGRx, which
	 *    has a declared conversion.
	 */
	if (richiesta->formato == CODIFICATORE_PIXEL_YUV420P10LE && richiesta->profondita != 10) {
		di(errore, errore_byte,
		   "the input is yuv420p10le and %d bits are requested: they do not mix — "
		   "for 8 bits enter through BGRx", richiesta->profondita);
		return NULL;
	}
	/* ⚠ 4:2:0 wants even sizes: an odd width would give a chroma of
	 *   half a sample, and the encoder would round it **silently**. */
	if ((richiesta->larghezza & 1) || (richiesta->altezza & 1)) {
		di(errore, errore_byte, "%ux%u: 4:2:0 wants even sizes",
		   richiesta->larghezza, richiesta->altezza);
		return NULL;
	}

	Codificatore *c = calloc(1, sizeof(*c));
	if (!c) {
		di(errore, errore_byte, "out of memory");
		return NULL;
	}
	c->richiesta = *richiesta;
	c->modo_corrente = richiesta->modo;
	c->qualita_corrente = richiesta->qualita;
	/* ⭐ Phase 9: the wait starts from its resting value and from there on only
	 *    doubles (`abbassa_qualita()`), never the opposite. */
	c->risalita_attesa = RISALITA_ATTESA;

	/* ⛔ PHASE 19: without a name there is nothing to open — the software
	 *    fallback (OpenH264, SVT-AV1) has left (`DECISIONI.md` §10.27), and
	 *    below it is refused saying so. */
	const char *nome = richiesta->componente ? richiesta->componente
	                                         : "(no encoder requested)";
	/*
	 * ⛔ REQUESTED BY NAME, NO FALLBACK — the v1 line
	 * (`codificatore.c:550-566`) that this file inherits in full:
	 *   "Whoever names an encoder is measuring: falling back to another would give
	 *    two different measurements with the same label, which is worse than not
	 *    measuring."
	 */
	snprintf(c->nome_componente, sizeof c->nome_componente, "%s", nome);
	c->superficie_pronta = VA_INVALID_ID;
	c->dispositivo.fd = -1;

	/*
	 * ⛔ "Is it in hardware?" is decided BEFORE opening: on that answer
	 *    depend the device, the store and the conversion — that is three
	 *    things that cannot be changed afterwards.  ⭐ Phase 18: the NAME says it
	 *    (`h264_vaapi`/`hevc_vaapi` are the card's two labels), and the
	 *    label's codec must be the one requested.
	 */
	{
		CodecVideo codec_scheda;
		c->hardware = componente_della_scheda(nome, &codec_scheda, &c->strada_chiesta);
		if (c->hardware && codec_scheda != richiesta->codec) {
			di(errore, errore_byte, "«%s» is not a %s encoder", nome,
			   nome_codec(richiesta->codec));
			free(c);
			return NULL;
		}
	}
	if (!c->hardware) {
		/* ⛔ PHASE 19 — NO PROCESSOR WITHOUT A CARD (`DECISIONI.md` §10.27,
		 *    the user's words: *"no CPU without a card"*).  The encoders
		 *    are the card's; any other name is refused, with the reason. */
		di(errore, errore_byte,
		   "the encoder «%s» does not exist: REMOTIX encodes ONLY on the card "
		   "(«h264_scheda»/«hevc_scheda» by capability, «*_vulkan» or «*_vaapi» by "
		   "name) — ⛔ the software fallback left with phase 19, and no other one "
		   "is taken",
		   nome);
		free(c);
		return NULL;
	}
	if (apri_dispositivo(c, errore, errore_byte) < 0) {
		codificatore_libera(c);
		return NULL;
	}

	if (apri_contesto(c, errore, errore_byte) < 0) {
		codificatore_libera(c);
		return NULL;
	}
	if (apri_fotogrammi(c, errore, errore_byte) < 0) {
		codificatore_libera(c);
		return NULL;
	}

	/*
	 * ⛔ The name carries the node and the power INSIDE it, not beside it: it is the line that
	 *    ends up in the log next to every number, and a 3 ms rate without
	 *    "which card" and "which entrypoint" next to it is a number that holds for
	 *    a machine nobody knows (`LEZIONI.md` §1.1).
	 */
	if (c->strada == STRADA_VULKAN)
		snprintf(c->nome, sizeof(c->nome),
		         "%s %s via %.40s (in HARDWARE · %.60s · Vulkan Video: %.160s)",
		         nome_codec(richiesta->codec),
		         richiesta->profondita == 10 ? "10 bit" : "8 bit",
		         c->nome_componente, c->conf.nodo, c->conf.fornitore_va);
	else
		snprintf(c->nome, sizeof(c->nome),
		         "%s %s via %.40s (in HARDWARE · %.60s · VA-API: %.120s · %s)",
		         nome_codec(richiesta->codec),
		         richiesta->profondita == 10 ? "10 bit" : "8 bit",
		         c->nome_componente, c->conf.nodo, c->conf.fornitore_va,
		         c->conf.bassa_potenza ? "⚠ EncSliceLP, low power — it is NOT "
		                                 "full encoding"
		                               : "EncSlice, full");

	/* ⭐ THE WORKING POINT WITH ITS NUMBER, not with its name.  ⛔ Until 23
	 *    Aug 2026 this line said *"constant QP"* and kept quiet about the **26**: whoever
	 *    reread a bench could not know which rung it had started from, and
	 *    `QP_HARDWARE` (`figlio.c:4052`) could be tried only by recompiling. */
	char punto[48];
	if (richiesta->modo == CODIFICATORE_QUALITA_LOSSLESS)
		snprintf(punto, sizeof(punto), "lossless");
	else
		snprintf(punto, sizeof(punto), "%s %d%s", nome_modo(richiesta->modo),
		         richiesta->qualita,
		         richiesta->modo == CODIFICATORE_QUALITA_QP ? " constant" : "");

	registro_dice(REG_CODIFICA, "opened: %s · %ux%u · %s · keys %s%s", c->nome,
	              richiesta->larghezza, richiesta->altezza, punto,
	              richiesta->chiavi_ogni ? "periodic" : "on request only",
	              c->conf.promozione_8_a_10
	                  ? " · ⚠ capture's 8 bits PROMOTED to 10: the desired value of "
	                    "SPECIFICHE.md §3.1 does not come from this source"
	                  : "");

	/*
	 * ⭐⭐ THE DEGRADATION LADDER, WRITTEN WITH THE VALUES IN FORCE.
	 *
	 * ⛔ Until now `CRF_PASSO`, `CRF_DI_EMERGENZA` and `RICODIFICHE_MASSIME` did not
	 *    appear **in any log line**: the ladder was known only by
	 *    reading the source, and tuning it meant recompiling **and** remembering
	 *    with which value it had been measured the time before.  ⚠ A number that
	 *    decides what is seen and appears nowhere is a number that
	 *    sooner or later gets measured wrong.
	 *
	 * ⚠ And `abbassa_qualita()` is SIMULATED instead of writing the ladder by hand: two
	 *   drafts of the same rule are a place to diverge silently, and
	 *   here they would diverge precisely on the day someone tunes the step.
	 */
	char scala[256];
	size_t usati = 0;
	ModoQualita m = richiesta->modo;
	int q = richiesta->qualita;
	/* ⛔ WHERE A DELTA STOPS, inside the same string — 23 Aug 2026.  The
	 *    line said *"a DELTA is abandoned after N re-encodings"* and then
	 *    drew the WHOLE ladder: whoever read it counted the rungs and believed
	 *    it walked all of them.  ⚠ And until today it did not walk N: it walked
	 *    **all of them**, because the count was dead code (the box in
	 *    `comprimi_comune()`).  ⇒ Now a delta makes `RICODIFICHE_MASSIME`
	 *    encodings, and the mark in the ladder says exactly on which rung
	 *    it stops.  ⭐ A line that declares a ladder the code does not walk
	 *    is worse than no line. */
	bool delta_si_ferma = false;
	scala[0] = 0;
	for (unsigned i = 0; i <= RICODIFICHE_MASSIME; i++) {
		if (i) {
			if (m == CODIFICATORE_QUALITA_LOSSLESS) {
				m = CODIFICATORE_QUALITA_CRF;
				q = CRF_DI_EMERGENZA;
			} else if (q >= 51) {
				break; /* the bottom: there is nothing below */
			} else {
				q += CRF_PASSO;
				if (q > 51)
					q = 51;
			}
		}
		if (usati + 72 >= sizeof(scala))
			break;
		if (i) {
			/* ⚠ `i == RICODIFICHE_MASSIME` is the first rung a delta does NOT
			 *   try: only a key gets there. */
			bool solo_chiave = (i == RICODIFICHE_MASSIME);
			int sep = snprintf(scala + usati, sizeof(scala) - usati, "%s",
			                   solo_chiave ? " ⟨a DELTA stops here⟩ → " : " → ");
			if (sep < 0)
				break;
			usati += (size_t) sep;
			if (solo_chiave)
				delta_si_ferma = true;
		}
		int n = (m == CODIFICATORE_QUALITA_LOSSLESS)
		            ? snprintf(scala + usati, sizeof(scala) - usati, "%s", nome_modo(m))
		            : snprintf(scala + usati, sizeof(scala) - usati, "%s %d", nome_modo(m), q);
		if (n < 0)
			break;
		usati += (size_t) n;
	}
	registro_dice(REG_CODIFICA,
	              "the degradation ladder, with the values in force: %s — step %d "
	              "(CRF_PASSO), bottom 51, exit from lossless at CRF %d "
	              "(CRF_DI_EMERGENZA).  ⛔ A DELTA makes %d encodings in all "
	              "(RICODIFICHE_MASSIME), that is %d descents, and each one is TRIED: %s.  "
	              "⚠ A KEY is never abandoned (RCP.md §5.2): for a key the ladder is "
	              "walked all the way down.  ⭐ And every RETRY comes out as a KEY even if the "
	              "frame was a delta: the descent reopens the context and throws away the "
	              "references",
	              scala, CRF_PASSO, CRF_DI_EMERGENZA, RICODIFICHE_MASSIME,
	              RICODIFICHE_MASSIME - 1,
	              delta_si_ferma
	                  ? "the ⟨⟩ in the ladder is the rung on which it stops, and those to "
	                    "its right are seen only by a key"
	                  : "the ladder is shorter than that, so a delta walks it "
	                    "ALL and, if not even the bottom is enough, it does not leave — the count of "
	                    "encodings does not get the chance to bite");

	/*
	 * ⛔⭐ AND THE SWITCH'S VALUE IN FORCE IS WRITTEN IN BOTH
	 *     CASES, on **and** off.  ⚠ It is not zeal: a climb that is off and a
	 *     climb that never had the chance to trigger produce the
	 *     **same** log, that is no line — and whoever rereads a bench would not
	 *     know which of the two it measured.  It is the reason `*come`
	 *     exists in `chiave_intervallo_ms()` (`webtransport.c`).
	 */
	registro_dice(REG_CODIFICA,
	              risalita_accesa
	                  ? "⭐ PHASE 9: the quality CLIMB is ON — after %u "
	                    "frames in a row below %u bytes we go back up by ONE rung of "
	                    "%d, and **never** beyond the requested working point (%s).  ⚠ Every "
	                    "step, down and up, ends up in the log (I1), and on every "
	                    "relapse the wait DOUBLES up to %u frames"
	                  : "the quality climb is OFF (invariant I6): once it has gone "
	                    "down, the quality stays down for the whole session — and "
	                    "this line is the why, not \"it never had to trigger\".  "
	                    "⚠ It is turned on with `codificatore_qualita_risale(true)`, and while "
	                    "off these numbers (%u frames, %u bytes, rung %d, "
	                    "working point %s, wait ceiling %u) have no effect",
	              RISALITA_ATTESA, RISALITA_MARGINE, CRF_PASSO, punto, RISALITA_ATTESA_MAX);

	/*
	 * ⛔⭐ AND THE BANDWIDTH CEILING TOO IS WRITTEN IN BOTH CASES, for the
	 *     same reason as the climb: a ceiling that is off and a ceiling that never
	 *     had the chance to bite would give the **same** log, and whoever
	 *     rereads a bench would not know which of the two it measured.
	 *
	 */
	if (tetto_pavimento_mbit)
		registro_dice(REG_CODIFICA,
		              "⭐ PHASE 9: the BANDWIDTH CEILING is ON over a floor of %u "
		              "Mbit/s — mode %s (asked for by name, never `auto`), working point "
		              "%" PRId64 " kbit/s, wire %" PRId64 " kbit/s (⛔ NEVER equal: that is "
		              "R31), buffer %d bits = **%u ms** (CODER.md §1-bis grants 50 "
		              "to ALL of our part; v1 took 500 and nobody "
		              "said so).  ⚠ QP %d stays and under QVBR it is the quality "
		              "factor.  ⭐ Whether it obeyed is said by the BYTES, the «video "
		              "bandwidth» line every %u s",
		              tetto_pavimento_mbit, modo_bitrate_voluto().nome,
		              tetto_punto() / 1000, tetto_filo() / 1000, tetto_serbatoio_bit(),
		              (unsigned) ((uint64_t) tetto_serbatoio_bit() * 1000 / tetto_filo()),
		              c->qualita_corrente, BANDA_FINESTRA_US / 1000000u);
	else
		registro_dice(REG_CODIFICA,
		              "the bandwidth ceiling is OFF (invariant I6): mode %s, QP %d "
		              "fixed, and ⛔ **nobody says no to the bandwidth** — `[M]` 23 Aug "
		              "2026 a film with grain at full screen asks for 58.7 Mbit/s, "
		              "that is 293 %% of the floor of 20.  ⚠ And this line is the "
		              "why, not \"it never had to bite\".  It is turned on with "
		              "`codificatore_tetto_banda(20)`, and while off its numbers (wire "
		              "at %u %% of the floor, working point at %u %% of the wire, buffer %u "
		              "ms) have no effect",
		              modo_bitrate_voluto().nome, c->qualita_corrente,
		              TETTO_QUOTA_FILO, TETTO_QUOTA_PUNTO, TETTO_VBV_MS);
	return c;
}

void codificatore_libera(Codificatore *c)
{
	if (!c)
		return;
	c->pacchetto_in_mano = false;
	free(c->appoggio);
	c->appoggio = NULL;
	/* ⛔ Before the device, and in this order: the imported surfaces, the
	 *    conversion context and the encoder live ON the device,
	 *    and freeing them afterwards would mean asking a display that is no longer
	 *    there. */
	butta_le_importate(c, "the encoder is closing");
	chiudi_vpp(c);
	chiudi_contesto(c);
	/* ⚠ The device is closed LAST — the one of the open route. */
	if (c->strada == STRADA_VULKAN)
		vulkanvideo_chiudi_dispositivo(c->vk_dispositivo);
	else if (c->hardware)
		vadiretta_chiudi_dispositivo(&c->dispositivo);
	free(c->uscita);
	free(c);
}

const char *codificatore_nome(const Codificatore *c)
{
	return c ? c->nome : "(none)";
}

bool codificatore_vulkan_sul_nodo(const char *nodo)
{
	VulkanVideoCapacita cap;
	char errore[256] = { 0 };

	memset(&cap, 0, sizeof cap);
	if (!nodo || !vulkanvideo_capacita(nodo, &cap, errore, sizeof errore))
		return false;
	return cap.h264.codifica || cap.hevc.codifica;
}

const char *codificatore_strada(const Codificatore *c)
{
	return c ? nome_strada(c->strada) : "";
}

const CodificatoreConfessione *codificatore_confessione(const Codificatore *c)
{
	return c ? &c->conf : NULL;
}

void codificatore_chiedi_chiave(Codificatore *c)
{
	if (c)
		c->prossimo_chiave = true;
}

bool codificatore_ridimensiona(Codificatore *c, uint32_t larghezza, uint32_t altezza,
                               char *errore, size_t errore_byte)
{
	if (!c)
		return false;
	if (larghezza == c->richiesta.larghezza && altezza == c->richiesta.altezza)
		return true;
	if ((larghezza & 1) || (altezza & 1)) {
		di(errore, errore_byte, "%ux%u: 4:2:0 wants even sizes", larghezza, altezza);
		return false;
	}

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⛔⛔ NOT WITH A PACKET IN HAND — it is the ONLY place in the file where
	 *      `chiudi_contesto()` could get there without a guard.
	 *
	 * `chiudi_contesto()` frees the encoder, and the bytes it holds.  And
	 * `comprimi_comune()` delivers `fuori->dati`, a pointer into `c->uscita`,
	 * valid until `codificatore_rilascia()`
	 * (`codificatore.h:439`).  ⇒ A caller that resized while still holding
	 * the frame would read freed memory, and it is **the same form** as the
	 * defect that on 23 Aug 2026 killed the server in the transport: below a
	 * certain size freed memory stays readable, and the fault shows up
	 * elsewhere, much later.
	 *
	 * ⭐ Today it is not reachable — `figlio.c:7426` resizes in the main
	 *   loop, and `codifica_e_manda()` releases at `figlio.c:4905` before
	 *   returning — but "it is not reachable" was true for the other two as well, and
	 *   here it cost nothing to make it **impossible** instead of lucky.
	 *
	 * ⚠ It REFUSES instead of unhooking on the sly: that would leave the caller's pointer
	 *   dangling anyway, and silently on top of that.  By refusing,
	 *   the frame stays alive and valid and the caller receives an error that
	 *   names it.
	 * ═══════════════════════════════════════════════════════════════════════ */
	if (c->pacchetto_in_mano) {
		di(errore, errore_byte,
		   "⛔ resize to %ux%u with the previous frame STILL IN HAND: "
		   "reopening now would free the bytes the caller is reading.  "
		   "⇒ `codificatore_rilascia()` BEFORE resizing",
		   larghezza, altezza);
		registro_dice(REG_CODIFICA, "%s", errore);
		return false;
	}

	/* ⛔ It really reopens.  An encoder opened at one size and fed at
	 *    another does not protest: it crops or pads, and the defect shows only
	 *    in the picture.
	 * ⚠ In hardware the STORE is reopened too — the surfaces have the size
	 *   inside, and reusing them would mean uploading 1920 rows into 1280. */
	chiudi_contesto(c);
	c->richiesta.larghezza = larghezza;
	c->richiesta.altezza = altezza;
	c->prima_codifica_fatta = false;
	c->conf.letto_dal_flusso = false;
	/* ⛔ AND THE COUNT OF CALM STARTS AGAIN FROM ZERO: 120 comfortable frames at
	 *    1280x720 are no proof at all that there is room at 7680x4320.  ⚠ Without
	 *    this line the first frame at the new canvas would trigger an
	 *    **unmeasured** climb, which is precisely what I1 forbids.
	 *    ⭐ `qualita_fallita` instead is KEPT: forgetting it would widen the
	 *      meshes, and the direction in which to err is caution. */
	c->sotto_margine = 0;
	/* ⛔ And the window of the third witness restarts too: 10 s of bytes at
	 *    1280x720 and 10 s at 7680x4320 under the same line would be two measurements
	 *    with the same label. */
	c->banda_t0_us = 0;
	c->banda_byte = 0;
	c->banda_fotogrammi = 0;
	c->banda_massimo = 0;

	if (apri_contesto(c, errore, errore_byte) < 0)
		return false;
	if (apri_fotogrammi(c, errore, errore_byte) < 0)
		return false;

	/* ⛔ `RCP.md` §5.2: the first frame at the new size MUST be a
	 *    key, and a REAL key.  `apri_contesto` has already demanded it; the line
	 *    stays because the rule is written here, not elsewhere. */
	c->prossimo_chiave = true;
	registro_dice(REG_CODIFICA,
	              "new canvas %ux%u: reopened, and the next frame is a key "
	              "(RCP.md §5.2)", larghezza, altezza);
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐⭐ ZERO COPY — from the compositor's DMA-BUF to the encoder's
 *      surface, without passing through system memory
 *
 * ⛔ WHAT THIS ROUTE REMOVES, and they are three stretches measured `[M]` on 22
 *    Aug 2026 inside the product (agent C, medians over 512 frames):
 *
 *      the copy (`memcpy` in the capture slot)       1.65 ms
 *      the CPU conversion (then in libswscale)        8.15 ms
 *      the upload (memory → GPU)                      1.16 ms
 *
 * ⛔⛔ AND WHAT IT DOES **NOT** REMOVE, and it is the half nobody expects: the
 *      colour conversion **must be done anyway**.  The compositor delivers
 *      BGRx; the hardware encoder wants NV12.  ⇒ The difference is not
 *      "no conversion": it is **who converts** — the GPU instead of the CPU, on the
 *      memory it already has under it instead of on eight megabytes pushed twice
 *      across the bus.
 *
 * ⇒ The cost of the GPU conversion ends up in `us_conversione`, under the
 *   same label as before, **on purpose**: it is the same quantity done in another
 *   place, and putting it in a new entry would make the comparison with
 *   "before" impossible.  ⛔ `us_caricamento` instead goes to **0**, and there zero
 *   means "this stretch is no longer there", not "it is free".
 *
 * ⚠ AND THERE IS AN EXPLICIT SYNCHRONISATION (`vaSyncSurface`) after the
 *   conversion, which could be removed: without it, the call would return before
 *   the GPU has finished and the number would look nicer.  ⛔ It is there for two
 *   reasons, and the second is worth more than the first:
 *     1. the measured time is the REAL one, not that of the order issued;
 *     2. ⭐⭐ **it is the release**: when this function returns, the GPU has finished
 *        reading the compositor's DMA-BUF, and only then can whoever captured it
 *        give it back.  Removing the synchronisation here would bring back
 *        the defect of `LEZIONI.md` §8 — two screens alternating, and
 *        no error.
 * ═══════════════════════════════════════════════════════════════════════════ */

static VADisplay display_di(Codificatore *c)
{
	/* ⛔ Only on the VA-API route: Vulkan's zero copy lives inside
	 *    `vulkanvideo.c` (import, cache, conversion) and does not pass through here. */
	return (c->hardware && c->strada == STRADA_VAAPI) ? c->dispositivo.display : NULL;
}

/*
 * ⭐⭐ PHASE 19 — THE ROUND OF ONE FRAME ON VULKAN VIDEO, in a single shot:
 *     `vulkanvideo.c` converts (shader) and encodes within the same call,
 *     and returns the three times separately as `CodificatoreFotogramma` keeps them.
 *     ⚠ On the zero copy `us_caricamento` is 0 and means "not there"; from
 *     memory it is the upload of the BGRx to the card (the shader is in
 *     `us_conversione`).  The bytes go into `c->uscita` as for VA-API, and from
 *     there on the common body no longer knows which route produced them.
 */
static bool codifica_vulkan(Codificatore *c, const uint8_t *pixel, uint32_t passo,
                            const CodificatoreSuperficie *s, CodificatoreFotogramma *fuori)
{
	const uint8_t *dati = NULL;
	size_t byte = 0;
	VulkanVideoTempi t;
	char errore[256] = { 0 };
	bool ok;

	memset(&t, 0, sizeof t);
	if (s) {
		VulkanVideoSuperficie vs = { .fd = s->fd, .offset = s->offset, .stride = s->stride,
			                         .larghezza = s->larghezza, .altezza = s->altezza,
			                         .formato_drm = s->formato_drm, .modificatore = s->modificatore,
			                         .generazione = s->generazione };
		ok = vulkanvideo_codifica_dmabuf(c->vk, &vs, c->prossimo_chiave, &dati, &byte, &t, errore,
		                                 sizeof errore);
		if (ok && !c->detto_copia_zero) {
			c->detto_copia_zero = true;
			registro_dice(REG_CODIFICA,
			              "⭐⭐ ZERO COPY in force (Vulkan): the compositor's DMA-BUF (fd %d, "
			              "%ux%u, stride %u, modifier 0x%llx) is imported as a Vulkan "
			              "image and converted to %s BY THE SHADER on the card — no "
			              "`memcpy`, no CPU conversion, no upload.  ⚠ The "
			              "conversion remains and costs %llu us (with the fence wait inside)",
			              s->fd, s->larghezza, s->altezza, s->stride,
			              (unsigned long long) s->modificatore,
			              c->richiesta.profondita == 10 ? "P010" : "NV12",
			              (unsigned long long) t.us_conversione);
		}
	} else {
		if (!FORMATO_PIXEL_IMPACCHETTATO(c->richiesta.formato)) {
			registro_dice(REG_CODIFICA,
			              "⛔ the Vulkan route takes only BGRx/RGBx from memory, and "
			              "the input is not: `vulkan_adatta()` should have stopped it earlier");
			return false;
		}
		ok = vulkanvideo_codifica_memoria(c->vk, pixel, passo ? passo : c->richiesta.larghezza * 4u,
		                                  c->richiesta.formato == CODIFICATORE_PIXEL_RGBX
		                                      ? VULKANVIDEO_RGBX
		                                      : VULKANVIDEO_BGRX,
		                                  c->prossimo_chiave, &dati, &byte, &t, errore,
		                                  sizeof errore);
	}
	if (!ok) {
		registro_dice(REG_CODIFICA, "⛔ Vulkan Video did not encode: %s", errore);
		return false;
	}
	if (!metti_in_uscita(c, dati, byte))
		return false;
	fuori->us_conversione = t.us_conversione;
	fuori->us_caricamento = t.us_caricamento;
	fuori->us_codifica = t.us_codifica;
	fuori->trattenuto = false;
	c->pacchetto_in_mano = true;
	return true;
}

/* Throws away all the imported surfaces.  ⛔ It is called when the generation of the
 * producer's buffers changes, and at closing: a surface that outlives
 * the `pw_buffer` it described points to someone else's memory. */
static void butta_le_importate(Codificatore *c, const char *perche)
{
	VADisplay dpy = display_di(c);

	if (!c->quante_importate)
		return;
	if (dpy)
		for (unsigned i = 0; i < c->quante_importate; i++)
			vaDestroySurfaces(dpy, &c->importate[i].superficie, 1);
	registro_dice(REG_CODIFICA,
	              "⭐ throwing away the %u imported surfaces: %s.  ⛔ Keeping them would mean giving "
	              "VA-API a descriptor that no longer describes anything — and the symptom "
	              "would be an OLD picture, with no error at all",
	              c->quante_importate, perche);
	c->quante_importate = 0;
}

/*
 * Imports the DMA-BUF as a VA-API surface, or returns the one already imported.
 *
 * ⛔ The cache compares on EVERYTHING that describes the buffer — descriptor,
 *    size, stride, offset, format and modifier — and not on the `fd` alone.
 *    ⚠ Two different buffers with the same descriptor number do exist (numbers
 *    are recycled), and the generation separates them; but even if the rest did not
 *    match, importing again costs once and getting it wrong costs the whole
 *    session.
 */
static VASurfaceID importa_dmabuf(Codificatore *c, const CodificatoreSuperficie *s)
{
	VADisplay dpy = display_di(c);
	VADRMPRIMESurfaceDescriptor d;
	VASurfaceAttrib attributi[2];
	VASurfaceID superficie = VA_INVALID_ID;
	VAStatus stato;
	unsigned i;

	if (!dpy)
		return VA_INVALID_ID;

	/* ⛔ The generation BEFORE everything: if the producer has redone its buffers,
	 *    what is in the cache no longer describes anything. */
	if (c->cache_nata && c->generazione_cache != s->generazione)
		butta_le_importate(c, "the producer has redone its buffers");
	c->generazione_cache = s->generazione;
	c->cache_nata = true;

	for (i = 0; i < c->quante_importate; i++)
		if (c->importate[i].fd == s->fd && c->importate[i].l == s->larghezza
		    && c->importate[i].a == s->altezza && c->importate[i].stride == s->stride
		    && c->importate[i].offset == s->offset
		    && c->importate[i].formato_drm == s->formato_drm
		    && c->importate[i].modificatore == s->modificatore)
			return c->importate[i].superficie;

	memset(&d, 0, sizeof d);
	/*
	 * ⛔ THE VA-API FOURCC IS NOT THE DRM ONE, and the two look alike
	 *    enough to be mistaken for each other.  ⚠ `VA_FOURCC_BGRX` is what ffmpeg
	 *    pairs with `AV_PIX_FMT_BGR0` and with `DRM_FORMAT_XRGB8888`
	 *    (`hwcontext_vaapi.c`), that is B,G,R,ignored **in the order of the bytes in
	 *    memory** — the same that `cattura.c` negotiates as `BGRx`.  ⛔ Getting it wrong
	 *    gives no error: it gives red and blue swapped.
	 * ⚠ Here the two this module knows how to receive are declared; for the others we
	 *   refuse instead of guessing.
	 */
	if (s->formato_drm == DRM_FORMAT_XRGB8888)
		d.fourcc = VA_FOURCC_BGRX;
	else if (s->formato_drm == DRM_FORMAT_ARGB8888)
		d.fourcc = VA_FOURCC_BGRA;
	else {
		registro_dice(REG_CODIFICA,
		              "⛔ DRM format 0x%08x cannot be imported: this route knows BGRx and "
		              "BGRA.  ⚠ A fourcc is NOT guessed — a wrong fourcc gives no "
		              "error, it gives swapped colours",
		              s->formato_drm);
		return VA_INVALID_ID;
	}
	d.width = s->larghezza;
	d.height = s->altezza;
	d.num_objects = 1;
	d.objects[0].fd = s->fd;
	d.objects[0].size = s->offset + s->stride * s->altezza;
	d.objects[0].drm_format_modifier = s->modificatore;
	d.num_layers = 1;
	d.layers[0].drm_format = s->formato_drm;
	d.layers[0].num_planes = 1;
	d.layers[0].object_index[0] = 0;
	d.layers[0].offset[0] = s->offset;
	d.layers[0].pitch[0] = s->stride;

	attributi[0].type = VASurfaceAttribMemoryType;
	attributi[0].flags = VA_SURFACE_ATTRIB_SETTABLE;
	attributi[0].value.type = VAGenericValueTypeInteger;
	attributi[0].value.value.i = VA_SURFACE_ATTRIB_MEM_TYPE_DRM_PRIME_2;
	attributi[1].type = VASurfaceAttribExternalBufferDescriptor;
	attributi[1].flags = VA_SURFACE_ATTRIB_SETTABLE;
	attributi[1].value.type = VAGenericValueTypePointer;
	attributi[1].value.value.p = &d;

	stato = vaCreateSurfaces(dpy, VA_RT_FORMAT_RGB32, s->larghezza, s->altezza, &superficie, 1,
	                         attributi, 2);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA,
		              "⛔ the DMA-BUF was not imported (vaCreateSurfaces: %s) — fd %d, "
		              "%ux%u, stride %u, offset %u, modifier 0x%llx.  ⚠ There is NO silent "
		              "fallback to the copy: the caller writes it",
		              vaErrorStr(stato), s->fd, s->larghezza, s->altezza, s->stride,
		              s->offset, (unsigned long long) s->modificatore);
		return VA_INVALID_ID;
	}

	if (c->quante_importate >= IMPORTATE_MAX)
		butta_le_importate(c, "the cache is full and starts over");
	i = c->quante_importate++;
	c->importate[i].fd = s->fd;
	c->importate[i].l = s->larghezza;
	c->importate[i].a = s->altezza;
	c->importate[i].stride = s->stride;
	c->importate[i].offset = s->offset;
	c->importate[i].formato_drm = s->formato_drm;
	c->importate[i].modificatore = s->modificatore;
	c->importate[i].superficie = superficie;
	return superficie;
}

/* Opens the GPU conversion context, at the size in force.
 * ⛔ It is reopened when the size changes: a VPP context carries the size inside,
 *    exactly like the surface store. */
static bool apri_vpp(Codificatore *c, uint32_t larghezza, uint32_t altezza)
{
	VADisplay dpy = display_di(c);
	VAStatus stato;

	if (!dpy)
		return false;
	if (c->vpp_aperto && c->vpp_l == larghezza && c->vpp_a == altezza)
		return true;
	if (c->vpp_aperto) {
		vaDestroyContext(dpy, c->vpp_contesto);
		vaDestroyConfig(dpy, c->vpp_configurazione);
		c->vpp_aperto = false;
	}
	/*
	 * ⛔ AND HERE WE ASK THE DRIVER, not ffmpeg: `VAEntrypointVideoProc` is there or
	 *    it is not, and if it is not this route **does not exist on this machine**.
	 *    ⚠ It is the same rule by which `apri_dispositivo()` asks for the encoding
	 *    entrypoints: "I asked it for it" and "it has it" look the same
	 *    until you look (`LEZIONI.md` §1.11).
	 */
	stato = vaCreateConfig(dpy, VAProfileNone, VAEntrypointVideoProc, NULL, 0,
	                       &c->vpp_configurazione);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA,
		              "⛔ this card has no GPU conversion (VAProfileNone / "
		              "VAEntrypointVideoProc: %s): zero copy is NOT viable here, "
		              "and it is declared instead of falling back silently",
		              vaErrorStr(stato));
		return false;
	}
	stato = vaCreateContext(dpy, c->vpp_configurazione, (int) larghezza, (int) altezza,
	                        VA_PROGRESSIVE, NULL, 0, &c->vpp_contesto);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA,
		              "⛔ the %ux%u conversion context did not open: %s",
		              larghezza, altezza, vaErrorStr(stato));
		vaDestroyConfig(dpy, c->vpp_configurazione);
		return false;
	}
	c->vpp_aperto = true;
	c->vpp_l = larghezza;
	c->vpp_a = altezza;
	return true;
}

static void chiudi_vpp(Codificatore *c)
{
	VADisplay dpy = display_di(c);

	if (!c->vpp_aperto || !dpy)
		return;
	vaDestroyContext(dpy, c->vpp_contesto);
	vaDestroyConfig(dpy, c->vpp_configurazione);
	c->vpp_aperto = false;
}

/*
 * The RGB → NV12 conversion on the GPU, and ⛔ **the matrix is IMPOSED**, as
 * `sws_setColorspaceDetails` imposed it on the memory route.
 *
 * ⛔ Without these four lines the driver would use its default, which is not
 *    written anywhere in our code: two versions of iHD could
 *    convert differently and nobody would notice by looking at the picture.
 *    ⚠ And the right pair is the one the old route declared:
 *    **FULL-range RGB source, LIMITED-range BT.709
 *    destination**.  Getting the direction wrong gives no error: it gives a washed-out or
 *    over-contrasted picture, that is a defect no log line names.
 */
static bool converti_sulla_gpu(Codificatore *c, VASurfaceID sorgente, VASurfaceID destinazione)
{
	VADisplay dpy = display_di(c);
	VAProcPipelineParameterBuffer p;
	VABufferID buffer = VA_INVALID_ID;
	VAStatus stato, fine;
	VARectangle regione;

	if (!dpy || !c->vpp_aperto)
		return false;

	memset(&p, 0, sizeof p);
	p.surface = sorgente;
	/* ═══════════════════════════════════════════════════════════════════════
	 * ⛔⛔⛔ THE TWO REGIONS ARE DECLARED, AND LEAVING THEM `NULL` IS A REAL
	 *       DEFECT — found by refuting, on 22 Aug 2026, and the milliseconds were
	 *       already beautiful.
	 *
	 * `NULL` does not mean "1:1": it means **the whole surface**.  ⛔ And the
	 * destination surface **is not 1920x1080**: `av_hwframe_ctx`
	 * allocates it aligned, and on iHD at 1920x1080 it comes out **1920x1088**.  ⇒ With the
	 * regions `NULL` the VPP **SCALES** the picture from 1080 to 1088 rows — an
	 * enlargement of 0.74 %, which is not visible by eye and which
	 * **destroys every structure at pixel level**.
	 *
	 * ⭐⭐ AND THE BENCH SAW IT AND THE COLOUR DID NOT: `[M]` the colour statistics
	 *     of the two streams matched within **0.17 levels out of 255** (a 0.7 % scale
	 *     does not move an average), while the drag bench
	 *     read **0 marks out of 903** against 870 out of 870 for the other route, with
	 *     the contrast between the cells dropped to 0.245, below the minimum of 0.25.
	 *     ⇒ Two instruments, and only one of the two could see this defect.
	 *
	 * ⚠ And the symptom for the user would have been **a slightly
	 *   blurred and slightly stretched desktop**, with no log line at all.
	 * ═══════════════════════════════════════════════════════════════════════ */
	regione.x = 0;
	regione.y = 0;
	regione.width = (unsigned short) c->vpp_l;
	regione.height = (unsigned short) c->vpp_a;
	p.surface_region = &regione;
	p.output_region = &regione;
	p.output_background_color = 0xff000000;
	p.filter_flags = VA_FRAME_PICTURE;
	p.filters = NULL;
	p.num_filters = 0;
	p.surface_color_standard = VAProcColorStandardNone; /* the source is RGB */
	p.output_color_standard = VAProcColorStandardBT709;
	p.input_color_properties.color_range = VA_SOURCE_RANGE_FULL;
	p.output_color_properties.color_range = VA_SOURCE_RANGE_REDUCED;

	stato = vaBeginPicture(dpy, c->vpp_contesto, destinazione);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA, "⛔ vaBeginPicture: %s", vaErrorStr(stato));
		return false;
	}
	stato = vaCreateBuffer(dpy, c->vpp_contesto, VAProcPipelineParameterBufferType, sizeof p, 1,
	                       &p, &buffer);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA, "⛔ vaCreateBuffer: %s", vaErrorStr(stato));
		vaEndPicture(dpy, c->vpp_contesto);
		return false;
	}
	stato = vaRenderPicture(dpy, c->vpp_contesto, &buffer, 1);
	if (stato != VA_STATUS_SUCCESS)
		registro_dice(REG_CODIFICA, "⛔ vaRenderPicture: %s", vaErrorStr(stato));
	fine = vaEndPicture(dpy, c->vpp_contesto);
	vaDestroyBuffer(dpy, buffer);
	if (stato != VA_STATUS_SUCCESS || fine != VA_STATUS_SUCCESS) {
		if (fine != VA_STATUS_SUCCESS)
			registro_dice(REG_CODIFICA, "⛔ vaEndPicture: %s", vaErrorStr(fine));
		return false;
	}
	/* ⛔⭐ AND HERE WE REALLY WAIT — see the box at the top: this line IS the
	 *     release.  When it returns, the GPU has finished reading the
	 *     compositor's buffer, and whoever captured it can give it back. */
	stato = vaSyncSurface(dpy, destinazione);
	if (stato != VA_STATUS_SUCCESS) {
		registro_dice(REG_CODIFICA, "⛔ vaSyncSurface: %s", vaErrorStr(stato));
		return false;
	}
	return true;
}

/*
 * Prepares the encoder's frame starting from the DMA-BUF — the half of the
 * zero copy that sits inside the attempts loop.
 *
 * ⛔ It is redone on every attempt, and it is not waste: if the frame breaks the
 *    16 MiB ceiling, `abbassa_qualita()` **closes and reopens the context and the
 *    store**, so the destination surface of the previous round no longer
 *    exists.  ⚠ The SOURCE surface instead stays: it is imported on the device,
 *    which nobody closes.
 */
static bool prepara_dalla_scheda(Codificatore *c, const CodificatoreSuperficie *s, uint64_t *us,
                                 uint64_t *us_carico)
{
	uint64_t t0 = adesso_us();
	VASurfaceID sorgente, destinazione;

	/* ⛔ The upload to the GPU IS NOT THERE on this route, and the zero says so.
	 *    ⚠ Whoever reads the table of stretches must be able to tell "free" from
	 *    "does not exist", and here the first-time log line writes it. */
	*us_carico = 0;

	if (!apri_vpp(c, c->richiesta.larghezza, c->richiesta.altezza))
		return false;
	sorgente = importa_dmabuf(c, s);
	if (sorgente == VA_INVALID_ID)
		return false;

	/* ⭐ Phase 18: the input surface is given by vadiretta, from its store
	 *    (a new one on every round, as yesterday with libavutil's store). */
	destinazione = vadiretta_superficie_ingresso(c->va);
	if (destinazione == VA_INVALID_ID) {
		registro_dice(REG_CODIFICA, "⛔ no input surface (%d ready)",
		              SUPERFICI_PRONTE);
		return false;
	}
	if (!converti_sulla_gpu(c, sorgente, destinazione))
		return false;
	c->superficie_pronta = destinazione;
	*us = adesso_us() - t0;

	if (!c->detto_copia_zero) {
		c->detto_copia_zero = true;
		registro_dice(REG_CODIFICA,
		              "⭐⭐ ZERO COPY in force: the compositor's DMA-BUF (fd %d, %ux%u, "
		              "stride %u, modifier 0x%llx) is imported as a VA-API surface and "
		              "converted to %s BY THE GPU — no `memcpy`, no CPU "
		              "conversion, no upload.  ⚠ The conversion remains and costs "
		              "%llu us: what changed is WHO does it, not that it must be done",
		              s->fd, s->larghezza, s->altezza, s->stride,
		              (unsigned long long) s->modificatore,
		              c->richiesta.profondita == 10 ? "P010" : "NV12",
		              (unsigned long long) *us);
	}
	return true;
}

/*
 * Fills the frame that enters the encoder, from the caller's pixels.
 *
 * ⭐ In hardware there are TWO steps and they are timed SEPARATELY:
 *      `us_conversione`  `colori709.c`, in system memory — the stretch that
 *                        was already there;
 *      `us_caricamento`  system memory → GPU — ⛔ the stretch that the phase 8
 *                        zero copy exists to remove.  Adding it to the
 *                        encoding would make invisible how much that work is worth.
 *
 * ⛔⭐ PHASE 18, AND THE ROUTE IS BACK TO WHAT IT WAS BEFORE: CPU conversion
 *     and then upload of the NV12/P010 planes.  In the first draft of the
 *     card line the BGRx were uploaded as they were into an RGB surface and
 *     the VPP converted them; `[M]` 30 Sep 2026 (`banchi/18-scheda/18-confronto.sh`,
 *     120 frames of fake desktop) that route was WORSE than the
 *     CPU conversion: Intel 1080p H.264 −1 dB and +82 % bytes, HEVC −4 dB
 *     and +255 %; Radeon −1…−6 dB.  ⇒ The VPP stays with the zero copy, where the
 *     frame is already on the card and there is no CPU to call on.
 */
static bool prepara_fotogramma(Codificatore *c, const uint8_t *pixel, uint32_t passo,
                               uint64_t *us, uint64_t *us_carico)
{
	uint64_t t0 = adesso_us();

	*us_carico = 0;
	*us = 0;

	char errore[256] = { 0 };
	const uint32_t l = c->richiesta.larghezza, a = c->richiesta.altezza;
	VASurfaceID destinazione = vadiretta_superficie_ingresso(c->va);
	if (destinazione == VA_INVALID_ID) {
		registro_dice(REG_CODIFICA, "⛔ no input surface (%d ready)",
		              SUPERFICI_PRONTE);
		return false;
	}
	if (FORMATO_PIXEL_IMPACCHETTATO(c->richiesta.formato)) {
		if (!c->appoggio) {
			registro_dice(REG_CODIFICA, "⛔ the NV12/P010 staging buffer was not allocated");
			return false;
		}
		Colori709Ordine ordine = (c->richiesta.formato == CODIFICATORE_PIXEL_RGBX)
		                             ? COLORI709_RGBX
		                             : COLORI709_BGRX;
		uint32_t passo_pixel = passo ? passo : l * 4u;
		bool ok, caricato;
		uint64_t t1;
		if (c->richiesta.profondita == 10) {
			uint16_t *y = (uint16_t *) c->appoggio;
			uint16_t *uv = y + (size_t) l * a;
			ok = colori709_a_p010(pixel, passo_pixel, l, a, ordine, y, l * 2u, uv, l * 2u);
			*us = adesso_us() - t0;
			t1 = adesso_us();
			caricato = ok && vadiretta_carica_p010(c->va, destinazione, y, l * 2u, uv, l * 2u,
			                                       errore, sizeof errore);
		} else {
			uint8_t *y = c->appoggio;
			uint8_t *uv = y + (size_t) l * a;
			ok = colori709_a_nv12(pixel, passo_pixel, l, a, ordine, y, l, uv, l);
			*us = adesso_us() - t0;
			t1 = adesso_us();
			caricato = ok && vadiretta_carica_nv12(c->va, destinazione, y, l, uv, l, errore,
			                                       sizeof errore);
		}
		if (!ok) {
			registro_dice(REG_CODIFICA, "⛔ the colour conversion refused %ux%u", l, a);
			return false;
		}
		if (!caricato) {
			registro_dice(REG_CODIFICA, "⛔ the planes were not uploaded to the card: %s", errore);
			return false;
		}
		*us_carico = adesso_us() - t1;
	} else {
		/* yuv420p10le (the bench) → P010, directly into the input */
		if (!vadiretta_carica_yuv420p10(c->va, destinazione, pixel, passo, errore,
		                                sizeof errore)) {
			registro_dice(REG_CODIFICA, "⛔ the samples were not uploaded to the card: %s",
			              errore);
			return false;
		}
		*us_carico = adesso_us() - t0;
	}
	c->superficie_pronta = destinazione;
	return true;
}

/*
 * ⭐⭐ D-023 — THE FRAME THE DRIVER DOES NOT WRITE (phase 16, 27 Sep 2026).
 *
 * `[M]` Radeon RX 6800, Mesa radeonsi 25.0.7, ffmpeg 7.1.5: `hevc_vaapi` at
 * 2544x1344 makes a stream that DECLARES 2560x1344 — it encodes the multiple of 64
 * (the card's 64 block) and does not write the conformance window.  The
 * same with ffmpeg from the command line, without a line of ours: 3824 → 3840,
 * 1904 → 1920.  H.264 on the same card is right, and so is the Intel.
 * ⛔ The symptom was a session BLACK forever: `forma_va_bene()` rightly refuses
 *    a stream whose size differs from the canvas (RCP.md §6.2), and
 *    Chrome chooses HEVC, and Chrome's canvases are never multiples of 64.
 *
 * ⭐ THE CURE: we write the window ourselves, with `hevc_metadata`/`h264_metadata`
 *    (`crop_right`/`crop_bottom`) — the libavcodec filter, not a hand-written
 *    parser.  `[M]` the 2560 stream cropped to 2544 and decoded against
 *    the original: PSNR 50 dB, that is the picture inside is that one, 1:1, and the 16
 *    extra columns are only padding.
 * ⚠ Only on the packets with the SPS (the keys): the size lives there, and a delta
 *   has nothing to rewrite.  And only if the stream is BIGGER than the
 *   canvas by less than one block: any other difference stays an error, and
 *   `forma_va_bene()` refuses it as before.
 */
/*
 * ⭐ PHASE 18: WE write the frame, bit by bit, and no longer with libavcodec's
 *    `hevc_metadata`/`h264_metadata` filter.  The method: we reread
 *    the SPS up to the cropping flag (the reader above says WHERE it is,
 *    `PosizioneCornice`), we rewrite the head unchanged, then the flag at 1 with the
 *    four offsets (added to those that were there), and we copy the TAIL
 *    of the SPS back as it is, bit by bit, up to the stop bit.  ⛔ It is legitimate
 *    because the SPS syntax is sequential and nothing, after the window,
 *    depends on the position it sits in.  Then the RBSP becomes a NAL again with the
 *    emulation bytes put back (`nal_annexb`) and takes the place of the old one in the
 *    frame.
 *
 * ⚠ The offsets are in chroma units: 4:2:0 ⇒ half the pixels, for both
 *   codecs (H.264 7.4.2.1.1 CropUnitX/Y = 2 with frame_mbs_only;
 *   H.265 7.4.3.2 SubWidthC/SubHeightC = 2).  `dx` and `dy` are even: the
 *   one who decides checks it.
 */
static bool riscrivi_sps_con_cornice(Codificatore *c, size_t sps_offset, size_t sps_byte)
{
	const bool hevc = c->richiesta.codec == CODIFICATORE_HEVC;
	const size_t testa_byte = hevc ? 2 : 1;
	const uint8_t *nal = c->uscita + sps_offset;
	uint8_t *rbsp, *nuovo_rbsp, *nuovo_nal, *fotogramma;
	size_t n, ultimo_uno, nuovo_byte, inizio_codice, dopo, totale;
	CodificatoreConfessione letta;
	PosizioneCornice dove;
	ScrittoreBit w;
	bool ok;

	memset(&letta, 0, sizeof letta);
	memset(&dove, 0, sizeof dove);
	ok = hevc ? leggi_sps_hevc(nal, sps_byte, &letta, &dove)
	          : leggi_sps_h264(nal, sps_byte, &letta, &dove);
	if (!ok || sps_byte <= testa_byte)
		return false;

	rbsp = malloc(sps_byte);
	nuovo_rbsp = malloc(sps_byte + 32);
	nuovo_nal = malloc(sps_byte + 64);
	if (!rbsp || !nuovo_rbsp || !nuovo_nal) {
		free(rbsp);
		free(nuovo_rbsp);
		free(nuovo_nal);
		return false;
	}
	n = togli_emulazione(nal + testa_byte, sps_byte - testa_byte, rbsp, sps_byte);
	/* the stop bit: the LAST 1 of the RBSP */
	ultimo_uno = 0;
	for (size_t b = n * 8; b > 0; b--) {
		if ((rbsp[(b - 1) >> 3] >> (7 - ((b - 1) & 7))) & 1u) {
			ultimo_uno = b - 1;
			break;
		}
	}
	if (dove.bit_dopo > ultimo_uno || dove.bit_flag >= dove.bit_dopo) {
		free(rbsp);
		free(nuovo_rbsp);
		free(nuovo_nal);
		return false;
	}
	sb_apri(&w, nuovo_rbsp, sps_byte + 32);
	sb_copia_bit(&w, rbsp, 0, dove.bit_flag);
	sb_flag(&w, true);
	sb_ue(&w, dove.sx);
	sb_ue(&w, dove.dx + c->cornice_dx / 2);
	sb_ue(&w, dove.su);
	sb_ue(&w, dove.giu + c->cornice_dy / 2);
	sb_copia_bit(&w, rbsp, dove.bit_dopo, ultimo_uno - dove.bit_dopo);
	sb_chiudi_rbsp(&w);
	if (w.traboccato) {
		free(rbsp);
		free(nuovo_rbsp);
		free(nuovo_nal);
		return false;
	}
	nuovo_byte = nal_annexb(nuovo_nal, sps_byte + 64, nal, testa_byte, nuovo_rbsp, sb_byte(&w));
	free(rbsp);
	free(nuovo_rbsp);
	if (!nuovo_byte) {
		free(nuovo_nal);
		return false;
	}
	/* the start code in front of the old SPS: 3 or 4 bytes */
	inizio_codice = sps_offset - 3;
	if (inizio_codice > 0 && c->uscita[inizio_codice - 1] == 0)
		inizio_codice--;
	dopo = sps_offset + sps_byte;
	totale = inizio_codice + nuovo_byte + (c->uscita_byte - dopo);
	fotogramma = malloc(totale);
	if (!fotogramma) {
		free(nuovo_nal);
		return false;
	}
	memcpy(fotogramma, c->uscita, inizio_codice);
	memcpy(fotogramma + inizio_codice, nuovo_nal, nuovo_byte);
	memcpy(fotogramma + inizio_codice + nuovo_byte, c->uscita + dopo, c->uscita_byte - dopo);
	free(nuovo_nal);
	free(c->uscita);
	c->uscita = fotogramma;
	c->uscita_capacita = totale;
	c->uscita_byte = totale;
	return true;
}

static bool cornice_al_suo_posto(Codificatore *c, bool chiave)
{
	const bool hevc = c->richiesta.codec == CODIFICATORE_HEVC;
	size_t off = 0, n = 0;

	if (!hevc && c->richiesta.codec != CODIFICATORE_H264)
		return true;
	if (!chiave)
		return true;

	/* where the SPS is in this frame */
	if (hevc) {
		FormaAnnexB f;
		annexb_leggi(c->uscita, c->uscita_byte, &f);
		off = f.sps_offset;
		n = f.sps_byte;
	} else {
		FormaAnnexB264 f;
		annexb264_leggi(c->uscita, c->uscita_byte, &f);
		off = f.sps_offset;
		n = f.sps_byte;
	}
	if (!n)
		return true; /* no SPS: `forma_va_bene()` decides */

	if (!c->cornice_decisa) {
		CodificatoreConfessione letta;
		memset(&letta, 0, sizeof letta);
		bool ok = hevc ? leggi_sps_hevc(c->uscita + off, n, &letta, NULL)
		               : leggi_sps_h264(c->uscita + off, n, &letta, NULL);
		if (!ok)
			return true; /* no readable SPS: `forma_va_bene()` decides */
		c->cornice_decisa = true;
		c->cornice_attiva = false;
		uint32_t dx = letta.larghezza_flusso - c->richiesta.larghezza;
		uint32_t dy = letta.altezza_flusso - c->richiesta.altezza;
		if (letta.larghezza_flusso < c->richiesta.larghezza ||
		    letta.altezza_flusso < c->richiesta.altezza || (dx == 0 && dy == 0) ||
		    dx >= 64 || dy >= 64 || (dx | dy) & 1u)
			return true;
		c->cornice_attiva = true;
		c->cornice_dx = dx;
		c->cornice_dy = dy;
		registro_dice(REG_CODIFICA,
		              "⭐ D-023: «%s» declares %ux%u for a %ux%u canvas (it encodes the "
		              "multiple of the block and does not write the frame): I write it in the SPS, "
		              "bit by bit, %u columns and %u rows cropped on the right and at the bottom",
		              c->nome_componente, letta.larghezza_flusso, letta.altezza_flusso,
		              c->richiesta.larghezza, c->richiesta.altezza, dx, dy);
	}
	if (!c->cornice_attiva)
		return true;
	if (!riscrivi_sps_con_cornice(c, off, n)) {
		registro_dice(REG_CODIFICA,
		              "⛔ D-023: the frame was not written (SPS of %zu bytes not "
		              "rewritable): this frame does not leave", n);
		return false;
	}
	return true;
}

/*
 * ⛔ THE SHAPE OF THE BYTES IS CHECKED BEFORE SENDING THEM.
 *
 * ⚠ And it is not extra caution: `[M]` 12 Aug 2026 the decoder **does not
 *   protest** when the shape is wrong — it paints black, or paints at the
 *   old size.  The symptom arrives three links further on and does not name the
 *   cause.  Here instead the frame does not leave, and the log says why.
 */
static bool forma_va_bene(Codificatore *c, const uint8_t *dati, size_t byte, bool *chiave)
{
	if (c->richiesta.codec == CODIFICATORE_HEVC) {
		FormaAnnexB f;
		annexb_leggi(dati, byte, &f);
		*chiave = f.primo_vcl_e_chiave;
		if (byte >= 4 && !(dati[0] == 0 && dati[1] == 0 && (dati[2] == 1 || (dati[2] == 0 && dati[3] == 1)))) {
			registro_dice(REG_CODIFICA,
			              "⛔ the frame does not start with a start code: it looks "
			              "length-prefixed (hvcC), and D1 says Annex-B");
			return false;
		}
		if (f.primo_vcl_e_chiave && !f.parametri_prima_dell_idr) {
			registro_dice(REG_CODIFICA,
			              "⛔ key without VPS+SPS+PPS in front: in Annex-B the «key» chunk "
			              "must carry them, or the symptom is a black screen with the frames "
			              "arriving (v1 codificatore.c:268-272)");
			return false;
		}
		if (!c->conf.letto_dal_flusso && f.sps_byte)
			c->conf.letto_dal_flusso =
			    leggi_sps_hevc(dati + f.sps_offset, f.sps_byte, &c->conf, NULL);
	} else if (c->richiesta.codec == CODIFICATORE_H264) {
		FormaAnnexB264 f;

		annexb264_leggi(dati, byte, &f);
		*chiave = f.primo_vcl_e_chiave;
		if (byte >= 4
		    && !(dati[0] == 0 && dati[1] == 0
		         && (dati[2] == 1 || (dati[2] == 0 && dati[3] == 1)))) {
			registro_dice(REG_CODIFICA,
			              "⛔ the H.264 frame does not start with a start code: "
			              "it looks length-prefixed (avcC), and the browser without "
			              "`description` wants Annex-B");
			return false;
		}
		if (f.primo_vcl_e_chiave && !f.parametri_prima_dell_idr) {
			registro_dice(REG_CODIFICA,
			              "⛔ H.264 key without SPS+PPS in front: in Annex-B the "
			              "«key» chunk must carry them, or whoever connects later stays black");
			return false;
		}
		if (!c->conf.letto_dal_flusso && f.sps_byte)
			c->conf.letto_dal_flusso =
			    leggi_sps_h264(dati + f.sps_offset, f.sps_byte, &c->conf, NULL);
	} else {
		FormaObu f;
		obu_leggi(dati, byte, &f);
		*chiave = f.primo_fotogramma_e_chiave;
		if (f.ha_chiave && !f.sequenza_prima_della_chiave) {
			registro_dice(REG_CODIFICA,
			              "⛔ AV1 key without a sequence header in front: a client that "
			              "connects later receives a bare key");
			return false;
		}
		if (!c->conf.letto_dal_flusso && f.seq_byte)
			c->conf.letto_dal_flusso =
			    leggi_sequenza_av1(dati + f.seq_offset, f.seq_byte, &c->conf);
	}

	/* ⛔ SECOND WITNESS: the depth and the size read IN THE BYTES. */
	if (c->conf.letto_dal_flusso) {
		if (c->conf.profondita_flusso != c->richiesta.profondita) {
			registro_dice(REG_CODIFICA,
			              "⛔ E2: %d bits requested, and the stream declares %d",
			              c->richiesta.profondita, c->conf.profondita_flusso);
			c->conf.ha_obbedito = false;
			di(c->conf.perche_no, sizeof(c->conf.perche_no),
			   "the stream carries %d bits instead of %d", c->conf.profondita_flusso,
			   c->richiesta.profondita);
			return false;
		}
		if (c->conf.larghezza_flusso != c->richiesta.larghezza ||
		    c->conf.altezza_flusso != c->richiesta.altezza) {
			registro_dice(REG_CODIFICA,
			              "⛔ the stream SHOWS %ux%u (it encodes %ux%u) and the canvas is "
			              "%ux%u: RCP.md §6.2 wants the size of the canvas in force",
			              c->conf.larghezza_flusso, c->conf.altezza_flusso,
			              c->conf.larghezza_codificata, c->conf.altezza_codificata,
			              c->richiesta.larghezza, c->richiesta.altezza);
			return false;
		}
	}
	return true;
}

/*
 * Reopens at lower quality, for the 16 MiB ceiling.
 *
 * ⭐ `prodotti` are the BYTES that triggered the descent, and they are not an
 *    ornament of the log line: they are the **proof**.  Invariant I1
 *    demands that every descent come from a measurement and not from a suspicion, and
 *    the only way to verify it **from outside**, without trusting the code, is
 *    to find the measurement written next to the threshold it exceeded.  ⇒ A line
 *    in which the bytes were **below** the ceiling would be a descent out of caution,
 *    and that line would denounce it by itself.
 *
 * ⚠ The caller must read them BEFORE throwing away the bytes: afterwards, the number
 *   is gone and the line would say zero.
 */
/*
 * ⭐ THE QUALITY CHANGE LIVES IN ONE PLACE ONLY: the card's context is closed and
 *    reopened (and the store).  ⛔ The next frame is a
 *    KEY, and it is written here.
 */
static bool cambia_qualita(Codificatore *c, char *errore, size_t errore_byte)
{
	chiudi_contesto(c);
	if (apri_contesto(c, errore, errore_byte) < 0)
		return false;
	/* ⛔ The store was reopened together with the context: the frames must be
	 *    rebound, or the next round would upload onto surfaces of a closed
	 *    store. */
	if (apri_fotogrammi(c, errore, errore_byte) < 0)
		return false;
	c->prossimo_chiave = true;
	return true;
}

static bool abbassa_qualita(Codificatore *c, uint32_t prodotti)
{
	char errore[256] = { 0 };
	int prima = c->qualita_corrente;
	ModoQualita modo_prima = c->modo_corrente;

	/* ⛔ THE RELAPSE IS PAID BEFORE KNOWING WHETHER THE DESCENT SUCCEEDS: if we had
	 *    just climbed and the ceiling bites again, the wait doubles.  ⚠ Without
	 *    this, a scene on the edge would make the door slam every two seconds
	 *    at 91-108 ms a time — and the price would be paid by the RATE, that is
	 *    precisely the invariant this cure claims to serve. */
	c->sotto_margine = 0;
	if (c->risalito_da_poco) {
		uint32_t era = c->risalita_attesa;
		c->risalita_attesa = era >= RISALITA_ATTESA_MAX / 2u ? RISALITA_ATTESA_MAX
		                                                     : era * 2u;
		c->risalito_da_poco = false;
		registro_dice(REG_CODIFICA,
		              "⚠ RELAPSE: the ceiling bit right after a climb ⇒ the "
		              "next one waits %u frames instead of %u.  ⛔ It is the defence "
		              "against FLAPPING: every round costs a reopening and a "
		              "key, [M] 91-108 ms on the card",
		              c->risalita_attesa, era);
	}

	if (c->modo_corrente == CODIFICATORE_QUALITA_LOSSLESS) {
		/* ⚠ Lossless does not exist on the card (and since phase 19 not
		 *   elsewhere either): historical branch, we exit to CRF as before. */
		c->modo_corrente = CODIFICATORE_QUALITA_CRF;
		c->qualita_corrente = CRF_DI_EMERGENZA;
	} else {
		/* ⚠ The mode does NOT change: whoever was on QP stays on QP.  Switching to CRF under the
		 *   ceiling would mean changing quantity mid-session, that is two
		 *   measurements under the same label. */
		c->qualita_corrente += CRF_PASSO;
		if (c->qualita_corrente > 51)
			c->qualita_corrente = 51;
	}
	if (c->qualita_corrente == prima && c->modo_corrente == modo_prima)
		return false;

	if (!cambia_qualita(c, errore, sizeof(errore))) {
		registro_dice(REG_CODIFICA, "⛔ did not reopen at lower quality: %s", errore);
		return false;
	}

	/*
	 * ⛔⛔ THE DESCENT IS DECLARED — and until 23 Aug 2026 it was NOT declared.
	 *
	 * `abbassa_qualita()` succeeded **silently**: the only line there was
	 * spoke of KEYS, and for a delta the ladder went down three rungs
	 * without a single line saying so.  ⚠ Invariant I1 demands that *every
	 * descent be declared in the log*, and a silent descent makes it
	 * unverifiable from outside.
	 *
	 * ⭐ AND NEXT TO THE THRESHOLD THERE IS THE MEASUREMENT THAT EXCEEDED IT.  The percentage
	 *    is the proof: **above 100 the descent is measured; at 100 or below it would be
	 *    caution**, that is what I1 forbids — and the line would say so by itself,
	 *    without anyone having to reread this file.
	 *
	 * ⚠ It is written at the CHANGE OF STATE and not on every frame: a line at 30/s is
	 *   the defect of the 30.8 GB of log of 14 Aug (`figlio.c`).
	 */
	registro_dice(REG_CODIFICA,
	              "⛔ QUALITY DOWN: %s %d → %s %d — the frame made %u bytes "
	              "against the ceiling's %u (RCP.md §6.2), that is %u %% of the threshold.  "
	              "⚠ If this percentage were not ABOVE 100 the descent would have "
	              "been out of caution, and I1 forbids it: the measurement is written here so that "
	              "it can be verified from outside without trusting the code",
	              nome_modo(modo_prima), prima, nome_modo(c->modo_corrente),
	              c->qualita_corrente, prodotti, TETTO_FOTOGRAMMA,
	              (unsigned) (((uint64_t) prodotti * 100u) / TETTO_FOTOGRAMMA));
	return true;
}

/*
 * ⭐⭐ A SINGLE RUNG TOWARDS THE REQUESTED QUALITY, AND NO FURTHER — phase 9.
 *
 * ⛔ IT DOES NOT GO BACK TO LOSSLESS: `abbassa_qualita()` leaves LOSSLESS once
 *    and for ever, because re-entering it would mean changing **quantity**
 *    mid-session — the same reason why the mode does not change on the way down.
 *
 * ⛔⛔ AND IT IS NOT CALLED WITH A PACKET IN HAND, and that is the constraint that decides
 *      WHERE this function sits: `chiudi_contesto()` **frees** the
 *      encoder and the bytes it holds, it does not merely unhook them — and after the `break` of
 *      `comprimi_comune()` the caller's `fuori->dati` points in there.
 *      ⇒ We COUNT at delivery and CLIMB at the entry of the next frame.
 *      ⭐ Good side effect: the cost of the reopening falls **between** two
 *        frames instead of in the middle of delivering one.
 *
 * Returns `false` only if the context was left broken: climbing is optional,
 * and a cure that kills the session when it fails is worse than the defect.
 */
static bool risali_qualita(Codificatore *c)
{
	char errore[256] = { 0 };

	if (!risalita_accesa)
		return true;                        /* ⛔ invariant I6: off by default */
	if (c->pacchetto_in_mano)
		return true;                        /* ⛔ the constraint above */
	if (c->modo_corrente != c->richiesta.modo)
		return true;                        /* left LOSSLESS: no going back in */
	if (c->qualita_corrente <= c->richiesta.qualita)
		return true;                        /* already at the requested working point */
	if (c->sotto_margine < c->risalita_attesa)
		return true;                        /* not calm enough yet */

	int prima = c->qualita_corrente;
	int dopo = prima - CRF_PASSO;
	/* ⛔ THE FLOOR IS WHAT WAS REQUESTED, and no field is needed to
	 *    remember it: `c->richiesta` keeps the request intact. */
	if (dopo < c->richiesta.qualita)
		dopo = c->richiesta.qualita;
	/* ⛔ And we do not set foot on the rung where the ceiling already bit
	 *    until TWICE the wait has passed: that is not a suspicion,
	 *    it is a number MEASURED on this content. */
	if (c->qualita_fallita && dopo <= c->qualita_fallita
	    && c->sotto_margine < c->risalita_attesa * 2u)
		return true;

	uint32_t calmi = c->sotto_margine; /* ⚠ the REAL number, not the threshold */
	c->qualita_corrente = dopo;
	c->sotto_margine = 0;
	if (!cambia_qualita(c, errore, sizeof(errore))) {
		/* ⚠ Climbing is OPTIONAL: if the context does not reopen at the new
		 *   value we go back to the one that worked, and the session carries on
		 *   grainy instead of dying. */
		registro_dice(REG_CODIFICA,
		              "⛔ did not reopen climbing to %s %d (%s): going back to %d",
		              nome_modo(c->modo_corrente), dopo, errore, prima);
		c->qualita_corrente = prima;
		if (!cambia_qualita(c, errore, sizeof(errore))) {
			registro_dice(REG_CODIFICA,
			              "⛔⛔ and not even at %s %d: the context is closed and nothing "
			              "more is sent — %s",
			              nome_modo(c->modo_corrente), prima, errore);
			c->conf.ha_obbedito = false;
			di(c->conf.perche_no, sizeof(c->conf.perche_no),
			   "the context did not reopen after a climb attempt: %s",
			   errore);
			return false;
		}
		c->prossimo_chiave = true;
		c->risalita_attesa = c->risalita_attesa >= RISALITA_ATTESA_MAX / 2u
		                         ? RISALITA_ATTESA_MAX
		                         : c->risalita_attesa * 2u;
		return true;
	}

	c->risalito_da_poco = true;
	/* ⛔ New context, no past: `RCP.md` §5.2 wants a real key.
	 *    `apri_contesto()` has already demanded it; the line stays because the rule is
	 *    written here, not elsewhere. */
	c->prossimo_chiave = true;
	registro_dice(REG_CODIFICA,
	              "⭐ QUALITY UP: %s %d → %d after %u frames in a row below %u bytes "
	              "(one eighth of the ceiling), requested floor %d.  ⚠ It costs a reopening "
	              "and a KEY — [M] 91-108 ms in hardware, 1.8-3.3 s in software — and "
	              "that is why we climb ONE rung at a time and wait twice as long on "
	              "every relapse.  ⭐ It is DECISIONI.md §3.3 «never grainy»: without this "
	              "line a single exceptional frame left the session grainy "
	              "for hours",
	              nome_modo(c->modo_corrente), prima, dopo, calmi, RISALITA_MARGINE,
	              c->richiesta.qualita);
	return true;
}

/* The encoded bytes are copied into `c->uscita`, which is ours: see the
 * structure.  It grows when needed and never shrinks. */
static bool metti_in_uscita(Codificatore *c, const uint8_t *dati, size_t byte)
{
	if (byte > c->uscita_capacita) {
		size_t nuova = byte + byte / 4 + 4096;
		uint8_t *p = realloc(c->uscita, nuova);
		if (!p) {
			registro_dice(REG_CODIFICA, "⛔ no memory for %zu output bytes", byte);
			return false;
		}
		c->uscita = p;
		c->uscita_capacita = nuova;
	}
	memcpy(c->uscita, dati, byte);
	c->uscita_byte = byte;
	return true;
}

/*
 * ⭐ THE BODY COMMON TO BOTH ROUTES — and there is ONE because what comes after
 *    the prepared frame is identical: the encoding, the 16 MiB ceiling, the
 *    re-encodings, the shape of the bytes, the key that must be a key.
 *
 * ⛔ Having it in two copies would be the worst form of all: the day a
 *    rule changes — and in this file they have all changed, at least once
 *    — one of the two copies stays behind **and no bench sees it**, because
 *    each one is green on its own.  ⇒ ONLY how `c->fotogramma` is filled
 *    changes, and that is the only `if` that tells them apart.
 *
 * ⚠ Exactly one of `pixel` and `superficie` is non-NULL, and it is not an implicit
 *   convention: the guard demands it and writes it.
 */
static bool comprimi_comune(Codificatore *c, const uint8_t *pixel, uint32_t passo,
                            const CodificatoreSuperficie *superficie,
                            CodificatoreFotogramma *fuori)
{
	if (!c || !fuori)
		return false;
	if ((pixel == NULL) == (superficie == NULL)) {
		registro_dice(REG_CODIFICA,
		              "⛔ we compress EITHER from the pixels OR from the surface, and here "
		              "%s arrived: we do not guess which of the two routes the caller "
		              "wanted",
		              pixel ? "both" : "neither");
		return false;
	}
	if (!c->conf.ha_obbedito) {
		registro_dice(REG_CODIFICA, "⛔ it did not obey (%s): nothing is sent",
		              c->conf.perche_no);
		return false;
	}
	if (c->pacchetto_in_mano) {
		registro_dice(REG_CODIFICA, "⛔ the previous frame was not released");
		return false;
	}
	if (c->svuotato) {
		/* ⛔ A context in drain no longer accepts frames: it is reopened, and the
		 *    reopening makes the next one a key.  Better one extra declared key
		 *    than a video that stops at the second frame. */
		char errore[256] = { 0 };
		chiudi_contesto(c);
		if (apri_contesto(c, errore, sizeof(errore)) < 0) {
			registro_dice(REG_CODIFICA, "⛔ did not reopen after the drain: %s", errore);
			return false;
		}
		if (apri_fotogrammi(c, errore, sizeof(errore)) < 0) {
			registro_dice(REG_CODIFICA, "⛔ the frames did not reopen: %s", errore);
			return false;
		}
		c->svuotato = false;
		registro_dice(REG_CODIFICA, "reopened after the drain: the next one is a key");
	}
	memset(fuori, 0, sizeof(*fuori));

	/* ⭐ THE CLIMB SITS HERE, BEFORE ENCODING, and not after delivery: after
	 *    the `break` the packet is in the caller's hands and `chiudi_contesto()`
	 *    FREES it.  ⚠ The count instead is kept at delivery, further down: that is where
	 *    we know how big it came out. */
	if (!risali_qualita(c))
		return false;

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⛔⛔ WHO THIS FRAME IS — AND IT IS DECIDED **HERE**, BEFORE THE FIRST
	 *      DESCENT, not inside the loop.
	 *
	 * ⛔ THE DEFECT THIS LINE CURES (23 Aug 2026, phase 9).  The count
	 *    of re-encodings read `c->prossimo_chiave` **inside** the loop, and
	 *    `abbassa_qualita()` calls `apri_contesto()`, which at `:2275` does
	 *    `c->prossimo_chiave = true` — *"after every opening the first is a
	 *    key"*, and it is right that it does: a new context has no
	 *    references, and a delta after a reopening would be undecodable.
	 *    ⇒ From the FIRST descent on `c->prossimo_chiave` was **always true**,
	 *      so `!c->prossimo_chiave && tentativo + 1 >= RICODIFICHE_MASSIME`
	 *      was **always false**: the branch abandoning the delta was **dead
	 *      code**, and `RICODIFICHE_MASSIME` never stopped a delta in its
	 *      life.  A delta above the ceiling walked the ladder **all the way down**,
	 *      and left only through the `break` (it fits) or through "not even at the bottom of the
	 *      ladder".  ⚠ Meanwhile the startup line declared *"a DELTA is abandoned
	 *      after 3 re-encodings"*, that is something that never happened.
	 *
	 * ⭐ And the same contamination made the "KEY above the
	 *   ceiling" line a liar: it printed it even for a frame born a delta.
	 *
	 * ⚠ The value is read AFTER `risali_qualita()` on purpose: if the climb has
	 *   reopened the context, this frame **really is** a key, and the
	 *   whole ladder is its due.
	 *
	 * ───────────────────────────────────────────────────────────────────────
	 * ⭐ THE TESTIMONY THAT THE BRANCH WAS DEAD, and it is not my reasoning:
	 *   `fasi/08-l-anello.md:2856` puts it among the `[?]` — *"the "abandoned
	 *   delta" branch: not walked even with the fault injected"* — and at
	 *   `:2810-2812`, with the ceiling lowered on purpose, the log says **"KEY
	 *   above the ceiling"** at attempt 2 and at 3.  ⚠ It is the contamination, seen
	 *   from outside: whoever rereads that bench was looking at the wrong label.
	 *
	 * ⛔⛔ THE FALSIFIABLE PREDICTION — `[?]`, and the hardware is the integrated Intel UHD 730,
	 *      not a powerful card.  The `[M]` numbers are agent D's,
	 *      22 Aug 2026, 7680x4320 with nearly incompressible content:
	 *      key at QP 38 = 16.654 MiB · at QP 44 = 11.056 MiB · at QP 51 =
	 *      1.771 MiB; each encoding+reopening 91-108 ms in hardware.
	 *
	 *   CASE 1 — a delta that breaks through at QP 26 but FITS at 44 (the case the
	 *   `[M]` numbers make likely): **before and after are identical**.  Three encodings
	 *   (26 delta, 35 key, 44 key), two reopenings, ~450-540 ms, delivered
	 *   as a KEY at QP 44.  ⛔ The count does not bite: the third attempt fits.
	 *
	 *   CASE 2 — a delta that breaks through **even at 44**, and it is the only case in which the
	 *   cure shows:
	 *     BEFORE 4 encodings, 3 reopenings, ~640-750 ms, delivered at QP 51, and
	 *            the session stays at 51.
	 *     AFTER  3 encodings, 2 reopenings, ~450-540 ms — **~190-215 ms
	 *            less** — the frame does NOT leave, and the session stays at **44**.
	 *            The next one is a KEY at 44 (the reopening imposed it), and
	 *            `[M]` at 44 an 8K key makes 11.056 MiB: **it fits**.
	 *   ⇒ ONE frame is lost and ONE quality rung is gained for the
	 *     session, plus one reopening.  ⚠ And the rung gained does not have to be
	 *     climbed again by the climb: that is 120 frames (~2 s at 60/s) less of grainy
	 *     picture for every time the ceiling bites.
	 *
	 *   IF THE CURE WERE WRONG, it would show like this:
	 *     a) *"delta abandoned after 1 (or 2) encodings"* in the log ⇒ it is
	 *        abandoned EARLIER, and that is a loss.  ⛔ I do not expect it: the threshold
	 *        is `tentativo + 1 >= RICODIFICHE_MASSIME` and `chiave_chiesta` is
	 *        false **only** for a frame born a delta.
	 *     b) *"delta abandoned"* and then the next frame is **not** a
	 *        key ⇒ the client is left without a past.  ⛔ It cannot happen:
	 *        every descent goes through `apri_contesto()`, which at `:2275` imposes the
	 *        key — and if one day it removed that, THIS is the symptom to
	 *        look for.
	 *     c) *"delta abandoned"* repeating on every frame for seconds ⇒
	 *        it is one key for every abandoned delta, that is **the spiral** that
	 *        `RCP.md:1284-1286` names.  ⚠ The remedy is not here: it is lowering the
	 *        frames (`SPECIFICHE.md` §8.3) or the bandwidth ceiling.  ⛔ This
	 *        cure neither creates nor removes it — the spiral was already there, because the
	 *        reopening imposed the key before too.
	 *   ⚠ And the unexpected gain someone might hope for — "the delta goes through
	 *     instead of being abandoned" — **will not come**: when the count
	 *     bites, that frame has already broken the ceiling three times.
	 * ═══════════════════════════════════════════════════════════════════════ */
	const bool chiave_chiesta = c->prossimo_chiave;

	for (uint32_t tentativo = 0;; tentativo++) {
		uint64_t us_conv = 0, us_carico = 0;
		/* ⭐ PHASE 19: the ONLY `if` between the two card routes — and it sits before
		 *    the bytes boundary, like the `if` between memory and zero copy. */
		if (c->strada == STRADA_VULKAN) {
			if (!codifica_vulkan(c, pixel, passo, superficie, fuori))
				return false;
			goto byte_pronti;
		}
		bool pronto = superficie
		                  ? prepara_dalla_scheda(c, superficie, &us_conv, &us_carico)
		                  : prepara_fotogramma(c, pixel, passo, &us_conv, &us_carico);
		if (!pronto)
			return false;
		fuori->us_conversione = us_conv;
		fuori->us_caricamento = us_carico;

		uint64_t t0 = adesso_us();
		{
			/* ⭐ PHASE 18 — the card: one round, one wait, the bytes.  No
			 *    EAGAIN by construction, no reordering by construction. */
			const uint8_t *dati = NULL;
			size_t byte = 0;
			char errore[256] = { 0 };
			if (!vadiretta_codifica(c->va, c->superficie_pronta, c->prossimo_chiave, &dati,
			                        &byte, errore, sizeof errore)) {
				registro_dice(REG_CODIFICA, "⛔ the card did not encode: %s", errore);
				return false;
			}
			if (!metti_in_uscita(c, dati, byte))
				return false;
			fuori->us_codifica = adesso_us() - t0;
			fuori->trattenuto = false;
			c->pacchetto_in_mano = true;
		}
byte_pronti:
		/* ⛔ BOUNDARY — from here down we work on the BYTES in `c->uscita`. */

		/* ───────────────────────────────────────────────────────────────────
		 * ⛔ THE 16 MiB CEILING — `RCP.md` §6.2, and it binds WHOEVER SENDS. */
		if ((uint32_t) c->uscita_byte > TETTO_FOTOGRAMMA) {
			/* ⭐ The size is read BEFORE throwing away the bytes, or the descent
			 *    line would say zero: it is the proof that the descent is measured (I1). */
			uint32_t prodotti = (uint32_t) c->uscita_byte;
			/* ⚠ The ceiling in the message is PRINTED, not written by hand: a
			 *   log line that said "16 MiB" while the constant says
			 *   otherwise would send the hunt the wrong way. */
			registro_dice(REG_CODIFICA,
			              "⛔ frame of %zu bytes, beyond the %u of the RCP.md §6.2 ceiling: "
			              "RE-ENCODING at lower quality (attempt %u), not sending",
			              c->uscita_byte, TETTO_FOTOGRAMMA, tentativo + 1);
			c->pacchetto_in_mano = false;

			/* ⛔ THE RUNG ON WHICH THE CEILING BIT is that of the FIRST
			 *    attempt: the others are descents that do not yet have a measurement
			 *    against them.  ⚠ It serves the climb, which on that one
			 *    alone waits twice as long before setting foot on it again. */
			if (tentativo == 0)
				c->qualita_fallita = c->qualita_corrente;

			/* ═══════════════════════════════════════════════════════════════
			 * ⛔⛔ AND ON A **KEY** WE DO NOT GIVE UP — `RCP.md` §5.2, and
			 *      until 22 Aug 2026 this branch abandoned it.
			 *
			 * §5.2 says the server **MUST NOT** abandon a key
			 * frame, and the reason is that a client without a key **has no
			 * past**: it cannot paint anything, neither now nor later.
			 *
			 * ⛔ AND THE DEFECT WAS NOT "one lost frame": it was a SPIRAL.
			 *    The client stays broken ⇒ sends `RICHIEDI_CHIAVE` ⇒ we redo
			 *    the same three re-encodings ⇒ we fail again ⇒ it asks again.
			 *    `[M]` (agent D, 22 Aug 2026) each attempt at 8K costs
			 *    **91-108 ms in hardware** and **1.8-3.3 s in software** ⇒
			 *    **~300 ms** or **~7.8 s** thrown away for every request, over
			 *    and over, and the session does not heal by itself.
			 *
			 * ⭐ AND THE CURE IS SAFE BECAUSE IT HAS A NUMBER UNDER IT: `[M]` at 8K
			 *    **QP 51 gives 1.771 MiB**, that is **10.6 %** of the ceiling.  ⇒ At the
			 *    bottom of the ladder a key **always fits**.
			 *
			 * ⇒ For a key we keep descending as long as the ladder has
			 *   rungs, and when it comes out ugly **we write it down**.  ⚠ It is invariant
			 *   I1 to the letter: **ugly and alive** beats beautiful and dead.  An
			 *   ugly picture lasts one frame; a broken client lasts the whole
			 *   session.
			 * ═══════════════════════════════════════════════════════════════ */
			/* ═══════════════════════════════════════════════════════════════
			 * ⛔ THE COUNT OF ATTEMPTS GOES **BEFORE** THE DESCENT, and not after.
			 *
			 * ⭐ The rule in one line: **a rung that will not be tried is not
			 *   applied**.  Every descent closes and reopens the context — `[M]`
			 *   91-108 ms in hardware, 1.8-3.3 s in software — and paying for it for a
			 *   frame that is about to be abandoned is time taken from the RATE
			 *   without even a measurement in exchange.  ⚠ The value then stays
			 *   on the session: the picture would come out uglier by a
			 *   rung nobody ever tried, and the climb would have to
			 *   climb it again at 120 frames per step.
			 *
			 * ⇒ A DELTA makes `RICODIFICHE_MASSIME` **encodings** in all, that is
			 *   `RICODIFICHE_MASSIME - 1` descents, and each one of those is
			 *   **tried**.
			 *
			 * ⛔ AND ABANDONING HERE DOES NOT BREAK §5.2, and the reason is an invariant
			 *    that can be checked: with `RICODIFICHE_MASSIME >= 2`
			 *    the abandonment comes **after at least one reopening**, and every
			 *    reopening leaves `c->prossimo_chiave = true` (`:2275`).  ⇒ The
			 *    next frame is a KEY, which is exactly what §5.2
			 *    demands after an abandoned delta (*"the server MUST send a
			 *    key as soon as it can"*).  ⚠ And if one day `RICODIFICHE_MASSIME`
			 *    dropped to 1, the abandonment would happen **without** a reopening: there
			 *    the context is intact, the client still has its past, and it is
			 *    fine all the same.  The two cases are covered, and they are the only two.
			 * ═══════════════════════════════════════════════════════════════ */
			if (!chiave_chiesta && tentativo + 1 >= RICODIFICHE_MASSIME) {
				registro_dice(REG_CODIFICA,
				              "⚠ delta abandoned after %u encodings (RICODIFICHE_"
				              "MASSIME) and %u TRIED descents: at %s %d it is still above "
				              "the %u bytes.  ⭐ It is not a key, so whoever is watching still "
				              "has their past — and the next frame is "
				              "a KEY anyway (§5.2), because the descents have "
				              "reopened the context.  ⛔ We do not descend another "
				              "rung: it would be applied and never tried",
				              tentativo + 1, tentativo,
				              c->modo_corrente == CODIFICATORE_QUALITA_QP ? "QP" : "CRF",
				              c->qualita_corrente, TETTO_FOTOGRAMMA);
				return false;
			}
			if (!abbassa_qualita(c, prodotti)) {
				/* ⛔ The bottom of the ladder: here it is not "I give up because of a count
				 *    of attempts", it is "there is nothing left to lower".  It is
				 *    the only case in which a key does not leave, and the line says
				 *    WHICH of the two it is. */
				registro_dice(REG_CODIFICA,
				              "⛔⛔ not even at the bottom of the ladder (%s %d) does the frame fit "
				              "under the %u bytes: it does NOT leave.  ⚠ And this is NOT \"I "
				              "gave up after %u attempts\": it is \"there is nothing left to "
				              "lower\"",
				              c->modo_corrente == CODIFICATORE_QUALITA_QP ? "QP" : "CRF",
				              c->qualita_corrente, TETTO_FOTOGRAMMA, tentativo + 1);
				return false;
			}
			/* ⚠ AND THE RETRY IS A KEY EVEN IF THE FRAME WAS A DELTA:
			 *   `apri_contesto()` has thrown away the references, and a delta without
			 *   a past is decoded by nobody.  ⛔ The line says so instead of
			 *   calling both of them "KEY", which is what it did as long as the
			 *   count read `c->prossimo_chiave` contaminated by the reopening. */
			/* ⚠ The ceiling of encodings is PRINTED from the constant, not written
			 *   by hand: it is the same rule as the ladder line at startup. */
			char quante[72];
			if (chiave_chiesta)
				snprintf(quante, sizeof(quante),
				         "as many as the ladder has — a key is not abandoned");
			else
				snprintf(quante, sizeof(quante), "%d (RICODIFICHE_MASSIME)",
				         RICODIFICHE_MASSIME);
			registro_dice(REG_CODIFICA,
			              "⚠ %s above the ceiling: going down to %s %d and RETRYING (encoding %u of "
			              "%s).  ⛔ A key is not abandoned (§5.2): the picture "
			              "will come out uglier, and this line is the declaration.  "
			              "⭐ `[M]` at the bottom of the ladder (51) an 8K key is worth 1.771 "
			              "MiB, that is 10.6 %% of the ceiling",
			              chiave_chiesta ? "KEY"
			                             : "delta (and the retry will be a KEY: the "
			                               "context is new and no longer has a past)",
			              c->modo_corrente == CODIFICATORE_QUALITA_QP ? "QP" : "CRF",
			              c->qualita_corrente, tentativo + 2, quante);
			fuori->ricodifiche = tentativo + 1;
			continue;
		}
		break;
	}

	/*
	 * ⭐ THE COUNT OF CALM — and we count the frame **comfortably**
	 *    below the ceiling, not the frame "below": one that brushes it is
	 *    no proof that there is room for one more quality rung.
	 *    ⛔ It is here that FLAPPING is switched off: a scene at 94.9 % of the ceiling
	 *    (`[M]` grain `alls=60` at 7680x4320) does not advance this counter
	 *    **even by one**, so it never climbs and there is nothing to
	 *    flap.
	 *
	 * ⚠ We count what the encoder PRODUCED, not what leaves: the
	 *   quantity that decides is "at this quality the frame fits", and it does not
	 *   depend on what the sender then does with it.
	 */
	if ((uint32_t) c->uscita_byte <= RISALITA_MARGINE) {
		if (c->sotto_margine < UINT32_MAX)
			c->sotto_margine++;
		/* The climb held up to the requested working point: the next
		 * bite is not its fault, and the wait does not double. */
		if (c->risalito_da_poco && c->qualita_corrente <= c->richiesta.qualita
		    && c->sotto_margine >= c->risalita_attesa)
			c->risalito_da_poco = false;
	} else {
		c->sotto_margine = 0;
	}

	bool chiave = false;
	if (!cornice_al_suo_posto(c, chiave_chiesta || c->prossimo_chiave) ||
	    !forma_va_bene(c, c->uscita, c->uscita_byte, &chiave)) {
		c->pacchetto_in_mano = false;
		return false;
	}

	/* ⛔ `RCP.md` §5.2: the first frame after `SESSIONE`, and the first after a
	 *    canvas change, MUST be a key.  If we had asked for it and it is
	 *    not, it is not sent: a delta marked key is what Chromium
	 *    discovers by rereading the bitstream, and our label does not save it. */
	if (c->prossimo_chiave && !chiave) {
		registro_dice(REG_CODIFICA,
		              "⛔ a KEY had been requested and the encoder produced a "
		              "delta: not sending (RCP.md §5.2)");
		c->pacchetto_in_mano = false;
		return false;
	}

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⭐⭐⭐ THE THIRD WITNESS: THE BYTES THAT REALLY GO OUT
	 *
	 * ⛔ Why it exists, in one line: **in v1 the first two witnesses would have
	 *    been green.**  `bit_rate` and `rc_max_rate` were exactly the numbers
	 *    requested and nobody had asked for CBR — CBR was **the name the
	 *    driver gave to that pair of numbers**.  ⇒ Only the bill
	 *    said it, and this line is the bill printed **before** it arrives.
	 *
	 * ⭐ And the number that unmasks CBR is the one on an **easy** scene: `[M]` on
	 *   this laptop, on a still scene, CBR **15.98 Mbit/s** against CQP
	 *   **0.193** — **83 times**.  On a hard scene the regulated modes all sit
	 *   within 1 % of one another and nothing could be told apart.
	 *   ⚠ On the product the truly still scene gives **zero frames** (`[M]`
	 *   §3.8: 0.00 fr/s), so the window does not close and the line does not come out:
	 *   rightly so, there is nothing to declare.  The scene that acts as
	 *   control is **the real desktop**, which moves and costs 1 %.
	 *
	 * ⚠ We count the bytes that **leave**, after the re-encodings and after the
	 *   shape checks: it is the quantity the viewer pays for, not the one
	 *   the encoder produced along the way.
	 * ═══════════════════════════════════════════════════════════════════════ */
	{
		uint64_t adesso = adesso_us();
		if (!c->banda_t0_us)
			c->banda_t0_us = adesso;
		c->banda_byte += (uint64_t) c->uscita_byte;
		c->banda_fotogrammi++;
		if ((uint32_t) c->uscita_byte > c->banda_massimo)
			c->banda_massimo = (uint32_t) c->uscita_byte;
		uint64_t durata = adesso - c->banda_t0_us;
		if (durata >= BANDA_FINESTRA_US) {
			uint64_t kbit = c->banda_byte * 8u * 1000u / durata; /* µs ⇒ kbit/s */
			char quota[128];
			if (tetto_pavimento_mbit)
				snprintf(quota, sizeof(quota),
				         " · CEILING ON: wire %" PRId64 " kbit/s, it uses %u %% of it",
				         tetto_filo() / 1000,
				         (unsigned) (kbit * 100u / (uint64_t) (tetto_filo() / 1000)));
			else
				snprintf(quota, sizeof(quota),
				         " · ceiling OFF (QP %d fixed): ⛔ nobody tells it no",
				         c->qualita_corrente);
			registro_dice(REG_CODIFICA,
			              "video bandwidth: %" PRIu64 " kbit/s over %" PRIu64 " ms — %u "
			              "frames (%" PRIu64 " bytes, the biggest %u), mode %s%s.  "
			              "⭐ It is the THIRD witness: what the driver REALLY did, "
			              "not what it said",
			              kbit, durata / 1000u, c->banda_fotogrammi, c->banda_byte,
			              c->banda_massimo, modo_bitrate_voluto().nome, quota);
			c->banda_t0_us = adesso;
			c->banda_byte = 0;
			c->banda_fotogrammi = 0;
			c->banda_massimo = 0;
		}
	}

	if (!c->prima_codifica_fatta) {
		c->prima_codifica_fatta = true;
		registro_dice(REG_CODIFICA,
		              "first frame: %s · %zu bytes · key %s · stream: %s, %d bits, "
		              "level %d, %ux%u · conversion %" PRIu64 " µs, upload "
		              "%" PRIu64 " µs, encoding %" PRIu64 " µs · %s",
		              c->conf.stringa_codec[0] ? c->conf.stringa_codec : "(not read)",
		              c->uscita_byte, chiave ? "yes" : "no",
		              c->conf.letto_dal_flusso ? "read" : "⛔ NOT read",
		              c->conf.profondita_flusso, c->conf.livello_flusso,
		              c->conf.larghezza_flusso, c->conf.altezza_flusso,
		              fuori->us_conversione, fuori->us_caricamento, fuori->us_codifica,
		              c->nome);
		if (c->conf.promozione_8_a_10)
			registro_dice(REG_CODIFICA,
			              "⚠ and the 10 bits are EIGHT PROMOTED: GNOME's capture delivers "
			              "BGRx [M], and the stream label will say «Main 10» anyway");
	}

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⛔⛔ THIS POINTER SITS **INSIDE** THE PACKET, AND `chiudi_contesto()`
	 *      **FREES** THE ENCODER'S BYTES (`vadiretta_chiudi`).
	 *
	 * ⚠ It is the third time in one day that someone trips over it, so the proof
	 *   is written here instead of being redone from memory.  From here until
	 *   `codificatore_rilascia()` the caller holds `fuori->dati`; in the same
	 *   interval `chiudi_contesto()` **must not** run.  The places it can
	 *   start from are SEVEN, and each has its guard:
	 *
	 *     `:2125` `:2140` `:2149` `:2265` `:2272`  the error exits of
	 *         `apri_contesto()`.  ⛔ Not reachable with a packet in hand
	 *         by construction: `apri_contesto()` is called only **right after**
	 *         a `chiudi_contesto()` — or on a newly born encoder — and at
	 *         `:2125`-`:2149` the packet has not even been allocated (it is at
	 *         `:2270`, at the bottom).
	 *     `:2681` `codificatore_libera()` — guard at `:2668`: it does the `unref`
	 *         first.  ⚠ After `libera()` the caller's `fuori` is worth nothing
	 *         anyway, and that is the contract of `codificatore.h:439`.
	 *     `:2760` `codificatore_ridimensiona()` — guard at `:2745`, added on
	 *         23 Aug 2026: it was **the only one without**, and it refuses instead of
	 *         freeing from under the reader's feet.
	 *     `:3445` `abbassa_qualita()` — called from one place only, the re-encoding
	 *         loop above, and there `pacchetto_in_mano = false` sits
	 *         **before** the descent, and
	 *         `fuori->dati` has not been written yet.
	 *     `:3536` `:3546` `risali_qualita()` — guard at `:3511`, and it is written
	 *         in its box: it is precisely the reason the climb lives
	 *         **at the entry** of the next frame and not after delivery.
	 *     `:3626` the reopening after the drain — guard at `:3617`, which refuses
	 *         if the previous frame was not released.
	 *
	 * ⇒ It is not reachable, and now it is not **by construction** instead of
	 *   by luck.  ⚠ Whoever adds an eighth `chiudi_contesto()` must also add
	 *   the line above, or they take the proof away from everyone.
	 * ═══════════════════════════════════════════════════════════════════════ */
	fuori->dati = c->uscita;
	fuori->byte = c->uscita_byte;
	fuori->chiave = chiave;
	c->prossimo_chiave = false;
	c->numero++;
	return true;
}

bool codificatore_comprimi(Codificatore *c, const uint8_t *pixel, uint32_t passo,
                           CodificatoreFotogramma *fuori)
{
	if (!pixel) {
		registro_dice(REG_CODIFICA, "⛔ no pixels to compress");
		return false;
	}
	return comprimi_comune(c, pixel, passo, NULL, fuori);
}

bool codificatore_comprimi_scheda(Codificatore *c, const CodificatoreSuperficie *superficie,
                                  CodificatoreFotogramma *fuori)
{
	if (!c || !superficie)
		return false;
	/* ⛔ Without the card open this route does not exist (phase 19: an
	 *    encoder that was born is always on the card; the guard stays so as not to let
	 *    a half-born encoder through silently). */
	if (!c->hardware) {
		registro_dice(REG_CODIFICA,
		              "⛔⛔ ZERO COPY requested on «%s», which has no card open: "
		              "nothing is imported",
		              c->nome_componente);
		return false;
	}
	if (superficie->fd < 0 || !superficie->larghezza || !superficie->altezza
	    || !superficie->stride || !superficie->formato_drm) {
		registro_dice(REG_CODIFICA,
		              "⛔ incomplete descriptor (fd %d, %ux%u, stride %u, format 0x%08x): "
		              "no half imports",
		              superficie->fd, superficie->larghezza, superficie->altezza,
		              superficie->stride, superficie->formato_drm);
		return false;
	}
	/* ⛔⛔ AND THE STRIDE MUST BE IMPORTABLE — see the box in
	 *      `codificatore.h`.  ⚠ The caller already knows and chooses the route
	 *      beforehand: this is the LAST line of defence, and it is needed because the defect
	 *      it stops **gives no error at all** — it gives a slanted picture that
	 *      passes every check on the milliseconds and every check on the colour. */
	if (!codificatore_stride_importabile(superficie->stride)) {
		registro_dice(REG_CODIFICA,
		              "⛔⛔ stride %u: it is NOT a multiple of %u, and the driver importing the "
		              "DMA-BUF would read the rows at a stride of its own — `[M]` 22 Aug 2026 "
		              "the mark can no longer be read on 0 frames out of 869, while the colour "
		              "averages stay identical within 0.17 levels out of 255.  ⇒ NOT "
		              "compressing: better the copy than a silently wrong picture",
		              superficie->stride, ALLINEAMENTO_SCHEDA);
		return false;
	}
	/* ⛔ And the descriptor's size must be the one the encoder
	 *    is open for: `comprimi_comune` does not look at it — it receives a surface and
	 *    trusts it.  ⚠ Feeding an encoder opened at 1920 with a 2560
	 *    surface does not protest: it crops or pads, and the defect shows only
	 *    in the picture (it is the same note as in `codificatore_ridimensiona`). */
	if (superficie->larghezza != c->richiesta.larghezza
	    || superficie->altezza != c->richiesta.altezza) {
		registro_dice(REG_CODIFICA,
		              "⛔ the surface is %ux%u and the encoder is open at %ux%u: we do "
		              "not compress a picture that is not its own",
		              superficie->larghezza, superficie->altezza, c->richiesta.larghezza,
		              c->richiesta.altezza);
		return false;
	}
	return comprimi_comune(c, NULL, 0, superficie, fuori);
}

bool codificatore_in_hardware(const Codificatore *c)
{
	return c ? c->hardware : false;
}

uint32_t codificatore_allineamento_scheda(void)
{
	return ALLINEAMENTO_SCHEDA;
}

bool codificatore_stride_importabile(uint32_t stride)
{
	return stride != 0 && (stride % ALLINEAMENTO_SCHEDA) == 0;
}

void codificatore_rilascia(Codificatore *c)
{
	if (!c || !c->pacchetto_in_mano)
		return;
	/* ⭐ Phase 18: the bytes are ours (`c->uscita`) and stay valid; the
	 *    release only says that the caller has finished reading them. */
	c->pacchetto_in_mano = false;
}
