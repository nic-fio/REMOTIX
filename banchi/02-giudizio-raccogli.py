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

⛔ E **anche le letture finiscono nel registro**, con il codice: vedi il
   riquadro D16 qui sotto.  Senza, un 404 sul flusso vive solo nello stderr,
   e il verdetto il registro lo legge dal JSONL.

===========================================================================
⛔ I DUE DIFETTI CURATI IL 12 AGOSTO 2026 A SERA, DOPO DIECI MINUTI
   DELL'UTENTE SPESI A SCOPRIRLI

**D16 — il 404 che nessun verdetto poteva vedere.**  La pagina chiedeva
`/flusso-<giro>.json`, il server rispondeva **404**, e la riga finiva solo
nello stderr.  Il registro JSONL — quello che `analizza` legge — non ne
sapeva niente.  ⇒ «il dispositivo non e' arrivato» e «il dispositivo e'
arrivato e non aveva niente da decodificare» avevano la **stessa faccia**:
forma **E8** (`REVIEWER.md` §2).  ⇒ Ora **ogni GET** e' una riga del registro,
col percorso e col codice.

**D17 — il registro non portava l'INDIRIZZO.**  Portava lo `User-Agent`, che
su Chrome per Android in **Samsung DeX** dice `X11; Linux x86_64` ed e'
indistinguibile da un desktop.  L'indirizzo — **192.168.0.24**, ne' il
portatile ne' il server — c'era, nello stderr, e nessuno lo guardava.
⇒ Ora ogni riga porta `ip`, ed e' l'unico segnale che il browser **non puo'
scrivere**: e' la difesa E10 di `02-giudizio-dispositivo.py`.

===========================================================================
⚠ E LA MODALITA' IN CHIARO — `cert` = «-», e SOLO su 127.0.0.1

