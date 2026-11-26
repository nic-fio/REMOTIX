"""lib - everything the checks of prove/ share, in one place: results and verdicts, the box, ONE headless compositor, the two
browser drivers (Chrome by the DevTools protocol over a hand-made WebSocket, Firefox by Marionette; no framework), and the
Rig = compositor + browser + user + the things every check does with them (open the page, log in, wait for the desktop, test
window in the session, real key chords).

Rules that make the tools reliable when several runs share the dev server (the reasons are in the comments below):
  * nothing is shared between runs: every compositor has its own runtime dir, every browser its own profile and a port the OS
    picks (DevTools / Marionette port 0, read back from the profile): one run can never talk to, or close, another run's browser;
  * every wait has a deadline and every failure of the TOOL is a ToolError that says why (browser exited? no answer?);
    a whole run has a deadline too (guard());
  * compositor and browsers die with the check (they are the check's children, killed with it even by SIGKILL) and are stopped
    in `finally`, on SIGTERM and at exit;
  * the product being dead (page not answering, login refused for a valid user) is a Fail = FAIL, never a tool error."""
import atexit
import base64
import ctypes
import hashlib
import io
import json
import os
import re
import secrets
import shutil
import signal
import socket
import struct
import subprocess
import sys
import tempfile
import time
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
BOXES = os.path.join(HERE, "boxes") if os.path.isdir(os.path.join(HERE, "boxes")) else os.path.join(HERE, "..", "boxes")
SHOTS, WORK = os.path.join(HERE, "shots"), os.path.join(HERE, "work")
PASS, FAIL, BLOCKED = "PASS", "FAIL", "BLOCKED"
PORTS = {"xfce": 8811, "lxqt": 8812, "gnome": 8813, "kde": 8814}  # boxes/box.sh header
if os.environ.get("RX_BANCO") == "vm":  # the four QEMU VMs of server/vm-radeon.sh instead of the containers: banco-vm/box.sh answers as box.sh
    BOXES = os.path.join(HERE, "banco-vm")
    PORTS = {"gnome": 8861, "kde": 8862, "xfce": 8863, "lxqt": 8864}  # VMs gnome kde xfce lxqt (hostname rx-deb-<name>)
SOUND = "/run/user/%d/pulse/native" % os.getuid()  # the host's PipeWire-pulse (server/prepara-server.sh), for Firefox audio


class ToolError(RuntimeError):
    """The tool could not look (BLOCKED)."""


class Fail(Exception):
    """The product did not do it (FAIL)."""


class NavError(Fail):
    """The page does not answer (connection refused, reset, timed out...): a dead product."""


# --------------------------------------------------------------------------------------------------------- results
class Results:
    """One line per check: `PASS|FAIL|BLOCKED <name> - evidence`. Exit code 0 only if every name is PASS."""

    def __init__(self, names):
        self.names, self.d = list(names), {}

    def say(self, status, name, evidence):
        self.d[name] = status
        print("%s %s - %s" % (status, name, str(evidence).replace("\n", " ")), flush=True)

    def pending(self):
        return [n for n in self.names if n not in self.d]

    def attempt(self, name, fn):
        """fn() returns (status, evidence); a Fail raised is a FAIL, anything else a BLOCKED, naming what happened."""
        try:
            st, ev = fn()
        except Fail as e:
            st, ev = FAIL, str(e)
        except Exception as e:  # noqa: BLE001 - a broken tool step is BLOCKED, never a PASS
            st, ev = BLOCKED, tool_error(e)
        self.say(st, name, ev)

    def sequence(self, fn, total=600):
        """fn() says the checks in order under the deadline `total`. What it leaves unsaid when it stops: the first name is
        FAIL if it ended with a Fail, BLOCKED if the tool broke; the others BLOCKED."""
        guard(total)
        try:
            fn()
        except Fail as e:
            self.rest(FAIL, str(e))
        except Exception as e:  # noqa: BLE001
            self.rest(BLOCKED, tool_error(e))
        finally:
            signal.alarm(0)
        return self.code()

    def rest(self, status, why):
        for i, n in enumerate(self.pending()):
            self.say(status if i == 0 else BLOCKED, n, why if i == 0 else "an earlier check stopped the run")

    def code(self):
        return 0 if all(self.d.get(n) == PASS for n in self.names) else 1


def tool_error(e):
    import traceback
    return "tool error: %s: %s (line %s)" % (type(e).__name__, str(e)[:300], traceback.extract_tb(e.__traceback__)[-1].lineno)


def guard(seconds):
    """A whole-run deadline (SIGALRM -> ToolError) and a clean stop on SIGTERM/SIGHUP (finally blocks and atexit run)."""
    def late(*_):
        raise ToolError("the whole run did not finish in %d s" % seconds)
    signal.signal(signal.SIGALRM, late)
    for s in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(s, lambda *_: sys.exit(143))
    tempo = os.environ.get("RX_TEMPO", "1")  # a slower bench (the VMs): an integer >= 1, anything else is refused (never "no deadline")
    if not tempo.isdigit() or int(tempo) < 1:
        raise ToolError("RX_TEMPO must be an integer >= 1 (got %r)" % tempo)
    signal.alarm(seconds * int(tempo))


