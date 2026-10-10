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


def _parola_sudo():
    """The server's sudo password: from REMOTIX_PAROLA_SUDO, or from the «pass:» line of
    ~/SERVER.ssh (the same file as fondamenta/strumenti/sshpw.py). ⛔ Never written
    in the benches: they are in the repository."""
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

QUI = os.path.dirname(os.path.abspath(__file__))
SERVER_SH = os.path.join(QUI, "15-g7-server.sh")
PORTE_G7 = {"gnome": 8611, "kde": 8612, "xfce": 8613, "lxqt": 8614}
DIR_G7 = "/var/lib/rete15-g7"
REGISTRO_G7 = DIR_G7 + "/registro.log"


def sudo(argv, secondi=60, entrata=""):
    """(code, output) of `argv` with sudo, on the server (local)."""
    try:
        r = subprocess.run(["sudo", "-S", "-p", ""] + list(argv),
                           input=_parola_sudo() + entrata, capture_output=True,
                           text=True, errors="replace", timeout=secondi)
    except subprocess.TimeoutExpired:
        return None, "(no answer in %d s)" % secondi
    return r.returncode, (r.stdout + r.stderr).strip()


def dentro(desktop, riga, secondi=60):
    """(code, output) of `riga` as root in the box rete11-<desktop>."""
    return sudo(["podman", "exec", "rete11-%s" % desktop, "sh", "-c", riga], secondi)


# ═══════════════════════════════════════════════════════════════════════════
#  OUR SERVER
# ═══════════════════════════════════════════════════════════════════════════
def server(azione, desktop, *opzioni, secondi=90):
    try:
        r = subprocess.run(["bash", SERVER_SH, azione, desktop] + list(opzioni),
                           capture_output=True, text=True, errors="replace",
                           timeout=secondi)
    except subprocess.TimeoutExpired:
        return False, "(15-g7-server.sh %s: no answer in %d s)" % (azione, secondi)
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def orologi_in_vigore(desktop):
    """The startup line with the three clocks of §5.3: (inattivita_s, abbandono_s, line)."""
    _c, t = dentro(desktop, "grep -a '§5.3, the three clocks' %s | tail -n 1" % REGISTRO_G7)
    m1 = re.search(r"user inactivity (\d+) s", t or "")
    m2 = re.search(r"session abandonment (\d+) s", t or "")
    return (int(m1.group(1)) if m1 else None, int(m2.group(1)) if m2 else None,
            (t or "").strip())


class Registro:
    """OUR server's log, with the same form as Scatola."""

    def __init__(self, desktop, percorso=REGISTRO_G7):
        self.d, self.p = desktop, percorso

    def righe(self):
        _c, t = dentro(self.d, "wc -l < %s" % self.p, 30)
        try:
            return int(t.split()[-1])
        except (ValueError, IndexError, AttributeError):
            return None

    def da(self, segno, chi=None):
        filtro = (" | grep -a -- '%s'" % chi) if chi else ""
        _c, t = dentro(self.d, "tail -n +%d %s%s" % ((segno or 0) + 1, self.p, filtro), 60)
        return (t or "").splitlines()

    def aspetta(self, segno, forme, chi=None, tetto=60, passo=1.0):
        """(form, line, seconds) of the first line with one of the `forme`."""
        t0 = time.time()
        while time.time() - t0 < tetto:
            for r in self.da(segno, chi):
                for f in forme:
                    if f in r:
                        return f, r, time.time() - t0
            time.sleep(passo)
        return None, None, time.time() - t0


