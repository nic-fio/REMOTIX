#!/usr/bin/env python3
"""01-b2-cliente-aioquic.py — the test client, and the environment check of B2.

    python3 01-b2-cliente-aioquic.py [https://192.168.0.2:7447/rcp/1] [expected :status]
    python3 01-b2-cliente-aioquic.py https://192.168.0.2:7447/rcp/9 404
    python3 01-b2-cliente-aioquic.py https://192.168.0.2:7448/rcp/1 200 --senza-eco

---------------------------------------------------------------------------
⛔⭐ AGAINST THE PRODUCT YOU USE `--senza-eco`, AND IT IS NOT A CONVENIENCE

*Added on 11 Aug 2026, and the defect it avoids has already cost a
morning.*

This client sends `ciao` on a stream and waits for it to come back identical.
⛔ **The echo exists only in the B2 graft**, which was a fifty-line server
made to send the bytes back.  The **product** speaks RCP: on that first
stream it expects a `CIAO`, and to a lowercase `ciao` it answers as it should
— that is, by not sending it back.

⚠ It is exactly the red of the morning of 10 Aug, the one that had been taken
  for a certificate defect: *"the red was the PROBE's, not the
  certificate's: it sent `ciao` and waited for the B2 echo, which with RCP
  grafted on no longer exists"* (`FASI.md` §01-filo-nudo, line of B3).  Without
  this option the same red would show up again against the product, and would
  look like a server defect.

⭐ With `--senza-eco` the program stops where what it can test ends:
  **the WebTransport session opened on that path, with that
  `:status`**.  What happens AFTER the CONNECT belongs to RCP, and B3 and
  B5 test it — not this file.

---------------------------------------------------------------------------
⛔ WHAT IT MEASURES, AND ABOVE ALL WHAT IT DOES NOT MEASURE

This program opens a WebTransport session **without a browser**.  It serves to
separate two causes that, seen from the page, look the same:

    the session does not open  =  "the server cannot hold it"
                               or "the browser does not accept it"

If this client connects and the page does not, the defect is **in the browser
or in the certificate**, not in the server nor in the network.  If not even
this one connects, there is no point looking at any browser.

⛔ BUT IT DOES NOT REPLACE THE MEASUREMENT WITH A BROWSER, AND BELIEVING SO
   WOULD BE **E10** — a green test on the wrong client, which is the form of
   error that cost v1 the most.  The differences that count:

     - a browser verifies the certificate with `serverCertificateHashes`,
       that is by comparing **the fingerprint**; here verification is skipped
       entirely (`verify_mode = CERT_NONE`).  ⚠ So this client **does not
       prove** that the published fingerprint is right: it is precisely cause
       no. 2 of the three false reds, and it stays uncovered;
     - a browser enforces the 14-day cap; here nobody enforces it;
     - a browser picks the transport parameters by itself (`RCP.md` §2.3).

   Hence: a green here is **necessary, not sufficient**.

---------------------------------------------------------------------------
⭐ AND THE SECOND JOB, WHICH IS THE ONE THAT LASTS

This file is the seed of the **test client** of `PIANO.md` §1.1 — the
second reader of `RCP.md`, in a language different from the server's and the
page's.  Its value is not "it passes": it is that whoever writes it reads the
specification and **has to choose** where the specification allows two
readings.  Those choices go into "what did NOT work", and they are defects of
the document.

⛔ Whoever grows it does not look at the C nor at the page (rule B9).
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
        # ⛔ The client SAYS what it receives, at both levels.
        #    The first round of 9 Aug 2026 timed out waiting for the return
        #    while the server declared it had sent it: without these two
        #    lines there was no way of knowing whether the bytes did not
        #    arrive at all or arrived and nobody recognised them —
        #    which are two defects in two different places.
        if type(event).__name__ == "StreamDataReceived":
            print(f"   [quic] stream {event.stream_id}: {len(event.data)} bytes")
            # ⛔ AND HERE THE RETURN IS READ, AT THE QUIC LEVEL.  It is not laziness:
            #
            #    `[R]` aioquic 1.2's `H3Connection.create_webtransport_stream`
            #    writes the WebTransport stream header and **does not
            #    register the stream for receiving**.  So the bytes coming back
            #    on that stream arrive — they can be seen just above — and the H3
            #    level emits no `WebTransportStreamDataReceived`.
            #
            #    It is an asymmetry of the library: it can CREATE a WebTransport
            #    stream and cannot RECOGNISE it when it answers.  Whoever grows
            #    the test client (B9) will trip over it again, and that is why
            #    it is written here instead of in the memory of whoever
            #    saw it.
            #
            #    ⚠ The return is therefore read at the QUIC level, declaring it —
            #      we do not pretend the H3 level recognised it.
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


async def principale(url: str, atteso: str = "200", eco: bool = True) -> int:
    u = urlparse(url)
    autorita = f"{u.hostname}:{u.port or 443}"

    conf = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        max_datagram_frame_size=65536,
    )
    # ⛔ Declared, not hidden: here the certificate is NOT verified.  A
    #    browser verifies it by fingerprint, and that difference is written at
    #    the top of this file so that nobody reads a green from here as a
    #    green from there.
    conf.verify_mode = ssl.CERT_NONE

    print(f"== test client -> {url}")
    print(f"   authority: {autorita}   path: {u.path}")
    print("   ⚠ certificate NOT verified (see the file header)\n")

    async with connect(u.hostname, u.port or 443, configuration=conf,
                       create_protocol=ClienteWebTransport) as cliente:
        await cliente.wait_connected()
        print("   QUIC/HTTP3 connection established")

        cliente.apri_sessione(autorita, u.path or "/")
        stato = await asyncio.wait_for(cliente.accettata, timeout=8)
        print(f"   answer to the extended CONNECT: :status = {stato}")

        # ⛔ THE REFUSAL IS MEASURED ON THE NUMBER, NOT ON "it went badly" — R8.8.
        #
        #    The wrong-path bench concluded "REFUSED, as §2.2 requires" from a
        #    non-zero exit code.  But this program exits 1 for ANY `:status`
        #    other than 200 and 2 for ANY exception: a CONNECT timeout, filtered
        #    UDP, an already dead server and a traceback all gave the same
        #    green.  ⛔ And `RCP.md` §2.2 does not ask for "not 200": it asks
        #    for **404** (finding R1.24).
        #
        # ⭐ The number passed under our eyes and was not captured: now the
        #    caller says which one it expects, and the bench does the comparison.
        if atteso != "200":
            if stato == atteso:
                print(f"\n   ✅ refused with :status {stato}, as expected")
                return 0
            if stato == "200":
                print(f"\n   ⛔ ACCEPTED (200) where {atteso} was expected:"
                      " the server does not check the path")
                return 1
            print(f"\n   ⛔ refused, but with {stato} instead of {atteso}:"
                  " it is a refusal that RCP.md §2.2 does not provide for")
            return 1
        if stato != "200":
            print(f"\n   ⛔ the session was NOT accepted (expected 200, got {stato})")
            return 1
        print("   ⭐ WebTransport session ACCEPTED")

        # ⛔ AND HERE WE STOP, IF NO ECHO IS TO BE EXPECTED.  The verdict
        #    says what it proves — "the session opened on this
        #    path" — and does NOT stretch to a claim that this
        #    program is not able to support.  The file header
        #    explains why against the product it is the only honest reading.
        if not eco:
            print("\n   ✅ session open on", u.path,
                  "— the echo was NOT requested (--senza-eco)")
            print("   ⚠ what travels after the CONNECT is RCP, and B3 and B5"
                  " test it: not this file")
            return 0

        # ⛔ "Accepted" is not enough: bytes are sent and we wait for them to
        #    come back.  A session that opens and carries nothing is the form of
        #    green this bench exists not to produce.
        cliente.manda_byte(b"ciao")
        dati = await asyncio.wait_for(cliente.tornato, timeout=8)
        print(f"   round trip on stream: {dati!r}")
        if dati == b"ciao":
            print("\n   ✅ the bytes come back identical — server and network are fine")
            return 0
        print("\n   ⛔ the bytes come back DIFFERENT")
        return 1


if __name__ == "__main__":
    # ⚠ `--senza-eco` is removed before reading the positionals, so the usual
    #   order of the arguments keeps holding.
    argomenti = [x for x in sys.argv[1:] if x != "--senza-eco"]
    eco = "--senza-eco" not in sys.argv[1:]
    url = argomenti[0] if len(argomenti) > 0 else "https://192.168.0.2:7447/rcp/1"
    # ⚠ The second argument is the EXPECTED `:status`: without it, it is 200 and
    #   the usual road holds.  With "404" the program tests the check that says
    #   NO, and an arbitrary failure no longer passes for a refusal (R8.8).
    atteso = argomenti[1] if len(argomenti) > 1 else "200"
    try:
        sys.exit(asyncio.run(principale(url, atteso, eco)))
    except Exception as e:
        print(f"\n   ⛔ failed: {type(e).__name__}: {e}")
        sys.exit(2)
