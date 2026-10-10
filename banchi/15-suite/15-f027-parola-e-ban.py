#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f027 — F-027 WRONG PASSWORD · N-1 NONEXISTENT USER · F-028 THE BAN

    python3 15-f027-parola-e-ban.py --scatola kde --browser firefox --porte-base 4910 [--guasto]

⛔ ON THE G8 GROUP'S SERVER (port 8621 gnome · 8622 kde · 8623 xfce · 8624 lxqt,
   `15-g8-server.sh`), NEVER on the 85xx: three errors ban 192.168.0.2 for 12 hours.
   If the G8 server is off the test starts it; at the beginning and at the end it
   UNBLOCKS it from the command socket.  Two browsers of the same type: A (porte-base)
   and B (porte-base+50).

F-027  (§4.2, src/rcp.c `rcp_verdetto`) real user, wrong password ⇒ the page
       says «incorrect username or password» (MOTIVO 0x07), the server
       writes «PAM … refused» and «failed attempt from [192.168.0.2]», and NO
       session: no «session open utente=…», no «child spawned for
       «…»», no process of the tenant in the box.
N-1    a user who does not exist ⇒ the SAME sentence, word for word (§4.2: «nonexistent
       user and wrong password are the same thing»: no list of the
       users), the attempt is counted, no session.
F-028  (§4.2, `DECISIONI.md` §1.9, src/rcp.c `segna_fallito`) —
       · GIA_ATTIVA_REMOTA does NOT count: two errors, then B with the RIGHT password
         while A is in and alive ⇒ B receives «taken by another client»
         (0x0F), and the ban does NOT fire (if it counted, it would be the third);
       · three errors ⇒ «⛔ BANNED address [192.168.0.2] for 12 hours»; the
         RIGHT password from that address receives «the attempts … are used up»
         (0x08); the reloaded page LOADS ANYWAY and says «attempts
         exhausted» with the hours (data-bannato="si"); the ban file of the
         G8 server carries [192.168.0.2];
       · ⛔ the 85xx server is NOT touched: its page says
         data-bannato="no" and its ban file does not carry the address;
       · the unblock from the command socket («TOLTO») reopens the page.
       ⚠ The mandate said «the port closes»: the product (§4.2) does NOT close it,
         it serves the page and makes it speak — that is what is judged.

FAULTS (after the healthy pass, same session):
  F-028  three real errors ⇒ banned; then the ban is REMOVED secretly (SBLOCCA)
         before the judge looks ⇒ the judge must say «not banned».
  F-027  A says farewell, and the «wrong» password that B sends is actually RIGHT
         ⇒ B is admitted ⇒ the judge must say red.
  N-1    the «nonexistent» user is the real one with the right password (while B is
         in) ⇒ the sentence is not that of 0x07 and the user exists ⇒ red.
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
RE_FALLITO = re.compile(r"failed attempt from \[([0-9.]+)\]: (\d) of (\d)")
IND = "[%s]" % G.INDIRIZZO


# ═══════════════════════════════════════════════════════════════════════════
#  THE JUDGES — pure
# ═══════════════════════════════════════════════════════════════════════════
def conti_falliti(righe):
    return [int(m.group(2)) for r in righe for m in [RE_FALLITO.search(r)]
            if m and m.group(1) == G.INDIRIZZO]


def giudica_rifiuto(ammesso, esito, righe, chi, processi):
    """F-027: (outcome, reason).  `righe` = G8 server log from the attempt,
    `processi` = how many processes the tenant has in the box (None = don't know)."""
    if ammesso is True:
        return S.FAIL, "wrong password and the page says ADMITTED («%s»)" % esito
    if ammesso is None:
        return S.BLOCKED, "no verdict from the page: «%s»" % esito
    sess = [r for r in righe if "session open utente=%s " % chi in r + " "
            or "child spawned for «%s»" % chi in r]
    if sess:
        return S.FAIL, "refused but the server opened a session: %s" % sess[0][:160]
    if G.FRASE[0x07] not in (esito or ""):
        return S.FAIL, "refused but the sentence is not clear: «%s»" % esito
    if not any("refused" in r and "PAM answered" in r for r in righe):
        return S.FAIL, "the page refuses but the server does not say «PAM … refused»"
    if not conti_falliti(righe):
        return S.FAIL, "the server does not count the failed attempt (§4.2)"
    if processi:
        return S.FAIL, "refused but the tenant has %d processes in the box" % processi
    return S.PASS, "«%s» · failed %s of 3 · no session, %s processes" % (
        esito, conti_falliti(righe)[-1], processi)


