#!/usr/bin/env python3
"""02-pagina-misura-cdp.py — ⭐ THE READING CHANNEL OF THE MEASUREMENT BENCH.

A minimal CDP (Chrome DevTools Protocol) client, written here instead of taken
from a library: it is an HTTP handshake and four lines of WebSocket
framing, and on this machine there is no `websockets` installed.

    python3 banchi/02-pagina-misura-cdp.py --porta 9222 --stato

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

MAGIA = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"


class Ws:
    """An essential client WebSocket: text, masked, no extensions."""

    def __init__(self, url, timeout=30):
        assert url.startswith("ws://"), url
        resto = url[5:]
        autorita, _, percorso = resto.partition("/")
        host, _, porta = autorita.partition(":")
        self.s = socket.create_connection((host, int(porta or 80)), timeout=10)
        self.s.settimeout(timeout)
        chiave = base64.b64encode(os.urandom(16)).decode()
        richiesta = (
            f"GET /{percorso} HTTP/1.1\r\n"
            f"Host: {autorita}\r\n"
            "Upgrade: websocket\r\nConnection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {chiave}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n")
        self.s.sendall(richiesta.encode())
        testa = b""
        while b"\r\n\r\n" not in testa:
            pezzo = self.s.recv(4096)
            if not pezzo:
                raise RuntimeError("the socket closed during the handshake")
            testa += pezzo
        intestazione, _, avanzo = testa.partition(b"\r\n\r\n")
        if b" 101 " not in intestazione.split(b"\r\n")[0]:
            raise RuntimeError("handshake refused: "
                               + intestazione.split(b"\r\n")[0].decode())
        atteso = base64.b64encode(
            hashlib.sha1((chiave + MAGIA).encode()).digest()).decode()
        # ⛔ The acceptance is CHECKED: without it, any server that
        #    answered 101 would pass for Chrome.
        if atteso.lower() not in intestazione.decode("latin1").lower():
            raise RuntimeError("Sec-WebSocket-Accept does not match")
        self.buf = bytearray(avanzo)
        self.n = 0

    # -- framing ------------------------------------------------------------
    def _leggi(self, quanti):
        while len(self.buf) < quanti:
            pezzo = self.s.recv(65536)
            if not pezzo:
                raise RuntimeError("the socket closed")
            self.buf += pezzo
        fuori = bytes(self.buf[:quanti])
        del self.buf[:quanti]
        return fuori

    def _pezzo(self):
        b0, b1 = self._leggi(2)
        fin = b0 & 0x80
        codice = b0 & 0x0F
        lung = b1 & 0x7F
        if lung == 126:
            lung = struct.unpack(">H", self._leggi(2))[0]
        elif lung == 127:
            lung = struct.unpack(">Q", self._leggi(8))[0]
        corpo = self._leggi(lung)
        return fin, codice, corpo

    def manda(self, testo):
        dati = testo.encode()
        testa = bytearray([0x81])
        n = len(dati)
        if n < 126:
            testa.append(0x80 | n)
        elif n < 65536:
            testa.append(0x80 | 126); testa += struct.pack(">H", n)
        else:
            testa.append(0x80 | 127); testa += struct.pack(">Q", n)
        m = os.urandom(4)
        testa += m
        self.s.sendall(bytes(testa) + bytes(b ^ m[i % 4]
                                            for i, b in enumerate(dati)))

    def ricevi(self):
        pezzi = b""
        while True:
            fin, codice, corpo = self._pezzo()
            if codice == 0x9:               # ping → pong
                self.s.sendall(b"\x8a\x80" + os.urandom(4))
                continue
            if codice == 0x8:
                raise RuntimeError("the browser closed the WebSocket")
            pezzi += corpo
            if fin:
                return pezzi.decode("utf-8", "replace")

    def chiudi(self):
        try:
            self.s.close()
        except OSError:
            pass


class Cdp:
    def __init__(self, url, timeout=40):
        self.ws = Ws(url, timeout)
        self.n = 0

    def chiama(self, metodo, **parametri):
        self.n += 1
        mio = self.n
        self.ws.manda(json.dumps({"id": mio, "method": metodo,
                                  "params": parametri}))
        while True:
            r = json.loads(self.ws.ricevi())
            if r.get("id") != mio:
                continue                     # it is an event: not needed
            if "error" in r:
                raise RuntimeError(metodo + ": " + json.dumps(r["error"]))
            return r.get("result", {})

    def valuta(self, espressione, attendi=True):
        """⛔ `awaitPromise` is on: what the bench reads are promises
        (`SONDAGGIO` is a promise that resolves when the probing is over).  Without it,
        one would read the `Promise` object and say «read» of a value that never
        arrived — the E1 form inside the bench."""
        r = self.chiama("Runtime.evaluate", expression=espressione,
                        returnByValue=True, awaitPromise=attendi)
        if "exceptionDetails" in r:
            return {"⛔ exception": json.dumps(r["exceptionDetails"])[:400]}
        return r.get("result", {}).get("value")

    def chiudi(self):
        self.ws.chiudi()


# ---------------------------------------------------------------------------
def bersagli(porta, attesa=25):
    """Waits for Chrome to open its diagnosis port and returns the targets."""
    fine = time.time() + attesa
    ultimo = None
    while time.time() < fine:
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{porta}/json/list", timeout=3) as r:
                return json.loads(r.read().decode())
        except Exception as e:            # noqa: BLE001 — anything at all: retry
            ultimo = e
            time.sleep(0.5)
    raise RuntimeError(f"the diagnosis port {porta} did not answer within "
                       f"{attesa} s: {ultimo}")


def pagina(porta, attesa=25):
    """The target of type `page`.  ⛔ If there is more than one the first is taken
    AND IT IS SAID: a bench that picked one at random would measure a
    tab different from the one being looked at."""
    fine = time.time() + attesa
    while True:
        elenco = [b for b in bersagli(porta, attesa) if b.get("type") == "page"]
        if elenco:
            if len(elenco) > 1:
                print(f"    ⚠ {len(elenco)} tabs open, taking the first: "
                      f"«{elenco[0].get('title')}»", file=sys.stderr)
            return elenco[0]
        if time.time() > fine:
            raise RuntimeError("no tab open")
        time.sleep(0.5)


# ⛔ THE PHONE PROLOGUE.  It refuses the decoder every configuration
#    beyond the ceiling, in both places where the page queries it:
#    `isConfigSupported` (the filter) and `configure` (the pixel).  ⚠ And it makes them
#    answer CONSISTENTLY: a fake decoder that said «yes» to the
#    filter and threw at `configure` would measure a device that does not
#    exist — and precisely the case in which the page already does not trust the filter.
PROLOGO_TELEFONO = r"""
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
    if "--porta" in sys.argv:
        p = int(sys.argv[sys.argv.index("--porta") + 1])
    b = pagina(p)
    print(json.dumps({"titolo": b.get("title"), "url": b.get("url")},
                     ensure_ascii=False))
