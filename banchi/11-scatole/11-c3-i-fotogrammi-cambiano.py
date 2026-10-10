#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c3 — ⭐⭐ «THE FRAMES ARRIVE, AND THE SCENE CHANGES»
===========================================================================

    python3 11-c3-i-fotogrammi-cambiano.py --porta 8511
    python3 11-c3-i-fotogrammi-cambiano.py --porta 8511 --scena-ferma
    python3 11-c3-i-fotogrammi-cambiano.py --porta 8511 --fotogramma-ripetuto
    python3 11-c3-i-fotogrammi-cambiano.py --porta 8511 --codificatore-fermo
    python3 11-c3-i-fotogrammi-cambiano.py --certifica

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

⚠ **AND THIS IS THE MEANING OF `--scena-ferma`**: it is the **negative control**, and
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
  ⇒ ⭐ Now `--scena-ferma` **asserts**, and demands three things together:

      · the stage was born        (⇒ the round really happened)
      · the client was admitted
      · and the verdict is «I do not know» **for the right reason** (reason
        `scena-ferma`), not for another one

    ⇒ `0` the negative control HOLDS · `1` ⛔ on a still scene the mesh gave
      a verdict, i.e. it is broken · `3` the round did not happen and I checked
      nothing.
  ⭐ And that round leaves the number with which `--ritmo-minimo` is calibrated: how many
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
       · ⇒ The `--ritmo-minimo` threshold is **wide on purpose**: it separates *«a trickle
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

  `--fotogramma-ripetuto`   ⭐ THE FROZEN IMAGE FAULT.  The REAL grab is
                            taken and **the in-memory copy** of the list of
                            frames is defaced: in place of the sequence
                            N copies of the first one are put.  ⛔ The stream on
                            disk is not touched — it is the same shape C9 uses
                            (`--togli-nome`), and the healthy control and the fault
                            run on the **same data**.  ⇒ A single tenant.
                            ⛔⛔ AND HERE ONE THING MUST BE SAID that a reviewer
                            found and was right about: **the defacement, on its own, cannot
                            fail** — if the healthy one is green, repeating the
                            same frame necessarily gives zero different
                            pairs.  It is arithmetic, and it is already proved by
                            `--certifica` in three tenths of a second.  ⇒ A round
                            on the real thing that asserted only that would spend a
                            session for a bit already known: `LEZIONI.md` §1.44
                            disguised as an acceptance test.
                            ⭐ That is why that round demands **one more thing that
                            can really fail**: that the **weakest** consecutive
                            pair of the healthy round sits at least
                            `MARGINE_SOGLIA` times above the threshold.  ⇒ It is a
                            measurement of the WORLD — how lively the real scene is
                            after the encoding — and if one day it dropped, it would
                            be seen **before** the mesh starts giving
                            false reds.  ⚠ It is what C5 does with the margin
                            of the RMS.

  `--codificatore-fermo`    ⛔ THE REAL FAULT, on the product.  ⭐⭐ **As soon as the
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
         `--fotogramma-ripetuto`  the different pairs collapse to **zero**
         `--codificatore-fermo`   ⭐⭐ the **work of the client inside the
                                  window** drops below a **SHARE** of
                                  the healthy one (`QUOTA_GUASTO`, a tenth).
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
                                  (`QUOTA_LORDA`).

⚠ And each fault also demands its own **signature**, or it is not that fault:
   with `--codificatore-fermo` at least one process of the tenant must
   really be in state **T** (stopped).  ⛔ If it is not, the injection touched
   nothing and the red — if there is one — belongs to someone else.

⭐⭐ AND `--codificatore-fermo` DEMANDS ONE MORE THING, since 27 August 2026:
   that the fault fell **at the right moment of the story**.  Three facts, and
   each one is measured and can be missing:
     · the frames had been seen ARRIVING before the graft;
     · the LAST frames delivered were **different from each other** — i.e. the
       scene was moving at the instant the encoder died;
     · the window was long enough that the frames born before
       the graft were not enough on their own to make the stream look alive
       (`finestra_bastante`, and the count is redone **with the real numbers of the round**).
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

  `--attesa-palco 60`    how long to wait for the compositor to announce a
                         `wl_output`.  `[M]` (C1's measurement, 27 August 2026,
                         **not mine**) in the GNOME box: 98.0 · 101.0 · 95.5 s
                         ⇒ maximum 101.0.  ⛔ And that delay is the **box's**
                         (`polkit` that does not start, `Contenitore.gnome` §6-bis),
                         not the product's: with that cured the stage is born in ~2 s
                         as in the other three boxes ⇒ **put back to ~20 s**.
                         ⚠ The mesh always prints how long it really took.
  `--attesa-scena 30`    how long the scene is given to be on the screen.
                         `[?]` — the first start of the browser in a cold
                         box exceeds 25 s (`[M]` C8, 26 Aug 2026).
  `--finestra 45`        how many seconds the scene in motion is watched.
  `--ritmo-minimo 4.0`   `[?]` ⇒ ~10 % of the rough reference.  See above:
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
    gives red, look at the PNG it leaves in `--lavoro` before believing it.
  · ⚠ **It is not blind to the program**: like C2, today it uses `firefox-esr`, the only
    program in the box that can paint a scene we decide.
    ⇒ `--applicazione` and `--argomenti` exist to move it elsewhere.
  · ⛔ **It does not look at audio** (that is C5) nor at input (that is C4).

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ I looked: the frames arrive and the scene CHANGES
     (with the grafted fault: ⭐ **the fault was seen**)
     (with `--scena-ferma`: ⭐ **the negative control holds**)
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

QUI = os.path.dirname(os.path.abspath(__file__))

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE YARDSTICK, DECLARED HERE AND PRINTED IN EVERY OUTCOME
# ═══════════════════════════════════════════════════════════════════════════

# ⭐ The two colours of the declared scene — ⛔ **the same as `11-c3-scena.html`**.
#    If someone changes one there and not here, this mesh will say «the scene
#    I declared is not on the screen» ⇒ **3**, not a red for the product.
SCENA_A = (0x00, 0x00, 0xFF)      # blue
SCENA_B = (0xFF, 0xFF, 0x00)      # yellow
# ⛔ The tolerance per channel: same quantity and same value as C8 — the
#    deviation of a declared colour after the same path (compositor →
#    capture → H.264 4:2:0 → client).  ⚠ It is not a borrowed ceiling
#    (`LEZIONI.md` §1.45): it is the same number for the same thing.
# ⛔⛔ BUT IT IS NOT CALIBRATED, and saying so would be §1.50.  `--certifica` crosses it **at the
#     edge** — ±48 must still be the scene, ±49 not — on **synthetic**
#     images, which have never seen either the 4:2:0 encoding or a
#     colour profile.  ⇒ It tests that the comparison falls where it says it falls,
#     not that 48 is enough.
# ⚠⚠ And there is one more reason to distrust it here: C8 is calibrated on **magenta**,
#    C3 asks for **pure blue** `#0000FF`, which has luma 0.07 and is the worst case
#    of chroma subsampling.  ⇒ `[?]`, and it is calibrated by looking at the fraction
#    the mesh prints at the first green round.
TOLLERANZA = 48
# ⛔ How much of the screen must be one of the two colours for us to say «the
#    declared scene is the one I am looking at».  ⚠ The black band covers 20 %,
#    plus the plate: 0.40 is prudent on the low side on purpose.  `[?]`
FRAZIONE_SCENA = 0.40

# ⭐⭐ THE ROUGH REFERENCE — `[M]` phase 9 §3.1, ⛔ **on the real iron, not in the
#     box**: 39.67 and 39.00 frames/s on two scenes in motion, against
#     **0.03** on a still scene.  ⇒ The value used is the lower of the two.
RIFERIMENTO_FPS = 39.0
# ⛔ Below how many frames per second we say «collapsed».  `[?]` ~10 % of the
#    reference: wide on purpose (see the top), and to be recalibrated in the box.
RITMO_MINIMO = 4.0

# ⛔ When two frames are DIFFERENT — two numbers, and both are needed.
#    · below `SOGLIA_RUMORE` levels on a channel, a pixel «did not change»:
#      it is the quantisation noise of the encoding, not movement.  `[?]`
#    · and the changed pixels must be at least `SOGLIA_COPPIA` of the image,
#      or a blinking cursor would be enough to declare a dead scene alive.
SOGLIA_RUMORE = 12
SOGLIA_COPPIA = 0.01
# ⛔ How many pairs must be different for the scene to «change».  ⚠ The declared
#    scene is made to make them ALL differ (the band moves at every
#    frame): 0.50 leaves half a margin for the cadence of the capture.  `[?]`
FRAZIONE_COPPIE = 0.50
# How many pairs are looked at, at the end of the grab.
COPPIE_ESAMINATE = 60

# ⭐⭐ With the grafted fault: how much the CLEAN measure must COLLAPSE for us to
#   be able to say «the fault bit» instead of «the verdict changed».
#   `LEZIONI.md` §1.52.
# ⛔⛔ AND SINCE 27 AUGUST 2026 THE CLEAN MEASURE IS NO LONGER THE RATE, but **the work
#     of the client inside the window** — see `QUOTA_LORDA` below and
#     `finestra_bastante`.  The rate is gross, i.e. it carries inside it the
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
#   above `--ritmo-minimo` (4.0/s) to be green, ⇒ with the fault one demands
#   less than 0.4/s, which is the rate of a still desktop ([M] 0.03/s, phase 9 §3.1).
QUOTA_GUASTO = 0.10

OUTPUT_MINIMI = 1
FIRMA_OUTPUT = re.compile(r"interface:\s*'wl_output'")

# ⛔⛔ AND THE ADMISSION SIGNATURE IS A WHOLE LINE, NOT A WORD.
#    `[R]` `01-b3-cliente.py:1615` writes «   AMMESSO after 1023 ms» when it goes
#    well, and «CONGEDO instead of AMMESSO: …» / «expected AMMESSO, arrived …»
#    when it goes badly — ⛔ all three on **stdout** (`:2560`) ⇒ `"AMMESSO" in
#    testo` would be **true in all three cases**: a predicate that cannot
#    say no (`LEZIONI.md` §1.44), precisely in the cases it exists to catch.
# ⭐⭐ Since 27 August 2026 the rule lives in `11-c1…py` and it lives there **only
#     once**, for all nine meshes (§1.47): see `e_stato_ammesso()`.

# ⭐ How WIDE the weakest pair of the healthy round must sit with respect to the
#   threshold, for us to be able to say the scene is lively enough to prove
#   something.  ⛔ It is the number that makes the round with the «repeated frame»
#   fault NOT EMPTY (see the top): without it, that round asserts only things
#   already certified.  ⚠ `[?]` — 2× is prudent, and it is calibrated by looking at the
#   `margine` the mesh prints at every round.
MARGINE_SOGLIA = 2.0

# ⛔ If the decoder pulls out many fewer than the client
#    declares, the stream was truncated and the count is not the
#    product's: it is «I could not look».  `[?]`
QUOTA_ESTRATTI = 0.50

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
SOGLIA_CPU = 0.10
# ⭐ Every how many seconds the client's work is looked at.  ⛔ It is short on purpose:
#   between the instant the scene starts painting and the graft lie
#   **all** the frames that later dirty the gross rate (see
#   `finestra_bastante`), ⇒ every extra second here is one more frame
#   that arrives anyway with the fault.
PASSO_CPU = 2.0

# ⛔ And the GROSS rate has a share **of its own, wider**, and the reason must be said
#    instead of hidden: its numerator also contains the frames born
#    BEFORE the window, and with the grafted fault those all remain.  ⇒ On
#    a dirty number one cannot demand the same tenth one demands
#    on a clean one: it would be a threshold that passes or does not pass depending on
#    how quick the scene was to be born.  `[?]`
# ⭐ The tenth is demanded where the measure is clean (`QUOTA_LAVORO`); here it is
#   demanded only that the gross rate dropped **a lot**, and the count of how much
#   could be expected is done by `finestra_bastante`.
QUOTA_LORDA = 0.35


def e_stato_ammesso(coda):
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
    return casa_di_c1().e_stato_ammesso(coda)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE JUDGES ARE IMPORTED, NOT REWRITTEN
