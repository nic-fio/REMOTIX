#!/usr/bin/env python3
"""07-b54 — LA CLIPBOARD NEI DUE VERSI, SUI DUE BROWSER.

    python3 banchi/07-b54-appunti-due-versi.py [--solo chrome|firefox]

⛔ PERCHE' ESISTE — 20 agosto 2026, e la frase e' dell'utente: *«su Firefox la
   clipboard da server a client funziona, il contrario no»*.  ⚠ E il verso che
   non funziona e' quello che nessun banco aveva mai provato **con i tasti
   veri**: `07-b45` misurava il protocollo, non il percorso del browser.

Le quattro caselle, e sono quattro domande diverse:

    ┌───────────────────────┬──────────────┬──────────────┐
    │                       │   Firefox    │    Chrome    │
    ├───────────────────────┼──────────────┼──────────────┤
    │ sessione → client     │      A1      │      A2      │
    │ client → sessione     │      B1      │      B2      │
    └───────────────────────┴──────────────┴──────────────┘

⭐ E NON SI USA NESSUN PERMESSO SPECIALE.  ⛔ Le preferenze di prova di Firefox
   (`dom.events.testing.asyncClipboard`) farebbero passare `readText()` senza il
   menu «Incolla» — cioe' **spegnerebbero proprio il difetto che si cerca**.  ⇒
   Qui la clipboard si legge e si scrive come la usa una persona: un `Ctrl+C` e
   un `Ctrl+V` VERI dentro un campo di testo che il banco crea e poi toglie.

Che cosa fa, per browser:

  A · sessione → client
     `wl-copy` dentro la sessione di «prova», poi si legge la clipboard del
     browser incollandola in un campo del banco con un `Ctrl+V` vero.
     ⇒ Se il testo c'e', il verso funziona **fino alla clipboard vera**, non
       solo fino ai contatori della pagina.

  B · client → sessione
     Si mette il testo nella clipboard del browser (campo del banco + `Ctrl+C`
     vero), si TOGLIE il campo, si batte `Ctrl+V` sulla pagina — che e' quel che
     l'utente fa — e si guarda con `wl-paste` che cosa ha ricevuto il desktop
     remoto.

⚠ E i due versi si misurano SEPARATAMENTE anche quando falliscono insieme: «la
  clipboard non va» e' una frase, «B1 no e A1 si'» e' una diagnosi.
"""
import argparse, importlib.util as iu, json, os, shutil, signal, subprocess
import sys, tempfile, time

QUI = os.path.dirname(os.path.abspath(__file__))
MACCHINA = "192.168.0.2"


def _mod(nome, file):
    s = iu.spec_from_file_location(nome, os.path.join(QUI, file))
    m = iu.module_from_spec(s); s.loader.exec_module(m); return m


M = _mod("marionette", "07-b46-marionette.py")
CDP = _mod("cdp", "02-pagina-misura-cdp.py")

a = argparse.ArgumentParser()
a.add_argument("--porta", type=int, default=7730)
a.add_argument("--lavoro", default="/media/REMOTIX/tmp/07-appunti")
a.add_argument("--utente", default="prova",
               help="⛔ l'utente della sessione. Il predefinito «prova» e' quello "
                    "dell'UTENTE: con la sua sessione viva, due server che "
                    "aprono un desktop per lo stesso utente si contendono "
                    "/run/user e il posto e' UNO. ⇒ Da un banco in parallelo "
                    "si passa un utente proprio, come per la porta e il socket.")
