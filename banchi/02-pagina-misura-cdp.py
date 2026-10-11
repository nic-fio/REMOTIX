#!/usr/bin/env python3
"""02-pagina-misura-cdp.py — ⭐ THE READING CHANNEL OF THE MEASUREMENT BENCH.

A minimal CDP (Chrome DevTools Protocol) client, written here instead of taken
from a library: it is an HTTP handshake and four lines of WebSocket
framing, and on this machine there is no `websockets` installed.

    python3 banchi/02-pagina-misura-cdp.py --port 9222 --stato

⛔ IT IS NOT A SWITCH OF THE PRODUCT, AND THAT IS THE LINE THAT COUNTS.

`src/pagina.html` does not have and must not have a way of handing its outcomes to
a bench: it is the decision of `P2-6` §7 point 1, and it stands.  ⇒ The bench **looks from
outside**, with the same tool used to look at any page —
`Runtime.evaluate` — and reads `window.REMOTIX`, which exists for diagnosis.
⚠ Not one byte of this file enters the product, and the product runs identically
  whether this file is there or not.

⛔⭐ AND THE SECOND THING IT CAN DO IS THE PHONE.

`Page.addScriptToEvaluateOnNewDocument` puts a prologue **before** every
script of the page.  The bench uses it for one thing only: **capping the
decoder**, that is making `VideoDecoder` refuse sizes beyond a ceiling.

⚠ It is exactly what is different on a phone, and it is the only honest
  way to test it on this machine: ⛔ the product is not touched and no fault is
  injected into its source — what changes is **the decoder it has
  underneath**.  A bench that had injected a fault into `pagina.html` would have
  measured the fault, not the phone.
"""
import base64
import hashlib
import json
import os
import socket
import struct
import sys
import time
import urllib.request

MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class Ws:
    """An essential client WebSocket: text, masked, no extensions."""

    def __init__(self, url, timeout=30):
        assert url.startswith("ws://"), url
        rest = url[5:]
        authority, _, fpath = rest.partition("/")
        host, _, port = authority.partition(":")
        self.s = socket.create_connection((host, int(port or 80)), timeout=10)
        self.s.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        request = (
            f"GET /{fpath} HTTP/1.1\r\n"
            f"Host: {authority}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n")
        self.s.sendall(request.encode())
        head = b""
        while b"\r\n\r\n" not in head:
            piece = self.s.recv(4096)
            if not piece:
                raise RuntimeError("the socket closed during the handshake")
            head += piece
        header, _, leftover = head.partition(b"\r\n\r\n")
        if b" 101 " not in header.split(b"\r\n")[0]:
            raise RuntimeError("handshake refused: "
                               + header.split(b"\r\n")[0].decode())
        expected = base64.b64encode(
            hashlib.sha1((key + MAGIC).encode()).digest()).decode()
        # ⛔ The acceptance is CHECKED: without it, any server that
        #    answered 101 would pass for Chrome.
        if expected.lower() not in header.decode("latin1").lower():
            raise RuntimeError("Sec-WebSocket-Accept does not match")
        self.buf = bytearray(leftover)
        self.n = 0

    # -- framing ------------------------------------------------------------
    def _read(self, amount):
        while len(self.buf) < amount:
            piece = self.s.recv(65536)
            if not piece:
                raise RuntimeError("the socket closed")
            self.buf += piece
        report = bytes(self.buf[:amount])
        del self.buf[:amount]
        return report

    def _piece(self):
        b0, b1 = self._read(2)
        fin = b0 & 0x80
        code = b0 & 0x0F
        lung = b1 & 0x7F
        if lung == 126:
            lung = struct.unpack(">H", self._read(2))[0]
        elif lung == 127:
            lung = struct.unpack(">Q", self._read(8))[0]
        body = self._read(lung)
        return fin, code, body

    def send_msg(self, text):
        data = text.encode()
        head = bytearray([0x81])
        n = len(data)
        if n < 126:
            head.append(0x80 | n)
        elif n < 65536:
            head.append(0x80 | 126); head += struct.pack(">H", n)
        else:
            head.append(0x80 | 127); head += struct.pack(">Q", n)
        m = os.urandom(4)
        head += m
        self.s.sendall(bytes(head) + bytes(b ^ m[i % 4]
                                            for i, b in enumerate(data)))

    def receive(self):
        pieces = b""
        while True:
            fin, code, body = self._piece()
            if code == 0x9:               # ping → pong
                self.s.sendall(b"\x8a\x80" + os.urandom(4))
                continue
            if code == 0x8:
                raise RuntimeError("the browser closed the WebSocket")
            pieces += body
            if fin:
                return pieces.decode("utf-8", "replace")

    def close(self):
        try:
            self.s.close()
        except OSError:
            pass