Serve a **una** cosa: certificare il banco su questa macchina senza chiedere a
un browser di accettare un certificato che non e' suo.  `http://127.0.0.1` e'
un **contesto sicuro** per specifica, quindi `WebCodecs` e `getImageData`
funzionano identici.  ⛔ Non e' una scorciatoia per il telefono: dal telefono
127.0.0.1 non esiste, e li' serve l'HTTPS.  Percio' in chiaro si ascolta
**solo** sul loopback — un banco in chiaro sulla rete di casa sarebbe una
sonda che non parte, cioe' un `[M]` falso contro il dispositivo.
==========================================================================="""
import datetime
import json
import os
import ssl
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

CARTELLA = "."
REGISTRO = os.environ.get("REGISTRO_SONDA", "02-giudizio-sonda.jsonl")


PENNA = threading.Lock()


def scrivi_riga(riga):
    """Una riga nel registro, e **subito sul disco**.

    ⛔ `flush` + `fsync`: se il raccoglitore muore un secondo dopo, la riga
       dev'esserci.  Un registro che perde l'ultima riga fa dire «non e'
       arrivato» a un dispositivo che era arrivato — che e' D16 un'altra volta.
    ⛔ E un lucchetto, perche' da qui in poi il servitore ha piu' fili: due
       righe intrecciate a meta' sarebbero un registro illeggibile, cioe' di
       nuovo «non ho potuto guardare» travestito da «non e' arrivato».
    """
    with PENNA:
        with open(os.path.join(CARTELLA, REGISTRO), "a") as f:
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())


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

    def _annota(self, tipo, **campi):
        """Ogni riga porta l'ORA, l'INDIRIZZO e lo user agent.

        ⛔ `ip` e' il campo che mancava, ed e' quello su cui poggia la difesa
           E10: il browser lo puo' leggere ma non lo puo' scrivere.
        """
        riga = {"ora": datetime.datetime.now().isoformat(timespec="seconds"),
                "tipo": tipo,
                "ip": self.client_address[0],
                "ua": self.headers.get("User-Agent", "")}
        # ⚠ Le indicazioni del client (UA-CH) che il browser manda da solo:
        #    si raccolgono perche' sono un segnale in piu' — e si dichiarano
        #    per quel che sono, cioe' scritte dal browser e falsificabili.
        for h in ("Sec-CH-UA-Platform", "Sec-CH-UA-Mobile", "Sec-CH-UA-Model",
                  "Sec-CH-UA"):
            v = self.headers.get(h)
            if v:
                riga.setdefault("indicazioni_client", {})[h] = v
        riga.update(campi)
        return riga

    def do_GET(self):                            # noqa: N802
        p = urlparse(self.path).path.lstrip("/")
        if p in ("", "/"):
            p = "02-giudizio-pagina.html"
        percorso = os.path.join(CARTELLA, os.path.basename(p))
        if not os.path.isfile(percorso):
            corpo = ("non c'e': %s\n" % percorso).encode()
            self._testa(404, lunghezza=len(corpo))
            self.wfile.write(corpo)
            # ⛔ D16: il 404 va NEL REGISTRO, non solo nello stderr.  E' la
            #    riga che distingue «il dispositivo non e' arrivato» da «il
            #    dispositivo e' arrivato e non aveva niente da decodificare».
            scrivi_riga(self._annota("richiesta", percorso=self.path,
                                     codice=404, byte=0))
            return
        tipi = {".html": "text/html; charset=utf-8", ".json": "application/json",
                ".js": "text/javascript", ".h265": "application/octet-stream",
                ".bin": "application/octet-stream"}
        est = os.path.splitext(percorso)[1]
        with open(percorso, "rb") as f:
            corpo = f.read()
        self._testa(200, tipi.get(est, "application/octet-stream"), len(corpo))
        self.wfile.write(corpo)
        # ⚠ Il favicon non si registra: e' rumore, e un registro rumoroso
        #    smette di essere letto.  Tutto il resto si', anche il 200.
        if os.path.basename(percorso) != "favicon.ico":
            scrivi_riga(self._annota("richiesta", percorso=self.path,
                                     codice=200, byte=len(corpo)))

    def do_POST(self):                           # noqa: N802
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", "0"))
        corpo = self.rfile.read(n) if n else b""

        if u.path == "/pixel":
            q = parse_qs(u.query)
            nome = os.path.basename(q.get("nome", ["pagina"])[0])
            fuori = os.path.join(CARTELLA, nome)
            with open(fuori, "wb") as f:
                f.write(corpo)
            riga = self._annota("pixel", nome=nome, byte=len(corpo))
        else:
            try:
                d = json.loads(corpo.decode("utf-8") or "{}")
            except Exception as e:               # noqa: BLE001
                d = {"⛔ corpo illeggibile": str(e),
                     "grezzo": corpo[:200].decode("latin1")}
            riga = self._annota("prova" if u.path == "/prova" else "esito",
                                dati=d)

        scrivi_riga(riga)
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
    # ⛔⭐ A PIU' FILI, e non e' un'ottimizzazione — `[M]` 12 agosto 2026,
    #    trovato certificando: con **un filo solo** e `HTTP/1.1` (che tiene la
    #    connessione aperta), una connessione lasciata in piedi da una scheda
    #    blocca il servitore finche' non scade.  Misurato: un `POST /esito`
    #    partito alle 20.31.00 e' arrivato alle **20.32.57** — due minuti.
    #    ⛔ Sul telefono il sintomo sarebbe «la pagina si e' piantata», e la
    #       diagnosi ovvia sarebbe «il dispositivo non ce la fa»: un'altra
    #       accusa al componente innocente, come D16.
    if cert == "-":
        # ⚠ In chiaro **solo** sul loopback: vedi il riquadro in cima.
        srv = ThreadingHTTPServer(("127.0.0.1", porta), Servo)
        sys.stderr.write("raccoglitore F2.6 su http://127.0.0.1:%d  "
                         "(IN CHIARO, solo loopback)  cartella %s  "
                         "registro %s\n" % (porta, CARTELLA, REGISTRO))
    else:
        ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        ctx.load_cert_chain(cert, chiave)
        srv = ThreadingHTTPServer(("0.0.0.0", porta), Servo)
        srv.socket = ctx.wrap_socket(srv.socket, server_side=True)
        sys.stderr.write("raccoglitore F2.6 su https://0.0.0.0:%d  cartella "
                         "%s  registro %s\n" % (porta, CARTELLA, REGISTRO))
    srv.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
