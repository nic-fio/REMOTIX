#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
19-android — THE ANDROID TESTS ON THE REAL PHONE (phase 19 §5 and §5.1)
===========================================================================

From the LAPTOP (where Phonestra's adb key lives):

    bash banchi/19-android/19-android.sh controlla
    bash banchi/19-android/19-android.sh prova 3                # row 3, on GNOME
    bash banchi/19-android/19-android.sh prova 1 --desktop kde
    bash banchi/19-android/19-android.sh prova tutte            # full round + short round
    bash banchi/19-android/19-android.sh ripristina             # after an interruption
    bash banchi/19-android/19-android.sh a-secco                # the bench without a phone

HOW IT IS MADE
  - The tests are those of the SUITE (phase 15), with its judges and its faults:
    they run ON THE SERVER with `15-giro.py --browser telefono` ("a red test is
    cured in the product, never by retouching the test").  The phone driver
    (`telefono.py`) talks to the phone's Chrome through two ports that this
    script carries to the server with `ssh -R`:
        server 127.0.0.1:19333 → laptop 9333 → adb forward → Chrome DevTools
        server 127.0.0.1:19334 → laptop 9334 → the COUNTER (below)
  - The COUNTER is the only one that uses adb during the tests: it answers a few
    named questions (call?, ready, tap, swipe, rotate, kill-chrome,
    keyboard?) and before every gesture it checks whether there is a call.  ⛔ Phonestra's key
    does not leave the laptop.
  - The results go into the suite's log, same format, in a log of
    its own: /media/REMOTIX/misure/fase19-android/registro.jsonl (browser
    "telefono"); evidence (uscita.log, photos of the canvas and of the phone's
    page via CDP) in /media/REMOTIX/misure/fase19-android/giro<giro>/...

⛔ THE PHONE BELONGS TO THE USER (DECISIONI §10.27, fasi/19 §5, memory):
  - ONLY Chrome, ONLY towards the server's boxes (https://192.168.0.2:8511-8514,
    and 8611-8614 for the network test); never other apps, settings, messages;
  - NEVER during a call: `dumpsys telephony.registry`, one line
    `mCallState=` per SIM, any `mCallState=[12]` = wait;
  - it is left AS IT WAS FOUND: the user's Chrome tabs are recorded at the start and
    not touched; ours are closed; rotation and screen timeout
    go back to how they were; if Chrome was closed, it is closed again.  The starting
    state lives in ~/.cache/remotix-19-android/stato.json until it is
    restored (and `ripristina` puts it back even after an interruption).
"""
import argparse
import datetime
import http.server
import json
import os
import re
import shlex
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.parse
import urllib.request

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(os.path.dirname(QUI))
CASA = os.path.expanduser("~")

ADB = os.environ.get("REMOTIX_ADB", "adb")
CHIAVE = os.environ.get("ADB_VENDOR_KEYS") or os.path.join(CASA, ".config/Phonestra/adbkey")
TELEFONI = os.path.join(CASA, ".config/Phonestra/telefoni.toml")
HOST = os.environ.get("REMOTIX_HOST", "nicfio@192.168.0.2")
IP_SERVER = os.environ.get("REMOTIX_TELEFONO_HOST", "192.168.0.2")
CONTROLLO = os.environ.get("REMOTIX_CONTROLLO_ANDROID", "/media/REMOTIX/src/controllo-android")
MISURE = os.environ.get("REMOTIX_MISURE_ANDROID", "/media/REMOTIX/misure/fase19-android")
CDP_QUI, SPORTELLO_QUI = 9333, 9334          # on the laptop
CDP_LA, SPORTELLO_LA = 19333, 19334          # on the server, at the end of the tunnel
CHROME = "com.android.chrome"
CHROME_MAIN = CHROME + "/com.google.android.apps.chrome.Main"
STATO_DIR = os.path.join(CASA, ".cache", "remotix-19-android")
STATO = os.path.join(STATO_DIR, "stato.json")
ATTESA_CHIAMATA_S = int(os.environ.get("REMOTIX_ATTESA_CHIAMATA_S", "1200"))
SCHERMO_ACCESO_MS = 30 * 60 * 1000
PORTE_SCATOLE = (8511, 8512, 8513, 8514)
DESKTOP = ("gnome", "kde", "xfce", "lxqt")

# The table of fasi/19-nvidia.md §5.1: row → (what, the suite's tests)
PROVE = {
    1: ("F-001, F-002 login and first image", ["f001"]),
    2: ("F-031 touch", ["f031-"]),
    3: ("F-007, F-009 keyboard", ["f007", "f009"]),
    4: ("F-014, F-015 clipboard", ["f014"]),
    5: ("F-012, F-013 audio and video", ["f012", "f013"]),
    6: ("F-003 update", ["f003"]),
    7: ("F-018 reattach at a different size (phone rotated)", ["f018-"]),
    8: ("F-016, F-017, F-020 detach and re-entry", ["f016", "f020"]),
    9: ("F-019 the network drops", ["f019"]),
    10: ("F-021 Exit", ["f021"]),
}
GIRO_PIENO = ("gnome", tuple(range(1, 11)))
GIRO_CORTO = (("kde", "xfce", "lxqt"), (1, 2, 6, 9))


# ═══════════════════════════════════════════════════════════════════════════
#  THE WORDS
# ═══════════════════════════════════════════════════════════════════════════
def ok(t):
    print("    \033[1;32mOK\033[0m  %s" % t, flush=True)


def no(t):
    print("    \033[1;31m⛔\033[0m  %s" % t, flush=True)


def nota(t):
    print("    --  %s" % t, flush=True)


def titolo(t):
    print("\n\033[1m== %s\033[0m" % t, flush=True)


class Fermo(Exception):
    """We stop, with the sentence for the user."""


# ═══════════════════════════════════════════════════════════════════════════
#  ADB — always and only here, on the laptop
# ═══════════════════════════════════════════════════════════════════════════
class Telefono:
    def __init__(self):
        self.seriale = None
        self._lock = threading.Lock()

    def _adb(self, *v, t=30, seriale=True):
        amb = dict(os.environ, ADB_VENDOR_KEYS=CHIAVE)
        cmd = [ADB] + (["-s", self.seriale] if (seriale and self.seriale) else []) + list(v)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                               timeout=t, env=amb)
            return r.returncode, (r.stdout or "") + (r.stderr or "")
        except FileNotFoundError:
            return 127, "adb is missing (%s)" % ADB
        except subprocess.TimeoutExpired:
            return 124, "adb did not answer in %d s" % t

    def sh(self, riga, t=30):
        with self._lock:
            return self._adb("shell", riga, t=t)

    # -- finding it ----------------------------------------------------------
    def visti(self):
        c, t = self._adb("devices", seriale=False, t=15)
        if c != 0:
            return None, t.strip()
        el = []
        for r in t.splitlines()[1:]:
            p = r.split()
            if len(p) >= 2 and p[1] == "device" and not p[0].startswith("emulator-"):
                el.append(p[0])
        return el, t.strip()

    def indirizzo_noto(self):
        """The last address Phonestra wrote (ip:port), or REMOTIX_TELEFONO."""
        if os.environ.get("REMOTIX_TELEFONO"):
            return os.environ["REMOTIX_TELEFONO"]
        try:
            m = re.search(r'^ultimo_indirizzo\s*=\s*"([^"]+)"', open(TELEFONI).read(), re.M)
            return m.group(1) if m else None
        except OSError:
            return None

    def trova(self, collega=True):
        """Returns (True, sentence) if the phone is seen by adb."""
        el, grezzo = self.visti()
        if el is None:
            return False, "adb is not answering: %s" % grezzo[-200:]
        ind = self.indirizzo_noto()
        if not el and collega and ind:
            if not os.path.exists(CHIAVE):
                return False, "phone not seen, and Phonestra's key is missing (%s)" % CHIAVE
            _c, t = self._adb("connect", ind, seriale=False, t=20)
            nota("adb connect %s: %s" % (ind, t.strip()[-120:]))
            el, grezzo = self.visti()
            el = el or []
        if not el:
            return False, ("phone not seen by adb%s.  Open Phonestra on the laptop (wireless "
                           "adb with the phone on and on the same network), then run again."
                           % (" (tried %s)" % ind if (collega and ind) else ""))
        scelto = None
        if len(el) == 1:
            scelto = el[0]
        else:
            ip = (ind or "").split(":")[0]
            vicini = [s for s in el if ip and s.startswith(ip + ":")]
            if len(vicini) == 1:
                scelto = vicini[0]
        if not scelto:
            return False, "more than one device seen by adb (%s): REMOTIX_TELEFONO=<serial>" % el
        self.seriale = scelto
        return True, scelto

    # -- the call ------------------------------------------------------------
    def chiamata(self):
        """(True|False|None, detail): None = unreadable (and then we wait)."""
        c, t = self.sh("dumpsys telephony.registry", t=20)
        if c != 0 or "mCallState=" not in t:
            return None, "call state unreadable: %s" % t.strip()[-120:]
        accese = re.findall(r"mCallState=[12]", t)
        return bool(accese), "%d mCallState lines, active: %s" % (
            len(re.findall(r"mCallState=", t)), accese or "none")

    def aspetta_fine_chiamata(self, tetto=None, parla=True):
        """True if (by now) no call; False if after `tetto` s there still is one."""
        tetto = ATTESA_CHIAMATA_S if tetto is None else tetto
        t0 = time.time()
        detto = False
        while True:
            c, d = self.chiamata()
            if c is False:
                if detto and parla:
                    nota("📞 call ended after %.0f s: resuming" % (time.time() - t0))
                return True
            if parla and not detto:
                nota("📞 %s — WAITING (no gesture on the phone)" % (
                    "call in progress" if c else d))
                detto = True
            if time.time() - t0 >= tetto:
                return False
            time.sleep(max(0.5, min(10, tetto - (time.time() - t0))))

    # -- the on-screen keyboard --------------------------------------------
    def tastiera(self):
        """(True|False|None, detail): is the on-screen keyboard open?  The input
        method manager says so (`mInputShown`), not the page: it is the fact
        the user sees ("keyboard only on request", DECISIONI §10.28)."""
        c, t = self.sh("dumpsys input_method | grep -m1 mInputShown=", t=15)
        m = re.search(r"mInputShown=(true|false)", t)
        if c != 0 or not m:
            return None, "keyboard state unreadable: %s" % t.strip()[-120:]
        return m.group(1) == "true", m.group(0)

    # -- the screen ----------------------------------------------------------
    def schermo(self):
        """(on, unlocked, sentence)."""
        _c, p = self.sh("dumpsys power | grep -m1 mWakefulness=", t=15)
        acceso = "mWakefulness=Awake" in p
        _c, w = self.sh("dumpsys window | grep -E 'mDreamingLockscreen|isKeyguardShowing|"
                        "mKeyguardShowing|mShowingLockscreen' | head -5", t=15)
        bloccato = bool(re.search(r"(mDreamingLockscreen|isKeyguardShowing|mKeyguardShowing|"
                                  r"mShowingLockscreen)=true", w))
        return acceso, not bloccato, "%s, %s" % ("on" if acceso else "OFF",
                                                  "locked" if bloccato else "unlocked")

    def chrome_versione(self):
        _c, t = self.sh("dumpsys package %s | grep -m1 versionName=" % CHROME, t=20)
        m = re.search(r"versionName=(\S+)", t)
        return m.group(1) if m else None

    def chrome_acceso(self):
        _c, t = self.sh("pidof %s" % CHROME, t=10)
        return bool(t.strip()) and t.strip().split()[0].isdigit()

    def chrome_davanti(self):
        _c, t = self.sh("dumpsys activity activities | grep -m1 -E "
                        "'topResumedActivity|mResumedActivity'", t=15)
        return CHROME in t

    def palco(self):
        _c, m = self.sh("getprop ro.product.manufacturer; getprop ro.product.model; "
                        "getprop ro.build.version.release", t=10)
        p = (m.split("\n") + ["", "", ""])[:3]
        return "Chrome %s on Android %s · %s %s (real phone, Wi-Fi)" % (
            self.chrome_versione() or "?", p[2].strip(), p[0].strip(), p[1].strip())

    def misura_schermo(self):
        _c, t = self.sh("wm size", t=10)
        m = re.findall(r"(\d+)x(\d+)", t)
        return tuple(int(v) for v in m[-1]) if m else None

    def forward(self, porta=CDP_QUI):
        return self._adb("forward", "tcp:%d" % porta, "localabstract:chrome_devtools_remote")

    def via_forward(self, porta=CDP_QUI):
        return self._adb("forward", "--remove", "tcp:%d" % porta)

    def impostazione(self, spazio, nome):
        _c, t = self.sh("settings get %s %s" % (spazio, nome), t=10)
        return t.strip()

    def metti(self, spazio, nome, valore):
        if valore in (None, "", "null"):
            return self.sh("settings delete %s %s" % (spazio, nome), t=10)
        return self.sh("settings put %s %s %s" % (spazio, nome, shlex.quote(str(valore))), t=10)


# ═══════════════════════════════════════════════════════════════════════════
#  THE PHONE'S CHROME, SEEN THROUGH THE PROTOCOL (via adb forward)
# ═══════════════════════════════════════════════════════════════════════════
def cdp_http(percorso, metodo="GET", porta=CDP_QUI, tetto=8):
    rq = urllib.request.Request("http://127.0.0.1:%d%s" % (porta, percorso), method=metodo)
    with urllib.request.urlopen(rq, timeout=tetto) as r:
        t = r.read().decode()
    try:
        return json.loads(t)
    except ValueError:
        return t


def schede(porta=CDP_QUI):
    return [x for x in cdp_http("/json/list", porta=porta) if x.get("type") == "page"]


def e_delle_scatole(url):
    u = urllib.parse.urlsplit(url or "")
    return u.hostname == IP_SERVER


def chiudi_scheda(sid, porta=CDP_QUI):
    for m in ("PUT", "GET"):
        try:
            cdp_http("/json/close/%s" % sid, m, porta=porta)
            return True
        except Exception:                         # noqa: BLE001
            continue
    return False


def aspetta_devtools(porta=CDP_QUI, tetto=25):
    fine = time.time() + tetto
    ultimo = ""
    while time.time() < fine:
        try:
            return cdp_http("/json/version", porta=porta)
        except Exception as e:                    # noqa: BLE001
            ultimo = str(e)
            time.sleep(1)
    raise Fermo("DevTools of the phone's Chrome not reachable: %s" % ultimo)


# ═══════════════════════════════════════════════════════════════════════════
#  THE STARTING STATE ("as I found it")
# ═══════════════════════════════════════════════════════════════════════════
def leggi_stato():
    try:
        return json.load(open(STATO))
    except (OSError, ValueError):
        return None


def scrivi_stato(st):
    os.makedirs(STATO_DIR, exist_ok=True)
    tmp = STATO + ".nuovo"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=1, ensure_ascii=False)
    os.replace(tmp, STATO)


def annota_partenza(tel):
    st = {"quando": datetime.datetime.now().isoformat(timespec="seconds"),
          "seriale": tel.seriale,
          "chrome_acceso": tel.chrome_acceso(),
          "rotazione": {"accelerometer_rotation": tel.impostazione("system",
                                                                   "accelerometer_rotation"),
                        "user_rotation": tel.impostazione("system", "user_rotation")},
          "spegnimento_ms": tel.impostazione("system", "screen_off_timeout"),
          "schede": [], "toccato": {}}
    if st["chrome_acceso"]:
        tel.forward()
        try:
            aspetta_devtools(tetto=10)
            st["schede"] = [{"id": x.get("id"), "url": x.get("url"), "title": x.get("title")}
                            for x in schede()]
        except Exception as e:                    # noqa: BLE001
            st["schede_errore"] = str(e)
    scrivi_stato(st)
    return st


def ripristina(tel, st, parla=True):
    """The phone as we found it.  Returns the sentences of what was done."""
    fatto = []
    if not st:
        return ["no state to restore"]
    if not tel.seriale:
        t_ok, _ = tel.trova(collega=False)
        if not t_ok:
            return ["⛔ phone not seen: NOT restored (the state stays in %s)" % STATO]
    if not tel.aspetta_fine_chiamata(parla=parla):
        return ["⛔ call in progress for too long: NOT restored (run `ripristina` again)"]
    loro = {x["id"] for x in st.get("schede", [])}
    if tel.chrome_acceso():
        tel.forward()
        try:
            aspetta_devtools(tetto=10)
            chiuse = 0
            for x in schede():
                if x.get("id") not in loro and e_delle_scatole(x.get("url")):
                    chiuse += chiudi_scheda(x["id"])
            fatto.append("closed %d tabs of ours (towards the boxes)" % chiuse)
            ora = {x.get("id") for x in schede()}
            perse = [x for x in st.get("schede", []) if x["id"] not in ora]
            if perse and st.get("toccato", {}).get("chrome_ucciso"):
                # after a force-stop Chrome reopens the tabs with new identifiers:
                # the addresses are compared
                urls = [x.get("url") for x in schede()]
                perse = [x for x in perse if x.get("url") not in urls]
            if perse:
                fatto.append("⚠ user's tabs I cannot find again: %s"
                             % [x.get("url") for x in perse])
            else:
                fatto.append("the user's %d tabs are all there" % len(loro))
        except Exception as e:                    # noqa: BLE001
            fatto.append("⚠ tabs not checked: %s" % e)
    tocc = st.get("toccato", {})
    if tocc.get("rotazione"):
        r = st["rotazione"]
        tel.sh("wm user-rotation free 2>/dev/null; true", t=10)
        tel.metti("system", "user_rotation", r.get("user_rotation"))
        tel.metti("system", "accelerometer_rotation", r.get("accelerometer_rotation"))
        fatto.append("rotation restored: automatic=%s, orientation=%s" % (
            r.get("accelerometer_rotation"), r.get("user_rotation")))
    if tocc.get("spegnimento"):
        tel.metti("system", "screen_off_timeout", st.get("spegnimento_ms"))
        fatto.append("screen timeout restored to %s ms" % st.get("spegnimento_ms"))
    if not st.get("chrome_acceso") and tel.chrome_acceso():
        tel.sh("am force-stop %s" % CHROME, t=15)
        fatto.append("Chrome closed again (it was closed when I arrived)")
    tel.via_forward()
    try:
        os.replace(STATO, STATO + ".ripristinato")
    except OSError:
        pass
    return fatto


# ═══════════════════════════════════════════════════════════════════════════
#  THE COUNTER: the only questions that reach adb from the server
# ═══════════════════════════════════════════════════════════════════════════
class Sportello:
    def __init__(self, tel, st, porta=SPORTELLO_QUI, cdp=CDP_QUI):
        self.tel, self.st, self.porta, self.cdp = tel, st, porta, cdp
        self.mie = set()
        self.diario = []
        self.srv = None

    def segna(self, chiave, valore=True):
        self.st.setdefault("toccato", {})[chiave] = valore
        scrivi_stato(self.st)

    def scrivi_diario(self, t):
        r = "%s %s" % (time.strftime("%H:%M:%S"), t)
        self.diario.append(r)
        if os.environ.get("REMOTIX_SPORTELLO_PARLA") == "1":
            nota("counter: " + t)

    # -- the answers ----------------------------------------------------------
    def guardia(self):
        """None if the phone may be touched; otherwise (code, sentence)."""
        if self.tel.aspetta_fine_chiamata():
            return None
        return 409, "call in progress on the phone for more than %d s" % ATTESA_CHIAMATA_S

    def pronto(self):
        g = self.guardia()
        if g:
            return g
        fine = time.time() + 180
        detto = False
        while True:
            acceso, sbloccato, frase = self.tel.schermo()
            if acceso and sbloccato:
                break
            if not detto:
                nota("🔓 the phone is %s: turn it on and unlock it (waiting 3 minutes)" % frase)
                detto = True
            if time.time() > fine:
                return 423, "phone %s: not touching anything" % frase
            time.sleep(5)
        if not self.tel.chrome_acceso() or not self.tel.chrome_davanti():
            self.tel.sh("am start -a android.intent.action.MAIN -c "
                        "android.intent.category.LAUNCHER -n %s" % CHROME_MAIN, t=20)
            self.scrivi_diario("Chrome brought to the front")
        self.tel.forward(self.cdp)
        aspetta_devtools(self.cdp)
        # the boxes' tabs left over by a killed Chrome (reopened by it): away
        loro = {x["id"] for x in self.st.get("schede", [])}
        for x in schede(self.cdp):
            if (x.get("id") not in loro and x.get("id") not in self.mie
                    and e_delle_scatole(x.get("url"))):
                chiudi_scheda(x["id"], self.cdp)
                self.scrivi_diario("closed the leftover tab %s" % x.get("url"))
        return 200, {"pronto": True}

    def dentro_schermo(self, *xy):
        m = self.tel.misura_schermo()
        if not m:
            return False
        lato = max(m)
        return all(0 <= v < lato for v in xy)

    def rispondi(self, percorso, d):
        if percorso == "/chiamata":
            g = self.guardia()
            return g or (200, {"chiamata": False})
        if percorso == "/pronto":
            return self.pronto()
        if percorso == "/palco":
            return 200, {"palco": self.tel.palco()}
        if percorso == "/tastiera":
            # ⚠ only a read (`dumpsys`): no gesture, no guard
            aperta, det = self.tel.tastiera()
            if aperta is None:
                return 500, det
            return 200, {"aperta": aperta, "riga": det}
        if percorso == "/mia":
            self.mie.add(d.get("id"))
            return 200, {}
        if percorso == "/non-mia":
            self.mie.discard(d.get("id"))
            return 200, {}
        if percorso in ("/tocca", "/scorri", "/ruota", "/uccidi-chrome"):
            g = self.guardia()
            if g:
                return g
        if percorso == "/tocca":
            x, y = int(d["x"]), int(d["y"])
            if not self.dentro_schermo(x, y):
                return 400, "tap outside the screen: %s" % ((x, y),)
            c, t = self.tel.sh("input tap %d %d" % (x, y), t=15)
            self.scrivi_diario("tap %d,%d" % (x, y))
            return (200, {}) if c == 0 else (500, "input tap: %s" % t[-120:])
        if percorso == "/scorri":
            v = [int(d[k]) for k in ("x1", "y1", "x2", "y2")]
            ms = max(100, min(3000, int(d.get("ms", 500))))
            if not self.dentro_schermo(*v):
                return 400, "finger outside the screen: %s" % v
            c, t = self.tel.sh("input swipe %d %d %d %d %d" % tuple(v + [ms]), t=15)
            self.scrivi_diario("finger %s in %d ms" % (v, ms))
            return (200, {}) if c == 0 else (500, "input swipe: %s" % t[-120:])
        if percorso == "/ruota":
            return 200, {"detto": self.ruota(d.get("verso", "altro"))}
        if percorso == "/uccidi-chrome":
            self.tel.sh("am force-stop %s" % CHROME, t=15)
            self.mie.clear()
            self.segna("chrome_ucciso")
            self.scrivi_diario("Chrome stopped abruptly (force-stop)")
            return 200, {}
        return 404, "the counter does not know %s" % percorso

    def ruota(self, verso):
        """partenza = portrait; altro = landscape.  Automatic rotation off
        while the round lasts; `ripristina` puts it back as it was."""
        self.segna("rotazione")
        n = 0 if verso == "partenza" else 1
        _c, t = self.tel.sh("wm user-rotation lock %d 2>&1" % n, t=10)
        if "rror" in t or "nknown" in t:
            self.tel.metti("system", "accelerometer_rotation", "0")
            self.tel.metti("system", "user_rotation", str(n))
        else:
            self.tel.metti("system", "accelerometer_rotation", "0")
        time.sleep(2.5)
        self.scrivi_diario("rotated: %s" % ("portrait" if n == 0 else "landscape"))
        return "phone %s" % ("portrait" if n == 0 else "landscape")

    # -- the server ------------------------------------------------------------
    def accendi(self):
        sp = self

        class H(http.server.BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_POST(self):
                n = int(self.headers.get("Content-Length") or 0)
                try:
                    d = json.loads(self.rfile.read(n).decode() or "{}")
                except ValueError:
                    d = {}
                try:
                    codice, corpo = sp.rispondi(self.path.split("?")[0], d)
                except Exception as e:            # noqa: BLE001
                    codice, corpo = 500, "the counter crashed: %s" % e
                if not isinstance(corpo, dict):
                    corpo = {"perche": corpo}
                b = json.dumps(corpo, ensure_ascii=False).encode()
                self.send_response(codice)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", self.porta), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def spegni(self):
        if self.srv:
            self.srv.shutdown()
            self.srv.server_close()


# ═══════════════════════════════════════════════════════════════════════════
#  THE SERVER (read only, except the tests themselves)
# ═══════════════════════════════════════════════════════════════════════════
def ssh(riga, t=60, avanti=None):
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8"]
    if avanti:
        cmd += ["-o", "ExitOnForwardFailure=yes"] + avanti
    try:
        r = subprocess.run(cmd + [HOST, riga], capture_output=True, text=True,
                           errors="replace", timeout=t)
        out = "\n".join(x for x in (r.stdout + r.stderr).splitlines() if not x.startswith("tput"))
        return r.returncode, out
    except subprocess.TimeoutExpired:
        return 124, "ssh: no answer in %d s" % t


# ⚠ /sys inside the box is the host's (renderD128 = the Intel even when the Radeon
#   is mapped inside): the GPU is read from the route the server declared in the log.
SCHEDA_SH = ("P=$(awk '/^pass:/{print $2; exit}' $HOME/SERVER.ssh 2>/dev/null); "
             "printf '%s\\n' \"$P\" | sudo -S -p '' podman exec rete11-gnome "
             "sh -c \"grep -ohE 'route (vulkan|vaapi)' /var/lib/rete11/registro.log | tail -1\"")


def scheda_delle_scatole():
    _c, t = ssh(SCHEDA_SH, 30)
    if "route vaapi" in t:
        return "intel", "Intel UHD 770 (VA-API)"
    if "route vulkan" in t:
        return "radeon", "AMD RX 6800 (Vulkan)"
    return "ignota", "GPU not read (%s)" % t.strip()[-60:]


# ═══════════════════════════════════════════════════════════════════════════
#  CHECK
# ═══════════════════════════════════════════════════════════════════════════
def controlla(tel, o):
    """Returns True if we can start.  The first missing check stops everything."""
    titolo("The phone")
    trovato, frase = tel.trova(collega=not o.non_collegare)
    if not trovato:
        no(frase)
        return False
    ok("adb sees the phone: %s" % frase)
    c, d = tel.chiamata()
    if c is None:
        no(d)
        return False
    if c:
        no("📞 call in progress (%s): wait for it to end, then run again" % d)
        return False
    ok("no call (%s)" % d)
    acceso, sbloccato, fr = tel.schermo()
    (ok if (acceso and sbloccato) else no)("screen %s" % fr)
    v = tel.chrome_versione()
    if not v:
        no("Chrome (%s) is not on the phone" % CHROME)
        return False
    ok("Chrome %s" % v)
    if tel.chrome_acceso():
        tel.forward()
        try:
            ver = aspetta_devtools(tetto=10)
            ok("DevTools reachable: %s" % ver.get("Browser"))
            sc = schede()
            ok("user's open tabs: %d (not touched)" % len(sc))
        except Fermo as e:
            no("%s — on the phone: Settings › Developer options › USB debugging on?" % e)
            return False
        finally:
            tel.via_forward()
    else:
        nota("Chrome closed: the test opens it and closes it again at the end (DevTools is checked then)")
    titolo("The boxes seen from the phone")
    _c, ping = tel.sh("ping -c 1 -W 2 %s >/dev/null 2>&1 && echo si || echo no" % IP_SERVER,
                      t=10)
    (ok if "si" in ping else no)("the server %s %s from the phone (ping)"
                                 % (IP_SERVER, "answers" if "si" in ping else "does NOT answer"))
    # ⚠ the ports are checked from the LAPTOP (same network as the phone): on the phone
    #   there is no reliable tool without installing anything; test 1
    #   crosses them anyway from the phone's Chrome
    viste = {}
    for p in PORTE_SCATOLE:
        try:
            socket.create_connection((IP_SERVER, p), timeout=3).close()
            viste[str(p)] = "si"
        except OSError as e:
            viste[str(p)] = "no"
            nota("port %d: %s" % (p, e))
        (ok if viste[str(p)] == "si" else no)("box on port %d %s" % (
            p, "listening" if viste[str(p)] == "si" else "does NOT answer"))
    titolo("The server")
    c, t = ssh("echo vivo; pgrep -af '15-giro.py|16-salita.py' | grep -v pgrep | head -3", 20)
    if c != 0 or "vivo" not in t:
        no("ssh %s does not work: %s" % (HOST, t[-160:]))
        return False
    ok("ssh %s" % HOST)
    altri = [r for r in t.splitlines()[1:] if r.strip()]
    if altri:
        no("a round is already running on the server (%s): the boxes are its own, wait" % altri[0][:100])
        return False
    ok("no other round on the server")
    s, frase = scheda_delle_scatole()
    ok("boxes on the GPU: %s" % frase)
    o.scheda = s
    pronto = (acceso and sbloccato and "si" in ping
              and all(viste.get(str(p)) == "si" for p in PORTE_SCATOLE))
    if not pronto:
        no("not starting: fix the red lines")
    else:
        titolo("Ready")
    return pronto


# ═══════════════════════════════════════════════════════════════════════════
#  TEST
# ═══════════════════════════════════════════════════════════════════════════
def piano(o):
    if o.cosa == "tutte":
        p = [(GIRO_PIENO[0], n) for n in GIRO_PIENO[1]]
        for d in GIRO_CORTO[0]:
            p += [(d, n) for n in GIRO_CORTO[1]]
        if o.desktop:
            p = [x for x in p if x[0] in o.desktop]
        return p
    n = int(o.cosa)
    if n not in PROVE:
        raise Fermo("tests go from 1 to 10 (fasi/19-nvidia.md §5.1)")
    return [(d, n) for d in (o.desktop or ["gnome"])]


def porta_i_banchi():
    amb = dict(os.environ, REMOTIX_CONTROLLO=CONTROLLO, REMOTIX_HOST=HOST)
    r = subprocess.run(["bash", os.path.join(RADICE, "banchi/15-suite/15-porta.sh")],
                       capture_output=True, text=True, env=amb, timeout=300)
    if r.returncode != 0:
        raise Fermo("the benches do not reach the server: %s" % (r.stdout + r.stderr)[-300:])
    nota((r.stdout.strip().splitlines() or ["?"])[-1])


def righe_del_registro(giro, desktop, prove):
    c, t = ssh("grep -F '\"giro\": \"%s\"' %s/registro.jsonl 2>/dev/null | grep -F "
               "'\"desktop\": \"%s\"' | tail -200" % (giro, MISURE, desktop), 30)
    righe = []
    for x in t.splitlines():
        try:
            r = json.loads(x)
        except ValueError:
            continue
        if any(f in r.get("prova", "") for f in prove):
            righe.append(r)
    # the last run of each test
    ultimo = {}
    for r in righe:
        ultimo[r["prova"]] = max(ultimo.get(r["prova"], ""), r.get("inizio", ""))
    return [r for r in righe if r.get("inizio") == ultimo.get(r["prova"])]


def una_riga(o, tel, sp, d, n, giro, sistema):
    cosa, prove = PROVE[n]
    titolo("Test %d · %s · %s" % (n, d.upper(), cosa))
    if not tel.aspetta_fine_chiamata():
        return [{"esito": "BLOCKED", "ragione": "call in progress for too long", "funzione": "?"}]
    if n == 7:
        sp.ruota("partenza")
    amb = {"REMOTIX_MISURE_15": MISURE, "REMOTIX_SISTEMA_15": sistema,
           "REMOTIX_TELEFONO_CDP": str(CDP_LA), "REMOTIX_TELEFONO_SPORTELLO": str(SPORTELLO_LA),
           "REMOTIX_TELEFONO_HOST": IP_SERVER}
    riga = ("cd %s/banchi/15-suite && env %s python3 15-giro.py --giro %s --desktop %s "
            "--browser telefono --prove %s%s" % (
                CONTROLLO, " ".join("%s=%s" % (k, shlex.quote(v)) for k, v in amb.items()),
                shlex.quote(giro), d, ",".join(prove), " --senza-guasto" if o.senza_guasto else ""))
    avanti = ["-R", "%d:127.0.0.1:%d" % (CDP_LA, CDP_QUI),
              "-R", "%d:127.0.0.1:%d" % (SPORTELLO_LA, SPORTELLO_QUI)]
    t0 = time.time()
    try:
        c, out = ssh(riga, t=60 * 12 * len(prove), avanti=avanti)
    finally:
        if n == 7:
            sp.ruota("partenza")
    for r in out.splitlines():
        if r.startswith(("[", "⛔", "⭐ ROUND", "   server")):
            nota(r)
    righe = righe_del_registro(giro, d, prove)
    if not righe:
        no("no line in the log (code %s): %s" % (c, out[-400:]))
    for r in righe:
        segno = {"PASS": "⭐", "FAIL": "⛔", "BLOCKED": "⚠"}.get(r["esito"], "?")
        print("    %s %-6s %-6s [%s] %s" % (segno, r["funzione"], r["esito"], r["passata"],
                                            (r.get("ragione") or "")[:150]), flush=True)
    nota("%.0f s" % (time.time() - t0))
    return righe


def prova(tel, o):
    if leggi_stato():
        raise Fermo("there is an unrestored starting state (%s): first "
                    "`19-android.sh ripristina`" % STATO)
    if not controlla(tel, o):
        return 3
    pi = piano(o)
    titolo("The plan: %s" % ", ".join("%s/%d" % x for x in pi))
    porta_i_banchi()
    st = annota_partenza(tel)
    ok("recorded the phone as I found it: Chrome %s, %d tabs, rotation %s, "
       "screen timeout %s ms" % ("open" if st["chrome_acceso"] else "closed", len(st["schede"]),
                              st["rotazione"], st["spegnimento_ms"]))
    sp = Sportello(tel, st)
    giro = o.giro or "19-android-%s" % o.scheda
    sistema = "%s · boxes on %s · server 192.168.0.2" % (
        tel.palco(), {"intel": "Intel UHD 770 (VA-API)", "radeon": "AMD RX 6800 (Vulkan)"}
        .get(o.scheda, o.scheda))
    tutte = []
    interrotto = []

    def ferma(_n, _f):
        interrotto.append(1)
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, ferma)
    try:
        sp.accendi()
        tel.forward()
        # the screen must not turn off halfway through a test (restored at the end)
        tel.metti("system", "screen_off_timeout", str(SCHERMO_ACCESO_MS))
        sp.segna("spegnimento")
        for d, n in pi:
            righe = una_riga(o, tel, sp, d, n, giro, sistema)
            if any("call in progress" in (r.get("ragione") or "") and r["esito"] == "BLOCKED"
                   for r in righe):
                nota("📞 a call interrupted test %d: redoing it" % n)
                tel.aspetta_fine_chiamata()
                righe = una_riga(o, tel, sp, d, n, giro, sistema)
            tutte += [(d, n, r) for r in righe]
    except KeyboardInterrupt:
        no("interrupted: putting the phone back in order")
    finally:
        sp.spegni()
        titolo("The phone as I found it")
        for f in ripristina(tel, leggi_stato() or st):
            (no if f.startswith("⛔") else nota)(f)
    titolo("Summary (round %s)" % giro)
    conto = {}
    for d, n, r in tutte:
        conto[r["esito"]] = conto.get(r["esito"], 0) + 1
    print("    %s" % " ".join("%s=%d" % kv for kv in sorted(conto.items())))
    for d, n, r in tutte:
        if r["esito"] != "PASS":
            print("    %s test %d %s %s [%s]: %s" % (d, n, r["funzione"], r["esito"],
                                                     r["passata"], (r.get("ragione") or "")[:200]))
    nota("log: %s:%s/registro.jsonl · evidence in %s/giro%s/" % (HOST, MISURE, MISURE, giro))
    nota("report: ssh %s python3 %s/banchi/15-suite/15-rapporto.py --registro "
         "%s/registro.jsonl --giro %s --testo" % (HOST, CONTROLLO, MISURE, giro))
    if interrotto or not tutte:
        return 3
    return 1 if conto.get("FAIL") else (3 if conto.get("BLOCKED") else 0)


# ═══════════════════════════════════════════════════════════════════════════
#  DRY RUN: the whole bench without phone and without server
# ═══════════════════════════════════════════════════════════════════════════
ADB_FINTO = r"""#!/bin/bash
# FAKE adb of the dry run: it talks to no phone.
D="$(dirname "$0")"
echo "$*" >> "$D/adb.log"
case "$*" in
  devices*) printf 'List of devices attached\n'; [ -f "$D/visto" ] && printf 'finto:5555\tdevice\n'; exit 0;;
  connect*) echo "failed to connect"; exit 1;;
