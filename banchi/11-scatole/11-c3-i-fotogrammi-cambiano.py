#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c3 — ⭐⭐ «THE FRAMES ARRIVE, AND THE SCENE CHANGES»
===========================================================================

    python3 11-c3-i-fotogrammi-cambiano.py --port 8511
    python3 11-c3-i-fotogrammi-cambiano.py --port 8511 --still-scene
    python3 11-c3-i-fotogrammi-cambiano.py --port 8511 --repeated-frame
    python3 11-c3-i-fotogrammi-cambiano.py --port 8511 --stopped-encoder
    python3 11-c3-i-fotogrammi-cambiano.py --certify

It is line **C3** of `fasi/11-la-rete-di-sicurezza.md` §4.1, to the letter:

    what must be true         : the frames arrive, and the scene CHANGES
    where it starts from      : NEW session, ⭐ **declared scene in
                                motion**
    what it looks at          : ⭐ **anti-death canary** — frames > 0 ·
                                **not collapsed** with respect to a rough
                                reference · ⛔ **consecutive frames are
                                different from each other**
    how I know it can say red : the encoder is stopped ⇒ red · ⭐ the
                                same frame is sent repeated ⇒ red
                                (frozen image).  ⚠ And *«still scene»*
                                must **not** give red

---------------------------------------------------------------------------
⛔⛔ THE MOST IMPORTANT THING IN THIS FILE, and it must be read before the numbers
---------------------------------------------------------------------------

⭐⭐ **«Consecutive frames are different» is NOT a property of the
     product: it is a property of the PAIR product + scene.**

`[M]` `fasi/09-la-qualita-e-la-degradazione.md` §3.1, on the real iron, 30 seconds
per scene:

    | scene   | frames/s     | empty waits/s    |
    |---------|--------------|------------------|
    | still   | ⛔ **0.03**   | **123**          |
    | bar     | **39.67**    | 80               |
    | full    | **39.00**    | 81               |

⇒ ⛔ **On a still scene, in 30 seconds, ONE single frame comes out — the opening
   keyframe — and then nothing more.**  And the product declares it by itself,
   `[R]` `src/figlio.c:3373`:

     *«on a STILL desktop Mutter delivers nothing … Zero frames on a
       still scene is a RESULT, not a defect.»*

⇒ ⭐ That is why this mesh **puts the scene in motion itself**, **declares** it
  (`11-c3-scena.html`), and **verifies that it is on the screen** before demanding
  that the frames change.  ⛔ A mesh that demanded «the frames
  change» on any desktop would be a generator of false reds — and a
  false red, in a safety net, always ends the same way: the
  net gets switched off by whoever works (§1.3 of the phase document).

⚠ **AND THIS IS THE MEANING OF `--still-scene`**: it is the **negative control**, and
  it is the other half of `LEZIONI.md` §1.49 (*the fault is removed and green is
  demanded*).  ⛔ With the still scene the JUDGEMENT ON THE FRAMES cannot give
  red: it says «I do not know» and says why — a frozen image and a desktop
  that has nothing to show have **the very same look**, and whoever cannot
  tell them apart must not judge.

  ⛔⛔ **BUT THE MESH'S OUTCOME IS NOT «3 anyway», and it is a correction.**
  The first draft always exited 3: ⚠ that way it did not distinguish *«the bench ran
  and the desktop was really still»* from *«nothing started»* — a broken
  container gave the same exit code as the successful control, and five minutes
  of session produced a bit that could not vary (§1.44).
  ⇒ ⭐ Now `--still-scene` **asserts**, and demands three things together:

      · the stage was born        (⇒ the round really happened)
      · the client was admitted
      · and the verdict is «I do not know» **for the right reason** (reason
        `scena-ferma`), not for another one

    ⇒ `0` the negative control HOLDS · `1` ⛔ on a still scene the mesh gave
      a verdict, i.e. it is broken · `3` the round did not happen and I checked
      nothing.
  ⭐ And that round leaves the number with which `--minimum-rate` is calibrated: how many
    frames a still desktop really delivers **inside the box**.

---------------------------------------------------------------------------
⭐ THE THREE CHECKS, and they do not have the same weight
---------------------------------------------------------------------------

  1. **frames > 0** — the poorest canary.  ⛔ It counts only because the
     scene is in motion (see above): on a still scene zero is right.

  2. **the rate has not collapsed** with respect to a **rough reference**.
     ⛔⛔ AND HERE THE LIMIT MUST BE DECLARED, or the number deceives:
       · the reference is `[M]` **39.0 frames/s** — phase 9 §3.1, ⚠ **on the
         real iron, not in the box**, and with the card all to itself;
       · the rate this mesh computes is **GROSS**, and it is worth saying
         how: in the **numerator** there are ALL the frames of the stream —
         those of the birth of the desktop included, because the client writes
         a single file and from an H.264 stream without timestamps one cannot cut a
         piece — while in the **denominator** there is **only the window in which the
         scene was moving**.  ⇒ The rate is **overestimated**, i.e. ⛔ **this
         check is OPTIMISTIC**: it can let a collapse through, it cannot
         invent one.  ⚠ It is the right direction in which to err (a false
         red switches off the net, §1.3), ⛔ but it is also the reason why the
         rate is not what decides.
       · ⚠⚠ And **by how much** it overestimates I do not know, and it must be said instead of
         inventing a limit.  Outside the window the desktop is still
         (`[M]` 0.03 frames/s, phase 9 §3.1) ⛔ **but the application is being
         born inside it**, and a window that opens draws plenty.  ⇒ The
         extra term is «the frames the compositor drew
         while the scene was starting», which nobody has measured: `[?]`.
         ⭐ The mesh always prints the frames, the seconds and the rate: they are the
           three numbers with which that `[?]` is closed, and they must be looked at at the first
           green round.
       · ⇒ The `--minimum-rate` threshold is **wide on purpose**: it separates *«a trickle
         arrives»* from *«nothing arrives»*, ⛔ **it does not judge smoothness**.
         Smoothness is the user's judgement (I8) and §6 puts it outside the
         net.  ⚠ `[?]` **To be recalibrated in the box**, measuring the real rate.

  3. ⭐⭐ **CONSECUTIVE FRAMES ARE DIFFERENT FROM EACH OTHER** — and it is the
     check that decides.  ⛔ It does not have the defect of the rate: it looks **only at the
     last frames**, which by construction sit inside the window in which
     the scene was moving.
     ⇒ It is the only one of the three that catches the **frozen image**: the mark is there,
       the screen is full, the rate is high, ⛔ and nothing updates
       (§4.3, the third row of the table «the mark alone is not enough»).

---------------------------------------------------------------------------
⛔ HOW I KNOW IT CAN SAY RED — two grafted faults, and they are of two natures
---------------------------------------------------------------------------

  `--repeated-frame`   ⭐ THE FROZEN IMAGE FAULT.  The REAL grab is
                            taken and **the in-memory copy** of the list of
                            frames is defaced: in place of the sequence
                            N copies of the first one are put.  ⛔ The stream on
                            disk is not touched — it is the same shape C9 uses
                            (`--remove-name`), and the healthy control and the fault
                            run on the **same data**.  ⇒ A single tenant.
                            ⛔⛔ AND HERE ONE THING MUST BE SAID that a reviewer
                            found and was right about: **the defacement, on its own, cannot
                            fail** — if the healthy one is green, repeating the
                            same frame necessarily gives zero different
                            pairs.  It is arithmetic, and it is already proved by
                            `--certify` in three tenths of a second.  ⇒ A round
                            on the real thing that asserted only that would spend a
                            session for a bit already known: `LEZIONI.md` §1.44
                            disguised as an acceptance test.
                            ⭐ That is why that round demands **one more thing that
                            can really fail**: that the **weakest** consecutive
                            pair of the healthy round sits at least
                            `THRESHOLD_MARGIN` times above the threshold.  ⇒ It is a
                            measurement of the WORLD — how lively the real scene is
                            after the encoding — and if one day it dropped, it would
                            be seen **before** the mesh starts giving
                            false reds.  ⚠ It is what C5 does with the margin
                            of the RMS.

  `--stopped-encoder`    ⛔ THE REAL FAULT, on the product.  ⭐⭐ **As soon as the
                            scene has been seen moving** — not before — **SIGSTOP**
                            is sent to the tenant's process that
                            encodes and delivers.
                            ⛔⛔ AND THAT «NOT BEFORE» IS A CURE OF 27 AUGUST
                            2026, not a detail.  Until that day
                            the graft sat **before** the scene
                            came on: the encoder died on an empty
                            desktop, the declared scene never appeared, and the
                            mesh said — ⭐ honestly — *«the scene I
                            declared is NOT on the screen»* ⇒ outcome **3**.
                            ⇒ It was not a product defect and it was not a
                            red: it was ⛔ **an acceptance test that did not test**,
                            because the fault was grafted at the wrong
                            moment of the story.  ⭐ The guardian was not
                            touched — it is the one that showed the defect
                            instead of passing it off as green: the graft
                            was moved.
                            ⭐ «It was seen moving» is a MEASUREMENT and not
                            trust: we look at the **work of the encoder**,
                            i.e. of the process that is about to be stopped.  ⛔ Not
                            the bytes on disk: the frames file the client
                            writes **only at the end** (`[R]`
                            `01-b3-cliente.py:1416`).  ⚠ And not the work of the
                            client: `[M]` 27 Aug 2026, with the desktop in
                            motion it burns 0.06 CPU/s, too little to
                            tell it from a still client without inventing
                            a thin threshold.  ⚠ And the name must be stated right:
                            **it does not stop «the encoder alone»**, it stops
                            the process that contains it — it is as much as can be
                            done without touching the product, and the difference is
                            declared instead of hidden.
                            ⇒ Two tenants: one healthy (control) and one
                              faulted.

⛔⛔ AND EVERY FAULT CARRIES ITS OWN HEALTHY CONTROL — `LEZIONI.md` §1.52:
   *the colour of the verdict is not enough; a mesh must distinguish «the fault
   bit» from «it was already red on its own»*.  ⇒ **Three** things are demanded:

     · the healthy control is GREEN     (or the comparison is worth nothing)
     · the faulted one is RED
     · ⭐ the **difference** is measurable:
         `--repeated-frame`  the different pairs collapse to **zero**
         `--stopped-encoder`   ⭐⭐ the **work of the client inside the
                                  window** drops below a **SHARE** of
                                  the healthy one (`FAULT_QUOTA`, a tenth).
                                  ⚠ A share and not an absolute difference:
                                  §1.45, an absolute number is a number taken
                                  from one condition.
                                  ⛔⛔ AND SINCE 27 AUGUST 2026 THE MEASURE IS
                                  NO LONGER THE RATE: the rate is **gross** (in the
                                  numerator there are also the frames born
                                  before the window opened), and now
                                  that the graft has been moved to the end those
                                  frames arrive **even with the fault**.
                                  ⇒ On a dirty number one cannot demand
                                  the tenth: it is demanded where the measure is
                                  clean — the work of the client, which has
                                  numerator and denominator both inside
                                  the window.  ⚠ The gross rate is looked at
                                  anyway, with a share of its own, declared
                                  (`GROSS_QUOTA`).

⚠ And each fault also demands its own **signature**, or it is not that fault:
   with `--stopped-encoder` at least one process of the tenant must
   really be in state **T** (stopped).  ⛔ If it is not, the injection touched
   nothing and the red — if there is one — belongs to someone else.

⭐⭐ AND `--stopped-encoder` DEMANDS ONE MORE THING, since 27 August 2026:
   that the fault fell **at the right moment of the story**.  Three facts, and
   each one is measured and can be missing:
     · the frames had been seen ARRIVING before the graft;
     · the LAST frames delivered were **different from each other** — i.e. the
       scene was moving at the instant the encoder died;
     · the window was long enough that the frames born before
       the graft were not enough on their own to make the stream look alive
       (`enough_window`, and the count is redone **with the real numbers of the round**).
   ⛔ If one is missing, the outcome is **3**: saying «the fault was not seen»
      would be accusing the net for an acceptance test that did not run.

⛔⛔ And if the signature is missing, the outcome is **3**, not a red: a mesh that could not
   graft the fault has neither seen nor missed anything, and writing
   *«the fault was NOT seen»* would be **an accusation against a test that did not
   run**.  ⇒ It is the same cure `11-gancio.sh` gave itself on 27 August
   2026 for its own `3`.

---------------------------------------------------------------------------
⛔ THE CEILINGS — they are arguments, and they must be RECALIBRATED ON THE REAL THING
---------------------------------------------------------------------------

`LEZIONI.md` §1.45: *every wait has its own name and its own value*.  ⛔ None
of the numbers below was measured by whoever wrote this file.

  `--wait-stage 60`    how long to wait for the compositor to announce a
                         `wl_output`.  `[M]` (C1's measurement, 27 August 2026,
                         **not mine**) in the GNOME box: 98.0 · 101.0 · 95.5 s
                         ⇒ maximum 101.0.  ⛔ And that delay is the **box's**
                         (`polkit` that does not start, `Contenitore.gnome` §6-bis),
                         not the product's: with that cured the stage is born in ~2 s
                         as in the other three boxes ⇒ **put back to ~20 s**.
                         ⚠ The mesh always prints how long it really took.
  `--wait-scene 30`    how long the scene is given to be on the screen.
                         `[?]` — the first start of the browser in a cold
                         box exceeds 25 s (`[M]` C8, 26 Aug 2026).
  `--window 45`        how many seconds the scene in motion is watched.
  `--minimum-rate 4.0`   `[?]` ⇒ ~10 % of the rough reference.  See above:
                         wide on purpose, and it does not judge smoothness.

---------------------------------------------------------------------------
⛔ WHAT THIS MESH DOES **NOT** LOOK AT
---------------------------------------------------------------------------

  · ⛔ **It does not look at smoothness**, nor latency, nor the quality
    of the image: they are quantities of phase 9, and §6 keeps them out of the net.
  · ⛔ **It does not prove that the scene was really moving.**  It measures that the
    program moving it was **alive** from start to end and that one of the two
    declared colours was on the screen.  ⚠ If the scene had frozen by
    itself with a colour in view, C3 would say red to the product for something of the
    browser.  ⇒ `[?]` **to be calibrated on the real thing**: the first time this mesh
    gives red, look at the PNG it leaves in `--workdir` before believing it.
  · ⚠ **It is not blind to the program**: like C2, today it uses `firefox-esr`, the only
    program in the box that can paint a scene we decide.
    ⇒ `--app` and `--args` exist to move it elsewhere.
  · ⛔ **It does not look at audio** (that is C5) nor at input (that is C4).

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ I looked: the frames arrive and the scene CHANGES
     (with the grafted fault: ⭐ **the fault was seen**)
     (with `--still-scene`: ⭐ **the negative control holds**)
  1  I looked: they do not arrive, or they collapsed, or the image is FROZEN
  3  ⛔ I could not look — the stage was not born, the declared scene was not
     on the screen, the client was not admitted, the decoder
     left a truncated list.  ⛔ And it is NOT a red.
     ⚠ With the grafted fault, **3** also means *«the injection did not
     take»*: neither a certification nor an accusation against the net
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import glob
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE YARDSTICK, DECLARED HERE AND PRINTED IN EVERY OUTCOME
# ═══════════════════════════════════════════════════════════════════════════

# ⭐ The two colours of the declared scene — ⛔ **the same as `11-c3-scena.html`**.
#    If someone changes one there and not here, this mesh will say «the scene
#    I declared is not on the screen» ⇒ **3**, not a red for the product.
SCENE_A = (0x00, 0x00, 0xFF)      # blue
SCENE_B = (0xFF, 0xFF, 0x00)      # yellow
# ⛔ The tolerance per channel: same quantity and same value as C8 — the
#    deviation of a declared colour after the same path (compositor →
#    capture → H.264 4:2:0 → client).  ⚠ It is not a borrowed ceiling
#    (`LEZIONI.md` §1.45): it is the same number for the same thing.
# ⛔⛔ BUT IT IS NOT CALIBRATED, and saying so would be §1.50.  `--certify` crosses it **at the
#     edge** — ±48 must still be the scene, ±49 not — on **synthetic**
#     images, which have never seen either the 4:2:0 encoding or a
#     colour profile.  ⇒ It tests that the comparison falls where it says it falls,
#     not that 48 is enough.
# ⚠⚠ And there is one more reason to distrust it here: C8 is calibrated on **magenta**,
#    C3 asks for **pure blue** `#0000FF`, which has luma 0.07 and is the worst case
#    of chroma subsampling.  ⇒ `[?]`, and it is calibrated by looking at the fraction
#    the mesh prints at the first green round.
TOLERANCE = 48
# ⛔ How much of the screen must be one of the two colours for us to say «the
#    declared scene is the one I am looking at».  ⚠ The black band covers 20 %,
#    plus the plate: 0.40 is prudent on the low side on purpose.  `[?]`
SCENE_FRACTION = 0.40

# ⭐⭐ THE ROUGH REFERENCE — `[M]` phase 9 §3.1, ⛔ **on the real iron, not in the
#     box**: 39.67 and 39.00 frames/s on two scenes in motion, against
#     **0.03** on a still scene.  ⇒ The value used is the lower of the two.
REFERENCE_FPS = 39.0
# ⛔ Below how many frames per second we say «collapsed».  `[?]` ~10 % of the
#    reference: wide on purpose (see the top), and to be recalibrated in the box.
MINIMUM_RATE = 4.0

# ⛔ When two frames are DIFFERENT — two numbers, and both are needed.
#    · below `NOISE_THRESHOLD` levels on a channel, a pixel «did not change»:
#      it is the quantisation noise of the encoding, not movement.  `[?]`
#    · and the changed pixels must be at least `PAIR_THRESHOLD` of the image,
#      or a blinking cursor would be enough to declare a dead scene alive.
NOISE_THRESHOLD = 12
PAIR_THRESHOLD = 0.01
# ⛔ How many pairs must be different for the scene to «change».  ⚠ The declared
#    scene is made to make them ALL differ (the band moves at every
#    frame): 0.50 leaves half a margin for the cadence of the capture.  `[?]`
PAIR_FRACTION = 0.50
# How many pairs are looked at, at the end of the grab.
EXAMINED_PAIRS = 60

