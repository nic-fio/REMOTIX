#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g6-common — THE TOOLS OF GROUP G6 «DETACH AND REATTACH» (phase 15)

Used by 15-f016, 15-f018, 15-f020.  It is not a test: it is the SCENE and the
pure judges that the three tests share.

⭐ THE SCENE, inside the tenant's session:
   - a minimal server (python3, 127.0.0.1:<port>, ⛔ the box is on the host
     network: the port is one of OURS, porte-base+5) that serves the page and
     writes down in the «notebook» (~/g6.log) what the page sends it;
   - a NORMAL `firefox-esr` (with borders, 800x440: the desktop centres it, and
     centred in the 4K it also fits inside a 2512x1296 desktop) that shows the page:
       · CYAN background (the window is found in the photo),
       · an always-focused text field,
       · the STRIP: 8 cells, one per character written, of one colour per
         letter («a»…«f»); empty = grey.  ⇒ the written text is READ from the
         photo of the canvas;
       · every 2 s it sends its state to the notebook: the TOKEN (born when the
         page loaded: if the page is reborn, it changes), the field value, the
         size of the SCREEN seen from inside (screen.width × height = the
         compositor's output) and the window.
   ⇒ two fields and a photo: «the program is alive» (same PID, beats that
     continue with the previous token), «the state is that one» (field value),
     «it is seen» (cyan window + strip read in the photo).
"""
import base64
import io
import json
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

C23 = S._load("c23", os.path.join(S.BENCHES, "11-boxes",
                                    "11-c23-shift-and-arrows-select.py"))

# ---------------------------------------------------------------------------
# THE STRIP'S PALETTE — far from the background's cyan, from the grey of the
# empty cell and from each other (minimum distance > 2 × TOLERANCE on at least one channel).
# ---------------------------------------------------------------------------
CYAN = (0, 255, 255)
EMPTY = (128, 128, 128)
PALETTE = {"a": (255, 0, 0), "b": (0, 0, 255), "c": (0, 150, 0),
             "d": (255, 0, 255), "e": (0, 0, 0), "f": (255, 140, 0)}
ALPHABET = "abcdef"
CELLS = 8
TOLERANCE = 60
# the strip, in fractions of the page's VIEW (= the cyan rectangle)
STR_X0, STR_X1, STR_Y0, STR_Y1 = 0.04, 0.96, 0.45, 0.80
# ⚠ `[M]` 25 Sep 2026, xfce (labwc): the window is born CENTRED in the 4K and at the
#   reattach at 2560x1440 stays where it was — a window 800 tall ended up below the
#   edge and the strip could no longer be read.  Centred in 3840x2160, a
#   800x440 window also fits inside 2512x1296.
SCENE_WINDOW = (800, 440)

PAGE = """<!doctype html><meta charset=utf-8><title>REMOTIX G6</title>
<style>
 html,body{margin:0;height:100%%;background:#00FFFF;overflow:hidden;cursor:default}
 #f{position:fixed;left:4vw;top:6vh;width:40vw;height:12vh;font:8vh/1 monospace;border:0;
    padding:0 1vw;box-sizing:border-box;background:#fff;color:#000;outline:0}
 .k{position:fixed;top:%(y0)fvh;height:%(h)fvh;width:calc(%(w)fvw - 1.4vw)}
</style>
<input id=f autocomplete=off spellcheck=false>
<div id=s></div>
<script>
const TAV=%(tav)s, VUOTO='rgb(128,128,128)', N=%(n)d;
const G=(Date.now().toString(36)+Math.random().toString(36).slice(2,8));
const f=document.getElementById('f'), s=document.getElementById('s'), k=[];
for (let i=0;i<N;i++){const d=document.createElement('div');d.className='k';
  d.style.left=(%(x0)f+i*%(w)f)+'vw';s.appendChild(d);k.push(d);}
const m=(t)=>fetch('/l',{method:'POST',body:t}).catch(()=>0);
function dipingi(){const v=f.value;
  for(let i=0;i<N;i++){k[i].style.background = i<v.length ? (TAV[v[i]]||'rgb(255,255,255)') : VUOTO;}}
function stato(perche){m(JSON.stringify({g:G,p:perche,v:f.value,sw:screen.width,sh:screen.height,
  iw:innerWidth,ih:innerHeight,t:Date.now()}));}
dipingi(); f.focus(); stato('caricata');
f.addEventListener('input',()=>{dipingi();stato('input');});
addEventListener('resize',()=>stato('resize'));
setInterval(()=>{ if(document.activeElement!==f) f.focus(); dipingi(); },300);
setInterval(()=>stato('battito'),2000);
</script>"""

SERVER = C23.SERVER
PREFERENCES = S.C21.PREFERENCES
PROFILE = ".g6-profilo"


def page():
    step = (STR_X1 - STR_X0) / CELLS * 100
    pal = {k: "rgb(%d,%d,%d)" % v for k, v in PALETTE.items()}
    return PAGE % {"pal": json.dumps(pal), "n": CELLS, "x0": STR_X0 * 100, "w": step,
                     "y0": STR_Y0 * 100, "h": (STR_Y1 - STR_Y0) * 100}


def scene_port(o):
    """⛔ The box is on the host network: the server's port is one of ours."""
    return o.base_port + 5


# ═══════════════════════════════════════════════════════════════════════════
#  THE SCENE IN THE SESSION
# ═══════════════════════════════════════════════════════════════════════════
def turn_on_scene(s, window=SCENE_WINDOW):
    """Server + normal firefox-esr in the session of `s.chi`.  (ok, text)."""
    b = lambda x: base64.b64encode(x.encode()).decode()     # noqa: E731
    p = scene_port(s.o)
    xul = S.C21.xulstore(*window)
    c, t = s.sc.inside(
        # (the REAL ~/.cache is now given by `suite.Session`, 25 Sep 2026)
        "set -e; h=/home/{c}; mkdir -p $h/{pr}; "
        "echo {srv} | base64 -d > $h/g6-servitore.py; echo {pag} | base64 -d > $h/g6.html; "
        "echo {pref} | base64 -d > $h/{pr}/user.js; echo {xul} | base64 -d > $h/{pr}/xulstore.json; "
        ": > $h/g6.log; chown -R {c}: $h/{pr} $h/g6-servitore.py $h/g6.html $h/g6.log; set +e; "
        "u=$(id -u {c}); "
        "setsid runuser -u {c} -- python3 $h/g6-servitore.py {p} $h/g6.html $h/g6.log "
        "</dev/null >/dev/null 2>&1 & "
        "d=''; for i in $(seq 1 40); do d=$(ls /run/user/$u 2>/dev/null | "
        "grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] && break; sleep 0.5; done; "
        "[ -n \"$d\" ] || {{ echo 'no wayland socket'; exit 2; }}; sleep 1; "
        "setsid runuser -u {c} -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=$h firefox-esr --no-remote --new-instance "
        "--profile $h/{pr} http://127.0.0.1:{p}/ "
        "</dev/null >$h/.g6-firefox.log 2>&1 & "
        "for i in $(seq 1 200); do grep -q caricata $h/g6.log && {{ echo accesa; exit 0; }}; "
        "sleep 0.5; done; echo 'the scene did not say «caricata»'; tail -n 5 $h/.g6-firefox.log; "
        "exit 1".format(c=s.chi, p=p, pr=PROFILE, srv=b(SERVER), page_map=b(page()),
                        pref=b(PREFERENCES), xul=b(xul)), 150)
    return c == 0, t


def turn_off_server(s):
    s.sc.inside("pkill -f '[g]6-servitore.py %d ' 2>/dev/null; true" % scene_port(s.o), 30)


def notebook(s):
    """The scene's state lines (dict), in order."""
    _c, t = s.sc.inside("cat /home/%s/g6.log 2>/dev/null" % s.chi, 30)
    report = []
    for r in t.splitlines():
        try:
            report.append(json.loads(r))
        except ValueError:
            pass
    return report


def last_state(s, fresh_s=8.0):
    """The last line of the notebook, ⛔ only if FRESH (the scene beats every 2 s):
    an old line is the state of a program that may no longer be there."""
    q = notebook(s)
    if not q:
        return None
    r = q[-1]
    if time.time() * 1000 - r.get("t", 0) > fresh_s * 1000:
        return None
    return r


def processes(s):
    """{name: [pid, ...]} of the programs of the tenant's session that matter."""
    _c, t = s.sc.inside(
        "for n in firefox-esr gnome-shell kwin_wayland labwc plasmashell xfce4-panel "
        "lxqt-panel; do for p in $(pgrep -u %s -x $n 2>/dev/null); do echo \"$n $p\"; "
        "done; done; loginctl list-sessions --no-legend 2>/dev/null | grep -w %s | "
        "awk '{print \"sessione \" $1}'" % (s.chi, s.chi), 30)
    report = {}
    for r in t.splitlines():
        p = r.split()
        if len(p) == 2 and "@" not in p[0] and not p[1].endswith(":"):
            report.setdefault(p[0], []).append(p[1])
    return report


def scene_pid(pr):
    """The lowest PID of firefox-esr: the scene's parent process."""
    v = pr.get("firefox-esr") or []
    try:
        return min(int(x) for x in v)
    except ValueError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  THE PHOTO: the cyan window and the strip
# ═══════════════════════════════════════════════════════════════════════════
def _near(p, c, toll=TOLERANCE):
    return abs(p[0] - c[0]) <= toll and abs(p[1] - c[1]) <= toll and abs(p[2] - c[2]) <= toll


def bitmap(png, largo=960):
    """PIL RGB reduced to `largo` (nearest neighbour): the counts in pure python."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if im.size[0] > largo:
        im = im.resize((largo, max(1, round(im.size[1] * largo / im.size[0]))),
                       Image.NEAREST)
    return im


def find_cyan(im):
    """The cyan rectangle (the scene's view): (x0,y0,x1,y1) or (None, reason)."""
    w, h = im.size
    px = list(im.getdata())
    clr, rig = [0] * w, [0] * h
    for y in range(h):
        b = y * w
        for x in range(w):
            if _near(px[b + x], CYAN, 40):
                clr[x] += 1
                rig[y] += 1
    if max(clr) == 0:
        return None, "no cyan pixel: the scene's window is not seen"
    xs = [x for x, n in enumerate(clr) if n >= 0.3 * max(clr)]
    ys = [y for y, n in enumerate(rig) if n >= 0.3 * max(rig)]
    r = (min(xs), min(ys), max(xs), max(ys))
    if (r[2] - r[0]) < 0.05 * w or (r[3] - r[1]) < 0.05 * h:
        return None, "the cyan is there but it is small (%s): it is not the window" % (r,)
    return r, ""


def color_name(p):
    best, dist = None, 10 ** 9
    for k, c in list(PALETTE.items()) + [("_", EMPTY), ("?", (255, 255, 255))]:
        d = max(abs(p[0] - c[0]), abs(p[1] - c[1]), abs(p[2] - c[2]))
        if d < dist:
            best, dist = k, d
    return best if dist <= TOLERANCE else "!"


def read_strip(im, r):
    """The text read from the strip inside the cyan rectangle `r`.
    Returns (text, detail): «_» = empty cell, «!» = unknown colour."""
    x0, y0, x1, y1 = r
    W, H = x1 - x0 + 1, y1 - y0 + 1
    step = (STR_X1 - STR_X0) / CELLS
    cy = y0 + H * (STR_Y0 + STR_Y1) / 2
    readings = []
    for i in range(CELLS):
        cx = x0 + W * (STR_X0 + (i + 0.4) * step)
        vals = []
        for dx in (-2, 0, 2):
            for dy in (-2, 0, 2):
                xx = min(max(int(cx) + dx, 0), im.size[0] - 1)
                yy = min(max(int(cy) + dy, 0), im.size[1] - 1)
                vals.append(im.getpixel((xx, yy)))
        vals.sort(key=lambda p: sum(p))
        readings.append(color_name(vals[len(vals) // 2]))
    s = "".join(readings)
    return s.rstrip("_"), s


def look_scene(s, name):
    """⭐ Photographs the canvas, finds the window, reads the strip.
    Returns dict {finestra, letto, crudo, foto, perche, png}."""
    png, dove = s.photo(name)
    if not png:
        return {"window": None, "read": None, "photo": "", "why": dove, "png": None}
    im = bitmap(png)
    r, why = find_cyan(im)
    if not r:
        return {"window": None, "read": None, "photo": dove, "why": why, "png": png,
                "size": list(im.size)}
    read, raw = read_strip(im, r)
    return {"window": list(r), "read": read, "raw": raw, "photo": dove, "why": "",
            "png": png, "size": list(im.size)}


def wait_text(s, wanted, name, cap=12.0):
    """Photographs until the strip says `wanted` (or the cap)."""
    fine = time.time() + cap
    v = None
    failures = 0
    while True:
        v = look_scene(s, name)
        if v.get("png") is None:
            failures += 1
        # ⚠ `[M]` 25 Sep 2026, gnome+Chrome under load: the CDP photo of a
        #   just reborn session goes «timed out» (60 s each) ⇒ after two
        #   failed in a row it stops: the test stays under 10 minutes
        if v.get("read") == wanted or time.time() >= fine or failures >= 2:
            return v
        time.sleep(1.0)


# ═══════════════════════════════════════════════════════════════════════════
#  THE REAL INPUT: the click on the window, the keys
# ═══════════════════════════════════════════════════════════════════════════
def wake(s):
    """A real ESC (GNOME is born in the overview: the scene would be small)."""
    try:
        geo = s.geometry()
        if geo:
            return S.C21.wake(s.g, geo)
    except Exception as e:                       # noqa: BLE001
        return "⚠ %s" % e
    return "⚠ no geometry"


def click_on_scene(s, v):
    """A REAL browser click on the scene's cyan (gives it the focus)."""
    geo = s.geometry()
    if not geo or not v.get("window"):
        return "⚠ no geometry or window"
    pw, ph = v["size"]
    x0, y0, x1, y1 = v["window"]
    # a point of the cyan below the strip
    fx, fy = x0 + (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.9
    X, Y = S.C21.from_photo_to_desktop(geo, pw, ph, fx, fy)
    vx, vy = S.C21.desktop_to_glass(geo, X, Y)
    try:
        s.g.js("if (document.activeElement && document.activeElement.blur) "
               "document.activeElement.blur(); return 1;")
    except Exception:                            # noqa: BLE001
        pass
    s.g.click(vx, vy)
    time.sleep(0.8)
    return "click at (%d,%d) of the desktop" % (X, Y)


def write_base(s, v, text, prove=3):
    """⭐ The PREPARATION (not the function looked at): click on the scene, text
    written, read in the photo.  `[M]` 24 Sep 2026, KDE under load 50: once
    in one 2 letters out of 4 arrived (the focus arrives late) ⇒ it is cleaned
    (Ctrl+A, Backspace) and rewritten, up to `prove` times.  Returns (v, notes)."""
    note = []
    for k in range(prove):
        cl = click_on_scene(s, v)
        if k:
            C23.send_msg(s.g, C23.CLEAN)
            time.sleep(0.5)
        time.sleep(0.7)
        C23.send_msg(s.g, C23.write(text))
        v2 = wait_text(s, text, "scritto-prima", cap=10)
        note.append("attempt %d: %s, read «%s»" % (k + 1, cl, v2.get("read")))
        if v2.get("read") == text:
            return v2, note
        if v2.get("window"):
            v = v2
    return v2, note


def write(s, text):
    C23.send_msg(s.g, C23.write(text))


# ═══════════════════════════════════════════════════════════════════════════
#  THE BROWSER: closing it, killing it, reopening it at a size
# ═══════════════════════════════════════════════════════════════════════════
def tree(pid):
    """The PID and all its descendants (from /proc)."""
    children = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open("/proc/%s/stat" % d) as f:
                st = f.read()
            pp = int(st.rsplit(")", 1)[1].split()[1])
            children.setdefault(pp, []).append(int(d))
        except (OSError, ValueError, IndexError):
            pass
    report, queue = [], [pid]
    while queue:
        p = queue.pop()
        report.append(p)
        queue.extend(children.get(p, []))
    return report


def kill_browser(s):
    """⛔ kill -9 of the browser and of all its processes: no farewell.
    Returns how many processes."""
    g = s.g
    if hasattr(g, "kill"):
        # ⭐ the phone (phase 19 §5): Chrome stopped abruptly by adb (`am force-stop`)
        n = g.kill()
        s.g = None
        return n
    p = getattr(g, "p", None)
    if p is None:
        return 0
    all_items = tree(p.pid)
    for x in all_items:
        try:
            os.kill(x, signal.SIGKILL)
        except OSError:
            pass
    try:
        p.wait(10)
    except Exception:                            # noqa: BLE001
        pass
    # the driver's shell: no farewell, only the leftovers on disk
    import shutil
    prof = getattr(g, "profile", None)
    if prof:
        shutil.rmtree(prof, ignore_errors=True)
    s.g = None
    return len(all_items)


def turn_on_at_size(s, largo, alto):
    """Restarts the session's browser at the requested size.  4K = maximised
    (like `Session`); the rest: Chrome is born with `--window-size`, Firefox with
    `SetWindowRect`.  Returns the size read back."""
    o = s.o
    if o.browser == "phone":
        # ⭐ the phone (phase 19 §5) has no windows to size: the new size is
        #   the phone TURNED; the starting 4K is the orientation the user left it in
        print("   phone: %s" % S.phone().orient(
            "start_base" if (largo, alto) == (3840, 2160) else "altro"), flush=True)
        s.turn_on_browser()
        try:
            return s.g.js("return [innerWidth, innerHeight, devicePixelRatio]")
        except Exception as e:                   # noqa: BLE001
            return "? (%s)" % e
    old = list(S.VERI.WINDOW)
    ol, oa = o.width, o.height
    try:
        if o.browser == "chrome" and (largo, alto) != (3840, 2160):
            S.VERI.WINDOW[:] = [largo, alto]
            o.width = 0                           # no «maximised»
        else:
            o.width, o.height = largo, alto
        s.turn_on_browser()
    finally:
        S.VERI.WINDOW[:] = old
        o.width, o.height = ol, oa
    try:
        return s.g.js("return [innerWidth, innerHeight, devicePixelRatio]")
    except Exception as e:                       # noqa: BLE001
        return "? (%s)" % e


def enter_with_retry(s, cap_s=45.0, first_open=True):
    """Logs in; if the slot is still taken (0x0F, the ghost of §5.1) it retries
    every 3 s up to the cap.  Returns (ok, reason, refusals, seconds)."""
    t0 = time.time()
    refusals = []
    while True:
        ok, m = s.enter()
        if ok:
            return True, m, refusals, time.time() - t0
        refusals.append("%.1fs %s" % (time.time() - t0, m[:160]))
        if time.time() - t0 > cap_s:
            return False, m, refusals, time.time() - t0
        time.sleep(3)


def observe_canvas(s):
    """The page's fields: canvas (buffer), view, rectangle, outcome, scale."""
    st = s.state()
    geo = None
    try:
        geo = s.geometry()
    except Exception:                            # noqa: BLE001
        pass
    return {"outcome": st.get("outcome"), "buffer": st.get("buffer"), "view": st.get("view"),
            "tela_rett": st.get("canvas"),
            "scala": [round(geo["sx"], 3), round(geo["sy"], 3)] if geo else None,
            "tl_ta": [geo["tl"], geo["ta"]] if geo else None}


def wait_canvas_still(s, cap=25.0):
    """After the reattach the canvas can still change (`FIT_CANVAS` → `CANVAS`):
    we wait for the buffer to stay the same for 4 s."""
    fine = time.time() + cap
    prev, da = None, time.time()
    ob = observe_canvas(s)
    while time.time() < fine:
        ob = observe_canvas(s)
        b = tuple(ob.get("buffer") or ())
        if b != prev:
            prev, da = b, time.time()
        elif time.time() - da >= 4:
            break
        time.sleep(0.8)
    return ob


BUCKETS = 50


def borders(im, r=None):
    """The signature of the photo's edges: mean colour of the 6 rows at the top and at the
    bottom (all, and in BUCKETS width slices), the fraction of BLACK in the
    3 % band on the right and at the bottom, and the slices COVERED by the
    scene's window `r` (± 3 %): ⚠ `[M]` 25 Sep 2026, xfce: shrinking the desktop the
    window stays where it was and reaches the edge — it is not the panel missing."""
    w, h = im.size
    px = im.load()

    def slices(ys):
        report = []
        for k in range(BUCKETS):
            t, n = [0, 0, 0], 0
            for x in range(int(w * k / BUCKETS), max(int(w * (k + 1) / BUCKETS), int(w * k / BUCKETS) + 1)):
                for y in ys:
                    p = px[min(x, w - 1), y]
                    t[0] += p[0]; t[1] += p[1]; t[2] += p[2]; n += 1        # noqa: E702
            report.append([round(v / max(1, n)) for v in t])
        return report
    covered = []
    if r:
        a, b = (r[0] / w) - 0.03, (r[2] / w) + 0.03
        covered = [k for k in range(BUCKETS) if (k + 1) / BUCKETS > a and k / BUCKETS < b]

    def media(ys):
        t = [0, 0, 0]
        n = 0
        for y in ys:
            for x in range(0, w, 2):
                p = px[x, y]
                t[0] += p[0]; t[1] += p[1]; t[2] += p[2]; n += 1        # noqa: E702
        return [round(v / max(1, n)) for v in t]

    # the window (with frame and bars: the 3 % margin, and 12 % at the top for
    # the browser's bars) does not count for the black band
    if r:
        fx0, fx1 = r[0] - 0.03 * w, r[2] + 0.03 * w
        fy0, fy1 = r[1] - 0.12 * h, r[3] + 0.03 * h
    else:
        fx0 = fx1 = fy0 = fy1 = -1

    def nero(xs, ys):
        n = k = 0
        for y in ys:
            for x in xs:
                if fx0 <= x <= fx1 and fy0 <= y <= fy1:
                    continue
                p = px[x, y]
                n += 1
                k += (p[0] < 12 and p[1] < 12 and p[2] < 12)
        return round(k / max(1, n), 3)
    return {"top": media(range(0, min(6, h))), "basso": media(range(max(0, h - 6), h)),
            "alto_f": slices(range(0, min(6, h))), "basso_f": slices(range(max(0, h - 6), h)),
            "covered": covered,
            "nero_destra": nero(range(int(w * 0.97), w), range(0, h, 3)),
            "nero_basso": nero(range(0, w, 3), range(int(h * 0.97), h))}


def distance(a, b):
    return max(abs(x - y) for x, y in zip(a, b))
