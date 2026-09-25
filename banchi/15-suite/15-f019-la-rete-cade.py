#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f019 — F-019 PERDITA DI RETE E RIENTRO · percorsi P-B e P-D

    python3 15-f019-la-rete-cade.py --scatola gnome --browser firefox --guasto --porta 8611

⛔ SERVER SUO: gira contro il SECONDO server del prodotto della scatola
   (`15-g7-server.sh`, porte 8611-8614, orologi PREDEFINITI) — la linea che
   cade si simula con nftables e sulla 851x la vedrebbero tutti.

⛔ LA SIMULAZIONE, dichiarata (decisione presa per la suite): la linea muore
   SULLA RETE DEL SERVER — una tabella nftables nostra (`inet remotix_g7_<porta>`)
   scarta TUTTO l'UDP della porta del server nostro (QUIC/WebTransport), nei due
   versi, per CADUTA_S secondi; poi si toglie (sempre: anche se la prova cade).
   ⚠ Non e' il percorso vero dal tablet (Wi-Fi, `wondershaper`): browser e
   server stanno sulla stessa macchina, e la pagina HTTPS (TCP) resta raggiungibile.

L'ATTESO VERO, letto nel codice (non nelle intenzioni):
  · il SERVER dichiara la linea morta dopo 10 s senza un pacchetto
    (`--linea-morta-silenzio-s`, predefinito 10: `webtransport.c`
    `linea_morta_giudica`, riga `linea-morta … causa=silenzio`), chiude la
    connessione e LASCIA IL POSTO; la sessione grafica resta (I4);
  · il rientro e' A MANO (decisione dell'utente del 23 ago 2026, `main.c`
    `--niente-linea-morta`: «il filo cade e si rientra a mano»): la pagina NON si
    ricollega da se' — non c'e' nessun codice che lo faccia;
  · la PAGINA deve DIRLO (SPECIFICHE §8.2 e §3.2 della pagina: «un'attesa muta
    e' un guasto»; `torna_al_modulo()` per ogni congedo): una frase visibile o il
    modulo tornato in vista.  ⚠ Nel codice di oggi la chiusura del trasporto
    SENZA `CONGEDO` (quella della linea morta: il `CONGEDO` non puo' arrivare su
    una linea che non porta) finisce in `nota()` — il registro nascosto — e basta.

F-019  atteso: il server scrive `linea-morta` per l'inquilino; la pagina lo dice
       entro OSSERVA_S dal ritorno della linea (con un movimento del mouse, come
       farebbe chi e' davanti); si rientra (dal modulo se c'e', altrimenti
       ricaricando: e' «a mano»); e i programmi
       della sessione sono gli STESSI (pid).  ⚠ Non si pretende la frase
       «sessione ripresa»: `rcp.c` manda SEMPRE `1 = NUOVA` in `SESSIONE`
       (riga ~3051), quindi la pagina dice «sessione nuova» anche quando la
       ritrova — lo si scrive nell'osservato, e il giudizio viene dai pid.
P-B    creazione → attivita' → perdita → rientro → attivita': dopo il rientro la
       scena in movimento (weston-simple-egl) si muove nelle FOTOGRAFIE, ed e' lo
       stesso processo di prima.
P-D    creazione → video/audio → perdita → rientro: con la scena E un tono vero
       (pw-play 440 Hz sul sink «remotix») accesi durante la caduta, dopo il
       rientro la foto si muove E il suono che la pagina SUONA non e' silenzio
       (RMS dei campioni passati a `AudioBufferSourceNode.start`, non un contatore).

GUASTO (seconda caduta, stessa sessione): durante la linea morta si UCCIDONO la
       scena e il tono (lo stato si perde) e il rientro si tenta con la linea
       ANCORA morta ⇒ F-019 deve vedere «non si rientra»; poi la linea torna, si
       rientra, e P-B deve vedere la scena ferma/sparita e P-D il silenzio.
"""
import importlib.util as _iu
import os
import signal
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

_s = _iu.spec_from_file_location("g7comune", os.path.join(S.QUI, "15-g7-comune.py"))
G7 = _iu.module_from_spec(_s)
_s.loader.exec_module(G7)
G7.scatola_locale(S)

FUNZIONI = ("F-019", "P-B", "P-D")
SERVER = "15-g7-server.sh"
CADUTA_S = 20          # la linea morta; il server la dichiara a 10 s
OSSERVA_S = 60         # dopo il ritorno della linea: quanto si aspetta che la pagina lo dica
TETTO_RIENTRO_S = 40


def extra(a):
    a.add_argument("--caduta-s", type=int, default=CADUTA_S)
    a.add_argument("--osserva-s", type=int, default=OSSERVA_S)


def certifica():
    ok = True
    lm = G7.LineaMorta(8611)
    r = lm.regole()
    for atteso in ("table inet remotix_g7_8611", "udp dport 8611 counter drop",
                   "udp sport 8611 counter drop", "hook input", "hook output"):
        if atteso not in r:
            print("⛔ la regola non ha «%s»" % atteso)
            ok = False
    try:
        G7.LineaMorta(8511)
        print("⛔ la linea morta accetta la 8511 (quella di tutti)")
        ok = False
    except AssertionError:
        print("⭐ la linea morta rifiuta le porte che non sono nostre")
    casi = [({"esito_visibile": True, "esito_classe": "male", "vestita": "acceso"}, True),
            ({"esito_visibile": False, "modulo_visibile": True, "vestita": None}, True),
            ({"esito_visibile": False, "modulo_visibile": False, "vestita": "acceso"}, False),
            ({"esito_visibile": True, "esito_classe": "bene", "vestita": "acceso"}, False),
            ({"errore": "x"}, None)]
    for st, att in casi:
        v = G7.la_pagina_lo_dice(st)
        if v is not att:
            print("⛔ la_pagina_lo_dice(%s) = %s, atteso %s" % (st, v, att))
            ok = False
    print("%s regole nft e giudice della pagina" % ("⭐" if ok else "⛔"))
    return 0 if ok else 1


# ─────────────────────────────────────────────────────────────────────────────
def server_pronto(o):
    """Il server nostro acceso e con gli orologi PREDEFINITI; se no lo accende."""
    inatt, abb, riga = G7.orologi_in_vigore(o.scatola)
    c, t = G7.dentro(o.scatola, "systemctl is-active rete15-g7", 30)
    if (t or "").strip() == "active" and inatt == 1800 and abb == 3600:
        return "server nostro gia' acceso, orologi predefiniti"
    ok, t = G7.server("accendi", o.scatola)
    if not ok:
        raise S.Bloccata("il server nostro non si accende: %s" % t[-300:])
    return t.splitlines()[0] if t else "acceso"


def sano_8511(o):
    """⛔ Il server di tutti (851x) deve restare quello di prima: pid e attivo."""
    c, t = G7.dentro(o.scatola, "systemctl is-active rete11-server; "
                     "systemctl show -p MainPID --value rete11-server", 30)
    return " ".join((t or "").split())


def clic_tela(s):
    """Un clic al centro della tela: e' il gesto dell'utente che sblocca
    l'audio del browser (autoplay) — senza, l'AudioContext resta sospeso."""
    st = s.stato()
    x, y = s.pr.centro(st, 0.5, 0.5)
    s.g.clic(x, y)
    time.sleep(0.5)
    return x, y


def entra_con_orecchio(s):
    ok, m = s.pr.apri()
    if not ok:
        return False, "la pagina non si apre: " + m
    G7.orecchio(s.g)
    ok, m = s.entra(apri=False)
    return ok, m


def rientra(s, tetto):
    """Il rientro «a mano»: dal modulo se la pagina l'ha rimesso in vista,
    altrimenti ricaricando (quel che farebbe chi guarda un desktop fermo).
    Torna (ok, come, esito)."""
    st = G7.pagina(s.g)
    come = "dal modulo tornato in vista"
    if not (st.get("modulo_visibile") and not st.get("vestita")):
        come = "ricaricando la pagina (il modulo non c'era)"
        ok, m = s.pr.apri()
        if not ok:
            return False, come, "la pagina non si riapre: " + m
    G7.orecchio(s.g)
    vecchio = s.o.tetto_s
    s.o.tetto_s = tetto
    try:
        e, m, st2 = s.pr.entra(s.parola)
        # ⚠ `[M]` 24 set 2026, server con carico ~50: il ciclo del server resta
        #   indietro fino a 13 s e il CIAO scade (0x0D «tempo scaduto durante la
        #   stretta di mano»).  Chi e' davanti riprova: si riprova UNA volta, e
        #   lo si scrive.
        if e != S.VERDE and "stretta di mano" in (m or ""):
            come += " (riprovato una volta dopo «%s»)" % m[:60]
            ok, m0 = s.pr.apri()
            G7.orecchio(s.g)
            e, m, st2 = s.pr.entra(s.parola)
    finally:
        s.o.tetto_s = vecchio
    if e != S.VERDE:
        return False, come, m
    e2, m2, _ = s.pr.primo_fotogramma()
    e2, m2 = S.C20V.desktop_scuro_ma_vivo(e2, m2, _)
    return e2 == S.VERDE, come, "%s · %s" % (m, m2)


def caduta(s, o, reg, lm, osserva_s, togli=True, durante=None):
    """La linea muore per `o.caduta_s`; `durante()` si chiama a meta'.
    Torna un dizionario coi fatti visti."""
    f = {"linea_morta": None, "detto": None, "detto_dopo_s": None, "scartati": 0}
    segno = reg.righe()
    lm.metti()
    t0 = time.time()
    try:
        chiamato = False
        while time.time() - t0 < o.caduta_s:
            if durante and not chiamato and time.time() - t0 > o.caduta_s / 3:
                durante()
                chiamato = True
            st = G7.pagina(s.g)
            if f["detto"] is None and G7.la_pagina_lo_dice(st):
                f["detto"], f["detto_dopo_s"] = st, time.time() - t0
            time.sleep(2)
        f["scartati"] = lm.contati()
        forma, riga, _ = reg.aspetta(segno, ["linea-morta"], s.chi, tetto=2)
        f["linea_morta"] = riga
    finally:
        if togli:
            f["tolta"] = lm.togli()
    if not togli:
        return f
    # la linea e' tornata: chi e' davanti muove il mouse e guarda
    t1 = time.time()
    mosso = 0
    while time.time() - t1 < osserva_s and f["detto"] is None:
        try:
            st0 = s.stato()
            x, y = s.pr.centro(st0, 0.3 + 0.1 * (mosso % 4), 0.5)
            s.g.muovi(x, y)
            mosso += 1
        except Exception:                        # noqa: BLE001
            pass
        st = G7.pagina(s.g)
        if G7.la_pagina_lo_dice(st):
            f["detto"], f["detto_dopo_s"] = st, time.time() - t0
            break
        time.sleep(3)
    f["ultima_pagina"] = G7.pagina(s.g)
    f["mossi"] = mosso
    if f["linea_morta"] is None:
        _f, riga, _ = reg.aspetta(segno, ["linea-morta"], s.chi, tetto=2)
        f["linea_morta"] = riga
    f["segno"] = segno
    return f


def corpo(o, E):
    if not o.porta:
        o.porta = G7.PORTE_G7[o.scatola]
        o.url = "https://%s:%d/" % (o.host, o.porta)
    if o.porta != G7.PORTE_G7[o.scatola]:
        raise S.Bloccata("la porta %d non e' quella del server nostro (%d)"
                         % (o.porta, G7.PORTE_G7[o.scatola]))
    print("   %s" % server_pronto(o), flush=True)
    prima_8511 = sano_8511(o)
    reg = G7.Registro(o.scatola)
    lm = G7.LineaMorta(o.porta)
    lm.togli()
    ev_srv = []
    try:
        with S.Sessione(o, "019", E) as s:
            segno0 = reg.righe()
            ok, m = entra_con_orecchio(s)
            if not ok:
                raise S.Bloccata("non si entra nemmeno a linea sana: " + m)
            print("   entrato: %s" % m, flush=True)
            clic_tela(s)
            pid_scena, t = G7.lancia_scena(s)
            print("   %s" % t, flush=True)
            if not pid_scena:
                raise S.Bloccata("la scena non parte: " + t)
            c, t = G7.lancia_tono(s)
            vista, t = G7.aspetta_scena(s, S)
            if not vista:
                raise S.Bloccata("prima della caduta: " + t)
            time.sleep(3)
            ps0 = G7.processi_inquilino(o.scatola, s.chi)
            pid_tono = [p for p, n in ps0.items() if n.startswith("pw-play")]
            rms0, d0 = G7.ascolta(s.g, 3)
            mossa0, dm0, ev0 = G7.la_scena_si_muove(s, "prima")
            print("   prima: scena %s (%s) · suono RMS %s %s · %d processi"
                  % (mossa0, dm0, rms0, d0, len(ps0)), flush=True)

            # ═══ LA CADUTA SANA ═══════════════════════════════════════════
            f = caduta(s, o, reg, lm, o.osserva_s)
            print("   caduta: scartati %d pacchetti · linea-morta: %s · detto: %s"
                  % (f["scartati"], bool(f["linea_morta"]),
                     ("dopo %.0f s" % f["detto_dopo_s"]) if f["detto"] else "NO"), flush=True)
            if f["scartati"] == 0:
                raise S.Bloccata("la regola nft non ha scartato niente: la linea non e' morta")
            ok_r, come, mr = rientra(s, TETTO_RIENTRO_S)
            print("   rientro %s: %s — %s" % (come, ok_r, mr[:200]), flush=True)
            if ok_r:
                clic_tela(s)
            time.sleep(4)
            ps1 = G7.processi_inquilino(o.scatola, s.chi)
            mossa1, dm1, ev1 = G7.la_scena_si_muove(s, "dopo")
            rms1, d1 = G7.ascolta(s.g, 3)
            ev_srv.append(s.salva_testo("server-f019-sana.txt", reg.da(segno0, s.chi)))
            ev_pag = s.salva_testo("pagina-dopo-caduta.txt", "\n".join(
                "%s: %s" % (k, v) for k, v in (f.get("ultima_pagina") or {}).items()))
            # ⚠ Il pid di pw-play cambia a ogni giro del ciclo (un file di 5 s):
            #   lo stato della sessione si giudica sul pid della scena.
            stessi = pid_scena in ps1
            ripresa = "ripresa" in mr
            ev = ev0 + ev1 + ev_srv + [ev_pag, s.salva_console()]

            # F-019
            osservato = ("linea-morta dal server: %s · la pagina: %s · rientro %s: %s · "
                         "la pagina scrive «sessione ripresa»: %s (⚠ rcp.c manda sempre "
                         "1=NUOVA) · programmi di prima vivi: %s"
                         % ("si'" if f["linea_morta"] else "NO",
                            ("lo dice dopo %.0f s: «%s»" % (f["detto_dopo_s"],
                                                           (f["detto"].get("esito") or "")[:100]))
                            if f["detto"] else
                            ("NON lo dice: dopo %d s dal ritorno della linea (e %d movimenti del "
                             "mouse) la pagina e' ancora vestita da desktop, congelata, esito "
                             "«%s»" % (o.osserva_s, f.get("mossi", 0),
                                      (f["ultima_pagina"].get("esito") or "")[:80])),
                            come, "riuscito" if ok_r else "FALLITO", ripresa, stessi))
            atteso = ("linea-morta nel registro; la pagina lo dice (frase o modulo) entro "
                      "%d s dal ritorno; si rientra a mano; «sessione ripresa» coi programmi "
                      "di prima" % o.osserva_s)
            if not f["linea_morta"]:
                E.metti("F-019", S.FAIL, "il server non ha dichiarato la linea morta in %d s"
                        % o.caduta_s, atteso=atteso, osservato=osservato, evidenze=ev)
            elif not ok_r or not stessi:
                E.metti("F-019", S.FAIL, "dopo la caduta la sessione non si ritrova: " + osservato,
                        atteso=atteso, osservato=osservato, evidenze=ev)
            elif not f["detto"]:
                E.metti("F-019", S.FAIL, "il filo cade e la pagina NON lo dice: desktop congelato "
                        "senza una parola (si rientra solo ricaricando di propria iniziativa)",
                        atteso=atteso, osservato=osservato, evidenze=ev)
            else:
                E.metti("F-019", S.PASS, osservato, atteso=atteso, osservato=osservato,
                        evidenze=ev)

            # P-B
            atteso_b = "dopo il rientro la scena si muove nelle foto, stesso processo di prima"
            if not ok_r:
                E.metti("P-B", S.FAIL, "non si rientra: " + mr[:200], atteso=atteso_b,
                        osservato=mr[:200], evidenze=ev)
            elif mossa1 is None:
                E.metti("P-B", S.BLOCKED, "foto non giudicabili: " + dm1, evidenze=ev)
            elif mossa1 and pid_scena in ps1:
                E.metti("P-B", S.PASS, "scena viva dopo il rientro (%s), pid %d" % (dm1, pid_scena),
                        atteso=atteso_b, osservato=dm1, evidenze=ev)
            else:
                E.metti("P-B", S.FAIL, "dopo il rientro la scena e' ferma o sparita (%s, pid vivo %s)"
                        % (dm1, pid_scena in ps1), atteso=atteso_b, osservato=dm1, evidenze=ev)

            # P-D
            atteso_d = "dopo il rientro foto in movimento E suono suonato non silenzio (RMS > %.2f)" \
                % G7.SOGLIA_RMS
            if rms0 is None or rms0 < G7.SOGLIA_RMS:
                E.metti("P-D", S.BLOCKED, "il suono non arrivava nemmeno PRIMA della caduta "
                        "(RMS %s, %s): non ho un «prima» da ritrovare" % (rms0, d0), evidenze=ev)
            elif not ok_r:
                E.metti("P-D", S.FAIL, "non si rientra: " + mr[:200], atteso=atteso_d, evidenze=ev)
            elif mossa1 and rms1 is not None and rms1 >= G7.SOGLIA_RMS:
                E.metti("P-D", S.PASS, "dopo il rientro video vivo (%s) e suono RMS %.3f (prima %.3f)"
                        % (dm1, rms1, rms0), atteso=atteso_d,
                        osservato="RMS %.3f · %s" % (rms1, d1), evidenze=ev)
            else:
                E.metti("P-D", S.FAIL, "dopo il rientro: video %s (%s), suono RMS %s (%s)"
                        % (mossa1, dm1, rms1, d1), atteso=atteso_d, evidenze=ev)

            if not o.guasto:
                return
            # ═══ IL GUASTO: lo stato si perde E la linea resta morta ═════
            if not ok_r:
                E.guasto("F-019", None, "la passata sana non e' rientrata: niente da guastare")
                E.guasto("P-B", None, "idem")
                E.guasto("P-D", None, "idem")
                return
            vittime = [pid_scena] + pid_tono

            def uccidi():
                G7.dentro(o.scatola, "pkill -KILL -u %s -f 'pw-play|weston-simple-egl'; "
                          "kill -KILL %s 2>/dev/null; true"
                          % (s.chi, " ".join(str(p) for p in vittime)), 30)
            f2 = caduta(s, o, reg, lm, 0, togli=False, durante=uccidi)
            try:
                ok_g, come_g, mg = rientra(s, 30)          # linea ANCORA morta
            finally:
                lm.togli()
            E.guasto("F-019", not ok_g, "rientro con la linea ancora morta ⇒ %s (%s)"
                     % ("NON si rientra: " + mg[:120] if not ok_g else "RIENTRATO?!", come_g))
            ok_r2, come2, mr2 = rientra(s, TETTO_RIENTRO_S)
            if not ok_r2:
                E.guasto("P-B", None, "dopo il guasto non si rientra piu': " + mr2[:150])
                E.guasto("P-D", None, "idem")
                return
            clic_tela(s)
            time.sleep(4)
            ps2 = G7.processi_inquilino(o.scatola, s.chi)
            mossa2, dm2, _e = G7.la_scena_si_muove(s, "guasto")
            rms2, d2 = G7.ascolta(s.g, 3)
            s.salva_testo("server-f019-guasto.txt", reg.da(f2.get("segno") or segno0, s.chi))
            vivo = pid_scena in ps2
            pb_rosso = not (mossa2 and vivo)
            E.guasto("P-B", pb_rosso if mossa2 is not None else None,
                     "scena uccisa durante la caduta ⇒ il giudice di P-B dice %s (%s, pid vivo %s)"
                     % ("rosso" if pb_rosso else "VERDE", dm2, vivo))
            pd_rosso = not (mossa2 and rms2 is not None and rms2 >= G7.SOGLIA_RMS)
            E.guasto("P-D", pd_rosso, "scena e tono uccisi ⇒ il giudice di P-D dice %s "
                     "(video %s, RMS %s)" % ("rosso" if pd_rosso else "VERDE", mossa2, rms2))
    finally:
        tolta = lm.togli()
        dopo_8511 = sano_8511(o)
        print("   regola nft tolta: %s · server 851x prima «%s» dopo «%s»%s"
              % (tolta, prima_8511, dopo_8511,
                 "" if prima_8511 == dopo_8511 else "  ⛔ CAMBIATO"), flush=True)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra=extra))
