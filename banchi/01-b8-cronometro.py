#!/usr/bin/env python3
"""01-b8-cronometro.py — ⛔ B8: il secondo fisso, e IL BAN DELL'INDIRIZZO.

    python3 01-b8-cronometro.py --previsione
    python3 01-b8-cronometro.py --campioni --blocco 3 --giro ...
    python3 01-b8-cronometro.py --ban prima  --giro ...    (una vita del server)
    python3 01-b8-cronometro.py --ban dopo   --giro ...    (dopo il riavvio)
    python3 01-b8-cronometro.py --verdetto --giro ...

⚠ Gira DENTRO il contenitore: `aioquic` sta li'.  Lo conduce `01-b8-lancia.sh`.

===========================================================================
⛔ RISCRITTO L'11 AGOSTO 2026, E QUEL CHE E' CADUTO VA SAPUTO LEGGENDO QUI

`DECISIONI.md` §1.9 ha sostituito la forma della limitazione: **tre
autenticazioni fallite dallo stesso indirizzo dentro cinque minuti, e
quell'indirizzo e' fuori per dodici ore**.  Con essa cadono, da questo file:

  · i **due contatori** (uno per nome utente, uno per indirizzo).  Ne resta
    **uno solo**, sull'indirizzo: ⛔ tre nomi diversi contano **tre**;
  · il controllo *«quattro falliti · uno riuscito · altri quattro»*: dopo il
    terzo fallito **non esiste nessun quinto tentativo**;
  · ⛔ e **le dodici vite del server**.  La vecchia coreografia spegneva e
    riaccendeva il processo a ogni blocco perche' quello era l'unico modo di
    azzerare i contatori: *«`rcp_azzera_registro_sessioni()` esiste ma non la
    chiama nessuno — non c'e' messaggio, segnale o opzione che ci arrivi»*.
    ⭐ Adesso **c'e'**: il comando di sblocco di §4.4-bis, che l'11 agosto e'
    nato lato ospite.  Le vite del server sono **due**, e la seconda esiste per
    una ragione sola — provare che il ban sopravvive al riavvio.

===========================================================================
⛔ CHE COSA MISURA, IN DUE PARTI CHE NON SI MESCOLANO

**1. Il secondo fisso, e le tre mediane** — invariato nella sostanza.  §4.4
vieta di distinguere nel **motivo** fra «utente inesistente» e «parola
sbagliata»; §4.4-bis impone un **ritardo fisso di un secondo** perche' quella
distinzione non si legga col **cronometro**.  ⛔ E il criterio NON e' «≥ 1 s»:
`pam_authenticate(); sleep(1); rispondi();` da 1,001 · 1,050 · 1,300 s nei tre
casi — tre righe verdi, e la distinzione leggibile esattamente come prima
(rilievo R3.2).  Il criterio e' **di forma diversa**: le tre mediane devono
differire **meno del rumore della misura**.

**2. Il ban** — nuovo.  Tre fallite con **tre nomi diversi**, poi il quarto
tentativo **con la parola d'ordine GIUSTA** che DEVE essere rifiutato con
`TROPPI_TENTATIVI`; piu' i tre controlli che dicono *no*; piu' la pagina che si
carica lo stesso e dice quante ore mancano; piu' il comando di sblocco.

===========================================================================
⛔ COME QUESTO BANCO SI PROCURA I CAMPIONI, E PERCHE' LA SCELTA VA DICHIARATA

`fasi/01-filo-nudo.md` B8 lo dice in una riga: *«i campioni adesso costano: tre
per indirizzo, poi il ban.  Le mediane vogliono molti campioni per caso, quindi
il banco deve **variare l'indirizzo di provenienza** o **sbloccare fra un blocco
e l'altro** — ⛔ e **dichiarare quale delle due fa**, perche' cambiano quel che
la misura sta misurando»*.

⭐ **Questo banco fa la SECONDA, e usa la prima solo come margine.**

  · un **blocco** e' la sequenza fra due sblocchi.  Dentro un blocco il banco
    porta al massimo **due** fallimenti per indirizzo — ⛔ **uno sotto la
    soglia**, e il conto e' fatto **senza contare l'azzeramento sul successo**:
    se un giorno l'azzeramento smettesse di funzionare, il bilancio reggerebbe
    lo stesso e il banco misurerebbe ancora PAM.  Un bilancio che poggia sulla
    regola che si sta provando non e' un bilancio;
  · i fallimenti si alternano fra **due indirizzi di provenienza**
    (`127.0.0.1` e `192.168.0.2`, che la stessa macchina raggiunge perche' il
    server e' acceso su `0.0.0.0`): raddoppia il margine e ⛔ **si vede nel
    registro del server**, che scrive `da=<indirizzo>:<porta>` — il denominatore
    letto dove la cosa succede, non nella nostra intenzione (`LEZIONI.md` §1.9);
  · fra un blocco e l'altro, `01-b8-lancia.sh` chiama il **comando di sblocco**
    su tutt'e due gli indirizzi, ⛔ **e lo stampa**.

⛔ **CHE COSA QUESTA SCELTA CAMBIA, DETTO INVECE CHE NASCOSTO.**  I campioni
   sono presi **sempre con il conto sotto soglia**, quindi le tre mediane
   misurano PAM piu' il ritardo fisso e **mai** la strada del rifiuto immediato.
   E' quel che serve — le tre mediane parlano di quel che PAM lascia trapelare —
   ⚠ ma vuol dire che questa parte del banco **non prova niente sul ban**: il
   ban lo prova la parte 2, dove nessuno sblocca niente.

⛔ **E NESSUNO SBLOCCA DENTRO IL GIRO DEL BAN** (B0.3: *«mai dentro il giro di
   B8, o B8 non prova piu' niente»*).  Gli sblocchi di questo banco sono in tre
   posti soli, e sono tutti e tre dichiarati:

     1. **prima** di cominciare, per partire da uno stato noto (B0.1);
     2. **fra un blocco e l'altro** dei campioni, e mai dentro il giro del ban;
     3. **in fondo**, dove lo sblocco non e' un attrezzo ma **la cosa provata**.

===========================================================================
⛔ LE TRE GUARDIE CONTRO IL LIMITATORE, E NESSUNA SI FIDA DELLE ALTRE

  a. **il bilancio**: due fallimenti per indirizzo per blocco, soglia tre;
  b. **il piano si verifica PRIMA di eseguirlo**: `simula()` e' un modello della
     §4.4-bis nuova — soglia 3, finestra scorrevole di 5 minuti, chiave sul solo
     indirizzo, azzeramento sul successo, sblocco che azzera tutto — e dice
     **tentativo per tentativo** che cosa dovrebbe arrivare.  `verifica_piano()`
     **non fa partire** un blocco che il modello vede sforare.  Un commento che
     dice «stiamo sotto soglia» non e' una verifica: questo lo e';
  c. ⛔ **e sul filo si guarda ogni singola risposta**: un campione che torna
     `RESPINTO(TROPPI_TENTATIVI)` **non entra nelle mediane**, si conta a parte e
     **toglie il verde**.  E' il controllo che non dipende da nessuna nostra
     aritmetica.

===========================================================================
⛔ LA REGOLA CON CUI SI DECIDE CHE DUE MEDIANE SONO «INDISTINGUIBILI»

Per ogni coppia di casi: la **differenza delle mediane** e il suo intervallo al
95 % per **ricampionamento** (bootstrap, 2000 ripetizioni, seme fisso perche'
due giri sugli stessi dati diano lo stesso verdetto).

  | l'intervallo | il verdetto |
  |---|---|
  | **non** contiene lo zero | ⛔ **SI DISTINGUONO** |
  | contiene lo zero, semiampiezza ≤ RISOLUZIONE_VOLUTA | ⭐ **indistinguibili**, e si dice fin dove si e' guardato |
  | contiene lo zero, semiampiezza piu' grande | ⚠ **SOSPESO**: non ho guardato abbastanza |

⭐ Guardare **meno** allarga l'intervallo e porta al *sospeso*, non al verde: e'
   l'unica forma di regola che non si puo' soddisfare misurando di meno.

===========================================================================
⚠ IL `[?]` CHE QUESTO BANCO HA GIA' TROVATO, E CHE IL BAN NON CHIUDE

`[M]` 10 agosto 2026: la mediana dei respinti era **2636 ms**, dove §4.4-bis
vuole ~1000.  ⛔ A governare i tempi non e' il nostro ritardo: e' **PAM**
(`pam_faildelay` nella pila di `/etc/pam.d/login` ritarda i FALLIMENTI di ~3 s,
con la randomizzazione di libpam).  Finche' quel ritardo non e' costante, il
secondo fisso **non nasconde quel che dichiara di nascondere**.  Il ban e' una
proprieta' diversa e **non la chiude**.

===========================================================================
⚠ DUE PUNTI IN CUI I DOCUMENTI AMMETTEVANO DUE LETTURE, E LA SCELTA FATTA

  1. §4.4-bis: *«il rifiuto di un indirizzo bannato **non passa dal secondo
     fisso** … si decide **prima di CREDENZIALI**»*.  ⛔ `banchi/rcp/rcp.c` lo
     decide **dopo** aver ricevuto `CREDENZIALI` (non puo' fare altrimenti: il
     canale di controllo e' l'unica cosa che vede) e lo fa passare **dal
     ritardo fisso lo stesso**.  ⭐ E deve essere cosi', o il banco non
     potrebbe esistere: B8 pretende `TROPPI_TENTATIVI` **dentro un `RESPINTO`**
     (§4.4, rilievo R1.18), e un rifiuto deciso prima di `CREDENZIALI` non
     avrebbe nessun `RESPINTO` da mandare.  Qui il tempo del rifiuto si
     **misura e si stampa**, e non fa ne' rosso ne' verde: e' un difetto del
     documento, non del codice;
  2. §4.4-bis: *«la pagina si serve lo stesso»* non dice **con quale stato
     HTTP**.  L'ospite risponde **200**, e la ragione sta nel suo commento: con
     un 4xx un intermediario o il browser possono sostituire il corpo, e la
     frase che l'utente DEVE leggere sparirebbe.  Qui si pretende **200**;
  3. ⭐ **e la piu' importante delle tre**: `fasi/01-filo-nudo.md` B8 chiede
     *«le TRE mediane indistinguibili»*, e §4.4-bis vuole il ritardo fisso
     *«anche quando la risposta e' AMMESSO»*.  ⚠ Ma quel che §4.4 **vieta** di
     far sapere e' una cosa sola — **se un nome utente esista** — mentre
     «ammesso» contro «respinto» il filo lo dice da se': sono due **messaggi
     diversi**.  ⛔ Le tre coppie non valgono lo stesso, e questo banco le
     esegue tutt'e tre **contandole a parte**:

       `inesistente − sbagliata` che si separa   ⇒ ⛔ ROSSO PIENO: e' la
                                                   separazione che §4.4 vieta;
       le altre due che si separano              ⇒ un esito a se' (5), col
                                                   colpevole nominato.

     ⚠ Non si sceglie la lettura comoda e non si tace: si eseguono tutt'e due
       e si dice **quale numero appartiene a quale**.  ⛔ E `[M]` 11 agosto
       2026 la coppia che porta il segreto **non** si separa (−56 ms,
       intervallo [−569; +442]) mentre le altre due si separano di ~2 secondi:
       il ritardo fisso fa quel che deve, e a spostare gli altri due e' PAM.
"""
import argparse
import asyncio
import importlib.util
import json
import os
import pwd
import random
import re
import socket
import ssl
import statistics
import sys
import time

from aioquic.asyncio import connect
from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration

QUI = os.path.dirname(os.path.abspath(__file__))


def _importa(nome, file):
    spec = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ⛔ Il cliente di prova di B3 si IMPORTA, non si ricopia: dentro c'e' la riga
#    che gli impedisce di dare gli eventi del canale di controllo allo strato
#    HTTP/3 di aioquic — senza la quale la connessione muore per mano del
#    CLIENT, e qui il sintomo sarebbe «il server non risponde in tempo».
b3 = _importa("b3cliente", "01-b3-cliente.py")
# ⛔ E il comando di sblocco pure: se questo file se lo riscrivesse, B0.3
#    avrebbe due comandi di sblocco e nessuno saprebbe quale ha girato.
cmd = _importa("b8sblocca", "01-b8-sblocca.py")
# ⛔ E il profilo del BERSAGLIO: le differenze fra i due server in un file solo.
b0 = _importa("b0bersaglio", "01-b0-bersaglio.py")

inquadra, s_str, MOTIVI = b3.inquadra, b3.s, b3.MOTIVI
T_CREDENZIALI = 0x0003
CREDENZIALI_ERRATE, TROPPI_TENTATIVI = 0x07, 0x08

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# ── I numeri della regola, tutti in un posto e tutti dichiarati ──────────────
# `RCP.md` §4.4-bis, forma dell'utente del 10 agosto 2026.
SOGLIA = 3                 # tre autenticazioni fallite dallo stesso indirizzo
FINESTRA_MIN = 5           # ...dentro cinque minuti (finestra SCORREVOLE)
BAN_ORE = 12               # ...e quell'indirizzo e' fuori per dodici ore
BILANCIO = 2               # ⛔ uno SOTTO la soglia, per indirizzo e per blocco
RITARDO_FISSO = 1000.0     # §4.4-bis: nessuna risposta a CREDENZIALI prima di 1 s
RISOLUZIONE_VOLUTA = 50.0  # ms — la separazione che il documento della fase nomina
MINIMO_CAMPIONI = 10       # sotto questo non si giudica: si dice «sospeso»
RIPETIZIONI = 2000         # ricampionamenti del bootstrap
SEME = 20260811            # ⛔ fisso: due verdetti sugli stessi dati coincidono
# ⛔ I DUE MARGINI CHE SERVONO A NOMINARE UN IMPUTATO, e stanno qui perche' un
#    numero scelto dentro un `if` e' un numero che nessuno confronta.
#    · `MARGINE_IMPUTATO`  quanto il server deve aver aspettato OLTRE il secondo
#      fisso perche' si possa dire «a governare non e' stato il nostro ritardo».
#      Sotto questa soglia il secondo fisso ha coperto tutto, e chi ha ritardato
#      non ha lasciato nessuna traccia nel punto in cui il server misura.
#    · `MARGINE_CRONOMETRI`  di quanto il cronometro del CLIENT puo' stare sotto
#      quello del SERVER prima che la differenza smetta di essere rumore di
#      rete.  ⛔ Il client misura un intervallo che CONTIENE quello del server
#      (parte prima di spedire e finisce dopo aver ricevuto): puo' solo essere
#      piu' grande.  Se e' piu' piccolo, non e' il server ad essere strano — e'
#      il cronometro del banco che non sta cronometrando quel che dichiara.
MARGINE_IMPUTATO = 200.0
MARGINE_CRONOMETRI = 100.0

CASI = ("inesistente", "sbagliata", "giusta")
ATTESO = {"inesistente": ("RESPINTO", CREDENZIALI_ERRATE),
          "sbagliata": ("RESPINTO", CREDENZIALI_ERRATE),
          "giusta": ("AMMESSO", None)}

# Le sei permutazioni della terzina.  ⛔ L'ordine RUOTA: se un caso stesse
#    sempre subito dopo lo sblocco e un altro sempre in fondo, qualunque deriva
#    dentro il blocco finirebbe **nelle mediane** travestita da differenza fra
#    i casi.
ROTAZIONI = [("inesistente", "sbagliata", "giusta"),
             ("sbagliata", "giusta", "inesistente"),
             ("giusta", "inesistente", "sbagliata"),
             ("inesistente", "giusta", "sbagliata"),
             ("sbagliata", "inesistente", "giusta"),
             ("giusta", "sbagliata", "inesistente")]

# ⛔ I TRE NOMI DEL GIRO DEL BAN — e DEVONO essere diversi.
#    `fasi/01-filo-nudo.md` B8: «con lo stesso nome tre volte, un server che
#    avesse ancora il contatore per NOME della forma vecchia darebbe verde: il
#    banco proverebbe la regola sbagliata.  E' la stessa forma con cui B5 ha
#    trovato il contatore chiavato sulla porta».
#    ⭐ E i tre non sono nemmeno dello stesso TIPO: due nomi che non esistono e
#       una parola sbagliata sull'utente vero.  §4.4-bis conta le due cose come
#       una sola — «il conto non sa se il nome non esistesse o se la parola
#       fosse sbagliata» — e questo e' il modo di provarlo invece di crederlo.
NOMI_DEL_BAN = ("nessuno-b8-uno", "<utente>", "nessuno-b8-tre")


