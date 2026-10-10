#!/usr/bin/env python3
"""01-b2-sonda-trasporto.py — the transport parameters, read ON THE WIRE.

    python3 01-b2-sonda-trasporto.py --bersaglio innesto  --porta 7447 --idle-atteso 30000
    python3 01-b2-sonda-trasporto.py --bersaglio prodotto --porta 7448 --idle-atteso 30000
    python3 01-b2-sonda-trasporto.py --bersaglio controllo --porta 7449 \\
            --idle-atteso 60000 --credito-atteso 125 --bozze-attese 02

---------------------------------------------------------------------------
⛔ WHAT IT MEASURES, AND WHY WHAT WAS THERE WAS NOT ENOUGH

The properties that `FASI.md` §01-filo-nudo assigns to B2 "because they belong
to the library and no other bench looks at them":

    max_idle_timeout = 30 s imposed by the server   RCP.md §2.2
    datagrams enabled on the HTTP/3 connection      RCP.md §2.2
    at least 16 unidirectional streams of credit    RCP.md §2.3
      ⚠ here ONLY the initial credit is read — see the check
    the server MUST NOT offer 0-RTT                 RCP.md §2.3
    the server MUST NOT disable migration           RCP.md §2.3

⚠ **The first two were already "measured", and badly.**  On 10 Aug the server
  printed by itself `max_idle_timeout=30000ms max_datagram_frame_size=65536`, and
  that line was written into the documents as a measurement.  ⛔ But it is its
  CONFIGURATION, not the wire: it says what the server asked ngtcp2 for, not
  what reached the peer.  It is exactly the corollary of `LEZIONI.md`
  §1.9 born that same morning — *a denominator is read where the thing
  happens* — applied against a measurement of ours instead of against someone
  else's library.

⭐ This probe rereads them all from the **peer**, that is from where they are really seen.

---------------------------------------------------------------------------
⛔⭐ THE TARGET IS INSIDE EVERY LINE OF THE LOG — and this file demands it

*Added on 11 Aug 2026, and it is the reason this probe was
reopened.*

The six properties are `[M]` **on the graft** (`bsslserver` + the B2
grafts, port 7447).  The **product** (`remotix`, port 7448) is another server, and
of five of the six nothing is known: ⛔ **six numbers read on two different
servers, if the log does not say which, are six numbers that cannot be
lined up.**  Hence `--bersaglio`, which is **mandatory**, and the JSONL
line that every round writes.

⚠ And next to the target goes **the fingerprint of what was measured**
(`--impronta`): a rebuilt binary is another target with the same
name.  If the launcher does not pass it, `ignota` ends up in the log — which is
a piece of information, not a zero.

---------------------------------------------------------------------------
⛔ HOW THEY ARE READ, AND THE TOOL IS DECLARED

`aioquic` keeps only two of the received parameters (`_remote_max_idle_timeout`
and `_remote_max_datagram_frame_size`) and throws away the rest after using it.
To see `disable_active_migration` and the stream credit too, a **spy** is put on
the function that parses them — `pull_quic_transport_parameters` —
and the whole object is kept.

⚠ It is a tool that goes inside someone else's library, so it is **declared
  here** instead of hidden: if an aioquic update moves that
  function, the probe **finds nothing and says so**, instead of printing zeros.

0-RTT is seen somewhere else again: it is a **session ticket** with
`max_early_data_size`, and it arrives after the handshake.  We wait a moment
and look whether one has arrived.

---------------------------------------------------------------------------
⛔ AND THE PROPERTY THAT **CANNOT BE READ** FROM THE PEER, said here and not elsewhere

The properties of B2 are six.  This probe reads **five** of them.

    `allowPooling: false`  —  `RCP.md` §4.1-bis

⛔ It is not a parameter the server sends: it is a field of the `WebTransport`
object **that the page builds**, inside the browser.  On the wire there
is no byte that carries it, and no QUIC probe will ever be able to read it.  It is
read in the page source (`[R]`) or in the browser that runs it — not here.
⚠ Declaring it is information; deducing it from a green of this probe would be
**E1**, a reading that proves less than is attributed to it.
"""
import argparse
import asyncio
import json
import ssl
import sys
from datetime import datetime
from pathlib import Path

import aioquic.quic.connection as mod_conn
from aioquic.asyncio import connect
from aioquic.asyncio.protocol import QuicConnectionProtocol
from aioquic.h3.connection import H3_ALPN, H3Connection
from aioquic.quic.configuration import QuicConfiguration
from aioquic.quic.events import QuicEvent

