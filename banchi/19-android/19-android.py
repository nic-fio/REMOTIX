#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
19-android — THE ANDROID TESTS ON THE REAL PHONE (phase 19 §5 and §5.1)
===========================================================================

From the LAPTOP (where Phonestra's adb key lives):

    bash banchi/19-android/19-android.sh check
    bash banchi/19-android/19-android.sh prova 3                # row 3, on GNOME
    bash banchi/19-android/19-android.sh prova 1 --desktop kde
    bash banchi/19-android/19-android.sh prova all_of            # full round + short round
    bash banchi/19-android/19-android.sh restore             # after an interruption
    bash banchi/19-android/19-android.sh a-secco                # the bench without a phone

HOW IT IS MADE
  - The tests are those of the SUITE (phase 15), with its judges and its faults:
    they run ON THE SERVER with `15-giro.py --browser phone` ("a red test is
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
    "phone"); evidence (uscita.log, photos of the canvas and of the phone's
    page via CDP) in /media/REMOTIX/misure/fase19-android/giro<lap>/...

⛔ THE PHONE BELONGS TO THE USER (DECISIONI §10.27, fasi/19 §5, memory):
  - ONLY Chrome, ONLY towards the server's boxes (https://192.168.0.2:8511-8514,
    and 8611-8614 for the network test); never other apps, settings, messages;
  - NEVER during a call: `dumpsys telephony.registry`, one line
    `mCallState=` per SIM, any `mCallState=[12]` = wait;
  - it is left AS IT WAS FOUND: the user's Chrome tabs are recorded at the start and
    not touched; ours are closed; rotation and screen timeout
    go back to how they were; if Chrome was closed, it is closed again.  The starting
    state lives in ~/.cache/remotix-19-android/stato.json until it is
    restored (and `restore` puts it back even after an interruption).
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

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
HOME_DIR = os.path.expanduser("~")

ADB = os.environ.get("REMOTIX_ADB", "adb")
KEY = os.environ.get("ADB_VENDOR_KEYS") or os.path.join(HOME_DIR, ".config/Phonestra/adbkey")
PHONES = os.path.join(HOME_DIR, ".config/Phonestra/telefoni.toml")
HOST = os.environ.get("REMOTIX_HOST", "nicfio@192.168.0.2")
IP_SERVER = os.environ.get("REMOTIX_PHONE_HOST", "192.168.0.2")
CHECK = os.environ.get("REMOTIX_CHECK_ANDROID", "/media/REMOTIX/src/controllo-android")
MEASURES = os.environ.get("REMOTIX_MEASURES_ANDROID", "/media/REMOTIX/misure/fase19-android")
CDP_HERE, ENDPOINT_HERE = 9333, 9334          # on the laptop
CDP_LA, ENDPOINT_THERE = 19333, 19334          # on the server, at the end of the tunnel
CHROME = "com.android.chrome"
CHROME_MAIN = CHROME + "/com.google.android.apps.chrome.Main"
STATE_DIR = os.path.join(HOME_DIR, ".cache", "remotix-19-android")
STATE = os.path.join(STATE_DIR, "stato.json")
CALL_WAIT_S = int(os.environ.get("REMOTIX_CALL_WAIT_S", "1200"))
SCREEN_ON_MS = 30 * 60 * 1000
BOX_PORTS = (8511, 8512, 8513, 8514)
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
FULL_ROUND = ("gnome", tuple(range(1, 11)))
SHORT_ROUND = (("kde", "xfce", "lxqt"), (1, 2, 6, 9))


# ═══════════════════════════════════════════════════════════════════════════
#  THE WORDS
# ═══════════════════════════════════════════════════════════════════════════
def ok(t):
    print("    \033[1;32mOK\033[0m  %s" % t, flush=True)


def no(t):
    print("    \033[1;31m⛔\033[0m  %s" % t, flush=True)


def remark(t):
    print("    --  %s" % t, flush=True)


def heading(t):
    print("\n\033[1m== %s\033[0m" % t, flush=True)


class Stopped(Exception):
    """We stop, with the sentence for the user."""


