#!/usr/bin/env python3
"""06-b37-comune.py — gli attrezzi delle scene di 6.5, e ⛔ IL GIUDIZIO SUL PALCO.

⛔⛔ PERCHE' IL PALCO SI GIUDICA PRIMA DEL PRODOTTO — `LEZIONI.md` §1.15

    «Su Xvfb `requestAnimationFrame` non gira MAI» — `[M]` 13 agosto 2026, fase
    3: 0 quadri in 3 secondi, con `visibilityState` a «visible».  ⛔ E in Blink
    l'evento `resize` si consegna DENTRO il giro di rendering ⇒ senza quadri non
    arriva mai.  Cioe' proprio il cammino che segue la finestra dell'utente —
    `rinegozia_vista()`, la scala, `?adatta=segui` — sarebbe **codice morto sul
    banco**, e il banco lo direbbe verde.

⇒ Qui il palco si MISURA prima di misurare il prodotto, e se e' morto il banco
  dice **«IL PALCO, NON IL PRODOTTO»** e si ferma.  ⚠ Il quadro si batte un
  numero FISSO di volte, dichiarato: mai «finche' diventa verde» — un'opzione di
  stampa che decide l'esito di una certificazione e' gia' costata a questo
  progetto una certificazione intera (`Page.captureScreenshot` sotto `if
  args.copia`).

⭐ E QUEL CHE QUESTA SPIA HA TROVATO, il 16 agosto 2026, va letto prima di
  fidarsi di §1.15 alla lettera: su **Chrome 151.0.7922.137** e su **Firefox
  140.13.0esr**, con Xvfb e SENZA nessuna battuta, i quadri girano e i `resize`
  arrivano — il numero esatto lo stampa `giudica_palco()` a ogni giro, ed e'
  quello che conta, non questa riga.
"""
import hashlib
import json
import os
import subprocess
import time
import urllib.request

# ⛔⭐ L'IDENTITA' DEL GIRO — 22 agosto 2026, rilievo della revisione avversariale
#    del 21 agosto (`fasi/06` §5.5).  Il deposito degli esiti si scriveva in
#    APPEND **senza orologio ne' numero di giro**: le righe dentro erano del 16
#    agosto mentre due script erano stati riscritti il 17, e chi apriva il file
#    NON POTEVA SAPERE DI QUALE GIRO FOSSE UNA RIGA.
#
# ⇒ Ogni riga porta adesso QUATTRO cose, e nessuna e' facoltativa:
#      `giro`      l'identita' del lancio (la mette `06-b37-lancia.sh`)
#      `orologio`  l'istante UNIX, e `ora` la stessa cosa leggibile
#      `sorgente`  QUALE pagina e' stata misurata, con la sua impronta SHA-256
#      `guasto`    il guasto innestato, o `nessuno`
# ⚠ L'impronta e' della SORGENTE (il prodotto o la sua copia guasta), non della
#   copia strumentata: la sonda si aggiunge sempre e non e' quel che si misura.
GIRO = os.environ.get("B37_GIRO") or "senza-giro"
# ⛔ Le fotografie grezze NON si conservano di suo: `/tmp` qui e' un tmpfs da
#    3,8 GB condiviso con gli altri agenti, e un giro intero ne scriveva 1,5 GB.
TIENI_FOTO = (os.environ.get("B37_FOTO") or "no") == "tieni"
SORGENTE = os.environ.get("B37_SORGENTE") or "?"
GUASTO = os.environ.get("B37_GUASTO") or "nessuno"


