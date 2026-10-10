#!/usr/bin/env python3
"""02-filo-cliente.py — ⛔ F2.4: the test client RECEIVES the frame, and judges it.

    python3 02-filo-cliente.py --porta 7514 --utente prova --parola X
    python3 02-filo-cliente.py --porta 7514 --registra t.rcpreg --attesa 20
    python3 02-filo-cliente.py --porta 7514 --violazioni      the tests against the server
    python3 02-filo-cliente.py --elenco                       the predictions, without network

⚠ It runs INSIDE the container: `aioquic` lives there.  ⛔ And the port is **7514**,
  which is F2.4's: 7448 is the house product and 7501 the target
  of P5, both on on purpose (mandate §4).

⏳ **IT HAS NOT BEEN RUN YET, and it must be said.**  The phase 2 product does not
   exist — `grep -c '0x0301\\|0x0302' src/rcp.c src/webtransport.c
   src/pagina.html` gives **0 · 0 · 0**, `[M]` 12 Aug 2026 — so there is
   no server that sends a frame.  ⛔ This file is the bench
   **written before the product** that `PIANO.md` §0.4 moment 1 requires, and its
   first round is the first measurement of phase 2.

===========================================================================
⛔ WHY THE SECOND READER IS WORTH DOUBLE HERE, AND IT IS NOT A REPETITION

`PIANO.md` §1.1.  The server is in **C**, the page is in **JavaScript**, and
both are written by the same hand.  If the server wrote `istante` in
little-endian and the page read it in little-endian, ⛔ **the desktop
would appear perfect** and no bench of ours would notice: the two
agreed on something `RCP.md` does not say.

This program is the **third reader**, in a third language, and ⛔ whoever
grows it **does not look at `src/`**.  Its value is not the green: it is that whoever
writes it **must choose** where `RCP.md` allows two readings — and those
choices are the most precious outcome of the phase, not a side effect.
`FASI.md` §01-filo-nudo collected **twelve** of them for the handshake; the
video chapter adds **seven**, and it is honest to separate them: ⛔ **four
are true double readings** — two conforming implementations produce different
bytes for the same input — and ⚠ **three are DERIVED rules**, that is they
follow from §3 and §1 but no line writes them.  The first are kept by
`02-filo-fotogramma.py` with the `AMBIGUO` outcome; the second are choices of the
bench, declared next to the case.  ⭐ Confusing them would inflate the count:
a derived rule does not make two careful implementations diverge, a double
reading does.

===========================================================================
⛔ WHAT IT LOOKS AT, AND THE FIRST TWO GET FORGOTTEN

  1. ⛔ **that the frame REALLY ARRIVED**, and with the denominator.
     `LEZIONI.md` §1.9: a count without a denominator is not a measurement.
     ⚠ *«no violation»* is true even on zero frames, and it is the
     easiest way to declare green a phase that delivered nothing —
     finding **R7.4** of `01-b4-validatore.py`.  ⛔ Here zero frames has
     an **exit code of its own** (`5`), and it is not a green;

  2. ⛔ **FROM THE RECEIVING SIDE** (`CODER.md` §3.8, error form **E7**).  The
     server's log says it called a function, not that the byte
     arrived.  In v1 the server wrote «farewelling the client» and the client, at the
     same time, «network error» — **for three phases** (`LEZIONI.md` §1.7);

  3. **on which STREAM** it arrived: a new unidirectional one, opened by the
     server, one per frame (§2.5, §5.1).  ⛔ And the channel is recognised by the
     **high byte of `tipo`**, never by the stream number — it is the cure of
     finding R11.9;

  4. ⛔ **how the stream ended**: FIN or `RESET_STREAM`, and they are two different
     things (§6.2, finding R1.7).  ⭐ **Only a live client can do
     this**: the recording of §11.1 does not have that field, and
     `02-filo-validatore.py` declares it not judgeable.  See proposal
     **P7**;

  5. ⛔ **what the client MUST do next**: on a gap or an abandonment,
     `RICHIEDI_CHIAVE` (§5.2); on a violation, `CONGEDO` **and** the reason in the
     error code of the closing (§3.1 points 2 and 3).  ⚠ A test client
     that limited itself to judging and staying silent would exercise **none** of the
     obligations §5.2 puts on the client — and it is the half of the protocol that
     no server bench can see.

===========================================================================
⛔ AND IT RECORDS, IN THE FORMAT OF §11.1

Every byte that arrives ends up in a recording that `02-filo-validatore.py`
can judge.  ⭐ This way the frame is read **twice by two
programs**: here live, and afterwards by the mechanical referee.  ⚠ And if the two
said different things it would be a measurement, not an accident.

⛔ **The password is masked**, as in phase 1: real length, bytes
replaced with `0x2A`, fingerprint of what was there (§11.1).

===========================================================================
⛔ THE EXIT CODES, AND THEY ARE SIX BECAUSE THE FACTS ARE SIX

  0  ⭐ at least one frame arrived and every frame is conforming
  1  ⛔ a frame is NOT conforming — and it says which byte and which rule
  2  the handshake did not reach `SESSIONE` (nothing was tested)
  3  ⛔ `RCP.md` allows two readings of what arrived: it is not a green
     and it is not a red.  See `02-filo-fotogramma.py --elenco`
  4  the connection or the session dropped before the end of the wait
  5  ⛔ ZERO frames.  «I have nothing to judge» is not «all is well»
"""
import argparse
import asyncio
import hashlib
import importlib.util
import json
import os
import ssl
import struct
import sys
import time

