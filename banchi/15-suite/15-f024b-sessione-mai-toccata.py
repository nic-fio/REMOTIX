#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-f024b — F-024b: UNA SESSIONE APERTA E MAI TOCCATA SCADE PER ABBANDONO (§5.3)

    python3 15-f024b-sessione-mai-toccata.py --scatola kde --browser firefox --guasto --porta 8612

⭐ SORVEGLIA IL DIFETTO D-004.  L'orologio dell'abbandono (`--abbandono-s`,
   predefinito 3600) si nutriva SOLO dei cinque gesti d'input: `main.c`
   `input_al_figlio` → `presenza_segna`.  Una sessione in cui nessuno ha mai
   mosso il mouse ne' premuto un tasto non entrava nella tabella della presenza,
   e ⛔ non scadeva mai — contro `SPECIFICHE.md` §5.3, «60 minuti senza input ⇒
   la sessione si chiude».  F-024 (in `15-f022-orologi.py`) non lo vede: fa un
   clic per sbloccare l'audio, e il clic mette l'utente in tabella.
   La cura (bonifica D-004): l'orologio parte alla NASCITA del palco.

⛔ SERVER SUO (`15-g7-server.sh`, porte 8611-8614), come F-022/23/24: l'orologio
   si accorcia dalla riga di comando.  Alla fine il server resta coi PREDEFINITI.

