#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f011 — F-011 THE CANVAS AT ATTACH

    python3 15-f011-la-tela-all-attacco.py --container_box kde --browser chrome [--fault]
    python3 15-f011-la-tela-all-attacco.py --certify

F-011  expected: right after entering, the desktop has the size of the browser WINDOW
       reduced as `canvas_to_request()` of `src/pagina.html` (~2130) says:
         vista = floor(clientWidth x dpr) x floor(clientHeight x dpr)
                 (`view_size()`, truncated downwards)
         canvas_size  = each side clamped between the limits (320..7680 x 240..4320) and
                 truncated to the multiple of 16 (CANVAS_STEP_W = CANVAS_STEP_H = 16,
                 cure of 24 Sep 2026: Firefox with hardware decoding
                 drew a green strip on the right and at the bottom)
       and we look in THREE places, which must all say the expected size:
         · the server's FIELD: «the stage answers the canvas — asked WxH,
           OBTAINED WxH» in the box's log (the real desktop took it)
         · the page: the canvas in force (`REMOTIX_POINTER.geometry` tl x ta)
         · the PHOTO of the canvas at full resolution: its size
       and in the photo (two photos, 2 s apart):
         · no GREEN STRIP (0,76,0) in the last 16 columns and rows
           (the green is the decoding of a block of zeros: the historical defect)
         · no BAND at the edges: the outer edge (2 px) uniform AND different
           from the desktop 24 and 40 px further in = a padding, not the
           desktop.  A panel at its edge is uniform but it is the SAME
           colour 24 px inside too (the panels are >= 28 px tall); the background
           reaches the edge continuously.

FAULT (same session, the same real photos, three injections, all must
       give red):
         a) a (0,76,0) strip 8 px wide painted on the right of the real photo
         b) the size expectation shifted by 16 in width
         c) a uniform MAGENTA band 12 px tall painted at the bottom (a colour
            no desktop has: black or white ended up on an identical panel)

⚠ LIMIT: on a black background (XFCE) a BLACK band cannot be told apart from the
  background; the band is seen only if it differs from the desktop next to it.