#
# ⛔ Two judges that can diverge silently are worse than one
#    (`banchi/10-f1-testimone.py`).  Here two are imported:
#      `10-f1-testimone.py`  `giudica()`, to say whether an image is black
#      `11-c8-…py`           `frazione_del_colore()`, already certified, and it takes
#                            colour and tolerance as ARGUMENTS ⇒ it is used with
#                            C3's numbers without inheriting C8's
# ⭐ The third judge — «are two frames different?» — does not exist anywhere
#   else, so it is born here **and it is certified here**.
# ═══════════════════════════════════════════════════════════════════════════
def _carica(nome_file, mestieri):
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, nome_file)
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location(
            "importato_" + re.sub(r"\W", "_", nome_file), perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None, perc
        for mestiere in mestieri:
            if not callable(getattr(m, mestiere, None)):
                return None, perc
        return m, perc
    return None, ""


def giudice_del_desktop():
    return _carica("10-f1-testimone.py", ("giudica",))


def lettore_del_colore():
    return _carica("11-c8-il-secondo-apre-il-browser.py", ("frazione_del_colore",))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ THE SHARED PROVISIONING — `/tmp/mozilla`, and it lives in ONE PLACE ONLY
#
# `[M]` 27 August 2026, round `--famiglia tutto` on all four boxes,
#   binary `aa950804fed7`: C3 ⛔ **3** — «the scene I declared is NOT
#   on the screen (0.0%)».  ⚠ And the judged image said something else entirely: the
#   GNOME session was **alive and painted**, ⛔ but Firefox was stuck on the
#   **profile chooser window**.
#
# ⇒ THE CAUSE: `/home/c3u1/.cache/mozilla` -> `/tmp/mozilla`, which had stayed with
#   «c8u1» with mode 0700 — C8 and C8b, in `famiglia tutto`, run BEFORE me and
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
#   can, it moves next to `applica_la_cura`, and this line changes by itself.
# ═══════════════════════════════════════════════════════════════════════════
_MESTIERI_PROVVISTA = ("cura_della_provvista", "sgombra_il_mio_rimasuglio",
                       "certifica_la_provvista")
_PROVVISTA = None


def casa_della_provvista():
    global _PROVVISTA
    if _PROVVISTA is None:
        _PROVVISTA, _ = _carica("11-c2-una-finestra-si-apre.py",
                                _MESTIERI_PROVVISTA)
    return _PROVVISTA


def cura_della_provvista(chi):
    """⭐⭐ (done, why) — and ⛔ if it does not hold it is NOT a red: it is a **3**."""
    casa = casa_della_provvista()
    if casa is None:
        return False, ("I cannot find `11-c2-una-finestra-si-apre.py` next to me: "
                       "the provisioning cure comes from there, and ⛔ no "
                       "copy of it is made here (§1.47)")
    return casa.cura_della_provvista(chi)


def sgombra_il_mio_rimasuglio(mio_base):
    """Removes `/tmp/mozilla` ⛔ only if it was left to one of MY tenants."""
    casa = casa_della_provvista()
    if casa is None:
        return "⚠ I cannot find C2: I did not even look at /tmp/mozilla"
    return casa.sgombra_il_mio_rimasuglio(mio_base)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ C1 IS THE HOME OF THE TWO STEPS COMMON TO ALL NINE MESHES — §1.47
#
# ⛔ It is not convenience: it is that a line repeated in nine files is **nine places
#    to diverge from**, and they had already diverged.  From `11-c1-nasce-e-si-vede.py`
#    come:
#
#   · `e_stato_ammesso(coda)`   — «was the client ADMITTED?», which ⛔ is not
#        the word inside a text: the client prints it also in the TWO refusal
#        messages, and on stdout (`01-b3-cliente.py:1315`, `:1322`, `:2560`).
#   · `garantisci_i_gruppi(chi)` — the groups of the `/dev/dri` nodes, ⛔ without
#        which `[M]` the session is born BLIND (0 of 4, zero frames,
#        `fasi/10-…` §7.4) and this mesh would measure the darkness.
#
# ⛔ If C1 does not load we exit **3** and say so: ⛔ we do not silently fall back
#    on a poorer judgement.
# ═══════════════════════════════════════════════════════════════════════════
_MESTIERI_C1 = ("e_stato_ammesso", "certifica_ammissione",
                "garantisci_i_gruppi", "verdetto_gruppi", "certifica_gruppi")
_C1 = None


def casa_di_c1():
    global _C1
    if _C1 is None:
        _C1, _perc = _carica("11-c1-nasce-e-si-vede.py", _MESTIERI_C1)
    if _C1 is None:
        print("⛔ I cannot find `11-c1-nasce-e-si-vede.py` next to me, and from there")
        print("   come the admission predicate and the guarantee of the")
        print("   card's groups — which live in one place only (§1.47).")
        print("⇒ I could not look — ⛔ and it is NOT a red (§4.5).")
        sys.exit(3)
    return _C1


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ THE CARD'S GROUPS — `(esito, perche)`; `0` = it can be measured.

    ⛔ Until 27 August 2026 this mesh created the tenant with
       `usermod -aG video,render` **and did not read back**: two nailed-down names (which
       belong to ONE distribution) and no verification — E1, «written is not in
       force».  ⭐ The work is done by `attrezzi-gruppi-scheda.sh`, which reads the gids
       from the NODES and reads back comparing the numbers.  ⛔ No copy of it is made here.
    """
    return casa_di_c1().garantisci_i_gruppi(chi, prefisso)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE NEW JUDGE: «are these two frames different?»
# ═══════════════════════════════════════════════════════════════════════════
def coppie_che_cambiano(elenco, soglia_rumore=SOGLIA_RUMORE,
                        soglia_coppia=SOGLIA_COPPIA):
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
    if not elenco or len(elenco) < 2:
        return None

    precedente = None
    coppie = diverse = illeggibili = 0
    minima = None
    massima = None
    for p in elenco:
        try:
            img = np.asarray(Image.open(p).convert("RGB")).astype("int16")
        except Exception:
            illeggibili += 1
            precedente = None      # ⛔ a pair with a hole in the middle is not a pair
            continue
        if img.ndim != 3 or img.size == 0:
            illeggibili += 1
            precedente = None
            continue
        if precedente is not None and precedente.shape == img.shape:
            scarto = abs(img - precedente).max(axis=2)
            quanti = float((scarto > soglia_rumore).mean())
            coppie += 1
            if quanti >= soglia_coppia:
                diverse += 1
            minima = quanti if minima is None else min(minima, quanti)
            massima = quanti if massima is None else max(massima, quanti)
        precedente = img

    if coppie == 0:
        return None
    return {"coppie": coppie, "diverse": diverse,
            "frazione": diverse / float(coppie),
            "minima": minima, "massima": massima,
            "illeggibili": illeggibili}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE JUDGEMENT — a PURE function, so `--certifica` runs it on
#    fake frames without switching anything on.
# ═══════════════════════════════════════════════════════════════════════════
def giudica_il_flusso(elenco, secondi, scena_ferma=False,
                      ritmo_minimo=RITMO_MINIMO,
                      frazione_coppie=FRAZIONE_COPPIE,
                      coppie_esaminate=COPPIE_ESAMINATE,
                      soglia_rumore=SOGLIA_RUMORE,
                      soglia_coppia=SOGLIA_COPPIA):
    """Returns a dictionary with `stato` among:

        "cambia"     ⭐ the frames arrive and the scene changes  ⇒ green
        "congelata"     they arrive and do NOT change            ⇒ red
        "crollati"      they do not arrive, or they are a trickle ⇒ red
        "non-lo-so"  ⛔ I could not look                          ⇒ neither one
                     nor the other
    """
    # ⭐⭐ AND NEXT TO THE VERDICT THERE IS A **REASON**, which is a fact and not a
    #    sentence.  ⛔ Without it, whoever wants to know *why* «I do not know» would have to
    #    read the text of `perche` — i.e. decide on a string, which is the
    #    way a bench starts going wrong silently when someone
    #    fixes a typo.  ⇒ The acceptance test of the negative control rests on
    #    this, not on the words.
    esito = {"stato": "non-lo-so", "motivo": "", "perche": "",
             "fotogrammi": None, "ritmo": None, "coppie": None,
             "diverse": None, "frazione_coppie": None, "minima": None,
             "massima": None, "illeggibili": None}
    if elenco is None:
        esito["motivo"] = "niente-elenco"
        esito["perche"] = "I could not extract any frame from the stream"
        return esito

    n = len(elenco)
    esito["fotogrammi"] = n
    ritmo = (n / float(secondi)) if secondi and secondi > 0 else None
    esito["ritmo"] = ritmo

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
    if scena_ferma:
        esito["motivo"] = "scena-ferma"
        esito["perche"] = (
            "the scene was STILL by my choice: %d frames, rate %s. "
            "⛔ On a still scene the product delivers nothing and that is right "
            "([M] phase 9 §3.1: 0.03 frames/s; [R] src/figlio.c:3373) ⇒ "
            "«frozen image» and «nothing to show» here have the same "
            "look, and I do not tell them apart"
            % (n, "unknown" if ritmo is None else "%.2f/s" % ritmo))
        return esito

    # ── 1. the poorest canary ──────────────────────────────────────────────
    if n == 0:
        esito["stato"] = "crollati"
        esito["motivo"] = "zero-fotogrammi"
        esito["perche"] = ("no frame arrived, and the scene was in "
                           "motion: it is the canary dying")
        return esito

    # ── 2. the rate, against the rough reference ───────────────────────────
    if ritmo is None:
        esito["motivo"] = "niente-secondi"
        esito["perche"] = "I do not know over how many seconds to count: I do not compute a rate"
        return esito
    if ritmo < ritmo_minimo:
        esito["stato"] = "crollati"
        esito["motivo"] = "ritmo-crollato"
        esito["perche"] = ("%d frames in %.0f s = %.2f/s, below the %.2f/s "
                           "demanded (rough reference [M] %.1f/s, phase 9 §3.1 "
                           "⇒ %.0f%% of the reference)"
                           % (n, secondi, ritmo, ritmo_minimo, RIFERIMENTO_FPS,
                              ritmo / RIFERIMENTO_FPS * 100))
        return esito

    # ── 3. ⭐ the check that decides: are consecutive ones different? ───────
    coda = elenco[-(coppie_esaminate + 1):]
    m = coppie_che_cambiano(coda, soglia_rumore, soglia_coppia)
    if m is None:
        esito["motivo"] = "niente-coppie"
        esito["perche"] = ("I could not compare the frames with each other "
                           "(fewer than two readable, or numpy/Pillow missing)")
        return esito
    esito.update({"coppie": m["coppie"], "diverse": m["diverse"],
                  "frazione_coppie": m["frazione"],
                  "minima": m["minima"], "massima": m["massima"],
                  "illeggibili": m["illeggibili"]})
    if m["frazione"] < frazione_coppie:
        esito["stato"] = "congelata"
        esito["motivo"] = "congelata"
        esito["perche"] = ("⛔ FROZEN IMAGE: only %d pairs out of %d are "
                           "different (%.0f%%, I demand %.0f%%) — the "
                           "frames arrive and they are always the same"
                           % (m["diverse"], m["coppie"], m["frazione"] * 100,
                              frazione_coppie * 100))
        return esito

    esito["stato"] = "cambia"
    esito["motivo"] = "cambia"
    # ⭐⭐ AND THE MARGIN IS ALWAYS PRINTED, even when it is green — it is the only thing
    #    that warns BEFORE a threshold becomes a false red.  ⚠ It is what
    #    C5 does (`11-c5…py`: *«the mesh always prints the margin»*), and the first
    #    draft of C3 computed the number and threw it away.
    esito["perche"] = ("%d frames in %.0f s = %.2f/s (%.0f%% of the "
                       "rough reference) · %d pairs out of %d are different · "
                       "⭐ the weakest pair changes %.2f%% of the pixels, "
                       "i.e. %.1f times the threshold (%.0f%%)"
                       % (n, secondi, ritmo, ritmo / RIFERIMENTO_FPS * 100,
                          m["diverse"], m["coppie"], (m["minima"] or 0) * 100,
                          (m["minima"] or 0) / soglia_coppia,
                          soglia_coppia * 100))
    return esito


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE CLIENT'S WORK — PURE functions, so `--certifica` crosses them
#    without switching anything on.
# ═══════════════════════════════════════════════════════════════════════════
def cpu_dalla_riga(testo, tick=100.0):
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
    if not testo or ")" not in testo or not tick:
        return None
    campi = testo.rsplit(")", 1)[1].split()
    if len(campi) < 13:
        return None
    try:
        return (int(campi[11]) + int(campi[12])) / float(tick)
    except (ValueError, ZeroDivisionError):
        return None


def lavoro_al_secondo(prima, dopo, secondi):
    """⭐ How much CPU per second between two readings.  ⛔ `None` = I do not know.

    ⚠ And it is never allowed below zero: a process reborn with the
      same pid would give a negative number, which is not a measurement.
    """
    if prima is None or dopo is None or not secondi or secondi <= 0:
        return None
    return max(0.0, (dopo - prima) / float(secondi))


def cpu_del_cliente(pid):
    """The CPU seconds of process `pid`, read now.  `None` if unknown."""
    try:
        with open("/proc/%d/stat" % pid, "rb") as f:
            testo = f.read().decode("utf-8", "replace")
    except OSError:
        return None
    return cpu_dalla_riga(testo, float(os.sysconf("SC_CLK_TCK")))


def somma_lavoro(testo, nome):
    """⭐ PURE: the CPU seconds of the processes whose command contains `nome`.

    Reads the output of `ps -o times=,args=`.
    ⛔ Returns **None** if there is not even one: *«there is no
       encoder»* and *«the encoder is not working»* are two opposite things, and
       this project has already paid for confusing them.
    ⚠ And **only** those with `nome` in the command line are summed: counting all the
      tenant's processes would be a predicate one level too high
      (`LEZIONI.md` §1.44), the same defect as `ferma_il_codificatore`.

    ⛔⛔ AND «has `nome` in the command line» IS NOT ENOUGH — 22 September 2026.
        The scene's browser opens on `file:///opt/remotix/11-c3-scena.html`
        ⇒ it too has the word `remotix`, and its work ended up in the
        encoder's sum: the measure that decides WHEN to graft the fault
        counted the browser's consumption.  ⚠ The test below did not catch it
        because the fake browser line did not name the real folder.
    ⇒ The **name of the executable** (`argv[0]`, without path) is compared, not
      a substring of the line.
    """
    if not testo:
        return None
    totale = None
    for riga in testo.splitlines():
        pezzi = riga.split(None, 1)
        if len(pezzi) < 2:
            continue
        argv0 = os.path.basename(pezzi[1].split(None, 1)[0])
        # ⚠ The product's child RENAMES ITSELF — `remotix-figlio --figlio-interno
        #   …` — so «equal to the name» is not enough: the name followed by
        #   `-` or `:` also counts, which is how processes give themselves a title.  ⛔ And the
        #   reverse does not count: `firefox-esr` never becomes `remotix`.
        if argv0 != nome and not argv0.startswith(nome + "-") \
           and not argv0.startswith(nome + ":"):
            continue
        try:
            secondi = int(pezzi[0])
        except ValueError:
            continue
        totale = secondi if totale is None else totale + secondi
    return None if totale is None else float(totale)


def cpu_del_codificatore(chi, nome):
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
    r = sh("ps -u %s -o times=,args=" % chi, secondi=30)
    return somma_lavoro(r.stdout or "", nome)


def secondi_in_vista(quanto, passo, soglia, cpu_al_s):
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
    if quanto is None or cpu_al_s is None or not cpu_al_s or cpu_al_s <= 0:
        return None
    if passo is None or soglia is None or passo <= 0 or soglia < 0:
        return None
    return max(float(quanto), float(passo))


# ⭐ The window ASKED for the two «encoder stopped» rounds, and its
#   ceiling.  ⛔ The right number is not one: it depends on the box's rate, and
#   `finestra_bastante()` computes it.  This is only the starting point.
FINESTRA_GUASTO = 90.0
# ⚠ And a ceiling is needed: a very slow box would ask for a window that
#   never ends, and a bench that never ends is a bench that gets switched off.
FINESTRA_GUASTO_TETTO = 400.0


def finestra_bastante(secondi_prima, ritmo_sano, ritmo_minimo=RITMO_MINIMO):
    """⭐⭐ HOW LONG THE WINDOW MUST BE for the fault to be able to BITE.

    ⛔⛔ And this is the thing that on 27 August 2026 was missing, and it is the reason why
        the graft sat at the wrong place in the story.

    The rate is **gross**: in the numerator there are ALL the frames of the stream,
    including those born before the window opened; in the denominator there is
    only the window.  ⇒ With the encoder stopped the numerator is not zero: it is
    `secondi_prima × ritmo_sano`, i.e. what the scene did in view between
    the instant it started painting and the instant of the graft.

    ⇒ For the mesh to be able to say «collapsed» it takes:

        secondi_prima × ritmo_sano / WINDOW  <  ritmo_minimo

    ⭐ Returns the seconds of window needed.  ⛔ `None` if unknown (and
       then no number is faked).
    """
    if secondi_prima is None or ritmo_sano is None or not ritmo_minimo:
        return None
    if secondi_prima <= 0 or ritmo_sano <= 0 or ritmo_minimo <= 0:
        return None
    return secondi_prima * ritmo_sano / float(ritmo_minimo)


def aspetta_che_il_desktop_si_fermi(leggi, tetto, soglia=SOGLIA_CPU,
                                    passo=PASSO_CPU):
    """⭐ PHASE 12 (19 Sep 2026) — BEFORE SWITCHING ON THE SCENE, the desktop STILL.

    ⛔ `[M]` On KDE the session is born with the Plasma splash screen, which
       ANIMATES for ~2.4 s: the encoder is already working, `aspetta_che_i_
       fotogrammi_arrivino` passes on the animation and not on the scene, and the
       SIGSTOP of the «encoder stopped» fault fell on black ⇒ the mesh did not
       judge (3).  ⚠ Moving the graft further on is not possible: the rate is
       GROSS (`finestra_bastante`), and more scene in view before the graft
       means a fault that can no longer be seen.
    ⭐ Instead the SWITCHING ON of the scene is moved: we wait for the encoder's work
       to drop below the threshold for a whole step — the desktop no longer
       has anything to say — and only then is it switched on.  On GNOME at mounting
       the desktop is already still ⇒ a single step, as it was.  It holds for every
       desktop, without asking which one it is.

    Returns `(fermo, secondi_attesi)` — `fermo` is `True`, `False` (ceiling
    expired: we go on SAYING SO) or `None` (work unreadable).
    """
    partito = time.time()
    prima = leggi()
    if prima is None:
        return None, 0.0
    while time.time() - partito < tetto:
        t0 = time.time()
        time.sleep(passo)
        dopo = leggi()
        quanto = lavoro_al_secondo(prima, dopo, time.time() - t0)
        prima = dopo
        if quanto is None:
            return None, round(time.time() - partito, 1)
        if quanto < soglia:
            return True, round(time.time() - partito, 1)
    return False, round(time.time() - partito, 1)


def aspetta_che_i_fotogrammi_arrivino(leggi, tetto, soglia=SOGLIA_CPU,
                                      passo=PASSO_CPU):
    """⭐⭐ WAITS FOR THE SCENE TO BE SEEN MOVING — and not a fixed time.

    ⛔ It is the step that replaces `time.sleep(--attesa-scena)`: `--attesa-scena`
       turns from a wait into a **CEILING**, and the round goes on as soon as the frames
       really arrive instead of by the clock.  `LEZIONI.md` §1.45.
    ⚠ `leggi()` returns the CPU seconds burned so far by whoever delivers, or
      `None`.  ⛔ The bytes on disk are not looked at: the frames file the
      client writes **only at the end** (`[R]` `01-b3-cliente.py:1416`),
      so during the round there is nothing to weigh.

    Returns `(visto, lavoro_al_s, secondi_attesi)` — `visto` is `True`, `False`
    (the ceiling expired) or ⛔ `None` (I could not read the work).
    """
    partito = time.time()
    prima = leggi()
    if prima is None:
        return None, None, 0.0
    migliore = 0.0
    while time.time() - partito < tetto:
        t0 = time.time()
        time.sleep(passo)
        dopo = leggi()
        quanto = lavoro_al_secondo(prima, dopo, time.time() - t0)
        prima = dopo
        if quanto is None:
            # ⛔ Whoever was delivering is no longer there, or cannot be read.
            return None, migliore, round(time.time() - partito, 1)
        migliore = max(migliore, quanto)
        if quanto >= soglia:
            return True, quanto, round(time.time() - partito, 1)
    return False, migliore, round(time.time() - partito, 1)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CERTIFICATION
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
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

    lettore, dove_l = lettore_del_colore()
    giudice, dove_g = giudice_del_desktop()
    if lettore is None or giudice is None:
        print("⛔ I cannot find (or it does not hold up) one of the two imported judges:")
        print("   10-f1-testimone.py    : %s" % (dove_g or "not found"))
        print("   11-c8-…apre-il-browser: %s" % (dove_l or "not found"))
        print("   ⇒ I could not look")
        return 3

    lav = tempfile.mkdtemp(prefix="c3cert-")
    L, A = 128, 72

    def sequenza(nome, quanti, disegna):
        """Writes `quanti` PNGs and returns their list.  `disegna(i)` -> array."""
        dove = os.path.join(lav, nome)
        os.makedirs(dove, exist_ok=True)
        fuori = []
        for i in range(quanti):
            p = os.path.join(dove, "f-%05d.png" % i)
            Image.fromarray(disegna(i)).save(p)
            fuori.append(p)
        return fuori

    def fondo(colore):
        a = np.zeros((A, L, 3), dtype="uint8")
        a[:, :] = colore
        return a

    def scena(i):
        """The declared scene: the alternating background and the scrolling band.

        ⚠ It is the synthetic copy of `11-c3-scena.html`, and the two numbers — the 3 %
          of the step and the 20 % of the width — must stay **the same**:
          if they diverge, the certification tests a scene that nobody ever puts
          on the screen.
        """
        a = fondo(SCENA_A if (i // 3) % 2 == 0 else SCENA_B)
        x = (i * 3) % 100
        c0 = int(L * x / 100.0)
        c1 = min(L, c0 + int(L * 0.20))
        a[:, c0:c1] = (10, 10, 10)
        return a

    def congelata(i):
        return scena(0)

    def rumore(i, ampiezza):
        """A fixed background with a disturbance of declared amplitude: ⭐ it serves to
        cross the NOISE threshold in both directions."""
        a = fondo(SCENA_A).astype("int16")
        # half of the image deviates by `ampiezza` on alternate frames
        if i % 2:
            a[: A // 2, :, 0] = np.clip(a[: A // 2, :, 0] + ampiezza, 0, 255)
        return a.astype("uint8")

    def macchiolina(i):
        """Changes VERY FEW pixels: ⭐ it crosses the PAIR threshold."""
        a = fondo(SCENA_A)
        a[0, (i * 3) % L] = (255, 255, 255)      # 1 pixel of 9216 = 0.01 %
        return a

    print("== certification of C3's judges ==")
    print("   desktop judge : %s" % dove_g)
    print("   colour reader : %s" % dove_l)
    print("   minimum rate %.2f/s (rough reference [M] %.1f/s) · noise ±%d "
          "per channel · pair ≥%.0f%% of the pixels · at least %.0f%% of the pairs"
          % (RITMO_MINIMO, RIFERIMENTO_FPS, SOGLIA_RUMORE, SOGLIA_COPPIA * 100,
             FRAZIONE_COPPIE * 100))
    print()
    guai = 0

    def prova(nome, ottenuto, atteso, extra=""):
        nonlocal guai
        ok = ottenuto == atteso
        if not ok:
            guai += 1
        print("  %s  %-58s  ⇒ %-10s (expected %s)%s"
              % ("OK " if ok else "NO ", nome, ottenuto, atteso,
                 ("  %s" % extra) if extra else ""))

    # ── 1. the real scene in motion ────────────────────────────────────────
    viva = sequenza("viva", 61, scena)
    e = giudica_il_flusso(viva, 2.0)
    prova("the declared scene moves", e["stato"], "cambia",
          "different pairs %s/%s" % (e["diverse"], e["coppie"]))

    # ── 2. ⭐ THE FAULT: the same frame repeated ───────────────────────────
    ferma = sequenza("ferma", 61, congelata)
    e2 = giudica_il_flusso(ferma, 2.0)
    prova("⭐ the same frame repeated ⇒ FROZEN IMAGE",
          e2["stato"], "congelata",
          "different pairs %s/%s" % (e2["diverse"], e2["coppie"]))

    # ── 3. the rate, crossed in BOTH directions ────────────────────────────
    #    61 frames in 5 s = 12.2/s (above 4.0) · in 30 s = 2.03/s (below)
    prova("the rate stays above the threshold (12.2/s)",
          giudica_il_flusso(viva, 5.0)["stato"], "cambia")
    prova("⭐ the rate COLLAPSES below the threshold (2.03/s)",
          giudica_il_flusso(viva, 30.0)["stato"], "crollati")
    prova("no frame with the scene in motion ⇒ red",
          giudica_il_flusso([], 10.0)["stato"], "crollati")

    # ── 4. ⚠⚠ THE NEGATIVE CONTROL: «still scene» must NEVER give red ──────
    prova("⚠ STILL scene and no frame ⇒ I do not know, NOT red",
          giudica_il_flusso([], 30.0, scena_ferma=True)["stato"], "non-lo-so")
    prova("⚠ STILL scene and frames all equal ⇒ I do not know, NOT red",
          giudica_il_flusso(ferma, 30.0, scena_ferma=True)["stato"], "non-lo-so")
    prova("⚠ STILL scene with a single frame ⇒ I do not know, NOT red",
          giudica_il_flusso(viva[:1], 30.0, scena_ferma=True)["stato"], "non-lo-so")

    # ── 5. the NOISE threshold, crossed in both directions ─────────────────
    sotto = sequenza("rumore-sotto", 21, lambda i: rumore(i, SOGLIA_RUMORE - 2))
    sopra = sequenza("rumore-sopra", 21, lambda i: rumore(i, SOGLIA_RUMORE + 6))
    ms = coppie_che_cambiano(sotto)
    mp = coppie_che_cambiano(sopra)
    prova("a disturbance of ±%d levels is NOISE, not movement" % (SOGLIA_RUMORE - 2),
          0 if ms is None else ms["diverse"], 0)
    prova("⭐ a disturbance of ±%d levels IS movement" % (SOGLIA_RUMORE + 6),
          0 if mp is None else mp["diverse"], 20)

    # ── 6. the PAIR threshold, crossed in both directions ──────────────────
    piccola = sequenza("macchiolina", 21, macchiolina)
    mm = coppie_che_cambiano(piccola)
    prova("one pixel changing is not a scene moving",
          0 if mm is None else mm["diverse"], 0)
    prova("⇒ and the corresponding stream is FROZEN",
          giudica_il_flusso(piccola, 1.0)["stato"], "congelata")

    # ── 7. ⛔ the «I do not know», which are neither green nor red ─────────
    prova("⛔ no list (ffmpeg produced nothing) ⇒ I do not know",
          giudica_il_flusso(None, 10.0)["stato"], "non-lo-so")
    prova("⛔ a single frame: there are no pairs ⇒ I do not know",
          giudica_il_flusso(viva[:1], 0.05)["stato"], "non-lo-so")
    manca = [os.path.join(lav, "non-ci-sono-%d.png" % i) for i in range(5)]
    prova("⛔ unreadable frames ⇒ I do not know",
          giudica_il_flusso(manca, 1.0)["stato"], "non-lo-so")
    prova("⛔ and the meter returns «I do not know», not zero",
          "unknown" if coppie_che_cambiano(manca) is None else "a number",
          "unknown")

    # ── 8. ⭐ is the DECLARED SCENE on the screen? (the imported reader) ────
    def fr(p, colore):
        return lettore.frazione_del_colore(p, colore, TOLLERANZA)

    ultimo_viva = viva[-1]
    ultimo_altro = sequenza("altro", 1, lambda i: fondo((58, 62, 70)))[0]
    prova("the declared scene IS on the screen",
          "yes" if max(fr(ultimo_viva, SCENA_A), fr(ultimo_viva, SCENA_B))
          >= FRAZIONE_SCENA else "no", "yes")
    prova("⛔ any desktop is NOT the declared scene",
          "yes" if max(fr(ultimo_altro, SCENA_A), fr(ultimo_altro, SCENA_B))
          >= FRAZIONE_SCENA else "no", "no")
    # ⭐ and the colour shifted by as much as the tolerance allows must stay «yes»
    spostato = sequenza("spostata", 1, lambda i: fondo(
        tuple(min(255, max(0, c + s)) for c, s in zip(SCENA_A, (+30, +30, -30)))))[0]
    prova("⭐ colour shifted within the tolerance ⇒ it is still the scene",
          "yes" if max(fr(spostato, SCENA_A), fr(spostato, SCENA_B))
          >= FRAZIONE_SCENA else "no", "yes")
    troppo = sequenza("troppo", 1, lambda i: fondo(
        tuple(min(255, max(0, c + s)) for c, s in zip(SCENA_A, (+120, +120, -120)))))[0]
    prova("colour shifted TOO MUCH ⇒ it is no longer the scene",
          "yes" if max(fr(troppo, SCENA_A), fr(troppo, SCENA_B))
          >= FRAZIONE_SCENA else "no", "no")

    # ── 9. ⭐⭐ AND THE PROOF OF THE «repeated frame» GRAFTED FAULT,
    #        done as it will be done on the real thing: **on the same data**.
    print()
    sano = giudica_il_flusso(viva, 2.0)
    sfregiato = giudica_il_flusso(sfregia_ripetendo(viva), 2.0)
    dimostrato = (sano["stato"] == "cambia" and sfregiato["stato"] == "congelata"
                  and sano["diverse"] > 0 and sfregiato["diverse"] == 0)
    if not dimostrato:
        guai += 1
    print("  %s  ⭐ the DEFACEMENT on the same data: different pairs from %s to %s, "
          "verdicts «%s» and «%s»"
          % ("OK " if dimostrato else "NO ", sano["diverse"],
             sfregiato["diverse"], sano["stato"], sfregiato["stato"]))

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
    b_sotto = sequenza("bordo-r-sotto", 11, lambda i: rumore(i, SOGLIA_RUMORE))
    b_sopra = sequenza("bordo-r-sopra", 11, lambda i: rumore(i, SOGLIA_RUMORE + 1))
    m1 = coppie_che_cambiano(b_sotto)
    m2 = coppie_che_cambiano(b_sopra)
    prova("a deviation of EXACTLY %d levels is still noise" % SOGLIA_RUMORE,
          0 if m1 is None else m1["diverse"], 0)
    prova("⭐ a deviation of %d levels is already movement" % (SOGLIA_RUMORE + 1),
          0 if m2 is None else m2["diverse"], 10)

    # the PAIR: how many pixels must change.  9216 pixels ⇒ 1 % = 92.16
    def blocco(i, quanti_pixel):
        a = fondo(SCENA_A)
        if i % 2:
            piatta = a.reshape(-1, 3)
            piatta[:quanti_pixel] = (255, 255, 255)
            a = piatta.reshape(A, L, 3)
        return a
    sotto = sequenza("bordo-c-sotto", 11, lambda i: blocco(i, 92))   # 0.998 %
    sopra = sequenza("bordo-c-sopra", 11, lambda i: blocco(i, 93))   # 1.009 %
    m3 = coppie_che_cambiano(sotto)
    m4 = coppie_che_cambiano(sopra)
    prova("92 pixels of 9216 (0.998 %) are NOT a change",
          0 if m3 is None else m3["diverse"], 0)
    prova("⭐ 93 pixels of 9216 (1.009 %) ARE",
          0 if m4 is None else m4["diverse"], 10)

    # the RATE, exactly astride 4.00/s: 61 frames in 15.25 s = 4.000
    prova("the rate at 4.07/s (just above the threshold) ⇒ GREEN",
          giudica_il_flusso(viva, 15.0)["stato"], "cambia")
    prova("⭐ the rate at 3.94/s (just below) ⇒ RED",
          giudica_il_flusso(viva, 15.5)["stato"], "crollati")

    # the TOLERANCE on the scene's colour, at the edge
    al_limite = sequenza("bordo-t1", 1, lambda i: fondo(
        (TOLLERANZA, TOLLERANZA, 255 - TOLLERANZA)))[0]
    oltre = sequenza("bordo-t2", 1, lambda i: fondo(
        (TOLLERANZA + 1, TOLLERANZA + 1, 255 - TOLLERANZA - 1)))[0]
    prova("⭐ colour shifted by EXACTLY ±%d ⇒ it is still the scene" % TOLLERANZA,
          "yes" if max(fr(al_limite, SCENA_A), fr(al_limite, SCENA_B))
          >= FRAZIONE_SCENA else "no", "yes")
    prova("colour shifted by ±%d ⇒ it is no longer the scene" % (TOLLERANZA + 1),
          "yes" if max(fr(oltre, SCENA_A), fr(oltre, SCENA_B))
          >= FRAZIONE_SCENA else "no", "no")

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ «WAS THE CLIENT ADMITTED?» — the word inside a text is NOT enough.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    for nome, testo, atteso in (
            ("the real line of the admitted client",
             "   AMMESSO after 1023 ms\n", True),
            ("⛔ CONGEDO instead of AMMESSO — the word is there, the sense is opposite",
             "   ⛔ RuntimeError: CONGEDO instead of AMMESSO: reason 0x03\n", False),
            ("⛔ «expected AMMESSO, arrived …» — likewise",
             "   ⛔ RuntimeError: expected AMMESSO, arrived CONGEDO\n", False)):
        prova(nome, e_stato_ammesso(testo), atteso)
    prova("⛔ the client said NOTHING ⇒ I do not know",
          "unknown" if e_stato_ammesso("") is None else "a yes or a no",
          "unknown")

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ «ARE THE FRAMES ARRIVING NOW?» — the signal that decides
    #    **when** the fault is grafted (cure of 27 August 2026).
    # ⛔ It is all in PURE functions on purpose: the moment of the graft is the thing
    #    that on 27 August 2026 was wrong, and it is not left to code that
    #    runs only inside the box.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    riga_vera = ("42 (remotix) S 1 42 42 0 -1 4194304 100 0 0 0 300 100 "
                 "5 5 20 0 3 0")
    prova("the work of a process, from /proc/<pid>/stat ⇒ 4.00 s of CPU",
          cpu_dalla_riga(riga_vera, 100.0), 4.0)
    prova("⛔ the command name WITH A SPACE does not shift the fields",
          cpu_dalla_riga("42 (a b) S 1 42 42 0 -1 4194304 100 0 0 0 300 100 "
                         "5 5 20 0 3 0", 100.0), 4.0)
    prova("⛔ the command name with a PARENTHESIS inside: the last one is cut",
          cpu_dalla_riga("42 (we)ird) S 1 42 42 0 -1 4194304 100 0 0 0 300 100 "
                         "5 5 20 0 3 0", 100.0), 4.0)
    prova("⛔ a truncated line ⇒ «I do not know», and not zero",
          cpu_dalla_riga("42 (remotix) S 1 42", 100.0), None)
    prova("⛔ no line ⇒ «I do not know», and not zero",
          cpu_dalla_riga("", 100.0), None)
    ps_vero = ("   12 /opt/remotix/remotix --sessione c3u1\n"
               "    3 /opt/remotix/remotix --sessione c3u1 --figlio\n"
               # ⛔ THE REAL LINE of the scene's browser, the one that on 22 Sep
               #    2026 ended up in the sum: the word `remotix` is in the
               #    PATH OF THE PAGE, not in the name of the program.
               "  400 /usr/lib/firefox-esr/firefox-esr --kiosk "
               "file:///opt/remotix/11-c3-scena.html\n")
    prova("⭐ the work of the ENCODER, and only its own: 12+3 ⇒ 15 s of CPU",
          somma_lavoro(ps_vero, "remotix"), 15.0)
    prova("⭐ the child that RENAMES ITSELF «remotix-figlio» counts anyway",
          somma_lavoro("    9 remotix-figlio --figlio-interno c3u2 4013 4013\n",
                       "remotix"), 9.0)
    prova("⛔ a name that starts the same but is another program does NOT count",
          somma_lavoro("    9 /usr/bin/remotixaltro --x\n", "remotix"), None)
    prova("⛔ the browser is not the encoder: it does not enter the sum",
          somma_lavoro(ps_vero, "remotix") != somma_lavoro(ps_vero, ""), True)
    prova("⛔ no process with that name ⇒ «I do not know», and ⛔ NOT zero",
          somma_lavoro(ps_vero, "kwin_wayland"), None)
    prova("⚠ a line without the time does not throw off the sum",
          somma_lavoro("nonunnumero /opt/remotix/remotix\n   7 "
                       "/opt/remotix/remotix\n", "remotix"), 7.0)
    prova("⛔ no line at all ⇒ «I do not know»", somma_lavoro("", "remotix"),
          None)

    # ── the pattern that chooses WHOM to stop ─────────────────────────────
    # ⛔ It is the line that on 22 September 2026 stopped the scene's browser
    #    for half a day: here it is tested on REAL lines, taken from `ps`.
    def prende(riga):
        return re.match(modello_del_prodotto("remotix"), riga) is not None

    prova("⭐ the child that renames itself («remotix-figlio …») IS taken",
          prende("remotix-figlio --figlio-interno c3u2 4013 4013 1920 1080 2 -"),
          True)
    prova("⭐ the binary called by path IS taken",
          prende("/opt/remotix/remotix --indirizzo 0.0.0.0 --porta 8512"), True)
    prova("⛔⛔ the SCENE'S BROWSER is not taken, and its line names "
          "«remotix»",
          prende("/usr/lib/firefox-esr/firefox-esr --kiosk "
                 "file:///opt/remotix/11-c3-scena.html"), False)
    prova("⛔ nor the shell running the search (the pkill -f trap)",
          prende("/bin/sh -c pgrep -u c3u2 -f '^(remotix|/[^ ]*/remotix)'"),
          False)
    prova("⛔ nor another program that starts the same",
          prende("/usr/bin/remotixaltro --x"), False)
    prova("the work per second between two readings (1.0 ⇒ 3.0 in 2 s) ⇒ 1.00/s",
          lavoro_al_secondo(1.0, 3.0, 2.0), 1.0)
    prova("⛔ a missing reading ⇒ «I do not know», and not zero",
          lavoro_al_secondo(None, 3.0, 2.0), None)
    prova("⛔ zero seconds between the two readings ⇒ «I do not know»",
          lavoro_al_secondo(1.0, 3.0, 0.0), None)
    prova("⚠ a backwards count is not a measurement ⇒ 0, never a negative",
          lavoro_al_secondo(5.0, 3.0, 2.0), 0.0)
    prova("⭐ the scene in view before the graft: 27 s of waiting ⇒ at most "
          "27 s (⛔ not 6.17: the old ceiling weighted on the CPU was "
          "disproved, 22 Sep 2026)",
          round(secondi_in_vista(27.0, 2.0, 0.10, 0.60), 2), 27.0)
    prova("⭐ if the frames arrive at the first try, it is only the step ⇒ 2.00 s",
          round(secondi_in_vista(2.0, 2.0, 0.10, 0.60), 2), 2.0)
    prova("⛔ without the client's work no ceiling is faked ⇒ «I do not know»",
          secondi_in_vista(27.0, 2.0, 0.10, None), None)
    prova("⭐⭐ the window needed: 6 s in view × 30/s healthy ÷ 4/s demanded "
          "⇒ 45 s",
          finestra_bastante(6.0, 30.0, 4.0), 45.0)
    prova("⛔ without the healthy rate no window is faked ⇒ «I do not know»",
          finestra_bastante(6.0, None, 4.0), None)
    prova("⛔ without the seconds in view no window is faked ⇒ «I do not know»",
          finestra_bastante(None, 30.0, 4.0), None)

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ THE THREE JOINTS — the exit codes, which are INVERTED and from which C13
    #      derives whether the net can still say red (`LEZIONI.md` §1.52).
    # ═══════════════════════════════════════════════════════════════════════
    print()

    def giro(stato, motivo="", diverse=None, coppie=None, minima=None,
             ritmo=None, fermati=None, preso=None, fotogrammi=None,
             secondi=90.0, lavoro_visto=True, coda_frazione=1.0,
             cpu_prima=0.60, cpu_finestra=0.60, secondi_prima=6.0):
        """⚠ The default values are those of a round **that holds**:
        so every case below breaks ONE thing only, and one knows which."""
        return {"stato": stato, "motivo": motivo, "perche": "(fake)",
                "diverse": diverse, "coppie": coppie, "minima": minima,
                "ritmo": ritmo, "fermati": fermati, "pkill_ha_preso": preso,
                "chi": "c3uX", "fotogrammi": fotogrammi, "secondi": secondi,
                "lavoro_visto": lavoro_visto, "coda_frazione": coda_frazione,
                "coda_diverse": 60, "coda_coppie": 60, "cpu_prima": cpu_prima,
                "cpu_finestra": cpu_finestra, "secondi_prima": secondi_prima}

    sano_ok = giro("cambia", "cambia", diverse=60, coppie=60, minima=0.08,
                   ritmo=30.0)
    congelato = giro("congelata", "congelata", diverse=0, coppie=60)
    # ⭐ The round with the fault that HOLDS: the scene was moving, the encoder
    #   died, and inside the window the client no longer worked.
    rotto_ok = giro("crollati", "ritmo-crollato", ritmo=0.4, fermati=1,
                    preso=True, cpu_finestra=0.01)
    giunti = [
        ("repeated: healthy green + defaced frozen + lively scene ⇒ 0",
         collauda_il_ripetuto(sano_ok, congelato), 0),
        ("⛔ repeated: the defacement was NOT seen ⇒ 1",
         collauda_il_ripetuto(sano_ok, giro("cambia", "cambia", 60, 60)), 1),
        ("⭐ repeated: the scene is TOO TIMID (1.2× the threshold) ⇒ 1",
         collauda_il_ripetuto(giro("cambia", "cambia", 60, 60, minima=0.012,
                                   ritmo=30.0), congelato), 1),
        ("⭐ repeated: the HEALTHY CONTROL is red ⇒ 3, ⛔ NOT 1",
         collauda_il_ripetuto(giro("congelata", "congelata", 0, 60), congelato), 3),
        ("repeated: the healthy one could not look ⇒ 3",
         collauda_il_ripetuto(giro("non-lo-so", "palco-non-nato"), congelato), 3),
        ("⭐ repeated: the DEFACED one could not be judged ⇒ 3, not 1",
         collauda_il_ripetuto(sano_ok, giro("non-lo-so", "niente-coppie")), 3),
        ("stopped: healthy green + fault collapsed + signature ⇒ 0",
         collauda_il_fermo(sano_ok, rotto_ok), 0),
        ("⛔ stopped: with the encoder stopped the frames arrive anyway ⇒ 1",
         collauda_il_fermo(sano_ok, giro("cambia", "cambia", ritmo=29.0,
                                         fermati=1, preso=True,
                                         cpu_finestra=0.01)), 1),
        ("⛔ stopped: the GROSS rate drops little (30 ⇒ 12, above the share) ⇒ 1",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=12.0, fermati=1, preso=True,
                                         cpu_finestra=0.01)), 1),
        ("⭐ stopped: the client STILL WORKS inside the window ⇒ 1",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=0.30)), 1),
        ("⚠ stopped: `pkill` took nothing ⇒ 3",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=0, preso=False)), 3),
        ("⭐ stopped: the HEALTHY CONTROL is red ⇒ 3, ⛔ NOT 1",
         collauda_il_fermo(giro("crollati", "ritmo-crollato", ritmo=0.1),
                           rotto_ok), 3),
        # ⭐⭐⭐ THE MOMENT OF THE GRAFT — the cases that on 27 August 2026 were
        #     missing, and they are the ones for which the round exited 3.
        ("⭐⭐ stopped: the frames had NEVER been seen arriving ⇒ 3, ⛔ not 1",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=0.01,
                                         lavoro_visto=False)), 3),
        ("⭐⭐ stopped: the last frames delivered were IDENTICAL "
         "(graft too early) ⇒ 3",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=0.01,
                                         coda_frazione=0.0)), 3),
        ("⭐ stopped: I do not know whether the last delivered ones changed ⇒ 3",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=0.01,
                                         coda_frazione=None)), 3),
        ("⭐⭐ stopped: the WINDOW was too short for this rate ⇒ 3, not 1",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=0.01, secondi=30.0)), 3),
        ("⭐ stopped: I do not know how much the client worked in the window ⇒ 3",
         collauda_il_fermo(sano_ok, giro("crollati", "ritmo-crollato",
                                         ritmo=0.4, fermati=1, preso=True,
                                         cpu_finestra=None)), 3),
        ("⭐ still scene: the round happened and did not give red ⇒ 0",
         collauda_la_scena_ferma(giro("non-lo-so", "scena-ferma",
                                      fotogrammi=1, secondi=60.0)), 0),
        ("⛔ still scene: the mesh gave RED ⇒ 1 (the control failed)",
         collauda_la_scena_ferma(giro("crollati", "zero-fotogrammi")), 1),
        ("⚠ still scene: the stage was not born ⇒ 3, ⛔ not a successful control",
         collauda_la_scena_ferma(giro("non-lo-so", "palco-non-nato")), 3),
    ]
    for nome, (e, _righe), atteso in giunti:
        prova(nome, e, atteso)

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
    guai_gr, quanti_gr = casa_di_c1().certifica_gruppi("C3")
    guai += guai_gr

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ THE SHARED PROVISIONING — ⛔ the case that on 27 August 2026 was missing,
    #    and for which this mesh said «I could not look» accusing the
    #    product of a fault of the bench.
    # ⚠ The cases live in C2, with the code they certify: ⛔ a copy here would be
    #   a second place to diverge from (§1.47).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    casa_pr = casa_della_provvista()
    if casa_pr is None:
        print("  NO   ⛔ I cannot find `11-c2-…py`: the provisioning cannot be certified")
        guai += 1
        quanti_pr = 0
    else:
        guai_pr, quanti_pr = casa_pr.certifica_la_provvista("C3", "c3u")
        guai += guai_pr

    print()
    if guai:
        print("⛔ C3's judges are NOT reliable: %d cases wrong" % guai)
        return 1
    print("⭐ the judges see the scene changing and catch the frozen "
          "image, the four thresholds fall where they say (at the edge),")
    print("   ⭐ «AMMESSO» is a line and not a word, ⚠ on a still scene a red "
          "never comes out, ⛔ and «I do not know» is not zero,")
    print("   ⭐⭐ and the THREE JOINTS — the exit codes of the two grafted faults and "
          "of the negative control — say 0, 1 and 3 where they must (§1.52)")
    print("   ⭐ and the CARD'S GROUPS: a tenant that cannot see makes it say "
          "«I could not look», ⛔ never red")
    # ⛔ The provisioning line is printed ONLY if the real cases ran.
    if quanti_pr >= 4:
        print("   ⭐⭐ and THE PROVISIONING: a /tmp/mozilla of another mesh I do not "
              "touch, and my tenant writes anyway — ⛔ never red")
    else:
        print("   ⚠ and THE PROVISIONING is covered ONLY halfway: the real cases "
              "need the administrator, and here I did not run them")
    print("⚠ and this certification covers THE JUDGES AND THE JOINTS, ⛔ not the "
          "real delivery of the frames nor that the five thresholds are at the "
          "right POINT (see the top)")
    return 0


def sfregia_ripetendo(elenco):
    """⭐ THE «repeated frame» GRAFTED FAULT, and it fits in one line.

    ⛔ **The in-memory copy** of the list is defaced: the stream on disk is not
       touched.  It is the same shape as C9 (`--togli-nome`), and it has the merit that
       the healthy control and the fault run **on the same data** ⇒ the difference
       cannot come from a different round.
    """
    if not elenco:
        return elenco
    return [elenco[0]] * len(elenco)


# ═══════════════════════════════════════════════════════════════════════════
# THE TERRAIN AND THE MOVES — ⚠ the same as C2, and for the same reasons
# ═══════════════════════════════════════════════════════════════════════════
def sh(comando, secondi=120):
    try:
        return subprocess.run(["/bin/sh", "-c", comando],
                              capture_output=True, text=True, timeout=secondi)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(comando, 124, "", "expired")


def quanti_schermi(testo):
    """⛔ `None` = I do not know; `0` = I asked and there is none."""
    if testo is None:
        return None
    return len(FIRMA_OUTPUT.findall(testo))


def crea(chi, parola):
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
           "printf '%s:%s\n' | chpasswd" % (chi, chi, parola))
    if r.returncode != 0:
        return False, (r.stderr or "").strip()[:120]
    e_gr, perche_gr = garantisci_i_gruppi(chi, prefisso="      ")
    if e_gr != 0:
        return False, perche_gr
    # ⭐⭐ AND THE PROVISIONING, right after the `useradd -m` that copies the skeleton:
    #    it is there that the tenant is born with `~/.cache` pointing at `/tmp`, ⇒ it is there
    #    that it is given its own.  ⛔ Before switching anything on.
    fatto_cura, perche_cura = cura_della_provvista(chi)
    if not fatto_cura:
        return False, perche_cura
    return True, ""


def sgombra(chi, attesa):
    # ⛔ First it is WOKEN UP: with `--codificatore-fermo` there is a process in state
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
    scadenza = time.time() + attesa
    while time.time() < scadenza:
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


def chiedi_al_compositore(chi):
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
           "wayland-info" % (chi, rtd, display), secondi=60)
    if r.returncode != 0 and not r.stdout:
        return None, ("wayland-info did not speak: %s"
                      % ((r.stderr or "").strip().replace("\n", " ")[:90]))
    return quanti_schermi(r.stdout), ""


def accendi_la_scena(chi, a):
    """Switches on the declared scene INSIDE the tenant's session."""
    rtd, display = il_socket_di(chi)
    if display is None:
        return None, ("in %s there is no wayland socket: there is no "
                      "compositor the scene can talk to" % rtd)
    args = a.argomenti % {"pagina": a.scena}
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
       % (chi, rtd, display, chi, a.applicazione, args, chi), secondi=30)
    return display, ""