# ═══════════════════════════════════════════════════════════════════════════
#  ADB — always and only here, on the laptop
# ═══════════════════════════════════════════════════════════════════════════
class Phone:
    def __init__(self):
        self.serial_number = None
        self._lock = threading.Lock()

    def _adb(self, *v, t=30, serial_number=True):
        amb = dict(os.environ, ADB_VENDOR_KEYS=KEY)
        cmd = [ADB] + (["-s", self.serial_number] if (serial_number and self.serial_number) else []) + list(v)
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, errors="replace",
                               timeout=t, env=amb)
            return r.returncode, (r.stdout or "") + (r.stderr or "")
        except FileNotFoundError:
            return 127, "adb is missing (%s)" % ADB
        except subprocess.TimeoutExpired:
            return 124, "adb did not answer in %d s" % t

    def sh(self, row, t=30):
        with self._lock:
            return self._adb("shell", row, t=t)

    # -- finding it ----------------------------------------------------------
    def seen_items(self):
        c, t = self._adb("devices", serial_number=False, t=15)
        if c != 0:
            return None, t.strip()
        el = []
        for r in t.splitlines()[1:]:
            p = r.split()
            if len(p) >= 2 and p[1] == "device" and not p[0].startswith("emulator-"):
                el.append(p[0])
        return el, t.strip()

    def known_address(self):
        """The last address Phonestra wrote (ip:port), or REMOTIX_PHONE."""
        if os.environ.get("REMOTIX_PHONE"):
            return os.environ["REMOTIX_PHONE"]
        try:
            m = re.search(r'^ultimo_indirizzo\s*=\s*"([^"]+)"', open(PHONES).read(), re.M)
            return m.group(1) if m else None
        except OSError:
            return None

    def find(self, connect=True):
        """Returns (True, sentence) if the phone is seen by adb."""
        el, raw = self.seen_items()
        if el is None:
            return False, "adb is not answering: %s" % raw[-200:]
        addr = self.known_address()
        if not el and connect and addr:
            if not os.path.exists(KEY):
                return False, "phone not seen, and Phonestra's key is missing (%s)" % KEY
            _c, t = self._adb("connect", addr, serial_number=False, t=20)
            remark("adb connect %s: %s" % (addr, t.strip()[-120:]))
            el, raw = self.seen_items()
            el = el or []
        if not el:
            return False, ("phone not seen by adb%s.  Open Phonestra on the laptop (wireless "
                           "adb with the phone on and on the same network), then run again."
                           % (" (tried %s)" % addr if (connect and addr) else ""))
        chosen = None
        if len(el) == 1:
            chosen = el[0]
        else:
            ip = (addr or "").split(":")[0]
            neighbors = [s for s in el if ip and s.startswith(ip + ":")]
            if len(neighbors) == 1:
                chosen = neighbors[0]
        if not chosen:
            return False, "more than one device seen by adb (%s): REMOTIX_PHONE=<serial>" % el
        self.serial_number = chosen
        return True, chosen

    # -- the call ------------------------------------------------------------
    def call(self):
        """(True|False|None, detail): None = unreadable (and then we wait)."""
        c, t = self.sh("dumpsys telephony.registry", t=20)
        if c != 0 or "mCallState=" not in t:
            return None, "call state unreadable: %s" % t.strip()[-120:]
        ongoing = re.findall(r"mCallState=[12]", t)
        return bool(ongoing), "%d mCallState lines, active: %s" % (
            len(re.findall(r"mCallState=", t)), ongoing or "none")

    def wait_call_end(self, ceiling=None, speaks=True):
        """True if (by now) no call; False if after `ceiling` s there still is one."""
        ceiling = CALL_WAIT_S if ceiling is None else ceiling
        t0 = time.time()
        said = False
        while True:
            c, d = self.call()
            if c is False:
                if said and speaks:
                    remark("📞 call ended after %.0f s: resuming" % (time.time() - t0))
                return True
            if speaks and not said:
                remark("📞 %s — WAITING (no gesture on the phone)" % (
                    "call in progress" if c else d))
                said = True
            if time.time() - t0 >= ceiling:
                return False
            time.sleep(max(0.5, min(10, ceiling - (time.time() - t0))))

    # -- the on-screen keyboard --------------------------------------------
    def keyboard(self):
        """(True|False|None, detail): is the on-screen keyboard open?  The input
        method manager says so (`mInputShown`), not the page: it is the fact
        the user sees ("keyboard only on request", DECISIONI §10.28)."""
        c, t = self.sh("dumpsys input_method | grep -m1 mInputShown=", t=15)
        m = re.search(r"mInputShown=(true|false)", t)
        if c != 0 or not m:
            return None, "keyboard state unreadable: %s" % t.strip()[-120:]
        return m.group(1) == "true", m.group(0)

    # -- the screen ----------------------------------------------------------
    def display_screen(self):
        """(on, unlocked, sentence)."""
        _c, p = self.sh("dumpsys power | grep -m1 mWakefulness=", t=15)
        lit = "mWakefulness=Awake" in p
        _c, w = self.sh("dumpsys window | grep -E 'mDreamingLockscreen|isKeyguardShowing|"
                        "mKeyguardShowing|mShowingLockscreen' | head -5", t=15)
        blocked = bool(re.search(r"(mDreamingLockscreen|isKeyguardShowing|mKeyguardShowing|"
                                  r"mShowingLockscreen)=true", w))
        return lit, not blocked, "%s, %s" % ("on" if lit else "OFF",
                                                  "locked" if blocked else "unlocked")

    def chrome_version(self):
        _c, t = self.sh("dumpsys package %s | grep -m1 versionName=" % CHROME, t=20)
        m = re.search(r"versionName=(\S+)", t)
        return m.group(1) if m else None

    def chrome_on(self):
        _c, t = self.sh("pidof %s" % CHROME, t=10)
        return bool(t.strip()) and t.strip().split()[0].isdigit()

    def chrome_in_front(self):
        _c, t = self.sh("dumpsys activity activities | grep -m1 -E "
                        "'topResumedActivity|mResumedActivity'", t=15)
        return CHROME in t

    def stage(self):
        _c, m = self.sh("getprop ro.product.manufacturer; getprop ro.product.model; "
                        "getprop ro.build.version.release", t=10)
        p = (m.split("\n") + ["", "", ""])[:3]
        return "Chrome %s on Android %s · %s %s (real phone, Wi-Fi)" % (
            self.chrome_version() or "?", p[2].strip(), p[0].strip(), p[1].strip())

    def screen_size(self):
        _c, t = self.sh("wm size", t=10)
        m = re.findall(r"(\d+)x(\d+)", t)
        return tuple(int(v) for v in m[-1]) if m else None

    def forward(self, port=CDP_HERE):
        return self._adb("forward", "tcp:%d" % port, "localabstract:chrome_devtools_remote")

    def via_forward(self, port=CDP_HERE):
        return self._adb("forward", "--remove", "tcp:%d" % port)

    def setting(self, space, label_name):
        _c, t = self.sh("settings get %s %s" % (space, label_name), t=10)
        return t.strip()

    def put(self, space, label_name, value_v):
        if value_v in (None, "", "null"):
            return self.sh("settings delete %s %s" % (space, label_name), t=10)
        return self.sh("settings put %s %s %s" % (space, label_name, shlex.quote(str(value_v))), t=10)


# ═══════════════════════════════════════════════════════════════════════════
#  THE PHONE'S CHROME, SEEN THROUGH THE PROTOCOL (via adb forward)
# ═══════════════════════════════════════════════════════════════════════════
def cdp_http(fpath, meth="GET", port=CDP_HERE, ceiling=8):
    rq = urllib.request.Request("http://127.0.0.1:%d%s" % (port, fpath), method=meth)
    with urllib.request.urlopen(rq, timeout=ceiling) as r:
        t = r.read().decode()
    try:
        return json.loads(t)
    except ValueError:
        return t


def cards(port=CDP_HERE):
    return [x for x in cdp_http("/json/list", port=port) if x.get("type") == "page"]


def is_from_boxes(url):
    u = urllib.parse.urlsplit(url or "")
    return u.hostname == IP_SERVER


def close_tab(sid, port=CDP_HERE):
    for m in ("PUT", "GET"):
        try:
            cdp_http("/json/close/%s" % sid, m, port=port)
            return True
        except Exception:                         # noqa: BLE001
            continue
    return False


