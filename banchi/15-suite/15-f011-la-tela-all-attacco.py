#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f011 — F-011 THE CANVAS AT ATTACH

    python3 15-f011-la-tela-all-attacco.py --scatola kde --browser chrome [--guasto]
    python3 15-f011-la-tela-all-attacco.py --certifica

F-011  expected: right after entering, the desktop has the size of the browser WINDOW
       reduced as `tela_da_chiedere()` of `src/pagina.html` (~2130) says:
         vista = floor(clientWidth x dpr) x floor(clientHeight x dpr)
                 (`misura_vista()`, truncated downwards)
         tela  = each side clamped between the limits (320..7680 x 240..4320) and
                 truncated to the multiple of 16 (TELA_L_PASSO = TELA_A_PASSO = 16,
                 cure of 24 Sep 2026: Firefox with hardware decoding
                 drew a green strip on the right and at the bottom)
       and we look in THREE places, which must all say the expected size:
         · the server's FIELD: «the stage answers the canvas — asked WxH,
           OBTAINED WxH» in the box's log (the real desktop took it)
         · the page: the canvas in force (`REMOTIX_PUNTATORE.geometria` tl x ta)
         · the PHOTO of the canvas at full resolution: its size
       and in the photo (two photos, 2 s apart):
         · no GREEN STRIP (0,76,0) in the last 16 columns and rows
           (the green is the decoding of a block of zeros: the historical defect)
         · no BAND at the edges: the outer edge (2 px) uniform AND different
           from the desktop 24 and 40 px further in = a padding, not the
           desktop.  A panel at its edge is uniform but it is the SAME
           colour 24 px inside too (the panels are >= 28 px tall); the background
           reaches the edge continuously.

FAULT (same session, the same real photos, three injections, all must
       give red):
         a) a (0,76,0) strip 8 px wide painted on the right of the real photo
         b) the size expectation shifted by 16 in width
         c) a uniform MAGENTA band 12 px tall painted at the bottom (a colour
            no desktop has: black or white ended up on an identical panel)

⚠ LIMIT: on a black background (XFCE) a BLACK band cannot be told apart from the
  background; the band is seen only if it differs from the desktop next to it.
