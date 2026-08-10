#!/usr/bin/env python3
"""01-b2-sonda-impostazioni.py — che cosa dichiara un server HTTP/3 sul filo.

    python3 01-b2-sonda-impostazioni.py --porta 7447 --etichetta ngtcp2 --atteso si
    python3 01-b2-sonda-impostazioni.py --porta 7449 --etichetta quiche --atteso no

---------------------------------------------------------------------------
⛔ CHE COSA MISURA, E PERCHE' PRIMA DEL COLLANTE

Una cosa sola: **il server dichiara WebTransport?**  Cioe' manda, nel suo
frame SETTINGS, almeno una delle due impostazioni con cui un server dice a un
browser «io WebTransport lo parlo»:

    0x2b603742  SETTINGS_ENABLE_WEBTRANSPORT   bozza 02   (la cerca aioquic)
    0xc671706a  SETTINGS_WT_MAX_SESSIONS       bozza 07+  (la cercano i browser)

⭐ E' la regola nata dalle 333 righe buttate su `lsquic`: **si prova per prima
   la cosa che puo' uccidere la candidata**, prima di scrivere il collante.
   Senza quella dichiarazione un browser non apre la sessione, e non c'e'
   riga di codice nostro che possa rimediare.

---------------------------------------------------------------------------
⛔ IL DENOMINATORE: SI LEGGE IL FILO, NON LA CONFIGURAZIONE

La misura e' `H3Connection.received_settings` di `aioquic` — cioe' **quel che
il server ha davvero spedito**, non quel che il suo codice dice di voler
spedire.  ⚠ La distinzione e' costata mezza giornata il 10 agosto 2026: la
sonda dell'SNI leggeva la configurazione del CLIENTE e la chiamava «quel che
e' andato sul filo», e le sue due gambe misuravano la stessa cosa credendo di
misurarne due opposte (`LEZIONI.md` §1.9, corollario della quarta regola).

⛔ E la sonda stampa **tutte** le impostazioni ricevute, non solo quelle che
   cerca: un elenco vuoto e un elenco senza le due che interessano sono due
   fatti diversi, e il primo e' un difetto del banco.
"""
import argparse
import asyncio
import ssl
import sys

from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent

# I nomi, perche' un numero esadecimale in un registro non dice niente a
# nessuno fra sei mesi.
NOMI = {
    0x01: "QPACK_MAX_TABLE_CAPACITY",
    0x06: "MAX_FIELD_SECTION_SIZE",
    0x07: "QPACK_BLOCKED_STREAMS",
    0x08: "ENABLE_CONNECT_PROTOCOL   (RFC 9220, la CONNECT estesa)",
    0x33: "H3_DATAGRAM               (RFC 9297)",
    0x276: "H3_DATAGRAM_00            (bozza vecchia)",
    0x2B603742: "⭐ ENABLE_WEBTRANSPORT     (bozza 02)",
    0xC671706A: "⭐ WT_MAX_SESSIONS         (bozza 07+, quella dei browser)",
}

WEBTRANSPORT = (0x2B603742, 0xC671706A)


class Ascoltatore(QuicConnectionProtocol):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = H3Connection(self._quic, enable_webtransport=True)
        self.arrivate = asyncio.get_event_loop().create_future()

    def quic_event_received(self, event: QuicEvent) -> None:
        for _ in self._http.handle_event(event):
            pass
        imp = self._http.received_settings
        if imp is not None and not self.arrivate.done():
            self.arrivate.set_result(imp)


async def principale(a) -> int:
    conf = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        max_datagram_frame_size=65536,
    )
    conf.verify_mode = ssl.CERT_NONE

    print(f"== le impostazioni di  {a.indirizzo}:{a.porta}   ({a.etichetta})")
    print(f"   atteso: dichiara WebTransport = {a.atteso}")
    print()

    try:
        async with connect(a.indirizzo, a.porta, configuration=conf,
                           create_protocol=Ascoltatore) as cliente:
            await asyncio.wait_for(cliente.wait_connected(), timeout=a.attesa)
            imp = await asyncio.wait_for(cliente.arrivate, timeout=a.attesa)
    except Exception as e:  # noqa: BLE001 — il tipo dell'errore E' la misura
        print(f"   ⛔ non si arriva alle impostazioni: {type(e).__name__}: {e}")
        print("   ⚠ Questo NON e' un verdetto sulla libreria: e' un verdetto sul")
        print("     banco.  Il server non e' in ascolto, o la porta e' un'altra.")
        return 3

    # ⛔ Il denominatore: quante ne sono arrivate, e QUALI.  Un elenco vuoto e
    #    un elenco senza le due che cerchiamo sono due fatti diversi.
    print(f"   impostazioni ricevute: {len(imp)}")
    if not imp:
        print("   ⛔ NESSUNA impostazione: il server non ha mandato un SETTINGS,")
        print("      oppure la sonda non l'ha letto.  Nessun verdetto da qui.")
        return 3
    for k, v in sorted(imp.items()):
        print(f"      {k:#012x}  = {v:<6}  {NOMI.get(k, '(sconosciuta)')}")

    trovate = [k for k in WEBTRANSPORT if imp.get(k)]
    print()
    print("== Verdetto")
    if trovate:
        print(f"   ⭐ {a.etichetta} DICHIARA WebTransport: "
              + ", ".join(NOMI[k].strip('⭐ ') for k in trovate))
        dichiara = "si"
    else:
        print(f"   ⛔ {a.etichetta} NON dichiara WebTransport.")
        print("      Nessuna delle due impostazioni e' sul filo, quindi un browser")
        print("      non aprira' la sessione — e non c'e' riga di codice NOSTRO")
        print("      che possa rimediare: quel frame lo scrive la libreria.")
        dichiara = "no"

    if dichiara == a.atteso:
        print(f"\n   ✅ come atteso ({a.atteso})")
        return 0
    print(f"\n   ⛔ NON come atteso: atteso '{a.atteso}', misurato '{dichiara}'"
          " — va scritto perche'")
    return 1


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="il server dichiara WebTransport?")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--etichetta", default="candidata")
    p.add_argument("--atteso", choices=("si", "no"), default="si")
    p.add_argument("--attesa", type=float, default=8.0)
    a = p.parse_args()
    try:
        sys.exit(asyncio.run(principale(a)))
    except KeyboardInterrupt:
        sys.exit(130)
