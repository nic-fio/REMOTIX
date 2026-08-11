#!/usr/bin/env python3
"""racc.py — serve la sonda e raccoglie il suo esito.  Banco, non prodotto."""
import json, sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
QUI = Path(__file__).resolve().parent
REG = QUI / "esiti.jsonl"
class H(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw): super().__init__(*a, directory=str(QUI), **kw)
    def do_POST(self):
        if self.path != "/esito":
            self.send_error(404); return
        n = int(self.headers.get("Content-Length", 0))
        try: d = json.loads(self.rfile.read(n).decode("utf-8", "replace"))
        except Exception as e: d = {"esito": "ILLEGGIBILE", "dettaglio": str(e)}
        d["ora"] = datetime.now().isoformat(timespec="seconds")
        with REG.open("a") as f: f.write(json.dumps(d, ensure_ascii=False) + "\n")
        print("=== esito:", d.get("esito"), "|", (d.get("motore") or "?")[:80], flush=True)
        print("    ", d.get("dettaglio"), flush=True)
        for r in (d.get("righe") or []): print("      .", r, flush=True)
        self.send_response(204); self.end_headers()
    def log_message(self, f, *a): print("richiesta:", f % a, flush=True)
if __name__ == "__main__":
    p = int(sys.argv[1]) if len(sys.argv) > 1 else 8898
    print(f"raccoglitore su 127.0.0.1:{p}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", p), H).serve_forever()
