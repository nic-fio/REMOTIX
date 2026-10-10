#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f026 — F-026 SEVERAL USERS TOGETHER: each one sees THEIR OWN session, and writes only in it

    python3 15-f026-piu-utenti-insieme.py --scatola xfce --browser chrome --porte-base 4920 [--guasto] [--inquilini 3]

Normal server of the box (85xx).  N tenants (2 normally, up to 3:
`c15026u<n>`), each with THEIR OWN real browser of the same type (porte-base,
+50, +54: 4K windows together in the labwc), all in TOGETHER.  In each one's
session a `firefox-esr --kiosk` scene of a COLOUR of their own (red, green,
magenta) with a focused text field; a small server writes down in the
tenant's home every key and every value of the field.

THE EXPECTATION (SPECIFICHE §5.5 «each one their own remote graphical session,
independent»):
  image     the canvas of each browser is covered by ITS OWN colour (>= 50 %) and does not
            show those of the others (<= 3 % each) — PHOTO;
  input     a different word for each one, typed with REAL KEYS in their
            browser, in turn: at the end the field of each one's scene is
            EXACTLY their word, and nobody received keys of the others
            (field value and notebook of the keys, in the session).

FAULTS (after the healthy pass, same sessions):
  image     the second tenant's scene repaints itself with the colour of the FIRST (the
            colour file changes: it is the scene, not the judge) ⇒ the image judge
            must say red;
  input     the first one's word is typed in the SECOND one's browser (the gesture goes
            to the wrong tenant) ⇒ the input judge must say red.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._carica("g8", os.path.join(S.QUI, "15-g8-comune.py"))
FUNZIONI = ("F-026",)
COLORI = {"rosso": (220, 40, 40), "verde": (40, 190, 60), "magenta": (200, 40, 200)}
NOMI = ("rosso", "verde", "magenta")
PAROLE = ("alfa", "bravo", "xyz")        # different letters: someone else's key shows
SUO_MIN = 0.5
ALTRUI_MAX = 0.03


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def giudica_immagini(frazioni, nomi):
    """`frazioni[i]` = {colour: fraction} of tenant i's canvas."""
    guai = []
    for i, fr in enumerate(frazioni):
        if fr is None:
            return S.BLOCKED, "tenant %d's canvas cannot be photographed" % (i + 1)
        if fr.get(nomi[i], 0) < SUO_MIN:
            guai.append("%d: ITS OWN %s covers only %.1f%%" % (i + 1, nomi[i], 100 * fr.get(nomi[i], 0)))
        for j, n in enumerate(nomi):
            if j != i and fr.get(n, 0) > ALTRUI_MAX:
                guai.append("%d: shows the %s of tenant %d (%.1f%%)" % (
                    i + 1, n, j + 1, 100 * fr[n]))
    if guai:
        return S.FAIL, "; ".join(guai)
    return S.PASS, " · ".join("%d sees %s %.0f%%" % (i + 1, nomi[i], 100 * fr[nomi[i]])
                              for i, fr in enumerate(frazioni))


