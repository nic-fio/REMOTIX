#!/usr/bin/env python3
"""07-b56 — L'INCOLLA FATTO COL MOUSE, non col `Ctrl+V`.

    python3 banchi/07-b56-incolla-col-mouse.py [--solo chrome|firefox]

⛔ PERCHE' ESISTE — 21 agosto 2026, e la frase e' dell'utente, che aveva appena
   verificato la cura del giorno prima: *«funziona l'incolla con ctrl+v, ma non
   con il mouse e scegliendo dal menu la voce "incolla"»*.

⚠ E i quattro banchi verdi di ieri non potevano prenderlo, perche' tutti e
  quattro **battevano `Ctrl+V` sulla pagina**.  ⇒ Misuravano l'unica strada che
  gia' funzionava.

LA DIFFERENZA, ed e' tutta qui:

  `Ctrl+V` sulla pagina        l'utente tocca IL BROWSER.  Nasce l'evento
                               `paste`, la pagina legge gratis, annuncia, il
                               server chiede, il testo passa.

  tasto destro → «Incolla»     l'utente tocca IL DESKTOP REMOTO.  Sul browser
  dentro il desktop remoto     **non succede niente**: quel menu e' dipinto nel
                               video, e la voce «Incolla» la esegue
                               un'applicazione che sta dall'altra parte del
                               filo.  ⇒ L'unica notizia che arriva alla pagina
                               e' l'`APPUNTI_CHIEDI` del server.

⭐ E DAL FILO IN GIU' I DUE CASI SONO LO STESSO: un programma nella sessione
   chiede la selezione.  ⇒ Il banco lo riproduce con `wl-paste`, che e'
   esattamente quel che fa la voce «Incolla» di GTK — senza doversi inventare
   un menu da cliccare dentro un video.

LE DUE DOMANDE, e sono separate:

  C1 · la pagina viene INTERPELLATA?   Prima della cura no: il server mette la
       richiesta in coda («la domanda ASPETTA l'annuncio») e la chiude a mani
       vuote dopo quattro secondi, perche' un client che non ha mai annunciato
       niente non si puo' chiedere.  Si guarda nel registro.

  C2 · il testo ARRIVA?                E dev'essere quello copiato ADESSO, non
       quello di un `Ctrl+V` di prima: il banco copia un testo nuovo e non
       batte MAI `Ctrl+V`.

⛔ IL PREZZO DI FIREFOX SI PAGA DAVANTI AL BANCO, NON SI SPEGNE.
   `dom.events.testing.asyncClipboard` farebbe passare `readText()` senza il
   bottoncino «Incolla»: sarebbe spegnere proprio la cosa che l'utente
   incontrera'.  ⇒ Qui il bottoncino si CERCA e si CLICCA nel contesto chrome,
   com'e' fatto di clic il gesto di una persona — e il banco riferisce **quante
   volte e' comparso**, che e' il numero che interessa all'utente.
"""
import argparse, importlib.util as iu, json, os, shutil, subprocess
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
a.add_argument("--solo", default="", choices=["", "chrome", "firefox"])
a.add_argument("--schermo", default=":96")
a.add_argument("--giri", type=int, default=2,
               help="quante incollate col mouse di seguito: il secondo giro "
                    "dice se il bottoncino di Firefox torna OGNI VOLTA")
o = a.parse_args()
URL = "https://%s:%d/" % (MACCHINA, o.porta)

TESTO = "COL-MOUSE-dal-browser-al-desktop-%d-%d"

DIARIO = """
  const r = document.getElementById('registro');
  const t = r ? r.textContent : "";
  return t.split("\\n").filter(function (x) {
    return x.indexOf("appunti") >= 0 || x.indexOf("APPUNTI") >= 0
        || x.indexOf("rilettura") >= 0 || x.indexOf("readText") >= 0
        || x.indexOf("ANNUNCIATO") >= 0;
  }).slice(-12);
"""

STATO = """
  const A = window.REMOTIX && window.REMOTIX.appunti;
  if (!A) return null;
  return { acceso: A.acceso, sorvegliata: A.sorvegliata || "nessuna",
           conti: A.conti, mio_id: A.mio_id, mio_testo: A.mio_testo };
"""


