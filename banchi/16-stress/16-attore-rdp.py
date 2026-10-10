#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-attore-rdp — A SIMULATED USER IN FRONT OF xrdp (fasi/20-le-prestazioni.md §7)

    python3 16-attore-rdp.py --container_box gnome|kde|xfce|lxqt --username N --display :2NN \\
        --dir DIR --seed S [--largo 3840 --alto 2160] [--video FILE]
    python3 16-attore-rdp.py --check --container_box xfce --display :200 --dir DIRLIV ...
    python3 16-attore-rdp.py --certify

It is the twin of 16-attore.py for the comparison with xrdp: SAME rhythm (Rate, same seeds),
SAME four jobs (16-lavori.py), SAME schema of stato.jsonl / nascita.json /
eventi.jsonl, so that 16-classifica.py --system_wide xrdp reads them.  The client changes:

  box       rete11-<desktop>-xrdp (Contenitore.xrdp): Debian 13's xrdp as it is, the
            desktop on X11
  client    xfreerdp3 /gfx full screen in this user's Xvfb
            (16-compositori-rdp.sh), /sound:sys:fake: the audio travels and is not played
  hands     XTEST on the Xvfb (python-xlib): the input goes THROUGH THE RDP CHANNEL, like that
            of a person in front of FreeRDP
  photo     the whole Xvfb (get_image), 1:1 with the remote desktop
  paints    XDamage on the FreeRDP window: the time of every draw, grouped in
            «bursts» separated by more than 5 ms.  ⭐ It is the measure from the viewer's side.
            ⚠ Two conditions measured on 9 Oct: `damage_query_version()` before
            everything (without it, ZERO events and no error), and the damage on the
            FreeRDP window, not on the root.

stato.jsonl, every 5 s: counts {"painted": CUMULATIVE bursts}, dipinti_s, input [{ok,
latenza_ms, action}], blocco_max_ms (impulse → first draw after it, or the still of the video),
ritardi_ms (the same, one per impulse closed in the interval), ritardi_eco_ms (only the
keys typed where the echo is immediate), work, drop (xfreerdp exited or the window
gone), errors, events.  ⛔ There are NO delivered, salt, holes, audio: xrdp does not send the
frames it cannot (FreeRDP acknowledges them), and has no counters in the page (§7.3).

nascita.json: access_ms = the start of xfreerdp (user and password on the line: no
login screen); primo_fotogramma_ms = the first instant at which the tenant's X session
exists AND the photo is not degenerate (at least 40 distinct colours, the rule of
`desktop_dark_but_alive`); degenerate if at 15 s from access still not (§9).

--check: the reduced short check of §7.3 — one more session (user 99,
profile C), which enters, opens the terminal, types two commands and finds them in the bash
history, and leaves.  Writes DIR/controllo-corto.json in the schema of 16-controllo-corto.py
(outcomes RDP-accesso, RDP-schermo, RDP-tastiera; birth).

