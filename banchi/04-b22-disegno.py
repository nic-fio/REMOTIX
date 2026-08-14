#!/usr/bin/env python3
"""04-b22-disegno.py — ⛔ IL TRATTO DEL DISEGNO, **SCOMPOSTO**, non un totale.

    python3 banchi/04-b22-disegno.py                il giro
    python3 banchi/04-b22-disegno.py --certifica    sano → guasto → risanato
    python3 banchi/04-b22-disegno.py --json FILE    deposita il verbale

===========================================================================
⛔ PERCHE' ESISTE — la tesi da refutare

`fasi/rapporti/F3-E-anello-rimisurato.md`, `[M]` 13-14 agosto 2026:

    | tratto (mediane, ms) | C AV1 sw | A HEVC sw | D HEVC hw (deposito) |
    | 6 **il disegno**     |  9,070   |  28,985   | ⛔ **27,995**        |
    | 7 TOTALE             | 71,862   | 109,770   |     78,115           |

⇒ **28,0 ms su 78,1 — il 36 %** — contro i **5 ms** che ormai costa la
  codifica in hardware.  ⛔ **E non era in nessun piano.**

⚠ E quel rapporto dichiara onestamente di non sapere il PERCHE':

    «`[?]` PERCHE' il disegno triplichi con HEVC, questa misura non lo dice.
     L'ipotesi naturale e' che la decodifica HEVC in hardware consegni un
     fotogramma **che vive sulla GPU**… ⛔ **E' una lettura, non una misura**:
     il banco misura *quando* il tempo passa, non *dove*.»

⇒ **Questo banco misura DOVE.**

===========================================================================
⛔ CHE COS'E' «IL DISEGNO», ESATTAMENTE

Il tratto 6 di `03-b17-ritardo.py:1786` e' *«richiamo → disegno finito
(`drawImage` ×2)»*, cioe' la durata di `Schermo.dipingi(f)` in
`src/pagina.html:1839`.  Dentro ci sono **quattro** cose e non una:

    1. `deposito_p.drawImage(f, 0, 0)`      il fotogramma → il deposito
                                            (`pagina.html:1863`)
    2. `f.close()`                          il fotogramma si rilascia
    3. `pennello.fillRect(...)`             le bande, quando servono
                                            (`pagina.html:1443`)
    4. `pennello.drawImage(deposito, …)`    il deposito → la tela, RISCALATO
                                            (`pagina.html:1446`)

⛔ **Un totale non dice quale delle quattro.**  E le cure sono opposte: se e'
   la 1, si toglie il deposito o si cambia strada al fotogramma; se e' la 4,
   si tocca il riscalamento; se e' la 3, si dipingono le bande una volta sola.

===========================================================================
⛔⛔ DOVE FINISCE LA MISURA — e il confine si sposta nella direzione SCOMODA

`CODER.md` §1-bis: *«la misura finisce al DISEGNO FINITO, non al richiamo del
decodificatore»*, e *«ogni confine ha due posizioni difendibili, e quella che
favorisce chi misura si sceglie da se' se nessuno la nomina»*.

⛔ **Qui il confine ha ANCORA due posizioni**, e nessuna delle due e' gratis:

  | confine | che cosa misura | perche' non basta |
  |---|---|---|
  | **il ritorno di `drawImage`** | quanto sta il JavaScript fermo | ⛔ `drawImage` su una tela 2D **puo' tornare prima che il lavoro sia fatto**: Chrome accoda |
  | ⭐ **la tela LEGGIBILE** (`getImageData` 1×1) | il lavoro **finito davvero** | ⚠ forzare la lettura CAMBIA la cosa misurata: una tela riletta ogni fotogramma puo' cambiare di sostrato |

⇒ ⭐ **Si misurano tutt'e due, ogni giro, e si scrivono ACCANTO.**  Il numero
  del banco e' quello **scomodo** — la tela leggibile — e l'altro sta di
  fianco come il numero che il metro di `03-b17` produce oggi.

⛔ **E il PEZZO CIECO resta fuori da tutt'e due**: fra la tela leggibile e il
  pixel acceso passano `[?]` **16-40 ms** che nessuna API vede (`web.md` §6.2,
  `CODER.md` §1-bis).  Si dichiara accanto a ogni numero — ⭐ **e qui esiste**,
  perche' questo banco gira sul **desktop vero**, non su Xvfb.

===========================================================================
⛔ LA SCENA SI DICHIARA E SI MUOVE SEMPRE — `CODER.md` §3.2

`testsrc2` a 1920×1080, che cambia **a ogni fotogramma**.  Una chiave e N
delta, e i delta sono la maggioranza: e' quel che fa il prodotto.

⛔ E SI SCARTA L'AVVIO — `CODER.md` §3.5.  I primi fotogrammi sono l'avvio:
   il decodificatore si sveglia, la tela si alloca, il sostrato si decide.  La
   mediana si prende sulla **seconda meta'**, e la prima meta' si stampa
   accanto: se le due sono uguali non c'era transitorio, e si vede.

===========================================================================
⛔ IL CONTROLLO POSITIVO — `CODER.md` §3.10

Ogni giro porta con se' **AV1 a 8 bit**, che il rapporto della fase 3 misura a
**9,1 ms**: se anche quello uscisse a 28, il banco starebbe misurando se
stesso.  ⇒ ⭐ **La domanda «questo cronometro sa vedere un disegno che costa
poco?» ha una risposta nello stesso giro, non in un altro.**

E ogni misura distingue **zero** da **fallimento**: un caso che non consegna
fotogrammi esce `n = 0` con il motivo scritto, non «0,0 ms».

===========================================================================
⛔ LA CERTIFICAZIONE — sano → guasto → risanato

    sano       il controllo positivo (AV1 8 bit) sta sotto la soglia, e i
               fotogrammi contati sono quelli offerti
    guasto     `GUASTO=disegno-lento` mette un ciclo di attesa di 10 ms DENTRO
               il tratto 1 ⇒ la scomposizione DEVE accusare il tratto 1, e non
               un altro.  ⛔ Un banco che desse la colpa al tratto 4 misurando
               un guasto nel tratto 1 non saprebbe scomporre niente
    guasto     `GUASTO=niente-fotogrammi` non consegna niente al decodificatore
               ⇒ `n = 0` **con il motivo**, e il banco NON deve dire «0,0 ms»
    risanato   come il sano
"""
import argparse
import base64
import http.server
import importlib.util
import json
import os
import shutil
import socketserver
import statistics
import subprocess
import sys
import tempfile
import threading
import time

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ Porte MIE — l'anello A2 ha 7611-7615 (`fasi/04-si-comanda.md:43`).
PORTA_HTTP = 7612
PORTA_CDP = 7613

