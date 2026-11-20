"""inputlib - what check-input.py and check-phone.py share on top of lib.py (lib.py itself is untouched): real mouse buttons,
wheel and keys for both browsers, the input test window (window-input.py) with its event log, the classification of a cursor
image by its pixels, touch (Chrome DevTools) and phone emulation.

Everything here drives the BROWSER the way a person's hands would (DevTools Input.* for Chrome, WebDriver actions for Firefox);
what is judged is what the application inside the box received (window-input.py) or what the client page shows."""
import base64
import io
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
from lib import ToolError  # noqa: E402

HERE = lib.HERE
ALT, CTRL, META, SHIFT = 1, 2, 4, 8  # Chrome modifier bits

# ------------------------------------------------------------------------------------------------------ keys
# name -> (key, code, windows virtual key); US positions (a physical keyboard sends positions, the page sends letters)
NAMED = {"Enter": ("Enter", "Enter", 13), "Backspace": ("Backspace", "Backspace", 8), "Delete": ("Delete", "Delete", 46),
         "Tab": ("Tab", "Tab", 9), "Escape": ("Escape", "Escape", 27), "Left": ("ArrowLeft", "ArrowLeft", 37),
         "Up": ("ArrowUp", "ArrowUp", 38), "Right": ("ArrowRight", "ArrowRight", 39), "Down": ("ArrowDown", "ArrowDown", 40),
         "Home": ("Home", "Home", 36), "End": ("End", "End", 35), "PageUp": ("PageUp", "PageUp", 33),
         "PageDown": ("PageDown", "PageDown", 34), "Insert": ("Insert", "Insert", 45), "CapsLock": ("CapsLock", "CapsLock", 20),
         " ": (" ", "Space", 32)}
for _i in range(1, 13):
    NAMED["F%d" % _i] = ("F%d" % _i, "F%d" % _i, 111 + _i)
MODKEYS = {"ctrl": ("Control", "ControlLeft", 17, CTRL), "alt": ("Alt", "AltLeft", 18, ALT), "shift": ("Shift", "ShiftLeft", 16, SHIFT),
           "meta": ("Meta", "MetaLeft", 91, META)}
# the US keyboard: character -> (code, shifted?)
_PUNCT = {"`": ("Backquote", 0), "~": ("Backquote", 1), "-": ("Minus", 0), "_": ("Minus", 1), "=": ("Equal", 0), "+": ("Equal", 1),
          "[": ("BracketLeft", 0), "{": ("BracketLeft", 1), "]": ("BracketRight", 0), "}": ("BracketRight", 1),
          "\\": ("Backslash", 0), "|": ("Backslash", 1), ";": ("Semicolon", 0), ":": ("Semicolon", 1), "'": ("Quote", 0),
          '"': ("Quote", 1), ",": ("Comma", 0), "<": ("Comma", 1), ".": ("Period", 0), ">": ("Period", 1), "/": ("Slash", 0),
          "?": ("Slash", 1), "!": ("Digit1", 1), "@": ("Digit2", 1), "#": ("Digit3", 1), "$": ("Digit4", 1), "%": ("Digit5", 1),
          "^": ("Digit6", 1), "&": ("Digit7", 1), "*": ("Digit8", 1), "(": ("Digit9", 1), ")": ("Digit0", 1)}
_VK = {"Backquote": 192, "Minus": 189, "Equal": 187, "BracketLeft": 219, "BracketRight": 221, "Backslash": 220, "Semicolon": 186,
       "Quote": 222, "Comma": 188, "Period": 190, "Slash": 191}
# WebDriver key codes (Firefox)
WD = {"Enter": "", "Backspace": "", "Delete": "", "Tab": "", "Escape": "", "Left": "",
      "Up": "", "Right": "", "Down": "", "Home": "", "End": "", "PageUp": "",
      "PageDown": "", "Insert": "", "ctrl": "", "alt": "", "shift": "", "meta": ""}
for _i in range(1, 13):
    WD["F%d" % _i] = chr(0xe031 + _i - 1)


