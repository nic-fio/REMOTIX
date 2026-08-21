#!/usr/bin/env python3
"""07-b57 — QUANTO COSTA MSE rispetto a WebCodecs, sullo stesso flusso.

    python3 banchi/07-b57-quanto-costa-mse.py [--solo chrome|firefox]

⛔ PERCHE' ESISTE — 21 agosto 2026.  `[M]` Firefox per Android non ha WebCodecs
   (ne' `VideoDecoder` ne' `AudioDecoder`), ma ha WebTransport e decodifica
   H.264 **in hardware** attraverso MSE.  ⇒ L'unico modo di coprirlo e' un
   secondo percorso di disegno, `MediaSource` con un `<video>`.

⛔ E il prezzo di quel percorso e' il RITARDO, cioe' il numero che
   `SPECIFICHE.md` §3.2 mette fra quelli del prodotto (tetto 50 ms).  ⇒ Si
   misura prima di scrivere il percorso, non dopo.

⚠ E si misura sulla stessa macchina, con lo stesso flusso — i 300 fotogrammi
  del NOSTRO codificatore — dati una volta a WebCodecs e una volta a MSE.

⛔ IL LIMITE, DICHIARATO: lo schermo del banco e' un `Xvfb`, quindi **non c'e'
   GPU** e tutte e due le strade decodificano in software.  ⇒ I valori assoluti
   NON sono quelli di una macchina vera; quel che regge e' la **differenza**
   fra le due strade, che nasce dalla coda di riproduzione e non dalla scheda.
"""
import argparse, http.server, importlib.util as iu, json, os, shutil
import socketserver, subprocess, sys, tempfile, threading, time

QUI = os.path.dirname(os.path.abspath(__file__))
DATI = os.path.join(QUI, "07-b48-dati")


def _mod(nome, file):
    s = iu.spec_from_file_location(nome, os.path.join(QUI, file))
    m = iu.module_from_spec(s); s.loader.exec_module(m); return m


M = _mod("marionette", "07-b46-marionette.py")
CDP = _mod("cdp", "02-pagina-misura-cdp.py")

a = argparse.ArgumentParser()
a.add_argument("--solo", default="", choices=["", "chrome", "firefox"])
a.add_argument("--porta", type=int, default=8097)
a.add_argument("--schermo", default=":96")
a.add_argument("--ritmo", type=int, default=16)
a.add_argument("--quanti", type=int, default=100)
o = a.parse_args()

# ⛔⛔ TRE RITMI, E IL PIU' LENTO E' QUELLO CHE VALE — `[M]` 21 agosto 2026.
#
# ⚠ A 60/s e a 30/s questa macchina (Xvfb, niente GPU) **non decodifica in
#   tempo reale** 2560x962: la coda di riproduzione di MSE e' arrivata a
#   **4,7 secondi** e i fotogrammi visti erano 22 su 200.  ⇒ Li' non si misura
#   MSE, si misura una CPU al limite — e i due numeri non si possono nemmeno
#   confrontare, perche' le due strade saturano in modo diverso.
# ⭐ A 10/s nessuna delle due e' al limite, e la coda che RESTA e' quella
#   dell'architettura: e' quella la risposta alla domanda.
GIRI = [
    ("WebCodecs 10/s",   "?strada=webcodecs&ritmo=100"),
    ("MSE 10/s",         "?strada=mse&ritmo=100"),
    ("MSE 10/s inseguo", "?strada=mse&insegui=1&ritmo=100"),
    ("WebCodecs 60/s",   "?strada=webcodecs&ritmo=16"),
    ("MSE 60/s",         "?strada=mse&ritmo=16"),
]


