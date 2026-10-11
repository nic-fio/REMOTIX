#!/usr/bin/env python3
"""04-b28-gestures.py — ⭐ THE BENCH FOR TOUCH MODE (link A8 of phase 4).

    python3 benches/04-b28-gestures.py --certify     ⭐ without a browser: can the
                                                      judge see the defect?
    python3 benches/04-b28-gestures.py --run --port 7671 --diagnosis 7672
    python3 benches/04-b28-gestures.py --verdict benches/04-b28-register.jsonl

===========================================================================
⛔ WHAT IT MEASURES, AND WHICH SIDE IT STANDS ON

Two DISTINCT questions, and they are judged separately:

  ⒜ **the seven gestures** (`SPECS.md` §7.2): a synthetic sequence of
     `Touch` events for each one ⇒ the expected message of `RCP.md` §7.3;
  ⒝ **the automatic switch** (`DECISIONS.md` §5-bis.0-bis): the context is
     declared and it is checked **which layout is IN FORCE** — by reading
     `body[data-layout]`, which the product writes, and by proving that
     the other half is really OFF.  ⛔ Not «there is a function that changes
     it»: a function that changes nothing can exist just fine.

⛔ The bytes are decoded with a reader written HERE, from the table of
   `RCP.md` §7.3, without looking at the page's JavaScript.  If one day the
   two disagree, **that disagreement is the gift**.

===========================================================================
⛔⛔ THE BENCH IS CERTIFIED ON THE CONFUSIONS, NOT ON THE CLEAN GESTURES

This is the most important line in this file.  A bench that tests the seven
clean gestures says **green** on a recogniser that gets every edge case wrong:
the clean gestures are easy, and no real defect lives there.

  G1..G7   the seven clean gestures  — they serve as POSITIVE control
  C1..C8   ⭐ the CONFUSIONS         — this is where the verdict is decided
  D1..D4   the automatic switch
  S1       ⭐ the SEAM between the two anchors, which in phase 3 no bench
           looked at (`fasi/rapporti/F5-desktop-vero.md`)

⛔ And `--certify` injects FIVE faults, one per family of confusion, and
   demands **green → red → green** on each.  A judge that cannot say red
   cannot say green (`CODER.md` §3.3, §3.10, §4.6).

===========================================================================
⚠ THE SCENE, DECLARED — and the stage is verified from the other end

The browser opens on the user's REAL desktop: that is what the mandate
asks, and ⛔ **it is not moved to a fake screen to make the numbers add up**.
What the scene really was is written by the collector in every line of
`04-b28-outcomes.jsonl` — `XDG_SESSION_TYPE`, the `userAgent`, and the layout
that the PRODUCT wrote into the document.

⛔ And touch is declared by the bench, not by the environment: `Emulation.setTouchEmulation
   Enabled` turns on the contact points, and ⚠ **what comes out of it is
   the emulation, not a finger** (`LESSONS.md` §1.11).  ⇒ NO number comes out
   of here on how a real hand behaves: what comes out are the boundaries of the
   RECOGNISER, which are deterministic and measure well even this way.
   ⭐ The judgement on the gestures stays with Nic, with a finger, and it is
   written in the report.
"""

import argparse
import http.server
import importlib.util
import json
import os
import socketserver
import struct
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# `RCP.md` §7.3 — the types of the input channel and the evdev codes.
POINTER, BUTTON, WHEEL = 0x0101, 0x0102, 0x0103
SINISTRO, DESTRO, CENTRALE = 0x110, 0x111, 0x112
NAMES = {POINTER: "POINTER", BUTTON: "BUTTON", WHEEL: "WHEEL"}
BTN_NAMES = {SINISTRO: "sinistro", DESTRO: "destro", CENTRALE: "centrale"}

TELA = (1920, 1080)

# ── the registers recorded before the English rename (DECISIONI §10.38: 04-b28-register.jsonl of
#    phase 4) keep the Italian words, and --verdict re-reads them.  The first tuple is protected
#    (english-migration/protetti.tsv), the second is renamed with the code: after the rename
#    OLD_SPELLING maps every old word to the code's own, before it is empty.
_OLD_WORDS = (
    "fase", "marca",
    "C1-tap-troppo-lungo", "C2-tap-che-scivola", "C3-due-dita-a-30ms",
    "C4-due-dita-senza-sovrapposizione", "C5a-doppio-clic", "C5b-tap-e-mezzo-che-trascina",
    "C6-trascinamento-che-comincia-fermo", "C7a-pizzico-non-rotella",
    "C7b-rotella-non-pizzico", "C8-il-dito-residuo", "G1-un-dito-trascina", "G2-un-dito-tap",
    "G3-due-dita-tap", "G4-due-dita-trascina", "G5-tap-e-mezzo", "G6-tre-dita-tap",
    "G7-pizzico", "F-fine",
)  # end of the old words
_WORDS_NOW = (
    "phase", "mark",
    "C1-tap-too-long", "C2-tap-that-slides", "C3-two-fingers-30ms-apart",
    "C4-two-fingers-without-overlap", "C5a-double-click", "C5b-tap-and-a-half-that-drags",
    "C6-drag-that-starts-still", "C7a-pinch-not-wheel", "C7b-wheel-not-pinch",
    "C8-the-leftover-finger", "G1-one-finger-drags", "G2-one-finger-tap", "G3-two-finger-tap",
    "G4-two-fingers-drag", "G5-tap-and-a-half", "G6-three-finger-tap", "G7-pinch", "F-end",
)
OLD_SPELLING = {a: b for a, b in zip(_OLD_WORDS, _WORDS_NOW) if a != b}


def current_spelling(x):
    """A row of an old register in the code's spelling: keys, and string values equal to a word."""
    if isinstance(x, dict):
        return {OLD_SPELLING.get(k, k): current_spelling(v) for k, v in x.items()}
    if isinstance(x, list):
        return [current_spelling(v) for v in x]
    return OLD_SPELLING.get(x, x) if isinstance(x, str) else x


class Violation(Exception):
    pass


# ---------------------------------------------------------------------------
# THE BYTE READER — written from the table of `RCP.md` §7.3.
#
# ⛔ Framing of §6.1: u16 type, u32 length, body.  Body of §7.3:
#    u32 id (increasing, never 0) + u64 instant (microseconds) + the type's fields.
# ---------------------------------------------------------------------------
def decode(byte):
    report, o = [], 0
    while o < len(byte):
        if len(byte) - o < 6:
            raise Violation("truncated framing: %d bytes left" % (len(byte) - o))
        kind, lung = struct.unpack_from(">HI", byte, o)
        o += 6
        if len(byte) - o < lung:
            raise Violation("truncated body: %d declared, %d present"
                             % (lung, len(byte) - o))
        body = byte[o:o + lung]
        o += lung
        if kind >> 8 != 0x01:
            raise Violation("type 0x%04X: not on the input channel (§2.5)" % kind)
        if lung < 12:
            raise Violation("body of %d bytes: id and instant do not fit" % lung)
        mid, instant = struct.unpack_from(">IQ", body, 0)
        if mid == 0:
            raise Violation("id 0: §7.3 reserves it for «no input»")
        m = {"kind": kind, "name": NAMES.get(kind, "?"), "id": mid, "instant": instant}
        if kind == POINTER:
            if lung != 20:
                raise Violation("POINTER of %d bytes, it wants 20" % lung)
            m["x"], m["y"] = struct.unpack_from(">II", body, 12)
        elif kind == BUTTON:
            if lung != 15:
                raise Violation("BUTTON of %d bytes, it wants 15" % lung)
            m["code"], m["pressed"] = struct.unpack_from(">HB", body, 12)
        elif kind == WHEEL:
            if lung != 20:
                raise Violation("WHEEL of %d bytes, it wants 20" % lung)
            m["axis_x"], m["axis_y"] = struct.unpack_from(">ii", body, 12)
        else:
            raise Violation("unknown type 0x%04X on the input channel" % kind)
        report.append(m)
    return report