def key_def(name):
    """(key, code, vk, text, shift_needed) of a name in NAMED or of one character."""
    if name in NAMED:
        k, c, v = NAMED[name]
        return k, c, v, None, False
    ch = name
    if ch.isascii() and ch.isalpha():
        return ch, "Key" + ch.upper(), ord(ch.upper()), ch, ch.isupper()
    if ch.isdigit():
        return ch, "Digit" + ch, ord(ch), ch, False
    if ch in _PUNCT:
        c, sh = _PUNCT[ch]
        return ch, c, _VK.get(c, ord(c[-1]) if c.startswith("Digit") else 0), ch, bool(sh)
    # an accented / other letter: the key is the character, the position the one the Italian keyboard has it on
    return ch, ITALIAN.get(ch, ("Unidentified", 0))[0], ITALIAN.get(ch, ("", 0))[1], ch, False


# Italian keyboard: the position (US name) of the accented letters and the like, as the browser reports it
ITALIAN = {"è": ("BracketLeft", 219), "é": ("BracketLeft", 219), "ò": ("Semicolon", 186), "ç": ("Semicolon", 186), "à": ("Quote", 222),
           "°": ("Quote", 222), "ù": ("Backslash", 220), "§": ("Backslash", 220), "ì": ("Equal", 187), "^": ("Equal", 187)}


class Kbd:
    """Real keys into the browser. tap(name, mods): the key with the modifiers held. hold(name, secs): a key held down
    (Chrome: with the browser's auto-repeat events, like a real keyboard; Firefox: down, wait, up: WebDriver sends no repeat)."""

    def __init__(self, g):
        self.g, self.chrome = g, g.name == "Chrome"

    # --- Chrome
    def _c(self, type_, key, code, vk, mod, text=None, **extra):
        p = dict(type=type_, key=key, code=code, windowsVirtualKeyCode=vk, modifiers=mod)
        if text:
            p["text"] = text
        p.update(extra)
        self.g.call("Input.dispatchKeyEvent", **p)

    def _chrome_tap(self, name, mods, hold=0.0, to_hold=None):
        key, code, vk, text, shift = key_def(name)
        mods = set(mods) | ({"shift"} if shift else set())
        bits, order = 0, [m for m in ("ctrl", "alt", "shift", "meta") if m in mods]
        for m in order:
            k, c, v, b = MODKEYS[m]
            bits |= b
            self._c("rawKeyDown", k, c, v, bits)
            time.sleep(0.05)
        printable = text is not None and not (mods & {"ctrl", "alt", "meta"})
        self._c("keyDown" if printable else "rawKeyDown", key, code, vk, bits, text if printable else None)
        if hold:
            end = time.time() + hold
            time.sleep(0.5)  # a real keyboard repeats after ~0.5 s, then ~30 per second
            while time.time() < end:
                self._c("keyDown" if printable else "rawKeyDown", key, code, vk, bits, text if printable else None, autoRepeat=True)
                time.sleep(0.033)
        else:
            time.sleep(0.08)
        self._c("keyUp", key, code, vk, bits)
        for m in reversed(order):
            k, c, v, b = MODKEYS[m]
            bits &= ~b
            time.sleep(0.04)
            self._c("keyUp", k, c, v, bits)

    # --- Firefox
    def _ff_tap(self, name, mods, hold=0.0):
        val = WD.get(name, name)
        a = []
        for m in ("ctrl", "alt", "shift", "meta"):
            if m in mods:
                a += [{"type": "keyDown", "value": WD[m]}, {"type": "pause", "duration": 50}]
        if hold:  # WebDriver sends the keydown of a key already down with repeat=true: like auto-repeat
            a += [{"type": "keyDown", "value": val}, {"type": "pause", "duration": 500}]
            a += [x for _ in range(int((hold - 0.5) / 0.05)) for x in ({"type": "keyDown", "value": val}, {"type": "pause", "duration": 33})]
            a += [{"type": "keyUp", "value": val}]
        else:
            a += [{"type": "keyDown", "value": val}, {"type": "pause", "duration": 80}, {"type": "keyUp", "value": val}]
        for m in ("meta", "shift", "alt", "ctrl"):
            if m in mods:
                a += [{"type": "pause", "duration": 40}, {"type": "keyUp", "value": WD[m]}]
        self.g._actions([{"type": "key", "id": "kbd", "actions": a}])

    def tap(self, name, mods=(), hold=0.0):
        if name in MODKEYS:  # a modifier key alone (Super, Alt...)
            if self.chrome:
                k, c, v, b = MODKEYS[name]
                self._c("rawKeyDown", k, c, v, b)
                time.sleep(0.1)
                self._c("keyUp", k, c, v, 0)
            else:
                self.g._actions([{"type": "key", "id": "kbd", "actions": [{"type": "keyDown", "value": WD[name]}, {"type": "pause", "duration": 100}, {"type": "keyUp", "value": WD[name]}]}])
            time.sleep(0.25)
            return
        (self._chrome_tap if self.chrome else self._ff_tap)(name, set(mods), hold)
        time.sleep(0.25)

    def hold(self, name, secs, mods=()):
        self.tap(name, mods, hold=secs)

    def type(self, s, delay=0.05):
        for ch in s:
            self.tap(ch)
            time.sleep(delay)

    def raw(self, key, code, vk, text=None, mods=0):
        """Chrome only: one key exactly as given (a dead key: key 'Dead', keyCode 229)."""
        self._c("keyDown" if text else "rawKeyDown", key, code, vk, mods, text)
        time.sleep(0.08)
        self._c("keyUp", key, code, vk, mods)
        time.sleep(0.25)


