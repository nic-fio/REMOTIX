#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g1b-comune — the tools of group G1b («the desktop behaves as a remote
desktop»: F-010, F-029, F-030).  Imported, not executed.

  · REAL clicks and keys given to the browser (CDP `Input.dispatch*` on Chrome, W3C
    Marionette actions on Firefox), in DESKTOP coordinates;
  · the OCR of the photo (tesseract, if present: see `TESSERACT`);
  · the reading of a field INSIDE the tenant's session.
"""
import io
import os
import re
import subprocess
import tempfile
import time

# ⭐ tesseract is NOT installed in the server's system (rootfs in RAM, and the
#   tests do not install packages): it is EXTRACTED from Trixie's .debs
#   (tesseract-ocr 5.5.0, libtesseract5, libleptonica6, eng/ita/osd data) into
#   a folder of the persistent disk, without root.  It is redone with:
#     cd /tmp && apt-get download tesseract-ocr libtesseract5 libleptonica6 \
#        tesseract-ocr-eng tesseract-ocr-osd tesseract-ocr-ita && \
#     for f in *.deb; do dpkg-deb -x $f /media/REMOTIX/strumenti/tesseract; done
TESSERACT = os.environ.get("REMOTIX_TESSERACT", "/media/REMOTIX/strumenti/tesseract")


def ocr_available():
    return os.path.exists(os.path.join(TESSERACT, "usr", "bin", "tesseract"))


def ocr(png, rect=None, zoom_in=2, psm=11, threshold=None):
    """The words read in the photo: [(text, x, y, w, h, confidence)] in pixels
    of the PHOTO (not of the crop).  None if tesseract is not there.
    `threshold`: the crop is brought to DARK text on a light background (it is inverted
    if it is dark on average) and binarised — `[M]` 24 Sep 2026: GNOME's dark menu
    in grey cannot be read, binarised at 110 it can."""
    if not ocr_available():
        return None
    from PIL import Image, ImageOps, ImageStat
    im = Image.open(io.BytesIO(png)).convert("L")
    ox, oy = 0, 0
    if rect:
        x0, y0, x1, y1 = [int(v) for v in rect]
        x0, y0 = max(0, x0), max(0, y0)
        x1, y1 = min(im.size[0], x1), min(im.size[1], y1)
        im = im.crop((x0, y0, x1, y1))
        ox, oy = x0, y0
    if zoom_in != 1:
        im = im.resize((im.size[0] * zoom_in, im.size[1] * zoom_in), Image.LANCZOS)
    if threshold is not None:
        if ImageStat.Stat(im).mean[0] < 128:
            im = ImageOps.invert(im)
        im = im.point(lambda v: 0 if v < threshold else 255)
    amb = dict(os.environ,
               LD_LIBRARY_PATH=os.path.join(TESSERACT, "usr", "lib", "x86_64-linux-gnu"),
               TESSDATA_PREFIX=os.path.join(TESSERACT, "usr", "share", "tesseract-ocr", "5",
                                            "tessdata"),
               OMP_THREAD_LIMIT="2")
    with tempfile.TemporaryDirectory() as d:
        f = os.path.join(d, "in.png")
        im.save(f)
        r = subprocess.run([os.path.join(TESSERACT, "usr", "bin", "tesseract"), f, "stdout",
                            "-l", "eng+ita", "--psm", str(psm), "tsv"],
                           capture_output=True, text=True, env=amb, timeout=120)
    words = []
    for row in r.stdout.splitlines()[1:]:
        c = row.split("\t")
        if len(c) < 12 or not c[11].strip():
            continue
        try:
            conf = float(c[10])
        except ValueError:
            conf = -1
        x, y, w, h = [int(v) / zoom_in for v in c[6:10]]
        words.append((c[11].strip(), ox + x, oy + y, w, h, conf))
    return words


def text_of(words):
    return " ".join(p[0] for p in words or [])


def search_word(words, model):
    """The first word (text, x, y, w, h, conf) that matches `model`
    (regex, case-insensitive)."""
    rx = re.compile(model, re.I)
    for p in words or []:
        if rx.search(p[0]):
            return p
    return None


def search_phrase(words, model):
    """Like `search_word` but on rebuilt lines: returns (sentence, x, y) of the
    first group of close words (same line) that matches."""
    rx = re.compile(model, re.I)
    line_list = []
    for p in sorted(words or [], key=lambda q: (round(q[2] / 12), q[1])):
        if line_list and abs(line_list[-1][-1][2] - p[2]) < 10 and \
                p[1] - (line_list[-1][-1][1] + line_list[-1][-1][3]) < 40:
            line_list[-1].append(p)
        else:
            line_list.append([p])
    for r in line_list:
        sentence = " ".join(q[0] for q in r)
        if rx.search(sentence):
            return sentence, r[0][1], r[0][2] + r[0][4] / 2
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  THE MOUSE AND THE KEYS, REAL
# ═══════════════════════════════════════════════════════════════════════════
def desktop_to_glass(geo, X, Y):
    return (geo["left"] + (geo["bx0"] + X * geo["left_side"]) * geo["vx"],
            geo["top"] + (geo["by0"] + Y * geo["sy"]) * geo["vy"])


def from_photo_to_desktop(geo, pw, ph, px, py):
    return ((px * geo["bw"] / pw - geo["bx0"]) / geo["left_side"],
            (py * geo["bh"] / ph - geo["by0"]) / geo["sy"])


def click_desktop(s, geo, X, Y, button_code=0):
    """A real click at the point (X, Y) of the desktop.  button_code 0 left, 2 right."""
    g = s.g
    x, y = desktop_to_glass(geo, X, Y)
    if hasattr(g, "cdp"):
        label_name = {0: "left", 1: "middle", 2: "right"}[button_code]
        try:
            g.cdp.call("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
        except RuntimeError:
            # ⚠ `[M]` 24 Sep 2026, server at load 40: «Internal error» on the
            #   first event; the second goes through
            time.sleep(1.5)
            g.cdp.call("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)
        time.sleep(0.15)
        g.cdp.call("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y,
                     button=label_name, clickCount=1)
        time.sleep(0.08)
        g.cdp.call("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y,
                     button=label_name, clickCount=1)
        return
    g._actions([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                "actions": [{"type": "pointerMove", "x": int(x), "y": int(y),
                             "origin": "viewport", "duration": 0},
                            {"type": "pause", "duration": 150},
                            {"type": "pointerDown", "button": button_code},
                            {"type": "pause", "duration": 80},
                            {"type": "pointerUp", "button": button_code}]}])


def move_desktop(s, geo, X, Y):
    x, y = desktop_to_glass(geo, X, Y)
    s.g.move_to(x, y)


#  name: (key, code, vk, WebDriver, CDP modifier bit)
KEYS = {
    "Alt": ("Alt", "AltLeft", 18, "", 1),
    "Control": ("Control", "ControlLeft", 17, "", 2),
    "Ctrl": ("Control", "ControlLeft", 17, "", 2),
    "Super": ("Meta", "MetaLeft", 91, "", 4),
    "Meta": ("Meta", "MetaLeft", 91, "", 4),
    "Shift": ("Shift", "ShiftLeft", 16, "", 8),
    "Tab": ("Tab", "Tab", 9, "", 0),
    "Escape": ("Escape", "Escape", 27, "", 0),
    "Esc": ("Escape", "Escape", 27, "", 0),
    "Enter": ("Enter", "Enter", 13, "", 0),
    "Space": (" ", "Space", 32, " ", 0),
    "F1": ("F1", "F1", 112, "", 0),
    "F2": ("F2", "F2", 113, "", 0),
    "Delete": ("Delete", "Delete", 46, "", 0),
}


def _key(label_name):
    if label_name in KEYS:
        return KEYS[label_name]
    if len(label_name) == 1 and label_name.isalnum():
        c = label_name.lower()
        code = ("Key" + c.upper()) if c.isalpha() else ("Digit" + c)
        return (c, code, ord(c.upper()), c, 0)
    raise KeyError(label_name)


def combination(g, names, keep_ms=120):
    """Presses the keys in order, holds them, releases them in reverse (a
    real combination: Alt down, Tab down, Tab up, Alt up)."""
    keys = [_key(n) for n in names]
    if hasattr(g, "cdp"):
        mod = 0
        for key, code, vk, _w, bit in keys:
            mod |= bit
            p = dict(type="rawKeyDown", key=key, code=code, windowsVirtualKeyCode=vk,
                     modifiers=mod)
            g.cdp.call("Input.dispatchKeyEvent", **p)
            time.sleep(0.06)
        time.sleep(keep_ms / 1000.0)
        for key, code, vk, _w, bit in reversed(keys):
            mod &= ~bit
            g.cdp.call("Input.dispatchKeyEvent", type="keyUp", key=key, code=code,
                         windowsVirtualKeyCode=vk, modifiers=mod)
            time.sleep(0.06)
        return
    az = []
    for t in keys:
        az += [{"type": "keyDown", "value": t[3]}, {"type": "pause", "duration": 60}]
    az.append({"type": "pause", "duration": keep_ms})
    for t in reversed(keys):
        az += [{"type": "keyUp", "value": t[3]}, {"type": "pause", "duration": 60}]
    g.m.call("WebDriver:PerformActions",
               {"actions": [{"type": "key", "id": "keyboard", "actions": az}]})
    g.m.call("WebDriver:ReleaseActions")


def focus_on_canvas(s, geo):
    """Takes the focus away from the form and brings the pointer onto the canvas, as
    the user does before writing (without clicking: a click would land in the desktop)."""
    try:
        s.g.js("if (document.activeElement && document.activeElement.blur) "
               "document.activeElement.blur(); "
               "const t=document.getElementById('display_screen'); if (t && t.focus) t.focus(); "
               "return 1;")
    except Exception:                            # noqa: BLE001
        pass
    move_desktop(s, geo, geo["tl"] * 0.5, geo["ta"] * 0.6)
    time.sleep(0.3)


# ═══════════════════════════════════════════════════════════════════════════
#  THE PHOTOS
# ═══════════════════════════════════════════════════════════════════════════
def bitmap(png):
    from PIL import Image
    return Image.open(io.BytesIO(png)).convert("RGB")


def difference(png_a, png_b, rect=None, step=4, threshold=40):
    """The fraction of the sampled pixels that changes between two photos (0..1)."""
    a, b = bitmap(png_a), bitmap(png_b)
    if a.size != b.size:
        return 1.0
    if rect:
        a, b = a.crop(rect), b.crop(rect)
    pa, pb = a.load(), b.load()
    n = changed = 0
    for y in range(0, a.size[1], step):
        for x in range(0, a.size[0], step):
            n += 1
            p, q = pa[x, y], pb[x, y]
            if abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > threshold:
                changed += 1
    return changed / max(1, n)


def mean_luminance(png, step=8):
    im = bitmap(png)
    px = im.load()
    t = n = 0
    for y in range(0, im.size[1], step):
        for x in range(0, im.size[0], step):
            r, g, b = px[x, y]
            t += 0.299 * r + 0.587 * g + 0.114 * b
            n += 1
    return t / max(1, n)


def png_nero(w, h):
    import struct
    import zlib
    row = b"\x00" + b"\x00\x00\x00" * w
    data_v = zlib.compress(row * h, 9)

    def piece(t, d):
        return (struct.pack(">I", len(d)) + t + d
                + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff))
    return (b"\x89PNG\r\n\x1a\n" + piece(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
            + piece(b"IDAT", data_v) + piece(b"IEND", b""))


def png_size(png):
    import struct
    return struct.unpack(">II", png[16:24])


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE SESSION
# ═══════════════════════════════════════════════════════════════════════════
def in_session(s, command, seconds=60):
    """(code, output) of `command` executed as the tenant, with
    the environment of their graphical session (and the XDG_CONFIG_DIRS of their
    compositor, which on KDE carries REMOTIX's KIOSK)."""
    return s.in_session(command, seconds, background=False)


def environment_of(s, process):
    """An environment variable by name, read from /proc/<pid>/environ of the
    tenant's first process named `process`: {name: value}."""
    c, t = s.sc.inside(
        "p=$(pgrep -u %s -x %s | head -1); [ -n \"$p\" ] || exit 4; "
        "tr '\\0' '\\n' < /proc/$p/environ" % (s.chi, process), 30)
    if c != 0:
        return {}
    amb = {}
    for row in t.splitlines():
        k, _, v = row.partition("=")
        if k:
            amb[k] = v
    return amb


def changed_rect(png_a, png_b, cell=8, threshold=60, headroom=24, minimum=3, near=None):
    """⭐ Where something opened: the box (x0, y0, x1, y1) of the LARGEST BLOB
    of changed cells between two photos (cells of `cell` px, one pixel
    per cell, 8-neighbours with one step of tolerance).  It serves to crop
    the open menu for the OCR: tesseract on a crop wide with background gets the
    threshold wrong and reads nothing (`[M]` 24 Sep 2026, GNOME: «Log Out…» read in the
    narrow crop, lost in the wide one).  None if nothing changes."""
    a, b = bitmap(png_a), bitmap(png_b)
    if a.size != b.size:
        return None
    pa, pb = a.load(), b.load()
    W, H = a.size
    cw, ch = W // cell, H // cell
    lit = set()
    for j in range(ch):
        y = j * cell + cell // 2
        for i in range(cw):
            x = i * cell + cell // 2
            if near and (x - near[0]) ** 2 + (y - near[1]) ** 2 > near[2] ** 2:
                continue
            p, q = pa[x, y], pb[x, y]
            if abs(p[0] - q[0]) + abs(p[1] - q[1]) + abs(p[2] - q[2]) > threshold:
                lit.add((i, j))
    seen_items, best = set(), None
    for c in lit:
        if c in seen_items:
            continue
        stack, blob = [c], []
        seen_items.add(c)
        while stack:
            i, j = stack.pop()
            blob.append((i, j))
            for di in (-2, -1, 0, 1, 2):
                for dj in (-2, -1, 0, 1, 2):
                    v = (i + di, j + dj)
                    if v in lit and v not in seen_items:
                        seen_items.add(v)
                        stack.append(v)
        if best is None or len(blob) > len(best):
            best = blob
    if not best or len(best) < minimum:
        return None
    xs = [c[0] for c in best]
    ys = [c[1] for c in best]
    return (max(0, min(xs) * cell - headroom), max(0, min(ys) * cell - headroom),
            min(W, (max(xs) + 1) * cell + headroom), min(H, (max(ys) + 1) * cell + headroom))


def read_rect(png, rect, zoom_in=3):
    """OCR of the box in three readings (grey psm 11; binarised at 110 psm 6;
    at 150 psm 11).  Returns (lines, text): the LINES of each reading, put
    together — an entry read by only one of the three counts (for the forbidden ones
    the most sensitive is wanted).  (None, reason) if tesseract is not there."""
    if not ocr_available():
        return None, "tesseract is not in %s" % TESSERACT
    all_of = []
    for psm, threshold in ((11, None), (6, 110), (11, 150)):
        p = ocr(png, rect, zoom_in=zoom_in, psm=psm, threshold=threshold) or []
        all_of += lines_of(p)
        read_rect.words = getattr(read_rect, "words", []) + p
    return all_of, " | ".join(r[0] for r in all_of)


def words_read():
    """The words (with the position) of the readings made by `read_rect`
    since the last `reset_words()`."""
    return list(getattr(read_rect, "words", []))


def reset_words():
    read_rect.words = []


def lines_of(words, stride_y=14):
    """The words put back into lines: [(sentence, x, y)] sorted from the top.  A
    line = the words with the centre at the same height (±stride_y), in x order.
    The three readings give duplicates: within a line the words overlapping one
    already taken are removed, and equal close lines are removed.
    ⚠ Two side-by-side menus at the same height end up in the same line: for
      the judgment that is fine (words are looked for, entries are not counted)."""
    line_list = []
    for p in sorted(words or [], key=lambda q: q[2] + q[4] / 2):
        cy = p[2] + p[4] / 2
        for r in line_list:
            if abs(r["y"] - cy) < stride_y:
                r["p"].append(p)
                break
        else:
            line_list.append({"y": cy, "p": [p]})
    outside = []
    for r in sorted(line_list, key=lambda r: r["y"]):
        taken = []
        for p in sorted(r["p"], key=lambda q: (-q[5], q[1])):
            if any(p[1] < q[1] + q[3] and q[1] < p[1] + p[3] for q in taken):
                continue
            taken.append(p)
        taken.sort(key=lambda q: q[1])
        outside.append((" ".join(q[0] for q in taken), taken[0][1], r["y"]))
    return outside


# ═══════════════════════════════════════════════════════════════════════════
#  THE KNOWN WINDOWS (GTK4: it is in all four boxes)
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ A window FILLED with a pure colour, with an app_id of its own: on GNOME Alt+Tab
#   switches between APPLICATIONS, and two windows of the same program would be
#   a single entry.  `[M]` 24 Sep 2026: GTK3 is only in the gnome box,
#   GTK4 in all.
WINDOW_GTK = r'''
import sys
import gi
gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gdk
import time
from gi.repository import GLib
label_name, color, largo, alto = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
# optional: a second colour and a period — the window changes colour by itself
# (color if (now // period) is even, other_one if odd), WITHOUT input: it is the
# proof that the image is live and not a frozen frame
other_one = sys.argv[5] if len(sys.argv) > 5 else None
period = int(sys.argv[6]) if len(sys.argv) > 6 else 30
app = Gtk.Application(application_id="org.remotix.c15" + label_name)
def rule_v(c):
    return ("window, window.background, headerbar, .titlebar { background: %s; "
            "background-image: none; }" % c)
def load(css, body_text):
    try:
        css.load_from_string(body_text)
    except AttributeError:
        css.load_from_data(body_text, -1)
def live(a):
    css = Gtk.CssProvider()
    load(css, rule_v(color))
    Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), css, 800)
    w = Gtk.ApplicationWindow(application=a, title="c15-" + label_name)
    w.set_default_size(largo, alto)
    w.present()
    if other_one:
        def run():
            load(css, rule_v(color if int(time.time() // period) % 2 == 0 else other_one))
            w.queue_draw()
            return True
        GLib.timeout_add(500, run)
app.connect("activate", live)
app.run([])
'''


def put_window(s):
    """Writes the window's program in the tenant's home."""
    import base64
    b = base64.b64encode(WINDOW_GTK.encode()).decode()
    return s.sc.inside("echo %s | base64 -d > /home/%s/.c15-finestra.py && chown %s: "
                       "/home/%s/.c15-finestra.py && echo written"
                       % (b, s.chi, s.chi, s.chi), 60)


def open_window(s, label_name, color, largo, alto, other_one=None, period=30):
    queue = " '%s' %d" % (other_one, period) if other_one else ""
    return s.in_session("python3 /home/%s/.c15-finestra.py %s '%s' %d %d%s"
                            % (s.chi, label_name, color, largo, alto, queue), 60, background=True)


CYAN = (0, 255, 255)
MAGENTA = (255, 0, 255)


def count_colors(png, colors, step=6, toll=50):
    """{colour: fraction of the sampled pixels close to that colour}."""
    im = bitmap(png)
    px = im.load()
    n = 0
    counts = {c: 0 for c in colors}
    for y in range(0, im.size[1], step):
        for x in range(0, im.size[0], step):
            p = px[x, y]
            n += 1
            for c in colors:
                if abs(p[0] - c[0]) + abs(p[1] - c[1]) + abs(p[2] - c[2]) < toll:
                    counts[c] += 1
                    break
    return {c: v / max(1, n) for c, v in counts.items()}


def living(png, step=6, threshold=24):
    """The fraction of NOT nearly black pixels: a turned-off screen is all black,
    even where the desktop was already dark (XFCE is born with a black background)."""
    im = bitmap(png)
    px = im.load()
    n = v = 0
    for y in range(0, im.size[1], step):
        for x in range(0, im.size[0], step):
            r, g, b = px[x, y]
            n += 1
            v += (0.299 * r + 0.587 * g + 0.114 * b) > threshold
    return v / max(1, n)


def wait_open(s, png_before, label_name, near, cap_s=10.0, min_side=120):
    """Photographs until near the click something of at least
    `min_side` x `min_side` px opens (a menu, not a button's highlight).
    Returns (png, path, box | None)."""
    fine = time.time() + cap_s
    png, dove, r = None, "", None
    while True:
        time.sleep(1.5)
        png, dove = picture(s, label_name)
        if png:
            r = changed_rect(png_before, png, near=near)
            if r and r[2] - r[0] >= min_side and r[3] - r[1] >= min_side:
                return png, dove, r
        if time.time() > fine:
            return png, dove, r


# ⭐ `[M]` 24 Sep 2026: on a STILL canvas (the desktop does not change, REMOTIX sends no
#   frames) Chrome's `Page.captureScreenshot` in the headless labwc
#   takes ~60 s — it waits for a frame nobody draws.  A 1 px dot
#   that changes colour at every photo gives the browser's compositor some damage
#   to draw, and the photo comes back at once.  Is it in the top-left corner
#   of the PAGE, outside the canvas? No: the canvas covers everything — it sits ON TOP, 1 px,
#   and changes between two nearly equal greys; in the judgments it weighs 1 pixel in 8 million.
JS_PROD = r"""
let p = document.getElementById('c15-pungolo');
if (!p) { p = document.createElement('div'); p.id = 'c15-pungolo';
  p.style.cssText = 'position:fixed;left:0;top:0;width:1px;height:1px;z-index:2147483647;pointer-events:none';
  document.body.appendChild(p); }
p.style.background = p.style.background === 'rgb(1, 1, 1)' ? 'rgb(2, 2, 2)' : 'rgb(1, 1, 1)';
return 1;
"""


def prods(s):
    try:
        s.g.js(JS_PROD)
    except Exception:                            # noqa: BLE001
        pass


def picture(s, label_name, scale_v=1.0, attempts=3):
    """The photo of the canvas, RETRIED (`[M]` 24 Sep 2026: with the server at load
    25-50 Chrome's 4K capture times out).  `scale_v` < 1 only on Chrome (CDP
    can reduce it; Marionette cannot): for the colour judgments half is enough,
    for the OCR scale 1 is needed.  Returns (png | None, path | reason)."""
    import base64
    last = ""
    for _ in range(attempts):
        prods(s)
        if scale_v < 1 and hasattr(s.g, "cdp"):
            try:
                r = s.g.js("const t=document.getElementById('display_screen');"
                           "if(!t) return null; const b=t.getBoundingClientRect();"
                           "return [b.left, b.top, b.width, b.height];")
                if not r:
                    last = "the canvas is not there"
                    time.sleep(2)
                    continue
                c = s.g.cdp.call("Page.captureScreenshot", format="png",
                                   clip={"x": r[0], "y": r[1], "width": r[2],
                                         "height": r[3], "scale": scale_v})
                png = base64.b64decode(c["data"])
                s._photo += 1
                dove = ""
                if s.o.evidence:
                    dove = os.path.join(s.o.evidence, "%02d-%s.png" % (s._photo, label_name))
                    with open(dove, "wb") as f:
                        f.write(png)
                return png, dove
            except Exception as e:               # noqa: BLE001
                last = "photo failed: %s" % str(e)[:200]
                step("⚠ photo %s: %s" % (label_name, last))
        else:
            png, dove = s.picture(label_name)
            if png:
                return png, dove
            last = dove
            step("⚠ photo %s: %s" % (label_name, last))
        time.sleep(3)
    return None, last


_T0 = time.time()


def step(body_text):
    """A line with the time elapsed since the start: where the test's time goes."""
    print("   [%5.0f s] %s" % (time.time() - _T0, body_text), flush=True)