QUI = os.path.dirname(os.path.abspath(__file__))


def _porta(nome, file):
    s = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    m = importlib.util.module_from_spec(s)
    s.loader.exec_module(m)
    return m


# ⛔ THEY ARE IMPORTED, NOT COPIED.
#
#    In `01-b3-cliente.py` there is the line that prevents giving the events of the
#    control channel to the HTTP/3 layer of `aioquic`: without it, the connection
#    dies at the CLIENT's hand with `0x105 — DATA frame is not allowed in this
#    state` (`[M]` 10 Aug 2026).  A diverging copy would bring that
#    defect back in here disguised as a server defect.
#    ⚠ And the frame judgement sits in a single file, or two copies of the
#      same reading would always agree with themselves.
#
# ⛔ And `01-b3-cliente.py` IS IMPORTED LATE, not here at the top.
#
#    That file imports `aioquic`, which lives **only inside the container**.
#    Importing it at the top, `--elenco` — which does not touch the network and serves to read
#    the predictions **before** the round — died with `ModuleNotFoundError` on
#    CHUWI.  ⚠ And the predictions are precisely the thing to be read by whoever
#    does not have the container: whoever reviews the bench before the product exists.
#    ⭐ `02-filo-fotogramma.py` instead has no dependencies, and it is intended: the
#    frame judgement must be able to run anywhere.
f24 = _porta("f24", "02-filo-fotogramma.py")
b3 = None


def carica_b3():
    global b3
    if b3 is None:
        b3 = _porta("b3", "01-b3-cliente.py")
    return b3

CLIENT, SERVER = 1, 2

# ⛔ THE RECORDING FORMAT IS `RCPREG 0x00 0x03` — §11.1.
#
#    `0x02`, 12 Aug 2026, proposal P7 (which this very bench had
#    found): the block carries `fine`, and goes from 16 to 17 bytes.
#    ⚠ Without that field, what this client records and what it saw
#      on the wire are not the same thing: **it** knows whether the stream ended with
#      FIN or was reset — QUIC tells it — and the recording could
#      not write it.  The referee reading it had to guess.
#
# ⭐⭐ `0x03`, **21 Aug 2026**: the block carries `istante_ms` and goes to 21
#    bytes, the header declares `orologio` (1 = the times are the client's).
#    Without time, §7.1 — the grace second — could not be tested from
#    any `.rcpreg`, and T4 («a server that says `TELA(ADATTATA)` and does not touch
#    the stage») could not be written at all.
#
# ⛔⛔ AND THIS FILE WAS THE SECOND ONE OF THE `0x02` ISLAND: `02-filo-validatore.py`
#    read it, `04-b20-desktop-vero.py` too, and the three agreed with each
#    other while `01-b3`/`01-b4` had moved to `0x03`.  ⚠ Two live formats
#    under a single specification are the exact condition of the 12 Aug
#    defect, only bigger — and none of the three files was broken on its own.
MAGIA = b"RCPREG\x00\x03"
BLOCCO = "!BBBIQIH"
CONTINUA, FIN, RESET = 0, 1, 2
OROLOGIO_CLIENT = 1        # §11.1: this program is the client

# ⛔ The instant is MONOTONIC and RELATIVE to the first block, never a wall-clock time:
#    §4.4 forbids secrets in the file, and an absolute date says **when** and —
#    with the address the trace already carries — **from where** a user
#    connected.  ⚠ `time.monotonic()` and not `time.time()`: an NTP adjustment
#    in the middle would make the instants go backwards, and the referee
#    would read a frame that arrived «before» the `TELA` preceding it.
_t0 = None


def istante():
    global _t0
    adesso = time.monotonic()
    if _t0 is None:
        _t0 = adesso
    return min(int((adesso - _t0) * 1000.0), 0xFFFFFFFF)

T_RICHIEDI_CHIAVE = 0x000D
T_CONGEDO = 0x000C
ERRORE_PROTOCOLLO = 0x0B      # §8.2
CHIUSO_DALL_UTENTE = 0x01

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


# ===========================================================================
class Flusso:
    """A unidirectional stream of the server: one stream, one frame (§6.2)."""

    def __init__(self, sid, ctx):
        self.sid = sid
        self.giudice = f24.Giudice(ctx, dove="uni")
        self.byte = 0
        self.aperto = time.monotonic()
        self.chiuso = None
        self.verdetto = None