def wait_devtools(port=CDP_HERE, ceiling=25):
    fine = time.time() + ceiling
    last = ""
    while time.time() < fine:
        try:
            return cdp_http("/json/version", port=port)
        except Exception as e:                    # noqa: BLE001
            last = str(e)
            time.sleep(1)
    raise Stopped("DevTools of the phone's Chrome not reachable: %s" % last)


# ═══════════════════════════════════════════════════════════════════════════
#  THE STARTING STATE ("as I found it")
# ═══════════════════════════════════════════════════════════════════════════
def read_state():
    try:
        return json.load(open(STATE))
    except (OSError, ValueError):
        return None


def write_state(st):
    os.makedirs(STATE_DIR, exist_ok=True)
    tmp = STATE + ".fresh"
    with open(tmp, "w") as f:
        json.dump(st, f, indent=1, ensure_ascii=False)
    os.replace(tmp, STATE)


def annotate_start(tel):
    st = {"when": datetime.datetime.now().isoformat(timespec="seconds"),
          "serial_number": tel.serial_number,
          "chrome_on": tel.chrome_on(),
          "rotazione": {"accelerometer_rotation": tel.setting("system",
                                                                   "accelerometer_rotation"),
                        "user_rotation": tel.setting("system", "user_rotation")},
          "spegnimento_ms": tel.setting("system", "screen_off_timeout"),
          "cards": [], "toccato": {}}
    if st["chrome_on"]:
        tel.forward()
        try:
            wait_devtools(ceiling=10)
            st["cards"] = [{"id": x.get("id"), "url": x.get("url"), "title": x.get("title")}
                            for x in cards()]
        except Exception as e:                    # noqa: BLE001
            st["schede_errore"] = str(e)
    write_state(st)
    return st


def restore(tel, st, speaks=True):
    """The phone as we found it.  Returns the sentences of what was done."""
    finished = []
    if not st:
        return ["no state to restore"]
    if not tel.serial_number:
        t_ok, _ = tel.find(connect=False)
        if not t_ok:
            return ["⛔ phone not seen: NOT restored (the state stays in %s)" % STATE]
    if not tel.wait_call_end(speaks=speaks):
        return ["⛔ call in progress for too long: NOT restored (run `restore` again)"]
    their = {x["id"] for x in st.get("cards", [])}
    if tel.chrome_on():
        tel.forward()
        try:
            wait_devtools(ceiling=10)
            closed = 0
            for x in cards():
                if x.get("id") not in their and is_from_boxes(x.get("url")):
                    closed += close_tab(x["id"])
            finished.append("closed %d tabs of ours (towards the boxes)" % closed)
            now = {x.get("id") for x in cards()}
            lost = [x for x in st.get("cards", []) if x["id"] not in now]
            if lost and st.get("toccato", {}).get("chrome_ucciso"):
                # after a force-stop Chrome reopens the tabs with new identifiers:
                # the addresses are compared
                urls = [x.get("url") for x in cards()]
                lost = [x for x in lost if x.get("url") not in urls]
            if lost:
                finished.append("⚠ user's tabs I cannot find again: %s"
                             % [x.get("url") for x in lost])
            else:
                finished.append("the user's %d tabs are all there" % len(their))
        except Exception as e:                    # noqa: BLE001
            finished.append("⚠ tabs not checked: %s" % e)
    touch = st.get("toccato", {})
    if touch.get("rotazione"):
        r = st["rotazione"]
        tel.sh("wm user-rotation free 2>/dev/null; true", t=10)
        tel.put("system", "user_rotation", r.get("user_rotation"))
        tel.put("system", "accelerometer_rotation", r.get("accelerometer_rotation"))
        finished.append("rotation restored: automatic=%s, orientation=%s" % (
            r.get("accelerometer_rotation"), r.get("user_rotation")))
    if touch.get("spegnimento"):
        tel.put("system", "screen_off_timeout", st.get("spegnimento_ms"))
        finished.append("screen timeout restored to %s ms" % st.get("spegnimento_ms"))
    if not st.get("chrome_on") and tel.chrome_on():
        tel.sh("am force-stop %s" % CHROME, t=15)
        finished.append("Chrome closed again (it was closed when I arrived)")
    tel.via_forward()
    try:
        os.replace(STATE, STATE + ".ripristinato")
    except OSError:
        pass
    return finished


