#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f025 — F-025 THE SAME USER FROM TWO BROWSERS: the refusal, the ghost, the eviction

    python3 15-f025-stesso-utente-due-schede.py --scatola gnome --browser chrome --porte-base 4900 [--guasto]

Normal server of the box (85xx): no wrong password.  Two REAL browsers
of the same type, two profiles, two 4K windows (A on porte-base, B on
porte-base+50), the same tenant `c15025u<n>`.

THE REAL EXPECTATION, from the code (src/rcp.c `tratta_attacca`, `sfratta_il_fantasma`,
`torna_a_parlare`, `SFRATTO_PREDEFINITO` = 15 000 ms) and from SPECIFICHE §5.1:
  1  A is in and ALIVE (the pointer moves) ⇒ B, with RIGHT user and
     password, is REFUSED: B's page says «this session's slot shows
     as taken by another client…» (MOTIVO 0x0F GIA_ATTIVA_REMOTA), the
     server writes «slot DENIED to <who>», and A stays in: its canvas still
     shows the scene (photo) and its page has not been sent away.
  2  A becomes a GHOST: its browser stops (SIGSTOP to the whole tree of
     processes — attached, but it no longer sends a packet).
     2a at once (A mute for ~2 s, below the threshold) ⇒ B still REFUSED with 0x0F;
     2b after 17 s of silence (beyond the 15 s of the eviction, before the 30 of
        silence) ⇒ B GETS IN: the page says «Admitted», the server writes
        «EVICTION for silence», and B FINDS A'S SESSION AGAIN: its canvas shows
        the scene of known colour that A had started (photo) — not a
        new desktop.
  3  A wakes up (SIGCONT) ⇒ there are NOT two clients attached: A's page
     says the farewell («taken by another client», 0x0F — «this time it is
     true») or at least is no longer in session; the server writes «speaks again
     after the silence, but their slot belongs to another client».

FAULTS (after the healthy pass, same session, with roles reversed: B is in):
  1  the premise «the other is alive» is FALSE: B says farewell (about:blank)
     before A knocks ⇒ A gets in ⇒ the judge of point 1 must say red.
  2  the ghost is not there: A is in, it is stopped and woken up at once, and
     its pointer keeps moving for 17 s ⇒ B knocks ⇒ the judge of
     point 2b («gets in after the silence») must say red.
"""
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._carica("g8", os.path.join(S.QUI, "15-g8-comune.py"))
FUNZIONI = ("F-025",)
CIANO = (0, 200, 200)
COLORI = {"scena": CIANO}
SOGLIA_SCENA = 0.5
SFRATTO_S = 15
DOPO_S = 17
RISVEGLIO_S = 60     # how long to wait for A, woken up, to know it is no longer in


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def giudica_rifiutato(ammesso, esito, righe, chi, pagina_a, fr_a):
    """Point 1 / 2a: B refused with the clear reason, A still in."""
    if ammesso is True:
        return S.FAIL, "B GOT IN while A was alive (expected 0x0F): «%s»" % esito
    if ammesso is None:
        return S.BLOCKED, "no verdict in B's page: «%s»" % esito
    if G.FRASE[0x0F] not in (esito or ""):
        return S.FAIL, "B refused but not with reason 0x0F: «%s»" % esito
    if not any("slot DENIED to %s" % chi in r for r in righe):
        return S.FAIL, "the page says 0x0F but the server does not write «slot DENIED»"
    if pagina_a is not None and (pagina_a.get("classe") == "male" or not pagina_a.get("sessione")):
        return S.FAIL, "B's refusal threw A out: «%s»" % pagina_a.get("esito")
    if fr_a is not None and fr_a.get("scena", 0) < SOGLIA_SCENA:
        return S.FAIL, "A is still in session but its canvas does not show the scene (%.1f%%)" % (
            100 * fr_a.get("scena", 0))
    return S.PASS, "B refused: «%s»; A stays in" % (esito or "")[:70]


def giudica_sfratto(ammesso, esito, righe, chi, fr_b):
    """Point 2b: after the silence B gets in and finds A's session again."""
    if ammesso is not True:
        return S.FAIL, "A has been silent for %d s and B does NOT get in: «%s»" % (DOPO_S, esito)
    sfratto = any("EVICTION for silence" in r for r in righe)
    lasciato = any("slot LEFT" in r for r in righe)
    if not (sfratto or lasciato):
        return S.FAIL, ("B got in but the server does not say how the ghost's slot was "
                        "freed (neither «EVICTION for silence» nor «slot LEFT»)")
    come = ("EVICTION for silence" if sfratto else
            "slot LEFT by the ghost earlier (the dead line closed its wire)")
    if fr_b is None:
        return S.BLOCKED, "B got in but its canvas cannot be photographed"
    if fr_b.get("scena", 0) < SOGLIA_SCENA:
        return S.FAIL, ("B got in but does NOT find A's session again: the scene covers %.1f%% "
                        "of the canvas" % (100 * fr_b.get("scena", 0)))
    return S.PASS, "after %d s of A's silence, B gets in (%s) and finds the scene again (%.0f%%)" % (
        DOPO_S, come, 100 * fr_b["scena"])


