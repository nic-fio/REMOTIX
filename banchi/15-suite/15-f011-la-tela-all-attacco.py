#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f011 — F-011 LA TELA ALL'ATTACCO

    python3 15-f011-la-tela-all-attacco.py --scatola kde --browser chrome [--guasto]
    python3 15-f011-la-tela-all-attacco.py --certifica

F-011  atteso: appena entrati, il desktop ha la misura della FINESTRA del browser
       ridotta come dice `tela_da_chiedere()` di `src/pagina.html` (~2130):
         vista = floor(clientWidth x dpr) x floor(clientHeight x dpr)
                 (`misura_vista()`, si tronca in giu')
         tela  = ogni lato stretto fra i limiti (320..7680 x 240..4320) e
                 troncato al multiplo di 16 (TELA_L_PASSO = TELA_A_PASSO = 16,
                 cura del 24 set 2026: Firefox in decodifica hardware
                 disegnava una striscia verde a destra e in basso)
       e si guarda in TRE posti, che devono dire tutti la misura attesa:
         · il CAMPO del server: «il palco risponde alla tela — chiesta WxH,
           AVUTA WxH» nel registro della scatola (il desktop vero l'ha presa)
         · la pagina: la tela in vigore (`REMOTIX_PUNTATORE.geometria` tl x ta)
         · la FOTOGRAFIA della tela a piena risoluzione: la sua misura
       e nella fotografia (due foto, a 2 s l'una dall'altra):
         · niente STRISCIA VERDE (0,76,0) nelle ultime 16 colonne e righe
           (il verde e' la decodifica di un blocco di zeri: il difetto storico)
         · niente FASCIA ai bordi: il bordo esterno (2 px) uniforme E diverso
           dal desktop che sta 24 e 40 px piu' dentro = un'imbottitura, non il
           desktop.  Un pannello al suo bordo e' uniforme ma e' lo STESSO
           colore anche 24 px dentro (i pannelli sono alti >= 28 px); lo sfondo
           arriva al bordo con continuita'.

GUASTO (stessa sessione, le stesse fotografie vere, tre innesti, tutti devono
       dare rosso):
         a) una striscia (0,76,0) di 8 px dipinta a destra della foto vera
         b) l'atteso di misura spostato di 16 in larghezza
         c) una fascia uniforme MAGENTA di 12 px dipinta in basso (un colore
            che nessun desktop ha: nera o bianca finiva su un pannello uguale)

⚠ LIMITE: su uno sfondo nero (XFCE) una fascia NERA non si distingue dallo
  sfondo; la fascia la vede solo se e' diversa dal desktop accanto.
"""
import io
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

FUNZIONI = ("F-011",)

# ⛔ Gli stessi numeri di src/pagina.html ~2127-2129 (verificati il 24 set 2026)
L_MIN, L_MAX, A_MIN, A_MAX, PASSO = 320, 7680, 240, 4320, 16
VERDE_DIFETTO = (0, 76, 0)
TOLL_VERDE = 24
STRISCIA = 16            # le colonne/righe guardate per la striscia verde
QUOTA_VERDE = 0.5        # una colonna e' «verde» se lo e' meta' dei suoi pixel
ESTERNO = 2              # lo spessore del bordo esterno guardato
DENTRO = (24, 40)        # dove si guarda il desktop «accanto»
UNIFORME_DEV = 4.0       # deviazione (per canale) sotto cui il bordo e' uniforme
DIVERSO = 25.0           # differenza media per pixel oltre cui e' «un'altra cosa»

RE_AVUTA = re.compile(r"chiesta (\d+)x(\d+), AVUTA (\d+)x(\d+)")


# ═══════════════════════════════════════════════════════════════════════════
#  LE FUNZIONI PURE
# ═══════════════════════════════════════════════════════════════════════════
def tela_attesa(cw, ch, dpr):
    """La regola di `misura_vista()` + `tela_da_chiedere()`."""
    import math
    v = [max(1, int(math.floor(cw * dpr))), max(1, int(math.floor(ch * dpr)))]

    def p(n, lo, hi):
        n = min(hi, max(lo, int(round(n))))
        return n - n % PASSO
    return [p(v[0], L_MIN, L_MAX), p(v[1], A_MIN, A_MAX)]


def striscia_verde(im):
    """(trovata, descrizione): colonne a destra e righe in basso dominate da (0,76,0)."""
    w, h = im.size
    trovate = []

    def verde(p):
        return all(abs(p[i] - VERDE_DIFETTO[i]) <= TOLL_VERDE for i in range(3))
    col = im.crop((w - STRISCIA, 0, w, h))
    px = list(col.getdata())
    for c in range(STRISCIA):
        n = sum(1 for y in range(h) if verde(px[y * STRISCIA + c]))
        if n >= QUOTA_VERDE * h:
            trovate.append("colonna x=%d (%d%%)" % (w - STRISCIA + c, 100 * n // h))
    rig = im.crop((0, h - STRISCIA, w, h))
    px = list(rig.getdata())
    for r in range(STRISCIA):
        n = sum(1 for x in range(w) if verde(px[r * w + x]))
        if n >= QUOTA_VERDE * w:
            trovate.append("riga y=%d (%d%%)" % (h - STRISCIA + r, 100 * n // w))
    if trovate:
        return True, "striscia (0,76,0): %d linee — %s" % (len(trovate), ", ".join(trovate[:4]))
    return False, "nessuna striscia (0,76,0) nelle ultime %d colonne e righe" % STRISCIA


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
    """(trovate: [lati], descrizione) — un bordo uniforme che non e' il desktop."""
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
                                                 " ⛔ FASCIA" if fascia else ""))
        if fascia:
            trovate.append(lato)
    return trovate, "; ".join(note)


