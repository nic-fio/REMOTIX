#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c22 — ⭐⭐ «THE EDGE CAN BE DRAGGED»
===========================================================================

    python3 11-c22-the-edge-drags.py --box kde [--browser firefox,chrome]
    python3 11-c22-the-edge-drags.py --port 8513 --host 192.168.0.2
    python3 11-c22-the-edge-drags.py --box kde --no-button
    python3 11-c22-the-edge-drags.py --certify

    what must be true         : a window is RESIZED by dragging its
                                edge with the mouse from the browser — on GNOME, KDE,
                                XFCE and LXQt (the user, 24 Sep 2026: «one
                                last check remains: that resizing
                                windows by dragging the edge
                                is implemented on all the DEs»)
    where it starts from      : ⛔ from scratch, a NEW tenant (`c22u<n>`)
    what it looks at          : ⛔ **THE IMAGE**: the right edge of the window
                                in the photograph of the canvas, before and after — not
                                a counter of clicks sent
    how I know it can give red: `--no-button` (the same drag with the
                                button UP) ⇒ the window does not change ⇒ RED

⭐ C21'S SISTER.  C21 proves that on the edge the SHAPE changes (the user knows they
   can grab); C22 proves that grabbing the window CHANGES ITS SIZE.  The
   scene is the same, and the functions are C21's — ⛔ IMPORTED, not
   copied: the known page with the cyan background, the Firefox profile with the size
   fixed (`xulstore.json`), the ESC that on GNOME leaves the overview,
   the search for the window in the photograph, the photo⇄desktop⇄
   glass conversions.  If one of those changes, it changes for both meshes.

⭐ WHAT IT DOES, for each browser (Firefox with Marionette, Chrome with CDP):
     1  creates the tenant `c22u<n>`, opens REMOTIX, logs in, first frame
     2  a real ESC (C21's wake-up), then a NORMAL `firefox-esr` on the known
        page, 45 % x 55 % of the screen
     3  finds the window in the photograph: the right edge `x_b` is the last
        cyan pixel, at half height
     4  for each grab point `x_b + k`, k in `GRIPS` (from 2 px inside to 6
        outside), at half height:
          presses the left button (a REAL browser event: Marionette's `pointerDown`,
          CDP's `mousePressed`), drags right by `PUSH`
          px in `STEPS` steps with the button pressed, releases
        ⇒ photographs, and measures again: the right edge, the left one, the top.
     5  GREEN at the first point where the right edge moved by at least
        `THRESHOLD` px and the window is still THE SAME (left edge and top
        still, and the yellow box inside): it declares AT WHICH point.

⛔⭐ WHY A SCAN OF GRABS AND NOT A POINT — the grab zone is not
   in the same place on the four desktops (`[M]` from C21, 24 Sep 2026):
     KWin (KDE)   ON the edge, from 1 px inside to 1 px outside
     GNOME        in the window's shadow, from ~+1 px
     labwc        from the edge pixel up to 7 px outside
   ⇒ A fixed point would give red to someone for something their desktop
     does on purpose.  ⚠ The scan stops at the FIRST green: after that, the window
     is wider, and carrying on would mean measuring everything again for a datum
     the user's question does not ask for.

   ⭐ `[M]` 24 Sep 2026, first measurement, 4K, real windows in the server's nested
     labwc: GREEN on gnome, kde, xfce and lxqt, Firefox 140 and Chrome 154, +150
     px out of 150 everywhere; the grab is at +1 px from the last cyan pixel (at +0 for
     Firefox on gnome), from -2 to 0 nothing.  `--no-button`: fault SEEN
     everywhere (9 still points, then the healthy control green).

⛔ WHY «THE SAME WINDOW» — a drag that MOVES the window
   (grabbed by the title bar, or with the «Alt+drag» gesture) also brings the
   right edge to the right: by 150 px, more than the threshold.  ⇒ Green wants the
   LEFT edge still (±`STOPPED` px): if both moved, it is a
   move, and it is said.

⛔ HOW I KNOW IT CAN GIVE RED — `--no-button`.
   The same gesture, the same points, the same steps, but the button is NOT
   pressed: no desktop resizes a window by merely passing over it.  ⇒ On
   all points the window must stay as it was, and the mesh must give RED.
   ⭐ And then the HEALTHY CONTROL, in the same session: the scan with the
   button must give green.  Without the control, a «red» with the button up
   could come from a broken product and not from the fault.
   ⛔ It reads THE OTHER WAY ROUND, like every fault of the net (`11-hook.sh`,
     `run_mesh`): 0 = the fault was SEEN, 1 = NOT seen, 3 = the
     healthy control was not green ⇒ nothing could be injected.

⚠ OUTCOMES: 0 green · 1 red · 3 «I could not look», with the reason.
   The 3 is the BENCH's (the window does not show, the press did not reach
   the PAGE, the pointer is not where I say); the red is the PRODUCT's (the
   page sent press and movement, and the window did not change
   size).

