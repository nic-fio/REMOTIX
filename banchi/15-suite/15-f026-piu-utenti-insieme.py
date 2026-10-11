#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f026 — F-026 SEVERAL USERS TOGETHER: each one sees THEIR OWN session, and writes only in it

    python3 15-f026-piu-utenti-insieme.py --box xfce --browser chrome --base-port 4920 [--fault] [--tenants 3]

Normal server of the box (85xx).  N tenants (2 normally, up to 3:
`c15026u<n>`), each with THEIR OWN real browser of the same type (porte-base,
+50, +54: 4K windows together in the labwc), all in TOGETHER.  In each one's
session a `firefox-esr --kiosk` scene of a COLOUR of their own (red, green,
magenta) with a focused text field; a small server writes down in the
tenant's home every key and every value of the field.

THE EXPECTATION (SPECIFICHE §5.5 «each one their own remote graphical session,
independent»):
  image     the canvas of each browser is covered by ITS OWN colour (>= 50 %) and does not
            show those of the others (<= 3 % each) — PHOTO;
  input     a different word for each one, typed with REAL KEYS in their
            browser, in turn: at the end the field of each one's scene is
            EXACTLY their word, and nobody received keys of the others
            (field value and notebook of the keys, in the session).

FAULTS (after the healthy pass, same sessions):
  image     the second tenant's scene repaints itself with the colour of the FIRST (the
            colour file changes: it is the scene, not the judge) ⇒ the image judge
            must say red;
  input     the first one's word is typed in the SECOND one's browser (the gesture goes
            to the wrong tenant) ⇒ the input judge must say red.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._load("g8", os.path.join(S.HERE, "15-g8-comune.py"))
FUNCTIONS = ("F-026",)
COLORS = {"red": (220, 40, 40), "green": (40, 190, 60), "magenta": (200, 40, 200)}
NAMES = ("red", "green", "magenta")
WORDS = ("alfa", "bravo", "xyz")        # different letters: someone else's key shows
MIN_SHARE = 0.5
OTHERS_MAX = 0.03


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def judge_images(fractions, names):
    """`fractions[i]` = {colour: fraction} of tenant i's canvas."""
    troubles = []
    for i, fr in enumerate(fractions):
        if fr is None:
            return S.BLOCKED, "tenant %d's canvas cannot be photographed" % (i + 1)
        if fr.get(names[i], 0) < MIN_SHARE:
            troubles.append("%d: ITS OWN %s covers only %.1f%%" % (i + 1, names[i], 100 * fr.get(names[i], 0)))
        for j, n in enumerate(names):
            if j != i and fr.get(n, 0) > OTHERS_MAX:
                troubles.append("%d: shows the %s of tenant %d (%.1f%%)" % (
                    i + 1, n, j + 1, 100 * fr[n]))
    if troubles:
        return S.FAIL, "; ".join(troubles)
    return S.PASS, " · ".join("%d sees %s %.0f%%" % (i + 1, names[i], 100 * fr[names[i]])
                              for i, fr in enumerate(fractions))


def judge_input(values, keys, words):
    """`values[i]` = final value of the field, `keys[i]` = keys received."""
    troubles = []
    for i, v in enumerate(values):
        if v is None:
            return S.BLOCKED, "tenant %d's notebook cannot be read" % (i + 1)
        if v != words[i]:
            troubles.append("%d: the field is «%s», expected «%s»" % (i + 1, v, words[i]))
        stray = [k for k in keys[i] if len(k) == 1 and k not in words[i]]
        if stray:
            troubles.append("%d: received someone else's keys %s" % (i + 1, "".join(stray)))
    if troubles:
        return S.FAIL, "; ".join(troubles)
    return S.PASS, " · ".join("%d «%s»" % (i + 1, v) for i, v in enumerate(values))


