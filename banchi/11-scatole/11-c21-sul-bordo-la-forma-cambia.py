#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c21 — ⭐⭐ «ON THE EDGE THE SHAPE CHANGES»
===========================================================================

    python3 11-c21-sul-bordo-la-forma-cambia.py --container_box gnome [--browser firefox,chrome]
    python3 11-c21-sul-bordo-la-forma-cambia.py --port 8513 --host 192.168.0.2
    python3 11-c21-sul-bordo-la-forma-cambia.py --container_box gnome --wrong-shape
    python3 11-c21-sul-bordo-la-forma-cambia.py --certify

    what must be true         : the REAL SHAPE of the pointer reaches the browser —
                                on GNOME, KDE, XFCE and LXQt (the user's
                                decision, 24 Sep 2026)
    where it starts from      : ⛔ from scratch, a NEW tenant (`c21u<n>`)
    what it looks at          : ⛔ **THE IMAGE** of the cursor the page makes
                                the browser wear — not a counter
    how I know it can give red: `--wrong-shape` (the table of expectations
                                shifted by one) ⇒ RED, on the same images

⛔⛔ WHY IT EXISTS, AND WHY WITH THE REAL BROWSERS.
   Today (24 Sep 2026) the cursor shape arrives only from GNOME: on the other
   three desktops the page always shows the arrow, and on the edge of a window
   the user does not know they can resize it.  ⇒ The test is written BEFORE the
   product, and on the desktops where the shape does not arrive it must give red.
   ⚠ With the real browsers and not with the Python client: the user, 23 Sep 2026, *«the tests
     must be done with the real browsers, not with emulators»*.  And here there is
     one more reason: the BROWSER WEARS the shape (`cursor: url(...) hx hy`),
     and the Python client has no cursor to dress.

⭐ WHAT IT DOES, for each browser (Firefox with Marionette, Chrome with CDP: the
   drivers are those of `banchi/12-client-veri.py`, and the entry into the
   box is that of `banchi/12-c20-veri.py` — ⛔ imported, not copied):
     1  creates the tenant `c21u<n>` and puts in its home a KNOWN PAGE
        (`PAGE`: cyan background, a yellow text box) and a Firefox
        profile with the declared measurement window (`xulstore.json`)
     2  opens REMOTIX, logs in, waits for the first non-degenerate frame
     3  inside the session starts a NORMAL `firefox-esr` — ⛔ not `--kiosk`,
        which has no borders — on the known page
     4  finds the window IN THE PHOTOGRAPH of the canvas: the cyan is the page, and
        its last pixel on the right is the right edge of the window.  ⚠ It is
        looked for in the pixels because there is no tool common to the four
        desktops to ask for a window's rectangle (GNOME does not expose
        `wlr-foreign-toplevel`, and inside the box there is no `lswt`).
     5  moves the pointer with REAL browser EVENTS (Marionette's `pointerMove`,
        CDP's `Input.dispatchMouseEvent`), in four steps:
          start     on the text            (prepares: the shape before is known)
          centre    at the centre of the window     ⇒ expected «arrow»
          edge      a SCAN on the right edge, from 4 px inside to 8 px
                    outside, one pixel per step  ⇒ expected «horizontal»
                    in at least one point of the scan
          text      on the yellow box          ⇒ expected «text»
        ⭐ The start on the text is there so that every judged step is a
          CHANGE: on the bare desktop the cursor is already an arrow, and a
          «centre» that does not change would prove nothing.
     6  for every step it reads in the page the `cursor` rule the page gives
        to the canvas (`#display_screen`, `cl_apply_mode()` in `src/pagina.html`
        ~9212-9222, which takes it from `REMOTIX_POINTER.shape()` ~9145-9186):
        a PNG image and its hotspot.  An observer
        (`MutationObserver`) writes the INSTANT of every change, and a listener
        the instant of the movement: the latency is measured INSIDE the page.

⛔⛔ THE YARDSTICK — THE IMAGE, NOT A COUNTER.
   The project's `LEZIONI`: *«counters do not see the image»* — a
   received `CURSOR_SHAPE` counts as a right one even if it carries the arrow.
   ⇒ Every image is CLASSIFIED from its pixels (`ranking()`): the
   silhouette is taken (alpha >= 128), its rectangle, and where the hotspot falls:
     arrow      hotspot in the top left corner of the silhouette
     horizontal  the horizontal resize arrow: hotspot at
                  half height, silhouette symmetric above/below, thin, with
                  the HORIZONTAL shaft passing through the hotspot
     body_text        hotspot at the centre, silhouette taller than wide
   ⛔⭐ `[M]` 24 Sep 2026, gnome: Adwaita's «e-resize» is NOT the double
       arrow with the hotspot at the centre one expected — it is ONE arrow
       pointing right against a bar, 18x17, with the hotspot on the
       bar (0,92 of the width, 0,56 of the height).  ⇒ The class does not
       demand the horizontal centre: it demands half HEIGHT and the horizontal
       shaft.  Breeze's double (`size_hor`) fits inside it all the same.
     nascosta  `cursor: none` (§5.5, width and height zero)
     the_other     everything else (a hand, an hourglass, ...)
   And a step is GREEN only if the shape IN FORCE `CAP_MS` (300 ms) after the
   movement is of the expected class, and it ARRIVED after the movement.

⛔⭐ WHY THE EDGE IS A SCAN AND NOT A POINT — the resize
   zone is NOT in the same place on the four desktops:
     `[M]` KWin (KDE)  `size_hor` only ON the edge (from 1 px inside to 1 px
                       outside); at 3 px outside there is already the normal arrow
     `[M]` labwc       from the edge pixel up to 7 px outside
     `[M]` GNOME       in the window's shadow (Firefox draws its own
                       borders): `[M]` from this mesh: from +1 px
   ⇒ A fixed «3 px outside» would give red to KWin for something KWin does
     on purpose.  We walk from `SCAN[0]` to `SCAN[-1]` px from the edge
     (the last pixel of the page), one pixel per step, `SCAN_STEP_S`
     per step: GREEN if at one point the shape becomes «horizontal» within
     300 ms of the movement that brought it, and the report says WHERE.

⛔ HOW I KNOW IT CAN GIVE RED — `--wrong-shape`.
   The table of expectations is shifted by one (centre⇒horizontal, edge⇒text,
   text⇒arrow) and THE SAME IMAGES are judged twice:
     · with the right table       ⇒ it must be GREEN (the healthy control)
     · with the shifted table     ⇒ it must be RED
   ⭐ The red can come only from the classes, that is from the PIXELS: the number of
     changes and the times are the same in the two judgements.
   ⛔ It reads THE OTHER WAY ROUND, like every fault of the net (`11-gancio.sh`,
     `run_mesh`): 0 = the fault was SEEN, 1 = NOT seen, 3 = the
     healthy control was not green ⇒ nothing could be injected.

