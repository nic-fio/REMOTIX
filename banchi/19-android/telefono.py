#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
telefono.py — THE REAL PHONE DRIVER for the suite (phase 19 §5)
===========================================================================

`suite.py --browser phone` loads it in place of Firefox or desktop
Chrome.  It runs ON THE SERVER, inside the suite's tests, and talks to two ports
that the laptop carries to it through the ssh tunnel (`19-android.py`):

  127.0.0.1:19333   the DevTools protocol of the phone's Chrome
                    (laptop: `adb forward tcp:9333 localabstract:chrome_devtools_remote`)
  127.0.0.1:19334   the laptop's COUNTER: the only things that need adb
                    (call in progress?, Chrome in front, real touch, rotation,
                    Chrome stopped abruptly, on-screen keyboard open?).  ⛔ The phone's key stays on the
                    laptop: only named questions pass through here.

⛔ THE PHONE'S RULES (DECISIONI §10.27, fasi/19 §5):
  - only Chrome, and only towards the server's boxes: `go_to()` refuses every
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

CDP_PORT = int(os.environ.get("REMOTIX_PHONE_CDP", "19333"))
ENDPOINT = "http://127.0.0.1:%s" % os.environ.get("REMOTIX_PHONE_ENDPOINT", "19334")
SERVER = os.environ.get("REMOTIX_PHONE_HOST", "192.168.0.2")
# 8599: the "nonexistent server" of the F-001 fault (nobody listens: the page does not open)
ALLOWED_PORTS = set(range(8511, 8515)) | set(range(8611, 8615)) | {8599}
# ⚠ only for the bench's dry run (19-android.py a-secco): a local page over http
DRY_RUN = os.environ.get("REMOTIX_PHONE_DRY_RUN") == "1"
GUARD_EVERY_S = 5.0

# The notebook of REAL touches: where every finger landed, as seen by the page.
NOTEBOOK_TOUCHES = r"""
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


class CallInProgress(RuntimeError):
    """The phone is in a call: no gesture."""


def endpoint(fpath, data_v=None, ceiling=1800):
    """A question to the laptop's counter.  Returns the answer's dictionary."""
    body_el = json.dumps(data_v or {}).encode()
    rq = urllib.request.Request(ENDPOINT + fpath, data=body_el, method="POST",
                                headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(rq, timeout=ceiling) as r:
            return json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            d = json.loads(e.read().decode() or "{}")
        except ValueError:
            d = {}
        if e.code == 409:
            raise CallInProgress(d.get("reason_text") or "call in progress on the phone")
        raise RuntimeError("counter %s: %s %s" % (fpath, e.code, d.get("reason_text", "")))
    except urllib.error.URLError as e:
        raise RuntimeError("the laptop's counter does not answer (%s): is the ssh tunnel "
                           "there?  %s" % (ENDPOINT, e))


def admitted(url):
    """⛔ Only the server's boxes (and the blank page)."""
    if url in ("about:blank",):
        return True
    u = urllib.parse.urlsplit(url)
    if DRY_RUN and u.scheme == "http" and u.hostname == "127.0.0.1":
        return True
    return u.scheme == "https" and u.hostname == SERVER and u.port in ALLOWED_PORTS


def orients(which_way):
    """\"other_one\" turns the phone the other way; \"departure\" puts it back as it was."""
    r = endpoint("/rotate", {"which_way": which_way})
    return r.get("said", str(r))


def _http(fpath, meth="GET"):
    rq = urllib.request.Request("http://127.0.0.1:%d%s" % (CDP_PORT, fpath), method=meth)
    with urllib.request.urlopen(rq, timeout=15) as r:
        t = r.read().decode()
    try:
        return json.loads(t)
    except ValueError:
        return t


def _real():
    """`12-client-veri.py` as the suite loads it (already loaded: not reloaded)."""
    import sys
    s = sys.modules.get("suite") or sys.modules.get("__main__")
    v = getattr(s, "REAL", None)
    if v is None:
        import importlib.util as iu
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        sp = iu.spec_from_file_location("genuine", os.path.join(here, "12-client-veri.py"))
        v = iu.module_from_spec(sp)
        sp.loader.exec_module(v)
    return v


