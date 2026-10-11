#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f031 — F-031 TOUCH (Android): the finger moves the pointer, the tap clicks,
          the tap-and-a-half drags; the on-screen keyboard opens ONLY on request

    python3 15-f031-touch.py --box gnome --browser phone [--fault]

⭐ ONLY with the REAL phone (phase 19 §5, `benches/19-android/`): Chrome on the
user's phone, driven from the laptop.  The other browsers skip it.

The scene and the JUDGES are those of F-004 (`15-f004-the-mouse.py`, `15-g2-scene.py`):
only the gesture changes, which here is a FINGER with the trackpad model of
`SPECS.md` §7.1-7.2 (the finger drags a drawn pointer; the tap
clicks where the pointer is, not where the finger lands):

  dito-muove     a REAL finger (`adb shell input swipe`) takes the pointer to two
                 points of the BLUE block: the remote page says where it saw it
                 (F-004's «movement» judge, within 5 %)
  tocco-clic     the pointer on the GREEN button, then a REAL tap
                 (`adb shell input tap`): the counter +1, button 0
                 (F-004's «left click» judge)
  tocco-e-mezzo  the pointer on the YELLOW box, then tap and at once finger down that
                 drags right by 15 % of the page: the box moves by
                 that much (F-004's «drag» judge).
                 ⚠ This gesture goes with the DevTools protocol (`Input.dispatchTouchEvent`,
                 real touch events in Chrome Android's renderer): between the tap and the
                 second contact the page allows 300 ms (`TOUCH_THRESHOLDS.T_SEQUENCE`)
                 and two `adb shell input` commands in a row do not fit.

  tastiera      «keyboard only on request» (DECISIONI §10.28, SPECIFICHE §7.2-7.3):
                 (a) after the login and the three gestures the on-screen keyboard is NOT open;
                 (b) a REAL tap on the page's ⌨ control opens it, and a word
                     written as an on-screen keyboard writes it (composition and
                     commit, DevTools protocol) arrives in the scene's field «a»;
                 (c) a second tap on the control closes it again.
                 ⭐ The state of the keyboard is told by ANDROID (`dumpsys input_method`,
                 `mInputShown`, from the laptop's window), not by the page.

  The pointer is BROUGHT onto the targets with protocol drags (it is the
  preparation, not the gesture judged).  First of all a short real finger
  (calibration): it says where the page is on the screen and puts the page in
  touch mode, as the hand would.

FAULT (--fault, same session): every gesture IN THE VOID, with the same judge:
  dito-muove ⇒ the finger takes the pointer OUTSIDE the block · tocco-clic ⇒ the
  pointer outside the button · tocco-e-mezzo ⇒ between the tap and the second
  contact 700 ms (beyond the threshold: it is no longer a tap-and-a-half, and the box must not
  move) · tastiera ⇒ the control IN THE VOID (the tap lands 60 px left
  of the ⌨): the keyboard does not open ⇒ red.  The fault is SEEN if EVERY gesture
  gives red.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G2 = S._load("g2scena", os.path.join(S.HERE, "15-g2-scene.py"))
F4 = S._load("f004", os.path.join(S.HERE, "15-f004-the-mouse.py"))

FUNCTIONS = ("F-031",)
PHONE_ONLY = True
GESTURES = ("dito-muove", "tocco-clic", "tocco-e-mezzo", "tastiera")
PASSWORD = "prova"
FAULT_OFFSET = 60       # CSS px: the tap of the control in the void lands left of the ⌨
FINGER_POINTS = ((0.25, 0.3), (0.7, 0.6))
REAL_FINGERS_MAX = 8        # a user corrects: several short finger passes to get there (each ≤ 30 % of the canvas)
HEALTHY_PAUSE_S = 0.12      # between the tap and the second contact (page threshold 0.3 s)
FAULT_PAUSE_S = 0.7


def judge_keyboard(before, is_open, n_written, is_closed):
    """«Keyboard only on request».  `before`/`is_open`/`is_closed`: the state read from
    Android (True/False/None) before the control, after the control, after the second
    control; `n_written`: the scene's field «a» (None if not read)."""
    if before is None:
        return S.BLOCKED, "the keyboard state cannot be read (window /tastiera)"
    if before:
        return S.FAIL, ("⛔ the on-screen keyboard OPENED by itself after the login and the gestures "
                        "(the decision: only on request)")
    if is_open is None:
        return S.BLOCKED, "after the control the keyboard state cannot be read"
    if not is_open:
        return S.FAIL, "the ⌨ control did NOT open the keyboard"
    if n_written != PASSWORD:
        return S.FAIL, ("the keyboard is open, but «%s» written does NOT reach the remote desktop "
                        "(field a=%r)" % (PASSWORD, n_written))
    if is_closed is None:
        return S.BLOCKED, "after the second control the keyboard state cannot be read"
    if is_closed:
        return S.FAIL, "the second tap on the ⌨ control did NOT close the keyboard"
    return S.PASS, ("closed after the gestures; the ⌨ opens it, «%s» arrives in the remote field; the ⌨ "
                    "closes it again" % PASSWORD)


def certify():
    """The judges of the three gestures are F-004's: they are certified there.  The
    keyboard one is certified here."""
    print("   F-031 uses F-004's judges (movement, click, box): certifying them")
    r = F4.certify()
    troubles = []

    def prova(what, real):
        print("   %s %s" % ("⭐ ok " if real else "⛔ NO ", what))
        if not real:
            troubles.append(what)
    prova("keyboard: all right ⇒ PASS", judge_keyboard(False, True, PASSWORD, False)[0] == S.PASS)
    prova("keyboard: opened by itself ⇒ FAIL", judge_keyboard(True, True, PASSWORD, False)[0] == S.FAIL)
    prova("keyboard: the control in the void (does not open) ⇒ FAIL",
          judge_keyboard(False, False, "", False)[0] == S.FAIL)
    prova("keyboard: open but the word does not arrive ⇒ FAIL",
          judge_keyboard(False, True, "", False)[0] == S.FAIL)
    prova("keyboard: a different word ⇒ FAIL",
          judge_keyboard(False, True, "prov", False)[0] == S.FAIL)
    prova("keyboard: does not close again ⇒ FAIL", judge_keyboard(False, True, PASSWORD, True)[0] == S.FAIL)
    prova("keyboard: unreadable state ⇒ BLOCKED",
          judge_keyboard(None, True, PASSWORD, False)[0] == S.BLOCKED)
    print("⛔ CERTIFICATION FAILED" if troubles else "⭐ CERTIFIED (keyboard)")
    return r or (1 if troubles else 0)


def keyboard(s, sc, mp, geo, fault, note):
    """The «tastiera» gesture: see the header.  Returns (outcome, sentence)."""
    g = s.g
    before = g.keyboard_is_open()
    note.append("keyboard after the gestures: %s" % {True: "OPEN", False: "closed"}.get(before, "?"))
    if before is None or before:
        return judge_keyboard(before, None, None, None)
    # the remote desktop's focus in the field «a»: the pointer above it, a REAL tap
    R = sc.rect
    err = g.move_pointer(geo, *glass(mp, *F4.center_r(R["a"])))
    if err is None or err > 3:
        return S.BLOCKED, "the pointer cannot be brought onto the field «a» (error %s px)" % err
    if not g.real_tap(geo):
        return S.BLOCKED, "the real tap on the field «a» did not reach the page (adb tap)"
    st = sc.in_charge("fuoco-a")
    if st is None or st.get("a") != "" or st.get("focus") != "a":
        return S.BLOCKED, "the scene is not ready to write: %s" % (st,)
    k = g.command_keyboard()
    if not k:
        return S.FAIL, "the page does NOT show the ⌨ control with the phone in hand"
    x, y = (k[0] - FAULT_OFFSET, k[1]) if fault else (k[0], k[1])
    t = g.real_touch_at(x, y)
    note.append("control%s: tap on «%s»" % (" IN THE VOID" if fault else "",
                                             (t or {}).get("su", "none")))
    is_open = g.wait_keyboard(True)
    n_written = None
    is_closed = None
    try:
        if is_open:
            g.write_ime(PASSWORD)
            st = sc.wait_until(lambda q: q.get("a") == PASSWORD, F4.WAIT_S)
            n_written = (st or {}).get("a")
            k = g.command_keyboard() or k
            g.real_touch_at(k[0], k[1])
            is_closed = g.wait_keyboard(False)
    finally:
        # ⛔ the keyboard does not stay open over the later tests (the fault, the other lines)
        if g.keyboard_is_open():
            k = g.command_keyboard()
            if k:
                g.real_touch_at(k[0], k[1])
                g.wait_keyboard(False)
    return judge_keyboard(before, is_open, n_written, is_closed)


def glass(mp, x, y):
    return mp.glass(x, y)


def perform_gesture(name, s, sc, mp, geo, fault, note):
    g = s.g
    if sc.in_charge("reset") is None:
        return S.BLOCKED, "the scene did not answer the reset"
    R = sc.rect
    W, H = R["W"], R["H"]
    report = glass(mp, W * 0.33, H * 0.12)        # between the pad and the button: outside everything
    if name == "dito-muove":
        outcomes = []
        for fx, fy in FINGER_POINTS:
            expected = (fx, fy)
            tx, ty = report if fault else glass(mp, *F4.in_rect(R["pad"], fx, fy))
            st = None
            for _i in range(REAL_FINGERS_MAX):
                p = g.glass_pointer(geo)
                if p is None:
                    return S.BLOCKED, "the page does not say where the pointer is (REMOTIX.touch)"
                if max(abs(tx - p[0]), abs(ty - p[1])) <= 2:
                    break
                t = g.real_scroll(geo, tx - p[0], ty - p[1])
                if not t:
                    return S.BLOCKED, ("the real finger did not reach the page (adb swipe "
                                       "from %s by (%.0f,%.0f) px of the glass; touches seen %d)"
                                       % (getattr(g, "last_finger", None), tx - p[0], ty - p[1],
                                          len(g.touches_seen())))
                note.append("finger on «%s» at (%.0f,%.0f)" % (t.get("su"), t["x"], t["y"]))
            st = sc.wait_until(lambda q, a=expected: F4.judge_motion(q, a)[0] == S.PASS,
                            F4.WAIT_S)
            outcomes.append(F4.judge_motion(st, expected))
            if outcomes[-1][0] != S.PASS:
                break
        ugly = [e for e in outcomes if e[0] != S.PASS]
        return ugly[0] if ugly else (S.PASS, "two points: " + " · ".join(e[1] for e in outcomes))
    if name == "tocco-clic":
        tx, ty = report if fault else glass(mp, *F4.center_r(R["bot"]))
        err = g.move_pointer(geo, tx, ty)
        if err is None or err > 3:
            return S.BLOCKED, "the pointer cannot be brought onto the target (error %s px)" % err
        t = g.real_tap(geo)
        if not t:
            return S.BLOCKED, "the real tap did not reach the page (adb tap)"
        note.append("tap on «%s» at (%.0f,%.0f)" % (t.get("su"), t["x"], t["y"]))
        st = sc.wait_until(lambda q: F4.judge_click(q)[0] == S.PASS, F4.WAIT_S)
        return F4.judge_click(st)
    if name == "tocco-e-mezzo":
        x0, y0 = F4.center_r(R["box"])
        x1 = x0 + F4.PUSH * W
        a0, b0 = glass(mp, x0, y0)
        a1, _b1 = glass(mp, x1, y0)
        err = g.move_pointer(geo, a0, b0)
        if err is None or err > 3:
            return S.BLOCKED, "the pointer cannot be brought onto the box (error %s px)" % err
        d = a1 - a0
        cx, cy = g._canvas_center(geo)
        fx, fy = cx - d / 2.0, cy                 # the finger: both ends inside the canvas
        g.guard(immediately=True)
        c = g.cdp.call
        c("Input.dispatchTouchEvent", type="touchStart", touchPoints=[{"x": fx, "y": fy}])
        time.sleep(0.06)
        c("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
        time.sleep(FAULT_PAUSE_S if fault else HEALTHY_PAUSE_S)
        points = [(fx + d * i / 15.0, fy) for i in range(1, 16)]
        g.finger_cdp([(fx, fy)] + points, pause_s=0.04, keep_s=0.15)
        st = sc.wait_until(lambda q: F4.judge_box(q, x1 - x0, H)[0] == S.PASS, F4.WAIT_S)
        return F4.judge_box(st, x1 - x0, H)
    if name == "tastiera":
        return keyboard(s, sc, mp, geo, fault, note)
    raise ValueError(name)


def passed(s, sc, mp, geo, fault):
    lines = []
    for name in GESTURES:
        note = []
        try:
            e, m = perform_gesture(name, s, sc, mp, geo, fault, note)
        except S.phone().CallInProgress:
            raise
        except Exception as x:                   # noqa: BLE001
            e, m = S.BLOCKED, "the bench fell over in the gesture: %s" % str(x)[:160]
        if e == S.FAIL and not fault:
            print("   ⚠ %s red (%s): redoing it to confirm" % (name, m), flush=True)
            try:
                e2, m2 = perform_gesture(name, s, sc, mp, geo, fault, note)
            except Exception as x:               # noqa: BLE001
                e2, m2 = S.BLOCKED, "the bench fell over in the gesture: %s" % str(x)[:160]
            m = ("⚠ RED at the first attempt (%s), green at the second: %s" % (m, m2)
                 if e2 == S.PASS else "red twice: %s · %s" % (m, m2))
            e = e2
        if note:
            m += " [%s]" % "; ".join(note[-3:])
        print("   %s %-14s %s" % ({S.PASS: "⭐", S.FAIL: "⛔", S.BLOCKED: "⚠"}[e], name, m),
              flush=True)
        lines.append((name, e, m))
    return lines


def body(o, E):
    if o.browser != "phone":
        raise S.Blocked("F-031 is the REAL phone's touch: --browser phone")
    scene_port = o.base_port + 5
    with S.Session(o, "031", E) as s:
        sc, mp, geo, dove = G2.prepare(s, scene_port)
        ev = [dove] if dove else []
        tar = s.g.calibration(geo)
        if not tar:
            raise S.Blocked("the real calibration finger did not reach the page (adb swipe)")
        avail = s.g.kb_layout()
        print("   calibration: %s · layout «%s»" % (tar, avail), flush=True)
        if avail != "touch":
            why = s.g.js("return REMOTIX.touch.why ? REMOTIX.touch.why() : null")
            E.put("F-031", S.FAIL, "after a real finger the page is NOT in touch mode: «%s» "
                    "(%s)" % (avail, why), expected="touch mode (SPECIFICHE §7.2)",
                    observed=str(why), evidence=ev)
            return
        geo = s.geometry() or geo
        expected = ("the finger takes the pointer onto the BLUE where it points; the tap clicks the GREEN; "
                  "the tap-and-a-half drags the YELLOW box; the on-screen keyboard closed after the "
                  "gestures, the ⌨ opens it, «%s» arrives in the remote field, the ⌨ closes it again" % PASSWORD)
        lines = passed(s, sc, mp, geo, False)
        _p, fin = G2.photo(s, "fine-sana")
        if fin:
            ev.append(fin)
        oss = " · ".join("%s: %s %s" % r for r in lines)
        es = [r[1] for r in lines]
        if S.FAIL in es:
            E.put("F-031", S.FAIL, "red gestures: " + ", ".join(n for n, e, _m in lines
                                                                   if e == S.FAIL),
                    expected=expected, observed=oss, evidence=ev + [s.save_console()])
        elif S.BLOCKED in es:
            E.put("F-031", S.BLOCKED, "gestures not looked at: " + ", ".join(
                "%s (%s)" % (n, m) for n, e, m in lines if e == S.BLOCKED),
                expected=expected, observed=oss, evidence=ev)
        else:
            E.put("F-031", S.PASS, "four gestures out of four: the effect is there "
                    "in the application, and the keyboard opens only on request",
                    expected=expected, observed=oss, evidence=ev)
        if o.fault:
            lines = passed(s, sc, mp, geo, True)
            seen = F4.outcome_with_fault([r[1] for r in lines])
            E.fault("F-031", seen,
                     {True: "every gesture in the void gave red",
                      False: "gestures in the void GREEN anyway: " + ", ".join(
                          n for n, e, _m in lines if e == S.PASS),
                      None: "a gesture in the void could not be looked at"}[seen],
                     expected="every gesture in the void ⇒ red",
                     observed=" · ".join("%s: %s %s" % r for r in lines))


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
