#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c7 — ⭐⭐ «SI CHIUDE TUTTO, E NON RESTA NIENTE»
===========================================================================

    python3 11-c7-si-chiude-e-non-resta-niente.py --porta 8513
    python3 11-c7-si-chiude-e-non-resta-niente.py --porta 8513 --solo-distacco
    python3 11-c7-si-chiude-e-non-resta-niente.py --porta 8513 --lascia-un-processo
    python3 11-c7-si-chiude-e-non-resta-niente.py --certifica

La riga C7 di `fasi/11-la-rete-di-sicurezza.md` §4.1:

    che cosa deve essere vero : si chiude tutto, e non resta niente
    da dove parte             : dopo una sessione FINITA
    che cosa guarda           : processi orfani, socket, lucchetti, ⭐ la
                                scheda grafica tornata a riposo
    come so che sa dare rosso : si lascia un processo apposta ⇒ rosso

⭐ C7 giudica **residui**, non pixel.  ⇒ Non e' fermata dal difetto aperto
   della fase 10 (`[M]` dieci sessioni GNOME nuove su dieci nascono cieche,
   §7-bis.13): a lei non serve che si VEDA qualcosa, le serve che qualcosa sia
   stato **appoggiato per terra** e poi tolto.
⛔ Ma la sessione deve PARTIRE davvero, o questa maglia diventa il difetto
   §1.44 — *«il predicato che non poteva dare rosso»*: una sessione che non
   nasce non lascia niente, e «non resta niente» sarebbe verde per sempre.
   ⇒ Vedi «LA GUARDIA CHE TIENE IN PIEDI TUTTO», piu' sotto.

---------------------------------------------------------------------------
⛔⛔ LA COSA PIU' IMPORTANTE DI QUESTA MAGLIA: «FINITA» NON VUOL DIRE «STACCATA»
---------------------------------------------------------------------------

L'invariante **I4** del progetto dice che **il palco appartiene alla SESSIONE
e sopravvive alla disconnessione**.  ⇒ ⛔ Un cliente che se ne va **non deve**
far scattare C7.  Una stesura ingenua — *«il cliente si stacca, adesso non
deve restare niente»* — sarebbe **rossa a ogni giro su un prodotto sano**, cioe'
il difetto §1.49: *un rosso che non si puo' far diventare verde e' peggio di
nessuna maglia*, e finisce spento da chi lavora.

⭐ **Come si distinguono, e si distinguono con un GESTO, non con un'opinione:**

    si stacca il CLIENTE   il filo QUIC cade.  ⭐ Il figlio dell'inquilino
                           resta vivo, il suo `/run/user/<uid>` resta, la sua
                           sessione `loginctl` resta.  `[M]` 26 ago 2026,
                           scatola XFCE: dopo il distacco l'inquilino aveva
                           ancora **8 processi** e **8 voci** in
                           `XDG_RUNTIME_DIR`.  E il registro del prodotto lo
                           dice con parole sue:
                             «il ciclo dei fotogrammi si SPEGNE: non guarda
                              piu' nessuno, e il palco resta in piedi (I4)»

    si CHIUDE la sessione  ⭐ il gesto e' `loginctl terminate-user <chi>` —
                           cioe' quel che succede quando l'inquilino ESCE.
                           ⛔ Non e' una scelta di comodo: il prodotto **non
                           ha** un comando «chiudi la sessione» (il socket di
                           comando serve al ban, `src/comando.c`), quindi la
                           fine di una sessione, oggi, e' la fine della
                           sessione di `logind`.  Se un domani il prodotto
                           ne avra' uno, si cambia QUESTA riga e non il resto.

⇒ ⭐ **Un giro normale giudica DUE cose, e sono due giudizi distinti:**

    1. il distacco NON ha portato via il palco   ⭐ il FIGLIO «remotix» e'
                                                 ancora fra i processi
                                                 dell'inquilino
    2. la chiusura NON ha lasciato niente        (prima = dopo)

⚠ E la (1) e' falsificabile davvero: se il palco sparisse col distacco, questa
  maglia dice **rosso di specie diversa** e lo dice per nome.  ⛔ Restare zitti
  li' vorrebbe dire che la (2) diventa verde **perche' non c'era niente da
  chiudere** — che e' la bugia piu' comoda di tutta questa maglia.

⛔⛔ E LA (1) HA GIA' MENTITO UNA VOLTA, ⚠ ed e' scritto qui perche' e' il
    difetto piu' grave che questa maglia abbia avuto.  Fino al **27 agosto
    2026** la domanda non era *«il figlio c'e' ancora?»* ma *«e' cambiato
    QUALCOSA fra la partenza e il distacco?»* — e dopo un distacco cambia
    sempre qualcosa che **non e' il prodotto**: `user@<uid>.service` e'
    `active`, le sessioni di `loginctl` sono 2, `/run/user/<uid>` ha i suoi
    socket.  ⇒ Il predicato non poteva fallire (`LEZIONI.md` §1.44), e con
    l'impronta vera **senza `remotix`** — cioe' con I4 rotta — la maglia
    rispondeva `(0, 'regge')` in tutt'e due i modi in cui il gancio la fa
    girare.  ⛔⛔ **C7 diceva VERDE su una I4 rotta**, e queste stesse righe
    promettevano il contrario.
  ⭐ E la certificazione non poteva prenderlo: il caso sintetico usava
    `staccato = vuota`, un'impronta **totalmente** vuota — la forma che
    l'autore aveva immaginato, non la forma che il guasto avrebbe.  ⇒ Adesso
    c'e' `SENZA_FIGLIO`, che e' `VIVA` tolto `remotix` e nient'altro.

---------------------------------------------------------------------------
⭐ CHE COSA ENTRA NELL'IMPRONTA — e che cosa NON ci entra, dichiarato
---------------------------------------------------------------------------

L'impronta si prende **per INQUILINO**, mai globalmente: fase 10 §7.3, dove un
`pkill -f` globale ha rischiato di uccidere il lavoro di un'altra prova in
corso.  ⇒ Tutto quel che segue e' filtrato per `uid`.

  ⭐ GIUDICATE (prima e dopo devono combaciare)

    processi dell'inquilino     i NOMI ordinati, ⛔ non i numeri di processo:
                                un pid diverso non e' un residuo.
                                `[M]` 26 ago 2026, durante: `(sd-pam) ·
                                dbus-daemon · pipewire · pipewire ·
                                pipewire-pulse · remotix · systemd ·
                                wireplumber`
    socket e file in            `/run/user/<uid>`: i nomi ordinati.
    XDG_RUNTIME_DIR             `[M]` durante: `bus · dbus-1 · pipewire-0 ·
                                pipewire-0-manager · pulse · systemd` + i
                                lucchetti
    ⭐ lucchetti                 i `*.lock` dentro `XDG_RUNTIME_DIR` (li mette
                                PipeWire).  ⚠ Sono un sottoinsieme della voce
                                di sopra, ed e' voluto: si contano **a parte**
                                perche' la riga C7 li nomina, e una voce
                                nominata dal documento che sparisce dentro
                                un'altra e' una voce che nessuno controlla piu'
    sessioni di `loginctl`      QUANTE ne ha l'inquilino, non quali: gli
                                identificativi cambiano a ogni giro
                                (`c85`, `c86`…) e confrontarli darebbe rosso
                                sempre.  `[M]` durante: **2** (`user` +
                                `manager`)
    unita' d'utente             `user@<uid>.service` e
                                `user-runtime-dir@<uid>.service`, lo stato in
                                vigore letto con `is-active`
    ⭐ /dev/dri                  quanti processi **dell'inquilino** tengono
                                aperto un descrittore sulla scheda.  ⇒ E'
                                *«la scheda grafica tornata a riposo»* della
                                riga C7

  ⚠ STAMPATE E NON GIUDICATE — ⛔ e la ragione conta

    la home                     una sessione SCRIVE nella propria home
                                (`.config`, `.cache`, `.local`), ed e' il suo
                                mestiere.  `[M]` 26 ago 2026: la home passa da
                                **4** a **8** voci in un giro.  ⇒ Metterla fra
                                le giudicate vorrebbe dire un rosso a ogni
                                giro su un prodotto sano: §1.49.
                                ⭐ Il prodotto non promette di cancellare la
                                home, promette di non lasciare **roba viva**.
    quel che ha scritto in      stessa ragione, e una in piu': sulla macchina
    `/tmp`                      vera `~/.cache` **e' un collegamento a /tmp**
                                (scelta del proprietario, `DECISIONI.md`
                                §4.6-undecies).  ⇒ Giudicare `/tmp` vorrebbe
                                dire giudicare la home per un'altra strada.

  ⛔ E IL RUMORE DI FONDO, dichiarato invece che tolto di nascosto:

    · l'impronta e' **per uid**, e l'inquilino e' creato NUOVO a ogni giro
      ⇒ tutto quel che appartiene ad altri (il server, gli altri banchi, il
        sistema della scatola) non entra mai nel confronto;
    · il numero **totale** di processi con la scheda aperta si stampa e ⛔ NON
      si giudica: dentro la scatola potrebbe esserci un altro banco al lavoro,
      e un confronto globale e' esattamente il difetto della fase 10 §7.3.

