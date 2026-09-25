#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g6-comune — GLI ATTREZZI DEL GRUPPO G6 «STACCO E RIATTACCO» (fase 15)

Usati da 15-f016, 15-f018, 15-f020.  Non e' una prova: e' la SCENA e i
giudici puri che le tre prove condividono.

⭐ LA SCENA, dentro la sessione dell'inquilino:
   - un servitore minimo (python3, 127.0.0.1:<porta>, ⛔ la scatola e' in rete
     host: la porta e' una delle NOSTRE, porte-base+5) che serve la pagina e
     annota nel «quaderno» (~/g6.log) quel che la pagina gli manda;
   - `firefox-esr` NORMALE (con i bordi, 800x440: il desktop la centra, e
     centrata nel 4K sta anche dentro un desktop 2512x1296) che mostra la pagina:
       · fondo CIANO (la finestra si trova nella foto),
       · un campo di testo sempre a fuoco,
       · la STRISCIA: 8 caselle, una per carattere scritto, di un colore per
         lettera («a»…«f»); vuota = grigio.  ⇒ il testo scritto si LEGGE dalla
         fotografia della tela;
       · ogni 2 s manda al quaderno il suo stato: il GETTONE (nato al carico
         della pagina: se la pagina rinasce, cambia), il valore del campo, la
         misura dello SCHERMO visto da dentro (screen.width × height = l'uscita
         del compositore) e la finestra.
   ⇒ due campi e una foto: «il programma e' vivo» (PID uguale, battiti che
     continuano col gettone di prima), «lo stato e' quello» (valore del campo),
     «si vede» (finestra ciano + striscia letta nella foto).
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
# LA TAVOLOZZA DELLA STRISCIA — lontana dal ciano del fondo, dal grigio del
# vuoto e fra loro (distanza minima > 2 × TOLLERANZA su almeno un canale).
# ---------------------------------------------------------------------------
CIANO = (0, 255, 255)
VUOTO = (128, 128, 128)
TAVOLOZZA = {"a": (255, 0, 0), "b": (0, 0, 255), "c": (0, 150, 0),
             "d": (255, 0, 255), "e": (0, 0, 0), "f": (255, 140, 0)}
ALFABETO = "abcdef"
CASELLE = 8
TOLLERANZA = 60
# la striscia, in frazioni della VISTA della pagina (= il rettangolo ciano)
STR_X0, STR_X1, STR_Y0, STR_Y1 = 0.04, 0.96, 0.45, 0.80
# ⚠ `[M]` 25 set 2026, xfce (labwc): la finestra nasce CENTRATA nel 4K e al
#   riattacco a 2560x1440 resta dov'era — una finestra alta 800 finiva sotto il
#   bordo e la striscia non si leggeva piu'.  Centrata in 3840x2160, una
#   finestra 800x440 sta anche dentro 2512x1296.
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
    """⛔ La scatola e' in rete host: la porta del servitore e' una delle nostre."""
    return o.porte_base + 5


# ═══════════════════════════════════════════════════════════════════════════
#  LA SCENA NELLA SESSIONE
# ═══════════════════════════════════════════════════════════════════════════
def accendi_scena(s):
    """Servitore + firefox-esr normale nella sessione di `s.chi`.  (ok, testo)."""
    b = lambda x: base64.b64encode(x.encode()).decode()     # noqa: E731
    p = porta_scena(s.o)
    xul = S.C21.xulstore(*FINESTRA_SCENA)
    c, t = s.sc.dentro(
        # (la ~/.cache VERA la da' ora `suite.Sessione`, 25 set 2026)
        "set -e; h=/home/{c}; mkdir -p $h/{pr}; "
        "echo {srv} | base64 -d > $h/g6-servitore.py; echo {pag} | base64 -d > $h/g6.html; "
        "echo {pref} | base64 -d > $h/{pr}/user.js; echo {xul} | base64 -d > $h/{pr}/xulstore.json; "
        ": > $h/g6.log; chown -R {c}: $h/{pr} $h/g6-servitore.py $h/g6.html $h/g6.log; set +e; "
        "u=$(id -u {c}); "
        "setsid runuser -u {c} -- python3 $h/g6-servitore.py {p} $h/g6.html $h/g6.log "
        "</dev/null >/dev/null 2>&1 & "
        "d=''; for i in $(seq 1 40); do d=$(ls /run/user/$u 2>/dev/null | "
        "grep -E '^wayland-[0-9]+$' | head -1); [ -n \"$d\" ] && break; sleep 0.5; done; "
        "[ -n \"$d\" ] || {{ echo 'nessun socket wayland'; exit 2; }}; sleep 1; "
        "setsid runuser -u {c} -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=$h firefox-esr --no-remote --new-instance "
        "--profile $h/{pr} http://127.0.0.1:{p}/ "
        "</dev/null >$h/.g6-firefox.log 2>&1 & "
        "for i in $(seq 1 200); do grep -q caricata $h/g6.log && {{ echo accesa; exit 0; }}; "
        "sleep 0.5; done; echo 'la scena non ha detto «caricata»'; tail -5 $h/.g6-firefox.log; "
        "exit 1".format(c=s.chi, p=p, pr=PROFILO, srv=b(SERVITORE), pag=b(pagina()),
                        pref=b(PREFERENZE), xul=b(xul)), 150)
    return c == 0, t


