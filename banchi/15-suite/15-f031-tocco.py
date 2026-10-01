#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f031 — F-031 IL TOCCO (Android): il dito muove il puntatore, il tocco clicca,
          il tocco-e-mezzo trascina

    python3 15-f031-tocco.py --scatola gnome --browser telefono [--guasto]

⭐ SOLO col telefono VERO (fase 19 §5, `banchi/19-android/`): Chrome del
telefono dell'utente, comandato dal portatile.  Gli altri browser la saltano.

La scena e i GIUDICI sono quelli di F-004 (`15-f004-il-mouse.py`, `15-g2-scena.py`):
cambia solo il gesto, che qui e' un DITO col modello a trackpad di
`SPECIFICHE.md` §7.1-7.2 (il dito trascina un puntatore disegnato; il tap
clicca dove sta il puntatore, non dove cade il dito):

  dito-muove     un dito VERO (`adb shell input swipe`) porta il puntatore in due
                 punti del blocco BLU: la pagina remota dice dove l'ha visto
                 (giudice di F-004 «movimento», entro 5 %)
  tocco-clic     il puntatore sul bottone VERDE, poi un tocco VERO
                 (`adb shell input tap`): il contatore +1, pulsante 0
                 (giudice di F-004 «clic sinistro»)
  tocco-e-mezzo  il puntatore sul box GIALLO, poi tap e subito dito giu' che
                 trascina a destra del 15 % della pagina: il box si sposta di
                 quanto (giudice di F-004 «trascinamento»).
                 ⚠ Questo gesto va col protocollo DevTools (`Input.dispatchTouchEvent`,
                 eventi di tocco veri nel renderer di Chrome Android): fra il tap e il
                 secondo contatto la pagina concede 300 ms (`TOCCO_SOGLIE.T_SEQUENZA`)
                 e due comandi `adb shell input` di fila non ci stanno.

  Il puntatore si PORTA sui bersagli con trascinamenti del protocollo (e' la
  preparazione, non il gesto giudicato).  Prima di tutto un dito vero corto
  (taratura): dice dove la pagina sta sullo schermo e mette la pagina nel modo
  a tocco, come farebbe la mano.

GUASTO (--guasto, stessa sessione): ogni gesto A VUOTO, con lo stesso giudice:
  dito-muove ⇒ il dito porta il puntatore FUORI dal blocco · tocco-clic ⇒ il
  puntatore fuori dal bottone · tocco-e-mezzo ⇒ fra il tap e il secondo
  contatto 700 ms (oltre la soglia: non e' piu' un tocco-e-mezzo, e il box non
  deve muoversi).  Il guasto e' VISTO se OGNI gesto da' rosso.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G2 = S._carica("g2scena", os.path.join(S.QUI, "15-g2-scena.py"))
F4 = S._carica("f004", os.path.join(S.QUI, "15-f004-il-mouse.py"))

FUNZIONI = ("F-031",)
SOLO_TELEFONO = True
GESTI = ("dito-muove", "tocco-clic", "tocco-e-mezzo")
PUNTI_DITO = ((0.25, 0.3), (0.7, 0.6))
DITI_VERI_MAX = 8        # un utente corregge: piu' passate corte di dito per arrivare (ognuna ≤ 30 % della tela)
PAUSA_SANA_S = 0.12      # fra il tap e il secondo contatto (soglia della pagina 0,3 s)
PAUSA_GUASTO_S = 0.7


def certifica():
    """I giudici sono quelli di F-004: si certificano la'."""
    print("   F-031 usa i giudici di F-004 (movimento, clic, box): li certifico")
    return F4.certifica()


def vetro(mp, x, y):
    return mp.vetro(x, y)


