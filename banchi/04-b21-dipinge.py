#!/usr/bin/env python3
"""04-b21-dipinge.py — ⛔ I FOTOGRAMMI **DIPINTI**, non quelli consegnati.

    python3 banchi/04-b21-dipinge.py --matrice     l'esperimento isolato
    python3 banchi/04-b21-dipinge.py --certifica   sano → guasto → risanato
    python3 banchi/04-b21-dipinge.py --json FILE   deposita il verbale

===========================================================================
⛔ PERCHE' ESISTE — la tesi da refutare

`fasi/03-movimento.md` §0-ter, `[M]` 14 agosto 2026, sessione vera:

    1748 fotogrammi consegnati (118 chiavi) … 0 guasti — codec 1
    [192.168.0.3]: §5.2 vuole una CHIAVE — richiesta girata al palco  ×1659

⇒ **Il server manda, il client rifiuta, chiede una chiave, per sempre.**
   Schermo nero.

⛔⛔ E LA TRAPPOLA E' GIA' SCATTATA UNA VOLTA: i banchi dicevano il contrario —
    1 047 dipinti, 30 fps, `consegnati == dipinti`.  Quel giro aveva **una
    scena sintetica** e **un Chrome lanciato dal banco**; la sessione vera ha
    **il browser dell'utente** e **il suo desktop**.
    ⇒ *Un banco che dice si' e un utente che vede nero: il banco stava
    misurando un'altra cosa.*

⭐ Da cui la forma di questo banco.  Non rifa' il giro della sessione sperando
   che stavolta si rompa: **isola la funzione sospetta e la chiama da fuori**
   (`CODER.md` §3.6), su una MATRICE in cui una casella sola puo' essere rossa.

===========================================================================
⭐⭐ L'IPOTESI, SCRITTA PRIMA DI MISURARE — e da dove viene

Letta nel codice, non supposta:

  `[R]` `src/rcp.c:1198`   `NOSTRA_PROFONDITA "8,10"`, e `prima_comune()`
                           prende **la prima in comune** ⇒ col client che
                           dichiara `8,10` si negozia **8**.
  `[R]` `src/figlio.c:1605` `r.profondita = 10;` — **fisso**.  La profondita'
                           negoziata NON arriva mai al codificatore.
  `[R]` `src/pagina.html:657` la stringa di WebCodecs porta il profilo della
                           profondita' NEGOZIATA: `hev1.1.6…` = Main (8 bit),
                           `hev1.2.4…` = Main10.

⇒ **Il server dice «8» e manda 10.**  La pagina configura un decodificatore
  **Main** e riceve un flusso **Main10**.

⛔ E le sonde non lo vedono: `SONDE["hevc-8"]` e' un Main VERO a 8 bit, e
   `SONDE_MISURA.hevc` sono **tutte a `profondita: 8`** (`pagina.html:589`).
   La sonda prova una cosa, la sessione ne riceve un'altra.

⚠ Perche' AV1 non e' mai caduto nello stesso buco: `[?]` dav1d legge la
  profondita' dalla sequence header e non dalla stringa.  ⛔ E' un'ipotesi, ed
  e' **una casella della matrice**, non una premessa.

===========================================================================
⛔ LA MATRICE, E PERCHE' HA QUATTRO CASELLE E NON UNA

              flusso Main (8 bit)     flusso Main10 (10 bit)
  config Main      A ⭐ controllo +          C ⛔ L'INCOGNITA
  config Main10    B                        D ⭐ controllo +

⭐ **A e D sono i controlli positivi**: «questo strumento sa dipingere un
   fotogramma che c'e' di sicuro?»  ⛔ Se A o D non dipinge, **il verdetto su C
   non si scrive**: sarebbe indistinguibile fra «il prodotto ha il difetto» e
   «il banco non sa dipingere» (`CODER.md` §3.3, §3.10).

⚠ E la matrice si gira **due volte**, a 64×48 e a 1920×1080: se C cadesse solo
  alla misura grande, la causa sarebbe la misura e non il profilo.

===========================================================================
⛔ ZERO E FALLIMENTO NON SI CONFONDONO — `CODER.md` §3.10

Ogni casella ha **tre** esiti e non due: `dipinge`, `non dipinge (motivo)`,
`non ho potuto guardare`.  Il terzo non e' un rosso: e' un buco nella misura, e
si conta a parte.

===========================================================================
⛔ IL PALCO SI DICHIARA E NON SI SPOSTA — `README.md` riga 397

I banchi browser **girano sul desktop dell'utente credendo di essere su uno
schermo finto**: Chrome ignora `DISPLAY` e va su Wayland da
`XDG_SESSION_TYPE`.  ⛔ **Non si forza `--ozone-platform=x11`**: sul vero Xvfb
non c'e' GPU, HEVC non si decodifica in hardware, e si curerebbe la scena
distruggendo la misura.

⇒ Qui il palco e' **quello vero, di proposito**, e si **verifica dall'altro
   capo** — `screen`, `webgl`, le bandiere — e finisce nel verbale accanto a
   ogni numero.  ⚠ Il **pezzo cieco** di `STUDI.md` §web §6.2 (16-40 ms fra il disegno
   e il pixel acceso) **esiste su questo palco** e non esisterebbe su Xvfb: qui
   non si misurano tempi, si contano pixel, e per questo non lo si dichiara
   accanto a un numero che non c'e'.

===========================================================================
⛔ LA CERTIFICAZIONE — sano → guasto → risanato

    sano       A e D dipingono in tutt'e due le misure (8 caselle-controllo)
    guasto     `GUASTO=una-tinta` costruisce i flussi di UNA tinta sola
               ⇒ **nessuna** casella deve dire «dipinge»: la prova dei pixel
                 e' due letture giuste E DIVERSE, e una tinta sola non le da'
    guasto     `GUASTO=vuoto` manda zero byte al decodificatore
               ⇒ nessuna casella dice «dipinge», e **nessuna** dice «non ho
                 potuto guardare»: un flusso vuoto e' un fallimento CHE SI
                 NOMINA, non uno zero silenzioso
    risanato   come il sano

⛔ Un banco che restasse verde col guasto dentro sarebbe la peggiore delle
   prove, perche' da' fiducia (`CODER.md` §4.6).
"""
import argparse
import base64
import http.server
import importlib.util
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
DEPOSITO = os.path.dirname(QUI)

