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


def accendi(profilo_prefs=None, headless=True, porta=2828, largo=1400, alto=1000):
    """Accende un Firefox con un profilo nuovo e Marionette aperta."""
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
    cmd = ["firefox", "--marionette", "--no-remote", "--profile", profilo,
           "--width", str(largo), "--height", str(alto)]
    if headless:
        cmd.append("--headless")
    log = open(os.path.join(profilo, "uscita.log"), "wb")
    p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT)
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
