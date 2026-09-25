#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f020 — F-020 IL BROWSER UCCISO DI COLPO, POI UN BROWSER NUOVO · percorso P-E

    python3 15-f020-browser-chiuso-di-colpo.py --scatola lxqt --browser chrome [--guasto]

La scena e' quella di 15-f016 (15-g6-comune): firefox-esr nella sessione, un
testo scritto con tasti veri e letto a colori nella foto; il programma annota
il suo stato (gettone, valore) ogni 2 s.

  P-E  creazione → applicazione aperta, testo scritto → il browser UCCISO
       (kill -9 del processo e di TUTTI i suoi figli: nessun congedo, il filo
       tace e basta) → un browser NUOVO (profilo nuovo) → stesso utente e parola
       → stato ritrovato → input.

F-020  atteso (`SPECIFICHE.md` §5.1, §5.3; `src/rcp.c` ~265-350):
       - il vecchio filo non si e' congedato: per il server e' un client che
         TACE.  Finche' tace da meno di 15 s il posto e' suo (lo «sfratto del
         fantasma», `SFRATTO_PREDEFINITO` = SILENZIO/2) e il nuovo accesso puo'
         essere rifiutato con `0x0F` («il posto di questa sessione risulta
         occupato… riprova fra qualche secondo»): e' il comportamento
         DICHIARATO, non un difetto — ci si riprova ogni 3 s, come l'utente;
       - entro SILENZIO (30 s) + margine (TETTO_S = 40 s dall'uccisione) si deve
         ENTRARE, e ritrovare la STESSA sessione: stesso PID del compositore e
         della scena (campo), stesso gettone e testo (campo), finestra e
         striscia nella foto.
P-E    atteso: F-020 e, dopo, l'input arriva (lettere nuove lette in foto).

GUASTO (vero, nella scena): si uccide di nuovo il browser e intanto si uccide
       la SESSIONE dell'inquilino (loginctl terminate-user + kill -9 dei suoi
       processi) — cioe' «la sessione non sopravvive al client».  Il rientro fa
       nascere una sessione NUOVA: F-020 e P-E devono dare ROSSO (gettone,
       PID, finestra: niente combacia).
