#!/usr/bin/env python3
"""
07-b40 — il lanciatore della sonda dell'audio.

Serve `07-b40-sonda-audio.html` su `http://localhost:PORTA` — che e' un
contesto SICURO su tutt'e due i motori, quindi WebCodecs c'e' — apre il
browser che gli si nomina, e ASPETTA il portatore invece di leggere uno
scatto dello schermo.

  ⛔ Un motore per giro, nominato sulla riga di comando: `CODER.md` §3.9 —
     «un componente che sceglie in autonomia produce due misure diverse sotto
     la stessa etichetta».  Qui il motore si chiede per nome e si VERIFICA che
     abbia risposto lui, leggendo lo `user agent` nell'esito.

Uso:  python3 07-b40-lancia.py chrome|firefox [--porta N]
"""
import argparse
import http.server
import json
import os
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
PAGINA = os.path.join(QUI, "07-b40-sonda-audio.html")

MOTORI = {
    "chrome": ["google-chrome", "google-chrome-stable", "chromium", "chrome"],
    "firefox": ["firefox", "firefox-esr"],
}

esito = {"dato": None, "pacchetti": ""}
pronto = threading.Event()


class Servo(http.server.BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def do_GET(self):
        # I pacchetti raccolti dal filo, per l'ultimo anello (`opus_dal_server`).
        if self.path.split("?", 1)[0] == "/pacchetti.jsonl":
            try:
                with open(esito["pacchetti"], "rb") as f:
                    corpo = f.read()
            except OSError as e:
                self.send_error(404, str(e))
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/x-ndjson")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
            return
        # ⛔ la query fa parte di `self.path`: confrontarlo intero fa dare 404
        #    alla pagina appena le si passa `?wt=…`, e il banco muore per
        #    «nessun portatore» invece che per il motivo vero.
        strada = self.path.split("?", 1)[0]
        if strada in ("/", "/index.html"):
            with open(PAGINA, "rb") as f:
                corpo = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(corpo)))
            self.end_headers()
            self.wfile.write(corpo)
        else:
            self.send_error(404)

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        try:
            esito["dato"] = json.loads(self.rfile.read(n))
        except Exception as e:  # noqa: BLE001
            esito["dato"] = {"errore": f"portatore illeggibile: {e}"}
        self.send_response(204)
        self.end_headers()
        pronto.set()


def trova(motore):
    for nome in MOTORI[motore]:
        strada = shutil.which(nome)
        if strada:
            return strada
    return None


def main():
    p = argparse.ArgumentParser()
    p.add_argument("motore", choices=sorted(MOTORI))
    p.add_argument("--porta", type=int, default=7607)
    p.add_argument("--tetto", type=int, default=90, help="secondi d'attesa")
    p.add_argument("--wt", help="A2: l'indirizzo WebTransport del server vero, "
                                "es. https://192.168.0.2:7700/rcp/1")
    p.add_argument("--impronta", help="A2: SHA-256 del DER in base64, "
                                      "come la pubblica la pagina del server")
    p.add_argument("--pacchetti", default="",
                   help="il JSONL dei blocchi raccolti dal filo da "
                        "`01-b3-cliente.py --audio-scrivi`: il browser prova a "
                        "decodificare i pacchetti DEL NOSTRO SERVER")
    a = p.parse_args()
    if bool(a.wt) != bool(a.impronta):
        print("⛔ --wt e --impronta vanno insieme: senza impronta la sessione "
              "non si apre, e il risultato sarebbe «FALLITA» per il motivo "
              "sbagliato", file=sys.stderr)
        return 3

    binario = trova(a.motore)
    if not binario:
        print(f"⛔ {a.motore} non c'e' su questa macchina: "
              f"cercati {MOTORI[a.motore]}", file=sys.stderr)
        return 3

    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("127.0.0.1", a.porta), Servo) as srv:
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        url = f"http://localhost:{a.porta}/"
        q = {}
        if a.wt:
            q.update({"wt": a.wt, "impronta": a.impronta})
        if a.pacchetti:
            esito["pacchetti"] = a.pacchetti
            q["pacchetti"] = "1"
        if q:
            from urllib.parse import urlencode
            url += "?" + urlencode(q)
        profilo = tempfile.mkdtemp(prefix=f"07-b40-{a.motore}-")
        if a.motore == "chrome":
            cmd = [binario, "--headless=new", f"--user-data-dir={profilo}",
                   "--no-first-run", "--disable-gpu", url]
        else:
            cmd = [binario, "--headless", "--profile", profilo, url]
        print(f"⏳ {a.motore}: {binario}\n   {url}", file=sys.stderr)
        proc = subprocess.Popen(cmd, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
        t0 = time.time()
        arrivato = pronto.wait(a.tetto)
        proc.terminate()
        try:
            proc.wait(5)
        except subprocess.TimeoutExpired:
            proc.kill()
        shutil.rmtree(profilo, ignore_errors=True)

    if not arrivato:
        # ⛔ e il silenzio NON e' uno zero: si dice che cosa e' mancato
        print(f"⛔ NIENTE DA GIUDICARE — nessun portatore in {a.tetto} s. "
              f"La pagina non e' arrivata in fondo, o il motore non l'ha aperta.",
              file=sys.stderr)
        return 2

    d = esito["dato"]
    d["secondi"] = round(time.time() - t0, 2)
    d["motore_chiesto"] = a.motore
    ua = d.get("motore", "")
    atteso = "Firefox" if a.motore == "firefox" else "Chrom"
    d["motore_confermato"] = atteso in ua      # ⛔ ha risposto quello che ho chiamato?
    print(json.dumps(d, indent=2, ensure_ascii=False))
    return 0 if d["motore_confermato"] else 4


if __name__ == "__main__":
    sys.exit(main())
