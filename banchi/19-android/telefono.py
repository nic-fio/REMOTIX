#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
telefono.py — THE REAL PHONE DRIVER for the suite (phase 19 §5)
===========================================================================

`suite.py --browser telefono` loads it in place of Firefox or desktop
Chrome.  It runs ON THE SERVER, inside the suite's tests, and talks to two ports
that the laptop carries to it through the ssh tunnel (`19-android.py`):

  127.0.0.1:19333   the DevTools protocol of the phone's Chrome
                    (laptop: `adb forward tcp:9333 localabstract:chrome_devtools_remote`)
  127.0.0.1:19334   the laptop's COUNTER: the only things that need adb
                    (call in progress?, Chrome in front, real touch, rotation,
                    Chrome stopped abruptly, on-screen keyboard open?).  ⛔ The phone's key stays on the
                    laptop: only named questions pass through here.

⛔ THE PHONE'S RULES (DECISIONI §10.27, fasi/19 §5):
  - only Chrome, and only towards the server's boxes: `vai()` refuses every
    address that is not https://192.168.0.2:8511-8514 or 8611-8614 (and 8599, the nonexistent server of the F-001 fault);
  - a tab of OUR OWN (new), never the user's: it is opened with /json/new,
    closed at the end; the laptop records it and closes it even if things crash here;
  - before every gesture the call check (the counter does it, one
    `mCallState=[12]` line per SIM): with a call we WAIT, and if it does not
    end the test falls BLOCKED "call in progress" — never a gesture during it.

The input of the common tests (clicks, keys, drags) goes through the DevTools
protocol as for desktop Chrome — mouse and keyboard, i.e. the DeX case
(`SPECIFICHE.md` §7.2: "on Android the primary use is DeX").  The REAL TOUCH
(`adb shell input`) is used by the touch test, `15-f031-tocco.py`.
"""
import base64
import json
import os
import time
import urllib.error
import urllib.parse
import urllib.request

PORTA_CDP = int(os.environ.get("REMOTIX_TELEFONO_CDP", "19333"))
SPORTELLO = "http://127.0.0.1:%s" % os.environ.get("REMOTIX_TELEFONO_SPORTELLO", "19334")
SERVER = os.environ.get("REMOTIX_TELEFONO_HOST", "192.168.0.2")
# 8599: the "nonexistent server" of the F-001 fault (nobody listens: the page does not open)
PORTE_AMMESSE = set(range(8511, 8515)) | set(range(8611, 8615)) | {8599}
# ⚠ only for the bench's dry run (19-android.py a-secco): a local page over http
A_SECCO = os.environ.get("REMOTIX_TELEFONO_A_SECCO") == "1"
GUARDIA_OGNI_S = 5.0

# The notebook of REAL touches: where every finger landed, as seen by the page.
QUADERNO_TOCCHI = r"""
(function () {
  if (window.__T19) return;
  window.__T19 = [];
  addEventListener("touchstart", function (e) {
    const t = e.touches[0];
    if (!t) return;
    window.__T19.push({ x: t.clientX, y: t.clientY, n: e.touches.length,
                        su: (e.target && e.target.id) || (e.target && e.target.tagName) || "",
                        t: performance.now() });
    if (window.__T19.length > 200) window.__T19.shift();
  }, { capture: true, passive: true });
})();
"""


class ChiamataInCorso(RuntimeError):
    """The phone is in a call: no gesture."""


def sportello(percorso, dati=None, tetto=1800):
    """A question to the laptop's counter.  Returns the answer's dictionary."""
    corpo = json.dumps(dati or {}).encode()
    rq = urllib.request.Request(SPORTELLO + percorso, data=corpo, method="POST",
                                headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(rq, timeout=tetto) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            d = json.loads(e.read().decode() or "{}")
        except ValueError:
            d = {}
        if e.code == 409:
            raise ChiamataInCorso(d.get("perche") or "call in progress on the phone")
        raise RuntimeError("counter %s: %s %s" % (percorso, e.code, d.get("perche", "")))
    except urllib.error.URLError as e:
        raise RuntimeError("the laptop's counter does not answer (%s): is the ssh tunnel "
                           "there?  %s" % (SPORTELLO, e))


def ammesso(url):
    """⛔ Only the server's boxes (and the blank page)."""
    if url in ("about:blank",):
        return True
    u = urllib.parse.urlsplit(url)
    if A_SECCO and u.scheme == "http" and u.hostname == "127.0.0.1":
        return True
    return u.scheme == "https" and u.hostname == SERVER and u.port in PORTE_AMMESSE