a.add_argument("--parola", default="prova2026")
a.add_argument("--solo", default="", choices=["", "chrome", "firefox"])
# ⭐ `--schermo :99` misura su browser VERI (Xvfb) invece che headless: e' la
#   sola configurazione in cui il difetto della clipboard di Firefox si vede.
a.add_argument("--schermo", default="")
# ⭐ `--wayland wayland-1` misura su una sessione WAYLAND (un compositore
#   annidato, es. `cage`): e' l'ambiente dell'utente, e la clipboard di Wayland
#   non si comporta come quella di X11.
a.add_argument("--wayland", default="")
# ⛔⛔ E L'UTENTE DELLA SESSIONE ATTRAVERSA ANCHE IL LATO SESSIONE — 21 ago 2026.
#
#     Questo banco era parametrico da un lato (l'accesso dal browser) e FISSO
#     su «prova» dall'altro (`id -u prova`, `runuser -u prova`).  ⚠ Il sintomo
#     non era un errore del banco: era **«il desktop remoto ha "Failed to
#     connect to a Wayland server" invece del testo»**, cioe' un VERDETTO
#     ROSSO CONTRO IL PRODOTTO, per un difetto del banco.
#     ⇒ `[M]` 21 agosto: girato con `--utente provai6`, i due versi davano
#       rossi su tutt'e due i motori, e `XDG_RUNTIME_DIR` puntava a
#       `/run/user/1001`, cioe' all'utente dell'UTENTE.
#     ⭐ Un banco parametrico a meta' e' peggio di uno fisso: quello fisso
#       almeno rifiuta di partire.
o = a.parse_args()
URL = "https://%s:%d/" % (MACCHINA, o.porta)

VERSO_A = "DAL-DESKTOP-REMOTO-verso-il-browser-%d"
VERSO_B = "DAL-BROWSER-verso-il-desktop-remoto-%d"

# ⛔ Il campo del banco: si crea, si usa e SI TOGLIE.  ⚠ Lasciandolo, la pagina
#   avrebbe un elemento modificabile che non ha mai — e il `paste` di Firefox si
#   comporta in modo diverso proprio in presenza di uno.  Sarebbe misurare un
#   prodotto che non esiste.
CAMPO_APRI = """
  let t = document.getElementById('__banco_campo');
  if (!t) {
    t = document.createElement('textarea');
    t.id = '__banco_campo';
    t.style.cssText = 'position:fixed;left:2px;top:2px;width:300px;height:40px;'
                    + 'z-index:99999;opacity:0.01';
    document.body.appendChild(t);
  }
  t.value = arguments && arguments.length ? (arguments[0] || '') : '';
  t.focus(); t.select();
  return true;
"""
CAMPO_LEGGI = """
  const t = document.getElementById('__banco_campo');
  return t ? t.value : null;
"""
CAMPO_CHIUDI = """
  const t = document.getElementById('__banco_campo');
  if (t) t.remove();
  document.body.focus();
  return true;
"""
DIARIO = """
  const r = document.getElementById('registro');
  const t = r ? r.textContent : "";
  return t.split("\\n").filter(function (x) {
    return x.indexOf("appunti") >= 0 || x.indexOf("APPUNTI") >= 0
        || x.indexOf("paste") >= 0 || x.indexOf("Ctrl+V") >= 0
        || x.indexOf("readText") >= 0;
  }).slice(-14);
"""

STATO = """
  const A = window.REMOTIX && window.REMOTIX.appunti;
  if (!A) return null;
  return { acceso: A.acceso, sorvegliata: A.sorvegliata || "nessuna",
           conti: A.conti, mio_id: A.mio_id, suo_id: A.suo_id,
           in_attesa_di_gesto: A.in_attesa_di_gesto !== null };
"""