def spegni_servitore(s):
    s.sc.dentro("pkill -f '[g]6-servitore.py %d ' 2>/dev/null; true" % porta_scena(s.o), 30)


def quaderno(s):
    """Le righe di stato della scena (dict), in ordine."""
    _c, t = s.sc.dentro("cat /home/%s/g6.log 2>/dev/null" % s.chi, 30)
    fuori = []
    for r in t.splitlines():
        try:
            fuori.append(json.loads(r))
        except ValueError:
            pass
    return fuori


def ultimo_stato(s, fresco_s=8.0):
    """L'ultima riga del quaderno, ⛔ solo se FRESCA (la scena batte ogni 2 s):
    una riga vecchia e' lo stato di un programma che forse non c'e' piu'."""
    q = quaderno(s)
    if not q:
        return None
    r = q[-1]
    if time.time() * 1000 - r.get("t", 0) > fresco_s * 1000:
        return None
    return r


def processi(s):
    """{nome: [pid, ...]} dei programmi della sessione dell'inquilino che contano."""
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
    """Il PID piu' basso di firefox-esr: il processo padre della scena."""
    v = pr.get("firefox-esr") or []
    try:
        return min(int(x) for x in v)
    except ValueError:
        return None


# ═══════════════════════════════════════════════════════════════════════════
#  LA FOTOGRAFIA: la finestra ciano e la striscia
# ═══════════════════════════════════════════════════════════════════════════
def _vicino(p, c, toll=TOLLERANZA):
    return abs(p[0] - c[0]) <= toll and abs(p[1] - c[1]) <= toll and abs(p[2] - c[2]) <= toll


def immagine(png, largo=960):
    """PIL RGB ridotta a `largo` (vicino piu' vicino): i conti in puro python."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    if im.size[0] > largo:
        im = im.resize((largo, max(1, round(im.size[1] * largo / im.size[0]))),
                       Image.NEAREST)
    return im


def trova_ciano(im):
    """Il rettangolo ciano (la vista della scena): (x0,y0,x1,y1) o (None, motivo)."""
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
        return None, "nessun pixel ciano: la finestra della scena non si vede"
    xs = [x for x, n in enumerate(col) if n >= 0.3 * max(col)]
    ys = [y for y, n in enumerate(rig) if n >= 0.3 * max(rig)]
    r = (min(xs), min(ys), max(xs), max(ys))
    if (r[2] - r[0]) < 0.05 * w or (r[3] - r[1]) < 0.05 * h:
        return None, "il ciano c'e' ma e' piccolo (%s): non e' la finestra" % (r,)
    return r, ""


def nome_colore(p):
    best, dist = None, 10 ** 9
    for k, c in list(TAVOLOZZA.items()) + [("_", VUOTO), ("?", (255, 255, 255))]:
        d = max(abs(p[0] - c[0]), abs(p[1] - c[1]), abs(p[2] - c[2]))
        if d < dist:
            best, dist = k, d
    return best if dist <= TOLLERANZA else "!"


def leggi_striscia(im, r):
    """Il testo letto dalla striscia dentro il rettangolo ciano `r`.
    Torna (testo, dettaglio): «_» = casella vuota, «!» = colore sconosciuto."""
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
    """⭐ Fotografa la tela, trova la finestra, legge la striscia.
    Torna dict {finestra, letto, crudo, foto, perche, png}."""
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
    """Fotografa finche' la striscia dice `voluto` (o il tetto)."""
    fine = time.time() + tetto
    v = None
    fallite = 0
    while True:
        v = guarda_la_scena(s, nome)
        if v.get("png") is None:
            fallite += 1
        # ⚠ `[M]` 25 set 2026, gnome+Chrome sotto carico: la fotografia CDP di una
        #   sessione appena rinata va in «timed out» (60 s l'una) ⇒ dopo due
        #   fallite di fila si smette: la prova resta sotto i 10 minuti
        if v.get("letto") == voluto or time.time() >= fine or fallite >= 2:
            return v
        time.sleep(1.0)