# ═══════════════════════════════════════════════════════════════════════════
#  THE COUNTER: the only questions that reach adb from the server
# ═══════════════════════════════════════════════════════════════════════════
class Endpoint:
    def __init__(self, tel, st, port=ENDPOINT_HERE, cdp=CDP_HERE):
        self.tel, self.st, self.port, self.cdp = tel, st, port, cdp
        self.my = set()
        self.diary = []
        self.srv = None

    def mark(self, key_id, value_v=True):
        self.st.setdefault("toccato", {})[key_id] = value_v
        write_state(self.st)

    def write_diary(self, t):
        r = "%s %s" % (time.strftime("%H:%M:%S"), t)
        self.diary.append(r)
        if os.environ.get("REMOTIX_ENDPOINT_SPEAKS") == "1":
            remark("counter: " + t)

    # -- the answers ----------------------------------------------------------
    def guard(self):
        """None if the phone may be touched; otherwise (code, sentence)."""
        if self.tel.wait_call_end():
            return None
        return 409, "call in progress on the phone for more than %d s" % CALL_WAIT_S

    def ready(self):
        g = self.guard()
        if g:
            return g
        fine = time.time() + 180
        said = False
        while True:
            lit, unlocked, sentence = self.tel.display_screen()
            if lit and unlocked:
                break
            if not said:
                remark("🔓 the phone is %s: turn it on and unlock it (waiting 3 minutes)" % sentence)
                said = True
            if time.time() > fine:
                return 423, "phone %s: not touching anything" % sentence
            time.sleep(5)
        if not self.tel.chrome_on() or not self.tel.chrome_in_front():
            self.tel.sh("am start -a android.intent.action.MAIN -c "
                        "android.intent.category.LAUNCHER -n %s" % CHROME_MAIN, t=20)
            self.write_diary("Chrome brought to the front")
        self.tel.forward(self.cdp)
        wait_devtools(self.cdp)
        # the boxes' tabs left over by a killed Chrome (reopened by it): away
        their = {x["id"] for x in self.st.get("cards", [])}
        for x in cards(self.cdp):
            if (x.get("id") not in their and x.get("id") not in self.my
                    and is_from_boxes(x.get("url"))):
                close_tab(x["id"], self.cdp)
                self.write_diary("closed the leftover tab %s" % x.get("url"))
        return 200, {"ready": True}

    def inside_screen(self, *xy):
        m = self.tel.screen_size()
        if not m:
            return False
        side = max(m)
        return all(0 <= v < side for v in xy)

    def reply(self, fpath, d):
        if fpath == "/call":
            g = self.guard()
            return g or (200, {"call": False})
        if fpath == "/ready":
            return self.ready()
        if fpath == "/stage":
            return 200, {"stage": self.tel.stage()}
        if fpath == "/keyboard":
            # ⚠ only a read (`dumpsys`): no gesture, no guard
            is_open, det = self.tel.keyboard()
            if is_open is None:
                return 500, det
            return 200, {"is_open": is_open, "row": det}
        if fpath == "/my":
            self.my.add(d.get("id"))
            return 200, {}
        if fpath == "/non-mia":
            self.my.discard(d.get("id"))
            return 200, {}
        if fpath in ("/touches", "/scroll", "/rotate", "/uccidi-chrome"):
            g = self.guard()
            if g:
                return g
        if fpath == "/touches":
            x, y = int(d["x"]), int(d["y"])
            if not self.inside_screen(x, y):
                return 400, "tap outside the screen: %s" % ((x, y),)
            c, t = self.tel.sh("input tap %d %d" % (x, y), t=15)
            self.write_diary("tap %d,%d" % (x, y))
            return (200, {}) if c == 0 else (500, "input tap: %s" % t[-120:])
        if fpath == "/scroll":
            v = [int(d[k]) for k in ("x1", "y1", "x2", "y2")]
            ms = max(100, min(3000, int(d.get("ms", 500))))
            if not self.inside_screen(*v):
                return 400, "finger outside the screen: %s" % v
            c, t = self.tel.sh("input swipe %d %d %d %d %d" % tuple(v + [ms]), t=15)
            self.write_diary("finger %s in %d ms" % (v, ms))
            return (200, {}) if c == 0 else (500, "input swipe: %s" % t[-120:])
        if fpath == "/rotate":
            return 200, {"said": self.rotate(d.get("which_way", "other_one"))}
        if fpath == "/uccidi-chrome":
            self.tel.sh("am force-stop %s" % CHROME, t=15)
            self.my.clear()
            self.mark("chrome_ucciso")
            self.write_diary("Chrome stopped abruptly (force-stop)")
            return 200, {}
        return 404, "the counter does not know %s" % fpath

    def rotate(self, which_way):
        """departure = portrait; other_one = landscape.  Automatic rotation off
        while the round lasts; `restore` puts it back as it was."""
        self.mark("rotazione")
        n = 0 if which_way == "departure" else 1
        _c, t = self.tel.sh("wm user-rotation lock %d 2>&1" % n, t=10)
        if "rror" in t or "nknown" in t:
            self.tel.put("system", "accelerometer_rotation", "0")
            self.tel.put("system", "user_rotation", str(n))
        else:
            self.tel.put("system", "accelerometer_rotation", "0")
        time.sleep(2.5)
        self.write_diary("rotated: %s" % ("portrait" if n == 0 else "landscape"))
        return "phone %s" % ("portrait" if n == 0 else "landscape")

    # -- the server ------------------------------------------------------------
    def turn_on(self):
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
                    code_v, body_el = sp.reply(self.path.split("?")[0], d)
                except Exception as e:            # noqa: BLE001
                    code_v, body_el = 500, "the counter crashed: %s" % e
                if not isinstance(body_el, dict):
                    body_el = {"reason_text": body_el}
                b = json.dumps(body_el, ensure_ascii=False).encode()
                self.send_response(code_v)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(b)))
                self.end_headers()
                self.wfile.write(b)

        self.srv = http.server.ThreadingHTTPServer(("127.0.0.1", self.port), H)
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()

    def turn_off(self):
        if self.srv:
            self.srv.shutdown()
            self.srv.server_close()


# ═══════════════════════════════════════════════════════════════════════════
#  THE SERVER (read only, except the tests themselves)
# ═══════════════════════════════════════════════════════════════════════════
def ssh(row, t=60, keep_going=None):
    cmd = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=8"]
    if keep_going:
        cmd += ["-o", "ExitOnForwardFailure=yes"] + keep_going
    try:
        r = subprocess.run(cmd + [HOST, row], capture_output=True, text=True,
                           errors="replace", timeout=t)
        out = "\n".join(x for x in (r.stdout + r.stderr).splitlines() if not x.startswith("tput"))
        return r.returncode, out
    except subprocess.TimeoutExpired:
        return 124, "ssh: no answer in %d s" % t


# ⚠ /sys inside the box is the host's (renderD128 = the Intel even when the Radeon
#   is mapped inside): the GPU is read from the route the server declared in the log.
CARD_SH = ("P=$(awk '/^pass:/{print $2; exit}' $HOME/SERVER.ssh 2>/dev/null); "
             "printf '%s\\n' \"$P\" | sudo -S -p '' podman exec rete11-gnome "
             "sh -c \"grep -ohE 'route (vulkan|vaapi)' /var/lib/rete11/registro.log | tail -1\"")


def card_of_boxes():
    _c, t = ssh(CARD_SH, 30)
    if "route vaapi" in t:
        return "intel", "Intel UHD 770 (VA-API)"
    if "route vulkan" in t:
        return "radeon", "AMD RX 6800 (Vulkan)"
    return "ignota", "GPU not read (%s)" % t.strip()[-60:]