def fa_gesto(nome, s, sc, mp, geo, guasto, note):
    g = s.g
    if sc.comanda("reset") is None:
        return S.BLOCKED, "la scena non ha risposto al reset"
    R = sc.rett
    W, H = R["W"], R["H"]
    fuori = vetro(mp, W * 0.33, H * 0.12)        # fra il pad e il bottone: fuori da tutto
    if nome == "dito-muove":
        esiti = []
        for fx, fy in PUNTI_DITO:
            atteso = (fx, fy)
            tx, ty = fuori if guasto else vetro(mp, *F4.nel_rett(R["pad"], fx, fy))
            st = None
            for _i in range(DITI_VERI_MAX):
                p = g.puntatore_vetro(geo)
                if p is None:
                    return S.BLOCKED, "la pagina non dice dove sta il puntatore (REMOTIX.tocco)"
                if max(abs(tx - p[0]), abs(ty - p[1])) <= 2:
                    break
                t = g.scorri_vero(geo, tx - p[0], ty - p[1])
                if not t:
                    return S.BLOCKED, ("il dito vero non e' arrivato alla pagina (adb swipe "
                                       "da %s per (%.0f,%.0f) px del vetro; tocchi visti %d)"
                                       % (getattr(g, "ultimo_dito", None), tx - p[0], ty - p[1],
                                          len(g.tocchi_visti())))
                note.append("dito su «%s» a (%.0f,%.0f)" % (t.get("su"), t["x"], t["y"]))
            st = sc.aspetta(lambda q, a=atteso: F4.giudica_movimento(q, a)[0] == S.PASS,
                            F4.ATTESA_S)
            esiti.append(F4.giudica_movimento(st, atteso))
            if esiti[-1][0] != S.PASS:
                break
        brutti = [e for e in esiti if e[0] != S.PASS]
        return brutti[0] if brutti else (S.PASS, "due punti: " + " · ".join(e[1] for e in esiti))
    if nome == "tocco-clic":
        tx, ty = fuori if guasto else vetro(mp, *F4.centro_r(R["bot"]))
        err = g.porta_il_puntatore(geo, tx, ty)
        if err is None or err > 3:
            return S.BLOCKED, "il puntatore non si porta sul bersaglio (errore %s px)" % err
        t = g.tap_vero(geo)
        if not t:
            return S.BLOCKED, "il tocco vero non e' arrivato alla pagina (adb tap)"
        note.append("tocco su «%s» a (%.0f,%.0f)" % (t.get("su"), t["x"], t["y"]))
        st = sc.aspetta(lambda q: F4.giudica_clic(q)[0] == S.PASS, F4.ATTESA_S)
        return F4.giudica_clic(st)
    if nome == "tocco-e-mezzo":
        x0, y0 = F4.centro_r(R["box"])
        x1 = x0 + F4.SPINTA * W
        a0, b0 = vetro(mp, x0, y0)
        a1, _b1 = vetro(mp, x1, y0)
        err = g.porta_il_puntatore(geo, a0, b0)
        if err is None or err > 3:
            return S.BLOCKED, "il puntatore non si porta sul box (errore %s px)" % err
        d = a1 - a0
        cx, cy = g._centro_tela(geo)
        fx, fy = cx - d / 2.0, cy                 # il dito: i due capi dentro la tela
        g.guardia(subito=True)
        c = g.cdp.chiama
        c("Input.dispatchTouchEvent", type="touchStart", touchPoints=[{"x": fx, "y": fy}])
        time.sleep(0.06)
        c("Input.dispatchTouchEvent", type="touchEnd", touchPoints=[])
        time.sleep(PAUSA_GUASTO_S if guasto else PAUSA_SANA_S)
        punti = [(fx + d * i / 15.0, fy) for i in range(1, 16)]
        g.dito_cdp([(fx, fy)] + punti, pausa_s=0.04, tieni_s=0.15)
        st = sc.aspetta(lambda q: F4.giudica_box(q, x1 - x0, H)[0] == S.PASS, F4.ATTESA_S)
        return F4.giudica_box(st, x1 - x0, H)
    raise ValueError(nome)


