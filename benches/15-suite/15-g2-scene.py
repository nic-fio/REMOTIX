#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g2-scene — THE SCENE AND THE COMMON TOOLS OF GROUP G2 (mouse and keyboard)
    used by 15-f004 (mouse), 15-f007 (special keys), 15-f009 (accents, AltGr).

⭐ THE SCENE: a known page, served by a small `python3` server in the
   tenant's home and opened with `firefox-esr --kiosk` INSIDE the session.
   It has the targets of the gestures:
      pad  BLUE    receives the movement (writes where the pointer touched it)
      bot  GREEN   the left-click button (counts the clicks with button 0)
      box  YELLOW  it is dragged (pointer events + capture)
      par  white   «alfa beta gamma delta»: double click and selection
      a    multi-line text field            (keyboard)
      b    single-line field: Tab gets there, Esc empties it (the application)
      menu MAGENTA the page's context menu, where the right button was pressed
   ⛔ THE SCENE DOES NOT JUDGE: it WRITES the application's state (field values,
     selected text, box position, where the menu is) in a file
     of the tenant.  It is «the value of a field read in the session»: the
     judgment is given by the tests, and the context menu they judge from the PHOTO.
   ⭐ The solid colours serve to FIND the scene in the photo: the
     correspondence between the pixels of the remote page and those of the desktop is
     measured (BLUE and GREEN: four edges per axis), not assumed — the kiosk
     may not cover the panel, the scale may not be 1.

⭐ THE COMMANDS: the server serves `/c` (the content of a file the bench
   writes); the page reads it every 250 ms and, at a new id, executes («reset»:
   empty fields, selection removed, menu hidden, box at home, focus on field a)
   and answers `FATTO <id>`.  ⇒ Between one gesture and the next the scene tidies itself
   up WITHOUT touching the input: so the next gesture inherits nothing.

⭐ THE REAL EVENTS: mouse and keyboard with `WebDriver:PerformActions`
   (Marionette) and `Input.dispatchMouseEvent`/`Input.dispatchKeyEvent` (CDP),
   like C22 and C23.  ⛔ Never written into the wire by hand.
"""
import base64
import io
import contextlib
import json
import os
import signal
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import suite as S                                                     # noqa: E402

C21 = S.C21


# ⚠ `inside()` on the server without ssh and the real `~/.cache`: `suite.py` does them now.

# ⛔ CHROME IN THE COMMON LABWC: the window covered by those of the other agents
#   receives no frames ⇒ `Page.captureScreenshot` stays hung (40 s, 17 min) and
#   `Input.dispatchMouseEvent` answers «Internal error» (`[M]` 25 Sep 2026,
#   kde/xfce/lxqt).  A real user has the browser IN FRONT: the throttling of
#   covered windows is turned off (declared: BENCH flags).
_OPT = os.environ.get("REMOTIX_CHROME_OPTIONS", "")
for _b in ("--disable-backgrounding-occluded-windows", "--disable-renderer-backgrounding",
           "--disable-background-timer-throttling"):
    if _b not in _OPT:
        _OPT += " " + _b
os.environ["REMOTIX_CHROME_OPTIONS"] = _OPT.strip()
BLUE, GREEN_C, YELLOW, MAGENTA = (0, 0, 255), (0, 255, 0), (255, 255, 0), (255, 0, 255)
TOL_COLOR = 70
WORDS = ("alfa", "beta", "gamma", "delta")

# ═══════════════════════════════════════════════════════════════════════════
#  THE PAGE AND THE SERVER
# ═══════════════════════════════════════════════════════════════════════════
PAGE = r"""<!doctype html><meta charset=utf-8><title>REMOTIX G2</title>
<style>
 html,body{margin:0;height:100%;background:#202020;overflow:hidden;font-family:monospace}
 #pad{position:fixed;left:3vw;top:4vh;width:27vw;height:16vh;background:#0000ff}
 #bot{position:fixed;left:36vw;top:4vh;width:24vw;height:16vh;background:#00ff00}
 #box{position:fixed;left:66vw;top:4vh;width:8vw;height:16vh;background:#ffff00;touch-action:none}
 #par{position:fixed;left:3vw;top:26vh;width:94vw;height:14vh;background:#fff;color:#000;
      font:9vh/14vh monospace;white-space:pre;padding-left:2vw;box-sizing:border-box;
      cursor:text}
 #a{position:fixed;left:3vw;top:46vh;width:58vw;height:46vh;font:6vh/1.2 monospace;
    background:#fff;color:#000;border:0;outline:0;resize:none;padding:0;margin:0}
 #b{position:fixed;left:65vw;top:46vh;width:32vw;height:12vh;font:6vh/1 monospace;
    background:#fff;color:#000;border:0;outline:0;padding:0;margin:0}
 #menu{position:fixed;display:none;width:12vw;height:16vh;background:#ff00ff}