Exit code as 16-attore.py: 0 stopped after having worked · 1 access or start
failed · 2 bench error.
"""
import argparse
import importlib.util as _iu
import json
import os
import re
import secrets
import select
import signal
import subprocess
import sys
import threading
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
BENCHES = os.path.dirname(HERE)
DESKTOP = ("gnome", "kde", "xfce", "lxqt")


def _load(label_name, file):
    s = _iu.spec_from_file_location(label_name, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A16 = _load("attore16", os.path.join(HERE, "16-attore.py"))
L = A16.L
Rate, Fine = A16.Rate, A16.Fine
pulse_waits, longest_pause = A16.pulse_waits, A16.longest_pause
outcome_birth, works_after_birth = A16.outcome_birth, A16.works_after_birth
CAP_DEGENERATE_S = A16.CAP_DEGENERATE_S
BURST_S = 0.005             # two draws less than 5 ms apart are the same frame (§7.3)
ALIVE_COLORS = 40              # the rule of desktop_dark_but_alive (12-c20-veri.py)


def _firefox_prefs():
    """The preferences of the inner Firefox: the same as 11-c21 (PREFERENCES), read from the
    file and not imported (that module drags in the browser guides)."""
    try:
        s = open(os.path.join(BENCHES, "11-scatole", "11-c21-sul-bordo-la-forma-cambia.py"),
                 encoding="utf-8").read()
        m = re.search(r'^PREFERENCES = """(.*?)"""', s, re.S | re.M)
        if m:
            return m.group(1)
    except OSError:
        pass
    return 'user_pref("browser.shell.checkDefaultBrowser", false);\n'


def _sudo_password():
    p = os.environ.get("REMOTIX_SUDO_PASSWORD")
    if p is None:
        try:
            for r in open(os.path.expanduser("~/SERVER.ssh")):
                if r.startswith("pass:"):
                    p = r.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    return (p or "") + "\n"


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS (certified)
# ═══════════════════════════════════════════════════════════════════════════
class Bursts:
    """⭐ The XDamage draws ⇒ «bursts» (a FreeRDP frame arrives as several
    rectangles): a draw more than BURST_S after the previous one opens a new burst."""

    def __init__(self, threshold=BURST_S):
        self.threshold, self.last, self.n, self.t = threshold, None, 0, []

    def drawing_v(self, t):
        new_one = self.last is None or t - self.last > self.threshold
        if new_one:
            self.n += 1
            self.t.append(t)
            if len(self.t) > 20000:
                del self.t[:5000]
        self.last = t
        return new_one


def distinct_colors(im, factor=8):
    """How many distinct colours in the photo reduced by `factor` (None if unreadable)."""
    w, h = im.size
    p = im.resize((max(1, w // factor), max(1, h // factor)))
    c = p.getcolors(maxcolors=1 << 20)
    return len(c) if c else None


def key_x(c):
    """The keysym name of a typed character (for XK.string_to_keysym)."""
    return KEY_NAMES.get(c, c)


KEY_NAMES = {" ": "space", "-": "minus", "~": "asciitilde", "/": "slash", "|": "bar",
              "*": "asterisk", ".": "period", "'": "apostrophe", "#": "numbersign",
              "_": "underscore", ",": "comma", "=": "equal", ":": "colon", ">": "greater",
              "<": "less", '"': "quotedbl", "(": "parenleft", ")": "parenright", "$": "dollar",
              "@": "at", "!": "exclam", "?": "question", "+": "plus", "&": "ampersand",
              ";": "semicolon", "\n": "Return", "\t": "Tab", "\\": "backslash",
              "[": "bracketleft", "]": "bracketright", "{": "braceleft", "}": "braceright",
              "%": "percent", "^": "asciicircum", "`": "grave",
              "Enter": "Return", "PageDown": "Next", "PageUp": "Prior", "Escape": "Escape",
              "Delete": "Delete", "Home": "Home", "Control": "Control_L", "Shift": "Shift_L",
              "Alt": "Alt_L"}


def drop_from_log(body_text):
    """Does the xfreerdp log say the connection dropped?  (phrase or None)"""
    for rx in (r"ERRCONNECT_\w+", r"ERRINFO_\w+", r"connection (?:lost|closed|failure)",
               r"Network disconnect", r"freerdp_check_fds\(\) failed"):
        m = re.search(rx, body_text or "", re.I)
        if m:
            return m.group(0)
    return None


def certify():
    troubles = []

    def prova(what, real, det=""):
        print("   %s %s%s" % ("⭐ ok " if real else "⛔ NO ", what, (" — " + det) if det else ""))
        if not real:
            troubles.append(what)

    print("── the bursts")
    r = Bursts()
    for t in (1.000, 1.001, 1.004, 1.040, 1.041, 1.080):
        r.drawing_v(t)
    prova("6 draws in 3 groups ⇒ 3 bursts", r.n == 3 and r.t == [1.000, 1.040, 1.080], str(r.t))
    r = Bursts()
    for k in range(300):
        r.drawing_v(10 + k / 30.0)
    prova("a video at 30 per second ⇒ 30 bursts per second", r.n == 300)
    # ⛔ FAULT: a 50 ms threshold (too wide) merges the video frames
    r = Bursts(threshold=0.05)
    for k in range(300):
        r.drawing_v(10 + k / 30.0)
    prova("FAULT seen: 50 ms threshold ⇒ the 30/s video becomes ONE burst", r.n == 1, str(r.n))
    at, ap = pulse_waits([10.0, 12.0], [10.03, 12.4], 13.0)
    prova("impulse → first draw after: 30 and 400 ms", [round(x, 3) for x in at] == [0.03, 0.4]
          and not ap, str(at))

    print("── the keys")
    prova("space, hyphen, tilde, slash, asterisk", [key_x(c) for c in " -~/*"] ==
          ["space", "minus", "asciitilde", "slash", "asterisk"])
    prova("letters and digits stay themselves", key_x("a") == "a" and key_x("7") == "7")
    prova("Enter, PageDown, PageUp with the X names", key_x("Enter") == "Return"
          and key_x("PageDown") == "Next" and key_x("PageUp") == "Prior")
    # ⛔ FAULT: every character of the jobs' commands has a known name
    from Xlib import XK
    all_v = set("".join(c for c, _p in L.COMMANDS_C) + " #k0123456789" + "".join(L.NOTE_WORDS)
                + "/home/c16001u1/prova16/new_ones")
    unknown = sorted(c for c in all_v if XK.string_to_keysym(key_x(c)) == 0)
    prova("every character of the C commands has a keysym", not unknown, str(unknown))
    prova("FAULT seen: a wrong name ⇒ keysym 0", XK.string_to_keysym("trattino") == 0)

    print("── the photo")
    try:
        from PIL import Image, ImageDraw
        nero = Image.new("RGB", (800, 600), (0, 0, 0))
        prova("all black ⇒ 1 colour (degenerate)", distinct_colors(nero) == 1)
        viva = nero.copy()
        dr = ImageDraw.Draw(viva)
        for i in range(60):
            dr.rectangle([i * 13, 0, i * 13 + 12, 20], fill=(i * 4, 255 - i * 4, (i * 37) % 255))
        prova("a panel of 60 colours ⇒ alive", (distinct_colors(viva) or 0) >= ALIVE_COLORS,
              str(distinct_colors(viva)))
    except ImportError:
        prova("PIL is there", False)

    print("── the drop from the FreeRDP log")
    prova("ERRCONNECT_CONNECT_TRANSPORT_FAILED seen",
          drop_from_log("[ERROR] ... ERRCONNECT_CONNECT_TRANSPORT_FAILED [0x0002000D]")
          == "ERRCONNECT_CONNECT_TRANSPORT_FAILED")
    prova("a clean log ⇒ no drop",
          drop_from_log("[WARN][com.freerdp.core.license] - license binary blob") is None)
    print("── the tenant and the ports")
    prova("tenant as in 16-attore (c16001u1, the check c16099u99)",
          L.tenant_of(1) == "c16001u1" and L.tenant_of(99) == "c16099u99")
    print("⛔ CERTIFICATION FAILED (%d)" % len(troubles) if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE BOX AND THE TENANT'S X SESSION
# ═══════════════════════════════════════════════════════════════════════════
class Box:
    """Root commands in the box, LOCAL (sudo podman exec), like suite.py on the server."""

    def __init__(self, desktop):
        self.label_name = desktop
        self.container = "rete11-%s-xrdp" % desktop

    def inside(self, row, seconds=90):
        try:
            r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", self.container,
                                "sh", "-c", row], input=_sudo_password(), capture_output=True,
                               text=True, errors="replace", timeout=seconds)
        except subprocess.TimeoutExpired:
            return None, "(no answer in %d s)" % seconds
        return r.returncode, (r.stdout + r.stderr).strip()

    def create(self, chi, password):
        return self.inside("useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
                           % (chi, chi, password), 60)

    def clear_out(self, chi):
        self.inside("loginctl terminate-user %s >/dev/null 2>&1; "
                    "pkill -KILL -f 'runuser -u [%s]%s ' 2>/dev/null; "
                    "pkill -KILL -u %s >/dev/null 2>&1; sleep 0.5; "
                    "userdel -r %s >/dev/null 2>&1 || userdel %s >/dev/null 2>&1; "
                    "rm -rf /home/%s" % (chi, chi[0], chi[1:], chi, chi, chi, chi), 90)


X_ENV = (r"(DISPLAY|XAUTHORITY|DBUS_SESSION_BUS_ADDRESS|XDG_[A-Z_]+|LANG|LC_[A-Z]+|PATH|"
              r"DESKTOP_SESSION|KDE_[A-Z_]+|GTK_[A-Z_]+|QT_[A-Z_]+|GNOME_[A-Z_]+|SESSION_MANAGER)")


class XSession:
    """`in_session` of suite.Session, for an X session carried by xrdp: the environment
    (DISPLAY of the tenant's Xorg, XAUTHORITY, the bus) is read from a process
    of the session (/proc/<pid>/environ), without MOZ_ENABLE_WAYLAND."""

    def __init__(self, sc, chi):
        self.sc, self.chi = sc, chi

    def _env(self):
        return ("u=$(id -u %(c)s) || exit 2; p=''; for q in $(pgrep -u $u); do "
                "tr '\\0' '\\n' < /proc/$q/environ 2>/dev/null | grep -q '^DISPLAY=' && p=$q; done; "
                "[ -n \"$p\" ] || { echo 'no X session'; exit 2; }; "
                "amb=$(tr '\\0' '\\n' < /proc/$p/environ | grep -E '^%(r)s=' | tr '\\n' ' '); "
                % {"c": self.chi, "r": X_ENV})

    def ready(self):
        """Is the tenant's X session there (does one of its processes have DISPLAY)?"""
        c, t = self.sc.inside(self._env() + "echo \"$amb\" | grep -o 'DISPLAY=[^ ]*'", 30)
        return c == 0, (t or "").strip()

    def in_session(self, command, seconds=60, background=True):
        body_el = ("runuser -u %(c)s -- env -i $amb HOME=/home/%(c)s USER=%(c)s LOGNAME=%(c)s "
                 "SHELL=/bin/bash sh -c %(q)s" % {"c": self.chi, "q": _q(command)})
        if background:
            body_el = "setsid %s < /dev/null > /home/%s/.c16-%s.log 2>&1 & echo launched" % (
                body_el, self.chi, re.sub(r"\W", "", command.split()[0])[:20])
        return self.sc.inside(self._env() + body_el, seconds)

    def as_user(self, command, seconds=60):
        return self.sc.inside("runuser -u %s -- %s 2>&1" % (self.chi, command), seconds)


# ═══════════════════════════════════════════════════════════════════════════
#  THE XDamage PROBE (a thread of its own, a connection of its own)
# ═══════════════════════════════════════════════════════════════════════════
class Probe(threading.Thread):
    def __init__(self, display_name, win):
        super().__init__(daemon=True)
        from Xlib import display
        from Xlib.ext import damage
        self.d = display.Display(display_name)
        self.d.damage_query_version()                      # ⛔ without it, ZERO events
        w = self.d.create_resource_object("window", win)
        self.dmg = w.damage_create(damage.DamageReportNonEmpty)
        self.d.flush()
        self.r = Bursts()
        self.lock = threading.Lock()
        self.alive = True
        self.failure = None

    def run(self):
        fd = self.d.fileno()
        try:
            while self.alive:
                select.select([fd], [], [], 0.5)
                n = 0
                while self.d.pending_events():
                    self.d.next_event()
                    n += 1
                if n:
                    t = time.time()
                    with self.lock:
                        self.r.drawing_v(t)
                    # NonEmpty: the damage is emptied, so the next draw notifies again
                    self.d.damage_subtract(self.dmg, 0, 0)
                    self.d.flush()
        except Exception as e:                               # noqa: BLE001
            self.failure = repr(e)

    def read_it(self):
        with self.lock:
            return self.r.n, list(self.r.t)

    def halt(self):
        self.alive = False


# ═══════════════════════════════════════════════════════════════════════════
#  THE HANDS — XTEST on the Xvfb (the input goes through the RDP channel)
# ═══════════════════════════════════════════════════════════════════════════
class Hands:
    def __init__(self, expect):
        from Xlib import X, XK, display
        from Xlib.ext import xtest
        self.a, self.X, self.XK, self.xtest = expect, X, XK, xtest
        self.d = display.Display(expect.o.display)
        self.pos = None
        self.pause_ms = 40

    def _kc(self, label_name):
        ks = self.XK.string_to_keysym(key_x(label_name))
        if not ks and len(label_name) == 1:
            ks = ord(label_name)
        kc = self.d.keysym_to_keycode(ks) if ks else 0
        if not kc:
            raise RuntimeError("no key for %r" % label_name)
        shift = self.d.keycode_to_keysym(kc, 0) != ks
        return kc, shift

    def _down(self, kc):
        self.xtest.fake_input(self.d, self.X.KeyPress, kc)
        self.d.sync()
        return time.time()

    def _su(self, kc):
        self.xtest.fake_input(self.d, self.X.KeyRelease, kc)
        self.d.sync()

    def _move(self, x, y):
        self.xtest.fake_input(self.d, self.X.MotionNotify, x=int(x), y=int(y))
        self.d.sync()

    def _limit(self, X, Y):
        tl, ta = self.a.desktop
        return max(1, min(tl - 2, X)), max(1, min(ta - 2, Y))

    def move_to(self, X, Y):
        X, Y = self._limit(X, Y)
        R = self.a.rate
        if self.pos:
            n = R.whole(3, 8)
            for i in range(1, n):
                f = i / float(n)
                self._move(self.pos[0] + (X - self.pos[0]) * f, self.pos[1] + (Y - self.pos[1]) * f)
                time.sleep(R.whole(12, 30) / 1000.0)
        self._move(X, Y)
        time.sleep(R.whole(60, 180) / 1000.0)
        self.pos = (X, Y)
        return time.time()

    def click(self, X, Y, button_code=0, expected_val=False):
        self.move_to(X, Y)
        b = {0: 1, 1: 2, 2: 3}.get(button_code, 1)
        self.xtest.fake_input(self.d, self.X.ButtonPress, b)
        self.d.sync()
        t = time.time()
        time.sleep(self.a.rate.whole(50, 120) / 1000.0)
        self.xtest.fake_input(self.d, self.X.ButtonRelease, b)
        self.d.sync()
        if expected_val:
            self.a.pulse(t)
        self.a.tally("clic_mouse")
        return t

    def scroll_wheel(self, X, Y, ticks, expected_val=False):
        """`ticks` > 0 down (button 5), < 0 up (button 4)."""
        self.move_to(X, Y)
        b = 5 if ticks > 0 else 4
        t = None
        for _ in range(abs(ticks)):
            self.xtest.fake_input(self.d, self.X.ButtonPress, b)
            self.xtest.fake_input(self.d, self.X.ButtonRelease, b)
            self.d.sync()
            t = t or time.time()
            time.sleep(self.a.rate.whole(40, 160) / 1000.0)
        t = t or time.time()
        if expected_val:
            self.a.pulse(t)
        self.a.tally("ticks")
        return t

    def press(self, label_name, expected_val=False):
        kc, shift = self._kc(label_name)
        sh = self._kc("Shift")[0] if shift else None
        if sh:
            self._down(sh)
        t = self._down(kc)
        time.sleep(self.pause_ms / 1000.0)
        self._su(kc)
        if sh:
            self._su(sh)
        time.sleep(self.pause_ms / 1000.0)
        if expected_val:
            self.a.pulse(t)
        return t

    def combo(self, mod, key):
        mods = [self._kc(m)[0] for m in mod]
        kc, _m = self._kc(key.lower() if len(key) == 1 else key)
        for m in mods:
            self._down(m)
            time.sleep(0.02)
        t = self._down(kc)
        time.sleep(self.pause_ms / 1000.0)
        self._su(kc)
        for m in reversed(mods):
            time.sleep(0.02)
            self._su(m)
        return t

    def beat(self, body_text, expected_val=True, echo=False):
        """Every character a real key, with the person's rhythm; every ~1.5 s the heart
        (the state row and the signals).  `echo`: the character appears at once ⇒ its
        impulse also counts among the «echo» delays."""
        R = self.a.rate
        dur = 0.0
        sh = self._kc("Shift")[0]
        for c in body_text:
            ten, bat = R.hold_ms(), R.keystroke_ms()
            kc, shift = self._kc(c)
            if shift:
                self._down(sh)
            t = self._down(kc)
            if expected_val:
                self.a.pulse(t, echo=echo)
            time.sleep(ten / 1000.0)
            self._su(kc)
            if shift:
                self._su(sh)
            time.sleep(max(0.0, bat - ten) / 1000.0)
            dur += bat / 1000.0
            if dur >= 1.5:
                dur = 0.0
                self.a.heart()
        self.a.tally("keys")
        return time.time()


# ═══════════════════════════════════════════════════════════════════════════
#  THE ACTOR
# ═══════════════════════════════════════════════════════════════════════════
class Actor:
    def __init__(self, o):
        self.o = o
        self.n = o.username
        self.profile_v = "C" if o.check else L.profile_of(self.n)
        self.browser = "freerdp"
        self.chi = L.tenant_of(self.n)
        if o.check:
            # ⛔ [M] 9 Oct, test at 2K: with the SAME name at every level xrdp-sesman found again
            #   the session of the previous level (still closing) and reattached to it ⇒
            #   ERRINFO_LOGOFF_BY_USER after 1.5 s.  One name per level, always «…u99»
            #   (16-classifica recognises the check from the tail of the name).
            k = int(re.sub(r"\D", "", str(o.level)) or 0)
            self.chi = "c16%03du99" % (900 + k % 100)
        self.password = "c16-" + secrets.token_hex(8)
        self.internal_port = L.internal_port(o.container_box, self.n)
        self.rate = Rate(o.seed, self.n)
        self.folder = os.path.join(o.dir, "controllo-corto" if o.check else "username-%02d" % self.n)
        os.makedirs(self.folder, exist_ok=True)
        self.f_state = open(os.path.join(self.folder, "stato.jsonl"), "a", buffering=1)
        self.f_events = open(os.path.join(self.folder, "eventi.jsonl"), "a", buffering=1)
        self.sc = Box(o.container_box)
        self.s = XSession(self.sc, self.chi)
        self.version_v = "?"
        self.events_window, self.errors_window = [], []
        self.pulses, self.echo_pulses = [], []
        self.entered = False
        self.desktop = (o.largo, o.alto)
        self.hands = self.probe = self.work = self.rdp = None
        self.win = None
        self.want_photo = self.n_stopped = False
        self.next_state = 0.0
        self.acts, self.done_window = {}, 0
        self.checks, self.ver_window = {"ok": 0, "ko": 0}, []
        self.prev = None
        self.photo_size = None
        self.x = None                          # X connection for the photos
        self.created = False

    # -- the rows --------------------------------------------------------------
    def _head(self, event):
        return {"t": round(time.time(), 3), "username": self.n, "profile_v": self.profile_v,
                "browser": self.browser, "version_v": self.version_v, "tenant": self.chi,
                "event": event}

    def row(self, **fields):
        r = self._head("state")
        r.pop("event")
        r.update(fields)
        self.f_state.write(json.dumps(r, ensure_ascii=False) + "\n")

    def event(self, kind, **fields):
        r = self._head(kind)
        r.update(fields)
        self.f_events.write(json.dumps(r, ensure_ascii=False) + "\n")
        self.events_window.append(r)
        print("   [%02d %s] %s %s" % (self.n, self.profile_v, kind,
                                    json.dumps(fields, ensure_ascii=False)[:240]), flush=True)

    def tally(self, action):
        self.acts[action] = self.acts.get(action, 0) + 1
        self.done_window += 1

    def verify(self, action, ok, lat_ms, det=""):
        self.tally(action)
        self.checks["ok" if ok else "ko"] += 1
        v = {"action": action, "ok": bool(ok),
             "latenza_ms": None if lat_ms is None else round(lat_ms), "det": det}
        self.ver_window.append(v)
        if not ok:
            print("   [%02d %s] ⚠ input NOT verified: %s" % (self.n, self.profile_v, v), flush=True)

    def pulse(self, t, echo=False):
        self.pulses.append(t)
        if echo:
            self.echo_pulses.append(t)

    # -- the heart -------------------------------------------------------------
    def heart(self):
        if self.n_stopped:
            raise Fine("signal")
        if self.want_photo:
            self.want_photo = False
            self.fires()
        if time.time() >= self.next_state:
            self.is_late = time.time() - self.next_state if self.next_state else 0.0
            self.write_state()
            self.next_state = time.time() + 5.0

    def sleeps(self, seconds):
        fine = time.time() + max(0.0, seconds)
        while True:
            self.heart()
            rest = fine - time.time()
            if rest <= 0:
                return
            time.sleep(min(0.25, rest))

    def rdp_alive(self):
        return self.rdp is not None and self.rdp.poll() is None

    def log_rdp(self):
        try:
            return open(os.path.join(self.folder, "xfreerdp.log"), errors="replace").read()[-20000:]
        except OSError:
            return ""

    def write_state(self):
        if self.probe is None:
            return
        now = time.time()
        n, dt_list = self.probe.read_it()
        errors = list(self.errors_window)
        if self.probe.failure:
            errors.append("the XDamage probe has stopped: %s" % self.probe.failure)
        drop = False
        if self.entered and not self.rdp_alive():
            drop = True
            errors.append("xfreerdp exited (code %s): %s" % (
                self.rdp.returncode if self.rdp else None,
                drop_from_log(self.log_rdp()) or "no error line"))
        block, work, delays, echo = None, False, [], []
        if self.profile_v == "D":
            if self.video_in_progress():
                block = longest_pause(dt_list, self.prev[0] if self.prev else now - 5, now)
                work = True
        else:
            delays, self.pulses = pulse_waits(self.pulses, dt_list, now)
            echo, self.echo_pulses = pulse_waits(self.echo_pulses, dt_list, now)
            if delays:
                block, work = max(delays), True
        counts = {"painted": n}
        fields = {"counts": counts, "input": self.ver_window,
                 "blocco_max_ms": None if block is None else round(block * 1000),
                 "ritardi_ms": [round(x * 1000, 1) for x in delays],
                 "ritardi_eco_ms": [round(x * 1000, 1) for x in echo],
                 "work": work, "drop": drop, "errors": errors,
                 "session_v": self.rdp_alive(), "system_wide": "xrdp"}
        if self.prev:
            dt = now - self.prev[0]
            fields["delta"] = {"painted": n - self.prev[1], "s": round(dt, 2)}
            if dt > 0:
                fields["dipinti_s"] = round((n - self.prev[1]) / dt, 2)
        self.prev = (now, n)
        fields["in_ritardo_s"] = round(getattr(self, "is_late", 0.0), 2)
        fields.update({"acts": dict(self.acts), "azioni_finestra": self.done_window,
                      "checks": dict(self.checks)})
        if self.work is not None:
            try:
                fields["dettagli_lavoro"] = self.work.extra()
            except Exception as e:                  # noqa: BLE001
                fields["dettagli_lavoro"] = {"failure": str(e)[:200]}
        if self.events_window:
            fields["events"] = self.events_window
        self.done_window = 0
        self.ver_window, self.errors_window, self.events_window = [], [], []
        self.row(**fields)

    def video_in_progress(self):
        v = getattr(self.work, "last_video", None) or {}
        return self.entered and v.get("state") == 1

    # -- the photos ------------------------------------------------------------
    def photo_pil(self):
        from PIL import Image
        from Xlib import X, display
        try:
            if self.x is None:
                self.x = display.Display(self.o.display)
            r = self.x.screen().root
            g = r.get_geometry()
            img = r.get_image(0, 0, g.width, g.height, X.ZPixmap, 0xffffffff)
            im = Image.frombytes("RGB", (g.width, g.height), img.data, "raw", "BGRX")
        except Exception:                            # noqa: BLE001
            return None
        self.photo_size = im.size
        return im

    def fires(self):
        t = time.time()
        im = self.photo_pil()
        if im is None:
            self.event("picture", ok=False, reason_text="the Xvfb cannot be photographed")
            return
        f = os.path.join(self.folder, "picture-%d.png" % int(t * 1000))
        im.save(f)
        self.event("picture", ok=True, file=f, ms=round((time.time() - t) * 1000))

    def photo_to_desktop(self, r):
        """⭐ The photo is the Xvfb, and FreeRDP is full screen: 1:1 with the remote desktop."""
        if not r:
            return None
        tl, ta = self.desktop
        return (max(0, r[0]), max(0, r[1]), min(tl, r[2]), min(ta, r[3]))

    def internal_preferences(self):
        return _firefox_prefs()

    # -- the client ------------------------------------------------------------
    def search_window(self):
        from Xlib import display
        if self.x is None:
            self.x = display.Display(self.o.display)
        for w in self.x.screen().root.query_tree().children:
            try:
                cl = w.get_wm_class() or ()
            except Exception:                        # noqa: BLE001
                continue
            if any("remotix-rdp" in (c or "") for c in cl):
                return w.id
        return None

    def turn_on_rdp(self):
        cmd = ["xfreerdp3", "/v:127.0.0.1", "/u:%s" % self.chi, "/p:%s" % self.password,
               "/cert:ignore", "/gfx", "/f", "/sound:sys:fake",
               "/wm-class:remotix-rdp-%02d" % self.n]
        amb = dict(os.environ, DISPLAY=self.o.display)
        amb.pop("WAYLAND_DISPLAY", None)
        log = open(os.path.join(self.folder, "xfreerdp.log"), "a")
        log.write("=== %s\n" % time.strftime("%F %T"))
        log.flush()

        def oom():
            try:
                open("/proc/self/oom_score_adj", "w").write("800")
            except OSError:
                pass
        self.rdp = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=amb,
                                    stdin=subprocess.DEVNULL, start_new_session=True,
                                    preexec_fn=oom)

    def enter(self):
        o = self.o
        n = {"tenant": self.chi, "browser": self.browser, "version_v": self.version_v,
             "container_box": o.container_box, "system_wide": "xrdp", "gauge": [o.largo, o.alto]}
        t0 = time.time()
        self.turn_on_rdp()
        n["access_ms"] = round(t0 * 1000)
        # the FreeRDP window, then the probe
        while time.time() < t0 + o.cap_s and self.win is None:
            if not self.rdp_alive():
                c = drop_from_log(self.log_rdp())
                n.update(outcome="refusal" if c and "AUTH" in c.upper() else "nessun_fotogramma",
                         motivo="xfreerdp exited before the window: %s" % c)
                return n
            self.win = self.search_window()
            if self.n_stopped:
                raise Fine("signal")
            time.sleep(0.1)
        if self.win is None:
            n.update(outcome="nessun_fotogramma", motivo="no FreeRDP window in %d s" % o.cap_s)
            return n
        self.probe = Probe(o.display, self.win)
        self.probe.start()
        # the live desktop: the tenant's X session is there, and the photo is not degenerate
        first, session_v, colors, last_ctl = None, False, None, 0.0
        while time.time() < t0 + o.cap_s:
            if self.n_stopped:
                raise Fine("signal")
            if not self.rdp_alive():
                n.update(outcome="nessun_fotogramma", motivo="xfreerdp exited during access: %s"
                         % drop_from_log(self.log_rdp()))
                return n
            if not session_v and time.time() - last_ctl > 1.0:
                last_ctl = time.time()
                session_v, _d = self.s.ready()
            im = self.photo_pil()
            colors = distinct_colors(im) if im is not None else None
            if session_v and colors is not None and colors >= ALIVE_COLORS:
                first = time.time()
                break
            time.sleep(0.25)
        n["primo_fotogramma_ms"] = round(first * 1000) if first else None
        n["nascita_ms"] = round((first - t0) * 1000) if first else None
        n["distinct_colors"] = colors
        n["sessione_x"] = session_v
        n["prima_raffica_ms"] = round(self.probe.read_it()[1][0] * 1000) if self.probe.read_it()[1] else None
        if not first:
            if session_v:
                # the session is there but the desktop stays degenerate: work goes on anyway
                n["primo_fotogramma_ms"] = n["prima_raffica_ms"]
                n["nascita_ms"] = (n["prima_raffica_ms"] - n["access_ms"]) if n["prima_raffica_ms"] else None
                n.update(outcome="degenerate", motivo="degenerate desktop (%s colours) at %d s" % (colors, o.cap_s))
            else:
                n.update(outcome="nessun_fotogramma", motivo="no X session in %d s" % o.cap_s)
            return n
        green_v = first - t0 <= CAP_DEGENERATE_S
        n["outcome"], remark = outcome_birth(green_v, not green_v)
        if not green_v:
            n["outcome"] = "degenerate"
            n["motivo"] = "the desktop is alive only at %.1f s from access (cap %d s)" % (
                first - t0, CAP_DEGENERATE_S)
        else:
            n["motivo"] = "X session and %s distinct colours at %.1f s" % (colors, first - t0)
        if remark:
            n["remark"] = remark
        return n

    def prepare_tenant(self):
        self.sc.clear_out(self.chi)
        c, t = self.sc.create(self.chi, self.password)
        if c != 0:
            raise RuntimeError("I could not create the tenant %s: %s" % (self.chi, (t or "")[-200:]))
        self.created = True
        self.sc.inside("h=/home/%s; [ -L $h/.cache ] && rm -f $h/.cache; "
                       "install -d -o %s -g %s -m 700 $h/.cache" % (self.chi, self.chi, self.chi), 30)
        # ⭐ ~/.xsession comes from the skeleton (Contenitore.xrdp): we LOOK that it is there
        c, t = self.sc.inside("cat /home/%s/.xsession" % self.chi, 30)
        if c != 0 or "exec " not in (t or ""):
            self.event("failure", body_text="the tenant's ~/.xsession is missing: the session would not be "
                                        "the desktop (%s)" % (t or "")[:120])
            raise RuntimeError("~/.xsession absent in the tenant %s" % self.chi)
        self.event("xsession", body_text=(t or "").strip().splitlines()[-1][:120])

    # -- everything -------------------------------------------------------------
    def run_loop(self):
        o = self.o
        self.version_v = (subprocess.run(["xfreerdp3", "/version"], capture_output=True, text=True)
                         .stdout.strip().splitlines() or ["?"])[0][:80]
        self.event("start", tenant=self.chi, container_box=o.container_box, display=o.display, seed=o.seed,
                    internal_port=self.internal_port, gauge=[o.largo, o.alto], video=o.video or None,
                    pid=os.getpid(), system_wide="xrdp")
        code_v = 2
        try:
            self.prepare_tenant()
            self.work = L.JOBS[self.profile_v](self)
            self.work.prepare()
            birth = self.enter()
            with open(os.path.join(self.folder, "nascita.json"), "w") as f:
                json.dump(birth, f, ensure_ascii=False, indent=1)
            self.event("birth", **birth)
            if not works_after_birth(birth):
                code_v = 1
                self.save_diagnosis()
                if o.check:
                    return code_v
                self.wait_end("access failed")
                return code_v
            self.entered = True
            self.hands = Hands(self)
            # the keyboard focus on the FreeRDP window (in the Xvfb there is no
            # window manager), then a click on an empty spot of the desktop
            try:
                from Xlib import X
                self.hands.d.create_resource_object("window", self.win).set_input_focus(
                    X.RevertToParent, X.CurrentTime)
                self.hands.d.sync()
            except Exception as e:                   # noqa: BLE001
                self.event("failure", body_text="focus on the FreeRDP window: %r" % e)
            self.sleeps(1.0)
            self.hands.click(self.desktop[0] * 0.55, self.desktop[1] * 0.55)
            self.sleeps(1.0)
            code_v = 0
            for prova in range(3):
                ok, m = self.work.start()
                self.event("application", ok=ok, body_text=m, attempt=prova + 1)
                if ok:
                    break
                self.sleeps(10)
            else:
                code_v = 1
                if o.check:
                    self.outcomes_check = {"application": False}
                    return code_v
                self.wait_end("the application does not start")
                return code_v
            if o.check:
                ok = self.work.command("uname -a")
                self.outcomes_check = {"application": True, "command": ok}
                return 0 if ok else 1
            errors = 0
            while True:
                try:
                    self.work.step()
                    errors = 0
                except Fine:
                    raise
                except Exception as e:               # noqa: BLE001
                    errors += 1
                    self.errors_window.append("%r" % e)
                    self.event("failure", body_text="%r" % e, dove=traceback.format_exc()[-600:],
                                in_a_row=errors)
                    self.sleeps(min(30, 2 * errors))
        except Fine:
            pass
        except Exception as e:                       # noqa: BLE001
            self.event("failure", body_text="%r" % e, dove=traceback.format_exc()[-800:], fatal=True)
            code_v = 2
        finally:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            self.shut()
        return code_v

    def save_diagnosis(self):
        """A failed birth: ~/.xsession-errors and the tenant's Xorg log
        in the folder, BEFORE the clean-up deletes them."""
        c, t = self.sc.inside("for f in /home/%s/.xsession-errors /home/%s/.xorgxrdp.*.log; do "
                              "echo \"== $f\"; tail -n 60 \"$f\" 2>/dev/null; done" % (self.chi, self.chi), 60)
        with open(os.path.join(self.folder, "diagnosi-sessione.txt"), "w") as f:
            f.write(t or "")

    def wait_end(self, reason_text):
        self.event("waiting", reason_text=reason_text)
        while True:
            self.sleeps(5)

    def shut(self):
        try:
            try:
                self.write_state()
            except Exception:                        # noqa: BLE001
                pass
            if self.probe is not None:
                self.probe.halt()
            if self.rdp is not None and self.rdp.poll() is None:
                try:
                    os.killpg(self.rdp.pid, signal.SIGTERM)
                    self.rdp.wait(timeout=10)
                except Exception:                    # noqa: BLE001
                    try:
                        os.killpg(self.rdp.pid, signal.SIGKILL)
                    except OSError:
                        pass
        finally:
            if self.created:
                try:
                    self.sc.clear_out(self.chi)
                except Exception as e:               # noqa: BLE001
                    print("   ⚠ exit: %s" % e, flush=True)
            _c, t = self.sc.inside("id %s >/dev/null 2>&1 && echo RESTA || echo via" % self.chi, 30)
            self.event("fine", cleared=(t or "").strip().endswith("via"), acts=self.acts,
                        checks=self.checks)
            self.f_state.close()
            self.f_events.close()


