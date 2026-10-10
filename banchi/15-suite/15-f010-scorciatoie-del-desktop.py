#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f010 — F-010 DESKTOP SHORTCUTS

    python3 15-f010-scorciatoie-del-desktop.py --scatola xfce --browser firefox [--guasto]

EXPECTED: the USE shortcuts reach the desktop and do their job; the
DANGEROUS ones (the screen lock) do NOT — the screen stays the desktop.

THE SCENE: in the tenant's session two KNOWN windows, GTK4 filled with a
pure colour — CYAN and then MAGENTA — 60% x 68% of the desktop in size, that is so
large that wherever the compositor puts them THEY OVERLAP (two widths exceed the
desktop).  They have different app_ids: on GNOME Alt+Tab switches between applications.

  1. use: Alt+Tab (REAL keys to the browser: CDP `Input.dispatchKeyEvent` on
     Chrome, W3C Marionette actions on Firefox, like C23).  From the PHOTO: the
     window that was on top (the one whose colour covers more pixels) goes
     below — the sign of (cyan - magenta) FLIPS.
  2. dangerous: Super+L, then Ctrl+Alt+L.  After 5 s the photo: the desktop is
     still that one (the two windows with their colour within 25%, luminance
     within 25 levels; a lock screen covers everything).
  3. and the desktop still ANSWERS: a second Alt+Tab flips again
     (a locked screen would swallow the key).

⚠ DECLARED: CDP and Marionette deliver the keys to the PAGE skipping the
  client's compositor and the browser's accelerators.  What is tested
  here is the stretch page → REMOTIX → desktop; that Alt+Tab or Super, on a
  real client, are kept by the client's operating system is declared
  by the page itself (`SC_CATALOGO`, «non-consegnata») and is not F-010's.

FAULT (two, both must give red):
  A) instead of Alt+Tab only Tab is sent (the gesture without the modifier):
     the windows do not swap ⇒ the use judge must say RED;
  B) the judge of the dangerous ones is given, instead of the photo after Super+L,
     a BLACK canvas of the same size (what is seen if the screen locks
     or turns off) ⇒ it must say RED.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G1B = S._carica("g1b", os.path.join(S.QUI, "15-g1b-comune.py"))
FUNZIONI = ("F-010",)

MARGINE = 0.01          # minimum difference (fraction of the pixels) to say «on top»
TOLLERANZA_REL = 0.25   # the desktop «is still that one»: colours within 25%
TOLLERANZA_LUM = 25


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES (pure functions)
# ═══════════════════════════════════════════════════════════════════════════
def sopra(conti):
    """'ciano' | 'magenta' | None: who covers more pixels (with margin)."""
    c, m = conti[G1B.CIANO], conti[G1B.MAGENTA]
    if c < 0.01 and m < 0.01:
        return None
    if abs(c - m) < MARGINE:
        return None
    return "ciano" if c > m else "magenta"


def scambiate(prima, dopo):
    """(outcome, sentence): VERDE if whoever was on top is now below."""
    a, b = sopra(prima), sopra(dopo)
    frase = "on top before: %s (c %.3f, m %.3f) · after: %s (c %.3f, m %.3f)" % (
        a, prima[G1B.CIANO], prima[G1B.MAGENTA], b, dopo[G1B.CIANO], dopo[G1B.MAGENTA])
    if a is None:
        return S.CIECO, "before the gesture it is not clear who is on top: " + frase
    if b is None:
        return S.ROSSO, "after the gesture the windows are no longer seen: " + frase
    return (S.VERDE if a != b else S.ROSSO), frase


def ancora_li(rif, lum_rif, conti, lum):
    """(outcome, sentence): VERDE if the desktop is still the reference one."""
    guai = []
    for col, nome in ((G1B.CIANO, "ciano"), (G1B.MAGENTA, "magenta")):
        r, v = rif[col], conti[col]
        if r > 0.01 and abs(v - r) > TOLLERANZA_REL * r:
            guai.append("%s %.3f → %.3f" % (nome, r, v))
    if abs(lum - lum_rif) > TOLLERANZA_LUM:
        guai.append("luminance %.0f → %.0f" % (lum_rif, lum))
    frase = "cyan %.3f, magenta %.3f, luminance %.0f" % (
        conti[G1B.CIANO], conti[G1B.MAGENTA], lum)
    return (S.ROSSO, "the desktop is NO longer that one: " + "; ".join(guai)) if guai \
        else (S.VERDE, "the desktop is still there: " + frase)


