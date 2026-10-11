#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-kasmvnc — THE LEAN COMPARISON REMOTIX vs KasmVNC (fasi/20-le-prestazioni.md §9, 11 Oct 2026)

    (on the server, as nicfio; sudo only for the REMOTIX twin, like 16-salita.py)
    python3 16-kasmvnc.py costruisci                 the image kasm-kde (Contenitore.kasmvnc)
    python3 16-kasmvnc.py accendi --misura fhd       the box kasm-kde, KasmVNC on 127.0.0.1:8701
    python3 16-kasmvnc.py gemello-accendi            the box kasm-remotix-kde, REMOTIX on :8702
    python3 16-kasmvnc.py spegni | gemello-spegni | stato
    python3 16-kasmvnc.py misura --sistema kasmvnc|remotix --misura fhd --browser chrome \
                                 --scena video|tasti --secondi 30 --dir D
    python3 16-kasmvnc.py campagna --dir D [--sistemi kasmvnc,remotix] [--misure fhd,2k,3k]
                                   [--browser chrome,firefox] [--scene video,tasti] [--secondi 90]
    python3 16-kasmvnc.py certifica                  the pure functions, no box, no browser

⭐ WHAT IT IS.  Not the climb of §7 (~2 days of work): ONE user, two scenes, the SAME for both systems,
   row by row at the same moment (for each size, browser and scene: KasmVNC, then REMOTIX):
     video   the 4K film at 30 fps (bbb_sunflower_2160p_30fps_normal, the file of profile D) in mpv
             full screen, decoded on the Intel (VA-API) in both sessions
     tasti   `konsole -e cat`, one key every 0.3-0.5 s (the same seeded sequence for both) typed IN THE
             BROWSER: it goes through the system's channel, like the user's
   KasmVNC  1.5.0, official package, KDE Plasma 6.3 on X11, rootless box `kasm-kde` (Contenitore.kasmvnc)
   REMOTIX  the product of phase 20 (rete11/prodotto, 716e35b) on KDE Wayland, a box of its own
            `kasm-remotix-kde` made by 11-accendi.sh (REMOTIX_11_NOME/PORTA) from a COPY of the rete11
            tree: rete11-* and 8511-8514 are never touched; a NEW session per measure (a resumed one
            keeps its first canvas)
   Client   each system's own web page, Chrome 155 and Firefox 153.4 ESR HEADLESS (no GPU, all in
            software, for both), viewport = the size measured.
