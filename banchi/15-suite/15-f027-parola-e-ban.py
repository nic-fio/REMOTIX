#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f027 — F-027 PAROLA SBAGLIATA · N-1 UTENTE INESISTENTE · F-028 IL BAN

    python3 15-f027-parola-e-ban.py --scatola kde --browser firefox --porte-base 4910 [--guasto]

⛔ SUL SERVER DEL GRUPPO G8 (porta 8621 gnome · 8622 kde · 8623 xfce · 8624 lxqt,
   `15-g8-server.sh`), MAI sull'85xx: tre errori bannano 192.168.0.2 per 12 ore.
   Se il server G8 e' spento la prova lo accende; all'inizio e alla fine lo
   SBLOCCA dal socket di comando.  Due browser dello stesso tipo: A (porte-base)
   e B (porte-base+50).

F-027  (§4.2, src/rcp.c `rcp_verdetto`) utente vero, parola sbagliata ⇒ la pagina
       dice «utente o parola d'ordine non corretti» (MOTIVO 0x07), il server
       scrive «PAM … respinto» e «tentativo fallito da [192.168.0.2]», e NESSUNA
       sessione: nessuna «sessione aperta utente=…», nessun «figlio generato per
       «…»», nessun processo dell'inquilino nella scatola.
N-1    utente che non esiste ⇒ la STESSA frase, parola per parola (§4.2: «utente
       inesistente e parola sbagliata sono la stessa cosa»: niente elenco degli
       utenti), il tentativo si conta, nessuna sessione.
F-028  (§4.2, `DECISIONI.md` §1.9, src/rcp.c `segna_fallito`) —
       · GIA_ATTIVA_REMOTA NON conta: due errori, poi B con la parola GIUSTA
         mentre A e' dentro e vivo ⇒ B riceve «occupato da un altro client»
         (0x0F), e NON scatta il ban (se contasse, sarebbe il terzo);
       · tre errori ⇒ «⛔ BANNATO l'indirizzo [192.168.0.2] per 12 ore»; la
         parola GIUSTA da quell'indirizzo riceve «i tentativi … sono esauriti»
         (0x08); la pagina ricaricata SI CARICA LO STESSO e dice «tentativi
         esauriti» con le ore (data-bannato="si"); il file dei ban del server
         G8 porta [192.168.0.2];
       · ⛔ il server dell'85xx NON e' toccato: la sua pagina dice
         data-bannato="no" e il suo file dei ban non porta l'indirizzo;
       · lo sblocco dal socket di comando («TOLTO») riapre la pagina.
       ⚠ Il mandato diceva «la porta si chiude»: il prodotto (§4.2) NON la chiude,
         serve la pagina e la fa parlare — si giudica quello.

GUASTI (dopo la passata sana, stessa sessione):
  F-028  tre errori veri ⇒ bannato; poi il ban si TOGLIE di nascosto (SBLOCCA)
         prima che il giudice guardi ⇒ il giudice deve dire «non bannato».
  F-027  A si congeda, e la parola «sbagliata» che B manda e' in realta' GIUSTA
         ⇒ B e' ammesso ⇒ il giudice deve dire rosso.
  N-1    l'utente «inesistente» e' quello vero con la parola giusta (mentre B e'
         dentro) ⇒ la frase non e' quella di 0x07 e l'utente esiste ⇒ rosso.
