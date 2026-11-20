#!/usr/bin/env python3
"""check-input - INPUT FIDELITY of a running REMOTIX box (SPECS §7.1, §7.3, §7.3-bis, §5.2-bis, §9), real browser, real input.

    python3 check-input.py [--box xfce|lxqt|gnome|kde] [--browser chrome|firefox]

Runs ON THE DEV SERVER. One line per check: PASS|FAIL|BLOCKED name - evidence; exit 0 only if all PASS.
  FAIL = the product did not do what the specification says (page, server or desktop; evidence given).   BLOCKED = the tool could not look.
Its own users: in1 (Chrome), in2 (Firefox). The desktop side is window-input.py, a window in the user's session that logs EVERY event it
receives (buttons with their repeat count, wheel, every key with its modifiers, selection, focus, size): the verdicts are built on what
the APPLICATION in the box got, never on what the browser was told to send. The browser is driven by DevTools (Chrome) or WebDriver
actions (Firefox), real mouse and key events; the layout negotiated is Italian (browser language it-IT, as page.html layout() reads it).
Declared limits of the tool: DevTools and WebDriver cannot press AltGr (no AltGraph modifier): the Italian AltGr characters are sent as the
browser reports them on an Italian keyboard (the character itself), which is the page's LETTER path; the browser's pointer lock and the
operating system's own cursor are not in any screenshot (the cursor is judged by the CSS rule the page puts on the canvas, classified by its
pixels, and the picture by comparing pictures with the pointer parked in two places)."""
import argparse
import difflib
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
import inputlib as il  # noqa: E402
from lib import PASS, FAIL, BLOCKED, Fail  # noqa: E402

PW = {"in1": "in1pass2026k", "in2": "in2pass2026k"}
COMMON = ("mouse-buttons", "mouse-doubleclick", "mouse-wheel", "mouse-drag", "mouse-coordinates",
          "pointer-shape-text", "pointer-shape-arrow", "pointer-shape-edge", "edge-drag", "no-double-cursor",
          "kbd-text", "kbd-ctrl-clipboard", "kbd-shift-arrows", "kbd-alt-tab", "kbd-super", "kbd-function-keys", "kbd-repeat",
          "kbd-accents", "kbd-altgr", "kbd-not-producible", "kbd-capslock",
          "page-shortcuts-declared", "page-cad-button", "page-cad-chain")
