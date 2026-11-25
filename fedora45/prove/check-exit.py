#!/usr/bin/env python3
"""check-exit - the ways a remote XFCE / LXQt desktop (labwc) ends leave nothing behind (the same three cases as check-kde-exit.py).

    RX_BANCO=vm python3 check-exit.py --box xfce|lxqt

Three cases with a user (kx1) logged in from the browser; after each, within 45 s NO process of the desktop (labwc, the session, the panel, Xwayland)
of the user may be left and no logind session of REMOTIX:
  1 terminate-session   `loginctl terminate-session` on the REMOTIX session (the desktop would be an ORPHAN: the sweep of the root side must stop it)
  2 service restart     `systemctl restart remotix` with the desktop open (the stop closes the remote desktops)
  3 close and wait      the browser window is closed and the user stays away 20 s: the desktop must still be ALIVE (it outlives the client), then a
                        new login resumes it (not an exit; it proves the sweep does not stop a desktop somebody may come back to)
PASS|FAIL per case; exit 0 only if all PASS.  Not part of all.sh."""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402

PROCS = {"xfce": "labwc|xfce4-session|xfce4-panel|xfdesktop|Xwayland", "lxqt": "labwc|lxqt-session|lxqt-panel|pcmanfm-qt|Xwayland"}
LOGOUT = {"xfce": "xfce4-session-logout --logout",
          "lxqt": "busctl --user --expect-reply=no call org.lxqt.session /LXQtSession org.lxqt.session logout"}
BOX = "xfce"
LEFT = ""
SESS = "for i in $(loginctl list-sessions --no-legend | awk '$3==\"kx1\"{print $1}'); do loginctl show-session $i -p Service --value; done | grep -c remotix"


def gone(rig, cap=45):
    t0 = time.time()
    while time.time() - t0 < cap:
        n = rig.box.run(LEFT)[1].strip()
        if n == "0":
            return time.time() - t0, True
        time.sleep(1)
    return cap, False


def facts(rig):
    return "desktop processes left %s, REMOTIX logind sessions %s" % (rig.box.run(LEFT)[1].strip(), rig.box.run(SESS)[1].strip() or "0")


def fresh(tag):
    rig = lib.Rig(BOX, "chrome", "kx1", "kx1pass2026", tag, cap=60)
    rig.start()
    rig.open_page()
    rig.login()
    rig.settle(60)
    return rig


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--box", default="xfce", choices=["xfce", "lxqt"])
    global BOX, LEFT
    BOX = ap.parse_args().box
    LEFT = "pgrep -u kx1 -x '%s' | wc -l" % PROCS[BOX]
    bad = []
    # 1
    rig = fresh("kx-a")
    try:
        sid = rig.box.run("loginctl list-sessions --no-legend | awk '$3==\"kx1\"{print $1}' | while read i; do [ \"$(loginctl show-session $i -p Service --value)\" = remotix ] && echo $i; done")[1].split()
        rig.box.run("loginctl terminate-session %s" % sid[0])
        dt, ok = gone(rig)
        print("%s 1 terminate-session %s: %s after %.0f s; %s" % ("PASS" if ok else "FAIL", sid, "desktop gone" if ok else "DESKTOP STILL THERE", dt, facts(rig)), flush=True)
        ok or bad.append(1)
    finally:
        rig.stop()
    time.sleep(3)
    # 2
    rig = fresh("kx-b")
    try:
        rig.box.run("systemctl restart remotix", timeout=120)
        dt, ok = gone(rig)
        print("%s 2 service restart: %s after %.0f s; %s" % ("PASS" if ok else "FAIL", "desktop gone" if ok else "DESKTOP STILL THERE", dt, facts(rig)), flush=True)
        ok or bad.append(2)
    finally:
        rig.stop()
    time.sleep(8)
    # 3
    rig = fresh("kx-c")
    try:
        rig.g.close()
        rig.g = None
        time.sleep(20)
        n = rig.box.run(LEFT)[1].strip()
        rig.new_browser()
        rig.open_page()
        out = rig.login()["outcome"].strip()
        ok = n != "0" and "resumed" in out
        print("%s 3 close and wait 20 s: %s desktop processes alive while away; login again: «%s»" % ("PASS" if ok else "FAIL", n, out[:60]), flush=True)
        ok or bad.append(3)
        rig.box.run("u=$(id -u kx1); runuser -u kx1 -- env XDG_RUNTIME_DIR=/run/user/$u DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus timeout 20 %s; true" % LOGOUT[BOX], timeout=40)
        dt, ok2 = gone(rig)
        print("   (clean up: Log Out, %s after %.0f s)" % ("gone" if ok2 else "STILL THERE", dt), flush=True)
    finally:
        rig.stop()
    print("RESULT:", "PASS" if not bad else "FAIL in cases %s" % bad)
    return 0 if not bad else 1


if __name__ == "__main__":
    sys.exit(main())
