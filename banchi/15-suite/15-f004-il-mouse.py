#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f004 — F-004 THE MOUSE: movement, left click, right click, double click,
          drag, selection

    python3 15-f004-il-mouse.py --container_box kde --browser chrome [--fault]

In the tenant's session runs the known scene of `15-g2-scena.py`
(firefox-esr --kiosk).  Every gesture is made with REAL browser EVENTS
(Marionette / CDP) on the REMOTIX canvas, and it is judged from the EFFECT
in the remote application — the state that the remote page writes in its
notebook, and for the context menu the PHOTO:

  motion     the pointer goes to three points of the BLUE block: the remote page
                says where it saw it (fraction of the block), within 5 %
  click sinistro a click on the GREEN button: its counter +1, button 0
  click right   a right click on the background: the MAGENTA menu appears IN THE
                PHOTO with its corner where it was pressed (within 2 % of the desktop)
  doppio click   on «gamma»: the selected text is «gamma»
  trascinamento the YELLOW box grabbed and carried right by 15 % of the page:
                it moves by that much (within 10 %), not vertically
  selezione     pressed at the start of «beta», dragged to the end of «delta»:
                the selected text is «beta gamma delta»

FAULT (--fault, same session): every gesture IN THE VOID, with the same judge:
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

G2 = S._load("g2scena", os.path.join(S.HERE, "15-g2-scena.py"))

FUNCTIONS = ("F-004",)
GESTURES = ("motion", "clic-sinistro", "clic-destro", "doppio-clic", "trascinamento",
         "selezione")
PAD_POINTS = ((0.25, 0.3), (0.7, 0.6), (0.5, 0.8))
TOLL_PAD = 0.05
PUSH = 0.15            # of the page width
STEPS = 15
WAIT_S = 5.0


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure functions: (outcome, sentence)
# ═══════════════════════════════════════════════════════════════════════════
def judge_motion(st, expected_val):
    p = (st or {}).get("pad")
    if not p:
        return S.FAIL, "the remote page did not see the pointer on the BLUE block"
    d = max(abs(p[0] - expected_val[0]), abs(p[1] - expected_val[1]))
    if d <= TOLL_PAD:
        return S.PASS, "seen at (%.2f,%.2f), expected (%.2f,%.2f)" % (p[0], p[1], expected_val[0],
                                                                    expected_val[1])
    return S.FAIL, "seen at (%.2f,%.2f) instead of (%.2f,%.2f)" % (p[0], p[1], expected_val[0],
                                                                  expected_val[1])


def judge_click(st):
    st = st or {}
    if st.get("click") == 1 and st.get("clicbtn") == 0:
        return S.PASS, "the button counted 1 click with button 0"
    return S.FAIL, "the button counted %s clicks (button %s; clicks outside %s; down %s)" % (
        st.get("click"), st.get("clicbtn"), st.get("outside"), st.get("down"))


def judge_menu(block, spot, tl):
    """`block` = magenta box in the desktop (X0,Y0,X1,Y1) or None;
    `spot` = where it was pressed (desktop)."""
    if not block:
        return S.FAIL, "no MAGENTA menu in the photo"
    d = max(abs(block[0] - spot[0]), abs(block[1] - spot[1]))
    if d <= 0.02 * tl:
        return S.PASS, "menu in the photo with its corner %.0f px from the pressed point" % d
    return S.FAIL, "menu in the photo but %.0f px from the pressed point (%s vs %s)" % (
        d, [round(v) for v in block[:2]], [round(v) for v in spot])


def judge_selection(st, expected_val):
    sel = ((st or {}).get("sel") or "").strip()
    if sel == expected_val:
        return S.PASS, "selected %r" % sel
    return S.FAIL, "selected %r instead of %r" % (sel, expected_val)


def judge_box(st, expected_dx, alto):
    st = st or {}
    b = st.get("box") or [0, 0]
    if not st.get("boxn"):
        return S.FAIL, "the box was not grabbed (no release) · moved %s" % (b,)
    if abs(b[0] - expected_dx) <= 0.1 * expected_dx and abs(b[1]) <= 0.05 * alto:
        return S.PASS, "the box moved by %.0f px (expected %.0f)" % (b[0], expected_dx)
    return S.FAIL, "the box moved by %s px, expected (%.0f, 0)" % (b, expected_dx)