# ⛔ H3_DATAGRAM (RFC 9297) — the HTTP/3 setting, which is NOT the QUIC
#    transport parameter.  Finding R8.11: here `max_datagram_frame_size`
#    (RFC 9221) was measured and called "datagrams on the HTTP/3
#    connection", which is what RCP.md §2.2 demands.  A server that
#    raised the transport parameter and did NOT announce H3_DATAGRAM passed the
#    check, and the audio datagrams would not leave — with the symptom
#    "looks like a network defect" of LEZIONI.md §2.2.
H3_DATAGRAM = 0x33

# ⛔ The TWO WebTransport declarations, and they are two because there are two
#    drafts in circulation.  `src/webtransport.c` sends both and says
#    why; here we check that they really are on the wire.
#
#      0x2b603742  SETTINGS_ENABLE_WEBTRANSPORT   draft 02  — aioquic looks for it
#      0xc671706a  SETTINGS_WT_MAX_SESSIONS       draft 07+ — browsers look for it
#
# ⚠ It is a BIG AND SILENT finding: a server that sent only one of them would
#   work with half of our tools and not with the other half, and the half that
#   works would be the wrong one to draw conclusions from.  The symptom, on the
#   side that gets it wrong, is "the session does not open" — which is the
#   same sentence as four other causes.
WT_BOZZA_02 = 0x2B603742
WT_BOZZA_07 = 0xC671706A
BOZZE = {"02": WT_BOZZA_02, "07": WT_BOZZA_07}

# ⚠ RFC 9220: without this, the extended CONNECT does not exist and WebTransport
#   over HTTP/3 cannot even begin.  `RCP.md` does not name it — so here it is
#   NOT a check against the referee, it is a declared READING: it is printed
#   because its absence alone would explain a "does not open".
ENABLE_CONNECT_PROTOCOL = 0x08

# ⛔ How many unidirectional streams HTTP/3 takes FOR ITSELF.  It is not a
#    believed constant: further down the ones our `H3Connection` really
#    opened are COUNTED, and the measured number is the one that
#    goes into the sum.  This only serves to say in the log what we
#    expected to count.
HTTP3_UNI_ATTESI = 3

# ---------------------------------------------------------------------------
# The spy on the transport parameters.
VISTI = {}
_originale = mod_conn.pull_quic_transport_parameters


def _spia(*a, **kw):
    p = _originale(*a, **kw)
    VISTI["parametri"] = p
    return p


mod_conn.pull_quic_transport_parameters = _spia

# The session tickets, that is the 0-RTT.
BIGLIETTI = []


def raccogli_biglietto(b):
    BIGLIETTI.append(b)


class Ascoltatore(QuicConnectionProtocol):
    """⛔ It serves ONLY to read the HTTP/3 SETTINGS.

    The probe connected with the HTTP/3 ALPN and **built no
    `H3Connection`**: so it read no SETTINGS, and the setting that
    §2.2 demands — `H3_DATAGRAM` — nobody looked at (R8.11).  The file
    next to it (`01-b2-sonda-impostazioni.py`) knows very well it is another thing:
    it lists it by name.
    """

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

    # ⛔ HOW MANY UNIDIRECTIONAL STREAMS HTTP/3 TOOK, COUNTED AND NOT BELIEVED.
    #
    #    `H3Connection` opens by itself the control channel and the two QPACK
    #    ones, and they NEVER close for the whole connection.  They are
    #    unidirectional client streams like all the others: they eat the same
    #    credit that `RCP.md` §2.3 reserves for RCP.
    #
    # ⚠ It is a count made on OUR client, not on the browser: it is written
    #   next to the number, and it is the reason the verdict on the credit
    #   carries the words "with this client".
    def uni_di_http3(self):
        ids = [
            getattr(self._http, "_local_control_stream_id", None),
            getattr(self._http, "_local_encoder_stream_id", None),
            getattr(self._http, "_local_decoder_stream_id", None),
        ]
        return [i for i in ids if i is not None]


