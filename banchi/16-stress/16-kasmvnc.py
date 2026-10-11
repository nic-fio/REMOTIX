#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-kasmvnc — THE LEAN COMPARISON WITH KasmVNC (fasi/20-le-prestazioni.md §9, 11 Oct 2026)

    (on the server, as nicfio, NO sudo: the box is rootless podman, storage on /media)
    python3 16-kasmvnc.py costruisci                 the image kasm-kde (Contenitore.kasmvnc)
    python3 16-kasmvnc.py accendi --misura fhd       the box kasm-kde, KasmVNC on 127.0.0.1:8701
    python3 16-kasmvnc.py spegni | stato
    python3 16-kasmvnc.py misura --misura fhd --browser chrome --scena video --secondi 30 --dir D
    python3 16-kasmvnc.py campagna --dir D [--misure fhd,2k,3k] [--browser chrome,firefox]
                                           [--scene video,tasti] [--secondi 60]
    python3 16-kasmvnc.py certifica                  the pure functions, no box, no browser

⭐ WHAT IT IS.  Not the climb of §7 (that is ~2 days of work): ONE user, the two scenes that decide,
   measured from the same side as the xrdp comparison (§7.3, «from the watcher's side»):
     video   the 4K film at 30 fps (the same file as profile D, bbb_sunflower_2160p_30fps_normal) in mpv
             full screen inside the KDE X11 session  ⇒ paints/s delivered to the page.  Decoding on
             the Intel (`--hwdec=vaapi-copy`: Xvnc has no DRI3, plain `vaapi` falls back to the
             processor and the player alone would cost ~2 cores of the «server side»)
     tasti   a konsole running `cat`, one key every ~0.4 s typed IN THE BROWSER (it goes through
             KasmVNC's channel, like the user's)  ⇒ delay key → first paint, p50/p95
   For both: the box's processor (cgroup, cores = server side: Xvnc + KDE + the application, the same
   «box total» of §7.4) and Xvnc's alone; the bandwidth = `bytes_sent` of KasmVNC's TCP connections
   (`ss -ti`, the wire, TLS included).  ⚠ The box is `--network host` (the host has neither pasta nor
   slirp4netns): Xvnc listens on 127.0.0.1:8701 only, display :87.
⭐ THE PROBE (in the page): the KasmVNC web client draws on a <canvas>; the prototypes of 2D / WebGL /
   bitmaprenderer are wrapped and every draw on a canvas IN THE DOCUMENT is timed; draws closer than
   5 ms are one paint (the same burst rule as XDamage for xrdp, §7.3).  The key time is the page's
   `keydown` (capture), so key and paint are on the same clock.
⛔ What is NOT measured: skipped frames (KasmVNC drops frames on the server, the client cannot count
   them — as for xrdp), audio, capacity with N users.
⚠ The configuration is the package's AS IT IS (kasmvnc.yaml untouched), except: basic auth off
   (`-disableBasicAuth`: the port is bound to 127.0.0.1 only, and a headless Firefox cannot answer the
   auth dialog), the session command = startplasma-x11, the screen size.  ⚠ The browsers are headless
   («HEADLESS — no GPU, all in software»), on the same server, like the phase-20 benches.

