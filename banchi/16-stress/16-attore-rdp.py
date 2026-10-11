#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-attore-rdp — A SIMULATED USER IN FRONT OF xrdp (fasi/20-le-prestazioni.md §7)

    python3 16-attore-rdp.py --scatola gnome|kde|xfce|lxqt --utente N --display :2NN \\
        --dir DIR --seme S [--largo 3840 --alto 2160] [--video FILE]
    python3 16-attore-rdp.py --controllo --scatola xfce --display :200 --dir DIRLIV ...
    python3 16-attore-rdp.py --certifica

It is the twin of 16-attore.py for the comparison with xrdp: SAME rhythm (Ritmo, same seeds),
SAME four jobs (16-lavori.py), SAME schema of stato.jsonl / nascita.json /
eventi.jsonl, so that 16-classifica.py --sistema xrdp reads them.  The client changes:

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

stato.jsonl, every 5 s: conti {"dipinti": CUMULATIVE bursts}, dipinti_s, input [{ok,
latenza_ms, azione}], blocco_max_ms (impulse → first draw after it, or the still of the video),
ritardi_ms (the same, one per impulse closed in the interval), ritardi_eco_ms (only the
keys typed where the echo is immediate), lavoro, caduta (xfreerdp exited or the window
gone), errori, eventi.  ⛔ There are NO consegnati, salt, buchi, audio: xrdp does not send the
frames it cannot (FreeRDP acknowledges them), and has no counters in the page (§7.3).

nascita.json: accesso_ms = the start of xfreerdp (user and password on the line: no
login screen); primo_fotogramma_ms = the first instant at which the tenant's X session
exists AND the photo is not degenerate (at least 40 distinct colours, the rule of
`desktop_scuro_ma_vivo`); degenerate if at 15 s from access still not (§9).

--controllo: the reduced short check of §7.3 — one more session (user 99,
profile C), which enters, opens the terminal, types two commands and finds them in the bash
history, and leaves.  Writes DIR/controllo-corto.json in the schema of 16-controllo-corto.py
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

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)
DESKTOP = ("gnome", "kde", "xfce", "lxqt")


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


A16 = _carica("attore16", os.path.join(QUI, "16-attore.py"))
L = A16.L
Ritmo, Fine = A16.Ritmo, A16.Fine
attese_impulsi, pausa_piu_lunga = A16.attese_impulsi, A16.pausa_piu_lunga
outcome_birth, works_after_birth = A16.outcome_birth, A16.works_after_birth
CAP_DEGENERATE_S = A16.CAP_DEGENERATE_S
RAFFICA_S = 0.005             # two draws less than 5 ms apart are the same frame (§7.3)
ALIVE_COLORS = 40              # the rule of desktop_scuro_ma_vivo (12-c20-veri.py)


def _firefox_prefs():
    """The preferences of the inner Firefox: the same as 11-c21 (PREFERENZE), read from the
    file and not imported (that module drags in the browser guides)."""
    try:
        s = open(os.path.join(BANCHI, "11-scatole", "11-c21-sul-bordo-la-forma-cambia.py"),
                 encoding="utf-8").read()
        m = re.search(r'^PREFERENZE = """(.*?)"""', s, re.S | re.M)
        if m:
            return m.group(1)
    except OSError:
        pass
    return 'user_pref("browser.shell.checkDefaultBrowser", false);\n'


