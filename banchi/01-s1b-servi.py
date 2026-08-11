#!/usr/bin/env python3
"""01-s1b-servi.py — il sito dietro l'avviso, per la misura S1b.

    python3 -u 01-s1b-servi.py <porta> <cartella-certificati>

⚠ GIRA SUL SERVER (192.168.0.2).  ⛔ E NON su `localhost`: `S1 §4.5` punto 3
  dice che Chrome ha una **corsia riservata** per localhost
  (`ssl_manager.cc:290-297`), e una misura fatta li' non rappresenta il caso
  vero.  Va usato un indirizzo privato di rete, da una macchina diversa — che
  e' esattamente la scena di questo progetto: i browser stanno sul portatile,
  il sito qui.

---------------------------------------------------------------------------
CHE COSA FA, E PERCHE' COSI' POCO

Serve **una** pagina in HTTPS con un certificato che nessuno riconosce, e
accetta un POST su `/esito`.  Tutto qui.

⛔ Il POST e' l'unico modo onesto di sapere se l'avviso e' comparso: se la
   pagina viene servita, lo spedisce; se davanti c'e' l'interstiziale del
   browser, la pagina **non gira** e non spedisce niente.  Guardare il
   registro degli accessi non basterebbe — una connessione TLS c'e' anche
   quando l'avviso compare, e «l'avviso c'e'» e «l'avviso non c'e'»
   avrebbero lo stesso aspetto.

⛔ E il POST va alla STESSA origine.  Una pagina in HTTPS non puo' spedire a
   un raccoglitore in HTTP: e' contenuto misto, e il browser lo blocca.  Il
   registro quindi nasce qui, e chi lancia il banco lo legge da qui.
---------------------------------------------------------------------------
"""
import json
import ssl
import sys
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

QUI = Path(__file__).resolve().parent
REGISTRO = QUI / "01-s1b-visite.jsonl"


class Sito(SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=str(QUI), **kw)

    def do_POST(self):
        if self.path != "/esito":
            self.send_error(404)
            return
        n = int(self.headers.get("Content-Length", 0))
        try:
            dati = json.loads(self.rfile.read(n).decode("utf-8", "replace"))
        except Exception:
            dati = {"grezzo": True}
        dati["ora"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with REGISTRO.open("a") as f:
            f.write(json.dumps(dati, ensure_ascii=False) + "\n")
        print("VISITA", json.dumps(dati, ensure_ascii=False), flush=True)
        self.send_response(204)
        self.end_headers()

    def log_message(self, formato, *a):
        # ⛔ Il denominatore: «nessuna visita» ha due cause opposte — il
        #    browser non ha chiesto niente, oppure ha chiesto e si e' fermato
        #    all'avviso.  Solo la seconda e' la misura (`LEZIONI.md` §1.9).
        sys.stderr.write("richiesta: " + (formato % a) + "\n")
        sys.stderr.flush()


if __name__ == "__main__":
    porta = int(sys.argv[1])
    cartella = Path(sys.argv[2])
    contesto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    contesto.load_cert_chain(cartella / "s1b-pagina.pem", cartella / "s1b-pagina.key")
    servitore = ThreadingHTTPServer(("0.0.0.0", porta), Sito)
    servitore.socket = contesto.wrap_socket(servitore.socket, server_side=True)
    print(f"== S1b: sito in HTTPS sulla porta {porta}, certificato in {cartella}", flush=True)
    servitore.serve_forever()
