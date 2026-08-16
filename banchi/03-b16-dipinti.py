#!/usr/bin/env python3
"""03-b16-dipinti.py — ⭐ I FOTOGRAMMI CHE ARRIVANO ALL'UTENTE, contati in
regime su un browser vero, e le quattro regole di `RCP.md` che li fanno arrivare.

    python3 banchi/03-b16-dipinti.py                    il giro sano
    python3 banchi/03-b16-dipinti.py --certifica        ⛔ sano + ogni guasto
    python3 banchi/03-b16-dipinti.py --sequenze         rifa' le sequenze e basta
    python3 banchi/03-b16-dipinti.py --casi D,P5a       solo alcuni casi

===========================================================================
⛔ PERCHE' ESISTE

`PIANO.md` fase 3 chiede *«i fotogrammi consegnati all'utente, non quelli
elaborati — il numero che in v1 nessuno aveva mai contato, e che era 18 mentre
si ottimizzava altro»*.  Il contatore `dipinti` in `src/pagina.html` c'e' da
F2.6, ⛔ ma **nessuno lo aveva mai misurato in regime**: la veglia del primo
fotogramma lo guarda per sapere se e' `> 0`, che e' una domanda diversa.

E accanto al numero vanno i suoi fratelli — `consegnati`, `completi`,
`azzerati`, `scartati_ordine`, `buchi` — perche' e' la DIFFERENZA fra quei
numeri a dire **dove** si perdono i fotogrammi.  Un `dipinti` basso con
`consegnati` alto accusa il disegno; con `azzerati` alto accusa la linea; con
`scartati_ordine` alto accusa l'ordine.  Il numero da solo non accusa nessuno.

===========================================================================
⛔ LA SCENA, DICHIARATA — `LEZIONI.md` §1.1

La scena e' una sequenza AV1 **generata qui**, 1920×1080, `testsrc2` che si
muove **a ogni fotogramma** (non a raffiche: e' la meta' della lezione che si
dimentica).  Una chiave e 119 delta, rimessa in giro a ciclo: la chiave torna
ogni due secondi, che e' anche quel che fara' il prodotto.

⛔ E SI CONTA QUANTO SI OFFRE, non solo quanto si dipinge.  E' il controllo
   dell'altra meta' di §1.1 — «si conta quanto disegna il client» — portato di
   qua: senza il conto di quel che il banco ha OFFERTO, un tetto a 41 fotogrammi
   non si sa se sia della pagina o dell'alimentatore.  I due numeri stanno
   accanto in ogni riga del registro.

⛔ E IL DECODIFICATORE E' IN SOFTWARE, e va detto prima del numero.  Xvfb non ha
   GPU e Chrome parte con `--disable-gpu`: AV1 lo decodifica `dav1d` sulla CPU e
   la tela 2D dipinge sulla CPU.  ⇒ `LEZIONI.md` §6.3 — «un banco il cui client
   decodifica in software misura il client, non noi».  Il numero che esce e' un
   **pavimento misurato su questa macchina**, non il tetto della pagina; ed e'
   per questo che il giro si fa a tre misure (480p, 720p, 1080p): se il numero
   cala con i pixel, il tetto e' del decodificatore; se resta, e' della pagina.

===========================================================================
⛔ IL BANCO SI CERTIFICA PRIMA DI ESSERE CREDUTO — `LEZIONI.md` §1.2

Ogni proprieta' ha un controllo **positivo** e uno **negativo**, e i guasti si
innestano nel **prodotto** — una sostituzione testuale su una copia di
`src/pagina.html`, servita a un percorso suo.  ⛔ Se la sostituzione non si
applica il banco **si ferma**: un guasto che non entra e' un verde falso, e ha
esattamente lo stesso aspetto di un guasto curato.

⭐ E LA REGOLA CHE HA DECISO META' DEI CASI: *«una pagina che butta TUTTO
   passerebbe il controllo positivo»*.  Per ogni «X si scarta» c'e' un caso
   gemello che pretende che **Y NON si scarti**, e un guasto che butta tutto per
   far vedere che il gemello lo prende.

| # | atteso sano | guasto | atteso guasto |
|---|---|---|---|
| **D60/D30/D720/D480** i dipinti in regime | dipinti/s ≥ 90 % di quelli OFFERTI, e non scollati dai consegnati | `nondipinge` | ⛔ dipinti/s = 0 **con `consegnati`/s pieno** — cioe' i fratelli distinguono il disegno dalla decodifica |
| **Dsat** ⛔ il TETTO | si offre a raffica, senza cadenza: e' l'unico modo di misurare quanti se ne POTEVANO dipingere.  ⚠ Offrendone 60 se ne dipingono 60 e il numero non dice niente — e' un verde per costruzione | — | — |
| **P5a** il vecchio si scarta | `scartati_ordine` = 1, `ultimo_consegnato` = 3, `consegnati` = 2 | `ordine-spento` | il vecchio entra: `ultimo_consegnato` **torna indietro** a 2 |
| | | `ordine-tutto` | butta anche il nuovo: `consegnati` = 1 |
| **P5b** fuori ordine VERO | la chiave grossa, spedita a pezzi lenti, e' scavalcata dal delta piccolo: la sessione non chiude e la chiave arriva lo stesso | `ordine-tutto` | la chiave scavalcata viene buttata: `ultimo_consegnato` resta 9 |
| **E8** azzerato ≠ finito | `azzerati` = 1, `consegnati` = 0, `dipinti` = 0, `buchi` = 1, tela nera | `reset-consegnato` | `consegnati` = 1: il fotogramma abbandonato e' entrato |
| **E8p** ⛔ il positivo | **gli stessi byte** con FIN: `consegnati` = 1, `dipinti` = 1 | — | ⛔ senza questo, una pagina che butta tutto passerebbe E8 |
| **B** un buco, una chiave | `buchi` = 1, `chiavi_chieste` = 1 su cinque delta persi, e nessun delta consegnato | `spirale` | `chiavi_chieste` = 5 |
| **Bp** ⛔ il positivo, dentro B | dopo la chiave si ricomincia a dipingere | — | ⛔ senza, «non chiede chiavi» sarebbe verde anche in una pagina ferma |
| **TR** il trattenuto | con una `ADATTA_TELA` senza risposta: `trattenuti` = 1, **zero errori**, e al `TELA` il fotogramma si dipinge | `chiude-sempre` | la sessione si chiude |
| **TRn** ⛔ il negativo | **senza** `ADATTA_TELA`: `ERRORE_PROTOCOLLO` **subito**, `trattenuti` = 0 | `trattieni-sempre` | trattiene e non chiude |
| **TRr** `TELA(RIFIUTATA)` | chiude l'attesa: il trattenuto si rigiudica ed e' `ERRORE_PROTOCOLLO`, e non resta niente in mano | — | — |
| **V3** la vista segue la finestra | a schermo FERMO: la tela vale `clientWidth × dpr`, `dipinti` non sale, `ricomposizioni` sale, l'immagine non diventa nera | `vista-fissa` | la tela resta quella di prima |
| **V3s** ⛔ la barra di scorrimento | `clientWidth` NON si muove quando la tela si accende: `html { overflow-y: scroll }` cura gia' la famiglia | — | ⚠ e' la misura che ha fatto RITIRARE la cura con `ResizeObserver`.  Se un giorno quella riga di stile sparisse, questo caso diventa rosso e lo dice |
| **V3d** il deposito | il prezzo del disegno in piu' e quel che compra: col deposito la tela ridimensionata a buco aperto e' **dipinta**; senza, e' **nera** | — | ⛔ le due meta' sono l'una il controllo negativo dell'altra |

⛔ **Che cosa questo banco NON copre, e va letto accanto a ogni verde:**

| | |
|---|---|
| ⛔ **Firefox** | si misura **solo su Chrome**.  Firefox 140esr non ha CDP e non si pilota cosi'; l'unica strada gia' percorsa in casa e' la pagina strumentata con `sendBeacon` (`01-p5-ff-strumenta.py`).  ⇒ E' la forma **E10**, dichiarata e non curata |
| ⛔ **HEVC** | si misura **solo su AV1**: su Xvfb non c'e' GPU e ogni stringa HEVC viene rifiutata (`[M]` 12 ago).  Il prodotto avra' due percorsi di decodifica e questo banco ne guarda uno |
| ⛔ **WebTransport** | i fotogrammi entrano da `leggi_uno_stream()` con uno stream finto — il punto giusto per FIN contro `RESET_STREAM`, ma senza la coda della rete, il credito degli stream e la banda |
| ⛔ **la consegna del `resize`** | `[M]` su questo palco `requestAnimationFrame` **non gira mai** (0 quadri in 3 s, con e senza GPU, `visibilityState` «visible») ⇒ il gestore del `resize` della pagina, che passa da un rAF, e' codice morto qui.  V3 prova quel che succede **dopo**, non la consegna |
| `[?]` **il cambio di `devicePixelRatio`** | sotto `Emulation.setDeviceMetricsOverride` non arriva **niente**: ne' `resize`, ne' `ResizeObserver`, ne' il `change` di `matchMedia("(resolution: Ndppx)")`.  ⇒ Il banco sta misurando **l'emulazione** e non il browser (`LEZIONI.md` §1.11): la domanda resta aperta e vuole uno zoom vero |

===========================================================================
⛔ IL PERIMETRO — `FASI.md` §03-movimento: ogni step ha porta, schermo e registro
   propri, o due banchi in parallelo si fermano a vicenda.

    porta HTTP    7604       (7448, 7501 e ⛔ 7561 non si toccano)
    diagnosi CDP  9604
    schermo       :81
    registro      banchi/03-b16-esiti.jsonl
    copie         banchi/03-b16-copie/

⛔ E NON SERVE IL PRODOTTO.  `[M]` 13 agosto 2026: su CHUWI il prodotto non si
   compila (mancano gli header di `nghttp3` e `ngtcp2`, e l'unico `remotix`
   eseguibile sulla macchina e' quello di v1, con dentro FreeRDP e zero
   occorrenze di «RCP»).  ⇒ La pagina si serve da `http.server` su
   `127.0.0.1:7604`, che e' **contesto sicuro** e quindi ha WebCodecs, e i
   fotogrammi entrano da dove entrano davvero.

⛔ IL PEZZO CIECO, DICHIARATO ACCANTO AL NUMERO: fra il banco e la pagina non
   c'e' **WebTransport**.  I casi che toccano il filo entrano da
   `REMOTIX.leggi_uno_stream()` con uno stream finto — cioe' dal punto esatto in
   cui la pagina distingue il FIN dal `RESET_STREAM` — ma la coda della rete,
   il credito degli stream e la banda **non sono in questo banco**.  Il numero
   dei dipinti e' quindi *«quanti ne dipinge la pagina se glieli si mette in
   mano»*, e il pezzo che manca lo misura lo step 5.
"""

import argparse
import base64
import importlib.util
import json
import os
import re
import shutil
import signal
import struct
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

