#!/usr/bin/env python3
"""01-b3-cliente.py — il cliente di prova: la stretta di mano di RCP, scritta una seconda volta.

    python3 01-b3-cliente.py --utente prova --parola X [--registra t.rcpreg]

---------------------------------------------------------------------------
⛔ IL SUO MESTIERE, CHE NON E' «FUNZIONARE»

`PIANO.md` §1.1: questo e' **il secondo lettore di `RCP.md`**, in un linguaggio
diverso dal server.  ⛔ **Chi lo fa crescere non guarda il C**: se lo
guardasse ne erediterebbe i fraintendimenti, e due programmi scritti dalla
stessa mano che vanno d'accordo non confermano niente.

⭐ Il suo valore non e' il verde: e' che chi lo scrive **deve scegliere** dove
   la specifica ammette due letture, e quelle scelte vanno scritte in «che cosa
   NON ha funzionato» — sono difetti del documento, e questa e' la fase in cui
   costano meno.

---------------------------------------------------------------------------
⭐ E REGISTRA, NEL FORMATO DI §11.1

Ogni byte che passa sul canale di controllo finisce in una registrazione che
**il validatore di B4 puo' giudicare**.  ⛔ La parola d'ordine no: viene
oscurata come impone §11.1 — lunghezza vera, byte sostituiti con `0x2A`,
impronta di quel che c'era.  Cosi' il validatore vede l'inquadratura intera e
la parola non finisce in un file.

⛔ **E si registra anche quando la stretta di mano NON riesce.**  Un
`CONGEDO(GIA_ATTIVA_REMOTA)` e' l'oggetto che il terzo giro di B3 esiste per
produrre: se la traccia si scrivesse solo lungo la strada che riesce, l'unico
banco dell'invariante I2 non consegnerebbe niente all'arbitro (rilievo R8.9).

⛔ **E il codice d'uscita dice CHE COSA e' successo alla connessione**: `0` sono
rimasto attaccato per tutto il tempo chiesto, `4` la connessione o la sessione
sono cadute prima — e il registro dice quale delle due (rilievi R8.2, R8.4).
`5` nessun `TELA` e' arrivato (§7.1, il silenzio).  ⭐ `6` — 22 agosto 2026 —
**la scena chiesta non e' esercitabile**: e' il caso di `--puntatore-vecchia`
quando non c'e' nessuna tela precedente, o quando la tela nuova non e' piu'
piccola.  ⛔ Non e' `1` e non e' `0`: un banco che leggesse «tutto bene» da una
scena che non e' avvenuta sarebbe verde per costruzione, e un banco che
leggesse «il prodotto ha sbagliato» darebbe il rosso all'imputato sbagliato.
"""
import argparse
import asyncio
import hashlib
import json
import os
import ssl
import struct
import sys
import time

from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import HeadersReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent

CLIENT, SERVER = 1, 2
T = {"CIAO": 0x0001, "ECCOMI": 0x0002, "CREDENZIALI": 0x0003, "AMMESSO": 0x0004,
     "RESPINTO": 0x0005, "ATTACCA": 0x0006, "SESSIONE": 0x0007,
     # ⭐ La strada della TELA, entrata qui il 16 agosto 2026 (sottofase 6.6).
     #    ⛔ `fasi/06-la-tela-e-la-vista.md` §0 punto 6: erano nel protocollo da
     #    una settimana e questo cliente **non ne mandava nemmeno uno**.
     "VISTA": 0x0008, "DISPOSIZIONE": 0x0009, "CURSORE_FORMA": 0x000A,
     "ADATTA_TELA": 0x000B, "CONGEDO": 0x000C, "RICHIEDI_CHIAVE": 0x000D,
     "TELA": 0x000E, "TERMINA_SESSIONE": 0x0011}
NOME = {v: k for k, v in T.items()}
# ⛔ IL CANALE DI INPUT STA IN UN DIZIONARIO SUO, e non e' pignoleria: `NOME`
#    e' la mappa inversa di `T` e la usa `_sfoglia()` per dare un nome ai
#    messaggi che arrivano **sul canale di controllo**.  Un `0x0101` la' dentro
#    farebbe comparire la parola «PUNTATORE» nel registro di un messaggio di
#    controllo malformato — cioe' una diagnosi che manda a guardare il canale
#    sbagliato.  ⚠ E i canali sono due davvero: §2.5, byte alto `0x00` contro
#    `0x01`.
T_PUNTATORE = 0x0101            # §7.3
# I due esiti e i tre motivi di `TELA` — §7.1.
TELA_ESITO = {1: "ADATTATA", 2: "RIFIUTATA"}
TELA_MOTIVO = {0: "-", 1: "COMPOSITORE_INCAPACE", 2: "MISURA_FUORI_LIMITI",
               3: "NON_ORA"}
MOTIVI = {0x07: "CREDENZIALI_ERRATE", 0x08: "TROPPI_TENTATIVI",
          0x09: "NIENTE_IN_COMUNE", 0x0A: "VERSIONE_INCOMPATIBILE",
          0x0B: "ERRORE_PROTOCOLLO", 0x0D: "TEMPO_SCADUTO",
          0x0E: "SESSIONE_NON_SERVIBILE", 0x0F: "GIA_ATTIVA_REMOTA"}


def s(t):
    b = t.encode("utf-8") if isinstance(t, str) else t
    return struct.pack("!H", len(b)) + b


def inquadra(tipo, corpo):
    return struct.pack("!HI", tipo, len(corpo)) + corpo


def _varint(d, i):
    """Legge un intero variabile QUIC da `d` a partire da `i`.

    Restituisce (valore, prossimo indice), oppure (None, i) se i byte non
    bastano.  ⚠ La lunghezza sta nei due bit alti del primo byte, e il valore
    e' quel che resta: leggere il primo byte per intero e' l'errore che fa
    scambiare 0x40 0x41 per due frame."""
    if i >= len(d):
        return None, i
    n = 1 << (d[i] >> 6)
    if i + n > len(d):
        return None, i
    v = d[i] & 0x3F
    for k in range(1, n):
        v = (v << 8) | d[i + k]
    return v, i + n


def _capsula_chiusura(d):
    """Cerca `CLOSE_WEBTRANSPORT_SESSION` (0x2843) e ne torna il codice.

    ⛔ Sul filo della CONNECT le capsule viaggiano **dentro i frame DATA**
       (RFC 9297), quindi il caso normale e' `DATA(0x00) → capsula`.  Il caso
       in cui la capsula arriva **nuda** e' un difetto del server — un browser
       leggerebbe `0x2843` come un tipo di frame HTTP/3 sconosciuto e la
       butterebbe (RFC 9114 §9) — e questo lettore lo riconosce per poterlo
       DIRE, non per perdonarlo.

    Restituisce (codice, nuda) oppure (None, False)."""
    def dentro(b):
        i = 0
        while i < len(b):
            tipo, j = _varint(b, i)
            if tipo is None:
                return None
            lung, j = _varint(b, j)
            if lung is None or j + lung > len(b):
                return None
            if tipo == 0x2843 and lung >= 4:
                return b[j + 3]      # i quattro byte del codice, il piu' basso
            i = j + lung
        return None

    # 1. la forma giusta: uno o piu' frame DATA, e le capsule dentro
    i = 0
    while i < len(d):
        tipo, j = _varint(d, i)
        if tipo is None:
            break
        lung, j = _varint(d, j)
        if lung is None or j + lung > len(d):
            break
        if tipo == 0x00:             # DATA
            c = dentro(d[j:j + lung])
            if c is not None:
                return c, False
        i = j + lung
    # 2. la forma sbagliata: la capsula senza il frame che la porta
    c = dentro(d)
    return (c, True) if c is not None else (None, False)


class Registratore:
    """Il formato di RCP.md §11.1, scritto una volta sola.

    ⛔⛔ LA MAGIA E' `RCPREG 0x00 0x02`, E FINO AL 16 AGOSTO 2026 NON LO ERA.

    ⭐ **E' il difetto piu' grosso trovato dalla sottofase 6.6, e non era nel
       prodotto: era fra due banchi.**  Il 12 agosto 2026 il formato di §11.1 e'
    passato a `0x00 0x02` — il blocco porta il campo `fine` e cresce da 16 a 17
    byte — e `01-b4-validatore.py` ha imparato a **rifiutare** il formato
    vecchio, come §11.1 gli impone: *«un validatore vecchio deve RIFIUTARE il
    formato nuovo, non leggerlo di traverso»*.

    ⛔ Ma questo registratore ha continuato a scrivere `0x00 0x01`.  ⇒ Da quel
       giorno **ogni traccia di B3 usciva 2 dall'arbitro** — «registrazione
    malformata» — e le cinque chiamate `valida` di `01-b3-lancia.sh` fallivano
    tutte, ⛔ facendo uscire **1** il banco intero.  ⚠ Nessuno dei due
    programmi era rotto da solo: il validatore faceva **esattamente** quel che
    la specifica gli chiede, e il registratore scriveva un formato che era
    stato valido fino a quattro giorni prima.  E' la forma d'errore che nasce
    fra due file, dove nessuna prova unitaria guarda.

    ⚠ **E il rosso non era muto: era illeggibile.**  «La traccia e' malformata»
      su un banco della stretta di mano manda a cercare un difetto del
    *registratore* — che infatti c'era — ma solo dopo aver escluso il server, la
    rete e il protocollo.  ⭐ Il banco che tiene chiusa questa porta e'
    `06-b38-registratore.py`, e non prova il filo: prova che i due banchi
    parlano la stessa lingua.

    ⭐⭐ **E DAL 21 AGOSTO 2026 LA MAGIA E' `0x00 0x03`: il blocco porta
       `istante_ms`.**

    §11.1 non registrava il **tempo**, e senza il tempo la regola del *«secondo
    di grazia dopo `TELA(ADATTATA)`»* di §7.1 non era collaudabile da nessun
    `.rcpreg` — era la `[?]` di `fasi/06-la-tela-e-la-vista.md` §7.2.

    ⛔ **E l'istante e' MONOTONO e RELATIVO al primo blocco, mai un'ora del
       mondo.**  §4.4 vieta i segreti nel file, e una data assoluta non e' un
    segreto per caso: dice **quando** e — insieme all'indirizzo che la
    registrazione gia' porta — **da dove** un utente si e' collegato.  Il primo
    blocco vale 0, e chi legge non impara niente su chi ha registrato.

    ⛔ **E il campo `orologio` nell'intestazione dice DI CHI sono i tempi**
       (1 = client, 2 = server), perche' la regola del secondo e' del **server**
    e una traccia presa al client misura un intervallo **piu' corto**: mezzo
    giro di rete per lato.  ⇒ Da qui l'arbitro conclude **in un verso solo**, e
    lo dichiara.  La riga sta in `01-b4-validatore.py`.
    """

    MAGIA = b"RCPREG\x00\x03"
    # ⛔ Le due magie di ieri si conservano QUI e non solo nell'arbitro: il
    #    banco che le rifiuta (`01-b4-registrazioni.py`) le scrive, e due
    #    elenchi di versioni in due file sono due elenchi che divergono.
    MAGIA_V1 = b"RCPREG\x00\x01"
    MAGIA_V2 = b"RCPREG\x00\x02"
    CONTINUA, FIN, RESET = 0, 1, 2
    OROLOGIO_CLIENT, OROLOGIO_SERVER = 1, 2

    def __init__(self):
        self.blocchi = []
        self.scritta = False
        # ⛔ Questo programma e' il CLIENT: i tempi sono i suoi, e lo dichiara.
        #    ⚠ Scrivere `2` qui vorrebbe dire far credere all'arbitro di avere
        #      l'orologio del server, e allora la conclusione «in un verso solo»
        #      diventerebbe una conclusione in due versi — sbagliata.
        self.orologio = self.OROLOGIO_CLIENT
        self.t0 = None
        # ⛔ Lo stream del canale di controllo, quello VERO.  §4.2: e' il primo
        #    stream bidirezionale della sessione, e ⚠ **non e' lo 0** — in
        #    HTTP/3 lo 0 e' gia' quello della CONNECT (rilievo R1.5).  Qui si
        #    scriveva `0` fisso: un numero che non e' mai stato quello, e che
        #    l'arbitro usa per P3 (§2.5, «un fotogramma sullo stream del canale
        #    di controllo»).
        self.stream = 0

    def istante(self):
        """⛔ Millisecondi dal PRIMO blocco, da un orologio monotono — §11.1.

        ⚠ `time.monotonic()` e non `time.time()`, e non e' pignoleria: un
          aggiustamento di NTP nel mezzo di una sessione farebbe **tornare
          indietro** gli istanti, e l'arbitro leggerebbe un `PUNTATORE`
          arrivato *prima* del `TELA` che lo precede sul filo.
        """
        adesso = time.monotonic()
        if self.t0 is None:
            self.t0 = adesso
        ms = int((adesso - self.t0) * 1000.0)
        # ⛔ Il campo e' u32: 49 giorni.  Si satura invece di avvolgersi, perche'
        #    un istante che riparte da zero e' peggio di un istante fermo.
        return min(ms, 0xFFFFFFFF)

    def aggiungi(self, verso, carico, oscurati=(), canale=0x00, stream=None,
                 fine=CONTINUA, istante=None):
        self.blocchi.append([verso, canale, fine,
                             self.stream if stream is None else stream,
                             carico, list(oscurati),
                             self.istante() if istante is None else istante])

    def segna_fine(self, verso, fine, stream=None):
        """⛔ Come si e' chiuso lo stream, e da QUALE lato — §11.1.

        ⭐ Non e' un dettaglio di formato: e' l'unico byte che permette
           all'arbitro di distinguere **«il server non ha risposto»** da **«la
        registrazione finisce qui»**.  §7.1 impone un `TELA` a ogni
        `ADATTA_TELA`, e senza questo campo una traccia che finisce con una
        richiesta in volo ha lo stesso aspetto nei due casi — la forma d'errore
        **E8**, e stavolta sulla regola con il sintomo peggiore:
        *«l'applicazione si e' piantata»*.

        ⚠ Se l'ultimo blocco e' gia' di quel verso lo si marca; altrimenti si
          aggiunge un blocco a carico **zero**, che e' il modo onesto di dire
          «da questo lato non e' arrivato altro, e poi si e' chiuso».
        """
        if self.blocchi and self.blocchi[-1][0] == verso:
            self.blocchi[-1][2] = fine
            return
        self.aggiungi(verso, b"", stream=stream, fine=fine)

    def scrivi(self, percorso):
        # ⛔ L'intestazione di §11.1: magia · u32 quanti_blocchi · u8 orologio ·
        #    3 byte riservati che DEVONO essere 0.
        out = bytearray(self.MAGIA + struct.pack("!IBBBB", len(self.blocchi),
                                                 self.orologio, 0, 0, 0))
        for verso, canale, fine, stream, carico, osc, ist in self.blocchi:
            out += struct.pack("!BBBIQIH", verso, canale, fine, ist, stream,
                               len(carico), len(osc))
            for ini, qua, imp in osc:
                out += struct.pack("!II", ini, qua) + imp
            out += carico
        with open(percorso, "wb") as f:
            f.write(bytes(out))