# ---------------------------------------------------------------------------
# THE JUDGE.  Each case is a function that receives the messages of its phase and
# returns (green: bool, why: str).
#
# ⛔ Expectations are written as PROPERTIES, not as strings to compare:
#    «no BUTTON» is a property that survives a different id or one extra
#    POINTER; «these exact bytes» would be green only on the run that
#    produced them (`LESSONS.md` §2.3 — v1's wheel bench, red with the
#    correct code, because of a badly searched string).
# ---------------------------------------------------------------------------
def _btn(ms):
    return [m for m in ms if m["kind"] == BUTTON]


def _click(ms, code):
    """The pressed/released pair of a button, counted as a CLICK."""
    p, n = None, 0
    for m in _btn(ms):
        if m["code"] != code:
            continue
        if m["pressed"] == 1:
            p = m
        elif p is not None:
            n += 1
            p = None
    return n


def _punt(ms):
    return [m for m in ms if m["kind"] == POINTER]


def _rot(ms):
    return [m for m in ms if m["kind"] == WHEEL]


def _solo(ms, code):
    """A single click, of that button, and nothing else on the wire."""
    if _rot(ms):
        return False, "there is a WHEEL: it was not a tap"
    if _click(ms, code) != 1:
        return False, ("%s clicks expected 1, counted %d (buttons: %s)"
                       % (BTN_NAMES.get(code, code), _click(ms, code),
                          [(BTN_NAMES.get(m["code"], m["code"]), m["pressed"])
                           for m in _btn(ms)]))
    others = [m for m in _btn(ms) if m["code"] != code]
    if others:
        return False, ("there are other buttons on the wire too: %s"
                       % [(BTN_NAMES.get(m["code"], m["code"]), m["pressed"])
                          for m in others])
    return True, "one %s click and nothing else" % BTN_NAMES.get(code, code)


def c_G1(ms):
    """1 finger drags = moves the pointer, and presses NOTHING."""
    if _btn(ms):
        return False, "a drag produced a button"
    p = _punt(ms)
    if len(p) < 3:
        return False, "only %d POINTER for a 200 px drag" % len(p)
    if p[-1]["x"] <= p[0]["x"]:
        return False, ("the finger went right and the pointer did not: from %d to %d"
                       % (p[0]["x"], p[-1]["x"]))
    return True, "%d POINTER, from x=%d to x=%d, no button" % (
        len(p), p[0]["x"], p[-1]["x"])


def c_G2(ms):
    return _solo(ms, SINISTRO)


def c_G3(ms):
    return _solo(ms, DESTRO)


def c_G4(ms):
    """2 fingers drag = wheel.  ⛔ The SIGN and the grain of 60 (§7.3)."""
    if _btn(ms):
        return False, "a two-finger scroll produced a button"
    r = _rot(ms)
    if not r:
        return False, "no WHEEL"
    for m in r:
        if m["axis_y"] % 60 or m["axis_x"] % 60:
            return False, ("WHEEL not a multiple of 60 (§7.3, the half notch): "
                           "%d, %d" % (m["axis_x"], m["axis_y"]))
    tot = sum(m["axis_y"] for m in r)
    if tot <= 0:
        return False, ("the fingers went down and the vertical axis is not positive "
                       "(%d): `RCP.md` §7.3 wants +120 for the wheel UP, and "
                       "two fingers going down push the sheet down" % tot)
    return True, "%d WHEEL, vertical sum +%d, all multiples of 60" % (len(r), tot)


def c_G5(ms):
    """⭐ TAP-AND-A-HALF: tap, then press and drag.  On the wire:
       click · pressed · moving POINTER · released.
       ⛔ And the POINTER must sit BETWEEN pressed and released, or it is not
          a drag: it is a double click."""
    p = _btn(ms)
    sin = [m for m in p if m["code"] == SINISTRO]
    if len(sin) != 4:
        return False, "expected 4 left-button events (down,up,down,up), counted %d" % len(sin)
    if [m["pressed"] for m in sin] != [1, 0, 1, 0]:
        return False, "the order is not down,up,down,up: %s" % [m["pressed"] for m in sin]
    # The POINTER between the THIRD and the FOURTH event: that is where the drag lives.
    i3 = ms.index(sin[2])
    i4 = ms.index(sin[3])
    inside = [m for m in ms[i3 + 1:i4] if m["kind"] == POINTER]
    if len(inside) < 2:
        return False, ("only %d POINTER between pressed and released: the "
                       "button stayed down without dragging anything" % len(inside))
    if inside[-1]["y"] == inside[0]["y"] and inside[-1]["x"] == inside[0]["x"]:
        return False, "the pointer did not move while the button was down"
    return True, ("click, then pressed + %d POINTER + released — "
                  "the drag is there" % len(inside))


def c_G6(ms):
    return _solo(ms, CENTRALE)


def c_G7(ms, zoom=None):
    """Pinch = zooms the client's VIEW.  ⛔ ZERO bytes on the wire."""
    if ms:
        return False, ("the pinch sent %d messages: §7.2 says it "
                       "zooms the VIEW, not the application" % len(ms))
    if zoom is None:
        return True, "no message on the wire (zoom not read)"
    if zoom <= 1.05:
        return False, "no message on the wire, but the view did not zoom in (zoom %.2f)" % zoom
    return True, "zero bytes on the wire, and the view is at %.2fx" % zoom


# ── ⭐ THE CONFUSIONS ───────────────────────────────────────────────────────
def c_C1(ms):
    """The tap that lasts a bit too long (400 ms, still) ⇒ NOT a click.
       Declared threshold: `T_TAP` = 180 ms."""
    if _btn(ms):
        return False, ("a still 400 ms contact produced a click: the "
                       "180 ms threshold is not checked")
    return True, "400 ms still, no click (T_TAP = 180 ms)"


def c_C2(ms):
    """The tap that slides (120 ms but 30 px) ⇒ NOT a click, it is a movement.
       Declared threshold: `D_TAP` = 9 CSS px."""
    if _btn(ms):
        return False, "a contact that slid 30 px produced a click (D_TAP = 9 px)"
    if not _punt(ms):
        return False, "slid 30 px and the pointer did not move at all"
    return True, "30 px of sliding: %d POINTER, no click" % len(_punt(ms))


def c_C3(ms):
    """⭐⭐ THE TWO FINGERS THAT LAND 30 ms APART.
       It is the case the mandate names.  A recogniser that counts the fingers
       at the start of the gesture sees ONE finger here and sends a LEFT click."""
    if _click(ms, SINISTRO):
        return False, ("LEFT click: the two fingers were 30 ms apart and the "
                       "count did not look at the maximum of simultaneous fingers")
    return _solo(ms, DESTRO)


def c_C4(ms):
    """⛔ THE DECLARED DEFECT, and the bench demands it exactly as it is.

    Two fingers that NEVER overlap (A 0→100 ms, B 130→230 ms, 60 px
    apart) come out as TWO LEFT CLICKS, not as one right click.
    ⛔ It is not a defect to fix here: the same sequence is also «I click
    here, then I click right there», and the only cure would be to delay EVERY
    left click by 300 ms — the price that `CODER.md` §1-bis forbids.
    ⇒ The bench pins the DECLARED behaviour: the day it changes,
      this line turns red and the report is reread."""
    if _click(ms, DESTRO):
        return False, ("a right click came out of two contacts that do not "
                       "overlap: the behaviour has changed from "
                       "what the A8 report declares — reread the report")
    n = _click(ms, SINISTRO)
    if n != 2:
        return False, "expected 2 left clicks (the declared defect), counted %d" % n
    return True, ("2 left clicks: it is the DECLARED defect — below an "
                  "overlap of one sample a right click comes out as a "
                  "double left click")


def c_C5a(ms):
    """⭐ Still double tap, same spot ⇒ DOUBLE CLICK (4 events, 0 POINTER)."""
    sin = [m for m in _btn(ms) if m["code"] == SINISTRO]
    if [m["pressed"] for m in sin] != [1, 0, 1, 0]:
        return False, "they are not four events down,up,down,up: %s" % [
            (BTN_NAMES.get(m["code"], m["code"]), m["pressed"]) for m in _btn(ms)]
    if _punt(ms):
        return False, ("there are %d POINTER inside a still double click: the "
                       "remote desktop would read it as a drag"
                       % len(_punt(ms)))
    return True, "four left-button events, zero POINTER — it is a double click"


def c_C5b(ms):
    """⭐ And the SAME opening that then drags ⇒ DRAG.  They are the same
       gesture up to the second contact: it is the refutation, and it is tested here."""
    return c_G5(ms)