⚠ OUTCOMES: 0 green · 1 red · 3 «I could not look», with the reason.
   The 3 is the BENCH's (the window does not show, the movement did not start,
   the page is not in `system_wide` mode); the red is the PRODUCT's (the shape
   does not arrive, arrives late, or is wrong).

⚠ WHERE IT RUNS: on the machine that has the browsers (the server, `REMOTIX_ON_SERVER=1`
  with nested `labwc` — `[M]` 24 Sep 2026, the tablet is the bottleneck), and one enters
  the box with `fondamenta/strumenti/sshpw.py` + `podman exec`, like
  `12-c20-veri.py`.  ⚠ The tenant is `c21u<n>` (C19's pattern
  `^c[0-9]+b?u[0-9]+$`): if the bench died half-way, the hook clears it out.
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


# ⛔ Imported, not copied: the browser drivers and the road into the box.
#   `12-c20-veri` brings `12-client-veri` (REAL) along — only one in memory.
C20V = _load("c20_veri", os.path.join(BENCHES, "12-c20-veri.py"))
REAL = C20V.REAL
GREEN, RED, BLIND = REAL.GREEN, REAL.RED, REAL.BLIND
PORTS = C20V.PORTS
OUTCOME_NAME = {GREEN: "GREEN", RED: "RED", BLIND: "I COULD NOT LOOK"}

# ⭐ The tenant: a name of the net, which C19 recognises and the hook clears out.
TENANT_PATTERN = re.compile(r"^c21u[0-9]+$")

# ---------------------------------------------------------------------------
# ⛔ THE NUMBERS — each with its reason.
# ---------------------------------------------------------------------------
# The user's request: the shape changes within 300 ms of the movement.
CAP_MS = 300.0
# How long we look AFTER the ceiling: not to give green, but to say WHEN
# a late shape arrived (a red «at 450 ms» is cured, «never» is another
# defect).
LOOK_S = 2.0
# ⭐ The scan of the right edge, in DESKTOP pixels relative to the last
#   pixel of the page: from 4 inside to 8 outside (the three measured zones are between
#   -1 and +7).  ⚠ The step lasts longer than the ceiling, so every change is attributed
#   to ONE movement only: the one right before.
SCAN = tuple(range(-4, 9))
SCAN_STEP_S = 0.4
# The page colours, and the tolerance: the chain goes through H.264 4:2:0, which
# subsamples the chroma (§4.3 of phase 11, the same reason as C2).
CYAN = (0x00, 0xFF, 0xFF)
YELLOW = (0xFF, 0xFF, 0x00)
TOLERANCE = 60
# The window must be at least this share of the canvas, or it is a leftover.
MIN_AREA = 0.02
# The alpha threshold of the silhouette: the theme's soft edges are not silhouette.
ALPHA = 128

# ⭐ THE TABLE OF EXPECTATIONS, and the same one shifted by one (the fault).
STEPS = ("center", "edge", "body_text")
EXPECTED = {"center": "arrow", "edge": "horizontal", "body_text": "body_text"}
EXPECTED_WRONG = {"center": "horizontal", "edge": "body_text", "body_text": "arrow"}

# ⭐ THE KNOWN PAGE.  Cyan background with `cursor: default`, and a yellow box
#   with `cursor: text` at the top left — far from the centre, so the centre
#   of the window is pure cyan.  ⚠ The `cursor` rules are declared and not
#   left to the engine: without them, the text cursor would appear only over the
#   glyphs and between one letter and the next it would go back to the arrow.
#   ⛔ No external resource: the box has no network to the outside.
PAGE = """<!doctype html>
<meta charset="utf-8"><title>REMOTIX C21</title>
<style>
 html,body{margin:0;padding:0;width:100%;height:100%;background:#00FFFF;cursor:default;overflow:hidden}
 #t{position:absolute;left:6%;top:8%;width:34%;height:30%;background:#FFFF00;color:#000;
    cursor:text;font:28px/1.25 sans-serif;overflow:hidden}
</style>
<div id="t">REMOTIX C21 &mdash; the pointer over this text must become
the text bar. REMOTIX C21 &mdash; text text text text text text
text text text text text text text text text text text text</div>
"""
PROFILE = ".c21-profile_v"
PAGE_FILE = "c21-finestra.html"
PREFERENCES = """user_pref("browser.shell.checkDefaultBrowser", false);
user_pref("browser.aboutwelcome.enabled", false);
user_pref("browser.startup.homepage_override.mstone", "ignore");
user_pref("startup.homepage_welcome_url", "");
user_pref("startup.homepage_welcome_url.additional", "");
user_pref("datareporting.policy.dataSubmissionEnabled", false);
user_pref("toolkit.telemetry.reportingpolicy.firstRun", false);
user_pref("browser.sessionstore.resume_from_crash", false);
user_pref("browser.tabs.warnOnClose", false);
"""


def xulstore(largo, alto):
    """⭐ The size of the Firefox window, declared in the profile.

    ⛔ A maximised window has no right edge inside the screen: without
       this line the test would depend on what the desktop decides."""
    return json.dumps({"chrome://browser/content/browser.xhtml": {"main-window": {
        "width": str(int(largo)), "height": str(int(alto)),
        "screenX": "80", "screenY": "80", "sizemode": "normal"}}})


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS — and they are the ones `--certify` tests
# ═══════════════════════════════════════════════════════════════════════════
_SKIN_URL = re.compile(r'url\(\s*["\']?(data:image/png;base64,[^"\')]+)["\']?\s*\)'
                    r'\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)')


def read_guise(style):
    """From the `cursor` rule of `#display_screen` to (png, hx, hy) — or a word.

    Returns ("png", bytes, hx, hy) · ("nascosta",) · ("system_wide",) if there is
    no garment (the browser's cursor is its own) · ("illeggibile", s)."""
    s = (style or "").strip()
    if not s or s in ("auto", "default"):
        return ("system_wide",)
    if s == "none":
        return ("nascosta",)
    m = _SKIN_URL.search(s)
    if not m:
        return ("illeggibile", s[:80])
    try:
        png = base64.b64decode(m.group(1).split(",", 1)[1])
    except Exception:                            # noqa: BLE001
        return ("illeggibile", s[:80])
    return ("png", png, float(m.group(2)), float(m.group(3)))