def la_scena_e_viva(chi, applicazione):
    """⚠ It does not prove that the scene MOVES: it proves that the program that
       moves it is not dead.  ⛔ And the difference is declared at the top of the file."""
    r = sh("pgrep -u %s -f %s >/dev/null 2>&1" % (chi, applicazione))
    return r.returncode == 0


def modello_del_prodotto(nome):
    """⭐ The expression that catches the processes OF THE PRODUCT and nothing else.

    ⛔⛔ And here there are two names for the same thing, which on 22 September 2026
        cost half a day.  The child **renames itself**: `src/figlio.c:1193`
        sets `argv[0] = "remotix-figlio"`, while `comm` stays `remotix`
        because it comes from the executable (`execve(/opt/remotix/remotix, …)`).
        ⇒ `pkill -f remotix` also caught the **scene's browser**, which has
          `file:///opt/remotix/11-c3-scena.html` in its command line, and
          left it in state `T` together with its `runuser`;
        ⇒ `pkill -x remotix` is not the safe inverse: it looks at `comm`, which the
          product does not control — the day the binary changes name it no longer
          catches anything, **silently**.
    ⭐ That is why it is anchored at the START of the command line, which is the only place
      where the product sits and the browser cannot sit:
        `remotix-figlio …`      the child that renamed itself
        `/opt/remotix/remotix …`  the binary called by path
    ⚠ And the anchor also protects from itself: the command line of the shell that
      runs this search starts with `/bin/sh`, so it does not fish itself out
      (the `pkill -f` trap — see `sgombra`).
    """
    return "^(%s|/[^ ]*/%s)([ -]|$)" % (nome, nome)


