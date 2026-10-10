#!/usr/bin/env python3
"""12-client-veri — THE REAL CLIENT TEST, on three browsers, with a verdict for each.

    python3 banchi/12-client-veri.py --url https://192.168.0.2:8511/ \\
        --utente prova --parola '…' [--browser firefox,chrome,android] \\
        [--visibile] [--tetto-s 30] [--scena muovi|viva|ferma] \\
        [--registro-cmd "ssh … tail -n 3000 …/registro.log"] [--certifica]

⭐ WHAT IT DOES.  It opens REMOTIX in a REAL browser — Firefox 140 ESR driven with
   Marionette (`07-b46-marionette.py`), Google Chrome driven with the DevTools
   protocol, and Chrome for Android in the `remotix` emulator, driven with the
   same protocol through `adb forward` — and for each it looks at seven things:

     a  the page opens (certificate accepted) and the login form is there
     b  with `--utente`/`--parola` the page is ADMITTED
     c  FIRST FRAME: the canvas has NON-degenerate pixels within `--tetto-s`
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
   (`src/pagina.html`, line numbers as of 18 Sep 2026):
     · admitted: `REMOTIX.schermo.sessione === true` (set by `negozia()`,
       line ~2816, and the worker branch line ~8234) AND `#esito` with class
       `bene` and text "Admitted, … session …" (line ~5058).  Refusal is `#esito`
       with class `male` (line 622 and the branches of `collega()`).
     · first frame and continuity: `REMOTIX.schermo.conti.dipinti` (line
       ~2689, grows at lines ~3186/3675/4099) — the phase's gauge, which the
       page itself reads in the first-frame watch.
     · the pixels: a PHOTOGRAPH of the canvas taken by the browser (CDP
       `Page.captureScreenshot`, Marionette `TakeScreenshot` with `id`).  ⚠ Not
       `getImageData`: the canvas may be `bitmaprenderer` or handed to a
       worker (`transferControlToOffscreen`, line ~8145), and there reading from
       the document sees nothing.  The photograph sees what the user sees.
     · input: the bench WRAPS `window.REMOTIX_INPUT.manda` (line ~5130) and
       counts by type what the page really sent (the `id` is in the
       first 4 bytes of the body, §7.3).  ⭐ And arrival at the server is proven in two
       independent ways: the lines "input id=… PUNTATORE/PULSANTE/
       POSIZIONE_TASTO" in the server log (`src/rcp.c` ~4726), if there is
       `--registro-cmd`; and from the page, with `REMOTIX.giro` (line ~2197): a
       frame that brings back `id` N proves the server has
       applied all inputs up to N (the input stream is one and
       ordered, §2.5).  ⚠ A frame arrives only if the screen CHANGES:
       without log and without return, the outcome is 3, not 1.
     · the page log: the text of `#registro` (`nota()` lines, line
       473) — the "⛔" lines are taken from there.

⚠ THE SCENE IS DECLARED (`--scena`).  A still desktop sends NO frames, and
  zero frames on a still desktop is the right thing:
     · `ferma`  no new frame ⇒ 3 (it cannot be told apart)
     · `viva`   whoever launches GUARANTEES that something moves ⇒ zero frames is 1
     · `muovi`  (default) the bench moves the pointer over the canvas for
                `--continuita-s` seconds, crossing the whole desktop ⇒ zero
                frames is 1.  ⚠ The cursor is drawn by the page, not by the
                server: the frame is born only if the desktop reacts to the
                passage (highlights, bar, dock).  On a desktop that does not
                react, use `viva` with a scene running.

⚠ HEADLESS IS DECLARED.  Without `--visibile` Firefox and Chrome run headless,
  that is without GPU: decoding and drawing are in SOFTWARE.  The Android
  emulator uses `swiftshader_indirect`, that is software too.  The outcome
  line carries it written: this bench judges BEHAVIOUR, not numbers.

⛔ THE CERTIFICATION (`PIANO.md` §0.3 rule 4) — `--certifica` proves that the
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
  (local, via `adb forward`).  They are changed with `--porte-base`.
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

QUI = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.expanduser("~")
ADB = os.path.join(CASA, "Android/Sdk/platform-tools/adb")
EMU = os.path.join(CASA, "Android/Sdk/emulator/emulator")
# ⛔ 19 Sep 2026 — NOT the system image's Chrome (113): WebCodecs on
#    Chrome for Android exists from 147 (`DECISIONI.md` line ~425), and `[M]` the
#    113 already falls at WebTransport (`ERR_METHOD_NOT_SUPPORTED`).  ⇒ Chromium for
#    Android from the official Chromium build archive (AndroidDesktop_x64,
#    `ChromePublic.apk`, 156.0.8067.0, in `~/Android/chromium/`), declared
#    as Chromium.  ⛔ Firefox for Android is NOT supported (§7.18).
#    ⚠ And Chromium does NOT work: `[M]` the public builds have no H.264
#    (`isConfigSupported` says no to `avc1.*`) ⇒ the page has no codec at all.
#    ⇒ The REAL Chrome of the Android 17 image is used (`remotix37`, Chrome
#    145.0.7632.218).  Both can be changed without touching the file:
#    `REMOTIX_ANDROID_PACCHETTO`, `REMOTIX_AVD`.
CHROME_ANDROID = os.environ.get("REMOTIX_ANDROID_PACCHETTO", "com.android.chrome")
AVD = os.environ.get("REMOTIX_AVD", "remotix37")


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, os.path.join(QUI, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MARIONETTE = _carica("marionette", "07-b46-marionette.py")
CDPMOD = _carica("cdp", "02-pagina-misura-cdp.py")

VERDE, ROSSO, CIECO = 0, 1, 3
NOMI_PUNTI = {
    "a": "the page opens and the form is there",
    "b": "admitted with user and password",
    "c": "first frame, non-degenerate pixels",
    "d": "continuity of the frames",
    "e": "input: key and mouse/touch reach the server",
    "f": "JavaScript and network errors",
    "g": "reconnection: reload, log in again, first frame",
}
TIPI_INPUT = {0x0101: "PUNTATORE", 0x0102: "PULSANTE", 0x0103: "ROTELLA",
              0x0104: "LETTERA", 0x0105: "POSIZIONE_TASTO"}


# ═══════════════════════════════════════════════════════════════════════════
#  THE PIXEL JUDGE
# ═══════════════════════════════════════════════════════════════════════════
def giudica_pixel(png):
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
    conta = {}
    for p in px:
        q = (p[0] >> 3, p[1] >> 3, p[2] >> 3)
        conta[q] = conta.get(q, 0) + 1
    dom_q, dom_n = max(conta.items(), key=lambda kv: kv[1])
    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px]
    media = sum(lum) / n
    dev = (sum((x - media) ** 2 for x in lum) / n) ** 0.5
    quota = dom_n / n
    desc = ("%dx%d · distinct colours %d · dominant %.1f%% (%d,%d,%d) · "
            "mean luminance %.0f dev %.1f"
            % (l, a, len(conta), 100 * quota, dom_q[0] << 3, dom_q[1] << 3,
               dom_q[2] << 3, media, dev))
    return (quota >= 0.97 or dev < 3.0), desc


def certifica_giudice():
    """The pixel judge must be able to say "degenerate"."""
    try:
        from PIL import Image
    except ImportError:
        return CIECO, "PIL is not there"
    def png(im):
        b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()
    nero = Image.new("RGB", (640, 400), (0, 0, 0))
    sfum = Image.new("RGB", (640, 400))
    sfum.putdata([(x % 256, (y * 2) % 256, (x + y) % 256)
                  for y in range(400) for x in range(640)])
    d1, t1 = giudica_pixel(png(nero))
    d2, t2 = giudica_pixel(png(sfum))
    ok = d1 is True and d2 is False
    return (VERDE if ok else ROSSO,
            "black canvas ⇒ %s (%s) · gradient ⇒ %s (%s)"
            % ("degenerate" if d1 else "⛔ NOT degenerate", t1,
               "not degenerate" if d2 is False else "⛔ degenerate", t2))


# ═══════════════════════════════════════════════════════════════════════════
#  THE JAVASCRIPT PIECES — function bodies, with `return`
# ═══════════════════════════════════════════════════════════════════════════
JS_MODULO = r"""
const m = document.getElementById('modulo');
const vis = (e) => !!e && getComputedStyle(e).display !== 'none'
                   && getComputedStyle(e).visibility !== 'hidden'
                   && e.getBoundingClientRect().width > 0;