"""
import io
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNZIONI = ("F-011",)

# ⛔ The same numbers as src/pagina.html ~2127-2129 (verified on 24 Sep 2026)
L_MIN, L_MAX, A_MIN, A_MAX, PASSO = 320, 7680, 240, 4320, 16
VERDE_DIFETTO = (0, 76, 0)
TOLL_VERDE = 24
STRISCIA = 16            # the columns/rows looked at for the green strip
QUOTA_VERDE = 0.5        # a column is «green» if half of its pixels are
ESTERNO = 2              # the thickness of the outer edge looked at
DENTRO = (24, 40)        # where the desktop «next to it» is looked at
UNIFORME_DEV = 4.0       # deviation (per channel) below which the edge is uniform
DIVERSO = 25.0           # mean difference per pixel beyond which it is «something else»

RE_AVUTA = re.compile(r"asked (\d+)x(\d+), OBTAINED (\d+)x(\d+)")


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def tela_attesa(cw, ch, dpr):
    """The rule of `misura_vista()` + `tela_da_chiedere()`."""
    import math
    v = [max(1, int(math.floor(cw * dpr))), max(1, int(math.floor(ch * dpr)))]

    def p(n, lo, hi):
        n = min(hi, max(lo, int(round(n))))
        return n - n % PASSO
    return [p(v[0], L_MIN, L_MAX), p(v[1], A_MIN, A_MAX)]


def striscia_verde(im):
    """(found, description): columns on the right and rows at the bottom dominated by (0,76,0)."""
    w, h = im.size
    trovate = []

    def verde(p):
        return all(abs(p[i] - VERDE_DIFETTO[i]) <= TOLL_VERDE for i in range(3))
    col = im.crop((w - STRISCIA, 0, w, h))
    px = list(col.getdata())
    for c in range(STRISCIA):
        n = sum(1 for y in range(h) if verde(px[y * STRISCIA + c]))
        if n >= QUOTA_VERDE * h:
            trovate.append("column x=%d (%d%%)" % (w - STRISCIA + c, 100 * n // h))
    rig = im.crop((0, h - STRISCIA, w, h))
    px = list(rig.getdata())
    for r in range(STRISCIA):
        n = sum(1 for x in range(w) if verde(px[r * w + x]))
        if n >= QUOTA_VERDE * w:
            trovate.append("row y=%d (%d%%)" % (h - STRISCIA + r, 100 * n // w))
    if trovate:
        return True, "strip (0,76,0): %d lines — %s" % (len(trovate), ", ".join(trovate[:4]))
    return False, "no (0,76,0) strip in the last %d columns and rows" % STRISCIA


def _bordo(im, lato, prof, spessore=ESTERNO):
    w, h = im.size
    if lato == "destra":
        return im.crop((w - prof - spessore, 0, w - prof, h))
    if lato == "sinistra":
        return im.crop((prof, 0, prof + spessore, h))
    if lato == "basso":
        return im.crop((0, h - prof - spessore, w, h - prof))
    return im.crop((0, prof, w, prof + spessore))


def fasce(im):
    """(found: [sides], description) — a uniform edge that is not the desktop."""
    from PIL import ImageChops, ImageStat
    trovate, note = [], []
    for lato in ("destra", "basso", "sinistra", "alto"):
        est = _bordo(im, lato, 0)
        st = ImageStat.Stat(est)
        dev = max(st.stddev)
        diff = []
        for d in DENTRO:
            den = _bordo(im, lato, d)
            diff.append(sum(ImageStat.Stat(ImageChops.difference(est, den)).mean) / 3.0)
        fascia = dev < UNIFORME_DEV and all(x > DIVERSO for x in diff)
        note.append("%s: dev %.1f, diff %s%s" % (lato, dev, "/".join("%.0f" % x for x in diff),
                                                 " ⛔ BAND" if fascia else ""))
        if fascia:
            trovate.append(lato)
    return trovate, "; ".join(note)


def giudica_misure(attesa, avuta_server, pagina, foto):
    """(outcome, reason).  `avuta_server`, `pagina`, `foto`: [w,h] or None."""
    manca = [n for n, v in (("server", avuta_server), ("pagina", pagina), ("foto", foto))
             if not v]
    if manca:
        return S.BLOCKED, "I could not read the size from: %s" % ", ".join(manca)
    sbagli = ["%s %dx%d" % (n, v[0], v[1]) for n, v in
              (("server", avuta_server), ("pagina", pagina), ("foto", foto))
              if list(v) != list(attesa)]
    if sbagli:
        return S.FAIL, ("expected %dx%d, but %s" % (attesa[0], attesa[1], ", ".join(sbagli)))
    return S.PASS, "server, page and photo all say %dx%d (the expected)" % tuple(attesa)


def giudica_foto(im):
    """(outcome, reason) of the photo: green strip and bands."""
    v, dv = striscia_verde(im)
    f, df = fasce(im)
    if v or f:
        return S.FAIL, "%s · bands %s (%s)" % (dv, f or "none", df)
    return S.PASS, "%s · no band (%s)" % (dv, df)


def dipingi_striscia(im, larghezza=8, colore=VERDE_DIFETTO):
    from PIL import ImageDraw
    c = im.copy()
    w, h = c.size
    ImageDraw.Draw(c).rectangle((w - larghezza, 0, w - 1, h - 1), fill=colore)
    return c


def dipingi_fascia_basso(im, spessore=12, colore=(255, 0, 255)):
    """⭐ The injected band is MAGENTA: far from every real desktop (black,
    white, grey, blue).  `[M]` 24 Sep 2026, lxqt: a white band chosen
    by looking 30-60 px above ended up on a light panel and could not be told apart."""
    from PIL import ImageDraw
    c = im.copy()
    w, h = c.size
    ImageDraw.Draw(c).rectangle((0, h - spessore, w - 1, h - 1), fill=colore)
    return c, colore


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION
# ═══════════════════════════════════════════════════════════════════════════
def _desktop_finto(w=800, h=480, pannello=32):
    """A shaded background with a dark panel at the top (with text)."""
    from PIL import Image, ImageDraw
    im = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(im)
    for x in range(w):
        d.line((x, 0, x, h), fill=(30 + x * 150 // w, 60, 120 + x * 100 // w))
    d.rectangle((0, 0, w, pannello - 1), fill=(20, 20, 20))
    for x in range(10, w - 10, 60):
        d.text((x, 10), "12:00", fill=(230, 230, 230))
    return im


def certifica():
    guai = []

    def ok(cond, cosa):
        print("%s %s" % ("⭐" if cond else "⛔", cosa))
        if not cond:
            guai.append(cosa)
    ok(tela_attesa(3838, 2069, 1) == [3824, 2064], "3838x2069 dpr1 ⇒ 3824x2064 (measured on the server)")
    ok(tela_attesa(3840, 2160, 1) == [3840, 2160], "3840x2160 ⇒ itself")
    ok(tela_attesa(653, 400, 1.5) == [976, 592], "653x400 at dpr 1.5 ⇒ 979x600 ⇒ 976x592")
    ok(tela_attesa(100, 100, 1) == [320, 240], "below the minimum ⇒ 320x240")
    ok(tela_attesa(9000, 5000, 1) == [7680, 4320], "above the maximum ⇒ 7680x4320")
    im = _desktop_finto()
    e, m = giudica_foto(im)
    ok(e == S.PASS, "fake desktop with a dark panel at the top ⇒ PASS (%s)" % m)
    e, m = giudica_foto(dipingi_striscia(im))
    ok(e == S.FAIL, "+ (0,76,0) strip 8 px on the right ⇒ FAIL (%s)" % m[:80])
    e, m = giudica_foto(dipingi_striscia(im, 3))
    ok(e == S.FAIL, "+ 3 px strip ⇒ FAIL")
    c, col = dipingi_fascia_basso(im)
    e, m = giudica_foto(c)
    ok(e == S.FAIL, "+ band %s 12 px at the bottom ⇒ FAIL (%s)" % (col, m[-90:]))
    from PIL import Image
    nero = Image.new("RGB", (800, 480))
    e, m = giudica_foto(nero)
    ok(e == S.PASS, "all black (the XFCE background) ⇒ no band: declared limit")
    ok(giudica_misure([3824, 2064], [3824, 2064], [3824, 2064], [3824, 2064])[0] == S.PASS,
       "three sizes equal to the expected ⇒ PASS")
    ok(giudica_misure([3840, 2064], [3824, 2064], [3824, 2064], [3824, 2064])[0] == S.FAIL,
       "expectation shifted by 16 ⇒ FAIL")
    ok(giudica_misure([3824, 2064], None, [3824, 2064], [3824, 2064])[0] == S.BLOCKED,
       "server size not read ⇒ BLOCKED")
    print("⭐ certification green" if not guai else "⛔ %d problems" % len(guai))
    return 0 if not guai else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
JS_FINESTRA = ("const d=document.documentElement; return [d.clientWidth, d.clientHeight, "
               "devicePixelRatio||1, innerWidth, innerHeight];")


def avuta_dal_server(righe):
    ultima = None
    for r in righe:
        m = RE_AVUTA.search(r)
        if m:
            ultima = [int(m.group(3)), int(m.group(4))]
    return ultima


def corpo(o, E):
    from PIL import Image
    with S.Sessione(o, "011", E) as s:
        segno = s.segno_registro()
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata(m)
        cw, ch, dpr, iw, ih = s.g.js(JS_FINESTRA)
        attesa = tela_attesa(cw, ch, dpr)
        print("   window: client %dx%d (inner %dx%d) dpr %s ⇒ expected canvas %dx%d"
              % (cw, ch, iw, ih, dpr, attesa[0], attesa[1]), flush=True)
        # the server: the «OBTAINED» line with the expected size (or the last one, within 20 s)
        fine = time.time() + 20
        avuta, righe = None, []
        while time.time() < fine:
            righe = s.registro_da(segno) if segno is not None else []
            avuta = avuta_dal_server(righe)
            geo = s.geometria() or {}
            if avuta == attesa and [geo.get("tl"), geo.get("ta")] == attesa:
                break
            time.sleep(1)
        time.sleep(2)                     # a few frames at the new size
        geo = s.geometria() or {}
        pagina = [geo.get("tl"), geo.get("ta")] if geo.get("tl") else None
        ev = [s.salva_testo("server-f011.txt", righe)]
        foto = []
        for k in range(2):
            png, dove = s.foto("tela-%d" % k)
            if not png:
                raise S.Bloccata("the canvas cannot be photographed: %s" % dove)
            foto.append(Image.open(io.BytesIO(png)).convert("RGB"))
            ev.append(dove)
            if k == 0:
                time.sleep(2)
        misura_foto = list(foto[-1].size) if dpr == 1 else None
        nota_dpr = "" if dpr == 1 else " (dpr %s: the photo size is not compared)" % dpr
        if dpr != 1:
            misura_foto = pagina
        e1, m1 = giudica_misure(attesa, avuta, pagina, misura_foto)
        g_foto = [giudica_foto(im) for im in foto]
        e2 = S.FAIL if any(x[0] == S.FAIL for x in g_foto) else S.PASS
        m2 = " | ".join("photo %d: %s" % (i, x[1]) for i, x in enumerate(g_foto))
        esito = S.FAIL if S.FAIL in (e1, e2) else (S.BLOCKED if S.BLOCKED in (e1, e2) else S.PASS)
        ragione = "sizes: %s%s · %s" % (m1, nota_dpr, m2)
        E.metti("F-011", esito, ragione if esito != S.PASS else "canvas %dx%d like the window "
                "(%dx%d, dpr %s), no green strip, no bands" % (
                    attesa[0], attesa[1], cw, ch, dpr),
                atteso="canvas %dx%d (client %dx%d at a multiple of 16), no (0,76,0) at the edges, "
                       "background up to the edge" % (attesa[0], attesa[1], cw, ch),
                osservato=ragione, evidenze=ev + [s.salva_console()])

        if o.guasto:
            if e1 != S.PASS or e2 != S.PASS:
                E.guasto("F-011", None, "the healthy pass is not green: the fault is not injected "
                         "(%s)" % ragione[:200])
                return
            im = foto[-1]
            ga = giudica_foto(dipingi_striscia(im))
            gb = giudica_misure([attesa[0] + 16, attesa[1]], avuta, pagina, misura_foto)
            fc, colore = dipingi_fascia_basso(im)
            gc = giudica_foto(fc)
            if o.evidenze:
                p = os.path.join(o.evidenze, "guasto-striscia-e-fascia.png")
                dipingi_fascia_basso(dipingi_striscia(im))[0].save(p)
            visti = [ga[0] == S.FAIL, gb[0] == S.FAIL, gc[0] == S.FAIL]
            E.guasto("F-011", all(visti),
                     "strip (0,76,0) 8 px ⇒ %s · expected +16 ⇒ %s · band %s 12 px at the bottom "
                     "⇒ %s" % (ga[0], gb[0], colore, gc[0]),
                     osservato="a) %s | b) %s | c) %s" % (ga[1][:160], gb[1], gc[1][-200:]))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