# ===========================================================================
# Il filo
# ===========================================================================
async def apri(indirizzo, porta, percorso="/rcp/1"):
    """Una connessione nuova, e la sessione WebTransport su `/rcp/1`.

    ⚠ Una per tentativo, e non e' una scelta: §4.4 ammette **un solo tentativo
      per connessione**."""
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{indirizzo}:{porta}"
    gestore = connect(indirizzo, porta, configuration=conf,
                      create_protocol=b3.Cliente)
    cli = await gestore.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    cli.apri_sessione(autorita, percorso)
    stato = await asyncio.wait_for(cli.accettata, timeout=8)
    return gestore, cli, stato


async def un_tentativo(indirizzo, porta, nome, parola, attesa_chiusura=4.0):
    """Un tentativo: `CREDENZIALI` che parte, la risposta che arriva, i millisecondi.

    ⛔ CHE COSA STA DENTRO IL CRONOMETRO, E CHE COSA NO.  Dentro: il viaggio di
       `CREDENZIALI`, il lavoro del server (guardia del ban, PAM, ritardo fisso)
       e il viaggio della risposta.  Fuori: la stretta di mano QUIC/TLS,
       l'apertura della sessione, `CIAO`/`ECCOMI`.

    ⚠ Il giro di rete e' dentro e non si toglie — ma e' **lo stesso per tutt'e
      tre i casi**, sullo stesso cammino: puo' spostare le tre mediane insieme,
      non separarle.  E' la ragione per cui il criterio e' una DIFFERENZA.

    ⛔ E SI ASPETTA ANCHE LA CHIUSURA DELLA SESSIONE, che e' la **seconda strada
       di §3.1 punto 3** e l'unica cosa che risponde a *«e la scheda gia'
       aperta?»* di B8.  ⚠ Non arriva insieme al `RESPINTO`: l'ospite la rimanda
       di cinque passate del ciclo di scrittura — mezzo secondo — apposta,
       perche' un browser che processa la capsula prima dei byte dello stream
       butterebbe il `RESPINTO` (difetto trovato da B11).  Chiudere subito dopo
       la risposta vorrebbe dire dichiarare «nessun codice di chiusura» su un
       codice che stava arrivando.

    ⛔ La parola d'ordine non finisce in nessun file (B13.2): di qui esce solo il
       **nome** e il tempo."""
    fuori = {"indirizzo": indirizzo, "nome": nome, "ms": None,
             "messaggio": None, "motivo": None, "chiusura": None,
             "esito": "errore", "errore": ""}
    gestore = None
    try:
        gestore, cli, stato = await apri(indirizzo, porta)
        if stato != "200":
            fuori["errore"] = f"la sessione non si e' aperta: :status={stato}"
            return fuori
        cli.apri_controllo()
        cli.manda(inquadra(b3.T["CIAO"], b3.corpo_ciao()))
        await b3.attendi(cli, "ECCOMI", attesa=10)
        corpo = s_str(nome) + s_str(parola)
        t0 = time.perf_counter()
        cli.manda(inquadra(T_CREDENZIALI, corpo))
        # ⛔ `quale=None`: si accetta QUALUNQUE risposta e la si classifica dopo.
        #    Pretendere `AMMESSO` farebbe sollevare un'eccezione sui casi che
        #    devono essere respinti — cioe' il banco non avrebbe il tempo dei
        #    casi che gli interessano di piu'.
        nome_msg, corpo_r, _ = await b3.attendi(cli, None, attesa=30)
        fuori["ms"] = (time.perf_counter() - t0) * 1000.0
        fuori["messaggio"] = nome_msg
        if nome_msg == "RESPINTO":
            fuori["motivo"] = corpo_r[0] if corpo_r else None
            # ⚠ Solo dopo un RESPINTO: dopo un AMMESSO la sessione resta viva e
            #   aspettare qui vorrebbe dire aspettare per niente quattro secondi
            #   per ogni campione «giusta» — cioe' un terzo del banco.
            try:
                await asyncio.wait_for(cli.caduto.wait(), timeout=attesa_chiusura)
            except asyncio.TimeoutError:
                pass
            fuori["chiusura"] = cli.codice_chiusura
        fuori["esito"] = "misurato"
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        fuori["errore"] = f"{type(e).__name__}: {e}"
    finally:
        if gestore is not None:
            try:
                await gestore.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
    return fuori


def classifica(rec, caso):
    """⛔ La terza guardia: che cosa e' arrivato DAVVERO.

    Un `TROPPI_TENTATIVI` non e' un campione di «parola sbagliata»: e' un'altra
    strada dentro il server — **non passa nemmeno da PAM** — e metterlo nella
    stessa mediana significherebbe mescolare due popolazioni sotto la stessa
    etichetta (forma E2)."""
    if rec["esito"] == "errore":
        return "errore"
    msg, motivo = ATTESO[caso]
    if rec["messaggio"] == "RESPINTO" and rec["motivo"] == TROPPI_TENTATIVI:
        return "limitatore"
    if rec["messaggio"] != msg:
        return "inatteso"
    if motivo is not None and rec["motivo"] != motivo:
        return "inatteso"
    return "atteso"


# ===========================================================================
# ⛔ LA PAGINA IN TCP — «quel che l'utente vede»
# ===========================================================================
# `RCP.md` §4.4-bis, e la ragione e' dell'utente: «la pagina si serve lo stesso,
# e mostra il rifiuto — *tentativi esauriti* … chi e' stato bannato per errore e'
# quasi sempre il proprietario».
#
# ⚠ E QUEL CHE QUESTA LETTURA **NON** E'.  `fasi/01-filo-nudo.md` B8 dice «si
#   legge il DOM, come per le otto frasi di B7».  Qui si legge **l'HTML servito**
#   con un socket, non un DOM costruito da un browser: e' legittimo perche' la
#   frase la scrive il server nel corpo e nessuno script la costruisce — quel
#   che il browser mostrerebbe e' esattamente questo testo — ⛔ ma va detto, ed
#   e' un `[?]`: con un browser vero non e' stato provato.
#
# ⛔⭐ E DI QUALE SERVER PARLANO QUESTI TRE MARCATORI — rilievo R12.2, lente D
#    della revisione dell'11 agosto 2026.  E' l'avvertenza piu' importante di
#    questa parte, e non c'era.
#
#    I tre marcatori che si cercano qui sotto — `data-bannato="(si|no)"`,
#    `data-restano-ms="(\d+)"` e la sottostringa esatta `tentativi esauriti` —
#    li produce **soltanto l'innesto**, `01-b3-rcp-innesta.py:1105-1139`.  ⛔ Il
#    server di prodotto in `src/` la stessa cosa la dice in un altro modo:
#
#      · `src/pagina.c:257-262` scrive «I tentativi di accesso da questo
#        indirizzo sono **esauriti**.  Riprova fra %llu ore e %llu minuti…» —
#        sette parole in mezzo, quindi la sottostringa che si cerca qui NON c'e';
#      · i millisecondi residui **non compaiono affatto** nel documento servito:
#        il prodotto li formatta gia' in ore e minuti e butta il resto;
#      · `data-bannato` e `data-restano-ms` compaiono **zero volte** in
#        `src/pagina.c` e in `src/pagina.html`.
#
# ⛔ CONSEGUENZA, E VA LETTA PRIMA DI CREDERE A UN ROSSO: il giorno in cui
#    qualcuno punta questo banco al server di `src/`, i tre controlli della
#    pagina diventano **rossi su un server che il ban lo fa**, tutti e tre
#    insieme — e il rosso finisce sull'imputato sbagliato, che e' il difetto
#    piu' caro di questo progetto (`LEZIONI.md` §1.9, settima veste).
#    ⚠ Prima di cercare nel server, si guardi se il server e' `bsslserver`
#      (l'innesto) o `remotix` (il prodotto): sono due formati di pagina senza
#      un solo campo in comune, ed e' la forma d'errore **E2** — due misure
#      diverse sotto la stessa etichetta.
#    ⛔ La cura non e' qui: e' che i due formati diventino uno.  Finche' non lo
#      sono, questa e' la riga che impedisce di perderci un'ora.
def _chiedi_pagina(indirizzo, porta, attesa, tls):
    """Una richiesta sola, nel dialetto chiesto.  (grezzo, errore)."""
    nudo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    nudo.settimeout(attesa)
    s = None
    try:
        nudo.connect((indirizzo, porta))
        if tls:
            # ⭐ Quel che NON cambia: l'indirizzo di provenienza continua a
            #    sceglierlo il nucleo.  `wrap_socket` incarta la connessione
            #    gia' aperta, non ne apre un'altra.
            conf = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            conf.check_hostname = False
            conf.verify_mode = ssl.CERT_NONE  # il certificato lo giudica B3
            s = conf.wrap_socket(nudo, server_hostname=indirizzo)
        else:
            s = nudo
        s.settimeout(attesa)
        s.sendall(f"GET / HTTP/1.1\r\nHost: {indirizzo}:{porta}\r\n"
                  f"Connection: close\r\n\r\n".encode())
        pezzi = []
        while True:
            d = s.recv(65536)
            if not d:
                break
            pezzi.append(d)
        return b"".join(pezzi), ""
    except OSError as e:
        # ⛔ E questo e' un esito, non un'assenza: §4.4-bis vieta «un errore di
        #    rete, un silenzio».  Chi legge questo campo deve poter distinguere
        #    «la pagina dice che non sono bannato» da «non ho parlato con
        #    nessuno» — sono la stessa faccia solo per chi non guarda.
        return b"", f"{type(e).__name__}: {e}"
    finally:
        try:
            (s or nudo).close()
        except OSError:
            pass


def leggi_pagina(indirizzo, porta, attesa=5.0, tls=True):
    """Chiede la pagina in TCP **da quell'indirizzo**, e legge che cosa dice.

    ⛔ L'indirizzo di provenienza non si dichiara: lo sceglie il nucleo, ed e'
       quello dell'interfaccia con cui si esce.  Chiedendo a `127.0.0.1` si
       arriva come `127.0.0.1`; chiedendo a `192.168.0.2` si arriva come
       `192.168.0.2`.  ⭐ E il server scrive nel registro **da quale** indirizzo
       ha ricevuto: il denominatore si legge dove la cosa succede."""
    fuori = {"indirizzo": indirizzo, "stato": None, "bannato": None,
             "restano_ms": None, "ore": None, "minuti": None,
             "frase": False, "byte": 0, "errore": "", "tls": tls}
    # ⛔⭐ IL DIALETTO DELLA PAGINA E' UNA DIFFERENZA FRA I DUE SERVER, e sono
    #     due rossi opposti pagati a un giorno di distanza (11 agosto 2026):
    #
    #       · questa funzione parlava HTTP IN CHIARO.  Contro l'innesto andava;
    #         contro il PRODOTTO il server chiudeva — `ConnectionResetError:
    #         [Errno 104]` da tutt'e due gli indirizzi — perche' li' la porta
    #         TCP serve HTTPS (`SPECIFICHE.md` §11.5);
    #       · la cura fu incartare SEMPRE in TLS, e ⛔ ha spostato il rosso
    #         sull'altro bersaglio: `[M]` 11 agosto sera, contro l'innesto,
    #         `SSLError: [SSL: WRONG_VERSION_NUMBER]` da tutt'e due gli
    #         indirizzi — perche' `01-b3-rcp-innesta.py` la pagina la scrive
    #         **in chiaro** (`HTTP/1.1 200 OK` su un fd nudo, nessuna riga di
    #         TLS in tutto il file).
    #
    # ⚠ In tutt'e due i casi il server faceva la cosa giusta e il banco leggeva
    #   un silenzio — la settima veste di `LEZIONI.md` §1.9 — e §4.4-bis vieta
    #   proprio al ban di presentarsi come «un errore di rete, un silenzio».
    #
    # ⭐ Quindi il dialetto lo DICHIARA chi chiama (dal bersaglio), e qui c'e' il
    #    controllo che dice no: se il dialetto dichiarato non risponde, si prova
    #    l'ALTRO — e se e' l'altro a rispondere, l'errore lo scrive a lettere,
    #    invece di lasciare «non ho parlato con nessuno».  ⛔ E' la differenza
    #    fra «la pagina non c'e'» e «la pagina la sto chiedendo nella lingua
    #    sbagliata», che senza questa riga hanno la stessa faccia.
    grezzo, errore = _chiedi_pagina(indirizzo, porta, attesa, tls)
    if errore:
        altro, err2 = _chiedi_pagina(indirizzo, porta, attesa, not tls)
        if not err2 and altro:
            fuori["errore"] = (
                f"⛔ IL DIALETTO E' L'ALTRO: chiesta in "
                f"{'TLS' if tls else 'chiaro'} ha dato «{errore}», e in "
                f"{'chiaro' if tls else 'TLS'} risponde ({len(altro)} byte). "
                f"Non e' «la pagina non risponde»: e' il bersaglio dichiarato "
                f"male, e i tre controlli della pagina qui sotto parlerebbero "
                f"del banco e non del server")
        else:
            fuori["errore"] = errore
        return fuori
    fuori["byte"] = len(grezzo)
    testo = grezzo.decode("utf-8", errors="replace")
    prima = testo.split("\r\n", 1)[0]
    m = re.match(r"HTTP/1\.[01] (\d{3})", prima)
    fuori["stato"] = int(m.group(1)) if m else None
    corpo = testo.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in testo else testo
    m = re.search(r'data-bannato="(si|no)"', corpo)
    if m:
        fuori["bannato"] = (m.group(1) == "si")
    m = re.search(r'data-restano-ms="(\d+)"', corpo)
    if m:
        fuori["restano_ms"] = int(m.group(1))
    m = re.search(r'id="ore">(\d+)<', corpo)
    if m:
        fuori["ore"] = int(m.group(1))
    m = re.search(r'id="minuti">(\d+)<', corpo)
    if m:
        fuori["minuti"] = int(m.group(1))
    fuori["frase"] = "tentativi esauriti" in corpo
    return fuori


# ===========================================================================
# ⛔ IL MODELLO DI §4.4-bis, APPLICATO AL PIANO PRIMA CHE AL FILO
# ===========================================================================
def simula(passi):
    """§4.4-bis letta come un modello, e applicata al piano prima di eseguirlo.

    Una chiave sola — **l'indirizzo** — perche' quella per nome utente non
    esiste piu' (`DECISIONI.md` §1.9).  ⛔ Tre nomi diversi contano tre.

    ⚠ La finestra dei cinque minuti qui e' presa per **sempre vera**: il modello
      suppone che tutti i tentativi di un blocco ci stiano dentro, che e' la
      lettura **pessimistica** — un giro piu' lungo farebbe scattare il ban di
      meno, mai di piu'.  ⭐ E' voluto: un modello ottimista lascerebbe partire
      un piano che sfora.

    ⚠ E' un MODELLO — la mia lettura dell'arbitro, scritta prima di misurare —
      non una prova.  Serve a due cose, e nessuna delle due e' «avere ragione»:
      dire **prima** se il piano resta sotto soglia, e dare a ogni singolo
      tentativo un'attesa invece di darne una complessiva.  Se il filo lo
      smentisce, uno dei due e' sbagliato e il banco dice **quale tentativo** li
      ha divisi.

    Restituisce (atteso per tentativo, picco dei fallimenti per indirizzo)."""
    falliti, bannati, picco, esiti = {}, set(), {}, []
    for p in passi:
        ind = p["indirizzo"]
        if p.get("azione") == "sblocca":
            # ⛔ Lo sblocco azzera la voce INTERA — ban e conteggio — perche' e'
            #    quel che `rcp_sblocca()` fa: `memset` della voce.
            #
            # ⛔ E FINO ALL'11 AGOSTO 2026 QUESTA RIGA ERA UNA CONVINZIONE
            #    (rilievo A22): su un indirizzo NON bannato lo sblocco risponde
            #    «NON-BANNATO», e che azzerasse comunque il conto non lo
            #    verificava nessuno — mentre l'intera strategia dei campioni
            #    («sbloccare fra un blocco e l'altro») ci poggia sopra.
            #    ⭐ Adesso e' misurato, e non da qui: `01-b8-prova-ban.c`
            #    sezione 5 fa fallire due volte, chiama `rcp_sblocca()` su un
            #    indirizzo che NON e' bannato, e verifica che il terzo
            #    fallimento non faccia scattare il ban.
            # ⚠ E il sintomo del caso opposto (§1.11), se un giorno tornasse:
            #   i fallimenti si accumulerebbero fra i blocchi, e i campioni
            #   comincerebbero a tornare `limitatore` — il verdetto lo dice, ed
            #   e' la prima delle quattro cause che stampa.
            falliti[ind] = 0
            bannati.discard(ind)
            esiti.append(("SBLOCCA", None, ""))
            continue
        if ind in bannati:
            esiti.append(("RESPINTO", TROPPI_TENTATIVI, "bannato"))
            continue
        if p["caso"] == "giusta":
            falliti[ind] = 0
            esiti.append(("AMMESSO", None, ""))
            continue
        falliti[ind] = falliti.get(ind, 0) + 1
        picco[ind] = max(picco.get(ind, 0), falliti[ind])
        # ⛔ Il terzo fallito riceve ancora `CREDENZIALI_ERRATE` — e' quello che
        #    FA scattare il ban, non il primo che lo subisce.  Chi si aspettasse
        #    il rifiuto gia' al terzo cercherebbe un difetto che non c'e'.
        esiti.append(("RESPINTO", CREDENZIALI_ERRATE, ""))
        if falliti[ind] >= SOGLIA:
            bannati.add(ind)
    return esiti, picco


