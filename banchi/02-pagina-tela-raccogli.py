#!/usr/bin/env python3
"""02-pagina-tela-raccogli.py — serve la pagina del cambio di tela e ne registra
gli esiti.

    python3 -u 02-pagina-tela-raccogli.py [porta]      predefinita: 7533

⛔ PERCHE' NON RIUSA `02-pagina-raccogli.py`, che fa lo stesso mestiere

Per una ragione sola, ed e' la stessa che ha fatto nascere quello: **il registro
non si condivide**.  `02-pagina-esiti.jsonl` e' la consegna di F2.5 a F2.6, e
mescolarci trenta righe di un'altra domanda vorrebbe dire che «le righe di
F2.5» smette di essere una cosa che si puo' chiedere al file (rilievo R8.10,
ripagato da S7).  Qui il registro e' `02-pagina-tela-esiti.jsonl`, e nessun
altro banco ci scrive.

⛔ La porta e' la **7533**, quella assegnata a questo giro — non la 7515 di
   F2.5, che potrebbe girare nello stesso momento: due banchi sulla stessa
   porta si fermano a vicenda, ed e' gia' successo.

⛔ IL DENOMINATORE: ogni richiesta si scrive su standard error.  «Nessun esito»
   ha tre cause con lo stesso aspetto — il browser che non apre la pagina · le
   sequenze che mancano (404) · la misura fatta e l'esito non uscito — e senza
   il conto delle richieste la seconda viene letta come la prima, cioe' un `[M]`
   falso contro il browser.
"""
import json
import re
import sys
from base64 import b64decode
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "02-pagina-tela-esiti.jsonl"
PIXEL = QUI / "02-pagina-tela-pixel"
SEQUENZE = QUI / "02-pagina-tela-sequenze"

NOME_BUONO = re.compile(r"^[A-Za-z0-9._-]{1,120}\.png$")


class Raccoglitore(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(QUI), **kw)

    def do_POST(self):
        if self.path == "/esito":
            return self._esito()
        if self.path.startswith("/pixel"):
            return self._pixel()
        self.send_error(404, "qui non si posta niente")

    def _corpo(self):
        n = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(n)

    def _esito(self):
        grezzo = self._corpo().decode("utf-8", "replace")
        try:
            dati = json.loads(grezzo)
        except Exception as e:
            # ⛔ Un corpo illeggibile si scrive lo stesso: buttarlo renderebbe
            #    «non e' arrivato» e «era storto» la stessa cosa.
            dati = {"tipo": "ILLEGGIBILE", "errore": str(e), "grezzo": grezzo[:2000]}
        dati["ora"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        with REGISTRO.open("a", encoding="utf-8") as f:
            f.write(json.dumps(dati, ensure_ascii=False) + "\n")
        print(f"=== {dati.get('tipo'):10s} {dati.get('caso', dati.get('prova','')):38s} "
              f"{dati.get('esito', '')}", flush=True)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def _pixel(self):
        from urllib.parse import urlparse, parse_qs
        nome = (parse_qs(urlparse(self.path).query).get("nome") or [""])[0]
        if not NOME_BUONO.match(nome):
            print(f"\033[1;31mNO\033[0m  nome di PNG rifiutato: {nome!r}",
                  file=sys.stderr, flush=True)
            self.send_error(400, "nome di file non accettabile")
            return
        corpo = self._corpo().decode("ascii", "replace")
        marca = "data:image/png;base64,"
        if not corpo.startswith(marca):
            self.send_error(400, "atteso un dataURL PNG")
            return
        PIXEL.mkdir(exist_ok=True)
        (PIXEL / nome).write_bytes(b64decode(corpo[len(marca):]))
        print(f"    pixel: {nome}", flush=True)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, formato, *a):
        riga = formato % a
        sys.stderr.write("richiesta: " + riga + "\n")
        if "02-pagina-tela-sequenze/" in riga and " 404 " in riga:
            sys.stderr.write(
                "\033[1;31mNO\033[0m  una SEQUENZA manca: la pagina misurerebbe "
                "«zero fotogrammi» su un flusso mai arrivato.\n"
                "        python3 banchi/02-pagina-tela-sequenze.py\n")
        sys.stderr.flush()


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 7533
    if not SEQUENZE.is_dir() or len(list(SEQUENZE.glob("*.json"))) != 4:
        print("\033[1;31mNO\033[0m  servono le 4 sequenze in "
              f"{SEQUENZE}.\n        python3 banchi/02-pagina-tela-sequenze.py",
              file=sys.stderr)
        sys.exit(2)
    print(f"== pagina su http://127.0.0.1:{porta}/02-pagina-tela-prova.html")
    print(f"   esiti in {REGISTRO}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", porta), Raccoglitore).serve_forever()