class Cliente(QuicConnectionProtocol):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = H3Connection(self._quic, enable_webtransport=True)
        self.accettata = asyncio.get_event_loop().create_future()
        self.sessione = None
        self.controllo = None
        self.arrivati = bytearray()
        self.messaggi = asyncio.Queue()
        self.finito = False
        # ⛔⛔ IL REGISTRATORE STA QUI, E NON NELLA CODA — 21 agosto 2026.
        #
        #    Fino a oggi ogni messaggio del server finiva nella traccia **nel
        #    momento in cui qualcuno lo tirava fuori dalla coda** (`attendi()`
        #    e `chiedi_tela()`).  ⇒ Un messaggio che arriva quando nessuno
        #    aspetta — cioe' durante `--resta`, che e' quasi tutta la vita di
        #    una sessione — NON entrava nella traccia affatto.
        #
        # ⛔ E le due regole che ci cadevano dentro sono proprio le due che
        #    §7.1 affida all'arbitro:
        #      · **T1** — un `TELA` NON SOLLECITATO;
        #      · **V3** — un `TELA` dopo una `VISTA`.
        #    L'arbitro le sa accusare (`01-b4-registrazioni.py` casi 22 e 30,
        #    `06-b38-mutazioni.py`), ma su registrazioni **costruite**: da una
        #    traccia di questo cliente non potevano uscire mai.  ⇒ Il giro 5 di
        #    `06-b38-tela.sh` — *«nessun TELA dopo la VISTA»* — era **verde per
        #    costruzione**, che `LEZIONI.md` dice essere peggio di nessun caso.
        #
        # ⭐ La cura e' di posto, non di logica: si registra dove i byte
        #    ARRIVANO (`_sfoglia`), non dove vengono consumati.  ⚠ E cosi'
        #    l'ordine dei blocchi e' quello del filo, che e' quel che §11.1
        #    chiede.  Trovato con `06-b40-lancia.sh`, casi 6 e 9.
        self.reg = None
        # ⛔ §3.1 punto 3: il motivo viaggia ANCHE nel codice d'errore
        #    applicativo con cui si chiude la sessione WebTransport.  Si
        #    conserva, perche' e' la seconda delle due strade — e il giorno in
        #    cui il `CONGEDO` non arriva e' l'unica.
        self.codice_chiusura = None
        # ⛔ CHE COSA E' CADUTO, E QUANDO — rilievi R8.2 e R8.4 del 10 agosto 2026.
        #
        #    B3 chiede due volte «la prima e' ancora attaccata?», e tutt'e due
        #    le volte lo leggeva dall'ESISTENZA DEL PROCESSO o dal suo codice
        #    d'uscita.  ⚠ Ma questo programma, dopo SESSIONE, dormiva e basta:
        #    la connessione poteva morire per il tetto d'inattivita' di QUIC, o
        #    la sessione poteva essere chiusa dal server, e il processo restava
        #    vivo e usciva 0 lo stesso.  Il banco leggeva «viva» da un fatto che
        #    non aveva osservato (E7: si verifica dal lato che invia).
        #
        # ⭐ Qui si osserva dal lato che riceve: chi cade lo dice, con il nome
        #    di CHE COSA e' caduto — e i due casi non si confondono, perche'
        #    «QUIC ha chiuso da se'» e «il server ha chiuso la sessione» sono i
        #    due imputati che il quarto giro esiste per separare.
        self.caduta = None
        # ═══ L'AUDIO — fase 7 ═════════════════════════════════════════════
        # ⛔ I contatori sono SEI e non uno, e ognuno nomina una regola diversa
        #    di §6.3: chi li sommasse otterrebbe un numero che non dice mai
        #    dove guardare (`LEZIONI.md` §2.2).
        self.a_ricevuti = 0      # datagram arrivati e conformi
        self.a_corti = 0         # < 12 byte: §6.3 li fa scartare
        self.a_tipo = 0          # `tipo` != 0x0401
        self.a_prefisso = 0      # il prefisso RFC 9297 non e' la nostra sessione
        self.a_vecchi = 0        # `istante` non piu' recente: §6.3
        self.a_codec = None      # il codec dichiarato nei datagram
        self.a_byte = 0
        self.a_ultimo_istante = None
        # I blocchi come sono arrivati, per il giudice di `07-b42`.
        self.a_blocchi = []
        self.caduto = asyncio.Event()
        # ⛔ E LA TERZA CAUSA: CHE LA CONNESSIONE L'ABBIAMO CHIUSA NOI.
        #
        #    `[M]` 10 agosto 2026, terzo giro: la finestra di `--resta` scade,
        #    questo programma esce 0, e `connect()` chiude la connessione
        #    uscendo dal suo contesto — aioquic alza `ConnectionTerminated`
        #    codice 0 senza motivo, e la riga qui sotto finiva nel registro
        #    IDENTICA a quella di un server che ti spodesta.  Il banco la
        #    trovava con un grep sull'intero file e dava il rosso al server,
        #    che aveva appena tenuto viva la sessione con i PING per 25 s.
        #
        # ⭐ «Terminata da noi» e «terminata da qualcun altro» sono due fatti
        #    diversi e adesso hanno due righe diverse (CODER.md §3.9, §4.2).
        self.chiusa_da_noi = False
        # ═══ GLI APPUNTI — fase 7, §7.4 ═══════════════════════════════════
        # ⛔ QUESTO CLIENTE E' IL SECONDO LETTORE DI `RCP.md` (`PIANO.md` §1.1),
        #    e i tre messaggi di §7.4 entrano qui perche' altrimenti il filo
        #    degli appunti sarebbe validato da UNA SOLA implementazione — la
        #    pagina, scritta dalla stessa mano del server.
        #
        # ⚠ Il montaggio e' PER STREAM, non uno solo: §2.5 dice «uno stream per
        #   trasferimento», quindi ce n'e' piu' d'uno vivo insieme.  ⛔ Con un
        #   accumulo unico due trasferimenti intrecciati si mescolerebbero, ed e'
        #   esattamente il difetto che l'identificatore di §7.4 esiste per
        #   togliere — trovarlo qui vorrebbe dire non trovarlo mai.
        self.app_in = {}          # stream_id -> bytearray, il montaggio
        self.app_mio_id = 0       # §7.4: ciascun lato numera i PROPRI, da 1
        self.app_mio_testo = ""
        self.app_suo_id = 0       # l'ultimo annuncio del server
        self.app_suo_len = 0
        self.app_ricevuto = None  # l'ultimo testo che il server ci ha mandato
        self.app_annunci = []     # [(id, byte)] tutti gli annunci del server
        self.app_chiesti = []     # [id] i trasferimenti che il server ci ha chiesto
        self.app_serviti = 0
        self.app_violazioni = []  # quel che NON torna con §7.4, con il nome
        self.app_evento = asyncio.Event()
        # Il preambolo degli stream unidirezionali del server, per stream:
        # `0x40 0x54` piu' il varint della sessione.  `None` = non e' nostro.
        self.uni_pref = {}
        self.uni_genere = {}
        # ═══ IL VIDEO PRESO DAL FILO — fase 3/7, 17 agosto 2026 ═══════════
        # ⛔ NON per dipingerlo: per SEPARARE il nostro flusso dal
        #    decodificatore del browser.  «Gli artefatti sono nostri» e «sono
        #    suoi» hanno la stessa faccia guardando lo schermo, e si dividono in
        #    un modo solo — dando gli STESSI BYTE a un terzo decodificatore che
        #    non e' nessuno dei due (`ffmpeg`/`dav1d`).
        # ⚠ E i byte sono quelli del FILO, non quelli del rilievo: fra il
        #   codificatore e il browser c'e' tutto il trasporto, e un difetto li'
        #   in mezzo il rilievo non lo vedrebbe.
        self.v_in = {}          # stream_id -> bytearray in montaggio
        # ⛔ Gli stream gia' registrati: l'intestazione di §6.2 si scrive UNA
        #    volta per stream, o una tela sola comparirebbe dieci volte e il
        #    denominatore di T4 conterebbe fotogrammi che non ci sono.
        self.v_reg = set()
        self.v_fotogrammi = []  # [(numero, chiave, larghezza, altezza, dati)]
        # ═══ IL CANALE DI INPUT — §2.5, §7.3, e il 22 agosto 2026 ═════════
        # ⛔ `RCP.md` §2.5: «**uno solo**, aperto dopo aver ricevuto `SESSIONE`
        #    e tenuto aperto».  ⚠ NON e' come gli appunti, dove ogni
        #    trasferimento ha il suo stream: qui uno stream per messaggio
        #    sarebbe **un altro protocollo**, e il server che conta gli `id`
        #    «su tutto il canale» (§7.3) non avrebbe piu' un canale su cui
        #    contarli.
        self.inp_stream = None
        # §7.3: «crescente, comincia da 1.  ⛔ 0 e' riservato».
        self.inp_id = 0
        # ⭐ L'ISTANTE **REGISTRATO** DELL'ULTIMO `TELA`, e non l'ora di
        #    adesso: il secondo di grazia lo arbitra §11.1 su `istante_ms`, e
        #    un ritardo contato su un orologio diverso da quello che finisce
        #    nel file darebbe un `dt` che non e' quello che l'arbitro legge.
        self.ultimo_tela_ms = None

    def _cade(self, perche: str) -> None:
        """La prima causa vince: le successive sono conseguenze, non cause."""
        if self.caduta is None:
            self.caduta = perche
            self.caduto.set()

    def apri_sessione(self, autorita, percorso):
        sid = self._quic.get_next_available_stream_id(is_unidirectional=False)
        self.sessione = sid
        self._http.send_headers(sid, [
            (b":method", b"CONNECT"), (b":protocol", b"webtransport"),
            (b":scheme", b"https"), (b":authority", autorita.encode()),
            (b":path", percorso.encode()),
            (b"origin", f"https://{autorita}".encode()),
        ])
        self.transmit()

    def apri_controllo(self):
        # ⛔ RCP.md §4.2: il canale di controllo e' il PRIMO stream
        #    bidirezionale della sessione.  ⚠ E NON e' «lo stream 0»: in
        #    HTTP/3 lo 0 e' gia' quello della CONNECT che stabilisce la
        #    sessione, e l'API non espone nessun numero (rilievo R1.5).
        self.controllo = self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=False)
        return self.controllo

    def manda(self, dati):
        self._quic.send_stream_data(self.controllo, dati, end_stream=False)
        self.transmit()

    # ══════════════════════════════════════════════════════════════════════
    # L'INPUT — §7.3, e il canale unico di §2.5
    # ══════════════════════════════════════════════════════════════════════

    def apri_input(self):
        """Lo stream del canale di input: **uno solo**, e si tiene aperto.

        ⛔ Si apre alla prima volta che serve, e non ad ogni messaggio: §2.5
           dice «uno solo … e tenuto aperto», e §7.3 conta gli `id` «su tutto
           il canale».  ⚠ Aprirlo e non chiuderlo non e' una svista: chiuderlo
           con FIN direbbe al server «il client non manda piu' input», che e'
           un'altra cosa da quella che questo banco vuole dire.
        """
        if self.inp_stream is None:
            self.inp_stream = self._http.create_webtransport_stream(
                self.sessione, is_unidirectional=True)
        return self.inp_stream

    def manda_puntatore(self, x, y):
        """⭐ `PUNTATORE(x, y)` — §7.3, coordinate sulla **tela**.

        ⛔ E si registra col canale `0x01` e con lo stream VERO: §11.1
           definisce il campo `canale` come «il byte alto di `tipo`», e
           l'arbitro **rifiuta** un blocco in cui i due non tornano — una
           registrazione che dichiarasse `0x00` farebbe leggere questi byte
           come se fossero controllo, e la regola del secondo non uscirebbe
           mai da questa traccia.
        """
        sid = self.apri_input()
        self.inp_id += 1
        # ⛔ §7.3: «microsecondi dell'orologio monotono del CLIENT», e «il
        #    client scrive microsecondi VERI e NON DEVE far credere a una
        #    precisione che non ha» (rilievo R1.27).  ⚠ Qui la grana e' quella
        #    di `time.monotonic()` di CPython — nanosecondi sul kernel Linux —
        #    quindi non si moltiplica niente per mille.
        ist_us = int(time.monotonic() * 1_000_000)
        b = inquadra(T_PUNTATORE,
                     struct.pack("!IQII", self.inp_id, ist_us, x, y))
        self._quic.send_stream_data(sid, b, end_stream=False)
        self.transmit()
        ms = None
        if self.reg is not None:
            self.reg.aggiungi(CLIENT, b, canale=0x01, stream=sid)
            ms = self.reg.blocchi[-1][6]
        return self.inp_id, ms

    # ══════════════════════════════════════════════════════════════════════
    # GLI APPUNTI — §7.4, e i tre messaggi letti da `RCP.md` e non dal C
    # ══════════════════════════════════════════════════════════════════════

    def appunti_manda(self, tipo, corpo):
        """Un messaggio del canale appunti, sul suo stream unidirezionale.

        ⛔ Uno stream per messaggio, e si chiude con FIN.  §2.5 dice «uno per
           trasferimento» e questo cliente ha scelto la lettura piu' stretta —
           la stessa del server — perche' a legare i messaggi di un
           trasferimento e' il campo `trasferimento` (§7.4), non lo stream.
           ⚠ Se le due implementazioni avessero letto §2.5 in modo diverso, il
             filo funzionerebbe lo stesso: e' la prova che la riga e' ambigua e
             che l'ambiguita' non morde.  Va scritta nel documento di fase.
        """
        sid = self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=True)
        self._quic.send_stream_data(sid, inquadra(tipo, corpo), end_stream=True)
        self.transmit()
        return sid

    def appunti_annuncia(self, testo):
        """«Ho del testo nuovo» — §7.4, `APPUNTI_ANNUNCIO`."""
        d = testo.encode("utf-8")
        self.app_mio_id = 1 if self.app_mio_id >= 0xFFFFFFFF else self.app_mio_id + 1
        self.app_mio_testo = testo
        self.appunti_manda(0x0201, struct.pack("!II", self.app_mio_id, len(d)))
        print(f"   [app]  annunciato il trasferimento {self.app_mio_id}, "
              f"{len(d)} byte")
        return self.app_mio_id

    def appunti_chiedi(self, trasferimento=None):
        """«Mandamelo» — §7.4, `APPUNTI_CHIEDI`."""
        t = self.app_suo_id if trasferimento is None else trasferimento
        self.appunti_manda(0x0202, struct.pack("!I", t))
        print(f"   [app]  chiesto il trasferimento {t}")
        return t

    def _appunti_uno(self, tipo, corpo):
        """Un messaggio intero del canale appunti, gia' srotolato da §6.1."""
        if tipo == 0x0201:                                   # ANNUNCIO
            if len(corpo) != 8:
                self.app_violazioni.append(
                    f"APPUNTI_ANNUNCIO con {len(corpo)} byte: §7.4 ne vuole 8")
                return
            t, n = struct.unpack("!II", corpo)
            self.app_suo_id, self.app_suo_len = t, n
            self.app_annunci.append((t, n))
            print(f"   [app]  ⭐ il server annuncia il trasferimento {t}, {n} byte")
            self.app_evento.set()
            return
        if tipo == 0x0202:                                   # CHIEDI
            if len(corpo) != 4:
                self.app_violazioni.append(
                    f"APPUNTI_CHIEDI con {len(corpo)} byte: §7.4 ne vuole 4")
                return
            (t,) = struct.unpack("!I", corpo)
            self.app_chiesti.append(t)
            print(f"   [app]  ⭐ il server chiede il trasferimento {t}")
            # ⛔ §7.4: «un identificatore che non corrisponde a nessun annuncio
            #    vivo e' ERRORE_PROTOCOLLO».  ⚠ Qui NON si chiude la sessione:
            #    questo e' un banco, e il suo mestiere e' REGISTRARE che il
            #    server ha sbagliato, non punirlo — se chiudesse, il giro
            #    finirebbe e nessuno leggerebbe piu' niente.
            if t == 0 or t > self.app_mio_id:
                self.app_violazioni.append(
                    f"APPUNTI_CHIEDI per il trasferimento {t}, e io ne ho "
                    f"annunciati {self.app_mio_id} (§7.4)")
                return
            d = self.app_mio_testo.encode("utf-8")
            self.appunti_manda(0x0203, struct.pack("!I", t) + d)
            self.app_serviti += 1
            print(f"   [app]  serviti {len(d)} byte al server (trasferimento {t})")
            self.app_evento.set()
            return
        if tipo == 0x0203:                                   # TESTO
            if len(corpo) < 4:
                self.app_violazioni.append(
                    f"APPUNTI_TESTO con {len(corpo)} byte: §7.4 ne vuole >= 4")
                return
            (t,) = struct.unpack("!I", corpo[:4])
            d = corpo[4:]
            if t != self.app_suo_id:
                self.app_violazioni.append(
                    f"APPUNTI_TESTO per il trasferimento {t}, e l'annuncio vivo "
                    f"e' il {self.app_suo_id} (§7.4)")
            if len(d) != self.app_suo_len:
                self.app_violazioni.append(
                    f"APPUNTI_TESTO porta {len(d)} byte e l'annuncio ne "
                    f"dichiarava {self.app_suo_len} (§7.4)")
            # ⛔ §5.4: «il testo DEVE essere UTF-8».  Si decodifica STRETTO: un
            #    decodificatore indulgente metterebbe caratteri di sostituzione
            #    al posto di un errore, e il banco direbbe verde su un testo che
            #    non e' quello che era stato copiato.
            try:
                self.app_ricevuto = d.decode("utf-8")
            except UnicodeDecodeError as e:
                self.app_violazioni.append(f"APPUNTI_TESTO non e' UTF-8: {e}")
                self.app_ricevuto = None
            print(f"   [app]  ⭐ arrivati {len(d)} byte dal server "
                  f"(trasferimento {t})")
            self.app_evento.set()
            return
        self.app_violazioni.append(
            f"tipo {tipo:#06x} sul canale appunti: §7.4 ne definisce TRE")

    def _decidi_canale(self, sid, carico, fine):
        """Il byte alto del `tipo` dice il canale (§2.5), e adesso c'e'."""
        self.uni_pref.pop(sid, None)
        if carico[0] == 0x02:
            self.uni_genere[sid] = "wt"
            self._appunti_stream(sid, carico, fine)
        elif carico[0] == 0x03:
            self.uni_genere[sid] = "video"
            self._video_stream(sid, carico, fine)
        else:
            # ⚠ Un canale che questo cliente non serve: lo DICE invece di
            #   tacere — «ricevuto e non usato» e «mai arrivato» non devono
            #   avere la stessa faccia.
            self.uni_genere[sid] = "altro"
            print(f"   [wt]   ⚠ stream uni {sid}, canale 0x{carico[0]:02x}: "
                  f"lecito e non servito da questo cliente (§2.5)")

    def _video_stream(self, sid, dati, fine):
        """Uno stream del canale VIDEO (§6.2): uno stream, un fotogramma.

        ⛔ E la fine dello stream E' la fine del fotogramma — ma **solo con un
           FIN**: uno stream azzerato porta un fotogramma incompleto, che §6.2
           impone di BUTTARE e non di consegnare al decodificatore.
        ⚠ Qui `aioquic` non distingue i due casi su questo cammino, quindi si
          registra quel che si e' visto e si dichiara: chi legge il file sa che
          i fotogrammi sono quelli finiti con FIN.
        """
        b = self.v_in.setdefault(sid, bytearray())
        b += dati
        # ⛔⛔ E DAL 21 AGOSTO 2026 I 28 BYTE DI §6.2 FINISCONO NELLA TRACCIA.
        #
        #    Fino a stamattina la registrazione portava **solo il canale di
        #    controllo**, e su una traccia senza video l'arbitro non puo'
        #    concludere niente su **T4** — *«un server che risponde
        #    `TELA(ADATTATA)` senza toccare il palco»*, che e' la crepa
        #    dichiarata di tutta la 6.6.  ⚠ `[M]` il primo giro vero contro il
        #    prodotto, 21 agosto: cinque tracce, e su tutte l'arbitro ha
        #    scritto *«dopo di lui la registrazione non porta NESSUN
        #    fotogramma: NON si giudica»*.  Una regola che non ha mai un
        #    ingresso e' una regola che non c'e'.
        #
        # ⛔⛔ E SI REGISTRA IL FLUSSO **INTERO**, non i soli 28 byte —
        #     e la prima stesura faceva l'altra cosa, per un'ora.
        #
        #  Sembrava furba: l'arbitro giudica misura, numero e codec, che stanno
        #  tutti nell'intestazione, e i pixel sono megabyte che nessuno legge.
        #  ⛔ **Ma un blocco di 28 byte marcato `fine = 0` dice all'arbitro una
        #  cosa falsa**: dice «di questo stream ho registrato tutto quel che e'
        #  passato, e non era finito».  ⇒ Il giudice del fotogramma non ha mai
        #  consumato quei flussi, e il fotogramma dopo — un delta legittimo —
        #  gli e' arrivato come **il primo della sessione**.
        #
        #  `[M]` 21 agosto 2026, giro vero sulla 7721: *«flusso 23: il primo
        #  fotogramma della sessione e' un DELTA — §5.2»*.  ⛔ **Un'accusa al
        #  PRODOTTO nata da una registrazione mia incompleta**, ed e' la cosa
        #  peggiore che un banco possa fare: §11.1 vuole i byte, e una traccia
        #  che ne porta un pezzo dichiarandosi intera non e' piu' un arbitro.
        #
        # ⚠ Il prezzo e' la misura del file, e si paga: chi vuole tracce
        #   piccole accorcia `--resta`, non il filo.
        if self.reg is not None:
            self.v_reg.add(sid)
            self.reg.aggiungi(SERVER, bytes(dati), canale=0x03, stream=sid,
                              fine=Registratore.FIN if fine
                              else Registratore.CONTINUA)
        if not fine:
            return
        del self.v_in[sid]
        if len(b) < 28:
            print(f"   [vid]  ⛔ stream {sid} finito con {len(b)} byte: §6.2 "
                  f"vuole 28 di intestazione")
            return
        tipo, codec, l, a, numero, istante, inp = struct.unpack("!HHIIIQI", bytes(b[:28]))
        self.v_fotogrammi.append((numero, tipo == 0x0301, l, a, bytes(b[28:])))

    def _appunti_stream(self, sid, dati, fine):
        """I byte di uno stream unidirezionale del SERVER, canale appunti.

        ⛔ Il preambolo di WebTransport si consuma qui: `0x40 0x54` piu' il
           varint della sessione.  ⚠ E si tiene per stream, perche' un
           pacchetto puo' tagliarlo in mezzo.
        """
        b = self.app_in.setdefault(sid, bytearray())
        b += dati
        while True:
            if len(b) < 6:
                break
            tipo, lung = struct.unpack("!HI", b[:6])
            if len(b) < 6 + lung:
                break
            corpo = bytes(b[6:6 + lung])
            del b[:6 + lung]
            self._appunti_uno(tipo, corpo)
        if fine:
            if b:
                self.app_violazioni.append(
                    f"lo stream di appunti {sid} e' finito con {len(b)} byte "
                    "che non fanno un messaggio (§6.1)")
            self.app_in.pop(sid, None)

    def _audio_datagram(self, d: bytes) -> None:
        """Un datagram di WebTransport: prefisso RFC 9297, poi §6.3.

        ⛔ Ogni scarto ha un contatore SUO.  «Non ho sentito niente» deve poter
           dire *perche'*: il prefisso sbagliato, il tipo sbagliato, il blocco
           corto e il blocco vecchio sono quattro difetti diversi con lo stesso
           sintomo, e senza quattro contatori si cerca per ore dalla parte
           sbagliata.
        """
        # Il prefisso: il quarto dell'identificativo dello stream della sessione.
        q, i = _varint(d, 0)
        if q is None:
            self.a_prefisso += 1
            return
        if self.sessione is not None and q != self.sessione // 4:
            # ⛔ Non e' un dettaglio di involucro: un prefisso sbagliato fa
            #    scartare il datagram AL BROWSER, senza un errore da nessuna
            #    parte — cioe' «l'audio non arriva» e basta.
            self.a_prefisso += 1
            return
        c = d[i:]
        if len(c) < 12:
            self.a_corti += 1
            return
        tipo = int.from_bytes(c[0:2], "big")
        if tipo != 0x0401:
            self.a_tipo += 1
            return
        codec = int.from_bytes(c[2:4], "big")
        istante = int.from_bytes(c[4:12], "big")
        # §6.3: «chi riceve scarta i datagram arrivati in ritardo rispetto a
        # quelli gia' consumati».
        if self.a_ultimo_istante is not None and istante <= self.a_ultimo_istante:
            self.a_vecchi += 1
            return
        self.a_ultimo_istante = istante
        self.a_ricevuti += 1
        self.a_byte += len(c) - 12
        if self.a_codec is None:
            self.a_codec = codec
            print(f"   [audio] ⭐ primo datagram: codec {codec} "
                  f"({'Opus' if codec == 1 else 'PCM' if codec == 2 else '⛔ ignoto'}), "
                  f"{len(c) - 12} byte di carico, prefisso {q} "
                  f"(sessione {self.sessione})")
        elif self.a_codec != codec:
            # ⚠ Il codec non cambia a meta' sessione: §4.3 lo negozia una volta.
            print(f"   [audio] ⛔ il codec e' CAMBIATO: {self.a_codec} → {codec}")
            self.a_codec = codec
        self.a_blocchi.append({"istante": istante, "codec": codec,
                               "byte": bytes(c[12:])})

    def quic_event_received(self, event: QuicEvent) -> None:
        nome = type(event).__name__
        # ═══ L'AUDIO — fase 7, `RCP.md` §6.3 ══════════════════════════════
        #
        # ⛔ Il datagram si legge QUI, prima di ogni altra cosa, e NON si passa
        #    allo strato H3 di aioquic: e' un datagram di WebTransport, non di
        #    HTTP/3 puro, e il suo primo campo e' il prefisso di RFC 9297.
        #
        # ⚠ E quel che questo lettore fa di piu' del browser e' il MOTIVO per
        #   cui esiste (`PIANO.md` §1.1): il browser dice «non sento niente»;
        #   questo dice QUALE regola di §6.3 e' stata violata e a quale byte.
        if nome == "DatagramFrameReceived":
            self._audio_datagram(event.data)
            return
        # ⛔ LA FINE DELLA CONNESSIONE SI STAMPA, SEMPRE.
        #
        #    E' l'unica riga che distingue «il tetto d'inattivita' di QUIC ha
        #    chiuso» da «il server ha liberato il posto lasciando aperta la
        #    connessione».  Senza, il quarto giro di B3 concludeva la seconda
        #    guardando /proc, che dice soltanto che un processo che dorme non
        #    e' morto (R8.2).
        if nome == "ConnectionTerminated":
            da_noi = " — CHIUSA DA NOI, a finestra finita" if self.chiusa_da_noi else ""
            print(f"   [quic] connessione TERMINATA: codice "
                  f"{getattr(event, 'error_code', '?')} · "
                  f"{getattr(event, 'reason_phrase', '') or '(nessun motivo)'}"
                  f"{da_noi}")
            self._cade(f"connessione TERMINATA ({getattr(event, 'reason_phrase', '') or 'senza motivo'})")
            self.messaggi.put_nowait(None)
            return
        if nome == "StreamDataReceived" and event.stream_id == self.controllo:
            self.arrivati += event.data
            self._sfoglia()
            if event.end_stream:
                self.finito = True
                self._cade("il canale di controllo si e' chiuso")
                self.messaggi.put_nowait(None)
            # ⛔ E NON si passa l'evento allo strato H3 di `aioquic`.
            #
            #    `[M]` 10 agosto 2026: passandoglielo, la prima stretta di mano
            #    e' morta con `CONNECTION_CLOSE 0x105 — DATA frame is not
            #    allowed in this state`, cioe' il CLIENTE che uccide la
            #    connessione mentre il server lavorava bene.
            #
            # ⚠ E' l'asimmetria gia' vista il 9 agosto: `aioquic` 1.2 sa
            #   CREARE uno stream WebTransport e non sa RICONOSCERLO quando
            #   risponde — quindi il suo strato HTTP/3 legge `ECCOMI` come un
            #   frame DATA su uno stream di richiesta.  Il banco di B2 non se
            #   n'era accorto perche' l'eco erano quattro byte; centosedici
            #   bastano a far cadere tutto.
            return
        # ⛔⭐ GLI STREAM UNIDIREZIONALI DEL SERVER — §2.5, e da qui passano il
        #     video (0x03) e gli appunti (0x02).  ⚠ Non tutti sono nostri: fra
        #     gli unidirezionali del server ci sono il canale di controllo di
        #     HTTP/3 e i due di QPACK, che sono di `aioquic`.  Uno stream
        #     WebTransport si riconosce dal suo tipo, `0x54` — che come `0x41`
        #     non sta in un byte: sul filo sono `0x40 0x54`.
        # ⛔⭐ GLI STREAM UNIDIREZIONALI DEL SERVER — §2.5: di qui passano il
        #     video (0x03) e gli appunti (0x02).  ⚠ Non tutti sono nostri: fra
        #     gli unidirezionali del server ci sono il canale di controllo di
        #     HTTP/3 e i due di QPACK, che sono di `aioquic`.
        #
        # ⛔⛔ E SI DECIDE SOLO QUANDO C'E' DA DECIDERE — tre volte in una sera
        #      il difetto e' stato lo stesso, e vale la pena scriverlo una volta
        #      per tutte: **classificare su byte che non sono ancora arrivati**.
        #
        #      1. si aspettavano DUE byte per riconoscere il preambolo, e gli
        #         stream QPACK ne portano UNO ⇒ inghiottiti, e il server ci
        #         congedava per `TEMPO_SCADUTO`;
        #      2. il giudizio «altro» non aveva un ramo suo ⇒ i byte del video
        #         finivano nello strato HTTP/3;
        #      3. `[M]` **il primo pacchetto di uno stream video porta il solo
        #         preambolo — `40 54 00`, tre byte, carico ZERO** ⇒ si decideva
        #         «non e' ne' appunti ne' video» su uno stream che era video, e
        #         si buttava tutto il resto.
        #
        # ⇒ La regola: finche' il byte che decide non e' arrivato, lo stato e'
        #   «lo so che e' nostro e non so ancora che cos'e'» — che e' uno stato
        #   VERO, non un giudizio.  ⛔ `LEZIONI.md` §1.9: «non lo so» e «non lo
        #   e'» non devono avere la stessa faccia.
        if nome == "StreamDataReceived" and (event.stream_id & 0x03) == 0x03:
            sid = event.stream_id
            if os.environ.get("B3_SPIA"):
                print(f"   [spia] uni {sid} genere={self.uni_genere.get(sid)} "
                      f"len={len(event.data)} fin={event.end_stream} "
                      f"primi={bytes(event.data[:6]).hex()}")
            g = self.uni_genere.get(sid)
            if g == "h3":
                pass                       # e' di `aioquic`: gli si lascia
            elif g == "wt":
                self._appunti_stream(sid, event.data, event.end_stream)
                return
            elif g == "video":
                self._video_stream(sid, event.data, event.end_stream)
                return
            elif g == "altro":
                return                     # nostro, e questo cliente non lo serve
            elif g == "wt-attesa":
                # Il preambolo c'e' gia': manca il byte che dice il canale.
                p = self.uni_pref.setdefault(sid, bytearray())
                p += event.data
                if p:
                    self._decidi_canale(sid, bytes(p), event.end_stream)
                return
            else:
                # ⛔ Si decide sul PRIMO byte: uno stream WebTransport comincia
                #    per `0x40` (il varint del tipo 0x54 non sta in un byte);
                #    qualunque altro primo byte e' di `aioquic`, e i suoi byte
                #    non devono passare di qui nemmeno per un giro.
                if not event.data:
                    return
                if event.data[0] != 0x40:
                    self.uni_genere[sid] = "h3"
                else:
                    p = self.uni_pref.setdefault(sid, bytearray())
                    p += event.data
                    if len(p) < 2:
                        return
                    if p[1] != 0x54:
                        self.uni_genere[sid] = "altro"
                        self.uni_pref.pop(sid, None)
                        print(f"   [wt]   ⚠ stream uni {sid} comincia per 0x40 "
                              f"0x{p[1]:02x}: non e' WebTransport, e i suoi byte "
                              f"sono stati trattenuti")
                        return
                    q, i = _varint(bytes(p), 2)
                    if q is None:
                        return         # il varint della sessione non e' tutto qui
                    resto = bytes(p[i:])
                    self.uni_genere[sid] = "wt-attesa"
                    self.uni_pref[sid] = bytearray(resto)
                    if resto:
                        self._decidi_canale(sid, resto, event.end_stream)
                    return
        if nome == "StreamDataReceived" and event.stream_id == self.sessione:
            # la capsula di chiusura della sessione (§3.1 punto 3)
            codice, nuda = _capsula_chiusura(event.data)
            if codice is not None:
                if nuda:
                    # ⛔ La capsula NUDA, senza il frame DATA che la porta.
                    #
                    #    E' quel che questo server faceva fino al 10 agosto 2026
                    #    (rilievo R10.1): sul filo della CONNECT le capsule
                    #    viaggiano DENTRO i frame DATA (RFC 9297), e un browser
                    #    che legge `0x2843` come tipo di frame HTTP/3 lo trova
                    #    sconosciuto e lo **ignora** (RFC 9114 §9).  Il motivo
                    #    non arrivava, e restava solo il FIN — cioe' `codice 0`.
                    #
                    # ⭐ Il banco lo legge lo stesso, ma lo DICHIARA: un cliente
                    #    indulgente che accettasse le due forme senza dire
                    #    quale ha visto nasconderebbe di nuovo quel difetto, ed
                    #    e' l'indulgenza che `REVIEWER.md` §5 vieta.
                    print("   [wt]   ⛔ capsula di chiusura NUDA, senza frame "
                          "DATA: un browser la ignorerebbe (RFC 9297)")
                self.codice_chiusura = codice
                print(f"   [wt]   sessione chiusa dal server, codice {codice:#04x}"
                      f" = {MOTIVI.get(codice, '?')}")
                self._cade(f"sessione chiusa dal server, codice {codice:#04x}"
                           f" = {MOTIVI.get(codice, '?')}")
            if event.end_stream:
                self.finito = True
                self._cade("la sessione WebTransport si e' chiusa")
                self.messaggi.put_nowait(None)
        for ev in self._http.handle_event(event):
            if isinstance(ev, HeadersReceived) and not self.accettata.done():
                self.accettata.set_result(
                    dict(ev.headers).get(b":status", b"?").decode())

    def _sfoglia(self):
        while len(self.arrivati) >= 6:
            tipo, lung = struct.unpack("!HI", self.arrivati[:6])
            if len(self.arrivati) < 6 + lung:
                return
            corpo = bytes(self.arrivati[6:6 + lung])
            grezzo = bytes(self.arrivati[:6 + lung])
            del self.arrivati[:6 + lung]
            # ⛔ SI REGISTRA QUI, all'arrivo: vedi il riquadro su `self.reg`.
            if self.reg is not None:
                self.reg.aggiungi(SERVER, grezzo)
                # ⭐ L'istante che l'arbitro leggera' nel file, preso dove il
                #    file lo prende.  ⛔ Non `time.monotonic()` di adesso: il
                #    `dt` del secondo di grazia si conta fra DUE `istante_ms`
                #    di §11.1, e contarlo su un orologio diverso vorrebbe dire
                #    che il ritardo dichiarato dal banco e quello letto
                #    dall'arbitro sono due numeri diversi — cioe' esattamente
                #    l'errore che il confine del secondo non perdona.
                if NOME.get(tipo) == "TELA":
                    self.ultimo_tela_ms = self.reg.blocchi[-1][6]
                if NOME.get(tipo) in ("TELA", "CURSORE_FORMA") \
                        and self.messaggi.qsize() > 0:
                    # ⚠ «E' arrivato mentre ce n'erano gia' altri in coda» non
                    #   e' una violazione: e' un fatto, e chi guarda deve
                    #   poterlo leggere senza aprire la traccia.
                    print(f"   ·  [filo] {NOME.get(tipo)} arrivato con "
                          f"{self.messaggi.qsize()} messaggi gia' in coda")
            self.messaggi.put_nowait((tipo, corpo, grezzo))


