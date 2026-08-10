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


class Registratore:
    """Il formato di RCP.md §11.1, scritto una volta sola."""

    def __init__(self):
        self.blocchi = []

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
        if nome == "StreamDataReceived" and event.stream_id == self.controllo:
            self.arrivati += event.data
            self._sfoglia()
            if event.end_stream:
                self.finito = True
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
            if len(event.data) >= 7 and event.data[0] == 0x68 and event.data[1] == 0x43:
                codice = event.data[6]
                print(f"   [wt]   sessione chiusa dal server, codice {codice:#04x}"
                      f" = {MOTIVI.get(codice, '?')}")
            if event.end_stream:
                self.finito = True
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


async def attendi(cli, quale, attesa=10.0):
    m = await asyncio.wait_for(cli.messaggi.get(), timeout=attesa)
    if m is None:
        raise RuntimeError("il canale di controllo si e' chiuso")
    tipo, corpo, grezzo = m
    nome = NOME.get(tipo, f"{tipo:#06x}")
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

        # ── CIAO ────────────────────────────────────────────────────────────
        b = inquadra(T["CIAO"], corpo_ciao())
        cli.manda(b)
        reg.aggiungi(CLIENT, b)
        nome, corpo, grezzo = await attendi(cli, "ECCOMI")
        reg.aggiungi(SERVER, grezzo)
        versione = struct.unpack("!H", corpo[:2])[0]
        print(f"   ECCOMI: versione {versione}")

        # ── CREDENZIALI ─────────────────────────────────────────────────────
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
        nome, corpo, grezzo = await attendi(cli, "AMMESSO", attesa=20)
        ms = (time.monotonic() - t0) * 1000
        reg.aggiungi(SERVER, grezzo)
        # ⭐ §4.4-bis: il ritardo fisso vale ANCHE per AMMESSO.  Si cronometra
        #    qui perche' nessun altro banco lo vede, e una regressione che lo
        #    togliesse non farebbe fallire niente.
        print(f"   AMMESSO dopo {ms:.0f} ms"
              + ("   ⭐ il secondo fisso c'e'" if ms >= 1000 else
                 "   ⛔ MENO DI UN SECONDO: §4.4-bis violata"))
        if ms < 1000:
            return 1

        # ── ATTACCA ─────────────────────────────────────────────────────────
        b = inquadra(T["ATTACCA"],
                     struct.pack("!IIII", a.larghezza, a.altezza,
                                 a.larghezza, a.altezza) + s(a.disposizione))
        cli.manda(b)
        reg.aggiungi(CLIENT, b)
        nome, corpo, grezzo = await attendi(cli, "SESSIONE")
        reg.aggiungi(SERVER, grezzo)
        stato_s = corpo[0]
        lar, alt = struct.unpack("!II", corpo[1:9])
        n = struct.unpack("!H", corpo[9:11])[0]
        desktop = corpo[11:11 + n].decode()
        print(f"   ⭐ SESSIONE: stato={stato_s} tela={lar}x{alt} desktop={desktop}")

        if a.registra:
            reg.scrivi(a.registra)
            print(f"   registrazione: {a.registra} ({len(reg.blocchi)} blocchi)")

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
            print(f"   resto attaccato per {a.resta} s")
            await asyncio.sleep(a.resta)
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