# ⛔ Il pezzo cieco, dichiarato accanto a OGNI numero e mai dentro.
PEZZO_CIECO = (16.0, 40.0)

_moduli = {}


def carica(nome, percorso):
    if nome in _moduli:
        return _moduli[nome]
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    _moduli[nome] = m
    return m


def cdp_modulo():
    return carica("cdp", os.path.join(QUI, "02-pagina-misura-cdp.py"))


def ok(t):
    print("\033[1;32mOK\033[0m  " + t)


def ko(t):
    print("\033[1;31mNO\033[0m  " + t)


def dub(t):
    print("\033[1;33m??\033[0m  " + t)


def inf(t):
    print("    " + t)


def tit(t):
    print("\n\033[1m== " + t + "\033[0m")


# ═══════════════════════════════════════════════════════════════════════════
# §1  LA SCENA — dichiarata, e in movimento a ogni fotogramma
# ═══════════════════════════════════════════════════════════════════════════
def sequenza(codec, profondita, l, a, quanti, guasto=""):
    """Una chiave e `quanti-1` delta di `testsrc2`, in Annex-B (HEVC) o OBU
    (AV1) — le stesse due forme di confezionamento che usa il prodotto
    (`src/pagina.html:635`, nessuna `description`).

    ⛔ Ritorna anche la LUNGHEZZA di ogni fotogramma: senza, la pagina non
       saprebbe dove finisce l'uno e comincia l'altro, e un banco che
       consegnasse due fotogrammi in un chunk misurerebbe un'altra cosa."""
    if guasto == "niente-fotogrammi":
        return [], "guasto innestato: nessun fotogramma costruito"
    pix = "yuv420p10le" if profondita == 10 else "yuv420p"
    comune = [
        "ffmpeg", "-hide_banner", "-nostdin", "-y",
        "-f", "lavfi", "-i", "testsrc2=size=%dx%d:rate=30" % (l, a),
        "-frames:v", str(quanti), "-pix_fmt", pix,
    ]
    if codec == "hevc":
        cmd = comune + [
            "-c:v", "libx265",
            # ⛔ Il profilo si CHIEDE PER NOME e si VERIFICA nei byte piu' sotto
            #    (`02-pagina-sonda-codec.py:120`: chiesto e non applicato, senza
            #    un errore, e' costato il codec dell'intero prodotto).
            "-profile:v", "main10" if profondita == 10 else "main",
            "-x265-params",
            "log-level=none:bframes=0:info=0:keyint=%d:min-keyint=%d" % (quanti * 4, quanti * 4),
            "-f", "hevc", "pipe:1",
        ]
    else:
        cmd = comune + [
            "-c:v", "libsvtav1", "-preset", "10", "-crf", "35",
            "-svtav1-params", "keyint=%d" % (quanti * 4),
            "-f", "obu", "pipe:1",
        ]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0 or len(p.stdout) < 64:
        return [], p.stderr.decode("utf-8", "replace")[-300:]
    return spezza(p.stdout, codec), None