# ═══════════════════════════════════════════════════════════════════════════
#  THE DEAD LINE — nftables on the server, ONLY our port
# ═══════════════════════════════════════════════════════════════════════════
class LineaMorta:
    """
        with LineaMorta(8611) as lm:   # from here no UDP from/to 8611
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

    def __init__(self, porta):
        self.porta = int(porta)
        assert 8600 <= self.porta <= 8699, "only our server's ports"
        self.tabella = "remotix_g7_%d" % self.porta
        self.messa = None

    def regole(self):
        p = self.porta
        return ("table inet %(t)s {\n"
                " chain dentro { type filter hook input priority -10; policy accept;\n"
                "  udp dport %(p)d counter drop\n  udp sport %(p)d counter drop\n }\n"
                " chain fuori { type filter hook output priority -10; policy accept;\n"
                "  udp dport %(p)d counter drop\n  udp sport %(p)d counter drop\n }\n"
                "}\n" % {"t": self.tabella, "p": p})

    def togli(self):
        sudo(["/usr/sbin/nft", "delete", "table", "inet", self.tabella], 30)
        c, t = sudo(["/usr/sbin/nft", "list", "tables"], 30)
        return self.tabella not in (t or "")

    def metti(self):
        self.togli()                              # a leftover from a round that fell over
        # ⚠ From a FILE, not from stdin: with sudo already authenticated the password is not
        #   consumed and would end up inside the rules (`[M]` «syntax error … nicfio»).
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".nft", delete=False) as f:
            f.write(self.regole())
        try:
            c, t = sudo(["/usr/sbin/nft", "-f", f.name], 30)
        finally:
            os.unlink(f.name)
        if c != 0:
            raise RuntimeError("nft did not put the rule: %s" % t[-200:])
        self.messa = time.time()
        return True

    def contati(self):
        """The dropped packets (witness that the rule BITES)."""
        _c, t = sudo(["/usr/sbin/nft", "list", "table", "inet", self.tabella], 30)
        return sum(int(x) for x in re.findall(r"packets (\d+)", t or ""))

    def __enter__(self):
        self.metti()
        return self

    def __exit__(self, *a):
        tolta = self.togli()
        if not tolta:
            print("   ⛔ THE nft RULE %s CANNOT BE REMOVED" % self.tabella, flush=True)
        return False


# ═══════════════════════════════════════════════════════════════════════════
#  THE PAGE
# ═══════════════════════════════════════════════════════════════════════════
JS_PAGINA = r"""
const e = document.getElementById('esito');
const m = document.getElementById('modulo');
const reg = document.getElementById('registro');
const vis = (x) => !!x && getComputedStyle(x).display !== 'none'
                  && getComputedStyle(x).visibility !== 'hidden'
                  && x.getBoundingClientRect().width > 0;
const R = window.REMOTIX, s = R && R.schermo;
const righe = reg ? reg.textContent.split('\n') : [];
return {
  esito: e ? e.textContent : null,
  esito_classe: e ? e.className : null,
  esito_visibile: vis(e) && !!(e && e.textContent.trim()),
  modulo_visibile: vis(m),
  vestita: document.body ? (document.body.dataset.schermo || null) : null,
  sessione: !!(s && s.sessione),
  input: !!window.REMOTIX_INPUT,
  dipinti: s && s.conti ? s.conti.dipinti : null,
  coda: righe.filter(r => r.indexOf('audio:') !== 0).slice(-14),
  n_righe: righe.length,
  testo: document.body ? document.body.innerText.slice(0, 400) : ''
};
"""


def pagina(g):
    try:
        return g.js(JS_PAGINA) or {}
    except Exception as e:                       # noqa: BLE001
        return {"errore": str(e)[:200]}


def la_pagina_lo_dice(st):
    """⭐ The page TELLS the user that the wire dropped: a visible sentence
    in the outcome line, or the sign-in form back in view (and the
    desktop dress removed).  ⛔ The hidden log (`#registro`, off
    by default) is not «telling»: the user does not see it."""
    if not isinstance(st, dict) or st.get("errore"):
        return None
    if st.get("esito_visibile") and st.get("esito_classe") == "male":
        return True
    if st.get("modulo_visibile") and not st.get("vestita"):
        return True
    return False


# ═══════════════════════════════════════════════════════════════════════════
#  THE BROWSER: stopping it and restarting it (the whole process tree)
# ═══════════════════════════════════════════════════════════════════════════
def discendenti(pid):
    figli = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open("/proc/%s/stat" % d) as f:
                st = f.read()
            pp = int(st.rsplit(")", 1)[1].split()[1])
        except Exception:                        # noqa: BLE001
            continue
        figli.setdefault(pp, []).append(int(d))
    tutti, coda = [], [pid]
    while coda:
        p = coda.pop()
        tutti.append(p)
        coda.extend(figli.get(p, []))
    return tutti


def pid_browser(g):
    p = getattr(g, "p", None)
    return getattr(p, "pid", None)


def segnale_albero(g, sig):
    pid = pid_browser(g)
    if not pid:
        return []
    fatti = []
    for p in discendenti(pid):
        try:
            os.kill(p, sig)
            fatti.append(p)
        except ProcessLookupError:
            pass
    return fatti


def ferma_browser(g):
    return segnale_albero(g, signal.SIGSTOP)


def riprendi_browser(g):
    return segnale_albero(g, signal.SIGCONT)


# ═══════════════════════════════════════════════════════════════════════════
#  THE TENANT IN THE BOX
# ═══════════════════════════════════════════════════════════════════════════
def processi_inquilino(desktop, chi):
    """{pid: command} of the tenant's processes (empty = the session is not there)."""
    _c, t = dentro(desktop, "ps -u %s -o pid=,comm= 2>/dev/null" % chi, 30)
    ps = {}
    for r in (t or "").splitlines():
        a = r.split(None, 1)
        if len(a) == 2 and a[0].isdigit():
            ps[int(a[0])] = a[1].strip()
    return ps