def giudica_risveglio(pagina_a, righe, chi):
    """Point 3: A woken up must NOT make the user believe it is still
    in: the page says a farewell (outcome «male») or puts the form back."""
    if pagina_a.get("errore") or pagina_a.get("classe") is None:
        return S.BLOCKED, "A's page cannot be read after the wake-up: %s" % (
            pagina_a.get("errore") or pagina_a)
    if pagina_a.get("classe") == "male":
        return S.PASS, "A woken up: the page says «%s»" % (pagina_a.get("esito") or "")[:90]
    if pagina_a.get("modulo"):
        return S.PASS, "A woken up: the page puts the sign-in form back"
    return S.FAIL, ("A woken up: its wire is already closed by the server, but the page still says "
                    "«%s» (sessione=%s, form hidden) — the user sees a frozen desktop and "
                    "no warning" % (pagina_a.get("esito"), pagina_a.get("sessione")))


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    ch = "c15025u1"
    f0f = "this session's slot shows as " + G.FRASE[0x0F]
    neg = ["slot DENIED to %s from [192.168.0.2]:1" % ch]
    pa = {"classe": "bene", "sessione": True, "esito": "Admitted"}
    prova("0x0F refusal, A in ⇒ PASS",
          giudica_rifiutato(False, f0f, neg, ch, pa, {"scena": 0.9})[0] == S.PASS)
    prova("B admitted ⇒ FAIL", giudica_rifiutato(True, "Admitted", [], ch, pa, None)[0] == S.FAIL)
    prova("different reason ⇒ FAIL",
          giudica_rifiutato(False, "user or password", neg, ch, pa, None)[0] == S.FAIL)
    prova("A thrown out ⇒ FAIL", giudica_rifiutato(
        False, f0f, neg, ch, {"classe": "male", "sessione": False, "esito": "x"}, None)[0] == S.FAIL)
    prova("eviction with the scene ⇒ PASS", giudica_sfratto(
        True, "Admitted", ["⭐ EVICTION for silence: 17000 ms"], ch, {"scena": 0.8})[0] == S.PASS)
    prova("eviction without the scene ⇒ FAIL", giudica_sfratto(
        True, "Admitted", ["⭐ EVICTION for silence"], ch, {"scena": 0.0})[0] == S.FAIL)
    prova("no eviction ⇒ FAIL", giudica_sfratto(False, f0f, [], ch, None)[0] == S.FAIL)
    prova("wake-up in session ⇒ FAIL",
          giudica_risveglio({"classe": "bene", "sessione": True, "modulo": False}, [], ch)[0] == S.FAIL)
    prova("wake-up with the form ⇒ PASS",
          giudica_risveglio({"classe": "bene", "sessione": False, "modulo": True}, [], ch)[0] == S.PASS)
    prova("wake-up sent away ⇒ PASS",
          giudica_risveglio({"classe": "male", "sessione": False, "esito": f0f}, [], ch)[0] == S.PASS)
    from PIL import Image
    import io
    im = Image.new("RGB", (40, 20), (20, 20, 20))
    im.paste(CIANO, (0, 0, 30, 20))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    fr = G.frazioni(buf.getvalue(), COLORI, riduci=1)
    prova("fractions: 75%% cyan (%s)" % G.fr_testo(fr), fr and abs(fr["scena"] - 0.75) < 0.01)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def aspetta_pagina(g, tetto=25):
    fine = time.time() + tetto
    p = {}
    while time.time() < fine:
        p = G.leggi_pagina(g)
        if p.get("classe") == "male":
            return p
        time.sleep(1)
    return p


