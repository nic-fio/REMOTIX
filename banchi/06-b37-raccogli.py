#!/usr/bin/env python3
"""06-b37-raccogli.py — il raccoglitore della sottofase 6.5, e il CANALE DI
COMANDO che funziona SUI DUE MOTORI.

    python3 banchi/06-b37-raccogli.py <porta> <sorgente-pagina> <esiti.jsonl>

⛔ PERCHE' NON SI USA CDP.  `banchi/02-pagina-misura-cdp.py` esiste e funziona,
   ⚠ ma parla **solo a Chrome**: il mandato di questa sottofase chiede la stessa
   misura sui DUE motori, e un banco che sa guidarne uno solo produrrebbe due
   misure non confrontabili — una per iniezione e una per osservazione.
   ⇒ Il canale e' HTTP e la sonda sta DENTRO la pagina: identico su Chrome e su
   Firefox, e non dipende da nessun protocollo di debug.

⭐ COME SI RAGGIUNGONO LE FUNZIONI DELLA PAGINA.  `src/pagina.html` ha **un solo
   `<script>` classico**: i suoi `function` stanno sull'oggetto globale e i suoi
   `const`/`let` di livello superiore (`schermo`, `ADATTA`, `chiedi_tela`)
   stanno nel **registro lessicale globale**, che e' condiviso fra tutti gli
   script classici dello stesso documento.  ⇒ Una `eval` DIRETTA dentro la sonda
   iniettata li vede per nome.  ⚠ Un `<script type=module>` non li vedrebbe, e
   nemmeno il mondo isolato di un'estensione: se un giorno la pagina diventasse
   un modulo, questo banco morirebbe con un `ReferenceError` — che e' il modo
   giusto di morire (rumoroso).

⛔ E QUEL CHE QUESTO BANCO NON E': non e' il prodotto.  La pagina servita qui e'
   una COPIA con una sonda in fondo (`06-b37-strumenta.py` dice esattamente che
   cosa aggiunge).  Ogni riga di misura porta `iniezione: si|no`, perche' una
   misura presa su una pagina strumentata e una presa sul prodotto non sono la
   stessa cosa e non si mescolano.
"""
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

PORTA = int(sys.argv[1]) if len(sys.argv) > 1 else 8871
SORGENTE = sys.argv[2] if len(sys.argv) > 2 else "/tmp/06-b37-pagina.html"
ESITI = sys.argv[3] if len(sys.argv) > 3 else "/tmp/06-b37-esiti.jsonl"

_lock = threading.Lock()
_comandi = []          # [{"n": i, "js": "..."}]
_risposte = {}         # n -> {"ok": bool, "valore": ...}
_pronto = threading.Condition(_lock)
_carichi = [0]         # quante volte la pagina si e' annunciata


def scrivi_esito(d):
    d.setdefault("orologio", time.time())
    with open(ESITI, "a", encoding="utf-8") as f:
        f.write(json.dumps(d, ensure_ascii=False) + "\n")


class Gestore(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _manda(self, corpo, tipo="application/json", codice=200):
        if isinstance(corpo, str):
            corpo = corpo.encode("utf-8")
        self.send_response(codice)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        # ⛔ La pagina si ricarica a ogni giro e una copia in cache sarebbe una
        #    misura vecchia sotto l'etichetta di una nuova.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(corpo)

    def do_GET(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path in ("/", "/pagina.html"):
            try:
                with open(SORGENTE, "rb") as f:
                    self._manda(f.read(), "text/html; charset=utf-8")
            except OSError as e:
                self._manda(str(e), "text/plain", 500)
            return
        if u.path == "/b37/comando":
            da = int(q.get("da", ["0"])[0])
            with _lock:
                fuori = [c for c in _comandi if c["n"] >= da]
            self._manda(json.dumps(fuori))
            return
        if u.path == "/b37/stato":
            with _lock:
                self._manda(json.dumps({"carichi": _carichi[0],
                                        "comandi": len(_comandi)}))
            return
        self._manda("no", "text/plain", 404)

    def do_POST(self):
        u = urlparse(self.path)
        n = int(self.headers.get("Content-Length", "0"))
        corpo = self.rfile.read(n).decode("utf-8", "replace") if n else ""
        if u.path == "/b37/esito":
            try:
                d = json.loads(corpo)
            except Exception:
                d = {"tipo": "illeggibile", "grezzo": corpo[:400]}
            if d.get("tipo") == "carico":
                with _lock:
                    _carichi[0] += 1
            scrivi_esito(d)
            self._manda("{}")
            return
        if u.path == "/b37/risposta":
            try:
                d = json.loads(corpo)
            except Exception:
                self._manda("{}")
                return
            with _pronto:
                _risposte[d.get("n")] = d
                _pronto.notify_all()
            self._manda("{}")
            return
        if u.path == "/comanda":
            # ⛔ Il guscio del banco chiama QUESTA: accoda, aspetta la risposta
            #    della pagina e la restituisce.  Un giro solo, e nessun file
            #    intermedio da cui leggere «l'ultima riga» (rilievo R8.10).
            attesa = float(self.headers.get("X-Attesa", "15"))
            with _pronto:
                num = len(_comandi)
                _comandi.append({"n": num, "js": corpo})
            scadenza = time.time() + attesa
            with _pronto:
                while num not in _risposte and time.time() < scadenza:
                    _pronto.wait(0.1)
                r = _risposte.get(num)
            if r is None:
                # ⛔ 3.10: «vuoto» e «proibito» hanno lo stesso aspetto.  Un
                #    comando scaduto NON restituisce un valore vuoto: dice che
                #    e' scaduto, e chi legge non lo puo' confondere con un dato.
                self._manda(json.dumps({"ok": False, "scaduto": True,
                                        "valore": "nessuna risposta dalla "
                                                  "pagina entro %.1f s" % attesa}))
            else:
                self._manda(json.dumps(r))
            return
        self._manda("no", "text/plain", 404)


if __name__ == "__main__":
    os.makedirs(os.path.dirname(os.path.abspath(ESITI)) or ".", exist_ok=True)
    s = ThreadingHTTPServer(("127.0.0.1", PORTA), Gestore)
    s.daemon_threads = True
    print("06-b37: raccoglitore su 127.0.0.1:%d, pagina da %s" % (PORTA, SORGENTE),
          flush=True)
    s.serve_forever()
