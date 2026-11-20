"""browserlib - two tiny browser drivers with the same face, no framework: Chrome/Chromium (DevTools protocol over a
hand-made WebSocket) and Firefox (Marionette). Extracted from the old bench (12-real-clients.py, 02-page-measure-cdp.py,
07-b46-marionette.py). Methods: navigate(url), js(body, *args), screenshot(), move(x,y), click(x,y), type_text(s),
press(name), close(). `js` takes a function BODY (with `return`) and returns its value."""
import base64
import hashlib
import json
import os
import shutil
import socket
import struct
import subprocess
import tempfile
import time
import urllib.request

MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
KEYS = {"Escape": ("Escape", "Escape", 27)}


def key_info(ch):
    """(key, code, windows virtual key) of one typed character (a-z, 0-9, space, '-')."""
    if ch.isalpha():
        return ch, "Key" + ch.upper(), ord(ch.upper())
    if ch.isdigit():
        return ch, "Digit" + ch, ord(ch)
    return {" ": (" ", "Space", 32), "-": ("-", "Minus", 189)}[ch]


class Ws:
    """Client WebSocket: text frames, masked, no extensions."""

    def __init__(self, host, port, path, timeout=60):
        self.s = socket.create_connection((host, port), timeout=10)
        self.s.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(("GET %s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (path, host, port, key)).encode())
        head = b""
        while b"\r\n\r\n" not in head:
            p = self.s.recv(4096)
            if not p:
                raise RuntimeError("socket closed during the WebSocket handshake")
            head += p
        header, _, self.buf = head.partition(b"\r\n\r\n")
        self.buf = bytearray(self.buf)
        if b" 101 " not in header.split(b"\r\n")[0]:
            raise RuntimeError("WebSocket handshake refused: " + header.split(b"\r\n")[0].decode())
        want = base64.b64encode(hashlib.sha1((key + MAGIC).encode()).digest()).decode().lower()
        if want not in header.decode("latin1").lower():
            raise RuntimeError("Sec-WebSocket-Accept does not match")

    def _read(self, n):
        while len(self.buf) < n:
            p = self.s.recv(65536)
            if not p:
                raise RuntimeError("socket closed")
            self.buf += p
        r = bytes(self.buf[:n])
        del self.buf[:n]
        return r

    def send(self, text):
        d = text.encode()
        h = bytearray([0x81])
        if len(d) < 126:
            h.append(0x80 | len(d))
        elif len(d) < 65536:
            h += bytes([0x80 | 126]) + struct.pack(">H", len(d))
        else:
            h += bytes([0x80 | 127]) + struct.pack(">Q", len(d))
        m = os.urandom(4)
        self.s.sendall(bytes(h) + m + bytes(b ^ m[i % 4] for i, b in enumerate(d)))

    def receive(self):
        out = b""
        while True:
            b0, b1 = self._read(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            body = self._read(n)
            if b0 & 0x0F == 0x9:
                self.s.sendall(b"\x8a\x80" + os.urandom(4))
            elif b0 & 0x0F == 0x8:
                raise RuntimeError("the browser closed the WebSocket")
            else:
                out += body
                if b0 & 0x80:
                    return out.decode("utf-8", "replace")


class Chrome:
    name = "chrome"

    def __init__(self, env, tmp, port=9341, size=(1400, 900)):
        exe = shutil.which("google-chrome") or shutil.which("chromium")
        if not exe:
            raise RuntimeError("neither google-chrome nor chromium is installed")
        self.exe, self.profile = exe, tempfile.mkdtemp(prefix="cr-", dir=tmp)
        cmd = [exe, "--remote-debugging-port=%d" % port, "--user-data-dir=" + self.profile, "--no-first-run",
               "--no-default-browser-check", "--disable-sync", "--password-store=basic", "--remote-allow-origins=*",
               "--ozone-platform=wayland", "--disable-gpu", "--window-size=%d,%d" % size, "about:blank"]
        self.p = subprocess.Popen(cmd, env=env, stdout=open(self.profile + "/out.log", "wb"), stderr=subprocess.STDOUT)
        end = time.time() + 40
        while True:
            try:
                tabs = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json/list" % port, timeout=3).read())
                tab = [t for t in tabs if t.get("type") == "page"][0]
                break
            except Exception as e:  # noqa: BLE001 - not up yet
                if time.time() > end:
                    raise RuntimeError("Chrome did not open its DevTools port: %s" % e)
                time.sleep(0.5)
        self.ws, self.n = Ws("127.0.0.1", port, "/devtools/page/" + tab["id"]), 0
        self.version = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port).read()).get("Browser", "?")
        for d in ("Page.enable", "Runtime.enable"):
            self.call(d)
        self.call("Emulation.setFocusEmulationEnabled", enabled=True)

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
        while True:
            r = json.loads(self.ws.receive())
            if r.get("id") == self.n:
                if "error" in r:
                    raise RuntimeError("%s: %s" % (method, json.dumps(r["error"])))
                return r.get("result", {})

    def navigate(self, url):
        err = self.call("Page.navigate", url=url).get("errorText")
        time.sleep(1.5)
        for _ in range(3):  # the certificate warning: the user's "Advanced" then "Proceed", no flag that disables checks
            if not self.js("return !!document.getElementById('proceed-link') || !!document.getElementById('details-button');"):
                break
            self.js("const d=document.getElementById('details-button'); if(d) d.click();"
                    "const p=document.getElementById('proceed-link'); if(p) p.click(); return 1;")
            time.sleep(3)
        if err and "CERT" not in err:
            raise RuntimeError(err)

    def js(self, body, *args):
        r = self.call("Runtime.evaluate", expression="(function(){%s}).apply(null,%s)" % (body, json.dumps(list(args))),
                      returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise RuntimeError("page exception: " + json.dumps(r["exceptionDetails"])[:300])
        return r.get("result", {}).get("value")

    def screenshot(self, clip=None):
        p = {"format": "png"}
        if clip:
            p["clip"] = {"x": clip[0], "y": clip[1], "width": clip[2], "height": clip[3], "scale": 1}
        return base64.b64decode(self.call("Page.captureScreenshot", **p)["data"])

    def move(self, x, y):
        self.call("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)

    def click(self, x, y):
        self.move(x, y)
        for t in ("mousePressed", "mouseReleased"):
            self.call("Input.dispatchMouseEvent", type=t, x=x, y=y, button="left", clickCount=1)

    def _key(self, key, code, vk, text=None):
        d = dict(key=key, code=code, windowsVirtualKeyCode=vk)
        self.call("Input.dispatchKeyEvent", type="keyDown" if text else "rawKeyDown", **d, **({"text": text} if text else {}))
        time.sleep(0.05)
        self.call("Input.dispatchKeyEvent", type="keyUp", **d)

    def type_text(self, s):
        for ch in s:
            k, c, vk = key_info(ch)
            self._key(k, c, vk, text=ch)
            time.sleep(0.05)

    def press(self, name):
        self._key(*KEYS[name])

    def close(self):
        for f in (lambda: self.call("Page.navigate", url="about:blank"), lambda: time.sleep(1),  # pagehide = FAREWELL
                  lambda: self.call("Browser.close")):
            try:
                f()
            except Exception:  # noqa: BLE001
                pass
        try:
            self.p.wait(10)
        except Exception:  # noqa: BLE001
            self.p.kill()
        shutil.rmtree(self.profile, ignore_errors=True)


class Firefox:
    name = "firefox"

    def __init__(self, env, tmp, port=2851, size=(1400, 900)):
        exe = shutil.which("firefox-esr") or shutil.which("firefox")
        if not exe:
            raise RuntimeError("firefox is not installed")
        self.profile = tempfile.mkdtemp(prefix="ff-", dir=tmp)
        prefs = {"browser.startup.homepage_override.mstone": "ignore", "datareporting.policy.firstRunURL": "",
                 "browser.aboutwelcome.enabled": False, "browser.shell.checkDefaultBrowser": False,
                 "marionette.port": port, "startup.homepage_welcome_url": "", "browser.startup.page": 0}
        with open(self.profile + "/user.js", "w") as f:
            for k, v in prefs.items():
                f.write('user_pref("%s", %s);\n' % (k, json.dumps(v)))
        e = dict(env, MOZ_ENABLE_WAYLAND="1")
        self.p = subprocess.Popen([exe, "--marionette", "--no-remote", "--profile", self.profile, "--width", str(size[0]),
                                   "--height", str(size[1])], env=e, stdout=open(self.profile + "/out.log", "wb"),
                                  stderr=subprocess.STDOUT)
        end = time.time() + 60
        while True:
            try:
                self.s = socket.create_connection(("127.0.0.1", port), timeout=120)
                break
            except OSError:
                if time.time() > end:
                    raise RuntimeError("Marionette did not open port %d" % port)
                time.sleep(0.5)
        self.s.settimeout(180)
        self.buf, self.n = b"", 0
        self._read()  # greeting
        caps = self.call("WebDriver:NewSession", {"capabilities": {"alwaysMatch": {"acceptInsecureCerts": True}},
                                                  "acceptInsecureCerts": True})
        self.version = "Firefox " + caps.get("capabilities", {}).get("browserVersion", "?")
        self.call("WebDriver:SetTimeouts", {"script": 60000, "pageLoad": 60000})

    def _read(self):  # frames are "length:json"
        while b":" not in self.buf:
            self.buf += self.s.recv(65536)
        head, rest = self.buf.split(b":", 1)
        while len(rest) < int(head):
            rest += self.s.recv(65536)
        self.buf = rest[int(head):]
        return json.loads(rest[:int(head)])

    def call(self, cmd, params=None):
        self.n += 1
        body = json.dumps([0, self.n, cmd, params or {}]).encode()
        self.s.sendall(str(len(body)).encode() + b":" + body)
        while True:
            m = self._read()
            if isinstance(m, list) and len(m) == 4 and m[0] == 1 and m[1] == self.n:
                if m[2] is not None:
                    raise RuntimeError("%s: %s" % (cmd, json.dumps(m[2])[:400]))
                return m[3]

    def navigate(self, url):
        self.call("WebDriver:Navigate", {"url": url})
        time.sleep(1)

    def js(self, body, *args):
        return self.call("WebDriver:ExecuteScript", {"script": body, "args": list(args)})["value"]

    def screenshot(self, clip=None):  # clip is not used: the whole viewport (the canvas has its own method below)
        return base64.b64decode(self.call("WebDriver:TakeScreenshot", {"full": False})["value"])

    def canvas_shot(self, selector):
        el = self.call("WebDriver:FindElement", {"using": "css selector", "value": selector})["value"]
        return base64.b64decode(self.call("WebDriver:TakeScreenshot", {"id": list(el.values())[0], "full": False})["value"])

    def _actions(self, a):
        self.call("WebDriver:PerformActions", {"actions": a})
        self.call("WebDriver:ReleaseActions")

    def _ptr(self, *steps):
        self._actions([{"type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"}, "actions": list(steps)}])

    def move(self, x, y):
        self._ptr({"type": "pointerMove", "x": int(x), "y": int(y), "origin": "viewport", "duration": 0})

    def click(self, x, y):
        self._ptr({"type": "pointerMove", "x": int(x), "y": int(y), "origin": "viewport", "duration": 0},
                  {"type": "pointerDown", "button": 0}, {"type": "pause", "duration": 60}, {"type": "pointerUp", "button": 0})

    def type_text(self, s):
        for ch in s:
            self._actions([{"type": "key", "id": "kbd", "actions": [{"type": "keyDown", "value": ch},
                                                                     {"type": "pause", "duration": 50},
                                                                     {"type": "keyUp", "value": ch}]}])
            time.sleep(0.05)

    def press(self, name):
        w = {"Escape": ""}[name]
        self._actions([{"type": "key", "id": "kbd", "actions": [{"type": "keyDown", "value": w}, {"type": "keyUp", "value": w}]}])

    def close(self):
        for f in (lambda: self.call("WebDriver:Navigate", {"url": "about:blank"}), lambda: time.sleep(1),
                  lambda: self.call("Marionette:Quit")):
            try:
                f()
            except Exception:  # noqa: BLE001
                pass
        try:
            self.p.wait(15)
        except Exception:  # noqa: BLE001
            self.p.kill()
        shutil.rmtree(self.profile, ignore_errors=True)