esac
while [ "${1:-}" = "-s" ]; do shift 2; done
case "$1" in
  forward) exit 0;;
  shell) shift; r="$*";;
  *) exit 0;;
esac
case "$r" in
  *telephony.registry*) if [ -f "$D/chiamata" ]; then echo "  mCallState=0"; echo "  mCallState=1"; else echo "  mCallState=0"; echo "  mCallState=0"; fi;;
  *mWakefulness*) echo "  mWakefulness=Awake";;
  *input_method*) if [ -f "$D/tastiera" ]; then echo "  mInputShown=true"; else echo "  mInputShown=false"; fi;;
  *Lockscreen*|*Keyguard*) echo "  mDreamingLockscreen=false";;
  *"dumpsys package"*) echo "    versionName=154.0.0.0";;
  *pidof*) echo 4242;;
  *"dumpsys activity"*) echo "  topResumedActivity=ActivityRecord{1 u0 com.android.chrome/.Main}";;
  *getprop*) printf 'samsung\nSM-S916B\n16\n';;
  *"wm size"*) echo "Physical size: 1080x2340";;
  *"settings get system accelerometer_rotation"*) echo 1;;
  *"settings get system user_rotation"*) echo 0;;
  *"settings get"*) echo 60000;;
  *ping*) echo si;;
  *) echo "(fake) $r";;