def giudica_misure(attesa, avuta_server, pagina, foto):
    """(esito, motivo).  `avuta_server`, `pagina`, `foto`: [w,h] o None."""
    manca = [n for n, v in (("server", avuta_server), ("pagina", pagina), ("foto", foto))
             if not v]
    if manca:
        return S.BLOCKED, "non ho potuto leggere la misura da: %s" % ", ".join(manca)
    sbagli = ["%s %dx%d" % (n, v[0], v[1]) for n, v in
              (("server", avuta_server), ("pagina", pagina), ("foto", foto))
              if list(v) != list(attesa)]
    if sbagli:
        return S.FAIL, ("attesa %dx%d, ma %s" % (attesa[0], attesa[1], ", ".join(sbagli)))
    return S.PASS, "server, pagina e foto dicono tutti %dx%d (l'atteso)" % tuple(attesa)


def giudica_foto(im):
    """(esito, motivo) della fotografia: striscia verde e fasce."""
    v, dv = striscia_verde(im)
    f, df = fasce(im)
    if v or f:
        return S.FAIL, "%s · fasce %s (%s)" % (dv, f or "nessuna", df)
    return S.PASS, "%s · nessuna fascia (%s)" % (dv, df)


def dipingi_striscia(im, larghezza=8, colore=VERDE_DIFETTO):
    from PIL import ImageDraw
    c = im.copy()
    w, h = c.size
    ImageDraw.Draw(c).rectangle((w - larghezza, 0, w - 1, h - 1), fill=colore)
    return c


def dipingi_fascia_basso(im, spessore=12, colore=(255, 0, 255)):
    """⭐ La fascia innestata e' MAGENTA: lontana da ogni desktop vero (nero,
    bianco, grigio, blu).  `[M]` 24 set 2026, lxqt: una fascia bianca scelta
    guardando 30-60 px sopra finiva su un pannello chiaro e non si distingueva."""
    from PIL import ImageDraw
    c = im.copy()
    w, h = c.size
    ImageDraw.Draw(c).rectangle((0, h - spessore, w - 1, h - 1), fill=colore)
    return c, colore


