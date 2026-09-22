#!/usr/bin/env python3
"""stress_nucleo — IL NUCLEO DELLA SUITE DI STRESS NOTTURNA (fase 14).

    from stress_nucleo import (avvia_browser, conta_dalla_pagina, conta_dal_server,
                               scena, giudica, sgombera, riga_di_esito)

    python3 stress_nucleo.py --certifica          le funzioni pure, e che sappia dare rosso
    python3 stress_nucleo.py --prova-viva         60 s veri su gnome con Firefox

⭐ CHE COS'E'.  Il pezzo condiviso su cui gli scenari e la regia appoggiano: apre
   un browser VERO sul tablet, lo porta dentro una sessione REMOTIX, legge i
   contatori dai due capi della catena (la pagina e il server), giudica con
   regole dichiarate e scrive una riga per giro.  ⛔ Non e' un banco: non ha un
   verdetto suo.  Il verdetto lo danno gli scenari, con `giudica()`.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ DOVE GIRA CIASCUNA COSA — e questo e' il disegno, non un dettaglio
═══════════════════════════════════════════════════════════════════════════════

    tablet (qui)                     macchina di prova 192.168.0.2
    ────────────────                 ─────────────────────────────────────
    questo modulo                    scatola rete11-<desktop>
    Firefox 140 / Chrome 153  ─────▶   server REMOTIX (porta 8511/2/3)
    (finestre VERE, viste)             sessione dell inquilino
                                       la SCENA (un browser dentro il desktop)

⭐ I browser stanno **sul tablet**, cioe' sulla catena vera che l utente guarda
   (`memoria: come-guarda-nic-lo-schermo`): quattro anelli, nessun intermediario.
⛔ E **mai headless**: `[M]` 22 settembre 2026, Firefox headless sotto carico
   riceve tutto e dipinge 277 fotogrammi su 6527 — un giro headless avrebbe
   accusato il prodotto di un difetto del banco.  ⇒ Qui headless non e' una
   bandiera: non c e proprio.
⚠ Il prezzo, dichiarato: le misure vanno fatte **una alla volta**.  Sei browser
  insieme su una N100 con 7,5 GB misurano il tablet, non il prodotto.

═══════════════════════════════════════════════════════════════════════════════
⛔⛔ LE TRAPPOLE GIA' PAGATE — 22 settembre 2026, in un giorno solo
═══════════════════════════════════════════════════════════════════════════════

 1. **Due copie dei banchi.**  Dentro la scatola i banchi girano da
    `/opt/remotix/`, ⛔ non da `/media/REMOTIX/rete11/`.  Aggiornare la seconda
    e provare la prima e' costato piu' di un ora: ogni prova rispondeva sulla
    versione vecchia.  ⇒ Qui dentro la scatola non si copia niente: quel che
    serve si manda **da stdin** a `podman exec -i` (la forma di
    `11-accendi.sh bilancio`), cosi' non c e una seconda copia da tenere
    allineata.
 2. **`pkill -f` pesca se stesso.**  Il guscio `/bin/sh -c` che esegue
    `pkill -f "runuser -u c3u2 "` ha quella stringa nella SUA riga di comando ⇒
    si uccide da solo.  ⇒ `modello_senza_se_stesso()`, che scrive `[c]3u2`.
 3. **Le scene si lanciano con `setsid … < /dev/null`.**  Senza, il browser
    della scena finisce in un gruppo di sfondo e il primo `tcsetattr` se lo
    prende un SIGTTOU: resta in stato `T` dal primo istante, e la scena che
    «non si muove» sembra un difetto del prodotto.
 4. **Marionette vuole le capacita PIATTE.**  `{"capabilities": {"alwaysMatch":
    …}}` da solo viene ignorato da Firefox 140 e il certificato non si accetta:
    `acceptInsecureCerts` va dato anche fuori (`12-client-veri.py`, riga ~660).
    ⇒ Qui il browser lo accende `12-client-veri.py`, che questa cura ce l ha.
 5. ⛔⛔ **UN BROWSER ALLA VOLTA, E I RESIDUI SI TOLGONO.**  `[M]` 22 settembre
    2026, sera: con tre Firefox di prova rimasti vivi (300 MB l uno su un
    tablet da 7,7 GB), `WebDriver:NewSession` **non risponde piu'** — la
    finestra si apre, Marionette dice «Listening on port», e la sessione non
    arriva mai; headless invece rispondeva in 2,3 s.  ⇒ Tolti i residui, lo
    stesso giro e' diventato verde (2249 fotogrammi consegnati e dipinti).
    ⚠ Chi lancia una serie tolga i browser morti fra un giro e l altro:
      `pkill -f "firefox-esr --[m]arionette"` — ⛔ con le parentesi, o il
      comando pesca se stesso (trappola 2).

═══════════════════════════════════════════════════════════════════════════════
⭐ E IL CODICE NON SI DUPLICA (`LEZIONI.md` §1.47)
═══════════════════════════════════════════════════════════════════════════════

 · i guidatori dei browser, il modulo d accesso, il giudice dei pixel:
   `banchi/12-client-veri.py` — importato, non ricopiato;
 · i gruppi della scheda: `attrezzi-gruppi-scheda.sh`, che gia' sta nella
   scatola, chiamato li dentro;
 · la cura della provvista (`~/.cache` propria) e la nascita dell inquilino:
   `11-c1`/`11-c2`/`11-c8`, chiamati **dentro la scatola** dove vivono.
 ⇒ Di mio qui c e solo quel che non esisteva: leggere i contatori dai due capi,
   giudicarli con regole dichiarate, e scrivere la riga del giro.
"""
import argparse
import importlib.util as _iu
import json
import os
import re
import shlex
import socket
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)

HOST = "192.168.0.2"
UTENTE_SSH = "nicfio"
PAROLA_SUDO = "nicfio"
PORTE = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}
ESITI = "/media/REMOTIX/tmp/stress/esiti.jsonl"

VERDE, ROSSO, CIECO = 0, 1, 3


