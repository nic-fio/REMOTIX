#!/usr/bin/env python3
"""check-kde-birth - KDE with KWin alone: a NEW session is born at the size the browser asks, whatever the previous session left.

    RX_BANCO=vm python3 check-kde-birth.py [--box kde]

KWin remembers the last mode of its `Virtual-0` output in ~/.config/kwinoutputconfig.json, and the start line's --width/--height only count
the first time (fedora45/studio/5-kde-progetto.md, I6): the child corrects the size before it mounts the stream.  Here a user logs in four
times with a browser window of a DIFFERENT size each time, logging out of the desktop (Log Out) in between; each time the canvas the login
announces must be the one the desktop window in the box really has, and different from the size the previous session ended at.
PASS|FAIL per birth; exit 0 only if all PASS.  Not part of all.sh."""
import argparse
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

SIZES = [(1400, 900), (900, 600), (1300, 700), (1000, 800)]
LOGOUT = "busctl --user call org.kde.Shutdown /Shutdown org.kde.Shutdown logout"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box", default="kde")
    a = ap.parse_args()
    bad, prev = [], None
    for i, (w, h) in enumerate(SIZES, 1):
        rig = lib.Rig(a.box, "chrome", "kb1", "kb1pass2026", "kbirth%d" % i, cap=60)
        try:
            rig.start(size=(w, h))
            rig.open_page()
            outcome = rig.login()["outcome"].strip()
            m = re.search(r"canvas (\d+)\D+(\d+)", outcome)
            asked = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
            rig.settle(60)
            rig.start_window()
            rig.g.move(*rig.px(0.4, 0.4))
            time.sleep(1.5)
            ev = [e for e in rig.events() if "w" in e]
            got = (ev[-1]["w"], ev[-1]["h"]) if ev else (0, 0)
            ok = asked != (0, 0) and got == asked and (prev is None or asked != prev) and "new session" in outcome
            print("%s birth %d: browser %dx%d -> «%s» -> desktop window in the box %dx%d (previous session ended at %s)" % (
                "PASS" if ok else "FAIL", i, w, h, outcome[:70], got[0], got[1], prev), flush=True)
            if not ok:
                bad.append(i)
            prev = got
            rig.box.run("u=$(id -u kb1); runuser -u kb1 -- env XDG_RUNTIME_DIR=/run/user/$u DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus timeout 20 %s; true" % LOGOUT, timeout=40)
            for _ in range(40):
                if rig.box.run("pgrep -u kb1 -x 'kwin_wayland|plasmashell' | wc -l")[1].strip() == "0":
                    break
                time.sleep(1)
        finally:
            rig.stop()
    print("RESULT:", "PASS" if not bad else "FAIL in births %s" % bad)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
