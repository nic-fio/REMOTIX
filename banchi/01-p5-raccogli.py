#!/usr/bin/env python3
"""01-p5-raccogli.py — serve le pagine del punto 5 e ne REGISTRA quel che vedono.

    python3 -u 01-p5-raccogli.py [porta]        predefinita: 8855

===========================================================================
PERCHE' UN TERZO RACCOGLITORE, VISTO CHE B2 E S7 NE HANNO GIA' UNO

Lo stesso mestiere di `01-b2-raccogli.py` e `01-s7-raccogli.py` — B0.4:
*l'atteso lo confronta il banco, non chi legge* — ma **su un registro suo**.

⛔ Non si riusa quello di B2 apposta, ed e' una lezione pagata: `b2-esiti.jsonl`
   e' condiviso fra B2 e B11, e il rilievo **R8.10** racconta per esteso che cosa
   costa un registro condiviso — *«l'ultima riga» smette di voler dire «la riga
   di questa prova»*.  Qui il file e' `01-p5-esiti.jsonl` e nessun altro banco ci
   scrive.

⚠ E dentro **questo** registro convivono due cose (la sonda S3 e il giro contro
  il prodotto): si distinguono per il campo `banco`, e **ogni riga porta il
  `giro`**, che e' un marchio irripetibile prodotto dal lanciatore.  Chi legge
  filtra per `giro`, mai per «le ultime N righe».

===========================================================================
⛔ L'ORA PORTA IL FUSO, E NON E' UN VEZZO

`RCP.md`/`fasi` misurano su due macchine con **due orologi diversi**: questa
stazione e' su **CEST**, il server e' su **UTC** — due ore di scarto `[M]`
11 agosto 2026.  Una riga di registro con un'ora senza fuso mette chi legge
davanti a due letture ugualmente plausibili a due ore di distanza, ed e' la
forma esatta con cui una misura diventa inservibile fra sei mesi.

Qui ogni riga porta **tutt'e tre**:

    ora        ISO 8601 con l'offset locale   2026-08-11T06:51:05+02:00
    ora_utc    la stessa istante in UTC       2026-08-11T04:51:05+00:00
    fuso       il nome della zona             CEST (UTC+02:00)

===========================================================================
⛔ IL DENOMINATORE — `LEZIONI.md` §1.9, quarta regola

Ogni richiesta va su standard error.  *«Nessun esito»* ha due cause opposte —
il browser non ha aperto la pagina, oppure l'ha aperta e non ha spedito — e
senza il registro delle richieste hanno **lo stesso aspetto**.  E' la stessa
riga che il 10 agosto 2026 diceva `pass` in `01-b2-raccogli.py` e ha reso
indistinguibili due difetti.
"""
import json
import os
import sys

from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "01-p5-esiti.jsonl"


def marca_il_tempo(dati):
    """Le tre forme dell'istante, e il bersaglio.  ⛔ Nessuno e' facoltativo.

    ⛔ `bersaglio` e `porta_bersaglio` seguono la convenzione di
       `01-b0-bersaglio.py`: *«un registro che non dice contro quale server ha
       misurato mette in fila numeri di due cose diverse»*, e non ha nessun
       sintomo — i numeri sono tutti buoni, uno per uno.  Li mette il
       lanciatore nell'ambiente; `ignoto` e' un valore legittimo, l'assenza
       del campo no.
    """
    dati.setdefault("bersaglio", os.environ.get("BERSAGLIO", "ignoto"))
    dati.setdefault("porta_bersaglio", os.environ.get("PORTA_BERSAGLIO", "ignota"))
    adesso = datetime.now().astimezone()
    dati["ora"] = adesso.isoformat(timespec="milliseconds")
    dati["ora_utc"] = adesso.astimezone(timezone.utc).isoformat(timespec="milliseconds")
    # ⛔ Il nome della zona si CHIEDE all'istante che stiamo marcando, non alla
    #    tabella globale `time.tzname`: quella ha due voci (con e senza ora
    #    legale) e sceglierla a mano e' il modo di scrivere «CET» in agosto.
    scarto = adesso.strftime("%z")
    dati["fuso"] = f"{adesso.tzname()} (UTC{scarto[:3]}:{scarto[3:]})"
    return dati


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
            # ⛔ Un corpo che non e' JSON NON si butta: si registra com'e'.
            #    «La riga non c'e'» e «la riga c'era ed era storta» sono due
            #    fatti diversi, e il secondo dice dove guardare.
            dati = {"grezzo": corpo, "tipo": "CORPO-NON-JSON"}
        marca_il_tempo(dati)
        with REGISTRO.open("a", encoding="utf-8") as f:
            f.write(json.dumps(dati, ensure_ascii=False) + "\n")
            f.flush()
        print(f"=== {dati['ora']}  banco={dati.get('banco')}  giro={dati.get('giro')}  "
              f"tipo={dati.get('tipo')}  {str(dati.get('nota') or '')[:70]}", flush=True)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def end_headers(self):
        # ⚠ Niente cache: una pagina servita dalla cache farebbe misurare il
        #   giro di prima.  E' la trappola che `01-s1b-eccezione.sh` cura col
        #   `?giro=`, qui curata alla radice perche' il prodotto **non accetta
        #   query string** sulla sua pagina (`pagina.c`: `strcmp(percorso, "/")`).
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def log_message(self, formato, *a):
        sys.stderr.write("richiesta: " + (formato % a) + "\n")
        sys.stderr.flush()


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 8855
    print(f"== punto 5: le pagine stanno su http://127.0.0.1:{porta}/")
    print(f"   il registro si accumula in {REGISTRO}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", porta), Raccoglitore).serve_forever()
