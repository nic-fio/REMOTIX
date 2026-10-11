#!/usr/bin/env python3
"""
18-a1 · chrome — the packets of the new `audio.c` inside a REAL CHROME.

    python3 chrome.py CARTELLA [--port 7621] [--page ../../src/pagina.html]

CARTELLA is the folder where `costruisci.sh` wrote `vecchio.pkt`, `nuovo.pkt`
and `nuovo.f32`.  `chrome.html` is served on http://127.0.0.1:PORTA (secure
context, like the `07-b40` probe), with the WebAssembly module TAKEN FROM
`pagina.html` between the markers `OPUS_WASM_INIZIO`/`OPUS_WASM_FINE` — that is the
decoder the user really has —, `google-chrome --headless` is launched
and we wait for the outcome, which the page sends back with a POST.

⛔ It does not start the product and does not touch other people's ports: the port
   belongs to phase 18, line A (7621-7625), and the server listens only on 127.0.0.1.

Exit 0 VERDE: nothing refused, old and new identical sample by
sample, and close to the server's native decoding.

⚠ "Close" and not "identical", and it is measured: `[M]` 30 Sep 2026, Chrome 154
  headless on the server, **3 569 330 float samples out of 3 571 200 different** from
  native, maximum deviation **1.37e-4** (≈ 4.5 LSB at 16 bit, −77 dBFS).  It is the
  decoder compiled twice (WebAssembly versus x86 with its SIMD),
  not the encoder: old and new in the browser are identical bit for bit.
  ⇒ The threshold (1e-3) checks that the page's decoder stays the same
  algorithm, not that it does the same arithmetic.
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

HERE = os.path.dirname(os.path.abspath(__file__))

a = argparse.ArgumentParser()
a.add_argument("folder")
a.add_argument("--port", type=int, default=7621)
a.add_argument("--page", default=os.path.join(HERE, "..", "..", "src", "pagina.html"))
arg = a.parse_args()

text = open(arg.page, encoding="utf-8").read()
m = re.search(r'/\*OPUS_WASM_INIZIO\*/"([A-Za-z0-9+/=]+)"', text)
if not m:
    print("⛔ NOTHING TO JUDGE: in %s I cannot find the module between the markers" % arg.page)
    sys.exit(2)
WASM_B64 = m.group(1).encode()

outcome = {}
ready = threading.Event()


class Manager(http.server.BaseHTTPRequestHandler):
    def log_message(self, *x):
        pass

    def _send(self, body, kind):
        self.send_response(200)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        p = self.path.lstrip("/") or "chrome.html"
        if p == "chrome.html":
            return self._send(open(os.path.join(HERE, p), "rb").read(), "text/html")
        if p == "wasm.b64":
            return self._send(WASM_B64, "text/plain")
        if p in ("vecchio.pkt", "nuovo.pkt", "nuovo.f32"):
            return self._send(open(os.path.join(arg.folder, p), "rb").read(),
                               "application/octet-stream")
        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        outcome.update(json.loads(self.rfile.read(n)))
        self._send(b"ok", "text/plain")
        ready.set()


socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("127.0.0.1", arg.port), Manager)
threading.Thread(target=srv.serve_forever, daemon=True).start()

chrome = shutil.which("google-chrome") or shutil.which("google-chrome-stable")
if not chrome:
    print("⛔ NOTHING TO JUDGE: google-chrome is not there")
    sys.exit(2)
profile = tempfile.mkdtemp(prefix="18-a1-chrome-")
p = subprocess.Popen([chrome, "--headless=new", "--no-first-run",
                      "--no-default-browser-check", "--user-data-dir=" + profile,
                      "http://127.0.0.1:%d/chrome.html" % arg.port],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
arrived = ready.wait(90)
p.terminate()
try:
    p.wait(10)
except subprocess.TimeoutExpired:
    p.kill()
srv.shutdown()
shutil.rmtree(profile, ignore_errors=True)

if not arrived:
    print("⛔ NOTHING TO JUDGE: the page did not answer within 90 s")
    sys.exit(2)
print(json.dumps(outcome, indent=2, ensure_ascii=False))
good = ("error" not in outcome
         and outcome["new"]["refused"] == 0 and outcome["vecchio"]["refused"] == 0
         and outcome["new"]["packets"] == outcome["vecchio"]["packets"]
         and outcome["diversi_vecchio_nuovo"] == 0
         and outcome["massimo_scarto_dal_nativo"] < 1e-3)
print("⭐ VERDE — Chrome decodes the new one like the old one, and a whisker away from the server's native"
      if good else "⛔ ROSSO")
sys.exit(0 if good else 1)
