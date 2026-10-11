#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c6 — ⭐⭐⭐ «IT DETACHES AND FINDS ITSELF AGAIN»
===========================================================================

    python3 11-c6-si-stacca-e-si-ritrova.py --port 8511
    python3 11-c6-si-stacca-e-si-ritrova.py --port 8511 --kill-session
    python3 11-c6-si-stacca-e-si-ritrova.py --certify

Line C6 of `fasi/11-la-rete-di-sicurezza.md` §4.1:

    what must be true         : it detaches and finds itself again
    where it starts from      : an ALREADY LIVE session (⚠ here that is right,
                                and it is the only line of the list that starts like this)
    what it looks at          : after the re-attach — same session, same
                                windows, ⭐ SEEN IN THE IMAGE
    how I know it can say red : the session is killed ⇒ red

---------------------------------------------------------------------------
⛔⛔⛔ WHY THIS MESH MATTERS MORE THAN THE OTHERS, and it must be read before the numbers
---------------------------------------------------------------------------

The project's invariant **I4** is a declared promise, and it is written in the
delivered code (`src/main.c:505-507`):

    *«the stage belongs to the SESSION, not to the connection, and dies only by
      explicit logout or by abandonment after 60 minutes without input»*

⇒ ⭐ **C6 is the mesh that goes to see whether that promise is true from the
  user's side** — i.e. not «is the process still there?» but *«I detach, come back, and
  do I find what I had left?»*.

⚠⚠ AND TODAY THERE IS A MEASUREMENT THAT SAYS NO.  `[M]` 27 August 2026, isolated bench
   with real Mutter (⛔ **I did not run it**: it is the measurement of another
   agent of this phase, and I report it in full because it is the reason why
   C6 is written this way):

     · the `wl_output` of a headless session is born **only when a
       PipeWire consumer hooks** onto the stream — 65÷93 ms later, ⛔ never
       before;
     · the monitor **survives** the detach of the CONSUMER (measured: at 15 s
       it is still there), ⛔ but **dies with the D-Bus connection of whoever called
       `RecordVirtual`**;
     · in the product that connection belongs to the tenant's **child**.

   ⇒ ⭐⭐ If the stage dies when nobody is looking, **today the desktop has a
     screen only while someone is looking at it** — and I4, from the
     user's side, is broken.

⛔ And so this mesh must be able to give **RED** today.  If it says green, it is not
   good news: it is a complacent mesh, and it must be looked in the face
   (`LEZIONI.md` §1.47, last line).

---------------------------------------------------------------------------
⛔⛔ THE THREE QUESTIONS C6 DOES NOT ASK — and each would be a green forever
---------------------------------------------------------------------------

  ⛔ *«does the session still exist?»*   ⭐ IT EXISTS.  The child survives the
     detach, and C7 has already MEASURED it (`[M]` 26 Aug 2026, XFCE box: after the
     detach the tenant still had 8 processes and 8 entries in
     `XDG_RUNTIME_DIR`).  ⇒ Asking this would mean a predicate that cannot
     fail: `LEZIONI.md` §1.44.  ⚠ **It is the STAGE that is lost, not the
     session** — they are two things, and the difference is this whole mesh.

  ⛔ *«is the process there?»*         the same thing, one level lower.  ⚠ The
     process count has already lied once in this project: `[M]`
     it said «1» with the window and without (§4.1, line C2).

  ⛔ *«does the log say it is fine?»*  ⚠ The log is C1's yardstick, and C1
     has a known defect precisely there: it reads as proof of blindness a line that
     the product writes in the **successful** birth (`src/sessione.c:345-348`).
     ⇒ C6 **does not open the log**, on purpose.  Its judgement lies
     in the image, and in the comparison between two images.

---------------------------------------------------------------------------
⭐⭐⭐ WHAT «SAME WINDOWS» MEANS — the yardstick, declared
---------------------------------------------------------------------------

§4.3 of the phase document: *«pixel-by-pixel comparison with a reference
image rots in a week»*, and ⛔ **nobody knows what a
desktop looks like**.  ⇒ The yardstick cannot be «I recognise the desktop»: it must be poor
and not fragile.

⭐ **So WE PUT the scene there ourselves, and that way we know what it looks like.**  Before
  the detach, inside the session, **a window of declared
  colour** is opened: the browser full screen on the page `11-c8-pagina.html`,
  which is `#FF00FF`.  ⇒ *«same windows»* becomes a question that can be
  answered with a histogram:

    1. ⭐ **the scene is found again**: after the re-attach at least **C8's minimum
       fraction** (today 25 % of the screen) is still the colour of the scene,
       within the tolerance declared by C8.  ⛔ That number is NOT copied here:
       it is imported, or the day someone calibrates C8 the two meshes would start
       judging the same image in two different ways;
    2. ⭐ **and it is the SAME scene**: the fraction AFTER does not deviate from the one
       BEFORE by more than **`MAXIMUM_GAP`** in absolute terms (today 0.25, ⚠ `[?]` not
       measured ⇒ it is an argument).  Not «identical»: a window that
       moves by twenty pixels is not a fault, and demanding exact equality
       would be the test that rots;
    3. ⚠ **and the image is not degenerate**: the judge of `10-f1-testimone.py`
       says «black» / «near-black» / «solid colour» / «drawn», and it serves to
       NAME the red — a desktop gone back to black and a desktop gone back empty
       are two different faults with the same fraction (zero).

⛔ **AND A WINDOW, NOT A BACKGROUND.**  The poor temptation was to tint the
   desktop background (`gsettings`) instead of opening a window: it costs less and
   does not want the browser.  ⚠ But it would not distinguish anything: if the monitor dies and
   is born again, the **background comes back by itself** — it is the compositor's.  ⭐ What does not
   come back, if the stage was lost, are **the windows**.  ⇒ The scene
   must be a window, or the mesh is complacent.

⛔ **AND WHAT IS NOT JUDGED, declared**: the position of the window, the
   GNOME bar, the fonts, the pixel-by-pixel similarity between the two
   images.  ⇒ §4.3: they are all things that change without anything being broken.

---------------------------------------------------------------------------
⛔⛔⛔ THE GUARD THAT HOLDS EVERYTHING UP — «two zeros are equal»
---------------------------------------------------------------------------

⚠ Without this line C6 would be the most complacent mesh of the net, and it would
  be so **silently**:

    the scene is not seen BEFORE (0.00)  and  not seen AFTER (0.00)
    ⇒ «same fraction» ⇒ ⛔ **GREEN**

  ⭐ It is `LEZIONI.md` §1.47 to the letter — *a comparison between values nobody
    can give is green, and has looked at nothing* — with the aggravating factor that here the two
    values are not mute: they are **zero**, which has the face of a measurement.

⇒ ⛔ **If the scene is not seen BEFORE the detach, C6 exits 3: «I could not
  look».**  It is not a red and it is not a green.  ⚠ And the reason is carried
  next to the symptom — the image's verdict says which defect UPSTREAM
  stopped the test: a «black» desktop is the late birth of §7-bis.13, a
  «drawn» desktop without magenta is the browser that did not open the window.

---------------------------------------------------------------------------
⭐⭐ C6 AND C7 LOOK AT THE SAME GESTURE FROM TWO SIDES — and ⛔ they do not contradict each other
---------------------------------------------------------------------------

`11-c7-si-chiude-e-non-resta-niente.py` has, for one case, the identical gesture to
this one: the client goes away and the session does **not** close (`--detach-only`).
⛔ And for C7 that case **must be GREEN**: it is I4 doing its job, and a
red there would be the defect §1.49 (*a red that cannot be made
green*).

⇒ ⭐ **The two meshes ask two different questions about the same gesture:**

    C7 · *«after the detach is the CHILD still alive?»*         today: ⭐ YES
    C6 · *«and is what the child kept standing found AGAIN?»*  today: ⛔ maybe not

⚠⚠ **C7 green and C6 red together is NOT a contradiction**: it is the measure of
   how little *«the child is alive»* guarantees the user.  ⛔ And if someone,
   reading C6 red, went to make C7 red «for consistency», they would break the
   healthy mesh to keep company with the one that found something.

⛔ **And the third case must be told apart once more: «it only detaches» is not
   a question of C6.**  C6 NEVER judges the moment of the detach: it judges
   **after the re-attach**.  Between the two there is a declared pause, and it is the only
   point of the mesh in which time is an argument of the test (see below).

---------------------------------------------------------------------------
⭐⭐ THE PAUSE MUST BE LONGER THAN THE MEASURED SURVIVAL
---------------------------------------------------------------------------

`[M]` (the measurement of 27 August reported at the top): the monitor **survives** the
detach of the consumer, and at **15 s** it is still there.

⇒ ⛔ A pause shorter than 15 s would make C6 re-attach **before the stage
  has had a chance to die**: the mesh would say green and would have proved
  nothing.  ⭐ The default pause is **twice the measured survival**,
  and it is printed at every round next to the measurement it comes from.

---------------------------------------------------------------------------
⛔ THE GRAFTED FAULT — `--kill-session`, and it is read on the DIFFERENCE
---------------------------------------------------------------------------

