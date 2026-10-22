#!/usr/bin/env python3
"""12-real-clients — THE REAL CLIENT TEST, on three browsers, with a verdict for each.

    python3 benches/12-real-clients.py --url https://192.168.0.2:8511/ \\
        --user prova --password '…' [--browser firefox,chrome,android] \\
        [--visible] [--cap-s 30] [--scene move|live|still] \\
        [--log-cmd "ssh … tail -n 3000 …/registro.log"] [--certify]

⭐ WHAT IT DOES.  It opens REMOTIX in a REAL browser — Firefox 140 ESR driven with
   Marionette (`07-b46-marionette.py`), Google Chrome driven with the DevTools
   protocol, and Chrome for Android in the `remotix` emulator, driven with the
   same protocol through `adb forward` — and for each it looks at seven things:

     a  the page opens (certificate accepted) and the login form is there
     b  with `--user`/`--password` the page is ADMITTED
     c  FIRST FRAME: the canvas has NON-degenerate pixels within `--cap-s`
     d  CONTINUITY: the frames keep arriving (see "the scene")
     e  INPUT: a key and a move+click (a tap on Android) reach the server
     f  the page's JavaScript errors and network errors (and what the page
        itself declares with "⛔" in its log)
     g  RECONNECTION: reload, log in again, and there is the first frame again

   Each point has an outcome: 0 green · 1 red · 3 "I could not look", with the
   reason.  ⛔ NEVER A GIFTED GREEN: if the tool could not look, it is 3.
   The browser's verdict is PASS (all 0) · FAIL (at least one 1) · BLOCKED
   (no 1, but at least one 3).  At the end of each browser, a JSON line.

⛔ WHERE THE STATE IS READ FROM — and it is read from the PAGE, not from the layout
   (`src/page.html`, line numbers as of 18 Sep 2026):
     · admitted: `REMOTIX.viewer.session === true` (set by `negozia()`,
       line ~2816, and the worker branch line ~8234) AND `#outcome` with class
       `bene` and text "Admitted, … session …" (line ~5058).  Refusal is `#outcome`
       with class `male` (line 622 and the branches of `collega()`).
     · first frame and continuity: `REMOTIX.viewer.counts.painted` (line
       ~2689, grows at lines ~3186/3675/4099) — the phase's gauge, which the
       page itself reads in the first-frame watch.
     · the pixels: a PHOTOGRAPH of the canvas taken by the browser (CDP
       `Page.captureScreenshot`, Marionette `TakeScreenshot` with `id`).  ⚠ Not
       `getImageData`: the canvas may be `bitmaprenderer` or handed to a
       worker (`transferControlToOffscreen`, line ~8145), and there reading from
       the document sees nothing.  The photograph sees what the user sees.
     · input: the bench WRAPS `window.REMOTIX_INPUT.send` (line ~5130) and
       counts by type what the page really sent (the `id` is in the
       first 4 bytes of the body, §7.3).  ⭐ And arrival at the server is proven in two
       independent ways: the lines "input id=… POINTER/BUTTON/
       KEY_POSITION" in the server log (`src/rcp.c` ~4726), if there is
       `--log-cmd`; and from the page, with `REMOTIX.round_trip` (line ~2197): a
       frame that brings back `id` N proves the server has
       applied all inputs up to N (the input stream is one and
       ordered, §2.5).  ⚠ A frame arrives only if the screen CHANGES:
       without log and without return, the outcome is 3, not 1.
     · the page log: the text of `#logbook` (`nota()` lines, line
       473) — the "⛔" lines are taken from there.

⚠ THE SCENE IS DECLARED (`--scene`).  A still desktop sends NO frames, and
  zero frames on a still desktop is the right thing:
     · `still`  no new frame ⇒ 3 (it cannot be told apart)
     · `live`   whoever launches GUARANTEES that something moves ⇒ zero frames is 1
     · `move`   (default) the bench moves the pointer over the canvas for
                `--continuity-s` seconds, crossing the whole desktop ⇒ zero
                frames is 1.  ⚠ The cursor is drawn by the page, not by the
                server: the frame is born only if the desktop reacts to the
                passage (highlights, bar, dock).  On a desktop that does not
                react, use `live` with a scene running.

⚠ HEADLESS IS DECLARED.  Without `--visible` Firefox and Chrome run headless,
  that is without GPU: decoding and drawing are in SOFTWARE.  The Android
  emulator uses `swiftshader_indirect`, that is software too.  The outcome
  line carries it written: this bench judges BEHAVIOUR, not numbers.

⛔ THE CERTIFICATION (`PLAN.md` §0.3 rule 4) — `--certify` proves that the
   bench can give red, before believing its green:
     1. a port where there is no server ⇒ (a) MUST be red;
     2. the WRONG password against `--url` ⇒ (b) MUST be red BY
        REFUSAL (the page sent the credentials and the server did not
        admit it), not for a missed connection: without a server answering
        the second test is "not certified" (3), not green.
        ⚠ It uses ONE login attempt on the server: it counts towards the ban.
     3. the pixel judge is tested on two images made here: an all-black
        canvas MUST be degenerate, a gradient NOT.

⚠ The ports: Marionette 2851, Chrome DevTools 9341, Android DevTools 9342
  (local, via `adb forward`).  They are changed with `--base-port`.
"""
import argparse
import base64
import importlib.util as _iu
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.expanduser("~")
ADB = os.path.join(CASA, "Android/Sdk/platform-tools/adb")
EMU = os.path.join(CASA, "Android/Sdk/emulator/emulator")
# ⛔ 19 Sep 2026 — NOT the system image's Chrome (113): WebCodecs on
#    Chrome for Android exists from 147 (`DECISIONS.md` line ~425), and `[M]` the
#    113 already falls at WebTransport (`ERR_METHOD_NOT_SUPPORTED`).  ⇒ Chromium for
#    Android from the official Chromium build archive (AndroidDesktop_x64,
#    `ChromePublic.apk`, 156.0.8067.0, in `~/Android/chromium/`), declared
#    as Chromium.  ⛔ Firefox for Android is NOT supported (§7.18).
#    ⚠ And Chromium does NOT work: `[M]` the public builds have no H.264
#    (`isConfigSupported` says no to `avc1.*`) ⇒ the page has no codec at all.
#    ⇒ The REAL Chrome of the Android 17 image is used (`remotix37`, Chrome
#    145.0.7632.218).  Both can be changed without touching the file:
#    `REMOTIX_ANDROID_PACKAGE`, `REMOTIX_AVD`.
CHROME_ANDROID = os.environ.get("REMOTIX_ANDROID_PACKAGE", "com.android.chrome")
AVD = os.environ.get("REMOTIX_AVD", "remotix37")