# ------------------------------------------------------------------------------------------------- the box
class Box:
    def __init__(self, name):
        self.name, self.sh = name, os.path.join(BOXES, "box.sh")

    def run(self, cmd, stdin=None, timeout=90):
        try:
            r = subprocess.run([self.sh, "ssh", self.name, cmd], input=stdin, capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired:
            raise ToolError("the box %s did not answer in %d s: %.80s" % (self.name, timeout, cmd))
        return r.returncode, (r.stdout + r.stderr).strip()

    def end_users(self, users, cap=40):
        """End the sessions of these users (only the ones that exist) and wait until no process and no logind session of them is
        left (SIGKILL after half the time). Returns the users that could not be got rid of. A user that does not exist has no
        session: that is not an error."""
        script = ("for u in %s; do id -u $u >/dev/null 2>&1 || continue; pkill -u $u -f rx-window; loginctl terminate-user $u 2>/dev/null; done; "
                  "for i in $(seq %d); do left=; for u in %s; do id -u $u >/dev/null 2>&1 || continue; "
                  "[ -n \"$(pgrep -u $u | head -1)$(loginctl list-sessions --no-legend | awk -v u=$u '$3==u' | head -1)\" ] && left=\"$left $u\"; done; "
                  "[ -z \"$left\" ] && break; [ $i = %d ] && pkill -KILL -u $(echo $left | tr ' ' ,); sleep 1; done; echo \"left:$left\"") % (
            " ".join(users), cap, " ".join(users), cap // 2)
        c, t = self.run(script, timeout=cap + 30)
        lines = [l for l in t.splitlines() if l.startswith("left:")]
        return lines[-1][5:].split() if lines else ["(no answer)"]

    def x_shortage(self, user):
        """The line of the user's session log that says the session could not get an X display (the 33 numbers are shared with
        the host and every box: --network=host), or ''. Only a recent log counts."""
        f = "/home/%s/.local/state/remotix/session.log" % user
        return self.run("[ -n \"$(find %s -mmin -4 2>/dev/null)\" ] && tail -n 80 %s | grep -iE 'xwayland/sockets|No display available|X11-unix.*(in use|bind)' | tail -1; true" % (f, f))[1].strip()[:200]

    def ensure_user(self, user, password):
        """Every check makes the users it needs, with its own names, and sets the password it will use: it never tries a login
        that could be a wrong password (the product bans the client address after repeated failures). The first time in this
        process an earlier session of the user is ended (so the first login is a NEW one); every user made here has its
        session ended when the check ends, on success or failure (a session lives on after its client: they would pile up)."""
        key = (self.name, user)
        if key not in _made:
            _made.add(key)
            self.end_users([user])
            _register_cleanup()
        c, t = self.run("id %s >/dev/null 2>&1 || useradd -m -s /bin/bash %s; echo '%s:%s' | chpasswd && "
                        "usermod -aG video,$(getent group render >/dev/null && echo render,)users %s 2>/dev/null; id -u %s" % ((user, user, user, password, user, user)))
        if c:
            raise ToolError("cannot create the user %s in the box: %s" % (user, t[-150:]))

    def in_session(self, user, cmd):
        """Run `cmd` detached as the user, in the user's graphical session environment."""
        c, t = self.run("u=$(id -u %s); d=$(ls /run/user/$u | grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] || { echo no wayland socket; exit 3; };"
                        " setsid runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d GDK_BACKEND=wayland bash -c %s"
                        " </dev/null >/dev/null 2>&1 & sleep 0.5; echo started" % (user, user, "'" + cmd.replace("'", "'\\''") + "'"))
        if c:
            raise ToolError("cannot run in the session of %s: %s" % (user, t[-150:]))

    def apparmor(self, since):
        """AppArmor lines about the profile of REMOTIX (remotix_network, or a child of it: remotix_network//...) from the epoch `since`.
        Returns (checked, lines, why). `checked` False = the log could not be read: the caller says «AppArmor NOT checked», never «none».
        Both apparmor="DENIED" (enforce) and apparmor="ALLOWED" (complain, the mode of the package) mean the profile does not cover what the
        program did. Source: the kernel journal; /var/log/audit/audit.log too when it exists (auditd is not there on Debian by default).
        The leading space before profile= leaves out peer_profile= and the lines of other programs' profiles (apparmor="STATUS" is not matched)."""
        pat = "grep -E 'apparmor=\"(DENIED|ALLOWED)\"' | grep -E ' profile=\"remotix_network(//[^\"]*)?\"'"
        c, t = self.run("grep -qE '^remotix_network ' /sys/kernel/security/apparmor/profiles 2>/dev/null || { echo RXNOPROFILE; exit 0; }; "
                        "journalctl -k --no-pager -n 1 -o cat >/dev/null 2>&1 || { echo RXNOLOG; exit 0; }; "
                        "o=$(journalctl -k --no-pager -o cat --since @%d 2>&1); rc=$?; "
                        "if [ $rc -ne 0 ] && ! echo \"$o\" | grep -q 'No entries'; then echo RXNOLOG; exit 0; fi; echo RXOK; "
                        "printf '%%s\\n' \"$o\" | %s | cut -c1-400 | tail -200; "
                        "if [ -r /var/log/audit/audit.log ]; then echo RXAUDIT; cat /var/log/audit/audit.log | %s | cut -c1-400 | tail -200; fi; true" % (since, pat, pat))
        rows = t.splitlines()
        if "RXNOPROFILE" in rows:
            return False, [], "profile not loaded (remotix_network is not in /sys/kernel/security/apparmor/profiles, or AppArmor is off)"
        if c != 0 or "RXOK" not in rows:
            return False, [], "the kernel journal could not be read (exit %d: %.100s)" % (c, t.replace("\n", " "))
        lines, in_audit = [], False
        for r in rows[rows.index("RXOK") + 1:]:
            if r == "RXAUDIT":
                in_audit = True
                continue
            m = re.search(r"audit\((\d+)", r)
            if in_audit and m and int(m.group(1)) < since:
                continue
            lines.append(r)
        return True, lines, ""

    @staticmethod
    def apparmor_summary(lines, n=5):
        """A short text for the lines found: how many ALLOWED (complain) and DENIED (enforce), and the first few distinct operations."""
        al = sum('apparmor="ALLOWED"' in l for l in lines)
        de = sum('apparmor="DENIED"' in l for l in lines)
        seen = []
        for l in lines:
            kv = {k: re.search(k + r'="([^"]*)"', l) for k in ("apparmor", "operation", "name", "comm", "profile")}
            e = " ".join("%s=%s" % (k, kv[k].group(1)) for k in ("apparmor", "profile", "operation", "name", "comm") if kv[k])
            if e not in seen:
                seen.append(e)
        return "%d ALLOWED (profile in complain mode: nothing blocked, but the profile does not cover it), %d DENIED (profile enforcing: blocked): %s" % (
            al, de, " | ".join(seen[:n]))

    def journal(self, grep, since="-4min", n=8):
        t = self.run("journalctl -u remotix --no-pager -o cat --since '%s' | grep -iE '%s' | grep -v 'rate of\\|quic-net\\|loop: \\|not there YET\\|not on the bus\\|DIGITAL silence' | tail -%d; true" % (since, grep, n))[1]
        return " | ".join(x.strip()[:160] for x in t.splitlines()) or "(no remotix journal line for %s)" % grep


_made, _cleanup_on = set(), []


def _register_cleanup():
    if not _cleanup_on:
        _cleanup_on.append(1)
        atexit.register(finish_users)


def finish_users():
    """At the end of a check (also after an exception or SIGTERM): the sessions of the users this process made are ended."""
    signal.alarm(0)  # the run's deadline no longer applies: the cleanup must finish
    by_box = {}
    for b, u in sorted(_made):
        by_box.setdefault(b, []).append(u)
    for b, us in by_box.items():
        try:
            left = Box(b).end_users(us)
            if left:
                print("NOTE cleanup - could not end the sessions of %s in %s" % (" ".join(left), b), flush=True)
        except Exception as e:  # noqa: BLE001
            print("NOTE cleanup - %s: %s" % (b, e), flush=True)


def sweep(boxname):
    """The final sweep of all.sh: every test user (the names the checks make) of the box has its session ended."""
    box = Box(boxname)
    t = box.run("getent passwd | cut -d: -f1 | grep -E '^(bc|lc|mu|rs|ac|cb|bn|dkf?|md|in|ph|pl)[0-9]+$'; true")[1].split()
    left = box.end_users(t) if t else []
    print("sweep %s: %d test user(s) ended%s" % (boxname, len(t), ("; NOT gone: " + " ".join(left)) if left else ""))
    return 1 if left else 0


# the desktop shell of each box must be running (and, on KDE, the splash screen gone) before the picture is judged
SHELL_UP = {"xfce": "pgrep -u %(u)s xfce4-panel", "lxqt": "pgrep -u %(u)s lxqt-panel", "gnome": "pgrep -u %(u)s gnome-shell",
            "kde": "pgrep -u %(u)s plasmashell && ! pgrep -u %(u)s ksplashqml"}

# page ids and counters as in src/page.html
JS_FORM = ("const f=document.getElementById('signin-form'); const v=e=>!!e&&getComputedStyle(e).display!=='none'"
           "&&e.getBoundingClientRect().width>0; return {title:document.title, form:v(f), user:!!document.getElementById('username'),"
           " pw:!!document.getElementById('password'), btn:!!document.getElementById('signin-button'), remotix:!!window.REMOTIX,"
           " ready:document.readyState};")
JS_ENTER = ("const u=document.getElementById('username'),p=document.getElementById('password'),m=document.getElementById('signin-form');"
            "u.value=arguments[0]; p.value=arguments[1]; u.dispatchEvent(new Event('input',{bubbles:true}));"
            "p.dispatchEvent(new Event('input',{bubbles:true})); m.requestSubmit(document.getElementById('signin-button')); return 1;")
JS_STATE = ("const R=window.REMOTIX, s=R&&R.viewer, o=document.getElementById('outcome'), t=document.getElementById('viewer');"
            "const r=t?t.getBoundingClientRect():null; return {session:!!(s&&s.session), cls:o?o.className:'', outcome:o?o.textContent:'',"
            " painted:s&&s.counts?s.counts.painted:0, delivered:s&&s.counts?s.counts.delivered:0, input:!!window.REMOTIX_INPUT,"
            " rect:r?[r.left,r.top,r.width,r.height]:null, vw:innerWidth, vh:innerHeight,"
            " log:(document.getElementById('logbook')||{}).textContent||''};")


# ------------------------------------------------------------------------------------------------- pictures
def frac(png, rgb, tol=120):
    """Share of the picture (160x120 reduction) near the colour rgb: `tol` is the sum of the channel differences, or a tuple
    of one limit per channel."""
    from PIL import Image
    pic = Image.open(io.BytesIO(png)).convert("RGB")
    pic = pic.resize((min(160, pic.width), min(120, pic.height)))
    if isinstance(tol, int):
        n = sum(1 for p in pic.getdata() if sum(abs(p[i] - rgb[i]) for i in range(3)) < tol)
    else:
        n = sum(1 for p in pic.getdata() if all(abs(p[i] - rgb[i]) < tol[i] for i in range(3)))
    return n / (pic.width * pic.height)


def judge_pixel(png):
    """(degenerate, description). Degenerate = (nearly) one colour: black, grey, waiting colour. A real desktop has at
    least a panel or an icon: >= 6 distinct colours (5 bits per channel) on a 160x120 reduction."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    pic = im.resize((min(160, im.width), min(120, im.height)))
    count = {}
    for r, g, b in pic.getdata():
        k = (r >> 3, g >> 3, b >> 3)
        count[k] = count.get(k, 0) + 1
    dom = max(count.values()) / (pic.width * pic.height)
    return len(count) < 6, "%dx%d, %d distinct colours, dominant %.1f%%" % (im.width, im.height, len(count), 100 * dom)


def settled(a, b):
    """True when two PNG pictures differ by less than 1 grey level on average (160x120 reduction): nothing is moving."""
    from PIL import Image, ImageChops, ImageStat
    x, y = (Image.open(io.BytesIO(p)).convert("L").resize((160, 120)) for p in (a, b))
    return ImageStat.Stat(ImageChops.difference(x, y)).mean[0] < 1.0


# ----------------------------------------------------------------------------------------- processes and compositor
def _die_with_parent():
    """Child of the check: SIGKILLed by the kernel if the check itself dies (even by SIGKILL), so nothing is leaked."""
    ctypes.CDLL("libc.so.6", use_errno=True).prctl(1, signal.SIGKILL)  # PR_SET_PDEATHSIG


def spawn(cmd, env, log):
    return subprocess.Popen(cmd, env=env, stdin=subprocess.DEVNULL, stdout=open(log, "wb"), stderr=subprocess.STDOUT,
                            start_new_session=True, preexec_fn=_die_with_parent)


def reap(p, grace=5):
    """Stop a spawned process and everything in its group: SIGTERM, then SIGKILL; always waits."""
    for sig, wait in ((signal.SIGTERM, grace), (signal.SIGKILL, 5)):
        try:
            os.killpg(p.pid, sig)
        except OSError:
            pass
        try:
            p.wait(wait)
            break
        except subprocess.TimeoutExpired:
            continue
    try:
        os.killpg(p.pid, signal.SIGKILL)  # stragglers of the group
    except OSError:
        pass


def tail(path, n=300):
    try:
        with open(path, "rb") as f:
            f.seek(0, 2)
            f.seek(max(0, f.tell() - n))
            return f.read().decode("utf-8", "replace").strip().replace("\n", " | ")
    except OSError:
        return ""


class Compositor:
    """A headless labwc (no screen, software rendering) for the test browser, in a runtime dir of its own (mode 700).
    The pid we hold IS labwc's, so stop() really stops it (the old shell helper stopped a setsid wrapper and leaked a
    labwc per run)."""

    def __init__(self, tag):
        self.dir = "/run/user/%d/rx-%s-%d-%s" % (os.getuid(), tag, os.getpid(), secrets.token_hex(2))
        self.p, self.sock = None, None

    def start(self):
        os.makedirs(self.dir, mode=0o700, exist_ok=True)
        env = {k: v for k, v in os.environ.items() if k not in ("WAYLAND_DISPLAY", "DISPLAY")}
        env.update(XDG_RUNTIME_DIR=self.dir, WLR_BACKENDS="headless", WLR_RENDERER="pixman", WLR_LIBINPUT_NO_DEVICES="1")
        # labwc starts Xwayland and dies when the shared server has no X display number free at that instant: try again
        for attempt in range(1, 7):
            for n in os.listdir(self.dir):
                if n.startswith("wayland-"):
                    os.unlink(os.path.join(self.dir, n))
            # labwc in its own user+network+mount namespace: it starts Xwayland, whose display number (33 of them) and sockets
            # (abstract ones: one namespace per network namespace; /tmp/.X<n>-lock) are shared by the host and the boxes
            # (--network=host), and a full run used them all up. Here it has its own, so it takes none of the real ones.
            self.p = spawn(["unshare", "--user", "--map-root-user", "--net", "--mount", "sh", "-c", "mount -t tmpfs tmpfs /tmp && exec labwc"],
                           env, self.dir + "/labwc.log")
            end = time.time() + 8
            while time.time() < end and self.p.poll() is None and not self._socket():
                time.sleep(0.2)
            if self._socket():
                time.sleep(1)  # it can still die right after opening the socket
                if self.p.poll() is None:
                    break
            reap(self.p, 2)
            time.sleep(attempt * 2)
        else:
            raise ToolError("labwc did not stay up in 6 tries: %s" % tail(self.dir + "/labwc.log"))
        self.sock = self._socket()
        e = dict(env, WAYLAND_DISPLAY=self.sock)
        try:
            out = subprocess.run(["wlr-randr"], env=e, capture_output=True, text=True, timeout=10).stdout.split()[0]
            subprocess.run(["wlr-randr", "--output", out, "--custom-mode", "1600x1000"], env=e, capture_output=True, timeout=10)
        except Exception:  # noqa: BLE001 - the default size is good enough
            pass
        return dict(env, WAYLAND_DISPLAY=self.sock, XDG_SESSION_TYPE="wayland")

    def _socket(self):
        s = [n for n in os.listdir(self.dir) if re.fullmatch(r"wayland-\d+", n)]
        return s[0] if s else None

    def stop(self):
        if self.p:
            reap(self.p, 3)
            self.p = None
        shutil.rmtree(self.dir, ignore_errors=True)


# ------------------------------------------------------------------------------------------------------ browsers
MAGIC = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
KEYS = {"Escape": ("Escape", "Escape", 27)}
NET_ERRORS = ("CONNECTION", "ERR_NAME", "ERR_ADDRESS", "ERR_TIMED_OUT", "ERR_EMPTY_RESPONSE", "ERR_SSL", "ERR_QUIC", "neterror",
              "connectionFailure", "netTimeout", "Reached error page")


def key_info(ch):
    """(key, code, windows virtual key) of one typed character (a-z, 0-9, space, '-')."""
    if ch.isalpha():
        return ch, "Key" + ch.upper(), ord(ch.upper())
    if ch.isdigit():
        return ch, "Digit" + ch, ord(ch)
    return {" ": (" ", "Space", 32), "-": ("-", "Minus", 189)}[ch]


def wait_file(path, p, cap, what):
    """The port a browser opened with port 0, read back from its profile; ends early if the browser exits."""
    end = time.time() + cap
    while time.time() < end:
        try:
            return open(path).read().split()[0]
        except (OSError, IndexError):
            pass
        if p.poll() is not None:
            raise ToolError("%s exited (code %s) before opening its control port; log: %s" % (what, p.returncode, tail(os.path.dirname(path) + "/out.log")))
        time.sleep(0.3)
    raise ToolError("%s did not open its control port in %d s; log: %s" % (what, cap, tail(os.path.dirname(path) + "/out.log")))


class Ws:
    """Client WebSocket: text frames, masked, no extensions. Every read has a deadline."""

    def __init__(self, host, port, path, timeout=30):
        self.s = socket.create_connection((host, port), timeout=10)
        self.s.settimeout(timeout)
        key = base64.b64encode(os.urandom(16)).decode()
        self.s.sendall(("GET %s HTTP/1.1\r\nHost: %s:%d\r\nUpgrade: websocket\r\nConnection: Upgrade\r\n"
                        "Sec-WebSocket-Key: %s\r\nSec-WebSocket-Version: 13\r\n\r\n" % (path, host, port, key)).encode())
        head = b""
        while b"\r\n\r\n" not in head:
            p = self.s.recv(4096)
            if not p:
                raise ToolError("socket closed during the WebSocket handshake")
            head += p
        header, _, self.buf = head.partition(b"\r\n\r\n")
        self.buf = bytearray(self.buf)
        if b" 101 " not in header.split(b"\r\n")[0]:
            raise ToolError("WebSocket handshake refused: " + header.split(b"\r\n")[0].decode())
        want = base64.b64encode(hashlib.sha1((key + MAGIC).encode()).digest()).decode().lower()
        if want not in header.decode("latin1").lower():
            raise ToolError("Sec-WebSocket-Accept does not match")

    def _read(self, n):
        while len(self.buf) < n:
            p = self.s.recv(65536)
            if not p:
                raise ToolError("socket closed")
            self.buf += p
        r = bytes(self.buf[:n])
        del self.buf[:n]
        return r

    def send(self, text):
        d = text.encode()
        h = bytearray([0x81])
        if len(d) < 126:
            h.append(0x80 | len(d))
        elif len(d) < 65536:
            h += bytes([0x80 | 126]) + struct.pack(">H", len(d))
        else:
            h += bytes([0x80 | 127]) + struct.pack(">Q", len(d))
        m = os.urandom(4)
        self.s.sendall(bytes(h) + m + bytes(b ^ m[i % 4] for i, b in enumerate(d)))

    def receive(self):
        out = b""
        while True:
            b0, b1 = self._read(2)
            n = b1 & 0x7F
            if n == 126:
                n = struct.unpack(">H", self._read(2))[0]
            elif n == 127:
                n = struct.unpack(">Q", self._read(8))[0]
            body = self._read(n)
            if b0 & 0x0F == 0x9:
                self.s.sendall(b"\x8a\x80" + os.urandom(4))
            elif b0 & 0x0F == 0x8:
                raise ToolError("the browser closed the WebSocket")
            else:
                out += body
                if b0 & 0x80:
                    return out.decode("utf-8", "replace")


class Browser:
    """What both drivers share: own profile dir, own process group, kill/close that always end, an explanation of failures."""

    def _start(self, cmd, env, work, prefix):
        os.makedirs(work, exist_ok=True)
        self.profile = tempfile.mkdtemp(prefix=prefix, dir=work)
        self.p = spawn(cmd(self.profile), env, self.profile + "/out.log")

    def why(self, what, e):
        rc = self.p.poll()
        return "%s: %s (%s %s; log: %s)" % (what, e, self.name, "has EXITED with code %s" % rc if rc is not None else "is still running",
                                            tail(self.profile + "/out.log", 200))

    def kill(self):
        """kill -9 the whole browser (the check of an abrupt end)."""
        try:
            os.killpg(self.p.pid, signal.SIGKILL)
        except OSError:
            pass
        self.p.wait()

    def _quit(self, polite):
        for f in polite:
            try:
                f()
            except Exception:  # noqa: BLE001
                pass
        reap(self.p, 15)
        shutil.rmtree(self.profile, ignore_errors=True)


class Chrome(Browser):
    name = "Chrome"

    def __init__(self, env, work, size=(1400, 900)):
        exe = shutil.which("google-chrome") or shutil.which("chromium")
        if not exe:
            raise ToolError("neither google-chrome nor chromium is installed")
        self._start(lambda prof: [exe, "--remote-debugging-port=0", "--user-data-dir=" + prof, "--no-first-run",
                                  "--no-default-browser-check", "--disable-sync", "--password-store=basic", "--remote-allow-origins=*",
                                  "--ozone-platform=wayland", "--disable-gpu", "--window-size=%d,%d" % size, "about:blank"], env, work, "cr-")
        # port 0: Chrome picks a free port and writes it to <profile>/DevToolsActivePort; ours alone, never another run's
        port = int(wait_file(self.profile + "/DevToolsActivePort", self.p, 40, "Chrome"))
        end = time.time() + 40
        while True:
            try:
                tab = [t for t in json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json/list" % port, timeout=3).read()) if t.get("type") == "page"][0]
                break
            except Exception as e:  # noqa: BLE001 - not up yet
                if self.p.poll() is not None or time.time() > end:
                    raise ToolError(self.why("Chrome did not open a page", e))
                time.sleep(0.5)
        self.ws, self.n = Ws("127.0.0.1", port, "/devtools/page/" + tab["id"]), 0
        self.version = json.loads(urllib.request.urlopen("http://127.0.0.1:%d/json/version" % port, timeout=5).read()).get("Browser", "?")
        for d in ("Page.enable", "Runtime.enable"):
            self.call(d)
        self.call("Emulation.setFocusEmulationEnabled", enabled=True)

    def call(self, method, **params):
        self.n += 1
        try:
            self.ws.send(json.dumps({"id": self.n, "method": method, "params": params}))
            while True:
                r = json.loads(self.ws.receive())
                if r.get("id") == self.n:
                    break
        except (OSError, ToolError) as e:  # socket.timeout is an OSError
            raise ToolError(self.why(method, e))
        if "error" in r:
            raise ToolError("%s: %s" % (method, json.dumps(r["error"])))
        return r.get("result", {})

    def navigate(self, url):
        err = self.call("Page.navigate", url=url).get("errorText")
        if err and "CERT" not in err:
            raise NavError("%s: %s" % (url, err))
        time.sleep(1.5)
        for _ in range(3):  # the certificate warning: the user's "Advanced" then "Proceed", no flag that disables checks
            if not self.js("return !!document.getElementById('proceed-link') || !!document.getElementById('details-button');"):
                break
            self.js("const d=document.getElementById('details-button'); if(d) d.click();"
                    "const p=document.getElementById('proceed-link'); if(p) p.click(); return 1;")
            time.sleep(3)

    def js(self, body, *args):
        r = self.call("Runtime.evaluate", expression="(function(){%s}).apply(null,%s)" % (body, json.dumps(list(args))),
                      returnByValue=True, awaitPromise=True)
        if "exceptionDetails" in r:
            raise ToolError("page exception: " + json.dumps(r["exceptionDetails"])[:300])
        return r.get("result", {}).get("value")

    def screenshot(self, clip=None):
        p = {"format": "png"}
        if clip:
            p["clip"] = {"x": clip[0], "y": clip[1], "width": clip[2], "height": clip[3], "scale": 1}
        return base64.b64decode(self.call("Page.captureScreenshot", **p)["data"])

    def canvas_shot(self, rect):
        return self.screenshot(clip=rect)

    def move(self, x, y):
        self.call("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y)

    def click(self, x, y):
        self.move(x, y)
        for t in ("mousePressed", "mouseReleased"):
            self.call("Input.dispatchMouseEvent", type=t, x=x, y=y, button="left", clickCount=1)

    def key(self, key, code, vk, text=None, mod=0, **extra):
        d = dict(key=key, code=code, windowsVirtualKeyCode=vk, modifiers=mod)
        self.call("Input.dispatchKeyEvent", type="keyDown" if text else "rawKeyDown", **d, **({"text": text} if text else {}), **extra)
        time.sleep(0.08)
        self.call("Input.dispatchKeyEvent", type="keyUp", **d)

    def type_text(self, s):
        for ch in s:
            k, c, vk = key_info(ch)
            self.key(k, c, vk, text=ch)
            time.sleep(0.05)

    def press(self, name):
        self.key(*KEYS[name])

    def chord(self, key, ctrl=False, cmd=None):
        """One real key (a-z, Enter, Backspace, Delete), optionally with Ctrl. cmd: Chrome editing command (e.g. 'paste')."""
        named = {"Enter": ("Enter", "Enter", 13, "\r"), "Backspace": ("Backspace", "Backspace", 8, None), "Delete": ("Delete", "Delete", 46, None)}
        k, code, vk, text = named[key] if key in named else (key, "Key" + key.upper(), ord(key.upper()), None)
        if ctrl:
            self.call("Input.dispatchKeyEvent", type="rawKeyDown", key="Control", code="ControlLeft", windowsVirtualKeyCode=17, modifiers=2)
            time.sleep(0.06)
        self.key(k, code, vk, text=text, mod=2 if ctrl else 0, **({"commands": [cmd]} if cmd else {}))
        if ctrl:
            time.sleep(0.06)
            self.call("Input.dispatchKeyEvent", type="keyUp", key="Control", code="ControlLeft", windowsVirtualKeyCode=17, modifiers=0)
        time.sleep(0.2)

    def close(self):
        self._quit([lambda: self.call("Page.navigate", url="about:blank"), lambda: time.sleep(1),  # pagehide = FAREWELL
                    lambda: self.call("Browser.close")])


class Firefox(Browser):
    name = "Firefox"

    def __init__(self, env, work, size=(1400, 900), prefs=None):
        exe = shutil.which("firefox-esr") or shutil.which("firefox")
        if not exe:
            raise ToolError("firefox is not installed")
        p = {"browser.startup.homepage_override.mstone": "ignore", "datareporting.policy.firstRunURL": "",
             "browser.aboutwelcome.enabled": False, "browser.shell.checkDefaultBrowser": False, "marionette.port": 0,
             "startup.homepage_welcome_url": "", "browser.startup.page": 0}
        p.update(prefs or {})

        def cmd(prof):
            with open(prof + "/user.js", "w") as f:
                for k, v in p.items():
                    f.write('user_pref("%s", %s);\n' % (k, json.dumps(v)))
            return [exe, "--marionette", "--no-remote", "--profile", prof, "--width", str(size[0]), "--height", str(size[1])]
        self._start(cmd, dict(env, MOZ_ENABLE_WAYLAND="1"), work, "ff-")
        # port 0: Firefox picks a free port and writes it to <profile>/MarionetteActivePort
        port = int(wait_file(self.profile + "/MarionetteActivePort", self.p, 60, "Firefox"))
        end = time.time() + 60
        while True:
            try:
                self.s = socket.create_connection(("127.0.0.1", port), timeout=10)
                break
            except OSError as e:
                if self.p.poll() is not None or time.time() > end:
                    raise ToolError(self.why("Marionette port %d" % port, e))
                time.sleep(0.5)
        self.buf, self.n = b"", 0
        self._read()  # greeting
        caps = self.call("WebDriver:NewSession", {"capabilities": {"alwaysMatch": {"acceptInsecureCerts": True}}, "acceptInsecureCerts": True})
        self.version = "Firefox " + caps.get("capabilities", {}).get("browserVersion", "?")
        self.call("WebDriver:SetTimeouts", {"script": 30000, "pageLoad": 30000})

    def _read(self, cap=45):  # frames are "length:json"; a closed socket or a silent one ends in a ToolError
        end = time.time() + cap
        while True:
            if b":" in self.buf:
                head, rest = self.buf.split(b":", 1)
                if len(rest) >= int(head):
                    self.buf = rest[int(head):]
                    return json.loads(rest[:int(head)])
            self.s.settimeout(max(1.0, end - time.time()))
            try:
                d = self.s.recv(65536)
            except OSError as e:
                raise ToolError(self.why("no answer from Marionette in %d s" % cap, e))
            if not d:
                raise ToolError(self.why("Marionette closed the connection", "end of stream"))
            self.buf += d

    def call(self, cmd, params=None):
        self.n += 1
        body = json.dumps([0, self.n, cmd, params or {}]).encode()
        try:
            self.s.sendall(str(len(body)).encode() + b":" + body)
        except OSError as e:
            raise ToolError(self.why(cmd, e))
        while True:
            m = self._read()
            if isinstance(m, list) and len(m) == 4 and m[0] == 1 and m[1] == self.n:
                if m[2] is not None:
                    raise ToolError("%s: %s" % (cmd, json.dumps(m[2])[:400]))
                return m[3]

    def navigate(self, url):
        try:
            self.call("WebDriver:Navigate", {"url": url})
        except ToolError as e:
            if any(x in str(e) for x in NET_ERRORS):
                raise NavError("%s: %s" % (url, str(e)[:200]))
            raise
        time.sleep(1)

    def js(self, body, *args):
        return self.call("WebDriver:ExecuteScript", {"script": body, "args": list(args)})["value"]

    def screenshot(self, clip=None):  # clip is not used: the whole viewport (the canvas has canvas_shot)
        return base64.b64decode(self.call("WebDriver:TakeScreenshot", {"full": False})["value"])

    def canvas_shot(self, rect):
        el = self.call("WebDriver:FindElement", {"using": "css selector", "value": "#viewer"})["value"]
        return base64.b64decode(self.call("WebDriver:TakeScreenshot", {"id": list(el.values())[0], "full": False})["value"])

    def _actions(self, a):
        self.call("WebDriver:PerformActions", {"actions": a})
        self.call("WebDriver:ReleaseActions")

    def _ptr(self, *steps):
        self._actions([{"type": "pointer", "id": "mouse", "parameters": {"pointerType": "mouse"}, "actions": list(steps)}])

    def move(self, x, y):
        self._ptr({"type": "pointerMove", "x": int(x), "y": int(y), "origin": "viewport", "duration": 0})

    def click(self, x, y):
        self._ptr({"type": "pointerMove", "x": int(x), "y": int(y), "origin": "viewport", "duration": 0},
                  {"type": "pointerDown", "button": 0}, {"type": "pause", "duration": 60}, {"type": "pointerUp", "button": 0})

    def type_text(self, s):
        for ch in s:
            self._actions([{"type": "key", "id": "kbd", "actions": [{"type": "keyDown", "value": ch}, {"type": "pause", "duration": 50},
                                                                     {"type": "keyUp", "value": ch}]}])
            time.sleep(0.05)

    def press(self, name):
        w = {"Escape": ""}[name]
        self._actions([{"type": "key", "id": "kbd", "actions": [{"type": "keyDown", "value": w}, {"type": "keyUp", "value": w}]}])

    def chord(self, key, ctrl=False, cmd=None):  # same face as Chrome.chord (cmd is Chrome's editing command: unused here)
        val = {"Enter": "", "Backspace": "", "Delete": ""}.get(key, key)
        C = ""  # WebDriver's Control
        acts = ([{"type": "keyDown", "value": C}, {"type": "pause", "duration": 60}] if ctrl else [])
        acts += [{"type": "keyDown", "value": val}, {"type": "pause", "duration": 80}, {"type": "keyUp", "value": val}]
        acts += ([{"type": "pause", "duration": 60}, {"type": "keyUp", "value": C}] if ctrl else [])
        self._actions([{"type": "key", "id": "kbd", "actions": acts}])
        time.sleep(0.2)

    def close(self):
        self._quit([lambda: self.call("WebDriver:Navigate", {"url": "about:blank"}), lambda: time.sleep(1),
                    lambda: self.call("Marionette:Quit")])


# ------------------------------------------------------------------------------------------------------------- rig
_rigs = []
atexit.register(lambda: [r.stop() for r in list(_rigs)])


class Rig:
    """Compositor + browser + the user of a box. One Rig per browser that must live in its own compositor."""

    def __init__(self, box, browser, user, password, tag, host="127.0.0.1", cap=60, sound=False, prefs=None):
        self.box, self.browser, self.user, self.password, self.tag = Box(box), browser, user, password, tag
        self.boxname, self.host, self.cap, self.sound, self.prefs = box, host, cap, sound, prefs or {}
        self.url = "https://%s:%d/" % (host, PORTS[box])
        self.comp, self.g, self.env, self.log = Compositor(tag), None, None, None
        _rigs.append(self)

    def start(self, size=(1400, 900), make_user=True):
        """Make the user, start the compositor (once) and a browser. Returns the browser's version."""
        if make_user:
            self.box.ensure_user(self.user, self.password)
        if self.env is None:
            self.env = self.comp.start()
        return self.new_browser(size)

    def new_browser(self, size=(1400, 900)):
        if self.g:
            self.g.close()
            self.g = None
        env = dict(self.env)
        if self.browser == "firefox":
            try:  # a PulseAudio-compatible server on the host: Firefox starts no AudioContext without one
                socket.socket(socket.AF_UNIX).connect(SOUND)
                env["PULSE_SERVER"] = "unix:" + SOUND
            except OSError:
                if self.sound:
                    raise ToolError("no sound server on the dev host (%s): run server/prepara-server.sh" % SOUND)
        self.g = (Chrome(env, WORK, size) if self.browser == "chrome" else Firefox(env, WORK, size, self.prefs))
        return self.g.version

    def stop(self):
        if self in _rigs:
            _rigs.remove(self)
        try:
            if self.g:
                self.g.close()
        finally:
            self.g = None
            try:
                self.box.run("pkill -u %s -f 'rx-window-%s.py|rx-tone'; true" % (self.user, self.user), timeout=20)
            except Exception:  # noqa: BLE001
                pass
            self.comp.stop()

    # --- the page
    def open_page(self, cap=30):
        """Open the page. The product not answering is a FAIL with the evidence; returns the form facts."""
        try:
            socket.create_connection((self.host, PORTS[self.boxname]), timeout=5).close()
        except OSError as e:
            raise NavError("%s: the page port does not answer (%s): the product is not listening" % (self.url, e))
        self.g.navigate(self.url)
        end, f = time.time() + cap, {}
        while time.time() < end:
            f = self.g.js(JS_FORM)
            if f.get("form") and f.get("ready") == "complete" and f.get("user") and f.get("pw") and f.get("btn") and f.get("remotix"):
                return f
            time.sleep(0.5)
        raise Fail("%s in %s: form not usable after %d s: %s" % (self.url, self.g.version, cap, f))

    def state(self):
        return self.g.js(JS_STATE)

    def wait_state(self, cond, cap=None):
        end, s = time.time() + (cap or self.cap), {}
        while time.time() < end:
            s = self.state()
            if cond(s):
                return s, True
            time.sleep(0.4)
        return s, False

    def center(self, elem_id):
        return self.g.js("const e=document.getElementById(arguments[0]); const b=e.getBoundingClientRect();"
                         "return [b.left+b.width/2, b.top+b.height/2];", elem_id)

    def try_login(self, real=False, retry=0):
        """Sign in as the rig's user: (admitted, state). `real`: click the fields, type, Enter, as a person does (names and
        passwords of a-z 0-9 only); else one synthetic submit. With `retry` seconds a refusal is tried again every 5 s (the
        previous client of the same user may still hold the slot) - NEVER after a wrong password: that counts for the ban."""
        g, t0, self.tries = self.g, time.time(), 0
        while True:
            self.tries += 1
            if real:
                g.js("document.getElementById('username').value=''; document.getElementById('password').value=''; return 1;")
                g.click(*self.center("username"))
                g.type_text(self.user)
                g.click(*self.center("password"))
                g.type_text(self.password)
                g.chord("Enter")
            else:
                g.js(JS_ENTER, self.user, self.password)
            s, ok = self.wait_state(lambda s: (s["session"] and s["cls"] == "good") or s["cls"] == "bad")
            if ok and s["session"] and s["cls"] == "good":
                return True, s
            if re.search(r"incorrect|wrong|password|banned|too many|blocked", s.get("outcome") or "", re.I) or time.time() - t0 > retry:
                return False, s
            time.sleep(5)

    def login(self, real=False, retry=0):
        ok, s = self.try_login(real, retry)
        if not ok:
            raise Fail("user %s not admitted in %d s: outcome \"%s\" (%s); page log tail: %s; remotix journal: %s" % (
                self.user, self.cap, (s.get("outcome") or "").strip(), s.get("cls"),
                " | ".join((s.get("log") or "").strip().splitlines()[-3:])[:250], self.box.journal(self.user)))
        return s

    # --- the desktop
    def leave_overview(self):
        """GNOME is born in the Activities Overview, which covers the desktop: ask the Shell, press a real ESC, verify."""
        q = ("u=$(id -u %s); runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$u DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus "
             "gdbus call --session --dest org.gnome.Shell --object-path /org/gnome/Shell --method org.freedesktop.DBus.Properties.Get "
             "org.gnome.Shell OverviewActive 2>&1" % (self.user, self.user))
        for _ in range(3):
            t = self.box.run(q)[1]
            if "<false>" in t:
                return "Overview off"
            self.g.js("const t=document.getElementById('viewer'); if(t&&t.focus) t.focus(); return 1;")
            self.g.press("Escape")
            time.sleep(2)
        return "Overview still on or unreadable: " + t[-80:]

    def shell_up(self, cap=None):
        """Wait for the desktop shell of the user (KDE: plasmashell running and the splash gone): (seconds waited, up)."""
        cap, t0, up = cap or self.cap, time.time(), False
        while time.time() - t0 < cap and not up:
            up = self.box.run(SHELL_UP[self.boxname] % {"u": self.user})[0] == 0
            if not up:
                time.sleep(1.5)
        return time.time() - t0, up

    def canvas_png(self, rect=None):
        return self.g.canvas_shot(rect or self.state()["rect"])

    def settle(self, cap=None, still=3, shell=True):
        """Frames painted, the shell up (+ GNOME overview left) and the picture not uniform AND still for `still` pairs of shots
        1.5 s apart (a splash animates). Raises Fail with the evidence; returns the facts."""
        cap, g = cap or self.cap, self.g
        s, ok = self.wait_state(lambda s: s["painted"] > 0, cap)
        if not ok:
            why = self.box.x_shortage(self.user)
            if why:  # the environment, not the product: the session could not get an X display
                raise ToolError("no decoded frame in %d s because the session could not get an X display (shared numbers used up): %s" % (cap, why))
            raise Fail("no decoded frame painted in %d s (delivered=%s painted=%s)" % (cap, s["delivered"], s["painted"]))
        shell_s, up, extra = 0, not shell, ""
        if shell:
            shell_s, up = self.shell_up(cap)
            extra = self.leave_overview() + "; " if (up and self.boxname == "gnome") else ""
        end, desc, n, prev, deg, t0, png = time.time() + cap, "", 0, None, True, time.time(), None
        while time.time() < end and up and n < still:
            time.sleep(1.5)
            s = self.state()
            if not s["rect"] or s["rect"][2] < 4:
                continue
            png = self.canvas_png(s["rect"])
            deg, desc = judge_pixel(png)
            n = n + 1 if (not deg and prev and settled(prev, png)) else 0
            prev = png
        if png is None and up:
            raise Fail("the canvas has no size after login (no picture to judge)")
        if not up:
            raise Fail("frames painted=%d but the desktop shell (%s) is not up %d s after login" % (s["painted"], SHELL_UP[self.boxname] % {"u": self.user}, cap))
        if n < still:
            raise Fail("frames painted=%d but the picture never became a settled non-uniform desktop in %d s (last: %s)" % (s["painted"], cap, desc))
        return dict(s=s, png=png, desc=desc, shell_s=shell_s, settle_s=time.time() - t0, extra=extra)

    # --- the test window in the user's session (window.py) and what it saw
    def start_window(self, colour=None):
        """The fullscreen entry window of window.py in the user's session, logging events to a file in the box."""
        src = "/tmp/rx-window-%s.py" % self.user
        self.log = "/tmp/rx-%s-%s.log" % (self.user, self.tag)
        self.box.run("pkill -u %s -f %s; cat > %s; chmod 644 %s; rm -f %s; true" % (self.user, os.path.basename(src), src, src, self.log),
                     stdin=open(os.path.join(HERE, "window.py")).read())
        self.box.in_session(self.user, "python3 %s %s %s 2>%s.err" % (src, self.log, colour or "", self.log))
        end = time.time() + 40
        while time.time() < end:
            if any(e["ev"] == "ready" for e in self.events()):
                time.sleep(1.5)  # let the desktop show the window to the client
                return
            time.sleep(1)
        raise ToolError("the test window of %s never reported ready: %s" % (self.user, self.box.run("tail -c 200 %s.err" % self.log)[1].replace("\n", " ")))

    def events(self):
        t = self.box.run("cat %s 2>/dev/null; true" % self.log)[1]
        return [json.loads(x) for x in t.splitlines() if x.startswith("{")]

    def win_pid(self):
        t = self.box.run("pgrep -u %s -f 'python3 /tmp/rx-window-%s.py' | head -1; true" % (self.user, self.user))[1].strip()
        return t if t.isdigit() else None

    def px(self, fx, fy):
        L, T, W, H = self.state()["rect"]
        return L + W * fx, T + H * fy

    def canvas_click(self, fx, fy):
        self.g.click(*self.px(fx, fy))


def save_png(name, png):
    os.makedirs(SHOTS, exist_ok=True)
    path = os.path.join(SHOTS, name)
    open(path, "wb").write(png)
    return path