def certifica():
    guai = []

    def prova(cosa, vero):
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
        if not vero:
            guai.append(cosa)

    C, M = G1B.CIANO, G1B.MAGENTA
    prova("real swap ⇒ VERDE", scambiate({C: 0.2, M: 0.3}, {C: 0.3, M: 0.2})[0] == S.VERDE)
    prova("no swap ⇒ ROSSO", scambiate({C: 0.2, M: 0.3}, {C: 0.2, M: 0.3})[0] == S.ROSSO)
    prova("windows vanished ⇒ ROSSO", scambiate({C: 0.2, M: 0.3}, {C: 0, M: 0})[0] == S.ROSSO)
    prova("before, not clear ⇒ CIECO",
          scambiate({C: 0.25, M: 0.255}, {C: 0.3, M: 0.2})[0] == S.CIECO)
    prova("same desktop ⇒ VERDE",
          ancora_li({C: 0.2, M: 0.3}, 120, {C: 0.21, M: 0.29}, 118)[0] == S.VERDE)
    prova("black screen ⇒ ROSSO", ancora_li({C: 0.2, M: 0.3}, 120, {C: 0, M: 0}, 0)[0] == S.ROSSO)
    prova("lock screen (colours gone, similar light) ⇒ ROSSO",
          ancora_li({C: 0.2, M: 0.3}, 120, {C: 0.0, M: 0.0}, 110)[0] == S.ROSSO)
    nero = G1B.png_nero(64, 36)
    prova("the black canvas: no cyan, no magenta",
          G1B.conta_colori(nero, (C, M)) == {C: 0.0, M: 0.0})
    print("⛔ %d problems" % len(guai) if guai else "⭐ CERTIFIED")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def guarda(s, nome):
    png, dove = G1B.foto(s, nome, scala=0.5)
    if not png:
        raise S.Bloccata("photo failed (%s): %s" % (nome, dove))
    return png, dove, G1B.conta_colori(png, (G1B.CIANO, G1B.MAGENTA)), \
        G1B.luminanza_media(png)