REAL = _real()


class PhoneDriver(REAL.CdpDriver):
    """The real phone's Chrome, in a tab of OUR OWN."""
    tap = False                 # the common input is the protocol's mouse+keyboard (DeX)
    _n_closures = 0

    def __init__(self, o=None):
        super().__init__(CDP_PORT, "phone")
        self.o = o
        self._last_guard = 0.0
        self.scale_photo = 1
        self._stage = None
        endpoint("/ready")                      # call? screen? Chrome in front
        self.gpu_card = self._new_tab()
        endpoint("/my", {"id": self.gpu_card["id"]})
        self.hook()
        try:
            self.scale_photo = float(self.js("return devicePixelRatio") or 1)
        except Exception:                         # noqa: BLE001
            self.scale_photo = 1

    # -- the tab ---------------------------------------------------------------
    def _new_tab(self):
        try:
            t = _http("/json/new?about:blank", "PUT")
            if isinstance(t, dict) and t.get("id"):
                return t
        except Exception:                         # noqa: BLE001
            pass
        # fallback: Target.createTarget from the browser target
        v = _http("/json/version")
        b = REAL.Cdp(self._here(v["webSocketDebuggerUrl"]))
        r = b.call("Target.createTarget", url="about:blank")
        try:
            b.ws.shut()
        except Exception:                         # noqa: BLE001
            pass
        for t in _http("/json/list"):
            if t.get("id") == r.get("targetId"):
                return t
        raise RuntimeError("the new tab does not appear in the phone's list")

    @staticmethod
    def _here(ws):
        """The websocket goes through the tunnel: the host is always 127.0.0.1:CDP_PORT."""
        u = urllib.parse.urlsplit(ws)
        return urllib.parse.urlunsplit(u._replace(netloc="127.0.0.1:%d" % CDP_PORT))

    def hook(self, wait=40):
        self.cdp = REAL.Cdp(self._here(self.gpu_card["webSocketDebuggerUrl"]))
        for d in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
            try:
                self.cdp.call(d)
            except Exception:                     # noqa: BLE001
                pass
        self.cdp.call("Page.addScriptToEvaluateOnNewDocument", source=REAL.COLLECTOR)
        self.cdp.call("Page.addScriptToEvaluateOnNewDocument", source=NOTEBOOK_TOUCHES)
        try:
            self.cdp.call("Page.bringToFront")
        except Exception:                         # noqa: BLE001
            pass

    def version_v(self):
        try:
            return _http("/json/version").get("Browser", "?")
        except Exception as e:                    # noqa: BLE001
            return "? (%s)" % e

    def stage(self):
        if self._stage is None:
            try:
                self._stage = endpoint("/stage").get("stage")
            except Exception as e:                # noqa: BLE001
                self._stage = "%s on Android (stage not read: %s)" % (self.version_v(), e)
        return self._stage

    # -- the call guard ------------------------------------------------------
    def guard(self, immediately=False):
        """⚠ The PROTOCOL events (clicks, keys) go to Chrome's renderer, not
        to the system: they cannot answer a call nor touch anything else.  For
        them the check is redone every 5 s (a test sends hundreds of keys).
        The REAL gestures (`adb shell input`) the counter checks every time."""
        if not immediately and time.time() - self._last_guard < GUARD_EVERY_S:
            return
        try:
            endpoint("/call")                # it waits; 409 ⇒ CallInProgress
        except Exception:
            self._last_guard = 0.0            # the next gesture checks again
            raise
        self._last_guard = time.time()

    # -- the actions: guard first --------------------------------------------
    def go_to(self, url):
        if not admitted(url):
            raise RuntimeError("⛔ the phone goes only to the server's boxes, not to %s" % url)
        self.guard(immediately=True)
        return super().go_to(url)

    def reload(self):
        self.guard()
        return super().reload()

    def move_to(self, x, y):
        self.guard()
        return super().move_to(x, y)

    def click(self, x, y):
        self.guard()
        return super().click(x, y)

    def touches(self, x, y):
        self.guard()
        return super().touches(x, y)

    def drag(self, points):
        self.guard()
        return super().drag(points)

    def key(self, t):
        self.guard()
        return super().key(t)

    # -- closing, and killing -------------------------------------------------
    def _close_tab(self):
        sid = self.gpu_card.get("id")
        try:
            _http("/json/close/%s" % sid, "PUT")
        except Exception:                         # noqa: BLE001
            try:
                _http("/json/close/%s" % sid)
            except Exception:                     # noqa: BLE001
                pass
        try:
            endpoint("/non-mia", {"id": sid})
        except Exception:                         # noqa: BLE001
            pass

    def shut(self):
        # ⭐ the evidence: how the phone's page was a moment before closing
        folder = getattr(self.o, "evidence", "") if self.o else ""
        if folder:
            PhoneDriver._n_closures += 1
            photo_png(self, "closure-%02d" % PhoneDriver._n_closures, folder)
        try:
            self.cdp.call("Page.navigate", url="about:blank")   # pagehide ⇒ FAREWELL
            time.sleep(1)
        except Exception:                         # noqa: BLE001
            pass
        try:
            self.cdp.ws.shut()
        except Exception:                         # noqa: BLE001
            pass
        self._close_tab()

    def kill(self):
        """⛔ Chrome stopped ABRUPTLY (`am force-stop`): no farewell, the wire goes silent.
        It is the gesture of F-020 "browser closed abruptly".  Returns 1 (one process)."""
        self.guard(immediately=True)
        endpoint("/uccidi-chrome")
        try:
            self.cdp.ws.shut()
        except Exception:                         # noqa: BLE001
            pass
        self.cdp = None
        return 1

    # ═════════════════════════════════════════════════════════════════════════
    #  TOUCH (for 15-f031-tocco.py): the trackpad model of SPECIFICHE §7.1
    # ═════════════════════════════════════════════════════════════════════════
    def touch_state(self):
        return self.js("return (window.REMOTIX && REMOTIX.tap) ? REMOTIX.tap.state() : null")

    def arrangement(self):
        return self.js("return (window.REMOTIX && REMOTIX.tap && REMOTIX.tap.arrangement)"
                       " ? REMOTIX.tap.arrangement() : null")

    def touches_seen(self, da=0):
        return (self.js("return (window.__T19 || []).slice(arguments[0])", da) or [])

    def glass_pointer(self, geo):
        """Where the DRAWN pointer is, in glass coordinates."""
        st = self.touch_state() or {}
        p = st.get("ptr")
        if not p:
            return None
        return (geo["left"] + (geo["bx0"] + p[0] * geo["left_side"]) * geo["vx"],
                geo["top"] + (geo["by0"] + p[1] * geo["sy"]) * geo["vy"])

    def display_screen(self):
        """(width, height) of the screen in REAL pixels, in the current orientation; dpr."""
        r = self.js("return [screen.width, screen.height, devicePixelRatio,"
                    " innerWidth, innerHeight]")
        return r[0] * r[2], r[1] * r[2], r[2], r[3], r[4]

    def finger_cdp(self, points, pause_s=0.03, keep_s=0.0):
        """A protocol finger: down on the first point, the moves, up."""
        self.guard()
        c = self.cdp.call
        c("Input.dispatchTouchEvent", type="touchStart",
          touchPoints=[{"x": points[0][0], "y": points[0][1]}])
        if keep_s:
            time.sleep(keep_s)
        for x, y in points[1:]:
            time.sleep(pause_s)
            c("Input.dispatchTouchEvent", type="touchMove", touchPoints=[{"x": x, "y": y}])
        time.sleep(pause_s)
        c("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])

    def _canvas_center(self, geo):
        return geo["left"] + geo["width"] / 2.0, geo["top"] + geo["height"] / 2.0

    def move_pointer(self, geo, tx, ty, rounds=6):
        """Drags a finger (protocol) until the drawn pointer is on (tx,ty)
        of the glass.  Returns the final error in glass px, or None if unreadable."""
        err = None
        for _ in range(rounds):
            p = self.glass_pointer(geo)
            if p is None:
                return None
            right, dy = tx - p[0], ty - p[1]
            err = max(abs(right), abs(dy))
            if err <= 1.0:
                return err
            # a step that stays inside the canvas, and that is ALWAYS a drag
            # (beyond the tap threshold, 9 CSS px): if the step is short, a wide loop
            lim = 0.35 * min(geo["width"], geo["height"])
            right, dy = max(-lim, min(lim, right)), max(-lim, min(lim, dy))
            cx, cy = self._canvas_center(geo)
            x0, y0 = cx - right / 2.0, cy - dy / 2.0
            # ⚠ the page CONSUMES the sample that exceeds the slop (D_TAP, 9 CSS
            #   px: `touch_move`, "the slop is consumed"): a first step
            #   of 12 px vertically that moves nothing, and from there the whole
            #   movement.  Before, the consumed step was a piece of right: the pointer
            #   lagged 9-18 px behind at every loop (2 Oct 2026, S23+).
            sb = 12.0 if y0 + 12.0 + max(dy, 0) < geo["top"] + geo["height"] else -12.0
            points = [(x0, y0), (x0, y0 + sb)]
            n = 10
            for i in range(1, n + 1):
                points.append((x0 + right * i / n, y0 + sb + dy * i / n))
            self.finger_cdp(points)
            time.sleep(0.25)
        p = self.glass_pointer(geo)
        return None if p is None else max(abs(tx - p[0]), abs(ty - p[1]))

    def real_tap(self, geo):
        """⭐ A REAL TAP (`adb shell input tap`) inside the canvas.  In the trackpad
        model the tap clicks where the pointer is, not where the finger lands:
        the finger goes to the centre of the canvas.  Returns the touch as the page saw it."""
        da = len(self.touches_seen())
        x, y = self.glass_on_screen(*self._canvas_center(geo))
        endpoint("/touches", {"x": round(x), "y": round(y)})
        time.sleep(0.6)
        return (self.touches_seen(da) or [None])[0]

    def real_scroll(self, geo, right, dy, ms=600):
        """⭐ A REAL finger that swipes (`adb shell input swipe`) by (right,dy) glass px,
        starting so that both ends stay inside the canvas."""
        da = len(self.touches_seen())
        # ⚠ a short stroke, like the hand on a trackpad: a half-screen diagonal
        #   swipe Chrome does not pass to the page (2 Oct
        #   2026, S23+: 200x284 CSS px ⇒ no touch seen).  The rest is done by
        #   the next stroke (15-f031 `REAL_FINGERS_MAX`).
        lim = 0.3 * min(geo["width"], geo["height"])
        k = min(1.0, lim / max(abs(right), abs(dy), 1e-9))
        right, dy = right * k, dy * k
        # ⚠ the page consumes the slop (D_TAP, 9 CSS px, and the sample that
        #   exceeds it: `touch_move`): the finger swipes ~10 px more, in the same
        #   direction, or small corrections would move nothing
        n = (right * right + dy * dy) ** 0.5
        if n > 0.5:
            right, dy = right * (n + 10.0) / n, dy * (n + 10.0) / n
        cx, cy = self._canvas_center(geo)
        # the finger STARTS from the centre of the canvas (where the real touch always arrives)
        x0, y0 = self.glass_on_screen(cx, cy)
        x1, y1 = self.glass_on_screen(cx + right, cy + dy)
        self.last_finger = (round(x0), round(y0), round(x1), round(y1))
        endpoint("/scroll", {"x1": round(x0), "y1": round(y0), "x2": round(x1),
                              "y2": round(y1), "ms": int(ms)})
        # ⚠ adb over Wi-Fi: the finger may start a little after the counter's
        #   answer (2 Oct 2026: with a fixed 0.5 s the first swipe "was not there")
        fine = time.time() + 3.0
        while True:
            t = self.touches_seen(da)
            if t or time.time() > fine:
                break
            time.sleep(0.2)
        time.sleep(0.3)
        return (t or [None])[0]

    # ═════════════════════════════════════════════════════════════════════════
    #  THE ON-SCREEN KEYBOARD (for 15-f031-tocco.py, "keyboard only on request",
    #  DECISIONI §10.28): the state is told by ANDROID, not the page
    # ═════════════════════════════════════════════════════════════════════════
    def keyboard_is_open(self):
        """True/False from the `mInputShown` line of `dumpsys input_method` (the
        counter); None if unreadable."""
        try:
            return endpoint("/keyboard").get("is_open")
        except RuntimeError:
            return None

    def wait_keyboard(self, intended, cap_s=3.0):
        """Waits for the keyboard to be `intended` (Android's animation lasts a few
        tenths).  Returns the last state read (True/False/None)."""
        fine = time.time() + cap_s
        while True:
            a = self.keyboard_is_open()
            if a is intended or time.time() > fine:
                return a
            time.sleep(0.3)

    def command_keyboard(self):
        """The centre of the page's ⌨ control, in glass coordinates, or None
        if the page does not show it."""
        return self.js("const b=document.getElementById('keyboard-command');"
                       "if(!b||getComputedStyle(b).display==='none') return null;"
                       "const r=b.getBoundingClientRect();"
                       "return [r.left+r.width/2, r.top+r.height/2, r.width, r.height];")

    def touch_true_in(self, x, y):
        """⭐ A REAL TAP (`adb shell input tap`) at (x,y) of the glass.  Returns the
        touch as the page saw it, or None."""
        self.guard(immediately=True)
        da = len(self.touches_seen())
        left_side, sy = self.glass_on_screen(x, y)
        endpoint("/touches", {"x": round(left_side), "y": round(sy)})
        time.sleep(0.6)
        return (self.touches_seen(da) or [None])[0]

    def write_ime(self, password):
        """A word as an on-screen keyboard writes it: composition letter by
        letter and then the commit (DevTools protocol, the input method
        route: `input` events, `keyCode` 229).  It goes to the focused field."""
        self.guard()
        c = self.cdp.call
        try:
            for i in range(1, len(password) + 1):
                c("Input.imeSetComposition", text=password[:i], selectionStart=i, selectionEnd=i)
                time.sleep(0.08)
        except Exception:                         # noqa: BLE001
            pass                                  # without composition: the commit remains
        c("Input.insertText", text=password)

    _gap = None        # (ox, oy): screen = offset + glass × dpr, from the first real touch

    def glass_on_screen(self, x, y):
        sw, sh, dpr, iw, ih = self.display_screen()
        if self._gap is None:
            # first estimate: the page fills the bottom of the screen, as wide as it
            # (above is Chrome's bar); the first real touch corrects it
            return (sw - iw * dpr) / 2.0 + x * dpr, (sh - ih * dpr) + y * dpr - 0.0
        return self._gap[0] + x * dpr, self._gap[1] + y * dpr

    def calibration(self, geo):
        """A real finger that swipes a little (it only moves the pointer, no click):
        where the page saw it tells the offset between screen and glass."""
        sw, sh, dpr, iw, ih = self.display_screen()
        cx, cy = self._canvas_center(geo)
        x0, y0 = self.glass_on_screen(cx, cy)
        da = len(self.touches_seen())
        endpoint("/scroll", {"x1": round(x0), "y1": round(y0), "x2": round(x0 + 60 * dpr),
                              "y2": round(y0), "ms": 400})
        time.sleep(0.5)
        t = (self.touches_seen(da) or [None])[0]
        if not t:
            return None
        self._gap = (x0 - t["x"] * dpr, y0 - t["y"] * dpr)
        return {"tap": t, "gap": [round(v, 1) for v in self._gap]}


def photo_png(g, label_name, folder):
    """A photo of the WHOLE phone page (evidence), or None."""
    try:
        s = g.cdp.call("Page.captureScreenshot", format="png")
    except Exception:                             # noqa: BLE001
        return None
    if not folder:
        return None
    p = os.path.join(folder, "phone-%s.png" % label_name)
    with open(p, "wb") as f:
        f.write(base64.b64decode(s["data"]))
    return p
