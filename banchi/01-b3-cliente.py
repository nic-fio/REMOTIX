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
     "RESPINTO": 0x0005, "ATTACCA": 0x0006, "SESSIONE": 0x0007, "CONGEDO": 0x000C}
NOME = {v: k for k, v in T.items()}
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
    """Il formato di RCP.md §11.1, scritto una volta sola."""

    def __init__(self):
        self.blocchi = []
        self.scritta = False

    def aggiungi(self, verso, carico, oscurati=()):
        self.blocchi.append((verso, carico, list(oscurati)))

    def scrivi(self, percorso):
        out = bytearray(b"RCPREG\x00\x01" + struct.pack("!II", len(self.blocchi), 0))
        for verso, carico, osc in self.blocchi:
            out += struct.pack("!BBQIH", verso, 0x00, 0, len(carico), len(osc))
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
        self.caduto = asyncio.Event()

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

    def quic_event_received(self, event: QuicEvent) -> None:
        nome = type(event).__name__
        # ⛔ LA FINE DELLA CONNESSIONE SI STAMPA, SEMPRE.
        #
        #    E' l'unica riga che distingue «il tetto d'inattivita' di QUIC ha
        #    chiuso» da «il server ha liberato il posto lasciando aperta la
        #    connessione».  Senza, il quarto giro di B3 concludeva la seconda
        #    guardando /proc, che dice soltanto che un processo che dorme non
        #    e' morto (R8.2).
        if nome == "ConnectionTerminated":
            print(f"   [quic] connessione TERMINATA: codice "
                  f"{getattr(event, 'error_code', '?')} · "
                  f"{getattr(event, 'reason_phrase', '') or '(nessun motivo)'}")
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


def scrivi_traccia(a, reg):
    """La registrazione si scrive UNA volta sola, e anche se si e' fallito.

    ⛔ «Non ho niente da giudicare» e «conforme» sono due cose diverse: un file
       vuoto non si scrive, cosi' chi lo cerca vede che non c'e' invece di
       giudicare zero blocchi.
    """
    if a.registra and reg.blocchi and not getattr(reg, "scritta", False):
        reg.scrivi(a.registra)
        reg.scritta = True
        print(f"   registrazione: {a.registra} ({len(reg.blocchi)} blocchi)")


def corpo_ciao():
    voci = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
            ("audio.codec", "opus,pcm"), ("video.livello", "5.1"),
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
        cli.apri_controllo()

        # ⛔ LA TRACCIA SI SCRIVE ANCHE QUANDO LA STRETTA DI MANO NON RIESCE.
        #
        #    Rilievo R8.9: il terzo giro di B3 esiste per produrre UN oggetto —
        #    la registrazione di chi ha ricevuto il `CONGEDO(0x0F)` — e quella
        #    registrazione non veniva scritta mai, perche' l'eccezione partiva
        #    prima.  ⭐ Il validatore di B4 e' l'arbitro anche del rifiuto.
        try:
            # ── CIAO ────────────────────────────────────────────────────────
            b = inquadra(T["CIAO"], corpo_ciao())
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
                scrivi_traccia(a, reg)
                return 1

            # ── ATTACCA ─────────────────────────────────────────────────────
            b = inquadra(T["ATTACCA"],
                         struct.pack("!IIII", a.larghezza, a.altezza,
                                     a.larghezza, a.altezza) + s(a.disposizione))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            nome, corpo, grezzo = await attendi(cli, "SESSIONE", reg=reg)
        except Exception:
            scrivi_traccia(a, reg)
            raise
        stato_s = corpo[0]
        lar, alt = struct.unpack("!II", corpo[1:9])
        n = struct.unpack("!H", corpo[9:11])[0]
        desktop = corpo[11:11 + n].decode()
        print(f"   ⭐ SESSIONE: stato={stato_s} tela={lar}x{alt} desktop={desktop}")

        scrivi_traccia(a, reg)

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
            print(f"   resto attaccato per {a.resta} s")
            try:
                await asyncio.wait_for(cli.caduto.wait(), timeout=a.resta)
            except asyncio.TimeoutError:
                print(f"   ⭐ ancora attaccato dopo {a.resta} s: niente e' caduto")
                return 0
            print(f"   ⛔ NON sono rimasto attaccato: {cli.caduta}")
            return 4
        return 0


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="la stretta di mano di RCP, dal lato client")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="prova")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--registra")
    p.add_argument("--resta", type=float, default=0)
    p.add_argument("--segnale",
                   help="file da scrivere quando la sessione e' aperta")
    a = p.parse_args()
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
