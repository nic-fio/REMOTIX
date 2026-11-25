#!/usr/bin/env python3
"""check-kde-live - KDE with KWin alone: the browser window is resized LIVE, several times in a row, with a program open in the session.

    RX_BANCO=vm python3 check-kde-live.py [--box kde] [--rounds 8]

Runs ON THE DEV SERVER (lib.py).  What the product does (page.html, `renegotiate_view`, owner's decision of 17 Aug 2026, DECISIONS.md §5.1-bis): the canvas is
asked for at BIRTH and at RE-ATTACH only; a LIVE window resize NEVER changes the desktop's size, the page just rescales the picture (`fit_view`).  So this
probe checks exactly that, on KDE: after each live resize (Chrome DevTools `Browser.setWindowBounds`, odd sizes included) (1) the window really changed size,
(2) the desktop window in the box kept its size (no change was asked), (3) the picture is a desktop and still ALIVE (the page's frame counter keeps growing after a typed character), (4) a click at (0.60, 0.50) of the NEW view lands at (0.60, 0.50) of the desktop, (5) the X11 program is alive.  PASS|FAIL."""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

SIZES = [(1100, 640), (1001, 601), (901, 555), (1365, 767), (777, 513), (1200, 800), (1366, 768), (1280, 720)]


def last_size(rig):
    ev = [e for e in rig.events() if "w" in e and "h" in e]
    return (ev[-1]["w"], ev[-1]["h"]) if ev else (0, 0)


def set_window(rig, w, h):
    tgt = rig.g.call("Browser.getWindowForTarget")
    rig.g.call("Browser.setWindowBounds", windowId=tgt["windowId"], bounds={"windowState": "normal", "width": w, "height": h})
    time.sleep(2.5)
    return rig.g.js("return [innerWidth, innerHeight];")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box", default="kde")
    ap.add_argument("--rounds", type=int, default=8)
    a = ap.parse_args()
    rig = lib.Rig(a.box, "chrome", "kr1", "kr1pass2026", "klive", cap=60)
    bad = []
    try:
        rig.start()
        rig.open_page()
        print("login:", rig.login()["outcome"].strip(), flush=True)
        rig.settle(60)
        env = rig.box.run("u=$(id -u kr1); runuser -u kr1 -- env XDG_RUNTIME_DIR=/run/user/$u systemctl --user show-environment | grep -E '^(DISPLAY|XAUTHORITY)='")[1]
        xenv = " ".join(l.strip() for l in env.splitlines() if "=" in l)
        if xenv:
            rig.box.in_session("kr1", "env %s MOZ_ENABLE_WAYLAND=0 GDK_BACKEND=x11 firefox --no-remote --new-instance --profile /tmp/kr1-ff about:blank" % xenv)
        rig.box.run("printf '%s' '<html><body style=\"margin:0\"><div id=a style=\"width:200px;height:200px;background:red\"></div><script>let x=0;function f(){x=(x+4)%800;a.style.marginLeft=x+\"px\";requestAnimationFrame(f)};f()</script></body></html>' > /tmp/kr1-clock.html; chmod 644 /tmp/kr1-clock.html")
        # the check needs a Chromium INSIDE the box (it tries a Wayland browser next to an X11 one): without it «Chromium GONE» was a lie about the
        # product (found 22 Nov 2026 on the Fedora VMs, which have only Firefox: the same check passes 8/8 once `dnf install chromium` is done)
        if rig.box.run("command -v chromium-browser >/dev/null && echo yes")[1].strip() != "yes":
            raise lib.ToolError("the box has no chromium-browser (dnf install chromium): the check cannot try a Wayland browser — BLOCKED, not a verdict on the product")
        rig.box.in_session("kr1", "chromium-browser --ozone-platform=wayland --user-data-dir=/tmp/kr1-chr --no-first-run --new-window file:///tmp/kr1-clock.html")
        time.sleep(15)
        rig.start_window()
        time.sleep(3)
        rig.g.move(*rig.px(0.3, 0.3))
        base = last_size(rig)
        print("desktop window before the live resizes: %dx%d" % base, flush=True)
        prev_inner = rig.g.js("return [innerWidth, innerHeight];")
        for i, (vw, vh) in enumerate(SIZES[:a.rounds], 1):
            inner = set_window(rig, vw, vh)
            time.sleep(1)
            rig.g.move(*rig.px(0.3, 0.3))
            time.sleep(0.6)
            got = last_size(rig)
            n0 = len([e for e in rig.events() if e["ev"] == "click"])
            painted0 = rig.state().get("painted", 0)
            rig.g.move(*rig.px(0.5, 0.5))
            time.sleep(0.4)
            rig.g.click(*rig.px(0.6, 0.5))
            clicks, end = [], time.time() + 8
            while time.time() < end:
                clicks = [e for e in rig.events() if e["ev"] == "click"]
                if len(clicks) > n0:
                    break
                time.sleep(0.5)
            rig.g.type_text("x")  # the click focused the test window's entry: a typed character changes the picture, so frames must arrive
            time.sleep(1.5)
            deg, desc = lib.judge_pixel(rig.canvas_png())
            painted1 = rig.state().get("painted", 0)
            alive = painted1 > painted0
            x11 = rig.box.run("pgrep -u kr1 -f 'firefox.*kr1-ff' | head -1")[1].strip()
            chrome = rig.box.run("pgrep -u kr1 -f 'chromium.*kr1-chr' | head -1")[1].strip()
            ok_click = len(clicks) > n0 and abs(clicks[-1]["fx"] - 0.6) < 0.06 and abs(clicks[-1]["fy"] - 0.5) < 0.06
            changed = list(inner) != list(prev_inner)
            prev_inner = inner
            ok = changed and got == base and ok_click and not deg and alive and x11 and chrome
            print(("PASS " if ok else "FAIL ") + "%d live resize -> browser view %dx%d (%s); desktop window %dx%d (%s); click at (0.60,0.50) seen at %s; picture %s, %s; X11 %s, Chromium %s" % (
                i, inner[0], inner[1], "changed" if changed else "NOT CHANGED", got[0], got[1], "unchanged" if got == base else "CHANGED",
                "(%.2f,%.2f)" % (clicks[-1]["fx"], clicks[-1]["fy"]) if len(clicks) > n0 else "NOTHING",
                "NOT a desktop (%s)" % desc if deg else "ok", "%d new frames after the input" % (painted1 - painted0) if alive else "NO NEW FRAMES", "alive" if x11 else "GONE", "alive" if chrome else "GONE"), flush=True)
            if not ok:
                bad.append(i)
        print("RESULT:", "PASS" if not bad else "FAIL in rounds %s" % bad)
        return 0 if not bad else 1
    finally:
        rig.stop()


if __name__ == "__main__":
    sys.exit(main())