async def attendi(cli, quale, attesa=10.0, reg=None):
    m = await asyncio.wait_for(cli.messaggi.get(), timeout=attesa)
    if m is None:
        raise RuntimeError(f"il canale di controllo si e' chiuso: {cli.caduta}")
    tipo, corpo, grezzo = m
    nome = NOME.get(tipo, f"{tipo:#06x}")
    # ⛔ SI REGISTRA QUEL CHE ARRIVA, NON QUEL CHE SI SPERAVA — rilievo R8.9.
    #
    #    La registrazione si scriveva solo lungo la strada che riesce: un
    #    `CONGEDO(GIA_ATTIVA_REMOTA)` faceva sollevare l'eccezione qui sotto
    #    PRIMA di essere messo nella traccia, e `b3-terza.rcpreg` — cioe'
    #    l'unico oggetto che il terzo giro esiste per produrre — non arrivava
    #    mai all'arbitro di B4.  ⭐ Il rifiuto e' una misura, non un incidente.
    #    ⭐ E dal 21 agosto 2026 la riga `reg.aggiungi()` NON e' piu' qui: si
    #       registra all'ARRIVO, dentro `Cliente._sfoglia()`, o i messaggi che
    #       nessuno aspetta non entrano nella traccia (riquadro in `__init__`).
    #       ⚠ `reg` resta nella firma perche' i chiamanti lo passano, e
    #         toglierlo sarebbe una modifica piu' larga di quel che serve.
    if quale and nome != quale:
        if nome == "CONGEDO":
            motivo = corpo[0] if corpo else 0
            raise RuntimeError(
                f"CONGEDO invece di {quale}: motivo {motivo:#04x} = "
                f"{MOTIVI.get(motivo, '?')}")
        if nome == "RESPINTO":
            motivo = corpo[0] if corpo else 0
            raise RuntimeError(
                f"RESPINTO: motivo {motivo:#04x} = {MOTIVI.get(motivo, '?')}")
        raise RuntimeError(f"atteso {quale}, arrivato {nome}")
    return nome, corpo, grezzo


