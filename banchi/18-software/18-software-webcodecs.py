#!/usr/bin/env python3
"""
18-software-webcodecs.py — phase 18: the fallback stream given to a REAL Chrome
(headless, on the test machine) with `VideoDecoder`, as the page does.

    python3 18-software-webcodecs.py DIR PORTA flusso:codec [flusso:codec …]

DIR holds the streams, their .csv (from the `18-software-confronto` bench) and the
ffmpeg fingerprints (<flusso>.ffmpeg.json: the sum of the luma of each
frame).  For each stream and each `hardwareAcceleration` it opens the page
`18-software-webcodecs.html`, waits for the outcome (the page sends it with a POST)
and compares it frame by frame with ffmpeg.

⚠ It listens ONLY on 127.0.0.1 and on a port that is not the product's (never
  7447/7448), and the Chrome profile is a folder of its own, thrown away at the end.
"""
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time

DIR, PORTA = sys.argv[1], int(sys.argv[2])
CASI = [a.split(":", 1) for a in sys.argv[3:]]
QUI = os.path.dirname(os.path.abspath(__file__))
esiti = {}


class Servo(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=DIR, **k)

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/pagina.html"):
            corpo = open(os.path.join(QUI, "18-software-webcodecs.html"), "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        super().do_GET()

    def do_POST(self):
        from urllib.parse import parse_qs, urlparse
        nome = parse_qs(urlparse(self.path).query).get("nome", ["?"])[0]
        n = int(self.headers.get("Content-Length", 0))
        esiti[nome] = json.loads(self.rfile.read(n))
        self.send_response(204)
        self.end_headers()


socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.ThreadingTCPServer(("127.0.0.1", PORTA), Servo)
threading.Thread(target=srv.serve_forever, daemon=True).start()
profilo = tempfile.mkdtemp(prefix="f18-chrome-", dir=DIR)
versione = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True).stdout.strip()
print(f"browser: {versione} (headless)")

for flusso, codec in CASI:
    rif = json.load(open(os.path.join(DIR, flusso + ".ffmpeg.json")))
    for hw in ("prefer-software", "no-preference"):
        chiave = f"{flusso}.{hw}"
        url = f"http://127.0.0.1:{PORTA}/pagina.html?flusso={flusso}&codec={codec}&hw={hw}"
        p = subprocess.Popen(["google-chrome", "--headless=new", "--no-first-run",
                              "--no-default-browser-check", f"--user-data-dir={profilo}",
                              "--enable-logging=stderr", "--v=0", url],
                             stdout=subprocess.DEVNULL, stderr=open(os.path.join(profilo, "chrome.log"), "w"))
        t0 = time.time()
        registro = os.path.join(profilo, "chrome.log")
        while chiave not in esiti and time.time() - t0 < 120:
            time.sleep(0.5)
            for r in open(registro, errors="replace"):
                if "F18ESITO " in r:
                    # the console line: "F18ESITO {json}", source: …
                    corpo = r.split("F18ESITO ", 1)[1]
                    corpo = corpo[:corpo.rindex("}") + 1].replace('\\"', '"')
                    esiti[chiave] = json.loads(corpo)
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            p.kill()
        e = esiti.get(chiave)
        if not e:
            righe = [r.strip()[-160:] for r in open(os.path.join(profilo, "chrome.log"), errors="replace")
                     if "F18" in r or "CONSOLE" in r]
            print(f"⛔ {flusso} [{codec}, {hw}]: no outcome in 120 s · console: {righe[-4:]}")
            continue
        imp = e.get("impronte", [])
        uguali = sum(1 for a, b in zip(imp, rif) if a == b)
        print(f"{flusso} [{codec}, {hw}]: supported {e['supportato']} · {e['uscite']} frames "
              f"from {e.get('chunk')} chunks · {e.get('l')}x{e.get('a')} {e.get('formato')} · errors "
              f"{e['errori'] or 'none'} · luma identical to ffmpeg in {uguali} out of {len(rif)}")

srv.shutdown()
shutil.rmtree(profilo, ignore_errors=True)
