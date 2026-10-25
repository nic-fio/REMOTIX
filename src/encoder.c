/*
 * encoder.c — HEVC Main10 and AV1, in software **or in hardware via VA-API**,
 * with the confession read from the bytes.  The why of every choice is in
 * `encoder.h`; here is the how, and next to every odd line the measurement
 * that made it necessary.
 *
 * ⭐ The GPU is used since 13 Aug 2026 (phase 3, brought forward by the user's
 *    decision).  ⛔ But **only for encoding**: zero copy — the frame that goes
 *    from capture to the GPU without passing through system memory — stays in
 *    phase 8, and here the upload is paid for and **measured separately**
 *    (`upload_us`), so that we can see how much removing it will be worth.
 *
 * ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ PHASE 18 (30 Sep 2026, `DECISIONS.md` §10.25) — THE TWO HALVES OF THE FILE
 * From today the file has TWO routes that do not share a line of codec, and
 * ⛔ neither of them goes through ffmpeg:
 *
 *   THE CARD      `vadirect.c`: libva used directly — parameters, headers
 *                 written by us, coded buffers.  The colour conversion is
 *                 done by the card's VPP on the zero copy; on the "from
 *                 memory" route it is done by `colors709.c` on the CPU
 *                 (NV12/P010) and then the planes are uploaded to the card, as
 *                 before phase 18 — the VPP from memory is measured WORSE
 *                 (see `prepare_frame()`).
 *   ⛔ The software FALLBACK (OpenH264, SVT-AV1: `ripiego.c`) LEFT with
 *                 phase 19 (1 Oct 2026, `DECISIONS.md` §10.27), in the
 *                 user's words: *"no CPU without a card"*.  A name that does
 *                 not belong to the card is refused in `codificatore_nuovo()`,
 *                 with the reason: without a capable card REMOTIX does not encode.
 *
 * What lies OUTSIDE the card route — the 16 MiB ceiling, the degradation
 * ladder and the climb back, the shape of the bytes, the D-023 frame, the
 * third bitrate witness — works on the BYTES, and holds identically for BOTH
 * card routes.
 *
 * ⭐⭐ PHASE 19 (1 Oct 2026, `DECISIONS.md` §10.27) — THE TWO CARD ROUTES,
 *     CHOSEN BY CAPABILITY AND NOT BY BRAND.  The user's words: *"encoding
 *     must happen with standard tools, preferably with Vulkan, which is common
 *     to all 4 architectures"*.
 *
 *   1. VULKAN VIDEO  `vulkanvideo.c`: if `vulkanvideo_capabilities()` says the
 *                    node's card encodes THAT codec (today AMD with RADV,
 *                    NVIDIA with the proprietary driver; Intel when Mesa makes
 *                    it stable).  Zero copy from the DMA-BUF and colour
 *                    conversion on the card with the shader; from memory the
 *                    BGRx are uploaded as they are and the same shader converts them.
 *   2. VA-API        `vadirect.c`, as it was: where Vulkan is missing (today Intel).
 *   —  no processor: without a route the encoder is not born, and it says
 *      so.
 *
 *   The choice is made in `open_device()`, ONCE per encoder, and is
 *   written to the log and to the confession (`route`).  ⛔ It can also be
 *   requested by name (`h264_vulkan`, `h264_vaapi`): then there is NO fallback
 *   to the other — whoever asks by name is measuring (`CODER.md` §3.9).
 *   ⚠ Everything downstream of the bytes (ceiling, ladder, climb, shape,
 *   frame, key on request, resize) is ONE for both routes: the cures are not
 *   duplicated, and a green bench on one holds for the other.
 * ═══════════════════════════════════════════════════════════════════════════
 */
#include "encoder.h"
#include "colors709.h"
#include "dimcheck.h"
#include "log.h"
#include "bit_writer.h"
#include "vadirect.h"
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
 *   Makefile already has for `capture.c`. */
#include <drm_fourcc.h>
#include <va/va_drmcommon.h>
#include <va/va_vpp.h>

/* ⚠ An area of its own instead of one of the six in `log.h`: that file is
 *   not part of this sub-phase and is not touched.  The line to centralise it —
 *   `#define REG_VIDEO "video"` — is in the report, together with the Makefile ones. */
#define LOG_ENCODING "video"

/* `RCP.md` §6.2: "the server MUST NOT produce a frame longer than 16 MiB.  If
 * encoding produced a bigger one, it MUST re-encode it at lower quality and
 * WRITE IT TO THE LOG — never send it." */
#define FRAME_CAP (16u * 1024u * 1024u)

/* ⛔ How many ENCODINGS a DELTA is granted in total — not how many descents: the
 *    descents are `MAX_REENCODES - 1`, because the first encoding is the
 *    one at the requested quality and does not come from any descent.  ⇒ With
 *    3: QP 26, 35, 44, and the ladder stops there.
 * ⛔ And the last rung is NOT applied unless it is tried: the count sits **before**
 *    `lower_quality()`, and the why is in the box inside
 *    `compress_common()`.
 * ⚠ It does not apply to a KEY at all: §5.2 forbids abandoning it, and for a key
 *   the ladder is walked all the way down. */
#define MAX_REENCODES 3

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
#define EMERGENCY_CRF 24
#define CRF_STEP 9

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐ AND THE LADDER IS CLIMBED BACK — phase 9, 23 Aug 2026.
 *
 * ⛔ THE DEFECT: until now `current_quality` was monotonic in the worse direction.
 *    Four writes in all (`codificatore_nuovo()` seeds it, and the three
 *    inside `lower_quality()`), **all going down**, and no path that would
 *    bring it back up — not even `codificatore_ridimensiona()`, which closes and
 *    reopens the context **keeping it**.
 *
 *    ⇒ A single exceptional frame — `[M]` the software fallback of the time
 *      at 7680x4320 on grainy footage broke the ceiling 1 time out of
 *      8 — left the
 *      encoder at CRF 47 (or QP 51) **for the whole session**: the user's
 *      still desktop came out grainy **for hours**, and no log line
 *      said why.  ⚠ It is the *"never grainy"* of `DECISIONS.md` §3.3 lost
 *      through inertia instead of by decision.
 *
 * ⛔ AND IT IS NOT SYMMETRIC TO THE DESCENT, ON PURPOSE: we descend several rungs in
 *    a single frame, we climb back **ONE** every `RISE_WAIT` quiet
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
 *                `MAX_REENCODES` count was dead code.  ⚠ Meanwhile the
 *                startup line declared that it stopped after three re-encodings.
 *        now     a DELTA makes `MAX_REENCODES` encodings, that is **two**
 *                descents (35, 44), both tried.  A KEY does not change
 *                one bit: §5.2 forbids abandoning it, and it walks the whole
 *                ladder as before.
 *
 *      ⇒ THE CLIMB HAS TWO RUNGS TO REDO INSTEAD OF THREE, and the numbers
 *        below **still hold**, for this reason: from QP 44 we go back to 35
 *        after `RISE_WAIT` (120) quiet frames, and from 35 to 26 after
 *        **twice** that (240), because 26 is the rung on which the ceiling bit
 *        (`failed_quality`) and we do not set foot there again in a hurry.  Total
 *        **360 frames, ~6 s at 60/s**, against the **480 (~8 s)** that were needed
 *        starting from 51.  ⛔ The change shortens the grainy spell by ~2 s and touches
 *        neither the direction nor the shape of the climb: **there is no written reason
 *        to retune `RISE_WAIT`**, and without a written reason it is not touched.
 *        ⚠ `RISE_MARGIN` stays one eighth of the ceiling = 2 MiB, and with two
 *        rungs instead of three the margin is if anything **wider**, not narrower.
 *
 * ⛔⛔ THE CHECK THAT DECIDES — FLAPPING, and it must be written here because it is the
 *      fault that would bring this cure down.  A scene that lives **on the edge
 *      of the ceiling** (`[M]` grain `alls=60` at 7680x4320 in hardware: **94.9 %**)
 *      could make it descend and climb continuously, paying a
 *      reopening and a KEY on every round — and the price would be paid by the
 *      **rate**, that is precisely invariant I1 that this cure claims to needs.
 *
 *      ⭐ It is against that that the two numbers are chosen, and the defence is DOUBLE:
 *
 *        1. `RISE_MARGIN` is **one eighth** of the ceiling, not the ceiling.  We
 *           count the frame **comfortably** below, not the frame
 *           "below": a scene at 94.9 % of the ceiling produces **not even one**
 *           quiet frame ⇒ `below_margin` stays at zero ⇒ **it never
 *           climbs**, and there is nothing to flap.  For
 *           flapping to happen you would need a scene that alternates **8x** in
 *           size while staying calm for two whole seconds: that is not an
 *           edge, it is a real scene change.
 *        2. `rise_wait` **DOUBLES on every relapse** and never comes back
 *           down.  Even in the worst case the frequency of reopenings
 *           halves on every round, and at `RISE_WAIT_MAX` it stops at one every
 *           ~64 s.  ⚠ The direction in which to err is patience.
 *
 *      ⇒ If the bench of `phases/09-quality-and-degradation.md` §5 (case 2: more than 3
 *        reopenings per minute; case 3: frames/s **with** the cure lower
 *        than those **without**, paired on the same scene) found
 *        flapping anyway, **these three numbers are wrong** — or the cure
 *        must be removed.
 *
 * ⚠ The three numbers are `[?]` **sufficient, not right**, exactly like
 *   `CRF_STEP` = 9: the working point belongs to this phase, and the one to tune them is the
 *   bench, not this line.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define RISE_MARGIN (FRAME_CAP / 8u) /* 2 MiB: there is room for two rungs */
#define RISE_WAIT 120u                     /* ~2 s at 60/s */
#define RISE_WAIT_MAX 3840u                /* ~64 s: the bottom of the doubling */

/*
 * ⛔ THE SWITCH, AND IT IS BORN OFF — invariant I6: *whatever changes what
 *    is SEEN stays behind a switch that is off until the user looks at it*
 *    (`CODER.md`, the table of invariants).  The climb changes what is
 *    seen — a desktop that
 *    turns sharp again instead of staying grainy — so it does not turn itself on.
 *
 * ⚠ Static and not per encoder: it is a decision of the **server**, not of the
 *   client nor of the single stream.  It is the same shape as `wt_adaptive_rate()`.
 */
static bool rise_enabled;

