#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c22 — ⭐⭐ «THE EDGE CAN BE DRAGGED»
===========================================================================

    python3 11-c22-il-bordo-si-trascina.py --scatola kde [--browser firefox,chrome]
    python3 11-c22-il-bordo-si-trascina.py --porta 8513 --host 192.168.0.2
    python3 11-c22-il-bordo-si-trascina.py --scatola kde --senza-pulsante
    python3 11-c22-il-bordo-si-trascina.py --certifica

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
    how I know it can give red: `--senza-pulsante` (the same drag with the
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
     4  for each grab point `x_b + k`, k in `PRESE` (from 2 px inside to 6
        outside), at half height:
          presses the left button (a REAL browser event: Marionette's `pointerDown`,
          CDP's `mousePressed`), drags right by `SPINTA`
          px in `PASSI` steps with the button pressed, releases
        ⇒ photographs, and measures again: the right edge, the left one, the top.
     5  GREEN at the first point where the right edge moved by at least
        `SOGLIA` px and the window is still THE SAME (left edge and top
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
     Firefox on gnome), from -2 to 0 nothing.  `--senza-pulsante`: fault SEEN
     everywhere (9 still points, then the healthy control green).

⛔ WHY «THE SAME WINDOW» — a drag that MOVES the window
   (grabbed by the title bar, or with the «Alt+drag» gesture) also brings the
   right edge to the right: by 150 px, more than the threshold.  ⇒ Green wants the
   LEFT edge still (±`FERMO` px): if both moved, it is a
   move, and it is said.

⛔ HOW I KNOW IT CAN GIVE RED — `--senza-pulsante`.
   The same gesture, the same points, the same steps, but the button is NOT
   pressed: no desktop resizes a window by merely passing over it.  ⇒ On
   all points the window must stay as it was, and the mesh must give RED.
   ⭐ And then the HEALTHY CONTROL, in the same session: the scan with the
   button must give green.  Without the control, a «red» with the button up
   could come from a broken product and not from the fault.
   ⛔ It reads THE OTHER WAY ROUND, like every fault of the net (`11-gancio.sh`,
     `esegui_maglia`): 0 = the fault was SEEN, 1 = NOT seen, 3 = the
     healthy control was not green ⇒ nothing could be injected.

⚠ OUTCOMES: 0 green · 1 red · 3 «I could not look», with the reason.
   The 3 is the BENCH's (the window does not show, the press did not reach
   the PAGE, the pointer is not where I say); the red is the PRODUCT's (the
   page sent press and movement, and the window did not change
   size).

