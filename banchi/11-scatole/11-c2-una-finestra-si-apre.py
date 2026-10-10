#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c2 — ⭐⭐ «A WINDOW OPENS»
===========================================================================

    python3 11-c2-una-finestra-si-apre.py --port 8511
    python3 11-c2-una-finestra-si-apre.py --port 8511 --dying-app
    python3 11-c2-una-finestra-si-apre.py --port 8511 --window-that-does-not-open
    python3 11-c2-una-finestra-si-apre.py --certify

It is line **C2** of `fasi/11-la-rete-di-sicurezza.md` §4.1, to the letter:

    what must be true         : a window opens
    where it starts from      : ⛔ from zero, NEW session
    what it looks at          : ⛔ **THE PIXEL** — the window must be SEEN,
                                the process is not counted
    how I know it can say red : an application that dies at once ⇒ red.
                                ⚠ And the check that the process count
                                is **not** enough: `[M]` it said 1 in both
                                cases

---------------------------------------------------------------------------
⭐⭐ WHY THIS MESH CAN BE WRITTEN NOW — *it was «blocked» until yesterday*
---------------------------------------------------------------------------

`fasi/11…` §4.1 listed it among the four **blocked** by the «sessions that
are born blind»: they look at a pixel, and there was no pixel to look at.

⭐ On 27 August 2026 the defect was **understood**, and it changes everything:

  1. `[R]` `src/mutter.c:697` — the capture session starts, ⛔ **and the
     virtual monitor does NOT exist yet**: `mutter_find_monitor()` looks for it
     *when the stream delivers*.  ⇒ ⭐ **the `wl_output` of a headless
     session is born when a consumer hooks onto the stream, never before.**
  2. ⇒ ⭐⭐ **While a client is attached, the screen is there.**  It is exactly
     the condition in which this mesh works.
  3. ⛔ But the monitor **dies with the child**, and the child dies with the client ⇒
     *«the desktop has a screen only while someone is looking at it»*.  ⚠ It is not
     C2's business (it is C6), ⭐ **but it dictates the order of the moves**: the client
     attaches **BEFORE** claiming to see anything, and stays attached
     until the end.  ⛔ A mesh that opened the application first
     would judge a desktop that does not have a screen yet, and would give red
     to the product for something the product did not do.
  4. ⚠ Inside the GNOME box a session took `[M]` **~97 s** to
     become useful, because of a defect of the **box** (`polkit` that does not
     start, `Contenitore.gnome` §6-bis).  ⛔ That is why **there are no nailed-down
     ceilings here**: they are arguments, with a prudent value, and ⇒ **they must be
     recalibrated on the real thing** (see «THE CEILINGS», further below).

---------------------------------------------------------------------------
⛔⛔ THE YARDSTICK — and where it comes from, number by number
---------------------------------------------------------------------------

⛔ **The process count is not a yardstick**, and this mesh proves it
   instead of claiming it.  `fasi/10…` §7.4, the line that opens C2:

     *«And the process count said **1** in both cases — window or
       no window, the same number.»*

⇒ ⭐ The yardstick is **the pixel**: an application is opened on a page of a
  **declared colour**, and we look at **how much of the screen has turned that
  colour**, with a **declared tolerance** (§4.3, Gemini's finding
  accepted: compositors apply colour profiles and the chain goes through an
  H.264 encoding in 4:2:0, which subsamples precisely the chroma).

And we look **BEFORE and AFTER**, not only after — three numbers, not one:

    before : the **first** frame of the grab — the bare desktop.
             ⛔ It must be «drawn» for the judge of `10-f1-testimone.py`,
             or it is not judged at all: a black desktop does not testify about a
             window, just as a black desktop does not testify about a browser
             (it is the same guard as C8, and for the same reason).
    after  : the **last** frame of the grab — the desktop with the window.
    margin : ⭐ `fraction_after - frazione_prima`.  ⛔ Without it, a window
             **left open from the previous round** would give green to an application
             that has not even started.

⚠ **And the «before» is the first frame of the grab, not the instant before
  opening the application** — this must be said, because the whole round lies
  between the two.  ⭐ And it is the reason why the verdict is **not** *«the screen
  changed»* (which changes also because of the GNOME clock) but *«the DECLARED
  COLOUR appeared»*: a quantity that does not move by itself.

---------------------------------------------------------------------------
⛔ HOW I KNOW IT CAN SAY RED — **two** grafted faults, and they are different
---------------------------------------------------------------------------

  `--dying-app`     the application starts and is killed after
                                 `--dies-after` seconds.  ⇒ no window,
                                 **and no process**.
  `--window-that-does-not-open`   ⭐⭐ THE CASE THAT COUNTS: the application starts
                                 **headless** (`--headless`), i.e. it stays
                                 **ALIVE** and paints nothing.  ⇒ the process
                                 count says **≥ 1**, exactly as
                                 in the healthy case, ⛔ **and the pixel says NO**.
                                 ⇒ It is the proof, measured by this
                                 mesh and not quoted from a document, that
                                 **counting processes is not enough**.

⛔⛔ **AND EVERY GRAFTED FAULT CARRIES ITS OWN HEALTHY CONTROL.**
`LEZIONI.md` §1.52: *the colour of the verdict is not enough — a mesh must
distinguish «the fault bit» from «it was already red on its own»*.
⇒ With the grafted fault this mesh opens **TWO** tenants:

    tenant 1  healthy  ⇒ **must be GREEN**
    tenant 2  faulted  ⇒ **must be RED**

and demands **all three** things together:

    · the healthy control is green                       (or we are not
      measuring the fault, we are measuring a red of its own — it is the
      «the FIRST one failed too» guard of C8)
    · the faulted tenant is red
    · ⭐ the fraction of the faulted tenant **drops below a SHARE** of
      that of the healthy one (`QUOTA_FAULT`, a third) — i.e. a
      MEASURABLE difference, not a change of colour of the verdict.  ⚠ A share and not
      a difference in points: §1.45, an absolute number is a number taken
      from one condition

⚠ And each fault also demands **its own signature**, or it is not that fault:

    `--dying-app`    processes after the kill = **0**
    `--window-that-does-not-open`  processes = **≥ 1** (⛔ if it were 0 we would be
                                  testing the other fault without noticing)

⛔⛔ And if the signature is missing, the outcome is **3**, not a red: a mesh that could not
   graft the fault has neither seen nor missed anything, and writing
   *«the fault was NOT seen»* would be **an accusation against a test that did not
   run**.  ⇒ It is the same cure `11-gancio.sh` gave itself on 27 August
   2026 for its own `3`.

---------------------------------------------------------------------------
⛔ THE CEILINGS — they are arguments, and they must be RECALIBRATED ON THE REAL THING
---------------------------------------------------------------------------

`LEZIONI.md` §1.45: *every wait has its own name and its own value, and the value
is justified by what is being waited for.*  ⛔ Here **no number has
been measured by whoever wrote this file**: they are prudent values,
declared, with where they come from written down.

  `--wait-stage 60`    how long to wait for the compositor to announce a
                         `wl_output`.  ⇒ `[M]` (C1's measurement, 27 August 2026,
                         **not mine**) inside the GNOME box: 98.0 · 101.0 ·
                         95.5 s, maximum 101.0.  C1 derives 152 s from it.
                         ⛔ Here it is 200 because C2 must then still **open a
                         window**, and a ceiling that expires halfway produces an
                         «I do not know» that looks like a product defect.
                         ⭐ AND THAT DELAY IS THE BOX'S, not the product's:
                         when the `polkit` cure (`Contenitore.gnome`
                         §6-bis) is in force the stage is born in ~2 s, as
                         in the other three boxes ⇒ ⛔ **then this ceiling
                         must be put back to ~20 s**, and the round costs a quarter.
                         ⚠ The mesh always PRINTS how long it really took:
                         so the ceiling is recalibrated with a number, not with
                         an opinion.
  `--wait-window 40` how long the application is given to paint.
                         ⛔ `[?]`: the first start of Firefox in a cold
                         box exceeds 25 s (`[M]` C8, 26 August 2026, where
                         the ceiling is 120 s **for the screenshot alone**), ⚠ but
                         here the tenant's profile was already born during
                         the wait for the stage.  ⇒ To be recalibrated.
  `--dies-after 1.5`     how long the application lives in the «dies at once» fault.

---------------------------------------------------------------------------
⛔ WHAT THIS MESH DOES **NOT** LOOK AT — declared, or someone will trust it
---------------------------------------------------------------------------

  · ⛔ **It does not look at whether the window is PRETTY, nor where it is, nor how
    big it is.**  It looks at a declared colour covering a declared fraction
    of the screen.  §4.3: *nobody knows what a desktop looks like*.
  · ⛔ **It does not distinguish «the application opened a window» from «something
    painted that colour»**.  It is the price of the poor yardstick, and it is intended.
  · ⚠ **It is not blind to the program**: today the default application is
    `firefox-esr`, because it is the only program in the box that can
    paint **a colour we decide** (`Contenitore.gnome` §4-ter).
    ⛔ So C2 and half B of C8 look through the **same program**:
    a Firefox defect would make both of them red, and whoever reads might
    believe in two independent confirmations.  ⇒ ⭐ `--application` and
    `--call_args` exist on purpose: the day the box has a
    minimal Wayland client that paints a declared colour (`weston-simple-shm`
    does not: its colours are its own), **C2 must be moved onto that**.
  · ⛔ **It does not look at input** (that is C4) nor at re-attach (that is C6).

---------------------------------------------------------------------------
⭐ AND TWO THINGS THIS MESH DOES DIFFERENTLY FROM C1 ON PURPOSE
---------------------------------------------------------------------------

  1. ⛔ **It does not read the PRODUCT log to know whether the screen is there.**
     It asks the **compositor**, with `wayland-info` (which is in the recipe
     on purpose, `Contenitore.gnome` §4).  ⚠ A bench that asks the product whether
     the product worked believes what it is testing.
     ⭐ And there is a second, more concrete reason: `[R]` the line *«⛔ ZERO
     MONITOR»* of `src/sessione.c:345-348` **the product writes also
     during a birth that will succeed** — because at that point the monitor has not
     appeared yet (`src/mutter.c:697`).  ⇒ Taking it as a proof of
     blindness is an error, and this mesh does not make it.
  2. ⭐ **A single round, not eight.**  C1 does eight because the fault it
     chases is intermittent; C2 chases a deterministic thing — *it is seen or
     it is not seen* — and every round costs a session birth.
     ⚠ `--rounds` is there anyway, for whoever wants to insist.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ I looked: the window IS SEEN
     (with the grafted fault: ⭐ **the fault was seen**)
  1  I looked: the window is NOT seen                           ⇒ red
     (with the grafted fault: ⛔ the fault was NOT seen, or the
      healthy control was already red on its own)
  3  ⛔ I could not look — the stage was not born, the desktop was black
     even before the application, no frame arrived, the judge
     is not there.  ⛔ And it is NOT a red
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
# ⛔ THE YARDSTICK, DECLARED HERE AND PRINTED IN EVERY OUTCOME — because «the window
#    is seen» is a verdict, and a verdict without its yardstick is an opinion.
# ═══════════════════════════════════════════════════════════════════════════

# ⭐ The colour of the target page.  ⛔ CYAN, and not C8's magenta:
#    two meshes running in the same box must be able to tell their
#    OWN window from the one left open by the other.  ⚠ It is not pedantry:
#    C8 leaves `/tmp/mozilla` and windows around, and a shared colour
#    would make a C8 window pass for «C2's window».
COLOR = (0x00, 0xFF, 0xFF)

# ⛔ The tolerance per channel.  ⚠ It is the same value as C8, and this is NOT a
#    borrowed ceiling (`LEZIONI.md` §1.45): it governs **the same
#    quantity** — the per-channel deviation of a declared colour after the
#    very same path (compositor → capture → H.264 4:2:0 → client).
#    ⭐ And `--certify` crosses it **at the edge**, one level above and one below:
#      shifted by ±48 it must still be GREEN, by ±49 RED.
#    ⛔⛔ BUT THIS IS NOT A CALIBRATION, and saying so would be §1.50.  The images
#      of the certification are synthetic and ⚠ **have never gone through the
#      4:2:0 encoding nor a colour profile**: it tests that the comparison
#      falls where it says it falls, ⛔ not that 48 is enough after the real path.
#      ⇒ It stays a `[?]`, and it is calibrated by looking at the fraction printed by the first
#        green round.
TOLERANCE = 48