def ssh(comando, timeout=40):
    return subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                          capture_output=True, text=True,
                          timeout=timeout).stdout


def registro(n=300):
    return ssh("printf 'nicfio\\n' | sudo -S -p '' tail -n %d %s/registro.log"
               % (n, o.lavoro))


def righe_nuove_di(prima, dopo):
    viste = set(prima.splitlines())
    return [r for r in dopo.splitlines() if r not in viste]


# ⛔⛔⭐ IL COPIONE DICE «PRONTO» E POI ASPETTA — e senza questo il banco
#      misurava se' stesso.
#
# ⚠ Fra il clic sulla pagina e l'`APPUNTI_CHIEDI` che ne nasce, in una sessione
#   vera passano MILLISECONDI: il menu remoto e' li' e l'applicazione chiede la
#   selezione appena l'utente sceglie «Incolla».  ⛔ Nel banco, in mezzo, ci
#   sono `ssh`, `sudo` e `runuser`: `[M]` secondi interi.  E l'attivazione
#   transitoria di un clic dura cinque secondi.
#   ⇒ Il primo giro ha detto «lack of user activation» — che non e' un difetto
#     del prodotto: e' il banco che clicca troppo presto.
#
# ⭐ Allora il copione si annuncia e ASPETTA: il banco sente «PRONTO», clicca, e
#   `wl-paste` parte un secondo e mezzo dopo.  Cosi' l'ordine dei fatti e'
#   quello vero, e la misura riguarda il prodotto.
INCOLLA = ("#!/bin/sh\n"
           "U=$(id -u prova)\n"
           "export XDG_RUNTIME_DIR=/run/user/$U WAYLAND_DISPLAY=wayland-0\n"
           "echo PRONTO\n"
           "sleep 1.5\n"
           "timeout 8 wl-paste -n 2>&1\n")


# ⛔⛔⭐ E LA DOMANDA CHE VIENE PRIMA DI TUTTE: chi si collega perde quel che
#      aveva copiato nel desktop?  `[M]` 21 agosto 2026: SI', e la colpa era
#      dell'annuncio d'apertura da zero byte — prendeva la selezione al
#      compositore con le mani vuote.  ⇒ In una sessione locale la clipboard non
#      sparisce perche' e' entrato qualcuno, e qui non deve sparire nemmeno.
TESTO_SESSIONE = "TESTO-CHE-ERA-GIA-NEL-DESKTOP-%d"

COPIA_SESSIONE = ("#!/bin/sh\n"
                  "U=$(id -u prova)\n"
                  "export XDG_RUNTIME_DIR=/run/user/$U WAYLAND_DISPLAY=wayland-0\n"
                  "pkill -u prova -x wl-copy 2>/dev/null\n"
                  "sleep 0.2\n"
                  # ⛔⛔ `setsid`, E NON E' UN VEZZO: `wl-copy` resta vivo per
                  #     SERVIRE la selezione, e il `timeout 12` che avvolge
                  #     questo copione lo ammazzerebbe insieme a tutto il gruppo
                  #     — portandosi via la clipboard del desktop.  `[M]` 21
                  #     agosto 2026: il banco ha dichiarato «collegandosi si e'
                  #     persa la clipboard» di una clipboard uccisa da lui.
                  "printf %s \"$1\" | setsid wl-copy >/dev/null 2>&1\n"
                  "sleep 0.5\n"
                  # ⛔ E SI VERIFICA CHE LA COPIA SIA ANDATA: un banco che
                  #    prepara la scena senza guardarla misura un'altra scena.
                  #    `[M]` 21 ago 2026: il banco credeva di aver copiato e
                  #    nella sessione c'era ancora il testo di due prove prima.
                  "timeout 5 wl-paste -n 2>&1\n")