---------------------------------------------------------------------------
⛔⛔ LA GUARDIA CHE TIENE IN PIEDI TUTTO — e sono TRE, in ordine
---------------------------------------------------------------------------

Senza queste, «non resta niente» e' verde anche quando non e' successo niente
(§1.44), e il verde non ha nessuna misura sotto (§1.46).

  1. ⛔ **Il campo dev'essere libero PRIMA.**  Se l'impronta di partenza non e'
     vuota, l'inquilino si porta dietro un avanzo di qualcun altro (o di questo
     banco di ieri: §1.39 «da zero comprende anche da zero rispetto a me
     stesso»).  ⇒ Esito **2**, terreno cattivo — e ⛔ **non** si accusa la
     sessione di un residuo che c'era gia'.
  2. ⛔ **Il cliente dev'essere stato AMMESSO.**  Se no: esito **3**, non ho
     potuto guardare.  ⚠ Come C1, il motivo si porta accanto al sintomo: `[M]`
     26 ago 2026 cinque giri di C1 dissero «NON-AMMESSO» e la causa vera era
     `aioquic` mancante.
  3. ⛔ **Il registro deve dire che il figlio E' NATO.**  «Ammesso» e «la
     sessione e' partita» sono due domande, ed e' la stessa distinzione che
     `sessione.h` fa fra *«e' viva?»* e *«ha un monitor?»*.  Se il registro non
     nomina il figlio di questo inquilino: esito **3**.

⚠ E una quarta, che e' la meta' dimenticata di §1.49: **si aspetta l'EVENTO**.
  Dopo la chiusura si guarda finche' il campo torna libero, fino a un tempo
  DICHIARATO (`--attesa-chiusura`), e ⭐ **si stampa quanto ci ha messo**.  Una
  chiusura lenta ma completa e' verde; ⛔ un tetto a orologio l'avrebbe chiamata
  rossa.  `[M]` 26 ago 2026, scatola XFCE, giro vero: **1,13 s**.

---------------------------------------------------------------------------
⛔ IL GUASTO INNESTATO — `--lascia-un-processo`
---------------------------------------------------------------------------

§3.6: *«ogni prova della lista ha, obbligatoriamente, il suo guasto innestato, e
quel caso va fatto girare, non immaginato»*.

Prima di chiudere si lascia apposta un processo dell'inquilino **fuori dalla
fetta di systemd dell'utente**:

    setsid runuser -u <chi> -- sleep N

⭐ E la forma non e' casuale: e' **la stessa** del figlio vero del prodotto —
  un processo che gira come l'inquilino ma pende dal server, non dalla sua
  sessione (`[M]` `pid 12113 remotix, ppid 10575, uid c7u1`).  ⇒ Cioe' si
  innesta la classe di orfano che questo prodotto puo' davvero lasciare, non
  un orfano di comodo.
`[M]` 26 ago 2026, misurato prima di scrivere questa maglia: `terminate-user`
**non** lo porta via ⇒ resta, ⇒ rosso.