def verifica_piano(passi, modo):
    """⛔ Il piano si verifica PRIMA di eseguirlo, e se non torna non si parte.

    Tre modi, perche' i piani sono di tre nature:

      `sotto-soglia`  nessun tentativo dev'essere bloccato, e nessun indirizzo
                      deve superare il BILANCIO.  E' il modo dei campioni;
      `banna-al-4`    il **quarto** tentativo DEVE essere bloccato, e nessuno
                      prima: e' il giro del ban;
      `non-banna`     nessun tentativo bloccato **e** almeno un indirizzo che
                      arriva a due fallimenti: e' il controllo dell'azzeramento,
                      e senza la seconda meta' sarebbe soddisfatto anche da un
                      piano che non fallisce mai — cioe' non proverebbe niente.
    """
    esiti, picco = simula(passi)
    bloccati = [i + 1 for i, (_m, mo, _c) in enumerate(esiti)
                if mo == TROPPI_TENTATIVI]
    righe = [f"picco dei fallimenti per indirizzo: "
             f"{ {k: v for k, v in sorted(picco.items())} or 'nessuno' }",
             f"tentativi che il modello vede bloccati: {bloccati or 'nessuno'}"]
    if modo == "sotto-soglia":
        ok = not bloccati and max(picco.values(), default=0) <= BILANCIO
        righe.append(f"atteso: nessun bloccato, e picco ≤ {BILANCIO} "
                     f"(soglia {SOGLIA})")
    elif modo == "banna-al-4":
        ok = bloccati == [4]
        righe.append("atteso: bloccato SOLO il quarto — i primi tre passano da "
                     "PAM, e il terzo e' quello che FA scattare il ban")
    elif modo == "non-banna":
        ok = (not bloccati) and max(picco.values(), default=0) >= 2
        righe.append("atteso: nessun bloccato, e almeno un indirizzo a 2 "
                     "fallimenti (se non ci arrivasse, il controllo sarebbe "
                     "verde per costruzione)")
    else:
        ok, _ = False, righe.append(f"modo sconosciuto: {modo}")
    return ok, esiti, righe


# ===========================================================================
# I piani
# ===========================================================================
def piano_campioni(k, per_caso, indirizzi, utente, inesistente):
    """Un blocco: `per_caso` terzine, con i fallimenti alternati fra gli indirizzi.

    ⛔ Gli indirizzi si alternano **fra i FALLIMENTI**, non fra i passi: solo i
       fallimenti muovono il conto di §4.4-bis, e alternare su tutti i passi
       lascerebbe l'alternanza in balia di dove cade il successo.

    ⚠ La rotazione parte da `k`, cosi' nessun caso resta legato a un indirizzo:
      se un giorno i due cammini avessero tempi diversi, la differenza si
      spalmerebbe su tutt'e tre le mediane invece di separarne una."""
    passi, falliti = [], 0
    for g in range(per_caso):
        for caso in ROTAZIONI[(k + g) % len(ROTAZIONI)]:
            ind = indirizzi[(falliti + k) % len(indirizzi)]
            if caso != "giusta":
                falliti += 1
            passi.append({"caso": caso, "indirizzo": ind,
                          "nome": inesistente if caso == "inesistente" else utente,
                          "scaldata": k == 0})
    return passi


def piano_ban(indirizzi, utente, nomi):
    """⛔ IL GIRO DEL BAN: tre fallite con TRE NOMI DIVERSI, poi la parola GIUSTA.

    ⭐ Il quarto tentativo **ha la parola d'ordine giusta** e dev'essere rifiutato
       lo stesso: *«e' la riga che distingue un ban da un contatore, ed e' anche
       il sintomo che l'utente vedra' — l'ho scritta giusta e non mi fa entrare —
       quindi e' voluto e va provato, non evitato»* (`fasi/01-filo-nudo.md` B8).

    ⛔ Tutti e quattro dallo STESSO indirizzo: il conto e' per indirizzo, e
       alternare qui vorrebbe dire non arrivare mai a tre."""
    a = indirizzi[0]
    passi = [{"caso": "inesistente", "indirizzo": a, "nome": nomi[0],
              "scaldata": False},
             {"caso": "sbagliata", "indirizzo": a, "nome": utente,
              "scaldata": False},
             {"caso": "inesistente", "indirizzo": a, "nome": nomi[2],
              "scaldata": False},
             # ⛔ il quarto: la parola GIUSTA
             {"caso": "giusta", "indirizzo": a, "nome": utente,
              "scaldata": False}]
    return passi


def piano_azzeramento(indirizzi, utente, inesistente):
    """⭐ IL CONTROLLO CHE DICE NO: 2 falliti · 1 riuscito · 2 falliti.

    *«Se il successo non azzerasse, il secondo blocco sarebbe gia' scattato»*
    (`fasi/01-filo-nudo.md` B8).  ⛔ Contando tutti i fallimenti, il **terzo** —
    cioe' il primo dopo il successo — sarebbe quello che fa scattare il ban su
    un server che non azzera.

    ⚠ Gira sul SECONDO indirizzo, e non e' un dettaglio: il primo lo si sta per
      bannare, e un controllo che dice «non e' bannato» condotto sull'indirizzo
      che verra' bannato subito dopo sarebbe illeggibile."""
    b = indirizzi[1]
    return [{"caso": "sbagliata", "indirizzo": b, "nome": utente, "scaldata": False},
            {"caso": "inesistente", "indirizzo": b, "nome": inesistente, "scaldata": False},
            {"caso": "giusta", "indirizzo": b, "nome": utente, "scaldata": False},
            {"caso": "sbagliata", "indirizzo": b, "nome": utente, "scaldata": False},
            {"caso": "inesistente", "indirizzo": b, "nome": inesistente, "scaldata": False}]


# ===========================================================================
# L'esecuzione
# ===========================================================================
# ⛔ IL BERSAGLIO ENTRA IN OGNI RIGA, e lo mette questa variabile invece dei
#    venti punti che chiamano `scrivi()`.  ⚠ Il caso concreto e' gia' sul disco:
#    `banchi/prodotto/b8-campioni.jsonl` sono i campioni del secondo fisso presi
#    contro il PRODOTTO la notte del 10 agosto, e `/media/REMOTIX/src/
#    b8-fatti.jsonl` quelli presi contro l'INNESTO.  Stesso nome, stessa forma,
#    stessi campi — e nessuna riga, in nessuno dei due, dice quale server ha
#    risposto.  Chi li mettesse insieme «per avere piu' campioni» calcolerebbe
#    la mediana di due popolazioni diverse credendo di ridurre il rumore.
BERSAGLIO = {"bersaglio": "non dichiarato", "porta": None, "md5": "ignota"}

# ⛔ Le righe che il lettore del registro cerca, e sono SCRITTE DIVERSE nei due
#    server: le riempie `principale()` dal profilo del bersaglio.  ⚠ I valori
#    qui sotto sono quelli dell'innesto e servono solo perche' il modulo si
#    possa importare: se restassero questi contro il prodotto, il lettore
#    direbbe «il server non ha detto niente sul ban» su un server che lo dice.
R_BAN = {"caricati": "ban caricati:",
         "illeggibile": "NON HO POTUTO LEGGERE il file dei ban",
         "pagina": "pagina TCP a"}


def scrivi(uscita, rec):
    """Una riga per fatto, scritta e **sincronizzata** subito.

    ⚠ Un file scritto e chiuso e' un fatto; una riga in un buffer e' una
      speranza sul momento in cui qualcuno la vedra' (`LEZIONI.md` §1.9, settima
      veste) — e questo processo muore e rinasce a ogni fase."""
    fuori = dict(BERSAGLIO)
    fuori.update(rec)
    with open(uscita, "a") as f:
        f.write(json.dumps(fuori, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def esistenza(nome, deve_esistere):
    """⛔ «Utente inesistente» si VERIFICA, non si suppone.

    Se il nome che crediamo inesistente fosse un utente vero, «inesistente» e
    «sbagliata» sarebbero **lo stesso caso** misurato due volte, e le due
    mediane coinciderebbero per costruzione: il verde piu' vuoto di tutti."""
    try:
        pwd.getpwnam(nome)
        c_e = True
    except KeyError:
        c_e = False
    return c_e == deve_esistere, c_e


async def prova_indirizzi(indirizzi, porta):
    """⛔ Il banco sa parlare da TUTT'E DUE gli indirizzi? — si chiede prima.

    ⚠ Si arriva a `ECCOMI` e si chiude: nessun `CREDENZIALI`, quindi **nessun
      conto si muove** e nessun posto viene preso.  E' un controllo che non
      costa niente al bilancio di §4.4-bis."""
    for ind in indirizzi:
        gestore = None
        try:
            gestore, cli, stato = await apri(ind, porta)
            if stato != "200":
                raise RuntimeError(f":status={stato}")
            cli.apri_controllo()
            cli.manda(inquadra(b3.T["CIAO"], b3.corpo_ciao()))
            await b3.attendi(cli, "ECCOMI", attesa=10)
        except Exception as e:  # noqa: BLE001
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ da «{ind}» non si arriva a ECCOMI: "
                  f"{type(e).__name__}: {e}")
            print(f"        il server dev'essere acceso su 0.0.0.0 e rispondere "
                  f"su tutt'e due gli indirizzi, o il bilancio di §4.4-bis non "
                  f"ha il margine che dichiara (B0.3)")
            return False
        finally:
            if gestore is not None:
                try:
                    await gestore.__aexit__(None, None, None)
                except Exception:  # noqa: BLE001
                    pass
    print(f"    {VERDE}OK{GRIGIO}  il server risponde su tutt'e due gli "
          f"indirizzi: {', '.join(indirizzi)}  (fino a ECCOMI, senza toccare "
          f"nessun conto)")
    return True


async def esegui(a, passi, tipo, etichetta, modo, confronta_modello=True):
    """Esegue un piano gia' verificato, e scrive un record per tentativo.

    ⚠ `confronta_modello=False` per l'unico caso in cui il modello **non puo'**
      sapere la risposta: il tentativo dopo il riavvio del server, dove il ban
      arriva dal DISCO e non dai fallimenti di questo giro.  Pretendere li' la
      concordanza col modello darebbe rosso sul codice giusto, e il rosso
      finirebbe sull'imputato sbagliato — che e' il difetto che `LEZIONI.md`
      §1.9 chiama la settima veste."""
    ok, esiti, righe = verifica_piano(passi, modo)
    print(f"    -- piano di «{etichetta}»: {len(passi)} tentativi, modo «{modo}» "
          f"(soglia {SOGLIA}, bilancio {BILANCIO}, finestra {FINESTRA_MIN} min)")
    for r in righe:
        print(f"       {r}")
    if not ok:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il piano non fa quel che deve: non parte. "
              f"Un piano che sfora misurerebbe il ban credendo di misurare PAM; "
              f"uno che non banna dove deve renderebbe cieco il controllo")
        return 2
    for i, p in enumerate(passi, 1):
        parola = a.parola if p["caso"] == "giusta" else a.sbagliata
        atteso_msg, atteso_motivo, _perche = esiti[i - 1]
        rec = await un_tentativo(p["indirizzo"], a.porta, p["nome"], parola)
        rec.update({"giro": a.giro, "tipo": tipo, "etichetta": etichetta,
                    "blocco": a.blocco, "ordine": i, "caso": p["caso"],
                    "scaldata": p["scaldata"],
                    "classe": classifica(rec, p["caso"]),
                    # ⭐ l'attesa del modello viaggia col tentativo: il verdetto
                    #    la confronta con quel che e' arrivato, uno per uno,
                    #    invece di guardare solo il totale.
                    "atteso_modello": atteso_msg,
                    "atteso_motivo": atteso_motivo})
        scrivi(a.uscita, rec)
        ms = "  —  " if rec["ms"] is None else f"{rec['ms']:8.1f}"
        motivo = MOTIVI.get(rec["motivo"], "") if rec["motivo"] is not None else ""
        atteso = MOTIVI.get(atteso_motivo, atteso_msg)
        chiude = "" if rec["chiusura"] is None else \
            f"chiusura={MOTIVI.get(rec['chiusura'], hex(rec['chiusura']))}"
        if not confronta_modello:
            concorda = "⚠ il modello non giudica qui (il ban viene dal disco)"
        elif rec["messaggio"] == atteso_msg and rec["motivo"] == atteso_motivo:
            concorda = ""
        else:
            concorda = f"⛔ il modello diceva {atteso}"
        marca = "scaldata" if p["scaldata"] else ""
        print(f"       {i:2d}. {p['caso']:12s} {p['indirizzo']:13s} "
              f"{p['nome']:16s} {ms} ms  "
              f"{rec['messaggio'] or rec['errore']:10s} {motivo:18s} "
              f"{rec['classe']:10s} {chiude} {marca} {concorda}")
    return 0


def pagina_in_tls(a):
    """⛔ In che lingua parla la pagina del ban, su QUESTO bersaglio.

    innesto   in chiaro — `01-b3-rcp-innesta.py` scrive `HTTP/1.1 200 OK` su un
              fd nudo, e in tutto il file non c'e' una riga di TLS;
    prodotto  in TLS — `SPECIFICHE.md` §11.5, e `01-p1-prodotto.sh` la
              interroga con `curl -k https://`.

    ⚠ E IL POSTO GIUSTO DI QUESTA RIGA NON E' QUI: e' il profilo condiviso
      (`01-b0-bersaglio.py`), accanto alle altre differenze fra i due server —
      la riga d'avvio sul ban, il formato della pagina, il tetto d'inattivita'.
      Sta scritto qui perche' la sera dell'11 agosto 2026 il profilo lo stanno
      usando altri tre banchi, e una chiave nuova la si aggiunge quando non c'e'
      nessun altro dentro.  ⛔ Finche' e' qui, e' una quinta copia di una
      differenza — cioe' esattamente la forma che R12C.5 ha gia' fatto pagare:
      si legge dal profilo appena la chiave esiste."""
    return bool(a.prof.get("pagina_tls", a.bersaglio == "prodotto"))


def guarda_pagina(a, indirizzo, etichetta, atteso_bannato):
    """La pagina, letta e SCRITTA nel file dei fatti — e confrontata subito."""
    rec = leggi_pagina(indirizzo, a.porta, tls=pagina_in_tls(a))
    rec.update({"giro": a.giro, "tipo": "pagina", "etichetta": etichetta,
                "atteso_bannato": atteso_bannato})
    scrivi(a.uscita, rec)
    if rec["errore"]:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ la pagina da «{indirizzo}» non si e' "
              f"caricata: {rec['errore']}")
        print(f"        §4.4-bis: «non un errore di rete, non un silenzio» — e "
              f"un silenzio e' esattamente quel che ho appena ricevuto")
        return rec
    quanto = "" if rec["ore"] is None else f" · mancano {rec['ore']}h {rec['minuti']}m"
    print(f"    -- pagina da {indirizzo:13s} → HTTP {rec['stato']} · "
          f"bannato={rec['bannato']} (atteso {atteso_bannato}) · "
          f"«tentativi esauriti» {'presente' if rec['frase'] else 'ASSENTE'}"
          f"{quanto} · {rec['byte']} byte")
    return rec