def _parola_sudo():
    p = os.environ.get("REMOTIX_PAROLA_SUDO")
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
    rectangles): a draw more than RAFFICA_S after the previous one opens a new burst."""

    def __init__(self, soglia=RAFFICA_S):
        self.soglia, self.ultimo, self.n, self.t = soglia, None, 0, []

    def disegno(self, t):
        nuova = self.ultimo is None or t - self.ultimo > self.soglia
        if nuova:
            self.n += 1
            self.t.append(t)
            if len(self.t) > 20000:
                del self.t[:5000]
        self.ultimo = t
        return nuova


def colori_distinti(im, fattore=8):
    """How many distinct colours in the photo reduced by `fattore` (None if unreadable)."""
    w, h = im.size
    p = im.resize((max(1, w // fattore), max(1, h // fattore)))
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


def drop_from_log(testo):
    """Does the xfreerdp log say the connection dropped?  (phrase or None)"""
    for rx in (r"ERRCONNECT_\w+", r"ERRINFO_\w+", r"connection (?:lost|closed|failure)",
               r"Network disconnect", r"freerdp_check_fds\(\) failed"):
        m = re.search(rx, testo or "", re.I)
        if m:
            return m.group(0)
    return None


def certifica():
    guai = []

    def prova(cosa, vero, det=""):
        print("   %s %s%s" % ("⭐ ok " if vero else "⛔ NO ", cosa, (" — " + det) if det else ""))
        if not vero:
            guai.append(cosa)

    print("── the bursts")
    r = Bursts()
    for t in (1.000, 1.001, 1.004, 1.040, 1.041, 1.080):
        r.disegno(t)
    prova("6 draws in 3 groups ⇒ 3 bursts", r.n == 3 and r.t == [1.000, 1.040, 1.080], str(r.t))
    r = Bursts()
    for k in range(300):
        r.disegno(10 + k / 30.0)
    prova("a video at 30 per second ⇒ 30 bursts per second", r.n == 300)
    # ⛔ FAULT: a 50 ms threshold (too wide) merges the video frames
    r = Bursts(soglia=0.05)
    for k in range(300):
        r.disegno(10 + k / 30.0)
    prova("FAULT seen: 50 ms threshold ⇒ the 30/s video becomes ONE burst", r.n == 1, str(r.n))
    at, ap = attese_impulsi([10.0, 12.0], [10.03, 12.4], 13.0)
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
    tutti = set("".join(c for c, _p in L.COMMANDS_C) + " #k0123456789" + "".join(L.PAROLE_NOTA)
                + "/home/c16001u1/prova16/nuove")
    ignoti = sorted(c for c in tutti if XK.string_to_keysym(key_x(c)) == 0)
    prova("every character of the C commands has a keysym", not ignoti, str(ignoti))
    prova("FAULT seen: a wrong name ⇒ keysym 0", XK.string_to_keysym("trattino") == 0)

    print("── the photo")
    try:
        from PIL import Image, ImageDraw
        nero = Image.new("RGB", (800, 600), (0, 0, 0))
        prova("all black ⇒ 1 colour (degenerate)", colori_distinti(nero) == 1)
        viva = nero.copy()
        dr = ImageDraw.Draw(viva)
        for i in range(60):
            dr.rectangle([i * 13, 0, i * 13 + 12, 20], fill=(i * 4, 255 - i * 4, (i * 37) % 255))
        prova("a panel of 60 colours ⇒ alive", (colori_distinti(viva) or 0) >= ALIVE_COLORS,
              str(colori_distinti(viva)))
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
    print("⛔ CERTIFICATION FAILED (%d)" % len(guai) if guai else "⭐ CERTIFIED")
    return 1 if guai else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE BOX AND THE TENANT'S X SESSION
# ═══════════════════════════════════════════════════════════════════════════
class Scatola:
    """Root commands in the box, LOCAL (sudo podman exec), like suite.py on the server."""

    def __init__(self, desktop):
        self.nome = desktop
        self.contenitore = "rete11-%s-xrdp" % desktop

    def dentro(self, riga, secondi=90):
        try:
            r = subprocess.run(["sudo", "-S", "-p", "", "podman", "exec", self.contenitore,
                                "sh", "-c", riga], input=_parola_sudo(), capture_output=True,
                               text=True, errors="replace", timeout=secondi)
        except subprocess.TimeoutExpired:
            return None, "(no answer in %d s)" % secondi
        return r.returncode, (r.stdout + r.stderr).strip()

    def crea(self, chi, parola):
        return self.dentro("useradd -m -s /bin/bash %s && printf '%s:%s\\n' | chpasswd"
                           % (chi, chi, parola), 60)

    def sgombera(self, chi):
        self.dentro("loginctl terminate-user %s >/dev/null 2>&1; "
                    "pkill -KILL -f 'runuser -u [%s]%s ' 2>/dev/null; "
                    "pkill -KILL -u %s >/dev/null 2>&1; sleep 0.5; "
                    "userdel -r %s >/dev/null 2>&1 || userdel %s >/dev/null 2>&1; "
                    "rm -rf /home/%s" % (chi, chi[0], chi[1:], chi, chi, chi, chi), 90)


X_ENV = (r"(DISPLAY|XAUTHORITY|DBUS_SESSION_BUS_ADDRESS|XDG_[A-Z_]+|LANG|LC_[A-Z]+|PATH|"
              r"DESKTOP_SESSION|KDE_[A-Z_]+|GTK_[A-Z_]+|QT_[A-Z_]+|GNOME_[A-Z_]+|SESSION_MANAGER)")


class XSession:
    """`nella_sessione` of suite.Sessione, for an X session carried by xrdp: the environment
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

    def pronta(self):
        """Is the tenant's X session there (does one of its processes have DISPLAY)?"""
        c, t = self.sc.dentro(self._env() + "echo \"$amb\" | grep -o 'DISPLAY=[^ ]*'", 30)
        return c == 0, (t or "").strip()

    def nella_sessione(self, comando, secondi=60, fondo=True):
        corpo = ("runuser -u %(c)s -- env -i $amb HOME=/home/%(c)s USER=%(c)s LOGNAME=%(c)s "
                 "SHELL=/bin/bash sh -c %(q)s" % {"c": self.chi, "q": _q(comando)})
        if fondo:
            corpo = "setsid %s < /dev/null > /home/%s/.c16-%s.log 2>&1 & echo launched" % (
                corpo, self.chi, re.sub(r"\W", "", comando.split()[0])[:20])
        return self.sc.dentro(self._env() + corpo, secondi)

    def as_user(self, comando, secondi=60):
        return self.sc.dentro("runuser -u %s -- %s 2>&1" % (self.chi, comando), secondi)