---------------------------------------------------------------------------
⛔ QUEL CHE C7 **NON** GUARDA — o qualcuno se ne fidera' troppo
---------------------------------------------------------------------------

  · **i pixel**: C7 non apre nessuna immagine.  Una sessione nera lascia gli
    stessi residui di una sessione sana ⇒ C7 dice verde su tutte e due.  Quella
    domanda e' di C1 e C2.
  · **la memoria**: aprire e chiudere cento sessioni e guardare se il server
    cresce e' una prova di lunga durata, ⛔ un altro mestiere (§6).
  · **i residui DENTRO il server**: una casella non liberata, una struttura non
    liberata, un descrittore che il PADRE non chiude.  C7 guarda **per terra**
    (processi, socket, unita', scheda), non dentro il processo del server.
  · **la home e /tmp**: misurate, stampate, ⛔ non giudicate (vedi sopra).
  · **la scatola**: C7 chiude una SESSIONE, non il contenitore.  Che il
    contenitore non si spenga da solo e' una domanda vicina e diversa, ed e'
    trattata nel rapporto di questa maglia, non qui dentro.
  · ⚠ **le altre scatole**: questa maglia lavora dentro quella in cui gira, e
    l'inquilino se lo crea e se lo cancella per nome.

---------------------------------------------------------------------------
GLI ESITI (§4.5 del documento di fase)
---------------------------------------------------------------------------

  0  ⭐ ho guardato: il distacco ha lasciato il palco in piedi, e la chiusura
     non ha lasciato niente
  1  ⛔ ho guardato e NON regge ⇒ rosso.  Due specie, e si dicono per nome:
       (a) la chiusura ha lasciato dei residui
       (b) il distacco si e' portato via il palco (I4)
  3  ⛔ non ho potuto guardare: il cliente non e' stato ammesso, il figlio non
     e' nato, o nessuna voce dell'impronta ha saputo rispondere — ⛔ e NON e'
     un rosso
  2  il terreno non regge: il campo non era libero prima di cominciare
===========================================================================
"""
import argparse
import importlib.util
import os
import pwd
import re
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ «IL CLIENTE E' STATO AMMESSO?» — ⛔ IL PREDICATO SI IMPORTA, NON SI
#     RISCRIVE.  La casa e' `11-c1-nasce-e-si-vede.py`, e ce n'e' UNA (§1.47).
#
# ⛔ Fino al 27 agosto 2026 qui c'era `"AMMESSO" in uscita`, ⭐ e non poteva
#    dire di no: `[R]` `01-b3-cliente.py` stampa quella parola anche nei **due
#    messaggi di rifiuto** — «CONGEDO invece di AMMESSO: motivo …» (:1315) e
#    «atteso AMMESSO, arrivato …» (:1322) — e li stampa sullo **stdout**, che
#    e' esattamente dove si guardava.  ⇒ Un predicato che non puo' fallire,
#    `LEZIONI.md` §1.44: la maglia si credeva entrata **anche quando era stata
#    respinta**, e poi giudicava il buio che ne seguiva come un difetto del
#    prodotto.
# ⚠ Era in CINQUE maglie con la stessa riga.  ⇒ Curarla cinque volte sarebbe
#   stato creare cinque posti da cui divergere di nuovo (§1.47): sta in C1, e
#   le altre quattro la importano da li'.
# ⛔ E se non si riesce a importarla si esce **3** e lo si dice, ⇒ ⛔ non si
#   ripiega in silenzio sul predicato povero — che e' il difetto stesso.
# ═══════════════════════════════════════════════════════════════════════════
_QUI_C1 = os.path.dirname(os.path.abspath(__file__))
_C1 = None


def _carica_c1():
    """⛔ E' un CARICATORE, non un giudice: trova il file, non decide niente.

    ⚠ Si cerca accanto a me (dentro la scatola tutto sta in `/opt/remotix`) e
      un piano piu' su, come fanno C2, C3 e C6 coi loro giudici importati.
    """
    for p in (os.path.join(_QUI_C1, "11-c1-nasce-e-si-vede.py"),
              os.path.join(os.path.dirname(_QUI_C1), "11-scatole",
                           "11-c1-nasce-e-si-vede.py")):
        if not os.path.exists(p):
            continue
        spec = importlib.util.spec_from_file_location("c1_ammissione", p)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        # ⛔ Si VERIFICA che ci sia quel che serve, invece di fidarsi del nome
        #    del file (`CODER.md` §3.9).
        if not callable(getattr(m, "e_stato_ammesso", None)):
            return None
        if not callable(getattr(m, "certifica_ammissione", None)):
            return None
        # ⭐ E da C1 viene anche la garanzia dei gruppi della scheda: stessa
        #    ragione, stesso posto solo (§1.47).
        for mestiere in ("garantisci_i_gruppi", "verdetto_gruppi",
                         "certifica_gruppi"):
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_dell_ammissione():
    global _C1
    if _C1 is None:
        _C1 = _carica_c1()
    if _C1 is None:
        print("⛔ non trovo `11-c1-nasce-e-si-vede.py` accanto a me, e da li'")
        print("   viene il predicato «il cliente e' stato AMMESSO?» — che sta")
        print("   in un posto solo apposta (§1.47).")
        print("⇒ non ho potuto guardare — ⛔ e NON e' un rosso (§4.5).")
        sys.exit(3)
    return _C1


def e_stato_ammesso(coda):
    """⭐ `True` ammesso · `False` **RESPINTO** · `None` non ha detto niente.

    ⛔ `False` non e' un rosso del prodotto: un cliente respinto e' un cliente
       respinto, e chi chiama esce **3**.
    """
    return casa_dell_ammissione().e_stato_ammesso(coda)


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ I GRUPPI DELLA SCHEDA — ⛔ e anche questo sta in un posto solo (C1).

    Torna `(esito, perche)`: `0` = l'inquilino vede e si puo' misurare,
    `3` = ⛔ NON si misura.

    ⛔ Fino al 27 agosto 2026 questa maglia creava l'inquilino con
       `usermod -aG video,render` **e non rileggeva**: due nomi inchiodati (che
       sono di UNA distribuzione) e nessuna verifica.  ⭐ `[M]` senza i gruppi
       dei nodi `/dev/dri` la sessione nasce CIECA — 0 su 4, mai in 90 s, zero
       fotogrammi — e questa maglia avrebbe misurato il buio chiamandolo
       difetto del prodotto (`fasi/10-…` §7.4).
    ⭐ Il lavoro lo fa `attrezzi-gruppi-scheda.sh`, che legge i gid dai NODI e
       rilegge confrontando i numeri.  ⛔ Non se ne fa una copia qui (§1.47).
    """
    return casa_dell_ammissione().garantisci_i_gruppi(chi, prefisso)

# ---------------------------------------------------------------------------
# ⛔ LE VOCI SONO DICHIARATE QUI e stampate in ogni esito: «non resta niente»
#    e' un verdetto, e un verdetto senza il suo metro e' un'opinione (C11).
# ---------------------------------------------------------------------------
PROCESSI = "processi dell'inquilino"
RUNTIME = "socket e file in XDG_RUNTIME_DIR"
LUCCHETTI = "lucchetti (*.lock)"
SESSIONI = "sessioni di loginctl"
UNITA = "unita' d'utente"
SCHEDA = "descrittori su /dev/dri"
HOME = "la home"
TEMPORANEI = "quel che ha scritto in /tmp"

GIUDICATE = (PROCESSI, RUNTIME, LUCCHETTI, SESSIONI, UNITA, SCHEDA)
STAMPATE = (HOME, TEMPORANEI)

# ⛔ Il valore che vuol dire «vuoto» — e non e' `None`.  `None` vuol dire «non
#    ho potuto guardare», e le due cose non devono avere la stessa faccia.
VUOTO = "(niente)"

# ⭐⭐ IL NOME DEL FIGLIO — ed e' la voce su cui si regge tutto il GIUDIZIO 1.
#
# ⛔⛔ 27 ago 2026, difetto vero di QUESTA maglia, trovato da un agente mandato
#     a smentirla: il GIUDIZIO 1 chiedeva *«e' cambiato QUALCOSA fra la
#     partenza e il distacco?»* invece di *«il figlio del prodotto c'e'
#     ancora?»*.  ⚠ E dopo un distacco cambia SEMPRE qualcosa che non e' il
#     prodotto — `user@<uid>.service` e' `active`, le sessioni di `loginctl`
#     sono 2, `/run/user/<uid>` ha i suoi socket.  ⇒ Il predicato non poteva
#     fallire (`LEZIONI.md` §1.44): chiamando `giudica` con l'impronta vera
#     **senza `remotix`** — cioe' con I4 rotta — la maglia rispondeva
#     `(0, 'regge')` in tutt'e due i modi in cui il gancio la fa girare.
#     ⛔ C7 diceva VERDE su una I4 rotta.
#
# ⇒ La domanda giusta e' per NOME, e il nome e' quello che il figlio porta in
#   `/proc/<pid>/comm`.  `[M]` 26 ago 2026, scatola XFCE, a sessione viva:
#   `(sd-pam) · dbus-daemon · pipewire · pipewire · pipewire-pulse · remotix ·
#   systemd · wireplumber` — ⭐ ed e' il `remotix` di mezzo, il figlio
#   dell'inquilino (`[M]` `pid 12113 remotix, ppid 10575, uid c7u1`).
NOME_FIGLIO = "remotix"

# ⛔ Il processo che il GUASTO INNESTATO lascia per terra — vedi
#    `--lascia-un-processo`.  Serve a distinguere «l'iniezione ha morso» da
#    «c'era gia' un residuo suo» (§1.52, la stessa cura che C9 ha gia').
NOME_INIETTATO = "sleep"

FIRMA_FIGLIO = re.compile(r"figlio\s+\[(?P<chi>[^\]]+)\]")


def nomi_processi(valore):
    """I nomi dell'impronta dei processi, uno per uno.

    ⛔ Il confronto e' per nome INTERO: un `remotix-cliente` non e' il figlio,
       e una sottostringa lo farebbe passare.  ⚠ `None` e `VUOTO` danno la
       lista vuota, e chi chiama distingue i due casi da se'.
    """
    if valore is None or valore == VUOTO:
        return []
    return [n.strip() for n in valore.split("·")]


# ---------------------------------------------------------------------------
# RACCOGLIERE L'IMPRONTA
# ---------------------------------------------------------------------------
def corri(argv, tempo=30):
    """Esegue e torna (codice, uscita).  ⛔ Niente `sh -c` in mezzo dove si puo'
       evitare: `LEZIONI.md` §1.46."""
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=tempo)
        return p.returncode, (p.stdout or "")
    except (OSError, subprocess.SubprocessError):
        return None, ""


def uid_di(chi):
    try:
        return pwd.getpwnam(chi).pw_uid
    except KeyError:
        return None


def processi_di(uid):
    """I NOMI dei processi dell'inquilino, ordinati.  ⛔ Non i pid.

    Si legge `/proc` invece di chiamare `ps`: ⭐ cosi' la stessa passata da'
    anche i descrittori sulla scheda, e non si chiede due volte al sistema una
    fotografia che nel frattempo cambia.
    Torna `(nomi, quanti_con_la_scheda, pid)` — ⛔ o `(None, None, None)` se
    `/proc` non si e' fatto leggere.
    """
    try:
        elenco = os.listdir("/proc")
    except OSError:
        return None, None, None
    nomi, schede, pid = [], 0, []
    for voce in elenco:
        if not voce.isdigit():
            continue
        try:
            if os.stat("/proc/%s" % voce).st_uid != uid:
                continue
        except OSError:
            continue
        try:
            with open("/proc/%s/comm" % voce) as f:
                nomi.append(f.read().strip())
        except OSError:
            continue
        pid.append(voce)
        if descrittori_scheda("/proc/%s/fd" % voce):
            schede += 1
    return sorted(nomi), schede, pid


def descrittori_scheda(cartella):
    """Quanti descrittori di quel processo puntano a `/dev/dri`."""
    quanti = 0
    try:
        for fd in os.listdir(cartella):
            try:
                if os.readlink(os.path.join(cartella, fd)).startswith("/dev/dri"):
                    quanti += 1
            except OSError:
                continue
    except OSError:
        return 0
    return quanti


def schede_in_tutto():
    """⚠ Si STAMPA e non si giudica: un confronto globale pesterebbe i piedi a
       un altro banco che stesse lavorando nella stessa scatola (fase 10 §7.3)."""
    try:
        elenco = os.listdir("/proc")
    except OSError:
        return None
    return sum(1 for v in elenco
               if v.isdigit() and descrittori_scheda("/proc/%s/fd" % v))


