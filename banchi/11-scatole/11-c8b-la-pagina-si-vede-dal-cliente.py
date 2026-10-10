#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c8b — ⭐⭐⭐ «AND THE SAME PAGE IS SEEN **FROM THE CLIENT**»
===========================================================================

    python3 11-c8b-la-pagina-si-vede-dal-cliente.py
    python3 11-c8b-la-pagina-si-vede-dal-cliente.py --no-fix
    python3 11-c8b-la-pagina-si-vede-dal-cliente.py --certify

⛔ It is HALF B of C8, the one that in the phase document (§4.1, line «C8b») was
   declared *«today it is not measured: new sessions are born blind»*.

---------------------------------------------------------------------------
⭐⭐ WHY IT CAN BE DONE NOW — and the reason must be read before the code
---------------------------------------------------------------------------

`[M]` 27 August 2026, isolated bench with real Mutter: the `wl_output` of a
headless session is born ⛔ **only when a PipeWire consumer hooks
onto the stream** — 65-93 ms after the hooking, ⛔ **never before**.

⇒ ⭐ **While a client is attached, the screen is there.**  And «while a client
  is attached» is exactly the condition of this test.  ⛔ The line «today
  it is not measured» is no longer true, and this mesh exists for that.

⚠⚠ AND THE SAME DISCOVERY BRINGS TWO CONSTRAINTS, which here are the design:

  1. ⭐ **The client attaches FIRST**, and the browser is switched on **afterwards**, with the
     client still attached.  ⛔ The old draft of test B did the
     opposite — screenshot, detach, browser, second screenshot — i.e. it switched on the
     browser **when the screen was not there**, and then was surprised not to see
     anything.
  2. ⛔ **The monitor dies with the child's D-Bus connection, and the child
     dies with the client.**  ⇒ Nothing of what is seen here survives a
     detach, and this mesh never counts on it: ⭐ **a single attach, continuous,
     that covers the switching on of the browser AND the recording.**  (What survives
     a detach is C6's job, not this one's.)

---------------------------------------------------------------------------
⛔⛔ A NEW FILE AND NOT AN ARM OF C8a — and the choice is argued
---------------------------------------------------------------------------

The real question was: *one more arm inside `11-c8-il-secondo-apre-il-
browser.py`, or a file of its own?*  ⚠ Both roads had real arguments.

⭐ **In favour of the arm**: the scene is the same — the skeleton with
  `.cache -> /tmp`, the two tenants made with `useradd -m`, the provisioning
  cure, the pixel judge.  ⛔ Duplicating them would mean **two places that
  can diverge silently**, which is the defect this project fears
  in writing (`LEZIONI.md` §1.25, §1.17).

⛔ **In favour of the new file**, and it won for three reasons that do not cancel out:

  · **they run in different places.**  C8a ⭐ does not go through the product and runs in
    ANY box (the acceptance test of 26 August ran in the PLASMA one).
    C8b goes through the product, ⛔ and the product then (27 Aug 2026) could
    start **only GNOME** ⇒ in the KDE box C8b would have said «I could not
    look» forever — the cousin of the perpetual red of §1.49.
    ⚠ Today (21 Sep 2026) the product gives the image on gnome, kde and xfce, and
    where C8b runs is decided by `11-capacita-del-prodotto.sh`; the reason to
    keep the two files separate stays whole.
  · **they cost differently.**  C8a: `[M]` two tenants, a couple of minutes.
    C8b: `[S]` **~6 minutes** — each tenant keeps a wire attached for
    `26 + 120 + 30 = 176 s` (C1's stage ceiling, the browser's, the
    margin), ⛔ and the wire is written only at the end.  ⇒ A single file
    would force the hook to pay the dear price to get the little.
  · **they have outcomes of their own.**  In the hook's log two different trades under the
    same name are two lines that cannot be read (§1.52: the joint between
    two meshes is the place where defects hide).

⭐⭐ **And the argument for the arm was not thrown away: it was honoured by importing.**
  ⛔ This mesh **rewrites nothing** of the scene: skeleton, creation
  of the tenants, provisioning cure, cleanup of the shared place, colour,
  tolerance, minimum fraction and pixel reader ⇒ **all come from C8a**,
  by `import`.  ⚠ It is the same discipline C8a applies to `10-f1-testimone.py`
  (*«the judge is IMPORTED, not rewritten»*) and that `10-f1` applies to
  `03-marca.py`.  ⇒ If tomorrow the tolerance changes in C8a, **it changes here too**,
  and there is no second place to remember.

---------------------------------------------------------------------------
⭐ HOW IT JUDGES — the pixel, **through the product**, and by DIFFERENCE
---------------------------------------------------------------------------