# ═══════════════════════════════════════════════════════════════════════════
#  THE XDamage PROBE (a thread of its own, a connection of its own)
# ═══════════════════════════════════════════════════════════════════════════
class Probe(threading.Thread):
    def __init__(self, display_name, finestra):
        super().__init__(daemon=True)
        from Xlib import display
        from Xlib.ext import damage
        self.d = display.Display(display_name)
        self.d.damage_query_version()                      # ⛔ without it, ZERO events
        w = self.d.create_resource_object("window", finestra)
        self.dmg = w.damage_create(damage.DamageReportNonEmpty)
        self.d.flush()
        self.r = Bursts()
        self.serratura = threading.Lock()
        self.vivo = True
        self.errore = None

    def run(self):
        fd = self.d.fileno()
        try:
            while self.vivo:
                select.select([fd], [], [], 0.5)
                n = 0
                while self.d.pending_events():
                    self.d.next_event()
                    n += 1
                if n:
                    t = time.time()
                    with self.serratura:
                        self.r.disegno(t)
                    # NonEmpty: the damage is emptied, so the next draw notifies again
                    self.d.damage_subtract(self.dmg, 0, 0)
                    self.d.flush()
        except Exception as e:                               # noqa: BLE001
            self.errore = repr(e)

    def leggi(self):
        with self.serratura:
            return self.r.n, list(self.r.t)

    def ferma(self):
        self.vivo = False


# ═══════════════════════════════════════════════════════════════════════════
#  THE HANDS — XTEST on the Xvfb (the input goes through the RDP channel)
# ═══════════════════════════════════════════════════════════════════════════
class Mani:
    def __init__(self, att):
        from Xlib import X, XK, display
        from Xlib.ext import xtest
        self.a, self.X, self.XK, self.xtest = att, X, XK, xtest
        self.d = display.Display(att.o.display)
        self.pos = None
        self.pause_ms = 40

    def _kc(self, nome):
        ks = self.XK.string_to_keysym(key_x(nome))
        if not ks and len(nome) == 1:
            ks = ord(nome)
        kc = self.d.keysym_to_keycode(ks) if ks else 0
        if not kc:
            raise RuntimeError("no key for %r" % nome)
        maiusc = self.d.keycode_to_keysym(kc, 0) != ks
        return kc, maiusc

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

    def muovi(self, X, Y):
        X, Y = self._limit(X, Y)
        R = self.a.ritmo
        if self.pos:
            n = R.intero(3, 8)
            for i in range(1, n):
                f = i / float(n)
                self._move(self.pos[0] + (X - self.pos[0]) * f, self.pos[1] + (Y - self.pos[1]) * f)
                time.sleep(R.intero(12, 30) / 1000.0)
        self._move(X, Y)
        time.sleep(R.intero(60, 180) / 1000.0)
        self.pos = (X, Y)
        return time.time()

    def clic(self, X, Y, bottone=0, atteso=False):
        self.muovi(X, Y)
        b = {0: 1, 1: 2, 2: 3}.get(bottone, 1)
        self.xtest.fake_input(self.d, self.X.ButtonPress, b)
        self.d.sync()
        t = time.time()
        time.sleep(self.a.ritmo.intero(50, 120) / 1000.0)
        self.xtest.fake_input(self.d, self.X.ButtonRelease, b)
        self.d.sync()
        if atteso:
            self.a.impulso(t)
        self.a.conta("clic_mouse")
        return t

    def rotella(self, X, Y, tacche, atteso=False):
        """`tacche` > 0 down (button 5), < 0 up (button 4)."""
        self.muovi(X, Y)
        b = 5 if tacche > 0 else 4
        t = None
        for _ in range(abs(tacche)):
            self.xtest.fake_input(self.d, self.X.ButtonPress, b)
            self.xtest.fake_input(self.d, self.X.ButtonRelease, b)
            self.d.sync()
            t = t or time.time()
            time.sleep(self.a.ritmo.intero(40, 160) / 1000.0)
        t = t or time.time()
        if atteso:
            self.a.impulso(t)
        self.a.conta("tacche")
        return t

    def premi(self, nome, atteso=False):
        kc, maiusc = self._kc(nome)
        sh = self._kc("Shift")[0] if maiusc else None
        if sh:
            self._down(sh)
        t = self._down(kc)
        time.sleep(self.pause_ms / 1000.0)
        self._su(kc)
        if sh:
            self._su(sh)
        time.sleep(self.pause_ms / 1000.0)
        if atteso:
            self.a.impulso(t)
        return t

    def combo(self, mod, tasto):
        mods = [self._kc(m)[0] for m in mod]
        kc, _m = self._kc(tasto.lower() if len(tasto) == 1 else tasto)
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

    def batti(self, testo, atteso=True, eco=False):
        """Every character a real key, with the person's rhythm; every ~1.5 s the heart
        (the state row and the signals).  `eco`: the character appears at once ⇒ its
        impulse also counts among the «echo» delays."""
        R = self.a.ritmo
        dur = 0.0
        sh = self._kc("Shift")[0]
        for c in testo:
            ten, bat = R.hold_ms(), R.keystroke_ms()
            kc, maiusc = self._kc(c)
            if maiusc:
                self._down(sh)
            t = self._down(kc)
            if atteso:
                self.a.impulso(t, eco=eco)
            time.sleep(ten / 1000.0)
            self._su(kc)
            if maiusc:
                self._su(sh)
            time.sleep(max(0.0, bat - ten) / 1000.0)
            dur += bat / 1000.0
            if dur >= 1.5:
                dur = 0.0
                self.a.cuore()
        self.a.conta("tasti")
        return time.time()


