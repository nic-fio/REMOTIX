#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g7-comune — the tools of group G7 (the network dropping and the clocks).

  · its OWN SERVER (`15-g7-server.sh`): port 8611-8614, unit `rete15-g7`,
    log /var/lib/rete15-g7/registro.log inside the box;
  · the DEAD LINE simulated ON THE SERVER with nftables: a table of ours,
    `inet remotix_g7_<port>`, that drops the UDP packets of ONLY our server's
    port (⛔ the other agents use 851x) — and it is ALWAYS removed;
  · the STATE OF THE PAGE that matters for these tests: what it says (outcome),
    whether it is still dressed as a desktop, whether the form is visible;
  · the browser's processes, to stop it (SIGSTOP) and restart it;
  · the tenant's processes in the box (is the session still there?).

⛔ It is imported from `15-f019-…` and `15-f022-…` (not copied).  It runs ON THE SERVER
   as nicfio: sudo with the password, local.
"""
import os
import re
import signal
import subprocess
import time


def _sudo_password():
    """The server's sudo password: from REMOTIX_SUDO_PASSWORD, or from the «pass:» line of
    ~/SERVER.ssh (the same file as fondamenta/strumenti/sshpw.py). ⛔ Never written
    in the benches: they are in the repository."""
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

HERE = os.path.dirname(os.path.abspath(__file__))
SERVER_SH = os.path.join(HERE, "15-g7-server.sh")
PORTS_G7 = {"gnome": 8611, "kde": 8612, "xfce": 8613, "lxqt": 8614}
DIR_G7 = "/var/lib/rete15-g7"
G7_LOG = DIR_G7 + "/registro.log"


def sudo(argv, seconds=60, entry=""):
    """(code, output) of `argv` with sudo, on the server (local)."""
    try:
        r = subprocess.run(["sudo", "-S", "-p", ""] + list(argv),
                           input=_sudo_password() + entry, capture_output=True,
                           text=True, errors="replace", timeout=seconds)
    except subprocess.TimeoutExpired:
        return None, "(no answer in %d s)" % seconds
    return r.returncode, (r.stdout + r.stderr).strip()


def inside(desktop, line, seconds=60):
    """(code, output) of `line` as root in the box rete11-<desktop>."""
    return sudo(["podman", "exec", "rete11-%s" % desktop, "sh", "-c", line], seconds)


# ═══════════════════════════════════════════════════════════════════════════
#  OUR SERVER
# ═══════════════════════════════════════════════════════════════════════════
def server(action, desktop, *options, seconds=90):
    try:
        r = subprocess.run(["bash", SERVER_SH, action, desktop] + list(options),
                           capture_output=True, text=True, errors="replace",
                           timeout=seconds)
    except subprocess.TimeoutExpired:
        return False, "(15-g7-server.sh %s: no answer in %d s)" % (action, seconds)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def clocks_in_effect(desktop):
    """The startup line with the three clocks of §5.3: (inattivita_s, abbandono_s, line)."""
    _c, t = inside(desktop, "grep -a '§5.3, the three clocks' %s | tail -n 1" % G7_LOG)
    m1 = re.search(r"user inactivity (\d+) s", t or "")
    m2 = re.search(r"session abandonment (\d+) s", t or "")
    return (int(m1.group(1)) if m1 else None, int(m2.group(1)) if m2 else None,
            (t or "").strip())


class Log:
    """OUR server's log, with the same form as Scatola."""

    def __init__(self, desktop, fpath=G7_LOG):
        self.d, self.p = desktop, fpath

    def lines(self):
        _c, t = inside(self.d, "wc -l < %s" % self.p, 30)
        try:
            return int(t.split()[-1])
        except (ValueError, IndexError, AttributeError):
            return None

    def da(self, sign, chi=None):
        pattern = (" | grep -a -- '%s'" % chi) if chi else ""
        _c, t = inside(self.d, "tail -n +%d %s%s" % ((sign or 0) + 1, self.p, pattern), 60)
        return (t or "").splitlines()

    def wait_until(self, sign, shapes, chi=None, cap=60, step=1.0):
        """(form, line, seconds) of the first line with one of the `shapes`."""
        t0 = time.time()
        while time.time() - t0 < cap:
            for r in self.da(sign, chi):
                for f in shapes:
                    if f in r:
                        return f, r, time.time() - t0
            time.sleep(step)
        return None, None, time.time() - t0


