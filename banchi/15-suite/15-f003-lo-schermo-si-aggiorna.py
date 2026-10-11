#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f003 — F-003 THE SCREEN UPDATE

    python3 15-f003-lo-schermo-si-aggiorna.py --box kde --browser chrome [--fault]
    python3 15-f003-lo-schermo-si-aggiorna.py --certify

The scene: C21's known window (NORMAL `firefox-esr` in the session, page
with a CYAN background and a YELLOW box, 45 % x 55 % of the screen, size fixed
in the profile) — plus a COUNTER: 15 white/black cells at the bottom of the
page writing in binary n = floor(Date.now() / 200 ms) mod 4096, that is
the page CHANGES every 200 ms.  (White guard, black guard, 12 bits, parity.)
⭐ The counter is a clock: `firefox-esr` in the box and the bench run
on the SAME machine (podman, same clock), so every photo also says
HOW old the image it shows is.

F-003, four parts in a row (like a real user), all from the PHOTO
of the canvas at full resolution:
  apre     first the photo has no cyan; the window is opened ⇒ the photo shows it
           (the cyan rectangle, at least 70 % as wide as what was requested)
  cambia   6 s of photos one after the other: every photo reads the counter, and
           the image must not be older than CAP_MS (1 s) relative to
           the instant the photo was REQUESTED (the measurement favours the
           product: if it comes out old, it surely is); no photo equal to the
           previous one if >= 400 ms passed between the two; at least 3 different
           values; at most a quarter of the photos unreadable
  sposta   the window is dragged by the TITLE BAR with the browser's mouse
           (real events: Marionette / CDP), by +320,+120 px: the bar is not
           in the same place on all desktops (Firefox with the tabs in the
           bar, or the desktop's bar above), so a ladder of
           grips above the cyan is tried, in the centre, stopping at the first one that moves
           ⇒ the photo shows the cyan ELSEWHERE (moved by at least 100 px), of the
           same size (±8 px)
  chiude   the window is closed (`firefox-esr` terminated in the session)
           ⇒ within 10 s the photo has no more cyan

FAULT («the old photo»): each part is re-judged on the photo from BEFORE the
change — the opening on the photo without the window, the rapid changes on the FIRST
photo repeated with the real instants, the move on the photo from before the
gesture, the closing on the last photo with the window open.  All four
must give red.

⚠ The judgment of «cambia» is a CAP on the delay (1 s), not the latency: the
  latency is measured by phase 16.
"""
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

C21 = S.C21
F011 = S._load("f011", os.path.join(S.HERE, "15-f011-la-tela-all-attacco.py"))
FUNCTIONS = ("F-003",)

PERIOD_MS = 200
BIT = 12
MODULE = 1 << BIT
CELLS = 2 + BIT + 1                 # white guard, black guard, 12 bits, parity
CELL_X0, CELL_STEP, CELL_W = 0.03, 0.063, 0.05      # fractions of the page
CELL_Y0, CELL_H = 0.62, 0.24
CAP_MS = 1000.0                   # the image no older than this
QUICK_S = 6.0
PHOTO_MIN = 8
QUICK_MAX_S = 30.0
STILL_MS = 400.0                    # two photos this far apart must differ
MOVE = (320, 120)                 # the drag, in desktop pixels
GRAB_DYS = (-62, -70, -54, -80, -100, -110, -46, -90, -120, -130)
MIN_MOVE = 100
SAME_SIZE_TOL = 8
CLOSED_S = 10.0
OPENING_S = 120.0                # [M] 24 Sep 2026, load 51: firefox-esr takes ~50 s to appear
CYAN_ABSENT = 0.001               # share of cyan pixels below which «it is not there»

PAGE = C21.PAGE.replace("REMOTIX C21", "REMOTIX F-003") + r"""
<script>
(function () {
  const N = %(celle)d, B = %(bit)d, celle = [];
  for (let i = 0; i < N; i++) {
    const d = document.createElement('div');
    d.style.cssText = 'position:absolute;top:%(y0)s%%;height:%(a)s%%;width:%(l)s%%;left:'
      + (%(x0)s + i * %(step)s) + '%%;background:#000';
    document.body.appendChild(d); celle.push(d);
  }
  let ultimo = -1;
  function giro() {
    const n = Math.floor(Date.now() / %(periodo)d) %% %(module)d;
    if (n === ultimo) return;
    ultimo = n;
    const b = [1, 0];
    let p = 0;
    for (let k = B - 1; k >= 0; k--) { const v = (n >> k) & 1; b.push(v); p ^= v; }
    b.push(p);
    for (let i = 0; i < N; i++) celle[i].style.background = b[i] ? '#fff' : '#000';
  }
  giro();
  setInterval(giro, 20);
})();
</script>
""" % {"celle": CELLS, "bit": BIT, "y0": CELL_Y0 * 100, "a": CELL_H * 100,
       "l": CELL_W * 100, "x0": CELL_X0 * 100, "step": CELL_STEP * 100,
       "periodo": PERIOD_MS, "module": MODULE}


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def bit_di(n):
    b = [1, 0]
    p = 0
    for k in range(BIT - 1, -1, -1):
        v = (n >> k) & 1
        b.append(v)
        p ^= v
    return b + [p]


def cell_centers(rect):
    """rett = [x0, y0, x1, y1] of the page in the photo ⇒ [(x, y, half_w, half_h)]."""
    x0, y0, x1, y1 = rect
    w, h = x1 - x0 + 1, y1 - y0 + 1
    y = y0 + (CELL_Y0 + CELL_H / 2) * h
    return [(x0 + (CELL_X0 + i * CELL_STEP + CELL_W / 2) * w, y,
             CELL_W * w * 0.25, CELL_H * h * 0.25) for i in range(CELLS)]


def read_counter(im, rect):
    """(n | None, reason) from the page's counter in the photo `im` (PIL RGB)."""
    from PIL import ImageStat
    b = []
    for x, y, ml, ma in cell_centers(rect):
        box = (int(x - ml), int(y - ma), int(x + ml) + 1, int(y + ma) + 1)
        m = ImageStat.Stat(im.crop(box).convert("L")).mean[0]
        if m < 70:
            b.append(0)
        elif m > 185:
            b.append(1)
        else:
            return None, "cell at (%d,%d) grey (%.0f): it is neither white nor black" % (x, y, m)
    if b[0] != 1 or b[1] != 0:
        return None, "the guards are not there (%s): the counter is not where I say" % b[:2]
    if sum(b[2:2 + BIT]) % 2 != b[-1]:
        return None, "wrong parity: %s" % "".join(map(str, b))
    n = 0
    for v in b[2:2 + BIT]:
        n = (n << 1) | v
    return n, ""


def delay_ms(n, t_ms):
    """How old, at instant `t_ms` (epoch ms), the image showing
    `n` is: t - (end of n's period).  Negative = n comes from the future (±1 period
    = clock)."""
    full = int(t_ms // PERIOD_MS)
    k = (full - n) % MODULE
    if k > MODULE // 2:
        k -= MODULE
    n_full = full - k
    return t_ms - (n_full + 1) * PERIOD_MS


def judge_quick(readings):
    """letture = [(t_before_ms, t_after_ms, n | None, reason)] ⇒ (outcome, reason, details)."""
    if len(readings) < 4:
        return S.BLOCKED, "only %d photos: too few to judge" % len(readings), []
    lines, troubles = [], []
    good = [(tp, td, n) for tp, td, n, _m in readings if n is not None]
    unreadable = len(readings) - len(good)
    for tp, td, n, m in readings:
        if n is None:
            lines.append("unreadable: %s" % m)
            continue
        r = delay_ms(n, tp)
        lines.append("n=%d delay %+.0f ms" % (n, r))
        if r > CAP_MS:
            troubles.append("photo %.0f ms old (n=%d, cap %.0f)" % (r, n, CAP_MS))
        if delay_ms(n, td) < -PERIOD_MS:
            troubles.append("n=%d comes from the future (%.0f ms): clock?" % (n, delay_ms(n, td)))
    for (tp0, _td0, n0), (tp1, _td1, n1) in zip(good, good[1:]):
        if n1 == n0 and tp1 - tp0 >= STILL_MS:
            troubles.append("two photos %.0f ms apart show the same n=%d: STILL"
                        % (tp1 - tp0, n0))
    different = len({n for _a, _b, n in good})
    if unreadable * 4 > len(readings):
        troubles.append("%d photos of %d with the counter unreadable" % (unreadable, len(readings)))
    if different < 3:
        troubles.append("only %d different values in %d photos" % (different, len(readings)))
    if troubles:
        return S.FAIL, "; ".join(troubles[:4]) + (" (+%d)" % (len(troubles) - 4) if len(troubles) > 4
                                               else ""), lines
    delay = [delay_ms(n, tp) for tp, _td, n in good]
    return S.PASS, ("%d photos in %.1f s, %d different values, maximum delay %.0f ms (cap %.0f)"
                    % (len(readings), (readings[-1][0] - readings[0][0]) / 1000.0, different,
                       max(delay), CAP_MS)), lines


def cyan_fraction(im):
    p = im.resize((max(1, im.size[0] // 4), max(1, im.size[1] // 4)))
    px = list(p.getdata())
    n = sum(1 for q in px if C21._near(q, C21.CYAN))
    return n / float(len(px))


CHANGED_MIN = 0.005                # share of changed pixels: «something appeared»


def changed(im_a, im_b):
    """The share of pixels (at 1/4) that differ by more than 40 in a channel."""
    if im_a.size != im_b.size:
        return 1.0
    from PIL import ImageChops
    w, h = im_a.size
    d = ImageChops.difference(im_a, im_b).resize((max(1, w // 4), max(1, h // 4)))
    px = list(d.getdata())
    return sum(1 for q in px if max(q) > 40) / float(len(px))


def find(im):
    """The test window in the photo (`C21.trova_finestra`): (dict | None, reason)."""
    w, h = im.size
    f, m = C21.find_window(w, h, list(im.getdata()), step=max(1, w // 960))
    if f:
        f["photo"] = [w, h]
        f["rett"] = [f["ciano"][0], f["ciano"][1], f["right"], f["ciano"][3]]
    return f, m


def judge_opening(f, largo_px):
    if not f:
        return S.FAIL, "the opened window is not seen in the photo"
    l = f["rett"][2] - f["rett"][0] + 1
    if l < 0.7 * largo_px:
        return S.FAIL, "the cyan is there but it is %d px wide (%d requested)" % (l, largo_px)
    return S.PASS, "the window is seen: cyan %s" % f["rett"]


def judge_move(r0, r1):
    """r0, r1 = [x0,y0,x1,y1] in the photo (or r1 None) ⇒ (outcome, reason)."""
    if not r1:
        return S.FAIL, "after the gesture the window is no longer seen"
    dx, dy = r1[0] - r0[0], r1[1] - r0[1]
    dl = (r1[2] - r1[0]) - (r0[2] - r0[0])
    da = (r1[3] - r1[1]) - (r0[3] - r0[1])
    if abs(dl) > SAME_SIZE_TOL or abs(da) > SAME_SIZE_TOL:
        return S.FAIL, "the window changed size (%+d,%+d): it is not a move" % (dl, da)
    if (dx * dx + dy * dy) ** 0.5 < MIN_MOVE:
        return S.FAIL, "the window is still (%+d,%+d px)" % (dx, dy)
    return S.PASS, "the window moved by (%+d,%+d) px, same size" % (dx, dy)


def judge_closing(quota):
    if quota < CYAN_ABSENT:
        return S.PASS, "in the photo there is no more cyan (%.3f %%)" % (100 * quota)
    return S.FAIL, "the closed window is still seen: cyan on %.1f %% of the photo" % (100 * quota)


def overall(parts):
    es = [e for _p, e, _m in parts]
    return S.FAIL if S.FAIL in es else (S.BLOCKED if S.BLOCKED in es else S.PASS)


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION
# ═══════════════════════════════════════════════════════════════════════════
def _fake_photo(n, rect=(100, 80, 899, 579), w=1000, h=700, background=(40, 40, 90)):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), background)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = rect
    d.rectangle(rect, fill=C21.CYAN)
    pw, ph = x1 - x0 + 1, y1 - y0 + 1
    d.rectangle((x0 + 0.06 * pw, y0 + 0.08 * ph, x0 + 0.40 * pw, y0 + 0.38 * ph), fill=C21.YELLOW)
    for i, v in enumerate(bit_di(n)):
        cx = x0 + (CELL_X0 + i * CELL_STEP) * pw
        cy = y0 + CELL_Y0 * ph
        d.rectangle((cx, cy, cx + CELL_W * pw, cy + CELL_H * ph),
                    fill=(255, 255, 255) if v else (0, 0, 0))
    return im


def certify():
    troubles = []

    def ok(c, what):
        print("%s %s" % ("⭐" if c else "⛔", what))
        if not c:
            troubles.append(what)
    for n in (0, 1, 1234, 4095):
        im = _fake_photo(n)
        f, m = find(im)
        ok(f is not None, "the fake window is found (%s)" % (f["rett"] if f else m))
        v, m = read_counter(im, f["rett"]) if f else (None, m)
        ok(v == n, "counter %d reads %s %s" % (n, v, m))
    im = _fake_photo(77)
    from PIL import ImageDraw
    ImageDraw.Draw(im).rectangle((100, 400, 899, 579), fill=(128, 128, 128))
    ok(read_counter(im, [100, 80, 899, 579])[0] is None, "counter covered ⇒ unreadable")
    t = 1_790_000_000_000.0
    n = int(t // PERIOD_MS) % MODULE
    ok(abs(delay_ms(n, t + 150) - (-50)) < 1e-6, "delay in the same period: -50 ms")
    ok(abs(delay_ms((n - 5) % MODULE, t) - 800) < 1e-6, "delay of 5 periods: 800 ms")
    vive = [(t + i * 700, t + i * 700 + 300, int((t + i * 700 - 150) // PERIOD_MS) % MODULE, "")
            for i in range(9)]
    e, m, _ = judge_quick(vive)
    ok(e == S.PASS, "real rapid changes ⇒ PASS (%s)" % m)
    stopped = [(tp, td, vive[0][2], "") for tp, td, _n, _m in vive]
    e, m, _ = judge_quick(stopped)
    ok(e == S.FAIL, "the first photo repeated (fault) ⇒ FAIL (%s)" % m[:90])
    slow = [(tp, td, int((tp - 1500) // PERIOD_MS) % MODULE, "") for tp, td, _n, _m in vive]
    e, m, _ = judge_quick(slow)
    ok(e == S.FAIL, "images 1.5 s old ⇒ FAIL")
    e, _m, _ = judge_quick(vive[:2])
    ok(e == S.BLOCKED, "only two photos ⇒ BLOCKED")
    ok(judge_move([10, 10, 500, 400], [330, 130, 820, 520])[0] == S.PASS, "moved ⇒ PASS")
    ok(judge_move([10, 10, 500, 400], [10, 10, 500, 400])[0] == S.FAIL, "still ⇒ FAIL")
    ok(judge_move([10, 10, 500, 400], [10, 10, 820, 400])[0] == S.FAIL,
       "widened ⇒ FAIL (it is not a move)")
    from PIL import Image
    ok(judge_closing(cyan_fraction(Image.new("RGB", (400, 300), (40, 40, 90))))[0] == S.PASS,
       "no cyan ⇒ closed")
    ok(judge_closing(cyan_fraction(_fake_photo(3)))[0] == S.FAIL, "cyan ⇒ not closed")
    ok(judge_opening(None, 800)[0] == S.FAIL, "no window ⇒ opening FAIL")
    print("⭐ certification green" if not troubles else "⛔ %d problems" % len(troubles))
    return 0 if not troubles else 1


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE PAGE AND IN THE BOX
# ═══════════════════════════════════════════════════════════════════════════
JS_OBSERVE = r"""
(function () {
  if (window.__F003__) return;
  const C = window.__F003__ = { giu: 0, su: 0, premuti: 0 };
  addEventListener('mousedown', function () { C.giu++; }, true);
  addEventListener('mouseup', function () { C.su++; }, true);
  /* ⚠ Since 2 Oct 2026 the page's click comes from `pointerdown` and the compatibility
     `mouse*` events are no longer born: the pointer events are counted too (like C22). */
  addEventListener('pointerdown', function (e) { if (e.pointerType !== 'touch') C.giu++; }, true);
  addEventListener('pointerup', function (e) { if (e.pointerType !== 'touch') C.su++; }, true);
  addEventListener('pointermove', function (e) { if (e.buttons & 1) C.premuti++; }, true);
})();
"""
JS_RESET = "const C=window.__F003__; if(!C) return false; C.giu=0; C.su=0; C.premuti=0; return true;"
JS_COUNT = r"""
const C = window.__F003__;
const st = window.REMOTIX && REMOTIX.classic_input ? REMOTIX.classic_input.state() : null;
return C ? { giu: C.giu, su: C.su, premuti: C.premuti,
             spedito: st ? st.last_sent : null } : null;
"""
GESTURE_STEPS = 16


def drag(g, geo, X, Y, DX, DY):
    """Left button down at (X,Y) of the desktop, dragged by (DX,DY), up."""
    points = [C21.desktop_to_glass(geo, X + DX * i / float(GESTURE_STEPS),
                                      Y + DY * i / float(GESTURE_STEPS))
             for i in range(GESTURE_STEPS + 1)]
    if hasattr(g, "cdp"):
        c = g.cdp.call
        x0, y0 = points[0]
        c("Input.dispatchMouseEvent", type="mouseMoved", x=x0, y=y0)
        time.sleep(0.15)
        c("Input.dispatchMouseEvent", type="mousePressed", x=x0, y=y0, button="left",
          buttons=1, clickCount=1)
        time.sleep(0.2)
        for x, y in points[1:]:
            c("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, button="left", buttons=1)
            time.sleep(0.03)
        time.sleep(0.2)
        x, y = points[-1]
        c("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left",
          buttons=0, clickCount=1)
        return
    az = [{"type": "pointerMove", "x": int(round(points[0][0])), "y": int(round(points[0][1])),
           "origin": "viewport", "duration": 0},
          {"type": "pause", "duration": 150}, {"type": "pointerDown", "button": 0},
          {"type": "pause", "duration": 200}]
    for x, y in points[1:]:
        az += [{"type": "pointerMove", "x": int(round(x)), "y": int(round(y)),
                "origin": "viewport", "duration": 0}, {"type": "pause", "duration": 30}]
    az += [{"type": "pause", "duration": 200}, {"type": "pointerUp", "button": 0}]
    g._actions([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                "actions": az}])


def prepare_home(s, largo, alto):
    """F-003's page in place of C21's (same file name: so
    `C21.turn_on_window` opens it), and C21's Firefox profile."""
    import base64
    b = lambda t: base64.b64encode(t.encode()).decode()       # noqa: E731
    return s.sc.inside(
        "set -e; h=/home/%(c)s; mkdir -p $h/%(p)s; echo %(pag)s | base64 -d > $h/%(f)s; "
        "echo %(pref)s | base64 -d > $h/%(p)s/user.js; "
        "echo %(xul)s | base64 -d > $h/%(p)s/xulstore.json; chown -R %(c)s: $h/%(p)s $h/%(f)s; "
        "echo pronta" % {"c": s.chi, "p": C21.PROFILE, "f": C21.PAGE_FILE, "pag": b(PAGE),
                         "pref": b(C21.PREFERENCES), "xul": b(C21.xulstore(largo, alto))}, 60)


def photo_im(s, name=None):
    """(png, PIL RGB, t_before_ms, t_after_ms).  Saves if `name`."""
    from PIL import Image
    tp = time.time() * 1000.0
    if name:
        png, _dove = s.photo(name)
    else:
        try:
            png = C21.full_photo(s.g)
        except Exception:                        # noqa: BLE001
            png = None
    td = time.time() * 1000.0
    if not png:
        return None, None, tp, td
    return png, Image.open(io.BytesIO(png)).convert("RGB"), tp, td


def wait_still(s, wait, name):
    """The window still in two photos in a row: (f, im) or (None, reason).

    ⚠ `[M]` 24 Sep 2026, lxqt under load 50: the moved window was seen
      in every photo but two photos in a row never came back equal within 12 s ⇒
      at the deadline the LAST window seen counts (with `ferma: False`): it is the
      photo, not a «not seen»."""
    fine = time.time() + wait
    latest, why, im, im_u = None, "no photo", None, None
    while time.time() < fine:
        png, im, _tp, _td = photo_im(s)
        if im is None:
            why = "the canvas cannot be photographed"
            time.sleep(1)
            continue
        f, why = find(im)
        if f and latest and all(abs(a - b) <= 2 for a, b in zip(latest["rett"], f["rett"])):
            if s.o.evidence and name:
                im.save(os.path.join(s.o.evidence, "%s.png" % name))
            f["ferma"] = True
            return f, im
        if f:
            latest, im_u = f, im
        time.sleep(0.8)
    if latest is not None:
        latest["ferma"] = False
        if s.o.evidence and name:
            im_u.save(os.path.join(s.o.evidence, "%s-non-ferma.png" % name))
        return latest, im_u
    if s.o.evidence and name and im is not None:
        im.save(os.path.join(s.o.evidence, "%s-NON-trovata.png" % name))
    return None, why


def process_alive(s):
    c, t = s.sc.inside("pgrep -u %s -f firefox-esr >/dev/null && echo vivo || echo morto" % s.chi,
                       30)
    return "vivo" in (t or "")


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def body(o, E):
    with S.Session(o, "003", E) as s:
        ok, m = s.enter()
        if not ok:
            raise S.Blocked(m)
        # ⚠ `[M]` 24 Sep 2026, kde: at the first frame the canvas was still
        #   640x340; the window size arrives later.  We wait for the expected
        #   canvas (the rule is F-011's), or the scene is not the intended one.
        cw, ch, dpr = s.g.js("const d=document.documentElement; "
                             "return [d.clientWidth, d.clientHeight, devicePixelRatio||1];")
        wait = F011.canvas_wait(cw, ch, dpr)
        fine = time.time() + 40
        geo = None
        while time.time() < fine:
            geo = s.geometry()
            if geo and [geo.get("tl"), geo.get("ta")] == wait:
                break
            time.sleep(1)
        if not geo:
            raise S.Blocked("`REMOTIX_PUNTATORE.geometry` is not there")
        if [geo.get("tl"), geo.get("ta")] != wait:
            raise S.Blocked("the canvas is %sx%s and not %dx%d after 40 s: the scene is not the "
                             "intended one (F-011 judges it)" % (geo.get("tl"), geo.get("ta"),
                                                                 wait[0], wait[1]))
        time.sleep(1.5)
        geo = s.geometry()
        if geo.get("layout") != "classic":
            raise S.Blocked("the page is not in the classic layout (%s): "
                             "dragging with the mouse is not this question" % geo.get("layout"))
        print("   canvas %sx%s · wake-up: %s" % (geo["tl"], geo["ta"], C21.wake(s.g, geo)),
              flush=True)
        parts, faults, ev = [], [], []

        # ── 0. the photo before: no cyan ───────────────────────────────────
        time.sleep(1.5)
        png0, im0, _a, _b = photo_im(s, "prima-dell-apertura")
        if im0 is None:
            raise S.Blocked("the canvas cannot be photographed")
        q0 = cyan_fraction(im0)
        if q0 >= CYAN_ABSENT:
            raise S.Blocked("before opening there is already some cyan (%.2f %%): the scene is not "
                             "clean" % (100 * q0))

        # ── 1. OPENS ───────────────────────────────────────────────────────
        largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
        c, t = prepare_home(s, largo_f, alto_f)
        if c != 0:
            raise S.Blocked("the home does not get ready: %s" % (t or "")[-200:])
        ok, t = C21.turn_on_window(s.sc, s.chi)
        if not ok:
            raise S.Blocked("firefox-esr does not start: %s" % (t or "")[-200:])
        t_ap = time.time()
        f1, im1 = wait_still(s, OPENING_S, "is_open")
        if not f1:
            _c, log = s.sc.inside("tail -n 40 /home/%s/.c21-firefox.log" % s.chi, 30)
            ev.append(s.save_text("firefox-esr-nella-sessione.log", log or ""))
            _p, im_x, _a, _b = photo_im(s, "apertura-non-vista")
            fresh = changed(im0, im_x) if im_x is not None else 0.0
            if not process_alive(s):
                parts.append(("apre", S.BLOCKED, "firefox-esr did not stay alive: %s" % im1))
            elif fresh > CHANGED_MIN:
                # ⚠ the screen updated (SOMETHING ELSE appeared: a notice,
                #   a preview): the scene is not the one I wanted ⇒ the bench
                parts.append(("apre", S.BLOCKED, "the photo changed (%.1f %% of the pixels) but "
                              "does not show the test page: something else appeared — see the photo "
                              "and the firefox-esr log" % (100 * fresh)))
            else:
                parts.append(("apre", S.FAIL, "firefox-esr has been alive for %.0f s and the photo is "
                              "IDENTICAL to the one before (%.2f %% of the pixels changed): the "
                              "screen does not update" % (time.time() - t_ap, 100 * fresh)))
            raise _Fine(parts, [], ev)
        pw, ph = f1["photo"]
        wide_photo = largo_f * geo["sx"] * pw / geo["bw"]       # desktop ⇒ photo
        e, m = judge_opening(f1, wide_photo)
        if e == S.FAIL and f1:
            e = S.BLOCKED
            m = ("the cyan is %d px wide and I asked for %d: a preview (overview?), "
                 "not the window" % (f1["rett"][2] - f1["rett"][0] + 1, largo_f))
        parts.append(("apre", e, m + " (in %.1f s)" % (time.time() - t_ap)))
        f0, _ = find(im0)
        faults.append(("apre", judge_opening(f0, wide_photo)))
        if e != S.PASS:
            raise _Fine(parts, faults)

        # ── 2. CHANGES: the counter, for QUICK_S seconds ─────────────────
        v0, mv = read_counter(im1, f1["rett"])
        if v0 is None:
            parts.append(("cambia", S.BLOCKED, "the counter cannot be read in the still "
                          "window: %s" % mv))
        else:
            # ⛔ a FAIL is confirmed by redoing it: if the first series is red a
            #   second one is done, and the red counts only if both are
            #   (`[M]` 24 Sep 2026, lxqt, load 50: ONE photo 1.5 s old)
            serial = []
            for cur_round in range(2):
                readings, first_im = [], None
                t_via = time.time()
                i = 0
                # ⚠ `[M]` 25 Sep 2026, gnome under load: a 4K Firefox photo
                #   cost 2-3 s, and in 6 s only 2 came ⇒ at least PHOTO_MIN photos,
                #   up to QUICK_MAX_S
                while (time.time() - t_via < QUICK_S or len(readings) < PHOTO_MIN) \
                        and time.time() - t_via < QUICK_MAX_S:
                    _png, im, tp, td = photo_im(s)
                    if im is None:
                        continue
                    n, mn = read_counter(im, f1["rett"])
                    readings.append((tp, td, n, mn))
                    if first_im is None:
                        first_im = im
                    if o.evidence:
                        x0, y0, x1, y1 = f1["rett"]
                        im.crop((x0, y0 + int(0.55 * (y1 - y0)), x1, y1)).save(
                            os.path.join(o.evidence, "rapida-%d-%02d-n%s.png" % (cur_round, i, n)))
                    i += 1
                e, m, lines = judge_quick(readings)
                ev.append(s.save_text("rapide-%d.txt" % cur_round, lines))
                serial.append((e, m, readings, first_im))
                print("   rapid changes, series %d: %s %s" % (cur_round + 1, e, m), flush=True)
                if e == S.PASS:
                    break
            e, m, readings, first_im = serial[-1]
            if len(serial) > 1:
                m = "series 1: %s %s · series 2: %s" % (serial[0][0], serial[0][1], m)
            parts.append(("cambia", e, m))
            # the fault: the FIRST photo for all, with the real instants
            if readings and first_im is not None:
                n0, m0 = read_counter(first_im, f1["rett"])
                old_ones = [(tp, td, n0, m0) for tp, td, _n, _m in readings]
                ge, gm, _ = judge_quick(old_ones)
                faults.append(("cambia", (ge, gm)))

        # ── 3. MOVES: by the title bar ─────────────────────────────────────
        s.g.js(S.VERI._inject(JS_OBSERVE))
        r0 = f1["rett"]
        f_before, im_before = f1, im1
        outcome_sp = None
        attempts = []
        for dy in GRAB_DYS:
            Xc, Yt = C21.from_photo_to_desktop(geo, pw, ph, (r0[0] + r0[2]) / 2.0 + 0.5,
                                               r0[1] + 0.5)
            X, Y = Xc, Yt + dy
            if Y < 2:
                continue
            if X + MOVE[0] + 4 >= geo["tl"] or Y + MOVE[1] + 4 >= geo["ta"]:
                outcome_sp = (S.BLOCKED, "there is no room to move the window")
                break
            s.g.js(JS_RESET)
            drag(s.g, geo, X, Y, MOVE[0], MOVE[1])
            time.sleep(0.4)
            n = s.g.js(JS_COUNT) or {}
            sp = n.get("spedito") or [-1, -1]
            if n.get("giu", 0) < 1 or n.get("su", 0) < 1 or n.get("premuti", 0) < GESTURE_STEPS // 2:
                outcome_sp = (S.BLOCKED, "the browser did not deliver the gesture to the page (%s)" % n)
                break
            if abs(sp[0] - int(X + MOVE[0])) > 2 or abs(sp[1] - int(Y + MOVE[1])) > 2:
                outcome_sp = (S.BLOCKED, "the page sent (%s,%s) instead of (%d,%d): the "
                            "pointer is not where I say" % (sp[0], sp[1], X + MOVE[0],
                                                           Y + MOVE[1]))
                break
            f2, im2 = wait_still(s, 20, "dopo-presa%+d" % dy)
            if not f2:
                attempts.append("%+d: the window is no longer seen (%s)" % (dy, im2))
                outcome_sp = (S.FAIL if process_alive(s) else S.BLOCKED,
                            "grip %+d px above the page: after the gesture the window is no longer "
                            "seen (%s)" % (dy, im2))
                break
            e, m = judge_move(r0, f2["rett"])
            if not f2.get("ferma", True):
                m += " (last photo: it did not stay still in two photos in a row)"
            attempts.append("%+d: %s" % (dy, m))
            print("   grip %+d px above the page → %s" % (dy, m), flush=True)
            if e == S.PASS:
                outcome_sp = (S.PASS, "grip %+d px above the page: %s" % (dy, m))
                faults.append(("move", judge_move(r0, f_before["rett"])))
                f_after, im_after = f2, im2
                break
            # resized or still: start again from the window as it is now
            r0, f_before, im_before = f2["rett"], f2, im2
            time.sleep(0.6)
        if outcome_sp is None:
            outcome_sp = (S.FAIL, "in none of the %d grips above the page did the window "
                        "move: %s" % (len(attempts), "; ".join(attempts[-3:])))
        parts.append(("move", outcome_sp[0], outcome_sp[1]))
        if outcome_sp[0] != S.PASS:
            f_after, im_after = f_before, im_before

        # ── 4. CLOSES ──────────────────────────────────────────────────────
        s.sc.inside("pkill -u %s -f '[f]irefox-esr' ; echo fatto" % s.chi, 30)
        t_ch = time.time()
        quota, im3, photos_taken = None, None, 0
        while time.time() - t_ch < CLOSED_S:
            time.sleep(0.7)
            _png, im_c, _a, _b = photo_im(s)
            if im_c is None:
                continue
            photos_taken += 1
            im3, quota = im_c, cyan_fraction(im_c)
            if quota < CYAN_ABSENT:
                break
        if im3 is not None and o.evidence:
            im3.save(os.path.join(o.evidence, "chiusa.png"))
        if quota is None:
            # ⚠ `[M]` 25 Sep 2026, gnome/chrome: 60 s without a successful photo
            #   (the browser under load): I did not look, it is not a «seen»
            parts.append(("chiude", S.BLOCKED, "after the closing no photo succeeded in "
                          "%.0f s" % (time.time() - t_ch)))
        elif quota >= CYAN_ABSENT and process_alive(s):
            parts.append(("chiude", S.BLOCKED, "firefox-esr did not close (pkill)"))
        else:
            e, m = judge_closing(quota)
            parts.append(("chiude", e, m + " (after %.1f s, %d photos)" % (time.time() - t_ch,
                                                                       photos_taken)))
        faults.append(("chiude", judge_closing(cyan_fraction(im_after))))
        raise _Fine(parts, faults, ev)


class _Fine(Exception):
    def __init__(self, parts, faults=None, ev=None):
        super().__init__("end")
        self.parts, self.faults, self.ev = parts, faults or [], ev or []


def body_and_verdict(o, E):
    try:
        body(o, E)
    except _Fine as f:
        es = overall(f.parts)
        text = " · ".join("%s %s: %s" % (p, e, m) for p, e, m in f.parts)
        troubles = [x for x in f.parts if x[1] != S.PASS]
        ev = [p for p in f.ev if p]
        if o.evidence:
            ev.append(o.evidence)
        E.put("F-003", es, text if es != S.PASS else
                "opens, changes, moves, closes: all the photos follow the screen",
                expected="the photo shows the open window; the new counter (≤ %.0f ms) in every "
                       "photo of %d s; the window elsewhere after the drag; no "
                       "window after the closing" % (CAP_MS, QUICK_S),
                observed=text, evidence=ev, parts={p: [e, m] for p, e, m in f.parts},
                troubles=[p for p, _e, _m in troubles])
        if o.fault:
            if es != S.PASS:
                E.fault("F-003", None, "the healthy pass is not green: the «old photo» fault "
                         "is judged only on a healthy pass (%s)" % text[:200])
                return
            seen_items = {p: r[0] == S.FAIL for p, r in f.faults}
            all_items = len(seen_items) == 4 and all(seen_items.values())
            E.fault("F-003", all_items, "photos from BEFORE the change ⇒ %s" % " · ".join(
                "%s %s" % (p, "red" if r[0] == S.FAIL else r[0]) for p, r in f.faults),
                observed=" | ".join("%s: %s" % (p, r[1]) for p, r in f.faults))


if __name__ == "__main__":
    sys.exit(S.run(__doc__, FUNCTIONS, body_and_verdict, certify))
