#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-n027 — THE NEGATIVE TESTS (fasi/15 §«Negative tests», adapted)

    python3 15-n027-negative.py --scatola lxqt --browser firefox --porte-base 4930 [--guasto]

N-1  nonexistent user .............. lives in 15-f027 (on the G8 server: it counts as an error)
N-2  wrong password ................ is F-027 (15-f027)
N-3  session already closed with «Exit» ⇒ the new login makes a NEW and CLEAN
     session be born.  Normal server (85xx).  The tenant logs in, opens a scene
     of known colour (YELLOW), exits with their desktop's «Exit» gesture (the same as
     C20/C24: the D-Bus method the menu reaches).  Expected: the product says
     the session ended, the page goes back to the form, the session's programs
     are no longer there; coming back in, the server MAKES a session BE BORN («I AM
     MAKING IT BE BORN») and the canvas — real desktop, not degenerate — does NOT show the yellow.
N-4  network not available.  On the G8 server (port 862x): the page is loaded,
     then the server is TURNED OFF, and the user presses «Connect».  Expected: within 40 s
     the page says it cannot connect (outcome «male», a sentence), no
     «Admitted», it does not stay hung.  And the page reloaded with the server off: what
     the browser says (it is recorded; the product's page is not there).  At the
     end the G8 server is started again.
N-5  same user already active from another device ... is F-025 (15-f025).

FAULTS:
  N-3  instead of «Exit», a DETACH (the page goes to about:blank: the wire
       drops, the session stays) and we come back in ⇒ the yellow scene is still there and
       no session is born ⇒ the judge must say red.
  N-4  the server is NOT turned off ⇒ «Admitted» ⇒ the judge must say red.
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._carica("g8", os.path.join(S.QUI, "15-g8-comune.py"))
FUNZIONI = ("N-3", "N-4")
PER_BROWSER = False
SERVER = "15-g8-server.sh"
GIALLO = (220, 200, 30)
COLORI = {"giallo": GIALLO}
NASCITA = "I AM MAKING IT BE BORN"
FINITA = [p for p, _d in S.C20V.C20.RIGHE_FINITA]


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def giudica_rientro(finita, pagina_modulo, processi_dopo, righe_rientro, entrato, fr):
    """N-3: (outcome, reason)."""
    if not finita:
        return S.BLOCKED, "the product did not declare the session ended: «Exit» not observable"
    if not entrato:
        return S.FAIL, "after «Exit» you do not get back in"
    if fr is None:
        return S.BLOCKED, "back in, but the canvas cannot be photographed"
    guai = []
    if not any(NASCITA in r for r in righe_rientro):
        guai.append("at the re-entry the server does NOT make a session be born")
    if fr.get("giallo", 0) > 0.01:
        guai.append("the closed session's scene is still there (yellow %.1f%%)" % (100 * fr["giallo"]))
    if processi_dopo:
        guai.append("after «Exit» %d processes of the scene remain" % processi_dopo)
    if guai:
        return S.FAIL, "; ".join(guai)
    return S.PASS, ("ended, form %s, no program left, at the re-entry session BORN and canvas "
                    "clean (yellow %.2f%%)" % ("visible" if pagina_modulo else "after reload",
                                                100 * fr.get("giallo", 0)))


def giudica_senza_rete(ammesso, stato, attesa_s):
    """N-4: (outcome, reason)."""
    esito = (stato or {}).get("esito") or ""
    if ammesso is True:
        return S.FAIL, "server off and the page says «%s»" % esito
    if (stato or {}).get("esito_classe") == "male" and esito.strip():
        return S.PASS, "in %.0f s the page says «%s»" % (attesa_s, esito[:120])
    return S.FAIL, ("server off: after %.0f s the page stays hung without saying anything clear "
                    "(outcome «%s»)" % (attesa_s, esito[:120]))


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    nata = ["[c] ⭐ no graphical session for «c»: I AM MAKING IT BE BORN (canvas 1x1)"]
    prova("clean re-entry ⇒ PASS", giudica_rientro(True, True, 0, nata, True, {"giallo": 0.0})[0] == S.PASS)
    prova("scene still there ⇒ FAIL", giudica_rientro(True, True, 0, nata, True, {"giallo": 0.8})[0] == S.FAIL)
    prova("no birth ⇒ FAIL", giudica_rientro(True, True, 0, [], True, {"giallo": 0.0})[0] == S.FAIL)
    prova("programs left ⇒ FAIL", giudica_rientro(True, True, 2, nata, True, {"giallo": 0.0})[0] == S.FAIL)
    prova("not ended ⇒ BLOCKED", giudica_rientro(False, True, 0, nata, True, {"giallo": 0.0})[0] == S.BLOCKED)
    prova("without network, sentence ⇒ PASS", giudica_senza_rete(
        False, {"esito_classe": "male", "esito": "the server does not answer"}, 5)[0] == S.PASS)
    prova("without network, admitted ⇒ FAIL", giudica_senza_rete(True, {"esito": "Admitted"}, 5)[0] == S.FAIL)
    prova("without network, hung ⇒ FAIL", giudica_senza_rete(
        None, {"esito_classe": "", "esito": "Connecting…"}, 40)[0] == S.FAIL)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def processi_scena(sc, chi):
    # ⚠ only the session's APPLICATION: the scene's server was
    #   launched by the bench outside the session (runuser), and «Exit» does not see it
    c, t = G.dentro(sc, "pgrep -u %s -x firefox-esr 2>/dev/null | wc -l; true" % chi, 30)
    try:
        return int(t.split()[-1])
    except (ValueError, IndexError):
        return None


def scena_gialla(o, s):
    S.C21.sveglia(s.g, s.geometria())
    ok, t = G.accendi_scena(s.sc, s.chi, o.porte_base + G.SPOSTA_SCENA, GIALLO)
    if not ok:
        return None, "the yellow scene does not start: %s" % " | ".join(t.splitlines()[-5:])[-300:]
    fr, dove, perche = G.aspetta_colore(s, "scena-gialla", COLORI, "giallo", 0.5, 40)
    if not fr or fr["giallo"] < 0.5:
        return None, "the yellow scene does not cover the canvas: %s %s" % (G.fr_testo(fr), perche)
    return fr, dove


def rientra_e_guarda(s, segno, pausa=8):
    """Comes back in (from the form if it is there, otherwise by reloading) and photographs after `pausa` s.
    Returns (got in, fractions, server lines from the mark, photo)."""
    p = G.leggi_pagina(s.g)
    if p.get("modulo"):
        e, m, st = s.pr.entra(s.parola)
        ok = e == S.VERDE
        if ok:
            e, m, st = s.pr.primo_fotogramma()
            e, m = S.C20V.desktop_scuro_ma_vivo(e, m, st)
            ok = e == S.VERDE
    else:
        ok, m = s.entra()
    if not ok:
        return False, None, s.registro_da(segno), m
    time.sleep(pausa)
    png, dove = s.foto("rientro")
    fr = G.frazioni(png, COLORI) if png else None
    return True, fr, s.registro_da(segno), dove


def n3(o, E):
    with S.Sessione(o, "027", E) as s:
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata("the tenant does not get in: " + m)
        fr, dove = scena_gialla(o, s)
        if fr is None:
            raise S.Bloccata(dove)
        ev = [dove]
        desk, gesto = s.sc.gesto_esci()
        if not gesto:
            raise S.Bloccata("I do not know how to say «Exit» in this box")
        segno = s.segno_registro()
        c, t = s.come_utente(gesto)
        forma, _r = S.C20V.aspetta_riga(s.sc, segno, s.chi, FINITA, 60)
        modulo = False
        fine = time.time() + 30
        while time.time() < fine:
            if G.leggi_pagina(s.g).get("modulo"):
                modulo = True
                break
            time.sleep(1)
        pag = G.leggi_pagina(s.g)
        proc = None
        fine = time.time() + 20
        while time.time() < fine:
            proc = processi_scena(s.sc, s.chi)
            if proc == 0:
                break
            time.sleep(2)
        segno2 = s.segno_registro()
        entrato, fr2, righe, dove2 = rientra_e_guarda(s, segno2)
        ev.append(dove2 if entrato else "")
        e, r = giudica_rientro(bool(forma), modulo, proc, righe, entrato, fr2)
        ev.append(s.salva_testo("n3-server.txt", s.registro_da(segno)))
        E.metti("N-3", e, r, atteso="«Exit» (%s) ⇒ session ended, form, no program; at the "
                "re-entry a NEW and clean session" % desk,
                osservato="%s · the product: «%s» · the page after «Exit»: «%s»" % (
                    r, forma, (pag.get("esito") or "")[:80]), evidenze=[x for x in ev if x])

        if o.guasto:
            fr, dove = scena_gialla(o, s)
            if fr is None:
                E.guasto("N-3", None, "the yellow scene does not start again: " + dove)
                return
            s.g.vai("about:blank")                     # ⛔ the fault: detach, not «Exit»
            time.sleep(4)
            segno3 = s.segno_registro()
            entrato, fr3, righe, _d = rientra_e_guarda(s, segno3)
            eg, rg = giudica_rientro(True, True, 0, righe, entrato, fr3)
            E.guasto("N-3", eg == S.FAIL if eg != S.BLOCKED else None,
                     "detach instead of «Exit» ⇒ the judge says %s: %s" % (eg, rg))


def n4(o, E):
    srv = G.MioServer(o.scatola)
    if not srv.acceso():
        ok, t = srv.accendi()
        if not ok:
            E.metti("N-4", S.BLOCKED, "the G8 server does not start: " + t)
            return
    o4 = G.o_per(o, 1)
    o4.porta = srv.porta
    o4.url = "https://%s:%d/" % (o.host, srv.porta)
    srv.sblocca()
    try:
        with S.Sessione(o4, "027", E) as s:
            ok, m = s.pr.apri()
            if not ok:
                E.metti("N-4", S.BLOCKED, "the G8 server's page does not open: " + m)
                return
            spento, t = srv.spegni()
            time.sleep(1)
            t0 = time.time()
            amm, st = G.tenta_senza_ricarica(s, s.chi, s.parola, 40)
            attesa = time.time() - t0
            e, r = giudica_senza_rete(amm, st, attesa)
            ricaricata = G.carica(s.g, o4.url, 30)
            browser_dice = " ".join((ricaricata.get("testo") or ricaricata.get("errore")
                                     or ricaricata.get("non_aperta") or "").split())[:160]
            ev = [s.salva_testo("n4-pagina.txt", [str(st.get("registro") or "")[-3000:],
                                                  "---", str(ricaricata)])]
            E.metti("N-4", e, r, atteso="server off ⇒ within 40 s a clear sentence, no "
                    "«Admitted», the page does not stay hung",
                    osservato="%s · reloaded with the server off the browser says: «%s» (%s)" % (
                        r, browser_dice, t.splitlines()[-1] if t else "?"), evidenze=ev)
            ok, t = srv.accendi()
            if o.guasto:
                if not ok:
                    E.guasto("N-4", None, "the G8 server does not start again: " + t)
                else:
                    t0 = time.time()
                    amm, st = G.tenta(s, s.chi, s.parola, 40)
                    eg, rg = giudica_senza_rete(amm, st, time.time() - t0)
                    E.guasto("N-4", eg == S.FAIL if amm is not None else None,
                             "server on instead of off ⇒ the judge says %s: %s" % (eg, rg))
    finally:
        if not srv.acceso():
            print("   G8 server restarted: %s" % (srv.accendi(),), flush=True)


def corpo(o, E):
    try:
        n3(o, E)
    except S.Bloccata as b:
        E.bloccate(["N-3"], str(b))
        if o.guasto:
            E.bloccate(["N-3"], str(b), passata="guasto")
    n4(o, E)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
