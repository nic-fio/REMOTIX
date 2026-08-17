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
     "ADATTA_TELA": 0x000B, "CONGEDO": 0x000C, "TELA": 0x000E,
     "TERMINA_SESSIONE": 0x0011}
NOME = {v: k for k, v in T.items()}
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
    """

    MAGIA = b"RCPREG\x00\x02"
    CONTINUA, FIN, RESET = 0, 1, 2

    def __init__(self):
        self.blocchi = []
        self.scritta = False
        # ⛔ Lo stream del canale di controllo, quello VERO.  §4.2: e' il primo
        #    stream bidirezionale della sessione, e ⚠ **non e' lo 0** — in
        #    HTTP/3 lo 0 e' gia' quello della CONNECT (rilievo R1.5).  Qui si
        #    scriveva `0` fisso: un numero che non e' mai stato quello, e che
        #    l'arbitro usa per P3 (§2.5, «un fotogramma sullo stream del canale
        #    di controllo»).
        self.stream = 0

    def aggiungi(self, verso, carico, oscurati=(), canale=0x00, stream=None,
                 fine=CONTINUA):
        self.blocchi.append([verso, canale, fine,
                             self.stream if stream is None else stream,
                             carico, list(oscurati)])

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
        out = bytearray(self.MAGIA + struct.pack("!II", len(self.blocchi), 0))
        for verso, canale, fine, stream, carico, osc in self.blocchi:
            out += struct.pack("!BBBQIH", verso, canale, fine, stream,
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
    if reg is not None:
        reg.aggiungi(SERVER, grezzo)
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
        reg.aggiungi(SERVER, grezzo)
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


def corpo_ciao(audio="opus,pcm"):
    # ⛔ `audio` si puo' restringere dalla riga di comando, e NON e' un trucco:
    #    e' quel che dichiara un client che Opus non lo sa fare.  §4.3 impone
    #    `pcm` a entrambi proprio per questo — e' «la base sempre disponibile»,
    #    e il controllo positivo di Opus.  ⇒ `--audio-codec pcm` esercita la
    #    negoziazione, non la scavalca.
    voci = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
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

        # ⛔ LA TRACCIA SI SCRIVE ANCHE QUANDO LA STRETTA DI MANO NON RIESCE.
        #
        #    Rilievo R8.9: il terzo giro di B3 esiste per produrre UN oggetto —
        #    la registrazione di chi ha ricevuto il `CONGEDO(0x0F)` — e quella
        #    registrazione non veniva scritta mai, perche' l'eccezione partiva
        #    prima.  ⭐ Il validatore di B4 e' l'arbitro anche del rifiuto.
        try:
            # ── CIAO ────────────────────────────────────────────────────────
            b = inquadra(T["CIAO"], corpo_ciao(a.audio_codec))
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
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli)
                return 1

            # ── ATTACCA ─────────────────────────────────────────────────────
            b = inquadra(T["ATTACCA"],
                         struct.pack("!IIII", a.larghezza, a.altezza,
                                     a.larghezza, a.altezza) + s(a.disposizione))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            nome, corpo, grezzo = await attendi(cli, "SESSIONE", reg=reg)
        except Exception:
            scrivi_traccia(a, reg, cli); scrivi_audio(a, cli)
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
                        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli)
                        return 4
                    except asyncio.TimeoutError:
                        pass
                r = await chiedi_tela(cli, reg, al, aa, a.attesa_tela)
                esiti_tela.append(r)
                if r is None:
                    # ⛔ Il silenzio si REGISTRA e si esce con un codice suo: e'
                    #    la scena di §7.1, e va distinta da «la sessione e'
                    #    caduta» (4) e da «tutto bene» (0).
                    scrivi_traccia(a, reg, cli); scrivi_audio(a, cli)
                    return 5
                tela_viva = (r[2], r[3])
        if a.vista:
            # ⚠ `VISTA` NON DEVE far cambiare la tela (§7.1).  Se dopo questa
            #   arriva un `TELA`, il filo lo dice e l'arbitro lo accusa: qui non
            #   si giudica, si registra.
            vl, va = a.vista
            b = inquadra(T["VISTA"], struct.pack("!II", vl, va))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            print(f"   → VISTA {vl}x{va}   ⚠ non deve far cambiare la tela")

        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli)

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
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli)
                return 0
            print(f"   ⛔ NON sono rimasto attaccato: {cli.caduta}")
            scrivi_traccia(a, reg, cli); scrivi_audio(a, cli)
            return 4
        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli)
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
    # ⚠ Il tetto NON e' una regola di RCP: §7.1 impone la risposta, non un
    #   tempo.  Serve a non riprodurre il sintomo che si vuole misurare.
    p.add_argument("--attesa-tela", type=float, default=5.0,
                   help="quanto si aspetta un TELA prima di dichiarare il "
                        "silenzio (⚠ non e' una regola di RCP.md)")
    # ═══ L'AUDIO — fase 7 ═════════════════════════════════════════════════
    p.add_argument("--audio-codec", default="opus,pcm",
                   help="che cosa dichiarare in `audio.codec` (§4.3).  "
                        "⛔ `pcm` da solo e' legittimo ed e' il controllo "
                        "positivo di Opus, non un aggiramento")
    p.add_argument("--audio-scrivi", default="",
                   help="dove scrivere i blocchi d'audio ricevuti, in JSONL — "
                        "il giudice di `07-b42` legge questo")
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