def spezza(flusso, codec):
    """⛔ I fotogrammi si separano **nei byte**, non contando.

    HEVC in Annex-B: un fotogramma nuovo comincia alla prima NAL con
    `first_slice_segment_in_pic_flag = 1` (il bit alto del byte dopo i due di
    intestazione) e tipo di NAL <= 31.  I parametri (VPS/SPS/PPS, 32-34) stanno
    davanti al fotogramma a cui appartengono.

    AV1: si taglia sulle unita' temporali (OBU di tipo 2, `TEMPORAL_DELIMITER`).
    """
    fuori = []
    if codec == "hevc":
        # gli offset di tutti gli start code
        off = []
        i = 0
        while True:
            j = flusso.find(b"\x00\x00\x01", i)
            if j < 0:
                break
            off.append(j)
            i = j + 3
        inizio = None
        for k, j in enumerate(off):
            testa = j + 3
            if testa + 2 > len(flusso):
                break
            tipo = (flusso[testa] >> 1) & 0x3F
            primo = tipo <= 31 and (flusso[testa + 2] & 0x80) != 0
            if primo:
                # il fotogramma comincia dai suoi parametri, se ci sono
                p = k
                while p > 0:
                    t = (flusso[off[p - 1] + 3] >> 1) & 0x3F
                    if t < 32:
                        break
                    p -= 1
                partenza = off[p]
                if inizio is not None:
                    fuori.append(flusso[inizio:partenza])
                inizio = partenza
        if inizio is not None:
            fuori.append(flusso[inizio:])
    else:
        i = 0
        inizio = None
        while i < len(flusso):
            b = flusso[i]
            tipo = (b >> 3) & 0x0F
            ha_misura = (b & 0x02) != 0
            j = i + 1
            if (b & 0x04) != 0:                 # obu_extension_flag
                j += 1
            if not ha_misura:
                break
            misura = 0
            spost = 0
            while j < len(flusso):
                c = flusso[j]
                misura |= (c & 0x7F) << spost
                j += 1
                spost += 7
                if not (c & 0x80):
                    break
            fine = j + misura
            if tipo == 2:                       # TEMPORAL_DELIMITER
                if inizio is not None:
                    fuori.append(flusso[inizio:i])
                inizio = i
            i = fine
        if inizio is not None:
            fuori.append(flusso[inizio:])
    return fuori


def profilo_nei_byte(pezzo, codec):
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(pezzo)
        p = f.name
    try:
        r = subprocess.run(["ffprobe", "-hide_banner", "-v", "error", "-f",
                            "hevc" if codec == "hevc" else "obu",
                            "-show_entries", "stream=profile,pix_fmt",
                            "-of", "json", p], capture_output=True, text=True)
        if r.returncode != 0:
            return None, None
        s = json.loads(r.stdout)["streams"][0]
        return s.get("profile"), s.get("pix_fmt")
    except Exception:                                          # noqa: BLE001
        return None, None
    finally:
        os.unlink(p)


