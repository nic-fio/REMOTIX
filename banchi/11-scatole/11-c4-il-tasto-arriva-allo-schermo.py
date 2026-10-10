#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c4 — ⭐⭐ «THE KEY ARRIVES ALL THE WAY TO THE SCREEN»
===========================================================================

    python3 11-c4-il-tasto-arriva-allo-schermo.py
    python3 11-c4-il-tasto-arriva-allo-schermo.py --senza-tasto
    python3 11-c4-il-tasto-arriva-allo-schermo.py --scena-sorda
    python3 11-c4-il-tasto-arriva-allo-schermo.py --certifica

`fasi/11-la-rete-di-sicurezza.md` §4.1, line **C4**:

  | what must be true         | the key arrives **all the way to the screen**|
  | where it starts from      | new session                                  |
  | what it looks at          | ⛔ **the pixel, before and after**: image ·   |
  |                           | key · image, and the pixels **of the expected|
  |                           | zone** must change                           |
  | how I know it can say red | the input path is cut ⇒ red                  |

---------------------------------------------------------------------------
⭐⭐ THE WORD THAT MATTERS IS «ALL THE WAY TO THE SCREEN»
---------------------------------------------------------------------------

⛔ It is not enough that the product says it sent the key.
⛔ It is not enough that the compositor says it received it.
⛔ It is not enough to count the `id`s of the inputs, nor to read the `input` field of the
   frames (§6.2): that says *«I injected it»*, which is another sentence.

⇒ ⭐ **A pixel must change.**  An input path that ends in nothing —
  the key leaves, travels, gets injected, and nothing happens on the screen —
  is exactly the fault that **no count catches**, and it is the same
  shape as the three faults that opened this phase (§0.3: *«the
  process was counted instead of looking at the pixel; the count said 1 with the window and
  without»*).

---------------------------------------------------------------------------
⚠⚠ AND THE SECOND WORD IS «OF THE EXPECTED ZONE»
---------------------------------------------------------------------------

⛔ Looking at the **whole** image is no use: a clock in a corner that advances
   by itself says *«something changed»* without any key having arrived
   anywhere.  ⇒ A bench like that would be **green by construction** on GNOME,
   where the top bar carries the clock and never goes off (`[M]` 25 August
   2026, measured by `10-f1-testimone.py`: a *whole* black desktop gives the same
   0.00121 of lit pixels **only because of the bar**).

⇒ ⭐ **The zone is declared, and we look ONLY inside it.**

    THE EXPECTED ZONE: the **central rectangle** of the image — from 35 % to
                       65 % of the width and of the height, i.e. **9 %**
                       of the screen, exactly in the middle.
    THE WITNESS ZONE : the **outer frame** — everything that lies **outside** the
                       12..88 % rectangle.  There nothing must change, and it is
                       exactly where bars, trays and clocks live.

    ⭐ WHY EXACTLY THAT ONE, and there are three reasons, not one:

      1. ⛔ **It is the only part of the screen that no desktop can occupy
         with its own stuff.**  Bars, trays, hot corners, window
         decorations and clocks sit **at the edges** — on all four desktops
         of this phase.  ⇒ The zone is chosen to be **blind to the desktop**
         (§3.7), and not because «usually there is nothing there».
      2. ⭐ The scene this mesh carries with it paints a target that
         occupies the central **60 %** of the screen (from 20 % to 80 %).  ⇒ The
         expected zone sits inside it with **a margin of 15 % of the width per
         side**: the page can slip by a whole GNOME bar without
         the zone leaving the target.
      3. ⚠ And it is **small**: 9 % of the screen.  ⇒ A change that fills
         the zone and leaves the rest still **cannot** be «everything changed»,
         and the mesh can tell them apart (third check, below).

---------------------------------------------------------------------------
⭐ THE SCENE — chosen, declared, and ⛔ DETERMINISTIC
---------------------------------------------------------------------------

Something is needed that, **on receiving a key**, changes a pixel in a
**predictable** place.  ⇒ The scene is a **page** the mesh writes by itself in the
tenant's home and opens in the browser full screen (`--kiosk`):

    · the background is of a fixed colour;
    · in the middle there is a **square target**, from 20 % to 80 % of the screen,
      painted in the STARTING COLOUR;
    · at the **first key that reaches the page** the target turns the
      ARRIVAL COLOUR, and stays so.

⛔ **AND THERE IS NOTHING ELSE.**  No clock, no animation, no
   `setTimeout`, no images loading, no font to download.
   ⇒ If the scene could change by itself, the mesh would no longer judge
   anything — it would say «changed» and would not know whose fault it was.

⭐ **AND THE SCENE WAS MEASURED, not imagined.**  `[M]` 27 August 2026, **on the
  laptop**, headless Firefox at **1920x1080** rendering the real page:

    the scene, before the key : zone 100 % of the starting colour, arrival 0 %
    the scene, after the key  : zone 0 % starting, **100 % arrival**
    the witness zone          : **0 %** changed, in both rounds
    the DEAF scene, with key  : zone still 100 % starting ⇒ RED, and
                                `guasto_visto` = **true**
    the «before» for `10-f1`  : **«drawn»** — neither black nor solid colour

  ⛔ And the limit of this measurement is declared: it is **the browser rendering the
     page**, not the key going through the product.  ⇒ It says that the scene and the
     zone are well chosen; ⚠ it says **nothing** about the input path, which
     is what the real round must measure inside the box.

⭐⭐ **AND THE SCENE IS NOT A SEPARATE FILE: THIS PROGRAM WRITES IT.**
   ⛔ The colour the page paints and the colour the judge looks for are **the
   same Python constant**, written once only below and slipped into the
   `<style>`.  ⇒ They cannot diverge: it is the same reason why the image judge
   **is imported and not rewritten** (`10-f1-testimone.py`).
   ⚠ And so the scene is **new at every round**, which is the half of «from zero» that
     always gets forgotten (`LEZIONI.md` §1.39, and C1 with its `userdel` before the
     `useradd`).

---------------------------------------------------------------------------
⭐⭐⭐ THE THREE POOR CHECKS — §4.3, and nobody knows what a desktop looks like
---------------------------------------------------------------------------

  1. ⭐ **BEFORE: the scene is in force.**  In the expected zone there must be the
     STARTING COLOUR, with a **declared tolerance** (§4.3, Gemini's finding
     accepted: compositors apply colour profiles, and the chain
     goes through an H.264 encoding in 4:2:0 that subsamples precisely the chroma).
     ⛔ If it is not there, the outcome is **3 — I could not look**, and ⛔ it is NOT a
     red: a desktop on which the scene never appeared does not testify about the
     key.  ⚠ It is the same rule with which C8 refuses to accuse the browser of
     a black desktop.

     ⛔⛔ And the twin check, which is worth even more: **the zone must NOT already be
        the arrival colour**.  If it were, the mesh would say green forever
        without any key ever arriving — *a predicate that cannot
        fail*, `LEZIONI.md` §1.44.

  2. ⭐ **AFTER: the zone is the ARRIVAL COLOUR.**  Not «it changed»: it is
     **that** colour.  ⛔ A zone that turned black (the window closed) has
     changed perfectly well, and it does not mean the key arrived.

  3. ⭐ **THE CHANGE IS CONCENTRATED, AND OUTSIDE IS STILL.**  The pixels
     that deviate between the two images are counted, **inside** the expected zone and in the
     **witness zone**.  Inside a lot must change; in the witness almost
     nothing.  ⚠ If the witness moves, the scene is moving by itself ⇒
     **3**, not green: the change in the zone can no longer be attributed to the
     key.  ⛔ It is the check the clock in the corner does not pass.

     ⛔⛔ **AND THE WITNESS ZONE IS NOT «ALL THE REST OF THE IMAGE»** — this
        cost the first draft, and `--certifica` caught it before
        any real round.  The target of the scene occupies 20..80 % of the
        screen, i.e. **36 %**; the expected zone looks at **9**.  ⇒ When the
        key arrives, the **27 percentage points** of target that lie outside
        the zone change too, ⛔ and an «all the rest» would have seen
        30 % of the screen change **at every successful round**: the mesh
        would have said *«I do not know»* forever (`LEZIONI.md` §1.49).

     ⇒ ⭐ **The witness zone is the OUTER FRAME**: everything outside
       the 12..88 % rectangle.  It never touches the target (margin of 8 %,
       i.e. 86 rows out of 1080: two GNOME bars), and it is exactly where
       bars, trays and clocks live.
     ⚠ **And the band in between — from 12 % to 35 % and from 65 % to 88 % — is NOT
       judged at all**, and that is declared: it is the margin that absorbs the bars,
       the decorations and the slipping of the page.  ⛔ A bench that
       judged that too would be red at the first desktop with a wider
       bar — i.e. at phase 12, which is what this phase exists to avoid.

---------------------------------------------------------------------------
⭐⭐ WHY THE CLIENT STAYS ATTACHED FOR THE WHOLE ROUND — and it is not convenience
---------------------------------------------------------------------------

`[M]` measured on the night of 26-27 August 2026: the `wl_output` of a headless
session **is born only when a PipeWire consumer hooks onto the stream**,
and never before.  ⇒ ⛔ **The screen exists only while our client is
attached.**

⇒ That is why this mesh opens **a single connection** and does everything inside it:
the stage, the scene, the BEFORE image, the key, the AFTER image.  ⛔ Detaching
in the middle to re-attach later would mean making the screen disappear between the two
photographs, and comparing two images of two different worlds.

⭐ And it attaches **BEFORE** claiming to see anything, never after.

---------------------------------------------------------------------------
⭐ HOW A KEY IS REALLY SENT — the part where it is easy to go wrong
---------------------------------------------------------------------------

⛔ We do **NOT** go through `org.gnome.Mutter.RemoteDesktop` (which is what
   `banchi/09-b72-tasto.py` does): that is **GNOME**'s door, and a mesh that
   used it would test the compositor instead of the product, ⛔ and would stay silent on the
   other three desktops — i.e. exactly the defect this phase exists to
   not introduce.

⭐ We go **through the product**, on the input channel of `RCP.md` §7.3:

    LETTERA          `0x0104`  + u32 Unicode character      (the measured key)
    POSIZIONE_TASTO  `0x0105`  + u16 evdev code · u8 pressed

  · the input channel is **one only**, unidirectional, opened after `SESSIONE` and
    **kept open** (§2.5);
  · the `id` grows by at least one **over the whole channel**, and `0` is reserved;
  · the codes are those of **evdev**, because `libei` works in evdev.

