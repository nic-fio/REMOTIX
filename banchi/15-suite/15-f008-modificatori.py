#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f008 — F-008 MODIFIERS AND COMBINATIONS (the C23 mesh inside the suite, widened)

    python3 15-f008-modificatori.py --container_box gnome --browser chrome [--fault]
    python3 15-f008-modificatori.py --certify

The scene is C23's — IMPORTED: `firefox-esr --kiosk` in the session with
an <input> always focused and below it the STRIP OF COLOURS, one cell per
character: the value of the field is read from the PHOTO of the canvas
(`C23.snapshot_and_read`), REAL keys given to the browser (`C23.send_it`).  For each
case: cleaning (Ctrl+A, Backspace) ⇒ empty strip; the BASE ⇒ strip =
base (if not, BLOCKED: plain typing belongs to F-007); the SEQUENCE ⇒ the expectation.

THE GROUPS (one SUITE line per pass, the groups and the cases in the fields `group_list`/`cases`):
  Maiusc+frecce        cases 1, 3, 4 of C23 (3 and 4: Shift does not stay stuck)
  Ctrl+Maiusc+frecce   case 2 of C23 (Ctrl+Shift+Left), Ctrl+Shift+Left×2,
                       Ctrl+Shift+Right (selection by word)
  Ctrl+A               selects everything, and the letter replaces it
  Ctrl+C / Ctrl+V      copy and paste INSIDE the session's application: a
                       part selected with Shift, then everything with Ctrl+A and pasted
                       twice — the pasted text is READ in the strip
