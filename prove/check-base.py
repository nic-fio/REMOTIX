#!/usr/bin/env python3
"""check-base - the small end-to-end check of a running REMOTIX box, with a real browser.

    python3 check-base.py [--box xfce] [--browser chrome|firefox]

Runs ON THE DEV SERVER (drives ./boxes/box.sh and a headless labwc there; see lib.py). One line per check:
    PASS|FAIL|BLOCKED <name> - evidence
exit 0 only if all five PASS. Checks: page, login, desktop, mouse, keyboard.
  FAIL    = the product did not do it (also: the page does not answer).   BLOCKED = the tool could not look.
Its own user bc1 is made in the box. Mouse and keyboard are proven INSIDE the box: a fullscreen GTK window (window.py) in the
user's session logs the events it receives. Pictures go to <prove>/shots/ (the client page, the desktop canvas)."""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
from lib import PASS, FAIL, BLOCKED  # noqa: E402

USER, PASSWORD, TYPED = "bc1", "bc1pass2026", "remotix2"
NAMES = ("page", "login", "desktop", "mouse", "keyboard")


def selftest():
    from PIL import Image
    import io
    b = io.BytesIO()
    Image.new("RGB", (320, 200), (0, 0, 0)).save(b, "PNG")
    d, t = lib.judge_pixel(b.getvalue())
    print("selftest: black picture is degenerate: %s (%s)" % (d, t))
    return 0 if d else 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--browser", default="chrome", choices=("chrome", "firefox"))
    ap.add_argument("--cap", type=int, default=60, help="seconds allowed for login and first picture")
    ap.add_argument("--selftest", action="store_true", help="check only that the picture judge can say 'degenerate'")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    stamp = time.strftime("%Y%m%d-%H%M%S")
    shot = "base-%s-%s-%s" % (a.box, a.browser, stamp)
    res, rig = lib.Results(NAMES), lib.Rig(a.box, a.browser, USER, PASSWORD, "base", cap=a.cap)

    def flow():
        say = res.say
        rig.start()
        g = rig.g
        # 1. page
        rig.open_page()
        say(PASS, "page", "%s loaded in %s, login form visible, title \"%s\"" % (rig.url, g.version, g.js(lib.JS_FORM).get("title")))
        # 2. login
        s = rig.login()
        say(PASS, "login", "user %s admitted: \"%s\"" % (USER, s["outcome"].strip()))
        # 3. desktop: decoded frames arrive, the shell is up, AND the picture is not uniform and stays still
        d = rig.settle(a.cap)
        lib.save_png(shot + "-desktop.png", d["png"])
        say(PASS, "desktop", "%sdecoded frames painted=%d (delivered=%d), picture not uniform and still (%s), shell up %.0f s and picture settled %.0f s after the first frame, saved %s-desktop.png"
            % (d["extra"], d["s"]["painted"], d["s"]["delivered"], d["desc"], d["shell_s"], d["settle_s"], shot))
        # 4/5. mouse and keyboard, seen from inside the box through the test window
        rig.start_window()
        L, T, W, H = rig.state()["rect"]
        # the pointer is tried again every 2 s for up to 20 s: dead the whole time = FAIL, late = PASS with the delay said
        t_m, tries = time.time(), 0
        while time.time() - t_m < 20 and not [e for e in rig.events() if e["ev"] == "click"]:
            tries += 1
            g.move(*rig.px(0.3, 0.3))
            time.sleep(0.3)
            g.move(*rig.px(0.6, 0.5))
            time.sleep(0.3)
            g.click(*rig.px(0.6, 0.5))
            time.sleep(1.5)
        ev = rig.events()
        clicks, motions = [e for e in ev if e["ev"] == "click"], [e for e in ev if e["ev"] == "motion"]
        if clicks and abs(clicks[0]["fx"] - 0.6) < 0.08 and abs(clicks[0]["fy"] - 0.5) < 0.08:
            say(PASS, "mouse", "clicked at (0.60,0.50) of the canvas (attempt %d, %.0f s); the window in the box got %d motion events and a click at (%.2f,%.2f)"
                % (tries, time.time() - t_m, len(motions), clicks[0]["fx"], clicks[0]["fy"]))
        elif clicks:
            say(FAIL, "mouse", "click sent at (0.60,0.50) but the box saw it at (%.2f,%.2f)" % (clicks[0]["fx"], clicks[0]["fy"]))
        else:
            say(FAIL, "mouse", "click sent %d times in 20 s at (0.60,0.50), %d motion events and NO click reached the window in the box" % (tries, len(motions)))
        g.type_text(TYPED)
        end = time.time() + 8
        while time.time() < end and not [e for e in rig.events() if e["ev"] == "text" and TYPED in e["text"]]:
            time.sleep(0.5)
        texts = [e["text"] for e in rig.events() if e["ev"] == "text"]
        if texts and TYPED in texts[-1]:
            say(PASS, "keyboard", "typed \"%s\" in the browser, the window in the box holds \"%s\"" % (TYPED, texts[-1]))
        else:
            say(FAIL, "keyboard", "typed \"%s\" in the browser, the window in the box holds %s" % (TYPED, repr(texts[-1]) if texts else "nothing"))

    try:
        return res.sequence(flow, 420)
    finally:
        if rig.g:
            try:
                print("screenshot of the client page: %s" % lib.save_png(shot + "-page.png", rig.g.screenshot()))
            except Exception as e:  # noqa: BLE001
                print("no screenshot of the client page: %s" % str(e)[:150])
        rig.stop()


if __name__ == "__main__":
    sys.exit(main())
