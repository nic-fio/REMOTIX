#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f004 — F-004 THE MOUSE: movement, left click, right click, double click,
          drag, selection

    python3 15-f004-il-mouse.py --scatola kde --browser chrome [--guasto]

In the tenant's session runs the known scene of `15-g2-scena.py`
(firefox-esr --kiosk).  Every gesture is made with REAL browser EVENTS
(Marionette / CDP) on the REMOTIX canvas, and it is judged from the EFFECT
in the remote application — the state that the remote page writes in its
notebook, and for the context menu the PHOTO:

  movimento     the pointer goes to three points of the BLUE block: the remote page
                says where it saw it (fraction of the block), within 5 %
  clic sinistro a click on the GREEN button: its counter +1, button 0
  clic destro   a right click on the background: the MAGENTA menu appears IN THE
                PHOTO with its corner where it was pressed (within 2 % of the desktop)
  doppio clic   on «gamma»: the selected text is «gamma»
  trascinamento the YELLOW box grabbed and carried right by 15 % of the page:
                it moves by that much (within 10 %), not vertically
  selezione     pressed at the start of «beta», dragged to the end of «delta»:
                the selected text is «beta gamma delta»

FAULT (--guasto, same session): every gesture IN THE VOID, with the same judge:
  movement ⇒ the pointer goes onto the BACKGROUND (off the target) · left
  click ⇒ click outside the button · right ⇒ button not pressed · double
  click ⇒ a single press · drag and selection ⇒ button not
  pressed.  The fault is SEEN if EVERY gesture gives red.

A red gesture in the healthy pass is REDONE once before calling it FAIL
(the server is shared by ten agents).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G2 = S._carica("g2scena", os.path.join(S.QUI, "15-g2-scena.py"))

FUNZIONI = ("F-004",)
GESTI = ("movimento", "clic-sinistro", "clic-destro", "doppio-clic", "trascinamento",
         "selezione")
PUNTI_PAD = ((0.25, 0.3), (0.7, 0.6), (0.5, 0.8))
TOLL_PAD = 0.05
SPINTA = 0.15            # of the page width
PASSI = 15
ATTESA_S = 5.0


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure functions: (outcome, sentence)
# ═══════════════════════════════════════════════════════════════════════════
def giudica_movimento(st, atteso):
    p = (st or {}).get("pad")
    if not p:
        return S.FAIL, "the remote page did not see the pointer on the BLUE block"
    d = max(abs(p[0] - atteso[0]), abs(p[1] - atteso[1]))
    if d <= TOLL_PAD:
        return S.PASS, "seen at (%.2f,%.2f), expected (%.2f,%.2f)" % (p[0], p[1], atteso[0],
                                                                    atteso[1])
    return S.FAIL, "seen at (%.2f,%.2f) instead of (%.2f,%.2f)" % (p[0], p[1], atteso[0],
                                                                  atteso[1])


def giudica_clic(st):
    st = st or {}
    if st.get("clic") == 1 and st.get("clicbtn") == 0:
        return S.PASS, "the button counted 1 click with button 0"
    return S.FAIL, "the button counted %s clicks (button %s; clicks outside %s; down %s)" % (
        st.get("clic"), st.get("clicbtn"), st.get("fuori"), st.get("giu"))


def giudica_menu(blocco, punto, tl):
    """`blocco` = magenta box in the desktop (X0,Y0,X1,Y1) or None;
    `punto` = where it was pressed (desktop)."""
    if not blocco:
        return S.FAIL, "no MAGENTA menu in the photo"
    d = max(abs(blocco[0] - punto[0]), abs(blocco[1] - punto[1]))
    if d <= 0.02 * tl:
        return S.PASS, "menu in the photo with its corner %.0f px from the pressed point" % d
    return S.FAIL, "menu in the photo but %.0f px from the pressed point (%s vs %s)" % (
        d, [round(v) for v in blocco[:2]], [round(v) for v in punto])


def giudica_selezione(st, atteso):
    sel = ((st or {}).get("sel") or "").strip()
    if sel == atteso:
        return S.PASS, "selected %r" % sel
    return S.FAIL, "selected %r instead of %r" % (sel, atteso)