QUI = Path(__file__).resolve().parent
RADICE = QUI.parent
SORGENTE = RADICE / "src" / "pagina.html"
SEQUENZE = QUI / "03-b16-sequenze"
COPIE = QUI / "03-b16-copie"
REGISTRO = QUI / "03-b16-esiti.jsonl"

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def ok(t):   print(f"    {VERDE}OK{GRIGIO}  {t}")
def ko(t):   print(f"    {ROSSO}NO{GRIGIO}  {t}")
def dub(t):  print(f"    {GIALLO}??{GRIGIO}  {t}")
def inf(t):  print(f"    --  {t}")
def log(t):  print(f"\n\033[1m== {t}{GRIGIO}")


# ═══════════════════════════════════════════════════════════════════════════
# 1. LE SEQUENZE — la scena, generata e dichiarata
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ AV1 e non HEVC, e la ragione e' misurata: `[M]` 12 agosto 2026 (F2.5) — su
#    Linux il decodificatore HEVC di Chrome e' quello della piattaforma
#    (VA-API), e su uno schermo finto non c'e' GPU ⇒ ogni stringa HEVC viene
#    rifiutata.  Un banco che misurasse HEVC su Xvfb misurerebbe zeri che non
#    dicono niente sulla domanda posta.  ⚠ E la conseguenza va scritta accanto
#    al verdetto: **questo banco copre meta' dei percorsi di decodifica del
#    prodotto** (`DECISIONI.md` §1.13: HEVC con AV1 come ripiego negoziato), ed
#    e' la forma E10 tenuta sotto controllo dichiarandola, non curata.
#
# ⛔ E IL FLUSSO E' A BASSA LATENZA — `pred-struct=1`.  Con la struttura ad
#    accesso casuale che SVT-AV1 usa di suo, i fotogrammi escono RIORDINATI e
#    compaiono i `show_existing_frame` da 5 byte: sarebbero un fuori ordine
#    **del codificatore**, cioe' un secondo imputato dentro il caso che misura
#    il fuori ordine **della rete**.  Il prodotto codifica a bassa latenza
#    (`optimizeForLatency` dall'altra parte); qui si fa lo stesso.

MISURE = [(1920, 1080), (1280, 720), (854, 480)]


def _ffmpeg_c_e():
    for p in ("ffmpeg", "ffprobe"):
        if shutil.which(p) is None:
            raise RuntimeError(f"⛔ manca {p}: la scena non si puo' generare")


def _spezza_ivf(byte):
    """Uno stream IVF in fotogrammi.  ⭐ IVF porta la lunghezza di ogni unita'
    temporale in testa (4 byte) piu' 8 di istante: spezzarlo e' esatto e non
    e' un'euristica sui marcatori OBU."""
    if byte[:4] != b"DKIF":
        raise RuntimeError("⛔ non e' un IVF: i primi quattro byte sono "
                           + repr(byte[:4]))
    testa = struct.unpack("<H", byte[6:8])[0]
    o, fuori = testa, []
    while o < len(byte):
        (lung,) = struct.unpack("<I", byte[o:o + 4])
        o += 12
        if o + lung > len(byte):
            raise RuntimeError("⛔ un fotogramma IVF esce dal file: il flusso e' troncato")
        fuori.append(byte[o:o + lung])
        o += lung
    return fuori


def genera_sequenza(l, a, secondi=2.0, ritmo=60):
    """Una sequenza AV1 alla misura chiesta.  ⛔ Il ritorno porta il conto dei
    fotogrammi **e** quale di essi e' la chiave: senza, «e' una chiave» sarebbe
    una deduzione dall'indice, e il caso B — che pretende una chiave a meta'
    sequenza — poggerebbe su una deduzione mai verificata (forma E5)."""
    _ffmpeg_c_e()
    SEQUENZE.mkdir(parents=True, exist_ok=True)
    dove = SEQUENZE / f"av1-{l}x{a}.json"
    if dove.is_file():
        d = json.loads(dove.read_text())
        if d.get("larghezza") == l and d.get("altezza") == a:
            return d
    with tempfile.TemporaryDirectory() as t:
        ivf = os.path.join(t, "u.ivf")
        cmd = ["ffmpeg", "-v", "error", "-y", "-f", "lavfi",
               "-i", f"testsrc2=size={l}x{a}:rate={ritmo}:duration={secondi}",
               "-c:v", "libsvtav1", "-preset", "10", "-crf", "40",
               "-g", "1000", "-svtav1-params", "pred-struct=1",
               "-pix_fmt", "yuv420p", "-f", "ivf", ivf]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError(f"⛔ ffmpeg e' fallito: {r.stderr[-500:]}")
        pezzi = _spezza_ivf(Path(ivf).read_bytes())
        # ⛔ Il tipo di ogni fotogramma si CHIEDE a ffprobe, non si deduce.
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "frame=key_frame", "-of", "csv=p=0", ivf],
            capture_output=True, text=True)
        chiavi = [x.strip() == "1" for x in p.stdout.split() if x.strip() != ""]
        s = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=profile,level,width,height",
             "-of", "json", ivf], capture_output=True, text=True)
        st = json.loads(s.stdout)["streams"][0]
    if len(chiavi) != len(pezzi):
        raise RuntimeError(f"⛔ ffprobe conta {len(chiavi)} fotogrammi e l'IVF "
                           f"ne porta {len(pezzi)}: non si sa quale sia la chiave")
    if not chiavi[0]:
        raise RuntimeError("⛔ il primo fotogramma non e' una chiave")
    if sum(chiavi) != 1:
        raise RuntimeError(f"⛔ chiavi attese 1, trovate {sum(chiavi)}")
    # ⛔ La stringa di WebCodecs si costruisce dai campi LETTI, non scritta a
    #    mano: `av01.P.LLT.BB` — profilo, livello (seq_level_idx), tier, bit.
    profili = {"Main": 0, "High": 1, "Professional": 2}
    prof = profili.get(st.get("profile"), 0)
    liv = int(st.get("level") or 8)
    stringa = f"av01.{prof}.{liv:02d}M.08"
    d = {"nome": f"av1-{l}x{a}", "larghezza": int(st["width"]),
         "altezza": int(st["height"]), "codec_rcp": 2, "stringa": stringa,
         "profilo": st.get("profile"), "livello": liv, "ritmo": ritmo,
         "quanti": len(pezzi), "chiavi": [i for i, k in enumerate(chiavi) if k],
         "byte": sum(len(x) for x in pezzi),
         "pezzi": [{"chiave": bool(chiavi[i]),
                    "dati": base64.b64encode(x).decode()}
                   for i, x in enumerate(pezzi)]}
    dove.write_text(json.dumps(d))
    return d


# ═══════════════════════════════════════════════════════════════════════════
# 2. I GUASTI INNESTATI NEL PRODOTTO
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Ogni guasto e' una sostituzione testuale su una COPIA di `src/pagina.html`,
#    e se non si applica il banco si ferma: un guasto che non entra e' un verde
#    falso con l'aspetto di un guasto curato (`LEZIONI.md` §2.2).
#
# ⚠ E la sostituzione si conta: `atteso` dice quante occorrenze devono cambiare.
#   Una riga che ne cambiasse due invece di una romperebbe qualcos'altro, e il
#   rosso accuserebbe l'imputato sbagliato.

GUASTI = {
    "nondipinge": (
        "if (this.componi()) this.conti.dipinti++;",
        "if (false && this.componi()) this.conti.dipinti++;", 1),
    "ordine-spento": (
        "differenza(i.numero, this.ultimo_consegnato) <= 0",
        "differenza(i.numero, this.ultimo_consegnato) < -2147483647", 1),
    "ordine-tutto": (
        "differenza(i.numero, this.ultimo_consegnato) <= 0",
        "differenza(i.numero, this.ultimo_consegnato) <= 2147483647", 1),
    # ⚠ L'ancora e' di DUE righe, e non e' pignoleria: `if (!completo) {` compare
    #   due volte nella pagina — in `stream_video` e in `leggi_uno_stream` — e
    #   con l'ancora corta il banco si e' fermato da solo invece di innestare il
    #   guasto nel posto sbagliato.  ⭐ E' la ragione per cui il conto delle
    #   occorrenze e' obbligatorio.
    "reset-consegnato": (
        "    if (!completo) {\n      /* ⛔ §6.2: uno stream AZZERATO",
        "    if (false) {\n      /* ⛔ §6.2: uno stream AZZERATO", 1),
    "spirale": (
        "    if (this.sospeso) {\n      this.riga(\"buco: \"",
        "    if (false) {\n      this.riga(\"buco: \"", 1),
    "trattieni-sempre": (
        "    if (this.attese_tela <= 0)",
        "    if (false)", 1),
    "chiude-sempre": (
        "    if (this.attese_tela <= 0)",
        "    if (true)", 1),
    # ⛔ Inchioda la vista: `vista()` non applica piu' niente.  Serve a
    #    certificare che il caso V3 guarda davvero il riscalamento e non l'aria.
    "vista-fissa": (
        "    if (this.vista_l === l && this.vista_a === a) return false;",
        "    if (true) return false;", 1),
    # ⚠ NON e' un guasto: e' la VARIANTE che toglie il deposito, cioe' il
    #   secondo `drawImage` per fotogramma.  Serve a misurare il prezzo di quel
    #   disegno e quel che compra — non a far diventare rosso un caso.
    "senza-deposito": (
        "    if (this.sessione && !this.vista_l) this.adatta_vista();\n"
        "    if (this.componi()) this.conti.dipinti++;",
        "    if (this.sessione && !this.vista_l) this.adatta_vista();\n"
        "    if (this.dipingi_diretto(f_originale)) this.conti.dipinti++;", 1),
}

# ⛔ La variante senza deposito ha bisogno di due innesti, non di uno: il
#    fotogramma va dipinto PRIMA di essere chiuso, e `dipingi()` lo chiude a
#    meta'.  ⇒ Si sostituisce il corpo intero, e la sostituzione si verifica.
SENZA_DEPOSITO = ("""  dipingi(f) {
    if (this.formato === null || this.formato === undefined)
      this.formato = (f.format === undefined) ? "assente" : f.format;
    const fl = f.displayWidth || f.codedWidth;
    const fa = f.displayHeight || f.codedHeight;
    /* ⚠ VARIANTE DI BANCO — un solo `drawImage`: dal fotogramma alla vista,
       senza passare dal deposito.  Non e' il prodotto. */
    let bene = false;
    try {
      const cl = this.tela.width, ca = this.tela.height;
      if (cl && ca && fl && fa) {
        const s = Math.min(cl / fl, ca / fa);
        const dl = Math.max(1, Math.round(fl * s)), da = Math.max(1, Math.round(fa * s));
        const dx = Math.floor((cl - dl) / 2), dy = Math.floor((ca - da) / 2);
        if (dl !== cl || da !== ca) {
          this.pennello.fillStyle = "#000";
          this.pennello.fillRect(0, 0, cl, ca);
        }
        this.pennello.drawImage(f, dx, dy, dl, da);
        this.conti.ricomposizioni++;
        this.dipinta = { l: dl, a: da, x: dx, y: dy, vista: [cl, ca],
                         fotogramma: [fl, fa], scala: Math.round(s * 1000) / 1000 };
        document.body.dataset.schermo = "acceso";
        bene = true;
      }
    } catch (e) {
      this.errori.push("drawImage: " + e);
    }
    try { f.close(); } catch (e) { /* gia' chiuso */ }
    if (this.sessione && !this.vista_l) this.adatta_vista();
    if (bene) this.conti.dipinti++;
  }
""")


