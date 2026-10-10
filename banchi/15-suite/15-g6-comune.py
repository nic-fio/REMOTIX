#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g6-comune — THE TOOLS OF GROUP G6 «DETACH AND REATTACH» (phase 15)

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

C23 = S._carica("c23", os.path.join(S.BANCHI, "11-scatole",
                                    "11-c23-maiusc-e-frecce-selezionano.py"))

# ---------------------------------------------------------------------------
# THE STRIP'S PALETTE — far from the background's cyan, from the grey of the
# empty cell and from each other (minimum distance > 2 × TOLLERANZA on at least one channel).
# ---------------------------------------------------------------------------
CIANO = (0, 255, 255)
VUOTO = (128, 128, 128)
TAVOLOZZA = {"a": (255, 0, 0), "b": (0, 0, 255), "c": (0, 150, 0),
             "d": (255, 0, 255), "e": (0, 0, 0), "f": (255, 140, 0)}
ALFABETO = "abcdef"
CASELLE = 8
TOLLERANZA = 60
# the strip, in fractions of the page's VIEW (= the cyan rectangle)
STR_X0, STR_X1, STR_Y0, STR_Y1 = 0.04, 0.96, 0.45, 0.80
# ⚠ `[M]` 25 Sep 2026, xfce (labwc): the window is born CENTRED in the 4K and at the
#   reattach at 2560x1440 stays where it was — a window 800 tall ended up below the
#   edge and the strip could no longer be read.  Centred in 3840x2160, a
#   800x440 window also fits inside 2512x1296.
FINESTRA_SCENA = (800, 440)

PAGINA = """<!doctype html><meta charset=utf-8><title>REMOTIX G6</title>
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

SERVITORE = C23.SERVITORE
PREFERENZE = S.C21.PREFERENZE
PROFILO = ".g6-profilo"


def pagina():
    passo = (STR_X1 - STR_X0) / CASELLE * 100
    tav = {k: "rgb(%d,%d,%d)" % v for k, v in TAVOLOZZA.items()}
    return PAGINA % {"tav": json.dumps(tav), "n": CASELLE, "x0": STR_X0 * 100, "w": passo,
                     "y0": STR_Y0 * 100, "h": (STR_Y1 - STR_Y0) * 100}


def porta_scena(o):
    """⛔ The box is on the host network: the server's port is one of ours."""
    return o.porte_base + 5


# ═══════════════════════════════════════════════════════════════════════════
#  THE SCENE IN THE SESSION
# ═══════════════════════════════════════════════════════════════════════════
def accendi_scena(s, finestra=FINESTRA_SCENA):
    """Server + normal firefox-esr in the session of `s.chi`.  (ok, text)."""
    b = lambda x: base64.b64encode(x.encode()).decode()     # noqa: E731
    p = porta_scena(s.o)
    xul = S.C21.xulstore(*finestra)
    c, t = s.sc.dentro(
        # (the REAL ~/.cache is now given by `suite.Sessione`, 25 Sep 2026)
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
        "exit 1".format(c=s.chi, p=p, pr=PROFILO, srv=b(SERVITORE), pag=b(pagina()),
                        pref=b(PREFERENZE), xul=b(xul)), 150)
    return c == 0, t


def spegni_servitore(s):
    s.sc.dentro("pkill -f '[g]6-servitore.py %d ' 2>/dev/null; true" % porta_scena(s.o), 30)


def quaderno(s):
    """The scene's state lines (dict), in order."""
    _c, t = s.sc.dentro("cat /home/%s/g6.log 2>/dev/null" % s.chi, 30)
    fuori = []
    for r in t.splitlines():
        try:
            fuori.append(json.loads(r))
        except ValueError:
            pass
    return fuori


def ultimo_stato(s, fresco_s=8.0):
    """The last line of the notebook, ⛔ only if FRESH (the scene beats every 2 s):
    an old line is the state of a program that may no longer be there."""
    q = quaderno(s)
    if not q:
        return None
    r = q[-1]
    if time.time() * 1000 - r.get("t", 0) > fresco_s * 1000:
        return None
    return r


def processi(s):
    """{name: [pid, ...]} of the programs of the tenant's session that matter."""
    _c, t = s.sc.dentro(
        "for n in firefox-esr gnome-shell kwin_wayland labwc plasmashell xfce4-panel "
        "lxqt-panel; do for p in $(pgrep -u %s -x $n 2>/dev/null); do echo \"$n $p\"; "
        "done; done; loginctl list-sessions --no-legend 2>/dev/null | grep -w %s | "
        "awk '{print \"sessione \" $1}'" % (s.chi, s.chi), 30)
    fuori = {}
    for r in t.splitlines():
        p = r.split()
        if len(p) == 2 and "@" not in p[0] and not p[1].endswith(":"):
            fuori.setdefault(p[0], []).append(p[1])
    return fuori