# ⛔ How much of the screen must be that colour for us to say «there is a window».
# ⚠ `[?]`, and it must be recalibrated on the real thing: 0.25 is the value C8 uses for a
#   full-screen browser **photographed by itself**; here the path is another one (the same
#   window seen THROUGH the product, which is half B of C8, ⛔ never
#   measured).  ⇒ Between the GNOME bar, the borders and the decorations a full-screen
#   window never covers everything; 0.25 is prudent on the low side on purpose,
#   because a high threshold would break at the first desktop with a wider
#   bar — i.e. at phase 12, which is what this phase exists to avoid.
MINIMUM_FRACTION = 0.25

# ⭐ The MARGIN: how much the fraction must have grown between the first and the last
#   frame.  ⛔ Without it, a window **already open** (a leftover of the previous
#   round, or of another mesh) would give green to an application that has
#   not even started.  ⚠ `[?]`, prudent: 0.20 sits below `MINIMUM_FRACTION`
#   because a bit of that colour could already be there by chance.
MARGIN = 0.20

# ⭐ With the grafted fault: how much the fraction must COLLAPSE between the healthy control
#   and the faulted tenant for us to be able to say «the fault BIT».
#   ⛔ `LEZIONI.md` §1.52: we do not measure the colour of the verdict, we measure the
#      difference.
# ⚠⚠ And it is a SHARE, not a difference in points — and the reason is §1.45.
#    An absolute difference (for example «20 points») is a number taken from one
#    condition: the day a full-screen window covered 30 %
#    instead of 85 % (a wider bar, a different desktop, phase 12),
#    ⛔ the acceptance test would start saying «the fault did not bite» on a fault
#    that bit perfectly well.  ⇒ A share carries its own scale.
QUOTA_FAULT = 0.33

# ⛔ How many `wl_output` are enough.  One: the question is «is there a screen?», not
#    «how many screens are there».
MIN_OUTPUTS = 1

# `wayland-info` lists the interfaces like this:
#     interface: 'wl_output', version: 4, name: 42
# ⚠ We look for the whole line anchored to the name between quotes, not the word inside a
#   text (`CODER.md` §3.3-bis: «wl_output» also appears in «wl_output_manager»).
OUTPUT_SIGNATURE = re.compile(r"interface:\s*'wl_output'")

# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ AND THE ADMISSION SIGNATURE IS A WHOLE LINE, NOT A WORD.
#
# `[R]` `01-b3-cliente.py:1615` writes, when it goes well:  «   AMMESSO after 1023 ms»
#       and when it goes badly:  «⛔ RuntimeError: CONGEDO instead of AMMESSO: reason …»
#                                «⛔ RuntimeError: expected AMMESSO, arrived …»
#       ⛔ and it prints all three on **stdout** (`01-b3-cliente.py:2560`).
#
# ⇒ ⛔ `"ADMITTED" in body_text` is **TRUE IN ALL THREE CASES**: it would be a predicate
#   that cannot say «not admitted», i.e. `LEZIONI.md` §1.44 — and precisely in the
#   case it exists to catch.  ⚠ The branch that carries the REASON next to the
#   symptom (§1.9) would never fire, and a credentials refusal would come out
#   as *«no frame arrived from the wire»*: an accusation against the wire.
#
# ⭐⭐ AND SINCE 27 AUGUST 2026 THE RULE LIVES IN ONE PLACE ONLY: `11-c1…py`, which
#     serves it to all nine meshes.  ⚠ The family defect (C1, C5, C6, C7,
#     C9) was cured by copying **this** line; ⇒ keeping a second
#     copy here, even a right one, would be a second place to diverge from the
#     day the client changes the sentence (§1.47).
# ═══════════════════════════════════════════════════════════════════════════


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
# ⭐ THE JUDGES ARE IMPORTED, NOT REWRITTEN — `banchi/10-f1-testimone.py`
#
# ⛔ Two judges that can diverge silently are worse than one: the day
#    they diverge, the red would be given by the wrong one.  ⇒ Here **two** are
#    imported, and neither of them is written in this file:
#
#      `10-f1-testimone.py`   `judge()` — says whether an image is black,
#                             near-black, solid colour or drawn.  ⭐ It is
#                             calibrated on the real thing (25 August 2026, black desktop
#                             measured, threshold put in the middle of the gap between the
#                             two worlds).
#      `11-c8-…py`            `color_fraction()` — says how much of
#                             an image is of a given colour, within a
#                             tolerance.  ⭐ It is already certified (8 cases of 8,
#                             26 August 2026) and takes the colour and the tolerance
#                             as ARGUMENTS: so it is used with C2's numbers
#                             without inheriting C8's.
#
# ⛔ If one of the two is missing, this mesh exits **3**: we do not fall back on a
#    poorer judgement without saying so.
# ═══════════════════════════════════════════════════════════════════════════
def _load(file_name, jobs):
    """Loads a module next to me (or one level up) and demands its trades.

    ⚠ «one level up» serves the laptop: in the box everything is in
      `/opt/remotix`, but in the repository `10-f1-testimone.py` is in `banchi/` and
      this mesh in `banchi/11-scatole/`.  ⛔ Without it, `--certify` could not
      run where the phase document says it must run.
    """
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
        # ⛔ And we VERIFY that what is needed is there, instead of trusting the name
        #    of the file: `CODER.md` §3.9 — ask for the piece by name, and verify
        #    that it obeyed.
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
# ⭐⭐ C8 IS ALSO THE HOME OF THE PROVISIONING — and THREE trades come from there
#
# ⛔ No copy is made here: the `/tmp/mozilla` rule written in two
#    places is two places to diverge from, and it is precisely the error that on
#    27 August 2026 cost a whole round.  ⇒ It is imported.
#
#   · `apply_fix(chi)`          — the lines of `src/provisiona.sh`: a
#        REAL `~/.cache` for the tenant we create.  ⭐ It is this that makes
#        the mesh immune, not a cleanup.
#   · `can_write_cache(chi)`  — E1: the cure is not declared, we TRY to
#        write into `~/.cache/mozilla`.
#   · `clear_out_slot_shared(b)` — removes `/tmp/mozilla` ⛔ only if it
#        belongs to a tenant of base `b`, i.e. MINE.
# ═══════════════════════════════════════════════════════════════════════════
_JOBS_C8 = ("apply_fix", "can_write_cache",
                "clear_out_slot_shared")
_C8 = None


