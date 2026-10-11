#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g8-comune — the helpers of group G8 («the users, the password, the ban»)

    python3 15-g8-comune.py start|stop|unblock|status <desktop>   (called by 15-g8-server.sh)

What is here (imported by 15-f025, 15-f026, 15-f027, 15-n027 with
`suite._carica`, not copied):

  MyServer     ⭐ the SECOND product server inside a box: same
                binary /opt/remotix/remotix, systemd unit `rete15-g8`, port
                862x, and ITS OWN ban-file, command socket, survey and log in
                /var/lib/rete15-g8/.  ⛔ It serves everything that gets the
                password wrong: three errors ban 192.168.0.2 for 12 hours, and on the box's
                server (8511-8514) they would stop everybody.  The ban is in
                the PROCESS's memory and in ITS file: the 85xx's does not see it.
  scena_colore  a `firefox-esr --kiosk` window in the tenant's session,
                all of a known COLOUR, with a focused text field; a small
                server writes down in the tenant's home every key and every
                value of the field (the suite's «value of a field»), and serves the
                colour from a file — changing that file changes the scene (the fault).
  frazioni      how much of the photo is of each known colour.
  ferma/riprendi  SIGSTOP/SIGCONT to a browser's process tree: the
                client stays «attached» but IS SILENT — the ghost of §5.1.
  read_page  outcome, class, ban, notice of the page, without touching it.
"""
import base64
import copy
import io
import json
import os
import re
import signal
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import suite as S                                                     # noqa: E402

C23 = S._load("c23_g8", os.path.join(S.BENCHES, "11-scatole",
                                       "11-c23-maiusc-e-frecce-selezionano.py"))

# ⛔ The ports of group G8 — only these (common mandate).
MY_PORTS = {"gnome": 8621, "kde": 8622, "xfce": 8623, "lxqt": 8624}
BASE_BROWSER = {"gnome": 4900, "kde": 4910, "xfce": 4920, "lxqt": 4930}
# the second and the third browser of the same type: base+50 and base+54
MOVE_BROWSER = (0, 50, 54)
# the scene's server: base+5+i (Firefox N, Chrome N+1, Android N+2 belong to the browsers)
MOVE_SCENE = 5
UNITA = "rete15-g8"
DIR = "/var/lib/rete15-g8"
LOG = DIR + "/registro.log"
BAN = DIR + "/ban"
SOCK = DIR + "/command.sock"
BAN_85XX = "/var/lib/rete11/ban"
ADDRESS = "192.168.0.2"

# The page's sentences (src/pagina.html, `REASON_TEXT`), by substring.
SENTENCE = {
    0x07: "incorrect username or password",
    0x08: "attempts from this address are used up",
    0x0F: "taken by another client",
}
# ⚠ The refusals that are NOT the thing tested: under load (10 agents, load
#   ~50) the handshake times out (0x0D) or the browser's codec probe does not
#   make it in time (0x09).  With the box's server we retry; never with the
#   G8 server after a wrong password (it might count).
ENVIRONMENT = ("timed out during the handshake",
            "have nothing in common to speak", "Cannot connect")


def inside(sc, line, seconds=90):
    """`Box.dentro` without sshpw's «password:» line."""
    c, t = sc.inside(line, seconds)
    t = "\n".join(x for x in (t or "").splitlines() if "'s password:" not in x)
    return c, t


# ═══════════════════════════════════════════════════════════════════════════
#  MY SERVER
# ═══════════════════════════════════════════════════════════════════════════
class MyServer:
    def __init__(self, desktop, sc=None):
        self.desktop = desktop
        self.port = MY_PORTS[desktop]
        self.sc = sc or S.C20V.Box(desktop)

    def startup_command(self):
        return (
            "mkdir -p %(d)s; systemctl stop %(u)s 2>/dev/null; "
            "systemctl reset-failed %(u)s 2>/dev/null; "
            "echo \"=== startup $(date -u +%%FT%%TZ) ===\" >> %(r)s; "
            "systemd-run --unit=%(u)s --working-directory=/opt/remotix "
            "--property=StandardOutput=append:%(r)s --property=StandardError=append:%(r)s "
            "--property=KillMode=mixed /opt/remotix/remotix --address 0.0.0.0 "
            "--name 127.0.0.1 --port %(p)d --certificates %(d)s/certificati "
            "--page /opt/remotix/pagina.html --ban-file %(b)s --command-socket %(s)s "
            "--survey %(d)s/rilievo --verbose >/dev/null 2>&1; "
            % {"d": DIR, "u": UNITA, "r": LOG, "p": self.port, "b": BAN, "s": SOCK})

    def turn_on(self, cap=30):
        """(True, lines) when the log says «ready: https» AFTER the startup."""
        n0 = self.log_line_list() or 0
        c, t = inside(self.sc, self.startup_command() + "echo acceso", 60)
        if c != 0:
            return False, "systemd-run: %s" % t[-300:]
        fine = time.time() + cap
        while time.time() < fine:
            _c, t = inside(self.sc, "tail -n +%d %s | grep -a -m1 'ready: https'"
                                   % (n0 + 1, LOG), 30)
            if "ready: https" in (t or ""):
                return True, t.strip()
            time.sleep(1)
        _c, t = inside(self.sc, "tail -n 8 %s" % LOG, 30)
        return False, "did not say «ready» in %d s: %s" % (cap, t[-400:])

    def turn_off(self):
        c, t = inside(self.sc, "systemctl stop %s 2>&1; systemctl reset-failed %s 2>/dev/null; "
                              "systemctl is-active %s; true" % (UNITA, UNITA, UNITA), 60)
        return c == 0, t.strip()

    def is_on(self):
        c, t = inside(self.sc, "systemctl is-active %s" % UNITA, 30)
        return (t or "").strip().endswith("active") and "inactive" not in (t or "")

    def speaks(self, line):
        """A line on the command socket (src/comando.c): PING, UNBLOCK <ind>."""
        prog = ("import socket,sys; s=socket.socket(socket.AF_UNIX); s.settimeout(5); "
                "s.connect(%r); s.sendall(%r.encode()); print(s.recv(300).decode().strip())"
                % (SOCK, line + "\n"))
        c, t = inside(self.sc, "python3 -c %s" % S._q(prog), 30)
        return (t or "").strip()

    def unblock(self, address=ADDRESS):
        return self.speaks("UNBLOCK %s" % address)

    def log_line_list(self):
        _c, t = inside(self.sc, "wc -l < %s 2>/dev/null || echo 0" % LOG, 30)
        try:
            return int(t.split()[-1])
        except (ValueError, IndexError, AttributeError):
            return None

    def log_from(self, sign, pattern=None):
        cmd = "tail -n +%d %s" % ((sign or 0) + 1, LOG)
        if pattern:
            cmd += " | grep -a -- %s" % S._q(pattern)
        _c, t = inside(self.sc, cmd, 60)
        return (t or "").splitlines()

    def file_ban(self, which=BAN):
        _c, t = inside(self.sc, "cat %s 2>/dev/null; true" % which, 30)
        return (t or "").strip()


# ═══════════════════════════════════════════════════════════════════════════
#  THE SCENE OF A COLOUR, with the text field and the notebook
# ═══════════════════════════════════════════════════════════════════════════
SCENE_PAGE = """<!doctype html><meta charset=utf-8><title>REMOTIX G8</title>
<style>
 html,body{margin:0;height:100%;overflow:hidden;background:rgb(__C__)}
 #f{position:fixed;left:15vw;top:40vh;width:70vw;height:14vh;font:10vh/1 monospace;
    border:0;padding:0 1vw;box-sizing:border-box;background:#fff;color:#000;outline:0}
</style>
<input id=f autocomplete=off spellcheck=false>
<script>
const f=document.getElementById('f');
const m=(t)=>fetch('/l',{method:'POST',body:t}).catch(()=>0);
f.focus(); m('caricata');
addEventListener('keydown',e=>m('K '+e.key));
f.addEventListener('input',()=>m('V '+JSON.stringify(f.value)));
let ult='';
setInterval(()=>{ if(document.activeElement!==f) f.focus();
  fetch('/c').then(r=>r.text()).then(c=>{c=c.trim(); if(c&&c!==ult){ult=c;
    document.body.style.background='rgb('+c+')'; m('C '+c);}}).catch(()=>0); },400);
</script>"""

SERVER = r'''
import http.server, sys
PAG = open(sys.argv[2], "rb").read()
LOG, COL = sys.argv[3], sys.argv[4]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        corpo = PAG
        if self.path.startswith("/c"):
            try: corpo = open(COL, "rb").read()
            except Exception: corpo = b""
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(corpo)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        t = self.rfile.read(n).decode("utf-8", "replace")
        with open(LOG, "a") as f: f.write(t + "\n")
        self.send_response(204); self.end_headers()
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
'''


def rgb(c):
    return "%d,%d,%d" % tuple(c)


def turn_on_scene(sc, chi, port, color, wait=45):
    """Server + `firefox-esr --kiosk` in the session of `chi`; waits for «caricata»."""
    b = lambda s: base64.b64encode(s.encode()).decode()     # noqa: E731
    page_map = SCENE_PAGE.replace("__C__", rgb(color))
    c, t = inside(sc, 
        "set -e; h=/home/{c}; mkdir -p $h/.g8-profilo; "
        "echo {srv} | base64 -d > $h/g8-servitore.py; echo {pag} | base64 -d > $h/g8.html; "
        "echo {pref} | base64 -d > $h/.g8-profilo/user.js; : > $h/g8.log; "
        "echo {col} > $h/g8-colore; "
        "chown -R {c}: $h/.g8-profilo $h/g8-servitore.py $h/g8.html $h/g8.log $h/g8-colore; "
        "set +e; u=$(id -u {c}); "
        "pkill -f 'python3 /home/[^ ]*/g8-servitore[.]py {p} ' 2>/dev/null; sleep 0.3; "
        "setsid runuser -u {c} -- python3 $h/g8-servitore.py {p} $h/g8.html $h/g8.log "
        "$h/g8-colore </dev/null >$h/.g8-servitore.log 2>&1 & "
        "for i in $(seq 1 20); do grep -q {c} /proc/$(ss -ltnpH 'sport = :{p}' | "
        "sed -n 's/.*pid=\\([0-9]*\\).*/\\1/p' | head -1)/cmdline 2>/dev/null && break; sleep 0.3; done; "
        "d=''; for i in $(seq 1 40); do d=$(ls /run/user/$u 2>/dev/null | "
        "grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] && break; sleep 0.5; done; "
        "[ -n \"$d\" ] || {{ echo 'no wayland socket'; exit 2; }}; sleep 1; "
        "setsid runuser -u {c} -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=$h firefox-esr --no-remote --new-instance "
        "--profile $h/.g8-profilo --kiosk http://127.0.0.1:{p}/ "
        "</dev/null >$h/.g8-firefox.log 2>&1 & "
        "for i in $(seq 1 {n}); do grep -q caricata $h/g8.log && {{ echo accesa; exit 0; }}; "
        "sleep 0.5; done; echo 'the scene did not say «caricata»'; tail -n 5 $h/.g8-firefox.log; "
        "echo '-- server:'; ss -ltn | grep ':{p} ' ; pgrep -a -u {c} | cut -c1-150 | tail -n 8; "
        "exit 1".format(c=chi, p=port, srv=b(SERVER), page_map=b(page_map),
                        pref=b(S.C21.PREFERENCES), clr=rgb(color), n=wait * 2), wait + 60)
    return c == 0, t


def change_color(sc, chi, color):
    c, t = inside(sc, "echo %s > /home/%s/g8-colore" % (rgb(color), chi), 30)
    return c == 0


def notebook(sc, chi):
    _c, t = inside(sc, "cat /home/%s/g8.log 2>/dev/null" % chi, 30)
    return [r for r in (t or "").splitlines() if r.strip()]


def value(lines):
    """The last value of the field written down (or "" if never written)."""
    v = ""
    for r in lines:
        if r.startswith("V "):
            try:
                v = json.loads(r[2:])
            except ValueError:
                pass
    return v


def keys(lines):
    return [r[2:] for r in lines if r.startswith("K ")]


# ═══════════════════════════════════════════════════════════════════════════
#  THE PHOTOS
# ═══════════════════════════════════════════════════════════════════════════
def fractions(png, colors, toll=60, reduce=8):
    """{name: fraction of the pixels close to that colour} — or None."""
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(png)).convert("RGB")
    except Exception:                            # noqa: BLE001
        return None
    w, h = im.size
    im = im.resize((max(1, w // reduce), max(1, h // reduce)), Image.NEAREST)
    px = list(im.getdata())
    n = float(len(px)) or 1.0
    report = {}
    for name, c in colors.items():
        k = 0
        for p in px:
            if abs(p[0] - c[0]) <= toll and abs(p[1] - c[1]) <= toll and abs(p[2] - c[2]) <= toll:
                k += 1
        report[name] = k / n
    return report


def wait_color(s, photo_name, colors, wanted, threshold=0.5, cap=40):
    """Photographs until the colour `wanted` covers `threshold` or the cap expires; the
    photo that decides is SAVED in the evidence.
    Returns (fractions or None, path of the photo, reason)."""
    fine = time.time() + cap
    fr, why = None, "no photo"
    while True:
        png, why = _quiet_photo(s)
        if png:
            fr = fractions(png, colors)
            if fr and fr.get(wanted, 0) >= threshold:
                break
        if time.time() >= fine:
            break
        time.sleep(1.5)
    png, dove = s.photo(photo_name)
    if png:
        fr = fractions(png, colors)
        return fr, dove, ""
    return fr, "", dove


def _quiet_photo(s):
    """A photo that is NOT saved (the attempts of the wait)."""
    try:
        png = S.C21.full_photo(s.g)
    except Exception as e:                       # noqa: BLE001
        return None, "photo failed: %s" % str(e)[:200]
    return (png, "") if png else (None, "the canvas cannot be photographed")


def fr_text(fr):
    if not fr:
        return "(no measurement)"
    return ", ".join("%s %.1f%%" % (k, 100 * v) for k, v in fr.items())


# ═══════════════════════════════════════════════════════════════════════════
#  THE BROWSERS: a second and a third of the same type, the ghost
# ═══════════════════════════════════════════════════════════════════════════
def o_per(o, i):
    """A copy of the options for browser number `i` (0, 1, 2)."""
    o2 = copy.copy(o)
    o2.base_port = o.base_port + MOVE_BROWSER[i]
    if o.evidence:
        o2.evidence = os.path.join(o.evidence, "browser%d" % i) if i else o.evidence
        os.makedirs(o2.evidence, exist_ok=True)
    return o2


def _children():
    fig = {}
    for v in os.listdir("/proc"):
        if not v.isdigit():
            continue
        try:
            with open("/proc/%s/stat" % v) as f:
                st = f.read()
            ppid = int(st[st.rindex(")") + 2:].split()[1])
        except (OSError, ValueError, IndexError):
            continue
        fig.setdefault(ppid, []).append(int(v))
    return fig


def tree(pid):
    fig = _children()
    all_items, queue = [], [pid]
    while queue:
        p = queue.pop()
        all_items.append(p)
        queue.extend(fig.get(p, []))
    return all_items


def _cmdline(pid):
    try:
        with open("/proc/%d/cmdline" % pid, "rb") as f:
            return f.read().replace(b"\0", b" ").decode("utf-8", "replace")
    except OSError:
        return ""


def halt(g, stop=True):
    """⛔ The GHOST: the client stays attached for the server but no longer sends
    a packet.  SIGSTOP (or SIGCONT) —
      Chrome   to the network service only (`network.mojom.NetworkService`, where
               QUIC lives): the browser and CDP stay alive, the page too;
      Firefox  to the WHOLE tree (the network is in the parent process or in the
               «socket» one); Marionette resumes after the SIGCONT.
    Returns how many processes."""
    p = getattr(g, "p", None)
    if p is None:
        return 0
    pids = tree(p.pid)
    if hasattr(g, "cdp"):
        network = [q for q in pids if "NetworkService" in _cmdline(q)]
        if network:
            pids = network
    for q in pids:
        try:
            os.kill(q, signal.SIGSTOP if stop else signal.SIGCONT)
        except OSError:
            pass
    return len(pids)


def resume(g):
    return halt(g, False)


def nudge(s, times=3):
    """A real user's sign of life: the pointer moves on the canvas."""
    try:
        geo = s.geometry()
        for k in range(times):
            x, y = S.C21.desktop_to_glass(geo, geo["tl"] * (0.3 + 0.1 * k),
                                              geo["ta"] * 0.2)
            s.g.move_to(x, y)
            time.sleep(0.2)
        return True
    except Exception:                            # noqa: BLE001
        return False


def click_center(s, fy=0.47):
    geo = s.geometry()
    x, y = S.C21.desktop_to_glass(geo, geo["tl"] * 0.5, geo["ta"] * fy)
    s.g.click(x, y)


JS_PAGE = r"""
const e = document.getElementById('outcome'), m = document.getElementById('signin-form');
const a = document.getElementById('warning');
const vis = (x) => !!x && getComputedStyle(x).display !== 'none' && x.getBoundingClientRect().width > 0;
const R = window.REMOTIX, s = R && R.viewer;
return { url: location.href, outcome: e ? e.textContent : null, class: e ? e.className : null,
         form: vis(m), session: !!(s && s.session),
         banned: document.body ? (document.body.dataset.banned || null) : null,
         warning: a ? a.textContent : '',
         hours: (document.getElementById('hours') || {}).textContent || null,
         minutes: (document.getElementById('minutes') || {}).textContent || null,
         text: document.body ? document.body.innerText.slice(0, 400) : '' };
"""


def read_page(g):
    try:
        return g.js(JS_PAGE) or {}
    except Exception as e:                       # noqa: BLE001
        return {"error": str(e)[:200]}


def load(g, url, wait=20):
    """Opens `url` and waits for the complete document; returns read_page()."""
    ok, why = g.navigate(url)
    fine = time.time() + wait
    p = {}
    while time.time() < fine:
        try:
            if g.js("return document.readyState") == "complete":
                break
        except Exception:                        # noqa: BLE001
            pass
        time.sleep(0.4)
    p = read_page(g)
    if not ok:
        p["non_aperta"] = why
    return p


def try_hard(s, user, password, cap=30, times=3):
    """`try_login`, retrying when the refusal is the ENVIRONMENT's (see `ENVIRONMENT`).
    Returns (admitted, state, [environment refusals seen])."""
    seen_items = []
    for _ in range(times):
        adm, st = try_login(s, user, password, cap)
        e = (st or {}).get("outcome") or ""
        if adm is False and any(a in e for a in ENVIRONMENT):
            seen_items.append(e[:80])
            time.sleep(2)
            continue
        return adm, st, seen_items
    return None, st, seen_items


def try_without_reload(s, user, password, cap=30):
    return try_login(s, user, password, cap, reload=False)


def try_login(s, user, password, cap=30, reload=True):
    """Reloads the page, sends user and password, and waits for a verdict.
    Returns (admitted: True/False/None, state of the page)."""
    if reload:
        s.pr.do_open()
    old = s.o.user
    s.o.user = user
    try:
        r = s.g.js(S.VERI.JS_ENTER, user, password)
    finally:
        s.o.user = old
    if r != "mandato":
        return None, {"outcome": "I could not fill in the form: %s" % r}
    fine = time.time() + cap
    st = {}
    while time.time() < fine:
        st = s.state()
        if st.get("session") and st.get("outcome_class") == "good" \
                and (st.get("outcome") or "").startswith("Admitted"):
            return True, st
        if st.get("outcome_class") == "bad" and st.get("outcome") \
                and "Collego" not in (st.get("outcome") or ""):
            return False, st
        time.sleep(0.4)
    return None, st


# ═══════════════════════════════════════════════════════════════════════════
#  THE COMMAND LINE (for 15-g8-server.sh)
# ═══════════════════════════════════════════════════════════════════════════
def main():
    if len(sys.argv) < 3 or sys.argv[1] not in ("start", "stop", "unblock", "status") \
            or sys.argv[2] not in MY_PORTS:
        print(__doc__)
        return 2
    what, d = sys.argv[1], sys.argv[2]
    m = MyServer(d)
    if what == "start":
        ok, t = m.turn_on()
        print(("⭐ on %s at %d: %s" if ok else "⛔ %s %d NOT on: %s")
              % (d, m.port, t))
        return 0 if ok else 1
    if what == "stop":
        ok, t = m.turn_off()
        print("stopped %s (%s)" % (d, t.splitlines()[-1] if t else "?"))
        return 0
    if what == "unblock":
        print(m.unblock(sys.argv[3] if len(sys.argv) > 3 else ADDRESS))
        return 0
    print("unit: %s · PING: %s · ban: «%s» · ban of the 85xx: «%s»"
          % ("active" if m.is_on() else "NOT active", m.speaks("PING"), m.file_ban(),
             m.file_ban(BAN_85XX)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
