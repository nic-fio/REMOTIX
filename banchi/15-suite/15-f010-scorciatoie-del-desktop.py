#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f010 — F-010 SCORCIATOIE DEL DESKTOP

    python3 15-f010-scorciatoie-del-desktop.py --scatola xfce --browser firefox [--guasto]

ATTESO: le scorciatoie d'USO arrivano al desktop e fanno il loro lavoro; quelle
PERICOLOSE (il blocco dello schermo) NO — lo schermo resta il desktop.

LA SCENA: nella sessione dell'inquilino due finestre NOTE, GTK4 piene di un
colore puro — CIANO e poi MAGENTA — grandi 60% x 68% del desktop, cioe' tanto
che dovunque il compositore le metta SI COPRONO (due larghezze superano il
desktop).  Hanno app_id diversi: su GNOME Alt+Tab passa fra applicazioni.

  1. d'uso: Alt+Tab (tasti VERI al browser: CDP `Input.dispatchKeyEvent` su
     Chrome, azioni W3C di Marionette su Firefox, come C23).  Dalla FOTO: la
     finestra che stava sopra (quella col colore che copre piu' pixel) passa
     sotto — il segno di (ciano - magenta) si ROVESCIA.
  2. pericolose: Super+L, poi Ctrl+Alt+L.  Dopo 5 s la foto: il desktop e'
     ancora quello (le due finestre col loro colore entro il 25%, luminanza
     entro 25 livelli; una schermata di blocco copre tutto).
  3. e il desktop RISPONDE ancora: un secondo Alt+Tab rovescia di nuovo
     (uno schermo bloccato si mangerebbe il tasto).

⚠ DICHIARATO: CDP e Marionette consegnano i tasti alla PAGINA saltando il
  compositore del cliente e gli acceleratori del browser.  Quel che si prova
  qui e' il tratto pagina → REMOTIX → desktop; che Alt+Tab o Super, su un
  cliente vero, se li tenga il sistema operativo del cliente e' dichiarato
  dalla pagina stessa (`SC_CATALOGO`, «non-consegnata») e non e' di F-010.

GUASTO (due, tutt'e due devono dare rosso):
  A) al posto di Alt+Tab si manda il solo Tab (il gesto senza il modificatore):
     le finestre non si scambiano ⇒ il giudice d'uso deve dire ROSSO;
  B) al giudice delle pericolose si da', al posto della foto dopo Super+L,
     una tela NERA della stessa misura (quel che si vede se lo schermo si
     blocca o si spegne) ⇒ deve dire ROSSO.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G1B = S._carica("g1b", os.path.join(S.QUI, "15-g1b-comune.py"))
FUNZIONI = ("F-010",)

MARGINE = 0.01          # differenza minima (frazione dei pixel) per dire «sopra»
TOLLERANZA_REL = 0.25   # il desktop «e' ancora quello»: colori entro il 25%
TOLLERANZA_LUM = 25


# ═══════════════════════════════════════════════════════════════════════════
#  I GIUDICI (funzioni pure)
# ═══════════════════════════════════════════════════════════════════════════
def sopra(conti):
    """'ciano' | 'magenta' | None: chi copre piu' pixel (con margine)."""
    c, m = conti[G1B.CIANO], conti[G1B.MAGENTA]
    if c < 0.01 and m < 0.01:
        return None
    if abs(c - m) < MARGINE:
        return None
    return "ciano" if c > m else "magenta"


def scambiate(prima, dopo):
    """(esito, frase): VERDE se chi stava sopra ora sta sotto."""
    a, b = sopra(prima), sopra(dopo)
    frase = "sopra prima: %s (c %.3f, m %.3f) · dopo: %s (c %.3f, m %.3f)" % (
        a, prima[G1B.CIANO], prima[G1B.MAGENTA], b, dopo[G1B.CIANO], dopo[G1B.MAGENTA])
    if a is None:
        return S.CIECO, "prima del gesto non si capisce chi e' sopra: " + frase
    if b is None:
        return S.ROSSO, "dopo il gesto le finestre non si vedono piu': " + frase
    return (S.VERDE if a != b else S.ROSSO), frase


