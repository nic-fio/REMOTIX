#!/usr/bin/env python3
"""Un cliente minimo di Marionette — il protocollo che Firefox parla da se',
senza geckodriver.  Serve a UNA cosa: guidare il Firefox VERO dell'utente
(140 ESR) contro il prodotto, ed estrarre quel che la pagina ha in mano.

⛔ Non e' un banco: e' uno strumento di diagnosi.  Il verdetto lo da' il
   confronto fra quel che la pagina DIPINGE e quel che il filo PORTA."""
import json, os, shutil, socket, subprocess, tempfile, time


class Marionette:
    def __init__(self, porta=2828, host="127.0.0.1"):
        self.s = socket.create_connection((host, porta), timeout=120)
        self.s.settimeout(180)
        self.buf = b""
        self.n = 0
        self._leggi()                      # il saluto del server

    # il quadro e' «lunghezza:json»
    def _leggi(self):
        while b":" not in self.buf:
            self.buf += self.s.recv(65536)
        testa, resto = self.buf.split(b":", 1)
        quanti = int(testa)
        while len(resto) < quanti:
            resto += self.s.recv(65536)
        self.buf = resto[quanti:]
        return json.loads(resto[:quanti])

    def chiama(self, comando, parametri=None):
        self.n += 1
        corpo = json.dumps([0, self.n, comando, parametri or {}]).encode()
        self.s.sendall(str(len(corpo)).encode() + b":" + corpo)
        while True:
            m = self._leggi()
            if isinstance(m, list) and len(m) == 4 and m[0] == 1 and m[1] == self.n:
                if m[2] is not None:
                    raise RuntimeError("%s: %s" % (comando, json.dumps(m[2])[:600]))
                return m[3]

    def sessione(self, insicuri=True):
        return self.chiama("WebDriver:NewSession",
                           {"capabilities": {"alwaysMatch":
                            {"acceptInsecureCerts": insicuri}}})

    def vai(self, url):
        return self.chiama("WebDriver:Navigate", {"url": url})

    def js(self, codice, args=None):
        return self.chiama("WebDriver:ExecuteScript",
                           {"script": codice, "args": args or []})

    def js_async(self, codice, args=None, timeout=120000):
        self.chiama("WebDriver:SetTimeouts", {"script": timeout})
        return self.chiama("WebDriver:ExecuteAsyncScript",
                           {"script": codice, "args": args or []})

    def misura(self, l, a):
        return self.chiama("WebDriver:SetWindowRect", {"width": l, "height": a})

    def schermata(self):
        return self.chiama("WebDriver:TakeScreenshot", {"full": False})