⭐ THE METERS, and from which side:
     paints/s    KasmVNC: every draw on a canvas in the document (2D/WebGL prototypes), bursts > 5 ms
                 apart (the XDamage rule of §7.3); REMOTIX: the page's own gauge `conti.dipinti`, read
                 every 4 ms (it draws in a worker: the document's prototypes never see it)
     delay       the page's keydown (capture) → the first paint after it, p50/p95 (same clock)
     cores       the box's whole cgroup (server + KDE + player) and the server alone (Xvnc · remotix)
     bandwidth   server side, the wire: KasmVNC `ss -ti bytes_sent` (TLS/TCP); REMOTIX the `rete-quic`
                 `byte_spediti` lines of its log (QUIC as sent, one line ≈ every second)
     delivered   KasmVNC: the source size of the biggest drawImage (`consegnata`, `ridotta` = the video
                 mode sent a reduced frame) and the log lines that mention video; REMOTIX: the canvas
                 agreed at the admission (a multiple of 16: 1080 → 1072, 1620 → 1616 — its own rule)
⛔ NOT measured: skipped frames, audio, capacity with N users.
⚠ KasmVNC's configuration is the package's AS IT IS (kasmvnc.yaml: only desktop.resolution), except
   `-disableBasicAuth` (127.0.0.1 only; a headless Firefox cannot answer the dialog) and
   `-hw3d -drinode /dev/dri/renderD128` (its documented GPU acceleration, the twin of xorgxrdp's glamor
   in §7.5; REMOTIX_KASM_GPU=0 = pure default).  Both boxes are `--network host`.

Rows: DIR/registro-kasmvnc.jsonl, one per (system, size, browser, scene), plus DIR/<tag>/ (photo, console).
Exit code: 0 ok · 1 a measure failed (the row says why) · 2 bench error.
"""
import argparse
import importlib.util as _iu
import json
import os
import random
import re
import secrets
import shutil
import types
import statistics
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)
NOME = "kasm-kde"
IMMAGINE = "localhost/kasm-kde:1.5.0"
PORTA = 8701                                   # 127.0.0.1 only; 8511-8514 are rete11's
# ⭐ KasmVNC's documented GPU acceleration (DRI3 on the Intel's render node), the twin of xorgxrdp's
#   glamor in the xrdp comparison (§7.5): without it the session draws in software (llvmpipe) and the
#   player alone costs ~2.4 cores  `[M]` 11 Oct, dry run.  Empty (REMOTIX_KASM_GPU=0) = pure default.
XVNC_GPU = "" if os.environ.get("REMOTIX_KASM_GPU") == "0" else "-hw3d -drinode /dev/dri/renderD128"
DISPLAY = 87                                   # host network ⇒ the abstract X socket is shared: not :0/:1
BASE = "/media/REMOTIX/kasm"
VIDEO_DIR = "/media/REMOTIX/rete11/.c16-video"
VIDEO = "bbb_sunflower_2160p_30fps_normal.mp4"
# ⭐ THE REMOTIX TWIN (coordinator's decision, 11 Oct): the SAME scenes, sizes, browsers and meters
#   against REMOTIX on KDE Wayland, as phase 20 ran it — a box of its own (`kasm-remotix-kde`, from
#   the image rete11/kde:p0, built by 11-accendi.sh with REMOTIX_11_NOME/REMOTIX_11_PORTA) on port
#   8702.  ⛔ rete11-* and 8511-8514 are never touched: 11-accendi.sh runs from a COPY of the rete11
#   tree (/media/REMOTIX/kasm/rete11), with the product of phase 20 (rete11/prodotto, 716e35b).
GEMELLO = "kasm-remotix-kde"
PORTA_R = 8702
RETE11 = "/media/REMOTIX/rete11"
COPIA = os.path.join(BASE, "rete11")
INQUILINO = "c87u1"                            # the tenant pattern C19 recognises
MISURE = {"fhd": (1920, 1080), "2k": (2560, 1440), "3k": (2880, 1620)}
ASSESTA_S = 8                                  # settling, not counted
PORTE_BROWSER = 8720                           # Firefox 8720, Chrome 8721 (debug ports, local)


def _env():
    e = dict(os.environ)
    e["CONTAINERS_STORAGE_CONF"] = os.path.join(BASE, "storage.conf")
    e["TMPDIR"] = os.path.join(BASE, "run")
    return e


def pod(*a, check=False, inp=None, t=300):
    r = subprocess.run(["podman", *a], env=_env(), input=inp, capture_output=True, text=True, timeout=t)
    if check and r.returncode:
        raise RuntimeError("podman %s: %s" % (" ".join(a[:3]), (r.stderr or r.stdout)[-400:]))
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def dentro(cmd, t=60):
    """A command in the session, as the test user, on the session's display."""
    return pod("exec", "-u", "kasm", "-e", "DISPLAY=:%d" % DISPLAY, "-e", "HOME=/home/kasm", NOME,
               "bash", "-lc", cmd, t=t)


# ═══════════════════════════════════════════════════════════════════════════
#  PURE FUNCTIONS (certified)
# ═══════════════════════════════════════════════════════════════════════════
def p(v, q):
    if not v:
        return None
    s = sorted(v)
    return s[min(len(s) - 1, int(round(q * (len(s) - 1))))]


def ritardi(tasti, dipinti, tetto=2000.0):
    """For each key, the wait to the FIRST paint after it (ms); a key with no paint within
    `tetto` counts as lost (None)."""
    out, j = [], 0
    d = sorted(dipinti)
    for k in sorted(tasti):
        while j < len(d) and d[j] <= k:
            j += 1
        out.append(d[j] - k if j < len(d) and d[j] - k <= tetto else None)
    return out


def al_secondo(dipinti, da, a):
    """Paints per whole second in [da, a) ms ⇒ list of counts."""
    n = int((a - da) // 1000)
    c = [0] * max(n, 0)
    for t in dipinti:
        i = int((t - da) // 1000)
        if 0 <= i < n:
            c[i] += 1
    return c


def certifica():
    ok = True

    def guarda(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print(("✅" if vero else "⛔") + " " + cosa)
    guarda("delay = first paint after the key", ritardi([100, 500], [90, 130, 520, 600]) == [30, 20])
    guarda("a key without a paint within the ceiling is lost", ritardi([0], [2500]) == [None])
    guarda("paints per second, edges", al_secondo([0, 999, 1000, 2999, 3000], 0, 3000) == [2, 1, 1])
    guarda("p95 of 1..100 = 95", p(list(range(1, 101)), 0.95) == 95)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE BOX
# ═══════════════════════════════════════════════════════════════════════════
def costruisci():
    c, t = pod("build", "-t", IMMAGINE, "-f", os.path.join(QUI, "Contenitore.kasmvnc"), QUI, t=3600)
    print(t[-1500:])
    return c


def spegni():
    c, t = pod("rm", "-f", "-t", "5", NOME, t=60)
    print("%s: %s" % (NOME, "switched off" if c == 0 else t.strip()[-200:]))


def accendi(misura):
    L, A = MISURE[misura]
    spegni()
    parola = secrets.token_urlsafe(12)
    c, t = pod("run", "-d", "--name", NOME, "--hostname", NOME,
               "--network", "host",                    # no pasta/slirp4netns on the host: Xvnc on 127.0.0.1
               "--shm-size", "2g",                     # not the 64 MB of §8.3: no wall for anyone
               "--memory", "8g", "--oom-score-adj", "800",   # §7.7: if something dies, it is the box
               "--device", "/dev/dri/renderD128", "--group-add", "keep-groups",
               "-v", "%s:/video:ro" % VIDEO_DIR,
               "--user", "kasm", IMMAGINE, "sleep", "infinity", t=120)
    if c:
        raise RuntimeError("the box does not start: " + t[-400:])
    # the test user's KasmVNC password (-w = full rights), random, never written in the image
    pod("exec", "-u", "kasm", "-i", NOME, "kasmvncpasswd", "-u", "kasm", "-w",
        inp="%s\n%s\n" % (parola, parola), check=True)
    with open(os.path.join(BASE, "parola-kasm"), "w") as f:
        f.write(parola + "\n")
    os.chmod(os.path.join(BASE, "parola-kasm"), 0o600)
    # ⚠ `-geometry` is ignored by the wrapper (the yaml wins): the size is the ONLY key written
    dentro("printf 'desktop:\\n  resolution:\\n    width: %d\\n    height: %d\\n' > ~/.vnc/kasmvnc.yaml"
           % (L, A))
    c, t = dentro("vncserver :%d -select-de manual -geometry %dx%d -depth 24 -websocketPort %d "
                  "-interface 127.0.0.1 -disableBasicAuth %s 2>&1 | tail -5" % (DISPLAY, L, A, PORTA, XVNC_GPU), t=90)
    print(t.strip()[-600:])
    for _ in range(60):
        if "plasmashell" in dentro("pgrep -a plasmashell || true")[1]:
            break
        time.sleep(1)
    print(stato())
    return 0


def stato():
    c, t = pod("ps", "-a", "--filter", "name=^%s$" % NOME, "--format", "{{.Names}} {{.Status}} {{.Ports}}")
    s = t.strip() or "%s: not there" % NOME
    if "Up" in s:
        s += "\n" + dentro("xdpyinfo | awk '/dimensions:/{print \"screen\", $2}'; "
                           "pgrep -a Xvnc | cut -c1-160; pgrep -c plasmashell | sed 's/^/plasmashell /'")[1]
    return s


# -- the REMOTIX twin ---------------------------------------------------------
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


def sudo(cmd, t=300):
    r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", cmd], input=_parola_sudo(),
                       capture_output=True, text=True, timeout=t)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


def gem(cmd, t=120):
    return sudo("podman exec %s sh -c %s" % (GEMELLO, _q(cmd)), t)


def gem_sessione(cmd, t=60):
    """A command in the tenant's KDE Wayland session, inside the twin."""
    return gem('u=$(id -u %s); r=/run/user/$u; w=$(ls $r 2>/dev/null | grep -m1 -E "^wayland-[0-9]+$"); '
               'runuser -u %s -- env XDG_RUNTIME_DIR=$r WAYLAND_DISPLAY=$w '
               'DBUS_SESSION_BUS_ADDRESS=unix:path=$r/bus sh -c %s' % (INQUILINO, INQUILINO, _q(cmd)), t)


def byte_remotix():
    """REMOTIX's own wire counter: the last `rete-quic` line of the tenant's connection in the server
    log (written every ~1 s): (connection, time s of the line, byte_spediti).  Server side, QUIC
    packets as sent — the twin of `ss -ti bytes_sent` for KasmVNC."""
    t = gem("grep -a 'rete-quic' /var/lib/rete11/registro.log | grep -a '\\[%s\\]' | tail -1" % INQUILINO)[1]
    m_ = re.search(r"^(\d+):(\d+):([\d.]+) .*rete-quic (\S+) .*byte_spediti=(\d+)", t.strip().splitlines()[-1]
                   if t.strip() else "")
    if not m_:
        return None
    return m_.group(4), int(m_.group(1)) * 3600 + int(m_.group(2)) * 60 + float(m_.group(3)), int(m_.group(5))


def gemello_spegni():
    sudo("podman kill -s KILL %s; podman rm -f -t 0 %s" % (GEMELLO, GEMELLO), 120)
    print("%s: switched off" % GEMELLO)


def gemello_accendi():
    """The twin from scratch: copy of the rete11 tree (the real one is only read), 11-accendi.sh with
    the twin's name and port, accendi · prodotto · server, mpv (the same player as the KasmVNC box),
    the tenant with a random password."""
    os.makedirs(os.path.join(COPIA, ".c16-video"), exist_ok=True)
    subprocess.run(["rsync", "-a", "--delete", "--exclude", ".c16-video", "--exclude", "11-accendi.sh",
                    RETE11 + "/", COPIA + "/"], check=True)
    dst = os.path.join(COPIA, "11-accendi.sh")
    if os.path.exists(dst):
        os.remove(dst)
    shutil.copy(os.path.join(BANCHI, "11-scatole", "11-accendi.sh"), dst)
    v = os.path.join(COPIA, ".c16-video", VIDEO)
    if not os.path.exists(v):
        os.link(os.path.join(VIDEO_DIR, VIDEO), v)        # same disk: no copy
    amb = "env REMOTIX_11_NOME=%s REMOTIX_11_PORTA=%d " % (GEMELLO, PORTA_R)
    for passo in ("accendi", "prodotto", "server"):
        c, t = sudo("cd %s && %sbash 11-accendi.sh %s kde" % (COPIA, amb, passo), 900)
        print("\n".join(t.strip().splitlines()[-4:]))
        # ⚠ `server` ends with a `grep -c` of the red lines: 0 of them ⇒ exit code 1.  The proof is the line.
        if c and not (passo == "server" and "the server listens on %d" % PORTA_R in t):
            raise RuntimeError("11-accendi.sh %s (twin) failed: %s" % (passo, t[-300:]))
    c, t = gem("command -v mpv || (apt-get update -qq && apt-get install -y -qq mpv >/dev/null && command -v mpv)",
               900)
    if c:
        raise RuntimeError("mpv not installed in the twin: " + t[-300:])
    parola = secrets.token_urlsafe(12)
    c, t = gem("id %s >/dev/null 2>&1 || useradd -m -s /bin/bash %s; echo %s:%s | chpasswd"
               % (INQUILINO, INQUILINO, INQUILINO, parola))
    if c:
        raise RuntimeError("tenant not created: " + t[-300:])
    f = os.path.join(BASE, "parola-remotix")
    with open(f, "w") as fh:
        fh.write(parola + "\n")
    os.chmod(f, 0o600)
    print("%s: REMOTIX on 127.0.0.1:%d, tenant %s" % (GEMELLO, PORTA_R, INQUILINO))
    return 0


# -- the meters on the server side ------------------------------------------
def _pid(sistema):
    if sistema == "remotix":
        return int(sudo("podman inspect -f '{{.State.Pid}}' %s" % GEMELLO)[1].strip().splitlines()[-1])
    return int(pod("inspect", "-f", "{{.State.Pid}}", NOME, check=True)[1].strip())


def _cgroup(sistema):
    """The box's WHOLE cgroup: the ancestor `libpod-<id>.scope` (rootful with systemd inside: pid 1
    is in …/init.scope; rootless: …/container)."""
    for r in open("/proc/%d/cgroup" % _pid(sistema)):
        if r.startswith("0::"):
            p = r.strip()[3:]
            while p not in ("", "/") and not re.search(r"libpod-[0-9a-f]+\.scope$", p):
                p = os.path.dirname(p)
            if p in ("", "/"):
                p = r.strip()[3:]
            return "/sys/fs/cgroup" + p
    raise RuntimeError("no cgroup v2 for the box")


def contatori(sistema):
    """(t s, cpu of the box µs, cpu of the server µs, bytes sent or None).
    server = Xvnc (KasmVNC) · the `remotix` processes (REMOTIX: server and its copying children)."""
    cg = _cgroup(sistema)
    cpu = int(re.search(r"usage_usec (\d+)", open(cg + "/cpu.stat").read()).group(1))
    tck = os.sysconf("SC_CLK_TCK")
    nomi = ("remotix",) if sistema == "remotix" else ("Xvnc",)
    sv = 0
    for radice, _d, files in os.walk(cg):
        if "cgroup.procs" not in files:
            continue
        try:
            pids = open(os.path.join(radice, "cgroup.procs")).read().split()
        except OSError:
            continue
        for pid in pids:
            try:
                if open("/proc/%s/comm" % pid).read().strip() in nomi:
                    f = open("/proc/%s/stat" % pid).read().rsplit(")", 1)[1].split()
                    sv += (int(f[11]) + int(f[12])) * 1_000_000 // tck
            except OSError:
                pass
    return time.time(), cpu, sv, (byte_inviati() if sistema == "kasmvnc" else None)


def byte_inviati():
    """Bytes KasmVNC sent on its TCP connections (port PORTA): the wire, TLS included."""
    t = subprocess.run(["ss", "-tinH", "state", "established", "( sport = :%d )" % PORTA],
                       capture_output=True, text=True).stdout
    return sum(int(x) for x in re.findall(r"bytes_sent:(\d+)", t))


def guardia():
    """§7.7: below 3 GiB available the measure is not started (and is stopped)."""
    m = int(re.search(r"MemAvailable:\s+(\d+)", open("/proc/meminfo").read()).group(1))
    return m >= 3 * 1024 * 1024, m // 1024


# ═══════════════════════════════════════════════════════════════════════════
#  THE PAGE
# ═══════════════════════════════════════════════════════════════════════════
SONDA = r"""
if (!window.__kx) {
  const K = window.__kx = {d: [], k: [], last: -1e9, n: 0, sorg: null, dest: null};
  const vis = (c) => c && c.isConnected && c.width >= 320;
  const segna = function () {
    if (!vis(this.canvas)) return;
    const t = performance.now(); K.n++;
    if (t - K.last > 5) K.d.push(t);
    K.last = t;
  };
  /* ⭐ the size DELIVERED: of the drawImage calls, the one with the biggest destination, and its
     source (KasmVNC's video mode sends a reduced frame and the page enlarges it) */
  const misura = function (a) {
    const im = a[0]; if (!im) return;
    let sw = im.width || im.videoWidth || 0, sh = im.height || im.videoHeight || 0, dw = sw, dh = sh;
    if (a.length === 5) { dw = a[3]; dh = a[4]; }
    if (a.length === 9) { sw = a[3]; sh = a[4]; dw = a[7]; dh = a[8]; }
    if (!K.dest || dw * dh > K.dest[0] * K.dest[1] ||
        (dw * dh === K.dest[0] * K.dest[1] && sw * sh < K.sorg[0] * K.sorg[1])) {
      K.dest = [dw, dh]; K.sorg = [sw, sh]; }
  };
  const P2 = window.CanvasRenderingContext2D && CanvasRenderingContext2D.prototype;
  if (P2) { const o = P2.drawImage; P2.drawImage = function () { try { misura(arguments); } catch (e) {}
    return o.apply(this, arguments); }; }
  const avvolgi = (P, metodi) => { if (!P) return; for (const m of metodi) { const o = P[m];
    if (typeof o !== 'function') continue;
    P[m] = function () { segna.call(this); return o.apply(this, arguments); }; } };
  avvolgi(window.CanvasRenderingContext2D && CanvasRenderingContext2D.prototype,
          ['drawImage', 'putImageData', 'fillRect']);
  for (const G of [window.WebGLRenderingContext, window.WebGL2RenderingContext])
    avvolgi(G && G.prototype, ['drawArrays', 'drawElements']);
  avvolgi(window.ImageBitmapRenderingContext && ImageBitmapRenderingContext.prototype,
          ['transferFromImageBitmap']);
  document.addEventListener('keydown', () => K.k.push(performance.now()), true);
}
"""


SONDA_R = r"""
if (!window.__kx) {
  const K = window.__kx = {d: [], k: [], wt: [], ultimo: null};
  /* the page's own gauge (REMOTIX.schermo.conti.dipinti, the frames that reached the glass), read
     every 4 ms — the probe of 16-attore.py at a finer step: the page draws in a worker, the
     prototypes of the document never see it */
  setInterval(function () {
    const s = window.REMOTIX && window.REMOTIX.schermo;
    const d = s && s.conti ? s.conti.dipinti : null;
    if (d === null || d === K.ultimo) return;
    if (K.ultimo !== null) K.d.push(performance.now());
    K.ultimo = d;
  }, 4);
  document.addEventListener('keydown', () => K.k.push(performance.now()), true);
  /* the transport, to read its bytes (WebTransport.getStats): it is born at the login, after this */
  const W = window.WebTransport;
  if (W) { const F = function (u, o) { const t = new W(u, o); K.wt.push(t); return t; };
           F.prototype = W.prototype; window.WebTransport = F; }
}
"""


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


class Pagina:
    """The browser on KasmVNC's own web client, headless, window = the remote screen."""

    def __init__(self, browser, L, A, sistema="kasmvnc"):
        cv = _carica("clientveri", os.path.join(BANCHI, "12-client-veri.py"))
        cv.FINESTRA[:] = [L, A]
        self.cv, self.nome, self.sistema = cv, browser, sistema
        self._L, self._A, self.ammesso = L, A, None
        self.g = (cv.GuidaFirefox(PORTE_BROWSER, False) if browser == "firefox"
                  else cv.GuidaChrome(PORTE_BROWSER + 1, False))
        if browser == "chrome":
            # ⛔ the Network domain sends an event per WebSocket frame (base64 payload): at 25 fps the
            #   CDP socket drowns and `Runtime.evaluate` never answers  `[M]` 11 Oct, dry run
            self.g.cdp.chiama("Network.disable")

    def apri(self):
        if self.sistema == "remotix":
            return self.apri_remotix()
        ok, perche = self.g.vai("https://127.0.0.1:%d/?autoconnect=1&resize=remote" % PORTA)
        if not ok:
            raise RuntimeError("the page does not open: " + perche)
        for _ in range(60):
            time.sleep(0.5)
            self.inietta()
            # connected = the remote screen's canvas is in the page (the first frame may have been
            # drawn before the probe: a still desktop paints nothing more)
            if self.js("return [...document.querySelectorAll('canvas')].some("
                       "c => c.isConnected && c.width >= 320 && c.height >= 240)"):
                return
        raise RuntimeError("no remote-screen canvas in 30 s (KasmVNC client not connected?)")

    def apri_remotix(self):
        """The REMOTIX page as the suite opens it (`Prova` of 12-client-veri: form, login, first
        frame NOT degenerate), with the probe armed BEFORE the login (the transport is born there)."""
        parola = open(os.path.join(BASE, "parola-remotix")).read().strip()
        o = types.SimpleNamespace(tetto_s=90, utente=INQUILINO, salva=None)
        pr = self.cv.Prova(self.g, o, "https://127.0.0.1:%d/" % PORTA_R, parola)
        ok, perche = pr.apri()
        if not ok:
            raise RuntimeError("REMOTIX page: " + perche)
        # the page's own measure of the view (documentElement.client*: a scrollbar takes 15 px)
        self.a_misura(self._L, self._A, campo="document.documentElement.client")
        self.g.js(self.cv._inject(SONDA_R))
        # ⚠ not `Prova.entra`: it waits for «Admitted», and the product of phase 20 (716e35b) is
        #   older than the English pass and writes «Ammesso»
        r = self.g.js(self.cv.JS_ENTER, INQUILINO, parola)
        if r != "sent":
            raise RuntimeError("REMOTIX login form: %s" % r)
        fine = time.time() + 90
        st = {}
        while time.time() < fine:
            st = pr.stato()
            if st.get("sessione") and st.get("esito_classe") == "bene":
                break
            if st.get("esito_classe") == "male" and st.get("esito"):
                raise RuntimeError("REMOTIX login refused: %s" % st.get("esito"))
            time.sleep(0.4)
        else:
            raise RuntimeError("REMOTIX login: no admission in 90 s (%s)" % st.get("esito"))
        self.ammesso = st.get("esito")
        e, perche, _s = pr.primo_fotogramma()
        if e != self.cv.VERDE:
            raise RuntimeError("REMOTIX first frame: " + perche)

    def byte_ricevuti(self):
        """REMOTIX: bytesReceived of the page's WebTransport (None if the browser has no getStats)."""
        try:
            return self.g.js("const K = window.__kx; const t = K && K.wt[K.wt.length - 1];"
                             "if (!t || !t.getStats) return null;"
                             "return t.getStats().then(s => s.bytesReceived ?? null, () => null);")
        except Exception:                            # noqa: BLE001
            return None

    def consegnata(self):
        """The size of the image the page RECEIVES (not the one it shows)."""
        if self.sistema == "remotix":
            # the canvas the server agreed on, from the admission line («… tela 1920×1072 …»); the
            # stream is that size (no video mode).  ⚠ The canvas is a multiple of 16 (TELA_A_PASSO):
            # 1080 → 1072, 1620 → 1616 — REMOTIX's own rule, declared, not the bench's
            m_ = re.search(r"(\d+)×(\d+)", self.ammesso or "")
            return {"tela": [int(m_.group(1)), int(m_.group(2))] if m_ else None, "ammesso": self.ammesso}
        return self.g.js("const K = window.__kx; return K ? {sorgente: K.sorg, destinazione: K.dest} : null;")

    def a_misura(self, L, A, campo="inner"):
        """The VIEWPORT must be L×A (resize=remote: the remote screen follows it): the window is
        corrected by the difference between window and viewport (Chrome headless: 88 px)."""
        self._L, self._A = L, A
        for _ in range(3):
            if campo == "inner":
                w, h = self.js("return [innerWidth, innerHeight]")
            else:
                w, h = self.js("return [%sWidth, %sHeight]" % (campo, campo))
            if (w, h) == (L, A):
                return True
            if self.nome == "chrome":
                wid = self.g.cdp.chiama("Browser.getWindowForTarget")["windowId"]
                b = self.g.cdp.chiama("Browser.getWindowBounds", windowId=wid)["bounds"]
                self.g.cdp.chiama("Browser.setWindowBounds", windowId=wid, bounds={
                    "width": b["width"] + L - w, "height": b["height"] + A - h})
            else:
                r = self.g.m.chiama("WebDriver:GetWindowRect")
                r = r.get("value", r)
                self.g.m.chiama("WebDriver:SetWindowRect", {"width": r["width"] + L - w,
                                                             "height": r["height"] + A - h})
            time.sleep(2)
        return False

    def js(self, corpo):
        return self.g.js(corpo)

    def inietta(self):
        self.g.js(self.cv._inject(SONDA_R if self.sistema == "remotix" else SONDA))

    def ora(self):
        return self.js("return performance.now()")

    def raccogli(self, da):
        return self.js("const K=window.__kx; return {d: K.d.filter(t=>t>=%f), k: K.k.filter(t=>t>=%f),"
                       " n: K.n, w: innerWidth, h: innerHeight};" % (da, da))

    def clic_centro(self, L, A):
        self.g.clic(L // 2, A // 2)

    def tasto(self, ch):
        if self.nome == "firefox":
            self.g._actions([{"type": "key", "id": "tastiera", "actions": [
                {"type": "keyDown", "value": ch}, {"type": "pause", "duration": 40},
                {"type": "keyUp", "value": ch}]}])
            return
        if ch == "\ue007":
            k = dict(key="Enter", code="Enter", windowsVirtualKeyCode=13, text="\r")
        else:
            k = dict(key=ch, code="Key" + ch.upper(), windowsVirtualKeyCode=ord(ch.upper()), text=ch)
        self.g.cdp.chiama("Input.dispatchKeyEvent", type="keyDown", **k)
        time.sleep(0.04)
        k.pop("text", None)
        self.g.cdp.chiama("Input.dispatchKeyEvent", type="keyUp", **k)

    def foto(self, percorso):
        try:
            if self.nome == "chrome":
                import base64
                d = self.g.cdp.chiama("Page.captureScreenshot", format="png")["data"]
                open(percorso, "wb").write(base64.b64decode(d))
            else:
                import base64
                d = self.g.m.chiama("WebDriver:TakeScreenshot", {"full": False})
                d = d.get("value", d) if isinstance(d, dict) else d
                open(percorso, "wb").write(base64.b64decode(d))
        except Exception as e:                       # noqa: BLE001
            print("   (photo not taken: %s)" % e)

    def versione(self):
        return self.g.palco()

    def chiudi(self):
        try:
            self.g.chiudi()
        except Exception:                            # noqa: BLE001
            pass


# ═══════════════════════════════════════════════════════════════════════════
#  ONE MEASURE
# ═══════════════════════════════════════════════════════════════════════════
def scena_su(sistema, scena):
    """Starts the scene in the session of the system (same player, same file, same terminal)."""
    if sistema == "remotix":
        if scena == "video":
            return gem_sessione("setsid -f mpv --fs --loop=inf --no-audio --hwdec=vaapi --really-quiet "
                                "/rete11/.c16-video/%s >/tmp/mpv-%s.log 2>&1" % (VIDEO, INQUILINO))
        return gem_sessione("setsid -f konsole --fullscreen -e cat >/dev/null 2>&1")
    if scena == "video":
        return dentro("setsid -f mpv --fs --loop=inf --no-audio --hwdec=vaapi --really-quiet "
                      "/video/%s >/tmp/mpv.log 2>&1" % VIDEO)
    return dentro("setsid -f konsole --fullscreen -e cat >/tmp/konsole.log 2>&1")


def scene_giu(sistema):
    if sistema == "remotix":
        return gem("pkill -u %s -x mpv; pkill -u %s -x konsole; true" % (INQUILINO, INQUILINO))
    return dentro("pkill -x mpv; pkill -x konsole; true")


def schermo_remoto(sistema):
    if sistema == "remotix":
        return gem_sessione("command -v kscreen-doctor >/dev/null && kscreen-doctor -o 2>/dev/null "
                            "| sed 's/\\x1b\\[[0-9;]*m//g' | grep -oE '[0-9]+x[0-9]+@[0-9.]+\\*' | head -1 "
                            "| cut -d@ -f1")[1].strip()
    return dentro("xdpyinfo | awk '/dimensions:/{print $2}'")[1].strip()


def log_video_kasm():
    """KasmVNC: how many lines of its log speak of the video mode (cumulative)."""
    t = dentro("grep -ciE 'video' ~/.vnc/*.log 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}'")[1]
    try:
        return int(t.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None


def misura(m, browser, scena, secondi, cartella, sistema="kasmvnc"):
    L, A = MISURE[m]
    tag = "%s-%s-%s-%s" % (sistema, m, browser, scena)
    ev = os.path.join(cartella, tag)
    os.makedirs(ev, exist_ok=True)
    riga = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "sistema": sistema,
            "desktop": "kde-wayland" if sistema == "remotix" else "kde-x11",
            "misura": m, "largo": L, "alto": A, "browser": browser, "scena": scena, "secondi": secondi}
    ok, libera = guardia()
    if not ok:
        riga.update(esito="NON MISURATO", ragione="host resources: %d MB available < 3 GiB" % libera)
        return riga
    scene_giu(sistema)
    if sistema == "remotix":
        # ⛔ a RESUMED session keeps the canvas it was born with (`[M]` 11 Oct, dry run: «sessione
        #   ripresa, tela 1904×1072» with a 1920 view) ⇒ every measure starts from a NEW session, as
        #   KasmVNC's box is born again at every size
        gem("loginctl terminate-user %s; true" % INQUILINO)
        time.sleep(3)
    pg = Pagina(browser, L, A, sistema)
    try:
        riga["client"] = pg.versione()
        pg.g.vai("about:blank")
        pg.a_misura(L, A)                           # BEFORE: REMOTIX asks its canvas at the attach
        pg.apri()
        riga["vista_giusta"] = pg.a_misura(L, A)
        time.sleep(2)
        scena_su(sistema, scena)
        time.sleep(ASSESTA_S)
        if scena == "tasti":
            pg.clic_centro(L, A)                    # focus on the canvas and on konsole
            time.sleep(1)
        v0 = log_video_kasm() if sistema == "kasmvnc" else None
        t0p = pg.ora()
        c0 = contatori(sistema)
        b0 = byte_remotix() if sistema == "remotix" else None
        rnd = random.Random("kasm:%s-%s-%s" % (m, browser, scena))   # the SAME keys for both systems
        fine = time.time() + secondi
        n = 0
        while time.time() < fine:
            if scena == "tasti":
                n += 1
                pg.tasto("" if n % 60 == 0 else rnd.choice("asdfghjkl"))
                time.sleep(rnd.uniform(0.3, 0.5))
            else:
                time.sleep(1)
            if not guardia()[0]:
                riga["interrotta"] = "host resources (§7.7)"
                break
        c1 = contatori(sistema)
        time.sleep(1.2 if sistema == "remotix" else 0)   # one more log line of the counter
        b1 = byte_remotix() if sistema == "remotix" else None
        t1p = pg.ora()
        r = pg.raccogli(t0p)
        riga["consegnata"] = pg.consegnata()
        if sistema == "kasmvnc":
            v1 = log_video_kasm()
            riga["righe_video_nel_log"] = (v1 - v0) if None not in (v0, v1) else None
            k = riga["consegnata"] or {}
            src, dst = k.get("sorgente"), k.get("destinazione")
            riga["ridotta"] = bool(src and dst and src[0] * src[1] < 0.9 * dst[0] * dst[1])
        pg.foto(os.path.join(ev, "foto.png"))
        riga["schermo_remoto"] = schermo_remoto(sistema)
        riga["vista_pagina"] = pg.js("return [innerWidth, innerHeight]")
        dt = c1[0] - c0[0]
        per_s = al_secondo(r["d"], t0p, t1p)
        if sistema == "remotix":
            banda = None
            if b0 and b1 and b0[0] == b1[0] and b1[1] > b0[1]:
                banda = (b1[2] - b0[2]) * dt / (b1[1] - b0[1])      # rate over the log's own interval
            riga["banda_da"] = "server log rete-quic byte_spediti (server side, QUIC as sent)"
        else:
            banda = c1[3] - c0[3]
            riga["banda_da"] = "ss -ti bytes_sent of KasmVNC's TCP connections (server side)"
        riga.update(
            dipinti_al_s=round(len([x for x in r["d"] if x < t0p + 1000 * len(per_s)]) / max(len(per_s), 1), 2),
            dipinti_al_s_p5=p(per_s, 0.05), dipinti_al_s_mediana=p(per_s, 0.5),
            fermo_piu_lungo_ms=round(max([b - a for a, b in zip(r["d"], r["d"][1:])] or [0]), 1),
            nuclei_scatola=round((c1[1] - c0[1]) / 1e6 / dt, 3),
            nuclei_server=round((c1[2] - c0[2]) / 1e6 / dt, 3),
            banda_mbit_s=round(banda * 8 / 1e6 / dt, 2) if banda is not None else None,
            durata_s=round(dt, 1))
        if scena == "tasti":
            w = ritardi(r["k"], r["d"])
            v = [x for x in w if x is not None]
            riga.update(tasti=len(w), tasti_persi=len(w) - len(v),
                        ritardo_p50_ms=round(p(v, 0.5), 1) if v else None,
                        ritardo_p95_ms=round(p(v, 0.95), 1) if v else None)
        if sistema == "remotix":
            tela = (riga["consegnata"] or {}).get("tela")
            schermo_ok = tela == [L, A - A % 16]
            riga["ridotta"] = False
        else:
            schermo_ok = riga["schermo_remoto"] == "%dx%d" % (L, A)
        riga["esito"] = "MISURATO" if schermo_ok and per_s and \
            (scena != "tasti" or riga.get("ritardo_p95_ms")) else "NON MISURATO"
    except Exception as e:                           # noqa: BLE001
        import traceback
        riga.update(esito="NON MISURATO", ragione=("%s: %s" % (type(e).__name__, e))[:300],
                    traccia=traceback.format_exc()[-600:])
    finally:
        try:
            js, rete, _ = pg.g.errors_out()
            open(os.path.join(ev, "console.txt"), "w").write("\n".join(js + rete))
        except Exception:                            # noqa: BLE001
            pass
        pg.chiudi()
        scene_giu(sistema)
    return riga


def scrivi(cartella, riga):
    with open(os.path.join(cartella, "registro-kasmvnc.jsonl"), "a") as f:
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    chiavi = ("sistema", "misura", "browser", "scena", "esito", "dipinti_al_s", "ritardo_p95_ms",
              "nuclei_scatola", "nuclei_server", "banda_mbit_s", "schermo_remoto", "consegnata", "ridotta",
              "ragione")
    print("   " + " · ".join("%s=%s" % (k, riga[k]) for k in chiavi if k in riga), flush=True)


def campagna(o):
    """Row by row, at the same moment: for each (size, browser, scene) KasmVNC then REMOTIX."""
    os.makedirs(o.dir, exist_ok=True)
    sistemi = o.sistemi.split(",")
    errori = 0
    if "remotix" in sistemi:
        gemello_accendi()
    try:
        for m in o.misure.split(","):
            if "kasmvnc" in sistemi:
                accendi(m)
            for b in o.browser.split(","):
                for sc in o.scene.split(","):
                    for si in sistemi:
                        if os.path.exists(os.path.join(o.dir, "FERMA")):
                            print("FERMA found: stop")
                            return 1
                        print("⏵ %s %s %s %s (%d s)" % (si, m, b, sc, o.secondi), flush=True)
                        riga = misura(m, b, sc, o.secondi, o.dir, si)
                        scrivi(o.dir, riga)
                        errori += riga.get("esito") != "MISURATO"
    finally:
        spegni()
        if "remotix" in sistemi:
            gemello_spegni()
    return 1 if errori else 0


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("cosa", choices=("costruisci", "accendi", "spegni", "stato", "misura", "campagna",
                                    "certifica", "gemello-accendi", "gemello-spegni"))
    a.add_argument("--sistema", choices=("kasmvnc", "remotix"), default="kasmvnc")
    a.add_argument("--sistemi", default="kasmvnc,remotix")
    a.add_argument("--misura", choices=tuple(MISURE), default="fhd")
    a.add_argument("--misure", default="fhd,2k,3k")
    a.add_argument("--browser", default="chrome,firefox")
    a.add_argument("--scena", choices=("video", "tasti"), default="video")
    a.add_argument("--scene", default="video,tasti")
    a.add_argument("--secondi", type=int, default=90)
    a.add_argument("--dir", default=os.path.join("/media/REMOTIX/misure/fase20-kasmvnc",
                                                  time.strftime("%Y%m%d-%H%M")))
    o = a.parse_args()
    if o.cosa == "certifica":
        return certifica()
    if o.cosa == "costruisci":
        return costruisci()
    if o.cosa == "accendi":
        return accendi(o.misura)
    if o.cosa == "gemello-accendi":
        return gemello_accendi()
    if o.cosa == "gemello-spegni":
        return gemello_spegni()
    if o.cosa == "spegni":
        return spegni()
    if o.cosa == "stato":
        print(stato())
        return 0
    if o.cosa == "misura":
        os.makedirs(o.dir, exist_ok=True)
        riga = misura(o.misura, o.browser.split(",")[0], o.scena, o.secondi, o.dir, o.sistema)
        scrivi(o.dir, riga)
        return 0 if riga.get("esito") == "MISURATO" else 1
    return campagna(o)


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except KeyboardInterrupt:
        sys.exit(2)
