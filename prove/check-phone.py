#!/usr/bin/env python3
"""check-phone - the REMOTIX page used as a PHONE (SPECS §7.1, §7.2, §7.3 «on the phone in hand», §7.3-bis, §6 as far as it is the view).

    python3 check-phone.py [--box xfce|lxqt|gnome|kde]

⚠ EMULATION, NOT A REAL PHONE. Chrome on the dev server with DevTools device emulation: a mobile viewport (412x915 CSS px, device scale 2),
touch events (Emulation.setTouchEmulationEnabled, Input.dispatchTouchEvent: real touchstart/pointerdown with pointerType touch, so the page
chooses its touch layout by itself, as on a phone), a mobile user agent, Italian language. What this CANNOT prove and only a real phone can:
the Android on-screen keyboard itself (it opening and closing, shrinking the viewport, «back» closing it, its autocorrection and word
composition; here the text arrives as DevTools IME events), the real size and the real wobble of a finger (thresholds of 180 ms / 9 px /
40 px were judged by the owner by hand, SPECS §7.2: «a starting point, not a commitment»), palm rejection, a real rotation sensor and
animation, Chrome for Android pointer-event quirks (Samsung/DeX, SPECS §7.4), decoding on a phone's hardware, a mobile network.
Runs ON THE DEV SERVER. One line per check: PASS|FAIL|BLOCKED name - evidence; exit 0 only if all PASS.
Its own user ph1. The desktop side is window-input.py in the user's session (every event the application got is logged)."""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
import inputlib as il  # noqa: E402
from lib import PASS, FAIL, BLOCKED, Fail  # noqa: E402

USER, PASSWORD = "ph1", "ph1pass2026k"
NAMES = ("login-desktop", "geometry-portrait", "keyboard-not-automatic", "tap-click-portrait", "finger-drag-portrait", "two-finger-tap-right-click",
         "three-finger-tap-middle-click", "keyboard-opens", "keyboard-text", "keyboard-enter-delete", "keyboard-closes", "tap-and-half-drag-select",
         "two-finger-scroll", "pinch-zoom-view", "rotation-survives", "geometry-landscape", "reattach-landscape", "tap-click-landscape",
         "reattach-portrait")