def fabbrica_cliente():
    """The phase 1 client, which learns to receive the video streams.

    ⛔ **It inherits, it does not rewrite**: the handshake is already the second reader
       of `RCP.md`, and rewriting it here would give two second readers that can
       diverge — that is two referees.

    ⚠ It is a factory and not a file-level class because the base
      class sits inside `01-b3-cliente.py`, which imports `aioquic`: see the
      box at the top.
    """
    class Cliente(carica_b3().Cliente):

        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            self.contesto = None       # set after `SESSIONE`
            # ⛔ The streams we recognised as VIDEO: the set is kept
            #    and not recomputed, because the WebTransport preamble
            #    arrives only once, in the first event.
            self.video_visti = set()
            self.flussi = {}
            self.finiti = []
            self.chiavi_chieste = 0
            # (direction, channel, stream, payload, masked, end) — §11.1
            self.reg_video = []
            self.primo_byte = None     # ⛔ when the FIRST video byte arrived
            # ⚠ The codec negotiated in §4.3.  The driver sets it BEFORE the
            #   handshake, because `_sfoglia` may need it already
            #   in the first packet that carries `SESSIONE`.
            self.codec_atteso = 1

        # ⛔⛔ THE CONTEXT IS SET **HERE**, AND NOT IN THE COROUTINE THAT WAITS —
        #     bench defect found by the FIRST round against a server that
        #     really sends, `[M]` 12 Aug 2026, phase 2 assembly.
        #
        #     The server sends `SESSIONE` on the control channel and RIGHT
        #     AFTER opens the stream of the first frame (§5.2: «the first after
        #     `SESSIONE` MUST be a keyframe»).  On the wire the order is
        #     right, and the two arrive in the same flight of packets.
        #
        # ⛔ But `cli.contesto` was set by the driver **after**
        #    `await attendi(cli, "SESSIONE")`, that is when `asyncio` resumes
        #    the coroutine — which is **after** all the events of that flight
        #    have been dispatched.  ⇒ `_arrivano()` found `contesto is None`,
        #    concluded *«a frame before SESSIONE»* and printed
        #    `ERRORE_PROTOCOLLO` — ⛔ **a red pointed at the server, which had
        #    done exactly what §2.5 requires of it**.
        #
        # ⭐ Who said whose fault it was: `02-filo-validatore.py`, the
        #    second reader, on the SAME recording — *«ACCETTATO, stream
        #    15: keyframe no. 1, 1920x1080, 11923 bytes, conforming»*, exit 0.  ⚠ And
        #    that the two referees of the same bench said opposite things about the
        #    same bytes is a MEASUREMENT, not an accident (`P2-4-filo.md` §4).
        #
        # ⛔ And the cure is not «wait a little»: it is looking at the buffer of the
        #    control channel **before** `_sfoglia` consumes it, that is
        #    at the same synchronous instant the bytes arrived.  This way
        #    «before `SESSIONE`» becomes again a question about BYTES, and not
        #    about the order in which `asyncio` wakes the coroutines.
        def _sfoglia(self):
            if self.contesto is None:
                dati = bytes(self.arrivati)
                i = 0
                while len(dati) - i >= 6:
                    tipo, lung = struct.unpack("!HI", dati[i:i + 6])
                    if len(dati) - i < 6 + lung:
                        break
                    # body: 1 byte of state, then width and height (§4.5)
                    if tipo == carica_b3().T["SESSIONE"] and lung >= 9:
                        lar, alt = struct.unpack("!II", dati[i + 7:i + 15])
                        self.contesto = f24.Contesto(
                            tela=(lar, alt),
                            codec_negoziato=self.codec_atteso,
                            sessione_aperta=True)
                        break
                    i += 6 + lung
            super()._sfoglia()

        def quic_event_received(self, event):
            nome = type(event).__name__
            # ⛔ The server's unidirectional streams are intercepted BEFORE
            #    passing the event to the phase 1 chain: that one does not know
            #    them and would give them to the HTTP/3 layer of `aioquic`, which would
            #    read them as HTTP/3 frames and close the connection —
            #    **by our own hand**.  ⚠ It is the same asymmetry paid for on 10
            #    Aug 2026 on the control channel (`01-b3-cliente.py`).
            if nome == "StreamDataReceived" and self._smista(event):
                return
            if nome == "StreamReset" and event.stream_id in self.video_visti:
                # ⛔ `RESET_STREAM`: the frame is INCOMPLETE (§6.2).
                self._azzerato(event.stream_id)
                return
            super().quic_event_received(event)

        # ⛔⛔ THE WEBTRANSPORT PREAMBLE, AND THE FIRST ROUND PAID FOR IT
        #
        # ⚠ `[M]` 12 Aug 2026, FIRST LIVE ROUND of this client against
        #   7514.  The previous line said: *«a unidirectional stream
        #   opened by the server is recognised by the two low bits
        #   of the QUIC identifier»* — and it also took **the three
        #   unidirectional streams of HTTP/3** (the control stream and the two of QPACK, which
        #   `aioquic` opens by itself and which have the same two bits).  ⇒ The
        #   HTTP/3 layer was left without its bytes, the extended CONNECT never
        #   reached `:status 200`, the control channel did not open, and the
        #   server closed with `TEMPO_SCADUTO` after 5 s (§4.6).
        #   ⛔ The symptom was **a red pointed at the server**, which had done
        #      exactly its job: the positive control —
        #      `01-b3-cliente.py` against the **same** server, in the same
        #      minute — reached `SESSIONE` in 1003 ms.
        #
        # ⭐ And the cure carries a discovery about `RCP.md`, which is in the
        #    report as **P18**: §2.5 says *«the first two bytes of the
        #    stream are read, which are in any case a `tipo` field»*, ⛔ and on
        #    WebTransport **it is not true**: a unidirectional stream of the server
        #    starts with type `0x54` as a varint (two bytes, `40 54`) and with the
        #    session number, and the 28 bytes of §6.2 start after.
        WT_UNI = 0x54  # draft-ietf-webtrans-http3: the type of the uni stream

        @staticmethod
        def _varint(b, i):
            """The QUIC varint (RFC 9000 §16).  `None` = it is not all here."""
            if i >= len(b):
                return None, i
            n = 1 << (b[i] >> 6)
            if i + n > len(b):
                return None, i
            v = b[i] & 0x3F
            for k in range(1, n):
                v = (v << 8) | b[i + k]
            return v, i + n

        def _smista(self, event):
            """Is this stream a frame?  ⛔ And if it is not, **not one byte of it
            is consumed**: those bytes belong to HTTP/3, and taking them is
            the defect the first round paid for."""
            sid = event.stream_id
            if sid in self.video_visti:
                self._arrivano(sid, event.data, event.end_stream)
                return True
            # 0b11 = unidirectional, opened by the server
            if (sid & 0x03) != 0x03 or sid == self.sessione:
                return False
            d = event.data
            # ⛔ The decision is made on the FIRST event and the first two bytes, and if they
            #    are not enough it is dropped instead of holding them back: «I did not
            #    understand» and «it is mine» are two different things.
            if len(d) < 2 or d[0] != 0x40 or d[1] != self.WT_UNI:
                return False
            tipo, i = self._varint(d, 0)
            sessione, i = self._varint(d, i)
            if tipo != self.WT_UNI or sessione is None:
                return False
            self.video_visti.add(sid)
            self._arrivano(sid, bytes(d[i:]), event.end_stream)
            return True

        def _arrivano(self, sid, dati, fine):
            if self.contesto is None:
                # ⛔ A frame before `SESSIONE`: the context is not there
                #    yet, and the judge MUST be able to say so — invariant I3.
                self.contesto = f24.Contesto(sessione_aperta=False)
            f = self.flussi.get(sid)
            if f is None:
                f = self.flussi[sid] = Flusso(sid, self.contesto)
                if self.primo_byte is None:
                    self.primo_byte = time.monotonic()
            f.byte += len(dati)
            self.reg_video.append([SERVER, 0x03, sid, bytes(dati), [],
                                   FIN if fine else CONTINUA, istante()])
            f.giudice.arrivano(dati)
            if fine:
                f.chiuso = "fin"
                self._chiudi(f)

        def _azzerato(self, sid):
            # ⛔ AND IT IS WRITTEN IN THE RECORDING — §11.1, field `fine`.
            #
            #    The `RESET_STREAM` carries no bytes, so it has no block of its own:
            #    it marks the LAST block of that stream.  ⚠ And if there is
            #    none — a stream reset before delivering a byte
            #    — an **empty** one is written: «zero bytes, reset» and «it never
            #    existed» are two different facts, and it is the E8 form.
            ultimo = None
            for b in self.reg_video:
                if b[2] == sid:
                    ultimo = b
            if ultimo is None:
                self.reg_video.append([SERVER, 0x03, sid, b"", [], RESET,
                                       istante()])
            else:
                ultimo[5] = RESET
            f = self.flussi.get(sid)
            if f is None:
                f = self.flussi[sid] = Flusso(
                    sid, self.contesto or f24.Contesto())
            f.chiuso = "reset"
            self._chiudi(f)

        def _chiudi(self, f):
            if f.verdetto is not None:
                return
            f.verdetto = (f.giudice.verdetto
                          if f.giudice.verdetto is not None
                          else f.giudice.finisce(f.chiuso))
            self.finiti.append(f)
            del self.flussi[f.sid]

        # -- the obligations §5.2 puts on the CLIENT -----------------------
        def chiedi_chiave(self, ultimo):
            """§5.2: the client MUST ask for a keyframe on a gap or an
            abandonment.

            ⛔ And `ultimo_numero` is «the last decoded frame, 0 if
               none» (§7.1) — which is ambiguity **A2**: if the counter of
               §6.2 could start from 0, this field would say two things.  Here
               what the document says is sent, and the ambiguity is flagged
               instead of being resolved by hand by the bench.
            """
            self.manda(struct.pack("!HII", T_RICHIEDI_CHIAVE, 4,
                                   ultimo if ultimo is not None else 0))
            self.chiavi_chieste += 1

    return Cliente


