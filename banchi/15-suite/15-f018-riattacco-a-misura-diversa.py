#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f018 — F-018 RIATTACCO A MISURA DIVERSA · percorso P-C

    python3 15-f018-riattacco-a-misura-diversa.py --scatola xfce --browser firefox [--guasto]

  P-C  creazione a 4K (finestra del browser 3840x2160) → applicazione aperta e
       testo scritto → STACCO → riattacco con la finestra a 2560x1440 → STACCO
       → riattacco INDIETRO a 4K.  Ad ogni riattacco: la tela, il desktop, lo
       stato.  (La risoluzione a caldo non c'e': la misura cambia SOLO
       riattaccandosi — `DECISIONI.md` §5.1-bis.)

F-018  atteso (`SPECIFICHE.md` §6.1-§6.3, `src/rcp.c` ~2998, `src/figlio.c`
       `misura_del_palco`):
   GNOME, XFCE, LXQt — la TELA prende la misura nuova e il DESKTOP la segue:
       · campo: la tela della pagina (`#schermo` width×height) e' quella della
         vista nuova (± 16 px: la pagina la tronca ai multipli di 16);
       · campo: dentro la sessione un programma vede lo SCHERMO di quella
         misura (screen.width×height di firefox-esr nella sessione = l'uscita
         del compositore);
       · foto: la finestra della scena c'e' e il testo si legge; i bordi della
         foto (le righe in alto e in basso, dove stanno i pannelli) sono quelli
         di prima; nessuna fascia NERA nuova a destra o in basso (sfondo pieno).
   ⭐ KDE — ECCEZIONE DICHIARATA dall'utente (KWin < 6.8, SPECIFICHE ~851,
       §6.3): la tela RESTA quella di prima e il browser RISCALA:
       · campo: tela uguale a prima; il rettangolo della tela nel browser sta
         dentro la vista nuova e ne riempie un lato (≥ 90 %);
       · campo: lo schermo visto da dentro e' quello di prima;
       · foto: come sopra (finestra, testo, bordi).
       ⇒ su KDE QUESTO e' il PASS.
P-C    atteso: i due riattacchi (a 2560x1440 e indietro a 4K) tutti e due giusti.

GUASTO: il giudice riceve il riattacco INDIETRO (misura uguale a quella di
       partenza) come se fosse a 2560x1440 — «il riattacco alla stessa misura
       giudicato come se fosse cambiata» — e poi il riattacco a 2560x1440 con
       l'atteso dell'ALTRA famiglia (KDE giudicato come GNOME e viceversa).
       Tutt'e due devono dare ROSSO, su osservazioni vere.
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
TOLL_TELA = 16            # la pagina tronca la tela ai multipli di 16 (fc0fbff)
TOLL_BORDO = 40           # colore medio delle righe di bordo
RIEMPIE = 0.90            # su KDE la tela riscalata riempie almeno un lato


def famiglia(desktop):
    return "kde" if desktop == "kde" else "segue"


# il lato del pannello che corre per TUTTA la larghezza (visto nelle foto del 24-25 set)
PANNELLO = {"gnome": "alto", "kde": "basso", "xfce": "alto", "lxqt": "basso"}


