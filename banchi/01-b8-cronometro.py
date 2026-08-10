#!/usr/bin/env python3
"""01-b8-cronometro.py — ⛔ B8: il secondo fisso, e le tre mediane indistinguibili.

    python3 01-b8-cronometro.py --previsione
    python3 01-b8-cronometro.py --blocco 3 --giro 1723...   (un blocco di campioni)
    python3 01-b8-cronometro.py --controllo con-successo --giro ...
    python3 01-b8-cronometro.py --verdetto --giro ...       (legge, conta, giudica)

⚠ Gira DENTRO il contenitore: `aioquic` sta li'.  Lo conduce `01-b8-lancia.sh`,
  che **accende e spegne il server fra un blocco e l'altro** — ed e' quello, non
  una riga di questo file, che azzera i due contatori di §4.4-bis.

===========================================================================
⛔ CHE COSA MISURA, E PERCHE' NESSUN ALTRO BANCO LO VEDE

`RCP.md` §4.4 vieta al server di **distinguere nel motivo** fra «utente
inesistente» e «parola d'ordine sbagliata»: entrambi sono `CREDENZIALI_ERRATE`.
⭐ Ma un divieto sul *motivo* non serve a niente se la stessa distinzione si
legge **col cronometro**: chi attacca imparerebbe i nomi degli utenti a tempo,
senza indovinare niente.  Per questo §4.4-bis impone il **ritardo fisso di un
secondo**, «anche quando la risposta e' `AMMESSO`» e «anche quando e'
`TROPPI_TENTATIVI`».

⛔ **«Indistinguibili» e' una parola che va misurata, non dichiarata** — e il
   criterio NON e' «≥ 1 s»:

       pam_authenticate(); sleep(1); rispondi();

   da **1,001 · 1,050 · 1,300 s** nei tre casi.  Tre righe verdi, e la
   distinzione che §4.4 vieta di scrivere nel motivo si legge col cronometro
   esattamente come prima (rilievo R3.2).  Il criterio giusto e' **di forma
   diversa, non di soglia diversa**: le mediane dei tre casi devono differire
   **meno del rumore della misura**.

===========================================================================
⛔ LE QUATTRO TRAPPOLE, E COME QUESTO BANCO LE EVITA

1. ⛔ **IL NUMERO DEI CAMPIONI E' UN DENOMINATORE, E SI STAMPA.**
   Con tre campioni per caso non si distingue niente, e un banco direbbe
   «indistinguibili» **perche' non ha guardato abbastanza**.  Qui il numero di
   campioni **entra nella regola** (vedi sotto): guardare meno **allarga**
   l'intervallo e porta al verdetto *sospeso*, non al verde.  ⭐ E' l'unica
   forma di regola che non si puo' soddisfare misurando di meno.

2. ⚠ **I CONTATORI DI §4.4-bis SONO LA TRAPPOLA PEGGIORE** (B0.3).
   Dopo cinque fallimenti il server risponde `TROPPI_TENTATIVI` **subito e senza
   interrogare PAM**: e' una **strada diversa**, con un tempo diverso.  Un banco
   che non se ne accorgesse **misurerebbe il limitatore credendo di misurare
   PAM**, e per giunta lo farebbe solo su alcuni campioni — cioe' mescolerebbe
   due popolazioni sotto la stessa etichetta (E2).

   ⭐ Qui il limitatore si evita **su tre livelli, e nessuno dei tre si fida
      degli altri**:

     a. **il bilancio**: ogni vita del server porta al massimo **4 fallimenti
        per indirizzo** e **4 per nome** — uno sotto la soglia di 5.  I
        fallimenti si distribuiscono su **due indirizzi di provenienza**
        (§4.4-bis conta per indirizzo, e `solo_indirizzo()` butta la porta) e
        il nome inesistente **cambia a ogni blocco**;
     b. **il piano si verifica PRIMA di eseguirlo**: `simula()` e' un modello
        della regola di §4.4-bis — soglia, chiave per nome, chiave per
        indirizzo, azzeramento del nome sul successo — che dice **tentativo per
        tentativo** che cosa dovrebbe arrivare, e `verifica_piano()` **non fa
        partire il blocco** se il modello vede anche un solo tentativo bloccato.
        Un commento che dice «stiamo sotto soglia» non e' una verifica: questo
        lo e';
     c. ⛔ **e sul filo si guarda ogni singola risposta**: un campione che torna
        `RESPINTO(TROPPI_TENTATIVI)` **non entra nelle mediane**, viene contato a
        parte e **toglie il verde**.  E' il controllo che non dipende da nessuna
        nostra aritmetica: se il bilancio fosse sbagliato, si vede.

   ⚠ E **non** si azzerano i contatori a meta' misura: `rcp_azzera_registro_sessioni()`
     esiste in `banchi/rcp/rcp.c` ma **non la chiama nessuno** — non c'e' un
     messaggio, un segnale o un'opzione che ci arrivi.  L'unico modo che il
     banco ha di ripartire da contatori azzerati e' **un processo nuovo**:
     `01-b8-lancia.sh` spegne e riaccende il server a ogni blocco, e cosi' lo
     stato iniziale e' **dichiarato e verificato** (B0.1) invece che sperato.

3. ⚠ **IL PRIMO CAMPIONE NON E' COME GLI ALTRI** — forma **E9**.
   La prima connessione di ogni vita del server paga la cache fredda, i moduli
   di PAM che si aprono, le arene di malloc che crescono.  ⛔ Qui **non si lascia
   al caso**: in ogni blocco i **primi tre tentativi** sono una **scaldata** —
   uno per caso, quindi la strada del successo *e* quella del fallimento — e
   sono **scartati per regola scritta prima, mai a posteriori**.
   ⭐ E si stampano lo stesso, con i loro tempi: scartare in silenzio e' il modo
      piu' comodo di nascondere un numero scomodo.

4. ⭐ **IL CONTROLLO POSITIVO E' NEL MANDATO**: quattro falliti, un **successo**,
   altri quattro — l'ottavo **non** dev'essere bloccato, perche' §4.4-bis dice
   che un'autenticazione riuscita azzera il contatore **di quel nome**.
   ⛔ E da solo non basterebbe: «otto rossi puliti» e' compatibile anche con un
      server che **non blocca mai**.  Per questo il controllo ha **due gambe
      identiche in tutto tranne una cosa** — la gamba `senza-successo` mette un
      nono fallimento al posto del successo — e li' il **sesto** fallimento
      DEVE ricevere `TROPPI_TENTATIVI`.  Una gamba verde e l'altra rossa: e' la
      differenza fra «il successo azzera» e «lo strumento non sa vedere un
      blocco» (rilievo R3.9).

===========================================================================
⛔ COME I DUE CONTATORI SI TENGONO SEPARATI NEL CONTROLLO — e perche' senza
   questo il controllo darebbe ROSSO SUL CODICE GIUSTO

`banchi/rcp/rcp.c` chiama `azzera_tentativi(s->utente)` — **il solo contatore
per nome**.  Quello per indirizzo non lo azzera nessun successo: §4.4-bis dice
che «scade da se' dopo 30 minuti di quiete», e la nota in fondo alla sezione
dice che il contatore per nome «e' quello che si azzera con un successo».

⛔ Conseguenza: **otto fallimenti dallo stesso indirizzo si bloccano al quinto**,
   comunque vada il contatore per nome.  Un controllo «4 · successo · 4»
   condotto da **un solo indirizzo** riceverebbe `TROPPI_TENTATIVI` all'ottavo
   **anche su un server che azzera perfettamente**, e il rosso finirebbe
   sull'imputato sbagliato.

⭐ La cura e' quella che B0.3 prescrive: **si cambia indirizzo di provenienza**.
   I primi cinque passi arrivano da un indirizzo e gli ultimi quattro
   dall'altro: nella gamba che DEVE bloccare, quando il sesto tentativo viene
   respinto per troppi tentativi il suo indirizzo ha **un solo** fallimento
   addosso, e l'unico contatore che puo' averlo fermato e' quello **per nome** —
   che e' esattamente la cosa che il controllo vuole interrogare.

⚠ E i due indirizzi non costano niente: il server si accende su `0.0.0.0`, e la
  stessa macchina lo raggiunge come `127.0.0.1` e come `192.168.0.2`.  Sono due
  chiavi diverse per `solo_indirizzo()`, ⭐ e non si crede sulla parola: il
  registro del server scrive `da=<indirizzo>:<porta>` a ogni rifiuto, e il
  verdetto **conta quanti indirizzi distinti ha visto il server**.  (E' il
  corollario di `LEZIONI.md` §1.9 che la sonda SNI ha pagato: *un denominatore
  si legge dove la cosa succede*.)

===========================================================================
⛔ LA REGOLA CON CUI SI DECIDE CHE DUE MEDIANE SONO «INDISTINGUIBILI»

Per ogni coppia di casi si calcola la **differenza delle mediane** e il suo
**intervallo di confidenza al 95 % per ricampionamento** (bootstrap, 2000
ripetizioni, seme fisso perche' due giri sugli stessi dati diano lo stesso
verdetto — C3).  Poi:

  | l'intervallo | il verdetto |
  |---|---|
  | **non** contiene lo zero | ⛔ **SI DISTINGUONO**: la separazione e' piu' grande del rumore |
  | contiene lo zero, e la sua semiampiezza ≤ RISOLUZIONE_VOLUTA | ⭐ **indistinguibili**, *e si dice fin dove si e' guardato* |
  | contiene lo zero, ma la semiampiezza e' piu' grande | ⚠ **SOSPESO**: non ho guardato abbastanza |

⭐ **Perche' questa regola e non un'altra.**
  · una **soglia fissa in millisecondi** («le mediane distano meno di 50 ms»)
    e' soddisfatta *meglio* da chi misura *meno*: con tre campioni le mediane
    ballano e capitano vicine.  Qui invece pochi campioni **allargano**
    l'intervallo, e l'esito diventa *sospeso*.  La regola **contiene il
    denominatore**;
  · si usano **mediane e ricampionamento** e non media e deviazione standard
    perche' un solo campione sfortunato — una pausa dello schedulatore, il
    disco che si sveglia — sposta la media e non la mediana.  Il documento
    della fase chiede *mediane*: la misura di dispersione dev'essere della
    stessa famiglia;
  · e l'esito **non e' binario**: «indistinguibili» e «non ho guardato
    abbastanza» sono due fatti diversi con due cure diverse, e confonderli e'
    la forma **E8** applicata a un verdetto.

⚠ E si stampa sempre la **risoluzione raggiunta**, cioe' la separazione piu'
  piccola che *questo* giro avrebbe potuto vedere, piu' quanti campioni
  servirebbero per arrivare a quella voluta.  Un «indistinguibili» senza quel
  numero non vuol dire niente.

===========================================================================
⛔ QUEL CHE QUESTO BANCO **NON** PROVA, E VA DETTO

  · non prova il limitatore in generale — soglia, raddoppio, tetto di 15
    minuti, scadenza a 30 minuti di quiete: quello e' **B5**, che lo ha gia' e
    che qui non si rifa'.  Qui si tocca il limitatore **solo** per la parte che
    §4.4-bis lega ai tempi: l'azzeramento sul successo e il fatto che anche
    `TROPPI_TENTATIVI` non parta prima di un secondo (rilievo R11.10);
  · non prova che l'attaccante **non** possa distinguere i casi: prova che
    **questo giro, con questi campioni, non ci e' riuscito** — e stampa con
    quale risoluzione.  Un attaccante con diecimila campioni guarda piu' a
    fondo di noi, e la riga della risoluzione e' li' per non farlo dimenticare;
  · non attacca (`ATTACCA` non si manda mai): il campione finisce alla risposta
    a `CREDENZIALI`.  Cosi' il registro delle sessioni non entra nella misura e
    un `GIA_ATTIVA_REMOTA` non puo' inquinare un campione (B0.2).

⚠ **E un avviso a chi lo lancia**: un giro completo fa alcune decine di
  autenticazioni **fallite** sull'utente vero.  Se un giorno la pila PAM
  guadagnasse un `pam_faillock`, quell'utente si troverebbe bloccato **fuori**
  dal server.  Il sintomo qui sarebbe visibile — i campioni del caso «giusta»
  smetterebbero di ricevere `AMMESSO` e finirebbero fra gli scartati, senza
  verde — ma la cura sta fuori da questo file.
"""
import argparse
import asyncio
import importlib.util
import json
import os
import pwd
import random
import ssl
import statistics
import sys
import time

