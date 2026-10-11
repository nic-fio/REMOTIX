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

DIR, PORT = sys.argv[1], int(sys.argv[2])
CASES = [a.split(":", 1) for a in sys.argv[3:]]
HERE = os.path.dirname(os.path.abspath(__file__))
outcomes = {}


class Serve(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=DIR, **k)

    def log_message(self, *a):
        pass

    def do_GET(self):
        if self.path.startswith("/page.html"):
            body = open(os.path.join(HERE, "18-software-webcodecs.html"), "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        super().do_GET()

    def do_POST(self):
        from urllib.parse import parse_qs, urlparse
        name = parse_qs(urlparse(self.path).query).get("name", ["?"])[0]
        n = int(self.headers.get("Content-Length", 0))
        outcomes[name] = json.loads(self.rfile.read(n))
        self.send_response(204)
        self.end_headers()


socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Serve)
threading.Thread(target=srv.serve_forever, daemon=True).start()
profile = tempfile.mkdtemp(prefix="f18-chrome-", dir=DIR)
version = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True).stdout.strip()
print(f"browser: {version} (headless)")

for stream, codec in CASES:
    ref = json.load(open(os.path.join(DIR, stream + ".ffmpeg.json")))
    for hw in ("prefer-software", "no-preference"):
        key = f"{stream}.{hw}"
        url = f"http://127.0.0.1:{PORT}/pagina.html?stream={stream}&codec={codec}&hw={hw}"
        p = subprocess.Popen(["google-chrome", "--headless=new", "--no-first-run",
                              "--no-default-browser-check", f"--user-data-dir={profile}",
                              "--enable-logging=stderr", "--v=0", url],
                             stdout=subprocess.DEVNULL, stderr=open(os.path.join(profile, "chrome.log"), "w"))
        t0 = time.time()
        log = os.path.join(profile, "chrome.log")
        while key not in outcomes and time.time() - t0 < 120:
            time.sleep(0.5)
            for r in open(log, errors="replace"):
                if "F18ESITO " in r:
                    # the console line: "F18ESITO {json}", source: …
                    body = r.split("F18ESITO ", 1)[1]
                    body = body[:body.rindex("}") + 1].replace('\\"', '"')
                    outcomes[key] = json.loads(body)
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            p.kill()
        e = outcomes.get(key)
        if not e:
            lines = [r.strip()[-160:] for r in open(os.path.join(profile, "chrome.log"), errors="replace")
                     if "F18" in r or "CONSOLE" in r]
            print(f"⛔ {stream} [{codec}, {hw}]: no outcome in 120 s · console: {lines[-4:]}")
            continue
        imp = e.get("fingerprints", [])
        equal = sum(1 for a, b in zip(imp, ref) if a == b)
        print(f"{stream} [{codec}, {hw}]: supported {e['supported']} · {e['outputs']} frames "
              f"from {e.get('chunk')} chunks · {e.get('l')}x{e.get('a')} {e.get('format')} · errors "
              f"{e['errors'] or 'none'} · luma identical to ffmpeg in {equal} out of {len(ref)}")

srv.shutdown()
shutil.rmtree(profile, ignore_errors=True)
