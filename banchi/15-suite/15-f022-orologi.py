#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f022 — I TRE OROLOGI DI §5.3: F-022 silenzio · F-023 inattivita' · F-024 abbandono

    python3 15-f022-orologi.py --scatola kde --browser chrome --guasto --porta 8612

⛔ SERVER SUO (`15-g7-server.sh`, porte 8611-8614): gli orologi si accorciano
   dalla riga di comando e il server si RIACCENDE fra una fase e l'altra — sulla
   851x non si puo'.  Alla fine il server resta acceso coi PREDEFINITI.

I NOMI E I VALORI VERI (letti nel codice, non in SPECIFICHE):
  · silenzio del client: 30 s FISSO (`rcp.c` `#define SILENZIO 30000`, non
    configurabile) — ⚠ ma prima scatta la LINEA MORTA a 10 s senza un pacchetto
    (`--linea-morta-silenzio-s`, predefinito 10, `webtransport.c`): e' lei che
    stacca un client muto, e lascia il posto.  ⇒ l'atteso di F-022 e' «staccato
    ENTRO 30 s», qualunque dei due lo faccia, e la riga lo dice;
  · inattivita' dell'utente: `--inattivita-s` (predefinito 1800), in SECONDI;
    si azzera su OGNI byte di RCP dal client (`rcp.c` ~7523), scatta con
    `CONGEDO 0x02` e la riga «§5.3 — INATTIVITA'»; la sessione grafica RESTA;
  · abbandono della sessione: `--abbandono-s` (predefinito 3600); si nutre dei
    SOLI cinque gesti d'input (`main.c` `input_al_figlio` → `presenza_segna`),
    scatta con la riga «§5.3 — ABBANDONO» e chiude la sessione grafica coi
    suoi programmi (`figli_termina_sessione`).

F-022  (server predefinito) il browser si FERMA (SIGSTOP a tutto l'albero dei
       processi: il client tace, come un portatile che si spegne) ⇒ atteso: entro
       30 s il server lo stacca (riga `linea-morta`/`STACCATO`/`posto LASCIATO`),
       la sessione resta (i programmi dell'inquilino vivi), e ripreso il browser
       si rientra con utente e parola ritrovando gli stessi programmi.
       GUASTO: il browser NON si ferma ⇒ nessuno stacco in 35 s ⇒ il giudice deve
       dire «non staccato» (rosso).
F-023  (server con `--inattivita-s 12 --abbandono-s 45`) un clic e poi niente ⇒
       atteso: fra 12 e 12+15 s la riga INATTIVITA', la pagina lo DICE (frase
       rossa, modulo in vista, niente ricollegamento da se'), i programmi restano,
       e si rientra SOLO con utente e parola.
F-024  (stessa sessione) nessun gesto da quel clic ⇒ atteso: entro 45+15 s la
       riga ABBANDONO, e i processi della sessione dell'inquilino (la scena
       compresa) SPARISCONO.
       GUASTO F-023/F-024: gli orologi LUNGHI (i predefiniti) al posto di quelli
       corti, stessa sequenza ⇒ nessuna INATTIVITA' in 12+15 s, nessun ABBANDONO
       in 45+15 s, scena viva ⇒ i due giudici devono dire rosso.
