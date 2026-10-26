#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f031c — F-031C THE PHONE'S DESKTOP MODE WITH A REAL MOUSE (DeX, Pixel desktop mode):
           the page leaves the touch layout at the first mouse move, and STAYS in classic

    python3 15-f031c-desktop-mode-mouse.py --box gnome --browser chrome [--fault]

⭐ WHY (26 Oct 2026, the user on a Galaxy S23+ in DeX, Chrome 155): the browser says
`(pointer: coarse)` and NO `(any-pointer: fine)` although a mouse is there, and fires the
media-query `change` again and again while the mouse is used.  The page went touch → classic →
touch at every change: TWO cursors and a mouse that jumped, with 1.0 and 1.5 alike.  The cure
(page.html, 88836350 + cb3c9e99): a mouse MOVE in the touch layout is proof of a fine pointer,
and a hardware change no longer erases what was seen.

CHROME ONLY (BROWSERS below): the desktop mode of the phones is Chrome's, and only Chrome
changes the pointer media features FOR REAL: `Emulation.setTouchEmulationEnabled` makes
`(pointer: coarse)` true and `(any-pointer: fine)` false, exactly DeX's answers, and the real
MediaQueryList objects of the page fire their real `change` listeners ([M] 26 Oct 2026, Chrome 156;
`Emulation.setEmulatedMedia` does NOT emulate pointer/hover: it is ignored without an error).
The mouse events stay `pointerType = "mouse"` (that is `setEmitTouchEventsForMouse`, not used).
Every switch is CHECKED in the page (the matches, and a counter of the real `change` events):
an emulation that did not take is BLOCKED, never green.

  phone     the media features of the S23+ in DeX (pointer coarse, any-pointer coarse, no hover):
            the page must be in touch.  If it is in classic because the login was done with the
            mouse (the page remembers the last pointer), one real TAP (CDP touch) first: the user
            touched the screen, then takes the mouse.
  fault     (--fault, FIRST, so nothing has been seen yet) no mouse move: the page stays touch
            ⇒ the judge must say red.
  mouse     two real mouse moves (`Input.dispatchMouseEvent`: pointerType "mouse", as in DeX):
            classic.
  storm     six times the features flip to a fine pointer and back to the phone's: twelve real
            `change` events; after each return to the phone's context the page must STILL be
            classic (the page of before the cure threw the observation away at every change).
The judge (one function, certified): touch after the phone context (else BLOCKED) · classic after
the move · classic after EVERY return of the storm.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNCTIONS = ("F-031C",)
BROWSERS = ("chrome",)
STORM = 6

PHONE, FINE = True, False
LAYOUT = "return REMOTIX.touch.layout();"
# the page's own reading of the context, and a counter of the REAL change events (installed once)
READ_MEDIA = r"""
if (window.__rx_changes === undefined) {
  window.__rx_changes = 0;
  window.__rx_mql = matchMedia("(pointer: coarse)");
  window.__rx_mql.addEventListener("change", function () { window.__rx_changes++; });
}
return [matchMedia("(pointer: coarse)").matches, matchMedia("(any-pointer: fine)").matches, window.__rx_changes];
"""


def judge(after_phone, after_move, storm):
    """(outcome, rationale): after_phone/after_move = the layout read, storm = the layouts after each return."""
    if after_phone != "touch":
        return S.BLOCKED, "the phone context did not take: the page is «%s», not touch" % after_phone
    if after_move != "classic":
        return S.FAIL, "a real mouse moved and the page stayed «%s» (two cursors in DeX)" % after_move
    if not storm:
        return S.BLOCKED, "the storm was not looked at"
    bad = [i + 1 for i, x in enumerate(storm) if x != "classic"]
    if bad:
        return S.FAIL, "back out of classic at return %s of %d (%s): the touch/classic ping-pong of DeX" % (
            ", ".join(map(str, bad)), len(storm), "/".join(map(str, storm)))
    return S.PASS, "touch in the phone context, classic at the first mouse move, classic through %d media changes" % len(storm)