class Zitto(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def servi(porta):
    os.chdir(DATI)
    srv = socketserver.TCPServer(("127.0.0.1", porta), Zitto)
    srv.allow_reuse_address = True
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def aspetta(leggi, quanto=300):
    t0 = time.time()
    while time.time() - t0 < quanto:
        r = leggi()
        if r:
            return r
        time.sleep(1)
    return None


def firefox(base):
    p, m, prof = M.accendi(porta=2891, headless=False, largo=1200, alto=800,
                           schermo=o.schermo)
    fuori = []
    try:
        m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        for nome, coda in GIRI:
            m.vai(base + coda + "&quanti=%d" % o.quanti)
            time.sleep(2)
            # ⛔ Il bottone si preme DAVVERO: un clic fabbricato in JavaScript
            #    non e' un gesto dell'utente, e il `<video>` non partirebbe.
            el = m.chiama("WebDriver:FindElement",
                          {"using": "css selector", "value": "#via"})["value"]
            m.chiama("WebDriver:ElementClick",
                     {"id": list(el.values())[0], "element": list(el.values())[0]})
            r = aspetta(lambda: m.js("return window.RISULTATO || null")["value"])
            fuori.append({"giro": nome, "esito": r})
            print("   %-14s %s" % (nome, breve(r)))
    finally:
        M.spegni(p, prof)
    return {"browser": "firefox", "giri": fuori}


def chrome(base):
    t = tempfile.mkdtemp(prefix="b57-")
    amb = {k: v for k, v in os.environ.items() if k != "WAYLAND_DISPLAY"}
    amb["DISPLAY"] = o.schermo
    br = subprocess.Popen(
        ["google-chrome", "--no-sandbox", "--user-data-dir=%s/p" % t,
         "--no-first-run", "--no-default-browser-check", "--ozone-platform=x11",
         "--autoplay-policy=no-user-gesture-required",
         "--remote-debugging-port=9713", "--remote-allow-origins=*",
         "--window-size=1200,800", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=amb)
    fuori = []
    try:
        b = CDP.pagina(9713, attesa=40)
        c = CDP.Cdp(b["webSocketDebuggerUrl"], timeout=600)
        for x in ("Page.enable", "Runtime.enable"):
            c.chiama(x)
        for nome, coda in GIRI:
            c.chiama("Page.navigate",
                     url=base + coda + "&quanti=%d" % o.quanti)
            time.sleep(3)
            # ⛔ Anche qui il clic e' vero, per la stessa ragione.
            r0 = c.valuta("JSON.stringify((document.getElementById('via')||{})"
                          ".getBoundingClientRect?document.getElementById('via')"
                          ".getBoundingClientRect():null)", attendi=False)
            if r0 and r0 != "null":
                q = json.loads(r0)
                x, y = int(q["x"] + q["width"] / 2), int(q["y"] + q["height"] / 2)
                for tipo in ("mouseMoved", "mousePressed", "mouseReleased"):
                    pp = {"type": tipo, "x": x, "y": y}
                    if tipo != "mouseMoved":
                        pp.update(button="left", clickCount=1)
                    c.chiama("Input.dispatchMouseEvent", **pp)
                    time.sleep(0.05)
            # ⛔ «null» E' UNA STRINGA, e `if r:` la prende per buona: il
            #    banco tornava dopo un secondo dicendo «nessun esito» su una
            #    pagina che stava lavorando.  `[M]` 21 ago 2026 — Chrome dava
            #    tre righe rosse su tre, e funzionava.
            r = aspetta(lambda: (lambda x: x if x and x != "null" else None)(
                c.valuta("JSON.stringify(window.RISULTATO||null)", attendi=False)))
            r = json.loads(r) if r else None
            fuori.append({"giro": nome, "esito": r})
            print("   %-14s %s" % (nome, breve(r)))
    finally:
        br.terminate()
        shutil.rmtree(t, ignore_errors=True)
    return {"browser": "chrome", "giri": fuori}


def breve(r):
    if not r:
        return "⛔ nessun esito"
    if r.get("guaio"):
        return "⛔ " + r["guaio"]
    d = r["ritardo"]
    # ⛔ Una mediana su tre campioni non e' una mediana: si dichiara invece di
    #    stamparla come se lo fosse.
    if d["n"] < 20:
        return ("⚠ SOLO %d campioni su %d fotogrammi: non e' una misura "
                "(mediana %.1f ms, coda %s)"
                % (d["n"], r["mandati"], d["mediana"], r.get("coda_ms")))
    return ("ritardo mediano %6.1f ms · p90 %6.1f · peggio %6.1f  (%d/%d "
            "fotogrammi visti%s)"
            % (d["mediana"], d["p90"], d["peggio"], r["presentati"],
               r["mandati"], (" · %d salti" % r["salti"]) if r.get("salti") else ""))


def main():
    mp4 = os.path.join(DATI, "h264-frammentato.mp4")
    if not os.path.exists(mp4):
        print("⛔ manca %s — si fa con:\n"
              "   ffmpeg -framerate 60 -f h264 -i h264.264 -c copy \\\n"
              "     -movflags empty_moov+default_base_moof+frag_every_frame \\\n"
              "     -f mp4 h264-frammentato.mp4" % mp4)
        return 2
    shutil.copy(os.path.join(QUI, "07-b57-mse-quanto-costa.html"),
                os.path.join(DATI, "b57.html"))
    xv = None
    if subprocess.run(["xdpyinfo", "-display", o.schermo],
                      capture_output=True).returncode != 0:
        xv = subprocess.Popen(["Xvfb", o.schermo, "-screen", "0", "1200x800x24"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
    srv = servi(o.porta)
    base = "http://127.0.0.1:%d/b57.html" % o.porta
    print("⛔ LIMITE DICHIARATO: schermo Xvfb, niente GPU — tutt'e due le strade "
          "decodificano in software.\n   Regge la DIFFERENZA fra le strade, non "
          "il valore assoluto.\n")
    esiti = []
    try:
        for nome, f in (("firefox", firefox), ("chrome", chrome)):
            if o.solo and o.solo != nome:
                continue
            print("⏳ %s" % nome.upper())
            try:
                esiti.append(f(base))
            except Exception as e:
                print("   ⛔ il banco e' caduto: %r" % e)
                esiti.append({"browser": nome, "guaio": repr(e)})
    finally:
        srv.shutdown()
        if xv:
            xv.terminate()
    fuori = os.path.join(QUI, "07-b57-esiti.json")
    with open(fuori, "w", encoding="utf-8") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)
    print("\n══════════ VERDETTO ══════════")
    for e in esiti:
        base_wc = {}
        for g in e.get("giri", []):
            r = g.get("esito") or {}
            if r.get("guaio") or not r.get("ritardo"):
                continue
            if (r["ritardo"] or {}).get("n", 0) < 20:
                continue
            ritmo = "60/s" if "60/s" in g["giro"] else "10/s"
            if g["giro"].startswith("WebCodecs"):
                base_wc[ritmo] = r["ritardo"]["mediana"]
            elif ritmo in base_wc:
                print("%-8s %-18s costa %+7.1f ms sulla mediana rispetto a "
                      "WebCodecs (coda %s ms)"
                      % (e["browser"], g["giro"],
                         r["ritardo"]["mediana"] - base_wc[ritmo],
                         r.get("coda_ms")))
    print("\n%s" % fuori)
    return 0


sys.exit(main())