# ═══════════════════════════════════════════════════════════════════════════
#  CHECK
# ═══════════════════════════════════════════════════════════════════════════
def check(tel, o):
    """Returns True if we can start.  The first missing check stops everything."""
    heading("The phone")
    located, sentence = tel.find(connect=not o.no_connect)
    if not located:
        no(sentence)
        return False
    ok("adb sees the phone: %s" % sentence)
    c, d = tel.call()
    if c is None:
        no(d)
        return False
    if c:
        no("📞 call in progress (%s): wait for it to end, then run again" % d)
        return False
    ok("no call (%s)" % d)
    lit, unlocked, fr = tel.display_screen()
    (ok if (lit and unlocked) else no)("screen %s" % fr)
    v = tel.chrome_version()
    if not v:
        no("Chrome (%s) is not on the phone" % CHROME)
        return False
    ok("Chrome %s" % v)
    if tel.chrome_on():
        tel.forward()
        try:
            ver = wait_devtools(ceiling=10)
            ok("DevTools reachable: %s" % ver.get("Browser"))
            sc = cards()
            ok("user's open tabs: %d (not touched)" % len(sc))
        except Stopped as e:
            no("%s — on the phone: Settings › Developer options › USB debugging on?" % e)
            return False
        finally:
            tel.via_forward()
    else:
        remark("Chrome closed: the test opens it and closes it again at the end (DevTools is checked then)")
    heading("The boxes seen from the phone")
    _c, ping = tel.sh("ping -c 1 -W 2 %s >/dev/null 2>&1 && echo si || echo no" % IP_SERVER,
                      t=10)
    (ok if "si" in ping else no)("the server %s %s from the phone (ping)"
                                 % (IP_SERVER, "answers" if "si" in ping else "does NOT answer"))
    # ⚠ the ports are checked from the LAPTOP (same network as the phone): on the phone
    #   there is no reliable tool without installing anything; test 1
    #   crosses them anyway from the phone's Chrome
    views = {}
    for p in BOX_PORTS:
        try:
            socket.create_connection((IP_SERVER, p), timeout=3).close()
            views[str(p)] = "si"
        except OSError as e:
            views[str(p)] = "no"
            remark("port %d: %s" % (p, e))
        (ok if views[str(p)] == "si" else no)("box on port %d %s" % (
            p, "listening" if views[str(p)] == "si" else "does NOT answer"))
    heading("The server")
    c, t = ssh("echo alive; pgrep -af '15-giro.py|16-salita.py' | grep -v pgrep | head -3", 20)
    if c != 0 or "alive" not in t:
        no("ssh %s does not work: %s" % (HOST, t[-160:]))
        return False
    ok("ssh %s" % HOST)
    others = [r for r in t.splitlines()[1:] if r.strip()]
    if others:
        no("a round is already running on the server (%s): the boxes are its own, wait" % others[0][:100])
        return False
    ok("no other round on the server")
    s, sentence = card_of_boxes()
    ok("boxes on the GPU: %s" % sentence)
    o.gpu_card = s
    ready = (lit and unlocked and "si" in ping
              and all(views.get(str(p)) == "si" for p in BOX_PORTS))
    if not ready:
        no("not starting: fix the red lines")
    else:
        heading("Ready")
    return ready


# ═══════════════════════════════════════════════════════════════════════════
#  TEST
# ═══════════════════════════════════════════════════════════════════════════
def piano(o):
    if o.what == "all_of":
        p = [(FULL_ROUND[0], n) for n in FULL_ROUND[1]]
        for d in SHORT_ROUND[0]:
            p += [(d, n) for n in SHORT_ROUND[1]]
        if o.desktop:
            p = [x for x in p if x[0] in o.desktop]
        return p
    n = int(o.what)
    if n not in PROVE:
        raise Stopped("tests go from 1 to 10 (fasi/19-nvidia.md §5.1)")
    return [(d, n) for d in (o.desktop or ["gnome"])]


def push_benches():
    amb = dict(os.environ, REMOTIX_CHECK=CHECK, REMOTIX_HOST=HOST)
    r = subprocess.run(["bash", os.path.join(ROOT, "banchi/15-suite/15-porta.sh")],
                       capture_output=True, text=True, env=amb, timeout=300)
    if r.returncode != 0:
        raise Stopped("the benches do not reach the server: %s" % (r.stdout + r.stderr)[-300:])
    remark((r.stdout.strip().splitlines() or ["?"])[-1])


def log_lines(lap, desktop, prove):
    c, t = ssh("grep -F '\"lap\": \"%s\"' %s/registro.jsonl 2>/dev/null | grep -F "
               "'\"desktop\": \"%s\"' | tail -200" % (lap, MEASURES, desktop), 30)
    line_list = []
    for x in t.splitlines():
        try:
            r = json.loads(x)
        except ValueError:
            continue
        if any(f in r.get("prova", "") for f in prove):
            line_list.append(r)
    # the last run of each test
    last = {}
    for r in line_list:
        last[r["prova"]] = max(last.get(r["prova"], ""), r.get("start", ""))
    return [r for r in line_list if r.get("start") == last.get(r["prova"])]


def one_line(o, tel, sp, d, n, lap, system_wide):
    what, prove = PROVE[n]
    heading("Test %d · %s · %s" % (n, d.upper(), what))
    if not tel.wait_call_end():
        return [{"outcome": "BLOCKED", "rationale": "call in progress for too long", "function": "?"}]
    if n == 7:
        sp.rotate("departure")
    amb = {"REMOTIX_MEASURES_15": MEASURES, "REMOTIX_SYSTEM_15": system_wide,
           "REMOTIX_PHONE_CDP": str(CDP_LA), "REMOTIX_PHONE_ENDPOINT": str(ENDPOINT_THERE),
           "REMOTIX_PHONE_HOST": IP_SERVER}
    row = ("cd %s/banchi/15-suite && env %s python3 15-giro.py --lap %s --desktop %s "
            "--browser phone --prove %s%s" % (
                CHECK, " ".join("%s=%s" % (k, shlex.quote(v)) for k, v in amb.items()),
                shlex.quote(lap), d, ",".join(prove), " --no-fault" if o.no_fault else ""))
    keep_going = ["-R", "%d:127.0.0.1:%d" % (CDP_LA, CDP_HERE),
              "-R", "%d:127.0.0.1:%d" % (ENDPOINT_THERE, ENDPOINT_HERE)]
    t0 = time.time()
    try:
        c, out = ssh(row, t=60 * 12 * len(prove), keep_going=keep_going)
    finally:
        if n == 7:
            sp.rotate("departure")
    for r in out.splitlines():
        if r.startswith(("[", "⛔", "⭐ ROUND", "   server")):
            remark(r)
    line_list = log_lines(lap, d, prove)
    if not line_list:
        no("no line in the log (code %s): %s" % (c, out[-400:]))
    for r in line_list:
        sign = {"PASS": "⭐", "FAIL": "⛔", "BLOCKED": "⚠"}.get(r["outcome"], "?")
        print("    %s %-6s %-6s [%s] %s" % (sign, r["function"], r["outcome"], r["passed"],
                                            (r.get("rationale") or "")[:150]), flush=True)
    remark("%.0f s" % (time.time() - t0))
    return line_list