# ===========================================================================
async def guarda(cli, a, ctx):
    """Keeps listening, and does what §5.2 requires of the client.

    ⛔ **With eyes open, not asleep** — findings R8.2/R8.4 of phase 1.
       An `asyncio.sleep` notices nothing: the connection can drop
       because of QUIC's idle ceiling, or the session can be closed by the
       server, and this program would exit 0 saying «I looked».
    """
    scadenza = asyncio.get_event_loop().time() + a.attesa
    visti = 0
    while asyncio.get_event_loop().time() < scadenza:
        if cli.caduta is not None:
            return visti, f"dropped: {cli.caduta}"
        while len(cli.finiti) > visti:
            f = cli.finiti[visti]
            visti += 1
            v = f.verdetto
            col = {f24.ACCETTATO: VERDE, f24.SCARTATO: GIALLO,
                   f24.AMBIGUO: GIALLO, f24.ERRORE_PROTOCOLLO: ROSSO}[v.esito]
            print(f"   {col}{v.esito:18s}{GRIGIO} stream {f.sid}, {f.byte} "
                  f"bytes, ended with {f.chiuso}: {v.dice}")
            if v.esito == f24.ERRORE_PROTOCOLLO:
                # ⛔ §3.1, and the points are THREE and in this order: in the log,
                #    the `CONGEDO` on the channel if the channel is usable, and the
                #    reason in the error code of the session's closing.
                print(f"      ⛔ {v.regola} — byte {v.scostamento} "
                      f"of the header")
                cli.manda(struct.pack("!HIB", T_CONGEDO, 3, ERRORE_PROTOCOLLO)
                          + struct.pack("!H", 0))
                return visti, f"NOT CONFORMING: {v.dice}"
            # ⛔ And the obligations of §5.2, which are the CLIENT's and which no
            #    server bench can exercise in its place.
            if ctx.chiedi_chiave:
                cli.chiedi_chiave(ctx.ultimo_consegnato)
                print(f"      ⇒ `RICHIEDI_CHIAVE(ultimo_numero="
                      f"{ctx.ultimo_consegnato or 0})` — §5.2")
                ctx.chiedi_chiave = False
        await asyncio.sleep(0.02)
    return visti, None