# ═══════════════════════════════════════════════════════════════════════════
#  THE DEAD LINE — nftables on the server, ONLY our port
# ═══════════════════════════════════════════════════════════════════════════
class DeadLine:
    """
        with DeadLine(8611) as lm:   # from here no UDP from/to 8611
            ...
        # here the rule is no longer there (even if the body fell over)

    ⛔ A table of OURS (`inet remotix_g7_<port>`): it is removed with a
       `delete table` and does not touch anybody else's rules.  It drops the UDP
       (QUIC/WebTransport) incoming AND outgoing, in both directions of the port:
       the browser and the server are on the same machine (it goes through `lo`), and the
       packet crosses `output` and then `input`.
    ⚠ The TCP (the HTTPS page) stays: the line that drops is the
      session's.  Declared: it is the server's network, not the real path from the
      tablet."""

    def __init__(self, port):
        self.port = int(port)
        assert 8600 <= self.port <= 8699, "only our server's ports"
        self.table = "remotix_g7_%d" % self.port
        self.placed = None

    def rules(self):
        p = self.port
        return ("table inet %(t)s {\n"
                " chain dentro { type filter hook input priority -10; policy accept;\n"
                "  udp dport %(p)d counter drop\n  udp sport %(p)d counter drop\n }\n"
                " chain fuori { type filter hook output priority -10; policy accept;\n"
                "  udp dport %(p)d counter drop\n  udp sport %(p)d counter drop\n }\n"
                "}\n" % {"t": self.table, "p": p})

    def remove(self):
        sudo(["/usr/sbin/nft", "delete", "table", "inet", self.table], 30)
        c, t = sudo(["/usr/sbin/nft", "list", "tables"], 30)
        return self.table not in (t or "")

    def put(self):
        self.remove()                              # a leftover from a round that fell over
        # ⚠ From a FILE, not from stdin: with sudo already authenticated the password is not
        #   consumed and would end up inside the rules (`[M]` «syntax error … nicfio»).
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".nft", delete=False) as f:
            f.write(self.rules())
        try:
            c, t = sudo(["/usr/sbin/nft", "-f", f.name], 30)
        finally:
            os.unlink(f.name)
        if c != 0:
            raise RuntimeError("nft did not put the rule: %s" % t[-200:])
        self.placed = time.time()
        return True

    def counted(self):
        """The dropped packets (witness that the rule BITES)."""
        _c, t = sudo(["/usr/sbin/nft", "list", "table", "inet", self.table], 30)
        return sum(int(x) for x in re.findall(r"packets (\d+)", t or ""))

    def __enter__(self):
        self.put()
        return self

    def __exit__(self, *a):
        removed = self.remove()
        if not removed:
            print("   ⛔ THE nft RULE %s CANNOT BE REMOVED" % self.table, flush=True)
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  THE PAGE
# ═══════════════════════════════════════════════════════════════════════════
JS_PAGE = r"""
const e = document.getElementById('outcome');
const m = document.getElementById('signin-form');
const reg = document.getElementById('logbook');
const vis = (x) => !!x && getComputedStyle(x).display !== 'none'
                  && getComputedStyle(x).visibility !== 'hidden'
                  && x.getBoundingClientRect().width > 0;
const R = window.REMOTIX, s = R && R.viewer;
const righe = reg ? reg.textContent.split('\n') : [];
return {
  outcome: e ? e.textContent : null,
  outcome_class: e ? e.className : null,
  esito_visibile: vis(e) && !!(e && e.textContent.trim()),
  modulo_visibile: vis(m),
  vestita: document.body ? (document.body.dataset.viewer || null) : null,
  session: !!(s && s.session),
  input: !!window.REMOTIX_INPUT,
  painted: s && s.counts ? s.counts.painted : null,
  coda: righe.filter(r => r.indexOf('audio:') !== 0).slice(-14),
  n_righe: righe.length,
  testo: document.body ? document.body.innerText.slice(0, 400) : ''
};
"""