def copia_nella_sessione(testo, riprove=3):
    """⚠ E SI RIPROVA, dichiarandolo: `[M]` 21 agosto 2026 `wl-copy` ha
    risposto «This seat has no keyboard» — succede quando nella sessione non
    c'e' nessun client attaccato e il posto e' senza tastiera virtuale.  ⛔ Non
    e' un difetto del prodotto ed e' la scena del banco che non si prepara: se
    non si riprova, il banco dichiara rosso un prodotto che non ha nemmeno
    misurato."""
    for i in range(riprove):
        visto = _copia_una_volta(testo)
        if visto == testo:
            return visto
        print("   ⚠ la sessione non ha preso la copia (%s): riprovo (%d/%d)"
              % (visto[:40], i + 1, riprove))
        time.sleep(2)
    return visto


def _copia_una_volta(testo):
    subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                    "cat > /tmp/b56c.sh && chmod +x /tmp/b56c.sh"],
                   input=COPIA_SESSIONE, text=True, capture_output=True)
    c = ("printf 'nicfio\\n' | sudo -S -p '' timeout 12 runuser -u prova -- "
         "/tmp/b56c.sh " + json.dumps(testo)
         + " > /tmp/b56c.log 2>&1; cat /tmp/b56c.log")
    return ssh(c, timeout=30).strip()


class Incollatore:
    """`wl-paste` nella sessione, ma con il momento della partenza in mano al
    banco: `aspetta_pronto()` torna quando manca un secondo e mezzo."""

    def __init__(self):
        subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA,
                        "cat > /tmp/b56.sh && chmod +x /tmp/b56.sh"],
                       input=INCOLLA, text=True, capture_output=True)

    def parti(self):
        c = ("printf 'nicfio\\n' | sudo -S -p '' timeout 20 runuser -u prova "
             "-- /tmp/b56.sh")
        self.p = subprocess.Popen(["ssh", "-o", "BatchMode=yes", MACCHINA, c],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True)

    def aspetta_pronto(self, quanto=20):
        t0 = time.time()
        while time.time() - t0 < quanto:
            r = self.p.stdout.readline()
            if not r:
                return False
            if r.strip() == "PRONTO":
                return True
        return False

    def raccogli(self, quanto=30):
        try:
            resto, _ = self.p.communicate(timeout=quanto)
        except subprocess.TimeoutExpired:
            self.p.kill()
            return "⛔ TIMEOUT"
        return (resto or "").strip()


class GuidaFirefox:
    """⛔ E QUESTA GUIDA SA CLICCARE IL BOTTONCINO «Incolla».

    ⚠ Non e' un permesso concesso di nascosto: e' il clic che l'utente fara' con
      la sua mano.  Il pannello sta nel contesto **chrome** di Firefox
      (`clipboardReadPasteMenuPopup`), fuori dal documento — e quindi fuori da
      qualunque `js()` di pagina."""

    def __init__(self, m):
        self.m = m
        self.bottoncini = 0

    def js(self, codice, args=None):
        return self.m.js(codice, args or [])["value"]

    def clic(self, x=400, y=400):
        self.m.chiama("WebDriver:PerformActions", {"actions": [{
            "type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"},
            "actions": [{"type": "pointerMove", "duration": 40, "x": x, "y": y},
                        {"type": "pointerDown", "button": 0},
                        {"type": "pause", "duration": 60},
                        {"type": "pointerUp", "button": 0}]}]})

    def paga_il_bottoncino(self, quanto=4.0):
        """Cerca il pannello «Incolla» e lo clicca.  Torna True se c'era."""
        t0 = time.time()
        visto = False
        while time.time() - t0 < quanto:
            try:
                self.m.chiama("Marionette:SetContext", {"value": "chrome"})
                r = self.m.chiama("WebDriver:ExecuteScript", {
                    "script": """
                      const w = Services.wm.getMostRecentWindow('navigator:browser');
                      if (!w) return 'niente-finestra';
                      const p = w.document.getElementById('clipboardReadPasteMenuPopup');
                      if (!p) return 'niente-pannello';
                      if (p.state !== 'open' && p.state !== 'showing') return p.state;
                      const v = p.querySelector('menuitem');
                      if (!v) return 'aperto-senza-voce';
                      v.doCommand();
                      p.hidePopup();
                      return 'cliccato';
                    """, "args": [], "sandbox": "system"})
                esito = (r or {}).get("value")
            except Exception as e:
                esito = "guasto: %s" % e
            finally:
                try:
                    self.m.chiama("Marionette:SetContext", {"value": "content"})
                except Exception:
                    pass
            if esito == "cliccato":
                self.bottoncini += 1
                visto = True
                break
            time.sleep(0.25)
        return visto


