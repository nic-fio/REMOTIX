#!/usr/bin/env python3
"""
18-a1 · chrome — i pacchetti del nuovo `audio.c` dentro un CHROME VERO.

    python3 chrome.py CARTELLA [--porta 7621] [--pagina ../../src/pagina.html]

CARTELLA e' quella dove `costruisci.sh` ha scritto `vecchio.pkt`, `nuovo.pkt`
e `nuovo.f32`.  Si serve `chrome.html` su http://127.0.0.1:PORTA (contesto
sicuro, come la sonda `07-b40`), con il modulo WebAssembly TOLTO DA
`pagina.html` fra i segni `OPUS_WASM_INIZIO`/`OPUS_WASM_FINE` — cioe' il
decodificatore che l'utente ha davvero —, si lancia `google-chrome --headless`
e si aspetta l'esito, che la pagina manda indietro con un POST.

⛔ Non accende il prodotto e non tocca porte d'altri: la porta e' della fase 18,
   linea A (7621-7625), e il server ascolta solo su 127.0.0.1.

Uscita 0 VERDE: niente rifiutato, vecchio e nuovo identici campione per
campione, e vicini alla decodifica nativa del server.

⚠ «Vicini» e non «identici», ed e' misurato: `[M]` 30 set 2026, Chrome 154
  headless sul server, **3 569 330 campioni float su 3 571 200 diversi** dal
  nativo, scarto massimo **1,37e-4** (≈ 4,5 LSB a 16 bit, −77 dBFS).  E' il
  decodificatore compilato due volte (WebAssembly contro x86 con le sue SIMD),
  non il codificatore: vecchio e nuovo nel browser sono identici bit per bit.
  ⇒ La soglia (1e-3) guarda che il decodificatore della pagina resti lo stesso
  algoritmo, non che faccia la stessa aritmetica.
"""
import argparse
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading

QUI = os.path.dirname(os.path.abspath(__file__))

a = argparse.ArgumentParser()
a.add_argument("cartella")
a.add_argument("--porta", type=int, default=7621)
a.add_argument("--pagina", default=os.path.join(QUI, "..", "..", "src", "pagina.html"))
arg = a.parse_args()

testo = open(arg.pagina, encoding="utf-8").read()
m = re.search(r'/\*OPUS_WASM_INIZIO\*/"([A-Za-z0-9+/=]+)"', testo)
if not m:
    print("⛔ NIENTE DA GIUDICARE: in %s non trovo il modulo fra i segni" % arg.pagina)
    sys.exit(2)
WASM_B64 = m.group(1).encode()

esito = {}
pronto = threading.Event()


class Gestore(http.server.BaseHTTPRequestHandler):
    def log_message(self, *x):
        pass

    def _manda(self, corpo, tipo):
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        p = self.path.lstrip("/") or "chrome.html"
        if p == "chrome.html":
            return self._manda(open(os.path.join(QUI, p), "rb").read(), "text/html")
        if p == "wasm.b64":
            return self._manda(WASM_B64, "text/plain")
        if p in ("vecchio.pkt", "nuovo.pkt", "nuovo.f32"):
            return self._manda(open(os.path.join(arg.cartella, p), "rb").read(),
                               "application/octet-stream")
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        esito.update(json.loads(self.rfile.read(n)))
        self._manda(b"ok", "text/plain")
        pronto.set()


socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", arg.porta), Gestore)
threading.Thread(target=srv.serve_forever, daemon=True).start()

chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
if not chrome:
    print("⛔ NIENTE DA GIUDICARE: google-chrome non c'e'")
    sys.exit(2)
profilo = tempfile.mkdtemp(prefix="18-a1-chrome-")
p = subprocess.Popen([chrome, "--headless=new", "--no-first-run",
                      "--no-default-browser-check", "--user-data-dir=" + profilo,
                      "http://127.0.0.1:%d/chrome.html" % arg.porta],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
arrivato = pronto.wait(90)
p.terminate()
try:
    p.wait(10)
except subprocess.TimeoutExpired:
    p.kill()
srv.shutdown()
shutil.rmtree(profilo, ignore_errors=True)

if not arrivato:
    print("⛔ NIENTE DA GIUDICARE: la pagina non ha risposto in 90 s")
    sys.exit(2)
print(json.dumps(esito, indent=2, ensure_ascii=False))
buono = ("errore" not in esito
         and esito["nuovo"]["rifiutati"] == 0 and esito["vecchio"]["rifiutati"] == 0
         and esito["nuovo"]["pacchetti"] == esito["vecchio"]["pacchetti"]
         and esito["diversi_vecchio_nuovo"] == 0
         and esito["massimo_scarto_dal_nativo"] < 1e-3)
print("⭐ VERDE — Chrome decodifica il nuovo come il vecchio, e a un soffio dal nativo del server"
      if buono else "⛔ ROSSO")
sys.exit(0 if buono else 1)
