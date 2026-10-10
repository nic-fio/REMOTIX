#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c23 — ⭐⭐ «SHIFT AND ARROWS SELECT»
===========================================================================

    python3 11-c23-maiusc-e-frecce-selezionano.py --container_box gnome [--browser firefox,chrome]
    python3 11-c23-maiusc-e-frecce-selezionano.py --container_box lxqt --port 8524 \\
            --container rete14-lxqt            # a development box
    python3 11-c23-maiusc-e-frecce-selezionano.py --container_box gnome --no-shift
    python3 11-c23-maiusc-e-frecce-selezionano.py --certify

    what must be true         : Shift+arrows SELECT in the remote desktop,
                                and Shift does not stay stuck — on GNOME,
                                KDE, XFCE and LXQt (the user, 24 Sep 2026:
                                «one last check remains: that selection
                                with Shift+arrows is implemented on all the
                                DEs»)
    where it starts from      : ⛔ from scratch, a NEW tenant (`c23u<n>`)
    what it looks at          : ⛔ **THE PHOTOGRAPH** of the remote field: the value
                                is read from the canvas pixels, not from an
                                event counter
    how I know it can give red: `--no-shift` (the same sequences without ever
                                pressing Shift: no selection) ⇒ RED

⛔⛔ WHY IT EXISTS.
   `[M]` 24 Sep 2026, on all four desktops: Shift+Left left
   the page as `105↓ 105↑` — the Shift already down was recovered only if
   there was also Ctrl/Alt/Super ⇒ the arrow moved the cursor and did NOT
   select.  And after a letter typed with Shift down the page believed
   Shift still pressed while the server had already released it.  The cure
   is in `src/pagina.html` (`cl_su_keydown`, commit 694f77f, two halves); this
   mesh is the test that remains, on the four desktops.
   ⚠ With the REAL BROWSERS (the user, 23 Sep 2026: *«the tests must be done with the
     real browsers, not with emulators»*): the defect was precisely in the way
     the page reads THE BROWSER's events (`getModifierState`, `ev.code`), and
     the Python client does not have those events.

⭐ WHAT IT DOES, for each browser (Firefox with Marionette, Chrome with CDP: the
   drivers are those of `banchi/12-client-veri.py`, the box that of
   `banchi/12-c20-veri.py`, the wake-up and the geometry those of
   `11-c21-sul-bordo-la-forma-cambia.py` — ⛔ imported, not copied):
     1  creates the tenant `c23u<n>`, logs in, waits for the first frame
     2  C21's WAKE-UP (a real ESC: on GNOME the session is born in the
        overview)
     3  in the session starts a small server (`python3`) and
        `firefox-esr --kiosk` on the SCENE: an <input> always focused
     4  for each case (`CASES`): cleans the field (Ctrl+A, Backspace),
        types the BASE, and then the sequence to test — with REAL KEYS given to the
        browser (`WebDriver:PerformActions`, `Input.dispatchKeyEvent`)
     5  photographs the canvas and READS the value of the field from the pixels