class Cdp:
    def __init__(self, url, timeout=40):
        self.ws = Ws(url, timeout)
        self.n = 0

    def call(self, method, **parameters):
        self.n += 1
        my = self.n
        self.ws.send_msg(json.dumps({"id": my, "method": method,
                                  "params": parameters}))
        while True:
            r = json.loads(self.ws.receive())
            if r.get("id") != my:
                continue                     # it is an event: not needed
            if "error" in r:
                raise RuntimeError(method + ": " + json.dumps(r["error"]))
            return r.get("result", {})

    def evaluate(self, js_expr, should_wait=True):
        """⛔ `awaitPromise` is on: what the bench reads are promises
        (`POLL` is a promise that resolves when the probing is over).  Without it,
        one would read the `Promise` object and say «read» of a value that never
        arrived — the E1 form inside the bench."""
        r = self.call("Runtime.evaluate", expression=js_expr,
                        returnByValue=True, awaitPromise=should_wait)
        if "exceptionDetails" in r:
            return {"⛔ exception": json.dumps(r["exceptionDetails"])[:400]}
        return r.get("result", {}).get("value")

    def close(self):
        self.ws.close()


# ---------------------------------------------------------------------------
def targets(port, wait=25):
    """Waits for Chrome to open its diagnosis port and returns the targets."""
    fine = time.time() + wait
    last = None
    while time.time() < fine:
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{port}/json/list", timeout=3) as r:
                return json.loads(r.read().decode())
        except Exception as e:            # noqa: BLE001 — anything at all: retry
            last = e
            time.sleep(0.5)
    raise RuntimeError(f"the diagnosis port {port} did not answer within "
                       f"{wait} s: {last}")


def page(port, wait=25):
    """The target of type `page`.  ⛔ If there is more than one the first is taken
    AND IT IS SAID: a bench that picked one at random would measure a
    tab different from the one being looked at."""
    fine = time.time() + wait
    while True:
        listing = [b for b in targets(port, wait) if b.get("type") == "page"]
        if listing:
            if len(listing) > 1:
                print(f"    ⚠ {len(listing)} tabs open, taking the first: "
                      f"«{listing[0].get('title')}»", file=sys.stderr)
            return listing[0]
        if time.time() > fine:
            raise RuntimeError("no tab open")
        time.sleep(0.5)


# ⛔ THE PHONE PROLOGUE.  It refuses the decoder every configuration
#    beyond the ceiling, in both places where the page queries it:
#    `isConfigSupported` (the filter) and `configure` (the pixel).  ⚠ And it makes them
#    answer CONSISTENTLY: a fake decoder that said «yes» to the
#    filter and threw at `configure` would measure a device that does not
#    exist — and precisely the case in which the page already does not trust the filter.
PHONE_PROLOGUE = r"""
(function () {
  if (typeof VideoDecoder === "undefined") return;
  const TETTO_L = %d, TETTO_A = %d;
  const dentro = (c) => !c || ((c.codedWidth || 0) <= TETTO_L &&
                               (c.codedHeight || 0) <= TETTO_A);
  const vero = VideoDecoder;
  const veroIs = VideoDecoder.isConfigSupported.bind(VideoDecoder);
  class Incappucciato extends vero {
    configure(c) {
      if (!dentro(c))
        throw new DOMException("bench: the fake decoder stops at " +
                               TETTO_L + "x" + TETTO_A, "NotSupportedError");
      return super.configure(c);
    }
  }
  Incappucciato.isConfigSupported = async function (c) {
    if (!dentro(c)) return { supported: false, config: c };
    return await veroIs(c);
  };
  window.VideoDecoder = Incappucciato;
  window.__BANCO_TETTO__ = TETTO_L + "x" + TETTO_A;
})();
"""


if __name__ == "__main__":
    p = 9222
    if "--port" in sys.argv:
        p = int(sys.argv[sys.argv.index("--port") + 1])
    b = page(p)
    print(json.dumps({"title": b.get("title"), "url": b.get("url")},
                     ensure_ascii=False))