void encoder_quality_rises(bool enabled)
{
	rise_enabled = enabled;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * ⭐⭐⭐ THE BANDWIDTH CEILING — phase 9, 23 Aug 2026, and IT IS BORN OFF
 *
 * ⛔ THE NUMBER THAT FORCES IT, and until this morning it was not there.  `[M]` test
 *    machine, canvas **2560x1080**, `h264_vaapi` `EncSliceLP`, **constant QP 26**
 *    (that is what the product does today), 30 s per point, wide line
 *    (`phases/09-quality-and-degradation.md` §3.8):
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
 * ⇒ ⛔⛔ And the regulator **cannot look at how many pixels change**: `full` and
 *   `bar` move **the same pixels** and cost **1.2 against 21.4**.  The
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
 *      this file** (`lower_quality()`, `CRF_STEP`) and **the
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
 * ⭐ And the fourth red of the study (`phases/09-quality-and-degradation.md` §5) has
 *   **FALLEN**: declaring 16 Mbit/s ffmpeg prints `Using level 5`, that is 5.0.
 *   The bandwidth does **not** raise `level_idc`, and `avc1.640033` holds.
 *
 * ───────────────────────────────────────────────────────────────────────────
 * ⛔ THE THREE NUMBERS, AND NONE IS WRITTEN BY HAND — they derive from the floor
 *
 * The floor is **20 Mbit/s** (`DECISIONS.md` §3.1-bis, `CODER.md` §1-bis).
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
 *          mask that `open_device()` has just written to the log.
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
 *   to `MAX_REENCODES` reopenings of `[M]` 91-108 ms.  ⛔ It is not turned on
 *   today: it is a **second** lever on the same quantity, and two levers on
 *   together in the first round would give two measurements under the same label.  ⭐ And
 *   the 40 ms buffer already does almost all of its work.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define VBV_CAP_MS 40u        /* the TARGET of CODER.md §1-bis, not the 50 ceiling */
#define WIRE_CAP_QUOTA 80u    /* % of the floor that goes to video: the rest is [M] 2.4 Mbit/s */
#define POINT_CAP_QUOTA 75u   /* % of the wire: the working point.  ⛔ NEVER 100 — that is R31 */

/*
 * ⭐ The window of the third witness.  ⚠ Ten seconds and not one: shorter, it
 *   would measure the single frame (which is already printed elsewhere) instead of the
 *   **bandwidth**, and longer it would arrive after the bench has finished.  ⛔ And it holds
 *   with the ceiling OFF as with the ceiling on: a witness that existed only with the
 *   cure on could not compare anything.
 */
#define BANDWIDTH_WINDOW_US (10u * 1000u * 1000u)

/*
 * 0 = OFF, and it is the value at birth.  Non-zero = the declared **floor**
 * in Mbit/s (20, today), from which the three numbers derive.
 *
 * ⚠ Static and not per encoder: it is a decision of the **server**, like the
 *   climb above and like `wt_adaptive_rate()`.
 */
static uint32_t cap_floor_mbit;

void codificatore_tetto_banda(uint32_t floor_mbit)
{
	cap_floor_mbit = floor_mbit;
}

/*
 * ⛔ The three numbers are COMPUTED in one place only, and whoever prints them in the log
 *    calls these, and does not rewrite the computation: two drafts of the same number are
 *    a place to diverge silently.
 */
static int64_t wire_cap(void)
{
	return (int64_t) cap_floor_mbit * 1000000 * WIRE_CAP_QUOTA / 100;
}

static int64_t point_cap(void)
{
	return wire_cap() * POINT_CAP_QUOTA / 100;
}

static int reservoir_cap_bit(void)
{
	return (int) (wire_cap() * VBV_CAP_MS / 1000);
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
	const char *name;
} BitrateMode;

static BitrateMode wanted_bitrate_mode(void)
{
	if (cap_floor_mbit)
		return (BitrateMode){ 5, VA_RC_QVBR, "QVBR" };
	return (BitrateMode){ 1, VA_RC_CQP, "CQP" };
}

/*
 * The driver's mask, in plain text.  ⚠ All the bits `va.h` knows, not
 * only the four we care about: a bit we cannot name is printed
 * as a number, and does not disappear.
 */
static void bitrate_mode_names(unsigned mask, char *report, size_t byte)
{
	static const struct {
		unsigned bit;
		const char *name;
	} KNOWN[] = {
		{ VA_RC_NONE, "NONE" },   { VA_RC_CBR, "CBR" },
		{ VA_RC_VBR, "VBR" },     { VA_RC_VCM, "VCM" },
		{ VA_RC_CQP, "CQP" },     { VA_RC_VBR_CONSTRAINED, "VBR_CONSTRAINED" },
		{ VA_RC_ICQ, "ICQ" },     { VA_RC_MB, "MB" },
		{ VA_RC_CFS, "CFS" },     { VA_RC_PARALLEL, "PARALLEL" },
		{ VA_RC_QVBR, "QVBR" },   { VA_RC_AVBR, "AVBR" },
		{ VA_RC_TCBRC, "TCBRC" },
	};
	if (!report || !byte)
		return;
	report[0] = 0;
	unsigned remaining = mask;
	for (size_t i = 0; i < sizeof(KNOWN) / sizeof(KNOWN[0]); i++) {
		if (!(mask & KNOWN[i].bit))
			continue;
		remaining &= ~KNOWN[i].bit;
		char piece[32];
		snprintf(piece, sizeof(piece), "%s%s", report[0] ? "|" : "", KNOWN[i].name);
		strncat(report, piece, byte - strlen(report) - 1);
	}
	if (remaining) {
		char piece[32];
		snprintf(piece, sizeof(piece), "%s0x%x(?)", report[0] ? "|" : "", remaining);
		strncat(report, piece, byte - strlen(report) - 1);
	}
	if (!report[0])
		strncat(report, "none", byte - 1);
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
	const uint8_t *data;
	size_t byte;
	size_t bit;   /* position, in bits */
	bool finished;  /* ⛔ three outcomes, not two: "0" and "I could not read" */
} BitReader;

/* ⭐ WHERE THE FRAME SITS in the SPS (D-023, phase 18): the position in bits — in
 *    the RBSP without emulation — of the cropping flag (`frame_cropping_flag` in
 *    H.264, `conformance_window_flag` in HEVC), the four offsets if there were any,
 *    and the bit after.  It lets `border_in_place()` rewrite the head
 *    of the SPS and copy the tail back as it is. */
typedef struct {
	size_t bit_flag;      /* where the flag sits */
	size_t bit_after;      /* the first bit after the flag and its offsets */
	bool is_present;        /* the flag was 1 */
	uint32_t sx, dx, su, down; /* the offsets read (0 if the flag was 0) */
} FramePosition;

static void lb_open(BitReader *l, const uint8_t *data, size_t byte)
{
	l->data = data;
	l->byte = byte;
	l->bit = 0;
	l->finished = false;
}

static uint32_t lb_bit(BitReader *l, int amount)
{
	uint32_t v = 0;
	for (int i = 0; i < amount; i++) {
		size_t idx = l->bit >> 3;
		if (idx >= l->byte) {
			l->finished = true;
			return v;
		}
		int gap = 7 - (int) (l->bit & 7);
		v = (v << 1) | (uint32_t) ((l->data[idx] >> gap) & 1);
		l->bit++;
	}
	return v;
}

/* ⭐ SIGNED Exp-Golomb — needed by the H.264 SPS (the scaling lists and the
 *    picture order count offsets), and HEVC did not need it here.
 * ⛔ The mapping is the standard's (9.1.1): k → (-1)^(k+1) * ceil(k/2). */
static int32_t lb_se(BitReader *l);

/* Unsigned Exp-Golomb, the H.265 one. */
static uint32_t lb_ue(BitReader *l)
{
	int zeros = 0;
	while (!l->finished && lb_bit(l, 1) == 0 && zeros < 32)
		zeros++;
	if (l->finished || zeros >= 32)
		return 0;
	return ((1u << zeros) - 1) + (zeros ? lb_bit(l, zeros) : 0);
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
#define NAL_VCL_MAX 31

typedef struct {
	bool ha_vps, ha_sps, ha_pps;
	bool ha_idr;
	bool parameters_before_idr; /* ⛔ the half that gets forgotten */
	bool first_vcl_is_key;
	size_t sps_offset, sps_byte;
} AnnexBLayout;

/* Finds the next start code: returns the offset of the first byte of the
 * NAL, or `byte` if there are no more.
 * ⛔ BOTH codes are recognised, `00 00 01` and `00 00 00 01`: a reader
 *    that knew only one would skip half the NALs **without complaining**, and
 *    would say "this stream has no PPS" of a stream that has it.  A false
 *    red costs as much as a false green. */
static size_t annexb_next(const uint8_t *d, size_t byte, size_t da, size_t *code_start)
{
	for (size_t i = da; i + 2 < byte; i++) {
		if (d[i] == 0 && d[i + 1] == 0 && d[i + 2] == 1) {
			if (code_start)
				*code_start = (i >= 1 && d[i - 1] == 0) ? i - 1 : i;
			return i + 3;
		}
	}
	if (code_start)
		*code_start = byte;
	return byte;
}

static void annexb_read(const uint8_t *d, size_t byte, AnnexBLayout *f)
{
	memset(f, 0, sizeof(*f));
	bool seen_vcl = false;
	bool p_vps = false, p_sps = false, p_pps = false;
	size_t body = annexb_next(d, byte, 0, NULL);
	while (body < byte) {
		size_t after_pos;
		size_t upcoming = annexb_next(d, byte, body, &after_pos);
		size_t fine = (upcoming < byte) ? after_pos : byte;
		int kind = (d[body] >> 1) & 0x3F;

		if (kind == NAL_VPS) {
			f->ha_vps = true;
			p_vps = true;
		} else if (kind == NAL_SPS) {
			f->ha_sps = true;
			p_sps = true;
			if (!f->sps_byte) {
				f->sps_offset = body;
				f->sps_byte = fine - body;
			}
		} else if (kind == NAL_PPS) {
			f->ha_pps = true;
			p_pps = true;
		} else if (kind <= NAL_VCL_MAX) {
			bool key = (kind == NAL_IDR_W_RADL || kind == NAL_IDR_N_LP || kind == NAL_CRA);
			if (!seen_vcl) {
				seen_vcl = true;
				f->first_vcl_is_key = key;
			}
			if (key) {
				f->ha_idr = true;
				/* ⛔ The group must be COMPLETE and come BEFORE this
				 *    IDR, not somewhere in the stream. */
				if (p_vps && p_sps && p_pps)
					f->parameters_before_idr = true;
			}
			p_vps = p_sps = p_pps = false;
		}
		body = upcoming;
	}
}

static int32_t lb_se(BitReader *l)
{
	uint32_t k = lb_ue(l);
	return (k & 1) ? (int32_t) ((k + 1) / 2) : -(int32_t) (k / 2);
}

/* Removes the emulation prevention bytes: `00 00 03` → `00 00`.
 * ⛔ Without this step an SPS that contains that sequence is read wrong, and
 *    the number that comes out of it (the bit depth) would be wrong WITHOUT
 *    looking it.  It is the same trap that ISO/IEC 14496-15 puts in the hvcC —
 *    one of the four reasons why D1 chooses Annex-B. */
static size_t remove_emulation(const uint8_t *inside, size_t byte, uint8_t *report, size_t maximum)
{
	size_t n = 0, zeros = 0;
	for (size_t i = 0; i < byte && n < maximum; i++) {
		if (zeros >= 2 && inside[i] == 3) {
			zeros = 0;
			continue;
		}
		report[n++] = inside[i];
		zeros = (inside[i] == 0) ? zeros + 1 : 0;
	}
	return n;
}

static uint32_t reverse32(uint32_t v)
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
#define NAL264_NOT_IDR 1
#define NAL264_IDR 5
#define NAL264_SPS 7
#define NAL264_PPS 8

typedef struct {
	bool ha_sps, ha_pps, ha_idr;
	bool parameters_before_idr;
	bool first_vcl_is_key;
	size_t sps_offset, sps_byte;
} AnnexB264Layout;

static void annexb264_read(const uint8_t *d, size_t byte, AnnexB264Layout *f)
{
	bool seen_vcl = false;
	bool p_sps = false, p_pps = false;
	size_t body;

	memset(f, 0, sizeof(*f));
	body = annexb_next(d, byte, 0, NULL);
	while (body < byte) {
		size_t after_pos;
		size_t upcoming = annexb_next(d, byte, body, &after_pos);
		size_t fine = (upcoming < byte) ? after_pos : byte;
		int kind = d[body] & 0x1F;

		if (kind == NAL264_SPS) {
			f->ha_sps = true;
			p_sps = true;
			if (!f->sps_byte) {
				f->sps_offset = body;
				f->sps_byte = fine - body;
			}
		} else if (kind == NAL264_PPS) {
			f->ha_pps = true;
			p_pps = true;
		} else if (kind >= NAL264_NOT_IDR && kind <= NAL264_IDR) {
			bool key = (kind == NAL264_IDR);
			if (!seen_vcl) {
				seen_vcl = true;
				f->first_vcl_is_key = key;
			}
			if (key) {
				f->ha_idr = true;
				if (p_sps && p_pps)
					f->parameters_before_idr = true;
			}
			p_sps = p_pps = false;
		}
		body = upcoming;
	}
}

/* The SPS scaling lists: their content is not read, they are SKIPPED — but they
 * are skipped by reading them, because they are variable-length and whoever counted them
 * in bytes would throw off everything that comes after (that is the size and the depth).
 */
static void skip_scaling_lists(BitReader *l, int how_many)
{
	for (int i = 0; i < how_many && !l->finished; i++) {
		if (!lb_bit(l, 1))
			continue;
		int measure = (i < 6) ? 16 : 64;
		int last = 8, upcoming = 8;
		for (int j = 0; j < measure && !l->finished; j++) {
			if (upcoming)
				upcoming = (last + lb_se(l) + 256) % 256;
			last = upcoming ? upcoming : last;
		}
	}
}

/*
 * ⭐ The H.264 SPS — and it serves the same two purposes as the HEVC SPS: the
 *    REAL depth (the second E2 witness) and the LEVEL, which ends up
 *    in the `avc1.<profile><constraints><level>` string the browser receives.
 *
 * ⛔ And the size is read down to the CROPPING.  Without it, a 1588x914 canvas (not
 *    a multiple of 16) would read as 1600x928 — that is the witness would accusations
 *    a correct stream of the wrong size, which is the false red of `LESSONS.md`
 *    §1.2.  ⚠ And the cropping units depend on the subsampling: 4:2:0
 *    counts two pixels per unit horizontally and two vertically.
 */
static bool read_h264_sps(const uint8_t *nal, size_t byte, EncoderConfession *c,
                           FramePosition *dove)
{
	uint8_t *rbsp;
	size_t n;
	BitReader l;
	uint32_t profile, level, constraints, chroma = 1, width_mb, height_mapunit;
	uint32_t below_w = 2, below_h = 2;
	uint32_t crop_left = 0, crop_right = 0, crop_top = 0, crop_bottom = 0;
	int frames_only;
	size_t bit_flag;

	if (byte < 5)
		return false;
	rbsp = malloc(byte);
	if (!rbsp)
		return false;
	/* ⛔ The NAL header byte is skipped BEFORE removing the emulation:
	 *    it is not part of the RBSP, and counting it would shift every bit by eight. */
	n = remove_emulation(nal + 1, byte - 1, rbsp, byte);
	lb_open(&l, rbsp, n);

	profile = lb_bit(&l, 8);
	/* ⛔⭐ THE CONSTRAINTS ARE NO LONGER THROWN AWAY — 23 Aug 2026.  Here there was a
	 *     `(void)`, and the byte ended up in nothing: it is the **CC** of
	 *     `avc1.PPCCLL`, that is exactly one third of the string the browser
	 *     passes to `configure()`.  ⚠ Throwing it away was the reason why that
	 *     string, under H.264, could not even be composed. */
	constraints = lb_bit(&l, 8);     /* constraint_set*_flag + the reserved bits */
	level = lb_bit(&l, 8);
	(void) lb_ue(&l);            /* seq_parameter_set_id */

	/* ⚠ Only the "high" profiles carry the chroma format and the depth: on
	 *   Baseline/Main they are NOT there, and reading them would shift all the rest.  It is
	 *   the standard's list (7.3.2.1.1), written out in full on purpose. */
	if (profile == 100 || profile == 110 || profile == 122 || profile == 244 || profile == 44
	    || profile == 83 || profile == 86 || profile == 118 || profile == 128 || profile == 138
	    || profile == 139 || profile == 134 || profile == 135) {
		chroma = lb_ue(&l);
		if (chroma == 3)
			(void) lb_bit(&l, 1);          /* separate_colour_plane_flag */
		c->stream_depth = 8 + (int) lb_ue(&l);   /* luma */
		(void) lb_ue(&l);                  /* chroma: read and not used */
		(void) lb_bit(&l, 1);              /* qpprime_y_zero_transform_bypass */
		if (lb_bit(&l, 1))
			skip_scaling_lists(&l, chroma == 3 ? 12 : 8);
	} else {
		/* ⛔ It is not "8 bits out of habit": on these profiles the standard
		 *    SAYS 8 and 4:2:0, so it is a fact that was read, not a default
		 *    value (`CODER.md` §3.10). */
		c->stream_depth = 8;
		chroma = 1;
	}
	if (chroma == 0) { below_w = 1; below_h = 1; }
	else if (chroma == 2) { below_w = 2; below_h = 1; }
	else if (chroma == 3) { below_w = 1; below_h = 1; }

	(void) lb_ue(&l);                      /* log2_max_frame_num_minus4 */
	{
		uint32_t order_type = lb_ue(&l);
		if (order_type == 0) {
			(void) lb_ue(&l);
		} else if (order_type == 1) {
			(void) lb_bit(&l, 1);
			(void) lb_se(&l);
			(void) lb_se(&l);
			uint32_t amount = lb_ue(&l);
			for (uint32_t i = 0; i < amount && !l.finished && i < 256; i++)
				(void) lb_se(&l);
		}
	}
	(void) lb_ue(&l);                      /* max_num_ref_frames */
	(void) lb_bit(&l, 1);                  /* gaps_in_frame_num_value_allowed */
	width_mb = lb_ue(&l) + 1;
	height_mapunit = lb_ue(&l) + 1;
	frames_only = (int) lb_bit(&l, 1);
	if (!frames_only)
		(void) lb_bit(&l, 1);              /* mb_adaptive_frame_field_flag */
	(void) lb_bit(&l, 1);                  /* direct_8x8_inference_flag */
	bit_flag = l.bit;
	if (lb_bit(&l, 1)) {                   /* frame_cropping_flag */
		crop_left = lb_ue(&l);
		crop_right = lb_ue(&l);
		crop_top = lb_ue(&l);
		crop_bottom = lb_ue(&l);
		if (dove)
			dove->is_present = true;
	} else if (dove) {
		dove->is_present = false;
	}
	if (dove) {
		dove->bit_flag = bit_flag;
		dove->bit_after = l.bit;
		dove->sx = crop_left;
		dove->dx = crop_right;
		dove->su = crop_top;
		dove->down = crop_bottom;
	}
	free(rbsp);
	if (l.finished)
		return false;

	c->stream_profile = (int) profile;
	c->stream_level = (int) level;
	/* ⛔⭐⭐ THE STRING FOR THE DECODER, AND UNTIL 23 AUG 2026 UNDER
	 *      H.264 THIS FIELD STAYED EMPTY.
	 *
	 *      `read_hevc_sps()` composed it (`hev1.1.6.L150.B0`), `leggi_sps_
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
	 * ⭐ It is the same form that `src/page.html` composes on its side
	 *    (`stringhe_codec()`, `avc1.6400` + the level in hexadecimal): the two
	 *    ends line up, and if they diverge it shows here.  `[M]` with
	 *    `DECLARED_LEVEL = "5.1"` the page asks for `avc1.640033`, and this
	 *    reader must say the same thing. */
	/* ⚠ LOWERCASE, and it is not taste: `src/page.html` composes its own with
	 *   `toString(16)`, which writes lowercase.  Two strings that must be
	 *   comparable by eye in the log do not differ by the case of
	 *   a letter. */
	snprintf(c->codec_string, sizeof(c->codec_string), "avc1.%02x%02x%02x",
	         profile & 0xFFu, constraints & 0xFFu, level & 0xFFu);
	{
		uint32_t unit_w = (chroma == 0) ? 1 : below_w;
		uint32_t unit_h = (uint32_t) ((chroma == 0 ? 1 : below_h) * (2 - frames_only));
		uint32_t width = width_mb * 16;
		uint32_t height = height_mapunit * 16 * (uint32_t) (2 - frames_only);
		uint32_t via_l = (crop_left + crop_right) * unit_w;
		uint32_t via_a = (crop_top + crop_bottom) * unit_h;

		c->stream_width = (width > via_l) ? width - via_l : width;
		c->stream_height = (height > via_a) ? height - via_a : height;
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
 *    (`video.level`: the server MUST emit a stream of a level no
 *    higher than the one declared by the client, and **does not guess it**) and for the
 *    `hev1.2.4.L93.B0` string of `VideoDecoder.configure()`.
 */
static bool read_hevc_sps(const uint8_t *nal, size_t byte, EncoderConfession *c,
                           FramePosition *dove)
{
	if (byte < 4)
		return false;
	uint8_t *rbsp = malloc(byte);
	if (!rbsp)
		return false;
	size_t n = remove_emulation(nal + 2, byte - 2, rbsp, byte); /* 2 = NAL header */

	BitReader l;
	lb_open(&l, rbsp, n);
	lb_bit(&l, 4);                              /* sps_video_parameter_set_id */
	uint32_t max_sub = lb_bit(&l, 3);           /* sps_max_sub_layers_minus1 */
	lb_bit(&l, 1);                              /* sps_temporal_id_nesting_flag */

	/* profile_tier_level(1, max_sub) */
	uint32_t space = lb_bit(&l, 2);
	uint32_t tier = lb_bit(&l, 1);
	uint32_t profile = lb_bit(&l, 5);
	uint32_t compat = lb_bit(&l, 32);
	uint8_t constraints[6];
	for (int i = 0; i < 6; i++)
		constraints[i] = (uint8_t) lb_bit(&l, 8); /* 48 bits: the source flags and the reserved ones */
	uint32_t level = lb_bit(&l, 8);

	uint32_t profile_present[8] = { 0 }, level_present[8] = { 0 };
	for (uint32_t i = 0; i < max_sub; i++) {
		profile_present[i] = lb_bit(&l, 1);
		level_present[i] = lb_bit(&l, 1);
	}
	if (max_sub > 0)
		for (uint32_t i = max_sub; i < 8; i++)
			lb_bit(&l, 2); /* reserved_zero_2bits */
	for (uint32_t i = 0; i < max_sub; i++) {
		if (profile_present[i]) {
			lb_bit(&l, 2); lb_bit(&l, 1); lb_bit(&l, 5);
			lb_bit(&l, 32);
			for (int k = 0; k < 6; k++)
				lb_bit(&l, 8);
		}
		if (level_present[i])
			lb_bit(&l, 8);
	}

	lb_ue(&l);                                  /* sps_seq_parameter_set_id */
	uint32_t chroma = lb_ue(&l);                 /* chroma_format_idc */
	if (chroma == 3)
		lb_bit(&l, 1);                          /* separate_colour_plane_flag */
	uint32_t width = lb_ue(&l);
	uint32_t height = lb_ue(&l);
	uint32_t coded_width = width, coded_height = height;
	/*
	 * ⛔⭐ THE CONFORMANCE WINDOW IS APPLIED — and until 13 Aug 2026 this
	 *     read SKIPPED it (four `lb_ue()` thrown away).
	 *
	 * ⚠ It had never been seen because `libx265` at 1920×1080 does not put one: 1080
	 *   is a multiple of 8 and fits without padding.  ⛔ `hevc_vaapi` **on AMD**
	 *   (radeonsi, navi21) encodes **1920×1088** and crops to 1080 with the
	 *   window — and the `bitstream_ok()` check refused EVERY frame
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
		uint32_t left_edge = lb_ue(&l), right_edge = lb_ue(&l);
		uint32_t above = lb_ue(&l), below = lb_ue(&l);
		uint32_t sub_l = (chroma == 1 || chroma == 2) ? 2 : 1;
		uint32_t sub_a = (chroma == 1) ? 2 : 1;
		uint32_t cut_w = sub_l * (left_edge + right_edge);
		uint32_t cut_h = sub_a * (above + below);
		if (dove) {
			dove->is_present = true;
			dove->sx = left_edge;
			dove->dx = right_edge;
			dove->su = above;
			dove->down = below;
		}
		/* ⚠ A crop bigger than the picture is not subtracted: it is left alone and
		 *   the caller will see a size that does not match, which is better than a
		 *   number that goes below zero and becomes huge. */
		if (cut_w < width)
			width -= cut_w;
		if (cut_h < height)
			height -= cut_h;
	}
	if (dove)
		dove->bit_after = l.bit;
	uint32_t bit_luma = lb_ue(&l) + 8;
	uint32_t bit_chroma = lb_ue(&l) + 8;
	free(rbsp);

	if (l.finished)
		return false;

	c->stream_depth = (int) (bit_luma < bit_chroma ? bit_luma : bit_chroma);
	c->stream_profile = (int) profile;
	c->stream_level = (int) level;
	c->tier_alto = tier != 0;
	c->stream_width = width;
	c->stream_height = height;
	c->encoded_width = coded_width;
	c->encoded_height = coded_height;
	c->stream_chroma = (int) chroma;

	/* ⭐ The string for `VideoDecoder.configure()`, built from the real bytes.
	 *   ⛔ `hev1` and not `hvc1`: the parameter sets travel in band.  ⚠ And `[M]`
	 *      F2.5 measured that **the prefix does not matter**: Chromium decides from the
	 *      presence of the `description`, not from the prefix.  `hev1` is written
	 *      anyway, because it is the one that describes the truth of the stream. */
	char constraints_text[24] = { 0 };
	int last = -1;
	for (int i = 0; i < 6; i++)
		if (constraints[i])
			last = i;
	for (int i = 0; i <= last; i++) {
		char piece[8];
		snprintf(piece, sizeof(piece), ".%02X", constraints[i]);
		strncat(constraints_text, piece, sizeof(constraints_text) - strlen(constraints_text) - 1);
	}
	char space_text[2] = { 0 };
	if (space > 0)
		space_text[0] = (char) ('A' + space - 1);
	snprintf(c->codec_string, sizeof(c->codec_string), "hev1.%s%u.%X.%c%u%s",
	         space_text, profile, reverse32(compat), tier ? 'H' : 'L', level,
	         constraints_text);
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════
 * AV1 — the OBU temporal units
 *
 * ⚠ Here there is no `hvcC` to defend against: AV1 "takes the temporal
 *   units as they are" (`DECISIONS.md` §1.13).  ⛔ But the half that gets
 *   forgotten is identical: the **sequence header OBU** must sit in front of every
 *   keyframe, or a client that connects later receives a bare key —
 *   the same black screen with the frames arriving.
 * ═══════════════════════════════════════════════════════════════════════════ */
#define OBU_SEQUENCE_HEADER 1
#define OBU_TEMPORAL_DELIMITER 2
#define OBU_FRAME_HEADER 3
#define OBU_FRAME 6

typedef struct {
	bool has_sequence;
	bool has_key;
	bool sequence_before_key;
	bool first_frame_is_key;
	size_t seq_offset, seq_byte;
} ObuLayout;

static uint64_t read_leb128(const uint8_t *d, size_t byte, size_t *dove)
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

static void obu_read(const uint8_t *d, size_t byte, ObuLayout *f)
{
	memset(f, 0, sizeof(*f));
	bool seen_frame = false, seq_in_progress = false;
	size_t i = 0;
	while (i < byte) {
		size_t start = i;
		uint8_t head = d[i++];
		int kind = (head >> 3) & 0xF;
		bool extension = (head >> 2) & 1;
		bool has_size = (head >> 1) & 1;
		if (extension && i < byte)
			i++;
		uint64_t trim;
		if (has_size)
			trim = read_leb128(d, byte, &i);
		else
			trim = byte - i; /* ⚠ without a size field the OBU runs to the end of the buffer */
		if (i + trim > byte)
			trim = byte - i;

		if (kind == OBU_SEQUENCE_HEADER) {
			f->has_sequence = true;
			seq_in_progress = true;
			if (!f->seq_byte) {
				f->seq_offset = i;
				f->seq_byte = (size_t) trim;
			}
		} else if (kind == OBU_FRAME || kind == OBU_FRAME_HEADER) {
			BitReader l;
			lb_open(&l, d + i, (size_t) trim);
			bool key = false;
			if (lb_bit(&l, 1) == 0)                 /* show_existing_frame */
				key = (lb_bit(&l, 2) == 0);      /* frame_type: 0 = KEY_FRAME */
			if (!seen_frame) {
				seen_frame = true;
				f->first_frame_is_key = key;
			}
			if (key) {
				f->has_key = true;
				if (seq_in_progress)
					f->sequence_before_key = true;
			}
			seq_in_progress = false;
		}
		i += (size_t) trim;
		if (i <= start)
			break; /* ⛔ a zero-size OBU would stop the loop here instead of never */
	}
}

/* The sequence header OBU, down to the bit depth.  Follows AV1 §5.5. */
static bool read_av1_sequence(const uint8_t *d, size_t byte, EncoderConfession *c)
{
	BitReader l;
	lb_open(&l, d, byte);
	uint32_t profile = lb_bit(&l, 3);
	lb_bit(&l, 1); /* still_picture */
	uint32_t reduced = lb_bit(&l, 1);
	uint32_t level = 0, tier = 0;
	uint32_t model_decoding = 0, initial_delay = 0;

	if (reduced) {
		level = lb_bit(&l, 5);
	} else {
		if (lb_bit(&l, 1)) {              /* timing_info_present_flag */
			lb_bit(&l, 32); lb_bit(&l, 32);
			if (lb_bit(&l, 1) == 0) {     /* equal_picture_interval */
				/* uvlc(): nothing to keep */
				int zeros = 0;
				while (!l.finished && lb_bit(&l, 1) == 0 && zeros < 32)
					zeros++;
				if (zeros && zeros < 32)
					lb_bit(&l, zeros);
			}
			model_decoding = lb_bit(&l, 1);
			if (model_decoding) {
				lb_bit(&l, 5); lb_bit(&l, 32); lb_bit(&l, 5); lb_bit(&l, 5);
			}
		}
		initial_delay = lb_bit(&l, 1);
		uint32_t amount = lb_bit(&l, 5);
		for (uint32_t k = 0; k <= amount; k++) {
			lb_bit(&l, 12);               /* operating_point_idc */
			uint32_t liv = lb_bit(&l, 5);
			uint32_t ti = 0;
			if (liv > 7)
				ti = lb_bit(&l, 1);
			if (k == 0) {
				level = liv;
				tier = ti;
			}
			if (model_decoding && lb_bit(&l, 1)) {
				/* operating_parameters_info: two delays and a flag.  ⚠ The
				 * length depends on buffer_delay_length, which we do not
				 * keep here: if this branch lit up, the read
				 * would become unreliable and the caller sees it from
				 * `read_from_stream = false`. */
				return false;
			}
			if (initial_delay && lb_bit(&l, 1))
				lb_bit(&l, 4);
		}
	}
	uint32_t bit_l = lb_bit(&l, 4) + 1;
	uint32_t bit_a = lb_bit(&l, 4) + 1;
	uint32_t width = lb_bit(&l, (int) bit_l) + 1;
	uint32_t height = lb_bit(&l, (int) bit_a) + 1;

	if (!reduced && lb_bit(&l, 1)) { /* frame_id_numbers_present_flag */
		lb_bit(&l, 4);
		lb_bit(&l, 3);
	}
	lb_bit(&l, 1); /* use_128x128_superblock */
	lb_bit(&l, 1); /* enable_filter_intra */
	lb_bit(&l, 1); /* enable_intra_edge_filter */
	if (!reduced) {
		lb_bit(&l, 1); /* enable_interintra_compound */
		lb_bit(&l, 1); /* enable_masked_compound */
		lb_bit(&l, 1); /* enable_warped_motion */
		lb_bit(&l, 1); /* enable_dual_filter */
		uint32_t order = lb_bit(&l, 1);
		if (order) {
			lb_bit(&l, 1); /* enable_jnt_comp */
			lb_bit(&l, 1); /* enable_ref_frame_mvs */
		}
		uint32_t force = 2;
		if (lb_bit(&l, 1) == 0)          /* seq_choose_screen_content_tools */
			force = lb_bit(&l, 1);
		if (force > 0 && lb_bit(&l, 1) == 0)
			lb_bit(&l, 1);               /* seq_force_integer_mv */
		if (order)
			lb_bit(&l, 3);               /* order_hint_bits_minus_1 */
	}
	lb_bit(&l, 1); /* enable_superres */
	lb_bit(&l, 1); /* enable_cdef */
	lb_bit(&l, 1); /* enable_restoration */

	/* color_config() */
	uint32_t alto = lb_bit(&l, 1);
	int depth;
	if (profile == 2 && alto)
		depth = lb_bit(&l, 1) ? 12 : 10;
	else
		depth = alto ? 10 : 8;

	if (l.finished)
		return false;

	c->stream_depth = depth;
	c->stream_profile = (int) profile;
	c->stream_level = (int) level;
	c->tier_alto = tier != 0;
	c->stream_width = width;
	c->stream_height = height;
	c->stream_chroma = 1; /* ⚠ the two formats SVT-AV1 accepts are 4:2:0 */

	/* ⚠ `seq_level_idx = 4` is NOT "level 4": it is 3.0 — the string takes
	 *   the INDEX (`DECISIONS.md` §1.13). */
	snprintf(c->codec_string, sizeof(c->codec_string), "av01.%u.%02u%c.%02d",
	         profile, level, tier ? 'H' : 'M', depth);
	return true;
}

/* ═══════════════════════════════════════════════════════════════════════════ */

/* ⛔ How many DMA-BUF imports are kept in the cache.  ⚠ The number is not one of
 *    convenience: the producer recycles `[M]` **four** buffers (`DECISIONS.md`
 *    §2.3-ter) and on the card route we ask it for **six**, because
 *    holding back takes two.  Eight covers all cases with margin, and when the
 *    cache is full we start over instead of evicting at random: a
 *    wrong policy on eight entries would cost more lines than it gives back. */
#define IMPORTED_MAX 8

/* ⛔ How many INPUT surfaces the card's store keeps.  With the wait
 *    on every frame one would be enough; four are kept so as not to
 *    rewrite the one the VPP has just filled while the driver is
 *    still reading it, on a driver that kept one round in the pipe. */
#define READY_SURFACES 4


/* ⛔ The number lives in ONE place only, with the measurement next to it in `encoder.h`.
 *    ⚠ It is not a multiple chosen out of caution: it is the boundary measured to the pixel
 *    between 1552 (which reads) and 1544 (which does not). */
#define CARD_ALIGNMENT 64u


/* ⭐ PHASE 19 — the card route.  `NESSUNA` in a request means
 *    "by capability" (`h264_card`); in an encoder that was born it is always one
 *    of the two. */
typedef enum { ROUTE_NONE = 0, ROUTE_VAAPI, ROUTE_VULKAN } Strada;

static const char *route_name(Strada s)
{
	return s == ROUTE_VULKAN ? "vulkan" : s == ROUTE_VAAPI ? "vaapi" : "";
}

struct Encoder {
	CodificatoreRichiesta request;
	/* ⛔ The component name is a REMOTIX LABEL, and it is the one
	 *    OPENED: `h264_vulkan`/`hevc_vulkan` or `h264_vaapi`/`hevc_vaapi`.  Whoever
	 *    asked for `h264_card` (by capability) reads here which of the two
	 *    came out.  `child.c` and `--encoding-test` write it to the log and
	 *    to the JSON, and the installer reads the outcome, not the name. */
	char component_name[64];
	/* ⭐ The route REQUESTED (NESSUNA = by capability) and the one OPENED. */
	Strada requested_route;
	Strada route;
	/* ⭐ The STAGING buffer of the from-memory route IN HARDWARE: the frame
	 *    converted on the CPU (NV12 or P010, `colors709.c`) before being uploaded to the
	 *    card.  Empty on the zero copy (the frame is already on the card). */
	uint8_t *staging;
	size_t staging_byte;
	EncoderConfession conf;
	/* ⭐ The entrypoint CHOSEN in `open_device()` after reading it from the
	 *    driver: it is what is asked of vadiretta and what the reread is compared
	 *    against.  ⛔ Not `request.power`: with
	 *    `LA_DICHIARATA` the request alone does not say which of the two. */
	bool low_power_choice;
	/* ⚠ 400 and not 160: it holds the VA vendor in full — "Intel iHD
	 *   driver for Intel(R) Gen Graphics - 25.2.3 ()" is already 53 bytes.  A name
	 *   truncated in the log removes precisely the piece that says WHICH machine made
	 *   the number. */
	char name[400];

	/* ───────────────────────────────────────────────────────────────────────
	 * ⭐ THE CARD ROUTE.  ⛔ Since phase 19 `hardware` is always true
	 *    in an encoder that was born: `codificatore_nuovo()` refuses every name that
	 *    does not belong to the card.  The field stays because `codificatore_libera()`
	 *    can run on a half-built encoder (the device not yet
	 *    open), and because the Vulkan route will be grafted alongside.
	 */
	bool hardware;
	VaDevice device;    /* the open node: display and vendor */
	VAProfile profile_va;         /* the pair chosen and VERIFIED in open_device() */
	VAEntrypoint entrypoint_va;
	VaDirect *va;                /* the encoder on the card */
	VASurfaceID surface_ready; /* the input filled by prepara_*, to be encoded */
	/* ⭐ PHASE 19 — the VULKAN VIDEO route: the device (instance, card chosen
	 *    from the node, queues) lives as long as the encoder, like `device` above;
	 *    the encoder (`vk`) is closed and reopened with the context, like
	 *    `va`.  ⚠ The cache of imported DMA-BUFs sits INSIDE `vk` (one per
	 *    session): on every reopening it is reimported — it costs one import per
	 *    buffer, and the producer recycles four. */
	VulkanVideoDevice *vk_device;
	VulkanVideo *vk;
	VulkanVideoCapabilities vk_capabilities; /* read in open_device(), for the choice */

	/* ───────────────────────────────────────────────────────────────────────
	 * ⭐⭐⭐ ZERO COPY — the three things needed, and nothing else
	 *
	 *   1. the VPP CONTEXT: the RGB → NV12 conversion done by the GPU, which
	 *      takes the place of the CPU conversion **and** of the upload
	 *      together.  ⛔ It lives on the DEVICE and not on the encoder's
	 *      context: `lower_quality()` closes and reopens the encoder
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
	VAConfigID vpp_configuration;
	VAContextID vpp_context;
	bool vpp_open;
	uint32_t vpp_l, vpp_a;        /* the size the VPP was opened for */
	/* ⭐ The padding layers of `convert_on_gpu()` (15 Oct 2026): off when
	 *    REMOTIX_VPP_PADDING=0, or after the driver refused them once. */
	bool vpp_padding_off;
	bool vpp_padding_logged;
	struct {
		int fd;
		uint32_t l, a, stride, offset, formato_drm;
		uint64_t modifier;
		VASurfaceID surface;
	} imported[IMPORTED_MAX];
	unsigned how_many_imported;
	uint64_t cache_generation;
	bool cache_created;
	bool logged_zero_copy;        /* the first-time line, once only */

	bool next_key;         /* ⛔ the next one is a REAL key */
	bool first_encode_done;
	bool emptied;                /* ⚠ it was put into drain: it must be reopened */
	/* ⭐ THE FRAME (D-023, phase 16): the conformance window rewritten
	 *    in the SPS when the driver does not write it there.  ⭐ Since phase 18
	 *    `border_in_place()` rewrites it with the bits.  It is decided on the first SPS of
	 *    each context. */
	bool decided_border;
	bool active_border;
	uint32_t border_dx, border_dy; /* columns and rows to crop on the right and at the bottom */
	/* ⭐ THE BYTES THAT ARE DELIVERED — ours, for both routes.  The
	 *    encoder (card or software) produces them in its buffer; here they are
	 *    copied (`[M]` a 4K key is ~1 MB: tens of µs) so that the
	 *    frame can rewrite them and so that `report->data` does not depend on the
	 *    life of the encoder's buffer — the defect of 23 Aug 2026. */
	uint8_t *output;
	size_t output_capabilities, output_byte;
	int current_quality;         /* CRF in force, after any re-encodings */
	ModoQualita current_mode;
	/* ⭐ THE CLIMB (phase 9).  ⛔ The floor does NOT live here: it is `request.quality`,
	 *    which `codificatore_nuovo()` keeps intact.  A second field with the
	 *    same number inside would be the E2 form — two measurements under the same
	 *    label, and the day they diverge no bench notices. */
	int failed_quality;          /* the rung on which the ceiling BIT; 0 = never */
	uint32_t below_margin;       /* frames in a row comfortably below the ceiling */
	uint32_t rise_wait;     /* how many are needed NOW: doubles on every relapse */
	bool recently_risen;        /* to recognise the relapse, and only for that */
	/* ⭐⭐⭐ THE THIRD BITRATE WITNESS — THE BYTES, and it is the only one that would have
	 *      caught R31.  See the bandwidth ceiling box: the first witness
	 *      says the mode **exists**, the second that the driver
	 *      **kept** it, and in v1 they would **both have been green** while
	 *      CBR came out.  ⛔ Only these four fields say it. */
	uint64_t bandwidth_t0_us;         /* when the current window started */
	uint64_t bandwidth_byte;          /* how many came out inside the window */
	uint32_t bandwidth_frames;
	uint32_t bandwidth_max;       /* the biggest: it is the peak, not the average */
	int64_t nr;               /* the pts, which here is the frame counter */
	bool packet_in_hand;       /* `output` is in the caller's hands until rilascia() */
};

/* ⚠ Declared here and defined with the rest of the zero copy, much further down:
 *   `codificatore_libera()` sits in between and must call them.  ⛔ Moving their
 *   definition up here would separate the GPU conversion from its
 *   box, which is the place where it is explained. */
static void drop_imported(Encoder *c, const char *why);
static void close_vpp(Encoder *c);
/* ⭐ Phase 19: the bytes in `c->output` are common to both routes, and the
 *    Vulkan round (`encode_vulkan`, with the zero copy box) puts them there. */
static bool put_in_output(Encoder *c, const uint8_t *data, size_t byte);

static uint64_t now_us(void)
{
	struct timespec t;
	clock_gettime(CLOCK_MONOTONIC, &t);
	return (uint64_t) t.tv_sec * 1000000u + (uint64_t) t.tv_nsec / 1000u;
}

static void di(char *dove, size_t how_much, const char *fmt, ...)
{
	if (!dove || !how_much)
		return;
	va_list ap;
	va_start(ap, fmt);
	vsnprintf(dove, how_much, fmt, ap);
	va_end(ap);
}

/* ⛔ The name for the log lives in ONE place only: until 20 Aug 2026 it was
 *    a `? :` repeated on six lines, and with the third codec each would have said
 *    "AV1" of an H.264 stream — six lies to fix one by one. */
static const char *codec_name(CodecVideo codec)
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
static const char *mode_name(ModoQualita mode)
{
	switch (mode) {
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
 * ⚠ A `strstr(name, "_vaapi")` would be the same thing written badly: the day
 *   `hevc_qsv` or `hevc_vulkan` were tried the line would say "software" of
 *   a hardware encoder, and the symptom would be swscale converting
 *   to a format the component does not accept — that is an error that names
 *   neither the GPU nor the name.  ⇒ We look at what it DECLARES: a
 *   hardware encoder accepts a surface format, not a pixel format.
 */
/*
 * ⭐ PHASE 18: the answer is given by the NAMES that REMOTIX reserves for the card.
 *    ⚠ It is not the `strstr(name, "_vaapi")` that the note above forbade: that one
 *    guessed among the components of another library; these are OUR
 *    labels, and a seventh (`hevc_qsv`) does not exist here and does not open —
 *    it fails saying so.
 * ⭐ PHASE 19: the names are six (`encoder.h`): `*_scheda` = the route is
 *    chosen by capability, `*_vulkan` and `*_vaapi` = that one and nothing else.
 */
static bool component_of_card(const char *name, CodecVideo *codec, Strada *route)
{
	static const struct {
		const char *name;
		CodecVideo codec;
		Strada route;
	} names[] = {
		{ "h264_card", CODIFICATORE_H264, ROUTE_NONE },
		{ "hevc_card", CODIFICATORE_HEVC, ROUTE_NONE },
		{ "h264_vulkan", CODIFICATORE_H264, ROUTE_VULKAN },
		{ "hevc_vulkan", CODIFICATORE_HEVC, ROUTE_VULKAN },
		{ "h264_vaapi", CODIFICATORE_H264, ROUTE_VAAPI },
		{ "hevc_vaapi", CODIFICATORE_HEVC, ROUTE_VAAPI },
	};
	for (size_t i = 0; i < sizeof names / sizeof names[0]; i++)
		if (strcmp(name, names[i].name) == 0) {
			if (codec)
				*codec = names[i].codec;
			if (route)
				*route = names[i].route;
			return true;
		}
	return false;
}

/* The Vulkan bitrate modes, by name (the `VULKANVIDEO_RC_*` mask). */
static void vulkan_mode_names(unsigned mask, char *report, size_t byte)
{
	snprintf(report, byte, "%s%s%s", (mask & VULKANVIDEO_RC_CQP) ? "CQP " : "",
	         (mask & VULKANVIDEO_RC_CBR) ? "CBR " : "",
	         (mask & VULKANVIDEO_RC_VBR) ? "VBR " : "");
	if (!report[0])
		snprintf(report, byte, "none");
}

/*
 * ⭐⭐ PHASE 19 — IS VULKAN VIDEO SUITABLE FOR THIS REQUEST?  We ask the
 *     node's card (`vulkanvideo_capabilities`: it opens and closes everything by itself)
 *     and compare with what the request wants: the codec at that
 *     depth, the canvas within the limits, the bitrate mode the ceiling
 *     asks for, the input format (the shader takes RGB: the bench that comes in
 *     as yuv420p10le stays on VA-API).
 *
 * ⛔ THREE OUTCOMES AND NOT TWO here too: "suitable", "not suitable, and why" (we go to
 *    VA-API if the route is by capability), and "asked for by name and not suitable",
 *    which is a refusal.  ⚠ `why` is always written: the log line
 *    must say WHY on this machine the other route was taken.
 */
static bool vulkan_fit(Encoder *c, char *why, size_t why_byte)
{
	const CodificatoreRichiesta *r = &c->request;
	VulkanVideoCapabilities *cap = &c->vk_capabilities;
	const VulkanVideoProfileCapabilities *p;
	char error[256] = { 0 };
	const char *profile;

	if (r->fmt == CODIFICATORE_PIXEL_YUV420P10LE) {
		di(why, why_byte,
		   "the input is yuv420p10le (the bench): the Vulkan route takes RGB and converts it "
		   "with the shader, not planes already converted");
		return false;
	}
	if (r->codec == CODIFICATORE_H264 && r->depth != 8) {
		di(why, why_byte, "H.264 at %d bits: in Vulkan only High at 8 bits is opened", r->depth);
		return false;
	}
	if (r->codec != CODIFICATORE_H264 && r->codec != CODIFICATORE_HEVC) {
		di(why, why_byte, "the codec %s is not encoded on the card", codec_name(r->codec));
		return false;
	}
	if (!vulkanvideo_capabilities(r->nodo_rendering, cap, error, sizeof error)) {
		di(why, why_byte, "no Vulkan device with the encode queue on «%s»: %s",
		   r->nodo_rendering, cap->why[0] ? cap->why : error);
		return false;
	}
	if (r->codec == CODIFICATORE_H264) {
		p = &cap->h264;
		profile = "H.264 High";
	} else if (r->depth == 10) {
		p = &cap->hevc10;
		profile = "HEVC Main 10";
	} else {
		p = &cap->hevc;
		profile = "HEVC Main";
	}
	if (!p->encode) {
		di(why, why_byte, "«%s» (%s) in Vulkan does NOT declare %s encoding", cap->card_name,
		   cap->driver, profile);
		return false;
	}
	if (r->width > p->max_size_w || r->height > p->max_size_h
	    || r->width < p->min_size_w || r->height < p->min_size_h) {
		di(why, why_byte,
		   "«%s» in Vulkan encodes %s between %ux%u and %ux%u, and the canvas is %ux%u", cap->card_name,
		   profile, p->min_size_w, p->min_size_h, p->max_size_w,
		   p->max_size_h, r->width, r->height);
		return false;
	}
	/* ⛔ R31 from the Vulkan end: the mode is asked for by name and we check that the
	 *    card DECLARES it — with the ceiling VBR is needed, without it CQP. */
	if (cap_floor_mbit && !(p->bitrate_modes & VULKANVIDEO_RC_VBR)) {
		char modes[48];
		vulkan_mode_names(p->bitrate_modes, modes, sizeof modes);
		di(why, why_byte, "the bandwidth ceiling wants VBR and «%s» in Vulkan declares [%s]",
		   cap->card_name, modes);
		return false;
	}
	if (!cap_floor_mbit && !(p->bitrate_modes & VULKANVIDEO_RC_CQP)) {
		char modes[48];
		vulkan_mode_names(p->bitrate_modes, modes, sizeof modes);
		di(why, why_byte, "constant QP wants CQP and «%s» in Vulkan declares [%s]",
		   cap->card_name, modes);
		return false;
	}
	if (p->qp_max > 0 && (c->current_quality < p->qp_min || c->current_quality > p->qp_max)) {
		di(why, why_byte, "QP %d outside what «%s» declares in Vulkan (%d..%d)",
		   c->current_quality, cap->card_name, p->qp_min, p->qp_max);
		return false;
	}
	/* the API version as Vulkan packs it (variant:3, major:7,
	 * minor:10, patch:12): unpacked here so as not to include `vulkan.h` */
	di(why, why_byte, "«%s» (%s, API %u.%u) declares %s up to %ux%u, DMA-BUF %s",
	   cap->card_name, cap->driver, (cap->api_version >> 22) & 0x7fu,
	   (cap->api_version >> 12) & 0x3ffu, profile, p->max_size_w, p->max_size_h,
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

static VAProfile profile_va(CodecVideo codec, int depth)
{
	if (codec == CODIFICATORE_HEVC)
		return depth == 10 ? VAProfileHEVCMain10 : VAProfileHEVCMain;
	/* ⛔ H.264 HERE IS 8 BIT AND THAT IS ALL, and it is declared instead of tried:
	 *    `High10` exists in the standard but `[M]` `vainfo` on this machine
	 *    lists `VAProfileH264High` and not the 10 bit — and whoever asked for 10 bits
	 *    would get `VAProfileNone`, that is the software fallback, with the
	 *    same name and a rate ten times worse (the E2 form). */
	if (codec == CODIFICATORE_H264)
		return depth == 10 ? VAProfileNone : VAProfileH264High;
	return VAProfileNone;
}

/*
 * ⛔ THREE OUTCOMES, NOT TWO: `it is there`, `it is not there`, `I could not look`.
 * `LESSONS.md` §1.9 rule 1 — "empty" and "forbidden" look the same.
 */
typedef enum { EP_C_E, EP_ABSENT, EP_UNCHECKED } EntrypointOutcome;

static EntrypointOutcome entrypoint_c_e(VADisplay d, VAProfile p, VAEntrypoint wanted,
                                      char *seen_items, size_t seen_byte)
{
	int maximum = vaMaxNumEntrypoints(d);
	if (maximum <= 0)
		return EP_UNCHECKED;
	VAEntrypoint *listing = calloc((size_t) maximum, sizeof(*listing));
	if (!listing)
		return EP_UNCHECKED;
	int amount = 0;
	VAStatus st = vaQueryConfigEntrypoints(d, p, listing, &amount);
	if (st != VA_STATUS_SUCCESS) {
		free(listing);
		return EP_UNCHECKED;
	}
	EntrypointOutcome outcome = EP_ABSENT;
	if (seen_items && seen_byte)
		seen_items[0] = 0;
	for (int i = 0; i < amount; i++) {
		if (seen_items && seen_byte) {
			char piece[24];
			snprintf(piece, sizeof(piece), "%s%d", i ? "," : "", (int) listing[i]);
			strncat(seen_items, piece, seen_byte - strlen(seen_items) - 1);
		}
		if (listing[i] == wanted)
			outcome = EP_C_E;
	}
	free(listing);
	return outcome;
}

/*
 * Opens the VA-API device on the declared node, reads its VENDOR, and
 * checks that (profile, entrypoint) really exists before opening.
 */
static int open_device(Encoder *c, char *error, size_t error_byte)
{
	const CodificatoreRichiesta *r = &c->request;

	if (!r->nodo_rendering || !r->nodo_rendering[0]) {
		di(error, error_byte,
		   "«%s» is a HARDWARE encoder and no render node "
		   "was declared: ⛔ none is guessed — on this machine the two "
		   "nodes are from two different vendors [M]", c->component_name);
		return -1;
	}
	snprintf(c->conf.node, sizeof(c->conf.node), "%s", r->nodo_rendering);

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⭐⭐ PHASE 19 — VULKAN VIDEO FIRST, IF THE CARD OFFERS IT FOR THIS CODEC
	 *
	 * The route is chosen by CAPABILITY (`DECISIONS.md` §10.27): we ask
	 * the node's card what it can do in Vulkan and, if it can do what
	 * the request wants, we take that.  If not we write WHY and go
	 * to VA-API — unless Vulkan was asked for by name: then we
	 * fail saying so, because whoever asks by name is measuring.
	 * ⚠ `[M]` 1 Oct 2026 on the server: the Radeon RX 6800 (RADV, Mesa 25.0.7)
	 *   offers it for H.264 and HEVC; the Intel UHD 770 (ANV) does not, and stays on VA-API.
	 * ═══════════════════════════════════════════════════════════════════════ */
	if (c->requested_route != ROUTE_VAAPI) {
		char why[512] = { 0 };
		char error_vk[256] = { 0 };
		bool fit = vulkan_fit(c, why, sizeof why);

		if (fit) {
			c->vk_device = vulkanvideo_open_device(r->nodo_rendering, error_vk,
			                                                 sizeof error_vk);
			if (!c->vk_device) {
				fit = false;
				di(why, sizeof why,
				   "the capability is there but the Vulkan device did not open: %s", error_vk);
			}
		}
		if (fit) {
			const VulkanVideoProfileCapabilities *p =
			    r->codec == CODIFICATORE_H264 ? &c->vk_capabilities.h264
			    : r->depth == 10        ? &c->vk_capabilities.hevc10
			                                 : &c->vk_capabilities.hevc;
			char modes[48];

			c->route = ROUTE_VULKAN;
			snprintf(c->component_name, sizeof c->component_name, "%s_vulkan",
			         r->codec == CODIFICATORE_H264 ? "h264" : "hevc");
			snprintf(c->conf.route, sizeof c->conf.route, "vulkan");
			snprintf(c->conf.vendor_va, sizeof c->conf.vendor_va, "%s · %s",
			         vulkanvideo_card_name(c->vk_device),
			         vulkanvideo_driver_name(c->vk_device));
			c->conf.low_power = false;
			c->conf.low_power_verified = false;
			c->conf.max_size_w = p->max_size_w;
			c->conf.max_size_h = p->max_size_h;
			c->conf.misura_massima_letta = true;
			c->conf.bitrate_modes = p->bitrate_modes;
			c->conf.modi_bitrate_letti = true;
			vulkan_mode_names(p->bitrate_modes, modes, sizeof modes);
			registro_dice(LOG_ENCODING,
			              "⭐⭐ PHASE 19: VULKAN VIDEO route on «%s» — %s.  Requested %s.  "
			              "Declared bitrate modes [%s], QP %d..%d, granularity %ux%u, "
			              "headers from the driver %s, direct conversion into the planes %s.  "
			              "⚠ Whether it really encodes is said by the BYTES (bitstream_ok) and the "
			              "third witness, not by this line",
			              r->nodo_rendering, why,
			              c->requested_route == ROUTE_VULKAN ? "BY NAME"
			                                                 : "by CAPABILITY (Vulkan before VA-API)",
			              modes, p->qp_min, p->qp_max, p->granularity_w, p->granularity_h,
			              p->headers_from_driver ? "yes" : "NO",
			              p->input_writable_by_shader ? "yes" : "no (copy)");
			return 0;
		}
		if (c->requested_route == ROUTE_VULKAN) {
			di(error, error_byte,
			   "«%s» on «%s»: Vulkan Video does NOT encode %s here — %s.  ⛔ Requested by name: "
			   "no fallback to VA-API, it would be two measurements under the same label",
			   c->component_name, r->nodo_rendering, codec_name(r->codec), why);
			return -1;
		}
		registro_dice(LOG_ENCODING,
		              "⭐ PHASE 19: route by capability on «%s» — Vulkan Video is NOT "
		              "suitable for %s (%s) ⇒ trying VA-API",
		              r->nodo_rendering, codec_name(r->codec), why);
	}
	c->route = ROUTE_VAAPI;
	snprintf(c->component_name, sizeof c->component_name, "%s_vaapi",
	         r->codec == CODIFICATORE_H264 ? "h264" : "hevc");
	snprintf(c->conf.route, sizeof c->conf.route, "vaapi");

	if (r->power == ENCODER_POWER_UNDECLARED) {
		di(error, error_byte,
		   "«%s»: the entrypoint was not declared.  ⛔ `EncSliceLP` (low "
		   "power) and `EncSlice` (full) are NOT equivalent, and a default "
		   "(full) is not inherited: ask for FULL or LOW",
		   c->component_name);
		return -1;
	}

	/* ⭐ PHASE 18: the node is opened by `vadirect.c` (vaGetDisplayDRM + vaInitialize),
	 *    no longer by `av_hwdevice_ctx_create`.  It asks for the vendor itself. */
	if (!vadirect_open_device(r->nodo_rendering, &c->device, error, error_byte))
		return -1;

	VADisplay display = c->device.display;
	snprintf(c->conf.vendor_va, sizeof(c->conf.vendor_va), "%s",
	         c->device.vendor);

	VAProfile profile = profile_va(r->codec, r->depth);
	if (profile == VAProfileNone) {
		di(error, error_byte,
		   "in hardware only HEVC can be opened: for AV1, hardware encoding on "
		   "this machine DOES NOT EXIST [M] — `av1_vaapi` exits 218, «No usable "
		   "encoding profile found», 3 runs out of 3");
		return -1;
	}
	VAEntrypoint wanted = (r->power == ENCODER_POWER_FULL)
	                          ? VAEntrypointEncSlice
	                          : VAEntrypointEncSliceLP;
	char seen_items[128] = { 0 };
	EntrypointOutcome found =
	    entrypoint_c_e(display, profile, wanted, seen_items, sizeof(seen_items));

	/* ⭐ THE `LA_DICHIARATA` RULE, and it is written in both branches: the
	 *    line says WHICH entrypoint and WHY, with the driver's list alongside.
	 *    ⛔ We switch to full only on "the driver does NOT declare it" — on "I
	 *    could not look" we fail as for the other two questions. */
	if (r->power == ENCODER_POWER_DECLARED) {
		if (found == EP_C_E)
			registro_dice(LOG_ENCODING,
			              "⭐ entrypoint EncSliceLP (low power) on «%s» (%s): the "
			              "driver DECLARES it for profile %d [%s] ⇒ taking "
			              "that one — rule: LP if declared, otherwise full",
			              r->nodo_rendering, c->conf.vendor_va, (int) profile,
			              seen_items);
		else if (found == EP_ABSENT) {
			char seen_lp[128];
			snprintf(seen_lp, sizeof(seen_lp), "%s", seen_items[0] ? seen_items : "none");
			wanted = VAEntrypointEncSlice;
			found = entrypoint_c_e(display, profile, wanted, seen_items,
			                         sizeof(seen_items));
			if (found == EP_C_E)
				registro_dice(LOG_ENCODING,
				              "⭐⚠ entrypoint EncSlice (FULL) on «%s» (%s): the "
				              "driver does NOT declare EncSliceLP for profile %d and "
				              "declares EncSlice [%s] ⇒ taking full — rule: "
				              "LP if declared, otherwise full.  ⚠ They are two different "
				              "encodings: the numbers from here do not hold for LP",
				              r->nodo_rendering, c->conf.vendor_va, (int) profile,
				              seen_lp);
		}
	}

	switch (found) {
	case EP_C_E:
		c->low_power_choice = (wanted == VAEntrypointEncSliceLP);
		c->conf.low_power = c->low_power_choice;
		c->conf.low_power_verified = true;
		/* ⭐ The VERIFIED pair is the one `vadirect_open()` will use: it does not
		 *    rediscover it, it receives it. */
		c->profile_va = profile;
		c->entrypoint_va = wanted;
		break;
	case EP_ABSENT:
		if (r->power == ENCODER_POWER_DECLARED) {
			di(error, error_byte,
			   "on «%s» (%s) profile %d has NEITHER EncSliceLP NOR EncSlice: the "
			   "driver declares [%s].  ⛔ No hardware encoding for "
			   "this profile — and without a card there is no encoding (phase 19: the "
			   "software fallback has left)",
			   r->nodo_rendering, c->conf.vendor_va, (int) profile,
			   seen_items[0] ? seen_items : "none");
			return -1;
		}
		di(error, error_byte,
		   "on «%s» (%s) profile %d does NOT have the entrypoint %s: the driver "
		   "declares [%s].  ⛔ No fallback to the other — they are two different "
		   "encodings, and falling back would give two measurements under the same label",
		   r->nodo_rendering, c->conf.vendor_va, (int) profile,
		   wanted == VAEntrypointEncSliceLP ? "EncSliceLP (low power)"
		                                    : "EncSlice (full)",
		   seen_items[0] ? seen_items : "none");
		return -1;
	case EP_UNCHECKED:
	default:
		di(error, error_byte,
		   "on «%s» I could NOT read the entrypoints of profile %d: ⛔ it is not "
		   "\"there are none\", it is \"I did not look\", and we do not encode on a machine "
		   "that could not be queried",
		   r->nodo_rendering, (int) profile);
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
	 *   of `LESSONS.md` §1.8 — *declare instead of suffer*.  Here instead
	 *   `codificatore_nuovo()` fails **before**, saying the driver's number,
	 *   and `child.c` writes the refusal with its line.
	 *
	 * ⛔⛔ AND IT IS ASKED OF THE DRIVER AND NOT OF FFMPEG, which is the same lesson taken
	 *      from the other end: `[M]` **`-low_power 0` on the Intel opens the same
	 *      `EncSliceLP`, and ffmpeg does NOT fail** — it takes what is there.  ⇒ A
	 *      check made through the command line would give two measurements
	 *      under the same label (`LESSONS.md` §1.11).
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
		VAStatus st = vaGetConfigAttributes(display, profile, wanted, attr, 3);

		if (st != VA_STATUS_SUCCESS) {
			registro_dice(LOG_ENCODING,
			              "⚠ on «%s» I could NOT ask the driver for the maximum size "
			              "(vaGetConfigAttributes: %d): ⛔ it is NOT \"there is no limit\", it is "
			              "\"I did not look\".  If %ux%u were too big it will be "
			              "found out at the first frame",
			              r->nodo_rendering, (int) st, r->width, r->height);
		} else if (attr[0].value == VA_ATTRIB_NOT_SUPPORTED ||
		           attr[1].value == VA_ATTRIB_NOT_SUPPORTED) {
			registro_dice(LOG_ENCODING,
			              "⚠ «%s» (%s) does not DECLARE a maximum size for profile %d: "
			              "⛔ we do not conclude that there is none",
			              r->nodo_rendering, c->conf.vendor_va, (int) profile);
		} else {
			c->conf.max_size_w = attr[0].value;
			c->conf.max_size_h = attr[1].value;
			c->conf.misura_massima_letta = true;
			if (r->width > attr[0].value || r->height > attr[1].value) {
				di(error, error_byte,
				   "«%s» on «%s» (%s) encodes at most %ux%u — requested %ux%u.  ⛔ The "
				   "driver says so BEFORE, and we declare it instead of finding out at the first "
				   "frame (phase 19: without the card there is no encoding, no "
				   "software fallback)",
				   c->component_name, r->nodo_rendering, c->conf.vendor_va,
				   attr[0].value, attr[1].value, r->width, r->height);
				return -1;
			}
			registro_dice(LOG_ENCODING,
			              "⭐ the driver declares at most %ux%u for «%s» on %s, and "
			              "%ux%u fits — ASKED of the driver, not deduced from the name",
			              attr[0].value, attr[1].value, c->component_name,
			              c->conf.node, r->width, r->height);
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
		BitrateMode mode = wanted_bitrate_mode();
		char modes[192];
		if (st != VA_STATUS_SUCCESS) {
			registro_dice(LOG_ENCODING,
			              "⚠ on «%s» I could NOT ask the driver for the bitrate "
			              "control modes (vaGetConfigAttributes: %d): ⛔ it is NOT "
			              "\"there is only CQP\", it is \"I did not look\".  %s is asked for by "
			              "name anyway, and if it is not there the opening will fail saying so",
			              r->nodo_rendering, (int) st, mode.name);
		} else if (attr[2].value == VA_ATTRIB_NOT_SUPPORTED) {
			registro_dice(LOG_ENCODING,
			              "⚠ «%s» (%s), profile %d, %s: the driver DECLARES NO "
			              "bitrate control mode.  ⛔ And we do not conclude that there "
			              "is only one (that was libavcodec's deduction, «assuming CQP "
			              "only», and vadiretta does NOT make it): %s is asked for by name, and if "
			              "the driver refuses it the opening will fail saying so",
			              r->nodo_rendering, c->conf.vendor_va, (int) profile,
			              wanted == VAEntrypointEncSliceLP ? "EncSliceLP (low power)"
			                                               : "EncSlice (full)",
			              mode.name);
		} else {
			c->conf.bitrate_modes = attr[2].value;
			c->conf.modi_bitrate_letti = true;
			bitrate_mode_names(attr[2].value, modes, sizeof(modes));
			if (!(attr[2].value & mode.va_bit)) {
				/* ⛔ NO FALLBACK: it would be R31 from the other end — taking "what
				 *    is there" is exactly the gesture that in v1 made CBR come out
				 *    of a choice nobody had made. */
				di(error, error_byte,
				   "«%s» on «%s» (%s), profile %d, %s: the bitrate control mode %s (0x%x) "
				   "was requested and the driver DECLARES [%s] (0x%x) — "
				   "⛔ it is NOT there.  No fallback to another mode: it would be R31 from the other "
				   "end, that is a bitrate mode chosen by nobody",
				   c->component_name, r->nodo_rendering, c->conf.vendor_va,
				   (int) profile,
				   wanted == VAEntrypointEncSliceLP ? "EncSliceLP" : "EncSlice",
				   mode.name, mode.va_bit, modes, attr[2].value);
				return -1;
			}
			registro_dice(LOG_ENCODING,
			              "⭐ bitrate control on «%s» (%s), profile %d, %s: the "
			              "driver DECLARES [%s] (0x%x) · requested %s (0x%x) · it is there.  "
			              "⚠ Being there does not mean it is applied: the BYTES say that "
			              "(third witness), not this line",
			              r->nodo_rendering, c->conf.vendor_va, (int) profile,
			              wanted == VAEntrypointEncSliceLP ? "EncSliceLP (low power)"
			                                               : "EncSlice (full)",
			              modes, attr[2].value, mode.name, mode.va_bit);
		}
	}
	return 0;
}

/* ------------------------------------------------------------------------ */
/* ⛔⭐⭐ THE LEVEL CEILING OF `RCP.md` §4.3 (line 701), TRANSLATED INTO THE ALPHABET
 *      OF EACH CODEC — 23 Aug 2026, and it comes from a measurement.
 *
 *      `[M]` canvas 3840x2160, H.264: the client declares `video.level=5.1` and
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
 *    ⚠ AV1 has been out of the product since 20 Aug 2026 (`DECISIONS.md` §1.13-ter,
 *      no longer negotiated): the line stays because the codec still exists in the
 *      program, and a `0` here means "I impose nothing", not "zero".
 *
 * ⇒ Returns **0** when there is no ceiling to impose, and the caller does not
 *   ask anything of the component.  ⛔ And the returned value is NOT the proof that
 *   the component obeyed: that is read from the bytes of the SPS
 *   (`stream_level`), and it is the second half of R31. */
static int imposed_level(const Encoder *c)
{
	int x10 = c->request.livello_x10;

	if (x10 <= 0)
		return 0; /* §4.3 does not oblige the client to declare it: no ceiling */
	switch (c->request.codec) {
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
 *   `rc_mode`       → `VaDirectRequest.banda_*`: zeros = CQP, otherwise QVBR
 *                     — asked for BY NAME here too, and `open_device()` has
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
 *                     `open_device()`, with the `LA_DICHIARATA` rule;
 *   `idr_interval=0`→ by construction: every I is an IDR (`vadirect.c`);
 *   `profile`       → `.profile` (VAProfileH264High / HEVCMain / HEVCMain10);
 *   `level`         → `.level_idc` = `imposed_level()`, 0 = computed
 *                     as ffmpeg computed it.
 *
 * ⛔ THE TWO REFUSALS STAY IDENTICAL: lossless and CRF do not exist on the
 *    card, and they are not faked (`ModoQualita`).
 */
/* ⛔ THE TWO REFUSALS (and the third, on the QP) are the same for both card
 *    routes, and live in one place only. */
static bool allowed_quality_on_card(const Encoder *c, char *error, size_t error_byte)
{
	if (c->current_mode == CODIFICATORE_QUALITA_LOSSLESS) {
		/* ⛔ It is not faked, as it is not faked on SVT-AV1: the card has no
		 *    lossless mode, and `qp=0` is NOT one — on VA-API zero is the
		 *    value that means "not requested" (the option's default), which is
		 *    the same implicit sentinel already paid for on `crf=0`. */
		di(error, error_byte,
		   "in hardware there is no lossless mode, and it is not faked: "
		   "the card has constant QP, and `qp=0` means \"not requested\", not "
		   "\"lossless\".  ⛔ And since phase 18 it is not there in software either "
		   "(OpenH264 and SVT-AV1 do not have it): ask for a low QP");
		return false;
	}
	if (c->current_mode == CODIFICATORE_QUALITA_CRF) {
		/* ⛔ CRF and QP are not the same quantity: see `ModoQualita`. */
		di(error, error_byte,
		   "in hardware there is no CRF: the card has constant QP.  ⛔ "
		   "Translating CRF %d into QP %d and still calling it CRF would give two "
		   "measurements under the same label ⇒ ask for CODIFICATORE_QUALITA_QP",
		   c->current_quality, c->current_quality);
		return false;
	}
	if (c->current_quality < 1 || c->current_quality > 51) {
		di(error, error_byte,
		   "QP %d out of range: ask between 1 and 51 — ⛔ and ZERO is not \"the "
		   "best\", it is the default value that means \"not requested\"",
		   c->current_quality);
		return false;
	}
	return true;
}

/* The three numbers of the ceiling, with the check that is worth R31 — the same for both
 * routes: with working point == wire the driver (or the regulator) deduces CBR. */
static bool cap_in_three_numbers(int64_t *spot, int64_t *wire, int *reservoir, char *error,
                                size_t error_byte)
{
	*spot = point_cap();
	*wire = wire_cap();
	*reservoir = reservoir_cap_bit();
	/* ⛔⛔ THE CHECK THAT IS WORTH R31, and it sits BEFORE the opening: if these
	 *      two numbers were equal the driver would deduce **CBR** — and `[M]`
	 *      CBR on this hardware spends **83 times** what is needed on a still
	 *      scene.  It is not a theoretical possibility: it is what v1 did. */
	if (*spot >= *wire || *reservoir <= 0) {
		di(error, error_byte,
		   "⛔ the ceiling numbers are broken: working point %" PRId64 ", wire "
		   "%" PRId64 ", buffer %d bits.  The working point MUST stay below the wire "
		   "(with wire == working point the driver deduces CBR: that is R31) and the "
		   "buffer MUST be positive",
		   *spot, *wire, *reservoir);
		return false;
	}
	return true;
}

/* ⛔⛔ THE BUFFER, AND THE NUMBER IS JUDGED IN MILLISECONDS — the defect of
 *      v1 nobody had ever named: `rc_buffer_size = bit_rate/2`
 *      is **500 ms**, ten times the 50 ceiling of `CODER.md` §1-bis.
 *      The same for both routes. */
static bool reservoir_within_50_ms(Encoder *c, char *error, size_t error_byte)
{
	if (cap_floor_mbit && c->conf.bandwidth_reservoir_ms > 50) {
		di(c->conf.why_no, sizeof(c->conf.why_no),
		   "the regulator's buffer is %u ms (%d bits at %" PRId64 " bit/s): "
		   "CODER.md §1-bis gives 50 ms to ALL of our part, and a regulator cannot "
		   "take them all.  ⚠ In v1 they were 500, and nobody said so",
		   c->conf.bandwidth_reservoir_ms, c->conf.bandwidth_reservoir, c->conf.bandwidth_wire);
		c->conf.has_obeyed = false;
		di(error, error_byte, "⛔ E2: %s", c->conf.why_no);
		return false;
	}
	return true;
}

static int open_vaapi_card(Encoder *c, char *error, size_t error_byte)
{
	const CodificatoreRichiesta *r = &c->request;
	VaDirectRequest v;
	const VaDirectDeclaration *d;
	char error_va[256] = { 0 };

	if (!allowed_quality_on_card(c, error, error_byte))
		return -1;

	memset(&v, 0, sizeof v);
	v.codec = (r->codec == CODIFICATORE_H264) ? VADIRECT_H264 : VADIRECT_HEVC;
	v.depth = r->depth;
	v.width = r->width;
	v.height = r->height;
	v.fotogrammi_al_secondo = r->fotogrammi_al_secondo ? r->fotogrammi_al_secondo : 30;
	v.profile = c->profile_va;
	v.entrypoint = c->entrypoint_va;
	v.qp = c->current_quality;
	v.chiavi_ogni = r->chiavi_ogni;
	v.input_surfaces = READY_SURFACES;
	if (cap_floor_mbit
	    && !cap_in_three_numbers(&v.bandwidth_point, &v.bandwidth_wire, &v.reservoir_bit, error,
	                            error_byte))
		return -1;
	/* ⛔⭐⭐ AND THE §4.3 LEVEL, ASKED FOR BY NAME — 23 Aug 2026.  A
	 *      failure HERE is a real error and stops the opening: if the card
	 *      refuses the ceiling, opening it anyway would mean producing again
	 *      a stream that overshoots — that is the defect of that evening. */
	v.level_idc = imposed_level(c);
	if (v.level_idc > 0)
		registro_dice(LOG_ENCODING,
		              "⭐ §4.3: level IMPOSED on «%s» — %d.%d, that is %d in "
		              "%s.  ⚠ Requested does not mean obeyed: the verdict "
		              "comes from the SPS",
		              c->component_name, r->livello_x10 / 10, r->livello_x10 % 10,
		              v.level_idc,
		              r->codec == CODIFICATORE_H264 ? "level_idc"
		                                            : "general_level_idc (three times)");

	c->va = vadirect_open(&c->device, &v, error_va, sizeof error_va);
	if (!c->va) {
		di(error, error_byte, "«%s» did not open: %s", c->component_name, error_va);
		return -1;
	}
	d = vadirect_declaration(c->va);

	/* ───────────────────────────────────────────────────────────────────────
	 * ⛔ FIRST WITNESS: the confession from the context — which is now OURS, and
	 *    therefore says what we wrote ourselves.  ⚠ It is worth less than yesterday, and it is
	 *    right to say so: yesterday rereading `async_depth` from libavcodec was a
	 *    check on someone else; today the fields are so by construction.  The
	 *    witness that counts has remained the SECOND — the bytes (`bitstream_ok`)
	 *    — and the THIRD, the measured bandwidth.
	 */
	c->conf.codec = r->codec;
	c->conf.componente = c->component_name;
	c->conf.requested_depth = r->depth;
	c->conf.frames_b = 0;
	c->conf.global_header = false;
	c->conf.in_hardware = true;
	c->conf.has_obeyed = true;
	c->conf.why_no[0] = 0;
	c->conf.profondita_asincrona = 1;
	c->conf.low_power = c->low_power_choice;
	/* yesterday's numbers for the mode (1 = CQP, 5 = QVBR) stay, so the log
	 * lines and the benches that read them do not change */
	c->conf.bitrate_mode = (d->va_mode == VA_RC_QVBR) ? 5 : 1;
	c->conf.bandwidth_point = v.bandwidth_point;
	c->conf.bandwidth_wire = v.bandwidth_wire;
	c->conf.bandwidth_reservoir = v.reservoir_bit;
	c->conf.bandwidth_reservoir_ms =
	    (v.bandwidth_wire > 0 && v.reservoir_bit > 0)
	        ? (uint32_t) ((int64_t) v.reservoir_bit * 1000 / v.bandwidth_wire)
	        : 0;
	if (!reservoir_within_50_ms(c, error, error_byte)) {
		vadirect_close(c->va);
		c->va = NULL;
		return -1;
	}
	c->next_key = true; /* ⛔ after every opening the first is a key */
	return 0;
}

/*
 * ⭐⭐ PHASE 19 — THE CARD OPENS IN VULKAN VIDEO.  The same numbers as
 *     `open_vaapi_card()`, told to `vulkanvideo.c`:
 *
 *   the ceiling   → `banda_*`/`reservoir_bit`: zeros = CQP, otherwise VBR with
 *                   the requested QP as the regulator's FLOOR (Vulkan does not
 *                   have VA-API's QVBR: `vulkanvideo.h`);
 *   the level     → `level_idc` = `imposed_level()`, 0 = computed as
 *                   ffmpeg computed it;
 *   the keys      → `chiavi_ogni` (0 = on request), and every I is an IDR;
 *   the entrypoint → does not exist in Vulkan: nothing to declare.
 *
 * ⛔ The headers (SPS/PPS/VPS) are written by THE DRIVER from our `StdVideo*`
 *    (`vkGetEncodedVideoSessionParametersKHR`); what came out of it is
 *    reread from the bytes in `bitstream_ok()`, exactly as for VA-API.
 */
static int open_vulkan_card(Encoder *c, char *error, size_t error_byte)
{
	const CodificatoreRichiesta *r = &c->request;
	VulkanVideoRequest v;
	const VulkanVideoDeclaration *d;
	char error_vk[256] = { 0 };

	if (!allowed_quality_on_card(c, error, error_byte))
		return -1;

	memset(&v, 0, sizeof v);
	v.codec = (r->codec == CODIFICATORE_H264) ? VULKANVIDEO_H264 : VULKANVIDEO_HEVC;
	v.depth = r->depth;
	v.width = r->width;
	v.height = r->height;
	v.fotogrammi_al_secondo = r->fotogrammi_al_secondo ? r->fotogrammi_al_secondo : 30;
	v.qp = c->current_quality;
	v.chiavi_ogni = r->chiavi_ogni;
	if (cap_floor_mbit
	    && !cap_in_three_numbers(&v.bandwidth_point, &v.bandwidth_wire, &v.reservoir_bit, error,
	                            error_byte))
		return -1;
	v.level_idc = imposed_level(c);
	if (v.level_idc > 0)
		registro_dice(LOG_ENCODING,
		              "⭐ §4.3: level IMPOSED on «%s» — %d.%d, that is %d in "
		              "%s.  ⚠ Requested does not mean obeyed: the verdict "
		              "comes from the SPS",
		              c->component_name, r->livello_x10 / 10, r->livello_x10 % 10,
		              v.level_idc,
		              r->codec == CODIFICATORE_H264 ? "level_idc"
		                                            : "general_level_idc (three times)");

	c->vk = vulkanvideo_open(c->vk_device, &v, error_vk, sizeof error_vk);
	if (!c->vk) {
		di(error, error_byte, "«%s» did not open: %s", c->component_name, error_vk);
		return -1;
	}
	d = vulkanvideo_declaration(c->vk);

	c->conf.codec = r->codec;
	c->conf.componente = c->component_name;
	c->conf.requested_depth = r->depth;
	c->conf.frames_b = 0;
	c->conf.global_header = false;
	c->conf.in_hardware = true;
	c->conf.has_obeyed = true;
	c->conf.why_no[0] = 0;
	c->conf.profondita_asincrona = 1;
	c->conf.low_power = false;
	/* in yesterday's alphabet: 1 = CQP, 3 = VBR (5 is VA-API's QVBR) */
	c->conf.bitrate_mode = (d->rate_control == VULKANVIDEO_RC_VBR) ? 3 : 1;
	c->conf.bandwidth_point = v.bandwidth_point;
	c->conf.bandwidth_wire = v.bandwidth_wire;
	c->conf.bandwidth_reservoir = v.reservoir_bit;
	c->conf.bandwidth_reservoir_ms =
	    (v.bandwidth_wire > 0 && v.reservoir_bit > 0)
	        ? (uint32_t) ((int64_t) v.reservoir_bit * 1000 / v.bandwidth_wire)
	        : 0;
	if (!reservoir_within_50_ms(c, error, error_byte)) {
		vulkanvideo_close(c->vk);
		c->vk = NULL;
		return -1;
	}
	/* ⭐ THE DRIVER'S DECLARATION, written once per opening: it is the
	 *    first witness, and as for VA-API it is worth less than the bytes. */
	registro_dice(LOG_ENCODING,
	              "⭐ Vulkan Video «%s»: encodes %ux%u (block %u) for the canvas %ux%u · "
	              "level %d in the SPS · %s · headers %s%s%s · conversion %s · "
	              "minimum latency %s · input %s · QP %d..%d · %zu bytes of "
	              "headers in front of every key",
	              c->component_name, d->encoded_width, d->encoded_height, d->block,
	              r->width, r->height, d->level_idc,
	              d->rate_control == VULKANVIDEO_RC_VBR ? "VBR (requested QP = floor)" : "CQP",
	              d->headers_from_driver ? "from the driver" : "written by us",
	              d->driver_has_changed_parameters ? " (⚠ the driver CHANGED the parameters)"
	                                              : "",
	              d->level_fixed_in_bytes ? " (⚠ HEVC level corrected in the bytes)" : "",
	              d->direct_conversion ? "direct into the planes" : "in two images and copy",
	              d->low_latency_requested ? "requested" : "not accepted by the driver",
	              d->input_format, d->qp_min, d->qp_max, d->headers_byte);
	c->next_key = true; /* ⛔ after every opening the first is a key */
	return 0;
}

/*
 * ⭐ The card's context is closed and opened here, and `lower_quality()`,
 *    `raise_quality()`, `codificatore_ridimensiona()` call these two.
 *    ⚠ vadiretta's context also carries the input store and the
 *    reconstructed surfaces; vulkanvideo's carries the session, the images and the
 *    DMA-BUF cache.  ⛔ Phase 19: the software fallback branch
 *    (`sw_apri`/`sw_chiudi`, `ripiego.c`) has left — `c->hardware` is true
 *    in every encoder that was born, and the guard stays for the half-born one.
 */
static void close_context(Encoder *c)
{
	if (c->route == ROUTE_VULKAN) {
		vulkanvideo_close(c->vk);
		c->vk = NULL;
	} else if (c->hardware) {
		vadirect_close(c->va);
		c->va = NULL;
		c->surface_ready = VA_INVALID_ID;
	}
	c->decided_border = false;
	c->active_border = false;
}

static int open_context(Encoder *c, char *error, size_t error_byte)
{
	if (!c->hardware) {
		di(error, error_byte, "no card open: without a card there is no encoding (phase 19)");
		return -1;
	}
	return c->route == ROUTE_VULKAN ? open_vulkan_card(c, error, error_byte)
	                                  : open_vaapi_card(c, error, error_byte);
}

/*
 * ⭐ THE FRAMES AND THE CONVERSION — in one place only, because `codificatore_
 *    fresh()` and `codificatore_ridimensiona()` did the same thing in two
 *    drafts, and ⛔ the second had already forgotten the declared promotion.
 *    Two drafts of the same thing are a place to diverge silently.
 *
 * ⭐ The input surfaces are kept by vadiretta, and here only the STAGING buffer
 *    of the from-memory route is allocated — NV12 (8 bit) or P010 (10 bit) at the size
 *    of the canvas, which `colors709.c` fills and `vadiretta_carica_*()` uploads.
 *    ⚠ It is redone on every reopening because the size may have changed.
 */
static int open_frames(Encoder *c, char *error, size_t error_byte)
{
	const CodificatoreRichiesta *r = &c->request;

	free(c->staging);
	c->staging = NULL;
	c->staging_byte = 0;
	/* ⭐ Phase 19: on the Vulkan route the BGRx are uploaded as they are and
	 *    the shader converts them: no staging buffer. */
	if (c->hardware && c->route == ROUTE_VAAPI && FORMATO_PIXEL_IMPACCHETTATO(r->fmt)) {
		size_t sample = r->depth == 10 ? 2u : 1u;
		/* Y in full, then interleaved UV at half height: 1.5 samples per pixel. */
		c->staging_byte = (size_t) r->width * r->height * sample * 3u / 2u;
		c->staging = malloc(c->staging_byte);
		if (!c->staging) {
			c->staging_byte = 0;
			di(error, error_byte, "no memory for the %ux%u staging buffer", r->width,
			   r->height);
			return -1;
		}
	}
	/* ⚠ The source has real 8 bits (`[M]` F2.2): the Main10 that comes out is 8 bits
	 *   PROMOTED, and the promotion is declared instead of suffered.  It holds for both
	 *   routes: in hardware the promotion is done by `colors709_to_p010()`. */
	c->conf.promotion_8_to_10 =
	    (FORMATO_PIXEL_IMPACCHETTATO(r->fmt) && r->depth == 10);
	return 0;
}

Encoder *codificatore_nuovo(const CodificatoreRichiesta *request,
                                 char *error, size_t error_byte)
{
	if (!request || request->width == 0 || request->height == 0) {
		di(error, error_byte, "zero size");
		return NULL;
	}
	if (request->depth != 8 && request->depth != 10) {
		di(error, error_byte, "depth %d: ask for 8 or 10", request->depth);
		return NULL;
	}
	/*
	 * ⛔ A 10-bit input inside an 8-bit encoder is not a conversion:
	 *    it is an out-of-bounds read.  ⚠ And the symptom would be **memory
	 *    overrun**, not an ugly picture — that is a defect that names
	 *    neither the colour nor the depth.  Whoever wants 8 bits goes through BGRx, which
	 *    has a declared conversion.
	 */
	if (request->fmt == CODIFICATORE_PIXEL_YUV420P10LE && request->depth != 10) {
		di(error, error_byte,
		   "the input is yuv420p10le and %d bits are requested: they do not mix — "
		   "for 8 bits enter through BGRx", request->depth);
		return NULL;
	}
	/* ⚠ 4:2:0 wants even sizes: an odd width would give a chroma of
	 *   half a sample, and the encoder would round it **silently**. */
	if ((request->width & 1) || (request->height & 1)) {
		di(error, error_byte, "%ux%u: 4:2:0 wants even sizes",
		   request->width, request->height);
		return NULL;
	}

	Encoder *c = calloc(1, sizeof(*c));
	if (!c) {
		di(error, error_byte, "out of memory");
		return NULL;
	}
	c->request = *request;
	c->current_mode = request->mode;
	c->current_quality = request->quality;
	/* ⭐ Phase 9: the wait starts from its resting value and from there on only
	 *    doubles (`lower_quality()`), never the opposite. */
	c->rise_wait = RISE_WAIT;

	/* ⛔ PHASE 19: without a name there is nothing to open — the software
	 *    fallback (OpenH264, SVT-AV1) has left (`DECISIONS.md` §10.27), and
	 *    below it is refused saying so. */
	const char *name = request->componente ? request->componente
	                                         : "(no encoder requested)";
	/*
	 * ⛔ REQUESTED BY NAME, NO FALLBACK — the v1 line
	 * (`encoder.c:550-566`) that this file inherits in full:
	 *   "Whoever names an encoder is measuring: falling back to another would give
	 *    two different measurements with the same label, which is worse than not
	 *    measuring."
	 */
	snprintf(c->component_name, sizeof c->component_name, "%s", name);
	c->surface_ready = VA_INVALID_ID;
	c->device.fd = -1;

	/*
	 * ⛔ "Is it in hardware?" is decided BEFORE opening: on that answer
	 *    depend the device, the store and the conversion — that is three
	 *    things that cannot be changed afterwards.  ⭐ Phase 18: the NAME says it
	 *    (`h264_vaapi`/`hevc_vaapi` are the card's two labels), and the
	 *    label's codec must be the one requested.
	 */
	{
		CodecVideo card_codec;
		c->hardware = component_of_card(name, &card_codec, &c->requested_route);
		if (c->hardware && card_codec != request->codec) {
			di(error, error_byte, "«%s» is not a %s encoder", name,
			   codec_name(request->codec));
			free(c);
			return NULL;
		}
	}
	if (!c->hardware) {
		/* ⛔ PHASE 19 — NO PROCESSOR WITHOUT A CARD (`DECISIONS.md` §10.27,
		 *    the user's words: *"no CPU without a card"*).  The encoders
		 *    are the card's; any other name is refused, with the reason. */
		di(error, error_byte,
		   "the encoder «%s» does not exist: REMOTIX encodes ONLY on the card "
		   "(«h264_card»/«hevc_card» by capability, «*_vulkan» or «*_vaapi» by "
		   "name) — ⛔ the software fallback left with phase 19, and no other one "
		   "is taken",
		   name);
		free(c);
		return NULL;
	}
	if (open_device(c, error, error_byte) < 0) {
		codificatore_libera(c);
		return NULL;
	}

	if (open_context(c, error, error_byte) < 0) {
		codificatore_libera(c);
		return NULL;
	}
	if (open_frames(c, error, error_byte) < 0) {
		codificatore_libera(c);
		return NULL;
	}

	/*
	 * ⛔ The name carries the node and the power INSIDE it, not beside it: it is the line that
	 *    ends up in the log next to every number, and a 3 ms rate without
	 *    "which card" and "which entrypoint" next to it is a number that holds for
	 *    a machine nobody knows (`LESSONS.md` §1.1).
	 */
	if (c->route == ROUTE_VULKAN)
		snprintf(c->name, sizeof(c->name),
		         "%s %s via %.40s (in HARDWARE · %.60s · Vulkan Video: %.160s)",
		         codec_name(request->codec),
		         request->depth == 10 ? "10 bit" : "8 bit",
		         c->component_name, c->conf.node, c->conf.vendor_va);
	else
		snprintf(c->name, sizeof(c->name),
		         "%s %s via %.40s (in HARDWARE · %.60s · VA-API: %.120s · %s)",
		         codec_name(request->codec),
		         request->depth == 10 ? "10 bit" : "8 bit",
		         c->component_name, c->conf.node, c->conf.vendor_va,
		         c->conf.low_power ? "⚠ EncSliceLP, low power — it is NOT "
		                                 "full encoding"
		                               : "EncSlice, full");

	/* ⭐ THE WORKING POINT WITH ITS NUMBER, not with its name.  ⛔ Until 23
	 *    Aug 2026 this line said *"constant QP"* and kept quiet about the **26**: whoever
	 *    reread a bench could not know which rung it had started from, and
	 *    `QP_HARDWARE` (`child.c:4052`) could be tried only by recompiling. */
	char spot[48];
	if (request->mode == CODIFICATORE_QUALITA_LOSSLESS)
		snprintf(spot, sizeof(spot), "lossless");
	else
		snprintf(spot, sizeof(spot), "%s %d%s", mode_name(request->mode),
		         request->quality,
		         request->mode == CODIFICATORE_QUALITA_QP ? " constant" : "");

	registro_dice(LOG_ENCODING, "opened: %s · %ux%u · %s · keys %s%s", c->name,
	              request->width, request->height, spot,
	              request->chiavi_ogni ? "periodic" : "on request only",
	              c->conf.promotion_8_to_10
	                  ? " · ⚠ capture's 8 bits PROMOTED to 10: the desired value of "
	                    "SPECS.md §3.1 does not come from this source"
	                  : "");

	/*
	 * ⭐⭐ THE DEGRADATION LADDER, WRITTEN WITH THE VALUES IN FORCE.
	 *
	 * ⛔ Until now `CRF_STEP`, `EMERGENCY_CRF` and `MAX_REENCODES` did not
	 *    appear **in any log line**: the ladder was known only by
	 *    reading the source, and tuning it meant recompiling **and** remembering
	 *    with which value it had been measured the time before.  ⚠ A number that
	 *    decides what is seen and appears nowhere is a number that
	 *    sooner or later gets measured wrong.
	 *
	 * ⚠ And `lower_quality()` is SIMULATED instead of writing the ladder by hand: two
	 *   drafts of the same rule are a place to diverge silently, and
	 *   here they would diverge precisely on the day someone tunes the step.
	 */
	char scale_factor[256];
	size_t used_len = 0;
	ModoQualita m = request->mode;
	int q = request->quality;
	/* ⛔ WHERE A DELTA STOPS, inside the same string — 23 Aug 2026.  The
	 *    line said *"a DELTA is abandoned after N re-encodings"* and then
	 *    drew the WHOLE ladder: whoever read it counted the rungs and believed
	 *    it walked all of them.  ⚠ And until today it did not walk N: it walked
	 *    **all of them**, because the count was dead code (the box in
	 *    `compress_common()`).  ⇒ Now a delta makes `MAX_REENCODES`
	 *    encodings, and the mark in the ladder says exactly on which rung
	 *    it stops.  ⭐ A line that declares a ladder the code does not walk
	 *    is worse than no line. */
	bool delta_stops = false;
	scale_factor[0] = 0;
	for (unsigned i = 0; i <= MAX_REENCODES; i++) {
		if (i) {
			if (m == CODIFICATORE_QUALITA_LOSSLESS) {
				m = CODIFICATORE_QUALITA_CRF;
				q = EMERGENCY_CRF;
			} else if (q >= 51) {
				break; /* the bottom: there is nothing below */
			} else {
				q += CRF_STEP;
				if (q > 51)
					q = 51;
			}
		}
		if (used_len + 72 >= sizeof(scale_factor))
			break;
		if (i) {
			/* ⚠ `i == MAX_REENCODES` is the first rung a delta does NOT
			 *   try: only a key gets there. */
			bool key_only = (i == MAX_REENCODES);
			int sep = snprintf(scale_factor + used_len, sizeof(scale_factor) - used_len, "%s",
			                   key_only ? " ⟨a DELTA stops here⟩ → " : " → ");
			if (sep < 0)
				break;
			used_len += (size_t) sep;
			if (key_only)
				delta_stops = true;
		}
		int n = (m == CODIFICATORE_QUALITA_LOSSLESS)
		            ? snprintf(scale_factor + used_len, sizeof(scale_factor) - used_len, "%s", mode_name(m))
		            : snprintf(scale_factor + used_len, sizeof(scale_factor) - used_len, "%s %d", mode_name(m), q);
		if (n < 0)
			break;
		used_len += (size_t) n;
	}
	registro_dice(LOG_ENCODING,
	              "the degradation ladder, with the values in force: %s — step %d "
	              "(CRF_STEP), bottom 51, exit from lossless at CRF %d "
	              "(EMERGENCY_CRF).  ⛔ A DELTA makes %d encodings in all "
	              "(MAX_REENCODES), that is %d descents, and each one is TRIED: %s.  "
	              "⚠ A KEY is never abandoned (RCP.md §5.2): for a key the ladder is "
	              "walked all the way down.  ⭐ And every RETRY comes out as a KEY even if the "
	              "frame was a delta: the descent reopens the context and throws away the "
	              "references",
	              scale_factor, CRF_STEP, EMERGENCY_CRF, MAX_REENCODES,
	              MAX_REENCODES - 1,
	              delta_stops
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
	 *     exists in `key_interval_ms()` (`webtransport.c`).
	 */
	registro_dice(LOG_ENCODING,
	              rise_enabled
	                  ? "⭐ PHASE 9: the quality CLIMB is ON — after %u "
	                    "frames in a row below %u bytes we go back up by ONE rung of "
	                    "%d, and **never** beyond the requested working point (%s).  ⚠ Every "
	                    "step, down and up, ends up in the log (I1), and on every "
	                    "relapse the wait DOUBLES up to %u frames"
	                  : "the quality climb is OFF (invariant I6): once it has gone "
	                    "down, the quality stays down for the whole session — and "
	                    "this line is the why, not \"it never had to trigger\".  "
	                    "⚠ It is turned on with `encoder_quality_rises(true)`, and while "
	                    "off these numbers (%u frames, %u bytes, rung %d, "
	                    "working point %s, wait ceiling %u) have no effect",
	              RISE_WAIT, RISE_MARGIN, CRF_STEP, spot, RISE_WAIT_MAX);

	/*
	 * ⛔⭐ AND THE BANDWIDTH CEILING TOO IS WRITTEN IN BOTH CASES, for the
	 *     same reason as the climb: a ceiling that is off and a ceiling that never
	 *     had the chance to bite would give the **same** log, and whoever
	 *     rereads a bench would not know which of the two it measured.
	 *
	 */
	if (cap_floor_mbit)
		registro_dice(LOG_ENCODING,
		              "⭐ PHASE 9: the BANDWIDTH CEILING is ON over a floor of %u "
		              "Mbit/s — mode %s (asked for by name, never `auto`), working point "
		              "%" PRId64 " kbit/s, wire %" PRId64 " kbit/s (⛔ NEVER equal: that is "
		              "R31), buffer %d bits = **%u ms** (CODER.md §1-bis grants 50 "
		              "to ALL of our part; v1 took 500 and nobody "
		              "said so).  ⚠ QP %d stays and under QVBR it is the quality "
		              "factor.  ⭐ Whether it obeyed is said by the BYTES, the «video "
		              "bandwidth» line every %u s",
		              cap_floor_mbit, wanted_bitrate_mode().name,
		              point_cap() / 1000, wire_cap() / 1000, reservoir_cap_bit(),
		              (unsigned) ((uint64_t) reservoir_cap_bit() * 1000 / wire_cap()),
		              c->current_quality, BANDWIDTH_WINDOW_US / 1000000u);
	else
		registro_dice(LOG_ENCODING,
		              "the bandwidth ceiling is OFF (invariant I6): mode %s, QP %d "
		              "fixed, and ⛔ **nobody says no to the bandwidth** — `[M]` 23 Aug "
		              "2026 a film with grain at full screen asks for 58.7 Mbit/s, "
		              "that is 293 %% of the floor of 20.  ⚠ And this line is the "
		              "why, not \"it never had to bite\".  It is turned on with "
		              "`codificatore_tetto_banda(20)`, and while off its numbers (wire "
		              "at %u %% of the floor, working point at %u %% of the wire, buffer %u "
		              "ms) have no effect",
		              wanted_bitrate_mode().name, c->current_quality,
		              WIRE_CAP_QUOTA, POINT_CAP_QUOTA, VBV_CAP_MS);
	return c;
}

void codificatore_libera(Encoder *c)
{
	if (!c)
		return;
	c->packet_in_hand = false;
	free(c->staging);
	c->staging = NULL;
	/* ⛔ Before the device, and in this order: the imported surfaces, the
	 *    conversion context and the encoder live ON the device,
	 *    and freeing them afterwards would mean asking a display that is no longer
	 *    there. */
	drop_imported(c, "the encoder is closing");
	close_vpp(c);
	close_context(c);
	/* ⚠ The device is closed LAST — the one of the open route. */
	if (c->route == ROUTE_VULKAN)
		vulkanvideo_close_device(c->vk_device);
	else if (c->hardware)
		vadirect_close_device(&c->device);
	free(c->output);
	free(c);
}

const char *encoder_name(const Encoder *c)
{
	return c ? c->name : "(none)";
}

bool encoder_vulkan_on_node(const char *node)
{
	VulkanVideoCapabilities cap;
	char error[256] = { 0 };

	memset(&cap, 0, sizeof cap);
	if (!node || !vulkanvideo_capabilities(node, &cap, error, sizeof error))
		return false;
	return cap.h264.encode || cap.hevc.encode;
}

const char *encoder_route(const Encoder *c)
{
	return c ? route_name(c->route) : "";
}

const EncoderConfession *codificatore_confessione(const Encoder *c)
{
	return c ? &c->conf : NULL;
}

void codificatore_chiedi_chiave(Encoder *c)
{
	if (c)
		c->next_key = true;
}

bool codificatore_ridimensiona(Encoder *c, uint32_t width, uint32_t height,
                               char *error, size_t error_byte)
{
	if (!c)
		return false;
	if (width == c->request.width && height == c->request.height)
		return true;
	if ((width & 1) || (height & 1)) {
		di(error, error_byte, "%ux%u: 4:2:0 wants even sizes", width, height);
		return false;
	}

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⛔⛔ NOT WITH A PACKET IN HAND — it is the ONLY place in the file where
	 *      `close_context()` could get there without a guard.
	 *
	 * `close_context()` frees the encoder, and the bytes it holds.  And
	 * `compress_common()` delivers `report->data`, a pointer into `c->output`,
	 * valid until `codificatore_rilascia()`
	 * (`encoder.h:439`).  ⇒ A caller that resized while still holding
	 * the frame would read freed memory, and it is **the same form** as the
	 * defect that on 23 Aug 2026 killed the server in the transport: below a
	 * certain size freed memory stays readable, and the fault shows up
	 * elsewhere, much later.
	 *
	 * ⭐ Today it is not reachable — `child.c:7426` resizes in the main
	 *   loop, and `encode_and_send()` releases at `child.c:4905` before
	 *   returning — but "it is not reachable" was true for the other two as well, and
	 *   here it cost nothing to make it **impossible** instead of lucky.
	 *
	 * ⚠ It REFUSES instead of unhooking on the sly: that would leave the caller's pointer
	 *   dangling anyway, and silently on top of that.  By refusing,
	 *   the frame stays alive and valid and the caller receives an error that
	 *   names it.
	 * ═══════════════════════════════════════════════════════════════════════ */
	if (c->packet_in_hand) {
		di(error, error_byte,
		   "⛔ resize to %ux%u with the previous frame STILL IN HAND: "
		   "reopening now would free the bytes the caller is reading.  "
		   "⇒ `codificatore_rilascia()` BEFORE resizing",
		   width, height);
		registro_dice(LOG_ENCODING, "%s", error);
		return false;
	}

	/* ⛔ It really reopens.  An encoder opened at one size and fed at
	 *    another does not protest: it crops or pads, and the defect shows only
	 *    in the picture.
	 * ⚠ In hardware the STORE is reopened too — the surfaces have the size
	 *   inside, and reusing them would mean uploading 1920 rows into 1280. */
	close_context(c);
	c->request.width = width;
	c->request.height = height;
	c->first_encode_done = false;
	c->conf.read_from_stream = false;
	/* ⛔ AND THE COUNT OF CALM STARTS AGAIN FROM ZERO: 120 comfortable frames at
	 *    1280x720 are no proof at all that there is room at 7680x4320.  ⚠ Without
	 *    this line the first frame at the new canvas would trigger an
	 *    **unmeasured** climb, which is precisely what I1 forbids.
	 *    ⭐ `failed_quality` instead is KEPT: forgetting it would widen the
	 *      meshes, and the direction in which to err is caution. */
	c->below_margin = 0;
	/* ⛔ And the window of the third witness restarts too: 10 s of bytes at
	 *    1280x720 and 10 s at 7680x4320 under the same line would be two measurements
	 *    with the same label. */
	c->bandwidth_t0_us = 0;
	c->bandwidth_byte = 0;
	c->bandwidth_frames = 0;
	c->bandwidth_max = 0;

	if (open_context(c, error, error_byte) < 0)
		return false;
	if (open_frames(c, error, error_byte) < 0)
		return false;

	/* ⛔ `RCP.md` §5.2: the first frame at the new size MUST be a
	 *    key, and a REAL key.  `open_context` has already demanded it; the line
	 *    stays because the rule is written here, not elsewhere. */
	c->next_key = true;
	registro_dice(LOG_ENCODING,
	              "new canvas %ux%u: reopened, and the next frame is a key "
	              "(RCP.md §5.2)", width, height);
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
 *   "before" impossible.  ⛔ `upload_us` instead goes to **0**, and there zero
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
 *        the defect of `LESSONS.md` §8 — two screens alternating, and
 *        no error.
 * ═══════════════════════════════════════════════════════════════════════════ */

static VADisplay display_di(Encoder *c)
{
	/* ⛔ Only on the VA-API route: Vulkan's zero copy lives inside
	 *    `vulkanvideo.c` (import, cache, conversion) and does not pass through here. */
	return (c->hardware && c->route == ROUTE_VAAPI) ? c->device.display : NULL;
}

/*
 * ⭐⭐ PHASE 19 — THE ROUND OF ONE FRAME ON VULKAN VIDEO, in a single shot:
 *     `vulkanvideo.c` converts (shader) and encodes within the same call,
 *     and returns the three times separately as `EncoderFrame` keeps them.
 *     ⚠ On the zero copy `upload_us` is 0 and means "not there"; from
 *     memory it is the upload of the BGRx to the card (the shader is in
 *     `us_conversione`).  The bytes go into `c->output` as for VA-API, and from
 *     there on the common body no longer knows which route produced them.
 */
static bool encode_vulkan(Encoder *c, const uint8_t *pixel, uint32_t step,
                            const EncoderSurface *s, EncoderFrame *report)
{
	const uint8_t *data = NULL;
	size_t byte = 0;
	VulkanVideoTimings t;
	char error[256] = { 0 };
	bool ok;

	memset(&t, 0, sizeof t);
	if (s) {
		VulkanVideoSurface vs = { .fd = s->fd, .offset = s->offset, .stride = s->stride,
			                         .width = s->width, .height = s->height,
			                         .formato_drm = s->formato_drm, .modifier = s->modifier,
			                         .generation = s->generation };
		ok = vulkanvideo_encode_dmabuf(c->vk, &vs, c->next_key, &data, &byte, &t, error,
		                                 sizeof error);
		if (ok && !c->logged_zero_copy) {
			c->logged_zero_copy = true;
			registro_dice(LOG_ENCODING,
			              "⭐⭐ ZERO COPY in force (Vulkan): the compositor's DMA-BUF (fd %d, "
			              "%ux%u, stride %u, modifier 0x%llx) is imported as a Vulkan "
			              "image and converted to %s BY THE SHADER on the card — no "
			              "`memcpy`, no CPU conversion, no upload.  ⚠ The "
			              "conversion remains and costs %llu us (with the fence wait inside)",
			              s->fd, s->width, s->height, s->stride,
			              (unsigned long long) s->modifier,
			              c->request.depth == 10 ? "P010" : "NV12",
			              (unsigned long long) t.us_conversione);
		}
	} else {
		if (!FORMATO_PIXEL_IMPACCHETTATO(c->request.fmt)) {
			registro_dice(LOG_ENCODING,
			              "⛔ the Vulkan route takes only BGRx/RGBx from memory, and "
			              "the input is not: `vulkan_fit()` should have stopped it earlier");
			return false;
		}
		ok = vulkanvideo_encode_memory(c->vk, pixel, step ? step : c->request.width * 4u,
		                                  c->request.fmt == CODIFICATORE_PIXEL_RGBX
		                                      ? VULKANVIDEO_RGBX
		                                      : VULKANVIDEO_BGRX,
		                                  c->next_key, &data, &byte, &t, error,
		                                  sizeof error);
	}
	if (!ok) {
		registro_dice(LOG_ENCODING, "⛔ Vulkan Video did not encode: %s", error);
		return false;
	}
	if (!put_in_output(c, data, byte))
		return false;
	report->us_conversione = t.us_conversione;
	report->upload_us = t.upload_us;
	report->us_codifica = t.us_codifica;
	report->trattenuto = false;
	c->packet_in_hand = true;
	return true;
}

/* Throws away all the imported surfaces.  ⛔ It is called when the generation of the
 * producer's buffers changes, and at closing: a surface that outlives
 * the `pw_buffer` it described points to someone else's memory. */
static void drop_imported(Encoder *c, const char *why)
{
	VADisplay dpy = display_di(c);

	if (!c->how_many_imported)
		return;
	if (dpy)
		for (unsigned i = 0; i < c->how_many_imported; i++)
			vaDestroySurfaces(dpy, &c->imported[i].surface, 1);
	registro_dice(LOG_ENCODING,
	              "⭐ throwing away the %u imported surfaces: %s.  ⛔ Keeping them would mean giving "
	              "VA-API a descriptor that no longer describes anything — and the symptom "
	              "would be an OLD picture, with no error at all",
	              c->how_many_imported, why);
	c->how_many_imported = 0;
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
static VASurfaceID import_dmabuf(Encoder *c, const EncoderSurface *s)
{
	VADisplay dpy = display_di(c);
	VADRMPRIMESurfaceDescriptor d;
	VASurfaceAttrib attributes[2];
	VASurfaceID surface = VA_INVALID_ID;
	VAStatus state;
	unsigned i;

	if (!dpy)
		return VA_INVALID_ID;

	/* ⛔ The generation BEFORE everything: if the producer has redone its buffers,
	 *    what is in the cache no longer describes anything. */
	if (c->cache_created && c->cache_generation != s->generation)
		drop_imported(c, "the producer has redone its buffers");
	c->cache_generation = s->generation;
	c->cache_created = true;

	for (i = 0; i < c->how_many_imported; i++)
		if (c->imported[i].fd == s->fd && c->imported[i].l == s->width
		    && c->imported[i].a == s->height && c->imported[i].stride == s->stride
		    && c->imported[i].offset == s->offset
		    && c->imported[i].formato_drm == s->formato_drm
		    && c->imported[i].modifier == s->modifier)
			return c->imported[i].surface;

	uint32_t object_size = 0;

	memset(&d, 0, sizeof d);
	/*
	 * ⛔ THE VA-API FOURCC IS NOT THE DRM ONE, and the two look alike
	 *    enough to be mistaken for each other.  ⚠ `VA_FOURCC_BGRX` is what ffmpeg
	 *    pairs with `AV_PIX_FMT_BGR0` and with `DRM_FORMAT_XRGB8888`
	 *    (`hwcontext_vaapi.c`), that is B,G,R,ignored **in the order of the bytes in
	 *    memory** — the same that `capture.c` negotiates as `BGRx`.  ⛔ Getting it wrong
	 *    gives no error: it gives red and blue swapped.
	 * ⚠ Here the two this module knows how to receive are declared; for the others we
	 *   refuse instead of guessing.
	 */
	if (s->formato_drm == DRM_FORMAT_XRGB8888)
		d.fourcc = VA_FOURCC_BGRX;
	else if (s->formato_drm == DRM_FORMAT_ARGB8888)
		d.fourcc = VA_FOURCC_BGRA;
	else {
		registro_dice(LOG_ENCODING,
		              "⛔ DRM format 0x%08x cannot be imported: this route knows BGRx and "
		              "BGRA.  ⚠ A fourcc is NOT guessed — a wrong fourcc gives no "
		              "error, it gives swapped colours",
		              s->formato_drm);
		return VA_INVALID_ID;
	}
	d.width = s->width;
	d.height = s->height;
	d.num_objects = 1;
	d.objects[0].fd = s->fd;
	/* ⭐ E-R6 (audit of 25 Oct 2026): the product is made in 64 bits; a size that does not fit the 32-bit field of the import is refused,
	 *    not wrapped to a smaller one. */
	if (!dim_object_size(s->offset, s->stride, s->height, &object_size)) {
		registro_dice(LOG_ENCODING,
		              "⛔ the DMA-BUF object (offset %u + stride %u x %u rows) does not fit in 32 bits: not imported",
		              s->offset, s->stride, s->height);
		return VA_INVALID_ID;
	}
	d.objects[0].size = object_size;
	d.objects[0].drm_format_modifier = s->modifier;
	d.num_layers = 1;
	d.layers[0].drm_format = s->formato_drm;
	d.layers[0].num_planes = 1;
	d.layers[0].object_index[0] = 0;
	d.layers[0].offset[0] = s->offset;
	d.layers[0].pitch[0] = s->stride;

	attributes[0].type = VASurfaceAttribMemoryType;
	attributes[0].flags = VA_SURFACE_ATTRIB_SETTABLE;
	attributes[0].value.type = VAGenericValueTypeInteger;
	attributes[0].value.value.i = VA_SURFACE_ATTRIB_MEM_TYPE_DRM_PRIME_2;
	attributes[1].type = VASurfaceAttribExternalBufferDescriptor;
	attributes[1].flags = VA_SURFACE_ATTRIB_SETTABLE;
	attributes[1].value.type = VAGenericValueTypePointer;
	attributes[1].value.value.p = &d;

	state = vaCreateSurfaces(dpy, VA_RT_FORMAT_RGB32, s->width, s->height, &surface, 1,
	                         attributes, 2);
	if (state != VA_STATUS_SUCCESS) {
		registro_dice(LOG_ENCODING,
		              "⛔ the DMA-BUF was not imported (vaCreateSurfaces: %s) — fd %d, "
		              "%ux%u, stride %u, offset %u, modifier 0x%llx.  ⚠ There is NO silent "
		              "fallback to the copy: the caller writes it",
		              vaErrorStr(state), s->fd, s->width, s->height, s->stride,
		              s->offset, (unsigned long long) s->modifier);
		return VA_INVALID_ID;
	}

	if (c->how_many_imported >= IMPORTED_MAX)
		drop_imported(c, "the cache is full and starts over");
	i = c->how_many_imported++;
	c->imported[i].fd = s->fd;
	c->imported[i].l = s->width;
	c->imported[i].a = s->height;
	c->imported[i].stride = s->stride;
	c->imported[i].offset = s->offset;
	c->imported[i].formato_drm = s->formato_drm;
	c->imported[i].modifier = s->modifier;
	c->imported[i].surface = surface;
	return surface;
}

/* Opens the GPU conversion context, at the size in force.
 * ⛔ It is reopened when the size changes: a VPP context carries the size inside,
 *    exactly like the surface store. */
static bool open_vpp(Encoder *c, uint32_t width, uint32_t height)
{
	VADisplay dpy = display_di(c);
	VAStatus state;

	if (!dpy)
		return false;
	if (c->vpp_open && c->vpp_l == width && c->vpp_a == height)
		return true;
	if (c->vpp_open) {
		vaDestroyContext(dpy, c->vpp_context);
		vaDestroyConfig(dpy, c->vpp_configuration);
		c->vpp_open = false;
	}
	/*
	 * ⛔ AND HERE WE ASK THE DRIVER, not ffmpeg: `VAEntrypointVideoProc` is there or
	 *    it is not, and if it is not this route **does not exist on this machine**.
	 *    ⚠ It is the same rule by which `open_device()` asks for the encoding
	 *    entrypoints: "I asked it for it" and "it has it" look the same
	 *    until you look (`LESSONS.md` §1.11).
	 */
	state = vaCreateConfig(dpy, VAProfileNone, VAEntrypointVideoProc, NULL, 0,
	                       &c->vpp_configuration);
	if (state != VA_STATUS_SUCCESS) {
		registro_dice(LOG_ENCODING,
		              "⛔ this card has no GPU conversion (VAProfileNone / "
		              "VAEntrypointVideoProc: %s): zero copy is NOT viable here, "
		              "and it is declared instead of falling back silently",
		              vaErrorStr(state));
		return false;
	}
	state = vaCreateContext(dpy, c->vpp_configuration, (int) width, (int) height,
	                        VA_PROGRESSIVE, NULL, 0, &c->vpp_context);
	if (state != VA_STATUS_SUCCESS) {
		registro_dice(LOG_ENCODING,
		              "⛔ the %ux%u conversion context did not open: %s",
		              width, height, vaErrorStr(state));
		vaDestroyConfig(dpy, c->vpp_configuration);
		return false;
	}
	c->vpp_open = true;
	c->vpp_l = width;
	c->vpp_a = height;
	{
		const char *e = getenv("REMOTIX_VPP_PADDING");
		if (e && strcmp(e, "0") == 0)
			c->vpp_padding_off = true;
	}
	return true;
}

static void close_vpp(Encoder *c)
{
	VADisplay dpy = display_di(c);

	if (!c->vpp_open || !dpy)
		return;
	vaDestroyContext(dpy, c->vpp_context);
	vaDestroyConfig(dpy, c->vpp_configuration);
	c->vpp_open = false;
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
/*
 * ⭐⭐ THE PADDING ON ZERO COPY (15 Oct 2026, the question of 4b194bbc).
 *
 * The destination surface is the aligned one (`vadirect.c`, the input pool):
 * 1920x1088 for a 1080 canvas in H.264, and the VPP writes only the canvas.
 * ⛔ The rows and columns past it are ENCODED (the SPS crops them only from
 *    what is shown) and nobody writes them: on iHD the driver's colour fill
 *    paints the part of the target the output region does not cover with
 *    `output_background_color` (black, Y 16) — `[S]` media-driver's
 *    colorfill rule, not measured; on radeonsi nothing is written at all, and
 *    the rows hold what the allocation held.  A step from the picture to
 *    black or to garbage, every key, next to the last visible row.
 * ⭐ THE CURE, in the SAME picture (`vaBeginPicture` … `vaEndPicture`): up to
 *    three more layers, each the source's last row / last column / last
 *    pixel STRETCHED over the padding — a 1-sample source region scaled into
 *    the strip is a copy of the edge, the rule of the memory route
 *    (`colors709_copy_padded()`) and of the Vulkan shader (`clamp()`).
 *    ⚠ In the same picture and not in a second one: on iHD a second picture
 *    whose output region does not cover the target would colour-fill the
 *    whole target again, the canvas included.  ⚠ `VA_FILTER_SCALING_FAST`
 *    on the strips: on a sampler that is bilinear the first padding rows
 *    take a part of the row above the edge; it is padding, and continuous.
 * ⛔ Not measured on a card on the day it was written (the server was in the
 *    final round): if the driver refuses the layers the frame is redone at
 *    once with the canvas alone, as before, and a line says so; and
 *    REMOTIX_VPP_PADDING=0 switches them off for an A/B on a box.
 */
static VAStatus vpp_render(Encoder *c, VADisplay dpy, VASurfaceID destination,
                           VAProcPipelineParameterBuffer *p, unsigned n)
{
	VABufferID buffer[4] = { VA_INVALID_ID, VA_INVALID_ID, VA_INVALID_ID, VA_INVALID_ID };
	VAStatus state, fine;
	unsigned made = 0;

	state = vaBeginPicture(dpy, c->vpp_context, destination);
	if (state != VA_STATUS_SUCCESS) {
		registro_dice(LOG_ENCODING, "⛔ vaBeginPicture: %s", vaErrorStr(state));
		return state;
	}
	for (; made < n; made++) {
		state = vaCreateBuffer(dpy, c->vpp_context, VAProcPipelineParameterBufferType,
		                       sizeof p[made], 1, &p[made], &buffer[made]);
		if (state != VA_STATUS_SUCCESS) {
			registro_dice(LOG_ENCODING, "⛔ vaCreateBuffer: %s", vaErrorStr(state));
			break;
		}
	}
	if (state == VA_STATUS_SUCCESS) {
		state = vaRenderPicture(dpy, c->vpp_context, buffer, (int) n);
		if (state != VA_STATUS_SUCCESS)
			registro_dice(LOG_ENCODING, "⛔ vaRenderPicture (%u layers): %s", n,
			              vaErrorStr(state));
	}
	fine = vaEndPicture(dpy, c->vpp_context);
	for (unsigned k = 0; k < made; k++)
		vaDestroyBuffer(dpy, buffer[k]);
	if (state == VA_STATUS_SUCCESS && fine != VA_STATUS_SUCCESS) {
		registro_dice(LOG_ENCODING, "⛔ vaEndPicture (%u layers): %s", n, vaErrorStr(fine));
		state = fine;
	}
	return state;
}

static bool convert_on_gpu(Encoder *c, VASurfaceID source, VASurfaceID destination)
{
	VADisplay dpy = display_di(c);
	VAProcPipelineParameterBuffer p[4];
	VAStatus state;
	VARectangle region, from[3], to[3];
	unsigned layers = 1;

	if (!dpy || !c->vpp_open)
		return false;

	memset(p, 0, sizeof p);
	p[0].surface = source;
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
	region.x = 0;
	region.y = 0;
	region.width = (unsigned short) c->vpp_l;
	region.height = (unsigned short) c->vpp_a;
	p[0].surface_region = &region;
	p[0].output_region = &region;
	p[0].output_background_color = 0xff000000;
	p[0].filter_flags = VA_FRAME_PICTURE;
	p[0].filters = NULL;
	p[0].num_filters = 0;
	p[0].surface_color_standard = VAProcColorStandardNone; /* the source is RGB */
	p[0].output_color_standard = VAProcColorStandardBT709;
	p[0].input_color_properties.color_range = VA_SOURCE_RANGE_FULL;
	p[0].output_color_properties.color_range = VA_SOURCE_RANGE_REDUCED;

	/* ⭐ The padding layers: the edge of the SOURCE stretched over the strips
	 *    of the aligned destination (see the box above). */
	if (!c->vpp_padding_off && c->va) {
		const VaDirectDeclaration *d = vadirect_declaration(c->va);
		const uint32_t l = c->vpp_l, a = c->vpp_a;
		const uint32_t sl = d ? d->surface_width : l, sa = d ? d->surface_height : a;
		unsigned k = 0;
		if (sa > a) {                                  /* below: the last row */
			from[k] = (VARectangle){ 0, (short) (a - 1), (unsigned short) l, 1 };
			to[k] = (VARectangle){ 0, (short) a, (unsigned short) l,
			                       (unsigned short) (sa - a) };
			k++;
		}
		if (sl > l) {                                  /* right: the last column */
			from[k] = (VARectangle){ (short) (l - 1), 0, 1, (unsigned short) a };
			to[k] = (VARectangle){ (short) l, 0, (unsigned short) (sl - l),
			                       (unsigned short) a };
			k++;
		}
		if (sa > a && sl > l) {                        /* the corner: the last pixel */
			from[k] = (VARectangle){ (short) (l - 1), (short) (a - 1), 1, 1 };
			to[k] = (VARectangle){ (short) l, (short) a, (unsigned short) (sl - l),
			                       (unsigned short) (sa - a) };
			k++;
		}
		for (unsigned i = 0; i < k; i++) {
			p[1 + i] = p[0];
			p[1 + i].surface_region = &from[i];
			p[1 + i].output_region = &to[i];
			p[1 + i].filter_flags = VA_FRAME_PICTURE | VA_FILTER_SCALING_FAST;
		}
		layers = 1 + k;
	}

	state = vpp_render(c, dpy, destination, p, layers);
	if (state != VA_STATUS_SUCCESS && layers > 1) {
		/* ⛔ The driver refused the padding layers: the frame again with the
		 *    canvas alone, as before 15 Oct 2026, and no more layers on this
		 *    encoder.  The padding is then the driver's (see the box above). */
		c->vpp_padding_off = true;
		registro_dice(LOG_ENCODING,
		              "⚠ VPP: the %u padding layers were refused (%s): the padding "
		              "past %ux%u stays the driver's, the canvas is converted alone",
		              layers - 1, vaErrorStr(state), c->vpp_l, c->vpp_a);
		layers = 1;
		state = vpp_render(c, dpy, destination, p, 1);
	}
	if (state != VA_STATUS_SUCCESS)
		return false;
	if (layers > 1 && !c->vpp_padding_logged) {
		c->vpp_padding_logged = true;
		registro_dice(LOG_ENCODING,
		              "⭐ VPP: the padding past %ux%u is filled with copies of the edge "
		              "(%u layers in the same picture; REMOTIX_VPP_PADDING=0 switches "
		              "them off)", c->vpp_l, c->vpp_a, layers - 1);
	}
	/* ⛔⭐ AND HERE WE REALLY WAIT — see the box at the top: this line IS the
	 *     release.  When it returns, the GPU has finished reading the
	 *     compositor's buffer, and whoever captured it can give it back. */
	state = vaSyncSurface(dpy, destination);
	if (state != VA_STATUS_SUCCESS) {
		registro_dice(LOG_ENCODING, "⛔ vaSyncSurface: %s", vaErrorStr(state));
		return false;
	}
	return true;
}

/*
 * Prepares the encoder's frame starting from the DMA-BUF — the half of the
 * zero copy that sits inside the attempts loop.
 *
 * ⛔ It is redone on every attempt, and it is not waste: if the frame breaks the
 *    16 MiB ceiling, `lower_quality()` **closes and reopens the context and the
 *    store**, so the destination surface of the previous round no longer
 *    exists.  ⚠ The SOURCE surface instead stays: it is imported on the device,
 *    which nobody closes.
 */
static bool prepare_from_card(Encoder *c, const EncoderSurface *s, uint64_t *us,
                                 uint64_t *load_us)
{
	uint64_t t0 = now_us();
	VASurfaceID source, destination;

	/* ⛔ The upload to the GPU IS NOT THERE on this route, and the zero says so.
	 *    ⚠ Whoever reads the table of stretches must be able to tell "free" from
	 *    "does not exist", and here the first-time log line writes it. */
	*load_us = 0;

	if (!open_vpp(c, c->request.width, c->request.height))
		return false;
	source = import_dmabuf(c, s);
	if (source == VA_INVALID_ID)
		return false;

	/* ⭐ Phase 18: the input surface is given by vadiretta, from its store
	 *    (a new one on every round, as yesterday with libavutil's store). */
	destination = vadirect_input_surface(c->va);
	if (destination == VA_INVALID_ID) {
		registro_dice(LOG_ENCODING, "⛔ no input surface (%d ready)",
		              READY_SURFACES);
		return false;
	}
	if (!convert_on_gpu(c, source, destination))
		return false;
	c->surface_ready = destination;
	*us = now_us() - t0;

	if (!c->logged_zero_copy) {
		c->logged_zero_copy = true;
		registro_dice(LOG_ENCODING,
		              "⭐⭐ ZERO COPY in force: the compositor's DMA-BUF (fd %d, %ux%u, "
		              "stride %u, modifier 0x%llx) is imported as a VA-API surface and "
		              "converted to %s BY THE GPU — no `memcpy`, no CPU "
		              "conversion, no upload.  ⚠ The conversion remains and costs "
		              "%llu us: what changed is WHO does it, not that it must be done",
		              s->fd, s->width, s->height, s->stride,
		              (unsigned long long) s->modifier,
		              c->request.depth == 10 ? "P010" : "NV12",
		              (unsigned long long) *us);
	}
	return true;
}

/*
 * Fills the frame that enters the encoder, from the caller's pixels.
 *
 * ⭐ In hardware there are TWO steps and they are timed SEPARATELY:
 *      `us_conversione`  `colors709.c`, in system memory — the stretch that
 *                        was already there;
 *      `upload_us`  system memory → GPU — ⛔ the stretch that the phase 8
 *                        zero copy exists to remove.  Adding it to the
 *                        encoding would make invisible how much that work is worth.
 *
 * ⛔⭐ PHASE 18, AND THE ROUTE IS BACK TO WHAT IT WAS BEFORE: CPU conversion
 *     and then upload of the NV12/P010 planes.  In the first draft of the
 *     card line the BGRx were uploaded as they were into an RGB surface and
 *     the VPP converted them; `[M]` 30 Sep 2026 (`benches/18-card/18-confronto.sh`,
 *     120 frames of fake desktop) that route was WORSE than the
 *     CPU conversion: Intel 1080p H.264 −1 dB and +82 % bytes, HEVC −4 dB
 *     and +255 %; Radeon −1…−6 dB.  ⇒ The VPP stays with the zero copy, where the
 *     frame is already on the card and there is no CPU to call on.
 */
static bool prepare_frame(Encoder *c, const uint8_t *pixel, uint32_t step,
                               uint64_t *us, uint64_t *load_us)
{
	uint64_t t0 = now_us();

	*load_us = 0;
	*us = 0;

	char error[256] = { 0 };
	const uint32_t l = c->request.width, a = c->request.height;
	VASurfaceID destination = vadirect_input_surface(c->va);
	if (destination == VA_INVALID_ID) {
		registro_dice(LOG_ENCODING, "⛔ no input surface (%d ready)",
		              READY_SURFACES);
		return false;
	}
	if (FORMATO_PIXEL_IMPACCHETTATO(c->request.fmt)) {
		if (!c->staging) {
			registro_dice(LOG_ENCODING, "⛔ the NV12/P010 staging buffer was not allocated");
			return false;
		}
		Colori709Ordine order = (c->request.fmt == CODIFICATORE_PIXEL_RGBX)
		                             ? COLORI709_RGBX
		                             : COLORI709_BGRX;
		uint32_t pixel_stride = step ? step : l * 4u;
		bool ok, loaded;
		uint64_t t1;
		if (c->request.depth == 10) {
			uint16_t *y = (uint16_t *) c->staging;
			uint16_t *uv = y + (size_t) l * a;
			ok = colors709_to_p010(pixel, pixel_stride, l, a, order, y, l * 2u, uv, l * 2u);
			*us = now_us() - t0;
			t1 = now_us();
			loaded = ok && vadirect_load_p010(c->va, destination, y, l * 2u, uv, l * 2u,
			                                       error, sizeof error);
		} else {
			uint8_t *y = c->staging;
			uint8_t *uv = y + (size_t) l * a;
			ok = colors709_to_nv12(pixel, pixel_stride, l, a, order, y, l, uv, l);
			*us = now_us() - t0;
			t1 = now_us();
			loaded = ok && vadirect_load_nv12(c->va, destination, y, l, uv, l, error,
			                                       sizeof error);
		}
		if (!ok) {
			registro_dice(LOG_ENCODING, "⛔ the colour conversion refused %ux%u", l, a);
			return false;
		}
		if (!loaded) {
			registro_dice(LOG_ENCODING, "⛔ the planes were not uploaded to the card: %s", error);
			return false;
		}
		*load_us = now_us() - t1;
	} else {
		/* yuv420p10le (the bench) → P010, directly into the input */
		if (!vadirect_load_yuv420p10(c->va, destination, pixel, step, error,
		                                sizeof error)) {
			registro_dice(LOG_ENCODING, "⛔ the samples were not uploaded to the card: %s",
			              error);
			return false;
		}
		*load_us = now_us() - t0;
	}
	c->surface_ready = destination;
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
 * ⛔ The symptom was a session BLACK forever: `bitstream_ok()` rightly refuses
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
 *   `bitstream_ok()` refuses it as before.
 */
/*
 * ⭐ PHASE 18: WE write the frame, bit by bit, and no longer with libavcodec's
 *    `hevc_metadata`/`h264_metadata` filter.  The method: we reread
 *    the SPS up to the cropping flag (the reader above says WHERE it is,
 *    `FramePosition`), we rewrite the head unchanged, then the flag at 1 with the
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
static bool rewrite_sps_with_crop(Encoder *c, size_t sps_offset, size_t sps_byte)
{
	const bool hevc = c->request.codec == CODIFICATORE_HEVC;
	const size_t head_byte = hevc ? 2 : 1;
	const uint8_t *nal = c->output + sps_offset;
	uint8_t *rbsp, *new_rbsp, *new_nal, *frame;
	size_t n, last_one, new_byte, code_start, after, total;
	EncoderConfession was_read;
	FramePosition dove;
	BitWriter w;
	bool ok;

	memset(&was_read, 0, sizeof was_read);
	memset(&dove, 0, sizeof dove);
	ok = hevc ? read_hevc_sps(nal, sps_byte, &was_read, &dove)
	          : read_h264_sps(nal, sps_byte, &was_read, &dove);
	if (!ok || sps_byte <= head_byte)
		return false;

	rbsp = malloc(sps_byte);
	new_rbsp = malloc(sps_byte + 32);
	new_nal = malloc(sps_byte + 64);
	if (!rbsp || !new_rbsp || !new_nal) {
		free(rbsp);
		free(new_rbsp);
		free(new_nal);
		return false;
	}
	n = remove_emulation(nal + head_byte, sps_byte - head_byte, rbsp, sps_byte);
	/* the stop bit: the LAST 1 of the RBSP */
	last_one = 0;
	for (size_t b = n * 8; b > 0; b--) {
		if ((rbsp[(b - 1) >> 3] >> (7 - ((b - 1) & 7))) & 1u) {
			last_one = b - 1;
			break;
		}
	}
	if (dove.bit_after > last_one || dove.bit_flag >= dove.bit_after) {
		free(rbsp);
		free(new_rbsp);
		free(new_nal);
		return false;
	}
	bw_open(&w, new_rbsp, sps_byte + 32);
	bw_copy_bit(&w, rbsp, 0, dove.bit_flag);
	bw_flag(&w, true);
	bw_ue(&w, dove.sx);
	bw_ue(&w, dove.dx + c->border_dx / 2);
	bw_ue(&w, dove.su);
	bw_ue(&w, dove.down + c->border_dy / 2);
	bw_copy_bit(&w, rbsp, dove.bit_after, last_one - dove.bit_after);
	bw_close_rbsp(&w);
	if (w.overflowed) {
		free(rbsp);
		free(new_rbsp);
		free(new_nal);
		return false;
	}
	new_byte = nal_annexb(new_nal, sps_byte + 64, nal, head_byte, new_rbsp, bw_byte(&w));
	free(rbsp);
	free(new_rbsp);
	if (!new_byte) {
		free(new_nal);
		return false;
	}
	/* the start code in front of the old SPS: 3 or 4 bytes */
	code_start = sps_offset - 3;
	if (code_start > 0 && c->output[code_start - 1] == 0)
		code_start--;
	after = sps_offset + sps_byte;
	total = code_start + new_byte + (c->output_byte - after);
	frame = malloc(total);
	if (!frame) {
		free(new_nal);
		return false;
	}
	memcpy(frame, c->output, code_start);
	memcpy(frame + code_start, new_nal, new_byte);
	memcpy(frame + code_start + new_byte, c->output + after, c->output_byte - after);
	free(new_nal);
	free(c->output);
	c->output = frame;
	c->output_capabilities = total;
	c->output_byte = total;
	return true;
}

static bool border_in_place(Encoder *c, bool key)
{
	const bool hevc = c->request.codec == CODIFICATORE_HEVC;
	size_t off = 0, n = 0;

	if (!hevc && c->request.codec != CODIFICATORE_H264)
		return true;
	if (!key)
		return true;

	/* where the SPS is in this frame */
	if (hevc) {
		AnnexBLayout f;
		annexb_read(c->output, c->output_byte, &f);
		off = f.sps_offset;
		n = f.sps_byte;
	} else {
		AnnexB264Layout f;
		annexb264_read(c->output, c->output_byte, &f);
		off = f.sps_offset;
		n = f.sps_byte;
	}
	if (!n)
		return true; /* no SPS: `bitstream_ok()` decides */

	if (!c->decided_border) {
		EncoderConfession was_read;
		memset(&was_read, 0, sizeof was_read);
		bool ok = hevc ? read_hevc_sps(c->output + off, n, &was_read, NULL)
		               : read_h264_sps(c->output + off, n, &was_read, NULL);
		if (!ok)
			return true; /* no readable SPS: `bitstream_ok()` decides */
		c->decided_border = true;
		c->active_border = false;
		uint32_t dx = was_read.stream_width - c->request.width;
		uint32_t dy = was_read.stream_height - c->request.height;
		if (was_read.stream_width < c->request.width ||
		    was_read.stream_height < c->request.height || (dx == 0 && dy == 0) ||
		    dx >= 64 || dy >= 64 || (dx | dy) & 1u)
			return true;
		c->active_border = true;
		c->border_dx = dx;
		c->border_dy = dy;
		registro_dice(LOG_ENCODING,
		              "⭐ D-023: «%s» declares %ux%u for a %ux%u canvas (it encodes the "
		              "multiple of the block and does not write the frame): I write it in the SPS, "
		              "bit by bit, %u columns and %u rows cropped on the right and at the bottom",
		              c->component_name, was_read.stream_width, was_read.stream_height,
		              c->request.width, c->request.height, dx, dy);
	}
	if (!c->active_border)
		return true;
	if (!rewrite_sps_with_crop(c, off, n)) {
		registro_dice(LOG_ENCODING,
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
static bool bitstream_ok(Encoder *c, const uint8_t *data, size_t byte, bool *key)
{
	if (c->request.codec == CODIFICATORE_HEVC) {
		AnnexBLayout f;
		annexb_read(data, byte, &f);
		*key = f.first_vcl_is_key;
		if (byte >= 4 && !(data[0] == 0 && data[1] == 0 && (data[2] == 1 || (data[2] == 0 && data[3] == 1)))) {
			registro_dice(LOG_ENCODING,
			              "⛔ the frame does not start with a start code: it looks "
			              "length-prefixed (hvcC), and D1 says Annex-B");
			return false;
		}
		if (f.first_vcl_is_key && !f.parameters_before_idr) {
			registro_dice(LOG_ENCODING,
			              "⛔ key without VPS+SPS+PPS in front: in Annex-B the «key» chunk "
			              "must carry them, or the symptom is a black screen with the frames "
			              "arriving (v1 encoder.c:268-272)");
			return false;
		}
		if (!c->conf.read_from_stream && f.sps_byte)
			c->conf.read_from_stream =
			    read_hevc_sps(data + f.sps_offset, f.sps_byte, &c->conf, NULL);
	} else if (c->request.codec == CODIFICATORE_H264) {
		AnnexB264Layout f;

		annexb264_read(data, byte, &f);
		*key = f.first_vcl_is_key;
		if (byte >= 4
		    && !(data[0] == 0 && data[1] == 0
		         && (data[2] == 1 || (data[2] == 0 && data[3] == 1)))) {
			registro_dice(LOG_ENCODING,
			              "⛔ the H.264 frame does not start with a start code: "
			              "it looks length-prefixed (avcC), and the browser without "
			              "`description` wants Annex-B");
			return false;
		}
		if (f.first_vcl_is_key && !f.parameters_before_idr) {
			registro_dice(LOG_ENCODING,
			              "⛔ H.264 key without SPS+PPS in front: in Annex-B the "
			              "«key» chunk must carry them, or whoever connects later stays black");
			return false;
		}
		if (!c->conf.read_from_stream && f.sps_byte)
			c->conf.read_from_stream =
			    read_h264_sps(data + f.sps_offset, f.sps_byte, &c->conf, NULL);
	} else {
		ObuLayout f;
		obu_read(data, byte, &f);
		*key = f.first_frame_is_key;
		if (f.has_key && !f.sequence_before_key) {
			registro_dice(LOG_ENCODING,
			              "⛔ AV1 key without a sequence header in front: a client that "
			              "connects later receives a bare key");
			return false;
		}
		if (!c->conf.read_from_stream && f.seq_byte)
			c->conf.read_from_stream =
			    read_av1_sequence(data + f.seq_offset, f.seq_byte, &c->conf);
	}

	/* ⛔ SECOND WITNESS: the depth and the size read IN THE BYTES. */
	if (c->conf.read_from_stream) {
		if (c->conf.stream_depth != c->request.depth) {
			registro_dice(LOG_ENCODING,
			              "⛔ E2: %d bits requested, and the stream declares %d",
			              c->request.depth, c->conf.stream_depth);
			c->conf.has_obeyed = false;
			di(c->conf.why_no, sizeof(c->conf.why_no),
			   "the stream carries %d bits instead of %d", c->conf.stream_depth,
			   c->request.depth);
			return false;
		}
		if (c->conf.stream_width != c->request.width ||
		    c->conf.stream_height != c->request.height) {
			registro_dice(LOG_ENCODING,
			              "⛔ the stream SHOWS %ux%u (it encodes %ux%u) and the canvas is "
			              "%ux%u: RCP.md §6.2 wants the size of the canvas in force",
			              c->conf.stream_width, c->conf.stream_height,
			              c->conf.encoded_width, c->conf.encoded_height,
			              c->request.width, c->request.height);
			return false;
		}
	}
	return true;
}

/*
 * Reopens at lower quality, for the 16 MiB ceiling.
 *
 * ⭐ `products` are the BYTES that triggered the descent, and they are not an
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
static bool change_quality(Encoder *c, char *error, size_t error_byte)
{
	close_context(c);
	if (open_context(c, error, error_byte) < 0)
		return false;
	/* ⛔ The store was reopened together with the context: the frames must be
	 *    rebound, or the next round would upload onto surfaces of a closed
	 *    store. */
	if (open_frames(c, error, error_byte) < 0)
		return false;
	c->next_key = true;
	return true;
}

static bool lower_quality(Encoder *c, uint32_t products)
{
	char error[256] = { 0 };
	int before = c->current_quality;
	ModoQualita prev_mode = c->current_mode;

	/* ⛔ THE RELAPSE IS PAID BEFORE KNOWING WHETHER THE DESCENT SUCCEEDS: if we had
	 *    just climbed and the ceiling bites again, the wait doubles.  ⚠ Without
	 *    this, a scene on the edge would make the door slam every two seconds
	 *    at 91-108 ms a time — and the price would be paid by the RATE, that is
	 *    precisely the invariant this cure claims to needs. */
	c->below_margin = 0;
	if (c->recently_risen) {
		uint32_t era = c->rise_wait;
		c->rise_wait = era >= RISE_WAIT_MAX / 2u ? RISE_WAIT_MAX
		                                                     : era * 2u;
		c->recently_risen = false;
		registro_dice(LOG_ENCODING,
		              "⚠ RELAPSE: the ceiling bit right after a climb ⇒ the "
		              "next one waits %u frames instead of %u.  ⛔ It is the defence "
		              "against FLAPPING: every round costs a reopening and a "
		              "key, [M] 91-108 ms on the card",
		              c->rise_wait, era);
	}

	if (c->current_mode == CODIFICATORE_QUALITA_LOSSLESS) {
		/* ⚠ Lossless does not exist on the card (and since phase 19 not
		 *   elsewhere either): historical branch, we exit to CRF as before. */
		c->current_mode = CODIFICATORE_QUALITA_CRF;
		c->current_quality = EMERGENCY_CRF;
	} else {
		/* ⚠ The mode does NOT change: whoever was on QP stays on QP.  Switching to CRF under the
		 *   ceiling would mean changing quantity mid-session, that is two
		 *   measurements under the same label. */
		c->current_quality += CRF_STEP;
		if (c->current_quality > 51)
			c->current_quality = 51;
	}
	if (c->current_quality == before && c->current_mode == prev_mode)
		return false;

	if (!change_quality(c, error, sizeof(error))) {
		registro_dice(LOG_ENCODING, "⛔ did not reopen at lower quality: %s", error);
		return false;
	}

	/*
	 * ⛔⛔ THE DESCENT IS DECLARED — and until 23 Aug 2026 it was NOT declared.
	 *
	 * `lower_quality()` succeeded **silently**: the only line there was
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
	 *   the defect of the 30.8 GB of log of 14 Aug (`child.c`).
	 */
	registro_dice(LOG_ENCODING,
	              "⛔ QUALITY DOWN: %s %d → %s %d — the frame made %u bytes "
	              "against the ceiling's %u (RCP.md §6.2), that is %u %% of the threshold.  "
	              "⚠ If this percentage were not ABOVE 100 the descent would have "
	              "been out of caution, and I1 forbids it: the measurement is written here so that "
	              "it can be verified from outside without trusting the code",
	              mode_name(prev_mode), before, mode_name(c->current_mode),
	              c->current_quality, products, FRAME_CAP,
	              (unsigned) (((uint64_t) products * 100u) / FRAME_CAP));
	return true;
}

/*
 * ⭐⭐ A SINGLE RUNG TOWARDS THE REQUESTED QUALITY, AND NO FURTHER — phase 9.
 *
 * ⛔ IT DOES NOT GO BACK TO LOSSLESS: `lower_quality()` leaves LOSSLESS once
 *    and for ever, because re-entering it would mean changing **quantity**
 *    mid-session — the same reason why the mode does not change on the way down.
 *
 * ⛔⛔ AND IT IS NOT CALLED WITH A PACKET IN HAND, and that is the constraint that decides
 *      WHERE this function sits: `close_context()` **frees** the
 *      encoder and the bytes it holds, it does not merely unhook them — and after the `break` of
 *      `compress_common()` the caller's `report->data` points in there.
 *      ⇒ We COUNT at delivery and CLIMB at the entry of the next frame.
 *      ⭐ Good side effect: the cost of the reopening falls **between** two
 *        frames instead of in the middle of delivering one.
 *
 * Returns `false` only if the context was left broken: climbing is optional,
 * and a cure that kills the session when it fails is worse than the defect.
 */
static bool raise_quality(Encoder *c)
{
	char error[256] = { 0 };

	if (!rise_enabled)
		return true;                        /* ⛔ invariant I6: off by default */
	if (c->packet_in_hand)
		return true;                        /* ⛔ the constraint above */
	if (c->current_mode != c->request.mode)
		return true;                        /* left LOSSLESS: no going back in */
	if (c->current_quality <= c->request.quality)
		return true;                        /* already at the requested working point */
	if (c->below_margin < c->rise_wait)
		return true;                        /* not calm enough yet */

	int before = c->current_quality;
	int after = before - CRF_STEP;
	/* ⛔ THE FLOOR IS WHAT WAS REQUESTED, and no field is needed to
	 *    remember it: `c->request` keeps the request intact. */
	if (after < c->request.quality)
		after = c->request.quality;
	/* ⛔ And we do not set foot on the rung where the ceiling already bit
	 *    until TWICE the wait has passed: that is not a suspicion,
	 *    it is a number MEASURED on this content. */
	if (c->failed_quality && after <= c->failed_quality
	    && c->below_margin < c->rise_wait * 2u)
		return true;

	uint32_t calm = c->below_margin; /* ⚠ the REAL number, not the threshold */
	c->current_quality = after;
	c->below_margin = 0;
	if (!change_quality(c, error, sizeof(error))) {
		/* ⚠ Climbing is OPTIONAL: if the context does not reopen at the new
		 *   value we go back to the one that worked, and the session carries on
		 *   grainy instead of dying. */
		registro_dice(LOG_ENCODING,
		              "⛔ did not reopen climbing to %s %d (%s): going back to %d",
		              mode_name(c->current_mode), after, error, before);
		c->current_quality = before;
		if (!change_quality(c, error, sizeof(error))) {
			registro_dice(LOG_ENCODING,
			              "⛔⛔ and not even at %s %d: the context is closed and nothing "
			              "more is sent — %s",
			              mode_name(c->current_mode), before, error);
			c->conf.has_obeyed = false;
			di(c->conf.why_no, sizeof(c->conf.why_no),
			   "the context did not reopen after a climb attempt: %s",
			   error);
			return false;
		}
		c->next_key = true;
		c->rise_wait = c->rise_wait >= RISE_WAIT_MAX / 2u
		                         ? RISE_WAIT_MAX
		                         : c->rise_wait * 2u;
		return true;
	}

	c->recently_risen = true;
	/* ⛔ New context, no past: `RCP.md` §5.2 wants a real key.
	 *    `open_context()` has already demanded it; the line stays because the rule is
	 *    written here, not elsewhere. */
	c->next_key = true;
	registro_dice(LOG_ENCODING,
	              "⭐ QUALITY UP: %s %d → %d after %u frames in a row below %u bytes "
	              "(one eighth of the ceiling), requested floor %d.  ⚠ It costs a reopening "
	              "and a KEY — [M] 91-108 ms in hardware, 1.8-3.3 s in software — and "
	              "that is why we climb ONE rung at a time and wait twice as long on "
	              "every relapse.  ⭐ It is DECISIONS.md §3.3 «never grainy»: without this "
	              "line a single exceptional frame left the session grainy "
	              "for hours",
	              mode_name(c->current_mode), before, after, calm, RISE_MARGIN,
	              c->request.quality);
	return true;
}

/* The encoded bytes are copied into `c->output`, which is ours: see the
 * structure.  It grows when needed and never shrinks. */
static bool put_in_output(Encoder *c, const uint8_t *data, size_t byte)
{
	if (byte > c->output_capabilities) {
		size_t new_one = byte + byte / 4 + 4096;
		uint8_t *p = realloc(c->output, new_one);
		if (!p) {
			registro_dice(LOG_ENCODING, "⛔ no memory for %zu output bytes", byte);
			return false;
		}
		c->output = p;
		c->output_capabilities = new_one;
	}
	memcpy(c->output, data, byte);
	c->output_byte = byte;
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
 *    each one is green on its own.  ⇒ ONLY how `c->frame` is filled
 *    changes, and that is the only `if` that tells them apart.
 *
 * ⚠ Exactly one of `pixel` and `surface` is non-NULL, and it is not an implicit
 *   convention: the guard demands it and writes it.
 */
static bool compress_common(Encoder *c, const uint8_t *pixel, uint32_t step,
                            const EncoderSurface *surface,
                            EncoderFrame *report)
{
	if (!c || !report)
		return false;
	if ((pixel == NULL) == (surface == NULL)) {
		registro_dice(LOG_ENCODING,
		              "⛔ we compress EITHER from the pixels OR from the surface, and here "
		              "%s arrived: we do not guess which of the two routes the caller "
		              "wanted",
		              pixel ? "both" : "neither");
		return false;
	}
	if (!c->conf.has_obeyed) {
		registro_dice(LOG_ENCODING, "⛔ it did not obey (%s): nothing is sent",
		              c->conf.why_no);
		return false;
	}
	if (c->packet_in_hand) {
		registro_dice(LOG_ENCODING, "⛔ the previous frame was not released");
		return false;
	}
	if (c->emptied) {
		/* ⛔ A context in drain no longer accepts frames: it is reopened, and the
		 *    reopening makes the next one a key.  Better one extra declared key
		 *    than a video that stops at the second frame. */
		char error[256] = { 0 };
		close_context(c);
		if (open_context(c, error, sizeof(error)) < 0) {
			registro_dice(LOG_ENCODING, "⛔ did not reopen after the drain: %s", error);
			return false;
		}
		if (open_frames(c, error, sizeof(error)) < 0) {
			registro_dice(LOG_ENCODING, "⛔ the frames did not reopen: %s", error);
			return false;
		}
		c->emptied = false;
		registro_dice(LOG_ENCODING, "reopened after the drain: the next one is a key");
	}
	memset(report, 0, sizeof(*report));

	/* ⭐ THE CLIMB SITS HERE, BEFORE ENCODING, and not after delivery: after
	 *    the `break` the packet is in the caller's hands and `close_context()`
	 *    FREES it.  ⚠ The count instead is kept at delivery, further down: that is where
	 *    we know how big it came out. */
	if (!raise_quality(c))
		return false;

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⛔⛔ WHO THIS FRAME IS — AND IT IS DECIDED **HERE**, BEFORE THE FIRST
	 *      DESCENT, not inside the loop.
	 *
	 * ⛔ THE DEFECT THIS LINE CURES (23 Aug 2026, phase 9).  The count
	 *    of re-encodings read `c->next_key` **inside** the loop, and
	 *    `lower_quality()` calls `open_context()`, which at `:2275` does
	 *    `c->next_key = true` — *"after every opening the first is a
	 *    key"*, and it is right that it does: a new context has no
	 *    references, and a delta after a reopening would be undecodable.
	 *    ⇒ From the FIRST descent on `c->next_key` was **always true**,
	 *      so `!c->next_key && attempt + 1 >= MAX_REENCODES`
	 *      was **always false**: the branch abandoning the delta was **dead
	 *      code**, and `MAX_REENCODES` never stopped a delta in its
	 *      life.  A delta above the ceiling walked the ladder **all the way down**,
	 *      and left only through the `break` (it fits) or through "not even at the bottom of the
	 *      ladder".  ⚠ Meanwhile the startup line declared *"a DELTA is abandoned
	 *      after 3 re-encodings"*, that is something that never happened.
	 *
	 * ⭐ And the same contamination made the "KEY above the
	 *   ceiling" line a liar: it printed it even for a frame born a delta.
	 *
	 * ⚠ The value is read AFTER `raise_quality()` on purpose: if the climb has
	 *   reopened the context, this frame **really is** a key, and the
	 *   whole ladder is its due.
	 *
	 * ───────────────────────────────────────────────────────────────────────
	 * ⭐ THE TESTIMONY THAT THE BRANCH WAS DEAD, and it is not my reasoning:
	 *   `phases/08-the-shortest-loop.md:2856` puts it among the `[?]` — *"the "abandoned
	 *   delta" branch: not walked even with the fault injected"* — and at
	 *   `:2810-2812`, with the ceiling lowered on purpose, the log says **"KEY
	 *   above the ceiling"** at attempt 2 and at 3.  ⚠ It is the contamination, seen
	 *   from outside: whoever rereads that bench was looking at the wrong label.
	 *
	 * ⛔⛔ THE FALSIFIABLE PREDICTION — `[?]`, and the hardware is the integrated Intel UHD 770,
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
	 *        is `attempt + 1 >= MAX_REENCODES` and `key_requested` is
	 *        false **only** for a frame born a delta.
	 *     b) *"delta abandoned"* and then the next frame is **not** a
	 *        key ⇒ the client is left without a past.  ⛔ It cannot happen:
	 *        every descent goes through `open_context()`, which at `:2275` imposes the
	 *        key — and if one day it removed that, THIS is the symptom to
	 *        look for.
	 *     c) *"delta abandoned"* repeating on every frame for seconds ⇒
	 *        it is one key for every abandoned delta, that is **the spiral** that
	 *        `RCP.md:1284-1286` names.  ⚠ The remedy is not here: it is lowering the
	 *        frames (`SPECS.md` §8.3) or the bandwidth ceiling.  ⛔ This
	 *        cure neither creates nor removes it — the spiral was already there, because the
	 *        reopening imposed the key before too.
	 *   ⚠ And the unexpected gain someone might hope for — "the delta goes through
	 *     instead of being abandoned" — **will not come**: when the count
	 *     bites, that frame has already broken the ceiling three times.
	 * ═══════════════════════════════════════════════════════════════════════ */
	const bool key_requested = c->next_key;

	for (uint32_t attempt = 0;; attempt++) {
		uint64_t us_conv = 0, load_us = 0;
		/* ⭐ PHASE 19: the ONLY `if` between the two card routes — and it sits before
		 *    the bytes boundary, like the `if` between memory and zero copy. */
		if (c->route == ROUTE_VULKAN) {
			if (!encode_vulkan(c, pixel, step, surface, report))
				return false;
			goto byte_ready;
		}
		bool ready = surface
		                  ? prepare_from_card(c, surface, &us_conv, &load_us)
		                  : prepare_frame(c, pixel, step, &us_conv, &load_us);
		if (!ready)
			return false;
		report->us_conversione = us_conv;
		report->upload_us = load_us;

		uint64_t t0 = now_us();
		{
			/* ⭐ PHASE 18 — the card: one round, one wait, the bytes.  No
			 *    EAGAIN by construction, no reordering by construction. */
			const uint8_t *data = NULL;
			size_t byte = 0;
			char error[256] = { 0 };
			if (!vadirect_encode(c->va, c->surface_ready, c->next_key, &data,
			                        &byte, error, sizeof error)) {
				registro_dice(LOG_ENCODING, "⛔ the card did not encode: %s", error);
				return false;
			}
			if (!put_in_output(c, data, byte))
				return false;
			report->us_codifica = now_us() - t0;
			report->trattenuto = false;
			c->packet_in_hand = true;
		}
byte_ready:
		/* ⛔ BOUNDARY — from here down we work on the BYTES in `c->output`. */

		/* ───────────────────────────────────────────────────────────────────
		 * ⛔ THE 16 MiB CEILING — `RCP.md` §6.2, and it binds WHOEVER SENDS. */
		if ((uint32_t) c->output_byte > FRAME_CAP) {
			/* ⭐ The size is read BEFORE throwing away the bytes, or the descent
			 *    line would say zero: it is the proof that the descent is measured (I1). */
			uint32_t products = (uint32_t) c->output_byte;
			/* ⚠ The ceiling in the message is PRINTED, not written by hand: a
			 *   log line that said "16 MiB" while the constant says
			 *   otherwise would send the hunt the wrong way. */
			registro_dice(LOG_ENCODING,
			              "⛔ frame of %zu bytes, beyond the %u of the RCP.md §6.2 ceiling: "
			              "RE-ENCODING at lower quality (attempt %u), not sending",
			              c->output_byte, FRAME_CAP, attempt + 1);
			c->packet_in_hand = false;

			/* ⛔ THE RUNG ON WHICH THE CEILING BIT is that of the FIRST
			 *    attempt: the others are descents that do not yet have a measurement
			 *    against them.  ⚠ It serves the climb, which on that one
			 *    alone waits twice as long before setting foot on it again. */
			if (attempt == 0)
				c->failed_quality = c->current_quality;

			/* ═══════════════════════════════════════════════════════════════
			 * ⛔⛔ AND ON A **KEY** WE DO NOT GIVE UP — `RCP.md` §5.2, and
			 *      until 22 Aug 2026 this branch abandoned it.
			 *
			 * §5.2 says the server **MUST NOT** abandon a key
			 * frame, and the reason is that a client without a key **has no
			 * past**: it cannot paint anything, neither now nor later.
			 *
			 * ⛔ AND THE DEFECT WAS NOT "one lost frame": it was a SPIRAL.
			 *    The client stays broken ⇒ sends `REQUEST_KEY` ⇒ we redo
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
			 * ⇒ A DELTA makes `MAX_REENCODES` **encodings** in all, that is
			 *   `MAX_REENCODES - 1` descents, and each one of those is
			 *   **tried**.
			 *
			 * ⛔ AND ABANDONING HERE DOES NOT BREAK §5.2, and the reason is an invariant
			 *    that can be checked: with `MAX_REENCODES >= 2`
			 *    the abandonment comes **after at least one reopening**, and every
			 *    reopening leaves `c->next_key = true` (`:2275`).  ⇒ The
			 *    next frame is a KEY, which is exactly what §5.2
			 *    demands after an abandoned delta (*"the server MUST send a
			 *    key as soon as it can"*).  ⚠ And if one day `MAX_REENCODES`
			 *    dropped to 1, the abandonment would happen **without** a reopening: there
			 *    the context is intact, the client still has its past, and it is
			 *    fine all the same.  The two cases are covered, and they are the only two.
			 * ═══════════════════════════════════════════════════════════════ */
			if (!key_requested && attempt + 1 >= MAX_REENCODES) {
				registro_dice(LOG_ENCODING,
				              "⚠ delta abandoned after %u encodings (RICODIFICHE_"
				              "MASSIME) and %u TRIED descents: at %s %d it is still above "
				              "the %u bytes.  ⭐ It is not a key, so whoever is watching still "
				              "has their past — and the next frame is "
				              "a KEY anyway (§5.2), because the descents have "
				              "reopened the context.  ⛔ We do not descend another "
				              "rung: it would be applied and never tried",
				              attempt + 1, attempt,
				              c->current_mode == CODIFICATORE_QUALITA_QP ? "QP" : "CRF",
				              c->current_quality, FRAME_CAP);
				return false;
			}
			if (!lower_quality(c, products)) {
				/* ⛔ The bottom of the ladder: here it is not "I give up because of a count
				 *    of attempts", it is "there is nothing left to lower".  It is
				 *    the only case in which a key does not leave, and the line says
				 *    WHICH of the two it is. */
				registro_dice(LOG_ENCODING,
				              "⛔⛔ not even at the bottom of the ladder (%s %d) does the frame fit "
				              "under the %u bytes: it does NOT leave.  ⚠ And this is NOT \"I "
				              "gave up after %u attempts\": it is \"there is nothing left to "
				              "lower\"",
				              c->current_mode == CODIFICATORE_QUALITA_QP ? "QP" : "CRF",
				              c->current_quality, FRAME_CAP, attempt + 1);
				return false;
			}
			/* ⚠ AND THE RETRY IS A KEY EVEN IF THE FRAME WAS A DELTA:
			 *   `open_context()` has thrown away the references, and a delta without
			 *   a past is decoded by nobody.  ⛔ The line says so instead of
			 *   calling both of them "KEY", which is what it did as long as the
			 *   count read `c->next_key` contaminated by the reopening. */
			/* ⚠ The ceiling of encodings is PRINTED from the constant, not written
			 *   by hand: it is the same rule as the ladder line at startup. */
			char how_many[72];
			if (key_requested)
				snprintf(how_many, sizeof(how_many),
				         "as many as the ladder has — a key is not abandoned");
			else
				snprintf(how_many, sizeof(how_many), "%d (MAX_REENCODES)",
				         MAX_REENCODES);
			registro_dice(LOG_ENCODING,
			              "⚠ %s above the ceiling: going down to %s %d and RETRYING (encoding %u of "
			              "%s).  ⛔ A key is not abandoned (§5.2): the picture "
			              "will come out uglier, and this line is the declaration.  "
			              "⭐ `[M]` at the bottom of the ladder (51) an 8K key is worth 1.771 "
			              "MiB, that is 10.6 %% of the ceiling",
			              key_requested ? "KEY"
			                             : "delta (and the retry will be a KEY: the "
			                               "context is new and no longer has a past)",
			              c->current_mode == CODIFICATORE_QUALITA_QP ? "QP" : "CRF",
			              c->current_quality, attempt + 2, how_many);
			report->reencodes = attempt + 1;
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
	if ((uint32_t) c->output_byte <= RISE_MARGIN) {
		if (c->below_margin < UINT32_MAX)
			c->below_margin++;
		/* The climb held up to the requested working point: the next
		 * bite is not its fault, and the wait does not double. */
		if (c->recently_risen && c->current_quality <= c->request.quality
		    && c->below_margin >= c->rise_wait)
			c->recently_risen = false;
	} else {
		c->below_margin = 0;
	}

	bool key = false;
	if (!border_in_place(c, key_requested || c->next_key) ||
	    !bitstream_ok(c, c->output, c->output_byte, &key)) {
		c->packet_in_hand = false;
		return false;
	}

	/* ⛔ `RCP.md` §5.2: the first frame after `SESSION`, and the first after a
	 *    canvas change, MUST be a key.  If we had asked for it and it is
	 *    not, it is not sent: a delta marked key is what Chromium
	 *    discovers by rereading the bitstream, and our label does not save it. */
	if (c->next_key && !key) {
		registro_dice(LOG_ENCODING,
		              "⛔ a KEY had been requested and the encoder produced a "
		              "delta: not sending (RCP.md §5.2)");
		c->packet_in_hand = false;
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
		uint64_t t_now = now_us();
		if (!c->bandwidth_t0_us)
			c->bandwidth_t0_us = t_now;
		c->bandwidth_byte += (uint64_t) c->output_byte;
		c->bandwidth_frames++;
		if ((uint32_t) c->output_byte > c->bandwidth_max)
			c->bandwidth_max = (uint32_t) c->output_byte;
		uint64_t duration = t_now - c->bandwidth_t0_us;
		if (duration >= BANDWIDTH_WINDOW_US) {
			uint64_t kbit = c->bandwidth_byte * 8u * 1000u / duration; /* µs ⇒ kbit/s */
			char quota[128];
			if (cap_floor_mbit)
				snprintf(quota, sizeof(quota),
				         " · CEILING ON: wire %" PRId64 " kbit/s, it uses %u %% of it",
				         wire_cap() / 1000,
				         (unsigned) (kbit * 100u / (uint64_t) (wire_cap() / 1000)));
			else
				snprintf(quota, sizeof(quota),
				         " · ceiling OFF (QP %d fixed): ⛔ nobody tells it no",
				         c->current_quality);
			registro_dice(LOG_ENCODING,
			              "video bandwidth: %" PRIu64 " kbit/s over %" PRIu64 " ms — %u "
			              "frames (%" PRIu64 " bytes, the biggest %u), mode %s%s.  "
			              "⭐ It is the THIRD witness: what the driver REALLY did, "
			              "not what it said",
			              kbit, duration / 1000u, c->bandwidth_frames, c->bandwidth_byte,
			              c->bandwidth_max, wanted_bitrate_mode().name, quota);
			c->bandwidth_t0_us = t_now;
			c->bandwidth_byte = 0;
			c->bandwidth_frames = 0;
			c->bandwidth_max = 0;
		}
	}

	if (!c->first_encode_done) {
		c->first_encode_done = true;
		registro_dice(LOG_ENCODING,
		              "first frame: %s · %zu bytes · key %s · stream: %s, %d bits, "
		              "level %d, %ux%u · conversion %" PRIu64 " µs, upload "
		              "%" PRIu64 " µs, encoding %" PRIu64 " µs · %s",
		              c->conf.codec_string[0] ? c->conf.codec_string : "(not read)",
		              c->output_byte, key ? "yes" : "no",
		              c->conf.read_from_stream ? "read" : "⛔ NOT read",
		              c->conf.stream_depth, c->conf.stream_level,
		              c->conf.stream_width, c->conf.stream_height,
		              report->us_conversione, report->upload_us, report->us_codifica,
		              c->name);
		if (c->conf.promotion_8_to_10)
			registro_dice(LOG_ENCODING,
			              "⚠ and the 10 bits are EIGHT PROMOTED: GNOME's capture delivers "
			              "BGRx [M], and the stream label will say «Main 10» anyway");
	}

	/* ═══════════════════════════════════════════════════════════════════════
	 * ⛔⛔ THIS POINTER SITS **INSIDE** THE PACKET, AND `close_context()`
	 *      **FREES** THE ENCODER'S BYTES (`vadirect_close`).
	 *
	 * ⚠ It is the third time in one day that someone trips over it, so the proof
	 *   is written here instead of being redone from memory.  From here until
	 *   `codificatore_rilascia()` the caller holds `report->data`; in the same
	 *   interval `close_context()` **must not** run.  The places it can
	 *   start from are SEVEN, and each has its guard:
	 *
	 *     `:2125` `:2140` `:2149` `:2265` `:2272`  the error exits of
	 *         `open_context()`.  ⛔ Not reachable with a packet in hand
	 *         by construction: `open_context()` is called only **right after**
	 *         a `close_context()` — or on a newly born encoder — and at
	 *         `:2125`-`:2149` the packet has not even been allocated (it is at
	 *         `:2270`, at the bottom).
	 *     `:2681` `codificatore_libera()` — guard at `:2668`: it does the `unref`
	 *         first.  ⚠ After `free_fn()` the caller's `report` is worth nothing
	 *         anyway, and that is the contract of `encoder.h:439`.
	 *     `:2760` `codificatore_ridimensiona()` — guard at `:2745`, added on
	 *         23 Aug 2026: it was **the only one without**, and it refuses instead of
	 *         freeing from under the reader's feet.
	 *     `:3445` `lower_quality()` — called from one place only, the re-encoding
	 *         loop above, and there `packet_in_hand = false` sits
	 *         **before** the descent, and
	 *         `report->data` has not been written yet.
	 *     `:3536` `:3546` `raise_quality()` — guard at `:3511`, and it is written
	 *         in its box: it is precisely the reason the climb lives
	 *         **at the entry** of the next frame and not after delivery.
	 *     `:3626` the reopening after the drain — guard at `:3617`, which refuses
	 *         if the previous frame was not released.
	 *
	 * ⇒ It is not reachable, and now it is not **by construction** instead of
	 *   by luck.  ⚠ Whoever adds an eighth `close_context()` must also add
	 *   the line above, or they take the proof away from everyone.
	 * ═══════════════════════════════════════════════════════════════════════ */
	report->data = c->output;
	report->byte = c->output_byte;
	report->key = key;
	c->next_key = false;
	c->nr++;
	return true;
}

bool codificatore_comprimi(Encoder *c, const uint8_t *pixel, uint32_t step,
                           EncoderFrame *report)
{
	if (!pixel) {
		registro_dice(LOG_ENCODING, "⛔ no pixels to compress");
		return false;
	}
	return compress_common(c, pixel, step, NULL, report);
}

bool codificatore_comprimi_scheda(Encoder *c, const EncoderSurface *surface,
                                  EncoderFrame *report)
{
	if (!c || !surface)
		return false;
	/* ⛔ Without the card open this route does not exist (phase 19: an
	 *    encoder that was born is always on the card; the guard stays so as not to let
	 *    a half-born encoder through silently). */
	if (!c->hardware) {
		registro_dice(LOG_ENCODING,
		              "⛔⛔ ZERO COPY requested on «%s», which has no card open: "
		              "nothing is imported",
		              c->component_name);
		return false;
	}
	if (surface->fd < 0 || !surface->width || !surface->height
	    || !surface->stride || !surface->formato_drm) {
		registro_dice(LOG_ENCODING,
		              "⛔ incomplete descriptor (fd %d, %ux%u, stride %u, format 0x%08x): "
		              "no half imports",
		              surface->fd, surface->width, surface->height,
		              surface->stride, surface->formato_drm);
		return false;
	}
	/* ⛔⛔ AND THE STRIDE MUST BE IMPORTABLE — see the box in
	 *      `encoder.h`.  ⚠ The caller already knows and chooses the route
	 *      beforehand: this is the LAST line of defence, and it is needed because the defect
	 *      it stops **gives no error at all** — it gives a slanted picture that
	 *      passes every check on the milliseconds and every check on the colour. */
	if (!encoder_stride_importable(surface->stride)) {
		registro_dice(LOG_ENCODING,
		              "⛔⛔ stride %u: it is NOT a multiple of %u, and the driver importing the "
		              "DMA-BUF would read the rows at a stride of its own — `[M]` 22 Aug 2026 "
		              "the mark can no longer be read on 0 frames out of 869, while the colour "
		              "averages stay identical within 0.17 levels out of 255.  ⇒ NOT "
		              "compressing: better the copy than a silently wrong picture",
		              surface->stride, CARD_ALIGNMENT);
		return false;
	}
	/* ⛔ And the descriptor's size must be the one the encoder
	 *    is open for: `compress_common` does not look at it — it receives a surface and
	 *    trusts it.  ⚠ Feeding an encoder opened at 1920 with a 2560
	 *    surface does not protest: it crops or pads, and the defect shows only
	 *    in the picture (it is the same note as in `codificatore_ridimensiona`). */
	if (surface->width != c->request.width
	    || surface->height != c->request.height) {
		registro_dice(LOG_ENCODING,
		              "⛔ the surface is %ux%u and the encoder is open at %ux%u: we do "
		              "not compress a picture that is not its own",
		              surface->width, surface->height, c->request.width,
		              c->request.height);
		return false;
	}
	return compress_common(c, NULL, 0, surface, report);
}

bool codificatore_in_hardware(const Encoder *c)
{
	return c ? c->hardware : false;
}

uint32_t encoder_card_alignment(void)
{
	return CARD_ALIGNMENT;
}

bool encoder_stride_importable(uint32_t stride)
{
	return stride != 0 && (stride % CARD_ALIGNMENT) == 0;
}

void codificatore_rilascia(Encoder *c)
{
	if (!c || !c->packet_in_hand)
		return;
	/* ⭐ Phase 18: the bytes are ours (`c->output`) and stay valid; the
	 *    release only says that the caller has finished reading them. */
	c->packet_in_hand = false;
}
