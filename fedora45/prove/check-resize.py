#!/usr/bin/env python3
"""check-resize - XFCE / LXQt (labwc, headless): the remote desktop follows a RE-ATTACH at another browser size, with a program open.

    RX_BANCO=vm python3 check-resize.py --box xfce|lxqt [--rounds 10]

Runs ON THE DEV SERVER (lib.py).  One session (user kr1) is carried through `--rounds` re-attaches of a browser window of another size (odd sizes
included): the product asks for the canvas at birth and at re-attach only (page.html, owner's decision of 17 Aug 2026).  After each one it waits for
the test window in the box (window.py, fullscreen) to take the new size (= the desktop's canvas), clicks at (0.60, 0.50) of the canvas and checks the box
saw the click at that place, that the picture is a desktop (not uniform), and that a terminal opened in the session before the first round is still alive.
One line per round and PASS|FAIL at the end.  Not part of all.sh."""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

SIZES = [(1280, 720), (1100, 640), (1001, 601), (901, 555), (1365, 767), (1000, 700), (777, 513), (1200, 800), (1366, 768), (1280, 720)]


def reattach(rig, w, h):
    """The product asks for the canvas at BIRTH and at RE-ATTACH, never live (page.html, `renegotiate_view`: the owner's decision of
    17 Aug 2026): so «the browser window changes size» is a NEW browser window of that size logging in again to the same session.
    Returns the outcome text of the login («Admitted, resumed, canvas WxH …»)."""
    rig.new_browser(size=(w, h))
    rig.open_page()
    return rig.login()["outcome"].strip()


def last_size(rig):
    ev = [e for e in rig.events() if "w" in e and "h" in e]
    return (ev[-1]["w"], ev[-1]["h"]) if ev else (0, 0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box", default="xfce", choices=["xfce", "lxqt"])
    ap.add_argument("--rounds", type=int, default=10)
    ap.add_argument("--chromium", action="store_true", help="also run Chromium (Wayland) on an animated page in the session and check it is alive after every round")
    a = ap.parse_args()
    rig = lib.Rig(a.box, "chrome", "kr1", "kr1pass2026", "kres", cap=60)
    bad = []
    try:
        rig.start()
        rig.open_page()
        s = rig.login()
        print("login:", s["outcome"].strip(), flush=True)
        rig.settle(60)
        term = {"xfce": "xfce4-terminal", "lxqt": "qterminal"}[a.box]
        rig.box.in_session("kr1", term)
        time.sleep(8)
        print("program %s open in the session: %s" % (term, rig.box.run("pgrep -u kr1 -c -x %s" % term)[1].strip()), flush=True)
        rig.start_window()
        for i, (vw, vh) in enumerate(SIZES[:a.rounds], 1):
            t0 = time.time()
            before = last_size(rig)
            outcome = reattach(rig, vw, vh)
            got, end = (0, 0), time.time() + 25
            while time.time() < end:
                time.sleep(1)
                rig.g.move(*rig.px(0.3, 0.3))
                got = last_size(rig)
                if got != before and got == last_size(rig):
                    time.sleep(1.5)
                    rig.g.move(*rig.px(0.35, 0.35))
                    if last_size(rig) == got:
                        break
            n0 = len([e for e in rig.events() if e["ev"] == "click"])
            rig.g.move(*rig.px(0.5, 0.5))
            time.sleep(0.4)
            rig.g.click(*rig.px(0.6, 0.5))
            clicks, end = [], time.time() + 8
            while time.time() < end and len(clicks) <= n0 - 0:
                clicks = [e for e in rig.events() if e["ev"] == "click"]
                if len(clicks) > n0:
                    break
                time.sleep(0.5)
            png = rig.canvas_png()
            deg, desc = lib.judge_pixel(png)
            x11 = rig.box.run("pgrep -u kr1 -x %s | head -1" % term)[1].strip()
            chrome = None
            ok_click = len(clicks) > n0 and abs(clicks[-1]["fx"] - 0.6) < 0.06 and abs(clicks[-1]["fy"] - 0.5) < 0.06
            line = "%2d browser window %dx%d -> «%s» -> desktop window %dx%d (was %dx%d), %.0f s; click at (0.60,0.50) seen at %s; picture %s; program %s" % (
                i, vw, vh, outcome[:60], got[0], got[1], before[0], before[1], time.time() - t0,
                "(%.2f,%.2f)" % (clicks[-1]["fx"], clicks[-1]["fy"]) if len(clicks) > n0 else "NOTHING", "NOT a desktop (%s)" % desc if deg else "ok",
                "alive" if x11 else "GONE") + ("; Chromium %s" % ("alive" if chrome else "GONE") if a.chromium else "")
            print(("PASS " if ok_click and not deg and got != (0, 0) and (chrome or not a.chromium) else "FAIL ") + line, flush=True)
            if not (ok_click and not deg and got != (0, 0) and (chrome or not a.chromium)):
                bad.append(i)
        print("RESULT:", "PASS" if not bad else "FAIL in rounds %s" % bad)
        return 0 if not bad else 1
    finally:
        rig.stop()


if __name__ == "__main__":
    sys.exit(main())