# ═══════════════════════════════════════════════════════════════════════════
#  LA CERTIFICAZIONE
# ═══════════════════════════════════════════════════════════════════════════
def _desktop_finto(w=800, h=480, pannello=32):
    """Uno sfondo sfumato con un pannello scuro in alto (con testo)."""
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
    ok(tela_attesa(3838, 2069, 1) == [3824, 2064], "3838x2069 dpr1 ⇒ 3824x2064 (misurata sul server)")
    ok(tela_attesa(3840, 2160, 1) == [3840, 2160], "3840x2160 ⇒ se stessa")
    ok(tela_attesa(653, 400, 1.5) == [976, 592], "653x400 a dpr 1,5 ⇒ 979x600 ⇒ 976x592")
    ok(tela_attesa(100, 100, 1) == [320, 240], "sotto il minimo ⇒ 320x240")
    ok(tela_attesa(9000, 5000, 1) == [7680, 4320], "sopra il massimo ⇒ 7680x4320")
    im = _desktop_finto()
    e, m = giudica_foto(im)
    ok(e == S.PASS, "desktop finto con pannello scuro in alto ⇒ PASS (%s)" % m)
    e, m = giudica_foto(dipingi_striscia(im))
    ok(e == S.FAIL, "+ striscia (0,76,0) di 8 px a destra ⇒ FAIL (%s)" % m[:80])
    e, m = giudica_foto(dipingi_striscia(im, 3))
    ok(e == S.FAIL, "+ striscia di 3 px ⇒ FAIL")
    c, col = dipingi_fascia_basso(im)
    e, m = giudica_foto(c)
    ok(e == S.FAIL, "+ fascia %s di 12 px in basso ⇒ FAIL (%s)" % (col, m[-90:]))
    from PIL import Image
    nero = Image.new("RGB", (800, 480))
    e, m = giudica_foto(nero)
    ok(e == S.PASS, "tutto nero (lo sfondo di XFCE) ⇒ nessuna fascia: limite dichiarato")
    ok(giudica_misure([3824, 2064], [3824, 2064], [3824, 2064], [3824, 2064])[0] == S.PASS,
       "tre misure uguali all'atteso ⇒ PASS")
    ok(giudica_misure([3840, 2064], [3824, 2064], [3824, 2064], [3824, 2064])[0] == S.FAIL,
       "atteso spostato di 16 ⇒ FAIL")
    ok(giudica_misure([3824, 2064], None, [3824, 2064], [3824, 2064])[0] == S.BLOCKED,
       "misura del server non letta ⇒ BLOCKED")
    print("⭐ certificazione verde" if not guai else "⛔ %d guai" % len(guai))
    return 0 if not guai else 1


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
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
        print("   finestra: client %dx%d (inner %dx%d) dpr %s ⇒ tela attesa %dx%d"
              % (cw, ch, iw, ih, dpr, attesa[0], attesa[1]), flush=True)
        # il server: la riga «AVUTA» con la misura attesa (o l'ultima, entro 20 s)
        fine = time.time() + 20
        avuta, righe = None, []
        while time.time() < fine:
            righe = s.registro_da(segno) if segno is not None else []
            avuta = avuta_dal_server(righe)
            geo = s.geometria() or {}
            if avuta == attesa and [geo.get("tl"), geo.get("ta")] == attesa:
                break
            time.sleep(1)
        time.sleep(2)                     # qualche fotogramma alla misura nuova
        geo = s.geometria() or {}
        pagina = [geo.get("tl"), geo.get("ta")] if geo.get("tl") else None
        ev = [s.salva_testo("server-f011.txt", righe)]
        foto = []
        for k in range(2):
            png, dove = s.foto("tela-%d" % k)
            if not png:
                raise S.Bloccata("la tela non si fotografa: %s" % dove)
            foto.append(Image.open(io.BytesIO(png)).convert("RGB"))
            ev.append(dove)
            if k == 0:
                time.sleep(2)
        misura_foto = list(foto[-1].size) if dpr == 1 else None
        nota_dpr = "" if dpr == 1 else " (dpr %s: la misura della foto non si confronta)" % dpr
        if dpr != 1:
            misura_foto = pagina
        e1, m1 = giudica_misure(attesa, avuta, pagina, misura_foto)
        g_foto = [giudica_foto(im) for im in foto]
        e2 = S.FAIL if any(x[0] == S.FAIL for x in g_foto) else S.PASS
        m2 = " | ".join("foto %d: %s" % (i, x[1]) for i, x in enumerate(g_foto))
        esito = S.FAIL if S.FAIL in (e1, e2) else (S.BLOCKED if S.BLOCKED in (e1, e2) else S.PASS)
        ragione = "misure: %s%s · %s" % (m1, nota_dpr, m2)
        E.metti("F-011", esito, ragione if esito != S.PASS else "tela %dx%d come la finestra "
                "(%dx%d, dpr %s), niente striscia verde, niente fasce" % (
                    attesa[0], attesa[1], cw, ch, dpr),
                atteso="tela %dx%d (client %dx%d a multiplo di 16), niente (0,76,0) ai bordi, "
                       "sfondo fino al bordo" % (attesa[0], attesa[1], cw, ch),
                osservato=ragione, evidenze=ev + [s.salva_console()])

        if o.guasto:
            if e1 != S.PASS or e2 != S.PASS:
                E.guasto("F-011", None, "la passata sana non e' verde: il guasto non si innesta "
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
                     "striscia (0,76,0) 8 px ⇒ %s · atteso +16 ⇒ %s · fascia %s 12 px in basso "
                     "⇒ %s" % (ga[0], gb[0], colore, gc[0]),
                     osservato="a) %s | b) %s | c) %s" % (ga[1][:160], gb[1], gc[1][-200:]))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
