#!/usr/bin/env python3
"""01-b2-raccogli.py — serves the B2 probe and RECORDS its outcome.

    python3 01-b2-raccogli.py [port]        default: 8899

---------------------------------------------------------------------------
WHY `python3 -m http.server` IS NOT ENOUGH

The probe runs in a browser, and its verdict ended up **in the eyes of whoever
was watching**: someone read it and copied it into the phase document.  ⛔ That
is exactly what rule B0.4 forbids — *the bench compares against the expected,
not the reader* — and phase 0 already paid for it with defect 11, where a
number compared from memory against the wrong column made the bench look
ten frames off.

⚠ And there is a second reason, less obvious and more costly: **the exact
  browser version**.  S1 §4.5 lists it among the errors that ruin a
  measurement — *"a result without a version, six months from now, is worth
  nothing"* — and it is precisely the field a hand transcription always
  forgets.  Here it arrives on its own, because the page sends it.

This program does two things and nothing more:
  1. it serves the bench files on 127.0.0.1;
  2. it accepts a POST on /esito and writes it, with the time, to `b2-esiti.jsonl`.
---------------------------------------------------------------------------
"""
import json
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "b2-esiti.jsonl"


class Raccoglitore(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(QUI), **kw)

    def do_POST(self):
        if self.path != "/esito":
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", 0))
        corpo = self.rfile.read(n).decode("utf-8", "replace")
        try:
            dati = json.loads(corpo)
        except Exception:
            dati = {"grezzo": corpo}
        dati["ora"] = datetime.now().isoformat(timespec="seconds")
        with REGISTRO.open("a") as f:
            f.write(json.dumps(dati, ensure_ascii=False) + "\n")

        # It is also printed on the terminal, so that whoever launches the bench
        # sees the measurement arrive instead of having to go looking for it.
        print(f"\n=== outcome received {dati['ora']}")
        print(f"    outcome: {dati.get('esito')}")
        print(f"    engine:  {dati.get('motore', '?')[:100]}")
        for riga in (dati.get("dettaglio") or "").splitlines():
            print(f"    | {riga}")
        print(flush=True)

        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def log_message(self, formato, *a):
        # ⛔ On 10 Aug 2026 this line said `pass`, with the explanation
        #    "the noise of the requests is not needed: the outcome is".  It was
        #    false, and the first browser measurement proved it: the page
        #    recorded nothing, and there was no way of knowing whether the
        #    browser had **requested** it or not — that is, whether the defect
        #    was in the browser or in the page.  Two opposite causes, the same silence.
        #
        # ⭐ The request IS the denominator of the outcome (`LEZIONI.md` §1.9,
        #    fourth rule): without it, "no outcome" is not a datum.
        sys.stderr.write("request: " + (formato % a) + "\n")
        sys.stderr.flush()


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
    print(f"== bench B2: probe on http://localhost:{porta}/01-b2-sonda.html")
    print(f"   the outcomes accumulate in {REGISTRO}")
    print("   waiting for someone to press the button.\n", flush=True)
    ThreadingHTTPServer(("127.0.0.1", porta), Raccoglitore).serve_forever()