def giudica_box(st, attesa_dx, alto):
    st = st or {}
    b = st.get("box") or [0, 0]
    if not st.get("boxn"):
        return S.FAIL, "the box was not grabbed (no release) · moved %s" % (b,)
    if abs(b[0] - attesa_dx) <= 0.1 * attesa_dx and abs(b[1]) <= 0.05 * alto:
        return S.PASS, "the box moved by %.0f px (expected %.0f)" % (b[0], attesa_dx)
    return S.FAIL, "the box moved by %s px, expected (%.0f, 0)" % (b, attesa_dx)


def esito_col_guasto(esiti):
    if S.BLOCKED in esiti:
        return None
    return all(e == S.FAIL for e in esiti)


def certifica():
    guai = []

    def prova(cosa, vero):
        print("   %s %s" % ("⭐ ok " if vero else "⛔ NO ", cosa))
        if not vero:
            guai.append(cosa)
    prova("right movement ⇒ PASS", giudica_movimento({"pad": [0.26, 0.31]}, (0.25, 0.3))[0]
          == S.PASS)
    prova("movement elsewhere ⇒ FAIL", giudica_movimento({"pad": [0.7, 0.6]}, (0.25, 0.3))[0]
          == S.FAIL)
    prova("no movement ⇒ FAIL", giudica_movimento({"pad": None}, (0.25, 0.3))[0] == S.FAIL)
    prova("click ⇒ PASS", giudica_clic({"clic": 1, "clicbtn": 0})[0] == S.PASS)
    prova("click outside ⇒ FAIL", giudica_clic({"clic": 0, "fuori": 1})[0] == S.FAIL)
    prova("menu at the point ⇒ PASS", giudica_menu((100, 100, 500, 400), (102, 98), 3840)[0]
          == S.PASS)
    prova("menu far away ⇒ FAIL", giudica_menu((900, 100, 1200, 400), (102, 98), 3840)[0]
          == S.FAIL)
    prova("no menu ⇒ FAIL", giudica_menu(None, (1, 1), 3840)[0] == S.FAIL)
    prova("right selection ⇒ PASS", giudica_selezione({"sel": "gamma "}, "gamma")[0] == S.PASS)
    prova("empty selection ⇒ FAIL", giudica_selezione({"sel": ""}, "gamma")[0] == S.FAIL)
    prova("box moved ⇒ PASS", giudica_box({"box": [570, 2], "boxn": 1}, 576, 2160)[0]
          == S.PASS)
    prova("box still ⇒ FAIL", giudica_box({"box": [0, 0], "boxn": 0}, 576, 2160)[0] == S.FAIL)
    prova("fault: all red ⇒ seen", esito_col_guasto([S.FAIL] * 6) is True)
    prova("fault: one green ⇒ not seen", esito_col_guasto([S.FAIL, S.PASS]) is False)
    prova("fault: one blocked ⇒ None", esito_col_guasto([S.FAIL, S.BLOCKED]) is None)
    # the colour box and the straight line
    try:
        from PIL import Image, ImageDraw
        im = Image.new("RGB", (800, 450), (32, 32, 32))
        d = ImageDraw.Draw(im)
        d.rectangle([24, 18, 239, 89], fill=G2.BLU)
        t = G2.trova_colore(im, G2.BLU, passo=2)
        prova("finds the blue block (%s)" % t, t and abs(t["x0"] - 24) <= 2
              and abs(t["x1"] - 240) <= 2 and t["pieno"] > 0.9)
    except ImportError:
        prova("PIL is there", False)
    a = G2.adatta([(0, 10), (100, 210), (50, 110)])
    prova("the line through three points (%s)" % (a,), a and abs(a[0] - 2) < 1e-6 and abs(a[1] - 10) < 1e-6)
    print("⛔ CERTIFICATION FAILED" if guai else "⭐ CERTIFIED")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE GESTURES
# ═══════════════════════════════════════════════════════════════════════════
def nel_rett(r, fx, fy):
    return r[0] + fx * (r[2] - r[0]), r[1] + fy * (r[3] - r[1])