def prova(tel, o):
    if read_state():
        raise Stopped("there is an unrestored starting state (%s): first "
                    "`19-android.sh restore`" % STATE)
    if not check(tel, o):
        return 3
    pi = piano(o)
    heading("The plan: %s" % ", ".join("%s/%d" % x for x in pi))
    push_benches()
    st = annotate_start(tel)
    ok("recorded the phone as I found it: Chrome %s, %d tabs, rotation %s, "
       "screen timeout %s ms" % ("open" if st["chrome_on"] else "closed", len(st["cards"]),
                              st["rotazione"], st["spegnimento_ms"]))
    sp = Endpoint(tel, st)
    lap = o.lap or "19-android-%s" % o.gpu_card
    system_wide = "%s · boxes on %s · server 192.168.0.2" % (
        tel.stage(), {"intel": "Intel UHD 770 (VA-API)", "radeon": "AMD RX 6800 (Vulkan)"}
        .get(o.gpu_card, o.gpu_card))
    all_of = []
    interrupted = []

    def halt(_n, _f):
        interrupted.append(1)
        raise KeyboardInterrupt
    signal.signal(signal.SIGTERM, halt)
    try:
        sp.turn_on()
        tel.forward()
        # the screen must not turn off halfway through a test (restored at the end)
        tel.put("system", "screen_off_timeout", str(SCREEN_ON_MS))
        sp.mark("spegnimento")
        for d, n in pi:
            line_list = one_line(o, tel, sp, d, n, lap, system_wide)
            if any("call in progress" in (r.get("rationale") or "") and r["outcome"] == "BLOCKED"
                   for r in line_list):
                remark("📞 a call interrupted test %d: redoing it" % n)
                tel.wait_call_end()
                line_list = one_line(o, tel, sp, d, n, lap, system_wide)
            all_of += [(d, n, r) for r in line_list]
    except KeyboardInterrupt:
        no("interrupted: putting the phone back in order")
    finally:
        sp.turn_off()
        heading("The phone as I found it")
        for f in restore(tel, read_state() or st):
            (no if f.startswith("⛔") else remark)(f)
    heading("Summary (round %s)" % lap)
    count = {}
    for d, n, r in all_of:
        count[r["outcome"]] = count.get(r["outcome"], 0) + 1
    print("    %s" % " ".join("%s=%d" % kv for kv in sorted(count.items())))
    for d, n, r in all_of:
        if r["outcome"] != "PASS":
            print("    %s test %d %s %s [%s]: %s" % (d, n, r["function"], r["outcome"],
                                                     r["passed"], (r.get("rationale") or "")[:200]))
    remark("log: %s:%s/registro.jsonl · evidence in %s/lap%s/" % (HOST, MEASURES, MEASURES, lap))
    remark("report: ssh %s python3 %s/banchi/15-suite/15-rapporto.py --logbook "
         "%s/registro.jsonl --lap %s --body_text" % (HOST, CHECK, MEASURES, lap))
    if interrupted or not all_of:
        return 3
    return 1 if count.get("FAIL") else (3 if count.get("BLOCKED") else 0)


