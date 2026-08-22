#!/usr/bin/env python3
"""03-b19-dipinti-worker.py — ⭐ I FOTOGRAMMI DIPINTI, con e senza il worker.

    python3 banchi/03-b19-dipinti-worker.py --giri 3
    python3 banchi/03-b19-dipinti-worker.py --giri 3 --seq av1-1280x720
    python3 banchi/03-b19-dipinti-worker.py --certifica       ⭐ il controllo positivo
    python3 banchi/03-b19-dipinti-worker.py --guasto zero-worker

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

═══════════════════════════════════════════════════════════════════════════════
⛔⛔⭐ ZERO CONTRO ZERO NON E' UN PAREGGIO — cura del 22 agosto 2026
═══════════════════════════════════════════════════════════════════════════════

⛔ **IL DIFETTO, con la sua data.**  `[M]` 21 agosto 2026, 21:10, sequenza
   `av1-1920x1080`, due giri per lato: **0 dipinti da tutt'e due le parti** —
   `dipinti` 0, `acceso` **false**, `dipinta` **null**, `saltati_coda` 1911 e
   1701 — e questo banco ha stampato

       `--  ⚠ differenza +0.0 dipinti/s, dispersione fra giri 0.0 ⇒ NON si
             distingue dal rumore: le due strade dipingono lo stesso`

   uscendo **0**, cioe' VERDE.  ⛔ E prima di quella riga aveva scritto due volte
   `OK  ⭐ «…»: mediane dei giri [0.0, 0.0] → 0.0 dipinti/s`.

⛔ E' esattamente `LEZIONI.md` §1.20: **la misura era giusta, il numero era li',
   e nessuna riga lo confrontava con niente.**  Il banco raccoglieva `acceso`,
   `dipinta`, `dec` e `saltati_coda`, li scriveva nel verbale — e non li
   guardava mai.  Nessun **limite inferiore**: due zeri uguali fra loro
   passavano per «le due strade si equivalgono».

⭐ **PERCHE' A 1920x1080 NON SI PUO' MISURARE, e a 854x480 si.**  Il prodotto ha
   preso l'ancora `F4-CODA-DEL-DECODIFICATORE` (`src/pagina.html`, `dipingi()`):
   se `dec.decodeQueueSize > 2` **il disegno si salta** e si conta in
   `conti.saltati_coda`.  ⇒ Un alimentatore che SATURA — che e' il mestiere di
   questo banco — a 1080p tiene la coda del decodificatore sempre sopra 2, e
   **ogni** fotogramma viene saltato al disegno.  `[M]` 21 agosto: `completi`
   2307 · `dipinti` 0 · `saltati_coda` 1911 · `offerti` ~230/s (la stessa
   portata del caso 854x480: la briglia dell'arretrato non entra nemmeno in
   funzione, perche' `completi` sale lo stesso).

   ⇒ A 1080p questo banco **non misura piu' il tetto del disegno**: misura la
     soglia di scarto della coda.  ⛔ E la risposta giusta non e' allargare una
     soglia ne' spegnere la cura del prodotto: e' **dire che non si e' misurato
     niente, e perche'** — `CODER.md` §3.10, «zero e fallimento non hanno lo
     stesso aspetto».

⭐ **A 854x480 il banco regge**, e quel caso resta il numero buono: `[M]` 21
   agosto 2026, 21:11 — `saltati_coda` 3-6 su ~2300 (0,2 %), `acceso` true,
   `bitmaprenderer` contro il vecchio disegno 2D **−18,9 %** (contro il −75,5 %
   del 13 agosto).

⛔ **LE TRE COSE CHE ADESSO SI CONFRONTANO**, e sono scritte in cima come
   soglie invece che sparse nel codice:

   | il numero | la riga che lo giudica |
   |---|---|
   | `acceso` | falso ⇒ il palco non si e' MAI acceso: giro **non misurabile** |
   | `dipinti/s` | sotto `DIPINTI_MINIMI` ⇒ non c'e' niente da confrontare |
   | `saltati_coda` | sopra `SALTATI_TETTO` degli offerti ⇒ si misurava lo scarto |
   | `dec` | diverso dalla misura della sequenza ⇒ non si confrontano due uguali |
   | i conti sporchi | `buchi`/`scartati_*`/`corti`/`azzerati` non zero |

   ⇒ **Un giro non misurabile non produce mai un OK.**  E il verdetto finale ha
     tre esiti invece di uno:

     - **tutt'e due** le strade non misurabili ⇒ uscita **3**, «non ho potuto
       misurare», col motivo scritto;
     - **una sola** ⇒ uscita **1**, ROSSO: lo stesso alimentatore, gli stessi
       fotogrammi, e una strada dipinge e l'altra no;
     - tutt'e due misurabili ⇒ il confronto di prima, invariato.

⭐ **E IL CONTROLLO POSITIVO — `--certifica`, `PIANO.md` §0.3 punto 4.**  Tre
   giri veri con l'esito ATTESO scritto prima e **confrontato** (non stampato):

   | caso | `--guasto` | atteso |
   |---|---|---|
   | sano | — | il banco **MISURA** (uno dei tre verdetti), e NON esce 3 |
   | una strada dipinge zero | `zero-worker` | uscita **1**, verdetto «una strada sola» |
   | zero contro zero | `zero-tutt-e-due` | uscita **3**, «NON MISURATO» |

   ⛔ Il guasto si innesta nell'ALIMENTATORE, non nel prodotto: la strada scelta
      riceve i fotogrammi «offerti» e non se li vede consegnare mai.  ⚠ E' il
      guasto piu' fedele al difetto del 21 agosto — i byte ci sono, la pagina e'
      viva, e sulla tela non arriva niente.
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
# ⛔ I LIMITI INFERIORI — scritti QUI, in cima, e PRIMA del giro
#
# Il riquadro «zero contro zero non e' un pareggio» in testa al file dice
# perche' esistono.  ⚠ Stanno insieme alle altre soglie e non sparsi nel
# codice: una soglia che si trova solo leggendo il conto e' una soglia che si
# puo' spostare dopo aver visto il risultato.
# ═══════════════════════════════════════════════════════════════════════════
DIPINTI_MINIMI = 5.0   # dipinti/s sotto i quali non c'e' NIENTE da confrontare.
                       # ⭐ Il metro: i casi che hanno misurato davvero stanno a
                       #    187-235/s (854x480) e 34-128/s (1080p, 13 agosto);
                       #    quello che non ha misurato sta a 0,0.  Cinque e'
                       #    lontano da tutt'e due, e non serve piu' precisione.
SALTATI_TETTO = 0.25   # quanta parte dei fotogrammi arrivati al disegno la coda
                       # puo' saltare prima che «tetto del disegno» sia una
                       # bugia.  ⭐ Il metro, dallo stesso giro del 21 agosto:
                       #    854x480 (misura buona) 0,2 % · 1080p (misura nulla)
                       #    100 %.  ⇒ Fra i due c'e' un ordine di grandezza in
                       #    ogni verso: 25 % non taglia nessuno dei due per un
                       #    soffio.

# ⛔ I conti che DEVONO restare a zero perche' il confronto sia fra due cose
#    uguali.  ⚠ Erano nel verbale gia' prima, e nessuno li guardava.
CONTI_SPORCHI = ("buchi", "scartati_ordine", "scartati_misura", "corti",
                 "azzerati")

# ⭐ I guasti che si possono INNESTARE nell'alimentatore, per certificare che il
#    banco sa dire di no.  ⛔ Nessuno tocca il prodotto.
GUASTI = ("nessuno", "zero-principale", "zero-worker", "zero-tutt-e-due")


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
  /* ⛔ IL GUASTO INNESTATO — sta nell'ALIMENTATORE e in nessun altro posto.
     Se e' innestato su questa strada, il fotogramma si costruisce, si conta
     fra gli offerti e NON si consegna a nessuno: la pagina resta viva, il
     palco non si accende mai, `dipinti` resta 0.  ⭐ E' la forma esatta del
     difetto del 21 agosto, che il banco deve saper accusare. */
  const GUASTO = %(guasto)s;
  const INNESTATO = (GUASTO === "zero-tutt-e-due" || GUASTO === "zero-" + modo);
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
    if (INNESTATO) { try { rs.cancel(); } catch (e) { /* gia' chiuso */ } }
    else if (modo === "worker") VW.manda_flusso(rs);
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
           innestato: INNESTATO,
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


def carico():
    """⛔ Il carico accanto a ogni tempo: otto banchi sulla stessa macchina, e
    un numero senza il carico che c'era non si puo' rileggere fra una settimana."""
    try:
        with open("/proc/loadavg") as f:
            return f.read().split()[0:3] + [str(os.cpu_count()) + " cpu"]
    except Exception:                              # noqa: BLE001
        return ["?"]


def esamina_giro(g, seq_l, seq_a):
    """⛔⭐ LA RIGA CHE CONFRONTA — `LEZIONI.md` §1.20.

    Per ogni numero che il giro ha prodotto, qui c'e' la riga che lo giudica.
    Rende l'elenco dei motivi per cui il giro **non e' misurabile**: elenco
    vuoto = si puo' confrontare.  ⛔ Non stampa e non decide da sola quale
    uscita dare: quello lo fa `principale()`, che sa se una strada sola o
    tutt'e due sono cadute — e sono due esiti diversi (1 e 3)."""
    motivi = []
    c = g["conti"]
    dip = c.get("dipinti", 0)
    salt = c.get("saltati_coda", 0)

    # ⛔ «non ho campioni» e «ho campioni e valgono zero» sono cose diverse.
    if g["dipinti_al_s"].get("n", 0) == 0:
        motivi.append("nessun campione utile: il giro e' durato meno "
                      "dell'avvio che si butta (%d ms) — e' lo STRUMENTO"
                      % AVVIO_MS)
        return motivi

    if not g["acceso"]:
        motivi.append("il palco non si e' MAI acceso (`data-schermo` non e' "
                      "«acceso»): sulla tela non e' arrivato un fotogramma")
    if g["dipinta"] is None:
        motivi.append("`S.dipinta` e' nullo: `componi()` non e' mai passato")
    if g["mediana"] < DIPINTI_MINIMI:
        motivi.append("%.1f dipinti/s, sotto il minimo di %.1f: non c'e' "
                      "niente da confrontare" % (g["mediana"], DIPINTI_MINIMI))
    if salt and salt > SALTATI_TETTO * (salt + dip):
        motivi.append("`saltati_coda` %d su %d arrivati al disegno (%.0f %%, "
                      "tetto %.0f %%): l'ancora F4-CODA-DEL-DECODIFICATORE "
                      "butta il disegno perche' l'alimentatore satura — quel "
                      "che si misurerebbe e' la soglia di scarto, non il tetto"
                      % (salt, salt + dip, 100.0 * salt / (salt + dip),
                         100.0 * SALTATI_TETTO))
    if list(g["dec"] or []) != [seq_l, seq_a]:
        motivi.append("il decodificatore si e' configurato a %s invece che a "
                      "%dx%d: le due strade non porterebbero la stessa misura"
                      % (g["dec"], seq_l, seq_a))
    sporchi = ["%s=%d" % (k, c[k]) for k in CONTI_SPORCHI if c.get(k)]
    if sporchi:
        motivi.append("il flusso non e' pulito (%s): il tetto misurato non e' "
                      "di una catena sana" % ", ".join(sporchi))
    return motivi


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


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⛔ IL CONTROLLO POSITIVO — `PIANO.md` §0.3 punto 4, `LEZIONI.md` §1.2 e §1.9
#
# Tre giri veri, con **l'esito atteso scritto qui, prima**, e — la parte che
# §1.20 dice che si dimentica — **confrontato**, non stampato.
#
# ⚠ Il caso «sano» NON dichiara un'uscita sola, e la ragione va detta: se il
#   prodotto vero avesse una differenza fra le due strade uscirebbe **1**, se
#   non l'avesse **0**, e tutt'e due sono risposte legittime di uno strumento
#   che funziona.  ⛔ Quel che si certifica li' e' un'altra cosa: che il banco
#   **abbia misurato**, cioe' che il verdetto sia uno dei tre del confronto e
#   non un «non misurato».  ⇒ L'atteso e' sul VERDETTO, e sull'uscita si
#   pretende solo «diversa da 3».
# ═══════════════════════════════════════════════════════════════════════════
MISURANTI = ("indistinguibili", "il worker alza il tetto",
             "il worker peggiora il tetto")