Rows: DIR/registro-kasmvnc.jsonl, one per (size, browser, scene), plus DIR/<tag>/ (photo, console).
Exit code: 0 ok · 1 a measure failed (the row says why) · 2 bench error.
"""
import argparse
import importlib.util as _iu
import json
import os
import random
import re
import secrets
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


# -- the meters on the server side ------------------------------------------
def _pid():
    return int(pod("inspect", "-f", "{{.State.Pid}}", NOME, check=True)[1].strip())


def _cgroup():
    for r in open("/proc/%d/cgroup" % _pid()):
        if r.startswith("0::"):
            return "/sys/fs/cgroup" + r.strip()[3:]
    raise RuntimeError("no cgroup v2 for the box")


def contatori():
    """(t s, cpu of the box µs, cpu of Xvnc µs, bytes sent by the box)."""
    cg = _cgroup()
    # the box's cgroup may be the leaf or its parent (podman's "container" sub-cgroup)
    cpu = 0
    for c in (cg, os.path.dirname(cg)):
        try:
            cpu = int(re.search(r"usage_usec (\d+)", open(c + "/cpu.stat").read()).group(1))
            if NOME in c or "libpod" in c:
                break
        except OSError:
            continue
    tck = os.sysconf("SC_CLK_TCK")
    xv = 0
    for pid in open(cg + "/cgroup.procs").read().split():
        try:
            if open("/proc/%s/comm" % pid).read().strip() == "Xvnc":
                f = open("/proc/%s/stat" % pid).read().rsplit(")", 1)[1].split()
                xv += (int(f[11]) + int(f[12])) * 1_000_000 // tck
        except OSError:
            pass
    return time.time(), cpu, xv, byte_inviati()


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
  const K = window.__kx = {d: [], k: [], last: -1e9, n: 0};
  const vis = (c) => c && c.isConnected && c.width >= 320;
  const segna = function () {
    if (!vis(this.canvas)) return;
    const t = performance.now(); K.n++;
    if (t - K.last > 5) K.d.push(t);
    K.last = t;
  };
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


def _carica(nome, file):
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


class Pagina:
    """The browser on KasmVNC's own web client, headless, window = the remote screen."""

    def __init__(self, browser, L, A):
        cv = _carica("clientveri", os.path.join(BANCHI, "12-client-veri.py"))
        cv.FINESTRA[:] = [L, A]
        self.cv, self.nome = cv, browser
        self.g = (cv.GuidaFirefox(PORTE_BROWSER, False) if browser == "firefox"
                  else cv.GuidaChrome(PORTE_BROWSER + 1, False))
        if browser == "chrome":
            # ⛔ the Network domain sends an event per WebSocket frame (base64 payload): at 25 fps the
            #   CDP socket drowns and `Runtime.evaluate` never answers  `[M]` 11 Oct, dry run
            self.g.cdp.chiama("Network.disable")

    def apri(self):
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

    def a_misura(self, L, A):
        """The VIEWPORT must be L×A (resize=remote: the remote screen follows it): the window is
        corrected by the difference between window and viewport (Chrome headless: 88 px)."""
        for _ in range(3):
            w, h = self.js("return [innerWidth, innerHeight]")
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
        self.g.js(self.cv._inject(SONDA))

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
def misura(m, browser, scena, secondi, cartella):
    L, A = MISURE[m]
    tag = "%s-%s-%s" % (m, browser, scena)
    ev = os.path.join(cartella, tag)
    os.makedirs(ev, exist_ok=True)
    riga = {"t": time.strftime("%Y-%m-%dT%H:%M:%S"), "sistema": "kasmvnc", "desktop": "kde-x11",
            "misura": m, "largo": L, "alto": A, "browser": browser, "scena": scena, "secondi": secondi}
    ok, libera = guardia()
    if not ok:
        riga.update(esito="NON MISURATO", ragione="host resources: %d MB available < 3 GiB" % libera)
        return riga
    dentro("pkill -x mpv; pkill -x konsole; true")
    pg = Pagina(browser, L, A)
    try:
        riga["client"] = pg.versione()
        pg.apri()
        riga["vista_giusta"] = pg.a_misura(L, A)
        time.sleep(2)
        riga["schermo_remoto"] = dentro("xdpyinfo | awk '/dimensions:/{print $2}'")[1].strip()
        riga["vista_pagina"] = pg.js("return [innerWidth, innerHeight]")
        if scena == "video":
            dentro("setsid -f mpv --fs --loop=inf --no-audio --hwdec=vaapi-copy --really-quiet "
                   "/video/%s >/tmp/mpv.log 2>&1" % VIDEO)
        else:
            dentro("setsid -f konsole --fullscreen -e cat >/tmp/konsole.log 2>&1")
        time.sleep(ASSESTA_S)
        if scena == "tasti":
            pg.clic_centro(L, A)                    # focus on the canvas and on konsole
            time.sleep(1)
        t0p = pg.ora()
        c0 = contatori()
        rnd = random.Random("kasm:%s" % tag)
        fine = time.time() + secondi
        n = 0
        while time.time() < fine:
            if scena == "tasti":
                n += 1
                pg.tasto("\ue007" if n % 60 == 0 else rnd.choice("asdfghjkl"))
                time.sleep(rnd.uniform(0.3, 0.5))
            else:
                time.sleep(1)
            if not guardia()[0]:
                riga["interrotta"] = "host resources (§7.7)"
                break
        c1 = contatori()
        t1p = pg.ora()
        r = pg.raccogli(t0p)
        pg.foto(os.path.join(ev, "foto.png"))
        riga["schermo_remoto"] = dentro("xdpyinfo | awk '/dimensions:/{print $2}'")[1].strip()
        riga["vista_pagina"] = pg.js("return [innerWidth, innerHeight]")
        dt = c1[0] - c0[0]
        per_s = al_secondo(r["d"], t0p, t1p)
        riga.update(
            dipinti_al_s=round(len([x for x in r["d"] if x < t0p + 1000 * len(per_s)]) / max(len(per_s), 1), 2),
            dipinti_al_s_p5=p(per_s, 0.05), dipinti_al_s_mediana=p(per_s, 0.5),
            fermo_piu_lungo_ms=round(max([b - a for a, b in zip(r["d"], r["d"][1:])] or [0]), 1),
            nuclei_scatola=round((c1[1] - c0[1]) / 1e6 / dt, 3),
            nuclei_xvnc=round((c1[2] - c0[2]) / 1e6 / dt, 3),
            banda_mbit_s=round((c1[3] - c0[3]) * 8 / 1e6 / dt, 2),
            durata_s=round(dt, 1))
        if scena == "tasti":
            w = ritardi(r["k"], r["d"])
            v = [x for x in w if x is not None]
            riga.update(tasti=len(w), tasti_persi=len(w) - len(v),
                        ritardo_p50_ms=round(p(v, 0.5), 1) if v else None,
                        ritardo_p95_ms=round(p(v, 0.95), 1) if v else None)
        riga["esito"] = "MISURATO" if riga["schermo_remoto"] == "%dx%d" % (L, A) and per_s and (scena != "tasti" or riga.get("ritardo_p95_ms")) \
            else "NON MISURATO"
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
        dentro("pkill -x mpv; pkill -x konsole; true")
    return riga