CHROME_ONLY = ("page-keyboard-lock",)
FIREFOX_ONLY = ("clipboard-firefox-session-to-browser", "clipboard-firefox-browser-to-session")
LAST = ("page-ctrl-alt-end",)
IGNORE_KEYS = {"Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "ISO_Level3_Shift", "Meta_L", "Super_L"}


def short(d):
    return str(d)[:230]


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--browser", default="chrome", choices=("chrome", "firefox"))
    ap.add_argument("--cap", type=int, default=60)
    ap.add_argument("--only", default="", help="comma list of check names (development)")
    a = ap.parse_args()
    ff = a.browser == "firefox"
    user = "in2" if ff else "in1"
    names = list(COMMON) + list(FIREFOX_ONLY if ff else CHROME_ONLY) + list(LAST)
    only = [x for x in a.only.split(",") if x]
    res = lib.Results([n for n in names if not only or n in only])
    rig = il.InputRig(a.box, a.browser, user, PW[user], "inp", cap=a.cap)
    stamp = time.strftime("%Y%m%d-%H%M%S")
    shot = "input-%s-%s-%s" % (a.box, a.browser, stamp)

    # ----------------------------------------------------------------------------------------------------- helpers
    def P(x, y):
        return rig.px(x, y)

    def ensure(name="a", mode="input", colour=None):
        if name not in rig.logs:
            rig.start_input_window(name, mode, colour)

    def focus():
        """The keyboard goes to window a: real click on its entry."""
        rig.focus_entry("a")

    def fresh():
        """Window a alone, empty entry, focused."""
        if rig.boxname == "gnome":  # GNOME's first-login «Welcome / Take Tour» dialog is modal and swallows the input: not the product's
            rig.box.run("pkill -u %s -f gnome-tour; true" % user, timeout=20)
        if set(rig.logs) - {"a"} or "a" not in rig.logs:
            rig.stop_windows()
            rig.start_input_window("a")
        if rig.boxname == "gnome":
            rig.leave_overview()
        focus()
        if rig.text("a"):
            rig.clear_entry()

    def keys(m, name="a", down=True):
        return [e for e in rig.since(m, name, ("key",)) if e["down"] == down]

    def names_of(evs):
        return [e["name"] for e in evs]

    def journal_declared(n_chars, t0):
        """The declarations RCP.md §7.3 requires («a character is not producible with layout ...», one per character, the character itself is
        not named by design) in the logs since epoch t0: (number of lines, text). The user's own journal, not the service's."""
        out = rig.box.run("journalctl --no-pager -o cat --since @%d | grep -i 'not producible' | grep -F '[%s]' | tail -40; true" % (int(t0) - 1, user))[1]
        n = len([x for x in out.splitlines() if x.strip()])
        for x in out.splitlines():  # «N more characters not producible ...» counts N
            if "more characters" in x:
                try:
                    n += int(x.split("] ")[1].split()[0]) - 1
                except (IndexError, ValueError):
                    pass
        return n, out

    # ------------------------------------------------------------------------------------------------------ mouse
    def t_buttons():
        fresh()
        m, got = rig.mark(), {}
        for b, num in (("left", 1), ("middle", 2), ("right", 3)):
            rig.mouse.click(*P(0.5, 0.6), button=b)
        ev = rig.since(m, "a", ("press", "release"))
        pr = [e["button"] for e in ev if e["ev"] == "press"]
        re_ = [e["button"] for e in ev if e["ev"] == "release"]
        if pr == [1, 2, 3] and re_ == [1, 2, 3]:
            return PASS, "left, middle, right clicked at (0.50,0.60): the desktop window got presses %s and releases %s (1 left, 2 middle, 3 right), at (%.3f,%.3f)" % (
                pr, re_, ev[0]["fx"], ev[0]["fy"])
        raise Fail("left, middle, right clicked: the desktop window got presses %s releases %s (wanted [1,2,3] both)" % (pr, re_))

    def t_double():
        fresh()
        m = rig.mark()
        rig.mouse.click(*P(0.5, 0.6), count=2)
        pr = [(e["button"], e["n"]) for e in rig.since(m, "a", ("press",))]
        if (1, 2) in pr:
            return PASS, "double click at (0.50,0.60): the desktop window got presses %s, the second one counted as a double click (n=2)" % pr
        raise Fail("double click: the desktop window got presses %s, no press with n=2" % pr)

    def t_wheel():
        fresh()
        out = {}
        for label, dy, dx in (("up", -100, 0), ("down", 100, 0), ("left", 0, -100), ("right", 0, 100)):
            m = rig.mark()
            rig.mouse.wheel(*P(0.5, 0.6), dy=dy, dx=dx)
            out[label] = [(e["dx"], e["dy"]) for e in rig.since(m, "a", ("scroll",))]
        up, down = out["up"], out["down"]
        vert = bool(up) and all(d[1] < 0 for d in up if d[1]) and bool(down) and all(d[1] > 0 for d in down if d[1]) \
            and any(d[1] for d in up) and any(d[1] for d in down)
        horiz = out["left"] and out["right"] and any(d[0] < 0 for d in out["left"]) and any(d[0] > 0 for d in out["right"])
        if vert:
            return PASS, "wheel up -> scroll %s, down -> %s (GTK: up is negative); horizontal left -> %s right -> %s%s" % (
                up, down, out["left"], out["right"], "" if horiz else " (horizontal not as expected, not required)")
        raise Fail("wheel up gave %s, down gave %s (wanted a negative then a positive vertical scroll)" % (up, down))

    def t_drag():
        fresh()
        rig.type_into("alpha beta gamma")
        out = []
        for label, (x0, x1) in (("left to right", (0.01, 0.99)), ("right to left", (0.99, 0.01))):
            m = rig.mark()
            rig.mouse.drag(*P(x0, 0.06), *P(x1, 0.06))
            ev = rig.since(m, "a")
            pr = [e for e in ev if e["ev"] == "press"]
            rl = [e for e in ev if e["ev"] == "release"]
            mo = [e for e in ev if e["ev"] == "motion"]
            sel = [e for e in ev if e["ev"] == "sel" and e["text"]]
            full = sel[-1]["text"] if sel else ""
            ok = bool(pr) and bool(rl) and abs(pr[0]["fx"] - x0) < 0.01 and abs(rl[-1]["fx"] - x1) < 0.01 and full == "alpha beta gamma"
            out.append((label, ok, "press at fx %.3f release at fx %.3f, %d motion events, selected %r" % (
                pr[0]["fx"] if pr else -1, rl[-1]["fx"] if rl else -1, len(mo), full)))
            rig.mouse.click(*P(0.5, 0.06))
        if all(o[1] for o in out):
            return PASS, "; ".join("%s: %s" % (o[0], o[2]) for o in out)
        raise Fail("; ".join("%s: %s %s" % (o[0], "ok" if o[1] else "WRONG", o[2]) for o in out))

    def t_coordinates():
        fresh()
        pts = {"top-left": (0.003, 0.004), "top-right": (0.997, 0.004), "bottom-left": (0.003, 0.996), "bottom-right": (0.997, 0.996),
               "centre": (0.5, 0.5)}
        bad, ok = [], []
        for n, (fx, fy) in pts.items():
            m = rig.mark()
            rig.mouse.move(*P(0.5, 0.5))
            time.sleep(0.3)
            rig.mouse.move(*P(fx, fy))
            time.sleep(0.8)
            mo = rig.since(m, "a", ("motion", "leave"))
            sent = rig.g.js("return REMOTIX.classic_input.state().last_sent;")
            if not mo or mo[-1]["ev"] == "leave" or (mo and (abs(mo[-1]["fx"] - fx) * mo[-1]["w"] > 40 or abs(mo[-1]["fy"] - fy) * mo[-1]["h"] > 40)):
                if rig.boxname == "gnome":
                    rig.leave_overview()
                lib.save_png(shot + "-corner-%s.png" % n, rig.canvas_png())
                bad.append("%s: sent (%.3f,%.3f), the page's last POINTER message was %s (canvas px), but the pointer %s (picture %s-corner-%s.png)" % (
                    n, fx, fy, sent, "LEFT the application window (another desktop surface is under that spot)" if mo and mo[-1]["ev"] == "leave" else "never reached the application window", shot, n))
                continue
            e = mo[-1]
            dx, dy = abs(e["fx"] - fx) * e["w"], abs(e["fy"] - fy) * e["h"]
            (ok if dx <= 2.5 and dy <= 2.5 else bad).append("%s sent (%.3f,%.3f) seen (%.3f,%.3f) off by (%.1f,%.1f) px of %dx%d" % (n, fx, fy, e["fx"], e["fy"], dx, dy, e["w"], e["h"]))
        if bad:
            raise Fail("; ".join(bad) + " | exact: " + "; ".join(ok))
        return PASS, "all five within 2.5 px of the desktop: " + "; ".join(ok)

    # ---------------------------------------------------------------------------------------------- pointer shape
    def poll_shape(want, cap=4.0):
        t0, last = time.time(), ("?", "", {})
        while time.time() - t0 < cap:
            last = il.shape_now(rig.g)
            if last[0] in want:
                return True, last, time.time() - t0
            time.sleep(0.15)
        return False, last, time.time() - t0

    def t_shape_text():
        fresh()
        rig.mouse.move(*P(0.5, 0.6))
        time.sleep(1.5)
        rig.mouse.move(*P(0.5, 0.05))
        ok, (c, d, css), dt = poll_shape(("text",))
        if ok:
            return PASS, "pointer over the text field: the client's cursor became the TEXT cursor after %.2f s (%s); pointer mode %s" % (dt, d, css.get("mode"))
        raise Fail("pointer over the text field: after %.1f s the client's cursor is %r (%s), not the text cursor" % (dt, c, d))

    def t_shape_arrow():
        fresh()
        rig.mouse.move(*P(0.5, 0.05))
        poll_shape(("text",), 3)
        rig.mouse.move(*P(0.5, 0.6))
        ok, (c, d, css), dt = poll_shape(("arrow",))
        if ok:
            return PASS, "pointer back on the plain area: the cursor is the ARROW after %.2f s (%s)" % (dt, d)
        raise Fail("pointer on the plain area after the text field: after %.1f s the client's cursor is %r (%s), not the arrow" % (dt, c, d))

    def edge_setup():
        rig.stop_windows()
        rig.start_input_window("e", "edge", "00e0e0")
        time.sleep(1.5)
        png = rig.canvas_png()
        box = il.find_colour(png, (0, 224, 224))
        if not box or box[2] - box[0] < 100:
            lib.save_png(shot + "-edge-nowindow.png", png)
            raise lib.ToolError("the cyan edge window was not found in the picture (saved %s-edge-nowindow.png)" % shot)
        return png, box

    edge = {}

    def t_shape_edge():
        png, (x0, y0, x1, y1) = edge_setup()
        edge.update(x0=x0, y0=y0, x1=x1, y1=y1)
        L, T = rig.state()["rect"][:2]
        y = (y0 + y1) // 2
        seen, grip = [], None
        for x in range(x1 - 4, x1 + 14, 2):
            rig.mouse.move(L + x, T + y)
            time.sleep(0.45)
            c, d, _ = il.shape_now(rig.g)
            seen.append("%+d:%s" % (x - x1, c))
            if c.startswith("resize") and grip is None:
                grip = x
        edge["grip"] = grip
        lib.save_png(shot + "-edge.png", png)
        if grip is not None:
            return PASS, "scan of the right edge of the window (offset from the last cyan pixel: shape) %s: resize shape at %+d px" % (" ".join(seen), grip - x1)
        raise Fail("scan of the right edge (offset from the last cyan pixel: shape) %s: the client's cursor never became a resize shape (picture %s-edge.png)" % (" ".join(seen), shot))

    def t_edge_drag():
        if edge.get("grip") is None:
            return BLOCKED, "no resize shape was found on the edge (pointer-shape-edge): there is no grip point to drag from"
        L, T = rig.state()["rect"][:2]
        y = (edge["y0"] + edge["y1"]) // 2
        m = rig.mark("e")
        w0 = ([e["w"] for e in rig.ev("e") if e["ev"] in ("size", "ready")] or [0])[-1]
        rig.mouse.drag(L + edge["grip"], T + y, L + edge["grip"] + 150, T + y, steps=15)
        time.sleep(1.5)
        sizes = [(e["w"], e["h"]) for e in rig.since(m, "e", ("size",))]
        png = rig.canvas_png()
        box = il.find_colour(png, (0, 224, 224))
        lib.save_png(shot + "-edge-after.png", png)
        w1 = sizes[-1][0] if sizes else w0
        if sizes and w1 - w0 >= 100 and box and abs(box[0] - edge["x0"]) <= 4 and abs(box[1] - edge["y0"]) <= 4:
            return PASS, "press on the edge, drag 150 px right, release: the window grew from %d to %d px wide, left and top edges still (%s -> %s)" % (
                w0, w1, (edge["x0"], edge["y0"]), (box[0], box[1]))
        raise Fail("press on the edge, drag 150 px right: window width %d -> %s (sizes seen %s), cyan box before %s after %s (picture %s-edge-after.png)" % (
            w0, w1, sizes[-3:], (edge["x0"], edge["y0"], edge["x1"]), box, shot))

    def t_no_double():
        fresh()
        g = rig.g
        css = g.js("const p=document.getElementById('pointer'); return {pdisp:p?getComputedStyle(p).display:'none', mode:document.body.dataset.pointer,"
                   " layout:document.body.dataset.layout};")
        # the page's own drawn arrow, if shown in this mode, is hidden for the pictures: only what is IN THE VIDEO is looked at
        g.js("const p=document.getElementById('pointer'); if(p) p.style.visibility='hidden'; return 1;")
        W, H = rig.state()["rect"][2:]
        ax, ay = W * 0.5, H * 0.6
        try:
            rig.mouse.move(*P(0.12, 0.85))
            time.sleep(2.0)
            far1 = rig.canvas_png()
            rig.mouse.move(*P(0.5, 0.6))
            time.sleep(2.0)
            on1 = rig.canvas_png()
            rig.mouse.move(*P(0.12, 0.85))
            time.sleep(2.0)
            far2 = rig.canvas_png()
        finally:
            g.js("const p=document.getElementById('pointer'); if(p) p.style.visibility=''; return 1;")
        noise = il.diff_around(far1, far2, ax, ay)
        d = il.diff_around(far1, on1, ax, ay)
        d2 = il.diff_around(far2, on1, ax, ay)
        dpx = min(len(d), len(d2))
        lib.save_png(shot + "-pointer-on.png", il.crop_zoom(on1, ax, ay))
        lib.save_png(shot + "-pointer-off.png", il.crop_zoom(far1, ax, ay))
        if dpx == 0:
            return PASS, "pointer parked at (0.50,0.60) then elsewhere: the video around the tip is identical (0 px differ in 49x49, noise %d px); the client page's own mode is %r, layout %r" % (
                len(noise), css["mode"], css["layout"])
        raise Fail("pointer parked at (0.50,0.60): %d px around the tip differ from the picture without the pointer there (noise between two pictures without it: %d px; first differences (dx,dy,delta) %s): the desktop's own cursor is in the video; crops saved %s-pointer-on.png / -off.png" % (
            dpx, len(noise), (d or d2)[:5], shot))

    # --------------------------------------------------------------------------------------------------- keyboard
    def type_and_read(seq, wait=1.0):
        """seq: list of (name, mods). Types them and returns the entry text."""
        before = rig.text("a")
        for nm, mods in seq:
            rig.kb.tap(nm, mods)
        time.sleep(wait)
        t = rig.text("a")
        return t[len(before):] if t.startswith(before) else t

    def compare(expected, got):
        sm = difflib.SequenceMatcher(None, expected, got, autojunk=False)
        missing, wrong = [], []
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "delete":
                missing += list(expected[i1:i2])
            elif op in ("replace", "insert"):
                wrong.append("%r->%r" % (expected[i1:i2], got[j1:j2]))
                missing += list(expected[i1:i2])
        return missing, wrong

    def t_text():
        fresh()
        exp = "abcxyz ABCXYZ 0123456789 !\"#$%&'()*+,-./:;<=>?@[]^_{}~"
        seq = [(c, ()) for c in exp]
        t0 = time.time()
        got = type_and_read(seq, 2.0)
        if got == exp:
            return PASS, "letters, digits and punctuation typed one key at a time: the entry holds exactly %r" % got
        missing, wrong = compare(exp, got)
        n_decl, lines = journal_declared(len(missing), t0)
        if wrong:
            raise Fail("typed %r, the application got %r: different characters %s (missing %s; declaration lines in the journal: %d)" % (exp, got, wrong, "".join(missing), n_decl))
        if n_decl >= len(missing):
            return PASS, "typed %r, got %r: %s are not on the Italian layout and the server DECLARED them (%d lines «not producible» in the journal; SPECS §7.3: declared, not faked)" % (exp, got, "".join(missing), n_decl)
        raise Fail("typed %r, got %r: characters lost %s but only %d declaration line(s) in the journal (journal: %s)" % (exp, got, "".join(missing), n_decl, short(lines.replace("\n", " | "))))

    def t_ctrl():
        fresh()
        rig.type_into("clip 77")
        m = rig.mark()
        rig.kb.tap("a", {"ctrl"})
        sel = [e for e in rig.since(m, "a", ("sel",)) if e["text"]]
        a_ok = bool(sel) and sel[-1]["text"] == "clip 77"
        rig.kb.tap("c", {"ctrl"})
        time.sleep(1.0)
        rig.kb.tap("End")
        rig.kb.tap("v", {"ctrl"})
        t, _ = rig.wait_for(lambda e: ([x["text"] for x in e if x["ev"] == "text"] or [""])[-1] == "clip 77clip 77", 8)
        txt = rig.text("a")
        ks = [(e["name"], e["mods"]) for e in rig.since(m, "a", ("key",)) if e["down"]]
        if a_ok and txt == "clip 77clip 77":
            return PASS, "Ctrl+A selected %r, Ctrl+C then End then Ctrl+V: the entry holds %r; keys the application saw %s" % (sel[-1]["text"], txt, ks[:8])
        raise Fail("Ctrl+A selection %r (wanted 'clip 77'), after Ctrl+C, End, Ctrl+V the entry holds %r (wanted 'clip 77clip 77'); keys seen %s" % (
            sel[-1]["text"] if sel else None, txt, ks[:10]))

    def t_shift_arrows():
        fresh()
        rig.type_into("shift test")
        rig.kb.tap("Home")
        m = rig.mark()
        for _ in range(3):
            rig.kb.tap("Right", {"shift"})
        s3 = [e for e in rig.since(m, "a", ("sel",)) if e["text"]]
        rig.kb.tap("End", {"shift"})
        s_all = [e for e in rig.since(m, "a", ("sel",)) if e["text"]]
        a, b = (s3[-1]["text"] if s3 else None), (s_all[-1]["text"] if s_all else None)
        if a == "shi" and b == "shift test":
            return PASS, "Home, Shift+Right x3 selected %r, Shift+End selected %r" % (a, b)
        raise Fail("Shift+Right x3 selected %r (wanted 'shi'), Shift+End selected %r (wanted 'shift test'); keys seen %s" % (
            a, b, [(e["name"], e["mods"]) for e in rig.since(m, "a", ("key",)) if e["down"]][:8]))

    def t_alt_tab():
        rig.stop_windows()
        rig.start_input_window("a")
        rig.start_input_window("b", "input", "d04010")
        if rig.boxname == "gnome":
            rig.leave_overview()
        rig.mouse.click(*P(0.5, 0.05))
        time.sleep(1)
        mb = rig.mark("b")
        ma = rig.mark("a")
        rig.kb.tap("Tab", {"alt"})
        time.sleep(1.5)
        a_act = [e["yes"] for e in rig.since(ma, "a", ("active",))]
        b_act = [e["yes"] for e in rig.since(mb, "b", ("active",))]
        rig.kb.tap("Tab", {"alt"})
        time.sleep(1.5)
        a_act2 = [e["yes"] for e in rig.since(ma, "a", ("active",))]
        b_act2 = [e["yes"] for e in rig.since(mb, "b", ("active",))]
        ks = [(e["name"], e["mods"]) for e in rig.since(mb, "b", ("key",)) if e["down"]] + [(e["name"], e["mods"]) for e in rig.since(ma, "a", ("key",)) if e["down"]]
        png = rig.canvas_png()
        lib.save_png(shot + "-alttab.png", png)
        if a_act[:1] == [True] and b_act[:1] == [False] and b_act2[-1:] == [True]:
            return PASS, "two windows; Alt+Tab: window A got the focus (A active events %s, B %s), a second Alt+Tab gave it back to B (A %s, B %s). Real keyboards: the page itself declares Alt+Tab among the combinations the USER'S computer keeps (SPECS §7.3-bis); here DevTools hands the key to the page" % (a_act, b_act, a_act2, b_act2)
        raise Fail("two windows (B in front); Alt+Tab: A active events %s, B %s (wanted A gains, B loses); second Alt+Tab: A %s, B %s; keys the windows saw %s; picture %s-alttab.png" % (
            a_act, b_act, a_act2, b_act2, ks[:6], shot))

    def t_super():
        fresh()
        m = rig.mark()
        sent0 = rig.g.js("return REMOTIX.classic_input.sent.length;")
        before = rig.canvas_png()
        rig.kb.tap("meta")
        time.sleep(2.5)
        after = rig.canvas_png()
        ev = rig.since(m, "a")
        saw = [e["name"] for e in ev if e["ev"] == "key"]
        lost_focus = [e for e in ev if e["ev"] == "active" and not e["yes"]]
        changed = not lib.settled(before, after)
        sent = rig.g.js("return REMOTIX.classic_input.sent.filter(x=>x.a===125).map(x=>['KEY_POSITION',x.a,x.b?'down':'up']);")
        if rig.boxname == "gnome":
            rig.kb.tap("Escape")
            rig.leave_overview()
        else:
            rig.kb.tap("Escape")
        lib.save_png(shot + "-super.png", after)
        if any(n in ("Super_L", "Meta_L", "Super_R") for n in saw) or lost_focus or changed:
            return PASS, "Super tapped: the page sent %s; in the box the application saw keys %s, lost focus %s, the desktop picture changed %s" % (sent, saw, bool(lost_focus), changed)
        raise Fail("Super tapped: the page sent %s but nothing happened in the box: the application saw %s, kept focus, picture unchanged (%s-super.png)" % (sent, saw, shot))

    def t_fkeys():
        fresh()
        m = rig.mark()
        for i in range(1, 13):
            rig.kb.tap("F%d" % i)
        time.sleep(1)
        got = [e["name"] for e in keys(m)]
        want = ["F%d" % i for i in range(1, 13)]
        lost = [w for w in want if w not in got]
        if not lost:
            return PASS, "F1..F12 pressed: the application saw all twelve key presses (%s)" % " ".join(got)
        sent = rig.g.js("return REMOTIX.classic_input.sent.length;")
        raise Fail("F1..F12 pressed: the application did not see %s (saw %s); page sent total %s messages; desktop-side swallowing is not told apart from a loss here" % (lost, got, sent))

    def t_repeat():
        fresh()
        m = rig.mark()
        rig.kb.hold("a", 2.5)
        time.sleep(1.5)
        n1 = rig.text("a").count("a")
        time.sleep(1.5)
        n2 = rig.text("a").count("a")
        rig.clear_entry()
        rig.type_into("0123456789" * 3)
        mk = rig.mark()
        rig.kb.hold("BackSpace" if False else "Backspace", 2.5)
        time.sleep(1.5)
        left = len(rig.text("a"))
        downs = [e for e in rig.since(mk, "a", ("key",)) if e["down"] and e["name"] == "BackSpace"]
        letters_ok = n1 >= 10 and n1 == n2
        pos_ok = len(downs) >= 5 and left <= 30 - 5
        if letters_ok and pos_ok:
            return PASS, "'a' held 2.5 s: %d repeats, none after release (%d later); Backspace held 2.5 s: the application saw %d presses, entry went from 30 to %d characters" % (n1, n2, len(downs), left)
        raise Fail("'a' held 2.5 s gave %d a's (wanted >= 10; %d one second later, must be equal: stops at release); Backspace held 2.5 s: %d presses, entry 30 -> %d characters (wanted >= 5 deleted)" % (n1, n2, len(downs), left))

    IT_ACCENTS = [("è", ()), ("à", ()), ("ò", ()), ("ù", ()), ("é", ("shift",)), ("ç", ("shift",)), ("°", ("shift",)), ("§", ("shift",))]

    def t_accents():
        fresh()
        lang = rig.language()
        got = type_and_read(IT_ACCENTS, 1.5)
        if got == "èàòùéç°§":
            return PASS, "browser language %s: the Italian keys è à ò ù and with Shift é ç ° § typed: the entry holds exactly %r" % (lang, got)
        raise Fail("browser language %s: Italian keys è à ò ù é ç ° § typed, the application got %r (wanted 'èàòùéç°§'); journal: %s" % (
            lang, got, rig.journal_tail("keyboard|layout|producible", 3)))

    def t_altgr():
        fresh()
        exp = "@#[]€"
        got = type_and_read([(c, ()) for c in exp], 1.5)
        if got == exp:
            return PASS, "the AltGr characters of the Italian layout typed as the browser reports them (the character itself; the tool cannot press AltGr): the entry holds exactly %r" % got
        missing, wrong = compare(exp, got)
        raise Fail("AltGr characters %r typed, the application got %r (wrong %s, missing %s); journal: %s" % (exp, got, wrong, "".join(missing), rig.journal_tail("keyboard|layout|producible", 3)))

    def t_not_producible():
        fresh()
        seq = [("x", ()), ("È", ()), ("y", ()), ("\U0001F600", ()), ("z", ())]
        t0 = time.time()
        got = type_and_read(seq, 2.0)
        n, lines = journal_declared(2, t0)
        if got == "xyz" and n >= 2:
            return PASS, "typed x È y (emoji) z: the entry holds %r (nothing faked, no different letter); the journal holds %d declaration lines «a character is not producible with layout it [Italian]: NOTHING sent» (the character itself is not named, by design RCP §7.3 / phase 16 §12)" % (got, n)
        if got == "xyz":
            raise Fail("typed x È y (emoji) z: entry %r is right but the journal declares %d of the 2 characters (journal: %s)" % (got, n, short(lines.replace("\n", " | "))))
        raise Fail("typed x È y (emoji) z: the application got %r (wanted 'xyz': nothing for what is not on the layout); declaration lines %d" % (got, n))

    def t_caps():
        fresh()
        m = rig.mark()
        if rig.g.name == "Chrome":
            rig.kb.tap("CapsLock")
            for ch in "ABC":
                rig.kb.raw(ch, "Key" + ch, ord(ch), text=ch)
            rig.kb.tap("CapsLock")
            for ch in "abc":
                rig.kb.raw(ch, "Key" + ch.upper(), ord(ch.upper()), text=ch)
            how = "CapsLock on, ABC typed as the browser reports them, CapsLock off, abc"
        else:  # WebDriver has no CapsLock key: only the characters the browser would report
            rig.kb.type("ABCabc")
            how = "ABCabc typed (WebDriver cannot press CapsLock: the lock key itself is not exercised on Firefox)"
        time.sleep(1.0)
        got = rig.text("a")
        caps = [e for e in rig.since(m, "a", ("key",)) if e["name"] == "Caps_Lock" or "caps" in e["mods"]]
        if got == "ABCabc" and not caps:
            return PASS, "%s: the entry holds %r; the desktop's own lock state was never touched (no Caps_Lock key, no caps modifier seen)" % (how, got)
        raise Fail("%s: entry %r (wanted 'ABCabc'), desktop lock state touched: %s" % (how, got, [(e["name"], e["mods"]) for e in caps][:4]))

    # ---------------------------------------------------------------------------------------------- page controls
    def t_declared():
        fresh()
        st = rig.g.js("const s=REMOTIX.shortcuts.state(); return {engine:s.engine&&s.engine.family, stage:s.stage, measured:s.lost&&s.lost.measured, n:s.lost&&s.lost.entries?s.lost.entries.length:null,"
                      " names:s.lost&&s.lost.entries?s.lost.entries.map(e=>e.combination+':'+e.state):null, warn:s.lost&&s.lost.warning};")
        log = rig.state().get("log") or ""
        lines = [x for x in log.splitlines() if "shortcuts" in x or "§7.3-bis" in x]
        btn = rig.g.js("return !!document.getElementById('shortcuts-open');")
        if lines and btn:
            return PASS, "the page declares what the browser keeps: %s; list from the page: engine %s stage %s %s entries %s; the little button to read it exists" % (
                short(" | ".join(x.strip()[:110] for x in lines[:2])), st.get("engine"), st.get("stage"), st.get("n"), st.get("names"))
        raise Fail("declaration of the shortcuts the browser keeps: log lines %s, button present %s, state %s" % (lines[:2], btn, st))

    def click_el(sel_js):
        c = rig.g.js("const e=%s; if(!e) return null; const b=e.getBoundingClientRect(); return [b.left+b.width/2, b.top+b.height/2];" % sel_js)
        if not c:
            raise Fail("the control is not on the page: %s" % sel_js)
        rig.mouse.click(*c)

    def t_cad():
        fresh()
        r = rig.g.js("const b=document.getElementById('shortcuts-open'); if(!b) return {exists:false}; const r=b.getBoundingClientRect();"
                     " return {exists:true, w:r.width, h:r.height, disp:getComputedStyle(b).display, diag:document.body.classList.contains('diagnostics')};")
        if r.get("exists") and r.get("w", 0) > 0 and r.get("disp") != "none":
            return PASS, "the control that opens the Ctrl+Alt+Del button is on screen (%dx%d px)" % (r["w"], r["h"])
        raise Fail("SPECS §7.3-bis: an on-screen Ctrl+Alt+Del button «is a requirement». As shipped there is none a user can see: the little ⌨ control that opens it exists (%s) but is not displayed (display %s, %s px) because page.html's stylesheet hides #shortcuts and #shortcuts-open unless diagnostics are on (?logbook), a change made on 16 Aug 2026 («it blocks everything for me»); the button is unreachable by default" % (
            r.get("exists"), r.get("disp"), r.get("w")))

    def t_cad_chain():
        fresh()
        rig.g.js("REMOTIX.logbook(true); return 1;")  # the page's own service route (?logbook): shows the hidden control
        time.sleep(1.0)
        try:
            m = rig.mark()
            click_el("document.getElementById('shortcuts-open')")
            time.sleep(0.8)
            before = rig.canvas_png()
            click_el("Array.from(document.querySelectorAll('#shortcuts-buttons button')).find(b=>b.textContent.indexOf('Ctrl+Alt+Del')>=0)")
            t_end, changed = time.time() + 9, False
            while time.time() < t_end:  # the desktop's own dialog (GNOME, KDE) can take seconds to appear
                time.sleep(1.5)
                ev = rig.since(m, "a")
                lost = [e for e in ev if e["ev"] == "active" and not e["yes"]]
                changed = not lib.settled(before, rig.canvas_png())
                if lost or changed:
                    break
            downs = [e["name"] for e in ev if e["ev"] == "key" and e["down"]]
            sent = rig.g.js("return (window.REMOTIX.shortcuts.dispatched||[]).slice(-1);")
            lib.save_png(shot + "-cad.png", rig.canvas_png())
            rig.kb.tap("Escape")
            if rig.boxname == "gnome":
                rig.leave_overview()
            click_el("document.getElementById('shortcuts-open')")
        finally:
            rig.g.js("REMOTIX.logbook(false); return 1;")
        if downs[:3] == ["Control_L", "Alt_L", "Delete"]:
            return PASS, "with the page's diagnostics on (service route ?logbook) the Ctrl+Alt+Del button sends the three keys: the application saw %s; page dispatched %s" % (downs, sent)
        if downs[:2] == ["Control_L", "Alt_L"] and (lost or changed):
            return PASS, "with the page's diagnostics on (service route ?logbook) the Ctrl+Alt+Del button sent the three keys (page dispatched %s); the desktop took the combination for itself, as on a local login: the application saw %s and then the desktop reacted (focus lost: %s, picture changed: %s): its own handler, a dialog" % (sent, downs, bool(lost), changed)
        raise Fail("Ctrl+Alt+Del button (diagnostics on) clicked: page dispatched %s but the application saw %s and the desktop did not react either in 9 s (focus kept: %s, picture unchanged: %s); picture %s-cad.png" % (sent, downs, not lost, not changed, shot))

    def t_lock():
        g = rig.g
        r = g.call("Runtime.evaluate", expression="REMOTIX_SHORTCUTS.enter(document.getElementById('viewer')).then(r=>JSON.stringify(r),e=>'ERR '+e)",
                   awaitPromise=True, returnByValue=True, userGesture=True).get("result", {}).get("value")
        time.sleep(2.5)
        st = g.js("const s=REMOTIX.shortcuts.state(); return {fs:s.fullscreen_API, lock:s.lock_alive, shape:s.lock_shape, why:s.lock_reason, stage:s.stage,"
                  " lost:(s.lost&&s.lost.entries)?s.lost.entries.map(e=>e.combination):null};")
        g.call("Runtime.evaluate", expression="REMOTIX_SHORTCUTS.exit()", awaitPromise=True, returnByValue=True, userGesture=True)
        time.sleep(2.5)
        left = g.js("return !!document.fullscreenElement;")
        if st.get("fs") and st.get("lock"):
            return PASS, "full screen entered from the page's own function inside a gesture: Keyboard Lock alive (%s), stage %s, still lost: %s; full screen left again: %s" % (
                st.get("shape"), st.get("stage"), st.get("lost"), not left)
        raise Fail("full screen + Keyboard Lock: fullscreen %s lock %s (%s); the call answered %s" % (st.get("fs"), st.get("lock"), st.get("why"), r))

    def t_ctrl_alt_end():
        rig.stop_windows()
        rig.start_input_window("a")
        if rig.boxname == "gnome":
            rig.leave_overview()
        focus()
        m = rig.mark()
        rig.kb.tap("End", {"ctrl", "alt"})
        time.sleep(2.5)
        dlg = rig.g.js("const d=document.getElementById('confirm'); return !!d && d.classList.contains('yes');")
        saw = [(e["name"], e["mods"]) for e in rig.since(m, "a", ("key",)) if e["down"]]
        s = rig.state()
        if dlg:
            c = rig.center("confirm-yes")
            rig.mouse.click(*c)
            s, ok = rig.wait_state(lambda s: not s["session"], 40)
            gone = rig.box.run("for i in $(seq 40); do [ -z \"$(loginctl list-sessions --no-legend | awk '$3==\"%s\"')\" ] && echo gone && break; sleep 1; done" % rig.user, timeout=70)[1]
            form = rig.g.js(lib.JS_FORM).get("form")
            if ok and form and "gone" in gone:
                return PASS, "Ctrl+Alt+End: confirmation shown, confirmed: the session ended, the page is back at the sign-in form (outcome %r), no logind session of %s is left" % (
                    (s.get("outcome") or "").strip()[:60], rig.user)
            raise Fail("Ctrl+Alt+End: confirmation shown and confirmed but the session did not end cleanly: page session %s form %s logind %s" % (s["session"], form, gone[-40:]))
        raise Fail("Ctrl+Alt+End (SPECS §5.2-bis: kept by the page, asks «end the session?», then ends it like Log Out): no confirmation appeared, the page session is still on (%s), and the desktop application RECEIVED the combination %s. The page says it removed this shortcut on 17 Aug 2026 (page.html comment before the keydown listener; «this page keeps NO key combination»), but no DECISIONS entry and SPECS §5.2-bis/§12 C2 still promise it" % (s["session"], saw[-3:]))

    # ------------------------------------------------------------------------------------- Firefox clipboard
    def ff_clip_get():
        g = rig.g
        g.call("Marionette:SetContext", {"value": "chrome"})
        try:
            return g.js("const x=Cc['@mozilla.org/widget/transferable;1'].createInstance(Ci.nsITransferable); x.init(null); x.addDataFlavor('text/plain');"
                        "try{Services.clipboard.getData(x, Services.clipboard.kGlobalClipboard);}catch(e){return '';}"
                        "const d={},l={}; try{x.getTransferData('text/plain', d); return d.value.QueryInterface(Ci.nsISupportsString).data;}catch(e){return '';}")
        finally:
            g.call("Marionette:SetContext", {"value": "content"})

    def ff_clip_set(text):
        g = rig.g
        g.call("Marionette:SetContext", {"value": "chrome"})
        try:
            g.js("Cc['@mozilla.org/widget/clipboardhelper;1'].getService(Ci.nsIClipboardHelper).copyString(arguments[0]); return 1;", text)
        finally:
            g.call("Marionette:SetContext", {"value": "content"})

    def t_ff_s2b():
        fresh()
        text = "copied from the desktop %s" % os.urandom(2).hex().translate(str.maketrans("abcdef", "ghijkl"))
        ff_clip_set("stale-before-test")
        rig.type_into(text)
        rig.kb.tap("a", {"ctrl"})
        rig.kb.tap("c", {"ctrl"})
        got, t0 = "", time.time()
        while time.time() - t0 < 10 and got != text:
            time.sleep(0.7)
            got = ff_clip_get()
        stage1 = got == text
        gesture = ""
        if not stage1:  # SPECS §9 / page.html: on Firefox the write may wait for the user's first gesture
            rig.mouse.click(*P(0.5, 0.6))
            t1 = time.time()
            while time.time() - t1 < 8 and got != text:
                time.sleep(0.7)
                got = ff_clip_get()
            gesture = " (only after a click on the desktop: the page kept it aside until a user gesture, as it declares)"
        diary = [x for x in (rig.state().get("log") or "").splitlines() if "clipboard" in x.lower()][-3:]
        if got == text:
            return PASS, "Firefox: %r typed in the desktop window, Ctrl+A Ctrl+C -> the browser clipboard holds exactly it%s" % (text, gesture)
        raise Fail("Firefox: %r copied in the desktop, the browser clipboard holds %r even after a click; page log: %s" % (text, got, short(" | ".join(diary))))

    def t_ff_b2s():
        fresh()
        text = "Ciao dal browser è € %s" % os.urandom(2).hex()
        ff_clip_set(text)
        seen = ""
        for tries in (1, 2, 3):
            rig.clear_entry()
            rig.focus_entry()
            time.sleep(0.8)
            rig.kb.tap("v", {"ctrl"})
            seen, _ = rig.wait_for(lambda e: ([x["text"] for x in e if x["ev"] == "text"] or [""])[-1] == text, 8)
            if seen:
                break
        got = rig.text("a")
        diary = [x for x in (rig.state().get("log") or "").splitlines() if "clipboard" in x.lower() or "paste" in x.lower()][-4:]
        if got == text:
            return PASS, "Firefox: %r put in the browser clipboard, Ctrl+V (attempt %d) -> the desktop window holds exactly it (the page's own hint: Ctrl+V is the route on Firefox)" % (text, tries)
        raise Fail("Firefox: %r in the browser clipboard, Ctrl+V x3 -> the desktop window holds %r; page log: %s" % (text, got, short(" | ".join(diary))))

    # -------------------------------------------------------------------------------------------------- the run
    rig.type_into = lambda s: (rig.kb.type(s), time.sleep(1.0))

    def flow():
        ver = rig.start()
        print("check-input %s %s (%s), user %s; browser language %s (Italian layout asked by the page)" % (a.box, a.browser, ver, user, rig.language() if rig.g else "?"), flush=True)
        rig.open_page()
        if a.browser == "chrome":
            rig.g.call("Browser.grantPermissions", origin=rig.url.rstrip("/"), permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
        rig.login(real=True)
        rig.settle(a.cap)
        rig.start_input_window("a")
        print("session up; layout asked: %s; navigator.language %s; desktop %s" % (rig.g.js("return typeof layout==='function'?layout():'?';"), rig.language(), rig.state()["rect"][2:]), flush=True)
        todo = [("mouse-buttons", t_buttons), ("mouse-doubleclick", t_double), ("mouse-wheel", t_wheel), ("mouse-drag", t_drag),
                ("mouse-coordinates", t_coordinates), ("pointer-shape-text", t_shape_text), ("pointer-shape-arrow", t_shape_arrow),
                ("no-double-cursor", t_no_double), ("kbd-text", t_text), ("kbd-ctrl-clipboard", t_ctrl), ("kbd-shift-arrows", t_shift_arrows),
                ("kbd-function-keys", t_fkeys), ("kbd-repeat", t_repeat), ("kbd-accents", t_accents), ("kbd-altgr", t_altgr),
                ("kbd-not-producible", t_not_producible), ("kbd-capslock", t_caps), ("page-shortcuts-declared", t_declared),
                ("page-cad-button", t_cad), ("page-cad-chain", t_cad_chain), ("kbd-super", t_super), ("kbd-alt-tab", t_alt_tab)]
        if ff:
            todo += [("clipboard-firefox-session-to-browser", t_ff_s2b), ("clipboard-firefox-browser-to-session", t_ff_b2s)]
        else:
            todo += [("page-keyboard-lock", t_lock)]
        todo += [("pointer-shape-edge", t_shape_edge), ("edge-drag", t_edge_drag), ("page-ctrl-alt-end", t_ctrl_alt_end)]
        for name, fn in todo:
            if only and name not in only:
                continue
            res.attempt(name, fn)

    try:
        return res.sequence(flow, 1500)
    finally:
        if rig.g:
            try:
                print("screenshot of the client page: %s" % lib.save_png(shot + "-page.png", rig.g.screenshot()))
            except Exception as e:  # noqa: BLE001
                print("no screenshot of the client page: %s" % str(e)[:150])
        rig.stop()


if __name__ == "__main__":
    sys.exit(main())