# ═══════════════════════════════════════════════════════════════════════════
# §2  LA PAGINA — riproduce il percorso del prodotto, riga per riga
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ Il percorso e' copiato da `src/pagina.html:1839-1879` (`dipingi`) e
#    `:1431-1457` (`componi`), con i cronometri IN MEZZO.  ⚠ Non si chiama la
#    funzione del prodotto: per cronometrarne i quattro pezzi bisognerebbe
#    spezzarla, e spezzarla nel prodotto per misurarla e' cambiare la cosa
#    misurata.  ⇒ Il prezzo e' che le due copie possono divergere, e si paga
#    dichiarandolo qui: **se `pagina.html:1839` cambia, questo blocco va
#    riletto.**
PAGINA = r"""<!doctype html>
<html lang="it"><head><meta charset="utf-8"><title>04-b22 · il disegno</title>
<style>body{margin:0;background:#111}canvas{display:block}</style></head>
<body><canvas id="tela"></canvas><script>
const CASI = __CASI__;
const GUASTO = __GUASTO__;
/* ⛔⭐ LA LETTURA DEL BANCO — e non e' un dettaglio, e' l'ipotesi.
 *
 * `03-b17-ritardo.py:534` legge una regione di **480×240** dal DEPOSITO a
 * OGNI fotogramma (`leggi_marca_celle`), per ritrovare la marca a 144 bit.
 * Quel `getImageData` e' cronometrato A PARTE (`t_let − t_dip`) e **non entra
 * nel tratto 6**.
 * ⇒ Ma un `getImageData` ripetuto puo' cambiare il SOSTRATO della tela — da
 *   acceleratа a di CPU — e allora il costo non resta dove e' stato pagato:
 *   ricade su `drawImage(VideoFrame → deposito)` del fotogramma DOPO, cioe'
 *   **dentro** il tratto 6.  ⛔ Questa e' l'ipotesi, e la casella qui sotto la
 *   mette alla prova: stesso giro, stessa scena, una variabile sola. */
const LETTURA = __LETTURA__;   /* 0 = nessuna · N = una regione N×(N/2) */

function byte(b64) {
  const s = atob(b64); const u = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
  return u;
}

const tela = document.getElementById("tela");
/* ⛔ Le stesse opzioni del prodotto: `alpha: false` e NIENTE
   `willReadFrequently` — quest'ultimo cambierebbe il sostrato della tela, che
   e' precisamente la grandezza sotto esame (`pagina.html:1861`). */
let pennello = null, deposito = null, deposito_p = null;

function attesa(ms) {          /* il guasto: un'attesa VERA, non un mock */
  const f = performance.now() + ms;
  while (performance.now() < f) { /* gira */ }
}

function misura(caso) {
  return new Promise((risolvi) => {
    const pezzi = caso.pezzi.map(byte);
    tela.width = caso.vista_l; tela.height = caso.vista_a;
    tela.style.width = caso.vista_l + "px";
    tela.style.height = caso.vista_a + "px";
    pennello = tela.getContext("2d", { alpha: false });
    deposito = null; deposito_p = null;
    const campioni = [];
    let fatto = false, dec = null, mandati = 0;
    let formato = null, ultimo_errore = null;

    const sveglia = setTimeout(() => chiudi("nessun fotogramma entro 30 s"), 30000);
    function chiudi(perche) {
      if (fatto) return; fatto = true; clearTimeout(sveglia);
      try { if (dec && dec.state !== "closed") dec.close(); } catch (e) {}
      risolvi({ campioni: campioni, offerti: pezzi.length, mandati: mandati,
                formato: formato, perche: perche || null,
                errore: ultimo_errore });
    }

    /* ⭐ `dipingi()` del prodotto, spezzato nei suoi quattro pezzi. */
    function dipingi(f) {
      const t1 = performance.now();
      if (formato === null) formato = (f.format === undefined) ? "assente"
                                    : (f.format === null ? "nullo (opaco)" : f.format);
      const fl = f.displayWidth || f.codedWidth;
      const fa = f.displayHeight || f.codedHeight;
      /* ── 1. il fotogramma → il deposito ─────────────────────────────── */
      if (!deposito) deposito = document.createElement("canvas");
      if (deposito.width !== fl || deposito.height !== fa) {
        deposito.width = fl; deposito.height = fa;
        deposito_p = deposito.getContext("2d", { alpha: false });
      }
      const tA = performance.now();
      if (GUASTO === "disegno-lento") attesa(10);
      deposito_p.drawImage(f, 0, 0);
      const tB = performance.now();
      /* ── 2. il rilascio ─────────────────────────────────────────────── */
      try { f.close(); } catch (e) {}
      const tC = performance.now();
      /* ── 3. le bande e 4. il riscalamento (`componi`) ────────────────── */
      const cl = tela.width, ca = tela.height;
      const s = Math.min(cl / fl, ca / fa);
      const dl = Math.max(1, Math.round(fl * s)), da = Math.max(1, Math.round(fa * s));
      const dx = Math.floor((cl - dl) / 2), dy = Math.floor((ca - da) / 2);
      if (dl !== cl || da !== ca) {
        pennello.fillStyle = "#000";
        pennello.fillRect(0, 0, cl, ca);
      }
      const tD = performance.now();
      pennello.drawImage(deposito, dx, dy, dl, da);
      const tE = performance.now();
      /* ── ⛔ IL CONFINE SCOMODO: la tela LEGGIBILE, non `drawImage` tornato.
         Un `getImageData` di 1×1 costringe Chrome a finire quel che ha
         accodato.  ⚠ E cambia la cosa misurata: per questo il numero sta
         ACCANTO all'altro, non al posto suo. ───────────────────────────── */
      let tF = tE;
      try { pennello.getImageData(0, 0, 1, 1); tF = performance.now(); }
      catch (e) { tF = -1; }
      /* ⛔ LA LETTURA DEL BANCO, cronometrata A PARTE e FUORI dai tratti —
         esattamente come fa `03-b17-ritardo.py:476-482`.  Il suo effetto, se
         c'e', si vedra' sul fotogramma DOPO. */
      let tLet = 0;
      if (LETTURA > 0 && deposito.width >= LETTURA
          && deposito.height >= LETTURA / 2) {
        const g0 = performance.now();
        try { deposito_p.getImageData(0, 0, LETTURA, LETTURA / 2); }
        catch (e) { /* non ho potuto guardare */ }
        tLet = performance.now() - g0;
      }
      campioni.push({
        lettura_del_banco: tLet,
        prep: tA - t1, deposito: tB - tA, chiusura: tC - tB,
        bande: tD - tC, componi: tE - tD,
        fino_al_ritorno: tE - t1,
        fino_alla_tela_leggibile: tF < 0 ? null : (tF - t1),
      });
      if (campioni.length >= pezzi.length) chiudi(null);
    }

    try {
      dec = new VideoDecoder({
        output: dipingi,
        error: (e) => { ultimo_errore = String(e); chiudi("il decodificatore "
                        + "ha fallito: " + e); },
      });
      dec.configure({ codec: caso.stringa, codedWidth: caso.l,
                      codedHeight: caso.a, optimizeForLatency: true });
      for (let k = 0; k < pezzi.length; k++) {
        dec.decode(new EncodedVideoChunk({
          type: k === 0 ? "key" : "delta", timestamp: k * 33333,
          data: pezzi[k] }));
        mandati++;
      }
    } catch (e) { chiudi("configure/decode ha lanciato: " + e); }
  });
}

async function tutto() {
  const fuori = { casi: [] };
  for (const caso of CASI) {
    const r = await misura(caso);
    fuori.casi.push({ nome: caso.nome, codec: caso.codec,
                      profondita: caso.profondita, ruolo: caso.ruolo,
                      stringa: caso.stringa, l: caso.l, a: caso.a,
                      vista: caso.vista_l + "x" + caso.vista_a,
                      offerti: r.offerti, mandati: r.mandati,
                      formato: r.formato, perche: r.perche, errore: r.errore,
                      campioni: r.campioni });
  }
  const c = document.createElement("canvas").getContext("webgl");
  const dbg = c && c.getExtension("WEBGL_debug_renderer_info");
  fuori.palco = { screen: screen.width + "x" + screen.height,
                  dpr: devicePixelRatio,
                  finestra: innerWidth + "x" + innerHeight,
                  webgl: dbg ? c.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : "non letto",
                  ua: navigator.userAgent };
  window.B22 = fuori;
  document.body.dataset.b22 = "fatto";
}
tutto();
</script></body></html>
"""