</style>
<div id=pad></div><div id=bot></div><div id=box></div>
<div id=par><span id=w1>alfa</span> <span id=w2>beta</span> <span id=w3>gamma</span> <span id=w4>delta</span></div>
<textarea id=a autocomplete=off spellcheck=false></textarea>
<input id=b autocomplete=off spellcheck=false>
<div id=menu></div>
<script>
const $=i=>document.getElementById(i);
const post=t=>fetch('/l',{method:'POST',body:t}).catch(()=>0);
let st, pend=null, ultimo='';
function azzera(){ st={seq:(st?st.seq:0), pad:null, padn:0, clic:0, clicbtn:null, fuori:0,
  menu:null, giu:[], box:[0,0], boxn:0, dbl:0, esc:0, tasti:[]}; }
azzera();
function manda(){ st.seq++; st.sel=String(getSelection()); st.a=$('a').value; st.b=$('b').value;
  st.focus=document.activeElement?document.activeElement.id:''; post('S '+JSON.stringify(st)); }
function presto(){ if(!pend) pend=setTimeout(()=>{pend=null;manda();},80); }
function rett(){ const r={W:innerWidth,H:innerHeight,dpr:devicePixelRatio};
  for(const i of ['pad','bot','box','par','a','b','w1','w2','w3','w4']){
    const q=$(i).getBoundingClientRect(); r[i]=[q.left,q.top,q.right,q.bottom];}
  post('R '+JSON.stringify(r)); }
$('pad').addEventListener('mousemove',e=>{const p=$('pad');
  st.pad=[e.offsetX/p.clientWidth, e.offsetY/p.clientHeight]; st.padn++; presto();});
$('bot').addEventListener('click',e=>{ if(e.button===0){st.clic++;} st.clicbtn=e.button; presto();});
document.addEventListener('click',e=>{ if(e.target.id!=='bot'){st.fuori++; presto();} });
document.addEventListener('mousedown',e=>{ st.giu.push(e.button+'@'+(e.target.id||e.target.tagName));
  if(st.giu.length>12) st.giu.shift(); if(e.button===0) $('menu').style.display='none'; presto();});
document.addEventListener('contextmenu',e=>{ e.preventDefault(); const m=$('menu');
  m.style.left=e.clientX+'px'; m.style.top=e.clientY+'px'; m.style.display='block';
  st.menu=[e.clientX,e.clientY]; presto();});
let tr=null;
$('box').addEventListener('pointerdown',e=>{ if(e.button!==0) return; $('box').setPointerCapture(e.pointerId);
  tr={x:e.clientX,y:e.clientY,bx:st.box[0],by:st.box[1]}; });
$('box').addEventListener('pointermove',e=>{ if(!tr) return; const dx=tr.bx+e.clientX-tr.x, dy=tr.by+e.clientY-tr.y;
  $('box').style.transform='translate('+dx+'px,'+dy+'px)'; st.box=[dx,dy]; });