def page(g):
    try:
        return g.js(JS_PAGE) or {}
    except Exception as e:                       # noqa: BLE001
        return {"error": str(e)[:200]}


def page_says(st):
    """⭐ The page TELLS the user that the wire dropped: a visible sentence
    in the outcome line, or the sign-in form back in view (and the
    desktop dress removed).  ⛔ The hidden log (`#logbook`, off
    by default) is not «telling»: the user does not see it."""
    if not isinstance(st, dict) or st.get("error"):
        return None
    if st.get("esito_visibile") and st.get("outcome_class") == "bad":
        return True
    if st.get("modulo_visibile") and not st.get("vestita"):
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
#  THE BROWSER: stopping it and restarting it (the whole process tree)
# ═══════════════════════════════════════════════════════════════════════════
def descendants(pid):
    children = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open("/proc/%s/stat" % d) as f:
                st = f.read()
            pp = int(st.rsplit(")", 1)[1].split()[1])
        except Exception:                        # noqa: BLE001
            continue
        children.setdefault(pp, []).append(int(d))
    all_items, queue = [], [pid]
    while queue:
        p = queue.pop()
        all_items.append(p)
        queue.extend(children.get(p, []))
    return all_items


def pid_browser(g):
    p = getattr(g, "p", None)
    return getattr(p, "pid", None)


def signal_tree(g, sig):
    pid = pid_browser(g)
    if not pid:
        return []
    done_ones = []
    for p in descendants(pid):
        try:
            os.kill(p, sig)
            done_ones.append(p)
        except ProcessLookupError:
            pass
    return done_ones


def stop_browser(g):
    return signal_tree(g, signal.SIGSTOP)


def resume_browser(g):
    return signal_tree(g, signal.SIGCONT)


# ═══════════════════════════════════════════════════════════════════════════
#  THE TENANT IN THE BOX
# ═══════════════════════════════════════════════════════════════════════════
def tenant_processes(desktop, chi):
    """{pid: command} of the tenant's processes (empty = the session is not there)."""
    _c, t = inside(desktop, "ps -u %s -o pid=,comm= 2>/dev/null" % chi, 30)
    ps = {}
    for r in (t or "").splitlines():
        a = r.split(None, 1)
        if len(a) == 2 and a[0].isdigit():
            ps[int(a[0])] = a[1].strip()
    return ps


def in_session(s, command, seconds=60):
    """Like `Session.in_session(fondo=True)`, but from here (local sudo on the
    server) instead of over ssh: `[M]` 24 Sep, with ten agents together the bench's
    ssh to the server itself drops («Connection closed … port 22»)."""
    chi = s.chi
    env = ("u=$(id -u %(c)s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
           "| head -1); [ -n \"$d\" ] || { echo 'no wayland socket'; exit 2; }; "
           % {"c": chi})
    body = ("runuser -u %(c)s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
             "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
             "XDG_SESSION_TYPE=wayland HOME=/home/%(c)s sh -c %(q)s"
             % {"c": chi, "q": S_q(command)})
    body = "setsid %s < /dev/null > /home/%s/.g7-%s.log 2>&1 & echo launched" % (
        body, chi, re.sub(r"\W", "", command.split()[0])[:20])
    return inside(s.o.box, env + body, seconds)


def S_q(x):
    return "'" + x.replace("'", "'\"'\"'") + "'"


def launch_scene(s, S=None, what="scene"):
    """The MOVING SCENE inside the session: `weston-simple-egl -f` — the
    spinning triangle, full screen, drawn by the card (EGL) and native
    Wayland: it is in all four boxes.
    ⛔ Not C3's scene in firefox-esr: `[M]` 24 Sep 2026 on GNOME, firefox-esr
       launched this way does not write a byte in the profile and opens «Your Firefox profile
       cannot be loaded» (even with the profile prepared like C21, even headless
       with a test user) ⇒ the scene never appeared.
    Returns (pid | None, text)."""
    c, t = in_session(s, "weston-simple-egl -f", 60)
    for _ in range(40):
        ps = tenant_processes(s.o.box, s.chi)
        f = [p for p, n in ps.items() if n.startswith("weston-simple")]
        if f:
            return min(f), "weston-simple-egl of the %s: pid %d" % (what, min(f))
        time.sleep(0.5)
    return None, "weston-simple-egl was not seen starting: %s" % (t or "")[-200:]