return { url: location.href, titolo: document.title,
         pronta: document.readyState,
         modulo: !!m, visibile: vis(m),
         utente: !!document.getElementById('utente'),
         parola: !!document.getElementById('parola'),
         vai: !!document.getElementById('vai'),
         remotix: !!window.REMOTIX,
         bannato: document.body ? document.body.dataset.bannato || null : null,
         avviso: (document.getElementById('avviso') || {}).textContent || '',
         testo: document.body ? document.body.innerText.slice(0, 300) : '' };
"""

# ⚠ The value is put in the field and `requestSubmit()` is asked of the form: it is
#   the same `submit` handler that starts the page when the user
#   presses "Connect" (pagina.html ~8445).  Nothing is typed at coordinates.
JS_ENTRA = r"""
const u = document.getElementById('utente'), p = document.getElementById('parola');
const m = document.getElementById('modulo');
if (!u || !p || !m) return 'the form is missing';
u.value = arguments[0]; p.value = arguments[1];
u.dispatchEvent(new Event('input', {bubbles: true}));
p.dispatchEvent(new Event('input', {bubbles: true}));
if (m.requestSubmit) m.requestSubmit(document.getElementById('vai'));
else document.getElementById('vai').click();
return 'sent';
"""

JS_STATO = r"""
const R = window.REMOTIX, s = R && R.schermo;
const e = document.getElementById('esito');
const reg = document.getElementById('registro');
let g = null;
try { if (R && R.giro) g = { visti: R.giro.visti, attesa: R.giro.quando.size }; } catch (x) {}
const t = document.getElementById('schermo');
const r = t ? t.getBoundingClientRect() : null;
return {
  sessione: !!(s && s.sessione),
  esito_classe: e ? e.className : null,
  esito: e ? e.textContent : null,
  dipinti: s && s.conti ? s.conti.dipinti : null,
  consegnati: s && s.conti ? s.conti.consegnati : null,
  acceso: document.body ? (document.body.dataset.schermo || null) : null,
  input: !!window.REMOTIX_INPUT,
  giro: g,
  tela: r ? [r.left, r.top, r.width, r.height] : null,
  buffer: t ? [t.width, t.height] : null,
  vista: [innerWidth, innerHeight, devicePixelRatio || 1],
  registro: reg ? reg.textContent : '',
  errori_schermo: s && s.errori ? s.errori.slice(-5).map(String) : [],
  banco: window.__BANCO__ ? { errori: window.__BANCO__.errori.slice(0, 40),
                              rete: window.__BANCO__.rete.slice(0, 40) } : null,
  ingresso: window.__BANCO_IN__ ? window.__BANCO_IN__ : null,
};
"""

# ⭐ The error collector.  In Chrome it goes in BEFORE the page
#   (`Page.addScriptToEvaluateOnNewDocument`); in Firefox it goes in after the load
#   and that is declared — the earlier errors are caught by the browser's output
#   (`devtools.console.stdout.content`).
RACCOGLITORE = r"""
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

