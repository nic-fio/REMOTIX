#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-attore-rdp — A SIMULATED USER IN FRONT OF xrdp (fasi/20-le-prestazioni.md §7)

    python3 16-attore-rdp.py --box gnome|kde|xfce|lxqt --user N --display :2NN \\
        --dir DIR --seed S [--width 3840 --height 2160] [--video FILE]
    python3 16-attore-rdp.py --check --box xfce --display :200 --dir DIRLIV ...
    python3 16-attore-rdp.py --certify

It is the twin of 16-attore.py for the comparison with xrdp: SAME rhythm (Ritmo, same seeds),
SAME four jobs (16-lavori.py), SAME schema of state.jsonl / birth.json /
events.jsonl, so that 16-classifica.py --system xrdp reads them.  The client changes:

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

state.jsonl, every 5 s: conti {"painted": CUMULATIVE bursts}, dipinti_s, input [{ok,
latenza_ms, azione}], blocco_max_ms (impulse → first draw after it, or the still of the video),
ritardi_ms (the same, one per impulse closed in the interval), ritardi_eco_ms (only the
keys typed where the echo is immediate), lavoro, caduta (xfreerdp exited or the window
gone), errori, eventi.  ⛔ There are NO consegnati, salt, buchi, audio: xrdp does not send the
frames it cannot (FreeRDP acknowledges them), and has no counters in the page (§7.3).

birth.json: accesso_ms = the start of xfreerdp (user and password on the line: no
login screen); primo_fotogramma_ms = the first instant at which the tenant's X session
exists AND the photo is not degenerate (at least 40 distinct colours, the rule of
`desktop_dark_but_alive`); degenerate if at 15 s from access still not (§9).

--check: the reduced short check of §7.3 — one more session (user 99,
profile C), which enters, opens the terminal, types two commands and finds them in the bash
history, and leaves.  Writes DIR/short-check.json in the schema of 16-controllo-corto.py
(outcomes RDP-accesso, RDP-schermo, RDP-tastiera; nascita).

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


def _load(name, file):
    s = _iu.spec_from_file_location(name, file)
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

    def drawing(self, t):
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