"""
import json
import os
import random
import re
import secrets
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

G = S._carica("g8", os.path.join(S.QUI, "15-g8-comune.py"))
FUNZIONI = ("F-027", "N-1", "F-028")
PER_BROWSER = False
SERVER = "15-g8-server.sh"
RE_FALLITO = re.compile(r"tentativo fallito da \[([0-9.]+)\]: (\d) di (\d)")
IND = "[%s]" % G.INDIRIZZO


# ═══════════════════════════════════════════════════════════════════════════
#  I GIUDICI — puri
# ═══════════════════════════════════════════════════════════════════════════
def conti_falliti(righe):
    return [int(m.group(2)) for r in righe for m in [RE_FALLITO.search(r)]
            if m and m.group(1) == G.INDIRIZZO]


def giudica_rifiuto(ammesso, esito, righe, chi, processi):
    """F-027: (esito, ragione).  `righe` = registro del server G8 dal tentativo,
    `processi` = quanti processi ha l'inquilino nella scatola (None = non so)."""
    if ammesso is True:
        return S.FAIL, "parola sbagliata e la pagina dice AMMESSO («%s»)" % esito
    if ammesso is None:
        return S.BLOCKED, "nessun verdetto dalla pagina: «%s»" % esito
    sess = [r for r in righe if "sessione aperta utente=%s " % chi in r + " "
            or "figlio generato per «%s»" % chi in r]
    if sess:
        return S.FAIL, "rifiutato ma il server ha aperto una sessione: %s" % sess[0][:160]
    if G.FRASE[0x07] not in (esito or ""):
        return S.FAIL, "rifiutato ma la frase non e' chiara: «%s»" % esito
    if not any("respinto" in r and "PAM ha risposto" in r for r in righe):
        return S.FAIL, "la pagina rifiuta ma il server non dice «PAM … respinto»"
    if not conti_falliti(righe):
        return S.FAIL, "il server non conta il tentativo fallito (§4.2)"
    if processi:
        return S.FAIL, "rifiutato ma l'inquilino ha %d processi nella scatola" % processi
    return S.PASS, "«%s» · fallito %s di 3 · nessuna sessione, %s processi" % (
        esito, conti_falliti(righe)[-1], processi)


def giudica_inesistente(ammesso, esito, esito_f027, righe, finto, esiste):
    """N-1: (esito, ragione)."""
    if ammesso is True:
        return S.FAIL, "utente inesistente e la pagina dice AMMESSO"
    if ammesso is None:
        return S.BLOCKED, "nessun verdetto dalla pagina: «%s»" % esito
    if esiste:
        return S.FAIL, "l'utente «%s» esiste: non e' la prova dell'utente inesistente" % finto
    if (esito or "").strip() != (esito_f027 or "").strip():
        return S.FAIL, ("la frase e' diversa da quella della parola sbagliata: «%s» contro "
                        "«%s» (§4.2: sono la stessa cosa)" % (esito, esito_f027))
    if any("sessione aperta utente=%s" % finto in r for r in righe):
        return S.FAIL, "il server ha aperto una sessione per un utente inesistente"
    if not conti_falliti(righe):
        return S.FAIL, "il tentativo con l'utente inesistente non si conta (§4.2)"
    return S.PASS, "«%s», identica alla parola sbagliata · fallito %d di 3" % (
        esito, conti_falliti(righe)[-1])


def giudica_gia_attiva(ammesso, esito, pagina_dopo, righe):
    """F-028, meta' 1: il rifiuto 0x0F non conta come errore."""
    if ammesso is True:
        return S.BLOCKED, "il secondo e' entrato: A non era vivo, non c'e' 0x0F da guardare"
    if ammesso is None or G.FRASE[0x0F] not in (esito or ""):
        return S.BLOCKED, "il rifiuto non e' 0x0F («%s»): non guardo quel che volevo" % esito
    if any("BANNATO l'indirizzo %s" % IND in r for r in righe):
        return S.FAIL, "0x0F dopo due errori ha BANNATO: il rifiuto del secondo conta (§4.2)"
    if pagina_dopo.get("bannato") != "no":
        return S.FAIL, "dopo 0x0F la pagina dice data-bannato=%s" % pagina_dopo.get("bannato")
    return S.PASS, "due errori + 0x0F «%s» ⇒ nessun ban" % esito