def giudica_inesistente(ammesso, esito, esito_f027, righe, finto, esiste):
    """N-1: (esito, ragione)."""
    if ammesso is True:
        return S.FAIL, "nonexistent user and the page says ADMITTED"
    if ammesso is None:
        return S.BLOCKED, "no verdict from the page: «%s»" % esito
    if esiste:
        return S.FAIL, "the user «%s» exists: it is not the nonexistent-user test" % finto
    if (esito or "").strip() != (esito_f027 or "").strip():
        return S.FAIL, ("the sentence differs from the wrong-password one: «%s» against "
                        "«%s» (§4.2: they are the same thing)" % (esito, esito_f027))
    if any("session open utente=%s" % finto in r for r in righe):
        return S.FAIL, "the server opened a session for a nonexistent user"
    if not conti_falliti(righe):
        return S.FAIL, "the attempt with the nonexistent user is not counted (§4.2)"
    return S.PASS, "«%s», identical to the wrong password · failed %d of 3" % (
        esito, conti_falliti(righe)[-1])


def giudica_gia_attiva(ammesso, esito, pagina_dopo, righe):
    """F-028, half 1: the 0x0F refusal does not count as an error."""
    if ammesso is True:
        return S.BLOCKED, "the second got in: A was not alive, there is no 0x0F to look at"
    if ammesso is None or G.FRASE[0x0F] not in (esito or ""):
        return S.BLOCKED, "the refusal is not 0x0F («%s»): I am not looking at what I wanted" % esito
    if any("BANNED address %s" % IND in r for r in righe):
        return S.FAIL, "0x0F after two errors BANNED: the second one's refusal counts (§4.2)"
    if pagina_dopo.get("bannato") != "no":
        return S.FAIL, "after 0x0F the page says data-bannato=%s" % pagina_dopo.get("bannato")
    return S.PASS, "two errors + 0x0F «%s» ⇒ no ban" % esito


def giudica_ban(pagina, file_mio, righe):
    """F-028, half 2: after three errors.  (outcome, reason)."""
    if not any("BANNED address %s" % IND in r for r in righe):
        return S.FAIL, "three failed attempts and the server does not say «BANNED»"
    if pagina.get("bannato") != "si":
        return S.FAIL, ("the reloaded page does not say the ban (data-bannato=%s, outcome «%s»)"
                        % (pagina.get("bannato"), pagina.get("esito")))
    if "attempts exhausted" not in (pagina.get("avviso") or ""):
        return S.FAIL, "the page is banned but the notice does not say so: «%s»" % pagina.get("avviso")
    if pagina.get("ore") not in ("11", "12"):
        return S.FAIL, "the notice says %s hours and %s minutes, not ~12 hours" % (
            pagina.get("ore"), pagina.get("minuti"))
    if IND not in (file_mio or ""):
        return S.FAIL, "the server's ban file does not carry %s: «%s»" % (IND, file_mio)
    return S.PASS, "banned: the page loads and says «attempts exhausted», %s hours %s min" % (
        pagina.get("ore"), pagina.get("minuti"))


