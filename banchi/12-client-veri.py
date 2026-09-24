#!/usr/bin/env python3
"""12-client-veri — LA PROVA CLIENT REALE, su tre browser, con un verdetto per ciascuno.

    python3 banchi/12-client-veri.py --url https://192.168.0.2:8511/ \\
        --utente prova --parola '…' [--browser firefox,chrome,android] \\
        [--visibile] [--tetto-s 30] [--scena muovi|viva|ferma] \\
        [--registro-cmd "ssh … tail -n 3000 …/registro.log"] [--certifica]

⭐ CHE COSA FA.  Apre REMOTIX in un browser VERO — Firefox 140 ESR guidato con
   Marionette (`07-b46-marionette.py`), Google Chrome guidato col protocollo
   DevTools, e Chrome per Android nell'emulatore `remotix`, guidato con lo
   stesso protocollo attraverso `adb forward` — e per ciascuno guarda sette cose:

     a  la pagina si apre (certificato accettato) e il modulo d'accesso c'e'
     b  con `--utente`/`--parola` la pagina viene AMMESSA
     c  PRIMO FOTOGRAMMA: la tela ha pixel NON degeneri entro `--tetto-s`
     d  CONTINUITA': i fotogrammi continuano ad arrivare (vedi «la scena»)
     e  INPUT: un tasto e un movimento+clic (un tocco su Android) arrivano al server
     f  errori JavaScript della pagina ed errori di rete (e quel che la pagina
        stessa dichiara con «⛔» nel suo registro)
     g  RICONNESSIONE: si ricarica, si rientra, e c'e' di nuovo il primo fotogramma

   Ogni punto ha un esito: 0 verde · 1 rosso · 3 «non ho potuto guardare», col
   motivo.  ⛔ MAI UN VERDE REGALATO: se lo strumento non ha potuto guardare, e' 3.
   Il verdetto del browser e' PASS (tutto 0) · FAIL (almeno un 1) · BLOCKED
   (nessun 1, ma almeno un 3).  In fondo a ogni browser, una riga JSON.

⛔ DA DOVE SI LEGGE LO STATO — e si legge dalla PAGINA, non dall'impaginazione
   (`src/pagina.html`, i numeri di riga sono del 18 settembre 2026):
     · ammessa: `REMOTIX.schermo.sessione === true` (la mette `negozia()`,
       riga ~2816, e il ramo del worker riga ~8234) E `#esito` con classe
       `bene` e testo «Ammesso, sessione …» (riga ~5058).  Il rifiuto e' `#esito`
       con classe `male` (riga 622 e i rami di `collega()`).
     · primo fotogramma e continuita': `REMOTIX.schermo.conti.dipinti` (riga
       ~2689, cresce alle righe ~3186/3675/4099) — il metro della fase, che la
       pagina stessa legge nella veglia del primo fotogramma.
     · i pixel: una FOTOGRAFIA della tela presa dal browser (CDP
       `Page.captureScreenshot`, Marionette `TakeScreenshot` con `id`).  ⚠ Non
       `getImageData`: la tela puo' essere `bitmaprenderer` o passata a un
       worker (`transferControlToOffscreen`, riga ~8145), e li' la lettura dal
       documento non vede niente.  La fotografia vede quel che vede l'utente.
     · input: il banco AVVOLGE `window.REMOTIX_INPUT.manda` (riga ~5130) e
       conta per tipo quel che la pagina ha davvero spedito (l'`id` e' nei
       primi 4 byte del corpo, §7.3).  ⭐ E l'arrivo al server si prova in due
       modi indipendenti: le righe «input id=… PUNTATORE/PULSANTE/
       POSIZIONE_TASTO» nel registro del server (`src/rcp.c` ~4726), se c'e'
       `--registro-cmd`; e dalla pagina, con `REMOTIX.giro` (riga ~2197): un
       fotogramma che riporta indietro l'`id` N dimostra che il server ha
       applicato tutti gli input fino a N (lo stream di input e' uno solo e
       ordinato, §2.5).  ⚠ Un fotogramma arriva solo se lo schermo CAMBIA:
       senza registro e senza ritorno, l'esito e' 3, non 1.
     · il registro della pagina: il testo di `#registro` (righe `nota()`, riga
       473) — da li' si prendono le righe «⛔».

⚠ LA SCENA SI DICHIARA (`--scena`).  Un desktop fermo NON manda fotogrammi, e
  zero fotogrammi su un desktop fermo e' la cosa giusta:
     · `ferma`  nessun fotogramma nuovo ⇒ 3 (non si puo' distinguere)
     · `viva`   chi lancia GARANTISCE che qualcosa si muove ⇒ zero fotogrammi e' 1
     · `muovi`  (predefinita) il banco muove il puntatore sopra la tela per
                `--continuita-s` secondi, attraversando tutto il desktop ⇒ zero
                fotogrammi e' 1.  ⚠ Il cursore lo disegna la pagina, non il
                server: il fotogramma nasce solo se il desktop reagisce al
                passaggio (evidenziazioni, barra, dock).  Su un desktop che non
                reagisce, usa `viva` con una scena accesa.

⚠ HEADLESS SI DICHIARA.  Senza `--visibile` Firefox e Chrome girano headless,
  cioe' senza GPU: la decodifica e il disegno sono in SOFTWARE.  L'emulatore
  Android usa `swiftshader_indirect`, cioe' anche lui software.  La riga
  d'esito lo porta scritto: questo banco giudica il COMPORTAMENTO, non i numeri.

⛔ LA CERTIFICAZIONE (`PIANO.md` §0.3 regola 4) — `--certifica` dimostra che il
   banco sa dare rosso, prima di credergli il verde:
     1. una porta dove non c'e' nessun server ⇒ (a) DEVE essere rosso;
     2. la parola d'ordine SBAGLIATA contro `--url` ⇒ (b) DEVE essere rosso PER
        RIFIUTO (la pagina ha mandato le credenziali e il server non l'ha
        ammessa), non per un collegamento mancato: senza server che risponda
        la seconda prova e' «non certificato» (3), non verde.
        ⚠ Consuma UN tentativo d'accesso sul server: vale per il ban.
     3. il giudice dei pixel si prova su due immagini fatte qui: una tela tutta
        nera DEVE essere degenere, una sfumatura NO.

⚠ Le porte: Marionette 2851, DevTools di Chrome 9341, DevTools di Android 9342
  (in locale, via `adb forward`).  Si cambiano con `--porte-base`.
"""
import argparse
import base64
import importlib.util as _iu
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request