from aioquic.asyncio import connect
from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ Il cliente di prova di B3 si IMPORTA, non si ricopia (come fa B5).  Dentro
#    c'e' la riga che gli impedisce di dare gli eventi del canale di controllo
#    allo strato HTTP/3 di aioquic — senza la quale la connessione muore per
#    mano del CLIENT, e qui il sintomo sarebbe «il server non risponde in
#    tempo», cioe' un difetto di TEMPI attribuito al server.
_spec = importlib.util.spec_from_file_location(
    "b3cliente", os.path.join(QUI, "01-b3-cliente.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)

inquadra, s_str, MOTIVI = b3.inquadra, b3.s, b3.MOTIVI
T_CREDENZIALI = 0x0003
CREDENZIALI_ERRATE, TROPPI_TENTATIVI = 0x07, 0x08

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# ── I numeri della regola, tutti in un posto e tutti dichiarati ──────────────
SOGLIA = 5                # §4.4-bis: 5 fallimenti in 5 minuti
BILANCIO = 4              # ⛔ uno SOTTO la soglia, per chiave e per vita del server
RITARDO_FISSO = 1000.0    # §4.4-bis: nessuna risposta a CREDENZIALI prima di 1 s
RISOLUZIONE_VOLUTA = 50.0 # ms — i «cinquanta millisecondi» che il documento della
                          #      fase nomina come la separazione che conta
MINIMO_CAMPIONI = 10      # sotto questo non si giudica: si dice «sospeso»
RIPETIZIONI = 2000        # ricampionamenti del bootstrap
SEME = 20260810           # ⛔ fisso: due verdetti sugli stessi dati devono coincidere

CASI = ("inesistente", "sbagliata", "giusta")
# Che cosa DEVE tornare, per caso.  ⛔ Un campione che torna altro non entra
#    nelle mediane: e' la terza guardia contro il limitatore.
ATTESO = {"inesistente": ("RESPINTO", CREDENZIALI_ERRATE),
          "sbagliata": ("RESPINTO", CREDENZIALI_ERRATE),
          "giusta": ("AMMESSO", None)}

# Le sei permutazioni della terzina.  ⛔ L'ordine RUOTA a ogni terzina: se un
#    caso stesse sempre subito dopo l'accensione e un altro sempre in fondo,
#    qualunque deriva dentro il blocco finirebbe **nelle mediane** travestita da
#    differenza fra i casi.
ROTAZIONI = [("inesistente", "sbagliata", "giusta"),
             ("sbagliata", "giusta", "inesistente"),
             ("giusta", "inesistente", "sbagliata"),
             ("inesistente", "giusta", "sbagliata"),
             ("sbagliata", "inesistente", "giusta"),
             ("giusta", "sbagliata", "inesistente")]


# ===========================================================================
# Il filo
# ===========================================================================
async def apri(indirizzo, porta, percorso="/rcp/1"):
    """Una connessione nuova, e la sessione WebTransport su `/rcp/1`.

    ⚠ Una per campione, e non e' una scelta: §4.4 ammette **un solo tentativo
      per connessione**.  Il cronometro pero' parte DOPO — vedi `un_tentativo`."""
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


async def un_tentativo(indirizzo, porta, nome, parola):
    """Un campione: `CREDENZIALI` che parte, la risposta che arriva, i millisecondi.

    ⛔ CHE COSA STA DENTRO IL CRONOMETRO, E CHE COSA NO.

       Dentro: il viaggio di `CREDENZIALI`, il lavoro del server (limitatore,
       PAM, ritardo fisso) e il viaggio della risposta.  Fuori: la stretta di
       mano QUIC/TLS, l'apertura della sessione, `CIAO`/`ECCOMI`.

    ⚠ Il giro di rete e' dentro e non si toglie — ma e' **lo stesso per tutt'e
      tre i casi**, sullo stesso cammino e nella stessa vita del server: puo'
      spostare le tre mediane insieme, non separarle.  E' la ragione per cui il
      criterio e' una DIFFERENZA fra mediane e non un valore assoluto.

    ⛔ La parola d'ordine non finisce in nessun file (B13.2): di qui esce solo
       il **nome** e il tempo."""
    fuori = {"indirizzo": indirizzo, "nome": nome, "ms": None,
             "messaggio": None, "motivo": None, "esito": "errore", "errore": ""}
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
        #    Pretendere `AMMESSO` farebbe sollevare un'eccezione sui due casi
        #    che devono essere respinti — cioe' il banco non avrebbe il tempo
        #    proprio dei due casi che gli interessano di piu'.
        nome_msg, corpo_r, _ = await b3.attendi(cli, None, attesa=30)
        fuori["ms"] = (time.perf_counter() - t0) * 1000.0
        fuori["messaggio"] = nome_msg
        if nome_msg == "RESPINTO":
            fuori["motivo"] = corpo_r[0] if corpo_r else None
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
    """⛔ La terza guardia contro il limitatore: che cosa e' arrivato DAVVERO.

    Un campione conta solo se ha ricevuto quel che il suo caso prevede.  Un
    `TROPPI_TENTATIVI` non e' un campione di «parola sbagliata»: e' un'altra
    strada dentro il server — **non passa nemmeno da PAM** — e metterlo nella
    stessa mediana significherebbe mescolare due popolazioni sotto la stessa
    etichetta (E2)."""
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
# ⛔ IL BILANCIO DI §4.4-bis, SIMULATO PRIMA DI ESEGUIRE
# ===========================================================================
def simula(passi):
    """§4.4-bis letta come un modello, e applicata al PIANO prima che al filo.

    Tiene le due chiavi del server — il nome e l'indirizzo — conta i fallimenti,
    blocca la chiave che arriva a `SOGLIA`, ⛔ e **azzera la sola chiave del
    nome** su un successo, perche' e' quel che `banchi/rcp/rcp.c` fa
    (`azzera_tentativi(s->utente)`) e quel che §4.4-bis dice in fondo alla
    sezione: *«il contatore per nome … e' quello che si azzera con un successo»*.
    ⚠ Un tentativo bloccato non arriva a PAM e **non incrementa niente**: anche
      questo e' nel codice, ed e' la ragione per cui il suo tempo e' di un'altra
      strada.

    ⚠ E' un MODELLO — la mia lettura dell'arbitro, scritta prima di misurare —
      non una prova.  Serve a due cose e nessuna delle due e' «avere ragione»:
      dire **prima** se il piano resta sotto soglia, e dare al controllo
      un'attesa per ogni singolo tentativo invece di un'attesa complessiva.  Se
      il filo lo smentisce, uno dei due e' sbagliato e il banco dice quale
      tentativo li ha divisi.

    Restituisce (atteso per tentativo, picco dei fallimenti per chiave)."""
    falliti, bloccate, picco, esiti = {}, set(), {}, []
    for caso, _scarto, indirizzo, nome in passi:
        chiavi = [("nome", nome), ("indirizzo", indirizzo)]
        blocca = [c for c in chiavi if c in bloccate]
        if blocca:
            esiti.append(("RESPINTO", TROPPI_TENTATIVI, blocca))
            continue
        if caso == "giusta":
            falliti[("nome", nome)] = 0
            bloccate.discard(("nome", nome))
            esiti.append(("AMMESSO", None, []))
            continue
        for c in chiavi:
            falliti[c] = falliti.get(c, 0) + 1
            picco[c] = max(picco.get(c, 0), falliti[c])
            if falliti[c] >= SOGLIA:
                bloccate.add(c)
        esiti.append(("RESPINTO", CREDENZIALI_ERRATE, []))
    return esiti, picco


def verifica_piano(passi, modo):
    """⛔ Il piano si verifica PRIMA di eseguirlo, e se non torna non si parte.

    Un banco che scoprisse *dopo* di aver superato la soglia avrebbe gia'
    bloccato una chiave per trenta secondi, e i campioni che seguono
    misurerebbero il limitatore credendo di misurare PAM.

    Due modi, perche' i piani sono di due nature:

      `sotto-soglia`     nessun tentativo dev'essere bloccato.  E' il modo dei
                         campioni e della gamba `con-successo`;
      `blocco-dal-nome`  il **sesto** tentativo DEVE essere bloccato, e ⛔ solo
                         dal contatore **per nome**: se a bloccarlo fosse anche
                         quello per indirizzo, la gamba non direbbe piu' niente
                         sull'azzeramento (B0.3)."""
    esiti, picco = simula(passi)
    righe = [f"{tipo}={chiave}: {n}" for (tipo, chiave), n in sorted(picco.items())]
    bloccati = [i + 1 for i, (_m, mo, _c) in enumerate(esiti)
                if mo == TROPPI_TENTATIVI]
    if modo == "sotto-soglia":
        ok = not bloccati and max(picco.values(), default=0) <= BILANCIO
        righe.append(f"tentativi che il modello vede bloccati: {bloccati or 'nessuno'}"
                     f"  (atteso: nessuno)")
    else:
        chi = esiti[5][2] if len(esiti) > 5 else []
        ok = (bloccati and bloccati[0] == 6
              and [t for t, _k in chi] == ["nome"])
        righe.append(f"primo tentativo bloccato: {bloccati[0] if bloccati else 'nessuno'}"
                     f" (atteso: 6), e a bloccarlo: {chi or 'nessuno'}"
                     f" (atteso: solo il nome)")
    return ok, esiti, righe


# ===========================================================================
# I piani
# ===========================================================================
def piano_blocco(k, per_caso, indirizzi, utente, inesistente):
    """La sequenza di UNA vita del server: tre scaldate, poi `per_caso` terzine.

    ⛔ I tre passi di scaldata sono scartati **per regola scritta prima**, e
       sono uno per caso: la strada del successo e quella del fallimento si
       scaldano separatamente, perche' non e' lo stesso codice a percorrerle.

    ⛔ E gli indirizzi si alternano **fra i FALLIMENTI**, non fra i passi: solo i
       fallimenti muovono i contatori di §4.4-bis, e alternare su tutti i passi
       lascerebbe l'alternanza in balia di dove cade il successo — al primo
       blocco dava sei fallimenti su un indirizzo e due sull'altro, cioe' un
       indirizzo **sopra la soglia**.  ⚠ E' stato trovato dalla prova a secco
       del piano, prima di misurare, che e' il posto in cui costa meno.

    ⚠ La partenza cambia a ogni blocco, cosi' nessun caso finisce legato a un
      indirizzo: se un giorno i due cammini avessero tempi diversi, la
      differenza si spalmerebbe su tutt'e tre le mediane invece di separarne una."""
    passi = [("giusta", True), ("inesistente", True), ("sbagliata", True)]
    for g in range(per_caso):
        for caso in ROTAZIONI[(k + g) % len(ROTAZIONI)]:
            passi.append((caso, False))
    fuori, falliti = [], 0
    for caso, scarto in passi:
        ind = indirizzi[(falliti + k) % len(indirizzi)]
        if caso != "giusta":
            falliti += 1
        nome = inesistente if caso == "inesistente" else utente
        fuori.append((caso, scarto, ind, nome))
    return fuori


def piano_controllo(gamba, indirizzi, utente):
    """⭐ 4 falliti · UN SUCCESSO (o un nono fallito) · altri 4.

    Le due gambe sono **identiche in tutto tranne il quinto passo**, ed e' li'
    che sta la domanda: se il successo azzera il contatore del nome, gli otto
    fallimenti sono 4+4 e nessuno viene bloccato; se non azzera, al **sesto**
    scatta `TROPPI_TENTATIVI`.

    ⛔ I primi cinque passi arrivano da un indirizzo e gli ultimi quattro
       dall'altro: cosi' quando il sesto tentativo viene bloccato — nella gamba
       che DEVE bloccare — il suo indirizzo ha **un solo** fallimento addosso, e
       l'unico contatore che puo' averlo fermato e' quello per NOME.  Con un
       indirizzo solo, l'ottavo sarebbe bloccato **anche su un server che azzera
       perfettamente**, e il rosso finirebbe sull'imputato sbagliato."""
    a, b = indirizzi[0], indirizzi[1]
    passi = [("sbagliata", False, a, utente) for _ in range(4)]
    passi.append(("giusta" if gamba == "con-successo" else "sbagliata",
                  False, a, utente))
    passi += [("sbagliata", False, b, utente) for _ in range(4)]
    return passi


# ===========================================================================
# L'esecuzione
# ===========================================================================
def scrivi(uscita, rec):
    """Una riga per campione, scritta e **svuotata** subito.

    ⚠ Un file scritto e chiuso e' un fatto; una riga in un buffer e' una
      speranza sul momento in cui qualcuno la vedra' — e questo processo muore
      e rinasce a ogni blocco."""
    with open(uscita, "a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def esistenza(nome, deve_esistere):
    """⛔ «Utente inesistente» si VERIFICA, non si suppone.

    Se il nome che crediamo inesistente fosse un utente vero, i due casi
    «inesistente» e «sbagliata» sarebbero **lo stesso caso** misurato due volte,
    e le due mediane coinciderebbero per costruzione: il banco stamperebbe il
    suo verde piu' vuoto.  ⚠ Lo strumento e' il **secondo testimone**: la banca
    dati degli utenti, non il server."""
    try:
        pwd.getpwnam(nome)
        c_e = True
    except KeyError:
        c_e = False
    return c_e == deve_esistere, c_e


async def prova_indirizzi(indirizzi, porta):
    """⛔ Il banco sa parlare da TUTT'E DUE gli indirizzi? — si chiede prima.

    Tutta la separazione dei due contatori di §4.4-bis poggia su questo: se il
    server fosse acceso su un indirizzo solo, meta' dei tentativi fallirebbe per
    rete e l'altra meta' arriverebbe dalla stessa chiave — cioe' il controllo
    misurerebbe il contatore sbagliato mentre il banco crede di averli separati.

    ⚠ Si arriva a `ECCOMI` e si chiude: nessun `CREDENZIALI`, quindi **nessun
      contatore si muove** e nessun posto viene preso.  E' un controllo che non
      costa niente al bilancio."""
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
                  f"su tutt'e due gli indirizzi: senza, i due contatori di "
                  f"§4.4-bis non sono separati e il controllo non vale (B0.3)")
            return False
        finally:
            if gestore is not None:
                try:
                    await gestore.__aexit__(None, None, None)
                except Exception:  # noqa: BLE001
                    pass
    print(f"    {VERDE}OK{GRIGIO}  il server risponde su tutt'e due gli "
          f"indirizzi: {', '.join(indirizzi)}  (fino a ECCOMI, senza toccare "
          f"nessun contatore)")
    return True


async def esegui(a, passi, tipo, etichetta, modo):
    ok, esiti, righe = verifica_piano(passi, modo)
    print(f"    -- piano di «{etichetta}»: {len(passi)} tentativi, modo "
          f"«{modo}» (soglia {SOGLIA}, bilancio {BILANCIO})")
    for r in righe:
        print(f"       {r}")
    if not ok:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il piano non fa quel che deve: non parte. "
              f"Un piano che sfora misurerebbe il limitatore credendo di "
              f"misurare PAM; uno che non blocca dove deve renderebbe cieco il "
              f"controllo")
        return 2
    if not await prova_indirizzi(a.indirizzi, a.porta):
        return 2
    for i, (caso, scarto, ind, nome) in enumerate(passi, 1):
        parola = a.parola if caso == "giusta" else a.sbagliata
        atteso_msg, atteso_motivo, _chi = esiti[i - 1]
        rec = await un_tentativo(ind, a.porta, nome, parola)
        rec.update({"giro": a.giro, "tipo": tipo, "etichetta": etichetta,
                    "blocco": a.blocco, "ordine": i, "caso": caso,
                    "scaldata": scarto, "classe": classifica(rec, caso),
                    # ⭐ l'attesa del modello viaggia col campione: il verdetto
                    #    la confronta con quel che e' arrivato, tentativo per
                    #    tentativo, invece di guardare solo il totale.
                    "atteso_modello": atteso_msg,
                    "atteso_motivo": atteso_motivo})
        scrivi(a.uscita, rec)
        ms = "  —  " if rec["ms"] is None else f"{rec['ms']:8.1f}"
        motivo = MOTIVI.get(rec["motivo"], "") if rec["motivo"] is not None else ""
        atteso = MOTIVI.get(atteso_motivo, atteso_msg)
        concorda = "" if (rec["messaggio"] == atteso_msg
                          and rec["motivo"] == atteso_motivo) else \
                   f"⛔ il modello diceva {atteso}"
        marca = "scaldata" if scarto else ""
        print(f"       {i:2d}. {caso:12s} {ind:13s} {ms} ms  "
              f"{rec['messaggio'] or rec['errore']:10s} {motivo:18s} "
              f"{rec['classe']:10s} {marca} {concorda}")
    return 0


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
    """Scarto assoluto mediano: la dispersione della stessa famiglia della mediana."""
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
    """Quanto tempo dice il SERVER, e da quale indirizzo dice di aver ricevuto.

    ⛔ Non e' l'arbitro — il tempo che conta e' quello letto dal lato che riceve
       (§8.1, e il registro e' la stessa mano che ha scritto il codice).  Serve a
       **separare due imputati** quando il verdetto e' rosso:

         «il secondo fisso e' passato (1003 ms)»  ⇒ a governare e' stato il
                                                     ritardo fisso;
         «il secondo fisso e' passato (3070 ms)»  ⇒ a governare e' stato PAM, e
                                                     la separazione non e' del
                                                     ritardo fisso ma di quel che
                                                     PAM aggiunge sopra.

    ⚠ Se il registro non c'e' o non dice niente, non si inventa: si dichiara.
      «Vuoto» e «non letto» sono due fatti diversi (E8)."""
    if not percorso or not os.path.exists(percorso):
        return None, "il registro del server non e' stato letto (file assente)"
    ammessi, respinti, indirizzi, fissi = [], [], set(), []
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
                    fissi.append(n)
                    (ammessi if ultimo_pam == "ammesso" else respinti).append(n)
                elif " da=" in riga and ("respinto motivo" in riga or "ammesso utente" in riga):
                    indirizzi.add(riga.rsplit(" da=", 1)[1].strip().rsplit(":", 1)[0])
    except OSError as e:
        return None, f"il registro del server non si legge: {e}"
    if not fissi:
        return None, ("il registro c'e' ma non contiene nessuna riga «il secondo "
                      "fisso e' passato»: o non e' il registro di questo giro, o "
                      "il server non e' quello con RCP innestato")
    return {"fissi": fissi, "ammessi": ammessi, "respinti": respinti,
            "indirizzi": sorted(indirizzi)}, ""


# ===========================================================================
# Il verdetto
# ===========================================================================
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
    #    B4 ha gia' dichiarato «conforme» una registrazione rimasta li' dal giro
    #    prima: qui il giro e' scritto in ogni riga e si confronta.
    estranei = [r for r in dati if r.get("giro") != a.giro]
    if estranei:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ {len(estranei)} righe su {len(dati)} sono "
              f"di un altro giro: non giudico un file stantio")
        return 2
    if not dati:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ il file c'e' ed e' vuoto: nessun campione")
        return 2

    guasti, sospeso = 0, False
    campioni = [r for r in dati if r["tipo"] == "campione"]
    vite = sorted({r["blocco"] for r in campioni})

    print()
    print("    == I DENOMINATORI — su che cosa ha guardato questo giro")
    print(f"    --  vite del server (accensioni): {len(vite)}")
    print(f"    --  tentativi in tutto: {len(dati)}  "
          f"(campioni {len(campioni)}, controllo {len(dati) - len(campioni)})")

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
              f"⛔ risposte del limitatore {len(limitati)} · "
              f"inattese {len(inattesi)} · errori {len(errori)} · "
              f"indirizzi {per_ind}")
        if limitati:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ {len(limitati)} campioni di «{caso}» "
                  f"hanno ricevuto TROPPI_TENTATIVI: il bilancio di §4.4-bis non "
                  f"ha retto, e quei tempi sono del LIMITATORE, non di PAM")
            guasti += 1
        if inattesi or errori:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ «{caso}»: {len(inattesi)} risposte "
                  f"inattese e {len(errori)} errori — un caso che non riceve quel "
                  f"che deve non e' un campione di quel caso")
            for r in (inattesi + errori)[:3]:
                print(f"        {r['messaggio'] or ''} {r['errore']}")
            guasti += 1

    # ⭐ Le scaldate si STAMPANO, non si nascondono: se il primo campione di ogni
    #    vita e' molto diverso dagli altri, quel numero e' la misura di E9.
    print()
    print("    == ⚠ I primi campioni di ogni vita del server (scartati per regola)")
    for caso in CASI:
        sc = [r["ms"] for r in campioni
              if r["caso"] == caso and r["scaldata"] and r["classe"] == "atteso"]
        if not sc:
            print(f"    --  {caso:12s} nessuna scaldata utilizzabile")
            continue
        tenuti = serie[caso]
        rif = statistics.median(tenuti) if tenuti else float("nan")
        print(f"    --  {caso:12s} n={len(sc):2d}  mediana {statistics.median(sc):8.1f} ms"
              f"   (i tenuti: {rif:8.1f} ms · scarto "
              f"{statistics.median(sc) - rif:+7.1f} ms)")

    # ── 1. il secondo fisso, campione per campione ──────────────────────────
    print()
    print(f"    == ⛔ Il primo criterio: NESSUNA risposta a CREDENZIALI prima di "
          f"{RITARDO_FISSO:.0f} ms (§4.4-bis)")
    tutte = [r for r in dati if r["classe"] in ("atteso", "limitatore")
             and r["ms"] is not None]
    sotto = [r for r in tutte if r["ms"] < RITARDO_FISSO]
    print(f"    --  guardate {len(tutte)} risposte (campioni, scaldate e "
          f"controllo insieme: il ritardo fisso vale per TUTTE, «anche quando la "
          f"risposta e' AMMESSO» e «anche quando e' TROPPI_TENTATIVI»)")
    if sotto:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ {len(sotto)} risposte sotto il secondo. "
              f"La piu' veloce: {min(r['ms'] for r in sotto):.1f} ms")
        for r in sotto[:5]:
            print(f"        {r['caso']:12s} {r['messaggio']} {r['ms']:.1f} ms")
        guasti += 1
    elif not tutte:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ nessuna risposta da guardare")
        guasti += 1
    else:
        print(f"    {VERDE}OK{GRIGIO}  {len(tutte)} su {len(tutte)} ≥ "
              f"{RITARDO_FISSO:.0f} ms — la piu' veloce: "
              f"{min(r['ms'] for r in tutte):.1f} ms")
    # ⭐ E il rifiuto DENTRO la finestra si guarda a parte, perche' e' il caso
    #    del rilievo R11.10: §4.4-bis diceva «subito» in una riga e «non prima
    #    di un secondo» in un'altra, e un rifiuto immediato dentro la finestra
    #    **rimette il tempismo come canale dal lato opposto**.  Non entra nelle
    #    tre mediane — non e' uno dei tre casi — ma il suo tempo si stampa.
    dentro = [r["ms"] for r in dati if r["classe"] == "limitatore"
              and r["ms"] is not None]
    if dentro:
        print(f"    --  e le risposte TROPPI_TENTATIVI (che non passano da PAM): "
              f"n={len(dentro)}  mediana {statistics.median(dentro):.1f} ms  "
              f"min {min(dentro):.1f} ms")
    else:
        print(f"    --  nessuna risposta TROPPI_TENTATIVI in tutto il giro: "
              f"⚠ se manca anche nella gamba «senza-successo», il controllo "
              f"qui sotto e' cieco")

    # ── 2. le tre mediane ───────────────────────────────────────────────────
    print()
    print("    == ⛔ Il secondo criterio: le tre mediane, e se si separano")
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

    coppie = [("inesistente", "sbagliata"), ("inesistente", "giusta"),
              ("sbagliata", "giusta")]
    print()
    print("    differenza delle mediane, con l'intervallo al 95 % che la contiene:")
    for u, v in coppie:
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
        # ⭐ quanti campioni servirebbero per arrivare alla risoluzione voluta:
        #    l'ampiezza scende come 1/√n, quindi n cresce col quadrato.
        n_ora = min(len(xa), len(xb))
        n_serve = int(n_ora * (risoluzione / RISOLUZIONE_VOLUTA) ** 2) + 1
        marca = f"{ROSSO}SI DISTINGUONO{GRIGIO}" if not contiene_zero else (
            f"{VERDE}indistinguibili{GRIGIO}" if risoluzione <= RISOLUZIONE_VOLUTA
            else f"{GIALLO}SOSPESO{GRIGIO}")
        etichetta = "  ⚠ e' QUESTA la coppia che dice i nomi degli utenti" \
            if (u, v) == ("inesistente", "sbagliata") else ""
        print(f"      {u:12s} − {v:12s} {d:+9.1f} ms   "
              f"[{lo:+8.1f}; {hi:+8.1f}]   risoluzione ±{risoluzione:.1f} ms   "
              f"{marca}{etichetta}")
        if not contiene_zero:
            guasti += 1
        elif risoluzione > RISOLUZIONE_VOLUTA:
            print(f"           ⚠ per arrivare a ±{RISOLUZIONE_VOLUTA:.0f} ms con "
                  f"questo rumore servirebbero ~{n_serve} campioni per caso "
                  f"(adesso {n_ora})")
            sospeso = True

    # ── 3. il controllo del limitatore ──────────────────────────────────────
    print()
    print("    == ⭐ Il controllo: 4 falliti · un successo · altri 4 (§4.4-bis)")
    for gamba, attesi in (("con-successo", "otto CREDENZIALI_ERRATE, mai un blocco"),
                          ("senza-successo", "il SESTO fallito bloccato")):
        righe = [r for r in dati if r["tipo"] == "controllo"
                 and r["etichetta"] == gamba]
        if not righe:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ la gamba «{gamba}» non e' stata "
                  f"eseguita: senza le due gambe il controllo non distingue "
                  f"«il successo azzera» da «lo strumento non vede i blocchi»")
            guasti += 1
            continue
        righe.sort(key=lambda r: r["ordine"])
        def nomina(msg, motivo):
            return MOTIVI.get(motivo, str(motivo)) if motivo is not None else (msg or "errore")
        print(f"    --  {gamba:15s} atteso: {attesi}")
        print(f"        modello:  " + " ".join(
            nomina(r["atteso_modello"], r["atteso_motivo"]) for r in righe))
        print(f"        sul filo: " + " ".join(
            nomina(r["messaggio"], r["motivo"]) for r in righe))
        # ⛔ Il confronto e' TENTATIVO PER TENTATIVO, non sul totale: «otto su
        #    nove» non dice quale, e quale e' tutta l'informazione che serve.
        divergenti = [r["ordine"] for r in righe
                      if r["messaggio"] != r["atteso_modello"]
                      or r["motivo"] != r["atteso_motivo"]]
        motivi = [r["motivo"] for r in righe]
        bloccati = [r["ordine"] for r in righe if r["motivo"] == TROPPI_TENTATIVI]
        if len(righe) != 9:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ la gamba «{gamba}» ha {len(righe)} "
                  f"tentativi invece di 9: non e' la sequenza del controllo")
            guasti += 1
            continue
        if divergenti:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ il filo e il modello di §4.4-bis si "
                  f"dividono ai tentativi {divergenti}")
            guasti += 1
        if gamba == "con-successo":
            if not bloccati and righe[4]["messaggio"] == "AMMESSO":
                print(f"    {VERDE}OK{GRIGIO}  ⭐ l'OTTAVO non e' bloccato (nessuno "
                      f"dei nove lo e'): il successo ha azzerato il contatore "
                      f"del nome, ed e' l'unico che poteva bloccare — i due "
                      f"indirizzi tengono l'altro contatore a 4 e a 4")
            else:
                print(f"    {ROSSO}NO{GRIGIO}  ⛔ la gamba con il successo non e' "
                      f"pulita (bloccati: {bloccati or 'nessuno'}; il quinto ha "
                      f"ricevuto {righe[4]['messaggio']})")
                print(f"        ⚠ prima di accusare l'azzeramento: se il blocco "
                      f"e' arrivato, guarda quanti INDIRIZZI ha visto il server "
                      f"qui sotto. Se ne ha visto uno solo, a bloccare e' stato "
                      f"il contatore per indirizzo e questa gamba non dice "
                      f"niente sull'azzeramento (B0.3)")
                guasti += 1
        else:
            if motivi[:5] == [CREDENZIALI_ERRATE] * 5 and bloccati and bloccati[0] == 6:
                print(f"    {VERDE}OK{GRIGIO}  ⭐ e il controllo che dice NO: senza "
                      f"il successo il SESTO fallito riceve TROPPI_TENTATIVI — "
                      f"lo strumento sa vedere un blocco, e le due gambe "
                      f"differiscono solo per il quinto passo")
            else:
                print(f"    {ROSSO}NO{GRIGIO}  ⛔ senza il successo il blocco NON e' "
                      f"arrivato al sesto (bloccati: {bloccati or 'nessuno'}): "
                      f"allora la gamba verde qui sopra non prova l'azzeramento "
                      f"— proverebbe soltanto che questo server non blocca mai "
                      f"(rilievo R3.9)")
                guasti += 1

    # ── 4. il secondo testimone: il registro del server ─────────────────────
    print()
    print("    == ⚠ Il registro del server — diagnosi, NON arbitro (§8.1)")
    reg, perche = leggi_registro(a.registro)
    if reg is None:
        print(f"    --  {perche}")
    else:
        # ⚠ Una mediana di zero numeri non e' uno zero: si dice che non c'e'.
        def med(x):
            return f"{statistics.median(x):.0f} ms" if x else "— (nessuna riga)"
        print(f"    --  «il secondo fisso e' passato»: n={len(reg['fissi'])}  "
              f"mediana {med(reg['fissi'])}  "
              f"(ammessi {med(reg['ammessi'])} su {len(reg['ammessi'])} · "
              f"respinti {med(reg['respinti'])} su {len(reg['respinti'])})")
        print(f"    --  se quel numero e' ~{RITARDO_FISSO:.0f} ms a governare e' "
              f"stato il RITARDO FISSO; se e' molto piu' alto a governare e' "
              f"stato PAM, e una separazione fra le mediane e' di PAM — non del "
              f"ritardo fisso")
        print(f"    --  indirizzi di provenienza visti DAL SERVER: "
              f"{reg['indirizzi']}")
        if len(reg["indirizzi"]) < 2:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ il server ha visto UN SOLO indirizzo: "
                  f"la separazione dei due contatori di §4.4-bis non c'e' stata, "
                  f"e il controllo qui sopra non vale (B0.3)")
            guasti += 1

    # ── L'esito ─────────────────────────────────────────────────────────────
    print()
    if guasti:
        print(f"    {ROSSO}⛔ B8: {guasti} "
              f"{'punto non passa' if guasti == 1 else 'punti non passano'}"
              f"{GRIGIO}")
        return 1
    if sospeso:
        print(f"    {GIALLO}⚠ B8 SOSPESO: quel che ho guardato non si separa, ma "
              f"non ho guardato abbastanza da poterlo chiamare "
              f"«indistinguibile»{GRIGIO}")
        print(f"    ⚠ «non ho visto una differenza» e «non c'e' una differenza» "
              f"sono due cose diverse: rilancia con piu' blocchi")
        return 3
    print(f"    {VERDE}⭐ B8 passa: ogni risposta a CREDENZIALI ≥ "
          f"{RITARDO_FISSO:.0f} ms, le tre mediane non si separano oltre il "
          f"rumore, e il controllo 4·successo·4 distingue{GRIGIO}")
    print(f"    ⚠ e vale fin dove si e' guardato: le risoluzioni sono stampate "
          f"qui sopra, coppia per coppia")
    return 0


