#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f007 — F-007 KEYBOARD: CHARACTERS AND SPECIAL KEYS inside an application

    python3 15-f007-special-keys.py --box xfce --browser firefox [--fault]

In the session runs the known scene of `15-g2-scene.py` (firefox-esr --kiosk):
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
computes it from the sequence, and `--certify` checks that REMOVING any
special key changes the value (no key is decorative).
The judgment: the values of the two fields READ IN THE SESSION (the remote page
writes them in its notebook); the photo of the canvas is saved as evidence.

FAULT (--fault, same session): the same sequence WITHOUT the Esc (a key
not sent) judged with the same expectation ⇒ it must give red.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G2 = S._load("g2scena", os.path.join(S.HERE, "15-g2-scene.py"))

FUNCTIONS = ("F-007",)
P = G2.press
SEQUENCE = (G2.write("uno") + P("Enter") + G2.write("dxe") + P("Backspace") * 2
            + G2.write("ue") + P("ArrowLeft") * 3 + G2.write("X") + P("ArrowUp")
            + G2.write("Y") + P("ArrowDown") + G2.write("Z") + P("Tab") + G2.write("tre")
            + P("Escape") + G2.write("end"))
TRIED_SPECIALS = ("Enter", "Backspace", "ArrowLeft", "ArrowUp", "ArrowDown", "Tab", "Escape")
FAULT_REMOVES = "Escape"
WAIT_S = 8.0


def without(steps, name):
    return [p for p in steps if p[1] != name]


# ═══════════════════════════════════════════════════════════════════════════
#  THE FAKE FIELD — the semantics of the scene (textarea «a» and input «b»)
# ═══════════════════════════════════════════════════════════════════════════
def simulate(steps):
    """Applies the steps to the fake scene; returns (a, b)."""
    val = {"a": "", "b": ""}
    pos = {"a": 0, "b": 0}
    with_mem = None
    f = "a"
    for kind, name, _c, _v in steps:
        if kind != "giu":
            continue
        v, p = val[f], pos[f]
        if name == "Enter":
            if f == "a":
                val[f], pos[f] = v[:p] + "\n" + v[p:], p + 1
            with_mem = None
        elif name == "Backspace":
            if p > 0:
                val[f], pos[f] = v[:p - 1] + v[p:], p - 1
            with_mem = None
        elif name == "ArrowLeft":
            pos[f] = max(0, p - 1)
            with_mem = None
        elif name == "ArrowRight":
            pos[f] = min(len(v), p + 1)
            with_mem = None
        elif name in ("ArrowUp", "ArrowDown"):
            if f != "a":
                continue
            lines = v.split("\n")
            r, rest = 0, p
            while rest > len(lines[r]):
                rest -= len(lines[r]) + 1
                r += 1
            c = rest if with_mem is None else with_mem
            with_mem = c
            r2 = r - 1 if name == "ArrowUp" else r + 1
            if r2 < 0:
                pos[f] = 0
            elif r2 >= len(lines):
                pos[f] = len(v)
            else:
                pos[f] = sum(len(x) + 1 for x in lines[:r2]) + min(c, len(lines[r2]))
        elif name == "Tab":
            f = "b" if f == "a" else f
            with_mem = None
        elif name == "Escape":
            if f == "b":
                val["b"], pos["b"] = "", 0
        elif len(name) == 1:
            val[f], pos[f] = v[:p] + name + v[p:], p + 1
            with_mem = None
    return val["a"], val["b"]


ATTESO = simulate(SEQUENCE)


def judge(st, expected):
    st = st or {}
    a, b = st.get("a"), st.get("b")
    if a is None:
        return S.BLOCKED, "the scene did not tell the values of the fields"
    if (a, b) == expected:
        return S.PASS, "a=%r b=%r" % (a, b)
    return S.FAIL, "a=%r b=%r instead of a=%r b=%r · keys seen in the session: %s" % (
        a, b, expected[0], expected[1], " ".join((st.get("keys") or [])[-40:]))


def certify():
    troubles = []

    def prova(what, real, det=""):
        print("   %s %s%s" % ("⭐ ok " if real else "⛔ NO ", what, (" — " + det) if det else ""))
        if not real:
            troubles.append(what)
    prova("the expectation is a='uYno\\nXdZue' b='end'", ATTESO == ("uYno\nXdZue", "end"),
          repr(ATTESO))
    for k in TRIED_SPECIALS:
        r = simulate(without(SEQUENCE, k))
        prova("without %s the value changes" % k, r != ATTESO, repr(r))
    prova("judge: right ⇒ PASS", judge({"a": ATTESO[0], "b": ATTESO[1]}, ATTESO)[0]
          == S.PASS)
    rg = simulate(without(SEQUENCE, FAULT_REMOVES))
    prova("judge: with the fault ⇒ FAIL", judge({"a": rg[0], "b": rg[1]}, ATTESO)[0] == S.FAIL,
          repr(rg))
    prova("judge: wrong expectation ⇒ FAIL",
          judge({"a": ATTESO[0], "b": ATTESO[1]}, ("x", "end"))[0] == S.FAIL)
    print("⛔ CERTIFICATION FAILED" if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
def beat(s, sc, mp, steps, name):
    expected = simulate(steps)
    st, dove, _salt, why = G2.beat(s, sc, mp, steps, name,
                                       lambda q: (q.get("a"), q.get("b")) == expected, WAIT_S)
    return st, dove, why


def body(o, E):
    with S.Session(o, "007", E) as s:
        sc, mp, geo, dove = G2.prepare(s, o.base_port + 6)
        expected_txt = "a=%r b=%r" % ATTESO
        st, photo, why = beat(s, sc, mp, SEQUENCE, "tasti-sana")
        if why:
            raise S.Blocked(why)
        e, m = judge(st, ATTESO)
        if e == S.FAIL:
            print("   ⚠ red (%s): redoing it to confirm" % m, flush=True)
            st2, photo2, why2 = beat(s, sc, mp, SEQUENCE, "tasti-sana-bis")
            e2, m2 = judge(st2, ATTESO) if not why2 else (S.BLOCKED, why2)
            if e2 == S.PASS:
                e, m = S.PASS, "⚠ RED at the first attempt (%s), green at the second" % m
            else:
                m = "red twice: %s · %s" % (m, m2)
            photo = photo2 or photo
        E.put("F-007", e, m, expected=expected_txt, observed=m,
                evidence=[x for x in (dove, photo, s.save_console() if e != S.PASS else "")
                          if x])
        if o.fault:
            steps = without(SEQUENCE, FAULT_REMOVES)
            st, photo, why = beat(s, sc, mp, steps, "tasti-guasto")
            if why:
                E.fault("F-007", None, why)
            else:
                eg, mg = judge(st, ATTESO)
                E.fault("F-007", None if eg == S.BLOCKED else eg == S.FAIL,
                         "without %s: %s" % (FAULT_REMOVES, mg),
                         expected="red (the Esc is missing: b is not emptied)", observed=mg,
                         evidence=[photo] if photo else [])


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