def confronta_pannello(bp, bd, lato):
    """Distanza massima fra le fette del lato del pannello, prima e dopo, fuori
    dalle fette coperte dalla finestra in una delle due foto.  (d, quante)."""
    fp, fd = bp.get(lato + "_f"), bd.get(lato + "_f")
    if not fp or not fd:
        return G.distanza(bp[lato], bd[lato]), 1
    via = set(bp.get("coperte") or []) | set(bd.get("coperte") or [])
    ks = [k for k in range(len(fp)) if k not in via]
    if not ks:
        return None, 0
    # la MEDIANA delle fette: le icone e l'orologio del pannello stanno a pixel
    # fissi e cambiano fetta quando cambia la larghezza; il pannello che manca
    # cambia TUTTE le fette
    d = sorted(G.distanza(fp[k], fd[k]) for k in ks)
    return d[len(d) // 2], len(ks)


def giudica_misura(fam, prima, dopo, vista_attesa, testo, pannello="alto"):
    """⭐ F-018 per un riattacco.  prima/dopo: le osservazioni (vedi `osserva`).
    `vista_attesa` [l, a]: la vista in cui il browser disegna adesso.
    Torna (esito, ragione)."""
    probl, bene = [], []
    b0, b1 = prima.get("buffer"), dopo.get("buffer")
    if not b0 or not b1:
        return S.BLOCKED, "la tela della pagina non si legge (prima %s, dopo %s)" % (b0, b1)
    vl, va = vista_attesa[0], vista_attesa[1]
    sch = dopo.get("schermo")
    if fam == "segue":
        if abs(b1[0] - vl) > TOLL_TELA or abs(b1[1] - va) > TOLL_TELA:
            probl.append("la tela e' %dx%d, la vista %dx%d: la tela NON ha preso la misura "
                         "della finestra" % (b1[0], b1[1], vl, va))
        else:
            bene.append("tela %dx%d per la vista %dx%d" % (b1[0], b1[1], vl, va))
        if not sch:
            probl.append("lo schermo visto da dentro la sessione non si legge")
        elif abs(sch[0] - b1[0]) > 2 or abs(sch[1] - b1[1]) > 2:
            probl.append("dentro la sessione lo schermo e' %dx%d, la tela %dx%d: il desktop "
                         "NON ha seguito" % (sch[0], sch[1], b1[0], b1[1]))
        else:
            bene.append("dentro, lo schermo e' %dx%d" % tuple(sch))
    else:
        if list(b1) != list(b0):
            probl.append("su KDE la tela doveva restare %dx%d (KWin < 6.8), e' %dx%d"
                         % (b0[0], b0[1], b1[0], b1[1]))
        else:
            bene.append("tela tenuta %dx%d (KWin < 6.8, eccezione dichiarata)" % tuple(b1))
        r = dopo.get("tela_rett") or [0, 0, 0, 0]
        if r[2] > vl + 1 or r[3] > va + 1:
            probl.append("la tela nel browser e' %dx%d, piu' grande della vista %dx%d: il "
                         "browser NON riscala" % (r[2], r[3], vl, va))
        elif max(r[2] / max(1, vl), r[3] / max(1, va)) < RIEMPIE:
            probl.append("la tela nel browser e' %dx%d nella vista %dx%d: non la riempie"
                         % (r[2], r[3], vl, va))
        else:
            bene.append("riscalata a %dx%d nella vista %dx%d" % (r[2], r[3], vl, va))
        s0 = prima.get("schermo")
        if sch and s0 and list(sch) != list(s0):
            probl.append("su KDE lo schermo dentro doveva restare %s, e' %s" % (s0, sch))
    # la foto: finestra, testo, bordi
    if dopo.get("cieco"):
        if probl:
            return S.FAIL, "; ".join(probl) + " (e la foto non si e' potuta fare)"
        return S.BLOCKED, ("i campi tornano (%s) ma la foto non si e' potuta fare: %s"
                           % (" · ".join(bene), dopo.get("perche")))
    if not dopo.get("finestra"):
        probl.append("nella foto la finestra della scena non c'e' (%s)" % dopo.get("perche"))
    elif dopo.get("letto") != testo:
        probl.append("nella foto la striscia dice «%s», scritto «%s»" % (dopo.get("letto"), testo))
    else:
        bene.append("finestra e testo «%s» in foto" % testo)
    bp, bd = prima.get("bordi"), dopo.get("bordi")
    if bp and bd:
        d, n = confronta_pannello(bp, bd, pannello)
        if d is None:
            probl.append("il bordo del pannello (%s) e' tutto coperto dalla finestra" % pannello)
        elif d > TOLL_BORDO:
            probl.append("il bordo del pannello (%s) e' cambiato (scarto mediano %d su %d fette "
                         "libere): il pannello non e' al bordo nuovo" % (pannello, d, n))
        else:
            bene.append("pannello al bordo %s (%d fette, scarto %d)" % (pannello, n, d))
        for lato in ("nero_destra", "nero_basso"):
            if bd[lato] > bp[lato] + 0.5:
                probl.append("una fascia NERA nuova (%s %.0f %%, prima %.0f %%): lo sfondo non "
                             "e' pieno" % (lato, 100 * bd[lato], 100 * bp[lato]))
    else:
        probl.append("i bordi della foto non si leggono")
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
    prova("gnome: tela e schermo nuovi ⇒ PASS (%s)" % m[:50], e == S.PASS)
    e, _ = giudica_misura("segue", A, C, B["vista"], "abc")
    prova("guasto: stessa misura giudicata come cambiata ⇒ FAIL", e == S.FAIL)
    Bs = dict(B, schermo=[3776, 2016])
    e, _ = giudica_misura("segue", A, Bs, B["vista"], "abc")
    prova("tela nuova ma desktop fermo ⇒ FAIL", e == S.FAIL)
    Bn = dict(B, bordi=dict(bo, nero_destra=0.9))
    e, _ = giudica_misura("segue", A, Bn, B["vista"], "abc")
    prova("fascia nera nuova ⇒ FAIL", e == S.FAIL)
    K = _oss([3776, 2016], [2548, 1350, 1], [0, 3, 2548, 1360], [3776, 2016], bo)
    K["tela_rett"] = [0, 0, 2528, 1350]
    e, m = giudica_misura("kde", A, K, K["vista"], "abc")
    prova("kde: tela tenuta e riscalata ⇒ PASS (%s)" % m[:50], e == S.PASS)
    e, _ = giudica_misura("segue", A, K, K["vista"], "abc")
    prova("guasto: kde giudicato come gnome ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_misura("kde", A, B, B["vista"], "abc")
    prova("guasto: gnome giudicato come kde ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_misura("kde", A, C, B["vista"], "abc")
    prova("guasto kde: stessa misura come cambiata ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_misura("segue", A, dict(B, letto="ab"), B["vista"], "abc")
    prova("testo perso ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_misura("segue", A, dict(B, cieco=True, finestra=None), B["vista"], "abc")
    prova("foto fallita, campi buoni ⇒ BLOCKED", e == S.BLOCKED)
    e, _ = giudica_misura("segue", A, dict(C, cieco=True), B["vista"], "abc")
    prova("foto fallita, campi sbagliati ⇒ FAIL", e == S.FAIL)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def osserva(s, testo, nome, schermo_voluto=None):
    """Tela (campi), schermo da dentro (campo), foto (finestra, testo, bordi)."""
    ob = G.aspetta_tela_ferma(s)
    v = G.aspetta_testo(s, testo, nome, tetto=12)
    # lo schermo visto da dentro: l'ultima riga fresca; se aspettiamo una misura,
    # le si da' qualche secondo (il desktop segue dopo la tela)
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
    return ("tela %s · vista %s · rett %s · schermo dentro %s · letto «%s» · bordi %s"
            % (ob.get("buffer"), (ob.get("vista") or [None])[:2],
               [round(x) for x in (ob.get("tela_rett") or [])], ob.get("schermo"),
               ob.get("letto"), {k: v for k, v in (ob.get("bordi") or {}).items()
                                  if not k.endswith("_f")}))


def riattacca(s, largo, alto, testo, nome, fam):
    """Stacco (browser chiuso) e riattacco con la finestra a largo x alto."""
    s.spegni_browser()
    time.sleep(2)
    mis = G.accendi_a_misura(s, largo, alto)
    print("   browser riacceso a %dx%d: vista %s" % (largo, alto, mis), flush=True)
    ok, m, rifiuti, sec = G.entra_con_riprova(s, tetto_s=40)
    if not ok:
        return None, "il riattacco a %dx%d non entra: %s" % (largo, alto, m)
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
                raise S.Bloccata("senza accesso non c'e' niente da riattaccare: " + m)
            ok, t = G.accendi_scena(s)
            if not ok:
                raise S.Bloccata("la scena non si accende nella sessione: " + t[-200:])
            G.sveglia(s)
            v = F16.trova_scena(s)
            if not v.get("finestra"):
                raise S.Bloccata("la finestra della scena non si vede nella foto: %s"
                                 % v.get("perche"))
            testo = F16.testo_a_caso(4)
            v, note = G.scrivi_la_base(s, v, testo)
            if v.get("letto") != testo:
                raise S.Bloccata("l'input di PREPARAZIONE non arriva alla scena (e' F-004/F-007, "
                                 "non questa funzione): %s" % " | ".join(note))
            A = osserva(s, testo, "A-4k")
            print("   A (creazione): %s" % breve(A), flush=True)
            if not A.get("buffer"):
                raise S.Bloccata("la tela di partenza non si legge")

            B, perche = riattacca(s, MISURA_NUOVA[0], MISURA_NUOVA[1], testo, "B-2560", fam)
            if B is None:
                E.metti("F-018", S.FAIL, perche)
                E.metti("P-C", S.FAIL, perche)
                raise S.Bloccata("il riattacco a misura diversa non e' entrato")
            if abs(B["vista"][0] - A["buffer"][0]) < 64:
                raise S.Bloccata("il browser non ha cambiato misura (vista %s, tela di prima %s):"
                                 " il riattacco non e' «a misura diversa»" % (B["vista"], A["buffer"]))
            pan = PANNELLO[o.scatola]
            eB, rB = giudica_misura(fam, A, B, B["vista"][:2], testo, pan)
            ev = [x for x in (A.get("foto"), B.get("foto")) if x]
            E.metti("F-018", eB, rB,
                    atteso=("tela e desktop alla misura nuova" if fam == "segue" else
                            "⭐ KDE: tela di prima, riscalata dal browser (eccezione dichiarata)"),
                    osservato="A: %s || B: %s" % (breve(A), breve(B)), evidenze=ev)

            C, perche = riattacca(s, 3840, 2160, testo, "C-4k", fam)
            if C is None:
                E.metti("P-C", S.FAIL, "a 2560x1440 %s; " % eB + perche)
                return
            eC, rC = giudica_misura(fam, B, C, C["vista"][:2], testo, pan)
            eP = S.PASS if (eB == S.PASS and eC == S.PASS) else S.FAIL
            E.metti("P-C", eP, "a 2560x1440: %s · indietro a 4K: %s — %s"
                    % (eB, eC, rC if eC != S.PASS else rC[:200]),
                    atteso="creazione → riattacco a misura diversa → riattacco indietro, "
                           "ogni volta come la sua famiglia (%s)" % fam,
                    osservato="B: %s || C: %s" % (breve(B), breve(C)),
                    evidenze=ev + [C.get("foto")])

            if o.guasto:
                # 1. la stessa misura (C = A) giudicata come se fosse cambiata a B
                g1, r1 = giudica_misura(fam, A, C, B["vista"][:2], testo, pan)
                # 2. il riattacco a 2560x1440 con l'atteso dell'altra famiglia
                altra = "segue" if fam == "kde" else "kde"
                g2, r2 = giudica_misura(altra, A, B, B["vista"][:2], testo, pan)
                visto = g1 == S.FAIL and g2 == S.FAIL
                E.guasto("F-018", visto, "stessa misura come cambiata ⇒ %s (%s) · atteso "
                         "«%s» su %s ⇒ %s (%s)" % (g1, r1[:140], altra, o.scatola, g2, r2[:140]))
                E.guasto("P-C", g1 == S.FAIL, "il percorso con l'atteso sbagliato al ritorno "
                         "⇒ %s" % g1)
        finally:
            if s.g:
                s.salva_console()
            G.spegni_servitore(s)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