def sblocca_e_dichiara(a, indirizzi, perche, pretendi=None):
    """⛔ Ogni sblocco si dichiara — B0.3: «o *il ban non e' scattato* e
    *qualcuno l'ha tolto* hanno lo stesso aspetto»."""
    esiti = []
    for ind in indirizzi:
        esito, dettaglio = cmd.sblocca(a.comando, ind)
        rec = {"giro": a.giro, "tipo": "sblocco", "etichetta": perche,
               "indirizzo": ind, "esito": esito, "dettaglio": dettaglio,
               "preteso": pretendi}
        scrivi(a.uscita, rec)
        colore = ROSSO if esito is None else GRIGIO
        print(f"    {colore}--{GRIGIO}  sblocco «{ind}» ({perche}): "
              f"{esito or '⛔ NON HO PARLATO COL COMANDO'} — {dettaglio}")
        esiti.append(esito)
    return esiti


# ===========================================================================
# Le statistiche
# ===========================================================================
def quantile(xs, q):
    y = sorted(xs)
    if not y:
        return float("nan")
    i = min(len(y) - 1, max(0, int(round(q * (len(y) - 1)))))
    return y[i]


def mad(xs):
    """Scarto assoluto mediano: la dispersione della famiglia della mediana."""
    if len(xs) < 2:
        return float("nan")
    m = statistics.median(xs)
    return statistics.median([abs(x - m) for x in xs])


def intervallo_differenza(xa, xb):
    """L'intervallo al 95 % della differenza fra le due mediane, per ricampionamento.

    ⭐ Il seme e' fisso: due esecuzioni del verdetto sugli stessi campioni devono
       dare la **stessa** riga, o il banco diventa lui una sorgente di rumore."""
    r = random.Random(SEME)
    na, nb = len(xa), len(xb)
    diff = []
    for _ in range(RIPETIZIONI):
        ca = [xa[r.randrange(na)] for _ in range(na)]
        cb = [xb[r.randrange(nb)] for _ in range(nb)]
        diff.append(statistics.median(ca) - statistics.median(cb))
    diff.sort()
    lo = diff[int(0.025 * RIPETIZIONI)]
    hi = diff[min(RIPETIZIONI - 1, int(0.975 * RIPETIZIONI))]
    return lo, hi


# ===========================================================================
# Il registro del server: il secondo testimone, e NON e' l'arbitro
# ===========================================================================
def leggi_registro(percorso):
    """Che cosa dice il SERVER — per separare gli imputati, non per giudicare.

    ⛔ Non e' l'arbitro: il tempo che conta e' quello letto dal lato che riceve,
       e il registro e' la stessa mano che ha scritto il codice.  Serve a
       distinguere «a governare e' stato il ritardo fisso» da «a governare e'
       stato PAM», e a dire quante vite del server e quali indirizzi ci sono
       stati davvero.

    ⚠ Se il registro non c'e' o non dice niente, non si inventa: si dichiara.
      «Vuoto» e «non letto» sono due fatti diversi."""
    if not percorso or not os.path.exists(percorso):
        return None, "il registro del server non e' stato letto (file assente)"
    d = {"fissi": [], "ammessi": [], "respinti": [], "indirizzi": set(),
         "avvii": [], "ban": [], "sbloccati": [], "non_bannati": [],
         "pagine": [], "carichi": [], "illeggibili": 0, "vite": 0}
    ultimo_pam = None
    try:
        with open(percorso, errors="replace") as f:
            for riga in f:
                if "PAM ha risposto:" in riga:
                    ultimo_pam = "ammesso" if riga.rstrip().endswith("ammesso") else "respinto"
                elif "il secondo fisso e' passato" in riga:
                    try:
                        n = int(riga.split("(")[1].split(" ms")[0])
                    except (IndexError, ValueError):
                        continue
                    d["fissi"].append(n)
                    (d["ammessi"] if ultimo_pam == "ammesso" else d["respinti"]).append(n)
                elif " da=" in riga and ("respinto motivo" in riga or "ammesso utente" in riga):
                    d["indirizzi"].add(riga.rsplit(" da=", 1)[1].strip().rsplit(":", 1)[0])
                elif R_BAN["caricati"] in riga:
                    d["vite"] += 1
                    # ⛔⭐ E LA RIGA D'AVVIO E' SCRITTA DIVERSA NEI DUE SERVER.
                    #
                    #     innesto   «REMOTIX B3: ban caricati: N»
                    #     prodotto  «HH:MM:SS.mmm avvio  ban: <file>, N
                    #               indirizzi caricati»
                    #
                    #  ⚠ Cercare la forma dell'innesto contro il prodotto
                    #    avrebbe dato «vite = 0» e «il server non ha detto
                    #    NIENTE sul ban all'avvio»: un rosso pieno su un server
                    #    che quella riga la scrive, e il rosso sarebbe finito
                    #    sull'imputato sbagliato.
                    m = re.search(r"(-?\d+) indirizzi caricati", riga) or \
                        re.search(r"ban caricati: (-?\d+)", riga)
                    d["carichi"].append(int(m.group(1)) if m else None)
                    d["avvii"].append(riga.strip())
                elif R_BAN["illeggibile"] in riga:
                    d["vite"] += 1
                    d["illeggibili"] += 1
                    d["avvii"].append(riga.strip())
                elif "BANNATO l'indirizzo" in riga and "SBLOCCATO" not in riga:
                    d["ban"].append(riga.strip())
                elif "SBLOCCATO su comando" in riga:
                    d["sbloccati"].append(riga.strip())
                elif "NON era bannato, non ho tolto niente" in riga:
                    d["non_bannati"].append(riga.strip())
                elif R_BAN["pagina"] in riga:
                    d["pagine"].append(riga.strip())
    except OSError as e:
        return None, f"il registro del server non si legge: {e}"
    d["indirizzi"] = sorted(d["indirizzi"])
    if not d["fissi"] and not d["avvii"]:
        return None, ("il registro c'e' ma non contiene ne' righe «il secondo "
                      "fisso e' passato» ne' righe d'avvio: o non e' il registro "
                      "di questo giro, o il server non e' quello con RCP innestato")
    return d, ""


# ===========================================================================
# ⛔⭐ CHI GOVERNA I TEMPI — e si MISURA, non si scrive nel testo del verdetto
# ===========================================================================
# *Rilievo A18 della revisione R12-A, 11 agosto 2026.*  Fino a stanotte questa
# risposta era **una frase costante**: qualunque coppia di mediane si separasse
# — e per qualunque ragione — il verdetto stampava *«a governare i tempi e' PAM,
# e la cura sta in `autenticazione.c` e nella pila PAM, non in `rcp.c`»*.  Il
# numero che avrebbe dovuto sostenerla era calcolato due righe sopra e **non
# condizionava niente**; col registro illeggibile diventava *«dopo una mediana
# di None ms … a governare i tempi e' PAM»*.
#
# ⛔ Un verdetto che nomina sempre lo stesso imputato non sta diagnosticando:
#    sta ripetendo una convinzione.  Ed e' la **settima veste** di `LEZIONI.md`
#    §1.9 — *il rosso puntato sull'imputato sbagliato* — dentro il banco che
#    quella lezione cita: manda a cercare in `autenticazione.c` e nella pila PAM
#    chiunque abbia rallentato **il nostro percorso**, e piu' il posto e'
#    plausibile piu' a lungo ci si resta.
#
# ⭐ IL CASO CONCRETO CHE L'HA FATTO VEDERE (`[M]` 11 agosto 2026, riprodotto su
#    fatti costruiti a mano): si mette due secondi di lavoro nostro sul percorso
#    dell'`AMMESSO` — un `getpwnam` lento, una scrittura sincrona — e si lascia
#    PAM a rispondere in 5 ms.  Il registro del server dice «il secondo fisso e'
#    passato» a **1005 ms sui respinti e 1010 sugli ammessi**, cioe' il ritardo
#    fisso ha coperto tutto e PAM non ha ritardato niente; la coppia
#    «sbagliata − giusta» si separa di due secondi **per colpa nostra**; e il
#    verdetto vecchio consegnava «e' PAM, la cura sta altrove».
#
# ⛔ LA REGOLA, ED E' §1.11: per ogni prova indiretta si scrive che aspetto
#    avrebbe il caso opposto.  Qui i due casi opposti hanno **due firme
#    numeriche diverse nel registro del server**, e questa funzione le legge:
#
#      PAM ritarda i fallimenti   il server aspetta MOLTO oltre il secondo fisso
#      (`pam_faildelay`)          prima di rispondere ai RESPINTI, e poco o
#                                 niente prima degli AMMESSI  ⇒  respinti ≫ 1000
#                                 e respinti ≫ ammessi, e il caso lento sul filo
#                                 e' uno dei due respinti
#      il ritardo e' NOSTRO       il server dichiara di aver risposto quasi
#                                 subito dopo il secondo fisso (respinti ≈
#                                 ammessi ≈ 1000) e le mediane si separano lo
#                                 stesso — oppure e' l'AMMESSO ad essere lento,
#                                 che e' il percorso in cui PAM non ha voce
#
# ⛔ E il terzo esito e' «non lo so», che e' quel che il verdetto vecchio non
#    aveva: senza il registro non si nomina nessuno.
def imputato_dei_tempi(serie, reg):
    """(nome, righe) con nome in «PAM» · «NOSTRO» · None (non misurato)."""
    righe = []
    if reg is None:
        return None, ["⛔ il registro del server non si e' letto: NESSUN "
                      "imputato si puo' nominare, e nominarlo lo stesso "
                      "sarebbe la settima veste di `LEZIONI.md` §1.9"]
    resp = statistics.median(reg["respinti"]) if reg["respinti"] else None
    amm = statistics.median(reg["ammessi"]) if reg["ammessi"] else None
    if resp is None or amm is None:
        return None, [f"⛔ il registro non porta le due mediane che servono "
                      f"(respinti: {len(reg['respinti'])} righe · ammessi: "
                      f"{len(reg['ammessi'])} righe): senza tutt'e due non si "
                      f"distingue «PAM ritarda i fallimenti» da «il ritardo e' "
                      f"nostro», e non si nomina nessuno"]
    med = {c: statistics.median(serie[c]) for c in CASI if serie[c]}
    if not med:
        return None, ["⛔ nessuna serie di campioni: non c'e' nessuna "
                      "separazione da attribuire"]
    lento = max(med, key=med.get)
    oltre_r, oltre_a = resp - RITARDO_FISSO, amm - RITARDO_FISSO
    righe.append(f"quel che il SERVER dichiara di aver aspettato oltre il "
                 f"secondo fisso: respinti {oltre_r:+.0f} ms · ammessi "
                 f"{oltre_a:+.0f} ms  (margine {MARGINE_IMPUTATO:.0f} ms)")
    righe.append(f"il caso piu' lento sul FILO: «{lento}» "
                 f"({med[lento]:.0f} ms)  ·  " +
                 " · ".join(f"{c} {med[c]:.0f}" for c in CASI if c in med))
    if oltre_r >= MARGINE_IMPUTATO and (resp - amm) >= MARGINE_IMPUTATO \
            and lento != "giusta":
        righe.append("⇒ ⛔ A GOVERNARE I TEMPI E' **PAM**: il server ha "
                     "aspettato oltre il secondo fisso SOLO sui fallimenti, "
                     "che e' la firma di `pam_faildelay`, e il caso lento sul "
                     "filo e' un respinto.  La cura sta in "
                     "`banchi/rcp/autenticazione.c` e nella pila PAM, non in "
                     "`rcp.c`")
        return "PAM", righe
    if lento == "giusta" or (oltre_a - oltre_r) >= MARGINE_IMPUTATO:
        righe.append("⇒ ⛔ L'IMPUTATO NON E' PAM: il percorso lento e' quello "
                     "dell'AMMESSO, dove `pam_faildelay` non ha voce — "
                     "`pam_faildelay` ritarda i FALLIMENTI.  Il ritardo e' "
                     "NOSTRO, e si cerca sul cammino che porta ad `AMMESSO` "
                     "(rcp.c: `S_ATTESA_VERDETTO` → `T_AMMESSO`), non nella "
                     "pila PAM")
        return "NOSTRO", righe
    if oltre_r < MARGINE_IMPUTATO and oltre_a < MARGINE_IMPUTATO:
        righe.append("⇒ ⛔ L'IMPUTATO NON E' PAM: il server dichiara di aver "
                     "risposto quasi subito dopo il secondo fisso in tutt'e "
                     "due i versi — cioe' il ritardo fisso ha coperto tutto e "
                     "PAM non ha ritardato niente — e le mediane si separano "
                     "LO STESSO.  Il tempo si perde FUORI dal punto in cui il "
                     "server lo misura: il nostro percorso, o la rete")
        return "NOSTRO", righe
    righe.append("⇒ ⚠ I NUMERI NON SEPARANO I DUE IMPUTATI: il registro dice "
                 "che qualcuno ha aspettato oltre il secondo fisso, ma non nel "
                 "verso che distingue PAM dal nostro percorso.  Non si nomina "
                 "nessuno — «non lo so» e' un esito, «e' PAM» detto per "
                 "abitudine non lo e'")
    return None, righe


# ===========================================================================
# Il verdetto
# ===========================================================================
def _serie(campioni, caso):
    return [r["ms"] for r in campioni
            if r["caso"] == caso and not r["scaldata"] and r["classe"] == "atteso"]