def _load(name, file):
    s = _iu.spec_from_file_location(name, os.path.join(HERE, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MARIONETTE = _load("marionette", "07-b46-marionette.py")
CDPMOD = _load("cdp", "02-page-measure-cdp.py")

GREEN, RED, BLIND = 0, 1, 3
POINT_NAMES = {
    "a": "the page opens and the form is there",
    "b": "admitted with user and password",
    "c": "first frame, non-degenerate pixels",
    "d": "continuity of the frames",
    "e": "input: key and mouse/touch reach the server",
    "f": "JavaScript and network errors",
    "g": "reconnection: reload, log in again, first frame",
}
INPUT_TYPES = {0x0101: "POINTER", 0x0102: "BUTTON", 0x0103: "WHEEL",
              0x0104: "LETTER", 0x0105: "KEY_POSITION"}


# ═══════════════════════════════════════════════════════════════════════════
#  THE PIXEL JUDGE
# ═══════════════════════════════════════════════════════════════════════════
def judge_pixel(png):
    """Returns (degenerate: bool|None, description).  None = I could not look.

    ⛔ Degenerate means: one colour only (or nearly) over the whole canvas — black,
       waiting magenta, grey.  A real desktop has at least a bar, some
       text, an icon: the dominant colour is required to cover less than 97 %
       and the luminance to have a deviation of at least 3 levels."""
    try:
        from PIL import Image
    except ImportError:
        return None, "PIL is not there: I cannot read the photograph"
    try:
        im = Image.open(io.BytesIO(png)).convert("RGB")
    except Exception as e:                       # noqa: BLE001
        return None, "unreadable photograph: %s" % e
    l, a = im.size
    if l < 8 or a < 8:
        return True, "photograph of %dx%d: the canvas has no size" % (l, a)
    pic = im.resize((min(160, l), min(120, a)))
    px = list(pic.getdata())
    n = len(px)
    count = {}
    for p in px:
        q = (p[0] >> 3, p[1] >> 3, p[2] >> 3)
        count[q] = count.get(q, 0) + 1
    dom_q, dom_n = max(count.items(), key=lambda kv: kv[1])
    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px]
    media = sum(lum) / n
    dev = (sum((x - media) ** 2 for x in lum) / n) ** 0.5
    quota = dom_n / n
    desc = ("%dx%d · distinct colours %d · dominant %.1f%% (%d,%d,%d) · "
            "mean luminance %.0f dev %.1f"
            % (l, a, len(count), 100 * quota, dom_q[0] << 3, dom_q[1] << 3,
               dom_q[2] << 3, media, dev))
    return (quota >= 0.97 or dev < 3.0), desc


def certify_judge():
    """The pixel judge must be able to say "degenerate"."""
    try:
        from PIL import Image
    except ImportError:
        return BLIND, "PIL is not there"
    def png(im):
        b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()
    nero = Image.new("RGB", (640, 400), (0, 0, 0))
    gradient = Image.new("RGB", (640, 400))
    gradient.putdata([(x % 256, (y * 2) % 256, (x + y) % 256)
                  for y in range(400) for x in range(640)])
    d1, t1 = judge_pixel(png(nero))
    d2, t2 = judge_pixel(png(gradient))
    ok = d1 is True and d2 is False
    return (GREEN if ok else RED,
            "black canvas ⇒ %s (%s) · gradient ⇒ %s (%s)"
            % ("degenerate" if d1 else "⛔ NOT degenerate", t1,
               "not degenerate" if d2 is False else "⛔ degenerate", t2))


# ═══════════════════════════════════════════════════════════════════════════
#  THE JAVASCRIPT PIECES — function bodies, with `return`
# ═══════════════════════════════════════════════════════════════════════════
JS_MODULE = r"""
const m = document.getElementById('signin-form');
const vis = (e) => !!e && getComputedStyle(e).display !== 'none'
                   && getComputedStyle(e).visibility !== 'hidden'
                   && e.getBoundingClientRect().width > 0;
return { url: location.href, title: document.title,
         ready: document.readyState,
         form: !!m, visible: vis(m),
         user: !!document.getElementById('username'),
         password: !!document.getElementById('password'),
         signin_button: !!document.getElementById('signin-button'),
         remotix: !!window.REMOTIX,
         banned: document.body ? document.body.dataset.banned || null : null,
         warning: (document.getElementById('warning') || {}).textContent || '',
         text: document.body ? document.body.innerText.slice(0, 300) : '' };
"""

# ⚠ The value is put in the field and `requestSubmit()` is asked of the form: it is
#   the same `submit` handler that starts the page when the user
#   presses "Connect" (page.html ~8445).  Nothing is typed at coordinates.
JS_ENTER = r"""
const u = document.getElementById('username'), p = document.getElementById('password');
const m = document.getElementById('signin-form');
if (!u || !p || !m) return 'the form is missing';
u.value = arguments[0]; p.value = arguments[1];
u.dispatchEvent(new Event('input', {bubbles: true}));
p.dispatchEvent(new Event('input', {bubbles: true}));
if (m.requestSubmit) m.requestSubmit(document.getElementById('signin-button'));
else document.getElementById('signin-button').click();
return 'sent';
"""

JS_STATE = r"""
const R = window.REMOTIX, s = R && R.viewer;
const e = document.getElementById('outcome');
const reg = document.getElementById('logbook');
let g = null;
try { if (R && R.round_trip) g = { seen: R.round_trip.seen, attesa: R.round_trip.when.size }; } catch (x) {}
const t = document.getElementById('viewer');
const r = t ? t.getBoundingClientRect() : null;
return {
  session: !!(s && s.session),
  outcome_class: e ? e.className : null,
  outcome: e ? e.textContent : null,
  painted: s && s.counts ? s.counts.painted : null,
  delivered: s && s.counts ? s.counts.delivered : null,
  on: document.body ? (document.body.dataset.viewer || null) : null,
  input: !!window.REMOTIX_INPUT,
  giro: g,
  canvas: r ? [r.left, r.top, r.width, r.height] : null,
  buffer: t ? [t.width, t.height] : null,
  view: [innerWidth, innerHeight, devicePixelRatio || 1],
  log: reg ? reg.textContent : '',
  screen_errors: s && s.errors ? s.errors.slice(-5).map(String) : [],
  bench: window.__BANCO__ ? { errors: window.__BANCO__.errori.slice(0, 40),
                              network: window.__BANCO__.rete.slice(0, 40) } : null,
  ingresso: window.__BANCO_IN__ ? window.__BANCO_IN__ : null,
};
"""

# ⭐ The error collector.  In Chrome it goes in BEFORE the page
#   (`Page.addScriptToEvaluateOnNewDocument`); in Firefox it goes in after the load
#   and that is declared — the earlier errors are caught by the browser's output
#   (`devtools.console.stdout.content`).
COLLECTOR = r"""
(function () {
  if (window.__BANCO__) return;
  const B = window.__BANCO__ = { errori: [], rete: [] };
  const metti = (a, t) => { if (a.length < 200) a.push(String(t).slice(0, 400)); };
  addEventListener('error', (ev) => {
    if (ev.target && ev.target !== window && (ev.target.src || ev.target.href))
      metti(B.rete, 'resource not loaded: ' + (ev.target.src || ev.target.href));
    else metti(B.errori, 'exception: ' + ev.message + ' @' + (ev.filename || '')
                         + ':' + (ev.lineno || ''));
  }, true);
  addEventListener('unhandledrejection', (ev) => {
    const r = ev.reason;
    metti(B.errori, 'rejected promise: ' + (r && r.stack ? r.stack.split('\n')[0] : r));
  });
  const ce = console.error.bind(console);
  console.error = function () {
    try { metti(B.errori, 'console.error: ' + Array.from(arguments).join(' ')); } catch (x) {}
    return ce.apply(null, arguments);
  };
})();
"""

# ⭐ The input link.  It wraps the seam's `send_msg` (line ~5130): it counts
#   by type what the page SENT, with the `id` taken from the first 4 bytes
#   of the body (§7.3, big-endian).  ⚠ It changes nothing of what the page
#   sends: it calls the real `send_msg` with the same arguments.
JS_LINK = r"""
(function () {
  const c = window.REMOTIX_INPUT;
  if (!c || typeof c.send !== 'function' || c.__banco) return;
  const vero = c.send;
  const B = window.__BANCO_IN__ = window.__BANCO_IN__ || { tipi: {}, ids: {} };
  c.send = function (tipo, corpo) {
    try {
      const id = new DataView(corpo.buffer, corpo.byteOffset, 4).getUint32(0);
      B.tipi[tipo] = (B.tipi[tipo] || 0) + 1;
      (B.ids[tipo] = B.ids[tipo] || []).push(id);
      if (B.ids[tipo].length > 400) B.ids[tipo].shift();
    } catch (x) {}
    return vero.apply(this, arguments);
  };
  c.__banco = true;
})();
"""

# ⭐ Which `id`s came back in a frame: the sent ones that
#   `ROUND.when` no longer has (`go_back()` deletes them, line ~2211).
JS_RETURNED = r"""
const B = window.__BANCO_IN__, R = window.REMOTIX;
if (!B || !R || !R.round_trip) return null;
let max_tornato = 0;
const per_tipo = {};
for (const t in B.ids) {
  per_tipo[t] = B.ids[t].slice();
  for (const id of B.ids[t]) if (!R.round_trip.when.has(id) && id > max_tornato) max_tornato = id;
}
return { max_tornato: max_tornato, ids: per_tipo, tipi: B.tipi, seen: R.round_trip.seen };
"""


def _inject(body):
    """A body to run in the REAL page, not in the driver's sandbox:
    in Firefox a function born in Marionette's sandbox and called by the
    page goes through the "xrays" and may not work.  ⇒ `<script>` in the DOM."""
    return ("const s = document.createElement('script');"
            "s.textContent = %s;"
            "(document.head || document.documentElement).appendChild(s); s.remove();"
            "return true;" % json.dumps(body))


# ═══════════════════════════════════════════════════════════════════════════
#  THE DRIVERS — one per browser, the same face
# ═══════════════════════════════════════════════════════════════════════════
class Cdp(CDPMOD.Cdp):
    """The CDP client of `02-page-measure-cdp.py`, which however KEEPS the events:
    exceptions and console messages arrive as events while
    waiting for the answer to a command, and it used to throw them away."""

    def __init__(self, url, timeout=60):
        super().__init__(url, timeout)
        self.events = []

    def call(self, method, **parameters):
        self.n += 1
        my = self.n
        self.ws.send_msg(json.dumps({"id": my, "method": method, "params": parameters}))
        while True:
            r = json.loads(self.ws.receive())
            if "method" in r and "id" not in r:
                if len(self.events) < 5000:
                    self.events.append(r)
                continue
            if r.get("id") != my:
                continue
            if "error" in r:
                raise RuntimeError(method + ": " + json.dumps(r["error"]))
            return r.get("result", {})


class CdpDriver:
    """Desktop Chrome and Chrome for Android: same protocol."""
    touch = False

    def __init__(self, port, name):
        self.port, self.name = port, name
        self.cdp = None

    def hook(self, wait=40):
        b = CDPMOD.page(self.port, wait)
        self.cdp = Cdp(b["webSocketDebuggerUrl"])
        for d in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
            try:
                self.cdp.call(d)
            except Exception:                    # noqa: BLE001
                pass
        self.cdp.call("Page.addScriptToEvaluateOnNewDocument", source=COLLECTOR)
        try:
            self.cdp.call("Emulation.setFocusEmulationEnabled", enabled=True)
        except Exception:                        # noqa: BLE001
            pass

    def version(self):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % self.port,
                                        timeout=5) as r:
                return json.loads(r.read().decode()).get("Browser", "?")
        except Exception as e:                   # noqa: BLE001
            return "? (%s)" % e

    def js(self, body, *arg):
        expr = "(function(){%s}).apply(null, %s)" % (body, json.dumps(list(arg)))
        r = self.cdp.call("Runtime.evaluate", expression=expr,
                            returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise RuntimeError("exception in the bench: %s"
                               % json.dumps(r["exceptionDetails"])[:300])
        return r.get("result", {}).get("value")

    def navigate(self, url):
        """Returns (opened, reason).  ⭐ The certificate is accepted as the user
        accepts it: the "Advanced" panel → "Proceed".  No flag that
        turns off the checks: with `--ignore-certificate-errors` WebTransport too
        would stop looking at the fingerprint, and the bench would test
        a browser the user does not have."""
        r = self.cdp.call("Page.navigate", url=url)
        err = r.get("errorText")
        time.sleep(1.5)
        for _ in range(3):
            try:
                panel = self.js(
                    "return !!document.getElementById('proceed-link')"
                    " || !!document.getElementById('details-button');")
            except Exception:                    # noqa: BLE001
                panel = False
            if not panel:
                break
            self.js("const d=document.getElementById('details-button'); if (d) d.click();"
                    "const p=document.getElementById('proceed-link'); if (p) p.click();"
                    "return 1;")
            time.sleep(3)
        if err and "CERT" not in err:
            return False, err
        return True, err or ""

    def reload(self):
        self.cdp.call("Page.reload", ignoreCache=False)
        time.sleep(1.5)

    def snapshot_canvas(self):
        r = self.js("const t=document.getElementById('viewer');"
                    "if(!t) return null; const b=t.getBoundingClientRect();"
                    "const x=Math.max(0,b.left), y=Math.max(0,b.top);"
                    "return [x, y, Math.min(innerWidth,b.right)-x,"
                    " Math.min(innerHeight,b.bottom)-y];")
        if not r or r[2] < 4 or r[3] < 4:
            return None, "the canvas has no visible area: %s" % (r,)
        scale_factor = min(1.0, 640.0 / r[2])
        s = self.cdp.call("Page.captureScreenshot", format="png",
                            clip={"x": r[0], "y": r[1], "width": r[2],
                                  "height": r[3], "scale": scale_factor})
        return base64.b64decode(s["data"]), ""

    # -- input: protocol events, that is TRUSTED events in the renderer -------
    def move_to(self, x, y):
        self.cdp.call("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)

    def click(self, x, y):
        self.move_to(x, y)
        for t in ("mousePressed", "mouseReleased"):
            self.cdp.call("Input.dispatchMouseEvent", type=t, x=x, y=y,
                            button="left", clickCount=1)

    def touches(self, x, y):
        self.cdp.call("Input.dispatchTouchEvent", type="touchStart",
                        touchPoints=[{"x": x, "y": y}])
        time.sleep(0.08)
        self.cdp.call("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])

    def drag(self, points):
        self.cdp.call("Input.dispatchTouchEvent", type="touchStart",
                        touchPoints=[{"x": points[0][0], "y": points[0][1]}])
        for x, y in points[1:]:
            time.sleep(0.05)
            self.cdp.call("Input.dispatchTouchEvent", type="touchMove",
                            touchPoints=[{"x": x, "y": y}])
        self.cdp.call("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])

    def key(self, t):
        k = KEY_LIST[t]
        mod = 2 if t == "Control" else 0
        self.cdp.call("Input.dispatchKeyEvent", type="rawKeyDown", key=k["key"],
                        code=k["code"], windowsVirtualKeyCode=k["vk"], modifiers=mod)
        time.sleep(0.08)
        self.cdp.call("Input.dispatchKeyEvent", type="keyUp", key=k["key"],
                        code=k["code"], windowsVirtualKeyCode=k["vk"])

    def errors_out(self):
        """The errors seen by the PROTOCOL, independent of the page."""
        try:
            self.cdp.call("Runtime.evaluate", expression="1")   # drains the queue
        except Exception:                        # noqa: BLE001
            pass
        js, network = [], []
        for e in self.cdp.events:
            m, p = e.get("method"), e.get("params", {})
            if m == "Runtime.exceptionThrown":
                d = p.get("exceptionDetails", {})
                ex = d.get("exception", {})
                js.append("exception: %s" % (ex.get("description") or d.get("text"))
                          .split("\n")[0][:300])
            elif m == "Runtime.consoleAPICalled" and p.get("type") == "error":
                js.append("console.error: " + " ".join(
                    str(a.get("value", a.get("description", ""))) for a in p.get("args", []))[:300])
            elif m == "Log.entryAdded":
                en = p.get("entry", {})
                if en.get("level") == "error":
                    # ⚠ the favicon is not there and it is not a defect: it is dropped by name
                    if (en.get("url") or "").endswith("/favicon.ico"):
                        continue
                    (network if en.get("source") == "network" else js).append(
                        "%s: %s%s" % (en.get("source"), en.get("text", "")[:300],
                                      " [%s]" % en["url"] if en.get("url") else ""))
            elif m == "Network.loadingFailed":
                # ⚠ the document's certificate error is the one the bench
                #   accepts on purpose from the "Proceed" panel: it is not a defect
                if p.get("canceled") or (p.get("type") == "Document"
                                         and "ERR_CERT_" in (p.get("errorText") or "")):
                    continue
                network.append("network: %s (%s)" % (p.get("errorText"), p.get("type")))
        return js, network, ""

    def reset_events(self):
        self.cdp.events = []


KEY_LIST = {
    "Control": {"key": "Control", "code": "ControlLeft", "vk": 17, "wd": "\ue009"},
    "ArrowRight": {"key": "ArrowRight", "code": "ArrowRight", "vk": 39, "wd": "\ue014"},
}


# ⭐ The window size of the two browsers, "WxH".  ⚠ It is changed with
#   `--window`: `[M]` 24 Sep 2026, Firefox's green strip depends on the
#   WIDTH (8 px at 1400, 12 at 1348), and a bench with a fixed window sees only one.
WINDOW = [1400, 1000]


class ChromeDriver(CdpDriver):
    def __init__(self, port, visible):
        super().__init__(port, "chrome")
        self.visible = visible
        self.profile = tempfile.mkdtemp(prefix="remotix-cr-")
        cmd = ["google-chrome", "--remote-debugging-port=%d" % port,
               "--user-data-dir=" + self.profile, "--no-first-run",
               "--no-default-browser-check", "--disable-sync",
               "--password-store=basic", "--window-size=%d,%d" % tuple(WINDOW),
               "--remote-allow-origins=*"]
        if not visible:
            cmd.append("--headless=new")
        # ⚠ Extra options declared by whoever launches: `[M]` 24 Sep 2026, on the
        #   server inside a labwc without a screen Chrome looked for X11 and did not
        #   start ⇒ `REMOTIX_CHROME_OPTIONS="--ozone-platform=wayland"`.
        cmd += os.environ.get("REMOTIX_CHROME_OPTIONS", "").split()
        cmd.append("about:blank")
        self.log = open(os.path.join(self.profile, "uscita.log"), "wb")
        self.p = subprocess.Popen(cmd, stdout=self.log, stderr=subprocess.STDOUT)
        self.hook()

    def stage(self):
        return "%s · %s" % (self.version(), "real window" if self.visible
                            else "HEADLESS — no GPU, all in software")

    def close(self):
        try:
            self.cdp.call("Page.navigate", url="about:blank")   # pagehide ⇒ FAREWELL
            time.sleep(1)
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.cdp.call("Browser.close")
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.p.wait(10)
        except Exception:                        # noqa: BLE001
            self.p.kill()
        shutil.rmtree(self.profile, ignore_errors=True)


def adb(*v, t=60):
    try:
        return subprocess.run([ADB] + list(v), capture_output=True, text=True,
                              timeout=t).stdout or ""
    except Exception as e:                       # noqa: BLE001
        return "⛔ %s" % e


class AndroidDriver(CdpDriver):
    """Chrome in the `remotix` emulator.  ⛔ The emulator eats RAM: the bench
    starts it if it is not there, and the bench stops it if it started it."""
    touch = True

    def __init__(self, port, leave_on):
        super().__init__(port, "android")
        self.turned_on_by_me = False
        self.leave = leave_on
        if "\tdevice" not in adb("devices"):
            print("   ⏳ starting the emulator «%s»…" % AVD, flush=True)
            subprocess.Popen([EMU, "-avd", AVD, "-no-window", "-no-audio",
                              "-no-boot-anim", "-gpu", "swiftshader_indirect",
                              "-no-snapshot", "-accel", "on", "-memory", "3072"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.turned_on_by_me = True
            t0 = time.time()
            while time.time() - t0 < 300:
                if adb("shell", "getprop", "sys.boot_completed").strip() == "1":
                    break
                time.sleep(4)
            else:
                raise RuntimeError("the emulator did not finish booting in 300 s")
            time.sleep(5)
        # ⭐ The flags are read from `/data/local/tmp/chrome-command-line` only
        #   if Chrome is the "debug" app; the first name on the line is ignored.
        adb("shell", "echo 'chrome --disable-fre --no-default-browser-check "
                     "--no-first-run --disable-signin-promo' "
                     "> /data/local/tmp/chrome-command-line")
        adb("shell", "am", "set-debug-app", "--persistent", CHROME_ANDROID)
        adb("shell", "am", "force-stop", CHROME_ANDROID)
        time.sleep(1)
        adb("shell", "am", "start", "-n",
            CHROME_ANDROID + "/com.google.android.apps.chrome.Main",
            "-a", "android.intent.action.VIEW", "-d", "about:blank")
        adb("forward", "tcp:%d" % port, "localabstract:chrome_devtools_remote")
        time.sleep(4)
        self.hook(wait=60)

    def stage(self):
        v = adb("shell", "dumpsys", "package", CHROME_ANDROID)
        ver = v.split("versionName=")[1].split()[0] if "versionName=" in v else "?"
        return ("%s %s on Android %s (emulator «%s», swiftshader GPU: SOFTWARE)"
                % ("Chromium" if "chromium" in CHROME_ANDROID else "Chrome", ver,
                   adb("shell", "getprop", "ro.build.version.release").strip(), AVD))

    def move_to(self, x, y):
        # ⚠ On Android the "mouse" is a finger: a move is a drag
        self.drag([(x, y), (x + 20, y + 10)])

    def click(self, x, y):
        self.touches(x, y)

    def close(self):
        try:
            self.cdp.call("Page.navigate", url="about:blank")   # pagehide ⇒ FAREWELL
            time.sleep(1)
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.cdp.close()
        except Exception:                        # noqa: BLE001
            pass
        adb("shell", "am", "force-stop", CHROME_ANDROID)
        adb("forward", "--remove", "tcp:%d" % self.port)
        if self.turned_on_by_me and not self.leave:
            print("   ⏹ stopping the emulator (I had started it)", flush=True)
            adb("emu", "kill")
            t0 = time.time()
            while time.time() - t0 < 30 and "emulator-" in adb("devices"):
                time.sleep(2)


class FirefoxDriver:
    touch = False

    def __init__(self, port, visible):
        self.name = "firefox"
        self.visible = visible
        self.p, self.m, self.profile = MARIONETTE.turn_on(
            port=port, headless=not visible, largo=WINDOW[0], alto=WINDOW[1])
        # ⚠ `acceptInsecureCerts` must be given ALSO outside `alwaysMatch`: `[M]` 18
        #   Sep 2026, Firefox 140 with only the form of `07-b46`
        #   (`session()`) refuses the self-signed certificate ("insecure
        #   certificate"); with both it accepts it.  It is the exception the
        #   user adds by hand from the panel.
        self.caps = self.m.call("WebDriver:NewSession", {
            "capabilities": {"alwaysMatch": {"acceptInsecureCerts": True}},
            "acceptInsecureCerts": True})
        self.log = os.path.join(self.profile, "uscita.log")
        self.log_da = 0
        self.m.call("WebDriver:SetTimeouts", {"script": 60000, "pageLoad": 60000})

    def stage(self):
        c = (self.caps or {}).get("capabilities", {})
        return "Firefox %s · %s" % (c.get("browserVersion", "?"),
                                    "real window" if self.visible
                                    else "HEADLESS — no GPU, all in software")

    def js(self, body, *arg):
        return self.m.js(body, list(arg))["value"]

    def navigate(self, url):
        try:
            self.m.navigate(url)
        except RuntimeError as e:
            return False, str(e)[:300]
        time.sleep(1)
        try:
            self.js(_inject(COLLECTOR))
        except Exception:                        # noqa: BLE001
            pass
        return True, ""

    def reload(self):
        self.m.call("WebDriver:Refresh")
        time.sleep(1)
        try:
            self.js(_inject(COLLECTOR))
        except Exception:                        # noqa: BLE001
            pass

    def snapshot_canvas(self):
        el = self.m.call("WebDriver:FindElement",
                           {"using": "css selector", "value": "#viewer"})["value"]
        # ⚠ Marionette has no `TakeElementScreenshot` (it is the W3C name on the
        #   geckodriver side): the element is passed to `TakeScreenshot` with `id`.
        r = self.m.call("WebDriver:TakeScreenshot",
                          {"id": list(el.values())[0], "full": False})
        return base64.b64decode(r["value"]), ""

    def _actions(self, actions):
        self.m.call("WebDriver:PerformActions", {"actions": actions})
        self.m.call("WebDriver:ReleaseActions")

    def move_to(self, x, y):
        self._actions([{"type": "pointer", "id": "topo",
                       "parameters": {"pointerType": "mouse"},
                       "actions": [{"type": "pointerMove", "x": int(x), "y": int(y),
                                    "origin": "viewport", "duration": 0}]}])

    def click(self, x, y):
        self._actions([{"type": "pointer", "id": "topo",
                       "parameters": {"pointerType": "mouse"},
                       "actions": [{"type": "pointerMove", "x": int(x), "y": int(y),
                                    "origin": "viewport", "duration": 0},
                                   {"type": "pointerDown", "button": 0},
                                   {"type": "pause", "duration": 60},
                                   {"type": "pointerUp", "button": 0}]}])

    def key(self, t):
        w = KEY_LIST[t]["wd"]
        self._actions([{"type": "key", "id": "tastiera",
                       "actions": [{"type": "keyDown", "value": w},
                                   {"type": "pause", "duration": 80},
                                   {"type": "keyUp", "value": w}]}])

    def errors_out(self):
        """⚠ From Firefox the errors "from outside" are read in its output
        (`devtools.console.stdout.content`, turned on by `07-b46`)."""
        try:
            with open(self.log, "rb") as f:
                f.seek(self.log_da)
                text = f.read().decode("utf-8", "replace")
        except OSError as e:
            return [], [], "Firefox output unreadable: %s" % e
        js, network = [], []
        for r in text.splitlines():
            if r.startswith("JavaScript error:"):
                # ⚠ only the PAGE's errors: those of Firefox's internal
                #   modules (`resource://`, `chrome://`) are not ours
                if "resource://" in r[:60] or "chrome://" in r[:60]:
                    continue
                js.append(r[:300])
            elif r.startswith("console.error:"):
                js.append(r[:300])
            elif "NS_ERROR_NET" in r or "NS_ERROR_CONNECTION" in r:
                network.append(r[:300])
        return js, network, ""

    def reset_events(self):
        try:
            self.log_da = os.path.getsize(self.log)
        except OSError:
            self.log_da = 0

    def close(self):
        try:
            self.m.navigate("about:blank")                             # pagehide ⇒ FAREWELL
            time.sleep(1)
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.m.call("Marionette:Quit")
        except Exception:                        # noqa: BLE001
            pass
        MARIONETTE.turn_off(self.p, self.profile)


# ═══════════════════════════════════════════════════════════════════════════
#  THE SERVER LOG
# ═══════════════════════════════════════════════════════════════════════════
def read_log(cmd):
    if not cmd:
        return None, "no --log-cmd"
    try:
        # ⛔ `errors="replace"`: the log carries ⭐ ⛔ ⚠ →, and whoever cuts it
        #    (`cut -c`, `tail -c`) breaks the three-byte letters.  `[M]` 23 Sep
        #    2026: with strict utf-8 the bench DIES of `UnicodeDecodeError`
        #    instead of returning an error — and the measurement already made is lost.
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           errors="replace", timeout=60)
    except Exception as e:                       # noqa: BLE001
        return None, "the log command did not answer: %s" % e
    if r.returncode != 0 and not r.stdout:
        return None, "the log command failed (%d): %s" % (
            r.returncode, r.stderr.strip()[:200])
    return r.stdout.splitlines(), ""


def new_lines(before, after):
    """The lines of `after` that were not in `before` — counting duplicates."""
    observed = {}
    for r in before:
        observed[r] = observed.get(r, 0) + 1
    report = []
    for r in after:
        if observed.get(r, 0):
            observed[r] -= 1
        else:
            report.append(r)
    return report


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST OF ONE BROWSER
# ═══════════════════════════════════════════════════════════════════════════
class Test:
    def __init__(self, g, o, url, password):
        self.g, self.o, self.url, self.password = g, o, url, password
        self.outcomes = {}                            # point -> (outcome, reason)
        self.note = []
        self.refusal = None

    def put(self, spot, outcome, reason):
        self.outcomes[spot] = (outcome, reason)
        sign = {GREEN: "⭐ 0", RED: "⛔ 1", BLIND: "⚠ 3"}[outcome]
        print("   %s  %-3s %-48s %s" % (spot, sign, POINT_NAMES[spot], reason),
              flush=True)

    def blind_from(self, da, why):
        for p in da:
            if p not in self.outcomes:
                self.put(p, BLIND, "I could not look: " + why)

    def state(self):
        try:
            return self.g.js(JS_STATE)
        except Exception as e:                   # noqa: BLE001
            return {"⛔": str(e)[:200]}

    def do_open(self):
        is_open, reason = self.g.navigate(self.url)
        if not is_open:
            return False, "the page does not open: %s" % reason
        fine = time.time() + min(self.o.cap_s, 30)
        m = None
        while time.time() < fine:
            try:
                m = self.g.js(JS_MODULE)
            except Exception as e:               # noqa: BLE001
                m = {"error": str(e)[:200]}
            if m and m.get("form") and m.get("ready") == "complete":
                break
            time.sleep(0.5)
        if not m or not m.get("form"):
            text = (m or {}).get("text", "") if isinstance(m, dict) else ""
            return False, ("the login form is not there (url %s): «%s»"
                           % ((m or {}).get("url"), " ".join(text.split())[:160]))
        if not (m["user"] and m["password"] and m["signin_button"]):
            return False, "the form is there but a field is missing: %s" % m
        if not m["remotix"]:
            return False, "the form is there but `window.REMOTIX` is not: the script stopped"
        if m.get("banned") == "yes":
            self.note.append("address BANNED: «%s»" % m.get("warning", "")[:160])
        if not m["visible"]:
            return False, "the form is there but cannot be seen (banned=%s)" % m.get("banned")
        return True, "%s · form visible%s" % (m["url"], " ⚠ BANNED"
                                              if m.get("banned") == "yes" else "")

    def enter(self, password):
        """Returns (outcome, reason, state)."""
        r = self.g.js(JS_ENTER, self.o.user, password)
        if r != "sent":
            return RED, "I could not fill in the form: %s" % r, None
        fine = time.time() + self.o.cap_s
        s = {}
        while time.time() < fine:
            s = self.state()
            if s.get("session") and s.get("outcome_class") == "good" \
                    and (s.get("outcome") or "").startswith("Admitted"):
                return GREEN, "«%s»" % s["outcome"], s
            if s.get("outcome_class") == "bad" and s.get("outcome"):
                self.refusal = self._refusal(s)
                return RED, "the page says: «%s»" % s["outcome"], s
            time.sleep(0.4)
        queue = [x for x in (s.get("log") or "").splitlines() if x.strip()][-3:]
        self.refusal = self._refusal(s)
        return RED, ("no admission in %d s (outcome «%s», session=%s); last "
                       "lines of the page: %s" % (self.o.cap_s, s.get("outcome"),
                                                  s.get("session"), " | ".join(queue)[:300])), s

    @staticmethod
    def _refusal(s):
        """⛔ A real REFUSAL: the page sent the credentials (line
        "CREDENTIALS sent", page.html ~4955) and "ADMITTED" did not arrive
        (line ~4980).  A missed connection is not a refusal."""
        reg = (s or {}).get("log") or ""
        return ("CREDENTIALS sent" in reg
                and not any(r.strip() == "ADMITTED" for r in reg.splitlines()))

    def first_frame(self):
        """Returns (outcome, reason, state).  The page's counter + photograph."""
        fine = time.time() + self.o.cap_s
        t0 = time.time()
        s = {}
        while time.time() < fine:
            s = self.state()
            if (s.get("painted") or 0) > 0:
                break
            time.sleep(0.3)
        if not (s.get("painted") or 0) > 0:
            return RED, ("no frame painted in %d s (painted=%s, delivered=%s, "
                           "viewer=%s)" % (self.o.cap_s, s.get("painted"),
                                            s.get("delivered"), s.get("on"))), s
        after = time.time() - t0
        # ⛔ "WITHIN THE CEILING", as this file's header says — and not one
        #    single photograph at +1 s.  `[M]` 18 Sep 2026 on KDE: the first
        #    frame of a freshly born session is Plasma's splash screen
        #    ("Plasma made by KDE", 99 % black + logo), that is the real desktop
        #    turning on, and the desktop arrives afterwards.  ⇒ Photographs are taken up
        #    to the ceiling; the green says WHEN the first non-degenerate one arrived, and
        #    how many degenerate photographs preceded it.  ⛔ A canvas that stays
        #    black up to the ceiling is still RED (the certification proves it).
        degenerate_count = 0
        first_desc = ""
        while True:
            time.sleep(1.0)        # the glass: the photograph after at least one frame
            try:
                png, why = self.g.snapshot_canvas()
            except Exception as e:               # noqa: BLE001
                png, why = None, "photograph failed: %s" % str(e)[:200]
            if not png:
                return BLIND, ("painted=%d in %.1f s, but I could not look at the "
                               "pixels: %s" % (s["painted"], after, why)), s
            if self.o.save:
                with open(os.path.join(self.o.save, "%s-%d.png"
                                       % (self.g.name, int(time.time() * 1000))), "wb") as f:
                    f.write(png)
            degenerate, desc = judge_pixel(png)
            if degenerate is None:
                return BLIND, "painted=%d, pixels not judgeable: %s" % (s["painted"], desc), s
            if not degenerate:
                break
            degenerate_count += 1
            first_desc = first_desc or desc
            if time.time() >= fine:
                return RED, ("painted=%d but the canvas is DEGENERATE up to the ceiling of %d s "
                               "(%d photographs): %s" % (s["painted"], self.o.cap_s,
                                                         degenerate_count, desc)), s
        s = self.state()
        observed = time.time() - t0
        if degenerate_count:
            return GREEN, ("painted=%d · first frame at %.1f s, desktop NOT degenerate at "
                           "%.1f s after %d degenerate photographs (the first: %s) · %s"
                           % (s.get("painted") or 0, after, observed, degenerate_count, first_desc,
                              desc)), s
        return GREEN, "painted=%d after %.1f s · %s" % (s["painted"], after, desc), s

    def center(self, s, fx=0.5, fy=0.5):
        t = s.get("canvas") or [0, 0, 0, 0]
        vl, va = s.get("view", [1400, 1000, 1])[:2]
        x0, y0 = max(0, t[0]), max(0, t[1])
        x1, y1 = min(vl, t[0] + t[2]), min(va, t[1] + t[3])
        return x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy

    def continuity(self):
        s0 = self.state()
        d0 = s0.get("painted") or 0
        scene = self.o.scene
        steps = 0
        fine = time.time() + self.o.continuity_s
        if scene == "move":
            # ⭐ crosses the whole canvas in a zigzag, edges included (bar and
            #   dock are at the edges: they are the things that react to the passage)
            fr = [(0.02 + 0.96 * (i % 25) / 24.0, 0.01 + 0.98 * (i // 25) / 7.0)
                  for i in range(200)]
            i = 0
            while time.time() < fine:
                fx, fy = fr[i % len(fr)]
                if (i // 25) % 2:
                    fx = 1.0 - fx
                x, y = self.center(s0, fx, fy)
                try:
                    self.g.move_to(x, y)
                    steps += 1
                except Exception as e:           # noqa: BLE001
                    self.note.append("move failed: %s" % str(e)[:120])
                    break
                i += 1
                time.sleep(0.12 if not self.g.touch else 0.3)
            time.sleep(1.0)
        else:
            time.sleep(self.o.continuity_s)
        s1 = self.state()
        d1 = s1.get("painted") or 0
        newcomers = d1 - d0
        base = "%d new frames in %.0f s (scene «%s»%s)" % (
            newcomers, self.o.continuity_s, scene,
            ", %d moves" % steps if scene == "move" else "")
        if newcomers > 0:
            return GREEN, base
        if not s1.get("session"):
            return RED, base + " · ⛔ and the session is gone: «%s»" % s1.get("outcome")
        if scene == "still":
            return BLIND, base + " · on a still scene zero is possible: declare " \
                                 "`--scene live` or `move_to` for a judgement"
        if scene == "move":
            return RED, base + " · ⚠ the cursor is drawn by the page: if the desktop " \
                                 "does not react to the passage, redo it with a live scene"
        return RED, base

    def ingress(self, before_log):
        """Key + move/click (tap on Android).  Returns (outcome, reason)."""
        a = self.g.js(_inject(JS_LINK))
        chk = self.g.js("const c=window.REMOTIX_INPUT; return c ? !!c.__banco : null;")
        if chk is None:
            return RED, "the page has no input seam (`REMOTIX_INPUT` is null)"
        if not chk:
            return BLIND, "I could not wrap `REMOTIX_INPUT.send` (%s)" % a
        s = self.state()
        x, y = self.center(s, self.o.click[0], self.o.click[1])
        done_ones = []
        try:
            # the click first: it gives focus to the canvas, and the keyboard goes where the focus is
            if self.g.touch:
                self.g.touches(x, y); done_ones.append("tap")
                time.sleep(0.4)
                self.g.drag([(x, y), (x + 30, y + 15), (x + 60, y + 30)])
                done_ones.append("drag")
            else:
                self.g.move_to(x - 40, y - 20); self.g.move_to(x, y)
                done_ones.append("move")
                if not self.o.no_click:
                    self.g.click(x, y); done_ones.append("click")
            time.sleep(0.4)
            self.g.key(self.o.key); done_ones.append("key %s" % self.o.key)
            time.sleep(0.4)
            # ⭐ one last move: if the desktop changes, a frame brings back
            #   an id ≥ all of those above
            self.g.move_to(x + 5, y + 5)
        except Exception as e:                   # noqa: BLE001
            return BLIND, "the injection did not start (%s): %s" % (", ".join(done_ones),
                                                                     str(e)[:200])
        time.sleep(3.0)
        t = self.g.js(JS_RETURNED) or {}
        tipi = {INPUT_TYPES.get(int(k), k): v for k, v in (t.get("tipi") or {}).items()}
        ids = {int(k): v for k, v in (t.get("ids") or {}).items()}
        key_ids = ids.get(0x0105, []) + ids.get(0x0104, [])
        mouse_ids = ids.get(0x0101, []) + ids.get(0x0102, [])
        shipped = "the page sent %s" % (tipi or "NOTHING")
        if not key_ids and not mouse_ids:
            return RED, "%s after %s: the input does not leave the page" % (shipped, done_ones)
        missing = []
        if not key_ids:
            missing.append("the key")
        if not mouse_ids:
            missing.append("the mouse/touch")
        # 1) the server log, if there is one
        after, why = read_log(self.o.log_cmd) if before_log is not None \
            else (None, "no --log-cmd")
        if after is not None:
            new_ones = [r for r in new_lines(before_log, after) if "input id=" in r]
            srv_t = [r for r in new_ones if "KEY_POSITION" in r or "LETTER" in r]
            srv_m = [r for r in new_ones if "POINTER" in r or "BUTTON" in r]
            base = ("%s · in the server log %d new input lines (key %d, "
                    "mouse %d)" % (shipped, len(new_ones), len(srv_t), len(srv_m)))
            if new_ones:
                self.note.append("server: " + new_ones[-1][:200])
            if missing:
                return RED, base + " · ⛔ the page did NOT send " + " and ".join(missing)
            if srv_t and srv_m:
                return GREEN, base
            return RED, base + " · ⛔ the server did not receive " + " and ".join(
                (["the key"] if not srv_t else []) + (["the mouse"] if not srv_m else []))
        # 2) without log: the return of the ids in the frames
        mx = t.get("max_tornato") or 0
        base = "%s · highest id returned in a frame: %s (%s)" % (
            shipped, mx or "none", why)
        if missing:
            return RED, base + " · ⛔ the page did NOT send " + " and ".join(missing)
        if mx >= max(key_ids) and mx >= min(mouse_ids):
            return GREEN, base + " ⇒ the server applied all of them up to %d" % mx
        return BLIND, base + " · no return covering both: without the server " \
                             "log I cannot tell whether they arrived"

    def errors(self, s):
        inside_js = (s.get("bench") or {}).get("errors") or []
        inside_network = (s.get("bench") or {}).get("network") or []
        out_js, out_of_network, why = self.g.errors_out()
        decl = [r for r in (s.get("log") or "").splitlines() if "⛔" in r]
        all_js = list(dict.fromkeys(out_js + inside_js))
        all_network = list(dict.fromkeys(out_of_network + inside_network))
        for r in all_js[:12]:
            print("         js    %s" % r[:220])
        for r in all_network[:12]:
            print("         net   %s" % r[:220])
        for r in decl[:12]:
            print("         ⛔pag %s" % r[:220])
        if s.get("screen_errors"):
            print("         schermo.errori %s" % s["screen_errors"])
        base = "%d JS errors · %d network · %d «⛔» lines declared by the page" % (
            len(all_js), len(all_network), len(decl))
        if s.get("bench") is None and why:
            return BLIND, base + " · ⚠ neither collector in the page nor output: " + why
        if all_js or all_network:
            return RED, base
        return GREEN, base + (" (the page's «⛔» are listed, not judged)"
                              if decl else "")

    def run_loop(self, solo_ab=False):
        before_log, why_log = (read_log(self.o.log_cmd)
                                 if self.o.log_cmd else (None, "no --log-cmd"))
        if self.o.log_cmd and before_log is None:
            self.note.append("server log: " + why_log)
        self.g.reset_events()
        ok, reason = self.do_open()
        self.put("a", GREEN if ok else RED, reason)
        if not ok:
            self.blind_from("bcdefg", "(a) is not green")
            return
        e, reason, s = self.enter(self.password)
        self.put("b", e, reason)
        if e != GREEN:
            if s:
                self.put("f", *self.errors(s))
            self.blind_from("cdeg", "(b) is not green")
            return
        if solo_ab:
            return
        e, reason, s = self.first_frame()
        self.put("c", e, reason)
        if s.get("painted"):
            self.put("d", *self.continuity())
        else:
            self.blind_from("d", "no first frame")
        if s.get("session"):
            before_in = None
            if self.o.log_cmd:
                before_in, _ = read_log(self.o.log_cmd)
            self.put("e", *self.ingress(before_in))
        else:
            self.blind_from("e", "the session is not there")
        s = self.state()
        self.put("f", *self.errors(s))
        # (g) the reconnection
        try:
            self.g.reload()
            ok, reason = self.open_after_reload()
            if not ok:
                self.put("g", RED, "after the reload: " + reason)
                return
            e, reason, s = self.enter(self.password)
            if e != GREEN:
                self.put("g", e, "after the reload it does not get back in: " + reason)
                return
            e, reason, s = self.first_frame()
            self.put("g", e, "back in (%s) · %s" % (
                (s.get("outcome") or "")[:60], reason))
        except Exception as ex:                  # noqa: BLE001
            self.put("g", BLIND, "the bench could not reload: %s" % str(ex)[:200])

    def open_after_reload(self):
        fine = time.time() + min(self.o.cap_s, 30)
        while time.time() < fine:
            try:
                m = self.g.js(JS_MODULE)
                if m and m.get("form") and m.get("ready") == "complete" and m.get("visible"):
                    return True, ""
            except Exception:                    # noqa: BLE001
                pass
            time.sleep(0.5)
        return False, "the form does not reappear in %d s" % min(self.o.cap_s, 30)

    def verdict(self):
        v = [e for e, _ in self.outcomes.values()]
        if RED in v:
            return "FAIL"
        if BLIND in v:
            return "BLOCKED"
        return "PASS"


# ═══════════════════════════════════════════════════════════════════════════
def turn_on_driver(name, o):
    if name == "firefox":
        return FirefoxDriver(o.base_port, o.visible)
    if name == "chrome":
        return ChromeDriver(o.base_port + 1, o.visible)
    if name == "android":
        return AndroidDriver(o.base_port + 2, o.leave_running)
    raise ValueError(name)


def un_browser(name, o, url, password, solo_ab=False, label=""):
    print("\n══ %s%s ══════════════════════════════" % (name.upper(), label), flush=True)
    g = None
    line = {"browser": name, "url": url, "label": label.strip(" ·") or "prova"}
    try:
        try:
            g = turn_on_driver(name, o)
        except Exception as e:                   # noqa: BLE001
            print("   ⛔ the browser did not start: %s" % str(e)[:300])
            line.update(verdict="BLOCKED", stage=None,
                        outcomes={p: [BLIND, "browser not started: %s" % str(e)[:200]]
                               for p in "abcdefg"})
            print("RIGA " + json.dumps(line, ensure_ascii=False))
            return line
        stage = g.stage()
        print("   stage: %s" % stage, flush=True)
        pr = Test(g, o, url, password)
        try:
            pr.run_loop(solo_ab=solo_ab)
        except Exception as e:                   # noqa: BLE001
            print("   ⛔ the bench fell over: %s" % repr(e)[:300])
            pr.blind_from("abcdefg", "the bench fell over: %s" % str(e)[:160])
        if solo_ab:
            for p in "cdefg":
                pr.outcomes.setdefault(p, (BLIND, "not looked at: certification test"))
        for n in pr.note:
            print("   note: %s" % n)
        v = pr.verdict()
        print("   ▶ %s: %s" % (name, v))
        line.update(verdict=v, stage=stage, headless=(not o.visible) if name != "android"
                    else "emulatore-software",
                    scene=o.scene, cap_s=o.cap_s,
                    outcomes={p: [e, m] for p, (e, m) in sorted(pr.outcomes.items())},
                    refusal=pr.refusal, note=pr.note)
        print("RIGA " + json.dumps(line, ensure_ascii=False), flush=True)
        return line
    finally:
        if g is not None:
            try:
                g.close()
            except Exception as e:               # noqa: BLE001
                print("   ⚠ closing the browser: %s" % e)


def unused_port():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def url_android(url):
    """⚠ From the emulator "localhost" is the emulator itself: the laptop is
    10.0.2.2.  The LAN (192.168.0.2) is reached directly."""
    u = urllib.parse.urlsplit(url)
    if u.hostname in ("localhost", "127.0.0.1"):
        return urllib.parse.urlunsplit(u._replace(
            netloc="10.0.2.2" + (":%d" % u.port if u.port else "")))
    return url


def certify(o, browser):
    print("\n══════════ CERTIFICATION OF THE BENCH ══════════")
    e, t = certify_judge()
    print("   pixel judge: %s — %s" % ({GREEN: "⭐ can say degenerate",
                                         RED: "⛔ BLIND", BLIND: "⚠ 3"}[e], t))
    tab = [("giudice-pixel", e, t)]
    for name in browser:
        blank = "https://127.0.0.1:%d/" % unused_port()
        u = url_android(blank) if name == "android" else blank
        r = un_browser(name, o, u, o.password, solo_ab=True, label=" · certify: empty port")
        ea = r["outcomes"]["a"][0]
        tab.append(("%s empty port" % name, GREEN if ea == RED else RED,
                    "(a)=%s — expected 1" % ea))
        u = url_android(o.url) if name == "android" else o.url
        r = un_browser(name, o, u, o.password + "-SBAGLIATA-" + str(os.getpid()),
                       solo_ab=True, label=" · certify: wrong password")
        ea, eb = r["outcomes"]["a"][0], r["outcomes"]["b"]
        # ⛔ the red must be a REFUSAL: the page sent the
        #   credentials (line "CREDENTIALS sent", page.html ~4955) and
        #   was not admitted.  A missed connection certifies nothing.
        if ea != GREEN:
            tab.append(("%s wrong password" % name, BLIND,
                        "(a)=%s: without the page (b) cannot be certified" % ea))
        elif eb[0] == RED and r.get("refusal"):
            tab.append(("%s wrong password" % name, GREEN, "(b)=1 by refusal: %s" % eb[1][:120]))
        elif eb[0] == RED:
            tab.append(("%s wrong password" % name, BLIND,
                        "(b)=1 but NOT by refusal (the server did not answer the "
                        "credentials): %s" % eb[1][:160]))
        else:
            tab.append(("%s wrong password" % name, RED,
                        "⛔ (b)=%s with the wrong password: bench BLIND" % eb[0]))
    print("\n══════════ OUTCOME OF THE CERTIFICATION ══════════")
    for n, e, t in tab:
        print("   %-28s %s  %s" % (n, {GREEN: "⭐ certified", RED: "⛔ NOT certified",
                                      BLIND: "⚠ 3 not certifiable here"}[e], t))
    print("RIGA " + json.dumps({"certification": [[n, e, t] for n, e, t in tab]},
                               ensure_ascii=False))
    return 1 if any(e == RED for _, e, _ in tab) else (3 if any(e == BLIND for _, e, _ in tab) else 0)


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--url", default="https://192.168.0.2:8511/")
    a.add_argument("--user", default="prova")
    a.add_argument("--password", default=os.environ.get("REMOTIX_PASSWORD", ""),
                   help="or in the REMOTIX_PASSWORD variable")
    a.add_argument("--browser", default="firefox,chrome,android")
    a.add_argument("--visible", action="store_true",
                   help="real window instead of headless (Firefox and Chrome)")
    a.add_argument("--cap-s", type=int, default=30,
                   help="ceiling for admission and for the first frame")
    a.add_argument("--scene", choices=("move", "live", "still"), default="move")
    a.add_argument("--continuity-s", type=int, default=8)
    a.add_argument("--key", choices=sorted(KEY_LIST), default="Control",
                   help="the key to press: Control alone does nothing on the desktop")
    a.add_argument("--click", default="0.5,0.5",
                   help="where to click/tap, in fractions of the canvas")
    a.add_argument("--no-click", action="store_true",
                   help="movement only, no click (desktop with delicate things)")
    a.add_argument("--log-cmd", default="",
                   help="shell command that prints the server log")
    a.add_argument("--window", default="1400x1000",
                   help="size of the browsers' window, WxH")
    a.add_argument("--save", default="", help="folder where to leave the photographs")
    a.add_argument("--base-port", type=int, default=2851)
    a.add_argument("--leave-running", action="store_true",
                   help="do not stop the emulator if the bench started it")
    a.add_argument("--certify", action="store_true")
    o = a.parse_args()
    WINDOW[:] = [int(x) for x in o.window.lower().split("x")]
    o.click = [float(x) for x in o.click.split(",")]
    if o.save:
        os.makedirs(o.save, exist_ok=True)
    browser = [b.strip() for b in o.browser.split(",") if b.strip()]
    for b in browser:
        if b not in ("firefox", "chrome", "android"):
            a.error("unknown browser: %s" % b)
    if not o.password:
        a.error("--password is needed (or REMOTIX_PASSWORD)")
    print("⭐ 12-real-clients · %s · user %s · browser %s · ceiling %d s · scene «%s» · %s"
          % (o.url, o.user, ",".join(browser), o.cap_s, o.scene,
             "real windows" if o.visible else "HEADLESS (no GPU)"))
    if o.certify:
        return certify(o, browser)
    lines = []
    for b in browser:
        u = url_android(o.url) if b == "android" else o.url
        lines.append(un_browser(b, o, u, o.password))
    print("\n══════════ VERDICTS ══════════")
    for r in lines:
        print("   %-8s %s" % (r["browser"], r["verdict"]))
    v = [r["verdict"] for r in lines]
    return 1 if "FAIL" in v else (3 if "BLOCKED" in v else 0)


if __name__ == "__main__":
    sys.exit(main())
