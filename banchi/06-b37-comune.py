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
import json
import subprocess
import time
import urllib.request


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

    def trova_finestra(self):
        r = self.x("xdotool", "search", "--onlyvisible", "--pid", self.pidbr)
        migliore, area = None, -1
        for w in r.stdout.split():
            g = self.geometria(w)
            if g and g["l"] * g["a"] > area:
                migliore, area = w, g["l"] * g["a"]
        self.wid = migliore
        return migliore

    def ridimensiona(self, l, a):
        self.x("xdotool", "windowsize", self.wid, str(l), str(a))

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

    # -- ⛔ IL PALCO ----------------------------------------------------------
    def giudica_palco(self, quadri_minimi=10, resize_battuti=5):
        """Conta i QUADRI e i `resize` VERAMENTE arrivati alla pagina.

        ⛔ Il conto dei quadri si fa con un `requestAnimationFrame` a catena
           dentro la pagina — cioe' con lo stesso meccanismo che il prodotto usa
           in `rinegozia_vista()`.  Un contatore che girasse su `setTimeout`
           direbbe che il palco e' vivo mentre il cammino del prodotto e' morto.
        """
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
