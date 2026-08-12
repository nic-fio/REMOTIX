#!/usr/bin/env python3
"""02-giudizio-raccogli.py — il raccoglitore della sonda F2.6, in HTTPS.

    python3 02-giudizio-raccogli.py <porta> <cert.pem> <chiave.pem> <cartella>

===========================================================================
⛔ PERCHE' E' IN HTTPS, E NON E' UNA PRECAUZIONE

`WebCodecs` **non esiste** fuori da un contesto sicuro, e nemmeno la lettura
della tela con `getImageData` su risorse d'altra origine.  Una sonda servita
in HTTP semplice non misurerebbe «un po' meno»: non partirebbe, e chi legge
concluderebbe che il telefono non sa decodificare.  ⛔ Sarebbe un `[M]` falso
prodotto dal banco, che in questo progetto costa piu' di una misura mancante.

⛔ E la porta e' la **7516**, che e' quella di F2.6.  Due banchi sulla stessa
porta si fermano a vicenda, ed e' gia' successo (`MANDATO` §4).

===========================================================================
⛔ CHE COSA RACCOGLIE, E PERCHE' DUE STRADE INVECE DI UNA

  POST /esito   una riga JSON — i numeri della sonda.  Si accumulano in
                `02-giudizio-sonda.jsonl`.
  POST /pixel   ⭐ **i pixel veri**, letti dalla tela con `getImageData` e
                spediti come RGB grezzo.  Diventano il file `pagina-*.rgb24`
                che `02-giudizio-metro.py` giudica.
                ⇒ **il confronto dei pixel si chiude SUL DISPOSITIVO VERO**,
                non su un browser di comodo: e' la meta' (a) di F2.6 che si
                incontra con la meta' (b) nello stesso giro.

⛔ E il canale di lettura ha un controllo positivo, che e' il piu' importante
   di tutto il file: `POST /prova` scrive nel registro un gettone che lo
   script sa rileggere.  Senza, «il telefono non ha risposto» e «il
   raccoglitore non scrive» hanno lo stesso aspetto — ed e' il buco A27 di
   `01-s1b-eccezione.sh`, che li' e' stato pagato su un orologio da sette
   giorni.
===========================================================================
"""
import datetime
import json
import os
import ssl
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

CARTELLA = "."
REGISTRO = "02-giudizio-sonda.jsonl"


class Servo(BaseHTTPRequestHandler):
    # ⛔ HTTP/1.1 e Content-Length su OGNI risposta.  Senza, la connessione si
    #    chiude senza dire quanto era lunga la risposta e `curl` esce con 56
    #    («Recv failure») su una scrittura che era **riuscita**: il controllo
    #    positivo del canale direbbe «rotto» a canale sano, cioe' un rosso
    #    della ragione sbagliata.  Trovato al primo giro, 12 agosto 2026.
    protocol_version = "HTTP/1.1"

    def _testa(self, codice, tipo="text/plain; charset=utf-8", lunghezza=0):
        self.send_response(codice)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(lunghezza))
        # ⛔ senza queste due la pagina non e' isolata e `getImageData` su
        #    fotogrammi decodificati puo' essere negato dal browser: una tela
        #    «sporcata» non si rilegge, e il confronto dei pixel non esiste.
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()

    def do_GET(self):                            # noqa: N802
        p = urlparse(self.path).path.lstrip("/")
        if p in ("", "/"):
            p = "02-giudizio-pagina.html"
        percorso = os.path.join(CARTELLA, os.path.basename(p))
        if not os.path.isfile(percorso):
            corpo = ("non c'e': %s\n" % percorso).encode()
            self._testa(404, lunghezza=len(corpo))
            self.wfile.write(corpo)
            return
        tipi = {".html": "text/html; charset=utf-8", ".json": "application/json",
                ".js": "text/javascript", ".h265": "application/octet-stream",
                ".bin": "application/octet-stream"}
        est = os.path.splitext(percorso)[1]
        with open(percorso, "rb") as f:
            corpo = f.read()
        self._testa(200, tipi.get(est, "application/octet-stream"), len(corpo))
        self.wfile.write(corpo)

    def do_POST(self):                           # noqa: N802
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", "0"))
        corpo = self.rfile.read(n) if n else b""
        ora = datetime.datetime.now().isoformat(timespec="seconds")

        if u.path == "/pixel":
            q = parse_qs(u.query)
            nome = os.path.basename(q.get("nome", ["pagina"])[0])
            fuori = os.path.join(CARTELLA, nome)
            with open(fuori, "wb") as f:
                f.write(corpo)
            riga = {"ora": ora, "tipo": "pixel", "nome": nome,
                    "byte": len(corpo), "ua": self.headers.get("User-Agent", "")}
        else:
            try:
                d = json.loads(corpo.decode("utf-8") or "{}")
            except Exception as e:               # noqa: BLE001
                d = {"⛔ corpo illeggibile": str(e),
                     "grezzo": corpo[:200].decode("latin1")}
            riga = {"ora": ora, "tipo": "prova" if u.path == "/prova" else "esito",
                    "ua": self.headers.get("User-Agent", ""), "dati": d}

        with open(os.path.join(CARTELLA, REGISTRO), "a") as f:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())
        self._testa(200, lunghezza=6)
        self.wfile.write(b"preso\n")

    def log_message(self, fmt, *a):
        # ⛔ Il registro va sullo stderr, e NON si butta: se il telefono non
        #    arriva alla pagina, la riga che manca qui e' la prima diagnosi.
        sys.stderr.write("%s  %s\n" % (self.address_string(), fmt % a))


def main():
    global CARTELLA
    if len(sys.argv) < 5:
        print(__doc__)
        return 2
    porta, cert, chiave, CARTELLA = int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ctx.load_cert_chain(cert, chiave)
    srv = HTTPServer(("0.0.0.0", porta), Servo)
    srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
    sys.stderr.write("raccoglitore F2.6 su https://0.0.0.0:%d  cartella %s\n"
                     % (porta, CARTELLA))
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