The expectation of each case is also computed by `simulate()` (a fake text field,
extended from C23's: Right, Ctrl+Right, Ctrl+C, Ctrl+V), and `--certify`
checks that it matches and that the sequence with the fault gives something else.

FAULT, for each group (same session, same scene, after the healthy pass):
  Maiusc+frecce, Ctrl+Maiusc+frecce   the same sequences without Shift (`C23.no_shift`)
  Ctrl+A                              the «a» without Ctrl
  Ctrl+C / Ctrl+V                     the «c» and the «v» without Ctrl (the Ctrl+A stays)
⇒ every case must give red; a case counts only if its healthy pass was green.

⚠ Ctrl+V goes through the browser: the page, on the `paste` event, announces to the server
  the BROWSER's clipboard (src/pagina.html ~7110-7220), and the server queues
  the paste until the announcement arrives.  ⇒ The Ctrl+C/Ctrl+V case tests the whole
  chain as the user lives it: copy over there ⇒ clipboard to the browser ⇒ paste
  over there.  ⛔ The server's labwc belongs to ALL the agents: the browser's clipboard
  is shared with their tests (see the report).
"""
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G3 = S._load("g3", os.path.join(S.HERE, "15-g3-comune.py"))
C23 = G3.load_mesh("c23", "11-c23-maiusc-e-frecce-selezionano.py")
GREEN, RED, BLIND = C23.GREEN, C23.RED, C23.BLIND
FUNCTIONS = ("F-008",)

# ⭐ The widening of C23's palette and keys — it is ADDED, not copied:
#   the page (`C23.scene_page`) and the judge (`C23.color_name`) read the
#   same dictionary, so they cannot diverge.
C23.SPECIAL.setdefault("ArrowRight", ("ArrowRight", "ArrowRight", 39, "", 0))
for _l in "rtv":
    if _l not in C23.COLORS:
        _free = [c for c in C23._cube() if c not in (C23.EMPTY, C23.OTHER, C23.MARK)
                   and c not in C23.COLORS.values()][0]
        C23.COLORS[_l] = _free
        C23.ALPHABET += _l

press, put_out, clr = C23.press, C23.put_out, C23.clr


def _cc(fault, steps):
    """Ctrl held down over `steps` — or, with the fault, no Ctrl."""
    return steps if fault else clr("Control", steps)


# (group, title, base, builder(fault) ⇒ sequence, expectation)
def _da_c23(i):
    t, b, seq, a = C23.CASES[i]
    return (t, b, lambda g, seq=seq: C23.no_shift(seq) if g else seq, a)


CASES = [
    ("Maiusc+frecce",) + _da_c23(0),
    ("Maiusc+frecce",) + _da_c23(2),
    ("Maiusc+frecce",) + _da_c23(3),
    ("Ctrl+Maiusc+frecce",) + _da_c23(1),
    ("Ctrl+Maiusc+frecce", "5 Ctrl+Shift+Left×2, z", "uno due tre",
     lambda g: (clr("Control", press("ArrowLeft") * 2) if g else
                clr("Control", clr("Shift", press("ArrowLeft") * 2))) + press("z"),
     "uno z"),
    ("Ctrl+Maiusc+frecce", "6 Ctrl+Left×2, Ctrl+Shift+Right, z", "abc def",
     lambda g: clr("Control", press("ArrowLeft") * 2)
     + (clr("Control", press("ArrowRight")) if g else
        clr("Control", clr("Shift", press("ArrowRight"))))
     + press("z"),
     "z def"),
    ("Ctrl+A", "7 Ctrl+A, q", "abc de",
     lambda g: _cc(g, press("a")) + press("q"), "q"),
    ("Ctrl+C/Ctrl+V", "8 Shift+Left×3, Ctrl+C, Right, Ctrl+V", "abcdef",
     lambda g: clr("Shift", press("ArrowLeft") * 3) + _cc(g, press("c"))
     + press("ArrowRight") + _cc(g, press("v")),
     "abcdefdef"),
    ("Ctrl+C/Ctrl+V", "9 Ctrl+A, Ctrl+C, Right, Ctrl+V×2", "ab",
     lambda g: clr("Control", press("a")) + _cc(g, press("c")) + press("ArrowRight")
     + _cc(g, press("v")) + _cc(g, press("v")),
     "ababab"),
]
GROUPS = []
for _c in CASES:
    if _c[0] not in GROUPS:
        GROUPS.append(_c[0])


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def simulate(steps, value_v=""):
    """C23's fake field, widened: Right, Ctrl+Right (to the end of the word, like
    Firefox/GTK on Linux), Ctrl+C and Ctrl+V with a clipboard."""
    still = focus = len(value_v)
    down, clip = set(), ""
    for kind, label_name in steps:
        if kind == "su":
            down.discard(label_name)
            continue
        if label_name in ("Shift", "Control"):
            down.add(label_name)
            continue
        a, b = min(still, focus), max(still, focus)
        ctrl, shift = "Control" in down, "Shift" in down
        if label_name in ("ArrowLeft", "ArrowRight"):
            n = len(value_v)
            if ctrl:
                i = focus
                if label_name == "ArrowLeft":
                    while i > 0 and value_v[i - 1] == " ":
                        i -= 1
                    while i > 0 and value_v[i - 1] != " ":
                        i -= 1
                else:
                    while i < n and value_v[i] == " ":
                        i += 1
                    while i < n and value_v[i] != " ":
                        i += 1
                fresh = i
            elif not shift and a != b:
                fresh = a if label_name == "ArrowLeft" else b
            else:
                fresh = max(0, focus - 1) if label_name == "ArrowLeft" else min(n, focus + 1)
            focus = fresh
            if not shift:
                still = focus
        elif label_name == "Backspace":
            if a != b:
                value_v = value_v[:a] + value_v[b:]
                still = focus = a
            elif a > 0:
                value_v = value_v[:a - 1] + value_v[a:]
                still = focus = a - 1
        elif ctrl:
            k = label_name.lower()
            if k == "a":
                still, focus = 0, len(value_v)
            elif k == "c" and a != b:
                clip = value_v[a:b]
            elif k == "v":
                value_v = value_v[:a] + clip + value_v[b:]
                still = focus = a + len(clip)
        else:
            value_v = value_v[:a] + label_name + value_v[b:]
            still = focus = a + len(label_name)
    return value_v


def outcome_fault_group(pairs):
    """[(healthy outcome, outcome with the fault)] of a group ⇒ True seen / False / None.
    ⛔ A case counts only if its healthy pass was green."""
    if not pairs or any(s != GREEN for s, _g in pairs):
        return None
    e = C23.outcome_with_fault([g for _s, g in pairs])
    return {GREEN: True, RED: False, BLIND: None}[e]


def certify():
    r = C23.certify()
    print("\n⭐ 15-f008 · THE WIDENING")
    troubles = []

    def prova(what, real, d=""):
        print("   %s %s%s" % ("⭐ ok  " if real else "⛔ NO  ", what, (" — " + d) if d else ""))
        if not real:
            troubles.append(what)

    all_v = [C23.MARK, C23.EMPTY, C23.OTHER] + list(C23.COLORS.values())
    dmin = min(C23._dist(a, b) for i, a in enumerate(all_v) for b in all_v[i + 1:])
    prova("widened palette: %d distinct colours, minimum distance %d > 2×%d"
          % (len(set(all_v)), dmin, C23.TOLERANCE),
          len(set(all_v)) == len(all_v) and dmin > 2 * C23.TOLERANCE)
    for t, b, seq, a in C23.CASES:
        prova("widened simulate = C23's simulate on case %s" % t.split()[0],
              simulate(put_out(b) + seq) == C23.simulate(put_out(b) + seq))
    for gr, t, b, constr, a in CASES:
        healthy, gu = simulate(put_out(b) + constr(False)), simulate(put_out(b) + constr(True))
        prova("[%s] %s ⇒ %r" % (gr, t, a), healthy == a, "gives %r" % healthy)
        prova("[%s] %s with the fault ⇒ something else" % (gr, t.split()[0]), gu != a,
              "gives %r" % gu)
        prova("[%s] %s: every character has its colour, and it fits" % (gr, t.split()[0]),
              all(c in C23.COLORS for c in b + a + gu) and max(len(b), len(a), len(gu))
              <= C23.CELLS)
    geo = {"tl": 1920, "ta": 1080, "bw": 1920, "bh": 1080, "bx0": 0, "by0": 0,
           "left_side": 1.0, "sy": 1.0}
    for v in ("abcdefdef", "ababab", "uno zdue tre", "cvv", "abccv"):
        read, reason_text = C23.read_strip(C23.sampler(C23._fake_photo(v, geo), geo))
        prova("strip %r reads back" % v, read == v, "read %r %s" % (read, reason_text))
    prova("fault: healthy green, fault all red ⇒ seen",
          outcome_fault_group([(GREEN, RED), (GREEN, RED)]) is True)
    prova("fault: one comes back the same ⇒ NOT seen",
          outcome_fault_group([(GREEN, RED), (GREEN, GREEN)]) is False)
    prova("fault: healthy red ⇒ not judged",
          outcome_fault_group([(RED, RED)]) is None)
    if troubles:
        print("⛔ WIDENING NOT CERTIFIED: %d" % len(troubles))
        return 1
    print("⭐ WIDENING CERTIFIED")
    return r


# ═══════════════════════════════════════════════════════════════════════════
#  THE PASS
# ═══════════════════════════════════════════════════════════════════════════
def one_case(s, geo, grp, heading, base, seq, expected_val, label):
    """The case as `C23.observe` does it: cleaning, base, sequence, three photos."""
    g, o = s.g, s.o
    short_v = heading.split()[0]
    label_name = "%s-%s-c%s" % (o.browser, label, short_v)
    C23.send_it(g, C23.CLEAN)
    blank, pv = C23.snapshot_and_read(g, geo, "", o.store, label_name + "-0vuoto")
    if blank:
        # ⚠ `[M]` 25 Sep, kde, server under load: a lost cleaning (the field keeps
        #   the value of the previous case).  It is repeated ONCE: the cleaning is not
        #   the thing judged, and the «empty» check stays as it is.
        C23.send_it(g, C23.CLEAN)
        blank, pv = C23.snapshot_and_read(g, geo, "", o.store, label_name + "-0vuoto-bis")
    C23.send_it(g, put_out(base))
    vb, pb = C23.snapshot_and_read(g, geo, base, o.store, label_name + "-1base")
    n0 = len(C23.read_notebook(s.sc, s.chi))
    C23.send_it(g, seq)
    seen_v, pvi = C23.snapshot_and_read(g, geo, expected_val, o.store, label_name + "-2dopo")
    es, msg = C23.judge_case(heading, base, expected_val, blank, vb, seen_v)
    if es == BLIND and (blank is None or vb is None):
        msg += " — %s" % (pv or pb)
    elif seen_v is None and es != BLIND:
        es, msg = BLIND, "%s: the strip cannot be read after the sequence: %s" % (heading, pvi)
    if es == RED and not G3.scene_alive(s.sc, s.chi):
        es, msg = BLIND, ("%s: the scene DIED during the case (firefox-esr is no longer "
                          "in the session): the red is not the product's%s"
                          % (heading, G3.explain_blind(s.oom0)))
    quad = C23.read_notebook(s.sc, s.chi)[n0:]
    keys = [r[2:] for r in quad if r.startswith("K ")]
    values = [r[2:] for r in quad if r.startswith("V ")]
    print("   %s [%s] %s" % ({GREEN: "⭐", RED: "⛔", BLIND: "⚠"}[es], grp, msg), flush=True)
    if es != GREEN:
        print("        remote keydowns: %s" % " | ".join(keys)[:400], flush=True)
        print("        remote values:   %s" % " | ".join(values)[-300:], flush=True)
    return {"grp": grp, "case_v": short_v, "heading": heading, "outcome": es, "motivo": msg,
            "seen_v": seen_v, "expected_val": expected_val, "keydown_remoti": keys[-40:],
            "valori_remoti": values[-10:]}


def passed(s, geo, fault):
    results = []
    for grp, heading, base, constr, expected_val in CASES:
        r = one_case(s, geo, grp, heading, base, constr(fault), expected_val,
                    "fault" if fault else "healthy")
        results.append(r)
        blind = [x for x in results[-2:] if x["outcome"] == BLIND]
        if r["outcome"] == BLIND and (not fault or len(blind) >= 2
                                    or not G3.scene_alive(s.sc, s.chi)):
            # like C23: a blind case means the scene does not bear witness
            break
    return results


def body_el(o, E):
    with S.Session(o, "008", E) as s:
        G3.prepare_o(o, s)
        s.oom0 = G3.killed_by_server()
        sign = s.log_mark()
        ok, m = s.enter()
        if not ok:
            raise S.Blocked(m)
        geo = s.geometry()
        if not geo:
            raise S.Blocked("`REMOTIX_POINTER.geometry` is not there")
        print("   wake-up: %s" % S.C21.wake(s.g, geo), flush=True)
        port = random.randint(39400, 39499)
        ok, t = C23.turn_on_scene(s.sc, s.chi, port)
        print("   scene: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
        if not ok:
            raise S.Blocked("the scene does not start: %s" % t[-300:])
        time.sleep(3)
        x, y = S.C21.desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * 0.26)
        s.g.click(x, y)
        time.sleep(1.0)

        before = G3.evidence_now(o)
        healthy_runs = passed(s, geo, False)
        ev = G3.new_evidence(o, before)
        group_list = {}
        for gr in GROUPS:
            es = [r["outcome"] for r in healthy_runs if r["grp"] == gr]
            group_list[gr] = C23.overall_outcome(es) if es else BLIND
        overall = C23.overall_outcome(list(group_list.values()))
        male = [r["motivo"] for r in healthy_runs if r["outcome"] != GREEN]
        if overall == GREEN:
            rationale = "all %d cases add up (%s)" % (len(healthy_runs), ", ".join(GROUPS))
        else:
            rationale = "; ".join(male) or "cases not looked at: %s" % [
                g for g, e in group_list.items() if e == BLIND]
            if overall == BLIND and "OOM" not in rationale:
                rationale += G3.explain_blind(s.oom0)
        notebook = s.save_text("quaderno-scena-%s.txt" % o.browser,
                                 C23.read_notebook(s.sc, s.chi))
        try:
            pressed = s.g.js("return REMOTIX.input_classic.state().pressed_keys")
        except Exception as ex:                  # noqa: BLE001
            pressed = "? (%s)" % str(ex)[:80]
        E.put("F-008", overall, rationale,
                expected_val="; ".join("%s: %r ⇒ %r" % (c[1].split()[0], c[2], c[4]) for c in CASES),
                observed="; ".join("%s %r" % (r["case_v"], r["seen_v"]) for r in healthy_runs),
                evidence=ev + [notebook, s.save_console()],
                group_list={k: S.FROM_CODE[v] for k, v in group_list.items()},
                cases=[dict(r, outcome=S.FROM_CODE[r["outcome"]]) for r in healthy_runs],
                pressed_keys_at_end=pressed)

        if o.fault:
            print("   ── FAULT: the same sequences without each group's modifier ──",
                  flush=True)
            before = G3.evidence_now(o)
            faults = passed(s, geo, True)
            per_group = {}
            for gr in GROUPS:
                pairs = [(sa["outcome"], gu["outcome"]) for sa, gu in zip(healthy_runs, faults)
                          if sa["grp"] == gr]
                per_group[gr] = outcome_fault_group(pairs)
            v = list(per_group.values())
            seen_v = None if None in v else all(v)
            rationale = "; ".join("%s: %s" % (gr, {True: "seen", False: "NOT SEEN",
                                                  None: "not judgeable"}[x])
                                for gr, x in per_group.items())
            E.fault("F-008", seen_v, rationale,
                     expected_val="without the modifier every case gives red",
                     observed="; ".join("%s %r" % (r["case_v"], r["seen_v"]) for r in faults),
                     evidence=G3.new_evidence(o, before),
                     group_list={k: x for k, x in per_group.items()},
                     cases=[dict(r, outcome=S.FROM_CODE[r["outcome"]]) for r in faults])
        server = s.log_from(sign) if sign is not None else []
        s.save_text("server-f008.txt", server)


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify))