# ═══════════════════════════════════════════════════════════════════════════
#  DRY RUN: the whole bench without phone and without server
# ═══════════════════════════════════════════════════════════════════════════
FAKE_ADB = r"""#!/bin/bash
# FAKE adb of the dry run: it talks to no phone.
D="$(dirname "$0")"
echo "$*" >> "$D/adb.log"
case "$*" in
  devices*) printf 'List of devices attached\n'; [ -f "$D/seen_v" ] && printf 'fake:5555\tdevice\n'; exit 0;;
  connect*) echo "failed to connect"; exit 1;;
esac
while [ "${1:-}" = "-s" ]; do shift 2; done
case "$1" in
  forward) exit 0;;
  shell) shift; r="$*";;
  *) exit 0;;
esac
case "$r" in
  *telephony.registry*) if [ -f "$D/call" ]; then echo "  mCallState=0"; echo "  mCallState=1"; else echo "  mCallState=0"; echo "  mCallState=0"; fi;;
  *mWakefulness*) echo "  mWakefulness=Awake";;
  *input_method*) if [ -f "$D/keyboard" ]; then echo "  mInputShown=true"; else echo "  mInputShown=false"; fi;;
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

FAKE_PAGE = """<!doctype html><meta charset=utf-8><title>fake box</title>
<style>html,body{margin:0;height:100%;background:#000}#display_screen{width:100vw;height:100vh;display:block}</style>
<canvas id=display_screen width=800 height=500></canvas>
<script>
const c=document.getElementById('display_screen').getContext('2d');
c.fillStyle='#1d6fd6';c.fillRect(0,0,400,250);c.fillStyle='#2bb34a';c.fillRect(400,250,400,250);
window.__visti=[];
for (const t of ['mousedown','keydown','touchstart']) addEventListener(t,e=>__visti.push(t+':'+(e.key||'')),true);
/* a fake trackpad like the real page's (SPECIFICHE §7.1): the finger moves the
   pointer by the same distance, after a 9 px threshold; canvas = glass */
let P=[400,250], down=null, prev=null, moved=false;
addEventListener('touchstart',e=>{const t=e.touches[0];down=[t.clientX,t.clientY];prev=down;moved=false;},true);
addEventListener('touchmove',e=>{const t=e.touches[0];const q=[t.clientX,t.clientY];
  if(!moved&&Math.hypot(q[0]-down[0],q[1]-down[1])>9) moved=true;
  const r=document.getElementById('display_screen').getBoundingClientRect(), kx=r.width/800, ky=r.height/500;
  if(moved){P[0]=Math.min(799,Math.max(0,P[0]+(q[0]-prev[0])/kx));P[1]=Math.min(499,Math.max(0,P[1]+(q[1]-prev[1])/ky));}
  prev=q;},true);
window.REMOTIX={tap:{state:()=>({ptr:P.slice(),in_effect:true}),arrangement:()=>'tap'}};
window.REMOTIX_POINTER={geometry:()=>{const r=document.getElementById('display_screen').getBoundingClientRect();
  return {r:r,bx0:0,by0:0,left_side:r.width/800,sy:r.height/500,vx:1,vy:1,tl:800,ta:500};}};
</script>"""


def dry_run(o):
    """The bench tested WITHOUT a phone: (1) without a device it must say "phone not
    seen" and exit cleanly; (2) the CDP part against a laptop Chrome (throwaway
    profile) on a local page; the counter with a FAKE adb."""
    import importlib.util as iu
    tmp = tempfile.mkdtemp(prefix="remotix-19-secco-")
    fake = os.path.join(tmp, "adb")
    open(fake, "w").write(FAKE_ADB)
    os.chmod(fake, 0o755)
    global ADB, STATE_DIR, STATE, IP_SERVER
    ADB = fake
    # ⛔ today the server and its ports are not touched: the "boxes" are a loopback
    #   address where nobody listens
    IP_SERVER = "127.0.0.9"
    STATE_DIR = os.path.join(tmp, "state")
    STATE = os.path.join(STATE_DIR, "stato.json")
    outcomes = []

    def outcome(what, real, detail=""):
        outcomes.append(real)
        (ok if real else no)("%s%s" % (what, (" — " + detail) if detail else ""))

    heading("DRY RUN 1 — without phone")
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "check"],
                       capture_output=True, text=True,
                       env=dict(os.environ, REMOTIX_ADB=fake, REMOTIX_PHONE="",
                                HOME=tmp), timeout=60)
    print("\n".join("      | " + x for x in r.stdout.strip().splitlines()))
    outcome("\"check\" says phone not seen and exits with 2", r.returncode == 2
          and "phone not seen" in r.stdout, "code %d" % r.returncode)
    r = subprocess.run([sys.executable, os.path.abspath(__file__), "prova", "1"],
                       capture_output=True, text=True,
                       env=dict(os.environ, REMOTIX_ADB=fake, REMOTIX_PHONE="",
                                HOME=tmp), timeout=60)
    outcome("\"prova 1\" stops at the same point, without touching the server",
          r.returncode == 2 and "phone not seen" in r.stdout and "The server" not in r.stdout,
          "code %d" % r.returncode)
    log = open(os.path.join(tmp, "adb.log")).read() if os.path.exists(
        os.path.join(tmp, "adb.log")) else ""
    outcome("adb got only \"devices\" (no connect without key, no shell)",
          all(x.startswith("devices") or x.startswith("connect") for x in log.splitlines())
          and "shell" not in log, log.replace("\n", " | "))

    heading("DRY RUN 2 — the phone driver against a laptop Chrome")
    open(os.path.join(tmp, "seen_v"), "w").close()
    # the "boxes" page, local
    os.makedirs(os.path.join(tmp, "site"))
    open(os.path.join(tmp, "site", "index.html"), "w").write(FAKE_PAGE)
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    site_port = s.getsockname()[1]
    s.close()
    site = subprocess.Popen([sys.executable, "-m", "http.server", str(site_port), "--bind",
                             "127.0.0.1", "--directory", os.path.join(tmp, "site")],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    prof = os.path.join(tmp, "chrome")
    chrome = subprocess.Popen(["google-chrome", "--headless=new",
                               "--remote-debugging-port=%d" % CDP_HERE, "--user-data-dir=" + prof,
                               "--no-first-run", "--no-default-browser-check",
                               "--remote-allow-origins=*", "--window-size=412,915",
                               "data:text/html,<title>user's tab</title><h1>theirs</h1>"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    sp = None
    try:
        wait_devtools(ceiling=30)
        tel = Phone()
        located, fr = tel.find(connect=False)
        outcome("with the fake adb the phone is \"seen\"", located, fr)
        st = annotate_start(tel)
        outcome("user's tabs recorded", len(st["cards"]) == 1,
              str([x["title"] for x in st["cards"]]))
        sp = Endpoint(tel, st)
        sp.turn_on()
        os.environ.update(REMOTIX_PHONE_CDP=str(CDP_HERE), REMOTIX_PHONE_HOST=IP_SERVER,
                          REMOTIX_PHONE_ENDPOINT=str(ENDPOINT_HERE),
                          REMOTIX_PHONE_DRY_RUN="1")
        spec = iu.spec_from_file_location("phone", os.path.join(HERE, "telefono.py"))
        T = iu.module_from_spec(spec)
        spec.loader.exec_module(T)

        class O:
            evidence = os.path.join(tmp, "evidence")
        os.makedirs(O.evidence)
        g = T.PhoneDriver(O())
        outcome("the driver opens a tab of ITS OWN", g.gpu_card["id"] not in
              {x["id"] for x in st["cards"]}, g.gpu_card["id"])
        outcome("stage", "Android 16" in g.stage(), g.stage())
        try:
            g.go_to("https://example.com/")
            outcome("refuses an address outside the boxes", False)
        except RuntimeError as e:
            outcome("refuses an address outside the boxes", "only to the server's boxes" in str(e))
        is_open, reason_text = g.go_to("http://127.0.0.1:%d/" % site_port)
        outcome("goes to the \"box\" (local page)", is_open, reason_text)
        time.sleep(1)
        png, _ = g.snapshot_canvas()
        outcome("photo of the canvas via CDP", bool(png) and png[:4] == b"\x89PNG",
              "%d byte" % len(png or b""))
        g.click(100, 100)
        g.key("ArrowRight")
        g.finger_cdp([(50, 50), (80, 60), (120, 70)])
        seen_items = g.js("return window.__visti")
        outcome("click, key and finger reach the page", seen_items and "mousedown:" in seen_items
              and "keydown:ArrowRight" in seen_items and "touchstart:" in seen_items, str(seen_items))
        touches = g.touches_seen()
        outcome("the touch notebook sees them", len(touches) >= 1, str(touches[:1]))
        # the trackpad pointer brought onto a target, even a near one (wide loop)
        geo = g.js("const P=window.REMOTIX_POINTER,t=document.getElementById('display_screen');"
                   "const q=P.geometry();return {left:q.r.left,top:q.r.top,width:q.r.width,"
                   "height:q.r.height,bx0:0,by0:0,left_side:q.left_side,sy:q.sy,vx:1,vy:1,tl:800,ta:500};")
        e1 = g.move_pointer(geo, geo["width"] * 0.2, geo["height"] * 0.3)
        e2 = g.move_pointer(geo, geo["width"] * 0.2 + 4, geo["height"] * 0.3 - 3)
        outcome("the pointer is brought onto the target (far and at 4 px)",
              e1 is not None and e1 <= 1 and e2 is not None and e2 <= 1,
              "errors %s and %s px" % (e1, e2))
        # the call: with the "call" on the counter must refuse
        open(os.path.join(tmp, "call"), "w").close()
        global CALL_WAIT_S
        old, CALL_WAIT_S = CALL_WAIT_S, 1
        try:
            g.guard(immediately=True)
            outcome("with a call the guard stops the gesture", False)
        except T.CallInProgress as e:
            outcome("with a call the guard stops the gesture (409)", True, str(e))
        try:
            g.click(10, 10)
            outcome("…a click too", False)
        except T.CallInProgress:
            outcome("…a click too", True)
        CALL_WAIT_S = old
        os.remove(os.path.join(tmp, "call"))
        g.guard(immediately=True)
        outcome("once the call is over we resume", True)
        # the on-screen keyboard: the question to the counter and the driver's method
        outcome("keyboard: closed ⇒ \"is_open\" false", g.keyboard_is_open() is False)
        open(os.path.join(tmp, "keyboard"), "w").close()
        outcome("keyboard: open ⇒ \"is_open\" true (dumpsys input_method)",
              g.wait_keyboard(True, 2) is True)
        os.remove(os.path.join(tmp, "keyboard"))
        outcome("keyboard: closed again ⇒ false again", g.wait_keyboard(False, 2) is False)
        outcome("keyboard: the counter asked adb only `dumpsys input_method`",
              "dumpsys input_method | grep -m1 mInputShown=" in
              open(os.path.join(tmp, "adb.log")).read())
        print("      | rotate: %s" % T.orients("other_one"))
        sp.mark("spegnimento")
        g.shut()
        left = cards()
        outcome("our tab closed, the user's is there",
              [x["id"] for x in left] == [x["id"] for x in st["cards"]],
              str([x.get("title") for x in left]))
        outcome("evidence of the closing saved",
              any(f.startswith("telefono-chiusura") for f in os.listdir(O.evidence)),
              str(os.listdir(O.evidence)))
        # a "boxes" tab left behind: the restore closes it
        cdp_http("/json/new?http://%s:8511/" % IP_SERVER, "PUT")
        time.sleep(1)
        for f in restore(tel, read_state()):
            print("      | %s" % f)
        left = cards()
        outcome("the restore closes the tabs towards the boxes and leaves the user's",
              [x["id"] for x in left] == [x["id"] for x in st["cards"]],
              str([x.get("url")[:40] for x in left]))
        log = open(os.path.join(tmp, "adb.log")).read()
        outcome("restore: rotation and screen timeout put back",
              "settings put system accelerometer_rotation 1" in log
              and "settings put system user_rotation 0" in log
              and "settings put system screen_off_timeout 60000" in log
              and "wm user-rotation free" in log, "")
        outcome("the starting state is closed (restored)", not os.path.exists(STATE))
        outcome("fake adb: no command outside the list",
              not re.search(r"\b(am start -a android.intent.action.VIEW|sms|svc wifi|"
                            r"settings put global)", log), "")
    finally:
        if sp:
            sp.turn_off()
        chrome.terminate()
        site.terminate()
        try:
            chrome.wait(10)
        except Exception:                         # noqa: BLE001
            chrome.kill()
        if not o.leave:
            for _ in range(5):                    # Chrome's children still write for a moment
                shutil.rmtree(tmp, ignore_errors=True)
                if not os.path.exists(tmp):
                    break
                time.sleep(1)
        else:
            remark("left %s" % tmp)
    heading("DRY RUN: %d/%d green" % (sum(outcomes), len(outcomes)))
    return 0 if all(outcomes) else 1


# ═══════════════════════════════════════════════════════════════════════════
def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("action", choices=("check", "prova", "restore", "a-secco"))
    a.add_argument("what", nargs="?", default="", help="prova: 1..10 or \"all_of\"")
    a.add_argument("--desktop", default="", help="gnome,kde,xfce,lxqt (prova: default gnome)")
    a.add_argument("--lap", default="", help="name of the round (default 19-android-<gpu>)")
    a.add_argument("--no-fault", action="store_true")
    a.add_argument("--no-connect", action="store_true",
                   help="do not try `adb connect`: only the phone already seen")
    a.add_argument("--leave", action="store_true", help="a-secco: keep the folder")
    o = a.parse_args()
    o.desktop = [x for x in o.desktop.split(",") if x]
    for d in o.desktop:
        if d not in DESKTOP:
            a.error("unknown desktop: %s" % d)
    o.gpu_card = "ignota"
    if o.action == "a-secco":
        return dry_run(o)
    tel = Phone()
    try:
        if o.action == "check":
            return 0 if check(tel, o) else 2 if not tel.serial_number else 3
        if o.action == "restore":
            st = read_state()
            if not st:
                remark("nothing to restore (%s is missing)" % STATE)
                return 0
            heading("The phone as I found it (%s)" % st.get("when"))
            finished = restore(tel, st)
            for f in finished:
                (no if f.startswith("⛔") else remark)(f)
            return 1 if any(f.startswith("⛔") for f in finished) else 0
        if o.action == "prova":
            if not o.what:
                a.error("prova <1..10>|all_of")
            located, sentence = tel.find(connect=not o.no_connect)
            if not located:
                no(sentence)
                return 2
            return prova(tel, o)
    except Stopped as e:
        no(str(e))
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
