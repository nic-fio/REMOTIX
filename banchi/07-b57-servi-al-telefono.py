#!/usr/bin/env python3
"""07-b57 (telefono) — serve il banco «quanto costa MSE» alla rete di casa.

    python3 banchi/07-b57-servi-al-telefono.py [--porta 8090]

⛔ PERCHE' ESISTE — 21 agosto 2026.  La domanda («quanto costa MSE rispetto a
   WebCodecs») **non si puo' misurare sul portatile del banco**: li' lo schermo
   e' un `Xvfb` senza GPU, il flusso e' 2560x962, e nessuna delle due strade
   decodifica in tempo reale.  `[M]` La coda di riproduzione e' arrivata a
   **4,7 secondi** e il `<video>` presentava 4 fotogrammi su 100: quel numero
   non parla di MSE, parla di una CPU al limite.

⭐ Il telefono invece decodifica H.264 **in hardware** — lo ha dichiarato lui
   (`decodingInfo` → `powerEfficient`) su tutt'e due i motori.  ⇒ La misura si
   fa dove la domanda vive.

L'esito torna da solo: la pagina lo manda in `/esito`, e qui si stampa e si
scrive in `07-b57-telefono.jsonl`.  ⚠ Chi prova non deve leggere niente sullo
schermo del telefono.
"""
import argparse, http.server, json, os, socket, socketserver, shutil, sys
import urllib.parse

QUI = os.path.dirname(os.path.abspath(__file__))
DATI = os.path.join(QUI, "07-b48-dati")
FUORI = os.path.join(QUI, "07-b57-telefono.jsonl")

a = argparse.ArgumentParser()
a.add_argument("--porta", type=int, default=8090)
o = a.parse_args()

shutil.copy(os.path.join(QUI, "07-b57-mse-quanto-costa.html"),
            os.path.join(DATI, "b57.html"))


class Mano(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path.startswith("/esito?"):
            testo = urllib.parse.unquote(self.path[len("/esito?"):])
            with open(FUORI, "a", encoding="utf-8") as f:
                f.write(testo + "\n")
            try:
                r = json.loads(testo)
                d = r.get("ritardo") or {}
                print("⭐ ESITO · %s · ritmo %s · %s"
                      % (r.get("strada"), r.get("ritmo"),
                         ("⛔ " + r["guaio"]) if r.get("guaio") else
                         ("mediana %.1f ms · p90 %.1f · %d campioni · coda %s ms "
                          "· buttati %s/%s"
                          % (d.get("mediana", 0), d.get("p90", 0), d.get("n", 0),
                             r.get("coda_ms"), r.get("buttati"), r.get("totali")))))
                print("   %s" % (r.get("browser") or "")[:110])
            except Exception:
                print("⭐ ESITO (grezzo): %s" % testo[:200])
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, *a):
        pass


def mio_indirizzo():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.168.0.2", 80))
        return s.getsockname()[0]
    finally:
        s.close()


os.chdir(DATI)
socketserver.TCPServer.allow_reuse_address = True
srv = socketserver.TCPServer(("0.0.0.0", o.porta), Mano)
ip = mio_indirizzo()
print("⭐ pronto.  Dal telefono, una alla volta:\n")
for nome, coda in (("WebCodecs (solo Chrome: Firefox Android non ce l'ha)",
                    "?strada=webcodecs&ritmo=16&quanti=200"),
                   ("MSE", "?strada=mse&ritmo=16&quanti=200"),
                   ("MSE inseguendo", "?strada=mse&insegui=1&ritmo=16&quanti=200")):
    print("   %-52s http://%s:%d/b57.html%s" % (nome, ip, o.porta, coda))
print("\n⚠ Ogni giro dura circa mezzo minuto.  L'esito arriva qui da solo.")
print("   Ctrl-C per finire.  Esiti anche in %s\n" % FUORI)
try:
    srv.serve_forever()
except KeyboardInterrupt:
    print("\nfinito")