"""
import importlib.util as _iu
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

_s = _iu.spec_from_file_location("g7comune", os.path.join(S.QUI, "15-g7-comune.py"))
G7 = _iu.module_from_spec(_s)
_s.loader.exec_module(G7)
G7.scatola_locale(S)
_f = _iu.spec_from_file_location("f019", os.path.join(S.QUI, "15-f019-la-rete-cade.py"))
F019 = _iu.module_from_spec(_f)
_f.loader.exec_module(F019)

FUNZIONI = ("F-022", "F-023", "F-024")
SERVER = "15-g7-server.sh"
SILENZIO_S = 30
MARGINE_S = 15
# ⚠ 25 e non 12: `[M]` 25 set 2026 (D-011) l'orologio d'inattivita' conta dall'ultimo
#   byte del client, cioe' dall'ATTACCA, anche mentre la sessione NASCE; su XFCE
#   in 4K la nascita supera i 12 s ⇒ CONGEDO 0x02 un secondo dopo il primo
#   fotogramma.  Coi valori veri (1800 s) non morde; qui l'orologio va tenuto
#   piu' lungo della nascita piu' lenta.
INATTIVITA_S = 25
ABBANDONO_S = 60
FORME_STACCO = ("linea-morta", "STACCATO per silenzio", "posto LASCIATO")


def certifica():
    ok = True
    # il giudice dello stacco: una riga di un ALTRO inquilino non conta
    righe = ["21:00 rcp [c15022u111] posto LASCIATO da c15022u111 via x (occupati 0)"]
    if giudica_stacco(righe, "c15022u222")[0]:
        print("⛔ lo stacco di un altro inquilino conta come mio")
        ok = False
    if not giudica_stacco(righe, "c15022u111")[0]:
        print("⛔ lo stacco dell'inquilino non si vede")
        ok = False
    for inatt, abb in ((12, 45), (1800, 3600)):
        if not (inatt + MARGINE_S < abb):
            print("⛔ gli orologi si pestano: inattivita' %d, abbandono %d" % (inatt, abb))
            ok = False
    print("%s giudici degli orologi" % ("⭐" if ok else "⛔"))
    return 0 if ok else 1


def giudica_stacco(righe, chi):
    for r in righe:
        if chi not in r:
            continue
        for f in FORME_STACCO:
            if f in r:
                return True, r
    return False, None


def accendi(o, *opz):
    ok, t = G7.server("accendi", o.scatola, *opz)
    if not ok:
        raise S.Bloccata("il server nostro non si accende (%s): %s" % (" ".join(opz), t[-300:]))
    inatt, abb, riga = G7.orologi_in_vigore(o.scatola)
    print("   server nostro: inattivita' %s s · abbandono %s s" % (inatt, abb), flush=True)
    return inatt, abb


def sessione_con_scena(s, reg=None):
    segno = reg.righe() if reg else None
    ok, m = F019.entra_con_orecchio(s)
    if not ok:
        # ⛔ D-011 (25 set 2026): qui il giro diceva solo «la tela non ha area
        #    visibile» e le prove del perche' sparivano col riavvio del server.
        #    ⇒ Prima di arrendersi si fotografa lo STATO DELLA PAGINA (che cosa
        #    dice, se e' ancora vestita da desktop, il suo registro) e le righe
        #    del server per questo inquilino, e la frase della pagina entra nella
        #    ragione del BLOCKED.
        time.sleep(1)
        pag = G7.pagina(s.g)
        s.salva_testo("pagina-ingresso-fallito.txt",
                      "\n".join("%s: %s" % kv for kv in pag.items()))
        if reg is not None and segno is not None:
            s.salva_testo("server-ingresso-fallito.txt", reg.da(segno, s.chi))
        s.salva_console()
        raise S.Bloccata("non si entra: %s · la pagina: esito «%s», vestita=%s, modulo=%s"
                         % (m, (pag.get("esito") or "")[:120], pag.get("vestita"),
                            pag.get("modulo_visibile")))
    F019.clic_tela(s)                 # ⭐ il PRIMO gesto: parte l'orologio dell'abbandono
    t_gesto = time.time()
    pid, t = G7.lancia_scena(s)
    if not pid:
        raise S.Bloccata("la scena non parte: " + t)
    vista, t = G7.aspetta_scena(s, S)
    if not vista:
        raise S.Bloccata(t)
    return pid, t_gesto


# ─────────────────────────────────────────────────────────────────────────────
def fase_silenzio(o, E, reg):
    with S.Sessione(o, "022", E) as s:
        pid, _t = sessione_con_scena(s, reg)
        segno = reg.righe()
        fermati = G7.ferma_browser(s.g)
        t0 = time.time()
        try:
            forma, riga, dopo = reg.aspetta(segno, FORME_STACCO, s.chi,
                                            tetto=SILENZIO_S + 5, passo=1.0)
            vivi = G7.processi_inquilino(o.scatola, s.chi)
        finally:
            G7.riprendi_browser(s.g)
        print("   F-022: fermati %d processi del browser · stacco: %s dopo %.0f s"
              % (len(fermati), forma, dopo), flush=True)
        time.sleep(2)
        ok_r, come, mr = F019.rientra(s, 40)
        ps1 = G7.processi_inquilino(o.scatola, s.chi)
        ev = [s.salva_testo("server-f022.txt", reg.da(segno, s.chi)), s.salva_console()]
        atteso = ("browser fermo ⇒ staccato entro %d s (riga linea-morta/STACCATO/posto "
                  "LASCIATO), sessione viva, si rientra coi programmi di prima" % SILENZIO_S)
        oss = ("stacco: %s · programmi vivi durante: %s · rientro %s: %s (%s) · scena di prima "
               "viva dopo: %s" % ((riga or "NESSUNO")[:180], pid in vivi, come,
                                   "riuscito" if ok_r else "FALLITO", mr[:100], pid in ps1))
        if not fermati:
            E.metti("F-022", S.BLOCKED, "non ho potuto fermare il browser (nessun pid)",
                    evidenze=ev)
        elif not forma:
            E.metti("F-022", S.FAIL, "il client tace da %d s e il server NON lo stacca"
                    % (SILENZIO_S + 5), atteso=atteso, osservato=oss, evidenze=ev)
        elif pid not in vivi or not ok_r or pid not in ps1:
            E.metti("F-022", S.FAIL, "staccato, ma la sessione non si ritrova: " + oss,
                    atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-022", S.PASS, "staccato dopo %.0f s da «%s», sessione ritrovata"
                    % (dopo, forma), atteso=atteso, osservato=oss, evidenze=ev)
        if o.guasto:
            # GUASTO: il browser NON si ferma — il giudice deve dire «non staccato»
            segno2 = reg.righe()
            forma2, riga2, dopo2 = reg.aspetta(segno2, FORME_STACCO, s.chi,
                                               tetto=SILENZIO_S + 5, passo=2.0)
            E.guasto("F-022", forma2 is None,
                     "browser vivo ⇒ il giudice %s" % ("non vede stacchi in %d s (rosso)"
                                                      % (SILENZIO_S + 5) if forma2 is None
                                                      else "vede uno STACCO: " + riga2[:150]))


def fase_orologi(o, E, reg, corti):
    """corti=True: la passata sana (F-023, F-024); False: il GUASTO (orologi lunghi)."""
    passata = "sana" if corti else "guasto"
    with S.Sessione(o, "022", E) as s:
        segno = reg.righe()
        pid, t_gesto = sessione_con_scena(s, reg)
        # — F-023 —
        forma, riga, _d = reg.aspetta(segno, ["INATTIVITA'"], s.chi,
                                      tetto=max(1, INATTIVITA_S + MARGINE_S - (time.time() - t_gesto)),
                                      passo=1.0)
        dopo = time.time() - t_gesto
        # la pagina ha fino a 10 s per dirlo (il CONGEDO arriva, poi il modulo)
        pag = G7.pagina(s.g)
        for _ in range(10):
            if not forma or G7.la_pagina_lo_dice(pag):
                break
            time.sleep(1)
            pag = G7.pagina(s.g)
        vivi = G7.processi_inquilino(o.scatola, s.chi)
        detto = G7.la_pagina_lo_dice(pag)
        if not corti:
            E.guasto("F-023", forma is None,
                     "orologio LUNGO ⇒ il giudice %s" % (
                         "non vede INATTIVITA' in %d s (rosso)" % (INATTIVITA_S + MARGINE_S)
                         if forma is None else "vede INATTIVITA': " + riga[:150]))
        else:
            ok_r, come, mr = (False, "", "non tentato")
            if forma:
                # si rientra SOLO con utente e parola: la pagina non deve essersi
                # ricollegata da se'
                da_se = bool(pag.get("sessione")) and pag.get("vestita") == "acceso" \
                    and not pag.get("modulo_visibile")
                ok_r, come, mr = F019.rientra(s, 40)
            ps1 = G7.processi_inquilino(o.scatola, s.chi)
            ev = [s.salva_testo("server-f023.txt", reg.da(segno, s.chi)),
                  s.salva_testo("pagina-f023.txt", "\n".join("%s: %s" % kv for kv in pag.items()))]
            atteso = ("un clic, poi niente ⇒ fra %d e %d s CONGEDO 0x02 (riga INATTIVITA'), la "
                      "pagina lo dice e torna al modulo, i programmi restano, si rientra con "
                      "utente e parola" % (INATTIVITA_S, INATTIVITA_S + MARGINE_S))
            oss = ("riga: %s · a %.0f s dal clic · pagina: esito «%s» modulo %s vestita %s · "
                   "scena viva %s · rientro %s: %s · scena viva dopo %s"
                   % ((riga or "NESSUNA")[:120], dopo, (pag.get("esito") or "")[:90],
                      pag.get("modulo_visibile"), pag.get("vestita"), pid in vivi, come,
                      "riuscito" if ok_r else mr[:80], pid in ps1))
            if not forma:
                E.metti("F-023", S.FAIL, "nessuna INATTIVITA' entro %d s dall'ultimo gesto"
                        % (INATTIVITA_S + MARGINE_S), atteso=atteso, osservato=oss, evidenze=ev)
            elif not detto:
                E.metti("F-023", S.FAIL, "staccato per inattivita', ma la pagina non lo dice: "
                        + oss, atteso=atteso, osservato=oss, evidenze=ev)
            elif pid not in vivi or not ok_r or pid not in ps1:
                E.metti("F-023", S.FAIL, "dopo l'inattivita' la sessione non si ritrova: " + oss,
                        atteso=atteso, osservato=oss, evidenze=ev)
            elif da_se:
                E.metti("F-023", S.FAIL, "la pagina si e' ricollegata da se' (non doveva)",
                        atteso=atteso, osservato=oss, evidenze=ev)
            else:
                E.metti("F-023", S.PASS, "staccato a %.0f s, pagina al modulo con «%s», rientrato "
                        "con la parola, scena ritrovata" % (dopo, (pag.get("esito") or "")[:60]),
                        atteso=atteso, osservato=oss, evidenze=ev)
        # — F-024 — nessun gesto dal clic: l'abbandono
        resta = ABBANDONO_S + MARGINE_S - (time.time() - t_gesto)
        forma4, riga4, _d = reg.aspetta(segno, ["ABBANDONO"], s.chi,
                                        tetto=max(1, resta), passo=2.0)
        dopo4 = time.time() - t_gesto
        time.sleep(4)
        ps4 = {}
        for _ in range(8):                        # la chiusura non e' istantanea
            ps4 = G7.processi_inquilino(o.scatola, s.chi)
            if pid not in ps4 and not (forma4 and ps4):
                break
            time.sleep(2)
        if not corti:
            rosso = forma4 is None and pid in ps4
            E.guasto("F-024", rosso,
                     "orologio LUNGO ⇒ il giudice %s" % (
                         "non vede ABBANDONO in %d s e la scena e' viva (rosso)"
                         % (ABBANDONO_S + MARGINE_S) if rosso
                         else "vede un ABBANDONO (%s) o la scena sparita (%s)"
                         % ((riga4 or "")[:100], pid not in ps4)))
            return
        ev = [s.salva_testo("server-f024.txt", reg.da(segno, s.chi)),
              s.salva_testo("processi-f024.txt", "\n".join("%d %s" % kv for kv in sorted(ps4.items())))]
        atteso = ("nessun gesto dal clic ⇒ entro %d s riga ABBANDONO e la sessione si chiude "
                  "coi suoi programmi (processi dell'inquilino spariti)" % (ABBANDONO_S + MARGINE_S))
        oss = ("riga: %s · a %.0f s dal clic · scena viva %s · processi dell'inquilino rimasti "
               "%d: %s" % ((riga4 or "NESSUNA")[:120], dopo4, pid in ps4, len(ps4),
                           ", ".join(sorted(set(ps4.values())))[:200]))
        if not forma4:
            E.metti("F-024", S.FAIL, "nessun ABBANDONO entro %d s dall'ultimo gesto"
                    % (ABBANDONO_S + MARGINE_S), atteso=atteso, osservato=oss, evidenze=ev)
        elif pid in ps4 or _residui(s):
            oss += " · non esenti (regola di F-021): %s" % ", ".join(_residui(s) or [])[:200]
            E.metti("F-024", S.FAIL, "ABBANDONO scritto, ma restano processi della sessione: "
                    + oss, atteso=atteso, osservato=oss, evidenze=ev)
        else:
            E.metti("F-024", S.PASS, "abbandono a %.0f s dal clic, nessun processo dell'inquilino "
                    "rimasto" % dopo4, atteso=atteso, osservato=oss, evidenze=ev)


def _residui(s):
    """⭐ I processi dell'inquilino che NON devono restare, con la stessa regola
    di F-021 (gruppo di controllo): il figlio `remotix` resta per disegno (il
    rientro nasce in lui) e il gestore d'utente di systemd coi suoi servizi
    (dbus, pipewire, wireplumber) vive quanto la sessione di logind del figlio.
    `[M]` 25 set 2026, LXQt: restavano esattamente quelli ⇒ un FAIL del BANCO."""
    import importlib.util as _iu
    f = os.path.join(os.path.dirname(os.path.abspath(__file__)), "15-f021-esci.py")
    sp = _iu.spec_from_file_location("f021", f)
    m = _iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m.residui(m.processi(s))


def corpo(o, E):
    if not o.porta:
        o.porta = G7.PORTE_G7[o.scatola]
        o.url = "https://%s:%d/" % (o.host, o.porta)
    if o.porta != G7.PORTE_G7[o.scatola]:
        raise S.Bloccata("la porta %d non e' quella del server nostro (%d)"
                         % (o.porta, G7.PORTE_G7[o.scatola]))
    prima_8511 = F019.sano_8511(o)
    reg = G7.Registro(o.scatola)
    try:
        print("   %s" % F019.server_pronto(o), flush=True)
        try:
            fase_silenzio(o, E, reg)
        except S.Bloccata as b:
            E.bloccate(["F-022"], str(b))
            if o.guasto:
                E.bloccate(["F-022"], str(b), passata="guasto")
        accendi(o, "--inattivita-s", str(INATTIVITA_S), "--abbandono-s", str(ABBANDONO_S))
        fase_orologi(o, E, reg, corti=True)
        if o.guasto:
            accendi(o)                                # i LUNGHI: i predefiniti
            try:
                fase_orologi(o, E, reg, corti=False)
            except S.Bloccata as b:
                E.bloccate(["F-023", "F-024"], str(b), passata="guasto")
    finally:
        inatt, abb, _r = G7.orologi_in_vigore(o.scatola)
        if (inatt, abb) != (1800, 3600):
            G7.server("accendi", o.scatola)           # si lascia coi predefiniti
        dopo_8511 = F019.sano_8511(o)
        print("   server 851x prima «%s» dopo «%s»%s" % (
            prima_8511, dopo_8511, "" if prima_8511 == dopo_8511 else "  ⛔ CAMBIATO"), flush=True)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