$('box').addEventListener('pointerup',e=>{ if(!tr) return; tr=null; st.boxn++; presto(); });
document.addEventListener('selectionchange',presto);
document.addEventListener('dblclick',e=>{st.dbl++; presto();});
document.addEventListener('keydown',e=>{ st.tasti.push(e.key+(e.shiftKey?'+S':'')+(e.ctrlKey?'+C':''));
  if(st.tasti.length>40) st.tasti.shift();
  if(e.key==='Escape' && document.activeElement===$('b')){ $('b').value=''; st.esc++; }
  presto();});
$('a').addEventListener('input',presto); $('b').addEventListener('input',presto);
function esegui(c){
  if(c==='reset'){ $('a').value=''; $('b').value=''; getSelection().removeAllRanges();
    $('menu').style.display='none'; $('box').style.transform=''; tr=null; azzera(); $('a').focus(); }
  else if(c==='fuoco-a'){ $('a').focus(); }
}
setInterval(()=>{ fetch('/c',{cache:'no-store'}).then(r=>r.text()).then(t=>{ t=t.trim();
  if(!t || t===ultimo) return; ultimo=t; const sp=t.indexOf(' ');
  esegui(t.slice(sp+1)); rett(); manda(); post('FATTO '+t.slice(0,sp)); }).catch(()=>0); },250);
addEventListener('resize',rett);
rett(); $('a').focus(); manda(); post('caricata');
</script>"""

SERVER = r'''
import http.server, sys
PAG = open(sys.argv[2], "rb").read()
LOG, CMD = sys.argv[3], sys.argv[4]
class H(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith("/c"):
            try:
                t = open(CMD, "rb").read()
            except OSError:
                t = b""
            self.send_response(200); self.send_header("Content-Type", "text/plain")
            self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(t)
            return
        self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers(); self.wfile.write(PAG)
    def do_POST(self):
        n = int(self.headers.get("Content-Length", "0"))
        t = self.rfile.read(n).decode("utf-8", "replace").replace("\n", "\\n")
        with open(LOG, "a") as f: f.write(t + "\n")
        self.send_response(204); self.end_headers()
http.server.ThreadingHTTPServer(("127.0.0.1", int(sys.argv[1])), H).serve_forever()
'''


class Scene:
    """The scene in the session of `s` (a `suite.Sessione`)."""

    def __init__(self, s, port):
        self.s, self.sc, self.chi, self.port = s, s.sc, s.chi, port
        self.h = "/home/%s" % self.chi
        self.n_cmd = 0
        self.rect = None

    def turn_on(self):
        """Server + `firefox-esr --kiosk` in the session; waits for «caricata»."""
        b = lambda x: base64.b64encode(x.encode()).decode()     # noqa: E731
        c, t = self.sc.inside(
            "set -e; h={h}; mkdir -p $h/.g2-profilo; "
            "echo {srv} | base64 -d > $h/g2-servitore.py; echo {page_map} | base64 -d > $h/g2.html; "
            "echo {pref} | base64 -d > $h/.g2-profilo/user.js; : > $h/g2.log; : > $h/g2.cmd; "
            "chown -R {c}: $h/.g2-profilo $h/g2-servitore.py $h/g2.html $h/g2.log $h/g2.cmd; "
            "set +e; u=$(id -u {c}); "
            "pkill -f 'python3 /home/[^ ]*servitore[.]py {p} ' 2>/dev/null; sleep 0.3; "
            "setsid runuser -u {c} -- python3 $h/g2-servitore.py {p} $h/g2.html $h/g2.log "
            "$h/g2.cmd </dev/null >$h/.g2-servitore.log 2>&1 & "
            "d=''; for i in $(seq 1 40); do d=$(ls /run/user/$u 2>/dev/null | "
            "grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] && break; sleep 0.5; done; "
            "[ -n \"$d\" ] || {{ echo 'no wayland socket'; exit 2; }}; sleep 1; "
            "setsid runuser -u {c} -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
            "XDG_SESSION_TYPE=wayland HOME=$h firefox-esr --no-remote --new-instance "
            "--profile $h/.g2-profilo --kiosk http://127.0.0.1:{p}/ "
            "</dev/null >$h/.g2-firefox.log 2>&1 & "
            "for i in $(seq 1 80); do grep -q caricata $h/g2.log && {{ echo accesa; exit 0; }}; "
            "sleep 0.5; done; echo 'the scene did not say «caricata»'; echo \"socket $d\"; tail -n 8 $h/.g2-firefox.log; "
            "tail -n 3 $h/.g2-servitore.log; tail -n 3 $h/g2.log; pgrep -u {c} -a firefox | head -3; exit 1".format(
                h=self.h, c=self.chi, p=self.port, srv=b(SERVER), page_map=b(PAGE),
                pref=b(C21.PREFERENCES)), 90)
        return c == 0, t

    # -- the application's state ---------------------------------------------
    def load(self):
        """(R, S, last FATTO) from the scene's notebook."""
        _c, t = self.sc.inside(
            "f=%s/g2.log; grep -a '^R ' $f | tail -n 1; echo @@; grep -a '^S ' $f | tail -n 1; "
            "echo @@; grep -a '^FATTO ' $f | tail -n 1" % self.h, 30)
        parts = (t or "").split("@@")
        while len(parts) < 3:
            parts.append("")
        r = _json(parts[0].strip()[2:]) if parts[0].strip().startswith("R ") else None
        s = _json(parts[1].strip()[2:]) if parts[1].strip().startswith("S ") else None
        f = parts[2].strip()[6:].strip() if parts[2].strip().startswith("FATTO") else ""
        if r:
            self.rect = r
        return r, s, f

    def in_charge(self, cmd, wait=20.0):
        """Writes the command and waits for `FATTO`.  Returns the state afterwards, or None."""
        self.n_cmd += 1
        ident = "%d-%d" % (int(time.time()), self.n_cmd)
        self.sc.inside("printf '%%s' '%s %s' > %s/g2.cmd" % (ident, cmd, self.h), 30)
        fine = time.time() + wait
        while time.time() < fine:
            time.sleep(0.5)
            r, s, f = self.load()
            if f == ident:
                return s
        return None

    def wait_until(self, referee, wait=5.0, every=0.7):
        """Reads the state again until `referee(stato)` says True or the wait ends.
        Returns the last state read."""
        fine = time.time() + wait
        s = None
        while True:
            _r, s, _f = self.load()
            if s is not None and referee(s):
                return s
            if time.time() >= fine:
                return s
            time.sleep(every)