def pid_del_codificatore(chi, nome):
    """The pids of the product's processes that belong to «chi».  ⛔ Never others."""
    r = sh("pgrep -u %s -f '%s'" % (chi, modello_del_prodotto(nome)))
    pid = []
    for riga in (r.stdout or "").split():
        if riga.isdigit():
            pid.append(riga)
    return pid


def ferma_il_codificatore(chi, nome):
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
    pid = pid_del_codificatore(chi, nome)
    preso = bool(pid)
    for p in pid:
        sh("kill -STOP %s 2>/dev/null" % p)
    time.sleep(1.0)
    # ⭐⭐ AND **THOSE** PIDS ARE VERIFIED, not «someone in state T»: it is the signature of the
    #     fault (`LEZIONI.md` §1.52), and a fault that could not be grafted
    #     must be able to say it was not there.
    fermati = []
    for p in pid:
        s = sh("ps -o stat=,comm= -p %s" % p)
        pezzi = (s.stdout or "").split(None, 1)
        if len(pezzi) == 2 and pezzi[0].startswith("T"):
            fermati.append(pezzi[1].strip())
    return len(fermati), fermati, preso


def estrai_i_fotogrammi(flusso, dove, larghezza, altezza, tetto=900.0):
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
           "-y %s/f-%%05d.png" % (flusso, larghezza, altezza, dove),
           secondi=tetto)
    elenco = sorted(glob.glob(os.path.join(dove, "f-*.png")))
    # ⛔⛔ AND HERE THE EXIT CODE **IS LOOKED AT**, and it is the reverse of §1.50.
    #    There the exit code had to be ignored because the work was
    #    **done** (the PNG was there and was right).  ⚠ Here an expiry leaves
    #    a **truncated** list, which looks exactly like a lean
    #    grab: ⛔ the rate would come out wrong and the mesh would say «collapsed»
    #    on a healthy session.
    return (elenco or None), (r.returncode == 124)