"""
import io
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNCTIONS = ("F-011",)

# ⛔ The same numbers as src/pagina.html ~2127-2129 (verified on 24 Sep 2026)
L_MIN, L_MAX, A_MIN, A_MAX, STEP = 320, 7680, 240, 4320, 16
DEFECT_GREEN = (0, 76, 0)
TOL_GREEN = 24
STRIP = 16            # the columns/rows looked at for the green strip
QUOTA_GREEN = 0.5        # a column is «green» if half of its pixels are
EXTERNAL = 2              # the thickness of the outer edge looked at
INSIDE = (24, 40)        # where the desktop «next to it» is looked at
UNIFORM_DEV = 4.0       # deviation (per channel) below which the edge is uniform
DIFFERENT = 25.0           # mean difference per pixel beyond which it is «something else»

RE_GOT = re.compile(r"asked (\d+)x(\d+), OBTAINED (\d+)x(\d+)")


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def canvas_wait(cw, ch, dpr):
    """The rule of `view_size()` + `canvas_to_request()`."""
    import math
    v = [max(1, int(math.floor(cw * dpr))), max(1, int(math.floor(ch * dpr)))]

    def p(n, lo, hi):
        n = min(hi, max(lo, int(round(n))))
        return n - n % STEP
    return [p(v[0], L_MIN, L_MAX), p(v[1], A_MIN, A_MAX)]


def green_strip(im):
    """(found, description): columns on the right and rows at the bottom dominated by (0,76,0)."""
    w, h = im.size
    found = []

    def green_v(p):
        return all(abs(p[i] - DEFECT_GREEN[i]) <= TOL_GREEN for i in range(3))
    clr = im.crop((w - STRIP, 0, w, h))
    px = list(clr.getdata())
    for c in range(STRIP):
        n = sum(1 for y in range(h) if green_v(px[y * STRIP + c]))
        if n >= QUOTA_GREEN * h:
            found.append("column x=%d (%d%%)" % (w - STRIP + c, 100 * n // h))
    rig = im.crop((0, h - STRIP, w, h))
    px = list(rig.getdata())
    for r in range(STRIP):
        n = sum(1 for x in range(w) if green_v(px[r * w + x]))
        if n >= QUOTA_GREEN * w:
            found.append("row y=%d (%d%%)" % (h - STRIP + r, 100 * n // w))
    if found:
        return True, "strip (0,76,0): %d lines — %s" % (len(found), ", ".join(found[:4]))
    return False, "no (0,76,0) strip in the last %d columns and rows" % STRIP


def _edge(im, side, prof, thickness=EXTERNAL):
    w, h = im.size
    if side == "right_edge":
        return im.crop((w - prof - thickness, 0, w - prof, h))
    if side == "left_edge":
        return im.crop((prof, 0, prof + thickness, h))
    if side == "low":
        return im.crop((0, h - prof - thickness, w, h - prof))
    return im.crop((0, prof, w, prof + thickness))


def bands(im):
    """(found: [sides], description) — a uniform edge that is not the desktop."""
    from PIL import ImageChops, ImageStat
    found, note = [], []
    for side in ("right_edge", "low", "left_edge", "alto"):
        est = _edge(im, side, 0)
        st = ImageStat.Stat(est)
        dev = max(st.stddev)
        diff = []
        for d in INSIDE:
            den = _edge(im, side, d)
            diff.append(sum(ImageStat.Stat(ImageChops.difference(est, den)).mean) / 3.0)
        band = dev < UNIFORM_DEV and all(x > DIFFERENT for x in diff)
        note.append("%s: dev %.1f, diff %s%s" % (side, dev, "/".join("%.0f" % x for x in diff),
                                                 " ⛔ BAND" if band else ""))
        if band:
            found.append(side)
    return found, "; ".join(note)


def judge_measures(wait, got_server, page_v, picture):
    """(outcome, reason).  `got_server`, `page_v`, `picture`: [w,h] or None."""
    missing = [n for n, v in (("server", got_server), ("page_v", page_v), ("picture", picture))
             if not v]
    if missing:
        return S.BLOCKED, "I could not read the size from: %s" % ", ".join(missing)
    mistakes = ["%s %dx%d" % (n, v[0], v[1]) for n, v in
              (("server", got_server), ("page_v", page_v), ("picture", picture))
              if list(v) != list(wait)]
    if mistakes:
        return S.FAIL, ("expected %dx%d, but %s" % (wait[0], wait[1], ", ".join(mistakes)))
    return S.PASS, "server, page and photo all say %dx%d (the expected)" % tuple(wait)


def judge_photo(im):
    """(outcome, reason) of the photo: green strip and bands."""
    v, dv = green_strip(im)
    f, df = bands(im)
    if v or f:
        return S.FAIL, "%s · bands %s (%s)" % (dv, f or "none", df)
    return S.PASS, "%s · no band (%s)" % (dv, df)


def paint_strip(im, width_px=8, color=DEFECT_GREEN):
    from PIL import ImageDraw
    c = im.copy()
    w, h = c.size
    ImageDraw.Draw(c).rectangle((w - width_px, 0, w - 1, h - 1), fill=color)
    return c


def paint_bottom_band(im, thickness=12, color=(255, 0, 255)):
    """⭐ The injected band is MAGENTA: far from every real desktop (black,
    white, grey, blue).  `[M]` 24 Sep 2026, lxqt: a white band chosen
    by looking 30-60 px above ended up on a light panel and could not be told apart."""
    from PIL import ImageDraw
    c = im.copy()
    w, h = c.size
    ImageDraw.Draw(c).rectangle((0, h - thickness, w - 1, h - 1), fill=color)
    return c, color


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION
# ═══════════════════════════════════════════════════════════════════════════
def _fake_desktop(w=800, h=480, panel=32):
    """A shaded background with a dark panel at the top (with text)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for x in range(w):
        d.line((x, 0, x, h), fill=(30 + x * 150 // w, 60, 120 + x * 100 // w))
    d.rectangle((0, 0, w, panel - 1), fill=(20, 20, 20))
    for x in range(10, w - 10, 60):
        d.text((x, 10), "12:00", fill=(230, 230, 230))
    return im


def certify():
    troubles = []

    def ok(cond, what):
        print("%s %s" % ("⭐" if cond else "⛔", what))
        if not cond:
            troubles.append(what)
    ok(canvas_wait(3838, 2069, 1) == [3824, 2064], "3838x2069 dpr1 ⇒ 3824x2064 (measured on the server)")
    ok(canvas_wait(3840, 2160, 1) == [3840, 2160], "3840x2160 ⇒ itself")
    ok(canvas_wait(653, 400, 1.5) == [976, 592], "653x400 at dpr 1.5 ⇒ 979x600 ⇒ 976x592")
    ok(canvas_wait(100, 100, 1) == [320, 240], "below the minimum ⇒ 320x240")
    ok(canvas_wait(9000, 5000, 1) == [7680, 4320], "above the maximum ⇒ 7680x4320")
    im = _fake_desktop()
    e, m = judge_photo(im)
    ok(e == S.PASS, "fake desktop with a dark panel at the top ⇒ PASS (%s)" % m)
    e, m = judge_photo(paint_strip(im))
    ok(e == S.FAIL, "+ (0,76,0) strip 8 px on the right ⇒ FAIL (%s)" % m[:80])
    e, m = judge_photo(paint_strip(im, 3))
    ok(e == S.FAIL, "+ 3 px strip ⇒ FAIL")
    c, clr = paint_bottom_band(im)
    e, m = judge_photo(c)
    ok(e == S.FAIL, "+ band %s 12 px at the bottom ⇒ FAIL (%s)" % (clr, m[-90:]))
    from PIL import Image
    nero = Image.new("RGB", (800, 480))
    e, m = judge_photo(nero)
    ok(e == S.PASS, "all black (the XFCE background) ⇒ no band: declared limit")
    ok(judge_measures([3824, 2064], [3824, 2064], [3824, 2064], [3824, 2064])[0] == S.PASS,
       "three sizes equal to the expected ⇒ PASS")
    ok(judge_measures([3840, 2064], [3824, 2064], [3824, 2064], [3824, 2064])[0] == S.FAIL,
       "expectation shifted by 16 ⇒ FAIL")
    ok(judge_measures([3824, 2064], None, [3824, 2064], [3824, 2064])[0] == S.BLOCKED,
       "server size not read ⇒ BLOCKED")
    print("⭐ certification green" if not troubles else "⛔ %d problems" % len(troubles))
    return 0 if not troubles else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
JS_WINDOW = ("const d=document.documentElement; return [d.clientWidth, d.clientHeight, "
               "devicePixelRatio||1, innerWidth, innerHeight];")


def got_from_server(line_list):
    latest = None
    for r in line_list:
        m = RE_GOT.search(r)
        if m:
            latest = [int(m.group(3)), int(m.group(4))]
    return latest


def body_el(o, E):
    from PIL import Image
    with S.Session(o, "011", E) as s:
        sign = s.log_mark()
        ok, m = s.enter()
        if not ok:
            raise S.Blocked(m)
        cw, ch, dpr, iw, ih = s.g.js(JS_WINDOW)
        wait = canvas_wait(cw, ch, dpr)
        print("   window: client %dx%d (inner %dx%d) dpr %s ⇒ expected canvas %dx%d"
              % (cw, ch, iw, ih, dpr, wait[0], wait[1]), flush=True)
        # the server: the «OBTAINED» line with the expected size (or the last one, within 20 s)
        fine = time.time() + 20
        got, line_list = None, []
        while time.time() < fine:
            line_list = s.log_from(sign) if sign is not None else []
            got = got_from_server(line_list)
            geo = s.geometry() or {}
            if got == wait and [geo.get("tl"), geo.get("ta")] == wait:
                break
            time.sleep(1)
        time.sleep(2)                     # a few frames at the new size
        geo = s.geometry() or {}
        page_v = [geo.get("tl"), geo.get("ta")] if geo.get("tl") else None
        ev = [s.save_text("server-f011.txt", line_list)]
        picture = []
        for k in range(2):
            png, dove = s.picture("canvas_size-%d" % k)
            if not png:
                raise S.Blocked("the canvas cannot be photographed: %s" % dove)
            picture.append(Image.open(io.BytesIO(png)).convert("RGB"))
            ev.append(dove)
            if k == 0:
                time.sleep(2)
        screenshot_size = list(picture[-1].size) if dpr == 1 else None
        note_dpr = "" if dpr == 1 else " (dpr %s: the photo size is not compared)" % dpr
        if dpr != 1:
            screenshot_size = page_v
        e1, m1 = judge_measures(wait, got, page_v, screenshot_size)
        g_photo = [judge_photo(im) for im in picture]
        e2 = S.FAIL if any(x[0] == S.FAIL for x in g_photo) else S.PASS
        m2 = " | ".join("photo %d: %s" % (i, x[1]) for i, x in enumerate(g_photo))
        outcome = S.FAIL if S.FAIL in (e1, e2) else (S.BLOCKED if S.BLOCKED in (e1, e2) else S.PASS)
        rationale = "sizes: %s%s · %s" % (m1, note_dpr, m2)
        E.put("F-011", outcome, rationale if outcome != S.PASS else "canvas %dx%d like the window "
                "(%dx%d, dpr %s), no green strip, no bands" % (
                    wait[0], wait[1], cw, ch, dpr),
                expected_val="canvas %dx%d (client %dx%d at a multiple of 16), no (0,76,0) at the edges, "
                       "background up to the edge" % (wait[0], wait[1], cw, ch),
                observed=rationale, evidence=ev + [s.save_console()])

        if o.fault:
            if e1 != S.PASS or e2 != S.PASS:
                E.fault("F-011", None, "the healthy pass is not green: the fault is not injected "
                         "(%s)" % rationale[:200])
                return
            im = picture[-1]
            ga = judge_photo(paint_strip(im))
            gb = judge_measures([wait[0] + 16, wait[1]], got, page_v, screenshot_size)
            fc, color = paint_bottom_band(im)
            gc = judge_photo(fc)
            if o.evidence:
                p = os.path.join(o.evidence, "guasto-striscia-e-fascia.png")
                paint_bottom_band(paint_strip(im))[0].save(p)
            seen_items = [ga[0] == S.FAIL, gb[0] == S.FAIL, gc[0] == S.FAIL]
            E.fault("F-011", all(seen_items),
                     "strip (0,76,0) 8 px ⇒ %s · expected +16 ⇒ %s · band %s 12 px at the bottom "
                     "⇒ %s" % (ga[0], gb[0], color, gc[0]),
                     observed="a) %s | b) %s | c) %s" % (ga[1][:160], gb[1], gc[1][-200:]))


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify))