def orienta(verso):
    """\"altro\" turns the phone the other way; \"partenza\" puts it back as it was."""
    r = sportello("/ruota", {"verso": verso})
    return r.get("detto", str(r))


def _http(percorso, metodo="GET"):
    rq = urllib.request.Request("http://127.0.0.1:%d%s" % (PORTA_CDP, percorso), method=metodo)
    with urllib.request.urlopen(rq, timeout=15) as r:
        t = r.read().decode()
    try:
        return json.loads(t)
    except ValueError:
        return t


def _veri():
    """`12-client-veri.py` as the suite loads it (already loaded: not reloaded)."""
    import sys
    s = sys.modules.get("suite") or sys.modules.get("__main__")
    v = getattr(s, "VERI", None)
    if v is None:
        import importlib.util as iu
        qui = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sp = iu.spec_from_file_location("veri", os.path.join(qui, "12-client-veri.py"))
        v = iu.module_from_spec(sp)
        sp.loader.exec_module(v)
    return v


VERI = _veri()


class GuidaTelefono(VERI.GuidaCdp):
    """The real phone's Chrome, in a tab of OUR OWN."""
    tocco = False                 # the common input is the protocol's mouse+keyboard (DeX)
    _n_chiusure = 0

    def __init__(self, o=None):
        super().__init__(PORTA_CDP, "telefono")
        self.o = o
        self._ultima_guardia = 0.0
        self.scala_foto = 1
        self._palco = None
        sportello("/pronto")                      # call? screen? Chrome in front
        self.scheda = self._nuova_scheda()
        sportello("/mia", {"id": self.scheda["id"]})
        self.aggancia()
        try:
            self.scala_foto = float(self.js("return devicePixelRatio") or 1)
        except Exception:                         # noqa: BLE001
            self.scala_foto = 1

    # -- the tab ---------------------------------------------------------------
    def _nuova_scheda(self):
        try:
            t = _http("/json/new?about:blank", "PUT")
            if isinstance(t, dict) and t.get("id"):
                return t
        except Exception:                         # noqa: BLE001
            pass
        # fallback: Target.createTarget from the browser target
        v = _http("/json/version")
        b = VERI.Cdp(self._qui(v["webSocketDebuggerUrl"]))
        r = b.chiama("Target.createTarget", url="about:blank")
        try:
            b.ws.chiudi()
        except Exception:                         # noqa: BLE001
            pass
        for t in _http("/json/list"):
            if t.get("id") == r.get("targetId"):
                return t
        raise RuntimeError("the new tab does not appear in the phone's list")

    @staticmethod
    def _qui(ws):
        """The websocket goes through the tunnel: the host is always 127.0.0.1:PORTA_CDP."""
        u = urllib.parse.urlsplit(ws)
        return urllib.parse.urlunsplit(u._replace(netloc="127.0.0.1:%d" % PORTA_CDP))

    def aggancia(self, attesa=40):
        self.cdp = VERI.Cdp(self._qui(self.scheda["webSocketDebuggerUrl"]))
        for d in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
            try:
                self.cdp.chiama(d)
            except Exception:                     # noqa: BLE001
                pass
        self.cdp.chiama("Page.addScriptToEvaluateOnNewDocument", source=VERI.RACCOGLITORE)
        self.cdp.chiama("Page.addScriptToEvaluateOnNewDocument", source=QUADERNO_TOCCHI)
        try:
            self.cdp.chiama("Page.bringToFront")
        except Exception:                         # noqa: BLE001
            pass

    def versione(self):
        try:
            return _http("/json/version").get("Browser", "?")
        except Exception as e:                    # noqa: BLE001
            return "? (%s)" % e

    def palco(self):
        if self._palco is None:
            try:
                self._palco = sportello("/palco").get("palco")
            except Exception as e:                # noqa: BLE001
                self._palco = "%s on Android (stage not read: %s)" % (self.versione(), e)
        return self._palco

    # -- the call guard ------------------------------------------------------
    def guardia(self, subito=False):
        """⚠ The PROTOCOL events (clicks, keys) go to Chrome's renderer, not
        to the system: they cannot answer a call nor touch anything else.  For
        them the check is redone every 5 s (a test sends hundreds of keys).
        The REAL gestures (`adb shell input`) the counter checks every time."""
        if not subito and time.time() - self._ultima_guardia < GUARDIA_OGNI_S:
            return
        try:
            sportello("/chiamata")                # it waits; 409 ⇒ ChiamataInCorso
        except Exception:
            self._ultima_guardia = 0.0            # the next gesture checks again
            raise
        self._ultima_guardia = time.time()

    # -- the actions: guard first --------------------------------------------
    def vai(self, url):
        if not ammesso(url):
            raise RuntimeError("⛔ the phone goes only to the server's boxes, not to %s" % url)
        self.guardia(subito=True)
        return super().vai(url)

    def ricarica(self):
        self.guardia()
        return super().ricarica()

    def muovi(self, x, y):
        self.guardia()
        return super().muovi(x, y)

    def clic(self, x, y):
        self.guardia()
        return super().clic(x, y)

    def tocca(self, x, y):
        self.guardia()
        return super().tocca(x, y)

    def trascina(self, punti):
        self.guardia()
        return super().trascina(punti)

    def tasto(self, t):
        self.guardia()
        return super().tasto(t)

    # -- closing, and killing -------------------------------------------------
    def _chiudi_scheda(self):
        sid = self.scheda.get("id")
        try:
            _http("/json/close/%s" % sid, "PUT")
        except Exception:                         # noqa: BLE001
            try:
                _http("/json/close/%s" % sid)
            except Exception:                     # noqa: BLE001
                pass
        try:
            sportello("/non-mia", {"id": sid})
        except Exception:                         # noqa: BLE001
            pass

    def chiudi(self):
        # ⭐ the evidence: how the phone's page was a moment before closing
        cartella = getattr(self.o, "evidenze", "") if self.o else ""
        if cartella:
            GuidaTelefono._n_chiusure += 1
            foto_png(self, "chiusura-%02d" % GuidaTelefono._n_chiusure, cartella)
        try:
            self.cdp.chiama("Page.navigate", url="about:blank")   # pagehide ⇒ CONGEDO
            time.sleep(1)
        except Exception:                         # noqa: BLE001
            pass
        try:
            self.cdp.ws.chiudi()
        except Exception:                         # noqa: BLE001
            pass
        self._chiudi_scheda()

    def uccidi(self):
        """⛔ Chrome stopped ABRUPTLY (`am force-stop`): no farewell, the wire goes silent.
        It is the gesture of F-020 "browser closed abruptly".  Returns 1 (one process)."""
        self.guardia(subito=True)
        sportello("/uccidi-chrome")
        try:
            self.cdp.ws.chiudi()
        except Exception:                         # noqa: BLE001
            pass
        self.cdp = None
        return 1

    # ═════════════════════════════════════════════════════════════════════════
    #  TOUCH (for 15-f031-tocco.py): the trackpad model of SPECIFICHE §7.1
    # ═════════════════════════════════════════════════════════════════════════
    def stato_tocco(self):
        return self.js("return (window.REMOTIX && REMOTIX.tocco) ? REMOTIX.tocco.stato() : null")

    def disposizione(self):
        return self.js("return (window.REMOTIX && REMOTIX.tocco && REMOTIX.tocco.disposizione)"
                       " ? REMOTIX.tocco.disposizione() : null")

    def tocchi_visti(self, da=0):
        return (self.js("return (window.__T19 || []).slice(arguments[0])", da) or [])

    def puntatore_vetro(self, geo):
        """Where the DRAWN pointer is, in glass coordinates."""
        st = self.stato_tocco() or {}
        p = st.get("puntatore")
        if not p:
            return None
        return (geo["left"] + (geo["bx0"] + p[0] * geo["sx"]) * geo["vx"],
                geo["top"] + (geo["by0"] + p[1] * geo["sy"]) * geo["vy"])

    def schermo(self):
        """(width, height) of the screen in REAL pixels, in the current orientation; dpr."""
        r = self.js("return [screen.width, screen.height, devicePixelRatio,"
                    " innerWidth, innerHeight]")
        return r[0] * r[2], r[1] * r[2], r[2], r[3], r[4]

    def dito_cdp(self, punti, pausa_s=0.03, tieni_s=0.0):
        """A protocol finger: down on the first point, the moves, up."""
        self.guardia()
        c = self.cdp.chiama
        c("Input.dispatchTouchEvent", type="touchStart",
          touchPoints=[{"x": punti[0][0], "y": punti[0][1]}])
        if tieni_s:
            time.sleep(tieni_s)
        for x, y in punti[1:]:
            time.sleep(pausa_s)
            c("Input.dispatchTouchEvent", type="touchMove", touchPoints=[{"x": x, "y": y}])
        time.sleep(pausa_s)
        c("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])

    def _centro_tela(self, geo):
        return geo["left"] + geo["width"] / 2.0, geo["top"] + geo["height"] / 2.0

    def porta_il_puntatore(self, geo, tx, ty, giri=6):
        """Drags a finger (protocol) until the drawn pointer is on (tx,ty)
        of the glass.  Returns the final error in glass px, or None if unreadable."""
        err = None
        for _ in range(giri):
            p = self.puntatore_vetro(geo)
            if p is None:
                return None
            dx, dy = tx - p[0], ty - p[1]
            err = max(abs(dx), abs(dy))
            if err <= 1.0:
                return err
            # a step that stays inside the canvas, and that is ALWAYS a drag
            # (beyond the tap threshold, 9 CSS px): if the step is short, a wide loop
            lim = 0.35 * min(geo["width"], geo["height"])
            dx, dy = max(-lim, min(lim, dx)), max(-lim, min(lim, dy))
            cx, cy = self._centro_tela(geo)
            x0, y0 = cx - dx / 2.0, cy - dy / 2.0
            # ⚠ the page CONSUMES the sample that exceeds the slop (D_TAP, 9 CSS
            #   px: `tocco_muovi`, "the slop is consumed"): a first step
            #   of 12 px vertically that moves nothing, and from there the whole
            #   movement.  Before, the consumed step was a piece of dx: the pointer
            #   lagged 9-18 px behind at every loop (2 Oct 2026, S23+).
            sb = 12.0 if y0 + 12.0 + max(dy, 0) < geo["top"] + geo["height"] else -12.0
            punti = [(x0, y0), (x0, y0 + sb)]
            n = 10
            for i in range(1, n + 1):
                punti.append((x0 + dx * i / n, y0 + sb + dy * i / n))
            self.dito_cdp(punti)
            time.sleep(0.25)
        p = self.puntatore_vetro(geo)
        return None if p is None else max(abs(tx - p[0]), abs(ty - p[1]))

    def tap_vero(self, geo):
        """⭐ A REAL TAP (`adb shell input tap`) inside the canvas.  In the trackpad
        model the tap clicks where the pointer is, not where the finger lands:
        the finger goes to the centre of the canvas.  Returns the touch as the page saw it."""
        da = len(self.tocchi_visti())
        x, y = self.vetro_su_schermo(*self._centro_tela(geo))
        sportello("/tocca", {"x": round(x), "y": round(y)})
        time.sleep(0.6)
        return (self.tocchi_visti(da) or [None])[0]

    def scorri_vero(self, geo, dx, dy, ms=600):
        """⭐ A REAL finger that swipes (`adb shell input swipe`) by (dx,dy) glass px,
        starting so that both ends stay inside the canvas."""
        da = len(self.tocchi_visti())
        # ⚠ a short stroke, like the hand on a trackpad: a half-screen diagonal
        #   swipe Chrome does not pass to the page (2 Oct
        #   2026, S23+: 200x284 CSS px ⇒ no touch seen).  The rest is done by
        #   the next stroke (15-f031 `DITI_VERI_MAX`).
        lim = 0.3 * min(geo["width"], geo["height"])
        k = min(1.0, lim / max(abs(dx), abs(dy), 1e-9))
        dx, dy = dx * k, dy * k
        # ⚠ the page consumes the slop (D_TAP, 9 CSS px, and the sample that
        #   exceeds it: `tocco_muovi`): the finger swipes ~10 px more, in the same
        #   direction, or small corrections would move nothing
        n = (dx * dx + dy * dy) ** 0.5
        if n > 0.5:
            dx, dy = dx * (n + 10.0) / n, dy * (n + 10.0) / n
        cx, cy = self._centro_tela(geo)
        # the finger STARTS from the centre of the canvas (where the real touch always arrives)
        x0, y0 = self.vetro_su_schermo(cx, cy)
        x1, y1 = self.vetro_su_schermo(cx + dx, cy + dy)
        self.ultimo_dito = (round(x0), round(y0), round(x1), round(y1))
        sportello("/scorri", {"x1": round(x0), "y1": round(y0), "x2": round(x1),
                              "y2": round(y1), "ms": int(ms)})
        # ⚠ adb over Wi-Fi: the finger may start a little after the counter's
        #   answer (2 Oct 2026: with a fixed 0.5 s the first swipe "was not there")
        fine = time.time() + 3.0
        while True:
            t = self.tocchi_visti(da)
            if t or time.time() > fine:
                break
            time.sleep(0.2)
        time.sleep(0.3)
        return (t or [None])[0]

    # ═════════════════════════════════════════════════════════════════════════
    #  THE ON-SCREEN KEYBOARD (for 15-f031-tocco.py, "keyboard only on request",
    #  DECISIONI §10.28): the state is told by ANDROID, not the page
    # ═════════════════════════════════════════════════════════════════════════
    def tastiera_aperta(self):
        """True/False from the `mInputShown` line of `dumpsys input_method` (the
        counter); None if unreadable."""
        try:
            return sportello("/tastiera").get("aperta")
        except RuntimeError:
            return None

    def aspetta_tastiera(self, voluta, tetto_s=3.0):
        """Waits for the keyboard to be `voluta` (Android's animation lasts a few
        tenths).  Returns the last state read (True/False/None)."""
        fine = time.time() + tetto_s
        while True:
            a = self.tastiera_aperta()
            if a is voluta or time.time() > fine:
                return a
            time.sleep(0.3)

    def comando_tastiera(self):
        """The centre of the page's ⌨ control, in glass coordinates, or None
        if the page does not show it."""
        return self.js("const b=document.getElementById('tastiera-comando');"
                       "if(!b||getComputedStyle(b).display==='none') return null;"
                       "const r=b.getBoundingClientRect();"
                       "return [r.left+r.width/2, r.top+r.height/2, r.width, r.height];")

    def tocco_vero_in(self, x, y):
        """⭐ A REAL TAP (`adb shell input tap`) at (x,y) of the glass.  Returns the
        touch as the page saw it, or None."""
        self.guardia(subito=True)
        da = len(self.tocchi_visti())
        sx, sy = self.vetro_su_schermo(x, y)
        sportello("/tocca", {"x": round(sx), "y": round(sy)})
        time.sleep(0.6)
        return (self.tocchi_visti(da) or [None])[0]

    def scrivi_ime(self, parola):
        """A word as an on-screen keyboard writes it: composition letter by
        letter and then the commit (DevTools protocol, the input method
        route: `input` events, `keyCode` 229).  It goes to the focused field."""
        self.guardia()
        c = self.cdp.chiama
        try:
            for i in range(1, len(parola) + 1):
                c("Input.imeSetComposition", text=parola[:i], selectionStart=i, selectionEnd=i)
                time.sleep(0.08)
        except Exception:                         # noqa: BLE001
            pass                                  # without composition: the commit remains
        c("Input.insertText", text=parola)

    _scarto = None        # (ox, oy): screen = offset + glass × dpr, from the first real touch

    def vetro_su_schermo(self, x, y):
        sw, sh, dpr, iw, ih = self.schermo()
        if self._scarto is None:
            # first estimate: the page fills the bottom of the screen, as wide as it
            # (above is Chrome's bar); the first real touch corrects it
            return (sw - iw * dpr) / 2.0 + x * dpr, (sh - ih * dpr) + y * dpr - 0.0
        return self._scarto[0] + x * dpr, self._scarto[1] + y * dpr

    def taratura(self, geo):
        """A real finger that swipes a little (it only moves the pointer, no click):
        where the page saw it tells the offset between screen and glass."""
        sw, sh, dpr, iw, ih = self.schermo()
        cx, cy = self._centro_tela(geo)
        x0, y0 = self.vetro_su_schermo(cx, cy)
        da = len(self.tocchi_visti())
        sportello("/scorri", {"x1": round(x0), "y1": round(y0), "x2": round(x0 + 60 * dpr),
                              "y2": round(y0), "ms": 400})
        time.sleep(0.5)
        t = (self.tocchi_visti(da) or [None])[0]
        if not t:
            return None
        self._scarto = (x0 - t["x"] * dpr, y0 - t["y"] * dpr)
        return {"tocco": t, "scarto": [round(v, 1) for v in self._scarto]}


def foto_png(g, nome, cartella):
    """A photo of the WHOLE phone page (evidence), or None."""
    try:
        s = g.cdp.chiama("Page.captureScreenshot", format="png")
    except Exception:                             # noqa: BLE001
        return None
    if not cartella:
        return None
    p = os.path.join(cartella, "telefono-%s.png" % nome)
    with open(p, "wb") as f:
        f.write(base64.b64decode(s["data"]))
    return p