esac
"""

PAGINA_FINTA = """<!doctype html><meta charset=utf-8><title>fake box</title>
<style>html,body{margin:0;height:100%;background:#000}#schermo{width:100vw;height:100vh;display:block}</style>
<canvas id=schermo width=800 height=500></canvas>
<script>
const c=document.getElementById('schermo').getContext('2d');
c.fillStyle='#1d6fd6';c.fillRect(0,0,400,250);c.fillStyle='#2bb34a';c.fillRect(400,250,400,250);
window.__visti=[];
for (const t of ['mousedown','keydown','touchstart']) addEventListener(t,e=>__visti.push(t+':'+(e.key||'')),true);
/* a fake trackpad like the real page's (SPECIFICHE §7.1): the finger moves the
   pointer by the same distance, after a 9 px threshold; canvas = glass */
let P=[400,250], giu=null, ult=null, mosso=false;
addEventListener('touchstart',e=>{const t=e.touches[0];giu=[t.clientX,t.clientY];ult=giu;mosso=false;},true);
addEventListener('touchmove',e=>{const t=e.touches[0];const q=[t.clientX,t.clientY];
  if(!mosso&&Math.hypot(q[0]-giu[0],q[1]-giu[1])>9) mosso=true;
  const r=document.getElementById('schermo').getBoundingClientRect(), kx=r.width/800, ky=r.height/500;
  if(mosso){P[0]=Math.min(799,Math.max(0,P[0]+(q[0]-ult[0])/kx));P[1]=Math.min(499,Math.max(0,P[1]+(q[1]-ult[1])/ky));}
  ult=q;},true);
window.REMOTIX={tocco:{stato:()=>({puntatore:P.slice(),in_vigore:true}),disposizione:()=>'tocco'}};
window.REMOTIX_PUNTATORE={geometria:()=>{const r=document.getElementById('schermo').getBoundingClientRect();
  return {r:r,bx0:0,by0:0,sx:r.width/800,sy:r.height/500,vx:1,vy:1,tl:800,ta:500};}};
</script>"""


def a_secco(o):
    """The bench tested WITHOUT a phone: (1) without a device it must say "phone not
    seen" and exit cleanly; (2) the CDP part against a laptop Chrome (throwaway
    profile) on a local page; the counter with a FAKE adb."""
    import importlib.util as iu
    tmp = tempfile.mkdtemp(prefix="remotix-19-secco-")
    finto = os.path.join(tmp, "adb")
    open(finto, "w").write(ADB_FINTO)
    os.chmod(finto, 0o755)
    global ADB, STATO_DIR, STATO, IP_SERVER
    ADB = finto
    # ⛔ today the server and its ports are not touched: the "boxes" are a loopback
    #   address where nobody listens
    IP_SERVER = "127.0.0.9"
    STATO_DIR = os.path.join(tmp, "stato")
    STATO = os.path.join(STATO_DIR, "stato.json")
    esiti = []

    def esito(cosa, vero, dettaglio=""):
        esiti.append(vero)
        (ok if vero else no)("%s%s" % (cosa, (" — " + dettaglio) if dettaglio else ""))

    titolo("DRY RUN 1 — without phone")
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "controlla"],
                       capture_output=True, text=True,
                       env=dict(os.environ, REMOTIX_ADB=finto, REMOTIX_TELEFONO="",
                                HOME=tmp), timeout=60)
    print("\n".join("      | " + x for x in r.stdout.strip().splitlines()))
    esito("\"controlla\" says phone not seen and exits with 2", r.returncode == 2
          and "phone not seen" in r.stdout, "code %d" % r.returncode)
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "prova", "1"],
                       capture_output=True, text=True,
                       env=dict(os.environ, REMOTIX_ADB=finto, REMOTIX_TELEFONO="",
                                HOME=tmp), timeout=60)
    esito("\"prova 1\" stops at the same point, without touching the server",
          r.returncode == 2 and "phone not seen" in r.stdout and "The server" not in r.stdout,
          "code %d" % r.returncode)
    log = open(os.path.join(tmp, "adb.log")).read() if os.path.exists(
        os.path.join(tmp, "adb.log")) else ""
    esito("adb got only \"devices\" (no connect without key, no shell)",
          all(x.startswith("devices") or x.startswith("connect") for x in log.splitlines())
          and "shell" not in log, log.replace("\n", " | "))

    titolo("DRY RUN 2 — the phone driver against a laptop Chrome")
    open(os.path.join(tmp, "visto"), "w").close()
    # the "boxes" page, local
    os.makedirs(os.path.join(tmp, "sito"))
    open(os.path.join(tmp, "sito", "index.html"), "w").write(PAGINA_FINTA)
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    porta_sito = s.getsockname()[1]
    s.close()
    sito = subprocess.Popen([sys.executable, "-m", "http.server", str(porta_sito), "--bind",
                             "127.0.0.1", "--directory", os.path.join(tmp, "sito")],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    prof = os.path.join(tmp, "chrome")
    chrome = subprocess.Popen(["google-chrome", "--headless=new",
                               "--remote-debugging-port=%d" % CDP_QUI, "--user-data-dir=" + prof,
                               "--no-first-run", "--no-default-browser-check",
                               "--remote-allow-origins=*", "--window-size=412,915",
                               "data:text/html,<title>user's tab</title><h1>theirs</h1>"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sp = None
    try:
        aspetta_devtools(tetto=30)
        tel = Telefono()
        trovato, fr = tel.trova(collega=False)
        esito("with the fake adb the phone is \"seen\"", trovato, fr)
        st = annota_partenza(tel)
        esito("user's tabs recorded", len(st["schede"]) == 1,
              str([x["title"] for x in st["schede"]]))
        sp = Sportello(tel, st)
        sp.accendi()
        os.environ.update(REMOTIX_TELEFONO_CDP=str(CDP_QUI), REMOTIX_TELEFONO_HOST=IP_SERVER,
                          REMOTIX_TELEFONO_SPORTELLO=str(SPORTELLO_QUI),
                          REMOTIX_TELEFONO_A_SECCO="1")
        spec = iu.spec_from_file_location("telefono", os.path.join(QUI, "telefono.py"))
        T = iu.module_from_spec(spec)
        spec.loader.exec_module(T)

        class O:
            evidenze = os.path.join(tmp, "evidenze")
        os.makedirs(O.evidenze)
        g = T.GuidaTelefono(O())
        esito("the driver opens a tab of ITS OWN", g.scheda["id"] not in
              {x["id"] for x in st["schede"]}, g.scheda["id"])
        esito("palco", "Android 16" in g.palco(), g.palco())
        try:
            g.vai("https://example.com/")
            esito("refuses an address outside the boxes", False)
        except RuntimeError as e:
            esito("refuses an address outside the boxes", "only to the server's boxes" in str(e))
        aperta, perche = g.vai("http://127.0.0.1:%d/" % porta_sito)
        esito("goes to the \"box\" (local page)", aperta, perche)
        time.sleep(1)
        png, _ = g.fotografa_tela()
        esito("photo of the canvas via CDP", bool(png) and png[:4] == b"\x89PNG",
              "%d byte" % len(png or b""))
        g.clic(100, 100)
        g.tasto("ArrowRight")
        g.dito_cdp([(50, 50), (80, 60), (120, 70)])
        visti = g.js("return window.__visti")
        esito("click, key and finger reach the page", visti and "mousedown:" in visti
              and "keydown:ArrowRight" in visti and "touchstart:" in visti, str(visti))
        tocchi = g.tocchi_visti()
        esito("the touch notebook sees them", len(tocchi) >= 1, str(tocchi[:1]))
        # the trackpad pointer brought onto a target, even a near one (wide loop)
        geo = g.js("const P=window.REMOTIX_PUNTATORE,t=document.getElementById('schermo');"
                   "const q=P.geometria();return {left:q.r.left,top:q.r.top,width:q.r.width,"
                   "height:q.r.height,bx0:0,by0:0,sx:q.sx,sy:q.sy,vx:1,vy:1,tl:800,ta:500};")
        e1 = g.porta_il_puntatore(geo, geo["width"] * 0.2, geo["height"] * 0.3)
        e2 = g.porta_il_puntatore(geo, geo["width"] * 0.2 + 4, geo["height"] * 0.3 - 3)
        esito("the pointer is brought onto the target (far and at 4 px)",
              e1 is not None and e1 <= 1 and e2 is not None and e2 <= 1,
              "errors %s and %s px" % (e1, e2))
        # the call: with the "call" on the counter must refuse
        open(os.path.join(tmp, "chiamata"), "w").close()
        global ATTESA_CHIAMATA_S
        vecchia, ATTESA_CHIAMATA_S = ATTESA_CHIAMATA_S, 1
        try:
            g.guardia(subito=True)
            esito("with a call the guard stops the gesture", False)
        except T.ChiamataInCorso as e:
            esito("with a call the guard stops the gesture (409)", True, str(e))
        try:
            g.clic(10, 10)
            esito("…a click too", False)
        except T.ChiamataInCorso:
            esito("…a click too", True)
        ATTESA_CHIAMATA_S = vecchia
        os.remove(os.path.join(tmp, "chiamata"))
        g.guardia(subito=True)
        esito("once the call is over we resume", True)
        # the on-screen keyboard: the question to the counter and the driver's method
        esito("keyboard: closed ⇒ \"aperta\" false", g.tastiera_aperta() is False)
        open(os.path.join(tmp, "tastiera"), "w").close()
        esito("keyboard: open ⇒ \"aperta\" true (dumpsys input_method)",
              g.aspetta_tastiera(True, 2) is True)
        os.remove(os.path.join(tmp, "tastiera"))
        esito("keyboard: closed again ⇒ false again", g.aspetta_tastiera(False, 2) is False)
        esito("keyboard: the counter asked adb only `dumpsys input_method`",
              "dumpsys input_method | grep -m1 mInputShown=" in
              open(os.path.join(tmp, "adb.log")).read())
        print("      | rotate: %s" % T.orienta("altro"))
        sp.segna("spegnimento")
        g.chiudi()
        rimaste = schede()
        esito("our tab closed, the user's is there",
              [x["id"] for x in rimaste] == [x["id"] for x in st["schede"]],
              str([x.get("title") for x in rimaste]))
        esito("evidence of the closing saved",
              any(f.startswith("telefono-chiusura") for f in os.listdir(O.evidenze)),
              str(os.listdir(O.evidenze)))
        # a "boxes" tab left behind: the restore closes it
        cdp_http("/json/new?http://%s:8511/" % IP_SERVER, "PUT")
        time.sleep(1)
        for f in ripristina(tel, leggi_stato()):
            print("      | %s" % f)
        rimaste = schede()
        esito("the restore closes the tabs towards the boxes and leaves the user's",
              [x["id"] for x in rimaste] == [x["id"] for x in st["schede"]],
              str([x.get("url")[:40] for x in rimaste]))
        log = open(os.path.join(tmp, "adb.log")).read()
        esito("restore: rotation and screen timeout put back",
              "settings put system accelerometer_rotation 1" in log
              and "settings put system user_rotation 0" in log
              and "settings put system screen_off_timeout 60000" in log
              and "wm user-rotation free" in log, "")
        esito("the starting state is closed (restored)", not os.path.exists(STATO))
        esito("fake adb: no command outside the list",
              not re.search(r"\b(am start -a android.intent.action.VIEW|sms|svc wifi|"
                            r"settings put global)", log), "")
    finally:
        if sp:
            sp.spegni()
        chrome.terminate()
        sito.terminate()
        try:
            chrome.wait(10)
        except Exception:                         # noqa: BLE001
            chrome.kill()
        if not o.lascia:
            for _ in range(5):                    # Chrome's children still write for a moment
                shutil.rmtree(tmp, ignore_errors=True)
                if not os.path.exists(tmp):
                    break
                time.sleep(1)
        else:
            nota("left %s" % tmp)
    titolo("DRY RUN: %d/%d green" % (sum(esiti), len(esiti)))
    return 0 if all(esiti) else 1


# ═══════════════════════════════════════════════════════════════════════════
def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("azione", choices=("controlla", "prova", "ripristina", "a-secco"))
    a.add_argument("cosa", nargs="?", default="", help="prova: 1..10 or \"tutte\"")
    a.add_argument("--desktop", default="", help="gnome,kde,xfce,lxqt (prova: default gnome)")
    a.add_argument("--giro", default="", help="name of the round (default 19-android-<gpu>)")
    a.add_argument("--senza-guasto", action="store_true")
    a.add_argument("--non-collegare", action="store_true",
                   help="do not try `adb connect`: only the phone already seen")
    a.add_argument("--lascia", action="store_true", help="a-secco: keep the folder")
    o = a.parse_args()
    o.desktop = [x for x in o.desktop.split(",") if x]
    for d in o.desktop:
        if d not in DESKTOP:
            a.error("unknown desktop: %s" % d)
    o.scheda = "ignota"
    if o.azione == "a-secco":
        return a_secco(o)
    tel = Telefono()
    try:
        if o.azione == "controlla":
            return 0 if controlla(tel, o) else 2 if not tel.seriale else 3
        if o.azione == "ripristina":
            st = leggi_stato()
            if not st:
                nota("nothing to restore (%s is missing)" % STATO)
                return 0
            titolo("The phone as I found it (%s)" % st.get("quando"))
            fatto = ripristina(tel, st)
            for f in fatto:
                (no if f.startswith("⛔") else nota)(f)
            return 1 if any(f.startswith("⛔") for f in fatto) else 0
        if o.azione == "prova":
            if not o.cosa:
                a.error("prova <1..10>|tutte")
            trovato, frase = tel.trova(collega=not o.non_collegare)
            if not trovato:
                no(frase)
                return 2
            return prova(tel, o)
    except Fermo as e:
        no(str(e))
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