def scrivi_registrazione(percorso, blocchi):
    """The format of §11.1, with the video blocks next to the control ones.

    ⛔ `fine` defaults to CONTINUA: the control channel lives on **a single
       stream for the whole session** (§2.5), and inside the recording that
       stream does not close.  ⚠ Writing `FIN` at every message would say that the
       session closes and reopens at every line.
    """
    # ⛔⛔ AND THE BLOCKS ARE PUT BACK IN TIME ORDER, and it is not cosmetic.
    #
    #    The caller passes `blocchi + cli.reg_video`: the CONTROL blocks
    #    all first, the VIDEO ones all after.  ⚠ But a `RICHIEDI_CHIAVE`
    #    sent midway through the session ended up **in front of** the first frame, which
    #    had passed on the wire much earlier.  ⛔ With `0x02` it did not show: without
    #    time, a wrong order and a right one look the same.
    #    With `0x03` the referee requires a monotonic clock and would say so —
    #    «broken recording» — on a trace of a perfectly healthy wire.
    #
    # ⭐ `sorted` is STABLE: two blocks with the same millisecond stay
    #    in the order in which they were recorded, which is what is known about
    #    them.  Inventing an order among equals would be worse than not having one.
    def _quando(b):
        return b[6] if len(b) > 6 else 0

    blocchi = sorted(blocchi, key=_quando)
    out = bytearray(MAGIA + struct.pack("!IBBBB", len(blocchi),
                                        OROLOGIO_CLIENT, 0, 0, 0))
    for verso, canale, stream, carico, *resto in blocchi:
        oscurati = resto[0] if resto else []
        fine = resto[1] if len(resto) > 1 else CONTINUA
        ist = resto[2] if len(resto) > 2 else 0
        out += struct.pack(BLOCCO, verso, canale, fine, ist, stream,
                           len(carico), len(oscurati))
        for ini, qua, imp in oscurati:
            out += struct.pack("!II", ini, qua) + imp
        out += carico
    with open(percorso, "wb") as f:
        f.write(bytes(out))
    return len(blocchi)