§4.1, column «how I know it can say red»: *«the session is killed ⇒ red»*.
Between the detach and the re-attach we do what `logind` does when the tenant
really leaves:

    loginctl terminate-user <chi>   +   pkill -KILL -u <chi>

⛔⛔ **AND HERE LIES THE MOST DELICATE THING OF THE WHOLE MESH** — `LEZIONI.md`
    §1.52.  C6 carries with it a **real and already known** defect: if the stage dies
    with the detach, C6 is red **even without** the grafted fault.  ⇒ Reading
    *«red ⇒ the fault was seen»* would mean certifying the whole net
    on a defect of the PRODUCT instead of on its own — a predicate that cannot
    fail, i.e. §1.44 again.

⭐ **The measurable difference that separates the two cases is the CHILD'S PID**, and the
  two faults have opposite signatures:

    the stage lost (today's defect)       the child is **THE SAME** pid, and the
                                          windows are no longer there
    the session killed (the injection)    ⛔ the child is **NO LONGER THERE**, or it is a
                                          **DIFFERENT** pid

⇒ The fault *«was seen»* **only if the child changed**.  ⛔ If the
  verdict is red but the child is the same, C6 says so out loud: *«red,
  but not because of the fault»*, and exits **1**.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ I looked: it detached, it re-attached, ⭐ it found the
     SAME session and the SAME scene again
  1  ⛔ I looked and it does not hold ⇒ red.  Four kinds, and they are named:
       (a) «the windows are not found again» — the scene is no longer there
       (b) «the stage is not found again»    — the screen went back to black
       (c) «another session»                 — the child changed, or disappeared
       (d) «one cannot get back in»          — the re-attach was REFUSED,
                                               with the same password as a minute ago
     ⚠ and a fifth, milder: «the scene changed» — it is there, but it is not that one
  3  ⛔ I could not look: the client was not admitted, the child was not
     born, ⭐ **or the scene was not seen even BEFORE** — ⛔ and it is NOT a red
  2  the terrain does not hold, or the usage is wrong
  4  ⚠ it does not use it: C6 takes no lock of the card.  It is declared
     here because an outcome that is not used is better written down than left to be
     guessed.

---------------------------------------------------------------------------
⛔ WHAT C6 DOES **NOT** LOOK AT — or someone will trust it too much
---------------------------------------------------------------------------

  · **the leftovers**: that nothing remains after closing is C7, and it is another
    trade.  C6 leaves the session alive until the bench's cleanup.
  · **the product log**: it does not open it (see «the three questions it does not ask»).
  · **the sound, the keys, the latency**: C5, C4, and phase 12.
  · **how many times in a row it holds**: a single round.  ⚠ If one day the defect
    became intermittent, this line will have to be redone like C1 (`--rounds`), and
    it is written now instead of being discovered then.
  · **the very first attach**: C6 starts from an ALREADY LIVE session by
    mandate.  That the session is born and is seen is C1 and C2.
===========================================================================
"""
import argparse
import importlib.util
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# ---------------------------------------------------------------------------
# ⭐⭐ THE CHILD'S NAME — the entry on which «same session» rests.
#
# ⛔ The comparison is by WHOLE name, as in C7: a `remotix-cliente` is not the
#    child, and a substring would let it pass.
# `[M]` 26 Aug 2026 (C7, XFCE box): `pid 12113 remotix, ppid 10575, uid c7u1`.
# ---------------------------------------------------------------------------
CHILD_NAME = "remotix"

# ⛔ The value that means «I looked and it is not there».  ⚠ `None` means «I could
#    not look», and the two things must not have the same face
#    (§4.5, and lesson §1.47).  It is the same convention as C7.
EMPTY = "(nothing)"

# ---------------------------------------------------------------------------
# ⭐ HOW MUCH THE SCENE CAN CHANGE AND STAY «THE SAME» — and it is not generic
#    prudence: it is the half of §4.3 that always gets forgotten.
#
# ⚠ Between one attach and the next the compositor can redraw the bar, the
#   window can move by a few pixels, the 4:2:0 encoding returns
#   slightly different edges.  ⛔ Demanding the same fraction to the thousandth
#   would be the test that rots in a week.
# ⛔ And it is not chosen by eye: `--certify` contains the case «the fraction
#   moved by as much as the deviation allows ⇒ must stay GREEN» **and** the case
#   «moved too much ⇒ red», which is the guard that keeps the number honest.
# `[?]` The value is PRUDENT and not measured on the real thing: ⇒ it is an argument
#   (`--maximum-gap`), and it is calibrated at the first green round.
# ---------------------------------------------------------------------------
MAXIMUM_GAP = 0.25

# ---------------------------------------------------------------------------
# ⭐⭐ THE MEASURED SURVIVAL OF THE MONITOR, and it is from here that the pause comes.
#
# `[M]` 27 Aug 2026, isolated bench with real Mutter (⛔ measurement of another
# agent, not mine): with the PipeWire consumer detached, the `wl_output` at **15 s**
# is still there.  ⇒ The default pause is TWICE that: below that threshold C6
# would re-attach before the stage had a chance to die, and would say green
# without having proved anything.
# ---------------------------------------------------------------------------
MEASURED_SURVIVAL_S = 15.0
DEFAULT_PAUSE_S = 2 * MEASURED_SURVIVAL_S


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE JUDGES ARE IMPORTED, NOT REWRITTEN — and here there are TWO
# ═══════════════════════════════════════════════════════════════════════════
def _load(paths, name):
    """Loads the first module that exists, or `None`.  ⛔ It is a LOADER, not a
       judge: it decides nothing, it only finds the file."""
    for p in paths:
        if not os.path.exists(p):
            continue
        spec = importlib.util.spec_from_file_location(name, p)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        return m
    return None


_C1 = None


def admission_home():
    """⭐⭐ «WAS THE CLIENT ADMITTED?» — ⛔ and its home is C1, not this file.

    ⛔ Until 27 August 2026 there was `"ADMITTED" in coda` here, ⭐ and it could not
       say no: `[R]` `01-b3-cliente.py` prints that word also in the
       **two refusal messages** — «FAREWELL instead of ADMITTED: reason …»
       (:1315) and «expected ADMITTED, arrived …» (:1322) — and prints them on
       **stdout**, i.e. exactly where it looked.  ⇒ `LEZIONI.md` §1.44, a
       predicate that cannot fail: C6 believed it had got back in **even when it
       had been turned away**, and then blamed the product if the scene was not
       there.  ⚠ And the trouble is double here, because `osservazione()` has always declared
       three states (`True`/`False`/`None`) and the old predicate
       never produced the third.
    ⚠ It was in five meshes: it lives in C1 only (§1.47), and the others import it.
    ⛔ If it does not load we exit **3** and say so: ⛔ we do not silently fall back
       on the poor predicate — which is the defect being cured.
    """
    global _C1
    if _C1 is None:
        m = _load([os.path.join(HERE, "11-c1-nasce-e-si-vede.py"),
                     os.path.join(os.path.dirname(HERE), "11-scatole",
                                  "11-c1-nasce-e-si-vede.py")],
                    "c1_ammissione")
        # ⛔ We verify that what is needed is there, we do not trust the name
        #    of the file (`CODER.md` §3.9).
        # ⭐ From C1 come TWO things: the admission predicate and the
        #    guarantee of the card's groups.  Same reason, same single
        #    place (§1.47).  ⛔ We verify they are all there.
        if m is not None and all(
                callable(getattr(m, x, None))
                for x in ("was_admitted", "certify_admission",
                          "ensure_groups", "group_verdict",
                          "certify_groups")):
            _C1 = m
    if _C1 is None:
        print("⛔ I cannot find `11-c1-nasce-e-si-vede.py` next to me, and from there")
        print("   comes the predicate «was the client ADMITTED?».")
        print("⇒ I could not look — ⛔ and it is NOT a red (§4.5).")
        sys.exit(3)
    return _C1


def was_admitted(queue):
    """⭐ `True` admitted · `False` **TURNED AWAY** · `None` said nothing.

    ⛔ `False` is not a product red: `judge()` brings it to **3**.
    """
    return admission_home().was_admitted(queue)


def ensure_groups(chi, prefix="   "):
    """⭐⭐ THE CARD'S GROUPS — ⛔ and this too lives in one place only (C1).

    Returns `(esito, perche)`: `0` = the tenant sees and it can be measured,
    `3` = ⛔ it is NOT measured.

    ⛔ Until 27 August 2026 this mesh created the tenant with
       `usermod -aG video,render` **and did not read back**: two nailed-down names (which
       belong to ONE distribution) and no verification.  ⭐ `[M]` without the groups
       of the `/dev/dri` nodes the session is born BLIND — 0 of 4, never in 90 s, zero
       frames — and this mesh would have measured the darkness calling it
       a product defect (`fasi/10-…` §7.4).
    ⭐ The work is done by `attrezzi-gruppi-scheda.sh`, which reads the gids from the NODES and
       reads back comparing the numbers.  ⛔ No copy of it is made here (§1.47).
    """
    return admission_home().ensure_groups(chi, prefix)


def image_judge():
    """⭐ The judge of DEGENERATION: `10-f1-testimone.py`.

    ⛔ It is already calibrated on the real thing (25 August 2026: black desktop measured, threshold
       of «near-black» put in the middle of the gap between the two worlds).  Rewriting
       a copy here would mean two judges that can diverge
       silently — and the day they diverge, the red would be given by the
       wrong one.
    ⚠ It is looked for next to me (inside the box it is in `/opt/remotix`) and one
      level up (in the repository it is in `banchi/`).
    """
    return _load([os.path.join(HERE, "10-f1-testimone.py"),
                    os.path.join(os.path.dirname(HERE), "10-f1-testimone.py")],
                   "testimone10f1")


def color_reader():
    """⭐⭐ The judge of the scene's COLOUR: it is **C8**'s, not another one.

    ⛔ And the reason is worth more than convenience: C6 opens **the same window
       on the same page** that C8 opens.  ⇒ If the colour, the tolerance and the
       minimum fraction were written in two files, the day someone
       calibrates C8 the two meshes would start judging the same image in
       two different ways — and nobody would notice, because both
       would keep running.
    ⚠ And the calibration of that reader is already done and already tested: the
      certification of C8 contains the case «colour shifted by as much as the
      tolerance allows ⇒ must be GREEN».  ⛔ C6 does not redo it: it inherits it.
    """
    return _load([os.path.join(HERE, "11-c8-il-secondo-apre-il-browser.py")],
                   "c8_browser")


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE JUDGE — ⛔ a PURE function: it does not touch the world, and so it
#                 is certified without boxes, without sessions and without network.
# ═══════════════════════════════════════════════════════════════════════════
def observation(admitted=None, child=None, fraction=None, verdict=None,
                 frames=None):
    """What was seen in ONE attach.

    ⛔ Every entry has three states and not two: `None` = «I could not look»,
       the value = «I looked».  ⚠ For the child there is also `EMPTY` = «I
       looked and it was not there», which ⛔ is not the same thing as `None`.
    """
    return {"admitted": admitted, "child": child, "fraction": fraction,
            "verdict": verdict, "frames": frames}


def judge(before, after, minimum_fraction, maximum_gap=MAXIMUM_GAP):
    """⭐ The judgement, all in here.  Returns `(esito, kind, motivi)`.

    `kind` is a word for whoever reads: «found again» · «the windows are not
    found again» · «the stage is not found again» · «the scene changed» ·
    «another session» · «the session is gone» · «one cannot get back in» ·
    «I do not know».
    """
    # ═══════════════════════════════════════════════════════════════════════
    # THE GUARDS OF THE «BEFORE» — ⛔ without these the comparison is between two zeros
    # ═══════════════════════════════════════════════════════════════════════
    if before["admitted"] is not True:
        return 3, "I do not know", [
            "the client of the FIRST attach was not admitted: there is",
            "no live session to find again, and C6 starts from a session",
            "already alive by mandate (§4.1).",
        ]
    if before["child"] is None:
        return 3, "I do not know", [
            "I could not read the tenant's processes BEFORE the detach",
            "⇒ I do not know which session I should find again.",
        ]
    if before["child"] == EMPTY:
        return 3, "I do not know", [
            "the tenant's «%s» child was not there even BEFORE the detach:"
            % CHILD_NAME,
            "the session did not really start.  ⛔ And a session that did not",
            "start can neither be lost nor found again.",
        ]
    if before["fraction"] is None:
        return 3, "I do not know", [
            "I could not look at the image BEFORE the detach (no",
            "frame from the wire, or unreadable image).",
            "⛔ And «I did not look» is not «the screen was empty».",
        ]
    # ⭐⭐⭐ THE GUARD THAT HOLDS EVERYTHING UP (see the top): two zeros are
    #      equal, and «same fraction» would be GREEN on a test that has
    #      never seen anything.
    if before["fraction"] < minimum_fraction:
        return 3, "I do not know", [
            "⛔ THE SCENE WAS NOT SEEN EVEN BEFORE THE DETACH: it covers",
            "   %.1f%% of the screen and at least %.0f%% would be needed."
            % (before["fraction"] * 100, minimum_fraction * 100),
            "   The image from before is: «%s»." % (before["verdict"] or "?"),
            "⇒ I cannot ask whether a scene is FOUND AGAIN if it was not there.",
            "⛔ And this is NOT a red of C6: it is a defect UPSTREAM — a",
            "   «black» or «near-black» desktop is the late birth",
            "   (§7-bis.13), a «drawn» desktop without the colour of the scene",
            "   is the browser that did not open the window.",
        ]

    # ═══════════════════════════════════════════════════════════════════════
    # THE RE-ATTACH — ⭐ from here on we JUDGE
    # ═══════════════════════════════════════════════════════════════════════
    if after["admitted"] is None:
        return 3, "I do not know", [
            "the client of the RE-ATTACH did not come back: it got stuck itself.",
            "⛔ It is a fault of the BENCH, not of the product (`LEZIONI.md` §1.51).",
        ]
    if after["admitted"] is False:
        return 1, "one cannot get back in", [
            "⛔ the RE-ATTACH was REFUSED, and the same password was good",
            "   a minute ago, on the same port and with the same tenant.",
            "⇒ «it detaches and finds itself again» fails even before the pixels: whoever",
            "  detaches can no longer get back in.",
        ]

    # ⚠ The «same session» half.  ⛔ `None` is not «not there»: if I could not
    #   read the processes, that half stays MUTE — and a mute half
    #   cannot produce a green (§1.47).
    session_muted = False
    if after["child"] is None:
        session_muted = True
    elif after["child"] == EMPTY:
        return 1, "the session is gone", [
            "after the re-attach the tenant no longer has any «%s» child."
            % CHILD_NAME,
            "⛔ It did not find its session again: there is none.",
        ]
    elif after["child"] != before["child"]:
        return 1, "another session", [
            "the child CHANGED between the two attaches: %s ⇒ %s"
            % (before["child"], after["child"]),
            "⛔ Whoever re-attached found a NEW session, not its own:",
            "   what it had opened is nowhere.",
        ]

    if after["fraction"] is None:
        return 3, "I do not know", [
            "I could not look at the image AFTER the re-attach (no",
            "frame from the wire, or unreadable image).",
            "⚠ And here C6 is more prudent than it could be: «no frame",
            "  after the re-attach» could be the lost stage, ⛔ but it could",
            "  be the wire — and I have no way of separating them.  ⇒ I say «I do not",
            "  know» and name the doubt, instead of choosing the red that would",
            "  suit me.",
        ]

    if after["fraction"] < minimum_fraction:
        degenerate = after["verdict"] in ("nero", "quasi-nero")
        if degenerate:
            return 1, "the stage is not found again", [
                "after the re-attach the screen is «%s»: the scene covered"
                % after["verdict"],
                "%.1f%% ⇒ %.1f%%." % (before["fraction"] * 100,
                                      after["fraction"] * 100),
                "⛔ It is not «the window closed»: there is NOTHING left to",
                "   see.  ⇒ It is the stage that the detach took away —",
                "   i.e. I4 broken from the user's side.",
            ]
        return 1, "the windows are not found again", [
            "after the re-attach the desktop is «%s» — there is a screen — ⛔ but the"
            % (after["verdict"] or "?"),
            "scene is no longer there: it covered %.1f%% and now it covers %.1f%%."
            % (before["fraction"] * 100, after["fraction"] * 100),
            "⇒ The session was found again, the WINDOWS were not.",
        ]

    gap = abs(after["fraction"] - before["fraction"])
    if gap > maximum_gap:
        return 1, "the scene changed", [
            "the scene is still there, ⛔ but it is not that one: it covered %.1f%% and"
            % (before["fraction"] * 100),
            "now it covers %.1f%% (deviation %.3f, the maximum allowed is %.3f)."
            % (after["fraction"] * 100, gap, maximum_gap),
            "⚠ It is the mildest red of the five: something was found again, but",
            "  not everything.  ⇒ If this fired on a healthy product, the number",
            "  to calibrate is `--maximum-gap`, and it must be calibrated with a measurement",
            "  underneath — not widened until it goes quiet.",
        ]

    if session_muted:
        return 3, "I do not know", [
            "⭐ the image holds: the scene was found again (%.1f%% ⇒ %.1f%%,"
            % (before["fraction"] * 100, after["fraction"] * 100),
            "   deviation %.3f).  ⛔ BUT I could not read the processes after the" % gap,
            "   re-attach ⇒ I do not know whether it is the SAME session or a new one that",
            "   resembles it.",
            "⇒ Half a judgement is not a green (`LEZIONI.md` §1.47).",
        ]

    return 0, "found again", [
        "the client detached, waited, re-attached,",
        "⭐ and found the SAME session again (child %s) and the SAME scene"
        % before["child"],
        "  (%.1f%% ⇒ %.1f%%, deviation %.3f ≤ %.3f)"
        % (before["fraction"] * 100, after["fraction"] * 100, gap,
           maximum_gap),
    ]


def fault_bitten(before, after):
    """⛔⛔ §1.52 — with the grafted fault the COLOUR of the verdict is not enough.

    ⭐ C6 carries with it a real and already known defect (the stage that dies with the
      detach), and with it it is red **even without** injection.  ⇒ A simple
      *«red ⇒ seen»* would say «the fault was seen» even if the injection
      had done nothing: a predicate that cannot fail (§1.44), and
      this time holding up the certification of the whole net (C13).

    ⇒ The bite is measured on the **DIFFERENCE** the injection produced, and it is
      the **CHILD'S PID**:

        stage lost (product defect)         the child is THE SAME
        session killed (the injection)      ⛔ the child is no longer there, or it is a
                                            different pid

    ⛔ And if I could not read the processes — before or after — it is not «seen»:
       «I do not know» is not a proof that the fault bit.
    """
    p = before.get("child")
    d = after.get("child")
    if p in (None, EMPTY):
        return False
    if d is None:
        return False
    return d != p


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CERTIFICATION — synthetic cases, and ⭐ it must run ON THE LAPTOP
# ═══════════════════════════════════════════════════════════════════════════
def certify(minimum_fraction=None, gap=MAXIMUM_GAP):
    """⛔ It proves that the judge can say green, red and «I do not know».

    ⚠ And it declares what it covers and what it does not.
      COVERS: the **decision** (the guards and the comparison between the two
      observations), the reading of the **bite** of the grafted fault, and ⭐ that the
      colour reader imported from C8 is REALLY alive — a synthetic
      image goes through it and we look at what number comes out.
      ⛔ DOES NOT COVER: that the browser really opens the window, that the stage is
      remounted, that the frames arrive.  That half is told only by the real
      round inside the box, and it is the `--kill-session` acceptance test.
    ⇒ A certification that declares itself wider than it is is worth less than
      no certification (C1's rule).
    """
    c8 = color_reader()
    if c8 is None:
        print("⛔ I cannot find C8 next to me: the colour reader is ITS and I do not")
        print("   rewrite it here.  ⇒ I could not look")
        return 3
    if minimum_fraction is None:
        minimum_fraction = c8.MINIMUM_FRACTION

    fm = minimum_fraction
    print("== certification of C6's judge ==")
    print("   ⛔ it covers the DECISION and the imported reader, not the real round")
    print("   yardstick: colour %s ±%d per channel (from C8) · at least %.0f%% of the"
          % (c8.COLOR, c8.TOLERANCE, fm * 100))
    print("          screen · maximum deviation between before and after %.3f" % gap)
    print("   pause: %.0f s = 2 × the measured survival (%.0f s)\n"
          % (DEFAULT_PAUSE_S, MEASURED_SURVIVAL_S))

    # The two «healthy» observations, from which every case is derived by changing one
    # thing only — ⭐ §3.3 of the phase document: one thing is moved at a time.
    def viva(**c):
        d = observation(admitted=True, child="12113", fraction=0.62,
                         verdict="disegnato", frames=180)
        d.update(c)
        return d

    cases = [
        # ── the healthy round ───────────────────────────────────────────────
        ("⭐ it detaches and finds itself again: same session, same scene",
         dict(before=viva(), after=viva()), (0, "found again")),

        ("⭐ the scene moved a little ⇒ must be GREEN",
         dict(before=viva(), after=viva(fraction=0.62 - gap + 0.02)),
         (0, "found again")),

        # ── the reds, one per kind ──────────────────────────────────────────
        ("⛔⛔ TODAY'S DEFECT: same child, ⛔ windows gone",
         dict(before=viva(), after=viva(fraction=0.001, verdict="disegnato")),
         (1, "the windows are not found again")),

        ("⛔⛔ …and if the screen went back to BLACK it is another kind of red",
         dict(before=viva(), after=viva(fraction=0.0, verdict="nero")),
         (1, "the stage is not found again")),

        ("⛔ «near-black» counts as black: there is the bar and nothing else",
         dict(before=viva(), after=viva(fraction=0.0, verdict="quasi-nero")),
         (1, "the stage is not found again")),

        ("⛔ THE GRAFTED FAULT: the session was killed ⇒ different child",
         dict(before=viva(), after=viva(child="20044", fraction=0.0,
                                      verdict="nero")),
         (1, "another session")),

        ("⛔ …and if after the re-attach there is no child at all",
         dict(before=viva(), after=viva(child=EMPTY, fraction=0.0,
                                      verdict="nero")),
         (1, "the session is gone")),

        ("⛔ the re-attach is REFUSED, with the password of a minute ago",
         dict(before=viva(), after=viva(admitted=False)), (1, "one cannot get back in")),

        ("⛔ the scene is there but changed TOO MUCH ⇒ mild red",
         dict(before=viva(), after=viva(fraction=0.62 - gap - 0.05)),
         (1, "the scene changed")),

        # ═══════════════════════════════════════════════════════════════════
        # ⭐⭐⭐ THE CASES THIS MESH EXISTS FOR — ⛔ «two zeros are equal»
        #
        # ⚠ Without the guard of the «before», the first of these three would answer
        #   (0, «found again»): the same fraction, the same child, no
        #   difference anywhere.  ⛔ And it would be the most
        #   complacent mesh of the net, silently.
        # ═══════════════════════════════════════════════════════════════════
        ("⭐⭐ the scene was not there EVEN BEFORE (0 ⇒ 0) ⇒ ⛔ NEVER green",
         dict(before=viva(fraction=0.0, verdict="nero"),
              after=viva(fraction=0.0, verdict="nero")), (3, "I do not know")),

        ("⭐⭐ …and not even if AFTER the scene appeared by chance",
         dict(before=viva(fraction=0.0, verdict="nero"), after=viva()),
         (3, "I do not know")),

        ("⭐ the scene was there but below the threshold (5%) ⇒ I looked at nothing",
         dict(before=viva(fraction=0.05), after=viva(fraction=0.05)),
         (3, "I do not know")),

        # ── the bench's «I do not know» ─────────────────────────────────────
        ("⛔ the FIRST attach was not admitted ⇒ I do not know, not a red",
         dict(before=viva(admitted=False), after=viva()), (3, "I do not know")),

        ("⛔ the child was never born BEFORE ⇒ there is nothing to find again",
         dict(before=viva(child=EMPTY), after=viva()), (3, "I do not know")),

        ("⛔ the processes could not be read BEFORE ⇒ I do not know",
         dict(before=viva(child=None), after=viva()), (3, "I do not know")),

        ("⛔ no frame BEFORE ⇒ I do not know, ⛔ not «empty screen»",
         dict(before=viva(fraction=None, verdict=None), after=viva()),
         (3, "I do not know")),

        ("⛔ no frame AFTER ⇒ I do not know, and the doubt is NAMED",
         dict(before=viva(), after=viva(fraction=None, verdict=None)),
         (3, "I do not know")),

        ("⛔ the client of the re-attach got stuck ⇒ fault of the BENCH",
         dict(before=viva(), after=viva(admitted=None)), (3, "I do not know")),

        # ⛔ §1.47: the image holds but the «same session» half is MUTE.
        ("⛔ scene found again, ⛔ but I do not know if it is the same session ⇒ I do not know",
         dict(before=viva(), after=viva(child=None)), (3, "I do not know")),
    ]

    troubles = 0
    for name, arg, expected in cases:
        outcome, kind, _m = judge(minimum_fraction=fm, maximum_gap=gap,
                                    **arg)
        ok = (outcome, kind) == expected
        print("  %s  %-62s  outcome=%s (%s)   expected %s (%s)"
              % ("OK " if ok else "NO ", name, outcome, kind,
                 expected[0], expected[1]))
        if not ok:
            troubles += 1

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE SECOND HALF — «did the fault bite?» is not «is the verdict
    #     red?» (§1.52).  ⛔ For C6 it is the part that is worth the most: the mesh
    #     can already be red on its own.
    # ═══════════════════════════════════════════════════════════════════════
    cases_bitten = [
        ("⭐ the session killed: the child is another one ⇒ SEEN",
         dict(before=viva(), after=viva(child="20044")), True),

        ("⭐ the session killed and no child was born again ⇒ SEEN",
         dict(before=viva(), after=viva(child=EMPTY)), True),

        ("⛔⛔ RED with the child THE SAME: it is the defect of the STAGE, ⛔ not the",
         dict(before=viva(), after=viva(fraction=0.0, verdict="nero")), False),

        ("⛔ I could not read the processes AFTER ⇒ it is NOT «seen»",
         dict(before=viva(), after=viva(child=None)), False),

        ("⛔ I had not read them even BEFORE ⇒ it is NOT «seen»",
         dict(before=viva(child=None), after=viva(child="20044")), False),

        ("⛔ the child was already not there before ⇒ it is NOT «seen»",
         dict(before=viva(child=EMPTY), after=viva(child=EMPTY)), False),
    ]
    print()
    print("   ⛔ and the grafted fault is read on the DIFFERENCE (the PID of the")
    print("      child), not on the colour of the verdict — `LEZIONI.md` §1.52:")
    for name, arg, expected in cases_bitten:
        got = fault_bitten(**arg)
        ok = got is expected
        print("  %s  %-62s  bitten=%-5s  expected %s"
              % ("OK " if ok else "NO ", name, got, expected))
        if not ok:
            troubles += 1

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ THE THIRD HALF — is the READER imported from C8 really alive?
    #
    # ⛔ An imported judge that does not work looks exactly like a
    #    judge that was not called: `LEZIONI.md` §1.46.  ⇒ A synthetic image
    #    is passed through it and we look at what number comes out.
    # ⚠ The CALIBRATION of the reader (shifted colour, tolerance) is NOT redone here:
    #   it is in C8's certification, and duplicating it would mean two calibrations
    #   that can diverge.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    print("   ⭐ and the colour reader is C8's, imported: I pass three images")
    print("      through it to be sure it is alive")
    try:
        import numpy as np
        from PIL import Image
        import tempfile
        lav = tempfile.mkdtemp(prefix="c6cert-")

        def paint(name, fill):
            a = np.zeros((216, 384, 3), dtype="uint8")
            a[:, :] = fill
            p = os.path.join(lav, name + ".png")
            Image.fromarray(a).save(p)
            return p

        prove = [
            ("the scene fills the screen", paint("a", c8.COLOR), True),
            ("a desktop without the scene", paint("b", (58, 62, 70)), False),
            ("a file that is not there ⇒ «I do not know», ⛔ not zero",
             os.path.join(lav, "manca.png"), None),
        ]
        for name, png, expected in prove:
            fr = c8.color_fraction(png)
            if expected is None:
                ok = fr is None
                said = "unknown" if fr is None else "%.3f" % fr
            else:
                ok = fr is not None and ((fr >= fm) == expected)
                said = "unknown" if fr is None else "%.3f" % fr
            print("  %s  %-62s  fraction=%s"
                  % ("OK " if ok else "NO ", name, said))
            if not ok:
                troubles += 1
    except ImportError:
        print("  ⛔  numpy or Pillow is missing: I could NOT test the reader")
        print("      ⇒ and this certification is incomplete, not passed")
        return 3

    # ⭐⭐ THE ADMISSION CASES — ⛔ the ones that were not there before today.
    #    The predicate lives in C1 and is certified with C1's cases: ⛔ a copy
    #    of the cases here would be a second place to diverge from (§1.47).
    print()
    admission_troubles, how_many_admitted = admission_home().certify_admission("C6")
    troubles += admission_troubles

    # ⭐⭐ AND THE CARD GROUPS CASES — ⛔ the other case that was missing:
    #    a tenant without the groups of the nodes ⇒ «I could not look», ⛔
    #    never red.  They live in C1 with the step they certify.
    print()
    group_troubles, how_many_groups = admission_home().certify_groups("C6")
    troubles += group_troubles

    amount = len(cases) + len(cases_bitten) + how_many_admitted + how_many_groups + 3
    print()
    if troubles:
        print("⛔ the judge is NOT reliable: %d cases out of %d wrong"
              % (troubles, amount))
        return 1
    print("⭐ %d cases out of %d: the judge sees the scene when it is found again, it"
          % (amount, amount))
    print("   sees it disappear when it disappears, ⛔ it does NOT say green when the scene")
    print("   was not there even before, and ⭐ it distinguishes «the fault bit» from")
    print("   «it was already red on its own».")
    print("⚠ and it covers the DECISION, not the real round (see the top)")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# THE WORLD — collecting the facts.  ⛔ From here down the machine is TOUCHED.
# ═══════════════════════════════════════════════════════════════════════════
def sh(command, seconds=120):
    """⚠ A shell is used only where it is really needed (`useradd`, `su`, `runuser`):
       `LEZIONI.md` §1.46 — every level of quoting is a place where the
       command can disappear."""
    try:
        return subprocess.run(["/bin/sh", "-c", command],
                              capture_output=True, text=True, timeout=seconds)
    except subprocess.SubprocessError:
        return subprocess.CompletedProcess([], 127, "", "expired")


def run_loop(argv, time_limit=60):
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=time_limit)
        return p.returncode, (p.stdout or "")
    except (OSError, subprocess.SubprocessError):
        return None, ""


def uid_di(chi):
    import pwd
    try:
        return pwd.getpwnam(chi).pw_uid
    except KeyError:
        return None


def child_of(uid):
    """The pid of the tenant's «remotix» child.

    ⛔ Three outcomes and not two: `None` = «/proc could not be read», `EMPTY` =
       «I looked and it is not there», otherwise the pid (or the pids, separated).
    ⚠ `/proc` is read instead of calling `ps`: one shell fewer, and the same
      choice as C7.
    """
    try:
        listing = os.listdir("/proc")
    except OSError:
        return None
    pid = []
    for entry in listing:
        if not entry.isdigit():
            continue
        try:
            if os.stat("/proc/%s" % entry).st_uid != uid:
                continue
            with open("/proc/%s/comm" % entry) as f:
                name = f.read().strip()
        except OSError:
            continue
        if name == CHILD_NAME:
            pid.append(entry)
    if not pid:
        return EMPTY
    return " · ".join(sorted(pid, key=int))


def socket_wayland(uid):
    """The tenant's compositor socket, or `None`.

    ⛔ The name is SEARCHED for, not guessed: nailing down `wayland-0` would mean
       a test that works on one desktop and stays silent on the others — the defect that
       this phase exists not to introduce (the same choice as C8).
    """
    try:
        entries = sorted(os.listdir("/run/user/%d" % uid))
    except OSError:
        return None
    for v in entries:
        if re.match(r"^wayland-[0-9]+$", v):
            return v
    return None


def wait_until(predicate, cap, step=1.0):
    """⭐ We wait for the EVENT, not for the clock (`LEZIONI.md` §1.49).

    Returns `(value, secondi)`; `value` is `None` if the ceiling expired — and
    then ⛔ the caller must say «I do not know», not carry on pretending.
    """
    start_offset = time.time()
    expiry = start_offset + cap
    while time.time() < expiry:
        v = predicate()
        if v:
            return v, time.time() - start_offset
        time.sleep(step)
    return None, time.time() - start_offset


# ---------------------------------------------------------------------------
# THE ATTACH — the test client, and the image that comes out of it
# ---------------------------------------------------------------------------
def load(fpath):
    try:
        with open(fpath, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return ""


def attach(chi, a, stays, diary, video=None):
    """Launches the client IN THE BACKGROUND and returns `(processo, presa_del_diario)`.

    ⛔ In the background and non-blocking, and the reason is the whole mesh: the scene
       must be opened **while a client is attached**.  `[M]` (the measurement of 27
       August at the top) the `wl_output` is born only when a consumer
       hooks on ⇒ opening a window with the wire detached would mean opening it on
       a desktop that has no screen, and then accusing the product of not
       having found it again.

    ⛔⛔ AND WHAT IT SAYS ENDS UP IN A FILE, not in a `PIPE` — ⚠ and this line
        is worth more than it looks.  With `stdout=PIPE` nobody reads the pipe
        while the bench sleeps (and here it sleeps almost a minute, waiting for the
        scene): the pipe fills up, ⛔ **the client blocks on the write**,
        and the bench would see it as «the product no longer sends anything».
        ⇒ A fault of the BENCH with the face of a fault of the product, which is
          the §1.51 family.
    ⭐ And in addition the diary stays on disk for whoever diagnoses, instead of
      disappearing inside a variable.
    """
    argv = ["python3", "-u", a.client,
            "--address", a.address, "--port", str(a.port),
            "--user", chi, "--password", a.password,
            "--stay", str(stays)]
    if video:
        if os.path.exists(video):
            os.unlink(video)
        argv += ["--video-out", video]
    take = open(diary, "w")
    return subprocess.Popen(argv, stdout=take, stderr=subprocess.STDOUT,
                            text=True), take


def collect_client(proc, take, diary, cap):
    """Waits for the client to finish.  Returns `(admitted, fotogrammi, coda)`.

    ⛔ `admitted` has THREE states: `True`, `False`, and `None` = «the client did not
       come back», which is a fault of the BENCH and not of the product (§1.51).
    """
    expired = False
    try:
        proc.wait(timeout=cap)
    except subprocess.TimeoutExpired:
        proc.kill()
        try:
            proc.wait(timeout=30)
        except subprocess.SubprocessError:
            pass
        expired = True
    try:
        take.close()
    except OSError:
        pass
    queue = load(diary)
    if expired:
        return None, None, ("the test client did not come back within the "
                            "ceiling\n" + queue)
    # ⛔ NOT `"ADMITTED" in queue`: the word is also in the two refusals, and it
    #    arrives on stdout — see `was_admitted()` at the top.  ⭐ And so
    #    the third state promised by the docstring above really exists.
    admitted = was_admitted(queue)
    # ⚠ The frame count is read from the client's `[vid]` line, as
    #   C8 does: it is information, ⛔ not a verdict.
    amount = None
    for line in queue.splitlines():
        if "[vid]" in line and "no frame" not in line:
            try:
                amount = int(line.split("[vid]", 1)[1].strip().split()[0])
            except (ValueError, IndexError):
                pass
    return admitted, amount, queue


def image_from_stream(stream, report):
    """The LAST frame of the stream, as PNG.  `None` if none was made.

    ⛔ `-update 1` keeps the LAST: it is what the desktop shows now.  The
       first would be the opening keyframe, i.e. a minute ago — and for a mesh
       that asks *«what do I see WHEN I come back»* it would be the wrong question.
    """
    if os.path.exists(report):
        os.unlink(report)
    if not os.path.exists(stream) or os.path.getsize(stream) == 0:
        return None
    sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -update 1 -y %s"
       % (stream, report), seconds=240)
    if os.path.exists(report) and os.path.getsize(report):
        return report
    return None


# ---------------------------------------------------------------------------
# THE SCENE — ⭐ the window that must be found again
# ---------------------------------------------------------------------------
def open_scene(chi, a):
    """Switches on the browser full screen on the page of the declared colour.

    ⛔ The Wayland socket is SEARCHED for (see `socket_wayland`).
    ⚠ The browser's log ends up in ITS home: `[M]` C8, 26 Aug 2026 — the
      bench's working folder belongs to `root` with mode 0755 and the browser runs
      as a user, and a file that cannot be written became «the browser did not
      draw», i.e. ⛔ the bench giving red to itself.
    """
    uid = uid_di(chi)
    if uid is None:
        return None, "I do not know the uid of «%s»" % chi
    display = socket_wayland(uid)
    if not display:
        return None, ("in /run/user/%d there is no wayland socket: the "
                      "session does not have a compositor the browser can "
                      "talk to" % uid)
    # ⛔ `setsid` + stdin closed: without it, the browser ends up in a BACKGROUND
    #    process group of the terminal that launched the net and the first
    #    `tcsetattr` gets it a SIGTTOU ⇒ it stays in state `T` from the first
    #    instant (22 Sep 2026, seen in C3 on all three boxes).
    sh("setsid runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/%d WAYLAND_DISPLAY=%s "
       "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
       "%s --kiosk file://%s < /dev/null > /home/%s/.c6-scena.log 2>&1 &"
       % (chi, uid, display, chi, a.browser, a.page, chi), seconds=30)
    return display, None


def browser_profile(chi):
    """⭐ The EVENT «the browser started»: its profile exists.

    ⛔ It is not «the window is seen» — that is said only by the pixel, and it is the
       judgement.  ⚠ But it is better than a blind wait: it separates «the browser did not
       start at all» from «it started and is taking its time».
    """
    r = sh("ls -d /home/%s/.cache/mozilla/firefox/*/ 2>/dev/null | head -1" % chi)
    return r.stdout.strip() or None


def warm_up_browser(chi, a, report):
    """⭐⭐ THE FIRST START IS DONE OUTSIDE THE SESSION, and it serves TWO things.

    1. ⛔ **It warms up the profile.**  `LEZIONI.md` §1.45: the first start of Firefox
       in a cold box well exceeds 25 s, because it has to create
       the profile.  ⇒ If that first start happened INSIDE the session, the wait
       for the scene would have to be very long, and every red of C6 would be
       indistinguishable from its own ceiling — which is exactly the defect for which
       C8 gave red to both tenants.

    2. ⭐ **It is a GUARD.**  If in this box the browser cannot
       draw the page even on its own, C6's question cannot be asked:
       ⛔ it is not a product red, it is a box without a scene.  `[M]` C8,
       26 Aug 2026: without `libpci3` Firefox produced no image, and the
       bench read it as a product fault.

    ⚠ And the ceiling is ITS OWN (`--wait-scene`), not lent by another wait
      (§1.45).  ⛔ And the FILE is judged, not the exit code: `[M]` §1.50 —
      with a tight ceiling Firefox exits 124 and **the PNG is there anyway**.
    """
    if os.path.exists(report):
        os.unlink(report)
    its = "/home/%s/.c6-scaldata.png" % chi
    sh("rm -f %s" % its)
    r = sh("runuser -u %s -- env HOME=/home/%s MOZ_HEADLESS=1 "
           "timeout %d %s --headless --screenshot %s file://%s"
           % (chi, chi, int(a.wait_scene), a.browser, its, a.page),
           seconds=int(a.wait_scene) + 60)
    if os.path.exists(its) and os.path.getsize(its):
        sh("cp -f %s %s" % (its, report))
    said = ((r.stdout or "") + (r.stderr or "")).strip()
    if os.path.exists(report) and os.path.getsize(report):
        return report, said[-160:]
    return None, said[-160:]


# ---------------------------------------------------------------------------
# THE TENANT — it is created new, and ⛔ deleted BEFORE creating it
# ---------------------------------------------------------------------------
def clear_out(chi, delete=True):
    """⭐ The BENCH's cleanup, which ⛔ is not the test.

    The tenant of THIS round is closed **by name**, never a global pattern
    (phase 10 §7.3, where a global `pkill -f` risked killing the work
    of another test in progress).  ⚠ And it is done in a `finally`: a bench that leaves
    its leftovers makes the next bench red, and that red is not the product's.
    """
    run_loop(["loginctl", "terminate-user", chi], time_limit=60)
    time.sleep(1.0)
    run_loop(["pkill", "-KILL", "-u", chi], time_limit=60)
    time.sleep(0.5)
    if delete:
        run_loop(["userdel", "-r", chi], time_limit=120)
        run_loop(["rm", "-rf", "/home/%s" % chi], time_limit=60)


def create(chi, password):
    """Creates the tenant **as the product creates it**: `useradd -m`, the password,
       ⭐ and the card's groups READ FROM THE NODES and read back.

    ⛔ Until 27 August 2026 there was `usermod -aG video,render` here: two nailed-down
       names (which belong to ONE distribution) and no verification.  ⭐ `[M]`
       without the groups of the `/dev/dri` nodes the session is born BLIND — 0 of 4,
       zero frames — and C6 would have said «the scene is not found again»
       accusing the product of a fault of the bench (§1.51).
    """
    r = sh("useradd -m -s /bin/bash %s && "
           "printf '%s:%s\n' | chpasswd" % (chi, chi, password))
    if r.returncode != 0:
        return False, ((r.stderr or "") + (r.stdout or "")).strip()[:140]
    e_gr, why_groups = ensure_groups(chi, prefix="      ")
    if e_gr != 0:
        return False, why_groups
    return True, ""


def remove_c8_defect(chi, c8):
    """⚠ C6 does NOT test the provisioning defect: it GETS IT OUT OF THE WAY.

    ⛔ And the reason is a real danger between benches: `11-c8` prepares the terrain
       by making `/etc/skel/.cache` a link to `/tmp`, and **does not
       undo it**.  ⇒ If C8 ran before C6 in this box, C6's tenant
       would be born with a shared `~/.cache`, and if `/tmp/mozilla` belonged to a
       tenant of C8 the browser of C6 would not make its profile.
    ⚠ Then C6 would say *«the scene was not seen even before»* — a perfectly
      honest «I do not know», ⛔ but for a defect that is not its own and that a
      day of calibration would not find.
    ⇒ The cure of `src/provisiona.sh` is applied to C6's tenant, and it is the
      SAME line as C8, imported instead of rewritten.
    """
    c8.apply_fix(chi)


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--user", default="c6u1",
                   help="the test tenant: it is created NEW and deleted")
    p.add_argument("--password", default="provanic2026")
    p.add_argument("--port", type=int, default=8511)
    p.add_argument("--address", default="127.0.0.1")
    p.add_argument("--client", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--page", default=os.path.join(HERE, "11-c8-pagina.html"),
                   help="the scene's page: it is C8's, and the colour "
                        "is declared by C8")
    p.add_argument("--browser", default="firefox-esr")
    p.add_argument("--workdir", default="/var/lib/rete11/c6")

    # ── THE WAITS.  ⛔ Each one has its own NAME and its own VALUE (`LEZIONI.md`
    #    §1.45): reusing a ceiling because «it is there and more or less works» is the
    #    exact way in which a red stops distinguishing the fault from the bench.
    p.add_argument("--stay-birth", type=float, default=30.0,
                   help="how long the client that makes the session BE BORN stays "
                        "attached. ⚠ No frame is asked of it")
    p.add_argument("--wait-admission", type=float, default=60.0,
                   help="how long to wait for the client's diary to say "
                        "ADMITTED. ⭐ It is an EVENT, not a blind wait")
    p.add_argument("--latch", type=float, default=5.0,
                   help="how long the consumer is given to hook onto the stream "
                        "AFTER the admission. `[M]` the wl_output is born 65÷93 ms "
                        "after the hooking: 5 s is very wide on purpose, and it is "
                        "the only point where this time is spent")
    p.add_argument("--shot-tail", type=float, default=10.0,
                   help="how long the client stays attached AFTER the scene has "
                        "settled. ⛔ It is needed because the photo is the LAST frame: "
                        "without a tail the last would be the one from half a second "
                        "before the window was in place")
    p.add_argument("--wait-compositor", type=float, default=240.0,
                   help="how long to wait for the tenant's wayland socket "
                        "to appear. ⛔ On GNOME `[M]` 101.0 s (C1, 27 Aug "
                        "2026, maximum over three sessions), and there is a defect "
                        "of the BOX (polkit, ~97 s) being cured right now: "
                        "⇒ the value is wide ON PURPOSE and must be recalibrated when the "
                        "cure is measured")
    p.add_argument("--wait-child", type=float, default=90.0,
                   help="how long to wait for the «%s» child to appear among the "
                        "tenant's processes. Expired: «I do not know»"
                        % CHILD_NAME)
    p.add_argument("--wait-scene", type=float, default=180.0,
                   help="how long the browser is given to create its profile and "
                        "draw the page OUTSIDE the session (the "
                        "warm-up). ⛔ Wide: `LEZIONI.md` §1.45, the first "
                        "start in a cold box exceeds 25 s")
    p.add_argument("--scene-settle", type=float, default=40.0,
                   help="how long the window is given to appear in the image "
                        "INSIDE the session, after the profile is already there. "
                        "`[?]` not measured: prudent value, to calibrate")
    p.add_argument("--stay-before", type=float, default=75.0,
                   help="how long the client that takes the BEFORE photo stays "
                        "attached. ⚠ It must be longer than --scene-settle, or the "
                        "photo arrives before the window")
    p.add_argument("--detached-pause", type=float, default=DEFAULT_PAUSE_S,
                   help="⭐⭐ how long we stay DETACHED. The default is "
                        "TWICE the measured survival of the monitor "
                        "(`[M]` 15 s): below that threshold one would re-attach "
                        "before the stage has a chance to die, ⛔ and the "
                        "mesh would say green without having proved anything")
    p.add_argument("--stay-after", type=float, default=60.0,
                   help="how long the client of the RE-ATTACH stays attached. ⚠ Longer "
                        "than the first on purpose: at the re-attach the stage may "
                        "have to be remounted, and a photo taken too early "
                        "would say «black» on a desktop that is coming back")

    p.add_argument("--maximum-gap", type=float, default=MAXIMUM_GAP,
                   help="by how much the scene's fraction can change between "
                        "before and after and stay «the same»")
    p.add_argument("--kill-session", action="store_true",
                   help="⛔ THE GRAFTED FAULT: between the detach and the re-attach "
                        "the tenant's session is closed. It must give RED, "
                        "⭐ and the bite is read on the child's PID")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()

    if a.certify:
        sys.exit(certify(gap=a.maximum_gap))

    if os.geteuid() != 0:
        print("⛔ it must be run as administrator: it creates and deletes a tenant")
        sys.exit(2)
    # ⛔⛔ THE BUDGET OF THE FIRST ATTACH IS VERIFIED BEFORE STARTING.
    #
    # ⚠ The «before» client must stay attached for EVERYTHING: the admission,
    #   the consumer's hooking, the settling of the scene, and a tail because the
    #   photo is the LAST frame.  If the sum does not add up, the client finishes
    #   writing the stream **while the window is still appearing** ⇒ the
    #   photo is from before the scene, ⛔ C6 says «the scene was not seen even
    #   BEFORE» and whoever reads blames the product.
    # ⭐ It is §1.45 applied to the sum instead of the single ceiling: a right
    #   ceiling and a wrong sum give the same false red.
    minimum = a.latch + a.scene_settle + a.shot_tail
    if a.stay_before < minimum:
        print("⛔ --stay-before is %.0f s and at least %.0f are needed:"
              % (a.stay_before, minimum))
        print("   hooking %.0f + settling of the scene %.0f + tail %.0f"
              % (a.latch, a.scene_settle, a.shot_tail))
        print("   ⇒ this way the photo would arrive before the window, and the red")
        print("     would be the BENCH's, not the product's")
        sys.exit(2)

    # ── the things without which we do not judge ──────────────────────────
    c8 = color_reader()
    if c8 is None:
        print("⛔ I cannot find C8 next to me: the colour reader is ITS and I do not")
        print("   rewrite it here.  ⇒ I could not look")
        sys.exit(3)
    referee = image_judge()
    if referee is None:
        print("⛔ I cannot find the image judge (10-f1-testimone.py)")
        print("   ⇒ I could not look")
        sys.exit(3)
    for desc, dove in (("the test client", a.client),
                      ("the scene's page", a.page)):
        if not os.path.exists(dove):
            print("⛔ I cannot find %s: %s" % (desc, dove))
            print("   ⇒ I could not look")
            sys.exit(3)
    for tool, why in ((a.browser, "I cannot open any window"),
                             ("ffmpeg", "the frames do not become an image")):
        if sh("command -v %s" % tool).returncode != 0:
            print("⛔ the box does not have %s: %s" % (tool, why))
            print("   ⇒ I could not look")
            sys.exit(3)

    fm = c8.MINIMUM_FRACTION
    os.makedirs(a.workdir, exist_ok=True)
    chi = a.user

    print("== C6 — it detaches and finds itself again ==")
    print("   tenant «%s» · port %d · scene %s"
          % (chi, a.port, os.path.basename(a.page)))
    print("   yardstick: colour %s ±%d per channel (C8's) · at least %.0f%% of the"
          % (c8.COLOR, c8.TOLERANCE, fm * 100))
    print("          screen · maximum deviation before/after %.3f" % a.maximum_gap)
    print("   detached pause: %.0f s  (⭐ = 2 × the %.0f s of measured survival "
          "of the monitor)" % (a.detached_pause, MEASURED_SURVIVAL_S))
    print("   mode: %s" % (
        "⛔ GRAFTED FAULT — between the detach and the re-attach the "
        "session is KILLED: it must give RED, and the bite is the child's PID changing"
        if a.kill_session else
        "normal round: it opens, the scene is seen, it detaches, it comes back"))
    print()

    # ⛔ IT IS DELETED BEFORE CREATING IT: «from zero» also includes «from zero
    #    with respect to myself of yesterday» (`LEZIONI.md` §1.39).
    clear_out(chi)
    completed, why = create(chi, a.password)
    if not completed:
        print("⛔ I could not create «%s»: %s" % (chi, why))
        print("   ⇒ I could not look")
        sys.exit(3)
    remove_c8_defect(chi, c8)
    uid = uid_di(chi)

    outcome = 3
    before = observation()
    after = observation()
    try:
        # ═══════════════════════════════════════════════════════════════════
        # 1 · THE SESSION BECOMES ALIVE — ⭐ C6 starts from here, by mandate
        # ═══════════════════════════════════════════════════════════════════
        print("  1 · I make the session be born (client attached %.0f s)…"
              % a.stay_birth)
        dn = os.path.join(a.workdir, "nascita.log")
        pn, sn = attach(chi, a, a.stay_birth, dn)
        admitted_n, _f, tail_n = collect_client(
            pn, sn, dn, max(120.0, a.stay_birth * 4))
        if admitted_n is None:
            print("      ⛔ the test client did not come back: it is a fault of the "
                  "BENCH (§1.51)")
            print("   ⇒ I could not look")
            sys.exit(3)
        if not admitted_n:
            # ⛔ «Not admitted» on its own is a silence: the REASON is carried
            #    next to the symptom (C1's lesson, 26 Aug 2026).
            reason = "?"
            for line in reversed((tail_n or "").strip().splitlines()):
                line = line.strip()
                if line and not line.startswith("=="):
                    reason = line[:100]
                    break
            print("      ⛔ NOT admitted: %s" % reason)
            print("   ⇒ I could not look")
            sys.exit(3)

        child, how_much = wait_until(lambda: (lambda v: v if v != EMPTY else None)(
            child_of(uid)), a.wait_child)
        print("      the «%s» child: %s"
              % (CHILD_NAME,
                 ("⭐ pid %s, after %.1f s" % (child, how_much)) if child
                 else "⛔ never appeared in %.0f s" % a.wait_child))
        display, how_much = wait_until(lambda: socket_wayland(uid),
                                  a.wait_compositor)
        print("      the compositor: %s"
              % (("⭐ %s, after %.1f s" % (display, how_much)) if display
                 else "⛔ no wayland socket in %.0f s"
                      % a.wait_compositor))
        if not display:
            print()
            print("⚠ NOT JUDGING (outcome 3) — without a compositor I cannot open")
            print("  any window, ⇒ there is no scene to find again.")
            print("  ⛔ And it is not a red of C6: it is the birth of the session,")
            print("     which is the question of C1 and C2.")
            sys.exit(3)

        # ═══════════════════════════════════════════════════════════════════
        # 2 · THE SCENE — ⭐ first it is warmed up OUTSIDE, then opened INSIDE
        # ═══════════════════════════════════════════════════════════════════
        print("  2 · I warm up the browser outside the session (ceiling %.0f s)…"
              % a.wait_scene)
        png_s, said = warm_up_browser(chi, a, os.path.join(a.workdir, "scaldata.png"))
        fr_s = c8.color_fraction(png_s) if png_s else None
        if fr_s is None or fr_s < fm:
            print("      ⛔ the browser does not draw the page even on its own "
                  "(fraction: %s)" % ("unknown" if fr_s is None
                                      else "%.3f" % fr_s))
            if said:
                print("      ⛔ it says: %s" % said.replace("\n", " ")[:150])
            print()
            print("⚠ NOT JUDGING (outcome 3) — in this box there is no")
            print("  scene to put in the session.  ⛔ It is not a red of the")
            print("  product: it is the box (`[M]` C8, 26 Aug 2026: without")
            print("  `libpci3` Firefox produces no image).")
            sys.exit(3)
        print("      ⭐ the browser draws: the page covers %.1f%% "
              "(profile warmed up)" % (fr_s * 100))

        print("  3 · «BEFORE» attach (%.0fs) and I open the scene INSIDE the session…"
              % a.stay_before)
        stream1 = os.path.join(a.workdir, "prima.264")
        dp = os.path.join(a.workdir, "prima.log")
        pp, sp = attach(chi, a, a.stay_before, dp, video=stream1)
        # ⭐ WE WAIT FOR THE EVENT, NOT FOR THE CLOCK (§1.49): the client's diary
        #    says when it was ADMITTED.  ⛔ Opening the window before
        #    that instant would mean opening it on a desktop that, `[M]`, does not
        #    have any screen yet — and then accusing the product of not
        #    having found it again.
        # ⛔ And we wait for the LINE, not the word: with the old predicate this
        #    loop exited **at once and happy** on a TURNED AWAY client, and the
        #    scene opened on a session that did not exist.
        seen, how_much = wait_until(lambda: was_admitted(load(dp)) is True,
                                a.wait_admission, step=0.5)
        print("      the «before» client was admitted: %s"
              % (("⭐ after %.1f s" % how_much) if seen
                 else "⛔ it did not say so in %.0f s" % a.wait_admission))
        # ⚠ And then the consumer's hooking, which `[M]` costs 65÷93 ms: the
        #   default value is very wide, and it is the only blind time
        #   this mesh spends.
        time.sleep(a.latch)
        started = time.time()
        display, err = open_scene(chi, a)
        if display is None:
            print("      ⛔ I could not switch on the scene: %s" % err)
        else:
            # ⛔⛔ THE WAIT FOR THE PROFILE SITS INSIDE THE SETTLING, not on top.
            #     ⚠ Adding them would break through `--stay-before` and the photo would arrive
            #       AFTER the client had already gone away — i.e. the defect
            #       that the budget check, above, exists to
            #       prevent.
            prof, q2 = wait_until(lambda: browser_profile(chi),
                               max(1.0, a.scene_settle / 2.0))
            print("      the browser started: %s"
                  % (("⭐ its own profile after %.1f s" % q2) if prof
                     else "⚠ no profile of its own (it was already warmed up)"))
            rest = a.scene_settle - (time.time() - started)
            print("      the settling of the scene: %.0f s in all (%.0f remain)"
                  % (a.scene_settle, max(0.0, rest)))
            if rest > 0:
                time.sleep(rest)

        admitted_p, frame_p, tail_p = collect_client(
            pp, sp, dp, max(180.0, a.stay_before * 3))
        if admitted_p is False:
            # ⛔ «Not admitted» on its own is a silence: the reason is carried
            #    next to the symptom, as C1 has done since 26 Aug 2026.
            reason = "?"
            for line in reversed((tail_p or "").strip().splitlines()):
                line = line.strip()
                if line and not line.startswith("=="):
                    reason = line[:100]
                    break
            print("      ⛔ the «before» client was NOT admitted: %s" % reason)
        child_p = child_of(uid)
        png1 = image_from_stream(stream1, os.path.join(a.workdir, "prima.png"))
        fr_p = c8.color_fraction(png1) if png1 else None
        g1 = referee.judge(png1) if png1 else None
        before = observation(admitted=admitted_p, child=child_p, fraction=fr_p,
                             verdict=(g1 or {}).get("verdict"),
                             frames=frame_p)
        print("      BEFORE: admitted=%s · child=%s · frames=%s · "
              "image=«%s» · scene=%s"
              % (admitted_p, child_p, frame_p, (g1 or {}).get("verdict", "?"),
                 "unknown" if fr_p is None else "%.1f%%" % (fr_p * 100)))

        # ═══════════════════════════════════════════════════════════════════
        # 4 · THE DETACH — ⛔ the client has already finished: IT IS the gesture.
        #     ⚠ And here NOTHING is judged: «it only detaches» is the
        #       question of C7, and for it it must be GREEN (I4).
        # ═══════════════════════════════════════════════════════════════════
        print("  4 · the client went away.  ⛔ The session does NOT close: "
              "I stay detached %.0f s" % a.detached_pause)
        if a.kill_session:
            # ⛔ THE GRAFTED FAULT, and it is the real gesture: what happens
            #    when the tenant LEAVES (the same line C7 calls
            #    «closing the session»).  ⚠ The product does not have a command
            #    «close the session»: the end of a session, today, is the
            #    end of the `logind` session.
            print("      ⛔ GRAFTED FAULT: I kill the session of «%s»" % chi)
            run_loop(["loginctl", "terminate-user", chi], time_limit=60)
            time.sleep(1.0)
            run_loop(["pkill", "-KILL", "-u", chi], time_limit=60)
        time.sleep(a.detached_pause)

        # ═══════════════════════════════════════════════════════════════════
        # 5 · THE RE-ATTACH — ⭐ and here we look
        # ═══════════════════════════════════════════════════════════════════
        print("  5 · re-attach (%.0f s)…" % a.stay_after)
        stream2 = os.path.join(a.workdir, "dopo.264")
        dd = os.path.join(a.workdir, "dopo.log")
        pd, sd = attach(chi, a, a.stay_after, dd, video=stream2)
        admitted_d, frame_d, tail_d = collect_client(
            pd, sd, dd, max(180.0, a.stay_after * 3))
        if admitted_d is False:
            reason = "?"
            for line in reversed((tail_d or "").strip().splitlines()):
                line = line.strip()
                if line and not line.startswith("=="):
                    reason = line[:100]
                    break
            print("      ⛔ the re-attach was NOT admitted: %s" % reason)
        child_d = child_of(uid)
        png2 = image_from_stream(stream2, os.path.join(a.workdir, "dopo.png"))
        fr_d = c8.color_fraction(png2) if png2 else None
        g2 = referee.judge(png2) if png2 else None
        after = observation(admitted=admitted_d, child=child_d, fraction=fr_d,
                            verdict=(g2 or {}).get("verdict"),
                            frames=frame_d)
        print("      AFTER : admitted=%s · child=%s · frames=%s · "
              "image=«%s» · scene=%s"
              % (admitted_d, child_d, frame_d, (g2 or {}).get("verdict", "?"),
                 "unknown" if fr_d is None else "%.1f%%" % (fr_d * 100)))
        print()

        # ═══════════════════════════════════════════════════════════════════
        outcome, kind, reasons = judge(before, after, fm, a.maximum_gap)
        if outcome == 0:
            print("⭐ GREEN (%s)" % kind)
        elif outcome == 1:
            print("⛔⛔ RED — kind: %s" % kind)
        elif outcome == 2:
            print("⛔ BAD TERRAIN (outcome 2)")
        else:
            print("⚠ NOT JUDGING (outcome 3) — kind: %s" % kind)
        for line in reasons:
            print("   %s" % line)
        if outcome == 3:
            print("   ⛔ And this is not a green: it is an outcome of its own (§4.5).")

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ WITH THE GRAFTED FAULT THE OUTCOME IS READ BACKWARDS — it is the
        #     hook's convention (`11-gancio.sh`, `run_mesh`): a
        #     mesh with the grafted fault exits 0 when the fault WAS
        #     SEEN.  ⇒ From there the hook derives `ha_visto_il_guasto`, and it is
        #     that key that keeps C13 alive.
        # ⛔ And ONLY 0 and 1 are inverted: 2 and 3 are not judgements, and an «I did
        #    not look» turned upside down would become an invented green.
        # ═══════════════════════════════════════════════════════════════════
        if a.kill_session and outcome in (0, 1):
            print()
            bitten = fault_bitten(before, after)
            if outcome == 1 and bitten:
                print("⭐ THE GRAFTED FAULT WAS SEEN ⇒ this mesh CAN "
                      "say red")
                print("   ⭐ and the bite is measurable: the child went from "
                      "%s to %s" % (before["child"], after["child"]))
                print("   ⚠ and that is why it exits **0**: with the grafted fault the outcome "
                      "is read backwards")
                outcome = 0
            elif outcome == 1:
                print("⛔⛔ RED, but NOT because of the fault: the child "
                      "stayed THE SAME (%s)." % before["child"])
                print("    ⇒ It is the defect of the STAGE, the one C6 exists to")
                print("      find — not the injection.  ⛔ Certifying the net")
                print("      on a defect of the product is `LEZIONI.md` §1.52.")
                print("    ⚠ The red stays true and stays important: ⛔ but it does not")
                print("      prove that this mesh can say red, and the")
                print("      two facts must not be confused.")
                outcome = 1
            else:
                print("⛔⛔ THE GRAFTED FAULT WAS NOT SEEN: the session was "
                      "killed and the mesh says GREEN.")
                print("    ⇒ either the tenant found a new session without")
                print("      noticing, or this mesh does not look in the right")
                print("      place — ⛔ and in both cases it cannot")
                print("      be trusted (`LEZIONI.md` §1.44).")
                outcome = 1
    finally:
        # ⛔ Whoever opens, closes (`LEZIONI.md` §9-ter): even with the grafted fault,
        #    and even if the judgement went badly.
        for f in ("prima.264", "dopo.264"):
            try:
                os.unlink(os.path.join(a.workdir, f))
            except OSError:
                pass
        clear_out(chi)
    sys.exit(outcome)


if __name__ == "__main__":
    main()