def ancora_li(rif, lum_rif, conti, lum):
    """(esito, frase): VERDE se il desktop e' ancora quello del riferimento."""
    guai = []
    for col, nome in ((G1B.CIANO, "ciano"), (G1B.MAGENTA, "magenta")):
        r, v = rif[col], conti[col]
        if r > 0.01 and abs(v - r) > TOLLERANZA_REL * r:
            guai.append("%s %.3f → %.3f" % (nome, r, v))
    if abs(lum - lum_rif) > TOLLERANZA_LUM:
        guai.append("luminanza %.0f → %.0f" % (lum_rif, lum))
    frase = "ciano %.3f, magenta %.3f, luminanza %.0f" % (
        conti[G1B.CIANO], conti[G1B.MAGENTA], lum)
    return (S.ROSSO, "il desktop NON e' piu' quello: " + "; ".join(guai)) if guai \
        else (S.VERDE, "il desktop e' ancora li': " + frase)


def certifica():
    guai = []

    def prova(cosa, vero):
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
        if not vero:
            guai.append(cosa)

    C, M = G1B.CIANO, G1B.MAGENTA
    prova("scambio vero ⇒ VERDE", scambiate({C: 0.2, M: 0.3}, {C: 0.3, M: 0.2})[0] == S.VERDE)
    prova("niente scambio ⇒ ROSSO", scambiate({C: 0.2, M: 0.3}, {C: 0.2, M: 0.3})[0] == S.ROSSO)
    prova("finestre sparite ⇒ ROSSO", scambiate({C: 0.2, M: 0.3}, {C: 0, M: 0})[0] == S.ROSSO)
    prova("prima non si capisce ⇒ CIECO",
          scambiate({C: 0.25, M: 0.255}, {C: 0.3, M: 0.2})[0] == S.CIECO)
    prova("stesso desktop ⇒ VERDE",
          ancora_li({C: 0.2, M: 0.3}, 120, {C: 0.21, M: 0.29}, 118)[0] == S.VERDE)
    prova("schermo nero ⇒ ROSSO", ancora_li({C: 0.2, M: 0.3}, 120, {C: 0, M: 0}, 0)[0] == S.ROSSO)
    prova("schermata di blocco (colori spariti, luce simile) ⇒ ROSSO",
          ancora_li({C: 0.2, M: 0.3}, 120, {C: 0.0, M: 0.0}, 110)[0] == S.ROSSO)
    nero = G1B.png_nero(64, 36)
    prova("la tela nera: niente ciano, niente magenta",
          G1B.conta_colori(nero, (C, M)) == {C: 0.0, M: 0.0})
    print("⛔ %d guai" % len(guai) if guai else "⭐ CERTIFICATO")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def guarda(s, nome):
    png, dove = G1B.foto(s, nome, scala=0.5)
    if not png:
        raise S.Bloccata("fotografia fallita (%s): %s" % (nome, dove))
    return png, dove, G1B.conta_colori(png, (G1B.CIANO, G1B.MAGENTA)), \
        G1B.luminanza_media(png)