def voci_cartella(percorso):
    try:
        return sorted(os.listdir(percorso))
    except FileNotFoundError:
        return []
    except OSError:
        return None


def conta_file(percorso):
    quanti = 0
    for radice, cartelle, file in os.walk(percorso, onerror=lambda e: None):
        quanti += len(cartelle) + len(file)
        if quanti > 5000:
            return quanti
    return quanti


def file_di_uid(percorso, uid, tetto=2000):
    """Quanti file di quell'uid ci sono sotto `percorso`. ⚠ Solo per stampare."""
    quanti = 0
    for radice, cartelle, file in os.walk(percorso, onerror=lambda e: None):
        for nome in cartelle + file:
            try:
                if os.lstat(os.path.join(radice, nome)).st_uid == uid:
                    quanti += 1
            except OSError:
                continue
            if quanti > tetto:
                return quanti
    return quanti


def raccogli(chi):
    """L'impronta dell'inquilino: {voce: valore-a-stringa}.

    ⛔ Una voce vale `None` **solo** quando non si e' potuto guardare; «non c'e'
       niente» e' `VUOTO`.  ⚠ E' la lezione §1.47 applicata prima del confronto:
       due `None` non sono «uguali», sono **muti**.
    """
    uid = uid_di(chi)
    if uid is None:
        return None
    d = {"_uid": uid}

    nomi, schede, _pid = processi_di(uid)
    d[PROCESSI] = None if nomi is None else (
        " · ".join(nomi) if nomi else VUOTO)
    d[SCHEDA] = None if schede is None else (
        "%d processi" % schede if schede else VUOTO)

    rtd = "/run/user/%d" % uid
    voci = voci_cartella(rtd)
    if voci is None:
        d[RUNTIME] = None
        d[LUCCHETTI] = None
    else:
        d[RUNTIME] = " · ".join(voci) if voci else VUOTO
        lucchetti = [v for v in voci if v.endswith(".lock")]
        d[LUCCHETTI] = " · ".join(lucchetti) if lucchetti else VUOTO

    codice, uscita = corri(["loginctl", "list-sessions", "--no-legend"])
    if codice is None:
        d[SESSIONI] = None
    else:
        # ⚠ Si contano, non si elencano: gli identificativi cambiano a ogni
        #   giro e confrontarli darebbe rosso sempre (§1.49).
        quante = sum(1 for riga in uscita.splitlines()
                     if len(riga.split()) > 2 and riga.split()[2] == chi)
        d[SESSIONI] = "%d" % quante if quante else VUOTO

    stati = []
    for unita in ("user@%d.service" % uid, "user-runtime-dir@%d.service" % uid):
        codice, uscita = corri(["systemctl", "is-active", unita])
        stati.append(None if codice is None else (uscita.strip() or "?"))
    if any(s is None for s in stati):
        d[UNITA] = None
    else:
        # ⭐ «inactive» e «failed» sono tutt'e due «non gira», e un gestore
        #   d'utente che ha fallito NON e' un residuo: e' un'unita' spenta.
        #   ⛔ Se le si distinguesse, il primo giro sporcherebbe il secondo.
        pulito = [("spenta" if s in ("inactive", "failed") else s) for s in stati]
        d[UNITA] = VUOTO if all(s == "spenta" for s in pulito) else " · ".join(pulito)

    d[HOME] = "%d voci" % conta_file("/home/%s" % chi)
    d[TEMPORANEI] = "%d voci" % file_di_uid("/tmp", uid)
    d["_schede in tutto"] = schede_in_tutto()
    return d


# ---------------------------------------------------------------------------
# IL GIUDICE — ⭐ e' una funzione PURA, cosi' `--certifica` puo' provarlo senza
#              toccare niente.
# ---------------------------------------------------------------------------
def differenze(a, b):
    """Le voci giudicate in cui `a` e `b` non dicono la stessa cosa.

    Torna `(diverse, mute)`: ⛔ una voce a cui uno dei due non ha saputo
    rispondere e' **muta**, e non entra nel confronto — perche' `None == None`
    passerebbe senza aver guardato niente (`LEZIONI.md` §1.47).
    """
    diverse, mute = [], []
    for voce in GIUDICATE:
        va, vb = a.get(voce), b.get(voce)
        if va is None or vb is None:
            mute.append(voce)
            continue
        if va != vb:
            diverse.append((voce, va, vb))
    return diverse, mute


def giudica(prima, staccato, dopo, solo_distacco=False,
            ammesso=True, figlio_nato=True):
    """⭐ Il giudizio, tutto qui dentro e senza toccare il mondo.

    Torna `(esito, specie, motivi)`.  `specie` e' una parola per chi legge:
    «residui», «palco sparito», «campo occupato», «non lo so», «regge».
    """
    # ⛔ GUARDIA 1 — il campo dev'essere libero PRIMA.
    sporco = [(v, prima.get(v)) for v in GIUDICATE
              if prima.get(v) not in (None, VUOTO)]
    if sporco:
        return 2, "campo occupato", [
            "l'impronta di PARTENZA non era vuota: %s"
            % ", ".join("%s = %s" % (v, x) for v, x in sporco),
            "⛔ e un residuo che c'era gia' non si mette in conto alla sessione",
        ]

    # ⛔ GUARDIA 2 — il cliente dev'essere stato ammesso.
    # ⭐ TRE stati, e i due «no» portano tutt'e due a 3 ma con parole diverse:
    #   `False` = respinto dal server, `None` = non ha detto niente.
    if ammesso is not True:
        return 3, "non lo so", [
            "il cliente e' stato RESPINTO dal server" if ammesso is False
            else "il cliente non ha detto niente: non so se sia entrato",
            "⇒ non c'e' nessuna sessione di cui giudicare i residui, ⛔ e un "
            "cliente respinto non e' un prodotto rotto"]

    # ⛔ GUARDIA 3 — il registro deve dire che il figlio e' nato.
    if not figlio_nato:
        return 3, "non lo so", ["il registro non nomina nessun figlio di questo "
                                "inquilino: la sessione non e' partita davvero"]

    # ⛔ GUARDIA 4 — se NESSUNA voce sa rispondere non si giudica.
    _d, mute = differenze(prima, staccato)
    if len(mute) == len(GIUDICATE):
        return 3, "non lo so", ["nessuna voce dell'impronta ha saputo "
                                "rispondere: non ho guardato niente"]

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ GIUDIZIO 1 — il distacco NON deve aver portato via il palco (I4).
    #
    # ⛔⛔ E LA DOMANDA E' «IL FIGLIO C'E' ANCORA?», non «e' cambiato qualcosa?».
    #     Vedi `NOME_FIGLIO` in testa: fino al 27 ago 2026 qui c'era solo il
    #     confronto generico, e lo soddisfaceva `systemd` — non il prodotto.
    # ═══════════════════════════════════════════════════════════════════════
    vive, _m = differenze(prima, staccato)
    if not vive:
        return 1, "palco sparito", [
            "dopo il DISTACCO del cliente non e' rimasto niente dell'inquilino,",
            "e l'impronta e' tornata identica a quella di partenza.",
            "⛔ I4 dice che il palco appartiene alla SESSIONE e sopravvive al",
            "   distacco ⇒ o I4 e' rotta, o questa maglia sta guardando la cosa",
            "   sbagliata.  ⚠ In tutt'e due i casi tacere sarebbe peggio: la",
            "   chiusura risulterebbe verde perche' non c'era piu' niente da",
            "   chiudere.",
        ]

    # ⛔ E prima di dire «il figlio non c'e'» bisogna aver potuto guardare i
    #    processi: `None` non e' «non c'e'» (§4.5, domanda 8).
    processi_staccato = staccato.get(PROCESSI)
    if processi_staccato is None:
        return 3, "non lo so", [
            "dopo il distacco l'impronta non ha saputo dire QUALI processi",
            "avesse l'inquilino ⇒ non posso dire se il figlio e' ancora li'.",
            "⛔ E «non lo so» non e' un verde: I4 resta non verificata.",
        ]
    if NOME_FIGLIO not in nomi_processi(processi_staccato):
        return 1, "palco sparito", [
            "dopo il DISTACCO del cliente il figlio «%s» NON c'e' piu' fra i"
            % NOME_FIGLIO,
            "processi dell'inquilino: %s" % processi_staccato,
            "⛔ I4 dice che il palco appartiene alla SESSIONE e sopravvive al",
            "   distacco: qui e' morto col filo ⇒ e' una regressione di I4.",
            "⚠ E il resto dell'impronta e' cambiato lo stesso (%d voci): e'"
            % len(vive),
            "   `systemd` che tiene in piedi la sua roba, ⛔ non il prodotto —",
            "   ed e' precisamente il modo in cui questo giudizio taceva prima",
            "   del 27 ago 2026.",
        ]

    if solo_distacco:
        return 0, "regge", [
            "il cliente si e' staccato e il FIGLIO «%s» e' ancora vivo "
            "(%d voci ancora diverse dalla partenza)" % (NOME_FIGLIO, len(vive)),
            "⭐ e questo NON e' un rosso: e' I4 che fa il suo mestiere",
        ]

    # ⭐ GIUDIZIO 2 — la chiusura non deve aver lasciato niente.
    # ⛔ E se l'impronta finale non si e' fatta leggere affatto, non si giudica:
    #    senza questa riga `differenze(prima, None)` faceva una traccia ⇒ Python
    #    usciva **1** ⇒ il gancio leggeva ROSSO su un guasto del banco (§1.51).
    if dopo is None:
        return 3, "non lo so", [
            "dopo la chiusura l'impronta non si e' fatta leggere affatto:",
            "⛔ non posso dire se sia rimasto qualcosa — e non e' un verde.",
        ]
    residui, _m2 = differenze(prima, dopo)
    if residui:
        return 1, "residui", [
            "la sessione e' stata CHIUSA e %d voci non sono tornate come prima:"
            % len(residui)]
    return 0, "regge", [
        "il distacco ha lasciato in piedi il figlio «%s» (%d voci diverse "
        "dalla partenza), e la chiusura ha rimesso tutte le %d voci giudicate "
        "come le aveva trovate" % (NOME_FIGLIO, len(vive), len(GIUDICATE))]