def outcome_with_fault(outcomes):
    if S.BLOCKED in outcomes:
        return None
    return all(e == S.FAIL for e in outcomes)


def certify():
    troubles = []

    def prova(what, real):
        print("   %s %s" % ("⭐ ok " if real else "⛔ NO ", what))
        if not real:
            troubles.append(what)
    prova("right movement ⇒ PASS", judge_motion({"pad": [0.26, 0.31]}, (0.25, 0.3))[0]
          == S.PASS)
    prova("movement elsewhere ⇒ FAIL", judge_motion({"pad": [0.7, 0.6]}, (0.25, 0.3))[0]
          == S.FAIL)
    prova("no movement ⇒ FAIL", judge_motion({"pad": None}, (0.25, 0.3))[0] == S.FAIL)
    prova("click ⇒ PASS", judge_click({"click": 1, "clicbtn": 0})[0] == S.PASS)
    prova("click outside ⇒ FAIL", judge_click({"click": 0, "outside": 1})[0] == S.FAIL)
    prova("menu at the point ⇒ PASS", judge_menu((100, 100, 500, 400), (102, 98), 3840)[0]
          == S.PASS)
    prova("menu far away ⇒ FAIL", judge_menu((900, 100, 1200, 400), (102, 98), 3840)[0]
          == S.FAIL)
    prova("no menu ⇒ FAIL", judge_menu(None, (1, 1), 3840)[0] == S.FAIL)
    prova("right selection ⇒ PASS", judge_selection({"sel": "gamma "}, "gamma")[0] == S.PASS)
    prova("empty selection ⇒ FAIL", judge_selection({"sel": ""}, "gamma")[0] == S.FAIL)
    prova("box moved ⇒ PASS", judge_box({"box": [570, 2], "boxn": 1}, 576, 2160)[0]
          == S.PASS)
    prova("box still ⇒ FAIL", judge_box({"box": [0, 0], "boxn": 0}, 576, 2160)[0] == S.FAIL)
    prova("fault: all red ⇒ seen", outcome_with_fault([S.FAIL] * 6) is True)
    prova("fault: one green ⇒ not seen", outcome_with_fault([S.FAIL, S.PASS]) is False)
    prova("fault: one blocked ⇒ None", outcome_with_fault([S.FAIL, S.BLOCKED]) is None)
    # the colour box and the straight line
    try:
        from PIL import Image, ImageDraw
        im = Image.new("RGB", (800, 450), (32, 32, 32))
        d = ImageDraw.Draw(im)
        d.rectangle([24, 18, 239, 89], fill=G2.BLUE)
        t = G2.find_color(im, G2.BLUE, step=2)
        prova("finds the blue block (%s)" % t, t and abs(t["x0"] - 24) <= 2
              and abs(t["x1"] - 240) <= 2 and t["full"] > 0.9)
    except ImportError:
        prova("PIL is there", False)
    a = G2.fit([(0, 10), (100, 210), (50, 110)])
    prova("the line through three points (%s)" % (a,), a and abs(a[0] - 2) < 1e-6 and abs(a[1] - 10) < 1e-6)
    print("⛔ CERTIFICATION FAILED" if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE GESTURES
# ═══════════════════════════════════════════════════════════════════════════
def in_rect(r, fx, fy):
    return r[0] + fx * (r[2] - r[0]), r[1] + fy * (r[3] - r[1])


def does_gesture(label_name, s, sc, mp, fault, ev):
    """Makes the gesture `label_name` (healthy or in the void) and judges it.  Returns (outcome, sentence)."""
    g = s.g
    R = sc.rect
    if sc.in_charge("reset") is None:
        return S.BLOCKED, "the scene did not answer the reset"
    R = sc.rect or R
    W, H = R["W"], R["H"]
    wallpaper = (W * 0.80, H * 0.72)          # empty: under field b, outside everything
    if label_name == "motion":
        outcomes = []
        for fx, fy in PAD_POINTS:
            x, y = in_rect(R["pad"], fx, fy)
            if fault:
                x, y = W * 0.33, H * 0.12   # between the pad and the button: off the target
            mouse_move(g, mp, x, y)
            st = sc.wait_for(lambda q, a=(fx, fy): judge_motion(q, a)[0] == S.PASS,
                            WAIT_S)
            outcomes.append(judge_motion(st, (fx, fy)))
            if outcomes[-1][0] != S.PASS:
                break
        ugly = [e for e in outcomes if e[0] != S.PASS]
        return (ugly[0] if ugly else
                (S.PASS, "three points: " + " · ".join(e[1] for e in outcomes)))
    if label_name == "clic-sinistro":
        x, y = center_r(R["bot"])
        if fault:
            x, y = W * 0.33, H * 0.12
        click(g, mp, x, y, 0)
        st = sc.wait_for(lambda q: judge_click(q)[0] == S.PASS, WAIT_S)
        return judge_click(st)
    if label_name == "clic-destro":
        x, y = wallpaper
        X, Y = mp.desktop(x, y)
        if fault:
            G2.mouse(g, [("move_to",) + mp.glass(x, y), ("pause_v", 300)])
        else:
            click(g, mp, x, y, 2)
        sc.wait_for(lambda q: bool(q.get("menu")), 3.0 if fault else WAIT_S)
        time.sleep(0.8)
        im, dove = G2.photo_pil(s, "right-%s" % ("fault" if fault else "healthy"))
        if im is None:
            return S.BLOCKED, "the photo of the menu cannot be taken: %s" % dove
        ev.append(dove)
        pw, ph = im.size
        t = G2.find_color(im, G2.MAGENTA)
        block = None
        if t and t["full"] > 0.7:
            X0, Y0 = S.C21.from_photo_to_desktop(mp.geo, pw, ph, t["x0"], t["y0"])
            X1, Y1 = S.C21.from_photo_to_desktop(mp.geo, pw, ph, t["x1"], t["y1"])
            block = (X0, Y0, X1, Y1)
        return judge_menu(block, (X, Y), mp.geo["tl"])
    if label_name == "doppio-clic":
        x, y = center_r(R["w3"])
        vx, vy = mp.glass(x, y)
        p = [("move_to", vx, vy), ("pause_v", 200), ("down", 0, 1), ("pause_v", 50), ("su", 0, 1)]
        if not fault:
            p += [("pause_v", 90), ("down", 0, 2), ("pause_v", 50), ("su", 0, 2)]
        G2.mouse(g, p)
        st = sc.wait_for(lambda q: judge_selection(q, "gamma")[0] == S.PASS,
                        WAIT_S)
        return judge_selection(st, "gamma")
    if label_name in ("trascinamento", "selezione"):
        if label_name == "trascinamento":
            x0, y0 = center_r(R["box"])
            x1, y1 = x0 + PUSH * W, y0
        else:
            cw = (R["w2"][2] - R["w2"][0]) / 4.0
            x0, y0 = R["w2"][0] + 0.25 * cw, center_r(R["w2"])[1]
            x1, y1 = R["w4"][2] - 0.25 * cw, y0
        drag(g, mp, (x0, y0), (x1, y1), press=not fault)
        if label_name == "trascinamento":
            st = sc.wait_for(lambda q: judge_box(q, x1 - x0, H)[0] == S.PASS, WAIT_S)
            return judge_box(st, x1 - x0, H)
        st = sc.wait_for(lambda q: judge_selection(q, "beta gamma delta")[0] == S.PASS,
                        WAIT_S)
        return judge_selection(st, "beta gamma delta")
    raise ValueError(label_name)


def center_r(r):
    return (r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0


def mouse_move(g, mp, x, y):
    vx, vy = mp.glass(x, y)
    G2.mouse(g, [("move_to", vx, vy), ("pause_v", 100)])


def click(g, mp, x, y, button_code):
    vx, vy = mp.glass(x, y)
    G2.mouse(g, [("move_to", vx, vy), ("pause_v", 200), ("down", button_code, 1), ("pause_v", 80),
                 ("su", button_code, 1)])


def drag(g, mp, da, a, press):
    p = [("move_to",) + mp.glass(*da), ("pause_v", 200)]
    if press:
        p += [("down", 0, 1), ("pause_v", 200)]
    for i in range(STEPS):
        f = (i + 1) / float(STEPS)
        p += [("move_to",) + mp.glass(da[0] + (a[0] - da[0]) * f, da[1] + (a[1] - da[1]) * f),
              ("pause_v", 40)]
    p += [("pause_v", 200)]
    if press:
        p += [("su", 0, 1)]
    G2.mouse(g, p)


def protected_gesture(label_name, s, sc, mp, fault, ev):
    """The gesture; a BENCH fault (the browser protocol falling over, the
    scene not answering under load) becomes BLOCKED for that gesture, and it is
    retried once before saying so."""
    last = None
    for _attempt in range(2):
        try:
            e, m = does_gesture(label_name, s, sc, mp, fault, ev)
        except Exception as x:                   # noqa: BLE001
            e, m = S.BLOCKED, "the bench fell over in the gesture: %s" % str(x)[:160]
        if e != S.BLOCKED:
            return e, m
        last = (e, m)
        time.sleep(3)
    return last


# ═══════════════════════════════════════════════════════════════════════════
def passed(s, sc, mp, fault):
    """All the gestures; returns [(gesture, outcome, sentence)]."""
    line_list = []
    for label_name in GESTURES:
        ev = []
        e, m = protected_gesture(label_name, s, sc, mp, fault, ev)
        if e == S.FAIL and not fault:
            print("   ⚠ %s red (%s): redoing it to confirm" % (label_name, m), flush=True)
            e2, m2 = protected_gesture(label_name, s, sc, mp, fault, ev)
            if e2 == S.PASS:
                m = "⚠ RED at the first attempt (%s), green at the second: %s" % (m, m2)
                e = S.PASS
            else:
                m = "red twice: %s · %s" % (m, m2)
                e = e2
        print("   %s %-14s %s" % ({S.PASS: "⭐", S.FAIL: "⛔", S.BLOCKED: "⚠"}[e], label_name, m),
              flush=True)
        line_list.append((label_name, e, m, ev))
    return line_list


def body_el(o, E):
    scene_port = o.base_ports + 5
    with S.Session(o, "004", E) as s:
        sc, mp, geo, dove = G2.prepare(s, scene_port)
        ev0 = [dove] if dove else []
        expected_val = ("movement on the BLUE block where it points, click on the GREEN counted, MAGENTA menu "
                  "where the right one is pressed, double click ⇒ «gamma», box moved, dragged "
                  "⇒ «beta gamma delta»")
        line_list = passed(s, sc, mp, False)
        _p, fin = G2.picture(s, "fine-sana")
        ev = ev0 + [x for r in line_list for x in r[3]] + ([fin] if fin else [])
        oss = " · ".join("%s: %s %s" % (n, e, m) for n, e, m, _ in line_list)
        es = [r[1] for r in line_list]
        if S.FAIL in es:
            E.put("F-004", S.FAIL, "red gestures: " + ", ".join(
                n for n, e, _m, _ in line_list if e == S.FAIL), expected_val=expected_val, observed=oss,
                evidence=ev + [s.save_console()])
        elif S.BLOCKED in es:
            E.put("F-004", S.BLOCKED, "gestures not looked at: " + ", ".join(
                "%s (%s)" % (n, m) for n, e, m, _ in line_list if e == S.BLOCKED),
                expected_val=expected_val, observed=oss, evidence=ev)
        else:
            E.put("F-004", S.PASS, "six gestures out of six: the effect is there in the application",
                    expected_val=expected_val, observed=oss, evidence=ev)
        if o.fault:
            line_list = passed(s, sc, mp, True)
            es = [r[1] for r in line_list]
            seen_v = outcome_with_fault(es)
            oss = " · ".join("%s: %s %s" % (n, e, m) for n, e, m, _ in line_list)
            E.fault("F-004", seen_v,
                     {True: "every gesture in the void gave red",
                      False: "gestures in the void GREEN anyway: " + ", ".join(
                          n for n, e, _m, _ in line_list if e == S.PASS),
                      None: "a gesture in the void could not be looked at"}[seen_v],
                     expected_val="every gesture in the void ⇒ red", observed=oss,
                     evidence=[x for r in line_list for x in r[3]])


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify))