# ═══════════════════════════════════════════════════════════════════════════
#  THE ACTOR
# ═══════════════════════════════════════════════════════════════════════════
class Attore:
    def __init__(self, o):
        self.o = o
        self.n = o.utente
        self.profilo = "C" if o.controllo else L.profile_of(self.n)
        self.browser = "freerdp"
        self.chi = L.tenant_of(self.n)
        if o.controllo:
            # ⛔ [M] 9 Oct, test at 2K: with the SAME name at every level xrdp-sesman found again
            #   the session of the previous level (still closing) and reattached to it ⇒
            #   ERRINFO_LOGOFF_BY_USER after 1.5 s.  One name per level, always «…u99»
            #   (16-classifica recognises the check from the tail of the name).
            k = int(re.sub(r"\D", "", str(o.livello)) or 0)
            self.chi = "c16%03du99" % (900 + k % 100)
        self.parola = "c16-" + secrets.token_hex(8)
        self.porta_interna = L.porta_interna(o.scatola, self.n)
        self.ritmo = Ritmo(o.seme, self.n)
        self.cartella = os.path.join(o.dir, "controllo-corto" if o.controllo else "utente-%02d" % self.n)
        os.makedirs(self.cartella, exist_ok=True)
        self.f_state = open(os.path.join(self.cartella, "stato.jsonl"), "a", buffering=1)
        self.f_events = open(os.path.join(self.cartella, "eventi.jsonl"), "a", buffering=1)
        self.sc = Scatola(o.scatola)
        self.s = XSession(self.sc, self.chi)
        self.versione = "?"
        self.events_window, self.errors_window = [], []
        self.pulses, self.echo_pulses = [], []
        self.entrato = False
        self.desktop = (o.largo, o.alto)
        self.mani = self.sonda = self.lavoro = self.rdp = None
        self.finestra = None
        self.want_photo = self.fermati = False
        self.next_state = 0.0
        self.azioni, self.done_window = {}, 0
        self.verifiche, self.ver_window = {"ok": 0, "ko": 0}, []
        self.prec = None
        self.photo_size = None
        self.x = None                          # X connection for the photos
        self.creato = False

    # -- the rows --------------------------------------------------------------
    def _head(self, evento):
        return {"t": round(time.time(), 3), "utente": self.n, "profilo": self.profilo,
                "browser": self.browser, "versione": self.versione, "inquilino": self.chi,
                "evento": evento}

    def riga(self, **campi):
        r = self._head("stato")
        r.pop("evento")
        r.update(campi)
        self.f_state.write(json.dumps(r, ensure_ascii=False) + "\n")

    def evento(self, tipo, **campi):
        r = self._head(tipo)
        r.update(campi)
        self.f_events.write(json.dumps(r, ensure_ascii=False) + "\n")
        self.events_window.append(r)
        print("   [%02d %s] %s %s" % (self.n, self.profilo, tipo,
                                    json.dumps(campi, ensure_ascii=False)[:240]), flush=True)

    def conta(self, azione):
        self.azioni[azione] = self.azioni.get(azione, 0) + 1
        self.done_window += 1

    def verifica(self, azione, ok, lat_ms, det=""):
        self.conta(azione)
        self.verifiche["ok" if ok else "ko"] += 1
        v = {"azione": azione, "ok": bool(ok),
             "latenza_ms": None if lat_ms is None else round(lat_ms), "det": det}
        self.ver_window.append(v)
        if not ok:
            print("   [%02d %s] ⚠ input NOT verified: %s" % (self.n, self.profilo, v), flush=True)

    def impulso(self, t, eco=False):
        self.pulses.append(t)
        if eco:
            self.echo_pulses.append(t)

    # -- the heart -------------------------------------------------------------
    def cuore(self):
        if self.fermati:
            raise Fine("signal")
        if self.want_photo:
            self.want_photo = False
            self.scatta()
        if time.time() >= self.next_state:
            self.in_ritardo = time.time() - self.next_state if self.next_state else 0.0
            self.write_state()
            self.next_state = time.time() + 5.0

    def dorme(self, secondi):
        fine = time.time() + max(0.0, secondi)
        while True:
            self.cuore()
            resto = fine - time.time()
            if resto <= 0:
                return
            time.sleep(min(0.25, resto))

    def rdp_alive(self):
        return self.rdp is not None and self.rdp.poll() is None

    def log_rdp(self):
        try:
            return open(os.path.join(self.cartella, "xfreerdp.log"), errors="replace").read()[-20000:]
        except OSError:
            return ""

    def write_state(self):
        if self.sonda is None:
            return
        ora = time.time()
        n, dt_list = self.sonda.leggi()
        errori = list(self.errors_window)
        if self.sonda.errore:
            errori.append("the XDamage probe has stopped: %s" % self.sonda.errore)
        caduta = False
        if self.entrato and not self.rdp_alive():
            caduta = True
            errori.append("xfreerdp exited (code %s): %s" % (
                self.rdp.returncode if self.rdp else None,
                drop_from_log(self.log_rdp()) or "no error line"))
        blocco, lavoro, ritardi, eco = None, False, [], []
        if self.profilo == "D":
            if self.video_in_progress():
                blocco = pausa_piu_lunga(dt_list, self.prec[0] if self.prec else ora - 5, ora)
                lavoro = True
        else:
            ritardi, self.pulses = attese_impulsi(self.pulses, dt_list, ora)
            eco, self.echo_pulses = attese_impulsi(self.echo_pulses, dt_list, ora)
            if ritardi:
                blocco, lavoro = max(ritardi), True
        conti = {"dipinti": n}
        campi = {"conti": conti, "input": self.ver_window,
                 "blocco_max_ms": None if blocco is None else round(blocco * 1000),
                 "ritardi_ms": [round(x * 1000, 1) for x in ritardi],
                 "ritardi_eco_ms": [round(x * 1000, 1) for x in eco],
                 "lavoro": lavoro, "caduta": caduta, "errori": errori,
                 "sessione": self.rdp_alive(), "sistema": "xrdp"}
        if self.prec:
            dt = ora - self.prec[0]
            campi["delta"] = {"dipinti": n - self.prec[1], "s": round(dt, 2)}
            if dt > 0:
                campi["dipinti_s"] = round((n - self.prec[1]) / dt, 2)
        self.prec = (ora, n)
        campi["in_ritardo_s"] = round(getattr(self, "in_ritardo", 0.0), 2)
        campi.update({"azioni": dict(self.azioni), "azioni_finestra": self.done_window,
                      "verifiche": dict(self.verifiche)})
        if self.lavoro is not None:
            try:
                campi["dettagli_lavoro"] = self.lavoro.extra()
            except Exception as e:                  # noqa: BLE001
                campi["dettagli_lavoro"] = {"errore": str(e)[:200]}
        if self.events_window:
            campi["eventi"] = self.events_window
        self.done_window = 0
        self.ver_window, self.errors_window, self.events_window = [], [], []
        self.riga(**campi)

    def video_in_progress(self):
        v = getattr(self.lavoro, "ultimo_video", None) or {}
        return self.entrato and v.get("stato") == 1

    # -- the photos ------------------------------------------------------------
    def foto_pil(self):
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

    def scatta(self):
        t = time.time()
        im = self.foto_pil()
        if im is None:
            self.evento("foto", ok=False, perche="the Xvfb cannot be photographed")
            return
        f = os.path.join(self.cartella, "foto-%d.png" % int(t * 1000))
        im.save(f)
        self.evento("foto", ok=True, file=f, ms=round((time.time() - t) * 1000))

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
        cmd = ["xfreerdp3", "/v:127.0.0.1", "/u:%s" % self.chi, "/p:%s" % self.parola,
               "/cert:ignore", "/gfx", "/f", "/sound:sys:fake",
               "/wm-class:remotix-rdp-%02d" % self.n]
        amb = dict(os.environ, DISPLAY=self.o.display)
        amb.pop("WAYLAND_DISPLAY", None)
        log = open(os.path.join(self.cartella, "xfreerdp.log"), "a")
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

    def entra(self):
        o = self.o
        n = {"inquilino": self.chi, "browser": self.browser, "versione": self.versione,
             "scatola": o.scatola, "sistema": "xrdp", "misura": [o.largo, o.alto]}
        t0 = time.time()
        self.turn_on_rdp()
        n["accesso_ms"] = round(t0 * 1000)
        # the FreeRDP window, then the probe
        while time.time() < t0 + o.tetto_s and self.finestra is None:
            if not self.rdp_alive():
                c = drop_from_log(self.log_rdp())
                n.update(esito="rifiuto" if c and "AUTH" in c.upper() else "nessun_fotogramma",
                         motivo="xfreerdp exited before the window: %s" % c)
                return n
            self.finestra = self.search_window()
            if self.fermati:
                raise Fine("signal")
            time.sleep(0.1)
        if self.finestra is None:
            n.update(esito="nessun_fotogramma", motivo="no FreeRDP window in %d s" % o.tetto_s)
            return n
        self.sonda = Probe(o.display, self.finestra)
        self.sonda.start()
        # the live desktop: the tenant's X session is there, and the photo is not degenerate
        primo, sessione, colori, last_ctl = None, False, None, 0.0
        while time.time() < t0 + o.tetto_s:
            if self.fermati:
                raise Fine("signal")
            if not self.rdp_alive():
                n.update(esito="nessun_fotogramma", motivo="xfreerdp exited during access: %s"
                         % drop_from_log(self.log_rdp()))
                return n
            if not sessione and time.time() - last_ctl > 1.0:
                last_ctl = time.time()
                sessione, _d = self.s.pronta()
            im = self.foto_pil()
            colori = colori_distinti(im) if im is not None else None
            if sessione and colori is not None and colori >= ALIVE_COLORS:
                primo = time.time()
                break
            time.sleep(0.25)
        n["primo_fotogramma_ms"] = round(primo * 1000) if primo else None
        n["nascita_ms"] = round((primo - t0) * 1000) if primo else None
        n["colori_distinti"] = colori
        n["sessione_x"] = sessione
        n["prima_raffica_ms"] = round(self.sonda.leggi()[1][0] * 1000) if self.sonda.leggi()[1] else None
        if not primo:
            if sessione:
                # the session is there but the desktop stays degenerate: work goes on anyway
                n["primo_fotogramma_ms"] = n["prima_raffica_ms"]
                n["nascita_ms"] = (n["prima_raffica_ms"] - n["accesso_ms"]) if n["prima_raffica_ms"] else None
                n.update(esito="degenere", motivo="degenerate desktop (%s colours) at %d s" % (colori, o.tetto_s))
            else:
                n.update(esito="nessun_fotogramma", motivo="no X session in %d s" % o.tetto_s)
            return n
        verde = primo - t0 <= CAP_DEGENERATE_S
        n["esito"], nota = outcome_birth(verde, not verde)
        if not verde:
            n["esito"] = "degenere"
            n["motivo"] = "the desktop is alive only at %.1f s from access (cap %d s)" % (
                primo - t0, CAP_DEGENERATE_S)
        else:
            n["motivo"] = "X session and %s distinct colours at %.1f s" % (colori, primo - t0)
        if nota:
            n["nota"] = nota
        return n

    def prepare_tenant(self):
        self.sc.sgombera(self.chi)
        c, t = self.sc.crea(self.chi, self.parola)
        if c != 0:
            raise RuntimeError("I could not create the tenant %s: %s" % (self.chi, (t or "")[-200:]))
        self.creato = True
        self.sc.dentro("h=/home/%s; [ -L $h/.cache ] && rm -f $h/.cache; "
                       "install -d -o %s -g %s -m 700 $h/.cache" % (self.chi, self.chi, self.chi), 30)
        # ⭐ ~/.xsession comes from the skeleton (Contenitore.xrdp): we LOOK that it is there
        c, t = self.sc.dentro("cat /home/%s/.xsession" % self.chi, 30)
        if c != 0 or "exec " not in (t or ""):
            self.evento("errore", testo="the tenant's ~/.xsession is missing: the session would not be "
                                        "the desktop (%s)" % (t or "")[:120])
            raise RuntimeError("~/.xsession absent in the tenant %s" % self.chi)
        self.evento("xsession", testo=(t or "").strip().splitlines()[-1][:120])

    # -- everything -------------------------------------------------------------
    def corri(self):
        o = self.o
        self.versione = (subprocess.run(["xfreerdp3", "/version"], capture_output=True, text=True)
                         .stdout.strip().splitlines() or ["?"])[0][:80]
        self.evento("inizio", inquilino=self.chi, scatola=o.scatola, display=o.display, seme=o.seme,
                    porta_interna=self.porta_interna, misura=[o.largo, o.alto], video=o.video or None,
                    pid=os.getpid(), sistema="xrdp")
        codice = 2
        try:
            self.prepare_tenant()
            self.lavoro = L.JOBS[self.profilo](self)
            self.lavoro.prepara()
            nascita = self.entra()
            with open(os.path.join(self.cartella, "nascita.json"), "w") as f:
                json.dump(nascita, f, ensure_ascii=False, indent=1)
            self.evento("nascita", **nascita)
            if not works_after_birth(nascita):
                codice = 1
                self.save_diagnosis()
                if o.controllo:
                    return codice
                self.wait_end("access failed")
                return codice
            self.entrato = True
            self.mani = Mani(self)
            # the keyboard focus on the FreeRDP window (in the Xvfb there is no
            # window manager), then a click on an empty spot of the desktop
            try:
                from Xlib import X
                self.mani.d.create_resource_object("window", self.finestra).set_input_focus(
                    X.RevertToParent, X.CurrentTime)
                self.mani.d.sync()
            except Exception as e:                   # noqa: BLE001
                self.evento("errore", testo="focus on the FreeRDP window: %r" % e)
            self.dorme(1.0)
            self.mani.clic(self.desktop[0] * 0.55, self.desktop[1] * 0.55)
            self.dorme(1.0)
            codice = 0
            for prova in range(3):
                ok, m = self.lavoro.avvia()
                self.evento("applicazione", ok=ok, testo=m, tentativo=prova + 1)
                if ok:
                    break
                self.dorme(10)
            else:
                codice = 1
                if o.controllo:
                    self.esiti_controllo = {"applicazione": False}
                    return codice
                self.wait_end("the application does not start")
                return codice
            if o.controllo:
                ok = self.lavoro.comando("uname -a")
                self.esiti_controllo = {"applicazione": True, "comando": ok}
                return 0 if ok else 1
            errori = 0
            while True:
                try:
                    self.lavoro.passo()
                    errori = 0
                except Fine:
                    raise
                except Exception as e:               # noqa: BLE001
                    errori += 1
                    self.errors_window.append("%r" % e)
                    self.evento("errore", testo="%r" % e, dove=traceback.format_exc()[-600:],
                                di_fila=errori)
                    self.dorme(min(30, 2 * errori))
        except Fine:
            pass
        except Exception as e:                       # noqa: BLE001
            self.evento("errore", testo="%r" % e, dove=traceback.format_exc()[-800:], fatale=True)
            codice = 2
        finally:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            self.chiudi()
        return codice

    def save_diagnosis(self):
        """A failed birth: ~/.xsession-errors and the tenant's Xorg log
        in the folder, BEFORE the clean-up deletes them."""
        c, t = self.sc.dentro("for f in /home/%s/.xsession-errors /home/%s/.xorgxrdp.*.log; do "
                              "echo \"== $f\"; tail -n 60 \"$f\" 2>/dev/null; done" % (self.chi, self.chi), 60)
        with open(os.path.join(self.cartella, "diagnosi-sessione.txt"), "w") as f:
            f.write(t or "")

    def wait_end(self, perche):
        self.evento("in_attesa", perche=perche)
        while True:
            self.dorme(5)

    def chiudi(self):
        try:
            try:
                self.write_state()
            except Exception:                        # noqa: BLE001
                pass
            if self.sonda is not None:
                self.sonda.ferma()
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
            if self.creato:
                try:
                    self.sc.sgombera(self.chi)
                except Exception as e:               # noqa: BLE001
                    print("   ⚠ exit: %s" % e, flush=True)
            _c, t = self.sc.dentro("id %s >/dev/null 2>&1 && echo RESTA || echo via" % self.chi, 30)
            self.evento("fine", sgomberato=(t or "").strip().endswith("via"), azioni=self.azioni,
                        verifiche=self.verifiche)
            self.f_state.close()
            self.f_events.close()


