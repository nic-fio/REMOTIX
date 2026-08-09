#!/usr/bin/env python3
"""01-b2-cliente-aioquic.py — il cliente di prova, e il controllo d'ambiente di B2.

    python3 01-b2-cliente-aioquic.py [https://192.168.0.2:7447/rcp/1]

---------------------------------------------------------------------------
⛔ CHE COSA MISURA, E SOPRATTUTTO CHE COSA NON MISURA

Questo programma apre una sessione WebTransport **senza un browser**.  Serve a
separare due cause che, viste dalla pagina, hanno lo stesso aspetto:

    la sessione non si apre  =  «il server non la regge»
                             o  «il browser non la accetta»

Se questo cliente si collega e la pagina no, il difetto e' **del browser o del
certificato**, non del server ne' della rete.  Se non si collega nemmeno
questo, non ha senso guardare nessun browser.

⛔ MA NON SOSTITUISCE LA MISURA CON UN BROWSER, E CREDERLO SAREBBE **E10** —
   una prova verde sul client sbagliato, che e' la forma d'errore che a v1 e'
   costata di piu'.  Le differenze che contano:

     - un browser verifica il certificato con `serverCertificateHashes`,
       cioe' confrontando **l'impronta**; qui si salta la verifica del tutto
       (`verify_mode = CERT_NONE`).  ⚠ Quindi questo cliente **non prova**
       che l'impronta pubblicata sia giusta: e' precisamente la causa n.2 dei
       tre falsi rossi, e resta scoperta;
     - un browser impone il tetto dei 14 giorni; qui non lo impone nessuno;
     - un browser sceglie da se' i parametri di trasporto (`RCP.md` §2.3).

   Da cui: un verde qui e' **necessario, non sufficiente**.

---------------------------------------------------------------------------
⭐ E IL SECONDO MESTIERE, CHE E' QUELLO CHE DURA

Questo file e' il germe del **cliente di prova** di `PIANO.md` §1.1 — il
secondo lettore di `RCP.md`, in un linguaggio diverso dal server e dalla
pagina.  Il suo valore non e' «passa»: e' che chi lo scrive legge la
specifica e **deve scegliere** dove la specifica ammette due letture.  Quelle
scelte vanno scritte in «che cosa NON ha funzionato», e sono difetti del
documento.

⛔ Chi lo fa crescere non guarda il C ne' la pagina (regola B9).
"""
import asyncio
import ssl
import sys
from urllib.parse import urlparse

from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import HeadersReceived, WebTransportStreamDataReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent


class ClienteWebTransport(QuicConnectionProtocol):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = H3Connection(self._quic, enable_webtransport=True)
        self.accettata = asyncio.get_event_loop().create_future()
        self.tornato = asyncio.get_event_loop().create_future()
        self._sessione = None
        self._stream_wt = None

    def apri_sessione(self, autorita: str, percorso: str) -> int:
        sid = self._quic.get_next_available_stream_id(is_unidirectional=False)
        self._sessione = sid
        self._http.send_headers(
            sid,
            [
                (b":method", b"CONNECT"),
                (b":protocol", b"webtransport"),
                (b":scheme", b"https"),
                (b":authority", autorita.encode()),
                (b":path", percorso.encode()),
                (b"origin", f"https://{autorita}".encode()),
            ],
        )
        self.transmit()
        return sid

    def manda_byte(self, dati: bytes) -> None:
        sid = self._http.create_webtransport_stream(self._sessione, is_unidirectional=False)
        self._stream_wt = sid
        self._quic.send_stream_data(sid, dati, end_stream=False)
        self.transmit()

    def quic_event_received(self, event: QuicEvent) -> None:
        # ⛔ Il cliente DICE che cosa riceve, a tutt'e due i livelli.
        #    Il primo giro del 9 agosto 2026 e' andato in timeout aspettando
        #    il ritorno mentre il server dichiarava di averlo spedito: senza
        #    queste due righe non c'era modo di sapere se i byte non
        #    arrivavano affatto o se arrivavano e nessuno li riconosceva —
        #    che sono due difetti in due posti diversi.
        if type(event).__name__ == "StreamDataReceived":
            print(f"   [quic] stream {event.stream_id}: {len(event.data)} byte")
            # ⛔ E QUI SI LEGGE IL RITORNO, AL LIVELLO QUIC.  Non e' pigrizia:
            #
            #    `[R]` `H3Connection.create_webtransport_stream` di aioquic 1.2
            #    scrive l'intestazione dello stream WebTransport e **non
            #    registra lo stream in ricezione**.  Quindi i byte che tornano
            #    su quello stream arrivano — si vedono qui sopra — e il livello
            #    H3 non emette nessun `WebTransportStreamDataReceived`.
            #
            #    E' un'asimmetria della libreria: sa CREARE uno stream
            #    WebTransport e non sa RICONOSCERLO quando risponde.  Chi fara'
            #    crescere il cliente di prova (B9) ci inciampera' di nuovo, e
            #    per questo sta scritto qui invece che nella memoria di chi
            #    l'ha visto.
            #
            #    ⚠ Il ritorno si legge dunque a livello QUIC, dichiarandolo —
            #      non si finge che il livello H3 l'abbia riconosciuto.
            if event.stream_id == self._stream_wt and not self.tornato.done():
                self.tornato.set_result(event.data)
        for ev in self._http.handle_event(event):
            print(f"   [h3]   {type(ev).__name__}")
            if isinstance(ev, HeadersReceived):
                stato = dict(ev.headers).get(b":status", b"?").decode()
                if not self.accettata.done():
                    self.accettata.set_result(stato)
            elif isinstance(ev, WebTransportStreamDataReceived):
                if not self.tornato.done():
                    self.tornato.set_result(ev.data)


async def principale(url: str) -> int:
    u = urlparse(url)
    autorita = f"{u.hostname}:{u.port or 443}"

    conf = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        max_datagram_frame_size=65536,
    )
    # ⛔ Dichiarato, non nascosto: qui NON si verifica il certificato.  Un
    #    browser lo verifica per impronta, e quella differenza e' scritta in
    #    cima a questo file perche' nessuno legga il verde di qui come un
    #    verde di la'.
    conf.verify_mode = ssl.CERT_NONE

    print(f"== cliente di prova -> {url}")
    print(f"   autorita: {autorita}   percorso: {u.path}")
    print("   ⚠ certificato NON verificato (vedi l'intestazione del file)\n")

    async with connect(u.hostname, u.port or 443, configuration=conf,
                       create_protocol=ClienteWebTransport) as cliente:
        await cliente.wait_connected()
        print("   connessione QUIC/HTTP3 stabilita")

        cliente.apri_sessione(autorita, u.path or "/")
        stato = await asyncio.wait_for(cliente.accettata, timeout=8)
        print(f"   risposta alla CONNECT estesa: :status = {stato}")
        if stato != "200":
            print(f"\n   ⛔ la sessione NON e' stata accettata (atteso 200, avuto {stato})")
            return 1
        print("   ⭐ sessione WebTransport ACCETTATA")

        # ⛔ «Accettata» non basta: si mandano byte e si aspetta che tornino.
        #    Una sessione che si apre e non trasporta niente e' la forma di
        #    verde che questo banco esiste per non produrre.
        cliente.manda_byte(b"ciao")
        dati = await asyncio.wait_for(cliente.tornato, timeout=8)
        print(f"   andata e ritorno su stream: {dati!r}")
        if dati == b"ciao":
            print("\n   ✅ i byte tornano identici — server e rete sono a posto")
            return 0
        print("\n   ⛔ i byte tornano DIVERSI")
        return 1


if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else "https://192.168.0.2:7447/rcp/1"
    try:
        sys.exit(asyncio.run(principale(url)))
    except Exception as e:
        print(f"\n   ⛔ fallito: {type(e).__name__}: {e}")
        sys.exit(2)