def certify():
    ok = True

    def prova(what, real):
        nonlocal ok
        ok &= bool(real)
        print("%s %s" % ("⭐" if real else "⛔", what))
    n = NAMES[:2]
    good = [{"red": 0.9, "green": 0.0}, {"red": 0.0, "green": 0.9}]
    prova("each their own ⇒ PASS", judge_images(good, n)[0] == S.PASS)
    prova("the second sees the red ⇒ FAIL", judge_images(
        [good[0], {"red": 0.9, "green": 0.0}], n)[0] == S.FAIL)
    prova("half and half ⇒ FAIL", judge_images(
        [good[0], {"red": 0.2, "green": 0.6}], n)[0] == S.FAIL)
    prova("photo missing ⇒ BLOCKED", judge_images([good[0], None], n)[0] == S.BLOCKED)
    p = WORDS[:2]
    prova("right words ⇒ PASS", judge_input(["alfa", "bravo"], [list("alfa"), list("bravo")], p)[0] == S.PASS)
    prova("word in the wrong place ⇒ FAIL", judge_input(
        ["", "bravoalfa"], [[], list("bravoalfa")], p)[0] == S.FAIL)
    prova("foreign key ⇒ FAIL", judge_input(
        ["alfa", "bravo"], [list("alfa") + ["x"], list("bravo")], p)[0] == S.FAIL)
    # the fractions on a synthetic photo
    from PIL import Image
    import io
    im = Image.new("RGB", (100, 50), COLORS["green"])
    im.paste(COLORS["red"], (0, 0, 10, 50))
    b = io.BytesIO()
    im.save(b, "PNG")
    fr = G.fractions(b.getvalue(), COLORS, reduce=1)
    prova("fractions: green 90%%, red 10%% (%s)" % G.fr_text(fr),
          abs(fr["green"] - 0.9) < 0.01 and abs(fr["red"] - 0.1) < 0.01 and fr["magenta"] == 0)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def extra(a):
    a.add_argument("--tenants", type=int, default=2, choices=(2, 3))


def front(s):
    """(Nothing to do: see `browser_per` — the Chrome window is always on top.)"""
    return


def browser_per(o, i, n):
    """⛔ THE CHROME COLUMN: Chrome for the LAST tenant, Firefox for the others.

    `[M]` 25 Sep 2026: under Wayland (labwc) a Chrome window COVERED by
    another no longer receives «frame callbacks», does not repaint, and its
    CDP photo (`Page.captureScreenshot`) waits FOREVER — F-026 hung for
    15 minutes on gnome, xfce, lxqt; neither `Page.bringToFront`, nor the options
    against occlusion, nor minimising the others (a Wayland client cannot
    come back from minimised by itself) are enough.  Firefox instead can be photographed even
    when covered.  ⇒ Two users with two different browsers (a real case), Chrome created
    LAST and therefore on top.  Declared in the report."""
    o2 = G.o_per(o, i)
    if o.browser == "chrome":
        if i < n - 1:
            o2.browser = "firefox"
            o2.base_port = o.base_port + G.MOVE_BROWSER[i + 1]
        else:
            o2.base_port = o.base_port
    return o2


def snapshot_all(sess, names, label):
    frs, ev = [], []
    for i, s in enumerate(sess):
        front(s)
        png, dove = s.photo("%s-%d-%s" % (label, i + 1, names[i]))
        frs.append(G.fractions(png, COLORS) if png else None)
        if dove:
            ev.append(dove)
    return frs, ev


def beat(s, password):
    front(s)
    G.click_center(s)
    time.sleep(0.8)
    G.C23.send_msg(s.g, G.C23.write(password))


def read_all(sess):
    val, kbd = [], []
    for s in sess:
        q = G.notebook(s.sc, s.chi)
        val.append(G.value(q))
        kbd.append(G.keys(q))
    return val, kbd