def giudica_ban(pagina, file_mio, righe):
    """F-028, meta' 2: dopo tre errori.  (esito, ragione)."""
    if not any("BANNATO l'indirizzo %s" % IND in r for r in righe):
        return S.FAIL, "tre tentativi falliti e il server non dice «BANNATO»"
    if pagina.get("bannato") != "si":
        return S.FAIL, ("la pagina ricaricata non dice il ban (data-bannato=%s, esito «%s»)"
                        % (pagina.get("bannato"), pagina.get("esito")))
    if "tentativi esauriti" not in (pagina.get("avviso") or ""):
        return S.FAIL, "la pagina e' bannata ma l'avviso non lo dice: «%s»" % pagina.get("avviso")
    if pagina.get("ore") not in ("11", "12"):
        return S.FAIL, "l'avviso dice %s ore e %s minuti, non ~12 ore" % (
            pagina.get("ore"), pagina.get("minuti"))
    if IND not in (file_mio or ""):
        return S.FAIL, "il file dei ban del server non porta %s: «%s»" % (IND, file_mio)
    return S.PASS, "bannato: la pagina si carica e dice «tentativi esauriti», %s ore %s min" % (
        pagina.get("ore"), pagina.get("minuti"))


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    ch = "c15027u1"
    fr = G.FRASE[0x07]
    righe = ["PAM ha risposto (pratica 3): respinto", "tentativo fallito da [192.168.0.2]: 1 di 3 dentro i 5 minuti"]
    prova("rifiuto chiaro ⇒ PASS", giudica_rifiuto(False, fr, righe, ch, 0)[0] == S.PASS)
    prova("ammesso ⇒ FAIL", giudica_rifiuto(True, "Ammesso", righe, ch, 0)[0] == S.FAIL)
    prova("sessione aperta ⇒ FAIL", giudica_rifiuto(
        False, fr, righe + ["sessione aperta utente=%s via=x" % ch], ch, 0)[0] == S.FAIL)
    prova("frase diversa ⇒ FAIL", giudica_rifiuto(False, "congedato", righe, ch, 0)[0] == S.FAIL)
    prova("processi ⇒ FAIL", giudica_rifiuto(False, fr, righe, ch, 3)[0] == S.FAIL)
    prova("inesistente, stessa frase ⇒ PASS",
          giudica_inesistente(False, fr, fr, righe, "c15027u9", False)[0] == S.PASS)
    prova("inesistente, frase diversa ⇒ FAIL",
          giudica_inesistente(False, "utente sconosciuto", fr, righe, "c15027u9", False)[0] == S.FAIL)
    prova("inesistente ma esiste ⇒ FAIL",
          giudica_inesistente(False, fr, fr, righe, "c15027u9", True)[0] == S.FAIL)
    g0f = "respinto: il posto di questa sessione risulta " + G.FRASE[0x0F]
    prova("0x0F senza ban ⇒ PASS", giudica_gia_attiva(False, g0f, {"bannato": "no"}, righe)[0] == S.PASS)
    prova("0x0F con ban ⇒ FAIL", giudica_gia_attiva(
        False, g0f, {"bannato": "si"}, righe + ["⛔ BANNATO l'indirizzo [192.168.0.2] per 12 ore"])[0] == S.FAIL)
    rb = ["⛔ BANNATO l'indirizzo [192.168.0.2] per 12 ore"]
    pb = {"bannato": "si", "avviso": "tentativi esauriti: … Mancano ancora 12 ore", "ore": "12", "minuti": "0"}
    prova("ban visto ⇒ PASS", giudica_ban(pb, "[192.168.0.2] 1790000000", rb)[0] == S.PASS)
    prova("pagina non bannata ⇒ FAIL", giudica_ban(dict(pb, bannato="no"), "[192.168.0.2] 1", rb)[0] == S.FAIL)
    prova("niente riga BANNATO ⇒ FAIL", giudica_ban(pb, "[192.168.0.2] 1", [])[0] == S.FAIL)
    prova("file senza indirizzo ⇒ FAIL", giudica_ban(pb, "", rb)[0] == S.FAIL)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def processi_di(sc, chi):
    c, t = G.dentro(sc, "pgrep -u %s 2>/dev/null | wc -l; true" % chi, 30)
    try:
        return int(t.split()[-1])
    except (ValueError, IndexError):
        return None


def esiste(sc, chi):
    c, t = G.dentro(sc, "id %s >/dev/null 2>&1 && echo si || echo no" % chi, 30)
    return t.strip().endswith("si")


def manda_senza_ricaricare(s, utente, parola, tetto=30):
    r = s.g.js(S.VERI.JS_ENTRA, utente, parola)
    if r != "mandato":
        return None, {"esito": "modulo non compilato: %s" % r}
    fine = time.time() + tetto
    st = {}
    while time.time() < fine:
        time.sleep(0.5)
        st = s.stato()
        if st.get("esito_classe") == "bene" and (st.get("esito") or "").startswith("Ammesso"):
            return True, st
        if st.get("esito_classe") == "male" and G.FRASE[0x07] not in (st.get("esito") or "") \
                and "Collego" not in (st.get("esito") or ""):
            return False, st
    return (False if st.get("esito_classe") == "male" else None), st