⛔⛔ AND THE TEST CLIENT CANNOT SEND KEYS: `01-b3-cliente.py` sends
   `PUNTATORE` and nothing else (`manda_puntatore`, §7.3).  ⇒ This mesh **imports** the
   client and adds to it the two missing messages — ⭐ **imports**, does not
   copy: the framing, the types, the QUIC/WebTransport handshake, the
   collection of frames from the wire stay **its own**, and the day
   the protocol changes they change in one place only.
   ⚠ And the debt that remains must be stated: the attach **sequence** (CIAO →
     CREDENZIALI → ATTACCA → SESSIONE) is copied, because the client's `principale()`
     is a single piece governed by `argparse` and cannot be called
     halfway.  ⛔ If that sequence changes, this mesh must be updated by hand.

---------------------------------------------------------------------------
⚠ THE WAKE-UP — why a key is sent BEFORE opening the scene
---------------------------------------------------------------------------

`[M]` 23 August 2026, `banchi/09-b72-tasto.py`: **a headless GNOME session
stays in the overview** (the Overview) until someone presses a key
inside, and there the windows are not windows — they are **shrunken previews** in
the middle of the screen.  ⇒ A scene opened in there would not fill the expected
zone, and the mesh would say **3** forever (`LEZIONI.md` §1.49: *an outcome that
cannot be made green is worse than no mesh*).

⇒ ⭐ An ESC is sent **before opening the browser**, and the order is the only thing
  that matters: the scene does not exist yet, so the wake-up **cannot** paint
  the target.  ⛔ Sending it afterwards would mean arriving at the «before» with the zone
  already the arrival colour — i.e. triggering by ourselves the predicate that cannot
  fail.

⭐ And the wake-up pays for itself: if the scene then appears full screen, that
  is **also** the proof that we left the overview.
⚠ `--senza-sveglia` removes it, and it is the road to take if one day the
  wake-up became useless: ⛔ a gesture is not kept because «it does no harm».

---------------------------------------------------------------------------
⛔ HOW I KNOW IT CAN SAY RED — two grafted faults, and they bracket the path
---------------------------------------------------------------------------

  `--senza-tasto`   ⛔ **the input path is cut at the HEAD**: everything is
                    done — new session, client attached, scene in force,
                    before image, wait, after image — **except sending the
                    key**.  ⇒ Nothing enters the product.
                    ⭐ What it proves: that the verdict **depends on the key**, and
                    that the scene **does not change by itself**.  If C4 said green
                    here, it would be looking at something else (encoder noise,
                    a window opening, a clock) — and it could not be
                    trusted.

  `--scena-sorda`   ⛔ **the path is cut at the TAIL**: the scene is written
                    **without the keyboard handler**.  ⇒ The key goes through the
                    product entirely, gets injected into the compositor, arrives
                    at the browser — ⛔ and paints nothing.
                    ⭐ What it proves: that C4's red is decided by **the pixel**,
                    and not by the fact of having sent a key.

⚠⚠ AND WHAT NEITHER OF THE TWO PROVES, declared instead of kept quiet:
   ⛔ **they do not cut the path in the MIDDLE** — between the product and the compositor,
   i.e. the EIS channel of `src/input.c`.  `[?]` A fault there today cannot be
   grafted without touching `src/` or restarting the server inside the box, and
   restarting the server while other meshes are measuring is forbidden.  ⇒ It is written
   here instead of being passed off as done, and it is among the things to calibrate on the real thing.

⭐⭐ AND THE FAULT IS READ ON THE **DIFFERENCE**, NOT ON THE COLOUR OF THE VERDICT
   — `LEZIONI.md` §1.52.  «Red ⇒ the fault was seen» would be a predicate
   that cannot fail: C4 could be red on its own (the window
   closed, the browser died), and the net would certify itself on a fault of the
   product instead of on its own.  ⇒ **Three** things are demanded together:

     · the verdict is red, **and**
     · the zone is **still** the starting colour (⛔ not black, not gone), **and**
     · inside the zone almost nothing changed (≤ 5 %), against the ≥ 60 % that
       is demanded when the key arrives.  ⭐ **A factor of twelve**, and it is
       written in the constants below.

---------------------------------------------------------------------------
⛔ WHAT C4 DOES **NOT** LOOK AT — or someone will trust it too much
---------------------------------------------------------------------------

  · ⛔ **it does not look at WHICH key arrives.**  The scene lights up at the **first key
    whatsoever**: C4's question is *«does the key arrive all the way to the screen»*, not
    *«does the right letter arrive»*.  ⚠ The keyboard layout, accents,
    modifiers, `LETTERA` against `POSIZIONE_TASTO` are another question, and
    a mesh that mixed them would give red without saying for what.
  · ⛔ **it does not measure the LATENCY** of the key: it says it arrives, not how long it takes.
  · ⛔ **it does not look at the mouse**, nor the wheel, nor the clipboard.  A fault that
    hit **only** the pointer, C4 would not see.
  · ⛔ **it is not an intermittency test**: it opens **one** session, not ten.
    ⇒ If input became sporadic, it is another round that catches it — and C1 is
    the example of how to count.
  · ⛔ **it does not prove that the desktop is healthy**: it looks at 9 % of the screen, and on it
    there is a page of ours.  ⇒ C4 green does not mean «the session is fine».
  · ⚠ **it does not separate the browser from the product**: if the browser does not start, C4 says
    **3**, not red — and it is C8 that is the mesh judging the browser.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ I looked: the key arrived all the way to the screen
  1  I looked: the expected zone did NOT change           ⇒ red
  3  ⛔ I could not look (no frame, scene never appeared, images
     unreadable, the scene moves by itself) — ⛔ and it is NOT a red
  2  the terrain does not hold, or the usage is wrong
  4  the turn never came

⛔ And with the grafted fault the outcome is read **BACKWARDS**: `0` = the fault was
   **seen**.  It is the convention of `11-gancio.sh` (`esegui_maglia`), which
   writes in the log the **fact** — `ha_visto_il_guasto` — and not the raw
   outcome.  ⛔ Exiting with the raw verdict would make it write «not seen» precisely in the
   round in which the fault was seen perfectly well (`LEZIONI.md` §1.52).