def verdetto(a):
    if not os.path.exists(a.uscita):
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ non c'e' niente da giudicare: "
              f"{a.uscita} non esiste")
        return 2
    dati = []
    with open(a.uscita) as f:
        for riga in f:
            riga = riga.strip()
            if riga:
                dati.append(json.loads(riga))
    # ⛔ Un file di un ALTRO giro non e' un file vuoto, e non e' questo giro.
    estranei = [r for r in dati if r.get("giro") != a.giro]
    if estranei:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ {len(estranei)} righe su {len(dati)} sono "
              f"di un altro giro: non giudico un file stantio")
        return 2
    if not dati:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il file c'e' ed e' vuoto: nessun fatto")
        return 2

    # ⛔ DUE CONTATORI, E NON E' UN'INDULGENZA — e' `LEZIONI.md` §1.11 e la
    #    regola dei «quattro esiti, non due».
    #
    #    `guasti` conta quel che questo banco ha il diritto di chiamare un
    #    difetto NOSTRO.  `guasti_mediane` conta la sola cosa che §4.4-bis ha
    #    gia' dichiarato `[?]` prima che questo banco esistesse: che a governare
    #    i tempi dell'autenticazione **non e' il nostro ritardo, e' PAM**.
    #
    # ⛔ E la differenza non e' cosmetica: se le due cose finissero nello stesso
    #    numero, B8 sarebbe **rosso per sempre** — e un banco sempre rosso non
    #    fa fallire nessuna regressione, perche' nessuno lo guarda piu'.  ⚠ La
    #    separazione delle mediane resta stampata a caratteri interi, l'esito
    #    resta diverso da zero, e il colpevole viene NOMINATO: quel che si toglie
    #    e' la confusione fra «il ban non funziona» e «PAM ritarda i
    #    fallimenti», che sono due cure diverse in due file diversi.
    guasti, guasti_mediane, sospeso = 0, 0, False
    campioni = [r for r in dati if r["tipo"] == "campione"]
    tentativi = [r for r in dati if r["tipo"] in ("campione", "ban", "controllo")]
    pagine = [r for r in dati if r["tipo"] == "pagina"]
    sblocchi = [r for r in dati if r["tipo"] == "sblocco"]
    blocchi = sorted({r["blocco"] for r in campioni})

    # ── 0. i denominatori ───────────────────────────────────────────────────
    print()
    print("    == I DENOMINATORI — su che cosa ha guardato questo giro")
    print(f"    --  fatti registrati: {len(dati)}  (tentativi {len(tentativi)} · "
          f"letture della pagina {len(pagine)} · sblocchi {len(sblocchi)})")
    print(f"    --  blocchi di campioni: {len(blocchi)}  "
          f"(fra un blocco e l'altro si sblocca, ed e' dichiarato)")
    # ⛔ E un verdetto ha un denominatore: quante cose ha approvato
    #    (`LEZIONI.md` §1.9 regola 6).  Se e' zero non si da' nessun esito.
    if not tentativi:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ ZERO tentativi: «tutti quelli provati "
              f"sono andati bene» e' vero anche quando i provati sono zero")
        return 2

    serie = {}
    for caso in CASI:
        del_caso = [r for r in campioni if r["caso"] == caso]
        scaldate = [r for r in del_caso if r["scaldata"]]
        tenuti = [r for r in del_caso if not r["scaldata"]]
        buoni = [r for r in tenuti if r["classe"] == "atteso"]
        serie[caso] = [r["ms"] for r in buoni]
        limitati = [r for r in tenuti if r["classe"] == "limitatore"]
        inattesi = [r for r in tenuti if r["classe"] == "inatteso"]
        errori = [r for r in tenuti if r["classe"] == "errore"]
        per_ind = {}
        for r in buoni:
            per_ind[r["indirizzo"]] = per_ind.get(r["indirizzo"], 0) + 1
        print(f"    --  {caso:12s} tenuti {len(buoni):3d} su {len(tenuti):3d} · "
              f"scartati per scaldata {len(scaldate)} · "
              f"⛔ risposte del ban {len(limitati)} · inattese {len(inattesi)} · "
              f"errori {len(errori)} · indirizzi {per_ind}")
        if limitati:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ {len(limitati)} campioni di «{caso}» "
                  f"hanno ricevuto TROPPI_TENTATIVI: il bilancio di §4.4-bis non "
                  f"ha retto, e quei tempi sono del BAN, non di PAM")
            print(f"        ⚠ quattro cause, e vanno separate: (1) lo sblocco fra "
                  f"i blocchi non ha funzionato; (2) il piano sfora davvero; "
                  f"(3) un blocco precedente ha lasciato dei fallimenti; "
                  f"(4) il server conta piu' di quel che §4.4-bis dice")
            guasti += 1
        if inattesi or errori:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ «{caso}»: {len(inattesi)} risposte "
                  f"inattese e {len(errori)} errori — un caso che non riceve quel "
                  f"che deve non e' un campione di quel caso")
            for r in (inattesi + errori)[:3]:
                print(f"        {r['messaggio'] or ''} {r['errore']}")
            guasti += 1

    # ── 1. il secondo fisso ─────────────────────────────────────────────────
    print()
    print(f"    == ⛔ Primo criterio: nessuna risposta di PAM prima di "
          f"{RITARDO_FISSO:.0f} ms (§4.4-bis)")
    da_pam = [r for r in tentativi if r["classe"] == "atteso" and r["ms"] is not None]
    sotto = [r for r in da_pam if r["ms"] < RITARDO_FISSO]
    print(f"    --  guardate {len(da_pam)} risposte (campioni, scaldate e giro "
          f"del ban insieme: il ritardo fisso vale per TUTTE, «anche quando la "
          f"risposta e' AMMESSO»)")
    if not da_pam:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ nessuna risposta da guardare")
        guasti += 1
    elif sotto:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ {len(sotto)} risposte sotto il secondo. "
              f"La piu' veloce: {min(r['ms'] for r in sotto):.1f} ms")
        for r in sotto[:5]:
            print(f"        {r['caso']:12s} {r['messaggio']} {r['ms']:.1f} ms")
        guasti += 1
    else:
        print(f"    {VERDE}OK{GRIGIO}  {len(da_pam)} su {len(da_pam)} ≥ "
              f"{RITARDO_FISSO:.0f} ms — la piu' veloce: "
              f"{min(r['ms'] for r in da_pam):.1f} ms")
    # ⚠ E il rifiuto del ban si misura A PARTE, e NON fa ne' rosso ne' verde.
    #   §4.4-bis dice che «il rifiuto di un indirizzo bannato non passa dal
    #   secondo fisso»; `rcp.c` lo fa passare lo stesso, perche' decide DOPO
    #   aver ricevuto `CREDENZIALI` — che e' l'unica strada che gli lascia un
    #   `RESPINTO` da mandare, cioe' quel che B8 pretende.  Due letture, e la
    #   differenza si misura invece di giudicarla.
    del_ban = [r["ms"] for r in tentativi
               if r["classe"] == "limitatore" and r["ms"] is not None]
    if del_ban:
        print(f"    --  ⚠ e le risposte TROPPI_TENTATIVI (che non passano da PAM): "
              f"n={len(del_ban)}  mediana {statistics.median(del_ban):.1f} ms  "
              f"min {min(del_ban):.1f} ms")
        print(f"        §4.4-bis dice che questo rifiuto «non passa dal secondo "
              f"fisso»; rcp.c ce lo fa passare.  Il numero e' qui, e non e' un "
              f"esito: e' un difetto del documento da chiudere in un verso o "
              f"nell'altro")
    else:
        print(f"    --  ⛔ nessuna risposta TROPPI_TENTATIVI in tutto il giro: il "
              f"giro del ban qui sotto non puo' essere passato")

    # ── 2. le tre mediane ───────────────────────────────────────────────────
    print()
    print("    == ⛔ Secondo criterio: le tre mediane, e se si separano")
    for caso in CASI:
        x = serie[caso]
        if not x:
            print(f"    --  {caso:12s} n=0 — nessun campione")
            continue
        print(f"    --  {caso:12s} n={len(x):3d}  min {min(x):8.1f}  "
              f"p25 {quantile(x, .25):8.1f}  mediana {statistics.median(x):8.1f}  "
              f"p75 {quantile(x, .75):8.1f}  max {max(x):8.1f}  "
              f"MAD {mad(x):6.1f}   (ms)")

    magri = [c for c in CASI if len(serie[c]) < MINIMO_CAMPIONI]
    if magri:
        print(f"    {GIALLO}??{GRIGIO}  ⚠ meno di {MINIMO_CAMPIONI} campioni per "
              f"{', '.join(magri)}: il verdetto sulle mediane e' SOSPESO, non verde")
        sospeso = True

    print()
    print("    differenza delle mediane, con l'intervallo al 95 % che la contiene:")
    for u, v in (("inesistente", "sbagliata"), ("inesistente", "giusta"),
                 ("sbagliata", "giusta")):
        xa, xb = serie[u], serie[v]
        if len(xa) < 3 or len(xb) < 3:
            print(f"    {GIALLO}??{GRIGIO}  {u} − {v}: campioni insufficienti "
                  f"({len(xa)} e {len(xb)})")
            sospeso = True
            continue
        d = statistics.median(xa) - statistics.median(xb)
        lo, hi = intervallo_differenza(xa, xb)
        risoluzione = (hi - lo) / 2.0
        contiene_zero = lo <= 0.0 <= hi
        n_ora = min(len(xa), len(xb))
        n_serve = int(n_ora * (risoluzione / RISOLUZIONE_VOLUTA) ** 2) + 1
        marca = f"{ROSSO}SI DISTINGUONO{GRIGIO}" if not contiene_zero else (
            f"{VERDE}indistinguibili{GRIGIO}" if risoluzione <= RISOLUZIONE_VOLUTA
            else f"{GIALLO}SOSPESO{GRIGIO}")
        segreto = (u, v) == ("inesistente", "sbagliata")
        nota = "  ⚠ e' QUESTA la coppia che dice i nomi degli utenti" if segreto \
            else "  (⚠ questa coppia non porta nessun segreto: vedi sotto)"
        print(f"      {u:12s} − {v:12s} {d:+9.1f} ms   "
              f"[{lo:+8.1f}; {hi:+8.1f}]   risoluzione ±{risoluzione:.1f} ms   "
              f"{marca}{nota}")
        if not contiene_zero:
            # ⛔⭐ E QUI LE TRE COPPIE NON VALGONO LA STESSA COSA, ED E' UN PUNTO
            #    IN CUI I DOCUMENTI AMMETTONO DUE LETTURE.
            #
            #    `fasi/01-filo-nudo.md` B8 chiede **le tre mediane
            #    indistinguibili**, e §4.4-bis vuole il ritardo fisso «anche
            #    quando la risposta e' AMMESSO».  ⚠ Ma quel che §4.4 VIETA di
            #    far sapere e' una cosa sola: se un nome utente esista — «il
            #    server NON DEVE distinguere nel motivo fra utente inesistente e
            #    parola d'ordine sbagliata».
            #
            #    ⛔ «Ammesso» contro «respinto», invece, il filo lo dice da se':
            #       sono due MESSAGGI diversi, `AMMESSO` e `RESPINTO`.  Un
            #       cronometro che li separa non aggiunge niente a quel che il
            #       client legge gia' nel messaggio.
            #
            # ⭐ Quindi: la coppia «inesistente − sbagliata» che si separa e' un
            #    difetto NOSTRO e va in rosso pieno.  Le altre due che si
            #    separano vanno nel loro contatore, che porta a un esito
            #    diverso e col colpevole nominato.  ⚠ Non si sceglie la lettura
            #    comoda e non si tace: si eseguono tutt'e due e si dice quale
            #    numero appartiene a quale.
            if segreto:
                print(f"           ⛔ E QUESTA E' LA SEPARAZIONE CHE §4.4 VIETA: "
                      f"col cronometro si legge se un nome utente esiste, che e' "
                      f"esattamente la cosa che il divieto sul motivo esiste per "
                      f"nascondere")
                guasti += 1
            else:
                print(f"           ⚠ questa separazione NON dice niente che il "
                      f"filo non dica gia': «ammesso» e «respinto» sono due "
                      f"MESSAGGI diversi (§4.4).  Conta lo stesso — "
                      f"`fasi/01-filo-nudo.md` B8 chiede le TRE mediane "
                      f"indistinguibili — ma nel suo contatore, e col colpevole "
                      f"nominato in fondo")
                guasti_mediane += 1
        elif risoluzione > RISOLUZIONE_VOLUTA:
            print(f"           ⚠ per arrivare a ±{RISOLUZIONE_VOLUTA:.0f} ms con "
                  f"questo rumore servirebbero ~{n_serve} campioni per caso "
                  f"(adesso {n_ora})")
            sospeso = True

    # ── 3. il giro del ban ──────────────────────────────────────────────────
    print()
    print("    == ⛔ Il ban: tre fallite con TRE NOMI DIVERSI, poi la parola GIUSTA")
    giro = sorted([r for r in dati if r["tipo"] == "ban"], key=lambda r: r["ordine"])
    if len(giro) != 4:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il giro del ban ha {len(giro)} tentativi "
              f"invece di 4: non e' la sequenza che §4.4-bis descrive")
        guasti += 1
    else:
        def nomina(msg, motivo):
            return MOTIVI.get(motivo, str(motivo)) if motivo is not None else (msg or "errore")
        print(f"        nomi:     " + " ".join(f"{r['nome']:18s}" for r in giro))
        print(f"        modello:  " + " ".join(
            f"{nomina(r['atteso_modello'], r['atteso_motivo']):18s}" for r in giro))
        print(f"        sul filo: " + " ".join(
            f"{nomina(r['messaggio'], r['motivo']):18s}" for r in giro))
        # ⛔ I TRE NOMI DEVONO ESSERE DIVERSI, e lo confronta il banco.
        nomi = [r["nome"] for r in giro[:3]]
        if len(set(nomi)) != 3:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ i tre nomi non sono diversi ({nomi}): "
                  f"con lo stesso nome tre volte un server col vecchio contatore "
                  f"PER NOME darebbe verde, e il banco proverebbe la regola "
                  f"sbagliata")
            guasti += 1
        else:
            print(f"    {VERDE}OK{GRIGIO}  i tre nomi sono diversi: il conto "
                  f"guarda l'indirizzo e non il nome (`DECISIONI.md` §1.9)")
        divergenti = [r["ordine"] for r in giro
                      if r["messaggio"] != r["atteso_modello"]
                      or r["motivo"] != r["atteso_motivo"]]
        if divergenti:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ il filo e il modello di §4.4-bis si "
                  f"dividono ai tentativi {divergenti}")
            guasti += 1
        quarto = giro[3]
        if quarto["motivo"] == TROPPI_TENTATIVI:
            print(f"    {VERDE}OK{GRIGIO}  ⭐ il QUARTO tentativo aveva la parola "
                  f"d'ordine GIUSTA ed e' stato rifiutato lo stesso, con "
                  f"TROPPI_TENTATIVI: e' la riga che distingue un ban da un "
                  f"contatore")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ il quarto tentativo — parola GIUSTA — "
                  f"ha ricevuto {nomina(quarto['messaggio'], quarto['motivo'])} "
                  f"invece di TROPPI_TENTATIVI")
            print(f"        ⚠ e se e' AMMESSO, il ban non e' scattato: guarda il "
                  f"registro del server qui sotto, riga «BANNATO l'indirizzo»")
            guasti += 1
        # ⛔ E la scheda gia' aperta: il motivo viaggia ANCHE nel codice di
        #    chiusura della sessione (§3.1 punto 3, §4.4-bis punto 2), e si
        #    verifica DAL LATO CHE RICEVE.
        if quarto.get("chiusura") == TROPPI_TENTATIVI:
            print(f"    {VERDE}OK{GRIGIO}  ⭐ e la sessione WebTransport si e' "
                  f"chiusa con TROPPI_TENTATIVI nel codice d'errore "
                  f"applicativo — letto dal lato che riceve (§3.1 punto 3)")
        else:
            c = quarto.get("chiusura")
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ il codice di chiusura della sessione "
                  f"e' {MOTIVI.get(c, c)}, non TROPPI_TENTATIVI: la scheda gia' "
                  f"aperta — quella che non ricarica la pagina — resterebbe ad "
                  f"aspettare (§4.4-bis punto 2)")
            guasti += 1

    # ── 4. i tre controlli che dicono NO ────────────────────────────────────
    print()
    print("    == ⭐ I tre controlli che dicono NO")

    # 4a. un altro indirizzo entra subito
    altro = [r for r in dati if r["tipo"] == "controllo"
             and r["etichetta"] == "altro-indirizzo"]
    if not altro:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ manca il controllo «un altro indirizzo "
              f"entra»: senza, «il quarto e' rifiutato» e' compatibile con un "
              f"server che ha smesso di funzionare")
        guasti += 1
    elif all(r["messaggio"] == "AMMESSO" for r in altro):
        print(f"    {VERDE}OK{GRIGIO}  1. un ALTRO indirizzo entra subito con le "
              f"credenziali buone ({len(altro)} tentativi): il server non ha "
              f"smesso di funzionare, e il conto e' per indirizzo")
    else:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ 1. l'altro indirizzo NON entra: "
              f"{[r['messaggio'] for r in altro]}")
        print(f"        ⚠ quattro cause: (1) il ban non e' per indirizzo — il "
              f"difetto; (2) quell'indirizzo ha un conto suo aperto; (3) PAM non "
              f"consente di verificare quell'utente; (4) l'utente non esiste o "
              f"non ha parola d'ordine")
        guasti += 1

    # 4b. l'azzeramento
    azz = sorted([r for r in dati if r["tipo"] == "controllo"
                  and r["etichetta"] == "azzeramento"], key=lambda r: r["ordine"])
    if len(azz) != 5:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ 2. il controllo dell'azzeramento ha "
              f"{len(azz)} tentativi invece di 5")
        guasti += 1
    else:
        motivi = [r["motivo"] for r in azz]
        bloccati = [r["ordine"] for r in azz if r["motivo"] == TROPPI_TENTATIVI]
        if not bloccati and azz[2]["messaggio"] == "AMMESSO":
            print(f"    {VERDE}OK{GRIGIO}  2. due falliti · UNO RIUSCITO · due "
                  f"falliti: nessun blocco.  Se il successo non azzerasse, il "
                  f"terzo fallito avrebbe fatto scattare il ban")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ 2. l'azzeramento non c'e' stato "
                  f"(bloccati: {bloccati or 'nessuno'}; il terzo passo ha "
                  f"ricevuto {azz[2]['messaggio']})")
            guasti += 1
        # ⛔ E il controllo del controllo: la pagina deve dire che quell'indirizzo
        #    NON e' bannato.  Senza, «nessun blocco» sarebbe compatibile con un
        #    server che ha bannato e non lo dice.
        dopo = [r for r in pagine if r["etichetta"] == "azzeramento-dopo"]
        if dopo and dopo[0].get("bannato") is False:
            print(f"        ⭐ e la pagina lo conferma da fuori: quell'indirizzo "
                  f"non e' bannato (il conto vale {len([m for m in motivi if m == CREDENZIALI_ERRATE])} "
                  f"su {SOGLIA})")
        elif dopo:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ ma la pagina dice bannato="
                  f"{dopo[0].get('bannato')}: il filo e la pagina non concordano")
            guasti += 1

    # 4c. la persistenza
    print()
    prima = [r for r in pagine if r["etichetta"] == "bannato-prima"]
    dopo = [r for r in pagine if r["etichetta"] == "bannato-dopo-riavvio"]
    filo_dopo = [r for r in dati if r["tipo"] == "controllo"
                 and r["etichetta"] == "dopo-riavvio"]
    if not prima or not dopo:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ 3. la persistenza non e' stata provata "
              f"(pagina prima: {len(prima)}, dopo il riavvio: {len(dopo)}): "
              f"senza, il ban puo' vivere in memoria e un aggiornamento del "
              f"pacchetto regala tre tentativi a chiunque — invariante I7")
        guasti += 1
    elif dopo[0].get("bannato") is True and filo_dopo and \
            all(r["motivo"] == TROPPI_TENTATIVI for r in filo_dopo):
        print(f"    {VERDE}OK{GRIGIO}  3. il ban SOPRAVVIVE al riavvio del "
              f"server: dopo la seconda accensione la pagina lo dice ancora, e "
              f"sul filo il tentativo con la parola giusta riceve ancora "
              f"TROPPI_TENTATIVI")
    else:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ 3. dopo il riavvio l'indirizzo non e' "
              f"piu' bannato: pagina bannato={dopo[0].get('bannato')}, sul filo "
              f"{[MOTIVI.get(r['motivo'], r['messaggio']) for r in filo_dopo]}")
        guasti += 1

    # ── 5. quel che l'utente vede ───────────────────────────────────────────
    print()
    print("    == ⛔ Quel che l'utente vede: la pagina si carica LO STESSO")
    # ⛔ E si dichiara che cosa questa lettura NON e', qui e non solo nei
    #    commenti: chi legge un verdetto legge il verdetto.
    print(f"    --  `[?]` letto con un socket, non con un browser: la frase la "
          f"scrive il server nel corpo e nessuno script la costruisce, quindi "
          f"quel che un browser mostrerebbe e' questo testo — ⚠ ma un motore "
          f"vero non l'ha guardata, e `fasi/01-filo-nudo.md` B8 chiede il DOM "
          f"«come per le otto frasi di B7»")
    # ⛔ E DI QUALE SERVER PARLANO QUESTE TRE RIGHE — R12.2, e si stampa nel
    #    verdetto perche' chi legge un verdetto legge il verdetto.
    print(f"    --  ⛔ i tre marcatori cercati qui (`data-bannato`, "
          f"`data-restano-ms`, «tentativi esauriti») li produce SOLO l'innesto "
          f"di `01-b3-rcp-innesta.py`.  Il server di prodotto in `src/` scrive "
          f"la stessa cosa in un formato senza un campo in comune: puntando "
          f"questo banco li', queste tre righe diventerebbero rosse SU UN "
          f"SERVER CHE IL BAN LO FA")
    if not pagine:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ nessuna lettura della pagina: il punto 1 "
              f"di §4.4-bis non e' stato provato affatto")
        guasti += 1
    for r in pagine:
        atteso = r["atteso_bannato"]
        buona = (not r["errore"] and r["stato"] == 200
                 and r["bannato"] is atteso
                 and (r["frase"] if atteso else not r["frase"]))
        if atteso and buona:
            buona = r["ore"] is not None
        segno = f"{VERDE}OK{GRIGIO}" if buona else f"{ROSSO}NO{GRIGIO}"
        print(f"    {segno}  {r['etichetta']:22s} da {r['indirizzo']:13s} → "
              f"HTTP {r['stato']} · bannato={r['bannato']} (atteso {atteso}) · "
              f"frase={r['frase']} · ore={r['ore']} minuti={r['minuti']}"
              f"{' · ⛔ ' + r['errore'] if r['errore'] else ''}")
        if not buona:
            guasti += 1
    bannate = [r for r in pagine if r["atteso_bannato"] and r["ore"] is not None]
    if bannate:
        ore = bannate[0]["ore"]
        # ⚠ Le ore che mancano devono essere PLAUSIBILI: 12 appena bannati.  Un
        #   «restano 0 ore» o un «restano 4 miliardi» direbbe che l'orologio
        #   della pagina non e' quello della sessione — il difetto piu' facile
        #   da fare e il piu' difficile da vedere.
        if 1 <= ore <= BAN_ORE:
            print(f"    {VERDE}OK{GRIGIO}  e le ore che mancano sono plausibili "
                  f"({ore} su {BAN_ORE}): l'orologio della pagina e' quello "
                  f"della sessione")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ la pagina dice che mancano {ore} ore, "
                  f"e il ban dura {BAN_ORE}: i due orologi non sono lo stesso")
            guasti += 1

    # ── 6. lo sblocco — e si prova IN FONDO ─────────────────────────────────
    print()
    print("    == ⛔ Il comando di sblocco, provato IN FONDO (B0.3)")
    finali = [r for r in sblocchi if r["etichetta"].startswith("prova-")]
    if not finali:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ lo sblocco non e' stato provato su un ban "
              f"vero: «tolto» e «non c'era» non sono stati distinti")
        guasti += 1
    for r in finali:
        buono = r["esito"] == r["preteso"]
        segno = f"{VERDE}OK{GRIGIO}" if buono else f"{ROSSO}NO{GRIGIO}"
        print(f"    {segno}  {r['etichetta']:22s} «{r['indirizzo']}» → "
              f"{r['esito']} (atteso {r['preteso']})")
        if not buono:
            guasti += 1
    dopo_sblocco = [r for r in dati if r["tipo"] == "controllo"
                    and r["etichetta"] == "dopo-sblocco"]
    if dopo_sblocco and all(r["messaggio"] == "AMMESSO" for r in dopo_sblocco):
        print(f"    {VERDE}OK{GRIGIO}  ⭐ e dopo lo sblocco quell'indirizzo ENTRA: "
              f"lo sblocco non ha solo cambiato una risposta, ha rimesso "
              f"l'indirizzo dentro")
    else:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ dopo lo sblocco l'indirizzo non entra "
              f"({[r['messaggio'] for r in dopo_sblocco] or 'non provato'})")
        guasti += 1

    # ── 7. il secondo testimone ─────────────────────────────────────────────
    print()
    print("    == ⚠ Il registro del server — diagnosi e denominatore, NON arbitro")
    reg, perche = leggi_registro(a.registro)
    if reg is None:
        print(f"    --  {perche}")
        # ⛔ Non e' l'arbitro, ma senza di lui due controlli qui sopra non hanno
        #    il loro denominatore: si dice, invece di far finta di niente.
        print(f"    {GIALLO}??{GRIGIO}  ⚠ senza il registro non posso dire quante "
              f"vite del server ci sono state ne' quanti ban ha caricato: il "
              f"verdetto sulla persistenza vale meno di quel che sembra")
        sospeso = True
    else:
        def med(x):
            return f"{statistics.median(x):.0f} ms" if x else "— (nessuna riga)"
        print(f"    --  vite del server nel registro: {reg['vite']}  "
              f"(attese 2: una per i campioni e il ban, una per la persistenza)")
        for r in reg["avvii"]:
            print(f"        {r}")
        print(f"    --  «il secondo fisso e' passato»: n={len(reg['fissi'])}  "
              f"mediana {med(reg['fissi'])}  "
              f"(ammessi {med(reg['ammessi'])} su {len(reg['ammessi'])} · "
              f"respinti {med(reg['respinti'])} su {len(reg['respinti'])})")
        print(f"    --  se quel numero e' ~{RITARDO_FISSO:.0f} ms a governare e' "
              f"stato il RITARDO FISSO; se e' molto piu' alto a governare e' "
              f"stato PAM, e una separazione fra le mediane sarebbe di PAM")
        print(f"    --  indirizzi di provenienza visti DAL SERVER: {reg['indirizzi']}")
        print(f"    --  righe «BANNATO»: {len(reg['ban'])} · «SBLOCCATO su "
              f"comando»: {len(reg['sbloccati'])} · «NON era bannato»: "
              f"{len(reg['non_bannati'])} · pagine servite: {len(reg['pagine'])}")
        if len(reg["indirizzi"]) < 2:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ il server ha visto UN SOLO indirizzo: "
                  f"il margine del bilancio non c'e' stato, e i controlli che "
                  f"separano i due indirizzi non valgono (B0.3)")
            guasti += 1
        if reg["vite"] < 2:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ il registro vede {reg['vite']} vite "
                  f"del server: la persistenza si prova con un RIAVVIO, e qui "
                  f"non ce n'e' stato uno")
            guasti += 1
        elif reg["carichi"] and reg["carichi"][-1] == 1:
            print(f"    {VERDE}OK{GRIGIO}  ⭐ e la seconda accensione dichiara «ban "
                  f"caricati: 1»: il ban e' tornato dal disco, non dalla memoria")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ la seconda accensione dichiara ban "
                  f"caricati = {reg['carichi'][-1] if reg['carichi'] else 'niente'}, "
                  f"atteso 1")
            guasti += 1
        if reg["illeggibili"]:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ {reg['illeggibili']} accensioni non "
                  f"hanno potuto leggere il file dei ban")
            guasti += 1
        # ⛔ E ogni sblocco si scrive nel registro (§4.4-bis): il banco lo
        #    confronta col numero di sblocchi che ha CHIESTO, o «l'ha scritto»
        #    resta una speranza.
        chiesti = [r for r in sblocchi if r["esito"] is not None]
        scritti = len(reg["sbloccati"]) + len(reg["non_bannati"])
        if scritti >= len(chiesti) and chiesti:
            print(f"    {VERDE}OK{GRIGIO}  ⭐ ogni sblocco e' finito nel registro: "
                  f"{len(chiesti)} chiesti, {scritti} righe scritte "
                  f"({len(reg['sbloccati'])} «tolto» + {len(reg['non_bannati'])} "
                  f"«non era bannato»)")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ sblocchi chiesti {len(chiesti)}, "
                  f"righe nel registro {scritti}: «ogni sblocco si scrive nel "
                  f"registro, o un ban tolto e un ban mai scattato hanno lo "
                  f"stesso aspetto» (§4.4-bis)")
            guasti += 1

    # ── 7-bis. ⛔ I DUE CRONOMETRI, e devono concordare ──────────────────────
    #
    # ⛔ Rilievo A19: la certificazione di questo banco guasta i FATTI GIA'
    #    REGISTRATI, quindi certifica il GIUDICE e non l'ACQUISIZIONE.  Un `t0`
    #    spostato in un punto che tiene i numeri plausibili non lo vedrebbe
    #    nessuno dei guasti costruiti a mano.  ⭐ Questa riga e' il controllo che
    #    l'acquisizione manca: il SERVER cronometra lo stesso fatto per conto
    #    suo, e i due numeri hanno un verso obbligato.
    #
    #    Il client parte PRIMA di spedire `CREDENZIALI` e ferma DOPO aver letto
    #    la risposta; il server parte quando `CREDENZIALI` arriva e ferma quando
    #    decide.  L'intervallo del client CONTIENE quello del server: puo' solo
    #    essere piu' grande.  ⛔ Se e' piu' piccolo, il cronometro del banco non
    #    sta misurando l'intervallo che dichiara — ed e' un difetto DEL BANCO,
    #    non del server, che e' precisamente quel che `REVIEWER.md` §1 mette per
    #    primo.
    if reg is not None and reg["fissi"] and da_pam:
        print()
        print("    == ⛔ I due cronometri sullo stesso fatto (B0.4: si stampa E "
              "si confronta)")
        med_cli = statistics.median([r["ms"] for r in da_pam])
        med_srv = statistics.median(reg["fissi"])
        print(f"    --  client (dal lato che riceve) {med_cli:.0f} ms  ·  server "
              f"(«il secondo fisso e' passato») {med_srv:.0f} ms  ·  differenza "
              f"{med_cli - med_srv:+.0f} ms")
        if med_cli >= med_srv - MARGINE_CRONOMETRI:
            print(f"    {VERDE}OK{GRIGIO}  il cronometro del client contiene "
                  f"quello del server, come deve: quel che il banco misura e' "
                  f"l'intervallo che dichiara di misurare")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ I DUE CRONOMETRI NON CONCORDANO: il "
                  f"client dice {med_cli:.0f} ms dove il server ne dichiara "
                  f"{med_srv:.0f}, e l'intervallo del client CONTIENE quello "
                  f"del server — non puo' essere piu' corto")
            print(f"        ⛔ Il primo sospetto e' sul banco, non sul server "
                  f"(`LEZIONI.md` §1.9 punto 3): `t0` di `un_tentativo()` "
                  f"cronometra meno di quel che la sua docstring dichiara, e "
                  f"tutte le mediane qui sopra sono di un altro intervallo")
            guasti += 1

    # ── 7-ter. ⛔ CHI GOVERNA I TEMPI, misurato ──────────────────────────────
    imputato, righe_imputato = None, []
    if guasti_mediane:
        print()
        print("    == ⛔ Le mediane si separano: CHI le separa — e si misura "
              "(A18)")
        imputato, righe_imputato = imputato_dei_tempi(serie, reg)
        for r in righe_imputato:
            print(f"    --  {r}")
        if imputato == "NOSTRO":
            # ⛔ E allora NON e' il `[?]` gia' dichiarato di §4.4-bis: e' un
            #    difetto nostro, e va nel contatore dei rossi veri.  Tenerlo nel
            #    contatore delle mediane vorrebbe dire concedere a un ritardo
            #    che abbiamo scritto noi l'indulgenza scritta per PAM.
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ la separazione NON e' quella che "
                  f"§4.4-bis ha gia' dichiarato `[?]`: e' un ritardo nostro, e "
                  f"conta come un rosso pieno")
            guasti += 1
        elif imputato is None:
            print(f"    {GIALLO}??{GRIGIO}  ⚠ l'imputato non e' stato misurato: "
                  f"il verdetto dira' CHE le mediane si separano e non DA CHI, "
                  f"che e' meno di prima e piu' vero")

    # ── L'esito ─────────────────────────────────────────────────────────────
    print()
    print(f"    == L'esito, e il suo denominatore: {len(tentativi)} tentativi, "
          f"{len(pagine)} pagine, {len(sblocchi)} sblocchi")
    if guasti:
        print(f"    {ROSSO}⛔ B8: {guasti} "
              f"{'punto non passa' if guasti == 1 else 'punti non passano'}{GRIGIO}")
        if guasti_mediane:
            print(f"    ⚠ e {guasti_mediane} coppie di mediane si separano, e "
                  f"l'imputato e' «{imputato or 'NON MISURATO'}»:")
            for r in righe_imputato:
                print(f"       {r}")
            if imputato != "NOSTRO":
                print(f"    ⚠ guarda le mediane DOPO aver curato i {guasti} "
                      f"punti qui sopra")
        return 1
    if guasti_mediane:
        # ⛔ IL QUINTO ESITO, e nasce da una misura, non da un'indulgenza — e da
        #    stanotte l'imputato lo nomina `imputato_dei_tempi()`, che lo LEGGE
        #    nei numeri, invece di una frase costante (A18).
        print(f"    {ROSSO}⛔ B8: {guasti_mediane} coppie di mediane SI SEPARANO "
              f"— «le tre mediane indistinguibili» di `fasi/01-filo-nudo.md` B8 "
              f"non e' soddisfatta{GRIGIO}")
        print(f"    ⭐ ma la coppia che porta il SEGRETO — «inesistente − "
              f"sbagliata», l'unica che direbbe se un nome utente esiste — NON "
              f"si separa: quel che §4.4 vieta non e' leggibile col cronometro")
        print(f"    ⭐ e il ban passa per intero: scatta al terzo, rifiuta il "
              f"quarto con la parola giusta, sopravvive al riavvio, lo dice "
              f"nella pagina, e lo sblocco lo toglie")
        for r in righe_imputato:
            print(f"    ⚠ {r}")
        if imputato == "PAM":
            print(f"    ⚠ E' il `[?]` che §4.4-bis ha gia' dichiarato il 10 "
                  f"agosto 2026 e che il ban NON chiude: sono due proprieta' "
                  f"diverse.  ⛔ Questo esito NON e' un verde, ed e' tenuto "
                  f"separato dal rosso di sopra per una ragione sola — un "
                  f"banco sempre rosso non fa fallire nessuna regressione, "
                  f"perche' nessuno lo guarda piu'.")
            return 5
        # ⛔ Senza imputato misurato l'indulgenza del quinto esito non si
        #    applica: e' scritta per PAM, e concederla a un ritardo di cui non
        #    si sa la provenienza vorrebbe dire assolvere chiunque.
        print(f"    ⛔ E l'imputato NON e' PAM (o non e' stato misurato): "
              f"l'esito 5 — l'indulgenza del `[?]` gia' dichiarato — NON si "
              f"applica, perche' e' scritta per `pam_faildelay` e non per un "
              f"ritardo qualunque")
        return 1
    if sospeso:
        print(f"    {GIALLO}⚠ B8 SOSPESO: il ban passa, ma quel che ho guardato "
              f"sulle mediane non basta a chiamarle «indistinguibili»{GRIGIO}")
        print(f"    ⚠ «non ho visto una differenza» e «non c'e' una differenza» "
              f"sono due cose diverse: rilancia con piu' blocchi")
        return 3
    print(f"    {VERDE}⭐ B8 passa: ogni risposta di PAM ≥ {RITARDO_FISSO:.0f} ms, "
          f"le tre mediane non si separano oltre il rumore, il ban scatta al "
          f"terzo e rifiuta il quarto con la parola giusta, sopravvive al "
          f"riavvio, lo dice nella pagina, e lo sblocco lo toglie{GRIGIO}")
    print(f"    ⚠ e vale fin dove si e' guardato: le risoluzioni sono stampate "
          f"qui sopra, coppia per coppia")
    return 0