def certifica():
    ok = True

    def prova(cosa, vero):
        nonlocal ok
        ok &= bool(vero)
        print("%s %s" % ("⭐" if vero else "⛔", cosa))
    ch = "c15027u1"
    fr = G.FRASE[0x07]
    righe = ["PAM answered (request 3): refused", "failed attempt from [192.168.0.2]: 1 of 3 within the 5 minutes"]
    prova("clear refusal ⇒ PASS", giudica_rifiuto(False, fr, righe, ch, 0)[0] == S.PASS)
    prova("admitted ⇒ FAIL", giudica_rifiuto(True, "Admitted", righe, ch, 0)[0] == S.FAIL)
    prova("session open ⇒ FAIL", giudica_rifiuto(
        False, fr, righe + ["session open utente=%s via=x" % ch], ch, 0)[0] == S.FAIL)
    prova("different sentence ⇒ FAIL", giudica_rifiuto(False, "sent away", righe, ch, 0)[0] == S.FAIL)
    prova("processes ⇒ FAIL", giudica_rifiuto(False, fr, righe, ch, 3)[0] == S.FAIL)
    prova("nonexistent, same sentence ⇒ PASS",
          giudica_inesistente(False, fr, fr, righe, "c15027u9", False)[0] == S.PASS)
    prova("nonexistent, different sentence ⇒ FAIL",
          giudica_inesistente(False, "unknown user", fr, righe, "c15027u9", False)[0] == S.FAIL)
    prova("nonexistent but exists ⇒ FAIL",
          giudica_inesistente(False, fr, fr, righe, "c15027u9", True)[0] == S.FAIL)
    g0f = "refused: this session's slot shows as " + G.FRASE[0x0F]
    prova("0x0F without ban ⇒ PASS", giudica_gia_attiva(False, g0f, {"bannato": "no"}, righe)[0] == S.PASS)
    prova("0x0F with ban ⇒ FAIL", giudica_gia_attiva(
        False, g0f, {"bannato": "si"}, righe + ["⛔ BANNED address [192.168.0.2] for 12 hours"])[0] == S.FAIL)
    rb = ["⛔ BANNED address [192.168.0.2] for 12 hours"]
    pb = {"bannato": "si", "avviso": "attempts exhausted: … There are still 12 hours", "ore": "12", "minuti": "0"}
    prova("ban seen ⇒ PASS", giudica_ban(pb, "[192.168.0.2] 1790000000", rb)[0] == S.PASS)
    prova("page not banned ⇒ FAIL", giudica_ban(dict(pb, bannato="no"), "[192.168.0.2] 1", rb)[0] == S.FAIL)
    prova("no BANNED line ⇒ FAIL", giudica_ban(pb, "[192.168.0.2] 1", [])[0] == S.FAIL)
    prova("file without address ⇒ FAIL", giudica_ban(pb, "", rb)[0] == S.FAIL)
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
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
        return None, {"esito": "form not filled in: %s" % r}
    fine = time.time() + tetto
    st = {}
    while time.time() < fine:
        time.sleep(0.5)
        st = s.stato()
        if st.get("esito_classe") == "bene" and (st.get("esito") or "").startswith("Admitted"):
            return True, st
        if st.get("esito_classe") == "male" and G.FRASE[0x07] not in (st.get("esito") or "") \
                and "Collego" not in (st.get("esito") or ""):
            return False, st
    return (False if st.get("esito_classe") == "male" else None), st