===========================================================================
"""
import argparse
import asyncio
import importlib.util
import os
import re
import struct
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ C1 IS THE HOME OF THE TWO STEPS COMMON TO ALL NINE MESHES — §1.47
#
# ⛔ It is not convenience: a line repeated in nine files is **nine places to
#    diverge from**, and they had already diverged.  From `11-c1-nasce-e-si-vede.py`:
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


def _carica_c1():
    """⛔ It is a LOADER, not a judge: it finds the file, it decides nothing.

    ⚠ It is looked for next to me (in the box everything is in `/opt/remotix`) and one
      level up, because in the repository this mesh sits in
      `banchi/11-scatole/`.
    """
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, "11-c1-nasce-e-si-vede.py")
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location("c1_comune", perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        # ⛔ We VERIFY that what is needed is there, we do not trust the name of the
        #    file (`CODER.md` §3.9).
        for mestiere in _MESTIERI_C1:
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_di_c1():
    global _C1
    if _C1 is None:
        _C1 = _carica_c1()
    if _C1 is None:
        print("⛔ I cannot find `11-c1-nasce-e-si-vede.py` next to me, and from there")
        print("   come the admission predicate and the guarantee of the")
        print("   card's groups — which live in one place only (§1.47).")
        print("⇒ I could not look — ⛔ and it is NOT a red (§4.5).")
        sys.exit(3)
    return _C1


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐⭐ THE SHARED PROVISIONING — `/tmp/mozilla`, and it lives in ONE PLACE ONLY
#
# `[M]` 27 August 2026, round `--famiglia tutto` on all four boxes,
#   binary `aa950804fed7`: C4 ⛔ **3** — «the zone is the starting colour
#   only for 0%».  ⚠ And the judged image said something else entirely: the GNOME
#   session was **alive and painted**, ⛔ but Firefox was stuck on the **profile
#   chooser window**, so the keyboard scene was never born.
#
# ⇒ THE CAUSE: `/home/c4u1/.cache/mozilla` -> `/tmp/mozilla`, which had stayed with
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
# ⛔ The code lives in C2 and ⛔ no copy of it is made here (§1.47).  ⚠ It lives in C2 and
#    not in C8 because C8 cannot be modified today; ⭐ the day it can, it
#    moves next to `applica_la_cura`.
# ═══════════════════════════════════════════════════════════════════════════
_MESTIERI_PROVVISTA = ("cura_della_provvista", "sgombra_il_mio_rimasuglio",
                       "certifica_la_provvista")
_PROVVISTA = None


def _carica_provvista():
    """⛔ It is a LOADER, not a judge: it finds the file, it decides nothing."""
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, "11-c2-una-finestra-si-apre.py")
        if not os.path.exists(perc):
            continue
        spec = importlib.util.spec_from_file_location("c2_provvista", perc)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        for mestiere in _MESTIERI_PROVVISTA:
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_della_provvista():
    global _PROVVISTA
    if _PROVVISTA is None:
        _PROVVISTA = _carica_provvista()
    return _PROVVISTA


def cura_della_provvista(chi):
    """⭐⭐ (done, why) — and ⛔ if it does not hold it is NOT a red."""
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


def e_stato_ammesso(coda):
    """⭐ `True` admitted · `False` **TURNED AWAY** · `None` said nothing.

    ⛔ `False` is not a product red: a client turned away is a client
       turned away, and the caller says «I could not look» (**3**).
    """
    return casa_di_c1().e_stato_ammesso(coda)


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
# ⛔ THE YARDSTICK — declared here, printed at every round, and certified by
#    `--certifica`.  A verdict without its yardstick is an opinion (§4.2).
# ═══════════════════════════════════════════════════════════════════════════

# The two colours of the scene.  ⭐ They are **a single constant** for the page and for the
# judge: `scena_html()` slips them into the `<style>`, `misura()` looks for them in the pixels.
#
# ⚠ Why these two and not any two:
#   · they are **saturated and very far apart** — the per-channel distance, in max
#     norm, is 255 of 255: no reasonable tolerance confuses them;
#   · ⛔ neither of the two resembles a desktop background.  It serves the check
#     «the scene is in force»: if the browser is not there, the zone will not be
#     this green for 60 % of its area, and the mesh will say so;
#   · magenta is **already measured** through this chain: it is the same as
#     C8, which finds it again after the H.264 encoding in 4:2:0 with ±48 (§7-bis.10).
COLORE_PARTENZA = (0x00, 0xC0, 0x60)     # bright green — before the key
COLORE_ARRIVO = (0xFF, 0x00, 0xFF)       # magenta — after the key
COLORE_FONDO = (0x18, 0x24, 0x30)        # the rest of the page, and it never changes

# ⛔ THE TOLERANCE IS NOT GENERIC PRUDENCE (§4.3, Gemini's finding accepted): the
#    compositors apply colour profiles and rescaling, the chain goes through
#    an H.264 encoding in **4:2:0** — which subsamples precisely the chroma, i.e.
#    the channel where the whole difference between magenta and non-magenta lies — and the
#    limited range (16..235) shifts every full scale by about twenty levels.
# ⇒ Demanding the exact colour would mean a mesh already dead.
# ⭐ And it is CALIBRATED, not chosen: `--certifica` contains the case «colour shifted
#   by as much as the tolerance allows ⇒ must stay GREEN» and its twin
#   «shifted too much ⇒ RED».  Without both, the tolerance separates nothing.
TOLLERANZA = 48                  # per channel, max norm, levels 0..255

# ⭐ THE EXPECTED ZONE, in fractions of the image.  The why is in the header.
ZONA = (0.35, 0.35, 0.65, 0.65)
# ⭐ The target the scene paints, in fractions of the screen: from 20 % to 80 %.
#    ⛔ `--certifica` verifies that the ZONE is **strictly inside** the
#    TARGET: two numbers written in two places that contradict each other would give
#    a mesh red forever without anything being broken.
BERSAGLIO = (0.20, 0.20, 0.80, 0.80)
# ⭐⭐ THE WITNESS ZONE: **everything that lies OUTSIDE this rectangle**, i.e.
#     the outer frame of the screen.  ⛔ It is NOT «all the rest of the image»:
#     the target changes all at once, and an «all the rest» would see
#     30 % of the screen change at every SUCCESSFUL round ⇒ «I do not know» forever
#     (`LEZIONI.md` §1.49).  ⇒ The margin between the target and the witness is
#     8 % of the screen — 86 rows out of 1080, two GNOME bars — and the band in
#     between is NOT judged, on purpose.
TESTIMONE = (0.12, 0.12, 0.88, 0.88)

# How much of the ZONE must be of a colour for us to say «it is that
# colour».  ⚠ 0.60 and not 0.95: the page may have slipped by a bar, and the
# encoding dirties the edges.  ⛔ And not 0.20: below half the zone it is no longer «the zone
# is that colour», it is «there is a spot».
FRAZIONE_COLORE = 0.60

# ⛔ When two pixels are considered «changed»: more than 40 levels on at least one
#    channel.  ⚠ It serves NOT to count the encoder's noise: between two
#    frames of a still scene the levels dance by a few points, and a bench
#    that counted them would always say «changed».
SOGLIA_CAMBIO = 40
CAMBIO_MINIMO_DENTRO = 0.60      # with the key: at least 60 % of the zone changes
CAMBIO_MASSIMO_TESTIMONE = 0.20  # beyond, the scene moves by itself ⇒ «I do not know»
CAMBIO_RESIDUO = 0.05            # ⭐ without the key: inside no more than this changes

# ⭐ The measured key.  §7.3: `LETTERA` carries a Unicode scalar value.
LETTERA = 0x0061                 # «a»
T_LETTERA = 0x0104
T_POSIZIONE_TASTO = 0x0105
ESC_EVDEV = 1                    # `linux/input-event-codes.h`, KEY_ESC

# ⭐⭐ THE STAGE DELAY — ⛔ it is a MEASUREMENT, not a round number (§1.45).
#     `[M]` 27 August 2026, inside the **gnome** box, three real sessions
#     (C1, `RITARDO_PALCO`): gu1 98.0 s · gu2 101.0 s · gu3 95.5 s ⇒ maximum
#     **101.0 s**, and the declared margin is half: 101.0 × 1.5 = **152 s**.
#     ⚠ On the other boxes they are ~2 s: this ceiling is wide **for GNOME**.
#
# ⛔⛔ AND EVERY WAIT HAS ITS OWN NAME AND ITS OWN VALUE — `LEZIONI.md` §1.45.  Here there
#     are five, and they are five because they wait for five different things:
#
#       ATTESA_SESSIONE    the `SESSIONE` reply           `[?]` 30 s, prudent
#       ATTESA_PALCO       for the stage to BE BORN       `[M]` 152 s — C1, above
#       ATTESA_PRIMO_FOTO  for the encoder to deliver     `[?]` 30 s, to calibrate
#       ATTESA_SCENA       for the page to appear         `[?]` 90 s, to calibrate
#       ATTESA_TASTO       for the pixel to change        `[?]` 8 s, to calibrate
#
#     ⚠ The first frame is waited for **ATTESA_PALCO + ATTESA_PRIMO_FOTO**: they are
#       two phenomena in a row (first the stage is born, then the encoder delivers),
#       and adding them is the only way not to lend the ceiling of one to the other.
#       ⛔ A single ceiling, as short as the second, would look **always in the
#       wrong window** on GNOME — and it is exactly the defect C1
#       paid for with ten «I do not know» out of ten.
#     ⇒ The four `[?]` are **prudent** and must be measured at the first real round:
#       they are written as such in the report, and ⛔ they are not passed off as measurements.
ATTESA_SESSIONE = 30.0
ATTESA_PALCO = 152.0
ATTESA_PRIMO_FOTOGRAMMA = 30.0
ATTESA_SCENA = 90.0
ATTESA_TASTO = 8.0

# ⚠ The default port is **gnome**'s (8511); the hook passes the one
#   of the box.  ⛔ C4 wants the image AND the input: today (21 Sep 2026) the
#   product gives them on gnome and kde (`11-capacita-del-prodotto.sh`); on xfce
#   the input is increment 3 of phase 13, on lxqt the product is not born.
#   There, launched by hand, C4 will give **3**, and that will be right — not a red.
PORTA_PREDEFINITA = 8511


# ═══════════════════════════════════════════════════════════════════════════
# THE SCENE — ⭐ this program writes it, with the colours above
# ═══════════════════════════════════════════════════════════════════════════
def _esa(c):
    return "#%02X%02X%02X" % c


def scena_html(sorda=False):
    """The target page.  ⛔ `sorda=True` is the tail grafted fault.

    ⚠ The rules this page follows, and that `--certifica` checks again:
      · ⛔ **nothing that changes by itself**: no `setTimeout`, no
        animation, no transition, no external resource to download.
        A scene that moves by itself takes away from the mesh the possibility of
        attributing the change to the key.
      · the target is declared **as a percentage of the frame**, not in pixels:
        so the same page holds for any canvas size.
      · ⭐ it lights up at the **first key whatsoever**, and stays so.  C4 does not ask
        *which* key (see «what C4 does not look at»).
    """
    ascolto = "" if sorda else """
 window.addEventListener('keydown', function () {
   document.getElementById('bersaglio').style.background = '%s';
 }, true);""" % _esa(COLORE_ARRIVO)
    return """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<title>C4 — the key arrives at the screen</title>
<style>
 html, body { margin:0; padding:0; width:100%%; height:100%%;
              background:%(fondo)s; overflow:hidden; }
 #bersaglio { position:absolute; left:%(bx)s%%; top:%(by)s%%;
              width:%(bw)s%%; height:%(bh)s%%; background:%(partenza)s; }
