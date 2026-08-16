#!/usr/bin/env python3
"""01-b10-secondo-utente.py — B10: un utente DIVERSO da chi possiede il processo entra.

    python3 01-b10-secondo-utente.py --bersaglio prodotto --porta 7491 \\
        --utente prova2 --parola-file /srv/src/tmp/sera-b10-parola \\
        --pid-server 1234 --registro-server /srv/src/b10-prodotto-filo.log \\
        --socket-comando /srv/src/tmp/sera-b10.sock

⛔ Gira DENTRO il contenitore: gli utenti, la pila PAM e `pamtester` stanno
   li'.  Chi lo accende e' `01-b10-lancia.sh`, che sta fuori.

---------------------------------------------------------------------------
⛔ CHE COSA PROVA, E PERCHE' ESISTE

`SPECIFICHE.md` §5.5 vuole un servizio **di sistema** che serve piu' utenti.
La versione di v1 di `autenticazione.c` chiamava `autenticazione_utente_atteso()`
— il nome ricavato dall'uid effettivo del processo — e **rifiutava chiunque
altro prima di interpellare PAM**.  Era giusto in v1, dove il server girava
dentro la sessione di una persona; qui contraddice il multi-tenant.

⚠ E il sintomo di quel difetto e' la sua parte cara: un server che funziona
  **solo per chi lo ha avviato** e che a tutti gli altri dice «credenziali
  errate».  ⛔ La diagnosi punta sulla parola d'ordine mentre il difetto e' una
  riga di guardia — la forma che `LEZIONI.md` §1.9 chiama la piu' costosa.

---------------------------------------------------------------------------
⛔ «NON ENTRA» HA QUATTRO CAUSE, E UN BANCO CHE NE NOMINA UNA MANDA A CERCARE
   NEL POSTO SBAGLIATO — rilievo R3.26, `LEZIONI.md` §1.6

  (1) ⛔ **la guardia e' ancora li'** — il difetto che questo banco esiste per
      vedere.  Il rifiuto nasce PRIMA di PAM;
  (2) il **contatore per indirizzo** di §4.4-bis e' nella sua finestra (B0.3):
      il server rifiuta senza interrogare PAM, e il motivo sul filo e'
      `TROPPI_TENTATIVI(0x08)`, non `CREDENZIALI_ERRATE(0x07)`;
  (3) la **pila PAM non consente al processo di verificare la parola di un
      altro utente**: e' il caso di `pam_unix` quando il processo non e' root —
      `unix_chkpwd` verifica solo il proprio utente;
  (4) il **secondo utente non esiste** o non ha una parola d'ordine
      utilizzabile in `/etc/shadow`.

⭐ E le quattro si distinguono con **tre osservazioni**, che questo banco fa
   tutte e stampa tutte:

  | osservazione | dove si legge |
  |---|---|
  | l'utente c'e' e ha una parola cifrata | `getent passwd` · `getent shadow` |
  | la stessa parola funziona FUORI dal server | `pamtester <servizio> <utente> authenticate` |
  | PAM e' stato INTERROGATO dal server | le righe che `autenticazione.c` scrive su stderr, nel registro del server |

  ⛔ La terza e' quella che separa (1) da tutto il resto: con la guardia
     addosso, `rcp_autentica()` ritorna `false` **senza chiamare `pam_start`**,
     quindi nel registro del server non compare ne' «PAM ha RIFIUTATO» ne'
     «PAM NON HA POTUTO GIUDICARE» per quell'utente — mentre `pamtester`, con
     la stessa parola e lo **stesso servizio**, riesce.

---------------------------------------------------------------------------
⭐ IL CONTROLLO CHE COSTA DIECI SECONDI — e il servizio PAM e' `remotix`

Prima di credere al rosso si verifica che la parola funzioni fuori dal server.
⚠ **Sullo stesso servizio PAM**: il prodotto usa `remotix` (`src/remotix.pam`,
`SPECIFICHE.md` §4.2), non `login`.  Un `pamtester login …` verde direbbe che
funziona una pila che il server non usa — e su Debian `login` e' la pila della
console locale, con `pam_securetty` dentro.

⭐ E lo strumento ha il suo controllo negativo: `pamtester` con una parola
   sbagliata **deve fallire**.  Senza, «pamtester dice di si'» non vale niente
   (`LEZIONI.md` §1.9, seconda regola).

---------------------------------------------------------------------------
⛔ CHI POSSIEDE IL PROCESSO SI LEGGE E SI SCRIVE, NON SI SUPPONE

Il banco si definiva «un utente diverso da quello che possiede il processo»
**senza dire chi sia**.  Qui il proprietario si legge da `/proc/<pid>/status`
(campo `Uid:`, l'uid **effettivo**, che e' quello su cui la guardia di v1
ragionava) e finisce stampato e nel registro dei fatti.

⛔ E c'e' un controllo di VACUITA' che vale quanto la prova: se il server
   girasse **come l'utente della prova**, questo banco sarebbe verde per
   costruzione e non proverebbe niente.  In quel caso esce 2 — «non ho potuto
   misurare» — invece di stampare un verde che non significa nulla.

---------------------------------------------------------------------------
⛔ LA PAROLA D'ORDINE NON STA SULLA RIGA DI COMANDO — compromesso NON accettato

`FASI.md` §01-filo-nudo, «quel che resta storto»: i banchi prendono la parola
sulla riga di comando, quindi finisce in `ps`.  Per `parola-di-prova` e' un
compromesso dichiarato; ⛔ **per la parola generata di `prova2` non lo e'**.

⭐ Qui la parola arriva da un **file** (`--parola-file`), che il lanciatore
   scrive con un builtin della shell — quindi nemmeno la scrittura passa per un
   processo — con permessi `0600`, e cancella in fondo.  ⚠ Il banco lo
   verifica: se il file e' leggibile da altri, lo DICE.

⚠ E `--parola-sbagliata` sulla riga di comando c'e' apposta: quella non e' un
  segreto di nessuno, ed e' l'unica che si puo' leggere in `ps` senza danno.

---------------------------------------------------------------------------
⛔ LE REGOLE DI B0 CHE QUESTO BANCO DEVE

  B0.1  lo stato iniziale si dichiara **e si verifica**: gli utenti, la loro
        parola in `/etc/shadow`, il file del servizio PAM, il proprietario del
        processo, e il file dei ban (che il lanciatore butta prima di
        accendere);
  B0.3  ⛔ **questo banco autentica, quindi banna**.  Fa tentativi FALLITI
        (il controllo che dice no), e chiama lo sblocco — dichiarandolo, con
        il `PING` come denominatore.  Il file dei ban e il socket sono suoi:
        `sera-b10-ban` e `sera-b10.sock`;
  B0.4  l'atteso lo confronta il banco, e lo stato d'uscita e' quello del
        confronto: **0** tutto come atteso · **1** almeno una prova ha dato
        altro · **2** non si e' potuto misurare (e non e' un verde);
  B0.5  dopo il tentativo fallito il server dev'essere **ancora li'**: l'ultima
        prova e' una connessione nuova che arriva fino a `SESSIONE`;
  B0.6  la versione si annota: qui non c'e' un browser, e quel che invecchia
        sono `aioquic`, l'impronta del binario misurato e il servizio PAM.
        Finiscono tutti nel registro dei fatti;
  B0.7  marcatori, non `sleep`: il registro del server si legge da un
        **offset** preso prima di ogni prova, cosi' quel che si conta e' di
        questo tentativo e non di quello di ieri.

---------------------------------------------------------------------------
⛔ E IL SECONDO LETTORE NON SI RISCRIVE

La stretta di mano la fa `01-b3-cliente.py`, importato come modulo — non
copiato.  ⭐ Cosi' B10 misura RCP con **lo stesso secondo lettore** di B3 e di
B9, e il giorno in cui quello cambia lettura, cambia anche qui.
⚠ Si importa invece di lanciarlo come processo per una ragione precisa: il suo
  `--parola` finirebbe in `ps`.
"""
import argparse
import asyncio
import contextlib
import importlib.util
import io
import json
import os
import pwd
import re
import shutil
import socket
import subprocess
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"
NETTO = "\033[1m"