def guasto_visto(prima, dopo, nome=NOME_INIETTATO):
    """⛔⛔ §1.52 — col guasto innestato non basta il COLORE del verdetto.

    ⚠ Un rosso e' un rosso, ma *«il guasto e' stato visto»* e' un'altra cosa:
      vuol dire che **l'iniezione ha morso**.  Se un giorno la chiusura
      lasciasse un residuo suo, un semplice «rosso ⇒ visto» direbbe che la rete
      sa dare rosso avendo visto un difetto del PRODOTTO — e la certificazione
      della rete poggerebbe su quel difetto.
    ⇒ Si pretende che fra i residui ci sia proprio il processo iniettato.
       ⭐ E' la stessa cura che C9 ha gia' (`LEZIONI.md` §1.52).
    """
    if dopo is None:
        return False
    for voce, _va, vb in differenze(prima, dopo)[0]:
        if voce == PROCESSI and nome in nomi_processi(vb):
            return True
    return False


# ---------------------------------------------------------------------------
# ⛔ LA CERTIFICAZIONE — casi sintetici, e il giudice non tocca il mondo.
# ---------------------------------------------------------------------------
def _impronta(**cambi):
    d = {v: VUOTO for v in GIUDICATE}
    d.update({HOME: "5 voci", TEMPORANEI: "0 voci"})
    d.update(cambi)
    return d


VIVA = _impronta(**{
    PROCESSI: "dbus-daemon · pipewire · remotix · systemd",
    RUNTIME: "bus · pipewire-0 · pipewire-0.lock · systemd",
    LUCCHETTI: "pipewire-0.lock",
    SESSIONI: "2",
    UNITA: "active · active",
    HOME: "9 voci",
})

# ⛔⛔ LA FORMA VERA DELLA REGRESSIONE DI I4, ed e' la ragione della cura del
#     27 ago 2026: il figlio del prodotto muore col filo, ⚠ e **tutto il resto
#     resta in piedi** perche' e' roba di `systemd` e di `logind` — il gestore
#     d'utente, le due sessioni, i socket in `/run/user/<uid>`.
# ⇒ E' identica a `VIVA` tolto `remotix`.  Nient'altro.
SENZA_FIGLIO = _impronta(**{
    PROCESSI: "dbus-daemon · pipewire · systemd",
    RUNTIME: "bus · pipewire-0 · pipewire-0.lock · systemd",
    LUCCHETTI: "pipewire-0.lock",
    SESSIONI: "2",
    UNITA: "active · active",
    HOME: "9 voci",
})