def corpo(o, E):
    sc = None
    with S.Sessione(o, "025", E) as A:
        chi = A.chi
        sc = A.sc
        ok, m = A.entra()
        if not ok:
            raise S.Bloccata("A does not get in: " + m)
        print("   ⭐ A in: %s" % m[:90], flush=True)
        S.C21.sveglia(A.g, A.geometria())
        ok, t = G.accendi_scena(sc, chi, o.porte_base + G.SPOSTA_SCENA, CIANO)
        if not ok:
            raise S.Bloccata("the colour scene does not start: %s" % " | ".join(t.splitlines()[-14:])[-900:])
        fr_a, foto_a, perche = G.aspetta_colore(A, "A-scena", COLORI, "scena", SOGLIA_SCENA)
        if not fr_a or fr_a["scena"] < SOGLIA_SCENA:
            raise S.Bloccata("the scene does not cover A's canvas: %s %s" % (G.fr_testo(fr_a), perche))
        print("   scene in A: %s" % G.fr_testo(fr_a), flush=True)

        with S.Sessione(G.o_per(o, 1), "025", E, inquilino=False, chi=chi,
                        parola=A.parola) as B:
            ev = [foto_a]
            # ── 1: A alive ⇒ B refused ──────────────────────────────────────
            segno = A.segno_registro()
            G.muovi_un_po(A)
            amm, st, amb = G.tenta_tenace(B, chi, B.parola)
            righe = A.registro_da(segno)
            pa = G.leggi_pagina(A.g)
            fr, dove, _ = G.aspetta_colore(A, "A-dopo-rifiuto", COLORI, "scena", SOGLIA_SCENA, 6)
            ev.append(dove)
            e1, r1 = giudica_rifiutato(amm, st.get("esito"), righe, chi, pa, fr)
            if amb:
                r1 += " (retried after %s)" % amb
            print("   1 (A alive): %s — %s" % (e1, r1), flush=True)

            # ── 2: the ghost ────────────────────────────────────────────────
            G.muovi_un_po(A)
            segno_f = A.segno_registro()
            n = G.ferma(A.g)
            t0 = time.time()
            print("   A STOPPED (%d processes)" % n, flush=True)
            e2a = e2b = e3 = S.BLOCKED
            r2a = r2b = r3 = "not looked at"
            try:
                segno = A.segno_registro()
                time.sleep(1.5)
                amm, st, amb = G.tenta_tenace(B, chi, B.parola)
                muto = time.time() - t0
                righe = A.registro_da(segno)
                e2a, r2a = giudica_rifiutato(amm, st.get("esito"), righe, chi, None, None)
                r2a = "(A mute for %.1f s) %s" % (muto, r2a)
                if muto >= SFRATTO_S - 2:
                    e2a, r2a = S.BLOCKED, "attempt 2a arrived late (%.1f s)" % muto
                print("   2a: %s — %s" % (e2a, r2a), flush=True)
                time.sleep(max(0.0, t0 + DOPO_S - time.time()))
                amm, st, amb = G.tenta_tenace(B, chi, B.parola)
                muto = time.time() - t0
                fr_b = None
                if amm:
                    e, m2, s2 = B.pr.primo_fotogramma()
                    fr_b, dove, _ = G.aspetta_colore(B, "B-dopo-sfratto", COLORI, "scena",
                                                     SOGLIA_SCENA, 20)
                    ev.append(dove)
                righe = A.registro_da(segno_f)
                e2b, r2b = giudica_sfratto(amm, st.get("esito"), righe, chi, fr_b)
                r2b = "(A mute for %.1f s) %s · B's page says «%s»%s" % (
                    muto, r2b, (st.get("esito") or "")[:60],
                    " (retried after %s)" % amb if amb else "")
                print("   2b: %s — %s" % (e2b, r2b), flush=True)
            finally:
                G.riprendi(A.g)
            # ── 3: the wake-up ──────────────────────────────────────────────
            t_sv = time.time()
            G.muovi_un_po(A)
            pa = aspetta_pagina(A.g, RISVEGLIO_S)
            dopo_sv = time.time() - t_sv
            righe = A.registro_da(segno_f)
            e3, r3 = giudica_risveglio(pa, righe, chi)
            reg_a = [x for x in (A.stato().get("registro") or "").splitlines() if x.strip()][-6:]
            detto = [r for r in righe if "speaks again after the silence" in r]
            r3 += " · server: %s" % ("«speaks again… their slot belongs to another»" if detto
                                     else "(no «speaks again» line)")
            r3 += " · dead line on A's wire: %s · A's page diary: %s" % (
                "YES" if any("DEAD LINE" in r or "linea-morta" in r for r in righe) else "no",
                " | ".join(reg_a)[-300:])
            r3 = "(after %.0f s) %s" % (dopo_sv, r3)
            print("   3: %s — %s" % (e3, r3), flush=True)

            tutti = [e1, e2a, e2b, e3]
            esito = S.FAIL if S.FAIL in tutti else (S.BLOCKED if S.BLOCKED in tutti else S.PASS)
            ev.append(A.salva_testo("f025-server.txt", righe))
            E.metti("F-025", esito, "1 %s · 2a %s · 2b %s · 3 %s" % (e1, e2a, e2b, e3),
                    atteso="A alive ⇒ B refused with 0x0F and A stays; A mute >15 s ⇒ B gets in "
                           "(eviction) and finds the scene again; A woken up sent away",
                    osservato="1: %s | 2a: %s | 2b: %s | 3: %s" % (r1, r2a, r2b, r3),
                    evidenze=[x for x in ev if x])

            if o.guasto:
                gv = []
                # 1: B (in) says farewell before A knocks
                B.g.vai("about:blank")
                time.sleep(3)
                segno = A.segno_registro()
                amm, st, amb = G.tenta_tenace(A, chi, A.parola)
                righe = A.registro_da(segno)
                eg1, rg1 = giudica_rifiutato(amm, st.get("esito"), righe, chi, None, None)
                gv.append(eg1 == S.FAIL if amm is not None else None)
                print("   fault 1 (the other is NOT alive): the judge says %s — %s" % (eg1, rg1),
                      flush=True)
                # 2: no ghost: A stopped and woken up at once, and alive
                eg2, rg2 = S.BLOCKED, "A did not get back in"
                if amm:
                    A.pr.primo_fotogramma()
                    n = G.ferma(A.g)
                    G.riprendi(A.g)
                    t0 = time.time()
                    B.pr.apri()
                    while time.time() < t0 + DOPO_S:
                        G.muovi_un_po(A, 2)
                        time.sleep(1.5)
                    segno = A.segno_registro()
                    amm2, st2, amb = G.tenta_tenace(B, chi, B.parola)
                    righe = A.registro_da(segno)
                    eg2, rg2 = giudica_sfratto(amm2, st2.get("esito"), righe, chi, None)
                    gv.append(eg2 == S.FAIL if amm2 is not None else None)
                else:
                    gv.append(None)
                print("   fault 2 (A alive, no ghost): the judge says %s — %s" % (eg2, rg2),
                      flush=True)
                visto = None if None in gv else all(gv)
                E.guasto("F-025", visto, "the other sent away ⇒ %s (%s) · A alive for %d s ⇒ %s (%s)"
                         % (eg1, rg1[:80], DOPO_S, eg2, rg2[:80]))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