async def chiedi_tela(cli, reg, lar, alt, tetto):
    """⭐ `ADATTA_TELA(lar, alt)` e l'attesa del `TELA` — RCP.md §7.1.

    Restituisce `(esito, motivo, tela_lar, tela_alt, ms)`, oppure `None` se il
    tetto scade **senza nessuna risposta**.

    ⛔⛔ IL TETTO E' LA MISURA, NON UNA COMODITA'.

    §7.1: *«A ogni `ADATTA_TELA` il server DEVE rispondere con un `TELA`,
    riuscito o no.  Un silenzio lascia il client ad aspettare per sempre una
    risposta che non arrivera', e il sintomo e' "l'applicazione si e'
    piantata"»*.  ⇒ Un cliente di prova che aspettasse **senza tetto**
    riprodurrebbe il sintomo invece di misurarlo: il banco resterebbe appeso, e
    chi guarda direbbe «il banco si e' piantato» — che e' la stessa frase, dal
    lato sbagliato.

    ⚠ E il tetto NON e' una regola del protocollo: §7.1 non dice **entro
      quanto**.  ⛔ Quindi la scadenza non si registra come violazione dal
      cliente: si registra il **silenzio**, e a giudicarlo e' l'arbitro, che
      legge i byte e il campo `fine` di §11.1.  Il cliente misura; il verdetto
      e' di `01-b4-validatore.py`.

    ⚠ E si registra quel che arriva NEL FRATTEMPO — `CURSORE_FORMA` e i
      fotogrammi arrivano quando vogliono — perche' una traccia con dei buchi
      non e' giudicabile: §11.1 vuole i byte, non quelli che aspettavamo.
    """
    b = inquadra(T["ADATTA_TELA"], struct.pack("!II", lar, alt))
    cli.manda(b)
    reg.aggiungi(CLIENT, b)
    print(f"   → ADATTA_TELA {lar}x{alt}")
    t0 = time.monotonic()
    scade = t0 + tetto
    while True:
        resta = scade - time.monotonic()
        if resta <= 0:
            ms = (time.monotonic() - t0) * 1000
            print(f"   ⛔ NESSUN TELA dopo {ms:.0f} ms: §7.1 vuole una risposta "
                  f"«riuscita o no».  ⚠ E' il silenzio che «lascia il client ad "
                  f"aspettare per sempre»")
            return None
        try:
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=resta)
        except asyncio.TimeoutError:
            continue
        if m is None:
            print(f"   ⛔ il canale si e' chiuso mentre aspettavo il TELA: "
                  f"{cli.caduta}")
            return None
        tipo, corpo, grezzo = m
        # ⭐ (registrato all'arrivo da `Cliente._sfoglia()`, non qui)
        nome = NOME.get(tipo, f"{tipo:#06x}")
        if nome != "TELA":
            print(f"   ·  nel frattempo: {nome} ({len(corpo)} byte)")
            if nome == "CONGEDO":
                mot = corpo[0] if corpo else 0
                print(f"   ⛔ CONGEDO invece del TELA: motivo {mot:#04x} = "
                      f"{MOTIVI.get(mot, '?')}")
                return None
            continue
        ms = (time.monotonic() - t0) * 1000
        if len(corpo) < 10:
            print(f"   ⛔ TELA con un corpo di {len(corpo)} byte: §7.1 ne vuole "
                  f"10 (u8, u8, u32, u32) — i byte sono nella traccia")
            return None
        es, mot = corpo[0], corpo[1]
        tl, ta = struct.unpack("!II", corpo[2:10])
        print(f"   ← TELA {TELA_ESITO.get(es, es)}"
              f"/{TELA_MOTIVO.get(mot, mot)} tela in vigore {tl}x{ta} "
              f"dopo {ms:.0f} ms")
        return es, mot, tl, ta, ms