# ⛔ Le porte sono MIE — l'anello A2 ha 7611-7615 (`fasi/04-si-comanda.md`).
#    Senza porte proprie il ban per indirizzo che fa scattare un banco ferma
#    gli altri nove che girano in parallelo.
PORTA_HTTP = 7614
PORTA_CDP = 7615


# ═══════════════════════════════════════════════════════════════════════════
# §1  ATTREZZI — e non se ne riscrive nessuno che esista gia'
# ═══════════════════════════════════════════════════════════════════════════
_moduli = {}


def carica(nome, percorso):
    """⛔ `import 02-pagina-sonda-codec` e' impossibile (il nome comincia per
    cifra): si carica con `importlib`, come gia' fa `03-b17-ritardo.py:167`."""
    if nome in _moduli:
        return _moduli[nome]
    spec = importlib.util.spec_from_file_location(nome, percorso)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    _moduli[nome] = m
    return m


def sonda_modulo():
    """⭐ Il costruttore dei flussi e' gia' scritto e gia' certificato
    (`02-pagina-sonda-codec.py`): qui si RIUSA cambiandogli la misura, non se
    ne scrive un secondo.  ⛔ Due costruttori di flussi darebbero due flussi
    diversi sotto la stessa etichetta."""
    return carica("sonda_codec", os.path.join(QUI, "02-pagina-sonda-codec.py"))


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
# §2  I FLUSSI — costruiti qui, e con il SECONDO TESTIMONE nei byte
# ═══════════════════════════════════════════════════════════════════════════
def profilo_nei_byte(flusso, codec):
    """⛔ IL PROFILO SI LEGGE NEI BYTE, non nella riga di comando che l'ha
    chiesto.  ⚠ E' la lezione che e' costata il codec dell'intero prodotto
    (`02-pagina-sonda-codec.py:126`): `-profile:v main10` era stato **chiesto e
    non applicato, senza un errore**, e la stringa e i byte erano d'accordo fra
    loro e discordi dal flusso.

    ⇒ Ritorna `(profilo, profondita)` letti da `ffprobe`, o `(None, None)` con
      il motivo: «non ho potuto guardare» non e' «profilo sbagliato»."""
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=False) as f:
        f.write(flusso)
        percorso = f.name
    try:
        r = subprocess.run(
            ["ffprobe", "-hide_banner", "-v", "error", "-f",
             "hevc" if codec == "hevc" else "obu",
             "-show_entries", "stream=profile,pix_fmt,width,height",
             "-of", "json", percorso],
            capture_output=True, text=True)
        if r.returncode != 0:
            return None, None, r.stderr.strip()[-200:]
        s = json.loads(r.stdout)["streams"][0]
        return s.get("profile"), s.get("pix_fmt"), None
    except Exception as e:                                     # noqa: BLE001
        return None, None, str(e)[:200]
    finally:
        os.unlink(percorso)