def classify_shape(width_px, height_px, alpha_ch, hx, hy):
    """⭐ The class of a cursor from its PIXELS: `alpha_ch` is the list row by
    row of the alpha values.  Returns (class, description)."""
    xs = [i % width_px for i, a in enumerate(alpha_ch) if a >= ALPHA]
    ys = [i // width_px for i, a in enumerate(alpha_ch) if a >= ALPHA]
    if not xs:
        return "nascosta", "%dx%d without opaque pixels" % (width_px, height_px)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    rx, ry = (hx - x0 + 0.5) / w, (hy - y0 + 0.5) / h
    filled = set(zip(xs, ys))
    # the above-below symmetry of the silhouette inside its rectangle
    symm = sum(1 for (x, y) in filled if (x, y0 + y1 - y) in filled) / len(filled)
    # how much of the rectangle is full: an arrow is thin, an hourglass is not
    full = len(filled) / float(w * h)
    # the shaft: the longest opaque run on the hotspot's row (± 1)
    stem = 0
    for y in (int(hy) - 1, int(hy), int(hy) + 1):
        run = 0
        for x in range(x0, x1 + 1):
            run = run + 1 if (x, y) in filled else 0
            stem = max(stem, run)
    desc = ("%dx%d, silhouette %dx%d at (%d,%d), hotspot (%g,%g) = %.2f,%.2f of the "
            "silhouette, above/below symmetry %.2f, full %.2f, shaft %d/%d"
            % (width_px, height_px, w, h, x0, y0, hx, hy, rx, ry, symm, full, stem, w))
    if rx <= 0.2 and ry <= 0.2:
        return "arrow", desc
    if 0.25 <= rx <= 0.75 and 0.25 <= ry <= 0.75 and h >= 1.5 * w:
        return "body_text", desc
    if 0.3 <= ry <= 0.7 and w >= 0.8 * h and symm >= 0.8 and full <= 0.68 \
            and stem >= 0.6 * w:
        return "horizontal", desc
    return "the_other", desc


def ranking(guise):
    """(class, description) of a garment read by `read_guise`."""
    if guise[0] == "nascosta":
        return "nascosta", "cursor: none"
    if guise[0] == "system_wide":
        return "system_wide", "no remote shape worn (the browser's cursor)"
    if guise[0] != "png":
        return "illeggibile", guise[1]
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(guise[1])).convert("RGBA")
    except Exception as e:                       # noqa: BLE001
        return "illeggibile", "unreadable PNG: %s" % e
    l, a = im.size
    alpha_ch = [p[3] for p in im.getdata()]
    return classify_shape(l, a, alpha_ch, guise[2], guise[3])


def judge_step(label_name, expected_val, before, changes, t_move):
    """⭐ The judgement of a step.

    `before`  the class in force at the instant of the movement
    `changes`  [(t_ms, class, description)] the changes after the movement
    Returns (outcome, reason, ms of the right change | None)."""
    after = [c for c in changes if c[0] >= t_move]
    if not after:
        if before == expected_val:
            # ⛔ It is not a green: the shape was already that one, the step proves
            #   nothing — and the start on the text exists so as not to end up here.
            return BLIND, ("%s: the shape was already «%s» before the movement and did not "
                           "change: the step proves nothing" % (label_name, expected_val)), None
        return RED, ("%s: in %.0f ms the shape DID NOT CHANGE (stays «%s», expected «%s»)"
                       % (label_name, LOOK_S * 1000, before, expected_val)), None
    within = [c for c in after if c[0] - t_move <= CAP_MS]
    if not within:
        c = after[0]
        return RED, ("%s: the shape changed at %.0f ms, BEYOND the %.0f (arrived «%s», "
                       "expected «%s»)" % (label_name, c[0] - t_move, CAP_MS, c[1], expected_val)), None
    effect = within[-1]
    if effect[1] != expected_val:
        return RED, ("%s: at %.0f ms the shape is «%s», expected «%s» (%s)"
                       % (label_name, CAP_MS, effect[1], expected_val, effect[2])), None
    correct = next(c for c in within if c[1] == expected_val)
    ms = correct[0] - t_move
    return GREEN, ("%s: «%s» at %.0f ms (%s)" % (label_name, expected_val, ms, correct[2])), ms


def judge_scan(label_name, expected_val, before, changes, moves):
    """⭐ The judgement of the EDGE: a scan, not a point.

    `moves`  [(offset_px, t_ms)] the instant of every movement of the scan
    Returns (outcome, reason, (offset, ms) | None)."""
    if not moves:
        return BLIND, "%s: the scan has no movements" % label_name, None
    moves = sorted(moves, key=lambda m: m[1])
    after = [c for c in changes if c[0] >= moves[0][1]]
    late = None
    for c in after:
        if c[1] != expected_val:
            continue
        # ⭐ the movement that brought it: the last one before the change
        chi = [m for m in moves if m[1] <= c[0]][-1]
        ms = c[0] - chi[1]
        if ms <= CAP_MS:
            return GREEN, ("%s: «%s» at %+d px from the edge, %.0f ms after the movement (%s)"
                           % (label_name, expected_val, chi[0], ms, c[2])), (chi[0], ms)
        late = late or (chi[0], ms)
    if late:
        return RED, ("%s: «%s» arrived at %+d px but %.0f ms after the movement, BEYOND "
                       "the %.0f" % (label_name, expected_val, late[0], late[1], CAP_MS)), None
    if not after and before == expected_val:
        return BLIND, ("%s: the shape was already «%s» before the scan and did not "
                       "change: the step proves nothing" % (label_name, expected_val)), None
    views = []
    for c in after:
        if c[1] not in views:
            views.append(c[1])
    return RED, ("%s: from %+d to %+d px from the edge the shape is NEVER «%s» (%s)"
                   % (label_name, moves[0][0], moves[-1][0], expected_val,
                      ("seen: " + ", ".join(views)) if views
                      else "stays «%s», no change" % before)), None


def judge_all(observed, table):
    """[(step, outcome, reason, ms)] and the overall outcome, for a table."""
    line_list = []
    for p in STEPS:
        o = observed.get(p)
        if o is None:
            line_list.append((p, BLIND, "%s: not observed" % p, None))
            continue
        if o.get("scan"):
            e, m, ms = judge_scan(p, table[p], o["before"], o["changes"],
                                         o["scan"])
        else:
            e, m, ms = judge_step(p, table[p], o["before"], o["changes"], o["t_move"])
        line_list.append((p, e, m, ms))
    v = [r[1] for r in line_list]
    return (RED if RED in v else (BLIND if BLIND in v else GREEN)), line_list


def _near(p, c, toll=TOLERANCE):
    return abs(p[0] - c[0]) <= toll and abs(p[1] - c[1]) <= toll and abs(p[2] - c[2]) <= toll


