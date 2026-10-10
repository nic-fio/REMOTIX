#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f031 — F-031 TOUCH (Android): the finger moves the pointer, the tap clicks,
          the tap-and-a-half drags; the on-screen keyboard opens ONLY on request

    python3 15-f031-tocco.py --scatola gnome --browser telefono [--guasto]

⭐ ONLY with the REAL phone (phase 19 §5, `banchi/19-android/`): Chrome on the
user's phone, driven from the laptop.  The other browsers skip it.

The scene and the JUDGES are those of F-004 (`15-f004-il-mouse.py`, `15-g2-scena.py`):
only the gesture changes, which here is a FINGER with the trackpad model of
`SPECIFICHE.md` §7.1-7.2 (the finger drags a drawn pointer; the tap
clicks where the pointer is, not where the finger lands):

  dito-muove     a REAL finger (`adb shell input swipe`) takes the pointer to two
                 points of the BLUE block: the remote page says where it saw it
                 (F-004's «movement» judge, within 5 %)
  tocco-clic     the pointer on the GREEN button, then a REAL tap
                 (`adb shell input tap`): the counter +1, button 0
                 (F-004's «left click» judge)
  tocco-e-mezzo  the pointer on the YELLOW box, then tap and at once finger down that
                 drags right by 15 % of the page: the box moves by
                 that much (F-004's «drag» judge).
                 ⚠ This gesture goes with the DevTools protocol (`Input.dispatchTouchEvent`,
                 real touch events in Chrome Android's renderer): between the tap and the
                 second contact the page allows 300 ms (`TOCCO_SOGLIE.T_SEQUENZA`)
                 and two `adb shell input` commands in a row do not fit.

  tastiera      «keyboard only on request» (DECISIONI §10.28, SPECIFICHE §7.2-7.3):
                 (a) after the login and the three gestures the on-screen keyboard is NOT open;
                 (b) a REAL tap on the page's ⌨ control opens it, and a word
                     written as an on-screen keyboard writes it (composition and
                     commit, DevTools protocol) arrives in the scene's field «a»;
                 (c) a second tap on the control closes it again.
                 ⭐ The state of the keyboard is told by ANDROID (`dumpsys input_method`,
                 `mInputShown`, from the laptop's window), not by the page.

  The pointer is BROUGHT onto the targets with protocol drags (it is the
  preparation, not the gesture judged).  First of all a short real finger
  (calibration): it says where the page is on the screen and puts the page in
  touch mode, as the hand would.

FAULT (--guasto, same session): every gesture IN THE VOID, with the same judge:
  dito-muove ⇒ the finger takes the pointer OUTSIDE the block · tocco-clic ⇒ the
  pointer outside the button · tocco-e-mezzo ⇒ between the tap and the second
  contact 700 ms (beyond the threshold: it is no longer a tap-and-a-half, and the box must not
  move) · tastiera ⇒ the control IN THE VOID (the tap lands 60 px left
  of the ⌨): the keyboard does not open ⇒ red.  The fault is SEEN if EVERY gesture
  gives red.
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
GESTI = ("dito-muove", "tocco-clic", "tocco-e-mezzo", "tastiera")
PAROLA = "prova"
SCARTO_GUASTO = 60       # CSS px: the tap of the control in the void lands left of the ⌨
PUNTI_DITO = ((0.25, 0.3), (0.7, 0.6))
DITI_VERI_MAX = 8        # a user corrects: several short finger passes to get there (each ≤ 30 % of the canvas)
PAUSA_SANA_S = 0.12      # between the tap and the second contact (page threshold 0.3 s)
PAUSA_GUASTO_S = 0.7


def giudica_tastiera(prima, aperta, scritto, chiusa):
    """«Keyboard only on request».  `prima`/`aperta`/`chiusa`: the state read from
    Android (True/False/None) before the control, after the control, after the second
    control; `scritto`: the scene's field «a» (None if not read)."""
    if prima is None:
        return S.BLOCKED, "the keyboard state cannot be read (window /tastiera)"
    if prima:
        return S.FAIL, ("⛔ the on-screen keyboard OPENED by itself after the login and the gestures "
                        "(the decision: only on request)")
    if aperta is None:
        return S.BLOCKED, "after the control the keyboard state cannot be read"
    if not aperta:
        return S.FAIL, "the ⌨ control did NOT open the keyboard"
    if scritto != PAROLA:
        return S.FAIL, ("the keyboard is open, but «%s» written does NOT reach the remote desktop "
                        "(field a=%r)" % (PAROLA, scritto))
    if chiusa is None:
        return S.BLOCKED, "after the second control the keyboard state cannot be read"
    if chiusa:
        return S.FAIL, "the second tap on the ⌨ control did NOT close the keyboard"
    return S.PASS, ("closed after the gestures; the ⌨ opens it, «%s» arrives in the remote field; the ⌨ "
                    "closes it again" % PAROLA)


def certifica():
    """The judges of the three gestures are F-004's: they are certified there.  The
    keyboard one is certified here."""
    print("   F-031 uses F-004's judges (movement, click, box): certifying them")
    r = F4.certifica()
    guai = []

    def prova(cosa, vero):
        print("   %s %s" % ("⭐ ok " if vero else "⛔ NO ", cosa))
        if not vero:
            guai.append(cosa)
    prova("keyboard: all right ⇒ PASS", giudica_tastiera(False, True, PAROLA, False)[0] == S.PASS)
    prova("keyboard: opened by itself ⇒ FAIL", giudica_tastiera(True, True, PAROLA, False)[0] == S.FAIL)
    prova("keyboard: the control in the void (does not open) ⇒ FAIL",
          giudica_tastiera(False, False, "", False)[0] == S.FAIL)
    prova("keyboard: open but the word does not arrive ⇒ FAIL",
          giudica_tastiera(False, True, "", False)[0] == S.FAIL)
    prova("keyboard: a different word ⇒ FAIL",
          giudica_tastiera(False, True, "prov", False)[0] == S.FAIL)
    prova("keyboard: does not close again ⇒ FAIL", giudica_tastiera(False, True, PAROLA, True)[0] == S.FAIL)
    prova("keyboard: unreadable state ⇒ BLOCKED",
          giudica_tastiera(None, True, PAROLA, False)[0] == S.BLOCKED)
    print("⛔ CERTIFICATION FAILED" if guai else "⭐ CERTIFIED (keyboard)")
    return r or (1 if guai else 0)


def tastiera(s, sc, mp, geo, guasto, note):
    """The «tastiera» gesture: see the header.  Returns (outcome, sentence)."""
    g = s.g
    prima = g.tastiera_aperta()
    note.append("keyboard after the gestures: %s" % {True: "OPEN", False: "closed"}.get(prima, "?"))
    if prima is None or prima:
        return giudica_tastiera(prima, None, None, None)
    # the remote desktop's focus in the field «a»: the pointer above it, a REAL tap
    R = sc.rett
    err = g.porta_il_puntatore(geo, *vetro(mp, *F4.centro_r(R["a"])))
    if err is None or err > 3:
        return S.BLOCKED, "the pointer cannot be brought onto the field «a» (error %s px)" % err
    if not g.tap_vero(geo):
        return S.BLOCKED, "the real tap on the field «a» did not reach the page (adb tap)"
    st = sc.comanda("fuoco-a")
    if st is None or st.get("a") != "" or st.get("fuoco") != "a":
        return S.BLOCKED, "the scene is not ready to write: %s" % (st,)
    k = g.comando_tastiera()
    if not k:
        return S.FAIL, "the page does NOT show the ⌨ control with the phone in hand"
    x, y = (k[0] - SCARTO_GUASTO, k[1]) if guasto else (k[0], k[1])
    t = g.tocco_vero_in(x, y)
    note.append("control%s: tap on «%s»" % (" IN THE VOID" if guasto else "",
                                             (t or {}).get("su", "none")))
    aperta = g.aspetta_tastiera(True)
    scritto = None
    chiusa = None
    try:
        if aperta:
            g.scrivi_ime(PAROLA)
            st = sc.aspetta(lambda q: q.get("a") == PAROLA, F4.ATTESA_S)
            scritto = (st or {}).get("a")
            k = g.comando_tastiera() or k
            g.tocco_vero_in(k[0], k[1])
            chiusa = g.aspetta_tastiera(False)
    finally:
        # ⛔ the keyboard does not stay open over the later tests (the fault, the other lines)
        if g.tastiera_aperta():
            k = g.comando_tastiera()
            if k:
                g.tocco_vero_in(k[0], k[1])
                g.aspetta_tastiera(False)
    return giudica_tastiera(prima, aperta, scritto, chiusa)


def vetro(mp, x, y):
    return mp.vetro(x, y)


def fa_gesto(nome, s, sc, mp, geo, guasto, note):
    g = s.g
    if sc.comanda("reset") is None:
        return S.BLOCKED, "the scene did not answer the reset"
    R = sc.rett
    W, H = R["W"], R["H"]
    fuori = vetro(mp, W * 0.33, H * 0.12)        # between the pad and the button: outside everything
    if nome == "dito-muove":
        esiti = []
        for fx, fy in PUNTI_DITO:
            atteso = (fx, fy)
            tx, ty = fuori if guasto else vetro(mp, *F4.nel_rett(R["pad"], fx, fy))
            st = None
            for _i in range(DITI_VERI_MAX):
                p = g.puntatore_vetro(geo)
                if p is None:
                    return S.BLOCKED, "the page does not say where the pointer is (REMOTIX.tocco)"
                if max(abs(tx - p[0]), abs(ty - p[1])) <= 2:
                    break
                t = g.scorri_vero(geo, tx - p[0], ty - p[1])
                if not t:
                    return S.BLOCKED, ("the real finger did not reach the page (adb swipe "
                                       "from %s by (%.0f,%.0f) px of the glass; touches seen %d)"
                                       % (getattr(g, "ultimo_dito", None), tx - p[0], ty - p[1],
                                          len(g.tocchi_visti())))
                note.append("finger on «%s» at (%.0f,%.0f)" % (t.get("su"), t["x"], t["y"]))
            st = sc.aspetta(lambda q, a=atteso: F4.giudica_movimento(q, a)[0] == S.PASS,
                            F4.ATTESA_S)
            esiti.append(F4.giudica_movimento(st, atteso))
            if esiti[-1][0] != S.PASS:
                break
        brutti = [e for e in esiti if e[0] != S.PASS]
        return brutti[0] if brutti else (S.PASS, "two points: " + " · ".join(e[1] for e in esiti))
    if nome == "tocco-clic":
        tx, ty = fuori if guasto else vetro(mp, *F4.centro_r(R["bot"]))
        err = g.porta_il_puntatore(geo, tx, ty)
        if err is None or err > 3:
            return S.BLOCKED, "the pointer cannot be brought onto the target (error %s px)" % err
        t = g.tap_vero(geo)
        if not t:
            return S.BLOCKED, "the real tap did not reach the page (adb tap)"
        note.append("tap on «%s» at (%.0f,%.0f)" % (t.get("su"), t["x"], t["y"]))
        st = sc.aspetta(lambda q: F4.giudica_clic(q)[0] == S.PASS, F4.ATTESA_S)
        return F4.giudica_clic(st)
    if nome == "tocco-e-mezzo":
        x0, y0 = F4.centro_r(R["box"])
        x1 = x0 + F4.SPINTA * W
        a0, b0 = vetro(mp, x0, y0)
        a1, _b1 = vetro(mp, x1, y0)
        err = g.porta_il_puntatore(geo, a0, b0)
        if err is None or err > 3:
            return S.BLOCKED, "the pointer cannot be brought onto the box (error %s px)" % err
        d = a1 - a0
        cx, cy = g._centro_tela(geo)
        fx, fy = cx - d / 2.0, cy                 # the finger: both ends inside the canvas
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
    if nome == "tastiera":
        return tastiera(s, sc, mp, geo, guasto, note)
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
            e, m = S.BLOCKED, "the bench fell over in the gesture: %s" % str(x)[:160]
        if e == S.FAIL and not guasto:
            print("   ⚠ %s red (%s): redoing it to confirm" % (nome, m), flush=True)
            try:
                e2, m2 = fa_gesto(nome, s, sc, mp, geo, guasto, note)
            except Exception as x:               # noqa: BLE001
                e2, m2 = S.BLOCKED, "the bench fell over in the gesture: %s" % str(x)[:160]
            m = ("⚠ RED at the first attempt (%s), green at the second: %s" % (m, m2)
                 if e2 == S.PASS else "red twice: %s · %s" % (m, m2))
            e = e2
        if note:
            m += " [%s]" % "; ".join(note[-3:])
        print("   %s %-14s %s" % ({S.PASS: "⭐", S.FAIL: "⛔", S.BLOCKED: "⚠"}[e], nome, m),
              flush=True)
        righe.append((nome, e, m))
    return righe


def corpo(o, E):
    if o.browser != "telefono":
        raise S.Bloccata("F-031 is the REAL phone's touch: --browser telefono")
    porta_scena = o.porte_base + 5
    with S.Sessione(o, "031", E) as s:
        sc, mp, geo, dove = G2.prepara(s, porta_scena)
        ev = [dove] if dove else []
        tar = s.g.taratura(geo)
        if not tar:
            raise S.Bloccata("the real calibration finger did not reach the page (adb swipe)")
        disp = s.g.disposizione()
        print("   calibration: %s · layout «%s»" % (tar, disp), flush=True)
        if disp != "tocco":
            perche = s.g.js("return REMOTIX.tocco.perche ? REMOTIX.tocco.perche() : null")
            E.metti("F-031", S.FAIL, "after a real finger the page is NOT in touch mode: «%s» "
                    "(%s)" % (disp, perche), atteso="touch mode (SPECIFICHE §7.2)",
                    osservato=str(perche), evidenze=ev)
            return
        geo = s.geometria() or geo
        atteso = ("the finger takes the pointer onto the BLUE where it points; the tap clicks the GREEN; "
                  "the tap-and-a-half drags the YELLOW box; the on-screen keyboard closed after the "
                  "gestures, the ⌨ opens it, «%s» arrives in the remote field, the ⌨ closes it again" % PAROLA)
        righe = passata(s, sc, mp, geo, False)
        _p, fin = G2.foto(s, "fine-sana")
        if fin:
            ev.append(fin)
        oss = " · ".join("%s: %s %s" % r for r in righe)
        es = [r[1] for r in righe]
        if S.FAIL in es:
            E.metti("F-031", S.FAIL, "red gestures: " + ", ".join(n for n, e, _m in righe
                                                                   if e == S.FAIL),
                    atteso=atteso, osservato=oss, evidenze=ev + [s.salva_console()])
        elif S.BLOCKED in es:
            E.metti("F-031", S.BLOCKED, "gestures not looked at: " + ", ".join(
                "%s (%s)" % (n, m) for n, e, m in righe if e == S.BLOCKED),
                atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-031", S.PASS, "four gestures out of four: the effect is there "
                    "in the application, and the keyboard opens only on request",
                    atteso=atteso, osservato=oss, evidenze=ev)
        if o.guasto:
            righe = passata(s, sc, mp, geo, True)
            visto = F4.esito_col_guasto([r[1] for r in righe])
            E.guasto("F-031", visto,
                     {True: "every gesture in the void gave red",
                      False: "gestures in the void GREEN anyway: " + ", ".join(
                          n for n, e, _m in righe if e == S.PASS),
                      None: "a gesture in the void could not be looked at"}[visto],
                     atteso="every gesture in the void ⇒ red",
                     osservato=" · ".join("%s: %s %s" % r for r in righe))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