def previsione(a):
    print("== B8 — che cosa si misura, e che cosa mi aspetto PRIMA di misurare")
    print()
    print("  I tre casi, e la coppia che conta:")
    print("    inesistente  un utente che NON esiste (verificato con getpwnam)")
    print("    sbagliata    l'utente vero, parola d'ordine sbagliata")
    print("    giusta       l'utente vero, parola giusta  → AMMESSO")
    print("    ⚠ la coppia «inesistente − sbagliata» e' quella che, se si separa,")
    print("      regala i nomi degli utenti a chi cronometra.")
    print()
    print("  L'atteso, scritto qui prima dei numeri:")
    print(f"    1. ogni risposta a CREDENZIALI ≥ {RITARDO_FISSO:.0f} ms — B3 ha gia'")
    print("       misurato 1074–1085 ms sull'AMMESSO il 10 agosto 2026;")
    print("    2. le tre mediane indistinguibili secondo la regola dell'intervallo;")
    print("    3. il controllo con-successo: otto CREDENZIALI_ERRATE, nessun blocco;")
    print("    4. il controllo senza-successo: il SESTO fallito bloccato.")
    print()
    print("  `[?]` E una previsione che puo' rendere ROSSO il punto 2, scritta")
    print("  adesso perche' domani sembri una previsione e non una scusa:")
    print("    `banchi/rcp/autenticazione.c` usa il servizio PAM «login», e su")
    print("    Debian `/etc/pam.d/login` porta `pam_faildelay.so delay=3000000`.")
    print("    Se quel modulo e' nella pila, la strada del FALLIMENTO aspetta")
    print("    ~3 s (con la randomizzazione di libpam, ±25 %) e quella del")
    print("    SUCCESSO no: le mediane si separerebbero di secondi, e la")
    print("    separazione NON sarebbe del ritardo fisso — sarebbe di quel che")
    print("    PAM aggiunge sopra.  ⭐ A distinguere i due imputati e' la riga")
    print("    «il secondo fisso e' passato (N ms)» del registro del server, che")
    print("    il verdetto stampa apposta.")
    print()
    print(f"  I numeri della regola: bilancio {BILANCIO} fallimenti per chiave e")
    print(f"  per vita del server (soglia {SOGLIA}), risoluzione voluta "
          f"±{RISOLUZIONE_VOLUTA:.0f} ms,")
    print(f"  minimo {MINIMO_CAMPIONI} campioni per caso, bootstrap "
          f"{RIPETIZIONI} ripetizioni, seme {SEME}.")
    return 0


