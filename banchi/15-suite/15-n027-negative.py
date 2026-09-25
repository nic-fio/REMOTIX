#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-n027 — LE PROVE NEGATIVE (fasi/15 §«Prove negative», adattate)

    python3 15-n027-negative.py --scatola lxqt --browser firefox --porte-base 4930 [--guasto]

N-1  utente inesistente ............ sta in 15-f027 (sul server G8: conta come errore)
N-2  parola sbagliata .............. e' F-027 (15-f027)
N-3  sessione gia' chiusa con «Esci» ⇒ il nuovo accesso fa nascere una sessione
     NUOVA e PULITA.  Server normale (85xx).  L'inquilino entra, apre una scena
     di colore noto (GIALLO), esce col gesto «Esci» del suo desktop (lo stesso di
     C20/C24: il metodo D-Bus che il menu raggiunge).  Atteso: il prodotto dice
     la sessione finita, la pagina torna al modulo, i programmi della sessione
     non ci sono piu'; rientrando, il server fa NASCERE una sessione («LA FACCIO
     NASCERE») e la tela — desktop vero, non degenere — NON mostra il giallo.
N-4  rete non disponibile.  Sul server G8 (porta 862x): la pagina e' caricata,
     poi il server si SPEGNE, e l'utente preme «Collegati».  Atteso: entro 40 s
     la pagina dice che non si collega (esito «male», una frase), niente
     «Ammesso», non resta appesa.  E la pagina ricaricata a server spento: che
     cosa dice il browser (si registra; la pagina del prodotto non c'e').  Alla
     fine il server G8 si riaccende.
N-5  stesso utente gia' attivo da un altro dispositivo ... e' F-025 (15-f025).

GUASTI:
  N-3  al posto di «Esci», uno STACCO (la pagina va su about:blank: il filo
       cade, la sessione resta) e si rientra ⇒ la scena gialla c'e' ancora e
       nessuna sessione nasce ⇒ il giudice deve dire rosso.
  N-4  il server NON si spegne ⇒ «Ammesso» ⇒ il giudice deve dire rosso.
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
NASCITA = "LA FACCIO NASCERE"
FINITA = [p for p, _d in S.C20V.C20.RIGHE_FINITA]


# ═══════════════════════════════════════════════════════════════════════════
#  I GIUDICI — puri
# ═══════════════════════════════════════════════════════════════════════════
def giudica_rientro(finita, pagina_modulo, processi_dopo, righe_rientro, entrato, fr):
    """N-3: (esito, ragione)."""
    if not finita:
        return S.BLOCKED, "il prodotto non ha dichiarato la sessione finita: «Esci» non guardabile"
    if not entrato:
        return S.FAIL, "dopo «Esci» non si rientra"
    if fr is None:
        return S.BLOCKED, "rientrato, ma la tela non si fotografa"
    guai = []
    if not any(NASCITA in r for r in righe_rientro):
        guai.append("al rientro il server NON fa nascere una sessione")
    if fr.get("giallo", 0) > 0.01:
        guai.append("la scena della sessione chiusa c'e' ancora (giallo %.1f%%)" % (100 * fr["giallo"]))
    if processi_dopo:
        guai.append("dopo «Esci» restano %d processi della scena" % processi_dopo)
    if guai:
        return S.FAIL, "; ".join(guai)
    return S.PASS, ("finita, modulo %s, nessun programma rimasto, al rientro sessione NATA e tela "
                    "pulita (giallo %.2f%%)" % ("visibile" if pagina_modulo else "dopo ricarica",
                                                100 * fr.get("giallo", 0)))


def giudica_senza_rete(ammesso, stato, attesa_s):
    """N-4: (esito, ragione)."""
    esito = (stato or {}).get("esito") or ""
    if ammesso is True:
        return S.FAIL, "server spento e la pagina dice «%s»" % esito
    if (stato or {}).get("esito_classe") == "male" and esito.strip():
        return S.PASS, "in %.0f s la pagina dice «%s»" % (attesa_s, esito[:120])
    return S.FAIL, ("server spento: dopo %.0f s la pagina resta appesa senza dire niente di chiaro "
                    "(esito «%s»)" % (attesa_s, esito[:120]))


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    nata = ["[c] ⭐ nessuna sessione grafica per «c»: LA FACCIO NASCERE io"]
    prova("rientro pulito ⇒ PASS", giudica_rientro(True, True, 0, nata, True, {"giallo": 0.0})[0] == S.PASS)
    prova("scena ancora li' ⇒ FAIL", giudica_rientro(True, True, 0, nata, True, {"giallo": 0.8})[0] == S.FAIL)
    prova("nessuna nascita ⇒ FAIL", giudica_rientro(True, True, 0, [], True, {"giallo": 0.0})[0] == S.FAIL)
    prova("programmi rimasti ⇒ FAIL", giudica_rientro(True, True, 2, nata, True, {"giallo": 0.0})[0] == S.FAIL)
    prova("non finita ⇒ BLOCKED", giudica_rientro(False, True, 0, nata, True, {"giallo": 0.0})[0] == S.BLOCKED)
    prova("senza rete, frase ⇒ PASS", giudica_senza_rete(
        False, {"esito_classe": "male", "esito": "il server non risponde"}, 5)[0] == S.PASS)
    prova("senza rete, ammesso ⇒ FAIL", giudica_senza_rete(True, {"esito": "Ammesso"}, 5)[0] == S.FAIL)
    prova("senza rete, appesa ⇒ FAIL", giudica_senza_rete(
        None, {"esito_classe": "", "esito": "Collego…"}, 40)[0] == S.FAIL)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def processi_scena(sc, chi):
    # ⚠ solo l'APPLICAZIONE della sessione: il servitore della scena l'ha
    #   lanciato il banco fuori dalla sessione (runuser), e «Esci» non lo vede
    c, t = G.dentro(sc, "pgrep -u %s -x firefox-esr 2>/dev/null | wc -l; true" % chi, 30)
    try:
        return int(t.split()[-1])
    except (ValueError, IndexError):
        return None