class Servitore(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def servi(cartella, porta):
    class H(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k):
            super().__init__(*a, directory=cartella, **k)

        def log_message(self, *a):
            pass
    s = Servitore(("127.0.0.1", porta), H)
    threading.Thread(target=s.serve_forever, daemon=True).start()
    return s


class Palco:
    """⛔ Chrome sul desktop VERO, dichiarato e non spostato (`README.md:397`):
    HEVC in hardware vuole la GPU vera, e su Xvfb il pezzo cieco non esiste."""

    def __init__(self, finestra=(1400, 900)):
        self.t = tempfile.mkdtemp(prefix="04-b22-")
        self.finestra = finestra
        self.chrome = None
        self.c = None
        self.bandiere = []

    def accendi(self, url):
        l, a = self.finestra
        flag = ["google-chrome", "--user-data-dir=%s/profilo" % self.t,
                "--no-first-run", "--no-default-browser-check", "--disable-sync",
                "--remote-debugging-port=%d" % PORTA_CDP,
                "--remote-allow-origins=*",
                "--window-size=%d,%d" % (l, a), "--window-position=0,0", url]
        self.bandiere = list(flag)
        self.chrome = subprocess.Popen(flag, env=dict(os.environ),
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
        cdp = cdp_modulo()
        b = cdp.pagina(PORTA_CDP, attesa=40)
        self.c = cdp.Cdp(b["webSocketDebuggerUrl"], timeout=240)
        for m in ("Page.enable", "Runtime.enable"):
            self.c.chiama(m)
        return b

    def valuta(self, e):
        return self.c.valuta(e, attendi=False)

    def spegni(self):
        if self.chrome:
            try:
                self.chrome.terminate()
                self.chrome.wait(timeout=8)
            except Exception:                                  # noqa: BLE001
                try:
                    self.chrome.kill()
                except Exception:                              # noqa: BLE001
                    pass
        shutil.rmtree(self.t, ignore_errors=True)


# ═══════════════════════════════════════════════════════════════════════════
# §3  I NUMERI
# ═══════════════════════════════════════════════════════════════════════════
def dist(v):
    """⛔ Ritorna SEMPRE un dizionario, e `n` dice se c'era qualcosa da
    guardare: «zero campioni» e «non ho potuto guardare» non si confondono."""
    v = [x for x in v if x is not None]
    if not v:
        return {"n": 0}
    v = sorted(v)
    return {"n": len(v), "mediana": statistics.median(v),
            "media": sum(v) / len(v), "p95": v[min(len(v) - 1, int(len(v) * 0.95))],
            "max": v[-1]}


def a_regime(campioni):
    """⛔ `CODER.md` §3.5 — un campione preso all'avvio non dice niente del
    regime.  Si torna (prima meta', seconda meta'): la seconda e' il numero, e
    la prima si stampa accanto perche' il transitorio si VEDA."""
    n = len(campioni)
    if n < 4:
        return campioni, campioni
    return campioni[:n // 2], campioni[n // 2:]


TRATTI = [("prep", "0 la preparazione del deposito"),
          ("deposito", "1 ⭐ fotogramma → DEPOSITO (`drawImage(VideoFrame)`)"),
          ("chiusura", "2 `f.close()` (il rilascio)"),
          ("bande", "3 le bande (`fillRect`)"),
          ("componi", "4 ⭐ deposito → TELA, riscalato (`drawImage`)"),
          ("fino_al_ritorno", "⇒ TOTALE fino al ritorno di `drawImage`"),
          ("fino_alla_tela_leggibile",
           "⇒ ⛔ TOTALE fino alla TELA LEGGIBILE (il confine SCOMODO)"),
          ("lettura_del_banco",
           "⚠ (fuori dai tratti) la LETTURA del banco sul deposito")]


def casi_del_giro(a, guasto=""):
    """⛔ Il controllo positivo viaggia nello stesso giro, non in un altro.

    ⚠ E la profondita' del FLUSSO e quella della STRINGA sono due colonne
      diverse, perche' nel prodotto **non coincidono**: `rcp.c:1198` negozia
      `8` e `figlio.c:1605` codifica `10`.  Un banco che le tenesse insieme non
      potrebbe misurare la sessione vera."""
    fuori = []
    prove = [
        ("sessione vera", "hevc", 10, "hev1.1.6.L153.B0", "incognita",
         "⭐⭐ LA SESSIONE VERA — flusso 10 bit (`figlio.c:1605`) letto con la "
         "stringa a 8 bit che la pagina configura (`rcp.c:1198` negozia 8)"),
        ("hevc 10/10", "hevc", 10, "hev1.2.4.L153.B0", "incognita",
         "flusso e stringa d'accordo, tutt'e due Main10"),
        ("hevc 8/8", "hevc", 8, "hev1.1.6.L153.B0", "incognita",
         "flusso e stringa d'accordo, tutt'e due Main"),
        ("av1 10/10", "av1", 10, "av01.0.13M.10", "incognita",
         "l'altro codec, 10 bit"),
        ("av1 8/8", "av1", 8, "av01.0.13M.08", "controllo+",
         "⭐ CONTROLLO POSITIVO — la fase 3 lo misura a 9,07 ms"),
    ]
    for nome, codec, prof, stringa, ruolo, perche in prove:
        fuori.append({"codec": codec, "profondita": prof, "stringa": stringa,
                      "nome": nome, "ruolo": ruolo, "perche": perche})
    return fuori


def costruisci(casi, a, guasto=""):
    for c in casi:
        pezzi, guaio = sequenza(c["codec"], c["profondita"], a.l, a.a,
                                a.fotogrammi, guasto)
        c["l"], c["a"] = a.l, a.a
        c["vista_l"], c["vista_a"] = a.vista_l, a.vista_a
        c["pezzi"] = [base64.b64encode(p).decode() for p in pezzi]
        c["quanti_pezzi"] = len(pezzi)
        c["guaio_costruzione"] = guaio
        c["profilo_nei_byte"], c["pix_nei_byte"] = (
            profilo_nei_byte(pezzi[0], c["codec"]) if pezzi else (None, None))
    return casi


def gira(casi, palco, guasto="", lettura=0):
    cartella = tempfile.mkdtemp(prefix="04-b22-web-")
    pagina = (PAGINA.replace("__CASI__", json.dumps(casi))
                    .replace("__GUASTO__", json.dumps(guasto))
                    .replace("__LETTURA__", json.dumps(lettura)))
    with open(os.path.join(cartella, "disegno.html"), "w") as f:
        f.write(pagina)
    s = servi(cartella, PORTA_HTTP)
    try:
        palco.accendi("http://127.0.0.1:%d/disegno.html" % PORTA_HTTP)
        fine = time.time() + 300
        while time.time() < fine:
            r = palco.valuta("document.body.dataset.b22 === 'fatto' ? "
                             "JSON.stringify(window.B22) : ''")
            if r:
                return json.loads(r), None
            time.sleep(0.5)
        return None, "la pagina non ha finito entro 300 s"
    finally:
        s.shutdown()
        s.server_close()
        shutil.rmtree(cartella, ignore_errors=True)


def stampa(fuori, casi):
    per_nome = {c["nome"]: c for c in casi}
    tit("i flussi, e il profilo letto NEI BYTE (secondo testimone)")
    for c in casi:
        inf("%-14s %3d fotogrammi · profilo «%s» · pix %s%s"
            % (c["nome"], c["quanti_pezzi"], c["profilo_nei_byte"],
               c["pix_nei_byte"],
               (" · ⛔ " + str(c["guaio_costruzione"])[:60])
               if c["guaio_costruzione"] else ""))

    for caso in fuori["casi"]:
        n = len(caso["campioni"])
        tit("%s — %s" % (caso["nome"], per_nome[caso["nome"]]["perche"]))
        inf("offerti %d · mandati al decodificatore %d · usciti dal "
            "decodificatore %d · `VideoFrame.format` = %s"
            % (caso["offerti"], caso["mandati"], n, caso["formato"]))
        if caso["perche"]:
            dub("il caso si e' chiuso cosi': " + str(caso["perche"])[:140])
        if n == 0:
            # ⛔ zero non e' «0,0 ms»: e' «non c'era niente da misurare».
            ko("n = 0 — nessun fotogramma e' uscito: qui non c'e' nessun "
               "numero, e non se ne scrive uno")
            continue
        avvio, regime = a_regime(caso["campioni"])
        print("    %-52s %9s %9s" % ("tratto (ms)", "avvio", "⭐ regime"))
        for chiave, etichetta in TRATTI:
            da = dist([c[chiave] for c in avvio])
            db = dist([c[chiave] for c in regime])
            print("    %-52s %9s %9s"
                  % (etichetta,
                     ("%.2f" % da["mediana"]) if da["n"] else "—",
                     ("%.2f" % db["mediana"]) if db["n"] else "—"))
        d = dist([c["fino_alla_tela_leggibile"] for c in regime])
        if d["n"]:
            inf("⛔ [?] col PEZZO CIECO (%g-%g ms, `web.md` §6.2, nessuna API "
                "lo vede, e su questo palco ESISTE): %.1f – %.1f ms"
                % (PEZZO_CIECO[0], PEZZO_CIECO[1],
                   d["mediana"] + PEZZO_CIECO[0], d["mediana"] + PEZZO_CIECO[1]))


def riassunto(fuori):
    r = {}
    for caso in fuori["casi"]:
        if not caso["campioni"]:
            r[caso["nome"]] = {"n": 0, "perche": caso["perche"]}
            continue
        _, regime = a_regime(caso["campioni"])
        r[caso["nome"]] = {
            "ruolo": caso["ruolo"], "formato": caso["formato"],
            "n": len(regime),
            "tratti": {k: dist([c[k] for c in regime]) for k, _ in TRATTI},
        }
    return r


def principale():
    ap = argparse.ArgumentParser()
    ap.add_argument("--certifica", action="store_true")
    ap.add_argument("--fotogrammi", type=int, default=90)
    ap.add_argument("--l", type=int, default=1920)
    ap.add_argument("--a", type=int, default=1080)
    ap.add_argument("--vista-l", type=int, default=1280, dest="vista_l")
    ap.add_argument("--vista-a", type=int, default=720, dest="vista_a")
    ap.add_argument("--solo", default="",
                    help="⛔ un caso solo, per giro: toglie l'effetto "
                         "dell'ORDINE — il sostrato che Chrome sceglie per una "
                         "tela dipende da quel che e' successo prima")
    ap.add_argument("--lettura", type=int, default=0,
                    help="la regione che il banco rilegge dal deposito a ogni "
                         "fotogramma: 0 = nessuna, 480 = come 03-b17")
    ap.add_argument("--json", default="")
    a = ap.parse_args()
    if a.certifica:
        return certifica(a)

    tit("04-b22 · il disegno SCOMPOSTO — %s" % time.strftime("%F %T"))
    inf("⚠ palco: il DESKTOP VERO dell'utente, dichiarato e non spostato "
        "(README.md:397).  Su Xvfb il pezzo cieco non esisterebbe.")
    inf("scena: testsrc2 %dx%d, in movimento a OGNI fotogramma, %d fotogrammi"
        % (a.l, a.a, a.fotogrammi))
    inf("vista (la tela sul vetro): %dx%d" % (a.vista_l, a.vista_a))
    if a.lettura:
        inf("⛔ LETTURA del banco ACCESA: %d×%d dal deposito a ogni fotogramma, "
            "come `03-b17-ritardo.py:534`.  E' cronometrata FUORI dai tratti."
            % (a.lettura, a.lettura // 2))
    else:
        inf("lettura del banco: SPENTA — nessun `getImageData` sul deposito")
    guasto = os.environ.get("GUASTO", "")
    casi = casi_del_giro(a)
    if a.solo:
        casi = [c for c in casi if c["nome"] == a.solo]
        if not casi:
            ko("⛔ nessun caso si chiama «%s»" % a.solo)
            return 2
        inf("⛔ UN CASO SOLO («%s»): l'effetto dell'ordine e' tolto" % a.solo)
    casi = costruisci(casi, a, guasto)
    palco = Palco()
    try:
        fuori, guaio = gira(casi, palco, guasto, a.lettura)
    finally:
        palco.spegni()
    if fuori is None:
        ko("⛔ " + guaio)
        return 2
    stampa(fuori, casi)
    tit("il palco, letto DALLA PAGINA (l'altro capo)")
    for k, v in (fuori.get("palco") or {}).items():
        inf("%-12s %s" % (k, v))
    r = riassunto(fuori)
    if a.json:
        with open(a.json, "w") as f:
            json.dump({"quando": time.strftime("%F %T"), "riassunto": r,
                       "palco": fuori.get("palco"), "bandiere": palco.bandiere,
                       "scena": {"l": a.l, "a": a.a, "fotogrammi": a.fotogrammi,
                                 "vista": [a.vista_l, a.vista_a],
                                 "lettura_del_banco": a.lettura},
                       "pezzo_cieco_ms": list(PEZZO_CIECO),
                       "casi": fuori["casi"]}, f)
        inf("verbale depositato in " + a.json)

    tit("il verdetto")
    ctrl = [v for v in r.values() if v.get("ruolo") == "controllo+"]
    if not ctrl or not ctrl[0].get("n"):
        ko("⛔ il controllo positivo non ha prodotto campioni: sui numeri degli "
           "altri casi non si scrive niente")
        return 2
    m = ctrl[0]["tratti"]["fino_al_ritorno"]["mediana"]
    if m > 20.0:
        ko("⛔ il controllo positivo (AV1 8 bit) costa %.1f ms: la fase 3 lo "
           "misura a 9,1 — questo banco sta misurando se stesso, e sugli altri "
           "numeri non si scrive niente" % m)
        return 2
    ok("il controllo positivo costa %.1f ms (la fase 3: 9,1) ⇒ i numeri degli "
       "altri casi si possono scrivere" % m)
    return 0


def certifica(a):
    tit("la certificazione di 04-b22 — sano → guasto → risanato")
    inf("atteso, scritto PRIMA di girare:")
    inf("  sano/risanato       il controllo positivo sotto i 20 ms")
    inf("  disegno-lento       il tratto **1** (fotogramma → deposito) sale di")
    inf("                      ~10 ms, e gli altri NO: se salisse il 4, questo")
    inf("                      banco non saprebbe scomporre niente")
    inf("  niente-fotogrammi   n = 0 CON il motivo scritto, e nessun «0,0 ms»")
    a.fotogrammi = min(a.fotogrammi, 40)
    esiti = []
    base = None
    for giro, guasto in (("sano", ""), ("disegno-lento", "disegno-lento"),
                         ("niente-fotogrammi", "niente-fotogrammi"),
                         ("risanato", "")):
        tit("giro «%s»" % giro)
        casi = costruisci(casi_del_giro(a), a, guasto)
        palco = Palco()
        try:
            fuori, guaio = gira(casi, palco, guasto)
        finally:
            palco.spegni()
        if fuori is None:
            ko("⛔ " + guaio)
            esiti.append(False)
            continue
        r = riassunto(fuori)
        for nome, v in r.items():
            if not v.get("n"):
                inf("%-14s n = 0 — %s" % (nome, str(v.get("perche"))[:70]))
            else:
                t = v["tratti"]
                inf("%-14s dep %5.2f · chiu %4.2f · band %4.2f · comp %5.2f "
                    "· tot %5.2f"
                    % (nome, t["deposito"]["mediana"], t["chiusura"]["mediana"],
                       t["bande"]["mediana"], t["componi"]["mediana"],
                       t["fino_al_ritorno"]["mediana"]))
        if guasto == "niente-fotogrammi":
            atteso = all(v.get("n", 0) == 0 and v.get("perche") is not None
                         for v in r.values())
            frase = "ogni caso ha n = 0 CON il motivo"
        elif guasto == "disegno-lento":
            if base is None:
                atteso, frase = False, "manca il giro sano di riferimento"
            else:
                salite = {}
                for nome, v in r.items():
                    if not v.get("n") or not base.get(nome, {}).get("n"):
                        continue
                    for k in ("deposito", "componi", "bande"):
                        salite.setdefault(k, []).append(
                            v["tratti"][k]["mediana"] - base[nome]["tratti"][k]["mediana"])
                sd = {k: statistics.median(v) for k, v in salite.items() if v}
                inf("salite mediane: " + ", ".join("%s %+.2f" % (k, v)
                                                   for k, v in sd.items()))
                atteso = (sd.get("deposito", 0) > 7.0
                          and abs(sd.get("componi", 0)) < 5.0
                          and abs(sd.get("bande", 0)) < 5.0)
                frase = ("il tratto 1 sale di %+.2f e gli altri restano fermi"
                         % sd.get("deposito", 0))
        else:
            c = [v for v in r.values() if v.get("ruolo") == "controllo+"]
            atteso = bool(c) and c[0].get("n") and \
                c[0]["tratti"]["fino_al_ritorno"]["mediana"] < 20.0
            frase = "il controllo positivo sta sotto i 20 ms"
            if guasto == "" and base is None:
                base = r
        esiti.append(bool(atteso))
        (ok if atteso else ko)("giro «%s»: %s" % (giro, frase))
    tit("esito della certificazione")
    if all(esiti):
        ok("PROMOSSO %d giri su %d" % (len(esiti), len(esiti)))
        return 0
    ko("BOCCIATO: %d giri su %d" % (sum(1 for e in esiti if e), len(esiti)))
    return 1


if __name__ == "__main__":
    sys.exit(principale())
