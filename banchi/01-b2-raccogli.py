#!/usr/bin/env python3
"""01-b2-raccogli.py — serve la sonda di B2 e ne REGISTRA l'esito.

    python3 01-b2-raccogli.py [porta]        predefinita: 8899

---------------------------------------------------------------------------
PERCHE' NON BASTA `python3 -m http.server`

La sonda gira in un browser, e il suo verdetto finiva **negli occhi di chi
guardava**: qualcuno lo leggeva e lo ricopiava nel documento di fase.  ⛔ E'
esattamente quel che la regola B0.4 vieta — *l'atteso lo confronta il banco,
non chi legge* — e la fase 0 l'ha gia' pagato con il difetto 11, dove un
numero confrontato a memoria con la colonna sbagliata faceva sembrare il
banco in errore di dieci fotogrammi.

⚠ E c'e' un secondo motivo, meno ovvio e piu' caro: **la versione esatta del
  browser**.  S1 §4.5 la mette fra gli errori che rovinano la misura — *«un
  risultato senza versione, fra sei mesi, non vale niente»* — ed e'
  precisamente il campo che una trascrizione a mano dimentica sempre.  Qui
  arriva da sola, perche' la manda la pagina.

Questo programma fa due cose e nessuna di piu':
  1. serve i file del banco su 127.0.0.1;
  2. accetta un POST su /esito e lo scrive, con l'ora, in `b2-esiti.jsonl`.
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

        # Si stampa anche a terminale, perche' chi lancia il banco veda
        # arrivare la misura invece di doverla andare a cercare.
        print(f"\n=== esito ricevuto {dati['ora']}")
        print(f"    esito:   {dati.get('esito')}")
        print(f"    motore:  {dati.get('motore', '?')[:100]}")
        for riga in (dati.get("dettaglio") or "").splitlines():
            print(f"    | {riga}")
        print(flush=True)

        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def log_message(self, formato, *a):
        # ⛔ Il 10 agosto 2026 questa riga diceva `pass`, con la spiegazione
        #    «il rumore delle richieste non serve: serve l'esito».  Era falsa,
        #    e l'ha dimostrato la prima misura col browser: la pagina non
        #    registrava niente, e non c'era modo di sapere se il browser
        #    l'avesse **chiesta** o no — cioe' se il difetto fosse nel browser
        #    o nella pagina.  Due cause opposte, lo stesso silenzio.
        #
        # ⭐ La richiesta E' il denominatore dell'esito (`LEZIONI.md` §1.9,
        #    quarta regola): senza, «nessun esito» non e' un dato.
        sys.stderr.write("richiesta: " + (formato % a) + "\n")
        sys.stderr.flush()


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8899
    print(f"== banco B2: sonda su http://localhost:{porta}/01-b2-sonda.html")
    print(f"   gli esiti si accumulano in {REGISTRO}")
    print("   in attesa che qualcuno prema il bottone.\n", flush=True)
    ThreadingHTTPServer(("127.0.0.1", porta), Raccoglitore).serve_forever()