# ⭐ The input link.  It wraps the seam's `manda` (line ~5130): it counts
#   by type what the page SENT, with the `id` taken from the first 4 bytes
#   of the body (§7.3, big-endian).  ⚠ It changes nothing of what the page
#   sends: it calls the real `manda` with the same arguments.
JS_ANELLO = r"""
(function () {
  const c = window.REMOTIX_INPUT;
  if (!c || typeof c.manda !== 'function' || c.__banco) return;
  const vero = c.manda;
  const B = window.__BANCO_IN__ = window.__BANCO_IN__ || { tipi: {}, ids: {} };
  c.manda = function (tipo, corpo) {
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
#   `GIRO.quando` no longer has (`torna()` deletes them, line ~2211).
JS_TORNATI = r"""
const B = window.__BANCO_IN__, R = window.REMOTIX;
if (!B || !R || !R.giro) return null;
let max_tornato = 0;
const per_tipo = {};
for (const t in B.ids) {
  per_tipo[t] = B.ids[t].slice();
  for (const id of B.ids[t]) if (!R.giro.quando.has(id) && id > max_tornato) max_tornato = id;
}
return { max_tornato: max_tornato, ids: per_tipo, tipi: B.tipi, visti: R.giro.visti };
"""


def _inietta(corpo):
    """A body to run in the REAL page, not in the driver's sandbox:
    in Firefox a function born in Marionette's sandbox and called by the
    page goes through the "xrays" and may not work.  ⇒ `<script>` in the DOM."""
    return ("const s = document.createElement('script');"
            "s.textContent = %s;"
            "(document.head || document.documentElement).appendChild(s); s.remove();"
            "return true;" % json.dumps(corpo))


# ═══════════════════════════════════════════════════════════════════════════
#  THE DRIVERS — one per browser, the same face
# ═══════════════════════════════════════════════════════════════════════════
class Cdp(CDPMOD.Cdp):
    """The CDP client of `02-pagina-misura-cdp.py`, which however KEEPS the events:
    exceptions and console messages arrive as events while
    waiting for the answer to a command, and it used to throw them away."""

    def __init__(self, url, timeout=60):
        super().__init__(url, timeout)
        self.eventi = []

    def chiama(self, metodo, **parametri):
        self.n += 1
        mio = self.n
        self.ws.manda(json.dumps({"id": mio, "method": metodo, "params": parametri}))
        while True:
            r = json.loads(self.ws.ricevi())
            if "method" in r and "id" not in r:
                if len(self.eventi) < 5000:
                    self.eventi.append(r)
                continue
            if r.get("id") != mio:
                continue
            if "error" in r:
                raise RuntimeError(metodo + ": " + json.dumps(r["error"]))
            return r.get("result", {})


class GuidaCdp:
    """Desktop Chrome and Chrome for Android: same protocol."""
    tocco = False

    def __init__(self, porta, nome):
        self.porta, self.nome = porta, nome
        self.cdp = None

    def aggancia(self, attesa=40):
        b = CDPMOD.pagina(self.porta, attesa)
        self.cdp = Cdp(b["webSocketDebuggerUrl"])
        for d in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
            try:
                self.cdp.chiama(d)
            except Exception:                    # noqa: BLE001
                pass
        self.cdp.chiama("Page.addScriptToEvaluateOnNewDocument", source=RACCOGLITORE)
        try:
            self.cdp.chiama("Emulation.setFocusEmulationEnabled", enabled=True)
        except Exception:                        # noqa: BLE001
            pass

    def versione(self):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % self.porta,
                                        timeout=5) as r:
                return json.loads(r.read().decode()).get("Browser", "?")
        except Exception as e:                   # noqa: BLE001
            return "? (%s)" % e

    def js(self, corpo, *arg):
        espr = "(function(){%s}).apply(null, %s)" % (corpo, json.dumps(list(arg)))
        r = self.cdp.chiama("Runtime.evaluate", expression=espr,
                            returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise RuntimeError("exception in the bench: %s"
                               % json.dumps(r["exceptionDetails"])[:300])
        return r.get("result", {}).get("value")

    def vai(self, url):
        """Returns (opened, reason).  ⭐ The certificate is accepted as the user
        accepts it: the "Advanced" panel → "Proceed".  No flag that
        turns off the checks: with `--ignore-certificate-errors` WebTransport too
        would stop looking at the fingerprint, and the bench would test
        a browser the user does not have."""
        r = self.cdp.chiama("Page.navigate", url=url)
        err = r.get("errorText")
        time.sleep(1.5)
        for _ in range(3):
            try:
                pannello = self.js(
                    "return !!document.getElementById('proceed-link')"
                    " || !!document.getElementById('details-button');")
            except Exception:                    # noqa: BLE001
                pannello = False
            if not pannello:
                break
            self.js("const d=document.getElementById('details-button'); if (d) d.click();"
                    "const p=document.getElementById('proceed-link'); if (p) p.click();"
                    "return 1;")
            time.sleep(3)
        if err and "CERT" not in err:
            return False, err
        return True, err or ""

    def ricarica(self):
        self.cdp.chiama("Page.reload", ignoreCache=False)
        time.sleep(1.5)

    def fotografa_tela(self):
        r = self.js("const t=document.getElementById('schermo');"
                    "if(!t) return null; const b=t.getBoundingClientRect();"
                    "const x=Math.max(0,b.left), y=Math.max(0,b.top);"
                    "return [x, y, Math.min(innerWidth,b.right)-x,"
                    " Math.min(innerHeight,b.bottom)-y];")
        if not r or r[2] < 4 or r[3] < 4:
            return None, "the canvas has no visible area: %s" % (r,)
        scala = min(1.0, 640.0 / r[2])
        s = self.cdp.chiama("Page.captureScreenshot", format="png",
                            clip={"x": r[0], "y": r[1], "width": r[2],
                                  "height": r[3], "scale": scala})
        return base64.b64decode(s["data"]), ""

    # -- input: protocol events, that is TRUSTED events in the renderer -------
    def muovi(self, x, y):
        self.cdp.chiama("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)

    def clic(self, x, y):
        self.muovi(x, y)
        for t in ("mousePressed", "mouseReleased"):
            self.cdp.chiama("Input.dispatchMouseEvent", type=t, x=x, y=y,
                            button="left", clickCount=1)

    def tocca(self, x, y):
        self.cdp.chiama("Input.dispatchTouchEvent", type="touchStart",
                        touchPoints=[{"x": x, "y": y}])
        time.sleep(0.08)
        self.cdp.chiama("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])

    def trascina(self, punti):
        self.cdp.chiama("Input.dispatchTouchEvent", type="touchStart",
                        touchPoints=[{"x": punti[0][0], "y": punti[0][1]}])
        for x, y in punti[1:]:
            time.sleep(0.05)
            self.cdp.chiama("Input.dispatchTouchEvent", type="touchMove",
                            touchPoints=[{"x": x, "y": y}])
        self.cdp.chiama("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])

    def tasto(self, t):
        k = TASTI[t]
        mod = 2 if t == "Control" else 0
        self.cdp.chiama("Input.dispatchKeyEvent", type="rawKeyDown", key=k["key"],
                        code=k["code"], windowsVirtualKeyCode=k["vk"], modifiers=mod)
        time.sleep(0.08)
        self.cdp.chiama("Input.dispatchKeyEvent", type="keyUp", key=k["key"],
                        code=k["code"], windowsVirtualKeyCode=k["vk"])

    def errori_fuori(self):
        """The errors seen by the PROTOCOL, independent of the page."""
        try:
            self.cdp.chiama("Runtime.evaluate", expression="1")   # drains the queue
        except Exception:                        # noqa: BLE001
            pass
        js, rete = [], []
        for e in self.cdp.eventi:
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
                    (rete if en.get("source") == "network" else js).append(
                        "%s: %s%s" % (en.get("source"), en.get("text", "")[:300],
                                      " [%s]" % en["url"] if en.get("url") else ""))
            elif m == "Network.loadingFailed":
                # ⚠ the document's certificate error is the one the bench
                #   accepts on purpose from the "Proceed" panel: it is not a defect
                if p.get("canceled") or (p.get("type") == "Document"
                                         and "ERR_CERT_" in (p.get("errorText") or "")):
                    continue
                rete.append("network: %s (%s)" % (p.get("errorText"), p.get("type")))
        return js, rete, ""

    def azzera_eventi(self):
        self.cdp.eventi = []


TASTI = {
    "Control": {"key": "Control", "code": "ControlLeft", "vk": 17, "wd": ""},
    "ArrowRight": {"key": "ArrowRight", "code": "ArrowRight", "vk": 39, "wd": ""},
}


# ⭐ The window size of the two browsers, "WxH".  ⚠ It is changed with
#   `--finestra`: `[M]` 24 Sep 2026, Firefox's green strip depends on the
#   WIDTH (8 px at 1400, 12 at 1348), and a bench with a fixed window sees only one.
FINESTRA = [1400, 1000]


class GuidaChrome(GuidaCdp):
    def __init__(self, porta, visibile):
        super().__init__(porta, "chrome")
        self.visibile = visibile
        self.profilo = tempfile.mkdtemp(prefix="remotix-cr-")
        cmd = ["google-chrome", "--remote-debugging-port=%d" % porta,
               "--user-data-dir=" + self.profilo, "--no-first-run",
               "--no-default-browser-check", "--disable-sync",
               "--password-store=basic", "--window-size=%d,%d" % tuple(FINESTRA),
               "--remote-allow-origins=*"]
        if not visibile:
            cmd.append("--headless=new")
        # ⚠ Extra options declared by whoever launches: `[M]` 24 Sep 2026, on the
        #   server inside a labwc without a screen Chrome looked for X11 and did not
        #   start ⇒ `REMOTIX_CHROME_OPZIONI="--ozone-platform=wayland"`.
        cmd += os.environ.get("REMOTIX_CHROME_OPZIONI", "").split()
        cmd.append("about:blank")
        self.log = open(os.path.join(self.profilo, "uscita.log"), "wb")
        self.p = subprocess.Popen(cmd, stdout=self.log, stderr=subprocess.STDOUT)
        self.aggancia()

    def palco(self):
        return "%s · %s" % (self.versione(), "real window" if self.visibile
                            else "HEADLESS — no GPU, all in software")

    def chiudi(self):
        try:
            self.cdp.chiama("Page.navigate", url="about:blank")   # pagehide ⇒ CONGEDO
            time.sleep(1)
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.cdp.chiama("Browser.close")
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.p.wait(10)
        except Exception:                        # noqa: BLE001
            self.p.kill()
        shutil.rmtree(self.profilo, ignore_errors=True)


def adb(*v, t=60):
    try:
        return subprocess.run([ADB] + list(v), capture_output=True, text=True,
                              timeout=t).stdout or ""
    except Exception as e:                       # noqa: BLE001
        return "⛔ %s" % e


class GuidaAndroid(GuidaCdp):
    """Chrome in the `remotix` emulator.  ⛔ The emulator eats RAM: the bench
    starts it if it is not there, and the bench stops it if it started it."""
    tocco = True

    def __init__(self, porta, lascia_acceso):
        super().__init__(porta, "android")
        self.acceso_da_me = False
        self.lascia = lascia_acceso
        if "\tdevice" not in adb("devices"):
            print("   ⏳ starting the emulator «%s»…" % AVD, flush=True)
            subprocess.Popen([EMU, "-avd", AVD, "-no-window", "-no-audio",
                              "-no-boot-anim", "-gpu", "swiftshader_indirect",
                              "-no-snapshot", "-accel", "on", "-memory", "3072"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.acceso_da_me = True
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
        adb("forward", "tcp:%d" % porta, "localabstract:chrome_devtools_remote")
        time.sleep(4)
        self.aggancia(attesa=60)

    def palco(self):
        v = adb("shell", "dumpsys", "package", CHROME_ANDROID)
        ver = v.split("versionName=")[1].split()[0] if "versionName=" in v else "?"
        return ("%s %s on Android %s (emulator «%s», swiftshader GPU: SOFTWARE)"
                % ("Chromium" if "chromium" in CHROME_ANDROID else "Chrome", ver,
                   adb("shell", "getprop", "ro.build.version.release").strip(), AVD))

    def muovi(self, x, y):
        # ⚠ On Android the "mouse" is a finger: a move is a drag
        self.trascina([(x, y), (x + 20, y + 10)])

    def clic(self, x, y):
        self.tocca(x, y)

    def chiudi(self):
        try:
            self.cdp.chiama("Page.navigate", url="about:blank")   # pagehide ⇒ CONGEDO
            time.sleep(1)
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.cdp.chiudi()
        except Exception:                        # noqa: BLE001
            pass
        adb("shell", "am", "force-stop", CHROME_ANDROID)
        adb("forward", "--remove", "tcp:%d" % self.porta)
        if self.acceso_da_me and not self.lascia:
            print("   ⏹ stopping the emulator (I had started it)", flush=True)
            adb("emu", "kill")
            t0 = time.time()
            while time.time() - t0 < 30 and "emulator-" in adb("devices"):
                time.sleep(2)


class GuidaFirefox:
    tocco = False

    def __init__(self, porta, visibile):
        self.nome = "firefox"
        self.visibile = visibile
        self.p, self.m, self.profilo = MARIONETTE.accendi(
            porta=porta, headless=not visibile, largo=FINESTRA[0], alto=FINESTRA[1])
        # ⚠ `acceptInsecureCerts` must be given ALSO outside `alwaysMatch`: `[M]` 18
        #   Sep 2026, Firefox 140 with only the form of `07-b46`
        #   (`sessione()`) refuses the self-signed certificate ("insecure
        #   certificate"); with both it accepts it.  It is the exception the
        #   user adds by hand from the panel.
        self.caps = self.m.chiama("WebDriver:NewSession", {
            "capabilities": {"alwaysMatch": {"acceptInsecureCerts": True}},
            "acceptInsecureCerts": True})
        self.log = os.path.join(self.profilo, "uscita.log")
        self.log_da = 0
        self.m.chiama("WebDriver:SetTimeouts", {"script": 60000, "pageLoad": 60000})

    def palco(self):
        c = (self.caps or {}).get("capabilities", {})
        return "Firefox %s · %s" % (c.get("browserVersion", "?"),
                                    "real window" if self.visibile
                                    else "HEADLESS — no GPU, all in software")

    def js(self, corpo, *arg):
        return self.m.js(corpo, list(arg))["value"]

    def vai(self, url):
        try:
            self.m.vai(url)
        except RuntimeError as e:
            return False, str(e)[:300]
        time.sleep(1)
        try:
            self.js(_inietta(RACCOGLITORE))
        except Exception:                        # noqa: BLE001
            pass
        return True, ""

    def ricarica(self):
        self.m.chiama("WebDriver:Refresh")
        time.sleep(1)
        try:
            self.js(_inietta(RACCOGLITORE))
        except Exception:                        # noqa: BLE001
            pass

    def fotografa_tela(self):
        el = self.m.chiama("WebDriver:FindElement",
                           {"using": "css selector", "value": "#schermo"})["value"]
        # ⚠ Marionette has no `TakeElementScreenshot` (it is the W3C name on the
        #   geckodriver side): the element is passed to `TakeScreenshot` with `id`.
        r = self.m.chiama("WebDriver:TakeScreenshot",
                          {"id": list(el.values())[0], "full": False})
        return base64.b64decode(r["value"]), ""

    def _azioni(self, azioni):
        self.m.chiama("WebDriver:PerformActions", {"actions": azioni})
        self.m.chiama("WebDriver:ReleaseActions")

    def muovi(self, x, y):
        self._azioni([{"type": "pointer", "id": "topo",
                       "parameters": {"pointerType": "mouse"},
                       "actions": [{"type": "pointerMove", "x": int(x), "y": int(y),
                                    "origin": "viewport", "duration": 0}]}])

    def clic(self, x, y):
        self._azioni([{"type": "pointer", "id": "topo",
                       "parameters": {"pointerType": "mouse"},
                       "actions": [{"type": "pointerMove", "x": int(x), "y": int(y),
                                    "origin": "viewport", "duration": 0},
                                   {"type": "pointerDown", "button": 0},
                                   {"type": "pause", "duration": 60},
                                   {"type": "pointerUp", "button": 0}]}])

    def tasto(self, t):
        w = TASTI[t]["wd"]
        self._azioni([{"type": "key", "id": "tastiera",
                       "actions": [{"type": "keyDown", "value": w},
                                   {"type": "pause", "duration": 80},
                                   {"type": "keyUp", "value": w}]}])

    def errori_fuori(self):
        """⚠ From Firefox the errors "from outside" are read in its output
        (`devtools.console.stdout.content`, turned on by `07-b46`)."""
        try:
            with open(self.log, "rb") as f:
                f.seek(self.log_da)
                testo = f.read().decode("utf-8", "replace")
        except OSError as e:
            return [], [], "Firefox output unreadable: %s" % e
        js, rete = [], []
        for r in testo.splitlines():
            if r.startswith("JavaScript error:"):
                # ⚠ only the PAGE's errors: those of Firefox's internal
                #   modules (`resource://`, `chrome://`) are not ours
                if "resource://" in r[:60] or "chrome://" in r[:60]:
                    continue
                js.append(r[:300])
            elif r.startswith("console.error:"):
                js.append(r[:300])
            elif "NS_ERROR_NET" in r or "NS_ERROR_CONNECTION" in r:
                rete.append(r[:300])
        return js, rete, ""

    def azzera_eventi(self):
        try:
            self.log_da = os.path.getsize(self.log)
        except OSError:
            self.log_da = 0

    def chiudi(self):
        try:
            self.m.vai("about:blank")                             # pagehide ⇒ CONGEDO
            time.sleep(1)
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.m.chiama("Marionette:Quit")
        except Exception:                        # noqa: BLE001
            pass
        MARIONETTE.spegni(self.p, self.profilo)


# ═══════════════════════════════════════════════════════════════════════════
#  THE SERVER LOG
# ═══════════════════════════════════════════════════════════════════════════
def leggi_registro(cmd):
    if not cmd:
        return None, "no --registro-cmd"
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


def righe_nuove(prima, dopo):
    """The lines of `dopo` that were not in `prima` — counting duplicates."""
    visto = {}
    for r in prima:
        visto[r] = visto.get(r, 0) + 1
    fuori = []
    for r in dopo:
        if visto.get(r, 0):
            visto[r] -= 1
        else:
            fuori.append(r)
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST OF ONE BROWSER
# ═══════════════════════════════════════════════════════════════════════════
class Prova:
    def __init__(self, g, o, url, parola):
        self.g, self.o, self.url, self.parola = g, o, url, parola
        self.esiti = {}                            # point -> (outcome, reason)
        self.note = []
        self.rifiuto = None

    def metti(self, punto, esito, motivo):
        self.esiti[punto] = (esito, motivo)
        segno = {VERDE: "⭐ 0", ROSSO: "⛔ 1", CIECO: "⚠ 3"}[esito]
        print("   %s  %-3s %-48s %s" % (punto, segno, NOMI_PUNTI[punto], motivo),
              flush=True)

    def cieco_da(self, da, perche):
        for p in da:
            if p not in self.esiti:
                self.metti(p, CIECO, "I could not look: " + perche)

    def stato(self):
        try:
            return self.g.js(JS_STATO)
        except Exception as e:                   # noqa: BLE001
            return {"⛔": str(e)[:200]}

    def apri(self):
        aperta, motivo = self.g.vai(self.url)
        if not aperta:
            return False, "the page does not open: %s" % motivo
        fine = time.time() + min(self.o.tetto_s, 30)
        m = None
        while time.time() < fine:
            try:
                m = self.g.js(JS_MODULO)
            except Exception as e:               # noqa: BLE001
                m = {"errore": str(e)[:200]}
            if m and m.get("modulo") and m.get("pronta") == "complete":
                break
            time.sleep(0.5)
        if not m or not m.get("modulo"):
            testo = (m or {}).get("testo", "") if isinstance(m, dict) else ""
            return False, ("the login form is not there (url %s): «%s»"
                           % ((m or {}).get("url"), " ".join(testo.split())[:160]))
        if not (m["utente"] and m["parola"] and m["vai"]):
            return False, "the form is there but a field is missing: %s" % m
        if not m["remotix"]:
            return False, "the form is there but `window.REMOTIX` is not: the script stopped"
        if m.get("bannato") == "si":
            self.note.append("address BANNED: «%s»" % m.get("avviso", "")[:160])
        if not m["visibile"]:
            return False, "the form is there but cannot be seen (bannato=%s)" % m.get("bannato")
        return True, "%s · form visible%s" % (m["url"], " ⚠ BANNED"
                                              if m.get("bannato") == "si" else "")

    def entra(self, parola):
        """Returns (outcome, reason, state)."""
        r = self.g.js(JS_ENTRA, self.o.utente, parola)
        if r != "sent":
            return ROSSO, "I could not fill in the form: %s" % r, None
        fine = time.time() + self.o.tetto_s
        s = {}
        while time.time() < fine:
            s = self.stato()
            if s.get("sessione") and s.get("esito_classe") == "bene" \
                    and (s.get("esito") or "").startswith("Admitted"):
                return VERDE, "«%s»" % s["esito"], s
            if s.get("esito_classe") == "male" and s.get("esito"):
                self.rifiuto = self._rifiuto(s)
                return ROSSO, "the page says: «%s»" % s["esito"], s
            time.sleep(0.4)
        coda = [x for x in (s.get("registro") or "").splitlines() if x.strip()][-3:]
        self.rifiuto = self._rifiuto(s)
        return ROSSO, ("no admission in %d s (outcome «%s», session=%s); last "
                       "lines of the page: %s" % (self.o.tetto_s, s.get("esito"),
                                                  s.get("sessione"), " | ".join(coda)[:300])), s

    @staticmethod
    def _rifiuto(s):
        """⛔ A real REFUSAL: the page sent the credentials (line
        "CREDENZIALI sent", pagina.html ~4955) and "AMMESSO" did not arrive
        (line ~4980).  A missed connection is not a refusal."""
        reg = (s or {}).get("registro") or ""
        return ("CREDENZIALI sent" in reg
                and not any(r.strip() == "AMMESSO" for r in reg.splitlines()))

    def primo_fotogramma(self):
        """Returns (outcome, reason, state).  The page's counter + photograph."""
        fine = time.time() + self.o.tetto_s
        t0 = time.time()
        s = {}
        while time.time() < fine:
            s = self.stato()
            if (s.get("dipinti") or 0) > 0:
                break
            time.sleep(0.3)
        if not (s.get("dipinti") or 0) > 0:
            return ROSSO, ("no frame painted in %d s (dipinti=%s, consegnati=%s, "
                           "schermo=%s)" % (self.o.tetto_s, s.get("dipinti"),
                                            s.get("consegnati"), s.get("acceso"))), s
        dopo = time.time() - t0
        # ⛔ "WITHIN THE CEILING", as this file's header says — and not one
        #    single photograph at +1 s.  `[M]` 18 Sep 2026 on KDE: the first
        #    frame of a freshly born session is Plasma's splash screen
        #    ("Plasma made by KDE", 99 % black + logo), that is the real desktop
        #    turning on, and the desktop arrives afterwards.  ⇒ Photographs are taken up
        #    to the ceiling; the green says WHEN the first non-degenerate one arrived, and
        #    how many degenerate photographs preceded it.  ⛔ A canvas that stays
        #    black up to the ceiling is still ROSSO (the certification proves it).
        degeneri = 0
        prima_desc = ""
        while True:
            time.sleep(1.0)        # the glass: the photograph after at least one frame
            try:
                png, perche = self.g.fotografa_tela()
            except Exception as e:               # noqa: BLE001
                png, perche = None, "photograph failed: %s" % str(e)[:200]
            if not png:
                return CIECO, ("dipinti=%d in %.1f s, but I could not look at the "
                               "pixels: %s" % (s["dipinti"], dopo, perche)), s
            if self.o.salva:
                with open(os.path.join(self.o.salva, "%s-%d.png"
                                       % (self.g.nome, int(time.time() * 1000))), "wb") as f:
                    f.write(png)
            degenere, desc = giudica_pixel(png)
            if degenere is None:
                return CIECO, "dipinti=%d, pixels not judgeable: %s" % (s["dipinti"], desc), s
            if not degenere:
                break
            degeneri += 1
            prima_desc = prima_desc or desc
            if time.time() >= fine:
                return ROSSO, ("dipinti=%d but the canvas is DEGENERATE up to the ceiling of %d s "
                               "(%d photographs): %s" % (s["dipinti"], self.o.tetto_s,
                                                         degeneri, desc)), s
        s = self.stato()
        visto = time.time() - t0
        if degeneri:
            return VERDE, ("dipinti=%d · first frame at %.1f s, desktop NOT degenerate at "
                           "%.1f s after %d degenerate photographs (the first: %s) · %s"
                           % (s.get("dipinti") or 0, dopo, visto, degeneri, prima_desc,
                              desc)), s
        return VERDE, "dipinti=%d after %.1f s · %s" % (s["dipinti"], dopo, desc), s

    def centro(self, s, fx=0.5, fy=0.5):
        t = s.get("tela") or [0, 0, 0, 0]
        vl, va = s.get("vista", [1400, 1000, 1])[:2]
        x0, y0 = max(0, t[0]), max(0, t[1])
        x1, y1 = min(vl, t[0] + t[2]), min(va, t[1] + t[3])
        return x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy

    def continuita(self):
        s0 = self.stato()
        d0 = s0.get("dipinti") or 0
        scena = self.o.scena
        passi = 0
        fine = time.time() + self.o.continuita_s
        if scena == "muovi":
            # ⭐ crosses the whole canvas in a zigzag, edges included (bar and
            #   dock are at the edges: they are the things that react to the passage)
            fr = [(0.02 + 0.96 * (i % 25) / 24.0, 0.01 + 0.98 * (i // 25) / 7.0)
                  for i in range(200)]
            i = 0
            while time.time() < fine:
                fx, fy = fr[i % len(fr)]
                if (i // 25) % 2:
                    fx = 1.0 - fx
                x, y = self.centro(s0, fx, fy)
                try:
                    self.g.muovi(x, y)
                    passi += 1
                except Exception as e:           # noqa: BLE001
                    self.note.append("move failed: %s" % str(e)[:120])
                    break
                i += 1
                time.sleep(0.12 if not self.g.tocco else 0.3)
            time.sleep(1.0)
        else:
            time.sleep(self.o.continuita_s)
        s1 = self.stato()
        d1 = s1.get("dipinti") or 0
        nuovi = d1 - d0
        base = "%d new frames in %.0f s (scene «%s»%s)" % (
            nuovi, self.o.continuita_s, scena,
            ", %d moves" % passi if scena == "muovi" else "")
        if nuovi > 0:
            return VERDE, base
        if not s1.get("sessione"):
            return ROSSO, base + " · ⛔ and the session is gone: «%s»" % s1.get("esito")
        if scena == "ferma":
            return CIECO, base + " · on a still scene zero is possible: declare " \
                                 "`--scena viva` or `muovi` for a judgement"
        if scena == "muovi":
            return ROSSO, base + " · ⚠ the cursor is drawn by the page: if the desktop " \
                                 "does not react to the passage, redo it with a live scene"
        return ROSSO, base

    def ingresso(self, prima_reg):
        """Key + move/click (tap on Android).  Returns (outcome, reason)."""
        a = self.g.js(_inietta(JS_ANELLO))
        chk = self.g.js("const c=window.REMOTIX_INPUT; return c ? !!c.__banco : null;")
        if chk is None:
            return ROSSO, "the page has no input seam (`REMOTIX_INPUT` is null)"
        if not chk:
            return CIECO, "I could not wrap `REMOTIX_INPUT.manda` (%s)" % a
        s = self.stato()
        x, y = self.centro(s, self.o.clic[0], self.o.clic[1])
        fatti = []
        try:
            # the click first: it gives focus to the canvas, and the keyboard goes where the focus is
            if self.g.tocco:
                self.g.tocca(x, y); fatti.append("tap")
                time.sleep(0.4)
                self.g.trascina([(x, y), (x + 30, y + 15), (x + 60, y + 30)])
                fatti.append("drag")
            else:
                self.g.muovi(x - 40, y - 20); self.g.muovi(x, y)
                fatti.append("move")
                if not self.o.senza_clic:
                    self.g.clic(x, y); fatti.append("click")
            time.sleep(0.4)
            self.g.tasto(self.o.tasto); fatti.append("key %s" % self.o.tasto)
            time.sleep(0.4)
            # ⭐ one last move: if the desktop changes, a frame brings back
            #   an id ≥ all of those above
            self.g.muovi(x + 5, y + 5)
        except Exception as e:                   # noqa: BLE001
            return CIECO, "the injection did not start (%s): %s" % (", ".join(fatti),
                                                                     str(e)[:200])
        time.sleep(3.0)
        t = self.g.js(JS_TORNATI) or {}
        tipi = {TIPI_INPUT.get(int(k), k): v for k, v in (t.get("tipi") or {}).items()}
        ids = {int(k): v for k, v in (t.get("ids") or {}).items()}
        tasto_ids = ids.get(0x0105, []) + ids.get(0x0104, [])
        topo_ids = ids.get(0x0101, []) + ids.get(0x0102, [])
        spediti = "the page sent %s" % (tipi or "NOTHING")
        if not tasto_ids and not topo_ids:
            return ROSSO, "%s after %s: the input does not leave the page" % (spediti, fatti)
        mancano = []
        if not tasto_ids:
            mancano.append("the key")
        if not topo_ids:
            mancano.append("the mouse/touch")
        # 1) the server log, if there is one
        dopo, perche = leggi_registro(self.o.registro_cmd) if prima_reg is not None \
            else (None, "no --registro-cmd")
        if dopo is not None:
            nuove = [r for r in righe_nuove(prima_reg, dopo) if "input id=" in r]
            srv_t = [r for r in nuove if "POSIZIONE_TASTO" in r or "LETTERA" in r]
            srv_m = [r for r in nuove if "PUNTATORE" in r or "PULSANTE" in r]
            base = ("%s · in the server log %d new input lines (key %d, "
                    "mouse %d)" % (spediti, len(nuove), len(srv_t), len(srv_m)))
            if nuove:
                self.note.append("server: " + nuove[-1][:200])
            if mancano:
                return ROSSO, base + " · ⛔ the page did NOT send " + " and ".join(mancano)
            if srv_t and srv_m:
                return VERDE, base
            return ROSSO, base + " · ⛔ the server did not receive " + " and ".join(
                (["the key"] if not srv_t else []) + (["the mouse"] if not srv_m else []))
        # 2) without log: the return of the ids in the frames
        mx = t.get("max_tornato") or 0
        base = "%s · highest id returned in a frame: %s (%s)" % (
            spediti, mx or "none", perche)
        if mancano:
            return ROSSO, base + " · ⛔ the page did NOT send " + " and ".join(mancano)
        if mx >= max(tasto_ids) and mx >= min(topo_ids):
            return VERDE, base + " ⇒ the server applied all of them up to %d" % mx
        return CIECO, base + " · no return covering both: without the server " \
                             "log I cannot tell whether they arrived"

    def errori(self, s):
        dentro_js = (s.get("banco") or {}).get("errori") or []
        dentro_rete = (s.get("banco") or {}).get("rete") or []
        fuori_js, fuori_rete, perche = self.g.errori_fuori()
        dich = [r for r in (s.get("registro") or "").splitlines() if "⛔" in r]
        tutti_js = list(dict.fromkeys(fuori_js + dentro_js))
        tutti_rete = list(dict.fromkeys(fuori_rete + dentro_rete))
        for r in tutti_js[:12]:
            print("         js    %s" % r[:220])
        for r in tutti_rete[:12]:
            print("         net   %s" % r[:220])
        for r in dich[:12]:
            print("         ⛔pag %s" % r[:220])
        if s.get("errori_schermo"):
            print("         schermo.errori %s" % s["errori_schermo"])
        base = "%d JS errors · %d network · %d «⛔» lines declared by the page" % (
            len(tutti_js), len(tutti_rete), len(dich))
        if s.get("banco") is None and perche:
            return CIECO, base + " · ⚠ neither collector in the page nor output: " + perche
        if tutti_js or tutti_rete:
            return ROSSO, base
        return VERDE, base + (" (the page's «⛔» are listed, not judged)"
                              if dich else "")

    def corri(self, solo_ab=False):
        prima_reg, perche_reg = (leggi_registro(self.o.registro_cmd)
                                 if self.o.registro_cmd else (None, "no --registro-cmd"))
        if self.o.registro_cmd and prima_reg is None:
            self.note.append("server log: " + perche_reg)
        self.g.azzera_eventi()
        ok, motivo = self.apri()
        self.metti("a", VERDE if ok else ROSSO, motivo)
        if not ok:
            self.cieco_da("bcdefg", "(a) is not green")
            return
        e, motivo, s = self.entra(self.parola)
        self.metti("b", e, motivo)
        if e != VERDE:
            if s:
                self.metti("f", *self.errori(s))
            self.cieco_da("cdeg", "(b) is not green")
            return
        if solo_ab:
            return
        e, motivo, s = self.primo_fotogramma()
        self.metti("c", e, motivo)
        if s.get("dipinti"):
            self.metti("d", *self.continuita())
        else:
            self.cieco_da("d", "no first frame")
        if s.get("sessione"):
            prima_in = None
            if self.o.registro_cmd:
                prima_in, _ = leggi_registro(self.o.registro_cmd)
            self.metti("e", *self.ingresso(prima_in))
        else:
            self.cieco_da("e", "the session is not there")
        s = self.stato()
        self.metti("f", *self.errori(s))
        # (g) the reconnection
        try:
            self.g.ricarica()
            ok, motivo = self.apri_dopo_ricarica()
            if not ok:
                self.metti("g", ROSSO, "after the reload: " + motivo)
                return
            e, motivo, s = self.entra(self.parola)
            if e != VERDE:
                self.metti("g", e, "after the reload it does not get back in: " + motivo)
                return
            e, motivo, s = self.primo_fotogramma()
            self.metti("g", e, "back in (%s) · %s" % (
                (s.get("esito") or "")[:60], motivo))
        except Exception as ex:                  # noqa: BLE001
            self.metti("g", CIECO, "the bench could not reload: %s" % str(ex)[:200])

    def apri_dopo_ricarica(self):
        fine = time.time() + min(self.o.tetto_s, 30)
        while time.time() < fine:
            try:
                m = self.g.js(JS_MODULO)
                if m and m.get("modulo") and m.get("pronta") == "complete" and m.get("visibile"):
                    return True, ""
            except Exception:                    # noqa: BLE001
                pass
            time.sleep(0.5)
        return False, "the form does not reappear in %d s" % min(self.o.tetto_s, 30)

    def verdetto(self):
        v = [e for e, _ in self.esiti.values()]
        if ROSSO in v:
            return "FAIL"
        if CIECO in v:
            return "BLOCKED"
        return "PASS"


# ═══════════════════════════════════════════════════════════════════════════
def accendi_guida(nome, o):
    if nome == "firefox":
        return GuidaFirefox(o.porte_base, o.visibile)
    if nome == "chrome":
        return GuidaChrome(o.porte_base + 1, o.visibile)
    if nome == "android":
        return GuidaAndroid(o.porte_base + 2, o.lascia_acceso)
    raise ValueError(nome)


def un_browser(nome, o, url, parola, solo_ab=False, etichetta=""):
    print("\n══ %s%s ══════════════════════════════" % (nome.upper(), etichetta), flush=True)
    g = None
    riga = {"browser": nome, "url": url, "etichetta": etichetta.strip(" ·") or "prova"}
    try:
        try:
            g = accendi_guida(nome, o)
        except Exception as e:                   # noqa: BLE001
            print("   ⛔ the browser did not start: %s" % str(e)[:300])
            riga.update(verdetto="BLOCKED", palco=None,
                        esiti={p: [CIECO, "browser not started: %s" % str(e)[:200]]
                               for p in "abcdefg"})
            print("RIGA " + json.dumps(riga, ensure_ascii=False))
            return riga
        palco = g.palco()
        print("   stage: %s" % palco, flush=True)
        pr = Prova(g, o, url, parola)
        try:
            pr.corri(solo_ab=solo_ab)
        except Exception as e:                   # noqa: BLE001
            print("   ⛔ the bench fell over: %s" % repr(e)[:300])
            pr.cieco_da("abcdefg", "the bench fell over: %s" % str(e)[:160])
        if solo_ab:
            for p in "cdefg":
                pr.esiti.setdefault(p, (CIECO, "not looked at: certification test"))
        for n in pr.note:
            print("   note: %s" % n)
        v = pr.verdetto()
        print("   ▶ %s: %s" % (nome, v))
        riga.update(verdetto=v, palco=palco, headless=(not o.visibile) if nome != "android"
                    else "emulatore-software",
                    scena=o.scena, tetto_s=o.tetto_s,
                    esiti={p: [e, m] for p, (e, m) in sorted(pr.esiti.items())},
                    rifiuto=pr.rifiuto, note=pr.note)
        print("RIGA " + json.dumps(riga, ensure_ascii=False), flush=True)
        return riga
    finally:
        if g is not None:
            try:
                g.chiudi()
            except Exception as e:               # noqa: BLE001
                print("   ⚠ closing the browser: %s" % e)


def porta_vuota():
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


def certifica(o, browser):
    print("\n══════════ CERTIFICATION OF THE BENCH ══════════")
    e, t = certifica_giudice()
    print("   pixel judge: %s — %s" % ({VERDE: "⭐ can say degenerate",
                                         ROSSO: "⛔ BLIND", CIECO: "⚠ 3"}[e], t))
    tab = [("giudice-pixel", e, t)]
    for nome in browser:
        vuota = "https://127.0.0.1:%d/" % porta_vuota()
        u = url_android(vuota) if nome == "android" else vuota
        r = un_browser(nome, o, u, o.parola, solo_ab=True, etichetta=" · certify: empty port")
        ea = r["esiti"]["a"][0]
        tab.append(("%s empty port" % nome, VERDE if ea == ROSSO else ROSSO,
                    "(a)=%s — expected 1" % ea))
        u = url_android(o.url) if nome == "android" else o.url
        r = un_browser(nome, o, u, o.parola + "-SBAGLIATA-" + str(os.getpid()),
                       solo_ab=True, etichetta=" · certify: wrong password")
        ea, eb = r["esiti"]["a"][0], r["esiti"]["b"]
        # ⛔ the red must be a REFUSAL: the page sent the
        #   credentials (line "CREDENZIALI sent", pagina.html ~4955) and
        #   was not admitted.  A missed connection certifies nothing.
        if ea != VERDE:
            tab.append(("%s wrong password" % nome, CIECO,
                        "(a)=%s: without the page (b) cannot be certified" % ea))
        elif eb[0] == ROSSO and r.get("rifiuto"):
            tab.append(("%s wrong password" % nome, VERDE, "(b)=1 by refusal: %s" % eb[1][:120]))
        elif eb[0] == ROSSO:
            tab.append(("%s wrong password" % nome, CIECO,
                        "(b)=1 but NOT by refusal (the server did not answer the "
                        "credentials): %s" % eb[1][:160]))
        else:
            tab.append(("%s wrong password" % nome, ROSSO,
                        "⛔ (b)=%s with the wrong password: bench BLIND" % eb[0]))
    print("\n══════════ OUTCOME OF THE CERTIFICATION ══════════")
    for n, e, t in tab:
        print("   %-28s %s  %s" % (n, {VERDE: "⭐ certified", ROSSO: "⛔ NOT certified",
                                      CIECO: "⚠ 3 not certifiable here"}[e], t))
    print("RIGA " + json.dumps({"certificazione": [[n, e, t] for n, e, t in tab]},
                               ensure_ascii=False))
    return 1 if any(e == ROSSO for _, e, _ in tab) else (3 if any(e == CIECO for _, e, _ in tab) else 0)


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--url", default="https://192.168.0.2:8511/")
    a.add_argument("--utente", default="prova")
    a.add_argument("--parola", default=os.environ.get("REMOTIX_PAROLA", ""),
                   help="or in the REMOTIX_PAROLA variable")
    a.add_argument("--browser", default="firefox,chrome,android")
    a.add_argument("--visibile", action="store_true",
                   help="real window instead of headless (Firefox and Chrome)")
    a.add_argument("--tetto-s", type=int, default=30,
                   help="ceiling for admission and for the first frame")
    a.add_argument("--scena", choices=("muovi", "viva", "ferma"), default="muovi")
    a.add_argument("--continuita-s", type=int, default=8)
    a.add_argument("--tasto", choices=sorted(TASTI), default="Control",
                   help="the key to press: Control alone does nothing on the desktop")
    a.add_argument("--clic", default="0.5,0.5",
                   help="where to click/tap, in fractions of the canvas")
    a.add_argument("--senza-clic", action="store_true",
                   help="movement only, no click (desktop with delicate things)")
    a.add_argument("--registro-cmd", default="",
                   help="shell command that prints the server log")
    a.add_argument("--finestra", default="1400x1000",
                   help="size of the browsers' window, WxH")
    a.add_argument("--salva", default="", help="folder where to leave the photographs")
    a.add_argument("--porte-base", type=int, default=2851)
    a.add_argument("--lascia-acceso", action="store_true",
                   help="do not stop the emulator if the bench started it")
    a.add_argument("--certifica", action="store_true")
    o = a.parse_args()
    FINESTRA[:] = [int(x) for x in o.finestra.lower().split("x")]
    o.clic = [float(x) for x in o.clic.split(",")]
    if o.salva:
        os.makedirs(o.salva, exist_ok=True)
    browser = [b.strip() for b in o.browser.split(",") if b.strip()]
    for b in browser:
        if b not in ("firefox", "chrome", "android"):
            a.error("unknown browser: %s" % b)
    if not o.parola:
        a.error("--parola is needed (or REMOTIX_PAROLA)")
    print("⭐ 12-client-veri · %s · user %s · browser %s · ceiling %d s · scene «%s» · %s"
          % (o.url, o.utente, ",".join(browser), o.tetto_s, o.scena,
             "real windows" if o.visibile else "HEADLESS (no GPU)"))
    if o.certifica:
        return certifica(o, browser)
    righe = []
    for b in browser:
        u = url_android(o.url) if b == "android" else o.url
        righe.append(un_browser(b, o, u, o.parola))
    print("\n══════════ VERDICTS ══════════")
    for r in righe:
        print("   %-8s %s" % (r["browser"], r["verdetto"]))
    v = [r["verdetto"] for r in righe]
    return 1 if "FAIL" in v else (3 if "BLOCKED" in v else 0)


if __name__ == "__main__":
    sys.exit(main())
