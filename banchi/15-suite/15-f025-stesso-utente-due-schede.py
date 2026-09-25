#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f025 — F-025 LO STESSO UTENTE DA DUE BROWSER: il rifiuto, il fantasma, lo sfratto

    python3 15-f025-stesso-utente-due-schede.py --scatola gnome --browser chrome --porte-base 4900 [--guasto]

Server normale della scatola (85xx): nessuna parola sbagliata.  Due browser
VERI dello stesso tipo, due profili, due finestre 4K (A su porte-base, B su
porte-base+50), lo stesso inquilino `c15025u<n>`.

L'ATTESO VERO, dal codice (src/rcp.c `tratta_attacca`, `sfratta_il_fantasma`,
`torna_a_parlare`, `SFRATTO_PREDEFINITO` = 15 000 ms) e da SPECIFICHE §5.1:
  1  A e' dentro e VIVO (il puntatore si muove) ⇒ B, con utente e parola
     GIUSTI, e' RIFIUTATO: la pagina di B dice «il posto di questa sessione
     risulta occupato da un altro client…» (MOTIVO 0x0F GIA_ATTIVA_REMOTA), il
     server scrive «posto NEGATO a <chi>», e A resta dentro: la sua tela mostra
     ancora la scena (fotografia) e la sua pagina non e' congedata.
  2  A diventa un FANTASMA: il suo browser si ferma (SIGSTOP a tutto l'albero dei
     processi — attaccato, ma non manda piu' un pacchetto).
     2a subito (A muto da ~2 s, sotto la soglia) ⇒ B ancora RIFIUTATO con 0x0F;
     2b dopo 17 s di silenzio (oltre i 15 s dello sfratto, prima dei 30 del
        silenzio) ⇒ B ENTRA: la pagina dice «Ammesso», il server scrive
        «SFRATTO per silenzio», e B RITROVA LA SESSIONE DI A: la sua tela mostra
        la scena di colore noto che A aveva acceso (fotografia) — non un
        desktop nuovo.
  3  A si risveglia (SIGCONT) ⇒ NON ci sono due client attaccati: la pagina di
     A dice il congedo («occupato da un altro client», 0x0F — «questa volta e'
     vero») o almeno non e' piu' in sessione; il server scrive «torna a parlare
     dopo il silenzio, ma il suo posto e' di un altro client».

GUASTI (dopo la passata sana, stessa sessione, a parti invertite: B e' dentro):
  1  il presupposto «l'altro e' vivo» e' FALSO: B si congeda (about:blank)
     prima che A bussi ⇒ A entra ⇒ il giudice del punto 1 deve dire rosso.
  2  il fantasma non c'e': A e' dentro, lo si ferma e lo si risveglia subito, e
     il suo puntatore continua a muoversi per 17 s ⇒ B bussa ⇒ il giudice del
     punto 2b («entra dopo il silenzio») deve dire rosso.
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
RISVEGLIO_S = 60     # quanto si aspetta che A, risvegliato, sappia di non essere piu' dentro


# ═══════════════════════════════════════════════════════════════════════════
#  I GIUDICI — puri
# ═══════════════════════════════════════════════════════════════════════════
def giudica_rifiutato(ammesso, esito, righe, chi, pagina_a, fr_a):
    """Punto 1 / 2a: B rifiutato col motivo chiaro, A ancora dentro."""
    if ammesso is True:
        return S.FAIL, "B e' ENTRATO mentre A era vivo (atteso 0x0F): «%s»" % esito
    if ammesso is None:
        return S.BLOCKED, "nessun verdetto nella pagina di B: «%s»" % esito
    if G.FRASE[0x0F] not in (esito or ""):
        return S.FAIL, "B rifiutato ma non col motivo 0x0F: «%s»" % esito
    if not any("posto NEGATO a %s" % chi in r for r in righe):
        return S.FAIL, "la pagina dice 0x0F ma il server non scrive «posto NEGATO»"
    if pagina_a is not None and (pagina_a.get("classe") == "male" or not pagina_a.get("sessione")):
        return S.FAIL, "il rifiuto di B ha buttato fuori A: «%s»" % pagina_a.get("esito")
    if fr_a is not None and fr_a.get("scena", 0) < SOGLIA_SCENA:
        return S.FAIL, "A e' ancora in sessione ma la sua tela non mostra la scena (%.1f%%)" % (
            100 * fr_a.get("scena", 0))
    return S.PASS, "B rifiutato: «%s»; A resta dentro" % (esito or "")[:70]


def giudica_sfratto(ammesso, esito, righe, chi, fr_b):
    """Punto 2b: dopo il silenzio B entra e ritrova la sessione di A."""
    if ammesso is not True:
        return S.FAIL, "A tace da %d s e B NON entra: «%s»" % (DOPO_S, esito)
    sfratto = any("SFRATTO per silenzio" in r for r in righe)
    lasciato = any("posto LASCIATO" in r for r in righe)
    if not (sfratto or lasciato):
        return S.FAIL, ("B e' entrato ma il server non dice come si e' liberato il posto del "
                        "fantasma (ne' «SFRATTO per silenzio» ne' «posto LASCIATO»)")
    come = ("SFRATTO per silenzio" if sfratto else
            "posto LASCIATO dal fantasma prima (la linea morta ha chiuso il suo filo)")
    if fr_b is None:
        return S.BLOCKED, "B e' entrato ma la sua tela non si fotografa"
    if fr_b.get("scena", 0) < SOGLIA_SCENA:
        return S.FAIL, ("B e' entrato ma NON ritrova la sessione di A: la scena copre il %.1f%% "
                        "della tela" % (100 * fr_b.get("scena", 0)))
    return S.PASS, "dopo %d s di silenzio di A, B entra (%s) e ritrova la scena (%.0f%%)" % (
        DOPO_S, come, 100 * fr_b["scena"])


def giudica_risveglio(pagina_a, righe, chi):
    """Punto 3: A risvegliato NON deve far credere all'utente di essere ancora
    dentro: la pagina dice un congedo (esito «male») o rimette il modulo."""
    if pagina_a.get("errore") or pagina_a.get("classe") is None:
        return S.BLOCKED, "la pagina di A non si legge dopo il risveglio: %s" % (
            pagina_a.get("errore") or pagina_a)
    if pagina_a.get("classe") == "male":
        return S.PASS, "A risvegliato: la pagina dice «%s»" % (pagina_a.get("esito") or "")[:90]
    if pagina_a.get("modulo"):
        return S.PASS, "A risvegliato: la pagina rimette il modulo d'accesso"
    return S.FAIL, ("A risvegliato: il suo filo e' gia' chiuso dal server, ma la pagina dice ancora "
                    "«%s» (sessione=%s, modulo nascosto) — l'utente vede un desktop fermo e "
                    "nessun avviso" % (pagina_a.get("esito"), pagina_a.get("sessione")))


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    ch = "c15025u1"
    f0f = "il posto di questa sessione risulta " + G.FRASE[0x0F]
    neg = ["posto NEGATO a %s da [192.168.0.2]:1" % ch]
    pa = {"classe": "bene", "sessione": True, "esito": "Ammesso"}
    prova("rifiuto 0x0F, A dentro ⇒ PASS",
          giudica_rifiutato(False, f0f, neg, ch, pa, {"scena": 0.9})[0] == S.PASS)
    prova("B ammesso ⇒ FAIL", giudica_rifiutato(True, "Ammesso", [], ch, pa, None)[0] == S.FAIL)
    prova("motivo diverso ⇒ FAIL",
          giudica_rifiutato(False, "utente o parola", neg, ch, pa, None)[0] == S.FAIL)
    prova("A buttato fuori ⇒ FAIL", giudica_rifiutato(
        False, f0f, neg, ch, {"classe": "male", "sessione": False, "esito": "x"}, None)[0] == S.FAIL)
    prova("sfratto con la scena ⇒ PASS", giudica_sfratto(
        True, "Ammesso", ["⭐ SFRATTO per silenzio: 17000 ms"], ch, {"scena": 0.8})[0] == S.PASS)
    prova("sfratto senza la scena ⇒ FAIL", giudica_sfratto(
        True, "Ammesso", ["⭐ SFRATTO per silenzio"], ch, {"scena": 0.0})[0] == S.FAIL)
    prova("nessuno sfratto ⇒ FAIL", giudica_sfratto(False, f0f, [], ch, None)[0] == S.FAIL)
    prova("risveglio in sessione ⇒ FAIL",
          giudica_risveglio({"classe": "bene", "sessione": True, "modulo": False}, [], ch)[0] == S.FAIL)
    prova("risveglio col modulo ⇒ PASS",
          giudica_risveglio({"classe": "bene", "sessione": False, "modulo": True}, [], ch)[0] == S.PASS)
    prova("risveglio congedato ⇒ PASS",
          giudica_risveglio({"classe": "male", "sessione": False, "esito": f0f}, [], ch)[0] == S.PASS)
    from PIL import Image
    import io
    im = Image.new("RGB", (40, 20), (20, 20, 20))
    im.paste(CIANO, (0, 0, 30, 20))
    buf = io.BytesIO()
    im.save(buf, "PNG")
    fr = G.frazioni(buf.getvalue(), COLORI, riduci=1)
    prova("frazioni: 75%% ciano (%s)" % G.fr_testo(fr), fr and abs(fr["scena"] - 0.75) < 0.01)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
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
            raise S.Bloccata("A non entra: " + m)
        print("   ⭐ A dentro: %s" % m[:90], flush=True)
        S.C21.sveglia(A.g, A.geometria())
        ok, t = G.accendi_scena(sc, chi, o.porte_base + G.SPOSTA_SCENA, CIANO)
        if not ok:
            raise S.Bloccata("la scena di colore non si accende: %s" % " | ".join(t.splitlines()[-14:])[-900:])
        fr_a, foto_a, perche = G.aspetta_colore(A, "A-scena", COLORI, "scena", SOGLIA_SCENA)
        if not fr_a or fr_a["scena"] < SOGLIA_SCENA:
            raise S.Bloccata("la scena non copre la tela di A: %s %s" % (G.fr_testo(fr_a), perche))
        print("   scena in A: %s" % G.fr_testo(fr_a), flush=True)

        with S.Sessione(G.o_per(o, 1), "025", E, inquilino=False, chi=chi,
                        parola=A.parola) as B:
            ev = [foto_a]
            # ── 1: A vivo ⇒ B rifiutato ─────────────────────────────────────
            segno = A.segno_registro()
            G.muovi_un_po(A)
            amm, st, amb = G.tenta_tenace(B, chi, B.parola)
            righe = A.registro_da(segno)
            pa = G.leggi_pagina(A.g)
            fr, dove, _ = G.aspetta_colore(A, "A-dopo-rifiuto", COLORI, "scena", SOGLIA_SCENA, 6)
            ev.append(dove)
            e1, r1 = giudica_rifiutato(amm, st.get("esito"), righe, chi, pa, fr)
            if amb:
                r1 += " (riprovato dopo %s)" % amb
            print("   1 (A vivo): %s — %s" % (e1, r1), flush=True)

            # ── 2: il fantasma ──────────────────────────────────────────────
            G.muovi_un_po(A)
            segno_f = A.segno_registro()
            n = G.ferma(A.g)
            t0 = time.time()
            print("   A FERMATO (%d processi)" % n, flush=True)
            e2a = e2b = e3 = S.BLOCKED
            r2a = r2b = r3 = "non guardato"
            try:
                segno = A.segno_registro()
                time.sleep(1.5)
                amm, st, amb = G.tenta_tenace(B, chi, B.parola)
                muto = time.time() - t0
                righe = A.registro_da(segno)
                e2a, r2a = giudica_rifiutato(amm, st.get("esito"), righe, chi, None, None)
                r2a = "(A muto da %.1f s) %s" % (muto, r2a)
                if muto >= SFRATTO_S - 2:
                    e2a, r2a = S.BLOCKED, "il tentativo 2a e' arrivato tardi (%.1f s)" % muto
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
                r2b = "(A muto da %.1f s) %s · la pagina di B dice «%s»%s" % (
                    muto, r2b, (st.get("esito") or "")[:60],
                    " (riprovato dopo %s)" % amb if amb else "")
                print("   2b: %s — %s" % (e2b, r2b), flush=True)
            finally:
                G.riprendi(A.g)
            # ── 3: il risveglio ─────────────────────────────────────────────
            t_sv = time.time()
            G.muovi_un_po(A)
            pa = aspetta_pagina(A.g, RISVEGLIO_S)
            dopo_sv = time.time() - t_sv
            righe = A.registro_da(segno_f)
            e3, r3 = giudica_risveglio(pa, righe, chi)
            reg_a = [x for x in (A.stato().get("registro") or "").splitlines() if x.strip()][-6:]
            detto = [r for r in righe if "torna a parlare dopo il silenzio" in r]
            r3 += " · server: %s" % ("«torna a parlare… il suo posto e' di un altro»" if detto
                                     else "(nessuna riga «torna a parlare»)")
            r3 += " · linea morta sul filo di A: %s · diario della pagina di A: %s" % (
                "SI'" if any("LINEA MORTA" in r or "linea-morta" in r for r in righe) else "no",
                " | ".join(reg_a)[-300:])
            r3 = "(dopo %.0f s) %s" % (dopo_sv, r3)
            print("   3: %s — %s" % (e3, r3), flush=True)

            tutti = [e1, e2a, e2b, e3]
            esito = S.FAIL if S.FAIL in tutti else (S.BLOCKED if S.BLOCKED in tutti else S.PASS)
            ev.append(A.salva_testo("f025-server.txt", righe))
            E.metti("F-025", esito, "1 %s · 2a %s · 2b %s · 3 %s" % (e1, e2a, e2b, e3),
                    atteso="A vivo ⇒ B rifiutato con 0x0F e A resta; A muto >15 s ⇒ B entra "
                           "(sfratto) e ritrova la scena; A risvegliato congedato",
                    osservato="1: %s | 2a: %s | 2b: %s | 3: %s" % (r1, r2a, r2b, r3),
                    evidenze=[x for x in ev if x])

            if o.guasto:
                gv = []
                # 1: B (dentro) si congeda prima che A bussi
                B.g.vai("about:blank")
                time.sleep(3)
                segno = A.segno_registro()
                amm, st, amb = G.tenta_tenace(A, chi, A.parola)
                righe = A.registro_da(segno)
                eg1, rg1 = giudica_rifiutato(amm, st.get("esito"), righe, chi, None, None)
                gv.append(eg1 == S.FAIL if amm is not None else None)
                print("   guasto 1 (l'altro NON e' vivo): il giudice dice %s — %s" % (eg1, rg1),
                      flush=True)
                # 2: nessun fantasma: A fermato e risvegliato subito, e vivo
                eg2, rg2 = S.BLOCKED, "A non e' rientrato"
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
                print("   guasto 2 (A vivo, niente fantasma): il giudice dice %s — %s" % (eg2, rg2),
                      flush=True)
                visto = None if None in gv else all(gv)
                E.guasto("F-025", visto, "l'altro congedato ⇒ %s (%s) · A vivo per %d s ⇒ %s (%s)"
                         % (eg1, rg1[:80], DOPO_S, eg2, rg2[:80]))


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
