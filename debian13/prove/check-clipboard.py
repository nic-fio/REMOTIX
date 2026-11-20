#!/usr/bin/env python3
"""check-clipboard - text clipboard, both directions (SPECS §9), real browser (Chrome), real input, real desktop window.

    python3 check-clipboard.py [--box xfce|lxqt|gnome|kde]

Runs ON THE DEV SERVER (Chrome only: the clipboard permission API is driven by DevTools). One line per check:
PASS|FAIL|BLOCKED name - evidence; exit 0 only if all PASS.
  FAIL = the product did not do it (also: page or login refused).   BLOCKED = the tool could not look.
Its own user cb1 is made in the box. The desktop side is the fullscreen GTK entry window of window.py, in the user's session.
  session-to-browser: type a unique text in that window, select all, real Ctrl+C -> the browser clipboard must hold it.
  browser-to-session: put a unique text in the browser clipboard, empty the window, real Ctrl+V -> the window must hold it.
The browser clipboard permission is granted the way the user would ("Allow" on the permission prompt)."""
import argparse
import os
import secrets
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
from lib import PASS, FAIL, BLOCKED  # noqa: E402

USER, PASSWORD = "cb1", "cbpass4821"
NAMES = ("clipboard-session-to-browser", "clipboard-browser-to-session")


def read_clip(g):
    """The browser's clipboard, read with readText() in the page: (text | None, error)."""
    r = g.js("return navigator.clipboard.readText().then(t=>({t:t}),e=>({e:String(e)}));")
    return (r.get("t"), r.get("e")) if r else (None, "no answer")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--cap", type=int, default=60)
    a = ap.parse_args()
    res, rig = lib.Results(NAMES), lib.Rig(a.box, "chrome", USER, PASSWORD, "clip", cap=a.cap)

    def flow():
        say = res.say
        ver = rig.start()
        rig.open_page()
        g = rig.g
        g.call("Browser.grantPermissions", origin=rig.url.rstrip("/"), permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
        rig.login(real=True)
        rig.settle(a.cap)
        rig.start_window()
        rig.canvas_click(0.5, 0.5)  # focus the window's entry (real click: also the user gesture for the page)
        time.sleep(1)
        # --- session -> browser
        text1 = "copied" + secrets.token_hex(3).translate(str.maketrans("abcdef", "ghijkl")) + " in the desktop"
        g.js("return navigator.clipboard.writeText('stale-before-test').then(()=>1,()=>0);")
        g.type_text(text1)
        time.sleep(1)
        shown = [e["text"] for e in rig.events() if e["ev"] == "text"]
        if not shown or shown[-1] != text1:
            say(BLOCKED, NAMES[0], "typing into the desktop window failed: it holds %r" % (shown[-1:],))
        else:
            got, err = None, None
            for attempt in (1, 2):
                g.chord("a", ctrl=True)
                g.chord("c", ctrl=True)
                end = time.time() + 10
                while time.time() < end:
                    got, err = read_clip(g)
                    if got == text1:
                        break
                    time.sleep(0.7)
                if got == text1:
                    break
            if got == text1:
                say(PASS, NAMES[0], "%s: \"%s\" typed in the desktop window, Ctrl+A Ctrl+C (attempt %d) -> browser clipboard holds exactly it" % (ver, text1, attempt))
            else:
                diary = [x for x in (rig.state().get("log") or "").splitlines() if "clipboard" in x.lower()][-3:]
                say(FAIL, NAMES[0], "\"%s\" copied in the desktop, browser clipboard after 2 tries holds %r (readText error: %s); page log: %s"
                    % (text1, got, err, " | ".join(diary)[:250]))

        # --- browser -> session
        text2 = "Ciao dal browser è € %s" % secrets.token_hex(3)
        r = g.js("return navigator.clipboard.writeText(arguments[0]).then(()=>'ok',e=>String(e));", text2)
        if r != "ok":
            say(BLOCKED, NAMES[1], "the tool could not put text into the browser clipboard: %s" % r)
        else:
            rig.canvas_click(0.5, 0.5)
            g.chord("a", ctrl=True)
            g.chord("Delete")
            time.sleep(1)
            last = ([e["text"] for e in rig.events() if e["ev"] == "text"] or [None])[-1]
            if last != "":
                say(BLOCKED, NAMES[1], "could not empty the desktop window (holds %r)" % last)
            else:
                seen, tries = None, 0
                for tries in (1, 2, 3):
                    rig.canvas_click(0.5, 0.5)
                    time.sleep(1)
                    g.chord("v", ctrl=True, cmd="paste")
                    end = time.time() + 8
                    while time.time() < end and seen != text2:
                        seen = ([e["text"] for e in rig.events() if e["ev"] == "text"] or [None])[-1]
                        time.sleep(0.5)
                    if seen == text2:
                        break
                if seen == text2:
                    say(PASS, NAMES[1], "\"%s\" in the browser clipboard, Ctrl+V (attempt %d) -> the desktop window holds exactly it" % (text2, tries))
                else:
                    diary = [x for x in (rig.state().get("log") or "").splitlines() if "clipboard" in x.lower() or "paste" in x.lower()][-4:]
                    say(FAIL, NAMES[1], "\"%s\" in the browser clipboard, Ctrl+V x3 -> the desktop window holds %r; page log: %s"
                        % (text2, seen, " | ".join(diary)[:300]))

    try:
        return res.sequence(flow, 420)
    finally:
        rig.stop()


if __name__ == "__main__":
    sys.exit(main())