# ⛔ LA MARCA DEL GUASTO DI B12 — e non e' una parola qualsiasi.
#
#    `01-b12-guasti.py` pretende che l'uscita del banco ROSSO contenga una
#    stringa che nel giro SANO non compare mai: senza, un rosso per una
#    compilazione fallita si conterebbe come «il banco ha visto il guasto»
#    (rilievo R12-A.3, che ha invalidato la certificazione di B7 e di B4).
#
# ⭐ Questa riga la stampa **soltanto** la diagnosi della causa (1), cioe' il
#    caso in cui il server ha rifiutato senza interrogare PAM mentre pamtester
#    con la stessa parola riesce.  Le altre tre cause hanno altre marche, e
#    l'elenco descrittivo qui sopra usa parole diverse apposta.
MARCA_CAUSA_1 = "CAUSA-1-GUARDIA-PRE-PAM"
MARCA_CAUSA_2 = "CAUSA-2-CONTATORE-PER-INDIRIZZO"
MARCA_CAUSA_3 = "CAUSA-3-PILA-PAM-ALTRO-UTENTE"
MARCA_CAUSA_4 = "CAUSA-4-UTENTE-SENZA-PAROLA"
# ⛔ E una quinta marca, che NON e' una causa del server: e' un difetto di
#    QUESTO file.  Sta separata dalle quattro apposta — `REVIEWER.md` §4 vieta
#    di mescolare quel che si e' misurato con quel che non si e' potuto
#    misurare, e un banco che non sa piu' leggere il registro non ha misurato
#    niente.  ⚠ Non e' la marca del guasto di catalogo: quella resta
#    `MARCA_CAUSA_1`, e le due non devono potersi confondere.
MARCA_ANCORA_ROTTA = "ANCORA-AL-REGISTRO-ROTTA"

# Le righe che `autenticazione.c` scrive su stderr, e che finiscono nel
# registro del server.  ⛔ Sono la prova che PAM E' STATO INTERROGATO.
RIGA_PAM_RIFIUTA = "PAM ha RIFIUTATO"
RIGA_PAM_INCERTA = "PAM NON HA POTUTO GIUDICARE"
RIGA_PAM_START = "pam_start"
# ===========================================================================
# ⛔⭐ LA RIGA DEL VERDETTO DI `rcp.c`, E PERCHE' QUI C'ERA UN'ANCORA GIA' CIECA
# ===========================================================================
# *Curata il 12 agosto 2026.  ⛔ Non ha mai prodotto un rosso — e questo e'
#  esattamente il motivo per cui e' la piu' insidiosa delle tre trovate oggi.*
#
# La riga che `rcp.c` scrive dopo aver chiamato la funzione di verifica.  ⚠ NON
# distingue (1) dal resto: c'e' anche quando la guardia rifiuta prima di PAM,
# perche' `rcp.c` non sa che cosa faccia dentro `rcp_autentica()`.
#
# ⛔ QUI C'ERA UNA SOTTOSTRINGA COI DUE PUNTI ATTACCATI:
#
#       RIGA_RCP_VERDETTO = "PAM ha risposto:"
#
#    e la si usava cosi': `if RIGA_RCP_VERDETTO in coda: ok(...)`.
#
#    La cura di `DECISIONI.md` §1.10 ha infilato **il numero di pratica fra
#    «risposto» e i due punti** (`rcp.c:2636`), e da quel momento la
#    sottostringa non combacia piu'.  ⛔ E siccome era il guardiano di un `if`
#    **senza ramo `else`**, quel che si e' rotto non e' diventato rosso: e'
#    diventato **niente**.  La conferma *«e il registro del server lo dice»* ha
#    semplicemente **smesso di stamparsi, in silenzio**, e B10 ha continuato a
#    uscire verde con un controllo in meno.
#
# ⛔ E' la forma **E8** di `REVIEWER.md` §2 — «vuoto» e «proibito» hanno lo
#    stesso aspetto — nella sua veste peggiore: un controllo che **sparisce
#    senza dirlo**.  ⚠ Un falso rosso costa un'ora e si nota; un controllo che
#    si spegne non costa niente **finche' non serve**, e allora costa il difetto
#    che doveva vedere.  Fra i due, questo e' il piu' caro.
#
# ⭐ LE TRE FORME VERE, e non sono immaginate: `[M]` 12 agosto 2026, lette con
#    `grep` nei registri veri sul server (`/media/REMOTIX/src/*.log` e
#    `tmp/*.log`), prodotto e innesto:
#
#      1.  «PAM ha risposto: ammesso»
#          — il prodotto PRIMA di §1.10 (ancora vivo sulla 7448 stamattina);
#      2.  «PAM ha risposto: ammesso  ⚠ (per via SINCRONA: nessun gancio
#           asincrono collegato — il filo e' rimasto fermo)»
#          — `rcp.c:1555`, la strada sincrona: l'INNESTO e i banchi in-processo;
#      3.  «PAM ha risposto (pratica 1): respinto  ⭐ e il filo non si e' mai
#           fermato (DECISIONI.md §1.10)»
#          — `rcp.c:2636`, la strada asincrona: il PRODOTTO allineato di oggi.
#
#    ⛔ La vecchia sottostringa combacia con 1 e 2 e **non** con 3, cioe' e'
#       cieca proprio sul server che B10 misura adesso.
#
# ⭐ LA FORMA CHE REGGE — la stessa gia' in casa in `01-b8-cronometro.py` e in
#    `01-p5-registro.py`: si ancora al **pezzo stabile** — il nome del fatto
#    («PAM ha risposto») e la parola che lo qualifica («ammesso»/«respinto») —
#    e si lascia libero **tutto quel che sta in mezzo e tutto quel che viene
#    dopo**.  Un numero di pratica, una spiegazione appesa in coda, un'emoji, un
#    secondo campo: nessuno di questi la tocca.
#
# ⛔ E SONO DUE APPIGLI, NON UNO, perche' sono due fatti diversi:
#      · `RIGA_RCP_VERDETTO`  «questa e' una riga di PAM»;
#      · `R_RCP_VERDETTO`     «e so leggerne il verdetto».
#    *«Non e' una riga di PAM»* e *«e' una riga di PAM che non so leggere»* non
#    devono avere la stessa faccia: la seconda e' un difetto **di questo file**,
#    e va detta a voce alta invece di essere arrotondata alla prima.
RIGA_RCP_VERDETTO = "PAM ha risposto"
R_RCP_VERDETTO = re.compile(r"PAM ha risposto\b[^:]*:\s*(ammesso|respinto)\b")