⚠ WHERE IT RUNS: on the machine that has the browsers (the server, `REMOTIX_ON_SERVER=1`
  with the nested `labwc`), like C21; the tenant `c22u<n>` follows C19's
  pattern (`^c[0-9]+b?u[0-9]+$`): if the bench died half-way, the hook clears it out.
"""
import argparse
import importlib.util as _iu
import json
import os
import random
import re
import secrets
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(name, file):
    s = _iu.spec_from_file_location(name, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ Imported, not copied: C21 brings `12-c20-real` and `12-real-clients` along
#   — a single VERI in memory, and the ESC already added to the key table.
C21 = _load("c21", os.path.join(HERE, "11-c21-on-the-edge-the-shape-changes.py"))
C20V, VERI = C21.C20V, C21.VERI
GREEN, RED, BLIND = C21.GREEN, C21.RED, C21.BLIND
PORTS = C21.PORTS
OUTCOME_NAME = C21.OUTCOME_NAME

TENANT_PATTERN = re.compile(r"^c22u[0-9]+$")

# ---------------------------------------------------------------------------
# ⛔ THE NUMBERS — each with its reason.
# ---------------------------------------------------------------------------
# ⭐ The grab points, in DESKTOP pixels relative to the last cyan pixel:
#   from 2 inside to 6 outside (the three measured zones are between -1 and +7).
GRIPS = tuple(range(-2, 7))
# How far it drags, and in how many steps: a hand gesture, not a jump.
PUSH = 150
STEPS = 15
STEP_PAUSE_MS = 30
# ⭐ Green wants at least 100 px of the 150: the desktop can round the size
#   (the character grid, a minimum, an unfinished animation) but a
#   real resize brings almost all of them.
THRESHOLD = 100
# The left edge and the top must stay still within these pixels: otherwise the
# window MOVED, it was not resized.
STOPPED = 4
# Between one point and the next: more than every desktop's double click (400-500 ms),
# so two close presses do not become a «double click on the edge».
BETWEEN_POINTS_S = 1.0


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS — and they are the ones `--certify` tests
# ═══════════════════════════════════════════════════════════════════════════
def window_in_desktop(geo, f):
    """The window found in the photo (`C21.trova_finestra`) in desktop pixels:
    {sinistro, destro, alto} — the right one is the LAST cyan pixel."""
    pw, ph = f["photo"]
    x0, y0 = C21.from_photo_to_desktop(geo, pw, ph, f["ciano"][0] + 0.5, f["ciano"][1] + 0.5)
    xd, _ = C21.from_photo_to_desktop(geo, pw, ph, f["right"] + 0.5, f["centro"][1] + 0.5)
    return {"sinistro": int(x0), "destro": int(xd), "top": int(y0)}


def judge_grip(k, before, after):
    """⭐ The judgement of ONE grab point.

    `before`, `after`  {sinistro, destro, alto} in desktop pixels, or None
    Returns (outcome, reason, shift of the right edge | None)."""
    if not after:
        return BLIND, "%+d px: after the drag the window is no longer visible" % k, None
    sp = after["destro"] - before["destro"]
    ds = after["sinistro"] - before["sinistro"]
    da = after["top"] - before["top"]
    stills = abs(ds) <= STOPPED and abs(da) <= STOPPED
    if sp >= THRESHOLD and stills:
        return GREEN, ("%+d px: the right edge went from x=%d to x=%d (%+d px), the "
                       "left one and the top still — RESIZED"
                       % (k, before["destro"], after["destro"], sp)), sp
    if sp >= THRESHOLD:
        return RED, ("%+d px: the right edge %+d px but the left one too %+d and the top "
                       "%+d — the window MOVED, it was not resized" % (k, sp, ds, da)), sp
    return RED, ("%+d px: the right edge %+d px (%d needed), the left one %+d — the size "
                   "did not change" % (k, sp, THRESHOLD, ds)), sp


def judge_scan(results):
    """[(k, outcome, reason, sp)] ⇒ (outcome, reason, (k, sp) | None).

    GREEN at the first green point; RED if all the points were looked at and
    none is green; CIECO if a point could not be looked at before a
    green (the vanished window is not a «does not resize»)."""
    if not results:
        return BLIND, "no grab point tried", None
    for k, e, m, sp in results:
        if e == GREEN:
            return GREEN, m, (k, sp)
        if e == BLIND:
            return BLIND, m, None
    return RED, ("in NONE of the %d grab points (from %+d to %+d px from the edge) did the window "
                   "change size: %s" % (len(results), results[0][0], results[-1][0],
                                              "; ".join(r[2] for r in results[-2:]))), None


def verdict_with_fault(without, healthy):
    """⭐ The injected fault, read the other way round.

    `without`  (outcome, reason, x) of the scan with the button UP
    `healthy`   (outcome, reason, x) of the control with the button, or None
    Returns (outcome of the mesh with the fault, reason)."""
    if without[0] == GREEN:
        return RED, ("⛔ FAULT NOT SEEN: with the button up the window changed size "
                       "all the same (%s)" % without[1])
    if without[0] == BLIND:
        return BLIND, "with the button up I could not look: %s" % without[1]
    if not healthy or healthy[0] != GREEN:
        return BLIND, ("the healthy control is not green (%s): the fault cannot be injected"
                       % (healthy[1] if healthy else "not done"))
    return GREEN, ("⭐ FAULT SEEN: with the button up no point resizes, with the button "
                   "they do (%s)" % healthy[1])


def gesture(x0, y0, dx, steps):
    """The points of the drag, in desktop pixels: the start excluded."""
    return [(x0 + dx * (i + 1) / float(steps), y0) for i in range(steps)]


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION OF THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def certify():
    print("⭐ 11-c22 · CERTIFICATION OF THE PURE FUNCTIONS")
    troubles, done = [], []

    def prova(what, real, detail=""):
        done.append(what)
        print("   %s %s%s" % ("⭐ ok  " if real else "⛔ NO  ", what,
                              (" — " + detail) if detail else ""))
        if not real:
            troubles.append(what)

    P = {"sinistro": 80, "destro": 1807, "top": 80}
    cases = [
        ("widened by 150, left still ⇒ GREEN",
         {"sinistro": 80, "destro": 1957, "top": 80}, GREEN),
        ("widened by 120 (rounded) ⇒ GREEN",
         {"sinistro": 81, "destro": 1927, "top": 80}, GREEN),
        ("widened by 60 ⇒ RED", {"sinistro": 80, "destro": 1867, "top": 80}, RED),
        ("still ⇒ RED", dict(P), RED),
        ("MOVED by 150 (both edges) ⇒ RED",
         {"sinistro": 230, "destro": 1957, "top": 80}, RED),
        ("widened but the top moved ⇒ RED",
         {"sinistro": 80, "destro": 1957, "top": 140}, RED),
        ("vanished ⇒ 3", None, BLIND),
    ]
    for name, after, expected in cases:
        e, m, _sp = judge_grip(3, P, after)
        prova("giudica_presa: %s" % name, e == expected, m)
    r = [(-2, RED, "a", 0), (-1, RED, "b", 1), (0, GREEN, "c", 148)]
    e, m, x = judge_scan(r)
    prova("giudica_scansione: green at 0 px ⇒ GREEN, and it says where", e == GREEN and x == (0, 148), m)
    e, m, x = judge_scan([(k, RED, "still", 0) for k in GRIPS])
    prova("giudica_scansione: no point ⇒ RED", e == RED, m)
    e, m, x = judge_scan([(-2, RED, "a", 0), (-1, BLIND, "vanished", None)])
    prova("giudica_scansione: vanished before a green ⇒ 3", e == BLIND, m)
    prova("judge_scan: empty ⇒ 3", judge_scan([])[0] == BLIND)
    # the fault, read the other way round
    R, V, Cc = (RED, "still", None), (GREEN, "+1 px", (1, 150)), (BLIND, "vanished", None)
    for name, without, healthy, expected in [
            ("up still, healthy green ⇒ 0 (seen)", R, V, GREEN),
            ("up RESIZES ⇒ 1 (not seen)", V, V, RED),
            ("up still, healthy RED ⇒ 3", R, (RED, "still", None), BLIND),
            ("up still, healthy not done ⇒ 3", R, None, BLIND),
            ("up blind ⇒ 3", Cc, V, BLIND)]:
        e, m = verdict_with_fault(without, healthy)
        prova("verdetto_col_guasto: %s" % name, e == expected, m)
    g = gesture(100, 50, PUSH, STEPS)
    prova("gesture: %d steps, the last one at +%d" % (STEPS, PUSH),
          len(g) == STEPS and g[-1] == (100 + PUSH, 50) and g[0][0] > 100)
    # the window in the photo ⇒ in the desktop (geometry 1:1 and 2:1)
    f = {"photo": [400, 250], "ciano": [50, 40, 299, 199], "right": 299, "centro": [174, 118]}
    geo = {"bw": 400, "bh": 250, "bx0": 0, "by0": 0, "sx": 1.0, "sy": 1.0}
    d = window_in_desktop(geo, f)
    prova("window_in_desktop 1:1", d == {"sinistro": 50, "destro": 299, "top": 40}, str(d))
    geo2 = dict(geo, bw=800, bh=500)
    d2 = window_in_desktop(geo2, f)
    prova("window_in_desktop with the photo at half size", d2["destro"] == 599, str(d2))
    print()
    if troubles:
        print("⛔ CERTIFICATION FAILED: %d tests out of %d" % (len(troubles), len(done)))
        return 1
    print("⭐ CERTIFIED: the judge tells apart resized, still and MOVED, and the\n"
          "   fault reads the other way round only with the healthy control green.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE PAGE — what it saw, to separate the bench from the product
# ═══════════════════════════════════════════════════════════════════════════
JS_OBSERVE = r"""
(function () {
  if (window.__C22__) return;
  const C = window.__C22__ = { giu: 0, su: 0, premuti: 0, alzati: 0 };
  /* ⚠ Since 2 Oct 2026 the page takes the click from `pointerdown` and with its
     `preventDefault` switches off the compatibility `mousedown`s: counting only those
     gave «giu 0» and a false BLOCKED (run `19-cattura-2`).  Both are
     counted: the thresholds look at «at least one» and «none». */
  addEventListener('mousedown', function () { C.giu++; }, true);
  addEventListener('mouseup', function () { C.su++; }, true);
  addEventListener('pointerdown', function (e) { if (e.pointerType !== 'touch') C.giu++; }, true);
  addEventListener('pointerup', function (e) { if (e.pointerType !== 'touch') C.su++; }, true);
  addEventListener('pointermove', function (e) {
    if (e.pointerType === 'touch') return;
    if (e.buttons & 1) C.premuti++; else C.alzati++;
  }, true);
})();
"""
JS_RESET = ("const C=window.__C22__; if(!C) return false; "
             "C.giu=0; C.su=0; C.premuti=0; C.alzati=0; return true;")
JS_COUNT = r"""
const C = window.__C22__;
const st = window.REMOTIX && REMOTIX.classic_input ? REMOTIX.classic_input.state() : null;
return C ? { giu: C.giu, su: C.su, premuti: C.premuti, alzati: C.alzati,
             spedito: st ? st.last_sent : null } : null;