def schermo_in_primo_piano():
    """⭐ Chi e' davanti allo schermo?  Torna `(va_bene, spiegazione)`.

    ⛔ Su Wayland una finestra NUOVA non si mappa se la sessione grafica in
       primo piano sul posto non e' la nostra: Firefox parte, apre la porta
       Marionette, e poi **non risponde piu'** — `WebDriver:NewSession` resta
       appeso fino al tetto del socket (180 s).

    `[M]` 23 settembre 2026, portatile CHUWI, due condizioni a confronto nello
    stesso quarto d'ora, Firefox 140.16 ESR:
      · sessione di `nicfio` in primo piano  →  NewSession in **1,39 s**;
      · sessione di un ALTRO utente in primo piano →  **3 tentativi su 3 in
        timeout**, e nel frattempo lo stesso Firefox `--headless` rispondeva in
        1,40 s e lo stesso Firefox VISIBILE su `Xvfb :99` in **1,63 s**.
    ⇒ Non e' Firefox, non e' la memoria: e' lo schermo.

    ⚠ Il confronto e' sull'UTENTE, non sul numero di sessione: un banco lanciato
      da `ssh` sta in una sessione senza posto, e il numero non combacerebbe
      mai.  Nel dubbio si dice di si', per non fermare chi funzionava."""
    try:
        def _chiedi(*a):
            return subprocess.run(["loginctl"] + list(a) + ["--value"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL,
                                  timeout=5).stdout.decode().strip()
        attiva = _chiedi("show-seat", "seat0", "-p", "ActiveSession")
        if not attiva:
            return True, ""
        di_chi = _chiedi("show-session", attiva, "-p", "User")
        if not di_chi or di_chi == str(os.getuid()):
            return True, ""
        nome = _chiedi("show-session", attiva, "-p", "Name") or di_chi
        return False, ("in primo piano c'e' la sessione %s dell'utente «%s», "
                       "non la tua" % (attiva, nome))
    except Exception:                          # noqa: BLE001
        return True, ""                        # non so dirlo: non ostacolo


def accendi(profilo_prefs=None, headless=True, porta=2828, largo=1400, alto=1000,
            schermo=None):
    """⭐ `schermo=":99"` accende un Firefox VERO su uno schermo virtuale.

    ⛔ Serve perche' `--headless` NON e' un browser vero dove conta: `[M]` 20
    agosto 2026, l'evento `paste` arriva in headless anche senza un elemento
    modificabile a fuoco, e su un browser con schermo NO.  ⇒ Un difetto della
    clipboard che l'utente vede si puo' misurare solo qui."""
    """Accende un Firefox con un profilo nuovo e Marionette aperta."""
    # ⭐ Il banco si guarda la scena PRIMA di accendere: una finestra vera sul
    #   desktop dell'utente vuole quel desktop in primo piano.  Meglio un
    #   verdetto in zero secondi che tre minuti di attesa cieca.
    if not headless and not schermo:
        ok, perche = schermo_in_primo_piano()
        if not ok:
            raise RuntimeError(
                "⛔ Firefox VISIBILE non puo' partire: %s.  Su Wayland la "
                "finestra non si mappa e `WebDriver:NewSession` non risponde "
                "(tetto 180 s).  ⇒ tre strade: torna sulla tua sessione "
                "grafica; oppure accendi uno schermo virtuale (`Xvfb :99 "
                "-screen 0 1600x1200x24` e poi `schermo=\":99\"`); oppure "
                "`headless=True` dove basta." % perche)
    profilo = tempfile.mkdtemp(prefix="remotix-ff-")
    prefs = {
        "browser.startup.homepage_override.mstone": "ignore",
        "datareporting.policy.firstRunURL": "",
        "browser.aboutwelcome.enabled": False,
        "browser.shell.checkDefaultBrowser": False,
        "marionette.port": porta,
        # ⚠ il registro della console: serve a raccogliere i guasti del
        #   decodificatore che la pagina non porta al server
        "devtools.console.stdout.content": True,
    }
    prefs.update(profilo_prefs or {})
    with open(os.path.join(profilo, "user.js"), "w") as f:
        for k, v in prefs.items():
            f.write('user_pref("%s", %s);\n' % (k, json.dumps(v)))
    # ⭐ `-remote-allow-system-access` apre il contesto **chrome** a Marionette:
    #   serve a chi deve guardare — o cliccare — quel che Firefox disegna FUORI
    #   dal documento, per esempio il bottoncino «Incolla» di §9 (`07-b56`).
    #   ⚠ E' una bandiera del BANCO: nessun Firefox di utente parte cosi'.
    cmd = ["firefox", "--marionette", "--no-remote", "-remote-allow-system-access",
           "--profile", profilo, "--width", str(largo), "--height", str(alto)]
    if headless:
        cmd.append("--headless")
    log = open(os.path.join(profilo, "uscita.log"), "wb")
    amb = dict(os.environ)
    if schermo:
        amb["DISPLAY"] = schermo
        # ⛔ Su una sessione Wayland, `DISPLAY` da solo non basta: Firefox
        #    prenderebbe comunque Wayland e ignorerebbe lo schermo virtuale.
        amb.pop("WAYLAND_DISPLAY", None)
        amb["MOZ_ENABLE_WAYLAND"] = "0"
    p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=amb)
    for _ in range(120):
        try:
            m = Marionette(porta)
            return p, m, profilo
        except OSError:
            time.sleep(0.5)
    p.kill()
    raise RuntimeError("Marionette non ha aperto la porta %d" % porta)


def spegni(p, profilo):
    try:
        p.terminate()
        p.wait(15)
    except Exception:
        p.kill()
    shutil.rmtree(profilo, ignore_errors=True)
