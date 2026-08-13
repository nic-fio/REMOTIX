#!/usr/bin/env python3
"""03-b19-dipinti-worker.py — ⭐ I FOTOGRAMMI DIPINTI, con e senza il worker.

    python3 banchi/03-b19-dipinti-worker.py --giri 3
    python3 banchi/03-b19-dipinti-worker.py --giri 3 --seq av1-1280x720

═══════════════════════════════════════════════════════════════════════════════
⛔ PERCHE' QUESTO BANCO ESISTE, invece di rigirare `03-b16-dipinti.py`
═══════════════════════════════════════════════════════════════════════════════

`LEZIONI.md` §6.2: «un guadagno che si paga in fluidita' non e' un guadagno» —
in v1 il costo per fotogramma scese da 41 ms a 6 **mentre i fotogrammi
consegnati scendevano da 29 a 22,7**.  ⇒ Accanto al RITARDO va misurato il
TETTO, o il risultato non e' leggibile.

⛔ E `03-b16-dipinti.py` NON puo' misurare il tetto del worker: il suo caso
   `Dsat` offre i fotogrammi chiamando `REMOTIX.leggi_uno_stream(...)`
   **sul thread principale** (righe 650, 702, 717, 879), e legge
   `S.conti`/`TELA.getContext("2d")` di la'.  Con `?video=worker` quel percorso
   non e' quello che dipinge.  ⚠ E quel banco NON si tocca: e' certificato
   (19 casi verdi, 8 guasti su 8 accusati) e altri ci si appoggiano.

⇒ Qui si misura la STESSA grandezza — `conti.dipinti` al secondo a saturazione
  — sulle due strade, **con lo stesso alimentatore**, e si stampano accanto.

═══════════════════════════════════════════════════════════════════════════════
⛔ COME SI TIENE ONESTO IL CONFRONTO
═══════════════════════════════════════════════════════════════════════════════

  1. ⭐ **Lo stesso oggetto in ingresso in tutt'e due i casi**: un
     `ReadableStream` VERO.  ⚠ `03-b16` usa un finto (`B.finto()`), che sul
     thread principale va bene ma non si puo' trasferire a un worker: usarne
     due diversi vorrebbe dire misurare anche la differenza fra i due
     alimentatori e chiamarla differenza fra le due strade;
  2. ⭐ **lo stesso respiro**: si offre un fotogramma e si cede il turno
     (`setTimeout(0)`), come fa `CASO_SATURA` di `03-b16`;
  3. ⛔ **un tetto all'arretrato** (`ARRETRATO`), e vale per tutt'e due.  Senza,
     il thread principale in modo worker — che non ha niente da fare — offrirebbe
     a migliaia e si misurerebbe la pressione sulla memoria invece del tetto;
  4. ⛔ **piu' giri per lato**, e non uno: `03-b16` ha misurato che la
     dispersione fra giri (un fotogramma al secondo) e' piu' piccola della
     differenza che si cerca (quattro).  Con un giro solo non si saprebbe;
  5. ⚠ **si stampano anche gli OFFERTI**: «dipinti al secondo» senza «offerti al
     secondo» non distingue «non ce la fa» da «non gliene hanno dati».

⚠ E IL BUCO CIECO, dichiarato: qui non c'e' ne' rete ne' WebTransport — i
  fotogrammi nascono in pagina.  Questo banco misura il TETTO DELLA PAGINA, non
  la consegna; il ritardo sulla catena vera lo misura `03-b19-ritardo-worker.py`.
"""
import argparse
import http.server
import importlib.util
import json
import os
import socketserver
import statistics
import subprocess
import sys
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)
SORGENTE = os.path.join(RADICE, "src", "pagina.html")
SEQUENZE = os.path.join(QUI, "03-b16-sequenze")