def launch_tone(s, seconds=600):
    """pw-play of a 440 Hz wave on the product's «remotix» sink, in a loop."""
    body = ("python3 -c \"import math,struct,wave;w=wave.open('/tmp/g7-onda-%(c)s.wav','wb');"
             "w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);"
             "w.writeframes(b''.join(struct.pack('<hh',int(16000*math.sin(2*math.pi*440*i/48000)),"
             "int(16000*math.sin(2*math.pi*440*i/48000))) for i in range(48000*5)));w.close()\" "
             "&& end=$(( $(date +%%s) + %(s)d )); while [ $(date +%%s) -lt $end ]; do "
             "pw-play --target=remotix /tmp/g7-onda-%(c)s.wav; done"
             % {"c": s.chi, "s": seconds})
    return in_session(s, body, 60)


# ⭐ THE EAR: the page's `AudioBufferSourceNode.start` is wrapped, and for
#   every buffer the page really sends to the output the RMS of the
#   SAMPLES is measured (blocks are not counted: a stream of zeros is blocks that
#   arrive and it is silence).  It is put after loading, before the login:
#   the page creates the sources only with the session open.
JS_EAR = r"""
if (window.__G7_ORECCHIO__) return 'gia';
const O = window.__G7_ORECCHIO__ = { finestre: [] };
const vero = AudioBufferSourceNode.prototype.start;
AudioBufferSourceNode.prototype.start = function () {
  try {
    const b = this.buffer;
    if (b && b.numberOfChannels > 0) {
      const d = b.getChannelData(0);
      let q = 0;
      for (let i = 0; i < d.length; i++) q += d[i] * d[i];
      const t = Math.floor(performance.now() / 1000);
      let f = O.finestre[O.finestre.length - 1];
      if (!f || f.t !== t) { f = { t: t, n: 0, q: 0, c: 0 }; O.finestre.push(f);
                             if (O.finestre.length > 900) O.finestre.shift(); }
      f.q += q; f.c += d.length; f.n += 1;
    }
  } catch (e) {}
  return vero.apply(this, arguments);
};
return 'messo';
"""

JS_LISTEN = r"""
const O = window.__G7_ORECCHIO__;
if (!O) return null;
const da = arguments[0], a = arguments[1];
let q = 0, c = 0, n = 0;
for (const f of O.finestre) if (f.t >= da && f.t < a) { q += f.q; c += f.c; n += f.n; }
return { rms: c ? Math.sqrt(q / c) : null, campioni: c, buffer: n,
         adesso: Math.floor(performance.now() / 1000) };
"""

RMS_THRESHOLD = 0.01      # the wave is 16000/32767 ≈ 0.49 peak ⇒ RMS ≈ 0.35


def ear(g):
    try:
        return g.js(JS_EAR)
    except Exception as e:                       # noqa: BLE001
        return "not put: %s" % str(e)[:120]


def listen(g, seconds):
    """(rms | None, details) over the last `seconds` of sound PLAYED by the page."""
    try:
        now = g.js("return Math.floor(performance.now() / 1000);")
        r = g.js(JS_LISTEN, now - seconds, now + 1)
    except Exception as e:                       # noqa: BLE001
        return None, "ear unreadable: %s" % str(e)[:120]
    if not r:
        return None, "the ear is not on the page"
    return r.get("rms"), r