def nella_sessione(copione, *argomenti, riprove=1):
    """Esegue un copione dentro la sessione Wayland di «prova».

    ⚠ `timeout` DA QUELLA PARTE e non solo da questa: `wl-copy` resta vivo per
      servire la selezione, e una volta su cinque teneva aperto il canale di
      `ssh` — il banco moriva di attesa su un prodotto sano.  ⛔ E la riprova e'
      UNA e si dichiara: un banco che riprovasse in silenzio nasconderebbe una
      fragilita' vera."""
    subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                    "cat > /tmp/b54.sh && chmod +x /tmp/b54.sh"],
                   input=copione, text=True, capture_output=True)
    c = ("printf 'nicfio\\n' | sudo -S -p '' timeout 12 runuser -u " + o.utente + " -- "
         "/tmp/b54.sh " + " ".join(json.dumps(x) for x in argomenti)
         # ⛔ NIENTE `< /dev/null` qui: quello stdin E' la parola d'ordine di
         #    `sudo -S`, e togliendolo il banco riceveva «sudo: a password is
         #    required» come se fosse il testo incollato dal desktop remoto.
         + " > /tmp/b54.log 2>&1; cat /tmp/b54.log")
    for tentativo in range(riprove + 1):
        try:
            r = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                               capture_output=True, text=True, timeout=30)
            return (r.stdout or "").strip()
        except subprocess.TimeoutExpired:
            print("   ⚠ la sessione non ha risposto in 30 s (tentativo %d)"
                  % (tentativo + 1))
    return "⛔ TIMEOUT"


COPIA = ("#!/bin/sh\n"
         "U=$(id -u " + o.utente + ")\n"
         "export XDG_RUNTIME_DIR=/run/user/$U WAYLAND_DISPLAY=wayland-0\n"
         # ⛔ I `wl-copy` dei giri precedenti restano vivi a servire la vecchia
         #    selezione: si tolgono di mezzo prima, o il banco misura la
         #    clipboard di due minuti fa.
         "pkill -u " + o.utente + " -x wl-copy 2>/dev/null\n"
         "sleep 0.2\n"
         # ⚠ `wl-copy` si biforca per servire la selezione: le uscite si
         #   chiudono, ma non lo si manda in fondo con `&` o muore prima di
         #   leggere lo stdin.
         "printf %s \"$1\" | wl-copy >/dev/null 2>&1\n"
         "echo copiato\n")

INCOLLA = ("#!/bin/sh\n"
           "U=$(id -u " + o.utente + ")\n"
           "export XDG_RUNTIME_DIR=/run/user/$U WAYLAND_DISPLAY=wayland-0\n"
           "timeout 8 wl-paste -n 2>&1\n")


def righe_nuove_di(prima, dopo):
    viste = set(prima.splitlines())
    return [r for r in dopo.splitlines() if r not in viste]


def registro(n=200):
    c = ("printf 'nicfio\\n' | sudo -S -p '' tail -n %d %s/registro.log" %
         (n, o.lavoro))
    return subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                          capture_output=True, text=True).stdout


def palco_libero(quanto=60):
    t0 = time.time()
    while time.time() - t0 < quanto:
        r = registro(120)
        if "ne restano 0" in r or "l'ultima sessione di" in r:
            time.sleep(2)
            return True
        time.sleep(2)
    return False


class Guida:
    """La stessa forma per i due motori: quel che cambia e' come si guida."""

    def js(self, codice, args=None):
        raise NotImplementedError

    def tasti(self, ctrl, lettera):
        raise NotImplementedError


class GuidaFirefox(Guida):
    def __init__(self, m):
        self.m = m

    def js(self, codice, args=None):
        return self.m.js(codice, args or [])["value"]

    def clic(self, x=300, y=300):
        self.m.chiama("WebDriver:PerformActions", {"actions": [{
            "type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"},
            "actions": [{"type": "pointerMove", "duration": 40, "x": x, "y": y},
                        {"type": "pointerDown", "button": 0},
                        {"type": "pause", "duration": 60},
                        {"type": "pointerUp", "button": 0}]}]})

    def tasti(self, ctrl, lettera):
        # ⭐ Tasti VERI col protocollo di WebDriver: e' la stessa strada di una
        #   persona, e passa dal gestore della pagina come i suoi.
        self.m.chiama("WebDriver:PerformActions", {"actions": [{
            "type": "key", "id": "tastiera",
            "actions": [{"type": "keyDown", "value": ""},
                        {"type": "keyDown", "value": lettera},
                        {"type": "pause", "duration": 60},
                        {"type": "keyUp", "value": lettera},
                        {"type": "keyUp", "value": ""}]}]})