def pid_scena(pr):
    """The lowest PID of firefox-esr: the scene's parent process."""
    v = pr.get("firefox-esr") or []
    try:
        return min(int(x) for x in v)
    except ValueError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  THE PHOTO: the cyan window and the strip
# ═══════════════════════════════════════════════════════════════════════════
def _vicino(p, c, toll=TOLLERANZA):
    return abs(p[0] - c[0]) <= toll and abs(p[1] - c[1]) <= toll and abs(p[2] - c[2]) <= toll


def immagine(png, largo=960):
    """PIL RGB reduced to `largo` (nearest neighbour): the counts in pure python."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if im.size[0] > largo:
        im = im.resize((largo, max(1, round(im.size[1] * largo / im.size[0]))),
                       Image.NEAREST)
    return im


def trova_ciano(im):
    """The cyan rectangle (the scene's view): (x0,y0,x1,y1) or (None, reason)."""
    w, h = im.size
    px = list(im.getdata())
    col, rig = [0] * w, [0] * h
    for y in range(h):
        b = y * w
        for x in range(w):
            if _vicino(px[b + x], CIANO, 40):
                col[x] += 1
                rig[y] += 1
    if max(col) == 0:
        return None, "no cyan pixel: the scene's window is not seen"
    xs = [x for x, n in enumerate(col) if n >= 0.3 * max(col)]
    ys = [y for y, n in enumerate(rig) if n >= 0.3 * max(rig)]
    r = (min(xs), min(ys), max(xs), max(ys))
    if (r[2] - r[0]) < 0.05 * w or (r[3] - r[1]) < 0.05 * h:
        return None, "the cyan is there but it is small (%s): it is not the window" % (r,)
    return r, ""


def nome_colore(p):
    best, dist = None, 10 ** 9
    for k, c in list(TAVOLOZZA.items()) + [("_", VUOTO), ("?", (255, 255, 255))]:
        d = max(abs(p[0] - c[0]), abs(p[1] - c[1]), abs(p[2] - c[2]))
        if d < dist:
            best, dist = k, d
    return best if dist <= TOLLERANZA else "!"


def leggi_striscia(im, r):
    """The text read from the strip inside the cyan rectangle `r`.
    Returns (text, detail): «_» = empty cell, «!» = unknown colour."""
    x0, y0, x1, y1 = r
    W, H = x1 - x0 + 1, y1 - y0 + 1
    passo = (STR_X1 - STR_X0) / CASELLE
    cy = y0 + H * (STR_Y0 + STR_Y1) / 2
    letti = []
    for i in range(CASELLE):
        cx = x0 + W * (STR_X0 + (i + 0.4) * passo)
        vals = []
        for dx in (-2, 0, 2):
            for dy in (-2, 0, 2):
                xx = min(max(int(cx) + dx, 0), im.size[0] - 1)
                yy = min(max(int(cy) + dy, 0), im.size[1] - 1)
                vals.append(im.getpixel((xx, yy)))
        vals.sort(key=lambda p: sum(p))
        letti.append(nome_colore(vals[len(vals) // 2]))
    s = "".join(letti)
    return s.rstrip("_"), s


def guarda_la_scena(s, nome):
    """⭐ Photographs the canvas, finds the window, reads the strip.
    Returns dict {finestra, letto, crudo, foto, perche, png}."""
    png, dove = s.foto(nome)
    if not png:
        return {"finestra": None, "letto": None, "foto": "", "perche": dove, "png": None}
    im = immagine(png)
    r, perche = trova_ciano(im)
    if not r:
        return {"finestra": None, "letto": None, "foto": dove, "perche": perche, "png": png,
                "misura": list(im.size)}
    letto, crudo = leggi_striscia(im, r)
    return {"finestra": list(r), "letto": letto, "crudo": crudo, "foto": dove, "perche": "",
            "png": png, "misura": list(im.size)}


def aspetta_testo(s, voluto, nome, tetto=12.0):
    """Photographs until the strip says `voluto` (or the cap)."""
    fine = time.time() + tetto
    v = None
    fallite = 0
    while True:
        v = guarda_la_scena(s, nome)
        if v.get("png") is None:
            fallite += 1
        # ⚠ `[M]` 25 Sep 2026, gnome+Chrome under load: the CDP photo of a
        #   just reborn session goes «timed out» (60 s each) ⇒ after two
        #   failed in a row it stops: the test stays under 10 minutes
        if v.get("letto") == voluto or time.time() >= fine or fallite >= 2:
            return v
        time.sleep(1.0)


# ═══════════════════════════════════════════════════════════════════════════
#  THE REAL INPUT: the click on the window, the keys
# ═══════════════════════════════════════════════════════════════════════════
def sveglia(s):
    """A real ESC (GNOME is born in the overview: the scene would be small)."""
    try:
        geo = s.geometria()
        if geo:
            return S.C21.sveglia(s.g, geo)
    except Exception as e:                       # noqa: BLE001
        return "⚠ %s" % e
    return "⚠ no geometry"


def clic_sulla_scena(s, v):
    """A REAL browser click on the scene's cyan (gives it the focus)."""
    geo = s.geometria()
    if not geo or not v.get("finestra"):
        return "⚠ no geometry or window"
    pw, ph = v["misura"]
    x0, y0, x1, y1 = v["finestra"]
    # a point of the cyan below the strip
    fx, fy = x0 + (x1 - x0) * 0.5, y0 + (y1 - y0) * 0.9
    X, Y = S.C21.dalla_foto_al_desktop(geo, pw, ph, fx, fy)
    vx, vy = S.C21.dal_desktop_al_vetro(geo, X, Y)
    try:
        s.g.js("if (document.activeElement && document.activeElement.blur) "
               "document.activeElement.blur(); return 1;")
    except Exception:                            # noqa: BLE001
        pass
    s.g.clic(vx, vy)
    time.sleep(0.8)
    return "click at (%d,%d) of the desktop" % (X, Y)


def scrivi_la_base(s, v, testo, prove=3):
    """⭐ The PREPARATION (not the function looked at): click on the scene, text
    written, read in the photo.  `[M]` 24 Sep 2026, KDE under load 50: once
    in one 2 letters out of 4 arrived (the focus arrives late) ⇒ it is cleaned
    (Ctrl+A, Backspace) and rewritten, up to `prove` times.  Returns (v, notes)."""
    note = []
    for k in range(prove):
        cl = clic_sulla_scena(s, v)
        if k:
            C23.manda(s.g, C23.PULISCI)
            time.sleep(0.5)
        time.sleep(0.7)
        C23.manda(s.g, C23.scrivi(testo))
        v2 = aspetta_testo(s, testo, "scritto-prima", tetto=10)
        note.append("attempt %d: %s, read «%s»" % (k + 1, cl, v2.get("letto")))
        if v2.get("letto") == testo:
            return v2, note
        if v2.get("finestra"):
            v = v2
    return v2, note


def scrivi(s, testo):
    C23.manda(s.g, C23.scrivi(testo))


# ═══════════════════════════════════════════════════════════════════════════
#  THE BROWSER: closing it, killing it, reopening it at a size
# ═══════════════════════════════════════════════════════════════════════════
def albero(pid):
    """The PID and all its descendants (from /proc)."""
    figli = {}
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        try:
            with open("/proc/%s/stat" % d) as f:
                st = f.read()
            pp = int(st.rsplit(")", 1)[1].split()[1])
            figli.setdefault(pp, []).append(int(d))
        except (OSError, ValueError, IndexError):
            pass
    fuori, coda = [], [pid]
    while coda:
        p = coda.pop()
        fuori.append(p)
        coda.extend(figli.get(p, []))
    return fuori


def uccidi_browser(s):
    """⛔ kill -9 of the browser and of all its processes: no farewell.
    Returns how many processes."""
    g = s.g
    if hasattr(g, "uccidi"):
        # ⭐ the phone (phase 19 §5): Chrome stopped abruptly by adb (`am force-stop`)
        n = g.uccidi()
        s.g = None
        return n
    p = getattr(g, "p", None)
    if p is None:
        return 0
    tutti = albero(p.pid)
    for x in tutti:
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
    prof = getattr(g, "profilo", None)
    if prof:
        shutil.rmtree(prof, ignore_errors=True)
    s.g = None
    return len(tutti)


def accendi_a_misura(s, largo, alto):
    """Restarts the session's browser at the requested size.  4K = maximised
    (like `Sessione`); the rest: Chrome is born with `--window-size`, Firefox with
    `SetWindowRect`.  Returns the size read back."""
    o = s.o
    if o.browser == "telefono":
        # ⭐ the phone (phase 19 §5) has no windows to size: the new size is
        #   the phone TURNED; the starting 4K is the orientation the user left it in
        print("   phone: %s" % S.telefono().orienta(
            "partenza" if (largo, alto) == (3840, 2160) else "altro"), flush=True)
        s.accendi_browser()
        try:
            return s.g.js("return [innerWidth, innerHeight, devicePixelRatio]")
        except Exception as e:                   # noqa: BLE001
            return "? (%s)" % e
    vecchio = list(S.VERI.FINESTRA)
    ol, oa = o.largo, o.alto
    try:
        if o.browser == "chrome" and (largo, alto) != (3840, 2160):
            S.VERI.FINESTRA[:] = [largo, alto]
            o.largo = 0                           # no «maximised»
        else:
            o.largo, o.alto = largo, alto
        s.accendi_browser()
    finally:
        S.VERI.FINESTRA[:] = vecchio
        o.largo, o.alto = ol, oa
    try:
        return s.g.js("return [innerWidth, innerHeight, devicePixelRatio]")
    except Exception as e:                       # noqa: BLE001
        return "? (%s)" % e


def entra_con_riprova(s, tetto_s=45.0, primo_apri=True):
    """Logs in; if the slot is still taken (0x0F, the ghost of §5.1) it retries
    every 3 s up to the cap.  Returns (ok, reason, refusals, seconds)."""
    t0 = time.time()
    rifiuti = []
    while True:
        ok, m = s.entra()
        if ok:
            return True, m, rifiuti, time.time() - t0
        rifiuti.append("%.1fs %s" % (time.time() - t0, m[:160]))
        if time.time() - t0 > tetto_s:
            return False, m, rifiuti, time.time() - t0
        time.sleep(3)


def osserva_tela(s):
    """The page's fields: canvas (buffer), view, rectangle, outcome, scale."""
    st = s.stato()
    geo = None
    try:
        geo = s.geometria()
    except Exception:                            # noqa: BLE001
        pass
    return {"esito": st.get("esito"), "buffer": st.get("buffer"), "vista": st.get("vista"),
            "tela_rett": st.get("tela"),
            "scala": [round(geo["sx"], 3), round(geo["sy"], 3)] if geo else None,
            "tl_ta": [geo["tl"], geo["ta"]] if geo else None}


def aspetta_tela_ferma(s, tetto=25.0):
    """After the reattach the canvas can still change (`ADATTA_TELA` → `TELA`):
    we wait for the buffer to stay the same for 4 s."""
    fine = time.time() + tetto
    ult, da = None, time.time()
    ob = osserva_tela(s)
    while time.time() < fine:
        ob = osserva_tela(s)
        b = tuple(ob.get("buffer") or ())
        if b != ult:
            ult, da = b, time.time()
        elif time.time() - da >= 4:
            break
        time.sleep(0.8)
    return ob


SECCHI = 50


def bordi(im, r=None):
    """The signature of the photo's edges: mean colour of the 6 rows at the top and at the
    bottom (all, and in SECCHI width slices), the fraction of BLACK in the
    3 % band on the right and at the bottom, and the slices COVERED by the
    scene's window `r` (± 3 %): ⚠ `[M]` 25 Sep 2026, xfce: shrinking the desktop the
    window stays where it was and reaches the edge — it is not the panel missing."""
    w, h = im.size
    px = im.load()

    def fette(ys):
        fuori = []
        for k in range(SECCHI):
            t, n = [0, 0, 0], 0
            for x in range(int(w * k / SECCHI), max(int(w * (k + 1) / SECCHI), int(w * k / SECCHI) + 1)):
                for y in ys:
                    p = px[min(x, w - 1), y]
                    t[0] += p[0]; t[1] += p[1]; t[2] += p[2]; n += 1        # noqa: E702
            fuori.append([round(v / max(1, n)) for v in t])
        return fuori
    coperte = []
    if r:
        a, b = (r[0] / w) - 0.03, (r[2] / w) + 0.03
        coperte = [k for k in range(SECCHI) if (k + 1) / SECCHI > a and k / SECCHI < b]

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
    return {"alto": media(range(0, min(6, h))), "basso": media(range(max(0, h - 6), h)),
            "alto_f": fette(range(0, min(6, h))), "basso_f": fette(range(max(0, h - 6), h)),
            "coperte": coperte,
            "nero_destra": nero(range(int(w * 0.97), w), range(0, h, 3)),
            "nero_basso": nero(range(0, w, 3), range(int(h * 0.97), h))}


def distanza(a, b):
    return max(abs(x - y) for x, y in zip(a, b))