def costruisci_flussi(misure, guasto=""):
    """I flussi della matrice: per ogni misura, HEVC Main e HEVC Main10, piu'
    AV1 a 8 e a 10 bit — AV1 e' il **controllo di specie**: se cadesse anche
    lui, la causa non sarebbe il profilo HEVC."""
    sc = sonda_modulo()
    fuori = {}
    for (l, a) in misure:
        sc.LARGHEZZA, sc.ALTEZZA = l, a
        for codec in ("hevc", "av1"):
            for prof in (8, 10):
                nome = "%s-%d-%dx%d" % (codec, prof, l, a)
                if guasto == "vuoto":
                    flusso = b""
                    profilo = pix = None
                    guai_p = "flusso VUOTO: guasto innestato apposta"
                else:
                    flusso = (sc.costruisci_hevc(prof, guasto) if codec == "hevc"
                              else sc.costruisci_av1(prof, guasto))
                    profilo, pix, guai_p = profilo_nei_byte(flusso, codec)
                # ⛔ Il controllo positivo del COSTRUTTORE: si ridecodifica il
                #    flusso appena fatto e si guarda che le due meta' siano
                #    ancora due tinte diverse.  Senza, «due tinte» sarebbe una
                #    proprieta' della SORGENTE, non del flusso.
                if flusso:
                    lette, guai = sc.tinte_del_flusso(flusso, codec, prof)
                else:
                    lette, guai = None, "flusso vuoto"
                fuori[nome] = {
                    "codec": codec, "profondita": prof, "l": l, "a": a,
                    "byte": len(flusso),
                    "dati": base64.b64encode(flusso).decode(),
                    "sinistra": list(sc.SINISTRA), "destra": list(sc.DESTRA),
                    "profilo_nei_byte": profilo, "pix_fmt_nei_byte": pix,
                    "guai_profilo": guai_p,
                    "riletto": lette, "guai_rilettura": guai,
                }
    return fuori


# ⛔ Le stringhe di WebCodecs sono **le stesse che scrive il prodotto**
#    (`src/pagina.html:657`), copiate qui a mano e con la riga accanto: se un
#    giorno divergessero, il banco misurerebbe una stringa che il prodotto non
#    manda mai.  ⚠ `L153` = livello 5.1, quello che `LIVELLO_DICHIARATO`
#    dichiara (`pagina.html:397`).
STRINGHE = {
    "hevc": {8: "hev1.1.6.L153.B0", 10: "hev1.2.4.L153.B0"},
    "av1": {8: "av01.0.13M.08", 10: "av01.0.13M.10"},
}


