#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f018b — F-018 REATTACH AT A DIFFERENT SIZE: THE WINDOWS ALL STAY INSIDE
           (the defect D-007)

    python3 15-f018b-finestre-dentro-al-riattacco.py --scatola xfce --browser firefox [--guasto]

  G6's scene with a LARGE window (1800x1000): creation at 4K
  (browser window 3840x2160), the window is born centred and whole →
  DETACH → reattach with the browser window at 2560x1440.  Centred in the 4K,
  that window, at 2544x1344, sticks out by ~240 px on the right and ~160 at the bottom;
  its midpoint however stays inside, and labwc by itself does not move it
  (`src/sessione.h`, the box of `SESSIONE_LABWC_TASTIERA`).

F-018b expected (D-007, decided by the user on 25 Sep 2026: «it must be cured»):
  photo: after the smaller reattach the scene's window is ENTIRELY inside
        the canvas — the cyan rectangle (the scene's page) has the SAME
        size, in desktop pixels, it had at 4K (± 3 %), and does not touch the
        edges.  ⇒ «Entirely inside» and also «moved, not shrunk»: it fits,
        and the product has no right to shrink it.
        ⚠ The edge alone is NOT enough: a window brought back inside sits
        right against the edge, to the pixel — and one cut by the edge touches it
        just the same.  The SIZE instead separates them: the cut one is shorter.
  ⭐ on all the desktops.  On KDE (canvas kept, declared exception) the
        window stays whole by itself; on GNOME Mutter brings it back inside; on
        XFCE and LXQt (labwc) the product does.

FAULT: the 4K photo of the creation, cut to the NEW size from the top-left
        corner — that is what is seen if at the reattach nobody moves
        the windows (the cure off: labwc leaves the window where it was, and
        the smaller output shows its corner) ⇒ the judge must say RED.
        And the cure REALLY off is tried by starting the standard server
        (`15-d007-server.sh accendi xfce stock`): same scene, RED.
"""
import io
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._carica("g6", os.path.join(S.QUI, "15-g6-comune.py"))
F16 = S._carica("f016", os.path.join(S.QUI, "15-f016-stacco-e-riattacco.py"))
FUNZIONI = ("F-018b", "F-018c")
FINESTRA = (1800, 1000)       # centred in 3776x2016 it sticks out of 2544x1344; it fits
MISURA_NUOVA = (2560, 1440)
TOLL_MISURA = 0.03            # the window must have the previous size (± 3 %)
MARGINE_4K = 4                # at 4K the window must not touch the edges (photo px)
ATTESA_CURA_S = 15.0          # how long the photo is looked at again after the reattach
TOLL_POSTO = 8                # desktop px: the photo is reduced to 960 (~4 px at 4K)


def ciano_in_px(v, tela):
    """The cyan rectangle of `guarda_la_scena` in CANVAS (desktop) pixels:
    (x0, y0, width, height) or None."""
    if not v or not v.get("finestra") or not v.get("misura") or not tela:
        return None
    w, h = v["misura"]
    x0, y0, x1, y1 = v["finestra"]
    sx, sy = tela[0] / float(w), tela[1] / float(h)
    return (x0 * sx, y0 * sy, (x1 - x0 + 1) * sx, (y1 - y0 + 1) * sy)


def giudica_dentro(prima, dopo):
    """⭐ F-018b.  prima/dopo: {"finestra": (x0,y0,x1,y1) in the photo,
    "misura": (w,h) of the photo, "tela": (W,H) in desktop px}.
    Returns (outcome, reason)."""
    a = ciano_in_px(prima, prima.get("tela"))
    if not a:
        return S.BLOCKED, "at 4K the scene's window is not seen: nothing to compare"
    w, h = prima["misura"]
    x0, y0, x1, y1 = prima["finestra"]
    if x0 < MARGINE_4K or y0 < MARGINE_4K or x1 > w - 1 - MARGINE_4K or y1 > h - 1 - MARGINE_4K:
        return S.BLOCKED, ("at 4K the window already touches an edge (%s in %dx%d): the scene is not "
                           "the intended one" % (prima["finestra"], w, h))
    b = ciano_in_px(dopo, dopo.get("tela"))
    if not b:
        return S.FAIL, "after the reattach the scene's window is not seen (%s)" % (
            (dopo or {}).get("perche") or "no cyan")
    dl, da = b[2] / a[2], b[3] / a[3]
    probl = []
    if dl < 1 - TOLL_MISURA or da < 1 - TOLL_MISURA:
        # cut by the edge (outside) or shrunk: both NO
        bw, bh = dopo["misura"]
        bx0, by0, bx1, by1 = dopo["finestra"]
        tocca = [n for n, t in (("right", bx1 >= bw - 2), ("bottom", by1 >= bh - 2),
                                ("left", bx0 <= 1), ("top", by0 <= 1)) if t]
        probl.append("the window is seen at %.0fx%.0f, at 4K it was %.0fx%.0f (%.0f %% x %.0f %%)%s"
                     % (b[2], b[3], a[2], a[3], 100 * dl, 100 * da,
                        (": CUT by the %s edge — it is partly OUTSIDE the screen"
                         % "/".join(tocca)) if tocca else
                        ": it was SHRUNK although it fits"))
    elif dl > 1 + TOLL_MISURA or da > 1 + TOLL_MISURA:
        probl.append("the window is seen at %.0fx%.0f, at 4K it was %.0fx%.0f: larger? the "
                     "photo does not add up" % (b[2], b[3], a[2], a[3]))
    if probl:
        return S.FAIL, "; ".join(probl)
    return S.PASS, ("whole window %.0fx%.0f (at 4K %.0fx%.0f) at (%.0f,%.0f) of the canvas "
                    "%dx%d" % (b[2], b[3], a[2], a[3], b[0], b[1], dopo["tela"][0],
                               dopo["tela"][1]))


def giudica_indietro(prima, dopo, stesso_posto):
    """⭐ F-018c: back at the starting size the window is whole and of the
    previous size; with `stesso_posto` (labwc) also in the previous place."""
    e, r = giudica_dentro(prima, dopo)
    if e != S.PASS or not stesso_posto:
        return e, r
    a = ciano_in_px(prima, prima.get("tela"))
    b = ciano_in_px(dopo, dopo.get("tela"))
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) > TOLL_POSTO or abs(dy) > TOLL_POSTO:
        return S.FAIL, ("back at 4K the window is whole but MOVED by (%+.0f, %+.0f) px "
                        "relative to the creation: the shortcut moved a window that "
                        "was already inside" % (dx, dy))
    return S.PASS, "%s · in the previous place (%+.0f, %+.0f px)" % (r, dx, dy)


def taglia(png, largo, alto):
    """⛔ The FAULT: the full-resolution photo cut to largo x alto
    from the top-left corner — the smaller screen with the windows
    left where they were."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    fuori = io.BytesIO()
    im.crop((0, 0, min(largo, im.size[0]), min(alto, im.size[1]))).save(fuori, "PNG")
    return fuori.getvalue()


def guarda_png(png):
    """`guarda_la_scena` on a png already in hand (the fault)."""
    im = G.immagine(png)
    r, perche = G.trova_ciano(im)
    return {"finestra": list(r) if r else None, "misura": list(im.size), "perche": perche}


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))

    from PIL import Image, ImageDraw

    def foto(tela, rett, largo=960):
        """A canvas `tela` with the cyan rectangle `rett` (desktop px), reduced
        as `G.immagine` reduces it: (view, png)."""
        im = Image.new("RGB", tela, (40, 40, 60))
        ImageDraw.Draw(im).rectangle(rett, fill=G.CIANO)
        f = io.BytesIO()
        im.save(f, "PNG")
        png = f.getvalue()
        v = guarda_png(png)
        v["tela"] = list(tela)
        return v, png

    A, pngA = foto((3776, 2016), (988, 522, 988 + 1799, 522 + 999))
    B, _ = foto((2544, 1344), (743, 343, 743 + 1799, 343 + 999))
    e, m = giudica_dentro(A, B)
    prova("brought back inside, same size ⇒ PASS (%s)" % m[:60], e == S.PASS)
    Bb, _ = foto((2544, 1344), (743, 343, 2543, 1343))           # against the edge, to the pixel
    e, m = giudica_dentro(A, Bb)
    prova("against the right/bottom edge but whole ⇒ PASS", e == S.PASS)
    T = guarda_png(taglia(pngA, 2544, 1344))
    T["tela"] = [2544, 1344]
    e, m = giudica_dentro(A, T)
    prova("fault: 4K cut (cure off) ⇒ FAIL (%s)" % m[:70], e == S.FAIL)
    Bp, _ = foto((2544, 1344), (100, 100, 100 + 1399, 100 + 799))   # inside but narrow
    e, m = giudica_dentro(A, Bp)
    prova("shrunk although it fits ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_dentro(A, {"finestra": None, "misura": [960, 507], "tela": [2544, 1344]})
    prova("window gone ⇒ FAIL", e == S.FAIL)
    Ab, _ = foto((3776, 2016), (3000, 522, 3775, 1521))
    e, _ = giudica_dentro(Ab, B)
    prova("at 4K already against the edge ⇒ BLOCKED (wrong scene)", e == S.BLOCKED)
    K, _ = foto((3776, 2016), (988, 522, 988 + 1799, 522 + 999))   # KDE: canvas kept
    e, _ = giudica_dentro(A, K)
    prova("kde: canvas kept, whole window ⇒ PASS", e == S.PASS)
    e, m = giudica_indietro(A, dict(A), True)
    prova("back at 4K in the previous place ⇒ PASS (%s)" % m[-40:], e == S.PASS)
    Cs, _ = foto((3776, 2016), (988, 522 + 13, 988 + 1799, 522 + 13 + 999))
    e, m = giudica_indietro(A, Cs, True)
    prova("fault: back, moved down by half a bar (13 px) ⇒ FAIL (%s)" % m[:60], e == S.FAIL)
    e, _ = giudica_indietro(A, Cs, False)
    prova("gnome/kde: the place is not judged ⇒ PASS", e == S.PASS)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def osserva(s, nome):
    ob = G.aspetta_tela_ferma(s)
    v = G.guarda_la_scena(s, nome)
    v["tela"] = ob.get("buffer")
    v["vista"] = ob.get("vista")
    return v


def breve(v):
    return "canvas %s · view %s · cyan %s (desktop px %s)" % (
        v.get("tela"), (v.get("vista") or [None])[:2], v.get("finestra"),
        [round(x) for x in (ciano_in_px(v, v.get("tela")) or [])])


def corpo(o, E):
    with S.Sessione(o, "918", E) as s:
        try:
            if o.ssd:
                # ⭐ the scene's window with labwc's title bar (the
                #   «with the bar» road of the shortcut, that of the Qt apps of
                #   LXQt): a rule in the USER's rc.xml, which on XFCE labwc
                #   adds to ours (`-m`).  ⚠ Before the login: labwc reads the
                #   configuration when it is born.
                if o.scatola != "xfce":
                    raise S.Bloccata("--ssd holds only on xfce: on LXQt labwc's configuration "
                                     "belongs only to the product (-C)")
                c, t = s.sc.dentro(
                    "h=/home/{c}; install -d -o {c} -g {c} $h/.config $h/.config/labwc; "
                    "printf '%s\\n' '<?xml version=\"1.0\"?><labwc_config><windowRules>"
                    "<windowRule identifier=\"firefox*\" serverDecoration=\"yes\"/>"
                    "</windowRules></labwc_config>' > $h/.config/labwc/rc.xml; "
                    "chown {c}: $h/.config/labwc/rc.xml; cat $h/.config/labwc/rc.xml"
                    .format(c=s.chi), 30)
                print("   --ssd: the user's rc.xml: %s" % t.strip()[-160:], flush=True)
            ok, m = s.entra()
            if not ok:
                raise S.Bloccata("without login there is nothing to reattach: " + m)
            ok, t = G.accendi_scena(s, FINESTRA)
            if not ok:
                raise S.Bloccata("the scene does not start in the session: " + t[-200:])
            G.sveglia(s)
            v = F16.trova_scena(s)
            if not v.get("finestra"):
                raise S.Bloccata("the scene's window is not seen in the photo: %s"
                                 % v.get("perche"))
            time.sleep(2)
            A = osserva(s, "A-4k")
            print("   A (creation): %s" % breve(A), flush=True)
            if not A.get("tela") or not A.get("finestra"):
                raise S.Bloccata("at 4K the canvas or the window cannot be read: %s" % breve(A))

            # ── DETACH and smaller reattach
            s.spegni_browser()
            time.sleep(2)
            mis = G.accendi_a_misura(s, *MISURA_NUOVA)
            print("   browser restarted at %dx%d: view %s" % (MISURA_NUOVA + (mis,)), flush=True)
            ok, m, _rif, _sec = G.entra_con_riprova(s, tetto_s=40)
            if not ok:
                E.metti("F-018b", S.FAIL, "the reattach at %dx%d does not get in: %s"
                        % (MISURA_NUOVA + (m,)))
                return
            G.sveglia(s)
            fine = time.time() + ATTESA_CURA_S
            while True:
                B = osserva(s, "B-2560")
                eB, rB = giudica_dentro(A, B)
                if eB == S.PASS or time.time() > fine:
                    break
                time.sleep(1.5)
            print("   B (reattach): %s" % breve(B), flush=True)
            if B.get("tela") and A.get("tela") and o.scatola != "kde" \
                    and abs(B["tela"][0] - A["tela"][0]) < 64:
                raise S.Bloccata("the canvas did not change size (%s → %s): the reattach is not "
                                 "«smaller»" % (A["tela"], B["tela"]))
            ev = [x for x in (A.get("foto"), B.get("foto")) if x]
            E.metti("F-018b", eB, rB,
                    atteso="the scene's window ENTIRELY inside the canvas, of the previous "
                           "size (moved, not shrunk)",
                    osservato="A: %s || B: %s" % (breve(A), breve(B)), evidenze=ev)

            # ── and BACK at 4K: the window comes back whole, and on labwc WHERE IT WAS —
            #    labwc restores the position from before the size changes
            #    (`last_layout_geometry`), and the product's shortcut, on a
            #    window already inside, must NOT move it by one pixel (if it
            #    moved it — half a title bar down, the risk of
            #    `MoveToCursor` — it would be seen here)
            s.spegni_browser()
            time.sleep(2)
            G.accendi_a_misura(s, 3840, 2160)
            ok, m, _rif, _sec = G.entra_con_riprova(s, tetto_s=40)
            if not ok:
                E.metti("F-018c", S.FAIL, "the reattach back at 4K does not get in: %s" % m)
            else:
                G.sveglia(s)
                time.sleep(2)
                C = osserva(s, "C-4k")
                print("   C (back at 4K): %s" % breve(C), flush=True)
                eC, rC = giudica_indietro(A, C, o.scatola in ("xfce", "lxqt"))
                E.metti("F-018c", eC, rC,
                        atteso="back at 4K the window whole, of the previous size; on "
                               "labwc also in the previous place (± %d px)" % TOLL_POSTO,
                        osservato="A: %s || C: %s" % (breve(A), breve(C)),
                        evidenze=[x for x in (A.get("foto"), C.get("foto")) if x])
                if o.guasto:
                    # the window moved down by half a title bar (13 px): RED
                    Cg = dict(C, finestra=[C["finestra"][0], C["finestra"][1] + 4,
                                           C["finestra"][2], C["finestra"][3] + 4]) \
                        if C.get("finestra") else C
                    g, r = giudica_indietro(A, Cg, True)
                    E.guasto("F-018c", g == S.FAIL, "C's window moved down by ~16 px ⇒ %s "
                             "(%s)" % (g, r[:160]))

            if o.guasto:
                if not A.get("png"):
                    E.guasto("F-018b", None, "the 4K photo is no longer there: nothing to cut")
                else:
                    tl, ta = B.get("tela") or (MISURA_NUOVA[0] - 16, MISURA_NUOVA[1] - 96)
                    if o.scatola == "kde":
                        tl, ta = B.get("vista")[:2] if B.get("vista") else (tl, ta)
                    T = guarda_png(taglia(A["png"], int(tl), int(ta)))
                    T["tela"] = [int(tl), int(ta)]
                    g, r = giudica_dentro(A, T)
                    E.guasto("F-018b", g == S.FAIL,
                             "the 4K cut to %dx%d (the windows left where they were) ⇒ %s (%s)"
                             % (tl, ta, g, r[:200]))
        finally:
            if s.g:
                s.salva_console()
            G.spegni_servitore(s)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica,
                      extra=lambda a: a.add_argument(
                          "--ssd", action="store_true",
                          help="(xfce) the scene's window with labwc's title bar: "
                               "the «with the bar» road of the cure")))