def controllo(o, att):
    """The reduced short check (§7.3): enters, screen, keyboard ⇒ controllo-corto.json."""
    t = time.time()
    codice = att.corri()
    try:
        na = json.load(open(os.path.join(att.cartella, "nascita.json")))
    except (OSError, ValueError):
        na = {}
    es_ctl = getattr(att, "esiti_controllo", {}) or {}
    acc = bool(na.get("primo_fotogramma_ms") or na.get("prima_raffica_ms"))
    esiti = {"RDP-accesso": "PASS" if acc else "FAIL",
             "RDP-schermo": "PASS" if na.get("esito") == "ok" else ("FAIL" if acc else "BLOCKED"),
             "RDP-tastiera": ("PASS" if es_ctl.get("applicazione") and es_ctl.get("comando") else
                              ("FAIL" if es_ctl else "BLOCKED"))}
    nas = {"nascita_s": round(na["nascita_ms"] / 1000.0, 2) if na.get("nascita_ms") is not None else None,
           "primo_non_degenere_s": round(na["nascita_ms"] / 1000.0, 2)
           if na.get("esito") == "ok" and na.get("nascita_ms") is not None else None,
           "rifiuto": na.get("esito") == "rifiuto", "esito": "PASS" if na.get("esito") == "ok" else "FAIL",
           "ragione": na.get("motivo")}
    out = {"utente": 99, "inquilino": att.chi, "browser": "freerdp", "versione": att.versione,
           "sistema": "xrdp", "esiti": esiti, "nascita": nas, "codice": codice,
           "esito": "FAIL" if "FAIL" in esiti.values() else ("PASS" if all(
               v == "PASS" for v in esiti.values()) else "BLOCKED"),
           "durata_s": round(time.time() - t, 1),
           "nota": "REDUCED short check (fasi/20 §7.3): access, screen, keyboard — the REMOTIX page's "
                   "F-0xx functions do not exist in xrdp"}
    with open(os.path.join(o.dir, "controllo-corto.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print("xrdp short check: %s %s" % (out["esito"], esiti), flush=True)
    return 0 if out["esito"] == "PASS" else 1


def argomenti():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--certifica", action="store_true")
    a.add_argument("--controllo", action="store_true", help="the reduced short check (user 99)")
    a.add_argument("--scatola", choices=DESKTOP)
    a.add_argument("--utente", type=int)
    a.add_argument("--display", help="this user's Xvfb (:2NN)")
    a.add_argument("--dir")
    a.add_argument("--seme", default="0")
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    a.add_argument("--video", default="")
    a.add_argument("--tetto-s", type=int, default=60)
    # accepted and ignored: the climb passes them equally to both actors
    a.add_argument("--porte-base", type=int, default=0)
    a.add_argument("--livello", default="")
    a.add_argument("--browser", default="")
    o = a.parse_args()
    if o.certifica:
        return o
    if o.controllo:
        o.utente = 99
        o.seme = o.seme if o.seme != "0" else "controllo"
    for k in ("scatola", "utente", "display", "dir"):
        if getattr(o, k) in (None, ""):
            a.error("--%s is needed" % k)
    return o


def main():
    o = argomenti()
    if o.certifica:
        return certifica()
    try:
        open("/proc/self/oom_score_adj", "w").write("800")      # §7.7: the clients die first
    except OSError:
        pass
    os.environ.pop("WAYLAND_DISPLAY", None)
    att = Attore(o)

    def _fine(_n, _f):
        att.fermati = True

    def _photo(_n, _f):
        att.want_photo = True
    signal.signal(signal.SIGTERM, _fine)
    signal.signal(signal.SIGINT, _fine)
    signal.signal(signal.SIGUSR1, _photo)
    print("⭐ xrdp actor %02d · %s · profile %s · %s · %s" % (
        o.utente, o.scatola, att.profilo, o.display, att.chi), flush=True)
    if o.controllo:
        return controllo(o, att)
    return att.corri()


if __name__ == "__main__":
    sys.exit(main())