# ═══════════════════════════════════════════════════════════════════════════
# §3  LA PAGINA DELLA MATRICE — piccola, e non e' il prodotto
# ═══════════════════════════════════════════════════════════════════════════
# ⛔ La prova dei pixel e' scritta qui e NON presa in prestito dal prodotto, e
#    va detto perche': se il banco chiamasse `dipingi_sonda()` di
#    `src/pagina.html`, un difetto DENTRO quella funzione sarebbe invisibile —
#    il banco e il prodotto sbaglierebbero insieme.  ⚠ Il prezzo e' che le due
#    prove possono divergere: per questo la regola e' scritta identica in
#    tutt'e due — due letture giuste E DIVERSE, su una tela riempita di
#    magenta, che non e' nessuna delle due tinte.
PAGINA = r"""<!doctype html>
<html lang="it"><head><meta charset="utf-8"><title>04-b21 · la matrice</title></head>
<body><pre id="esito">in corso…</pre><script>
const CASI = __CASI__;
const FLUSSI = __FLUSSI__;

function byte(b64) {
  const s = atob(b64); const u = new Uint8Array(s.length);
  for (let i = 0; i < s.length; i++) u[i] = s.charCodeAt(i);
  return u;
}
function medio(d, w, x0, y0, x1, y1) {
  let r = 0, g = 0, b = 0, n = 0;
  for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) {
    const i = (y * w + x) * 4; r += d[i]; g += d[i+1]; b += d[i+2]; n++;
  }
  return n ? [Math.round(r/n), Math.round(g/n), Math.round(b/n)] : null;
}
function lontano(a, b) {
  return Math.round(Math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2 + (a[2]-b[2])**2));
}

/* ⛔ Tre esiti e non due: `dipinge`, `non dipinge`, `non ho potuto guardare`. */
function prova(caso) {
  return new Promise((risolvi) => {
    const f = FLUSSI[caso.flusso];
    const RL = 64, RA = 48;
    const tela = document.createElement("canvas");
    tela.width = RL; tela.height = RA;
    const p = tela.getContext("2d", { willReadFrequently: true, alpha: false });
    if (!p) { risolvi({ stato: "cieco", perche: "niente contesto 2d" }); return; }
    p.fillStyle = "#7a007a"; p.fillRect(0, 0, RL, RA);   /* magenta: nessuna delle due */

    let fatto = false, dec = null;
    const t0 = performance.now();
    const sveglia = setTimeout(() => chiudi({
      stato: "no", perche: "nessun fotogramma entro 4 s" }), 4000);
    function chiudi(e) {
      if (fatto) return; fatto = true; clearTimeout(sveglia);
      try { if (dec && dec.state !== "closed") dec.close(); } catch (x) {}
      e.ms = Math.round(performance.now() - t0);
      risolvi(e);
    }
    const config = { codec: caso.stringa, codedWidth: f.l, codedHeight: f.a,
                     optimizeForLatency: true };
    VideoDecoder.isConfigSupported(config).then((r) => {
      caso.isConfigSupported = r.supported;
      if (r.supported !== true) {
        chiudi({ stato: "no", perche: "isConfigSupported: " + r.supported });
        return;
      }
      try {
        dec = new VideoDecoder({
          output: (fr) => {
            const m = [fr.displayWidth || fr.codedWidth,
                       fr.displayHeight || fr.codedHeight];
            const formato = (fr.format === undefined) ? "assente" : fr.format;
            try { p.drawImage(fr, 0, 0, RL, RA); }
            catch (e) { try { fr.close(); } catch (x) {}
                        chiudi({ stato: "cieco", perche: "drawImage: " + e }); return; }
            try { fr.close(); } catch (e) {}
            let d;
            try { d = p.getImageData(0, 0, RL, RA).data; }
            catch (e) { chiudi({ stato: "cieco", perche: "getImageData: " + e }); return; }
            const b = 4;
            const sx = medio(d, RL, b, b, RL/2 - b, RA - b);
            const dx = medio(d, RL, RL/2 + b, b, RL - b, RA - b);
            const bene = sx && dx &&
              lontano(sx, f.sinistra) < lontano(sx, f.destra) &&
              lontano(dx, f.destra) < lontano(dx, f.sinistra);
            chiudi({ stato: bene ? "si" : "no", formato: formato, misura: m,
                     letture: { sinistra: sx, destra: dx },
                     perche: bene ? null : "il fotogramma e' uscito ma i pixel "
                       + "non sono quelli del flusso (sinistra " + sx
                       + ", destra " + dx + ")" });
          },
          /* ⛔ Il richiamo d'errore e' l'unico posto in cui il decodificatore
             puo' dire «sono fallito»: buttarlo renderebbe ogni fallimento
             indistinguibile da uno zero. */
          error: (e) => chiudi({ stato: "no", perche: String(e) }),
        });
        dec.configure(config);
        dec.decode(new EncodedVideoChunk({
          type: "key", timestamp: 0, data: byte(f.dati) }));
      } catch (e) { chiudi({ stato: "no", perche: String(e) }); }
    }).catch((e) => chiudi({ stato: "cieco",
                             perche: "isConfigSupported ha lanciato: " + e }));
  });
}

async function tutto() {
  const fuori = { casi: [], webcodecs: typeof VideoDecoder !== "undefined" };
  if (!fuori.webcodecs) { window.B21 = fuori; document.body.dataset.b21 = "fatto"; return; }
  for (const caso of CASI) {
    const r = await prova(caso);
    fuori.casi.push(Object.assign({}, caso, r));
    document.getElementById("esito").textContent =
      fuori.casi.length + "/" + CASI.length;
  }
  /* ⛔ Il palco si dichiara DA DENTRO, e si verifica dall'altro capo. */
  const c = document.createElement("canvas").getContext("webgl");
  const dbg = c && c.getExtension("WEBGL_debug_renderer_info");
  fuori.palco = {
    screen: screen.width + "x" + screen.height,
    dpr: devicePixelRatio,
    finestra: innerWidth + "x" + innerHeight,
    webgl: dbg ? c.getParameter(dbg.UNMASKED_RENDERER_WEBGL) : "non letto",
    ua: navigator.userAgent,
    crossOriginIsolated: crossOriginIsolated,
  };
  window.B21 = fuori;
  document.getElementById("esito").textContent = "fatto";
  document.body.dataset.b21 = "fatto";
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


# ═══════════════════════════════════════════════════════════════════════════
# §4  IL PALCO — dichiarato, non spostato
# ═══════════════════════════════════════════════════════════════════════════
class Palco:
    """⛔ Chrome sul desktop VERO, e si dice.  ⚠ Nessuna `--ozone-platform`,
    nessun `--disable-gpu`: HEVC in hardware vuole la GPU vera, e questo banco
    esiste per riprodurre quel che vede l'utente."""

    def __init__(self, gpu=True, finestra=(1280, 900)):
        self.t = tempfile.mkdtemp(prefix="04-b21-")
        self.gpu = gpu
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
                "--window-size=%d,%d" % (l, a), "--window-position=0,0",
                url]
        if not self.gpu:
            flag.insert(1, "--disable-gpu")
        # ⛔ Le bandiere si conservano perche' vanno nel verbale: un default nel
        #    sorgente non e' una dichiarazione (`LEZIONI.md` §2.0).
        self.bandiere = list(flag)
        amb = dict(os.environ)
        self.chrome = subprocess.Popen(flag, env=amb,
                                       stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL)
        cdp = cdp_modulo()
        b = cdp.pagina(PORTA_CDP, attesa=40)
        self.c = cdp.Cdp(b["webSocketDebuggerUrl"], timeout=180)
        for m in ("Page.enable", "Runtime.enable"):
            self.c.chiama(m)
        return b

    def valuta(self, e, attendi=False):
        return self.c.valuta(e, attendi=attendi)

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
# §5  IL GIRO
# ═══════════════════════════════════════════════════════════════════════════
def casi_della_matrice(flussi):
    """Le quattro caselle per codec e per misura, con l'ATTESO scritto qui e
    non dopo aver visto i numeri."""
    casi = []
    misure = sorted({(f["l"], f["a"]) for f in flussi.values()})
    for (l, a) in misure:
        for codec in ("hevc", "av1"):
            for p_config in (8, 10):
                for p_flusso in (8, 10):
                    nome_f = "%s-%d-%dx%d" % (codec, p_flusso, l, a)
                    if nome_f not in flussi:
                        continue
                    casi.append({
                        "caso": "%s · config %d bit · flusso %d bit · %dx%d"
                                % (codec, p_config, p_flusso, l, a),
                        "codec": codec, "p_config": p_config,
                        "p_flusso": p_flusso, "l": l, "a": a,
                        "stringa": STRINGHE[codec][p_config],
                        "flusso": nome_f,
                        # ⛔ L'atteso: le diagonali sono i CONTROLLI POSITIVI,
                        #    le altre due sono l'incognita.  Un banco che non
                        #    dichiara l'atteso prima non puo' essere smentito.
                        "ruolo": ("controllo+" if p_config == p_flusso
                                  else "incognita"),
                    })
    return casi