class GuidaChrome:
    def __init__(self, c):
        self.c = c
        self.bottoncini = 0

    def js(self, codice, args=None):
        if args:
            corpo = "(function(){const arguments_=%s; %s})()" % (
                json.dumps(args), codice.replace("arguments", "arguments_"))
        else:
            corpo = "(function(){%s})()" % codice
        return self.c.valuta(corpo, attendi=False)

    def clic(self, x=400, y=400):
        for tipo in ("mouseMoved", "mousePressed", "mouseReleased"):
            p = {"type": tipo, "x": x, "y": y, "button": "left", "clickCount": 1}
            if tipo == "mouseMoved":
                p.pop("button"); p.pop("clickCount")
            self.c.chiama("Input.dispatchMouseEvent", **p)
            time.sleep(0.05)

    def paga_il_bottoncino(self, quanto=4.0):
        return False        # ⭐ su Chrome il permesso si concede una volta sola


def giro(nome, g, n, schermo, testo=None):
    """Una incollata col mouse: si copia FUORI, non si batte mai `Ctrl+V`.

    ⭐ `testo` gia' dato = NON si ricopia niente: e' la seconda incollata dello
       STESSO testo, e serve a rispondere alla domanda che interessa
       all'utente — «il bottoncino di Firefox torna ogni volta?»."""
    v = {"giro": n, "guai": [], "ricopiato": testo is None}
    if testo is None:
        testo = TESTO % (os.getpid() % 1000, n)

    # ⛔⭐ SI COPIA DA UN'ALTRA APPLICAZIONE — e non e' un dettaglio: e' quel che
    #    fa l'utente (copia in un terminale, poi incolla nel desktop remoto).  E
    #    NIENTE `Ctrl+V` sulla pagina, mai: e' l'unica strada che il difetto
    #    lascia scoperta.
    # ⛔ `xclip` NON si aspetta: si biforca per SERVIRE la selezione e tiene
    #    aperte le sue uscite finche' qualcuno non gliela porta via.  ⚠ Con
    #    `capture_output` il banco restava appeso dieci secondi e moriva di
    #    timeout su una copia riuscita — la stessa trappola di `wl-copy` nella
    #    sessione (`07-b54`).  ⇒ Si scrive sullo stdin e si lascia vivo.
    if v["ricopiato"]:
        subprocess.run(["pkill", "-x", "xclip"], capture_output=True)
        time.sleep(0.2)
        px = subprocess.Popen(["xclip", "-selection", "clipboard"],
                              stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,
                              env=dict(os.environ, DISPLAY=schermo))
        px.stdin.write(testo.encode()); px.stdin.close()
        time.sleep(0.8)

    prima = registro(400)
    # ⭐ IL CLIC arriva piu' sotto, un istante prima che il desktop remoto
    #   chieda: da questa parte del filo e' un clic sulla tela come tutti gli
    #   altri, e porta con se' l'attivazione transitoria che `readText()`
    #   pretende.

    tira = Incollatore()
    tira.parti()
    if not tira.aspetta_pronto():
        v["guai"].append("⛔ BANCO: la sessione non ha detto «PRONTO»")
        return v
    # ⭐ ADESSO il clic, e `wl-paste` parte un secondo e mezzo dopo: e' l'ordine
    #   vero — l'utente sceglie «Incolla» dal menu e l'applicazione chiede.
    g.clic()
    # ⚠ Mentre il desktop remoto aspetta, il bottoncino di Firefox e' li' e
    #   qualcuno deve cliccarlo: e' il gesto dell'utente, non un permesso.
    v["bottoncino_comparso"] = g.paga_il_bottoncino(quanto=6.0)
    ricevuto = tira.raccogli()
    dopo = registro(700)
    nuove = righe_nuove_di(prima, dopo)
    v["interpellata"] = any("chiesto al client il trasferimento" in r for r in nuove)
    v["aspettava_l_annuncio"] = any("la domanda ASPETTA" in r for r in nuove)
    v["copiato_nel_browser"] = testo
    v["arrivato_nella_sessione"] = ricevuto
    v["diario"] = g.js(DIARIO)
    v["stato"] = g.js(STATO)

    if not v["interpellata"]:
        v["guai"].append("⛔ C1 — LA PAGINA NON E' STATA NEMMENO INTERPELLATA: "
                         "il server non le ha chiesto niente%s"
                         % (" (la domanda ASPETTA l'annuncio)"
                            if v["aspettava_l_annuncio"] else ""))
    if ricevuto != testo:
        v["guai"].append("⛔ C2 — il desktop remoto ha «%s» invece di «%s»"
                         % (ricevuto[:60], testo))
    return v