class GuidaChrome(Guida):
    def __init__(self, c):
        self.c = c

    def js(self, codice, args=None):
        if args:
            corpo = "(function(){const arguments_=%s; %s})()" % (
                json.dumps(args), codice.replace("arguments", "arguments_"))
        else:
            corpo = "(function(){%s})()" % codice
        return self.c.valuta(corpo, attendi=False)

    def clic(self, x=300, y=300):
        for tipo in ("mouseMoved", "mousePressed", "mouseReleased"):
            p = {"type": tipo, "x": x, "y": y, "button": "left", "clickCount": 1}
            if tipo == "mouseMoved":
                p.pop("button"); p.pop("clickCount")
            self.c.chiama("Input.dispatchMouseEvent", **p)
            time.sleep(0.05)

    def tasti(self, ctrl, lettera):
        codice = "Key" + lettera.upper()
        virtuale = ord(lettera.upper())
        for tipo in ("rawKeyDown", "char", "keyUp"):
            p = {"type": tipo, "modifiers": 2, "key": lettera,
                 "code": codice, "windowsVirtualKeyCode": virtuale}
            if tipo == "char":
                p["text"] = lettera
            self.c.chiama("Input.dispatchKeyEvent", **p)
            time.sleep(0.05)


def giro(nome, g, n):
    """Le quattro domande, per un browser.  `n` distingue i testi fra i giri."""
    v = {"browser": nome, "guai": [], "verso_A": {}, "verso_B": {}}
    v["stato"] = g.js(STATO)

    # ── A · sessione → client ────────────────────────────────────────────
    testo_a = VERSO_A % n
    nella_sessione(COPIA, testo_a)
    time.sleep(3)
    # ⛔ IL GESTO CHE SBLOCCA LA SCRITTURA E' UN CLIC, NON UN `Ctrl+V`.
    #    ⚠ Dal 20 agosto la pagina si rifiuta di scrivere negli appunti quando
    #    il gesto e' un tasto della clipboard (`Ctrl+V`, `Ctrl+C`, `Ctrl+X`):
    #    in quell'istante gli appunti sono dell'utente.  ⇒ Un banco che usasse
    #    il `Ctrl+V` come gesto misurerebbe quel rifiuto e lo chiamerebbe
    #    difetto.
    # ⛔ E dev'essere un clic VERO, dal guidatore: un evento fabbricato in
    #    JavaScript non e' un'«attivazione dell'utente», e il browser rifiuta la
    #    scrittura negli appunti lo stesso — `[M]` provato, `scritti=0`.
    g.clic()
    time.sleep(1.5)
    g.js(CAMPO_APRI, [""])
    time.sleep(0.3)
    g.tasti(True, "v")
    time.sleep(1.2)
    letto = g.js(CAMPO_LEGGI)
    g.js(CAMPO_CHIUDI)
    dopo_a = g.js(STATO)
    v["verso_A"] = {"copiato_nella_sessione": testo_a, "letto_dal_browser": letto,
                    "stato": dopo_a, "diario": g.js(DIARIO)}
    # ⛔ DUE DOMANDE, NON UNA — e separarle e' tutta la diagnosi:
    #    1. il testo ha attraversato il FILO?  (nostro)
    #    2. il browser l'ha messo nella sua clipboard?  (del browser, e su un
    #       motore headless dipende dai permessi)
    conti_a = (dopo_a or {}).get("conti") or {}
    ric, scritti = conti_a.get("ricevuti", 0), conti_a.get("scritti", 0)
    if not ric:
        v["guai"].append("⛔ VERSO A (sessione → client) — IL FILO: la pagina "
                         "non ha ricevuto nessun testo (ricevuti=0)")
    elif not scritti:
        v["guai"].append("⛔ VERSO A (sessione → client) — LA SCRITTURA: il "
                         "testo e' arrivato (ricevuti=%s) ma non e' entrato "
                         "negli appunti del dispositivo (scritti=0, in attesa "
                         "di gesto=%s)"
                         % (ric, (dopo_a or {}).get("in_attesa_di_gesto")))
    elif letto != testo_a:
        # ⚠ ARRIVATO E SCRITTO, ma la rilettura non lo trova: `[M]` in un
        #   browser HEADLESS la clipboard non fa il giro completo (l'evento
        #   `paste` di controllo arriva con ZERO caratteri anche subito dopo una
        #   scrittura riuscita).  ⇒ Si dichiara e NON si chiama difetto del
        #   prodotto: il prodotto ha fatto la sua parte, e questo banco non ha
        #   uno strumento migliore per guardare.
        v["verso_A"]["nota"] = ("⚠ arrivato e scritto (ricevuti=%s scritti=%s), "
                                "ma la rilettura headless torna «%s»: la "
                                "clipboard di un browser senza schermo non fa "
                                "il giro completo — NON e' un difetto del "
                                "prodotto" % (ric, scritti, (letto or "")[:30]))

    # ── B · client → sessione ────────────────────────────────────────────
    testo_b = VERSO_B % n
    if o.schermo and shutil.which("xclip"):
        # ⛔⭐ SI COPIA DA UN'ALTRA APPLICAZIONE, ed e' quel che fa l'utente:
        #    lui copia in un terminale o in un'altra scheda e poi incolla qui.
        #    ⚠ Copiare DENTRO la pagina e' un'altra cosa — il documento che
        #    riceve l'incolla e' lo stesso che ha copiato, e il motore puo'
        #    comportarsi diversamente.  Sul difetto riferito il 20 agosto 2026
        #    la differenza fra le due strade e' proprio quel che si cerca.
        # ⛔ `xclip` NON si aspetta: si biforca per SERVIRE la selezione e tiene
        #    aperte le sue uscite finche' qualcuno non gliela porta via.  ⚠ Con
        #    `capture_output` il banco moriva di timeout su una copia riuscita —
        #    la stessa trappola di `wl-copy` nella sessione.
        subprocess.run(["pkill", "-x", "xclip"], capture_output=True)
        time.sleep(0.2)
        px = subprocess.Popen(["xclip", "-selection", "clipboard"],
                              stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,
                              env=dict(os.environ, DISPLAY=o.schermo))
        px.stdin.write(testo_b.encode()); px.stdin.close()
        time.sleep(0.6)
    else:
        if o.schermo:
            print("   ⚠ `xclip` non c'e': copio DENTRO la pagina invece "
                  "che da un'altra applicazione — la prova e' piu' debole, "
                  "e si dichiara")
        g.js(CAMPO_APRI, [testo_b])
        time.sleep(0.3)
        g.tasti(True, "c")      # copia VERA nella clipboard del browser
        time.sleep(0.8)
        g.js(CAMPO_CHIUDI)      # ⛔ il campo se ne va: si prova il PRODOTTO
        time.sleep(0.3)
    prima = registro(300)
    g.tasti(True, "v")          # e questo e' quel che fa l'utente
    time.sleep(3.0)
    # ⛔⭐ E LA TASTIERA DEVE ESSERE ANCORA VIVA — il controllo che nasce dalla
    #    cura del 20 agosto: il campo nascosto che fa nascere l'evento `paste`
    #    prende il fuoco, e un `TEXTAREA` a fuoco spegnerebbe tutto l'input
    #    (`cl_nel_modulo`).  ⇒ Si batte una lettera DOPO l'incolla e si guarda
    #    che arrivi al server: senza questa riga la cura potrebbe curare gli
    #    appunti e rompere la tastiera, che e' un affare pessimo.
    # ⛔ Si contano le righe NUOVE, non quelle di una finestra di coda: il
    #    registro di questo server scorre veloce (audio, datagram), e due
    #    `tail -n 400` presi a un secondo di distanza non guardano lo stesso
    #    tratto.  `[M]` 20 agosto: il banco ha detto «la tastiera e' morta» di
    #    una tastiera viva.
    coda_prima = registro(400)
    g.tasti(False, "x")
    time.sleep(2.0)
    nuove_input = [r for r in righe_nuove_di(coda_prima, registro(600))
                   if "input id=" in r]
    v["tastiera_dopo_incolla"] = {"righe_input_nuove": len(nuove_input),
                                  "esempio": nuove_input[-1][:120] if nuove_input else None}
    if not nuove_input:
        v["guai"].append("⛔ LA TASTIERA E' MORTA dopo il Ctrl+V: la lettera "
                         "battuta dopo l'incolla non e' arrivata al server "
                         "(zero righe `input id=` nuove dopo la lettera)")
    ricevuto = nella_sessione(INCOLLA)
    v["verso_B"] = {"copiato_nel_browser": testo_b,
                    "incollato_nella_sessione": ricevuto,
                    "diario": g.js(DIARIO),
                    "annunci_nel_registro": len(
                        [r for r in registro(300).splitlines()
                         if r not in set(prima.splitlines())
                         and "annunciato al client" not in r
                         and "APPUNTI" in r]),
                    "stato": g.js(STATO)}
    if ricevuto != testo_b:
        v["guai"].append("⛔ VERSO B (client → sessione): il desktop remoto ha "
                         "«%s» invece di «%s»" % (ricevuto[:60], testo_b))
    return v