def giudica_input(valori, tasti, parole):
    """`valori[i]` = final value of the field, `tasti[i]` = keys received."""
    guai = []
    for i, v in enumerate(valori):
        if v is None:
            return S.BLOCKED, "tenant %d's notebook cannot be read" % (i + 1)
        if v != parole[i]:
            guai.append("%d: the field is «%s», expected «%s»" % (i + 1, v, parole[i]))
        estranei = [k for k in tasti[i] if len(k) == 1 and k not in parole[i]]
        if estranei:
            guai.append("%d: received someone else's keys %s" % (i + 1, "".join(estranei)))
    if guai:
        return S.FAIL, "; ".join(guai)
    return S.PASS, " · ".join("%d «%s»" % (i + 1, v) for i, v in enumerate(valori))


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    n = NOMI[:2]
    buone = [{"rosso": 0.9, "verde": 0.0}, {"rosso": 0.0, "verde": 0.9}]
    prova("each their own ⇒ PASS", giudica_immagini(buone, n)[0] == S.PASS)
    prova("the second sees the red ⇒ FAIL", giudica_immagini(
        [buone[0], {"rosso": 0.9, "verde": 0.0}], n)[0] == S.FAIL)
    prova("half and half ⇒ FAIL", giudica_immagini(
        [buone[0], {"rosso": 0.2, "verde": 0.6}], n)[0] == S.FAIL)
    prova("photo missing ⇒ BLOCKED", giudica_immagini([buone[0], None], n)[0] == S.BLOCKED)
    p = PAROLE[:2]
    prova("right words ⇒ PASS", giudica_input(["alfa", "bravo"], [list("alfa"), list("bravo")], p)[0] == S.PASS)
    prova("word in the wrong place ⇒ FAIL", giudica_input(
        ["", "bravoalfa"], [[], list("bravoalfa")], p)[0] == S.FAIL)
    prova("foreign key ⇒ FAIL", giudica_input(
        ["alfa", "bravo"], [list("alfa") + ["x"], list("bravo")], p)[0] == S.FAIL)
    # the fractions on a synthetic photo
    from PIL import Image
    import io
    im = Image.new("RGB", (100, 50), COLORI["verde"])
    im.paste(COLORI["rosso"], (0, 0, 10, 50))
    b = io.BytesIO()
    im.save(b, "PNG")
    fr = G.frazioni(b.getvalue(), COLORI, riduci=1)
    prova("fractions: green 90%%, red 10%% (%s)" % G.fr_testo(fr),
          abs(fr["verde"] - 0.9) < 0.01 and abs(fr["rosso"] - 0.1) < 0.01 and fr["magenta"] == 0)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def extra(a):
    a.add_argument("--inquilini", type=int, default=2, choices=(2, 3))


def davanti(s):
    """(Nothing to do: see `browser_per` — the Chrome window is always on top.)"""
    return


def browser_per(o, i, n):
    """⛔ THE CHROME COLUMN: Chrome for the LAST tenant, Firefox for the others.

    `[M]` 25 Sep 2026: under Wayland (labwc) a Chrome window COVERED by
    another no longer receives «frame callbacks», does not repaint, and its
    CDP photo (`Page.captureScreenshot`) waits FOREVER — F-026 hung for
    15 minutes on gnome, xfce, lxqt; neither `Page.bringToFront`, nor the options
    against occlusion, nor minimising the others (a Wayland client cannot
    come back from minimised by itself) are enough.  Firefox instead can be photographed even
    when covered.  ⇒ Two users with two different browsers (a real case), Chrome created
    LAST and therefore on top.  Declared in the report."""
    o2 = G.o_per(o, i)
    if o.browser == "chrome":
        if i < n - 1:
            o2.browser = "firefox"
            o2.porte_base = o.porte_base + G.SPOSTA_BROWSER[i + 1]
        else:
            o2.porte_base = o.porte_base
    return o2


def fotografa_tutti(sess, nomi, etichetta):
    frs, ev = [], []
    for i, s in enumerate(sess):
        davanti(s)
        png, dove = s.foto("%s-%d-%s" % (etichetta, i + 1, nomi[i]))
        frs.append(G.frazioni(png, COLORI) if png else None)
        if dove:
            ev.append(dove)
    return frs, ev


def batti(s, parola):
    davanti(s)
    G.clic_centro(s)
    time.sleep(0.8)
    G.C23.manda(s.g, G.C23.scrivi(parola))


def leggi_tutti(sess):
    val, tas = [], []
    for s in sess:
        q = G.quaderno(s.sc, s.chi)
        val.append(G.valore(q))
        tas.append(G.tasti(q))
    return val, tas