async def principale(a) -> int:
    conf = QuicConfiguration(
        is_client=True,
        alpn_protocols=H3_ALPN,
        max_datagram_frame_size=65536,
    )
    conf.verify_mode = ssl.CERT_NONE

    print(f"== the transport parameters of {a.indirizzo}:{a.porta}")
    print(f"   ⛔ TARGET: {a.bersaglio}   ({a.etichetta})")
    print(f"   fingerprint of the target: {a.impronta}")
    print()

    impostazioni = None
    perche_niente_settings = None
    uni_h3 = []
    credito_corrente = None
    try:
        # ⚠ `session_ticket_handler` sits on `connect`, not on the
        #   configuration: they are two different places in two different modules.
        async with connect(a.indirizzo, a.porta, configuration=conf,
                           create_protocol=Ascoltatore,
                           session_ticket_handler=raccogli_biglietto) as cliente:
            await asyncio.wait_for(cliente.wait_connected(), timeout=a.attesa)
            # ⛔ The HTTP/3 SETTINGS is awaited and read: that is where
            #    `H3_DATAGRAM` (R8.11) and the two WebTransport declarations are.
            # ⚠ And "no SETTINGS arrived" remains a fact of its own, different
            #   from "it arrived and did not contain X": the why is kept, and further
            #   down it is printed instead of a number.
            try:
                impostazioni = await asyncio.wait_for(cliente.arrivate,
                                                      timeout=a.attesa)
            except Exception as e:  # noqa: BLE001
                perche_niente_settings = f"{type(e).__name__}: {e}"
            # ⚠ The session ticket arrives AFTER the handshake: without
            #   this wait, "no 0-RTT" would only be "I did not wait".
            await asyncio.sleep(a.attesa_biglietto)
            uni_h3 = cliente.uni_di_http3()
            # ⛔ The credit AS IT STANDS NOW, and it comes from the peer: `aioquic` raises
            #    `_remote_max_streams_uni` at every `MAX_STREAMS_UNI` received.
            #    If the server renews, a number higher than the initial one is seen
            #    here; if it does not renew, the same one is seen.
            credito_corrente = getattr(cliente._quic, "_remote_max_streams_uni",
                                       None)
    except Exception as e:  # noqa: BLE001
        print(f"   ⛔ cannot connect: {type(e).__name__}: {e}")
        print("   ⚠ verdict on the bench, not on the library.")
        scrivi_registro(a, esito="NON-COLLEGATO",
                        dettaglio=f"{type(e).__name__}: {e}", misure={},
                        controlli=[])
        return 3

    p = VISTI.get("parametri")
    if p is None:
        print("   ⛔ the spy caught nothing: `aioquic` has moved")
        print("      `pull_quic_transport_parameters`.  No number below")
        print("      would be valid, so none is printed.")
        scrivi_registro(a, esito="SPIA-CIECA", dettaglio="pull_quic_transport_"
                        "parameters is no longer where it was", misure={}, controlli=[])
        return 3

    idle = getattr(p, "max_idle_timeout", None)
    dgram = getattr(p, "max_datagram_frame_size", None)
    migr = getattr(p, "disable_active_migration", None)
    suni = getattr(p, "initial_max_streams_uni", None)
    sbidi = getattr(p, "initial_max_streams_bidi", None)

    # ⛔⭐ THE SUM THAT SEPARATES 19 FROM 16, and it is all in this line.
    #
    #    `initial_max_streams_uni` is a TOTAL.  HTTP/3 takes three of them
    #    (control + the two QPACK ones) from the first second and never gives
    #    them back.  What is left to RCP — the input stream, one for every
    #    clipboard transfer — is the total MINUS those.
    #
    #    §2.3 asks for "at least 16 AVAILABLE at any moment": the quantity
    #    it talks about is this one, not the total.
    consumati = len(uni_h3)
    disponibili = None if suni is None else suni - consumati

    print("   what the server SENT:")
    print(f"      max_idle_timeout           = {idle}")
    print(f"      max_datagram_frame_size    = {dgram}")
    print(f"      disable_active_migration   = {migr}")
    print(f"      initial_max_streams_uni    = {suni}   (TOTAL)")
    print(f"      initial_max_streams_bidi   = {sbidi}")
    print(f"      uni credit NOW             = {credito_corrente}"
          "   (initial + any MAX_STREAMS_UNI)")
    print()
    print("   what is left of it to RCP, and the sum is written out:")
    print(f"      uni streams taken by HTTP/3 = {consumati}   (counted: {uni_h3})")
    print(f"      available to RCP           = {suni} - {consumati} = {disponibili}")
    if impostazioni is None:
        print(f"      HTTP/3 SETTINGS            = none read"
              f"  ({perche_niente_settings})")
    else:
        print(f"      HTTP/3 SETTINGS            = {len(impostazioni)} settings")
        for chiave, nome in ((H3_DATAGRAM, "H3_DATAGRAM        (0x33)"),
                             (ENABLE_CONNECT_PROTOCOL,
                              "ENABLE_CONNECT_PROT (0x08)"),
                             (WT_BOZZA_02, "WT draft 02 (0x2b603742)"),
                             (WT_BOZZA_07, "WT draft 07 (0xc671706a)")):
            v = impostazioni.get(chiave, "absent")
            print(f"         {nome} = {v}")
    print(f"      session tickets            = {len(BIGLIETTI)}")
    for b in BIGLIETTI:
        print(f"         max_early_data_size = {getattr(b, 'max_early_data_size', None)}")
    print()

    # -----------------------------------------------------------------------
    # The checks, each with its expected value and its line of RCP.
    esiti = []

    def prova(nome, dove, passa, visto, atteso):
        esiti.append({"nome": nome, "dove": dove, "passa": bool(passa),
                      "visto": str(visto), "atteso": str(atteso)})
        segno = "OK " if passa else "NO "
        print(f"   {segno} {nome:38s} {dove}")
        print(f"       expected {atteso} · measured {visto}")

    prova("max_idle_timeout", "RCP.md §2.2",
          idle == a.idle_atteso, idle, a.idle_atteso)

    # ⛔ TWO DIFFERENT THINGS, TWO DIFFERENT CHECKS — finding R8.11.
    #
    #    `max_datagram_frame_size` is the TRANSPORT parameter (RFC 9221):
    #    it says the QUIC connection can carry datagrams.  `H3_DATAGRAM`
    #    (0x33, RFC 9297) is the HTTP/3 setting, and it is the one that
    #    `RCP.md` §2.2 demands — "datagrams MUST be enabled on the
    #    HTTP/3 connection".  The first was measured under the name of the second.
    prova("datagrams on the QUIC transport", "RFC 9221 (the foundations)",
          bool(dgram), dgram, "> 0")

    if impostazioni is None:
        prova("datagrams on HTTP/3 (H3_DATAGRAM)", "RCP.md §2.2",
              False, f"no SETTINGS read — {perche_niente_settings}",
              "0x33 present and non-zero")
    else:
        prova("datagrams on HTTP/3 (H3_DATAGRAM)", "RCP.md §2.2",
              bool(impostazioni.get(H3_DATAGRAM)),
              impostazioni.get(H3_DATAGRAM, "absent"),
              "0x33 present and non-zero")

    # ⛔⭐ THE TWO WEBTRANSPORT DRAFTS, AND HERE WE DECIDE WHAT A RED IS.
    #
    #    `--bozze-attese` says which are demanded from THIS target:
    #      · on the product and on the graft there are TWO (02 and 07): a server that
    #        sent only one would open the session with half of the tools
    #        and not with the other half;
    #      · on the positive control (`aioquic` acting as server) there is ONE only —
    #        aioquic 1.2 knows draft 02 and that is all `[R]`.  ⭐ And it is exactly the
    #        NEGATIVE CONTROL of this check: if, pointing the probe
    #        at aioquic, draft 07 turned out present, the check would not
    #        be able to say no and the greens on the other two targets would
    #        be worth nothing.
    attese = [b.strip() for b in a.bozze_attese.split(",") if b.strip()]
    for nome_bozza in ("02", "07"):
        chiave = BOZZE[nome_bozza]
        presente = bool(impostazioni.get(chiave)) if impostazioni else False
        if nome_bozza in attese:
            prova(f"WebTransport declared — draft {nome_bozza}",
                  "RCP.md §2 (the graft sends two)",
                  presente,
                  impostazioni.get(chiave, "absent") if impostazioni
                  else f"no SETTINGS — {perche_niente_settings}",
                  "present and non-zero")
        else:
            # It is not a check: it is a reading, and it is printed without a grade.
            visto = (impostazioni.get(chiave, "absent") if impostazioni
                     else "no SETTINGS")
            print(f"   --  draft {nome_bozza} not demanded from this target "
                  f"· read: {visto}")

    if impostazioni is not None:
        # ⚠ A reading, not a check: `RCP.md` does not name RFC 9220.  But its
        #   absence alone would explain a "the session does not open", and
        #   looking for it afterwards costs an evening.
        print(f"   --  ENABLE_CONNECT_PROTOCOL (RFC 9220, non-normative "
              f"reading) = {impostazioni.get(ENABLE_CONNECT_PROTOCOL, 'absent')}")

    # ⛔ The credit of unidirectional streams: §2.3 imposes at least 16 "at
    #    any moment", because the client opens an input stream and one for
    #    every clipboard transfer.  If it ran out, input would not leave
    #    at all and the symptom would be "the desktop does not respond".
    #
    # ⚠ AND THE NAME OF THE CHECK SAYS WHAT IT MEASURES — finding R8.12.
    #   `initial_max_streams_uni` is the credit the server grants
    #   AT OPENING, and says nothing about what happens afterwards: §2.3 is
    #   written exactly for the afterwards, and it is the form of defect a short
    #   bench does not see — it works for the first seconds and stops (LEZIONI.md
    #   §1.4).  This probe opens, reads a number and closes: it is the short bench
    #   against which that line was written.  ⛔ The credit "at any
    #   moment" is NOT measured here, and we say so instead of letting it be believed.
    #
    # ⛔⭐ AND THE CHECK IS ON THE AVAILABLE ONES, NOT ON THE TOTAL — 11 Aug 2026.
    #    Before, `suni >= 16` was checked, and with that check a server that
    #    declares 16 passed while 13 were left to RCP.  It is finding B-12,
    #    which `src/trasporto.c` has already cured by declaring 19: that 19 is
    #    READ here, and the verdict is given on the number §2.3 talks about.
    if disponibili is None:
        prova("uni credit AVAILABLE to RCP at opening",
              "RCP.md §2.3 (opening only)",
              False, "the peer did not send initial_max_streams_uni",
              f">= {a.credito_atteso}")
    else:
        prova("uni credit AVAILABLE to RCP at opening",
              "RCP.md §2.3 (opening only)",
              disponibili >= a.credito_atteso,
              f"{disponibili}  (= {suni} declared - {consumati} of HTTP/3)",
              f">= {a.credito_atteso}")

    # ⚠ And a check on the TOOL, not on the server: if HTTP/3 had not
    #   taken the three streams we expect, the sum above would be made
    #   with a wrong denominator — and it would be a credible and false number.
    prova("the tool counted the HTTP/3 streams",
          "check of the PROBE, not of the server",
          consumati == HTTP3_UNI_ATTESI, consumati, HTTP3_UNI_ATTESI)

    # ⛔ Migration: it is the reason QUIC was chosen — the
    #    phone moving from WiFi to mobile network.  The parameter is a
    #    switch that MUST stay off.
    prova("migration NOT disabled", "RCP.md §2.3",
          not migr, migr, "false or absent")

    # ⛔ 0-RTT: the data can be replayed, and the second RCP message is
    #    `CREDENZIALI`.
    #
    # ⭐ And this check had its POSITIVE control right away, from the
    #    target itself: at the first round the ngtcp2 example server
    #    sent **two tickets with max_early_data_size = 4294967295** `[M]`
    #    10 Aug 2026.  That is, the probe can see a 0-RTT turned on, because
    #    it saw one.  The green that follows is a green after a cure, not a
    #    green from a blind tool — which is the difference that counts.
    con_early = [b for b in BIGLIETTI
                 if getattr(b, "max_early_data_size", None)]
    prova("no 0-RTT", "RCP.md §2.3",
          not con_early, f"{len(con_early)} tickets with early data",
          "none")

    print()
    print("== Verdict")
    # ⛔ What these checks do NOT say, said here and not elsewhere: an
    #    "all of all" verdict that covers a property different from the one
    #    named is worse than a red (finding R8.12).
    print("   ⚠ NOT measured here: the stream credit \"at any moment\"")
    print("     (§2.3).  Above there is only the credit at opening; what")
    print("     happens when it runs out is seen by a bench that keeps the")
    print("     session alive and opens streams until the credit is exhausted.")
    print("   ⚠ NOT measured here: `allowPooling: false` (§4.1-bis) — it does not")
    print("     go over the wire, it is in the page.  It is read in the source or in")
    print("     the browser, and this probe knows nothing about it.")
    print(f"   ⚠ The {consumati} HTTP/3 streams are counted on THIS client")
    print("     (aioquic).  A browser could open more of them — for example")
    print("     a \"grease\" stream — and then the available ones would be fewer")
    print("     than the ones read here.  Nobody has measured it: `[?]`")
    if not BIGLIETTI:
        # ⛔ "No ticket" and "tickets without early data" are two different
        #    facts, and the green is the same.  Whoever reads must know which of the
        #    two they got: in the first case this round did not prove that the
        #    tool can see a 0-RTT turned on, and the positive control
        #    of that line remains the HISTORICAL one of 10 Aug (the graft before
        #    the cure, two tickets with max_early_data_size 4294967295).
        print("   ⚠ NO session ticket arrived: the green on \"no")
        print("     0-RTT\" comes from an absence, not from a ticket looked at.")
        print("     The positive control of that line remains the one of 10")
        print("     Aug on the graft, not this round.")

    falliti = [c["nome"] for c in esiti if not c["passa"]]
    misure = {
        "max_idle_timeout": idle,
        "max_datagram_frame_size": dgram,
        "disable_active_migration": migr,
        "initial_max_streams_uni": suni,
        "initial_max_streams_bidi": sbidi,
        "credito_uni_adesso": credito_corrente,
        "uni_presi_da_http3": consumati,
        "uni_disponibili_a_rcp": disponibili,
        "settings_http3": (None if impostazioni is None
                           else {hex(k): v for k, v in impostazioni.items()}),
        "perche_niente_settings": perche_niente_settings,
        "biglietti": len(BIGLIETTI),
        "biglietti_con_early_data": len(con_early),
    }
    esito = "TUTTI" if not falliti else "ROSSO"
    scrivi_registro(a, esito=esito,
                    dettaglio=("all checks pass" if not falliti
                               else "not passing: " + ", ".join(falliti)),
                    misure=misure, controlli=esiti)

    if not falliti:
        print(f"   ⭐ {len(esiti)} checks of {len(esiti)}")
        return 0
    print(f"   ⛔ {len(falliti)} checks of {len(esiti)} do NOT pass:")
    for n in falliti:
        print(f"      - {n}")
    return 1