def c8_home():
    """⭐ C8's module, or `None`.  ⛔ We do not exit here: the caller decides."""
    global _C8
    if _C8 is None:
        _C8, _ = _load("11-c8-il-secondo-apre-il-browser.py", _JOBS_C8)
    return _C8


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
    """⭐⭐ THE CARD'S GROUPS — `(outcome, reason_text)`; `0` = it can be measured.

    ⛔ Until 27 August 2026 this mesh created the tenant with
       `usermod -aG video,render` **and did not read back**: two nailed-down names (which
       belong to ONE distribution) and no verification — E1, «written is not in
       force».  ⭐ The work is done by `attrezzi-gruppi-scheda.sh`, which reads the gids
       from the NODES and reads back comparing the numbers.  ⛔ No copy of it is made here.
    """
    return c1_home().ensure_groups(chi, prefix)


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE JUDGEMENT — and it lives in a PURE function, so `--certify` can
#    run it on fake images without switching anything on.
# ═══════════════════════════════════════════════════════════════════════════
def judge_round(first, last, judge, fraction, processes,
                    minimum_fraction=MINIMUM_FRACTION, headroom=MARGIN):
    """Given the FIRST and the LAST frame of the grab, says whether the window is seen.

    `judge`  = `10-f1-testimone.py:judge`  (black / near-black / drawn)
    `fraction` = a function (path) -> fraction of the colour, or `None`
    `processes` = how many processes of the application were alive.  ⛔⛔ **It does NOT enter
                 the verdict**: it is only reported.  It is precisely the
                 quantity that `fasi/10…` §7.4 measured equal (1) in the two
                 opposite cases, ⇒ letting it decide here would mean repeating
                 the error this mesh exists not to repeat.

    Returns a dictionary with `state` among:
        "vista"     ⭐ the window is seen             ⇒ green
        "non-vista"    the window is NOT seen        ⇒ red
        "non-lo-so" ⛔ I could not look               ⇒ neither green nor red
    """
    outcome = {"state": "non-lo-so", "reason_text": "", "frazione_prima": None,
             "fraction_after": None, "desktop_prima": None, "processes": processes}

    g = judge(first) if first else None
    if g is None:
        outcome["reason_text"] = ("the FIRST frame could not be looked at "
                           "(it is not there, it is empty, or it is not an image)")
        return outcome
    outcome["desktop_prima"] = g["verdict"]
    # ⛔ The guard that is worth more than all the others, and it is the same as C8: **a black
    #    desktop does not testify about a window.**  Calling «C2's red» a
    #    screen that was black even before the application existed would
    #    mean blaming the application for something that happened before it.
    if g["verdict"] in ("nero", "quasi-nero"):
        outcome["reason_text"] = ("the desktop was «%s» BEFORE the application: the "
                           "session had nothing to show, and this is not "
                           "a judgement on C2" % g["verdict"])
        return outcome

    fp = fraction(first)
    fd = fraction(last) if last else None
    outcome["frazione_prima"], outcome["fraction_after"] = fp, fd
    if fp is None or fd is None:
        outcome["reason_text"] = ("I could not read %s frame"
                           % ("the FIRST" if fp is None else "the LAST"))
        return outcome

    if fd < minimum_fraction:
        outcome["state"] = "non-vista"
        outcome["reason_text"] = ("the declared colour covers %.1f%% of the screen, "
                           "below the %.0f%% demanded" % (fd * 100, minimum_fraction * 100))
        return outcome
    if fd - fp < headroom:
        # ⭐ The case the margin exists to catch: the colour was ALREADY there.
        outcome["state"] = "non-vista"
        outcome["reason_text"] = ("the colour covers %.1f%%, ⛔ but it already covered "
                           "%.1f%% BEFORE: grown by %.1f points, below the %.0f "
                           "demanded ⇒ this window was not opened by my "
                           "application" % (fd * 100, fp * 100, (fd - fp) * 100,
                                            headroom * 100))
        return outcome
    outcome["state"] = "vista"
    outcome["reason_text"] = ("the declared colour covers %.1f%% of the screen "
                       "(it covered %.1f%% before: +%.1f points)"
                       % (fd * 100, fp * 100, (fd - fp) * 100))
    return outcome


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CERTIFICATION — it proves that the judge can give GREEN, RED and
#    «I DO NOT KNOW», and that the thresholds are crossed in BOTH directions.
# ═══════════════════════════════════════════════════════════════════════════
def certify():
    """⚠ And it declares what it covers and what it does not.

    It COVERS three things, and the third is the one that gets forgotten:
      1. **the judge** — the colour found when it is there and not when it is not;
         a window already open that does not pass for a new one; a black desktop
         BEFORE that gives «I do not know» and not red; ⭐ and the three thresholds crossed
         **at the edge**, one level above and one below;
      2. ⭐ that **the process count decides nothing** — in both directions:
         equal counts with opposite verdicts, and very different counts with the same
         verdict;
      3. ⭐⭐⭐ **the JOINT**: the exit code with the grafted fault, which is
         **inverted** and from which C13 derives whether the net can still say red.
         ⛔ It is the piece `LEZIONI.md` §1.52 was born for, and which neither of the
         two certifications of the time covered.
    ⛔ It DOES NOT COVER, and it must be said because it is the half that matters:
      · that the application really starts inside the session, nor that the stage
        is born — that is said by the grafted faults **on the real thing**;
      · ⚠⚠ **that `TOLERANCE = 48` is the right number AFTER THE REAL PATH.**
        Here the images are synthetic and have never gone through either the
        H.264 encoding in 4:2:0 or a colour profile.  ⇒ This
        certification proves that the comparison **falls where it says it falls**, not
        that 48 is enough.  ⛔ That is calibrated on the real thing, and until it is done the
        tolerance stays a `[?]`.
    """
    try:
        import numpy as np
        from PIL import Image
    except ImportError:
        print("⛔ numpy or Pillow is missing: I cannot even certify myself")
        print("   ⇒ I could not look")
        return 3
    import tempfile

    assessor, dove_g = desktop_judge()
    reader, dove_l = color_reader()
    if assessor is None:
        print("⛔ I cannot find (or it does not hold up) the image judge "
              "10-f1-testimone.py%s" % (" in %s" % dove_g if dove_g else ""))
        print("   ⇒ I could not look")
        return 3
    if reader is None:
        print("⛔ I cannot find (or it does not hold up) C8's colour reader%s"
              % (" in %s" % dove_l if dove_l else ""))
        print("   ⇒ I could not look")
        return 3

    def fraction(p):
        return reader.color_fraction(p, COLOR, TOLERANCE)

    lav = tempfile.mkdtemp(prefix="c2cert-")

    def paint_lines(label_name, background, win, line_list, drawing_v=True):
        """⭐ The window is painted by EXACT ROWS, not by share.

        ⛔ It serves to cross the thresholds **at the edge**: with a round share one
           tests only the direction of the comparison, not the point where it falls — and a
           number that can be changed by twenty points without the
           certification noticing is not calibrated, it is only written
           (`LEZIONI.md` §1.50).
        """
        a = np.zeros((216, 384, 3), dtype="uint8")
        a[:, :] = background
        if drawing_v:
            a[::7, ::5] = (210, 214, 220)
            a[0:12, :] = (30, 32, 36)
        if line_list > 0:
            a[216 - line_list:, :] = win
        p = os.path.join(lav, label_name + ".png")
        Image.fromarray(a).save(p)
        return p

    def paint(label_name, background, win=None, quota=1.0, drawing_v=True):
        """A fake desktop: a background, a bit of stuff on top, and maybe a window.

        ⚠ `drawing_v=True` puts ordered noise over the background — it is needed
          because the 10-f1 judge declares «solid colour» a screen of a
          single colour, and a real desktop never is.
        """
        a = np.zeros((216, 384, 3), dtype="uint8")
        a[:, :] = background
        if drawing_v:
            a[::7, ::5] = (210, 214, 220)
            a[0:12, :] = (30, 32, 36)          # the bar at the top
        if win is not None and quota > 0:
            line_list = max(1, int(216 * quota))
            a[216 - line_list:, :] = win
        p = os.path.join(lav, label_name + ".png")
        Image.fromarray(a).save(p)
        return p

    BACKGROUND = (58, 62, 70)
    bare = paint("bare", BACKGROUND)
    nero = paint("nero", (0, 0, 0), drawing_v=False)
    # ⭐ «near-black»: black with the GNOME bar on — it is the real case
    #   measured by 10-f1 on 25 August 2026, not an invention: `[M]` desktop with
    #   background `#000000`, the top bar carries the clock and the icons ⇒ lit
    #   **0.00121** (just above the black threshold) and mean **0.28** (below the
    #   near-black threshold).  ⛔ The few lit pixels below are calibrated to
    #   reproduce those two numbers, not put in by eye: with too much stuff lit
    #   the image becomes «drawn» and the case would no longer prove anything.
    almost_black = paint("almost_black", (0, 0, 0), drawing_v=False)
    _q = np.asarray(Image.open(almost_black).convert("RGB")).copy()
    _q[0:5, ::20] = (200, 200, 200)
    Image.fromarray(_q).save(almost_black)

    moved = tuple(min(255, max(0, c + s))
                     for c, s in zip(COLOR, (+30, -30, -30)))
    too = tuple(min(255, max(0, c + s))
                   for c, s in zip(COLOR, (+120, -120, -120)))

    # (name, first, last, processes, expected state)
    cases = [
        ("the window opens",
         bare, paint("full", BACKGROUND, COLOR, 0.85), 1, "vista"),
        ("no window: the screen is the one from before",
         bare, paint("eq_sign", BACKGROUND), 0, "non-vista"),
        # ⭐⭐ THE CASE WORTH MORE THAN ALL OTHERS, and it is the line of §4.1:
        #    same process count, opposite verdicts.
        ("⭐ process ALIVE and no window (the case of fasi/10 §7.4)",
         bare, paint("viva-cieca", BACKGROUND), 1, "non-vista"),
        ("⭐ colour SHIFTED by %s: must be GREEN" % (moved,),
         bare, paint("spostata", BACKGROUND, moved, 0.85), 1, "vista"),
        ("colour shifted TOO MUCH %s: must be RED" % (too,),
         bare, paint("too", BACKGROUND, too, 0.85), 1, "non-vista"),
        ("a small spot is not a window",
         bare, paint("blot", BACKGROUND, COLOR, 0.05), 1, "non-vista"),
        # ⛔ The MARGIN case: the window was already there before.
        ("⛔ the window was ALREADY there before (leftover of another round)",
         paint("gia-aperta", BACKGROUND, COLOR, 0.85),
         paint("ancora-aperta", BACKGROUND, COLOR, 0.87), 1, "non-vista"),
        # ⛔ And the two «I do not know», which are NOT reds.
        ("⛔ the desktop was BLACK before ⇒ I do not know",
         nero, paint("dopo-nero", BACKGROUND, COLOR, 0.85), 1, "non-lo-so"),
        ("⛔ the desktop was NEAR-BLACK before ⇒ I do not know",
         almost_black, paint("dopo-qn", BACKGROUND, COLOR, 0.85), 1, "non-lo-so"),
        ("⛔ the first frame is not there ⇒ I do not know",
         os.path.join(lav, "manca.png"),
         paint("dopo-manca", BACKGROUND, COLOR, 0.85), 1, "non-lo-so"),
    ]
    # an empty file: «I did not look», not «it was black»
    blank = os.path.join(lav, "vuoto.png")
    open(blank, "wb").close()
    cases.append(("⛔ the first frame is empty ⇒ I do not know",
                 blank, paint("dopo-vuoto", BACKGROUND, COLOR, 0.85), 1, "non-lo-so"))
    cases.append(("⛔ the last frame is not there ⇒ I do not know",
                 bare, os.path.join(lav, "manca2.png"), 1, "non-lo-so"))

    print("== certification of C2's judge ==")
    print("   desktop judge : %s" % dove_g)
    print("   colour reader : %s" % dove_l)
    print("   colour %s · tolerance ±%d per channel · at least %.0f%% of the "
          "screen · margin %.0f points"
          % (COLOR, TOLERANCE, MINIMUM_FRACTION * 100, MARGIN * 100))
    print()
    troubles = 0
    for label_name, first, last, proc, expected_val in cases:
        e = judge_round(first, last, assessor.judge, fraction, proc)
        ok = e["state"] == expected_val
        troubles += 0 if ok else 1
        print("  %s  %-56s  processes=%s  ⇒ %-10s (expected %s)"
              % ("OK " if ok else "NO ", label_name, proc, e["state"], expected_val))
        if not ok:
            print("        ⛔ it said: %s" % e["reason_text"])

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ AND THE EXPLICIT PROOF, with a number instead of a sentence:
    #    **two rounds with THE SAME process count and OPPOSITE verdicts.**
    # ⛔ Without this, «the process count is not enough» would remain a quotation
    #    from a document; with this it is a fact the mesh produces by itself.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    a = judge_round(bare, paint("dim-si", BACKGROUND, COLOR, 0.85),
                        assessor.judge, fraction, 1)
    b = judge_round(bare, paint("dim-no", BACKGROUND),
                        assessor.judge, fraction, 1)
    proven = (a["state"] == "vista" and b["state"] == "non-vista"
                  and a["processes"] == b["processes"] == 1)
    troubles += 0 if proven else 1
    print("  %s  ⭐ THE PROCESS COUNT IS NOT ENOUGH: processes 1 and 1, "
          "verdicts «%s» and «%s»"
          % ("OK " if proven else "NO ", a["state"], b["state"]))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ AND THE COMPOSITOR READING: `wayland-info` says or does not say that there is
    #   a screen.  ⛔ An «I do not know» and a «zero screens» are not the same
    #   thing (`LEZIONI.md` §1.47), and here it is certified that they do not look alike.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    readings = [
        ("two screens announced",
         "interface: 'wl_compositor', version: 6, name: 1\n"
         "interface: 'wl_output', version: 4, name: 42\n"
         "interface: 'wl_output', version: 4, name: 43\n", 2),
        ("one screen announced",
         "interface: 'wl_output', version: 4, name: 42\n", 1),
        ("⛔ no screen: the compositor is there and has no outputs",
         "interface: 'wl_compositor', version: 6, name: 1\n"
         "interface: 'wl_seat', version: 9, name: 5\n", 0),
        ("⚠ a name that CONTAINS wl_output is not wl_output",
         "interface: 'zwlr_wl_output_manager_v1', version: 1, name: 7\n", 0),
    ]
    for label_name, body_text, expected_val in readings:
        n = how_many_screens(body_text)
        ok = n == expected_val
        troubles += 0 if ok else 1
        print("  %s  %-56s  screens=%s (expected %s)"
              % ("OK " if ok else "NO ", label_name, n, expected_val))
    n = how_many_screens(None)
    ok = n is None
    troubles += 0 if ok else 1
    print("  %s  %-56s  screens=%s (expected «I do not know»)"
          % ("OK " if ok else "NO ", "⛔ wayland-info did not speak ⇒ I do not know",
             "unknown" if n is None else n))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ «WAS THE CLIENT ADMITTED?» — and the word inside a text is NOT enough.
    #
    # ⛔ `[R]` `01-b3-cliente.py` writes «AMMESSO» in all three cases: when
    #    it was admitted, when it received a FAREWELL in place of the ADMITTED,
    #    and when it was waiting for one and another arrived.  ⇒ `"ADMITTED" in
    #    body_text` would be **true also on the two refusals**, i.e. a predicate that
    #    cannot say no (`LEZIONI.md` §1.44) — precisely in the cases the
    #    check exists to catch.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    admissions = [
        ("the real line of the admitted client",
         "   ← HERE_I_AM\n   ADMITTED after 1023 ms (fixed delay §4.4-bis)\n", True),
        ("⛔ FAREWELL instead of ADMITTED — the word is there and the sense is opposite",
         "   ⛔ RuntimeError: FAREWELL instead of ADMITTED: reason 0x03\n", False),
        ("⛔ «expected ADMITTED, arrived …» — likewise",
         "   ⛔ RuntimeError: expected ADMITTED, arrived FAREWELL\n", False),
        ("⚠ a line that NAMES the admission without being it",
         "   [reg] waiting for ADMITTED\n", False),
        ("the client did not start at all",
         "Traceback (most recent call last):\n  ImportError: aioquic\n", False),
    ]
    for label_name, body_text, expected_val in admissions:
        got = was_admitted(body_text)
        ok = got is expected_val
        troubles += 0 if ok else 1
        print("  %s  %-56s  ⇒ %s (expected %s)"
              % ("OK " if ok else "NO ", label_name, got, expected_val))
    got = was_admitted("")
    ok = got is None
    troubles += 0 if ok else 1
    print("  %s  %-56s  ⇒ %s (expected «I do not know»)"
          % ("OK " if ok else "NO ", "⛔ the client said NOTHING",
             "unknown" if got is None else got))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE THREE THRESHOLDS, CROSSED **AT THE EDGE** — and not from afar.
    #
    # ⛔ Before, there were only distant cases here: colour shifted by 30 against 120,
    #    fraction 0.85 against 0.05, margin 0.85 against 0.02.  ⚠ With those one
    #    could set `TOLERANCE` to any value between 31 and 119 and the
    #    certification stayed green: it crossed **the direction** of the
    #    comparison, not **the threshold**.  And since the three numbers are declared
    #    `[?]` to be recalibrated, it is exactly the place where the trap bites.
    # ⇒ ⭐ Now every threshold is tested at **one level above and one below**: if
    #   someone changes it by a single step, a case turns red.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    edge = []
    to_limit = (min(255, COLOR[0] + TOLERANCE), COLOR[1], COLOR[2])
    beyond = (min(255, COLOR[0] + TOLERANCE + 1), COLOR[1], COLOR[2])
    edge.append(("⭐ colour shifted by EXACTLY ±%d ⇒ still GREEN" % TOLERANCE,
                  bare, paint("bordo-t1", BACKGROUND, to_limit, 0.85), "vista"))
    edge.append(("colour shifted by ±%d ⇒ RED" % (TOLERANCE + 1),
                  bare, paint("bordo-t2", BACKGROUND, beyond, 0.85), "non-vista"))
    # the fraction: 55/216 = 0.2546 (above 0.25) · 53/216 = 0.2454 (below)
    edge.append(("⭐ the window covers 25.5%% ⇒ GREEN (threshold %.0f%%)"
                  % (MINIMUM_FRACTION * 100),
                  bare, paint_lines("bordo-f1", BACKGROUND, COLOR, 55), "vista"))
    edge.append(("the window covers 24.5% ⇒ RED",
                  bare, paint_lines("bordo-f2", BACKGROUND, COLOR, 53), "non-vista"))
    # the margin: before 65/216 = 0.3009 · after 111 ⇒ +0.2130 · after 106 ⇒ +0.1898
    already_open = paint_lines("bordo-m0", BACKGROUND, COLOR, 65)
    edge.append(("⭐ the colour grows by 21.3 points ⇒ GREEN (margin %.0f)"
                  % (MARGIN * 100),
                  already_open, paint_lines("bordo-m1", BACKGROUND, COLOR, 111), "vista"))
    edge.append(("the colour grows by 19.0 points ⇒ RED",
                  already_open, paint_lines("bordo-m2", BACKGROUND, COLOR, 106),
                  "non-vista"))
    for label_name, first, last, expected_val in edge:
        e = judge_round(first, last, assessor.judge, fraction, 1)
        ok = e["state"] == expected_val
        troubles += 0 if ok else 1
        print("  %s  %-56s  ⇒ %-10s (expected %s)"
              % ("OK " if ok else "NO ", label_name, e["state"], expected_val))
        if not ok:
            print("        ⛔ it said: %s" % e["reason_text"])

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ AND THAT THE PROCESS COUNT DOES NOT ENTER THE VERDICT — tested, not said.
    # ⛔ Above it is shown that two equal counts give opposite verdicts; here the
    #    reverse, which is the half that was missing: **very different counts on the
    #    same images give the same verdict**.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    full = paint("proc-si", BACKGROUND, COLOR, 0.85)
    empty = paint("proc-no", BACKGROUND)
    for label_name, last, expected_val in (("with the window", full, "vista"),
                                 ("without the window", empty, "non-vista")):
        seen_items = set()
        for proc in (0, 1, 7, None):
            seen_items.add(judge_round(bare, last, assessor.judge,
                                      fraction, proc)["state"])
        ok = seen_items == {expected_val}
        troubles += 0 if ok else 1
        print("  %s  ⭐ processes 0/1/7/«unknown» %-30s ⇒ always «%s»"
              % ("OK " if ok else "NO ", label_name, ", ".join(sorted(seen_items))))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ THE JOINT — the exit code with the grafted fault, in both directions.
    #
    # ⛔ It is the piece `LEZIONI.md` §1.52 was born for: C9's certification
    #    tested the judge, C13's the reading of the log, ⛔ and the
    #    defect was **in between**, in the exit code, which belongs to neither
    #    of the two trades.  ⇒ Here the exit code is tested.
    # ═══════════════════════════════════════════════════════════════════════
    print()

    def lap(state, fraction_after, processes, killed=None, reason_text="(fake)"):
        return {"state": state, "fraction_after": fraction_after,
                "processes": processes, "killed": killed, "reason_text": reason_text}

    joints = [
        ("blind: healthy green + fault red + process alive ⇒ 0 (seen)",
         "blind", lap("vista", 0.85, 3), lap("non-vista", 0.00, 2), 0),
        ("dies: healthy green + fault red + processes 0 ⇒ 0 (seen)",
         "dies", lap("vista", 0.85, 3), lap("non-vista", 0.00, 0, True), 0),
        ("⛔ the fault does NOT bite: the window is seen anyway ⇒ 1",
         "blind", lap("vista", 0.85, 3), lap("vista", 0.84, 2), 1),
        ("⛔ it bites too little: 0.85 ⇒ 0.40, above the share ⇒ 1",
         "blind", lap("vista", 0.85, 3), lap("non-vista", 0.40, 2), 1),
        # ⭐⭐ THE CASE WORTH MORE THAN ALL OTHERS, and it is a correction:
        ("⭐ the HEALTHY CONTROL is red ⇒ 3, ⛔ NOT 1 (the net is not accused)",
         "blind", lap("non-vista", 0.01, 3), lap("non-vista", 0.00, 2), 3),
        ("the healthy one could not look ⇒ 3",
         "blind", lap("non-lo-so", None, None), lap("non-vista", 0.0, 2), 3),
        ("the faulted one could not look ⇒ 3",
         "blind", lap("vista", 0.85, 3), lap("non-lo-so", None, None), 3),
        ("⚠ signature missing: «dies» and the process is still alive ⇒ 3",
         "dies", lap("vista", 0.85, 3), lap("non-vista", 0.0, 2), 3),
        ("⚠ signature missing: «blind» and there is no process ⇒ 3",
         "blind", lap("vista", 0.85, 3), lap("non-vista", 0.0, 0), 3),
        ("⚠ signature missing: `pkill` found nothing ⇒ 3",
         "dies", lap("vista", 0.85, 3), lap("non-vista", 0.0, 0, False), 3),
    ]
    for label_name, which, healthy, broken, expected_val in joints:
        e, _lines = test_fault(which, healthy, broken)
        ok = e == expected_val
        troubles += 0 if ok else 1
        print("  %s  %-62s  ⇒ outcome %s (expected %s)"
              % ("OK " if ok else "NO ", label_name, e, expected_val))

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
    group_troubles, _how_many_groups = c1_home().certify_groups("C2")
    troubles += group_troubles

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ THE SHARED PROVISIONING — ⛔ the case that on 27 August 2026 was missing,
    #    and it cost a whole round read backwards.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    troubles_pr, how_many_pr = certify_provisioning("C2", "c2u")
    troubles += troubles_pr

    print()
    if troubles:
        print("⛔ C2's judge is NOT reliable: %d cases wrong" % troubles)
        return 1
    print("⭐ the judge sees the window when it is there and not when it is not, the "
          "three thresholds fall where they say,")
    print("   ⭐ the process count does not enter the verdict in either "
          "direction, «ADMITTED» is a line and not a word,")
    print("   ⭐⭐ and the JOINT — the exit code with the grafted fault — says 0, "
          "1 and 3 where it must (LEZIONI.md §1.52)")
    print("   ⭐ and the CARD'S GROUPS: a tenant that cannot see makes it say "
          "«I could not look», ⛔ never red")
    # ⛔ And the provisioning line is printed ONLY if the real cases ran:
    #    saying «covered» after skipping them would be §1.50 in one line.
    if how_many_pr >= 4:
        print("   ⭐⭐ and THE PROVISIONING: a /tmp/mozilla of another mesh I do not "
              "touch, and my tenant writes anyway — ⛔ never red")
    else:
        print("   ⚠ and THE PROVISIONING is covered ONLY halfway: the real cases "
              "need the administrator, and here I did not run them")
    print("⚠ and this certification covers THE JUDGES AND THE JOINT, ⛔ not "
          "the real opening of the window nor that ±%d is enough after the encoding "
          "(see the top)" % TOLERANCE)
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# THE TERRAIN AND THE MOVES
# ═══════════════════════════════════════════════════════════════════════════
def sh(command, seconds=120):
    try:
        return subprocess.run(["/bin/sh", "-c", command],
                              capture_output=True, text=True, timeout=seconds)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(command, 124, "", "expired")