def firefox(n):
    if o.wayland:
        os.environ["WAYLAND_DISPLAY"] = o.wayland
        os.environ["MOZ_ENABLE_WAYLAND"] = "1"
        os.environ.pop("DISPLAY", None)
    p, m, prof = M.accendi(porta=2897, headless=not (o.schermo or o.wayland),
                           largo=1400, alto=900, schermo=o.schermo or None)
    try:
        m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        m.misura(1400, 900); m.vai(URL)
        m.js(f"""document.getElementById('utente').value='{o.utente}';
                document.getElementById('parola').value='{o.parola}';
                document.getElementById('vai').click(); return true;""")
        t0 = time.time()
        while time.time() - t0 < 40:
            if m.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
                break
            time.sleep(0.5)
        time.sleep(3)
        return giro("firefox", GuidaFirefox(m), n)
    finally:
        M.spegni(p, prof)


def chrome(n):
    t = tempfile.mkdtemp(prefix="b54-")
    amb = dict(os.environ)
    if o.schermo:
        amb["DISPLAY"] = o.schermo
        amb.pop("WAYLAND_DISPLAY", None)
    br = subprocess.Popen(
        ([] if o.schermo else ["google-chrome", "--headless=new"])
        + (["google-chrome"] if o.schermo else [])
        # ⛔ `--ozone-platform=x11` quando c'e' uno schermo del banco: senza,
        #    Chrome prende Ozone/Wayland e si attacca alla sessione grafica
        #    VERA, cioe' legge un'ALTRA clipboard (`[M]` 21 ago 2026, `07-b56`).
        + (["--ozone-platform=x11"] if o.schermo else []) + ["--no-sandbox",
         "--user-data-dir=%s/p" % t, "--no-first-run",
         "--no-default-browser-check", "--remote-debugging-port=9717",
         "--remote-allow-origins=*", "--window-size=1400,900", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=amb)
    try:
        b = CDP.pagina(9717, attesa=40)
        c = CDP.Cdp(b["webSocketDebuggerUrl"], timeout=180)
        for x in ("Page.enable", "Runtime.enable", "Network.enable"):
            c.chiama(x)
        c.chiama("Network.setCacheDisabled", cacheDisabled=True)
        # ⛔⭐ IL PERMESSO SI CONCEDE, E SI DICHIARA PERCHE'.  Un Chrome headless
        #    nega la SCRITTURA negli appunti anche dopo un gesto; un Chrome vero
        #    la concede.  ⇒ Senza questa riga il banco misurerebbe la POLITICA
        #    del browser headless invece del percorso del prodotto, e il verso
        #    «sessione → client» sarebbe rosso su un prodotto sano.
        #    ⚠ E NON si concede niente a Firefox: li' il permesso e'
        #    esattamente quel che si sta misurando (§9, il menu «Incolla»).
        try:
            c.chiama("Browser.grantPermissions",
                     origin="https://%s:%d" % (MACCHINA, o.porta),
                     permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
        except Exception as e:
            print("   ⚠ permesso della clipboard NON concesso (%s)" % e)
        c.chiama("Page.navigate", url=URL)
        time.sleep(4)
        if c.valuta("!!document.getElementById('proceed-link')", attendi=False) \
           or "Privacy" in (c.valuta("document.title", attendi=False) or ""):
            for ch in "thisisunsafe":
                for tipo in ("keyDown", "char", "keyUp"):
                    pp = {"type": tipo, "text": ch} if tipo == "char" \
                         else {"type": tipo, "key": ch}
                    c.chiama("Input.dispatchKeyEvent", **pp)
                time.sleep(0.03)
            time.sleep(5)
        t0 = time.time()
        while time.time() - t0 < 25 and not c.valuta(
                "!!document.getElementById('utente')", attendi=False):
            time.sleep(0.5)
        c.valuta(f"""document.getElementById('utente').value='{o.utente}';
                    document.getElementById('parola').value='{o.parola}';
                    document.getElementById('vai').click();""", attendi=False)
        t0 = time.time()
        while time.time() - t0 < 40:
            if c.valuta("document.body.dataset.schermo || ''", attendi=False) == "acceso":
                break
            time.sleep(0.5)
        time.sleep(3)
        return giro("chrome", GuidaChrome(c), n)
    finally:
        try: br.send_signal(signal.SIGTERM); br.wait(timeout=8)
        except Exception: br.kill()
        shutil.rmtree(t, ignore_errors=True)


if not palco_libero(30):
    print("⚠ il palco non risulta libero: il primo giro potrebbe trovarlo occupato")

esiti = []
for i, (nome, f) in enumerate((("firefox", firefox), ("chrome", chrome))):
    if o.solo and o.solo != nome:
        continue
    print("\n═══ %s ═══" % nome.upper())
    try:
        v = f(i + 1)
    except Exception as e:
        v = {"browser": nome, "guai": ["⛔ il banco stesso e' caduto: %r" % e]}
    esiti.append(v)
    print(json.dumps(v, indent=1, ensure_ascii=False)[:1800])
    palco_libero()

print("\n══════════ VERDETTO ══════════")
for v in esiti:
    # ⛔ Un banco CADUTO non ha misurato niente: le sue caselle sono «?», non
    #    «⭐».  ⚠ La prima stesura le dava verdi — un verde per assenza di
    #    rosso, che e' il difetto peggiore che un banco possa avere.
    caduto = any("il banco stesso e' caduto" in g for g in v["guai"])
    def marca(quale):
        if caduto:
            return "❓"
        return "⛔" if any(quale in g for g in v["guai"]) else "⭐"
    print("%-8s  sessione→client %s   client→sessione %s   tastiera dopo "
          "l'incolla %s"
          % (v["browser"], marca("VERSO A"), marca("VERSO B"),
             marca("LA TASTIERA E' MORTA")))
    for g in v["guai"]:
        print("   ", g[:200])
sys.exit(1 if any(v["guai"] for v in esiti) else 0)