# ===========================================================================
# ⛔⭐ LA CERTIFICAZIONE DEL BANCO — `LEZIONI.md` §1.2 e §1.3
# ===========================================================================
# *«Il banco si certifica prima della misura»*, e *«un banco che NON riproduce
# non e' una prova di correttezza»*.  Qui si costruisce **un guasto per volta,
# a mano**, dentro i fatti che il giro ha appena prodotto, e si pretende che il
# verdetto diventi rosso **in quel punto** — non genericamente rosso.
#
# ⛔ IL CRITERIO E' DUPLICE, E LA SECONDA META' E' QUELLA CHE CONTA: la frase
#    attesa deve comparire nel verdetto **guasto** e **non** in quello sano.
#    Un banco gia' rosso per un'altra ragione soddisferebbe la prima meta' da
#    solo, e la certificazione direbbe «vede tutto» senza aver visto niente —
#    che e' la forma di verde su insieme vuoto di `LEZIONI.md` §1.9 regola 6,
#    trasferita alla certificazione.
def _prima(dati, **cerca):
    for r in dati:
        if all(r.get(k) == v for k, v in cerca.items()):
            return r
    return None


def _guasti_possibili():
    """(nome, funzione che rompe UNA cosa, frase che il verdetto DEVE dire)."""
    def quarto_ammesso(d, reg):
        r = [x for x in d if x.get("tipo") == "ban"]
        r[-1]["messaggio"], r[-1]["motivo"] = "AMMESSO", None
        return d, reg

    def nomi_uguali(d, reg):
        for x in d:
            if x.get("tipo") == "ban":
                x["nome"] = "sempre-lo-stesso"
        return d, reg

    def troppo_veloce(d, reg):
        r = _prima(d, tipo="campione", classe="atteso")
        r["ms"] = 900.0
        return d, reg

    def nomi_a_tempo(d, reg):
        # ⛔ Il guasto che questo banco esiste per trovare: «utente inesistente»
        #    risponde sistematicamente prima di «parola sbagliata», e col
        #    cronometro si legge se un nome utente esiste.  ⚠ Due secondi sono
        #    grossolani apposta: se il banco non vedesse nemmeno QUESTO, non
        #    vedrebbe niente.
        for x in d:
            if x.get("tipo") == "campione" and x.get("caso") == "inesistente" \
                    and x.get("ms"):
                x["ms"] += 2000.0
        return d, reg

    def pagina_bugiarda(d, reg):
        r = _prima(d, tipo="pagina", etichetta="bannato-prima")
        r["bannato"] = False
        return d, reg

    def pagina_muta(d, reg):
        r = _prima(d, tipo="pagina", etichetta="bannato-prima")
        r["frase"] = False
        return d, reg

    def chiusura_storta(d, reg):
        r = [x for x in d if x.get("tipo") == "ban"]
        r[-1]["chiusura"] = CREDENZIALI_ERRATE
        return d, reg

    def altro_fuori(d, reg):
        r = _prima(d, tipo="controllo", etichetta="altro-indirizzo")
        r["messaggio"], r["motivo"] = "RESPINTO", TROPPI_TENTATIVI
        return d, reg

    def niente_azzeramento(d, reg):
        r = [x for x in d if x.get("etichetta") == "azzeramento"]
        r[-1]["motivo"], r[-1]["messaggio"] = TROPPI_TENTATIVI, "RESPINTO"
        return d, reg

    def sblocco_cieco(d, reg):
        r = _prima(d, tipo="sblocco", etichetta="prova-tolto")
        r["esito"] = "NON-BANNATO"
        return d, reg

    def niente_persistenza(d, reg):
        return [x for x in d
                if x.get("etichetta") != "bannato-dopo-riavvio"], reg

    def registro_smemorato(d, reg):
        return d, [r.replace("ban caricati: 1", "ban caricati: 0") for r in reg]

    def imputato_nostro(d, reg):
        # ⛔ Il guasto che certifica la cura di A18: il ritardo si mette sul
        #    percorso dell'AMMESSO — dove `pam_faildelay` non ha voce — e il
        #    registro del server continua a dire che il secondo fisso ha
        #    coperto tutto.  Il verdetto DEVE smettere di accusare PAM.
        for x in d:
            if x.get("tipo") == "campione" and x.get("caso") == "giusta" \
                    and x.get("ms"):
                x["ms"] += 2000.0
        fuori = []
        for r in reg:
            if "il secondo fisso e' passato" in r:
                fuori.append("il secondo fisso e' passato (1005 ms)\n")
            else:
                fuori.append(r)
        return d, fuori

    def cronometro_scollato(d, reg):
        # ⛔ Il guasto che certifica l'ACQUISIZIONE e non il giudice (A19):
        #    `t0` spostato in un punto che tiene i numeri plausibili — qui
        #    modellato dimezzandoli — e nessuno dei tredici guasti di prima se
        #    ne sarebbe accorto.  Il secondo testimone si', perche' il
        #    cronometro del client non puo' essere piu' corto di quello del
        #    server.
        for x in d:
            if x.get("ms"):
                x["ms"] = x["ms"] / 2.0
        return d, [r if "il secondo fisso e' passato" not in r
                   else "il secondo fisso e' passato (2500 ms)\n" for r in reg]

    def nessun_tentativo(d, reg):
        # ⛔ Il file NON e' vuoto: restano le pagine e gli sblocchi, e sparisce
        #    ogni tentativo.  E' la forma piu' insidiosa di verde — «tutti
        #    quelli provati sono andati bene» e' vero anche quando i provati
        #    sono zero (`LEZIONI.md` §1.9 regola 6) — e un file vuoto la
        #    proverebbe piu' debolmente, perche' un file vuoto lo nota chiunque.
        return [x for x in d
                if x.get("tipo") not in ("campione", "ban", "controllo")], reg

    return [
        ("il quarto tentativo, con la parola GIUSTA, e' AMMESSO",
         quarto_ammesso, "il quarto tentativo — parola GIUSTA —"),
        ("i tre nomi del giro del ban sono UGUALI",
         nomi_uguali, "i tre nomi non sono diversi"),
        ("una risposta di PAM arriva a 900 ms",
         troppo_veloce, "risposte sotto il secondo"),
        ("⛔ «utente inesistente» risponde 2 s prima di «parola sbagliata»",
         nomi_a_tempo, "LA SEPARAZIONE CHE §4.4 VIETA"),
        ("la pagina di un indirizzo bannato dice «non sei bannato»",
         pagina_bugiarda, "bannato=False (atteso True)"),
        ("la pagina bannata non contiene «tentativi esauriti»",
         pagina_muta, "atteso True) · frase=False"),
        ("la sessione si chiude con un codice diverso da TROPPI_TENTATIVI",
         chiusura_storta, "il codice di chiusura della sessione"),
        ("l'altro indirizzo NON entra",
         altro_fuori, "l'altro indirizzo NON entra"),
        ("il successo non azzera il conto",
         niente_azzeramento, "l'azzeramento non c'e' stato"),
        ("lo sblocco risponde «non era bannato» su un ban vero",
         sblocco_cieco, "NON-BANNATO (atteso TOLTO)"),
        ("la persistenza non e' stata provata (manca la pagina dopo il riavvio)",
         niente_persistenza, "la persistenza non e' stata provata"),
        ("la seconda accensione dichiara «ban caricati: 0»",
         registro_smemorato, "la seconda accensione dichiara ban caricati"),
        ("⛔ ZERO tentativi: «tutti quelli provati sono andati bene» su zero provati",
         nessun_tentativo, "ZERO tentativi"),
        ("⛔ il ritardo e' NOSTRO, sul percorso dell'AMMESSO, e PAM risponde in "
         "5 ms (A18: il verdetto deve smettere di accusare PAM)",
         imputato_nostro, "L'IMPUTATO NON E' PAM"),
        ("⛔ il cronometro del CLIENT misura meno di quello del SERVER "
         "(A19: `t0` spostato in un punto che tiene i numeri plausibili)",
         cronometro_scollato, "I DUE CRONOMETRI NON CONCORDANO"),
    ]