def c_C6(ms):
    """The two-finger drag that starts STILL (350 ms of waiting).
       ⛔ A recogniser that decided «tap» when T_TAP is exceeded and
          stopped there would send no wheel."""
    if _btn(ms):
        return False, "350 ms still and then scrolling: a button came out"
    if not _rot(ms):
        return False, "350 ms still and then scrolling: no WHEEL"
    return True, "%d WHEEL after 350 ms of still fingers, no click" % len(_rot(ms))


def c_C7a(ms, zoom=None):
    """⭐ WHEEL VERSUS PINCH — the fingers move APART: zoom only."""
    if _rot(ms):
        return False, ("two fingers moving apart produced %d WHEEL: "
                       "pinch and wheel are confused" % len(_rot(ms)))
    if zoom is not None and zoom <= 1.05:
        return False, "no wheel, but the zoom did not change either (%.2f)" % zoom
    return True, "zero WHEEL, zoom %s" % ("%.2f" % zoom if zoom else "not read")


def c_C7b(ms, zoom=None):
    """⭐ And the PARALLEL fingers: wheel only, and the view does NOT zoom in."""
    if not _rot(ms):
        return False, "two parallel fingers and no WHEEL"
    if zoom is not None and zoom > 1.05:
        return False, ("two parallel fingers zoomed the view to %.2fx: "
                       "it was read as a pinch" % zoom)
    return True, "%d WHEEL, view still at %s" % (
        len(_rot(ms)), "%.2f" % zoom if zoom else "?")


def c_C8(ms):
    """The leftover: two fingers scroll, one lifts, the other still moves.
       ⛔ The pointer must NOT jump — it is the most visible defect,
          because at the end of a scroll one finger always lifts a moment earlier."""
    if _punt(ms):
        return False, ("the finger left after a scroll moved the "
                       "pointer (%d POINTER): at the end of the scroll the "
                       "pointer jumps" % len(_punt(ms)))
    return True, "the leftover finger did not move the pointer"


CASES = {
    "G1-one-finger-drags": c_G1,
    "G2-one-finger-tap": c_G2,
    "G3-two-finger-tap": c_G3,
    "G4-two-fingers-drag": c_G4,
    "G5-tap-and-a-half": c_G5,
    "G6-three-finger-tap": c_G6,
    "G7-pinch": c_G7,
    "C1-tap-too-long": c_C1,
    "C2-tap-that-slides": c_C2,
    "C3-two-fingers-30ms-apart": c_C3,
    "C4-two-fingers-without-overlap": c_C4,
    "C5a-double-click": c_C5a,
    "C5b-tap-and-a-half-that-drags": c_C5b,
    "C6-drag-that-starts-still": c_C6,
    "C7a-pinch-not-wheel": c_C7a,
    "C7b-wheel-not-pinch": c_C7b,
    "C8-the-leftover-finger": c_C8,
}

# Which cases also want the zoom read from the page.
WANT_ZOOM = {"G7-pinch", "C7a-pinch-not-wheel", "C7b-wheel-not-pinch"}


def judge(lines):
    """righe: [{"phase":…, "hex":…} | {"phase":…, "mark":True} | {"phase":…, "zoom":…}]"""
    per_phase, zoom = {}, {}
    for r in lines:
        f = r.get("phase", "?")
        if "hex" in r:
            per_phase.setdefault(f, b"")
            per_phase[f] += bytes.fromhex(r["hex"])
        elif "zoom" in r:
            zoom[f] = r["zoom"]
        else:
            per_phase.setdefault(f, b"")
    outcomes = []
    for name, fn in CASES.items():
        data = per_phase.get(name)
        if data is None:
            outcomes.append({"case": name, "green": False,
                          "why": "⛔ the phase was not recorded at all"})
            continue
        try:
            ms = decode(data)
        except Violation as e:
            outcomes.append({"case": name, "green": False,
                          "why": "⛔ violation of RCP.md §7.3: %s" % e})
            continue
        if name in WANT_ZOOM:
            green, why = fn(ms, zoom.get(name))
        else:
            green, why = fn(ms)
        outcomes.append({"case": name, "green": bool(green), "why": why,
                      "messages": len(ms)})
    # ⛔ The id grows over the WHOLE channel, not per type (§7.3): it is checked
    #    once, over all the messages of all the phases, in order of arrival.
    # ⚠ Only the gesture phases: after the switch measurement the page is
    #   RELOADED, and on a new page the counter restarts from 1 — which is
    #   correct, and it is a different session.  Counting them together would
    #   measure the bench, not the product.
    all_items = []
    for r in lines:
        if "hex" in r and r.get("phase") in CASES:
            try:
                all_items += decode(bytes.fromhex(r["hex"]))
            except Violation:
                pass
    ids = [m["id"] for m in all_items]
    grows = all(b > a for a, b in zip(ids, ids[1:]))
    outcomes.append({"case": "R1-increasing-identifier", "green": bool(ids) and grows,
                  "why": ("%d messages, id from %d to %d, increasing over the whole channel"
                             % (len(ids), ids[0], ids[-1])) if ids and grows
                            else "the identifiers do not increase over the whole channel: %s"
                                 % ids[:20]})
    return outcomes


# ---------------------------------------------------------------------------
# ⭐ THE CERTIFICATION — green → red → green, on FIVE faults, one per
#    family of confusion.  ⛔ `CODER.md` §3.3: the bench is certified before
#    the measurement, or a red is ambiguous between «it does not work» and «the
#    bench was not working».
# ---------------------------------------------------------------------------
def _b(kind, mid, ist, rest):
    body = struct.pack(">IQ", mid, ist) + rest
    return struct.pack(">HI", kind, len(body)) + body


class Pen:
    def __init__(self):
        self.n = 0
        self.t = 1000
        self.lines = []

    def _id(self):
        self.n += 1
        self.t += 5
        return self.n, self.t * 1000

    def punt(self, phase, x, y):
        i, t = self._id()
        self.lines.append({"phase": phase, "hex": _b(POINTER, i, t,
                                                   struct.pack(">II", x, y)).hex()})

    def btn(self, phase, cod, down):
        i, t = self._id()
        self.lines.append({"phase": phase, "hex": _b(BUTTON, i, t,
                                                   struct.pack(">HB", cod, down)).hex()})

    def rot(self, phase, ax, ay):
        i, t = self._id()
        self.lines.append({"phase": phase, "hex": _b(WHEEL, i, t,
                                                   struct.pack(">ii", ax, ay)).hex()})

    def zoom(self, phase, z):
        self.lines.append({"phase": phase, "zoom": z})

    def blank(self, phase):
        self.lines.append({"phase": phase, "mark": True})


def recording(fault=None):
    """A HEALTHY recording, with an optional injected fault."""
    p = Pen()

    def click(phase, cod):
        p.btn(phase, cod, 1)
        p.btn(phase, cod, 0)

    f = "G1-one-finger-drags"
    for x in range(1000, 1210, 50):
        p.punt(f, x, 540)

    click("G2-one-finger-tap", SINISTRO)
    click("G3-two-finger-tap", DESTRO)

    f = "G4-two-fingers-drag"
    for _ in range(3):
        p.rot(f, 0, 120 if fault != "rotella-al-contrario" else -120)

    f = "G5-tap-and-a-half"
    click(f, SINISTRO)
    p.btn(f, SINISTRO, 1)
    if fault != "tap-e-mezzo-non-trascina":
        for y in range(540, 620, 20):
            p.punt(f, 900, y)
    p.btn(f, SINISTRO, 0)

    click("G6-three-finger-tap", CENTRALE)

    f = "G7-pinch"
    p.blank(f)
    if fault == "pizzico-manda-rotella":
        p.rot(f, 0, 120)
    p.zoom(f, 2.0)

    f = "C1-tap-too-long"
    p.blank(f)
    if fault == "tap-lungo-clicca":
        click(f, SINISTRO)

    f = "C2-tap-that-slides"
    for x in range(900, 960, 20):
        p.punt(f, x, 540)

    f = "C3-two-fingers-30ms-apart"
    if fault == "trenta-ms-diventa-doppio-sinistro":
        click(f, SINISTRO)
        click(f, SINISTRO)
    else:
        click(f, DESTRO)

    f = "C4-two-fingers-without-overlap"
    click(f, SINISTRO)
    click(f, SINISTRO)

    f = "C5a-double-click"
    click(f, SINISTRO)
    click(f, SINISTRO)

    f = "C5b-tap-and-a-half-that-drags"
    click(f, SINISTRO)
    p.btn(f, SINISTRO, 1)
    for y in range(540, 620, 20):
        p.punt(f, 900, y)
    p.btn(f, SINISTRO, 0)

    f = "C6-drag-that-starts-still"
    for _ in range(2):
        p.rot(f, 0, 120)

    f = "C7a-pinch-not-wheel"
    p.blank(f)
    p.zoom(f, 1.8)

    f = "C7b-wheel-not-pinch"
    for _ in range(2):
        p.rot(f, 0, 120)
    p.zoom(f, 1.0)

    p.blank("C8-the-leftover-finger")
    return p.lines


