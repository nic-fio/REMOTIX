#!/usr/bin/env python3
"""01-b2-aioquic-client.py — the test client, and the environment check of B2.

    python3 01-b2-aioquic-client.py [https://192.168.0.2:7447/rcp/1] [expected :status]
    python3 01-b2-aioquic-client.py https://192.168.0.2:7447/rcp/9 404
    python3 01-b2-aioquic-client.py https://192.168.0.2:7448/rcp/1 200 --no-echo
    python3 01-b2-aioquic-client.py https://127.0.0.1:7547/rcp/1 200 --rebind [--verbose]

⭐ `--rebind` (24 Oct 2026, the live test of the §2.3 migration): once the session is open the client changes its
SOURCE PORT as a NAT rebinding does — a new UDP socket on another local port, the same protocol object
(`client._transport` replaced) — sends bytes on a new WebTransport stream and COUNTS for 5 s the datagrams that arrive on
the new port and, apart, those still arriving on the old socket (not given to the client).  «REBIND OK» only if
at least one arrives on the NEW port; else «REBIND FAIL: <reason>».  The server's log must
then say «MOVED to» (that is the script's check, `migrazione-dal-vivo.sh`).

---------------------------------------------------------------------------
⛔⭐ AGAINST THE PRODUCT YOU USE `--no-echo`, AND IT IS NOT A CONVENIENCE

*Added on 11 Aug 2026, and the defect it avoids has already cost a
morning.*

This client sends `ciao` on a stream and waits for it to come back identical.
⛔ **The echo exists only in the B2 graft**, which was a fifty-line server
made to send the bytes back.  The **product** speaks RCP: on that first
stream it expects a `HELLO`, and to a lowercase `ciao` it answers as it should
— that is, by not sending it back.

⚠ It is exactly the red of the morning of 10 Aug, the one that had been taken
  for a certificate defect: *"the red was the PROBE's, not the
  certificate's: it sent `ciao` and waited for the B2 echo, which with RCP
  grafted on no longer exists"* (`PHASES.md` §01-filo-nudo, line of B3).  Without
  this option the same red would show up again against the product, and would
  look like a server defect.

⭐ With `--no-echo` the program stops where what it can test ends:
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

This file is the seed of the **test client** of `PLAN.md` §1.1 — the
second reader of `RCP.md`, in a language different from the server's and the
page's.  Its value is not "it passes": it is that whoever writes it reads the
specification and **has to choose** where the specification allows two
readings.  Those choices go into "what did NOT work", and they are defects of
the document.

⛔ Whoever grows it does not look at the C nor at the page (rule B9).
"""
import asyncio
import socket
import ssl
import sys
import time
from urllib.parse import urlparse

from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.h3.events import HeadersReceived, WebTransportStreamDataReceived
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent


class ClientWebTransport(QuicConnectionProtocol):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = H3Connection(self._quic, enable_webtransport=True)
        self.accepted = asyncio.get_event_loop().create_future()
        self.returned = asyncio.get_event_loop().create_future()
        self._session = None
        self._stream_wt = None

    def open_session(self, authority: str, fpath: str) -> int:
        sid = self._quic.get_next_available_stream_id(is_unidirectional=False)
        self._session = sid
        self._http.send_headers(
            sid,
            [
                (b":method", b"CONNECT"),
                (b":protocol", b"webtransport"),
                (b":scheme", b"https"),
                (b":authority", authority.encode()),
                (b":path", fpath.encode()),
                (b"origin", f"https://{authority}".encode()),
            ],
        )
        self.transmit()
        return sid

    def send_byte(self, data: bytes) -> None:
        sid = self._http.create_webtransport_stream(self._session, is_unidirectional=False)
        self._stream_wt = sid
        self._quic.send_stream_data(sid, data, end_stream=False)
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
            if event.stream_id == self._stream_wt and not self.returned.done():
                self.returned.set_result(event.data)
        for ev in self._http.handle_event(event):
            print(f"   [h3]   {type(ev).__name__}")
            if isinstance(ev, HeadersReceived):
                state = dict(ev.headers).get(b":status", b"?").decode()
                if not self.accepted.done():
                    self.accepted.set_result(state)
            elif isinstance(ev, WebTransportStreamDataReceived):
                if not self.returned.done():
                    self.returned.set_result(ev.data)


REBIND_WAIT_S = 5.0