def certifica():
    """⛔ Si dimostra che il giudice sa dire verde, rosso e «non lo so».

    ⚠ E si dichiara che cosa copre: la **decisione**, cioe' il confronto fra
      tre impronte e le quattro guardie.  ⛔ NON copre la RACCOLTA
      dell'impronta — che `/proc` sia letto bene, che `loginctl` risponda.
      Quella parte si certifica solo facendola girare sui dati veri, ed e' il
      giro col guasto innestato.  ⇒ Una certificazione che si dichiara piu'
      larga di quel che e' vale meno di nessuna certificazione (C1).
    """
    vuota = _impronta()
    casi = [
        ("⭐ il giro sano: si apre, si stacca, si chiude, non resta niente",
         dict(prima=vuota, staccato=VIVA, dopo=vuota), (0, "regge")),

        ("⛔ IL GUASTO INNESTATO: un processo dell'inquilino resta",
         dict(prima=vuota, staccato=VIVA,
              dopo=_impronta(**{PROCESSI: "sleep", HOME: "9 voci"})),
         (1, "residui")),

        ("⛔ il socket in XDG_RUNTIME_DIR non e' stato tolto",
         dict(prima=vuota, staccato=VIVA,
              dopo=_impronta(**{RUNTIME: "bus · pipewire-0"})),
         (1, "residui")),

        ("⛔ un lucchetto di PipeWire rimasto per terra",
         dict(prima=vuota, staccato=VIVA,
              dopo=_impronta(**{RUNTIME: "pipewire-0.lock",
                                LUCCHETTI: "pipewire-0.lock"})),
         (1, "residui")),

        ("⛔ ⭐ la scheda grafica NON e' tornata a riposo",
         dict(prima=vuota, staccato=VIVA,
              dopo=_impronta(**{PROCESSI: "remotix", SCHEDA: "1 processi"})),
         (1, "residui")),

        ("⛔ la sessione di loginctl e' rimasta aperta",
         dict(prima=vuota, staccato=VIVA, dopo=_impronta(**{SESSIONI: "1"})),
         (1, "residui")),

        # ⭐⭐ IL CASO CHE QUESTA MAGLIA ESISTE PER NON SBAGLIARE (I4).
        ("⭐ si stacca soltanto: il palco resta ⇒ ⛔ NON e' un rosso",
         dict(prima=vuota, staccato=VIVA, dopo=None, solo_distacco=True),
         (0, "regge")),

        ("⛔ il distacco si e' portato via il palco ⇒ rosso di specie sua",
         dict(prima=vuota, staccato=vuota, dopo=vuota), (1, "palco sparito")),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ I CASI CHE OGGI NON C'ERANO — e sono quelli che avrebbero preso
        #     il difetto del 27 ago 2026 (vedi `NOME_FIGLIO` in testa).
        #
        # ⚠ Il caso di sopra usa `staccato=vuota`: un'impronta TOTALMENTE
        #   vuota, cioe' la forma che l'autore aveva immaginato.  ⛔ Ma la
        #   forma che il guasto avrebbe davvero e' un'altra: il figlio muore
        #   col filo e **tutto il resto resta in piedi**, perche' quel resto
        #   e' di `systemd`.  ⇒ Prima di questa cura, questi tre casi
        #   rispondevano `(0, 'regge')`: C7 diceva VERDE su una I4 rotta.
        # ═══════════════════════════════════════════════════════════════════
        ("⛔⛔ il FIGLIO muore col distacco e systemd resta ⇒ ROSSO (I4)",
         dict(prima=vuota, staccato=SENZA_FIGLIO, dopo=vuota),
         (1, "palco sparito")),

        ("⛔⛔ …e lo dice anche col solo distacco (l'altro modo del gancio)",
         dict(prima=vuota, staccato=SENZA_FIGLIO, dopo=None,
              solo_distacco=True), (1, "palco sparito")),

        ("⛔ un processo che SOMIGLIA al figlio non e' il figlio",
         dict(prima=vuota, staccato=_impronta(**{
             PROCESSI: "dbus-daemon · remotix-cliente · systemd",
             RUNTIME: "bus · pipewire-0 · systemd", SESSIONI: "2",
             UNITA: "active · active", HOME: "9 voci"}), dopo=vuota),
         (1, "palco sparito")),

        # ⛔ `None` non e' «non c'e'»: se `/proc` non si e' fatto leggere non si
        #    puo' dire che il figlio sia morto — e non si puo' nemmeno dire che
        #    sia vivo.  ⚠ Le altre voci parlano, quindi la GUARDIA 4 non scatta.
        ("⛔ i processi non si sono fatti leggere ⇒ «non lo so», ⛔ MAI verde",
         dict(prima=vuota, staccato=_impronta(**{
             PROCESSI: None, RUNTIME: "bus · pipewire-0 · systemd",
             SESSIONI: "2", UNITA: "active · active", HOME: "9 voci"}),
              dopo=vuota), (3, "non lo so")),

        # ⚠ Il rumore dichiarato: la home cresce, ed e' il suo mestiere.
        ("⚠ la home e' cresciuta e /tmp pure ⇒ ⛔ NON e' un residuo",
         dict(prima=vuota, staccato=VIVA,
              dopo=_impronta(**{HOME: "41 voci", TEMPORANEI: "12 voci"})),
         (0, "regge")),

        ("⛔ il campo NON era libero prima di cominciare ⇒ terreno",
         dict(prima=_impronta(**{PROCESSI: "sleep"}), staccato=VIVA, dopo=vuota),
         (2, "campo occupato")),

        ("⛔ il cliente e' stato RESPINTO ⇒ non lo so, e NON e' un rosso",
         dict(prima=vuota, staccato=vuota, dopo=vuota, ammesso=False),
         (3, "non lo so")),

        # ⭐ Il TERZO stato, che prima del 27 ago 2026 non poteva arrivare
        #   qui: il cliente non ha detto niente.  ⛔ Anche questo e' un 3.
        ("⚠ il cliente non ha detto NIENTE (None) ⇒ non lo so, non un rosso",
         dict(prima=vuota, staccato=vuota, dopo=vuota, ammesso=None),
         (3, "non lo so")),

        ("⛔ ammesso ma il figlio non e' nato ⇒ non lo so",
         dict(prima=vuota, staccato=vuota, dopo=vuota, figlio_nato=False),
         (3, "non lo so")),

        # ⛔ L'impronta finale non si e' fatta leggere ⇒ «non lo so», e ⛔ non
        #    una traccia che il gancio leggerebbe come un rosso del prodotto.
        ("⛔ l'impronta DOPO LA CHIUSURA non si e' letta ⇒ «non lo so»",
         dict(prima=vuota, staccato=VIVA, dopo=None), (3, "non lo so")),

        # ⛔ §1.47: «non lo so» uguale a «non lo so» PASSEREBBE il confronto.
        ("⛔ nessuna voce sa rispondere ⇒ non lo so, ⛔ mai verde",
         dict(prima={v: None for v in GIUDICATE},
              staccato={v: None for v in GIUDICATE},
              dopo={v: None for v in GIUDICATE}), (3, "non lo so")),
    ]

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ LA SECONDA META' — «il guasto e' stato visto?» non e' «il verdetto e'
    #    rosso?» (§1.52).  ⛔ Anche questa non c'era prima del 27 ago 2026.
    # ═══════════════════════════════════════════════════════════════════════
    casi_guasto = [
        ("⭐ fra i residui c'e' proprio lo `sleep` iniettato ⇒ VISTO",
         dict(prima=vuota, dopo=_impronta(**{PROCESSI: "sleep"})), True),

        ("⛔ un residuo c'e', ma NON e' quello iniettato ⇒ NON e' «visto»",
         dict(prima=vuota, dopo=_impronta(**{RUNTIME: "bus · pipewire-0"})),
         False),

        ("⛔⛔ un `remotix` rimasto per terra e' un difetto del PRODOTTO,",
         dict(prima=vuota, dopo=_impronta(**{PROCESSI: "remotix"})), False),

        ("⛔ l'impronta finale non si e' fatta leggere ⇒ NON e' «visto»",
         dict(prima=vuota, dopo=None), False),

        ("⛔ non e' rimasto niente ⇒ NON e' «visto»",
         dict(prima=vuota, dopo=vuota), False),
    ]

    print("== certificazione del giudice di C7 ==")
    print("   ⛔ copre la DECISIONE, non la raccolta dell'impronta (vedi in testa)\n")
    guai = 0
    for nome, arg, atteso in casi:
        esito, specie, _motivi = giudica(**arg)
        ok = (esito, specie) == atteso
        print("  %s  %-62s  esito=%s (%s)   atteso %s (%s)"
              % ("OK " if ok else "NO ", nome, esito, specie,
                 atteso[0], atteso[1]))
        if not ok:
            guai += 1
    print()
    print("   ⛔ e il guasto innestato si legge sulla DIFFERENZA, non sul colore:")
    for nome, arg, atteso in casi_guasto:
        avuto = guasto_visto(**arg)
        ok = avuto is atteso
        print("  %s  %-62s  visto=%-5s  atteso %s"
              % ("OK " if ok else "NO ", nome, avuto, atteso))
        if not ok:
            guai += 1
    # ⭐⭐ I CASI DELL'AMMISSIONE — ⛔ quelli che oggi non c'erano.
    #    Il predicato vive in C1 e si certifica coi casi di C1: ⛔ una copia
    #    dei casi qui sarebbe un secondo posto da cui divergere (§1.47).
    print()
    guai_amm, quanti_amm = casa_dell_ammissione().certifica_ammissione("C7")
    guai += guai_amm

    # ⭐⭐ E I CASI DEI GRUPPI DELLA SCHEDA — ⛔ l'altro caso che non c'era:
    #    un inquilino senza i gruppi dei nodi ⇒ «non ho potuto guardare», ⛔
    #    mai rosso.  Vivono in C1 col passo che certificano.
    print()
    guai_gr, quanti_gr = casa_dell_ammissione().certifica_gruppi("C7")
    guai += guai_gr

    quanti = len(casi) + len(casi_guasto) + quanti_amm + quanti_gr
    print()
    if guai:
        print("⛔ il giudice NON e' affidabile: %d casi su %d sbagliati"
              % (guai, quanti))
        return 1
    print("⭐ %d casi su %d: il giudice vede il residuo, ⛔ non chiama residuo un"
          % (quanti, quanti))
    print("   DISTACCO, ⛔ si accorge se il FIGLIO muore col distacco (I4), e non")
    print("   dice verde quando non ha guardato niente.")
    return 0


# ---------------------------------------------------------------------------
def stampa_impronta(titolo, d):
    print("   %s" % titolo)
    for voce in GIUDICATE:
        v = d.get(voce)
        print("     %-34s %s" % (voce, "⛔ non lo so" if v is None else v))
    for voce in STAMPATE:
        print("     %-34s %s   ⚠ stampata, NON giudicata" % (voce, d.get(voce)))
    print("     %-34s %s   ⚠ stampato, NON giudicato"
          % ("processi con /dev/dri, in tutto", d.get("_schede in tutto")))
    print()