# ------------------------------------------------------------------------------------------------------ mouse
BTN = {"left": ("left", 0, 1), "middle": ("middle", 1, 4), "right": ("right", 2, 2)}


class Mouse:
    def __init__(self, g):
        self.g, self.chrome = g, g.name == "Chrome"

    def move(self, x, y):
        self.g.move(x, y)

    def press(self, x, y, button="left", count=1):
        if self.chrome:
            n, _, mask = BTN[button]
            self.g.call("Input.dispatchMouseEvent", type="mousePressed", x=x, y=y, button=n, buttons=mask, clickCount=count)
        else:
            self.g._ptr({"type": "pointerMove", "x": int(x), "y": int(y), "origin": "viewport", "duration": 0},
                        {"type": "pointerDown", "button": BTN[button][1]})

    def release(self, x, y, button="left", count=1):
        if self.chrome:
            n, _, mask = BTN[button]
            self.g.call("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button=n, buttons=0, clickCount=count)
        else:
            self.g._ptr({"type": "pointerMove", "x": int(x), "y": int(y), "origin": "viewport", "duration": 0},
                        {"type": "pointerUp", "button": BTN[button][1]})

    def click(self, x, y, button="left", count=1):
        self.move(x, y)
        time.sleep(0.15)
        if self.chrome:
            for i in range(1, count + 1):
                self.press(x, y, button, i)
                time.sleep(0.05)
                self.release(x, y, button, i)
                time.sleep(0.06)
        else:
            b = BTN[button][1]
            acts = [{"type": "pointerMove", "x": int(x), "y": int(y), "origin": "viewport", "duration": 0}]
            for _ in range(count):
                acts += [{"type": "pointerDown", "button": b}, {"type": "pause", "duration": 40}, {"type": "pointerUp", "button": b},
                         {"type": "pause", "duration": 60}]
            self.g._ptr(*acts)
        time.sleep(0.4)

    def drag(self, x0, y0, x1, y1, button="left", steps=12):
        """Press at (x0,y0), move in steps, release at (x1,y1)."""
        self.move(x0, y0)
        time.sleep(0.2)
        if self.chrome:
            n, _, mask = BTN[button]
            self.press(x0, y0, button)
            time.sleep(0.15)
            for i in range(1, steps + 1):
                self.g.call("Input.dispatchMouseEvent", type="mouseMoved", x=x0 + (x1 - x0) * i / steps, y=y0 + (y1 - y0) * i / steps,
                            button=n, buttons=mask)
                time.sleep(0.05)
            time.sleep(0.15)
            self.release(x1, y1, button)
        else:
            b = BTN[button][1]
            acts = [{"type": "pointerMove", "x": int(x0), "y": int(y0), "origin": "viewport", "duration": 0},
                    {"type": "pointerDown", "button": b}, {"type": "pause", "duration": 150}]
            for i in range(1, steps + 1):
                acts.append({"type": "pointerMove", "x": int(x0 + (x1 - x0) * i / steps), "y": int(y0 + (y1 - y0) * i / steps),
                             "origin": "viewport", "duration": 40})
            acts += [{"type": "pause", "duration": 150}, {"type": "pointerUp", "button": b}]
            self.g._ptr(*acts)
        time.sleep(0.5)

    def wheel(self, x, y, dy=0, dx=0):
        """One wheel turn: dy > 0 = the user turns the wheel DOWN (content moves up), dy < 0 = UP. Pixels of the browser's wheel event."""
        if self.chrome:
            self.g.call("Input.dispatchMouseEvent", type="mouseWheel", x=x, y=y, deltaX=dx, deltaY=dy)
        else:
            self.g._actions([{"type": "wheel", "id": "wheel", "actions": [{"type": "scroll", "x": int(x), "y": int(y), "deltaX": int(dx),
                                                                          "deltaY": int(dy), "origin": "viewport", "duration": 0}]}])
        time.sleep(0.5)


# ------------------------------------------------------------------------------------------------------ the rig
class InputRig(lib.Rig):
    """lib.Rig + window-input.py (any number of windows, each with its own log)."""

    def __init__(self, box, browser, user, password, tag, lang="it-IT", **k):
        # the page asks the server for the layout from navigator.language (page.html layout()): Italian keyboard
        if browser == "firefox":
            k["prefs"] = dict(k.get("prefs") or {}, **{"intl.accept_languages": "%s,%s" % (lang, lang[:2]), "intl.locale.requested": lang[:2]})
        super().__init__(box, browser, user, password, tag, **k)
        self.lang, self.logs = lang, {}
        self.kb = self.mouse = None

    def new_browser(self, size=(1400, 900)):
        if self.browser == "firefox":  # chrome-context access over Marionette (the real clipboard of the browser): only for this process
            orig = lib.spawn
            lib.spawn = lambda cmd, env, log: orig(cmd + ["-remote-allow-system-access"] if "--marionette" in cmd else cmd, env, log)
            try:
                v = super().new_browser(size)
            finally:
                lib.spawn = orig
            self.kb, self.mouse = Kbd(self.g), Mouse(self.g)
            return v
        v = super().new_browser(size)
        self.kb, self.mouse = Kbd(self.g), Mouse(self.g)
        if self.browser == "chrome":
            self.g.call("Emulation.setUserAgentOverride", userAgent=self.g.js("return navigator.userAgent;"), acceptLanguage=self.lang)
            self.g.call("Emulation.setLocaleOverride", locale=self.lang)
        return v

    def language(self):
        return self.g.js("return navigator.language;")

    # --- windows
    def start_input_window(self, name="a", mode="input", colour=None):
        """A window-input.py in the user's session; its log is self.logs[name]. Waits for 'ready'."""
        src = "/tmp/rx-window-%s.py" % self.user
        log = "/tmp/rx-in-%s-%s-%s.log" % (self.user, self.tag, name)
        self.logs[name] = log
        self.box.run("cat > %s; chmod 644 %s; rm -f %s; true" % (src, src, log), stdin=open(os.path.join(HERE, "window-input.py")).read())
        self.box.in_session(self.user, "python3 %s %s %s %s 2>%s.err" % (src, log, mode, colour or "", log))
        end = time.time() + 40
        while time.time() < end:
            if any(e["ev"] == "ready" for e in self.ev(name)):
                time.sleep(1.5)
                return
            time.sleep(1)
        raise ToolError("the input window %s of %s never reported ready: %s" % (name, self.user, self.box.run("tail -c 300 %s.err" % log)[1].replace("\n", " ")))

    def stop_windows(self):
        self.box.run("pkill -u %s -f 'rx-window-%s.py'; true" % (self.user, self.user), timeout=20)
        self.logs.clear()

    def ev(self, name="a"):
        t = self.box.run("cat %s 2>/dev/null; true" % self.logs[name])[1]
        out = []
        for x in t.splitlines():
            if x.startswith("{"):
                try:
                    out.append(json.loads(x))
                except ValueError:
                    pass
        return out

    def mark(self, name="a"):
        return len(self.ev(name))

    def since(self, m, name="a", kinds=None):
        e = self.ev(name)[m:]
        return [x for x in e if not kinds or x["ev"] in kinds]

    def text(self, name="a"):
        t = [e["text"] for e in self.ev(name) if e["ev"] == "text"]
        return t[-1] if t else ""

    def wait_for(self, fn, cap=8, name="a"):
        """Poll fn(events) until true or the cap; returns (value, events)."""
        end, e, v = time.time() + cap, [], None
        while True:
            e = self.ev(name)
            v = fn(e)
            if v or time.time() > end:
                return v, e
            time.sleep(0.5)

    def focus_entry(self, name="a", fx=0.5, fy=0.05):
        """A real click on the entry at the top of the input window: it takes the keyboard focus."""
        self.mouse.click(*self.px(fx, fy))
        time.sleep(0.6)

    def clear_entry(self):
        self.kb.tap("a", {"ctrl"})
        self.kb.tap("Delete")
        time.sleep(0.5)

    def journal_tail(self, grep, n=4, since="-3min"):
        return self.box.journal(grep, since, n)


# ------------------------------------------------------------------------------------------------------ pictures
def cursor_rule(g):
    """The cursor the BROWSER wears over the desktop canvas (what the page sets): (png bytes, hx, hy) or (word, None, None)."""
    css = g.js("const v=document.getElementById('viewer'); return {inline:v.style.cursor, computed:getComputedStyle(v).cursor,"
               " pointer:getComputedStyle(document.getElementById('pointer')||document.body).display, layout:document.body.dataset.layout,"
               " mode:document.body.dataset.pointer};")
    s = (css.get("inline") or "").strip()
    m = re.search(r'url\(\s*["\']?(data:image/png;base64,[^"\')]+)["\']?\s*\)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)', s)
    if m:
        return base64.b64decode(m.group(1).split(",", 1)[1]), float(m.group(2)), float(m.group(3)), css
    return (s or css.get("computed") or "auto"), None, None, css


def classify_cursor(png, hx, hy, alpha_min=100):
    """The class of a cursor image by its pixels: 'arrow', 'text', 'resize-h', 'resize-v', 'resize-diag', 'hidden', 'other'."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGBA")
    W, H = im.size
    px = list(im.getdata())
    pts = [(i % W, i // W) for i, p in enumerate(px) if p[3] >= alpha_min]
    if not pts:
        return "hidden", "%dx%d no opaque pixel" % (W, H)
    x0, x1, y0, y1 = min(p[0] for p in pts), max(p[0] for p in pts), min(p[1] for p in pts), max(p[1] for p in pts)
    w, h = x1 - x0 + 1, y1 - y0 + 1
    filled = set(pts)
    rx, ry = (hx - x0 + 0.5) / w, (hy - y0 + 0.5) / h
    symm_v = sum(1 for (x, y) in filled if (x, y0 + y1 - y) in filled) / len(filled)
    symm_h = sum(1 for (x, y) in filled if (x0 + x1 - x, y) in filled) / len(filled)
    full = len(filled) / float(w * h)
    desc = "%dx%d image, silhouette %dx%d, hotspot (%g,%g) = %.2f,%.2f of it, symmetry up/down %.2f left/right %.2f, filled %.2f" % (
        W, H, w, h, hx, hy, rx, ry, symm_v, symm_h, full)
    if rx <= 0.2 and ry <= 0.2:
        return "arrow", desc
    if 0.25 <= rx <= 0.75 and 0.25 <= ry <= 0.75 and h >= 1.5 * w:
        return "text", desc
    # the arrow-into-a-bar of the resize cursors: the hotspot is on the bar, often at one end of the silhouette
    stem_h = max((sum(1 for x in range(x0, x1 + 1) if (x, y) in filled) for y in (int(hy) - 1, int(hy), int(hy) + 1)), default=0)
    stem_v = max((sum(1 for y in range(y0, y1 + 1) if (x, y) in filled) for x in (int(hx) - 1, int(hx), int(hx) + 1)), default=0)
    if 0.3 <= ry <= 0.7 and w >= 0.8 * h and symm_v >= 0.8 and full <= 0.68 and stem_h >= 0.6 * w:
        return "resize-h", desc
    if 0.3 <= rx <= 0.7 and h >= 0.8 * w and symm_h >= 0.8 and full <= 0.68 and stem_v >= 0.6 * h:
        return "resize-v", desc
    if 0.2 <= ry <= 0.8 and 0.2 <= rx <= 0.8 and 0.6 <= w / float(h) <= 1.6:
        return "resize-diag-or-move", desc
    return "other", desc


def shape_now(g):
    """(class, description, css facts) of the cursor the client shows right now."""
    png, hx, hy, css = cursor_rule(g)
    if isinstance(png, bytes):
        c, d = classify_cursor(png, hx, hy)
        return c, d, css
    return "system:%s" % png, "no remote shape on the canvas: the browser's own cursor (%s)" % png, css


def find_colour(png, rgb, tol=40):
    """Box (x0,y0,x1,y1) of the window painted in colour rgb: the longest horizontal run of that colour (the other bits of the same colour
    that a desktop may have, panel icons, are not part of it), then its vertical extent along the run's margin; or None."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    W, H = im.size
    px = im.load()

    def near(x, y):
        p = px[x, y]
        return sum(abs(p[i] - rgb[i]) for i in range(3)) < tol
    best = (0, 0, 0, 0)
    for y in range(0, H, 4):
        x = 0
        while x < W:
            if near(x, y):
                s = x
                while x < W and near(x, y):
                    x += 1
                if x - s > best[0]:
                    best = (x - s, s, x - 1, y)
            else:
                x += 1
    n, xa, xb, y = best
    if n < 50:
        return None
    xm = xa + 6
    ya = yb = y
    while ya > 0 and near(xm, ya - 1):
        ya -= 1
    while yb < H - 1 and near(xm, yb + 1):
        yb += 1
    return (xa, ya, xb, yb)


def diff_around(png_a, png_b, cx, cy, r=24, thr=40):
    """Pixels of the square around (cx,cy) that differ between two pictures by more than thr in some channel."""
    from PIL import Image
    a, b = (Image.open(io.BytesIO(p)).convert("RGB") for p in (png_a, png_b))
    pa, pb = a.load(), b.load()
    out = []
    for y in range(max(0, int(cy) - r), min(a.size[1], int(cy) + r + 1)):
        for x in range(max(0, int(cx) - r), min(a.size[0], int(cx) + r + 1)):
            d = max(abs(pa[x, y][i] - pb[x, y][i]) for i in range(3))
            if d > thr:
                out.append((x - int(cx), y - int(cy), d))
    return out


def crop_zoom(png, cx, cy, r=24, k=8):
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    c = im.crop((int(cx) - r, int(cy) - r, int(cx) + r + 1, int(cy) + r + 1)).resize(((2 * r + 1) * k, (2 * r + 1) * k), 0)
    b = io.BytesIO()
    c.save(b, "PNG")
    return b.getvalue()


# ------------------------------------------------------------------------------------------------------ touch (Chrome)
PHONE_UA = ("Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Mobile Safari/537.36")


class Touch:
    """Fingers by the DevTools protocol (Input.dispatchTouchEvent): real touchstart/pointerdown events with pointerType touch."""

    def __init__(self, g):
        self.g = g

    def _send(self, type_, pts):
        self.g.call("Input.dispatchTouchEvent", type=type_, touchPoints=[{"x": x, "y": y, "id": i + 1, "radiusX": 4, "radiusY": 4, "force": 1} for i, (x, y) in enumerate(pts)])

    def tap(self, x, y, hold=0.06):
        self._send("touchStart", [(x, y)])
        time.sleep(hold)
        self._send("touchEnd", [])
        time.sleep(0.3)

    def multi_tap(self, pts, hold=0.07):
        """Several fingers down together, up together (a 2- or 3-finger tap)."""
        self._send("touchStart", pts)
        time.sleep(hold)
        self._send("touchEnd", [])
        time.sleep(0.4)

    def drag(self, x0, y0, x1, y1, steps=12, dt=0.025, hold_start=0.05):
        self._send("touchStart", [(x0, y0)])
        time.sleep(hold_start)
        for i in range(1, steps + 1):
            self._send("touchMove", [(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps)])
            time.sleep(dt)
        time.sleep(0.05)
        self._send("touchEnd", [])
        time.sleep(0.4)

    def multi_drag(self, starts, ends, steps=15, dt=0.025):
        """Several fingers moving together from `starts` to `ends` (two-finger scroll, pinch)."""
        self._send("touchStart", starts)
        time.sleep(0.06)
        for i in range(1, steps + 1):
            self._send("touchMove", [(sx + (ex - sx) * i / steps, sy + (ey - sy) * i / steps) for (sx, sy), (ex, ey) in zip(starts, ends)])
            time.sleep(dt)
        time.sleep(0.05)
        self._send("touchEnd", [])
        time.sleep(0.4)

    def tap_and_half(self, x, y, dx, dy, gap=0.1, steps=15):
        """Tap, then within `gap` s a finger down near the same place that drags by (dx,dy): the drag-and-select gesture."""
        self._send("touchStart", [(x, y)])
        time.sleep(0.06)
        self._send("touchEnd", [])
        time.sleep(gap)
        self._send("touchStart", [(x + 3, y + 3)])
        time.sleep(0.08)
        for i in range(1, steps + 1):
            self._send("touchMove", [(x + 3 + dx * i / steps, y + 3 + dy * i / steps)])
            time.sleep(0.03)
        time.sleep(0.1)
        self._send("touchEnd", [])
        time.sleep(0.5)