def corpo(o, E):
    srv = G.MioServer(o.scatola)
    if not srv.acceso():
        ok, t = srv.accendi()
        print("   G8 server: %s" % t, flush=True)
        if not ok:
            raise S.Bloccata("the G8 server on %d does not start: %s" % (srv.porta, t))
    o.porta = srv.porta
    o.url = "https://%s:%d/" % (o.host, srv.porta)
    print("   ⭐ G8 server %s · initial unblock: %s" % (o.url, srv.sblocca()), flush=True)
    ban85 = srv.file_ban(G.BAN_85XX)
    sbagliata = lambda: "wrong-" + secrets.token_hex(4)   # noqa: E731
    ev_testi = {}

    with S.Sessione(o, "027", E) as A:
        chi = A.chi
        ok, m = A.pr.apri()
        if not ok:
            raise S.Bloccata("the G8 server's page does not open: " + m)

        # ── F-027: wrong password ───────────────────────────────────────────
        segno = srv.righe_registro()
        amm, st = G.tenta(A, chi, sbagliata())
        time.sleep(1)
        righe = srv.registro_da(segno)
        esito_f027 = st.get("esito")
        e, r = giudica_rifiuto(amm, esito_f027, righe, chi, processi_di(A.sc, chi))
        ev = [A.salva_testo("f027-server.txt", righe)]
        E.metti("F-027", e, r, atteso="«%s», no session, attempt counted" % G.FRASE[0x07],
                osservato=r, evidenze=[x for x in ev if x])

        # ── N-1: nonexistent user ───────────────────────────────────────────
        finto = "c15027u%d" % random.randint(10000, 99999)
        segno = srv.righe_registro()
        amm, st = G.tenta(A, finto, sbagliata())
        time.sleep(1)
        righe = srv.registro_da(segno)
        e, r = giudica_inesistente(amm, st.get("esito"), esito_f027, righe, finto,
                                   esiste(A.sc, finto))
        ev = [A.salva_testo("n1-server.txt", righe)]
        E.metti("N-1", e, r, atteso="the same sentence as the wrong password, counted, no session",
                osservato=r, evidenze=ev)

        # ── A gets in (the count goes back to zero) ─────────────────────────
        segno = srv.righe_registro()
        ok, m = A.entra()
        if not ok:
            raise S.Bloccata("the tenant with the RIGHT password does not get into the G8 server: " + m)
        azzera = [x for x in srv.registro_da(segno) if "the count of failures goes back to zero" in x]
        print("   ⭐ A in: %s · %s" % (m[:80], azzera[0][-90:] if azzera else "(no reset written)"),
              flush=True)

        with S.Sessione(G.o_per(o, 1), "027", E, inquilino=False, chi=chi,
                        parola=A.parola) as B:
            # ── F-028 (1): GIA_ATTIVA_REMOTA does not count ─────────────────
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
            print("   F-028 (0x0F does not count): %s — %s" % (e1, r1), flush=True)
            if pagina.get("bannato") == "si":
                print("   ⚠ banned already here: unblocking to be able to look at the rest: %s"
                      % srv.sblocca(), flush=True)

            # ── F-028 (2): three errors ⇒ ban ───────────────────────────────
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
            # the fourth attempt, with the RIGHT password
            if e2 == S.PASS and (quarta_amm is not False
                                 or G.FRASE[0x08] not in (quarta.get("esito") or "")):
                e2, r2 = S.FAIL, ("banned, but the RIGHT password from that address receives: "
                                  "admitted=%s «%s» (expected 0x08)" % (quarta_amm, quarta.get("esito")))
            # ⛔ the 85xx not touched
            p85 = G.carica(B.g, "https://%s:%d/" % (o.host, S.PORTE[o.scatola]))
            ban85_dopo = srv.file_ban(G.BAN_85XX)
            if e2 == S.PASS and (p85.get("bannato") != "no" or IND in ban85_dopo):
                e2, r2 = S.FAIL, ("the G8 server's ban touched %d: data-bannato=%s, file «%s»"
                                  % (S.PORTE[o.scatola], p85.get("bannato"), ban85_dopo))
            vivo_a = G.leggi_pagina(A.g)
            # the unblock
            sbl = srv.sblocca()
            pagina2 = G.carica(B.g, o.url)
            if e2 == S.PASS and (not sbl.startswith("TOLTO") or pagina2.get("bannato") != "no"):
                e2, r2 = S.FAIL, "the unblock from the socket does not reopen: «%s», data-bannato=%s" % (
                    sbl, pagina2.get("bannato"))
            conti = conti_falliti(righe)
            oss = ("%s · failures counted %s · fourth (right password): «%s» · %d data-bannato=%s, "
                   "file «%s» (before «%s») · A during the ban: sessione=%s «%s» · unblock «%s»"
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
            E.metti("F-028", ef, "0x0F does not count: %s · ban: %s" % (r1, r2),
                    atteso="0x0F does not count; 3 errors ⇒ 12 h ban said by the page, 0x08 on the "
                           "right password, 85xx intact, the unblock reopens",
                    osservato=oss, evidenze=ev)

            if o.guasto:
                # F-028: the ban is removed secretly before the judge looks
                segno = srv.righe_registro()
                for _ in range(3):
                    G.tenta(B, chi, sbagliata())
                righe = srv.registro_da(segno)
                vero = any("BANNED address %s" % IND in x for x in righe)
                srv.sblocca()                                   # ⛔ the fault
                pagina = G.carica(B.g, o.url)
                eg, rg = giudica_ban(pagina, srv.file_ban(), righe)
                E.guasto("F-028", (eg != S.PASS) if vero else None,
                         "real ban (%s), removed before the judgment ⇒ the judge says %s: %s"
                         % (vero, eg, rg))
                srv.sblocca()
                # F-027: the «wrong» password is the right one (A says farewell first)
                A.g.vai("about:blank")
                time.sleep(3)
                segno = srv.righe_registro()
                amm, st = G.tenta(B, chi, B.parola)
                time.sleep(1)
                righe = srv.registro_da(segno)
                eg, rg = giudica_rifiuto(amm, st.get("esito"), righe, chi, processi_di(A.sc, chi))
                E.guasto("F-027", eg == S.FAIL if amm is not None else None,
                         "right password passed off as wrong ⇒ the judge says %s: %s" % (eg, rg))
                # N-1: the «nonexistent» one is the real user with the right password
                segno = srv.righe_registro()
                amm, st = G.tenta(A, chi, A.parola)
                time.sleep(1)
                righe = srv.registro_da(segno)
                eg, rg = giudica_inesistente(amm, st.get("esito"), esito_f027, righe, chi,
                                             esiste(A.sc, chi))
                E.guasto("N-1", eg == S.FAIL if amm is not None else None,
                         "real user instead of the nonexistent one ⇒ the judge says %s: %s" % (eg, rg))
    print("   final unblock: %s" % srv.sblocca(), flush=True)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