CASI = (
    ("sano — il banco sa dire di SI'", "nessuno",
     None, MISURANTI,
     "su dati che si possono misurare il banco MISURA"),
    ("una strada dipinge zero", "zero-worker",
     1, ("una strada sola ha misurato",),
     "⛔ e' il guasto che il 21 agosto sarebbe passato: deve essere ROSSO"),
    ("zero contro zero", "zero-tutt-e-due",
     3, ("NON MISURATO: nessuna delle due strade",),
     "⛔ due zeri uguali NON sono un pareggio: «non ho potuto misurare»"),
)


def certifica(a):
    """⛔ Gira il banco per davvero, tre volte, e CONFRONTA l'esito con quello
    scritto sopra.  ⚠ Per sottoprocesso e non in linea: quel che si certifica
    e' il **codice d'uscita visto da fuori**, che e' il bit su cui
    `01-b12-guasti.py --giudica` giudichera'."""
    log("⭐ IL CONTROLLO POSITIVO DI `03-b19-dipinti-worker.py`")
    inf("sequenza %s · %d giri da %g s per lato · carico %s"
        % (a.seq, a.giri, a.secondi, carico()))
    inf("⛔ il guasto sta nell'ALIMENTATORE del banco: il prodotto non si tocca")
    esiti, storti = [], 0
    for i, (nome, guasto, uscita_attesa, verdetti_attesi, perche) in enumerate(CASI):
        log("caso %d/%d — %s" % (i + 1, len(CASI), nome))
        inf(perche)
        lav = os.path.join(a.lavoro, "certifica-%d" % i)
        verb = os.path.join(lav, "verbale.json")
        # ⛔ Uno schermo, una porta e una porta di diagnosi PER CASO: Xvfb non
        #    sempre toglie il suo socket, e `Palco.accendi()` rifiuta di partire
        #    su uno schermo occupato — cosa giusta, che qui si rispetta invece
        #    di aggirarla.
        cmd = [sys.executable, os.path.abspath(__file__),
               "--seq", a.seq, "--giri", str(a.giri),
               "--secondi", str(a.secondi),
               "--schermo", ":%d" % (int(a.schermo.lstrip(":")) + i),
               "--porta", str(a.porta + i), "--diagnosi", str(a.diagnosi + i),
               "--lavoro", lav, "--verbale", verb, "--guasto", guasto]
        t0 = time.time()
        r = subprocess.run(cmd, capture_output=True, text=True)
        dt = time.time() - t0
        verdetto = None
        try:
            with open(verb) as f:
                verdetto = json.load(f)["confronto"]["verdetto"]
        except Exception as e:                     # noqa: BLE001
            inf("⚠ verbale illeggibile: %s" % e)
        inf("uscita %d · verdetto «%s» · %.0f s · carico %s"
            % (r.returncode, verdetto, dt, carico()))

        # ⛔⭐ LE DUE RIGHE CHE CONFRONTANO.  Senza di queste, tutto il lavoro
        #    qui sopra sarebbe §1.20 dentro il certificatore stesso.
        male = []
        if uscita_attesa is None:
            if r.returncode == 3:
                male.append("l'uscita e' 3 («non ho potuto misurare») e qui il "
                            "banco DOVEVA misurare")
        elif r.returncode != uscita_attesa:
            male.append("uscita %d, attesa %d" % (r.returncode, uscita_attesa))
        if verdetto not in verdetti_attesi:
            male.append("verdetto «%s», atteso uno di %s"
                        % (verdetto, list(verdetti_attesi)))
        if male:
            storti += 1
            ko("⛔ «%s»: %s" % (nome, " · ".join(male)))
            for riga in (r.stdout or "").splitlines()[-12:]:
                print("        %s" % riga)
            for riga in (r.stderr or "").splitlines()[-6:]:
                print("        ⚠ %s" % riga)
        else:
            ok("«%s»: uscita %d, verdetto «%s» — come scritto prima"
               % (nome, r.returncode, verdetto))
        esiti.append({"caso": nome, "guasto": guasto,
                      "uscita": r.returncode, "uscita_attesa": uscita_attesa,
                      "verdetto": verdetto, "verdetti_attesi": list(verdetti_attesi),
                      "secondi": round(dt, 1), "giusto": not male})

    log("⭐ L'ESITO DELLA CERTIFICAZIONE")
    print("      %-34s %-8s %s" % ("caso", "uscita", "verdetto"))
    for e in esiti:
        print("      %-34s %-8s %s  %s"
              % (e["caso"][:34], e["uscita"], e["verdetto"],
                 "OK" if e["giusto"] else "⛔ STORTO"))
    reg = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "certificazione": True,
           "seq": a.seq, "giri": a.giri, "secondi": a.secondi,
           "carico": carico(), "casi": esiti,
           "esito": "%d su %d" % (len(esiti) - storti, len(esiti))}
    with open(a.esiti, "a") as f:
        f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    if storti:
        ko("⛔ %d casi su %d NON hanno dato l'esito scritto prima: questo banco "
           "NON e' certificato, e i suoi numeri non si citano"
           % (storti, len(esiti)))
        return 1
    ok("⭐ %d casi su %d: il banco sa dire di si', sa accusare una strada che "
       "dipinge zero, e NON chiama pareggio due zeri" % (len(esiti), len(esiti)))
    return 0


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
    p.add_argument("--guasto", default="nessuno", choices=GUASTI,
                   help="⭐ innesta un guasto NELL'ALIMENTATORE, per "
                        "certificare che il banco sa dire di no")
    p.add_argument("--certifica", action="store_true",
                   help="⭐ il controllo positivo: tre giri con l'esito "
                        "atteso scritto prima e CONFRONTATO")
    p.add_argument("--esiti", default=os.path.join(QUI,
                                                   "03-b19-dipinti-esiti.jsonl"))
    a = p.parse_args()

    if a.certifica:
        # ⛔ La certificazione gira sulla sequenza che SI PUO' misurare, e con
        #    giri corti: e' una prova dello STRUMENTO, non una misura del
        #    prodotto.  ⚠ E solo se chi chiama non ha detto altro.
        if a.seq == p.get_default("seq"):
            a.seq = "av1-854x480"
        if a.giri == p.get_default("giri"):
            a.giri = 2
        if a.secondi == p.get_default("secondi"):
            a.secondi = 6.0
        return certifica(a)

    print(__doc__.split("═══")[0])
    # ⛔ La misura della sequenza si legge QUI, dal file, e non si prende da
    #    quel che la pagina dichiara: se la si prendesse da li' il confronto
    #    «il decodificatore si e' configurato bene» sarebbe la pagina che si
    #    da' ragione da sola.
    with open(os.path.join(SEQUENZE, a.seq + ".json")) as f:
        _s = json.load(f)
    seq_l, seq_a = _s["larghezza"], _s["altezza"]
    del _s
    sito = Sito(("127.0.0.1", a.porta), Servente)
    threading.Thread(target=sito.serve_forever, daemon=True).start()
    palco = Palco(a.schermo, a.diagnosi, os.path.join(a.lavoro, "palco"))
    v = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S"), "seq": a.seq,
         "secondi": a.secondi, "giri": a.giri, "arretrato": ARRETRATO,
         "guasto": a.guasto, "carico": carico(),
         "soglie": {"dipinti_minimi": DIPINTI_MINIMI,
                    "saltati_tetto": SALTATI_TETTO},
         "sorgente": SORGENTE, "esiti": {}}
    if a.guasto != "nessuno":
        inf("⭐ GUASTO INNESTATO NELL'ALIMENTATORE: «%s» — questo giro NON e' "
            "una misura del prodotto" % a.guasto)
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
                    "guasto": json.dumps(a.guasto),
                    "vista_l": 1400, "vista_a": 788}, attendi=True)
                if not isinstance(r, dict) or "campioni" not in r:
                    ko("⛔ il giro non ha reso campioni: %s" % str(r)[:300])
                    return 3
                dip = ritmi(r["campioni"], "dipinti")
                off = ritmi(r["campioni"], "offerti")
                med = statistics.median(dip) if dip else 0.0
                g_v = {"dipinti_al_s": stat(dip), "offerti_al_s": stat(off),
                       "mediana": round(med, 1), "conti": r["conti"],
                       "errori": r["errori"], "acceso": r["acceso"],
                       "dipinta": r["dipinta"], "dec": r["dec"],
                       "innestato": r.get("innestato", False)}
                # ⛔⭐ QUI, e non nel verbale: ogni numero che la riga qui sotto
                #    STAMPA trova adesso una riga che lo GIUDICA (§1.20).
                g_v["motivi"] = esamina_giro(g_v, seq_l, seq_a)
                giri.append(g_v)
                inf("giro %d: ⭐ %5.1f dipinti/s (offerti %5.1f/s) · "
                    "dipinti=%d completi=%d saltati_coda=%d acceso=%s errori=%d"
                    % (g + 1, med,
                       statistics.median(off) if off else 0.0,
                       r["conti"].get("dipinti", 0), r["conti"].get("completi", 0),
                       r["conti"].get("saltati_coda", 0),
                       "si" if r["acceso"] else "NO", len(r["errori"])))
                if r["errori"]:
                    ko("⛔ errori nella pagina: %s" % r["errori"][:2])
                for m in g_v["motivi"]:
                    inf("   ⚠ giro %d NON misurabile: %s" % (g + 1, m))
            mediane = [g["mediana"] for g in giri]
            # ⛔ Una strada e' misurabile solo se lo sono TUTTI i suoi giri: con
            #    un giro caduto, la dispersione fra giri — che e' il metro della
            #    differenza — non vuol piu' dire niente.
            caduti = [i + 1 for i, g in enumerate(giri) if g["motivi"]]
            v["esiti"][modo] = {
                "giri": giri, "mediane": mediane,
                "mediana_dei_giri": round(statistics.median(mediane), 1),
                "misurabile": not caduti, "giri_caduti": caduti,
                "motivi": sorted({m for g in giri for m in g["motivi"]})}
            if caduti:
                # ⛔ E QUI NON SI DICE «OK».  Era la prima delle due frasi verdi
                #    del 21 agosto: `OK  «principale»: mediane [0.0, 0.0] → 0.0`.
                inf("⛔ «%s» NON E' MISURABILE — giri caduti: %s (su %d)"
                    % (modo, caduti, a.giri))
            else:
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
        print("      strada          dipinti/s (mediana dei %d giri)   misurabile"
              % a.giri)
        for modo in ("principale", "worker"):
            e = v["esiti"][modo]
            print("      %-14s  %25.1f   %s   %s"
                  % (modo, e["mediana_dei_giri"],
                     "si " if e["misurabile"] else "⛔NO", e["mediane"]))
        d = v["confronto"]
        print()

        # ⛔⭐ IL BIVIO CHE MANCAVA — «zero contro zero non e' un pareggio».
        buone = [m for m in ("principale", "worker") if v["esiti"][m]["misurabile"]]
        if len(buone) < 2:
            perdute = [m for m in ("principale", "worker")
                       if not v["esiti"][m]["misurabile"]]
            for m in perdute:
                for t in v["esiti"][m]["motivi"]:
                    inf("⛔ «%s»: %s" % (m, t))
            if not buone:
                # ⛔ NON un rosso e NON un verde: «non ho potuto misurare».
                #    `CODER.md` §3.10 — e non si arrotonda con l'1.
                inf("⛔⛔ NON HO MISURATO NIENTE: nessuna delle due strade ha "
                    "dipinto.  ⚠ Un confronto fra due zeri non e' un pareggio, "
                    "e questo banco NON dice che le due strade si equivalgono.")
                v["confronto"]["verdetto"] = "NON MISURATO: nessuna delle due strade"
                v["uscita"] = 3
            else:
                # ⛔ Stesso alimentatore, stessi fotogrammi, stesso secondo: se
                #    una strada dipinge e l'altra no, la differenza e' NELLA
                #    STRADA.  E' un rosso, non un «non ho potuto».
                ko("⛔ UNA STRADA SOLA HA MISURATO: «%s» dipinge %.1f/s e «%s» "
                   "NON dipinge affatto — stesso alimentatore, stessi "
                   "fotogrammi, stesso palco" % (buone[0],
                                                 v["esiti"][buone[0]]["mediana_dei_giri"],
                                                 perdute[0]))
                v["confronto"]["verdetto"] = "una strada sola ha misurato"
                v["uscita"] = 1
        else:
            # ⛔ La dispersione fra giri e' il metro della differenza: se la
            #    differenza non la supera, NON si dice che c'e' una differenza.
            disp = max(d["dispersione_fra_giri"]["principale"],
                       d["dispersione_fra_giri"]["worker"])
            if abs(d["differenza"]) <= disp:
                inf("⚠ differenza %+.1f dipinti/s, dispersione fra giri %.1f ⇒ "
                    "NON si distingue dal rumore: le due strade dipingono lo "
                    "stesso" % (d["differenza"], disp))
                v["confronto"]["verdetto"] = "indistinguibili"
            elif d["differenza"] < 0:
                ko("⛔ il worker DIPINGE MENO: %+.1f dipinti/s (%.1f %%) — "
                   "`LEZIONI.md` §6.2, un guadagno che si paga in fluidita' non "
                   "e' un guadagno" % (d["differenza"], d["per_cento"]))
                v["confronto"]["verdetto"] = "il worker peggiora il tetto"
            else:
                ok("⭐ il worker dipinge di piu': %+.1f dipinti/s (%.1f %%)"
                   % (d["differenza"], d["per_cento"]))
                v["confronto"]["verdetto"] = "il worker alza il tetto"
            v["uscita"] = 1 if ROSSI else 0
    finally:
        palco.spegni()
        sito.shutdown()
    v.setdefault("uscita", 1 if ROSSI else 0)
    # ⛔ Un ROSSO di pagina (`errori`) vince su un 3: e' un fatto osservato, non
    #    un «non ho potuto».
    if ROSSI and v["uscita"] == 3:
        v["uscita"] = 1
    os.makedirs(os.path.dirname(a.verbale), exist_ok=True)
    with open(a.verbale, "w") as f:
        json.dump(v, f, indent=1, ensure_ascii=False)
    # ⛔ Un giro col GUASTO INNESTATO non entra nel registro delle misure: e'
    #    una prova dello strumento, e mescolarla ai numeri del prodotto
    #    vorrebbe dire lasciare in archivio una misura che non e' del prodotto.
    if a.guasto == "nessuno":
        with open(a.esiti, "a") as f:
            f.write(json.dumps(v, ensure_ascii=False) + "\n")
    inf("verbale: %s · carico %s" % (a.verbale, v["carico"]))
    # ⛔ L'esito nel codice d'uscita: vedi il riquadro sopra `ko()`.  Il verbale
    #    si scrive PRIMA e comunque — un rosso non e' una ragione per buttare la
    #    misura che l'ha prodotto.
    return v["uscita"]


if __name__ == "__main__":
    sys.exit(principale())