def giri_di(nome, g, quanti, era_nel_desktop=None):
    """I giri con testo NUOVO, e poi UNO che ripete lo stesso senza ricopiare."""
    v = []
    if era_nel_desktop:
        # ⛔⛔ E LA CLIPBOARD DEL BROWSER DEV'ESSERE VUOTA, o la domanda e'
        #     un'altra.  ⚠ Se il dispositivo ha del testo suo, il desktop lo
        #     riceve — ed e' GIUSTO: e' quel che vuole chi incolla.  `[M]` 21
        #     agosto 2026: il banco ha gridato «si e' persa la clipboard del
        #     desktop» mentre il prodotto consegnava, correttamente, il testo
        #     che il browser aveva ancora dalla prova precedente.
        # ⇒ «Sopravvive?» si chiede solo quando il dispositivo NON ha niente da
        #   dare: allora il desktop deve ritrovare quel che aveva lui.
        # ⛔⛔ E LA CLIPBOARD DEL BROWSER SI SVUOTA DAVVERO, con un
        #     proprietario che dichiara ZERO byte.  ⚠ Non basta uccidere
        #     `xclip`: la domanda «sopravvive?» ha senso solo se il dispositivo
        #     NON ha niente da dare — se ha del testo suo il desktop riceve
        #     QUELLO, ed e' giusto.  `[M]` 21 agosto 2026: il banco ha
        #     dichiarato rosso un prodotto che consegnava correttamente il
        #     testo rimasto nel browser dalla prova precedente.
        # ⛔ E non si rilegge con `readText()` per verificarlo: su Firefox
        #    quella lettura vuole un gesto, e il banco finirebbe per misurare il
        #    permesso invece della clipboard.
        subprocess.run(["pkill", "-x", "xclip"], capture_output=True)
        time.sleep(0.3)
        pv = subprocess.Popen(["xclip", "-selection", "clipboard"],
                              stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL,
                              env=dict(os.environ, DISPLAY=o.schermo))
        pv.stdin.write(b""); pv.stdin.close()
        time.sleep(0.8)
        # ⛔ PRIMA DI TUTTO: quel che c'era nel desktop c'e' ancora?
        tira = Incollatore(); tira.parti(); tira.aspetta_pronto()
        resta = tira.raccogli()
        v.append({"giro": 0, "ricopiato": False, "interpellata": None,
                  "prova": "la clipboard del desktop sopravvive al collegamento",
                  "copiato_nel_browser": era_nel_desktop,
                  "arrivato_nella_sessione": resta,
                  "guai": ([] if resta == era_nel_desktop else
                           ["⛔ C0 — COLLEGANDOSI SI E' PERSA la clipboard del "
                            "desktop: c'era «%s», adesso c'e' «%s»"
                            % (era_nel_desktop[:40], resta[:40])])})
    v += [giro(nome, g, n + 1, o.schermo) for n in range(quanti)]
    if v and not v[-1]["guai"]:
        v.append(giro(nome, g, quanti + 1, o.schermo,
                      testo=v[-1]["copiato_nel_browser"]))
    return v