def how_many_screens(body_text):
    """How many `wl_output` the compositor announces.  ⛔ `None` = I do not know.

    ⚠ `None` and `0` are two different things and must not look alike: *«I could
      not ask»* and *«I asked and there is none»* lead to two
      opposite outcomes (3 against a wait that goes on).  `LEZIONI.md` §1.47.
    """
    if body_text is None:
        return None
    return len(OUTPUT_SIGNATURE.findall(body_text))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ THE SHARED PROVISIONING — `/tmp/mozilla`, and why the cure lives HERE
#
# `[M]` 27 August 2026, round `--famiglia tutto` on all four boxes,
#   binary `aa950804fed7`: C2 ⛔ 1 («the colour covers 0.0% of the screen»),
#   C3 ⛔ 3, C4 ⛔ 3.  ⚠ And the judged image said something else entirely: the GNOME
#   session was **alive and painted** — panel, dock, background, Firefox on — ⛔ but
#   Firefox was stuck on the **profile chooser window**.
#
# ⇒ THE CAUSE, read inside the box:
#     /home/c2u1/.cache/mozilla -> /tmp/mozilla   (the skeleton of the real
#                                                  machine, which C8 reproduces and
#                                                  ⛔ does NOT undo)
#     /tmp/mozilla        of «c8u1», mode 0700
#   i.e. the shared place had stayed with the FIRST tenant that took it —
#   the one of C8/C8b, which in `famiglia tutto` runs BEFORE me.  ⛔ Neither of the
#   two benches is wrong on its own: it is the ORDER that breaks them.
#
# ⛔⛔ AND THE CURE CANNOT LIVE IN WHOEVER SWITCHES ME ON.  For a day it was in
#     `11-accendi.sh`; ⚠ but a mesh that needs to be «prepared from
#     outside» is, when launched by hand or by another hook, a mesh that gives a
#     **false red** — and it is the defect that costs the most in this net.
#
# ⭐⭐ AND IT IS NOT A CLEANUP.  `src/provisiona.sh` already stated the rule —
#     *«do not touch the `/tmp/mozilla` of whoever already has it: it is not ours and
#     we do not know who uses it»* — and ⛔ it holds also between meshes: in parallel (C14) the other
#     mesh is INSIDE it, and deleting it would make it fall.  ⇒ The cure is
#     the same as the product's: **a real `~/.cache` for the tenant I create**.
#     With that, I no longer care whose `/tmp/mozilla` is: I do not look at it.
#
# ⚠ Only one legitimate cleanup remains, and it concerns only ME: the `/tmp/mozilla`
#   that one of MY tenants of a previous round left there.  ⛔ That one is
#   removed by C8's `clear_out_slot_shared()`, imported, and ⛔ it touches
#   nothing else.
#
# ⛔ And if the cure does not hold we do NOT give red: we exit **3** saying why
#   (`create` returns `(False, reason_text)`), because a browser stuck on the profile
#   chooser is a defect of the BENCH and not of the product.
# ═══════════════════════════════════════════════════════════════════════════
SHARED_DIR = "/tmp/mozilla"


def shared_slot_owner():
    """Whose `/tmp/mozilla` is — `""` if it is not there.  It serves only to SAY it."""
    return sh("stat -c %%U %s 2>/dev/null" % SHARED_DIR).stdout.strip()


def clear_out_my_leftover(my_base):
    """Removes `/tmp/mozilla` ⛔ only if it was left to one of MY tenants.

    ⛔ The rule is not rewritten: it is C8's `clear_out_slot_shared()`,
       imported — *«only what belongs to a tenant of THIS
       test is removed»*.  ⇒ If it belongs to another mesh, or to a stranger, that function
       says «I do NOT touch it» and touches nothing, which is what I want.
    ⚠ Returns a line to print, or `None` if there is nothing to say.
    """
    c8 = c8_home()
    if c8 is None:
        return "⚠ I cannot find C8: I did not even look at %s" % SHARED_DIR
    return c8.clear_out_slot_shared(my_base)