# ⛔ Quanti fotogrammi si lasciano in volo.  Vale per tutt'e due le strade.
ARRETRATO = 30
AVVIO_MS = 3000       # ⚠ i primi 3 s si buttano: c'e' dentro la configurazione
CODA_MS = 400         # e gli ultimi, dove l'alimentatore ha gia' smesso


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ESITO STA NEL CODICE D'USCITA, NON NELLA PROSA — cura del 13 agosto 2026
#
# Fino a stasera `principale()` finiva con `return 0` e `ko()` si limitava a
# STAMPARE.  Tre dei cinque rossi tornavano gia' **3** (il palco non si
# accende), ⛔ ma gli altri due — «errori nella pagina» e ⭐ «il worker DIPINGE
# MENO» — restavano **soltanto nel testo**, e il banco usciva **0** dicendo di
# no.  ⇒ `01-b12-guasti.py --giudica` avrebbe letto «col guasto ha dato lo
# stesso esito del sano»: il difetto che B12 esiste per trovare, dentro il
# banco.  La nota della voce `03-b19` del catalogo lo dichiarava gia'.
#
# ⭐ La forma e' quella dei banchi gia' certificati: `03-b18-credito.py` chiude
#    con `return 1 if rossi else 0`, `03-b15-movimento.py` con
#    `return 1 if conto["rosso"] else 0`.  ⇒ **1** = c'e' stato un rosso;
#    **0** = nessuno; il **3** resta «non ho potuto misurare», che e' un'altra
#    cosa e non si arrotonda con l'1.
# ⚠ E non tocca nessuna misura: per `ko()` non passa nessun numero.
# ═══════════════════════════════════════════════════════════════════════════
ROSSI = 0


def ok(t):
    print("    \033[1;32mOK\033[0m  %s" % t)


def ko(t):
    global ROSSI
    ROSSI += 1
    print("    \033[1;31mNO\033[0m  %s" % t)


def inf(t):
    print("    --  %s" % t)


def log(t):
    print("\n\033[1m== %s\033[0m" % t)


class Servente(http.server.BaseHTTPRequestHandler):
    """⛔ COOP+COEP anche qui: senza, `crossOriginIsolated` e' falso, i
    cronometri cadono su una griglia da 1 ms e il numero non varrebbe niente
    (`SPECIFICHE.md` §11.5)."""

    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/pagina.html"):
            corpo = open(SORGENTE, "rb").read()
            tipo = "text/html; charset=utf-8"
        elif p.startswith("/sequenze/"):
            f = os.path.join(SEQUENZE, os.path.basename(p))
            if not os.path.exists(f):
                self.send_error(404)
                return
            corpo = open(f, "rb").read()
            tipo = "application/json"
        else:
            self.send_error(404)
            return
        self.send_response(200)
        for k, v in (("Content-Type", tipo),
                     ("Cross-Origin-Opener-Policy", "same-origin"),
                     ("Cross-Origin-Embedder-Policy", "require-corp"),
                     ("Cross-Origin-Resource-Policy", "same-origin"),
                     ("Cache-Control", "no-store"),
                     ("Content-Length", str(len(corpo)))):
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(corpo)

    def log_message(self, *a):
        pass


