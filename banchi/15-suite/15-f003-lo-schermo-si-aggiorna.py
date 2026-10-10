#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f003 — F-003 THE SCREEN UPDATE

    python3 15-f003-lo-schermo-si-aggiorna.py --scatola kde --browser chrome [--guasto]
    python3 15-f003-lo-schermo-si-aggiorna.py --certifica

The scene: C21's known window (NORMAL `firefox-esr` in the session, page
with a CYAN background and a YELLOW box, 45 % x 55 % of the screen, size fixed
in the profile) — plus a COUNTER: 15 white/black cells at the bottom of the
page writing in binary n = floor(Date.now() / 200 ms) mod 4096, that is
the page CHANGES every 200 ms.  (White guard, black guard, 12 bits, parity.)
⭐ The counter is a clock: `firefox-esr` in the box and the bench run
on the SAME machine (podman, same clock), so every photo also says
HOW old the image it shows is.

F-003, four parts in a row (like a real user), all from the PHOTO
of the canvas at full resolution:
  apre     first the photo has no cyan; the window is opened ⇒ the photo shows it
           (the cyan rectangle, at least 70 % as wide as what was requested)
  cambia   6 s of photos one after the other: every photo reads the counter, and
           the image must not be older than TETTO_MS (1 s) relative to
           the instant the photo was REQUESTED (the measurement favours the
           product: if it comes out old, it surely is); no photo equal to the
           previous one if >= 400 ms passed between the two; at least 3 different
           values; at most a quarter of the photos unreadable
  sposta   the window is dragged by the TITLE BAR with the browser's mouse
           (real events: Marionette / CDP), by +320,+120 px: the bar is not
           in the same place on all desktops (Firefox with the tabs in the
           bar, or the desktop's bar above), so a ladder of
           grips above the cyan is tried, in the centre, stopping at the first one that moves
           ⇒ the photo shows the cyan ELSEWHERE (moved by at least 100 px), of the
           same size (±8 px)
  chiude   the window is closed (`firefox-esr` terminated in the session)
           ⇒ within 10 s the photo has no more cyan

FAULT («the old photo»): each part is re-judged on the photo from BEFORE the
change — the opening on the photo without the window, the rapid changes on the FIRST
photo repeated with the real instants, the move on the photo from before the
gesture, the closing on the last photo with the window open.  All four
must give red.

⚠ The judgment of «cambia» is a CAP on the delay (1 s), not the latency: the
  latency is measured by phase 16.
"""
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

C21 = S.C21
F011 = S._carica("f011", os.path.join(S.QUI, "15-f011-la-tela-all-attacco.py"))
FUNZIONI = ("F-003",)

PERIODO_MS = 200
BIT = 12
MODULO = 1 << BIT
CELLE = 2 + BIT + 1                 # white guard, black guard, 12 bits, parity
CELLA_X0, CELLA_PASSO, CELLA_L = 0.03, 0.063, 0.05      # fractions of the page
CELLA_Y0, CELLA_A = 0.62, 0.24
TETTO_MS = 1000.0                   # the image no older than this
RAPIDI_S = 6.0
FOTO_MIN = 8
RAPIDI_MAX_S = 30.0
FERMA_MS = 400.0                    # two photos this far apart must differ
SPOSTA = (320, 120)                 # the drag, in desktop pixels
PRESE_DY = (-62, -70, -54, -80, -100, -110, -46, -90, -120, -130)
SPOSTATA_MIN = 100
STESSA_MISURA = 8
CHIUSA_S = 10.0
APERTURA_S = 120.0                # [M] 24 Sep 2026, load 51: firefox-esr takes ~50 s to appear
CIANO_ASSENTE = 0.001               # share of cyan pixels below which «it is not there»

PAGINA = C21.PAGINA.replace("REMOTIX C21", "REMOTIX F-003") + r"""
<script>
(function () {
  const N = %(celle)d, B = %(bit)d, celle = [];
  for (let i = 0; i < N; i++) {
    const d = document.createElement('div');
    d.style.cssText = 'position:absolute;top:%(y0)s%%;height:%(a)s%%;width:%(l)s%%;left:'
      + (%(x0)s + i * %(passo)s) + '%%;background:#000';
    document.body.appendChild(d); celle.push(d);
  }
  let ultimo = -1;
  function giro() {
    const n = Math.floor(Date.now() / %(periodo)d) %% %(modulo)d;
    if (n === ultimo) return;
    ultimo = n;
    const b = [1, 0];
    let p = 0;
    for (let k = B - 1; k >= 0; k--) { const v = (n >> k) & 1; b.push(v); p ^= v; }
    b.push(p);
    for (let i = 0; i < N; i++) celle[i].style.background = b[i] ? '#fff' : '#000';
  }
  giro();
  setInterval(giro, 20);
})();
</script>
""" % {"celle": CELLE, "bit": BIT, "y0": CELLA_Y0 * 100, "a": CELLA_A * 100,
       "l": CELLA_L * 100, "x0": CELLA_X0 * 100, "passo": CELLA_PASSO * 100,
       "periodo": PERIODO_MS, "modulo": MODULO}


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def bit_di(n):
    b = [1, 0]
    p = 0
    for k in range(BIT - 1, -1, -1):
        v = (n >> k) & 1
        b.append(v)
        p ^= v
    return b + [p]


def centri_celle(rett):
    """rett = [x0, y0, x1, y1] of the page in the photo ⇒ [(x, y, half_w, half_h)]."""
    x0, y0, x1, y1 = rett
    w, h = x1 - x0 + 1, y1 - y0 + 1
    y = y0 + (CELLA_Y0 + CELLA_A / 2) * h
    return [(x0 + (CELLA_X0 + i * CELLA_PASSO + CELLA_L / 2) * w, y,
             CELLA_L * w * 0.25, CELLA_A * h * 0.25) for i in range(CELLE)]


def leggi_contatore(im, rett):
    """(n | None, reason) from the page's counter in the photo `im` (PIL RGB)."""
    from PIL import ImageStat
    b = []
    for x, y, ml, ma in centri_celle(rett):
        box = (int(x - ml), int(y - ma), int(x + ml) + 1, int(y + ma) + 1)
        m = ImageStat.Stat(im.crop(box).convert("L")).mean[0]
        if m < 70:
            b.append(0)
        elif m > 185:
            b.append(1)
        else:
            return None, "cell at (%d,%d) grey (%.0f): it is neither white nor black" % (x, y, m)
    if b[0] != 1 or b[1] != 0:
        return None, "the guards are not there (%s): the counter is not where I say" % b[:2]
    if sum(b[2:2 + BIT]) % 2 != b[-1]:
        return None, "wrong parity: %s" % "".join(map(str, b))
    n = 0
    for v in b[2:2 + BIT]:
        n = (n << 1) | v
    return n, ""


def ritardo_ms(n, t_ms):
    """How old, at instant `t_ms` (epoch ms), the image showing
    `n` is: t - (end of n's period).  Negative = n comes from the future (±1 period
    = clock)."""
    pieno = int(t_ms // PERIODO_MS)
    k = (pieno - n) % MODULO
    if k > MODULO // 2:
        k -= MODULO
    n_pieno = pieno - k
    return t_ms - (n_pieno + 1) * PERIODO_MS


def giudica_rapidi(letture):
    """letture = [(t_before_ms, t_after_ms, n | None, reason)] ⇒ (outcome, reason, details)."""
    if len(letture) < 4:
        return S.BLOCKED, "only %d photos: too few to judge" % len(letture), []
    righe, guai = [], []
    buone = [(tp, td, n) for tp, td, n, _m in letture if n is not None]
    illeggibili = len(letture) - len(buone)
    for tp, td, n, m in letture:
        if n is None:
            righe.append("unreadable: %s" % m)
            continue
        r = ritardo_ms(n, tp)
        righe.append("n=%d delay %+.0f ms" % (n, r))
        if r > TETTO_MS:
            guai.append("photo %.0f ms old (n=%d, cap %.0f)" % (r, n, TETTO_MS))
        if ritardo_ms(n, td) < -PERIODO_MS:
            guai.append("n=%d comes from the future (%.0f ms): clock?" % (n, ritardo_ms(n, td)))
    for (tp0, _td0, n0), (tp1, _td1, n1) in zip(buone, buone[1:]):
        if n1 == n0 and tp1 - tp0 >= FERMA_MS:
            guai.append("two photos %.0f ms apart show the same n=%d: STILL"
                        % (tp1 - tp0, n0))
    diversi = len({n for _a, _b, n in buone})
    if illeggibili * 4 > len(letture):
        guai.append("%d photos of %d with the counter unreadable" % (illeggibili, len(letture)))
    if diversi < 3:
        guai.append("only %d different values in %d photos" % (diversi, len(letture)))
    if guai:
        return S.FAIL, "; ".join(guai[:4]) + (" (+%d)" % (len(guai) - 4) if len(guai) > 4
                                               else ""), righe
    rit = [ritardo_ms(n, tp) for tp, _td, n in buone]
    return S.PASS, ("%d photos in %.1f s, %d different values, maximum delay %.0f ms (cap %.0f)"
                    % (len(letture), (letture[-1][0] - letture[0][0]) / 1000.0, diversi,
                       max(rit), TETTO_MS)), righe


def frazione_ciano(im):
    p = im.resize((max(1, im.size[0] // 4), max(1, im.size[1] // 4)))
    px = list(p.getdata())
    n = sum(1 for q in px if C21._vicino(q, C21.CIANO))
    return n / float(len(px))


CAMBIATO_MIN = 0.005                # share of changed pixels: «something appeared»


def cambiato(im_a, im_b):
    """The share of pixels (at 1/4) that differ by more than 40 in a channel."""
    if im_a.size != im_b.size:
        return 1.0
    from PIL import ImageChops
    w, h = im_a.size
    d = ImageChops.difference(im_a, im_b).resize((max(1, w // 4), max(1, h // 4)))
    px = list(d.getdata())
    return sum(1 for q in px if max(q) > 40) / float(len(px))


def trova(im):
    """The test window in the photo (`C21.trova_finestra`): (dict | None, reason)."""
    w, h = im.size
    f, m = C21.trova_finestra(w, h, list(im.getdata()), passo=max(1, w // 960))
    if f:
        f["foto"] = [w, h]
        f["rett"] = [f["ciano"][0], f["ciano"][1], f["destro"], f["ciano"][3]]
    return f, m


def giudica_apertura(f, largo_px):
    if not f:
        return S.FAIL, "the opened window is not seen in the photo"
    l = f["rett"][2] - f["rett"][0] + 1
    if l < 0.7 * largo_px:
        return S.FAIL, "the cyan is there but it is %d px wide (%d requested)" % (l, largo_px)
    return S.PASS, "the window is seen: cyan %s" % f["rett"]


def giudica_spostamento(r0, r1):
    """r0, r1 = [x0,y0,x1,y1] in the photo (or r1 None) ⇒ (outcome, reason)."""
    if not r1:
        return S.FAIL, "after the gesture the window is no longer seen"
    dx, dy = r1[0] - r0[0], r1[1] - r0[1]
    dl = (r1[2] - r1[0]) - (r0[2] - r0[0])
    da = (r1[3] - r1[1]) - (r0[3] - r0[1])
    if abs(dl) > STESSA_MISURA or abs(da) > STESSA_MISURA:
        return S.FAIL, "the window changed size (%+d,%+d): it is not a move" % (dl, da)
    if (dx * dx + dy * dy) ** 0.5 < SPOSTATA_MIN:
        return S.FAIL, "the window is still (%+d,%+d px)" % (dx, dy)
    return S.PASS, "the window moved by (%+d,%+d) px, same size" % (dx, dy)


def giudica_chiusura(quota):
    if quota < CIANO_ASSENTE:
        return S.PASS, "in the photo there is no more cyan (%.3f %%)" % (100 * quota)
    return S.FAIL, "the closed window is still seen: cyan on %.1f %% of the photo" % (100 * quota)


def complessivo(parti):
    es = [e for _p, e, _m in parti]
    return S.FAIL if S.FAIL in es else (S.BLOCKED if S.BLOCKED in es else S.PASS)


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION
# ═══════════════════════════════════════════════════════════════════════════
def _foto_finta(n, rett=(100, 80, 899, 579), w=1000, h=700, fondo=(40, 40, 90)):
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h), fondo)
    d = ImageDraw.Draw(im)
    x0, y0, x1, y1 = rett
    d.rectangle(rett, fill=C21.CIANO)
    pw, ph = x1 - x0 + 1, y1 - y0 + 1
    d.rectangle((x0 + 0.06 * pw, y0 + 0.08 * ph, x0 + 0.40 * pw, y0 + 0.38 * ph), fill=C21.GIALLO)
    for i, v in enumerate(bit_di(n)):
        cx = x0 + (CELLA_X0 + i * CELLA_PASSO) * pw
        cy = y0 + CELLA_Y0 * ph
        d.rectangle((cx, cy, cx + CELLA_L * pw, cy + CELLA_A * ph),
                    fill=(255, 255, 255) if v else (0, 0, 0))
    return im


def certifica():
    guai = []

    def ok(c, cosa):
        print("%s %s" % ("⭐" if c else "⛔", cosa))
        if not c:
            guai.append(cosa)
    for n in (0, 1, 1234, 4095):
        im = _foto_finta(n)
        f, m = trova(im)
        ok(f is not None, "the fake window is found (%s)" % (f["rett"] if f else m))
        v, m = leggi_contatore(im, f["rett"]) if f else (None, m)
        ok(v == n, "counter %d reads %s %s" % (n, v, m))
    im = _foto_finta(77)
    from PIL import ImageDraw
    ImageDraw.Draw(im).rectangle((100, 400, 899, 579), fill=(128, 128, 128))
    ok(leggi_contatore(im, [100, 80, 899, 579])[0] is None, "counter covered ⇒ unreadable")
    t = 1_790_000_000_000.0
    n = int(t // PERIODO_MS) % MODULO
    ok(abs(ritardo_ms(n, t + 150) - (-50)) < 1e-6, "delay in the same period: -50 ms")
    ok(abs(ritardo_ms((n - 5) % MODULO, t) - 800) < 1e-6, "delay of 5 periods: 800 ms")
    vive = [(t + i * 700, t + i * 700 + 300, int((t + i * 700 - 150) // PERIODO_MS) % MODULO, "")
            for i in range(9)]
    e, m, _ = giudica_rapidi(vive)
    ok(e == S.PASS, "real rapid changes ⇒ PASS (%s)" % m)
    ferme = [(tp, td, vive[0][2], "") for tp, td, _n, _m in vive]
    e, m, _ = giudica_rapidi(ferme)
    ok(e == S.FAIL, "the first photo repeated (fault) ⇒ FAIL (%s)" % m[:90])
    lente = [(tp, td, int((tp - 1500) // PERIODO_MS) % MODULO, "") for tp, td, _n, _m in vive]
    e, m, _ = giudica_rapidi(lente)
    ok(e == S.FAIL, "images 1.5 s old ⇒ FAIL")
    e, _m, _ = giudica_rapidi(vive[:2])
    ok(e == S.BLOCKED, "only two photos ⇒ BLOCKED")
    ok(giudica_spostamento([10, 10, 500, 400], [330, 130, 820, 520])[0] == S.PASS, "moved ⇒ PASS")
    ok(giudica_spostamento([10, 10, 500, 400], [10, 10, 500, 400])[0] == S.FAIL, "still ⇒ FAIL")
    ok(giudica_spostamento([10, 10, 500, 400], [10, 10, 820, 400])[0] == S.FAIL,
       "widened ⇒ FAIL (it is not a move)")
    from PIL import Image
    ok(giudica_chiusura(frazione_ciano(Image.new("RGB", (400, 300), (40, 40, 90))))[0] == S.PASS,
       "no cyan ⇒ closed")
    ok(giudica_chiusura(frazione_ciano(_foto_finta(3)))[0] == S.FAIL, "cyan ⇒ not closed")
    ok(giudica_apertura(None, 800)[0] == S.FAIL, "no window ⇒ opening FAIL")
    print("⭐ certification green" if not guai else "⛔ %d problems" % len(guai))
    return 0 if not guai else 1


# ═══════════════════════════════════════════════════════════════════════════
#  INSIDE THE PAGE AND IN THE BOX
# ═══════════════════════════════════════════════════════════════════════════
JS_OSSERVA = r"""
(function () {
  if (window.__F003__) return;
  const C = window.__F003__ = { giu: 0, su: 0, premuti: 0 };
  addEventListener('mousedown', function () { C.giu++; }, true);
  addEventListener('mouseup', function () { C.su++; }, true);
  /* ⚠ Since 2 Oct 2026 the page's click comes from `pointerdown` and the compatibility
     `mouse*` events are no longer born: the pointer events are counted too (like C22). */
  addEventListener('pointerdown', function (e) { if (e.pointerType !== 'touch') C.giu++; }, true);
  addEventListener('pointerup', function (e) { if (e.pointerType !== 'touch') C.su++; }, true);
  addEventListener('pointermove', function (e) { if (e.buttons & 1) C.premuti++; }, true);
})();
"""
JS_AZZERA = "const C=window.__F003__; if(!C) return false; C.giu=0; C.su=0; C.premuti=0; return true;"
JS_CONTA = r"""
const C = window.__F003__;
const st = window.REMOTIX && REMOTIX.input_classico ? REMOTIX.input_classico.stato() : null;
return C ? { giu: C.giu, su: C.su, premuti: C.premuti,
             spedito: st ? st.ultimo_spedito : null } : null;
"""
PASSI_GESTO = 16


def trascina(g, geo, X, Y, DX, DY):
    """Left button down at (X,Y) of the desktop, dragged by (DX,DY), up."""
    punti = [C21.dal_desktop_al_vetro(geo, X + DX * i / float(PASSI_GESTO),
                                      Y + DY * i / float(PASSI_GESTO))
             for i in range(PASSI_GESTO + 1)]
    if hasattr(g, "cdp"):
        c = g.cdp.chiama
        x0, y0 = punti[0]
        c("Input.dispatchMouseEvent", type="mouseMoved", x=x0, y=y0)
        time.sleep(0.15)
        c("Input.dispatchMouseEvent", type="mousePressed", x=x0, y=y0, button="left",
          buttons=1, clickCount=1)
        time.sleep(0.2)
        for x, y in punti[1:]:
            c("Input.dispatchMouseEvent", type="mouseMoved", x=x, y=y, button="left", buttons=1)
            time.sleep(0.03)
        time.sleep(0.2)
        x, y = punti[-1]
        c("Input.dispatchMouseEvent", type="mouseReleased", x=x, y=y, button="left",
          buttons=0, clickCount=1)
        return
    az = [{"type": "pointerMove", "x": int(round(punti[0][0])), "y": int(round(punti[0][1])),
           "origin": "viewport", "duration": 0},
          {"type": "pause", "duration": 150}, {"type": "pointerDown", "button": 0},
          {"type": "pause", "duration": 200}]
    for x, y in punti[1:]:
        az += [{"type": "pointerMove", "x": int(round(x)), "y": int(round(y)),
                "origin": "viewport", "duration": 0}, {"type": "pause", "duration": 30}]
    az += [{"type": "pause", "duration": 200}, {"type": "pointerUp", "button": 0}]
    g._azioni([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                "actions": az}])


def prepara_la_casa(s, largo, alto):
    """F-003's page in place of C21's (same file name: so
    `C21.accendi_la_finestra` opens it), and C21's Firefox profile."""
    import base64
    b = lambda t: base64.b64encode(t.encode()).decode()       # noqa: E731
    return s.sc.dentro(
        "set -e; h=/home/%(c)s; mkdir -p $h/%(p)s; echo %(pag)s | base64 -d > $h/%(f)s; "
        "echo %(pref)s | base64 -d > $h/%(p)s/user.js; "
        "echo %(xul)s | base64 -d > $h/%(p)s/xulstore.json; chown -R %(c)s: $h/%(p)s $h/%(f)s; "
        "echo pronta" % {"c": s.chi, "p": C21.PROFILO, "f": C21.FILE_PAGINA, "pag": b(PAGINA),
                         "pref": b(C21.PREFERENZE), "xul": b(C21.xulstore(largo, alto))}, 60)


def foto_im(s, nome=None):
    """(png, PIL RGB, t_before_ms, t_after_ms).  Saves if `nome`."""
    from PIL import Image
    tp = time.time() * 1000.0
    if nome:
        png, _dove = s.foto(nome)
    else:
        try:
            png = C21.foto_piena(s.g)
        except Exception:                        # noqa: BLE001
            png = None
    td = time.time() * 1000.0
    if not png:
        return None, None, tp, td
    return png, Image.open(io.BytesIO(png)).convert("RGB"), tp, td


def aspetta_ferma(s, attesa, nome):
    """The window still in two photos in a row: (f, im) or (None, reason).

    ⚠ `[M]` 24 Sep 2026, lxqt under load 50: the moved window was seen
      in every photo but two photos in a row never came back equal within 12 s ⇒
      at the deadline the LAST window seen counts (with `ferma: False`): it is the
      photo, not a «not seen»."""
    fine = time.time() + attesa
    ultima, perche, im, im_u = None, "no photo", None, None
    while time.time() < fine:
        png, im, _tp, _td = foto_im(s)
        if im is None:
            perche = "the canvas cannot be photographed"
            time.sleep(1)
            continue
        f, perche = trova(im)
        if f and ultima and all(abs(a - b) <= 2 for a, b in zip(ultima["rett"], f["rett"])):
            if s.o.evidenze and nome:
                im.save(os.path.join(s.o.evidenze, "%s.png" % nome))
            f["ferma"] = True
            return f, im
        if f:
            ultima, im_u = f, im
        time.sleep(0.8)
    if ultima is not None:
        ultima["ferma"] = False
        if s.o.evidenze and nome:
            im_u.save(os.path.join(s.o.evidenze, "%s-non-ferma.png" % nome))
        return ultima, im_u
    if s.o.evidenze and nome and im is not None:
        im.save(os.path.join(s.o.evidenze, "%s-NON-trovata.png" % nome))
    return None, perche


def processo_vivo(s):
    c, t = s.sc.dentro("pgrep -u %s -f firefox-esr >/dev/null && echo vivo || echo morto" % s.chi,
                       30)
    return "vivo" in (t or "")


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def corpo(o, E):
    with S.Sessione(o, "003", E) as s:
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata(m)
        # ⚠ `[M]` 24 Sep 2026, kde: at the first frame the canvas was still
        #   640x340; the window size arrives later.  We wait for the expected
        #   canvas (the rule is F-011's), or the scene is not the intended one.
        cw, ch, dpr = s.g.js("const d=document.documentElement; "
                             "return [d.clientWidth, d.clientHeight, devicePixelRatio||1];")
        attesa = F011.tela_attesa(cw, ch, dpr)
        fine = time.time() + 40
        geo = None
        while time.time() < fine:
            geo = s.geometria()
            if geo and [geo.get("tl"), geo.get("ta")] == attesa:
                break
            time.sleep(1)
        if not geo:
            raise S.Bloccata("`REMOTIX_PUNTATORE.geometria` is not there")
        if [geo.get("tl"), geo.get("ta")] != attesa:
            raise S.Bloccata("the canvas is %sx%s and not %dx%d after 40 s: the scene is not the "
                             "intended one (F-011 judges it)" % (geo.get("tl"), geo.get("ta"),
                                                                 attesa[0], attesa[1]))
        time.sleep(1.5)
        geo = s.geometria()
        if geo.get("disposizione") != "classico":
            raise S.Bloccata("the page is not in the classic layout (%s): "
                             "dragging with the mouse is not this question" % geo.get("disposizione"))
        print("   canvas %sx%s · wake-up: %s" % (geo["tl"], geo["ta"], C21.sveglia(s.g, geo)),
              flush=True)
        parti, guasti, ev = [], [], []

        # ── 0. the photo before: no cyan ───────────────────────────────────
        time.sleep(1.5)
        png0, im0, _a, _b = foto_im(s, "prima-dell-apertura")
        if im0 is None:
            raise S.Bloccata("the canvas cannot be photographed")
        q0 = frazione_ciano(im0)
        if q0 >= CIANO_ASSENTE:
            raise S.Bloccata("before opening there is already some cyan (%.2f %%): the scene is not "
                             "clean" % (100 * q0))

        # ── 1. OPENS ───────────────────────────────────────────────────────
        largo_f, alto_f = geo["tl"] * 0.45, geo["ta"] * 0.55
        c, t = prepara_la_casa(s, largo_f, alto_f)
        if c != 0:
            raise S.Bloccata("the home does not get ready: %s" % (t or "")[-200:])
        ok, t = C21.accendi_la_finestra(s.sc, s.chi)
        if not ok:
            raise S.Bloccata("firefox-esr does not start: %s" % (t or "")[-200:])
        t_ap = time.time()
        f1, im1 = aspetta_ferma(s, APERTURA_S, "aperta")
        if not f1:
            _c, log = s.sc.dentro("tail -n 40 /home/%s/.c21-firefox.log" % s.chi, 30)
            ev.append(s.salva_testo("firefox-esr-nella-sessione.log", log or ""))
            _p, im_x, _a, _b = foto_im(s, "apertura-non-vista")
            nuovo = cambiato(im0, im_x) if im_x is not None else 0.0
            if not processo_vivo(s):
                parti.append(("apre", S.BLOCKED, "firefox-esr did not stay alive: %s" % im1))
            elif nuovo > CAMBIATO_MIN:
                # ⚠ the screen updated (SOMETHING ELSE appeared: a notice,
                #   a preview): the scene is not the one I wanted ⇒ the bench
                parti.append(("apre", S.BLOCKED, "the photo changed (%.1f %% of the pixels) but "
                              "does not show the test page: something else appeared — see the photo "
                              "and the firefox-esr log" % (100 * nuovo)))
            else:
                parti.append(("apre", S.FAIL, "firefox-esr has been alive for %.0f s and the photo is "
                              "IDENTICAL to the one before (%.2f %% of the pixels changed): the "
                              "screen does not update" % (time.time() - t_ap, 100 * nuovo)))
            raise _Fine(parti, [], ev)
        pw, ph = f1["foto"]
        largo_foto = largo_f * geo["sx"] * pw / geo["bw"]       # desktop ⇒ photo
        e, m = giudica_apertura(f1, largo_foto)
        if e == S.FAIL and f1:
            e = S.BLOCKED
            m = ("the cyan is %d px wide and I asked for %d: a preview (overview?), "
                 "not the window" % (f1["rett"][2] - f1["rett"][0] + 1, largo_f))
        parti.append(("apre", e, m + " (in %.1f s)" % (time.time() - t_ap)))
        f0, _ = trova(im0)
        guasti.append(("apre", giudica_apertura(f0, largo_foto)))
        if e != S.PASS:
            raise _Fine(parti, guasti)

        # ── 2. CHANGES: the counter, for RAPIDI_S seconds ─────────────────
        v0, mv = leggi_contatore(im1, f1["rett"])
        if v0 is None:
            parti.append(("cambia", S.BLOCKED, "the counter cannot be read in the still "
                          "window: %s" % mv))
        else:
            # ⛔ a FAIL is confirmed by redoing it: if the first series is red a
            #   second one is done, and the red counts only if both are
            #   (`[M]` 24 Sep 2026, lxqt, load 50: ONE photo 1.5 s old)
            serie = []
            for giro in range(2):
                letture, prima_im = [], None
                t_via = time.time()
                i = 0
                # ⚠ `[M]` 25 Sep 2026, gnome under load: a 4K Firefox photo
                #   cost 2-3 s, and in 6 s only 2 came ⇒ at least FOTO_MIN photos,
                #   up to RAPIDI_MAX_S
                while (time.time() - t_via < RAPIDI_S or len(letture) < FOTO_MIN) \
                        and time.time() - t_via < RAPIDI_MAX_S:
                    _png, im, tp, td = foto_im(s)
                    if im is None:
                        continue
                    n, mn = leggi_contatore(im, f1["rett"])
                    letture.append((tp, td, n, mn))
                    if prima_im is None:
                        prima_im = im
                    if o.evidenze:
                        x0, y0, x1, y1 = f1["rett"]
                        im.crop((x0, y0 + int(0.55 * (y1 - y0)), x1, y1)).save(
                            os.path.join(o.evidenze, "rapida-%d-%02d-n%s.png" % (giro, i, n)))
                    i += 1
                e, m, righe = giudica_rapidi(letture)
                ev.append(s.salva_testo("rapide-%d.txt" % giro, righe))
                serie.append((e, m, letture, prima_im))
                print("   rapid changes, series %d: %s %s" % (giro + 1, e, m), flush=True)
                if e == S.PASS:
                    break
            e, m, letture, prima_im = serie[-1]
            if len(serie) > 1:
                m = "series 1: %s %s · series 2: %s" % (serie[0][0], serie[0][1], m)
            parti.append(("cambia", e, m))
            # the fault: the FIRST photo for all, with the real instants
            if letture and prima_im is not None:
                n0, m0 = leggi_contatore(prima_im, f1["rett"])
                vecchie = [(tp, td, n0, m0) for tp, td, _n, _m in letture]
                ge, gm, _ = giudica_rapidi(vecchie)
                guasti.append(("cambia", (ge, gm)))

        # ── 3. MOVES: by the title bar ─────────────────────────────────────
        s.g.js(S.VERI._inietta(JS_OSSERVA))
        r0 = f1["rett"]
        f_prima, im_prima = f1, im1
        esito_sp = None
        tentativi = []
        for dy in PRESE_DY:
            Xc, Yt = C21.dalla_foto_al_desktop(geo, pw, ph, (r0[0] + r0[2]) / 2.0 + 0.5,
                                               r0[1] + 0.5)
            X, Y = Xc, Yt + dy
            if Y < 2:
                continue
            if X + SPOSTA[0] + 4 >= geo["tl"] or Y + SPOSTA[1] + 4 >= geo["ta"]:
                esito_sp = (S.BLOCKED, "there is no room to move the window")
                break
            s.g.js(JS_AZZERA)
            trascina(s.g, geo, X, Y, SPOSTA[0], SPOSTA[1])
            time.sleep(0.4)
            n = s.g.js(JS_CONTA) or {}
            sp = n.get("spedito") or [-1, -1]
            if n.get("giu", 0) < 1 or n.get("su", 0) < 1 or n.get("premuti", 0) < PASSI_GESTO // 2:
                esito_sp = (S.BLOCKED, "the browser did not deliver the gesture to the page (%s)" % n)
                break
            if abs(sp[0] - int(X + SPOSTA[0])) > 2 or abs(sp[1] - int(Y + SPOSTA[1])) > 2:
                esito_sp = (S.BLOCKED, "the page sent (%s,%s) instead of (%d,%d): the "
                            "pointer is not where I say" % (sp[0], sp[1], X + SPOSTA[0],
                                                           Y + SPOSTA[1]))
                break
            f2, im2 = aspetta_ferma(s, 20, "dopo-presa%+d" % dy)
            if not f2:
                tentativi.append("%+d: the window is no longer seen (%s)" % (dy, im2))
                esito_sp = (S.FAIL if processo_vivo(s) else S.BLOCKED,
                            "grip %+d px above the page: after the gesture the window is no longer "
                            "seen (%s)" % (dy, im2))
                break
            e, m = giudica_spostamento(r0, f2["rett"])
            if not f2.get("ferma", True):
                m += " (last photo: it did not stay still in two photos in a row)"
            tentativi.append("%+d: %s" % (dy, m))
            print("   grip %+d px above the page → %s" % (dy, m), flush=True)
            if e == S.PASS:
                esito_sp = (S.PASS, "grip %+d px above the page: %s" % (dy, m))
                guasti.append(("sposta", giudica_spostamento(r0, f_prima["rett"])))
                f_dopo, im_dopo = f2, im2
                break
            # resized or still: start again from the window as it is now
            r0, f_prima, im_prima = f2["rett"], f2, im2
            time.sleep(0.6)
        if esito_sp is None:
            esito_sp = (S.FAIL, "in none of the %d grips above the page did the window "
                        "move: %s" % (len(tentativi), "; ".join(tentativi[-3:])))
        parti.append(("sposta", esito_sp[0], esito_sp[1]))
        if esito_sp[0] != S.PASS:
            f_dopo, im_dopo = f_prima, im_prima

        # ── 4. CLOSES ──────────────────────────────────────────────────────
        s.sc.dentro("pkill -u %s -f '[f]irefox-esr' ; echo fatto" % s.chi, 30)
        t_ch = time.time()
        quota, im3, foto_fatte = None, None, 0
        while time.time() - t_ch < CHIUSA_S:
            time.sleep(0.7)
            _png, im_c, _a, _b = foto_im(s)
            if im_c is None:
                continue
            foto_fatte += 1
            im3, quota = im_c, frazione_ciano(im_c)
            if quota < CIANO_ASSENTE:
                break
        if im3 is not None and o.evidenze:
            im3.save(os.path.join(o.evidenze, "chiusa.png"))
        if quota is None:
            # ⚠ `[M]` 25 Sep 2026, gnome/chrome: 60 s without a successful photo
            #   (the browser under load): I did not look, it is not a «seen»
            parti.append(("chiude", S.BLOCKED, "after the closing no photo succeeded in "
                          "%.0f s" % (time.time() - t_ch)))
        elif quota >= CIANO_ASSENTE and processo_vivo(s):
            parti.append(("chiude", S.BLOCKED, "firefox-esr did not close (pkill)"))
        else:
            e, m = giudica_chiusura(quota)
            parti.append(("chiude", e, m + " (after %.1f s, %d photos)" % (time.time() - t_ch,
                                                                       foto_fatte)))
        guasti.append(("chiude", giudica_chiusura(frazione_ciano(im_dopo))))
        raise _Fine(parti, guasti, ev)


class _Fine(Exception):
    def __init__(self, parti, guasti=None, ev=None):
        super().__init__("end")
        self.parti, self.guasti, self.ev = parti, guasti or [], ev or []


def corpo_e_giudizio(o, E):
    try:
        corpo(o, E)
    except _Fine as f:
        es = complessivo(f.parti)
        testo = " · ".join("%s %s: %s" % (p, e, m) for p, e, m in f.parti)
        guai = [x for x in f.parti if x[1] != S.PASS]
        ev = [p for p in f.ev if p]
        if o.evidenze:
            ev.append(o.evidenze)
        E.metti("F-003", es, testo if es != S.PASS else
                "opens, changes, moves, closes: all the photos follow the screen",
                atteso="the photo shows the open window; the new counter (≤ %.0f ms) in every "
                       "photo of %d s; the window elsewhere after the drag; no "
                       "window after the closing" % (TETTO_MS, RAPIDI_S),
                osservato=testo, evidenze=ev, parti={p: [e, m] for p, e, m in f.parti},
                guai=[p for p, _e, _m in guai])
        if o.guasto:
            if es != S.PASS:
                E.guasto("F-003", None, "the healthy pass is not green: the «old photo» fault "
                         "is judged only on a healthy pass (%s)" % testo[:200])
                return
            visti = {p: r[0] == S.FAIL for p, r in f.guasti}
            tutti = len(visti) == 4 and all(visti.values())
            E.guasto("F-003", tutti, "photos from BEFORE the change ⇒ %s" % " · ".join(
                "%s %s" % (p, "red" if r[0] == S.FAIL else r[0]) for p, r in f.guasti),
                osservato=" | ".join("%s: %s" % (p, r[1]) for p, r in f.guasti))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo_e_giudizio, certifica))