def check(o, expect):
    """The reduced short check (§7.3): enters, screen, keyboard ⇒ controllo-corto.json."""
    t = time.time()
    code_v = expect.run_loop()
    try:
        na = json.load(open(os.path.join(expect.folder, "nascita.json")))
    except (OSError, ValueError):
        na = {}
    es_ctl = getattr(expect, "outcomes_check", {}) or {}
    acc = bool(na.get("primo_fotogramma_ms") or na.get("prima_raffica_ms"))
    outcomes = {"RDP-accesso": "PASS" if acc else "FAIL",
             "RDP-schermo": "PASS" if na.get("outcome") == "ok" else ("FAIL" if acc else "BLOCKED"),
             "RDP-tastiera": ("PASS" if es_ctl.get("application") and es_ctl.get("command") else
                              ("FAIL" if es_ctl else "BLOCKED"))}
    nas = {"nascita_s": round(na["nascita_ms"] / 1000.0, 2) if na.get("nascita_ms") is not None else None,
           "primo_non_degenere_s": round(na["nascita_ms"] / 1000.0, 2)
           if na.get("outcome") == "ok" and na.get("nascita_ms") is not None else None,
           "refusal": na.get("outcome") == "refusal", "outcome": "PASS" if na.get("outcome") == "ok" else "FAIL",
           "rationale": na.get("motivo")}
    out = {"username": 99, "tenant": expect.chi, "browser": "freerdp", "version_v": expect.version_v,
           "system_wide": "xrdp", "outcomes": outcomes, "birth": nas, "code_v": code_v,
           "outcome": "FAIL" if "FAIL" in outcomes.values() else ("PASS" if all(
               v == "PASS" for v in outcomes.values()) else "BLOCKED"),
           "duration_s": round(time.time() - t, 1),
           "remark": "REDUCED short check (fasi/20 §7.3): access, screen, keyboard — the REMOTIX page's "
                   "F-0xx functions do not exist in xrdp"}
    with open(os.path.join(o.dir, "controllo-corto.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("xrdp short check: %s %s" % (out["outcome"], outcomes), flush=True)
    return 0 if out["outcome"] == "PASS" else 1


def call_args():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--certify", action="store_true")
    a.add_argument("--check", action="store_true", help="the reduced short check (user 99)")
    a.add_argument("--container_box", choices=DESKTOP)
    a.add_argument("--username", type=int)
    a.add_argument("--display", help="this user's Xvfb (:2NN)")
    a.add_argument("--dir")
    a.add_argument("--seed", default="0")
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    a.add_argument("--video", default="")
    a.add_argument("--cap-s", type=int, default=60)
    # accepted and ignored: the climb passes them equally to both actors
    a.add_argument("--base-ports", type=int, default=0)
    a.add_argument("--level", default="")
    a.add_argument("--browser", default="")
    o = a.parse_args()
    if o.certify:
        return o
    if o.check:
        o.username = 99
        o.seed = o.seed if o.seed != "0" else "check"
    for k in ("container_box", "username", "display", "dir"):
        if getattr(o, k) in (None, ""):
            a.error("--%s is needed" % k)
    return o


def main():
    o = call_args()
    if o.certify:
        return certify()
    try:
        open("/proc/self/oom_score_adj", "w").write("800")      # §7.7: the clients die first
    except OSError:
        pass
    os.environ.pop("WAYLAND_DISPLAY", None)
    expect = Actor(o)

    def _fine(_n, _f):
        expect.n_stopped = True

    def _photo(_n, _f):
        expect.want_photo = True
    signal.signal(signal.SIGTERM, _fine)
    signal.signal(signal.SIGINT, _fine)
    signal.signal(signal.SIGUSR1, _photo)
    print("⭐ xrdp actor %02d · %s · profile %s · %s · %s" % (
        o.username, o.container_box, expect.profile_v, o.display, expect.chi), flush=True)
    if o.check:
        return check(o, expect)
    return expect.run_loop()


if __name__ == "__main__":
    sys.exit(main())