# ⭐⭐ With the grafted fault: how much the CLEAN measure must COLLAPSE for us to
#   be able to say «the fault bit» instead of «the verdict changed».
#   `LEZIONI.md` §1.52.
# ⛔⛔ AND SINCE 27 AUGUST 2026 THE CLEAN MEASURE IS NO LONGER THE RATE, but **the work
#     of the client inside the window** — see `GROSS_QUOTA` below and
#     `enough_window`.  The rate is gross, i.e. it carries inside it the
#     frames born before the graft; the work of the client has numerator and
#     denominator both inside the window, ⇒ it is the only one of the two on which one
#     can demand a tenth without cheating.
# ⚠⚠ And it is a SHARE of the healthy rate, not a difference in frames/s — and the
#    reason is §1.45: an absolute difference («at least 10/s fewer») is a
#    number taken from one condition.  ⛔ In the box the card is shared with
#    three other boxes and the healthy rate could be 12/s instead of 39: then
#    a margin of 10/s would start saying «the fault did not bite» on a
#    fault that stopped it completely.  ⇒ A share carries its own scale.
# ⭐ And it is not a predicate that cannot fail: the healthy rate must already be
#   above `--minimum-rate` (4.0/s) to be green, ⇒ with the fault one demands
#   less than 0.4/s, which is the rate of a still desktop ([M] 0.03/s, phase 9 §3.1).
FAULT_QUOTA = 0.10

MIN_OUTPUTS = 1
OUTPUT_SIGNATURE = re.compile(r"interface:\s*'wl_output'")

# ⛔⛔ AND THE ADMISSION SIGNATURE IS A WHOLE LINE, NOT A WORD.
#    `[R]` `01-b3-cliente.py:1615` writes «   ADMITTED after 1023 ms» when it goes
#    well, and «FAREWELL instead of ADMITTED: …» / «expected ADMITTED, arrived …»
#    when it goes badly — ⛔ all three on **stdout** (`:2560`) ⇒ `"ADMITTED" in
#    text` would be **true in all three cases**: a predicate that cannot
#    say no (`LEZIONI.md` §1.44), precisely in the cases it exists to catch.
# ⭐⭐ Since 27 August 2026 the rule lives in `11-c1…py` and it lives there **only
#     once**, for all nine meshes (§1.47): see `was_admitted()`.

# ⭐ How WIDE the weakest pair of the healthy round must sit with respect to the
#   threshold, for us to be able to say the scene is lively enough to prove
#   something.  ⛔ It is the number that makes the round with the «repeated frame»
#   fault NOT EMPTY (see the top): without it, that round asserts only things
#   already certified.  ⚠ `[?]` — 2× is prudent, and it is calibrated by looking at the
#   `margin` the mesh prints at every round.
THRESHOLD_MARGIN = 2.0

# ⛔ If the decoder pulls out many fewer than the client
#    declares, the stream was truncated and the count is not the
#    product's: it is «I could not look».  `[?]`
QUOTA_EXTRACTS = 0.50

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ «ARE THE FRAMES ARRIVING NOW?» — the LIVE signal, and it serves to
#    decide **when** to graft the fault (27 August 2026, see the top).
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ The stream on disk does not help: `[R]` `01-b3-cliente.py:1416` — the client
#    keeps the frames in memory and writes the file **only once, at the
#    end**.  ⇒ During the round the file does not exist, and one cannot look at
#    how many have arrived.
# ⭐ What instead can be seen live is the WORK OF THE ENCODER — i.e. of the
#   process that is about to be stopped: `ps -o times=`.  Compressing 1920x1080
#   costs; ⛔ a still desktop costs nothing (`[M]` phase 9 §3.1: 0.03
#   frames/s).
# ⛔⛔ AND THE CLIENT IS NOT LOOKED AT, and the reason is a MEASUREMENT and not a taste:
#     `[M]` 27 August 2026, gnome box, with the desktop in motion the client
#     burns **0.06 CPU/s**.  ⚠ Too little: to tell it from a client
#     attached to a still desktop a thin threshold would be needed, i.e. a
#     number that one day says yes and another day no.
# ⚠ `[?]` — 0.10 seconds of CPU per second of clock is not calibrated: it is
#   chosen well below what one expects from a 1080p compression, and the
#   mesh **always** prints the real value, so it is calibrated by looking.
CPU_THRESHOLD = 0.10
# ⭐ Every how many seconds the client's work is looked at.  ⛔ It is short on purpose:
#   between the instant the scene starts painting and the graft lie
#   **all** the frames that later dirty the gross rate (see
#   `enough_window`), ⇒ every extra second here is one more frame
#   that arrives anyway with the fault.
CPU_STEP = 2.0

# ⛔ And the GROSS rate has a share **of its own, wider**, and the reason must be said
#    instead of hidden: its numerator also contains the frames born
#    BEFORE the window, and with the grafted fault those all remain.  ⇒ On
#    a dirty number one cannot demand the same tenth one demands
#    on a clean one: it would be a threshold that passes or does not pass depending on
#    how quick the scene was to be born.  `[?]`
# ⭐ The tenth is demanded where the measure is clean (`QUOTA_LAVORO`); here it is
#   demanded only that the gross rate dropped **a lot**, and the count of how much
#   could be expected is done by `enough_window`.
GROSS_QUOTA = 0.35


def was_admitted(queue):
    """⭐ `True` admitted · `False` **TURNED AWAY** · `None` said nothing.

    ⛔⛔ AND SINCE 27 AUGUST 2026 THE PREDICATE IS NO LONGER HERE: it lives in C1, and it lives there
        **only once** for all nine meshes (§1.47).  ⚠ This mesh
        and C3 had it right but in their own copy; C1, C5, C6, C7 and C9 had
        it WRONG — five times the same line, five times the same
        defect.  ⇒ Two right copies are still two places to
        diverge from the day the client changes the sentence.
    ⛔ `False` is not a product red: a client turned away is a client
       turned away, and the caller exits **3**.
    """
    return c1_home().was_admitted(queue)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE JUDGES ARE IMPORTED, NOT REWRITTEN
#
# ⛔ Two judges that can diverge silently are worse than one
#    (`banchi/10-f1-testimone.py`).  Here two are imported:
#      `10-f1-testimone.py`  `judge()`, to say whether an image is black
#      `11-c8-…py`           `color_fraction()`, already certified, and it takes
#                            colour and tolerance as ARGUMENTS ⇒ it is used with
#                            C3's numbers without inheriting C8's
# ⭐ The third judge — «are two frames different?» — does not exist anywhere
#   else, so it is born here **and it is certified here**.
# ═══════════════════════════════════════════════════════════════════════════
def _load(file_name, jobs):
    for base in (HERE, os.path.dirname(HERE)):
        path = os.path.join(base, file_name)
        if not os.path.exists(path):
            continue
        spec = importlib.util.spec_from_file_location(
            "importato_" + re.sub(r"\W", "_", file_name), path)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None, path
        for duty in jobs:
            if not callable(getattr(m, duty, None)):
                return None, path
        return m, path
    return None, ""


def desktop_judge():
    return _load("10-f1-testimone.py", ("judge",))


def color_reader():
    return _load("11-c8-il-secondo-apre-il-browser.py", ("color_fraction",))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ THE SHARED PROVISIONING — `/tmp/mozilla`, and it lives in ONE PLACE ONLY
#
# `[M]` 27 August 2026, round `--family all` on all four boxes,
#   binary `aa950804fed7`: C3 ⛔ **3** — «the scene I declared is NOT
#   on the screen (0.0%)».  ⚠ And the judged image said something else entirely: the
#   GNOME session was **alive and painted**, ⛔ but Firefox was stuck on the
#   **profile chooser window**.
#
# ⇒ THE CAUSE: `/home/c3u1/.cache/mozilla` -> `/tmp/mozilla`, which had stayed with
#   «c8u1» with mode 0700 — C8 and C8b, in `family all`, run BEFORE me and
#   ⛔ do not undo the skeleton they set up.  ⛔ Neither of the two meshes
#   is wrong on its own: it is the ORDER that breaks them.
#
# ⛔⛔ AND THE CURE CANNOT LIVE IN WHOEVER SWITCHES ME ON: for a day it was in
#     `11-accendi.sh`, ⚠ but a mesh that must be «prepared from outside» is, when launched
#     by hand or by another hook, a mesh that gives a **false red**.
#
# ⭐⭐ AND IT IS NOT A CLEANUP: it is the cure of `src/provisiona.sh` — a REAL
#     `~/.cache` for the tenant I create.  ⛔ Deleting the `/tmp/mozilla` of
#     another mesh would be damage, and in parallel (C14) it would make it fall.
#
# ⛔ The code lives in C2 and ⛔ no copy of it is made here: the same rule in three
#    files is three places to diverge from, and it is the error this cure repairs.
# ⚠ It lives in C2 and not in C8 because C8 cannot be modified today; ⭐ the day it
#   can, it moves next to `apply_fix`, and this line changes by itself.
# ═══════════════════════════════════════════════════════════════════════════
_PROVISIONING_JOBS = ("cura_della_provvista", "sgombra_il_mio_rimasuglio",
                       "certifica_la_provvista")
_PROVISIONING = None


def provisioning_home():
    global _PROVISIONING
    if _PROVISIONING is None:
        _PROVISIONING, _ = _load("11-c2-una-finestra-si-apre.py",
                                _PROVISIONING_JOBS)
    return _PROVISIONING


def provisioning_fix(chi):
    """⭐⭐ (done, why) — and ⛔ if it does not hold it is NOT a red: it is a **3**."""
    home = provisioning_home()
    if home is None:
        return False, ("I cannot find `11-c2-una-finestra-si-apre.py` next to me: "
                       "the provisioning cure comes from there, and ⛔ no "
                       "copy of it is made here (§1.47)")
    return home.provisioning_fix(chi)


def clear_out_my_leftover(my_base):
    """Removes `/tmp/mozilla` ⛔ only if it was left to one of MY tenants."""
    home = provisioning_home()
    if home is None:
        return "⚠ I cannot find C2: I did not even look at /tmp/mozilla"
    return home.clear_out_my_leftover(my_base)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ C1 IS THE HOME OF THE TWO STEPS COMMON TO ALL NINE MESHES — §1.47
#
# ⛔ It is not convenience: it is that a line repeated in nine files is **nine places
#    to diverge from**, and they had already diverged.  From `11-c1-nasce-e-si-vede.py`
#    come:
#
#   · `was_admitted(queue)`   — «was the client ADMITTED?», which ⛔ is not
#        the word inside a text: the client prints it also in the TWO refusal
#        messages, and on stdout (`01-b3-cliente.py:1315`, `:1322`, `:2560`).
#   · `ensure_groups(chi)` — the groups of the `/dev/dri` nodes, ⛔ without
#        which `[M]` the session is born BLIND (0 of 4, zero frames,
#        `fasi/10-…` §7.4) and this mesh would measure the darkness.
#
# ⛔ If C1 does not load we exit **3** and say so: ⛔ we do not silently fall back
#    on a poorer judgement.
# ═══════════════════════════════════════════════════════════════════════════
_JOBS_C1 = ("was_admitted", "certify_admission",
                "ensure_groups", "group_verdict", "certify_groups")
_C1 = None


def c1_home():
    global _C1
    if _C1 is None:
        _C1, _path = _load("11-c1-nasce-e-si-vede.py", _JOBS_C1)
    if _C1 is None:
        print("⛔ I cannot find `11-c1-nasce-e-si-vede.py` next to me, and from there")
        print("   come the admission predicate and the guarantee of the")
        print("   card's groups — which live in one place only (§1.47).")
        print("⇒ I could not look — ⛔ and it is NOT a red (§4.5).")
        sys.exit(3)
    return _C1


def ensure_groups(chi, prefix="   "):
    """⭐⭐ THE CARD'S GROUPS — `(esito, perche)`; `0` = it can be measured.

    ⛔ Until 27 August 2026 this mesh created the tenant with
       `usermod -aG video,render` **and did not read back**: two nailed-down names (which
       belong to ONE distribution) and no verification — E1, «written is not in
       force».  ⭐ The work is done by `attrezzi-gruppi-scheda.sh`, which reads the gids
       from the NODES and reads back comparing the numbers.  ⛔ No copy of it is made here.
    """
    return c1_home().ensure_groups(chi, prefix)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE NEW JUDGE: «are these two frames different?»
