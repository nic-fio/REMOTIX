#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c19 — ⭐⭐ «A FINE GIRO NON SOPRAVVIVE NESSUN INQUILINO DELLA RETE»
===========================================================================

    python3 11-c19-la-scatola-resta-pulita.py
    python3 11-c19-la-scatola-resta-pulita.py --lascia-un-inquilino
    python3 11-c19-la-scatola-resta-pulita.py --lascia-una-casa
    python3 11-c19-la-scatola-resta-pulita.py --anche-lo-sporco
    python3 11-c19-la-scatola-resta-pulita.py --certifica

    che cosa deve essere vero : quando la rete ha finito di lavorare in una
                                scatola, **della rete non resta dentro
                                nessuno**: nessun inquilino vivo, nessuna
                                casa sua, nessun suo processo
    da dove parte             : dalla scatola COM'E' — ⛔ questa maglia non
                                prepara niente e non pulisce niente prima di
                                guardare.  ⭐ E' l'unica della lista che
                                giudica **il lavoro delle altre**
    che cosa guarda           : tre fatti, ciascuno col suo nome
      U  utenti     `/etc/passwd` non ha nessun nome dello spazio di nomi
                    della rete
      C  case       `/home` non ha nessuna cartella di quei nomi (⛔ il
                    `userdel` senza `-r`, che toglie l'utente e lascia la casa)
      P  processi   nessun processo gira per conto di uno di quei nomi
    come so che sa dare rosso : `--lascia-un-inquilino` (un utente della rete
                                vivo, con la sua casa e un suo processo) ·
                                `--lascia-una-casa` (⭐ solo la casa, l'utente
                                no: il residuo che nessun `pgrep` vede)

---------------------------------------------------------------------------
⛔⛔ PERCHE' ESISTE — 23 settembre 2026, `fasi/13-xfce.md` «Che cosa resta»
---------------------------------------------------------------------------

La sgomberata c'e' gia' (`11-gancio.sh`, `sgombera_inquilini`, 22 set 2026):
dopo ogni maglia il gancio passa sullo spazio di nomi della rete e toglie
utenti, case, unita' `user@` fallite e orfani di `/tmp`.  ⭐ Quel che mancava
e' il **VERDETTO**: oggi `bilancio_dopo` scrive *«la SCATOLA si e' sporcata»*
come una riga `inf`, annotata `riuscita=true`.

⇒ ⛔ **La rete puo' lasciare venti inquilini dentro una scatola e dichiararsi
  verde lo stesso.**  Questa maglia e' la riga che dice di no.

⚠ E non e' un caso di scuola: `[M]` 22 set 2026, dopo `--famiglia tutto`,
  22-24 inquilini vivi in ognuna delle tre scatole, con le loro `/home`, piu'
  unita' `user@…` fallite e orfani in `/tmp`.  ⇒ E quel che si accumula ROMPE
  le maglie: la bisezione del 21 set 2026 (C17 rossa su gnome e kde) ha
  dimostrato che lo stato accumulato dalla scatola fa accusare il prodotto di
  un rosso che non e' suo.

---------------------------------------------------------------------------
⛔⛔⛔ L'INSIDIA, E SI CHIAMA `nictest` — dichiarata perche' e' la sola cosa
      che, sbagliata, renderebbe questa maglia un generatore di rossi falsi
---------------------------------------------------------------------------

`11-accendi.sh bilancio` conta gli inquilini **per uid**:

    getent passwd | awk -F: '$3 >= 1000 && $3 < 60000 && $1 != "provanic"'

⇒ ⛔ Esclude **solo** `provanic`.  Per quel conto `nictest` — l'utente delle
  prove a mano, che **sta nelle scatole apposta** e ci deve restare — e' un
  inquilino, e una maglia costruita su quel conto direbbe rosso ogni volta che
  l'utente ha una sessione aperta.  ⚠ Un rosso falso, in una rete di sicurezza,
  finisce sempre allo stesso modo: la rete viene spenta da chi lavora.

⭐⭐ LA CURA: **si conta per NOME, non per uid** — e il nome e' quello che il
    gancio stesso usa per sgomberare (`sgombera_inquilini`):

        ^c[0-9]+b?u[0-9]+$        c1u1 · c3u2 · c8bu5 · c17u931 · c20u407

  ⇒ E' lo **spazio di nomi della rete**: chi ci sta dentro e' roba della rete e
    va tolto; chi ci sta fuori non e' mio da giudicare.  `nictest`, `provanic`,
    `root` e tutti gli utenti di sistema non ci cascano dentro **per forma**,
    non per una lista di eccezioni che qualcuno dovra' ricordarsi di aggiornare.

⚠ E c'e' il prezzo, dichiarato: un banco che chiama il suo inquilino **fuori**
  dallo spazio di nomi (`[M]` 23 set 2026, in gnome: `corrx1`, `corrx2` di
  `12-client-veri.py`; e il vecchio `13-w4` lo chiamava `w4u$$`) ⛔ non viene
  visto da questa maglia **e non viene sgomberato dal gancio**: sono la stessa
  lacuna, non due.  ⇒ Qui si STAMPANO come rilievo, cosi' chi legge li vede,
  ⛔ e si chiude alla radice dando ai banchi nuovi un nome della rete — e' il
  motivo per cui C20 chiama il suo inquilino `c20u<n>`.

---------------------------------------------------------------------------
⭐ CHE COSA GIUDICA E CHE COSA NO, e perche' il confine sta li'
---------------------------------------------------------------------------

⭐ **VERDETTO** sui tre fatti U · C · P: sono *«un inquilino della rete
   sopravvive»*, cioe' la frase esatta che questa maglia porta nel nome.

⚠ **RILIEVO, non verdetto** (si stampa coi numeri, ⛔ non fa rosso):
     · le unita' `user@N.service` fallite il cui uid non ha piu' un nome
     · le voci di `/tmp` senza padrone
     · le sessioni di `logind` senza un utente
   ⇒ Sono **la spazzatura degli inquilini, non gli inquilini**.  Farne un rosso
     vorrebbe dire che basta un file dimenticato in `/tmp` da un banco di
     un'altra fase per tenere la rete rossa per sempre — e un rosso perpetuo
     non e' una maglia, e' un interruttore che qualcuno spegnera'
     (`LEZIONI.md` §1.49).
   ⭐ E chi quel giorno vuole misurarla lo chiede per nome: `--anche-lo-sporco`
     promuove il rilievo a verdetto.  ⛔ La rete NON lo passa.

Esiti: 0 verde · 1 rosso · 3 non ho potuto guardare (⛔ NON e' un rosso).
⛔ Con un guasto innestato si legge AL CONTRARIO: 0 = il guasto e' stato VISTO.
"""
import argparse
import os
import random
import re
import subprocess
import sys
import time

# ⭐⭐ LO SPAZIO DI NOMI DELLA RETE, in un posto solo — ed e' LO STESSO che
#    `11-gancio.sh` (`sgombera_inquilini`) usa per sgomberare.
#    ⛔ Se i due divergono, il gancio toglie una cosa e questa maglia ne
#      giudica un'altra: vedi `LEZIONI.md` §1.46.
MODELLO = re.compile(r"^c[0-9]+b?u[0-9]+$")

# ⚠ Gli utenti di servizio che nelle scatole ci stanno APPOSTA.  ⛔ Non e' la
#   regola — la regola e' il modello qui sopra, e loro non ci cascano dentro
#   per forma.  Questa lista serve solo a STAMPARLI, cosi' chi legge vede che
#   la distinzione e' stata fatta e non dimenticata.
DI_SERVIZIO = {
    "provanic": "l'utente delle prove dei banchi (lo mette la ricetta)",
    "nictest":  "⭐ l'utente delle prove A MANO: sta nelle scatole apposta, "
                "e questa maglia non lo tocca e non lo conta",
}


def corri(argv, tempo=30):
    """Un comando, o `None` se non ha risposto.  ⛔ Non solleva mai."""
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=tempo)
    except (subprocess.TimeoutExpired, OSError):
        return None


def guscio(riga, tempo=30):
    try:
        return subprocess.run(["/bin/sh", "-c", riga], capture_output=True,
                              text=True, timeout=tempo)
    except (subprocess.TimeoutExpired, OSError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I FATTI — si leggono dalla macchina, e ciascuno torna `None` quando non
#   si e' potuto leggere.  ⛔ `None` non e' «vuoto»: vuoto e' un verde, `None`
#   e' un «non ho potuto guardare».
# ═══════════════════════════════════════════════════════════════════════════
def tutti_gli_utenti():
    """[(nome, uid)] di `/etc/passwd`, o `None`."""
    r = corri(["getent", "passwd"], 20)
    if r is None or r.returncode != 0:
        return None
    fuori = []
    for riga in (r.stdout or "").splitlines():
        pezzi = riga.split(":")
        if len(pezzi) < 3:
            continue
        try:
            fuori.append((pezzi[0], int(pezzi[2])))
        except ValueError:
            continue
    return fuori


def case_in(cartella="/home"):
    """I nomi delle cartelle di `/home`, o `None`."""
    try:
        return sorted(os.listdir(cartella))
    except OSError:
        return None


def processi_di(nomi):
    """{nome: [pid…]} per i nomi dati.  ⛔ Chiede a `pgrep -u`, che guarda
       l'uid REALE: ⚠ un `pkill -f` sul nome pescherebbe anche il guscio che
       lo sta eseguendo (`LEZIONI.md`, 22 set 2026: il guscio si uccideva da
       solo), e qui non serve uccidere niente — serve CONTARE."""
    fuori = {}
    for n in nomi:
        r = corri(["pgrep", "-u", n], 15)
        if r is None:
            continue
        pid = [x for x in (r.stdout or "").split() if x.isdigit()]
        if pid:
            fuori[n] = pid
    return fuori


def sporco_della_scatola(noti):
    """⚠ RILIEVO: la spazzatura, non gli inquilini.  `noti` = gli uid che in
       `/etc/passwd` un nome ce l'hanno ancora."""
    unita, orfani, sessioni = [], [], []
    r = corri(["systemctl", "--failed", "--no-legend", "--plain"], 30)
    if r is not None:
        for riga in (r.stdout or "").splitlines():
            m = re.match(r"^\s*user@(\d+)\.service", riga)
            if m and int(m.group(1)) not in noti:
                unita.append(m.group(1))
    r = guscio("find /tmp -mindepth 1 -maxdepth 1 -nouser 2>/dev/null", 30)
    if r is not None:
        orfani = [x for x in (r.stdout or "").splitlines() if x.strip()]
    r = corri(["loginctl", "list-sessions", "--no-legend"], 20)
    if r is not None:
        for riga in (r.stdout or "").splitlines():
            pezzi = riga.split()
            if len(pezzi) >= 3 and pezzi[1].isdigit() and int(pezzi[1]) not in noti:
                sessioni.append(pezzi[0])
    return unita, orfani, sessioni


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ IL GIUDIZIO — funzione PURA: nessuna lettura di file, nessun comando.
#   ⇒ `--certifica` la attraversa senza toccare ne' la macchina ne' il prodotto.
# ═══════════════════════════════════════════════════════════════════════════
def giudizio(utenti, case, processi, sporco=None):
    """⭐ (esito, U, C, P, perche) dai FATTI gia' raccolti.

    `utenti` [(nome, uid)] di tutta la macchina · `case` i nomi in `/home` ·
    `processi` {nome: [pid…]} · `sporco` (unita, orfani, sessioni) oppure
    `None` quando lo sporco NON entra nel verdetto (il modo della rete).
    """
    if utenti is None or case is None:
        return 3, "?", "?", "?", ("non ho potuto leggere %s: senza questo non "
                                  "so chi e' rimasto dentro"
                                  % ("/etc/passwd" if utenti is None else "/home"))

    della_rete = sorted(n for n, _ in utenti if MODELLO.match(n))
    case_rete = sorted(n for n in case if MODELLO.match(n))
    proc_rete = sorted(n for n in processi if MODELLO.match(n))

    accuse = []
    if della_rete:
        accuse.append("in /etc/passwd sopravvivono %d inquilini della rete: %s"
                      % (len(della_rete), " ".join(della_rete)))
    if case_rete:
        accuse.append("in /home restano %d case della rete: %s"
                      % (len(case_rete), " ".join(case_rete)))
    if proc_rete:
        accuse.append("girano ancora processi di %s"
                      % ", ".join("%s (%d)" % (n, len(processi[n]))
                                  for n in proc_rete))
    # ⚠ Lo sporco entra SOLO se chi chiama lo ha chiesto (`--anche-lo-sporco`).
    if sporco is not None:
        unita, orfani, sessioni = sporco
        if unita:
            accuse.append("%d unita' user@ fallite senza piu' un utente: %s"
                          % (len(unita), " ".join(unita[:8])))
        if orfani:
            accuse.append("%d voci di /tmp senza padrone: %s"
                          % (len(orfani), " ".join(orfani[:5])))
        if sessioni:
            accuse.append("%d sessioni di logind senza un utente" % len(sessioni))

    u = "NO" if della_rete else "SI"
    c = "NO" if case_rete else "SI"
    p = "NO" if proc_rete else "SI"
    if accuse:
        return 1, u, c, p, "; ".join(accuse)
    return 0, u, c, p, ("della rete non e' rimasto dentro nessuno: 0 inquilini, "
                        "0 case, 0 processi")


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ I GUASTI INNESTATI — si innestano sulla SCATOLA, e si tolgono sempre.
#
# ⭐ Portano un nome dello spazio di nomi della rete apposta: se questo giro
#   muore a meta', il gancio li sgombera da se' alla maglia dopo.  ⛔ Un banco
#   che lascia residui mentre misura i residui sarebbe una barzelletta.
# ═══════════════════════════════════════════════════════════════════════════
def innesta_un_inquilino(chi):
    """⛔ Un inquilino della rete VIVO: utente + casa + un suo processo."""
    r = corri(["useradd", "-m", "-s", "/bin/bash", chi], 60)
    if r is None or r.returncode != 0:
        return False, "useradd non e' riuscito"
    # ⚠ `setsid` e stdin su /dev/null, come la scena di C3: un figlio lasciato
    #   nel gruppo di processi del terminale finisce fermo in `T`.
    guscio("setsid runuser -u %s -- sleep 600 < /dev/null > /dev/null 2>&1 &"
           % chi, 20)
    for _ in range(20):
        r = corri(["pgrep", "-u", chi], 10)
        if r is not None and r.returncode == 0:
            return True, ""
        time.sleep(0.25)
    return True, "⚠ l'utente c'e' ma il suo processo non si e' visto"


def innesta_una_casa(chi):
    """⛔ SOLO la casa: l'utente no.  E' il `userdel` senza `-r`, cioe' il
       residuo che nessun `pgrep` e nessun `getent passwd` vedono."""
    try:
        os.makedirs(os.path.join("/home", chi), exist_ok=True)
        with open(os.path.join("/home", chi, ".c19"), "w") as f:
            f.write("residuo innestato da C19\n")
        return True, ""
    except OSError as e:
        return False, "non ho potuto fare /home/%s: %s" % (chi, e)


def togli_il_guasto(chi):
    """⭐ Sempre, e senza chiedere."""
    corri(["loginctl", "terminate-user", chi], 20)
    corri(["pkill", "-KILL", "-u", chi], 10)
    time.sleep(0.3)
    corri(["userdel", "-r", chi], 30)
    guscio("rm -rf /home/%s" % chi, 20)


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⛔ La maglia sa dare rosso, e sa NON darlo? Si prova sul GIUDIZIO."""
    guai = 0
    sistema = [("root", 0), ("daemon", 1), ("systemd-network", 998)]
    servizio = [("provanic", 4011), ("nictest", 4012)]
    casi = [
        ("⭐ scatola pulita (ci sono solo provanic e nictest) ⇒ VERDE",
         (sistema + servizio, ["provanic", "nictest", "lost+found"], {}, None), 0),
        ("⛔ un inquilino della rete sopravvive ⇒ ROSSO",
         (sistema + servizio + [("c3u2", 4013)],
          ["provanic", "nictest", "c3u2"], {"c3u2": ["991"]}, None), 1),
        ("⛔ l'utente non c'e' piu' ma la CASA si' (userdel senza -r) ⇒ ROSSO",
         (sistema + servizio, ["provanic", "nictest", "c8bu5"], {}, None), 1),
        ("⛔ utente e casa spariti, un PROCESSO suo e' vivo ⇒ ROSSO",
         (sistema + servizio, ["provanic", "nictest"], {"c17u931": ["4"]}, None), 1),
        ("⛔ venti inquilini della rete, come il 22 set ⇒ ROSSO",
         (sistema + servizio + [("c%du1" % i, 4020 + i) for i in range(20)],
          ["provanic", "nictest"], {}, None), 1),
        ("⭐⭐ nictest vivo, con la sua casa E un suo processo ⇒ VERDE "
         "(⛔ l'insidia: `bilancio` lo conterebbe)",
         (sistema + servizio, ["provanic", "nictest"],
          {"nictest": ["101", "102", "103"]}, None), 0),
        ("⭐ provanic con la sua casa e i suoi processi ⇒ VERDE",
         (sistema + servizio, ["provanic", "nictest"],
          {"provanic": ["77"]}, None), 0),
        ("⚠ un utente FUORI dallo spazio di nomi (corrx1) ⇒ VERDE: "
         "non e' mio da giudicare, si stampa e basta",
         (sistema + servizio + [("corrx1", 4013)],
          ["provanic", "nictest", "corrx1"], {"corrx1": ["55"]}, None), 0),
        ("⚠ solo SPORCO (unita' fallite e orfani di /tmp) ⇒ VERDE: "
         "e' spazzatura, non un inquilino",
         (sistema + servizio, ["provanic", "nictest"], {}, None), 0),
        ("⭐ lo stesso sporco, ma chiesto col verdetto (--anche-lo-sporco) ⇒ ROSSO",
         (sistema + servizio, ["provanic", "nictest"], {},
          (["4023", "4024"], ["/tmp/mozilla"], [])), 1),
        ("⚠ /etc/passwd non si legge ⇒ 3, ⛔ mai un rosso",
         (None, ["provanic"], {}, None), 3),
        ("⚠ /home non si legge ⇒ 3, ⛔ mai un rosso",
         (sistema + servizio, None, {}, None), 3),
    ]
    print("== C19 — certificazione del giudizio (⛔ senza toccare la scatola)")
    for nome, argomenti, atteso in casi:
        e = giudizio(*argomenti)[0]
        if e != atteso:
            guai += 1
        print("  %s %-78s esito %s (atteso %s)"
              % ("OK " if e == atteso else "NO ", nome, e, atteso))

    # ⭐ E il modello si prova per NOME, non per fiducia: e' l'unica cosa che
    #   separa un inquilino della rete da `nictest`.
    prove_nome = [("c1u1", True), ("c3u2", True), ("c8bu5", True),
                  ("c17u931", True), ("c20u407", True), ("c19u100", True),
                  ("nictest", False), ("provanic", False), ("root", False),
                  ("corrx1", False), ("w4u12345", False), ("ki9", False),
                  ("c1u1x", False), ("xc1u1", False)]
    for nome, atteso in prove_nome:
        avuto = bool(MODELLO.match(nome))
        if avuto != atteso:
            guai += 1
        print("  %s lo spazio di nomi della rete: %-12s ⇒ %s (atteso %s)"
              % ("OK " if avuto == atteso else "NO ", nome,
                 "della rete" if avuto else "non mio",
                 "della rete" if atteso else "non mio"))
    print()
    if guai:
        print("⛔ %d casi del giudizio NON danno quel che devono" % guai)
        return 1
    print("⭐ il giudizio da' verde, rosso e «non lo so» dove deve — e ⭐ "
          "`nictest` con la sua casa, i suoi processi e la sua\n   sessione "
          "resta un VERDE, che e' l'unico modo perche' questa maglia sia "
          "utile invece che molesta")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=0,
                   help="⚠ non serve: questa maglia non parla col prodotto. "
                        "C'e' perche' il gancio chiama tutte le maglie allo "
                        "stesso modo")
    p.add_argument("--lascia-un-inquilino", action="store_true",
                   help="⛔ IL GUASTO INNESTATO: un utente della rete vivo, "
                        "con la sua casa e un suo processo")
    p.add_argument("--lascia-una-casa", action="store_true",
                   help="⛔ IL GUASTO INNESTATO, l'altro: SOLO la casa, "
                        "l'utente no (il `userdel` senza `-r`)")
    p.add_argument("--anche-lo-sporco", action="store_true",
                   help="⚠ promuove a VERDETTO le unita' fallite e gli orfani "
                        "di /tmp.  ⛔ La rete non lo passa: vedi in testa")
    p.add_argument("--case", default="/home")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if os.geteuid() != 0:
        print("⛔ vuole l'amministratore (legge le unita' e i processi di "
              "tutti) ⇒ non ho potuto guardare")
        return 3

    innestato = ""
    if a.lascia_un_inquilino:
        innestato = " ⛔ GUASTO INNESTATO: --lascia-un-inquilino"
    elif a.lascia_una_casa:
        innestato = " ⛔ GUASTO INNESTATO: --lascia-una-casa"
    chi = "c19u%d" % random.randint(100, 999)
    print("== C19 — a fine giro non sopravvive nessun inquilino della rete%s"
          % innestato)

    guasto_chi = None
    try:
        if a.lascia_un_inquilino or a.lascia_una_casa:
            guasto_chi = chi
            togli_il_guasto(chi)
            if a.lascia_un_inquilino:
                fatto, nota = innesta_un_inquilino(chi)
            else:
                fatto, nota = innesta_una_casa(chi)
            if not fatto:
                print("   ⛔ non ho potuto innestare il guasto (%s) ⇒ non ho "
                      "potuto guardare" % nota)
                return 3
            print("   ⛔ innestato: %s%s" % (chi, (" — " + nota) if nota else ""))

        utenti = tutti_gli_utenti()
        case = case_in(a.case)
        if utenti is None or case is None:
            esito, u, c, pf, perche = giudizio(utenti, case, {}, None)
            print("   ⚠ %s" % perche)
            return 3

        della_rete = sorted(n for n, _ in utenti if MODELLO.match(n))
        processi = processi_di(della_rete + sorted(DI_SERVIZIO))
        noti = set(uid for _, uid in utenti)
        sporco = sporco_della_scatola(noti)

        # ── quel che NON conto, stampato: la distinzione si vede ──
        fuori = sorted(n for n, uid in utenti
                       if 1000 <= uid < 60000 and not MODELLO.match(n)
                       and n not in DI_SERVIZIO)
        for n in sorted(DI_SERVIZIO):
            if any(x == n for x, _ in utenti):
                print("   ⭐ NON lo conto: «%s» — %s%s"
                      % (n, DI_SERVIZIO[n],
                         (" (adesso ha %d processi)" % len(processi[n]))
                         if n in processi else ""))
        if fuori:
            print("   ⚠ RILIEVO: %d utenti fuori dallo spazio di nomi della "
                  "rete, che ne' io ne' il gancio\n      tocchiamo: %s  ⇒ il "
                  "banco che li ha fatti dovrebbe dare loro un nome della rete"
                  % (len(fuori), " ".join(fuori)))

        esito, u, c, pf, perche = giudizio(
            utenti, case, processi, sporco if a.anche_lo_sporco else None)

        print("   U %-3s C %-3s P %-3s" % (u, c, pf))
        unita, orfani, sessioni = sporco
        print("   %s unita' user@ fallite senza utente: %d · voci di /tmp "
              "senza padrone: %d · sessioni orfane: %d"
              % ("⭐ VERDETTO (--anche-lo-sporco):" if a.anche_lo_sporco
                 else "⚠ RILIEVO, non verdetto:", len(unita), len(orfani),
                 len(sessioni)))

        print()
        if a.lascia_un_inquilino or a.lascia_una_casa:
            # ⛔ Al contrario, e si dice a voce: qui lo 0 e' la buona notizia.
            if esito == 1:
                print("⭐ IL GUASTO INNESTATO E' STATO VISTO — questa maglia SA "
                      "dare rosso,\n   ⭐ e per la ragione giusta: %s" % perche)
                return 0
            if esito == 3:
                print("⚠ col guasto innestato NON ho potuto guardare: %s\n"
                      "   ⇒ esito 3, non un verde" % perche)
                return 3
            print("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: «%s» era dentro "
                  "la scatola\n   e la maglia ha detto verde lo stesso." % chi)
            return 1
        if esito == 0:
            print("⭐ VERDE — %s" % perche)
        elif esito == 1:
            print("⛔⛔ ROSSO — %s" % perche)
            print("   ⇒ la rete ha lavorato in questa scatola e non ha "
                  "sgomberato: vedi `sgombera_inquilini`\n     in "
                  "`11-gancio.sh`, e il banco che ha creato questi nomi")
        else:
            print("⚠ non ho potuto guardare — %s" % perche)
        return esito
    finally:
        if guasto_chi:
            togli_il_guasto(guasto_chi)
            print("   ⭐ il guasto innestato e' stato tolto: «%s» non c'e' piu'"
                  % guasto_chi)


if __name__ == "__main__":
    sys.exit(main())
