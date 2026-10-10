#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f007 — F-007 KEYBOARD: CHARACTERS AND SPECIAL KEYS inside an application

    python3 15-f007-tasti-speciali.py --container_box xfce --browser firefox [--fault]

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
without Esc b = «trefine».  ⭐ The expectation is not written by hand: `simulate()`
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

G2 = S._load("g2scena", os.path.join(S.HERE, "15-g2-scena.py"))

FUNCTIONS = ("F-007",)
P = G2.press
SEQUENCE = (G2.put_out("uno") + P("Enter") + G2.put_out("dxe") + P("Backspace") * 2
            + G2.put_out("ue") + P("ArrowLeft") * 3 + G2.put_out("X") + P("ArrowUp")
            + G2.put_out("Y") + P("ArrowDown") + G2.put_out("Z") + P("Tab") + G2.put_out("tre")
            + P("Escape") + G2.put_out("fine"))
TRIED_SPECIALS = ("Enter", "Backspace", "ArrowLeft", "ArrowUp", "ArrowDown", "Tab", "Escape")
FAULT_REMOVES = "Escape"
WAIT_S = 8.0


def without(steps, label_name):
    return [p for p in steps if p[1] != label_name]


# ═══════════════════════════════════════════════════════════════════════════
#  THE FAKE FIELD — the semantics of the scene (textarea «a» and input «b»)
# ═══════════════════════════════════════════════════════════════════════════
def simulate(steps):
    """Applies the steps to the fake scene; returns (a, b)."""
    val = {"a": "", "b": ""}
    pos = {"a": 0, "b": 0}
    with_mem = None
    f = "a"
    for kind, label_name, _c, _v in steps:
        if kind != "down":
            continue
        v, p = val[f], pos[f]
        if label_name == "Enter":
            if f == "a":
                val[f], pos[f] = v[:p] + "\n" + v[p:], p + 1
            with_mem = None
        elif label_name == "Backspace":
            if p > 0:
                val[f], pos[f] = v[:p - 1] + v[p:], p - 1
            with_mem = None
        elif label_name == "ArrowLeft":
            pos[f] = max(0, p - 1)
            with_mem = None
        elif label_name == "ArrowRight":
            pos[f] = min(len(v), p + 1)
            with_mem = None
        elif label_name in ("ArrowUp", "ArrowDown"):
            if f != "a":
                continue
            line_list = v.split("\n")
            r, rest = 0, p
            while rest > len(line_list[r]):
                rest -= len(line_list[r]) + 1
                r += 1
            c = rest if with_mem is None else with_mem
            with_mem = c
            r2 = r - 1 if label_name == "ArrowUp" else r + 1
            if r2 < 0:
                pos[f] = 0
            elif r2 >= len(line_list):
                pos[f] = len(v)
            else:
                pos[f] = sum(len(x) + 1 for x in line_list[:r2]) + min(c, len(line_list[r2]))
        elif label_name == "Tab":
            f = "b" if f == "a" else f
            with_mem = None
        elif label_name == "Escape":
            if f == "b":
                val["b"], pos["b"] = "", 0
        elif len(label_name) == 1:
            val[f], pos[f] = v[:p] + label_name + v[p:], p + 1
            with_mem = None
    return val["a"], val["b"]


EXPECTED = simulate(SEQUENCE)


def judge(st, expected_val):
    st = st or {}
    a, b = st.get("a"), st.get("b")
    if a is None:
        return S.BLOCKED, "the scene did not tell the values of the fields"
    if (a, b) == expected_val:
        return S.PASS, "a=%r b=%r" % (a, b)
    return S.FAIL, "a=%r b=%r instead of a=%r b=%r · keys seen in the session: %s" % (
        a, b, expected_val[0], expected_val[1], " ".join((st.get("keys") or [])[-40:]))


def certify():
    troubles = []

    def prova(what, real, det=""):
        print("   %s %s%s" % ("⭐ ok " if real else "⛔ NO ", what, (" — " + det) if det else ""))
        if not real:
            troubles.append(what)
    prova("the expectation is a='uYno\\nXdZue' b='fine'", EXPECTED == ("uYno\nXdZue", "fine"),
          repr(EXPECTED))
    for k in TRIED_SPECIALS:
        r = simulate(without(SEQUENCE, k))
        prova("without %s the value changes" % k, r != EXPECTED, repr(r))
    prova("judge: right ⇒ PASS", judge({"a": EXPECTED[0], "b": EXPECTED[1]}, EXPECTED)[0]
          == S.PASS)
    rg = simulate(without(SEQUENCE, FAULT_REMOVES))
    prova("judge: with the fault ⇒ FAIL", judge({"a": rg[0], "b": rg[1]}, EXPECTED)[0] == S.FAIL,
          repr(rg))
    prova("judge: wrong expectation ⇒ FAIL",
          judge({"a": EXPECTED[0], "b": EXPECTED[1]}, ("x", "fine"))[0] == S.FAIL)
    print("⛔ CERTIFICATION FAILED" if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
def beat(s, sc, mp, steps, label_name):
    expected_val = simulate(steps)
    st, dove, _salt, reason_text = G2.beat(s, sc, mp, steps, label_name,
                                       lambda q: (q.get("a"), q.get("b")) == expected_val, WAIT_S)
    return st, dove, reason_text


def body_el(o, E):
    with S.Session(o, "007", E) as s:
        sc, mp, geo, dove = G2.prepare(s, o.base_ports + 6)
        expected_txt = "a=%r b=%r" % EXPECTED
        st, picture, reason_text = beat(s, sc, mp, SEQUENCE, "tasti-sana")
        if reason_text:
            raise S.Blocked(reason_text)
        e, m = judge(st, EXPECTED)
        if e == S.FAIL:
            print("   ⚠ red (%s): redoing it to confirm" % m, flush=True)
            st2, photo2, why2 = beat(s, sc, mp, SEQUENCE, "tasti-sana-bis")
            e2, m2 = judge(st2, EXPECTED) if not why2 else (S.BLOCKED, why2)
            if e2 == S.PASS:
                e, m = S.PASS, "⚠ RED at the first attempt (%s), green at the second" % m
            else:
                m = "red twice: %s · %s" % (m, m2)
            picture = photo2 or picture
        E.put("F-007", e, m, expected_val=expected_txt, observed=m,
                evidence=[x for x in (dove, picture, s.save_console() if e != S.PASS else "")
                          if x])
        if o.fault:
            steps = without(SEQUENCE, FAULT_REMOVES)
            st, picture, reason_text = beat(s, sc, mp, steps, "tasti-guasto")
            if reason_text:
                E.fault("F-007", None, reason_text)
            else:
                eg, mg = judge(st, EXPECTED)
                E.fault("F-007", None if eg == S.BLOCKED else eg == S.FAIL,
                         "without %s: %s" % (FAULT_REMOVES, mg),
                         expected_val="red (the Esc is missing: b is not emptied)", observed=mg,
                         evidence=[picture] if picture else [])


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify))