def quanti_fotogrammi_dice_il_cliente(coda):
    quanti = None
    for riga in coda.splitlines():
        if "[vid]" in riga and "no frame" not in riga:
            try:
                quanti = int(riga.split("[vid]", 1)[1].strip().split()[0])
            except Exception:
                pass
    return quanti


# ═══════════════════════════════════════════════════════════════════════════
# ONE ROUND
# ═══════════════════════════════════════════════════════════════════════════
def un_giro(chi, modo, a, giudice, lettore, ritmo_sano=None):
    """`modo` = None (healthy) | "fermo" (SIGSTOP to the encoder).

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
              (`aspetta_che_i_fotogrammi_arrivino`)
           6. (with the fault: ⛔ SIGSTOP **HERE**) ⇒ ⭐ the scene is there, it moves, and the
              frames are arriving: **then** the encoder dies
           7. the measuring window is opened and watched for `--finestra` seconds
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
    esito = {"chi": chi, "modo": modo or "sano", "stato": "non-lo-so",
             "perche": "", "fotogrammi": None, "ritmo": None, "coppie": None,
             "diverse": None, "palco_s": None, "schermi": None,
             "motivo": "", "scena_viva": None, "scena_viva_prima": None,
             "frazione_scena": None, "fermati": None, "pkill_ha_preso": None,
             "elenco": None, "secondi": None, "minima": None, "massima": None,
             # ⭐ the new facts of 27 August 2026 — see the order of the moves
             "lavoro_visto": None, "cpu_prima": None, "cpu_finestra": None,
             "secondi_prima": None, "coda_coppie": None, "coda_diverse": None,
             "coda_frazione": None, "finestra_pretesa": None}

    fatto, perche = crea(chi, a.parola)
    if not fatto:
        esito["motivo"] = "inquilino-non-creato"
        esito["perche"] = "I could not create «%s»: %s" % (chi, perche)
        return esito

    lavoro = os.path.join(a.lavoro, chi)
    os.makedirs(lavoro, exist_ok=True)
    flusso = os.path.join(lavoro, "presa.264")
    if os.path.exists(flusso):
        os.unlink(flusso)

    resta = a.attesa_palco + a.attesa_scena + a.finestra + a.coda
    partito = time.time()
    # ⛔⛔ AND THE CLIENT'S OUTPUT GOES INTO A FILE, NOT INTO A PIPE — and it is not
    #     style: it is a fault avoided.  This client stays on for minutes
    #     **while the bench does other things**, and with `-u` it writes without restraint.  A
    #     pipe nobody empties fills up (64 KB on Linux) and ⛔ **blocks the
    #     writer**: the client would stop halfway through a `print`, would stop
    #     keeping the session alive, and the bench would read «no frame»
    #     blaming the product.
    # ⚠ The examples do not have this problem because they use `subprocess.run`,
    #   which empties the pipes while it waits.  Here we do not wait: we work.
    detto_file = os.path.join(lavoro, "cliente.log")
    detto_fd = open(detto_file, "w")
    cliente = subprocess.Popen(
        ["python3", "-u", a.cliente,
         "--indirizzo", a.indirizzo, "--porta", str(a.porta),
         "--utente", chi, "--parola", a.parola,
         "--video-scrivi", flusso, "--resta", str(resta)],
        stdout=detto_fd, stderr=subprocess.STDOUT, text=True)

    def chiudi_il_cliente(scadenza):
        """Waits for the client to finish, and returns what it said.

        ⛔ It always returns a string: if the file cannot be read it is an
           «I could not look», and the caller sees it as «not AMMESSO».
        """
        try:
            cliente.wait(timeout=scadenza)
        except subprocess.TimeoutExpired:
            cliente.kill()
            cliente.wait()
        detto_fd.close()
        try:
            with open(detto_file, "r", errors="replace") as f:
                return f.read()
        except OSError:
            return ""

    schermi = None
    motivo = "I was never able to ask"
    scadenza = time.time() + a.attesa_palco
    while time.time() < scadenza:
        if cliente.poll() is not None:
            motivo = "the client went away before a screen was born"
            break
        schermi, motivo = chiedi_al_compositore(chi)
        if schermi is not None and schermi >= OUTPUT_MINIMI:
            esito["palco_s"] = round(time.time() - partito, 1)
            break
        schermi = None
        time.sleep(2.0)
    esito["schermi"] = schermi

    if schermi is None or schermi < OUTPUT_MINIMI:
        esito["motivo"] = "palco-non-nato"
        esito["perche"] = ("in %.0f s the compositor did not announce any "
                           "screen (%s) ⇒ there was nothing to capture"
                           % (a.attesa_palco, motivo or "?"))
        cliente.kill()
        chiudi_il_cliente(30)
        sgombra(chi, a.attesa_sgombero)
        return esito

    # ── from here down there is the switching on of the scene and — with the fault — the graft
    # ⛔⛔ AND WE STAY INSIDE A `try/finally`: between the injection and the cleanup there
    #     are minutes of waiting, and ⚠ a Ctrl-C or an exception there would leave
    #     **the tenant frozen in state T**, the client attached and the
    #     test machine dirty for whoever comes next.
    #     ⭐ The `finally` always wakes up, even when the graft never
    #       happened: waking someone who is not asleep costs nothing,
    #       forgetting it a single time does.
    #     ⚠ And the `try` sits HERE and not lower down on purpose: the graft moved
    #       down into `_il_resto_del_giro` (step 6), but the safety net that
    #       wakes it up must be wider than it.
    try:
        return _il_resto_del_giro(chi, modo, a, giudice, lettore, esito,
                                  cliente, chiudi_il_cliente, flusso, lavoro,
                                  partito, resta, ritmo_sano)
    finally:
        if modo == "fermo":
            sh("pkill -CONT -u %s 2>/dev/null" % chi)


def _il_resto_del_giro(chi, modo, a, giudice, lettore, esito, cliente,
                       chiudi_il_cliente, flusso, lavoro, partito, resta,
                       ritmo_sano=None):
    """The part of the round that sits inside the injection's `try/finally`."""
    # ── 4. the scene ───────────────────────────────────────────────────────
    if not a.scena_ferma:
        fermo, attesi = aspetta_che_il_desktop_si_fermi(
            lambda: cpu_del_codificatore(chi, a.nome_figlio),
            a.attesa_scena, a.soglia_cpu, a.passo_cpu)
        esito["desktop_fermo_s"] = attesi
        print("           %s the desktop %s before the scene (%.1f s)"
              % ("⭐" if fermo else "⚠",
                 "is still" if fermo else ("did NOT become still within the ceiling"
                                          if fermo is False else
                                          "I do not know whether it is still"), attesi))
        display, err = accendi_la_scena(chi, a)
        if display is None:
            esito["motivo"] = "scena-non-accesa"
            esito["perche"] = "I could not switch on the scene: %s" % err
            cliente.kill()
            chiudi_il_cliente(30)
            sgombra(chi, a.attesa_sgombero)
            return esito
        # ── 5. ⭐⭐ WE WAIT FOR THE FRAMES TO REALLY ARRIVE ─────────────────
        #    ⛔ And not a fixed time: `--attesa-scena` turns from a wait into a CEILING.
        #    ⚠ The moment the scene starts painting is the one that
        #      decides everything (the graft, and how many frames dirty the gross
        #      rate), and by the clock one does not know it.
        visto, cpu_al_s, quanto = aspetta_che_i_fotogrammi_arrivino(
            lambda: cpu_del_codificatore(chi, a.nome_figlio),
            a.attesa_scena, a.soglia_cpu, a.passo_cpu)
        esito["lavoro_visto"] = visto
        esito["cpu_prima"] = cpu_al_s
        esito["secondi_prima"] = secondi_in_vista(
            quanto, a.passo_cpu, a.soglia_cpu, cpu_al_s) if visto else None
        print("           %s the frames arrive: the encoder burns %s "
              "CPU/s (I demand %.2f) after %.1f s · scene in view before "
              "the graft: at most %s s"
              % ("⭐" if visto else "⚠",
                 "unknown" if cpu_al_s is None else "%.2f" % cpu_al_s,
                 a.soglia_cpu, quanto,
                 "unknown" if esito["secondi_prima"] is None
                 else "%.1f" % esito["secondi_prima"]))
        # ⭐ PHASE 12 (19 Sep 2026) — A BREATH BEFORE THE GRAFT, and it is COUNTED.
        #   `[M]` On KDE the SIGSTOP 2 s after the encoder's work fell
        #   halfway through the opening of the window (scene at 58 % of the colour and a
        #   black strip): the last frame was not «the scene» and the mesh
        #   did not judge.  ⇒ We wait `--respiro-innesco` more, on every
        #   desktop, ⛔ and it is ADDED to the seconds of scene in view: the rate is
        #   gross (`finestra_bastante`), and an uncounted breath would be a
        #   fault that stops being visible without saying so.
        if visto and a.respiro_innesco > 0:
            time.sleep(a.respiro_innesco)
            if esito["secondi_prima"] is not None:
                esito["secondi_prima"] += a.respiro_innesco
            print("           ⭐ breath before the graft: %.1f s (scene in view, "
                  "counted: at most %.1f s)" % (a.respiro_innesco,
                                               esito["secondi_prima"] or -1))
        esito["scena_viva_prima"] = la_scena_e_viva(chi, a.applicazione)
    else:
        # ⚠ THE NEGATIVE CONTROL: nothing is switched on, and we look at a
        #   desktop that has no reason to change.  ⛔ Here the wait
        #   stays by the clock: there is no frame to wait for, and
        #   waiting for one would mean waiting for the ceiling for nothing.
        time.sleep(a.attesa_scena)

    # ── 6. ⛔⛔ THE REAL FAULT, AND NOW IT IS AT THE RIGHT MOMENT OF THE STORY ─
    #    ⭐ The scene is on, the program moving it is alive, and the
    #      frames were seen arriving: **then** the encoder dies.
    #    ⇒ It is this question the mesh exists to ask — «do the frames
    #      stop?» — and before 27 August 2026 it was not being asked.
    if modo == "fermo":
        quanti, chi_fermato, preso = ferma_il_codificatore(chi, a.nome_figlio)
        esito["fermati"] = quanti
        esito["pkill_ha_preso"] = preso
        print("           ⛔ `pkill -STOP` %s · processes in state T: %d%s"
              % ("took hold" if preso else "⚠ did NOT take hold", quanti,
                 (" (%s)" % ", ".join(sorted(set(chi_fermato))[:6]))
                 if chi_fermato else ""))

    # ⭐⭐ AND THE WINDOW GROWS AS MUCH AS NEEDED — 22 September 2026.
    #
    # ⛔ The rate of this mesh is GROSS: inside the window there are also the
    #    frames born BEFORE the graft, and as long as they alone are enough to keep it
    #    above the threshold the fault cannot bite.  `finestra_bastante()` knows
    #    from which second on it can bite, and until now the bench said so **after
    #    having measured**, with a «relaunch with --finestra-guasto N» that nobody
    #    relaunched: in the net a 3 came out — «I could not look» — and the
    #    mesh no longer certified anything.
    # ⚠ Before 22 Sep the defect was not visible for a wrong reason: the
    #   `pkill` pattern also stopped the scene's BROWSER, so the
    #   scene itself stopped moving and the rate collapsed much earlier.
    #   ⇒ With the graft cured, this came to the surface.
    # ⭐ The number is not invented: it is the one the bench printed in its
    #   advice (`serve × 2 + 10`), and it is always said out loud.
    finestra = a.finestra
    if modo == "fermo":
        serve = finestra_bastante(esito.get("secondi_prima"), ritmo_sano,
                                  a.ritmo_minimo)
        chiesta_a_mano = abs(a.finestra_guasto - FINESTRA_GUASTO) > 0.001
        if serve is not None and finestra <= serve and not chiesta_a_mano:
            finestra = min(serve * 1.25 + 10.0, FINESTRA_GUASTO_TETTO)
            print("           ⭐ the window grows to %.0f s: with the healthy "
                  "rate of %.1f/s and %.1f s of scene in view before "
                  "the graft, below %.0f s the fault could not "
                  "bite%s"
                  % (finestra, ritmo_sano, esito.get("secondi_prima") or -1,
                     serve,
                     " (⚠ CEILING: and it is not enough)"
                     if finestra >= FINESTRA_GUASTO_TETTO
                     and serve * 1.25 + 10.0 > FINESTRA_GUASTO_TETTO else ""))
        elif serve is not None and finestra <= serve:
            print("           ⚠ the window asked by hand (%.0f s) is "
                  "shorter than the %.0f s that would be needed: I leave it as you "
                  "asked, and the judgement will say it could not bite"
                  % (finestra, serve))

    # ⭐⭐ HERE THE MEASURING WINDOW OPENS, and the instant is MARKED — it is the
    #     denominator of the rate, and a denominator nobody marks is a
    #     number that says whatever happens.
    inizio_finestra = time.time()
    cpu_apertura = cpu_del_cliente(cliente.pid)
    time.sleep(finestra)
    # ⛔ AND THE CLIENT'S WORK IS READ AGAIN **BEFORE** THE CLIENT DIES:
    #    afterwards, `/proc/<pid>` is no longer there and the measure would be «I do not know» because of
    #    a defect of the bench.
    esito["cpu_finestra"] = lavoro_al_secondo(
        cpu_apertura, cpu_del_cliente(cliente.pid), time.time() - inizio_finestra)

    # ── 8. the client finishes ─────────────────────────────────────────────
    coda = chiudi_il_cliente(int(resta) + 240)
    fine = time.time()
    detto = quanti_fotogrammi_dice_il_cliente(coda or "")
    ammesso = e_stato_ammesso(coda)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ AND THE SCENE IS LOOKED AT AGAIN **NOW**, at the end — not only at the start.
    #
    # ⚠ The first draft looked at it only once, right after `--attesa-scena`,
    #   and then declared at the top «alive from start to end».  ⛔ But the pairs
    #   that decide the verdict are the LAST frames, i.e. minutes later:
    #   a scene that dies halfway leaves a declared colour on the screen
    #   (so the guard on the colours passes) and identical frames ⇒ ⛔ **red
    #   for the product for something of the browser**, which is exactly the scenario
    #   the file says it fears.
    # ⇒ It is demanded alive **at the end**; and if it was alive at the start and not at the end,
    #   it is said, because it is a different diagnosis from «it never started».
    # ═══════════════════════════════════════════════════════════════════════
    if not a.scena_ferma:
        esito["scena_viva"] = la_scena_e_viva(chi, a.applicazione)

    if ammesso is not True:
        ultimo = "?"
        for riga in reversed((coda or "").strip().splitlines()):
            riga = riga.strip()
            if riga and not riga.startswith("=="):
                ultimo = riga[:90]
                break
        esito["motivo"] = "cliente-non-ammesso"
        esito["perche"] = ("the client %s: %s"
                           % ("was not ADMITTED" if ammesso is False
                              else "said NOTHING", ultimo))
        sgombra(chi, a.attesa_sgombero)
        return esito

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
    secondi = max(1.0, fine - inizio_finestra)
    esito["secondi"] = round(secondi, 1)

    if not os.path.exists(flusso) or os.path.getsize(flusso) == 0:
        # ⛔ No byte on the wire.  ⚠ With the STILL scene this is an expected
        #   result; with the scene in motion it is the canary dying, and
        #   `giudica_il_flusso` says so.
        g = giudica_il_flusso([], secondi, a.scena_ferma, a.ritmo_minimo)
        esito.update({k: g[k] for k in ("stato", "motivo", "perche",
                                        "fotogrammi", "ritmo", "coppie",
                                        "diverse", "minima", "massima")})
        sgombra(chi, a.attesa_sgombero)
        return esito

    # ⛔ The ceiling FOLLOWS the work it governs, instead of standing still while
    #    `--attesa-palco` grows (`LEZIONI.md` §1.17).
    elenco, scaduto = estrai_i_fotogrammi(
        flusso, os.path.join(lavoro, "fotogrammi"),
        a.larghezza, a.altezza, max(900.0, resta * 4.0))
    esito["elenco"] = elenco
    if scaduto:
        esito["motivo"] = "estrazione-troncata"
        esito["perche"] = ("the decoder did not finish: the list of "
                           "frames is TRUNCATED, and a truncated list has "
                           "the look of a lean grab ⇒ I do not judge")
        sgombra(chi, a.attesa_sgombero)
        return esito
    # ⭐ And the two counts are compared BEFORE judging, not after: the client
    #   says how many frames it took from the wire, the decoder how many it
    #   pulled out.  ⛔ If the second is much lower, the stream was
    #   lost along the way and the rate is not the product's.
    if detto and elenco and len(elenco) < detto * QUOTA_ESTRATTI:
        esito["fotogrammi"] = len(elenco)
        esito["motivo"] = "estrazione-magra"
        esito["perche"] = ("the client declares %d frames and the "
                           "decoder pulled out %d (less than "
                           "%.0f%%): the stream was lost along the way, and the "
                           "rate would not be the product's"
                           % (detto, len(elenco), QUOTA_ESTRATTI * 100))
        sgombra(chi, a.attesa_sgombero)
        return esito

    # ── ⭐ IS THE DECLARED SCENE THE ONE I AM LOOKING AT? ──────────────────
    #    ⛔ If it is not, we do not judge: we would say red to the product for
    #       something of the browser.
    if elenco and not a.scena_ferma:
        ultimo_png = elenco[-1]
        g = giudice.giudica(ultimo_png)
        fa = lettore.frazione_del_colore(ultimo_png, SCENA_A, TOLLERANZA)
        fb = lettore.frazione_del_colore(ultimo_png, SCENA_B, TOLLERANZA)
        esito["frazione_scena"] = (None if (fa is None or fb is None)
                                   else max(fa, fb))
        if g is not None and g["verdetto"] in ("nero", "quasi-nero"):
            esito["motivo"] = "desktop-nero"
            esito["perche"] = ("the last frame is «%s»: the session "
                               "had nothing to show, and this is not a "
                               "judgement on C3" % g["verdetto"])
            sgombra(chi, a.attesa_sgombero)
            return esito
        if esito["frazione_scena"] is None or esito["frazione_scena"] < FRAZIONE_SCENA:
            esito["motivo"] = "scena-non-mia"
            esito["perche"] = (
                "the scene I declared is NOT on the screen (its colours "
                "cover %s, I demand %.0f%%) ⇒ I cannot demand that "
                "the frames change: the scene alive? %s"
                % ("unknown" if esito["frazione_scena"] is None
                   else "%.1f%%" % (esito["frazione_scena"] * 100),
                   FRAZIONE_SCENA * 100,
                   "yes" if esito["scena_viva"] else "⛔ NO"))
            sgombra(chi, a.attesa_sgombero)
            return esito
        if not esito["scena_viva"]:
            esito["motivo"] = "scena-morta"
            esito["perche"] = (
                "the program that moves the scene %s: I cannot say whether "
                "the image was frozen or whether there was nothing left to move"
                % ("DIED between the start and the end"
                   if esito["scena_viva_prima"] else "never started"))
            sgombra(chi, a.attesa_sgombero)
            return esito

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE TAIL OF THE DELIVERED FRAMES — and it is ALWAYS looked at, even when
    #    the verdict will come out «crollati».
    #
    # ⛔ `giudica_il_flusso` compares the pairs **only if the rate holds**: with the
    #    encoder stopped it exits with «crollati» first, and that number it
    #    never computes.  ⚠ But it is exactly the number that says whether the fault fell
    #    at the right moment of the story: if the LAST frames that arrived —
    #    those of the instant the encoder died — were **different
    #    from each other**, then the scene was there and moving, and what happened
    #    afterwards is that the frames STOPPED.
    # ⇒ If instead they were identical, the graft fell on a still desktop, and the
    #   round proved nothing: outcome 3, not a red (`collauda_il_fermo`).
    # ═══════════════════════════════════════════════════════════════════════
    # ⚠ And the list can be **None** (the decoder pulled out
    #   nothing): `None` is not an empty list, and slicing it would be a fault
    #   of the bench with the face of a fault of the product.
    m_coda = (coppie_che_cambiano(elenco[-(a.coppie_esaminate + 1):],
                                  SOGLIA_RUMORE, a.soglia_coppia)
              if elenco else None)
    if m_coda is not None:
        esito["coda_coppie"] = m_coda["coppie"]
        esito["coda_diverse"] = m_coda["diverse"]
        esito["coda_frazione"] = m_coda["frazione"]

    g = giudica_il_flusso(elenco, secondi, a.scena_ferma, a.ritmo_minimo,
                          a.frazione_coppie, a.coppie_esaminate,
                          SOGLIA_RUMORE, a.soglia_coppia)
    esito.update({k: g[k] for k in ("stato", "motivo", "perche", "fotogrammi",
                                    "ritmo", "coppie", "diverse", "minima",
                                    "massima")})
    if detto is not None and esito["fotogrammi"] is not None \
            and detto != esito["fotogrammi"]:
        # ⚠ It is not a verdict: it is information.  The client counts the
        #   frames taken from the wire, ffmpeg those that were decoded:
        #   ⛔ if the two numbers diverge a lot, the stream has holes and whoever
        #      diagnoses must know it.
        esito["perche"] += (" ⚠ (the client declares %d of them, the decoder "
                            "pulled out %d)" % (detto, esito["fotogrammi"]))
    sgombra(chi, a.attesa_sgombero)
    return esito