def firefox(giri, era=None):
    p, m, prof = M.accendi(porta=2896, headless=False, largo=1400, alto=900,
                           schermo=o.schermo)
    try:
        m.chiama("WebDriver:NewSession", {"acceptInsecureCerts": True})
        m.misura(1400, 900); m.vai(URL)
        m.js("""document.getElementById('utente').value='prova';
                document.getElementById('parola').value='prova2026';
                document.getElementById('vai').click(); return true;""")
        t0 = time.time()
        while time.time() - t0 < 40:
            if m.js("return document.body.dataset.schermo || ''")["value"] == "acceso":
                break
            time.sleep(0.5)
        time.sleep(3)
        g = GuidaFirefox(m)
        v = giri_di("firefox", g, giri, era)
        return {"browser": "firefox", "giri": v, "bottoncini": g.bottoncini}
    finally:
        M.spegni(p, prof)


def chrome(giri, era=None):
    t = tempfile.mkdtemp(prefix="b56-")
    amb = dict(os.environ, DISPLAY=o.schermo)
    amb.pop("WAYLAND_DISPLAY", None)
    br = subprocess.Popen(
        # ⛔⛔⭐ `--ozone-platform=x11` E NON E' UN DETTAGLIO — `[M]` 21 agosto
        #      2026: senza, Chrome **non va sullo schermo del banco**.  Prende
        #      Ozone/Wayland e si attacca alla sessione grafica VERA di chi
        #      lancia il banco, quindi legge un'ALTRA clipboard: `readText()`
        #      tornava «» mentre `xclip -o` sullo schermo del banco mostrava il
        #      testo.  ⇒ Il banco avrebbe dichiarato rotto un prodotto sano.
        ["google-chrome", "--no-sandbox", "--user-data-dir=%s/p" % t,
         "--no-first-run", "--no-default-browser-check", "--ozone-platform=x11",
         "--remote-debugging-port=9716", "--remote-allow-origins=*",
         "--window-size=1400,900", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=amb)
    try:
        b = CDP.pagina(9716, attesa=40)
        c = CDP.Cdp(b["webSocketDebuggerUrl"], timeout=180)
        for x in ("Page.enable", "Runtime.enable", "Network.enable"):
            c.chiama(x)
        c.chiama("Network.setCacheDisabled", cacheDisabled=True)
        # ⛔⭐ IL FUOCO SI EMULA, E SI DICHIARA PERCHE'.  `[M]` Senza, Chrome
        #    rifiuta ogni lettura della clipboard con «Document is not focused»:
        #    su uno schermo virtuale senza gestore di finestre nessuna finestra
        #    prende mai il fuoco.  ⚠ Un browser di una persona ce l'ha per
        #    forza — e' la finestra che sta guardando — quindi senza questa riga
        #    il banco misurerebbe l'assenza del gestore di finestre e la
        #    chiamerebbe difetto del prodotto.
        try:
            c.chiama("Emulation.setFocusEmulationEnabled", enabled=True)
        except Exception as e:
            print("   ⚠ fuoco NON emulato (%s)" % e)
        # ⛔ Il permesso si concede e si dichiara: su Chrome e' quel che l'utente
        #    concede UNA VOLTA con un clic, e non e' la cosa in prova.
        try:
            c.chiama("Browser.grantPermissions",
                     origin="https://%s:%d" % (MACCHINA, o.porta),
                     permissions=["clipboardReadWrite", "clipboardSanitizedWrite"])
        except Exception as e:
            print("   ⚠ permesso della clipboard NON concesso (%s)" % e)
        c.chiama("Page.navigate", url=URL)
        time.sleep(4)
        if c.valuta("!!document.getElementById('proceed-link')", attendi=False):
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
        c.valuta("""document.getElementById('utente').value='prova';
                    document.getElementById('parola').value='prova2026';
                    document.getElementById('vai').click();""", attendi=False)
        t0 = time.time()
        while time.time() - t0 < 40:
            if c.valuta("document.body.dataset.schermo || ''", attendi=False) == "acceso":
                break
            time.sleep(0.5)
        time.sleep(3)
        try:
            c.chiama("Page.bringToFront")
        except Exception:
            pass
        g = GuidaChrome(c)
        v = giri_di("chrome", g, giri, era)
        return {"browser": "chrome", "giri": v, "bottoncini": 0}
    finally:
        br.terminate()
        shutil.rmtree(t, ignore_errors=True)


def main():
    if not shutil.which("xclip"):
        print("⛔ serve `xclip`: senza, non si puo' copiare DA UN'ALTRA "
              "APPLICAZIONE, ed e' proprio la strada in prova")
        return 2
    # ⛔ Lo schermo virtuale e' del banco: un Firefox headless non ha una
    #    clipboard di sistema, e questo difetto vive li' dentro.
    xv = None
    if subprocess.run(["xdpyinfo", "-display", o.schermo],
                      capture_output=True).returncode != 0:
        xv = subprocess.Popen(["Xvfb", o.schermo, "-screen", "0", "1400x900x24"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(2)
    esiti = []
    try:
        for nome, f in (("firefox", firefox), ("chrome", chrome)):
            if o.solo and o.solo != nome:
                continue
            print("\n⏳ %s — %d incollate COL MOUSE, nessun `Ctrl+V`"
                  % (nome.upper(), o.giri))
            # ⛔ La prova «sopravvive?» si fa col PRIMO browser del giro, e la
            #    ragione e' misurata: il figlio sopravvive fra un collegamento e
            #    l'altro e si porta dietro lo stato della prova precedente —
            #    dal secondo browser in poi non si sta piu' misurando un
            #    collegamento, si sta misurando una coda.  ⚠ Per l'altro motore
            #    si rilancia il banco con `--solo`, a server appena riacceso.
            era = (TESTO_SESSIONE % (os.getpid() % 1000)) if not esiti else None
            visto = copia_nella_sessione(era) if era else None
            if era and visto != era:
                print("   ⛔ BANCO: la clipboard del desktop NON si e' "
                      "preparata: volevo «%s», la sessione rilegge «%s»"
                      % (era, visto[:60]))
                era = None
            try:
                e = f(o.giri, era)
            except Exception as ex:
                e = {"browser": nome, "guai_di_banco": repr(ex), "giri": []}
            esiti.append(e)
            for gg in e.get("giri", []):
                if gg["giro"] == 0:
                    print("   prima di tutto · %s"
                          % (gg["guai"][0] if gg["guai"] else
                             ("⚠ " + gg["prova"]) if "NON FATTA" in gg["prova"]
                             else "⭐ la clipboard del desktop e' SOPRAVVISSUTA"))
                    continue
                print("   giro %d (%s) · interpellata=%s · bottoncino=%s · %s"
                      % (gg["giro"],
                         "testo NUOVO" if gg["ricopiato"] else "STESSO testo",
                         gg["interpellata"], gg.get("bottoncino_comparso"),
                         "⭐ ARRIVATO" if not gg["guai"] else " · ".join(gg["guai"])))
            # ⚠ Il timeout d'inattivita' di QUIC e' ~20 s: il browser dopo se ne
            #   va, e il palco dev'essere libero prima del prossimo.
            time.sleep(22)
    finally:
        if xv:
            xv.terminate()
    fuori = os.path.join(QUI, "07-b56-esiti.json")
    with open(fuori, "w", encoding="utf-8") as f:
        json.dump(esiti, f, ensure_ascii=False, indent=1)
    guai = sum(len(g["guai"]) for e in esiti for g in e.get("giri", [])) \
         + sum(1 for e in esiti if e.get("guai_di_banco"))
    print("\n%s — %s" % ("⛔ ROSSO" if guai else "⭐ VERDE", fuori))
    for e in esiti:
        if e.get("guai_di_banco"):
            print("   ⛔ %s: il banco stesso e' caduto — %s"
                  % (e["browser"], e["guai_di_banco"]))
        elif e["browser"] == "firefox":
            print("   ⚠ Firefox ha chiesto il bottoncino «Incolla» %d volte su "
                  "%d incollate: e' il prezzo di §9, e questo e' il numero"
                  % (e.get("bottoncini", 0), len(e.get("giri", []))))
    return 1 if guai else 0


sys.exit(main())
