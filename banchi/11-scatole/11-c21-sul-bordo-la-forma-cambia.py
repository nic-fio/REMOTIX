#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c21 — ⭐⭐ «ON THE EDGE THE SHAPE CHANGES»
===========================================================================

    python3 11-c21-sul-bordo-la-forma-cambia.py --scatola gnome [--browser firefox,chrome]
    python3 11-c21-sul-bordo-la-forma-cambia.py --porta 8513 --host 192.168.0.2
    python3 11-c21-sul-bordo-la-forma-cambia.py --scatola gnome --forma-sbagliata
    python3 11-c21-sul-bordo-la-forma-cambia.py --certifica

    what must be true         : the REAL SHAPE of the pointer reaches the browser —
                                on GNOME, KDE, XFCE and LXQt (the user's
                                decision, 24 Sep 2026)
    where it starts from      : ⛔ from scratch, a NEW tenant (`c21u<n>`)
    what it looks at          : ⛔ **THE IMAGE** of the cursor the page makes
                                the browser wear — not a counter
    how I know it can give red: `--forma-sbagliata` (the table of expectations
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
        (`PAGINA`: cyan background, a yellow text box) and a Firefox
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
        to the canvas (`#schermo`, `cl_applica_modo()` in `src/pagina.html`
        ~9212-9222, which takes it from `REMOTIX_PUNTATORE.forma()` ~9145-9186):
        a PNG image and its hotspot.  An observer
        (`MutationObserver`) writes the INSTANT of every change, and a listener
        the instant of the movement: the latency is measured INSIDE the page.

⛔⛔ THE YARDSTICK — THE IMAGE, NOT A COUNTER.
   The project's `LEZIONI`: *«counters do not see the image»* — a
   received `CURSORE_FORMA` counts as a right one even if it carries the arrow.
   ⇒ Every image is CLASSIFIED from its pixels (`classifica()`): the
   silhouette is taken (alpha >= 128), its rectangle, and where the hotspot falls:
     freccia      hotspot in the top left corner of the silhouette
     orizzontale  the horizontal resize arrow: hotspot at
                  half height, silhouette symmetric above/below, thin, with
                  the HORIZONTAL shaft passing through the hotspot
     testo        hotspot at the centre, silhouette taller than wide
   ⛔⭐ `[M]` 24 Sep 2026, gnome: Adwaita's «e-resize» is NOT the double
       arrow with the hotspot at the centre one expected — it is ONE arrow
       pointing right against a bar, 18x17, with the hotspot on the
       bar (0,92 of the width, 0,56 of the height).  ⇒ The class does not
       demand the horizontal centre: it demands half HEIGHT and the horizontal
       shaft.  Breeze's double (`size_hor`) fits inside it all the same.
     nascosta  `cursor: none` (§5.5, width and height zero)
     altra     everything else (a hand, an hourglass, ...)
   And a step is GREEN only if the shape IN FORCE `TETTO_MS` (300 ms) after the
   movement is of the expected class, and it ARRIVED after the movement.

⛔⭐ WHY THE EDGE IS A SCAN AND NOT A POINT — the resize
   zone is NOT in the same place on the four desktops:
     `[M]` KWin (KDE)  `size_hor` only ON the edge (from 1 px inside to 1 px
                       outside); at 3 px outside there is already the normal arrow
     `[M]` labwc       from the edge pixel up to 7 px outside
     `[M]` GNOME       in the window's shadow (Firefox draws its own
                       borders): `[M]` from this mesh: from +1 px
   ⇒ A fixed «3 px outside» would give red to KWin for something KWin does
     on purpose.  We walk from `SCANSIONE[0]` to `SCANSIONE[-1]` px from the edge
     (the last pixel of the page), one pixel per step, `PASSO_SCANSIONE_S`
     per step: GREEN if at one point the shape becomes «horizontal» within
     300 ms of the movement that brought it, and the report says WHERE.

⛔ HOW I KNOW IT CAN GIVE RED — `--forma-sbagliata`.
   The table of expectations is shifted by one (centre⇒horizontal, edge⇒text,
   text⇒arrow) and THE SAME IMAGES are judged twice:
     · with the right table       ⇒ it must be GREEN (the healthy control)
     · with the shifted table     ⇒ it must be RED
   ⭐ The red can come only from the classes, that is from the PIXELS: the number of
     changes and the times are the same in the two judgements.
   ⛔ It reads THE OTHER WAY ROUND, like every fault of the net (`11-gancio.sh`,
     `esegui_maglia`): 0 = the fault was SEEN, 1 = NOT seen, 3 = the
     healthy control was not green ⇒ nothing could be injected.

⚠ OUTCOMES: 0 green · 1 red · 3 «I could not look», with the reason.
   The 3 is the BENCH's (the window does not show, the movement did not start,
   the page is not in `sistema` mode); the red is the PRODUCT's (the shape
   does not arrive, arrives late, or is wrong).