# ═══════════════════════════════════════════════════════════════════════════
def changing_pairs(listing, noise_threshold=NOISE_THRESHOLD,
                        pair_threshold=PAIR_THRESHOLD):
    """How many consecutive pairs of frames are DIFFERENT from each other.

    Returns a dictionary, or ⛔ **`None`** if it could not look
    (numpy/Pillow missing, fewer than two readable images).
    ⚠ `None` is not zero: *«I did not look»* and *«I looked and it did not change»*
      are two opposite things, and this project has already paid for confusing them.

    ⛔ The distance is taken **channel by channel** (max norm) and not as a
       sum: a sum would let through a big change on a single channel
       diluted by the other two.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        return None
    if not listing or len(listing) < 2:
        return None

    previous = None
    pairs = diverse = unreadable = 0
    minima = None
    max_dims = None
    for p in listing:
        try:
            img = np.asarray(Image.open(p).convert("RGB")).astype("int16")
        except Exception:
            unreadable += 1
            previous = None      # ⛔ a pair with a hole in the middle is not a pair
            continue
        if img.ndim != 3 or img.size == 0:
            unreadable += 1
            previous = None
            continue
        if previous is not None and previous.shape == img.shape:
            gap = abs(img - previous).max(axis=2)
            amount = float((gap > noise_threshold).mean())
            pairs += 1
            if amount >= pair_threshold:
                diverse += 1
            minima = amount if minima is None else min(minima, amount)
            max_dims = amount if max_dims is None else max(max_dims, amount)
        previous = img

    if pairs == 0:
        return None
    return {"pairs": pairs, "diverse": diverse,
            "frazione": diverse / float(pairs),
            "minima": minima, "max_dims": max_dims,
            "unreadable": unreadable}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE JUDGEMENT — a PURE function, so `--certify` runs it on
#    fake frames without switching anything on.
# ═══════════════════════════════════════════════════════════════════════════
def judge_stream(listing, seconds, scene_stop=False,
                      rate_minimum=MINIMUM_RATE,
                      fraction_pairs=PAIR_FRACTION,
                      examined_pairs=EXAMINED_PAIRS,
                      noise_threshold=NOISE_THRESHOLD,
                      pair_threshold=PAIR_THRESHOLD):
    """Returns a dictionary with `state` among:

        "cambia"     ⭐ the frames arrive and the scene changes  ⇒ green
        "congelata"     they arrive and do NOT change            ⇒ red
        "crollati"      they do not arrive, or they are a trickle ⇒ red
        "non-lo-so"  ⛔ I could not look                          ⇒ neither one
                     nor the other
    """
    # ⭐⭐ AND NEXT TO THE VERDICT THERE IS A **REASON**, which is a fact and not a
    #    sentence.  ⛔ Without it, whoever wants to know *why* «I do not know» would have to
    #    read the text of `why` — i.e. decide on a string, which is the
    #    way a bench starts going wrong silently when someone
    #    fixes a typo.  ⇒ The acceptance test of the negative control rests on
    #    this, not on the words.
    outcome = {"state": "non-lo-so", "reason": "", "why": "",
             "frames": None, "ritmo": None, "coppie": None,
             "diverse": None, "frazione_coppie": None, "minima": None,
             "massima": None, "illeggibili": None}
    if listing is None:
        outcome["reason"] = "niente-elenco"
        outcome["why"] = "I could not extract any frame from the stream"
        return outcome

    n = len(listing)
    outcome["frames"] = n
    rate = (n / float(seconds)) if seconds and seconds > 0 else None
    outcome["rate"] = rate

    # ═══════════════════════════════════════════════════════════════════════
    # ⚠⚠ THE NEGATIVE CONTROL — «still scene» MUST NOT GIVE RED.
    #
    # `[M]` phase 9 §3.1: on a still scene **0.03 frames/s** come out — in 30
    # seconds ONE, the opening keyframe.  `[R]` `src/figlio.c:3373`: *«zero
    # frames on a still scene is a RESULT, not a defect»*.
    # ⇒ ⛔ A frozen image and a desktop that has nothing to show have
    #   the very same look.  Whoever cannot tell them apart does not judge.
    # ⚠ And this branch exits BEFORE every other check on purpose: it is not a
    #   shortcut, it is the declaration that in this condition the mesh does not
    #   have a yardstick.
    # ═══════════════════════════════════════════════════════════════════════
    if scene_stop:
        outcome["reason"] = "scena-ferma"
        outcome["why"] = (
            "the scene was STILL by my choice: %d frames, rate %s. "
            "⛔ On a still scene the product delivers nothing and that is right "
            "([M] phase 9 §3.1: 0.03 frames/s; [R] src/figlio.c:3373) ⇒ "
            "«frozen image» and «nothing to show» here have the same "
            "look, and I do not tell them apart"
            % (n, "unknown" if rate is None else "%.2f/s" % rate))
        return outcome

    # ── 1. the poorest canary ──────────────────────────────────────────────
    if n == 0:
        outcome["state"] = "crollati"
        outcome["reason"] = "zero-fotogrammi"
        outcome["why"] = ("no frame arrived, and the scene was in "
                           "motion: it is the canary dying")
        return outcome

    # ── 2. the rate, against the rough reference ───────────────────────────
    if rate is None:
        outcome["reason"] = "niente-secondi"
        outcome["why"] = "I do not know over how many seconds to count: I do not compute a rate"
        return outcome
    if rate < rate_minimum:
        outcome["state"] = "crollati"
        outcome["reason"] = "ritmo-crollato"
        outcome["why"] = ("%d frames in %.0f s = %.2f/s, below the %.2f/s "
                           "demanded (rough reference [M] %.1f/s, phase 9 §3.1 "
                           "⇒ %.0f%% of the reference)"
                           % (n, seconds, rate, rate_minimum, REFERENCE_FPS,
                              rate / REFERENCE_FPS * 100))
        return outcome

    # ── 3. ⭐ the check that decides: are consecutive ones different? ───────
    queue = listing[-(examined_pairs + 1):]
    m = changing_pairs(queue, noise_threshold, pair_threshold)
    if m is None:
        outcome["reason"] = "niente-coppie"
        outcome["why"] = ("I could not compare the frames with each other "
                           "(fewer than two readable, or numpy/Pillow missing)")
        return outcome
    outcome.update({"coppie": m["coppie"], "diverse": m["diverse"],
                  "frazione_coppie": m["frazione"],
                  "minima": m["minima"], "massima": m["massima"],
                  "illeggibili": m["illeggibili"]})
    if m["frazione"] < fraction_pairs:
        outcome["state"] = "congelata"
        outcome["reason"] = "congelata"
        outcome["why"] = ("⛔ FROZEN IMAGE: only %d pairs out of %d are "
                           "different (%.0f%%, I demand %.0f%%) — the "
                           "frames arrive and they are always the same"
                           % (m["diverse"], m["coppie"], m["frazione"] * 100,
                              fraction_pairs * 100))
        return outcome

    outcome["state"] = "cambia"
    outcome["reason"] = "cambia"
    # ⭐⭐ AND THE MARGIN IS ALWAYS PRINTED, even when it is green — it is the only thing
    #    that warns BEFORE a threshold becomes a false red.  ⚠ It is what
    #    C5 does (`11-c5…py`: *«the mesh always prints the margin»*), and the first
    #    draft of C3 computed the number and threw it away.
    outcome["why"] = ("%d frames in %.0f s = %.2f/s (%.0f%% of the "
                       "rough reference) · %d pairs out of %d are different · "
                       "⭐ the weakest pair changes %.2f%% of the pixels, "
                       "i.e. %.1f times the threshold (%.0f%%)"
                       % (n, seconds, rate, rate / REFERENCE_FPS * 100,
                          m["diverse"], m["coppie"], (m["minima"] or 0) * 100,
                          (m["minima"] or 0) / pair_threshold,
                          pair_threshold * 100))
    return outcome


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE CLIENT'S WORK — PURE functions, so `--certify` crosses them
#    without switching anything on.
# ═══════════════════════════════════════════════════════════════════════════
def cpu_from_line(text, tick=100.0):
    """The CPU seconds burned by a process, from a line of `/proc/<pid>/stat`.

    ⛔⛔ AND THE COMMAND NAME SITS BETWEEN PARENTHESES AND **CAN CONTAIN SPACES** —
        `[R]` `proc(5)`.  A process called «(a b)» would shift
        all the fields by one, and this function would return the wrong number
        without saying so.  ⇒ We cut after the **last** closing parenthesis, and from there
        on the fields are positional for real.
    ⚠ After the `)` the first field is `state`, i.e. the **third** of `proc(5)`:
      `utime` is the 14th ⇒ index 11, `stime` the 15th ⇒ index 12.
    ⛔ Returns **None** if the line cannot be read: «I do not know» is not zero,
       and this mesh has already paid for confusing them.
    """
    if not text or ")" not in text or not tick:
        return None
    fields = text.rsplit(")", 1)[1].split()
    if len(fields) < 13:
        return None
    try:
        return (int(fields[11]) + int(fields[12])) / float(tick)
    except (ValueError, ZeroDivisionError):
        return None


def work_per_second(before, after, seconds):
    """⭐ How much CPU per second between two readings.  ⛔ `None` = I do not know.

    ⚠ And it is never allowed below zero: a process reborn with the
      same pid would give a negative number, which is not a measurement.
    """
    if before is None or after is None or not seconds or seconds <= 0:
        return None
    return max(0.0, (after - before) / float(seconds))


def client_cpu(pid):
    """The CPU seconds of process `pid`, read now.  `None` if unknown."""
    try:
        with open("/proc/%d/stat" % pid, "rb") as f:
            text = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    return cpu_from_line(text, float(os.sysconf("SC_CLK_TCK")))


def sum_work(text, name):
    """⭐ PURE: the CPU seconds of the processes whose command contains `name`.

    Reads the output of `ps -o times=,args=`.
    ⛔ Returns **None** if there is not even one: *«there is no
       encoder»* and *«the encoder is not working»* are two opposite things, and
       this project has already paid for confusing them.
    ⚠ And **only** those with `name` in the command line are summed: counting all the
      tenant's processes would be a predicate one level too high
      (`LEZIONI.md` §1.44), the same defect as `stop_encoder`.

    ⛔⛔ AND «has `name` in the command line» IS NOT ENOUGH — 22 September 2026.
        The scene's browser opens on `file:///opt/remotix/11-c3-scena.html`
        ⇒ it too has the word `remotix`, and its work ended up in the
        encoder's sum: the measure that decides WHEN to graft the fault
        counted the browser's consumption.  ⚠ The test below did not catch it
        because the fake browser line did not name the real folder.
    ⇒ The **name of the executable** (`argv[0]`, without path) is compared, not
      a substring of the line.
    """
    if not text:
        return None
    total = None
    for line in text.splitlines():
        pieces = line.split(None, 1)
        if len(pieces) < 2:
            continue
        argv0 = os.path.basename(pieces[1].split(None, 1)[0])
        # ⚠ The product's child RENAMES ITSELF — `remotix-child --internal-child
        #   …` — so «equal to the name» is not enough: the name followed by
        #   `-` or `:` also counts, which is how processes give themselves a title.  ⛔ And the
        #   reverse does not count: `firefox-esr` never becomes `remotix`.
        if argv0 != name and not argv0.startswith(name + "-") \
           and not argv0.startswith(name + ":"):
            continue
        try:
            seconds = int(pieces[0])
        except ValueError:
            continue
        total = seconds if total is None else total + seconds
    return None if total is None else float(total)


def encoder_cpu(chi, name):
    """⭐⭐ THE ENCODER'S WORK — and it is **the process that is about to be
    stopped**, not another one.

    ⛔⛔ AND HERE WE LOOK AT IT AND NOT AT THE CLIENT, and the reason is a MEASUREMENT.
        `[M]` 27 August 2026, gnome box: with the desktop in motion the
        client burns **0.06 CPU/s** — too little to tell it from a
        client attached to a still desktop without inventing a thin threshold.
        ⭐ The encoder instead **compresses 1920x1080**: its work is of
          another order of magnitude, and on a still scene it is almost zero
          (`[M]` phase 9 §3.1: 0.03 frames/s).
    ⇒ It is also the right quantity for the question: before stopping an
      encoder one wants to know whether **that** encoder was working.
    """
    r = sh("ps -u %s -o times=,args=" % chi, seconds=30)
    return sum_work(r.stdout or "", name)


def seconds_in_view(how_much, step, threshold, cpu_al_s):
    """⭐⭐ HOW MUCH SCENE WENT BY IN VIEW BEFORE THE GRAFT — a CEILING.

    ⛔ It is the term that dirties the gross rate: the frames born between the instant
       the scene started painting and the instant of the graft
       arrive **even with the fault**, because the fault came afterwards.

    ⛔⛔ AND THE CEILING IS `quanto`, i.e. ALL the time gone by since the scene
        was switched on — 22 September 2026, and the old ceiling was
        DISPROVED BY A MEASUREMENT.

        Until today that time was weighted with the encoder's work: in the
        intervals in which the CPU was below the threshold it was assumed that the
        scene had delivered **in proportion**, i.e. at most
        `soglia / cpu_al_s` of the full delivery.  ⇒ `[M]` KDE, 22 Sep 2026:
        estimated ceiling **4.8 s** (443 frames at the healthy rate of 65.1/s), ⛔ but
        in the window **1167** arrived, i.e. 17.9 s of full delivery
        out of 18.1 s elapsed.  The scene was painting at full rate **from
        the start**: what stayed below the threshold was the MEASUREMENT, not the work —
        `ps -o times=` counts whole seconds, and in the first seconds an
        encoder that works looks still.
    ⇒ A ceiling the fact goes through is not a ceiling: we go back to the one that
      cannot be wrong — the scene, at most, painted for all the time
      it was switched on.
    ⚠ `passo`, `soglia` and `cpu_al_s` stay in the signature because the caller
      has them and because they serve to say «I do not know»: without the encoder's
      work one does not even know whether the scene was on.

    ⛔ `None` if one of the numbers is unknown: an invented ceiling would be worse than
      no ceiling.
    """
    if how_much is None or cpu_al_s is None or not cpu_al_s or cpu_al_s <= 0:
        return None
    if step is None or threshold is None or step <= 0 or threshold < 0:
        return None
    return max(float(how_much), float(step))


# ⭐ The window ASKED for the two «encoder stopped» rounds, and its
#   ceiling.  ⛔ The right number is not one: it depends on the box's rate, and
#   `enough_window()` computes it.  This is only the starting point.
FAULT_WINDOW = 90.0
# ⚠ And a ceiling is needed: a very slow box would ask for a window that
#   never ends, and a bench that never ends is a bench that gets switched off.
FAULT_WINDOW_CAP = 400.0


def enough_window(seconds_before, healthy_rate, rate_minimum=MINIMUM_RATE):
    """⭐⭐ HOW LONG THE WINDOW MUST BE for the fault to be able to BITE.

    ⛔⛔ And this is the thing that on 27 August 2026 was missing, and it is the reason why
        the graft sat at the wrong place in the story.

    The rate is **gross**: in the numerator there are ALL the frames of the stream,
    including those born before the window opened; in the denominator there is
    only the window.  ⇒ With the encoder stopped the numerator is not zero: it is
    `secondi_prima × healthy_rate`, i.e. what the scene did in view between
    the instant it started painting and the instant of the graft.

    ⇒ For the mesh to be able to say «collapsed» it takes:

        secondi_prima × healthy_rate / WINDOW  <  rate_minimum

    ⭐ Returns the seconds of window needed.  ⛔ `None` if unknown (and
       then no number is faked).
    """
    if seconds_before is None or healthy_rate is None or not rate_minimum:
        return None
    if seconds_before <= 0 or healthy_rate <= 0 or rate_minimum <= 0:
        return None
    return seconds_before * healthy_rate / float(rate_minimum)


def wait_desktop_settled(load, cap, threshold=CPU_THRESHOLD,
                                    step=CPU_STEP):
    """⭐ PHASE 12 (19 Sep 2026) — BEFORE SWITCHING ON THE SCENE, the desktop STILL.

    ⛔ `[M]` On KDE the session is born with the Plasma splash screen, which
       ANIMATES for ~2.4 s: the encoder is already working, `aspetta_che_i_
       fotogrammi_arrivino` passes on the animation and not on the scene, and the
       SIGSTOP of the «encoder stopped» fault fell on black ⇒ the mesh did not
       judge (3).  ⚠ Moving the graft further on is not possible: the rate is
       GROSS (`enough_window`), and more scene in view before the graft
       means a fault that can no longer be seen.
    ⭐ Instead the SWITCHING ON of the scene is moved: we wait for the encoder's work
       to drop below the threshold for a whole step — the desktop no longer
       has anything to say — and only then is it switched on.  On GNOME at mounting
       the desktop is already still ⇒ a single step, as it was.  It holds for every
       desktop, without asking which one it is.

    Returns `(fermo, secondi_attesi)` — `fermo` is `True`, `False` (ceiling
    expired: we go on SAYING SO) or `None` (work unreadable).
    """
    started = time.time()
    before = load()
    if before is None:
        return None, 0.0
    while time.time() - started < cap:
        t0 = time.time()
        time.sleep(step)
        after = load()
        how_much = work_per_second(before, after, time.time() - t0)
        before = after
        if how_much is None:
            return None, round(time.time() - started, 1)
        if how_much < threshold:
            return True, round(time.time() - started, 1)
    return False, round(time.time() - started, 1)


def wait_for_frames(load, cap, threshold=CPU_THRESHOLD,
                                      step=CPU_STEP):
    """⭐⭐ WAITS FOR THE SCENE TO BE SEEN MOVING — and not a fixed time.

    ⛔ It is the step that replaces `time.sleep(--wait-scene)`: `--wait-scene`
       turns from a wait into a **CEILING**, and the round goes on as soon as the frames
       really arrive instead of by the clock.  `LEZIONI.md` §1.45.
    ⚠ `leggi()` returns the CPU seconds burned so far by whoever delivers, or
      `None`.  ⛔ The bytes on disk are not looked at: the frames file the
      client writes **only at the end** (`[R]` `01-b3-cliente.py:1416`),
      so during the round there is nothing to weigh.

    Returns `(visto, lavoro_al_s, secondi_attesi)` — `visto` is `True`, `False`
    (the ceiling expired) or ⛔ `None` (I could not read the work).
    """
    started = time.time()
    before = load()
    if before is None:
        return None, None, 0.0
    best = 0.0
    while time.time() - started < cap:
        t0 = time.time()
        time.sleep(step)
        after = load()
        how_much = work_per_second(before, after, time.time() - t0)
        before = after
        if how_much is None:
            # ⛔ Whoever was delivering is no longer there, or cannot be read.
            return None, best, round(time.time() - started, 1)
        best = max(best, how_much)
        if how_much >= threshold:
            return True, how_much, round(time.time() - started, 1)
    return False, best, round(time.time() - started, 1)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CERTIFICATION
# ═══════════════════════════════════════════════════════════════════════════
def certify():
    """⚠ And it declares what it covers and what it does not.

    It COVERS three things, and the third is the one that gets forgotten:
      1. **the two judges** — the new one («are two frames different?») and
         the stream one: that a sequence of identical frames is RED,
         that *«still scene»* never is, that «I could not look» returns
         «I do not know» and not zero, ⭐ and that the four thresholds are crossed
         **at the edge**, one level above and one below;
      2. ⭐ **«was the client ADMITTED?»**, which is not a word inside a
         text;
      3. ⭐⭐⭐ **the three JOINTS**: the exit codes of the two grafted faults and of the
         negative control, which are **inverted** and from which C13 derives whether the
         net can still say red.  ⛔ It is the piece `LEZIONI.md` §1.52 was
         born for, and which neither of the two certifications of the time covered.
    ⛔ It DOES NOT COVER, and it must be said because it is the half that matters:
      · that the scene really moves on the screen, nor that the product
        delivers — that is said by the grafted faults **on the real thing**;
      · ⚠⚠ **that the five thresholds are at the right POINT.**  Here the images
        are synthetic and have never gone through either the H.264 encoding in
        4:2:0 or a colour profile.  ⇒ It tests that every comparison **falls
        where it says it falls**, ⛔ not that the point is the good one.  They stay
        `[?]`, and they are calibrated with the numbers the mesh prints at every round.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        print("⛔ numpy or Pillow is missing: I cannot even certify myself")
        print("   ⇒ I could not look")
        return 3
    import tempfile

    reader, dove_l = color_reader()
    referee, dove_g = desktop_judge()
    if reader is None or referee is None:
        print("⛔ I cannot find (or it does not hold up) one of the two imported judges:")
        print("   10-f1-testimone.py    : %s" % (dove_g or "not found"))
        print("   11-c8-…apre-il-browser: %s" % (dove_l or "not found"))
        print("   ⇒ I could not look")
        return 3

    lav = tempfile.mkdtemp(prefix="c3cert-")
    L, A = 128, 72

    def sequence(name, amount, draw):
        """Writes `amount` PNGs and returns their list.  `draw(i)` -> array."""
        dove = os.path.join(lav, name)
        os.makedirs(dove, exist_ok=True)
        report = []
        for i in range(amount):
            p = os.path.join(dove, "f-%05d.png" % i)
            Image.fromarray(draw(i)).save(p)
            report.append(p)
        return report

    def background(color):
        a = np.zeros((A, L, 3), dtype="uint8")
        a[:, :] = color
        return a

    def scene(i):
        """The declared scene: the alternating background and the scrolling band.

        ⚠ It is the synthetic copy of `11-c3-scena.html`, and the two numbers — the 3 %
          of the step and the 20 % of the width — must stay **the same**:
          if they diverge, the certification tests a scene that nobody ever puts
          on the screen.
        """
        a = background(SCENE_A if (i // 3) % 2 == 0 else SCENE_B)
        x = (i * 3) % 100
        c0 = int(L * x / 100.0)
        c1 = min(L, c0 + int(L * 0.20))
        a[:, c0:c1] = (10, 10, 10)
        return a

    def frozen(i):
        return scene(0)

    def noise(i, amplitude):
        """A fixed background with a disturbance of declared amplitude: ⭐ it serves to
        cross the NOISE threshold in both directions."""
        a = background(SCENE_A).astype("int16")
        # half of the image deviates by `amplitude` on alternate frames
        if i % 2:
            a[: A // 2, :, 0] = np.clip(a[: A // 2, :, 0] + amplitude, 0, 255)
        return a.astype("uint8")

    def speck(i):
        """Changes VERY FEW pixels: ⭐ it crosses the PAIR threshold."""
        a = background(SCENE_A)
        a[0, (i * 3) % L] = (255, 255, 255)      # 1 pixel of 9216 = 0.01 %
        return a

    print("== certification of C3's judges ==")
    print("   desktop judge : %s" % dove_g)
    print("   colour reader : %s" % dove_l)
    print("   minimum rate %.2f/s (rough reference [M] %.1f/s) · noise ±%d "
          "per channel · pair ≥%.0f%% of the pixels · at least %.0f%% of the pairs"
          % (MINIMUM_RATE, REFERENCE_FPS, NOISE_THRESHOLD, PAIR_THRESHOLD * 100,
             PAIR_FRACTION * 100))
    print()
    troubles = 0

    def prova(name, obtained, expected, extra=""):
        nonlocal troubles
        ok = obtained == expected
        if not ok:
            troubles += 1
        print("  %s  %-58s  ⇒ %-10s (expected %s)%s"
              % ("OK " if ok else "NO ", name, obtained, expected,
                 ("  %s" % extra) if extra else ""))

    # ── 1. the real scene in motion ────────────────────────────────────────
    alive = sequence("alive", 61, scene)
    e = judge_stream(viva, 2.0)
    prova("the declared scene moves", e["state"], "cambia",
          "different pairs %s/%s" % (e["diverse"], e["coppie"]))

    # ── 2. ⭐ THE FAULT: the same frame repeated ───────────────────────────
    halt = sequence("halt", 61, frozen)
    e2 = judge_stream(halt, 2.0)
    prova("⭐ the same frame repeated ⇒ FROZEN IMAGE",
          e2["state"], "congelata",
          "different pairs %s/%s" % (e2["diverse"], e2["coppie"]))

    # ── 3. the rate, crossed in BOTH directions ────────────────────────────
    #    61 frames in 5 s = 12.2/s (above 4.0) · in 30 s = 2.03/s (below)
    prova("the rate stays above the threshold (12.2/s)",
          judge_stream(viva, 5.0)["state"], "cambia")
    prova("⭐ the rate COLLAPSES below the threshold (2.03/s)",
          judge_stream(viva, 30.0)["state"], "crollati")
    prova("no frame with the scene in motion ⇒ red",
          judge_stream([], 10.0)["state"], "crollati")

    # ── 4. ⚠⚠ THE NEGATIVE CONTROL: «still scene» must NEVER give red ──────
    prova("⚠ STILL scene and no frame ⇒ I do not know, NOT red",
          judge_stream([], 30.0, scene_stop=True)["state"], "non-lo-so")
    prova("⚠ STILL scene and frames all equal ⇒ I do not know, NOT red",
          judge_stream(halt, 30.0, scene_stop=True)["state"], "non-lo-so")
    prova("⚠ STILL scene with a single frame ⇒ I do not know, NOT red",
          judge_stream(viva[:1], 30.0, scene_stop=True)["state"], "non-lo-so")

    # ── 5. the NOISE threshold, crossed in both directions ─────────────────
    below = sequence("rumore-sotto", 21, lambda i: noise(i, NOISE_THRESHOLD - 2))
    above = sequence("rumore-sopra", 21, lambda i: noise(i, NOISE_THRESHOLD + 6))
    ms = changing_pairs(below)
    mp = changing_pairs(above)
    prova("a disturbance of ±%d levels is NOISE, not movement" % (NOISE_THRESHOLD - 2),
          0 if ms is None else ms["diverse"], 0)
    prova("⭐ a disturbance of ±%d levels IS movement" % (NOISE_THRESHOLD + 6),
          0 if mp is None else mp["diverse"], 20)

    # ── 6. the PAIR threshold, crossed in both directions ──────────────────
    small = sequence("speck", 21, speck)
    mm = changing_pairs(small)
    prova("one pixel changing is not a scene moving",
          0 if mm is None else mm["diverse"], 0)
    prova("⇒ and the corresponding stream is FROZEN",
          judge_stream(small, 1.0)["state"], "congelata")

    # ── 7. ⛔ the «I do not know», which are neither green nor red ─────────
    prova("⛔ no list (ffmpeg produced nothing) ⇒ I do not know",
          judge_stream(None, 10.0)["state"], "non-lo-so")
    prova("⛔ a single frame: there are no pairs ⇒ I do not know",
          judge_stream(viva[:1], 0.05)["state"], "non-lo-so")
    missing = [os.path.join(lav, "non-ci-sono-%d.png" % i) for i in range(5)]
    prova("⛔ unreadable frames ⇒ I do not know",
          judge_stream(missing, 1.0)["state"], "non-lo-so")
    prova("⛔ and the meter returns «I do not know», not zero",
          "unknown" if changing_pairs(missing) is None else "a number",
          "unknown")

    # ── 8. ⭐ is the DECLARED SCENE on the screen? (the imported reader) ────
    def fr(p, color):
        return reader.color_fraction(p, color, TOLERANCE)

    last_alive = viva[-1]
    last_other = sequence("altro", 1, lambda i: background((58, 62, 70)))[0]
    prova("the declared scene IS on the screen",
          "yes" if max(fr(last_alive, SCENE_A), fr(last_alive, SCENE_B))
          >= SCENE_FRACTION else "no", "yes")
    prova("⛔ any desktop is NOT the declared scene",
          "yes" if max(fr(last_other, SCENE_A), fr(last_other, SCENE_B))
          >= SCENE_FRACTION else "no", "no")
    # ⭐ and the colour shifted by as much as the tolerance allows must stay «yes»
    moved = sequence("spostata", 1, lambda i: background(
        tuple(min(255, max(0, c + s)) for c, s in zip(SCENE_A, (+30, +30, -30)))))[0]
    prova("⭐ colour shifted within the tolerance ⇒ it is still the scene",
          "yes" if max(fr(moved, SCENE_A), fr(moved, SCENE_B))
          >= SCENE_FRACTION else "no", "yes")
    too = sequence("too", 1, lambda i: background(
        tuple(min(255, max(0, c + s)) for c, s in zip(SCENE_A, (+120, +120, -120)))))[0]
    prova("colour shifted TOO MUCH ⇒ it is no longer the scene",
          "yes" if max(fr(too, SCENE_A), fr(too, SCENE_B))
          >= SCENE_FRACTION else "no", "no")

    # ── 9. ⭐⭐ AND THE PROOF OF THE «repeated frame» GRAFTED FAULT,
    #        done as it will be done on the real thing: **on the same data**.
    print()
    healthy = judge_stream(viva, 2.0)
    scarred = judge_stream(scar_repeating(viva), 2.0)
    proven = (healthy["state"] == "cambia" and scarred["state"] == "congelata"
                  and healthy["diverse"] > 0 and scarred["diverse"] == 0)
    if not proven:
        troubles += 1
    print("  %s  ⭐ the DEFACEMENT on the same data: different pairs from %s to %s, "
          "verdicts «%s» and «%s»"
          % ("OK " if proven else "NO ", healthy["diverse"],
             scarred["diverse"], healthy["state"], scarred["state"]))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE THRESHOLDS CROSSED **AT THE EDGE**, and not from afar.
    #
    # ⛔ Before there were only distant cases (noise 10 and 18 against 12; rate 12.2 and
    #    2.03 against 4.0; tolerance 30 and 120 against 48): with those one tests
    #    that the comparison has the right **direction**, ⚠ not that the threshold falls at the
    #    point where it says it falls.  ⇒ And since the numbers are all `[?]` to be
    #    recalibrated, it is exactly the place where the trap bites (§1.50).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    # the NOISE, one level below and one above
    b_below = sequence("bordo-r-sotto", 11, lambda i: noise(i, NOISE_THRESHOLD))
    b_above = sequence("bordo-r-sopra", 11, lambda i: noise(i, NOISE_THRESHOLD + 1))
    m1 = changing_pairs(b_below)
    m2 = changing_pairs(b_above)
    prova("a deviation of EXACTLY %d levels is still noise" % NOISE_THRESHOLD,
          0 if m1 is None else m1["diverse"], 0)
    prova("⭐ a deviation of %d levels is already movement" % (NOISE_THRESHOLD + 1),
          0 if m2 is None else m2["diverse"], 10)

    # the PAIR: how many pixels must change.  9216 pixels ⇒ 1 % = 92.16
    def block(i, how_many_pixel):
        a = background(SCENE_A)
        if i % 2:
            flat = a.reshape(-1, 3)
            flat[:how_many_pixel] = (255, 255, 255)
            a = flat.reshape(A, L, 3)
        return a
    below = sequence("bordo-c-sotto", 11, lambda i: block(i, 92))   # 0.998 %
    above = sequence("bordo-c-sopra", 11, lambda i: block(i, 93))   # 1.009 %
    m3 = changing_pairs(below)
    m4 = changing_pairs(above)
    prova("92 pixels of 9216 (0.998 %) are NOT a change",
          0 if m3 is None else m3["diverse"], 0)
    prova("⭐ 93 pixels of 9216 (1.009 %) ARE",
          0 if m4 is None else m4["diverse"], 10)

    # the RATE, exactly astride 4.00/s: 61 frames in 15.25 s = 4.000
    prova("the rate at 4.07/s (just above the threshold) ⇒ GREEN",
          judge_stream(viva, 15.0)["state"], "cambia")
    prova("⭐ the rate at 3.94/s (just below) ⇒ RED",
          judge_stream(viva, 15.5)["state"], "crollati")

    # the TOLERANCE on the scene's colour, at the edge
    to_limit = sequence("bordo-t1", 1, lambda i: background(
        (TOLERANCE, TOLERANCE, 255 - TOLERANCE)))[0]
    beyond = sequence("bordo-t2", 1, lambda i: background(
        (TOLERANCE + 1, TOLERANCE + 1, 255 - TOLERANCE - 1)))[0]
    prova("⭐ colour shifted by EXACTLY ±%d ⇒ it is still the scene" % TOLERANCE,
          "yes" if max(fr(to_limit, SCENE_A), fr(to_limit, SCENE_B))
          >= SCENE_FRACTION else "no", "yes")
    prova("colour shifted by ±%d ⇒ it is no longer the scene" % (TOLERANCE + 1),
          "yes" if max(fr(beyond, SCENE_A), fr(beyond, SCENE_B))
          >= SCENE_FRACTION else "no", "no")

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ «WAS THE CLIENT ADMITTED?» — the word inside a text is NOT enough.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    for name, text, expected in (
            ("the real line of the admitted client",
             "   ADMITTED after 1023 ms\n", True),
            ("⛔ FAREWELL instead of ADMITTED — the word is there, the sense is opposite",
             "   ⛔ RuntimeError: FAREWELL instead of ADMITTED: reason 0x03\n", False),
            ("⛔ «expected ADMITTED, arrived …» — likewise",
             "   ⛔ RuntimeError: expected ADMITTED, arrived FAREWELL\n", False)):
        prova(name, was_admitted(text), expected)
    prova("⛔ the client said NOTHING ⇒ I do not know",
          "unknown" if was_admitted("") is None else "a yes or a no",
          "unknown")

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ «ARE THE FRAMES ARRIVING NOW?» — the signal that decides
    #    **when** the fault is grafted (cure of 27 August 2026).
    # ⛔ It is all in PURE functions on purpose: the moment of the graft is the thing
    #    that on 27 August 2026 was wrong, and it is not left to code that
    #    runs only inside the box.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    real_line = ("42 (remotix) S 1 42 42 0 -1 4194304 100 0 0 0 300 100 "
                 "5 5 20 0 3 0")
    prova("the work of a process, from /proc/<pid>/stat ⇒ 4.00 s of CPU",
          cpu_from_line(real_line, 100.0), 4.0)
    prova("⛔ the command name WITH A SPACE does not shift the fields",
          cpu_from_line("42 (a b) S 1 42 42 0 -1 4194304 100 0 0 0 300 100 "
                         "5 5 20 0 3 0", 100.0), 4.0)
    prova("⛔ the command name with a PARENTHESIS inside: the last one is cut",
          cpu_from_line("42 (we)ird) S 1 42 42 0 -1 4194304 100 0 0 0 300 100 "
                         "5 5 20 0 3 0", 100.0), 4.0)
    prova("⛔ a truncated line ⇒ «I do not know», and not zero",
          cpu_from_line("42 (remotix) S 1 42", 100.0), None)
    prova("⛔ no line ⇒ «I do not know», and not zero",
          cpu_from_line("", 100.0), None)
    real_ps = ("   12 /opt/remotix/remotix --sessione c3u1\n"
               "    3 /opt/remotix/remotix --sessione c3u1 --figlio\n"
               # ⛔ THE REAL LINE of the scene's browser, the one that on 22 Sep
               #    2026 ended up in the sum: the word `remotix` is in the
               #    PATH OF THE PAGE, not in the name of the program.
               "  400 /usr/lib/firefox-esr/firefox-esr --kiosk "
               "file:///opt/remotix/11-c3-scena.html\n")
    prova("⭐ the work of the ENCODER, and only its own: 12+3 ⇒ 15 s of CPU",
          sum_work(real_ps, "remotix"), 15.0)
    prova("⭐ the child that RENAMES ITSELF «remotix-child» counts anyway",
          sum_work("    9 remotix-child --internal-child c3u2 4013 4013\n",
                       "remotix"), 9.0)
    prova("⛔ a name that starts the same but is another program does NOT count",
          sum_work("    9 /usr/bin/remotixaltro --x\n", "remotix"), None)
    prova("⛔ the browser is not the encoder: it does not enter the sum",
          sum_work(real_ps, "remotix") != sum_work(real_ps, ""), True)
    prova("⛔ no process with that name ⇒ «I do not know», and ⛔ NOT zero",
          sum_work(real_ps, "kwin_wayland"), None)
    prova("⚠ a line without the time does not throw off the sum",
          sum_work("nonunnumero /opt/remotix/remotix\n   7 "
                       "/opt/remotix/remotix\n", "remotix"), 7.0)
    prova("⛔ no line at all ⇒ «I do not know»", sum_work("", "remotix"),
          None)

    # ── the pattern that chooses WHOM to stop ─────────────────────────────
    # ⛔ It is the line that on 22 September 2026 stopped the scene's browser
    #    for half a day: here it is tested on REAL lines, taken from `ps`.
    def takes(line):
        return re.match(product_model("remotix"), line) is not None

    prova("⭐ the child that renames itself («remotix-child …») IS taken",
          takes("remotix-child --internal-child c3u2 4013 4013 1920 1080 2 -"),
          True)
    prova("⭐ the binary called by path IS taken",
          takes("/opt/remotix/remotix --address 0.0.0.0 --port 8512"), True)
    prova("⛔⛔ the SCENE'S BROWSER is not taken, and its line names "
          "«remotix»",
          takes("/usr/lib/firefox-esr/firefox-esr --kiosk "
                 "file:///opt/remotix/11-c3-scena.html"), False)
    prova("⛔ nor the shell running the search (the pkill -f trap)",
          takes("/bin/sh -c pgrep -u c3u2 -f '^(remotix|/[^ ]*/remotix)'"),
          False)
    prova("⛔ nor another program that starts the same",
          takes("/usr/bin/remotixaltro --x"), False)
    prova("the work per second between two readings (1.0 ⇒ 3.0 in 2 s) ⇒ 1.00/s",
          work_per_second(1.0, 3.0, 2.0), 1.0)
    prova("⛔ a missing reading ⇒ «I do not know», and not zero",
          work_per_second(None, 3.0, 2.0), None)
    prova("⛔ zero seconds between the two readings ⇒ «I do not know»",
          work_per_second(1.0, 3.0, 0.0), None)
    prova("⚠ a backwards count is not a measurement ⇒ 0, never a negative",
          work_per_second(5.0, 3.0, 2.0), 0.0)
    prova("⭐ the scene in view before the graft: 27 s of waiting ⇒ at most "
          "27 s (⛔ not 6.17: the old ceiling weighted on the CPU was "
          "disproved, 22 Sep 2026)",
          round(seconds_in_view(27.0, 2.0, 0.10, 0.60), 2), 27.0)
    prova("⭐ if the frames arrive at the first try, it is only the step ⇒ 2.00 s",
          round(seconds_in_view(2.0, 2.0, 0.10, 0.60), 2), 2.0)
    prova("⛔ without the client's work no ceiling is faked ⇒ «I do not know»",
          seconds_in_view(27.0, 2.0, 0.10, None), None)
    prova("⭐⭐ the window needed: 6 s in view × 30/s healthy ÷ 4/s demanded "
          "⇒ 45 s",
          enough_window(6.0, 30.0, 4.0), 45.0)
    prova("⛔ without the healthy rate no window is faked ⇒ «I do not know»",
          enough_window(6.0, None, 4.0), None)
    prova("⛔ without the seconds in view no window is faked ⇒ «I do not know»",
          enough_window(None, 30.0, 4.0), None)

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ THE THREE JOINTS — the exit codes, which are INVERTED and from which C13
    #      derives whether the net can still say red (`LEZIONI.md` §1.52).
    # ═══════════════════════════════════════════════════════════════════════
    print()

    def cur_round(state, reason="", diverse=None, pairs=None, minima=None,
             rate=None, stopped_count=None, taken=None, frames=None,
             seconds=90.0, work_seen=True, queue_fraction=1.0,
             cpu_before=0.60, cpu_window=0.60, seconds_before=6.0):
        """⚠ The default values are those of a round **that holds**:
        so every case below breaks ONE thing only, and one knows which."""
        return {"state": state, "reason": reason, "why": "(fake)",
                "diverse": diverse, "pairs": pairs, "minima": minima,
                "rate": rate, "stopped_count": stopped_count, "pkill_ha_preso": taken,
                "who": "c3uX", "frames": frames, "seconds": seconds,
                "work_seen": work_seen, "queue_fraction": queue_fraction,
                "coda_diverse": 60, "coda_coppie": 60, "cpu_before": cpu_before,
                "cpu_window": cpu_window, "seconds_before": seconds_before}

    healthy_ok = cur_round("cambia", "cambia", diverse=60, pairs=60, minima=0.08,
                   rate=30.0)
    frozen_run = cur_round("congelata", "congelata", diverse=0, pairs=60)
    # ⭐ The round with the fault that HOLDS: the scene was moving, the encoder
    #   died, and inside the window the client no longer worked.
    broken_ok = cur_round("crollati", "ritmo-crollato", rate=0.4, stopped_count=1,
                    taken=True, cpu_window=0.01)
    joints = [
        ("repeated: healthy green + defaced frozen + lively scene ⇒ 0",
         test_repeated(healthy_ok, frozen_run), 0),
        ("⛔ repeated: the defacement was NOT seen ⇒ 1",
         test_repeated(healthy_ok, cur_round("cambia", "cambia", 60, 60)), 1),
        ("⭐ repeated: the scene is TOO TIMID (1.2× the threshold) ⇒ 1",
         test_repeated(cur_round("cambia", "cambia", 60, 60, minima=0.012,
                                   rate=30.0), frozen_run), 1),
        ("⭐ repeated: the HEALTHY CONTROL is red ⇒ 3, ⛔ NOT 1",
         test_repeated(cur_round("congelata", "congelata", 0, 60), frozen_run), 3),
        ("repeated: the healthy one could not look ⇒ 3",
         test_repeated(cur_round("non-lo-so", "palco-non-nato"), frozen_run), 3),
        ("⭐ repeated: the DEFACED one could not be judged ⇒ 3, not 1",
         test_repeated(healthy_ok, cur_round("non-lo-so", "niente-coppie")), 3),
        ("stopped: healthy green + fault collapsed + signature ⇒ 0",
         test_stopped(healthy_ok, broken_ok), 0),
        ("⛔ stopped: with the encoder stopped the frames arrive anyway ⇒ 1",
         test_stopped(healthy_ok, cur_round("cambia", "cambia", rate=29.0,
                                         stopped_count=1, taken=True,
                                         cpu_window=0.01)), 1),
        ("⛔ stopped: the GROSS rate drops little (30 ⇒ 12, above the share) ⇒ 1",
         test_stopped(healthy_ok, cur_round("crollati", "ritmo-crollato",
                                         rate=12.0, stopped_count=1, taken=True,
                                         cpu_window=0.01)), 1),
        ("⭐ stopped: the client STILL WORKS inside the window ⇒ 1",
         test_stopped(healthy_ok, cur_round("crollati", "ritmo-crollato",
                                         rate=0.4, stopped_count=1, taken=True,
                                         cpu_window=0.30)), 1),
        ("⚠ stopped: `pkill` took nothing ⇒ 3",
         test_stopped(healthy_ok, cur_round("crollati", "ritmo-crollato",
                                         rate=0.4, stopped_count=0, taken=False)), 3),
        ("⭐ stopped: the HEALTHY CONTROL is red ⇒ 3, ⛔ NOT 1",
         test_stopped(cur_round("crollati", "ritmo-crollato", rate=0.1),
                           broken_ok), 3),
        # ⭐⭐⭐ THE MOMENT OF THE GRAFT — the cases that on 27 August 2026 were
        #     missing, and they are the ones for which the round exited 3.
        ("⭐⭐ stopped: the frames had NEVER been seen arriving ⇒ 3, ⛔ not 1",
         test_stopped(healthy_ok, cur_round("crollati", "ritmo-crollato",
                                         rate=0.4, stopped_count=1, taken=True,
                                         cpu_window=0.01,
                                         work_seen=False)), 3),
        ("⭐⭐ stopped: the last frames delivered were IDENTICAL "
         "(graft too early) ⇒ 3",
         test_stopped(healthy_ok, cur_round("crollati", "ritmo-crollato",
                                         rate=0.4, stopped_count=1, taken=True,
                                         cpu_window=0.01,
                                         queue_fraction=0.0)), 3),
        ("⭐ stopped: I do not know whether the last delivered ones changed ⇒ 3",
         test_stopped(healthy_ok, cur_round("crollati", "ritmo-crollato",
                                         rate=0.4, stopped_count=1, taken=True,
                                         cpu_window=0.01,
                                         queue_fraction=None)), 3),
        ("⭐⭐ stopped: the WINDOW was too short for this rate ⇒ 3, not 1",
         test_stopped(healthy_ok, cur_round("crollati", "ritmo-crollato",
                                         rate=0.4, stopped_count=1, taken=True,
                                         cpu_window=0.01, seconds=30.0)), 3),
        ("⭐ stopped: I do not know how much the client worked in the window ⇒ 3",
         test_stopped(healthy_ok, cur_round("crollati", "ritmo-crollato",
                                         rate=0.4, stopped_count=1, taken=True,
                                         cpu_window=None)), 3),
        ("⭐ still scene: the round happened and did not give red ⇒ 0",
         test_still_scene(cur_round("non-lo-so", "scena-ferma",
                                      frames=1, seconds=60.0)), 0),
        ("⛔ still scene: the mesh gave RED ⇒ 1 (the control failed)",
         test_still_scene(cur_round("crollati", "zero-fotogrammi")), 1),
        ("⚠ still scene: the stage was not born ⇒ 3, ⛔ not a successful control",
         test_still_scene(cur_round("non-lo-so", "palco-non-nato")), 3),
    ]
    for name, (e, _lines), expected in joints:
        prova(name, e, expected)

    shutil.rmtree(lav, ignore_errors=True)
    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE CARD'S GROUPS — ⛔ the case that was missing before today.
    #
    # ⛔ A tenant outside the groups of the `/dev/dri` nodes makes a
    #    BLIND session be born (`[M]` 0 of 4, zero frames, `fasi/10-…` §7.4) ⇒
    #    this mesh would measure the darkness.  ⭐ It is demanded that it says «I could
    #    not look», ⛔ and NEVER red: it is a fault of the BENCH (§1.51).
    # ⚠ The cases live in C1, with the step they certify: ⛔ a copy here
    #   would be a second place to diverge from (§1.47).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    group_troubles, how_many_groups = c1_home().certify_groups("C3")
    troubles += group_troubles

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ THE SHARED PROVISIONING — ⛔ the case that on 27 August 2026 was missing,
    #    and for which this mesh said «I could not look» accusing the
    #    product of a fault of the bench.
    # ⚠ The cases live in C2, with the code they certify: ⛔ a copy here would be
    #   a second place to diverge from (§1.47).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    home_pr = provisioning_home()
    if home_pr is None:
        print("  NO   ⛔ I cannot find `11-c2-…py`: the provisioning cannot be certified")
        troubles += 1
        how_many_pr = 0
    else:
        troubles_pr, how_many_pr = home_pr.certify_provisioning("C3", "c3u")
        troubles += troubles_pr

    print()
    if troubles:
        print("⛔ C3's judges are NOT reliable: %d cases wrong" % troubles)
        return 1
    print("⭐ the judges see the scene changing and catch the frozen "
          "image, the four thresholds fall where they say (at the edge),")
    print("   ⭐ «ADMITTED» is a line and not a word, ⚠ on a still scene a red "
          "never comes out, ⛔ and «I do not know» is not zero,")
    print("   ⭐⭐ and the THREE JOINTS — the exit codes of the two grafted faults and "
          "of the negative control — say 0, 1 and 3 where they must (§1.52)")
    print("   ⭐ and the CARD'S GROUPS: a tenant that cannot see makes it say "
          "«I could not look», ⛔ never red")
    # ⛔ The provisioning line is printed ONLY if the real cases ran.
    if how_many_pr >= 4:
        print("   ⭐⭐ and THE PROVISIONING: a /tmp/mozilla of another mesh I do not "
              "touch, and my tenant writes anyway — ⛔ never red")
    else:
        print("   ⚠ and THE PROVISIONING is covered ONLY halfway: the real cases "
              "need the administrator, and here I did not run them")
    print("⚠ and this certification covers THE JUDGES AND THE JOINTS, ⛔ not the "
          "real delivery of the frames nor that the five thresholds are at the "
          "right POINT (see the top)")
    return 0


def scar_repeating(listing):
    """⭐ THE «repeated frame» GRAFTED FAULT, and it fits in one line.

    ⛔ **The in-memory copy** of the list is defaced: the stream on disk is not
       touched.  It is the same shape as C9 (`--remove-name`), and it has the merit that
       the healthy control and the fault run **on the same data** ⇒ the difference
       cannot come from a different round.
    """
    if not listing:
        return listing
    return [listing[0]] * len(listing)


# ═══════════════════════════════════════════════════════════════════════════
# THE TERRAIN AND THE MOVES — ⚠ the same as C2, and for the same reasons
# ═══════════════════════════════════════════════════════════════════════════
def sh(command, seconds=120):
    try:
        return subprocess.run(["/bin/sh", "-c", command],
                              capture_output=True, text=True, timeout=seconds)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(command, 124, "", "expired")


def how_many_screens(text):
    """⛔ `None` = I do not know; `0` = I asked and there is none."""
    if text is None:
        return None
    return len(OUTPUT_SIGNATURE.findall(text))


def create(chi, password):
    """⛔ It is deleted BEFORE creating it: «from zero» includes «from zero with respect to
       myself of yesterday» (`[M]` C1, 26 August 2026)."""
    sh("loginctl terminate-user %s 2>/dev/null; pkill -KILL -u %s 2>/dev/null; "
       "userdel -r %s 2>/dev/null; rm -rf /home/%s" % (chi, chi, chi, chi))
    # ⛔⛔ THE CARD'S GROUPS ARE NO LONGER INSIDE THE `useradd`.
    #     `usermod -aG video,render` nailed down two names — which belong to ONE
    #     distribution — and ⛔ **did not read back**: a successful `usermod` does not
    #     mean «it is in there» (E1, «written is not in force»).
    # ⭐ They are given by `attrezzi-gruppi-scheda.sh`, which READS them from the `/dev/dri` nodes and
    #   then VERIFIES comparing the numbers.  ⇒ Here there is no longer any group
    #   name and no number.
    # ⛔ And without them, `[M]` the session is born BLIND (0 of 4, zero frames,
    #   `fasi/10-…` §7.4): this mesh would measure the darkness and call it
    #   a product defect.  ⇒ We do not measure: the caller exits **3**.
    r = sh("useradd -m -s /bin/bash %s && "
           "printf '%s:%s\n' | chpasswd" % (chi, chi, password))
    if r.returncode != 0:
        return False, (r.stderr or "").strip()[:120]
    e_gr, why_groups = ensure_groups(chi, prefix="      ")
    if e_gr != 0:
        return False, why_groups
    # ⭐⭐ AND THE PROVISIONING, right after the `useradd -m` that copies the skeleton:
    #    it is there that the tenant is born with `~/.cache` pointing at `/tmp`, ⇒ it is there
    #    that it is given its own.  ⛔ Before switching anything on.
    done_fix, why_fix = provisioning_fix(chi)
    if not done_fix:
        return False, why_fix
    return True, ""


def clear_out(chi, wait):
    # ⛔ First it is WOKEN UP: with `--stopped-encoder` there is a process in state
    #    T, and a stopped process does not go away by itself.  ⚠ And ONLY one's own
    #    stuff is cleared, by name (phase 10 §7.3).
    sh("pkill -CONT -u %s 2>/dev/null" % chi)
    # ⛔ AND ALSO THE PARENT, which belongs to root and not to the tenant: the scene is opened
    #    with `runuser -u <chi> -- … firefox-esr`, and `runuser` mirrors the stop
    #    of the child.  ⚠ A `-CONT` that looks only at the tenant's processes
    #    leaves it stopped in `T` forever, with the zombie browser underneath (22 Sep 2026).
    #    ⭐ The pattern stays LIMITED to one's own tenant, §7.3 of phase 10.
    # ⛔⛔ AND THE PATTERN MUST NOT FIND ITSELF — 22 September 2026.
    #     `pkill -f "runuser -u c3u2 "` also catches the `/bin/sh -c` that is
    #     running that command, because that string is in ITS command
    #     line: with `-KILL` the shell died halfway through the work and the
    #     `runuser` survived.  ⭐ Square brackets are the classic cure:
    #     `[c]3u2` as an **expression** is worth `c3u2`, but as **text** it does not
    #     look like it, so the command does not fish itself out.
    sh("pkill -CONT -f 'runuser -u [%s]%s ' 2>/dev/null" % (chi[0], chi[1:]))
    sh("loginctl terminate-user %s 2>/dev/null" % chi)
    time.sleep(1.0)
    sh("pkill -KILL -u %s 2>/dev/null" % chi)
    sh("pkill -KILL -f 'runuser -u [%s]%s ' 2>/dev/null" % (chi[0], chi[1:]))
    expiry = time.time() + wait
    while time.time() < expiry:
        viva = sh("loginctl show-user %s >/dev/null 2>&1" % chi).returncode == 0
        proc = sh("pgrep -u %s >/dev/null 2>&1" % chi).returncode == 0
        if not viva and not proc:
            return True
        time.sleep(0.5)
    return False


def il_socket_di(chi):
    """⛔ The Wayland socket is SEARCHED for, not guessed (§3.7)."""
    uid = sh("id -u %s" % chi).stdout.strip()
    if not uid:
        return None, None
    rtd = "/run/user/%s" % uid
    soc = sh("ls %s 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1" % rtd)
    d = soc.stdout.strip()
    return (rtd, d) if d else (rtd, None)


def ask_compositor(chi):
    """⭐ We ask the COMPOSITOR whether there is a screen, not the product.

    ⛔ `[R]` the line *«⛔ ZERO MONITOR»* of `src/sessione.c:345-348` the product
       writes **also during a birth that will succeed** — at that point the
       monitor has not appeared yet (`src/mutter.c:697`).  ⇒ Reading it as
       proof of blindness is an error, and this mesh does not make it.
    """
    rtd, display = il_socket_di(chi)
    if rtd is None:
        return None, "I do not know the uid of «%s»" % chi
    if display is None:
        return None, ("in %s there is no wayland socket: the compositor has not "
                      "been born (yet)" % rtd)
    r = sh("runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
           "wayland-info" % (chi, rtd, display), seconds=60)
    if r.returncode != 0 and not r.stdout:
        return None, ("wayland-info did not speak: %s"
                      % ((r.stderr or "").strip().replace("\n", " ")[:90]))
    return how_many_screens(r.stdout), ""


def turn_on_scene(chi, a):
    """Switches on the declared scene INSIDE the tenant's session."""
    rtd, display = il_socket_di(chi)
    if display is None:
        return None, ("in %s there is no wayland socket: there is no "
                      "compositor the scene can talk to" % rtd)
    args = a.args % {"page": a.scene}
    # ⛔⛔ `setsid`, AND IT IS NOT AN ORNAMENT — 22 September 2026.
    #     Put in the background with `&`, the scene ends up in a BACKGROUND
    #     process group of the terminal that launched the bench (the net runs from `ssh
    #     -tt`).  As soon as the browser touches the terminal — `tcsetattr`, and it does so
    #     at start-up — the kernel sends it **SIGTTOU** and stops it: `[M]` 22 Sep
    #     2026, `firefox-esr` in state `T` from the first instant, i.e. BEFORE the
    #     grafted fault sent its SIGSTOP, and `runuser` stopped with it.
    #     ⇒ The scene that «does not move» was not a product fault: it was the
    #       bench stopping it, and it stayed stopped in all three boxes
    #       even after the round ended.
    # ⭐ With `setsid` the scene no longer has a controlling terminal: no
    #    SIGTTOU, no SIGTTIN.  ⚠ And stdin is closed on /dev/null for the
    #    same reason.
    sh("setsid runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
       "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
       "%s %s < /dev/null > /home/%s/.c3-scena.log 2>&1 &"
       % (chi, rtd, display, chi, a.app, args, chi), seconds=30)
    return display, ""


def scene_is_alive(chi, application):
    """⚠ It does not prove that the scene MOVES: it proves that the program that
       moves it is not dead.  ⛔ And the difference is declared at the top of the file."""
    r = sh("pgrep -u %s -f %s >/dev/null 2>&1" % (chi, application))
    return r.returncode == 0


def product_model(name):
    """⭐ The expression that catches the processes OF THE PRODUCT and nothing else.

    ⛔⛔ And here there are two names for the same thing, which on 22 September 2026
        cost half a day.  The child **renames itself**: `src/figlio.c:1193`
        sets `argv[0] = "remotix-child"`, while `comm` stays `remotix`
        because it comes from the executable (`execve(/opt/remotix/remotix, …)`).
        ⇒ `pkill -f remotix` also caught the **scene's browser**, which has
          `file:///opt/remotix/11-c3-scena.html` in its command line, and
          left it in state `T` together with its `runuser`;
        ⇒ `pkill -x remotix` is not the safe inverse: it looks at `comm`, which the
          product does not control — the day the binary changes name it no longer
          catches anything, **silently**.
    ⭐ That is why it is anchored at the START of the command line, which is the only place
      where the product sits and the browser cannot sit:
        `remotix-child …`      the child that renamed itself
        `/opt/remotix/remotix …`  the binary called by path
    ⚠ And the anchor also protects from itself: the command line of the shell that
      runs this search starts with `/bin/sh`, so it does not fish itself out
      (the `pkill -f` trap — see `sgombra`).
    """
    return "^(%s|/[^ ]*/%s)([ -]|$)" % (name, name)


def encoder_pid(chi, name):
    """The pids of the product's processes that belong to «chi».  ⛔ Never others."""
    r = sh("pgrep -u %s -f '%s'" % (chi, product_model(name)))
    pid = []
    for line in (r.stdout or "").split():
        if line.isdigit():
            pid.append(line)
    return pid


def stop_encoder(chi, name):
    """⛔ THE REAL FAULT: SIGSTOP to the tenant's process that delivers.

    ⚠ And the name must be stated right: **it does not stop «the encoder alone»**, it
      stops the process that contains it.  It is as much as can be done without touching
      the product, and the difference is declared instead of hidden.

    Returns (how_many_stopped, list) — ⭐ and this is the SIGNATURE of the fault: if
    none ended up in state **T**, the injection touched nothing and an
    eventual red belongs to someone else (`LEZIONI.md` §1.52).
    """
    # ⭐ THE OUTCOME IS LOOKED AT: it says exactly whether there was something to stop, and it is
    #   the difference between «I stopped the encoder» and «there was nothing to
    #   stop».  ⛔ Throwing it away would mean trusting a command without
    #   looking at whether it was run (`LEZIONI.md` §1.46).
    pid = encoder_pid(chi, name)
    taken = bool(pid)
    for p in pid:
        sh("kill -STOP %s 2>/dev/null" % p)
    time.sleep(1.0)
    # ⭐⭐ AND **THOSE** PIDS ARE VERIFIED, not «someone in state T»: it is the signature of the
    #     fault (`LEZIONI.md` §1.52), and a fault that could not be grafted
    #     must be able to say it was not there.
    stopped_count = []
    for p in pid:
        s = sh("ps -o stat=,comm= -p %s" % p)
        pieces = (s.stdout or "").split(None, 1)
        if len(pieces) == 2 and pieces[0].startswith("T"):
            stopped_count.append(pieces[1].strip())
    return len(stopped_count), stopped_count, taken


def extract_frames(stream, dove, width, height, cap=900.0):
    """From the H.264 stream taken from the wire pulls out ALL the frames, scaled down.

    ⛔ They are scaled down on purpose: at 1920x1080 a thousand frames are a
       gigabyte and a half, and the comparison gains nothing — the declared
       scene changes in wide blocks, not in fine details.
    ⚠ And the price is declared: a change smaller than one pixel of the
      thumbnail disappears.  ⇒ That is why the scene is made of big blocks, and
      not of a blinking cursor.
    ⛔ And **the result, not the exit code** of ffmpeg is judged
      (`LEZIONI.md` §1.50).
    """
    if os.path.isdir(dove):
        shutil.rmtree(dove, ignore_errors=True)
    os.makedirs(dove, exist_ok=True)
    r = sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -vf scale=%d:%d "
           "-y %s/f-%%05d.png" % (stream, width, height, dove),
           seconds=cap)
    listing = sorted(glob.glob(os.path.join(dove, "f-*.png")))
    # ⛔⛔ AND HERE THE EXIT CODE **IS LOOKED AT**, and it is the reverse of §1.50.
    #    There the exit code had to be ignored because the work was
    #    **done** (the PNG was there and was right).  ⚠ Here an expiry leaves
    #    a **truncated** list, which looks exactly like a lean
    #    grab: ⛔ the rate would come out wrong and the mesh would say «collapsed»
    #    on a healthy session.
    return (listing or None), (r.returncode == 124)


def client_frame_count(queue):
    amount = None
    for line in queue.splitlines():
        if "[vid]" in line and "no frame" not in line:
            try:
                amount = int(line.split("[vid]", 1)[1].strip().split()[0])
            except Exception:
                pass
    return amount


# ═══════════════════════════════════════════════════════════════════════════
# ONE ROUND
# ═══════════════════════════════════════════════════════════════════════════
def one_round(chi, mode, a, referee, reader, healthy_rate=None):
    """`mode` = None (healthy) | "still" (SIGSTOP to the encoder).

    ⛔⛔ THE ORDER OF THE MOVES — and it is the reason why this mesh can be
         written today:

           1. the tenant is created
           2. ⭐ **the client attaches, and STAYS there**: `[R]` `src/mutter.c:697`
              — the `wl_output` of a headless session is born when a
              consumer hooks onto the stream, and dies with the child
           3. we wait for the COMPOSITOR to announce a screen
           4. the declared scene is switched on
           5. ⭐⭐ we wait for the frames to **really arrive** — not a
              fixed time: the client's work is looked at
              (`wait_for_frames`)
           6. (with the fault: ⛔ SIGSTOP **HERE**) ⇒ ⭐ the scene is there, it moves, and the
              frames are arriving: **then** the encoder dies
           7. the measuring window is opened and watched for `--window` seconds
           8. the client finishes and writes the stream

    ⛔⛔ AND POINT 6 IS A CURE OF 27 AUGUST 2026, not a detail.
        Until that day the SIGSTOP sat between 3 and 4, i.e. **before
        the scene existed**: the encoder died on an empty desktop, the
        declared scene never appeared on the screen, and the mesh — ⭐
        honestly — said *«the scene I declared is NOT on the screen
        ⇒ I could not look»*, outcome **3**.
        ⇒ It was not a product defect and it was not a red: it was ⛔ **an
          acceptance test that did not test**, because the fault was grafted at the
          wrong moment of the story.  The guardian was not touched: the graft
          was moved.
    """
    outcome = {"who": who, "mode": mode or "healthy", "state": "non-lo-so",
             "why": "", "frames": None, "ritmo": None, "coppie": None,
             "diverse": None, "palco_s": None, "schermi": None,
             "reason": "", "scena_viva": None, "scena_viva_prima": None,
             "frazione_scena": None, "stopped_count": None, "pkill_ha_preso": None,
             "elenco": None, "seconds": None, "minima": None, "massima": None,
             # ⭐ the new facts of 27 August 2026 — see the order of the moves
             "lavoro_visto": None, "cpu_prima": None, "cpu_finestra": None,
             "secondi_prima": None, "coda_coppie": None, "coda_diverse": None,
             "coda_frazione": None, "finestra_pretesa": None}

    completed, why = create(chi, a.password)
    if not completed:
        outcome["reason"] = "inquilino-non-creato"
        outcome["why"] = "I could not create «%s»: %s" % (chi, why)
        return outcome

    workdir = os.path.join(a.workdir, chi)
    os.makedirs(workdir, exist_ok=True)
    stream = os.path.join(workdir, "presa.264")
    if os.path.exists(stream):
        os.unlink(stream)

    stays = a.wait_stage + a.wait_scene + a.window + a.tail
    started = time.time()
    # ⛔⛔ AND THE CLIENT'S OUTPUT GOES INTO A FILE, NOT INTO A PIPE — and it is not
    #     style: it is a fault avoided.  This client stays on for minutes
    #     **while the bench does other things**, and with `-u` it writes without restraint.  A
    #     pipe nobody empties fills up (64 KB on Linux) and ⛔ **blocks the
    #     writer**: the client would stop halfway through a `print`, would stop
    #     keeping the session alive, and the bench would read «no frame»
    #     blaming the product.
    # ⚠ The examples do not have this problem because they use `subprocess.run`,
    #   which empties the pipes while it waits.  Here we do not wait: we work.
    out_file = os.path.join(workdir, "cliente.log")
    out_fd = open(out_file, "w")
    client = subprocess.Popen(
        ["python3", "-u", a.client,
         "--address", a.address, "--port", str(a.port),
         "--user", chi, "--password", a.password,
         "--video-out", stream, "--stay", str(stays)],
        stdout=out_fd, stderr=subprocess.STDOUT, text=True)

    def close_client(expiry):
        """Waits for the client to finish, and returns what it said.

        ⛔ It always returns a string: if the file cannot be read it is an
           «I could not look», and the caller sees it as «not ADMITTED».
        """
        try:
            client.wait(timeout=expiry)
        except subprocess.TimeoutExpired:
            client.kill()
            client.wait()
        out_fd.close()
        try:
            with open(out_file, "r", errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    screens = None
    reason = "I was never able to ask"
    expiry = time.time() + a.wait_stage
    while time.time() < expiry:
        if client.poll() is not None:
            reason = "the client went away before a screen was born"
            break
        screens, reason = ask_compositor(chi)
        if screens is not None and screens >= MIN_OUTPUTS:
            outcome["palco_s"] = round(time.time() - started, 1)
            break
        screens = None
        time.sleep(2.0)
    outcome["screens"] = screens

    if screens is None or screens < MIN_OUTPUTS:
        outcome["reason"] = "palco-non-nato"
        outcome["why"] = ("in %.0f s the compositor did not announce any "
                           "screen (%s) ⇒ there was nothing to capture"
                           % (a.wait_stage, reason or "?"))
        client.kill()
        close_client(30)
        clear_out(chi, a.wait_clearout)
        return outcome

    # ── from here down there is the switching on of the scene and — with the fault — the graft
    # ⛔⛔ AND WE STAY INSIDE A `try/finally`: between the injection and the cleanup there
    #     are minutes of waiting, and ⚠ a Ctrl-C or an exception there would leave
    #     **the tenant frozen in state T**, the client attached and the
    #     test machine dirty for whoever comes next.
    #     ⭐ The `finally` always wakes up, even when the graft never
    #       happened: waking someone who is not asleep costs nothing,
    #       forgetting it a single time does.
    #     ⚠ And the `try` sits HERE and not lower down on purpose: the graft moved
    #       down into `_rest_of_round` (step 6), but the safety net that
    #       wakes it up must be wider than it.
    try:
        return _rest_of_round(chi, mode, a, referee, reader, outcome,
                                  client, close_client, stream, workdir,
                                  started, stays, healthy_rate)
    finally:
        if mode == "still":
            sh("pkill -CONT -u %s 2>/dev/null" % chi)


def _rest_of_round(chi, mode, a, referee, reader, outcome, client,
                       close_client, stream, workdir, started, stays,
                       healthy_rate=None):
    """The part of the round that sits inside the injection's `try/finally`."""
    # ── 4. the scene ───────────────────────────────────────────────────────
    if not a.still_scene:
        stopped, expected_vals = wait_desktop_settled(
            lambda: encoder_cpu(chi, a.child_name),
            a.wait_scene, a.cpu_threshold, a.cpu_step)
        outcome["desktop_fermo_s"] = expected_vals
        print("           %s the desktop %s before the scene (%.1f s)"
              % ("⭐" if stopped else "⚠",
                 "is still" if stopped else ("did NOT become still within the ceiling"
                                          if stopped is False else
                                          "I do not know whether it is still"), expected_vals))
        display, err = turn_on_scene(chi, a)
        if display is None:
            outcome["reason"] = "scena-non-accesa"
            outcome["why"] = "I could not switch on the scene: %s" % err
            client.kill()
            close_client(30)
            clear_out(chi, a.wait_clearout)
            return outcome
        # ── 5. ⭐⭐ WE WAIT FOR THE FRAMES TO REALLY ARRIVE ─────────────────
        #    ⛔ And not a fixed time: `--wait-scene` turns from a wait into a CEILING.
        #    ⚠ The moment the scene starts painting is the one that
        #      decides everything (the graft, and how many frames dirty the gross
        #      rate), and by the clock one does not know it.
        seen, cpu_al_s, how_much = wait_for_frames(
            lambda: encoder_cpu(chi, a.child_name),
            a.wait_scene, a.cpu_threshold, a.cpu_step)
        outcome["lavoro_visto"] = seen
        outcome["cpu_prima"] = cpu_al_s
        outcome["secondi_prima"] = seconds_in_view(
            how_much, a.cpu_step, a.cpu_threshold, cpu_al_s) if seen else None
        print("           %s the frames arrive: the encoder burns %s "
              "CPU/s (I demand %.2f) after %.1f s · scene in view before "
              "the graft: at most %s s"
              % ("⭐" if seen else "⚠",
                 "unknown" if cpu_al_s is None else "%.2f" % cpu_al_s,
                 a.cpu_threshold, how_much,
                 "unknown" if outcome["secondi_prima"] is None
                 else "%.1f" % outcome["secondi_prima"]))
        # ⭐ PHASE 12 (19 Sep 2026) — A BREATH BEFORE THE GRAFT, and it is COUNTED.
        #   `[M]` On KDE the SIGSTOP 2 s after the encoder's work fell
        #   halfway through the opening of the window (scene at 58 % of the colour and a
        #   black strip): the last frame was not «the scene» and the mesh
        #   did not judge.  ⇒ We wait `--trigger-respite` more, on every
        #   desktop, ⛔ and it is ADDED to the seconds of scene in view: the rate is
        #   gross (`enough_window`), and an uncounted breath would be a
        #   fault that stops being visible without saying so.
        if seen and a.trigger_respite > 0:
            time.sleep(a.trigger_respite)
            if outcome["secondi_prima"] is not None:
                outcome["secondi_prima"] += a.trigger_respite
            print("           ⭐ breath before the graft: %.1f s (scene in view, "
                  "counted: at most %.1f s)" % (a.trigger_respite,
                                               outcome["secondi_prima"] or -1))
        outcome["scena_viva_prima"] = scene_is_alive(chi, a.app)
    else:
        # ⚠ THE NEGATIVE CONTROL: nothing is switched on, and we look at a
        #   desktop that has no reason to change.  ⛔ Here the wait
        #   stays by the clock: there is no frame to wait for, and
        #   waiting for one would mean waiting for the ceiling for nothing.
        time.sleep(a.wait_scene)

    # ── 6. ⛔⛔ THE REAL FAULT, AND NOW IT IS AT THE RIGHT MOMENT OF THE STORY ─
    #    ⭐ The scene is on, the program moving it is alive, and the
    #      frames were seen arriving: **then** the encoder dies.
    #    ⇒ It is this question the mesh exists to ask — «do the frames
    #      stop?» — and before 27 August 2026 it was not being asked.
    if mode == "still":
        amount, who_stopped, taken = stop_encoder(chi, a.child_name)
        outcome["stopped_count"] = amount
        outcome["pkill_ha_preso"] = taken
        print("           ⛔ `pkill -STOP` %s · processes in state T: %d%s"
              % ("took hold" if taken else "⚠ did NOT take hold", amount,
                 (" (%s)" % ", ".join(sorted(set(who_stopped))[:6]))
                 if who_stopped else ""))

    # ⭐⭐ AND THE WINDOW GROWS AS MUCH AS NEEDED — 22 September 2026.
    #
    # ⛔ The rate of this mesh is GROSS: inside the window there are also the
    #    frames born BEFORE the graft, and as long as they alone are enough to keep it
    #    above the threshold the fault cannot bite.  `enough_window()` knows
    #    from which second on it can bite, and until now the bench said so **after
    #    having measured**, with a «relaunch with --fault-window N» that nobody
    #    relaunched: in the net a 3 came out — «I could not look» — and the
    #    mesh no longer certified anything.
    # ⚠ Before 22 Sep the defect was not visible for a wrong reason: the
    #   `pkill` pattern also stopped the scene's BROWSER, so the
    #   scene itself stopped moving and the rate collapsed much earlier.
    #   ⇒ With the graft cured, this came to the surface.
    # ⭐ The number is not invented: it is the one the bench printed in its
    #   advice (`needs × 2 + 10`), and it is always said out loud.
    window = a.window
    if mode == "still":
        needs = enough_window(outcome.get("secondi_prima"), healthy_rate,
                                  a.minimum_rate)
        requested_manually = abs(a.fault_window - FAULT_WINDOW) > 0.001
        if needs is not None and window <= needs and not requested_manually:
            window = min(needs * 1.25 + 10.0, FAULT_WINDOW_CAP)
            print("           ⭐ the window grows to %.0f s: with the healthy "
                  "rate of %.1f/s and %.1f s of scene in view before "
                  "the graft, below %.0f s the fault could not "
                  "bite%s"
                  % (window, healthy_rate, outcome.get("secondi_prima") or -1,
                     needs,
                     " (⚠ CEILING: and it is not enough)"
                     if window >= FAULT_WINDOW_CAP
                     and needs * 1.25 + 10.0 > FAULT_WINDOW_CAP else ""))
        elif needs is not None and window <= needs:
            print("           ⚠ the window asked by hand (%.0f s) is "
                  "shorter than the %.0f s that would be needed: I leave it as you "
                  "asked, and the judgement will say it could not bite"
                  % (window, needs))

    # ⭐⭐ HERE THE MEASURING WINDOW OPENS, and the instant is MARKED — it is the
    #     denominator of the rate, and a denominator nobody marks is a
    #     number that says whatever happens.
    window_start = time.time()
    cpu_opening = client_cpu(client.pid)
    time.sleep(window)
    # ⛔ AND THE CLIENT'S WORK IS READ AGAIN **BEFORE** THE CLIENT DIES:
    #    afterwards, `/proc/<pid>` is no longer there and the measure would be «I do not know» because of
    #    a defect of the bench.
    outcome["cpu_finestra"] = work_per_second(
        cpu_opening, client_cpu(client.pid), time.time() - window_start)

    # ── 8. the client finishes ─────────────────────────────────────────────
    queue = close_client(int(stays) + 240)
    fine = time.time()
    said = client_frame_count(queue or "")
    admitted = was_admitted(queue)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ AND THE SCENE IS LOOKED AT AGAIN **NOW**, at the end — not only at the start.
    #
    # ⚠ The first draft looked at it only once, right after `--wait-scene`,
    #   and then declared at the top «alive from start to end».  ⛔ But the pairs
    #   that decide the verdict are the LAST frames, i.e. minutes later:
    #   a scene that dies halfway leaves a declared colour on the screen
    #   (so the guard on the colours passes) and identical frames ⇒ ⛔ **red
    #   for the product for something of the browser**, which is exactly the scenario
    #   the file says it fears.
    # ⇒ It is demanded alive **at the end**; and if it was alive at the start and not at the end,
    #   it is said, because it is a different diagnosis from «it never started».
    # ═══════════════════════════════════════════════════════════════════════
    if not a.still_scene:
        outcome["scena_viva"] = scene_is_alive(chi, a.app)

    if admitted is not True:
        last = "?"
        for line in reversed((queue or "").strip().splitlines()):
            line = line.strip()
            if line and not line.startswith("=="):
                last = line[:90]
                break
        outcome["reason"] = "cliente-non-ammesso"
        outcome["why"] = ("the client %s: %s"
                           % ("was not ADMITTED" if admitted is False
                              else "said NOTHING", last))
        clear_out(chi, a.wait_clearout)
        return outcome

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ THE DENOMINATOR OF THE RATE IS **ONLY THE WINDOW IN WHICH THE SCENE
    #     WAS MOVING**, and the choice must be stated in full because it decides the direction
    #     of the error — `LEZIONI.md` §1.50, a comment that describes a
    #     quantity different from the one the code governs.
    #
    #   numerator    ⚠ ALL the frames of the stream, those of the birth of the
    #                desktop included: the client writes a single file, and from an
    #                H.264 stream without timestamps one cannot cut a piece.
    #   denominator  ⭐ only from when the scene was on the screen to the end.
    #
    # ⇒ The rate is thus **OVERESTIMATED**, i.e. ⛔ **this check is
    #   OPTIMISTIC**: it can let a collapse through, it cannot invent one.
    #   ⚠ It is the right direction in which to err — a false red switches off the net
    #     (§1.3 of the phase document) — ⛔ but it is also the reason why the
    #     rate is NOT the check that decides: that is «consecutive
    #     frames are different», which looks only at the tail of the grab.
    #
    # ⚠⚠ And **by how much** it overestimates I DO NOT KNOW, and it must be said instead of inventing
    #    a limit.  Outside the window the desktop is still (`[M]` 0.03
    #    frames/s, phase 9 §3.1), ⛔ **but the application is being born
    #    inside it**, and a window that opens draws plenty.  ⇒ The extra
    #    term is «what the compositor drew while the scene was
    #    starting», and nobody has measured it: `[?]`.
    # ⭐ The three numbers with which that `[?]` is closed — frames, seconds, rate —
    #   the mesh prints at every round.
    #
    # ⚠ If the stage was born at the limit of the ceiling, the window shortens but
    #   is NOT falsified: it stays what it was, and the rate stays its own.
    # ═══════════════════════════════════════════════════════════════════════
    seconds = max(1.0, fine - window_start)
    outcome["seconds"] = round(seconds, 1)

    if not os.path.exists(stream) or os.path.getsize(stream) == 0:
        # ⛔ No byte on the wire.  ⚠ With the STILL scene this is an expected
        #   result; with the scene in motion it is the canary dying, and
        #   `judge_stream` says so.
        g = judge_stream([], seconds, a.still_scene, a.minimum_rate)
        outcome.update({k: g[k] for k in ("state", "reason", "why",
                                        "frames", "ritmo", "coppie",
                                        "diverse", "minima", "massima")})
        clear_out(chi, a.wait_clearout)
        return outcome

    # ⛔ The ceiling FOLLOWS the work it governs, instead of standing still while
    #    `--wait-stage` grows (`LEZIONI.md` §1.17).
    listing, expired = extract_frames(
        stream, os.path.join(workdir, "frames"),
        a.width, a.height, max(900.0, stays * 4.0))
    outcome["listing"] = listing
    if expired:
        outcome["reason"] = "estrazione-troncata"
        outcome["why"] = ("the decoder did not finish: the list of "
                           "frames is TRUNCATED, and a truncated list has "
                           "the look of a lean grab ⇒ I do not judge")
        clear_out(chi, a.wait_clearout)
        return outcome
    # ⭐ And the two counts are compared BEFORE judging, not after: the client
    #   says how many frames it took from the wire, the decoder how many it
    #   pulled out.  ⛔ If the second is much lower, the stream was
    #   lost along the way and the rate is not the product's.
    if said and listing and len(listing) < said * QUOTA_EXTRACTS:
        outcome["frames"] = len(listing)
        outcome["reason"] = "estrazione-magra"
        outcome["why"] = ("the client declares %d frames and the "
                           "decoder pulled out %d (less than "
                           "%.0f%%): the stream was lost along the way, and the "
                           "rate would not be the product's"
                           % (said, len(listing), QUOTA_EXTRACTS * 100))
        clear_out(chi, a.wait_clearout)
        return outcome

    # ── ⭐ IS THE DECLARED SCENE THE ONE I AM LOOKING AT? ──────────────────
    #    ⛔ If it is not, we do not judge: we would say red to the product for
    #       something of the browser.
    if listing and not a.still_scene:
        last_png = listing[-1]
        g = referee.judge(last_png)
        fa = reader.color_fraction(last_png, SCENE_A, TOLERANCE)
        fb = reader.color_fraction(last_png, SCENE_B, TOLERANCE)
        outcome["frazione_scena"] = (None if (fa is None or fb is None)
                                   else max(fa, fb))
        if g is not None and g["verdict"] in ("nero", "quasi-nero"):
            outcome["reason"] = "desktop-nero"
            outcome["why"] = ("the last frame is «%s»: the session "
                               "had nothing to show, and this is not a "
                               "judgement on C3" % g["verdict"])
            clear_out(chi, a.wait_clearout)
            return outcome
        if outcome["frazione_scena"] is None or outcome["frazione_scena"] < SCENE_FRACTION:
            outcome["reason"] = "scena-non-mia"
            outcome["why"] = (
                "the scene I declared is NOT on the screen (its colours "
                "cover %s, I demand %.0f%%) ⇒ I cannot demand that "
                "the frames change: the scene alive? %s"
                % ("unknown" if outcome["frazione_scena"] is None
                   else "%.1f%%" % (outcome["frazione_scena"] * 100),
                   SCENE_FRACTION * 100,
                   "yes" if outcome["scena_viva"] else "⛔ NO"))
            clear_out(chi, a.wait_clearout)
            return outcome
        if not outcome["scena_viva"]:
            outcome["reason"] = "scena-morta"
            outcome["why"] = (
                "the program that moves the scene %s: I cannot say whether "
                "the image was frozen or whether there was nothing left to move"
                % ("DIED between the start and the end"
                   if outcome["scena_viva_prima"] else "never started"))
            clear_out(chi, a.wait_clearout)
            return outcome

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE TAIL OF THE DELIVERED FRAMES — and it is ALWAYS looked at, even when
    #    the verdict will come out «crollati».
    #
    # ⛔ `judge_stream` compares the pairs **only if the rate holds**: with the
    #    encoder stopped it exits with «crollati» first, and that number it
    #    never computes.  ⚠ But it is exactly the number that says whether the fault fell
    #    at the right moment of the story: if the LAST frames that arrived —
    #    those of the instant the encoder died — were **different
    #    from each other**, then the scene was there and moving, and what happened
    #    afterwards is that the frames STOPPED.
    # ⇒ If instead they were identical, the graft fell on a still desktop, and the
    #   round proved nothing: outcome 3, not a red (`test_stopped`).
    # ═══════════════════════════════════════════════════════════════════════
    # ⚠ And the list can be **None** (the decoder pulled out
    #   nothing): `None` is not an empty list, and slicing it would be a fault
    #   of the bench with the face of a fault of the product.
    m_queue = (changing_pairs(listing[-(a.examined_pairs + 1):],
                                  NOISE_THRESHOLD, a.pair_threshold)
              if listing else None)
    if m_queue is not None:
        outcome["coda_coppie"] = m_queue["coppie"]
        outcome["coda_diverse"] = m_queue["diverse"]
        outcome["coda_frazione"] = m_queue["frazione"]

    g = judge_stream(listing, seconds, a.still_scene, a.minimum_rate,
                          a.pair_fraction, a.examined_pairs,
                          NOISE_THRESHOLD, a.pair_threshold)
    outcome.update({k: g[k] for k in ("state", "reason", "why", "frames",
                                    "ritmo", "coppie", "diverse", "minima",
                                    "massima")})
    if said is not None and outcome["frames"] is not None \
            and said != outcome["frames"]:
        # ⚠ It is not a verdict: it is information.  The client counts the
        #   frames taken from the wire, ffmpeg those that were decoded:
        #   ⛔ if the two numbers diverge a lot, the stream has holes and whoever
        #      diagnoses must know it.
        outcome["why"] += (" ⚠ (the client declares %d of them, the decoder "
                            "pulled out %d)" % (said, outcome["frames"]))
    clear_out(chi, a.wait_clearout)
    return outcome


def _n(x):
    return "unknown" if x is None else x


def show(e):
    face = {"cambia": "YES", "congelata": "NO ", "crollati": "NO ",
              "non-lo-so": "?  "}[e["state"]]
    print("  %-8s %-6s %s  %s" % (e["who"], e["modo"], face, e["why"]))
    print("           screens: %s · stage in %s s · frames %s in %s s "
          "(real window, ⚠ not `--window`) · different pairs %s/%s"
          % (_n(e["schermi"]), _n(e["palco_s"]), _n(e["frames"]),
             _n(e["seconds"]), _n(e["diverse"]), _n(e["coppie"])))
    # ⭐⭐ THE MARGIN IS ALWAYS PRINTED, as C5 does: it is the number that warns BEFORE
    #    a threshold becomes a false red, and the first draft computed it
    #    and threw it away.
    # ⭐ AND WHERE THE JUDGED FRAMES ARE: on a red, without the path, there
    #   is nothing to look at without already knowing where to search.  ⚠ And they stay there
    #   on purpose — the next round of the same tenant redoes them.
    if e["elenco"]:
        print("           the judged frames (the last %d of %d): %s"
              % (min(len(e["elenco"]), EXAMINED_PAIRS + 1), len(e["elenco"]),
                 os.path.dirname(e["elenco"][0])))
    print("           ⭐ margin on the pair threshold: the weakest %s · "
          "the strongest %s (threshold %.0f%%) · scene on the screen %s · alive "
          "at the end %s"
          % ("unknown" if e["minima"] is None else "%.2f%%" % (e["minima"] * 100),
             "unknown" if e["massima"] is None else "%.2f%%" % (e["massima"] * 100),
             PAIR_THRESHOLD * 100,
             "unknown" if e["frazione_scena"] is None
             else "%.1f%%" % (e["frazione_scena"] * 100),
             _n(e["scena_viva"])))


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ THE THREE JOINTS — and they live in PURE functions so that `--certify` tests them.
#
# ⛔⛔ It is the piece `LEZIONI.md` §1.52 was born for: *«C9's certification
#     tested the judge, C13's the reading of the log; the defect
#     was in the JOINT between the two — in the exit code, which belongs to neither
#     of the two trades»*.  ⇒ Here the exit code with the grafted fault is
#     **inverted**, and from it `11-gancio.sh` derives `ha_visto_il_guasto`.
# ═══════════════════════════════════════════════════════════════════════════
TEST_DID_NOT_RUN = (
    "palco-non-nato", "scena-non-accesa", "cliente-non-ammesso",
    "estrazione-troncata", "estrazione-magra", "desktop-nero",
    "scena-non-mia", "scena-morta", "inquilino-non-creato", "niente-elenco",
    "niente-secondi", "niente-coppie")


def _healthy_does_not_hold(healthy, r):
    """The guard common to the two acceptance tests.  Returns the outcome, or `None` if it holds.

    ⛔⛔ THE RED HEALTHY CONTROL EXITS **3**, AND NOT 1 — and it is a correction.
    The first draft exited 1.  ⚠ But `11-gancio.sh` reads a grafted round
    BACKWARDS: `1` ⇒ `ha_visto_il_guasto: false`.  ⇒ ⛔ A REAL regression of the
    product, happening precisely during the round with the grafted fault, would have
    made C13 write *«the net can no longer say red»* — i.e. the defect
    of §1.52 produced by the cure of §1.52.
    ⭐ The real red is already there and it is given by the round WITHOUT the fault, which in the family
      runs right before: here there is no need to repeat it, there is a need not to lie.
    """
    if healthy["state"] == "non-lo-so":
        r.append("⚠ the healthy round could not look (%s): I cannot say "
                 "whether the fault would have been seen" % (healthy["reason"] or "?"))
        r.append("   ⇒ and this does NOT accuse the mesh (§4.5: «graft not "
                 "judged»)")
        return 3
    if healthy["state"] != "cambia":
        r.append("⛔⛔ THE HEALTHY CONTROL IS RED: %s" % healthy["why"])
        r.append("    ⇒ this round does NOT measure the fault — it measures a red that "
                 "is already there on its own (§1.45).")
        r.append("    ⚠ And the outcome is 3 and not 1: saying «the fault was not "
                 "seen» would be an accusation")
        r.append("      against the net for a regression of the PRODUCT. ⇒ The real "
                 "red is given by the round without the fault.")
        return 3
    return None


def test_repeated(healthy, scarred, threshold_margin=THRESHOLD_MARGIN,
                         pair_threshold=PAIR_THRESHOLD):
    """`--repeated-frame`.  Returns `(esito, [lines])`, outcome BACKWARDS.

    ⛔⛔ AND HERE THERE IS A THING THAT MUST BE SAID, because a reviewer found it and
         was right: **the defacement, on its own, cannot fail.**  If the healthy
         round is green, repeating the same frame N times necessarily gives
         zero different pairs: it is arithmetic, and it is already certified in 0.3
         seconds by `--certify`.  ⇒ A round on the real thing that asserted **only**
         that would spend a whole session for a bit already known — i.e.
         `LEZIONI.md` §1.44 disguised as an acceptance test.

    ⭐ That is why this acceptance test demands **one more thing, and that one can
      really fail**: that the **weakest** consecutive pair of the healthy
      round sits at least `threshold_margin` times above the threshold.
      ⇒ It is a measurement of the WORLD — how lively the real scene is, seen
        through the product, after the encoding — and if one day the scene
        became timid (a browser skipping frames, an encoding that
        flattens) **this number would drop before the mesh starts giving
        false reds**.  ⚠ It is the same thing C5 does with the margin of the RMS.
    """
    r = []
    outcome = _healthy_does_not_hold(healthy, r)
    if outcome is not None:
        return outcome, r
    if scarred is None:
        r.append("⚠ I do not have a list of frames to deface: I cannot "
                 "graft the fault (outcome 3, not a red)")
        return 3, r

    r.append("  healthy   : %s" % healthy["why"])
    r.append("  defaced   : %s" % scarred["why"])
    r.append("")
    if scarred["state"] == "non-lo-so":
        # ⛔ «I do not know» is NOT «the fault was not seen»: the first
        #    frame could be unreadable, and accusing the net for a
        #    broken PNG would be the same form of error as §1.47.
        r.append("⚠ the defaced one could not be judged (%s): I cannot "
                 "say whether the fault would have been seen" % (scarred["reason"] or "?"))
        r.append("   ⇒ outcome 3, not a red.")
        return 3, r
    if scarred["state"] != "congelata":
        r.append("⛔⛔ THE GRAFTED FAULT WAS NOT SEEN: the same "
                 "frame repeated passes for a scene that changes.")
        r.append("    ⇒ this mesh does not look in the right place.")
        return 1, r
    if not (healthy["diverse"] and scarred["diverse"] == 0):
        r.append("⛔ the verdict changed but the NUMBER did not: different pairs "
                 "%s ⇒ %s." % (_n(healthy["diverse"]), _n(scarred["diverse"])))
        return 1, r
    r.append("  ⭐ measurable difference, on the SAME data: the different pairs "
             "go from %s to %s out of %s"
             % (healthy["diverse"], scarred["diverse"], healthy["coppie"]))

    # ⭐⭐ AND THE MEASURE THAT CAN REALLY FAIL: how lively the real scene is.
    minima = healthy["minima"]
    if minima is None:
        r.append("⚠ I do not know how much the weakest pair of the healthy round "
                 "changed: without that number this acceptance test asserts nothing "
                 "about the world (outcome 3).")
        return 3, r
    times = minima / pair_threshold if pair_threshold else 0.0
    r.append("  ⭐ and the real scene is lively: the weakest pair changes "
             "%.2f%% of the pixels, %.1f times the threshold (I demand %.1f)"
             % (minima * 100, times, threshold_margin))
    if times < threshold_margin:
        r.append("⛔ THE SCENE IS TOO TIMID, or the threshold is too close: "
                 "the weakest pair")
        r.append("   sits at %.1f times the threshold instead of %.1f. ⇒ Today the "
                 "verdict is still right," % (times, threshold_margin))
        r.append("   ⚠ but tomorrow a false red is one step away, and this mesh "
                 "warns BEFORE instead of after.")
        return 1, r
    r.append("")
    r.append("⭐ THE GRAFTED FAULT WAS SEEN — this mesh CAN catch "
             "the frozen image,")
    r.append("   ⭐ and the real scene sits well clear of the threshold.")
    return 0, r


def test_stopped(healthy, broken, quota=FAULT_QUOTA, gross_quota=GROSS_QUOTA,
                      fraction_pairs=PAIR_FRACTION,
                      rate_minimum=MINIMUM_RATE):
    """`--stopped-encoder`.  Returns `(esito, [lines])`, outcome BACKWARDS.

    ⛔⛔ AND SINCE 27 AUGUST 2026 THIS ACCEPTANCE TEST ALSO DEMANDS **THAT THE FAULT
        FELL AT THE RIGHT MOMENT OF THE STORY** — because before it did not
        demand it, and the round exited **3** for the wrong honest reason.

    The meaning of the fault is only one: ⭐ *the scene is there and moving, then the
    encoder dies* ⇒ **the frames stop**.  ⇒ For that round to
    count, three things must be true that are MEASURED and that can be missing:

      1. ⭐ the frames had been seen arriving        (`lavoro_visto`)
      2. ⭐ the LAST frames delivered were different from each other — i.e. the
         scene was moving at the instant the encoder died
         (`coda_frazione`)
      3. ⭐ the window was long enough that the frames born BEFORE
         the graft were not enough to make the stream look alive
         (`enough_window`)

    ⛔ If one is missing, the outcome is **3**: what was believed was not grafted,
       and saying «the fault was not seen» would be an accusation against the net for an
       acceptance test that did not run.
    """
    r = []
    outcome = _healthy_does_not_hold(healthy, r)
    if outcome is not None:
        return outcome, r
    if broken["state"] == "non-lo-so":
        r.append("⚠ the round with the fault could not look (%s): I cannot "
                 "say whether the fault would have been seen" % (broken["reason"] or "?"))
        r.append("   ⇒ outcome 3, not a red (§4.5).")
        return 3, r
    # ⚠⚠ THE FAULT'S SIGNATURE — and if it is missing the outcome is **3**, not a red.
    if not broken["stopped_count"] or broken["pkill_ha_preso"] is False:
        r.append("⚠ the injection stopped nothing: `pkill -STOP` %s, and the "
                 "processes of «%s» in state T are %s."
                 % ("took hold" if broken["pkill_ha_preso"] else "did NOT take hold",
                    broken["who"], _n(broken["stopped_count"])))
        r.append("   ⇒ whatever verdict comes out is NOT the fault I believed I had "
                 "grafted (§1.52).")
        r.append("   ⇒ outcome 3, not a red.")
        return 3, r

    # ── ⭐⭐ THE MOMENT OF THE GRAFT — the cure of 27 August 2026 ───────────
    if broken.get("lavoro_visto") is not True:
        r.append("⚠ before stopping the encoder I NEVER saw the frames "
                 "arrive (the encoder was burning %s CPU/s)."
                 % _n(broken.get("cpu_prima")))
        r.append("   ⇒ I stopped an encoder that was not delivering: "
                 "it is not «the frames stop»,")
        r.append("     it is «they had never started». ⛔ Outcome 3, not a red.")
        return 3, r
    if broken.get("coda_frazione") is None:
        r.append("⚠ I could not compare the last delivered frames with each other: "
                 "I do not know whether the scene was moving")
        r.append("   at the instant the encoder died. ⇒ Outcome 3.")
        return 3, r
    if broken["coda_frazione"] < fraction_pairs:
        r.append("⛔ THE LAST FRAMES DELIVERED WERE IDENTICAL TO EACH OTHER "
                 "(%s different pairs out of %s, %.0f%%):"
                 % (_n(broken["coda_diverse"]), _n(broken["coda_coppie"]),
                    broken["coda_frazione"] * 100))
        r.append("   the graft fell when the scene was not moving yet "
                 "⇒ this round does NOT prove «the frames stop»,")
        r.append("   it proves «there was nothing to stop». ⛔ Outcome 3, not a "
                 "red — and the graft must be moved, not the judge softened.")
        return 3, r
    r.append("  ⭐ the graft fell at the right moment: the encoder "
             "was working (%.2f CPU/s) and the last frames delivered"
             % (broken.get("cpu_prima") or 0.0))
    r.append("     were different from each other (%s pairs out of %s, %.0f%%) ⇒ the scene "
             "was there and moving, **then** the encoder died."
             % (_n(broken["coda_diverse"]), _n(broken["coda_coppie"]),
                broken["coda_frazione"] * 100))

    # ── ⭐ WAS THE WINDOW LONG ENOUGH? ─────────────────────────────────────
    #    ⛔ The rate is GROSS: with the frames born before the graft a dead
    #       stream can look alive, and then the round could not bite.
    needs = enough_window(broken.get("secondi_prima"), healthy["ritmo"],
                              rate_minimum)
    if needs is not None:
        r.append("  ⭐ the window: %s s watched, and for this box more than "
                 "%.0f were needed (%.1f s of scene in view before "
                 "the graft × %.1f/s healthy ÷ %.1f/s demanded)"
                 % (_n(broken["seconds"]), needs, broken["secondi_prima"],
                    healthy["ritmo"], rate_minimum))
        if broken["seconds"] is None or broken["seconds"] <= needs:
            r.append("⚠ THE WINDOW WAS TOO SHORT for this rate: the "
                     "frames born before the graft are enough on their own")
            r.append("   to keep the gross rate above the threshold ⇒ the fault "
                     "could not bite, and I did not test it.")
            r.append("   ⛔ Outcome 3, not a red. ⇒ Relaunch with "
                     "`--fault-window %d`." % int(needs * 1.25 + 10))
            return 3, r

    if broken["state"] == "cambia":
        r.append("⛔⛔ THE GRAFTED FAULT WAS NOT SEEN: with the encoder "
                 "stopped the frames arrive anyway.")
        return 1, r

    # ── ⭐⭐ THE MEASURABLE DIFFERENCE, and the CLEAN one comes before the gross one ─
    ls = healthy.get("cpu_finestra")
    lr = broken.get("cpu_finestra")
    if ls is None or lr is None:
        r.append("⚠ I do not know how much the client worked inside the window "
                 "(healthy %s · fault %s): without that number" % (_n(ls), _n(lr)))
        r.append("   the difference is not measured, it is only a changed "
                 "verdict. ⇒ Outcome 3.")
        return 3, r
    r.append("  ⭐⭐ CLEAN measurable difference (numerator and denominator "
             "both inside the window):")
    r.append("     the client's work goes from %.2f to %.2f CPU/s, i.e. "
             "%.1f%% of the healthy one (I allow at most %.0f%%)"
             % (ls, lr, (lr / ls * 100) if ls else 0.0, quota * 100))
    if ls <= 0 or lr > ls * quota:
        r.append("⛔ the verdict changed but the client still works: the "
                 "frames did not really stop,")
        r.append("   and an acceptance test like this does not certify the net (§1.52).")
        return 1, r

    rs = healthy["ritmo"] or 0.0
    rr = broken["ritmo"] or 0.0
    r.append("  ⭐ and the GROSS difference, which carries inside it the frames born "
             "before the graft: the rate goes from %.2f/s to %.2f/s"
             % (rs, rr))
    r.append("     ⇒ %.2f/s fewer, i.e. %.1f%% of the healthy one (here I allow "
             "at most %.0f%%, ⛔ and not %.0f%%: the number is dirty "
             "on purpose)"
             % (rs - rr, (rr / rs * 100) if rs else 0.0, gross_quota * 100,
                quota * 100))
    if rs <= 0 or rr > rs * gross_quota:
        r.append("⛔ the verdict changed but the NUMBER hardly did: the fault "
                 "bit little, and an acceptance test like this does not certify the net.")
        return 1, r
    r.append("")
    r.append("⭐ THE GRAFTED FAULT WAS SEEN — this mesh CAN say red,")
    r.append("   ⭐ and for the right reason: the scene was moving, the "
             "encoder died, and THE FRAMES STOPPED.")
    return 0, r


def test_still_scene(e):
    """⚠⚠ THE NEGATIVE CONTROL — and now it ASSERTS something.

    ⛔ The first draft exited **3 anyway**, and a reviewer pointed out that
       that way it did not distinguish *«the bench ran and the desktop was really
       still»* from *«nothing started»*: a broken container gave the same
       exit code as the successful control.  ⇒ Five minutes of session for
       a bit that could not vary — `LEZIONI.md` §1.44.

    ⭐ Now it demands **three things together**, and each one can be missing:
         · the stage was born        (⇒ the round really happened)
         · the client was admitted
         · and the verdict is «I do not know» **for the right reason**, i.e. the
           reason `scena-ferma` and not another
       ⇒ `0` = the negative control HOLDS: on a still scene this mesh does not give
         red, and I verified it on a round that really happened.
       ⇒ `1` = ⛔ on a still scene the mesh gave a verdict: **it is broken**.
       ⇒ `3` = the round did not happen, and so I checked nothing.
    """
    r = []
    if e["state"] in ("congelata", "crollati"):
        r.append("⛔⛔ THE NEGATIVE CONTROL FAILED: with the STILL scene "
                 "this mesh gave RED (%s)." % e["state"])
        r.append("    ⇒ `[M]` phase 9 §3.1: on a still scene 0.03 "
                 "frames/s come out and it is a RESULT, not a defect.")
        r.append("    ⛔ A mesh that gives red there is a generator of false "
                 "reds, and §1.3 says how it ends.")
        return 1, r
    if e["reason"] != "scena-ferma":
        r.append("⚠ the round did not reach the control: it stopped earlier "
                 "(%s)." % (e["reason"] or "?"))
        r.append("   ⇒ %s" % e["why"])
        r.append("   ⛔ So I verified NOTHING: outcome 3, and it must not be "
                 "mistaken for a successful control.")
        return 3, r
    r.append("⭐ THE NEGATIVE CONTROL HOLDS — the round happened (stage born, "
             "client admitted),")
    r.append("   the scene was still, and this mesh ⛔ did NOT give red: it "
             "said «I do not know» and said why.")
    r.append("   ⭐ And the round leaves the number with which `--minimum-rate` is calibrated: "
             "%s frames in %s s."
             % (_n(e["frames"]), _n(e["seconds"])))
    return 0, r


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-user", default="c3u")
    p.add_argument("--password", default="provanic2026")
    p.add_argument("--port", type=int, default=8511)
    p.add_argument("--address", default="127.0.0.1")
    p.add_argument("--client", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--scene", default="/opt/remotix/11-c3-scena.html",
                   help="⭐ THE DECLARED SCENE: it is this file that decides what "
                        "moves and by how much")
    p.add_argument("--trigger-respite", type=float, default=2.0,
                   help="seconds between «the encoder works» and the graft, COUNTED "
                        "in the scene in view: on KDE the window finishes "
                        "appearing (phase 12)")
    p.add_argument("--app", default="firefox-esr",
                   help="⚠ today the browser, because it is the only program in the "
                        "box that can paint a scene we decide. "
                        "⛔ To be moved as soon as there is another one")
    p.add_argument("--args", default="--kiosk file://%(pagina)s")
    p.add_argument("--child-name", default="remotix",
                   help="what the tenant's process that encodes and delivers "
                        "is called, in the command line")
    p.add_argument("--workdir", default="/var/lib/rete11/c3")
    p.add_argument("--width", type=int, default=128)
    p.add_argument("--height", type=int, default=72)
    # ⭐ 60 s, and the number comes from a MEASUREMENT: `[M]` 27 August 2026, inside the
    #   cured GNOME box the stage is born in **2.1÷4.2 s** ⇒ 60 s are more
    #   than ten times the worst measured.  ⛔ The 200 s of before were a
    #   prudent number chosen when the phenomenon seemed to last ~97 s — which
    #   was a fault of the box, later cured (`LEZIONI.md` §1.54).
    # ⚠ And here it is not a deadline but an ADDEND of `--stay`: every second
    #   too many is a second thrown away for every tenant, not a margin.
    p.add_argument("--wait-stage", type=float, default=60.0,
                   help="⛔ CEILING TO RECALIBRATE: [M] (C1, 27 Aug 2026, not mine) "
                        "95-101 s in the GNOME box because of a defect of the "
                        "BOX; with that cured, ~2 s ⇒ put back to ~20")
    p.add_argument("--wait-scene", type=float, default=30.0,
                   help="⛔ CEILING TO RECALIBRATE [?]: how long the scene is given to "
                        "be on the screen")
    p.add_argument("--window", type=float, default=45.0,
                   help="⚠ the MINIMUM of seconds in which the scene in "
                        "motion is watched — NOT the real window. ⛔ The client stays "
                        "attached `--wait-stage + --wait-scene + "
                        "--window + --tail` seconds in all, decided at "
                        "launch: if the stage is born early, the real window is "
                        "longer than this number. ⭐ The REAL one the mesh "
                        "prints at every round, and it is the denominator of the rate")
    # ⭐⭐ THE WINDOW OF THE ROUND WITH THE FAULT IS LONGER, and the reason is a
    #    calculation, not a taste: `enough_window`.  The rate is GROSS, ⇒ the
    #    frames born between the instant the scene started painting
    #    and the instant of the graft arrive **even with the fault**.  For them not
    #    to be enough to make a dead stream look alive, the window must be
    #    long with respect to them.
    # ⚠ `[?]` 90 s: with ~6 s of scene in view before the graft it holds up to
    #   a healthy rate of ~58/s, i.e. ⭐ beyond the rough reference of 39/s
    #   (phase 9 §3.1).  ⛔ And the mesh CHECKS the calculation afterwards with the real numbers
    #   of the round: if the window was not enough it says so, and exits 3.
    # ⚠ And it holds for **both** rounds of the acceptance test, the healthy and the faulted:
    #   two different windows would make the two rates not comparable.
    p.add_argument("--fault-window", type=float, default=FAULT_WINDOW,
                   help="⭐ the window of the TWO rounds of `--stopped-encoder`: "
                        "measuring an absence takes time")
    p.add_argument("--tail", type=float, default=10.0)
    # ⭐ The live signal «the frames are arriving»: see the top.
    p.add_argument("--cpu-threshold", type=float, default=CPU_THRESHOLD,
                   help="⭐ how much CPU per second the ENCODER must "
                        "burn for us to say that the frames "
                        "ARRIVE. [?] and the mesh always prints the real value")
    p.add_argument("--cpu-step", type=float, default=CPU_STEP,
                   help="every how many seconds the client's work is looked at. "
                        "⛔ short on purpose: it is the scene time that ends up in the "
                        "gross rate even with the fault")
    p.add_argument("--wait-clearout", type=float, default=60.0)
    p.add_argument("--minimum-rate", type=float, default=MINIMUM_RATE,
                   help="⛔ [?] wide on purpose: it separates «a trickle» from «nothing», "
                        "it does NOT judge smoothness")
    p.add_argument("--pair-fraction", type=float, default=PAIR_FRACTION)
    p.add_argument("--examined-pairs", type=int, default=EXAMINED_PAIRS)
    p.add_argument("--pair-threshold", type=float, default=PAIR_THRESHOLD,
                   help="how many pixels must change for two frames "
                        "to be «different». [?] to be recalibrated in the box")
    p.add_argument("--threshold-margin", type=float, default=THRESHOLD_MARGIN,
                   help="⭐ how many times the WEAKEST pair of the healthy round "
                        "must sit above the threshold. ⛔ It is what makes the "
                        "`--repeated-frame` acceptance test not empty")
    p.add_argument("--still-scene", action="store_true",
                   help="⚠ THE NEGATIVE CONTROL: no scene is switched on. "
                        "⛔ In this mode the mesh CANNOT give red")
    p.add_argument("--repeated-frame", action="store_true",
                   help="⛔ GRAFTED FAULT: the in-memory copy of the list is defaced "
                        "by putting the first frame in it N times. "
                        "The outcome is read BACKWARDS")
    p.add_argument("--stopped-encoder", action="store_true",
                   help="⛔ GRAFTED FAULT: SIGSTOP to the tenant's process "
                        "that delivers. The outcome is read BACKWARDS")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()

    if a.certify:
        sys.exit(certify())

    how_many_faults = sum([a.repeated_frame, a.stopped_encoder])
    if how_many_faults > 1:
        print("⛔ one fault at a time: if two are grafted one no longer knows "
              "which one bit")
        sys.exit(2)
    if a.still_scene and how_many_faults:
        print("⛔ «still scene» is the NEGATIVE CONTROL, not a fault: with the "
              "scene still there is nothing to graft")
        sys.exit(2)
    # ⛔⛔ THE GUARDS ON THE NUMBERS — `LEZIONI.md` §1.44: a threshold set to zero
    #     from the command line is a predicate that can no longer fail, and
    #     `--certify` would not notice (it certifies the CONSTANTS).
    if not 0 < a.pair_fraction <= 1:
        print("⛔ --pair-fraction %s: outside 0..1 this mesh could no "
              "longer give either red or green" % a.pair_fraction)
        sys.exit(2)
    if a.pair_threshold <= 0 or a.minimum_rate <= 0:
        print("⛔ --pair-threshold and --minimum-rate must be greater than "
              "zero: at zero neither of the two could give red any more")
        sys.exit(2)
    if a.examined_pairs < 2:
        print("⛔ --examined-pairs %d: with fewer than two pairs there is nothing "
              "to compare" % a.examined_pairs)
        sys.exit(2)
    if a.cpu_threshold <= 0 or a.cpu_step <= 0:
        print("⛔ --cpu-threshold and --cpu-step must be greater than zero: at "
              "zero «the frames arrive» would always be true, even on a "
              "dead desktop")
        sys.exit(2)
    # ⭐⭐ AND THE WINDOW OF THE ACCEPTANCE TEST WITH THE ENCODER STOPPED IS LONGER — for
    #    both rounds, the healthy and the faulted, or the two rates would not be
    #    comparable.  ⛔ The reason is a calculation and lives in `enough_window`.
    if a.stopped_encoder:
        a.window = a.fault_window
    if os.geteuid() != 0:
        print("⛔ it must be run as administrator: it has to create new tenants")
        sys.exit(2)

    referee, dove_g = desktop_judge()
    if referee is None:
        print("⛔ I cannot find the image judge (10-f1-testimone.py) next to me")
        print("   ⇒ I could not look")
        sys.exit(3)
    reader, dove_l = color_reader()
    if reader is None:
        print("⛔ I cannot find the colour reader (11-c8-…py) next to me")
        print("   ⇒ I could not look")
        sys.exit(3)
    for desc, dove in (("the test client", a.client),
                      ("the declared scene", a.scene)):
        if not os.path.exists(dove):
            print("⛔ I cannot find %s: %s" % (desc, dove))
            print("   ⇒ I could not look")
            sys.exit(3)
    for program in (a.app, "ffmpeg", "wayland-info", "runuser"):
        if sh("command -v %s" % program).returncode != 0:
            print("⛔ the box does not have %s" % program)
            print("   ⇒ I could not look")
            sys.exit(3)
    try:
        import numpy, PIL  # noqa: F401
    except ImportError:
        print("⛔ numpy or Pillow is missing: I cannot compare two frames")
        print("   ⇒ I could not look")
        sys.exit(3)

    os.makedirs(a.workdir, exist_ok=True)

    # ⭐ BEFORE any `create`: `create` does `userdel -r`, and from that moment the
    #   owner of `/tmp/mozilla` would be a NUMBER instead of a name — i.e.
    #   I would no longer recognise it as mine.
    rest = clear_out_my_leftover(a.base_user)

    print("== C3 — the frames arrive, and the scene CHANGES ==")
    print("   port %d · scene %s · application «%s»"
          % (a.port, os.path.basename(a.scene), a.app))
    print("   yardstick: rate ≥ %.2f/s (rough reference [M] %.1f/s, phase 9 §3.1 "
          "⇒ %.0f%%) · at least %.0f%% of consecutive pairs different"
          % (a.minimum_rate, REFERENCE_FPS,
             a.minimum_rate / REFERENCE_FPS * 100, a.pair_fraction * 100))
    print("   ⚠ the rate is GROSS and therefore OPTIMISTIC: it is not the check that "
          "decides (see the top)")
    print("   imported judges: %s · %s"
          % (os.path.basename(dove_g), os.path.basename(dove_l)))
    print("   provisioning: the cure of src/provisiona.sh, imported from C2, for every "
          "tenant I create")
    if rest:
        print("   %s" % rest)
    print("   ceilings (⛔ to recalibrate on the real thing): stage %.0f s · scene %.0f s · "
          "window %.0f s" % (a.wait_stage, a.wait_scene, a.window))
    if a.still_scene:
        print("   ⚠ NEGATIVE CONTROL «still scene»: ⛔ this mesh in "
              "this mode CANNOT give red, and it will say why")
    if a.repeated_frame:
        print("   ⛔ GRAFTED FAULT: «the same frame repeated» — it defaces "
              "the IN-MEMORY COPY, the stream on disk is not touched")
        print("   ⭐ healthy control and fault run on the SAME data: the "
              "difference cannot come from a different round")
    if a.stopped_encoder:
        print("   ⛔ GRAFTED FAULT: SIGSTOP to the tenant's «%s» process"
              % a.child_name)
        print("   ⭐ and with it runs a HEALTHY CONTROL, or one could not "
              "distinguish «the fault bit» from «it was already red»")
        print("   ⭐⭐ and the graft falls AFTER the scene was seen moving "
              "(cure of 27 Aug 2026): before, it died on an empty desktop")
        print("   ⚠ window %.0f s for both rounds: measuring "
              "an absence takes time (see `enough_window`)" % a.window)
    print()

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ «REPEATED FRAME»: a single tenant, and the same data is judged
    #    TWICE.
    # ═══════════════════════════════════════════════════════════════════════
    if a.repeated_frame:
        e = one_round("%s1" % a.base_user, None, a, referee, reader)
        show(e)
        print()
        scarred = judge_stream(scar_repeating(e["elenco"]),
                                      e["seconds"] or 1.0, False,
                                      a.minimum_rate, a.pair_fraction,
                                      a.examined_pairs, NOISE_THRESHOLD,
                                      a.pair_threshold) if e["elenco"] else None
        outcome, lines = test_repeated(e, scarred, a.threshold_margin,
                                            a.pair_threshold)
        for line in lines:
            print(line)
        sys.exit(outcome)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔ «ENCODER STOPPED»: two tenants, one healthy and one faulted.
    # ═══════════════════════════════════════════════════════════════════════
    if a.stopped_encoder:
        healthy = one_round("%s1" % a.base_user, None, a, referee, reader)
        show(healthy)
        broken = one_round("%s2" % a.base_user, "still", a, referee, reader,
                        healthy_rate=healthy.get("ritmo"))
        show(broken)
        print()
        outcome, lines = test_stopped(healthy, broken, FAULT_QUOTA,
                                         GROSS_QUOTA, a.pair_fraction,
                                         a.minimum_rate)
        for line in lines:
            print(line)
        sys.exit(outcome)

    # ═══════════════════════════════════════════════════════════════════════
    # THE NORMAL ROUND — and the NEGATIVE CONTROL, which now asserts something
    # ═══════════════════════════════════════════════════════════════════════
    e = one_round("%s1" % a.base_user, None, a, referee, reader)
    show(e)
    print()
    if a.still_scene:
        outcome, lines = test_still_scene(e)
        for line in lines:
            print(line)
        sys.exit(outcome)
    if e["state"] == "cambia":
        print("⭐ GREEN — the frames arrive and the scene CHANGES.")
        sys.exit(0)
    if e["state"] == "non-lo-so":
        print("⚠ NOT JUDGING — %s" % e["why"])
        print("  ⛔ And this is not a green: it is an outcome of its own (§4.5).")
        sys.exit(3)
    print("⛔⛔ RED — %s" % e["why"])
    sys.exit(1)


if __name__ == "__main__":
    main()