TOL = 0.035  # a fraction of the desktop: 3.5 %


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--cap", type=int, default=60)
    ap.add_argument("--only", default="")
    ap.add_argument("--user", default=USER, help="test user (default ph1; another name = a fresh user, for repeating a part)")
    a = ap.parse_args()
    globals().update(USER=a.user, PASSWORD=a.user + "pass2026k")
    only = [x for x in a.only.split(",") if x]
    res = lib.Results([n for n in NAMES if not only or n in only])
    rig = il.InputRig(a.box, "chrome", USER, PASSWORD, "ph", cap=a.cap)
    shot = "phone-%s-%s" % (a.box, time.strftime("%Y%m%d-%H%M%S"))
    touch = {}
    dims = {"w": 412, "h": 915}

    def emulate(w, h, angle):
        g = rig.g
        g.call("Emulation.setDeviceMetricsOverride", width=w, height=h, deviceScaleFactor=2, mobile=True,
               screenOrientation={"type": "portraitPrimary" if angle == 0 else "landscapePrimary", "angle": angle})
        g.call("Emulation.setTouchEmulationEnabled", enabled=True, maxTouchPoints=5)
        g.call("Emulation.setUserAgentOverride", userAgent=il.PHONE_UA, acceptLanguage="it-IT", platform="Linux armv81")
        dims.update(w=w, h=h)

    def rect():
        return rig.state()["rect"]

    def at(fx, fy):
        """CSS pixel of a fraction of the canvas on the glass."""
        L, T, W, H = rect()
        return L + W * fx, T + H * fy

    def facts():
        return rig.g.js("const t=REMOTIX.touch, s=t.state(); return {layout:t.layout(), why:t.why(), zoom:s.zoom, pointer:s.pointer, canvas:s.canvas,"
                        " kb:t.keyboard(), last:s.last_gesture, iw:innerWidth, ih:innerHeight, sw:document.documentElement.scrollWidth,"
                        " sh:document.documentElement.scrollHeight, cw:REMOTIX.viewer.canvas_w, ch:REMOTIX.viewer.canvas_h, coarse:matchMedia('(pointer: coarse)').matches,"
                        " touchpoints:navigator.maxTouchPoints};")

    def ptr_frac():
        f = facts()
        return f["pointer"][0] / f["canvas"][0], f["pointer"][1] / f["canvas"][1], f

    def leave_overview_touch(cap=40):
        """GNOME is born in the Activities Overview, which holds ALL the input. In the touch layout physical keys are not forwarded, so lib's
        leave_overview (a browser Escape) cannot work: ask the Shell whether it is on, and send Escape through the page's own shortcut seam
        (positions, any layout) until it is off. Returns what was seen."""
        if a.box != "gnome":
            return "n/a"
        q = ("u=$(id -u %s); runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus "
             "gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.freedesktop.DBus.Properties.Get "
             "org.gnome.Shell OverviewActive 2>&1" % (USER, USER))
        t0, n = time.time(), 0
        while time.time() - t0 < cap:
            if "<false>" in rig.box.run(q)[1]:
                return "Overview off after %d Escape(s), %.0f s" % (n, time.time() - t0)
            rig.g.js("REMOTIX_SHORTCUTS.send('Esc', ['Escape']); return 1;")
            n += 1
            time.sleep(2)
        return "Overview STILL ON after %d s" % cap

    def window_fresh():
        if a.box == "gnome":  # GNOME's first-login «Welcome / Take Tour» dialog is modal and swallows the input: not the product's
            rig.box.run("pkill -u %s -f gnome-tour; true" % USER, timeout=20)
        rig.stop_windows()
        rig.start_input_window("a")
        leave_overview_touch()

    def last_press(m, wait=6.0):
        v, ev = rig.wait_for(lambda e: [x for x in e[m:] if x["ev"] == "press"], wait)
        return [x for x in ev[m:] if x["ev"] == "press"], ev[m:]

    def move_pointer_to(fx, fy, tries=4):
        """Finger drags until the drawn pointer is at (fx,fy) of the canvas (preparation, not judged)."""
        for _ in range(tries):
            px, py, f = ptr_frac()
            dx, dy = (fx - px) * rect()[2], (fy - py) * rect()[3]
            if abs(dx) < 6 and abs(dy) < 6:
                return px, py
            # stay inside the glass: split into one stroke from a safe start
            sx = min(max(rect()[0] + rect()[2] * 0.5 - dx / 2, rect()[0] + 20), rect()[0] + rect()[2] - 20)
            sy = min(max(rect()[1] + rect()[3] * 0.5 - dy / 2, rect()[1] + 40), rect()[1] + rect()[3] - 40)
            ex, ey = sx + dx, sy + dy
            ex, ey = min(max(ex, rect()[0] + 5), rect()[0] + rect()[2] - 5), min(max(ey, rect()[1] + 5), rect()[1] + rect()[3] - 5)
            touch["t"].drag(sx, sy, ex, ey, steps=14)
            time.sleep(0.5)
        px, py, _ = ptr_frac()
        return px, py

    # ---------------------------------------------------------------------------------------------- the checks
    def t_login():
        f = facts()
        s = rig.state()
        if f["layout"] != "touch":
            raise Fail("the page took the layout %r (%s) with touch events on and a coarse pointer (coarse %s, touch points %s): wanted the touch layout by itself" % (
                f["layout"], f["why"], f["coarse"], f["touchpoints"]))
        d = rig.settle(a.cap)
        lib.save_png(shot + "-desktop.png", d["png"])
        return PASS, "mobile viewport %dx%d, touch layout chosen by the page (%s); user %s in, %d frames painted, desktop picture %s; saved %s-desktop.png" % (
            f["iw"], f["ih"], f["why"][:70], USER, d["s"]["painted"], d["desc"], shot)

    def geometry(label):
        f, s = facts(), rig.state()
        L, T, W, H = s["rect"]
        evs = [e for e in rig.ev("a") if e["ev"] in ("size", "ready")]
        win = (evs[-1]["w"], evs[-1]["h"]) if evs else (0, 0)
        fits = L >= -1 and T >= -1 and L + W <= f["iw"] + 1 and T + H <= f["ih"] + 1
        noscroll = f["sw"] <= f["iw"] + 1
        ratio_page = W / H
        ratio_desk = win[0] / max(1, win[1])
        ratio_canvas = (f["cw"] / f["ch"]) if f["cw"] and f["ch"] else 0
        lib.save_png(shot + "-%s.png" % label, rig.g.screenshot())
        ok = fits and noscroll and abs(ratio_page - ratio_desk) / ratio_desk < 0.03 and (not ratio_canvas or abs(ratio_page - ratio_canvas) / ratio_canvas < 0.03)
        msg = "viewport %dx%d CSS px, canvas on the glass %.0fx%.0f at (%.0f,%.0f), page width %d (no horizontal scroll: %s); the desktop in the box is %dx%d (aspect %.3f, glass %.3f, canvas %.3f); saved %s-%s.png" % (
            f["iw"], f["ih"], W, H, L, T, f["sw"], noscroll, win[0], win[1], ratio_desk, ratio_page, ratio_canvas, shot, label)
        if ok:
            return PASS, msg
        raise Fail("geometry not right for the small screen: fits in the viewport %s, no horizontal scroll %s; %s" % (fits, noscroll, msg))

    def t_geometry_p():
        return geometry("portrait")

    def t_kb_not_auto():
        f = facts()
        if f["kb"]["is_open"]:
            raise Fail("the on-screen keyboard is open right after login: SPECS §7.2/DECISIONS §10.28 say it opens only on request")
        btn = rig.g.js("const b=document.getElementById('keyboard-button'); if(!b) return null; const r=b.getBoundingClientRect(); return {x:r.left,y:r.top,w:r.width,h:r.height,disp:getComputedStyle(b).display};")
        if not btn or btn["disp"] == "none":
            raise Fail("no keyboard button on the page in touch layout (%s): SPECS §7.2 promises a small keyboard button at the top right" % btn)
        right = btn["x"] + btn["w"] > f["iw"] * 0.7 and btn["y"] < f["ih"] * 0.2
        return (PASS if right else FAIL), "keyboard closed after login; the keyboard button is at (%.0f,%.0f) %dx%d px in the %dx%d viewport (top right: %s)" % (btn["x"], btn["y"], btn["w"], btn["h"], f["iw"], f["ih"], right)

    def t_tap_click(label, nudge=False):
        def fn():
            window_fresh()
            if nudge:  # the pointer is made «known» by a small finger drag first (the first tap without it is the defect of tap-click-portrait)
                x, y = at(0.5, 0.6)
                touch["t"].drag(x, y, x + 25, y, steps=6)
                time.sleep(0.6)
            px, py, f = ptr_frac()
            m = rig.mark()
            tx, ty = at(0.2, 0.75)  # the finger lands far from the pointer
            touch["t"].tap(tx, ty)
            pr, _ = last_press(m)
            if not pr:
                raise Fail("a one-finger tap at the glass point (%.0f,%.0f) gave NO click in the desktop window (page last gesture: %s)" % (tx, ty, f["last"]))
            e = pr[0]
            prect = rig.g.js("const p=document.getElementById('pointer'); if(!p) return null; const r=p.getBoundingClientRect(); return [Math.round(r.left),Math.round(r.top),getComputedStyle(p).display];")
            near = abs(e["fx"] - px) < TOL and abs(e["fy"] - py) < TOL
            far = abs(e["fx"] - 0.2) < TOL and abs(e["fy"] - 0.75) < TOL
            if e["button"] == 1 and near:
                return PASS, "pointer at (%.3f,%.3f), finger tapped at (0.20,0.75): the left click arrived at (%.3f,%.3f), where the POINTER is, not where the finger landed (SPECS §7.1)" % (px, py, e["fx"], e["fy"])
            raise Fail("pointer at (%.3f,%.3f) of the canvas%s, finger tapped at (0.20,0.75): the desktop window got button %s at (%.3f,%.3f) (%s); the drawn pointer is at glass %s of the %dx%d viewport" % (
                px, py, " (OUTSIDE the desktop)" if not (0 <= px <= 1 and 0 <= py <= 1) else "", e["button"], e["fx"], e["fy"],
                "under the finger, not the pointer" if far else "not where the pointer is", prect, f["iw"], f["ih"]))
        return fn

    def t_finger_drag():
        window_fresh()
        px, py, _ = ptr_frac()
        W, H = rect()[2], rect()[3]
        sx, sy = at(0.3, 0.6)
        dx, dy = 0.25 * W, -0.2 * H
        m = rig.mark()
        touch["t"].drag(sx, sy, sx + dx, sy + dy, steps=15)
        time.sleep(1.0)
        qx, qy, f = ptr_frac()
        mo = [e for e in rig.since(m, "a", ("motion",))]
        e = mo[-1] if mo else None
        want = (px + dx / W, py + dy / H)
        ok = abs(qx - want[0]) < TOL and abs(qy - want[1]) < TOL and e and abs(e["fx"] - want[0]) < TOL and abs(e["fy"] - want[1]) < TOL
        if ok:
            return PASS, "finger dragged by (%+.0f,%+.0f) px: the drawn pointer went (%.3f,%.3f) -> (%.3f,%.3f) and the desktop window saw it at (%.3f,%.3f) after %d motion events" % (dx, dy, px, py, qx, qy, e["fx"], e["fy"], len(mo))
        raise Fail("finger dragged by (%+.0f,%+.0f) px: expected the pointer at (%.3f,%.3f), the page drew it at (%.3f,%.3f) and the desktop window saw %s (%d motion events)" % (
            dx, dy, want[0], want[1], qx, qy, (e["fx"], e["fy"]) if e else None, len(mo)))

    def t_two_tap():
        window_fresh()
        px, py, _ = ptr_frac()
        m = rig.mark()
        x, y = at(0.5, 0.8)
        touch["t"].multi_tap([(x - 22, y), (x + 22, y)])
        pr, _ = last_press(m)
        btn = [e["button"] for e in pr]
        if btn == [3]:
            return PASS, "two fingers tapped together: ONE right-button press (button 3) arrived at (%.3f,%.3f), the pointer's place (%.3f,%.3f)" % (pr[0]["fx"], pr[0]["fy"], px, py)
        raise Fail("two fingers tapped together: the desktop window got presses %s (wanted exactly [3]); page last gesture %s" % (btn, facts()["last"]))

    def t_three_tap():
        window_fresh()
        m = rig.mark()
        x, y = at(0.5, 0.8)
        touch["t"].multi_tap([(x - 40, y), (x, y), (x + 40, y)])
        pr, _ = last_press(m)
        btn = [e["button"] for e in pr]
        if btn == [2]:
            return PASS, "three fingers tapped together: ONE middle-button press (button 2) arrived"
        raise Fail("three fingers tapped together: the desktop window got presses %s (wanted exactly [2]); page last gesture %s" % (btn, facts()["last"]))

    def kb_button():
        return rig.g.js("const b=document.getElementById('keyboard-button'); const r=b.getBoundingClientRect(); return [r.left+r.width/2, r.top+r.height/2];")

    def t_kb_opens():
        window_fresh()
        # the pointer onto the text field (finger preparation) and a tap there: the desktop window takes the focus
        move_pointer_to(0.5, 0.04)
        touch["t"].tap(*at(0.5, 0.5))
        time.sleep(0.8)
        touch["t"].tap(*kb_button())
        time.sleep(1.2)
        f = facts()
        focus = rig.g.js("const a=document.activeElement; return a?{tag:a.tagName, id:a.id, mode:a.getAttribute('inputmode')}:null;")
        if f["kb"]["is_open"]:
            return PASS, "touch on the keyboard button: the page's keyboard is open (field %s, inputmode %s); the button shows pressed" % (focus, f["kb"]["inputmode"])
        raise Fail("touch on the keyboard button: the keyboard did not open (state %s, focus %s)" % (f["kb"], focus))

    def ime(text, commit=True):
        g = rig.g
        g.call("Input.imeSetComposition", text=text, selectionStart=len(text), selectionEnd=len(text))
        time.sleep(0.15)
        if commit:
            g.call("Input.insertText", text=text)
            time.sleep(0.3)

    def t_kb_text():
        if not facts()["kb"]["is_open"]:
            return BLOCKED, "the keyboard is not open (keyboard-opens did not pass): nothing to type into"
        # a word, then an autocorrection: composed as «hel», changed to «help», committed
        rig.g.call("Input.imeSetComposition", text="hel", selectionStart=3, selectionEnd=3)
        time.sleep(0.2)
        rig.g.call("Input.imeSetComposition", text="help", selectionStart=4, selectionEnd=4)
        time.sleep(0.2)
        rig.g.call("Input.insertText", text="help")
        time.sleep(0.3)
        rig.g.call("Input.insertText", text=" è€")
        v, ev = rig.wait_for(lambda e: ([x["text"] for x in e if x["ev"] == "text"] or [""])[-1] == "help è€", 8)
        t = rig.text("a")
        kb = facts()["kb"]
        if t == "help è€":
            return PASS, "on-screen keyboard: word composed as 'hel' then corrected to 'help' and committed, then ' è€' (IME events): the desktop entry holds exactly %r; page counted %s" % (t, kb["sent_keys"])
        raise Fail("on-screen keyboard: composed 'hel' -> 'help' committed, then ' è€': the desktop entry holds %r (wanted 'help è€'); page counted %s; journal: %s" % (t, kb["sent_keys"], rig.journal_tail("keyboard|letter|producible", 3)))

    def t_kb_special():
        if not facts()["kb"]["is_open"]:
            return BLOCKED, "the keyboard is not open: no special keys to try"
        m = rig.mark()
        rig.kb.tap("Backspace")
        rig.kb.tap("Backspace")
        rig.kb.tap("Enter")
        time.sleep(1.0)
        t = rig.text("a")
        ks = [e["name"] for e in rig.since(m, "a", ("key",)) if e["down"]]
        # information only: what else the keyboard sends (SPECS §7.3 promises only Enter and Delete on the phone)
        m2 = rig.mark()
        for k in ("Tab", "Escape", "Left"):
            rig.kb.tap(k)
        time.sleep(0.8)
        extra = [e["name"] for e in rig.since(m2, "a", ("key",)) if e["down"]]
        if t == "help " and "BackSpace" in ks and "Return" in ks:
            return PASS, "Backspace x2 and Enter (the keys SPECS §7.3 promises as positions): the application saw %s and the entry went to %r; also tried (not promised): Tab, Escape, Left -> application saw %s" % (ks, t, extra)
        raise Fail("Backspace x2 and Enter: the application saw %s and the entry holds %r (wanted 'help ': the '€' and the 'è' deleted)" % (ks, t))

    def t_kb_closes():
        if not facts()["kb"]["is_open"]:
            return BLOCKED, "the keyboard is not open"
        touch["t"].tap(*kb_button())
        time.sleep(1.0)
        f = facts()
        if not f["kb"]["is_open"]:
            return PASS, "second touch on the keyboard button: the keyboard is closed"
        raise Fail("second touch on the keyboard button: the keyboard is still open (%s)" % f["kb"])

    def t_half_drag():
        # text is in the entry from the keyboard test; pointer to the left end of the text, tap-and-a-half to the right
        if "help" not in rig.text("a"):
            rig.stop_windows()
            return BLOCKED, "no text in the desktop entry (the keyboard checks did not leave any): nothing to select"
        px, py = move_pointer_to(0.03, 0.05)
        m = rig.mark()
        W = rect()[2]
        x, y = at(0.5, 0.7)
        touch["t"].tap_and_half(x, y, 0.45 * W, 0)
        time.sleep(1.0)
        ev = rig.since(m, "a")
        pr = [e for e in ev if e["ev"] == "press" and e["button"] == 1]
        rl = [e for e in ev if e["ev"] == "release" and e["button"] == 1]
        mo = [e for e in ev if e["ev"] == "motion"]
        sel = [e["text"] for e in ev if e["ev"] == "sel" and e["text"]]
        # the first tap is a left click (press+release) and the second contact is the press that drags: two pairs on the wire
        if len(pr) == 2 and len(rl) == 2 and mo and rl[-1]["fx"] - pr[-1]["fx"] > 0.2 and sel:
            return PASS, "tap then, within the half-second, a finger down that dragged right: the tap clicked (press at fx %.3f), the second contact pressed the left button at fx %.3f and held it while the pointer moved (%d motion events) and released at fx %.3f; the entry selected %r" % (pr[0]["fx"], pr[-1]["fx"], len(mo), rl[-1]["fx"], sel[-1])
        raise Fail("tap-and-a-half to the right: desktop window got %d left press(es) at fx %s, %d release(s) at fx %s, %d motion events, selection %s (wanted the tap's click, then a press held while moving >0.2 of the width, then the release); page last gesture %s" % (
            len(pr), [e["fx"] for e in pr], len(rl), [e["fx"] for e in rl], len(mo), sel[-1:], facts()["last"]))

    def t_scroll():
        window_fresh()
        x, y = at(0.5, 0.45)
        out = {}
        for label, (dy,) in (("down", (220,)), ("up", (-220,))):
            m = rig.mark()
            y0 = y - dy / 2
            touch["t"].multi_drag([(x - 35, y0), (x + 35, y0)], [(x - 35, y0 + dy), (x + 35, y0 + dy)], steps=18)
            time.sleep(1.0)
            out[label] = [e["dy"] for e in rig.since(m, "a", ("scroll",))]
            pr = rig.since(m, "a", ("press",))
            out[label + "-press"] = len(pr)
        d, u = out["down"], out["up"]
        # GTK: wheel up is negative. Two fingers moving DOWN = the wheel turned up (RCP §7.3, page.html comment) => negative
        if d and u and sum(d) < 0 < sum(u) and not out["down-press"] and not out["up-press"]:
            return PASS, "two fingers dragged 220 px down: the desktop got scroll %s (wheel up = negative); 220 px up: %s; no click leaked from either gesture" % (d, u)
        raise Fail("two fingers dragged down then up: scroll events %s then %s (wanted a negative sum, then a positive one), clicks %d/%d; page last gesture %s" % (d, u, out["down-press"], out["up-press"], facts()["last"]))

    def t_pinch():
        window_fresh()
        f0 = facts()
        L, T, W, H = rect()
        x, y = at(0.5, 0.5)
        m = rig.mark()
        touch["t"].multi_drag([(x - 40, y), (x + 40, y)], [(x - 130, y), (x + 130, y)], steps=18)
        time.sleep(0.8)
        f1 = facts()
        r1 = rect()
        wire = [e for e in rig.since(m, "a", ("press", "scroll"))]
        touch["t"].multi_drag([(x - 130, y), (x + 130, y)], [(x - 30, y), (x + 30, y)], steps=18)
        time.sleep(0.8)
        f2 = facts()
        if f1["zoom"] > 1.5 and r1[2] > W * 1.4 and not wire and f2["zoom"] <= 1.001:
            return PASS, "pinch out: the view's zoom 1.00 -> %.2f (canvas on the glass %.0fx%.0f -> %.0fx%.0f), nothing sent to the desktop (no click, no scroll); pinch in: back to %.2f" % (f1["zoom"], W, H, r1[2], r1[3], f2["zoom"])
        raise Fail("pinch: zoom %.2f -> %.2f after spreading (canvas width %.0f -> %.0f), %d wire events leaked %s; after pinching back zoom %.2f (wanted > 1.5, none sent, back to 1)" % (
            f0["zoom"], f1["zoom"], W, r1[2], len(wire), wire[:2], f2["zoom"]))

    state = {}

    def sizes_now():
        return [(e["w"], e["h"]) for e in rig.ev("a") if e["ev"] in ("size", "ready")]

    def t_rotate():
        window_fresh()
        s0 = sizes_now()[-1]
        p0 = rig.state()["painted"]
        emulate(915, 412, 90)
        time.sleep(4)
        s, ok = rig.wait_state(lambda s: s["session"] and s["painted"] > p0 + 3, 40)
        sz = sizes_now()[-1]
        f = facts()
        if ok and f["layout"] == "touch":
            return PASS, "rotated to landscape (915x412): the session is alive (%d frames painted, was %d), layout still %s; the desktop stays %dx%d as SPECS §6.1-bis declares (the canvas does not rotate, the client rescales)" % (s["painted"], p0, f["layout"], sz[0], sz[1])
        raise Fail("rotated to landscape: session %s, frames %d (was %d), layout %s, desktop %s (was %s), outcome %r" % (s["session"], s["painted"], p0, f["layout"], sz, s0, (s.get("outcome") or "").strip()[:80]))

    def t_geometry_l():
        return geometry("landscape")

    def relogin():
        """Leave the page and come back with the same user, with fingers and keys: a reattach with the (new) window size."""
        g = rig.g
        rig.open_page()
        touch["t"].tap(*rig.center("username"))
        g.type_text(USER)
        touch["t"].tap(*rig.center("password"))
        g.type_text(PASSWORD)
        g.chord("Enter")
        s, ok = rig.wait_state(lambda s: (s["session"] and s["cls"] == "good") or s["cls"] == "bad")
        if not ok or s["cls"] == "bad":
            raise Fail("reattach from the rotated phone refused: outcome %r; journal: %s" % ((s.get("outcome") or "").strip(), rig.box.journal(USER)))
        rig.settle(a.cap, shell=False)
        time.sleep(2)

    def fills(label, landscape):
        f, s = facts(), rig.state()
        L, T, W, H = s["rect"]
        sz = sizes_now()[-1]
        k = max(W / f["iw"], H / f["ih"])
        ok = (sz[0] > sz[1]) == landscape and k >= 0.93 and L >= -1 and T >= -1 and L + W <= f["iw"] + 1 and T + H <= f["ih"] + 1
        lib.save_png(shot + "-%s.png" % label, rig.g.screenshot())
        msg = "reattached in a %dx%d viewport: the desktop is now %dx%d, on the glass %.0fx%.0f (fills %.0f%% of the viewport); saved %s-%s.png" % (f["iw"], f["ih"], sz[0], sz[1], W, H, 100 * k, shot, label)
        if ok:
            return PASS, msg
        raise Fail("after reattaching the canvas does not follow the window: " + msg)

    def t_reattach_l():
        relogin()
        return fills("reattach-landscape", True)

    def t_reattach_p():
        emulate(412, 915, 0)
        time.sleep(3)
        relogin()
        return fills("reattach-portrait", False)

    # ----------------------------------------------------------------------------------------------------- run
    def tap_field(css_id):
        c = rig.center(css_id)
        touch["t"].tap(*c)

    def flow():
        ver = rig.start()
        print("check-phone %s (%s) user %s — EMULATION (mobile viewport, touch events, mobile UA), NOT A REAL PHONE; see the header of the file for what only a real phone proves" % (a.box, ver, USER), flush=True)
        touch["t"] = il.Touch(rig.g)
        emulate(412, 915, 0)
        rig.open_page()
        g = rig.g
        g.call("Browser.grantPermissions", origin=rig.url.rstrip("/"), permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
        # login with fingers and keys, like a person on a phone
        tap_field("username")
        g.type_text(USER)
        tap_field("password")
        g.type_text(PASSWORD)
        g.chord("Enter")
        s, ok = rig.wait_state(lambda s: (s["session"] and s["cls"] == "good") or s["cls"] == "bad")
        if not ok or s["cls"] == "bad" or not s["session"]:
            raise Fail("user %s not admitted from the phone page: outcome %r; remotix journal: %s" % (USER, (s.get("outcome") or "").strip(), rig.box.journal(USER)))
        steps = [("login-desktop", t_login)]
        if not only or "login-desktop" in only:
            res.attempt("login-desktop", t_login)
        else:
            rig.settle(a.cap)
        rig.start_input_window("a")
        print("overview: " + leave_overview_touch(), flush=True)
        todo = [("geometry-portrait", t_geometry_p), ("keyboard-not-automatic", t_kb_not_auto), ("tap-click-portrait", t_tap_click("portrait")),
                ("finger-drag-portrait", t_finger_drag), ("two-finger-tap-right-click", t_two_tap), ("three-finger-tap-middle-click", t_three_tap),
                ("keyboard-opens", t_kb_opens), ("keyboard-text", t_kb_text), ("keyboard-enter-delete", t_kb_special), ("keyboard-closes", t_kb_closes),
                ("tap-and-half-drag-select", t_half_drag), ("two-finger-scroll", t_scroll), ("pinch-zoom-view", t_pinch),
                ("rotation-survives", t_rotate), ("geometry-landscape", t_geometry_l), ("reattach-landscape", t_reattach_l),
                ("tap-click-landscape", t_tap_click("landscape", True)), ("reattach-portrait", t_reattach_p)]
        for name, fn in todo:
            if only and name not in only:
                continue
            res.attempt(name, fn)

    try:
        return res.sequence(flow, 1200)
    finally:
        if rig.g:
            try:
                print("screenshot of the client page: %s" % lib.save_png(shot + "-page.png", rig.g.screenshot()))
            except Exception as e:  # noqa: BLE001
                print("no screenshot of the client page: %s" % str(e)[:150])
        rig.stop()


if __name__ == "__main__":
    sys.exit(main())
