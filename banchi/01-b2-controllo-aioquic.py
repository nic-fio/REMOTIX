#!/usr/bin/env python3
"""01-b2-controllo-aioquic.py — il CONTROLLO POSITIVO del banco B2.

    python3 01-b2-controllo-aioquic.py [porta]        predefinita: 7447

---------------------------------------------------------------------------
PERCHE' ESISTE, E PERCHE' PRIMA DELLE CANDIDATE

B2 deve dire se una candidata regge una sessione WebTransport aperta da un
browser vero.  ⛔ Ma «la candidata non apre la sessione» e «il banco non sa
aprirne nessuna» hanno esattamente lo stesso aspetto: pagina che gira,
sessione che non si stabilisce, nessun errore utile.

Le tre cause che producono quel sintomo identico, e che nessuna misura sulla
candidata distingue:

  - la porta UDP 7447 e' filtrata (il TCP risponde lo stesso);
  - l'impronta pubblicata nella pagina non e' quella del certificato servito;
  - il certificato della sessione supera i 14 giorni, e il browser lo rifiuta.

E' il rilievo R3.17 della revisione del banco: `C2` provava solo «nessuno in
ascolto», che e' il caso facile.  ⭐ Questo programma toglie di mezzo tutte e
tre in un colpo: e' un'implementazione WebTransport che NON e' una candidata,
quindi se la sessione non si apre nemmeno qui, il difetto e' dell'ambiente e
nessun verdetto sulle candidate vale.

⚠ E NON e' il prodotto, e non lo diventera' mai: e' Python, e il server e'
in C (`DECISIONI.md` §6.3).  Il suo secondo mestiere e' un altro — B9, il
CLIENTE DI PROVA, cioe' il secondo lettore di `RCP.md` in un linguaggio
diverso dal server e dalla pagina.

`[M]` 9 agosto 2026: aioquic 1.2.0 porta WebTransport — 29 occorrenze nel
modulo h3, l'evento `WebTransportStreamDataReceived`, e
`create_webtransport_stream`.  Era la `[?]` del rilievo R3.21, e se fosse
stata «no» sarebbe caduto l'arbitro.
---------------------------------------------------------------------------
"""
import asyncio
import sys
from pathlib import Path

from aioquic.asyncio import QuicConnectionProtocol, serve
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import (
    DatagramReceived,
    HeadersReceived,
    WebTransportStreamDataReceived,
)
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import ProtocolNegotiated, QuicEvent

CERTIFICATI = Path("/media/REMOTIX/b2-certificati")
# ⛔ Il percorso e' quello di `RCP.md` §2.2: l'identita' del protocollo vive
#    li', al posto dell'ALPN che una pagina non puo' scegliere.  Un percorso
#    diverso si rifiuta con 404 — ed e' §3 applicata al primo byte.
PERCORSO = "/rcp/1"


def registra(*cose):
    print(*cose, flush=True)


class ControlloWebTransport(QuicConnectionProtocol):
    """Accetta una sessione WebTransport su /rcp/1 e rimanda indietro i byte."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = None
        self._sessioni = set()

    def quic_event_received(self, event: QuicEvent) -> None:
        if isinstance(event, ProtocolNegotiated):
            # ⚠ `enable_webtransport=True` e' la riga che accende tutto: senza,
            #   aioquic non annuncia SETTINGS_WT_MAX_SESSIONS e il browser non
            #   prova nemmeno la CONNECT estesa.
            self._http = H3Connection(self._quic, enable_webtransport=True)
            registra("  connessione stabilita, ALPN:", event.alpn_protocol)

        if self._http is None:
            return

        for ev in self._http.handle_event(event):
            self._gestisci(ev)

    def _gestisci(self, ev) -> None:
        if isinstance(ev, HeadersReceived):
            intestazioni = dict(ev.headers)
            metodo = intestazioni.get(b":method", b"").decode()
            protocollo = intestazioni.get(b":protocol", b"").decode()
            percorso = intestazioni.get(b":path", b"").decode()
            registra(f"  richiesta: {metodo} {percorso} (:protocol={protocollo or '-'})")

            if metodo == "CONNECT" and protocollo == "webtransport":
                if percorso != PERCORSO:
                    # ⛔ `RCP.md` §2.2: un percorso sconosciuto si rifiuta con
                    #    404, e si scrive nel registro.  Non si indovina.
                    registra(f"  ⛔ percorso sconosciuto {percorso!r} -> 404")
                    self._http.send_headers(ev.stream_id, [(b":status", b"404")], end_stream=True)
                else:
                    registra("  ⭐ SESSIONE WEBTRANSPORT ACCETTATA")
                    self._http.send_headers(ev.stream_id, [(b":status", b"200")])
                    self._sessioni.add(ev.stream_id)
            else:
                registra("  richiesta non-WebTransport -> 400")
                self._http.send_headers(ev.stream_id, [(b":status", b"400")], end_stream=True)
            self.transmit()

        elif isinstance(ev, WebTransportStreamDataReceived):
            registra(f"  stream {ev.stream_id}: {len(ev.data)} byte -> rimando indietro")
            self._http._quic.send_stream_data(ev.stream_id, ev.data, end_stream=ev.stream_ended)
            self.transmit()

        elif isinstance(ev, DatagramReceived):
            registra(f"  datagram: {len(ev.data)} byte -> rimando indietro")
            self._http.send_datagram(ev.flow_id, ev.data)
            self.transmit()


async def principale(porta: int) -> None:
    conf = QuicConfiguration(
        is_client=False,
        alpn_protocols=H3_ALPN,
        # ⛔ I datagram DEVONO essere abilitati sulla connessione HTTP/3
        #    (`RCP.md` §2.2): senza, l'audio non esiste.  Qui servono a
        #    provare che il canale c'e'.
        max_datagram_frame_size=65536,
    )
    conf.load_cert_chain(CERTIFICATI / "sessione.pem", CERTIFICATI / "sessione.key")

    registra(f"== controllo positivo B2 — WebTransport su UDP {porta}{PERCORSO}")
    registra("   certificato: sessione.pem (13 giorni, ECDSA P-256)")
    registra("   in ascolto. Ctrl-C per fermare.\n")

    await serve("0.0.0.0", porta, configuration=conf, create_protocol=ControlloWebTransport)
    await asyncio.Future()


if __name__ == "__main__":
    try:
        asyncio.run(principale(int(sys.argv[1]) if len(sys.argv) > 1 else 7447))
    except KeyboardInterrupt:
        registra("\nfermato")