def nella_sessione(s, comando, secondi=60):
    """Like `Sessione.nella_sessione(fondo=True)`, but from here (local sudo on the
    server) instead of over ssh: `[M]` 24 Sep, with ten agents together the bench's
    ssh to the server itself drops («Connection closed … port 22»)."""
    chi = s.chi
    amb = ("u=$(id -u %(c)s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
           "| head -1); [ -n \"$d\" ] || { echo 'no wayland socket'; exit 2; }; "
           % {"c": chi})
    corpo = ("runuser -u %(c)s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
             "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
             "XDG_SESSION_TYPE=wayland HOME=/home/%(c)s sh -c %(q)s"
             % {"c": chi, "q": S_q(comando)})
    corpo = "setsid %s < /dev/null > /home/%s/.g7-%s.log 2>&1 & echo launched" % (
        corpo, chi, re.sub(r"\W", "", comando.split()[0])[:20])
    return dentro(s.o.scatola, amb + corpo, secondi)


def S_q(x):
    return "'" + x.replace("'", "'\"'\"'") + "'"


def lancia_scena(s, S=None, cosa="scena"):
    """The MOVING SCENE inside the session: `weston-simple-egl -f` — the
    spinning triangle, full screen, drawn by the card (EGL) and native
    Wayland: it is in all four boxes.
    ⛔ Not C3's scene in firefox-esr: `[M]` 24 Sep 2026 on GNOME, firefox-esr
       launched this way does not write a byte in the profile and opens «Your Firefox profile
       cannot be loaded» (even with the profile prepared like C21, even headless
       with a test user) ⇒ the scene never appeared.
    Returns (pid | None, text)."""
    c, t = nella_sessione(s, "weston-simple-egl -f", 60)
    for _ in range(40):
        ps = processi_inquilino(s.o.scatola, s.chi)
        f = [p for p, n in ps.items() if n.startswith("weston-simple")]
        if f:
            return min(f), "weston-simple-egl of the %s: pid %d" % (cosa, min(f))
        time.sleep(0.5)
    return None, "weston-simple-egl was not seen starting: %s" % (t or "")[-200:]


def lancia_tono(s, secondi=600):
    """pw-play of a 440 Hz wave on the product's «remotix» sink, in a loop."""
    corpo = ("python3 -c \"import math,struct,wave;w=wave.open('/tmp/g7-onda-%(c)s.wav','wb');"
             "w.setnchannels(2);w.setsampwidth(2);w.setframerate(48000);"
             "w.writeframes(b''.join(struct.pack('<hh',int(16000*math.sin(2*math.pi*440*i/48000)),"
             "int(16000*math.sin(2*math.pi*440*i/48000))) for i in range(48000*5)));w.close()\" "
             "&& end=$(( $(date +%%s) + %(s)d )); while [ $(date +%%s) -lt $end ]; do "
             "pw-play --target=remotix /tmp/g7-onda-%(c)s.wav; done"
             % {"c": s.chi, "s": secondi})
    return nella_sessione(s, corpo, 60)


# ⭐ THE EAR: the page's `AudioBufferSourceNode.start` is wrapped, and for
#   every buffer the page really sends to the output the RMS of the
#   SAMPLES is measured (blocks are not counted: a stream of zeros is blocks that
#   arrive and it is silence).  It is put after loading, before the login:
#   the page creates the sources only with the session open.
JS_ORECCHIO = r"""
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

JS_ASCOLTA = r"""
const O = window.__G7_ORECCHIO__;
if (!O) return null;
const da = arguments[0], a = arguments[1];
let q = 0, c = 0, n = 0;
for (const f of O.finestre) if (f.t >= da && f.t < a) { q += f.q; c += f.c; n += f.n; }
return { rms: c ? Math.sqrt(q / c) : null, campioni: c, buffer: n,
         adesso: Math.floor(performance.now() / 1000) };