def _n(x):
    return "unknown" if x is None else x


def stampa(e):
    faccia = {"cambia": "YES", "congelata": "NO ", "crollati": "NO ",
              "non-lo-so": "?  "}[e["stato"]]
    print("  %-8s %-6s %s  %s" % (e["chi"], e["modo"], faccia, e["perche"]))
    print("           screens: %s · stage in %s s · frames %s in %s s "
          "(real window, ⚠ not `--finestra`) · different pairs %s/%s"
          % (_n(e["schermi"]), _n(e["palco_s"]), _n(e["fotogrammi"]),
             _n(e["secondi"]), _n(e["diverse"]), _n(e["coppie"])))
    # ⭐⭐ THE MARGIN IS ALWAYS PRINTED, as C5 does: it is the number that warns BEFORE
    #    a threshold becomes a false red, and the first draft computed it
    #    and threw it away.
    # ⭐ AND WHERE THE JUDGED FRAMES ARE: on a red, without the path, there
    #   is nothing to look at without already knowing where to search.  ⚠ And they stay there
    #   on purpose — the next round of the same tenant redoes them.
    if e["elenco"]:
        print("           the judged frames (the last %d of %d): %s"
              % (min(len(e["elenco"]), COPPIE_ESAMINATE + 1), len(e["elenco"]),
                 os.path.dirname(e["elenco"][0])))
    print("           ⭐ margin on the pair threshold: the weakest %s · "
          "the strongest %s (threshold %.0f%%) · scene on the screen %s · alive "
          "at the end %s"
          % ("unknown" if e["minima"] is None else "%.2f%%" % (e["minima"] * 100),
             "unknown" if e["massima"] is None else "%.2f%%" % (e["massima"] * 100),
             SOGLIA_COPPIA * 100,
             "unknown" if e["frazione_scena"] is None
             else "%.1f%%" % (e["frazione_scena"] * 100),
             _n(e["scena_viva"])))


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ THE THREE JOINTS — and they live in PURE functions so that `--certifica` tests them.
#
# ⛔⛔ It is the piece `LEZIONI.md` §1.52 was born for: *«C9's certification
#     tested the judge, C13's the reading of the log; the defect
#     was in the JOINT between the two — in the exit code, which belongs to neither
#     of the two trades»*.  ⇒ Here the exit code with the grafted fault is
#     **inverted**, and from it `11-gancio.sh` derives `ha_visto_il_guasto`.
# ═══════════════════════════════════════════════════════════════════════════
LA_PROVA_NON_E_GIRATA = (
    "palco-non-nato", "scena-non-accesa", "cliente-non-ammesso",
    "estrazione-troncata", "estrazione-magra", "desktop-nero",
    "scena-non-mia", "scena-morta", "inquilino-non-creato", "niente-elenco",
    "niente-secondi", "niente-coppie")