def certify():
    troubles = []

    def prova(what, real):
        print("   %s %s" % ("⭐ ok " if real else "⛔ NO ", what))
        if not real:
            troubles.append(what)
    prova("all right ⇒ PASS", judge("touch", "classic", ["classic"] * STORM)[0] == S.PASS)
    prova("the move does not count ⇒ FAIL", judge("touch", "touch", ["touch"] * STORM)[0] == S.FAIL)
    prova("ping-pong in the storm ⇒ FAIL", judge("touch", "classic", ["classic", "touch"] + ["classic"] * 4)[0] == S.FAIL)
    prova("the phone context did not take ⇒ BLOCKED", judge("classic", "classic", ["classic"] * STORM)[0] == S.BLOCKED)
    prova("unreadable layout ⇒ BLOCKED", judge(None, "classic", ["classic"])[0] == S.BLOCKED)
    prova("no storm ⇒ BLOCKED", judge("touch", "classic", [])[0] == S.BLOCKED)
    print("⛔ CERTIFICATION FAILED" if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


def media(g, phone):
    """The phone's context (touch emulation on) or the computer's (off), CHECKED in the page."""
    g.cdp.call("Emulation.setTouchEmulationEnabled", enabled=phone, **({"maxTouchPoints": 5} if phone else {}))
    time.sleep(0.3)
    coarse, fine, n = g.js(READ_MEDIA)
    if phone and not (coarse and not fine):
        raise S.Blocked("the phone context did not take: (pointer: coarse) %s, (any-pointer: fine) %s" % (coarse, fine))
    if not phone and coarse:
        raise S.Blocked("the computer context did not come back: (pointer: coarse) still true")
    return n


def phone_on(g, geo, note):
    """The phone's media; one real tap if the page still remembers the login's mouse.  Returns the layout."""
    media(g, PHONE)
    lay = g.js(LAYOUT)
    if lay == "classic":
        x, y = S.C21.desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * 0.45)    # the empty desktop (no window is opened here)
        g.touches(x, y)
        time.sleep(0.4)
        lay = g.js(LAYOUT)
        note.append("one real tap first (the page remembered the login's mouse)")
    return lay


def play(g, geo, move):
    note = []
    after_phone = phone_on(g, geo, note)
    if move:
        for fx, fy in ((0.45, 0.5), (0.55, 0.55)):
            x, y = S.C21.desktop_to_glass(geo, geo["tl"] * fx, geo["ta"] * fy)
            g.move_to(x, y)
            time.sleep(0.15)
    time.sleep(0.3)
    after_move = g.js(LAYOUT)
    storm = []
    if move:
        n0 = g.js(READ_MEDIA)[2]
        for _ in range(STORM):
            media(g, FINE)
            media(g, PHONE)
            storm.append(g.js(LAYOUT))
        changes = g.js(READ_MEDIA)[2] - n0
        if changes < 2 * STORM:
            raise S.Blocked("only %d real media changes in the storm (%d expected): the storm did not happen" % (changes, 2 * STORM))
        note.append("%d real media changes" % changes)
    else:
        storm = [after_move]
    why = g.js("return REMOTIX.touch.why ? REMOTIX.touch.why() : null")
    e, m = judge(after_phone, after_move, storm)
    return e, m, "after the phone context «%s» · after %s «%s» · returns %s · why «%s»%s" % (
        after_phone, "the move" if move else "NO move", after_move, "/".join(map(str, storm)), why,
        (" · " + "; ".join(note)) if note else "")


def body(o, E):
    if o.browser != "chrome":
        raise S.Blocked("F-031C is Chrome's (Emulation.setTouchEmulationEnabled): --browser chrome")
    with S.Session(o, "933", E) as s:
        ok, m = s.enter()
        if not ok:
            raise S.Blocked("the session does not open: %s" % m)
        geo = s.geometry() or {}
        if not geo.get("tl"):
            raise S.Blocked("the canvas geometry is not readable")
        g = s.g
        try:
            if o.fault:                    # FIRST: nothing has been seen yet in the phone context
                e, m, obs = play(g, geo, False)
                seen = {S.FAIL: True, S.PASS: False}.get(e)
                E.fault("F-031C", seen,
                         {True: "without a mouse move the page stays touch: red, as it must",
                          False: "GREEN without any mouse move: the test would not see the defect",
                          None: "the fault could not be looked at: " + m}[seen],
                         expected="no mouse move ⇒ red", observed=obs)
            expected = "touch in the phone context; classic at the first real mouse move; classic through %d media changes" % STORM
            e, m, obs = play(g, geo, True)
            E.put("F-031C", e, m, expected=expected, observed=obs)
        finally:
            try:
                g.cdp.call("Emulation.setTouchEmulationEnabled", enabled=False)   # the browser's own answers again
            except Exception:                                                 # noqa: BLE001
                pass


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