def body(o, E):
    n = o.tenants
    names, words = NAMES[:n], WORDS[:n]
    sess = []
    try:
        for i in range(n):
            s = S.Session(browser_per(o, i, n), "026", E)
            s.__enter__()
            sess.append(s)
            ok, m = s.enter()
            if not ok:
                raise S.Blocked("tenant %d (%s) does not get in: %s" % (i + 1, s.chi, m))
            print("   ⭐ %d %s (%s) in: %s" % (i + 1, s.chi, s.o.browser, m[:70]), flush=True)
            front(s)
            S.C21.wake(s.g, s.geometry())
            ok, t = G.turn_on_scene(s.sc, s.chi, o.base_port + G.MOVE_SCENE + i,
                                    COLORS[names[i]])
            if not ok:
                raise S.Blocked("the %s scene of %s does not start: %s"
                                 % (names[i], s.chi, " | ".join(t.splitlines()[-6:])[-400:]))
        # all in, each with their scene: wait for each one to be seen
        for i, s in enumerate(sess):
            front(s)
            fr, _d, why = G.wait_color(s, "attesa-%d" % (i + 1), COLORS, names[i],
                                              MIN_SHARE, 40)
            print("   canvas %d: %s %s" % (i + 1, G.fr_text(fr), why), flush=True)
        # ── the image ──────────────────────────────────────────────────────
        frs, ev = snapshot_all(sess, names, "immagine")
        ei, ri = judge_images(frs, names)
        print("   image: %s — %s" % (ei, ri), flush=True)
        # ── the input, in turn ─────────────────────────────────────────────
        for i, s in enumerate(sess):
            beat(s, words[i])
            time.sleep(2.5)
        time.sleep(2)
        val, kbd = read_all(sess)
        ein, rin = judge_input(val, kbd, words)
        print("   input: %s — %s" % (ein, rin), flush=True)
        _f, ev2 = snapshot_all(sess, names, "dopo-input")
        chi = [s.chi for s in sess]
        lines = []
        for s in sess:
            lines += ["## %s" % s.chi] + [r for r in s.log_from(0)
                                          if "session open" in r or "slot" in r][-6:]
        ev.append(sess[0].save_text("f026-server.txt", lines))
        all_items = [ei, ein]
        outcome = S.FAIL if S.FAIL in all_items else (S.BLOCKED if S.BLOCKED in all_items else S.PASS)
        E.put("F-026", outcome, "image %s · input %s" % (ei, ein),
                expected="%d tenants together (%s): each one sees ITS OWN colour and not the others; "
                       "their word ends up ONLY in their field" % (n, ", ".join(chi)),
                observed="image: %s | input: %s" % (ri, rin), evidence=ev + ev2)

        if o.fault:
            # image: the second one's scene takes the colour of the first
            G.change_color(sess[1].sc, sess[1].chi, COLORS[names[0]])
            front(sess[1])
            G.wait_color(sess[1], "guasto-attesa", COLORS, names[0], MIN_SHARE, 20)
            frs, _e = snapshot_all(sess, names, "guasto-immagine")
            eg1, rg1 = judge_images(frs, names)
            G.change_color(sess[1].sc, sess[1].chi, COLORS[names[1]])
            # input: the first one's word in the second one's browser
            beat(sess[1], words[0])
            time.sleep(3)
            val, kbd = read_all(sess)
            eg2, rg2 = judge_input(val, kbd, words)
            v1 = eg1 == S.FAIL if eg1 != S.BLOCKED else None
            v2 = eg2 == S.FAIL if eg2 != S.BLOCKED else None
            seen = None if None in (v1, v2) else (v1 and v2)
            E.fault("F-026", seen, "scene of 2 with the colour of 1 ⇒ %s (%s) · word of 1 in "
                     "the browser of 2 ⇒ %s (%s)" % (eg1, rg1[:100], eg2, rg2[:100]))
    finally:
        for s in reversed(sess):
            try:
                s.__exit__(None, None, None)
            except Exception as e:               # noqa: BLE001
                print("   ⚠ exit of %s: %s" % (s.chi, e))


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify, extra))
