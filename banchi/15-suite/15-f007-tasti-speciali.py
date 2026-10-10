#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f007 — F-007 KEYBOARD: CHARACTERS AND SPECIAL KEYS inside an application

    python3 15-f007-tasti-speciali.py --scatola xfce --browser firefox [--guasto]

In the session runs the known scene of `15-g2-scena.py` (firefox-esr --kiosk):
a multi-line field «a» and, after it, a single-line field «b» (Esc empties it:
it is the APPLICATION's behaviour).  With REAL browser KEYS
(Marionette / CDP) on the REMOTIX canvas we type:

    «uno» Enter «dxe» Backspace Backspace «ue»          a = «uno⏎due»
    Left×3 «X» · Up «Y» · Down «Z»                      a = «uYno⏎XdZue»
    Tab «tre» Esc «fine»                                b = «fine»

expected: a = «uYno\\nXdZue», b = «fine».  Every special key leaves a mark
in the value: without Enter there is no second line, without Backspace «dxe» stays,
without arrows the letters end up at the end, without Tab «trefine» ends up in «a»,
without Esc b = «trefine».  ⭐ The expectation is not written by hand: `simula()`
computes it from the sequence, and `--certifica` checks that REMOVING any
special key changes the value (no key is decorative).
The judgment: the values of the two fields READ IN THE SESSION (the remote page
writes them in its notebook); the photo of the canvas is saved as evidence.

FAULT (--guasto, same session): the same sequence WITHOUT the Esc (a key
not sent) judged with the same expectation ⇒ it must give red.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G2 = S._carica("g2scena", os.path.join(S.QUI, "15-g2-scena.py"))

FUNZIONI = ("F-007",)
P = G2.premi
SEQUENZA = (G2.scrivi("uno") + P("Enter") + G2.scrivi("dxe") + P("Backspace") * 2
            + G2.scrivi("ue") + P("ArrowLeft") * 3 + G2.scrivi("X") + P("ArrowUp")
            + G2.scrivi("Y") + P("ArrowDown") + G2.scrivi("Z") + P("Tab") + G2.scrivi("tre")
            + P("Escape") + G2.scrivi("fine"))
SPECIALI_PROVATI = ("Enter", "Backspace", "ArrowLeft", "ArrowUp", "ArrowDown", "Tab", "Escape")
GUASTO_TOGLIE = "Escape"
ATTESA_S = 8.0


def senza(passi, nome):
    return [p for p in passi if p[1] != nome]


# ═══════════════════════════════════════════════════════════════════════════
#  THE FAKE FIELD — the semantics of the scene (textarea «a» and input «b»)
# ═══════════════════════════════════════════════════════════════════════════
def simula(passi):
    """Applies the steps to the fake scene; returns (a, b)."""
    val = {"a": "", "b": ""}
    pos = {"a": 0, "b": 0}
    col_mem = None
    f = "a"
    for tipo, nome, _c, _v in passi:
        if tipo != "giu":
            continue
        v, p = val[f], pos[f]
        if nome == "Enter":
            if f == "a":
                val[f], pos[f] = v[:p] + "\n" + v[p:], p + 1
            col_mem = None
        elif nome == "Backspace":
            if p > 0:
                val[f], pos[f] = v[:p - 1] + v[p:], p - 1
            col_mem = None
        elif nome == "ArrowLeft":
            pos[f] = max(0, p - 1)
            col_mem = None
        elif nome == "ArrowRight":
            pos[f] = min(len(v), p + 1)
            col_mem = None
        elif nome in ("ArrowUp", "ArrowDown"):
            if f != "a":
                continue
            righe = v.split("\n")
            r, resto = 0, p
            while resto > len(righe[r]):
                resto -= len(righe[r]) + 1
                r += 1
            c = resto if col_mem is None else col_mem
            col_mem = c
            r2 = r - 1 if nome == "ArrowUp" else r + 1
            if r2 < 0:
                pos[f] = 0
            elif r2 >= len(righe):
                pos[f] = len(v)
            else:
                pos[f] = sum(len(x) + 1 for x in righe[:r2]) + min(c, len(righe[r2]))
        elif nome == "Tab":
            f = "b" if f == "a" else f
            col_mem = None
        elif nome == "Escape":
            if f == "b":
                val["b"], pos["b"] = "", 0
        elif len(nome) == 1:
            val[f], pos[f] = v[:p] + nome + v[p:], p + 1
            col_mem = None
    return val["a"], val["b"]


ATTESO = simula(SEQUENZA)


def giudica(st, atteso):
    st = st or {}
    a, b = st.get("a"), st.get("b")
    if a is None:
        return S.BLOCKED, "the scene did not tell the values of the fields"
    if (a, b) == atteso:
        return S.PASS, "a=%r b=%r" % (a, b)
    return S.FAIL, "a=%r b=%r instead of a=%r b=%r · keys seen in the session: %s" % (
        a, b, atteso[0], atteso[1], " ".join((st.get("tasti") or [])[-40:]))


def certifica():
    guai = []

    def prova(cosa, vero, det=""):
        print("   %s %s%s" % ("⭐ ok " if vero else "⛔ NO ", cosa, (" — " + det) if det else ""))
        if not vero:
            guai.append(cosa)
    prova("the expectation is a='uYno\\nXdZue' b='fine'", ATTESO == ("uYno\nXdZue", "fine"),
          repr(ATTESO))
    for k in SPECIALI_PROVATI:
        r = simula(senza(SEQUENZA, k))
        prova("without %s the value changes" % k, r != ATTESO, repr(r))
    prova("judge: right ⇒ PASS", giudica({"a": ATTESO[0], "b": ATTESO[1]}, ATTESO)[0]
          == S.PASS)
    rg = simula(senza(SEQUENZA, GUASTO_TOGLIE))
    prova("judge: with the fault ⇒ FAIL", giudica({"a": rg[0], "b": rg[1]}, ATTESO)[0] == S.FAIL,
          repr(rg))
    prova("judge: wrong expectation ⇒ FAIL",
          giudica({"a": ATTESO[0], "b": ATTESO[1]}, ("x", "fine"))[0] == S.FAIL)
    print("⛔ CERTIFICATION FAILED" if guai else "⭐ CERTIFIED")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
def batti(s, sc, mp, passi, nome):
    atteso = simula(passi)
    st, dove, _salt, perche = G2.batti(s, sc, mp, passi, nome,
                                       lambda q: (q.get("a"), q.get("b")) == atteso, ATTESA_S)
    return st, dove, perche


def corpo(o, E):
    with S.Sessione(o, "007", E) as s:
        sc, mp, geo, dove = G2.prepara(s, o.porte_base + 6)
        atteso_txt = "a=%r b=%r" % ATTESO
        st, foto, perche = batti(s, sc, mp, SEQUENZA, "tasti-sana")
        if perche:
            raise S.Bloccata(perche)
        e, m = giudica(st, ATTESO)
        if e == S.FAIL:
            print("   ⚠ red (%s): redoing it to confirm" % m, flush=True)
            st2, foto2, perche2 = batti(s, sc, mp, SEQUENZA, "tasti-sana-bis")
            e2, m2 = giudica(st2, ATTESO) if not perche2 else (S.BLOCKED, perche2)
            if e2 == S.PASS:
                e, m = S.PASS, "⚠ RED at the first attempt (%s), green at the second" % m
            else:
                m = "red twice: %s · %s" % (m, m2)
            foto = foto2 or foto
        E.metti("F-007", e, m, atteso=atteso_txt, osservato=m,
                evidenze=[x for x in (dove, foto, s.salva_console() if e != S.PASS else "")
                          if x])
        if o.guasto:
            passi = senza(SEQUENZA, GUASTO_TOGLIE)
            st, foto, perche = batti(s, sc, mp, passi, "tasti-guasto")
            if perche:
                E.guasto("F-007", None, perche)
            else:
                eg, mg = giudica(st, ATTESO)
                E.guasto("F-007", None if eg == S.BLOCKED else eg == S.FAIL,
                         "without %s: %s" % (GUASTO_TOGLIE, mg),
                         atteso="red (the Esc is missing: b is not emptied)", osservato=mg,
                         evidenze=[foto] if foto else [])


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
