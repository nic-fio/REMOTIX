#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f010 — F-010 DESKTOP SHORTCUTS

    python3 15-f010-desktop-shortcuts.py --box xfce --browser firefox [--fault]

EXPECTED: the USE shortcuts reach the desktop and do their job; the
DANGEROUS ones (the screen lock) do NOT — the screen stays the desktop.

THE SCENE: in the tenant's session two KNOWN windows, GTK4 filled with a
pure colour — CYAN and then MAGENTA — 60% x 68% of the desktop in size, that is so
large that wherever the compositor puts them THEY OVERLAP (two widths exceed the
desktop).  They have different app_ids: on GNOME Alt+Tab switches between applications.

  1. use: Alt+Tab (REAL keys to the browser: CDP `Input.dispatchKeyEvent` on
     Chrome, W3C Marionette actions on Firefox, like C23).  From the PHOTO: the
     window that was on top (the one whose colour covers more pixels) goes
     below — the sign of (cyan - magenta) FLIPS.
  2. dangerous: Super+L, then Ctrl+Alt+L.  After 5 s the photo: the desktop is
     still that one (the two windows with their colour within 25%, luminance
     within 25 levels; a lock screen covers everything).
  3. and the desktop still ANSWERS: a second Alt+Tab flips again
     (a locked screen would swallow the key).

⚠ DECLARED: CDP and Marionette deliver the keys to the PAGE skipping the
  client's compositor and the browser's accelerators.  What is tested
  here is the stretch page → REMOTIX → desktop; that Alt+Tab or Super, on a
  real client, are kept by the client's operating system is declared
  by the page itself (`SC_CATALOG`, «non-consegnata») and is not F-010's.

FAULT (two, both must give red):
  A) instead of Alt+Tab only Tab is sent (the gesture without the modifier):
     the windows do not swap ⇒ the use judge must say RED;
  B) the judge of the dangerous ones is given, instead of the photo after Super+L,
     a BLACK canvas of the same size (what is seen if the screen locks
     or turns off) ⇒ it must say RED.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G1B = S._load("g1b", os.path.join(S.HERE, "15-g1b-common.py"))
FUNCTIONS = ("F-010",)

HEADROOM = 0.01          # minimum difference (fraction of the pixels) to say «on top»
REL_TOLERANCE = 0.25   # the desktop «is still that one»: colours within 25%
LUM_TOLERANCE = 25


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES (pure functions)
# ═══════════════════════════════════════════════════════════════════════════
def above(counts):
    """'ciano' | 'magenta' | None: who covers more pixels (with margin)."""
    c, m = counts[G1B.CYAN], counts[G1B.MAGENTA]
    if c < 0.01 and m < 0.01:
        return None
    if abs(c - m) < HEADROOM:
        return None
    return "ciano" if c > m else "magenta"


def swapped(before, after):
    """(outcome, sentence): VERDE if whoever was on top is now below."""
    a, b = above(before), above(after)
    sentence = "on top before: %s (c %.3f, m %.3f) · after: %s (c %.3f, m %.3f)" % (
        a, before[G1B.CYAN], before[G1B.MAGENTA], b, after[G1B.CYAN], after[G1B.MAGENTA])
    if a is None:
        return S.BLIND, "before the gesture it is not clear who is on top: " + sentence
    if b is None:
        return S.RED, "after the gesture the windows are no longer seen: " + sentence
    return (S.GREEN if a != b else S.RED), sentence