FAULTS = [
    ("tap-lungo-clicca", "C1-tap-too-long",
     "a still 400 ms contact that sends a click (the T_TAP threshold not checked)"),
    ("trenta-ms-diventa-doppio-sinistro", "C3-two-fingers-30ms-apart",
     "two fingers 30 ms apart that come out as two left clicks instead of one right"),
    ("rotella-al-contrario", "G4-two-fingers-drag",
     "the wheel sign inverted (`RCP.md` §7.3, form E11)"),
    ("tap-e-mezzo-non-trascina", "G5-tap-and-a-half",
     "the tap-and-a-half that presses and releases without dragging — that is, a double click"),
    ("pizzico-manda-rotella", "G7-pinch",
     "the pinch that sends a wheel instead of zooming the view"),
]


def certify():
    print("⭐ CERTIFICATION OF THE JUDGE — green → red → green, on five")
    print("   faults, one per family of confusion.\n")
    healthy = judge(recording())
    rossi = [e for e in healthy if not e["green"]]
    if rossi:
        print("⛔ the HEALTHY recording is not green: the judge is broken.")
        for e in rossi:
            print("     %-40s %s" % (e["case"], e["why"]))
        return 1
    print("  ✅ HEALTHY recording: %d cases, all green" % len(healthy))

    ok = True
    for fault, case, text in FAULTS:
        outcomes = judge(recording(fault))
        my = [e for e in outcomes if e["case"] == case][0]
        others = [e["case"] for e in outcomes if not e["green"] and e["case"] != case]
        if my["green"]:
            print("  ⛔ fault «%s»: the judge does NOT see it." % fault)
            print("       %s" % text)
            ok = False
        elif others:
            print("  ⚠ fault «%s»: seen, but it also turned %s red"
                  % (fault, others))
            print("       (a judge that bleeds cannot say WHERE the defect is)")
            ok = False
        else:
            print("  ✅ %-36s red only on %s" % (fault, case))
            print("       ↳ %s" % text)

    healed = judge(recording())
    if [e for e in healed if not e["green"]]:
        print("⛔ the HEALED recording does not turn green again.")
        return 1
    print("  ✅ HEALED recording: green again")
    print("\n%s" % ("⭐ the judge is certified." if ok
                    else "⛔ the judge is NOT certified: nothing is measured."))
    return 0 if ok else 1


# ---------------------------------------------------------------------------
# THE SERVER AND THE SEAM — the same shape as `04-b27-classico.py`.
# ---------------------------------------------------------------------------
class Collection:
    def __init__(self):
        self.lines = []
        self.phase = "F-nessuna"
        self.block = threading.Lock()
        self.byte = 0

    def mark(self, phase):
        with self.block:
            self.phase = phase
            self.lines.append({"t": time.time(), "phase": phase, "mark": True})

    def add(self, data):
        with self.block:
            self.byte += len(data)
            self.lines.append({"t": time.time(), "phase": self.phase, "hex": data.hex()})

    def zoom(self, phase, z):
        with self.block:
            self.lines.append({"t": time.time(), "phase": phase, "zoom": z})


