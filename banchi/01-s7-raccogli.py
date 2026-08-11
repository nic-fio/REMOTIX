#!/usr/bin/env python3
"""01-s7-raccogli.py — serve la pagina di S7 e ne REGISTRA quel che vede.

    python3 -u 01-s7-raccogli.py [porta]        predefinita: 8877

---------------------------------------------------------------------------
PERCHE' ESISTE, VISTO CHE B2 NE HA GIA' UNO

Lo stesso mestiere di `01-b2-raccogli.py` — B0.4: *l'atteso lo confronta il
banco, non chi legge* — ma su un altro registro e un'altra porta.  ⛔ Non si
riusa quello di B2 apposta: `b2-esiti.jsonl` e' gia' condiviso fra B2 e B11, e
il rilievo R8.10 racconta per esteso che cosa costa un registro condiviso —
«l'ultima riga» smette di voler dire «la riga di questa prova».  S7 ha il suo
file, e nessun altro banco ci scrive.

⛔ E QUI IL REGISTRO E' L'UNICO OCCHIO CHE ABBIAMO.  La sessione GNOME di
   questa misura non ha uno schermo: nessuno puo' *guardare* da che parte va
   la pagina.  Quel che la pagina non spedisce non e' successo per nessuno.

---------------------------------------------------------------------------
⛔ IL DENOMINATORE, e in questo banco morde piu' che altrove

Ogni richiesta si scrive su standard error (`LEZIONI.md` §1.9, quarta regola).
«Nessun esito» ha due cause opposte — il browser non ha aperto la pagina,
oppure l'ha aperta e lo scatto non e' arrivato — e senza il registro delle
richieste hanno lo stesso aspetto.  E' la stessa riga che il 10 agosto 2026
diceva `pass` in `01-b2-raccogli.py` e ha reso indistinguibili due difetti.
"""
import json
import sys
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "01-s7-esiti.jsonl"


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
        dati["ora"] = datetime.now().isoformat(timespec="milliseconds")
        with REGISTRO.open("a") as f:
            f.write(json.dumps(dati, ensure_ascii=False) + "\n")
        print(f"=== {dati['ora']}  {dati.get('tipo')}  "
              f"deltaY={dati.get('deltaY')}  scorrimento={dati.get('scorrimento')}", flush=True)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def log_message(self, formato, *a):
        sys.stderr.write("richiesta: " + (formato % a) + "\n")
        sys.stderr.flush()


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8877
    print(f"== S7: pagina su http://127.0.0.1:{porta}/01-s7-pagina.html")
    print(f"   il registro si accumula in {REGISTRO}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", porta), Raccoglitore).serve_forever()