def certifica(a):
    import copy as _copy
    import io
    import contextlib

    if not os.path.exists(a.uscita):
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ non c'e' nessun giro da guastare: "
              f"{a.uscita} non esiste.  La certificazione si fa **sui fatti di "
              f"un giro vero**, o guasta un file che nessuno ha prodotto")
        return 2
    with open(a.uscita) as f:
        sani = [json.loads(r) for r in f if r.strip()]
    reg_sano = []
    if a.registro and os.path.exists(a.registro):
        with open(a.registro, errors="replace") as f:
            reg_sano = f.readlines()

    tmp_u = a.uscita + ".guasto"
    tmp_r = (a.registro or "/tmp/b8-reg") + ".guasto"

    def gira(dati, reg):
        with open(tmp_u, "w") as f:
            for r in dati:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(tmp_r, "w") as f:
            f.writelines(reg)
        b = argparse.Namespace(**vars(a))
        b.uscita, b.registro = tmp_u, tmp_r
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            esito = verdetto(b)
        return esito, buf.getvalue()

    print()
    print("    == ⛔ LA CERTIFICAZIONE: si costruisce il guasto e si pretende il rosso")
    # ⛔ E SI DICHIARA CHE COSA QUESTA CERTIFICAZIONE **NON** CERTIFICA — A19.
    #    Chi legge un verdetto legge il verdetto, non i commenti del file: senza
    #    queste tre righe, «certificato» si legge come «B8 e' certificato», e
    #    quel che e' certificato e' meta' di B8.
    print("    --  ⛔ QUEL CHE QUESTA RIGA CERTIFICA: il GIUDICE.  I guasti si "
          "costruiscono sui FATTI GIA' REGISTRATI, quindi provano che "
          "`verdetto()` sa vedere un fatto storto, non che i fatti siano stati "
          "presi bene")
    print("    --  ⛔ QUEL CHE NON CERTIFICA: l'ACQUISIZIONE.  Un `t0` spostato "
          "in un punto che tiene i numeri plausibili, un `RITARDO_CREDENZIALI` "
          "tolto dal server, un innesto che non c'e': nessuno di questi vive "
          "nei fatti registrati.  ⚠ Il solo guasto che ci arriva e' "
          "«cronometro scollato», e ci arriva per il SECONDO TESTIMONE (il "
          "registro del server), non per i fatti")
    print("    --  ⛔ E il guasto che coprirebbe il resto — togliere "
          "`RITARDO_CREDENZIALI` dal server — sta nel catalogo di "
          "`01-b12-guasti.py` ed e' **catalogato e non eseguito**: e' un buco "
          "di due file di due mani diverse, e va detto qui perche' e' qui che "
          "si legge la parola «certificato»")
    esito_sano, testo_sano = gira(sani, reg_sano)
    print(f"    --  il giro SANO, cosi' com'e': esito {esito_sano} "
          f"({'verde' if esito_sano == 0 else 'sospeso' if esito_sano == 3 else 'rosso'})")
    print(f"    --  fatti su cui si guasta: {len(sani)} · righe di registro: "
          f"{len(reg_sano)}")

    prove = _guasti_possibili()
    print(f"    --  guasti costruiti a mano: {len(prove)}  ⛔ e questo e' il "
          f"denominatore: un elenco di OK senza di lui non e' una misura")
    falliti = 0
    for nome, rompi, frase in prove:
        dati, reg = rompi(_copy.deepcopy(sani), list(reg_sano))
        esito, testo = gira(dati, reg)
        vede = frase in testo
        # ⛔ e la seconda meta' del criterio: il verdetto sano NON deve gia'
        #    dirla, o questa riga non prova che il guasto sia stato visto.
        gia = frase in testo_sano
        # ⛔ E l'esito deve essere un ROSSO VERO (1) o «niente da giudicare» (2),
        #    non il 5 delle mediane: se bastasse «diverso da zero», un giro in
        #    cui PAM domina soddisferebbe questa riga **senza che il guasto sia
        #    stato visto**, e la certificazione direbbe «vedo tutto» guardando
        #    un esito che c'era gia'.
        buono = vede and esito in (1, 2) and not gia
        segno = f"{VERDE}OK{GRIGIO}" if buono else f"{ROSSO}NO{GRIGIO}"
        perche = ""
        if gia:
            perche = "  ⛔ ma il giro SANO lo diceva gia': non prova niente"
        elif not vede:
            perche = f"  ⛔ il verdetto NON ha detto «{frase}» (esito {esito})"
        elif esito not in (1, 2):
            perche = f"  ⛔ lo dice, ma l'esito e' {esito} e non un rosso vero"
        print(f"    {segno}  {nome}{perche}")
        if not buono:
            falliti += 1

    for p in (tmp_u, tmp_r):
        try:
            os.remove(p)
        except OSError:
            pass

    print()
    if falliti:
        print(f"    {ROSSO}⛔ LA CERTIFICAZIONE NON PASSA: {falliti} guasti su "
              f"{len(prove)} non fanno diventare rosso il banco.{GRIGIO}")
        print(f"    ⚠ Finche' questa riga e' rossa, un verde di B8 non vuol dire "
              f"niente: un banco che non riproduce non e' una prova di "
              f"correttezza (`LEZIONI.md` §1.3)")
        return 1
    print(f"    {VERDE}⭐ IL GIUDICE di B8 e' certificato: tutti e {len(prove)} i "
          f"guasti costruiti a mano lo fanno diventare rosso, ciascuno nel suo "
          f"punto{GRIGIO}")
    print(f"    ⚠ e NON e' «B8 e' certificato»: l'acquisizione dei tempi resta "
          f"coperta da un guasto solo (i due cronometri).  Le tre righe in "
          f"cima dicono che cosa e' rimasto fuori")
    return 0


def previsione(a):
    print("== B8 — che cosa si misura, e che cosa mi aspetto PRIMA di misurare")
    print()
    print("  PARTE 1 — il secondo fisso e le tre mediane")
    print("    inesistente  un utente che NON esiste (verificato con getpwnam)")
    print("    sbagliata    l'utente vero, parola d'ordine sbagliata")
    print("    giusta       l'utente vero, parola giusta  → AMMESSO")
    print("    ⚠ la coppia «inesistente − sbagliata» e' quella che, se si separa,")
    print("      regala i nomi degli utenti a chi cronometra.")
    print()
    print("  PARTE 2 — il ban (RCP.md §4.4-bis, DECISIONI.md §1.9)")
    print(f"    {SOGLIA} autenticazioni fallite dallo stesso indirizzo dentro")
    print(f"    {FINESTRA_MIN} minuti ⇒ quell'indirizzo e' fuori per {BAN_ORE} ore.")
    print()
    print("  L'atteso, scritto qui prima dei numeri:")
    print(f"    1. ogni risposta di PAM a CREDENZIALI ≥ {RITARDO_FISSO:.0f} ms;")
    print("    2. le tre mediane indistinguibili secondo la regola dell'intervallo;")
    print("    3. le prime tre fallite — CON TRE NOMI DIVERSI — ricevono")
    print("       CREDENZIALI_ERRATE, e la terza fa scattare il ban;")
    print("    4. ⛔ il QUARTO tentativo ha la parola GIUSTA e riceve")
    print("       TROPPI_TENTATIVI, dentro un RESPINTO e non dentro un CONGEDO,")
    print("       e la sessione si chiude con lo stesso codice;")
    print("    5. un ALTRO indirizzo entra subito;")
    print("    6. 2 falliti · 1 riuscito · 2 falliti NON bannano;")
    print("    7. il ban sopravvive al riavvio del server (invariante I7);")
    print("    8. la pagina si carica LO STESSO, con HTTP 200, dice «tentativi")
    print(f"       esauriti» e quante ore mancano (~{BAN_ORE});")
    print("    9. il comando di sblocco lo toglie, lo scrive nel registro, e la")
    print("       seconda volta risponde «non era bannato».")
    print()
    print("  `[?]` E la previsione che puo' rendere SOSPESO il punto 2, scritta")
    print("  adesso perche' domani sembri una previsione e non una scusa:")
    print("    `banchi/rcp/autenticazione.c` usa il servizio PAM «login», e su")
    print("    Debian `/etc/pam.d/login` porta `pam_faildelay.so delay=3000000`.")
    print("    Se quel modulo e' nella pila, la strada del FALLIMENTO aspetta")
    print("    ~3 s (±25 % per la randomizzazione di libpam) e quella del")
    print("    SUCCESSO no: le mediane si separerebbero di secondi, e la")
    print("    separazione NON sarebbe del ritardo fisso — sarebbe di quel che")
    print("    PAM aggiunge sopra.  ⭐ A distinguere i due imputati e' la riga")
    print("    «il secondo fisso e' passato (N ms)» del registro del server.")
    print("    `[M]` 10 agosto 2026: mediana 2636 ms sui respinti.")
    print()
    print(f"  I numeri della regola: soglia {SOGLIA} fallimenti per indirizzo,")
    print(f"  bilancio {BILANCIO} per blocco, risoluzione voluta "
          f"±{RISOLUZIONE_VOLUTA:.0f} ms, minimo {MINIMO_CAMPIONI} campioni per")
    print(f"  caso, bootstrap {RIPETIZIONI} ripetizioni, seme {SEME}.")
    return 0