⚠ WHERE IT RUNS: on the machine that has the browsers (the server, `REMOTIX_SUL_SERVER=1`
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

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ Imported, not copied: the browser drivers and the road into the box.
#   `12-c20-veri` brings `12-client-veri` (VERI) along — only one in memory.
C20V = _carica("c20_veri", os.path.join(BANCHI, "12-c20-veri.py"))
VERI = C20V.VERI
VERDE, ROSSO, CIECO = VERI.VERDE, VERI.ROSSO, VERI.CIECO
PORTE = C20V.PORTE
NOME_ESITO = {VERDE: "VERDE", ROSSO: "ROSSO", CIECO: "I COULD NOT LOOK"}

# ⭐ The tenant: a name of the net, which C19 recognises and the hook clears out.
MODELLO_INQUILINO = re.compile(r"^c21u[0-9]+$")

# ---------------------------------------------------------------------------
# ⛔ THE NUMBERS — each with its reason.
# ---------------------------------------------------------------------------
# The user's request: the shape changes within 300 ms of the movement.
TETTO_MS = 300.0
# How long we look AFTER the ceiling: not to give green, but to say WHEN
# a late shape arrived (a red «at 450 ms» is cured, «never» is another
# defect).
GUARDA_S = 2.0
# ⭐ The scan of the right edge, in DESKTOP pixels relative to the last
#   pixel of the page: from 4 inside to 8 outside (the three measured zones are between
#   -1 and +7).  ⚠ The step lasts longer than the ceiling, so every change is attributed
#   to ONE movement only: the one right before.
SCANSIONE = tuple(range(-4, 9))
PASSO_SCANSIONE_S = 0.4
# The page colours, and the tolerance: the chain goes through H.264 4:2:0, which
# subsamples the chroma (§4.3 of phase 11, the same reason as C2).
CIANO = (0x00, 0xFF, 0xFF)
GIALLO = (0xFF, 0xFF, 0x00)
TOLLERANZA = 60
# The window must be at least this share of the canvas, or it is a leftover.
AREA_MINIMA = 0.02
# The alpha threshold of the silhouette: the theme's soft edges are not silhouette.
ALFA = 128

# ⭐ THE TABLE OF EXPECTATIONS, and the same one shifted by one (the fault).
PASSI = ("centro", "bordo", "testo")
ATTESO = {"centro": "freccia", "bordo": "orizzontale", "testo": "testo"}
ATTESO_SBAGLIATO = {"centro": "orizzontale", "bordo": "testo", "testo": "freccia"}

# ⭐ THE KNOWN PAGE.  Cyan background with `cursor: default`, and a yellow box
#   with `cursor: text` at the top left — far from the centre, so the centre
#   of the window is pure cyan.  ⚠ The `cursor` rules are declared and not
#   left to the engine: without them, the text cursor would appear only over the
#   glyphs and between one letter and the next it would go back to the arrow.
#   ⛔ No external resource: the box has no network to the outside.
PAGINA = """<!doctype html>
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
PROFILO = ".c21-profilo"
FILE_PAGINA = "c21-finestra.html"
PREFERENZE = """user_pref("browser.shell.checkDefaultBrowser", false);
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
#  THE PURE FUNCTIONS — and they are the ones `--certifica` tests
# ═══════════════════════════════════════════════════════════════════════════
_VESTE = re.compile(r'url\(\s*["\']?(data:image/png;base64,[^"\')]+)["\']?\s*\)'
                    r'\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)')


def leggi_veste(stile):
    """From the `cursor` rule of `#schermo` to (png, hx, hy) — or a word.

    Returns ("png", bytes, hx, hy) · ("nascosta",) · ("sistema",) if there is
    no garment (the browser's cursor is its own) · ("illeggibile", s)."""
    s = (stile or "").strip()
    if not s or s in ("auto", "default"):
        return ("sistema",)
    if s == "none":
        return ("nascosta",)
    m = _VESTE.search(s)
    if not m:
        return ("illeggibile", s[:80])
    try:
        png = base64.b64decode(m.group(1).split(",", 1)[1])
    except Exception:                            # noqa: BLE001
        return ("illeggibile", s[:80])
    return ("png", png, float(m.group(2)), float(m.group(3)))


def classifica_sagoma(larghezza, altezza, alfa, hx, hy):
    """⭐ The class of a cursor from its PIXELS: `alfa` is the list row by
    row of the alpha values.  Returns (class, description)."""
    xs = [i % larghezza for i, a in enumerate(alfa) if a >= ALFA]
    ys = [i // larghezza for i, a in enumerate(alfa) if a >= ALFA]
    if not xs:
        return "nascosta", "%dx%d without opaque pixels" % (larghezza, altezza)
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    rx, ry = (hx - x0 + 0.5) / w, (hy - y0 + 0.5) / h
    pieni = set(zip(xs, ys))
    # the above-below symmetry of the silhouette inside its rectangle
    simm = sum(1 for (x, y) in pieni if (x, y0 + y1 - y) in pieni) / len(pieni)
    # how much of the rectangle is full: an arrow is thin, an hourglass is not
    pieno = len(pieni) / float(w * h)
    # the shaft: the longest opaque run on the hotspot's row (± 1)
    asta = 0
    for y in (int(hy) - 1, int(hy), int(hy) + 1):
        corsa = 0
        for x in range(x0, x1 + 1):
            corsa = corsa + 1 if (x, y) in pieni else 0
            asta = max(asta, corsa)
    desc = ("%dx%d, silhouette %dx%d at (%d,%d), hotspot (%g,%g) = %.2f,%.2f of the "
            "silhouette, above/below symmetry %.2f, full %.2f, shaft %d/%d"
            % (larghezza, altezza, w, h, x0, y0, hx, hy, rx, ry, simm, pieno, asta, w))
    if rx <= 0.2 and ry <= 0.2:
        return "freccia", desc
    if 0.25 <= rx <= 0.75 and 0.25 <= ry <= 0.75 and h >= 1.5 * w:
        return "testo", desc
    if 0.3 <= ry <= 0.7 and w >= 0.8 * h and simm >= 0.8 and pieno <= 0.68 \
            and asta >= 0.6 * w:
        return "orizzontale", desc
    return "altra", desc


def classifica(veste):
    """(class, description) of a garment read by `leggi_veste`."""
    if veste[0] == "nascosta":
        return "nascosta", "cursor: none"
    if veste[0] == "sistema":
        return "sistema", "no remote shape worn (the browser's cursor)"
    if veste[0] != "png":
        return "illeggibile", veste[1]
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(veste[1])).convert("RGBA")
    except Exception as e:                       # noqa: BLE001
        return "illeggibile", "unreadable PNG: %s" % e
    l, a = im.size
    alfa = [p[3] for p in im.getdata()]
    return classifica_sagoma(l, a, alfa, veste[2], veste[3])


def giudica_passo(nome, atteso, prima, cambi, t_mossa):
    """⭐ The judgement of a step.

    `prima`  the class in force at the instant of the movement
    `cambi`  [(t_ms, class, description)] the changes after the movement
    Returns (outcome, reason, ms of the right change | None)."""
    dopo = [c for c in cambi if c[0] >= t_mossa]
    if not dopo:
        if prima == atteso:
            # ⛔ It is not a green: the shape was already that one, the step proves
            #   nothing — and the start on the text exists so as not to end up here.
            return CIECO, ("%s: the shape was already «%s» before the movement and did not "
                           "change: the step proves nothing" % (nome, atteso)), None
        return ROSSO, ("%s: in %.0f ms the shape DID NOT CHANGE (stays «%s», expected «%s»)"
                       % (nome, GUARDA_S * 1000, prima, atteso)), None
    entro = [c for c in dopo if c[0] - t_mossa <= TETTO_MS]
    if not entro:
        c = dopo[0]
        return ROSSO, ("%s: the shape changed at %.0f ms, BEYOND the %.0f (arrived «%s», "
                       "expected «%s»)" % (nome, c[0] - t_mossa, TETTO_MS, c[1], atteso)), None
    vigore = entro[-1]
    if vigore[1] != atteso:
        return ROSSO, ("%s: at %.0f ms the shape is «%s», expected «%s» (%s)"
                       % (nome, TETTO_MS, vigore[1], atteso, vigore[2])), None
    giusto = next(c for c in entro if c[1] == atteso)
    ms = giusto[0] - t_mossa
    return VERDE, ("%s: «%s» at %.0f ms (%s)" % (nome, atteso, ms, giusto[2])), ms


def giudica_scansione(nome, atteso, prima, cambi, mosse):
    """⭐ The judgement of the EDGE: a scan, not a point.

    `mosse`  [(offset_px, t_ms)] the instant of every movement of the scan
    Returns (outcome, reason, (offset, ms) | None)."""
    if not mosse:
        return CIECO, "%s: the scan has no movements" % nome, None
    mosse = sorted(mosse, key=lambda m: m[1])
    dopo = [c for c in cambi if c[0] >= mosse[0][1]]
    tardi = None
    for c in dopo:
        if c[1] != atteso:
            continue
        # ⭐ the movement that brought it: the last one before the change
        chi = [m for m in mosse if m[1] <= c[0]][-1]
        ms = c[0] - chi[1]
        if ms <= TETTO_MS:
            return VERDE, ("%s: «%s» at %+d px from the edge, %.0f ms after the movement (%s)"
                           % (nome, atteso, chi[0], ms, c[2])), (chi[0], ms)
        tardi = tardi or (chi[0], ms)
    if tardi:
        return ROSSO, ("%s: «%s» arrived at %+d px but %.0f ms after the movement, BEYOND "
                       "the %.0f" % (nome, atteso, tardi[0], tardi[1], TETTO_MS)), None
    if not dopo and prima == atteso:
        return CIECO, ("%s: the shape was already «%s» before the scan and did not "
                       "change: the step proves nothing" % (nome, atteso)), None
    viste = []
    for c in dopo:
        if c[1] not in viste:
            viste.append(c[1])
    return ROSSO, ("%s: from %+d to %+d px from the edge the shape is NEVER «%s» (%s)"
                   % (nome, mosse[0][0], mosse[-1][0], atteso,
                      ("seen: " + ", ".join(viste)) if viste
                      else "stays «%s», no change" % prima)), None


def giudica_tutto(osservati, tabella):
    """[(step, outcome, reason, ms)] and the overall outcome, for a table."""
    righe = []
    for p in PASSI:
        o = osservati.get(p)
        if o is None:
            righe.append((p, CIECO, "%s: not observed" % p, None))
            continue
        if o.get("scansione"):
            e, m, ms = giudica_scansione(p, tabella[p], o["prima"], o["cambi"],
                                         o["scansione"])
        else:
            e, m, ms = giudica_passo(p, tabella[p], o["prima"], o["cambi"], o["t_mossa"])
        righe.append((p, e, m, ms))
    v = [r[1] for r in righe]
    return (ROSSO if ROSSO in v else (CIECO if CIECO in v else VERDE)), righe


def _vicino(p, c, toll=TOLLERANZA):
    return abs(p[0] - c[0]) <= toll and abs(p[1] - c[1]) <= toll and abs(p[2] - c[2]) <= toll


def trova_finestra(larghezza, altezza, pixel, passo=1):
    """⭐ The test window in the photograph: dict or (None, reason).

    `pixel` is the RGB list row by row.  The CYAN of the page is looked for:
      · its rectangle, from the columns and rows where the cyan is plentiful (the
        30 % of the maximum: a black text or an icon does not shift it)
      · ⭐ the FINE right edge: on five rows around the centre we walk
        from the centre to the right as long as the pixel is cyan, and take the
        median — the last cyan pixel, in photograph pixels
      · the YELLOW text box, inside.
    ⚠ `passo`: the rectangle's sums are done on one pixel every `passo` (in 4K
      they are 8 million pixels, and without numpy the whole round costs ~10 s per
      photograph); the fine edge is looked for pixel by pixel anyway."""
    col = [0] * larghezza
    rig = [0] * altezza
    gcol, grig = [0] * larghezza, [0] * altezza
    for y in range(0, altezza, passo):
        base = y * larghezza
        for x in range(0, larghezza, passo):
            p = pixel[base + x]
            if _vicino(p, CIANO):
                col[x] += 1
                rig[y] += 1
            elif _vicino(p, GIALLO):
                gcol[x] += 1
                grig[y] += 1
    if max(col) == 0:
        return None, "no cyan pixel: the test window does not show"
    xs = [x for x, n in enumerate(col) if n >= 0.3 * max(col)]
    ys = [y for y, n in enumerate(rig) if n >= 0.3 * max(rig)]
    x0, x1, y0, y1 = min(xs), max(xs) + passo - 1, min(ys), max(ys) + passo - 1
    if (x1 - x0 + 1) * (y1 - y0 + 1) < AREA_MINIMA * larghezza * altezza:
        return None, ("the cyan is there but it is small (%dx%d): it is not the window"
                      % (x1 - x0 + 1, y1 - y0 + 1))
    cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
    # ⚠ with `passo` the centre must be put back on a sampled row of the cyan
    cx, cy = cx - cx % passo, cy - cy % passo
    if not _vicino(pixel[cy * larghezza + cx], CIANO):
        return None, "the centre of the cyan (%d,%d) is not cyan: the window is covered" % (cx, cy)
    bordi = []
    for dy in (-20, -10, 0, 10, 20):
        y = min(max(cy + dy, 0), altezza - 1)
        x = cx
        while x + 1 < larghezza and _vicino(pixel[y * larghezza + x + 1], CIANO):
            x += 1
        bordi.append(x)
    bordi.sort()
    destro = bordi[2]
    if max(gcol) == 0:
        return None, "no yellow pixel: the text box does not show"
    gx = [x for x, n in enumerate(gcol) if n >= 0.3 * max(gcol)]
    gy = [y for y, n in enumerate(grig) if n >= 0.3 * max(grig)]
    return {"ciano": [x0, y0, x1, y1], "centro": [cx, cy], "destro": destro,
            "bordi": bordi,
            "testo": [(min(gx) + max(gx)) // 2, (min(gy) + max(gy)) // 2],
            "giallo": [min(gx), min(gy), max(gx), max(gy)]}, ""


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION OF THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def _png(im):
    b = io.BytesIO()
    im.save(b, "PNG")
    return b.getvalue()


def cursori_finti():
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
    return {"freccia": (("png", _png(fr), 3, 3), "freccia"),
            "doppia di Breeze": (("png", _png(dp), 15, 15), "orizzontale"),
            "e-resize di Adwaita": (("png", _png(ae), 19, 12), "orizzontale"),
            "text bar": (("png", _png(te), 15, 15), "testo"),
            "clessidra piena": (("png", _png(cl), 11, 11), "altra"),
            "mano": (("png", _png(ma), 9, 2), "altra")}


def certifica():
    print("⭐ 11-c21 · CERTIFICATION OF THE PURE FUNCTIONS")
    guai, fatte = [], []

    def prova(cosa, vero, dettaglio=""):
        fatte.append(cosa)
        print("   %s %s%s" % ("⭐ ok  " if vero else "⛔ NO  ", cosa,
                              (" — " + dettaglio) if dettaglio else ""))
        if not vero:
            guai.append(cosa)

    try:
        c = cursori_finti()
    except ImportError:
        print("⛔ PIL is not there: I cannot certify ⇒ 3")
        return 3
    # 1. the CSS rule is read, in the two spellings of the browsers
    dv = c["doppia di Breeze"][0]
    b64 = base64.b64encode(dv[1]).decode()
    for s in ('url("data:image/png;base64,%s") 15 15, default' % b64,
              "url(data:image/png;base64,%s) 15 15, default" % b64):
        v = leggi_veste(s)
        prova("leggi_veste: %s…" % s[:14], v[0] == "png" and v[2:] == (15.0, 15.0))
    prova("leggi_veste: «none» ⇒ hidden", leggi_veste("none") == ("nascosta",))
    prova("leggi_veste: empty ⇒ system", leggi_veste("") == ("sistema",))
    # 2. the classifier from the PIXELS
    for nome, (veste, attesa) in c.items():
        k, d = classifica(veste)
        prova("classifica %s ⇒ %s" % (nome, k), k == attesa, d)
    # ⛔ and the same image of the double with the hotspot at the top left
    #   is NOT a resize: the hotspot is part of the shape
    k, d = classifica(dv[:2] + (3, 8))
    prova("double with the hotspot at the top left ⇒ not horizontal (%s)" % k,
          k != "orizzontale", d)
    # 3. the judgement of the step
    fr, dp = classifica(c["freccia"][0]), classifica(dv)
    te = classifica(c["text bar"][0])
    casi = [
        ("right at 120 ms ⇒ GREEN", ("freccia", [(1120, dp[0], dp[1])], 1000), VERDE),
        ("right at 350 ms ⇒ RED", ("freccia", [(1350, dp[0], dp[1])], 1000), ROSSO),
        ("no change ⇒ RED", ("freccia", [], 1000), ROSSO),
        ("wrong at 100 ms ⇒ RED", ("freccia", [(1100, fr[0], fr[1])], 1000), ROSSO),
        ("already right and still ⇒ 3", ("orizzontale", [], 1000), CIECO),
        ("change from BEFORE the movement ⇒ RED", ("freccia", [(900, dp[0], dp[1])], 1000),
         ROSSO),
        ("right at 100 then wrong at 250 ⇒ RED",
         ("freccia", [(1100, dp[0], dp[1]), (1250, fr[0], fr[1])], 1000), ROSSO),
    ]
    for nome, (prima, cambi, t), atteso in casi:
        e, m, _ms = giudica_passo("bordo", "orizzontale", prima, cambi, t)
        prova("giudica_passo: %s" % nome, e == atteso, m)
    # 3-bis. the scan of the edge (three desktops, three places)
    mosse = [(k, 10000 + 400 * i) for i, k in enumerate(SCANSIONE)]
    t_di = dict(mosse)
    scasi = [
        ("KWin: on the edge (-1 px) ⇒ GREEN at -1",
         ("freccia", [(t_di[-1] + 40, dp[0], dp[1]), (t_di[2] + 40, fr[0], fr[1])]),
         VERDE, -1),
        ("GNOME: in the shadow (+4 px) ⇒ GREEN at +4",
         ("freccia", [(t_di[4] + 30, dp[0], dp[1])]), VERDE, 4),
        ("never horizontal ⇒ RED", ("freccia", [(t_di[3] + 30, te[0], te[1])]), ROSSO, None),
        ("no change ⇒ RED", ("freccia", []), ROSSO, None),
        ("horizontal at 350 ms from its movement ⇒ RED",
         ("freccia", [(t_di[5] + 350, dp[0], dp[1])]), ROSSO, None),
    ]
    for nome, (prima, cambi), atteso, dove in scasi:
        e, m, x = giudica_scansione("bordo", "orizzontale", prima, cambi, mosse)
        prova("giudica_scansione: %s" % nome,
              e == atteso and (dove is None or (x and x[0] == dove)), m)
    e, m, _x = giudica_scansione("bordo", "testo", "freccia",
                                 [(t_di[4] + 30, dp[0], dp[1])], mosse)
    prova("giudica_scansione with the shifted table ⇒ RED", e == ROSSO, m)

    # 4. ⭐ the injected fault: the SAME observations, two tables
    oss = {"centro": {"prima": "testo", "cambi": [(1080, fr[0], fr[1])], "t_mossa": 1000},
           "bordo": {"prima": "freccia", "cambi": [(2090, dp[0], dp[1])], "t_mossa": 2000,
                     "scansione": [(-1, 2000), (0, 2400)]},
           "testo": {"prima": "orizzontale", "cambi": [(3070, te[0], te[1])],
                     "t_mossa": 3000}}
    es, _ = giudica_tutto(oss, ATTESO)
    eg, righe = giudica_tutto(oss, ATTESO_SBAGLIATO)
    prova("right table ⇒ GREEN, shifted table ⇒ RED", es == VERDE and eg == ROSSO,
          "healthy %s · fault %s (%s)" % (es, eg, righe[0][2]))
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
    f, perche = trova_finestra(L, A, px)
    prova("trova_finestra: right edge = 299", bool(f) and f["destro"] == 299,
          perche or json.dumps(f))
    f3, perche3 = trova_finestra(L, A, px, passo=3)
    prova("trova_finestra with step 3: right edge = 299 all the same",
          bool(f3) and f3["destro"] == 299, perche3 or json.dumps(f3))
    prova("trova_finestra: the text falls in the yellow",
          bool(f) and 62 <= f["testo"][0] < 150 and 52 <= f["testo"][1] < 100)
    f2, perche2 = trova_finestra(L, A, [(90, 90, 90)] * (L * A))
    prova("trova_finestra: without cyan ⇒ no window", f2 is None, perche2)
    print()
    if guai:
        print("⛔ CERTIFICATION FAILED: %d tests out of %d" % (len(guai), len(fatte)))
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
JS_OSSERVA = r"""
(function () {
  if (window.__C21__) return;
  const s = document.getElementById('schermo');
  if (!s) return;
  const C = window.__C21__ = { mosse: [], vesti: [] };
  addEventListener('pointermove', function (e) {
    C.mosse.push([performance.now(), e.clientX, e.clientY]);
    if (C.mosse.length > 200) C.mosse.shift();
  }, true);
  const leggi = function () {
    const v = s.style.cursor || '';
    const u = C.vesti.length ? C.vesti[C.vesti.length - 1][1] : null;
    if (v === u) return;
    C.vesti.push([performance.now(), v]);
    if (C.vesti.length > 60) C.vesti.shift();
  };
  leggi();
  new MutationObserver(leggi).observe(s, { attributes: true, attributeFilter: ['style'] });
})();
"""

JS_ORA = "return performance.now();"

JS_DOPO = r"""
const C = window.__C21__;
if (!C) return null;
const t = arguments[0];
let prima = '';
for (const v of C.vesti) if (v[0] <= t) prima = v[1];
const st = window.REMOTIX && REMOTIX.input_classico ? REMOTIX.input_classico.stato() : null;
return { mosse: C.mosse.filter(m => m[0] > t),
         vesti: C.vesti.filter(v => v[0] > t),
         prima: prima,
         spedito: st ? st.ultimo_spedito : null,
         utilizzabile: st ? st.utilizzabile : null };
"""

JS_GEOMETRIA = r"""
const P = window.REMOTIX_PUNTATORE, t = document.getElementById('schermo');
if (!P || !P.geometria || !t) return null;
const g = P.geometria();
return { left: g.r.left, top: g.r.top, width: g.r.width, height: g.r.height,
         bx0: g.bx0, by0: g.by0, sx: g.sx, sy: g.sy, vx: g.vx, vy: g.vy,
         tl: g.tl, ta: g.ta, bw: t.width, bh: t.height,
         modo: document.body.dataset.puntatore || null,
         disposizione: document.body.dataset.disposizione || null };
"""


def foto_piena(g):
    """The photograph of the canvas at FULL resolution.  ⚠ The Chrome driver of
    `12-client-veri` reduces it to 640 px of width (for the degenerate judge):
    here the single pixels of the edge are needed, and scale 1 is asked for."""
    if hasattr(g, "cdp"):
        r = g.js("const t=document.getElementById('schermo');"
                 "if(!t) return null; const b=t.getBoundingClientRect();"
                 "return [b.left, b.top, b.width, b.height];")
        if not r:
            return None
        if getattr(g, "scala_foto", 1) != 1:
            # ⚠ the phone (phase 19 §5): Chrome Android with `clip.scale` > 1 does not
            #   enlarge, it REPEATS the page as tiles (2 Oct 2026: the scene three times
            #   across).  ⇒ the photo of the whole glass, already in device pixels,
            #   and the crop of the canvas here.
            import io
            from PIL import Image
            s = g.cdp.chiama("Page.captureScreenshot", format="png")
            im = Image.open(io.BytesIO(base64.b64decode(s["data"])))
            k = im.size[0] / float(g.js("return window.innerWidth;") or im.size[0])
            im = im.crop((round(r[0] * k), round(r[1] * k),
                          round((r[0] + r[2]) * k), round((r[1] + r[3]) * k)))
            b = io.BytesIO()
            im.save(b, "PNG")
            return b.getvalue()
        s = g.cdp.chiama("Page.captureScreenshot", format="png",
                         clip={"x": r[0], "y": r[1], "width": r[2], "height": r[3],
                               "scale": 1})
        return base64.b64decode(s["data"])
    png, _p = g.fotografa_tela()
    return png


def dalla_foto_al_desktop(geo, pw, ph, px, py):
    """Photograph pixels ⇒ desktop pixels (floating point)."""
    return ((px * geo["bw"] / pw - geo["bx0"]) / geo["sx"],
            (py * geo["bh"] / ph - geo["by0"]) / geo["sy"])


def dal_desktop_al_vetro(geo, X, Y):
    """Desktop pixels ⇒ browser coordinates (the same as `cl_disegna`)."""
    return (geo["left"] + (geo["bx0"] + X * geo["sx"]) * geo["vx"],
            geo["top"] + (geo["by0"] + Y * geo["sy"]) * geo["vy"])


def cerca_la_finestra(g, attesa, salva, nome):
    """Waits for the test window to appear STILL (two equal photographs)."""
    from PIL import Image
    fine = time.time() + attesa
    ultima, perche, png = None, "no photograph", None
    while time.time() < fine:
        time.sleep(1.5)
        try:
            png = foto_piena(g)
        except Exception as e:                   # noqa: BLE001
            perche = "photograph failed: %s" % str(e)[:120]
            continue
        if not png:
            perche = "the canvas cannot be photographed"
            continue
        im = Image.open(io.BytesIO(png)).convert("RGB")
        f, perche = trova_finestra(im.size[0], im.size[1], list(im.getdata()),
                                   passo=max(1, im.size[0] // 960))
        if not f:
            ultima = None
            continue
        f["foto"] = list(im.size)
        if ultima and all(abs(a - b) <= 2 for a, b in zip(ultima["ciano"], f["ciano"])) \
                and abs(ultima["destro"] - f["destro"]) <= 1:
            if salva:
                with open(os.path.join(salva, "%s-finestra.png" % nome), "wb") as fh:
                    fh.write(png)
            return f, ""
        ultima = f
    if salva and png:
        with open(os.path.join(salva, "%s-finestra-NON-trovata.png" % nome), "wb") as fh:
            fh.write(png)
    return None, perche


# ⭐ The ESC in the key table of `12-client-veri` (which has only Control and
#   the arrow): an entry is ADDED, the driver is not copied.
VERI.TASTI.setdefault("Escape", {"key": "Escape", "code": "Escape", "vk": 27,
                                 "wd": "\ue00c"})


def sveglia(g, geo):
    """A real ESC, with the pointer on the canvas and the focus outside the form."""
    try:
        g.js("if (document.activeElement && document.activeElement.blur) "
             "document.activeElement.blur(); return 1;")
        x, y = dal_desktop_al_vetro(geo, geo["tl"] * 0.5, geo["ta"] * 0.5)
        g.muovi(x, y)
        time.sleep(0.3)
        g.tasto("Escape")
        time.sleep(1.5)
        return "ESC sent"
    except Exception as e:                       # noqa: BLE001
        return "⚠ ESC not sent: %s" % str(e)[:120]


def scansiona(g, geo, Xbordo, Y):
    """⭐ The edge, one pixel per step.  Returns (final X, [(offset, t0)], t0, data)."""
    t_inizio = g.js(JS_ORA)
    passi = []
    for k in SCANSIONE:
        vx, vy = dal_desktop_al_vetro(geo, Xbordo + k, Y)
        passi.append((k, g.js(JS_ORA)))
        g.muovi(vx, vy)
        time.sleep(PASSO_SCANSIONE_S)
    time.sleep(max(0.0, GUARDA_S - PASSO_SCANSIONE_S))
    return Xbordo + SCANSIONE[-1], passi, t_inizio, g.js(JS_DOPO, t_inizio)


def un_passo(g, x, y):
    """Moves the pointer and gathers what the page saw."""
    t0 = g.js(JS_ORA)
    g.muovi(x, y)
    time.sleep(GUARDA_S)
    return t0, g.js(JS_DOPO, t0)


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE BOX
# ═══════════════════════════════════════════════════════════════════════════
def prepara_la_casa(sc, chi, largo, alto):
    """The known page and the Firefox profile, in the tenant's home."""
    b = lambda s: base64.b64encode(s.encode()).decode()     # noqa: E731
    c, t = sc.dentro(
        "set -e; h=/home/%s; mkdir -p $h/%s; "
        "echo %s | base64 -d > $h/%s; echo %s | base64 -d > $h/%s/user.js; "
        "echo %s | base64 -d > $h/%s/xulstore.json; chown -R %s: $h/%s $h/%s; echo ready"
        % (chi, PROFILO, b(PAGINA), FILE_PAGINA, b(PREFERENZE), PROFILO,
           b(xulstore(largo, alto)), PROFILO, chi, PROFILO, FILE_PAGINA), 60)
    return c == 0, t


def accendi_la_finestra(sc, chi):
    """⭐ NORMAL `firefox-esr` in the tenant's session: it has the borders."""
    c, t = sc.dentro(
        "u=$(id -u %(c)s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
        "| head -1); [ -n \"$d\" ] || { echo 'no wayland socket'; exit 2; }; "
        "setsid runuser -u %(c)s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=/home/%(c)s firefox-esr --no-remote --new-instance "
        "--profile /home/%(c)s/%(p)s file:///home/%(c)s/%(f)s "
        "< /dev/null > /home/%(c)s/.c21-firefox.log 2>&1 & "
        "for i in $(seq 1 40); do pgrep -u %(c)s -f firefox-esr >/dev/null && "
        "{ echo started; exit 0; }; sleep 0.25; done; echo 'it was not seen'; exit 1"
        % {"c": chi, "p": PROFILO, "f": FILE_PAGINA}, 60)
    return c == 0, t


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST OF ONE BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def osserva(nome, o, sc, chi):
    """Returns (riga, osservati) — `osservati` is None if nothing was looked at."""
    print("\n══ %s ══════════════════════════════" % nome.upper(), flush=True)
    riga = {"browser": nome}
    g = VERI.accendi_guida(nome, o)
    try:
        print("   stage: %s" % g.palco(), flush=True)
        if o.largo:
            print("   %s" % C20V.dimensiona(g, nome, o.largo, o.alto), flush=True)
        pr = VERI.Prova(g, o, o.url, o.parola)
        ok, m = pr.apri()
        if not ok:
            return dict(riga, esito=CIECO, perche="the page does not open: " + m), None
        e, m, s = pr.entra(o.parola)
        if e != VERDE:
            return dict(riga, esito=CIECO, perche="the login: " + m), None
        e, m, s = pr.primo_fotogramma()
        e, m = C20V.desktop_scuro_ma_vivo(e, m, s)
        print("   ⭐ first frame: %s" % m, flush=True)
        if e != VERDE:
            return dict(riga, esito=CIECO, perche="without an image there is no looking: " + m), None
        geo = g.js(JS_GEOMETRIA)
        if not geo:
            return dict(riga, esito=CIECO, perche="`REMOTIX_PUNTATORE.geometria` is not there"), None
        riga["geometria"] = {k: geo[k] for k in ("tl", "ta", "bw", "bh", "sx", "vx",
                                                 "modo", "disposizione")}
        print("   canvas %sx%s · buffer %sx%s · mode «%s» · layout «%s»"
              % (geo["tl"], geo["ta"], geo["bw"], geo["bh"], geo["modo"],
                 geo["disposizione"]), flush=True)
        if geo["modo"] != "sistema" or geo["disposizione"] != "classico":
            # ⛔ Outside `sistema` mode the garment does not go on the canvas: looking at
            #   the `cursor` rule would say «it does not change» to a healthy product.
            return dict(riga, esito=CIECO, perche="the page is not in «sistema» "
                        "classic mode (mode %s, layout %s): the garment cannot be read"
                        % (geo["modo"], geo["disposizione"])), None

        # ── the wake-up: an ESC BEFORE opening the window ──────────────────
        # ⚠ `[M]` 24 Sep 2026, gnome: the session is born in the OVERVIEW,
        #   and there the window is a shrunk preview on which the desktop
        #   does not change shape (the first run of this mesh: false RED, three
        #   steps without a change).  ⭐ It is C4's wake-up (`11-c4…`, «THE
        #   WAKE-UP»), sent as the user sends it: a REAL key of the
        #   browser, with the focus outside the form's fields (`cl_nel_modulo`).
        #   ⛔ No click to give the focus: the first click on the canvas asks for the
        #     `Pointer Lock`, and from there the movements would be relative.
        e_sv = sveglia(g, geo)
        print("   wake-up: %s" % e_sv, flush=True)

        # ── the test window ────────────────────────────────────────────────
        largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
        ok, t = prepara_la_casa(sc, chi, largo_f, alto_f)
        if not ok:
            return dict(riga, esito=CIECO, perche="the home cannot be prepared: %s" % t[-200:]), None
        ok, t = accendi_la_finestra(sc, chi)
        if not ok:
            return dict(riga, esito=CIECO, perche="firefox-esr does not start: %s" % t[-200:]), None
        f, perche = cerca_la_finestra(g, o.attesa_finestra, o.salva, nome)
        if not f:
            return dict(riga, esito=CIECO, perche="the test window does not show within "
                        "%d s: %s" % (o.attesa_finestra, perche)), None
        pw, ph = f["foto"]
        # ⛔ A preview is not a window: if the cyan is much narrower than
        #   the size asked for in the profile, the overview is still there.
        lx0, _ = dalla_foto_al_desktop(geo, pw, ph, f["ciano"][0], 0)
        lx1, _ = dalla_foto_al_desktop(geo, pw, ph, f["destro"] + 1, 0)
        if lx1 - lx0 < 0.7 * largo_f:
            return dict(riga, esito=CIECO, perche="the window is %d px wide and I asked for "
                        "%d: it is a preview (the overview?), not the window"
                        % (lx1 - lx0, largo_f)), None
        Xd, Yc = dalla_foto_al_desktop(geo, pw, ph, f["destro"] + 0.5, f["centro"][1] + 0.5)
        Xd = int(Xd)                               # the last cyan pixel, in the desktop
        Xc, Yc = dalla_foto_al_desktop(geo, pw, ph, f["centro"][0] + 0.5, f["centro"][1] + 0.5)
        Xt, Yt = dalla_foto_al_desktop(geo, pw, ph, f["testo"][0] + 0.5, f["testo"][1] + 0.5)
        if Xd + SCANSIONE[-1] + 2 >= geo["tl"]:
            return dict(riga, esito=CIECO, perche="the right edge of the window (x=%d) is "
                        "on the edge of the screen: there is no room outside" % Xd), None
        mira = {"partenza": (Xt, Yt), "centro": (Xc, Yc),
                "bordo": (Xd + 0.5, Yc), "testo": (Xt, Yt)}
        riga["finestra"] = {"ciano_foto": f["ciano"], "bordo_destro_desktop": Xd,
                            "bordi_foto": f["bordi"], "foto": f["foto"],
                            "mira_desktop": {k: [round(a, 1), round(b, 1)]
                                             for k, (a, b) in mira.items()}}
        print("   ⭐ window: cyan %s in the photo %dx%d · right edge x=%d in the desktop · "
              "scan from x=%d to x=%d" % (f["ciano"], pw, ph, Xd, Xd + SCANSIONE[0],
                                            Xd + SCANSIONE[-1]), flush=True)

        # ── the steps ──────────────────────────────────────────────────────
        g.js(VERI._inietta(JS_OSSERVA))
        if not g.js("return !!window.__C21__;"):
            return dict(riga, esito=CIECO, perche="the observer did not install itself"), None
        osservati = {}
        for passo in ("partenza",) + PASSI:
            X, Y = mira[passo]
            scansione = None
            if passo == "bordo":
                X, scansione, t0, d = scansiona(g, geo, X, Y)
            else:
                vx, vy = dal_desktop_al_vetro(geo, X, Y)
                t0, d = un_passo(g, vx, vy)
            if not d:
                return dict(riga, esito=CIECO, perche="%s: the observer does not answer" % passo), \
                    None
            if not d["mosse"]:
                # ⛔ The movement did not reach the PAGE: it is the bench.
                return dict(riga, esito=CIECO, perche="%s: the browser did not deliver the "
                            "movement to the page (no pointermove)" % passo), None
            sp = d.get("spedito") or [-1, -1]
            if abs(sp[0] - int(X)) > 2 or abs(sp[1] - int(Y)) > 2:
                return dict(riga, esito=CIECO, perche="%s: the page sent (%s,%s) "
                            "instead of (%d,%d): the pointer is not where I say"
                            % (passo, sp[0], sp[1], X, Y)), None
            t_mossa = d["mosse"][0][0]
            pk, pd = classifica(leggi_veste(d["prima"]))
            cambi = []
            for tv, stile in d["vesti"]:
                k, kd = classifica(leggi_veste(stile))
                cambi.append((tv, k, kd))
            osservati[passo] = {"prima": pk, "cambi": cambi, "t_mossa": t_mossa}
            if scansione is not None:
                # ⭐ every movement of the scan with ITS instant in the page
                mm = [m[0] for m in d["mosse"]]
                sc_t = []
                for k, tk in scansione:
                    dopo_k = [t for t in mm if t >= tk]
                    if dopo_k:
                        sc_t.append((k, dopo_k[0]))
                if len(sc_t) < len(scansione):
                    return dict(riga, esito=CIECO, perche="edge: %d movements of the "
                                "scan out of %d reached the page"
                                % (len(sc_t), len(scansione))), None
                osservati[passo]["scansione"] = sc_t
                t_mossa = sc_t[0][1]
                osservati[passo]["t_mossa"] = t_mossa

                def dove(tc):
                    ks = [k for k, tk in sc_t if tk <= tc]
                    return ("%+dpx" % ks[-1]) if ks else "?"
                print("   %-8s → scan x=%+d..%+d px from the edge, y=%.1f: before «%s» · "
                      "changes %s" % (passo, SCANSIONE[0], SCANSIONE[-1], Y, pk,
                                    " ".join("%s «%s»" % (dove(c[0]), c[1]) for c in cambi)
                                    or "none"), flush=True)
            else:
                print("   %-8s → (%.1f,%.1f): before «%s» · changes %s" % (
                    passo, X, Y, pk,
                    " ".join("+%.0fms «%s»" % (c[0] - t_mossa, c[1]) for c in cambi)
                    or "none"), flush=True)
            for c in cambi:
                print("            %s: %s" % (c[1], c[2]), flush=True)
            if o.salva:
                for i, (tv, stile) in enumerate(d["vesti"]):
                    v = leggi_veste(stile)
                    if v[0] == "png":
                        with open(os.path.join(o.salva, "%s-%s-%d.png" % (nome, passo, i)),
                                  "wb") as fh:
                            fh.write(v[1])
        riga["osservati"] = {p: {"prima": v["prima"],
                                 "cambi": [[round(c[0] - v["t_mossa"]), c[1], c[2]]
                                           for c in v["cambi"]]}
                             for p, v in osservati.items()}
        return riga, osservati
    finally:
        try:
            g.chiudi()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ closing the browser: %s" % ex)


def giudica_browser(riga, osservati, guasto):
    """The verdict of one browser.  ⛔ With the fault it reads the other way round."""
    if osservati is None:
        return riga
    es, rs = giudica_tutto(osservati, ATTESO)
    for p, e, m, _ms in rs:
        print("   %s %s" % ({VERDE: "⭐ 0", ROSSO: "⛔ 1", CIECO: "⚠ 3"}[e], m))
    riga["sano"] = {"esito": es, "passi": [[p, e, m] for p, e, m, _ in rs]}
    if not guasto:
        perche = "; ".join(m for _p, e, m, _ in rs if e == es) if es != VERDE else \
            "the shape changes on all three steps within %.0f ms" % TETTO_MS
        return dict(riga, esito=es, perche=perche)
    eg, rg = giudica_tutto(osservati, ATTESO_SBAGLIATO)
    riga["guasto"] = {"esito": eg, "passi": [[p, e, m] for p, e, m, _ in rg]}
    print("   ── the table shifted by one (--forma-sbagliata) ──")
    for p, e, m, _ms in rg:
        print("   %s %s" % ({VERDE: "⭐ 0", ROSSO: "⛔ 1", CIECO: "⚠ 3"}[e], m))
    if es != VERDE:
        return dict(riga, esito=CIECO, perche="the healthy control is not green (%s): the "
                    "fault cannot be injected" % NOME_ESITO[es])
    if eg == ROSSO:
        return dict(riga, esito=VERDE, perche="⭐ FAULT SEEN: with the shifted table the "
                    "same images give RED (%s)"
                    % "; ".join(m for _p, e, m, _ in rg if e == ROSSO))
    return dict(riga, esito=ROSSO, perche="⛔ FAULT NOT SEEN: the shifted table gives %s"
                % NOME_ESITO[eg])


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", choices=sorted(PORTE))
    a.add_argument("--porta", type=int)
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--visibile", action="store_true",
                   help="real windows (in the nested compositor) instead of headless")
    a.add_argument("--salva", default="", help="folder for the photographs and the cursors")
    a.add_argument("--forma-sbagliata", action="store_true",
                   help="INJECTED FAULT: the table of expectations shifted by one")
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--attesa-finestra", type=int, default=60)
    a.add_argument("--tetto-s", type=int, default=45)
    a.add_argument("--porte-base", type=int, default=2961)
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    o = a.parse_args()
    if o.certifica:
        return certifica()
    if not o.scatola and o.porta:
        o.scatola = {p: s for s, p in PORTE.items()}.get(o.porta)
    if not o.scatola:
        print("⛔ --scatola is needed, or a --porta of the net (%s)" % PORTE)
        return 3
    porta = o.porta or PORTE[o.scatola]
    # ⚠ the fields the drivers and `Prova` of 12-client-veri expect
    o.url = "https://%s:%d/" % (o.host, porta)
    o.parola = "c21-" + secrets.token_hex(6)
    o.scena, o.continuita_s, o.registro_cmd = "viva", 8, ""
    o.lascia_acceso = False
    if o.salva:
        os.makedirs(o.salva, exist_ok=True)
    sc = C20V.Scatola(o.scatola)
    chi = "c21u%03d" % random.randint(0, 999)
    assert MODELLO_INQUILINO.match(chi)
    o.utente = chi
    print("⭐ 11-c21 · %s · %s · inquilino %s · browser %s · %s%s"
          % (sc.contenitore, o.url, chi, o.browser,
             "real windows" if o.visibile else "HEADLESS",
             " · ⛔ INJECTED FAULT --forma-sbagliata" if o.forma_sbagliata else ""))
    righe = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.sgombera(chi)
        c, t = sc.crea(chi, o.parola)
        if c != 0:
            print("⛔ I could not create %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r, oss = osserva(b, o, sc, chi)
            r = giudica_browser(r, oss, o.forma_sbagliata)
        except Exception as e:                   # noqa: BLE001
            r = {"browser": b, "esito": CIECO, "perche": "the bench fell over: %r" % e}
        finally:
            sc.sgombera(chi)
        print("   ▶ %s: %s — %s" % (b, NOME_ESITO.get(r["esito"], r["esito"]),
                                   r.get("perche")))
        print("RIGA " + json.dumps(r, ensure_ascii=False), flush=True)
        righe.append(r)
    v = [r["esito"] for r in righe]
    esito = ROSSO if ROSSO in v else (CIECO if CIECO in v else VERDE)
    print()
    if o.forma_sbagliata:
        print({VERDE: "⭐ THE INJECTED FAULT WAS SEEN (outcome 0: the other way round, "
                      "like every fault of the net)",
               ROSSO: "⛔⛔ THE INJECTED FAULT WAS NOT SEEN",
               CIECO: "⚠ with the injected fault I could NOT look ⇒ 3"}[esito])
    else:
        print("%s C21(%s): %s" % ({VERDE: "⭐", ROSSO: "⛔⛔", CIECO: "⚠"}[esito],
                                  o.scatola, NOME_ESITO[esito]))
    return esito


if __name__ == "__main__":
    sys.exit(main())