def scrivi(cartella, riga):
    with open(os.path.join(cartella, "registro-kasmvnc.jsonl"), "a") as f:
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    chiavi = ("misura", "browser", "scena", "esito", "dipinti_al_s", "ritardo_p95_ms", "nuclei_scatola",
              "nuclei_xvnc", "banda_mbit_s", "schermo_remoto", "ragione")
    print("   " + " · ".join("%s=%s" % (k, riga[k]) for k in chiavi if k in riga), flush=True)


def campagna(o):
    os.makedirs(o.dir, exist_ok=True)
    errori = 0
    for m in o.misure.split(","):
        accendi(m)
        for b in o.browser.split(","):
            for s in o.scene.split(","):
                if os.path.exists(os.path.join(o.dir, "FERMA")):
                    print("FERMA found: stop")
                    spegni()
                    return 1
                print("⏵ %s %s %s (%d s)" % (m, b, s, o.secondi), flush=True)
                riga = misura(m, b, s, o.secondi, o.dir)
                scrivi(o.dir, riga)
                errori += riga.get("esito") != "MISURATO"
    spegni()
    return 1 if errori else 0


def main():
    a = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    a.add_argument("cosa", choices=("costruisci", "accendi", "spegni", "stato", "misura", "campagna",
                                    "certifica"))
    a.add_argument("--misura", choices=tuple(MISURE), default="fhd")
    a.add_argument("--misure", default="fhd,2k,3k")
    a.add_argument("--browser", default="chrome,firefox")
    a.add_argument("--scena", choices=("video", "tasti"), default="video")
    a.add_argument("--scene", default="video,tasti")
    a.add_argument("--secondi", type=int, default=60)
    a.add_argument("--dir", default=os.path.join("/media/REMOTIX/misure/fase20-kasmvnc",
                                                  time.strftime("%Y%m%d-%H%M")))
    o = a.parse_args()
    if o.cosa == "certifica":
        return certifica()
    if o.cosa == "costruisci":
        return costruisci()
    if o.cosa == "accendi":
        return accendi(o.misura)
    if o.cosa == "spegni":
        return spegni()
    if o.cosa == "stato":
        print(stato())
        return 0
    if o.cosa == "misura":
        os.makedirs(o.dir, exist_ok=True)
        riga = misura(o.misura, o.browser.split(",")[0], o.scena, o.secondi, o.dir)
        scrivi(o.dir, riga)
        return 0 if riga.get("esito") == "MISURATO" else 1
    return campagna(o)


if __name__ == "__main__":
    try:
        sys.exit(main() or 0)
    except KeyboardInterrupt:
        sys.exit(2)