For each tenant, with **a single attach**:

    t=0    the test client attaches  (⇒ the monitor is born)
    t=?    we wait for **the event**: the product log says that the stage
           mounted a monitor for THIS tenant
    +resp  a breath, so that at least one frame without browser has left
    ⇒      the browser is switched on INSIDE the session (kiosk, C8's page)
    +brw   we wait for it to draw
    t=R    the client detaches and **writes the stream** (⛔ it writes it only at the
           end: `01-b3-cliente.py`, `write_video`)
           ⇒ TWO frames are pulled out of the stream:
               the FIRST  = the desktop **before** the browser drew
               the LAST   = what the desktop shows **now**

And the verdict is a **difference**, not an absolute value:

    ⭐ it saw the page  ⟺  fraction(last) >= minimum  AND  fraction(first) < minimum

⛔ The «before» is not ceremony, and here it does **three** jobs:

  1. if the desktop is black or near-black, ⇒ ⛔ **it is not a red of C8b**: it is the
     fault that sits upstream, and blaming the browser for something that happened
     before the browser existed is the exact way in which this project has
     already lost two diagnoses;
  2. if the page is **already** there before I switch on the browser, ⛔ **it is not a
     green**: it would mean taking credit for someone else's browser.
     ⇒ «I could not look», and it says why;
  3. and without it *«the browser did not open»* and *«there was no screen»*
     would have the same face — ⚠ two different faults with a single symptom.

⛔⛔ AND «THE STAGE IS THERE» IT DOES NOT ASK ITSELF: IT ASKS **C1**.
   The birth judge — `read_birth`, `monitor_born`, `round_verdict` —
   and its ceiling `CAP_BIRTH` are **imported** from `11-c1-nasce-e-si-vede.py`.
   ⇒ ⭐ *«did the stage mount a monitor for this tenant?»* is a single
     question, and in the whole net it has **a single answer**.

   ⚠⚠ And the import avoids an error this mesh would have gladly copied:
      until 27 August 2026 the line «⛔ ZERO MONITOR» was read as **proof of
      blindness**, ⛔ and `[R]` `src/sessione.c:345-348` writes it in the mandatory
      step of a **SUCCESSFUL** birth — the monitor is mounted by capture,
      afterwards, when someone hooks on.  ⭐ C1 today counts that line and
      prints it without judging it, and C8b inherits the correction instead of repeating it.

   ⛔⛔ AND THE SAME HOLDS FOR THE CEILING, which is not here.  The first draft had
      written **152 s**, copied from C1 — 101.0 s measured on GNOME plus half.
      `[M]` A few hours later it was discovered that those ~97 s **were not the
      product's**: they were a defect of the BOX, and with the box cured the stage
      is born in **1.0 s** and C1's ceiling went down to **26 s**.  ⇒ ⭐ A number
      copied is a number that stays behind (`LEZIONI.md` §1.17): here there is
      **only one**, and it lives in C1.

---------------------------------------------------------------------------
⛔ HOW I KNOW IT CAN SAY RED — `--no-fix`, and it is read BACKWARDS
---------------------------------------------------------------------------

The same grafted fault as C8a: the tenants are born **without** the cure of
`src/provisiona.sh`, i.e. as the code of 25 August 2026 made them ⇒ the
**second** cannot make its Firefox profile, and the page does not arrive.

⭐ And the outcome with the grafted fault **is not measured on the colour of the verdict** —
  `LEZIONI.md` §1.52.  A **measurable difference** is demanded:

    fault SEEN (outcome 0)  ⟺  the FIRST saw the page
                            AND  at least one other did NOT
                            AND  ⭐ the two fractions are at least `MIN_JUMP` apart

  ⛔ Red to both ⇒ outcome **1**, and the line says so: *«the FIRST failed
     too»* — what is being measured is not that fault (§7-bis.12, §1.45).
  ⛔ Green to both ⇒ outcome **1**: either the cure was not needed, or this mesh
     does not look in the right place.
  ⛔ No judgement ⇒ outcome **3**: I cannot say whether the fault would have been seen.

---------------------------------------------------------------------------
⭐ WHAT HAS ALREADY RUN — and what has not, which is the half that matters
---------------------------------------------------------------------------

  `[M]` 27 Aug 2026, **on the laptop**  `--certify`: **51 cases of 51**, and
        ⭐ **12 faults grafted into the bench itself, all 12 bit**
        (among them: the «the FIRST failed too» guard dismantled, the minimum
        jump dismantled, the stage ceiling copied instead of taken from C1).
  `[M]` 27 Aug 2026, **on the laptop**  a **dry** run of the mechanics —
        fake client, fake log, real `ffmpeg`, real H.264 streams:
        the five cases (the browser draws · does not draw · black desktop ·
        no frame · the stage is not born) give **YES · NO · unknown ·
        unknown · unknown**, which is what they must give.
        ⭐ And a number that counts: through a **real H.264 4:2:0** chain the
        magenta comes back at **97.8 %** — i.e. C8a's tolerance
        (±48) withstands the chroma subsampling, which was Gemini's
        finding accepted in §4.3.

  ⛔⛔ AND WHAT HAS NOT RUN, declared: **the real round, in the box**.
     There is no `[M]` of this mesh against the product — neither green nor
     red — and until there is, ⚠ **the ceilings are arguments, not measurements**.
     ⇒ `--certify` covers the judgements and the joint; ⛔ it does **not** cover the mechanics
       (the wire, `ffmpeg`, the wait) — those were exercised by the dry run,
       and not even that one ever talked to the product.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ I looked: ALL the tenants see the page FROM THE CLIENT
  1  I looked: at least one does NOT see it                 ⇒ red
  3  ⛔ I could not look (no stage, no frames, judge
     absent, field not clean) — ⛔ and it is NOT a red
  2  the terrain does not hold, or the usage is wrong

⚠ ⛔ AND WHAT THIS MESH DOES **NOT** LOOK AT, declared:
  · it does **not** say that the browser started when the page is not seen: it says
    that it is not seen from the client.  ⭐ Whoever separates the three faults (browser dead ·
    profile never born · page not on screen) is **C8a**, and the two must be read
    together;
  · it does **not** look at the `/etc/skel/.cache` link: it looks at the effect, not the
    cause we believe we know;
  · it says **nothing** about sessions with **nobody** attached — ⛔ and about
    those, after the discovery of 27 August, there is nothing to say: the screen
    there does not exist by construction.
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


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CEILINGS — each one with ITS OWN name and ITS OWN value.  `LEZIONI.md` §1.45: a
#    ceiling borrowed from another test produces a red that no longer distinguishes
#    the fault from the bench, and then the acceptance test is worth nothing.
# ═══════════════════════════════════════════════════════════════════════════

# ── how long the stage may take to mount a monitor ──────────────────────────
# ⭐⭐ THIS NUMBER **DOES NOT LIVE HERE**: it is taken from `11-c1-nasce-e-si-vede.py`
#     (`CAP_BIRTH`), which is the mesh whose job is the birth, and which
#     certifies that ceiling against its own measurement.
#
# ⛔⛔ And the reason cost someone else half a day, today.  The first
#     draft of this mesh had written **152 s** in it, copied from C1 —
#     101.0 s measured on GNOME plus half.  ⚠ A few hours later it was discovered that
#     those ~97 s **were not the product's**: they were a defect of the BOX
#     (`groupmod -g` on `polkitd` not carrying the files along ⇒ polkit
#     dead ⇒ four 25 s timeouts on `gnome-shell`).  ⇒ `[M]` 27
#     August 2026, cured box: the stage is born in **1.0 s**, and C1's ceiling
#     went down to **26 s**.
# ⇒ ⛔ A number copied is a number that stays behind (`LEZIONI.md` §1.17:
#   *a new number enters five places, and one always stays behind*).  ⭐ Here
#   there is **only one**, and it is C1's.

# ── how long the BROWSER is given to draw, inside the session ────────────────
# ⛔ It is NOT 25 s, and the reason is measured: `LEZIONI.md` §1.45 — the **first**
#    start of Firefox in a cold box (which must first make its profile)
#    well exceeds 25 s, and with that ceiling C8a gave **red to both**
#    tenants, with the cure and without.  ⇒ C8a gave itself 120 s
#    (`--wait-shot`), and here the browser is **just as cold**: the
#    tenants of this mesh are new, and the profile does not exist yet.
# ⚠ `[?]` Here the browser must also **map a window on Wayland** and get it
#   to the encoder — i.e. it does **more** than in C8a.  ⇒ 120 s is a
#   credible lower limit, not a measured one: it is calibrated at the first real round.
WAIT_BROWSER = 120.0

# ── the breath between «the stage is there» and «I switch on the browser» ────
# ⚠ It serves one thing only: that at least one frame **without browser** has already
#   left, or the «first frame» would already contain the page and the mesh would not
#   know how to tell its own page from one that was already there.
# ⛔ `[?]` Three seconds is a prudent choice, not a measurement.  If at the real round
#    the «before» already comes out magenta, ⭐ **the number to raise is this one** — and the
#    mesh says so by itself instead of leaving it to be guessed.
RESPITE = 3.0

# ── the margin on the wire, after the browser has had its time ───────────────
# ⛔ The test client writes the stream **only at the end** of `--stays`
#    (`01-b3-cliente.py`, `write_video`: *«it is called AFTER the wait of --resta»*)
#    ⇒ there is no file to look at halfway, and `--stays` must be decided
#    BEFORE knowing how long the stage will take.  ⚠ It is the cost of this
#    mesh, and it is declared instead of hidden.
WIRE_MARGIN = 30.0

# ── ⭐ THE JUMP THAT MAKES THE DIFFERENCE MEASURABLE (`LEZIONI.md` §1.52) ─────
# With the grafted fault it is not enough that the first is «yes» and the second «no»: the
# two fractions must be **far apart**, or we would be celebrating a hair.
# ⚠ And the threshold is written on the real size of the phenomenon (§1.13): `[M]` 26
#   August 2026, C8a with the grafted fault ⇒ first **98.7 %**, second **nothing**.
#   ⇒ A jump of 0.10 is a tenth of what the phenomenon really does: far
#   from the noise, and very far from the real thing.
MIN_JUMP = 0.10


# ═══════════════════════════════════════════════════════════════════════════
# THE IMPORTS — ⛔ and each one with the reason why it is not rewritten
# ═══════════════════════════════════════════════════════════════════════════
def _module(fpath, label_name):
    """Loads a nearby bench as a module.  Returns `None` if it is not there or cannot
    be loaded — ⛔ and the caller must say «I could not look», never
    silently fall back on a poorer judgement."""
    if not fpath or not os.path.exists(fpath):
        return None
    spec = importlib.util.spec_from_file_location(label_name, fpath)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception:
        return None
    return m


def take_c8a():
    """⭐⭐ THE SCENE AND THE YARDSTICK COME FROM C8a, and not from a paraphrase of them.

    ⛔ From here come: `COLOR`, `TOLERANCE`, `MINIMUM_FRACTION`,
       `color_fraction`, `prepare_skeleton`, `clear_out_slot_shared`,
       `create`, `apply_fix`, `can_write_cache`, `open_browser`,
       `sh` and `image_judge`.
    ⇒ ⭐ Two meshes that measure the same colour with the same tolerance
      **because it is the same number**, not because someone remembered to
      copy it both times.
    """
    return _module(os.path.join(HERE, "11-c8-il-secondo-apre-il-browser.py"),
                   "c8a")


# ⭐ The four pieces of C1 without which this mesh cannot wait for the stage.
#   ⛔ They are here, in a list, and not scattered in the code: a list can be
#      checked, a dozen `getattr` cannot.
C1_PIECES = ("read_birth", "monitor_born", "round_verdict", "CAP_BIRTH")


def c1_has_what_it_needs(c1):
    """⛔ «C1 is there» is not «C1 has what I need».

    ⚠ C1 is alive: `[M]` on 27 August 2026 it was rewritten twice in one
      day, and the first draft of C8b imported a `FIRMA_MONITOR` that after
      that rewrite **no longer existed**.  ⇒ The mesh noticed it
      because `--certify` asked it; ⛔ without the check it would have
      noticed only inside the box, with a `None` in hand and a crooked red.
    ⭐ So: if the birth mesh changes shape, this one **says so** instead
      of silently falling back on a judgement of its own (`LEZIONI.md` §1.29).
    """
    if c1 is None:
        return False
    return all(hasattr(c1, piece) for piece in C1_PIECES)


def take_c1():
    """⭐⭐ THE BIRTH JUDGE COMES FROM C1 — ⛔ and it is not rewritten.

    From here come `read_birth`, `monitor_born`, `round_verdict` and the ceiling
    `CAP_BIRTH`.  ⇒ ⭐ *«did the stage mount a monitor for this
    tenant»* is **a single question**, and it has **a single answer** in the whole
    net: C1's.

    ⚠⚠ And the import avoids inheriting a defect this mesh would have
       gladly copied: until 27 August 2026 the line «⛔ ZERO MONITOR» was
       read as **proof of blindness**, ⛔ and `[R]` `src/sessione.c:345-348`
       writes it in the mandatory step of a **SUCCESSFUL** birth — the
       monitor is mounted by capture, afterwards.  ⇒ C1 today **counts and
       prints** that line, and does not judge it.  ⭐ By importing, C8b inherits the correction
       instead of repeating the error.

    Returns the module, or `None` if it is not there or does not have what is needed.
    """
    c1 = _module(os.path.join(HERE, "11-c1-nasce-e-si-vede.py"), "c1")
    return c1 if c1_has_what_it_needs(c1) else None


def find_judge(c8a):
    """The image judge of `10-f1-testimone.py`.

    ⚠ Two places, and we SAY which one was used (`LEZIONI.md` §1.48: a success
      message that repeats the intention is not a verification, it is an echo):
        · next to C8a  ⇒ as it is inside the box (`/opt/remotix`)
        · in the folder above ⇒ as it is in the repository (`banchi/`)
    ⛔ If it is neither here nor there, the outcome is **3**, never a poorer judgement.
    """
    g = c8a.image_judge() if c8a is not None else None
    if g is not None:
        return g, os.path.join(HERE, "10-f1-testimone.py")
    above = os.path.join(os.path.dirname(HERE), "10-f1-testimone.py")
    g = _module(above, "testimone10f1")
    if g is not None and hasattr(g, "judge"):
        return g, above
    return None, None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE JUDGEMENTS — PURE functions, so that `--certify` can run them all
#    without a box, without a server and without a browser.
# ═══════════════════════════════════════════════════════════════════════════
def stage_cap(c1):
    """⭐ The waiting ceiling for the stage, **taken from C1**.

    ⛔ It is not a constant of this file, and it must not become one: the day
       the birth changes speed, the number is corrected in **one place only**,
       that of the mesh that measures it.
    """
    return float(c1.CAP_BIRTH)


def wire_time_left(wait_stage, wait_browser, headroom=WIRE_MARGIN):
    """How long the client must stay attached.

    ⛔ It is COMPUTED from the three ceilings, not chosen: the wire must cover the wait
       for the stage **plus** that of the browser, or the mesh would detach before
       having looked at what it came to look at.
    """
    return float(wait_stage) + float(wait_browser) + float(headroom)


def judge_before(verdict, fraction, lowest):
    """What the desktop showed **before** I switched on the browser.

    `verdict`  what the `10-f1` judge says («nero», «quasi-nero»,
                «tinta-unita», «disegnato»), or `None` = I did not look
    `fraction`  how much was already the colour of the page, or `None`

    Returns `(state, explanation)`, with `state` among:
      «clean»       ⭐ there is a screen, drawn, and the page is NOT there yet
      «a-monte»      ⛔ the screen is black: the fault sits before the browser
      «gia-magenta»  ⛔ the page was already there: I cannot claim it
      «non-lo-so»    ⛔ I did not look — ⚠ and `None` is not zero
    """
    if verdict is None or fraction is None:
        return "non-lo-so", ("I could not look at the desktop BEFORE the "
                             "browser ⇒ ⛔ it is not «it was black»")
    if verdict in ("nero", "quasi-nero"):
        return "a-monte", ("the desktop is «%s» BEFORE the browser: the fault sits "
                           "upstream of C8b, ⛔ and it is not its red" % verdict)
    if fraction >= lowest:
        return "gia-magenta", ("⛔ the page already covered %.1f%% of the screen "
                               "BEFORE I switched on the browser: I cannot say "
                               "that I drew it" % (fraction * 100))
    return "clean", ("the desktop is «%s» and the page is not there yet "
                      "(%.1f%%)" % (verdict, fraction * 100))


def tenant_judgment(state_before, fraction_after, lowest):
    """⭐ The verdict on ONE tenant: did it see the page from the client?

    Returns `(True|False|None, motivo)` — ⛔ and `None` («I did not look») is not
    `False` («I looked and it was not there»).
    """
    if state_before != "clean":
        return None, "the field was not clean ⇒ I do not judge the after"
    if fraction_after is None:
        return None, ("I could not look at the desktop AFTER ⇒ ⛔ it is not «the "
                      "page was not there»")
    if fraction_after >= lowest:
        return True, "the page covers %.1f%% of the screen" % (fraction_after * 100)
    return False, ("⛔ the page covers %.1f%%, and at least %.0f%% is needed"
                   % (fraction_after * 100, lowest * 100))


def decide(outcomes, no_fix, lowest, jump=MIN_JUMP):
    """⭐⭐ THE JOINT — from N judgements to ONE exit code.

    ⛔ It lives in a pure function on purpose: `LEZIONI.md` §1.52 tells of a defect
       that **no certification caught** because it lay in the joint between two
       meshes — in the exit code, which was the job of neither of the two
       judges.  ⇒ Here the exit code **is** a job, and it has its cases.

    `outcomes` is a list, **in order of birth**, of dictionaries:
        {"chi": str, "seen_v": True|False|None, "after": float|None, ...}

    Returns `(code_v, motivo, righe_da_stampare)`.

    ⭐⭐ AND THE `motivo` IS NOT A LUXURY — it was born from a grafted fault that DID NOT
    BITE.  `[M]` 27 August 2026, while writing this mesh: undoing the
    guard *«the FIRST failed too»* the exit code stayed **1** anyway
    — by another road (the jump too small) — ⛔ and a
    certification that looked only at the number **said OK on a dismantled
    guard**.
    ⇒ ⛔ A right verdict for the wrong reason is a verdict that will stop
      being right without anyone noticing (`LEZIONI.md` §2.0: *a
      bench that says «no» must say WITH WHICH STAGE it said no*).  ⭐ That is why the
      reason comes out of the function, and the certification demands it together with the
      number.
    """
    line_list = []
    si = [e for e in outcomes if e["seen_v"] is True]
    no = [e for e in outcomes if e["seen_v"] is False]
    unknown = [e for e in outcomes if e["seen_v"] is None]

    line_list.append("  ⭐ see the page from the client: %d · ⛔ do NOT see it: %d · "
                 "not judged: %d" % (len(si), len(no), len(unknown)))

    if not no_fix:
        if no:
            line_list.append("⛔ RED: %d tenants out of %d do not see the page from the "
                         "client" % (len(no), len(outcomes)))
            for e in no:
                line_list.append("   ⇒ %s: %s" % (e["chi"], e.get("reason_text", "")))
            return 1, "red", line_list
        if unknown or not outcomes:
            line_list.append("⛔ I could not judge %d tenants out of %d ⇒ it is not "
                         "a green and it is not a red (§4.5)"
                         % (len(unknown), len(outcomes)))
            for e in unknown:
                line_list.append("   ⇒ %s: %s" % (e["chi"], e.get("reason_text", "")))
            return 3, "non-giudicato", line_list
        line_list.append("⭐ all %d tenants see the page THROUGH THE "
                     "PRODUCT" % len(outcomes))
        return 0, "tutti-vedono", line_list

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔ WITH THE GRAFTED FAULT IT IS READ BACKWARDS: here green is a red.
    # ═══════════════════════════════════════════════════════════════════════
    if not outcomes or all(e["seen_v"] is None for e in outcomes):
        line_list.append("⛔ I could not judge anyone: I cannot say whether the "
                     "fault would have been seen")
        return 3, "nessun-giudizio", line_list
    first = outcomes[0]
    if first["seen_v"] is None:
        line_list.append("⛔ I could not judge the FIRST tenant (%s): without "
                     "it I do not know WHOSE the red would be" % first["chi"])
        return 3, "primo-non-giudicato", line_list
    if first["seen_v"] is False:
        line_list.append("⛔⛔ THE FIRST FAILED TOO (%s): the expected fault bites "
                     "from the SECOND on." % first["chi"])
        line_list.append("   ⇒ either the shared place was already dirty, or what is "
                     "being measured is not the provisioning defect.")
        line_list.append("   ⚠ And a red that does not distinguish the fault from the bench "
                     "certifies nothing (`LEZIONI.md` §1.45).")
        return 1, "anche-il-primo", line_list
    if not no:
        line_list.append("⛔⛔ THE GRAFTED FAULT WAS NOT SEEN: everyone sees the "
                     "page even without the cure.")
        line_list.append("   ⇒ either the cure was not needed, or this mesh does not look in "
                     "the right place — and in both cases it cannot "
                     "be trusted.")
        return 1, "guasto-non-visto", line_list

    # ⭐ And now the part that counts: the DIFFERENCE, measured (`LEZIONI.md` §1.52).
    fr_first = first.get("after")
    worst = [e.get("after") for e in no if e.get("after") is not None]
    if fr_first is None or not worst:
        line_list.append("⛔ the fault seems seen, but I do not have the two numbers to "
                     "measure the difference ⇒ I certify nothing")
        return 3, "senza-numeri", line_list
    distance = fr_first - max(worst)
    line_list.append("   the difference: first %.1f%% · worst %.1f%% ⇒ jump "
                 "%.1f points (%.1f are needed)"
                 % (fr_first * 100, max(worst) * 100,
                    distance * 100, jump * 100))
    if distance < jump:
        line_list.append("⛔ THE JUMP IS TOO SMALL: the two tenants sit on the "
                     "two sides of a hair.")
        line_list.append("   ⇒ ⛔ a net is not certified on a difference that "
                     "cannot be told from the noise (`LEZIONI.md` §1.52).")
        return 1, "salto-troppo-piccolo", line_list
    line_list.append("⭐ THE GRAFTED FAULT WAS SEEN: %d tenants out of %d do not "
                 "see the page, ⛔ and the FIRST does"
                 % (len(no), len(outcomes)))
    line_list.append("   ⇒ they did not make it: %s"
                 % ", ".join(e["chi"] for e in no))
    line_list.append("   ⇒ ⭐ this mesh CAN say red, and the difference is "
                 "measurable")
    return 0, "guasto-visto", line_list


# ═══════════════════════════════════════════════════════════════════════════
# THE GRAB — ⛔ a single attach, and the browser is switched on INSIDE that attach
# ═══════════════════════════════════════════════════════════════════════════
def read_it(fpath):
    try:
        with open(fpath, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def how_many_frames(body_text):
    """From the client's log: how many frames ARRIVED.

    ⛔ `None` when nothing arrived, and not zero: an empty stream
       decoded would say «black screen» on a server that never had the
       chance to send anything (`LEZIONI.md` §1.30).
    """
    how_many = None
    for row in (body_text or "").splitlines():
        if "[vid]" in row and "no frame" not in row:
            try:
                how_many = int(row.split("[vid]", 1)[1].strip().split()[0])
            except Exception:
                pass
    return how_many or None


def ffmpeg(c8a, command):
    return c8a.sh(command, seconds=240)


# ── how many opening frames are looked at for the «before» ──────────────────
# ⭐ PHASE 12 (19 Sep 2026).  `[M]` On KDE the first frame of a new session
#   is the Plasma splash screen (99 % black + logo, ~2.4 s): it is the
#   REAL desktop switching on, and with the first frame only C8b called it
#   «upstream fault» forever.  ⇒ The «before» is the FIRST NON-BLACK frame
#   among the first `OPENING` — which on GNOME is the first, i.e. as it was.
# ⛔ And it gives nothing away: if they are all black the «before» stays the first (⇒
#    «upstream», as before); if the first non-black one is already the page, the judgement
#    of the «before» says «already magenta» and the mesh does not judge the after.
OPENING = 240


def extract(c8a, flow, first, last, assessor=None):
    """From the H.264 stream pulls out the «BEFORE» and the LAST frame.

    ⛔ They are two different questions and two commands are needed: the opening frames
       (the desktop **before** the browser), and `-update 1`, which always rewrites the
       same file and so the LAST decoded wins — which is what the
       desktop shows now.
    ⭐ The «before» is the first NON-BLACK among the first `OPENING` (see above);
       without a judge, the very first.
    """
    for f in (first, last):
        if os.path.exists(f):
            os.unlink(f)
    folder = os.path.dirname(first) or "."
    root = os.path.splitext(os.path.basename(first))[0]
    model = os.path.join(folder, "%s-apertura-%%03d.png" % root)
    c8a.sh("rm -f %s" % os.path.join(folder, "%s-apertura-*.png" % root))
    ffmpeg(c8a, "ffmpeg -hide_banner -loglevel error -i %s -vsync 0 "
                "-frames:v %d -y %s" % (flow, OPENING if assessor else 1, model))
    chosen = None
    for i in range(1, (OPENING if assessor else 1) + 1):
        p = model % i
        if not (os.path.exists(p) and os.path.getsize(p)):
            break
        if chosen is None:
            chosen = p              # the first, if none is better
        if assessor is None:
            break
        g = assessor.judge(p)
        if g and g.get("verdict") not in ("nero", "quasi-nero"):
            chosen = p
            if i > 1:
                print("           ⭐ the «before» is frame %d: the %d before it "
                      "were black (on KDE: the Plasma splash screen)" % (i, i - 1))
            break
    if chosen:
        c8a.sh("cp %s %s" % (chosen, first))
    c8a.sh("rm -f %s" % os.path.join(folder, "%s-apertura-*.png" % root))
    ffmpeg(c8a, "ffmpeg -hide_banner -loglevel error -i %s -vsync 0 "
                "-update 1 -y %s" % (flow, last))
    return (first if os.path.exists(first) and os.path.getsize(first) else None,
            last if os.path.exists(last) and os.path.getsize(last) else None)


def search_whole_recording(c8a, flow, folder, chi, lowest, how_many=240):
    """⭐ DIAGNOSIS ONLY — did the page appear **at some moment**?

    ⛔ It changes no verdict, and it cannot: the verdict is on the last
       frame, i.e. on what the desktop shows **now**.
    ⚠ But it serves to name the reason next to the symptom: `[M]` 25 August 2026, the
      Firefox «Profile Missing» dialog appeared halfway through the grab and
      on the last frame it was no longer there (`10-f1-testimone.py`, `--all_v`).
      ⇒ *«it never drew»* and *«it drew and then it disappeared»* are two
      different faults, and whoever reads has the right to know which of the two it is.
    """
    model = os.path.join(folder, "%s-seq-%%03d.png" % chi)
    c8a.sh("rm -f %s" % os.path.join(folder, "%s-seq-*.png" % chi))
    # ⚠ One frame per second, at most `how_many`: the recording lasts minutes, and
    #   decoding it all would cost more than the test.
    ffmpeg(c8a, "ffmpeg -hide_banner -loglevel error -i %s -vf fps=1 "
                "-frames:v %d -y %s" % (flow, how_many, model))
    best = None
    dove = None
    n = 0
    for i in range(1, how_many + 1):
        p = os.path.join(folder, "%s-seq-%03d.png" % (chi, i))
        if not os.path.exists(p):
            continue
        n += 1
        fr = c8a.color_fraction(p)
        if fr is not None and (best is None or fr > best):
            best = fr
            dove = i
    if not n:
        return "⚠ I could not reread the recording: no sample"
    if best is None:
        return "⚠ %d samples reviewed, none readable" % n
    if best >= lowest:
        return ("⛔⛔ THE PAGE WAS THERE and then it disappeared: at sample %d/%d it covered "
                "%.1f%% — ⚠ the browser drew, and something took it "
                "away from underneath" % (dove, n, best * 100))
    return ("⚠ in %d samples of the recording the page NEVER appeared "
            "(maximum %.1f%%): ⇒ it is not «it appeared and disappeared»"
            % (n, best * 100))


def await_stage(logbook, chi, c1, sign, expiry, client):
    """⛔ We wait for THE EVENT, not for the clock — with C1's birth judge.

    Returns `(seconds|None, reason_text|None)`.

    ⚠ The client is watched too: if it dies on its own, waiting for the stage
      until the deadline would be waiting for a dead man — we return at once, and say
      **who** died instead of leaving a silence (`LEZIONI.md` §1.29).
    ⭐ And when it expires, the why is said by **C1**: «CIECA» and «NON-LO-SO» are two
      different things, and whoever reads has the right to know which of the two.
    """
    t0 = time.time()
    last = None
    while time.time() < expiry:
        if client.poll() is not None:
            return None, ("the test client went away after %.0f s, before "
                          "the stage mounted a monitor" % (time.time() - t0))
        body_text = read_it(logbook)
        slice = body_text[sign:] if body_text is not None else ""
        last = c1.read_birth(slice, chi)
        if c1.monitor_born(last):
            return time.time() - t0, None
        time.sleep(1.0)
    state, reason_text = c1.round_verdict(last)
    return None, ("in %.0f s the stage did not mount any monitor for «%s» "
                  "(C1 says «%s»: %s): ⛔ without a screen the browser has nowhere "
                  "to draw, and this is NOT a red of C8b"
                  % (time.time() - t0, chi, state, reason_text))


def look_tenant(chi, a, c8a, c1, assessor):
    """⭐⭐ THE HEART — a single attach, and everything fits inside it.

    Returns a dictionary:
        {"before": float|None, "after": float|None, "verdetto_prima": str|None,
         "frames": int|None, "palco_s": float|None, "reason_text": str}
    """
    outcome = {"before": None, "after": None, "verdetto_prima": None,
             "frames": None, "palco_s": None, "reason_text": ""}
    flow = os.path.join(a.work, "%s.264" % chi)
    diary = os.path.join(a.work, "%s-cliente.log" % chi)
    for f in (flow, diary):
        if os.path.exists(f):
            os.unlink(f)

    body_text = read_it(a.logbook)
    if body_text is None:
        outcome["reason_text"] = ("I cannot read the product log (%s): "
                           "⛔ I do not know when the stage was born" % a.logbook)
        return outcome
    sign = len(body_text)

    stays = wire_time_left(a.wait_stage, a.wait_browser, a.wire_margin)
    # ⛔ The client writes the stream ONLY at the end: it is launched in the background and we
    #    work while it is attached.  ⚠ And the output goes into a FILE, not into a
    #    pipe: a full pipe would block the client, and a hung bench does not
    #    say anything to anyone (`LEZIONI.md` §1.51).
    lit = False
    with open(diary, "wb") as f:
        client = subprocess.Popen(
            ["python3", "-u", a.client,
             "--address", a.address, "--port", str(a.port),
             "--username", chi, "--password", a.password,
             "--video-write", flow, "--stays", "%.1f" % stays],
            stdout=f, stderr=subprocess.STDOUT)

    try:
        stage, reason_text = await_stage(
            a.logbook, chi, c1, sign,
            time.time() + a.wait_stage, client)
        outcome["palco_s"] = stage
        if stage is None:
            outcome["reason_text"] = reason_text
            return outcome

        # ⭐ The breath: at least one frame WITHOUT browser must have left,
        #   or the «before» would already contain the page.
        time.sleep(a.respite)

        display, err = c8a.open_browser(chi, a)
        if display is None:
            outcome["reason_text"] = "⛔ I could not switch on the browser: %s" % err
            return outcome
        lit = True
        outcome["reason_text"] = "browser switched on on %s" % display
        time.sleep(a.wait_browser)
    finally:
        if outcome["palco_s"] is None or not lit:
            # ⛔ Here there is nothing to collect — the stage was not born, or the
            #    browser did not switch on — and staying attached until the end
            #    would mean paying three minutes for a file I will not look at.
            # ⚠ And it is said: a bench that spends and does not explain is a bench that
            #   someone will switch off (§1.3 of the phase document).
            client.terminate()
            try:
                client.wait(timeout=30)
            except subprocess.TimeoutExpired:
                client.kill()
                client.wait(timeout=30)
        else:
            # ⭐ Otherwise we wait for it to finish BY ITSELF: it is the one that writes the
            #   stream — only at the end — and killing it would throw away the recording.
            try:
                client.wait(timeout=stays + 120)
            except subprocess.TimeoutExpired:
                client.kill()
                client.wait(timeout=30)

    queue = read_it(diary) or ""
    outcome["frames"] = how_many_frames(queue)
    if outcome["frames"] is None:
        latest = ""
        for row in reversed(queue.strip().splitlines()):
            if row.strip():
                latest = row.strip()[:110]
                break
        outcome["reason_text"] = ("no frame arrived from the wire ⇒ ⛔ it is not "
                           "«the screen was empty».  The client says: %s" % latest)
        return outcome

    first, last = extract(c8a, flow,
                           os.path.join(a.work, "%s-prima.png" % chi),
                           os.path.join(a.work, "%s-dopo.png" % chi), assessor)
    if first is None or last is None:
        outcome["reason_text"] = ("%d frames arrived but ffmpeg did not make "
                           "an image of them" % outcome["frames"])
        return outcome
    g = assessor.judge(first)
    outcome["verdetto_prima"] = g["verdict"] if g else None
    outcome["before"] = c8a.color_fraction(first)
    outcome["after"] = c8a.color_fraction(last)
    outcome["png_before"], outcome["png_after"] = first, last
    return outcome


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CERTIFICATION — and it declares what it covers and what it does not
# ═══════════════════════════════════════════════════════════════════════════
def certify():
    """⭐ Runs **all** the judgements of this mesh, on the laptop, without
    box, without server and without browser.

    COVERS: ⭐ the judgement of the «before» (black ⇒ it is not a red · already magenta ⇒
    it is not a green · nothing ⇒ «I do not know») · the verdict on the single tenant ·
    ⭐⭐ **the joint**, i.e. the exit code, in both directions (without fault and
    with the grafted fault, `LEZIONI.md` §1.52) · the ceilings, which are thresholds and as
    such are certified · ⭐ that the yardstick is **C8a's** and not a copy.
    ⛔ DOES NOT COVER: that the pixel reader can recognise the colour — that
    is certified in C8a (8 cases of 8) — nor that the image judge
    can say «black» — that is certified in `10-f1` (12 grafted faults).
    ⇒ A certification that declares itself wider than it is is worth less than
      no certification.
    """
    print("== certification of C8b — «the page is seen FROM THE CLIENT» ==")

    c8a = take_c8a()
    if c8a is None:
        print("⛔ I cannot find C8a (11-c8-il-secondo-apre-il-browser.py) next to me:")
        print("   ⇒ without it I have neither the scene nor the yardstick")
        print("   ⇒ I could not look")
        return 3
    assessor, dove = find_judge(c8a)
    if assessor is None:
        print("⛔ I cannot find the image judge (10-f1-testimone.py)")
        print("   ⇒ I could not look")
        return 3
    c1 = take_c1()
    if c1 is None:
        print("⛔ I cannot find C1 (11-c1-nasce-e-si-vede.py), or it no longer has the")
        print("   birth judge I need ⇒ I could not look")
        return 3

    lowest = c8a.MINIMUM_FRACTION
    print("   the yardstick comes from C8a: colour %s · tolerance ±%d · minimum "
          "fraction %.2f" % (c8a.COLOR, c8a.TOLERANCE, lowest))
    print("   the image judge: %s" % dove)
    print("   the birth judge and its ceiling: from C1, %.0f s"
          % c1.CAP_BIRTH)
    print()

    troubles = 0
    how_many = 0

    def prova(grp, label_name, expected_val, obtained):
        # ⛔ The count is kept HERE and printed by READING IT BACK: an «N of N» written
        #    by hand at the end is a number that stays behind (`LEZIONI.md` §1.48).
        nonlocal troubles, how_many
        how_many += 1
        ok = (expected_val == obtained)
        if not ok:
            troubles += 1
        print("  %s  %-8s %-52s expected %-14s got %s"
              % ("OK " if ok else "NO ", grp, label_name, repr(expected_val),
                 repr(obtained)))
        return ok

    # ── P1 · the judgement of the BEFORE ────────────────────────────────────
    print("  P1 · the desktop BEFORE the browser — ⛔ three outcomes, not two")
    prova("P1", "desktop drawn, no page ⇒ clean", "clean",
          judge_before("disegnato", 0.001, lowest)[0])
    prova("P1", "BLACK desktop ⇒ «upstream», ⛔ not a red of C8b", "a-monte",
          judge_before("nero", 0.0, lowest)[0])
    prova("P1", "NEAR-BLACK desktop ⇒ «upstream»", "a-monte",
          judge_before("quasi-nero", 0.0, lowest)[0])
    prova("P1", "⭐ the page was ALREADY there ⇒ I do not claim it", "gia-magenta",
          judge_before("disegnato", 0.99, lowest)[0])
    prova("P1", "⛔ I did not look ⇒ «I do not know», not «it was black»", "non-lo-so",
          judge_before(None, None, lowest)[0])
    prova("P1", "⛔ I have a verdict but not the fraction ⇒ «I do not know»", "non-lo-so",
          judge_before("disegnato", None, lowest)[0])

    # ⭐ And the two cases that REALLY go through the pixels, with real images: here
    #   the reader is not certified (it is C8a's), it is certified that the IMPORT is
    #   alive — ⛔ that the yardstick used is C8a's and not a faded copy.
    print("\n  P2 · ⭐ the yardstick is REALLY C8a's (the import is alive)")
    try:
        import numpy as np
        from PIL import Image
        import tempfile
        lav = tempfile.mkdtemp(prefix="c8bcert-")

        def paint(label_name, fill, blot=None):
            arr = np.zeros((216, 384, 3), dtype="uint8")
            arr[:, :] = fill
            if blot is not None:
                arr[80:136, 100:284] = blot
            p = os.path.join(lav, label_name + ".png")
            Image.fromarray(arr).save(p)
            return p

        page_v = paint("page_v", c8a.COLOR, (0, 0, 0))
        blank = paint("blank", (58, 62, 70), (200, 200, 200))
        nero = paint("nero", (0, 0, 0))
        fr_page = c8a.color_fraction(page_v)
        fr_empty = c8a.color_fraction(blank)
        prova("P2", "the page is found with the imported yardstick", True,
              fr_page is not None and fr_page >= lowest)
        prova("P2", "a desktop without the page does not find it", True,
              fr_empty is not None and fr_empty < lowest)
        prova("P2", "⛔ a file that is not there ⇒ None, not zero", None,
              c8a.color_fraction(os.path.join(lav, "manca.png")))
        prova("P2", "the 10-f1 judge says «nero» on a black screen",
              "nero", (assessor.judge(nero) or {}).get("verdict"))
        # ⭐ And the whole chain, from the PNG to the tenant's verdict.
        state, _ = judge_before(
            (assessor.judge(blank) or {}).get("verdict"),
            c8a.color_fraction(blank), lowest)
        prova("P2", "⭐ whole chain: empty desktop ⇒ clean field", "clean",
              state)
        prova("P2", "⭐ whole chain: clean + page ⇒ SEEN", True,
              tenant_judgment(state, fr_page, lowest)[0])
    except ImportError:
        print("  ⛔ numpy or Pillow is missing: I cannot certify the import")
        print("     ⇒ I could not look")
        return 3

    # ── P3 · the verdict on a tenant ────────────────────────────────────────
    print("\n  P3 · the verdict on ONE tenant")
    prova("P3", "clean field, full page ⇒ YES", True,
          tenant_judgment("clean", 0.987, lowest)[0])
    prova("P3", "clean field, no page ⇒ NO", False,
          tenant_judgment("clean", 0.004, lowest)[0])
    prova("P3", "⛔ clean field, after not looked at ⇒ «I do not know»", None,
          tenant_judgment("clean", None, lowest)[0])
    prova("P3", "⛔ black desktop before ⇒ «I do not know», not a red", None,
          tenant_judgment("a-monte", 0.0, lowest)[0])
    prova("P3", "⛔ page already present before ⇒ «I do not know», not a green", None,
          tenant_judgment("gia-magenta", 0.99, lowest)[0])
    # ⚠ And the threshold is calibrated in both directions, like C1 and C8a: just above passes,
    #   just below does not — or it is not a threshold, it is an opinion.
    prova("P3", "just ABOVE the minimum fraction ⇒ YES", True,
          tenant_judgment("clean", lowest + 0.001, lowest)[0])
    prova("P3", "just BELOW the minimum fraction ⇒ NO", False,
          tenant_judgment("clean", lowest - 0.001, lowest)[0])

    def E(chi, seen_v, after):
        return {"chi": chi, "seen_v": seen_v, "after": after, "reason_text": ""}

    # ⛔⛔ AND FROM HERE ON **THE NUMBER AND THE REASON** ARE DEMANDED, not the number.
    #
    # `[M]` 27 August 2026, while writing this mesh: dismantling the guard «the
    # FIRST failed too» the exit code stayed **1** anyway, by
    # another road — ⛔ and this certification, which looked only at the number,
    # said **OK on a dismantled guard**.  ⇒ It is §1.44 in another guise: a
    # check that cannot give red looks like one that passes.
    def judgment(outcomes_, no_fix_):
        c, m, _ = decide(outcomes_, no_fix_, lowest)
        return (c, m)

    # ── P4 · the joint, WITHOUT grafted fault ───────────────────────────────
    print("\n  P4 · the exit code, normal round — ⭐ number AND reason")
    prova("P4", "both see ⇒ 0", (0, "tutti-vedono"),
          judgment([E("u1", True, 0.98), E("u2", True, 0.98)], False))
    prova("P4", "one does not see ⇒ 1 (red)", (1, "red"),
          judgment([E("u1", True, 0.98), E("u2", False, 0.00)], False))
    prova("P4", "⛔ one not judged ⇒ 3, and it is not a green", (3, "non-giudicato"),
          judgment([E("u1", True, 0.98), E("u2", None, None)], False))
    prova("P4", "⛔ nobody judged ⇒ 3", (3, "non-giudicato"),
          judgment([E("u1", None, None), E("u2", None, None)], False))
    prova("P4", "⛔ no tenant at all ⇒ 3, not 0", (3, "non-giudicato"),
          judgment([], False))

    # ── P5 · the joint WITH the grafted fault — it is read backwards ────────
    print("\n  P5 · ⛔ with the grafted fault: `0` = fault SEEN (§1.52)")
    prova("P5", "⭐ first yes, second no, wide jump ⇒ 0 (seen)",
          (0, "guasto-visto"),
          judgment([E("u1", True, 0.987), E("u2", False, 0.001)], True))
    prova("P5", "⛔ both see ⇒ 1 (the fault did not bite)",
          (1, "guasto-non-visto"),
          judgment([E("u1", True, 0.98), E("u2", True, 0.98)], True))
    # ⭐⭐ THE GUARD OF §7-bis.12, and it is demanded BY NAME: with the grafted fault
    #    a red also on the FIRST is not that fault — ⛔ and without the reason
    #    this case passed even with the guard dismantled.
    prova("P5", "⛔ the FIRST failed too ⇒ 1, and for THAT reason",
          (1, "anche-il-primo"),
          judgment([E("u1", False, 0.0), E("u2", False, 0.0)], True))
    prova("P5", "⛔ no judgement ⇒ 3, and not «it was not seen»",
          (3, "nessun-giudizio"),
          judgment([E("u1", None, None), E("u2", None, None)], True))
    prova("P5", "⛔ the first not judged ⇒ 3, and for THAT reason",
          (3, "primo-non-giudicato"),
          judgment([E("u1", None, None), E("u2", False, 0.0)], True))
    # ⭐⭐ THE CASE WORTH MORE THAN ALL — `LEZIONI.md` §1.52: the grafted
    #    fault is not measured on the COLOUR of the verdict, it is measured on the
    #    DIFFERENCE.  Here the two sit on the two sides of a hair: the verdict
    #    would be «seen», ⛔ and it must not be enough.
    prova("P5", "⛔⛔ jump below the minimum (0.26 vs 0.24) ⇒ 1, not 0",
          (1, "salto-troppo-piccolo"),
          judgment([E("u1", True, lowest + 0.01), E("u2", False, lowest - 0.01)],
                   True))
    prova("P5", "⭐ and as soon as the jump is enough ⇒ 0", (0, "guasto-visto"),
          judgment([E("u1", True, lowest + MIN_JUMP),
                    E("u2", False, lowest - 0.001)], True))
    prova("P5", "⛔ seen but without the numbers ⇒ 3 (I do not certify in the dark)",
          (3, "senza-numeri"),
          judgment([E("u1", True, None), E("u2", False, None)], True))

    # ── P6 · the ceilings are thresholds, and thresholds are certified ──────
    print("\n  P6 · ⭐ the BIRTH judge is C1's, and I prove it")
    # `[M]` 27 Aug 2026, cured GNOME box — the real line of witness A
    #   (10 Oct 2026: in the English text of the product).
    born = c1.read_birth(
        "capture_v  [c8bu1] negotiated format: 1920x1080\n", "c8bu1")
    prova("P6", "the «negotiated format» ⇒ the monitor is there", True,
          bool(c1.monitor_born(born)))
    prova("P6", "and C1's verdict is «NATA»", "NATA",
          c1.round_verdict(born)[0])
    # ⛔⛔ THE CASE WORTH THE MOST: the «ZERO MONITOR» line alone is NOT a
    #    monitor — and it is not even a proof of blindness.  ⇒ If this mesh
    #    read it as the event it is waiting for, it would switch on the browser on a
    #    screen that is not there.
    zero = c1.read_birth(
        "session_v [c8bu1] ⛔ ZERO MONITORS, and the session is alive\n", "c8bu1")
    prova("P6", "⛔ «ZERO MONITOR» alone does NOT make the monitor be born", False,
          bool(c1.monitor_born(zero)))
    # ⚠ And homonymy: the log is shared by the two tenants.
    others = c1.read_birth(
        "capture_v  [c8bu2] negotiated format: 1920x1080\n", "c8bu1")
    prova("P6", "⛔ the stage of ANOTHER tenant is not mine", False,
          bool(c1.monitor_born(others)))
    prova("P6", "⛔ silent log ⇒ «I do not know», not «blind»", "NON-LO-SO",
          c1.round_verdict(c1.read_birth("", "c8bu1"))[0])
    # ⛔⛔ AND THE GUARD ON THE IMPORT, exercised with a fake C1 missing a
    #    piece: ⚠ a check that has never been seen firing is not a
    #    check, it is a hope (`LEZIONI.md` §1.44).
    import types as _types
    prova("P6", "the real C1 has all the pieces I need", True,
          c1_has_what_it_needs(c1))
    for missing in C1_PIECES:
        mock = _types.SimpleNamespace(**{p: (1 if p == "CAP_BIRTH"
                                             else (lambda *x: None))
                                         for p in C1_PIECES if p != missing})
        prova("P6", "⛔ a C1 without «%s» is refused" % missing, False,
              c1_has_what_it_needs(mock))
    prova("P6", "⛔ and no C1 at all is refused", False,
          c1_has_what_it_needs(None))

    print("\n  P7 · the ceilings — ⛔ each one with ITS OWN value, `LEZIONI.md` §1.45")
    # ⭐⭐ The stage ceiling is NOT a number of this file: it is C1's.
    #    ⛔ The following case is the only one that would have caught the defect of the first
    #    draft, which had copied 152 s from C1 a few hours before C1
    #    lowered them to 26 (`LEZIONI.md` §1.17).
    prova("P7", "⭐ I take the stage ceiling from C1, I do not have one of my own", True,
          "RITARDO_PALCO" not in globals())
    prova("P7", "and the default is exactly its own", c1.CAP_BIRTH,
          stage_cap(c1))
    # ⛔ The browser ceiling is NOT lent by another wait: it is its own, and it is
    #    at least as much as C8a gives itself for the cold first start (`--wait-shot`
    #    = 120 s, `LEZIONI.md` §1.45).
    prova("P7", "the browser ceiling withstands the cold first start (120 s)",
          True, WAIT_BROWSER >= 120.0)
    prova("P7", "⛔ the two ceilings are DIFFERENT: neither is lent to the other",
          True, WAIT_BROWSER != c1.CAP_BIRTH)
    prova("P7", "the wire stays attached longer than the sum of the two", True,
          wire_time_left(c1.CAP_BIRTH, WAIT_BROWSER)
          > c1.CAP_BIRTH + WAIT_BROWSER)
    prova("P7", "the wire's count is a CALCULATION, not a round number", 176.0,
          wire_time_left(26.0, 120.0, 30.0))
    prova("P7", "⭐ the breath is there, or the «before» would already contain the page",
          True, RESPITE > 0)
    prova("P7", "⛔ the minimum jump is well below the measured phenomenon (98.7 %)",
          True, 0.0 < MIN_JUMP < 0.5)

    print()
    if troubles:
        print("⛔ C8b is NOT certified: %d cases wrong out of %d" % (troubles, how_many))
        return 1
    print("⭐ %d cases out of %d: C8b can say green, red and «I do not know» — and with the "
          "grafted fault" % (how_many, how_many))
    print("   ⭐ it demands a measurable DIFFERENCE, not the colour of the verdict")
    print("⚠ and this certification covers THE JUDGEMENTS AND THE JOINT, not the pixel")
    print("  reader (certified in C8a) nor the image judge")
    print("  (certified in 10-f1) — see the declaration at the top of certify()")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--base-user", default="c8bu",
                   help="⛔ different from C8a's («c8u»): two benches with the "
                        "same tenants falsify each other silently (§1.26)")
    p.add_argument("--how_many", type=int, default=2,
                   help="TWO, like C8a: the question is correctness with several "
                        "tenants, not capacity")
    p.add_argument("--password", default="provanic2026")
    p.add_argument("--port", type=int, default=8511)
    p.add_argument("--address", default="127.0.0.1")
    p.add_argument("--client", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--page_v", default="/opt/remotix/11-c8-pagina.html")
    p.add_argument("--browser", default="firefox-esr")
    p.add_argument("--logbook", default="/var/lib/rete11/registro.log")
    p.add_argument("--work", default="/var/lib/rete11/c8b")
    p.add_argument("--wait-stage", type=float, default=None,
                   help="how long to wait for the stage to mount a monitor. "
                        "⭐ Default: C1's ceiling (`CAP_BIRTH`), taken "
                        "from it and not copied. Expired: «I could not "
                        "look», ⛔ NEVER a red")
    p.add_argument("--wait-browser", type=float, default=WAIT_BROWSER,
                   help="how long the browser is given to draw the page "
                        "INSIDE the session. ⛔ 120 s and not 25: the cold first "
                        "start must make its profile (LEZIONI.md §1.45)")
    p.add_argument("--respite", type=float, default=RESPITE,
                   help="⭐ how long to wait, after the stage is there, before "
                        "switching on the browser: it serves to get at least one "
                        "frame WITHOUT the page going")
    p.add_argument("--wire-margin", type=float, default=WIRE_MARGIN,
                   help="how long the wire stays attached beyond the sum of the two "
                        "ceilings. ⛔ The client writes the stream only at the end")
    p.add_argument("--wait-clearout", type=float, default=45.0,
                   help="how long to wait for the previous tenant to be REALLY "
                        "gone, before making the next one be born")
    p.add_argument("--no-fix", action="store_true",
                   help="⛔ THE GRAFTED FAULT: the provisioning cure is not "
                        "applied. The second tenant MUST give red, and the "
                        "difference must be measurable")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()

    if a.certify:
        sys.exit(certify())

    if os.geteuid() != 0:
        print("⛔ it must be run as administrator: it has to create the tenants")
        sys.exit(2)

    # ── what we cannot judge without ───────────────────────────────────────
    c8a = take_c8a()
    if c8a is None:
        print("⛔ I cannot find C8a (11-c8-il-secondo-apre-il-browser.py) next to me")
        print("   ⇒ without it I have neither the scene nor the yardstick")
        print("   ⇒ I could not look")
        sys.exit(3)
    assessor, judge_path = find_judge(c8a)
    if assessor is None:
        print("⛔ I cannot find the image judge (10-f1-testimone.py)")
        print("   ⇒ I could not look")
        sys.exit(3)
    c1 = take_c1()
    if c1 is None:
        print("⛔ I cannot find C1 (11-c1-nasce-e-si-vede.py), or it no longer has the "
              "birth judge I need")
        print("   ⇒ I could not look")
        sys.exit(3)
    # ⛔ The ceiling is filled NOW, from C1: `argparse` cannot do it, because
    #    when it builds the defaults C1 has not been loaded yet.
    if a.wait_stage is None:
        a.wait_stage = stage_cap(c1)
    for label_name, path in (("the test client", a.client),
                       ("the target page", a.page_v)):
        if not os.path.exists(path):
            print("⛔ I cannot find %s: %s" % (label_name, path))
            print("   ⇒ I could not look")
            sys.exit(3)
    if c8a.sh("command -v %s" % a.browser).returncode != 0:
        print("⛔ the box does not have %s" % a.browser)
        print("   ⇒ I could not look")
        sys.exit(3)
    if c8a.sh("command -v ffmpeg").returncode != 0:
        print("⛔ the box does not have ffmpeg: the frames do not become "
              "an image")
        print("   ⇒ I could not look")
        sys.exit(3)
    if read_it(a.logbook) is None:
        print("⛔ I cannot read the product log: %s" % a.logbook)
        print("   ⇒ I could not look")
        sys.exit(3)

    os.makedirs(a.work, exist_ok=True)
    lowest = c8a.MINIMUM_FRACTION
    dove = c8a.prepare_skeleton()
    # ⛔ `/tmp/mozilla` is cleared for BOTH families of tenants: if
    #    C8a's remained, the FIRST of this mesh would fail like the
    #    second — i.e. a red for the wrong reason.
    # ⭐ And C8a's function is called twice instead of rewriting one: its
    #   rule («do not touch the `/tmp/mozilla` of whoever is not a tenant of
    #   this net») stays written in one place only.
    remainders = [c8a.clear_out_slot_shared(b)
             for b in (a.base_user, "c8u")]

    stays = wire_time_left(a.wait_stage, a.wait_browser, a.wire_margin)
    print("== C8b — and the same page is seen FROM THE CLIENT ==")
    print("   %d tenants · port %d · page %s"
          % (a.how_many, a.port, os.path.basename(a.page_v)))
    print("   terrain: /etc/skel/.cache -> %s  (the configuration of the "
          "real machine)" % (dove or "⛔ I COULD NOT PUT IT THERE"))
    print("   provisioning cure: %s"
          % ("⛔ NOT APPLIED (grafted fault: the second MUST give red)"
             if a.no_fix else "applied, as src/provisiona.sh"))
    print("   yardstick (from C8a): colour %s ±%d, at least %.0f%% of the screen"
          % (c8a.COLOR, c8a.TOLERANCE, lowest * 100))
    print("   image judge: %s" % judge_path)
    print("   birth judge: C1 (and the stage ceiling is its own)")
    print("   ceilings: stage %.0f s · browser %.0f s · breath %.0f s ⇒ the wire "
          "stays attached %.0f s per tenant"
          % (a.wait_stage, a.wait_browser, a.respite, stays))
    for r in remainders:
        if r:
            print("   %s" % r)
    if not dove:
        print("⛔ I could not prepare the skeleton: the terrain does not hold")
        sys.exit(2)
    print()

    outcomes = []
    for n in range(1, a.how_many + 1):
        chi = "%s%d" % (a.base_user, n)
        finished, reason_text = c8a.create(chi, a.password)
        if not finished:
            print("  %-7s  ?   I could not create it: %s" % (chi, reason_text))
            outcomes.append({"chi": chi, "seen_v": None, "after": None,
                          "reason_text": "not created"})
            continue
        if not a.no_fix:
            c8a.apply_fix(chi)
        writes = c8a.can_write_cache(chi)

        r = look_tenant(chi, a, c8a, c1, assessor)
        state, said = judge_before(r["verdetto_prima"], r["before"], lowest)
        if r["before"] is None and r["verdetto_prima"] is None:
            said = r["reason_text"] or said
        seen_v, motivo = tenant_judgment(state, r["after"], lowest)

        print("  %-7s  %-3s  %s"
              % (chi, "YES" if seen_v else ("NO" if seen_v is False else "?"),
                 motivo))
        print("           before: %s" % said)
        print("           wire: %s frames · stage at %s · can write in "
              "~/.cache/mozilla: %s"
              % ("unknown" if r["frames"] is None else r["frames"],
                 "unknown" if r["palco_s"] is None else "%.0f s" % r["palco_s"],
                 "yes" if writes else "⛔ NO"))
        # ⭐ The reason next to the symptom: «it is not seen» hides two different
        #   faults, and the recording can say which.
        if seen_v is False and os.path.exists(
                os.path.join(a.work, "%s.264" % chi)):
            print("           %s" % search_whole_recording(
                c8a, os.path.join(a.work, "%s.264" % chi), a.work, chi,
                lowest))

        outcomes.append({"chi": chi, "seen_v": seen_v, "after": r["after"],
                      "before": r["before"],
                      "reason_text": motivo if seen_v is not None else said})
        c8a.sh("pkill -KILL -u %s 2>/dev/null; loginctl terminate-user %s "
               "2>/dev/null" % (chi, chi))
        # ⛔ And we wait for it to be REALLY gone: `[M]` in C1, without this
        #    wait the rounds alternated «I do not know» / red, because the next
        #    round started on a field still occupied.
        expiry = time.time() + a.wait_clearout
        free_slot = False
        while time.time() < expiry:
            viva = subprocess.run(["loginctl", "show-user", chi],
                                  capture_output=True).returncode == 0
            proc = subprocess.run(["pgrep", "-u", chi],
                                  capture_output=True).returncode == 0
            if not viva and not proc:
                free_slot = True
                break
            time.sleep(0.5)
        if not free_slot:
            print("           ⚠ «%s» did not go away in %.0f s: the next one "
                  "does NOT start from a free field" % (chi, a.wait_clearout))

    # ⛔⛔ AND NOW ONE'S OWN IS CLEARED — «whoever opens, closes» (`LEZIONI.md`
    #    §9-ter), and here it is not good manners: it is correctness.
    #    ⚠ `/tmp/mozilla` stays with `c8bu1`, mode 0700.  ⭐ C8a removes it only if
    #      it belongs to a «c8u*» — its prefix — ⇒ if this mesh ran BEFORE
    #      it, the FIRST tenant of C8a would fail like the second, and C8a
    #      would say «the FIRST failed too»: ⛔ a red left as an inheritance
    #      by one bench to another, which is §1.26 in small.
    finale = c8a.clear_out_slot_shared(a.base_user)
    if finale:
        print("  %s" % finale)

    print()
    code_v, motivo, line_list = decide(outcomes, a.no_fix, lowest)
    for r in line_list:
        print(r)
    # ⭐ The reason is printed next to the number: an outcome without the reason that
    #   produced it is a number that nobody can reread at the next round.
    print("  (outcome %d · reason «%s»)" % (code_v, motivo))
    return code_v


if __name__ == "__main__":
    sys.exit(main())