def _sano_non_regge(sano, r):
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
    if sano["stato"] == "non-lo-so":
        r.append("⚠ the healthy round could not look (%s): I cannot say "
                 "whether the fault would have been seen" % (sano["motivo"] or "?"))
        r.append("   ⇒ and this does NOT accuse the mesh (§4.5: «graft not "
                 "judged»)")
        return 3
    if sano["stato"] != "cambia":
        r.append("⛔⛔ THE HEALTHY CONTROL IS RED: %s" % sano["perche"])
        r.append("    ⇒ this round does NOT measure the fault — it measures a red that "
                 "is already there on its own (§1.45).")
        r.append("    ⚠ And the outcome is 3 and not 1: saying «the fault was not "
                 "seen» would be an accusation")
        r.append("      against the net for a regression of the PRODUCT. ⇒ The real "
                 "red is given by the round without the fault.")
        return 3
    return None


def collauda_il_ripetuto(sano, sfregiato, margine_soglia=MARGINE_SOGLIA,
                         soglia_coppia=SOGLIA_COPPIA):
    """`--fotogramma-ripetuto`.  Returns `(esito, [lines])`, outcome BACKWARDS.

    ⛔⛔ AND HERE THERE IS A THING THAT MUST BE SAID, because a reviewer found it and
         was right: **the defacement, on its own, cannot fail.**  If the healthy
         round is green, repeating the same frame N times necessarily gives
         zero different pairs: it is arithmetic, and it is already certified in 0.3
         seconds by `--certifica`.  ⇒ A round on the real thing that asserted **only**
         that would spend a whole session for a bit already known — i.e.
         `LEZIONI.md` §1.44 disguised as an acceptance test.

    ⭐ That is why this acceptance test demands **one more thing, and that one can
      really fail**: that the **weakest** consecutive pair of the healthy
      round sits at least `margine_soglia` times above the threshold.
      ⇒ It is a measurement of the WORLD — how lively the real scene is, seen
        through the product, after the encoding — and if one day the scene
        became timid (a browser skipping frames, an encoding that
        flattens) **this number would drop before the mesh starts giving
        false reds**.  ⚠ It is the same thing C5 does with the margin of the RMS.
    """
    r = []
    esito = _sano_non_regge(sano, r)
    if esito is not None:
        return esito, r
    if sfregiato is None:
        r.append("⚠ I do not have a list of frames to deface: I cannot "
                 "graft the fault (outcome 3, not a red)")
        return 3, r

    r.append("  healthy   : %s" % sano["perche"])
    r.append("  defaced   : %s" % sfregiato["perche"])
    r.append("")
    if sfregiato["stato"] == "non-lo-so":
        # ⛔ «I do not know» is NOT «the fault was not seen»: the first
        #    frame could be unreadable, and accusing the net for a
        #    broken PNG would be the same form of error as §1.47.
        r.append("⚠ the defaced one could not be judged (%s): I cannot "
                 "say whether the fault would have been seen" % (sfregiato["motivo"] or "?"))
        r.append("   ⇒ outcome 3, not a red.")
        return 3, r
    if sfregiato["stato"] != "congelata":
        r.append("⛔⛔ THE GRAFTED FAULT WAS NOT SEEN: the same "
                 "frame repeated passes for a scene that changes.")
        r.append("    ⇒ this mesh does not look in the right place.")
        return 1, r
    if not (sano["diverse"] and sfregiato["diverse"] == 0):
        r.append("⛔ the verdict changed but the NUMBER did not: different pairs "
                 "%s ⇒ %s." % (_n(sano["diverse"]), _n(sfregiato["diverse"])))
        return 1, r
    r.append("  ⭐ measurable difference, on the SAME data: the different pairs "
             "go from %s to %s out of %s"
             % (sano["diverse"], sfregiato["diverse"], sano["coppie"]))

    # ⭐⭐ AND THE MEASURE THAT CAN REALLY FAIL: how lively the real scene is.
    minima = sano["minima"]
    if minima is None:
        r.append("⚠ I do not know how much the weakest pair of the healthy round "
                 "changed: without that number this acceptance test asserts nothing "
                 "about the world (outcome 3).")
        return 3, r
    volte = minima / soglia_coppia if soglia_coppia else 0.0
    r.append("  ⭐ and the real scene is lively: the weakest pair changes "
             "%.2f%% of the pixels, %.1f times the threshold (I demand %.1f)"
             % (minima * 100, volte, margine_soglia))
    if volte < margine_soglia:
        r.append("⛔ THE SCENE IS TOO TIMID, or the threshold is too close: "
                 "the weakest pair")
        r.append("   sits at %.1f times the threshold instead of %.1f. ⇒ Today the "
                 "verdict is still right," % (volte, margine_soglia))
        r.append("   ⚠ but tomorrow a false red is one step away, and this mesh "
                 "warns BEFORE instead of after.")
        return 1, r
    r.append("")
    r.append("⭐ THE GRAFTED FAULT WAS SEEN — this mesh CAN catch "
             "the frozen image,")
    r.append("   ⭐ and the real scene sits well clear of the threshold.")
    return 0, r


def collauda_il_fermo(sano, rotto, quota=QUOTA_GUASTO, quota_lorda=QUOTA_LORDA,
                      frazione_coppie=FRAZIONE_COPPIE,
                      ritmo_minimo=RITMO_MINIMO):
    """`--codificatore-fermo`.  Returns `(esito, [lines])`, outcome BACKWARDS.

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
         (`finestra_bastante`)

    ⛔ If one is missing, the outcome is **3**: what was believed was not grafted,
       and saying «the fault was not seen» would be an accusation against the net for an
       acceptance test that did not run.
    """
    r = []
    esito = _sano_non_regge(sano, r)
    if esito is not None:
        return esito, r
    if rotto["stato"] == "non-lo-so":
        r.append("⚠ the round with the fault could not look (%s): I cannot "
                 "say whether the fault would have been seen" % (rotto["motivo"] or "?"))
        r.append("   ⇒ outcome 3, not a red (§4.5).")
        return 3, r
    # ⚠⚠ THE FAULT'S SIGNATURE — and if it is missing the outcome is **3**, not a red.
    if not rotto["fermati"] or rotto["pkill_ha_preso"] is False:
        r.append("⚠ the injection stopped nothing: `pkill -STOP` %s, and the "
                 "processes of «%s» in state T are %s."
                 % ("took hold" if rotto["pkill_ha_preso"] else "did NOT take hold",
                    rotto["chi"], _n(rotto["fermati"])))
        r.append("   ⇒ whatever verdict comes out is NOT the fault I believed I had "
                 "grafted (§1.52).")
        r.append("   ⇒ outcome 3, not a red.")
        return 3, r

    # ── ⭐⭐ THE MOMENT OF THE GRAFT — the cure of 27 August 2026 ───────────
    if rotto.get("lavoro_visto") is not True:
        r.append("⚠ before stopping the encoder I NEVER saw the frames "
                 "arrive (the encoder was burning %s CPU/s)."
                 % _n(rotto.get("cpu_prima")))
        r.append("   ⇒ I stopped an encoder that was not delivering: "
                 "it is not «the frames stop»,")
        r.append("     it is «they had never started». ⛔ Outcome 3, not a red.")
        return 3, r
    if rotto.get("coda_frazione") is None:
        r.append("⚠ I could not compare the last delivered frames with each other: "
                 "I do not know whether the scene was moving")
        r.append("   at the instant the encoder died. ⇒ Outcome 3.")
        return 3, r
    if rotto["coda_frazione"] < frazione_coppie:
        r.append("⛔ THE LAST FRAMES DELIVERED WERE IDENTICAL TO EACH OTHER "
                 "(%s different pairs out of %s, %.0f%%):"
                 % (_n(rotto["coda_diverse"]), _n(rotto["coda_coppie"]),
                    rotto["coda_frazione"] * 100))
        r.append("   the graft fell when the scene was not moving yet "
                 "⇒ this round does NOT prove «the frames stop»,")
        r.append("   it proves «there was nothing to stop». ⛔ Outcome 3, not a "
                 "red — and the graft must be moved, not the judge softened.")
        return 3, r
    r.append("  ⭐ the graft fell at the right moment: the encoder "
             "was working (%.2f CPU/s) and the last frames delivered"
             % (rotto.get("cpu_prima") or 0.0))
    r.append("     were different from each other (%s pairs out of %s, %.0f%%) ⇒ the scene "
             "was there and moving, **then** the encoder died."
             % (_n(rotto["coda_diverse"]), _n(rotto["coda_coppie"]),
                rotto["coda_frazione"] * 100))

    # ── ⭐ WAS THE WINDOW LONG ENOUGH? ─────────────────────────────────────
    #    ⛔ The rate is GROSS: with the frames born before the graft a dead
    #       stream can look alive, and then the round could not bite.
    serve = finestra_bastante(rotto.get("secondi_prima"), sano["ritmo"],
                              ritmo_minimo)
    if serve is not None:
        r.append("  ⭐ the window: %s s watched, and for this box more than "
                 "%.0f were needed (%.1f s of scene in view before "
                 "the graft × %.1f/s healthy ÷ %.1f/s demanded)"
                 % (_n(rotto["secondi"]), serve, rotto["secondi_prima"],
                    sano["ritmo"], ritmo_minimo))
        if rotto["secondi"] is None or rotto["secondi"] <= serve:
            r.append("⚠ THE WINDOW WAS TOO SHORT for this rate: the "
                     "frames born before the graft are enough on their own")
            r.append("   to keep the gross rate above the threshold ⇒ the fault "
                     "could not bite, and I did not test it.")
            r.append("   ⛔ Outcome 3, not a red. ⇒ Relaunch with "
                     "`--finestra-guasto %d`." % int(serve * 1.25 + 10))
            return 3, r

    if rotto["stato"] == "cambia":
        r.append("⛔⛔ THE GRAFTED FAULT WAS NOT SEEN: with the encoder "
                 "stopped the frames arrive anyway.")
        return 1, r

    # ── ⭐⭐ THE MEASURABLE DIFFERENCE, and the CLEAN one comes before the gross one ─
    ls = sano.get("cpu_finestra")
    lr = rotto.get("cpu_finestra")
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

    rs = sano["ritmo"] or 0.0
    rr = rotto["ritmo"] or 0.0
    r.append("  ⭐ and the GROSS difference, which carries inside it the frames born "
             "before the graft: the rate goes from %.2f/s to %.2f/s"
             % (rs, rr))
    r.append("     ⇒ %.2f/s fewer, i.e. %.1f%% of the healthy one (here I allow "
             "at most %.0f%%, ⛔ and not %.0f%%: the number is dirty "
             "on purpose)"
             % (rs - rr, (rr / rs * 100) if rs else 0.0, quota_lorda * 100,
                quota * 100))
    if rs <= 0 or rr > rs * quota_lorda:
        r.append("⛔ the verdict changed but the NUMBER hardly did: the fault "
                 "bit little, and an acceptance test like this does not certify the net.")
        return 1, r
    r.append("")
    r.append("⭐ THE GRAFTED FAULT WAS SEEN — this mesh CAN say red,")
    r.append("   ⭐ and for the right reason: the scene was moving, the "
             "encoder died, and THE FRAMES STOPPED.")
    return 0, r


