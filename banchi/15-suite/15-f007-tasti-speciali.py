#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f007 — F-007 TASTIERA: CARATTERI E TASTI SPECIALI dentro un'applicazione

    python3 15-f007-tasti-speciali.py --scatola xfce --browser firefox [--guasto]

Nella sessione gira la scena nota di `15-g2-scena.py` (firefox-esr --kiosk):
un campo a piu' righe «a» e, dopo, un campo di una riga «b» (Esc lo svuota:
e' il comportamento dell'APPLICAZIONE).  Con TASTI VERI del browser
(Marionette / CDP) sulla tela di REMOTIX si batte:

    «uno» Invio «dxe» Backspace Backspace «ue»          a = «uno⏎due»
    Sinistra×3 «X» · Su «Y» · Giu' «Z»                  a = «uYno⏎XdZue»
    Tab «tre» Esc «fine»                                b = «fine»

atteso: a = «uYno\\nXdZue», b = «fine».  Ogni tasto speciale lascia un segno
nel valore: senza Invio non c'e' la seconda riga, senza Backspace resta «dxe»,
senza frecce le lettere finiscono in fondo, senza Tab «trefine» finisce in «a»,
senza Esc b = «trefine».  ⭐ L'atteso non e' scritto a mano: `simula()` lo
calcola dalla sequenza, e `--certifica` controlla che TOGLIENDO un qualunque
tasto speciale il valore cambi (nessun tasto e' decorativo).
Il giudizio: i valori dei due campi LETTI NELLA SESSIONE (la pagina remota li
scrive nel suo quaderno); la foto della tela si salva come evidenza.

GUASTO (--guasto, stessa sessione): la stessa sequenza SENZA l'Esc (un tasto
non mandato) giudicata con lo stesso atteso ⇒ deve dare rosso.
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
#  IL CAMPO FINTO — la semantica della scena (textarea «a» e input «b»)
# ═══════════════════════════════════════════════════════════════════════════
def simula(passi):
    """Applica i passi alla scena finta; torna (a, b)."""
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
        return S.BLOCKED, "la scena non ha detto i valori dei campi"
    if (a, b) == atteso:
        return S.PASS, "a=%r b=%r" % (a, b)
    return S.FAIL, "a=%r b=%r invece di a=%r b=%r · tasti visti nella sessione: %s" % (
        a, b, atteso[0], atteso[1], " ".join((st.get("tasti") or [])[-40:]))


def certifica():
    guai = []

    def prova(cosa, vero, det=""):
        print("   %s %s%s" % ("⭐ ok " if vero else "⛔ NO ", cosa, (" — " + det) if det else ""))
        if not vero:
            guai.append(cosa)
    prova("l'atteso e' a='uYno\\nXdZue' b='fine'", ATTESO == ("uYno\nXdZue", "fine"),
          repr(ATTESO))
    for k in SPECIALI_PROVATI:
        r = simula(senza(SEQUENZA, k))
        prova("senza %s il valore cambia" % k, r != ATTESO, repr(r))
    prova("giudice: giusto ⇒ PASS", giudica({"a": ATTESO[0], "b": ATTESO[1]}, ATTESO)[0]
          == S.PASS)
    rg = simula(senza(SEQUENZA, GUASTO_TOGLIE))
    prova("giudice: col guasto ⇒ FAIL", giudica({"a": rg[0], "b": rg[1]}, ATTESO)[0] == S.FAIL,
          repr(rg))
    prova("giudice: atteso sbagliato ⇒ FAIL",
          giudica({"a": ATTESO[0], "b": ATTESO[1]}, ("x", "fine"))[0] == S.FAIL)
    print("⛔ CERTIFICAZIONE FALLITA" if guai else "⭐ CERTIFICATO")
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
            print("   ⚠ rosso (%s): lo rifaccio per confermarlo" % m, flush=True)
            st2, foto2, perche2 = batti(s, sc, mp, SEQUENZA, "tasti-sana-bis")
            e2, m2 = giudica(st2, ATTESO) if not perche2 else (S.BLOCKED, perche2)
            if e2 == S.PASS:
                e, m = S.PASS, "⚠ ROSSO al primo tentativo (%s), verde al secondo" % m
            else:
                m = "rosso due volte: %s · %s" % (m, m2)
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
                         "senza %s: %s" % (GUASTO_TOGLIE, mg),
                         atteso="rosso (manca l'Esc: b non si svuota)", osservato=mg,
                         evidenze=[foto] if foto else [])


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