def provisioning_fix(chi):
    """⭐⭐ (done, why) — the cure of `src/provisiona.sh`, and its PROOF.

    ⛔ E1: applying it is not enough, we really try to write into
       `~/.cache/mozilla` — which with the link to `/tmp` is the place that bites.
       ⚠ Writing into `~/.cache` would prove nothing: with the link it is
       `/tmp`, which is writable by anyone (mode 1777).
    """
    c8 = c8_home()
    if c8 is None:
        return False, ("I cannot find `11-c8-il-secondo-apre-il-browser.py` next "
                       "to me: the cure of `src/provisiona.sh` comes from there, and "
                       "⛔ no copy of it is made here (§1.47)")
    c8.apply_fix(chi)
    if c8.can_write_cache(chi):
        return True, ""
    owner = shared_slot_owner()
    return False, ("«%s» cannot write into ~/.cache/mozilla (%s belongs to "
                   "«%s»): Firefox would stay on the profile chooser and this "
                   "mesh would measure the BENCH, not the product"
                   % (chi, SHARED_DIR, owner or "nobody"))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE CERTIFICATION OF THE PROVISIONING — and it lives in ONE PLACE ONLY (§1.47)
#
# ⚠ It lives here, in C2, and not in C8, because C8 is not mine to modify today.  ⭐ The
#   day it is, this function goes with `apply_fix`, which is the
#   piece it certifies.  C3 and C4 call it from here, ⛔ they do not make a
#   copy of it — three copies are three places to diverge from, and it is exactly
#   the error this cure was born to repair.
#
# ⛔⛔ AND IT INSPECTS NOTHING (E1): it makes a `/tmp/mozilla` of another tenant,
#     with a real tenant and the real skeleton, and then LOOKS at what happens.
# ═══════════════════════════════════════════════════════════════════════════
def certify_provisioning(mesh_name, own_base):
    """⭐ Returns `(troubles, quanti_casi_provati)`.

    The cases, and there are three:
      1. ⛔ the cure CANNOT succeed ⇒ `(False, reason_text')`, i.e. the mesh
         stops saying why (outcome **3**) — ⛔ and NEVER a red;
      2. ⛔ `/tmp/mozilla` belongs to a tenant of ANOTHER mesh ⇒ I do not touch it,
         ⭐ and my tenant writes anyway into `~/.cache/mozilla`;
      3. ⭐ `/tmp/mozilla` belongs to one of MY tenants, left from the previous round ⇒ I
         clear it.
    ⚠ 2 and 3 need the administrator.  ⛔ Without it, we SAY that they were not
      tested: a certification that keeps quiet about the half that matters is worse than
      one that is missing.
    """
    troubles = 0
    how_many = 0
    print("  ── the shared provisioning of %s (%s) ──"
          % (mesh_name, SHARED_DIR))
    if c8_home() is None:
        print("  NO   ⛔ I cannot find C8: the cure of src/provisiona.sh cannot be "
              "imported, and ⛔ no copy of it is made")
        return 1, 1

    # ── 1 · and no permission is needed ────────────────────────────────────
    how_many += 1
    finished, reason_text = provisioning_fix("non-esiste-%s-x" % own_base)
    ok = (finished is False) and bool(reason_text)
    troubles += 0 if ok else 1
    print("  %s  ⛔ the cure cannot succeed ⇒ it stops SAYING WHY "
          "(outcome 3), ⛔ never a red" % ("OK " if ok else "NO "))
    if not ok:
        print("        ⛔ it said: (%s, %r)" % (finished, reason_text))

    # ── 2 and 3 · the REAL cases ───────────────────────────────────────────
    if os.geteuid() != 0:
        print("  ⚠   the two REAL cases need the administrator: ⛔ I did NOT "
              "test them, and so this certification does not cover the cure")
        return troubles, how_many
    if os.path.exists(SHARED_DIR):
        print("  ⚠   %s is already there and belongs to «%s»: ⛔ I do not touch it to run a "
              "test on it — the two REAL cases I did NOT test"
              % (SHARED_DIR, shared_slot_owner()))
        return troubles, how_many

    foreign = "c99u9"          # a tenant of the net, ⛔ but of another mesh
    my = "%s9" % own_base

    def real_machine_skeleton(chi):
        """`~/.cache` as a link to `/tmp`, ⛔ only on this tenant.

        ⚠ `/etc/skel` is not touched: here the terrain is reproduced by hand, on two
          users that are born and die inside this function.
        """
        sh("rm -rf /home/%s/.cache && ln -s /tmp /home/%s/.cache && "
           "chown -h %s:%s /home/%s/.cache" % (chi, chi, chi, chi, chi))

    def slot_belongs_to(chi):
        sh("rm -rf %s && mkdir -p %s/firefox && chown -R %s:%s %s && "
           "chmod 700 %s"
           % (SHARED_DIR, SHARED_DIR, chi, chi,
              SHARED_DIR, SHARED_DIR))

    def via(chi):
        # ⛔ The link is removed BEFORE `userdel -r`: it is a pointer to
        #    `/tmp`, and it is given no chance to follow it.
        sh("rm -f /home/%s/.cache; userdel -r %s 2>/dev/null; rm -rf /home/%s"
           % (chi, chi, chi))

    try:
        via(foreign)
        via(my)
        for chi in (foreign, my):
            r = sh("useradd -m -s /bin/bash %s" % chi)
            if r.returncode != 0:
                print("  ⚠   I could not create «%s»: %s ⇒ ⛔ the two "
                      "REAL cases I did NOT test"
                      % (chi, (r.stderr or "").strip()[:80]))
                return troubles, how_many
            real_machine_skeleton(chi)

        # ── 2 · the place belongs to ANOTHER mesh ──────────────────────────
        slot_belongs_to(foreign)
        said = clear_out_my_leftover(own_base)
        how_many += 1
        ok = shared_slot_owner() == foreign
        troubles += 0 if ok else 1
        print("  %s  ⛔ %s belongs to «%s» (another mesh) ⇒ I do NOT touch it"
              % ("OK " if ok else "NO ", SHARED_DIR, foreign))
        if said:
            print("        says: %s" % said)

        # ⭐ …and the cure makes me immune ANYWAY: this is the case that
        #   proves that the red of 27 August would not come back.
        how_many += 1
        finished, reason_text = provisioning_fix(my)
        still = shared_slot_owner() == foreign
        ok = bool(finished) and still
        troubles += 0 if ok else 1
        print("  %s  ⭐ and «%s» writes anyway into ~/.cache/mozilla, with %s "
              "still belonging to «%s»" % ("OK " if ok else "NO ", my,
                                           SHARED_DIR, foreign))
        if not ok:
            print("        ⛔ it said: (%s, %s) · now it belongs to «%s»"
                  % (finished, reason_text, shared_slot_owner()))

        # ── 3 · the place is MINE, left from the previous round ────────────
        real_machine_skeleton(my)      # the cure had given it its own
        slot_belongs_to(my)
        said = clear_out_my_leftover(own_base)
        how_many += 1
        ok = not os.path.exists(SHARED_DIR)
        troubles += 0 if ok else 1
        print("  %s  ⭐ %s belongs to «%s» (MINE, from the previous round) ⇒ I clear it"
              % ("OK " if ok else "NO ", SHARED_DIR, my))
        if said:
            print("        says: %s" % said)
    finally:
        # ⛔ ONLY what this function made is removed.
        sh("rm -rf %s" % SHARED_DIR)
        via(foreign)
        via(my)
    return troubles, how_many


def create(chi, password):
    """Creates the tenant **from zero**, and ⛔ deletes it BEFORE creating it.

    ⚠ `[M]` (C1, 26 August 2026): an `id -u X || useradd X` makes the user new
      **only the first time the bench runs in its life**.  ⇒ «from zero»
      also includes «from zero with respect to myself of yesterday».
    """
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
    """⛔ We wait for it to be REALLY gone, not half a second by the clock.

    `[M]` (C1, 26 August 2026): without this wait the rounds alternated
    «I do not know» / judgement, because the next round started while the previous one
    was still dying.
    """
    sh("loginctl terminate-user %s 2>/dev/null" % chi)
    time.sleep(1.0)
    sh("pkill -KILL -u %s 2>/dev/null" % chi)
    expiry = time.time() + wait
    while time.time() < expiry:
        viva = sh("loginctl show-user %s >/dev/null 2>&1" % chi).returncode == 0
        proc = sh("pgrep -u %s >/dev/null 2>&1" % chi).returncode == 0
        if not viva and not proc:
            return True
        time.sleep(0.5)
    return False


def il_socket_di(chi):
    """Where this tenant's compositor talks.  ⛔ It is SEARCHED for, not guessed.

    ⚠ Nailing down `wayland-0` would mean a mesh that works on one desktop
      and stays silent on the others — i.e. exactly the defect this phase exists
      not to introduce (§3.7).
    """
    uid = sh("id -u %s" % chi).stdout.strip()
    if not uid:
        return None, None
    rtd = "/run/user/%s" % uid
    soc = sh("ls %s 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1" % rtd)
    d = soc.stdout.strip()
    return (rtd, d) if d else (rtd, None)

def ask_compositor(chi):
    """⭐ We ask the COMPOSITOR whether there is a screen, not the product.

    ⛔ A bench that asks the product whether the product worked believes what
       it is testing.  ⚠ And there is one more concrete reason: `[R]` the line
       *«⛔ ZERO MONITOR»* of `src/sessione.c:345-348` the product writes
       **also during a birth that will succeed**, because at that point the
       monitor has not appeared yet (`src/mutter.c:697`).

    Returns (how_many_screens | None, motivo).
    """
    rtd, display = il_socket_di(chi)
    if rtd is None:
        return None, ("I do not know the uid of «%s»: it does not exist, or `id` did not "
                      "answer" % chi)
    if display is None:
        return None, ("in %s there is no wayland socket: the compositor "
                      "has not been born (yet)" % rtd)
    r = sh("runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
           "wayland-info" % (chi, rtd, display), seconds=60)
    if r.returncode != 0 and not r.stdout:
        return None, ("wayland-info did not speak: %s"
                      % ((r.stderr or "").strip().replace("\n", " ")[:90]))
    return how_many_screens(r.stdout), ""


def turn_on_application(chi, application, call_args, page_v):
    """Switches on the application INSIDE the tenant's session.

    ⚠ `HOME` explicit and not inherited: the program's profile lives inside
      `$HOME`, and a mesh that looked at the wrong home would say one thing
      for another.
    ⛔ And the program's log ends up in a file of ITS OWN, not in the bench's working
       folder: `[M]` (C8, 26 August 2026) the bench's folder belongs to
       `root` with mode 0755 and the program runs as a USER ⇒ it could not write there,
       and the bench read its own defect as a product defect.
    """
    rtd, display = il_socket_di(chi)
    if display is None:
        return None, ("in %s there is no wayland socket: there is no "
                      "compositor the application can talk to"
                      % (rtd or "(unknown uid)"))
    try:
        args = call_args % {"page_v": page_v}
    except (ValueError, KeyError) as mistake:
        # ⛔ A literal `%` inside `--call_args` would blow up this line
        #    with a Python traceback instead of a message.  ⇒ Wrong usage.
        return None, ("I cannot build the arguments from «%s»: %s ⇒ in the "
                      "template one writes `%%(page_v)s`, and a literal `%%` must be "
                      "doubled" % (call_args, mistake))
    command = (
        # ⛔ `setsid` + stdin closed: without it, the browser ends up in a BACKGROUND
        #    process group of the terminal that launched the net and the first
        #    `tcsetattr` gets it a SIGTTOU ⇒ it stays in state `T` from the first
        #    instant (22 Sep 2026, seen in C3 on all three boxes).
        "setsid runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
        "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
        "%s %s < /dev/null > %s 2>&1 &"
        % (chi, rtd, display, chi, application, args, app_log(chi)))
    r = sh(command, seconds=30)
    if r.returncode != 0:
        # ⛔ And the result is NOT thrown away.  `LEZIONI.md` §1.46: a command that
        #    may not be run at all, and whose outcome nobody looks at,
        #    is a bench that accuses the product of what it did not do itself.
        return None, ("the launch did not start (outcome %d): %s"
                      % (r.returncode,
                         ((r.stderr or "") + (r.stdout or "")).strip()[:120]))
    return display, ""