def verdetto_nel_registro(coda):
    """(stato, verdetto, quante) — ⛔ e gli stati sono TRE, non due.

        `assente`      nessuna riga di PAM in questa coda — non si sa niente,
                       e «non ho potuto guardare» non si arrotonda a un no;
        `illeggibile`  la riga c'e' e l'appiglio non la apre — ⛔ e' un difetto
                       DEL BANCO, ed e' il caso che il 12 agosto 2026 e' passato
                       inosservato perche' non aveva un nome;
        `letto`        e allora il verdetto e' «ammesso» o «respinto».

    ⚠ Si tiene l'**ultimo** verdetto della coda: la coda parte dal marcatore
      preso prima del tentativo (`coda_registro`), quindi le righe che ci sono
      dentro sono di questo giro — ma un P1-bis dopo uno sblocco ne aggiunge
      una seconda, e quella che conta e' l'ultima.
    """
    righe = [r for r in coda.splitlines() if RIGA_RCP_VERDETTO in r]
    if not righe:
        return "assente", None, 0
    letti = [m.group(1) for m in map(R_RCP_VERDETTO.search, righe) if m]
    if not letti:
        return "illeggibile", None, len(righe)
    return "letto", letti[-1], len(righe)


# ===========================================================================
# ⛔⭐ IL CONTROLLO POSITIVO DELL'ANCORA — e non e' un guasto, e' il suo rovescio
# ===========================================================================
# *Nato il 12 agosto 2026, dallo stesso difetto che ha accecato B8.*
#
# ⛔ PERCHE' NESSUN GUASTO LO AVREBBE MAI TROVATO.  Il guasto di catalogo di
#    B10 — rimettere la guardia di v1 — chiede al banco di diventare **rosso**.
#    Un'ancora rotta rende il banco rosso o muto, mai verde-quando-doveva-essere
#    rosso: ⇒ un'ancora fragile **passa il guasto di catalogo** e la
#    certificazione dice «B10 vede» mentre B10 ha un occhio chiuso.  E' la
#    ragione per cui questo difetto ha attraversato indenne ogni giro finora.
#
# ⭐ Quindi si costruisce il contrario di un guasto: si danno all'appiglio le
#    righe **vere** — quelle lette nei registri del prodotto e dell'innesto — e
#    quelle che gli si allungheranno addosso domani, e si pretende che l'esito
#    **non cambi**.  ⚠ E' il controllo positivo di `REVIEWER.md` §1 punto 5
#    applicato al lettore del registro: «lo strumento sa ancora trovare quel che
#    c'e' di sicuro?»
#
# ⛔ E HA ANCHE LA META' NEGATIVA, o non proverebbe niente: due righe che NON
#    devono farsi leggere come un verdetto.  Un appiglio che dicesse «ammesso»
#    a tutto passerebbe la prima meta' a occhi chiusi.
CASI_ANCORA = [
    # (che riga, stato atteso, verdetto atteso)
    ("il prodotto PRIMA di §1.10 — la forma nuda (7448, [M] 12 ago)",
     "12:48:55.369 rcp     PAM ha risposto: ammesso",
     "letto", "ammesso"),
    ("la strada SINCRONA, rcp.c:1555 — l'innesto e i banchi in-processo",
     "12:48:55.369 rcp     PAM ha risposto: ammesso  ⚠ (per via SINCRONA: "
     "nessun gancio asincrono collegato — il filo e' rimasto fermo)",
     "letto", "ammesso"),
    # ⛔ E' QUESTA la riga su cui l'appiglio vecchio era cieco.
    ("la strada ASINCRONA, rcp.c:2636 — il PRODOTTO allineato di oggi",
     "16:35:48.273 rcp     PAM ha risposto (pratica 2): ammesso  ⭐ e il filo "
     "non si e' mai fermato (DECISIONI.md §1.10)",
     "letto", "ammesso"),
    ("la stessa, col verdetto opposto: «respinto» dev'essere letto «respinto», "
     "non arrotondato",
     "16:34:03.401 rcp     PAM ha risposto (pratica 1): respinto  ⭐ e il filo "
     "non si e' mai fermato (DECISIONI.md §1.10)",
     "letto", "respinto"),
    # ⚠ La riga che NON esiste ancora: il campo in piu' che qualcuno aggiungera'
    #   in mezzo, esattamente come «(pratica N)» e' stato aggiunto in mezzo.
    ("⏳ un SECONDO campo in mezzo, che oggi non c'e' e domani ci sara'",
     "16:35:48.273 rcp     PAM ha risposto (pratica 2, aiutante 3): ammesso  "
     "⭐ e il filo non si e' mai fermato",
     "letto", "ammesso"),
    # ── ⛔ la meta' negativa: qui l'appiglio DEVE dire di no ────────────────
    ("⛔ una riga di PAM SENZA verdetto: dev'essere «illeggibile», mai un "
     "verdetto inventato",
     "16:35:48.273 rcp     PAM ha risposto (pratica 2): boh",
     "illeggibile", None),
    ("⛔ una riga che non parla di PAM: dev'essere «assente», che non e' "
     "«illeggibile»",
     "16:35:48.273 rcp     CREDENZIALI ricevute utente=prova2",
     "assente", None),
]


def controllo_positivo_ancora():
    """⭐ (falliti, quanti) — e stampa riga per riga che cosa ha guardato.

    ⛔ Gira a OGNI esecuzione di B10, prima di qualunque misura, e non e' una
       cerimonia: un controllo che si esegue solo quando qualcuno se lo ricorda
       e' un controllo che il giorno che serve non c'era.  Costa microsecondi e
       non tocca ne' il server ne' PAM ne' il conto di §4.4-bis.
    """
    titolo("A0 — ⭐ il CONTROLLO POSITIVO dell'appiglio al registro del server")
    inf("le righe vere del prodotto e dell'innesto, piu' quelle che gli si")
    inf("allungheranno addosso: l'esito NON deve cambiare (REVIEWER.md §1.5)")
    falliti = 0
    for che, riga, stato_atteso, verdetto_atteso in CASI_ANCORA:
        stato, verdetto, _ = verdetto_nel_registro(riga)
        buono = (stato == stato_atteso and verdetto == verdetto_atteso)
        if buono:
            ok(f"{che}  ⇒ {stato}"
               + (f"/{verdetto}" if verdetto else ""))
        else:
            falliti += 1
            ko(f"{che}")
            ko(f"   atteso «{stato_atteso}"
               + (f"/{verdetto_atteso}" if verdetto_atteso else "")
               + f"», ottenuto «{stato}"
               + (f"/{verdetto}" if verdetto else "") + "»")
            ko(f"   riga: {riga[:110]}")
    if falliti:
        ko(f"⛔ L'APPIGLIO AL REGISTRO E' ROTTO: {falliti} casi su "
           f"{len(CASI_ANCORA)}.")
        ko("   ⛔ Finche' questa riga e' rossa, un verde di B10 non vale: la")
        ko("      conferma «il registro del server lo dice» puo' essere sparita")
        ko("      IN SILENZIO, che e' quel che e' successo il 12 agosto 2026")
        ko(f"   ⇒ {MARCA_ANCORA_ROTTA}")
    else:
        ok(f"⭐ tutte e {len(CASI_ANCORA)} — l'appiglio regge alle tre forme "
           f"vere, all'aggiunta di domani, e dice di no alle due righe che "
           f"non portano un verdetto")
    return falliti, len(CASI_ANCORA)


def ok(t):
    print(f"    {VERDE}OK{GRIGIO}  {t}")


def ko(t):
    print(f"    {ROSSO}NO{GRIGIO}  {t}")


def inf(t):
    print(f"    --  {t}")