"""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._carica("g6", os.path.join(S.QUI, "15-g6-comune.py"))
F16 = S._carica("f016", os.path.join(S.QUI, "15-f016-stacco-e-riattacco.py"))
FUNZIONI = ("F-020", "P-E")
TETTO_S = 40.0           # SILENZIO (30 s, §5.3) + il margine dei 3 s fra un tentativo e l'altro
FANTASMA_S = 15.0        # SFRATTO_PREDEFINITO: sotto, un rifiuto 0x0F e' l'atteso


def giudica_rientro(ok, secondi, rifiuti, prima, dopo, vista, stato, testo, gettone):
    """F-020.  Torna (esito, ragione)."""
    if not ok:
        return S.FAIL, ("nessun rientro in %.0f s dall'uccisione del browser (tetto %d s = "
                        "silenzio + margine); rifiuti: %s" % (secondi, TETTO_S,
                                                               " | ".join(rifiuti)[:400]))
    probl = []
    fuori_tempo = [r for r in rifiuti if "occupato" not in r]
    if fuori_tempo:
        probl.append("rifiuti che NON sono il posto occupato del fantasma: %s"
                     % " | ".join(fuori_tempo)[:300])
    pf0, pf1 = G.pid_scena(prima), G.pid_scena(dopo)
    if pf0 is None:
        return S.BLOCKED, "prima dell'uccisione la scena non c'era"
    if pf1 != pf0:
        probl.append("il programma della scena era %s, dopo %s" % (pf0, pf1))
    for comp in ("gnome-shell", "kwin_wayland", "labwc"):
        if prima.get(comp) and sorted(prima[comp]) != sorted(dopo.get(comp) or []):
            probl.append("il compositore %s era %s, dopo %s" % (comp, prima[comp],
                                                               dopo.get(comp)))
    e, r = F16.giudica_ritrovo(testo, vista, stato, gettone)
    if e != S.PASS:
        probl.append(r)
    if probl:
        return S.FAIL, "; ".join(probl)
    return S.PASS, ("rientrato %.1f s dopo l'uccisione (%d rifiuti del fantasma prima): "
                    "stessa sessione, stessi PID, %s" % (secondi, len(rifiuti), r))


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    pr = {"firefox-esr": ["100"], "labwc": ["90"]}
    vista = G.guarda_la_scena(F16._Finta(F16.scena_finta("abc")), "x")
    st = {"g": "x", "v": "abc"}
    e, m = giudica_rientro(True, 17.0, ["3.0s l'accesso: la pagina dice: «il posto di questa "
                                        "sessione risulta occupato»"], pr, pr, vista, st, "abc", "x")
    prova("rientro dopo il fantasma ⇒ PASS (%s)" % m[:60], e == S.PASS)
    e, _ = giudica_rientro(False, 41.0, ["occupato"] * 12, pr, pr, vista, st, "abc", "x")
    prova("mai rientrato ⇒ FAIL", e == S.FAIL)
    vuota = G.guarda_la_scena(F16._Finta(F16.scena_finta(None)), "x")
    e, _ = giudica_rientro(True, 5.0, [], pr, {"labwc": ["300"]}, vuota,
                           {"g": "nuovo", "v": ""}, "abc", "x")
    prova("sessione rinata ⇒ FAIL", e == S.FAIL)
    e, _ = giudica_rientro(True, 5.0, ["3.0s l'accesso: nessuna ammissione"], pr, pr, vista, st,
                           "abc", "x")
    prova("un rifiuto che non e' il fantasma ⇒ FAIL", e == S.FAIL)
    return 0 if ok else 1


def un_giro(o, E, s, testo, passata, guasto=False):
    metti = (lambda f, e, r, **k: E.guasto(f, e == S.FAIL, "guasto (sessione uccisa): " + r, **k)) \
        if guasto else (lambda f, e, r, **k: E.metti(f, e, r, passata=passata, **k))
    q0 = G.quaderno(s)
    gettone = next((r.get("g") for r in reversed(q0) if r.get("v") == testo), None)
    prima = G.processi(s)
    segno = s.segno_registro()
    print("   prima: %s · gettone %s" % (prima, gettone), flush=True)
    # ── IL BROWSER UCCISO: kill -9 di tutto l'albero, nessun congedo
    n = G.uccidi_browser(s)
    t_kill = time.time()
    print("   ⛔ browser ucciso: %d processi (kill -9)" % n, flush=True)
    if guasto:
        c, t = s.sc.dentro("loginctl terminate-user %s >/dev/null 2>&1; sleep 1; "
                           "pkill -KILL -u %s; sleep 2; pgrep -u %s -x firefox-esr || "
                           "echo 'sessione uccisa'" % (s.chi, s.chi, s.chi), 60)
        print("   ⛔ GUASTO: %s" % t.strip()[-60:], flush=True)
    # ── UN BROWSER NUOVO, subito: se il fantasma tiene il posto, si riprova
    s.accendi_browser()
    ok, m, rifiuti, _sec = G.entra_con_riprova(s, tetto_s=TETTO_S - (time.time() - t_kill))
    secondi = time.time() - t_kill
    reg = s.registro_da(segno) if segno is not None else []
    ev = [s.salva_testo("server-%s.txt" % passata, reg)]
    sfr = [r for r in reg if "sfratt" in r.lower() or "fantasma" in r.lower()]
    vista, stato, dopo = {"finestra": None, "perche": "non rientrato"}, None, {}
    if ok:
        vista = G.aspetta_testo(s, testo, "rientro-%s" % passata,
                                tetto=12 if not guasto else 20)
        stato = G.ultimo_stato(s)
        dopo = G.processi(s)
    e20, r20 = giudica_rientro(ok, secondi, rifiuti, prima, dopo, vista, stato, testo, gettone)
    metti("F-020", e20, r20,
          atteso="entro %d s dall'uccisione: ammesso (prima dei %d s un rifiuto «posto "
                 "occupato» e' l'atteso), stessa sessione, stato ritrovato" % (TETTO_S, FANTASMA_S),
          osservato="%s · rientro a %.1f s · rifiuti %d · registro del fantasma: %s · PID %s → %s"
          % (m[:120], secondi, len(rifiuti), (sfr[-1].split("] ", 1)[-1][:160] if sfr else "—"),
             G.pid_scena(prima), G.pid_scena(dopo)),
          evidenze=ev + [vista.get("foto", "")])
    # ── P-E: l'input dopo
    in_ok, r_in = False, "nessuna finestra su cui scrivere"
    if ok and vista.get("finestra"):
        agg = F16.testo_a_caso(2)
        cl = G.clic_sulla_scena(s, vista)
        G.scrivi(s, agg)
        v2 = G.aspetta_testo(s, testo + agg, "input-dopo-%s" % passata, tetto=10)
        in_ok = v2.get("letto") == testo + agg
        r_in = "scritto «%s» (%s): la foto legge «%s»" % (agg, cl, v2.get("letto"))
        if in_ok:
            testo = testo + agg
    ee = S.PASS if (e20 == S.PASS and in_ok) else S.FAIL
    metti("P-E", ee, "rientro %s · input dopo: %s" % (e20, r_in),
          atteso="creazione→browser ucciso→nuova connessione→stato→input",
          osservato=r_in, evidenze=ev)
    return testo


def corpo(o, E):
    with S.Sessione(o, "020", E) as s:
        try:
            ok, m = s.entra()
            if not ok:
                raise S.Bloccata("senza accesso non c'e' niente da uccidere: " + m)
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
            testo = un_giro(o, E, s, testo, "sana")
            if o.guasto:
                if s.g is None:
                    s.accendi_browser()
                un_giro(o, E, s, testo, "guasto", guasto=True)
        finally:
            if s.g:
                s.salva_console()
            G.spegni_servitore(s)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