def app_log(chi):
    """⭐ Where the application writes what it says — and ⛔ **it is read**.

    `[M]` (C8, 26 August 2026) the bench's working folder belongs to `root` with
    mode 0755 and the application runs as a USER ⇒ it could not write there.  So
    it writes in its own home.  ⚠ But a log nobody reads is worse than
    no log: it gives the impression that someone is looking.
    """
    return "/home/%s/.c2-applicazione.log" % chi


def last_line_said(chi):
    """The last line the application said, or «» if it said nothing."""
    r = sh("tail -n 5 %s 2>/dev/null" % app_log(chi))
    line_list = [x.strip() for x in (r.stdout or "").splitlines() if x.strip()]
    return line_list[-1][:160] if line_list else ""


def wait_started(chi, application, wait):
    """⛔ We wait for the application to EXIST before demanding a window.

    ⚠ It serves two things, and the second is worth more than the first:
      1. if it does not start at all (PAM, group, `$HOME` not writable) the outcome is
         **«I could not look»**, not a red for the product;
      2. ⛔⛔ the «dies at once» fault kills **by name and by user**, and at 1.5
         seconds from the launch the chain `runuser` → `env` → program may not
         have switched user yet: the `pkill` would find nothing,
         the program would start AFTERWARDS, paint, and the mesh would say *«the
         fault was NOT seen»* ⇒ ⛔ the hook would write
         `ha_visto_il_guasto: false` and **C13 would start saying that the net can
         no longer say red** while it is perfectly fine (`LEZIONI.md` §1.52).
      ⇒ We kill what we saw alive, not what we hope exists.
    """
    expiry = time.time() + wait
    while time.time() < expiry:
        n = how_many_processes(chi, application)
        if n:
            return n, round(wait - (expiry - time.time()), 1)
        time.sleep(1.0)
    return 0, None


def how_many_processes(chi, application):
    """How many processes of the application are alive.

    ⛔⛔ AND THIS NUMBER DECIDES NOTHING.  It is the quantity that `fasi/10…` §7.4
         measured **equal (1) in the two opposite cases**; it is here so that the
         mesh REPORTS it, and because with the «window that does not open» fault
         it serves to say that the fault is the right one — not to judge.
    ⚠ `None` = I could not count.
    """
    # ⛔⛔ AND WE DO NOT COUNT WITH `wc -l`, WHICH ALWAYS EXITS 0 AND ALWAYS PRINTS A
    #     NUMBER: with it «I could not count» and «zero processes»
    #     would become the same `0` — `LEZIONI.md` §1.47 — and zero is
    #     exactly the condition by which the «dies at once» fault is recognised.
    # ⭐ `pgrep` instead tells them apart by itself: 0 = I found some, 1 = none,
    #   ≥2 = I could not search.
    r = sh("pgrep -u %s -f %s" % (chi, application))
    if r.returncode == 1:
        return 0
    if r.returncode != 0:
        return None
    return len([x for x in (r.stdout or "").split() if x.strip()])


def previous_frames(flow, dove, how_many, ceiling):
    """The FIRST `how_many` frames of the stream — ⛔ and not just one.

    ⚠ The first draft took one.  ⛔ But the first frame of a grab
      is the natural candidate to be black or half drawn: the stage has
      just been born and the desktop is still painting itself.  ⇒ If the judge
      called it «black», this mesh would exit **3 forever** — i.e. the
      cousin of the perpetual red of `LEZIONI.md` §1.49, the one that cannot
      be made green.
    ⭐ With more frames we take **the first one the judge calls
      drawn**, and if none is we SAY how many were looked at.
    """
    outside = os.path.join(dove, "before")
    if os.path.isdir(outside):
        shutil.rmtree(outside, ignore_errors=True)
    os.makedirs(outside, exist_ok=True)
    r = sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -frames:v %d "
           "-y %s/p-%%03d.png" % (flow, how_many, outside), seconds=ceiling)
    listing = sorted(glob.glob(os.path.join(outside, "p-*.png")))
    return listing, (r.returncode == 124)


def last_frame_seen(flow, dove, ceiling):
    """The LAST frame of the stream — what the desktop shows at the end.

    ⛔ `-update 1` rewrites the same file at every decoded frame: at the
       end the last one remains.  ⚠⚠ **And for this reason the ceiling here BITES in a
       treacherous way**: if it expires halfway, the file is there anyway and it is a frame
       **from the middle** — which looks exactly like the last one.
    ⇒ ⛔ That is why here the exit code **is looked at**, and an expiry becomes
      «I could not look».  ⚠ It is the reverse of `LEZIONI.md` §1.50: there
      the exit code had to be ignored because the work was **done**
      (the PNG was there and was right); here the work was **interrupted**, and the
      PNG is there and it is another one.
    """
    last = os.path.join(dove, "ultimo.png")
    if os.path.exists(last):
        os.unlink(last)
    r = sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -update 1 -y %s"
           % (flow, last), seconds=ceiling)
    if r.returncode == 124:
        return None, True
    if not os.path.exists(last) or not os.path.getsize(last):
        return None, False
    return last, False


def choose_earliest(listing, judge):
    """⭐ The first frame the judge calls «drawn».

    Returns (path|None, how_many_looked_at, verdicts).
    """
    verdicts = []
    for p in listing:
        g = judge(p)
        verdicts.append("?" if g is None else g["verdict"])
        if g is not None and g["verdict"] not in ("nero", "quasi-nero"):
            return p, len(verdicts), verdicts
    return None, len(verdicts), verdicts


def how_many_frames(queue):
    """How many frames the client says it took from the wire.  `None` = I do not know."""
    how_many = None
    for row in queue.splitlines():
        if "[vid]" in row and "no frame" not in row:
            try:
                how_many = int(row.split("[vid]", 1)[1].strip().split()[0])
            except Exception:
                pass
    return how_many