def leggi(percorso):
    try:
        with open(percorso, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def sgombera(chi, cancella=True):
    """⭐ Lo sgombero del BANCO, che ⛔ non e' la prova.

    Si chiude l'inquilino di QUESTO giro **per nome**, mai un modello globale
    (fase 10 §7.3).  ⚠ E si fa in un `finally`: un banco che lascia i suoi
    avanzi rende rosso il banco dopo, e quel rosso non e' del prodotto.
    """
    corri(["loginctl", "terminate-user", chi], tempo=30)
    time.sleep(1.0)
    corri(["pkill", "-KILL", "-u", chi], tempo=30)
    time.sleep(0.5)
    if cancella:
        corri(["userdel", "-r", chi], tempo=60)
        corri(["rm", "-rf", "/home/%s" % chi], tempo=30)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente", default="c7u1",
                   help="l'inquilino di prova: si crea NUOVO e si cancella")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--registro", default="/var/lib/rete11/registro.log")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--resta", type=float, default=20.0,
                   help="quanto il cliente resta attaccato")
    p.add_argument("--attesa-palco", type=float, default=45.0,
                   help="quanto si aspetta che il registro nomini il figlio. "
                        "Scaduto: «non lo so», ⛔ MAI verde")
    p.add_argument("--attesa-chiusura", type=float, default=45.0,
                   help="quanto si aspetta che il campo torni libero DOPO la "
                        "chiusura. ⛔ Si aspetta l'EVENTO, e si stampa quanto "
                        "ci ha messo: una chiusura lenta ma completa e' verde")
    p.add_argument("--solo-distacco", action="store_true",
                   help="⭐ il cliente se ne va e la sessione NON si chiude: "
                        "deve restare VERDE (I4)")
    p.add_argument("--lascia-un-processo", action="store_true",
                   help="⛔ il guasto innestato: prima di chiudere si lascia "
                        "apposta un processo dell'inquilino ⇒ deve dare rosso")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if os.geteuid() != 0:
        print("⛔ va eseguita da amministratore: crea e cancella un inquilino")
        sys.exit(2)
    if not os.path.exists(a.cliente):
        print("⛔ non trovo il cliente di prova: %s" % a.cliente)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    if leggi(a.registro) is None:
        print("⛔ non riesco a leggere il registro del server: %s" % a.registro)
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)

    chi = a.utente
    print("== C7 — si chiude tutto, e non resta niente ==")
    print("   inquilino «%s» · porta %d" % (chi, a.porta))
    print("   modo: %s" % (
        "⭐ SOLO DISTACCO — il cliente se ne va e la sessione NON si chiude: "
        "deve restare VERDE (I4)" if a.solo_distacco else
        "⛔ GUASTO INNESTATO — si lascia un processo apposta: deve dare ROSSO"
        if a.lascia_un_processo else "giro normale: si apre, si stacca, si chiude"))
    print()

    # ⛔ SI CANCELLA PRIMA DI CREARLO: «da zero» comprende anche «da zero
    #    rispetto a me stesso di ieri» (`LEZIONI.md` §1.39, e il difetto vero
    #    trovato in C1 il 26 ago 2026).
    sgombera(chi)
    # ⛔ I gruppi della scheda non stanno piu' dentro il `useradd`: li da'
    #    l'attrezzo, che li LEGGE dai nodi `/dev/dri` e poi RILEGGE.
    fatto = subprocess.run(
        ["/bin/sh", "-c",
         "useradd -m -s /bin/bash %s && "
         "printf '%s:%s\n' | chpasswd" % (chi, chi, a.parola)],
        capture_output=True, text=True)
    if fatto.returncode != 0:
        print("⛔ non sono riuscito a creare «%s»: %s"
              % (chi, fatto.stderr.strip()[:120]))
        print("   ⇒ non ho potuto guardare")
        sys.exit(3)
    # ⛔⛔ E SENZA I GRUPPI DELLA SCHEDA NON SI MISURA: `[M]` la sessione nasce
    #     cieca, e i «residui» di una sessione mai nata non dicono niente.
    e_gr, perche_gr = garantisci_i_gruppi(chi)
    if e_gr != 0:
        # ⭐ Si propaga l'esito dell'attrezzo, non un 3 inchiodato: «non ho
        #   potuto guardare» (3) e «uso sbagliato» (2) hanno nomi diversi.
        print("   %s" % perche_gr)
        print("   ⇒ non misuro — ⛔ e NON e' un rosso (§4.5): esito %d" % e_gr)
        sys.exit(e_gr)

    esito = 3
    try:
        prima = raccogli(chi)
        if prima is None:
            print("⛔ l'inquilino «%s» non esiste: ⇒ non ho potuto guardare" % chi)
            sys.exit(3)
        stampa_impronta("IMPRONTA PRIMA — il campo dev'essere libero:", prima)

        # -------------------------------------------------------------------
        # Si segna dove siamo nel registro PRIMA di aprire, cosi' il giudizio
        # guarda solo la fetta di QUESTO giro (come C1).
        segno = len(leggi(a.registro) or "")

        print("   il cliente si attacca e resta %.0f s…" % a.resta)
        tetto_cliente = max(90, a.resta * 4)
        try:
            r = subprocess.run(
                ["python3", a.cliente,
                 "--indirizzo", a.indirizzo, "--porta", str(a.porta),
                 "--utente", chi, "--parola", a.parola, "--resta", str(a.resta)],
                capture_output=True, text=True, timeout=tetto_cliente)
            uscita, errore = (r.stdout or ""), (r.stderr or "")
        except subprocess.TimeoutExpired:
            # ⛔⛔ §1.51 — SENZA QUESTO `except` il banco accusava il prodotto.
            #    `subprocess.TimeoutExpired` non discende da `OSError` e il
            #    `try` di questo blocco ha solo un `finally`: una traccia qui
            #    faceva uscire Python **1**, ⇒ il gancio leggeva **NON REGGE**,
            #    ⇒ §5.2 mandava a riparare un guasto che non era del prodotto.
            #    ⭐ C9 la stessa cosa la catturava gia'; C7 no (27 ago 2026).
            print("   ⛔ il CLIENTE DI PROVA non e' tornato entro %.0f s: si e'"
                  % tetto_cliente)
            print("      piantato lui, e questo e' un guasto del BANCO.")
            print("   ⇒ non ho potuto guardare — ⛔ e NON e' un rosso del "
                  "prodotto (§4.5, §1.51)")
            sys.exit(3)
        # ⛔ NON `"AMMESSO" in uscita`: la parola c'e' anche nei due rifiuti, e
        #    ci arriva sullo stdout — vedi `e_stato_ammesso()` in testa.
        ammesso = e_stato_ammesso(uscita + errore)
        if ammesso is not True:
            # ⛔ «Non ammesso» da solo e' un silenzio: si porta il MOTIVO
            #    accanto al sintomo (la lezione di C1, 26 ago 2026).
            coda = uscita + errore
            motivo = "?"
            for riga in reversed(coda.strip().splitlines()):
                riga = riga.strip()
                if riga and not riga.startswith("=="):
                    motivo = riga[:90]
                    break
            # ⭐ I due «no» si dicono per nome (§1.44: mescolarli e' meta' del
            #   difetto).  ⚠ Tutt'e due portano a **3** nella GUARDIA 2 di
            #   `giudica_residui()`: un cliente respinto non e' un prodotto
            #   rotto.
            print("   ⛔ %s: %s"
                  % ("il cliente e' stato RESPINTO dal server"
                     if ammesso is False else
                     "il cliente non ha detto NIENTE", motivo))

        # ⛔ Si aspetta l'EVENTO — che il registro nomini il figlio — non
        #    l'orologio.  `[M]` 26 ago 2026 in C1: con un'attesa fissa di 1,5 s
        #    sei giri su sei dissero «non lo so» perche' il palco nasce in ~13 s.
        figlio_nato = False
        scadenza = time.time() + a.attesa_palco
        while time.time() < scadenza:
            fetta = (leggi(a.registro) or "")[segno:]
            if any(m.group("chi") == chi for m in FIRMA_FIGLIO.finditer(fetta)):
                figlio_nato = True
                break
            time.sleep(0.5)
        print("   il figlio nel registro: %s"
              % ("⭐ nato" if figlio_nato else "⛔ mai nominato"))

        staccato = raccogli(chi)
        stampa_impronta("IMPRONTA DOPO IL DISTACCO — ⭐ qui il palco DEVE "
                        "essere ancora in piedi (I4):", staccato)

        dopo = staccato
        secondi_chiusura = None
        if not a.solo_distacco:
            if a.lascia_un_processo:
                # ⛔ IL GUASTO INNESTATO, e ha la forma del figlio vero:
                #    un processo che gira come l'inquilino ma pende dal server,
                #    non dalla sua fetta di systemd ⇒ `terminate-user` non lo
                #    porta via (`[M]` 26 ago 2026, misurato prima di scrivere).
                subprocess.Popen(
                    ["/usr/sbin/runuser", "-u", chi, "--", "/bin/sleep", "300"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, start_new_session=True)
                time.sleep(1.5)
                print("   ⛔ guasto innestato: lasciato un `sleep` di «%s» "
                      "fuori dalla sua fetta di systemd\n" % chi)

            print("   si CHIUDE la sessione: loginctl terminate-user %s" % chi)
            partenza = time.time()
            corri(["loginctl", "terminate-user", chi], tempo=60)
            # ⭐ Si aspetta l'EVENTO, e si stampa quanto ci ha messo.  Una
            #   chiusura lenta ma completa e' VERDE: un tetto a orologio
            #   l'avrebbe chiamata rossa (§1.49).
            scadenza = time.time() + a.attesa_chiusura
            tornato = False
            while time.time() < scadenza:
                dopo = raccogli(chi)
                if dopo is not None and not differenze(prima, dopo)[0]:
                    tornato = True
                    break
                time.sleep(0.5)
            secondi_chiusura = time.time() - partenza
            # ⛔⛔ E IL MESSAGGIO SI COSTRUISCE RILEGGENDO IL RISULTATO, non
            #    ricopiando l'intenzione (`LEZIONI.md` §1.48: *«un messaggio di
            #    riuscita che ripete l'intenzione non e' una verifica, e' un
            #    eco»*).  `[M]` 26 ago 2026, primo giro col guasto innestato:
            #    qui c'era scritto **«il campo ci ha messo 45,48 s a tornare
            #    come prima»** ⛔ e il campo non era tornato affatto — era
            #    scaduto il tetto.  ⚠ Il verdetto era giusto lo stesso (rosso),
            #    ma la riga sopra il verdetto diceva una cosa falsa, ed e'
            #    esattamente il genere di riga che poi manda a tarare al buio.
            if tornato:
                print("   ⭐ il campo E' TORNATO come prima in %.2f s "
                      "(tetto dichiarato: %.0f s)\n"
                      % (secondi_chiusura, a.attesa_chiusura))
            else:
                print("   ⛔ il campo NON e' tornato come prima entro il tetto "
                      "dichiarato di %.0f s\n" % a.attesa_chiusura)
            stampa_impronta("IMPRONTA DOPO LA CHIUSURA — qui non deve restare "
                            "niente:", dopo)

        esito, specie, motivi = giudica(
            prima, staccato, dopo, solo_distacco=a.solo_distacco,
            ammesso=ammesso, figlio_nato=figlio_nato)

        # ⛔ §1.47: le voci mute si dichiarano, o passano il confronto senza
        #    aver guardato niente.
        _d, mute = differenze(prima, dopo if dopo is not None else staccato)
        # ⚠ E una voce che dice VUOTO in tutt'e tre le impronte e' «uguale»
        #   senza aver mai parlato: sulla scatola di XFCE e' il caso di
        #   `/dev/dri`, perche' senza compositore nessuno apre la scheda.
        immobili = [v for v in GIUDICATE
                    if prima.get(v) == VUOTO and staccato.get(v) == VUOTO]
        if mute:
            print("⚠ ⛔ %d voci a cui l'impronta non ha saputo rispondere — e"
                  % len(mute))
            print("   «non lo so» uguale a «non lo so» PASSEREBBE il confronto:")
            for v in mute:
                print("     · %s" % v)
            print()
        if immobili:
            print("⚠ %d voci sono rimaste VUOTE anche a sessione viva: hanno"
                  % len(immobili))
            print("   passato il confronto ⛔ senza aver mai avuto niente da dire:")
            for v in immobili:
                print("     · %s" % v)
            print("   ⇒ su questa scatola vale per la scheda grafica finche' la")
            print("     sessione non monta un compositore (§7-bis.13).\n")

        if esito == 1 and specie == "residui":
            residui, _ = differenze(prima, dopo)
            print("⛔⛔ ROSSO — %s" % motivi[0])
            for voce, va, vb in residui:
                print("   · %-34s prima: %s" % (voce, va))
                print("     %-34s dopo : %s" % ("", vb))
            print()
            print("   ⇒ la sessione e' finita e la macchina non e' tornata come")
            print("     l'ha trovata: ⛔ il prossimo inquilino parte su un campo")
            print("     occupato, e il guasto arrivera' altrove.")
        elif esito == 1:
            print("⛔⛔ ROSSO (specie: %s)" % specie)
            for riga in motivi:
                print("   %s" % riga)
        elif esito == 0:
            print("⭐ VERDE — %s" % motivi[0])
            for riga in motivi[1:]:
                print("   %s" % riga)
            if secondi_chiusura is not None:
                print("   ⚠ e ci ha messo %.2f s: e' una MISURA, non un tetto"
                      % secondi_chiusura)
        elif esito == 2:
            print("⛔ TERRENO CATTIVO (esito 2)")
            for riga in motivi:
                print("   %s" % riga)
        else:
            print("⚠ NON GIUDICO (esito 3)")
            for riga in motivi:
                print("   %s" % riga)
            print("   ⛔ E questo non e' un verde: e' un esito suo (§4.5).")

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ COL GUASTO INNESTATO L'ESITO SI LEGGE AL CONTRARIO, e non e' un
        #     vezzo: e' la convenzione del gancio, scritta in `11-gancio.sh`
        #     dentro `esegui_maglia` — *«una maglia col guasto innestato esce 0
        #     quando il guasto E' STATO VISTO»*.  ⇒ Il gancio ne ricava
        #     `ha_visto_il_guasto`, e ⭐ **e' quella chiave che tiene in vita
        #     C13** (*«la certificazione e' recente»*).
        # ⚠ Se C7 uscisse 1 col guasto visto, il gancio scriverebbe
        #   `ha_visto_il_guasto: false` ⛔ e C13 direbbe che la rete non sa piu'
        #   dare rosso proprio nel giro in cui il rosso l'ha dato.
        # ⛔ E si invertono SOLO 0 e 1: il 2 e il 3 non sono giudizi, e un «non
        #   ho guardato» rovesciato diventerebbe un verde inventato.
        # ═══════════════════════════════════════════════════════════════════
        if a.lascia_un_processo and esito in (0, 1):
            print()
            # ⛔⛔ E NON BASTA IL COLORE — §1.52, ed e' la cura del 27 ago 2026.
            #     Un rosso e' un rosso, ma «il guasto e' stato visto» vuol dire
            #     che l'INIEZIONE ha morso: si pretende che fra i residui ci sia
            #     proprio lo `sleep` (vedi `guasto_visto`).
            morso = guasto_visto(prima, dopo)
            if esito == 1 and morso:
                print("⭐ IL GUASTO INNESTATO E' STATO VISTO ⇒ questa maglia SA "
                      "dare rosso")
                print("   ⭐ e il residuo e' proprio lo `%s` iniettato, non un "
                      "difetto che c'era gia' (§1.52)" % NOME_INIETTATO)
                print("   ⚠ e percio' esce **0**: col guasto innestato l'esito "
                      "si legge al contrario (convenzione di 11-gancio.sh)")
                esito = 0
            elif esito == 1:
                print("⛔⛔ ROSSO, ma NON per colpa del guasto: fra i residui non")
                print("    c'e' lo `%s` che avevo iniettato." % NOME_INIETTATO)
                print("    ⇒ o `terminate-user` se l'e' portato via, o il rosso")
                print("      viene da un difetto del PRODOTTO — e certificare la")
                print("      rete su un difetto del prodotto e' §1.52.")
                esito = 1
            else:
                print("⛔⛔ IL GUASTO INNESTATO NON E' STATO VISTO: si e' lasciato "
                      "un processo apposta e l'impronta e' tornata pulita.")
                print("    ⇒ o `terminate-user` se l'e' portato via, o questa "
                      "maglia non guarda nel posto giusto — ⛔ e in tutt'e due i")
                print("      casi non ci si puo' fidare di lei (`LEZIONI.md` §1.44).")
                esito = 1
    finally:
        # ⛔ Chi apre, chiude (`LEZIONI.md` §9-ter): anche col guasto innestato,
        #    e anche se il giudizio e' andato male.
        sgombera(chi)
    sys.exit(esito)


if __name__ == "__main__":
    main()