def impronta_sorgente(percorso):
    try:
        with open(percorso, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except OSError:
        return "?"


SORGENTE_SHA = os.environ.get("B37_SORGENTE_SHA") or impronta_sorgente(SORGENTE)


def marca(d):
    """⛔ Le quattro marche del giro, su OGNI riga di esito.  Si mettono qui e in
       un posto solo: due funzioni che marcano sono due marche che divergono."""
    d.setdefault("giro", GIRO)
    d.setdefault("orologio", round(time.time(), 3))
    d.setdefault("ora", time.strftime("%Y-%m-%dT%H:%M:%S"))
    d.setdefault("sorgente", SORGENTE)
    d.setdefault("sorgente_sha", SORGENTE_SHA)
    d.setdefault("guasto", GUASTO)
    return d


# ⛔⭐⭐ LA CALIBRAZIONE ESTERNA — 22 agosto 2026, e senza di lei tre verdetti di
#      questo banco erano IDENTITA' ALGEBRICHE (`fasi/06` §5.5, falsi verdi 1, 3 e 4).
#
#   Il difetto vecchio: la «verita' esterna» di `06-b37-numeri.py` era
#   `xwininfo − BORDO − barra`, e `BORDO` veniva **calibrato come la moda di
#   `xwininfo − innerWidth×dpr`**.  ⇒ La misura di `xwininfo` si semplifica via, e
#   quel che restava era `round(iw·dpr) − round(barra·dpr) ≈ round(cw·dpr)`,
#   cioe' **lo stesso ingresso di `misura_vista()`**.  Un prodotto che sbagliasse
#   la conversione da pixel CSS a pixel del dispositivo — per esempio col
#   `Math.round` che questa fase ha curato — restava VERDE.
#
#   La cura: la larghezza del contenuto si legge **sui pixel dello schermo**.  Si
#   appendono due strisce a posizione FISSA — una orizzontale larga `100 %` in
#   cima, una verticale alta `100 %` a sinistra — e si fotografa.  Il loro
#   rettangolo, in pixel del dispositivo, e':
#
#     · `ox`, `oy`   dove sta il pixel CSS (0,0) della vista sullo schermo X;
#     · `l`, `a`     quanti pixel del dispositivo vale davvero la vista.
#
#   ⛔ E non passa da `devicePixelRatio`, da `innerWidth`, da `clientWidth` ne' da
#      nessuna riga del prodotto: e' il rasterizzatore che risponde.
#
# ⚠ Perche' `position: fixed` non falsa la scena: non partecipa al flusso, non
#   entra nella regione di scorrimento della vista (quindi non fa comparire
#   barre), e `width: 100 %` si risolve sul blocco contenitore iniziale — cioe'
#   esattamente `documentElement.clientWidth`.  ⛔ Verificato a ogni chiamata:
#   `cw`/`ch` prima e dopo devono coincidere, altrimenti la calibrazione si
#   RIFIUTA invece di restituire un numero.
CAL_METTI = """(function () {
  if (window.__b37_cal) return "gia' messe";
  const mk = function (id, css) {
    const e = document.createElement("div");
    e.id = id;
    e.style.cssText = "position:fixed;pointer-events:none;margin:0;padding:0;"
                    + "border:0;box-sizing:border-box;" + css;
    document.documentElement.appendChild(e);
    return e;
  };
  window.__b37_cal = [
    mk("b37calV", "left:0;bottom:0;width:3px;height:100%;background:#00ffff;"
                + "z-index:2147483646;"),
    mk("b37calH", "left:0;top:0;width:100%;height:3px;background:#ff00ff;"
                + "z-index:2147483647;")];
  return "messe";
})()"""

CAL_TOGLI = """(function () {
  if (!window.__b37_cal) return "gia' tolte";
  for (const e of window.__b37_cal) if (e.parentNode) e.parentNode.removeChild(e);
  window.__b37_cal = null;
  return "tolte";
})()"""


# ⛔⛔⭐ IL FOTOGRAMMA SI METTE DALLA STRADA CHE IL PRODOTTO USA DAVVERO —
#      22 agosto 2026, e senza questa riga le QUATTRO scene sui pixel di questa
#      sottofase **non misuravano piu' niente**.
#
#   Le scene `pixel`, `sfora`, `coordinate` e `windows` mettevano il fotogramma
#   cosi': `schermo.deposito = c; schermo.componi()`.  ⛔ Ma `componi()` comincia
#   con `if (this.bm) { this.cornice(); return false; }` — e `this.bm` c'e' su
#   tutt'e due i motori dal giorno in cui la tela e' passata a
#   `bitmaprenderer` (`DECISIONI.md` §5.4).  ⇒ Il deposito veniva **ignorato**,
#   sullo schermo non compariva nessun disegno, e i marcatori non si trovavano.
#
# ⚠ `[M]` 22 agosto 2026, `sfora` su Chrome 151: **12 larghezze su 12** senza
#   nessun marcatore nella fotografia.  ⭐ I banchi si sono comportati bene — «i
#   marcatori non si trovano» invece di uno zero — ⛔ ma gli esiti del 16 agosto
#   nel deposito sono di PRIMA di quel cambiamento, e §4.3-bis li dichiarava
#   ancora validi.
#
# ⇒ Adesso la strada si sceglie come la sceglie il prodotto, si percorre con la
#   FUNZIONE DEL PRODOTTO (`schermo.mostra()`, la stessa che riceve i fotogrammi
#   veri) e **si dichiara in ogni riga di esito** (`strada`).
STRUMENTI = r"""(function () {
  window.__b37_disegna = function (L, A, quali) {
    const c = document.createElement("canvas");
    c.width = L; c.height = A;
    const g = c.getContext("2d");
    g.fillStyle = (quali.indexOf("grigio") >= 0) ? "#202020" : "#000000";
    g.fillRect(0, 0, L, A);
    if (quali.indexOf("righe") >= 0) {
      /* righe verticali da UN pixel: il caso peggiore del ricampionamento, ed
         e' esattamente il testo di un terminale */
      g.fillStyle = "#ffffff";
      for (let x = 0; x < L; x += 2) g.fillRect(x, 0, 1, A);
    }
    g.fillStyle = "#ff0000"; g.fillRect(0, 0, 4, A);
    g.fillStyle = "#00ff00"; g.fillRect(L - 4, 0, 4, A);
    if (quali.indexOf("orizzontali") >= 0) {
      g.fillStyle = "#0000ff"; g.fillRect(0, 0, L, 4);
      g.fillStyle = "#ffff00"; g.fillRect(0, A - 4, L, 4);
    }
    return c;
  };

  window.__b37_mostra = async function (L, A, quali) {
    const c = window.__b37_disegna(L, A, quali);
    schermo.tela_l = L; schermo.tela_a = A;
    schermo.adatta_vista();
    let strada;
    if (schermo.bm) {
      /* ⭐ LA STRADA VERA: `mostra()` e' la funzione che riceve i fotogrammi
         del server.  Le si da' una `<canvas>` invece di un `VideoFrame`:
         `createImageBitmap` la accetta, `f.timestamp` esce `undefined` (e il
         codice lo controlla) e `f.close()` alza, dentro il suo try/catch. */
      strada = "bitmaprenderer/mostra";
      schermo.mostra(c, L, A);
    } else {
      strada = "deposito/componi";
      schermo.deposito = c;
      schermo.componi();
    }
    /* ⛔ `mostra()` e' ASINCRONA: si aspetta che il fotogramma sia AL VETRO, e
       si aspetta un numero FINITO di giri — mai «finche' diventa verde». */
    /* ⚠ Si aspetta che il FOTOGRAMMA sia arrivato — `dipinta.fotogramma` — e
       NON che il buffer valga il fotogramma: sono due cose diverse, e la
       seconda e' proprio quel che un guasto puo' rompere.  ⛔ Metterla qui
       farebbe morire il banco PRIMA del verdetto, cioe' lo farebbe rosso per
       il motivo sbagliato (`[M]` 22 agosto 2026, guasto G4). */
    let giri = 0;
    for (; giri < 80; giri++) {
      const d = schermo.dipinta;
      if (d && d.fotogramma && d.fotogramma[0] === L && d.fotogramma[1] === A)
        break;
      await new Promise(function (r) { setTimeout(r, 25); });
    }
    const el = $("schermo"), doc = document.documentElement;
    const r = el.getBoundingClientRect();
    const mr = el.parentElement.getBoundingClientRect();
    const st = getComputedStyle(el);
    return JSON.stringify({
      strada: strada, giri: giri, al_vetro: giri < 80,
      /* ⛔ Il buffer vale il fotogramma?  Si OSSERVA e si scrive, non si
         pretende qui: chi lo pretende e' il verdetto della scena. */
      buffer_pari_al_fotogramma: (schermo.tela.width === L
                                  && schermo.tela.height === A),
      dpr: devicePixelRatio,
      cw: doc.clientWidth, ch: doc.clientHeight,
      scrollW: doc.scrollWidth, scrollH: doc.scrollHeight,
      buffer: [el.width, el.height],
      rect: [r.left, r.top, r.width, r.height],
      rect_destro: r.right,
      rect_fisico: [r.left * devicePixelRatio, r.top * devicePixelRatio,
                    r.width * devicePixelRatio, r.height * devicePixelRatio],
      genitore: [mr.left, mr.top, mr.width, mr.height],
      stile: [st.width, st.height, st.imageRendering],
      image_rendering: st.imageRendering,
      vista: [schermo.vista_l, schermo.vista_a],
      tela: [schermo.tela_l, schermo.tela_a],
      dipinta: schermo.dipinta,
      scala_pagina: Math.min(schermo.vista_l / L, schermo.vista_a / A, 1)
    });
  };
  return "pronti";
})()"""


class Banco:
    def __init__(self, porta, display, pidbr, nome, esiti):
        self.porta = int(porta)
        self.display = display
        self.pidbr = str(pidbr)
        self.nome = nome
        self.esiti = esiti
        self.base = "http://127.0.0.1:%d" % self.porta
        self.wid = None

    # -- il filo con la pagina ------------------------------------------------
    def com(self, js, attesa=20):
        r = urllib.request.Request(self.base + "/comanda",
                                   data=js.encode("utf-8"),
                                   headers={"X-Attesa": str(attesa)})
        with urllib.request.urlopen(r, timeout=attesa + 10) as f:
            return json.loads(f.read().decode("utf-8"))

    def val(self, js, attesa=20):
        """Il valore di un'espressione.  ⛔ Se non e' arrivata risposta si alza
           un'eccezione: uno scaduto non deve poter passare per un dato."""
        d = self.com(js, attesa)
        if not d.get("ok"):
            raise RuntimeError("comando fallito (%s): %s"
                               % (js[:60], d.get("valore")))
        return d["valore"]

    def js(self, js, attesa=20):
        return json.loads(self.val("JSON.stringify(%s)" % js, attesa))

    def scrivi(self, d, iniezione="no"):
        d["banco"] = "06-b37"
        d["motore"] = self.nome
        d["iniezione"] = iniezione
        marca(d)
        with open(self.esiti, "a", encoding="utf-8") as f:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")

    # -- lo schermo X ---------------------------------------------------------
    def x(self, *a):
        return subprocess.run(a, capture_output=True, text=True,
                              env={"DISPLAY": self.display,
                                   "PATH": "/usr/bin:/bin"})

    def geometria(self, wid=None):
        r = self.x("xwininfo", "-id", wid or self.wid)
        g = {}
        for riga in r.stdout.splitlines():
            riga = riga.strip()
            for chiave, etichetta in (("l", "Width:"), ("a", "Height:"),
                                      ("x", "Absolute upper-left X:"),
                                      ("y", "Absolute upper-left Y:")):
                if riga.startswith(etichetta):
                    g[chiave] = int(riga.split()[-1])
        return g if len(g) == 4 else None

    def trova_finestra(self, secondi=30):
        """⛔ E si ASPETTA che compaia — 22 agosto 2026.  Qui c'era un colpo
           solo: se il browser stava ancora aprendosi la scena moriva con
           «nessuna finestra X per il pid …».  ⚠ Una finestra che non c'e'
           ANCORA e una che non ci sara' MAI hanno lo stesso aspetto, e la
           differenza e' il tempo che le si concede — dichiarato, finito."""
        scadenza = time.time() + secondi
        while True:
            r = self.x("xdotool", "search", "--onlyvisible", "--pid", self.pidbr)
            migliore, area = None, -1
            for w in r.stdout.split():
                g = self.geometria(w)
                if g and g["l"] * g["a"] > area:
                    migliore, area = w, g["l"] * g["a"]
            # ⚠ Chrome apre finestre invisibili da 1×1: una finestra vera e'
            #   piu' grande di quello, e prima di allora non si e' aperta.
            if migliore and area > 10000:
                self.wid = migliore
                return migliore
            if time.time() >= scadenza:
                self.wid = migliore
                return migliore
            time.sleep(0.5)

    def ridimensiona(self, l, a):
        self.x("xdotool", "windowsize", self.wid, str(l), str(a))

    def aspetta_canale(self, secondi=45):
        """⛔⭐ IL CANALE DI COMANDO RISPONDE? — e non si presume, si aspetta.
        `[M]` 22 agosto 2026, `voce` su Firefox 140esr lanciata subito dopo una
        scena che aveva aperto un altro Firefox: la pagina si era annunciata
        (`carichi > 0`) ⛔ ma il primo comando e' scaduto a 20 s, e la scena e'
        morta con un `RuntimeError` che il certificatore ha letto come «il giro
        SANO e' rosso» — cioe' **tre guasti non certificati per una flaky**.
        ⚠ La pagina che si annuncia e il ciclo che chiede comandi sono due cose
          diverse: la prima e' una `fetch` sola, il secondo e' un ciclo che deve
          partire.  ⇒ Si aspetta il SECONDO, con un comando che non fa niente."""
        scadenza = time.time() + secondi
        ultimo = None
        while time.time() < scadenza:
            try:
                d = self.com("1+1", 3)
                if d.get("ok") and d.get("valore") == 2:
                    return True
                ultimo = d.get("valore")
            except Exception as e:
                ultimo = str(e)
            time.sleep(0.5)
        print("    NO  ⛔ il canale di comando non ha risposto in %d s "
              "(ultimo: %s): non e' uno zero, e' un banco che non parla con la "
              "pagina" % (secondi, ultimo), flush=True)
        return False

    def aspetta_pagina(self, secondi=30):
        for _ in range(secondi * 2):
            try:
                with urllib.request.urlopen(self.base + "/b37/stato",
                                            timeout=2) as f:
                    if json.loads(f.read())["carichi"] > 0:
                        return True
            except Exception:
                pass
            time.sleep(0.5)
        return False

    # -- lo schermo, in pixel veri -------------------------------------------
    def fotografa(self, percorso, l, a):
        """⛔ I PIXEL, presi FUORI dal browser: `ffmpeg` legge lo schermo X.
           ⚠ Non `Page.captureScreenshot`, che e' di Chrome e che sveglia la
             conduttura — cioe' cambierebbe la scena che sta misurando."""
        r = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-f", "x11grab",
             "-video_size", "%dx%d" % (l, a), "-i", self.display,
             "-frames:v", "1", "-pix_fmt", "rgb24", "-f", "rawvideo",
             "-y", percorso], capture_output=True, text=True)
        return r.returncode == 0, r.stderr

    def _grezza(self, l, a):
        """⛔⭐ LA FOTOGRAFIA IN MEMORIA, e non e' un dettaglio di comodo.
        `[M]` 22 agosto 2026: un giro intero di questo banco scriveva **1,5 GB**
        di fotogrammi grezzi (1600×1000×3 = 4,8 MB l'uno, 63 calibrazioni nella
        sola scena `numeri`) in `/tmp`, che su questa macchina e' un **tmpfs da
        3,8 GB CONDIVISO con gli altri agenti**.  ⛔ L'ha riempito al 100 % e il
        giro dopo e' morto con «No space left on device» — su un banco altrui
        sarebbe morto senza che nessuno capisse perche'.
        ⇒ I pixel si leggono da una PIPE.  Su disco ci finiscono solo se
          `B37_FOTO=tieni`, e in quel caso la riga di esito porta il percorso;
          altrimenti porta `null`, che vuol dire «non conservata», non «non
          fotografata»."""
        r = subprocess.run(
            ["ffmpeg", "-loglevel", "error", "-f", "x11grab",
             "-video_size", "%dx%d" % (l, a), "-i", self.display,
             "-frames:v", "1", "-pix_fmt", "rgb24", "-f", "rawvideo",
             "pipe:1"], capture_output=True)
        if r.returncode != 0 or len(r.stdout) != l * a * 3:
            raise RuntimeError("ffmpeg: %s (%d byte invece di %d)"
                               % (r.stderr.decode("utf-8", "replace")[:300],
                                  len(r.stdout), l * a * 3))
        return r.stdout

    def mostra(self, l, a, quali="righe"):
        """Mette un fotogramma di prova nella pagina PER LA STRADA DEL PRODOTTO,
           e torna quel che la pagina dice di se' stessa.  ⛔ Alza se il
           fotogramma non e' arrivato al vetro: «non ci e' arrivato» non e' una
           misura riuscita (`CODER.md` §3.10)."""
        if not getattr(self, "_strumenti", False):
            self.val(STRUMENTI)
            self._strumenti = True
        d = json.loads(self.val("__b37_mostra(%d, %d, %r)" % (l, a, quali), 30))
        if not d.get("al_vetro"):
            raise RuntimeError(
                "il fotogramma %dx%d NON e' arrivato al vetro per la strada "
                "«%s» (tela %s, dipinta %s): non e' uno zero, e' un buco"
                % (l, a, d.get("strada"), d.get("buffer"), d.get("dipinta")))
        return d

    def schermo_misura(self):
        for r in self.x("xdpyinfo").stdout.splitlines():
            if "dimensions:" in r:
                l, a = (int(v) for v in r.split()[1].split("x"))
                return l, a
        raise RuntimeError("xdpyinfo non risponde su " + self.display)

    def immagine(self, percorso=None):
        """La fotografia dello schermo X come matrice (a, l, 3).  ⛔ Il file si
           scrive SOLO con `B37_FOTO=tieni` (vedi `_grezza`)."""
        import numpy as np
        l, a = self.schermo_misura()
        grezza = self._grezza(l, a)
        if percorso and TIENI_FOTO:
            with open(percorso, "wb") as f:
                f.write(grezza)
        return np.frombuffer(grezza, dtype=np.uint8).reshape((a, l, 3))

    def percorso_foto(self, percorso):
        """Il percorso da scrivere nella riga di esito: quello vero se la
           fotografia e' stata conservata, `None` se no."""
        return percorso if TIENI_FOTO else None

    # -- ⛔⭐ LA VISTA MISURATA SUI PIXEL, non raccontata dalla pagina ---------
    def calibra(self, percorso, marche=True):
        """Dove sta e quanto e' larga la VISTA, in pixel del dispositivo, letta
           dalla fotografia dello schermo.  ⛔ Torna `None` se la calibrazione
           non e' riuscita: un `None` non e' uno zero (`CODER.md` §3.10)."""
        import numpy as np
        prima = self.js("[document.documentElement.clientWidth,"
                        " document.documentElement.clientHeight]")
        self.val(CAL_METTI)
        time.sleep(0.35)
        try:
            img = self.immagine(percorso)
        finally:
            self.val(CAL_TOGLI)
        dopo = self.js("[document.documentElement.clientWidth,"
                       " document.documentElement.clientHeight]")
        if prima != dopo:
            print("        ⛔ la calibrazione ha CAMBIATO la vista (%s → %s): "
                  "si rifiuta, non e' una misura" % (prima, dopo), flush=True)
            return None
        # ⛔⭐ DUE MASCHERE, E NON E' PIGNOLERIA — 22 agosto 2026, `[M]`.
        #
        #   A `dpr` non intero l'origine della vista puo' cadere a MEZZO pixel
        #   del dispositivo: la striscia copre allora la prima e l'ultima riga
        #   solo a meta', quei pixel escono mescolati col fondo, e la maschera
        #   stretta li perde.  ⇒ `[M]` con `--force-device-scale-factor=1.5`:
        #   `clientHeight × dpr` = 630 e la striscia stretta ne misurava **629**,
        #   e A6 accusava il PRODOTTO di chiedere un pixel di troppo.  ⛔ Era lo
        #   strumento (`CODER.md` §3.11: il sospetto va prima sulla misura).
        #
        #   ⇒ Si misurano DUE estensioni e si tengono tutt'e due:
        #     · `l`/`a`   maschera STRETTA — solo i pixel COPERTI DEL TUTTO:
        #                 e' il limite INFERIORE della vista vera;
        #     · `l_max`/`a_max` maschera PERMISSIVA — anche i pixel mescolati
        #                 col fondo: e' il limite SUPERIORE.
        #   La vista vera sta nell'intervallo, e i verdetti giudicano contro
        #   l'INTERVALLO invece di inventarsi una tolleranza.
        r_, g_, b_ = (img[:, :, 0].astype(np.int16),
                      img[:, :, 1].astype(np.int16),
                      img[:, :, 2].astype(np.int16))
        mag = (r_ > 170) & (g_ < 90) & (b_ > 170)
        cia = (r_ < 90) & (g_ > 170) & (b_ > 170)
        # ⚠ La permissiva chiede che il pixel PENDA verso il colore della
        #   striscia piu' che verso qualunque fondo: bianco puro e nero puro ne
        #   restano fuori (per tutt'e due `R+B−2G` e `G+B−2R` valgono 0).
        mag_p = (r_ >= 60) & (b_ >= 60) & ((r_ + b_ - 2 * g_) > 60)
        cia_p = (g_ >= 60) & (b_ >= 60) & ((g_ + b_ - 2 * r_) > 60)
        if not (mag.any() and cia.any()):
            print("        ⛔ le strisce di calibrazione NON si trovano nella "
                  "fotografia (magenta=%s ciano=%s)" % (bool(mag.any()),
                                                        bool(cia.any())),
                  flush=True)
            return None
        my, mx = np.nonzero(mag)
        cy, cx = np.nonzero(cia)
        myp, mxp = np.nonzero(mag_p)
        cyp, _cxp = np.nonzero(cia_p)
        ox, oy = int(mx.min()), int(my.min())
        ox_p, oy_p = int(mxp.min()), int(myp.min())
        l = int(mx.max()) - ox + 1
        a = int(cy.max()) - oy + 1
        l_max = int(mxp.max()) - ox_p + 1
        a_max = int(cyp.max()) - oy_p + 1
        # ⛔ Le due misure devono distare al massimo 2 px (una mezza riga per
        #    capo).  Se distano di piu' la fotografia ha preso altro, e una
        #    calibrazione che non si capisce NON si restituisce.
        if l_max - l > 2 or a_max - a > 2 or l_max < l or a_max < a:
            print("        ⛔ le due maschere di calibrazione non concordano "
                  "(stretta %dx%d, permissiva %dx%d): RIFIUTATA"
                  % (l, a, l_max, a_max), flush=True)
            return None
        # ⛔ Le due strisce devono cominciare nello STESSO punto: la verticale a
        #    `left:0` e l'orizzontale a `top:0` nascono tutte e due dall'origine
        #    della vista.  Se non combaciano, la fotografia ha preso altro.
        if abs(int(cx.min()) - ox) > 1:
            print("        ⛔ le due strisce non partono dallo stesso x "
                  "(%d contro %d): calibrazione RIFIUTATA"
                  % (int(cx.min()), ox), flush=True)
            return None
        return {"ox": ox, "oy": oy, "l": l, "a": a,
                "l_max": l_max, "a_max": a_max, "cw": prima[0],
                "ch": prima[1], "fotografia": percorso}

    # -- ⛔ IL PALCO ----------------------------------------------------------
    def giudica_palco(self, quadri_minimi=10, resize_battuti=5):
        """Conta i QUADRI e i `resize` VERAMENTE arrivati alla pagina.

        ⛔ Il conto dei quadri si fa con un `requestAnimationFrame` a catena
           dentro la pagina — cioe' con lo stesso meccanismo che il prodotto usa
           in `rinegozia_vista()`.  Un contatore che girasse su `setTimeout`
           direbbe che il palco e' vivo mentre il cammino del prodotto e' morto.
        """
        # ⛔ Prima di qualunque comando: il canale risponde?  (vedi
        #    `aspetta_canale`, e la flaky del 22 agosto 2026 su Firefox)
        if not self.aspetta_canale():
            return False
        self.val("""(function(){
          window.__b37_q = 0; window.__b37_r = 0;
          if (window.__b37_spia) return "gia' accesa";
          window.__b37_spia = true;
          (function giro(){ window.__b37_q++; requestAnimationFrame(giro); })();
          addEventListener("resize", function(){ window.__b37_r++; });
          return "accesa";
        })()""")
        # ⛔ Tre secondi, come la misura del 13 agosto: si confrontano numeri
        #    presi con la stessa finestra di tempo.
        time.sleep(3.0)
        quadri = self.js("window.__b37_q")
        g = self.geometria() or {"l": 1200, "a": 760}
        # ⛔ I passi sono da OTTO pixel del dispositivo, non da uno: a dpr 1,5 o
        #    2 un passo da 1 px non cambia la vista in pixel CSS, il motore non
        #    consegna nessun `resize`, e la spia accusa il palco di essere morto
        #    mentre e' vivo (`[M]` 16 agosto 2026: 4 resize su 6 a dpr 1,5).
        #    ⚠ E' la forma 3.11: quando codice e misura si contraddicono, il
        #    sospetto va prima sulla misura.
        for i in range(resize_battuti):
            self.ridimensiona(g["l"] - 8 * (i + 1), g["a"])
            time.sleep(0.35)
        self.ridimensiona(g["l"], g["a"])
        time.sleep(0.5)
        arrivati = self.js("window.__b37_r")
        vivo = quadri >= quadri_minimi and arrivati >= resize_battuti
        d = {"tipo": "palco", "quadri_in_3s": quadri,
             "resize_battuti": resize_battuti + 1,
             "resize_arrivati": arrivati, "vivo": vivo,
             "visibilita": self.js("document.visibilityState")}
        self.scrivi(d)
        print("    --  PALCO: %d quadri in 3 s · %d resize battuti → %d "
              "arrivati · visibilita' «%s»"
              % (quadri, resize_battuti + 1, arrivati, d["visibilita"]),
              flush=True)
        if vivo:
            print("    OK  il palco REGGE i cammini dietro a un quadro "
                  "(LEZIONI.md §1.15 diceva 0 quadri: qui non si riproduce)",
                  flush=True)
        else:
            print("    NO  ⛔⛔ IL PALCO, NON IL PRODOTTO: %d quadri e %d resize."
                  " Ogni cammino dietro a un quadro qui e' CODICE MORTO, e"
                  " nessun verdetto sul prodotto puo' uscire da questo giro"
                  % (quadri, arrivati), flush=True)
        return vivo