# ═══════════════════════════════════════════════════════════════════════════
#  THE PHOTOS: does the scene move?
# ═══════════════════════════════════════════════════════════════════════════
def diversity(png_a, png_b):
    """Fraction of pixels that change (|Δ| > 40 on a channel) between two photos,
    at reduced scale.  None if they cannot be compared."""
    try:
        import io
        from PIL import Image, ImageChops
        a = Image.open(io.BytesIO(png_a)).convert("RGB").resize((320, 180))
        b = Image.open(io.BytesIO(png_b)).convert("RGB").resize((320, 180))
        d = ImageChops.difference(a, b).getdata()
        changed = sum(1 for p in d if max(p) > 40)
        return changed / float(len(d))
    except Exception:                            # noqa: BLE001
        return None


def scene_colors(png):
    """Share of blue (#0000FF) and yellow (#FFFF00) pixels of C3's scene."""
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(png)).convert("RGB").resize((320, 180))
        px = list(im.getdata())
        blue = sum(1 for r, g_, b in px if b > 180 and r < 80 and g_ < 80)
        already = sum(1 for r, g_, b in px if r > 180 and g_ > 180 and b < 80)
        return blue / float(len(px)), already / float(len(px))
    except Exception:                            # noqa: BLE001
        return None, None


def wait_scene(s, S, cap=40):
    """(True | None, description): the moving scene in view within
    `cap` — two photos 0.7 s apart differing by > 2 % of the pixels."""
    t0 = time.time()
    desc = ""
    before = None
    while time.time() - t0 < cap:
        try:
            png = S.C21.full_photo(s.g)
        except Exception as e:                   # noqa: BLE001
            png, desc = None, str(e)[:120]
        if png and before:
            d = diversity(before, png)
            desc = "change %.1f%%" % (100 * (d or 0))
            if d and d > 0.02:
                return True, "moving scene after %.0f s (%s)" % (time.time() - t0, desc)
        before = png
        time.sleep(0.7)
    return None, "the moving scene did not appear in %d s (%s)" % (cap, desc)


def scene_moves(s, name, pairs=3, delay=None):
    """(True/False/None, description, [paths]) — photos at IRREGULAR pauses,
    and ALL the pairs are compared: at least one different by > 2 % of the pixels.

    ⛔ `[M]` 25 Sep 2026 (D-019, class C): with a fixed pause of 0.7 s plus the
    time of the 4K photo (~0.9 s in all) the photos almost always fell at the
    same point of the turn of weston-simple-egl's triangle (half a turn
    ~0.9 s) ⇒ 0.9-1.6 % change with the scene ALIVE, and a false FAIL."""
    pause = [0.43, 0.61, 0.77, 0.29, 0.53]
    photo, ev = [], []
    for i in range(pairs + 1):
        png, dove = s.photo("%s-%d" % (name, i))
        if not png:
            return None, "photo failed: %s" % dove, ev
        photo.append(png)
        if dove:
            ev.append(dove)
        time.sleep(delay if delay is not None else pause[i % len(pause)])
    diffs = [diversity(photo[i], photo[j]) for i in range(len(photo))
             for j in range(i + 1, len(photo))]
    if any(d is None for d in diffs):
        return None, "photos not comparable", ev
    desc = "changes between photos %s" % ["%.1f%%" % (100 * d) for d in diffs]
    return max(diffs) > 0.02, desc, ev


# ═══════════════════════════════════════════════════════════════════════════
#  ⛔ THE BOX WITHOUT SSH, when running ON THE SERVER
# ═══════════════════════════════════════════════════════════════════════════
def local_box(S):
    """`[M]` 24 Sep 2026, ten agents together: `Box.dentro()` goes through
    `sshpw.py` → ssh to the server ITSELF, and sshd cuts off some of them
    («Connection closed by 192.168.0.2 port 22») ⇒ tenants not created,
    BLOCKED that are not the product's.  On the server (REMOTIX_ON_SERVER=1) the
    same line is executed with local `sudo podman exec`.  ⚠ The class loaded by
    suite.py is changed in THIS process, not suite.py."""
    if os.environ.get("REMOTIX_ON_SERVER") != "1":
        return False

    def _inside(self, line, seconds=90):
        c, t = sudo(["podman", "exec", self.container, "sh", "-c", line], seconds)
        return c, (t or "").strip()
    S.C20V.Box.inside = _inside
    return True
