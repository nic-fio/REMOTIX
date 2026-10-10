#!/usr/bin/env python3
"""
18-software-webcodecs.py — phase 18: the fallback stream given to a REAL Chrome
(headless, on the test machine) with `VideoDecoder`, as the page does.

    python3 18-software-webcodecs.py DIR PORT flow:codec [flow:codec …]

DIR holds the streams, their .csv (from the `18-software-confronto` bench) and the
ffmpeg fingerprints (<flow>.ffmpeg.json: the sum of the luma of each
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
        if self.path.startswith("/pagina.html"):
            body_el = open(os.path.join(HERE, "18-software-webcodecs.html"), "rb").read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body_el)))
            self.end_headers()
            self.wfile.write(body_el)
            return
        super().do_GET()

    def do_POST(self):
        from urllib.parse import parse_qs, urlparse
        label_name = parse_qs(urlparse(self.path).query).get("label_name", ["?"])[0]
        n = int(self.headers.get("Content-Length", 0))
        outcomes[label_name] = json.loads(self.rfile.read(n))
        self.send_response(204)
        self.end_headers()


socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.ThreadingTCPServer(("127.0.0.1", PORT), Serve)
threading.Thread(target=srv.serve_forever, daemon=True).start()
profile_v = tempfile.mkdtemp(prefix="f18-chrome-", dir=DIR)
version_v = subprocess.run(["google-chrome", "--version"], capture_output=True, text=True).stdout.strip()
print(f"browser: {version_v} (headless)")

for flow, codec in CASES:
    ref = json.load(open(os.path.join(DIR, flow + ".ffmpeg.json")))
    for hw in ("prefer-software", "no-preference"):
        key_id = f"{flow}.{hw}"
        url = f"http://127.0.0.1:{PORT}/pagina.html?flow={flow}&codec={codec}&hw={hw}"
        p = subprocess.Popen(["google-chrome", "--headless=new", "--no-first-run",
                              "--no-default-browser-check", f"--user-data-dir={profile_v}",
                              "--enable-logging=stderr", "--v=0", url],
                             stdout=subprocess.DEVNULL, stderr=open(os.path.join(profile_v, "chrome.log"), "w"))
        t0 = time.time()
        logbook = os.path.join(profile_v, "chrome.log")
        while key_id not in outcomes and time.time() - t0 < 120:
            time.sleep(0.5)
            for r in open(logbook, errors="replace"):
                if "F18OUTCOME " in r:
                    # the console line: "F18OUTCOME {json}", source: …
                    body_el = r.split("F18OUTCOME ", 1)[1]
                    body_el = body_el[:body_el.rindex("}") + 1].replace('\\"', '"')
                    outcomes[key_id] = json.loads(body_el)
        p.terminate()
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            p.kill()
        e = outcomes.get(key_id)
        if not e:
            line_list = [r.strip()[-160:] for r in open(os.path.join(profile_v, "chrome.log"), errors="replace")
                     if "F18" in r or "CONSOLE" in r]
            print(f"⛔ {flow} [{codec}, {hw}]: no outcome in 120 s · console: {line_list[-4:]}")
            continue
        imp = e.get("fingerprints", [])
        equal = sum(1 for a, b in zip(imp, ref) if a == b)
        print(f"{flow} [{codec}, {hw}]: supported {e['supported']} · {e['outputs']} frames "
              f"from {e.get('chunk')} chunks · {e.get('l')}x{e.get('a')} {e.get('schema')} · errors "
              f"{e['errors'] or 'none'} · luma identical to ffmpeg in {equal} out of {len(ref)}")

srv.shutdown()
shutil.rmtree(profile_v, ignore_errors=True)