# ===========================================================================
# Le fasi
# ===========================================================================
async def fase_campioni(a):
    inesistente = f"nessuno-b8-{a.blocco}"
    if not await controlla_utenti(a, inesistente):
        return 2
    if not await prova_indirizzi(a.indirizzi, a.porta):
        return 2
    passi = piano_campioni(a.blocco, a.per_caso, a.indirizzi, a.utente, inesistente)
    return await esegui(a, passi, "campione", f"blocco {a.blocco}", "sotto-soglia")


async def fase_ban_prima(a):
    """⛔ Il giro del ban, e NESSUNO SBLOCCA QUI DENTRO (B0.3).

    L'ordine e' scelto e non e' indifferente:

      1. il controllo dell'azzeramento sul SECONDO indirizzo (che finisce a due
         fallimenti, e la pagina lo conferma non bannato);
      2. il ban sul PRIMO indirizzo, con tre nomi diversi, e il quarto con la
         parola giusta;
      3. il controllo «un altro indirizzo entra» — ⛔ **subito dopo** il rifiuto,
         che e' l'unico posto in cui risponde alla domanda «il server e' ancora
         vivo?»;
      4. le due pagine.
    """
    inesistente = "nessuno-b8-ban"
    if not await controlla_utenti(a, inesistente, *[n for n in NOMI_DEL_BAN
                                                    if n != "<utente>"]):
        return 2

    print()
    print("    == ⭐ Controllo che dice NO n.2: 2 falliti · 1 riuscito · 2 falliti")
    passi = piano_azzeramento(a.indirizzi, a.utente, inesistente)
    e = await esegui(a, passi, "controllo", "azzeramento", "non-banna")
    if e:
        return e
    guarda_pagina(a, a.indirizzi[1], "azzeramento-dopo", False)

    print()
    print("    == ⛔ Il giro del ban — tre nomi diversi, poi la parola GIUSTA")
    nomi = tuple(a.utente if n == "<utente>" else n for n in NOMI_DEL_BAN)
    passi = piano_ban(a.indirizzi, a.utente, nomi)
    e = await esegui(a, passi, "ban", "ban", "banna-al-4")
    if e:
        return e

    print()
    print("    == ⭐ Controllo che dice NO n.1: un ALTRO indirizzo entra subito")
    passi = [{"caso": "giusta", "indirizzo": a.indirizzi[1], "nome": a.utente,
              "scaldata": False}]
    e = await esegui(a, passi, "controllo", "altro-indirizzo", "sotto-soglia")
    if e:
        return e

    print()
    print("    == ⛔ Quel che l'utente vede, adesso")
    guarda_pagina(a, a.indirizzi[0], "bannato-prima", True)
    guarda_pagina(a, a.indirizzi[1], "non-bannato-prima", False)
    return 0


async def fase_ban_dopo(a):
    """⭐ Dopo il riavvio: la persistenza, e poi lo sblocco — che si prova in fondo."""
    print()
    print("    == ⭐ Controllo che dice NO n.3: il ban sopravvive al RIAVVIO")
    guarda_pagina(a, a.indirizzi[0], "bannato-dopo-riavvio", True)
    guarda_pagina(a, a.indirizzi[1], "non-bannato-dopo-riavvio", False)
    passi = [{"caso": "giusta", "indirizzo": a.indirizzi[0], "nome": a.utente,
              "scaldata": False}]
    # ⚠ Il modello direbbe AMMESSO — non sa che il ban e' tornato dal disco — e
    #   pretenderlo qui darebbe rosso sul codice giusto.  Il confronto lo fa il
    #   verdetto, che sa che siamo dopo un riavvio.
    e = await esegui(a, passi, "controllo", "dopo-riavvio", "sotto-soglia",
                     confronta_modello=False)
    if e:
        return e

    print()
    print("    == ⛔ E ADESSO lo sblocco, che fin qui non ha toccato niente")
    sblocca_e_dichiara(a, [a.indirizzi[0]], "prova-tolto", pretendi="TOLTO")
    guarda_pagina(a, a.indirizzi[0], "dopo-sblocco", False)
    sblocca_e_dichiara(a, [a.indirizzi[0]], "prova-non-bannato",
                       pretendi="NON-BANNATO")
    passi = [{"caso": "giusta", "indirizzo": a.indirizzi[0], "nome": a.utente,
              "scaldata": False}]
    return await esegui(a, passi, "controllo", "dopo-sblocco", "sotto-soglia")


async def controlla_utenti(a, *inesistenti):
    """⛔ Lo stato iniziale si dichiara e si VERIFICA (B0.1)."""
    ok = True
    for nome, deve, che in [(a.utente, True, "l'utente vero")] + \
            [(n, False, "un nome inesistente") for n in inesistenti]:
        buono, c_e = esistenza(nome, deve)
        stato = "esiste" if c_e else "non esiste"
        if buono:
            print(f"    {VERDE}OK{GRIGIO}  {che} «{nome}»: {stato}, come deve")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ {che} «{nome}»: {stato} — il "
                  f"contrario di quel che questo banco presuppone")
            ok = False
    return ok


def principale():
    p = argparse.ArgumentParser(
        description="B8 — il secondo fisso, le tre mediane e il ban dell'indirizzo")
    # ⛔ Nessun predefinito che nomini un bersaglio: 7447 e' l'innesto e 7448 il
    #    prodotto, e un predefinito qui vorrebbe dire che «--bersaglio prodotto»
    #    senza «--porta» misura l'innesto dichiarando il prodotto.
    p.add_argument("--porta", type=int, required=True)
    p.add_argument("--indirizzi", default="127.0.0.1,192.168.0.2",
                   help="⛔ due: raddoppiano il margine del bilancio e si "
                        "vedono nel registro del server")
    p.add_argument("--utente", default="prova")
    # ⛔ `parola-di-prova`, e la storia di questa riga vale il commento.
    #
    #    Fino all'11 agosto 2026 qui c'era scritto `prova`, e ⛔ **nessuna
    #    autenticazione di questo banco e' mai riuscita**: `01-b3-lancia.sh`,
    #    `01-b6-lancia.sh` e `01-b7-lancia.sh` usano tutti e tre
    #    `PAROLA=parola-di-prova`.  Il caso «giusta» riceveva
    #    `CREDENZIALI_ERRATE` come gli altri due, cioe' ⛔ **i tre casi erano
    #    due**, e la terza mediana era una copia della seconda.
    #
    # ⚠ E il difetto non aveva un sintomo proprio: il banco diceva «risposte
    #   inattese», che si legge come un guasto del server.  ⭐ Da oggi c'e' il
    #   controllo positivo in `--stato-iniziale` — *«questo strumento sa
    #   produrre un AMMESSO?»* — che e' `LEZIONI.md` §1.9 regola 2 applicata al
    #   banco invece che alla misura, e costa un tentativo.
    p.add_argument("--parola", default="parola-di-prova")
    p.add_argument("--sbagliata", default="questa-non-e-la-parola-di-nessuno")
    p.add_argument("--comando", default="/srv/src/b8-comando.sock",
                   help="il socket del comando di sblocco di §4.4-bis")
    p.add_argument("--blocco", type=int, default=0)
    p.add_argument("--per-caso", type=int, default=2,
                   help="terzine per blocco.  ⛔ 2 tiene i fallimenti a due per "
                        "indirizzo, cioe' UNO sotto la soglia")
    p.add_argument("--campioni", action="store_true")
    p.add_argument("--ban", choices=("prima", "dopo"))
    p.add_argument("--sblocca", default="",
                   help="sblocca questi indirizzi (separati da virgola) e lo dichiara")
    p.add_argument("--perche", default="fra-i-blocchi")
    p.add_argument("--stato-iniziale", action="store_true")
    p.add_argument("--verdetto", action="store_true")
    p.add_argument("--certifica", action="store_true",
                   help="⛔ costruisce un guasto per volta nei fatti di un giro "
                        "vero e pretende che il banco diventi rosso in QUEL punto")
    p.add_argument("--previsione", action="store_true")
    # ⛔ `--giro` idem: lo dichiara il profilo comune (vedi la nota qui sotto).
    # ⛔ `--uscita` NON si dichiara qui: lo dichiara il profilo comune del
    #    bersaglio, `01-b0-bersaglio.py`, poche righe piu' sotto.  Dichiararlo
    #    in tutt'e due i posti fa morire il banco all'avvio con
    #    «conflicting option string: --uscita» — misurato l'11 agosto 2026, e
    #    il giro si fermava PRIMA di accendere qualunque cosa.
    # ⚠ E' la cucitura fra due autori dello stesso giorno: chi ha scritto il
    #   profilo non sapeva che B8 avesse gia' quell'argomento, e chi ha scritto
    #   B8 non sapeva che sarebbe arrivato un profilo.  Il predefinito di
    #   allora — `b8-fatti.jsonl`, senza il bersaglio nel nome — e' proprio
    #   quello che il profilo esiste per togliere: due bersagli nello stesso
    #   file sono due misure che non si possono mettere in fila.
    p.add_argument("--registro", default="")
    # ⛔ Gli stessi quattro argomenti di B5, B6 e B7 — bersaglio obbligatorio e
    #    senza predefinito, uscita, giro, md5 del binario.
    b0.aggiungi_argomenti(p)
    a = p.parse_args()
    a.indirizzi = [x for x in a.indirizzi.split(",") if x]
    a.prof = b0.profilo(a.bersaglio)
    # ⛔ E da qui in poi OGNI riga del registro porta il bersaglio, la porta e
    #    l'impronta md5 del binario misurato.
    BERSAGLIO.update({"bersaglio": a.bersaglio, "porta": a.porta,
                      "md5": a.md5 or "ignota"})
    R_BAN.update({"caricati": a.prof["r_ban_caricati"],
                  "illeggibile": a.prof["r_ban_illeggibile"],
                  "pagina": a.prof["r_pagina"]})

    if a.previsione:
        return previsione(a)
    if a.certifica:
        return certifica(a)
    if a.verdetto:
        return verdetto(a)
    if len(a.indirizzi) < 2:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ servono DUE indirizzi di provenienza")
        return 2

    # ⛔ E LA RIGA D'APERTURA DEL GIRO — che dice contro che cosa si misura, e
    #    che cosa questo bersaglio fa di diverso.
    scrivi(a.uscita, {"giro": a.giro, "tipo": "giro", "banco": "B8",
                      "eseguibile": a.prof["eseguibile"],
                      "indirizzi": a.indirizzi,
                      # ⛔ La differenza che cambia il SIGNIFICATO di un rosso:
                      #    se il file dei ban c'e' e non si legge, il prodotto
                      #    RIFIUTA di partire (src/main.c: «non e' "zero ban",
                      #    e' la protezione di §4.4-bis spenta.  Non si
                      #    parte.»), mentre l'innesto parte e lo scrive.  ⚠ Su
                      #    questo bersaglio quel caso non si osserva come una
                      #    riga di registro: si osserva come «il server non si
                      #    e' acceso».
                      "ban_illeggibile_parte": a.prof["ban_illeggibile_parte"],
                      "righe_cercate": dict(R_BAN)})

    if a.stato_iniziale:
        # ⛔ B0.1: si dichiara E si verifica da che stato si parte.  Qui lo stato
        #    che conta e' triplo: il comando di sblocco esiste, i due indirizzi
        #    non sono bannati, e la pagina sa dire di no.
        vivo, che = cmd.ping(a.comando)
        if not vivo:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ il comando di sblocco non risponde: "
                  f"{che}")
            print(f"        senza, questo banco non puo' ne' partire da uno stato "
                  f"noto ne' rimettere la macchina a posto — e ogni banco "
                  f"successivo resterebbe fuori per {BAN_ORE} ore (B0.3)")
            return 2
        print(f"    {VERDE}OK{GRIGIO}  il comando di sblocco risponde ({che})")
        sblocca_e_dichiara(a, a.indirizzi, "stato-iniziale")
        tutte = True
        for ind in a.indirizzi:
            r = guarda_pagina(a, ind, "stato-iniziale", False)
            if r["errore"] or r["bannato"] is not False:
                tutte = False
        if not tutte:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ lo stato iniziale non e' quello "
                  f"dichiarato: qualcuno e' gia' bannato, o la pagina non "
                  f"risponde")
            return 2
        print(f"    {VERDE}OK{GRIGIO}  ⭐ e la pagina SA DIRE DI NO: senza questa "
              f"riga, «tentativi esauriti» piu' tardi sarebbe compatibile con "
              f"una pagina che lo dice sempre")

        # ⛔ IL CONTROLLO POSITIVO SULLO STRUMENTO — `LEZIONI.md` §1.9 regola 2:
        #    *«ogni misura vuole un controllo positivo, sullo stesso strumento —
        #    questo strumento sa trovare qualcosa che c'e' di sicuro?»*
        #
        #    Qui la domanda e': **questo banco sa produrre un AMMESSO?**  Se non
        #    lo sa — parola d'ordine sbagliata, utente senza password, PAM che
        #    non gli parla — il caso «giusta» riceve `CREDENZIALI_ERRATE` come
        #    gli altri due, ⛔ **i tre casi diventano due**, e la coppia
        #    «sbagliata − giusta» sarebbe indistinguibile **per costruzione**:
        #    il verde piu' vuoto che questo banco possa stampare.
        #
        # ⚠ E costa un tentativo che non consuma niente: un'autenticazione
        #   RIUSCITA azzera il conto di quell'indirizzo (§4.4-bis), quindi
        #   lascia la macchina piu' pulita di come l'ha trovata.
        r = asyncio.run(un_tentativo(a.indirizzi[0], a.porta, a.utente, a.parola))
        rec = dict(r)
        rec.update({"giro": a.giro, "tipo": "controllo",
                    "etichetta": "so-fare-un-ammesso", "blocco": 0, "ordine": 1,
                    "caso": "giusta", "scaldata": True,
                    "classe": classifica(r, "giusta"),
                    "atteso_modello": "AMMESSO", "atteso_motivo": None})
        scrivi(a.uscita, rec)
        if rec["messaggio"] != "AMMESSO":
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ il controllo positivo NON passa: con "
                  f"l'utente «{a.utente}» e la parola che questo banco crede "
                  f"giusta il server risponde "
                  f"{rec['messaggio'] or rec['errore']} "
                  f"{MOTIVI.get(rec['motivo'], '')}")
            print(f"        ⛔ senza un AMMESSO i tre casi sono DUE, e «le tre "
                  f"mediane non si separano» sarebbe vero per costruzione.  "
                  f"Guarda la parola d'ordine (gli altri banchi usano "
                  f"«parola-di-prova»), non il server")
            return 2
        print(f"    {VERDE}OK{GRIGIO}  ⭐ e questo banco SA produrre un AMMESSO "
              f"({rec['ms']:.0f} ms): i tre casi sono davvero tre")
        return 0

    if a.sblocca:
        sblocca_e_dichiara(a, [x for x in a.sblocca.split(",") if x], a.perche)
        return 0

    if a.campioni:
        return asyncio.run(fase_campioni(a))
    if a.ban == "prima":
        return asyncio.run(fase_ban_prima(a))
    if a.ban == "dopo":
        return asyncio.run(fase_ban_dopo(a))
    print(f"    {ROSSO}NO{GRIGIO}  ⛔ non mi hai detto che cosa fare")
    return 2


if __name__ == "__main__":
    sys.exit(principale())