def _json(t):
    try:
        return json.loads(t)
    except ValueError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  WHERE THE SCENE IS IN THE DESKTOP — from the PHOTO
# ═══════════════════════════════════════════════════════════════════════════
def find_color(im, color, step=4, toll=TOL_COLOR):
    """The box {x0,y0,x1,y1, n, full} of the pixels close to `color` in
    a PIL image, sampling every `step` pixels; None if there are none.
    `full` = fraction of the box covered (a real block is ~1)."""
    w, h = im.size
    pic = im.resize((max(1, w // step), max(1, h // step)))
    pw, ph = pic.size
    data = pic.getdata()
    xs, ys = [], []
    for i, p in enumerate(data):
        if max(abs(p[0] - color[0]), abs(p[1] - color[1]), abs(p[2] - color[2])) <= toll:
            xs.append(i % pw)
            ys.append(i // pw)
    if len(xs) < 4:
        return None
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    area = (x1 - x0 + 1) * (y1 - y0 + 1)
    fx, fy = w / float(pw), h / float(ph)
    return {"x0": x0 * fx, "y0": y0 * fy, "x1": (x1 + 1) * fx, "y1": (y1 + 1) * fy,
            "n": len(xs), "pieno": len(xs) / float(area)}


def fit(pairs):
    """Least squares of y = a*x + b on the pairs [(x, y)]."""
    n = float(len(pairs))
    sx = sum(c[0] for c in pairs)
    sy = sum(c[1] for c in pairs)
    sxx = sum(c[0] * c[0] for c in pairs)
    sxy = sum(c[0] * c[1] for c in pairs)
    den = n * sxx - sx * sx
    if abs(den) < 1e-9:
        return None
    a = (n * sxy - sx * sy) / den
    return a, (sy - a * sx) / n


class Map:
    """CSS pixels of the remote page ⇒ pixels of the remote desktop ⇒ glass."""

    def __init__(self, ax, bx, ay, by, geo):
        self.ax, self.bx, self.ay, self.by, self.geo = ax, bx, ay, by, geo

    def desktop(self, cx, cy):
        return self.ax * cx + self.bx, self.ay * cy + self.by

    def glass(self, cx, cy):
        X, Y = self.desktop(cx, cy)
        return C21.desktop_to_glass(self.geo, X, Y)

    def describe(self):
        return "desktop = %.3f·x%+.0f, %.3f·y%+.0f" % (self.ax, self.bx, self.ay, self.by)


def calibrate(im, geo, rect):
    """⭐ The Mappa, from the edges of BLUE (pad) and GREEN (bot) in the photo and from their
    rectangles declared by the page.  Returns (Mappa | None, why)."""
    pw, ph = im.size
    matches = {}
    for name, clr in (("pad", BLUE), ("bot", GREEN_C)):
        t = find_color(im, clr)
        if not t:
            return None, "the %s block (%s) is not seen in the photo" % (name, clr)
        if t["pieno"] < 0.8:
            return None, ("the colour of %s is scattered (pieno %.2f): the scene does not cover the "
                          "desktop or there is something else of the same colour" % (name, t["pieno"]))
        X0, Y0 = C21.from_photo_to_desktop(geo, pw, ph, t["x0"], t["y0"])
        X1, Y1 = C21.from_photo_to_desktop(geo, pw, ph, t["x1"], t["y1"])
        matches[name] = (X0, Y0, X1, Y1)
    cx, cy = [], []
    for name in ("pad", "bot"):
        r, d = rect[name], matches[name]
        cx += [(r[0], d[0]), (r[2], d[2])]
        cy += [(r[1], d[1]), (r[3], d[3])]
    fx, fy = fit(cx), fit(cy)
    if not fx or not fy:
        return None, "the page⇒desktop correspondence cannot be computed"
    ax, bx = fx
    ay, by = fy
    if not (0.3 < ax < 4 and 0.3 < ay < 4 and abs(ax - ay) / ax < 0.1):
        return None, "absurd correspondence: ax=%.3f ay=%.3f" % (ax, ay)
    # the deviation of the points from the line: if it is large, one of the blocks is cut
    gap = max([abs(ax * x + bx - X) for x, X in cx] + [abs(ay * y + by - Y) for y, Y in cy])
    if gap > 30:
        return None, "the edges do not lie on a line (deviation %.0f desktop px)" % gap
    return Map(ax, bx, ay, by, geo), "deviation %.0f px" % gap


class Cap(Exception):
    """The browser did not answer within the cap."""


@contextlib.contextmanager
def cap(seconds, what):
    """⛔ A cap on a browser call.  `[M]` 25 Sep 2026, lxqt+Chrome
    with the server shared by ten agents: `Page.captureScreenshot` NEVER
    came back (17 minutes), and before that `Input.dispatchMouseEvent` gave «Internal
    error» — the Chrome window in the common labwc covered by those of the
    others no longer receives frames.  The protocol reading does not time out because
    the EVENTS keep arriving ⇒ an alarm is needed."""
    def _on_alarm(_n, _f):
        raise Cap("%s: no answer from the browser in %d s" % (what, seconds))
    old = signal.signal(signal.SIGALRM, _on_alarm)
    signal.alarm(int(seconds))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def front(g):
    """Asks to bring the window to the front (Chrome only: `Page.bringToFront`)."""
    if hasattr(g, "cdp"):
        try:
            with cap(10, "Page.bringToFront"):
                g.cdp.call("Page.bringToFront")
        except Exception:                        # noqa: BLE001
            pass


def photo(s, name):
    """`s.foto()` with front and cap: (png | None, path | reason)."""
    why = ""
    for _i in range(3):
        front(s.g)
        try:
            with cap(25, "the photo"):
                return s.photo(name)
        except Cap as e:
            why = str(e)
    return None, why + " (three times)"


def photo_pil(s, name):
    """(PIL image | None, path | reason) — the full photo of the canvas."""
    from PIL import Image
    png, dove = photo(s, name)
    if not png:
        return None, dove
    return Image.open(io.BytesIO(png)).convert("RGB"), dove


# ═══════════════════════════════════════════════════════════════════════════
#  THE REAL MOUSE
# ═══════════════════════════════════════════════════════════════════════════
_CDP_BUTTONS = {0: ("left", 1), 1: ("middle", 4), 2: ("right", 2)}


def mouse(g, steps):
    """⭐ A chain of REAL browser events.  `steps`:
         ("move_to", x, y)        glass coordinates (the browser's viewport)
         ("giu", bottone, n)    n = the click count (2 = second press)
         ("su", bottone, n)
         ("pausa", ms)"""
    if hasattr(g, "cdp"):
        front(g)
        with cap(60, "the mouse events"):
            _mouse_cdp(g, steps)
        return
    _mouse_wd(g, steps)


def _mouse_cdp(g, steps):
    if True:
        c = g.cdp.call
        x = y = 0
        mask = 0
        for p in steps:
            if p[0] == "move_to":
                x, y = p[1], p[2]
                k = dict(type="mouseMoved", x=x, y=y)
                if mask:
                    down = [b for b, (_n, m) in _CDP_BUTTONS.items() if mask & m]
                    k.update(button=_CDP_BUTTONS[down[0]][0], buttons=mask)
                c("Input.dispatchMouseEvent", **k)
            elif p[0] in ("giu", "su"):
                name, m = _CDP_BUTTONS[p[1]]
                mask = (mask | m) if p[0] == "giu" else (mask & ~m)
                c("Input.dispatchMouseEvent",
                  type="mousePressed" if p[0] == "giu" else "mouseReleased",
                  x=x, y=y, button=name, buttons=mask, clickCount=p[2])
            elif p[0] == "pausa":
                time.sleep(p[1] / 1000.0)


def _mouse_wd(g, steps):
    az = []
    for p in steps:
        if p[0] == "move_to":
            az.append({"type": "pointerMove", "x": int(round(p[1])), "y": int(round(p[2])),
                       "origin": "viewport", "duration": 0})
        elif p[0] == "giu":
            az.append({"type": "pointerDown", "button": p[1]})
        elif p[0] == "su":
            az.append({"type": "pointerUp", "button": p[1]})
        elif p[0] == "pausa":
            az.append({"type": "pause", "duration": int(p[1])})
    g._actions([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                "actions": az}])


# ═══════════════════════════════════════════════════════════════════════════
#  THE REAL KEYBOARD
# ═══════════════════════════════════════════════════════════════════════════
#  name: (key, code, vk, WebDriver code | None, CDP bit)
#  ⚠ AltGraph and CapsLock have no WebDriver code: with Marionette they CANNOT
#    be pressed (declared limit); with CDP they can.
SPECIAL = {
    "Shift":      ("Shift", "ShiftLeft", 16, "", 8),
    "Control":    ("Control", "ControlLeft", 17, "", 2),
    "AltGraph":   ("AltGraph", "AltRight", 225, None, 0),
    "CapsLock":   ("CapsLock", "CapsLock", 20, None, 0),
    "Enter":      ("Enter", "Enter", 13, "", 0),
    "Backspace":  ("Backspace", "Backspace", 8, "", 0),
    "Escape":     ("Escape", "Escape", 27, "", 0),
    "Tab":        ("Tab", "Tab", 9, "", 0),
    "ArrowLeft":  ("ArrowLeft", "ArrowLeft", 37, "", 0),
    "ArrowUp":    ("ArrowUp", "ArrowUp", 38, "", 0),
    "ArrowRight": ("ArrowRight", "ArrowRight", 39, "", 0),
    "ArrowDown":  ("ArrowDown", "ArrowDown", 40, "", 0),
    "End":        ("End", "End", 35, "", 0),
}
PAUSE_MS = 90


def code_of(c):
    """The `code` and the keyCode of an ASCII character on any keyboard."""
    if c.isalpha() and c.isascii():
        return "Key" + c.upper(), ord(c.upper())
    if c.isdigit():
        return "Digit" + c, ord(c)
    if c == " ":
        return "Space", 32
    return "", 0


def keys(g, steps, pause_ms=PAUSE_MS):
    """⭐ REAL keys.  `steps` = [(«giu»|«su», name, code, vk)]; for the letters
    `name` is the character (the `key` the browser reports) and code/vk those
    of the position (None ⇒ those of any keyboard).
    Returns the SKIPPED steps (those Marionette cannot press)."""
    skipped = []
    if hasattr(g, "cdp"):
        front(g)
        with cap(90, "the keys"):
            _cdp_keys(g, steps, pause_ms)
        return skipped
    return _wd_keys(g, steps, pause_ms)


def _cdp_keys(g, steps, pause_ms):
    if True:
        mod = 0
        for kind, name, code, vk in steps:
            if name in SPECIAL:
                key, cd, v, _w, bit = SPECIAL[name]
                if kind == "giu":
                    mod |= bit
                g.cdp.call("Input.dispatchKeyEvent",
                             type="rawKeyDown" if kind == "giu" else "keyUp",
                             key=key, code=cd, windowsVirtualKeyCode=v, modifiers=mod)
                if kind == "su":
                    mod &= ~bit
            else:
                cd, v = code_of(name)
                cd, v = code or cd, vk or v
                p = dict(type="keyDown" if kind == "giu" else "keyUp", key=name, code=cd,
                         windowsVirtualKeyCode=v, modifiers=mod)
                if kind == "giu" and not (mod & 2):
                    p["text"] = p["unmodifiedText"] = name
                g.cdp.call("Input.dispatchKeyEvent", **p)
            time.sleep(pause_ms / 1000.0)


def _wd_keys(g, steps, pause_ms):
    skipped = []
    az = []
    for kind, name, _code, _vk in steps:
        v = SPECIAL[name][3] if name in SPECIAL else name
        if v is None:
            skipped.append((kind, name))
            continue
        az.append({"type": "keyDown" if kind == "giu" else "keyUp", "value": v})
        az.append({"type": "pause", "duration": pause_ms})
    g.m.call("WebDriver:PerformActions",
               {"actions": [{"type": "key", "id": "tastiera", "actions": az}]})
    g.m.call("WebDriver:ReleaseActions")
    return skipped


def press(name, code=None, vk=None):
    return [("giu", name, code, vk), ("su", name, code, vk)]


def write(text):
    p = []
    for c in text:
        p += press(c)
    return p


def clr(mod, steps):
    return [("giu", mod, None, None)] + steps + [("su", mod, None, None)]


# ═══════════════════════════════════════════════════════════════════════════
#  THE BROWSER'S LANGUAGE — from it the page declares the layout (ATTACH)
# ═══════════════════════════════════════════════════════════════════════════
def set_language(g, language):
    """Makes the browser say `navigator.language == lingua` (for the documents that
    open AFTERWARDS).  Returns a sentence saying how."""
    if hasattr(g, "cdp"):
        ua = g.js("return navigator.userAgent")
        g.cdp.call("Emulation.setUserAgentOverride", userAgent=ua, acceptLanguage=language)
        try:
            g.cdp.call("Emulation.setLocaleOverride", local=language)
        except Exception:                        # noqa: BLE001
            try:
                g.cdp.call("Emulation.setLocaleOverride")
                g.cdp.call("Emulation.setLocaleOverride", local=language)
            except Exception:                    # noqa: BLE001
                pass
        return "CDP Emulation (acceptLanguage=%s)" % language
    g.m.call("Marionette:SetContext", {"value": "chrome"})
    try:
        g.m.call("WebDriver:ExecuteScript", {
            "script": "Services.prefs.setStringPref('intl.accept_languages', arguments[0]);"
                      "return Services.prefs.getStringPref('intl.accept_languages');",
            "args": [language + "," + language.split("-")[0]]})
    finally:
        g.m.call("Marionette:SetContext", {"value": "content"})
    return "Firefox intl.accept_languages=%s" % language


# ═══════════════════════════════════════════════════════════════════════════
#  THE COMMON START: login, wake-up, scene, calibration
# ═══════════════════════════════════════════════════════════════════════════
def prepare(s, scene_port, language=None):
    """Logs in, wakes up, starts the scene, finds it in the photo.
    Returns (Scena, Mappa, geo, evidence_photo).  Raises `S.Bloccata`."""
    if language:
        print("   language: %s" % set_language(s.g, language), flush=True)
    ok, m = s.enter()
    if not ok:
        raise S.Blocked(m)
    if language:
        nl = s.g.js("return navigator.language")
        print("   navigator.language = %s" % nl, flush=True)
        if (nl or "").lower() != language.lower():
            raise S.Blocked("the browser does not say the language %s (it says %s): the page would not "
                             "declare the intended layout" % (language, nl))
    geo = s.geometry()
    if not geo:
        raise S.Blocked("`REMOTIX_PUNTATORE.geometry` is not there")
    print("   canvas %sx%s · buffer %sx%s" % (geo["tl"], geo["ta"], geo["bw"], geo["bh"]),
          flush=True)
    print("   wake-up: %s" % C21.wake(s.g, geo), flush=True)
    sc = Scene(s, scene_port)
    ok, t = sc.turn_on()
    print("   scene: %s" % ((t or "?").splitlines() or ["?"])[-1], flush=True)
    if not ok:
        raise S.Blocked("the scene does not start: %s" % " | ".join((t or "").splitlines())[-700:])
    mp, why, dove = None, "", ""
    fine = time.time() + 25
    while time.time() < fine:
        time.sleep(2.0)
        sc.in_charge("reset")
        r, _s, _f = sc.load()
        if not r:
            why = "the page did not declare its rectangles"
            continue
        im, dove = photo_pil(s, "scene")
        if im is None:
            why = dove
            continue
        mp, why = calibrate(im, geo, r)
        if mp:
            break
    if not mp:
        raise S.Blocked("the scene is not found in the photo: %s" % why)
    print("   scene found: %s (%s)" % (mp.describe(), why), flush=True)
    return sc, mp, geo, dove


def center(r):
    return (r[0] + r[2]) / 2.0, (r[1] + r[3]) / 2.0


def beat(s, sc, mp, steps, name, completed, wait=8.0, skippable=()):
    """Clean scene, click in field «a», the REAL KEYS, the state read until
    `completed(stato)` or the wait ends.  Returns (state, photo, skipped, why):
    a non-empty `why` = it could not be looked at."""
    if sc.in_charge("reset") is None:
        return None, "", [], "the scene did not answer the reset"
    R = sc.rect
    x, y = R["a"][0] + 0.5 * (R["a"][2] - R["a"][0]), R["a"][1] + 0.3 * (R["a"][3] - R["a"][1])
    vx, vy = mp.glass(x, y)
    mouse(s.g, [("move_to", vx, vy), ("pausa", 150), ("giu", 0, 1), ("pausa", 60),
                ("su", 0, 1), ("pausa", 400)])
    st = sc.in_charge("fuoco-a")
    if st is None or st.get("a") != "" or st.get("focus") != "a":
        return None, "", [], "the scene is not ready: %s" % (st,)
    skipped = keys(s.g, steps)
    report = [x for x in skipped if x[1] not in skippable]
    if report:
        return None, "", skipped, "keys this browser cannot press: %s" % report
    st = sc.wait_until(completed, wait)
    time.sleep(0.5)
    _png, dove = photo(s, name)
    return st, dove, skipped, ""