def corpo(o, E):
    n = o.inquilini
    nomi, parole = NOMI[:n], PAROLE[:n]
    sess = []
    try:
        for i in range(n):
            s = S.Sessione(browser_per(o, i, n), "026", E)
            s.__enter__()
            sess.append(s)
            ok, m = s.entra()
            if not ok:
                raise S.Bloccata("tenant %d (%s) does not get in: %s" % (i + 1, s.chi, m))
            print("   ⭐ %d %s (%s) in: %s" % (i + 1, s.chi, s.o.browser, m[:70]), flush=True)
            davanti(s)
            S.C21.sveglia(s.g, s.geometria())
            ok, t = G.accendi_scena(s.sc, s.chi, o.porte_base + G.SPOSTA_SCENA + i,
                                    COLORI[nomi[i]])
            if not ok:
                raise S.Bloccata("the %s scene of %s does not start: %s"
                                 % (nomi[i], s.chi, " | ".join(t.splitlines()[-6:])[-400:]))
        # all in, each with their scene: wait for each one to be seen
        for i, s in enumerate(sess):
            davanti(s)
            fr, _d, perche = G.aspetta_colore(s, "attesa-%d" % (i + 1), COLORI, nomi[i],
                                              SUO_MIN, 40)
            print("   canvas %d: %s %s" % (i + 1, G.fr_testo(fr), perche), flush=True)
        # ── the image ──────────────────────────────────────────────────────
        frs, ev = fotografa_tutti(sess, nomi, "immagine")
        ei, ri = giudica_immagini(frs, nomi)
        print("   image: %s — %s" % (ei, ri), flush=True)
        # ── the input, in turn ─────────────────────────────────────────────
        for i, s in enumerate(sess):
            batti(s, parole[i])
            time.sleep(2.5)
        time.sleep(2)
        val, tas = leggi_tutti(sess)
        ein, rin = giudica_input(val, tas, parole)
        print("   input: %s — %s" % (ein, rin), flush=True)
        _f, ev2 = fotografa_tutti(sess, nomi, "dopo-input")
        chi = [s.chi for s in sess]
        righe = []
        for s in sess:
            righe += ["## %s" % s.chi] + [r for r in s.registro_da(0)
                                          if "session open" in r or "slot" in r][-6:]
        ev.append(sess[0].salva_testo("f026-server.txt", righe))
        tutti = [ei, ein]
        esito = S.FAIL if S.FAIL in tutti else (S.BLOCKED if S.BLOCKED in tutti else S.PASS)
        E.metti("F-026", esito, "image %s · input %s" % (ei, ein),
                atteso="%d tenants together (%s): each one sees ITS OWN colour and not the others; "
                       "their word ends up ONLY in their field" % (n, ", ".join(chi)),
                osservato="image: %s | input: %s" % (ri, rin), evidenze=ev + ev2)

        if o.guasto:
            # image: the second one's scene takes the colour of the first
            G.cambia_colore(sess[1].sc, sess[1].chi, COLORI[nomi[0]])
            davanti(sess[1])
            G.aspetta_colore(sess[1], "guasto-attesa", COLORI, nomi[0], SUO_MIN, 20)
            frs, _e = fotografa_tutti(sess, nomi, "guasto-immagine")
            eg1, rg1 = giudica_immagini(frs, nomi)
            G.cambia_colore(sess[1].sc, sess[1].chi, COLORI[nomi[1]])
            # input: the first one's word in the second one's browser
            batti(sess[1], parole[0])
            time.sleep(3)
            val, tas = leggi_tutti(sess)
            eg2, rg2 = giudica_input(val, tas, parole)
            v1 = eg1 == S.FAIL if eg1 != S.BLOCKED else None
            v2 = eg2 == S.FAIL if eg2 != S.BLOCKED else None
            visto = None if None in (v1, v2) else (v1 and v2)
            E.guasto("F-026", visto, "scene of 2 with the colour of 1 ⇒ %s (%s) · word of 1 in "
                     "the browser of 2 ⇒ %s (%s)" % (eg1, rg1[:100], eg2, rg2[:100]))
    finally:
        for s in reversed(sess):
            try:
                s.__exit__(None, None, None)
            except Exception as e:               # noqa: BLE001
                print("   ⚠ exit of %s: %s" % (s.chi, e))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra))
