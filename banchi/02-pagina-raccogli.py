#!/usr/bin/env python3
"""02-pagina-raccogli.py — serve la pagina di prova di F2.5 e ne REGISTRA gli esiti.

    python3 -u 02-pagina-raccogli.py [porta]        predefinita: 7515

===========================================================================
⛔ PERCHE' ESISTE, VISTO CHE S5 E S7 NE HANNO GIA' UNO

Lo stesso mestiere di `01-s5-raccogli.py` — B0.4: *l'atteso lo confronta il
banco, non chi legge* — ma con **tre differenze che contano**, e nessuna delle
tre e' un gusto:

 1. ⛔ **Un registro suo, `02-pagina-esiti.jsonl`, e nessun altro banco ci
    scrive.**  Il rilievo R8.10 racconta che cosa costa un registro condiviso:
    «l'ultima riga» smette di voler dire «la riga di questa prova».  Qui morde
    di piu' che altrove, perche' un giro di F2.5 scrive **una quindicina** di
    righe e il banco deve saper dire quali sono del suo giro.

 2. ⛔ **Risponde con una conferma, e la pagina l'aspetta.**  `01-s5-*` usa
    `navigator.sendBeacon`, che e' senza conferma — e la trappola gia' pagata
    di P5 e' esattamente li': *il tracciatore e' cieco su Chrome dentro
    `pagehide`, non esce ne' `sendBeacon` ne' la XHR sincrona, sei giri e zero
    tracce* (`fasi/01-filo-nudo.md`).  Sei colonne a zero che sembravano un
    silenzio del prodotto ed erano il silenzio del **portatore**.  Qui gli
    esiti partono con un `fetch` atteso mentre la scheda e' viva, e il banco
    chiude il browser solo dopo aver letto la riga `FINITO`.

 3. ⭐ **Riceve anche i PIXEL**, su `/pixel`, e li scrive come file PNG.  E'
    la consegna di F2.5 a F2.6 (`PIANO.md` fase 2: *«il fotogramma decodificato
    confrontato con quello catturato.  Non "il programma non e' crollato": i
    pixel»*).  Un banco che porta fuori solo il proprio verdetto obbliga la
    fase dopo a fidarsi; portare fuori i pixel la lascia giudicare.

===========================================================================
⛔ IL DENOMINATORE, e qui morde in un modo suo

Ogni richiesta si scrive su standard error (`LEZIONI.md` §1.9, quarta regola).
«Nessun esito» ha tre cause con lo stesso aspetto:

    a) il browser non ha aperto la pagina        → nessuna richiesta
    b) l'ha aperta e le sequenze non c'erano     → richieste 404 su
                                                   `02-pagina-sequenze/*.json`
    c) l'ha aperta, ha misurato, e l'esito non e' uscito

⛔ Senza il registro delle richieste, `b` viene letta come «il browser non
   decodifica»: un `[M]` falso contro un componente innocente.  Per questo il
   404 sulle sequenze si stampa **in rosso e per esteso**, invece di finire in
   una riga di accesso come tutte le altre.

===========================================================================
⛔ E NON SI SERVE PIU' DI QUEL CHE SERVE

La cartella servita e' `banchi/`, e la porta e' la **7515** — quella assegnata
a F2.5 dal mandato §2.  ⚠ Due banchi sulla stessa porta si fermano a vicenda,
ed e' gia' successo: qui la porta si apre su `127.0.0.1`, non su tutte le
interfacce.
"""
import json
import re
import sys
from base64 import b64decode
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "02-pagina-esiti.jsonl"
PIXEL = QUI / "02-pagina-pixel"
SEQUENZE = QUI / "02-pagina-sequenze"

# ⛔ Un nome di file che arriva dal browser non si usa come nome di file.
#    Non e' una paranoia da server pubblico: e' che un nome storto qui
#    scriverebbe un PNG fuori dalla cartella e il banco non lo troverebbe piu'.
NOME_BUONO = re.compile(r"^[A-Za-z0-9._-]{1,120}\.png$")


class Raccoglitore(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(QUI), **kw)

    # ------------------------------------------------------------------
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
            # ⛔ Un corpo illeggibile si SCRIVE lo stesso: buttarlo
            #    renderebbe «l'esito non e' arrivato» e «l'esito era storto»
            #    la stessa cosa.
            dati = {"tipo": "ILLEGGIBILE", "errore": str(e), "grezzo": grezzo[:2000]}
        dati["ora"] = datetime.now(timezone.utc).isoformat(timespec="milliseconds")
        with REGISTRO.open("a", encoding="utf-8") as f:
            f.write(json.dumps(dati, ensure_ascii=False) + "\n")
        print(f"=== {dati['ora']}  {dati.get('tipo'):10s} "
              f"{dati.get('prova', ''):34s} "
              f"celle {dati.get('celle_giuste', '-')}/{dati.get('celle_attese', '-')} "
              f"fotogrammi {dati.get('fotogrammi_usciti', '-')}", flush=True)
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
        print(f"    pixel: {nome}  ({len(corpo)} byte di dataURL)", flush=True)
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    # ------------------------------------------------------------------
    def end_headers(self):
        # ⚠ `SPECIFICHE.md` §11.5 (rilievo O11) vuole la pagina del prodotto
        #   isolata fra origini, perche' senza le due intestazioni i cronometri
        #   di Firefox e Safari cadono su una griglia da 1 ms.  ⛔ Qui F2.5 non
        #   misura tempi, quindi non servirebbero — ma servirle costa niente e
        #   fa girare il banco nella stessa condizione del prodotto, che e' la
        #   sola forma in cui un banco vale (E10).
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "same-origin")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, formato, *a):
        riga = formato % a
        sys.stderr.write("richiesta: " + riga + "\n")
        if "02-pagina-sequenze/" in riga and " 404 " in riga:
            sys.stderr.write(
                "\033[1;31mNO\033[0m  una SEQUENZA manca: la pagina misurerebbe "
                "«zero fotogrammi» su un flusso che non le e' mai arrivato.\n"
                "        si rimedia con: python3 banchi/02-pagina-sequenze.py\n")
        sys.stderr.flush()


if __name__ == "__main__":
    porta = int(sys.argv[1]) if len(sys.argv) > 1 else 7515
    if not SEQUENZE.is_dir() or not list(SEQUENZE.glob("*.json")):
        print("\033[1;31mNO\033[0m  non c'e' nessuna sequenza in "
              f"{SEQUENZE}: il banco non ha niente da dare al browser.\n"
              "        python3 banchi/02-pagina-sequenze.py",
              file=sys.stderr)
        sys.exit(2)
    print(f"== F2.5: pagina su http://127.0.0.1:{porta}/02-pagina-prova.html")
    print(f"   esiti in {REGISTRO}")
    print(f"   pixel in {PIXEL}", flush=True)
    ThreadingHTTPServer(("127.0.0.1", porta), Raccoglitore).serve_forever()