# ═══════════════════════════════════════════════════════════════════════════
# ONE ROUND — a new tenant, a new session, a window
# ═══════════════════════════════════════════════════════════════════════════
def one_round(chi, manner, a, assessor, reader):
    """Returns a dictionary with the verdict of this tenant.

    `manner` = None | "dies" | "blind"

    ⛔⛔ THE ORDER OF THE MOVES IS NOT A DETAIL, and it is the reason why
         this mesh can be written today:

           1. the tenant is created
           2. ⭐ **the client attaches, and STAYS there** — the `wl_output` of
              a headless session is born when a consumer hooks onto the
              stream (`src/mutter.c:697` `[R]`) and dies with the child
           3. we wait for the COMPOSITOR to announce a screen
           4. **only then** is the application opened
           5. the client finishes its time and writes the stream
           6. the first and the last frame are judged

        ⇒ Swapping 2 and 4 would mean opening a window on a session that
          does not have a screen yet, ⛔ and blaming the application.
    """
    outcome = {"chi": chi, "manner": manner or "healthy", "state": "non-lo-so",
             "reason_text": "", "frazione_prima": None, "fraction_after": None,
             # ⚠ TWO counts, and not one: the one at the opening of the window and
             #   the one at the end.  ⛔ The frame that is judged is the last one,
             #   and counting the processes two minutes earlier would mean putting side by side
             #   two quantities taken at different moments and calling them a
             #   comparison.  ⇒ The fault signature uses the **final** one.
             "processes": None, "processi_apertura": None,
             "frames": None, "palco_s": None, "avvio_s": None,
             "screens": None, "desktop_prima": None, "said": "",
             "killed": None,
             "png_before": None, "png_after": None, "guardati_prima": None}

    finished, reason_text = create(chi, a.password)
    if not finished:
        outcome["reason_text"] = "I could not create «%s»: %s" % (chi, reason_text)
        return outcome

    work = os.path.join(a.work, chi)
    os.makedirs(work, exist_ok=True)
    flow = os.path.join(work, "take.264")
    if os.path.exists(flow):
        os.unlink(flow)

    # ── 2. the client attaches, and stays there ─────────────────────────────
    # ⛔ The time is computed, not nailed down: it must be enough for the
    #    birth of the stage PLUS the opening of the window PLUS a tail.  ⚠ If
    #    the stage is born early the surplus is wasted: it is the price of the fact that
    #    `--stays` is decided at launch and cannot be shortened later.
    stays = a.wait_stage + a.wait_window + a.queue
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
    out_file = os.path.join(work, "cliente.log")
    out_fd = open(out_file, "w")
    client = subprocess.Popen(
        ["python3", "-u", a.client,
         "--address", a.address, "--port", str(a.port),
         "--username", chi, "--password", a.password,
         "--video-write", flow, "--stays", str(stays)],
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

    # ── 3. we wait for the COMPOSITOR to announce a screen ──────────────────
    screens = None
    motivo = "I was never able to ask"
    expiry = time.time() + a.wait_stage
    while time.time() < expiry:
        if client.poll() is not None:
            motivo = "the client went away before a screen was born"
            break
        screens, motivo = ask_compositor(chi)
        if screens is not None and screens >= MIN_OUTPUTS:
            outcome["palco_s"] = round(time.time() - started, 1)
            break
        screens = None
        time.sleep(2.0)
    outcome["screens"] = screens

    if screens is None or screens < MIN_OUTPUTS:
        # ⛔ And it is NOT a red: it is «I could not look».  A window cannot
        #    open where there is no screen, and accusing the application
        #    would mean accusing it of something that happened before it.
        outcome["reason_text"] = ("in %.0f s the compositor did not announce any "
                           "screen (%s) ⇒ no application could open "
                           "a window" % (a.wait_stage, motivo or "?"))
        client.kill()
        close_client(30)
        clear_out(chi, a.wait_clearout)
        return outcome

    # ── 4. the application ──────────────────────────────────────────────────
    call_args = a.blind_arguments if manner == "blind" else a.call_args
    display, err = turn_on_application(chi, a.application, call_args, a.page_v)
    if display is None:
        outcome["reason_text"] = "I could not switch on the application: %s" % err
        client.kill()
        close_client(30)
        clear_out(chi, a.wait_clearout)
        return outcome

    # ⛔⛔ AND BEFORE ANYTHING ELSE WE WAIT FOR IT TO EXIST — see
    #     `wait_started`: if it does not start at all the outcome is «I could not
    #     look», not a red for the product; and the «dies at once» fault must
    #     kill what it SAW alive, not what it hopes exists.
    living, outcome["avvio_s"] = wait_started(chi, a.application, a.wait_startup)
    if not living:
        stated = last_line_said(chi)
        outcome["reason_text"] = ("the application «%s» never started in %.0f s%s "
                           "⇒ it is not the product that failed to show me a "
                           "window: there was nobody to draw it"
                           % (a.application, a.wait_startup,
                              (": it says «%s»" % stated) if stated else
                              " (and it said nothing)"))
        client.kill()
        close_client(30)
        clear_out(chi, a.wait_clearout)
        return outcome

    if manner == "dies":
        # ⛔ THE FAULT: the application dies at once.  ⚠ And it is killed BY NAME and
        #    BY USER, never with a global pattern — phase 10 §7.3, where a
        #    global `pkill -f` risked killing the work of another
        #    test that was measuring.
        # ⭐ AND THE OUTCOME OF THE `pkill` IS LOOKED AT: it is the difference between «I killed» and
        #   «there was nothing to kill», and it is what distinguishes a grafted
        #   fault from an injection that went nowhere (`LEZIONI.md` §1.46).
        time.sleep(a.dies_after)
        r = sh("pkill -KILL -u %s -f %s" % (chi, a.application))
        outcome["killed"] = (r.returncode == 0)
        if r.returncode != 0:
            outcome["reason_text"] = ("I asked to kill «%s» and `pkill` found "
                               "nothing to kill (outcome %d): "
                               "the injection did not take"
                               % (a.application, r.returncode))
            client.kill()
            close_client(30)
            clear_out(chi, a.wait_clearout)
            return outcome

    # ── 5. we wait for it to paint ──────────────────────────────────────────
    time.sleep(a.wait_window)
    outcome["processi_apertura"] = how_many_processes(chi, a.application)

    # ── 6. the client finishes and writes the stream ────────────────────────
    # ⛔ AND THE PROCESSES ARE COUNTED AGAIN HERE, next to the last frame: it is the one
    #    that is judged, and a count taken two minutes earlier does not sit next to it.
    queue = close_client(int(stays) + 180)
    outcome["processes"] = how_many_processes(chi, a.application)
    outcome["frames"] = how_many_frames(queue or "")
    outcome["said"] = last_line_said(chi)
    admitted = was_admitted(queue)

    if admitted is not True:
        # ⛔ «Not admitted» on its own is a silence: it hides three different things.
        #    ⇒ The REASON is carried next to the symptom (`LEZIONI.md` §1.9).
        last = "?"
        for row in reversed((queue or "").strip().splitlines()):
            row = row.strip()
            if row and not row.startswith("=="):
                last = row[:90]
                break
        outcome["reason_text"] = ("the client %s: %s"
                           % ("was not ADMITTED" if admitted is False
                              else "said NOTHING", last))
        clear_out(chi, a.wait_clearout)
        return outcome
    if not outcome["frames"]:
        # ⚠ And «zero» is told apart from «I do not know», which here have opposite causes.
        outcome["reason_text"] = (
            "%s ⇒ I have nothing to look at (last line of the client: «%s»)"
            % ("no frame arrived from the wire"
               if outcome["frames"] == 0 else
               "the client did not say how many frames it took", last_said(queue)))
        clear_out(chi, a.wait_clearout)
        return outcome

    # ── 7. the judgement, in the pixel ──────────────────────────────────────
    # ⛔ The ffmpeg ceilings FOLLOW the work they govern, instead of standing
    #    still while `--wait-stage` grows: `LEZIONI.md` §1.17 — a number
    #    that depends on another and does not know it is a number that will lie.
    ceiling = max(300.0, stays * 2.0)
    before_all, expired_p = previous_frames(
        flow, work, a.frames_before, ceiling)
    last, expired_u = last_frame_seen(flow, work, ceiling)
    if expired_u:
        outcome["reason_text"] = ("the decoder did not finish in %.0f s: what it "
                           "left is NOT the last frame but one from the "
                           "middle, and I do not judge it" % ceiling)
        clear_out(chi, a.wait_clearout)
        return outcome
    if not before_all:
        outcome["reason_text"] = ("%d frames arrived but the decoder "
                           "made no image of any of them%s"
                           % (outcome["frames"],
                              " (and it expired)" if expired_p else ""))
        clear_out(chi, a.wait_clearout)
        return outcome

    first, watched, verdicts = choose_earliest(before_all, assessor.judge)
    outcome["guardati_prima"] = watched
    outcome["png_before"], outcome["png_after"] = first, last
    if first is None:
        outcome["reason_text"] = ("the first %d frames are all black or nearly (%s): "
                           "the desktop had nothing to show BEFORE "
                           "the application, and this is not a judgement on C2"
                           % (watched, ", ".join(verdicts[:6])))
        clear_out(chi, a.wait_clearout)
        return outcome

    def fraction(p):
        return reader.color_fraction(p, COLOR, TOLERANCE)

    g = judge_round(first, last, assessor.judge, fraction,
                        outcome["processes"], a.minimum_fraction, a.headroom)
    outcome.update({k: g[k] for k in ("state", "reason_text", "frazione_prima",
                                    "fraction_after", "desktop_prima")})
    if outcome["state"] == "non-vista" and outcome["said"]:
        # ⭐ The reason next to the symptom: «it is not seen» alone hides
        #   «the application complained», and its log says so.
        outcome["reason_text"] += " ⚠ (the application says: «%s»)" % outcome["said"]
    clear_out(chi, a.wait_clearout)
    return outcome


def last_said(queue):
    for row in reversed((queue or "").strip().splitlines()):
        row = row.strip()
        if row and not row.startswith("=="):
            return row[:90]
    return "?"


def _n(x):
    return "unknown" if x is None else x


def print_out(e):
    face = {"vista": "YES", "non-vista": "NO ", "non-lo-so": "?  "}[e["state"]]
    print("  %-8s %-6s %s  %s" % (e["chi"], e["manner"], face, e["reason_text"]))
    print("           screens announced: %s · stage in %s s · application alive "
          "after %s s · frames: %s"
          % (_n(e["screens"]), _n(e["palco_s"]), _n(e["avvio_s"]),
             _n(e["frames"])))
    print("           ⚠ processes (they do NOT decide): %s at the opening, %s at the end · "
          "frames looked at for the «before»: %s"
          % (_n(e["processi_apertura"]), _n(e["processes"]),
             _n(e["guardati_prima"])))
    # ⭐ AND THE TWO JUDGED PNGs ARE ALWAYS STATED: on a red, without the path,
    #   there is nothing to look at without already knowing where to search.
    if e["png_before"] or e["png_after"]:
        print("           the two judged images: %s  ·  %s"
              % (e["png_before"] or "—", e["png_after"] or "—"))


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ THE JOINT — and it lives in a PURE function so that `--certify` tests it.
#
# ⛔⛔ It is the piece `LEZIONI.md` §1.52 was born for: *«C9's certification
#     tested the judge, C13's tested the reading of the log; the
#     defect was in the JOINT between the two — in the exit code, which belongs to
#     neither of the two trades»*.  ⇒ Here the exit code with the grafted fault
#     is **inverted** (`0` = the fault was seen), and from it `11-gancio.sh`
#     derives `ha_visto_il_guasto`, from which C13 says whether the net can still say
#     red.  ⛔ A joint like that is not left uncertified.
# ═══════════════════════════════════════════════════════════════════════════
def test_fault(fault, healthy, broken, minimum_fraction=MINIMUM_FRACTION,
                       quota=QUOTA_FAULT):
    """Returns `(outcome, [lines to print])`.  ⛔ The outcome is read BACKWARDS.

        0  ⭐ the fault WAS SEEN — the mesh can say red
        1  ⛔ the fault was NOT seen, or it bit too little
        3  ⚠ I could not graft it or I could not look
           ⇒ neither a certification nor an accusation
    """
    r = []
    r.append("  healthy control : %-10s (colour %s · processes %s)"
             % (healthy["state"],
                "unknown" if healthy["fraction_after"] is None
                else "%.1f%%" % (healthy["fraction_after"] * 100),
                _n(healthy["processes"])))
    r.append("  with the fault  : %-10s (colour %s · processes %s)"
             % (broken["state"],
                "unknown" if broken["fraction_after"] is None
                else "%.1f%%" % (broken["fraction_after"] * 100),
                _n(broken["processes"])))
    r.append("")

    if healthy["state"] == "non-lo-so" or broken["state"] == "non-lo-so":
        r.append("⚠ I could not judge: I cannot say whether the fault "
                 "would have been seen")
        r.append("   ⇒ and this does NOT accusations the mesh (§4.5: the hook writes it "
                 "as «graft not judged»)")
        return 3, r

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ THE RED HEALTHY CONTROL EXITS **3**, AND NOT 1 — and it is a correction.
    #
    # The first draft exited **1**.  ⚠ But `11-gancio.sh` reads a grafted round
    # BACKWARDS: `1` ⇒ `ha_visto_il_guasto: false`.  ⇒ ⛔ A REAL regression
    # of the product, happening precisely during the round with the grafted fault,
    # would have made C13 write *«the net can no longer say red»* — which is
    # exactly the defect of §1.52, produced by the cure of §1.52.
    # ⭐ The real red is already there and it is given by the round WITHOUT the fault, which in the
    #   family runs right before: here there is no need to repeat it, there is a need not to lie.
    # ═══════════════════════════════════════════════════════════════════════
    if healthy["state"] != "vista":
        r.append("⛔⛔ THE HEALTHY CONTROL IS RED: %s" % healthy["reason_text"])
        r.append("    ⇒ this round does NOT measure the fault — it measures a red that")
        r.append("      is already there on its own (LEZIONI.md §1.45).")
        r.append("    ⚠ And the outcome is 3 and not 1: saying «the fault was not "
                 "seen» would be")
        r.append("      an accusation against the net for a regression of the PRODUCT. "
                 "⇒ The real red")
        r.append("      is given by the round without the fault, which runs right before.")
        return 3, r

    if broken["state"] != "non-vista":
        r.append("⛔⛔ THE GRAFTED FAULT WAS NOT SEEN: the window is "
                 "seen anyway.")
        r.append("    ⇒ either the fault does not bite, or this mesh does not look in "
                 "the right place —")
        r.append("      and in both cases it cannot be trusted.")
        return 1, r

    # ⚠ AND EVERY FAULT DEMANDS ITS OWN SIGNATURE, or it is not that fault.
    #   ⛔ And if the signature is missing the outcome is **3**: a mesh that could not
    #      graft the fault has neither seen nor missed anything.
    proc = broken["processes"]
    if fault == "dies":
        if proc is None or proc > 0:
            r.append("⚠ the fault asked for was «the application dies at once», ⛔ "
                     "but at the end the processes are %s: the injection did not take."
                     % _n(proc))
            r.append("   ⇒ I did not graft that fault (outcome 3, not a red).")
            return 3, r
        if broken.get("killed") is False:
            r.append("⚠ `pkill` found nothing to kill: the injection "
                     "did not take (outcome 3, not a red).")
            return 3, r
    else:
        if proc is None or proc < 1:
            r.append("⚠ the fault asked for was «the window does not open and the "
                     "process STAYS ALIVE», ⛔ but the processes are %s." % _n(proc))
            r.append("   ⇒ without a live process I would be testing the other "
                     "fault (outcome 3, not a red).")
            return 3, r

    # ⭐ AND NOW THE MEASURABLE DIFFERENCE, which is what §1.52 demands.
    fs = healthy["fraction_after"] or 0.0
    fr = broken["fraction_after"] or 0.0
    r.append("  ⭐ measurable difference: the colour goes from %.1f%% to %.1f%% "
             "⇒ %.1f points, i.e. %.0f%% of the healthy one (I allow at most "
             "%.0f%%)"
             % (fs * 100, fr * 100, (fs - fr) * 100,
                (fr / fs * 100) if fs else 0.0, quota * 100))
    if fs <= 0 or fr > fs * quota:
        r.append("⛔ the verdict changed but the NUMBER hardly did: the fault "
                 "bit little or not at all,")
        r.append("   and an acceptance test like this does not certify the net.")
        return 1, r

    if fault == "dies":
        r.append("  ⭐ and the fault's signature is there: processes = 0 at the end "
                 "(the application really died)")
    else:
        # ⭐⭐ THE PROOF, with two numbers instead of a quotation.
        # ⚠ And it states what it REALLY proves: not that the two counts are
        #   equal (Firefox in kiosk makes more processes than headless), ⛔ but
        #   that **in both cases there is at least one live process** — i.e.
        #   that the count, whatever it is, does not separate the two worlds.  The pixel does.
        r.append("  ⭐⭐ AND THIS IS THE PROOF, with two numbers instead of "
                 "a quotation:")
        r.append("     the application is ALIVE in both rounds — %s processes "
                 "with the healthy one, %s with the fault —"
                 % (_n(healthy["processes"]), _n(broken["processes"])))
        r.append("     and the verdicts are OPPOSITE.  ⇒ ⛔ the process count does not "
                 "separate the two worlds; the pixel does.")
        r.append("     It is the finding of `fasi/11…` §4.1 (`[M]` it said 1 in "
                 "both cases), measured here.")

    r.append("")
    r.append("⭐ THE GRAFTED FAULT WAS SEEN — this mesh CAN say red.")
    return 0, r


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-user", default="c2u")
    p.add_argument("--rounds", type=int, default=1,
                   help="⚠ one is enough: «it is seen or it is not seen» is deterministic, "
                        "and every round costs a session birth")
    p.add_argument("--password", default="provanic2026")
    p.add_argument("--port", type=int, default=8511)
    p.add_argument("--address", default="127.0.0.1")
    p.add_argument("--client", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--page_v", default="/opt/remotix/11-c2-finestra.html")
    p.add_argument("--application", default="firefox-esr",
                   help="⚠ today the browser, because it is the only program in the "
                        "box that paints a DECLARED colour. ⛔ It must be "
                        "moved onto a minimal Wayland client as soon as there is "
                        "one that can do it (see the top)")
    p.add_argument("--call_args", default="--kiosk file://%(page_v)s",
                   help="how the application is asked to open the page")
    p.add_argument("--blind-arguments", default="--headless file://%(page_v)s",
                   help="⛔ THE «window that does not open» FAULT: the application "
                        "stays ALIVE and paints nothing")
    p.add_argument("--work", default="/var/lib/rete11/c2")
    # ⭐ 60 s, and the number comes from a MEASUREMENT: `[M]` 27 August 2026, inside the
    #   cured GNOME box the stage is born in **2.1÷4.2 s** ⇒ 60 s are more
    #   than ten times the worst measured.  ⛔ The 200 s of before were a
    #   prudent number chosen when the phenomenon seemed to last ~97 s — which
    #   was a fault of the box, later cured (`LEZIONI.md` §1.54).
    # ⚠ And here it is not a deadline but an ADDEND of `--stays`: every second
    #   too many is a second thrown away for every tenant, not a margin.
    p.add_argument("--wait-stage", type=float, default=60.0,
                   help="⛔ CEILING TO RECALIBRATE. [M] (C1, 27 Aug 2026, not mine) the "
                        "stage in the GNOME box is born in 95-101 s because of a "
                        "defect of the BOX (polkit); with that cured, ~2 s ⇒ "
                        "put back to ~20")
    p.add_argument("--wait-startup", type=float, default=30.0,
                   help="⛔ how long to wait for the application to EXIST (a "
                        "process of its own). Expired: «I could not look», never "
                        "a red — and the «dies at once» fault kills only what "
                        "it saw alive")
    p.add_argument("--wait-window", type=float, default=120.0,
                   help="⛔ CEILING TO RECALIBRATE: how long the application is given "
                        "to PAINT, after it has started. ⚠ 120 like C8, and "
                        "for the same MEASURED reason: [M] the first start of "
                        "Firefox in a cold box exceeds 25 s, and here the "
                        "box is really cold — `create()` does `userdel -r`, "
                        "so no profile exists")
    # ⭐ PHASE 12 (19 Sep 2026): from 12 to 240.  `[M]` On KDE the Plasma
    #   splash screen lasts ~2.4 s and sends ~140 black frames: with 12 the
    #   «before» on KDE was «I do not know» forever.  On GNOME the first
    #   drawn one arrives among the first anyway, and the choice does not change.
    #
    # ⛔⛔ AND 240 WAS NOT ENOUGH — 20 September 2026, baseline of phase 13.
    #
    # `[M]` Inside the complete round C2(kde) exited **3** three times out of three
    # («the first 240 frames are all black or nearly»), ⛔ and it was not the
    # product: the window had opened and covered 98.7 % of the screen —
    # the «after» image is the right one.  The bench did not have the **term of
    # comparison**, so it abstained.
    #
    # `[M]` Re-measured right afterwards, on the same box, **three times**:
    #   186 · 186 (box rebuilt from zero) · 189 (⭐ and with the host's
    #   cache emptied, `drop_caches`, to rule out the suspicion
    #   that it was the cold disk).  ⇒ The real number is around **187**,
    #   and it is **stable**: the margin on 240 was 54 frames, 29 %.
    #
    # `[?]` Why more are needed inside the complete round (379 frames
    #   in all against 249) is not measured.  The suspicion is written down:
    #   `PIANO.md` — between two benches on the same seat **the previous seat
    #   stays attached for about twenty seconds**, and C2(kde) in the round comes
    #   right after C9(kde), which made two sessions.
    #
    # ⭐ And the right cure is a ceiling that **does not bite**, not a ceiling recalibrated
    #   to a hair: searching for the «before» **stops at the first drawn frame**
    #   (`choose_earliest`), so raising it costs nothing when the desktop
    #   paints early — it only costs ffmpeg a few more PNGs to extract,
    #   and only in the case in which without them the mesh would say «I do not know».
    #   ⇒ 900: more than the stream has ever had (379), i.e.
    #     «look at them all».  ⛔ The judgement does not change one bit: the
    #     yardstick remains the colour that grows by 20 points and covers 25 %.
    p.add_argument("--frames-before", type=int, default=900,
                   help="how many initial frames are looked at to find the drawn "
                        "«before». ⛔ A single one would give «I do not know» "
                        "forever if the first were black (LEZIONI.md §1.49); 12 "
                        "are not enough for the Plasma splash screen")
    p.add_argument("--queue", type=float, default=15.0,
                   help="how long the client stays attached AFTER the window "
                        "has been judged ready, to carry away the frames")
    p.add_argument("--wait-clearout", type=float, default=60.0)
    p.add_argument("--dies-after", type=float, default=1.5,
                   help="how long the application lives in the «dies at once» fault")
    p.add_argument("--minimum-fraction", type=float, default=MINIMUM_FRACTION)
    p.add_argument("--headroom", type=float, default=MARGIN)
    p.add_argument("--dying-app", action="store_true",
                   help="⛔ GRAFTED FAULT: the application starts and dies at once. "
                        "The outcome is read BACKWARDS (0 = the fault was seen)")
    p.add_argument("--window-that-does-not-open", action="store_true",
                   help="⛔ GRAFTED FAULT: the application stays ALIVE and does not "
                        "paint. ⭐ It is the case that proves that counting the "
                        "processes is not enough")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()

    if a.certify:
        sys.exit(certify())

    if a.dying_app and a.window_that_does_not_open:
        print("⛔ one fault at a time: if two are grafted one no longer knows "
              "which one bit")
        sys.exit(2)
    # ═══════════════════════════════════════════════════════════════════════
    # ⛔⛔ THE GUARDS ON THE NUMBERS, and they are not pedantry: they are `LEZIONI.md` §1.44.
    #
    #   `--rounds 0`            ⇒ no round, no red, no «I do not know»
    #                           ⇒ ⛔ **GREEN with zero measurements underneath**
    #   `--minimum-fraction 0` ⇒ any image passes ⇒ a predicate that cannot
    #                           fail, asked for from the command line
    # ⚠ And `--certify` would not notice: it certifies the CONSTANTS, not the
    #   arguments.  ⇒ The guard goes here, where the arguments arrive.
    # ═══════════════════════════════════════════════════════════════════════
    if a.rounds < 1:
        print("⛔ --rounds %d: a round that does not run is not a green, it is wrong "
              "usage" % a.rounds)
        sys.exit(2)
    if a.minimum_fraction <= 0 or a.minimum_fraction > 1:
        print("⛔ --minimum-fraction %s: with 0 (or less) this mesh could no "
              "longer give red, and above 1 it could not give green"
              % a.minimum_fraction)
        sys.exit(2)
    if a.headroom < 0 or a.headroom > 1:
        print("⛔ --headroom %s: outside 0..1 it no longer governs anything"
              % a.headroom)
        sys.exit(2)
    if os.geteuid() != 0:
        print("⛔ it must be run as administrator: it has to create new tenants")
        sys.exit(2)

    # ── the terrain: without one of these we do not judge, and we say which ──
    assessor, dove_g = desktop_judge()
    if assessor is None:
        print("⛔ I cannot find the image judge (10-f1-testimone.py) next to me")
        print("   ⇒ I could not look")
        sys.exit(3)
    reader, dove_l = color_reader()
    if reader is None:
        print("⛔ I cannot find the colour reader (11-c8-…py) next to me")
        print("   ⇒ I could not look")
        sys.exit(3)
    for desc, dove in (("the test client", a.client),
                      ("the target page", a.page_v)):
        if not os.path.exists(dove):
            print("⛔ I cannot find %s: %s" % (desc, dove))
            print("   ⇒ I could not look")
            sys.exit(3)
    for program in (a.application, "ffmpeg", "wayland-info", "runuser"):
        if sh("command -v %s" % program).returncode != 0:
            print("⛔ the box does not have %s" % program)
            print("   ⇒ I could not look")
            sys.exit(3)
    try:
        import numpy, PIL  # noqa: F401
    except ImportError:
        print("⛔ numpy or Pillow is missing: the judge cannot read an image")
        print("   ⇒ I could not look")
        sys.exit(3)

    os.makedirs(a.work, exist_ok=True)
    fault = ("dies" if a.dying_app else
              "blind" if a.window_that_does_not_open else None)

    # ⭐ BEFORE any `create`: `create` does `userdel -r`, and from that moment the
    #   owner of `/tmp/mozilla` would be a NUMBER instead of a name — i.e.
    #   I would no longer recognise it as mine.
    rest = clear_out_my_leftover(a.base_user)

    print("== C2 — a window opens ==")
    print("   port %d · application «%s» · page %s"
          % (a.port, a.application, os.path.basename(a.page_v)))
    print("   yardstick: colour %s ±%d per channel, at least %.0f%% of the screen, "
          "grown by at least %.0f points"
          % (COLOR, TOLERANCE, a.minimum_fraction * 100, a.headroom * 100))
    print("   imported judges: %s · %s"
          % (os.path.basename(dove_g), os.path.basename(dove_l)))
    print("   provisioning: the cure of src/provisiona.sh, imported from C8, for every "
          "tenant I create")
    if rest:
        print("   %s" % rest)
    print("   ceilings (⛔ to recalibrate on the real thing): stage %.0f s · window %.0f s · "
          "tail %.0f s" % (a.wait_stage, a.wait_window, a.queue))
    if fault:
        print("   ⛔ GRAFTED FAULT: «%s» — and the outcome is read BACKWARDS"
              % ("the application dies at once" if fault == "dies"
                 else "the application stays ALIVE and does not paint"))
        print("   ⭐ and with it runs a HEALTHY CONTROL, or one could not "
              "distinguish «the fault bit» from «it was already red»")
    print("   ⛔ the process count is reported and decides NOTHING: "
          "[M] fasi/10 §7.4 said 1 in both cases")
    print()

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ WITH THE GRAFTED FAULT TWO TENANTS ARE OPENED, and not one.
    #    `LEZIONI.md` §1.52: the fault is not measured on the colour of the verdict, it is
    #    measured on the DIFFERENCE with respect to the round without the fault.
    # ═══════════════════════════════════════════════════════════════════════
    legs = []
    if fault:
        legs.append((None, "healthy"))
        legs.append((fault, "fault"))
    else:
        for n in range(a.rounds):
            legs.append((None, "healthy"))

    outcomes = []
    for n, (manner, _name) in enumerate(legs, 1):
        chi = "%s%d" % (a.base_user, n)
        e = one_round(chi, manner, a, assessor, reader)
        outcomes.append(e)
        print_out(e)

    print()
    if not fault:
        views = sum(1 for e in outcomes if e["state"] == "vista")
        no = sum(1 for e in outcomes if e["state"] == "non-vista")
        unknown = sum(1 for e in outcomes if e["state"] == "non-lo-so")
        print("  windows seen: %d   ⛔ NOT seen: %d   not judged: %d"
              % (views, no, unknown))
        if no:
            print("\n  ⛔⛔ RED — %d sessions out of %d showed no "
                  "window." % (no, len(outcomes)))
            sys.exit(1)
        if unknown:
            print("\n  ⚠ NOT JUDGING — %d rounds could not speak." % unknown)
            print("     ⛔ And this is not a green: it is an outcome of its own (§4.5).")
            sys.exit(3)
        print("\n  ⭐ GREEN — the window is seen in all %d sessions."
              % len(outcomes))
        sys.exit(0)

    # ── the acceptance test of the grafted fault ────────────────────────────
    outcome, line_list = test_fault(fault, outcomes[0], outcomes[1],
                                      a.minimum_fraction)
    for row in line_list:
        print(row)
    sys.exit(outcome)


if __name__ == "__main__":
    main()