async def rebind(client, verbose=False):
    """changes the source port; (old transport, ok, reason).  OK only if datagrams ARRIVE ON THE NEW PORT:
    the server must answer where the client now is.  What still arrives on the OLD socket is counted apart
    and NOT given to the client (it would otherwise keep the session alive without any migration)."""
    loop = asyncio.get_running_loop()
    old = client._transport
    counts = {"new": 0, "old": 0}
    to_client = client.datagram_received            # the library's own handler

    class NewPath(asyncio.DatagramProtocol):
        def connection_made(self, transport):
            client.connection_made(transport)       # client._transport = the new transport

        def datagram_received(self, data, addr):
            counts["new"] += 1
            to_client(data, addr)

    def old_path(data, addr):                       # the old socket's protocol is `client`: this replaces its handler
        counts["old"] += 1

    sock = socket.socket(socket.AF_INET6, socket.SOCK_DGRAM)       # as aioquic's own connect(): dual stack
    sock.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 0)
    sock.bind(("::", 0, 0, 0))
    sock.setblocking(False)
    before = old.get_extra_info("sockname")
    await loop.create_datagram_endpoint(NewPath, sock=sock)
    client.datagram_received = old_path             # from now on nothing from the old socket reaches the client
    after = client._transport.get_extra_info("sockname")
    print(f"   source port {before[1]} -> {after[1]}")
    if after[1] == before[1]:
        return old, False, "the source port did not change"
    # Keep the connection alive with QUIC PINGs, NOT with stream bytes: raw bytes on a new stream are read by
    # the server as RCP (kind "re", huge length) -> dismiss "message over 1 MiB" -> connection closed before
    # the path validation ends, so the migration would never be seen (false REBIND OK).
    t_end = loop.time() + REBIND_WAIT_S
    uid = 1
    while loop.time() < t_end:
        try:
            client._quic.send_ping(uid)
            client.transmit()
        except Exception:  # noqa: BLE001
            break
        uid += 1
        await asyncio.sleep(min(0.5, max(0.0, t_end - loop.time())))
    print(f"   datagrammi sul nuovo percorso: {counts['new']}, sul vecchio: {counts['old']}")
    ce = getattr(client._quic, "_close_event", None)
    if verbose:
        print(f"   close_event after {REBIND_WAIT_S:.0f} s: {ce!r}")
    if counts["new"] > 0 and ce is None:
        return old, True, f"{counts['new']} datagrams arrived on the new port, connection still alive"
    if counts["new"] > 0:
        return old, False, (f"{counts['new']} datagrams on the new port but the connection was closed"
                            f" ({ce.error_code}: {ce.reason_phrase!r})")
    return old, False, (f"no datagram on the new port in {REBIND_WAIT_S:.0f} s (old port: {counts['old']})"
                        + (f"; the connection was closed ({ce.error_code}: {ce.reason_phrase!r})" if ce else ""))


rebind_old = []        # the transport left behind by --rebind: closed after the connection


async def main(url: str, expected: str = "200", echo: bool = True, do_rebind: bool = False,
               verbose: bool = False) -> int:
    u = urlparse(url)
    authority = f"{u.hostname}:{u.port or 443}"

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
    print(f"   authority: {authority}   path: {u.path}")
    print("   ⚠ certificate NOT verified (see the file header)\n")

    async with connect(u.hostname, u.port or 443, configuration=conf,
                       create_protocol=ClientWebTransport) as client:
        await client.wait_connected()
        print("   QUIC/HTTP3 connection established")

        client.open_session(authority, u.path or "/")
        state = await asyncio.wait_for(client.accepted, timeout=8)
        print(f"   answer to the extended CONNECT: :status = {state}")

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
        if expected != "200":
            if state == expected:
                print(f"\n   ✅ refused with :status {state}, as expected")
                return 0
            if state == "200":
                print(f"\n   ⛔ ACCEPTED (200) where {expected} was expected:"
                      " the server does not check the path")
                return 1
            print(f"\n   ⛔ refused, but with {state} instead of {expected}:"
                  " it is a refusal that RCP.md §2.2 does not provide for")
            return 1
        if state != "200":
            print(f"\n   ⛔ the session was NOT accepted (expected 200, got {state})")
            return 1
        print("   ⭐ WebTransport session ACCEPTED")

        if do_rebind:
            old, ok, why = await rebind(client, verbose)
            print(("REBIND OK: " if ok else "REBIND FAIL: ") + why)
            rebind_old.append(old)
            return 0 if ok else 1

        # ⛔ AND HERE WE STOP, IF NO ECHO IS TO BE EXPECTED.  The verdict
        #    says what it proves — "the session opened on this
        #    path" — and does NOT stretch to a claim that this
        #    program is not able to support.  The file header
        #    explains why against the product it is the only honest reading.
        if not echo:
            print("\n   ✅ session open on", u.path,
                  "— the echo was NOT requested (--no-echo)")
            print("   ⚠ what travels after the CONNECT is RCP, and B3 and B5"
                  " test it: not this file")
            return 0

        # ⛔ "Accepted" is not enough: bytes are sent and we wait for them to
        #    come back.  A session that opens and carries nothing is the form of
        #    green this bench exists not to produce.
        client.send_byte(b"ciao")
        data = await asyncio.wait_for(client.returned, timeout=8)
        print(f"   round trip on stream: {data!r}")
        if data == b"ciao":
            print("\n   ✅ the bytes come back identical — server and network are fine")
            return 0
        print("\n   ⛔ the bytes come back DIFFERENT")
        return 1


if __name__ == "__main__":
    # ⚠ `--no-echo` is removed before reading the positionals, so the usual
    #   order of the arguments keeps holding.
    call_args = [x for x in sys.argv[1:] if x not in ("--no-echo", "--rebind", "--verbose")]
    echo = "--no-echo" not in sys.argv[1:]
    url = call_args[0] if len(call_args) > 0 else "https://192.168.0.2:7447/rcp/1"
    # ⚠ The second argument is the EXPECTED `:status`: without it, it is 200 and
    #   the usual road holds.  With "404" the program tests the check that says
    #   NO, and an arbitrary failure no longer passes for a refusal (R8.8).
    expected = call_args[1] if len(call_args) > 1 else "200"
    try:
        rc = asyncio.run(main(url, expected, echo, "--rebind" in sys.argv[1:], "--verbose" in sys.argv[1:]))
        for t in rebind_old:
            t.close()
        sys.exit(rc)
    except Exception as e:
        print(f"\n   ⛔ failed: {type(e).__name__}: {e}")
        sys.exit(2)