def gira_matrice(flussi, palco, verbale):
    cartella = tempfile.mkdtemp(prefix="04-b21-web-")
    casi = casi_della_matrice(flussi)
    # ⛔ I byte non passano dal CDP: una `evaluate` con dentro 3 MB di base64
    #    e' un modo di perdere il giro.  Vanno nella pagina, servita da qui.
    magri = {n: {k: v for k, v in f.items() if k != "guai_rilettura"}
             for n, f in flussi.items()}
    pagina = (PAGINA.replace("__CASI__", json.dumps(casi))
                    .replace("__FLUSSI__", json.dumps(magri)))
    with open(os.path.join(cartella, "matrice.html"), "w") as f:
        f.write(pagina)
    s = servi(cartella, PORTA_HTTP)
    try:
        palco.accendi("http://127.0.0.1:%d/matrice.html" % PORTA_HTTP)
        fine = time.time() + 180
        fuori = None
        while time.time() < fine:
            r = palco.valuta("document.body.dataset.b21 === 'fatto' ? "
                             "JSON.stringify(window.B21) : ''")
            if r:
                fuori = json.loads(r)
                break
            time.sleep(0.5)
        if fuori is None:
            # ⛔ «non ho potuto guardare» non e' «zero caselle dipingono».
            return None, "la pagina non ha finito entro 180 s"
        verbale["palco"] = fuori.get("palco")
        verbale["bandiere"] = palco.bandiere
        return fuori, None
    finally:
        s.shutdown()
        s.server_close()
        shutil.rmtree(cartella, ignore_errors=True)