def drop_from_log(text):
    """Does the xfreerdp log say the connection dropped?  (phrase or None)"""
    for rx in (r"ERRCONNECT_\w+", r"ERRINFO_\w+", r"connection (?:lost|closed|failure)",
               r"Network disconnect", r"freerdp_check_fds\(\) failed"):
        m = re.search(rx, text or "", re.I)
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
        r.drawing(t)
    prova("6 draws in 3 groups ⇒ 3 bursts", r.n == 3 and r.t == [1.000, 1.040, 1.080], str(r.t))
    r = Bursts()
    for k in range(300):
        r.drawing(10 + k / 30.0)
    prova("a video at 30 per second ⇒ 30 bursts per second", r.n == 300)
    # ⛔ FAULT: a 50 ms threshold (too wide) merges the video frames
    r = Bursts(threshold=0.05)
    for k in range(300):
        r.drawing(10 + k / 30.0)
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
    all_items = set("".join(c for c, _p in L.COMMANDS_C) + " #k0123456789" + "".join(L.NOTE_WORDS)
                + "/home/c16001u1/prova16/nuove")
    unknown = sorted(c for c in all_items if XK.string_to_keysym(key_x(c)) == 0)
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
        self.name = desktop
        self.container = "rete11-%s-xrdp" % desktop

    def inside(self, line, seconds=90):
        try:
            r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", self.container,
                                "sh", "-c", line], input=_sudo_password(), capture_output=True,
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
    """`in_session` of suite.Sessione, for an X session carried by xrdp: the environment
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
        body = ("runuser -u %(c)s -- env -i $amb HOME=/home/%(c)s USER=%(c)s LOGNAME=%(c)s "
                 "SHELL=/bin/bash sh -c %(q)s" % {"c": self.chi, "q": _q(command)})
        if background:
            body = "setsid %s < /dev/null > /home/%s/.c16-%s.log 2>&1 & echo launched" % (
                body, self.chi, re.sub(r"\W", "", command.split()[0])[:20])
        return self.sc.inside(self._env() + body, seconds)

    def as_user(self, command, seconds=60):
        return self.sc.inside("runuser -u %s -- %s 2>&1" % (self.chi, command), seconds)


# ═══════════════════════════════════════════════════════════════════════════
#  THE XDamage PROBE (a thread of its own, a connection of its own)
# ═══════════════════════════════════════════════════════════════════════════
class Probe(threading.Thread):
    def __init__(self, display_name, window):
        super().__init__(daemon=True)
        from Xlib import display
        from Xlib.ext import damage
        self.d = display.Display(display_name)
        self.d.damage_query_version()                      # ⛔ without it, ZERO events
        w = self.d.create_resource_object("window", window)
        self.dmg = w.damage_create(damage.DamageReportNonEmpty)
        self.d.flush()
        self.r = Bursts()
        self.lock = threading.Lock()
        self.alive = True
        self.error = None

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
                        self.r.drawing(t)
                    # NonEmpty: the damage is emptied, so the next draw notifies again
                    self.d.damage_subtract(self.dmg, 0, 0)
                    self.d.flush()
        except Exception as e:                               # noqa: BLE001
            self.error = repr(e)

    def load(self):
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

    def _kc(self, name):
        ks = self.XK.string_to_keysym(key_x(name))
        if not ks and len(name) == 1:
            ks = ord(name)
        kc = self.d.keysym_to_keycode(ks) if ks else 0
        if not kc:
            raise RuntimeError("no key for %r" % name)
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

    def click(self, X, Y, button_code=0, expected=False):
        self.move_to(X, Y)
        b = {0: 1, 1: 2, 2: 3}.get(button_code, 1)
        self.xtest.fake_input(self.d, self.X.ButtonPress, b)
        self.d.sync()
        t = time.time()
        time.sleep(self.a.rate.whole(50, 120) / 1000.0)
        self.xtest.fake_input(self.d, self.X.ButtonRelease, b)
        self.d.sync()
        if expected:
            self.a.pulse(t)
        self.a.count("mouse_click")
        return t

    def wheel(self, X, Y, ticks, expected=False):
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
        if expected:
            self.a.pulse(t)
        self.a.count("notches")
        return t

    def press(self, name, expected=False):
        kc, shift = self._kc(name)
        sh = self._kc("Shift")[0] if shift else None
        if sh:
            self._down(sh)
        t = self._down(kc)
        time.sleep(self.pause_ms / 1000.0)
        self._su(kc)
        if sh:
            self._su(sh)
        time.sleep(self.pause_ms / 1000.0)
        if expected:
            self.a.pulse(t)
        return t

    def combo(self, mod, keystroke):
        mods = [self._kc(m)[0] for m in mod]
        kc, _m = self._kc(keystroke.lower() if len(keystroke) == 1 else keystroke)
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

    def beat(self, text, expected=True, echo=False):
        """Every character a real key, with the person's rhythm; every ~1.5 s the heart
        (the state row and the signals).  `echo`: the character appears at once ⇒ its
        impulse also counts among the «echo» delays."""
        R = self.a.rate
        dur = 0.0
        sh = self._kc("Shift")[0]
        for c in text:
            ten, bat = R.hold_ms(), R.keystroke_ms()
            kc, shift = self._kc(c)
            if shift:
                self._down(sh)
            t = self._down(kc)
            if expected:
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
        self.a.count("keys")
        return time.time()


# ═══════════════════════════════════════════════════════════════════════════
#  THE ACTOR
# ═══════════════════════════════════════════════════════════════════════════
class Actor:
    def __init__(self, o):
        self.o = o
        self.n = o.user
        self.profile = "C" if o.check else L.profile_of(self.n)
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
        self.porta_interna = L.porta_interna(o.box, self.n)
        self.rate = Rate(o.seed, self.n)
        self.folder = os.path.join(o.dir, "short-check" if o.check else "user-%02d" % self.n)
        os.makedirs(self.folder, exist_ok=True)
        self.f_state = open(os.path.join(self.folder, "state.jsonl"), "a", buffering=1)
        self.f_events = open(os.path.join(self.folder, "events.jsonl"), "a", buffering=1)
        self.sc = Box(o.box)
        self.s = XSession(self.sc, self.chi)
        self.version = "?"
        self.events_window, self.errors_window = [], []
        self.pulses, self.echo_pulses = [], []
        self.entered = False
        self.desktop = (o.width, o.height)
        self.hands = self.probe = self.work = self.rdp = None
        self.window = None
        self.want_photo = self.n_stopped = False
        self.next_state = 0.0
        self.actions, self.done_window = {}, 0
        self.checks, self.ver_window = {"ok": 0, "ko": 0}, []
        self.prev = None
        self.photo_size = None
        self.x = None                          # X connection for the photos
        self.created = False

    # -- the rows --------------------------------------------------------------
    def _head(self, event):
        return {"t": round(time.time(), 3), "user": self.n, "profile": self.profile,
                "browser": self.browser, "version": self.version, "tenant": self.chi,
                "event": event}

    def line(self, **fields):
        r = self._head("state")
        r.pop("event")
        r.update(fields)
        self.f_state.write(json.dumps(r, ensure_ascii=False) + "\n")

    def event(self, kind, **fields):
        r = self._head(kind)
        r.update(fields)
        self.f_events.write(json.dumps(r, ensure_ascii=False) + "\n")
        self.events_window.append(r)
        print("   [%02d %s] %s %s" % (self.n, self.profile, kind,
                                    json.dumps(fields, ensure_ascii=False)[:240]), flush=True)

    def count(self, action):
        self.actions[action] = self.actions.get(action, 0) + 1
        self.done_window += 1

    def verify(self, action, ok, lat_ms, det=""):
        self.count(action)
        self.checks["ok" if ok else "ko"] += 1
        v = {"action": action, "ok": bool(ok),
             "latency_ms": None if lat_ms is None else round(lat_ms), "det": det}
        self.ver_window.append(v)
        if not ok:
            print("   [%02d %s] ⚠ input NOT verified: %s" % (self.n, self.profile, v), flush=True)

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

    def sleep_ms(self, seconds):
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
        n, dt_list = self.probe.load()
        errors = list(self.errors_window)
        if self.probe.error:
            errors.append("the XDamage probe has stopped: %s" % self.probe.error)
        drop = False
        if self.entered and not self.rdp_alive():
            drop = True
            errors.append("xfreerdp exited (code %s): %s" % (
                self.rdp.returncode if self.rdp else None,
                drop_from_log(self.log_rdp()) or "no error line"))
        block, work, delays, echo = None, False, [], []
        if self.profile == "D":
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
                 "block_max_ms": None if block is None else round(block * 1000),
                 "delays_ms": [round(x * 1000, 1) for x in delays],
                 "echo_delays_ms": [round(x * 1000, 1) for x in echo],
                 "work": work, "drop": drop, "errors": errors,
                 "session": self.rdp_alive(), "system": "xrdp"}
        if self.prev:
            dt = now - self.prev[0]
            fields["delta"] = {"painted": n - self.prev[1], "s": round(dt, 2)}
            if dt > 0:
                fields["painted_s"] = round((n - self.prev[1]) / dt, 2)
        self.prev = (now, n)
        fields["late_s"] = round(getattr(self, "is_late", 0.0), 2)
        fields.update({"actions": dict(self.actions), "window_actions": self.done_window,
                      "checks": dict(self.checks)})
        if self.work is not None:
            try:
                fields["work_details"] = self.work.extra()
            except Exception as e:                  # noqa: BLE001
                fields["work_details"] = {"error": str(e)[:200]}
        if self.events_window:
            fields["events"] = self.events_window
        self.done_window = 0
        self.ver_window, self.errors_window, self.events_window = [], [], []
        self.line(**fields)

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
            self.event("photo", ok=False, why="the Xvfb cannot be photographed")
            return
        f = os.path.join(self.folder, "foto-%d.png" % int(t * 1000))
        im.save(f)
        self.event("photo", ok=True, file=f, ms=round((time.time() - t) * 1000))

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
        env = dict(os.environ, DISPLAY=self.o.display)
        env.pop("WAYLAND_DISPLAY", None)
        log = open(os.path.join(self.folder, "xfreerdp.log"), "a")
        log.write("=== %s\n" % time.strftime("%F %T"))
        log.flush()

        def oom():
            try:
                open("/proc/self/oom_score_adj", "w").write("800")
            except OSError:
                pass
        self.rdp = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=env,
                                    stdin=subprocess.DEVNULL, start_new_session=True,
                                    preexec_fn=oom)

    def enter(self):
        o = self.o
        n = {"tenant": self.chi, "browser": self.browser, "version": self.version,
             "box": o.box, "system": "xrdp", "size": [o.width, o.height]}
        t0 = time.time()
        self.turn_on_rdp()
        n["access_ms"] = round(t0 * 1000)
        # the FreeRDP window, then the probe
        while time.time() < t0 + o.cap_s and self.window is None:
            if not self.rdp_alive():
                c = drop_from_log(self.log_rdp())
                n.update(outcome="refusal" if c and "AUTH" in c.upper() else "no_frame",
                         reason="xfreerdp exited before the window: %s" % c)
                return n
            self.window = self.search_window()
            if self.n_stopped:
                raise Fine("signal")
            time.sleep(0.1)
        if self.window is None:
            n.update(outcome="no_frame", reason="no FreeRDP window in %d s" % o.cap_s)
            return n
        self.probe = Probe(o.display, self.window)
        self.probe.start()
        # the live desktop: the tenant's X session is there, and the photo is not degenerate
        first, session, colors, last_ctl = None, False, None, 0.0
        while time.time() < t0 + o.cap_s:
            if self.n_stopped:
                raise Fine("signal")
            if not self.rdp_alive():
                n.update(outcome="no_frame", reason="xfreerdp exited during access: %s"
                         % drop_from_log(self.log_rdp()))
                return n
            if not session and time.time() - last_ctl > 1.0:
                last_ctl = time.time()
                session, _d = self.s.ready()
            im = self.photo_pil()
            colors = distinct_colors(im) if im is not None else None
            if session and colors is not None and colors >= ALIVE_COLORS:
                first = time.time()
                break
            time.sleep(0.25)
        n["first_frame_ms"] = round(first * 1000) if first else None
        n["birth_ms"] = round((first - t0) * 1000) if first else None
        n["distinct_colors"] = colors
        n["session_x"] = session
        n["first_burst_ms"] = round(self.probe.load()[1][0] * 1000) if self.probe.load()[1] else None
        if not first:
            if session:
                # the session is there but the desktop stays degenerate: work goes on anyway
                n["first_frame_ms"] = n["first_burst_ms"]
                n["birth_ms"] = (n["first_burst_ms"] - n["access_ms"]) if n["first_burst_ms"] else None
                n.update(outcome="degenerate", reason="degenerate desktop (%s colours) at %d s" % (colors, o.cap_s))
            else:
                n.update(outcome="no_frame", reason="no X session in %d s" % o.cap_s)
            return n
        green = first - t0 <= CAP_DEGENERATE_S
        n["outcome"], note = outcome_birth(green, not green)
        if not green:
            n["outcome"] = "degenerate"
            n["reason"] = "the desktop is alive only at %.1f s from access (cap %d s)" % (
                first - t0, CAP_DEGENERATE_S)
        else:
            n["reason"] = "X session and %s distinct colours at %.1f s" % (colors, first - t0)
        if note:
            n["note"] = note
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
            self.event("error", text="the tenant's ~/.xsession is missing: the session would not be "
                                        "the desktop (%s)" % (t or "")[:120])
            raise RuntimeError("~/.xsession absent in the tenant %s" % self.chi)
        self.event("xsession", text=(t or "").strip().splitlines()[-1][:120])

    # -- everything -------------------------------------------------------------
    def run_loop(self):
        o = self.o
        self.version = (subprocess.run(["xfreerdp3", "/version"], capture_output=True, text=True)
                         .stdout.strip().splitlines() or ["?"])[0][:80]
        self.event("start", tenant=self.chi, box=o.box, display=o.display, seed=o.seed,
                    porta_interna=self.porta_interna, measure=[o.width, o.height], video=o.video or None,
                    pid=os.getpid(), system_wide="xrdp")
        code = 2
        try:
            self.prepare_tenant()
            self.work = L.JOBS[self.profile](self)
            self.work.prepare()
            birth = self.enter()
            with open(os.path.join(self.folder, "birth.json"), "w") as f:
                json.dump(birth, f, ensure_ascii=False, indent=1)
            self.event("birth", **birth)
            if not works_after_birth(birth):
                code = 1
                self.save_diagnosis()
                if o.check:
                    return code
                self.wait_end("access failed")
                return code
            self.entered = True
            self.hands = Hands(self)
            # the keyboard focus on the FreeRDP window (in the Xvfb there is no
            # window manager), then a click on an empty spot of the desktop
            try:
                from Xlib import X
                self.hands.d.create_resource_object("window", self.window).set_input_focus(
                    X.RevertToParent, X.CurrentTime)
                self.hands.d.sync()
            except Exception as e:                   # noqa: BLE001
                self.event("error", text="focus on the FreeRDP window: %r" % e)
            self.sleep_ms(1.0)
            self.hands.click(self.desktop[0] * 0.55, self.desktop[1] * 0.55)
            self.sleep_ms(1.0)
            code = 0
            for prova in range(3):
                ok, m = self.work.launch()
                self.event("application", ok=ok, text=m, attempt=prova + 1)
                if ok:
                    break
                self.sleep_ms(10)
            else:
                code = 1
                if o.check:
                    self.outcomes_check = {"application": False}
                    return code
                self.wait_end("the application does not start")
                return code
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
                    self.event("error", text="%r" % e, dove=traceback.format_exc()[-600:],
                                di_fila=errors)
                    self.sleep_ms(min(30, 2 * errors))
        except Fine:
            pass
        except Exception as e:                       # noqa: BLE001
            self.event("error", text="%r" % e, dove=traceback.format_exc()[-800:], fatale=True)
            code = 2
        finally:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            self.close()
        return code

    def save_diagnosis(self):
        """A failed birth: ~/.xsession-errors and the tenant's Xorg log
        in the folder, BEFORE the clean-up deletes them."""
        c, t = self.sc.inside("for f in /home/%s/.xsession-errors /home/%s/.xorgxrdp.*.log; do "
                              "echo \"== $f\"; tail -n 60 \"$f\" 2>/dev/null; done" % (self.chi, self.chi), 60)
        with open(os.path.join(self.folder, "diagnosi-sessione.txt"), "w") as f:
            f.write(t or "")

    def wait_end(self, why):
        self.event("waiting", why=why)
        while True:
            self.sleep_ms(5)

    def close(self):
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
            self.event("end", cleared=(t or "").strip().endswith("via"), actions=self.actions,
                        checks=self.checks)
            self.f_state.close()
            self.f_events.close()


def check(o, expect):
    """The reduced short check (§7.3): enters, screen, keyboard ⇒ short-check.json."""
    t = time.time()
    code = expect.run_loop()
    try:
        na = json.load(open(os.path.join(expect.folder, "birth.json")))
    except (OSError, ValueError):
        na = {}
    es_ctl = getattr(expect, "outcomes_check", {}) or {}
    acc = bool(na.get("first_frame_ms") or na.get("first_burst_ms"))
    outcomes = {"RDP-access": "PASS" if acc else "FAIL",
             "RDP-screen": "PASS" if na.get("outcome") == "ok" else ("FAIL" if acc else "BLOCKED"),
             "RDP-keyboard": ("PASS" if es_ctl.get("application") and es_ctl.get("command") else
                              ("FAIL" if es_ctl else "BLOCKED"))}
    nas = {"birth_s": round(na["birth_ms"] / 1000.0, 2) if na.get("birth_ms") is not None else None,
           "first_non_degenerate_s": round(na["birth_ms"] / 1000.0, 2)
           if na.get("outcome") == "ok" and na.get("birth_ms") is not None else None,
           "refusal": na.get("outcome") == "refusal", "outcome": "PASS" if na.get("outcome") == "ok" else "FAIL",
           "rationale": na.get("reason")}
    out = {"user": 99, "tenant": expect.chi, "browser": "freerdp", "version": expect.version,
           "system": "xrdp", "outcomes": outcomes, "birth": nas, "code": code,
           "outcome": "FAIL" if "FAIL" in outcomes.values() else ("PASS" if all(
               v == "PASS" for v in outcomes.values()) else "BLOCKED"),
           "duration_s": round(time.time() - t, 1),
           "note": "REDUCED short check (fasi/20 §7.3): access, screen, keyboard — the REMOTIX page's "
                   "F-0xx functions do not exist in xrdp"}
    with open(os.path.join(o.dir, "short-check.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("xrdp short check: %s %s" % (out["outcome"], outcomes), flush=True)
    return 0 if out["outcome"] == "PASS" else 1


def call_args():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--certify", action="store_true")
    a.add_argument("--check", action="store_true", help="the reduced short check (user 99)")
    a.add_argument("--box", choices=DESKTOP)
    a.add_argument("--user", type=int)
    a.add_argument("--display", help="this user's Xvfb (:2NN)")
    a.add_argument("--dir")
    a.add_argument("--seed", default="0")
    a.add_argument("--width", type=int, default=3840)
    a.add_argument("--height", type=int, default=2160)
    a.add_argument("--video", default="")
    a.add_argument("--cap-s", type=int, default=60)
    # accepted and ignored: the climb passes them equally to both actors
    a.add_argument("--base-port", type=int, default=0)
    a.add_argument("--level", default="")
    a.add_argument("--browser", default="")
    o = a.parse_args()
    if o.certify:
        return o
    if o.check:
        o.user = 99
        o.seed = o.seed if o.seed != "0" else "check"
    for k in ("box", "user", "display", "dir"):
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
        o.user, o.box, expect.profile, o.display, expect.chi), flush=True)
    if o.check:
        return check(o, expect)
    return expect.run_loop()


if __name__ == "__main__":
    sys.exit(main())