def find_window(width_px, height_px, pixel, step=1):
    """⭐ The test window in the photograph: dict or (None, reason).

    `pixel` is the RGB list row by row.  The CYAN of the page is looked for:
      · its rectangle, from the columns and rows where the cyan is plentiful (the
        30 % of the maximum: a black text or an icon does not shift it)
      · ⭐ the FINE right edge: on five rows around the centre we walk
        from the centre to the right as long as the pixel is cyan, and take the
        median — the last cyan pixel, in photograph pixels
      · the YELLOW text box, inside.
    ⚠ `step`: the rectangle's sums are done on one pixel every `step` (in 4K
      they are 8 million pixels, and without numpy the whole round costs ~10 s per
      photograph); the fine edge is looked for pixel by pixel anyway."""
    clr = [0] * width_px
    rig = [0] * height_px
    gcol, gray_rows = [0] * width_px, [0] * height_px
    for y in range(0, height_px, step):
        base = y * width_px
        for x in range(0, width_px, step):
            p = pixel[base + x]
            if _near(p, CYAN):
                clr[x] += 1
                rig[y] += 1
            elif _near(p, YELLOW):
                gcol[x] += 1
                gray_rows[y] += 1
    if max(clr) == 0:
        return None, "no cyan pixel: the test window does not show"
    xs = [x for x, n in enumerate(clr) if n >= 0.3 * max(clr)]
    ys = [y for y, n in enumerate(rig) if n >= 0.3 * max(rig)]
    x0, x1, y0, y1 = min(xs), max(xs) + step - 1, min(ys), max(ys) + step - 1
    if (x1 - x0 + 1) * (y1 - y0 + 1) < MIN_AREA * width_px * height_px:
        return None, ("the cyan is there but it is small (%dx%d): it is not the window"
                      % (x1 - x0 + 1, y1 - y0 + 1))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    # ⚠ with `step` the centre must be put back on a sampled row of the cyan
    cx, cy = cx - cx % step, cy - cy % step
    if not _near(pixel[cy * width_px + cx], CYAN):
        return None, "the centre of the cyan (%d,%d) is not cyan: the window is covered" % (cx, cy)
    borders = []
    for dy in (-20, -10, 0, 10, 20):
        y = min(max(cy + dy, 0), height_px - 1)
        x = cx
        while x + 1 < width_px and _near(pixel[y * width_px + x + 1], CYAN):
            x += 1
        borders.append(x)
    borders.sort()
    right = borders[2]
    if max(gcol) == 0:
        return None, "no yellow pixel: the text box does not show"
    gx = [x for x, n in enumerate(gcol) if n >= 0.3 * max(gcol)]
    gy = [y for y, n in enumerate(gray_rows) if n >= 0.3 * max(gray_rows)]
    return {"cyan": [x0, y0, x1, y1], "center": [cx, cy], "right": right,
            "borders": borders,
            "body_text": [(min(gx) + max(gx)) // 2, (min(gy) + max(gy)) // 2],
            "yellow": [min(gx), min(gy), max(gx), max(gy)]}, ""


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION OF THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def _png(im):
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def fake_cursors():
    """The cursors drawn here, with the shape of the real ones."""
    from PIL import Image, ImageDraw
    fr = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(fr)
    d.polygon([(3, 3), (3, 20), (7, 16), (10, 22), (12, 21), (9, 15), (15, 15)],
              fill=(255, 255, 255, 255), outline=(0, 0, 0, 255))
    # Breeze's double: shaft and two tips, hotspot at the centre
    dp = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(dp)
    d.rectangle([9, 14, 22, 17], fill=(0, 0, 0, 255))
    d.polygon([(3, 15), (10, 8), (10, 23)], fill=(0, 0, 0, 255))
    d.polygon([(28, 15), (21, 8), (21, 23)], fill=(0, 0, 0, 255))
    # ⭐ Adwaita's e-resize, `[M]` 24 Sep 2026: arrow towards the right against
    #   a bar, hotspot on the bar
    ae = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(ae)
    d.rectangle([17, 4, 20, 20], fill=(0, 0, 0, 255))
    d.rectangle([3, 11, 16, 13], fill=(0, 0, 0, 255))
    d.polygon([(11, 5), (16, 12), (11, 19)], fill=(0, 0, 0, 255))
    te = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
    d = ImageDraw.Draw(te)
    d.rectangle([15, 5, 16, 26], fill=(0, 0, 0, 255))
    d.rectangle([11, 5, 20, 6], fill=(0, 0, 0, 255))
    d.rectangle([11, 25, 20, 26], fill=(0, 0, 0, 255))
    # a full hourglass with the hotspot at the centre: it is NOT a resize
    cl = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    ImageDraw.Draw(cl).ellipse([2, 2, 21, 21], fill=(0, 0, 0, 255))
    # a hand: hotspot at the top, at the finger
    ma = Image.new("RGBA", (24, 24), (0, 0, 0, 0))
    d = ImageDraw.Draw(ma)
    d.rectangle([8, 2, 11, 12], fill=(0, 0, 0, 255))
    d.rectangle([5, 10, 19, 21], fill=(0, 0, 0, 255))
    return {"arrow": (("png", _png(fr), 3, 3), "arrow"),
            "Breeze double arrow": (("png", _png(dp), 15, 15), "horizontal"),
            "Adwaita e-resize": (("png", _png(ae), 19, 12), "horizontal"),
            "text bar": (("png", _png(te), 15, 15), "body_text"),
            "full hourglass": (("png", _png(cl), 11, 11), "the_other"),
            "hand": (("png", _png(ma), 9, 2), "the_other")}


def certify():
    print("⭐ 11-c21 · CERTIFICATION OF THE PURE FUNCTIONS")
    troubles, done = [], []

    def prova(what, real, detail=""):
        done.append(what)
        print("   %s %s%s" % ("⭐ ok  " if real else "⛔ NO  ", what,
                              (" — " + detail) if detail else ""))
        if not real:
            troubles.append(what)

    try:
        c = fake_cursors()
    except ImportError:
        print("⛔ PIL is not there: I cannot certify ⇒ 3")
        return 3
    # 1. the CSS rule is read, in the two spellings of the browsers
    dv = c["Breeze double arrow"][0]
    b64 = base64.b64encode(dv[1]).decode()
    for s in ('url("data:image/png;base64,%s") 15 15, default' % b64,
              "url(data:image/png;base64,%s) 15 15, default" % b64):
        v = read_guise(s)
        prova("read_guise: %s…" % s[:14], v[0] == "png" and v[2:] == (15.0, 15.0))
    prova("read_guise: «none» ⇒ hidden", read_guise("none") == ("nascosta",))
    prova("read_guise: empty ⇒ system", read_guise("") == ("system_wide",))
    # 2. the classifier from the PIXELS
    for label_name, (guise, wait) in c.items():
        k, d = ranking(guise)
        prova("ranking %s ⇒ %s" % (label_name, k), k == wait, d)
    # ⛔ and the same image of the double with the hotspot at the top left
    #   is NOT a resize: the hotspot is part of the shape
    k, d = ranking(dv[:2] + (3, 8))
    prova("double with the hotspot at the top left ⇒ not horizontal (%s)" % k,
          k != "horizontal", d)
    # 3. the judgement of the step
    fr, dp = ranking(c["arrow"][0]), ranking(dv)
    te = ranking(c["text bar"][0])
    cases = [
        ("right at 120 ms ⇒ GREEN", ("arrow", [(1120, dp[0], dp[1])], 1000), GREEN),
        ("right at 350 ms ⇒ RED", ("arrow", [(1350, dp[0], dp[1])], 1000), RED),
        ("no change ⇒ RED", ("arrow", [], 1000), RED),
        ("wrong at 100 ms ⇒ RED", ("arrow", [(1100, fr[0], fr[1])], 1000), RED),
        ("already right and still ⇒ 3", ("horizontal", [], 1000), BLIND),
        ("change from BEFORE the movement ⇒ RED", ("arrow", [(900, dp[0], dp[1])], 1000),
         RED),
        ("right at 100 then wrong at 250 ⇒ RED",
         ("arrow", [(1100, dp[0], dp[1]), (1250, fr[0], fr[1])], 1000), RED),
    ]
    for label_name, (before, changes, t), expected_val in cases:
        e, m, _ms = judge_step("edge", "horizontal", before, changes, t)
        prova("judge_step: %s" % label_name, e == expected_val, m)
    # 3-bis. the scan of the edge (three desktops, three places)
    moves = [(k, 10000 + 400 * i) for i, k in enumerate(SCAN)]
    t_di = dict(moves)
    scasi = [
        ("KWin: on the edge (-1 px) ⇒ GREEN at -1",
         ("arrow", [(t_di[-1] + 40, dp[0], dp[1]), (t_di[2] + 40, fr[0], fr[1])]),
         GREEN, -1),
        ("GNOME: in the shadow (+4 px) ⇒ GREEN at +4",
         ("arrow", [(t_di[4] + 30, dp[0], dp[1])]), GREEN, 4),
        ("never horizontal ⇒ RED", ("arrow", [(t_di[3] + 30, te[0], te[1])]), RED, None),
        ("no change ⇒ RED", ("arrow", []), RED, None),
        ("horizontal at 350 ms from its movement ⇒ RED",
         ("arrow", [(t_di[5] + 350, dp[0], dp[1])]), RED, None),
    ]
    for label_name, (before, changes), expected_val, dove in scasi:
        e, m, x = judge_scan("edge", "horizontal", before, changes, moves)
        prova("judge_scan: %s" % label_name,
              e == expected_val and (dove is None or (x and x[0] == dove)), m)
    e, m, _x = judge_scan("edge", "body_text", "arrow",
                                 [(t_di[4] + 30, dp[0], dp[1])], moves)
    prova("judge_scan with the shifted table ⇒ RED", e == RED, m)

    # 4. ⭐ the injected fault: the SAME observations, two tables
    oss = {"center": {"before": "body_text", "changes": [(1080, fr[0], fr[1])], "t_move": 1000},
           "edge": {"before": "arrow", "changes": [(2090, dp[0], dp[1])], "t_move": 2000,
                     "scan": [(-1, 2000), (0, 2400)]},
           "body_text": {"before": "horizontal", "changes": [(3070, te[0], te[1])],
                     "t_move": 3000}}
    es, _ = judge_all(oss, EXPECTED)
    eg, line_list = judge_all(oss, EXPECTED_WRONG)
    prova("right table ⇒ GREEN, shifted table ⇒ RED", es == GREEN and eg == RED,
          "healthy %s · fault %s (%s)" % (es, eg, line_list[0][2]))
    # 5. the window in the photograph
    L, A = 400, 250
    px = [((x * 7 + y * 3) % 90 + 60,) * 3 for y in range(A) for x in range(L)]
    for y in range(40, 200):
        for x in range(50, 300):
            px[y * L + x] = (8, 250, 244)        # cyan «after encoding»
    for y in range(52, 100):
        for x in range(62, 150):
            px[y * L + x] = (250, 248, 10)
    for x in range(70, 140, 6):                  # black text in the yellow
        px[70 * L + x] = (0, 0, 0)
    f, reason_text = find_window(L, A, px)
    prova("find_window: right edge = 299", bool(f) and f["right"] == 299,
          reason_text or json.dumps(f))
    f3, why3 = find_window(L, A, px, step=3)
    prova("find_window with step 3: right edge = 299 all the same",
          bool(f3) and f3["right"] == 299, why3 or json.dumps(f3))
    prova("find_window: the text falls in the yellow",
          bool(f) and 62 <= f["body_text"][0] < 150 and 52 <= f["body_text"][1] < 100)
    f2, why2 = find_window(L, A, [(90, 90, 90)] * (L * A))
    prova("find_window: without cyan ⇒ no window", f2 is None, why2)
    print()
    if troubles:
        print("⛔ CERTIFICATION FAILED: %d tests out of %d" % (len(troubles), len(done)))
        return 1
    print("⭐ CERTIFIED: the classifier tells the three shapes apart from the pixels, the "
          "judge\n   gives red to the late, the still and the wrong, and the shifted "
          "table is RED.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE PAGE
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ The observer: the instant of every movement and of every change of the garment,
#   with the page's `performance.now()` — that is the latency measured where the
#   user sees it, not by the bench waiting for Marionette's answers.
JS_OBSERVE = r"""
(function () {
  if (window.__C21__) return;
  const s = document.getElementById('display_screen');
  if (!s) return;
  const C = window.__C21__ = { moves: [], dress: [] };
  addEventListener('pointermove', function (e) {
    C.moves.push([performance.now(), e.clientX, e.clientY]);
    if (C.moves.length > 200) C.moves.shift();
  }, true);
  const read_it = function () {
    const v = s.style.cursor || '';
    const u = C.dress.length ? C.dress[C.dress.length - 1][1] : null;
    if (v === u) return;
    C.dress.push([performance.now(), v]);
    if (C.dress.length > 60) C.dress.shift();
  };
  read_it();
  new MutationObserver(read_it).observe(s, { attributes: true, attributeFilter: ['style'] });
})();
"""

JS_NOW = "return performance.now();"

JS_AFTER = r"""
const C = window.__C21__;
if (!C) return null;
const t = arguments[0];
let before = '';
for (const v of C.dress) if (v[0] <= t) before = v[1];
const st = window.REMOTIX && REMOTIX.input_classic ? REMOTIX.input_classic.state() : null;
return { moves: C.moves.filter(m => m[0] > t),
         dress: C.dress.filter(v => v[0] > t),
         before: before,
         spedito: st ? st.last_sent : null,
         usable: st ? st.usable : null };
"""

JS_GEOMETRY = r"""
const P = window.REMOTIX_POINTER, t = document.getElementById('display_screen');
if (!P || !P.geometry || !t) return null;
const g = P.geometry();
return { left: g.r.left, top: g.r.top, width: g.r.width, height: g.r.height,
         bx0: g.bx0, by0: g.by0, left_side: g.left_side, sy: g.sy, vx: g.vx, vy: g.vy,
         tl: g.tl, ta: g.ta, bw: t.width, bh: t.height,
         manner: document.body.dataset.ptr || null,
         arrangement: document.body.dataset.arrangement || null };
"""


def full_photo(g):
    """The photograph of the canvas at FULL resolution.  ⚠ The Chrome driver of
    `12-client-veri` reduces it to 640 px of width (for the degenerate judge):
    here the single pixels of the edge are needed, and scale 1 is asked for."""
    if hasattr(g, "cdp"):
        r = g.js("const t=document.getElementById('display_screen');"
                 "if(!t) return null; const b=t.getBoundingClientRect();"
                 "return [b.left, b.top, b.width, b.height];")
        if not r:
            return None
        if getattr(g, "scale_photo", 1) != 1:
            # ⚠ the phone (phase 19 §5): Chrome Android with `clip.scale` > 1 does not
            #   enlarge, it REPEATS the page as tiles (2 Oct 2026: the scene three times
            #   across).  ⇒ the photo of the whole glass, already in device pixels,
            #   and the crop of the canvas here.
            import io
            from PIL import Image
            s = g.cdp.call("Page.captureScreenshot", format="png")
            im = Image.open(io.BytesIO(base64.b64decode(s["data"])))
            k = im.size[0] / float(g.js("return window.innerWidth;") or im.size[0])
            im = im.crop((round(r[0] * k), round(r[1] * k),
                          round((r[0] + r[2]) * k), round((r[1] + r[3]) * k)))
            b = io.BytesIO()
            im.save(b, "PNG")
            return b.getvalue()
        s = g.cdp.call("Page.captureScreenshot", format="png",
                         clip={"x": r[0], "y": r[1], "width": r[2], "height": r[3],
                               "scale": 1})
        return base64.b64decode(s["data"])
    png, _p = g.snapshot_canvas()
    return png


def from_photo_to_desktop(geo, pw, ph, px, py):
    """Photograph pixels ⇒ desktop pixels (floating point)."""
    return ((px * geo["bw"] / pw - geo["bx0"]) / geo["left_side"],
            (py * geo["bh"] / ph - geo["by0"]) / geo["sy"])


def desktop_to_glass(geo, X, Y):
    """Desktop pixels ⇒ browser coordinates (the same as `cl_draw`)."""
    return (geo["left"] + (geo["bx0"] + X * geo["left_side"]) * geo["vx"],
            geo["top"] + (geo["by0"] + Y * geo["sy"]) * geo["vy"])


def search_window(g, wait, store, label_name):
    """Waits for the test window to appear STILL (two equal photographs)."""
    from PIL import Image
    fine = time.time() + wait
    latest, reason_text, png = None, "no photograph", None
    while time.time() < fine:
        time.sleep(1.5)
        try:
            png = full_photo(g)
        except Exception as e:                   # noqa: BLE001
            reason_text = "photograph failed: %s" % str(e)[:120]
            continue
        if not png:
            reason_text = "the canvas cannot be photographed"
            continue
        im = Image.open(io.BytesIO(png)).convert("RGB")
        f, reason_text = find_window(im.size[0], im.size[1], list(im.getdata()),
                                   step=max(1, im.size[0] // 960))
        if not f:
            latest = None
            continue
        f["picture"] = list(im.size)
        if latest and all(abs(a - b) <= 2 for a, b in zip(latest["cyan"], f["cyan"])) \
                and abs(latest["right"] - f["right"]) <= 1:
            if store:
                with open(os.path.join(store, "%s-finestra.png" % label_name), "wb") as fh:
                    fh.write(png)
            return f, ""
        latest = f
    if store and png:
        with open(os.path.join(store, "%s-finestra-NON-trovata.png" % label_name), "wb") as fh:
            fh.write(png)
    return None, reason_text


# ⭐ The ESC in the key table of `12-client-veri` (which has only Control and
#   the arrow): an entry is ADDED, the driver is not copied.
REAL.KEYS.setdefault("Escape", {"key": "Escape", "code": "Escape", "vk": 27,
                                 "wd": "\ue00c"})


def wake(g, geo):
    """A real ESC, with the pointer on the canvas and the focus outside the form."""
    try:
        g.js("if (document.activeElement && document.activeElement.blur) "
             "document.activeElement.blur(); return 1;")
        x, y = desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * 0.5)
        g.move_to(x, y)
        time.sleep(0.3)
        g.key("Escape")
        time.sleep(1.5)
        return "ESC sent"
    except Exception as e:                       # noqa: BLE001
        return "⚠ ESC not sent: %s" % str(e)[:120]


def scan_edge(g, geo, Xedge, Y):
    """⭐ The edge, one pixel per step.  Returns (final X, [(offset, t0)], t0, data)."""
    t_start = g.js(JS_NOW)
    steps = []
    for k in SCAN:
        vx, vy = desktop_to_glass(geo, Xedge + k, Y)
        steps.append((k, g.js(JS_NOW)))
        g.move_to(vx, vy)
        time.sleep(SCAN_STEP_S)
    time.sleep(max(0.0, LOOK_S - SCAN_STEP_S))
    return Xedge + SCAN[-1], steps, t_start, g.js(JS_AFTER, t_start)


def one_step(g, x, y):
    """Moves the pointer and gathers what the page saw."""
    t0 = g.js(JS_NOW)
    g.move_to(x, y)
    time.sleep(LOOK_S)
    return t0, g.js(JS_AFTER, t0)


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE BOX
# ═══════════════════════════════════════════════════════════════════════════
def prepare_home(sc, chi, largo, alto):
    """The known page and the Firefox profile, in the tenant's home."""
    b = lambda s: base64.b64encode(s.encode()).decode()     # noqa: E731
    c, t = sc.inside(
        "set -e; h=/home/%s; mkdir -p $h/%s; "
        "echo %s | base64 -d > $h/%s; echo %s | base64 -d > $h/%s/user.js; "
        "echo %s | base64 -d > $h/%s/xulstore.json; chown -R %s: $h/%s $h/%s; echo ready"
        % (chi, PROFILE, b(PAGE), PAGE_FILE, b(PREFERENCES), PROFILE,
           b(xulstore(largo, alto)), PROFILE, chi, PROFILE, PAGE_FILE), 60)
    return c == 0, t


def turn_on_window(sc, chi):
    """⭐ NORMAL `firefox-esr` in the tenant's session: it has the borders."""
    c, t = sc.inside(
        "u=$(id -u %(c)s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
        "| head -1); [ -n \"$d\" ] || { echo 'no wayland socket'; exit 2; }; "
        "setsid runuser -u %(c)s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=/home/%(c)s firefox-esr --no-remote --new-instance "
        "--profile /home/%(c)s/%(p)s file:///home/%(c)s/%(f)s "
        "< /dev/null > /home/%(c)s/.c21-firefox.log 2>&1 & "
        "for i in $(seq 1 40); do pgrep -u %(c)s -f firefox-esr >/dev/null && "
        "{ echo started; exit 0; }; sleep 0.25; done; echo 'it was not seen'; exit 1"
        % {"c": chi, "p": PROFILE, "f": PAGE_FILE}, 60)
    return c == 0, t


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST OF ONE BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def observe(label_name, o, sc, chi):
    """Returns (row, observed) — `observed` is None if nothing was looked at."""
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
            return dict(row, outcome=BLIND, reason_text="the page does not open: " + m), None
        e, m, s = pr.enter(o.password)
        if e != GREEN:
            return dict(row, outcome=BLIND, reason_text="the login: " + m), None
        e, m, s = pr.first_frame()
        e, m = C20V.desktop_dark_but_alive(e, m, s)
        print("   ⭐ first frame: %s" % m, flush=True)
        if e != GREEN:
            return dict(row, outcome=BLIND, reason_text="without an image there is no looking: " + m), None
        geo = g.js(JS_GEOMETRY)
        if not geo:
            return dict(row, outcome=BLIND, reason_text="`REMOTIX_POINTER.geometry` is not there"), None
        row["geometry"] = {k: geo[k] for k in ("tl", "ta", "bw", "bh", "left_side", "vx",
                                                 "manner", "arrangement")}
        print("   canvas %sx%s · buffer %sx%s · mode «%s» · layout «%s»"
              % (geo["tl"], geo["ta"], geo["bw"], geo["bh"], geo["manner"],
                 geo["arrangement"]), flush=True)
        if geo["manner"] != "system_wide" or geo["arrangement"] != "classic":
            # ⛔ Outside `system_wide` mode the garment does not go on the canvas: looking at
            #   the `cursor` rule would say «it does not change» to a healthy product.
            return dict(row, outcome=BLIND, reason_text="the page is not in «system_wide» "
                        "classic mode (mode %s, layout %s): the garment cannot be read"
                        % (geo["manner"], geo["arrangement"])), None

        # ── the wake-up: an ESC BEFORE opening the window ──────────────────
        # ⚠ `[M]` 24 Sep 2026, gnome: the session is born in the OVERVIEW,
        #   and there the window is a shrunk preview on which the desktop
        #   does not change shape (the first run of this mesh: false RED, three
        #   steps without a change).  ⭐ It is C4's wake-up (`11-c4…`, «THE
        #   WAKE-UP»), sent as the user sends it: a REAL key of the
        #   browser, with the focus outside the form's fields (`cl_in_form`).
        #   ⛔ No click to give the focus: the first click on the canvas asks for the
        #     `Pointer Lock`, and from there the movements would be relative.
        e_sv = wake(g, geo)
        print("   wake-up: %s" % e_sv, flush=True)

        # ── the test window ────────────────────────────────────────────────
        largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
        ok, t = prepare_home(sc, chi, largo_f, alto_f)
        if not ok:
            return dict(row, outcome=BLIND, reason_text="the home cannot be prepared: %s" % t[-200:]), None
        ok, t = turn_on_window(sc, chi)
        if not ok:
            return dict(row, outcome=BLIND, reason_text="firefox-esr does not start: %s" % t[-200:]), None
        f, reason_text = search_window(g, o.wait_window, o.store, label_name)
        if not f:
            return dict(row, outcome=BLIND, reason_text="the test window does not show within "
                        "%d s: %s" % (o.wait_window, reason_text)), None
        pw, ph = f["picture"]
        # ⛔ A preview is not a window: if the cyan is much narrower than
        #   the size asked for in the profile, the overview is still there.
        lx0, _ = from_photo_to_desktop(geo, pw, ph, f["cyan"][0], 0)
        lx1, _ = from_photo_to_desktop(geo, pw, ph, f["right"] + 1, 0)
        if lx1 - lx0 < 0.7 * largo_f:
            return dict(row, outcome=BLIND, reason_text="the window is %d px wide and I asked for "
                        "%d: it is a preview (the overview?), not the window"
                        % (lx1 - lx0, largo_f)), None
        Xd, Yc = from_photo_to_desktop(geo, pw, ph, f["right"] + 0.5, f["center"][1] + 0.5)
        Xd = int(Xd)                               # the last cyan pixel, in the desktop
        Xc, Yc = from_photo_to_desktop(geo, pw, ph, f["center"][0] + 0.5, f["center"][1] + 0.5)
        Xt, Yt = from_photo_to_desktop(geo, pw, ph, f["body_text"][0] + 0.5, f["body_text"][1] + 0.5)
        if Xd + SCAN[-1] + 2 >= geo["tl"]:
            return dict(row, outcome=BLIND, reason_text="the right edge of the window (x=%d) is "
                        "on the edge of the screen: there is no room outside" % Xd), None
        mira = {"departure": (Xt, Yt), "center": (Xc, Yc),
                "edge": (Xd + 0.5, Yc), "body_text": (Xt, Yt)}
        row["win"] = {"ciano_foto": f["cyan"], "bordo_destro_desktop": Xd,
                            "bordi_foto": f["borders"], "picture": f["picture"],
                            "mira_desktop": {k: [round(a, 1), round(b, 1)]
                                             for k, (a, b) in mira.items()}}
        print("   ⭐ window: cyan %s in the photo %dx%d · right edge x=%d in the desktop · "
              "scan from x=%d to x=%d" % (f["cyan"], pw, ph, Xd, Xd + SCAN[0],
                                            Xd + SCAN[-1]), flush=True)

        # ── the steps ──────────────────────────────────────────────────────
        g.js(REAL._inject(JS_OBSERVE))
        if not g.js("return !!window.__C21__;"):
            return dict(row, outcome=BLIND, reason_text="the observer did not install itself"), None
        observed = {}
        for step in ("departure",) + STEPS:
            X, Y = mira[step]
            scan = None
            if step == "edge":
                X, scan, t0, d = scan_edge(g, geo, X, Y)
            else:
                vx, vy = desktop_to_glass(geo, X, Y)
                t0, d = one_step(g, vx, vy)
            if not d:
                return dict(row, outcome=BLIND, reason_text="%s: the observer does not answer" % step), \
                    None
            if not d["moves"]:
                # ⛔ The movement did not reach the PAGE: it is the bench.
                return dict(row, outcome=BLIND, reason_text="%s: the browser did not deliver the "
                            "movement to the page (no pointermove)" % step), None
            sp = d.get("spedito") or [-1, -1]
            if abs(sp[0] - int(X)) > 2 or abs(sp[1] - int(Y)) > 2:
                return dict(row, outcome=BLIND, reason_text="%s: the page sent (%s,%s) "
                            "instead of (%d,%d): the pointer is not where I say"
                            % (step, sp[0], sp[1], X, Y)), None
            t_move = d["moves"][0][0]
            pk, pd = ranking(read_guise(d["before"]))
            changes = []
            for tv, style in d["dress"]:
                k, kd = ranking(read_guise(style))
                changes.append((tv, k, kd))
            observed[step] = {"before": pk, "changes": changes, "t_move": t_move}
            if scan is not None:
                # ⭐ every movement of the scan with ITS instant in the page
                mm = [m[0] for m in d["moves"]]
                sc_t = []
                for k, tk in scan:
                    after_k = [t for t in mm if t >= tk]
                    if after_k:
                        sc_t.append((k, after_k[0]))
                if len(sc_t) < len(scan):
                    return dict(row, outcome=BLIND, reason_text="edge: %d movements of the "
                                "scan out of %d reached the page"
                                % (len(sc_t), len(scan))), None
                observed[step]["scan"] = sc_t
                t_move = sc_t[0][1]
                observed[step]["t_move"] = t_move

                def dove(tc):
                    ks = [k for k, tk in sc_t if tk <= tc]
                    return ("%+dpx" % ks[-1]) if ks else "?"
                print("   %-8s → scan x=%+d..%+d px from the edge, y=%.1f: before «%s» · "
                      "changes %s" % (step, SCAN[0], SCAN[-1], Y, pk,
                                    " ".join("%s «%s»" % (dove(c[0]), c[1]) for c in changes)
                                    or "none"), flush=True)
            else:
                print("   %-8s → (%.1f,%.1f): before «%s» · changes %s" % (
                    step, X, Y, pk,
                    " ".join("+%.0fms «%s»" % (c[0] - t_move, c[1]) for c in changes)
                    or "none"), flush=True)
            for c in changes:
                print("            %s: %s" % (c[1], c[2]), flush=True)
            if o.store:
                for i, (tv, style) in enumerate(d["dress"]):
                    v = read_guise(style)
                    if v[0] == "png":
                        with open(os.path.join(o.store, "%s-%s-%d.png" % (label_name, step, i)),
                                  "wb") as fh:
                            fh.write(v[1])
        row["observed"] = {p: {"before": v["before"],
                                 "changes": [[round(c[0] - v["t_move"]), c[1], c[2]]
                                           for c in v["changes"]]}
                             for p, v in observed.items()}
        return row, observed
    finally:
        try:
            g.shut()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ closing the browser: %s" % ex)


def judge_browser(row, observed, fault):
    """The verdict of one browser.  ⛔ With the fault it reads the other way round."""
    if observed is None:
        return row
    es, rs = judge_all(observed, EXPECTED)
    for p, e, m, _ms in rs:
        print("   %s %s" % ({GREEN: "⭐ 0", RED: "⛔ 1", BLIND: "⚠ 3"}[e], m))
    row["healthy"] = {"outcome": es, "steps": [[p, e, m] for p, e, m, _ in rs]}
    if not fault:
        reason_text = "; ".join(m for _p, e, m, _ in rs if e == es) if es != GREEN else \
            "the shape changes on all three steps within %.0f ms" % CAP_MS
        return dict(row, outcome=es, reason_text=reason_text)
    eg, rg = judge_all(observed, EXPECTED_WRONG)
    row["fault"] = {"outcome": eg, "steps": [[p, e, m] for p, e, m, _ in rg]}
    print("   ── the table shifted by one (--wrong-shape) ──")
    for p, e, m, _ms in rg:
        print("   %s %s" % ({GREEN: "⭐ 0", RED: "⛔ 1", BLIND: "⚠ 3"}[e], m))
    if es != GREEN:
        return dict(row, outcome=BLIND, reason_text="the healthy control is not green (%s): the "
                    "fault cannot be injected" % OUTCOME_NAME[es])
    if eg == RED:
        return dict(row, outcome=GREEN, reason_text="⭐ FAULT SEEN: with the shifted table the "
                    "same images give RED (%s)"
                    % "; ".join(m for _p, e, m, _ in rg if e == RED))
    return dict(row, outcome=RED, reason_text="⛔ FAULT NOT SEEN: the shifted table gives %s"
                % OUTCOME_NAME[eg])


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--container_box", choices=sorted(PORTS))
    a.add_argument("--port", type=int)
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--is_visible", action="store_true",
                   help="real windows (in the nested compositor) instead of headless")
    a.add_argument("--store", default="", help="folder for the photographs and the cursors")
    a.add_argument("--wrong-shape", action="store_true",
                   help="INJECTED FAULT: the table of expectations shifted by one")
    a.add_argument("--certify", action="store_true")
    a.add_argument("--wait-window", type=int, default=60)
    a.add_argument("--cap-s", type=int, default=45)
    a.add_argument("--base-ports", type=int, default=2961)
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
    # ⚠ the fields the drivers and `Test` of 12-client-veri expect
    o.url = "https://%s:%d/" % (o.host, port)
    o.password = "c21-" + secrets.token_hex(6)
    o.scene, o.continuity_s, o.log_cmd = "viva", 8, ""
    o.leave_on = False
    if o.store:
        os.makedirs(o.store, exist_ok=True)
    sc = C20V.Box(o.container_box)
    chi = "c21u%03d" % random.randint(0, 999)
    assert TENANT_PATTERN.match(chi)
    o.username = chi
    print("⭐ 11-c21 · %s · %s · tenant %s · browser %s · %s%s"
          % (sc.container, o.url, chi, o.browser,
             "real windows" if o.is_visible else "HEADLESS",
             " · ⛔ INJECTED FAULT --wrong-shape" if o.wrong_shape else ""))
    line_list = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.clear_out(chi)
        c, t = sc.create(chi, o.password)
        if c != 0:
            print("⛔ I could not create %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r, oss = observe(b, o, sc, chi)
            r = judge_browser(r, oss, o.wrong_shape)
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
    if o.wrong_shape:
        print({GREEN: "⭐ THE INJECTED FAULT WAS SEEN (outcome 0: the other way round, "
                      "like every fault of the net)",
               RED: "⛔⛔ THE INJECTED FAULT WAS NOT SEEN",
               BLIND: "⚠ with the injected fault I could NOT look ⇒ 3"}[outcome])
    else:
        print("%s C21(%s): %s" % ({GREEN: "⭐", RED: "⛔⛔", BLIND: "⚠"}[outcome],
                                  o.container_box, OUTCOME_NAME[outcome]))
    return outcome


if __name__ == "__main__":
    sys.exit(main())