def dub(t):
    print(f"    {GIALLO}??{GRIGIO}  {t}")


def titolo(t):
    print(f"\n{NETTO}== {t}{GRIGIO}")


# ===========================================================================
# Gli strumenti, e ciascuno distingue TRE esiti: si' · no · non ho potuto
# guardare.  ⛔ «Non ho potuto guardare» non si arrotonda a nessuno dei due.
# ===========================================================================
def esegui(argomenti, dentro=None, attesa=60):
    """(uscita, testo).  uscita None = non si e' potuto eseguire."""
    try:
        p = subprocess.run(argomenti, input=dentro, capture_output=True,
                           text=True, timeout=attesa)
    except (OSError, subprocess.SubprocessError) as e:
        return None, f"{type(e).__name__}: {e}"
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def proprietario_del_processo(pid):
    """(nome, uid, come) del proprietario EFFETTIVO del processo.

    ⛔ Si legge l'uid **effettivo** e non il reale: la guardia di v1 chiamava
       `geteuid()`, ed e' quello il numero su cui ragionava.  Un banco che
       leggesse l'uid reale direbbe il nome giusto per caso su un server
       normale e quello sbagliato su un server che lascia i privilegi.
    """
    try:
        with open(f"/proc/{pid}/status", encoding="utf-8") as f:
            for riga in f:
                if riga.startswith("Uid:"):
                    parti = riga.split()
                    uid_eff = int(parti[2])          # reale, EFFETTIVO, salvato, fs
                    try:
                        nome = pwd.getpwuid(uid_eff).pw_name
                    except KeyError:
                        nome = f"(uid {uid_eff} senza nome)"
                    return nome, uid_eff, f"/proc/{pid}/status campo Uid:"
    except OSError as e:
        return None, None, f"⛔ non si e' potuto leggere: {e}"
    return None, None, f"⛔ /proc/{pid}/status non porta il campo Uid:"


def utente_utilizzabile(nome):
    """(esiste, ha_parola, spiegazione).  ⛔ None = non ho potuto guardare."""
    u, testo = esegui(["getent", "passwd", nome])
    if u is None:
        return None, None, f"⛔ `getent` non si e' potuto eseguire: {testo}"
    if u != 0:
        return False, False, f"`getent passwd {nome}` non lo trova"
    riga_passwd = testo.strip().splitlines()[0]
    u2, testo2 = esegui(["getent", "shadow", nome])
    if u2 is None:
        return True, None, f"c'e' ({riga_passwd}) — ⛔ shadow non letto: {testo2}"
    if u2 != 0 or ":" not in testo2:
        return True, None, (f"c'e' ({riga_passwd}) — ⛔ `getent shadow` non "
                            f"risponde: PAM potrebbe non poter giudicare")
    cifrata = testo2.split(":")[1]
    # ⚠ Un `!` o un `*` in testa sono un conto BLOCCATO, e un campo vuoto e'
    #   «nessuna parola»: tutt'e tre fanno rifiutare PAM, e nessuno dei tre e'
    #   «parola sbagliata».
    buona = bool(cifrata) and cifrata.startswith("$")
    return True, buona, (f"c'e' · parola in /etc/shadow: "
                         f"{'cifrata (' + cifrata[:3] + '…)' if buona else '⛔ ' + repr(cifrata[:3])}")


def pamtester(servizio, utente, parola, come=None):
    """(riuscito, spiegazione).  ⛔ None = lo strumento non c'era.

    `come` = (uid, gid) per provare **da un altro utente**: e' la misura di
    R3.26, la pila PAM per un utente diverso dal proprietario del processo.
    """
    if not shutil.which("pamtester"):
        return None, "⛔ `pamtester` non e' installato: il controllo non si e' fatto"
    cmd = ["pamtester", servizio, utente, "authenticate"]
    if come is not None:
        if not shutil.which("setpriv"):
            return None, "⛔ `setpriv` non c'e': non ho potuto scendere di privilegi"
        cmd = ["setpriv", f"--reuid={come[0]}", f"--regid={come[1]}",
               "--clear-groups"] + cmd
    u, testo = esegui(cmd, dentro=parola + "\n", attesa=30)
    if u is None:
        return None, f"⛔ non si e' potuto eseguire: {testo}"
    return u == 0, f"uscita {u} · {testo.strip().splitlines()[-1] if testo.strip() else '(muto)'}"


def coda_registro(percorso, da):
    """Il pezzo di registro del server scritto DOPO il marcatore `da`.

    ⛔ B0.7: non si dorme e non si legge tutto il file — si prende la lunghezza
       prima della prova e si legge da li'.  Cosi' «PAM e' stato interrogato»
       parla di QUESTO tentativo e non di uno di ieri.
    """
    try:
        with open(percorso, "rb") as f:
            f.seek(da)
            return f.read().decode("utf-8", "replace")
    except OSError as e:
        return f"⛔ registro del server non letto ({e})"


def lunghezza(percorso):
    try:
        return os.path.getsize(percorso)
    except OSError:
        return 0


def sblocca(sock, indirizzo, perche):
    """⛔ Lo sblocco si chiama E SI DICHIARA — B0.3.

    Restituisce (esito, testo): `TOLTO`, `NON-BANNATO`, oppure None se non si
    e' potuto parlare col server.  ⚠ E il `PING` e' il denominatore: senza,
    «il ban non e' scattato» e «lo sblocco non e' arrivato a nessuno» hanno la
    stessa faccia.
    """
    def parla(comando):
        try:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            s.settimeout(5)
            s.connect(sock)
            s.sendall(comando.encode() + b"\n")
            r = s.recv(256).decode("utf-8", "replace").strip()
            s.close()
            return r
        except OSError as e:
            return f"⛔ {type(e).__name__}: {e}"

    pong = parla("PING")
    if not pong.startswith("PONG"):
        inf(f"⛔ PING al comando di sblocco: «{pong}» — e senza PING questo "
            f"sblocco non e' un fatto")
        return None, pong
    r = parla(f"SBLOCCA {indirizzo}")
    inf(f"⛔ SBLOCCO DICHIARATO (B0.3) · indirizzo {indirizzo} · perche': "
        f"{perche} · risposta: {r}")
    return r, r


# ===========================================================================
# La stretta di mano, con il secondo lettore di RCP — importato, non copiato.
# ===========================================================================
def carica_cliente():
    percorso = os.path.join(QUI, "01-b3-cliente.py")
    spec = importlib.util.spec_from_file_location("b3cliente", percorso)
    if spec is None or spec.loader is None:
        return None, f"⛔ non si e' potuto caricare {percorso}"
    modulo = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(modulo)
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        return None, f"⛔ {type(e).__name__}: {e}"
    return modulo, percorso