"""


def drag(g, geo, X, Y, press):
    """⭐ The gesture, with REAL browser EVENTS: the pointer is brought to (X,Y),
    pressed (if `press`), dragged right by `PUSH` px in `STEPS`
    steps, released.  (X,Y) and the points are DESKTOP pixels."""
    points = [C21.desktop_to_glass(geo, X, Y)] + \
        [C21.desktop_to_glass(geo, x, y) for x, y in gesture(X, Y, PUSH, STEPS)]
    if hasattr(g, "cdp"):
        c = g.cdp.call
        x0, y0 = points[0]
        c("Input.dispatchMouseEvent", type="mouseMoved", x=x0, y=y0)
        time.sleep(0.15)
        if press:
            c("Input.dispatchMouseEvent", type="mousePressed", x=x0, y=y0, button="left",
              buttons=1, clickCount=1)
        time.sleep(0.2)
        for x, y in points[1:]:
            if press:
                c("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, button="left",
                  buttons=1)
            else:
                c("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
            time.sleep(STEP_PAUSE_MS / 1000.0)
        time.sleep(0.2)
        if press:
            x, y = points[-1]
            c("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left",
              buttons=0, clickCount=1)
        return
    # Marionette: ONE chain of actions, so the button stays down between the steps
    az = [{"type": "pointerMove", "x": int(round(points[0][0])), "y": int(round(points[0][1])),
           "origin": "viewport", "duration": 0},
          {"type": "pause", "duration": 150}]
    if press:
        az.append({"type": "pointerDown", "button": 0})
    az.append({"type": "pause", "duration": 200})
    for x, y in points[1:]:
        az.append({"type": "pointerMove", "x": int(round(x)), "y": int(round(y)),
                   "origin": "viewport", "duration": 0})
        az.append({"type": "pause", "duration": STEP_PAUSE_MS})
    az.append({"type": "pause", "duration": 200})
    if press:
        az.append({"type": "pointerUp", "button": 0})
    g._actions([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                "actions": az}])


def measure(g, geo, o, name, label):
    """The window in the desktop, from the (still) photograph, or (None, reason)."""
    f, why = C21.search_window(g, o.wait_window, "", name)
    if not f:
        return None, why
    if o.save:
        try:
            with open(os.path.join(o.save, "%s-%s.png" % (name, label)), "wb") as fh:
                fh.write(C21.full_photo(g))
        except Exception:                        # noqa: BLE001
            pass
    return dict(window_in_desktop(geo, f), cy=f["centro"][1], f=f), ""


def scan_edge(g, geo, o, name, press):
    """⭐ The scan of the grab points.  Returns (outcome, reason, x, rows)."""
    lines = []
    for k in GRIPS:
        before, why = measure(g, geo, o, name, "before%+d" % k)
        if not before:
            lines.append((k, BLIND, "%+d px: before the gesture the window does not show: %s"
                          % (k, why), None))
            break
        pw, ph = before["f"]["photo"]
        _x, Yc = C21.from_photo_to_desktop(geo, pw, ph, 0, before["cy"] + 0.5)
        X = before["destro"] + k + 0.5
        if X + PUSH + 2 >= geo["tl"]:
            lines.append((k, BLIND, "%+d px: on the right there is no room to drag (edge "
                          "x=%d, screen %d)" % (k, before["destro"], geo["tl"]), None))
            break
        g.js(JS_RESET)
        drag(g, geo, X, Yc, press)
        time.sleep(0.3)
        n = g.js(JS_COUNT) or {}
        # ⛔ The bench before the product: if the page did not see the gesture,
        #   there is nothing to judge.
        if press and (n.get("giu", 0) < 1 or n.get("su", 0) < 1
                      or n.get("premuti", 0) < STEPS // 2):
            lines.append((k, BLIND, "%+d px: the browser did not deliver the gesture to the page "
                          "(%s)" % (k, n), None))
            break
        if not press and (n.get("giu", 0) or n.get("alzati", 0) < STEPS // 2):
            lines.append((k, BLIND, "%+d px: the gesture with the button up did not arrive as "
                          "it should (%s)" % (k, n), None))
            break
        sp_ = n.get("spedito") or [-1, -1]
        expected_x = int(X + PUSH)
        if abs(sp_[0] - expected_x) > 2 or abs(sp_[1] - int(Yc)) > 2:
            lines.append((k, BLIND, "%+d px: the page sent last (%s,%s) instead of "
                          "(%d,%d): the pointer is not where I say"
                          % (k, sp_[0], sp_[1], expected_x, int(Yc)), None))
            break
        after, why = measure(g, geo, o, name, "after%+d" % k)
        e, m, sp = judge_grip(k, before, after)
        if not after:
            m += " (%s)" % why
        print("   %s grab %+d px (x=%d, y=%d)%s → %s" % (
            {GREEN: "⭐", RED: "·", BLIND: "⚠"}[e], k, int(X), int(Yc),
            "" if press else " with the button UP", m), flush=True)
        lines.append((k, e, m, sp))
        if e != RED:
            break
        time.sleep(BETWEEN_POINTS_S)
    es, ms, x = judge_scan(lines)
    return es, ms, x, lines


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST OF ONE BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def test_browser(name, o, sc, chi):
    print("\n══ %s ══════════════════════════════" % name.upper(), flush=True)
    line = {"browser": name}
    g = VERI.turn_on_driver(name, o)
    try:
        print("   stage: %s" % g.stage(), flush=True)
        if o.width:
            print("   %s" % C20V.resize_to(g, name, o.width, o.height), flush=True)
        pr = VERI.Test(g, o, o.url, o.password)
        ok, m = pr.do_open()
        if not ok:
            return dict(line, outcome=BLIND, why="the page does not open: " + m)
        e, m, s = pr.enter(o.password)
        if e != GREEN:
            return dict(line, outcome=BLIND, why="the login: " + m)
        e, m, s = pr.first_frame()
        e, m = C20V.desktop_dark_but_alive(e, m, s)
        print("   ⭐ first frame: %s" % m, flush=True)
        if e != GREEN:
            return dict(line, outcome=BLIND, why="without an image there is no looking: " + m)
        geo = g.js(C21.JS_GEOMETRY)
        if not geo:
            return dict(line, outcome=BLIND, why="`REMOTIX_PUNTATORE.geometry` is not there")
        print("   canvas %sx%s · buffer %sx%s · layout «%s»"
              % (geo["tl"], geo["ta"], geo["bw"], geo["bh"], geo["layout"]), flush=True)
        if geo["layout"] != "classic":
            # ⛔ The mouse with buttons belongs to the classic layout; with the finger
            #   the drag is another gesture, and it is not this question.
            return dict(line, outcome=BLIND, why="the page is not in the classic "
                        "layout (%s)" % geo["layout"])
        # ⚠ C21's wake-up (GNOME is born in the overview), BEFORE the window
        print("   wake-up: %s" % C21.wake(g, geo), flush=True)
        largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
        ok, t = C21.prepare_home(sc, chi, largo_f, alto_f)
        if not ok:
            return dict(line, outcome=BLIND, why="the home cannot be prepared: %s" % t[-200:])
        ok, t = C21.turn_on_window(sc, chi)
        if not ok:
            return dict(line, outcome=BLIND, why="firefox-esr does not start: %s" % t[-200:])
        w0, why = measure(g, geo, o, name, "window")
        if not w0:
            return dict(line, outcome=BLIND, why="the test window does not show within %d s: %s"
                        % (o.wait_window, why))
        if w0["destro"] - w0["sinistro"] < 0.7 * largo_f:
            return dict(line, outcome=BLIND, why="the window is %d px wide and I asked for "
                        "%d: it is a preview (the overview?), not the window"
                        % (w0["destro"] - w0["sinistro"], largo_f))
        line["window"] = {k: w0[k] for k in ("sinistro", "destro", "top")}
        print("   ⭐ window: x=%d..%d, top y=%d in the desktop · grabs from %+d to %+d px"
              % (w0["sinistro"], w0["destro"], w0["top"], GRIPS[0], GRIPS[-1]), flush=True)
        g.js(VERI._inject(JS_OBSERVE))
        if not g.js("return !!window.__C22__;"):
            return dict(line, outcome=BLIND, why="the observer did not install itself")

        if not o.no_button:
            es, ms, x, lines = scan_edge(g, geo, o, name, True)
            line["prese"] = [[k, e, m] for k, e, m, _ in lines]
            if x:
                line["presa_px"], line["spostamento_px"] = x
            return dict(line, outcome=es, why=ms)
        # ── the injected fault: first with the button up, then the control ──
        print("   ── --no-button: the same gesture, button UP ──", flush=True)
        without = scan_edge(g, geo, o, name, False)
        line["senza_pulsante"] = [[k, e, m] for k, e, m, _ in without[3]]
        healthy = None
        if without[0] == RED:
            print("   ── the healthy control: with the button ──", flush=True)
            healthy = scan_edge(g, geo, o, name, True)
            line["healthy"] = [[k, e, m] for k, e, m, _ in healthy[3]]
            if healthy[2]:
                line["presa_px"], line["spostamento_px"] = healthy[2]
        eg, mg = verdict_with_fault(without[:3], healthy[:3] if healthy else None)
        return dict(line, outcome=eg, why=mg)
    finally:
        try:
            g.close()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ closing the browser: %s" % ex)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--box", choices=sorted(PORTS))
    a.add_argument("--port", type=int)
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--visible", action="store_true",
                   help="real windows (in the nested compositor) instead of headless")
    a.add_argument("--save", default="", help="folder for the photographs")
    a.add_argument("--no-button", action="store_true",
                   help="INJECTED FAULT: the same drag with the button up")
    a.add_argument("--certify", action="store_true")
    a.add_argument("--wait-window", type=int, default=60)
    a.add_argument("--cap-s", type=int, default=45)
    a.add_argument("--base-port", type=int, default=2961)
    a.add_argument("--width", type=int, default=3840)
    a.add_argument("--height", type=int, default=2160)
    o = a.parse_args()
    if o.certify:
        return certify()
    if not o.box and o.port:
        o.box = {p: s for s, p in PORTS.items()}.get(o.port)
    if not o.box:
        print("⛔ --box is needed, or a --port of the net (%s)" % PORTS)
        return 3
    port = o.port or PORTS[o.box]
    # ⚠ the fields the drivers and `Test` of 12-real-clients expect
    o.url = "https://%s:%d/" % (o.host, port)
    o.password = "c22-" + secrets.token_hex(6)
    o.scene, o.continuity_s, o.log_cmd = "alive", 8, ""
    o.leave_on = False
    if o.save:
        os.makedirs(o.save, exist_ok=True)
    sc = C20V.Box(o.box)
    chi = "c22u%03d" % random.randint(0, 999)
    assert TENANT_PATTERN.match(chi)
    o.user = chi
    print("⭐ 11-c22 · %s · %s · inquilino %s · browser %s · %s%s"
          % (sc.container, o.url, chi, o.browser,
             "real windows" if o.visible else "HEADLESS",
             " · ⛔ INJECTED FAULT --no-button" if o.no_button else ""))
    lines = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.clear_out(chi)
        c, t = sc.create(chi, o.password)
        if c != 0:
            print("⛔ I could not create %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r = test_browser(b, o, sc, chi)
        except Exception as e:                   # noqa: BLE001
            r = {"browser": b, "outcome": BLIND, "why": "the bench fell over: %r" % e}
        finally:
            sc.clear_out(chi)
        print("   ▶ %s: %s — %s" % (b, OUTCOME_NAME.get(r["outcome"], r["outcome"]),
                                   r.get("why")))
        print("RIGA " + json.dumps(r, ensure_ascii=False), flush=True)
        lines.append(r)
    v = [r["outcome"] for r in lines]
    outcome = RED if RED in v else (BLIND if BLIND in v else GREEN)
    print()
    if o.no_button:
        print({GREEN: "⭐ THE INJECTED FAULT WAS SEEN (outcome 0: the other way round, "
                      "like every fault of the net)",
               RED: "⛔⛔ THE INJECTED FAULT WAS NOT SEEN",
               BLIND: "⚠ with the injected fault I could NOT look ⇒ 3"}[outcome])
    else:
        print("%s C22(%s): %s" % ({GREEN: "⭐", RED: "⛔⛔", BLIND: "⚠"}[outcome],
                                  o.box, OUTCOME_NAME[outcome]))
    return outcome


if __name__ == "__main__":
    sys.exit(main())