def corpo(o, E):
    srv = G.MioServer(o.scatola)
    if not srv.acceso():
        ok, t = srv.accendi()
        print("   server G8: %s" % t, flush=True)
        if not ok:
            raise S.Bloccata("il server G8 sulla %d non si accende: %s" % (srv.porta, t))
    o.porta = srv.porta
    o.url = "https://%s:%d/" % (o.host, srv.porta)
    print("   ⭐ server G8 %s · sblocco iniziale: %s" % (o.url, srv.sblocca()), flush=True)
    ban85 = srv.file_ban(G.BAN_85XX)
    sbagliata = lambda: "sbagliata-" + secrets.token_hex(4)   # noqa: E731
    ev_testi = {}

    with S.Sessione(o, "027", E) as A:
        chi = A.chi
        ok, m = A.pr.apri()
        if not ok:
            raise S.Bloccata("la pagina del server G8 non si apre: " + m)

        # ── F-027: parola sbagliata ─────────────────────────────────────────
        segno = srv.righe_registro()
        amm, st = G.tenta(A, chi, sbagliata())
        time.sleep(1)
        righe = srv.registro_da(segno)
        esito_f027 = st.get("esito")
        e, r = giudica_rifiuto(amm, esito_f027, righe, chi, processi_di(A.sc, chi))
        ev = [A.salva_testo("f027-server.txt", righe)]
        E.metti("F-027", e, r, atteso="«%s», nessuna sessione, tentativo contato" % G.FRASE[0x07],
                osservato=r, evidenze=[x for x in ev if x])

        # ── N-1: utente inesistente ─────────────────────────────────────────
        finto = "c15027u%d" % random.randint(10000, 99999)
        segno = srv.righe_registro()
        amm, st = G.tenta(A, finto, sbagliata())
        time.sleep(1)
        righe = srv.registro_da(segno)
        e, r = giudica_inesistente(amm, st.get("esito"), esito_f027, righe, finto,
                                   esiste(A.sc, finto))
        ev = [A.salva_testo("n1-server.txt", righe)]
        E.metti("N-1", e, r, atteso="la stessa frase della parola sbagliata, contato, niente sessione",
                osservato=r, evidenze=ev)

        # ── A entra (il conto torna a zero) ─────────────────────────────────
        segno = srv.righe_registro()
        ok, m = A.entra()
        if not ok:
            raise S.Bloccata("l'inquilino con la parola GIUSTA non entra nel server G8: " + m)
        azzera = [x for x in srv.registro_da(segno) if "il conto dei falliti torna a zero" in x]
        print("   ⭐ A dentro: %s · %s" % (m[:80], azzera[0][-90:] if azzera else "(nessun azzeramento scritto)"),
              flush=True)

        with S.Sessione(G.o_per(o, 1), "027", E, inquilino=False, chi=chi,
                        parola=A.parola) as B:
            # ── F-028 (1): GIA_ATTIVA_REMOTA non conta ──────────────────────
            segno = srv.righe_registro()
            for _ in range(2):
                G.tenta(B, chi, sbagliata())
            G.muovi_un_po(A)
            amm, st = G.tenta(B, chi, A.parola)
            time.sleep(1.5)
            pagina = G.carica(B.g, o.url)
            righe = srv.registro_da(segno)
            ev_testi["f028-gia-attiva-server.txt"] = righe
            e1, r1 = giudica_gia_attiva(amm, st.get("esito"), pagina, righe)
            print("   F-028 (0x0F non conta): %s — %s" % (e1, r1), flush=True)
            if pagina.get("bannato") == "si":
                print("   ⚠ bannato gia' qui: sblocco per poter guardare il resto: %s"
                      % srv.sblocca(), flush=True)

            # ── F-028 (2): tre errori ⇒ ban ─────────────────────────────────
            segno = srv.righe_registro()
            for _ in range(3):
                amm, st = G.tenta(B, chi, sbagliata())
            quarta_amm, quarta = manda_senza_ricaricare(B, chi, A.parola)
            time.sleep(1)
            pagina = G.carica(B.g, o.url)
            righe = srv.registro_da(segno)
            ev_testi["f028-ban-server.txt"] = righe
            file_mio = srv.file_ban()
            e2, r2 = giudica_ban(pagina, file_mio, righe)
            # il quarto tentativo, con la parola GIUSTA
            if e2 == S.PASS and (quarta_amm is not False
                                 or G.FRASE[0x08] not in (quarta.get("esito") or "")):
                e2, r2 = S.FAIL, ("bannato, ma la parola GIUSTA da quell'indirizzo riceve: "
                                  "ammesso=%s «%s» (atteso 0x08)" % (quarta_amm, quarta.get("esito")))
            # ⛔ l'85xx non toccato
            p85 = G.carica(B.g, "https://%s:%d/" % (o.host, S.PORTE[o.scatola]))
            ban85_dopo = srv.file_ban(G.BAN_85XX)
            if e2 == S.PASS and (p85.get("bannato") != "no" or IND in ban85_dopo):
                e2, r2 = S.FAIL, ("il ban del server G8 ha toccato l'%d: data-bannato=%s, file «%s»"
                                  % (S.PORTE[o.scatola], p85.get("bannato"), ban85_dopo))
            vivo_a = G.leggi_pagina(A.g)
            # lo sblocco
            sbl = srv.sblocca()
            pagina2 = G.carica(B.g, o.url)
            if e2 == S.PASS and (not sbl.startswith("TOLTO") or pagina2.get("bannato") != "no"):
                e2, r2 = S.FAIL, "lo sblocco dal socket non riapre: «%s», data-bannato=%s" % (
                    sbl, pagina2.get("bannato"))
            conti = conti_falliti(righe)
            oss = ("%s · falliti contati %s · quarto (parola giusta): «%s» · %d data-bannato=%s, "
                   "file «%s» (prima «%s») · A durante il ban: sessione=%s «%s» · sblocco «%s»"
                   % (r2, conti, (quarta.get("esito") or "")[:90], S.PORTE[o.scatola],
                      p85.get("bannato"), ban85_dopo, ban85, vivo_a.get("sessione"),
                      (vivo_a.get("esito") or "")[:40], sbl))
            if e1 == S.FAIL or e2 == S.FAIL:
                ef = S.FAIL
            elif e1 == S.BLOCKED or e2 == S.BLOCKED:
                ef = S.BLOCKED
            else:
                ef = S.PASS
            ev = [B.salva_testo(n, t) for n, t in ev_testi.items()]
            ev.append(B.salva_testo("f028-pagine.json", json.dumps(
                {"bannata": pagina, "quarto": quarta, "85xx": p85, "sbloccata": pagina2},
                ensure_ascii=False, indent=1)))
            E.metti("F-028", ef, "0x0F non conta: %s · ban: %s" % (r1, r2),
                    atteso="0x0F non conta; 3 errori ⇒ ban di 12 h detto dalla pagina, 0x08 sulla "
                           "parola giusta, 85xx intatto, lo sblocco riapre",
                    osservato=oss, evidenze=ev)

            if o.guasto:
                # F-028: il ban si toglie di nascosto prima che il giudice guardi
                segno = srv.righe_registro()
                for _ in range(3):
                    G.tenta(B, chi, sbagliata())
                righe = srv.registro_da(segno)
                vero = any("BANNATO l'indirizzo %s" % IND in x for x in righe)
                srv.sblocca()                                   # ⛔ il guasto
                pagina = G.carica(B.g, o.url)
                eg, rg = giudica_ban(pagina, srv.file_ban(), righe)
                E.guasto("F-028", (eg != S.PASS) if vero else None,
                         "ban vero (%s), tolto prima del giudizio ⇒ il giudice dice %s: %s"
                         % (vero, eg, rg))
                srv.sblocca()
                # F-027: la parola «sbagliata» e' quella giusta (A si congeda prima)
                A.g.vai("about:blank")
                time.sleep(3)
                segno = srv.righe_registro()
                amm, st = G.tenta(B, chi, B.parola)
                time.sleep(1)
                righe = srv.registro_da(segno)
                eg, rg = giudica_rifiuto(amm, st.get("esito"), righe, chi, processi_di(A.sc, chi))
                E.guasto("F-027", eg == S.FAIL if amm is not None else None,
                         "parola giusta spacciata per sbagliata ⇒ il giudice dice %s: %s" % (eg, rg))
                # N-1: l'«inesistente» e' l'utente vero con la parola giusta
                segno = srv.righe_registro()
                amm, st = G.tenta(A, chi, A.parola)
                time.sleep(1)
                righe = srv.registro_da(segno)
                eg, rg = giudica_inesistente(amm, st.get("esito"), esito_f027, righe, chi,
                                             esiste(A.sc, chi))
                E.guasto("N-1", eg == S.FAIL if amm is not None else None,
                         "utente vero al posto dell'inesistente ⇒ il giudice dice %s: %s" % (eg, rg))
    print("   sblocco finale: %s" % srv.sblocca(), flush=True)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