def stretta(cliente, a, utente, parola, registra=None):
    """(esito, motivo, testo) di una stretta di mano intera.

    esito:  'SESSIONE' e' arrivata · 'RIFIUTO' il server ha detto no (motivo
    riempito) · 'GUASTO' qualcos'altro e' andato storto (motivo = il tipo).
    ⛔ L'uscita del cliente si CATTURA e si stampa indentata: e' la traccia da
       cui si legge dove si e' fermata la stretta di mano.
    """
    import argparse as _ap
    ns = _ap.Namespace(indirizzo=a.indirizzo, porta=a.porta, percorso="/rcp/1",
                       utente=utente, parola=parola,
                       larghezza=1920, altezza=1080, disposizione="it",
                       registra=registra, resta=0, segnale=None)
    buf = io.StringIO()
    t0 = time.monotonic()
    try:
        with contextlib.redirect_stdout(buf):
            uscita = asyncio.run(cliente.principale(ns))
        testo = buf.getvalue()
        ms = (time.monotonic() - t0) * 1000
        if uscita == 0 and "SESSIONE:" in testo:
            return "SESSIONE", f"{ms:.0f} ms", testo
        return "GUASTO", f"il cliente e' uscito {uscita} senza SESSIONE", testo
    except RuntimeError as e:
        testo = buf.getvalue()
        m = re.search(r"motivo (0x[0-9a-f]{2}) = ([A-Z_]+)", str(e))
        if m:
            return "RIFIUTO", f"{m.group(2)} ({m.group(1)})", testo + f"\n   {e}"
        return "GUASTO", f"RuntimeError: {e}", testo + f"\n   {e}"
    except Exception as e:  # noqa: BLE001
        return "GUASTO", f"{type(e).__name__}: {e}", buf.getvalue()


def stampa_traccia(testo):
    for riga in testo.strip().splitlines():
        print(f"        {riga}")


# ===========================================================================
# ⛔ LA DIAGNOSI: una causa NOMINATA, e le altre tre escluse per iscritto.
# ===========================================================================
def diagnosi(motivo, coda, pam_root, utente_ok, parola_ok, falliti_del_giro):
    """Stampa la causa e restituisce la sua marca."""
    print()
    ko("⛔ IL SECONDO UTENTE NON E' ENTRATO.  Le cause possibili sono quattro,")
    ko("   e questo banco le distingue invece di nominarne una sola (R3.26):")

    pam_interrogata = (RIGA_PAM_RIFIUTA in coda or RIGA_PAM_INCERTA in coda
                       or RIGA_PAM_START in coda)

    # ── (4) l'utente non c'e' o non ha parola ──────────────────────────────
    if utente_ok is not True or parola_ok is not True:
        ko(f"   ⇒ {MARCA_CAUSA_4}: il secondo utente non esiste o non ha una")
        ko("      parola d'ordine utilizzabile in /etc/shadow.  ⛔ Non e' un")
        ko("      difetto del server: e' il terreno.")
        return MARCA_CAUSA_4

    # ── (2) il contatore per indirizzo ─────────────────────────────────────
    if motivo and "TROPPI_TENTATIVI" in motivo:
        ko(f"   ⇒ {MARCA_CAUSA_2}: il motivo sul filo e' TROPPI_TENTATIVI(0x08),")
        ko("      cioe' §4.4-bis: il server ha rifiutato SENZA interrogare PAM")
        ko("      perche' l'indirizzo e' nella finestra del ban (B0.3).")
        ko(f"      ⚠ tentativi falliti fatti da QUESTO giro: {falliti_del_giro}")
        ko("      ⛔ Finche' questa causa e' in piedi, le altre tre non si")
        ko("         possono ne' confermare ne' escludere: si sblocca (B0.3) e")
        ko("         si riprova, ed e' quel che questo banco fa.")
        return MARCA_CAUSA_2

    # ── (3) la pila PAM non giudica un altro utente ───────────────────────
    if pam_root is not True:
        ko(f"   ⇒ {MARCA_CAUSA_3}: la stessa parola, sullo stesso servizio PAM,")
        ko("      NON funziona nemmeno fuori dal server (`pamtester`).")
        ko("      ⛔ Quindi non si sta misurando il server: o la pila non")
        ko("         consente a questo processo di verificare la parola di un")
        ko("         altro utente, o la parola non e' quella.")
        return MARCA_CAUSA_3

    # ── (1) la guardia ─────────────────────────────────────────────────────
    if not pam_interrogata:
        ko(f"   ⇒ {MARCA_CAUSA_1}: il server ha rifiutato e PAM NON E' STATA")
        ko("      NEMMENO INTERROGATA — nel suo registro non c'e' nessuna riga")
        ko("      di autenticazione.c per questo tentativo — mentre la stessa")
        ko("      parola, sullo stesso servizio, passa da `pamtester`.")
        ko("      ⛔ Il rifiuto nasce PRIMA di PAM: e' la guardia di v1")
        ko("         (`autenticazione_utente_atteso()`), che contraddice il")
        ko("         multi-tenant di SPECIFICHE.md §5.5.")
        return MARCA_CAUSA_1

    # ── nessuna delle quattro: e si dice, invece di sceglierne una ─────────
    ko("   ⇒ ⛔ NESSUNA DELLE QUATTRO: PAM e' stata interrogata e ha rifiutato,")
    ko("      ma la stessa parola passa da `pamtester` sullo stesso servizio.")
    ko("      ⚠ E' un quinto caso, e va guardato: la differenza fra i due")
    ko("        chiamanti (ambiente, tty, privilegi) e non la parola.")
    inf("   la coda del registro del server:")
    stampa_traccia(coda[-1200:])
    return "CAUSA-IGNOTA"


# ===========================================================================
def previsione(a):
    print(f"\n{NETTO}== B10 — le prove e l'atteso, scritti PRIMA{GRIGIO}\n")
    righe = [
        # ⭐ A0 sta in CIMA all'elenco perche' sta in cima al giro: e' l'unica
        #    prova che non guarda il server ma **questo file**, e se cade non
        #    c'e' nessuna ragione di credere alle sette sotto.
        ("A0", "il controllo positivo dell'appiglio al registro del server "
               f"({len(CASI_ANCORA)} righe vere e di domani)",
         "l'esito NON cambia — o la conferma di P1 e' gia' sparita in silenzio"),
        ("T1", "il secondo utente esiste e ha una parola in /etc/shadow",
         f"«{a.utente}» c'e', parola cifrata"),
        ("T2", "chi possiede il processo del server (letto, non supposto)",
         "un utente DI SISTEMA, e diverso da quello della prova"),
        ("T3", f"pamtester {a.servizio_pam} {a.utente} authenticate (da root)",
         "riesce — o non si sta misurando il server"),
        ("T3b", "lo stesso, da un utente NON privilegiato (rilievo R3.26)",
         "si misura e si dichiara: non e' un rosso"),
        ("T4", "pamtester con una parola sbagliata (il controllo che dice no)",
         "fallisce — o il si' di T3 non vale niente"),
        ("P1", f"la stretta di mano intera con «{a.utente}»",
         "⭐ SESSIONE — e' l'atteso di B10"),
        ("P2", f"«{a.utente}» con la parola sbagliata",
         "RESPINTO(CREDENZIALI_ERRATE 0x07)"),
        ("P3", f"la stretta di mano con «{a.utente_controllo}» (B0.5 + §5.5)",
         "SESSIONE: il server e' ancora li', e sono DUE utenti diversi"),
    ]
    for sigla, cosa, atteso in righe:
        print(f"    {sigla:<4} {cosa}")
        print(f"         atteso: {atteso}")
    print(f"\n    stati d'uscita: 0 = tutto come atteso · 1 = almeno una prova"
          f" ha dato altro\n                    2 = non ho potuto misurare"
          f" (⛔ e non e' un verde)\n")