def scrivi_video(a, cli):
    """I fotogrammi presi dal filo, per un decodificatore TERZO.

    ⛔ E si chiama DOPO l'attesa di `--resta`, non prima: alla riga in cui la
       sessione si apre non e' ancora arrivato nessun fotogramma, e un file
       vuoto direbbe «il server non manda video» su un server che lo manda.
       ⚠ E' costato un giro, il 17 agosto 2026 — un difetto del banco con la
         faccia di un difetto del prodotto, il terzo della giornata.
    """
    if not a.video_scrivi or not cli.v_fotogrammi:
        if a.video_scrivi:
            print("   [vid]  ⛔ nessun fotogramma preso dal filo: niente file")
        return
    # ⛔ I fotogrammi si concatenano NELL'ORDINE DEL NUMERO (§6.2): gli stream
    #    sono indipendenti e possono arrivare fuori ordine, e un flusso rimesso
    #    in fila male darebbe artefatti che sarebbero NOSTRI del banco — cioe'
    #    la risposta sbagliata alla domanda che questo file esiste per fare.
    ordinati = sorted(cli.v_fotogrammi, key=lambda f: f[0])
    with open(a.video_scrivi, "wb") as f:
        for _, _, _, _, d in ordinati:
            f.write(d)
    chiavi = sum(1 for x in ordinati if x[1])
    print(f"   [vid]  {len(ordinati)} fotogrammi ({chiavi} chiavi), "
          f"{ordinati[0][2]}x{ordinati[0][3]}, scritti in {a.video_scrivi}")


def scrivi_appunti(a, cli):
    """L'esito degli appunti, in JSON, per il giudice del banco.

    ⛔ E i fatti si scrivono TUTTI, anche quelli che non servono a questo giro:
       «nessun annuncio», «annuncio senza testo» e «testo diverso da quello
       copiato» sono tre difetti con lo stesso sintomo, e un file che portasse
       solo il verdetto li renderebbe indistinguibili (`LEZIONI.md` §1.9).

    ⛔ E le VIOLAZIONI di §7.4 si scrivono anche quando il giro e' verde: un
       server che consegna il testo giusto violando il protocollo lungo la
       strada e' un server che il banco deve bocciare — «funziona» non e'
       «e' conforme».
    """
    if not a.appunti_scrivi:
        return
    esito = {
        "annunci_dal_server": cli.app_annunci,
        "chiesti_dal_server": cli.app_chiesti,
        "serviti_al_server": cli.app_serviti,
        "mio_id": cli.app_mio_id,
        "mio_testo": cli.app_mio_testo,
        # ⛔ `None` = non e' arrivato niente, `""` = e' arrivata una stringa
        #    vuota.  Sono due fatti diversi, e JSON li tiene separati.
        "ricevuto": cli.app_ricevuto,
        "violazioni": cli.app_violazioni,
    }
    with open(a.appunti_scrivi, "w") as f:
        json.dump(esito, f, ensure_ascii=False, indent=1)
    print(f"   [app]  esito scritto in {a.appunti_scrivi} "
          f"({len(cli.app_violazioni)} violazioni di §7.4)")


def scrivi_audio(a, cli):
    """I blocchi d'audio su disco, e i sei contatori a schermo.

    ⛔ I contatori si stampano SEMPRE, anche a zero: `CODER.md` §3.10 — «una
       lettura negata non e' una lettura che dice zero».  Un giro che non
       stampa niente e uno che ha ricevuto zero datagram devono avere due
       facce diverse.
    """
    if cli is None:
        return
    print(f"   [audio] ricevuti {cli.a_ricevuti} · {cli.a_byte} byte di carico · "
          f"codec {cli.a_codec if cli.a_codec is not None else '(nessuno)'}")
    print(f"   [audio] scartati — corti {cli.a_corti} · tipo {cli.a_tipo} · "
          f"prefisso {cli.a_prefisso} · vecchi {cli.a_vecchi}")
    if not a.audio_scrivi:
        return
    import base64
    with open(a.audio_scrivi, "w") as f:
        for b in cli.a_blocchi:
            f.write(json.dumps({"istante": b["istante"], "codec": b["codec"],
                                "byte": base64.b64encode(b["byte"]).decode()}) + "\n")
    print(f"   [audio] blocchi scritti in {a.audio_scrivi} ({len(cli.a_blocchi)})")