def passata(s, sc, mp, geo, guasto):
    righe = []
    for nome in GESTI:
        note = []
        try:
            e, m = fa_gesto(nome, s, sc, mp, geo, guasto, note)
        except S.telefono().ChiamataInCorso:
            raise
        except Exception as x:                   # noqa: BLE001
            e, m = S.BLOCKED, "il banco e' caduto nel gesto: %s" % str(x)[:160]
        if e == S.FAIL and not guasto:
            print("   ⚠ %s rosso (%s): lo rifaccio per confermarlo" % (nome, m), flush=True)
            try:
                e2, m2 = fa_gesto(nome, s, sc, mp, geo, guasto, note)
            except Exception as x:               # noqa: BLE001
                e2, m2 = S.BLOCKED, "il banco e' caduto nel gesto: %s" % str(x)[:160]
            m = ("⚠ ROSSO al primo tentativo (%s), verde al secondo: %s" % (m, m2)
                 if e2 == S.PASS else "rosso due volte: %s · %s" % (m, m2))
            e = e2
        if note:
            m += " [%s]" % "; ".join(note[-3:])
        print("   %s %-14s %s" % ({S.PASS: "⭐", S.FAIL: "⛔", S.BLOCKED: "⚠"}[e], nome, m),
              flush=True)
        righe.append((nome, e, m))
    return righe


def corpo(o, E):
    if o.browser != "telefono":
        raise S.Bloccata("F-031 e' il tocco del telefono VERO: --browser telefono")
    porta_scena = o.porte_base + 5
    with S.Sessione(o, "031", E) as s:
        sc, mp, geo, dove = G2.prepara(s, porta_scena)
        ev = [dove] if dove else []
        tar = s.g.taratura(geo)
        if not tar:
            raise S.Bloccata("il dito vero di taratura non e' arrivato alla pagina (adb swipe)")
        disp = s.g.disposizione()
        print("   taratura: %s · disposizione «%s»" % (tar, disp), flush=True)
        if disp != "tocco":
            perche = s.g.js("return REMOTIX.tocco.perche ? REMOTIX.tocco.perche() : null")
            E.metti("F-031", S.FAIL, "dopo un dito vero la pagina NON e' nel modo a tocco: «%s» "
                    "(%s)" % (disp, perche), atteso="il modo a tocco (SPECIFICHE §7.2)",
                    osservato=str(perche), evidenze=ev)
            return
        geo = s.geometria() or geo
        atteso = ("il dito porta il puntatore sul BLU dove punta; il tocco clicca il VERDE; "
                  "il tocco-e-mezzo trascina il box GIALLO")
        righe = passata(s, sc, mp, geo, False)
        _p, fin = G2.foto(s, "fine-sana")
        if fin:
            ev.append(fin)
        oss = " · ".join("%s: %s %s" % r for r in righe)
        es = [r[1] for r in righe]
        if S.FAIL in es:
            E.metti("F-031", S.FAIL, "gesti rossi: " + ", ".join(n for n, e, _m in righe
                                                                   if e == S.FAIL),
                    atteso=atteso, osservato=oss, evidenze=ev + [s.salva_console()])
        elif S.BLOCKED in es:
            E.metti("F-031", S.BLOCKED, "gesti non guardati: " + ", ".join(
                "%s (%s)" % (n, m) for n, e, m in righe if e == S.BLOCKED),
                atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-031", S.PASS, "tre gesti su tre: l'effetto c'e' nell'applicazione",
                    atteso=atteso, osservato=oss, evidenze=ev)
        if o.guasto:
            righe = passata(s, sc, mp, geo, True)
            visto = F4.esito_col_guasto([r[1] for r in righe])
            E.guasto("F-031", visto,
                     {True: "ogni gesto a vuoto ha dato rosso",
                      False: "gesti a vuoto VERDI lo stesso: " + ", ".join(
                          n for n, e, _m in righe if e == S.PASS),
                      None: "un gesto a vuoto non si e' potuto guardare"}[visto],
                     atteso="ogni gesto a vuoto ⇒ rosso",
                     osservato=" · ".join("%s: %s %s" % r for r in righe))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