⭐⭐ THE SCENE — the value shows, twice.
   · IN LARGE, in the field itself: it is for whoever looks at the saved photographs
     (`--store`), that is for the user.
   · AND AS A STRIP OF COLOURS under the field: one box per character, of the
     colour `ALPHABET` gives to that character (and grey `EMPTY` where the
     value has ended), between two white MARK boxes.  ⇒ The mesh reads
     the value from the photograph without recognising the letters: it takes the colour
     at the centre of each box and looks for the nearest in the palette.
     ⛔ The palette is written ONCE, here, and put into the page: the
       colour the page paints and the one the judge looks for cannot
       diverge (the same reason as C4's scene).
     ⚠ The colours are the 27 vertices and midpoints of the RGB cube (0, 128, 255 per
       channel): two colours are at least 127 apart, and the tolerance is 60 — the
       chain goes through H.264 4:2:0, which subsamples the chroma (§4.3 of phase
       11), but on boxes of ~270 px the chroma at the centre arrives whole.
   · The server also writes, in a file of the tenant, every keydown of the
     remote page and every value of the field: ⛔ it does NOT judge — it is the diagnosis
     of the red (which key arrived, with which Shift).

⭐ THE CASES — those of the cure, measured on 24 Sep 2026 on rete14-lxqt:
     1  «abcdef», Shift+Left×3, Y                     ⇒ «abcY»
     2  «uno due», Ctrl+Shift+Left, z                  ⇒ «uno z»
     3  «abcdef», Shift down, Left, A, Shift up, b
                                                      ⇒ «abcdeAb»
        (the risky case: after the letter Shift does NOT stay stuck,
         and the «b» comes out lowercase)
     4  «abcdef», Shift down, Left, A, Left×2, X, Shift up, q
                                                      ⇒ «abcdXq»
        (the second half of the cure: AFTER the letter, with Shift still down,
         the arrows still select.  `[M]` without that half ⇒ «abcdXqeA»)
   ⭐ The expected value is not only written by hand: `simulate()` applies the sequence to a
     fake text field, and `--certify` checks that it gives the expected value — and that
     the same sequence WITHOUT Shift gives something else (the fault shows).

⛔ THE THREE POOR CHECKS, for each case:
     1  after the cleaning the strip is there and is EMPTY  — if not, 3: the scene is not
        in force (or the field does not clean) and does not bear witness
     2  after the base the strip says THE BASE          — if not, 3: if
        plain typing does not arrive it is C4's, not C23's; and so a red
        here comes ONLY from the selection
     3  after the sequence the strip says THE EXPECTED VALUE — if not, RED, with the
        value seen and the tail of the remote keydowns
   ⚠ It photographs several times until `WAIT_S`: here latency is not measured,
     and a late frame is not a selection defect.

⛔ HOW I KNOW IT CAN GIVE RED — `--no-shift`.
   The same sequences, with the «Shift down» and «Shift up» removed: the letters
   keep their form (the «Y» is still «Y»), ⇒ the only difference is
   that the arrows move instead of selecting, and every case must give RED.
   ⛔ It reads THE OTHER WAY ROUND, like every fault of the net (`11-gancio.sh`,
     `run_mesh`): 0 = the fault was SEEN (all cases red),
     1 = NOT seen (a case came out right anyway), 3 = I could not look.

⚠ OUTCOMES: 0 green · 1 red · 3 «I could not look», with the reason.

⚠ WHERE IT RUNS: like C21, on the host with the real browsers (`REMOTIX_ON_SERVER=1`,
  screenless `labwc`), and in the box with `podman exec`.  The tenant is
  `c23u<n>` (C19's pattern `^c[0-9]+b?u[0-9]+$`): if the bench died
  half-way, the hook clears it out.
"""
import argparse
import base64
import importlib.util as _iu
import io
import json
import os
import random
import re
import secrets
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BENCHES = os.path.dirname(HERE)


def _load(label_name, file):
    s = _iu.spec_from_file_location(label_name, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ Imported, not copied: C21 brings `12-c20-veri` (the box) and
#   `12-client-veri` (the browsers) along — only one in memory, and the ESC already in the table.
C21 = _load("c21", os.path.join(HERE, "11-c21-sul-bordo-la-forma-cambia.py"))
C20V = C21.C20V
REAL = C21.REAL
GREEN, RED, BLIND = REAL.GREEN, REAL.RED, REAL.BLIND
PORTS = C20V.PORTS
OUTCOME_NAME = C21.OUTCOME_NAME

TENANT_PATTERN = re.compile(r"^c23u[0-9]+$")

# ---------------------------------------------------------------------------
# ⛔ THE NUMBERS — each with its reason.
# ---------------------------------------------------------------------------
# Between one event and the next: more than a human's shortest repeat, and
# enough for every key to travel on its own (`[M]` c95: 90 ms are enough).
PAUSE_MS = 90
# How long we wait for the photograph to say the value: it is not a latency, it is
# a ceiling beyond which the value no longer arrives.
WAIT_S = 6.0
PHOTO_EVERY_S = 0.7
# The tolerance on a box's colour: half the minimum distance between two
# colours of the palette (127) minus a margin.
TOLERANCE = 60
# ⭐ The strip, in fractions of the kiosk window (= the desktop): wide and
#   in the middle, far from bars and drawers even if the kiosk did not cover them.
CELLS = 14
STRIP_X0, STRIP_X1 = 0.04, 0.96      # from the left mark to the right one
STRIP_Y0, STRIP_Y1 = 0.55, 0.75
# The sample at the centre of each box: +/- this fraction of the box.
SAMPLE = 0.2

# ⭐ THE PALETTE.  Reserved: EMPTY (box without a character), OTHER (a
#   character outside the alphabet, or the value too long), MARK (the two
#   ends of the strip).  The letters take the other colours in order.
EMPTY = (128, 128, 128)
OTHER = (0, 0, 0)
MARK = (255, 255, 255)
ALPHABET = "abcdefnoquxyzAXY "


def _cube():
    levels = (0, 128, 255)
    return [(r, g, b) for r in levels for g in levels for b in levels]


COLORS = {}
for _c in [c for c in _cube() if c not in (EMPTY, OTHER, MARK)][:len(ALPHABET)]:
    COLORS[ALPHABET[len(COLORS)]] = _c
assert len(COLORS) == len(ALPHABET)

# ---------------------------------------------------------------------------
# ⭐ THE KEYS.  A step is («giu»|«su», name).  The letters are written ALREADY
#   in the form the browser reports (`ev.key`): «Y», not «y» + Shift.
#   ⇒ The fault can remove Shift without changing the letters.
# ---------------------------------------------------------------------------
SPECIAL = {
    #  name        key          code          vk  WebDriver   CDP bit
    "Shift":     ("Shift",     "ShiftLeft",   16, "", 8),
    "Control":   ("Control",   "ControlLeft", 17, "", 2),
    "ArrowLeft": ("ArrowLeft", "ArrowLeft",   37, "", 0),
    "Backspace": ("Backspace", "Backspace",    8, "", 0),
}


def press(label_name):
    return [("down", label_name), ("su", label_name)]


def put_out(body_text):
    p = []
    for c in body_text:
        p += press(c)
    return p


def clr(mod, steps):
    """`steps` with the modifier `mod` held down."""
    return [("down", mod)] + steps + [("su", mod)]


CLEAN = clr("Control", press("a")) + press("Backspace")

# (title, base, sequence, expected)
CASES = [
    ("1 Shift+Left×3, Y", "abcdef",
     clr("Shift", press("ArrowLeft") * 3 + press("Y")), "abcY"),
    ("2 Ctrl+Shift+Left, z", "uno due",
     clr("Control", clr("Shift", press("ArrowLeft"))) + press("z"), "uno z"),
    ("3 RISK Shift down, Left, A, Shift up, b", "abcdef",
     clr("Shift", press("ArrowLeft") + press("A")) + press("b"), "abcdeAb"),
    ("4 RISK+ Shift down, Left, A, Left×2, X, Shift up, q", "abcdef",
     clr("Shift", press("ArrowLeft") + press("A") + press("ArrowLeft") * 2 + press("X"))
     + press("q"), "abcdXq"),
]


def no_shift(steps):
    """⛔ THE FAULT: the same sequences without ever pressing Shift."""
    return [p for p in steps if p[1] != "Shift"]


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def simulate(steps, value_v=""):
    """⭐ A fake text field: applies the steps and returns the value.

    The semantics is that of a Firefox/GTK <input>: the letter replaces
    the selection; Left without Shift with a selection closes it at its
    start; Ctrl+Left jumps to the start of the word; Ctrl+A selects
    everything; Backspace deletes the selection or the character before."""
    still = focus = len(value_v)
    down = set()
    for kind, label_name in steps:
        if kind == "su":
            down.discard(label_name)
            continue
        if label_name in ("Shift", "Control"):
            down.add(label_name)
            continue
        a, b = min(still, focus), max(still, focus)
        if label_name == "ArrowLeft":
            if "Control" in down:
                i = focus
                while i > 0 and value_v[i - 1] == " ":
                    i -= 1
                while i > 0 and value_v[i - 1] != " ":
                    i -= 1
                fresh = i
            elif "Shift" not in down and a != b:
                fresh = a
            else:
                fresh = max(0, focus - 1)
            focus = fresh
            if "Shift" not in down:
                still = focus
        elif label_name == "Backspace":
            if a != b:
                value_v = value_v[:a] + value_v[b:]
                still = focus = a
            elif a > 0:
                value_v = value_v[:a - 1] + value_v[a:]
                still = focus = a - 1
        elif "Control" in down:
            if label_name.lower() == "a":
                still, focus = 0, len(value_v)
        else:
            value_v = value_v[:a] + label_name + value_v[b:]
            still = focus = a + len(label_name)
    return value_v


def box_centers():
    """[(fx, fy)] of the centres: mark, CELLS boxes, mark — in fractions."""
    step = (STRIP_X1 - STRIP_X0) / (CELLS + 2)
    fy = (STRIP_Y0 + STRIP_Y1) / 2
    return [(STRIP_X0 + (i + 0.5) * step, fy) for i in range(CELLS + 2)]


def _dist(a, b):
    return max(abs(x - y) for x, y in zip(a, b))


def color_name(c):
    """(name, distance) of the nearest palette colour."""
    all_v = [("MARK", MARK), ("EMPTY", EMPTY), ("OTHER", OTHER)] + \
        [(k, v) for k, v in COLORS.items()]
    k, v = min(all_v, key=lambda kv: _dist(kv[1], c))
    return k, _dist(v, c)


def read_strip(sample):
    """⭐ The value of the field from the photograph.

    `sample(fx, fy, rx, ry)` returns the (median) colour of the rectangle
    centred in (fx, fy) with half-width (rx, ry), in fractions of the desktop.
    Returns (value or None, why)."""
    cc = box_centers()
    step = (STRIP_X1 - STRIP_X0) / (CELLS + 2)
    rx, ry = step * SAMPLE, (STRIP_Y1 - STRIP_Y0) * SAMPLE
    names = []
    for i, (fx, fy) in enumerate(cc):
        c = sample(fx, fy, rx, ry)
        k, d = color_name(c)
        if d > TOLERANCE:
            return None, "box %d unreadable: %s is %d away from the nearest (%s)" % (
                i, c, d, k)
        names.append(k)
    if names[0] != "MARK" or names[-1] != "MARK":
        return None, "the strip does not show: at the ends %s and %s instead of the marks" % (
            names[0], names[-1])
    body_el = names[1:-1]
    if "MARK" in body_el:
        return None, "a mark in the middle of the strip: %s" % body_el
    v = ""
    fine = False
    for k in body_el:
        if k == "EMPTY":
            fine = True
            continue
        if fine:
            return None, "a character after an empty box: %s" % body_el
        v += "�" if k == "OTHER" else k
    return v, ""


def sampler(im, geo):
    """`sample()` on a PIL image of the canvas, with C21's geometry:
    fraction of the desktop ⇒ desktop pixel ⇒ photograph pixel."""
    pw, ph = im.size

    def al_pixel(fx, fy):
        X, Y = fx * geo["tl"], fy * geo["ta"]
        return ((geo["bx0"] + X * geo["left_side"]) * pw / geo["bw"],
                (geo["by0"] + Y * geo["sy"]) * ph / geo["bh"])

    def sample(fx, fy, rx, ry):
        vals = []
        for i in range(5):
            for j in range(5):
                x, y = al_pixel(fx + rx * (i - 2) / 2, fy + ry * (j - 2) / 2)
                x = min(pw - 1, max(0, int(x)))
                y = min(ph - 1, max(0, int(y)))
                vals.append(im.getpixel((x, y))[:3])
        return tuple(sorted(v[k] for v in vals)[len(vals) // 2] for k in range(3))
    return sample


def judge_case(heading, base, expected_val, blank, seen_base, seen_v):
    """(outcome, reason) of a case, from the three values read in the photographs."""
    if blank != "":
        return BLIND, "%s: after the cleaning the strip is not empty (%r): the scene does not " \
            "bear witness" % (heading, blank)
    if seen_base != base:
        return BLIND, "%s: the base %r did not arrive (seen %r): plain typing " \
            "is C4's, the selection is not judged" % (heading, base, seen_base)
    if seen_v == expected_val:
        return GREEN, "%s: %r ⇒ %r" % (heading, base, seen_v)
    return RED, "%s: %r ⇒ %r instead of %r" % (heading, base, seen_v, expected_val)


def overall_outcome(outcomes):
    return RED if RED in outcomes else (BLIND if BLIND in outcomes else GREEN)


def outcome_with_fault(outcomes):
    """⛔ The other way round: 0 if EVERY case is red (the fault shows everywhere)."""
    if BLIND in outcomes:
        return BLIND
    return GREEN if all(e == RED for e in outcomes) else RED


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION OF THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def _fake_photo(value_v, geo, shift=(0, 0), noise=25, seed=7):
    """A canvas painted like the scene, with a shift (a bar the
    kiosk does not cover) and some noise (the encoding)."""
    from PIL import Image, ImageDraw
    rnd = random.Random(seed)
    im = Image.new("RGB", (geo["bw"], geo["bh"]), (32, 32, 32))
    d = ImageDraw.Draw(im)
    step = (STRIP_X1 - STRIP_X0) / (CELLS + 2)
    colors = [MARK] + [COLORS.get(c, OTHER) for c in value_v[:CELLS]] + \
        [EMPTY] * (CELLS - len(value_v[:CELLS])) + [MARK]
    for i, c in enumerate(colors):
        x0 = (STRIP_X0 + i * step) * geo["bw"] + shift[0]
        x1 = (STRIP_X0 + (i + 1) * step) * geo["bw"] + shift[0] - 3
        c = tuple(min(255, max(0, v + rnd.randint(-noise, noise))) for v in c)
        d.rectangle([x0, STRIP_Y0 * geo["bh"] + shift[1], x1,
                     STRIP_Y1 * geo["bh"] + shift[1]], fill=c)
    return im


def certify():
    print("⭐ 11-c23 · CERTIFICATION OF THE PURE FUNCTIONS")
    troubles, done = [], []

    def prova(what, real, detail=""):
        done.append(what)
        print("   %s %s%s" % ("⭐ ok  " if real else "⛔ NO  ", what,
                              (" — " + detail) if detail else ""))
        if not real:
            troubles.append(what)

    # 1. the palette: colours distinct well beyond twice the tolerance
    all_v = [MARK, EMPTY, OTHER] + list(COLORS.values())
    dmin = min(_dist(a, b) for i, a in enumerate(all_v) for b in all_v[i + 1:])
    prova("palette: %d colours, minimum distance %d > 2×%d" % (len(all_v), dmin, TOLERANCE),
          dmin > 2 * TOLERANCE)
    prova("every character of the cases is in the alphabet",
          all(c in ALPHABET for _t, b, s, a in CASES for c in b + a
              + "".join(n for _x, n in s if len(n) == 1)))
    # 2. the fake field: the expected value written by hand is what the sequence gives
    for t, base, seq, expected_val in CASES:
        v = simulate(put_out(base) + seq)
        prova("simulate %s ⇒ %r" % (t.split()[0], expected_val), v == expected_val, "gives %r" % v)
        vg = simulate(put_out(base) + no_shift(seq))
        prova("simulate %s WITHOUT Shift ⇒ something else" % t.split()[0], vg != expected_val,
              "gives %r" % vg)
    prova("simulate: the cleaning empties the field", simulate(CLEAN, "abc") == "")
    # ⭐ case 4 with only the first half of the cure: after the letter Shift
    #   is UP for the server ⇒ the two Lefts move.  `[M]` c95: «abcdXqeA».
    old = put_out("abcdef") + clr("Shift", press("ArrowLeft") + press("A")) \
        + press("ArrowLeft") * 2 + press("X") + press("q")
    prova("simulate case 4 as it was before half 2 ⇒ «abcdXqeA» (the [M] of c95)",
          simulate(old) == "abcdXqeA", "gives %r" % simulate(old))
    # 3. the strip is read from the pixels
    try:
        from PIL import Image                     # noqa: F401
    except ImportError:
        print("⛔ PIL is not there: I cannot certify the reading ⇒ 3")
        return 3
    geo = {"tl": 1920, "ta": 1080, "bw": 1920, "bh": 1080, "bx0": 0, "by0": 0,
           "left_side": 1.0, "sy": 1.0}
    for v in ("", "abcY", "uno z", "abcdeAb", "abcdXqeA", "abcdefabcdefab"):
        for sp in ((0, 0), (0, 40), (-30, 25)):
            read, reason_text = read_strip(sampler(_fake_photo(v, geo, sp), geo))
            prova("strip %r shifted %s ⇒ it reads back" % (v, sp), read == v,
                  "read %r %s" % (read, reason_text))
    read, reason_text = read_strip(sampler(_fake_photo("abc@", geo), geo))
    prova("a character outside the alphabet ⇒ the replacement sign", read == "abc�",
          "read %r %s" % (read, reason_text))
    # the canvas bigger than the photo (Chrome shrinks it) and with black margins
    geo2 = {"tl": 3840, "ta": 2160, "bw": 1920, "bh": 1200, "bx0": 0, "by0": 60,
            "left_side": 0.5, "sy": 0.5}
    from PIL import Image
    canvas_size = Image.new("RGB", (1920, 1200), (0, 0, 0))
    canvas_size.paste(_fake_photo("abcY", {"bw": 1920, "bh": 1080}), (0, 60))
    read, reason_text = read_strip(sampler(canvas_size, geo2))
    prova("4K canvas in a buffer with margins ⇒ it reads back", read == "abcY",
          "read %r %s" % (read, reason_text))
    read, reason_text = read_strip(sampler(Image.new("RGB", (1920, 1080), (90, 60, 30)),
                                                geo))
    prova("without a strip ⇒ None (no judgement)", read is None, reason_text)
    # 4. the judges
    prova("judge: expected ⇒ GREEN",
          judge_case("t", "abcdef", "abcY", "", "abcdef", "abcY")[0] == GREEN)
    prova("judge: Shift does not select ⇒ RED",
          judge_case("t", "abcdef", "abcY", "", "abcdef", "abcYdef")[0] == RED)
    prova("judge: the base does not arrive ⇒ 3",
          judge_case("t", "abcdef", "abcY", "", "abc", "abcY")[0] == BLIND)
    prova("judge: the cleaning does not empty ⇒ 3",
          judge_case("t", "abcdef", "abcY", "xx", "abcdef", "abcY")[0] == BLIND)
    prova("with the fault: all red ⇒ 0 (seen)", outcome_with_fault([RED] * 4) == GREEN)
    prova("with the fault: one green ⇒ 1 (not seen)",
          outcome_with_fault([RED, GREEN, RED, RED]) == RED)
    prova("with the fault: one blind ⇒ 3", outcome_with_fault([RED, BLIND]) == BLIND)
    print()
    if troubles:
        print("⛔ CERTIFICATION FAILED: %d tests out of %d" % (len(troubles), len(done)))
        return 1
    print("⭐ CERTIFIED (%d tests): the expected value is what a field does with those keys, "
          "without Shift\n   something else comes out, and the value reads back from the pixels even "
          "shifted and dirtied." % len(done))
    return 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE BOX — the scene
# ═══════════════════════════════════════════════════════════════════════════
def scene_page():
    """⭐ The page, with THIS program's palette put inside."""
    pal = {k: "rgb(%d,%d,%d)" % v for k, v in COLORS.items()}
    step = (STRIP_X1 - STRIP_X0) / (CELLS + 2) * 100
    return """<!doctype html><meta charset=utf-8><title>REMOTIX C23</title>
<style>
 html,body{margin:0;height:100%%;background:#202020;overflow:hidden}
 #f{position:fixed;left:4vw;top:8vh;width:92vw;height:36vh;font:18vh/1 monospace;
    border:0;padding:0 2vw;box-sizing:border-box;background:#fff;color:#000;outline:0}
 .k{position:fixed;top:%(y0)fvh;height:%(h)fvh;width:calc(%(w)fvw - 6px)}
</style>
<input id=f autocomplete=off spellcheck=false>
<div id=s></div>
<script>
const TAV=%(pal)s, EMPTY='rgb(%(vu)s)', OTHER='rgb(%(al)s)', MARK='rgb(%(ma)s)', N=%(n)d;
const f=document.getElementById('f'), s=document.getElementById('s'), k=[];
for (let i=0;i<N+2;i++){const d=document.createElement('div');d.className='k';
  d.style.left=(%(x0)f+i*%(w)f)+'vw';s.appendChild(d);k.push(d);}
const m=(t)=>fetch('/l',{method:'POST',body:t}).catch(()=>0);
function paint(){const v=f.value;k[0].style.background=MARK;k[N+1].style.background=MARK;
  for(let i=0;i<N;i++){k[i+1].style.background = i<v.length ? (TAV[v[i]]||OTHER) : EMPTY;}
  if(v.length>N) k[N].style.background=OTHER;}
paint(); f.focus(); m('caricata');
addEventListener('keydown',e=>m('K '+e.key+' shift='+e.shiftKey+' ctrl='+e.ctrlKey));
f.addEventListener('input',()=>{paint();m('V '+JSON.stringify(f.value));});
setInterval(()=>{ if(document.activeElement!==f) f.focus(); paint(); },300);
</script>""" % {"pal": json.dumps(pal), "vu": "%d,%d,%d" % EMPTY, "al": "%d,%d,%d" % OTHER,
                "ma": "%d,%d,%d" % MARK, "n": CELLS, "x0": STRIP_X0 * 100,
                "w": step, "y0": STRIP_Y0 * 100, "h": (STRIP_Y1 - STRIP_Y0) * 100}


# The scene's server: it serves the page and notes what the page says.
SERVER = r'''
import http.server, sys
PAG = open(sys.argv[2], "rb").read()
LOG = sys.argv[3]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers(); self.wfile.write(PAG)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        t = self.rfile.read(n).decode("utf-8", "replace")
        with open(LOG, "a") as f: f.write(t + "\n")
        self.send_response(204); self.end_headers()
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
'''


def turn_on_scene(sc, chi, port):
    """Server + `firefox-esr --kiosk` in the session; waits for «caricata»."""
    b = lambda s: base64.b64encode(s.encode()).decode()     # noqa: E731
    c, t = sc.inside(
        "set -e; h=/home/{c}; mkdir -p $h/.c23-profile_v; "
        "echo {srv} | base64 -d > $h/c23-servitore.py; echo {page_map} | base64 -d > $h/c23.html; "
        "echo {pref} | base64 -d > $h/.c23-profile_v/user.js; : > $h/c23.log; "
        "chown -R {c}: $h/.c23-profile_v $h/c23-servitore.py $h/c23.html $h/c23.log; set +e; "
        "u=$(id -u {c}); "
        "setsid runuser -u {c} -- python3 $h/c23-servitore.py {p} $h/c23.html $h/c23.log "
        "</dev/null >/dev/null 2>&1 & "
        "d=''; for i in $(seq 1 40); do d=$(ls /run/user/$u 2>/dev/null | "
        "grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] && break; sleep 0.5; done; "
        "[ -n \"$d\" ] || {{ echo 'no wayland socket'; exit 2; }}; sleep 1; "
        "setsid runuser -u {c} -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=$h firefox-esr --no-remote --new-instance "
        "--profile $h/.c23-profile_v --kiosk http://127.0.0.1:{p}/ "
        "</dev/null >$h/.c23-firefox.log 2>&1 & "
        "for i in $(seq 1 80); do grep -q caricata $h/c23.log && {{ echo started; exit 0; }}; "
        "sleep 0.5; done; echo 'the scene did not say «caricata»'; tail -5 $h/.c23-firefox.log; "
        "exit 1".format(c=chi, p=port, srv=b(SERVER), page_map=b(scene_page()),
                        pref=b(C21.PREFERENCES)), 90)
    return c == 0, t


def read_notebook(sc, chi):
    _c, t = sc.inside("cat /home/%s/c23.log 2>/dev/null" % chi, 30)
    return [r for r in t.splitlines() if r.strip()]


# ═══════════════════════════════════════════════════════════════════════════
#  THE REAL KEYS
# ═══════════════════════════════════════════════════════════════════════════
def send_it(g, steps):
    """⭐ REAL keys given to the browser: `Input.dispatchKeyEvent` or the W3C actions."""
    if hasattr(g, "cdp"):
        mod = 0
        for kind, label_name in steps:
            if label_name in SPECIAL:
                key, code, vk, _w, bit = SPECIAL[label_name]
                if kind == "down":
                    mod |= bit
                g.cdp.call("Input.dispatchKeyEvent",
                             type="rawKeyDown" if kind == "down" else "keyUp",
                             key=key, code=code, windowsVirtualKeyCode=vk, modifiers=mod)
                if kind == "su":
                    mod &= ~bit
            else:
                code = "Space" if label_name == " " else "Key" + label_name.upper()
                vk = 32 if label_name == " " else ord(label_name.upper())
                p = dict(type="keyDown" if kind == "down" else "keyUp", key=label_name, code=code,
                         windowsVirtualKeyCode=vk, modifiers=mod)
                if kind == "down" and not (mod & 2):
                    p["text"] = p["unmodifiedText"] = label_name
                g.cdp.call("Input.dispatchKeyEvent", **p)
            time.sleep(PAUSE_MS / 1000.0)
        return
    az = []
    for kind, label_name in steps:
        v = SPECIAL[label_name][3] if label_name in SPECIAL else label_name
        az.append({"type": "keyDown" if kind == "down" else "keyUp", "value": v})
        az.append({"type": "pause", "duration": PAUSE_MS})
    g.m.call("WebDriver:PerformActions",
               {"actions": [{"type": "key", "id": "keyboard", "actions": az}]})
    g.m.call("WebDriver:ReleaseActions")


def snapshot_and_read(g, geo, wanted, store, label_name):
    """Photographs until the strip says `wanted` or `WAIT_S` runs out.
    Returns (value read or None, why)."""
    from PIL import Image
    fine = time.time() + WAIT_S
    read, reason_text, png = None, "no photograph", None
    while True:
        try:
            png = C21.full_photo(g)
        except Exception as e:                   # noqa: BLE001
            png, reason_text = None, "photograph failed: %s" % str(e)[:120]
        if png:
            im = Image.open(io.BytesIO(png)).convert("RGB")
            read, reason_text = read_strip(sampler(im, geo))
            if read == wanted:
                break
        if time.time() >= fine:
            break
        time.sleep(PHOTO_EVERY_S)
    if store and png:
        with open(os.path.join(store, "%s.png" % label_name), "wb") as fh:
            fh.write(png)
    return read, reason_text


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST OF ONE BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def observe(label_name, o, sc, chi):
    """Returns the browser's row, with the cases' `outcomes` (or `outcome` BLIND)."""
    print("\n══ %s ══════════════════════════════" % label_name.upper(), flush=True)
    row = {"browser": label_name}
    g = REAL.turn_on_driver(label_name, o)
    try:
        print("   stage: %s" % g.stage(), flush=True)
        if o.largo:
            print("   %s" % C20V.resize_to(g, label_name, o.largo, o.alto), flush=True)
        pr = REAL.Test(g, o, o.url, o.password)
        ok, m = pr.open_it()
        if not ok:
            return dict(row, outcome=BLIND, reason_text="the page does not open: " + m)
        e, m, s = pr.enter(o.password)
        if e != GREEN:
            return dict(row, outcome=BLIND, reason_text="the login: " + m)
        e, m, s = pr.first_frame()
        e, m = C20V.desktop_dark_but_alive(e, m, s)
        print("   ⭐ first frame: %s" % m, flush=True)
        if e != GREEN:
            return dict(row, outcome=BLIND, reason_text="without an image there is no looking: " + m)
        geo = g.js(C21.JS_GEOMETRY)
        if not geo:
            return dict(row, outcome=BLIND, reason_text="`REMOTIX_POINTER.geometry` is not there")
        print("   canvas %sx%s · buffer %sx%s" % (geo["tl"], geo["ta"], geo["bw"], geo["bh"]),
              flush=True)
        # ⭐ C21's wake-up: on GNOME the session is born in the overview
        print("   wake-up: %s" % C21.wake(g, geo), flush=True)
        ok, t = turn_on_scene(sc, chi, o.scene_port)
        print("   scene: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
        if not ok:
            return dict(row, outcome=BLIND, reason_text="the scene does not start: %s" % t[-300:])
        time.sleep(3)
        # ⚠ A click in the remote field: the new window takes the keyboard
        #   focus even where the desktop does not give it by itself.
        x, y = C21.desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * 0.26)
        g.click(x, y)
        time.sleep(1.0)
        outcomes, cases = [], []
        for heading, base, seq, expected_val in CASES:
            if o.no_shift:
                seq = no_shift(seq)
            short_v = heading.split()[0]
            send_it(g, CLEAN)
            blank, pv = snapshot_and_read(g, geo, "", o.store, "%s-c%s-0vuoto" % (label_name, short_v))
            send_it(g, put_out(base))
            vb, pb = snapshot_and_read(g, geo, base, o.store, "%s-c%s-1base" % (label_name, short_v))
            n0 = len(read_notebook(sc, chi))
            send_it(g, seq)
            seen_v, pvi = snapshot_and_read(g, geo, expected_val, o.store,
                                           "%s-c%s-2dopo" % (label_name, short_v))
            es, msg = judge_case(heading, base, expected_val, blank, vb, seen_v)
            if es == BLIND and (blank is None or vb is None):
                msg += " — %s" % (pv or pb)
            elif seen_v is None:
                es, msg = BLIND, "%s: the strip cannot be read after the sequence: %s" % (
                    heading, pvi)
            quad = read_notebook(sc, chi)[n0:]
            keys = [r[2:] for r in quad if r.startswith("K ")]
            print("   %s %s" % ({GREEN: "⭐ 0", RED: "⛔ 1", BLIND: "⚠ 3"}[es], msg),
                  flush=True)
            if es != GREEN:
                print("        remote keydowns: %s" % " | ".join(keys)[:400], flush=True)
            outcomes.append(es)
            cases.append({"case_v": short_v, "outcome": es, "seen_v": seen_v, "expected_val": expected_val,
                         "keydown_remoti": keys})
            if es == BLIND:
                break
        try:
            st = g.js("return REMOTIX.input_classic.state().pressed_keys")
        except Exception as ex:                  # noqa: BLE001
            st = "? (%s)" % str(ex)[:80]
        print("   keys pressed for the page, at the end: %s" % (st,), flush=True)
        return dict(row, outcomes=outcomes, cases=cases, pressed_keys_at_end=st)
    finally:
        try:
            g.shut()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ closing the browser: %s" % ex)


def judge_browser(row, fault):
    if "outcomes" not in row:
        return row
    es = row["outcomes"]
    if not fault:
        e = overall_outcome(es)
        reason_text = {GREEN: "all %d cases come out right" % len(es),
                  RED: "%d cases out of %d do not come out right" % (es.count(RED), len(es)),
                  BLIND: "one case could not be looked at"}[e]
        return dict(row, outcome=e, reason_text=reason_text)
    e = outcome_with_fault(es)
    reason_text = {GREEN: "⭐ FAULT SEEN: without Shift all %d cases are red" % len(es),
              RED: "⛔ FAULT NOT SEEN: without Shift %d cases come out right all the same"
                     % es.count(GREEN),
              BLIND: "with the fault one case could not be looked at"}[e]
    return dict(row, outcome=e, reason_text=reason_text)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--container_box", choices=sorted(PORTS))
    a.add_argument("--port", type=int, help="the product's port (normally that "
                   "of the net's box)")
    a.add_argument("--container", default="", help="the podman container, if it is not "
                   "rete11-<container_box> (the development boxes rete14-*)")
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--is_visible", action="store_true",
                   help="real windows (in the nested compositor) instead of headless")
    a.add_argument("--store", default="", help="folder for the photographs")
    a.add_argument("--no-shift", action="store_true",
                   help="INJECTED FAULT: the same sequences without ever pressing Shift")
    a.add_argument("--certify", action="store_true")
    a.add_argument("--cap-s", type=int, default=45)
    a.add_argument("--base-ports", type=int, default=3231)
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    o = a.parse_args()
    if o.certify:
        return certify()
    if not o.container_box and o.port:
        o.container_box = {p: s for s, p in PORTS.items()}.get(o.port)
    if not o.container_box:
        print("⛔ --container_box is needed, or a --port of the net (%s)" % PORTS)
        return 3
    port = o.port or PORTS[o.container_box]
    o.url = "https://%s:%d/" % (o.host, port)
    o.password = "c23-" + secrets.token_hex(6)
    o.scene, o.continuity_s, o.log_cmd = "viva", 8, ""
    o.leave_on = False
    o.scene_port = random.randint(39000, 39899)
    if o.store:
        os.makedirs(o.store, exist_ok=True)
    sc = C20V.Box(o.container_box)
    if o.container:
        sc.container = o.container
    chi = "c23u%03d" % random.randint(0, 999)
    assert TENANT_PATTERN.match(chi)
    o.username = chi
    print("⭐ 11-c23 · %s · %s · tenant %s · browser %s · %s%s"
          % (sc.container, o.url, chi, o.browser,
             "real windows" if o.is_visible else "HEADLESS",
             " · ⛔ INJECTED FAULT --no-shift" if o.no_shift else ""))
    line_list = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.clear_out(chi)
        c, t = sc.create(chi, o.password)
        if c != 0:
            print("⛔ I could not create %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r = judge_browser(observe(b, o, sc, chi), o.no_shift)
        except Exception as e:                   # noqa: BLE001
            r = {"browser": b, "outcome": BLIND, "reason_text": "the bench fell over: %r" % e}
        finally:
            sc.clear_out(chi)
        print("   ▶ %s: %s — %s" % (b, OUTCOME_NAME.get(r["outcome"], r["outcome"]),
                                   r.get("reason_text")))
        print("LINE " + json.dumps(r, ensure_ascii=False), flush=True)
        line_list.append(r)
    v = [r["outcome"] for r in line_list]
    outcome = RED if RED in v else (BLIND if BLIND in v else GREEN)
    print()
    if o.no_shift:
        print({GREEN: "⭐ THE INJECTED FAULT WAS SEEN (outcome 0: the other way round, "
                      "like every fault of the net)",
               RED: "⛔⛔ THE INJECTED FAULT WAS NOT SEEN",
               BLIND: "⚠ with the injected fault I could NOT look ⇒ 3"}[outcome])
    else:
        print("%s C23(%s): %s" % ({GREEN: "⭐", RED: "⛔⛔", BLIND: "⚠"}[outcome],
                                  o.container_box, OUTCOME_NAME[outcome]))
    return outcome


if __name__ == "__main__":
    sys.exit(main())