def still_there(ref, lum_ref, counts, lum):
    """(outcome, sentence): VERDE if the desktop is still the reference one."""
    troubles = []
    for clr, name in ((G1B.CYAN, "ciano"), (G1B.MAGENTA, "magenta")):
        r, v = ref[clr], counts[clr]
        if r > 0.01 and abs(v - r) > REL_TOLERANCE * r:
            troubles.append("%s %.3f → %.3f" % (name, r, v))
    if abs(lum - lum_ref) > LUM_TOLERANCE:
        troubles.append("luminance %.0f → %.0f" % (lum_ref, lum))
    sentence = "cyan %.3f, magenta %.3f, luminance %.0f" % (
        counts[G1B.CYAN], counts[G1B.MAGENTA], lum)
    return (S.RED, "the desktop is NO longer that one: " + "; ".join(troubles)) if troubles \
        else (S.GREEN, "the desktop is still there: " + sentence)


def certify():
    troubles = []

    def prova(what, real):
        print("%s %s" % ("⭐" if real else "⛔", what))
        if not real:
            troubles.append(what)

    C, M = G1B.CYAN, G1B.MAGENTA
    prova("real swap ⇒ GREEN", swapped({C: 0.2, M: 0.3}, {C: 0.3, M: 0.2})[0] == S.GREEN)
    prova("no swap ⇒ RED", swapped({C: 0.2, M: 0.3}, {C: 0.2, M: 0.3})[0] == S.RED)
    prova("windows vanished ⇒ RED", swapped({C: 0.2, M: 0.3}, {C: 0, M: 0})[0] == S.RED)
    prova("before, not clear ⇒ CIECO",
          swapped({C: 0.25, M: 0.255}, {C: 0.3, M: 0.2})[0] == S.BLIND)
    prova("same desktop ⇒ VERDE",
          still_there({C: 0.2, M: 0.3}, 120, {C: 0.21, M: 0.29}, 118)[0] == S.GREEN)
    prova("black screen ⇒ RED", still_there({C: 0.2, M: 0.3}, 120, {C: 0, M: 0}, 0)[0] == S.RED)
    prova("lock screen (colours gone, similar light) ⇒ ROSSO",
          still_there({C: 0.2, M: 0.3}, 120, {C: 0.0, M: 0.0}, 110)[0] == S.RED)
    nero = G1B.png_nero(64, 36)
    prova("the black canvas: no cyan, no magenta",
          G1B.count_colors(nero, (C, M)) == {C: 0.0, M: 0.0})
    print("⛔ %d problems" % len(troubles) if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def look(s, name):
    png, dove = G1B.photo(s, name, scale_factor=0.5)
    if not png:
        raise S.Blocked("photo failed (%s): %s" % (name, dove))
    return png, dove, G1B.count_colors(png, (G1B.CYAN, G1B.MAGENTA)), \
        G1B.mean_luminance(png)


def body(o, E):
    d = o.box
    with S.Session(o, "010", E) as s:
        G1B.step("tenant and browser ready")
        ok, m = s.enter()
        G1B.step("inside: %s" % m[:80])
        if not ok:
            raise S.Blocked(m)
        time.sleep(6 if d != "kde" else 10)
        geo = s.geometry()
        W, H = geo["tl"], geo["ta"]
        c, t = G1B.put_window(s)
        if c != 0:
            raise S.Blocked("the window's program cannot be written: " + t[-200:])
        lw, la = int(W * 0.60), int(H * 0.68)
        for name, clr in (("ciano", "#00ffff"), ("magenta", "#ff00ff")):
            c, t = G1B.open_window(s, name, clr, lw, la)
            if c != 0:
                raise S.Blocked("the window %s does not start: %s" % (name, t[-200:]))
            time.sleep(5)
        G1B.step("windows open")
        G1B.focus_on_canvas(s, geo)
        if d == "gnome":
            # ⚠ GNOME is born in the overview: ESC closes it (and on the desktop does nothing)
            G1B.combination(s.g, ["Escape"])
            time.sleep(2)
        ev = []
        png0, p0, k0, l0 = look(s, "scene")
        ev.append(p0)
        if above(k0) is None:
            ev.append(s.save_text("f010-scena.txt", "cyan %.3f magenta %.3f" % (
                k0[G1B.CYAN], k0[G1B.MAGENTA])))
            raise S.Blocked("the scene is not there: the two known windows are not seen or do not "
                             "overlap (cyan %.3f, magenta %.3f)"
                             % (k0[G1B.CYAN], k0[G1B.MAGENTA]))

        G1B.step("scene photographed")
        # 1. use
        G1B.combination(s.g, ["Alt", "Tab"])
        time.sleep(2.5)
        png1, p1, k1, l1 = look(s, "dopo-alt-tab")
        ev.append(p1)
        e1, f1 = swapped(k0, k1)

        G1B.step("Alt+Tab: %s" % f1)
        # 2. dangerous
        dangerous = []
        ref, lref = k1, l1
        after_super = None
        for keys, name in ((["Super", "l"], "super-l"), (["Control", "Alt", "l"], "ctrl-alt-l")):
            G1B.combination(s.g, keys)
            time.sleep(5)
            pngx, px, kx, lx = look(s, "dopo-" + name)
            ev.append(px)
            if after_super is None:
                after_super = pngx
            ex, fx = still_there(ref, lref, kx, lx)
            dangerous.append((name, ex, fx))

        G1B.step("dangerous: %s" % [p[1] for p in dangerous])
        # 3. still answers
        G1B.combination(s.g, ["Alt", "Tab"])
        time.sleep(2.5)
        png3, p3, k3, l3 = look(s, "dopo-secondo-alt-tab")
        ev.append(p3)
        e3, f3 = swapped(ref, k3)

        lines = ["1 Alt+Tab: %s · %s" % (S.C21.OUTCOME_NAME[e1], f1)]
        lines += ["2 %s: %s · %s" % (n, S.C21.OUTCOME_NAME[e], f) for n, e, f in dangerous]
        lines += ["3 second Alt+Tab: %s · %s" % (S.C21.OUTCOME_NAME[e3], f3)]
        ev.append(s.save_text("f010-giudizi.txt", lines))
        oss = " | ".join(lines)
        expected = ("Alt+Tab swaps the two known windows; after Super+L and Ctrl+Alt+L the "
                  "desktop is still there and a second Alt+Tab swaps them again")
        rossi = [r for r, e in zip(lines, [e1] + [p[1] for p in dangerous] + [e3])
                 if e == S.RED]
        blind = [r for r, e in zip(lines, [e1] + [p[1] for p in dangerous] + [e3])
                  if e == S.BLIND]
        if rossi:
            E.put("F-010", S.FAIL, " ; ".join(rossi), expected=expected, observed=oss,
                    evidence=ev)
        elif blind:
            E.put("F-010", S.BLOCKED, " ; ".join(blind), expected=expected, observed=oss,
                    evidence=ev)
        else:
            E.put("F-010", S.PASS, "Alt+Tab swaps (twice), Super+L and Ctrl+Alt+L "
                    "do not lock", expected=expected, observed=oss, evidence=ev)

        if o.fault:
            # A) only Tab, without Alt
            _pa, pa, ka, _la = look(s, "guasto-prima-del-tab")
            G1B.combination(s.g, ["Tab"])
            time.sleep(2.5)
            _pb, pb, kb, _lb = look(s, "guasto-dopo-il-tab")
            ea, fa = swapped(ka, kb)
            # B) the black canvas instead of the photo after Super+L
            w, h = G1B.png_size(after_super)
            nero = G1B.png_nero(w, h)
            eb, fb = still_there(ref, lref, G1B.count_colors(nero, (G1B.CYAN, G1B.MAGENTA)),
                               G1B.mean_luminance(nero))
            seen = (ea == S.RED) and (eb == S.RED)
            E.fault("F-010", None if ea == S.BLIND else seen,
                     "A) only Tab ⇒ %s (%s) · B) black canvas after Super+L ⇒ %s"
                     % (S.C21.OUTCOME_NAME[ea], fa, S.C21.OUTCOME_NAME[eb]),
                     evidence=[pa, pb])


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify))