def scena_gialla(o, s):
    S.C21.sveglia(s.g, s.geometria())
    ok, t = G.accendi_scena(s.sc, s.chi, o.porte_base + G.SPOSTA_SCENA, GIALLO)
    if not ok:
        return None, "la scena gialla non si accende: %s" % " | ".join(t.splitlines()[-5:])[-300:]
    fr, dove, perche = G.aspetta_colore(s, "scena-gialla", COLORI, "giallo", 0.5, 40)
    if not fr or fr["giallo"] < 0.5:
        return None, "la scena gialla non copre la tela: %s %s" % (G.fr_testo(fr), perche)
    return fr, dove


def rientra_e_guarda(s, segno, pausa=8):
    """Rientra (dal modulo se c'e', se no ricaricando) e fotografa dopo `pausa` s.
    Torna (entrato, frazioni, righe del server dal segno, foto)."""
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
            raise S.Bloccata("l'inquilino non entra: " + m)
        fr, dove = scena_gialla(o, s)
        if fr is None:
            raise S.Bloccata(dove)
        ev = [dove]
        desk, gesto = s.sc.gesto_esci()
        if not gesto:
            raise S.Bloccata("non so come si dice «Esci» in questa scatola")
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
        E.metti("N-3", e, r, atteso="«Esci» (%s) ⇒ sessione finita, modulo, nessun programma; al "
                "rientro una sessione NUOVA e pulita" % desk,
                osservato="%s · il prodotto: «%s» · la pagina dopo «Esci»: «%s»" % (
                    r, forma, (pag.get("esito") or "")[:80]), evidenze=[x for x in ev if x])

        if o.guasto:
            fr, dove = scena_gialla(o, s)
            if fr is None:
                E.guasto("N-3", None, "la scena gialla non si riaccende: " + dove)
                return
            s.g.vai("about:blank")                     # ⛔ il guasto: stacco, non «Esci»
            time.sleep(4)
            segno3 = s.segno_registro()
            entrato, fr3, righe, _d = rientra_e_guarda(s, segno3)
            eg, rg = giudica_rientro(True, True, 0, righe, entrato, fr3)
            E.guasto("N-3", eg == S.FAIL if eg != S.BLOCKED else None,
                     "stacco al posto di «Esci» ⇒ il giudice dice %s: %s" % (eg, rg))


def n4(o, E):
    srv = G.MioServer(o.scatola)
    if not srv.acceso():
        ok, t = srv.accendi()
        if not ok:
            E.metti("N-4", S.BLOCKED, "il server G8 non si accende: " + t)
            return
    o4 = G.o_per(o, 1)
    o4.porta = srv.porta
    o4.url = "https://%s:%d/" % (o.host, srv.porta)
    srv.sblocca()
    try:
        with S.Sessione(o4, "027", E) as s:
            ok, m = s.pr.apri()
            if not ok:
                E.metti("N-4", S.BLOCKED, "la pagina del server G8 non si apre: " + m)
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
            E.metti("N-4", e, r, atteso="server spento ⇒ entro 40 s una frase chiara, niente "
                    "«Ammesso», la pagina non resta appesa",
                    osservato="%s · ricaricata a server spento il browser dice: «%s» (%s)" % (
                        r, browser_dice, t.splitlines()[-1] if t else "?"), evidenze=ev)
            ok, t = srv.accendi()
            if o.guasto:
                if not ok:
                    E.guasto("N-4", None, "il server G8 non si riaccende: " + t)
                else:
                    t0 = time.time()
                    amm, st = G.tenta(s, s.chi, s.parola, 40)
                    eg, rg = giudica_senza_rete(amm, st, time.time() - t0)
                    E.guasto("N-4", eg == S.FAIL if amm is not None else None,
                             "server acceso al posto di spento ⇒ il giudice dice %s: %s" % (eg, rg))
    finally:
        if not srv.acceso():
            print("   server G8 riacceso: %s" % (srv.accendi(),), flush=True)


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