⚠ WHERE IT RUNS: on the machine that has the browsers (the server, `REMOTIX_SUL_SERVER=1`
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

QUI = os.path.dirname(os.path.abspath(__file__))


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ Imported, not copied: C21 brings `12-c20-veri` and `12-client-veri` along
#   — a single VERI in memory, and the ESC already added to the key table.
C21 = _carica("c21", os.path.join(QUI, "11-c21-sul-bordo-la-forma-cambia.py"))
C20V, VERI = C21.C20V, C21.VERI
VERDE, ROSSO, CIECO = C21.VERDE, C21.ROSSO, C21.CIECO
PORTE = C21.PORTE
NOME_ESITO = C21.NOME_ESITO

MODELLO_INQUILINO = re.compile(r"^c22u[0-9]+$")

# ---------------------------------------------------------------------------
# ⛔ THE NUMBERS — each with its reason.
# ---------------------------------------------------------------------------
# ⭐ The grab points, in DESKTOP pixels relative to the last cyan pixel:
#   from 2 inside to 6 outside (the three measured zones are between -1 and +7).
PRESE = tuple(range(-2, 7))
# How far it drags, and in how many steps: a hand gesture, not a jump.
SPINTA = 150
PASSI = 15
PAUSA_PASSO_MS = 30
# ⭐ Green wants at least 100 px of the 150: the desktop can round the size
#   (the character grid, a minimum, an unfinished animation) but a
#   real resize brings almost all of them.
SOGLIA = 100
# The left edge and the top must stay still within these pixels: otherwise the
# window MOVED, it was not resized.
FERMO = 4
# Between one point and the next: more than every desktop's double click (400-500 ms),
# so two close presses do not become a «double click on the edge».
FRA_I_PUNTI_S = 1.0


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS — and they are the ones `--certifica` tests
# ═══════════════════════════════════════════════════════════════════════════
def finestra_nel_desktop(geo, f):
    """The window found in the photo (`C21.trova_finestra`) in desktop pixels:
    {sinistro, destro, alto} — the right one is the LAST cyan pixel."""
    pw, ph = f["foto"]
    x0, y0 = C21.dalla_foto_al_desktop(geo, pw, ph, f["ciano"][0] + 0.5, f["ciano"][1] + 0.5)
    xd, _ = C21.dalla_foto_al_desktop(geo, pw, ph, f["destro"] + 0.5, f["centro"][1] + 0.5)
    return {"sinistro": int(x0), "destro": int(xd), "alto": int(y0)}


def giudica_presa(k, prima, dopo):
    """⭐ The judgement of ONE grab point.

    `prima`, `dopo`  {sinistro, destro, alto} in desktop pixels, or None
    Returns (outcome, reason, shift of the right edge | None)."""
    if not dopo:
        return CIECO, "%+d px: after the drag the window is no longer visible" % k, None
    sp = dopo["destro"] - prima["destro"]
    ds = dopo["sinistro"] - prima["sinistro"]
    da = dopo["alto"] - prima["alto"]
    fermi = abs(ds) <= FERMO and abs(da) <= FERMO
    if sp >= SOGLIA and fermi:
        return VERDE, ("%+d px: the right edge went from x=%d to x=%d (%+d px), the "
                       "left one and the top still — RESIZED"
                       % (k, prima["destro"], dopo["destro"], sp)), sp
    if sp >= SOGLIA:
        return ROSSO, ("%+d px: the right edge %+d px but the left one too %+d and the top "
                       "%+d — the window MOVED, it was not resized" % (k, sp, ds, da)), sp
    return ROSSO, ("%+d px: the right edge %+d px (%d needed), the left one %+d — the size "
                   "did not change" % (k, sp, SOGLIA, ds)), sp


def giudica_scansione(risultati):
    """[(k, outcome, reason, sp)] ⇒ (outcome, reason, (k, sp) | None).

    GREEN at the first green point; RED if all the points were looked at and
    none is green; CIECO if a point could not be looked at before a
    green (the vanished window is not a «does not resize»)."""
    if not risultati:
        return CIECO, "no grab point tried", None
    for k, e, m, sp in risultati:
        if e == VERDE:
            return VERDE, m, (k, sp)
        if e == CIECO:
            return CIECO, m, None
    return ROSSO, ("in NONE of the %d grab points (from %+d to %+d px from the edge) did the window "
                   "change size: %s" % (len(risultati), risultati[0][0], risultati[-1][0],
                                              "; ".join(r[2] for r in risultati[-2:]))), None


def verdetto_col_guasto(senza, sano):
    """⭐ The injected fault, read the other way round.

    `senza`  (outcome, reason, x) of the scan with the button UP
    `sano`   (outcome, reason, x) of the control with the button, or None
    Returns (outcome of the mesh with the fault, reason)."""
    if senza[0] == VERDE:
        return ROSSO, ("⛔ FAULT NOT SEEN: with the button up the window changed size "
                       "all the same (%s)" % senza[1])
    if senza[0] == CIECO:
        return CIECO, "with the button up I could not look: %s" % senza[1]
    if not sano or sano[0] != VERDE:
        return CIECO, ("the healthy control is not green (%s): the fault cannot be injected"
                       % (sano[1] if sano else "not done"))
    return VERDE, ("⭐ FAULT SEEN: with the button up no point resizes, with the button "
                   "they do (%s)" % sano[1])


def gesto(x0, y0, dx, passi):
    """The points of the drag, in desktop pixels: the start excluded."""
    return [(x0 + dx * (i + 1) / float(passi), y0) for i in range(passi)]


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION OF THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    print("⭐ 11-c22 · CERTIFICATION OF THE PURE FUNCTIONS")
    guai, fatte = [], []

    def prova(cosa, vero, dettaglio=""):
        fatte.append(cosa)
        print("   %s %s%s" % ("⭐ ok  " if vero else "⛔ NO  ", cosa,
                              (" — " + dettaglio) if dettaglio else ""))
        if not vero:
            guai.append(cosa)

    P = {"sinistro": 80, "destro": 1807, "alto": 80}
    casi = [
        ("widened by 150, left still ⇒ GREEN",
         {"sinistro": 80, "destro": 1957, "alto": 80}, VERDE),
        ("widened by 120 (rounded) ⇒ GREEN",
         {"sinistro": 81, "destro": 1927, "alto": 80}, VERDE),
        ("widened by 60 ⇒ RED", {"sinistro": 80, "destro": 1867, "alto": 80}, ROSSO),
        ("still ⇒ RED", dict(P), ROSSO),
        ("MOVED by 150 (both edges) ⇒ RED",
         {"sinistro": 230, "destro": 1957, "alto": 80}, ROSSO),
        ("widened but the top moved ⇒ RED",
         {"sinistro": 80, "destro": 1957, "alto": 140}, ROSSO),
        ("vanished ⇒ 3", None, CIECO),
    ]
    for nome, dopo, atteso in casi:
        e, m, _sp = giudica_presa(3, P, dopo)
        prova("giudica_presa: %s" % nome, e == atteso, m)
    r = [(-2, ROSSO, "a", 0), (-1, ROSSO, "b", 1), (0, VERDE, "c", 148)]
    e, m, x = giudica_scansione(r)
    prova("giudica_scansione: green at 0 px ⇒ GREEN, and it says where", e == VERDE and x == (0, 148), m)
    e, m, x = giudica_scansione([(k, ROSSO, "still", 0) for k in PRESE])
    prova("giudica_scansione: no point ⇒ RED", e == ROSSO, m)
    e, m, x = giudica_scansione([(-2, ROSSO, "a", 0), (-1, CIECO, "vanished", None)])
    prova("giudica_scansione: vanished before a green ⇒ 3", e == CIECO, m)
    prova("giudica_scansione: empty ⇒ 3", giudica_scansione([])[0] == CIECO)
    # the fault, read the other way round
    R, V, Cc = (ROSSO, "still", None), (VERDE, "+1 px", (1, 150)), (CIECO, "vanished", None)
    for nome, senza, sano, atteso in [
            ("up still, healthy green ⇒ 0 (seen)", R, V, VERDE),
            ("up RESIZES ⇒ 1 (not seen)", V, V, ROSSO),
            ("up still, healthy RED ⇒ 3", R, (ROSSO, "still", None), CIECO),
            ("up still, healthy not done ⇒ 3", R, None, CIECO),
            ("up blind ⇒ 3", Cc, V, CIECO)]:
        e, m = verdetto_col_guasto(senza, sano)
        prova("verdetto_col_guasto: %s" % nome, e == atteso, m)
    g = gesto(100, 50, SPINTA, PASSI)
    prova("gesture: %d steps, the last one at +%d" % (PASSI, SPINTA),
          len(g) == PASSI and g[-1] == (100 + SPINTA, 50) and g[0][0] > 100)
    # the window in the photo ⇒ in the desktop (geometry 1:1 and 2:1)
    f = {"foto": [400, 250], "ciano": [50, 40, 299, 199], "destro": 299, "centro": [174, 118]}
    geo = {"bw": 400, "bh": 250, "bx0": 0, "by0": 0, "sx": 1.0, "sy": 1.0}
    d = finestra_nel_desktop(geo, f)
    prova("finestra_nel_desktop 1:1", d == {"sinistro": 50, "destro": 299, "alto": 40}, str(d))
    geo2 = dict(geo, bw=800, bh=500)
    d2 = finestra_nel_desktop(geo2, f)
    prova("finestra_nel_desktop with the photo at half size", d2["destro"] == 599, str(d2))
    print()
    if guai:
        print("⛔ CERTIFICATION FAILED: %d tests out of %d" % (len(guai), len(fatte)))
        return 1
    print("⭐ CERTIFIED: the judge tells apart resized, still and MOVED, and the\n"
          "   fault reads the other way round only with the healthy control green.")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE PAGE — what it saw, to separate the bench from the product
# ═══════════════════════════════════════════════════════════════════════════
JS_OSSERVA = r"""
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
JS_AZZERA = ("const C=window.__C22__; if(!C) return false; "
             "C.giu=0; C.su=0; C.premuti=0; C.alzati=0; return true;")
JS_CONTA = r"""
const C = window.__C22__;
const st = window.REMOTIX && REMOTIX.input_classico ? REMOTIX.input_classico.stato() : null;
return C ? { giu: C.giu, su: C.su, premuti: C.premuti, alzati: C.alzati,
             spedito: st ? st.ultimo_spedito : null } : null;
"""


def trascina(g, geo, X, Y, premi):
    """⭐ The gesture, with REAL browser EVENTS: the pointer is brought to (X,Y),
    pressed (if `premi`), dragged right by `SPINTA` px in `PASSI`
    steps, released.  (X,Y) and the points are DESKTOP pixels."""
    punti = [C21.dal_desktop_al_vetro(geo, X, Y)] + \
        [C21.dal_desktop_al_vetro(geo, x, y) for x, y in gesto(X, Y, SPINTA, PASSI)]
    if hasattr(g, "cdp"):
        c = g.cdp.chiama
        x0, y0 = punti[0]
        c("Input.dispatchMouseEvent", type="mouseMoved", x=x0, y=y0)
        time.sleep(0.15)
        if premi:
            c("Input.dispatchMouseEvent", type="mousePressed", x=x0, y=y0, button="left",
              buttons=1, clickCount=1)
        time.sleep(0.2)
        for x, y in punti[1:]:
            if premi:
                c("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, button="left",
                  buttons=1)
            else:
                c("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
            time.sleep(PAUSA_PASSO_MS / 1000.0)
        time.sleep(0.2)
        if premi:
            x, y = punti[-1]
            c("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left",
              buttons=0, clickCount=1)
        return
    # Marionette: ONE chain of actions, so the button stays down between the steps
    az = [{"type": "pointerMove", "x": int(round(punti[0][0])), "y": int(round(punti[0][1])),
           "origin": "viewport", "duration": 0},
          {"type": "pause", "duration": 150}]
    if premi:
        az.append({"type": "pointerDown", "button": 0})
    az.append({"type": "pause", "duration": 200})
    for x, y in punti[1:]:
        az.append({"type": "pointerMove", "x": int(round(x)), "y": int(round(y)),
                   "origin": "viewport", "duration": 0})
        az.append({"type": "pause", "duration": PAUSA_PASSO_MS})
    az.append({"type": "pause", "duration": 200})
    if premi:
        az.append({"type": "pointerUp", "button": 0})
    g._azioni([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                "actions": az}])


def misura(g, geo, o, nome, etichetta):
    """The window in the desktop, from the (still) photograph, or (None, reason)."""
    f, perche = C21.cerca_la_finestra(g, o.attesa_finestra, "", nome)
    if not f:
        return None, perche
    if o.salva:
        try:
            with open(os.path.join(o.salva, "%s-%s.png" % (nome, etichetta)), "wb") as fh:
                fh.write(C21.foto_piena(g))
        except Exception:                        # noqa: BLE001
            pass
    return dict(finestra_nel_desktop(geo, f), cy=f["centro"][1], f=f), ""


def scansiona(g, geo, o, nome, premi):
    """⭐ The scan of the grab points.  Returns (outcome, reason, x, rows)."""
    righe = []
    for k in PRESE:
        prima, perche = misura(g, geo, o, nome, "prima%+d" % k)
        if not prima:
            righe.append((k, CIECO, "%+d px: before the gesture the window does not show: %s"
                          % (k, perche), None))
            break
        pw, ph = prima["f"]["foto"]
        _x, Yc = C21.dalla_foto_al_desktop(geo, pw, ph, 0, prima["cy"] + 0.5)
        X = prima["destro"] + k + 0.5
        if X + SPINTA + 2 >= geo["tl"]:
            righe.append((k, CIECO, "%+d px: on the right there is no room to drag (edge "
                          "x=%d, screen %d)" % (k, prima["destro"], geo["tl"]), None))
            break
        g.js(JS_AZZERA)
        trascina(g, geo, X, Yc, premi)
        time.sleep(0.3)
        n = g.js(JS_CONTA) or {}
        # ⛔ The bench before the product: if the page did not see the gesture,
        #   there is nothing to judge.
        if premi and (n.get("giu", 0) < 1 or n.get("su", 0) < 1
                      or n.get("premuti", 0) < PASSI // 2):
            righe.append((k, CIECO, "%+d px: the browser did not deliver the gesture to the page "
                          "(%s)" % (k, n), None))
            break
        if not premi and (n.get("giu", 0) or n.get("alzati", 0) < PASSI // 2):
            righe.append((k, CIECO, "%+d px: the gesture with the button up did not arrive as "
                          "it should (%s)" % (k, n), None))
            break
        sp_ = n.get("spedito") or [-1, -1]
        atteso_x = int(X + SPINTA)
        if abs(sp_[0] - atteso_x) > 2 or abs(sp_[1] - int(Yc)) > 2:
            righe.append((k, CIECO, "%+d px: the page sent last (%s,%s) instead of "
                          "(%d,%d): the pointer is not where I say"
                          % (k, sp_[0], sp_[1], atteso_x, int(Yc)), None))
            break
        dopo, perche = misura(g, geo, o, nome, "dopo%+d" % k)
        e, m, sp = giudica_presa(k, prima, dopo)
        if not dopo:
            m += " (%s)" % perche
        print("   %s grab %+d px (x=%d, y=%d)%s → %s" % (
            {VERDE: "⭐", ROSSO: "·", CIECO: "⚠"}[e], k, int(X), int(Yc),
            "" if premi else " with the button UP", m), flush=True)
        righe.append((k, e, m, sp))
        if e != ROSSO:
            break
        time.sleep(FRA_I_PUNTI_S)
    es, ms, x = giudica_scansione(righe)
    return es, ms, x, righe


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST OF ONE BROWSER
# ═══════════════════════════════════════════════════════════════════════════
def prova_browser(nome, o, sc, chi):
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
            return dict(riga, esito=CIECO, perche="the page does not open: " + m)
        e, m, s = pr.entra(o.parola)
        if e != VERDE:
            return dict(riga, esito=CIECO, perche="the login: " + m)
        e, m, s = pr.primo_fotogramma()
        e, m = C20V.desktop_scuro_ma_vivo(e, m, s)
        print("   ⭐ first frame: %s" % m, flush=True)
        if e != VERDE:
            return dict(riga, esito=CIECO, perche="without an image there is no looking: " + m)
        geo = g.js(C21.JS_GEOMETRIA)
        if not geo:
            return dict(riga, esito=CIECO, perche="`REMOTIX_PUNTATORE.geometria` is not there")
        print("   canvas %sx%s · buffer %sx%s · layout «%s»"
              % (geo["tl"], geo["ta"], geo["bw"], geo["bh"], geo["disposizione"]), flush=True)
        if geo["disposizione"] != "classico":
            # ⛔ The mouse with buttons belongs to the classic layout; with the finger
            #   the drag is another gesture, and it is not this question.
            return dict(riga, esito=CIECO, perche="the page is not in the classic "
                        "layout (%s)" % geo["disposizione"])
        # ⚠ C21's wake-up (GNOME is born in the overview), BEFORE the window
        print("   wake-up: %s" % C21.sveglia(g, geo), flush=True)
        largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
        ok, t = C21.prepara_la_casa(sc, chi, largo_f, alto_f)
        if not ok:
            return dict(riga, esito=CIECO, perche="the home cannot be prepared: %s" % t[-200:])
        ok, t = C21.accendi_la_finestra(sc, chi)
        if not ok:
            return dict(riga, esito=CIECO, perche="firefox-esr does not start: %s" % t[-200:])
        w0, perche = misura(g, geo, o, nome, "finestra")
        if not w0:
            return dict(riga, esito=CIECO, perche="the test window does not show within %d s: %s"
                        % (o.attesa_finestra, perche))
        if w0["destro"] - w0["sinistro"] < 0.7 * largo_f:
            return dict(riga, esito=CIECO, perche="the window is %d px wide and I asked for "
                        "%d: it is a preview (the overview?), not the window"
                        % (w0["destro"] - w0["sinistro"], largo_f))
        riga["finestra"] = {k: w0[k] for k in ("sinistro", "destro", "alto")}
        print("   ⭐ window: x=%d..%d, top y=%d in the desktop · grabs from %+d to %+d px"
              % (w0["sinistro"], w0["destro"], w0["alto"], PRESE[0], PRESE[-1]), flush=True)
        g.js(VERI._inietta(JS_OSSERVA))
        if not g.js("return !!window.__C22__;"):
            return dict(riga, esito=CIECO, perche="the observer did not install itself")

        if not o.senza_pulsante:
            es, ms, x, righe = scansiona(g, geo, o, nome, True)
            riga["prese"] = [[k, e, m] for k, e, m, _ in righe]
            if x:
                riga["presa_px"], riga["spostamento_px"] = x
            return dict(riga, esito=es, perche=ms)
        # ── the injected fault: first with the button up, then the control ──
        print("   ── --senza-pulsante: the same gesture, button UP ──", flush=True)
        senza = scansiona(g, geo, o, nome, False)
        riga["senza_pulsante"] = [[k, e, m] for k, e, m, _ in senza[3]]
        sano = None
        if senza[0] == ROSSO:
            print("   ── the healthy control: with the button ──", flush=True)
            sano = scansiona(g, geo, o, nome, True)
            riga["sano"] = [[k, e, m] for k, e, m, _ in sano[3]]
            if sano[2]:
                riga["presa_px"], riga["spostamento_px"] = sano[2]
        eg, mg = verdetto_col_guasto(senza[:3], sano[:3] if sano else None)
        return dict(riga, esito=eg, perche=mg)
    finally:
        try:
            g.chiudi()
        except Exception as ex:                  # noqa: BLE001
            print("   ⚠ closing the browser: %s" % ex)


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", choices=sorted(PORTE))
    a.add_argument("--porta", type=int)
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--browser", default="firefox,chrome")
    a.add_argument("--visibile", action="store_true",
                   help="real windows (in the nested compositor) instead of headless")
    a.add_argument("--salva", default="", help="folder for the photographs")
    a.add_argument("--senza-pulsante", action="store_true",
                   help="INJECTED FAULT: the same drag with the button up")
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
    o.parola = "c22-" + secrets.token_hex(6)
    o.scena, o.continuita_s, o.registro_cmd = "viva", 8, ""
    o.lascia_acceso = False
    if o.salva:
        os.makedirs(o.salva, exist_ok=True)
    sc = C20V.Scatola(o.scatola)
    chi = "c22u%03d" % random.randint(0, 999)
    assert MODELLO_INQUILINO.match(chi)
    o.utente = chi
    print("⭐ 11-c22 · %s · %s · inquilino %s · browser %s · %s%s"
          % (sc.contenitore, o.url, chi, o.browser,
             "real windows" if o.visibile else "HEADLESS",
             " · ⛔ INJECTED FAULT --senza-pulsante" if o.senza_pulsante else ""))
    righe = []
    for b in [x.strip() for x in o.browser.split(",") if x.strip()]:
        sc.sgombera(chi)
        c, t = sc.crea(chi, o.parola)
        if c != 0:
            print("⛔ I could not create %s: %s" % (chi, t[-200:]))
            return 3
        try:
            r = prova_browser(b, o, sc, chi)
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
    if o.senza_pulsante:
        print({VERDE: "⭐ THE INJECTED FAULT WAS SEEN (outcome 0: the other way round, "
                      "like every fault of the net)",
               ROSSO: "⛔⛔ THE INJECTED FAULT WAS NOT SEEN",
               CIECO: "⚠ with the injected fault I could NOT look ⇒ 3"}[esito])
    else:
        print("%s C22(%s): %s" % ({VERDE: "⭐", ROSSO: "⛔⛔", CIECO: "⚠"}[esito],
                                  o.scatola, NOME_ESITO[esito]))
    return esito


if __name__ == "__main__":
    sys.exit(main())