F-024b (server con `--abbandono-s 60`, inattivita' predefinita) si entra col
       browser vero e NON SI FA NIENTE: nessun clic, nessun tasto, nessuna
       scena lanciata ⇒ atteso: entro ABBANDONO_S + MARGINE_S dall'accesso la
       riga «§5.3 — ABBANDONO» dell'inquilino, e poi la sessione SPARISCE: il
       compositore (gnome-shell / kwin_wayland / labwc) non c'e' piu', e dei
       processi dell'inquilino restano solo gli esenti della regola di F-021
       (il figlio `remotix` e il gestore d'utente di systemd coi suoi servizi).
       GUASTO: l'orologio LUNGO (il predefinito, 3600 s), stessa sequenza ⇒
       nessun ABBANDONO nella stessa finestra e la sessione viva ⇒ il giudice
       deve dire rosso.

⛔⛔ «NESSUN GESTO» SI VERIFICA, non si presume.  Il banco non ne fa: l'accesso
     (`Prova.entra`) compila e manda il modulo da JavaScript, il primo
     fotogramma si giudica con fotografie (`fotografa_tela`), e le foto non
     passano dal puntatore.  ⚠ Ma un browser puo' generare da se' eventi di
     puntatore (un `mousemove` sintetico dopo un cambio di impaginazione, col
     puntatore di labwc fermo sopra la finestra), e la pagina li girerebbe al
     server come `PUNTATORE` — cioe' come un gesto, che rinnova l'orologio.
     ⇒ Si CONTANO le righe `input id=` dell'inquilino nel registro del server
       (`rcp.c`, una per ogni messaggio dei cinque tipi del canale di input,
       lo stesso insieme che nutre `presenza_segna`).  Se ce n'e' anche UNA la
       premessa e' caduta e l'esito e' BLOCKED con la riga — non un FAIL del
       prodotto e non un PASS.
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

FUNZIONI = ("F-024b",)
SERVER = "15-g7-server.sh"
PER_BROWSER = False
ABBANDONO_S = 60
MARGINE_S = 30          # il giro dell'orologio + la nascita del palco prima dell'accesso
CHIUSURA_S = 40         # la chiusura della sessione grafica non e' istantanea
FORMA_ABBANDONO = "§5.3 — ABBANDONO"
FORMA_GESTO = "input id="
# ⭐ Il CUORE della sessione: il compositore.  ⚠ Non basta la regola di F-021
#   da sola: su GNOME la Shell e' un servizio del gestore d'utente
#   (`org.gnome.Shell@wayland.service`), cioe' ESENTE per quella regola ⇒ la
#   sessione viva avrebbe zero processi non esenti, e «chiusa» sarebbe vera per
#   forza.  Il compositore c'e' su tutti e quattro (lo stesso elenco di F-016).
CUORI = ("gnome-shell", "kwin_wayland", "labwc")


# ═══════════════════════════════════════════════════════════════════════════
#  I GIUDICI (puri: li prova --certifica)
# ═══════════════════════════════════════════════════════════════════════════
def righe_di(righe, chi):
    """Le righe che nominano l'inquilino.  ⛔ Il nome si cerca intero: un
    inquilino c15024u11 non deve prendere le righe di c15024u111."""
    fuori = []
    for r in righe:
        i = r.find(chi)
        while i >= 0:
            if not r[i + len(chi):i + len(chi) + 1].isdigit():
                fuori.append(r)
                break
            i = r.find(chi, i + 1)
    return fuori


def trova_abbandono(righe, chi):
    for r in righe_di(righe, chi):
        if FORMA_ABBANDONO in r:
            return r
    return None


def gesti(righe, chi):
    return [r for r in righe_di(righe, chi) if FORMA_GESTO in r]


def cuore(ps):
    """«nome pid» dei compositori fra i processi {pid: nome}; None se illeggibili."""
    if ps is None:
        return None
    return ["%s %d" % (n, p) for p, n in sorted(ps.items()) if n in CUORI]


def giudica(d):
    """(esito, ragione) dai campi misurati:
         nati      il compositore dell'inquilino DOPO il primo fotogramma
                   («nome pid», lista; vuota = la sessione non si e' vista nascere)
         gesti     le righe `input id=` dell'inquilino (lista)
         abbandono la riga ABBANDONO, o None
         cuore     il compositore alla fine (lista, o None = illeggibile)
         rimasti   i processi non esenti alla fine (lista, o None = illeggibili)
    ⛔ L'ordine conta: prima la premessa (sessione nata, nessun gesto), poi i
       fatti del prodotto."""
    if not d.get("nati"):
        return S.BLOCKED, ("la sessione non si e' vista nascere (nessun compositore %s "
                           "dell'inquilino dopo il primo fotogramma): non c'e' niente che "
                           "possa scadere" % "/".join(CUORI))
    if d.get("gesti"):
        return S.BLOCKED, ("la premessa e' caduta: al server sono arrivati %d gesti che il "
                           "banco non ha fatto (il primo: %s) — rinnovano l'orologio"
                           % (len(d["gesti"]), d["gesti"][0][:160]))
    if d.get("rimasti") is None or d.get("cuore") is None:
        return S.BLOCKED, "non ho potuto leggere i processi dell'inquilino"
    if not d.get("abbandono"):
        return S.FAIL, ("nessun ABBANDONO entro %d s da un accesso senza nessun gesto "
                        "(compositore alla fine: %s)"
                        % (ABBANDONO_S + MARGINE_S, ", ".join(d["cuore"]) or "sparito"))
    if d["cuore"] or d["rimasti"]:
        return S.FAIL, ("ABBANDONO scritto, ma la sessione non si e' chiusa: compositore "
                        "%s · non esenti %s" % (", ".join(d["cuore"]) or "sparito",
                                                ", ".join(d["rimasti"])[:180] or "nessuno"))
    return S.PASS, ("abbandono senza nessun gesto: compositore sparito, nessun processo "
                    "non esente rimasto")


def certifica():
    ok = True

    def prova(nome, vero):
        nonlocal ok
        if not vero:
            print("⛔ " + nome)
            ok = False

    chi = "c15024u111"
    ab = "21:00 avvio ⭐ §5.3 — ABBANDONO: «%s» non tocca niente da 61000 ms (tetto 60000)"
    gesto = "21:00 rcp [%s] input id=3 (era 2) PUNTATORE 10,10 · istante del client 1 us"
    prova("l'ABBANDONO dell'inquilino si vede", trova_abbandono([ab % chi], chi))
    prova("l'ABBANDONO di un ALTRO inquilino non conta",
          trova_abbandono([ab % "c15024u222"], chi) is None)
    prova("l'ABBANDONO di un nome piu' lungo non conta",
          trova_abbandono([ab % "c15024u1110"], chi) is None)
    prova("un gesto dell'inquilino si conta", len(gesti([gesto % chi], chi)) == 1)
    prova("un gesto di un altro non si conta", not gesti([gesto % "c15024u222"], chi))
    prova("il cuore si legge dai processi",
          cuore({1: "bash", 9: "kwin_wayland"}) == ["kwin_wayland 9"]
          and cuore({1: "bash"}) == [] and cuore(None) is None)
    viva = ["labwc 4242"]
    base = {"nati": viva, "gesti": [], "abbandono": ab % chi, "cuore": [], "rimasti": []}
    prova("abbandono, compositore sparito, niente rimasti ⇒ PASS",
          giudica(base)[0] == S.PASS)
    prova("nessun abbandono ⇒ FAIL (il difetto D-004)",
          giudica(dict(base, abbandono=None, cuore=viva))[0] == S.FAIL)
    prova("nessun abbandono su GNOME (zero non esenti, la Shell e' un servizio) ⇒ FAIL",
          giudica(dict(base, abbandono=None, cuore=["gnome-shell 7"]))[0] == S.FAIL)
    prova("abbandono ma compositore vivo ⇒ FAIL", giudica(dict(base, cuore=viva))[0] == S.FAIL)
    prova("abbandono ma processi non esenti rimasti ⇒ FAIL",
          giudica(dict(base, rimasti=["xfce4-panel|0::/user.slice/x/session-5.scope"]))[0]
          == S.FAIL)
    prova("un gesto non fatto dal banco ⇒ BLOCKED, non PASS ne' FAIL",
          giudica(dict(base, gesti=[gesto % chi]))[0] == S.BLOCKED)
    prova("sessione mai nata ⇒ BLOCKED (sarebbe «chiusa» per forza)",
          giudica(dict(base, nati=[]))[0] == S.BLOCKED)
    prova("processi illeggibili ⇒ BLOCKED",
          giudica(dict(base, rimasti=None))[0] == S.BLOCKED
          and giudica(dict(base, cuore=None))[0] == S.BLOCKED)
    prova("l'orologio corto e l'attesa stanno sotto il predefinito",
          ABBANDONO_S + MARGINE_S + CHIUSURA_S < 3600)
    print("%s giudici di F-024b" % ("⭐" if ok else "⛔"))
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA
# ═══════════════════════════════════════════════════════════════════════════
def _f021():
    sp = _iu.spec_from_file_location("f021", os.path.join(S.QUI, "15-f021-esci.py"))
    m = _iu.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


def accendi(o, *opz):
    ok, t = G7.server("accendi", o.scatola, *opz)
    if not ok:
        raise S.Bloccata("il server nostro non si accende (%s): %s" % (" ".join(opz), t[-300:]))
    inatt, abb, _r = G7.orologi_in_vigore(o.scatola)
    print("   server nostro: inattivita' %s s · abbandono %s s" % (inatt, abb), flush=True)
    return abb


def passata(o, E, reg, corta):
    """corta=True: la passata sana; False: il GUASTO (l'orologio lungo)."""
    F021 = _f021()
    with S.Sessione(o, "024", E) as s:
        segno = reg.righe()
        # ⛔ NESSUN GESTO: niente `clic_tela`, niente scena, niente tasti.  Si
        #    entra e basta (modulo compilato da JavaScript, primo fotogramma
        #    giudicato con fotografie).
        ok, m = s.entra()
        if not ok:
            raise S.Bloccata("non si entra: " + m)
        t_accesso = time.time()
        nati = cuore(G7.processi_inquilino(o.scatola, s.chi)) or []
        # l'attesa: la riga ABBANDONO, entro abbandono + margine dall'accesso
        forma, riga, _d = reg.aspetta(segno, [FORMA_ABBANDONO], s.chi,
                                      tetto=ABBANDONO_S + MARGINE_S, passo=2.0)
        dopo = time.time() - t_accesso
        # la chiusura: il compositore e i processi non esenti devono sparire
        fine = time.time() + (CHIUSURA_S if forma else 0)
        while True:
            cuore_ora = cuore(G7.processi_inquilino(o.scatola, s.chi))
            rimasti = F021.residui(F021.processi(s))
            if (not cuore_ora and not rimasti) or time.time() >= fine:
                break
            time.sleep(2)
        righe = reg.da(segno, s.chi)
        pag = G7.pagina(s.g)
        d = {"nati": nati, "gesti": gesti(righe, s.chi),
             "abbandono": trova_abbandono(righe, s.chi), "cuore": cuore_ora,
             "rimasti": rimasti}
        esito, ragione = giudica(d)
        if not corta:
            if esito == S.BLOCKED:
                E.bloccate(["F-024b"], "passata col guasto: " + ragione, passata="guasto")
                return
            rosso = esito == S.FAIL and not d["abbandono"]
            E.guasto("F-024b", rosso,
                     "orologio LUNGO ⇒ il giudice %s" % (
                         "non vede ABBANDONO in %d s e la sessione e' viva (rosso)"
                         % (ABBANDONO_S + MARGINE_S) if rosso
                         else "dice %s: %s" % (esito, ragione[:150])))
            return
        ev = [s.salva_testo("server-f024b.txt", righe),
              s.salva_testo("processi-f024b.txt",
                            "compositore alla nascita:\n%s\ncompositore alla fine:\n%s\n"
                            "non esenti alla fine:\n%s"
                            % ("\n".join(nati), "\n".join(cuore_ora or ["(nessuno)"]),
                               "\n".join(rimasti or ["(nessuno o illeggibili)"]))),
              s.salva_testo("pagina-f024b.txt",
                            "\n".join("%s: %s" % kv for kv in pag.items()))]
        atteso = ("accesso e poi NESSUN gesto ⇒ entro %d s la riga «§5.3 — ABBANDONO» e la "
                  "sessione si chiude (compositore sparito, non esenti spariti: regola di "
                  "F-021)" % (ABBANDONO_S + MARGINE_S))
        oss = ("riga: %s · a %.0f s dall'accesso · gesti arrivati al server %d · compositore "
               "alla nascita %s, alla fine %s · non esenti alla fine %s · pagina: «%s»"
               % ((riga or "NESSUNA")[:140], dopo, len(d["gesti"]), ", ".join(nati),
                  ", ".join(cuore_ora or []) or "sparito",
                  "?" if rimasti is None else len(rimasti), (pag.get("esito") or "")[:80]))
        E.metti("F-024b", esito, ragione, atteso=atteso, osservato=oss, evidenze=ev)


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
        if accendi(o, "--abbandono-s", str(ABBANDONO_S)) != ABBANDONO_S:
            raise S.Bloccata("l'orologio dell'abbandono non e' quello chiesto (%d s)"
                             % ABBANDONO_S)
        passata(o, E, reg, corta=True)
        if o.guasto:
            try:
                accendi(o)                            # il LUNGO: il predefinito
                passata(o, E, reg, corta=False)
            except S.Bloccata as b:
                E.bloccate(["F-024b"], str(b), passata="guasto")
    finally:
        inatt, abb, _r = G7.orologi_in_vigore(o.scatola)
        if (inatt, abb) != (1800, 3600):
            G7.server("accendi", o.scatola)           # si lascia coi predefiniti
        dopo_8511 = F019.sano_8511(o)
        print("   server 851x prima «%s» dopo «%s»%s" % (
            prima_8511, dopo_8511, "" if prima_8511 == dopo_8511 else "  ⛔ CAMBIATO"), flush=True)


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica))