QUI = os.path.dirname(os.path.abspath(__file__))
CASA = os.path.expanduser("~")
ADB = os.path.join(CASA, "Android/Sdk/platform-tools/adb")
EMU = os.path.join(CASA, "Android/Sdk/emulator/emulator")
# ⛔ 19 set 2026 — NON il Chrome dell'immagine di sistema (113): WebCodecs su
#    Chrome per Android c'e' dalla 147 (`DECISIONI.md` riga ~425), e `[M]` il
#    113 cade gia' a WebTransport (`ERR_METHOD_NOT_SUPPORTED`).  ⇒ Chromium per
#    Android dall'archivio ufficiale delle build di Chromium (AndroidDesktop_x64,
#    `ChromePublic.apk`, 156.0.8067.0, in `~/Android/chromium/`), dichiarato
#    come Chromium.  ⛔ Firefox per Android e' NON supportato (§7.18).
#    ⚠ E Chromium NON va: `[M]` le build pubbliche non hanno H.264
#    (`isConfigSupported` no a `avc1.*`) ⇒ la pagina non ha nessun codec.
#    ⇒ Si usa il Chrome VERO dell'immagine Android 17 (`remotix37`, Chrome
#    145.0.7632.218).  Tutt'e due si cambiano senza toccare il file:
#    `REMOTIX_ANDROID_PACCHETTO`, `REMOTIX_AVD`.
CHROME_ANDROID = os.environ.get("REMOTIX_ANDROID_PACCHETTO", "com.android.chrome")
AVD = os.environ.get("REMOTIX_AVD", "remotix37")


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, os.path.join(QUI, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


MARIONETTE = _carica("marionette", "07-b46-marionette.py")
CDPMOD = _carica("cdp", "02-pagina-misura-cdp.py")

VERDE, ROSSO, CIECO = 0, 1, 3
NOMI_PUNTI = {
    "a": "la pagina si apre e il modulo c'e'",
    "b": "ammessa con utente e parola",
    "c": "primo fotogramma, pixel non degeneri",
    "d": "continuita' dei fotogrammi",
    "e": "input: tasto e mouse/tocco arrivano al server",
    "f": "errori JavaScript e di rete",
    "g": "riconnessione: ricarica, rientra, primo fotogramma",
}
TIPI_INPUT = {0x0101: "PUNTATORE", 0x0102: "PULSANTE", 0x0103: "ROTELLA",
              0x0104: "LETTERA", 0x0105: "POSIZIONE_TASTO"}


# ═══════════════════════════════════════════════════════════════════════════
#  IL GIUDICE DEI PIXEL
# ═══════════════════════════════════════════════════════════════════════════
def giudica_pixel(png):
    """Torna (degenere: bool|None, descrizione).  None = non ho potuto guardare.

    ⛔ Degenere vuol dire: un colore solo (o quasi) su tutta la tela — nero,
       magenta di attesa, grigio.  Un desktop vero ha almeno una barra, del
       testo, un'icona: si chiede che il colore dominante copra meno del 97 %
       e che la luminanza abbia una deviazione di almeno 3 livelli."""
    try:
        from PIL import Image
    except ImportError:
        return None, "PIL non c'e': non posso leggere la fotografia"
    try:
        im = Image.open(io.BytesIO(png)).convert("RGB")
    except Exception as e:                       # noqa: BLE001
        return None, "fotografia illeggibile: %s" % e
    l, a = im.size
    if l < 8 or a < 8:
        return True, "fotografia di %dx%d: la tela non ha misura" % (l, a)
    pic = im.resize((min(160, l), min(120, a)))
    px = list(pic.getdata())
    n = len(px)
    conta = {}
    for p in px:
        q = (p[0] >> 3, p[1] >> 3, p[2] >> 3)
        conta[q] = conta.get(q, 0) + 1
    dom_q, dom_n = max(conta.items(), key=lambda kv: kv[1])
    lum = [0.299 * r + 0.587 * g + 0.114 * b for r, g, b in px]
    media = sum(lum) / n
    dev = (sum((x - media) ** 2 for x in lum) / n) ** 0.5
    quota = dom_n / n
    desc = ("%dx%d · colori distinti %d · dominante %.1f%% (%d,%d,%d) · "
            "luminanza media %.0f dev %.1f"
            % (l, a, len(conta), 100 * quota, dom_q[0] << 3, dom_q[1] << 3,
               dom_q[2] << 3, media, dev))
    return (quota >= 0.97 or dev < 3.0), desc


def certifica_giudice():
    """Il giudice dei pixel deve saper dire «degenere»."""
    try:
        from PIL import Image
    except ImportError:
        return CIECO, "PIL non c'e'"
    def png(im):
        b = io.BytesIO(); im.save(b, "PNG"); return b.getvalue()
    nero = Image.new("RGB", (640, 400), (0, 0, 0))
    sfum = Image.new("RGB", (640, 400))
    sfum.putdata([(x % 256, (y * 2) % 256, (x + y) % 256)
                  for y in range(400) for x in range(640)])
    d1, t1 = giudica_pixel(png(nero))
    d2, t2 = giudica_pixel(png(sfum))
    ok = d1 is True and d2 is False
    return (VERDE if ok else ROSSO,
            "tela nera ⇒ %s (%s) · sfumatura ⇒ %s (%s)"
            % ("degenere" if d1 else "⛔ NON degenere", t1,
               "non degenere" if d2 is False else "⛔ degenere", t2))


# ═══════════════════════════════════════════════════════════════════════════
#  I PEZZI DI JAVASCRIPT — corpi di funzione, con `return`
# ═══════════════════════════════════════════════════════════════════════════
JS_MODULO = r"""
const m = document.getElementById('modulo');
const vis = (e) => !!e && getComputedStyle(e).display !== 'none'
                   && getComputedStyle(e).visibility !== 'hidden'
                   && e.getBoundingClientRect().width > 0;
return { url: location.href, titolo: document.title,
         pronta: document.readyState,
         modulo: !!m, visibile: vis(m),
         utente: !!document.getElementById('utente'),
         parola: !!document.getElementById('parola'),
         vai: !!document.getElementById('vai'),
         remotix: !!window.REMOTIX,
         bannato: document.body ? document.body.dataset.bannato || null : null,
         avviso: (document.getElementById('avviso') || {}).textContent || '',
         testo: document.body ? document.body.innerText.slice(0, 300) : '' };
"""

# ⚠ Il valore si mette nel campo e si chiede `requestSubmit()` sul modulo: e'
#   lo stesso gestore di `submit` che fa partire la pagina quando l'utente
#   preme «Collegati» (pagina.html ~8445).  Non si scrive a coordinate.
JS_ENTRA = r"""
const u = document.getElementById('utente'), p = document.getElementById('parola');
const m = document.getElementById('modulo');
if (!u || !p || !m) return 'manca il modulo';
u.value = arguments[0]; p.value = arguments[1];
u.dispatchEvent(new Event('input', {bubbles: true}));
p.dispatchEvent(new Event('input', {bubbles: true}));
if (m.requestSubmit) m.requestSubmit(document.getElementById('vai'));
else document.getElementById('vai').click();
return 'mandato';
"""

JS_STATO = r"""
const R = window.REMOTIX, s = R && R.schermo;
const e = document.getElementById('esito');
const reg = document.getElementById('registro');
let g = null;
try { if (R && R.giro) g = { visti: R.giro.visti, attesa: R.giro.quando.size }; } catch (x) {}
const t = document.getElementById('schermo');
const r = t ? t.getBoundingClientRect() : null;
return {
  sessione: !!(s && s.sessione),
  esito_classe: e ? e.className : null,
  esito: e ? e.textContent : null,
  dipinti: s && s.conti ? s.conti.dipinti : null,
  consegnati: s && s.conti ? s.conti.consegnati : null,
  acceso: document.body ? (document.body.dataset.schermo || null) : null,
  input: !!window.REMOTIX_INPUT,
  giro: g,
  tela: r ? [r.left, r.top, r.width, r.height] : null,
  buffer: t ? [t.width, t.height] : null,
  vista: [innerWidth, innerHeight, devicePixelRatio || 1],
  registro: reg ? reg.textContent : '',
  errori_schermo: s && s.errori ? s.errori.slice(-5).map(String) : [],
  banco: window.__BANCO__ ? { errori: window.__BANCO__.errori.slice(0, 40),
                              rete: window.__BANCO__.rete.slice(0, 40) } : null,
  ingresso: window.__BANCO_IN__ ? window.__BANCO_IN__ : null,
};
"""

# ⭐ Il raccoglitore degli errori.  In Chrome entra PRIMA della pagina
#   (`Page.addScriptToEvaluateOnNewDocument`); in Firefox entra dopo il carico
#   e lo si dichiara — gli errori di prima li prende l'uscita del browser
#   (`devtools.console.stdout.content`).
RACCOGLITORE = r"""
(function () {
  if (window.__BANCO__) return;
  const B = window.__BANCO__ = { errori: [], rete: [] };
  const metti = (a, t) => { if (a.length < 200) a.push(String(t).slice(0, 400)); };
  addEventListener('error', (ev) => {
    if (ev.target && ev.target !== window && (ev.target.src || ev.target.href))
      metti(B.rete, 'risorsa non caricata: ' + (ev.target.src || ev.target.href));
    else metti(B.errori, 'eccezione: ' + ev.message + ' @' + (ev.filename || '')
                         + ':' + (ev.lineno || ''));
  }, true);
  addEventListener('unhandledrejection', (ev) => {
    const r = ev.reason;
    metti(B.errori, 'promessa rifiutata: ' + (r && r.stack ? r.stack.split('\n')[0] : r));
  });
  const ce = console.error.bind(console);
  console.error = function () {
    try { metti(B.errori, 'console.error: ' + Array.from(arguments).join(' ')); } catch (x) {}
    return ce.apply(null, arguments);
  };
})();
"""

# ⭐ L'anello dell'input.  Avvolge `manda` della cucitura (riga ~5130): conta
#   per tipo quel che la pagina ha SPEDITO, con l'`id` preso dai primi 4 byte
#   del corpo (§7.3, big-endian).  ⚠ Non cambia niente di quel che la pagina
#   manda: chiama la `manda` vera con gli stessi argomenti.
JS_ANELLO = r"""
(function () {
  const c = window.REMOTIX_INPUT;
  if (!c || typeof c.manda !== 'function' || c.__banco) return;
  const vero = c.manda;
  const B = window.__BANCO_IN__ = window.__BANCO_IN__ || { tipi: {}, ids: {} };
  c.manda = function (tipo, corpo) {
    try {
      const id = new DataView(corpo.buffer, corpo.byteOffset, 4).getUint32(0);
      B.tipi[tipo] = (B.tipi[tipo] || 0) + 1;
      (B.ids[tipo] = B.ids[tipo] || []).push(id);
      if (B.ids[tipo].length > 400) B.ids[tipo].shift();
    } catch (x) {}
    return vero.apply(this, arguments);
  };
  c.__banco = true;
})();
"""

# ⭐ Quali `id` sono tornati indietro in un fotogramma: quelli spediti che
#   `GIRO.quando` non ha piu' (`torna()` li cancella, riga ~2211).
JS_TORNATI = r"""
const B = window.__BANCO_IN__, R = window.REMOTIX;
if (!B || !R || !R.giro) return null;
let max_tornato = 0;
const per_tipo = {};
for (const t in B.ids) {
  per_tipo[t] = B.ids[t].slice();
  for (const id of B.ids[t]) if (!R.giro.quando.has(id) && id > max_tornato) max_tornato = id;
}
return { max_tornato: max_tornato, ids: per_tipo, tipi: B.tipi, visti: R.giro.visti };
"""


def _inietta(corpo):
    """Un corpo da eseguire nella pagina VERA, non nella sandbox del driver:
    in Firefox una funzione nata nella sandbox di Marionette e chiamata dalla
    pagina passa per le «xray» e puo' non funzionare.  ⇒ `<script>` nel DOM."""
    return ("const s = document.createElement('script');"
            "s.textContent = %s;"
            "(document.head || document.documentElement).appendChild(s); s.remove();"
            "return true;" % json.dumps(corpo))


# ═══════════════════════════════════════════════════════════════════════════
#  I GUIDATORI — uno per browser, la stessa faccia
# ═══════════════════════════════════════════════════════════════════════════
class Cdp(CDPMOD.Cdp):
    """Il cliente CDP di `02-pagina-misura-cdp.py`, che pero' TIENE gli eventi:
    le eccezioni e i messaggi della console arrivano come eventi mentre si
    aspetta la risposta a un comando, e lui li buttava."""

    def __init__(self, url, timeout=60):
        super().__init__(url, timeout)
        self.eventi = []

    def chiama(self, metodo, **parametri):
        self.n += 1
        mio = self.n
        self.ws.manda(json.dumps({"id": mio, "method": metodo, "params": parametri}))
        while True:
            r = json.loads(self.ws.ricevi())
            if "method" in r and "id" not in r:
                if len(self.eventi) < 5000:
                    self.eventi.append(r)
                continue
            if r.get("id") != mio:
                continue
            if "error" in r:
                raise RuntimeError(metodo + ": " + json.dumps(r["error"]))
            return r.get("result", {})


class GuidaCdp:
    """Chrome da tavolo e Chrome per Android: stesso protocollo."""
    tocco = False

    def __init__(self, porta, nome):
        self.porta, self.nome = porta, nome
        self.cdp = None

    def aggancia(self, attesa=40):
        b = CDPMOD.pagina(self.porta, attesa)
        self.cdp = Cdp(b["webSocketDebuggerUrl"])
        for d in ("Page.enable", "Runtime.enable", "Log.enable", "Network.enable"):
            try:
                self.cdp.chiama(d)
            except Exception:                    # noqa: BLE001
                pass
        self.cdp.chiama("Page.addScriptToEvaluateOnNewDocument", source=RACCOGLITORE)
        try:
            self.cdp.chiama("Emulation.setFocusEmulationEnabled", enabled=True)
        except Exception:                        # noqa: BLE001
            pass

    def versione(self):
        try:
            with urllib.request.urlopen("http://127.0.0.1:%d/json/version" % self.porta,
                                        timeout=5) as r:
                return json.loads(r.read().decode()).get("Browser", "?")
        except Exception as e:                   # noqa: BLE001
            return "? (%s)" % e

    def js(self, corpo, *arg):
        espr = "(function(){%s}).apply(null, %s)" % (corpo, json.dumps(list(arg)))
        r = self.cdp.chiama("Runtime.evaluate", expression=espr,
                            returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise RuntimeError("eccezione nel banco: %s"
                               % json.dumps(r["exceptionDetails"])[:300])
        return r.get("result", {}).get("value")

    def vai(self, url):
        """Torna (aperta, motivo).  ⭐ Il certificato si accetta come lo accetta
        l'utente: il pannello «Avanzate» → «Procedi».  Nessuna bandiera che
        spenga i controlli: con `--ignore-certificate-errors` anche il
        WebTransport smetterebbe di guardare l'impronta, e il banco proverebbe
        un browser che l'utente non ha."""
        r = self.cdp.chiama("Page.navigate", url=url)
        err = r.get("errorText")
        time.sleep(1.5)
        for _ in range(3):
            try:
                pannello = self.js(
                    "return !!document.getElementById('proceed-link')"
                    " || !!document.getElementById('details-button');")
            except Exception:                    # noqa: BLE001
                pannello = False
            if not pannello:
                break
            self.js("const d=document.getElementById('details-button'); if (d) d.click();"
                    "const p=document.getElementById('proceed-link'); if (p) p.click();"
                    "return 1;")
            time.sleep(3)
        if err and "CERT" not in err:
            return False, err
        return True, err or ""

    def ricarica(self):
        self.cdp.chiama("Page.reload", ignoreCache=False)
        time.sleep(1.5)

    def fotografa_tela(self):
        r = self.js("const t=document.getElementById('schermo');"
                    "if(!t) return null; const b=t.getBoundingClientRect();"
                    "const x=Math.max(0,b.left), y=Math.max(0,b.top);"
                    "return [x, y, Math.min(innerWidth,b.right)-x,"
                    " Math.min(innerHeight,b.bottom)-y];")
        if not r or r[2] < 4 or r[3] < 4:
            return None, "la tela non ha area visibile: %s" % (r,)
        scala = min(1.0, 640.0 / r[2])
        s = self.cdp.chiama("Page.captureScreenshot", format="png",
                            clip={"x": r[0], "y": r[1], "width": r[2],
                                  "height": r[3], "scale": scala})
        return base64.b64decode(s["data"]), ""

    # -- l'input: eventi del protocollo, cioe' eventi FIDATI nel renderer ----
    def muovi(self, x, y):
        self.cdp.chiama("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)

    def clic(self, x, y):
        self.muovi(x, y)
        for t in ("mousePressed", "mouseReleased"):
            self.cdp.chiama("Input.dispatchMouseEvent", type=t, x=x, y=y,
                            button="left", clickCount=1)

    def tocca(self, x, y):
        self.cdp.chiama("Input.dispatchTouchEvent", type="touchStart",
                        touchPoints=[{"x": x, "y": y}])
        time.sleep(0.08)
        self.cdp.chiama("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])

    def trascina(self, punti):
        self.cdp.chiama("Input.dispatchTouchEvent", type="touchStart",
                        touchPoints=[{"x": punti[0][0], "y": punti[0][1]}])
        for x, y in punti[1:]:
            time.sleep(0.05)
            self.cdp.chiama("Input.dispatchTouchEvent", type="touchMove",
                            touchPoints=[{"x": x, "y": y}])
        self.cdp.chiama("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])

    def tasto(self, t):
        k = TASTI[t]
        mod = 2 if t == "Control" else 0
        self.cdp.chiama("Input.dispatchKeyEvent", type="rawKeyDown", key=k["key"],
                        code=k["code"], windowsVirtualKeyCode=k["vk"], modifiers=mod)
        time.sleep(0.08)
        self.cdp.chiama("Input.dispatchKeyEvent", type="keyUp", key=k["key"],
                        code=k["code"], windowsVirtualKeyCode=k["vk"])

    def errori_fuori(self):
        """Gli errori visti dal PROTOCOLLO, indipendenti dalla pagina."""
        try:
            self.cdp.chiama("Runtime.evaluate", expression="1")   # svuota la coda
        except Exception:                        # noqa: BLE001
            pass
        js, rete = [], []
        for e in self.cdp.eventi:
            m, p = e.get("method"), e.get("params", {})
            if m == "Runtime.exceptionThrown":
                d = p.get("exceptionDetails", {})
                ex = d.get("exception", {})
                js.append("eccezione: %s" % (ex.get("description") or d.get("text"))
                          .split("\n")[0][:300])
            elif m == "Runtime.consoleAPICalled" and p.get("type") == "error":
                js.append("console.error: " + " ".join(
                    str(a.get("value", a.get("description", ""))) for a in p.get("args", []))[:300])
            elif m == "Log.entryAdded":
                en = p.get("entry", {})
                if en.get("level") == "error":
                    # ⚠ la favicon non c'e' e non e' un difetto: si scarta per nome
                    if (en.get("url") or "").endswith("/favicon.ico"):
                        continue
                    (rete if en.get("source") == "network" else js).append(
                        "%s: %s%s" % (en.get("source"), en.get("text", "")[:300],
                                      " [%s]" % en["url"] if en.get("url") else ""))
            elif m == "Network.loadingFailed":
                # ⚠ l'errore di certificato del documento e' quello che il banco
                #   accetta apposta dal pannello «Procedi»: non e' un difetto
                if p.get("canceled") or (p.get("type") == "Document"
                                         and "ERR_CERT_" in (p.get("errorText") or "")):
                    continue
                rete.append("rete: %s (%s)" % (p.get("errorText"), p.get("type")))
        return js, rete, ""

    def azzera_eventi(self):
        self.cdp.eventi = []


TASTI = {
    "Control": {"key": "Control", "code": "ControlLeft", "vk": 17, "wd": ""},
    "ArrowRight": {"key": "ArrowRight", "code": "ArrowRight", "vk": 39, "wd": ""},
}


# ⭐ La misura della finestra dei due browser, «LxA».  ⚠ Si cambia con
#   `--finestra`: `[M]` 24 set 2026, la striscia verde di Firefox dipende dalla
#   LARGHEZZA (8 px a 1400, 12 a 1348), e un banco a finestra fissa ne vede una.
FINESTRA = [1400, 1000]


class GuidaChrome(GuidaCdp):
    def __init__(self, porta, visibile):
        super().__init__(porta, "chrome")
        self.visibile = visibile
        self.profilo = tempfile.mkdtemp(prefix="remotix-cr-")
        cmd = ["google-chrome", "--remote-debugging-port=%d" % porta,
               "--user-data-dir=" + self.profilo, "--no-first-run",
               "--no-default-browser-check", "--disable-sync",
               "--password-store=basic", "--window-size=%d,%d" % tuple(FINESTRA),
               "--remote-allow-origins=*"]
        if not visibile:
            cmd.append("--headless=new")
        # ⚠ Opzioni in piu' dichiarate da chi lancia: `[M]` 24 set 2026, sul
        #   server dentro un labwc senza schermo Chrome cercava X11 e non
        #   partiva ⇒ `REMOTIX_CHROME_OPZIONI="--ozone-platform=wayland"`.
        cmd += os.environ.get("REMOTIX_CHROME_OPZIONI", "").split()
        cmd.append("about:blank")
        self.log = open(os.path.join(self.profilo, "uscita.log"), "wb")
        self.p = subprocess.Popen(cmd, stdout=self.log, stderr=subprocess.STDOUT)
        self.aggancia()

    def palco(self):
        return "%s · %s" % (self.versione(), "finestra vera" if self.visibile
                            else "HEADLESS — senza GPU, tutto in software")

    def chiudi(self):
        try:
            self.cdp.chiama("Page.navigate", url="about:blank")   # pagehide ⇒ CONGEDO
            time.sleep(1)
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.cdp.chiama("Browser.close")
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.p.wait(10)
        except Exception:                        # noqa: BLE001
            self.p.kill()
        shutil.rmtree(self.profilo, ignore_errors=True)


def adb(*v, t=60):
    try:
        return subprocess.run([ADB] + list(v), capture_output=True, text=True,
                              timeout=t).stdout or ""
    except Exception as e:                       # noqa: BLE001
        return "⛔ %s" % e


class GuidaAndroid(GuidaCdp):
    """Chrome nell'emulatore `remotix`.  ⛔ L'emulatore mangia RAM: lo accende
    il banco se non c'e', e lo spegne il banco se l'ha acceso lui."""
    tocco = True

    def __init__(self, porta, lascia_acceso):
        super().__init__(porta, "android")
        self.acceso_da_me = False
        self.lascia = lascia_acceso
        if "\tdevice" not in adb("devices"):
            print("   ⏳ accendo l'emulatore «%s»…" % AVD, flush=True)
            subprocess.Popen([EMU, "-avd", AVD, "-no-window", "-no-audio",
                              "-no-boot-anim", "-gpu", "swiftshader_indirect",
                              "-no-snapshot", "-accel", "on", "-memory", "3072"],
                             stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self.acceso_da_me = True
            t0 = time.time()
            while time.time() - t0 < 300:
                if adb("shell", "getprop", "sys.boot_completed").strip() == "1":
                    break
                time.sleep(4)
            else:
                raise RuntimeError("l'emulatore non ha finito l'avvio in 300 s")
            time.sleep(5)
        # ⭐ Le bandiere si leggono da `/data/local/tmp/chrome-command-line` solo
        #   se Chrome e' l'app «in debug»; il primo nome della riga e' ignorato.
        adb("shell", "echo 'chrome --disable-fre --no-default-browser-check "
                     "--no-first-run --disable-signin-promo' "
                     "> /data/local/tmp/chrome-command-line")
        adb("shell", "am", "set-debug-app", "--persistent", CHROME_ANDROID)
        adb("shell", "am", "force-stop", CHROME_ANDROID)
        time.sleep(1)
        adb("shell", "am", "start", "-n",
            CHROME_ANDROID + "/com.google.android.apps.chrome.Main",
            "-a", "android.intent.action.VIEW", "-d", "about:blank")
        adb("forward", "tcp:%d" % porta, "localabstract:chrome_devtools_remote")
        time.sleep(4)
        self.aggancia(attesa=60)

    def palco(self):
        v = adb("shell", "dumpsys", "package", CHROME_ANDROID)
        ver = v.split("versionName=")[1].split()[0] if "versionName=" in v else "?"
        return ("%s %s su Android %s (emulatore «%s», GPU swiftshader: SOFTWARE)"
                % ("Chromium" if "chromium" in CHROME_ANDROID else "Chrome", ver,
                   adb("shell", "getprop", "ro.build.version.release").strip(), AVD))

    def muovi(self, x, y):
        # ⚠ Su Android il «mouse» e' un dito: un movimento e' un trascinamento
        self.trascina([(x, y), (x + 20, y + 10)])

    def clic(self, x, y):
        self.tocca(x, y)

    def chiudi(self):
        try:
            self.cdp.chiama("Page.navigate", url="about:blank")   # pagehide ⇒ CONGEDO
            time.sleep(1)
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.cdp.chiudi()
        except Exception:                        # noqa: BLE001
            pass
        adb("shell", "am", "force-stop", CHROME_ANDROID)
        adb("forward", "--remove", "tcp:%d" % self.porta)
        if self.acceso_da_me and not self.lascia:
            print("   ⏹ spengo l'emulatore (l'avevo acceso io)", flush=True)
            adb("emu", "kill")
            t0 = time.time()
            while time.time() - t0 < 30 and "emulator-" in adb("devices"):
                time.sleep(2)


class GuidaFirefox:
    tocco = False

    def __init__(self, porta, visibile):
        self.nome = "firefox"
        self.visibile = visibile
        self.p, self.m, self.profilo = MARIONETTE.accendi(
            porta=porta, headless=not visibile, largo=FINESTRA[0], alto=FINESTRA[1])
        # ⚠ `acceptInsecureCerts` va dato ANCHE fuori da `alwaysMatch`: `[M]` 18
        #   settembre 2026, Firefox 140 con la sola forma di `07-b46`
        #   (`sessione()`) rifiuta il certificato autofirmato («insecure
        #   certificate»); con tutt'e due lo accetta.  E' l'eccezione che
        #   l'utente aggiunge a mano col pannello.
        self.caps = self.m.chiama("WebDriver:NewSession", {
            "capabilities": {"alwaysMatch": {"acceptInsecureCerts": True}},
            "acceptInsecureCerts": True})
        self.log = os.path.join(self.profilo, "uscita.log")
        self.log_da = 0
        self.m.chiama("WebDriver:SetTimeouts", {"script": 60000, "pageLoad": 60000})

    def palco(self):
        c = (self.caps or {}).get("capabilities", {})
        return "Firefox %s · %s" % (c.get("browserVersion", "?"),
                                    "finestra vera" if self.visibile
                                    else "HEADLESS — senza GPU, tutto in software")

    def js(self, corpo, *arg):
        return self.m.js(corpo, list(arg))["value"]

    def vai(self, url):
        try:
            self.m.vai(url)
        except RuntimeError as e:
            return False, str(e)[:300]
        time.sleep(1)
        try:
            self.js(_inietta(RACCOGLITORE))
        except Exception:                        # noqa: BLE001
            pass
        return True, ""

    def ricarica(self):
        self.m.chiama("WebDriver:Refresh")
        time.sleep(1)
        try:
            self.js(_inietta(RACCOGLITORE))
        except Exception:                        # noqa: BLE001
            pass

    def fotografa_tela(self):
        el = self.m.chiama("WebDriver:FindElement",
                           {"using": "css selector", "value": "#schermo"})["value"]
        # ⚠ Marionette non ha `TakeElementScreenshot` (e' il nome W3C lato
        #   geckodriver): l'elemento si passa a `TakeScreenshot` con `id`.
        r = self.m.chiama("WebDriver:TakeScreenshot",
                          {"id": list(el.values())[0], "full": False})
        return base64.b64decode(r["value"]), ""

    def _azioni(self, azioni):
        self.m.chiama("WebDriver:PerformActions", {"actions": azioni})
        self.m.chiama("WebDriver:ReleaseActions")

    def muovi(self, x, y):
        self._azioni([{"type": "pointer", "id": "topo",
                       "parameters": {"pointerType": "mouse"},
                       "actions": [{"type": "pointerMove", "x": int(x), "y": int(y),
                                    "origin": "viewport", "duration": 0}]}])

    def clic(self, x, y):
        self._azioni([{"type": "pointer", "id": "topo",
                       "parameters": {"pointerType": "mouse"},
                       "actions": [{"type": "pointerMove", "x": int(x), "y": int(y),
                                    "origin": "viewport", "duration": 0},
                                   {"type": "pointerDown", "button": 0},
                                   {"type": "pause", "duration": 60},
                                   {"type": "pointerUp", "button": 0}]}])

    def tasto(self, t):
        w = TASTI[t]["wd"]
        self._azioni([{"type": "key", "id": "tastiera",
                       "actions": [{"type": "keyDown", "value": w},
                                   {"type": "pause", "duration": 80},
                                   {"type": "keyUp", "value": w}]}])

    def errori_fuori(self):
        """⚠ Da Firefox gli errori «da fuori» si leggono nella sua uscita
        (`devtools.console.stdout.content`, acceso da `07-b46`)."""
        try:
            with open(self.log, "rb") as f:
                f.seek(self.log_da)
                testo = f.read().decode("utf-8", "replace")
        except OSError as e:
            return [], [], "uscita di Firefox illeggibile: %s" % e
        js, rete = [], []
        for r in testo.splitlines():
            if r.startswith("JavaScript error:"):
                # ⚠ solo gli errori della PAGINA: quelli dei moduli interni di
                #   Firefox (`resource://`, `chrome://`) non sono nostri
                if "resource://" in r[:60] or "chrome://" in r[:60]:
                    continue
                js.append(r[:300])
            elif r.startswith("console.error:"):
                js.append(r[:300])
            elif "NS_ERROR_NET" in r or "NS_ERROR_CONNECTION" in r:
                rete.append(r[:300])
        return js, rete, ""

    def azzera_eventi(self):
        try:
            self.log_da = os.path.getsize(self.log)
        except OSError:
            self.log_da = 0

    def chiudi(self):
        try:
            self.m.vai("about:blank")                             # pagehide ⇒ CONGEDO
            time.sleep(1)
        except Exception:                        # noqa: BLE001
            pass
        try:
            self.m.chiama("Marionette:Quit")
        except Exception:                        # noqa: BLE001
            pass
        MARIONETTE.spegni(self.p, self.profilo)


# ═══════════════════════════════════════════════════════════════════════════
#  IL REGISTRO DEL SERVER
# ═══════════════════════════════════════════════════════════════════════════
def leggi_registro(cmd):
    if not cmd:
        return None, "nessun --registro-cmd"
    try:
        # ⛔ `errors="replace"`: il registro porta ⭐ ⛔ ⚠ →, e chi lo taglia
        #    (`cut -c`, `tail -c`) spezza le lettere da tre byte.  `[M]` 23 set
        #    2026: con l utf-8 stretto il banco MUORE di `UnicodeDecodeError`
        #    invece di tornare un errore — e si perde la misura gia' fatta.
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           errors="replace", timeout=60)
    except Exception as e:                       # noqa: BLE001
        return None, "il comando del registro non ha risposto: %s" % e
    if r.returncode != 0 and not r.stdout:
        return None, "il comando del registro e' fallito (%d): %s" % (
            r.returncode, r.stderr.strip()[:200])
    return r.stdout.splitlines(), ""


def righe_nuove(prima, dopo):
    """Le righe di `dopo` che non stavano in `prima` — contando i doppioni."""
    visto = {}
    for r in prima:
        visto[r] = visto.get(r, 0) + 1
    fuori = []
    for r in dopo:
        if visto.get(r, 0):
            visto[r] -= 1
        else:
            fuori.append(r)
    return fuori


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA DI UN BROWSER
# ═══════════════════════════════════════════════════════════════════════════
class Prova:
    def __init__(self, g, o, url, parola):
        self.g, self.o, self.url, self.parola = g, o, url, parola
        self.esiti = {}                            # punto -> (esito, motivo)
        self.note = []
        self.rifiuto = None

    def metti(self, punto, esito, motivo):
        self.esiti[punto] = (esito, motivo)
        segno = {VERDE: "⭐ 0", ROSSO: "⛔ 1", CIECO: "⚠ 3"}[esito]
        print("   %s  %-3s %-48s %s" % (punto, segno, NOMI_PUNTI[punto], motivo),
              flush=True)

    def cieco_da(self, da, perche):
        for p in da:
            if p not in self.esiti:
                self.metti(p, CIECO, "non ho potuto guardare: " + perche)

    def stato(self):
        try:
            return self.g.js(JS_STATO)
        except Exception as e:                   # noqa: BLE001
            return {"⛔": str(e)[:200]}

    def apri(self):
        aperta, motivo = self.g.vai(self.url)
        if not aperta:
            return False, "la pagina non si apre: %s" % motivo
        fine = time.time() + min(self.o.tetto_s, 30)
        m = None
        while time.time() < fine:
            try:
                m = self.g.js(JS_MODULO)
            except Exception as e:               # noqa: BLE001
                m = {"errore": str(e)[:200]}
            if m and m.get("modulo") and m.get("pronta") == "complete":
                break
            time.sleep(0.5)
        if not m or not m.get("modulo"):
            testo = (m or {}).get("testo", "") if isinstance(m, dict) else ""
            return False, ("il modulo d'accesso non c'e' (url %s): «%s»"
                           % ((m or {}).get("url"), " ".join(testo.split())[:160]))
        if not (m["utente"] and m["parola"] and m["vai"]):
            return False, "il modulo c'e' ma manca un campo: %s" % m
        if not m["remotix"]:
            return False, "il modulo c'e' ma `window.REMOTIX` no: lo script si e' fermato"
        if m.get("bannato") == "si":
            self.note.append("indirizzo BANNATO: «%s»" % m.get("avviso", "")[:160])
        if not m["visibile"]:
            return False, "il modulo c'e' ma non si vede (bannato=%s)" % m.get("bannato")
        return True, "%s · modulo visibile%s" % (m["url"], " ⚠ BANNATO"
                                                 if m.get("bannato") == "si" else "")

    def entra(self, parola):
        """Torna (esito, motivo, stato)."""
        r = self.g.js(JS_ENTRA, self.o.utente, parola)
        if r != "mandato":
            return ROSSO, "non ho potuto compilare il modulo: %s" % r, None
        fine = time.time() + self.o.tetto_s
        s = {}
        while time.time() < fine:
            s = self.stato()
            if s.get("sessione") and s.get("esito_classe") == "bene" \
                    and (s.get("esito") or "").startswith("Ammesso"):
                return VERDE, "«%s»" % s["esito"], s
            if s.get("esito_classe") == "male" and s.get("esito"):
                self.rifiuto = self._rifiuto(s)
                return ROSSO, "la pagina dice: «%s»" % s["esito"], s
            time.sleep(0.4)
        coda = [x for x in (s.get("registro") or "").splitlines() if x.strip()][-3:]
        self.rifiuto = self._rifiuto(s)
        return ROSSO, ("nessuna ammissione in %d s (esito «%s», sessione=%s); ultime "
                       "righe della pagina: %s" % (self.o.tetto_s, s.get("esito"),
                                                    s.get("sessione"), " | ".join(coda)[:300])), s

    @staticmethod
    def _rifiuto(s):
        """⛔ Un RIFIUTO vero: la pagina ha mandato le credenziali (riga
        «CREDENZIALI mandate», pagina.html ~4955) e non e' arrivato «AMMESSO»
        (riga ~4980).  Un collegamento mancato non e' un rifiuto."""
        reg = (s or {}).get("registro") or ""
        return ("CREDENZIALI mandate" in reg
                and not any(r.strip() == "AMMESSO" for r in reg.splitlines()))

    def primo_fotogramma(self):
        """Torna (esito, motivo, stato).  Contatore della pagina + fotografia."""
        fine = time.time() + self.o.tetto_s
        t0 = time.time()
        s = {}
        while time.time() < fine:
            s = self.stato()
            if (s.get("dipinti") or 0) > 0:
                break
            time.sleep(0.3)
        if not (s.get("dipinti") or 0) > 0:
            return ROSSO, ("nessun fotogramma dipinto in %d s (dipinti=%s, consegnati=%s, "
                           "schermo=%s)" % (self.o.tetto_s, s.get("dipinti"),
                                            s.get("consegnati"), s.get("acceso"))), s
        dopo = time.time() - t0
        # ⛔ «ENTRO IL TETTO», come dice la testa di questo file — e non una
        #    fotografia sola a +1 s.  `[M]` 18 set 2026 su KDE: il primo
        #    fotogramma di una sessione appena nata e' la schermata d'avvio di
        #    Plasma («Plasma made by KDE», 99 % nero + logo), cioe' il desktop
        #    vero che si accende, e dopo arriva il desktop.  ⇒ Si fotografa fino
        #    al tetto; il verde dice QUANDO e' arrivato il primo non degenere, e
        #    quante fotografie degeneri l'hanno preceduto.  ⛔ Una tela che resta
        #    nera fino al tetto e' ancora ROSSO (la certificazione lo prova).
        degeneri = 0
        prima_desc = ""
        while True:
            time.sleep(1.0)        # il vetro: la fotografia dopo almeno un quadro
            try:
                png, perche = self.g.fotografa_tela()
            except Exception as e:               # noqa: BLE001
                png, perche = None, "fotografia fallita: %s" % str(e)[:200]
            if not png:
                return CIECO, ("dipinti=%d in %.1f s, ma i pixel non li ho potuti "
                               "guardare: %s" % (s["dipinti"], dopo, perche)), s
            if self.o.salva:
                with open(os.path.join(self.o.salva, "%s-%d.png"
                                       % (self.g.nome, int(time.time() * 1000))), "wb") as f:
                    f.write(png)
            degenere, desc = giudica_pixel(png)
            if degenere is None:
                return CIECO, "dipinti=%d, pixel non giudicabili: %s" % (s["dipinti"], desc), s
            if not degenere:
                break
            degeneri += 1
            prima_desc = prima_desc or desc
            if time.time() >= fine:
                return ROSSO, ("dipinti=%d ma la tela e' DEGENERE fino al tetto di %d s "
                               "(%d fotografie): %s" % (s["dipinti"], self.o.tetto_s,
                                                        degeneri, desc)), s
        s = self.stato()
        visto = time.time() - t0
        if degeneri:
            return VERDE, ("dipinti=%d · primo fotogramma a %.1f s, desktop NON degenere a "
                           "%.1f s dopo %d fotografie degeneri (la prima: %s) · %s"
                           % (s.get("dipinti") or 0, dopo, visto, degeneri, prima_desc,
                              desc)), s
        return VERDE, "dipinti=%d dopo %.1f s · %s" % (s["dipinti"], dopo, desc), s

    def centro(self, s, fx=0.5, fy=0.5):
        t = s.get("tela") or [0, 0, 0, 0]
        vl, va = s.get("vista", [1400, 1000, 1])[:2]
        x0, y0 = max(0, t[0]), max(0, t[1])
        x1, y1 = min(vl, t[0] + t[2]), min(va, t[1] + t[3])
        return x0 + (x1 - x0) * fx, y0 + (y1 - y0) * fy

    def continuita(self):
        s0 = self.stato()
        d0 = s0.get("dipinti") or 0
        scena = self.o.scena
        passi = 0
        fine = time.time() + self.o.continuita_s
        if scena == "muovi":
            # ⭐ attraversa tutta la tela a serpentina, bordi compresi (barra e
            #   dock sono ai bordi: sono le cose che reagiscono al passaggio)
            fr = [(0.02 + 0.96 * (i % 25) / 24.0, 0.01 + 0.98 * (i // 25) / 7.0)
                  for i in range(200)]
            i = 0
            while time.time() < fine:
                fx, fy = fr[i % len(fr)]
                if (i // 25) % 2:
                    fx = 1.0 - fx
                x, y = self.centro(s0, fx, fy)
                try:
                    self.g.muovi(x, y)
                    passi += 1
                except Exception as e:           # noqa: BLE001
                    self.note.append("movimento fallito: %s" % str(e)[:120])
                    break
                i += 1
                time.sleep(0.12 if not self.g.tocco else 0.3)
            time.sleep(1.0)
        else:
            time.sleep(self.o.continuita_s)
        s1 = self.stato()
        d1 = s1.get("dipinti") or 0
        nuovi = d1 - d0
        base = "%d fotogrammi nuovi in %.0f s (scena «%s»%s)" % (
            nuovi, self.o.continuita_s, scena,
            ", %d movimenti" % passi if scena == "muovi" else "")
        if nuovi > 0:
            return VERDE, base
        if not s1.get("sessione"):
            return ROSSO, base + " · ⛔ e la sessione non c'e' piu': «%s»" % s1.get("esito")
        if scena == "ferma":
            return CIECO, base + " · su una scena ferma zero e' possibile: dichiara " \
                                 "`--scena viva` o `muovi` per un giudizio"
        if scena == "muovi":
            return ROSSO, base + " · ⚠ il cursore lo disegna la pagina: se il desktop " \
                                 "non reagisce al passaggio, rifai con una scena viva"
        return ROSSO, base

    def ingresso(self, prima_reg):
        """Tasto + movimento/clic (tocco su Android).  Torna (esito, motivo)."""
        a = self.g.js(_inietta(JS_ANELLO))
        chk = self.g.js("const c=window.REMOTIX_INPUT; return c ? !!c.__banco : null;")
        if chk is None:
            return ROSSO, "la pagina non ha la cucitura dell'input (`REMOTIX_INPUT` e' null)"
        if not chk:
            return CIECO, "non sono riuscito ad avvolgere `REMOTIX_INPUT.manda` (%s)" % a
        s = self.stato()
        x, y = self.centro(s, self.o.clic[0], self.o.clic[1])
        fatti = []
        try:
            # il clic prima: da' il fuoco alla tela, e la tastiera va dove c'e' il fuoco
            if self.g.tocco:
                self.g.tocca(x, y); fatti.append("tocco")
                time.sleep(0.4)
                self.g.trascina([(x, y), (x + 30, y + 15), (x + 60, y + 30)])
                fatti.append("trascinamento")
            else:
                self.g.muovi(x - 40, y - 20); self.g.muovi(x, y)
                fatti.append("movimento")
                if not self.o.senza_clic:
                    self.g.clic(x, y); fatti.append("clic")
            time.sleep(0.4)
            self.g.tasto(self.o.tasto); fatti.append("tasto %s" % self.o.tasto)
            time.sleep(0.4)
            # ⭐ un ultimo movimento: se il desktop cambia, un fotogramma riporta
            #   indietro un id ≥ di tutti quelli di sopra
            self.g.muovi(x + 5, y + 5)
        except Exception as e:                   # noqa: BLE001
            return CIECO, "l'iniezione non e' partita (%s): %s" % (", ".join(fatti),
                                                                    str(e)[:200])
        time.sleep(3.0)
        t = self.g.js(JS_TORNATI) or {}
        tipi = {TIPI_INPUT.get(int(k), k): v for k, v in (t.get("tipi") or {}).items()}
        ids = {int(k): v for k, v in (t.get("ids") or {}).items()}
        tasto_ids = ids.get(0x0105, []) + ids.get(0x0104, [])
        topo_ids = ids.get(0x0101, []) + ids.get(0x0102, [])
        spediti = "la pagina ha spedito %s" % (tipi or "NIENTE")
        if not tasto_ids and not topo_ids:
            return ROSSO, "%s dopo %s: l'input non esce dalla pagina" % (spediti, fatti)
        mancano = []
        if not tasto_ids:
            mancano.append("il tasto")
        if not topo_ids:
            mancano.append("il mouse/tocco")
        # 1) il registro del server, se c'e'
        dopo, perche = leggi_registro(self.o.registro_cmd) if prima_reg is not None \
            else (None, "nessun --registro-cmd")
        if dopo is not None:
            nuove = [r for r in righe_nuove(prima_reg, dopo) if "input id=" in r]
            srv_t = [r for r in nuove if "POSIZIONE_TASTO" in r or "LETTERA" in r]
            srv_m = [r for r in nuove if "PUNTATORE" in r or "PULSANTE" in r]
            base = ("%s · nel registro del server %d righe d'input nuove (tasto %d, "
                    "mouse %d)" % (spediti, len(nuove), len(srv_t), len(srv_m)))
            if nuove:
                self.note.append("server: " + nuove[-1][:200])
            if mancano:
                return ROSSO, base + " · ⛔ la pagina NON ha spedito " + " e ".join(mancano)
            if srv_t and srv_m:
                return VERDE, base
            return ROSSO, base + " · ⛔ al server non e' arrivato " + " e ".join(
                (["il tasto"] if not srv_t else []) + (["il mouse"] if not srv_m else []))
        # 2) senza registro: il ritorno degli id nei fotogrammi
        mx = t.get("max_tornato") or 0
        base = "%s · id piu' alto tornato in un fotogramma: %s (%s)" % (
            spediti, mx or "nessuno", perche)
        if mancano:
            return ROSSO, base + " · ⛔ la pagina NON ha spedito " + " e ".join(mancano)
        if mx >= max(tasto_ids) and mx >= min(topo_ids):
            return VERDE, base + " ⇒ il server li ha applicati tutti fino a %d" % mx
        return CIECO, base + " · nessun ritorno che copra tutti e due: senza registro " \
                             "del server non posso dire se sono arrivati"

    def errori(self, s):
        dentro_js = (s.get("banco") or {}).get("errori") or []
        dentro_rete = (s.get("banco") or {}).get("rete") or []
        fuori_js, fuori_rete, perche = self.g.errori_fuori()
        dich = [r for r in (s.get("registro") or "").splitlines() if "⛔" in r]
        tutti_js = list(dict.fromkeys(fuori_js + dentro_js))
        tutti_rete = list(dict.fromkeys(fuori_rete + dentro_rete))
        for r in tutti_js[:12]:
            print("         js    %s" % r[:220])
        for r in tutti_rete[:12]:
            print("         rete  %s" % r[:220])
        for r in dich[:12]:
            print("         ⛔pag %s" % r[:220])
        if s.get("errori_schermo"):
            print("         schermo.errori %s" % s["errori_schermo"])
        base = "%d errori JS · %d di rete · %d righe «⛔» dichiarate dalla pagina" % (
            len(tutti_js), len(tutti_rete), len(dich))
        if s.get("banco") is None and perche:
            return CIECO, base + " · ⚠ ne' raccoglitore nella pagina ne' uscita: " + perche
        if tutti_js or tutti_rete:
            return ROSSO, base
        return VERDE, base + (" (le «⛔» della pagina sono elencate, non giudicate)"
                              if dich else "")

    def corri(self, solo_ab=False):
        prima_reg, perche_reg = (leggi_registro(self.o.registro_cmd)
                                 if self.o.registro_cmd else (None, "nessun --registro-cmd"))
        if self.o.registro_cmd and prima_reg is None:
            self.note.append("registro del server: " + perche_reg)
        self.g.azzera_eventi()
        ok, motivo = self.apri()
        self.metti("a", VERDE if ok else ROSSO, motivo)
        if not ok:
            self.cieco_da("bcdefg", "(a) non e' verde")
            return
        e, motivo, s = self.entra(self.parola)
        self.metti("b", e, motivo)
        if e != VERDE:
            if s:
                self.metti("f", *self.errori(s))
            self.cieco_da("cdeg", "(b) non e' verde")
            return
        if solo_ab:
            return
        e, motivo, s = self.primo_fotogramma()
        self.metti("c", e, motivo)
        if s.get("dipinti"):
            self.metti("d", *self.continuita())
        else:
            self.cieco_da("d", "nessun primo fotogramma")
        if s.get("sessione"):
            prima_in = None
            if self.o.registro_cmd:
                prima_in, _ = leggi_registro(self.o.registro_cmd)
            self.metti("e", *self.ingresso(prima_in))
        else:
            self.cieco_da("e", "la sessione non c'e'")
        s = self.stato()
        self.metti("f", *self.errori(s))
        # (g) la riconnessione
        try:
            self.g.ricarica()
            ok, motivo = self.apri_dopo_ricarica()
            if not ok:
                self.metti("g", ROSSO, "dopo la ricarica: " + motivo)
                return
            e, motivo, s = self.entra(self.parola)
            if e != VERDE:
                self.metti("g", e, "dopo la ricarica non rientra: " + motivo)
                return
            e, motivo, s = self.primo_fotogramma()
            self.metti("g", e, "rientrata (%s) · %s" % (
                (s.get("esito") or "")[:60], motivo))
        except Exception as ex:                  # noqa: BLE001
            self.metti("g", CIECO, "la ricarica non e' riuscita dal banco: %s" % str(ex)[:200])

    def apri_dopo_ricarica(self):
        fine = time.time() + min(self.o.tetto_s, 30)
        while time.time() < fine:
            try:
                m = self.g.js(JS_MODULO)
                if m and m.get("modulo") and m.get("pronta") == "complete" and m.get("visibile"):
                    return True, ""
            except Exception:                    # noqa: BLE001
                pass
            time.sleep(0.5)
        return False, "il modulo non ricompare in %d s" % min(self.o.tetto_s, 30)

    def verdetto(self):
        v = [e for e, _ in self.esiti.values()]
        if ROSSO in v:
            return "FAIL"
        if CIECO in v:
            return "BLOCKED"
        return "PASS"


# ═══════════════════════════════════════════════════════════════════════════
def accendi_guida(nome, o):
    if nome == "firefox":
        return GuidaFirefox(o.porte_base, o.visibile)
    if nome == "chrome":
        return GuidaChrome(o.porte_base + 1, o.visibile)
    if nome == "android":
        return GuidaAndroid(o.porte_base + 2, o.lascia_acceso)
    raise ValueError(nome)


def un_browser(nome, o, url, parola, solo_ab=False, etichetta=""):
    print("\n══ %s%s ══════════════════════════════" % (nome.upper(), etichetta), flush=True)
    g = None
    riga = {"browser": nome, "url": url, "etichetta": etichetta.strip(" ·") or "prova"}
    try:
        try:
            g = accendi_guida(nome, o)
        except Exception as e:                   # noqa: BLE001
            print("   ⛔ il browser non si e' acceso: %s" % str(e)[:300])
            riga.update(verdetto="BLOCKED", palco=None,
                        esiti={p: [CIECO, "browser non acceso: %s" % str(e)[:200]]
                               for p in "abcdefg"})
            print("RIGA " + json.dumps(riga, ensure_ascii=False))
            return riga
        palco = g.palco()
        print("   palco: %s" % palco, flush=True)
        pr = Prova(g, o, url, parola)
        try:
            pr.corri(solo_ab=solo_ab)
        except Exception as e:                   # noqa: BLE001
            print("   ⛔ il banco e' caduto: %s" % repr(e)[:300])
            pr.cieco_da("abcdefg", "il banco e' caduto: %s" % str(e)[:160])
        if solo_ab:
            for p in "cdefg":
                pr.esiti.setdefault(p, (CIECO, "non guardato: prova di certificazione"))
        for n in pr.note:
            print("   nota: %s" % n)
        v = pr.verdetto()
        print("   ▶ %s: %s" % (nome, v))
        riga.update(verdetto=v, palco=palco, headless=(not o.visibile) if nome != "android"
                    else "emulatore-software",
                    scena=o.scena, tetto_s=o.tetto_s,
                    esiti={p: [e, m] for p, (e, m) in sorted(pr.esiti.items())},
                    rifiuto=pr.rifiuto, note=pr.note)
        print("RIGA " + json.dumps(riga, ensure_ascii=False), flush=True)
        return riga
    finally:
        if g is not None:
            try:
                g.chiudi()
            except Exception as e:               # noqa: BLE001
                print("   ⚠ chiusura del browser: %s" % e)


def porta_vuota():
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def url_android(url):
    """⚠ Dall'emulatore «localhost» e' l'emulatore stesso: il portatile e'
    10.0.2.2.  La LAN (192.168.0.2) si raggiunge direttamente."""
    u = urllib.parse.urlsplit(url)
    if u.hostname in ("localhost", "127.0.0.1"):
        return urllib.parse.urlunsplit(u._replace(
            netloc="10.0.2.2" + (":%d" % u.port if u.port else "")))
    return url


def certifica(o, browser):
    print("\n══════════ CERTIFICAZIONE DEL BANCO ══════════")
    e, t = certifica_giudice()
    print("   giudice dei pixel: %s — %s" % ({VERDE: "⭐ sa dire degenere",
                                               ROSSO: "⛔ CIECO", CIECO: "⚠ 3"}[e], t))
    tab = [("giudice-pixel", e, t)]
    for nome in browser:
        vuota = "https://127.0.0.1:%d/" % porta_vuota()
        u = url_android(vuota) if nome == "android" else vuota
        r = un_browser(nome, o, u, o.parola, solo_ab=True, etichetta=" · certifica: porta vuota")
        ea = r["esiti"]["a"][0]
        tab.append(("%s porta vuota" % nome, VERDE if ea == ROSSO else ROSSO,
                    "(a)=%s — atteso 1" % ea))
        u = url_android(o.url) if nome == "android" else o.url
        r = un_browser(nome, o, u, o.parola + "-SBAGLIATA-" + str(os.getpid()),
                       solo_ab=True, etichetta=" · certifica: parola sbagliata")
        ea, eb = r["esiti"]["a"][0], r["esiti"]["b"]
        # ⛔ il rosso deve essere un RIFIUTO: la pagina ha mandato le
        #   credenziali (riga «CREDENZIALI mandate», pagina.html ~4955) e
        #   non e' stata ammessa.  Un collegamento mancato non certifica niente.
        if ea != VERDE:
            tab.append(("%s parola sbagliata" % nome, CIECO,
                        "(a)=%s: senza pagina non si certifica (b)" % ea))
        elif eb[0] == ROSSO and r.get("rifiuto"):
            tab.append(("%s parola sbagliata" % nome, VERDE, "(b)=1 per rifiuto: %s" % eb[1][:120]))
        elif eb[0] == ROSSO:
            tab.append(("%s parola sbagliata" % nome, CIECO,
                        "(b)=1 ma NON per rifiuto (il server non ha risposto alle "
                        "credenziali): %s" % eb[1][:160]))
        else:
            tab.append(("%s parola sbagliata" % nome, ROSSO,
                        "⛔ (b)=%s con la parola sbagliata: banco CIECO" % eb[0]))
    print("\n══════════ ESITO DELLA CERTIFICAZIONE ══════════")
    for n, e, t in tab:
        print("   %-28s %s  %s" % (n, {VERDE: "⭐ certificato", ROSSO: "⛔ NON certificato",
                                      CIECO: "⚠ 3 non certificabile qui"}[e], t))
    print("RIGA " + json.dumps({"certificazione": [[n, e, t] for n, e, t in tab]},
                               ensure_ascii=False))
    return 1 if any(e == ROSSO for _, e, _ in tab) else (3 if any(e == CIECO for _, e, _ in tab) else 0)


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--url", default="https://192.168.0.2:8511/")
    a.add_argument("--utente", default="prova")
    a.add_argument("--parola", default=os.environ.get("REMOTIX_PAROLA", ""),
                   help="o nella variabile REMOTIX_PAROLA")
    a.add_argument("--browser", default="firefox,chrome,android")
    a.add_argument("--visibile", action="store_true",
                   help="finestra vera invece di headless (Firefox e Chrome)")
    a.add_argument("--tetto-s", type=int, default=30,
                   help="tetto per l'ammissione e per il primo fotogramma")
    a.add_argument("--scena", choices=("muovi", "viva", "ferma"), default="muovi")
    a.add_argument("--continuita-s", type=int, default=8)
    a.add_argument("--tasto", choices=sorted(TASTI), default="Control",
                   help="il tasto da premere: Control da solo non fa niente sul desktop")
    a.add_argument("--clic", default="0.5,0.5",
                   help="dove cliccare/toccare, in frazioni della tela")
    a.add_argument("--senza-clic", action="store_true",
                   help="solo movimento, niente clic (desktop con cose delicate)")
    a.add_argument("--registro-cmd", default="",
                   help="comando shell che stampa il registro del server")
    a.add_argument("--finestra", default="1400x1000",
                   help="misura della finestra dei browser, LxA")
    a.add_argument("--salva", default="", help="cartella dove lasciare le fotografie")
    a.add_argument("--porte-base", type=int, default=2851)
    a.add_argument("--lascia-acceso", action="store_true",
                   help="non spegnere l'emulatore se l'ha acceso il banco")
    a.add_argument("--certifica", action="store_true")
    o = a.parse_args()
    FINESTRA[:] = [int(x) for x in o.finestra.lower().split("x")]
    o.clic = [float(x) for x in o.clic.split(",")]
    if o.salva:
        os.makedirs(o.salva, exist_ok=True)
    browser = [b.strip() for b in o.browser.split(",") if b.strip()]
    for b in browser:
        if b not in ("firefox", "chrome", "android"):
            a.error("browser sconosciuto: %s" % b)
    if not o.parola:
        a.error("serve --parola (o REMOTIX_PAROLA)")
    print("⭐ 12-client-veri · %s · utente %s · browser %s · tetto %d s · scena «%s» · %s"
          % (o.url, o.utente, ",".join(browser), o.tetto_s, o.scena,
             "finestre vere" if o.visibile else "HEADLESS (senza GPU)"))
    if o.certifica:
        return certifica(o, browser)
    righe = []
    for b in browser:
        u = url_android(o.url) if b == "android" else o.url
        righe.append(un_browser(b, o, u, o.parola))
    print("\n══════════ VERDETTI ══════════")
    for r in righe:
        print("   %-8s %s" % (r["browser"], r["verdetto"]))
    v = [r["verdetto"] for r in righe]
    return 1 if "FAIL" in v else (3 if "BLOCKED" in v else 0)


if __name__ == "__main__":
    sys.exit(main())