"""

SOGLIA_RMS = 0.01      # the wave is 16000/32767 ≈ 0.49 peak ⇒ RMS ≈ 0.35


def orecchio(g):
    try:
        return g.js(JS_ORECCHIO)
    except Exception as e:                       # noqa: BLE001
        return "not put: %s" % str(e)[:120]


def ascolta(g, secondi):
    """(rms | None, details) over the last `secondi` of sound PLAYED by the page."""
    try:
        ora = g.js("return Math.floor(performance.now() / 1000);")
        r = g.js(JS_ASCOLTA, ora - secondi, ora + 1)
    except Exception as e:                       # noqa: BLE001
        return None, "ear unreadable: %s" % str(e)[:120]
    if not r:
        return None, "the ear is not on the page"
    return r.get("rms"), r


# ═══════════════════════════════════════════════════════════════════════════
#  THE PHOTOS: does the scene move?
# ═══════════════════════════════════════════════════════════════════════════
def diversita(png_a, png_b):
    """Fraction of pixels that change (|Δ| > 40 on a channel) between two photos,
    at reduced scale.  None if they cannot be compared."""
    try:
        import io
        from PIL import Image, ImageChops
        a = Image.open(io.BytesIO(png_a)).convert("RGB").resize((320, 180))
        b = Image.open(io.BytesIO(png_b)).convert("RGB").resize((320, 180))
        d = ImageChops.difference(a, b).getdata()
        cambiati = sum(1 for p in d if max(p) > 40)
        return cambiati / float(len(d))
    except Exception:                            # noqa: BLE001
        return None


def colori_scena(png):
    """Share of blue (#0000FF) and yellow (#FFFF00) pixels of C3's scene."""
    try:
        import io
        from PIL import Image
        im = Image.open(io.BytesIO(png)).convert("RGB").resize((320, 180))
        px = list(im.getdata())
        blu = sum(1 for r, g_, b in px if b > 180 and r < 80 and g_ < 80)
        gia = sum(1 for r, g_, b in px if r > 180 and g_ > 180 and b < 80)
        return blu / float(len(px)), gia / float(len(px))
    except Exception:                            # noqa: BLE001
        return None, None


def aspetta_scena(s, S, tetto=40):
    """(True | None, description): the moving scene in view within
    `tetto` — two photos 0.7 s apart differing by > 2 % of the pixels."""
    t0 = time.time()
    desc = ""
    prima = None
    while time.time() - t0 < tetto:
        try:
            png = S.C21.foto_piena(s.g)
        except Exception as e:                   # noqa: BLE001
            png, desc = None, str(e)[:120]
        if png and prima:
            d = diversita(prima, png)
            desc = "change %.1f%%" % (100 * (d or 0))
            if d and d > 0.02:
                return True, "moving scene after %.0f s (%s)" % (time.time() - t0, desc)
        prima = png
        time.sleep(0.7)
    return None, "the moving scene did not appear in %d s (%s)" % (tetto, desc)


def la_scena_si_muove(s, nome, coppie=3, pausa=None):
    """(True/False/None, description, [paths]) — photos at IRREGULAR pauses,
    and ALL the pairs are compared: at least one different by > 2 % of the pixels.

    ⛔ `[M]` 25 Sep 2026 (D-019, class C): with a fixed pause of 0.7 s plus the
    time of the 4K photo (~0.9 s in all) the photos almost always fell at the
    same point of the turn of weston-simple-egl's triangle (half a turn
    ~0.9 s) ⇒ 0.9-1.6 % change with the scene ALIVE, and a false FAIL."""
    pause = [0.43, 0.61, 0.77, 0.29, 0.53]
    foto, ev = [], []
    for i in range(coppie + 1):
        png, dove = s.foto("%s-%d" % (nome, i))
        if not png:
            return None, "photo failed: %s" % dove, ev
        foto.append(png)
        if dove:
            ev.append(dove)
        time.sleep(pausa if pausa is not None else pause[i % len(pause)])
    diffs = [diversita(foto[i], foto[j]) for i in range(len(foto))
             for j in range(i + 1, len(foto))]
    if any(d is None for d in diffs):
        return None, "photos not comparable", ev
    desc = "changes between photos %s" % ["%.1f%%" % (100 * d) for d in diffs]
    return max(diffs) > 0.02, desc, ev


# ═══════════════════════════════════════════════════════════════════════════
#  ⛔ THE BOX WITHOUT SSH, when running ON THE SERVER
# ═══════════════════════════════════════════════════════════════════════════
def scatola_locale(S):
    """`[M]` 24 Sep 2026, ten agents together: `Scatola.dentro()` goes through
    `sshpw.py` → ssh to the server ITSELF, and sshd cuts off some of them
    («Connection closed by 192.168.0.2 port 22») ⇒ tenants not created,
    BLOCKED that are not the product's.  On the server (REMOTIX_SUL_SERVER=1) the
    same line is executed with local `sudo podman exec`.  ⚠ The class loaded by
    suite.py is changed in THIS process, not suite.py."""
    if os.environ.get("REMOTIX_SUL_SERVER") != "1":
        return False

    def _dentro(self, riga, secondi=90):
        c, t = sudo(["podman", "exec", self.contenitore, "sh", "-c", riga], secondi)
        return c, (t or "").strip()
    S.C20V.Scatola.dentro = _dentro
    return True