def server(port, collection, page_html):
    class H(http.server.BaseHTTPRequestHandler):
        protocol_version = "HTTP/1.1"

        def log_message(self, *a):
            pass

        def _body(self, kind, data, state=200):
            self.send_response(state)
            self.send_header("Content-Type", kind)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            p = self.path.split("?")[0].split("#")[0]
            if p == "/":
                self._body("text/html; charset=utf-8", page_html)
            else:
                self._body("text/plain", b"not here", 404)

        def do_POST(self):
            n = int(self.headers.get("Content-Length") or 0)
            data = self.rfile.read(n)
            p = self.path.split("?")[0]
            if p == "/byte":
                collection.add(data)
            elif p == "/fase":
                collection.mark(data.decode("utf-8", "replace"))
            self._body("text/plain", b"ok")

    # ⛔ `allow_reuse_address` must be set on the CLASS: `TCPServer.__init__` binds
    #    the port at once, and `server_bind()` reads the attribute BEFORE it can be
    #    written on the instance.  ⚠ Written afterwards, it has no effect — and the
    #    symptom is «Address already in use» on the next run, with the port that
    #    `ss` declares free because it is only in TIME_WAIT.
    class _Server(socketserver.ThreadingTCPServer):
        allow_reuse_address = True
        daemon_threads = True

    s = _Server(("127.0.0.1", port), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


# ---------------------------------------------------------------------------
# ⛔⭐ THE BROWSER DRIVER, WITH RECONNECTION.
#
# `[M]` 14 Aug 2026, Chrome 151.0.7922.137: `Input.dispatchTouchEvent`
# **does not return** under some conditions (after a mouse event, and after a
# recycled contact identifier).  ⇒ The first run of this bench died
# halfway and threw away sixteen good measurements for a defect of the driver.
#
# ⛔ And we do not pretend it did not happen: every reconnection ends up in `faults`,
#    which goes into the outcomes log — so a red can be attributed to the
#    tool instead of to the product (`CODER.md` §3.10, §3.11).
# ---------------------------------------------------------------------------
class Driver:
    def __init__(self, module, url, timeout=20):
        self._m = module
        self._url = url
        self._t = timeout
        self.c = module.Cdp(url, timeout)
        self.faults = []

    def reattaches(self, why):
        self.faults.append(why)
        try:
            self.c.close()
        except Exception:                      # noqa: BLE001
            pass
        time.sleep(0.6)
        self.c = self._m.Cdp(self._url, self._t)
        self.c.call("Runtime.enable")
        try:
            self.c.call("Emulation.setTouchEmulationEnabled",
                          enabled=True, maxTouchPoints=5)
        except Exception:                      # noqa: BLE001
            pass

    def call(self, method, **p):
        return self.c.call(method, **p)

    def evaluate(self, e, should_wait=True):
        return self.c.evaluate(e, should_wait)


def _cdp():
    p = os.path.join(HERE, "02-page-measure-cdp.py")
    spec = importlib.util.spec_from_file_location("cdpmod", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# ⛔ The seam that the `F4-TOUCH` anchor asks for, put in by the bench.  It is the same
#    as in `04-b27-classico.py`: the coordinator will write it in `connect()` on the
#    unidirectional stream of §2.5, here it sends to this process.
#    ⚠ It is the only difference between bench and product, and it is declared: the
#      TRANSPORT is not measured here.
PROLOGUE = r"""
(function () {
  var n = 0, coda = Promise.resolve();
  window.__b28 = { spediti: 0, errori: [] };
  window.REMOTIX_INPUT = {
    prossimo_id: function () { n = (n >= 4294967295) ? 1 : n + 1; return n; },
    manda: function (tipo, corpo) {
      var m = new Uint8Array(6 + corpo.length);
      var v = new DataView(m.buffer);
      v.setUint16(0, tipo); v.setUint32(2, corpo.length); m.set(corpo, 6);
      window.__b28.spediti++;
      coda = coda.then(function () { return fetch("/byte", { method: "POST", body: m }); })
                 .catch(function (e) { window.__b28.errori.push(String(e)); });
    },
  };
  window.__b28.fase = function (nome) {
    coda = coda.then(function () { return fetch("/fase", { method: "POST", body: nome }); })
               .catch(function (e) { window.__b28.errori.push(String(e)); });
    return coda;
  };
  window.__b28.attendi = function () { return coda.then(function () { return true; }); };
  /* ⛔⭐ THE SPY — `CODER.md` §3.7: «the sender is not deduced: it is asked».
     It records what the BROWSER really delivered to the page, so a
     red of the automatic switch can be attributed — to the product, or to the bench
     that did not deliver the event it believed it had sent.
     ⚠ These are the bench's observations on Chrome: no verdict is built on
       these fields, they serve to say WHERE to look. */
})()
"""

# ⛔⭐ THE SPY OF THE SWITCH TAB — `CODER.md` §3.7: «the sender is not
#     deduced: it is asked of the core».  It records what the BROWSER
#     really delivered to the page, so a red of the switch can be
#     attributed: to the product, or to the bench that did not deliver the event.
# ⚠ It is PASSIVE: a non-passive listener on `touchstart` blocks
#   `Input.dispatchTouchEvent` — measured on 14 Aug 2026.
SPY = r"""
(function () {
  window.__spia = [];
  var p = { capture: true, passive: true };
  addEventListener("pointerdown", function (e) {
    window.__spia.push(["pointerdown", e.pointerType]); }, p);
  addEventListener("touchstart", function (e) {
    window.__spia.push(["touchstart", e.touches.length]); }, p);
  addEventListener("mousedown", function () {
    window.__spia.push(["mousedown", 0]); }, p);
})()
"""

# ⛔ The page's scene: the canvas is switched on and given a KNOWN frame, or
#    we would not know where to touch.  ⚠ It is what `04-b27` does for the classic one.
SCENA = r"""
(function () {
  document.body.dataset.viewer = "on";
  const t = document.getElementById("viewer");
  t.width = %d; t.height = %d;
  t.style.width = "960px"; t.style.height = "540px";
  const s = window.REMOTIX && window.REMOTIX.touch;
  if (!s) return JSON.stringify({error: "⛔ REMOTIX.touch does not exist"});
  const r = t.getBoundingClientRect();
  return JSON.stringify({ layout: document.body.dataset.layout,
                          why: s.why(), context: s.context(),
                          thresholds: s.thresholds, state: s.state(),
                          border: [r.left, r.top, r.width, r.height] });
})()
"""


def runs(port, diagnosis, outcomes_f, log_f, wait=30):
    cdp = _cdp()
    with open(os.path.join(ROOT, "src", "page.html"), "rb") as f:
        html = f.read()
    for key, value in ((b"__FINGERPRINT__", b""), (b"__WARNING__", b""),
                           (b"__BANNED__", b"no"), (b"__REMAINING_MS__", b"0")):
        html = html.replace(key, value)
    collection = Collection()
    s = server(port, collection, html)
    print("  server on http://127.0.0.1:%d — the PRODUCT's page, %d bytes"
          % (port, len(html)))

    b = cdp.page(diagnosis, wait)
    c = Driver(cdp, b["webSocketDebuggerUrl"], timeout=20)
    c.call("Page.enable")
    c.call("Runtime.enable")
    c.call("Page.addScriptToEvaluateOnNewDocument", source=PROLOGUE)
    # ⛔ Touch is DECLARED: without it, a desktop Chrome delivers no
    #    `Touch` event and the bench would measure its own silence.
    c.call("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
    # ⛔⭐ THE WINDOW MUST BE IN FRONT AND ACTIVE, AND IT IS NOT A WHIM.
    #  `[M]` 14 Aug 2026: `Input.dispatchTouchEvent` **does not return**
    #  intermittently, in different phases on every run.  The bench runs on the
    #  user's REAL desktop (that is what the mandate asks): when the window
    #  ends up behind another one, the renderer stops producing frames — it is the
    #  same fact that `STUDIES.md` §web §6.2 measures on Xvfb, «without a screen there is no
    #  scanout» — and the acknowledgement of the input event never arrives.
    #  ⇒ The page is told that it has the focus, and the window is brought
    #    to the front.  ⚠ It is a declaration about the SCENE, not a cure of the
    #    product: the stage is declared, not moved.
    try:
        c.call("Emulation.setFocusEmulationEnabled", enabled=True)
    except Exception:                          # noqa: BLE001
        print("  ⚠ this Chrome does not have `setFocusEmulationEnabled`")
    try:
        c.call("Page.bringToFront")
    except Exception:                          # noqa: BLE001
        pass
    c.call("Page.navigate",
             url="http://127.0.0.1:%d/?layout=touch" % port)
    time.sleep(2.0)

    scene = {
        "machine": os.uname().nodename,
        "session": os.environ.get("XDG_SESSION_TYPE"),
        "wayland": os.environ.get("WAYLAND_DISPLAY"),
        "display": os.environ.get("DISPLAY"),
        "browser": c.evaluate("navigator.userAgent"),
        "canvas": list(TELA),
        "when": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    is_on = c.evaluate(SCENA % TELA)
    if not is_on:
        print("  ⛔ the page did not answer the scene")
        s.shutdown()
        return 3, scene, []
    page_map = json.loads(is_on)
    scene["page"] = page_map
    print("  scene:", json.dumps(scene, ensure_ascii=False)[:600])
    if page_map.get("error"):
        print("  " + page_map["error"])
        s.shutdown()
        return 3, scene, []
    if page_map.get("layout") != "touch":
        print("  ⛔ the layout in force is «%s», not «tocco»: the bench "
              "would measure the other half of the page" % page_map.get("layout"))
        s.shutdown()
        return 3, scene, []

    cx, cy, cw, ch = page_map["border"]
    ox, oy = cx + cw / 2, cy + ch / 2      # the centre of the canvas, in CSS px

    # ── THE SYNTHETIC HAND ─────────────────────────────────────────────────
    # ⛔ CDP wants the ACTIVE points at every event: at `touchEnd` the ones
    #    that REMAIN are sent, and the released one is omitted.  Getting it wrong
    #    means measuring a hand that nobody ever made.
    #
    # ⛔⭐ AND EVERY NEW CONTACT TAKES A NEW IDENTIFIER — `[M]` 14 Aug
    #     2026, and the line was born from a HANG of the bench, not from reasoning.
    #
    #  Reusing identifier `1` for the second contact of the tap-and-a-half,
    #  `Input.dispatchTouchEvent` **no longer returned**: the CDP call timed out
    #  at the first `touchMove` after the finger landed again, reproducibly (case C5b,
    #  two runs out of two).  ⛔ It is a defect of the TOOL, not of the product.
    #
    # ⭐ And the new identifier is also truer to reality: a touch
    #    panel assigns a NEW `tracking id` to every new contact, and does not
    #    recycle the one just released.  ⇒ The bench now tests the tap-and-a-half
    #    with two DIFFERENT identifiers, which is what happens with a real
    #    finger — and it necessarily proves that the recogniser links it on SPACE
    #    (40 px) and TIME (300 ms), never on the identity of the contact.
    active = {}
    slots = {}
    upcoming = [100]

    def _send(kind):
        c.call("Input.dispatchTouchEvent", type=kind,
                 touchPoints=[{"x": float(v[0]), "y": float(v[1]), "id": k}
                              for k, v in active.items()])

    def down(i, x, y):
        upcoming[0] += 1
        slots[i] = upcoming[0]
        active[slots[i]] = (ox + x, oy + y)
        _send("touchStart")

    def move_to(points):
        for i, x, y in points:
            if i in slots:
                active[slots[i]] = (ox + x, oy + y)
        _send("touchMove")

    def su(i):
        active.pop(slots.pop(i, None), None)
        _send("touchEnd")

    def sleep_ms(ms):
        time.sleep(ms / 1000.0)

    def phase(name):
        c.evaluate("window.__b28.attendi()")
        c.evaluate("window.__b28.fase(%s)" % json.dumps(name))
        c.evaluate("window.__b28.attendi()")

    def zoom_reset():
        # ⚠ It is not a product switch: it is a reversed PINCH,
        #   made with the same synthetic fingers, to bring the view back to 1x.
        down(80, -150, 0)
        down(81, 150, 0)
        for k in range(1, 7):
            move_to([(80, -150 + 24 * k, 0), (81, 150 - 24 * k, 0)])
            sleep_ms(16)
        su(80)
        su(81)
        sleep_ms(60)

    def read_zoom(name):
        z = c.evaluate("window.REMOTIX.touch.state().zoom")
        collection.zoom(name, z if isinstance(z, (int, float)) else 0)

    def idle():
        # ⛔ Beyond `T_SEQUENZA` (300 ms), or the next gesture would link as a
        #    tap-and-a-half to the previous one: it is exactly the trap the bench
        #    must avoid walking into by itself.
        sleep_ms(450)

    # ══════════════════════════════════════════════════════════════════════
    # THE SCENES, ONE FUNCTION PER GESTURE.
    #
    # ⛔ AND EVERY SCENE IS PROTECTED: a fault of the TOOL (the CDP call
    #    that does not return) must not throw away the other sixteen measurements, and ⛔ it
    #    must not pass for an outcome either.  ⇒ We reconnect, cancel the
    #    touch in progress, the phase stays WITHOUT bytes — and the judge declares it
    #    red with «the phase was not recorded at all», which is the truth.
    #    ⚠ `CODER.md` §3.10: «a denied reading is not a reading that says
    #      zero».  The faults end up in `04-b28-outcomes.jsonl` under `faults`,
    #      so a red can be attributed to the bench instead of to the product.
    # ══════════════════════════════════════════════════════════════════════

    def f_G1():
        down(1, -200, 0)
        for k in range(1, 11):
            move_to([(1, -200 + 20 * k, 0)])
            sleep_ms(16)
        su(1)

    def f_G2():
        down(1, 0, 0)
        sleep_ms(80)
        su(1)

    def f_G3():
        down(1, -30, 0)
        down(2, 30, 0)
        sleep_ms(80)
        su(1)
        su(2)

    def _two_fingers_go_down():
        down(1, -30, -100)
        down(2, 30, -100)
        for k in range(1, 9):
            move_to([(1, -30, -100 + 25 * k), (2, 30, -100 + 25 * k)])
            sleep_ms(16)
        su(1)
        su(2)

    def f_G4():
        # The fingers go DOWN ⇒ `RCP.md` §7.3 wants the vertical axis POSITIVE.
        _two_fingers_go_down()

    def f_G5():
        down(1, 0, 0)
        sleep_ms(80)
        su(1)
        sleep_ms(90)            # within the 300 ms of T_SEQUENZA
        down(1, 3, 3)         # and within the 40 px of D_STESSO_DITO
        sleep_ms(30)
        for k in range(1, 9):
            move_to([(1, 3, 3 + 20 * k)])
            sleep_ms(16)
        su(1)

    def f_G6():
        # ⛔⭐ HERE IT IS HELD DOWN 20 ms AND NOT 80, AND THE REASON IS MEASURED.
        #
        # `[M]` 14 Aug 2026: with 80 ms of waiting the three-finger tap came out
        # **without a middle click**, and the recogniser was correct.  Direct
        # probe: `durata_max` = **147 ms** against a threshold of 180 — that is, the
        # SYNTHETIC HAND alone costs ~120 ms, because three fingers down and three up
        # are SIX CDP round trips at ~20 ms each.
        #
        # ⇒ The bench was measuring the latency of its own tool, not the
        #   gesture (`LESSONS.md` §1.11).  The wait is removed, and the time that
        #   remains is the real one of the six trips.
        # ⭐ And a question remains for Nic, which no bench closes: **are 180 ms per
        #    contact enough for a three-finger tap made with a real hand?**
        #    Three fingers do not lift together, and this is exactly the case in
        #    which the threshold is judged by using it.
        down(1, -40, 0)
        down(2, 0, 0)
        down(3, 40, 0)
        sleep_ms(20)
        su(1)
        su(2)
        su(3)

    def _move_away():
        down(1, -60, 0)
        down(2, 60, 0)
        for k in range(1, 9):
            move_to([(1, -60 - 15 * k, 0), (2, 60 + 15 * k, 0)])
            sleep_ms(16)
        su(1)
        su(2)
        sleep_ms(60)

    def f_G7():
        _move_away()
        read_zoom("G7-pinch")
        zoom_reset()

    def f_C1():
        # The tap that lasts a bit too long: 400 ms, and STILL.  T_TAP = 180 ms.
        down(1, 0, 0)
        sleep_ms(400)
        su(1)

    def f_C2():
        # The tap that slides: 120 ms, but 30 px.  D_TAP = 9 CSS px.
        down(1, 0, 0)
        for k in range(1, 4):
            move_to([(1, 10 * k, 0)])
            sleep_ms(30)
        su(1)

    def f_C3():
        # ⭐ The two fingers that land 30 ms apart — BUT they
        #    overlap: it is the declared threshold.
        down(1, -30, 0)
        sleep_ms(30)
        down(2, 30, 0)
        sleep_ms(70)
        su(1)
        sleep_ms(20)
        su(2)

    def f_C4():
        # ⛔ And the two fingers that NEVER overlap: the declared defect.
        down(1, -30, 0)
        sleep_ms(90)
        su(1)
        sleep_ms(40)
        down(2, 30, 0)
        sleep_ms(90)
        su(2)

    def f_C5a():
        # Still double tap, same spot ⇒ DOUBLE CLICK.
        down(1, 0, 0)
        sleep_ms(70)
        su(1)
        sleep_ms(90)
        down(1, 2, 2)
        sleep_ms(70)
        su(1)

    def f_C5b():
        # ⭐ The SAME opening, and then it drags ⇒ DRAG.
        down(1, 0, 0)
        sleep_ms(70)
        su(1)
        sleep_ms(90)
        down(1, 2, 2)
        sleep_ms(40)
        for k in range(1, 9):
            move_to([(1, 2 + 18 * k, 2)])
            sleep_ms(16)
        su(1)

    def f_C6():
        # The two-finger drag that starts STILL.
        down(1, -30, -100)
        down(2, 30, -100)
        sleep_ms(350)
        for k in range(1, 9):
            move_to([(1, -30, -100 + 25 * k), (2, 30, -100 + 25 * k)])
            sleep_ms(16)
        su(1)
        su(2)

    def f_C7a():
        _move_away()
        read_zoom("C7a-pinch-not-wheel")
        zoom_reset()

    def f_C7b():
        _two_fingers_go_down()
        sleep_ms(60)
        read_zoom("C7b-wheel-not-pinch")

    def f_C8():
        # The leftover finger: two scroll, one lifts, the other carries on.
        down(1, -30, -100)
        down(2, 30, -100)
        for k in range(1, 5):
            move_to([(1, -30, -100 + 25 * k), (2, 30, -100 + 25 * k)])
            sleep_ms(16)
        su(1)
        for k in range(1, 5):
            move_to([(2, 30 + 20 * k, 0)])
            sleep_ms(16)
        su(2)

    SCENE = [
        ("G1-one-finger-drags", f_G1),
        ("G2-one-finger-tap", f_G2),
        ("G3-two-finger-tap", f_G3),
        ("G4-two-fingers-drag", f_G4),
        ("G5-tap-and-a-half", f_G5),
        ("G6-three-finger-tap", f_G6),
        ("G7-pinch", f_G7),
        ("C1-tap-too-long", f_C1),
        ("C2-tap-that-slides", f_C2),
        ("C3-two-fingers-30ms-apart", f_C3),
        ("C4-two-fingers-without-overlap", f_C4),
        ("C5a-double-click", f_C5a),
        ("C5b-tap-and-a-half-that-drags", f_C5b),
        ("C6-drag-that-starts-still", f_C6),
        ("C7a-pinch-not-wheel", f_C7a),
        ("C7b-wheel-not-pinch", f_C7b),
        ("C8-the-leftover-finger", f_C8),
    ]
    assert sorted(n for n, _ in SCENE) == sorted(CASES), \
        "the scenes and the judge's cases do not match"

    verdicts = {}
    phase_faults = []
    for name, fn in SCENE:
        # ⛔ ONE ATTEMPT ONLY, and the second is NOT made.  On a retry, the bytes of the
        #    half-successful attempt stay in the phase and add up to those
        #    of the second: the judge read «three left-button events out of
        #    four» on a gesture the product had done right twice.
        #    ⇒ A fault of the tool is DECLARED, not hidden with a
        #      repetition (`CODER.md` §3.10: «a denied reading is not a
        #      reading that says zero»).
        for attempt in (1,):
            try:
                phase(name)
                fn()                # ⛔ The verdict the PAGE gave to the gesture, with its numbers:
                #    when a case is red, it says which condition gave way —
                #    duration, smear or decision — instead of leaving it to be deduced.
                try:
                    verdicts[name] = json.loads(c.evaluate(
                        "JSON.stringify(window.REMOTIX.touch.state().last_gesture)")
                        or "null")
                except Exception:              # noqa: BLE001
                    pass
                break
            except (TimeoutError, OSError, RuntimeError) as e:
                print("  ⚠ TOOL FAULT in phase %s (%s)"
                      % (name, type(e).__name__))
                phase_faults.append(name)
                c.reattaches("phase %s: %s" % (name, type(e).__name__))
                active.clear()
                slots.clear()
                try:
                    c.call("Input.dispatchTouchEvent", type="touchCancel",
                             touchPoints=[])
                except Exception:              # noqa: BLE001
                    pass
                sleep_ms(400)
        idle()

    phase("F-end")

    c.evaluate("window.__b28.attendi()")
    time.sleep(0.5)

    # ── ⒝ THE AUTOMATIC SWITCH, and S1 the seam ─────────────────────────────
    hover = measure_crossing(c, cdp, port, ox, oy, diagnosis)
    scene["hover"] = hover
    scene["page_verdicts"] = verdicts
    scene["instrument_faults"] = list(c.faults)
    if c.faults:
        print("  ⚠ %d tool faults, reconnected: %s"
              % (len(c.faults), c.faults))

    with collection.block:
        lines = list(collection.lines)
    s.shutdown()

    with open(log_f, "w", encoding="utf-8") as f:
        for r in lines:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    outcomes = judge(lines)
    outcomes += hover["outcomes"]
    # ⛔ The phases in which the TOOL failed are not counted among the product's
    #    reds — and they are not counted among the greens either.  They stay NOT
    #    MEASURED, with a mark all their own, and the bench exits with a different
    #    code: «to be redone», not «the product is broken».
    for e in outcomes:
        if e["case"] in phase_faults:
            e["strumento"] = True
    return 0, scene, outcomes


# ⛔ The switch is measured on WHICH LAYOUT IS IN FORCE, read from the
#    document — not «there is a function that changes it».
def measure_crossing(c_old, cdp, port, ox, oy, diagnosis):
    """⛔⭐ THE SWITCH IS MEASURED IN A NEW TAB, AND IT IS NOT A CONVENIENCE.

    `[M]` 14 Aug 2026, Chrome 151.0.7922.137.  Measuring the switch in the
    **same** tab as the gestures — that is, after a second `Page.navigate` and after
    a mouse event — ⛔ `Input.dispatchTouchEvent` **no longer delivers
    anything to the page**: the prologue's spy records neither a `touchstart`
    nor a `pointerdown` of type `touch`, and the CDP call returns without error.
    ⇒ The bench read «after a FINGER: classico» and blamed the PRODUCT.

    ⭐ In a freshly opened tab the same sequence works, and the switch
       is measured in full: start → **tocco**, mouse → **classico**, finger →
       **tocco**.  ⚠ `CODER.md` §3.11: suspicion goes first to the measurement.
    """
    import urllib.request
    outcomes, note = [], {}

    # A new tab, its own, closed at the end.
    with urllib.request.urlopen(urllib.request.Request(
            "http://127.0.0.1:%d/json/new?about:blank" % diagnosis,
            method="PUT"), timeout=10) as r:
        card = json.loads(r.read().decode())
    c = Driver(cdp, card["webSocketDebuggerUrl"], timeout=20)
    c.call("Page.enable")
    c.call("Runtime.enable")
    c.call("Page.addScriptToEvaluateOnNewDocument", source=SPY)
    c.call("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)

    # ⛔⭐ A DEFECT OF THE TOOL, MEASURED AND WORKED AROUND — `[M]` 14 Aug 2026,
    #     Chrome 151.0.7922.137 on CHUWI.
    #
    # After an `Input.dispatchMouseEvent`, the following `Input.dispatchTouchEvent`
    # **never returns**: the CDP call times out waiting for an answer that never
    # arrives.  ⇒ The first run of this bench read «after a TOUCH: classico»
    # and blamed the PRODUCT for not going back to touch.
    #
    # ⚠ `CODER.md` §3.11 — «when code read and measurement contradict each other, the
    #   suspicion goes FIRST to the measurement».  Here the code said the switch
    #   was there and the measurement said no: the code was right.
    #
    # ⭐ The cure: touch emulation is switched on again after every mouse event.
    #    Measured: start «touch» → finger «touch» → mouse «classico» → finger
    #    «touch».  ⛔ And it is declared here instead of hidden in a line.
    def mouse():
        c.call("Input.dispatchMouseEvent", type="mousePressed", x=ox, y=oy,
                 button="left", clickCount=1, buttons=1)
        c.call("Input.dispatchMouseEvent", type="mouseReleased", x=ox, y=oy,
                 button="left", clickCount=1, buttons=0)
        time.sleep(0.3)
        c.call("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)

    # ⚠ A NEW identifier at every contact, as in the synthetic hand: a recycled
    #   id blocks `Input.dispatchTouchEvent` (measured, see above).
    finger_id = [200]

    def finger(pt=None):
        finger_id[0] += 1
        # ⛔ Touch emulation is switched ON AGAIN before every contact — `[M]`
        #    14 Aug 2026, and the page's spy is the one that said so:
        #    after the second navigation and after a mouse event the
        #    `touchStart` events NO LONGER reached the page (no `touchstart`
        #    and no `pointerdown` of type touch in the spy), and the bench
        #    blamed the PRODUCT for not going back to touch.  ⚠ `CODER.md` §3.7:
        #    the sender is not deduced, it is asked.
        c.call("Emulation.setTouchEmulationEnabled", enabled=True,
                 maxTouchPoints=5)
        c.call("Input.dispatchTouchEvent", type="touchStart",
                 touchPoints=[{"x": pt[0] if pt else ox, "y": pt[1] if pt else oy,
                               "id": finger_id[0]}])
        c.call("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
        time.sleep(0.3)

    def layout():
        return c.evaluate("document.body.dataset.layout")

    def state():
        v = c.evaluate("JSON.stringify(window.REMOTIX.touch.state())")
        return json.loads(v) if v else {}

    def shipped():
        return c.evaluate("window.__b28.spediti") or 0

    # ── D1 · the forced layout is really in force, and touch speaks ────────
    #    ⚠ It is read on the GESTURES tab, not on the new one.
    d = c_old.evaluate("document.body.dataset.layout")
    outcomes.append({"case": "D1-layout-in-effect", "green": d == "touch",
                  "why": "`body[data-layout]` = «%s» (the PRODUCT "
                            "wrote it, not the bench)" % d})

    # ── D2 · ⭐ THE REAL SWITCH, on REAL events ──────────────────────────
    # The forcing is removed by reloading without `?layout`, then the
    # mouse is used (⇒ classico) and then the finger (⇒ touch).  ⛔ No hardware
    # is emulated: events are sent that the browser delivers like any other.
    c.call("Page.navigate", url="http://127.0.0.1:%d/" % port)
    time.sleep(2.0)
    c.evaluate(SCENA % TELA)
    d0 = layout()
    note["allavvio"] = {"layout": d0,
                        "why": c.evaluate("window.REMOTIX.touch.why()"),
                        "context": json.loads(
                            c.evaluate("JSON.stringify(window.REMOTIX.touch.context())"))}

    finger()
    d_finger0 = layout()
    mouse()
    d_mouse = layout()
    finger()
    d_finger = layout()

    note["indicator"] = json.loads(c.evaluate("JSON.stringify(window.__spia)") or "[]")
    green = (d_finger0 == "touch" and d_mouse == "classic" and d_finger == "touch")
    outcomes.append({"case": "D2-automatic-switch", "green": green,
                  "why": ("at start «%s»; after a FINGER «%s»; after a mouse "
                             "CLICK «%s»; after another FINGER «%s»"
                             % (d0, d_finger0, d_mouse, d_finger))
                            + ("" if green else
                               "  ⛔ expected tocco → classico → tocco; the spy says: %s"
                               % note["indicator"][-8:])})

    # ── D3 · ⭐ «in force» means the OTHER ONE IS OFF ────────────────
    # In classic, a complete touch must NOT produce any touch
    # message: the handlers are really detached, not just declared detached.
    mouse()
    if layout() != "classic":
        outcomes.append({"case": "D3-the-other-is-off", "green": False,
                      "why": "could not get back into classic"})
    else:
        # ⛔ Before: in CLASSIC the touch one must be off and the classic one on.
        t_before = json.loads(c.evaluate("JSON.stringify(window.REMOTIX.touch.state())"))
        cl_before = json.loads(c.evaluate(
            "JSON.stringify(window.REMOTIX.classic_input.state())"))
        before = c.evaluate("window.REMOTIX.touch.sent.length")
        c.call("Input.dispatchTouchEvent", type="touchStart",
                 touchPoints=[{"x": ox - 100, "y": oy, "id": 7}])
        for k in range(1, 6):
            c.call("Input.dispatchTouchEvent", type="touchMove",
                     touchPoints=[{"x": ox - 100 + 30 * k, "y": oy, "id": 7}])
            time.sleep(0.02)
        c.call("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
        time.sleep(0.3)
        after = c.evaluate("window.REMOTIX.touch.sent.length")
        cl = json.loads(c.evaluate(
            "JSON.stringify(window.REMOTIX.classic_input.state())"))
        newcomers = json.loads(c.evaluate(
            "JSON.stringify(window.REMOTIX.touch.sent.slice(%d))" % before) or "[]")
        d_fin = layout()
        # ⛔⭐ «IN FORCE» MEANS THE OTHER ONE IS OFF, and it is proven on three
        #    observable facts, not on a variable that says so:
        #
        #   1. before the gesture, in CLASSIC: touch is off and classic
        #      on — the two halves are never on together;
        #   2. after the gesture, in TOUCH: classic is off;
        #   3. ⛔ and the drag started IN THE OTHER layout produces
        #      **no ghost click**: it may move the pointer (the
        #      contact is what switches to touch, and it is right that the
        #      gesture is not lost), but a BUTTON in there would mean
        #      that half a gesture was taken for a whole gesture.
        click = [m for m in newcomers if m.get("name") == "BUTTON"]
        green = (t_before.get("in_effect") is False
                 and cl_before.get("in_effect") is True
                 and d_fin == "touch" and not cl.get("in_effect")
                 and not click)
        outcomes.append({"case": "D3-the-other-is-off", "green": green,
                      "why": ("in classic: touch in force %s, classic in "
                                 "force %s; after the gesture: layout «%s», "
                                 "classic in force %s; the gesture produced %d "
                                 "messages, of which %d BUTTON (ghost click)"
                                 % (t_before.get("in_effect"),
                                    cl_before.get("in_effect"), d_fin,
                                    cl.get("in_effect"), after - before, len(click)))})

    # ── S1 · ⭐ THE SEAM between the two anchors ────────────────────────────
    c.call("Input.dispatchTouchEvent", type="touchStart",
             touchPoints=[{"x": ox, "y": oy, "id": 5}])
    for k in range(1, 6):
        c.call("Input.dispatchTouchEvent", type="touchMove",
                 touchPoints=[{"x": ox + 25 * k, "y": oy, "id": 5}])
        time.sleep(0.02)
    c.call("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
    time.sleep(0.3)
    st = state()
    is_visible = c.evaluate(r"""
      (function () {
        const nomi = ["pointer", "puntatore-di-ripiego"];
        for (const n of nomi) {
          const e = document.getElementById(n);
          if (e && getComputedStyle(e).display !== "none"
                && e.getBoundingClientRect().width > 0) return n;
        }
        return null;
      })()""")
    # ⛔ TWO DISTINCT THINGS, and confusing them would hide the more important one:
    #   S1a  the user SEES a pointer while dragging            (invariant I8)
    #   S1b  and sees it without FALLBACK, i.e. the seam holds  (the F5 lesson)
    outcomes.append({"case": "S1a-the-pointer-shows", "green": bool(is_visible),
                  "why": "in touch layout the visible pointer is «%s»"
                            % is_visible})
    outcomes.append({"case": "S1b-seam-without-fallback",
                  "green": bool(st.get("pointer_stitched"))
                           and not st.get("pointer_seam_broken"),
                  "why": ("`REMOTIX_PUNTATORE` is there: %s; seam broken: %s"
                             % (st.get("pointer_stitched"),
                                st.get("pointer_seam_broken")))
                            + ("" if not st.get("pointer_seam_broken") else
                               "  ⛔ `move_to()` does not turn on `cl_known`: in touch the "
                               "shared pointer stays invisible — a cure of ONE "
                               "line in the F4-CLASSIC-INPUT anchor (link A7)")})
    outcomes.append({"case": "S2-classic-seam",
                  "green": bool(st.get("classic_stitched")),
                  "why": "`REMOTIX_CLASSICO` (F4-CLASSIC-INPUT anchor, link A7): %s"
                            % st.get("classic_stitched")})

    # ── D4 · the context is NOT the operating system ──────────────────────
    with open(os.path.join(ROOT, "src", "page.html"), encoding="utf-8") as f:
        text = f.read()
    a = text.split("ANCHOR F4-TOUCH — START")[-1].split("ANCHOR F4-TOUCH — END")[0]
    # ⛔ Comments are removed BEFORE searching, and it is not a nicety: the first
    #    run of this check was red on a comment line that said
    #    «`navigator.userAgent` does not appear here».  A check that reads its
    #    own explanations measures the prose, not the code.
    import re as _re
    code = _re.sub(r"/\*.*?\*/", "", a, flags=_re.S)
    code = _re.sub(r"^\s*//.*$", "", code, flags=_re.M)
    culprits = [s for s in ("userAgent", "navigator.platform", "userAgentData")
                 if s in code]
    outcomes.append({"case": "D4-the-context-is-not-the-system", "green": not culprits,
                  "why": ("in the F4-TOUCH anchor nothing appears that comes from the "
                             "operating system" if not culprits
                             else "⛔ they appear: %s" % culprits)})

    try:
        urllib.request.urlopen(
            "http://127.0.0.1:%d/json/close/%s" % (diagnosis, card["id"]),
            timeout=5).read()
    except Exception:                          # noqa: BLE001
        pass
    note["card_faults"] = list(c.faults)
    return {"outcomes": outcomes, "notes": note}


# ---------------------------------------------------------------------------
def show(outcomes):
    faults = [e for e in outcomes if e.get("strumento")]
    measured = [e for e in outcomes if not e.get("strumento")]
    greens = sum(1 for e in measured if e["green"])
    rossi = [e for e in measured if not e["green"]]
    for e in outcomes:
        sign = "⚠ " if e.get("strumento") else ("✅" if e["green"] else "⛔")
        print("  %s %-38s %s" % (sign, e["case"], e["why"]))
    print("\n  %d green out of %d measured" % (greens, len(measured)))
    if faults:
        print("  ⚠ %d NOT MEASURED because of a tool fault: %s"
              % (len(faults), [e["case"] for e in faults]))
        print("    (⛔ they are neither green nor red: the run is redone)")
    if rossi:
        return 1
    return 2 if faults else 0


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--certify", action="store_true")
    a.add_argument("--run", action="store_true")
    a.add_argument("--verdict")
    a.add_argument("--port", type=int, default=7671)
    a.add_argument("--diagnosis", type=int, default=7672)
    a.add_argument("--outcomes", default=os.path.join(HERE, "04-b28-outcomes.jsonl"))
    a.add_argument("--log", default=os.path.join(HERE, "04-b28-register.jsonl"))
    o = a.parse_args()

    if o.certify:
        return certify()
    if o.verdict:
        lines = [current_spelling(json.loads(r)) for r in open(o.verdict, encoding="utf-8") if r.strip()]
        return show(judge(lines))
    if o.run:
        code, scene, outcomes = runs(o.port, o.diagnosis, o.outcomes, o.log)
        if code:
            return code
        with open(o.outcomes, "a", encoding="utf-8") as f:
            f.write(json.dumps({"scene": scene, "outcomes": outcomes},
                               ensure_ascii=False) + "\n")
        return show(outcomes)
    a.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