def scrivi_traccia(a, reg, cli=None):
    """La registrazione si scrive presto, e si RISCRIVE a ogni tappa.

    ⛔ «Non ho niente da giudicare» e «conforme» sono due cose diverse: un file
       vuoto non si scrive, cosi' chi lo cerca vede che non c'e' invece di
       giudicare zero blocchi.

    ⚠⛔ **E dal 16 agosto 2026 si RISCRIVE, dove prima si scriveva una volta
        sola.**  La guardia `scritta` era giusta finche' dopo `SESSIONE` questo
    programma non registrava piu' niente: adesso registra l'`ADATTA_TELA`, il
    `TELA`, la `VISTA` e la chiusura del canale — ⛔ e con la guardia in piedi
    **la meta' interessante della traccia non arrivava nel file**.  Un banco
    che chiude il file prima di fare la cosa che deve misurare consegna
    all'arbitro una registrazione conforme e vuota.

    ⭐ E il FIN si segna QUI, non nell'evento che lo riceve: i messaggi del
       server passano per una coda, e marcare la fine dal gestore dell'evento
    scriverebbe la chiusura **prima** di messaggi che nella traccia vengono
    dopo.  ⛔ Sarebbe un byte falso proprio nel campo che §11.1 ha aggiunto per
    non far confondere una fine con un'interruzione.
    """
    if not (a.registra and reg.blocchi):
        return
    if cli is not None and cli.finito and not getattr(reg, "fine_segnata", False):
        reg.segna_fine(SERVER, Registratore.FIN)
        reg.fine_segnata = True
    reg.scrivi(a.registra)
    reg.scritta = True
    print(f"   registrazione: {a.registra} ({len(reg.blocchi)} blocchi)")


def corpo_ciao(audio="opus,pcm", video="h264", prof="8,10"):
    # ⛔ `audio` si puo' restringere dalla riga di comando, e NON e' un trucco:
    #    e' quel che dichiara un client che Opus non lo sa fare.  §4.3 impone
    #    `pcm` a entrambi proprio per questo — e' «la base sempre disponibile»,
    #    e il controllo positivo di Opus.  ⇒ `--audio-codec pcm` esercita la
    #    negoziazione, non la scavalca.
    # ⛔ E anche il VIDEO si puo' restringere, dal 17 agosto 2026: serve a
    #    esercitare il ramo del ripiego senza un browser di mezzo.  ⚠ Non e' un
    #    trucco — e' quel che dichiara un client che l'HEVC non lo sa
    #    decodificare, cioe' **esattamente Firefox**.  §4.3 fa scegliere al
    #    server dentro l'intersezione, e restringere l'intersezione e' un uso
    #    del protocollo, non un aggiramento.
    #
    # ⛔⛔⛔ HO CAMBIATO IL METRO — 23 agosto 2026, sera (`fasi/09` §14.1).
    #    Il predefinito era **`hevc,av1`** ed e' rimasto tale quando AV1 e'
    #    uscito dal prodotto (20 agosto, `DECISIONI.md` §1.13-ter): il server
    #    sceglieva dunque **HEVC** in ogni giro di banco, mentre `pagina.html`
    #    (`PREFERENZA = ["hevc", "h264"]`, riga 818) dichiara **solo i codec che
    #    hanno davvero DIPINTO la sonda** — e su Firefox HEVC non dipinge.
    #    ⇒ Il banco misurava un codec che l'utente non riceve mai.
    #    `[M]` stessa scena, stessa tela, stesso QP 26: **21,18 Mbit/s in HEVC
    #    contro 7,92 in H.264**, un fattore **2,7** (`fasi/09` §13.5.1).
    #    ⇒ ⛔ **I numeri di banda presi prima di questa riga NON si confrontano
    #      con quelli presi dopo.**  Il vecchio metro si rifa' con
    #      `--video-codec hevc`, e va detto ogni volta che lo si usa.
    voci = [("video.codec", video), ("video.profondita", prof),
            ("audio.codec", audio), ("video.livello", "5.1"),
            ("video.misura_massima", "3840x2160"), ("appunti.testo", "si"),
            ("input.tocco", "no"), ("client.nome", "cliente-di-prova 0.1.0")]
    out = struct.pack("!HH", 1, len(voci))
    for n, v in voci:
        out += s(n) + s(v)
    return out