def scrivi_registro(a, esito, dettaglio, misure, controlli):
    """⛔ One line per round, and the TARGET is inside it.

    Without it, six numbers read on two different servers cannot be lined
    up — and that is precisely the job for which this probe was reopened
    on 11 Aug 2026.
    """
    riga = {
        "banco": "B2-trasporto",
        "bersaglio": a.bersaglio,
        "impronta_bersaglio": a.impronta,
        "indirizzo": f"{a.indirizzo}:{a.porta}",
        "etichetta": a.etichetta,
        "attesi": {
            "max_idle_timeout": a.idle_atteso,
            "uni_disponibili_a_rcp": a.credito_atteso,
            "bozze_webtransport": a.bozze_attese,
        },
        "esito": esito,
        "dettaglio": dettaglio,
        "misure": misure,
        "controlli": controlli,
        "ora": datetime.now().isoformat(timespec="seconds"),
    }
    try:
        with Path(a.registro).open("a") as f:
            f.write(json.dumps(riga, ensure_ascii=False, default=str) + "\n")
        print(f"   ·· recorded in {a.registro}")
    except Exception as e:  # noqa: BLE001
        # ⛔ A log that cannot be written is SAID.  A round without a line is a
        #    round that six months from now never happened.
        print(f"   ⛔ the log was NOT written: {type(e).__name__}: {e}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="the transport parameters, on the wire")
    # ⛔ Mandatory, and deliberately without a default value: a round without a
    #    target produces a number that cannot be lined up with the
    #    others, and that is worse than no round.
    p.add_argument("--bersaglio", required=True,
                   choices=("innesto", "prodotto", "controllo"),
                   help="innesto = bsslserver+B2 (7447) · prodotto = remotix "
                        "(7448) · controllo = aioquic acting as server")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--etichetta", default="senza-etichetta")
    p.add_argument("--impronta", default="ignota",
                   help="the fingerprint of WHAT IS MEASURED (md5 of the binary): "
                        "a rebuilt binary is another target with the "
                        "same name")
    p.add_argument("--idle-atteso", type=int, default=30000)
    p.add_argument("--credito-atteso", type=int, default=16,
                   help="uni streams AVAILABLE to RCP after the 3 of HTTP/3 "
                        "(RCP.md §2.3)")
    p.add_argument("--bozze-attese", default="02,07",
                   help="which WebTransport declarations are demanded from "
                        "this target")
    p.add_argument("--registro",
                   default=str(Path(__file__).resolve().parent
                               / "b2-trasporto-esiti.jsonl"))
    p.add_argument("--attesa", type=float, default=8.0)
    p.add_argument("--attesa-biglietto", type=float, default=1.5)
    a = p.parse_args()
    try:
        sys.exit(asyncio.run(principale(a)))
    except KeyboardInterrupt:
        sys.exit(130)