</style></head>
<body><div id="bersaglio"></div>
<script>%(ascolto)s
</script></body></html>
""" % {"fondo": _esa(COLORE_FONDO),
       "partenza": _esa(COLORE_PARTENZA),
       "bx": "%g" % round(BERSAGLIO[0] * 100, 4),
       "by": "%g" % round(BERSAGLIO[1] * 100, 4),
       "bw": "%g" % round((BERSAGLIO[2] - BERSAGLIO[0]) * 100, 4),
       "bh": "%g" % round((BERSAGLIO[3] - BERSAGLIO[1]) * 100, 4),
       "ascolto": ascolto}


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE PIXEL JUDGE — «two PNGs» is not «the key arrived»
# ═══════════════════════════════════════════════════════════════════════════
def _numpy_o_niente():
    try:
        import numpy
        return numpy
    except ImportError:
        return None


def _carica(percorso):
    """A PNG as an int16 array, or ⛔ `None` if I could not look.

    ⛔ `None` is not «black» and is not «zero»: a file that is not there, an empty file, a
       truncated PNG, `numpy`/`Pillow` missing are all *«I did not look»*, and
       this project has already paid for confusing them with a judgement.
    """
    if not percorso or not os.path.exists(percorso) \
            or os.path.getsize(percorso) == 0:
        return None
    np = _numpy_o_niente()
    if np is None:
        return None
    try:
        from PIL import Image
        img = np.asarray(Image.open(percorso).convert("RGB")).astype("int16")
    except Exception:
        return None
    if img.ndim != 3 or img.shape[2] != 3 or img.size == 0:
        return None
    return img


def taglia(img, zona=ZONA):
    """The rectangle of the expected zone.  ⛔ `None` if it does not fit."""
    h, w = img.shape[0], img.shape[1]
    x0, y0 = int(round(zona[0] * w)), int(round(zona[1] * h))
    x1, y1 = int(round(zona[2] * w)), int(round(zona[3] * h))
    if x1 - x0 < 2 or y1 - y0 < 2:
        return None, None
    return img[y0:y1, x0:x1], (x0, y0, x1, y1)


def frazione_del_colore(pezzo, colore, tolleranza=TOLLERANZA):
    """How much of `pezzo` is of that colour, within the tolerance.

    ⚠ The distance is taken **channel by channel** (max norm) and not as a
      sum: a sum would let through a colour very wrong on a single channel,
      provided it is right on the other two — and between magenta and green the
      difference lies entirely in one channel at a time.
    """
    np = _numpy_o_niente()
    scarto = np.abs(pezzo - np.array(colore, dtype="int16")).max(axis=2)
    return float((scarto <= tolleranza).mean())


def frazione_cambiata(a, b, soglia=SOGLIA_CAMBIO):
    """How many pixels deviate by more than `soglia` on at least one channel."""
    np = _numpy_o_niente()
    return float((np.abs(a - b).max(axis=2) > soglia).mean())


def misura(png_prima, png_dopo, zona=ZONA):
    """The six quantities on which the whole judgement rests.

    ⛔ Returns `None` — «I could not look» — if one of the two images cannot
       be read, or ⚠ **if the two have different sizes**: two
       images of different canvas are not compared, and pretending to do so
       would produce a number that means nothing.
    """
    a = _carica(png_prima)
    b = _carica(png_dopo)
    if a is None or b is None:
        return None
    if a.shape != b.shape:
        return None
    za, box = taglia(a, zona)
    zb, _ = taglia(b, zona)
    if za is None or zb is None:
        return None
    _, cornice = taglia(a, TESTIMONE)
    if cornice is None:
        return None
    np = _numpy_o_niente()
    # ⭐ The two masks, and ⛔ **they are not the complement of each other**: the
    #   band in between (from 12 % to 35 % and from 65 % to 88 %) is in
    #   neither of the two, and it is not judged.  It is the declared margin that
    #   absorbs bars, decorations and slipping of the page.
    dentro = np.zeros(a.shape[:2], dtype=bool)
    dentro[box[1]:box[3], box[0]:box[2]] = True
    testimone = np.ones(a.shape[:2], dtype=bool)
    testimone[cornice[1]:cornice[3], cornice[0]:cornice[2]] = False
    diff = np.abs(a - b).max(axis=2) > SOGLIA_CAMBIO
    return {
        "larghezza": int(a.shape[1]), "altezza": int(a.shape[0]),
        "zona": box, "cornice": cornice,
        "prima_partenza": frazione_del_colore(za, COLORE_PARTENZA),
        "prima_arrivo": frazione_del_colore(za, COLORE_ARRIVO),
        "dopo_partenza": frazione_del_colore(zb, COLORE_PARTENZA),
        "dopo_arrivo": frazione_del_colore(zb, COLORE_ARRIVO),
        "dentro": float(diff[dentro].mean()),
        "testimone": (float(diff[testimone].mean())
                      if int(testimone.sum()) else 0.0),
    }


def giudica(m):
    """⭐ The verdict, and its reason in one line.

    Returns `(verdetto, motivo)` with `verdetto` among:
        True   the key arrived all the way to the screen
        False  ⛔ RED: the expected zone did not change as it should
        None   ⛔ I could not look — and it is NOT a red
    """
    if m is None:
        return None, "the images could not be read (or they have different sizes)"

    # ── 1. BEFORE: the scene is in force, and has not already arrived ──────
    #
    # ⛔⛔ This case is looked at FIRST, and it is the most important of all:
    #    if the zone were already the arrival colour, the «after» check
    #    would be green whatever happens — *a predicate that cannot
    #    fail*, `LEZIONI.md` §1.44.
    if m["prima_arrivo"] >= FRAZIONE_COLORE:
        return None, ("⛔ the zone was ALREADY the arrival colour BEFORE the key "
                      "(%.0f %%): the scene does not start from the starting colour, and "
                      "a green «after» would prove nothing"
                      % (100 * m["prima_arrivo"]))
    if m["prima_partenza"] < FRAZIONE_COLORE:
        return None, ("⛔ the scene is NOT in force before the key: in the zone "
                      "the starting colour is there only for %.0f %% (%.0f %% is "
                      "needed) — the page did not appear, or does not cover the "
                      "screen.  ⚠ It is not a red of C4: it is a desktop that does not "
                      "testify" % (100 * m["prima_partenza"],
                                   100 * FRAZIONE_COLORE))

    # ── 2. AFTER: the zone is the arrival colour, and 3. it changed ────────
    if m["dopo_arrivo"] < FRAZIONE_COLORE:
        return False, ("⛔ after the key the expected zone is NOT the arrival "
                       "colour: only %.0f %% (%.0f %% is needed)"
                       % (100 * m["dopo_arrivo"], 100 * FRAZIONE_COLORE))
    if m["dentro"] < CAMBIO_MINIMO_DENTRO:
        # ⚠ The colour is there but the pixels did not move: it is the case in which the
        #   «before» and the «after» are the same image.  ⛔ It must be said separately,
        #   because it is a defect of the BENCH more than of the product.
        return False, ("⛔ the zone is the arrival colour but only %.0f %% of "
                       "its pixels changed (%.0f %% is needed): the two "
                       "images are almost identical"
                       % (100 * m["dentro"], 100 * CAMBIO_MINIMO_DENTRO))

    # ── 3-bis. the change is CONCENTRATED in the zone ──────────────────────
    #
    # ⭐ It is the check the clock in the corner does not pass — in reverse: here
    #   the zone **did** change right, but if the frame moved too, the
    #   credit cannot be attributed to the key.
    # ⚠ And it is an «I do not know», not a red: the product is not accused of a
    #   scene that moves by itself.
    if m["testimone"] > CAMBIO_MASSIMO_TESTIMONE:
        return None, ("⚠ the zone changed right, ⛔ but in the WITNESS ZONE "
                      "(the frame) %.0f %% changed (the ceiling is %.0f %%): "
                      "the scene moves by itself and the change cannot be "
                      "attributed to the key"
                      % (100 * m["testimone"], 100 * CAMBIO_MASSIMO_TESTIMONE))

    return True, ("⭐ the expected zone went from the starting colour to the "
                  "arrival one: %.0f %% of its pixels changed, and in the frame "
                  "only %.0f %%"
                  % (100 * m["dentro"], 100 * m["testimone"]))


def guasto_visto(verdetto, m):
    """⛔⛔ §1.52 — «the fault was seen» is NOT «the verdict is red».

    C4 can be red **on its own**: the browser died, the window
    closed, the canvas changed.  ⇒ A predicate that looked only at the colour
    of the verdict would say «seen» even if the injection had bitten nothing, and
    the net's certification would rest on a fault of the product.

    ⭐ A **measurable difference** is demanded, and they are two numbers:
      · the zone is **still** the starting colour (⛔ not black, not gone);
      · inside the zone at most `CAMBIO_RESIDUO` (5 %) changed, against the
        `CAMBIO_MINIMO_DENTRO` (60 %) that is demanded when the key really
        arrives.  ⭐ **A factor of twelve**, and it is written in the constants.
    """
    if verdetto is not False or m is None:
        return False
    return (m["dopo_partenza"] >= FRAZIONE_COLORE
            and m["dentro"] <= CAMBIO_RESIDUO)


def riga_misure(m):
    if m is None:
        return "unknown"
    return ("zone %d,%d..%d,%d on %dx%d · BEFORE starting %.0f %% arrival %.0f %% · "
            "AFTER starting %.0f %% arrival %.0f %% · changed: inside %.0f %%, "
            "witness %.0f %%"
            % (m["zona"][0], m["zona"][1], m["zona"][2], m["zona"][3],
               m["larghezza"], m["altezza"],
               100 * m["prima_partenza"], 100 * m["prima_arrivo"],
               100 * m["dopo_partenza"], 100 * m["dopo_arrivo"],
               100 * m["dentro"], 100 * m["testimone"]))


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE CERTIFICATION — it proves that the judge can say green, red and
#     «I do not know», and ⭐ that it can tell a fault that bit from one that did not
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⚠ And it declares what it covers and what it does not.

    COVERS: the **judge** — the zone, the two colours, the tolerance, the three
    poor checks, the reading of the grafted fault, and the consistency between the
    scene that is written and the colour that is looked for.
    ⛔ DOES NOT COVER: that the key really goes through the product.  That is said by
    the real round and its two grafted faults, on the box — and it is the other
    half of the acceptance test.  ⇒ A certification that declares itself wider than
    it is is worth less than no certification.
    """
    np = _numpy_o_niente()
    if np is None:
        print("⛔ numpy is missing: I cannot even certify myself")
        print("   ⇒ I could not look")
        return 3
    try:
        from PIL import Image
    except ImportError:
        print("⛔ Pillow is missing: I cannot even certify myself")
        print("   ⇒ I could not look")
        return 3
    import tempfile

    lav = tempfile.mkdtemp(prefix="c4cert-")
    L, A = 384, 216       # the same shape as a 16:9 screen, in small

    def dipingi(nome, bersaglio, fondo=COLORE_FONDO, macchia=None):
        """A fake screen: background + target at 20..80 % + a spot.

        ⚠ `macchia = (x0, y0, x1, y1, colore)` in fractions: it serves to put
          stuff **outside** the expected zone — i.e. the clock in the corner.
        """
        img = np.zeros((A, L, 3), dtype="uint8")
        img[:, :] = fondo
        bx0, by0 = int(BERSAGLIO[0] * L), int(BERSAGLIO[1] * A)
        bx1, by1 = int(BERSAGLIO[2] * L), int(BERSAGLIO[3] * A)
        img[by0:by1, bx0:bx1] = bersaglio
        if macchia is not None:
            x0, y0, x1, y1, c = macchia
            img[int(y0 * A):int(y1 * A), int(x0 * L):int(x1 * L)] = c
        p = os.path.join(lav, nome + ".png")
        Image.fromarray(img).save(p)
        return p

    guai = 0
    print("== certification of C4's judge ==")
    print("   expected zone %s (%.0f %% of the screen, in the middle)"
          % (ZONA, 100 * (ZONA[2] - ZONA[0]) * (ZONA[3] - ZONA[1])))
    print("   witness zone: everything OUTSIDE %s (the frame)" % (TESTIMONE,))
    print("   starting %s · arrival %s · tolerance ±%d per channel"
          % (_esa(COLORE_PARTENZA), _esa(COLORE_ARRIVO), TOLLERANZA))
    print("   %.0f %% of the zone must be the colour · changed: inside ≥ %.0f %%, "
          "witness ≤ %.0f %%"
          % (100 * FRAZIONE_COLORE, 100 * CAMBIO_MINIMO_DENTRO,
             100 * CAMBIO_MASSIMO_TESTIMONE))
    print()

    # ── PART 1 · THE VERDICT ───────────────────────────────────────────────
    verde = dipingi("v-prima", COLORE_PARTENZA)
    arrivato = dipingi("v-dopo", COLORE_ARRIVO)

    # ⭐ The colour shifted by **as much as the tolerance allows**: colour
    #    profiles, 4:2:0, limited range.  It must stay GREEN, or the threshold is
    #    too tight and the mesh gets thrown away in two weeks.
    spostato = tuple(min(255, max(0, c + s))
                     for c, s in zip(COLORE_ARRIVO, (-TOLLERANZA, +TOLLERANZA,
                                                     -TOLLERANZA)))
    # ⛔ And one shifted TOO MUCH must not pass, or the tolerance no longer separates
    #    anything: a colour admitted anyway is an infinite tolerance.
    troppo = tuple(min(255, max(0, c + s))
                   for c, s in zip(COLORE_ARRIVO, (0, +3 * TOLLERANZA, 0)))

    casi = [
        # name, png before, png after, expected verdict
        ("⭐ the key arrives: the zone goes from starting to arrival",
         verde, arrivato, True),

        ("⛔ no key: the two images are identical",
         verde, dipingi("r-dopo", COLORE_PARTENZA), False),

        # ⭐⭐⭐ THE CASE THAT MATTERS MOST (C4's mandate, and §4.3):
        #    something changes OUTSIDE the expected zone — a clock in a corner
        #    that advances — and inside nothing changes.  ⛔ It MUST be RED.
        ("⭐⭐ ONLY outside the zone changes (the clock in the corner) ⇒ RED",
         dipingi("o-prima", COLORE_PARTENZA,
                 macchia=(0.02, 0.02, 0.20, 0.09, (0, 0, 0))),
         dipingi("o-dopo", COLORE_PARTENZA,
                 macchia=(0.02, 0.02, 0.20, 0.09, (255, 255, 255))),
         False),

        ("⛔ the zone changes but to the WRONG colour (the window closed)",
         verde, dipingi("n-dopo", (0, 0, 0)), False),

        ("⭐ arrival colour shifted by ±%d ⇒ must be GREEN" % TOLLERANZA,
         verde, dipingi("t-dopo", spostato), True),

        ("⛔ arrival colour shifted by ±%d ⇒ must be RED" % (3 * TOLLERANZA),
         verde, dipingi("tt-dopo", troppo), False),

        # ⚠ The scene is not in force: any desktop, without the page.
        #   ⛔ It is an «I do not know», not a red: a desktop that does not testify is not
        #   a product that is wrong.
        ("⚠ the scene is not in force before the key ⇒ «I do not know»",
         dipingi("s-prima", (58, 62, 70), fondo=(58, 62, 70)),
         dipingi("s-dopo", COLORE_ARRIVO), None),

        # ⛔⛔ The predicate that cannot fail (§1.44): the zone is ALREADY the
        #    arrival colour before the key leaves.
        ("⛔⛔ the zone had ALREADY arrived BEFORE the key ⇒ «I do not know»",
         dipingi("g-prima", COLORE_ARRIVO), arrivato, None),

        # ⭐ The scene moves by itself: the zone changes right, but so does half the
        #   screen around it.  ⇒ «I do not know», not green.
        ("⭐ the zone is right but the frame moves too ⇒ «I do not know»",
         dipingi("m-prima", COLORE_PARTENZA),
         dipingi("m-dopo", COLORE_ARRIVO, fondo=(240, 240, 240)), None),

        # ⭐⭐ THE CASE THE FIRST DRAFT DID NOT PASS, and which corrected the
        #    design before any real round: the target changes **all of it
        #    at once** — which is what happens on the real thing — and the witness zone
        #    stays still.  ⛔ With an «outside» made of all-the-rest, this
        #    case gave «I do not know», i.e. the mesh would NEVER have turned
        #    green (`LEZIONI.md` §1.49).
        ("⭐⭐ the target changes ALL AT ONCE (the real case) ⇒ GREEN",
         dipingi("b-prima", COLORE_PARTENZA), dipingi("b-dopo", COLORE_ARRIVO),
         True),

        # ⚠ And a bar at the top that lights up: it is IN THE WITNESS, but it is small.
        #   ⛔ It must not spoil a green, or the mesh would break at the first
        #   desktop with a wider bar — i.e. at phase 12.
        ("⚠ a bar at the top lights up, and the key arrives ⇒ GREEN anyway",
         dipingi("br-prima", COLORE_PARTENZA,
                 macchia=(0.0, 0.0, 1.0, 0.04, (30, 30, 30))),
         dipingi("br-dopo", COLORE_ARRIVO,
                 macchia=(0.0, 0.0, 1.0, 0.04, (200, 200, 200))), True),
    ]

    for nome, pa, pb, atteso in casi:
        m = misura(pa, pb)
        v, perche = giudica(m)
        ok = (v is atteso)
        print("  %s  %-58s ⇒ %-11s (expected %s)"
              % ("OK " if ok else "NO ", nome,
                 {True: "GREEN", False: "RED", None: "unknown"}[v],
                 {True: "GREEN", False: "RED", None: "unknown"}[atteso]))
        if not ok:
            guai += 1
            print("        ⛔ %s" % perche)
            print("        %s" % riga_misure(m))

    # ── PART 2 · «I COULD NOT LOOK» must be `None`, not zero ───────────────
    print()
    print("  ⛔ and «I could not look» must be «I do not know», never a number:")
    vuoto = os.path.join(lav, "vuoto.png")
    open(vuoto, "wb").close()
    # ⚠ Two images of different size: they are not compared, and pretending to do so
    #   would produce a meaningless number.
    piccola = np.zeros((100, 100, 3), dtype="uint8")
    piccola[:, :] = COLORE_PARTENZA
    pic = os.path.join(lav, "piccola.png")
    Image.fromarray(piccola).save(pic)
    for nome, pa, pb in (("the «before» file is not there",
                          os.path.join(lav, "manca.png"), arrivato),
                         ("the «after» file is empty", verde, vuoto),
                         ("the two images have different sizes", pic, arrivato)):
        m = misura(pa, pb)
        v, _ = giudica(m)
        ok = (m is None and v is None)
        print("  %s  %-58s ⇒ %s"
              % ("OK " if ok else "NO ", nome,
                 "unknown" if ok else "⛔ it judged anyway"))
        if not ok:
            guai += 1

    # ── PART 3 · THE GRAFTED FAULT IS READ ON THE DIFFERENCE (§1.52) ──────
    print()
    print("  ⭐⭐ and «the fault was seen» is not «the verdict is red»:")
    casi_guasto = [
        ("⭐ without the key: the zone is STILL starting and does not change ⇒ SEEN",
         verde, dipingi("gv-dopo", COLORE_PARTENZA), True),
        # ⛔ Red, but for another reason: the window disappeared.  The injection
        #    bit nothing, and saying «seen» would be certifying the net on
        #    a fault of the product.
        ("⛔ red because the window disappeared ⇒ it is NOT the fault",
         verde, dipingi("gn-dopo", (0, 0, 0)), False),
        # ⛔ And green is never «the fault was seen».
        ("⛔ green ⇒ the fault was NOT seen", verde, arrivato, False),
        # ⛔ And neither is «I could not look» (§4.5, and the defect of the hook
        #    of 27 August: a `3` written as «it did not see it» is an accusation against
        #    a test that did not look).
        ("⛔ «I do not know» ⇒ the fault was NOT seen",
         dipingi("gi-prima", (58, 62, 70), fondo=(58, 62, 70)), arrivato, False),
    ]
    for nome, pa, pb, atteso in casi_guasto:
        m = misura(pa, pb)
        v, _ = giudica(m)
        avuto = guasto_visto(v, m)
        ok = (avuto == atteso)
        print("  %s  %-58s ⇒ %-9s (expected %s)"
              % ("OK " if ok else "NO ", nome,
                 "SEEN" if avuto else "not seen",
                 "SEEN" if atteso else "not seen"))
        if not ok:
            guai += 1

    # ── PART 4 · THE CONSTANTS ARE CERTIFIED LIKE A THRESHOLD ─────────────
    #
    # ⭐ `LEZIONI.md` §1.45 and the lesson of C1's ceiling: a number nobody
    #   checks any more is a number that one day will look in the wrong
    #   window.  Here the numbers are **geometric**, and they check themselves.
    print()
    print("  ⭐⭐ and the constants check each other, or they contradict each other silently:")
    controlli = [
        ("the ZONE sits STRICTLY inside the scene's TARGET",
         ZONA[0] > BERSAGLIO[0] and ZONA[1] > BERSAGLIO[1]
         and ZONA[2] < BERSAGLIO[2] and ZONA[3] < BERSAGLIO[3],
         "zone %s · target %s · margin %.0f %% per side"
         % (ZONA, BERSAGLIO, 100 * (ZONA[0] - BERSAGLIO[0]))),
        ("the two colours are further apart than the tolerance, by a lot",
         max(abs(a - b) for a, b in zip(COLORE_PARTENZA, COLORE_ARRIVO))
         > 3 * TOLLERANZA,
         "per-channel distance %d, tolerance %d"
         % (max(abs(a - b) for a, b in zip(COLORE_PARTENZA, COLORE_ARRIVO)),
            TOLLERANZA)),
        ("the «changes» with the key and «does not change» without are a factor ≥ 10 apart",
         CAMBIO_MINIMO_DENTRO >= 10 * CAMBIO_RESIDUO,
         "inside ≥ %.2f with the key · ≤ %.2f without ⇒ factor %.0f"
         % (CAMBIO_MINIMO_DENTRO, CAMBIO_RESIDUO,
            CAMBIO_MINIMO_DENTRO / CAMBIO_RESIDUO)),
        ("the witness ceiling is lower than the «inside» minimum",
         CAMBIO_MASSIMO_TESTIMONE < CAMBIO_MINIMO_DENTRO,
         "witness ≤ %.2f · inside ≥ %.2f"
         % (CAMBIO_MASSIMO_TESTIMONE, CAMBIO_MINIMO_DENTRO)),
        # ⭐⭐ The check that corrected the design: the WITNESS must not
        #    touch the TARGET, or it would see the scene change at every successful
        #    round and the mesh would never turn green (§1.49).
        ("the WITNESS ZONE NEVER touches the scene's target",
         TESTIMONE[0] < BERSAGLIO[0] and TESTIMONE[1] < BERSAGLIO[1]
         and TESTIMONE[2] > BERSAGLIO[2] and TESTIMONE[3] > BERSAGLIO[3],
         "witness outside %s · target %s · margin %.0f %% (%.0f rows of "
         "1080)" % (TESTIMONE, BERSAGLIO, 100 * (BERSAGLIO[0] - TESTIMONE[0]),
                    1080 * (BERSAGLIO[0] - TESTIMONE[0]))),
        ("and the margin holds two GNOME bars (40 rows each)",
         1080 * (BERSAGLIO[0] - TESTIMONE[0]) >= 80,
         "%.0f rows of margin" % (1080 * (BERSAGLIO[0] - TESTIMONE[0]))),
        # ⭐ The scene and the judge share the constant: it is verified on the text
        #   the program really writes, not on a promise.
        ("the scene paints EXACTLY the colours the judge looks for",
         _esa(COLORE_PARTENZA) in scena_html()
         and _esa(COLORE_ARRIVO) in scena_html()
         and _esa(COLORE_FONDO) in scena_html(),
         "%s · %s · %s" % (_esa(COLORE_PARTENZA), _esa(COLORE_ARRIVO),
                           _esa(COLORE_FONDO))),
        ("the scene has NOTHING that changes by itself",
         not any(x in scena_html() for x in
                 ("setTimeout", "setInterval", "requestAnimationFrame",
                  "animation", "transition", "http://", "https://")),
         "no timer, no animation, no external resource"),
        ("the DEAF scene does not listen to the keyboard (tail grafted fault)",
         "keydown" in scena_html() and "keydown" not in scena_html(sorda=True),
         "healthy: listens · deaf: does not listen"),
        ("and the deaf scene paints the starting colour anyway",
         _esa(COLORE_PARTENZA) in scena_html(sorda=True)
         and _esa(COLORE_ARRIVO) not in scena_html(sorda=True),
         "⇒ the «before» stays judgeable, and the «after» cannot arrive"),
    ]
    for nome, ok, detto in controlli:
        print("  %s  %-58s  %s" % ("OK " if ok else "NO ", nome, detto))
        if not ok:
            guai += 1

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
    guai_gr, quanti_gr = casa_di_c1().certifica_gruppi("C4")
    guai += guai_gr

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐⭐ THE SHARED PROVISIONING — ⛔ the case that on 27 August 2026 was missing,
    #    and for which this mesh said «I could not look» while the
    #    session was alive and painted.
    # ⚠ The cases live in C2, with the code they certify: ⛔ a copy here would be
    #   a second place to diverge from (§1.47).
    # ═══════════════════════════════════════════════════════════════════════
    print()
    casa_pr = casa_della_provvista()
    if casa_pr is None:
        print("  NO   ⛔ I cannot find `11-c2-…py`: the provisioning cannot be certified")
        guai += 1
        guai_pr, quanti_pr = 0, 0
    else:
        guai_pr, quanti_pr = casa_pr.certifica_la_provvista("C4", "c4u")
        guai += guai_pr

    quanti = (len(casi) + 3 + len(casi_guasto) + len(controlli)
              + quanti_gr + quanti_pr)
    print()
    if guai:
        print("⛔ the judge is NOT reliable: %d cases out of %d wrong"
              % (guai, quanti))
        return 1
    print("⭐ %d cases out of %d: the judge can say GREEN, RED and «I do not know»," % (quanti, quanti))
    print("   ⭐⭐ it gives RED when ONLY outside the expected zone changes,")
    print("   ⭐ it withstands a colour shift of ±%d, and ⛔ it reads the grafted" % TOLLERANZA)
    print("   fault on the DIFFERENCE and not on the colour of the verdict.")
    # ⛔ The provisioning line is printed ONLY if the real cases ran.
    if quanti_pr >= 4:
        print("   ⭐⭐ and THE PROVISIONING: a /tmp/mozilla of another mesh I do not "
              "touch, and my tenant writes anyway — ⛔ never red")
    else:
        print("   ⚠ and THE PROVISIONING is covered ONLY halfway: the real cases "
              "need the administrator, and here I did not run them")
    print("⚠ and this certification covers THE JUDGE, not the input path")
    print("  (see the top): that is said by the real round and its two faults.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# THE TERRAIN — ⛔ it is prepared, and it is VERIFIED to be in force
# ═══════════════════════════════════════════════════════════════════════════
def sh(comando, secondi=180):
    return subprocess.run(["/bin/sh", "-c", comando],
                          capture_output=True, text=True, timeout=secondi)


def cliente_di_prova(percorso):
    """⭐ The RCP client is IMPORTED, not rewritten.

    ⛔ The whole QUIC/WebTransport handshake, the framing of §6.1, the
       types of §7.3 and the collection of frames from the wire sit in there and
       have already gone through B4's referee.  Rewriting a copy here
       would mean two clients that can diverge silently.
    ⇒ If it is not there, or if it cannot be imported, this mesh exits **3**.
    """
    if not percorso or not os.path.exists(percorso):
        return None
    spec = importlib.util.spec_from_file_location("b3cliente", percorso)
    m = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(m)
    except Exception:
        return None
    return m


def giudice_immagini():
    """⭐ The «black / solid colour / drawn» judge is IMPORTED too.

    ⚠ Here it does not decide the verdict — that is decided by the expected zone — but it says
      **why** a «before» is not in force: *«the screen was black»* and *«the
      page did not appear»* are two different diagnoses, and carrying both
      costs one line.  ⛔ If it is missing, we go on without it: and we say so.
    """
    for base in (QUI, os.path.dirname(QUI)):
        perc = os.path.join(base, "10-f1-testimone.py")
        if os.path.exists(perc):
            spec = importlib.util.spec_from_file_location("testimone10f1", perc)
            m = importlib.util.module_from_spec(spec)
            try:
                spec.loader.exec_module(m)
                return m
            except Exception:
                return None
    return None


def crea(chi, parola):
    """The tenant, ⛔ **from zero**, and created **as the product creates it**.

    ⛔⛔ AND IT IS DELETED BEFORE CREATING IT.  `LEZIONI.md` §1.39, and the line C1
       paid for: `id -u X || useradd X` makes a new user **only the first
       time the bench runs in its life**.  ⇒ «From zero» also includes «from
       zero with respect to myself of yesterday».
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


def sgombra(chi, attesa=45.0):
    """⛔ We wait for it to be REALLY gone, not half a second by the clock.

    ⚠ It is C1's cure: `[M]` 26 August 2026, ten rounds, a perfect alternation
      between «I do not know» and «blind» — a state that survived the round.
    """
    sh("loginctl terminate-user %s 2>/dev/null" % chi)
    time.sleep(1.0)
    sh("pkill -KILL -u %s 2>/dev/null" % chi)
    scadenza = time.time() + attesa
    while time.time() < scadenza:
        viva = sh("loginctl show-user %s >/dev/null 2>&1" % chi).returncode == 0
        proc = sh("pgrep -u %s >/dev/null 2>&1" % chi).returncode == 0
        if not viva and not proc:
            return True
        time.sleep(0.5)
    return False


def scrivi_la_scena(chi, sorda):
    """⭐ The scene is written **in the tenant's home**, and new at every round.

    ⛔ And not in the bench's working folder: `[M]` 26 August 2026, C8 —
       that belongs to `root`, and the browser runs **as a user**.  The defect there
       came out as «the browser did not draw», i.e. ⛔ the bench gave red to
       itself and attributed it to the product (`LEZIONI.md`, §7-bis.10).
    """
    perc = "/home/%s/.c4-scena.html" % chi
    try:
        with open(perc, "w") as f:
            f.write(scena_html(sorda=sorda))
    except OSError as e:
        return None, str(e)[:120]
    sh("chown %s:%s %s; chmod 644 %s" % (chi, chi, perc, perc))
    return perc, None


def apri_la_scena(chi, browser, pagina, registro):
    """Switches on the browser INSIDE the tenant's session, full screen.

    ⛔ The Wayland socket is SEARCHED for, not guessed: the name depends on how
       the compositor was born, and nailing down `wayland-0` here would mean a
       mesh that works on one desktop and stays silent on the others — i.e. the defect
       this phase exists not to introduce.
    """
    uid = sh("id -u %s" % chi).stdout.strip()
    if not uid:
        return None, "I do not know the uid of %s" % chi
    rtd = "/run/user/%s" % uid
    soc = sh("ls %s 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1" % rtd)
    display = soc.stdout.strip()
    if not display:
        return None, ("in %s there is no wayland socket: the session does not have "
                      "a compositor the browser can talk to" % rtd)
    # ⛔ `setsid` + stdin closed: without it, the browser ends up in a BACKGROUND
    #    process group of the terminal that launched the net and the first
    #    `tcsetattr` gets it a SIGTTOU ⇒ it stays in state `T` from the first
    #    instant (22 Sep 2026, seen in C3 on all three boxes).
    sh("setsid runuser -u %s -- env XDG_RUNTIME_DIR=%s WAYLAND_DISPLAY=%s "
       "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/%s "
       "%s --kiosk file://%s < /dev/null > %s 2>&1 &"
       % (chi, rtd, display, chi, browser, pagina, registro), secondi=30)
    return display, None


# ═══════════════════════════════════════════════════════════════════════════
# THE WIRE — ⭐ a single connection, and the whole round fits inside it
# ═══════════════════════════════════════════════════════════════════════════
def fabbrica_cliente(B3):
    """⭐ The test client, **plus the two messages it could not send**.

    ⛔ §7.3: `LETTERA` and `POSIZIONE_TASTO` travel on the **input channel** —
       a single unidirectional stream, opened after `SESSIONE` and kept open —
       and carry `u32 id` (increasing over the whole channel, `0` reserved) and
       `u64 istante` in microseconds of the client's monotonic clock.
    ⚠ The `id` is the one of `apri_input()`/`inp_id` of the imported client: we
      **continue its numbering**, we do not open a second one.  Two counters
      on the same channel would be two truths about the same fact.
    """

    class ClienteCoiTasti(B3.Cliente):
        def _manda_input(self, tipo, resto):
            sid = self.apri_input()
            self.inp_id += 1
            # ⛔ §7.3, finding R1.27: REAL microseconds.  Milliseconds are not
            #    multiplied by a thousand to make believe in a precision one does not
            #    have — and on Linux `time.monotonic()` has nanosecond grain.
            ist = int(time.monotonic() * 1_000_000)
            b = B3.inquadra(tipo, struct.pack("!IQ", self.inp_id, ist) + resto)
            self._quic.send_stream_data(sid, b, end_stream=False)
            self.transmit()
            return self.inp_id

        def manda_lettera(self, carattere):
            """§7.3 `LETTERA` — a Unicode scalar value."""
            return self._manda_input(T_LETTERA, struct.pack("!I", carattere))

        def manda_posizione_tasto(self, codice, premuto):
            """§7.3 `POSIZIONE_TASTO` — **evdev** code, pressed/released."""
            return self._manda_input(
                T_POSIZIONE_TASTO, struct.pack("!HB", codice, 1 if premuto else 0))

    return ClienteCoiTasti


def fetta_di_flusso(fotogrammi, percorso):
    """The frames of a time window, put into a `.264` file.

    ⛔ We start from the first **keyframe**: a stream that begins with a
       differential frame does not decode, and ffmpeg would produce either nothing or
       a dirty image — i.e. artefacts **of our own bench**, the wrong answer
       to the question this mesh exists to ask.
    ⛔ And they are sorted by NUMBER (§6.2): the streams are independent and can
       arrive out of order.
    ⇒ Returns `None` if no keyframe arrived in that window.
    """
    ordinati = sorted(fotogrammi, key=lambda f: f[0])
    inizio = None
    for i, f in enumerate(ordinati):
        if f[1]:
            inizio = i
            break
    if inizio is None:
        return None
    with open(percorso, "wb") as f:
        for x in ordinati[inizio:]:
            f.write(x[4])
    return len(ordinati) - inizio


def _decodifica(flusso, fuori):
    """⛔ `-update 1` keeps the LAST frame: it is what the desktop shows
       NOW.  The first would be the opening keyframe, i.e. a second ago."""
    d = sh("ffmpeg -hide_banner -loglevel error -i %s -vsync 0 -update 1 -y %s"
           % (flusso, fuori), secondi=180)
    if d.returncode != 0 or not os.path.exists(fuori) \
            or os.path.getsize(fuori) == 0:
        return None
    return fuori


async def scatta(B3, cli, lavoro, nome, secondi):
    """A photograph of the session, **without detaching**.

    ⇒ Returns `(png|None, quanti_fotogrammi, perche'|None)`.
    ⛔ Three outcomes and not two: «the PNG is there», «no frame arrived»,
       «they arrived but no image was made of them» — and the last two are
       *«I did not look»*, not «the screen was empty».
    """
    n0 = len(cli.v_fotogrammi)
    # ⛔ A STILL DESKTOP DOES NOT SEND FRAMES: the server sends only what
    #    changes.  ⇒ A keyframe is ASKED for, or the «before» of a motionless scene
    #    would always be empty and the mesh would say «I do not know» forever.
    #    ⚠ It is the same reason why the client has `--chiave-dopo` (§6.2).
    ultimo = max((f[0] for f in cli.v_fotogrammi), default=0)
    try:
        cli.manda(B3.inquadra(B3.T["RICHIEDI_CHIAVE"], struct.pack("!I", ultimo)))
    except Exception as e:
        return None, 0, "I could not ask for a keyframe: %s" % str(e)[:80]
    # ⛔ We wait with our eyes open: a `sleep` would not notice that the
    #    session fell, and the bench would measure itself (R8.2/R8.4).
    try:
        await asyncio.wait_for(cli.caduto.wait(), timeout=secondi)
        return None, 0, "the session fell while I was looking: %s" % cli.caduta
    except asyncio.TimeoutError:
        pass
    fetta = cli.v_fotogrammi[n0:]
    if not fetta:
        return None, 0, ("no frame arrived from the wire in %.0f s "
                         "(stage that does not deliver, or session without a monitor)"
                         % secondi)
    flusso = os.path.join(lavoro, "%s.264" % nome)
    quanti = fetta_di_flusso(fetta, flusso)
    if quanti is None:
        return None, len(fetta), ("%d frames arrived but no keyframe: I do not "
                                  "know where to start decoding"
                                  % len(fetta))
    fuori = os.path.join(lavoro, "%s.png" % nome)
    # ⚠ ffmpeg can take quite a while: it runs in its own thread, or the client
    #   would stop reading from the socket and the connection would drop by itself.
    png = await asyncio.to_thread(_decodifica, flusso, fuori)
    if png is None:
        return None, quanti, ("%d frames arrived but ffmpeg did not make "
                              "an image of them" % quanti)
    return png, quanti, None


async def aspetta_la_scena(B3, cli, a, lavoro):
    """⛔ WE WAIT FOR THE EVENT, NOT FOR THE CLOCK.

    `[M]` 26 August 2026, C1: with a fixed wait **six rounds out of six** said
    «I do not know» — not because something was broken, but because the bench looked
    too early.  ⇒ Here we look **until the scene appears**, and if it does not appear
    within the declared time the outcome is «I do not know», ⛔ never a green.

    Returns `(png|None, perche')` — the image is already the «before».
    """
    scadenza = time.time() + a.attesa_scena
    ultimo_perche = "the scene did not appear in %.0f s" % a.attesa_scena
    giro = 0
    while time.time() < scadenza:
        giro += 1
        png, quanti, perche = await scatta(
            B3, cli, lavoro, "prima-%02d" % giro, a.passo_scena)
        if png is None:
            ultimo_perche = perche
            continue
        img = _carica(png)
        if img is None:
            ultimo_perche = "the image could not be read"
            continue
        pezzo, _ = taglia(img)
        fr = frazione_del_colore(pezzo, COLORE_PARTENZA)
        if fr >= FRAZIONE_COLORE:
            return png, ("the scene is in force: the zone is the starting "
                         "colour for %.0f %% (after %d attempts)"
                         % (100 * fr, giro))
        ultimo_perche = ("the zone is the starting colour only for %.0f %% "
                         "(%.0f %% is needed)"
                         % (100 * fr, 100 * FRAZIONE_COLORE))
    return None, ultimo_perche


async def il_giro(B3, a, chi, lavoro):
    """The real round: a single connection, and everything inside.

    ⇒ Returns `(png_prima, png_dopo, note)`; the two `None` mean «I could not
      look», and the note says **why**.
    """
    note = []
    Cl = fabbrica_cliente(B3)
    conf = B3.QuicConfiguration(is_client=True, alpn_protocols=B3.H3_ALPN,
                                max_datagram_frame_size=65536)
    conf.verify_mode = B3.ssl.CERT_NONE
    autorita = "%s:%d" % (a.indirizzo, a.porta)

    async with B3.connect(a.indirizzo, a.porta, configuration=conf,
                          create_protocol=Cl) as cli:
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.apri_sessione(autorita, a.percorso)
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        if stato != "200":
            return None, None, ["the extended CONNECT answered %s" % stato]
        cli.apri_controllo()

        # ⚠ THE ATTACH SEQUENCE IS COPIED FROM THE CLIENT'S `principale()`:
        #   that program is a single piece governed by `argparse` and cannot
        #   be called halfway.  ⛔ If the handshake changes, this
        #   mesh must be updated by hand — and it is the debt declared at the top.
        # ⚠ **H.264** is declared, and it must be said: the PNG is made by `ffmpeg` from the bytes of the
        #   wire, and narrowing the intersection is a use of the protocol, not a
        #   workaround (§4.3).  ⛔ And numbers taken with different codecs are not
        #   compared — here none are taken, but the rule holds anyway.
        cli.manda(B3.inquadra(
            B3.T["CIAO"], B3.corpo_ciao(audio="pcm", video="h264", prof="8,10")))
        await B3.attendi(cli, "ECCOMI")
        cli.manda(B3.inquadra(B3.T["CREDENZIALI"], B3.s(chi) + B3.s(a.parola)))
        # ⚠ §4.4-bis: the AMMESSO has a fixed delay of one second.  ⛔ Here it is not
        #   judged (that is another mesh): we wait long enough.
        await B3.attendi(cli, "AMMESSO", attesa=30)
        cli.manda(B3.inquadra(
            B3.T["ATTACCA"],
            struct.pack("!IIII", a.larghezza, a.altezza, a.larghezza, a.altezza)
            + B3.s(a.disposizione)))
        nome, corpo, _ = await B3.attendi(cli, "SESSIONE",
                                          attesa=a.attesa_sessione)
        lar, alt = struct.unpack("!II", corpo[1:9])
        note.append("SESSIONE: canvas %dx%d" % (lar, alt))

        # ── the stage: we wait for the FIRST FRAME ─────────────────────────
        #
        # ⭐ And not «the log says monitor»: that is what C1 looks at.  Here it is needed
        #   that the wire delivers pixels, which is the layer above.
        # ⛔ And we wait for the EVENT: the deadline produces «I do not know», never a green.
        # ⚠ The ceiling is the SUM of two distinct waits (see the top): the stage
        #   being born `[M]` (up to 152 s on GNOME) and the encoder
        #   delivering `[?]`.
        tetto = a.attesa_palco + a.attesa_primo_fotogramma
        t0 = time.monotonic()
        scadenza = time.time() + tetto
        while time.time() < scadenza and not cli.v_fotogrammi:
            try:
                await asyncio.wait_for(cli.caduto.wait(), timeout=1.0)
                return None, None, note + ["the session fell while waiting for the "
                                           "first frame: %s" % cli.caduta]
            except asyncio.TimeoutError:
                pass
        if not cli.v_fotogrammi:
            return None, None, note + [
                "no frame in %.0f s (stage %.0f + encoder %.0f): "
                "the stage does not deliver"
                % (tetto, a.attesa_palco, a.attesa_primo_fotogramma)]
        # ⭐ And the time is PRINTED: it is the number from which the `[?]` are calibrated, and without
        #   writing it the next calibration would be a guess again.
        note.append("the stage delivers: first frame after %.1f s from SESSIONE"
                    % (time.monotonic() - t0))

        # ── the wake-up — ⛔ BEFORE opening the scene, and the why is at the top ─
        if a.sveglia > 0:
            for _ in range(a.sveglia):
                cli.manda_posizione_tasto(ESC_EVDEV, True)
                await asyncio.sleep(0.06)
                cli.manda_posizione_tasto(ESC_EVDEV, False)
                await asyncio.sleep(0.12)
            note.append("wake-up: %d ESC sent BEFORE the scene exists "
                        "(⇒ they cannot paint it)" % a.sveglia)
            await asyncio.sleep(a.attesa_sveglia)

        # ── the scene ──────────────────────────────────────────────────────
        pagina, err = scrivi_la_scena(chi, a.scena_sorda)
        if pagina is None:
            return None, None, note + ["I could not write the scene: %s" % err]
        note.append("scene written in %s%s"
                    % (pagina, "  ⛔ DEAF (grafted fault)"
                       if a.scena_sorda else ""))
        display, err = apri_la_scena(chi, a.browser, pagina,
                                     "/tmp/c4-%s.log" % chi)
        if display is None:
            return None, None, note + ["I could not open the scene: %s" % err]
        note.append("browser switched on on %s" % display)

        png_prima, perche = await aspetta_la_scena(B3, cli, a, lavoro)
        note.append(perche)
        if png_prima is None:
            return None, None, note

        # ── ⭐ THE KEY ──────────────────────────────────────────────────────
        if a.senza_tasto:
            note.append("⛔ GRAFTED FAULT: the key was NOT sent")
        else:
            for i in range(a.ripetizioni):
                if a.tasto == "posizione":
                    cli.manda_posizione_tasto(a.codice_evdev, True)
                    await asyncio.sleep(0.06)
                    cli.manda_posizione_tasto(a.codice_evdev, False)
                else:
                    cli.manda_lettera(a.lettera)
                if i + 1 < a.ripetizioni:
                    await asyncio.sleep(a.pausa_tasto)
            note.append("sent %d keys (%s, id up to %d)"
                        % (a.ripetizioni,
                           "POSIZIONE_TASTO evdev %d" % a.codice_evdev
                           if a.tasto == "posizione"
                           else "LETTERA U+%04X" % a.lettera,
                           cli.inp_id))

        # ── and the AFTER image ────────────────────────────────────────────
        png_dopo, quanti, perche = await scatta(
            B3, cli, lavoro, "dopo", a.attesa_tasto)
        if png_dopo is None:
            return png_prima, None, note + ["the «after» could not be "
                                            "looked at: %s" % perche]
        note.append("«after» taken from %d frames" % quanti)
        return png_prima, png_dopo, note


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente", default="c4u1",
                   help="⛔ it is deleted and recreated at every round: «from zero» "
                        "includes «from zero with respect to myself of yesterday»")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=PORTA_PREDEFINITA)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--browser", default="firefox-esr")
    p.add_argument("--lavoro", default="/var/lib/rete11/c4")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")

    p.add_argument("--tasto", choices=("lettera", "posizione"), default="lettera",
                   help="⭐ which message of §7.3 is used. «lettera» also goes through "
                        "the map of src/tastiera.c, and it is the longest "
                        "path: it is the default on purpose")
    p.add_argument("--lettera", type=lambda x: int(x, 0), default=LETTERA,
                   help="the Unicode scalar value of the LETTERA (default «a»)")
    p.add_argument("--codice-evdev", type=int, default=ESC_EVDEV,
                   help="the evdev code of POSIZIONE_TASTO (1 = ESC)")
    p.add_argument("--ripetizioni", type=int, default=3,
                   help="⚠ it is not «hoping»: [M] 23 Aug 2026 (09-b72) a "
                        "freshly born GNOME session can consume the first "
                        "key to leave the overview. ⛔ And if NONE "
                        "of the keys makes a pixel change, the path is broken")
    p.add_argument("--pausa-tasto", type=float, default=0.15)

    p.add_argument("--sveglia", type=int, default=1,
                   help="how many ESC to send BEFORE opening the scene, to leave "
                        "the GNOME overview. ⛔ Before, not after: "
                        "after they would paint the target by themselves")
    p.add_argument("--senza-sveglia", action="store_true",
                   help="⭐ removes the wake-up: to be used to measure whether it is still "
                        "needed. ⛔ A gesture is not kept because «it does no harm»")
    p.add_argument("--attesa-sveglia", type=float, default=3.0)

    p.add_argument("--attesa-sessione", type=float, default=ATTESA_SESSIONE,
                   help="how long to wait for the SESSIONE reply. ⚠ [?] prudent")
    p.add_argument("--attesa-palco", type=float, default=ATTESA_PALCO,
                   help="how long the STAGE is given to be born. ⭐ 152 s = the "
                        "maximum measured on GNOME (101.0 s) plus half — [M] "
                        "27 Aug 2026, C1")
    p.add_argument("--attesa-primo-fotogramma", type=float,
                   default=ATTESA_PRIMO_FOTOGRAMMA,
                   help="how long the ENCODER is given after the stage is there. "
                        "⚠ [?] not measured: it is ADDED to the wait for the stage, "
                        "because they are two phenomena in a row (§1.45)")
    p.add_argument("--attesa-scena", type=float, default=ATTESA_SCENA,
                   help="how long to wait for the page to appear in the zone. "
                        "⚠ [?] not measured: it includes the FIRST start of Firefox "
                        "in a cold box, which [M] exceeds 25 s (C8, §1.45)")
    p.add_argument("--passo-scena", type=float, default=5.0,
                   help="how often to look again, waiting for the scene")
    p.add_argument("--attesa-tasto", type=float, default=ATTESA_TASTO,
                   help="how long to wait for the pixel to change. ⚠ [?] to calibrate")
    p.add_argument("--attesa-sgombero", type=float, default=45.0)

    p.add_argument("--senza-tasto", action="store_true",
                   help="⛔ GRAFTED FAULT (head): everything is done except sending "
                        "the key. The mesh MUST give red")
    p.add_argument("--scena-sorda", action="store_true",
                   help="⛔ GRAFTED FAULT (tail): the scene is written without the "
                        "keyboard handler. The mesh MUST give red")
    p.add_argument("--tieni-inquilino", action="store_true",
                   help="⚠ for diagnosis only: it does not clean up at the end")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if a.senza_sveglia:
        a.sveglia = 0
    innestato = a.senza_tasto or a.scena_sorda

    if os.geteuid() != 0:
        print("⛔ it must be run as administrator: it has to create a tenant")
        sys.exit(2)

    # ── the terrain, and the things without which we do not judge ──────────
    if _numpy_o_niente() is None:
        print("⛔ the box does not have numpy: I cannot look at a pixel")
        print("   ⇒ I could not look")
        sys.exit(3)
    B3 = cliente_di_prova(a.cliente)
    if B3 is None:
        print("⛔ I cannot find (or cannot import) the test client: %s"
              % a.cliente)
        print("   ⇒ I could not look")
        sys.exit(3)
    if getattr(B3, "AIOQUIC", None) is not None:
        print("⛔ the box is missing `aioquic`: the client cannot even "
              "try (%s)" % B3.AIOQUIC)
        print("   ⇒ I could not look")
        sys.exit(3)
    if sh("command -v %s" % a.browser).returncode != 0:
        print("⛔ the box does not have %s: I have no scene to put on the "
              "screen" % a.browser)
        print("   ⇒ I could not look")
        sys.exit(3)
    if sh("command -v ffmpeg").returncode != 0:
        print("⛔ the box does not have ffmpeg: the frames do not become "
              "an image")
        print("   ⇒ I could not look")
        sys.exit(3)

    os.makedirs(a.lavoro, exist_ok=True)
    giudice = giudice_immagini()

    print("== C4 — the key arrives all the way to the screen ==")
    print("   tenant «%s» (NEW) · port %d · canvas %dx%d"
          % (a.utente, a.porta, a.larghezza, a.altezza))
    print("   the scene: target from %.0f %% to %.0f %% of the screen, "
          "%s → %s at the first key"
          % (100 * BERSAGLIO[0], 100 * BERSAGLIO[2],
             _esa(COLORE_PARTENZA), _esa(COLORE_ARRIVO)))
    print("   the EXPECTED ZONE: from %.0f %% to %.0f %% in both directions "
          "(%.0f %% of the screen, in the middle)"
          % (100 * ZONA[0], 100 * ZONA[2],
             100 * (ZONA[2] - ZONA[0]) * (ZONA[3] - ZONA[1])))
    print("   the WITNESS ZONE: the frame, everything outside %.0f..%.0f %% — "
          "nothing must change there"
          % (100 * TESTIMONE[0], 100 * TESTIMONE[2]))
    print("   the yardstick: %.0f %% of the zone the colour ±%d · changed inside "
          "≥ %.0f %% · witness ≤ %.0f %%"
          % (100 * FRAZIONE_COLORE, TOLLERANZA, 100 * CAMBIO_MINIMO_DENTRO,
             100 * CAMBIO_MASSIMO_TESTIMONE))
    print("   the key: %s × %d"
          % ("POSIZIONE_TASTO evdev %d" % a.codice_evdev
             if a.tasto == "posizione" else "LETTERA U+%04X" % a.lettera,
             a.ripetizioni))
    if a.senza_tasto:
        print("   ⛔ GRAFTED FAULT (head): the key will NOT be sent")
    if a.scena_sorda:
        print("   ⛔ GRAFTED FAULT (tail): the scene does not listen to the keyboard")
    if giudice is None:
        print("   ⚠ I cannot find 10-f1-testimone.py: the «before» will be diagnosed "
              "without its word («black» / «drawn»)")
    print()

    # ⭐ BEFORE `crea`: `crea` does `userdel -r`, and from that moment the owner of
    #   `/tmp/mozilla` would be a NUMBER instead of a name — i.e. I would no
    #   longer recognise it as mine.  ⛔ My base is the name without the trailing
    #   digits: «c4u1» ⇒ «c4u».
    resto = sgombra_il_mio_rimasuglio(re.sub(r"\d+$", "", a.utente))
    print("   provisioning: the cure of src/provisiona.sh, imported from C2, "
          "for the tenant I create")
    if resto:
        print("   %s" % resto)

    fatto, perche = crea(a.utente, a.parola)
    if not fatto:
        print("⛔ I could not create «%s»: %s" % (a.utente, perche))
        print("   ⇒ the terrain does not hold")
        sys.exit(2)

    png_prima = png_dopo = None
    note = []
    try:
        png_prima, png_dopo, note = asyncio.run(il_giro(B3, a, a.utente, a.lavoro))
    except Exception as e:
        note = ["the round was interrupted: %s: %s" % (type(e).__name__, str(e)[:160])]
    finally:
        if not a.tieni_inquilino:
            if not sgombra(a.utente, a.attesa_sgombero):
                note.append("⚠ «%s» did not go away in %.0f s"
                            % (a.utente, a.attesa_sgombero))

    for n in note:
        print("   ·  %s" % n)

    # ── and the diagnosis of the «before», when the witness is there ───────
    if giudice is not None and png_prima:
        g = giudice.giudica(png_prima)
        if g is not None:
            print("   ·  the «before», seen by the 10-f1 witness: %s "
                  "(mean %.1f, lit %.5f)"
                  % (g["verdetto"], g["media"], g["accesi"]))

    m = misura(png_prima, png_dopo)
    verdetto, motivo = giudica(m)
    print()
    print("   %s" % riga_misure(m))
    print("   %s" % motivo)
    print()

    # ═══════════════════════════════════════════════════════════════════════
    # ⛔ WITH THE GRAFTED FAULT THE OUTCOME IS READ BACKWARDS: `0` = seen.
    #    And «seen» is read on the DIFFERENCE, not on the colour of the verdict
    #    (`LEZIONI.md` §1.52).
    # ═══════════════════════════════════════════════════════════════════════
    if innestato:
        quale = "without key" if a.senza_tasto else "deaf scene"
        if guasto_visto(verdetto, m):
            print("⭐ THE GRAFTED FAULT (%s) WAS SEEN: the mesh is red,"
                  % quale)
            print("   ⛔ the zone is STILL the starting colour (%.0f %%) and "
                  "inside only %.0f %% changed (the ceiling is %.0f %%)."
                  % (100 * m["dopo_partenza"], 100 * m["dentro"],
                     100 * CAMBIO_RESIDUO))
            print("   ⇒ this mesh CAN say red, and it says it for the right reason")
            return 0
        if verdetto is None:
            print("⛔ I could not judge: I cannot say whether the fault "
                  "would have been seen.")
            print("   ⚠ And this is NOT «the fault was not seen»: it is a "
                  "test that did not look (§4.5).")
            return 3
        if verdetto is False:
            print("⛔⛔ RED, but NOT because of the fault: the zone did not stay "
                  "at the starting colour,")
            print("    or inside more than %.0f %% changed.  ⇒ Saying «the fault "
                  "was seen» here" % (100 * CAMBIO_RESIDUO))
            print("    would mean certifying the net on a fault of the "
                  "product (§1.52).")
            return 1
        print("⛔⛔ THE GRAFTED FAULT (%s) WAS NOT SEEN: the mesh says "
              "GREEN." % quale)
        print("    ⇒ either the key has nothing to do with the pixel that changes, or this "
              "mesh does not look")
        print("    in the right place — and in both cases it cannot "
              "be trusted.")
        return 1

    # ── the normal round ───────────────────────────────────────────────────
    if verdetto is True:
        print("⭐ GREEN — the key arrived ALL THE WAY TO THE SCREEN.")
        return 0
    if verdetto is False:
        print("⛔⛔ RED — the key does NOT arrive at the screen.")
        print("    The session was there, the scene was there, the key left, ⛔ and the "
              "expected zone did not change.")
        return 1
    print("⚠ NOT JUDGING — ⛔ and this is not a green: it is an outcome of its own (§4.5).")
    return 3


if __name__ == "__main__":
    sys.exit(main())