async def principale(a) -> int:
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                            max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    reg = Registratore()
    autorita = f"{a.indirizzo}:{a.porta}"

    print(f"== cliente di prova RCP -> https://{autorita}{a.percorso}")
    async with connect(a.indirizzo, a.porta, configuration=conf,
                       create_protocol=Cliente) as cli:
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.apri_sessione(autorita, a.percorso)
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        print(f"   CONNECT estesa: :status = {stato}")
        if stato != "200":
            return 1
        # ⛔ Lo stream VERO del canale di controllo finisce nella traccia: §11.1
        #    lo chiede, e §2.5 ci fa poggiare sopra P3 — «un fotogramma sullo
        #    stream del canale di controllo».  Con lo `0` scritto a mano quel
        #    controllo dell'arbitro guardava un numero inventato.
        reg.stream = cli.apri_controllo()
        # ⛔ E il registratore si consegna al CLIENTE, perche' da qui in poi i
        #    byte del server si registrano dove arrivano (riquadro in
        #    `Cliente.__init__`).  ⚠ Prima di questa riga non puo' essere
        #    arrivato niente: il canale di controllo non esisteva.
        cli.reg = reg

        # ⛔ LA TRACCIA SI SCRIVE ANCHE QUANDO LA STRETTA DI MANO NON RIESCE.
        #
        #    Rilievo R8.9: il terzo giro di B3 esiste per produrre UN oggetto —
        #    la registrazione di chi ha ricevuto il `CONGEDO(0x0F)` — e quella
        #    registrazione non veniva scritta mai, perche' l'eccezione partiva
        #    prima.  ⭐ Il validatore di B4 e' l'arbitro anche del rifiuto.
        try:
            # ── CIAO ────────────────────────────────────────────────────────
            b = inquadra(T["CIAO"], corpo_ciao(a.audio_codec, a.video_codec, a.video_profondita))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            nome, corpo, grezzo = await attendi(cli, "ECCOMI", reg=reg)
            versione = struct.unpack("!H", corpo[:2])[0]
            print(f"   ECCOMI: versione {versione}")

            # ── CREDENZIALI ─────────────────────────────────────────────────
            corpo_c = s(a.utente) + s(a.parola)
            b = inquadra(T["CREDENZIALI"], corpo_c)
            # §11.1: la parola si oscura, la lunghezza resta vera
            ini = 6 + 2 + len(a.utente.encode()) + 2
            qua = len(a.parola.encode())
            imp = hashlib.sha256(a.parola.encode()).digest()
            cli.manda(b)
            reg.aggiungi(CLIENT,
                         b[:ini] + bytes([0x2A]) * qua + b[ini + qua:],
                         [(ini, qua, imp)])
            t0 = time.monotonic()
            nome, corpo, grezzo = await attendi(cli, "AMMESSO", attesa=20, reg=reg)
            ms = (time.monotonic() - t0) * 1000
            # ⭐ §4.4-bis: il ritardo fisso vale ANCHE per AMMESSO.  Si
            #    cronometra qui perche' nessun altro banco lo vede, e una
            #    regressione che lo togliesse non farebbe fallire niente.
            print(f"   AMMESSO dopo {ms:.0f} ms"
                  + ("   ⭐ il secondo fisso c'e'" if ms >= 1000 else
                     "   ⛔ MENO DI UN SECONDO: §4.4-bis violata"))
            if ms < 1000:
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 1

            # ── ATTACCA ─────────────────────────────────────────────────────
            b = inquadra(T["ATTACCA"],
                         struct.pack("!IIII", a.larghezza, a.altezza,
                                     a.larghezza, a.altezza) + s(a.disposizione))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            nome, corpo, grezzo = await attendi(cli, "SESSIONE", reg=reg)
        except Exception:
            scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
            raise
        stato_s = corpo[0]
        lar, alt = struct.unpack("!II", corpo[1:9])
        n = struct.unpack("!H", corpo[9:11])[0]
        desktop = corpo[11:11 + n].decode()
        print(f"   ⭐ SESSIONE: stato={stato_s} tela={lar}x{alt} desktop={desktop}")

        # ═══════════════════════════════════════════════════════════════════
        # ⭐⛔ LA STRADA DELLA TELA — sottofase 6.6, 16 agosto 2026
        #
        #    ⛔ *«Nessuno dei due manda un `ADATTA_TELA`»*: da qui in poi non e'
        #       piu' vero.  E c'e' una ragione in piu' per farlo **all'attacco**,
        #       ed e' del 15 agosto: `DECISIONI.md` §5.0-sexies fa chiedere al
        #       client *«la tela della propria finestra all'attacco di ogni
        #       sessione, da se'»* — quindi questa non e' una prova di
        #       laboratorio, e' quel che il client vero fa ogni volta.
        #
        # ⚠ E il conto in volo si tiene ANCHE QUI, non solo nell'arbitro: §6.2
        #   lega al conto il modo in cui il client tratta i fotogrammi, e un
        #   cliente di prova che non lo tenesse non potrebbe accorgersi di un
        #   `TELA` che non ha chiesto.
        tela_viva = (lar, alt)
        # ⭐ La tela in vigore **PRIMA** dell'ultimo `TELA(ADATTATA)`: e' quella
        #    su cui le coordinate in volo di §7.1 sono ancora valide, ed e'
        #    l'unico numero da cui si puo' costruire il caso del secondo di
        #    grazia senza inventarselo.  ⛔ `None` finche' nessun adattamento e'
        #    riuscito: allora la scena non esiste, e si dice invece di fingerla.
        tela_prec_adattata = None
        esiti_tela = []
        if a.adatta:
            for al, aa, quando in a.adatta:
                if quando:
                    # ⭐ E' il ridimensionamento **a caldo**: la sessione e' gia'
                    #    viva e in mezzo passano fotogrammi.  ⚠ Si aspetta con
                    #    gli occhi aperti — un `sleep` non si accorgerebbe che
                    #    la sessione e' caduta nel frattempo, e la misura
                    #    dell'`ADATTA_TELA` sarebbe presa su una connessione
                    #    morta (rilievi R8.2, R8.4).
                    print(f"   ·  aspetto {quando} s a sessione viva")
                    try:
                        await asyncio.wait_for(cli.caduto.wait(), timeout=quando)
                        print(f"   ⛔ caduta prima di poter chiedere la tela: "
                              f"{cli.caduta}")
                        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                        return 4
                    except asyncio.TimeoutError:
                        pass
                prima_di_questo = tela_viva
                r = await chiedi_tela(cli, reg, al, aa, a.attesa_tela)
                esiti_tela.append(r)
                if r is not None and r[0] == 1:
                    tela_prec_adattata = prima_di_questo
                if r is None:
                    # ⛔ Il silenzio si REGISTRA e si esce con un codice suo: e'
                    #    la scena di §7.1, e va distinta da «la sessione e'
                    #    caduta» (4) e da «tutto bene» (0).
                    scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                    return 5
                tela_viva = (r[2], r[3])
        # ═══════════════════════════════════════════════════════════════════
        # ⭐⛔ IL SECONDO DI GRAZIA DI §7.1, PUNTATO CONTRO IL SERVER
        #     — 22 agosto 2026, e fino a stamattina non era mai stato fatto.
        #
        # §7.1: *«Dopo aver mandato `TELA(ADATTATA)` il server DEVE accettare
        # per **un secondo** coordinate di input valide sulla tela
        # **precedente**, saturandole alla nuova e scrivendolo nel registro;
        # passato quel secondo, sono `ERRORE_PROTOCOLLO`»*.
        #
        # ⛔⛔ LA TRAPPOLA, E VA DISINNESCATA PRIMA DI SCEGLIERE IL RITARDO.
        #
        #     La regola e' del **SERVER**; la registrazione la prende il
        #     **CLIENT**.  L'intervallo visto qui e' piu' CORTO di quello vero
        #     di mezzo giro di rete per lato (§11.1, *«il tempo registrato e'
        #     di CHI REGISTRA»*).  ⇒ Un caso «dentro il secondo» messo a 0,95 s
        #     potrebbe essere 1,02 s per il server, e il banco accuserebbe il
        #     prodotto di un difetto che non ha — o, peggio, si assolverebbe da
        #     solo.
        #
        # ⭐ La cura non e' un calcolo: e' **stare lontani dal confine**, e
        #    dichiarare perche'.  Chi chiama questo cliente sceglie il ritardo;
        #    qui si stampa il margine, cosi' un ritardo scelto male si vede
        #    invece di produrre un verdetto.
        #
        # ⛔ E LA COORDINATA NON SI INVENTA: e' **l'ultimo pixel della tela
        #    precedente**, `(prec_l - 1, prec_a - 1)`.  Due ragioni, e la
        #    seconda vale piu' della prima:
        #      · e' valida sulla tela di prima **per definizione** (§7.3: «0 <=
        #        x < tela_larghezza»), quindi il caso e' quello di §7.1 e non
        #        «una coordinata sbagliata» — che §7.1 NON copre, e il server
        #        ha una riga apposta per dirlo;
        #      · saturata, deve finire **esattamente** su `(nuova_l - 1,
        #        nuova_a - 1)`, cioe' su un punto NOTO.  ⭐ E' il controllo che
        #        attraversa la conversione: un server che rifiutasse la
        #        coordinata *dicendolo nel registro* ma la applicasse lo stesso
        #        passerebbe l'arbitro, e non passerebbe questo.
        if a.puntatore_vecchia is not None:
            if tela_prec_adattata is None:
                print("   ⛔ --puntatore-vecchia, ma nessun TELA(ADATTATA) e' "
                      "riuscito: non esiste nessuna «tela precedente», e una "
                      "coordinata scelta a caso proverebbe un'ALTRA regola "
                      "(§7.3 «fuori dalla tela»), non il secondo di grazia")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 6
            px = tela_prec_adattata[0] - 1
            py = tela_prec_adattata[1] - 1
            if px < tela_viva[0] and py < tela_viva[1]:
                print(f"   ⛔ ({px},{py}) e' DENTRO la tela in vigore "
                      f"{tela_viva[0]}x{tela_viva[1]}: la scena di §7.1 non e' "
                      f"esercitata affatto — serve una tela nuova piu' piccola "
                      f"della precedente {tela_prec_adattata[0]}x"
                      f"{tela_prec_adattata[1]}")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 6
            # La saturazione attesa, calcolata come §7.1 la descrive: «all'ultimo
            # pixel valido».
            sx = px if px < tela_viva[0] else tela_viva[0] - 1
            sy = py if py < tela_viva[1] else tela_viva[1] - 1
            rit_ms = int(round(a.puntatore_vecchia * 1000))
            print(f"   ⛔ ATTESO, dichiarato PRIMA: PUNTATORE ({px},{py}) — "
                  f"valido sulla tela precedente {tela_prec_adattata[0]}x"
                  f"{tela_prec_adattata[1]}, fuori da quella in vigore "
                  f"{tela_viva[0]}x{tela_viva[1]} — a {rit_ms} ms dal "
                  f"TELA(ADATTATA)")
            if rit_ms > 1000:
                print(f"      ⇒ oltre il secondo di grazia, e il margine e' "
                      f"{rit_ms - 1000} ms.  ⛔ Il server DEVE rifiutare: il "
                      f"SUO intervallo e' ancora piu' lungo di questo")
            else:
                print(f"      ⇒ dentro il secondo, e il margine e' "
                      f"{1000 - rit_ms} ms — cioe' quanto giro di rete ci "
                      f"vorrebbe per portarlo oltre.  ⛔ Il server DEVE "
                      f"saturare a ({sx},{sy}) e scriverlo nel registro")
            if cli.ultimo_tela_ms is None:
                print("   ⛔ nessun istante registrato per il TELA: non so da "
                      "quando contare")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 6
            bersaglio = cli.ultimo_tela_ms + rit_ms
            # ⛔ SI ASPETTA CON GLI OCCHI APERTI — rilievi R8.2/R8.4.  Un
            #    `sleep` non si accorgerebbe che la sessione e' morta nel
            #    frattempo, e il `PUNTATORE` partirebbe su una connessione gia'
            #    chiusa: il banco misurerebbe se stesso.
            caduto_prima = False
            while True:
                resta = (bersaglio - reg.istante()) / 1000.0
                if resta <= 0:
                    break
                try:
                    await asyncio.wait_for(cli.caduto.wait(), timeout=resta)
                    caduto_prima = True
                    break
                except asyncio.TimeoutError:
                    pass
            if caduto_prima:
                print(f"   ⛔ la sessione e' caduta PRIMA del PUNTATORE: "
                      f"{cli.caduta} — la regola del secondo non e' stata "
                      f"esercitata")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 4
            pid, pms = cli.manda_puntatore(px, py)
            dt = None if pms is None else pms - cli.ultimo_tela_ms
            print(f"   → PUNTATORE id={pid} ({px},{py}) — dt registrato "
                  f"{dt} ms dal TELA(ADATTATA).  ⚠ E' il numero che l'arbitro "
                  f"leggera': l'intervallo del SERVER e' piu' lungo di questo")

            # ═══════════════════════════════════════════════════════════════
            # ⭐⛔ IL TERZO TESTIMONE: SI CHIEDE UN FOTOGRAMMA, PERCHE' UN
            #     DESKTOP FERMO NON NE MANDA.
            #
            # `[M]` 22 agosto 2026, primo giro vero su 7721: dopo il
            # `PUNTATORE` la traccia porta **zero** fotogrammi — la sessione
            # GNOME senza monitor non ha niente che si muova, e il server
            # spedisce solo quel che cambia.  ⇒ Il campo `input` di §6.2 —
            # *«l'identificatore dell'ultimo input INIETTATO»*, l'unico
            # testimone dell'iniezione che vive **sul filo** — non poteva dire
            # niente, e «non ha iniettato» e «non e' passato nessun
            # fotogramma» avevano la stessa faccia (`LEZIONI.md` §1.9).
            #
            # ⛔ E lo si chiede DOPO il puntatore, con un ritardo: il canale di
            #    input e quello di controllo sono **due stream indipendenti**
            #    (§2.5) e niente ne ordina la consegna.  Senza attesa la chiave
            #    potrebbe essere catturata PRIMA che l'input sia iniettato, e
            #    un `input = 0` significherebbe «non so», non «non iniettato».
            #
            # ⚠ E se la sessione e' gia' caduta non si manda niente: nel giro
            #   «oltre il secondo» quella e' la strada GIUSTA, e insistere su
            #   una connessione morta produrrebbe un errore del banco al posto
            #   di una misura.
            if a.chiave_dopo:
                try:
                    await asyncio.wait_for(cli.caduto.wait(),
                                           timeout=a.chiave_dopo)
                    print(f"   ·  niente RICHIEDI_CHIAVE: la sessione e' gia' "
                          f"caduta ({cli.caduta}) — ⭐ dopo un PUNTATORE oltre "
                          f"il secondo e' quel che §7.1 vuole")
                except asyncio.TimeoutError:
                    ultimo = max((f[0] for f in cli.v_fotogrammi), default=0)
                    b = inquadra(T["RICHIEDI_CHIAVE"],
                                 struct.pack("!I", ultimo))
                    cli.manda(b)
                    reg.aggiungi(CLIENT, b)
                    print(f"   → RICHIEDI_CHIAVE({ultimo}) — ⚠ non e' la scena "
                          f"di §5.2: serve a far passare UN fotogramma, cosi' "
                          f"il campo `input` di §6.2 puo' testimoniare")

        if a.vista:
            # ⚠ `VISTA` NON DEVE far cambiare la tela (§7.1).  Se dopo questa
            #   arriva un `TELA`, il filo lo dice e l'arbitro lo accusa: qui non
            #   si giudica, si registra.
            vl, va = a.vista
            b = inquadra(T["VISTA"], struct.pack("!II", vl, va))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            print(f"   → VISTA {vl}x{va}   ⚠ non deve far cambiare la tela")

        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)

        # ⛔ IL SEGNALE DI «ATTACCATO», E PERCHE' NON BASTA UNA RIGA STAMPATA.
        #
        #    Il 10 agosto 2026 il terzo giro di B3 aspettava la parola
        #    «SESSIONE» nel registro di questo programma — e Python **bufferizza
        #    lo stdout quando e' rediretto su un file**: quella riga compariva
        #    solo all'uscita del processo, cioe' **nell'istante esatto in cui il
        #    client si staccava**.
        #
        # ⚠ Il banco diceva «la prima e' attaccata» leggendo una verita' appena
        #   scaduta, e la seconda connessione arrivava sempre a posto libero.
        #   ⛔ Un controllo che sembra giusto e misura l'istante sbagliato: il
        #      rosso finiva sul server, che non c'entrava niente.
        #
        # ⭐ Un file scritto e chiuso e' un fatto; una riga stampata e' una
        #    speranza sul momento in cui qualcuno la vedra'.
        if a.segnale:
            with open(a.segnale, "w") as f:
                f.write("attaccato\n")

        # ═══ GLI APPUNTI — §7.4 ═══════════════════════════════════════════
        #
        # ⛔ E il verso `dispositivo → sessione` si annuncia PRIMA di scrivere
        #    il segnale?  NO, e la ragione e' l'ordine dei due lati del banco:
        #    il segnale dice «sono attaccato», e il lato che copia con `xclip`
        #    aspetta proprio quello.  Annunciare prima vorrebbe dire annunciare
        #    quando l'altro lato non e' ancora pronto a guardare.
        if a.appunti_copia:
            cli.appunti_annuncia(a.appunti_copia)

        if a.appunti_attendi:
            # ⛔ SI ASPETTA UN ANNUNCIO, E POI LO SI CHIEDE — §7.4: «si annuncia
            #    e si chiede, invece di spingere».  ⚠ E i due passi si contano
            #    separati: «non e' arrivato nessun annuncio» e «l'annuncio e'
            #    arrivato e il testo no» sono due difetti diversi con lo stesso
            #    sintomo (`LEZIONI.md` §1.9).
            print(f"   [app]  aspetto un annuncio dal server, fino a "
                  f"{a.appunti_attendi} s")
            fine = time.monotonic() + a.appunti_attendi
            while not cli.app_annunci and time.monotonic() < fine:
                cli.app_evento.clear()
                try:
                    await asyncio.wait_for(cli.app_evento.wait(),
                                           timeout=max(0.1, fine - time.monotonic()))
                except asyncio.TimeoutError:
                    break
            if not cli.app_annunci:
                print("   [app]  ⛔ nessun annuncio dal server entro il tempo")
            else:
                cli.appunti_chiedi()
                fine = time.monotonic() + a.appunti_attendi
                while cli.app_ricevuto is None and time.monotonic() < fine:
                    cli.app_evento.clear()
                    try:
                        await asyncio.wait_for(cli.app_evento.wait(),
                                               timeout=max(0.1, fine - time.monotonic()))
                    except asyncio.TimeoutError:
                        break
                if cli.app_ricevuto is None:
                    print("   [app]  ⛔ l'annuncio e' arrivato e il testo NO")
                else:
                    print(f"   [app]  ⭐ ricevuti {len(cli.app_ricevuto)} "
                          f"caratteri: «{cli.app_ricevuto[:60]}»")
        scrivi_appunti(a, cli)
        if a.resta:
            # ⛔ SI RESTA CON GLI OCCHI APERTI, NON DORMENDO — rilievi R8.2/R8.4.
            #
            #    Un `asyncio.sleep` non si accorge di niente: la connessione
            #    poteva cadere per il tetto d'inattivita' di QUIC, o la sessione
            #    poteva essere chiusa dal server per far posto a un altro, e
            #    questo programma usciva 0 dicendo «sono rimasto attaccato».
            #    Su quel codice d'uscita il terzo giro concludeva «nessun client
            #    vivo viene spodestato», che e' l'invariante I2 alla lettera.
            #
            # ⚠ NON si manda niente per accertarsene: il quarto giro misura
            #   l'orologio del SILENZIO, e un byte lo azzererebbe.  Si ascolta e
            #   basta — che e' precisamente il lato che riceve.
            print(f"   resto attaccato per {a.resta} s"
                  + (f", facendomi sentire ogni {a.vivo} s" if a.vivo else ""))
            try:
                if a.vivo:
                    # ⛔⛔ E QUESTA OPZIONE E' UNA TRAPPOLA — 16 agosto 2026.
                    #
                    #    `VISTA` (0x0008) e' nel protocollo, ⛔ ma QUESTO server
                    #    non la serve ancora: risponde `ERRORE_PROTOCOLLO` e
                    #    CHIUDE.  `[M]` Su venti giri di misura, tre sessioni
                    #    sono morte a 8 secondi per colpa di questa riga, e i
                    #    tempi risultavano «10,4 s» — un numero del banco, non
                    #    del prodotto.
                    #
                    # ⭐ La lezione, che l'utente ha detto meglio: *«per i test
                    #    usa il browser, non il banco — e' l'unico modo di
                    #    misurare quello che accade davvero»*.  Un client di
                    #    prova che manda quel che il vero client non manda non
                    #    misura il prodotto: misura se stesso.
                    raise SystemExit(
                        "⛔ --vivo manda VISTA (0x0008), che questo server non "
                        "serve: chiuderebbe la sessione con ERRORE_PROTOCOLLO. "
                        "Per misurare i tempi si usa il BROWSER.")
                    # ⭐ `--vivo`: si manda una `VISTA` IDENTICA ogni tanto, solo
                    #    per non farsi staccare dall'orologio del silenzio (§5.3).
                    #
                    # ⛔ SPENTO DI SUO, ed e' il punto: il comportamento
                    #    predefinito — tacere — serve a MISURARE quell'orologio, e
                    #    il commento qui sopra lo dice dal 10 agosto.  ⚠ Chi lo
                    #    accende sta misurando un'altra cosa: la scena in cui il
                    #    client c'e' e lavora, che e' quella del browser vero.
                    #
                    # ⚠ E `VISTA` con gli stessi numeri e' un no-op semantico: non
                    #   cambia niente, e' lecita a sessione attiva (§7.1), e non
                    #   chiede niente al palco — a differenza di `RICHIEDI_CHIAVE`,
                    #   che gli farebbe rifare una chiave e falserebbe la misura.
                    scaduto = asyncio.get_event_loop().time() + a.resta
                    while asyncio.get_event_loop().time() < scaduto:
                        quanto = min(a.vivo, scaduto - asyncio.get_event_loop().time())
                        try:
                            await asyncio.wait_for(cli.caduto.wait(), timeout=quanto)
                            break
                        except asyncio.TimeoutError:
                            pass
                        cli.manda(inquadra(0x0008,
                                           struct.pack("!II", a.larghezza,
                                                       a.altezza)))
                    if not cli.caduto.is_set():
                        raise asyncio.TimeoutError
                else:
                    await asyncio.wait_for(cli.caduto.wait(), timeout=a.resta)
            except asyncio.TimeoutError:
                # ⛔ La bandiera si alza PRIMA di uscire: uscendo di qui
                #    `connect()` chiude la connessione, e l'evento che ne segue
                #    dev'essere gia' riconoscibile come nostro.
                cli.chiusa_da_noi = True
                print(f"   ⭐ ancora attaccato dopo {a.resta} s: niente e' caduto")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 0
            print(f"   ⛔ NON sono rimasto attaccato: {cli.caduta}")
            scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
            return 4
        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
        return 0


# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE NON DEVE PASSARE DALLA RIGA DI COMANDO — difetto **D12**,
#    curato il 12 agosto 2026.
#
# ⛔ `--parola` finisce nell'`argv` del processo, cioe' in `/proc/<pid>/cmdline`,
#    che su Linux e' **leggibile da chiunque**: un `ps` lanciato da un altro
#    utente durante il giro la stampa per intero.
#
# ⭐ La strada buona esisteva gia' in casa e questa e' la sua estensione, non un
#    secondo modo: `01-b10-secondo-utente.py` prende `--parola-file`, un file
#    `0600` che il lanciatore scrive con `printf` — un **builtin** della shell,
#    quindi nemmeno la scrittura passa per un processo con la parola in `argv` —
#    e cancella con una `trap`.
#
# ⚠ E `--parola` NON e' stata tolta, e non per pigrizia: dei chiamanti non
#   ancora curati la passano ancora, e romperli **in silenzio** sarebbe peggio
#   del difetto.  ⛔ Ma il ripiego si DICHIARA (`CODER.md` §4.2): un ripiego
#   silenzioso produce due comportamenti sotto la stessa etichetta, che e' la
#   forma **E2** — e qui i due comportamenti sono «il segreto e' protetto» e
#   «il segreto e' pubblico».  ⇒ chi passa `--parola` se lo sente dire.
#
# ⚠ E l'avviso guarda `sys.argv`, non il valore: il predefinito scritto nel
#   codice non sta in nessuna riga di comando, e dirgli il contrario sarebbe un
#   allarme che si impara a ignorare.
def parola_dagli_argomenti(a):
    """La parola d'ordine: da `--parola-file` se c'e', da `--parola` altrimenti.

    ⛔ E i tre modi di fallire si distinguono: «non si legge», «e' leggibile da
    altri» e «e' vuoto» hanno tre cure diverse, e un file vuoto NON e' una
    parola vuota — e' «il lanciatore non l'ha scritta» (`LEZIONI.md` §1.9).
    """
    percorso = getattr(a, "parola_file", "") or ""
    if percorso:
        try:
            modo = os.stat(percorso).st_mode & 0o077
        except OSError as e:
            print(f"   ⛔ il file della parola «{percorso}» non si legge: {e}")
            sys.exit(2)
        if modo:
            print(f"   ⚠ «{percorso}» e' leggibile da altri (bit {modo:o}): il "
                  f"segreto non e' protetto")
        try:
            with open(percorso, encoding="utf-8") as f:
                parola = f.read().strip("\n")
        except OSError as e:
            print(f"   ⛔ la parola non si legge da «{percorso}»: {e}")
            sys.exit(2)
        if not parola:
            print(f"   ⛔ il file della parola «{percorso}» e' VUOTO.  Non e'")
            print("      «la parola e' vuota»: e' «il lanciatore non l'ha scritta».")
            sys.exit(2)
        return parola
    if any(x == "--parola" or x.startswith("--parola=") for x in sys.argv[1:]):
        print("   ⚠ D12: la parola d'ordine e' arrivata da `--parola`, cioe' dalla")
        print("     RIGA DI COMANDO: sta in `/proc/<pid>/cmdline` e la vede chiunque")
        print("     faccia `ps` su questa macchina.  Il giro prosegue — il chiamante")
        print("     non e' stato curato — ma non e' un giro riservato.")
        print("     ⭐ La cura: `--parola-file <file 0600>`, come in B10.")
    return a.parola


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="la stretta di mano di RCP, dal lato client")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="prova")
    # ⛔ D12: la strada che NON passa da `ps`.  Vince su `--parola` se ci sono
    #    tutt'e due — un file scritto apposta e' sempre piu' recente di un
    #    predefinito.
    p.add_argument("--parola-file", default="",
                   help="file 0600 con la sola parola d'ordine (⭐ D12: cosi' "
                        "non finisce in `ps`)")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--registra")
    # ⭐ LA STRADA DELLA TELA — sottofase 6.6.
    #
    # ⛔ `--adatta LxH` oppure `LxH@S`: manda `ADATTA_TELA` e aspetta il `TELA`
    #    che §7.1 impone.  Ripetibile, e con `@S` si aspettano S secondi PRIMA
    #    di mandarla — ⭐ cosi' la stessa opzione copre le due scene della fase
    #    6: la richiesta **all'attacco** (`DECISIONI.md` §5.0-sexies, il client
    #    chiede la tela della propria finestra da se') e il **ridimensionamento
    #    a caldo** a sessione avviata.
    p.add_argument("--adatta", action="append", default=[], metavar="LxH[@S]",
                   help="ADATTA_TELA (0x000B), ripetibile; @S = secondi di "
                        "attesa prima di mandarla")
    p.add_argument("--vista", metavar="LxH",
                   help="VISTA (0x0008) dopo l'attacco — ⚠ §7.1: NON deve far "
                        "cambiare la tela")
    # ⭐⛔ IL SECONDO DI GRAZIA DI §7.1 — 22 agosto 2026.
    #
    # ⛔ Il ritardo si passa in SECONDI e non ha predefinito: la regola vive su
    #    un confine, e un valore scelto dal programma invece che dal banco
    #    sarebbe un confine scelto da chi non dichiara perche'.
    p.add_argument("--puntatore-vecchia", type=float, default=None,
                   metavar="RITARDO",
                   help="§7.1: manda un PUNTATORE all'ULTIMO PIXEL della tela "
                        "PRECEDENTE, RITARDO secondi dopo il TELA(ADATTATA).  "
                        "⚠ Il tempo e' quello del CLIENT: l'intervallo del "
                        "SERVER e' piu' LUNGO, quindi si sta lontani dal "
                        "secondo dai due lati")
    p.add_argument("--chiave-dopo", type=float, default=0, metavar="SECONDI",
                   help="dopo il PUNTATORE, aspetta SECONDI e manda una "
                        "RICHIEDI_CHIAVE: serve a far passare un fotogramma "
                        "su un desktop fermo, perche' il campo `input` di §6.2 "
                        "possa dire se l'input e' stato INIETTATO.  ⚠ Non si "
                        "manda se la sessione e' gia' caduta")
    # ⚠ Il tetto NON e' una regola di RCP: §7.1 impone la risposta, non un
    #   tempo.  Serve a non riprodurre il sintomo che si vuole misurare.
    p.add_argument("--attesa-tela", type=float, default=5.0,
                   help="quanto si aspetta un TELA prima di dichiarare il "
                        "silenzio (⚠ non e' una regola di RCP.md)")
    # ═══ L'AUDIO — fase 7 ═════════════════════════════════════════════════
    p.add_argument("--video-scrivi", default="",
                   help="dove scrivere i fotogrammi presi DAL FILO, cosi' come "
                        "sono — per darli a un decodificatore terzo e separare "
                        "il nostro flusso da quello del browser")
    p.add_argument("--video-codec", default="h264",
                   help="che cosa dichiarare in `video.codec` (§4.3).  "
                        "⭐ Il predefinito e' **quel che dichiara Firefox**: "
                        "`pagina.html` manda solo i codec che hanno DIPINTO la "
                        "sonda, e li' HEVC non dipinge.  ⛔ `hevc` rifa' il "
                        "vecchio metro (fino al 23 agosto 2026), e i due "
                        "insiemi di numeri NON si confrontano: `fasi/09` §14.1")
    p.add_argument("--video-profondita", default="8,10",
                   help="che cosa dichiarare in `video.profondita` (§4.3)")
    p.add_argument("--audio-codec", default="opus,pcm",
                   help="che cosa dichiarare in `audio.codec` (§4.3).  "
                        "⛔ `pcm` da solo e' legittimo ed e' il controllo "
                        "positivo di Opus, non un aggiramento")
    p.add_argument("--audio-scrivi", default="",
                   help="dove scrivere i blocchi d'audio ricevuti, in JSONL — "
                        "il giudice di `07-b42` legge questo")
    # ═══ GLI APPUNTI — fase 7, §7.4 ═══════════════════════════════════════
    p.add_argument("--appunti-copia", default="",
                   help="annuncia questo testo al server (verso dispositivo → "
                        "sessione) e poi resta a servirlo quando lo chiede")
    p.add_argument("--appunti-attendi", type=float, default=0,
                   help="aspetta fino a N secondi un annuncio dal server, lo "
                        "chiede, e scrive il testo che arriva (verso sessione → "
                        "dispositivo)")
    p.add_argument("--appunti-scrivi", default="",
                   help="dove scrivere l'esito degli appunti, in JSON — il "
                        "banco `07-b45` legge questo")
    p.add_argument("--resta", type=float, default=0)
    # ⭐ Ogni quanti secondi farsi sentire (0 = mai, ed e' il predefinito:
    #    tacere e' quel che serve a misurare l'orologio del silenzio).
    p.add_argument("--vivo", type=float, default=0)
    p.add_argument("--segnale",
                   help="file da scrivere quando la sessione e' aperta")
    a = p.parse_args()
    a.parola = parola_dagli_argomenti(a)

    def misura(testo, dove):
        """`LxH` o `LxH@S`.  ⛔ Un argomento storto si dice, non si indovina.

        ⚠ Un banco che accettasse `1264-800` interpretandolo come puo' darebbe
          una misura diversa da quella che chi lancia crede di aver chiesto, e
          il numero finirebbe in un rapporto: la forma d'errore **E2**.
        """
        quando = 0.0
        if "@" in testo:
            testo, _, s = testo.partition("@")
            try:
                quando = float(s)
            except ValueError:
                print(f"   ⛔ {dove}: «{s}» non e' un numero di secondi")
                sys.exit(2)
        parti = testo.lower().split("x")
        if len(parti) != 2 or not all(x.isdigit() for x in parti):
            print(f"   ⛔ {dove}: «{testo}» non ha la forma LxH (es. 1264x800)")
            sys.exit(2)
        return int(parti[0]), int(parti[1]), quando

    a.adatta = [misura(x, "--adatta") for x in a.adatta]
    a.vista = misura(a.vista, "--vista")[:2] if a.vista else None
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
