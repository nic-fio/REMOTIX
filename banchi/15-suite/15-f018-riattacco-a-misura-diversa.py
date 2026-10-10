#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f018 — F-018 REATTACH AT A DIFFERENT SIZE · path P-C

    python3 15-f018-riattacco-a-misura-diversa.py --scatola xfce --browser firefox [--guasto]

  P-C  creation at 4K (browser window 3840x2160) → application open and
       text written → DETACH → reattach with the window at 2560x1440 → DETACH
       → reattach BACK at 4K.  At every reattach: the canvas, the desktop, the
       state.  (Live resolution change does not exist: the size changes ONLY
       by reattaching — `DECISIONI.md` §5.1-bis.)

F-018  expected (`SPECIFICHE.md` §6.1-§6.3, `src/rcp.c` ~2998, `src/figlio.c`
       `misura_del_palco`):
   GNOME, XFCE, LXQt — the CANVAS takes the new size and the DESKTOP follows it:
       · field: the page's canvas (`#schermo` width×height) is that of the
         new view (± 16 px: the page truncates it to multiples of 16);
       · field: inside the session a program sees the SCREEN of that
         size (screen.width×height of firefox-esr in the session = the
         compositor's output);
       · photo: the scene's window is there and the text can be read; the edges of the
         photo (the rows at the top and bottom, where the panels are) are the ones
         from before; no new BLACK band on the right or at the bottom (full background).
   ⭐ KDE — EXCEPTION DECLARED by the user (KWin < 6.8, SPECIFICHE ~851,
       §6.3): the canvas STAYS the previous one and the browser RESCALES:
       · field: canvas equal to before; the canvas rectangle in the browser is
         inside the new view and fills one side of it (≥ 90 %);
       · field: the screen seen from inside is the one from before;
       · photo: as above (window, text, edges).
       ⇒ on KDE THIS is the PASS.
P-C    expected: the two reattaches (at 2560x1440 and back at 4K) both right.

FAULT: the judge receives the reattach BACK (size equal to the starting
       one) as if it were at 2560x1440 — «the reattach at the same size
       judged as if it had changed» — and then the reattach at 2560x1440 with
       the expectation of the OTHER family (KDE judged as GNOME and vice versa).
       Both must give RED, on real observations.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._carica("g6", os.path.join(S.QUI, "15-g6-comune.py"))
F16 = S._carica("f016", os.path.join(S.QUI, "15-f016-stacco-e-riattacco.py"))
FUNZIONI = ("F-018", "P-C")
MISURA_NUOVA = (2560, 1440)
TOLL_TELA = 16            # the page truncates the canvas to multiples of 16 (fc0fbff)
TOLL_BORDO = 40           # mean colour of the edge rows
RIEMPIE = 0.90            # on KDE the rescaled canvas fills at least one side


def famiglia(desktop):
    return "kde" if desktop == "kde" else "segue"


# the side of the panel that runs along the WHOLE width (seen in the photos of 24-25 Sep)
PANNELLO = {"gnome": "alto", "kde": "basso", "xfce": "alto", "lxqt": "basso"}


def confronta_pannello(bp, bd, lato):
    """Maximum distance between the slices of the panel side, before and after, outside
    the slices covered by the window in either photo.  (d, how many)."""
    fp, fd = bp.get(lato + "_f"), bd.get(lato + "_f")
    if not fp or not fd:
        return G.distanza(bp[lato], bd[lato]), 1
    via = set(bp.get("coperte") or []) | set(bd.get("coperte") or [])
    ks = [k for k in range(len(fp)) if k not in via]
    if not ks:
        return None, 0
    # the MEDIAN of the slices: the panel's icons and clock sit at fixed
    # pixels and change slice when the width changes; the missing panel
    # changes ALL the slices
    d = sorted(G.distanza(fp[k], fd[k]) for k in ks)
    return d[len(d) // 2], len(ks)


def giudica_misura(fam, prima, dopo, vista_attesa, testo, pannello="alto"):
    """⭐ F-018 for one reattach.  prima/dopo: the observations (see `osserva`).
    `vista_attesa` [w, h]: the view the browser draws in now.
    Returns (outcome, reason)."""
    probl, bene = [], []
    b0, b1 = prima.get("buffer"), dopo.get("buffer")
    if not b0 or not b1:
        return S.BLOCKED, "the page's canvas cannot be read (before %s, after %s)" % (b0, b1)
    vl, va = vista_attesa[0], vista_attesa[1]
    sch = dopo.get("schermo")
    if fam == "segue":
        # ⚠ the view is in CSS pixels; the canvas in DEVICE pixels (the page:
        #   `misura_vista()` = view × devicePixelRatio, truncated).  On the computer dpr 1 and
        #   the two coincide; on the phone (phase 19 §5, dpr 3.375) not.
        k = dopo.get("dpr") or 1
        tl, ta = int(vl * k), int(va * k)
        detta = "%dx%d" % (vl, va) if k == 1 else "%dx%d (%dx%d CSS × dpr %g)" % (tl, ta, vl, va, k)
        if abs(b1[0] - tl) > TOLL_TELA or abs(b1[1] - ta) > TOLL_TELA:
            probl.append("the canvas is %dx%d, the view %s: the canvas did NOT take the size "
                         "of the window" % (b1[0], b1[1], detta))
        else:
            bene.append("canvas %dx%d for the view %s" % (b1[0], b1[1], detta))
        if not sch:
            probl.append("the screen seen from inside the session cannot be read")
        elif abs(sch[0] - b1[0]) > 2 or abs(sch[1] - b1[1]) > 2:
            probl.append("inside the session the screen is %dx%d, the canvas %dx%d: the desktop "
                         "did NOT follow" % (sch[0], sch[1], b1[0], b1[1]))
        else:
            bene.append("inside, the screen is %dx%d" % tuple(sch))
    else:
        if list(b1) != list(b0):
            probl.append("on KDE the canvas had to stay %dx%d (KWin < 6.8), it is %dx%d"
                         % (b0[0], b0[1], b1[0], b1[1]))
        else:
            bene.append("canvas kept %dx%d (KWin < 6.8, declared exception)" % tuple(b1))
        r = dopo.get("tela_rett") or [0, 0, 0, 0]
        if r[2] > vl + 1 or r[3] > va + 1:
            probl.append("the canvas in the browser is %dx%d, larger than the view %dx%d: the "
                         "browser does NOT rescale" % (r[2], r[3], vl, va))
        elif max(r[2] / max(1, vl), r[3] / max(1, va)) < RIEMPIE:
            probl.append("the canvas in the browser is %dx%d in the view %dx%d: it does not fill it"
                         % (r[2], r[3], vl, va))
        else:
            bene.append("rescaled to %dx%d in the view %dx%d" % (r[2], r[3], vl, va))
        s0 = prima.get("schermo")
        if sch and s0 and list(sch) != list(s0):
            probl.append("on KDE the screen inside had to stay %s, it is %s" % (s0, sch))
    # the photo: window, text, edges
    if dopo.get("cieco"):
        if probl:
            return S.FAIL, "; ".join(probl) + " (and the photo could not be taken)"
        return S.BLOCKED, ("the fields add up (%s) but the photo could not be taken: %s"
                           % (" · ".join(bene), dopo.get("perche")))
    if not dopo.get("finestra"):
        probl.append("in the photo the scene's window is not there (%s)" % dopo.get("perche"))
    elif dopo.get("letto") != testo:
        probl.append("in the photo the strip says «%s», written «%s»" % (dopo.get("letto"), testo))
    else:
        bene.append("window and text «%s» in the photo" % testo)
    bp, bd = prima.get("bordi"), dopo.get("bordi")
    if bp and bd:
        d, n = confronta_pannello(bp, bd, pannello)
        if d is None:
            probl.append("the panel edge (%s) is entirely covered by the window" % pannello)
        elif d > TOLL_BORDO:
            probl.append("the panel edge (%s) changed (median deviation %d over %d free "
                         "slices): the panel is not at the new edge" % (pannello, d, n))
        else:
            bene.append("panel at the %s edge (%d slices, deviation %d)" % (pannello, n, d))
        for lato in ("nero_destra", "nero_basso"):
            if bd[lato] > bp[lato] + 0.5:
                probl.append("a new BLACK band (%s %.0f %%, before %.0f %%): the background is not "
                             "full" % (lato, 100 * bd[lato], 100 * bp[lato]))
    else:
        probl.append("the edges of the photo cannot be read")
    if probl:
        return S.FAIL, "; ".join(probl)
    return S.PASS, " · ".join(bene)


# ═══════════════════════════════════════════════════════════════════════════
def _oss(buffer, vista, rett, schermo, bordi, finestra=True, letto="abc"):
    return {"buffer": buffer, "vista": vista, "tela_rett": rett, "schermo": schermo,
            "bordi": bordi, "finestra": [0, 0, 1, 1] if finestra else None, "letto": letto}


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    bo = {"alto": [0, 0, 0], "basso": [30, 30, 40], "nero_destra": 0.0, "nero_basso": 0.0}
    A = _oss([3776, 2016], [3788, 2023, 1], [0, 0, 3776, 2016], [3776, 2016], bo)
    B = _oss([2544, 1344], [2548, 1350, 1], [0, 0, 2544, 1344], [2544, 1344], bo)
    C = _oss([3776, 2016], [3788, 2023, 1], [0, 0, 3776, 2016], [3776, 2016], bo)
    e, m = giudica_misura("segue", A, B, B["vista"], "abc")
    prova("gnome: new canvas and screen ⇒ PASS (%s)" % m[:50], e == S.PASS)
    e, _ = giudica_misura("segue", A, C, B["vista"], "abc")
    prova("fault: same size judged as changed ⇒ FAIL", e == S.FAIL)
    Bs = dict(B, schermo=[3776, 2016])
    e, _ = giudica_misura("segue", A, Bs, B["vista"], "abc")
    prova("new canvas but desktop still ⇒ FAIL", e == S.FAIL)
    Bn = dict(B, bordi=dict(bo, nero_destra=0.9))
    e, _ = giudica_misura("segue", A, Bn, B["vista"], "abc")
    prova("new black band ⇒ FAIL", e == S.FAIL)
    K = _oss([3776, 2016], [2548, 1350, 1], [0, 3, 2548, 1360], [3776, 2016], bo)
    K["tela_rett"] = [0, 0, 2528, 1350]
    e, m = giudica_misura("kde", A, K, K["vista"], "abc")
    prova("kde: canvas kept and rescaled ⇒ PASS (%s)" % m[:50], e == S.PASS)
    e, _ = giudica_misura("segue", A, K, K["vista"], "abc")
    prova("fault: kde judged as gnome ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_misura("kde", A, B, B["vista"], "abc")
    prova("fault: gnome judged as kde ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_misura("kde", A, C, B["vista"], "abc")
    prova("kde fault: same size as changed ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_misura("segue", A, dict(B, letto="ab"), B["vista"], "abc")
    prova("text lost ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_misura("segue", A, dict(B, cieco=True, finestra=None), B["vista"], "abc")
    prova("photo failed, good fields ⇒ BLOCKED", e == S.BLOCKED)
    e, _ = giudica_misura("segue", A, dict(C, cieco=True), B["vista"], "abc")
    prova("photo failed, wrong fields ⇒ FAIL", e == S.FAIL)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def osserva(s, testo, nome, schermo_voluto=None):
    """Canvas (fields), screen from inside (field), photo (window, text, edges)."""
    ob = G.aspetta_tela_ferma(s)
    try:
        ob["dpr"] = float(s.g.js("return window.devicePixelRatio || 1;") or 1)
    except Exception:                            # noqa: BLE001
        ob["dpr"] = 1
    v = G.aspetta_testo(s, testo, nome, tetto=12)
    # the screen seen from inside: the last fresh line; if we are waiting for a size,
    # it is given a few seconds (the desktop follows after the canvas)
    sch = None
    fine = time.time() + 12
    while True:
        st = G.ultimo_stato(s)
        if st:
            sch = [st.get("sw"), st.get("sh")]
        if schermo_voluto is None or (sch and abs(sch[0] - schermo_voluto[0]) <= 2
                                      and abs(sch[1] - schermo_voluto[1]) <= 2) \
                or time.time() > fine:
            break
        time.sleep(1.5)
    ob.update({"schermo": sch, "finestra": v.get("finestra"), "letto": v.get("letto"),
               "perche": v.get("perche"), "foto": v.get("foto"), "cieco": v.get("png") is None})
    ob["bordi"] = G.bordi(G.immagine(v["png"]), v.get("finestra")) if v.get("png") else None
    return ob


def breve(ob):
    return ("canvas %s · view %s · rect %s · screen inside %s · read «%s» · edges %s"
            % (ob.get("buffer"), (ob.get("vista") or [None])[:2],
               [round(x) for x in (ob.get("tela_rett") or [])], ob.get("schermo"),
               ob.get("letto"), {k: v for k, v in (ob.get("bordi") or {}).items()
                                  if not k.endswith("_f")}))


def riattacca(s, largo, alto, testo, nome, fam):
    """Detach (browser closed) and reattach with the window at largo x alto."""
    s.spegni_browser()
    time.sleep(2)
    mis = G.accendi_a_misura(s, largo, alto)
    print("   browser restarted at %dx%d: view %s" % (largo, alto, mis), flush=True)
    ok, m, rifiuti, sec = G.entra_con_riprova(s, tetto_s=40)
    if not ok:
        return None, "the reattach at %dx%d does not get in: %s" % (largo, alto, m)
    G.sveglia(s)
    ob0 = G.osserva_tela(s)
    ob = osserva(s, testo, nome, schermo_voluto=None)
    if fam == "segue" and ob.get("buffer") and ob.get("schermo") != ob.get("buffer"):
        ob = osserva(s, testo, nome + "-bis", schermo_voluto=ob.get("buffer"))
    ob["esito"] = ob0.get("esito")
    print("   %s: %s" % (nome, breve(ob)), flush=True)
    return ob, ""


def corpo(o, E):
    fam = famiglia(o.scatola)
    with S.Sessione(o, "018", E) as s:
        try:
            ok, m = s.entra()
            if not ok:
                raise S.Bloccata("without login there is nothing to reattach: " + m)
            ok, t = G.accendi_scena(s)
            if not ok:
                raise S.Bloccata("the scene does not start in the session: " + t[-200:])
            G.sveglia(s)
            v = F16.trova_scena(s)
            if not v.get("finestra"):
                raise S.Bloccata("the scene's window is not seen in the photo: %s"
                                 % v.get("perche"))
            testo = F16.testo_a_caso(4)
            v, note = G.scrivi_la_base(s, v, testo)
            if v.get("letto") != testo:
                raise S.Bloccata("the PREPARATION input does not reach the scene (it is F-004/F-007, "
                                 "not this function): %s" % " | ".join(note))
            A = osserva(s, testo, "A-4k")
            print("   A (creation): %s" % breve(A), flush=True)
            if not A.get("buffer"):
                raise S.Bloccata("the starting canvas cannot be read")

            B, perche = riattacca(s, MISURA_NUOVA[0], MISURA_NUOVA[1], testo, "B-2560", fam)
            if B is None:
                E.metti("F-018", S.FAIL, perche)
                E.metti("P-C", S.FAIL, perche)
                raise S.Bloccata("the reattach at a different size did not get in")
            if abs(B["vista"][0] - A["buffer"][0]) < 64:
                raise S.Bloccata("the browser did not change size (view %s, previous canvas %s):"
                                 " the reattach is not «at a different size»" % (B["vista"], A["buffer"]))
            pan = PANNELLO[o.scatola]
            eB, rB = giudica_misura(fam, A, B, B["vista"][:2], testo, pan)
            ev = [x for x in (A.get("foto"), B.get("foto")) if x]
            E.metti("F-018", eB, rB,
                    atteso=("canvas and desktop at the new size" if fam == "segue" else
                            "⭐ KDE: previous canvas, rescaled by the browser (declared exception)"),
                    osservato="A: %s || B: %s" % (breve(A), breve(B)), evidenze=ev)

            C, perche = riattacca(s, 3840, 2160, testo, "C-4k", fam)
            if C is None:
                E.metti("P-C", S.FAIL, "at 2560x1440 %s; " % eB + perche)
                return
            eC, rC = giudica_misura(fam, B, C, C["vista"][:2], testo, pan)
            eP = S.PASS if (eB == S.PASS and eC == S.PASS) else S.FAIL
            E.metti("P-C", eP, "at 2560x1440: %s · back at 4K: %s — %s"
                    % (eB, eC, rC if eC != S.PASS else rC[:200]),
                    atteso="creation → reattach at a different size → reattach back, "
                           "each time like its family (%s)" % fam,
                    osservato="B: %s || C: %s" % (breve(B), breve(C)),
                    evidenze=ev + [C.get("foto")])

            if o.guasto:
                # 1. the same size (C = A) judged as if it had changed to B
                g1, r1 = giudica_misura(fam, A, C, B["vista"][:2], testo, pan)
                # 2. the reattach at 2560x1440 with the other family's expectation
                altra = "segue" if fam == "kde" else "kde"
                g2, r2 = giudica_misura(altra, A, B, B["vista"][:2], testo, pan)
                visto = g1 == S.FAIL and g2 == S.FAIL
                E.guasto("F-018", visto, "same size as changed ⇒ %s (%s) · expectation "
                         "«%s» on %s ⇒ %s (%s)" % (g1, r1[:140], altra, o.scatola, g2, r2[:140]))
                E.guasto("P-C", g1 == S.FAIL, "the path with the wrong expectation on the way back "
                         "⇒ %s" % g1)
        finally:
            if s.g:
                s.salva_console()
            G.spegni_servitore(s)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