def pagina_guasta(nome):
    """La pagina del prodotto con il guasto `nome` dentro.  ⛔ Si ferma se la
    sostituzione non si applica esattamente quante volte deve."""
    testo = SORGENTE.read_text()
    if nome == "sano":
        return testo
    if nome == "senza-deposito":
        i = testo.index("  dipingi(f) {")
        j = testo.index("\n  }\n}", i) + len("\n  }\n")
        return testo[:i] + SENZA_DEPOSITO + testo[j:]
    if nome not in GUASTI:
        raise RuntimeError(f"⛔ guasto sconosciuto: {nome}")
    vecchio, nuovo, atteso = GUASTI[nome]
    quante = testo.count(vecchio)
    if quante != atteso:
        raise RuntimeError(
            f"⛔ il guasto «{nome}» non si innesta: cercavo {atteso} occorrenza/e "
            f"di\n    {vecchio!r}\n  e ne ho trovate {quante}.  ⚠ La pagina e' "
            f"cambiata sotto il banco: il guasto va riscritto, e finche' non lo "
            f"e' ogni verde di questo banco e' un verde di cui non si sa niente.")
    return testo.replace(vecchio, nuovo, atteso)


# ═══════════════════════════════════════════════════════════════════════════
# 3. IL SERVENTE
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Ogni variante al SUO percorso — `/sano/pagina.html`, `/spirale/pagina.html`
#    — ed e' una cura pagata da un verde falso in F2.6: con un percorso solo,
#    Chrome serve dalla cache e il banco dice verde di un guasto mai arrivato.
#    ⚠ Piu' `Network.setCacheDisabled`, che e' la seconda cintura.

class Servente(SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass  # il denominatore lo tiene il banco, non il servente

    def do_GET(self):
        p = self.path.split("?")[0]
        m = re.match(r"^/([a-z0-9-]+)/pagina\.html$", p)
        if m:
            try:
                corpo = pagina_guasta(m.group(1)).encode()
            except Exception as e:
                self.send_error(500, str(e)[:200])
                return
            self._manda(corpo, "text/html; charset=utf-8")
            return
        m = re.match(r"^/sequenze/([a-z0-9x-]+)\.json$", p)
        if m:
            d = SEQUENZE / (m.group(1) + ".json")
            if not d.is_file():
                self.send_error(404, "sequenza assente")
                return
            self._manda(d.read_bytes(), "application/json")
            return
        self.send_error(404, "percorso non servito da questo banco")

    def _manda(self, corpo, tipo):
        self.send_response(200)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(corpo)))
        self.send_header("Cache-Control", "no-store, must-revalidate")
        self.end_headers()
        self.wfile.write(corpo)


# ═══════════════════════════════════════════════════════════════════════════
# 4. IL PALCO — Xvfb e Chrome
# ═══════════════════════════════════════════════════════════════════════════

def _cdp():
    s = importlib.util.spec_from_file_location(
        "cdp", str(QUI / "02-pagina-misura-cdp.py"))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