def principale():
    p = argparse.ArgumentParser(description="B8 — il secondo fisso e le tre mediane")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--indirizzi", default="127.0.0.1,192.168.0.2",
                   help="⛔ due, e servono a tenere separati i due contatori di §4.4-bis")
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="prova")
    p.add_argument("--sbagliata", default="questa-non-e-la-parola-di-nessuno",
                   help="la parola SBAGLIATA: un letterale che non e' di nessuno")
    p.add_argument("--blocco", type=int, default=0)
    p.add_argument("--per-caso", type=int, default=3,
                   help="campioni tenuti per caso in ogni vita del server")
    p.add_argument("--controllo", choices=("con-successo", "senza-successo"))
    p.add_argument("--verdetto", action="store_true")
    p.add_argument("--previsione", action="store_true")
    p.add_argument("--giro", default="")
    p.add_argument("--uscita", default="b8-campioni.jsonl")
    p.add_argument("--registro", default="")
    a = p.parse_args()
    a.indirizzi = [x for x in a.indirizzi.split(",") if x]

    if a.previsione:
        return previsione(a)
    if a.verdetto:
        return verdetto(a)
    if len(a.indirizzi) < 2:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ servono DUE indirizzi di provenienza: "
              f"con uno solo il contatore per indirizzo blocca al quinto "
              f"fallimento e il controllo darebbe rosso sul codice giusto")
        return 2

    # ⛔ LO STATO INIZIALE SI DICHIARA E SI VERIFICA (B0.1), e qui la cosa da
    #    verificare e' che i due casi falliti siano DAVVERO due casi diversi.
    inesistente = f"nessuno-b8-{a.blocco}"
    for nome, deve, che in ((a.utente, True, "l'utente vero"),
                            (inesistente, False, "l'utente inesistente")):
        ok, c_e = esistenza(nome, deve)
        if not ok:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ {che} «{nome}»: "
                  f"{'esiste' if c_e else 'non esiste'} — il contrario di quel "
                  f"che questo banco presume. I due casi falliti sarebbero lo "
                  f"stesso caso misurato due volte")
            return 2
    print(f"    {VERDE}OK{GRIGIO}  «{a.utente}» esiste e «{inesistente}» no "
          f"(getpwnam: un testimone diverso dal server)")

    if a.controllo:
        passi = piano_controllo(a.controllo, a.indirizzi, a.utente)
        modo = "sotto-soglia" if a.controllo == "con-successo" else "blocco-dal-nome"
        return asyncio.run(esegui(a, passi, "controllo", a.controllo, modo))
    passi = piano_blocco(a.blocco, a.per_caso, a.indirizzi, a.utente, inesistente)
    return asyncio.run(
        esegui(a, passi, "campione", f"blocco {a.blocco}", "sotto-soglia"))


if __name__ == "__main__":
    sys.exit(principale())