def fa_gesto(nome, s, sc, mp, guasto, ev):
    """Makes the gesture `nome` (healthy or in the void) and judges it.  Returns (outcome, sentence)."""
    g = s.g
    R = sc.rett
    if sc.comanda("reset") is None:
        return S.BLOCKED, "the scene did not answer the reset"
    R = sc.rett or R
    W, H = R["W"], R["H"]
    sfondo = (W * 0.80, H * 0.72)          # empty: under field b, outside everything
    if nome == "movimento":
        esiti = []
        for fx, fy in PUNTI_PAD:
            x, y = nel_rett(R["pad"], fx, fy)
            if guasto:
                x, y = W * 0.33, H * 0.12   # between the pad and the button: off the target
            mouse_muovi(g, mp, x, y)
            st = sc.aspetta(lambda q, a=(fx, fy): giudica_movimento(q, a)[0] == S.PASS,
                            ATTESA_S)
            esiti.append(giudica_movimento(st, (fx, fy)))
            if esiti[-1][0] != S.PASS:
                break
        brutti = [e for e in esiti if e[0] != S.PASS]
        return (brutti[0] if brutti else
                (S.PASS, "three points: " + " · ".join(e[1] for e in esiti)))
    if nome == "clic-sinistro":
        x, y = centro_r(R["bot"])
        if guasto:
            x, y = W * 0.33, H * 0.12
        clic(g, mp, x, y, 0)
        st = sc.aspetta(lambda q: giudica_clic(q)[0] == S.PASS, ATTESA_S)
        return giudica_clic(st)
    if nome == "clic-destro":
        x, y = sfondo
        X, Y = mp.desktop(x, y)
        if guasto:
            G2.mouse(g, [("muovi",) + mp.vetro(x, y), ("pausa", 300)])
        else:
            clic(g, mp, x, y, 2)
        sc.aspetta(lambda q: bool(q.get("menu")), 3.0 if guasto else ATTESA_S)
        time.sleep(0.8)
        im, dove = G2.foto_pil(s, "destro-%s" % ("guasto" if guasto else "sano"))
        if im is None:
            return S.BLOCKED, "the photo of the menu cannot be taken: %s" % dove
        ev.append(dove)
        pw, ph = im.size
        t = G2.trova_colore(im, G2.MAGENTA)
        blocco = None
        if t and t["pieno"] > 0.7:
            X0, Y0 = S.C21.dalla_foto_al_desktop(mp.geo, pw, ph, t["x0"], t["y0"])
            X1, Y1 = S.C21.dalla_foto_al_desktop(mp.geo, pw, ph, t["x1"], t["y1"])
            blocco = (X0, Y0, X1, Y1)
        return giudica_menu(blocco, (X, Y), mp.geo["tl"])
    if nome == "doppio-clic":
        x, y = centro_r(R["w3"])
        vx, vy = mp.vetro(x, y)
        p = [("muovi", vx, vy), ("pausa", 200), ("giu", 0, 1), ("pausa", 50), ("su", 0, 1)]
        if not guasto:
            p += [("pausa", 90), ("giu", 0, 2), ("pausa", 50), ("su", 0, 2)]
        G2.mouse(g, p)
        st = sc.aspetta(lambda q: giudica_selezione(q, "gamma")[0] == S.PASS,
                        ATTESA_S)
        return giudica_selezione(st, "gamma")
    if nome in ("trascinamento", "selezione"):
        if nome == "trascinamento":
            x0, y0 = centro_r(R["box"])
            x1, y1 = x0 + SPINTA * W, y0
        else:
            cw = (R["w2"][2] - R["w2"][0]) / 4.0
            x0, y0 = R["w2"][0] + 0.25 * cw, centro_r(R["w2"])[1]
            x1, y1 = R["w4"][2] - 0.25 * cw, y0
        trascina(g, mp, (x0, y0), (x1, y1), premi=not guasto)
        if nome == "trascinamento":
            st = sc.aspetta(lambda q: giudica_box(q, x1 - x0, H)[0] == S.PASS, ATTESA_S)
            return giudica_box(st, x1 - x0, H)
        st = sc.aspetta(lambda q: giudica_selezione(q, "beta gamma delta")[0] == S.PASS,
                        ATTESA_S)
        return giudica_selezione(st, "beta gamma delta")
    raise ValueError(nome)