def stampa(fuori, flussi):
    tit("i flussi, e il profilo letto NEI BYTE (secondo testimone)")
    for n, f in sorted(flussi.items()):
        riga = ("%-22s %7d byte · profilo «%s» · pix %s"
                % (n, f["byte"], f["profilo_nei_byte"], f["pix_fmt_nei_byte"]))
        if f["guai_profilo"]:
            dub(riga + " — " + str(f["guai_profilo"])[:80])
        elif f["riletto"] is None:
            dub(riga + " — non si e' potuto ridecodificare")
        else:
            sx, dx = f["riletto"]
            d = sum((x - y) ** 2 for x, y in zip(sx, dx)) ** 0.5
            inf(riga + " · tinte %s / %s · distanza %.0f" % (sx, dx, d))

    tit("la matrice — quattro caselle, e due sono controlli positivi")
    segni = {"si": "\033[1;32mdipinge\033[0m",
             "no": "\033[1;31mNON dipinge\033[0m",
             "cieco": "\033[1;33mnon ho potuto guardare\033[0m"}
    for c in fuori["casi"]:
        print("    %-13s %-46s %s  %s"
              % ("[" + c["ruolo"] + "]", c["caso"], segni.get(c["stato"], "?"),
                 ("· " + str(c.get("perche"))[:90]) if c.get("perche") else
                 ("· formato %s, misura %s" % (c.get("formato"),
                                               c.get("misura")))))


def giudica(fuori):
    """⛔ Il verdetto, con la regola scritta prima: se un CONTROLLO POSITIVO non
    dipinge, sull'incognita non si scrive niente."""
    ctrl = [c for c in fuori["casi"] if c["ruolo"] == "controllo+"]
    inc = [c for c in fuori["casi"] if c["ruolo"] == "incognita"]
    ciechi = [c for c in fuori["casi"] if c["stato"] == "cieco"]
    ctrl_rossi = [c for c in ctrl if c["stato"] != "si"]
    return {
        "controlli": len(ctrl), "controlli_rossi": len(ctrl_rossi),
        "incognite": len(inc),
        "incognite_che_dipingono": len([c for c in inc if c["stato"] == "si"]),
        "ciechi": len(ciechi),
        "verdetto_scrivibile": len(ctrl_rossi) == 0,
    }


