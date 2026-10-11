#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f018b — F-018 REATTACH AT A DIFFERENT SIZE: THE WINDOWS ALL STAY INSIDE
           (the defect D-007)

    python3 15-f018b-finestre-dentro-al-riattacco.py --box xfce --browser firefox [--fault]

  G6's scene with a LARGE window (1800x1000): creation at 4K
  (browser window 3840x2160), the window is born centred and whole →
  DETACH → reattach with the browser window at 2560x1440.  Centred in the 4K,
  that window, at 2544x1344, sticks out by ~240 px on the right and ~160 at the bottom;
  its midpoint however stays inside, and labwc by itself does not move it
  (`src/sessione.h`, the box of `SESSION_LABWC_KEYBOARD`).

F-018b expected (D-007, decided by the user on 25 Sep 2026: «it must be cured»):
  photo: after the smaller reattach the scene's window is ENTIRELY inside
        the canvas — the cyan rectangle (the scene's page) has the SAME
        size, in desktop pixels, it had at 4K (± 3 %), and does not touch the
        edges.  ⇒ «Entirely inside» and also «moved, not shrunk»: it fits,
        and the product has no right to shrink it.
        ⚠ The edge alone is NOT enough: a window brought back inside sits
        right against the edge, to the pixel — and one cut by the edge touches it
        just the same.  The SIZE instead separates them: the cut one is shorter.
  ⭐ on all the desktops.  On GNOME Mutter brings it back inside, on KDE KWin
        (nested since 11 Oct 2026, `src/kwin.h`: the canvas changes there too),
        on XFCE and LXQt (labwc) the product does.

FAULT: the 4K photo of the creation, cut to the NEW size from the top-left
        corner — that is what is seen if at the reattach nobody moves
        the windows (the cure off: labwc leaves the window where it was, and
        the smaller output shows its corner) ⇒ the judge must say RED.
        And the cure REALLY off is tried by starting the standard server
        (`15-d007-server.sh start xfce stock`): same scene, RED.
"""
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._load("g6", os.path.join(S.HERE, "15-g6-comune.py"))
F16 = S._load("f016", os.path.join(S.HERE, "15-f016-stacco-e-riattacco.py"))
FUNCTIONS = ("F-018b", "F-018c")
WINDOW = (1800, 1000)       # centred in 3776x2016 it sticks out of 2544x1344; it fits
NEW_SIZE = (2560, 1440)
TOL_SIZE = 0.03            # the window must have the previous size (± 3 %)
MARGIN_4K = 4                # at 4K the window must not touch the edges (photo px)
WAIT_FIX_S = 15.0          # how long the photo is looked at again after the reattach
TOL_POS = 8                # desktop px: the photo is reduced to 960 (~4 px at 4K)


def cyan_in_px(v, canvas):
    """The cyan rectangle of `look_scene` in CANVAS (desktop) pixels:
    (x0, y0, width, height) or None."""
    if not v or not v.get("window") or not v.get("size") or not canvas:
        return None
    w, h = v["size"]
    x0, y0, x1, y1 = v["window"]
    sx, sy = canvas[0] / float(w), canvas[1] / float(h)
    return (x0 * sx, y0 * sy, (x1 - x0 + 1) * sx, (y1 - y0 + 1) * sy)


def judge_inside(before, after):
    """⭐ F-018b.  prima/dopo: {"window": (x0,y0,x1,y1) in the photo,
    "size": (w,h) of the photo, "canvas": (W,H) in desktop px}.
    Returns (outcome, reason)."""
    a = cyan_in_px(before, before.get("canvas"))
    if not a:
        return S.BLOCKED, "at 4K the scene's window is not seen: nothing to compare"
    w, h = before["size"]
    x0, y0, x1, y1 = before["window"]
    if x0 < MARGIN_4K or y0 < MARGIN_4K or x1 > w - 1 - MARGIN_4K or y1 > h - 1 - MARGIN_4K:
        return S.BLOCKED, ("at 4K the window already touches an edge (%s in %dx%d): the scene is not "
                           "the intended one" % (before["window"], w, h))
    b = cyan_in_px(after, after.get("canvas"))
    if not b:
        return S.FAIL, "after the reattach the scene's window is not seen (%s)" % (
            (after or {}).get("why") or "no cyan")
    dl, da = b[2] / a[2], b[3] / a[3]
    probs = []
    if dl < 1 - TOL_SIZE or da < 1 - TOL_SIZE:
        # cut by the edge (outside) or shrunk: both NO
        bw, bh = after["size"]
        bx0, by0, bx1, by1 = after["window"]
        touches = [n for n, t in (("right", bx1 >= bw - 2), ("bottom", by1 >= bh - 2),
                                ("left", bx0 <= 1), ("top", by0 <= 1)) if t]
        probs.append("the window is seen at %.0fx%.0f, at 4K it was %.0fx%.0f (%.0f %% x %.0f %%)%s"
                     % (b[2], b[3], a[2], a[3], 100 * dl, 100 * da,
                        (": CUT by the %s edge — it is partly OUTSIDE the screen"
                         % "/".join(touches)) if touches else
                        ": it was SHRUNK although it fits"))
    elif dl > 1 + TOL_SIZE or da > 1 + TOL_SIZE:
        probs.append("the window is seen at %.0fx%.0f, at 4K it was %.0fx%.0f: larger? the "
                     "photo does not add up" % (b[2], b[3], a[2], a[3]))
    if probs:
        return S.FAIL, "; ".join(probs)
    return S.PASS, ("whole window %.0fx%.0f (at 4K %.0fx%.0f) at (%.0f,%.0f) of the canvas "
                    "%dx%d" % (b[2], b[3], a[2], a[3], b[0], b[1], after["canvas"][0],
                               after["canvas"][1]))


def judge_going_back(before, after, same_slot):
    """⭐ F-018c: back at the starting size the window is whole and of the
    previous size; with `same_slot` (labwc) also in the previous place."""
    e, r = judge_inside(before, after)
    if e != S.PASS or not same_slot:
        return e, r
    a = cyan_in_px(before, before.get("canvas"))
    b = cyan_in_px(after, after.get("canvas"))
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) > TOL_POS or abs(dy) > TOL_POS:
        return S.FAIL, ("back at 4K the window is whole but MOVED by (%+.0f, %+.0f) px "
                        "relative to the creation: the shortcut moved a window that "
                        "was already inside" % (dx, dy))
    return S.PASS, "%s · in the previous place (%+.0f, %+.0f px)" % (r, dx, dy)


def trim(png, largo, alto):
    """⛔ The FAULT: the full-resolution photo cut to largo x alto
    from the top-left corner — the smaller screen with the windows
    left where they were."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    report = io.BytesIO()
    im.crop((0, 0, min(largo, im.size[0]), min(alto, im.size[1]))).save(report, "PNG")
    return report.getvalue()


def look_png(png):
    """`look_scene` on a png already in hand (the fault)."""
    im = G.bitmap(png)
    r, why = G.find_cyan(im)
    return {"window": list(r) if r else None, "size": list(im.size), "why": why}


# ═══════════════════════════════════════════════════════════════════════════
def certify():
    ok = True

    def prova(what, real):
        nonlocal ok
        ok &= bool(real)
        print("%s %s" % ("⭐" if real else "⛔", what))

    from PIL import Image, ImageDraw

    def photo(canvas, rect, largo=960):
        """A canvas `canvas` with the cyan rectangle `rect` (desktop px), reduced
        as `G.immagine` reduces it: (view, png)."""
        im = Image.new("RGB", canvas, (40, 40, 60))
        ImageDraw.Draw(im).rectangle(rect, fill=G.CYAN)
        f = io.BytesIO()
        im.save(f, "PNG")
        png = f.getvalue()
        v = look_png(png)
        v["canvas"] = list(canvas)
        return v, png

    A, pngA = photo((3776, 2016), (988, 522, 988 + 1799, 522 + 999))
    B, _ = photo((2544, 1344), (743, 343, 743 + 1799, 343 + 999))
    e, m = judge_inside(A, B)
    prova("brought back inside, same size ⇒ PASS (%s)" % m[:60], e == S.PASS)
    Bb, _ = photo((2544, 1344), (743, 343, 2543, 1343))           # against the edge, to the pixel
    e, m = judge_inside(A, Bb)
    prova("against the right/bottom edge but whole ⇒ PASS", e == S.PASS)
    T = look_png(trim(pngA, 2544, 1344))
    T["canvas"] = [2544, 1344]
    e, m = judge_inside(A, T)
    prova("fault: 4K cut (cure off) ⇒ FAIL (%s)" % m[:70], e == S.FAIL)
    Bp, _ = photo((2544, 1344), (100, 100, 100 + 1399, 100 + 799))   # inside but narrow
    e, m = judge_inside(A, Bp)
    prova("shrunk although it fits ⇒ FAIL", e == S.FAIL)
    e, _ = judge_inside(A, {"window": None, "size": [960, 507], "canvas": [2544, 1344]})
    prova("window gone ⇒ FAIL", e == S.FAIL)
    Ab, _ = photo((3776, 2016), (3000, 522, 3775, 1521))
    e, _ = judge_inside(Ab, B)
    prova("at 4K already against the edge ⇒ BLOCKED (wrong scene)", e == S.BLOCKED)
    K, _ = photo((3776, 2016), (988, 522, 988 + 1799, 522 + 999))   # KDE: canvas kept
    e, _ = judge_inside(A, K)
    prova("kde: canvas kept, whole window ⇒ PASS", e == S.PASS)
    e, m = judge_going_back(A, dict(A), True)
    prova("back at 4K in the previous place ⇒ PASS (%s)" % m[-40:], e == S.PASS)
    Cs, _ = photo((3776, 2016), (988, 522 + 13, 988 + 1799, 522 + 13 + 999))
    e, m = judge_going_back(A, Cs, True)
    prova("fault: back, moved down by half a bar (13 px) ⇒ FAIL (%s)" % m[:60], e == S.FAIL)
    e, _ = judge_going_back(A, Cs, False)
    prova("gnome/kde: the place is not judged ⇒ PASS", e == S.PASS)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def observe(s, name):
    ob = G.wait_canvas_still(s)
    v = G.look_scene(s, name)
    v["canvas"] = ob.get("buffer")
    v["view"] = ob.get("view")
    return v


def brief(v):
    return "canvas %s · view %s · cyan %s (desktop px %s)" % (
        v.get("canvas"), (v.get("view") or [None])[:2], v.get("window"),
        [round(x) for x in (cyan_in_px(v, v.get("canvas")) or [])])


def body(o, E):
    with S.Session(o, "918", E) as s:
        try:
            if o.ssd:
                # ⭐ the scene's window with labwc's title bar (the
                #   «with the bar» road of the shortcut, that of the Qt apps of
                #   LXQt): a rule in the USER's rc.xml, which on XFCE labwc
                #   adds to ours (`-m`).  ⚠ Before the login: labwc reads the
                #   configuration when it is born.
                if o.box != "xfce":
                    raise S.Blocked("--ssd holds only on xfce: on LXQt labwc's configuration "
                                     "belongs only to the product (-C)")
                c, t = s.sc.inside(
                    "h=/home/{c}; install -d -o {c} -g {c} $h/.config $h/.config/labwc; "
                    "printf '%s\\n' '<?xml version=\"1.0\"?><labwc_config><windowRules>"
                    "<windowRule identifier=\"firefox*\" serverDecoration=\"yes\"/>"
                    "</windowRules></labwc_config>' > $h/.config/labwc/rc.xml; "
                    "chown {c}: $h/.config/labwc/rc.xml; cat $h/.config/labwc/rc.xml"
                    .format(c=s.chi), 30)
                print("   --ssd: the user's rc.xml: %s" % t.strip()[-160:], flush=True)
            ok, m = s.enter()
            if not ok:
                raise S.Blocked("without login there is nothing to reattach: " + m)
            ok, t = G.turn_on_scene(s, WINDOW)
            if not ok:
                raise S.Blocked("the scene does not start in the session: " + t[-200:])
            G.wake(s)
            v = F16.find_scene(s)
            if not v.get("window"):
                raise S.Blocked("the scene's window is not seen in the photo: %s"
                                 % v.get("why"))
            time.sleep(2)
            A = observe(s, "A-4k")
            print("   A (creation): %s" % brief(A), flush=True)
            if not A.get("canvas") or not A.get("window"):
                raise S.Blocked("at 4K the canvas or the window cannot be read: %s" % brief(A))

            # ── DETACH and smaller reattach
            s.turn_off_browser()
            time.sleep(2)
            mis = G.turn_on_at_size(s, *NEW_SIZE)
            print("   browser restarted at %dx%d: view %s" % (NEW_SIZE + (mis,)), flush=True)
            ok, m, _ref, _sec = G.enter_with_retry(s, cap_s=40)
            if not ok:
                E.put("F-018b", S.FAIL, "the reattach at %dx%d does not get in: %s"
                        % (NEW_SIZE + (m,)))
                return
            G.wake(s)
            fine = time.time() + WAIT_FIX_S
            while True:
                B = observe(s, "B-2560")
                eB, rB = judge_inside(A, B)
                if eB == S.PASS or time.time() > fine:
                    break
                time.sleep(1.5)
            print("   B (reattach): %s" % brief(B), flush=True)
            if B.get("canvas") and A.get("canvas") \
                    and abs(B["canvas"][0] - A["canvas"][0]) < 64:
                raise S.Blocked("the canvas did not change size (%s → %s): the reattach is not "
                                 "«smaller»" % (A["canvas"], B["canvas"]))
            ev = [x for x in (A.get("photo"), B.get("photo")) if x]
            E.put("F-018b", eB, rB,
                    expected="the scene's window ENTIRELY inside the canvas, of the previous "
                           "size (moved, not shrunk)",
                    observed="A: %s || B: %s" % (brief(A), brief(B)), evidence=ev)

            # ── and BACK at 4K: the window comes back whole, and on labwc WHERE IT WAS —
            #    labwc restores the position from before the size changes
            #    (`last_layout_geometry`), and the product's shortcut, on a
            #    window already inside, must NOT move it by one pixel (if it
            #    moved it — half a title bar down, the risk of
            #    `MoveToCursor` — it would be seen here)
            s.turn_off_browser()
            time.sleep(2)
            G.turn_on_at_size(s, 3840, 2160)
            ok, m, _ref, _sec = G.enter_with_retry(s, cap_s=40)
            if not ok:
                E.put("F-018c", S.FAIL, "the reattach back at 4K does not get in: %s" % m)
            else:
                G.wake(s)
                time.sleep(2)
                C = observe(s, "C-4k")
                print("   C (back at 4K): %s" % brief(C), flush=True)
                eC, rC = judge_going_back(A, C, o.box in ("xfce", "lxqt"))
                E.put("F-018c", eC, rC,
                        expected="back at 4K the window whole, of the previous size; on "
                               "labwc also in the previous place (± %d px)" % TOL_POS,
                        observed="A: %s || C: %s" % (brief(A), brief(C)),
                        evidence=[x for x in (A.get("photo"), C.get("photo")) if x])
                if o.fault:
                    # the window moved down by half a title bar (13 px): RED
                    Cg = dict(C, window=[C["window"][0], C["window"][1] + 4,
                                           C["window"][2], C["window"][3] + 4]) \
                        if C.get("window") else C
                    g, r = judge_going_back(A, Cg, True)
                    E.fault("F-018c", g == S.FAIL, "C's window moved down by ~16 px ⇒ %s "
                             "(%s)" % (g, r[:160]))

            if o.fault:
                if not A.get("png"):
                    E.fault("F-018b", None, "the 4K photo is no longer there: nothing to cut")
                else:
                    tl, ta = B.get("canvas") or (NEW_SIZE[0] - 16, NEW_SIZE[1] - 96)
                    T = look_png(trim(A["png"], int(tl), int(ta)))
                    T["canvas"] = [int(tl), int(ta)]
                    g, r = judge_inside(A, T)
                    E.fault("F-018b", g == S.FAIL,
                             "the 4K cut to %dx%d (the windows left where they were) ⇒ %s (%s)"
                             % (tl, ta, g, r[:200]))
        finally:
            if s.g:
                s.save_console()
            G.turn_off_server(s)


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body, certify,
                      extra=lambda a: a.add_argument(
                          "--ssd", action="store_true",
                          help="(xfce) the scene's window with labwc's title bar: "
                               "the «with the bar» road of the cure")))