class Sito(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ L'ALIMENTATORE — lo STESSO per le due strade, e la differenza sta in una
#    riga sola: `VW.manda_flusso(rs)` contro `REMOTIX.leggi_uno_stream(rs, …)`
# ═══════════════════════════════════════════════════════════════════════════
SATURA = r"""
(async function () {
  const modo = %(modo)s, secondi = %(secondi)s, ARRETRATO = %(arretrato)d;
  const R = window.REMOTIX, S = R.schermo;
  const pausa = (ms) => new Promise(r => setTimeout(r, ms));

  const s = await (await fetch("/sequenze/%(seq)s.json", {cache:"no-store"})).json();
  const b2b = (b) => { const x = atob(b), u = new Uint8Array(x.length);
                       for (let i = 0; i < x.length; i++) u[i] = x.charCodeAt(i);
                       return u; };
  const pezzi = s.pezzi.map(p => ({ chiave: p.chiave, b: b2b(p.dati) }));

  /* ⛔ Si riparte da zero e si negozia, come fa `avvia()` di `03-b16`. */
  S.riparti();
  S.negozia(2, 8, s.stringa, s.larghezza, s.altezza);
  S.vista(%(vista_l)d, %(vista_a)d);
  await pausa(300);

  function pacco(tipo, dati, numero, istante) {
    const b = new Uint8Array(28 + dati.length), v = new DataView(b.buffer);
    v.setUint16(0, tipo); v.setUint16(2, 2);
    v.setUint32(4, s.larghezza); v.setUint32(8, s.altezza);
    v.setUint32(12, numero); v.setBigUint64(16, BigInt(istante));
    v.setUint32(24, 0); b.set(dati, 28);
    return b;
  }
  /* ⭐ Un `ReadableStream` VERO — l'unico oggetto che va bene per tutt'e due
     le strade, perche' e' l'unico TRASFERIBILE. */
  function flusso(b) {
    const passo = Math.max(1, Math.ceil(b.length / 4));
    return new ReadableStream({ start(c) {
      for (let o = 0; o < b.length; o += passo)
        c.enqueue(b.subarray(o, Math.min(b.length, o + passo)));
      c.close();
    } });
  }

  const campioni = [];
  let offerti = 0;
  const spia = setInterval(function () {
    campioni.push({ t: performance.now(), offerti: offerti,
                    c: Object.assign({}, S.conti) });
  }, 250);

  const t0 = performance.now();
  while (performance.now() - t0 < secondi * 1000) {
    /* ⛔ IL TETTO ALL'ARRETRATO, e vale per tutt'e due: `S.conti.completi` di
       qua e' specchiato dal worker ogni 100 ms, quindi e' un freno GROSSOLANO —
       ed e' voluto, perche' 30 in volo sono molti piu' di quanti se ne
       dipingano in 100 ms: satura lo stesso, e non esplode la memoria. */
    if (offerti - (S.conti.completi || 0) > ARRETRATO) { await pausa(1); continue; }
    const p = pezzi[offerti %% pezzi.length];
    const b = pacco(p.chiave ? 0x0301 : 0x0302, p.b, offerti + 1,
                    Math.round(offerti * 16667));
    const rs = flusso(b);
    if (modo === "worker") VW.manda_flusso(rs);
    else R.leggi_uno_stream(rs, async function () {});
    offerti++;
    await pausa(0);
  }
  await pausa(1500);
  clearInterval(spia);
  campioni.push({ t: performance.now(), offerti: offerti,
                  c: Object.assign({}, S.conti) });
  return { campioni: campioni, offerti: offerti,
           conti: Object.assign({}, S.conti), errori: S.errori.slice(-6),
           dipinta: S.dipinta, dec: [S.dec_l, S.dec_a],
           acceso: document.body.dataset.schermo === "acceso",
           seq: { l: s.larghezza, a: s.altezza, stringa: s.stringa } };
})()
"""


def ritmi(campioni, chiave):
    """⭐ Da contatori cumulativi a ritmi, a DISTRIBUZIONE.  ⛔ Si butta
    l'avvio (la configurazione del decodificatore ci sta dentro) e la coda
    (l'alimentatore ha gia' smesso): un ritmo medio che li comprende non e' il
    tetto, e' una media fra il tetto e due pezzi di niente."""
    if len(campioni) < 3:
        return []
    t0 = campioni[0]["t"]
    tf = campioni[-1]["t"]
    fuori = []
    for a, b in zip(campioni, campioni[1:]):
        if a["t"] - t0 < AVVIO_MS or tf - b["t"] < CODA_MS:
            continue
        dt = (b["t"] - a["t"]) / 1000.0
        if dt <= 0:
            continue
        va = a["c"].get(chiave, 0) if chiave != "offerti" else a["offerti"]
        vb = b["c"].get(chiave, 0) if chiave != "offerti" else b["offerti"]
        fuori.append((vb - va) / dt)
    return fuori


def stat(v):
    if not v:
        return {"n": 0}
    w = sorted(v)

    def q(p):
        return w[min(len(w) - 1, max(0, int(round(p * (len(w) - 1)))))]

    return {"n": len(w), "min": round(w[0], 1), "p05": round(q(0.05), 1),
            "mediana": round(q(0.50), 1), "p95": round(q(0.95), 1),
            "max": round(w[-1], 1), "media": round(sum(w) / len(w), 1)}


class Palco:
    def __init__(self, schermo, diagnosi, lavoro, finestra=(1400, 900)):
        self.schermo, self.diagnosi = schermo, diagnosi
        self.finestra = finestra
        self.t = lavoro
        self.x = self.chrome = self.c = None
        os.makedirs(self.t, exist_ok=True)

    def _amb(self):
        e = dict(os.environ)
        e.pop("WAYLAND_DISPLAY", None)
        e["DISPLAY"] = self.schermo
        return e

    def accendi(self):
        sock = "/tmp/.X11-unix/X" + self.schermo.lstrip(":")
        if os.path.exists(sock):
            raise RuntimeError("⛔ %s esiste gia': un altro banco usa %s"
                               % (sock, self.schermo))
        l, a = self.finestra
        self.x = subprocess.Popen(
            ["Xvfb", self.schermo, "-screen", "0", "%dx%dx24" % (l + 100, a + 200)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        fine = time.time() + 15
        misurato = None
        while time.time() < fine:
            r = subprocess.run(["xdpyinfo"], env=self._amb(),
                               capture_output=True, text=True)
            if r.returncode == 0:
                for riga in r.stdout.splitlines():
                    if "dimensions:" in riga:
                        misurato = riga.split()[1]
                break
            time.sleep(0.3)
        if misurato is None:
            raise RuntimeError("⛔ Xvfb non ha risposto a `xdpyinfo`: non e' "
                               "«schermo vuoto», e' «non ho potuto guardare»")
        self.chrome = subprocess.Popen(
            ["google-chrome", "--user-data-dir=%s/profilo" % self.t,
             "--no-first-run", "--no-default-browser-check", "--disable-sync",
             "--remote-debugging-port=%d" % self.diagnosi,
             "--remote-allow-origins=*",
             "--window-size=%d,%d" % (l, a), "--window-position=0,0",
             "about:blank"], env=self._amb(),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        spec = importlib.util.spec_from_file_location(
            "cdp", os.path.join(QUI, "02-pagina-misura-cdp.py"))
        cdp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cdp)
        b = cdp.pagina(self.diagnosi, attesa=40)
        self.c = cdp.Cdp(b["webSocketDebuggerUrl"], timeout=600)
        for m in ("Page.enable", "Runtime.enable", "Network.enable"):
            self.c.chiama(m)
        self.c.chiama("Network.setCacheDisabled", cacheDisabled=True)
        return misurato

    def spegni(self):
        for p in (self.chrome, self.x):
            if p:
                try:
                    p.terminate()
                    p.wait(timeout=8)
                except Exception:              # noqa: BLE001
                    try:
                        p.kill()
                    except Exception:          # noqa: BLE001
                        pass


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=7611)
    p.add_argument("--diagnosi", type=int, default=9611)
    p.add_argument("--schermo", default=":87")
    p.add_argument("--seq", default="av1-1920x1080")
    p.add_argument("--secondi", type=float, default=12.0)
    p.add_argument("--giri", type=int, default=3)
    p.add_argument("--lavoro", default="/tmp/03-b19-dipinti")
    p.add_argument("--verbale", default="/tmp/03-b19-dipinti/verbale.json")
    a = p.parse_args()

    print(__doc__.split("═══")[0])
    sito = Sito(("127.0.0.1", a.porta), Servente)
    threading.Thread(target=sito.serve_forever, daemon=True).start()
    palco = Palco(a.schermo, a.diagnosi, os.path.join(a.lavoro, "palco"))
    v = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "seq": a.seq,
         "secondi": a.secondi, "giri": a.giri, "arretrato": ARRETRATO,
         "sorgente": SORGENTE, "esiti": {}}
    try:
        log("Il palco")
        inf("Xvfb %s: %s" % (a.schermo, palco.accendi()))
        c = palco.c

        for modo in ("principale", "worker"):
            log("LA STRADA «%s» — %d giri da %g s, sequenza %s"
                % (modo, a.giri, a.secondi, a.seq))
            url = "http://127.0.0.1:%d/pagina.html%s" % (
                a.porta, "?video=worker" if modo == "worker" else "")
            giri = []
            for g in range(a.giri):
                c.chiama("Page.navigate", url=url)
                time.sleep(2.5)
                pronto = c.valuta(
                    "!!(window.REMOTIX && window.REMOTIX.schermo"
                    " && window.REMOTIX.leggi_uno_stream)")
                if not pronto:
                    ko("⛔ la pagina non e' pronta")
                    return 3
                if modo == "worker":
                    vivo = c.valuta("!!(VW && VW.pronto)")
                    if not vivo:
                        ko("⛔ «?video=worker» ma il worker non e' pronto: NON "
                           "misuro (sarebbe il thread principale con "
                           "l'etichetta del worker)")
                        return 3
                r = c.valuta(SATURA % {
                    "modo": json.dumps(modo), "secondi": a.secondi,
                    "seq": a.seq, "arretrato": ARRETRATO,
                    "vista_l": 1400, "vista_a": 788}, attendi=True)
                if not isinstance(r, dict) or "campioni" not in r:
                    ko("⛔ il giro non ha reso campioni: %s" % str(r)[:300])
                    return 3
                dip = ritmi(r["campioni"], "dipinti")
                off = ritmi(r["campioni"], "offerti")
                med = statistics.median(dip) if dip else 0.0
                giri.append({"dipinti_al_s": stat(dip), "offerti_al_s": stat(off),
                             "mediana": round(med, 1), "conti": r["conti"],
                             "errori": r["errori"], "acceso": r["acceso"],
                             "dipinta": r["dipinta"], "dec": r["dec"]})
                inf("giro %d: ⭐ %5.1f dipinti/s (offerti %5.1f/s) · "
                    "dipinti=%d completi=%d ricomposizioni=%d errori=%d"
                    % (g + 1, med,
                       statistics.median(off) if off else 0.0,
                       r["conti"].get("dipinti", 0), r["conti"].get("completi", 0),
                       r["conti"].get("ricomposizioni", 0), len(r["errori"])))
                if r["errori"]:
                    ko("⛔ errori nella pagina: %s" % r["errori"][:2])
            mediane = [g["mediana"] for g in giri]
            v["esiti"][modo] = {"giri": giri, "mediane": mediane,
                                "mediana_dei_giri": round(statistics.median(mediane), 1)}
            ok("⭐ «%s»: mediane dei giri %s → %.1f dipinti/s"
               % (modo, mediane, statistics.median(mediane)))

        # ── il confronto ────────────────────────────────────────────────────
        log("⭐ IL CONFRONTO — e si stampano tutt'e due le grandezze")
        pr = v["esiti"]["principale"]["mediana_dei_giri"]
        wo = v["esiti"]["worker"]["mediana_dei_giri"]
        v["confronto"] = {
            "principale_dipinti_al_s": pr, "worker_dipinti_al_s": wo,
            "differenza": round(wo - pr, 1),
            "per_cento": round(100.0 * (wo - pr) / pr, 1) if pr else None,
            "dispersione_fra_giri": {
                "principale": round(max(v["esiti"]["principale"]["mediane"])
                                    - min(v["esiti"]["principale"]["mediane"]), 1),
                "worker": round(max(v["esiti"]["worker"]["mediane"])
                                - min(v["esiti"]["worker"]["mediane"]), 1)},
        }
        print()
        print("      strada          dipinti/s (mediana dei %d giri)   i giri"
              % a.giri)
        for modo in ("principale", "worker"):
            e = v["esiti"][modo]
            print("      %-14s  %25.1f   %s"
                  % (modo, e["mediana_dei_giri"], e["mediane"]))
        d = v["confronto"]
        print()
        # ⛔ La dispersione fra giri e' il metro della differenza: se la
        #    differenza non la supera, NON si dice che c'e' una differenza.
        disp = max(d["dispersione_fra_giri"]["principale"],
                   d["dispersione_fra_giri"]["worker"])
        if abs(d["differenza"]) <= disp:
            inf("⚠ differenza %+.1f dipinti/s, dispersione fra giri %.1f ⇒ "
                "NON si distingue dal rumore: le due strade dipingono lo stesso"
                % (d["differenza"], disp))
            v["confronto"]["verdetto"] = "indistinguibili"
        elif d["differenza"] < 0:
            ko("⛔ il worker DIPINGE MENO: %+.1f dipinti/s (%.1f %%) — "
               "`LEZIONI.md` §6.2, un guadagno che si paga in fluidita' non e' "
               "un guadagno" % (d["differenza"], d["per_cento"]))
            v["confronto"]["verdetto"] = "il worker peggiora il tetto"
        else:
            ok("⭐ il worker dipinge di piu': %+.1f dipinti/s (%.1f %%)"
               % (d["differenza"], d["per_cento"]))
            v["confronto"]["verdetto"] = "il worker alza il tetto"
    finally:
        palco.spegni()
        sito.shutdown()
    os.makedirs(os.path.dirname(a.verbale), exist_ok=True)
    with open(a.verbale, "w") as f:
        json.dump(v, f, indent=1, ensure_ascii=False)
    with open(os.path.join(QUI, "03-b19-dipinti-esiti.jsonl"), "a") as f:
        f.write(json.dumps(v, ensure_ascii=False) + "\n")
    inf("verbale: %s" % a.verbale)
    # ⛔ L'esito nel codice d'uscita: vedi il riquadro sopra `ko()`.  Il verbale
    #    si scrive PRIMA e comunque — un rosso non e' una ragione per buttare la
    #    misura che l'ha prodotto.
    return 1 if ROSSI else 0


if __name__ == "__main__":
    sys.exit(principale())