def principale(a):
    fatti = []
    esito_finale = 0
    marche = []

    print(f"\n{NETTO}== B10 — il secondo utente: un utente DIVERSO da chi "
          f"possiede il processo{GRIGIO}")
    inf(f"bersaglio: {a.bersaglio} · {a.indirizzo}:{a.porta} · binario md5 "
        f"{a.md5} · giro {a.giro}")
    inf(f"servizio PAM: «{a.servizio_pam}» (⛔ NON «login»: SPECIFICHE.md §4.2)")
    inf(f"registro del server: {a.registro_server}")

    # ── ⭐ A0: PRIMA DI MISURARE, SI CONTROLLA LO STRUMENTO ────────────────
    #
    # ⛔ Sta qui, in cima e prima di tutto, e non in fondo: se l'appiglio al
    #    registro e' rotto, la conferma di P1 e' gia' sparita **e chi legge deve
    #    saperlo prima di credere a qualunque riga sotto**.  ⚠ Non tocca il
    #    server, non tocca PAM, non muove il conto di §4.4-bis e costa
    #    microsecondi: non c'e' nessun giro in cui valga la pena saltarlo.
    falliti_ancora, quanti_ancora = controllo_positivo_ancora()
    fatti.append({"prova": "A0", "casi": quanti_ancora,
                  "falliti": falliti_ancora})
    if falliti_ancora:
        esito_finale = 1
        marche.append(MARCA_ANCORA_ROTTA)

    # ── il secondo lettore ────────────────────────────────────────────────
    cliente, dove = carica_cliente()
    if cliente is None:
        ko(dove)
        return 2, fatti
    import aioquic
    inf(f"il secondo lettore di RCP: {dove} · aioquic {aioquic.__version__}")

    # =======================================================================
    titolo("T1 — lo stato iniziale: gli utenti esistono e hanno una parola (B0.1)")
    utenti = {}
    for nome in (a.utente, a.utente_controllo):
        esiste, parola_ok, spiega = utente_utilizzabile(nome)
        utenti[nome] = (esiste, parola_ok)
        if esiste is True and parola_ok is True:
            ok(f"«{nome}»: {spiega}")
        elif esiste is None or parola_ok is None:
            dub(f"«{nome}»: {spiega}")
        else:
            ko(f"«{nome}»: {spiega}")
    fatti.append({"prova": "T1", "utenti": {n: list(v) for n, v in utenti.items()}})

    if utenti[a.utente][0] is not True or utenti[a.utente][1] is not True:
        ko(f"⛔ {MARCA_CAUSA_4}: «{a.utente}» non e' utilizzabile.  Non e' il")
        ko("   server a rifiutare: e' il terreno, e il banco non misura.")
        ko("   ⭐ Si crea dal PROVISIONING, non a mano: "
           "/media/REMOTIX/provision-server.sh (passo 5-bis)")
        return 2, fatti

    # ⛔ E il file della parola: se lo legge chiunque, va detto.
    try:
        modo = os.stat(a.parola_file).st_mode & 0o077
        if modo:
            ko(f"⛔ il file della parola «{a.parola_file}» e' leggibile da altri "
               f"(bit {modo:o}): il segreto non e' protetto")
        else:
            ok(f"la parola arriva da «{a.parola_file}» (0600, mai in `ps`)")
    except OSError as e:
        ko(f"⛔ il file della parola non si legge: {e}")
        return 2, fatti
    try:
        with open(a.parola_file, encoding="utf-8") as f:
            parola = f.read().strip("\n")
    except OSError as e:
        ko(f"⛔ la parola non si legge: {e}")
        return 2, fatti
    if not parola:
        ko("⛔ il file della parola e' vuoto")
        return 2, fatti

    # =======================================================================
    titolo("T2 — chi possiede il processo del server: si LEGGE e si scrive")
    nome_prop, uid_prop, come = proprietario_del_processo(a.pid_server)
    if nome_prop is None:
        dub(come)
        ko("⛔ e senza sapere chi possiede il processo, «un utente diverso dal")
        ko("   proprietario» non e' una frase misurabile: non misuro (R3.26)")
        return 2, fatti
    ok(f"il processo {a.pid_server} e' di «{nome_prop}» (uid effettivo "
       f"{uid_prop}) — letto da {come}")
    if uid_prop < 1000:
        ok(f"⭐ e' un utente DI SISTEMA (uid {uid_prop} < 1000), come "
           f"SPECIFICHE.md §5.5 vuole")
    else:
        dub(f"⚠ uid {uid_prop} ≥ 1000: non e' un utente di sistema.  §5.5 vuole "
            f"un servizio di sistema — si dichiara, non e' un rosso di B10")
    fatti.append({"prova": "T2", "proprietario": nome_prop, "uid": uid_prop})

    # ⛔ IL CONTROLLO DI VACUITA'.
    if nome_prop == a.utente:
        ko(f"⛔ il server e' di «{nome_prop}», che e' L'UTENTE DELLA PROVA:")
        ko("   questo banco sarebbe verde per costruzione e non proverebbe")
        ko("   niente — la guardia di v1 lascerebbe passare proprio lui.")
        ko("   ⛔ Non misuro: 2, e non e' un verde.")
        return 2, fatti
    ok(f"⭐ «{a.utente}» ≠ «{nome_prop}»: la prova non e' vacua")

    # =======================================================================
    titolo("T3 — ⭐ il controllo che costa dieci secondi: la parola funziona "
           "FUORI dal server?")
    inf(f"⛔ sullo stesso servizio PAM del prodotto: «{a.servizio_pam}» "
        f"(src/remotix.pam)")
    pam_root, spiega = pamtester(a.servizio_pam, a.utente, parola)
    if pam_root is True:
        ok(f"pamtester {a.servizio_pam} {a.utente} authenticate: RIESCE · {spiega}")
    elif pam_root is None:
        dub(f"⛔ non si e' potuto fare: {spiega}")
    else:
        ko(f"⛔ pamtester FALLISCE con la stessa parola: {spiega}")
        ko("   ⇒ non si sta misurando il server (causa 3 o 4).")
    fatti.append({"prova": "T3", "pamtester_root": pam_root, "testo": spiega})

    # ── T3b: ⭐ la `[?]` R3.26 misurata, non discussa ──────────────────────
    titolo("T3b — ⭐ la pila PAM per un utente diverso dal proprietario del "
           "processo (rilievo R3.26)")
    inf("la domanda aperta e': un processo puo' verificare la parola di un")
    inf("ALTRO utente?  Dipende dai privilegi, e qui si misura invece di")
    inf("discuterne — `pam_unix` legge /etc/shadow, e da non-root passa per")
    inf("`unix_chkpwd`, che verifica soltanto chi lo ha chiamato.")
    try:
        info_c = pwd.getpwnam(a.utente_controllo)
        pam_altro, spiega_altro = pamtester(a.servizio_pam, a.utente, parola,
                                            come=(info_c.pw_uid, info_c.pw_gid))
    except KeyError:
        pam_altro, spiega_altro = None, f"⛔ «{a.utente_controllo}» non esiste"
    if pam_altro is True:
        ok(f"da «{a.utente_controllo}» (non privilegiato) la verifica di "
           f"«{a.utente}» RIESCE · {spiega_altro}")
    elif pam_altro is None:
        dub(f"non ho potuto guardare: {spiega_altro}")
    else:
        ok(f"⭐ da «{a.utente_controllo}» (non privilegiato) la verifica di "
           f"«{a.utente}» FALLISCE · {spiega_altro}")
        inf("⇒ ⭐ R3.26 MISURATA: la pila PAM giudica un altro utente **solo**")
        inf("  se il processo e' privilegiato.  Il server oggi e' di "
            f"«{nome_prop}» e ci riesce; ⛔ un servizio di sistema che lasciasse")
        inf("  i privilegi vedrebbe la causa (3) — e il sintomo sarebbe di")
        inf("  nuovo «credenziali errate».")
    fatti.append({"prova": "T3b", "pamtester_non_privilegiato": pam_altro,
                  "testo": spiega_altro})

    # ── T4: il controllo che dice NO, sullo strumento ─────────────────────
    titolo("T4 — il controllo negativo di `pamtester` (LEZIONI.md §1.9 regola 2)")
    pam_no, spiega_no = pamtester(a.servizio_pam, a.utente, a.parola_sbagliata)
    if pam_no is False:
        ok(f"con una parola sbagliata pamtester FALLISCE · {spiega_no}")
    elif pam_no is None:
        dub(f"non ho potuto guardare: {spiega_no}")
    else:
        ko("⛔ pamtester dice di si' anche con la parola sbagliata: il suo")
        ko("   «riesce» di T3 non vale niente")
        esito_finale = 1
    fatti.append({"prova": "T4", "pamtester_parola_sbagliata": pam_no})

    # =======================================================================
    # ⛔ P1 — L'ATTESO DI B10.
    # =======================================================================
    titolo(f"P1 — ⭐ la stretta di mano intera con «{a.utente}» "
           f"(atteso: SESSIONE)")
    falliti = 0
    marcatore = lunghezza(a.registro_server)
    esito, motivo, testo = stretta(cliente, a, a.utente, parola,
                                   registra=a.registra)
    stampa_traccia(testo)
    coda = coda_registro(a.registro_server, marcatore)

    if esito == "SESSIONE":
        ok(f"⭐ «{a.utente}» — che NON possiede il processo («{nome_prop}») — "
           f"e' arrivato fino a SESSIONE ({motivo})")
        ok("⇒ la guardia di v1 non c'e' piu': SPECIFICHE.md §5.5 regge sul filo")
        # ── ⛔ LA CONFERMA DAL LATO CHE RICEVE, e adesso ha QUATTRO esiti ────
        #
        # ⛔ Qui c'era un `if` senza `else`, guardato da una sottostringa che la
        #    cura di §1.10 ha reso cieca: quando ha smesso di combaciare, questa
        #    conferma **non e' diventata rossa — e' sparita**.  ⚠ E il ramo
        #    «senza ammesso» stampava per giunta con `ok()`, cioe' in VERDE: un
        #    avviso vestito da conferma.
        #
        # ⛔ E il vecchio criterio era «"ammesso" in coda», che e' un'altra
        #    trappola: la parola «ammesso» compare anche in `ammesso utente=…`,
        #    scritta da un ALTRO punto del server.  ⇒ La conferma poteva
        #    risultare vera anche leggendo una riga che non e' il verdetto di
        #    PAM.  Adesso il verdetto e' quello **catturato dall'appiglio**, e
        #    non una parola trovata in giro per la coda.
        stato_reg, verdetto_reg, quante_reg = verdetto_nel_registro(coda)
        fatti.append({"prova": "P1-registro", "stato": stato_reg,
                      "verdetto": verdetto_reg, "righe_pam": quante_reg})
        if stato_reg == "letto" and verdetto_reg == "ammesso":
            ok(f"⭐ e il registro del server lo conferma dal lato che RICEVE: "
               f"«PAM ha risposto … ammesso» ({quante_reg} riga/e di PAM in "
               f"questa coda)")
        elif stato_reg == "letto":
            falliti += 1
            esito_finale = 1
            ko(f"⛔ IL FILO E IL REGISTRO SI CONTRADDICONO: sul filo e' arrivato "
               f"SESSIONE, e il registro del server dice «{verdetto_reg}».")
            ko("   ⚠ Uno dei due sta mentendo, e non si sceglie quale: si dice.")
        elif stato_reg == "illeggibile":
            # ⛔ E QUESTO E' UN ROSSO SUL BANCO, NON SUL SERVER.
            esito_finale = 1
            marche.append(MARCA_ANCORA_ROTTA)
            ko(f"⛔ {quante_reg} riga/e «{RIGA_RCP_VERDETTO}» ci sono e NON SI "
               f"LASCIANO LEGGERE dall'appiglio «{R_RCP_VERDETTO.pattern}».")
            ko("   ⛔ Il primo imputato e' il BANCO (`REVIEWER.md` §1): il")
            ko("      server ha scritto il verdetto, e sono io a non saperlo")
            ko("      piu' leggere.  E' la forma E8, ed e' esattamente quel che")
            ko("      il 12 agosto 2026 ha accecato B8 per un giro intero.")
            ko(f"   ⇒ {MARCA_ANCORA_ROTTA}")
        else:
            # ⚠ Tre esiti, e il terzo non si arrotonda a nessuno degli altri due.
            dub("non ho potuto guardare: nessuna riga «PAM ha risposto» nella "
                "coda di questo tentativo")
            dub("   ⚠ non e' «il server non l'ha scritta»: puo' essere il")
            dub("     registro sbagliato, o un marcatore preso troppo tardi.")
    else:
        falliti += 1
        esito_finale = 1
        marche.append(diagnosi(motivo, coda, pam_root,
                               utenti[a.utente][0], utenti[a.utente][1],
                               falliti))
        # ⛔ E se la causa e' il contatore, si sblocca DICHIARANDOLO e si
        #    riprova: altrimenti (2) coprirebbe (1), che e' il difetto che
        #    questo banco esiste per vedere.
        if marche[-1] == MARCA_CAUSA_2 and a.socket_comando:
            titolo("P1-bis — si sblocca (dichiarato, B0.3) e si riprova: il "
                   "contatore non deve coprire le altre tre cause")
            sblocca(a.socket_comando, a.indirizzo_client,
                    "il contatore per indirizzo copriva le altre cause di B10")
            marcatore = lunghezza(a.registro_server)
            esito, motivo, testo = stretta(cliente, a, a.utente, parola)
            stampa_traccia(testo)
            coda = coda_registro(a.registro_server, marcatore)
            if esito == "SESSIONE":
                ok(f"⭐ dopo lo sblocco «{a.utente}» ENTRA: la causa era il "
                   f"contatore, e le altre tre sono escluse")
                marche.pop()
                esito_finale = 0
            else:
                falliti += 1
                marche.append(diagnosi(motivo, coda, pam_root, True, True,
                                       falliti))
    fatti.append({"prova": "P1", "esito": esito, "motivo": motivo,
                  "atteso": "SESSIONE",
                  "pam_interrogata": (RIGA_PAM_RIFIUTA in coda
                                      or RIGA_PAM_INCERTA in coda)})

    # =======================================================================
    titolo(f"P2 — il controllo che dice NO: «{a.utente}» con la parola sbagliata")
    inf("⛔ senza, «entra» sarebbe soddisfatto anche da un server che ammette")
    inf("   chiunque — e P1 non proverebbe niente")
    marcatore = lunghezza(a.registro_server)
    esito2, motivo2, testo2 = stretta(cliente, a, a.utente, a.parola_sbagliata)
    stampa_traccia(testo2)
    coda2 = coda_registro(a.registro_server, marcatore)
    if esito2 == "RIFIUTO" and "CREDENZIALI_ERRATE" in motivo2:
        falliti += 1
        ok(f"RESPINTO: {motivo2} — il server sa dire di no")
        if RIGA_PAM_RIFIUTA in coda2:
            ok("⭐ e il registro del server porta «PAM ha RIFIUTATO»: PAM E'")
            ok("   STATA INTERROGATA, cioe' il rifiuto viene da PAM e non da")
            ok("   una guardia precedente")
        else:
            dub("⚠ il registro non porta «PAM ha RIFIUTATO» per questo "
                "tentativo: il no potrebbe non venire da PAM")
    elif esito2 == "RIFIUTO":
        falliti += 1
        ko(f"⛔ RESPINTO con un motivo diverso dall'atteso: {motivo2}")
        esito_finale = 1
    else:
        ko(f"⛔ con la parola SBAGLIATA il server ha risposto «{esito2}» "
           f"({motivo2}): atteso CREDENZIALI_ERRATE")
        esito_finale = 1
    fatti.append({"prova": "P2", "esito": esito2, "motivo": motivo2,
                  "atteso": "RIFIUTO CREDENZIALI_ERRATE"})

    # =======================================================================
    titolo(f"P3 — B0.5 + §5.5: il server e' ancora li', e con un TERZO utente "
           f"(«{a.utente_controllo}»)")
    inf("⛔ B0.5: dopo un tentativo respinto il server dev'essere ancora li' —")
    inf("   una connessione nuova che arriva fino a SESSIONE.  ⭐ E qui vale")
    inf("   doppio: e' un utente ANCORA diverso, cioe' due utenti non")
    inf("   proprietari del processo sullo stesso server (multi-tenant §5.5)")
    if utenti[a.utente_controllo][0] is not True:
        dub(f"«{a.utente_controllo}» non c'e': B0.5 non si e' potuto verificare")
        fatti.append({"prova": "P3", "esito": "non-misurato"})
    else:
        esito3, motivo3, testo3 = stretta(cliente, a, a.utente_controllo,
                                          a.parola_controllo)
        stampa_traccia(testo3)
        if esito3 == "SESSIONE":
            ok(f"⭐ «{a.utente_controllo}» e' arrivato a SESSIONE ({motivo3}): "
               f"il server e' ancora li' (B0.5)")
            ok(f"⭐ e sono DUE utenti diversi — «{a.utente}» e "
               f"«{a.utente_controllo}» — nessuno dei due proprietario del "
               f"processo («{nome_prop}»)")
        else:
            ko(f"⛔ «{a.utente_controllo}»: {esito3} ({motivo3})")
            if esito3 == "RIFIUTO" and "TROPPI_TENTATIVI" in motivo3:
                ko(f"   ⚠ {MARCA_CAUSA_2}: il tentativo fallito di P2 ha")
                ko("      consumato il conto per indirizzo di §4.4-bis.  Il")
                ko("      lanciatore sblocca in fondo, dichiarandolo (B0.3)")
            esito_finale = 1
        fatti.append({"prova": "P3", "esito": esito3, "motivo": motivo3,
                      "atteso": "SESSIONE"})

    # =======================================================================
    titolo("Il verdetto — e lo confronta il banco, non chi legge (B0.4)")
    for f in fatti:
        if "atteso" in f:
            va = f.get("esito") == f["atteso"] or (
                f["atteso"].startswith("RIFIUTO") and f.get("esito") == "RIFIUTO"
                and "CREDENZIALI_ERRATE" in (f.get("motivo") or ""))
            print(f"    {'⭐' if va else '⛔'} {f['prova']:<4} atteso "
                  f"{f['atteso']:<32} ottenuto {f.get('esito')} "
                  f"{f.get('motivo') or ''}")
    inf(f"tentativi FALLITI fatti da questo giro: {falliti} (§4.4-bis conta per "
        f"indirizzo)")
    if marche:
        inf("marche della diagnosi: " + " · ".join(marche))
    return esito_finale, fatti