async def principale(a):
    from aioquic.h3.connection import H3_ALPN
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.asyncio import connect
    b3 = carica_b3()
    Cliente = fabbrica_cliente()

    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    blocchi = []

    print(f"== F2.4 — the test client RECEIVES the frame")
    print(f"   ⛔ TARGET: https://{autorita}{a.percorso}")
    print(f"   ⛔ SCENE: session just opened, no input, no "
          f"movement —")
    print(f"      phase 2 delivers **a still image** (`PIANO.md` "
          f"«Phase 2»).")
    print(f"      ⚠ And it must be declared: `CODER.md` §3.2 wants a scene always in")
    print(f"        motion, and here the still scene **is the subject**, not "
          f"a")
    print(f"        distraction.  From phase 3 onwards that rule applies "
          f"again.")
    print(f"   wait: {a.attesa} s\n")

    async with connect(a.indirizzo, a.porta, configuration=conf,
                       create_protocol=Cliente) as cli:
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.apri_sessione(autorita, a.percorso)
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        print(f"   extended CONNECT: :status = {stato}")
        if stato != "200":
            return 2
        cli.apri_controllo()
        # ⛔ BEFORE the handshake: `_sfoglia` may need the
        #    codec already in the packet that carries `SESSIONE`, and a value set
        #    after would be set too late — it is the same ordering defect
        #    the box of `_sfoglia` describes.
        cli.codec_atteso = a.codec
        try:
            b = b3.inquadra(b3.T["CIAO"], b3.corpo_ciao())
            cli.manda(b)
            blocchi.append((CLIENT, 0x00, 0, b, [], CONTINUA, istante()))
            _, corpo, grezzo = await b3.attendi(cli, "ECCOMI")
            blocchi.append((SERVER, 0x00, 0, grezzo, [], CONTINUA, istante()))

            corpo_c = b3.s(a.utente) + b3.s(a.parola)
            b = b3.inquadra(b3.T["CREDENZIALI"], corpo_c)
            ini = 6 + 2 + len(a.utente.encode()) + 2
            qua = len(a.parola.encode())
            cli.manda(b)
            blocchi.append((CLIENT, 0x00, 0,
                            b[:ini] + bytes([0x2A]) * qua + b[ini + qua:],
                            [(ini, qua, hashlib.sha256(a.parola.encode()).digest())],
                            CONTINUA, istante()))
            _, corpo, grezzo = await b3.attendi(cli, "AMMESSO", attesa=20)
            blocchi.append((SERVER, 0x00, 0, grezzo, [], CONTINUA, istante()))

            b = b3.inquadra(b3.T["ATTACCA"],
                            struct.pack("!IIII", a.larghezza, a.altezza,
                                        a.larghezza, a.altezza)
                            + b3.s(a.disposizione))
            cli.manda(b)
            blocchi.append((CLIENT, 0x00, 0, b, [], CONTINUA, istante()))
            _, corpo, grezzo = await b3.attendi(cli, "SESSIONE")
            blocchi.append((SERVER, 0x00, 0, grezzo, [], CONTINUA, istante()))
        except Exception as e:      # noqa: BLE001 — the error type IS the measurement
            print(f"   ⛔ the handshake did not reach SESSIONE: "
                  f"{type(e).__name__}: {e}")
            print(f"      ⚠ This is NOT a video red: nothing was "
                  f"tested")
            return 2

        lar, alt = struct.unpack("!II", corpo[1:9])
        print(f"   ⭐ SESSIONE: canvas granted {lar}x{alt}")
        # ⛔ THE CONTEXT IS TAKEN FROM `SESSIONE`, NOT FROM THE DEFAULTS.
        #
        #    §6.2 ties `largh.`/`altezza` to the **granted canvas** — which can
        #    differ from the requested one (§4.5, the fallback on KDE) — and
        #    `codec` to what §4.3 negotiated.  A judge that used its
        #    own defaults would be judging itself.
        # ⚠ `_sfoglia` may have set it already, on the same bytes and with the
        #   same values: then it is not redone.  ⛔ Redoing it here would erase
        #   a context already used by the streams arrived in the same flight — and their
        #   `Flusso` would keep the old object, that is two truths
        #   about the same session.
        if cli.contesto is None:
            cli.contesto = f24.Contesto(tela=(lar, alt),
                                        codec_negoziato=a.codec,
                                        sessione_aperta=True)
        ctx = cli.contesto

        visti, perche = await guarda(cli, a, ctx)

    if a.registra:
        n = scrivi_registrazione(a.registra, blocchi + cli.reg_video)
        print(f"\n   recording: {a.registra} ({n} blocks) — "
              f"⛔ and it must be given to `02-filo-validatore.py`, which is the other reader")

    esiti = [f.verdetto.esito for f in cli.finiti]
    conformi = sum(1 for e in esiti if e == f24.ACCETTATO)
    ambigui = sum(1 for e in esiti if e == f24.AMBIGUO)
    print(f"\n   watched: {len(cli.finiti)} video streams · {conformi} "
          f"conforming · {ambigui} ambiguous · {cli.chiavi_chieste} "
          f"`RICHIEDI_CHIAVE` sent")

    if a.uscita:
        with open(a.uscita, "a") as f:
            f.write(json.dumps({
                "quando": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
                "banco": "F2.4-cliente", "porta": a.porta,
                "scena": "session just opened, no input, still image",
                "flussi": len(cli.finiti), "conformi": conformi,
                "ambigui": ambigui, "chiavi_chieste": cli.chiavi_chieste,
                "esiti": esiti, "caduta": cli.caduta}, ensure_ascii=False) + "\n")

    # ⛔ AND ZERO HAS A CODE OF ITS OWN — see point 1 of the header.
    if not cli.finiti:
        print(f"\n   {ROSSO}⛔ ZERO frames in {a.attesa} s.{GRIGIO}")
        print(f"      This is NOT «conforming»: it is the absence of the object of "
              f"judgement.")
        print(f"      Look at whoever had to send them — not at `RCP.md`.")
        return 5
    if f24.ERRORE_PROTOCOLLO in esiti:
        print(f"\n   {ROSSO}⛔ a frame is NOT conforming{GRIGIO}")
        return 1
    if perche:
        print(f"\n   {ROSSO}⛔ {perche}{GRIGIO}")
        return 4
    if ambigui:
        print(f"\n   {GIALLO}⭐⛔ `RCP.md` allows two readings of what "
              f"arrived{GRIGIO}")
        print(f"      It is not a green and it is not a red: it is a defect of the "
              f"DOCUMENT.")
        print(f"      The proposals: `python3 02-filo-fotogramma.py --elenco`")
        return 3
    print(f"\n   {VERDE}⭐ {conformi} frames, all conforming to `RCP.md`"
          f"{GRIGIO}")
    print(f"   ⚠ and it is NOT «the user sees their desktop»: here the "
          f"BYTES are judged.")
    print(f"     The pixels are compared by F2.6, and the yardstick is the user (I8).")
    return 0


