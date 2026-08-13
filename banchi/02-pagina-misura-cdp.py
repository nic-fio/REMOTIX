#!/usr/bin/env python3
"""02-pagina-misura-cdp.py — ⭐ IL CANALE DI LETTURA DEL BANCO DELLE MISURE.

Un cliente CDP (Chrome DevTools Protocol) minimo, scritto qui invece che preso
da una libreria: sono un handshake HTTP e quattro righe di inquadratura
WebSocket, e su questa macchina non c'e' nessun `websockets` installato.

    python3 banchi/02-pagina-misura-cdp.py --porta 9222 --stato

⛔ NON E' UN INTERRUTTORE DEL PRODOTTO, ED E' LA RIGA CHE CONTA.

`src/pagina.html` non ha e non deve avere un modo di consegnare i propri esiti a
un banco: e' la decisione di `P2-6` §7 punto 1, e resta.  ⇒ Il banco **guarda da
fuori**, con lo stesso strumento con cui si guarda una pagina qualunque —
`Runtime.evaluate` — e legge `window.REMOTIX`, che esiste per la diagnosi.
⚠ Nessun byte di questo file entra nel prodotto, e il prodotto gira identico
  che questo file ci sia o no.

⛔⭐ E LA SECONDA COSA CHE SA FARE E' IL TELEFONO.

`Page.addScriptToEvaluateOnNewDocument` mette un prologo **prima** di ogni
script della pagina.  Il banco lo usa per una cosa sola: **incappucciare il
decodificatore**, cioe' far rifiutare a `VideoDecoder` le misure oltre un tetto.

⚠ E' esattamente quel che e' diverso su un telefono, ed e' la sola forma
  onesta di provarlo su questa macchina: ⛔ non si tocca il prodotto e non si
  innesta un guasto nel suo sorgente — si cambia **il decodificatore che ha
  sotto**.  Un banco che avesse innestato un guasto in `pagina.html` avrebbe
  misurato il guasto, non il telefono.
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
    """Un WebSocket cliente essenziale: testo, mascherato, senza estensioni."""

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
                raise RuntimeError("il socket si e' chiuso durante l'handshake")
            testa += pezzo
        intestazione, _, avanzo = testa.partition(b"\r\n\r\n")
        if b" 101 " not in intestazione.split(b"\r\n")[0]:
            raise RuntimeError("handshake rifiutato: "
                               + intestazione.split(b"\r\n")[0].decode())
        atteso = base64.b64encode(
            hashlib.sha1((chiave + MAGIA).encode()).digest()).decode()
        # ⛔ Si VERIFICA l'accettazione: senza, un server qualunque che
        #    rispondesse 101 passerebbe per Chrome.
        if atteso.lower() not in intestazione.decode("latin1").lower():
            raise RuntimeError("Sec-WebSocket-Accept non torna")
        self.buf = bytearray(avanzo)
        self.n = 0

    # -- inquadratura -------------------------------------------------------
    def _leggi(self, quanti):
        while len(self.buf) < quanti:
            pezzo = self.s.recv(65536)
            if not pezzo:
                raise RuntimeError("il socket si e' chiuso")
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
                raise RuntimeError("il browser ha chiuso il WebSocket")
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
                continue                     # e' un evento: non serve
            if "error" in r:
                raise RuntimeError(metodo + ": " + json.dumps(r["error"]))
            return r.get("result", {})

    def valuta(self, espressione, attendi=True):
        """⛔ `awaitPromise` e' acceso: quel che il banco legge sono promesse
        (`SONDAGGIO` e' una promessa che si risolve a sondaggio finito).  Senza,
        si leggerebbe l'oggetto `Promise` e si direbbe «letto» di un valore mai
        arrivato — la forma E1 dentro il banco."""
        r = self.chiama("Runtime.evaluate", expression=espressione,
                        returnByValue=True, awaitPromise=attendi)
        if "exceptionDetails" in r:
            return {"⛔ eccezione": json.dumps(r["exceptionDetails"])[:400]}
        return r.get("result", {}).get("value")

    def chiudi(self):
        self.ws.chiudi()


# ---------------------------------------------------------------------------
def bersagli(porta, attesa=25):
    """Aspetta che Chrome apra la sua porta di diagnosi e torna i bersagli."""
    fine = time.time() + attesa
    ultimo = None
    while time.time() < fine:
        try:
            with urllib.request.urlopen(
                    f"http://127.0.0.1:{porta}/json/list", timeout=3) as r:
                return json.loads(r.read().decode())
        except Exception as e:            # noqa: BLE001 — qualunque cosa: si riprova
            ultimo = e
            time.sleep(0.5)
    raise RuntimeError(f"la porta di diagnosi {porta} non ha risposto in "
                       f"{attesa} s: {ultimo}")


def pagina(porta, attesa=25):
    """Il bersaglio di tipo `page`.  ⛔ Se ce n'e' piu' d'uno si prende il
    primo E LO SI DICE: un banco che ne scegliesse uno a caso misurerebbe una
    scheda diversa da quella che si sta guardando."""
    fine = time.time() + attesa
    while True:
        elenco = [b for b in bersagli(porta, attesa) if b.get("type") == "page"]
        if elenco:
            if len(elenco) > 1:
                print(f"    ⚠ {len(elenco)} schede aperte, prendo la prima: "
                      f"«{elenco[0].get('title')}»", file=sys.stderr)
            return elenco[0]
        if time.time() > fine:
            raise RuntimeError("nessuna scheda aperta")
        time.sleep(0.5)


# ⛔ IL PROLOGO DEL TELEFONO.  Rifiuta al decodificatore ogni configurazione
#    oltre il tetto, in tutt'e due i posti in cui la pagina lo interroga:
#    `isConfigSupported` (il filtro) e `configure` (il pixel).  ⚠ E li fa
#    rispondere in modo COERENTE: un finto decodificatore che dicesse «si» al
#    filtro e lanciasse a `configure` misurerebbe un dispositivo che non
#    esiste — e proprio il caso in cui la pagina non si fida gia' del filtro.
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
        throw new DOMException("banco: il decodificatore finto si ferma a " +
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