def corpo(o, E):
    d = o.scatola
    with S.Sessione(o, "010", E) as s:
        G1B.passo("inquilino e browser pronti")
        ok, m = s.entra()
        G1B.passo("dentro: %s" % m[:80])
        if not ok:
            raise S.Bloccata(m)
        time.sleep(6 if d != "kde" else 10)
        geo = s.geometria()
        W, H = geo["tl"], geo["ta"]
        c, t = G1B.metti_finestra(s)
        if c != 0:
            raise S.Bloccata("il programma della finestra non si scrive: " + t[-200:])
        lw, la = int(W * 0.60), int(H * 0.68)
        for nome, col in (("ciano", "#00ffff"), ("magenta", "#ff00ff")):
            c, t = G1B.apri_finestra(s, nome, col, lw, la)
            if c != 0:
                raise S.Bloccata("la finestra %s non parte: %s" % (nome, t[-200:]))
            time.sleep(5)
        G1B.passo("finestre aperte")
        G1B.fuoco_sulla_tela(s, geo)
        if d == "gnome":
            # ⚠ GNOME nasce nella panoramica: ESC la chiude (e sul desktop non fa niente)
            G1B.combinazione(s.g, ["Escape"])
            time.sleep(2)
        ev = []
        png0, p0, k0, l0 = guarda(s, "scena")
        ev.append(p0)
        if sopra(k0) is None:
            ev.append(s.salva_testo("f010-scena.txt", "ciano %.3f magenta %.3f" % (
                k0[G1B.CIANO], k0[G1B.MAGENTA])))
            raise S.Bloccata("la scena non c'e': le due finestre note non si vedono o non "
                             "si coprono (ciano %.3f, magenta %.3f)"
                             % (k0[G1B.CIANO], k0[G1B.MAGENTA]))

        G1B.passo("scena fotografata")
        # 1. d'uso
        G1B.combinazione(s.g, ["Alt", "Tab"])
        time.sleep(2.5)
        png1, p1, k1, l1 = guarda(s, "dopo-alt-tab")
        ev.append(p1)
        e1, f1 = scambiate(k0, k1)

        G1B.passo("Alt+Tab: %s" % f1)
        # 2. pericolose
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

        G1B.passo("pericolose: %s" % [p[1] for p in pericolose])
        # 3. risponde ancora
        G1B.combinazione(s.g, ["Alt", "Tab"])
        time.sleep(2.5)
        png3, p3, k3, l3 = guarda(s, "dopo-secondo-alt-tab")
        ev.append(p3)
        e3, f3 = scambiate(rif, k3)

        righe = ["1 Alt+Tab: %s · %s" % (S.C21.NOME_ESITO[e1], f1)]
        righe += ["2 %s: %s · %s" % (n, S.C21.NOME_ESITO[e], f) for n, e, f in pericolose]
        righe += ["3 secondo Alt+Tab: %s · %s" % (S.C21.NOME_ESITO[e3], f3)]
        ev.append(s.salva_testo("f010-giudizi.txt", righe))
        oss = " | ".join(righe)
        atteso = ("Alt+Tab scambia le due finestre note; dopo Super+L e Ctrl+Alt+L il "
                  "desktop e' ancora li' e un secondo Alt+Tab le scambia di nuovo")
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
            E.metti("F-010", S.PASS, "Alt+Tab scambia (due volte), Super+L e Ctrl+Alt+L "
                    "non bloccano", atteso=atteso, osservato=oss, evidenze=ev)

        if o.guasto:
            # A) il solo Tab, senza Alt
            _pa, pa, ka, _la = guarda(s, "guasto-prima-del-tab")
            G1B.combinazione(s.g, ["Tab"])
            time.sleep(2.5)
            _pb, pb, kb, _lb = guarda(s, "guasto-dopo-il-tab")
            ea, fa = scambiate(ka, kb)
            # B) la tela nera al posto della foto dopo Super+L
            w, h = G1B.misura_png(dopo_super)
            nero = G1B.png_nero(w, h)
            eb, fb = ancora_li(rif, lrif, G1B.conta_colori(nero, (G1B.CIANO, G1B.MAGENTA)),
                               G1B.luminanza_media(nero))
            visto = (ea == S.ROSSO) and (eb == S.ROSSO)
            E.guasto("F-010", None if ea == S.CIECO else visto,
                     "A) solo Tab ⇒ %s (%s) · B) tela nera dopo Super+L ⇒ %s"
                     % (S.C21.NOME_ESITO[ea], fa, S.C21.NOME_ESITO[eb]),
                     evidenze=[pa, pb])


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
