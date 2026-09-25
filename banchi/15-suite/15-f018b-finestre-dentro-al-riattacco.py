#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f018b — F-018 RIATTACCO A MISURA DIVERSA: LE FINESTRE RESTANO TUTTE DENTRO
           (il difetto D-007)

    python3 15-f018b-finestre-dentro-al-riattacco.py --scatola xfce --browser firefox [--guasto]

  La scena di G6 con una finestra GRANDE (1800x1000): creazione a 4K
  (finestra del browser 3840x2160), la finestra nasce centrata e intera →
  STACCO → riattacco con la finestra del browser a 2560x1440.  Centrata nel 4K
  quella finestra, a 2544x1344, esce di ~240 px a destra e di ~160 in basso;
  il suo punto medio pero' resta dentro, e labwc da solo non la sposta
  (`src/sessione.h`, il riquadro di `SESSIONE_LABWC_TASTIERA`).

F-018b atteso (D-007, deciso dall'utente il 25 set 2026: «va curato»):
  foto: dopo il riattacco piu' piccolo la finestra della scena e' TUTTA dentro
        la tela — il rettangolo ciano (la pagina della scena) ha la STESSA
        misura, in pixel del desktop, che aveva a 4K (± 3 %), e non tocca i
        bordi.  ⇒ «Tutta dentro» e anche «spostata, non rimpicciolita»: ci sta,
        e il prodotto non ha il diritto di stringerla.
        ⚠ Il bordo da solo NON basta: una finestra riportata dentro sta
        proprio contro il bordo, al pixel — e una tagliata dal bordo lo tocca
        uguale.  La MISURA invece le separa: la tagliata e' piu' corta.
  ⭐ su tutti i desktop.  Su KDE (tela tenuta, eccezione dichiarata) la
        finestra resta intera da se'; su GNOME la riporta dentro Mutter; su
        XFCE e LXQt (labwc) il prodotto.

GUASTO: la foto a 4K della creazione, tagliata alla misura NUOVA dall'angolo in
        alto a sinistra — cioe' quel che si vede se al riattacco nessuno sposta
        le finestre (la cura spenta: labwc lascia la finestra dov'era, e
        l'uscita piu' piccola ne mostra l'angolo) ⇒ il giudice deve dire ROSSO.
        E la cura spenta DAVVERO si prova accendendo il server di serie
        (`15-d007-server.sh accendi xfce stock`): stessa scena, ROSSO.
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
FINESTRA = (1800, 1000)       # centrata in 3776x2016 esce da 2544x1344; ci sta
MISURA_NUOVA = (2560, 1440)
TOLL_MISURA = 0.03            # la finestra deve avere la misura di prima (± 3 %)
MARGINE_4K = 4                # a 4K la finestra non deve toccare i bordi (px foto)
ATTESA_CURA_S = 15.0          # quanto si riguarda la foto dopo il riattacco
TOLL_POSTO = 8                # px del desktop: la foto e' ridotta a 960 (~4 px a 4K)


def ciano_in_px(v, tela):
    """Il rettangolo ciano di `guarda_la_scena` in pixel della TELA (desktop):
    (x0, y0, larghezza, altezza) o None."""
    if not v or not v.get("finestra") or not v.get("misura") or not tela:
        return None
    w, h = v["misura"]
    x0, y0, x1, y1 = v["finestra"]
    sx, sy = tela[0] / float(w), tela[1] / float(h)
    return (x0 * sx, y0 * sy, (x1 - x0 + 1) * sx, (y1 - y0 + 1) * sy)


def giudica_dentro(prima, dopo):
    """⭐ F-018b.  prima/dopo: {"finestra": (x0,y0,x1,y1) nella foto,
    "misura": (w,h) della foto, "tela": (W,H) in px del desktop}.
    Torna (esito, ragione)."""
    a = ciano_in_px(prima, prima.get("tela"))
    if not a:
        return S.BLOCKED, "a 4K la finestra della scena non si vede: niente da confrontare"
    w, h = prima["misura"]
    x0, y0, x1, y1 = prima["finestra"]
    if x0 < MARGINE_4K or y0 < MARGINE_4K or x1 > w - 1 - MARGINE_4K or y1 > h - 1 - MARGINE_4K:
        return S.BLOCKED, ("a 4K la finestra tocca gia' un bordo (%s in %dx%d): la scena non "
                           "e' quella voluta" % (prima["finestra"], w, h))
    b = ciano_in_px(dopo, dopo.get("tela"))
    if not b:
        return S.FAIL, "dopo il riattacco la finestra della scena non si vede (%s)" % (
            (dopo or {}).get("perche") or "nessun ciano")
    dl, da = b[2] / a[2], b[3] / a[3]
    probl = []
    if dl < 1 - TOLL_MISURA or da < 1 - TOLL_MISURA:
        # tagliata dal bordo (fuori) o rimpicciolita: tutt'e due NO
        bw, bh = dopo["misura"]
        bx0, by0, bx1, by1 = dopo["finestra"]
        tocca = [n for n, t in (("destro", bx1 >= bw - 2), ("basso", by1 >= bh - 2),
                                ("sinistro", bx0 <= 1), ("alto", by0 <= 1)) if t]
        probl.append("la finestra si vede %.0fx%.0f, a 4K era %.0fx%.0f (%.0f %% x %.0f %%)%s"
                     % (b[2], b[3], a[2], a[3], 100 * dl, 100 * da,
                        (": TAGLIATA dal bordo %s — e' in parte FUORI dallo schermo"
                         % "/".join(tocca)) if tocca else
                        ": e' stata RIMPICCIOLITA pur standoci"))
    elif dl > 1 + TOLL_MISURA or da > 1 + TOLL_MISURA:
        probl.append("la finestra si vede %.0fx%.0f, a 4K era %.0fx%.0f: piu' grande? la "
                     "foto non torna" % (b[2], b[3], a[2], a[3]))
    if probl:
        return S.FAIL, "; ".join(probl)
    return S.PASS, ("finestra intera %.0fx%.0f (a 4K %.0fx%.0f) in (%.0f,%.0f) della tela "
                    "%dx%d" % (b[2], b[3], a[2], a[3], b[0], b[1], dopo["tela"][0],
                               dopo["tela"][1]))


def giudica_indietro(prima, dopo, stesso_posto):
    """⭐ F-018c: indietro alla misura di partenza la finestra e' intera e della
    misura di prima; con `stesso_posto` (labwc) anche nel posto di prima."""
    e, r = giudica_dentro(prima, dopo)
    if e != S.PASS or not stesso_posto:
        return e, r
    a = ciano_in_px(prima, prima.get("tela"))
    b = ciano_in_px(dopo, dopo.get("tela"))
    dx, dy = b[0] - a[0], b[1] - a[1]
    if abs(dx) > TOLL_POSTO or abs(dy) > TOLL_POSTO:
        return S.FAIL, ("indietro a 4K la finestra e' intera ma SPOSTATA di (%+.0f, %+.0f) px "
                        "rispetto alla creazione: la scorciatoia ha mosso una finestra che "
                        "stava gia' dentro" % (dx, dy))
    return S.PASS, "%s · nel posto di prima (%+.0f, %+.0f px)" % (r, dx, dy)


def taglia(png, largo, alto):
    """⛔ Il GUASTO: la foto a piena risoluzione tagliata a largo x alto
    dall'angolo in alto a sinistra — lo schermo piu' piccolo con le finestre
    rimaste dov'erano."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    fuori = io.BytesIO()
    im.crop((0, 0, min(largo, im.size[0]), min(alto, im.size[1]))).save(fuori, "PNG")
    return fuori.getvalue()


def guarda_png(png):
    """`guarda_la_scena` su un png gia' in mano (il guasto)."""
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
        """Una tela `tela` col rettangolo ciano `rett` (px desktop), ridotta
        come la riduce `G.immagine`: (vista, png)."""
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
    prova("riportata dentro, stessa misura ⇒ PASS (%s)" % m[:60], e == S.PASS)
    Bb, _ = foto((2544, 1344), (743, 343, 2543, 1343))           # contro il bordo, al pixel
    e, m = giudica_dentro(A, Bb)
    prova("contro il bordo destro/basso ma intera ⇒ PASS", e == S.PASS)
    T = guarda_png(taglia(pngA, 2544, 1344))
    T["tela"] = [2544, 1344]
    e, m = giudica_dentro(A, T)
    prova("guasto: 4K tagliata (cura spenta) ⇒ FAIL (%s)" % m[:70], e == S.FAIL)
    Bp, _ = foto((2544, 1344), (100, 100, 100 + 1399, 100 + 799))   # dentro ma stretta
    e, m = giudica_dentro(A, Bp)
    prova("rimpicciolita pur standoci ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_dentro(A, {"finestra": None, "misura": [960, 507], "tela": [2544, 1344]})
    prova("finestra sparita ⇒ FAIL", e == S.FAIL)
    Ab, _ = foto((3776, 2016), (3000, 522, 3775, 1521))
    e, _ = giudica_dentro(Ab, B)
    prova("a 4K gia' contro il bordo ⇒ BLOCKED (scena sbagliata)", e == S.BLOCKED)
    K, _ = foto((3776, 2016), (988, 522, 988 + 1799, 522 + 999))   # KDE: tela tenuta
    e, _ = giudica_dentro(A, K)
    prova("kde: tela tenuta, finestra intera ⇒ PASS", e == S.PASS)
    e, m = giudica_indietro(A, dict(A), True)
    prova("indietro a 4K nel posto di prima ⇒ PASS (%s)" % m[-40:], e == S.PASS)
    Cs, _ = foto((3776, 2016), (988, 522 + 13, 988 + 1799, 522 + 13 + 999))
    e, m = giudica_indietro(A, Cs, True)
    prova("guasto: indietro scesa di mezza barra (13 px) ⇒ FAIL (%s)" % m[:60], e == S.FAIL)
    e, _ = giudica_indietro(A, Cs, False)
    prova("gnome/kde: il posto non si giudica ⇒ PASS", e == S.PASS)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def osserva(s, nome):
    ob = G.aspetta_tela_ferma(s)
    v = G.guarda_la_scena(s, nome)
    v["tela"] = ob.get("buffer")
    v["vista"] = ob.get("vista")
    return v


def breve(v):
    return "tela %s · vista %s · ciano %s (px desktop %s)" % (
        v.get("tela"), (v.get("vista") or [None])[:2], v.get("finestra"),
        [round(x) for x in (ciano_in_px(v, v.get("tela")) or [])])


def corpo(o, E):
    with S.Sessione(o, "918", E) as s:
        try:
            if o.ssd:
                # ⭐ la finestra della scena con la barra del titolo di labwc (la
                #   strada «con la barra» della scorciatoia, quella delle app Qt di
                #   LXQt): una regola nel rc.xml DELL'UTENTE, che su XFCE labwc
                #   somma al nostro (`-m`).  ⚠ Prima dell'accesso: labwc legge la
                #   configurazione quando nasce.
                if o.scatola != "xfce":
                    raise S.Bloccata("--ssd vale solo su xfce: su LXQt la configurazione "
                                     "di labwc e' solo del prodotto (-C)")
                c, t = s.sc.dentro(
                    "h=/home/{c}; install -d -o {c} -g {c} $h/.config $h/.config/labwc; "
                    "printf '%s\\n' '<?xml version=\"1.0\"?><labwc_config><windowRules>"
                    "<windowRule identifier=\"firefox*\" serverDecoration=\"yes\"/>"
                    "</windowRules></labwc_config>' > $h/.config/labwc/rc.xml; "
                    "chown {c}: $h/.config/labwc/rc.xml; cat $h/.config/labwc/rc.xml"
                    .format(c=s.chi), 30)
                print("   --ssd: rc.xml dell'utente: %s" % t.strip()[-160:], flush=True)
            ok, m = s.entra()
            if not ok:
                raise S.Bloccata("senza accesso non c'e' niente da riattaccare: " + m)
            ok, t = G.accendi_scena(s, FINESTRA)
            if not ok:
                raise S.Bloccata("la scena non si accende nella sessione: " + t[-200:])
            G.sveglia(s)
            v = F16.trova_scena(s)
            if not v.get("finestra"):
                raise S.Bloccata("la finestra della scena non si vede nella foto: %s"
                                 % v.get("perche"))
            time.sleep(2)
            A = osserva(s, "A-4k")
            print("   A (creazione): %s" % breve(A), flush=True)
            if not A.get("tela") or not A.get("finestra"):
                raise S.Bloccata("a 4K la tela o la finestra non si leggono: %s" % breve(A))

            # ── STACCO e riattacco piu' piccolo
            s.spegni_browser()
            time.sleep(2)
            mis = G.accendi_a_misura(s, *MISURA_NUOVA)
            print("   browser riacceso a %dx%d: vista %s" % (MISURA_NUOVA + (mis,)), flush=True)
            ok, m, _rif, _sec = G.entra_con_riprova(s, tetto_s=40)
            if not ok:
                E.metti("F-018b", S.FAIL, "il riattacco a %dx%d non entra: %s"
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
            print("   B (riattacco): %s" % breve(B), flush=True)
            if B.get("tela") and A.get("tela") and o.scatola != "kde" \
                    and abs(B["tela"][0] - A["tela"][0]) < 64:
                raise S.Bloccata("la tela non ha cambiato misura (%s → %s): il riattacco non "
                                 "e' «piu' piccolo»" % (A["tela"], B["tela"]))
            ev = [x for x in (A.get("foto"), B.get("foto")) if x]
            E.metti("F-018b", eB, rB,
                    atteso="la finestra della scena TUTTA dentro la tela, della misura di "
                           "prima (spostata, non rimpicciolita)",
                    osservato="A: %s || B: %s" % (breve(A), breve(B)), evidenze=ev)

            # ── e INDIETRO a 4K: la finestra torna intera, e su labwc DOV'ERA —
            #    labwc rimette la posizione di prima dei cambi di misura
            #    (`last_layout_geometry`), e la scorciatoia del prodotto, su una
            #    finestra gia' dentro, NON deve spostarla di un pixel (se la
            #    spostasse — mezza barra del titolo in giu', il rischio di
            #    `MoveToCursor` — qui si vedrebbe)
            s.spegni_browser()
            time.sleep(2)
            G.accendi_a_misura(s, 3840, 2160)
            ok, m, _rif, _sec = G.entra_con_riprova(s, tetto_s=40)
            if not ok:
                E.metti("F-018c", S.FAIL, "il riattacco indietro a 4K non entra: %s" % m)
            else:
                G.sveglia(s)
                time.sleep(2)
                C = osserva(s, "C-4k")
                print("   C (indietro a 4K): %s" % breve(C), flush=True)
                eC, rC = giudica_indietro(A, C, o.scatola in ("xfce", "lxqt"))
                E.metti("F-018c", eC, rC,
                        atteso="indietro a 4K la finestra intera, della misura di prima; su "
                               "labwc anche nel posto di prima (± %d px)" % TOLL_POSTO,
                        osservato="A: %s || C: %s" % (breve(A), breve(C)),
                        evidenze=[x for x in (A.get("foto"), C.get("foto")) if x])
                if o.guasto:
                    # la finestra scesa di mezza barra del titolo (13 px): ROSSO
                    Cg = dict(C, finestra=[C["finestra"][0], C["finestra"][1] + 4,
                                           C["finestra"][2], C["finestra"][3] + 4]) \
                        if C.get("finestra") else C
                    g, r = giudica_indietro(A, Cg, True)
                    E.guasto("F-018c", g == S.FAIL, "la finestra di C scesa di ~16 px ⇒ %s "
                             "(%s)" % (g, r[:160]))

            if o.guasto:
                if not A.get("png"):
                    E.guasto("F-018b", None, "la foto a 4K non c'e' piu': niente da tagliare")
                else:
                    tl, ta = B.get("tela") or (MISURA_NUOVA[0] - 16, MISURA_NUOVA[1] - 96)
                    if o.scatola == "kde":
                        tl, ta = B.get("vista")[:2] if B.get("vista") else (tl, ta)
                    T = guarda_png(taglia(A["png"], int(tl), int(ta)))
                    T["tela"] = [int(tl), int(ta)]
                    g, r = giudica_dentro(A, T)
                    E.guasto("F-018b", g == S.FAIL,
                             "la 4K tagliata a %dx%d (le finestre rimaste dov'erano) ⇒ %s (%s)"
                             % (tl, ta, g, r[:200]))
        finally:
            if s.g:
                s.salva_console()
            G.spegni_servitore(s)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica,
                      extra=lambda a: a.add_argument(
                          "--ssd", action="store_true",
                          help="(xfce) la finestra della scena con la barra del titolo "
                               "di labwc: la strada «con la barra» della cura")))