def centro_r(r):
    return (r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0


def mouse_muovi(g, mp, x, y):
    vx, vy = mp.vetro(x, y)
    G2.mouse(g, [("muovi", vx, vy), ("pausa", 100)])


def clic(g, mp, x, y, bottone):
    vx, vy = mp.vetro(x, y)
    G2.mouse(g, [("muovi", vx, vy), ("pausa", 200), ("giu", bottone, 1), ("pausa", 80),
                 ("su", bottone, 1)])


def trascina(g, mp, da, a, premi):
    p = [("muovi",) + mp.vetro(*da), ("pausa", 200)]
    if premi:
        p += [("giu", 0, 1), ("pausa", 200)]
    for i in range(PASSI):
        f = (i + 1) / float(PASSI)
        p += [("muovi",) + mp.vetro(da[0] + (a[0] - da[0]) * f, da[1] + (a[1] - da[1]) * f),
              ("pausa", 40)]
    p += [("pausa", 200)]
    if premi:
        p += [("su", 0, 1)]
    G2.mouse(g, p)


def gesto_protetto(nome, s, sc, mp, guasto, ev):
    """The gesture; a BENCH fault (the browser protocol falling over, the
    scene not answering under load) becomes BLOCKED for that gesture, and it is
    retried once before saying so."""
    ultimo = None
    for _tentativo in range(2):
        try:
            e, m = fa_gesto(nome, s, sc, mp, guasto, ev)
        except Exception as x:                   # noqa: BLE001
            e, m = S.BLOCKED, "the bench fell over in the gesture: %s" % str(x)[:160]
        if e != S.BLOCKED:
            return e, m
        ultimo = (e, m)
        time.sleep(3)
    return ultimo


# ═══════════════════════════════════════════════════════════════════════════
def passata(s, sc, mp, guasto):
    """All the gestures; returns [(gesture, outcome, sentence)]."""
    righe = []
    for nome in GESTI:
        ev = []
        e, m = gesto_protetto(nome, s, sc, mp, guasto, ev)
        if e == S.FAIL and not guasto:
            print("   ⚠ %s red (%s): redoing it to confirm" % (nome, m), flush=True)
            e2, m2 = gesto_protetto(nome, s, sc, mp, guasto, ev)
            if e2 == S.PASS:
                m = "⚠ RED at the first attempt (%s), green at the second: %s" % (m, m2)
                e = S.PASS
            else:
                m = "red twice: %s · %s" % (m, m2)
                e = e2
        print("   %s %-14s %s" % ({S.PASS: "⭐", S.FAIL: "⛔", S.BLOCKED: "⚠"}[e], nome, m),
              flush=True)
        righe.append((nome, e, m, ev))
    return righe


def corpo(o, E):
    porta_scena = o.porte_base + 5
    with S.Sessione(o, "004", E) as s:
        sc, mp, geo, dove = G2.prepara(s, porta_scena)
        ev0 = [dove] if dove else []
        atteso = ("movement on the BLUE block where it points, click on the GREEN counted, MAGENTA menu "
                  "where the right one is pressed, double click ⇒ «gamma», box moved, dragged "
                  "⇒ «beta gamma delta»")
        righe = passata(s, sc, mp, False)
        _p, fin = G2.foto(s, "fine-sana")
        ev = ev0 + [x for r in righe for x in r[3]] + ([fin] if fin else [])
        oss = " · ".join("%s: %s %s" % (n, e, m) for n, e, m, _ in righe)
        es = [r[1] for r in righe]
        if S.FAIL in es:
            E.metti("F-004", S.FAIL, "red gestures: " + ", ".join(
                n for n, e, _m, _ in righe if e == S.FAIL), atteso=atteso, osservato=oss,
                evidenze=ev + [s.salva_console()])
        elif S.BLOCKED in es:
            E.metti("F-004", S.BLOCKED, "gestures not looked at: " + ", ".join(
                "%s (%s)" % (n, m) for n, e, m, _ in righe if e == S.BLOCKED),
                atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-004", S.PASS, "six gestures out of six: the effect is there in the application",
                    atteso=atteso, osservato=oss, evidenze=ev)
        if o.guasto:
            righe = passata(s, sc, mp, True)
            es = [r[1] for r in righe]
            visto = esito_col_guasto(es)
            oss = " · ".join("%s: %s %s" % (n, e, m) for n, e, m, _ in righe)
            E.guasto("F-004", visto,
                     {True: "every gesture in the void gave red",
                      False: "gestures in the void GREEN anyway: " + ", ".join(
                          n for n, e, _m, _ in righe if e == S.PASS),
                      None: "a gesture in the void could not be looked at"}[visto],
                     atteso="every gesture in the void ⇒ red", osservato=oss,
                     evidenze=[x for r in righe for x in r[3]])


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