def collauda_la_scena_ferma(e):
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
    if e["stato"] in ("congelata", "crollati"):
        r.append("⛔⛔ THE NEGATIVE CONTROL FAILED: with the STILL scene "
                 "this mesh gave RED (%s)." % e["stato"])
        r.append("    ⇒ `[M]` phase 9 §3.1: on a still scene 0.03 "
                 "frames/s come out and it is a RESULT, not a defect.")
        r.append("    ⛔ A mesh that gives red there is a generator of false "
                 "reds, and §1.3 says how it ends.")
        return 1, r
    if e["motivo"] != "scena-ferma":
        r.append("⚠ the round did not reach the control: it stopped earlier "
                 "(%s)." % (e["motivo"] or "?"))
        r.append("   ⇒ %s" % e["perche"])
        r.append("   ⛔ So I verified NOTHING: outcome 3, and it must not be "
                 "mistaken for a successful control.")
        return 3, r
    r.append("⭐ THE NEGATIVE CONTROL HOLDS — the round happened (stage born, "
             "client admitted),")
    r.append("   the scene was still, and this mesh ⛔ did NOT give red: it "
             "said «I do not know» and said why.")
    r.append("   ⭐ And the round leaves the number with which `--ritmo-minimo` is calibrated: "
             "%s frames in %s s."
             % (_n(e["fotogrammi"]), _n(e["secondi"])))
    return 0, r


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente-base", default="c3u")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--scena", default="/opt/remotix/11-c3-scena.html",
                   help="⭐ THE DECLARED SCENE: it is this file that decides what "
                        "moves and by how much")
    p.add_argument("--respiro-innesco", type=float, default=2.0,
                   help="seconds between «the encoder works» and the graft, COUNTED "
                        "in the scene in view: on KDE the window finishes "
                        "appearing (phase 12)")
    p.add_argument("--applicazione", default="firefox-esr",
                   help="⚠ today the browser, because it is the only program in the "
                        "box that can paint a scene we decide. "
                        "⛔ To be moved as soon as there is another one")
    p.add_argument("--argomenti", default="--kiosk file://%(pagina)s")
    p.add_argument("--nome-figlio", default="remotix",
                   help="what the tenant's process that encodes and delivers "
                        "is called, in the command line")
    p.add_argument("--lavoro", default="/var/lib/rete11/c3")
    p.add_argument("--larghezza", type=int, default=128)
    p.add_argument("--altezza", type=int, default=72)
    # ⭐ 60 s, and the number comes from a MEASUREMENT: `[M]` 27 August 2026, inside the
    #   cured GNOME box the stage is born in **2.1÷4.2 s** ⇒ 60 s are more
    #   than ten times the worst measured.  ⛔ The 200 s of before were a
    #   prudent number chosen when the phenomenon seemed to last ~97 s — which
    #   was a fault of the box, later cured (`LEZIONI.md` §1.54).
    # ⚠ And here it is not a deadline but an ADDEND of `--resta`: every second
    #   too many is a second thrown away for every tenant, not a margin.
    p.add_argument("--attesa-palco", type=float, default=60.0,
                   help="⛔ CEILING TO RECALIBRATE: [M] (C1, 27 Aug 2026, not mine) "
                        "95-101 s in the GNOME box because of a defect of the "
                        "BOX; with that cured, ~2 s ⇒ put back to ~20")
    p.add_argument("--attesa-scena", type=float, default=30.0,
                   help="⛔ CEILING TO RECALIBRATE [?]: how long the scene is given to "
                        "be on the screen")
    p.add_argument("--finestra", type=float, default=45.0,
                   help="⚠ the MINIMUM of seconds in which the scene in "
                        "motion is watched — NOT the real window. ⛔ The client stays "
                        "attached `--attesa-palco + --attesa-scena + "
                        "--finestra + --coda` seconds in all, decided at "
                        "launch: if the stage is born early, the real window is "
                        "longer than this number. ⭐ The REAL one the mesh "
                        "prints at every round, and it is the denominator of the rate")
    # ⭐⭐ THE WINDOW OF THE ROUND WITH THE FAULT IS LONGER, and the reason is a
    #    calculation, not a taste: `finestra_bastante`.  The rate is GROSS, ⇒ the
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
    p.add_argument("--finestra-guasto", type=float, default=FINESTRA_GUASTO,
                   help="⭐ the window of the TWO rounds of `--codificatore-fermo`: "
                        "measuring an absence takes time")
    p.add_argument("--coda", type=float, default=10.0)
    # ⭐ The live signal «the frames are arriving»: see the top.
    p.add_argument("--soglia-cpu", type=float, default=SOGLIA_CPU,
                   help="⭐ how much CPU per second the ENCODER must "
                        "burn for us to say that the frames "
                        "ARRIVE. [?] and the mesh always prints the real value")
    p.add_argument("--passo-cpu", type=float, default=PASSO_CPU,
                   help="every how many seconds the client's work is looked at. "
                        "⛔ short on purpose: it is the scene time that ends up in the "
                        "gross rate even with the fault")
    p.add_argument("--attesa-sgombero", type=float, default=60.0)
    p.add_argument("--ritmo-minimo", type=float, default=RITMO_MINIMO,
                   help="⛔ [?] wide on purpose: it separates «a trickle» from «nothing», "
                        "it does NOT judge smoothness")
    p.add_argument("--frazione-coppie", type=float, default=FRAZIONE_COPPIE)
    p.add_argument("--coppie-esaminate", type=int, default=COPPIE_ESAMINATE)
    p.add_argument("--soglia-coppia", type=float, default=SOGLIA_COPPIA,
                   help="how many pixels must change for two frames "
                        "to be «different». [?] to be recalibrated in the box")
    p.add_argument("--margine-soglia", type=float, default=MARGINE_SOGLIA,
                   help="⭐ how many times the WEAKEST pair of the healthy round "
                        "must sit above the threshold. ⛔ It is what makes the "
                        "`--fotogramma-ripetuto` acceptance test not empty")
    p.add_argument("--scena-ferma", action="store_true",
                   help="⚠ THE NEGATIVE CONTROL: no scene is switched on. "
                        "⛔ In this mode the mesh CANNOT give red")
    p.add_argument("--fotogramma-ripetuto", action="store_true",
                   help="⛔ GRAFTED FAULT: the in-memory copy of the list is defaced "
                        "by putting the first frame in it N times. "
                        "The outcome is read BACKWARDS")
    p.add_argument("--codificatore-fermo", action="store_true",
                   help="⛔ GRAFTED FAULT: SIGSTOP to the tenant's process "
                        "that delivers. The outcome is read BACKWARDS")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    quanti_guasti = sum([a.fotogramma_ripetuto, a.codificatore_fermo])
    if quanti_guasti > 1:
        print("⛔ one fault at a time: if two are grafted one no longer knows "
              "which one bit")
        sys.exit(2)
    if a.scena_ferma and quanti_guasti:
        print("⛔ «still scene» is the NEGATIVE CONTROL, not a fault: with the "
              "scene still there is nothing to graft")
        sys.exit(2)
    # ⛔⛔ THE GUARDS ON THE NUMBERS — `LEZIONI.md` §1.44: a threshold set to zero
    #     from the command line is a predicate that can no longer fail, and
    #     `--certifica` would not notice (it certifies the CONSTANTS).
    if not 0 < a.frazione_coppie <= 1:
        print("⛔ --frazione-coppie %s: outside 0..1 this mesh could no "
              "longer give either red or green" % a.frazione_coppie)
        sys.exit(2)
    if a.soglia_coppia <= 0 or a.ritmo_minimo <= 0:
        print("⛔ --soglia-coppia and --ritmo-minimo must be greater than "
              "zero: at zero neither of the two could give red any more")
        sys.exit(2)
    if a.coppie_esaminate < 2:
        print("⛔ --coppie-esaminate %d: with fewer than two pairs there is nothing "
              "to compare" % a.coppie_esaminate)
        sys.exit(2)
    if a.soglia_cpu <= 0 or a.passo_cpu <= 0:
        print("⛔ --soglia-cpu and --passo-cpu must be greater than zero: at "
              "zero «the frames arrive» would always be true, even on a "
              "dead desktop")
        sys.exit(2)
    # ⭐⭐ AND THE WINDOW OF THE ACCEPTANCE TEST WITH THE ENCODER STOPPED IS LONGER — for
    #    both rounds, the healthy and the faulted, or the two rates would not be
    #    comparable.  ⛔ The reason is a calculation and lives in `finestra_bastante`.
    if a.codificatore_fermo:
        a.finestra = a.finestra_guasto
    if os.geteuid() != 0:
        print("⛔ it must be run as administrator: it has to create new tenants")
        sys.exit(2)

    giudice, dove_g = giudice_del_desktop()
    if giudice is None:
        print("⛔ I cannot find the image judge (10-f1-testimone.py) next to me")
        print("   ⇒ I could not look")
        sys.exit(3)
    lettore, dove_l = lettore_del_colore()
    if lettore is None:
        print("⛔ I cannot find the colour reader (11-c8-…py) next to me")
        print("   ⇒ I could not look")
        sys.exit(3)
    for che, dove in (("the test client", a.cliente),
                      ("the declared scene", a.scena)):
        if not os.path.exists(dove):
            print("⛔ I cannot find %s: %s" % (che, dove))
            print("   ⇒ I could not look")
            sys.exit(3)
    for programma in (a.applicazione, "ffmpeg", "wayland-info", "runuser"):
        if sh("command -v %s" % programma).returncode != 0:
            print("⛔ the box does not have %s" % programma)
            print("   ⇒ I could not look")
            sys.exit(3)
    try:
        import numpy, PIL  # noqa: F401
    except ImportError:
        print("⛔ numpy or Pillow is missing: I cannot compare two frames")
        print("   ⇒ I could not look")
        sys.exit(3)

    os.makedirs(a.lavoro, exist_ok=True)

    # ⭐ BEFORE any `crea`: `crea` does `userdel -r`, and from that moment the
    #   owner of `/tmp/mozilla` would be a NUMBER instead of a name — i.e.
    #   I would no longer recognise it as mine.
    resto = sgombra_il_mio_rimasuglio(a.utente_base)

    print("== C3 — the frames arrive, and the scene CHANGES ==")
    print("   port %d · scene %s · application «%s»"
          % (a.porta, os.path.basename(a.scena), a.applicazione))
    print("   yardstick: rate ≥ %.2f/s (rough reference [M] %.1f/s, phase 9 §3.1 "
          "⇒ %.0f%%) · at least %.0f%% of consecutive pairs different"
          % (a.ritmo_minimo, RIFERIMENTO_FPS,
             a.ritmo_minimo / RIFERIMENTO_FPS * 100, a.frazione_coppie * 100))
    print("   ⚠ the rate is GROSS and therefore OPTIMISTIC: it is not the check that "
          "decides (see the top)")
    print("   imported judges: %s · %s"
          % (os.path.basename(dove_g), os.path.basename(dove_l)))
    print("   provisioning: the cure of src/provisiona.sh, imported from C2, for every "
          "tenant I create")
    if resto:
        print("   %s" % resto)
    print("   ceilings (⛔ to recalibrate on the real thing): stage %.0f s · scene %.0f s · "
          "window %.0f s" % (a.attesa_palco, a.attesa_scena, a.finestra))
    if a.scena_ferma:
        print("   ⚠ NEGATIVE CONTROL «still scene»: ⛔ this mesh in "
              "this mode CANNOT give red, and it will say why")
    if a.fotogramma_ripetuto:
        print("   ⛔ GRAFTED FAULT: «the same frame repeated» — it defaces "
              "the IN-MEMORY COPY, the stream on disk is not touched")
        print("   ⭐ healthy control and fault run on the SAME data: the "
              "difference cannot come from a different round")
    if a.codificatore_fermo:
        print("   ⛔ GRAFTED FAULT: SIGSTOP to the tenant's «%s» process"
              % a.nome_figlio)
        print("   ⭐ and with it runs a HEALTHY CONTROL, or one could not "
              "distinguish «the fault bit» from «it was already red»")
        print("   ⭐⭐ and the graft falls AFTER the scene was seen moving "
              "(cure of 27 Aug 2026): before, it died on an empty desktop")
        print("   ⚠ window %.0f s for both rounds: measuring "
              "an absence takes time (see `finestra_bastante`)" % a.finestra)
    print()

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ «REPEATED FRAME»: a single tenant, and the same data is judged
    #    TWICE.
    # ═══════════════════════════════════════════════════════════════════════
    if a.fotogramma_ripetuto:
        e = un_giro("%s1" % a.utente_base, None, a, giudice, lettore)
        stampa(e)
        print()
        sfregiato = giudica_il_flusso(sfregia_ripetendo(e["elenco"]),
                                      e["secondi"] or 1.0, False,
                                      a.ritmo_minimo, a.frazione_coppie,
                                      a.coppie_esaminate, SOGLIA_RUMORE,
                                      a.soglia_coppia) if e["elenco"] else None
        esito, righe = collauda_il_ripetuto(e, sfregiato, a.margine_soglia,
                                            a.soglia_coppia)
        for riga in righe:
            print(riga)
        sys.exit(esito)

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔ «ENCODER STOPPED»: two tenants, one healthy and one faulted.
    # ═══════════════════════════════════════════════════════════════════════
    if a.codificatore_fermo:
        sano = un_giro("%s1" % a.utente_base, None, a, giudice, lettore)
        stampa(sano)
        rotto = un_giro("%s2" % a.utente_base, "fermo", a, giudice, lettore,
                        ritmo_sano=sano.get("ritmo"))
        stampa(rotto)
        print()
        esito, righe = collauda_il_fermo(sano, rotto, QUOTA_GUASTO,
                                         QUOTA_LORDA, a.frazione_coppie,
                                         a.ritmo_minimo)
        for riga in righe:
            print(riga)
        sys.exit(esito)

    # ═══════════════════════════════════════════════════════════════════════
    # THE NORMAL ROUND — and the NEGATIVE CONTROL, which now asserts something
    # ═══════════════════════════════════════════════════════════════════════
    e = un_giro("%s1" % a.utente_base, None, a, giudice, lettore)
    stampa(e)
    print()
    if a.scena_ferma:
        esito, righe = collauda_la_scena_ferma(e)
        for riga in righe:
            print(riga)
        sys.exit(esito)
    if e["stato"] == "cambia":
        print("⭐ GREEN — the frames arrive and the scene CHANGES.")
        sys.exit(0)
    if e["stato"] == "non-lo-so":
        print("⚠ NOT JUDGING — %s" % e["perche"])
        print("  ⛔ And this is not a green: it is an outcome of its own (§4.5).")
        sys.exit(3)
    print("⛔⛔ RED — %s" % e["perche"])
    sys.exit(1)


if __name__ == "__main__":
    main()