def principale():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrice", action="store_true")
    ap.add_argument("--certifica", action="store_true")
    ap.add_argument("--misure", default="64x48,1920x1080")
    ap.add_argument("--json", default="")
    ap.add_argument("--senza-gpu", action="store_true")
    a = ap.parse_args()

    if a.certifica:
        return certifica(a)

    misure = []
    for m in a.misure.split(","):
        l, h = m.lower().split("x")
        misure.append((int(l), int(h)))

    tit("04-b21 · la matrice profilo × flusso — %s" % time.strftime("%F %T"))
    inf("⚠ il palco e' il DESKTOP VERO dell'utente, dichiarato e non spostato "
        "(README.md:397)")
    flussi = costruisci_flussi(misure, os.environ.get("GUASTO", ""))
    verbale = {"quando": time.strftime("%F %T"), "misure": a.misure,
               "guasto": os.environ.get("GUASTO", "")}
    palco = Palco(gpu=not a.senza_gpu)
    try:
        fuori, guaio = gira_matrice(flussi, palco, verbale)
    finally:
        palco.spegni()
    if fuori is None:
        ko("⛔ " + guaio)
        return 2
    stampa(fuori, flussi)
    g = giudica(fuori)
    verbale["giudizio"] = g
    verbale["casi"] = fuori["casi"]
    verbale["flussi"] = {n: {k: v for k, v in f.items() if k != "dati"}
                         for n, f in flussi.items()}

    tit("il palco, letto DALLA PAGINA (l'altro capo)")
    for k, v in (fuori.get("palco") or {}).items():
        inf("%-20s %s" % (k, v))

    tit("il verdetto")
    if g["ciechi"]:
        dub("%d caselle «non ho potuto guardare»: non sono rossi, sono buchi "
            "nella misura" % g["ciechi"])
    if not g["verdetto_scrivibile"]:
        ko("⛔ %d controlli positivi su %d NON dipingono ⇒ sull'incognita non "
           "si scrive niente: sarebbe indistinguibile fra «il prodotto ha il "
           "difetto» e «il banco non sa dipingere»"
           % (g["controlli_rossi"], g["controlli"]))
        esito = 2
    else:
        ok("i %d controlli positivi dipingono tutti ⇒ il verdetto "
           "sull'incognita si puo' scrivere" % g["controlli"])
        esito = 0 if g["incognite_che_dipingono"] == g["incognite"] else 1
        if esito:
            ko("⛔ %d incognite su %d NON dipingono"
               % (g["incognite"] - g["incognite_che_dipingono"], g["incognite"]))
        else:
            ok("tutte le incognite dipingono")
    if a.json:
        with open(a.json, "w") as f:
            json.dump(verbale, f, indent=1)
        inf("verbale depositato in " + a.json)
    return esito


def certifica(a):
    """⛔ sano → guasto → risanato, con l'atteso scritto PRIMA."""
    tit("la certificazione di 04-b21 — sano → guasto → risanato")
    inf("atteso, scritto PRIMA di girare:")
    inf("  sano/risanato  i controlli positivi DIPINGONO (verdetto scrivibile)")
    inf("  una-tinta      NESSUNA casella dipinge — la prova dei pixel vuole")
    inf("                 due letture giuste E DIVERSE, e una tinta non le da'")
    inf("  vuoto          NESSUNA casella dipinge, e nessuna e' «cieca»: un")
    inf("                 flusso vuoto e' un fallimento CHE SI NOMINA")
    esiti = []
    # ⛔ La certificazione gira alla misura piccola: e' la stessa prova, e a
    #    1920×1080 costerebbe quattro costruzioni di libx265 per giro senza
    #    aggiungere una proprieta'.
    misure = [(64, 48)]
    for giro, guasto in (("sano", ""), ("guasto una-tinta", "una-tinta"),
                         ("guasto vuoto", "vuoto"), ("risanato", "")):
        tit("giro «%s»" % giro)
        flussi = costruisci_flussi(misure, guasto)
        palco = Palco(gpu=not a.senza_gpu)
        verbale = {}
        try:
            fuori, guaio = gira_matrice(flussi, palco, verbale)
        finally:
            palco.spegni()
        if fuori is None:
            ko("⛔ " + guaio)
            esiti.append(False)
            continue
        g = giudica(fuori)
        dipingono = len([c for c in fuori["casi"] if c["stato"] == "si"])
        inf("caselle che dipingono: %d su %d · cieche %d"
            % (dipingono, len(fuori["casi"]), g["ciechi"]))
        for c in fuori["casi"]:
            inf("   %-46s %-6s %s" % (c["caso"], c["stato"],
                                      str(c.get("perche") or "")[:70]))
        if guasto == "":
            atteso = g["verdetto_scrivibile"]
            frase = "i controlli positivi dipingono"
        elif guasto == "una-tinta":
            atteso = dipingono == 0
            frase = "nessuna casella dipinge (0 su %d)" % len(fuori["casi"])
        else:
            atteso = dipingono == 0 and g["ciechi"] == 0
            frase = ("nessuna dipinge E nessuna e' cieca (dipinte %d, cieche %d)"
                     % (dipingono, g["ciechi"]))
        esiti.append(atteso)
        (ok if atteso else ko)("giro «%s»: %s" % (giro, frase))
    tit("esito della certificazione")
    if all(esiti):
        ok("PROMOSSO %d giri su %d" % (len(esiti), len(esiti)))
        return 0
    ko("BOCCIATO: %d giri su %d" % (sum(1 for e in esiti if e), len(esiti)))
    return 1


if __name__ == "__main__":
    sys.exit(principale())