def _carica(nome, file):
    """Un modulo accanto a noi, caricato per percorso (la forma di `12-client-veri`)."""
    s = _iu.spec_from_file_location(nome, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


CLIENTI = None                                    # `12-client-veri.py`, a richiesta


def clienti():
    """⛔ A RICHIESTA, non all importazione: `12-client-veri.py` tira dentro
    `02-pagina-misura-cdp.py` e amici, e la regia lo importa anche solo per
    scrivere una riga di esito."""
    global CLIENTI
    if CLIENTI is None:
        CLIENTI = _carica("client_veri", os.path.join(BANCHI, "12-client-veri.py"))
    return CLIENTI


# ═══════════════════════════════════════════════════════════════════════════
#  LE FUNZIONI PURE — quelle che `--certifica` attraversa
# ═══════════════════════════════════════════════════════════════════════════
def modello_senza_se_stesso(chi):
    """⭐ `c3u2` ⇒ `[c]3u2`: come espressione vale se stesso, come TESTO no.

    ⛔ Serve perche' `pkill -f "<testo>"` prende anche il guscio che sta
       eseguendo quel comando — `[M]` 22 set 2026, il guscio si uccideva a meta'
       del lavoro e il processo da togliere sopravviveva.
    """
    if not chi:
        return chi
    return "[%s]%s" % (chi[0], chi[1:])


def conti_dalla_riga_diario(testo):
    """⭐ I numeri della riga che la pagina manda a `/diario` ogni 5 s.

    E' l unica riga in cui stanno INSIEME l audio, il video e lo scarto A/V
    (`src/pagina.html` ~6437).  ⛔ Si legge quella vera: niente numeri inventati,
    e quel che non c e torna `None` invece di zero — «non lo so» e «zero» sono
    due cose diverse, ed e' la regola di tutto questo progetto.

    Torna `{}` se nel testo non c e nessuna riga `audio: …`.
    """
    righe = [r for r in (testo or "").splitlines() if "audio: ricevuti" in r]
    if not righe:
        return {}
    r = righe[-1]
    c = {}

    def num(nome, chiave=None, dentro=r):
        m = re.search(r"(?<![\w-])" + re.escape(nome) + r"\s+(-?\d+)", dentro)
        c[chiave or nome] = int(m.group(1)) if m else None

    for n in ("ricevuti", "suonati", "BUCHI", "vecchi", "tardivi", "fuori",
              "mancati", "usciti", "tagliati", "sospesi", "salti"):
        num(n, "audio_" + n.lower())
    # ⚠ `video A→B`: A e' quel che il FILO ha portato, B quel che e' arrivato al
    #   vetro.  Se divergono, la distanza dice DOVE si perde (pagina.html ~6463).
    m = re.search(r"video (\d+)→(\d+) salt (\d+) buchi (\d+) ord (\d+) "
                  r"mis (\d+) tard (\d+) err (\S+)", r)
    if m:
        c.update(consegnati=int(m.group(1)), dipinti=int(m.group(2)),
                 salt=int(m.group(3)), buchi=int(m.group(4)),
                 ord=int(m.group(5)), mis=int(m.group(6)), tard=int(m.group(7)),
                 err=(int(m.group(8)) if m.group(8).isdigit() else None))
    m = re.search(r"\bAV (\?|[+-]?\d+)ms", r)
    c["av_ms"] = None if (not m or m.group(1) == "?") else int(m.group(1))
    m = re.search(r"\bdipinti (\d+)", r)
    if m and c.get("dipinti") is None:
        c["dipinti"] = int(m.group(1))
    c["fuoco"] = ("fuoco si" in r) if "fuoco" in r else None
    c["riga"] = r.strip()[:400]
    return c


# ⛔⛔ I MOTIVI CHE SI CONTANO, IN UN POSTO SOLO.
#
# `conti_dal_registro()` guarda **solo** le righe che portano uno di questi
# pezzi, e `conta_dal_server()` fa la stessa scelta DENTRO la scatola con un
# `grep`, per non trascinare 2 MB di registro attraverso il filo a ogni misura.
# ⚠ Sono due letture della stessa lista, e per questo la lista e' UNA: il giorno
#   che si conta un motivo nuovo, chi lo aggiunge qui lo aggiunge a tutt e due —
#   ⛔ se divergessero, il numero calerebbe in silenzio, che e' il modo peggiore
#   in cui un banco puo' sbagliare.
MOTIVI_REGISTRO = [
    "SPEDITO", "RICHIEDI_CHIAVE", "si TENGONO", "LINEA MORTA",
    "sessione aperta utente=", "non e' alla tela in vigore",
    "delta TENUTI", "banda del video", "⛔",
    # ⭐ E LA RIGA DELLA PAGINA, che il server riceve su `/diario` ogni 5 s
    #   (`la pagina di … dice: audio%3A…`).  ⛔ E' l unico posto dove i conti di
    #   chi CONSUMA arrivano comunque: il riquadro della diagnostica nella
    #   pagina e' spento di suo dal 16 agosto 2026, quindi leggerli dal DOM a
    #   volte non si puo' — `[M]` 22 set 2026, `AV=None` dal capo della pagina e
    #   la stessa riga presente nel registro del server.
    "la pagina di",
]


def conti_dal_registro(testo, chi=None):
    """⭐ I fatti del server, contati sulle righe del suo registro.

    ⚠ `chi` filtra per inquilino (`[nome]` in testa alle righe): senza, due
      sessioni nella stessa scatola si sommerebbero e il numero direbbe
      un altra cosa.
    ⚠ Legge il testo che le si da'.  `conta_dal_server()` glielo porta gia'
      tagliato sui `MOTIVI_REGISTRO`: ⛔ quel taglio dev essere un SOVRAINSIEME
      di quel che si conta qui, e la certificazione lo verifica invece di
      fidarsene.
    """
    righe = (testo or "").splitlines()
    if chi:
        marca = "[%s]" % chi
        righe = [r for r in righe if marca in r]
    u = "\n".join(righe)
    spediti = len(re.findall(r"fotogramma \d+ SPEDITO", u))
    chiavi = len(re.findall(r"fotogramma \d+ SPEDITO: CHIAVE", u))
    c = {
        "spediti": spediti,
        "chiavi": chiavi,
        "delta": spediti - chiavi,
        "rc_accolte": len(re.findall(r"RICHIEDI_CHIAVE\([^)]*\) accolta", u)),
        "rc_ignorate": len(re.findall(r"RICHIEDI_CHIAVE\([^)]*\) ignorata", u)),
        "tenuti_dietro_chiave": u.count("si TENGONO"),
        "linee_morte": u.count("LINEA MORTA"),
        "sessioni_aperte": len(re.findall(r"sessione aperta utente=", u)),
        "tela_non_combacia": u.count("non e' alla tela in vigore"),
        "errori_rossi": len([r for r in righe if "⛔" in r]),
    }
    # ⭐ L ultimo riepilogo della soglia (esce alla chiusura della sessione):
    #   `delta TENUTI …, abbandonati per soglia …, e NON ACCETTATI per credito …`
    m = None
    for r in righe:
        x = re.search(r"delta TENUTI (\d+), abbandonati per soglia (\d+), e NON "
                      r"ACCETTATI per credito mancato (\d+)", r)
        if x:
            m = x
    c["soglia_tenuti"] = int(m.group(1)) if m else None
    c["soglia_abbandonati"] = int(m.group(2)) if m else None
    c["credito_mancato"] = int(m.group(3)) if m else None
    bande = [int(x) for x in re.findall(r"banda del video: (\d+) kbit/s", u)]
    c["banda_max_kbit"] = max(bande) if bande else None
    # ⭐ E i conti di chi CONSUMA, che il server riceve su `/diario`: la riga
    #   arriva percento-codificata, si decodifica e si legge con lo stesso
    #   lettore della pagina — ⛔ non un secondo lettore che puo' divergere.
    # ⚠ E si pescano dal testo INTERO, non dalle righe filtrate per inquilino:
    #   il server scrive la riga del diario senza il `[nome]` in testa (porta
    #   l indirizzo di chi l ha mandata, non l utente).  ⛔ Quindi con due
    #   inquilini insieme nella stessa scatola questi numeri non si possono
    #   attribuire: chi misura due sessioni alla volta non li guardi.
    diario = [r for r in (testo or "").splitlines() if "la pagina di" in r]
    if diario:
        try:
            import urllib.parse
            testo_diario = "\n".join(urllib.parse.unquote(r) for r in diario[-4:])
        except Exception:                        # noqa: BLE001
            testo_diario = ""
        for k, v in conti_dalla_riga_diario(testo_diario).items():
            c["pagina_" + k] = v
    return c


def bilancio_in_numeri(riga):
    """`server_pid=1 server_fd=42 …` ⇒ dizionario di numeri (`-` ⇒ None)."""
    c = {}
    for pezzo in (riga or "").split():
        if "=" not in pezzo:
            continue
        k, _, v = pezzo.partition("=")
        if v in ("-", "", "?"):
            c[k] = None
        else:
            try:
                c[k] = int(v)
            except ValueError:
                c[k] = v
    return c


def giudica(pagina, server, regole):
    """⭐⭐ IL GIUDIZIO, e le regole si DICHIARANO da fuori.

    `regole` e' una lista di terzine `(dove, espressione, perche)`:
      · `dove`  «pagina» o «server» — da quale capo si legge il numero;
      · `espressione` una di queste forme, e nessun altra:
            ("almeno",  chiave, n)      il numero dev essere ≥ n
            ("almeno_al_s", chiave, n, secondi)
            ("al_piu",  chiave, n)      il numero dev essere ≤ n
            ("esatto",  chiave, n)
            ("cresce",  chiave)         > 0
      · `perche` la frase che si legge nel verdetto.

    Torna `(esito, perche)` con:
      0  regge        tutte le regole dicono di si
      1  non regge    almeno una dice di no  ⇒ e la prima che dice no e' quella
                      che si legge: le altre sarebbero rumore
      3  non ho potuto guardare — ⛔⛔ **mai rosso** quando il numero manca
                      (`None`): un banco che non ha guardato non accusa nessuno
                      (§1.51, ed e' la regola che tiene in piedi tutta la rete)
    """
    capi = {"pagina": pagina or {}, "server": server or {}}
    for dove, espr, perche in regole:
        capo = capi.get(dove)
        if capo is None:
            return CIECO, "«%s» non e' un capo che conosco (%s)" % (dove, perche)
        forma = espr[0]
        chiave = espr[1]
        if chiave not in capo:
            return CIECO, ("dal capo «%s» manca del tutto «%s»: non ho potuto "
                           "guardare (%s)" % (dove, chiave, perche))
        v = capo.get(chiave)
        if v is None:
            return CIECO, ("«%s» dal capo «%s» non si sa (None): non ho potuto "
                           "guardare (%s)" % (chiave, dove, perche))
        if forma == "almeno":
            if v < espr[2]:
                return ROSSO, "%s: %s=%s, ne volevo almeno %s" % (perche, chiave, v, espr[2])
        elif forma == "almeno_al_s":
            secondi = espr[3]
            if not secondi or secondi <= 0:
                return CIECO, "%s: senza i secondi non calcolo un ritmo" % perche
            al_s = v / float(secondi)
            if al_s < espr[2]:
                return ROSSO, ("%s: %s=%s in %.0f s ⇒ %.2f/s, ne volevo almeno %s/s"
                               % (perche, chiave, v, secondi, al_s, espr[2]))
        elif forma == "al_piu":
            if v > espr[2]:
                return ROSSO, "%s: %s=%s, ne ammettevo al piu' %s" % (perche, chiave, v, espr[2])
        elif forma == "esatto":
            if v != espr[2]:
                return ROSSO, "%s: %s=%s, lo volevo %s" % (perche, chiave, v, espr[2])
        elif forma == "cresce":
            if not v > 0:
                return ROSSO, "%s: %s=%s, e non e' cresciuto" % (perche, chiave, v)
        else:
            return CIECO, "regola «%s» che non conosco (%s)" % (forma, perche)
    return VERDE, "tutte le %d regole reggono" % len(regole)


# ═══════════════════════════════════════════════════════════════════════════
#  IL FILO VERSO LA MACCHINA DI PROVA
# ═══════════════════════════════════════════════════════════════════════════
def _ssh(comando, secondi=180, pty=False):
    """⛔⛔ SENZA pty, e non e' un dettaglio di stile — 22 settembre 2026.

    La ricetta che si usa a mano e' `ssh -tt` piu' la parola sullo stdin, e
    funziona; ⚠ ma un pty fa passare TUTTA l uscita dalla disciplina di linea
    del terminale, che la traduce riga per riga: `[M]` il primo giro vivo di
    questo nucleo e' morto al tetto di 900 s, e il tempo se lo mangiava un
    `cat` di 2 MB di registro attraverso il pty.  ⭐ `sudo -S` legge la parola
    dallo stdin e **non pretende un terminale** (Debian non ha `requiretty`):
    `[M]` provato, `primo=0 secondo=0`.  ⇒ Qui il pty resta un interruttore,
    per il giorno che una macchina lo pretenda, ma non e' piu' la strada.
    """
    v = ["ssh"] + (["-tt"] if pty else []) + ["-o", "BatchMode=yes",
                                              "%s@%s" % (UTENTE_SSH, HOST), comando]
    try:
        r = subprocess.run(v, capture_output=True, text=True, timeout=secondi)
    except subprocess.TimeoutExpired:
        return 124, "", "scaduto dopo %d s" % secondi
    # ⚠ `tput: No value for $TERM` lo scrive il profilo della macchina, non noi.
    pulita = "\n".join(r for r in (r.stdout or "").splitlines()
                       if "tput: No value" not in r and not r.startswith("Connection to "))
    return r.returncode, pulita, (r.stderr or "")[:400]


ASKPASS = "/home/%s/.remotix-askpass" % UTENTE_SSH
_askpass_pronto = False


def _prepara_askpass():
    """⛔⛔ PERCHE' UN AIUTANTE E NON LA PAROLA SULLO STDIN — 22 settembre 2026.

    La macchina di prova ha `Defaults use_pty` in `sudoers`, ⇒ il credito di
    `sudo` **non si conserva** fra un comando e il successivo dello stesso
    collegamento: `[M]` `sudo -n wc -l` passava e il `sudo -n head` subito dopo
    diceva «a password is required».  ⚠ E la parola sullo stdin non si puo'
    usare per il comando vero, perche' lo stdin porta gia' il copione.
    ⇒ `SUDO_ASKPASS` + `sudo -A`: la parola la da' un aiutante, lo stdin resta
      libero, e ogni comando e' indipendente da quello di prima.

    ⚠ L aiutante tiene la parola in chiaro sulla macchina di prova, in un file
      di solo suo (600).  ⛔ Non e' un segreto nuovo: la stessa parola sta gia'
      in nove banchi e in `~/SERVER.ssh` (`memoria: credenziali-da-rigenerare`),
      ed e' la macchina di prova, non una macchina di produzione.  ⭐ Il giorno
      che quella riga sparira' dai banchi, questa sparisce con loro.
    """
    global _askpass_pronto
    if _askpass_pronto:
        return True
    c, u, _ = _ssh("printf '#!/bin/sh\\necho %s\\n' > %s && chmod 700 %s && echo PRONTO"
                   % (PAROLA_SUDO, ASKPASS, ASKPASS), secondi=60, pty=False)
    _askpass_pronto = ("PRONTO" in u)
    return _askpass_pronto


def _sudo(comando, secondi=180):
    """⭐ Un comando da amministratore sulla macchina di prova, con lo stdin libero."""
    if not _prepara_askpass():
        # ⚠ Ripiego dichiarato: la ricetta a mano (pty + parola sullo stdin).
        #   ⛔ Vale per UN comando solo, e va detto invece di scoprirlo dopo.
        return _ssh("printf '%s\\n' | sudo -S -p '' %s" % (PAROLA_SUDO, comando),
                    secondi, pty=True)
    # ⚠ `export`, ⛔ non `VAR=… comando`: con una catena di tubi l assegnazione
    #   davanti vale solo per il PRIMO anello, e il `sudo` che sta in fondo
    #   resterebbe senza aiutante — `[M]` `dentro()` tornava vuoto e in silenzio.
    return _ssh("export SUDO_ASKPASS=%s; %s" % (ASKPASS, comando), secondi)


def dentro(desktop, copione, interprete="sh", argomenti=None, secondi=180):
    """⭐ Un copione ESEGUITO DENTRO la scatola, mandato da stdin.

    ⛔ Cosi' non nasce una seconda copia da tenere allineata: e' la lezione
       piu' cara del 22 settembre 2026 (i banchi in `/opt/remotix` contro quelli
       in `/media/REMOTIX/rete11`).
    ⚠ E il copione viaggia in base64: passa da due gusci (ssh e sh) e qualunque
      apostrofo o virgoletta si perderebbe per strada (`CODER.md` §4-bis).
    ⚠ `argomenti` sta DOPO il `-` che dice «il programma viene da stdin»: e'
      l ordine che `python3` e `sh` pretendono, e metterlo prima li fa leggere
      come nomi di file.
    """
    import base64
    b = base64.b64encode(copione.encode("utf-8")).decode("ascii")
    coda = " ".join(shlex.quote(str(a)) for a in (argomenti or []))
    cmd = ("echo %s | base64 -d | sudo -A podman exec -i rete11-%s %s - %s"
           % (b, desktop, interprete, coda))
    return _sudo(cmd, secondi)


def istante_nella_scatola(desktop):
    """L orologio della scatola in `HH:MM:SS`, che e' come il registro marca le righe."""
    _, u, _ = dentro(desktop, "date -u +%H:%M:%S\n", secondi=60)
    for r in u.splitlines():
        if re.fullmatch(r"\d{2}:\d{2}:\d{2}", r.strip()):
            return r.strip()
    return None


# ═══════════════════════════════════════════════════════════════════════════
#  L INQUILINO E LA SCENA
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ La nascita dell inquilino usa le cure che gia' esistono — i gruppi della
#   scheda dall attrezzo che li LEGGE dai nodi `/dev/dri`, e la provvista di
#   `src/provisiona.sh` — chiamandole DENTRO la scatola, dove vivono.
#   ⛔ Qui non si riscrive nessuna delle due: `usermod -aG video,render` sarebbe
#      due nomi di UNA distribuzione inchiodati in un undicesimo posto.
COPIONE_CREA = r"""
import sys, subprocess, importlib.util, os
chi, parola = sys.argv[1], sys.argv[2]
def sh(c):
    return subprocess.run(["/bin/sh", "-c", c], capture_output=True, text=True)
# da zero comprende da zero rispetto a me stesso di ieri
sh("loginctl terminate-user %s 2>/dev/null; pkill -KILL -u %s 2>/dev/null; "
   "userdel -r %s 2>/dev/null; rm -rf /home/%s" % (chi, chi, chi, chi))
r = sh("useradd -m -s /bin/bash %s && printf '%s:%s\n' | chpasswd" % (chi, chi, parola))
if r.returncode != 0:
    print("NO nascita: " + (r.stderr or "").strip()[:200]); raise SystemExit(1)
g = sh("bash /opt/remotix/attrezzi-gruppi-scheda.sh " + chi)
if g.returncode != 0:
    print("NO gruppi della scheda (%d): %s" % (g.returncode,
          (g.stdout or g.stderr or "").strip().splitlines()[-1:] or "")); raise SystemExit(3)
def carica(nome, file):
    s = importlib.util.spec_from_file_location(nome, file)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
try:
    c8 = carica("c8", "/opt/remotix/11-c8-il-secondo-apre-il-browser.py")
    c8.applica_la_cura(chi)
    if not c8.sa_scrivere_nella_cache(chi):
        print("NO provvista: non sa scrivere in ~/.cache/mozilla"); raise SystemExit(3)
except SystemExit:
    raise
except Exception as e:
    print("NO provvista: " + str(e)[:200]); raise SystemExit(3)
print("SI " + chi)
"""


def crea_inquilino(desktop, chi, parola):
    """⭐ (fatto, perche').  ⛔ Se non si puo' creare **non e' un rosso**: chi
    chiama esce 3 — un inquilino che non nasce non e' un prodotto rotto."""
    c, u, e = dentro(desktop, COPIONE_CREA + "\n", interprete="python3",
                     argomenti=[chi, parola], secondi=240)
    riga = " ".join(u.split())
    if "SI " + chi in u:
        return True, "inquilino «%s» pronto in %s" % (chi, desktop)
    return False, (riga or e or "nessuna risposta")[:300]


# ⭐ LE SCENE.  «pesante» e' la stessa che il 22 settembre 2026 ha fatto uscire
#   la spirale della chiave: rumore casuale a tutto schermo, che e' il caso
#   peggiore per un codificatore (`[M]` 86-264 Mbit/s).  ⛔ Un video di YouTube
#   non andrebbe bene come SCENA DI BANCO: dipende da una rete e da un sito, e
#   una grandezza che dipende da qualcun altro e' una soglia che si sposta senza
#   dirlo (`11-c3-scena.html`, «la scena dichiarata»).
SCENA_PESANTE = r"""<!doctype html><meta charset="utf-8"><title>pesante</title>
<style>html,body{margin:0;height:100%;overflow:hidden;background:#000}
canvas{width:100vw;height:100vh;display:block}</style>
<canvas id="c"></canvas><script>
const c=document.getElementById("c"),x=c.getContext("2d");
function mis(){const f=+(new URLSearchParams(location.search).get("f")||2);
c.width=Math.ceil(innerWidth/f);c.height=Math.ceil(innerHeight/f);}mis();onresize=mis;
let n=0;function g(){const w=c.width,h=c.height,im=x.createImageData(w,h),d=im.data;
for(let i=0;i<d.length;i+=4){const r=Math.random()*255|0;d[i]=r;d[i+1]=(r*7+n)&255;
d[i+2]=(r*13)&255;d[i+3]=255;}
x.putImageData(im,0,0);x.fillStyle="hsl("+(n*3%360)+",90%,50%)";
x.fillRect((n*9)%w,0,w/6,h);n++;requestAnimationFrame(g);}g();
</script>
"""

SCENE = {
    # quale      pagina dentro la scatola                   che cosa e'
    "pesante": ("/opt/remotix/14-scena-pesante.html", "rumore a tutto schermo"),
    "normale": ("/opt/remotix/11-c3-scena.html", "la scena dichiarata di C3"),
    "ferma": (None, "niente: il desktop com e'"),
}


def scena(desktop, quale, chi, secondi=40):
    """⭐ Accende la scena chiesta DENTRO la sessione dell inquilino.

    Torna `(accesa, perche)`.  ⛔ «ferma» non accende niente ed e' un caso
    legittimo: su un desktop fermo zero fotogrammi e' la cosa GIUSTA.

    ⚠ `setsid … < /dev/null` non e' un ornamento: senza, il browser della scena
      finisce in un gruppo di processi di sfondo del terminale che ha lanciato
      il banco e il primo `tcsetattr` se lo prende un SIGTTOU — `[M]` 22 set
      2026, `firefox-esr` in stato `T` dal primo istante, in tutte e tre le
      scatole, e la scena «ferma» che sembrava un difetto del prodotto.
    """
    if quale not in SCENE:
        return False, "scena «%s» che non conosco (%s)" % (quale, ", ".join(SCENE))
    pagina, che_cos_e = SCENE[quale]
    if pagina is None:
        return True, "scena «ferma»: %s" % che_cos_e
    if quale == "pesante":
        import base64
        b = base64.b64encode(SCENA_PESANTE.encode("utf-8")).decode("ascii")
        dentro(desktop, "echo %s | base64 -d > %s\n" % (b, pagina), secondi=60)
    copione = (
        "u=%s\n"
        "rtd=/run/user/$(id -u $u)\n"
        "d=$(ls $rtd 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1)\n"
        "if [ -z \"$d\" ]; then echo NO-SOCKET; exit 3; fi\n"
        "setsid runuser -u $u -- env XDG_RUNTIME_DIR=$rtd WAYLAND_DISPLAY=$d "
        "MOZ_ENABLE_WAYLAND=1 XDG_SESSION_TYPE=wayland HOME=/home/$u "
        "firefox-esr --kiosk file://%s < /dev/null > /home/$u/.scena.log 2>&1 &\n"
        "sleep 2\n"
        "if pgrep -u $u -x firefox-esr > /dev/null; then echo ACCESA; else echo NO-BROWSER; fi\n"
        % (shlex.quote(chi), pagina))
    _, u, e = dentro(desktop, copione, secondi=secondi)
    if "ACCESA" in u:
        return True, "scena «%s» accesa (%s)" % (quale, che_cos_e)
    if "NO-SOCKET" in u:
        return False, ("la sessione di «%s» non ha ancora un socket wayland: "
                       "niente compositore a cui la scena possa parlare" % chi)
    return False, ("la scena non si e' accesa: %s" % (" ".join((u + e).split())[:200]))


def sgombera(desktop, chi):
    """⭐ Toglie l inquilino e tutto il suo, e lo DICE.

    ⛔ Il modello non deve pescare se stesso (`modello_senza_se_stesso`), e il
       `runuser` che fa da padre alla scena e' di **root**: va ripreso prima di
       chiuderlo, o resta fermo in `T` con un figlio zombie — il residuo che il
       22 settembre 2026 e' stato trovato in tutte e tre le scatole.
    """
    m = modello_senza_se_stesso(chi)
    copione = (
        "u=%s\n"
        "loginctl terminate-user $u 2>/dev/null\n"
        "pkill -CONT -f 'runuser -u %s ' 2>/dev/null\n"
        "pkill -CONT -u $u 2>/dev/null\n"
        "sleep 1\n"
        "pkill -KILL -f 'runuser -u %s ' 2>/dev/null\n"
        "pkill -KILL -u $u 2>/dev/null\n"
        "sleep 1\n"
        "id=$(id -u $u 2>/dev/null)\n"
        "userdel -r $u 2>/dev/null || userdel $u 2>/dev/null\n"
        "[ -n \"$id\" ] && systemctl reset-failed user@$id.service 2>/dev/null\n"
        "[ -n \"$id\" ] && find /tmp -maxdepth 1 -uid $id -exec rm -rf {} + 2>/dev/null\n"
        "rm -rf /home/$u\n"
        "resta=$(id -u $u 2>/dev/null || echo no)\n"
        "fermi=$(ps -eo stat= | grep -c '^[TZ]')\n"
        "echo SGOMBERO resta=$resta fermi=$fermi\n"
        % (shlex.quote(chi), m, m))
    _, u, _ = dentro(desktop, copione, secondi=120)
    for r in u.splitlines():
        if r.startswith("SGOMBERO"):
            d = bilancio_in_numeri(r.replace("SGOMBERO ", ""))
            return (d.get("resta") == "no"), r.strip()
    return False, "lo sgombero non ha risposto: %s" % " ".join(u.split())[:200]


# ═══════════════════════════════════════════════════════════════════════════
#  I CONTATORI, DAI DUE CAPI
# ═══════════════════════════════════════════════════════════════════════════
# ⭐ Dalla pagina: i conti VIVI della classe `Schermo` (`src/pagina.html` ~2709)
#   piu' l ultima riga del diario, che e' l unica che porta l audio e lo scarto
#   A/V.  ⛔ I conti dell audio non stanno su `window.REMOTIX`: vivono in una
#   chiusura, e l unico modo onesto di averli e' la riga che la pagina scrive.
JS_CONTI = r"""
const R = window.REMOTIX, s = R && R.schermo, c = s && s.conti;
const reg = document.getElementById('registro');
const e = document.getElementById('esito');
return {
  sessione: !!(s && s.sessione),
  esito: e ? e.textContent : null,
  acceso: document.body ? (document.body.dataset.schermo || null) : null,
  conti: c ? {
    consegnati: c.consegnati, dipinti: c.dipinti, stream: c.stream,
    completi: c.completi, azzerati: c.azzerati, buchi: c.buchi,
    salt: c.saltati_coda, ord: c.scartati_ordine, mis: c.scartati_misura,
    tard: c.tardive, chiavi_chieste: c.chiavi_chieste,
    riconfigurazioni: c.riconfigurazioni, corti: c.corti,
    trattenuti: c.trattenuti, tollerati: c.tollerati
  } : null,
  sospeso: s ? !!s.sospeso : null,
  errori: s && s.errori ? s.errori.slice(-6).map(String) : [],
  registro: reg ? reg.textContent.slice(-8000) : ''
};
"""


def conta_dalla_pagina(browser):
    """⭐⭐ I numeri del capo che CONSUMA — e sono i suoi, non una stima.

    ⛔ `consegnati` e `dipinti` sono due grandezze diverse apposta: la prima e'
       quel che il FILO ha portato, la seconda quel che e' arrivato al vetro.
       `[M]` 22 set 2026, Firefox su KDE sotto carico: 48/s consegnati e 37/s
       dipinti — mille e ottocento fotogrammi spariti dentro il decodificatore,
       senza un errore.  ⇒ Chi guarda solo `dipinti` non vede quel calo, e chi
       guarda solo `consegnati` lo chiama sano.

    Torna un dizionario piatto; ⚠ le chiavi che non si sono potute leggere
    valgono `None`, ⛔ mai zero.
    """
    try:
        s = browser.js(JS_CONTI)
    except Exception as e:                       # noqa: BLE001
        return {"errore_lettura": str(e)[:200], "sessione": None}
    if not isinstance(s, dict):
        return {"errore_lettura": "la pagina non ha risposto un oggetto", "sessione": None}
    fuori = {"sessione": s.get("sessione"), "esito": s.get("esito"),
             "acceso": s.get("acceso"), "sospeso": s.get("sospeso"),
             "errori_pagina": len(s.get("errori") or []),
             "errori_testo": s.get("errori") or []}
    for k, v in (s.get("conti") or {}).items():
        fuori[k] = v
    # ⭐ E l audio e lo scarto A/V dalla riga del diario, che la pagina scrive
    #   ogni 5 s: l unico posto dove i due flussi stanno sulla stessa riga.
    fuori.update({k: v for k, v in conti_dalla_riga_diario(s.get("registro") or "").items()
                  if k not in fuori or fuori.get(k) is None})
    return fuori


def conta_dal_server(desktop, da_istante=None, chi=None):
    """⭐⭐ I numeri del capo che PRODUCE, e la crescita del server.

    `da_istante` (`HH:MM:SS`, l orologio della scatola) taglia il registro:
    senza, si conterebbero anche le sessioni di prima.
    ⚠ La crescita del server la da' `11-accendi.sh bilancio`, che e' gia'
      scritto e diviso per padrone (prodotto ↔ scatola): ⛔ non se ne fa una
      copia qui.
    """
    # ⭐ Si taglia DENTRO la scatola, prima del filo: l orologio per la
    #   finestra, e il `grep` sui motivi che si contano davvero.  `[M]` 22 set
    #   2026: 2 MB di registro trascinati fuori a ogni misura sono il tempo che
    #   ha fatto morire il primo giro vivo al tetto.
    filtro = ""
    if da_istante:
        filtro = (" | awk '$1 >= \"%s\"'" % da_istante)
    copione = ("cat /var/lib/rete11/registro.log%s | grep -aF -e %s\n"
               % (filtro, " -e ".join(shlex.quote(m) for m in MOTIVI_REGISTRO)))
    _, testo, _ = dentro(desktop, copione, secondi=240)
    c = conti_dal_registro(testo, chi)
    _, riga, _ = _sudo("sudo -A bash /media/REMOTIX/rete11/11-accendi.sh bilancio %s"
                       % desktop, secondi=120)
    for r in riga.splitlines():
        if "server_pid=" in r:
            c.update(bilancio_in_numeri(r))
            break
    return c


# ═══════════════════════════════════════════════════════════════════════════
#  IL BROWSER VERO
# ═══════════════════════════════════════════════════════════════════════════
class Browser:
    """⭐ Un browser VERO del tablet, gia' dentro una sessione REMOTIX.

    ⛔ Non reimplementa niente: dietro c e il guidatore di `12-client-veri.py`
       (Marionette per Firefox, DevTools per Chrome), che porta gia' le cure
       pagate — le capacita PIATTE di Firefox 140, il pannello «Procedi» del
       certificato accettato come lo accetta l utente, il raccoglitore degli
       errori.  ⚠ Quel che si aggiunge qui e' la MISURA della finestra e il
       modo di entrare, che gli scenari ripetono decine di volte.
    """

    def __init__(self, guida, marca, porta, url):
        self.g = guida
        self.marca = marca
        self.porta = porta
        self.url = url
        self.palco = guida.palco()

    # -- quel che gli scenari usano ------------------------------------------
    def js(self, corpo, *arg):
        return self.g.js(corpo, *arg)

    def stato(self):
        return self.g.js(clienti().JS_STATO)

    def vai(self, url=None):
        return self.g.vai(url or self.url)

    def ricarica(self):
        return self.g.ricarica()

    def muovi(self, x, y):
        return self.g.muovi(x, y)

    def clic(self, x, y):
        return self.g.clic(x, y)

    def tasto(self, t):
        return self.g.tasto(t)

    def fotografa(self):
        return self.g.fotografa_tela()

    def misura(self, l, a):
        """⭐ La misura della finestra CONTA: e' la «tela» che il client chiede
        (§4.5), ed e' la grandezza con cui il 22 settembre 2026 KDE non ripartiva
        dopo un riavvio del server.  ⇒ Gli scenari la cambiano apposta."""
        try:
            if self.marca == "firefox":
                self.g.m.chiama("WebDriver:SetWindowRect",
                                {"width": int(l), "height": int(a)})
            else:
                b = self.g.cdp.chiama("Browser.getWindowForTarget")
                self.g.cdp.chiama("Browser.setWindowBounds",
                                  windowId=b["windowId"],
                                  bounds={"width": int(l), "height": int(a),
                                          "windowState": "normal"})
            time.sleep(1.0)
            return True, ""
        except Exception as e:                   # noqa: BLE001
            return False, str(e)[:200]

    def apri(self, tetto_s=40):
        """Torna (aperta, perche): la pagina c e ed e' visibile il modulo."""
        aperta, motivo = self.g.vai(self.url)
        if not aperta:
            return False, "la pagina non si apre: %s" % motivo
        fine = time.time() + tetto_s
        m = {}
        while time.time() < fine:
            try:
                m = self.g.js(clienti().JS_MODULO)
            except Exception as e:               # noqa: BLE001
                m = {"errore": str(e)[:160]}
            if m and m.get("modulo") and m.get("pronta") == "complete":
                break
            time.sleep(0.5)
        if not (m or {}).get("modulo"):
            return False, "il modulo d accesso non c e: %s" % json.dumps(m)[:200]
        if not m.get("remotix"):
            return False, "il modulo c e ma `window.REMOTIX` no: lo script si e' fermato"
        return True, "modulo visibile a %s" % m.get("url")

    def entra(self, utente, parola, tetto_s=60):
        """Torna (esito, perche).  ⛔ Un rifiuto e' ROSSO; un collegamento che
        non risponde in tempo e' **3**: non si accusa il prodotto di un tetto."""
        r = self.g.js(clienti().JS_ENTRA, utente, parola)
        if r != "mandato":
            return CIECO, "non ho potuto compilare il modulo: %s" % r
        fine = time.time() + tetto_s
        s = {}
        while time.time() < fine:
            s = self.stato()
            if s.get("sessione") and (s.get("esito") or "").startswith("Ammesso"):
                return VERDE, "«%s»" % s.get("esito")
            if s.get("esito_classe") == "male" and s.get("esito"):
                return ROSSO, "la pagina dice: «%s»" % s.get("esito")
            time.sleep(0.4)
        return CIECO, ("nessuna ammissione in %d s (esito «%s»): non so se e' il "
                       "prodotto o il tetto" % (tetto_s, s.get("esito")))

    def chiudi(self):
        try:
            self.g.chiudi()
        except Exception:                        # noqa: BLE001
            pass


def _porta_libera(base):
    """Una porta che non risponde — ⚠ si PROVA, non si indovina: due giri
    sovrapposti sulla stessa porta di Marionette sono due banchi che si
    pestano i piedi (`memoria: banchi-in-parallelo-isolamento`)."""
    for p in range(base, base + 60):
        s = socket.socket()
        try:
            s.bind(("127.0.0.1", p))
            return p
        except OSError:
            continue
        finally:
            s.close()
    return clienti().porta_vuota()


def avvia_browser(marca, porta, misura=(1600, 1000), tetto_s=40):
    """⭐⭐ Apre il browser VERO e lo porta fino al modulo d accesso.

    `porta` e' la porta del SERVER (8511/8512/8513), non quella del browser:
    quella se la sceglie libera da se'.  ⛔ E la finestra e' sempre VERA: qui
    headless non c e, e la ragione sta in testa a questo file.

    Torna un `Browser`; solleva se il browser non si accende — chi chiama lo
    legge come **3**, non come un rosso.
    """
    C = clienti()
    if marca not in ("firefox", "chrome"):
        raise ValueError("browser «%s»: qui ci sono firefox e chrome" % marca)
    url = "https://%s:%d/" % (HOST, porta)
    p = _porta_libera(2860 if marca == "firefox" else 9360)
    guida = (C.GuidaFirefox(p, True) if marca == "firefox" else C.GuidaChrome(p, True))
    b = Browser(guida, marca, porta, url)
    if misura:
        b.misura(*misura)
    return b


# ═══════════════════════════════════════════════════════════════════════════
#  LA RIGA DEL GIRO
# ═══════════════════════════════════════════════════════════════════════════
def riga_di_esito(scenario, desktop, browser, esito, perche, pagina=None,
                  server=None, secondi=None, extra=None, dove=ESITI):
    """⭐⭐ UNA RIGA, SCRITTA APPENA IL GIRO FINISCE.

    ⛔ Non alla fine della notte: se alle tre qualcosa si inchioda, tutto quel
       che e' gia' stato misurato dev essere gia' su disco.  ⚠ E si scrive sulla
       macchina di prova, non sul tablet: la suite gira di la', e un risultato
       che vive solo nella sessione di chi l ha lanciata e' un risultato che si
       perde con la sessione.

    Torna la riga (dizionario), anche quando non si e' potuta scrivere: ⛔ un
    esito che non si riesce a salvare non si butta, si dice.
    """
    riga = {
        "quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "scenario": scenario, "desktop": desktop, "browser": browser,
        "esito": esito,
        "verdetto": {VERDE: "REGGE", ROSSO: "NON REGGE",
                     CIECO: "non ho potuto guardare"}.get(esito, "esito %s" % esito),
        "perche": perche, "secondi": secondi,
        "pagina": pagina or {}, "server": server or {},
    }
    if extra:
        riga.update(extra)
    testo = json.dumps(riga, ensure_ascii=False, default=str)
    import base64
    b = base64.b64encode((testo + "\n").encode("utf-8")).decode("ascii")
    c, _, e = _sudo("sudo -A mkdir -p %s && echo %s | base64 -d | sudo -A tee -a %s > /dev/null"
                    % (shlex.quote(os.path.dirname(dove)), b, shlex.quote(dove)),
                    secondi=90)
    riga["_scritta"] = (c == 0)
    if c != 0:
        print("⚠ la riga di esito NON si e' potuta scrivere in %s: %s" % (dove, e))
        print("RIGA " + testo, flush=True)
    return riga


# ═══════════════════════════════════════════════════════════════════════════
#  LA CERTIFICAZIONE — ⛔ prima si prova che sa dire di NO
# ═══════════════════════════════════════════════════════════════════════════
GUAI = 0
QUANTE = 0


def prova(nome, ottenuto, atteso):
    global GUAI, QUANTE
    QUANTE += 1
    bene = ottenuto == atteso
    if not bene:
        GUAI += 1
    print("  %s  %-64s %s" % ("OK " if bene else "NO ", nome,
                              "" if bene else "⇒ %r (volevo %r)" % (ottenuto, atteso)))


DIARIO_VERO = (
    "12:34:56 qualcosa\n"
    "audio: ricevuti 573 suonati 568 BUCHI 0 vecchi 0 tardivi 0 fuori 0 rec 0 "
    "dop 0 pieni 0 errori 0 mancati 34 volte 2 usciti 563 tagliati 5 sospesi 5 "
    "salti 34 risv 0 coda 0ms usc 40ms aoff -1802061 ctx running | tasti 16 "
    "ultimo Enter classico si schermo acceso dipinti 146 video 190→146 salt 44 "
    "buchi 2 ord 0 mis 0 tard 0 err 0 voff -1802061 AV +73ms fuoco si\n")

REGISTRO_VERO = (
    "10:41:43.007 rcp     [prova] sessione aperta utente=prova via=[192.168.0.3]:1 tela=100x100\n"
    "10:41:44.100 rcp     [prova] fotogramma 1 SPEDITO: CHIAVE 0x0301, codec 3, 100x100\n"
    "10:41:44.200 rcp     [prova] fotogramma 2 SPEDITO: delta 0x0302, codec 3, 100x100\n"
    "10:41:44.300 rcp     [altro] fotogramma 9 SPEDITO: delta 0x0302, codec 3, 100x100\n"
    "10:41:45.000 rcp     [prova] RICHIEDI_CHIAVE(ultimo_numero=2) accolta (§5.2)\n"
    "10:41:45.100 rcp     [prova] ⚠ TOLLERANZA DICHIARATA: RICHIEDI_CHIAVE(ultimo_numero=1) ignorata\n"
    "10:41:46.000 rcp     [prova] ⭐ la coda del video e' sopra la soglia ma c'e' la CHIAVE 3 "
    "davanti: i 2 delta dietro di lei si TENGONO\n"
    "10:41:47.000 wt      [prova] ⛔ [192.168.0.3]:1: LINEA MORTA — la connessione QUIC si chiude\n"
    "10:41:48.000 video   [prova] banda del video: 12193 kbit/s su 10013 ms\n"
    "10:41:49.000 rcp     [prova] ⭐ FASE 9, la soglia della coda video: ACCESA (100 ms) — "
    "delta TENUTI 180, abbandonati per soglia 13, e NON ACCETTATI per credito mancato 0\n")


def certifica():
    print("\n══ stress_nucleo — la certificazione ═══════════════════════════════")
    print("\n── il modello che non pesca se stesso ──")
    prova("c3u2 ⇒ [c]3u2", modello_senza_se_stesso("c3u2"), "[c]3u2")
    prova("⛔ e il modello NON si riconosce nel proprio testo",
          bool(re.search(modello_senza_se_stesso("c3u2"),
                         "pkill -f runuser -u %s " % modello_senza_se_stesso("c3u2"))), False)
    prova("⭐ ma riconosce il processo vero",
          bool(re.search(modello_senza_se_stesso("c3u2"), "runuser -u c3u2 -- env X")), True)
    prova("⚠ una stringa vuota non rompe niente", modello_senza_se_stesso(""), "")

    print("\n── la riga del diario della pagina ──")
    d = conti_dalla_riga_diario(DIARIO_VERO)
    prova("⭐ consegnati e dipinti sono DUE numeri diversi",
          (d.get("consegnati"), d.get("dipinti")), (190, 146))
    prova("buchi", d.get("buchi"), 2)
    prova("salt (saltati dalla coda del decodificatore)", d.get("salt"), 44)
    prova("audio ricevuti", d.get("audio_ricevuti"), 573)
    prova("⭐ lo scarto A/V col segno", d.get("av_ms"), 73)
    prova("il fuoco della finestra", d.get("fuoco"), True)
    prova("⛔ senza riga del diario torna vuoto, ⛔ non zeri",
          conti_dalla_riga_diario("nessuna riga qui"), {})
    prova("⛔ `AV ?` ⇒ None, e non 0",
          conti_dalla_riga_diario("audio: ricevuti 1 suonati 1 AV ?ms").get("av_ms"), None)
    prova("⚠ una riga TRONCA: quel che c e si legge, il resto e' None",
          (conti_dalla_riga_diario("audio: ricevuti 7 suonati 7").get("audio_ricevuti"),
           conti_dalla_riga_diario("audio: ricevuti 7 suonati 7").get("consegnati")),
          (7, None))
    prova("⭐ si legge l ULTIMA riga, non la prima",
          conti_dalla_riga_diario(DIARIO_VERO + "audio: ricevuti 999 suonati 9\n")
          .get("audio_ricevuti"), 999)

    print("\n── i fatti dal registro del server ──")
    r = conti_dal_registro(REGISTRO_VERO, "prova")
    prova("⭐ spediti solo dell inquilino chiesto (l altro non entra)", r["spediti"], 2)
    prova("di cui chiavi", r["chiavi"], 1)
    prova("delta", r["delta"], 1)
    prova("RICHIEDI_CHIAVE accolte", r["rc_accolte"], 1)
    prova("⛔ e quelle IGNORATE, che sono un altra cosa", r["rc_ignorate"], 1)
    prova("delta tenuti dietro una chiave", r["tenuti_dietro_chiave"], 1)
    prova("linee morte", r["linee_morte"], 1)
    prova("abbandonati per soglia (dall ultimo riepilogo)", r["soglia_abbandonati"], 13)
    prova("banda massima vista", r["banda_max_kbit"], 12193)
    prova("⚠ senza filtro si contano tutti e due gli inquilini",
          conti_dal_registro(REGISTRO_VERO)["spediti"], 3)
    prova("⛔ un registro vuoto: zero spediti ma soglia «non lo so»",
          (conti_dal_registro("")["spediti"], conti_dal_registro("")["soglia_abbandonati"]),
          (0, None))
    # ⛔⛔ IL TAGLIO DENTRO LA SCATOLA NON DEVE MANGIARE NIENTE.  `conta_dal_server`
    #     porta fuori solo le righe coi `MOTIVI_REGISTRO`: se un motivo
    #     mancasse, il numero CALEREBBE IN SILENZIO — il modo peggiore in cui un
    #     banco puo' sbagliare.  ⇒ Si conta due volte, prima e dopo il taglio, e
    #     si pretende lo stesso risultato.
    tagliato = "\n".join(r for r in REGISTRO_VERO.splitlines()
                         if any(m in r for m in MOTIVI_REGISTRO))
    # ⭐ La riga del diario, come arriva al server: percento-codificata.
    diario_srv = ("10:41:50.000 pagina  📄 la pagina di 192.168.0.3:1 dice: "
                  "audio%3A%20ricevuti%20573%20suonati%20568%20BUCHI%200%20"
                  "video%20190%E2%86%92146%20salt%2044%20buchi%202%20ord%200%20"
                  "mis%200%20tard%200%20err%200%20AV%20%2B73ms\n")
    r2 = conti_dal_registro(REGISTRO_VERO + diario_srv, "prova")
    prova("⭐ i conti della PAGINA letti dal registro del server (consegnati)",
          r2.get("pagina_consegnati"), 190)
    prova("⭐ e lo scarto A/V, che dal DOM a volte non si puo' leggere",
          r2.get("pagina_av_ms"), 73)
    prova("⚠ senza righe del diario non ci sono chiavi «pagina_» inventate",
          [k for k in conti_dal_registro(REGISTRO_VERO).keys() if k.startswith("pagina_")], [])
    prova("⭐ il taglio dentro la scatola da' gli STESSI numeri del registro intero",
          conti_dal_registro(tagliato, "prova"), conti_dal_registro(REGISTRO_VERO, "prova"))
    prova("⛔ e se un motivo sparisse, il taglio si accorgerebbe (controllo negativo)",
          conti_dal_registro("\n".join(r for r in REGISTRO_VERO.splitlines()
                                       if "SPEDITO" not in r), "prova")["spediti"], 0)

    print("\n── il bilancio della scatola ──")
    b = bilancio_in_numeri("server_pid=42 server_fd=91 server_rss_kb=- inquilini=2")
    prova("i numeri", (b["server_pid"], b["server_fd"], b["inquilini"]), (42, 91, 2))
    prova("⛔ il trattino e' «non lo so», ⛔ non zero", b["server_rss_kb"], None)

    print("\n── ⛔⛔ IL GIUDICE, e prima si prova che sa dire di NO ──")
    pag = {"consegnati": 1000, "dipinti": 900, "buchi": 3, "err": 0, "sessione": True}
    srv = {"spediti": 1100, "linee_morte": 0, "soglia_abbandonati": 0}
    prova("⭐ tutte le regole reggono ⇒ 0",
          giudica(pag, srv, [("pagina", ("cresce", "dipinti"), "dipinge"),
                             ("pagina", ("al_piu", "buchi", 10), "pochi buchi"),
                             ("server", ("esatto", "linee_morte", 0), "nessuna caduta")])[0],
          VERDE)
    prova("⛔ un numero oltre il tetto ⇒ 1",
          giudica(pag, srv, [("pagina", ("al_piu", "buchi", 2), "pochi buchi")])[0], ROSSO)
    prova("⛔ un numero sotto il minimo ⇒ 1",
          giudica(pag, srv, [("pagina", ("almeno", "dipinti", 5000), "abbastanza")])[0], ROSSO)
    prova("⛔ un ritmo troppo basso ⇒ 1",
          giudica(pag, srv, [("pagina", ("almeno_al_s", "dipinti", 60, 190), "ritmo")])[0],
          ROSSO)
    prova("⭐ lo stesso ritmo, ma preteso basso ⇒ 0",
          giudica(pag, srv, [("pagina", ("almeno_al_s", "dipinti", 4, 190), "ritmo")])[0],
          VERDE)
    prova("⛔ un contatore che non e' cresciuto ⇒ 1",
          giudica({"dipinti": 0}, srv, [("pagina", ("cresce", "dipinti"), "dipinge")])[0],
          ROSSO)
    prova("⚠ un numero che NON SI SA (None) ⇒ 3, ⛔ mai rosso",
          giudica({"dipinti": None}, srv, [("pagina", ("cresce", "dipinti"), "dipinge")])[0],
          CIECO)
    prova("⚠ una chiave che manca del tutto ⇒ 3, ⛔ mai rosso",
          giudica({}, srv, [("pagina", ("cresce", "dipinti"), "dipinge")])[0], CIECO)
    prova("⚠ un capo che non esiste ⇒ 3",
          giudica(pag, srv, [("luna", ("cresce", "dipinti"), "?")])[0], CIECO)
    prova("⚠ una forma di regola che non conosco ⇒ 3",
          giudica(pag, srv, [("pagina", ("piu_o_meno", "dipinti", 3), "?")])[0], CIECO)
    prova("⚠ i secondi a zero in un ritmo ⇒ 3, ⛔ non una divisione per zero",
          giudica(pag, srv, [("pagina", ("almeno_al_s", "dipinti", 1, 0), "ritmo")])[0],
          CIECO)
    prova("⭐ nessuna regola ⇒ 0 (e lo dice)", giudica(pag, srv, [])[0], VERDE)
    prova("⛔ il PRIMO no e' quello che si legge",
          "pochi buchi" in giudica(pag, srv,
                                   [("pagina", ("al_piu", "buchi", 2), "pochi buchi"),
                                    ("pagina", ("almeno", "dipinti", 99999), "tanti")])[1],
          True)

    print("\n── le scene dichiarate ──")
    prova("⛔ una scena che non conosco non si accende", scena("gnome", "lunare", "x")[0], False)
    prova("⭐ «ferma» e' una scena legittima: non accende niente",
          scena("gnome", "ferma", "x"), (True, "scena «ferma»: niente: il desktop com e'"))

    print("\n── le forme che il nucleo pretende ──")
    prova("le tre porte dei desktop", (PORTE["gnome"], PORTE["kde"], PORTE["xfce"]),
          (8511, 8512, 8513))
    prova("⛔ un browser che non esiste si rifiuta subito",
          _errore_di(lambda: avvia_browser("safari", 8511)), True)

    print("\n%s  %d prove, %d guai"
          % ("⭐ IL NUCLEO SA DIRE DI NO, e lo dice per la ragione giusta."
             if GUAI == 0 else "⛔ QUALCOSA NON TORNA.", QUANTE, GUAI))
    print("⚠ e questa certificazione copre LE FUNZIONI PURE: la catena viva la "
          "prova `--prova-viva`, che e' un altra cosa e va fatta sul ferro.")
    return 1 if GUAI else 0


def _errore_di(f):
    try:
        f()
        return False
    except Exception:                            # noqa: BLE001
        return True


# ═══════════════════════════════════════════════════════════════════════════
#  LA PROVA VIVA — ⛔ «uno script nuovo si esegue almeno una volta» (CODER §4-bis)
# ═══════════════════════════════════════════════════════════════════════════
def prova_viva(desktop="gnome", marca="firefox", secondi=60, quale_scena="normale",
               chi="stressviva", parola="stressviva"):
    print("\n══ prova viva: %s · %s · scena «%s» · %d s ═══════════"
          % (desktop, marca, quale_scena, secondi))
    porta = PORTE[desktop]
    b = None
    t0 = time.time()
    esito, perche = CIECO, "non sono arrivato in fondo"
    pagina, server = {}, {}
    try:
        fatto, dice = crea_inquilino(desktop, chi, parola)
        print("   inquilino: %s" % dice)
        if not fatto:
            return riga_di_esito("prova-viva", desktop, marca, CIECO,
                                 "inquilino non nato: %s" % dice)
        da = istante_nella_scatola(desktop)
        print("   orologio della scatola: %s" % da)
        b = avvia_browser(marca, porta)
        print("   palco: %s" % b.palco)
        aperta, dice = b.apri()
        print("   pagina: %s" % dice)
        if not aperta:
            esito, perche = CIECO, dice
        else:
            e, dice = b.entra(chi, parola)
            print("   accesso: %s %s" % (e, dice))
            if e != VERDE:
                esito, perche = (e if e != ROSSO else ROSSO), dice
            else:
                # la sessione grafica nasce adesso: la scena aspetta il compositore
                for _ in range(30):
                    ok, dice = scena(desktop, quale_scena, chi)
                    if ok:
                        break
                    time.sleep(2)
                print("   scena: %s" % dice)
                time.sleep(secondi)
                pagina = conta_dalla_pagina(b)
                server = conta_dal_server(desktop, da, chi)
                print("   pagina: consegnati=%s dipinti=%s buchi=%s salt=%s AV=%s"
                      % (pagina.get("consegnati"), pagina.get("dipinti"),
                         pagina.get("buchi"), pagina.get("salt"), pagina.get("av_ms")))
                print("   server: spediti=%s chiavi=%s rc=%s/%s linee_morte=%s fd=%s"
                      % (server.get("spediti"), server.get("chiavi"),
                         server.get("rc_accolte"), server.get("rc_ignorate"),
                         server.get("linee_morte"), server.get("server_fd")))
                esito, perche = giudica(pagina, server, [
                    ("pagina", ("cresce", "consegnati"), "il filo porta fotogrammi"),
                    ("pagina", ("cresce", "dipinti"), "e arrivano al vetro"),
                    ("server", ("cresce", "spediti"), "il server ne ha spediti"),
                    ("server", ("esatto", "linee_morte", 0), "il filo non e' caduto"),
                ])
                print("   giudizio: %s — %s" % (esito, perche))
    except Exception as e:                       # noqa: BLE001
        esito, perche = CIECO, "il nucleo e' caduto: %r" % e
        print("   ⛔ %s" % perche)
    finally:
        if b is not None:
            b.chiudi()
        tolto, dice = sgombera(desktop, chi)
        print("   sgombero: %s (%s)" % ("pulito" if tolto else "⚠ resta roba", dice))
    riga = riga_di_esito("prova-viva", desktop, marca, esito, perche, pagina, server,
                         round(time.time() - t0, 1))
    print("   riga scritta in %s: %s" % (ESITI, riga.get("_scritta")))
    return riga


def main():
    p = argparse.ArgumentParser(description="il nucleo della suite di stress")
    p.add_argument("--certifica", action="store_true",
                   help="le funzioni pure, e che sappia dare rosso")
    p.add_argument("--prova-viva", action="store_true",
                   help="un giro vero e corto, sul ferro")
    p.add_argument("--desktop", default="gnome")
    p.add_argument("--browser", default="firefox")
    p.add_argument("--secondi", type=int, default=60)
    p.add_argument("--scena", default="normale", choices=sorted(SCENE))
    o = p.parse_args()
    if o.certifica:
        return certifica()
    if o.prova_viva:
        r = prova_viva(o.desktop, o.browser, o.secondi, o.scena)
        return 0 if r["esito"] == VERDE else (1 if r["esito"] == ROSSO else 3)
    p.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())