def corpo(o, E):
    d = o.scatola
    with S.Sessione(o, "010", E) as s:
        G1B.passo("tenant and browser ready")
        ok, m = s.entra()
        G1B.passo("inside: %s" % m[:80])
        if not ok:
            raise S.Bloccata(m)
        time.sleep(6 if d != "kde" else 10)
        geo = s.geometria()
        W, H = geo["tl"], geo["ta"]
        c, t = G1B.metti_finestra(s)
        if c != 0:
            raise S.Bloccata("the window's program cannot be written: " + t[-200:])
        lw, la = int(W * 0.60), int(H * 0.68)
        for nome, col in (("ciano", "#00ffff"), ("magenta", "#ff00ff")):
            c, t = G1B.apri_finestra(s, nome, col, lw, la)
            if c != 0:
                raise S.Bloccata("the window %s does not start: %s" % (nome, t[-200:]))
            time.sleep(5)
        G1B.passo("windows open")
        G1B.fuoco_sulla_tela(s, geo)
        if d == "gnome":
            # ⚠ GNOME is born in the overview: ESC closes it (and on the desktop does nothing)
            G1B.combinazione(s.g, ["Escape"])
            time.sleep(2)
        ev = []
        png0, p0, k0, l0 = guarda(s, "scena")
        ev.append(p0)
        if sopra(k0) is None:
            ev.append(s.salva_testo("f010-scena.txt", "cyan %.3f magenta %.3f" % (
                k0[G1B.CIANO], k0[G1B.MAGENTA])))
            raise S.Bloccata("the scene is not there: the two known windows are not seen or do not "
                             "overlap (cyan %.3f, magenta %.3f)"
                             % (k0[G1B.CIANO], k0[G1B.MAGENTA]))

        G1B.passo("scene photographed")
        # 1. use
        G1B.combinazione(s.g, ["Alt", "Tab"])
        time.sleep(2.5)
        png1, p1, k1, l1 = guarda(s, "dopo-alt-tab")
        ev.append(p1)
        e1, f1 = scambiate(k0, k1)

        G1B.passo("Alt+Tab: %s" % f1)
        # 2. dangerous
        pericolose = []
        rif, lrif = k1, l1
        dopo_super = None
        for tasti, nome in ((["Super", "l"], "super-l"), (["Control", "Alt", "l"], "ctrl-alt-l")):
            G1B.combinazione(s.g, tasti)
            time.sleep(5)
            pngx, px, kx, lx = guarda(s, "dopo-" + nome)
            ev.append(px)
            if dopo_super is None:
                dopo_super = pngx
            ex, fx = ancora_li(rif, lrif, kx, lx)
            pericolose.append((nome, ex, fx))

        G1B.passo("dangerous: %s" % [p[1] for p in pericolose])
        # 3. still answers
        G1B.combinazione(s.g, ["Alt", "Tab"])
        time.sleep(2.5)
        png3, p3, k3, l3 = guarda(s, "dopo-secondo-alt-tab")
        ev.append(p3)
        e3, f3 = scambiate(rif, k3)

        righe = ["1 Alt+Tab: %s · %s" % (S.C21.NOME_ESITO[e1], f1)]
        righe += ["2 %s: %s · %s" % (n, S.C21.NOME_ESITO[e], f) for n, e, f in pericolose]
        righe += ["3 second Alt+Tab: %s · %s" % (S.C21.NOME_ESITO[e3], f3)]
        ev.append(s.salva_testo("f010-giudizi.txt", righe))
        oss = " | ".join(righe)
        atteso = ("Alt+Tab swaps the two known windows; after Super+L and Ctrl+Alt+L the "
                  "desktop is still there and a second Alt+Tab swaps them again")
        rossi = [r for r, e in zip(righe, [e1] + [p[1] for p in pericolose] + [e3])
                 if e == S.ROSSO]
        ciechi = [r for r, e in zip(righe, [e1] + [p[1] for p in pericolose] + [e3])
                  if e == S.CIECO]
        if rossi:
            E.metti("F-010", S.FAIL, " ; ".join(rossi), atteso=atteso, osservato=oss,
                    evidenze=ev)
        elif ciechi:
            E.metti("F-010", S.BLOCKED, " ; ".join(ciechi), atteso=atteso, osservato=oss,
                    evidenze=ev)
        else:
            E.metti("F-010", S.PASS, "Alt+Tab swaps (twice), Super+L and Ctrl+Alt+L "
                    "do not lock", atteso=atteso, osservato=oss, evidenze=ev)

        if o.guasto:
            # A) only Tab, without Alt
            _pa, pa, ka, _la = guarda(s, "guasto-prima-del-tab")
            G1B.combinazione(s.g, ["Tab"])
            time.sleep(2.5)
            _pb, pb, kb, _lb = guarda(s, "guasto-dopo-il-tab")
            ea, fa = scambiate(ka, kb)
            # B) the black canvas instead of the photo after Super+L
            w, h = G1B.misura_png(dopo_super)
            nero = G1B.png_nero(w, h)
            eb, fb = ancora_li(rif, lrif, G1B.conta_colori(nero, (G1B.CIANO, G1B.MAGENTA)),
                               G1B.luminanza_media(nero))
            visto = (ea == S.ROSSO) and (eb == S.ROSSO)
            E.guasto("F-010", None if ea == S.CIECO else visto,
                     "A) only Tab ⇒ %s (%s) · B) black canvas after Super+L ⇒ %s"
                     % (S.C21.NOME_ESITO[ea], fa, S.C21.NOME_ESITO[eb]),
                     evidenze=[pa, pb])


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