class Palco:
    """Xvfb + Chrome + CDP.  ⛔ Xvfb si verifica con `xdpyinfo` e non con uno
    `sleep`: uno schermo che non e' partito e uno partito alla misura sbagliata
    hanno lo stesso aspetto da fuori."""

    def __init__(self, schermo, misura, diagnosi, gpu=False):
        self.schermo, self.misura, self.diagnosi = schermo, misura, diagnosi
        self.gpu = gpu
        self.x = self.br = None
        self.t = tempfile.mkdtemp(prefix="b16-")

    def _amb(self):
        a = dict(os.environ)
        a.pop("WAYLAND_DISPLAY", None)   # o Chrome ignora DISPLAY su Wayland
        a["DISPLAY"] = self.schermo
        return a

    def accendi(self):
        sock = Path("/tmp/.X11-unix") / ("X" + self.schermo.lstrip(":"))
        if sock.exists():
            raise RuntimeError(
                f"⛔ lo schermo {self.schermo} e' gia' occupato: un altro banco "
                f"ci sta sopra, e due banchi sullo stesso schermo si fermano a "
                f"vicenda (fasi/03-movimento.md)")
        l, a = self.misura
        self.x = subprocess.Popen(
            ["Xvfb", self.schermo, "-screen", "0", f"{l}x{a}x24"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        for _ in range(60):
            r = subprocess.run(["xdpyinfo"], env=self._amb(),
                               capture_output=True, text=True)
            if r.returncode == 0:
                dim = re.search(r"dimensions:\s+(\d+x\d+)", r.stdout)
                if dim and dim.group(1) == f"{l}x{a}":
                    break
                raise RuntimeError(f"⛔ chiesto {l}x{a}, letto {dim and dim.group(1)}")
            time.sleep(0.25)
        else:
            raise RuntimeError("⛔ Xvfb non ha risposto a xdpyinfo in 15 s")
        flag = ["google-chrome", f"--user-data-dir={self.t}/profilo",
                "--no-first-run", "--no-default-browser-check", "--disable-sync",
                f"--remote-debugging-port={self.diagnosi}",
                "--remote-allow-origins=*",
                f"--window-size={l},{a}", "--window-position=0,0", "about:blank"]
        if not self.gpu:
            flag.insert(1, "--disable-gpu")
        self.br = subprocess.Popen(flag, env=self._amb(),
                                   stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL)
        self.cdp = _cdp()
        b = self.cdp.pagina(self.diagnosi, attesa=40)
        self.c = self.cdp.Cdp(b["webSocketDebuggerUrl"], timeout=180)
        self.c.chiama("Page.enable")
        self.c.chiama("Runtime.enable")
        self.c.chiama("Network.enable")
        self.c.chiama("Network.setCacheDisabled", cacheDisabled=True)
        return self

    def spegni(self):
        for p in (self.br, self.x):
            if p:
                try:
                    p.send_signal(signal.SIGTERM)
                    p.wait(timeout=8)
                except Exception:
                    try:
                        p.kill()
                    except Exception:
                        pass
        shutil.rmtree(self.t, ignore_errors=True)


def versione_di(binario, flag="--version"):
    """⛔ La versione si legge dal binario, non si copia dai documenti."""
    try:
        r = subprocess.run([binario, flag], capture_output=True, text=True, timeout=20)
        return r.stdout.strip() or r.stderr.strip()
    except Exception as e:
        return f"non letta: {e}"


# ═══════════════════════════════════════════════════════════════════════════
# 5. IL PRELUDIO — gli attrezzi che si installano DENTRO la pagina
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ Guidano l'oggetto DEL PRODOTTO — `REMOTIX.schermo` e
#    `REMOTIX.leggi_uno_stream` — e non una copia che gli somiglia.  Un banco
#    che misurasse una copia della catena misurerebbe la copia (forma E10), e il
#    verde non direbbe niente del prodotto.
#
# ⛔ E RACCOLGONO FATTI, NON GIUDIZI: il confronto con l'atteso lo fa Python,
#    fuori dal browser.  La pagina gira DENTRO l'imputato, e un confronto fatto
#    qui sarebbe d'accordo con il difetto.

PRELUDIO = r"""
window.__B16 = (function () {
  const R = window.REMOTIX;
  if (!R || !R.schermo) return { guaio: "REMOTIX assente" };
  const S = R.schermo;
  const TELA = document.getElementById("schermo");
  let chiavi = [], errori_p = [], congedi = [];

  function congeda(mot, perche) { congedi.push([mot, String(perche)]); return Promise.resolve(); }
  function pausa(ms) { return new Promise((r) => setTimeout(r, ms)); }
  function b2b(b64) {
    const s = atob(b64), u = new Uint8Array(s.length);
    for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
    return u;
  }
  /* I 28 byte di RCP.md §6.2, scritti QUI e non copiati dalla pagina: due
     scritture indipendenti degli stessi 28 byte.  Se un giorno non andranno
     d'accordo, quel disaccordo e' il regalo. */
  function pacco(tipo, codec, l, a, numero, dati, istante) {
    const b = new Uint8Array(28 + dati.length), v = new DataView(b.buffer);
    v.setUint16(0, tipo); v.setUint16(2, codec);
    v.setUint32(4, l); v.setUint32(8, a); v.setUint32(12, numero);
    v.setBigUint64(16, BigInt(istante || 0)); v.setUint32(24, 0);
    b.set(dati, 28);
    return b;
  }
  function spezza(b, n) {
    const fuori = [], passo = Math.max(1, Math.ceil(b.length / n));
    for (let o = 0; o < b.length; o += passo) fuori.push(b.subarray(o, Math.min(b.length, o + passo)));
    return fuori;
  }
  /* ⛔ Uno stream finto per `leggi_uno_stream`: e' l'unico modo di provare la
     distinzione FIN / RESET_STREAM sul percorso VERO.  `read()` che finisce con
     `done` = FIN; `read()` che LANCIA = azzerato (§6.2). */
  function finto(blocchi, azzerato, ritardo) {
    let i = 0;
    return { getReader: function () { return { read: function () {
      const mio = i++;
      const fatto = function () {
        if (mio < blocchi.length) return { done: false, value: blocchi[mio] };
        if (azzerato) throw new DOMException("RESET_STREAM (finto)", "AbortError");
        return { done: true, value: undefined };
      };
      if (!ritardo) { try { return Promise.resolve(fatto()); } catch (e) { return Promise.reject(e); } }
      return new Promise(function (ris, rif) {
        setTimeout(function () { try { ris(fatto()); } catch (e) { rif(e); } }, ritardo);
      });
    } }; } };
  }
  function avvia(seq) {
    S.riparti();
    chiavi = []; errori_p = []; congedi = [];
    S.su_chiave = function (u) { chiavi.push(u); };
    S.su_errore_protocollo = function (p) { errori_p.push(String(p)); };
    S.negozia(2, 8, seq.stringa, seq.larghezza, seq.altezza);
    S.adatta_vista();
  }
  function fatti() {
    const d = document.documentElement;
    return { conti: Object.assign({}, S.conti), errori: S.errori.slice(),
             errori_protocollo: errori_p.slice(), chiavi_chieste: chiavi.slice(),
             congedi: congedi.slice(),
             ultimo_consegnato: S.ultimo_consegnato, atteso: S.atteso,
             sospeso: S.sospeso, attese_tela: S.attese_tela,
             in_mano: S.trattenuti.length,
             dec: [S.dec_l, S.dec_a], vista: [S.vista_l, S.vista_a],
             tela: [TELA.width, TELA.height], dipinta: S.dipinta,
             acceso: document.body.dataset.schermo === "acceso",
             cliente: [d.clientWidth, d.clientHeight], dpr: devicePixelRatio || 1 };
  }
  /* ⛔ I pixel, e si guarda la frazione NERA: una tela che non e' stata
     ridipinta e una dipinta di nero hanno lo stesso aspetto da un contatore, e
     nessuna delle due porta un'immagine. */
  function nero() {
    try {
      const p = TELA.getContext("2d", { willReadFrequently: true });
      const im = p.getImageData(0, 0, TELA.width, TELA.height).data;
      let n = 0, neri = 0;
      for (let i = 0; i < im.length; i += 4 * 101) {
        n++;
        if (im[i] + im[i + 1] + im[i + 2] < 24) neri++;
      }
      return { campioni: n, frazione_nera: neri / n };
    } catch (e) { return { errore: String(e) }; }
  }
  async function sequenza(nome) {
    const r = await fetch("/sequenze/" + nome + ".json", { cache: "no-store" });
    if (!r.ok) throw new Error("sequenza " + nome + ": HTTP " + r.status);
    const s = await r.json();
    s.byte = s.pezzi.map(function (p) { return { chiave: p.chiave, b: b2b(p.dati) }; });
    return s;
  }
  return { S: S, R: R, TELA: TELA, congeda: congeda, pausa: pausa, pacco: pacco,
           spezza: spezza, finto: finto, avvia: avvia, fatti: fatti, nero: nero,
           sequenza: sequenza, b2b: b2b,
           chiavi: function () { return chiavi; } };
})();
"""


# ── I casi.  Ognuno ritorna FATTI; il giudizio e' in Python. ────────────────

CASO_REGIME = r"""
(async function () {
  const B = window.__B16, S = B.S;
  const seq = await B.sequenza("%(seq)s");
  B.avvia(seq);
  const ritmo = %(ritmo)d, secondi = %(secondi)s;
  const periodo = 1000 / ritmo, totale = Math.round(ritmo * secondi);
  let offerti = 0, ritardo_massimo = 0;
  const campioni = [];
  /* ⛔ Il campionamento e' DENTRO la pagina e con l'orologio della pagina: un
     campione preso da fuori porta dentro il tempo di andata e ritorno del
     canale di diagnosi, che non c'entra niente con quel che si misura. */
  const spia = setInterval(function () {
    campioni.push({ t: performance.now(), offerti: offerti,
                    c: Object.assign({}, S.conti) });
  }, 250);
  const t0 = performance.now();
  for (let n = 0; n < totale; n++) {
    const scadenza = t0 + n * periodo, ora = performance.now();
    if (ora < scadenza) await B.pausa(scadenza - ora);
    else if (ora - scadenza > ritardo_massimo) ritardo_massimo = ora - scadenza;
    const p = seq.byte[n %% seq.byte.length];
    const b = B.pacco(p.chiave ? 0x0301 : 0x0302, 2, seq.larghezza, seq.altezza,
                      n + 1, p.b, Math.round(n * 1e6 / ritmo));
    offerti++;
    /* ⛔ Senza `await`: e' esattamente quel che fa `avvia_video()`, e un
       `await` qui rimetterebbe il blocco di testa che §5.1 toglie. */
    B.R.leggi_uno_stream(B.finto([b], false, 0), B.congeda);
  }
  /* La coda del decodificatore: si aspetta che finisca di uscire. */
  await B.pausa(700);
  clearInterval(spia);
  campioni.push({ t: performance.now(), offerti: offerti,
                  c: Object.assign({}, S.conti) });
  return { campioni: campioni, offerti: offerti, t0: t0,
           ritardo_massimo: ritardo_massimo, ritmo_chiesto: ritmo,
           seq: { l: seq.larghezza, a: seq.altezza, quanti: seq.quanti,
                  stringa: seq.stringa, byte: seq.byte.reduce(function (s, p) { return s + p.b.length; }, 0) },
           fatti: B.fatti(), pixel: B.nero() };
})()
"""

CASO_P5A = r"""
(async function () {
  const B = window.__B16, S = B.S;
  const seq = await B.sequenza("%(seq)s");
  B.avvia(seq);
  const k = seq.byte[0].b;
  /* ⛔ Tre CHIAVI, e non un delta fra loro: cosi' l'unica ragione per cui una
     di esse puo' essere rifiutata e' la regola dell'ORDINE.  Con un delta di
     mezzo, un rifiuto sarebbe ambiguo fra l'ordine e il buco. */
  for (const n of [1, 3, 2]) {
    S.stream_video(B.pacco(0x0301, 2, seq.larghezza, seq.altezza, n, k, n * 16667), true);
    await B.pausa(80);
  }
  await B.pausa(400);
  return { fatti: B.fatti() };
})()
"""

CASO_P5B = r"""
(async function () {
  const B = window.__B16, S = B.S;
  const seq = await B.sequenza("%(seq)s");
  B.avvia(seq);
  const k = seq.byte[0].b, d = seq.byte[1].b;
  S.stream_video(B.pacco(0x0301, 2, seq.larghezza, seq.altezza, 9, k, 9 * 16667), true);
  await B.pausa(300);
  const prima = Object.assign({}, S.conti);
  /* ⛔⭐ IL FUORI ORDINE VERO, e non a mano: lo stream della CHIAVE parte per
   * primo ed e' GROSSO (arriva a pezzi, lentamente); quello del delta parte
   * dopo ed e' piccolo.  Il delta FINISCE PRIMA — ed e' la forma che si
   * presenta davvero, perche' `stream_video` viene chiamato quando lo stream si
   * CHIUDE, non quando comincia: l'ordine di completamento e' quello delle
   * DIMENSIONI, e una chiave e' dieci volte un delta (§5.2). */
  const grande = B.pacco(0x0301, 2, seq.larghezza, seq.altezza, 10, k, 10 * 16667);
  const piccolo = B.pacco(0x0302, 2, seq.larghezza, seq.altezza, 11, d, 11 * 16667);
  B.R.leggi_uno_stream(B.finto(B.spezza(grande, 6), false, 40), B.congeda);
  await B.pausa(10);
  B.R.leggi_uno_stream(B.finto([piccolo], false, 0), B.congeda);
  await B.pausa(900);
  return { prima: prima, fatti: B.fatti() };
})()
"""

CASO_E8 = r"""
(async function () {
  const B = window.__B16, S = B.S;
  const seq = await B.sequenza("%(seq)s");
  B.avvia(seq);
  const b = B.pacco(0x0301, 2, seq.larghezza, seq.altezza, 1, seq.byte[0].b, 0);
  /* ⛔ GLI STESSI BYTE, spezzati allo stesso modo: fra il caso positivo e il
     negativo cambia SOLO come finisce lo stream.  Se cambiassero anche i byte,
     un rifiuto sarebbe ambiguo fra «era azzerato» e «erano byte cattivi». */
  await B.R.leggi_uno_stream(B.finto(B.spezza(b, 5), %(azzerato)s, 0), B.congeda);
  await B.pausa(600);
  return { byte_offerti: b.length, fatti: B.fatti(), pixel: B.nero() };
})()
"""

CASO_B = r"""
(async function () {
  const B = window.__B16, S = B.S;
  const seq = await B.sequenza("%(seq)s");
  B.avvia(seq);
  const k = seq.byte[0].b, d = seq.byte[1].b;
  const L = seq.larghezza, A = seq.altezza;
  S.stream_video(B.pacco(0x0301, 2, L, A, 1, k, 16667), true);
  await B.pausa(300);
  /* Il 2 non arriva mai: e' il buco.  Poi cinque delta di fila. */
  for (const n of [3, 4, 5, 6, 7]) {
    S.stream_video(B.pacco(0x0302, 2, L, A, n, d, n * 16667), true);
    await B.pausa(50);
  }
  const dopo_i_delta = { conti: Object.assign({}, S.conti),
                         chiavi_chieste: B.chiavi().slice(), sospeso: S.sospeso };
  /* ⛔ E adesso la chiave che ricuce: senza questa meta', «non chiede chiavi a
     ripetizione» sarebbe verde anche in una pagina che si e' fermata del tutto. */
  S.stream_video(B.pacco(0x0301, 2, L, A, 8, k, 8 * 16667), true);
  await B.pausa(600);
  return { dopo_i_delta: dopo_i_delta, fatti: B.fatti() };
})()
"""

CASO_TR = r"""
(async function () {
  const B = window.__B16, S = B.S;
  const grande = await B.sequenza("%(seq)s"), piccola = await B.sequenza("%(seq2)s");
  B.avvia(grande);
  S.stream_video(B.pacco(0x0301, 2, grande.larghezza, grande.altezza, 1,
                         grande.byte[0].b, 16667), true);
  await B.pausa(400);
  /* ⭐ La condizione di §6.2: una `ADATTA_TELA` spedita e senza risposta. */
  if (%(chiedi)s) S.adatta_tela_chiesta();
  const b = B.pacco(0x0301, 2, piccola.larghezza, piccola.altezza, 2,
                    piccola.byte[0].b, 2 * 16667);
  S.stream_video(b, true);
  await B.pausa(120);
  const durante = B.fatti();
  if (%(rifiuta)s) S.tela_rifiutata();
  else if (%(chiedi)s) S.tela_adattata(piccola.larghezza, piccola.altezza);
  await B.pausa(700);
  return { durante: durante, fatti: B.fatti(), pixel: B.nero() };
})()
"""

CASO_V3_ACCESO = r"""
(async function () {
  const B = window.__B16, S = B.S, d = document.documentElement;
  const seq = await B.sequenza("%(seq)s");
  function m() { return [d.clientWidth, d.clientHeight, d.scrollWidth, d.scrollHeight]; }
  S.riparti();
  S.su_chiave = function (u) {}; S.su_errore_protocollo = function (p) {};
  S.negozia(2, 8, seq.stringa, seq.larghezza, seq.altezza);
  /* ⛔ ESATTAMENTE QUEL CHE FA LA STRETTA DI MANO (`collega()`): la vista si
   * misura ADESSO — pagina ancora nell'impaginazione SPENTA, `main` largo
   * 34rem, tela `display:none` — e si applica cosi' com'e' con `S.vista(...)`.
   * ⚠ Non si chiama `adatta_vista()`: sul percorso vero non la chiama nessuno,
   *   perche' `dipingi()` la chiama solo `if (!this.vista_l)` e `vista_l` e'
   *   gia' stato scritto qui.  ⇒ Se l'impaginazione ACCESA avesse una larghezza
   *   utile diversa, la vista resterebbe vecchia per sempre. */
  const r = devicePixelRatio || 1;
  const spento = m();
  S.vista(Math.max(1, Math.round(spento[0] * r)), Math.max(1, Math.round(spento[1] * r)));
  S.stream_video(B.pacco(0x0301, 2, seq.larghezza, seq.altezza, 1, seq.byte[0].b, 0), true);
  await B.pausa(900);
  return { spento: spento, acceso: m(), dpr: r, fatti: B.fatti() };
})()
"""

# ⛔ Il ridimensionamento VERO non si puo' fare da dentro la pagina: una finestra
#    non si allarga da sola.  ⇒ Questo caso e' guidato da Python, in tre tempi.

V3_PREPARA = r"""
(async function () {
  const B = window.__B16, S = B.S, d = document.documentElement;
  const seq = await B.sequenza("%(seq)s");
  B.avvia(seq);
  S.stream_video(B.pacco(0x0301, 2, seq.larghezza, seq.altezza, 1, seq.byte[0].b, 0), true);
  await B.pausa(800);
  return { prima: { cliente: [d.clientWidth, d.clientHeight], dpr: devicePixelRatio || 1,
                    tela: [B.TELA.width, B.TELA.height], viste: S.conti.viste,
                    ricomposizioni: S.conti.ricomposizioni, dipinti: S.conti.dipinti },
           dipinta: S.dipinta };
})()
"""

V3_LEGGI = r"""
(async function () {
  const B = window.__B16, S = B.S, d = document.documentElement;
  /* ⛔⭐ E QUI SI CHIAMA `adatta_vista()` A MANO, E VA DETTO PERCHE': su questo
   * palco `requestAnimationFrame` NON GIRA MAI.  `[M]` 13 agosto 2026: zero
   * quadri in tre secondi, con e senza `--disable-gpu`, e con
   * `document.visibilityState` che dice «visible» — misurato prima di scrivere
   * questa riga, perche' il caso era ROSSO e il primo sospetto va sulla misura
   * (`CODER.md` §3.11).
   *
   * ⇒ Il gestore del `resize` della pagina passa da un `requestAnimationFrame`
   *   (che serve a non riallocare un buffer da milioni di pixel a ogni evento
   *   mentre si trascina il bordo), quindi su Xvfb quel gestore e' codice morto
   *   e il caso accuserebbe il prodotto per un difetto della SCENA.
   *
   * ⛔ QUEL CHE QUESTO CASO NON COPRE, dichiarato: la CONSEGNA della notizia —
   *   `resize` → rAF → `adatta_vista()`.  Copre quel che succede DOPO, cioe' la
   *   doppia passata, il riscalamento e la ricomposizione dal deposito.  La
   *   consegna vuole uno schermo vero, ed e' una riga dello step 5. */
  S.adatta_vista();
  await B.pausa(150);
  return { dopo: { cliente: [d.clientWidth, d.clientHeight], dpr: devicePixelRatio || 1,
                   tela: [B.TELA.width, B.TELA.height], viste: S.conti.viste,
                   ricomposizioni: S.conti.ricomposizioni, dipinti: S.conti.dipinti },
           dipinta: S.dipinta, pixel: B.nero(), fatti: B.fatti() };
})()
"""


def caso_v3(palco, par):
    """⛔ Un ridimensionamento VERO della finestra, a sessione viva e a schermo
    fermo: `Emulation.setDeviceMetricsOverride` e' l'unico modo di cambiare la
    finestra **a pagina viva** — `--window-size` la fissa all'avvio."""
    r = palco.c.valuta(V3_PREPARA % par, attendi=True)
    prima_dipinta = r.get("dipinta")
    l, a = r["prima"]["cliente"]
    nuova = (int(l * 0.7), int(a * 0.8))
    palco.c.chiama("Emulation.setDeviceMetricsOverride", width=nuova[0],
                   height=nuova[1], deviceScaleFactor=r["prima"]["dpr"], mobile=False)
    time.sleep(2.0)
    d = palco.c.valuta(V3_LEGGI, attendi=True)
    palco.c.chiama("Emulation.clearDeviceMetricsOverride")
    time.sleep(1.0)
    d["prima"] = r["prima"]
    d["prima_dipinta"] = prima_dipinta
    d["chiesta"] = list(nuova)
    return d


CASO_SATURA = r"""
(async function () {
  const B = window.__B16, S = B.S;
  const seq = await B.sequenza("%(seq)s");
  B.avvia(seq);
  const campioni = []; let offerti = 0;
  const spia = setInterval(function () {
    campioni.push({ t: performance.now(), offerti: offerti,
                    c: Object.assign({}, S.conti) });
  }, 250);
  const t0 = performance.now();
  /* ⛔ NESSUNA CADENZA: si offre finche' regge, con un solo respiro per lasciar
   * girare il decodificatore.  ⭐ E' l'unico modo di misurare il TETTO della
   * pagina invece del ritmo dell'alimentatore: offrendone 60 se ne dipingono 60
   * e il numero non dice quanti se ne potevano dipingere — e' un verde per
   * costruzione. */
  while (performance.now() - t0 < %(secondi)s * 1000) {
    const p = seq.byte[offerti %% seq.byte.length];
    B.R.leggi_uno_stream(B.finto([B.pacco(p.chiave ? 0x0301 : 0x0302, 2,
        seq.larghezza, seq.altezza, offerti + 1, p.b,
        Math.round(offerti * 16667))], false, 0), B.congeda);
    offerti++;
    await B.pausa(0);
  }
  await B.pausa(1500);
  clearInterval(spia);
  campioni.push({ t: performance.now(), offerti: offerti,
                  c: Object.assign({}, S.conti) });
  return { campioni: campioni, offerti: offerti, t0: t0, ritardo_massimo: 0,
           ritmo_chiesto: 0,
           seq: { l: seq.larghezza, a: seq.altezza, quanti: seq.quanti,
                  stringa: seq.stringa,
                  byte: seq.byte.reduce(function (s, p) { return s + p.b.length; }, 0) },
           fatti: B.fatti(), pixel: B.nero() };
})()
"""

CASO_V3D = r"""
(async function () {
  const B = window.__B16, S = B.S;
  const seq = await B.sequenza("%(seq)s");
  B.avvia(seq);
  const L = seq.larghezza, A = seq.altezza;
  S.stream_video(B.pacco(0x0301, 2, L, A, 1, seq.byte[0].b, 0), true);
  await B.pausa(800);
  const dipinta = S.dipinta ? [S.dipinta.l, S.dipinta.a] : null;
  /* ⛔⭐ I DUE DISEGNI, ISOLATI E CRONOMETRATI SEPARATAMENTE (`LEZIONI.md` §1.5)
   * — e il sorgente e' il DEPOSITO VERO, col fotogramma decodificato dentro.
   * ⚠ Con una tinta piatta al posto dell'immagine il numero cade di duecento
   *   volte: Skia ha una strada rapida per il colore uniforme, e misurarla
   *   vorrebbe dire misurare la strada rapida invece del disegno.
   *
   * ⛔ E il conto che serve e' UNO SOLO: quel che il deposito AGGIUNGE, cioe' la
   *    copia 1:1 alla misura nativa.  La scalatura alla vista si paga in tutte e
   *    due le strade — con deposito la fa `componi()`, senza deposito la fa
   *    `drawImage(f, …)` — e metterla nel conto del deposito sarebbe attribuirgli
   *    un prezzo che non e' suo. */
  const dep = S.deposito;
  const GIRI_C = 200;
  let ms_copia = null, ms_scala = null;
  if (dep) {
  const d2 = document.createElement("canvas");
  d2.width = L; d2.height = A;
  const d2p = d2.getContext("2d", { alpha: false });
  const vis = document.createElement("canvas");
  vis.width = B.TELA.width; vis.height = B.TELA.height;
  const vp = vis.getContext("2d", { alpha: false });
  const dl = dipinta ? dipinta[0] : vis.width, da = dipinta ? dipinta[1] : vis.height;
  function crono(f, giri) {
    for (let i = 0; i < 20; i++) f();
    const t = performance.now();
    for (let i = 0; i < giri; i++) f();
    /* ⛔ Una lettura di un pixel forza il termine dei disegni: senza, si
       misurerebbe la coda invece del disegno. */
    d2p.getImageData(0, 0, 1, 1); vp.getImageData(0, 0, 1, 1);
    return (performance.now() - t) / giri;
  }
  ms_copia = crono(function () { d2p.drawImage(dep, 0, 0); }, GIRI_C);
  ms_scala = crono(function () { vp.drawImage(dep, 0, 0, dl, da); }, GIRI_C);
  }

  /* ⛔ E QUEL CHE IL DEPOSITO COMPRA: un buco aperto (niente piu' fotogrammi
     finche' non arriva una chiave) e l'utente che ridimensiona la finestra. */
  S.stream_video(B.pacco(0x0302, 2, L, A, 5, seq.byte[1].b, 5 * 16667), true);
  await B.pausa(150);
  const sospeso = S.sospeso;
  const nuova = [Math.round(B.TELA.width * 0.72), Math.round(B.TELA.height * 0.72)];
  S.vista(nuova[0], nuova[1]);
  await B.pausa(250);
  return { ms_copia: ms_copia, ms_scala: ms_scala, giri: GIRI_C, dipinta: dipinta,
           deposito: dep ? [dep.width, dep.height] : null,
           col_deposito: !!dep, vista_nuova: nuova, sospeso: sospeso,
           pixel_dopo_ridimensionamento: B.nero(), fatti: B.fatti() };
})()
"""


# ═══════════════════════════════════════════════════════════════════════════
# 6. IL GIUDIZIO — fuori dal browser
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ `LEZIONI.md` §1.4 e `STUDI.md` §web §6.3: si lavora **a distribuzioni**, non a
#    campioni, e ⛔ **l'avvio si butta**.  I primi fotogrammi sono l'avvio —
#    il decodificatore che si configura, la tela che si alloca, il foglio che si
#    riorganizza — e la distribuzione dell'avvio non e' quella del regime.

AVVIO_MS = 3000.0      # quanto si butta in testa
CODA_MS = 400.0        # e quanto in fondo, dove l'alimentazione e' gia' finita


def ritmi(campioni, quale, t0, avvio=AVVIO_MS, coda=CODA_MS):
    """I ritmi al secondo fra campioni consecutivi, sul solo REGIME."""
    fine = campioni[-1]["t"] - coda
    fuori = []
    for a, b in zip(campioni, campioni[1:]):
        if a["t"] < t0 + avvio or b["t"] > fine:
            continue
        dt = (b["t"] - a["t"]) / 1000.0
        if dt <= 0:
            continue
        va = a["offerti"] if quale == "offerti" else a["c"].get(quale, 0)
        vb = b["offerti"] if quale == "offerti" else b["c"].get(quale, 0)
        fuori.append((vb - va) / dt)
    return fuori


def stat(v):
    if not v:
        return {"n": 0}
    s = sorted(v)
    def q(p):
        i = min(len(s) - 1, max(0, int(round(p * (len(s) - 1)))))
        return round(s[i], 2)
    return {"n": len(s), "min": q(0), "p05": q(0.05), "mediana": q(0.5),
            "p95": q(0.95), "max": q(1.0)}


class Pretese:
    """⛔ Ogni pretesa e' scritta PRIMA del giro, nel catalogo in testa al file,
    e qui si limita a confrontare."""

    def __init__(self, caso):
        self.caso, self.righe, self.guai = caso, [], 0

    def che(self, vero, testo):
        self.righe.append({"esito": "OK" if vero else "NO", "testo": testo})
        (ok if vero else ko)(testo)
        if not vero:
            self.guai += 1
        return vero

    def nota(self, testo):
        self.righe.append({"esito": "--", "testo": testo})
        inf(testo)

    def dubbio(self, testo):
        self.righe.append({"esito": "??", "testo": testo})
        dub(testo)


def giudica_regime(p, r):
    c = r["campioni"]
    if len(c) < 6:
        p.che(False, f"solo {len(c)} campioni: non e' una distribuzione")
        return {}
    dip = stat(ritmi(c, "dipinti", r["t0"]))
    con = stat(ritmi(c, "consegnati", r["t0"]))
    off = stat(ritmi(c, "offerti", r["t0"]))
    f = r["fatti"]["conti"]
    p.nota(f"scena: AV1 {r['seq']['l']}×{r['seq']['a']}, «{r['seq']['stringa']}», "
           f"{r['seq']['quanti']} fotogrammi, {r['seq']['byte']} byte")
    p.nota(f"OFFERTI   /s  mediana {off.get('mediana')}  "
           f"(p05 {off.get('p05')} · p95 {off.get('p95')} · min {off.get('min')})")
    p.nota(f"⭐ DIPINTI/s  mediana {dip.get('mediana')}  "
           f"(p05 {dip.get('p05')} · p95 {dip.get('p95')} · min {dip.get('min')} "
           f"· max {dip.get('max')}) su {dip.get('n')} intervalli da 250 ms")
    p.nota(f"CONSEGNATI/s  mediana {con.get('mediana')}  "
           f"(p05 {con.get('p05')} · p95 {con.get('p95')})")
    p.nota(f"i fratelli, sul giro intero: stream {f['stream']} · completi "
           f"{f['completi']} · azzerati {f['azzerati']} · consegnati "
           f"{f['consegnati']} · dipinti {f['dipinti']} · scartati_ordine "
           f"{f['scartati_ordine']} · scartati_misura {f['scartati_misura']} · "
           f"buchi {f['buchi']} · chiavi {f['chiavi_chieste']} · corti {f['corti']}")
    p.nota(f"ritardo massimo dell'alimentatore: {round(r['ritardo_massimo'], 1)} ms "
           f"(se e' grande, il tetto e' del banco e non della pagina)")
    p.nota(f"pixel della tela: frazione nera {r['pixel'].get('frazione_nera')}")
    # ⛔ Il rapporto fra dipinti e offerti e' il numero che dice se la pagina
    #    tiene il passo.  Sotto il 90 % non e' un guasto: e' un TETTO, e va
    #    detto quale — per questo accanto ci sono i fratelli.
    if off.get("mediana"):
        quota = dip.get("mediana", 0) / off["mediana"]
        p.nota(f"⭐ dipinti / offerti = {round(quota * 100, 1)} %")
    # ⛔⭐ LA PRETESA CHE E' IL CUORE DELLA FASE, e guarda i DIPINTI e non i
    #    consegnati: un fotogramma decodificato che non arriva al vetro non e'
    #    arrivato all'utente.  ⚠ Il denominatore sono gli OFFERTI, non un numero
    #    scritto a mano: se l'alimentatore non tiene, il tetto e' del banco.
    if off.get("mediana"):
        p.che(dip.get("mediana", 0) >= 0.9 * off["mediana"],
              f"⭐ i fotogrammi DIPINTI tengono il passo degli offerti: "
              f"{dip.get('mediana')}/s contro {off['mediana']}/s offerti "
              f"(≥ 90 %)")
        p.che(abs(dip.get("mediana", 0) - con.get("mediana", 0)) <= 0.15 * off["mediana"],
              f"e i dipinti non si scollano dai consegnati: {dip.get('mediana')} "
              f"contro {con.get('mediana')} — se si scollassero, quel che si "
              f"perde si perde fra il decodificatore e il vetro")
    p.che(f["stream"] == r["offerti"],
          f"ogni fotogramma offerto e' diventato uno stream: "
          f"{f['stream']} contro {r['offerti']} offerti")
    p.che(f["corti"] == 0 and f["scartati_misura"] == 0,
          "nessun fotogramma corto e nessuno buttato per misura")
    p.che(not r["fatti"]["errori"],
          f"il decodificatore non ha protestato: {r['fatti']['errori'][:2]}")
    p.che(r["pixel"].get("frazione_nera", 1) < 0.9,
          "la tela porta un'immagine e non e' nera")
    return {"dipinti": dip, "consegnati": con, "offerti": off, "conti": f,
            "quota": (dip.get("mediana", 0) / off["mediana"]) if off.get("mediana") else None}


def giudica_p5a(p, r):
    f = r["fatti"]
    c = f["conti"]
    p.nota(f"arrivo 1(chiave) → 3(chiave) → 2(chiave); conti: {c}")
    p.che(c["scartati_ordine"] == 1,
          f"il VECCHIO si scarta: scartati_ordine = {c['scartati_ordine']} (atteso 1)")
    p.che(c["consegnati"] == 2,
          f"⛔ e il NUOVO no: consegnati = {c['consegnati']} (atteso 2) — una "
          f"pagina che buttasse tutto avrebbe 1")
    p.che(f["ultimo_consegnato"] == 3,
          f"l'ultimo consegnato e' il piu' RECENTE: {f['ultimo_consegnato']} (atteso 3)")
    p.che(c["dipinti"] == 2, f"dipinti = {c['dipinti']} (atteso 2)")
    p.che(not f["errori_protocollo"],
          f"la sessione non si e' chiusa: {f['errori_protocollo'][:1]}")
    return {"conti": c, "ultimo_consegnato": f["ultimo_consegnato"]}


def giudica_p5b(p, r):
    f, c = r["fatti"], r["fatti"]["conti"]
    p.nota("la CHIAVE (numero 10, a pezzi lenti) parte per prima; il DELTA "
           "(numero 11, in un pezzo solo) parte dopo e FINISCE PRIMA")
    p.nota(f"conti: {c}")
    p.che(not f["errori_protocollo"] and not f["congedi"],
          "un fuori ordine vero NON chiude la sessione")
    p.che(f["ultimo_consegnato"] == 10,
          f"la chiave scavalcata arriva lo stesso al decodificatore: "
          f"ultimo_consegnato = {f['ultimo_consegnato']} (atteso 10)")
    p.che(c["consegnati"] == 2,
          f"consegnati = {c['consegnati']} (atteso 2: il 9 e il 10)")
    # ⭐ Non e' una pretesa: e' il PREZZO, misurato.
    costo_b = c["buchi"] - r["prima"]["buchi"]
    costo_k = c["chiavi_chieste"] - r["prima"]["chiavi_chieste"]
    p.nota(f"⭐ IL PREZZO DEL FUORI ORDINE, misurato: {costo_b} buco/buchi e "
           f"{costo_k} RICHIEDI_CHIAVE per UNO scavalcamento, e il fotogramma "
           f"scavalcante (11) e' perso — non e' un difetto della pagina, e' il "
           f"conto che la regola di §5.2 presenta quando due stream si "
           f"sorpassano")
    return {"conti": c, "costo_buchi": costo_b, "costo_chiavi": costo_k}


def giudica_e8(p, r, azzerato):
    f, c = r["fatti"], r["fatti"]["conti"]
    p.nota(f"{r['byte_offerti']} byte, stream {'AZZERATO' if azzerato else 'chiuso con FIN'}; conti: {c}")
    if azzerato:
        p.che(c["azzerati"] == 1, f"azzerati = {c['azzerati']} (atteso 1)")
        p.che(c["completi"] == 0, f"completi = {c['completi']} (atteso 0)")
        p.che(c["consegnati"] == 0,
              f"⛔ NON e' entrato nel decodificatore: consegnati = "
              f"{c['consegnati']} (atteso 0) — forma d'errore E8")
        p.che(c["dipinti"] == 0, f"e non e' arrivato al vetro: dipinti = {c['dipinti']}")
        p.che(c["buchi"] == 1 and c["chiavi_chieste"] == 1,
              f"ed e' stato trattato come un buco: buchi {c['buchi']}, "
              f"chiavi {c['chiavi_chieste']} (attesi 1 e 1)")
        p.che(r["pixel"].get("frazione_nera", 0) > 0.9,
              "la tela e' rimasta nera: non e' stato dipinto niente")
    else:
        p.che(c["completi"] == 1, f"completi = {c['completi']} (atteso 1)")
        p.che(c["azzerati"] == 0, f"azzerati = {c['azzerati']} (atteso 0)")
        p.che(c["consegnati"] == 1,
              f"⛔⭐ GLI STESSI BYTE, con FIN, ENTRANO: consegnati = "
              f"{c['consegnati']} (atteso 1) — senza questa meta' una pagina "
              f"che butta tutto passerebbe il caso negativo")
        p.che(c["dipinti"] == 1, f"e arrivano al vetro: dipinti = {c['dipinti']} (atteso 1)")
        p.che(c["buchi"] == 0, f"e non e' un buco: buchi = {c['buchi']} (atteso 0)")
        p.che(r["pixel"].get("frazione_nera", 1) < 0.9,
              "la tela porta un'immagine")
    return {"conti": c}


def giudica_b(p, r):
    d, f = r["dopo_i_delta"], r["fatti"]
    cd, c = d["conti"], f["conti"]
    p.nota(f"chiave 1, poi il 2 non arriva mai e passano cinque delta (3..7); "
           f"conti dopo i delta: {cd}")
    p.che(cd["buchi"] == 1,
          f"UN buco solo, non cinque: buchi = {cd['buchi']} (atteso 1)")
    p.che(len(d["chiavi_chieste"]) == 1,
          f"⛔ UNA sola RICHIEDI_CHIAVE, non una spirale: "
          f"{len(d['chiavi_chieste'])} (atteso 1) — §5.2")
    p.che(cd["consegnati"] == 1,
          f"e nessun delta e' entrato nel decodificatore mentre il buco era "
          f"aperto: consegnati = {cd['consegnati']} (atteso 1)")
    p.che(d["sospeso"] is True, "il buco e' rimasto aperto fino alla chiave")
    p.che(c["consegnati"] == 2 and c["dipinti"] == 2,
          f"⭐ e con la chiave si ricomincia a DIPINGERE: consegnati "
          f"{c['consegnati']}, dipinti {c['dipinti']} (attesi 2 e 2) — senza "
          f"questa meta', «non chiede chiavi» sarebbe verde anche in una pagina ferma")
    p.che(f["sospeso"] is False, "e il buco si e' chiuso")
    return {"dopo_i_delta": cd, "chiavi_dopo_i_delta": len(d["chiavi_chieste"]),
            "conti": c}


def giudica_tr(p, r, chiedi, rifiuta):
    du, f = r["durante"], r["fatti"]
    p.nota(f"ADATTA_TELA spedita: {chiedi} · TELA(RIFIUTATA): {rifiuta}")
    p.nota(f"durante: trattenuti {du['conti']['trattenuti']}, in mano "
           f"{du['in_mano']}, attese_tela {du['attese_tela']}, "
           f"errori_protocollo {len(du['errori_protocollo'])}")
    if chiedi and not rifiuta:
        p.che(du["conti"]["trattenuti"] == 1,
              f"il fotogramma alla misura mai annunciata si TRATTIENE: "
              f"trattenuti = {du['conti']['trattenuti']} (atteso 1)")
        p.che(not du["errori_protocollo"],
              f"⛔ e la sessione NON si chiude: errori_protocollo = "
              f"{du['errori_protocollo'][:1]} (atteso nessuno)")
        p.che(f["conti"]["consegnati"] == 2,
              f"⭐ e al TELA il trattenuto si RIGIUDICA e passa: consegnati = "
              f"{f['conti']['consegnati']} (atteso 2)")
        p.che(f["conti"]["dipinti"] == 2,
              f"e arriva al vetro: dipinti = {f['conti']['dipinti']} (atteso 2)")
        p.che(f["conti"]["riconfigurazioni"] == 2,
              f"col decodificatore riconfigurato alla misura nuova: "
              f"riconfigurazioni = {f['conti']['riconfigurazioni']} (atteso 2)")
        p.che(f["attese_tela"] == 0 and f["in_mano"] == 0,
              "e non resta niente in mano")
    elif not chiedi:
        p.che(du["conti"]["trattenuti"] == 0,
              f"⛔ SENZA una ADATTA_TELA senza risposta non si trattiene "
              f"niente: trattenuti = {du['conti']['trattenuti']} (atteso 0)")
        p.che(len(du["errori_protocollo"]) == 1,
              f"⛔ ed e' ERRORE_PROTOCOLLO SUBITO: {len(du['errori_protocollo'])} "
              f"(atteso 1) — §6.2, rilievo P21")
        p.che(du["conti"]["consegnati"] == 1,
              f"e il fotogramma non e' entrato: consegnati = "
              f"{du['conti']['consegnati']} (atteso 1, la sola chiave iniziale)")
    else:
        p.che(du["conti"]["trattenuti"] == 1,
              f"prima si trattiene: trattenuti = {du['conti']['trattenuti']}")
        p.che(len(f["errori_protocollo"]) == 1,
              f"⛔ e il TELA(RIFIUTATA) CHIUDE l'attesa: il trattenuto si "
              f"rigiudica ed e' ERRORE_PROTOCOLLO — "
              f"{len(f['errori_protocollo'])} (atteso 1)")
        p.che(f["in_mano"] == 0 and f["attese_tela"] == 0,
              f"e non resta niente in mano: {f['in_mano']} trattenuti, "
              f"{f['attese_tela']} attese")
    return {"durante": du["conti"], "dopo": f["conti"],
            "errori_protocollo_durante": du["errori_protocollo"],
            "errori_protocollo_dopo": f["errori_protocollo"]}


def giudica_v3s(p, r):
    """⛔ NON e' una pretesa sul prodotto: e' la misura che ha fatto RITIRARE la
    cura del 13 agosto — un `ResizeObserver` per la barra di scorrimento.  Resta
    nel banco perche' il giorno in cui `html { overflow-y: scroll }` sparisse dal
    foglio di stile, questo caso diventa rosso e lo dice."""
    sp, ac = r["spento"], r["acceso"]
    p.nota(f"impaginazione SPENTA  clientWidth×clientHeight {sp[:2]}, "
           f"scrollHeight {sp[3]}")
    p.nota(f"impaginazione ACCESA  clientWidth×clientHeight {ac[:2]}, "
           f"scrollHeight {ac[3]}")
    p.che(ac[3] > sp[3] * 1.4,
          f"la scena e' quella giusta: accendendo la tela il documento diventa "
          f"molto piu' alto ({sp[3]} → {ac[3]} px)")
    p.che(sp[0] == ac[0],
          f"⭐ e la larghezza utile NON si muove ({sp[0]} → {ac[0]}): "
          f"`html {{ overflow-y: scroll }}` tiene la barra verticale sempre "
          f"presente, quindi la famiglia «la barra compare e la vista resta "
          f"vecchia» e' gia' curata dal foglio di stile")
    p.che(ac[2] == ac[0],
          f"e la tela non fa comparire nessuna barra orizzontale: scrollWidth "
          f"{ac[2]} = clientWidth {ac[0]}")
    p.che(r["fatti"]["tela"][0] == round(ac[0] * r["dpr"]),
          f"la tela vale la vista: {r['fatti']['tela'][0]} px "
          f"(attesi {round(ac[0] * r['dpr'])})")
    return {"spento": sp, "acceso": ac, "tela": r["fatti"]["tela"]}


def giudica_v3(p, r):
    a, b = r["prima"], r["dopo"]
    p.nota("⛔ su questo palco `requestAnimationFrame` non gira (0 quadri in 3 s, "
           "misurato): la CONSEGNA del `resize` non e' coperta da questo caso — "
           "solo quel che succede dopo")
    p.nota(f"finestra chiesta {r['chiesta']}; vista utile {a['cliente']} → "
           f"{b['cliente']} (dpr {b['dpr']})")
    p.nota(f"tela {a['tela']} → {b['tela']}; viste {a['viste']} → {b['viste']}; "
           f"ricomposizioni {a['ricomposizioni']} → {b['ricomposizioni']}")
    if a["cliente"] == b["cliente"]:
        p.dubbio("⛔ NON CONCLUDENTE: la finestra non e' cambiata davvero")
        return {"non_concludente": True}
    p.che(b["viste"] > a["viste"],
          f"la vista si e' rinegoziata: viste {a['viste']} → {b['viste']}")
    p.che(b["tela"][0] == round(b["cliente"][0] * b["dpr"]) and
          b["tela"][1] == round(b["cliente"][1] * b["dpr"]),
          f"e la tela vale la vista NUOVA: {b['tela']} (attesa "
          f"{[round(b['cliente'][0] * b['dpr']), round(b['cliente'][1] * b['dpr'])]})")
    p.che(b["dipinti"] == a["dipinti"],
          f"⛔ e NON e' arrivato nessun fotogramma nuovo (dipinti {a['dipinti']} "
          f"→ {b['dipinti']}): quel che si e' ridipinto e' il DEPOSITO")
    p.che(b["ricomposizioni"] > a["ricomposizioni"],
          f"ma la tela e' stata RICOMPOSTA ({a['ricomposizioni']} → "
          f"{b['ricomposizioni']})")
    p.che(r["dipinta"] and r["prima_dipinta"] and
          [r["dipinta"]["l"], r["dipinta"]["a"]] !=
          [r["prima_dipinta"]["l"], r["prima_dipinta"]["a"]],
          f"e la misura dipinta e' CAMBIATA: "
          f"{r['prima_dipinta'] and [r['prima_dipinta']['l'], r['prima_dipinta']['a']]} → "
          f"{r['dipinta'] and [r['dipinta']['l'], r['dipinta']['a']]}")
    fn = r["pixel"].get("frazione_nera")
    p.che(fn is not None and fn < 0.9,
          f"⭐ e a schermo FERMO l'immagine c'e' ancora: frazione nera {fn} — "
          f"scrivere `canvas.width` svuota la tela, e senza il deposito qui "
          f"resterebbe nera")
    p.che(not r["fatti"]["errori"], f"nessun errore: {r['fatti']['errori'][:1]}")
    return {"prima": a, "dopo": b, "frazione_nera": fn,
            "dipinta": r["dipinta"], "prima_dipinta": r["prima_dipinta"]}


def giudica_v3d(p, r):
    if not r.get("col_deposito"):
        p.nota("⚠ questa e' la variante SENZA deposito: non c'e' niente da "
               "cronometrare, e si guarda solo che cosa resta sulla tela dopo "
               "un ridimensionamento a schermo fermo")
    else:
        p.nota(f"⭐ la COPIA 1:1 che il deposito AGGIUNGE ({r['deposito']}), "
               f"cronometrata su {r['giri']} giri: {round(r['ms_copia'] * 1000)} µs "
               f"per fotogramma, cioe' il "
               f"{round(r['ms_copia'] / 16.667 * 100, 2)} % di un intervallo di "
               f"quadro a 60 Hz")
        p.nota(f"e la SCALATURA alla vista {r['dipinta']}, che si paga in tutte e "
               f"due le strade: {round(r['ms_scala'] * 1000)} µs "
               f"({round(r['ms_scala'] / 16.667 * 100, 1)} % di un quadro)")
    p.che(r["sospeso"] is True,
          "il buco e' aperto: da qui non arriva nessun fotogramma finche' non "
          "arriva una chiave (§5.2)")
    fn = r["pixel_dopo_ridimensionamento"].get("frazione_nera")
    p.nota(f"e dopo il ridimensionamento della finestra, a schermo fermo, la "
           f"frazione nera della tela e': {fn}")
    # ⛔ Le due meta' della stessa domanda, e la seconda e' il CONTROLLO
    #    NEGATIVO: senza deposito la tela DEVE restare nera.  Se restasse
    #    dipinta, vorrebbe dire che a ricomporla e' qualcos'altro — e allora il
    #    verde della prima meta' non proverebbe che a farlo e' il deposito.
    if r.get("col_deposito"):
        p.che(fn is not None and fn < 0.9,
              f"⭐ la tela e' stata RICOMPOSTA dal deposito: frazione nera {fn} "
              f"(sotto 0.9).  ⛔ Senza deposito qui e' 1.0 — nero — e ci resta "
              f"finche' non arriva la chiave, cioe' fino a 200 ms di smorzatore "
              f"del server piu' un giro di rete (§5.2)")
    else:
        p.che(fn is not None and fn > 0.9,
              f"⛔⭐ IL CONTROLLO NEGATIVO: senza deposito la tela resta NERA "
              f"(frazione nera {fn}, sopra 0.9) — e ci resta finche' non arriva "
              f"la chiave.  E' il prezzo che il deposito compra, misurato invece "
              f"che dichiarato")
    return {"col_deposito": r.get("col_deposito"),
            "microsecondi_copia": round((r.get("ms_copia") or 0) * 1000),
            "microsecondi_scala": round((r.get("ms_scala") or 0) * 1000),
            "frazione_nera_dopo_ridimensionamento": fn,
            "dipinta": r.get("dipinta")}


# ═══════════════════════════════════════════════════════════════════════════
# 7. IL GIRO, IL REGISTRO E LA CERTIFICAZIONE
# ═══════════════════════════════════════════════════════════════════════════

SECONDI_REGIME = 10.0

# ⛔ Ogni caso: (sorgente JS, parametri, giudice).  Il nome della sequenza si
#    mette qui e non nel JS, cosi' la scena e' dichiarata in un posto solo.
def _casi(grande, piccola):
    return {
        "D60":  (CASO_REGIME, {"seq": grande, "ritmo": 60, "secondi": SECONDI_REGIME},
                 lambda p, r: giudica_regime(p, r)),
        "D30":  (CASO_REGIME, {"seq": grande, "ritmo": 30, "secondi": SECONDI_REGIME},
                 lambda p, r: giudica_regime(p, r)),
        "D720": (CASO_REGIME, {"seq": "av1-1280x720", "ritmo": 60, "secondi": SECONDI_REGIME},
                 lambda p, r: giudica_regime(p, r)),
        "D480": (CASO_REGIME, {"seq": "av1-854x480", "ritmo": 60, "secondi": SECONDI_REGIME},
                 lambda p, r: giudica_regime(p, r)),
        "P5a":  (CASO_P5A, {"seq": grande}, giudica_p5a),
        "P5b":  (CASO_P5B, {"seq": grande}, giudica_p5b),
        "E8":   (CASO_E8, {"seq": grande, "azzerato": "true"},
                 lambda p, r: giudica_e8(p, r, True)),
        "E8p":  (CASO_E8, {"seq": grande, "azzerato": "false"},
                 lambda p, r: giudica_e8(p, r, False)),
        "B":    (CASO_B, {"seq": grande}, giudica_b),
        "TR":   (CASO_TR, {"seq": grande, "seq2": piccola, "chiedi": "true",
                           "rifiuta": "false"},
                 lambda p, r: giudica_tr(p, r, True, False)),
        "TRn":  (CASO_TR, {"seq": grande, "seq2": piccola, "chiedi": "false",
                           "rifiuta": "false"},
                 lambda p, r: giudica_tr(p, r, False, False)),
        "TRr":  (CASO_TR, {"seq": grande, "seq2": piccola, "chiedi": "true",
                           "rifiuta": "true"},
                 lambda p, r: giudica_tr(p, r, True, True)),
        "V3":   ("py", caso_v3, giudica_v3, {"seq": grande}),
        "V3s":  (CASO_V3_ACCESO, {"seq": grande}, giudica_v3s),
        "Dsat": (CASO_SATURA, {"seq": grande, "secondi": 8},
                 lambda p, r: giudica_regime(p, r)),
        "V3d":  (CASO_V3D, {"seq": grande}, giudica_v3d),
    }


ATTESA_PRONTA = r"""
(function () { return !!(window.REMOTIX && window.REMOTIX.schermo
                         && window.REMOTIX.leggi_uno_stream); })()
"""


def apri(palco, variante):
    """Una pagina FRESCA.  ⛔ Fresca per ogni caso, e non per ogni variante: il
    caso V3 misura l'impaginazione SPENTA, che un caso precedente ha gia'
    acceso.  Un caso che eredita lo stato di quello prima non misura quel che
    dice il suo nome."""
    c = palco.c
    c.chiama("Page.navigate", url=f"http://127.0.0.1:{palco.porta}/{variante}/pagina.html")
    for _ in range(80):
        time.sleep(0.25)
        try:
            if c.valuta(ATTESA_PRONTA, attendi=False) is True:
                break
        except Exception:
            pass
    else:
        raise RuntimeError(f"⛔ la pagina «{variante}» non ha esposto REMOTIX in 20 s")
    # ⛔ Si verifica che la pagina servita sia QUELLA: una variante che arriva
    #    dalla cache e una servita hanno lo stesso aspetto da qui.
    marca = c.valuta(
        "(document.documentElement.outerHTML.indexOf('%s') >= 0)"
        % ("dipingi_diretto" if variante == "senza-deposito" else
           "attese_tela"), attendi=False)
    if marca is not True and variante != "senza-deposito":
        raise RuntimeError("⛔ la pagina servita non porta la marca attesa")
    r = c.valuta(PRELUDIO + "\n(window.__B16 && !window.__B16.guaio) === true",
                 attendi=False)
    if r is not True:
        raise RuntimeError(f"⛔ il preludio non si e' installato: {r}")


def giro(palco, variante, nomi, grande, piccola, quando, giro_id):
    casi = _casi(grande, piccola)
    esiti = []
    for nome in nomi:
        if nome not in casi:
            raise RuntimeError(f"⛔ caso sconosciuto: {nome}")
        voce = casi[nome]
        log(f"{variante} · caso {nome}")
        apri(palco, variante)
        t0 = time.time()
        # ⛔ Alcuni casi hanno bisogno di un'azione che DENTRO la pagina non si
        #    puo' fare — una finestra non si allarga da sola — e allora li guida
        #    Python.  La forma e' dichiarata qui e non indovinata dal chiamante.
        if voce[0] == "py":
            _, funzione, giudice, par = voce
            grezzo = funzione(palco, par)
        else:
            sorgente, par, giudice = voce
            grezzo = palco.c.valuta(sorgente % par, attendi=True)
        durata = round(time.time() - t0, 1)
        p = Pretese(nome)
        if not isinstance(grezzo, dict) or "⛔ eccezione" in (grezzo or {}):
            p.che(False, f"il caso non e' arrivato in fondo: {str(grezzo)[:400]}")
            sunto = {}
        else:
            sunto = giudice(p, grezzo) or {}
        inf(f"({durata} s)")
        e = {"quando": quando, "giro": giro_id, "variante": variante,
             "caso": nome, "durata_s": durata, "guai": p.guai,
             "esito": "verde" if p.guai == 0 else "rosso",
             "pretese": p.righe, "sunto": sunto}
        with REGISTRO.open("a") as f:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")
        esiti.append(e)
    return esiti


# ⛔⭐ LA CERTIFICAZIONE, CON L'ATTESO SCRITTO PRIMA — `LEZIONI.md` §1.2.
#    Ogni riga: il guasto, i casi che DEVONO diventare rossi, e i casi che
#    devono restare VERDI.  ⚠ La seconda meta' non e' un di piu': un guasto che
#    facesse diventare rosso TUTTO non proverebbe che il caso guarda proprio
#    quella proprieta'.
CERTIFICAZIONE = [
    ("nondipinge",       ["D60"],         [],       "il conto dei dipinti non sale piu'"),
    ("ordine-spento",    ["P5a"],         ["E8"],   "il fotogramma vecchio entra"),
    ("ordine-tutto",     ["P5a", "P5b"],  ["E8"],   "si butta anche il nuovo"),
    ("reset-consegnato", ["E8"],          ["E8p"],  "l'azzerato entra nel decodificatore"),
    ("spirale",          ["B"],           ["E8p"],  "una RICHIEDI_CHIAVE per delta"),
    ("trattieni-sempre", ["TRn"],         ["TR"],   "trattiene anche senza ADATTA_TELA"),
    ("chiude-sempre",    ["TR"],          ["TRn"],  "chiude anche con ADATTA_TELA in volo"),
    ("vista-fissa",      ["V3"],          ["E8p"],  "la vista non si applica piu'"),
]


def principale():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("--porta", type=int, default=7604)
    a.add_argument("--diagnosi", type=int, default=9604)
    a.add_argument("--schermo", default=":81")
    a.add_argument("--finestra", default="1400x900")
    a.add_argument("--casi", default="")
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--sequenze", action="store_true")
    a.add_argument("--gpu", action="store_true",
                   help="senza --disable-gpu (di norma su Xvfb non serve a niente)")
    args = a.parse_args()

    log("le sequenze — la scena, generata e dichiarata")
    seq = {}
    for l, al in MISURE:
        d = genera_sequenza(l, al)
        seq[(l, al)] = d
        inf(f"av1-{l}x{al}: {d['quanti']} fotogrammi ({len(d['chiavi'])} chiave), "
            f"{d['byte']} byte, «{d['stringa']}» (profilo {d['profilo']}, "
            f"livello {d['livello']})")
    if args.sequenze:
        return 0
    grande, piccola = "av1-1920x1080", "av1-1280x720"

    quando = datetime.now(timezone.utc).isoformat()
    giro_id = "b16-" + datetime.now().strftime("%Y%m%d-%H%M%S")
    log(f"il palco — giro {giro_id}")
    inf(f"Chrome: {versione_di('google-chrome')}")
    inf(f"schermo {args.schermo} · porta {args.porta} · diagnosi {args.diagnosi}")
    inf(f"⛔ decodifica in SOFTWARE (Xvfb, --disable-gpu={not args.gpu}): il "
        f"numero che esce e' un pavimento su questa macchina, non il tetto "
        f"della pagina (LEZIONI.md §6.3)")

    fl, fa = (int(x) for x in args.finestra.split("x"))
    srv = ThreadingHTTPServer(("127.0.0.1", args.porta), Servente)
    Thread(target=srv.serve_forever, daemon=True).start()
    palco = Palco(args.schermo, (fl, fa), args.diagnosi, gpu=args.gpu)
    palco.porta = args.porta
    esito = 0
    try:
        palco.accendi()
        if args.certifica:
            log("⛔ LA CERTIFICAZIONE — sano, poi ogni guasto, contro l'atteso "
                "scritto prima")
            interessati = sorted({c for _, rossi, verdi, _ in CERTIFICAZIONE
                                  for c in rossi + verdi})
            sani = {e["caso"]: e for e in
                    giro(palco, "sano", interessati, grande, piccola, quando, giro_id)}
            for nome, rossi, verdi, che_rompe in CERTIFICAZIONE:
                log(f"⛔ guasto «{nome}» — {che_rompe}")
                g = {e["caso"]: e for e in
                     giro(palco, nome, rossi + verdi, grande, piccola, quando, giro_id)}
                for c in rossi:
                    if sani.get(c, {}).get("esito") != "verde":
                        ko(f"il caso {c} non era verde da sano: la certificazione "
                           f"non dice niente")
                        esito = 1
                    elif g[c]["esito"] == "rosso":
                        ok(f"⭐ {c} diventa ROSSO col guasto: il caso vede il difetto")
                    else:
                        ko(f"⛔ {c} resta VERDE col guasto «{nome}»: il caso NON "
                           f"vede il difetto che dice di vedere")
                        esito = 1
                for c in verdi:
                    if g[c]["esito"] == "verde":
                        ok(f"{c} resta verde: il guasto non sporca quel che non tocca")
                    else:
                        ko(f"⛔ {c} diventa rosso col guasto «{nome}», che non lo "
                           f"riguarda: il caso guarda piu' cose di quel che dice")
                        esito = 1
            return esito
        nomi = ([x.strip() for x in args.casi.split(",") if x.strip()] or
                ["D60", "D30", "D720", "D480", "Dsat", "P5a", "P5b", "E8",
                 "E8p", "B", "TR", "TRn", "TRr", "V3", "V3s", "V3d"])
        e = giro(palco, "sano", nomi, grande, piccola, quando, giro_id)
        if "D60" in nomi:
            log("⭐ e la stessa domanda senza il deposito — il secondo drawImage")
            e += giro(palco, "senza-deposito", ["D60", "Dsat", "V3d"], grande,
                      piccola, quando, giro_id)
        log("il conto del giro")
        for x in e:
            (ok if x["esito"] == "verde" else ko)(
                f"{x['variante']}/{x['caso']}: {x['esito']} ({x['guai']} guai)")
            if x["esito"] != "verde":
                esito = 1
        inf(f"registro: {REGISTRO}")
        return esito
    finally:
        palco.spegni()
        srv.shutdown()


if __name__ == "__main__":
    sys.exit(principale())