if __name__ == "__main__":
    # ⛔ SI GUARDA PRIMA DI `argparse`, E NON E' PIGRIZIA.  Il controllo
    #    positivo dell'appiglio non ha bisogno di NIENTE — ne' porta, ne'
    #    parola d'ordine, ne' pid del server — mentre `argparse` qui sotto
    #    pretende cinque argomenti obbligatori che esistono solo su NIC-OS,
    #    dentro il contenitore.  ⭐ Volerli anche per questo passo vorrebbe dire
    #    renderlo eseguibile **solo dove costa**, cioe' non eseguirlo mai: ed e'
    #    la ragione per cui il difetto del 12 agosto 2026 e' rimasto in piedi.
    if "--controllo-ancora" in sys.argv:
        _falliti, _quanti = controllo_positivo_ancora()
        print()
        sys.exit(1 if _falliti else 0)
    p = argparse.ArgumentParser(
        description="B10 — il secondo utente: la guardia ereditata da v1")
    p.add_argument("--bersaglio", required=True)
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, required=True)
    p.add_argument("--utente", default="prova2")
    # ⛔ NON `--parola`: la parola generata di `prova2` non deve finire in `ps`.
    p.add_argument("--parola-file", required=True,
                   help="file 0600 con la sola parola d'ordine")
    p.add_argument("--utente-controllo", default="prova")
    p.add_argument("--parola-controllo", default="parola-di-prova",
                   help="⚠ questa SI' sulla riga di comando: e' la parola "
                        "pubblica dei banchi, compromesso gia' dichiarato")
    p.add_argument("--parola-sbagliata", default="questa-non-e-la-sua")
    p.add_argument("--pid-server", type=int, required=True)
    p.add_argument("--registro-server", required=True)
    p.add_argument("--servizio-pam", default="remotix")
    p.add_argument("--socket-comando", default="")
    p.add_argument("--indirizzo-client", default="192.168.0.2")
    p.add_argument("--registra", default="")
    p.add_argument("--uscita", default="")
    p.add_argument("--md5", default="ignota")
    p.add_argument("--giro", default="")
    p.add_argument("--elenco", action="store_true")
    # ⭐ Il controllo positivo dell'appiglio, da solo e SENZA SERVER: non serve
    #    ne' porta, ne' PAM, ne' contenitore.  ⛔ Gira comunque a ogni giro di
    #    B10 (passo A0); questa opzione esiste perche' lo si possa provare in un
    #    secondo dopo aver toccato una riga di registro nel prodotto, che e'
    #    precisamente il momento in cui il 12 agosto 2026 nessuno l'ha fatto.
    p.add_argument("--controllo-ancora", action="store_true")
    a = p.parse_args()
    if a.elenco:
        previsione(a)
        sys.exit(0)
    try:
        stato, fatti = principale(a)
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        print(f"\n    {ROSSO}NO{GRIGIO}  ⛔ {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
    # ⛔ Il registro dei fatti si scrive SEMPRE, anche quando si e' rossi: e'
    #    quel che permette di confrontare due giri a distanza di ore.
    if a.uscita:
        riga = {"quando": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "banco": "B10", "bersaglio": a.bersaglio, "porta": a.porta,
                "utente": a.utente, "servizio_pam": a.servizio_pam,
                "md5_binario": a.md5, "giro": a.giro, "stato": stato,
                "fatti": fatti}
        try:
            with open(a.uscita, "a", encoding="utf-8") as f:
                f.write(json.dumps(riga, ensure_ascii=False) + "\n")
            print(f"    --  registro dei fatti: {a.uscita}")
        except OSError as e:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ registro non scritto: {e}")
    print(f"\n    {'⭐ B10: tutto come atteso' if stato == 0 else '⛔ B10: ' + ('non ho potuto misurare' if stato == 2 else 'ALMENO UNA PROVA NON HA DATO L ATTESO')} (uscita {stato})\n")
    sys.exit(stato)