# ═══════════════════════════════════════════════════════════════════════════
#  L'INPUT VERO: il clic sulla finestra, i tasti
# ═══════════════════════════════════════════════════════════════════════════
def sveglia(s):
    """Un ESC vero (GNOME nasce nella panoramica: la scena starebbe in piccolo)."""
    try:
        geo = s.geometria()
        if geo:
            return S.C21.sveglia(s.g, geo)
    except Exception as e:                       # noqa: BLE001
        return "⚠ %s" % e
    return "⚠ niente geometria"


def clic_sulla_scena(s, v):
    """Un clic VERO del browser sul ciano della scena (le da' il fuoco)."""
    geo = s.geometria()
    if not geo or not v.get("finestra"):
        return "⚠ niente geometria o finestra"
    pw, ph = v["misura"]
    x0, y0, x1, y1 = v["finestra"]
    # un punto del ciano sotto la striscia
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
    return "clic in (%d,%d) del desktop" % (X, Y)


def scrivi_la_base(s, v, testo, prove=3):
    """⭐ La PREPARAZIONE (non la funzione guardata): clic sulla scena, testo
    scritto, letto in foto.  `[M]` 24 set 2026, KDE sotto carico 50: una volta
    su una sono arrivate 2 lettere su 4 (il fuoco arriva tardi) ⇒ si pulisce
    (Ctrl+A, Backspace) e si riscrive, fino a `prove` volte.  Torna (v, note)."""
    note = []
    for k in range(prove):
        cl = clic_sulla_scena(s, v)
        if k:
            C23.manda(s.g, C23.PULISCI)
            time.sleep(0.5)
        time.sleep(0.7)
        C23.manda(s.g, C23.scrivi(testo))
        v2 = aspetta_testo(s, testo, "scritto-prima", tetto=10)
        note.append("prova %d: %s, letto «%s»" % (k + 1, cl, v2.get("letto")))
        if v2.get("letto") == testo:
            return v2, note
        if v2.get("finestra"):
            v = v2
    return v2, note


def scrivi(s, testo):
    C23.manda(s.g, C23.scrivi(testo))


# ═══════════════════════════════════════════════════════════════════════════
#  IL BROWSER: chiuderlo, ucciderlo, riaprirlo a una misura
# ═══════════════════════════════════════════════════════════════════════════
def albero(pid):
    """Il PID e tutti i discendenti (da /proc)."""
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
    """⛔ kill -9 del browser e di tutti i suoi processi: nessun congedo.
    Torna quanti processi."""
    g = s.g
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
    # il guscio della guida: niente congedo, solo i resti su disco
    import shutil
    prof = getattr(g, "profilo", None)
    if prof:
        shutil.rmtree(prof, ignore_errors=True)
    s.g = None
    return len(tutti)


def accendi_a_misura(s, largo, alto):
    """Riaccende il browser della sessione alla misura chiesta.  4K = massimizzata
    (come `Sessione`); il resto: Chrome nasce con `--window-size`, Firefox con
    `SetWindowRect`.  Torna la misura riletta."""
    o = s.o
    vecchio = list(S.VERI.FINESTRA)
    ol, oa = o.largo, o.alto
    try:
        if o.browser == "chrome" and (largo, alto) != (3840, 2160):
            S.VERI.FINESTRA[:] = [largo, alto]
            o.largo = 0                           # niente «massimizzata»
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
    """Entra; se il posto e' ancora occupato (0x0F, il fantasma di §5.1) riprova
    ogni 3 s fino al tetto.  Torna (ok, motivo, rifiuti, secondi)."""
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
    """I campi della pagina: tela (buffer), vista, rettangolo, esito, scala."""
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
    """Dopo il riattacco la tela puo' cambiare ancora (`ADATTA_TELA` → `TELA`):
    si aspetta che il buffer resti uguale per 4 s."""
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
    """La firma dei bordi della foto: colore medio delle 6 righe in alto e in
    basso (tutte, e in SECCHI fette di larghezza), la frazione di NERO nella
    fascia del 3 % a destra e in basso, e le fette COPERTE dalla finestra della
    scena `r` (± 3 %): ⚠ `[M]` 25 set 2026, xfce: rimpicciolendo il desktop la
    finestra resta dov'era e arriva al bordo — non e' il pannello che manca."""
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

    # la finestra (con cornice e barre: il 3 % di margine, e 12 % in alto per
    # le barre del browser) non conta per la fascia nera
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