# ===========================================================================
# ⛔ THE VIOLATIONS TOWARDS THE SERVER, and they are those phase 2 adds.
#
#    `01-b5-violazioni.py` tests forty-four of them on the handshake, and
#    declares at the top which ones it does NOT test because the message does not exist yet:
#    among these, *«two `RICHIEDI_CHIAVE` less than 200 ms apart»*, postponed to
#    phase 3.  ⭐ Here are added those born with the first frame.
#
# ⚠ And one already in B5 is REDONE, and it is not a duplicate: `uni-video`
#   sent `0x0301` to a server that did **not know** the video channel
#   at all — it fell into the `default` branch.  Against a server that knows it,
#   the same input exercises a **different** code path, and a case
#   that passes against the first says nothing about the second.
VIOLAZIONI = [
    ("video-dal-client", ERRORE_PROTOCOLLO,
     "a WELL-FORMED keyframe on a unidirectional stream of the "
     "client: §2.5, «a `0x03` that arrives from the client».  ⛔ The payload is legal "
     "in itself: the only wrong thing is the direction"),
    ("richiedi-chiave-prima-di-sessione", ERRORE_PROTOCOLLO,
     "`RICHIEDI_CHIAVE` between `AMMESSO` and `SESSIONE`: there is no "
     "frame whose keyframe could be asked for (§1, §3)"),
    ("richiedi-chiave-corta", ERRORE_PROTOCOLLO,
     "`RICHIEDI_CHIAVE` with three bytes of body instead of four: §6.1, «a "
     "length inconsistent with what the type expects»"),
    ("richiedi-chiave-zero", None,
     "⭐ `RICHIEDI_CHIAVE(ultimo_numero = 0)`: §7.1 declares it legal — «0 if "
     "none» — and it is what a just-attached client sends.  ⛔ The "
     "session MUST stay alive"),
    ("richiedi-chiave-due-volte", None,
     "⏳ two `RICHIEDI_CHIAVE` less than 200 ms apart: the server **MAY** ignore the "
     "second (§3 exception 5, §5.2) — and in both cases the session "
     "MUST stay alive.  ⚠ The real measurement belongs to **phase 3**, where the "
     "keyframes are counted: here it is only proved that the session holds"),
]


def elenco():
    print("== F2.4 — the test client: what it tests, and against what")
    print("   ⏳ NOT RUN YET: the phase 2 product does not exist\n")
    print("== ⛔ from the RECEIVING side — the cases are in 02-filo-fotogramma.py")
    print("   `python3 02-filo-fotogramma.py --elenco`\n")
    print("== ⛔ towards the SERVER — the violations phase 2 adds")
    print("   ⛔ Every line is a PREDICTION, written before the round\n")
    for nome, atteso, spiega in VIOLAZIONI:
        att = (f"{atteso:#04x} ERRORE_PROTOCOLLO" if atteso
               else "⭐ MUST PASS, and the session MUST stay alive")
        print(f"  {nome:36s} {att}")
        print(f"  {'':36s}   {spiega}")
    print(f"\n  {len(VIOLAZIONI)} cases: "
          f"{sum(1 for v in VIOLAZIONI if v[1])} violations and "
          f"{sum(1 for v in VIOLAZIONI if not v[1])} ⭐ expected greens")
    return 0


# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD MUST NOT GO THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 Aug 2026.
#
# ⛔ `--parola` ends up in the process's `argv`, that is in `/proc/<pid>/cmdline`,
#    which on Linux is **readable by anyone**: a `ps` launched by another
#    user during the round prints it in full.
#
# ⭐ The good road already existed in the house and this is its extension, not a
#    second way: `01-b10-secondo-utente.py` takes `--parola-file`, a `0600`
#    file the launcher writes with `printf` — a shell **builtin**,
#    so not even the writing goes through a process with the password in `argv` —
#    and deletes with a `trap`.
#
# ⚠ And `--parola` was NOT removed, and not out of laziness: some callers not
#   yet cured still pass it, and breaking them **silently** would be worse
#   than the defect.  ⛔ But the fallback is DECLARED (`CODER.md` §4.2): a silent
#   fallback produces two behaviours under the same label, which is the
#   **E2** form — and here the two behaviours are «the secret is protected» and
#   «the secret is public».  ⇒ whoever passes `--parola` gets told.
#
# ⚠ And the warning looks at `sys.argv`, not at the value: the default written in the
#   code is on no command line, and telling it otherwise would be an
#   alarm one learns to ignore.
def parola_dagli_argomenti(a):
    """The password: from `--parola-file` if present, from `--parola` otherwise.

    ⛔ And the three ways of failing are kept apart: «cannot be read», «is readable by
    others» and «is empty» have three different cures, and an empty file is NOT an
    empty password — it is «the launcher did not write it» (`LEZIONI.md` §1.9).
    """
    percorso = getattr(a, "parola_file", "") or ""
    if percorso:
        try:
            modo = os.stat(percorso).st_mode & 0o077
        except OSError as e:
            print(f"   ⛔ the password file «{percorso}» cannot be read: {e}")
            sys.exit(2)
        if modo:
            print(f"   ⚠ «{percorso}» is readable by others (bits {modo:o}): the "
                  f"secret is not protected")
        try:
            with open(percorso, encoding="utf-8") as f:
                parola = f.read().strip("\n")
        except OSError as e:
            print(f"   ⛔ the password cannot be read from «{percorso}»: {e}")
            sys.exit(2)
        if not parola:
            print(f"   ⛔ the password file «{percorso}» is EMPTY.  It is not")
            print("      «the password is empty»: it is «the launcher did not write it».")
            sys.exit(2)
        return parola
    if any(x == "--parola" or x.startswith("--parola=") for x in sys.argv[1:]):
        print("   ⚠ D12: the password arrived from `--parola`, that is from the")
        print("     COMMAND LINE: it is in `/proc/<pid>/cmdline` and anyone who runs")
        print("     `ps` on this machine sees it.  The round goes on — the caller")
        print("     has not been cured — but it is not a private round.")
        print("     ⭐ The cure: `--parola-file <0600 file>`, as in B10.")
    return a.parola


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="F2.4 — the test client that receives the frame")
    p.add_argument("--indirizzo", default="192.168.0.2")
    # ⛔ The port has NO default naming a target: 7448 is the
    #    house product and 7501 the P5 target, both on on purpose.
    #    The F2.4 port is **7514**, and it is passed by hand.
    p.add_argument("--porta", type=int, help="⛔ 7514, for F2.4")
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="parola-di-prova")
    # ⛔ D12: the road that does NOT go through `ps`.  It wins over `--parola` if both
    #    are there — a file written on purpose is always more recent than a
    #    default.
    p.add_argument("--parola-file", default="",
                   help="0600 file with only the password (⭐ D12: this way "
                        "it does not end up in `ps`)")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--codec", type=int, default=1, help="1 = HEVC, 2 = AV1")
    p.add_argument("--attesa", type=float, default=15.0,
                   help="how many seconds to keep listening")
    p.add_argument("--registra", help="the trace, in the format of §11.1")
    p.add_argument("--uscita", default="", help="the round's log, in JSONL")
    p.add_argument("--elenco", action="store_true",
                   help="the predictions, without network")
    p.add_argument("--violazioni", action="store_true",
                   help="⏳ the tests against the server (needs a server)")
    a = p.parse_args()
    a.parola = parola_dagli_argomenti(a)
    if a.elenco:
        sys.exit(elenco())
    if not a.porta:
        print("⛔ --porta is needed.  For F2.4 it is 7514: 7448 and 7501 are")
        print("   on on purpose and are not touched (mandate §4).")
        sys.exit(2)
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
