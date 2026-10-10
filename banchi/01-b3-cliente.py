#!/usr/bin/env python3
"""01-b3-cliente.py — the test client: the RCP handshake, written a second time.

    python3 01-b3-cliente.py --utente prova --parola X [--registra t.rcpreg]
    python3 01-b3-cliente.py --certifica     ⭐ HERE, with no network and no machine

---------------------------------------------------------------------------
⭐⭐ PHASE 9 — THE TWO AUDIO RULES, AND THE SWITCH BETWEEN THEM

The reorder cure — the one that stops throwing away blocks that arrived out of
sequence — was written **only in `src/pagina.html`**.  ⇒ No bench could
measure whether it bites, because the client the benches use did not have it.
Now it has it, behind `--audio-regola vecchia|nuova`.

⛔⛔ **The default is `vecchia`, and it changes only by the user's decision.**
     Dozens of already-measured benches use this program: with the new rule
     as the default, every number already written would stop being
     comparable — and the «before / after the cure» comparison is exactly
     what we want to be able to make.  ⭐ `--certifica` case 6 checks it against a
     LITERAL transcription of the code of 22 August, not against an opinion.

⚠ The translation from the page to here is NOT identical, and the five differences
  are written out in full above `class VaglioAudio` (T1..T5).  The most
  important one: **here decoding costs zero**, and with `--audio-decodifica-ms 0`
  the `scartati_tardivi` counter is not a measurement, it is a blind zero.

---------------------------------------------------------------------------
⛔ ITS JOB, WHICH IS NOT «WORKING»

`PIANO.md` §1.1: this is **the second reader of `RCP.md`**, in a language
different from the server's.  ⛔ **Whoever grows it does not look at the C**: if
they looked they would inherit its misunderstandings, and two programs written by
the same hand that agree confirm nothing.

⭐ Its value is not the green: it is that whoever writes it **must choose** where
   the specification allows two readings, and those choices go in «what did
   NOT work» — they are defects of the document, and this is the phase in which
   they cost least.

---------------------------------------------------------------------------
⭐ AND IT RECORDS, IN THE FORMAT OF §11.1

Every byte that passes on the control channel ends up in a recording that
**the B4 validator can judge**.  ⛔ Not the password: it is
obscured as §11.1 requires — true length, bytes replaced with `0x2A`,
fingerprint of what was there.  So the validator sees the whole framing and
the password does not end up in a file.

⛔ **And it records even when the handshake does NOT succeed.**  A
`CONGEDO(GIA_ATTIVA_REMOTA)` is the object the third round of B3 exists to
produce: if the trace were written only along the path that succeeds, the only
bench of invariant I2 would deliver nothing to the arbiter (finding R8.9).

⛔ **And the exit code says WHAT happened to the connection**: `0` I
stayed attached for the whole time asked, `4` the connection or the session
dropped earlier — and the log says which of the two (findings R8.2, R8.4).
`5` no `TELA` arrived (§7.1, the silence).  ⭐ `6` — 22 August 2026 —
**the requested scene cannot be exercised**: it is the case of `--puntatore-vecchia`
when there is no previous canvas, or when the new canvas is not
smaller.  ⛔ It is not `1` and it is not `0`: a bench that read «all fine» from a
scene that did not happen would be green by construction, and a bench that
read «the product got it wrong» would give the red to the wrong defendant.
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

# ⛔⭐ AND `aioquic` MAY NOT BE THERE — 23 August 2026, phase 9.
#
#     `aioquic` lives INSIDE the container, not on the laptop.  ⚠ As long as this
#     program could do only one thing — attach to a server — a
#     `ModuleNotFoundError` at the top of the file was the right diagnosis.  ⛔ But
#     `--certifica` does not touch the network: it is a self-test of the audio screening, and
#     it must be able to run WHERE THE CODE IS WRITTEN.  With the import at the top it
#     did not even start.
#
# ⇒ We try to import, and if it is missing we carry on with placeholders: whoever
#   asks for the NETWORK finds out at once and with a line that says what to do, whoever
#   asks for `--certifica` runs anyway.  ⚠ And the placeholder RAISES: an
#   import silently faked that let a real round start would be the worst form
#   of error, «it works and measures nothing».
try:
    from aioquic.asyncio import connect
    from aioquic.asyncio.protocol import QuicConnectionProtocol
    from aioquic.h3.connection import H3_ALPN, H3Connection
    from aioquic.h3.events import HeadersReceived
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.events import QuicEvent
    AIOQUIC = None
except ModuleNotFoundError as _e:          # noqa: N816 — the name states the fact
    AIOQUIC = str(_e)

    class QuicConnectionProtocol:          # placeholder
        def __init__(self, *a, **kw):
            raise RuntimeError(f"⛔ without `aioquic` there is no network at all: {AIOQUIC}")

    class QuicEvent:                       # placeholder (needed by the annotation)
        pass

    class HeadersReceived:                 # placeholder (needed by `isinstance`)
        pass

    H3_ALPN = H3Connection = QuicConfiguration = connect = None

CLIENT, SERVER = 1, 2
T = {"CIAO": 0x0001, "ECCOMI": 0x0002, "CREDENZIALI": 0x0003, "AMMESSO": 0x0004,
     "RESPINTO": 0x0005, "ATTACCA": 0x0006, "SESSIONE": 0x0007,
     # ⭐ The CANVAS path, entered here on 16 August 2026 (sub-phase 6.6).
     #    ⛔ `fasi/06-la-tela-e-la-vista.md` §0 point 6: they had been in the protocol for
     #    a week and this client **did not send even one of them**.
     "VISTA": 0x0008, "DISPOSIZIONE": 0x0009, "CURSORE_FORMA": 0x000A,
     "ADATTA_TELA": 0x000B, "CONGEDO": 0x000C, "RICHIEDI_CHIAVE": 0x000D,
     "TELA": 0x000E, "TERMINA_SESSIONE": 0x0011}
NOME = {v: k for k, v in T.items()}
# ⛔ THE INPUT CHANNEL LIVES IN A DICTIONARY OF ITS OWN, and it is not pedantry: `NOME`
#    is the inverse map of `T` and `_sfoglia()` uses it to give a name to the
#    messages that arrive **on the control channel**.  A `0x0101` in there
#    would make the word «PUNTATORE» appear in the log for a malformed control
#    message — that is, a diagnosis that sends you to look at the wrong
#    channel.  ⚠ And the channels really are two: §2.5, high byte `0x00` versus
#    `0x01`.
T_PUNTATORE = 0x0101            # §7.3
T_PULSANTE = 0x0102             # §7.3
BOTTONE_SINISTRO = 0x110        # evdev BTN_LEFT
# The two outcomes and the three reasons of `TELA` — §7.1.
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
    """Reads a QUIC variable-length integer from `d` starting at `i`.

    Returns (value, next index), or (None, i) if the bytes are not
    enough.  ⚠ The length is in the two high bits of the first byte, and the value
    is what remains: reading the first byte whole is the mistake that makes
    0x40 0x41 look like two frames."""
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
    """Looks for `CLOSE_WEBTRANSPORT_SESSION` (0x2843) and returns its code.

    ⛔ On the CONNECT wire capsules travel **inside DATA frames**
       (RFC 9297), so the normal case is `DATA(0x00) → capsule`.  The case
       in which the capsule arrives **naked** is a server defect — a browser
       would read `0x2843` as an unknown HTTP/3 frame type and would
       throw it away (RFC 9114 §9) — and this reader recognises it in order to
       SAY it, not to forgive it.

    Returns (code, naked) or (None, False)."""
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
                return b[j + 3]      # the four bytes of the code, the lowest
            i = j + lung
        return None

    # 1. the right form: one or more DATA frames, and the capsules inside
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
    # 2. the wrong form: the capsule without the frame that carries it
    c = dentro(d)
    return (c, True) if c is not None else (None, False)


class Registratore:
    """The format of RCP.md §11.1, written once only.

    ⛔⛔ THE MAGIC IS `RCPREG 0x00 0x02`, AND UNTIL 16 AUGUST 2026 IT WAS NOT.

    ⭐ **It is the biggest defect found by sub-phase 6.6, and it was not in the
       product: it was between two benches.**  On 12 August 2026 the format of §11.1
    moved to `0x00 0x02` — the block carries the `fine` field and grows from 16 to 17
    bytes — and `01-b4-validatore.py` learned to **refuse** the old
    format, as §11.1 requires of it: *«an old validator must REFUSE the
    new format, not read it askew»*.

    ⛔ But this recorder kept on writing `0x00 0x01`.  ⇒ From that
       day **every B3 trace came out 2 from the arbiter** — «malformed
    recording» — and the five `valida` calls of `01-b3-lancia.sh` all
    failed, ⛔ making the whole bench exit **1**.  ⚠ Neither of the two
    programs was broken on its own: the validator did **exactly** what
    the specification asks of it, and the recorder wrote a format that had
    been valid until four days earlier.  It is the form of error that is born
    between two files, where no unit test looks.

    ⚠ **And the red was not mute: it was unreadable.**  «The trace is malformed»
      on a handshake bench sends you looking for a defect of the
    *recorder* — which indeed was there — but only after ruling out the server, the
    network and the protocol.  ⭐ The bench that keeps this door shut is
    `06-b38-registratore.py`, and it does not test the wire: it tests that the two benches
    speak the same language.

    ⭐⭐ **AND FROM 21 AUGUST 2026 THE MAGIC IS `0x00 0x03`: the block carries
       `istante_ms`.**

    §11.1 did not record **time**, and without time the rule of the *«grace
    second after `TELA(ADATTATA)`»* of §7.1 was not testable from any
    `.rcpreg` — it was the `[?]` of `fasi/06-la-tela-e-la-vista.md` §7.2.

    ⛔ **And the instant is MONOTONIC and RELATIVE to the first block, never a
       wall-clock time.**  §4.4 forbids secrets in the file, and an absolute date is not a
    secret by chance: it says **when** and — together with the address the
    recording already carries — **from where** a user connected.  The first
    block is 0, and whoever reads learns nothing about who recorded.

    ⛔ **And the `orologio` field in the header says WHOSE times they are**
       (1 = client, 2 = server), because the second rule belongs to the **server**
    and a trace taken at the client measures a **shorter** interval: half a
    network round trip per side.  ⇒ From here the arbiter concludes **in one direction only**, and
    declares it.  The line is in `01-b4-validatore.py`.
    """

    MAGIA = b"RCPREG\x00\x03"
    # ⛔ Yesterday's two magics are kept HERE and not only in the arbiter: the
    #    bench that refuses them (`01-b4-registrazioni.py`) writes them, and two
    #    lists of versions in two files are two lists that diverge.
    MAGIA_V1 = b"RCPREG\x00\x01"
    MAGIA_V2 = b"RCPREG\x00\x02"
    CONTINUA, FIN, RESET = 0, 1, 2
    OROLOGIO_CLIENT, OROLOGIO_SERVER = 1, 2

    def __init__(self):
        self.blocchi = []
        self.scritta = False
        # ⛔ This program is the CLIENT: the times are its own, and it says so.
        #    ⚠ Writing `2` here would mean making the arbiter believe it has
        #      the server's clock, and then the «one direction only» conclusion
        #      would become a two-direction conclusion — wrong.
        self.orologio = self.OROLOGIO_CLIENT
        self.t0 = None
        # ⛔ The control channel stream, the REAL one.  §4.2: it is the first
        #    bidirectional stream of the session, and ⚠ **it is not 0** — in
        #    HTTP/3 stream 0 is already the CONNECT one (finding R1.5).  Here we
        #    used to write a fixed `0`: a number that was never the right one, and that
        #    the arbiter uses for P3 (§2.5, «a frame on the control channel
        #    stream»).
        self.stream = 0

    def istante(self):
        """⛔ Milliseconds since the FIRST block, from a monotonic clock — §11.1.

        ⚠ `time.monotonic()` and not `time.time()`, and it is not pedantry: an
          NTP adjustment in the middle of a session would make the instants **go
          backwards**, and the arbiter would read a `PUNTATORE`
          arrived *before* the `TELA` that precedes it on the wire.
        """
        adesso = time.monotonic()
        if self.t0 is None:
            self.t0 = adesso
        ms = int((adesso - self.t0) * 1000.0)
        # ⛔ The field is u32: 49 days.  It saturates instead of wrapping, because
        #    an instant that restarts from zero is worse than an instant standing still.
        return min(ms, 0xFFFFFFFF)

    def aggiungi(self, verso, carico, oscurati=(), canale=0x00, stream=None,
                 fine=CONTINUA, istante=None):
        self.blocchi.append([verso, canale, fine,
                             self.stream if stream is None else stream,
                             carico, list(oscurati),
                             self.istante() if istante is None else istante])

    def segna_fine(self, verso, fine, stream=None):
        """⛔ How the stream closed, and from WHICH side — §11.1.

        ⭐ It is not a format detail: it is the only byte that lets
           the arbiter tell **«the server did not answer»** from **«the
        recording ends here»**.  §7.1 requires a `TELA` for every
        `ADATTA_TELA`, and without this field a trace that ends with a
        request in flight looks the same in both cases — the form of error
        **E8**, and this time on the rule with the worst symptom:
        *«the application has hung»*.

        ⚠ If the last block is already of that direction it is marked; otherwise a
          block with **zero** payload is added, which is the honest way of saying
          «from this side nothing else arrived, and then it closed».
        """
        if self.blocchi and self.blocchi[-1][0] == verso:
            self.blocchi[-1][2] = fine
            return
        self.aggiungi(verso, b"", stream=stream, fine=fine)

    def scrivi(self, percorso):
        # ⛔ The header of §11.1: magic · u32 quanti_blocchi · u8 orologio ·
        #    3 reserved bytes that MUST be 0.
        out = bytearray(self.MAGIA + struct.pack("!IBBBB", len(self.blocchi),
                                                 self.orologio, 0, 0, 0))
        for verso, canale, fine, stream, carico, osc, ist in self.blocchi:
            out += struct.pack("!BBBIQIH", verso, canale, fine, ist, stream,
                               len(carico), len(osc))
            for ini, qua, imp in osc:
                out += struct.pack("!II", ini, qua) + imp
            out += carico
        with open(percorso, "wb") as f:
            f.write(bytes(out))


# ══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE AUDIO SCREENING — §6.3, and the reorder cure of phase 9
#
# ⛔⛔ WHY THIS CLASS EXISTS, AND THE HOLE IT CLOSES — 23 August 2026.
#
#      The reorder cure was written **only in `src/pagina.html`**
#      (`audio_posto_passato`, `scartati_tardivi`, `fuori_ordine`, `doppioni`,
#      `recuperati`, `ist_max_us`).  This client — which is the second reader
#      of `RCP.md` and the one ALL the benches use — still had the rule of
#      before: `istante <= ultimo ⇒ throw away`.  ⇒ **No bench could measure whether
#      the cure bites**, because the client the benches use does not have it.
#
# ⛔⛔ AND THE DEFAULT STAYS `vecchia`, by the user's decision.
#      `01-b3-cliente.py` is used by dozens of already-measured benches: changing the
#      default behaviour would make every number already written stop being
#      comparable.  ⭐ With `--audio-regola vecchia` the counters
#      `ricevuti` and `vecchi` and the list of delivered blocks are IDENTICAL to
#      those of before — and `--certifica` case 6 checks it against a
#      literal transcription of the code of before, not against an opinion.
#
# ── THE PAGE'S RULE, IN FOUR CASES ────────────────────────────────────────
#   `[R]` src/pagina.html:6497-6572 (the wire) and 5889-6186 (`suona()`).
#
#   1. `istante == ultimo`  ⇒ **duplicate**: thrown away.  Playing it twice
#      would double the signal, which is the worst way to fail.
#      ⛔ Zero is the expected number: QUIC discards repeated packets by itself.
#   2. `istante < ultimo` (BEHIND) and its place in time has ALREADY PASSED
#      ⇒ `scartati_vecchi`: it is truly consumed, §6.3 to the letter.
#   3. `istante < ultimo` but its place **is still there** ⇒ `fuori_ordine`:
#      ⭐ IT IS KEPT, and that is the whole cure.  The anchor gives it an absolute place:
#      it does not need to arrive in order to land in it.  And the
#      debt of `mancati` is repaid (`recuperati`), or every cured overtaking would
#      show up as a loss — the cure would accuse itself.
#   4. `istante > ultimo` (THE NEWEST) ⇒ it is NEVER screened, the hole is counted
#      (`mancati`) and `ultimo` advances.  ⛔ Screening the newest too
#      would leave the anchor adrift with no possible rearm: session mute for
#      ever with all counters green (`LEZIONI.md` §2.2).
#
#   And then there is the SECOND DOOR, which in the page lives inside `suona()`: a
#   block that has passed the wire may have lost its place **while we were
#   decoding it**.  There the cases are two and not one:
#     · it is the newest we have ⇒ it is the WHOLE playback that is late:
#       the anchor is rearmed (`riarmi`), as it always has been;
#     · it is an OVERTAKEN one (`ist_max_us > istante`) ⇒ only it is late:
#       `scartati_tardivi`, and the anchor is NOT touched.  ⛔ Treating them the same
#       would cost a rearm for every overtaking, that is 250 ms of delay
#       given away for a 5 ms block.
#
# ── ⚠ THE TRANSLATION, AND WHERE IT IS **NOT** IDENTICAL TO THE PAGE ──────
#
#   The page measures «the place has passed» with `a.base + istante < ctx.currentTime`,
#   that is with the playhead of a real `AudioContext`.  Here there is neither an
#   `AudioContext` nor a decoder.  ⇒ The DECLARED differences are
#   five, and whoever reads a number from this client must know them:
#
#   T1 · **The playback clock is SIMULATED**: `ora` comes from the monotonic one
#        (or from the fake clock of `--certifica`), not from `ctx.currentTime`.
#        ⚠ A real `AudioContext` can drift from the monotonic clock by a few parts
#        per million; here the two clocks are the SAME clock, so this
#        client **cannot see the drift** between sound card and system.
#   T2 · **There is no «suspended» state**: the page, with `ctx.state !== "running"`,
#        answers «no» to the passed place and throws into `sospesi`.  Here the clock
#        always runs ⇒ `sospesi` does not exist and cannot be measured from here.
#   T3 · **Decoding costs zero**: in the page, between the wire and `suona()` there is
#        a real `AudioDecoder`, and `scartati_tardivi` is born PRECISELY from that
#        delay.  ⇒ Here the second door opens at the same instant as the
#        first and `scartati_tardivi` would stay **zero by construction** — which
#        would be a false green.  ⭐ That is why there is `ritardo_decodifica_s`: the
#        time we pretend to spend decoding.  At zero (the default
#        on the network) `scartati_tardivi` **is not a measurement, it is a blind zero**.
#   T4 · **`passo_us` does not come from a decoder**: for PCM it is COMPUTED
#        from the payload — `[S]` `RCP.md`:1299, «480 samples, 960 bytes, 5 ms per
#        datagram» — which is exact and not circular.  ⚠ For Opus we cannot
#        decode: `passo_us` stays 0 (and then, as in the page, the count
#        of `mancati` IS OFF) until it is declared with
#        `--audio-passo-us`.
#   T5 · **`Math.round` versus `round()`**: JS rounds the half upwards,
#        Python to even.  Here we write `int(x + 0.5)` by hand, or on a
#        jump of exactly 1.5 steps the two programs would count different
#        `mancati` — and it would be a difference invisible until the wrong day.
#
# ── PURITY, AND WHY THERE ARE TWO ─────────────────────────────────────────
#
#   `purezza` = **delivered at the output / arrived on the wire** — where «arrived
#   on the wire» are the conforming datagrams (right prefix, ≥12 bytes, type 0x0401)
#   and «delivered» those that end up in `a_blocchi`, that is what the
#   sound judge will be able to listen to.  ⭐ It is the definition needed here.
#
#   ⛔ And it is **NOT** the formula the page benches use
#   (`09-b74-audio-firefox.py`:300, `suonati / ricevuti`): there `ricevuti` is
#   incremented **after** the screening (`src/pagina.html`:6574), so the datagrams
#   thrown away on the wire **are neither in the numerator nor in the denominator** — and
#   that fraction is BLIND precisely to the damage this cure repairs.  It is
#   printed anyway, as `purezza_pagina`, because it is the number with which the
#   rounds on the page are compared; ⚠ in this client it is 1.000 by
#   construction with the old rule, and whoever read it alone would conclude
#   «all healthy» from a destroyed sequence.
AUDIO_CUSCINO_MS = 250          # `[R]` src/pagina.html:5550
# ⛔⛔ THE DEFAULT IS `vecchia`, and it changes ONLY by the user's decision.
REGOLA_AUDIO = "vecchia"
PASSO_AUDIO_US = 0              # 0 = derived from the PCM (T4)
DECODIFICA_AUDIO_S = 0.0        # ⚠ T3: at zero `scartati_tardivi` is blind


class VaglioAudio:
    """§6.3 and the reorder cure, with the switch between the two rules.

    ⛔ `regola="vecchia"` is the DEFAULT and is not changed from here: it is what
       keeps the already-measured numbers comparable.
    """

    REGOLE = ("vecchia", "nuova")

    def __init__(self, regola="vecchia", cuscino_ms=AUDIO_CUSCINO_MS,
                 orologio=time.monotonic, passo_us=0,
                 ritardo_decodifica_s=0.0):
        if regola not in self.REGOLE:
            raise ValueError(f"audio rule «{regola}»: the rules are {self.REGOLE}")
        self.regola = regola
        self.cuscino_s = cuscino_ms / 1000.0
        self._orologio = orologio
        self.ritardo_decodifica_s = ritardo_decodifica_s
        # ⚠ T4: 0 = I do not know, and then the count of `mancati` is OFF —
        #   as in the page, which writes `if (a.passo_us > 0)`.
        self.passo_us = passo_us
        self.passo_dichiarato = passo_us > 0
        # ── the counters, with the page's names ───────────────────────────
        self.sul_filo = 0            # conforming datagrams arrived (denominator)
        self.ricevuti = 0            # passed the wire screening
        self.consegnati = 0          # the page's `suonati`: actually output
        self.scartati_vecchi = 0     # behind, and its place has passed
        self.scartati_tardivi = 0    # overtaken, and the place passed afterwards
        self.fuori_ordine = 0        # ⭐ behind AND KEPT: the cure
        self.doppioni = 0            # the same `istante` twice
        self.recuperati = 0          # `mancati` repaid by an out-of-order one
        self.mancati = 0             # never arrived: the hole on the wire
        self.mancati_volte = 0
        self.riarmi = 0              # the anchor moved (the «HOLES»)
        self.ist_max_us = 0          # the maximum PUT IN THE SCHEDULE
        self.ultimo_istante = None   # the maximum ACCEPTED ON THE WIRE
        self.base = None             # the anchor: seconds to add to `istante`

    # ── the frontier «its place has already passed» ───────────────────────
    def _posto_passato(self, ist_us, ora):
        """`[R]` `audio_posto_passato`, src/pagina.html:5889.

        ⛔ Two cases in which the answer is «no» and not «I do not know»: `istante`
           null, and anchor not yet hooked — there NOTHING has been consumed.
        ⚠ T2: the page's third case (suspended context) is missing, because here
          the clock never stops.
        """
        if not ist_us > 0 or self.base is None:
            return False
        return self.base + ist_us / 1e6 < ora

    def _conta_mancati(self, istante):
        """`[R]` src/pagina.html:6550.  ⚠ T5: `int(x + 0.5)`, not `round()`."""
        if self.ultimo_istante is None or self.passo_us <= 0:
            return
        salto = istante - self.ultimo_istante
        quanti = int(salto / self.passo_us + 0.5) - 1
        # ⚠ The threshold is 1.5 steps and not «more than one step»: the `istante` comes
        #   from the capture and not from a metronome.
        if quanti >= 1 and salto > self.passo_us * 1.5:
            self.mancati += quanti
            self.mancati_volte += 1

    def arrivo(self, istante, codec=0, byte_carico=0):
        """A conforming datagram has arrived.  Returns `(delivered, reason)`.

        ⛔ The count of `sul_filo` is HERE and not earlier: datagrams discarded for
           prefix, length or type are not audio blocks, and putting them in the
           denominator of purity would confuse «the network reorders» with «the
           server sends garbage».
        """
        self.sul_filo += 1
        nuova = self.regola == "nuova"

        if self.ultimo_istante is not None and istante == self.ultimo_istante:
            # ⚠ With the OLD rule `doppioni` is a SUB-COUNT of
            #   `scartati_vecchi`, not a separate item: the code of before
            #   counted them in there (`istante <= ultimo`), and removing them
            #   would change every number already measured.  ⭐ Counting them anyway
            #   costs zero and says something that was not known before.
            self.doppioni += 1
            if not nuova:
                self.scartati_vecchi += 1
            return (False, "duplicate: the same `istante` twice")

        if self.ultimo_istante is not None and istante < self.ultimo_istante:
            if not nuova:
                # The rule of before, to the letter: behind ⇒ thrown away.
                self.scartati_vecchi += 1
                return (False, "istante no longer the most recent (old rule)")
            ora = self._orologio()
            if self._posto_passato(istante, ora):
                self.scartati_vecchi += 1
                return (False, "its place in time has already passed (§6.3)")
            # ⭐ OUT OF ORDER BUT STILL PLAYABLE: that is the whole cure.
            self.fuori_ordine += 1
            if self.mancati > 0:
                self.mancati -= 1
                self.recuperati += 1
        else:
            self._conta_mancati(istante)
            # ⛔ ONLY FORWARDS: `ultimo_istante` is a MAXIMUM.  Bringing it
            #    back on an out-of-order one would make the next datagram
            #    look like a huge jump, and the count of `mancati` would
            #    fill up with fake losses.
            self.ultimo_istante = istante

        self.ricevuti += 1
        return self._consegna(istante, codec, byte_carico)

    def _consegna(self, ist_us, codec, byte_carico):
        """The second door: in the page it is inside `suona()`.

        ⚠ T3: here decoding costs `ritardo_decodifica_s`, which on the network is
          zero — and with zero `scartati_tardivi` is not a measurement, it is a blind
          zero.  `--certifica` exercises it with a declared delay.
        """
        ora = self._orologio() + self.ritardo_decodifica_s
        t = ist_us / 1e6
        if self.base is None:
            self.base = ora + self.cuscino_s - t
        quando = self.base + t
        if quando < ora + 0.001:
            if self.regola == "nuova" and self.ist_max_us > ist_us:
                # ⛔ IT IS AN OVERTAKEN ONE, and only it is late: it is thrown away
                #    and the anchor stays where it is.
                self.scartati_tardivi += 1
                return (False, "overtaken, and the place passed while we were "
                               "decoding it")
            # It is the newest we have: it is the WHOLE playback that is
            # late ⇒ the anchor moves.  ⚠ It is the only thing that RAISES the
            # queue again, and it is audible.
            self.riarmi += 1
            self.base = ora + self.cuscino_s - t
        if ist_us > self.ist_max_us:
            self.ist_max_us = ist_us
        # ⚠ T4: the step from the PCM payload, not from a decoder.
        if not self.passo_dichiarato and codec == 2 and byte_carico > 0:
            self.passo_us = int(byte_carico * 5000 / 960 + 0.5)
        self.consegnati += 1
        return (True, "")

    # ── the two numbers that get printed ──────────────────────────────────
    @property
    def purezza(self):
        """Delivered at the output / arrived on the wire.  `None` = nothing to say."""
        if self.sul_filo == 0:
            return None
        return self.consegnati / self.sul_filo

    @property
    def purezza_pagina(self):
        """`suonati / ricevuti`, the formula of `09-b74`.  ⚠ Blind to the screening."""
        if self.ricevuti == 0:
            return None
        return self.consegnati / self.ricevuti

    def riga(self):
        """The counters, ALWAYS, with both rules and even at zero."""
        p, pp = self.purezza, self.purezza_pagina
        return (f"rule {self.regola} · on wire {self.sul_filo} · "
                f"received {self.ricevuti} · delivered {self.consegnati} · "
                f"PURITY {'?' if p is None else format(p, '.4f')} "
                f"(page {'?' if pp is None else format(pp, '.4f')})")

    def riga_conti(self):
        return (f"late {self.scartati_tardivi} · out {self.fuori_ordine} · "
                f"rec {self.recuperati} · dup {self.doppioni} · "
                f"missed {self.mancati} times {self.mancati_volte} · "
                f"rearms {self.riarmi} · step {self.passo_us}us")


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
        # ⛔⛔ THE RECORDER LIVES HERE, AND NOT IN THE QUEUE — 21 August 2026.
        #
        #    Until today every server message ended up in the trace **at the
        #    moment someone pulled it out of the queue** (`attendi()`
        #    and `chiedi_tela()`).  ⇒ A message that arrives when nobody is
        #    waiting — that is, during `--resta`, which is almost the whole life of
        #    a session — did NOT enter the trace at all.
        #
        # ⛔ And the two rules that fell into that hole are exactly the two that
        #    §7.1 entrusts to the arbiter:
        #      · **T1** — an UNSOLICITED `TELA`;
        #      · **V3** — a `TELA` after a `VISTA`.
        #    The arbiter knows how to accuse them (`01-b4-registrazioni.py` cases 22 and 30,
        #    `06-b38-mutazioni.py`), but on **built** recordings: from a
        #    trace of this client they could never come out.  ⇒ Round 5 of
        #    `06-b38-tela.sh` — *«no TELA after the VISTA»* — was **green by
        #    construction**, which `LEZIONI.md` says is worse than no case at all.
        #
        # ⭐ The cure is one of place, not of logic: we record where the bytes
        #    ARRIVE (`_sfoglia`), not where they are consumed.  ⚠ And this way
        #    the order of the blocks is the wire's, which is what §11.1
        #    asks for.  Found with `06-b40-lancia.sh`, cases 6 and 9.
        self.reg = None
        # ⛔ §3.1 point 3: the reason ALSO travels in the application error
        #    code with which the WebTransport session is closed.  It is
        #    kept, because it is the second of the two paths — and on the day
        #    the `CONGEDO` does not arrive it is the only one.
        self.codice_chiusura = None
        # ⛔ WHAT DROPPED, AND WHEN — findings R8.2 and R8.4 of 10 August 2026.
        #
        #    B3 asks twice «is the first one still attached?», and both
        #    times it read it from the EXISTENCE OF THE PROCESS or from its exit
        #    code.  ⚠ But this program, after SESSIONE, just slept:
        #    the connection could die from QUIC's idle cap, or
        #    the session could be closed by the server, and the process stayed
        #    alive and exited 0 all the same.  The bench read «alive» from a fact it
        #    had not observed (E7: verify from the sending side).
        #
        # ⭐ Here we observe from the receiving side: whoever drops says so, with the name
        #    of WHAT dropped — and the two cases are not confused, because
        #    «QUIC closed by itself» and «the server closed the session» are the
        #    two defendants the fourth round exists to separate.
        self.caduta = None
        # ═══ THE AUDIO — phase 7 ══════════════════════════════════════════
        # ⛔ The counters are SIX and not one, and each names a different rule
        #    of §6.3: whoever summed them would get a number that never says
        #    where to look (`LEZIONI.md` §2.2).
        self.a_ricevuti = 0      # datagrams arrived and conforming
        self.a_corti = 0         # < 12 bytes: §6.3 has them discarded
        self.a_tipo = 0          # `tipo` != 0x0401
        self.a_prefisso = 0      # the RFC 9297 prefix is not our session
        self.a_vecchi = 0        # `istante` no longer the most recent: §6.3
        self.a_codec = None      # the codec declared in the datagrams
        self.a_byte = 0
        # ⭐ THE SCREENING — phase 9.  ⛔ The rule comes from a module
        #    variable and not from the constructor because `create_protocol=Cliente`
        #    passes no arguments; the default is `vecchia` in two places (here
        #    and in `--audio-regola`), and they agree on purpose.
        self.a_vaglio = VaglioAudio(regola=REGOLA_AUDIO, passo_us=PASSO_AUDIO_US,
                                    ritardo_decodifica_s=DECODIFICA_AUDIO_S)
        # The blocks as they arrived, for the judge of `07-b42`.
        self.a_blocchi = []
        self.caduto = asyncio.Event()
        # ⛔ AND THE THIRD CAUSE: THAT WE CLOSED THE CONNECTION OURSELVES.
        #
        #    `[M]` 10 August 2026, third round: the `--resta` window expires,
        #    this program exits 0, and `connect()` closes the connection
        #    leaving its context — aioquic raises `ConnectionTerminated`
        #    code 0 with no reason, and the line below ended up in the log
        #    IDENTICAL to that of a server that ousts you.  The bench
        #    found it with a grep over the whole file and gave the red to the server,
        #    which had just kept the session alive with PINGs for 25 s.
        #
        # ⭐ «Terminated by us» and «terminated by someone else» are two different
        #    facts and now they have two different lines (CODER.md §3.9, §4.2).
        self.chiusa_da_noi = False
        # ═══ THE CLIPBOARD — phase 7, §7.4 ════════════════════════════════
        # ⛔ THIS CLIENT IS THE SECOND READER OF `RCP.md` (`PIANO.md` §1.1),
        #    and the three messages of §7.4 come in here because otherwise the clipboard
        #    wire would be validated by ONE SINGLE implementation — the
        #    page, written by the same hand as the server.
        #
        # ⚠ Assembly is PER STREAM, not a single one: §2.5 says «one stream per
        #   transfer», so there is more than one alive at once.  ⛔ With a
        #   single accumulator two interleaved transfers would get mixed, and that is
        #   exactly the defect the identifier of §7.4 exists to
        #   remove — finding it here would mean never finding it.
        self.app_in = {}          # stream_id -> bytearray, the assembly
        self.app_mio_id = 0       # §7.4: each side numbers its OWN, from 1
        self.app_mio_testo = ""
        self.app_suo_id = 0       # the server's last announcement
        self.app_suo_len = 0
        self.app_ricevuto = None  # the last text the server sent us
        self.app_annunci = []     # [(id, bytes)] all the server's announcements
        self.app_chiesti = []     # [id] the transfers the server asked us for
        self.app_serviti = 0
        self.app_violazioni = []  # what does NOT match §7.4, with its name
        self.app_evento = asyncio.Event()
        # The preamble of the server's unidirectional streams, per stream:
        # `0x40 0x54` plus the session varint.  `None` = not ours.
        self.uni_pref = {}
        self.uni_genere = {}
        # ═══ THE VIDEO TAKEN FROM THE WIRE — phase 3/7, 17 August 2026 ════
        # ⛔ NOT to paint it: to SEPARATE our stream from the
        #    browser's decoder.  «The artefacts are ours» and «they are
        #    its» look the same when watching the screen, and they are told apart in
        #    one way only — by giving the SAME BYTES to a third decoder that
        #    is neither of the two (`ffmpeg`/`dav1d`).
        # ⚠ And the bytes are those of the WIRE, not those of the survey: between the
        #   encoder and the browser there is the whole transport, and a defect there
        #   in the middle the survey would not see.
        self.v_in = {}          # stream_id -> bytearray being assembled
        # ⛔ The streams already recorded: the §6.2 header is written ONCE
        #    per stream, or a single canvas would appear ten times and the
        #    denominator of T4 would count frames that are not there.
        self.v_reg = set()
        self.v_fotogrammi = []  # [(number, key, width, height, data)]
        # ═══ THE INPUT CHANNEL — §2.5, §7.3, and 22 August 2026 ═══════════
        # ⛔ `RCP.md` §2.5: «**only one**, opened after receiving `SESSIONE`
        #    and kept open».  ⚠ It is NOT like the clipboard, where every
        #    transfer has its own stream: here one stream per message
        #    would be **another protocol**, and the server that counts the `id`s
        #    «over the whole channel» (§7.3) would no longer have a channel on which to
        #    count them.
        self.inp_stream = None
        # §7.3: «increasing, starts from 1.  ⛔ 0 is reserved».
        self.inp_id = 0
        # ⭐ THE **RECORDED** INSTANT OF THE LAST `TELA`, and not the time of
        #    now: the grace second is arbitrated by §11.1 on `istante_ms`, and
        #    a delay counted on a clock different from the one that ends up
        #    in the file would give a `dt` that is not the one the arbiter reads.
        self.ultimo_tela_ms = None

    def _cade(self, perche: str) -> None:
        """The first cause wins: the following ones are consequences, not causes."""
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
        # ⛔ RCP.md §4.2: the control channel is the FIRST bidirectional
        #    stream of the session.  ⚠ And it is NOT «stream 0»: in
        #    HTTP/3 stream 0 is already the CONNECT one that establishes the
        #    session, and the API exposes no number (finding R1.5).
        self.controllo = self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=False)
        return self.controllo

    def manda(self, dati):
        self._quic.send_stream_data(self.controllo, dati, end_stream=False)
        self.transmit()

    # ══════════════════════════════════════════════════════════════════════
    # THE INPUT — §7.3, and the single channel of §2.5
    # ══════════════════════════════════════════════════════════════════════

    def apri_input(self):
        """The input channel stream: **only one**, and it is kept open.

        ⛔ It is opened the first time it is needed, and not at every message: §2.5
           says «only one … and kept open», and §7.3 counts the `id`s «over the whole
           channel».  ⚠ Opening it and not closing it is not an oversight: closing it
           with FIN would tell the server «the client sends no more input», which is
           a different thing from what this bench wants to say.
        """
        if self.inp_stream is None:
            self.inp_stream = self._http.create_webtransport_stream(
                self.sessione, is_unidirectional=True)
        return self.inp_stream

    def manda_puntatore(self, x, y):
        """⭐ `PUNTATORE(x, y)` — §7.3, coordinates on the **canvas**.

        ⛔ And it is recorded with channel `0x01` and with the REAL stream: §11.1
           defines the `canale` field as «the high byte of `tipo`», and
           the arbiter **refuses** a block in which the two do not match — a
           recording that declared `0x00` would make these bytes be read
           as if they were control, and the second rule would never come out
           of this trace.
        """
        sid = self.apri_input()
        self.inp_id += 1
        # ⛔ §7.3: «microseconds of the CLIENT's monotonic clock», and «the
        #    client writes TRUE microseconds and MUST NOT suggest a
        #    precision it does not have» (finding R1.27).  ⚠ Here the grain is that
        #    of CPython's `time.monotonic()` — nanoseconds on the Linux kernel —
        #    so nothing is multiplied by a thousand.
        ist_us = int(time.monotonic() * 1_000_000)
        b = inquadra(T_PUNTATORE,
                     struct.pack("!IQII", self.inp_id, ist_us, x, y))
        self._quic.send_stream_data(sid, b, end_stream=False)
        self.transmit()
        ms = None
        if self.reg is not None:
            self.reg.aggiungi(CLIENT, b, canale=0x01, stream=sid)
            ms = self.reg.blocchi[-1][6]
        return self.inp_id, ms

    def manda_pulsante(self, premuto, codice=BOTTONE_SINISTRO):
        """⭐ `PULSANTE` — §7.3, **evdev** code, pressed/released.

        ⛔ It serves one reason only and it must be written down: **giving FOCUS to a
           window of the remote desktop**.  `[M]` 20 Sep 2026, `gnome` box:
           on Mutter the clipboard is granted to whoever has the active window, and in
           a remote session nobody clicks ⇒ neither `wl-copy` nor `wl-paste` nor
           a GTK application manage to touch the clipboard, and the clipboard mesh
           could not judge.  ⭐ With the click, sent from here —
           through the product, not bypassing it — focus arrives and the
           clipboard behaves as it does for a person.
        """
        sid = self.apri_input()
        self.inp_id += 1
        ist_us = int(time.monotonic() * 1_000_000)
        b = inquadra(T_PULSANTE,
                     struct.pack("!IQHB", self.inp_id, ist_us, codice,
                                 1 if premuto else 0))
        self._quic.send_stream_data(sid, b, end_stream=False)
        self.transmit()
        if self.reg is not None:
            self.reg.aggiungi(CLIENT, b, canale=0x01, stream=sid)
        return self.inp_id

    # ══════════════════════════════════════════════════════════════════════
    # THE CLIPBOARD — §7.4, and the three messages read from `RCP.md` and not from the C
    # ══════════════════════════════════════════════════════════════════════

    def appunti_manda(self, tipo, corpo):
        """A clipboard channel message, on its unidirectional stream.

        ⛔ One stream per message, and it is closed with FIN.  §2.5 says «one per
           transfer» and this client chose the strictest reading —
           the same as the server's — because what binds the messages of a
           transfer is the `trasferimento` field (§7.4), not the stream.
           ⚠ If the two implementations had read §2.5 differently, the
             wire would work all the same: it is the proof that the line is ambiguous and
             that the ambiguity does not bite.  It goes in the phase document.
        """
        sid = self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=True)
        self._quic.send_stream_data(sid, inquadra(tipo, corpo), end_stream=True)
        self.transmit()
        return sid

    def appunti_annuncia(self, testo):
        """«I have new text» — §7.4, `APPUNTI_ANNUNCIO`."""
        d = testo.encode("utf-8")
        self.app_mio_id = 1 if self.app_mio_id >= 0xFFFFFFFF else self.app_mio_id + 1
        self.app_mio_testo = testo
        self.appunti_manda(0x0201, struct.pack("!II", self.app_mio_id, len(d)))
        print(f"   [app]  announced transfer {self.app_mio_id}, "
              f"{len(d)} bytes")
        return self.app_mio_id

    def appunti_chiedi(self, trasferimento=None):
        """«Send it to me» — §7.4, `APPUNTI_CHIEDI`."""
        t = self.app_suo_id if trasferimento is None else trasferimento
        self.appunti_manda(0x0202, struct.pack("!I", t))
        print(f"   [app]  asked for transfer {t}")
        return t

    def _appunti_uno(self, tipo, corpo):
        """A whole clipboard channel message, already unrolled from §6.1."""
        if tipo == 0x0201:                                   # ANNUNCIO
            if len(corpo) != 8:
                self.app_violazioni.append(
                    f"APPUNTI_ANNUNCIO with {len(corpo)} bytes: §7.4 wants 8")
                return
            t, n = struct.unpack("!II", corpo)
            self.app_suo_id, self.app_suo_len = t, n
            self.app_annunci.append((t, n))
            print(f"   [app]  ⭐ the server announces transfer {t}, {n} bytes")
            self.app_evento.set()
            return
        if tipo == 0x0202:                                   # CHIEDI
            if len(corpo) != 4:
                self.app_violazioni.append(
                    f"APPUNTI_CHIEDI with {len(corpo)} bytes: §7.4 wants 4")
                return
            (t,) = struct.unpack("!I", corpo)
            self.app_chiesti.append(t)
            print(f"   [app]  ⭐ the server asks for transfer {t}")
            # ⛔ §7.4: «an identifier that matches no live announcement
            #    is ERRORE_PROTOCOLLO».  ⚠ Here the session is NOT closed:
            #    this is a bench, and its job is to RECORD that the
            #    server got it wrong, not to punish it — if it closed, the round
            #    would end and nobody would read anything any more.
            if t == 0 or t > self.app_mio_id:
                self.app_violazioni.append(
                    f"APPUNTI_CHIEDI for transfer {t}, and I have "
                    f"announced {self.app_mio_id} (§7.4)")
                return
            d = self.app_mio_testo.encode("utf-8")
            self.appunti_manda(0x0203, struct.pack("!I", t) + d)
            self.app_serviti += 1
            print(f"   [app]  served {len(d)} bytes to the server (transfer {t})")
            self.app_evento.set()
            return
        if tipo == 0x0203:                                   # TESTO
            if len(corpo) < 4:
                self.app_violazioni.append(
                    f"APPUNTI_TESTO with {len(corpo)} bytes: §7.4 wants >= 4")
                return
            (t,) = struct.unpack("!I", corpo[:4])
            d = corpo[4:]
            if t != self.app_suo_id:
                self.app_violazioni.append(
                    f"APPUNTI_TESTO for transfer {t}, and the live announcement "
                    f"is {self.app_suo_id} (§7.4)")
            if len(d) != self.app_suo_len:
                self.app_violazioni.append(
                    f"APPUNTI_TESTO carries {len(d)} bytes and the announcement "
                    f"declared {self.app_suo_len} (§7.4)")
            # ⛔ §5.4: «the text MUST be UTF-8».  It is decoded STRICTLY: a
            #    lenient decoder would put replacement characters
            #    in place of an error, and the bench would say green on a text that
            #    is not the one that had been copied.
            try:
                self.app_ricevuto = d.decode("utf-8")
            except UnicodeDecodeError as e:
                self.app_violazioni.append(f"APPUNTI_TESTO is not UTF-8: {e}")
                self.app_ricevuto = None
            print(f"   [app]  ⭐ {len(d)} bytes arrived from the server "
                  f"(transfer {t})")
            self.app_evento.set()
            return
        self.app_violazioni.append(
            f"type {tipo:#06x} on the clipboard channel: §7.4 defines THREE")

    def _decidi_canale(self, sid, carico, fine):
        """The high byte of `tipo` gives the channel (§2.5), and now it is here."""
        self.uni_pref.pop(sid, None)
        if carico[0] == 0x02:
            self.uni_genere[sid] = "wt"
            self._appunti_stream(sid, carico, fine)
        elif carico[0] == 0x03:
            self.uni_genere[sid] = "video"
            self._video_stream(sid, carico, fine)
        else:
            # ⚠ A channel this client does not serve: it SAYS so instead of
            #   keeping quiet — «received and not used» and «never arrived» must not
            #   look the same.
            self.uni_genere[sid] = "altro"
            print(f"   [wt]   ⚠ uni stream {sid}, channel 0x{carico[0]:02x}: "
                  f"legitimate and not served by this client (§2.5)")

    def _video_stream(self, sid, dati, fine):
        """A stream of the VIDEO channel (§6.2): one stream, one frame.

        ⛔ And the end of the stream IS the end of the frame — but **only with a
           FIN**: a reset stream carries an incomplete frame, which §6.2
           requires to be THROWN AWAY and not handed to the decoder.
        ⚠ Here `aioquic` does not tell the two cases apart on this path, so we
          record what we saw and declare it: whoever reads the file knows that
          the frames are those finished with FIN.
        """
        b = self.v_in.setdefault(sid, bytearray())
        b += dati
        # ⛔⛔ AND FROM 21 AUGUST 2026 THE 28 BYTES OF §6.2 END UP IN THE TRACE.
        #
        #    Until this morning the recording carried **only the control
        #    channel**, and on a trace without video the arbiter cannot
        #    conclude anything about **T4** — *«a server that answers
        #    `TELA(ADATTATA)` without touching the stage»*, which is the declared
        #    crack of all of 6.6.  ⚠ `[M]` the first real round against the
        #    product, 21 August: five traces, and on all of them the arbiter
        #    wrote *«after it the recording carries NO
        #    frame: NOT judged»*.  A rule that never has an
        #    input is a rule that is not there.
        #
        # ⛔⛔ AND THE **WHOLE** STREAM IS RECORDED, not just the 28 bytes —
        #     and the first draft did the other thing, for an hour.
        #
        #  It seemed clever: the arbiter judges size, number and codec, which are
        #  all in the header, and the pixels are megabytes nobody reads.
        #  ⛔ **But a 28-byte block marked `fine = 0` tells the arbiter a
        #  false thing**: it says «of this stream I recorded everything that
        #  passed, and it was not finished».  ⇒ The frame judge never
        #  consumed those streams, and the next frame — a legitimate delta —
        #  reached it as **the first of the session**.
        #
        #  `[M]` 21 August 2026, real round on 7721: *«stream 23: the first
        #  frame of the session is a DELTA — §5.2»*.  ⛔ **An accusation against the
        #  PRODUCT born from an incomplete recording of mine**, and it is the worst
        #  thing a bench can do: §11.1 wants the bytes, and a trace
        #  that carries a piece of them while declaring itself whole is no longer an arbiter.
        #
        # ⚠ The price is the size of the file, and it is paid: whoever wants small
        #   traces shortens `--resta`, not the wire.
        if self.reg is not None:
            self.v_reg.add(sid)
            self.reg.aggiungi(SERVER, bytes(dati), canale=0x03, stream=sid,
                              fine=Registratore.FIN if fine
                              else Registratore.CONTINUA)
        if not fine:
            return
        del self.v_in[sid]
        if len(b) < 28:
            print(f"   [vid]  ⛔ stream {sid} finished with {len(b)} bytes: §6.2 "
                  f"wants 28 of header")
            return
        tipo, codec, l, a, numero, istante, inp = struct.unpack("!HHIIIQI", bytes(b[:28]))
        self.v_fotogrammi.append((numero, tipo == 0x0301, l, a, bytes(b[28:])))

    def _appunti_stream(self, sid, dati, fine):
        """The bytes of a unidirectional SERVER stream, clipboard channel.

        ⛔ The WebTransport preamble is consumed here: `0x40 0x54` plus the
           session varint.  ⚠ And it is kept per stream, because a
           packet can cut it in the middle.
        """
        b = self.app_in.setdefault(sid, bytearray())
        b += dati
        while True:
            if len(b) < 6:
                break
            tipo, lung = struct.unpack("!HI", b[:6])
            if len(b) < 6 + lung:
                break
            corpo = bytes(b[6:6 + lung])
            del b[:6 + lung]
            self._appunti_uno(tipo, corpo)
        if fine:
            if b:
                self.app_violazioni.append(
                    f"clipboard stream {sid} finished with {len(b)} bytes "
                    "that do not make a message (§6.1)")
            self.app_in.pop(sid, None)

    def _audio_datagram(self, d: bytes) -> None:
        """A WebTransport datagram: RFC 9297 prefix, then §6.3.

        ⛔ Every discard has its OWN counter.  «I heard nothing» must be able to
           say *why*: the wrong prefix, the wrong type, the short block
           and the old block are four different defects with the same
           symptom, and without four counters one searches for hours on the wrong
           side.
        """
        # The prefix: a quarter of the identifier of the session stream.
        q, i = _varint(d, 0)
        if q is None:
            self.a_prefisso += 1
            return
        if self.sessione is not None and q != self.sessione // 4:
            # ⛔ It is not a wrapper detail: a wrong prefix makes the
            #    BROWSER discard the datagram, with no error anywhere
            #    — that is, «the audio does not arrive» and that is all.
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
        # §6.3: «the receiver discards datagrams that arrive late compared to
        # those already consumed» — and WHAT «already consumed» means is decided by
        # `--audio-regola`.  ⛔ The default is `vecchia`: with it, these
        # lines do exactly what they did before 23 August 2026.
        consegnato, _perche = self.a_vaglio.arrivo(istante, codec, len(c) - 12)
        self.a_vecchi = self.a_vaglio.scartati_vecchi
        self.a_ricevuti = self.a_vaglio.ricevuti
        if not consegnato:
            return
        self.a_byte += len(c) - 12
        if self.a_codec is None:
            self.a_codec = codec
            print(f"   [audio] ⭐ first datagram: codec {codec} "
                  f"({'Opus' if codec == 1 else 'PCM' if codec == 2 else '⛔ unknown'}), "
                  f"{len(c) - 12} bytes of payload, prefix {q} "
                  f"(session {self.sessione})")
        elif self.a_codec != codec:
            # ⚠ The codec does not change mid-session: §4.3 negotiates it once.
            print(f"   [audio] ⛔ the codec has CHANGED: {self.a_codec} → {codec}")
            self.a_codec = codec
        self.a_blocchi.append({"istante": istante, "codec": codec,
                               "byte": bytes(c[12:])})

    def quic_event_received(self, event: QuicEvent) -> None:
        nome = type(event).__name__
        # ═══ THE AUDIO — phase 7, `RCP.md` §6.3 ═══════════════════════════
        #
        # ⛔ The datagram is read HERE, before anything else, and is NOT passed
        #    to aioquic's H3 layer: it is a WebTransport datagram, not a pure
        #    HTTP/3 one, and its first field is the RFC 9297 prefix.
        #
        # ⚠ And what this reader does beyond the browser is the REASON
        #   it exists (`PIANO.md` §1.1): the browser says «I hear nothing»;
        #   this one says WHICH rule of §6.3 was violated and at which byte.
        if nome == "DatagramFrameReceived":
            self._audio_datagram(event.data)
            return
        # ⛔ THE END OF THE CONNECTION IS PRINTED, ALWAYS.
        #
        #    It is the only line that tells «QUIC's idle cap
        #    closed» from «the server freed the slot leaving the
        #    connection open».  Without it, the fourth round of B3 concluded the second
        #    by looking at /proc, which only says that a sleeping process is
        #    not dead (R8.2).
        if nome == "ConnectionTerminated":
            da_noi = " — CLOSED BY US, window over" if self.chiusa_da_noi else ""
            print(f"   [quic] connection TERMINATED: code "
                  f"{getattr(event, 'error_code', '?')} · "
                  f"{getattr(event, 'reason_phrase', '') or '(no reason)'}"
                  f"{da_noi}")
            self._cade(f"connection TERMINATED ({getattr(event, 'reason_phrase', '') or 'no reason'})")
            self.messaggi.put_nowait(None)
            return
        if nome == "StreamDataReceived" and event.stream_id == self.controllo:
            self.arrivati += event.data
            self._sfoglia()
            if event.end_stream:
                self.finito = True
                self._cade("the control channel has closed")
                self.messaggi.put_nowait(None)
            # ⛔ AND the event is NOT passed to `aioquic`'s H3 layer.
            #
            #    `[M]` 10 August 2026: passing it on, the first handshake
            #    died with `CONNECTION_CLOSE 0x105 — DATA frame is not
            #    allowed in this state`, that is the CLIENT killing the
            #    connection while the server was working well.
            #
            # ⚠ It is the asymmetry already seen on 9 August: `aioquic` 1.2 can
            #   CREATE a WebTransport stream and cannot RECOGNISE it when
            #   it answers — so its HTTP/3 layer reads `ECCOMI` as a
            #   DATA frame on a request stream.  The B2 bench had not
            #   noticed because the echo was four bytes; one hundred and sixteen
            #   are enough to bring everything down.
            return
        # ⛔⭐ THE SERVER'S UNIDIRECTIONAL STREAMS — §2.5, and through here pass the
        #     video (0x03) and the clipboard (0x02).  ⚠ Not all of them are ours: among
        #     the server's unidirectional ones there are the HTTP/3 control channel
        #     and the two QPACK ones, which belong to `aioquic`.  A
        #     WebTransport stream is recognised by its type, `0x54` — which like `0x41`
        #     does not fit in a byte: on the wire they are `0x40 0x54`.
        # ⛔⭐ THE SERVER'S UNIDIRECTIONAL STREAMS — §2.5: through here pass the
        #     video (0x03) and the clipboard (0x02).  ⚠ Not all of them are ours: among
        #     the server's unidirectional ones there are the HTTP/3 control channel
        #     and the two QPACK ones, which belong to `aioquic`.
        #
        # ⛔⛔ AND WE DECIDE ONLY WHEN THERE IS SOMETHING TO DECIDE — three times in one evening
        #      the defect was the same, and it is worth writing down once
        #      and for all: **classifying on bytes that have not arrived yet**.
        #
        #      1. TWO bytes were expected to recognise the preamble, and the
        #         QPACK streams carry ONE ⇒ swallowed, and the server
        #         dismissed us for `TEMPO_SCADUTO`;
        #      2. the «other» verdict had no branch of its own ⇒ the video bytes
        #         ended up in the HTTP/3 layer;
        #      3. `[M]` **the first packet of a video stream carries only the
        #         preamble — `40 54 00`, three bytes, payload ZERO** ⇒ we decided
        #         «it is neither clipboard nor video» on a stream that was video, and
        #         threw away all the rest.
        #
        # ⇒ The rule: until the deciding byte has arrived, the state is
        #   «I know it is ours and I do not know yet what it is» — which is a
        #   TRUE state, not a verdict.  ⛔ `LEZIONI.md` §1.9: «I do not know» and «it is
        #   not» must not look the same.
        if nome == "StreamDataReceived" and (event.stream_id & 0x03) == 0x03:
            sid = event.stream_id
            if os.environ.get("B3_SPIA"):
                print(f"   [spia] uni {sid} genere={self.uni_genere.get(sid)} "
                      f"len={len(event.data)} fin={event.end_stream} "
                      f"primi={bytes(event.data[:6]).hex()}")
            g = self.uni_genere.get(sid)
            if g == "h3":
                pass                       # it belongs to `aioquic`: left to it
            elif g == "wt":
                self._appunti_stream(sid, event.data, event.end_stream)
                return
            elif g == "video":
                self._video_stream(sid, event.data, event.end_stream)
                return
            elif g == "altro":
                return                     # ours, and this client does not serve it
            elif g == "wt-attesa":
                # The preamble is already here: the byte that gives the channel is missing.
                p = self.uni_pref.setdefault(sid, bytearray())
                p += event.data
                if p:
                    self._decidi_canale(sid, bytes(p), event.end_stream)
                return
            else:
                # ⛔ We decide on the FIRST byte: a WebTransport stream starts
                #    with `0x40` (the varint of type 0x54 does not fit in a byte);
                #    any other first byte belongs to `aioquic`, and its bytes
                #    must not pass through here even for one round.
                if not event.data:
                    return
                if event.data[0] != 0x40:
                    self.uni_genere[sid] = "h3"
                else:
                    p = self.uni_pref.setdefault(sid, bytearray())
                    p += event.data
                    if len(p) < 2:
                        return
                    if p[1] != 0x54:
                        self.uni_genere[sid] = "altro"
                        self.uni_pref.pop(sid, None)
                        print(f"   [wt]   ⚠ uni stream {sid} starts with 0x40 "
                              f"0x{p[1]:02x}: it is not WebTransport, and its bytes "
                              f"have been held back")
                        return
                    q, i = _varint(bytes(p), 2)
                    if q is None:
                        return         # the session varint is not all here
                    resto = bytes(p[i:])
                    self.uni_genere[sid] = "wt-attesa"
                    self.uni_pref[sid] = bytearray(resto)
                    if resto:
                        self._decidi_canale(sid, resto, event.end_stream)
                    return
        if nome == "StreamDataReceived" and event.stream_id == self.sessione:
            # the session close capsule (§3.1 point 3)
            codice, nuda = _capsula_chiusura(event.data)
            if codice is not None:
                if nuda:
                    # ⛔ The NAKED capsule, without the DATA frame that carries it.
                    #
                    #    It is what this server did until 10 August 2026
                    #    (finding R10.1): on the CONNECT wire capsules
                    #    travel INSIDE DATA frames (RFC 9297), and a browser
                    #    that reads `0x2843` as an HTTP/3 frame type finds it
                    #    unknown and **ignores** it (RFC 9114 §9).  The reason
                    #    did not arrive, and only the FIN remained — that is `codice 0`.
                    #
                    # ⭐ The bench reads it anyway, but DECLARES it: a lenient
                    #    client that accepted both forms without saying
                    #    which it saw would hide that defect again, and
                    #    that is the leniency `REVIEWER.md` §5 forbids.
                    print("   [wt]   ⛔ NAKED close capsule, without a DATA "
                          "frame: a browser would ignore it (RFC 9297)")
                self.codice_chiusura = codice
                print(f"   [wt]   session closed by the server, code {codice:#04x}"
                      f" = {MOTIVI.get(codice, '?')}")
                self._cade(f"session closed by the server, code {codice:#04x}"
                           f" = {MOTIVI.get(codice, '?')}")
            if event.end_stream:
                self.finito = True
                self._cade("the WebTransport session has closed")
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
            # ⛔ RECORDED HERE, on arrival: see the box on `self.reg`.
            if self.reg is not None:
                self.reg.aggiungi(SERVER, grezzo)
                # ⭐ The instant the arbiter will read in the file, taken where the
                #    file takes it.  ⛔ Not `time.monotonic()` of now: the
                #    `dt` of the grace second is counted between TWO `istante_ms`
                #    of §11.1, and counting it on a different clock would mean
                #    that the delay declared by the bench and the one read
                #    by the arbiter are two different numbers — that is exactly
                #    the error the boundary of the second does not forgive.
                if NOME.get(tipo) == "TELA":
                    self.ultimo_tela_ms = self.reg.blocchi[-1][6]
                if NOME.get(tipo) in ("TELA", "CURSORE_FORMA") \
                        and self.messaggi.qsize() > 0:
                    # ⚠ «It arrived while there were already others in the queue» is not
                    #   a violation: it is a fact, and whoever watches must
                    #   be able to read it without opening the trace.
                    print(f"   ·  [filo] {NOME.get(tipo)} arrived with "
                          f"{self.messaggi.qsize()} messages already in the queue")
            self.messaggi.put_nowait((tipo, corpo, grezzo))


async def attendi(cli, quale, attesa=10.0, reg=None):
    m = await asyncio.wait_for(cli.messaggi.get(), timeout=attesa)
    if m is None:
        raise RuntimeError(f"the control channel has closed: {cli.caduta}")
    tipo, corpo, grezzo = m
    nome = NOME.get(tipo, f"{tipo:#06x}")
    # ⛔ WHAT ARRIVES IS RECORDED, NOT WHAT WAS HOPED FOR — finding R8.9.
    #
    #    The recording was written only along the path that succeeds: a
    #    `CONGEDO(GIA_ATTIVA_REMOTA)` made the exception below be raised
    #    BEFORE being put in the trace, and `b3-terza.rcpreg` — that is
    #    the only object the third round exists to produce — never reached
    #    the B4 arbiter.  ⭐ The refusal is a measurement, not an accident.
    #    ⭐ And from 21 August 2026 the `reg.aggiungi()` line is NO longer here: it
    #       records on ARRIVAL, inside `Cliente._sfoglia()`, or the messages that
    #       nobody waits for do not enter the trace (box in `__init__`).
    #       ⚠ `reg` stays in the signature because the callers pass it, and
    #         removing it would be a wider change than needed.
    if quale and nome != quale:
        if nome == "CONGEDO":
            motivo = corpo[0] if corpo else 0
            raise RuntimeError(
                f"CONGEDO instead of {quale}: reason {motivo:#04x} = "
                f"{MOTIVI.get(motivo, '?')}")
        if nome == "RESPINTO":
            motivo = corpo[0] if corpo else 0
            raise RuntimeError(
                f"RESPINTO: reason {motivo:#04x} = {MOTIVI.get(motivo, '?')}")
        raise RuntimeError(f"expected {quale}, arrived {nome}")
    return nome, corpo, grezzo


async def chiedi_tela(cli, reg, lar, alt, tetto):
    """⭐ `ADATTA_TELA(lar, alt)` and the wait for `TELA` — RCP.md §7.1.

    Returns `(esito, motivo, tela_lar, tela_alt, ms)`, or `None` if the
    cap expires **with no answer at all**.

    ⛔⛔ THE CAP IS THE MEASUREMENT, NOT A CONVENIENCE.

    §7.1: *«To every `ADATTA_TELA` the server MUST answer with a `TELA`,
    successful or not.  A silence leaves the client waiting for ever for an
    answer that will not come, and the symptom is "the application has
    hung"»*.  ⇒ A test client that waited **without a cap**
    would reproduce the symptom instead of measuring it: the bench would stay hung, and
    whoever watches would say «the bench has hung» — which is the same sentence, from the
    wrong side.

    ⚠ And the cap is NOT a protocol rule: §7.1 does not say **within
      how long**.  ⛔ So the expiry is not recorded as a violation by the
      client: what is recorded is the **silence**, and the one to judge it is the arbiter, which
      reads the bytes and the `fine` field of §11.1.  The client measures; the verdict
      belongs to `01-b4-validatore.py`.

    ⚠ And whatever arrives IN THE MEANTIME is recorded — `CURSORE_FORMA` and the
      frames arrive when they like — because a trace with holes
      cannot be judged: §11.1 wants the bytes, not the ones we were expecting.
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
            print(f"   ⛔ NO TELA after {ms:.0f} ms: §7.1 wants an answer "
                  f"«successful or not».  ⚠ It is the silence that «leaves the client "
                  f"waiting for ever»")
            return None
        try:
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=resta)
        except asyncio.TimeoutError:
            continue
        if m is None:
            print(f"   ⛔ the channel closed while I was waiting for the TELA: "
                  f"{cli.caduta}")
            return None
        tipo, corpo, grezzo = m
        # ⭐ (recorded on arrival by `Cliente._sfoglia()`, not here)
        nome = NOME.get(tipo, f"{tipo:#06x}")
        if nome != "TELA":
            print(f"   ·  in the meantime: {nome} ({len(corpo)} bytes)")
            if nome == "CONGEDO":
                mot = corpo[0] if corpo else 0
                print(f"   ⛔ CONGEDO instead of the TELA: reason {mot:#04x} = "
                      f"{MOTIVI.get(mot, '?')}")
                return None
            continue
        ms = (time.monotonic() - t0) * 1000
        if len(corpo) < 10:
            print(f"   ⛔ TELA with a body of {len(corpo)} bytes: §7.1 wants "
                  f"10 (u8, u8, u32, u32) — the bytes are in the trace")
            return None
        es, mot = corpo[0], corpo[1]
        tl, ta = struct.unpack("!II", corpo[2:10])
        print(f"   ← TELA {TELA_ESITO.get(es, es)}"
              f"/{TELA_MOTIVO.get(mot, mot)} canvas in force {tl}x{ta} "
              f"after {ms:.0f} ms")
        return es, mot, tl, ta, ms


def scrivi_video(a, cli):
    """The frames taken from the wire, for a THIRD decoder.

    ⛔ And it is called AFTER the `--resta` wait, not before: at the line where the
       session opens no frame has arrived yet, and an
       empty file would say «the server sends no video» about a server that sends it.
       ⚠ It cost a round, on 17 August 2026 — a bench defect with the
         face of a product defect, the third of the day.
    """
    if not a.video_scrivi or not cli.v_fotogrammi:
        if a.video_scrivi:
            print("   [vid]  ⛔ no frame taken from the wire: no file")
        return
    # ⛔ The frames are concatenated IN THE ORDER OF THE NUMBER (§6.2): the streams
    #    are independent and can arrive out of order, and a stream put back
    #    in line badly would give artefacts that would be OURS, the bench's — that is
    #    the wrong answer to the question this file exists to ask.
    ordinati = sorted(cli.v_fotogrammi, key=lambda f: f[0])
    with open(a.video_scrivi, "wb") as f:
        for _, _, _, _, d in ordinati:
            f.write(d)
    chiavi = sum(1 for x in ordinati if x[1])
    print(f"   [vid]  {len(ordinati)} frames ({chiavi} keys), "
          f"{ordinati[0][2]}x{ordinati[0][3]}, written to {a.video_scrivi}")


def scrivi_appunti(a, cli):
    """The clipboard outcome, in JSON, for the bench's judge.

    ⛔ And ALL the facts are written, even those not needed for this round:
       «no announcement», «announcement without text» and «text different from the one
       copied» are three defects with the same symptom, and a file that carried
       only the verdict would make them indistinguishable (`LEZIONI.md` §1.9).

    ⛔ And the VIOLATIONS of §7.4 are written even when the round is green: a
       server that delivers the right text while violating the protocol along the
       way is a server the bench must fail — «it works» is not
       «it conforms».
    """
    if not a.appunti_scrivi:
        return
    esito = {
        "annunci_dal_server": cli.app_annunci,
        "chiesti_dal_server": cli.app_chiesti,
        "serviti_al_server": cli.app_serviti,
        "mio_id": cli.app_mio_id,
        "mio_testo": cli.app_mio_testo,
        # ⛔ `None` = nothing arrived, `""` = an empty string arrived.
        #    They are two different facts, and JSON keeps them apart.
        "ricevuto": cli.app_ricevuto,
        "violazioni": cli.app_violazioni,
    }
    with open(a.appunti_scrivi, "w") as f:
        json.dump(esito, f, ensure_ascii=False, indent=1)
    print(f"   [app]  outcome written to {a.appunti_scrivi} "
          f"({len(cli.app_violazioni)} violations of §7.4)")


def scrivi_audio(a, cli):
    """The audio blocks on disk, and the six counters on screen.

    ⛔ The counters are printed ALWAYS, even at zero: `CODER.md` §3.10 — «a
       denied reading is not a reading that says zero».  A round that
       prints nothing and one that received zero datagrams must look
       different.
    """
    if cli is None:
        return
    print(f"   [audio] received {cli.a_ricevuti} · {cli.a_byte} bytes of payload · "
          f"codec {cli.a_codec if cli.a_codec is not None else '(none)'}")
    # ⛔ `vecchi {n}` STAYS WHERE IT WAS AND AS IT WAS: `07-b64-rete.py`:538 reads it
    #    with the regex `vecchi (\d+)` on this line.  The four of phase 9
    #    are added AT THE END, where no regex of before meets them.
    print(f"   [audio] discarded — short {cli.a_corti} · type {cli.a_tipo} · "
          f"prefix {cli.a_prefisso} · old {cli.a_vecchi}")
    # ⛔ The phase 9 counters are printed ALWAYS and with BOTH
    #    rules, even all at zero: «a denied reading is not a reading that
    #    says zero» (`CODER.md` §3.10).  ⚠ With the old rule `tardivi`,
    #    `fuori` and `rec` are zero BY CONSTRUCTION — it is not health, it is that
    #    that rule cannot produce them.
    print(f"   [audio] reorder — {cli.a_vaglio.riga()}")
    print(f"   [audio] reorder — {cli.a_vaglio.riga_conti()}")
    if not a.audio_scrivi:
        return
    import base64
    with open(a.audio_scrivi, "w") as f:
        for b in cli.a_blocchi:
            f.write(json.dumps({"istante": b["istante"], "codec": b["codec"],
                                "byte": base64.b64encode(b["byte"]).decode()}) + "\n")
    print(f"   [audio] blocks written to {a.audio_scrivi} ({len(cli.a_blocchi)})")


def scrivi_traccia(a, reg, cli=None):
    """The recording is written early, and REWRITTEN at every stage.

    ⛔ «I have nothing to judge» and «conforming» are two different things: an empty
       file is not written, so whoever looks for it sees that it is not there instead of
       judging zero blocks.

    ⚠⛔ **And from 16 August 2026 it is REWRITTEN, where before it was written once
        only.**  The `scritta` guard was right as long as after `SESSIONE` this
    program recorded nothing more: now it records the `ADATTA_TELA`, the
    `TELA`, the `VISTA` and the closing of the channel — ⛔ and with the guard standing
    **the interesting half of the trace did not reach the file**.  A bench
    that closes the file before doing the thing it must measure hands
    the arbiter a conforming and empty recording.

    ⭐ And the FIN is marked HERE, not in the event that receives it: the server's
       messages go through a queue, and marking the end from the event handler
    would write the closing **before** messages that come after it in the
    trace.  ⛔ It would be a false byte precisely in the field that §11.1 added in order
    not to confuse an end with an interruption.
    """
    if not (a.registra and reg.blocchi):
        return
    if cli is not None and cli.finito and not getattr(reg, "fine_segnata", False):
        reg.segna_fine(SERVER, Registratore.FIN)
        reg.fine_segnata = True
    reg.scrivi(a.registra)
    reg.scritta = True
    print(f"   recording: {a.registra} ({len(reg.blocchi)} blocks)")


def corpo_ciao(audio="opus,pcm", video="h264", prof="8,10"):
    # ⛔ `audio` can be narrowed from the command line, and it is NOT a trick:
    #    it is what a client that cannot do Opus declares.  §4.3 requires
    #    `pcm` on both sides precisely for this — it is «the base always available»,
    #    and the positive control of Opus.  ⇒ `--audio-codec pcm` exercises the
    #    negotiation, it does not bypass it.
    # ⛔ And the VIDEO can be narrowed too, since 17 August 2026: it serves to
    #    exercise the fallback branch without a browser in between.  ⚠ It is not a
    #    trick — it is what a client that cannot decode HEVC
    #    declares, that is **exactly Firefox**.  §4.3 has the server choose
    #    within the intersection, and narrowing the intersection is a use
    #    of the protocol, not a workaround.
    #
    # ⛔⛔⛔ I CHANGED THE YARDSTICK — 23 August 2026, evening (`fasi/09` §14.1).
    #    The default was **`hevc,av1`** and it stayed so when AV1
    #    left the product (20 August, `DECISIONI.md` §1.13-ter): the server
    #    therefore chose **HEVC** in every bench round, while `pagina.html`
    #    (`PREFERENZA = ["hevc", "h264"]`, line 818) declares **only the codecs that
    #    have really PAINTED the probe** — and on Firefox HEVC does not paint.
    #    ⇒ The bench measured a codec the user never receives.
    #    `[M]` same scene, same canvas, same QP 26: **21.18 Mbit/s in HEVC
    #    against 7.92 in H.264**, a factor of **2.7** (`fasi/09` §13.5.1).
    #    ⇒ ⛔ **The bandwidth numbers taken before this line are NOT comparable
    #      with those taken after.**  The old yardstick is redone with
    #      `--video-codec hevc`, and it must be said every time it is used.
    voci = [("video.codec", video), ("video.profondita", prof),
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

    print(f"== RCP test client -> https://{autorita}{a.percorso}")
    async with connect(a.indirizzo, a.porta, configuration=conf,
                       create_protocol=Cliente) as cli:
        await asyncio.wait_for(cli.wait_connected(), timeout=8)
        cli.apri_sessione(autorita, a.percorso)
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        print(f"   extended CONNECT: :status = {stato}")
        if stato != "200":
            return 1
        # ⛔ The REAL stream of the control channel ends up in the trace: §11.1
        #    asks for it, and §2.5 rests P3 on it — «a frame on the
        #    control channel stream».  With the `0` written by hand that
        #    check of the arbiter looked at an invented number.
        reg.stream = cli.apri_controllo()
        # ⛔ And the recorder is handed to the CLIENT, because from here on the
        #    server's bytes are recorded where they arrive (box in
        #    `Cliente.__init__`).  ⚠ Before this line nothing can have
        #    arrived: the control channel did not exist.
        cli.reg = reg

        # ⛔ THE TRACE IS WRITTEN EVEN WHEN THE HANDSHAKE DOES NOT SUCCEED.
        #
        #    Finding R8.9: the third round of B3 exists to produce ONE object —
        #    the recording of whoever received the `CONGEDO(0x0F)` — and that
        #    recording was never written, because the exception went off
        #    earlier.  ⭐ The B4 validator is the arbiter of the refusal too.
        try:
            # ── CIAO ────────────────────────────────────────────────────────
            b = inquadra(T["CIAO"], corpo_ciao(a.audio_codec, a.video_codec, a.video_profondita))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            nome, corpo, grezzo = await attendi(cli, "ECCOMI", reg=reg)
            versione = struct.unpack("!H", corpo[:2])[0]
            print(f"   ECCOMI: version {versione}")

            # ── CREDENZIALI ─────────────────────────────────────────────────
            corpo_c = s(a.utente) + s(a.parola)
            b = inquadra(T["CREDENZIALI"], corpo_c)
            # §11.1: the password is obscured, the length stays true
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
            # ⭐ §4.4-bis: the fixed delay applies TO AMMESSO TOO.  It is
            #    timed here because no other bench sees it, and a
            #    regression that removed it would make nothing fail.
            print(f"   AMMESSO after {ms:.0f} ms"
                  + ("   ⭐ the fixed second is there" if ms >= 1000 else
                     "   ⛔ LESS THAN ONE SECOND: §4.4-bis violated"))
            if ms < 1000:
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 1

            # ── ATTACCA ─────────────────────────────────────────────────────
            b = inquadra(T["ATTACCA"],
                         struct.pack("!IIII", a.larghezza, a.altezza,
                                     a.larghezza, a.altezza) + s(a.disposizione))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            nome, corpo, grezzo = await attendi(cli, "SESSIONE", reg=reg)
        except Exception:
            scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
            raise
        stato_s = corpo[0]
        lar, alt = struct.unpack("!II", corpo[1:9])
        n = struct.unpack("!H", corpo[9:11])[0]
        desktop = corpo[11:11 + n].decode()
        print(f"   ⭐ SESSIONE: stato={stato_s} tela={lar}x{alt} desktop={desktop}")

        # ═══════════════════════════════════════════════════════════════════
        # ⭐⛔ THE CANVAS PATH — sub-phase 6.6, 16 August 2026
        #
        #    ⛔ *«Neither of the two sends an `ADATTA_TELA`»*: from here on it is no
        #       longer true.  And there is one more reason to do it **at attach**,
        #       and it dates from 15 August: `DECISIONI.md` §5.0-sexies has the
        #       client ask for *«the canvas of its own window at the attach of every
        #       session, by itself»* — so this is not a laboratory
        #       test, it is what the real client does every time.
        #
        # ⚠ And the in-flight count is kept HERE TOO, not only in the arbiter: §6.2
        #   ties to the count the way the client treats frames, and a
        #   test client that did not keep it could not notice a
        #   `TELA` it did not ask for.
        tela_viva = (lar, alt)
        # ⭐ The canvas in force **BEFORE** the last `TELA(ADATTATA)`: it is the one
        #    on which the in-flight coordinates of §7.1 are still valid, and it is
        #    the only number from which the grace-second case can be built
        #    without making it up.  ⛔ `None` as long as no adaptation has
        #    succeeded: then the scene does not exist, and we say so instead of faking it.
        tela_prec_adattata = None
        esiti_tela = []
        if a.adatta:
            for al, aa, quando in a.adatta:
                if quando:
                    # ⭐ It is the **live** resize: the session is already
                    #    alive and frames pass in between.  ⚠ We wait with
                    #    our eyes open — a `sleep` would not notice that
                    #    the session dropped in the meantime, and the measurement
                    #    of the `ADATTA_TELA` would be taken on a dead connection
                    #    (findings R8.2, R8.4).
                    print(f"   ·  waiting {quando} s with the session alive")
                    try:
                        await asyncio.wait_for(cli.caduto.wait(), timeout=quando)
                        print(f"   ⛔ dropped before the canvas could be asked for: "
                              f"{cli.caduta}")
                        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                        return 4
                    except asyncio.TimeoutError:
                        pass
                prima_di_questo = tela_viva
                r = await chiedi_tela(cli, reg, al, aa, a.attesa_tela)
                esiti_tela.append(r)
                if r is not None and r[0] == 1:
                    tela_prec_adattata = prima_di_questo
                if r is None:
                    # ⛔ The silence is RECORDED and we exit with a code of its own: it is
                    #    the scene of §7.1, and it must be told apart from «the session
                    #    dropped» (4) and from «all fine» (0).
                    scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                    return 5
                tela_viva = (r[2], r[3])
        # ═══════════════════════════════════════════════════════════════════
        # ⭐⛔ THE GRACE SECOND OF §7.1, AIMED AT THE SERVER
        #     — 22 August 2026, and until this morning it had never been done.
        #
        # §7.1: *«After sending `TELA(ADATTATA)` the server MUST accept
        # for **one second** valid input coordinates on the
        # **previous** canvas, saturating them to the new one and writing it in the log;
        # once that second has passed, they are `ERRORE_PROTOCOLLO`»*.
        #
        # ⛔⛔ THE TRAP, AND IT MUST BE DEFUSED BEFORE CHOOSING THE DELAY.
        #
        #     The rule belongs to the **SERVER**; the recording is taken by the
        #     **CLIENT**.  The interval seen here is SHORTER than the true one
        #     by half a network round trip per side (§11.1, *«the recorded time is
        #     WHOEVER RECORDS'»*).  ⇒ A case «inside the second» set at 0.95 s
        #     could be 1.02 s for the server, and the bench would accuse the
        #     product of a defect it does not have — or, worse, would acquit itself
        #     on its own.
        #
        # ⭐ The cure is not a calculation: it is **staying away from the boundary**, and
        #    declaring why.  Whoever calls this client chooses the delay;
        #    here the margin is printed, so a badly chosen delay shows
        #    instead of producing a verdict.
        #
        # ⛔ AND THE COORDINATE IS NOT MADE UP: it is **the last pixel of the
        #    previous canvas**, `(prec_l - 1, prec_a - 1)`.  Two reasons, and the
        #    second is worth more than the first:
        #      · it is valid on the previous canvas **by definition** (§7.3: «0 <=
        #        x < tela_larghezza»), so the case is that of §7.1 and not
        #        «a wrong coordinate» — which §7.1 does NOT cover, and the server
        #        has a line on purpose to say so;
        #      · saturated, it must land **exactly** on `(nuova_l - 1,
        #        nuova_a - 1)`, that is on a KNOWN point.  ⭐ It is the check that
        #        crosses the conversion: a server that refused the
        #        coordinate *saying so in the log* but applied it anyway
        #        would pass the arbiter, and would not pass this.
        if a.puntatore_vecchia is not None:
            if tela_prec_adattata is None:
                print("   ⛔ --puntatore-vecchia, but no TELA(ADATTATA) "
                      "succeeded: there is no «previous canvas», and a "
                      "coordinate chosen at random would test ANOTHER rule "
                      "(§7.3 «outside the canvas»), not the grace second")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 6
            px = tela_prec_adattata[0] - 1
            py = tela_prec_adattata[1] - 1
            if px < tela_viva[0] and py < tela_viva[1]:
                print(f"   ⛔ ({px},{py}) is INSIDE the canvas in force "
                      f"{tela_viva[0]}x{tela_viva[1]}: the scene of §7.1 is not "
                      f"exercised at all — what is needed is a new canvas smaller "
                      f"than the previous {tela_prec_adattata[0]}x"
                      f"{tela_prec_adattata[1]}")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 6
            # The expected saturation, computed as §7.1 describes it: «to the last
            # valid pixel».
            sx = px if px < tela_viva[0] else tela_viva[0] - 1
            sy = py if py < tela_viva[1] else tela_viva[1] - 1
            rit_ms = int(round(a.puntatore_vecchia * 1000))
            print(f"   ⛔ EXPECTED, declared BEFOREHAND: PUNTATORE ({px},{py}) — "
                  f"valid on the previous canvas {tela_prec_adattata[0]}x"
                  f"{tela_prec_adattata[1]}, outside the one in force "
                  f"{tela_viva[0]}x{tela_viva[1]} — at {rit_ms} ms from the "
                  f"TELA(ADATTATA)")
            if rit_ms > 1000:
                print(f"      ⇒ beyond the grace second, and the margin is "
                      f"{rit_ms - 1000} ms.  ⛔ The server MUST refuse: "
                      f"ITS interval is even longer than this")
            else:
                print(f"      ⇒ inside the second, and the margin is "
                      f"{1000 - rit_ms} ms — that is how much network round trip it "
                      f"would take to push it beyond.  ⛔ The server MUST "
                      f"saturate to ({sx},{sy}) and write it in the log")
            if cli.ultimo_tela_ms is None:
                print("   ⛔ no instant recorded for the TELA: I do not know from "
                      "when to count")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 6
            bersaglio = cli.ultimo_tela_ms + rit_ms
            # ⛔ WE WAIT WITH OUR EYES OPEN — findings R8.2/R8.4.  A
            #    `sleep` would not notice that the session died in the
            #    meantime, and the `PUNTATORE` would leave on an already
            #    closed connection: the bench would measure itself.
            caduto_prima = False
            while True:
                resta = (bersaglio - reg.istante()) / 1000.0
                if resta <= 0:
                    break
                try:
                    await asyncio.wait_for(cli.caduto.wait(), timeout=resta)
                    caduto_prima = True
                    break
                except asyncio.TimeoutError:
                    pass
            if caduto_prima:
                print(f"   ⛔ the session dropped BEFORE the PUNTATORE: "
                      f"{cli.caduta} — the second rule was not "
                      f"exercised")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 4
            pid, pms = cli.manda_puntatore(px, py)
            dt = None if pms is None else pms - cli.ultimo_tela_ms
            print(f"   → PUNTATORE id={pid} ({px},{py}) — recorded dt "
                  f"{dt} ms from the TELA(ADATTATA).  ⚠ It is the number the arbiter "
                  f"will read: the SERVER's interval is longer than this")

            # ═══════════════════════════════════════════════════════════════
            # ⭐⛔ THE THIRD WITNESS: A FRAME IS ASKED FOR, BECAUSE A
            #     STILL DESKTOP DOES NOT SEND ANY.
            #
            # `[M]` 22 August 2026, first real round on 7721: after the
            # `PUNTATORE` the trace carries **zero** frames — the
            # monitorless GNOME session has nothing that moves, and the server
            # ships only what changes.  ⇒ The `input` field of §6.2 —
            # *«the identifier of the last INJECTED input»*, the only
            # witness of the injection that lives **on the wire** — could not say
            # anything, and «it did not inject» and «no
            # frame passed» looked the same (`LEZIONI.md` §1.9).
            #
            # ⛔ And it is asked for AFTER the pointer, with a delay: the input
            #    channel and the control one are **two independent streams**
            #    (§2.5) and nothing orders their delivery.  Without waiting, the key
            #    could be captured BEFORE the input is injected, and
            #    an `input = 0` would mean «I do not know», not «not injected».
            #
            # ⚠ And if the session has already dropped nothing is sent: in the round
            #   «beyond the second» that is the RIGHT path, and insisting on
            #   a dead connection would produce a bench error instead
            #   of a measurement.
            if a.chiave_dopo:
                try:
                    await asyncio.wait_for(cli.caduto.wait(),
                                           timeout=a.chiave_dopo)
                    print(f"   ·  no RICHIEDI_CHIAVE: the session has already "
                          f"dropped ({cli.caduta}) — ⭐ after a PUNTATORE beyond "
                          f"the second it is what §7.1 wants")
                except asyncio.TimeoutError:
                    ultimo = max((f[0] for f in cli.v_fotogrammi), default=0)
                    b = inquadra(T["RICHIEDI_CHIAVE"],
                                 struct.pack("!I", ultimo))
                    cli.manda(b)
                    reg.aggiungi(CLIENT, b)
                    print(f"   → RICHIEDI_CHIAVE({ultimo}) — ⚠ it is not the scene "
                          f"of §5.2: it serves to let ONE frame through, so that "
                          f"the `input` field of §6.2 can bear witness")

        if a.vista:
            # ⚠ `VISTA` MUST NOT change the canvas (§7.1).  If after this one
            #   a `TELA` arrives, the wire says so and the arbiter accuses it: here we do not
            #   judge, we record.
            vl, va = a.vista
            b = inquadra(T["VISTA"], struct.pack("!II", vl, va))
            cli.manda(b)
            reg.aggiungi(CLIENT, b)
            print(f"   → VISTA {vl}x{va}   ⚠ must not change the canvas")

        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)

        # ⛔ THE «ATTACHED» SIGNAL, AND WHY A PRINTED LINE IS NOT ENOUGH.
        #
        #    On 10 August 2026 the third round of B3 waited for the word
        #    «SESSIONE» in the log of this program — and Python **buffers
        #    stdout when it is redirected to a file**: that line appeared
        #    only at process exit, that is **at the exact instant the
        #    client detached**.
        #
        # ⚠ The bench said «the first is attached» by reading a truth that had just
        #   expired, and the second connection always arrived to a free slot.
        #   ⛔ A check that looks right and measures the wrong instant: the
        #      red ended up on the server, which had nothing to do with it.
        #
        # ⭐ A file written and closed is a fact; a printed line is a
        #    hope about the moment someone will see it.
        if a.segnale:
            with open(a.segnale, "w") as f:
                f.write("attaccato\n")

        # ═══ THE CLIPBOARD — §7.4 ═════════════════════════════════════════
        #
        # ⛔ And is the `device → session` direction announced BEFORE writing
        #    the signal?  NO, and the reason is the order of the two sides of the bench:
        #    the signal says «I am attached», and the side that copies with `xclip`
        #    waits precisely for that.  Announcing before would mean announcing
        #    when the other side is not yet ready to look.
        if a.clic:
            # ⛔ We wait: the window must already be on the screen, or the click
            #    lands on the background and nobody takes the focus.
            px, _, py = a.clic.partition(",")
            print(f"   [clic] waiting {a.clic_dopo} s, then clicking at ({px},{py})")
            await asyncio.sleep(a.clic_dopo)
            cli.manda_puntatore(int(px), int(py))
            await asyncio.sleep(0.2)
            cli.manda_pulsante(True)
            await asyncio.sleep(0.12)
            cli.manda_pulsante(False)
            print("   [clic] ⭐ done: that window now has the focus")

            if a.clic_ogni > 0:
                async def ancora():
                    while True:
                        await asyncio.sleep(a.clic_ogni)
                        cli.manda_puntatore(int(px), int(py))
                        await asyncio.sleep(0.15)
                        cli.manda_pulsante(True)
                        await asyncio.sleep(0.1)
                        cli.manda_pulsante(False)

                asyncio.ensure_future(ancora())
                print(f"   [clic] and I redo it every {a.clic_ogni} s")

        if a.appunti_copia:
            cli.appunti_annuncia(a.appunti_copia)

        if a.appunti_attendi:
            # ⛔ WE WAIT FOR AN ANNOUNCEMENT, AND THEN ASK FOR IT — §7.4: «one announces
            #    and one asks, instead of pushing».  ⚠ And the two steps are counted
            #    separately: «no announcement arrived» and «the announcement
            #    arrived and the text did not» are two different defects with the same
            #    symptom (`LEZIONI.md` §1.9).
            print(f"   [app]  waiting for an announcement from the server, up to "
                  f"{a.appunti_attendi} s")
            fine = time.monotonic() + a.appunti_attendi
            while not cli.app_annunci and time.monotonic() < fine:
                cli.app_evento.clear()
                try:
                    await asyncio.wait_for(cli.app_evento.wait(),
                                           timeout=max(0.1, fine - time.monotonic()))
                except asyncio.TimeoutError:
                    break
            if not cli.app_annunci:
                print("   [app]  ⛔ no announcement from the server in time")
            else:
                cli.appunti_chiedi()
                fine = time.monotonic() + a.appunti_attendi
                while cli.app_ricevuto is None and time.monotonic() < fine:
                    cli.app_evento.clear()
                    try:
                        await asyncio.wait_for(cli.app_evento.wait(),
                                               timeout=max(0.1, fine - time.monotonic()))
                    except asyncio.TimeoutError:
                        break
                if cli.app_ricevuto is None:
                    print("   [app]  ⛔ the announcement arrived and the text did NOT")
                else:
                    print(f"   [app]  ⭐ received {len(cli.app_ricevuto)} "
                          f"characters: «{cli.app_ricevuto[:60]}»")
        scrivi_appunti(a, cli)
        if a.resta:
            # ⛔ WE STAY WITH OUR EYES OPEN, NOT SLEEPING — findings R8.2/R8.4.
            #
            #    An `asyncio.sleep` notices nothing: the connection
            #    could drop from QUIC's idle cap, or the session
            #    could be closed by the server to make room for another, and
            #    this program exited 0 saying «I stayed attached».
            #    On that exit code the third round concluded «no live client
            #    is ousted», which is invariant I2 to the letter.
            #
            # ⚠ Nothing is sent to make sure: the fourth round measures
            #   the SILENCE clock, and one byte would reset it.  We just listen
            #   — which is precisely the receiving side.
            print(f"   staying attached for {a.resta} s"
                  + (f", making myself heard every {a.vivo} s" if a.vivo else ""))
            try:
                if a.vivo:
                    # ⛔⛔ AND THIS OPTION IS A TRAP — 16 August 2026.
                    #
                    #    `VISTA` (0x0008) is in the protocol, ⛔ but THIS server
                    #    does not serve it yet: it answers `ERRORE_PROTOCOLLO` and
                    #    CLOSES.  `[M]` Over twenty measurement rounds, three sessions
                    #    died at 8 seconds because of this line, and the
                    #    times came out as «10.4 s» — a number of the bench, not
                    #    of the product.
                    #
                    # ⭐ The lesson, which the user put better: *«for tests
                    #    use the browser, not the bench — it is the only way to
                    #    measure what really happens»*.  A test client
                    #    that sends what the real client does not send does not
                    #    measure the product: it measures itself.
                    raise SystemExit(
                        "⛔ --vivo sends VISTA (0x0008), which this server does not "
                        "serve: it would close the session with ERRORE_PROTOCOLLO. "
                        "To measure times, use the BROWSER.")
                    # ⭐ `--vivo`: an IDENTICAL `VISTA` is sent every so often, only
                    #    so as not to be detached by the silence clock (§5.3).
                    #
                    # ⛔ OFF BY DEFAULT, and that is the point: the default
                    #    behaviour — keeping quiet — serves to MEASURE that clock, and
                    #    the comment above has said so since 10 August.  ⚠ Whoever
                    #    turns it on is measuring something else: the scene in which the
                    #    client is there and working, which is that of the real browser.
                    #
                    # ⚠ And `VISTA` with the same numbers is a semantic no-op: it
                    #   changes nothing, it is legitimate with an active session (§7.1), and it
                    #   asks nothing of the stage — unlike `RICHIEDI_CHIAVE`,
                    #   which would make it redo a key and would distort the measurement.
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
                # ⛔ The flag is raised BEFORE leaving: leaving here
                #    `connect()` closes the connection, and the event that follows
                #    must already be recognisable as ours.
                cli.chiusa_da_noi = True
                print(f"   ⭐ still attached after {a.resta} s: nothing dropped")
                scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
                return 0
            print(f"   ⛔ I did NOT stay attached: {cli.caduta}")
            scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
            return 4
        scrivi_traccia(a, reg, cli); scrivi_audio(a, cli); scrivi_video(a, cli)
        return 0


# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD MUST NOT PASS THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 August 2026.
#
# ⛔ `--parola` ends up in the process `argv`, that is in `/proc/<pid>/cmdline`,
#    which on Linux is **readable by anyone**: a `ps` run by another
#    user during the round prints it in full.
#
# ⭐ The good path already existed in house and this is its extension, not a
#    second way: `01-b10-secondo-utente.py` takes `--parola-file`, a `0600`
#    file that the launcher writes with `printf` — a shell **builtin**,
#    so not even the writing goes through a process with the password in `argv` —
#    and deletes with a `trap`.
#
# ⚠ And `--parola` has NOT been removed, and not out of laziness: some callers not
#   yet cured still pass it, and breaking them **silently** would be worse
#   than the defect.  ⛔ But the fallback is DECLARED (`CODER.md` §4.2): a silent
#   fallback produces two behaviours under the same label, which is the
#   form **E2** — and here the two behaviours are «the secret is protected» and
#   «the secret is public».  ⇒ whoever passes `--parola` gets told.
#
# ⚠ And the warning looks at `sys.argv`, not at the value: the default written in the
#   code is in no command line, and telling it the opposite would be an
#   alarm one learns to ignore.
# ══════════════════════════════════════════════════════════════════════════
# ⭐⭐ `--certifica` — THE SELF-TEST OF THE SCREENING, WITH NO NETWORK AND NO MACHINE
#
# ⛔⛔ R13 — EVERY EXPECTATION IS A PREDICATE WRITTEN BEFOREHAND.  Not a sentence printed
#      next to the numbers (that stays true «when read» whatever comes out),
#      but a function `(numbers) -> (passes, why)`.  `passa=None` is the third
#      outcome: **the bench refuses to judge**, and it is not a green.
#
# ⛔ And the clock is FAKE, for two reasons that both hold:
#    · the screening depends on time (the cushion is 250 ms), and with the
#      real clock this test would last minutes and be different every time;
#    · a bench that sleeps also measures the load of the machine hosting it.
PCM_BYTE = 960                  # `[S]` RCP.md:1299 — 480 samples, 5 ms
PCM_PASSO_US = 5000


class OrologioFinto:
    """Time is moved by the bench, not by the system."""

    def __init__(self, t=1000.0):
        self.t = t

    def __call__(self):
        return self.t


def _p(cond, perche):
    return (bool(cond), perche)


def _giro(regola, arrivi, ritardo_decodifica_s=0.0):
    """`arrivi` = [(seconds from the start, istante_us)].  Returns `(vaglio, usciti)`.

    ⛔ `usciti` is the LIST of the delivered `istante`s, not the count: it serves to
       verify that neither of the two rules **fabricates** a block that was not on
       the wire, and that a duplicate does not come out twice.
    """
    orol = OrologioFinto()
    t0 = orol.t
    v = VaglioAudio(regola=regola, orologio=orol,
                    ritardo_decodifica_s=ritardo_decodifica_s)
    usciti = []
    for quando, ist in arrivi:
        orol.t = t0 + quando
        ok, _perche = v.arrivo(ist, 2, PCM_BYTE)
        if ok:
            usciti.append(ist)
    return v, usciti


def _conti(v):
    return {"sul_filo": v.sul_filo, "ricevuti": v.ricevuti,
            "consegnati": v.consegnati, "vecchi": v.scartati_vecchi,
            "tardivi": v.scartati_tardivi, "fuori": v.fuori_ordine,
            "doppioni": v.doppioni, "recuperati": v.recuperati,
            "mancati": v.mancati, "volte": v.mancati_volte,
            "riarmi": v.riarmi,
            "purezza": None if v.purezza is None else round(v.purezza, 4)}


def _ordinata(n):
    """n PCM blocks of 5 ms, in order, with no losses: the denominator."""
    return [(i * 0.005, i * PCM_PASSO_US) for i in range(n)]


def _riordinata(n, k):
    """Reorder by `k` places: groups of `k+1` reversed.

    ⭐ It is the reorder on which the OLD rule has a COMPUTABLE purity, not
       one measured afterwards: within each reversed group only the first
       to arrive is the newest, the other `k` are behind and the old
       rule throws them all away ⇒ **expected purity = 1/(k+1) exactly**.
    ⛔ This is the expectation written beforehand, and it is stronger than a magic number:
       if the count does not add up, either the reorder is not what I believe or the old
       rule is not what I believe.
    """
    fuori = []
    for i in range(0, n, k + 1):
        fuori += list(range(i, min(i + k + 1, n)))[::-1]
    return [(p * 0.005, j * PCM_PASSO_US) for p, j in enumerate(fuori)]


def _con_doppioni(n, ogni):
    """In order, but every `ogni`-th block arrives TWICE.

    ⚠ The twin arrives 1 ms later and **does not consume a slot**: if it did,
      the real blocks would slip by 5 ms each and after 50 duplicates the
      accumulated delay would exceed the cushion ⇒ a rearm of the anchor, and the case would
      no longer measure the duplicates but the drift the bench itself fabricated.
    """
    a = []
    for i in range(n):
        a.append((i * 0.005, i * PCM_PASSO_US))
        if i and i % ogni == 0:
            a.append((i * 0.005 + 0.001, i * PCM_PASSO_US))
    return a


def _con_buchi(n, ogni):
    """REAL holes: the blocks do not arrive at all, and those present stay in their place.

    ⛔ Block 0 is ALWAYS there, and it is a choice of the bench: a hole **at the head**
       cannot be counted — there is no `ultimo_istante` from which to measure the
       jump — and mixing it with the holes in the middle would give an expectation off by 1.
       ⭐ The blind spot has a case of its own (4-blind).
    """
    return [(i * 0.005, i * PCM_PASSO_US)
            for i in range(n) if i == 0 or i % ogni]


def _vecchio_letterale(istanti):
    """⛔ THE CODE OF BEFORE, TRANSCRIBED TO THE LETTER from `_audio_datagram`
       as it was until 22 August 2026.  It serves one thing only: proving that
       `--audio-regola vecchia` has changed NOTHING.  Not to be touched."""
    ric = vecchi = 0
    ult = None
    usciti = []
    for ist in istanti:
        if ult is not None and ist <= ult:
            vecchi += 1
            continue
        ult = ist
        ric += 1
        usciti.append(ist)
    return ric, vecchi, usciti


def certifica():
    esiti = []

    def caso(nome, passa, perche, numeri=None):
        esiti.append({"caso": nome, "passa": passa, "perche": perche,
                      "numeri": numeri})
        segno = "OK " if passa else ("-- " if passa is None else "⛔ NO")
        print(f"  {segno} {nome}")
        print(f"      expected: {perche}")
        if numeri:
            print(f"      seen:     {numeri}")

    print("== ⭐ `01-b3-cliente.py --certifica` — the audio screening, "
          "with no network and no test machine")
    print(f"   PCM of {PCM_BYTE} bytes = {PCM_PASSO_US} us (RCP.md:1299), "
          f"cushion {AUDIO_CUSCINO_MS} ms, fake clock")

    # ── 1 · in order: the two rules must be INDISTINGUISHABLE ──────────────
    print("\n  ── 1 · sequence in order ──")
    av, uv = _giro("vecchia", _ordinata(840))
    an, un = _giro("nuova", _ordinata(840))
    caso("1 · in order ⇒ the two rules give the SAME result",
         _conti(av) == _conti(an) and uv == un and av.purezza == 1.0,
         "every counter equal, same list of outputs, purity 1.0000 "
         "(⛔ if they differ, the new rule has a defect on the easy case)",
         {"vecchia": _conti(av), "nuova": _conti(an)})

    # ── 2 · reorder by 1, 2, 3 (and 7) places ──────────────────────────────
    print("\n  ── 2 · reordered sequence ──")
    for k in (1, 2, 3, 7):
        av, uv = _giro("vecchia", _riordinata(840, k))
        an, un = _giro("nuova", _riordinata(840, k))
        atteso_v = 1.0 / (k + 1)
        arretrati = 840 - 840 // (k + 1)
        passa = (abs(av.purezza - atteso_v) <= 0.005
                 and an.purezza >= 0.95
                 and an.fuori_ordine == arretrati
                 and an.scartati_vecchi == 0 and an.doppioni == 0
                 and sorted(un) == [i * PCM_PASSO_US for i in range(840)])
        caso(f"2.{k} · reorder by {k} places ⇒ the old one throws away, the new one keeps",
             passa,
             f"old purity = 1/(k+1) = {atteso_v:.4f} (±0.005) · "
             f"new purity ≥ 0.95 · fuori_ordine = {arretrati} · "
             f"vecchi 0 · and the output contains ALL 840 `istante`s",
             {"purezza_vecchia": round(av.purezza, 4),
              "purezza_nuova": round(an.purezza, 4),
              "vecchia": _conti(av), "nuova": _conti(an)})

    # ── 3 · duplicates: counted, and never played twice ────────────────────
    print("\n  ── 3 · duplicates ──")
    arrivi = _con_doppioni(840, 10)
    attesi_dop = len(arrivi) - 840
    for regola in ("vecchia", "nuova"):
        v, u = _giro(regola, arrivi)
        passa = (v.doppioni == attesi_dop and len(u) == len(set(u))
                 and len(u) == 840)
        caso(f"3.{regola} · {attesi_dop} duplicates ⇒ counted, and never twice "
             "at the output",
             passa,
             f"doppioni = {attesi_dop} · no repeated `istante` at the output · "
             f"840 delivered (⛔ a duplicate played twice doubles the "
             "signal, which §6.3 does not allow)",
             _conti(v))

    # ── 4 · real holes: neither of the two must FABRICATE audio ────────────
    print("\n  ── 4 · real holes ──")
    arrivi = _con_buchi(840, 7)
    spediti = [ist for _q, ist in arrivi]
    attesi_mancati = 840 - len(spediti)
    for regola in ("vecchia", "nuova"):
        v, u = _giro(regola, arrivi)
        passa = (v.mancati == attesi_mancati and u == spediti
                 and v.consegnati == len(spediti)
                 and v.recuperati == 0)
        caso(f"4.{regola} · {attesi_mancati} blocks NEVER arrived ⇒ `mancati` "
             "rises and nothing is fabricated",
             passa,
             f"mancati = {attesi_mancati} · consegnati = {len(spediti)} · "
             "at the output ONLY the `istante`s that were on the wire · recuperati 0",
             _conti(v))
    # ⛔⭐ THE BLIND SPOT, AND IT IS DECLARED INSTEAD OF HIDDEN — found by
    #     this bench on 23 August 2026, and it was a red that was right.
    #     The datagrams lost BEFORE the first one that arrives cannot be counted:
    #     `mancati` measures the distance between two `istante`s, and without the first there
    #     is no distance.  ⚠ It is a limit of the PAGE, not of the
    #     translation (`src/pagina.html`:6550, `a.ultimo_istante !== undefined`).
    #     ⇒ A bench that asked «mancati == all the holes» on a sequence
    #     that starts with a hole would give red to the product for a defect of its own.
    ceco = [(i * 0.005, i * PCM_PASSO_US) for i in range(3, 200)]
    v, u = _giro("nuova", ceco)
    caso("4-blind · ⚠ the 3 holes AT THE HEAD are not counted, and it is not a defect",
         v.mancati == 0 and v.consegnati == len(ceco),
         "mancati 0 (⛔ there is no earlier `istante` from which to measure the "
         "jump: it is a declared limit, not a fault) · all delivered",
         _conti(v))

    # ── 5 · and the block that arrived REALLY too late ─────────────────────
    #
    # ⛔⛔ THIS IS THE CASE THAT PROVES THE CURE IS NOT «I KEEP EVERYTHING».
    #     If the new rule kept this one too, it would not be a cure: it would be
    #     the removal of a check.
    #
    # ⚠ And the cases are TWO, because in the page the counters are two and fall
    #   at different points of the path:
    #     5a · the place passed ALREADY ON THE WIRE ⇒ `scartati_vecchi`
    #          (`src/pagina.html`:5999-6001 is in `suona()`; the twin on the wire
    #          is :6514, and there the counter is `scartati_vecchi`);
    #     5b · the place passed WHILE WE WERE DECODING IT ⇒ `scartati_tardivi`.
    #   ⛔ Calling them both «late» would be convenient and wrong: the first
    #     is §6.3 to the letter, the second is the safety net after the
    #     decoder, and if one day they were confused nobody would know any more
    #     whether what throws away is the wire or the machine.
    # ⭐ AND THE MARGIN CALCULATION, written here because without it the case goes wrong.
    #    The anchor hooks INSIDE `_consegna`, that is **after** decoding:
    #    `base = ora + ritardo + cuscino - t`.  ⇒ A block that arrives `Δ`
    #    late on its own place is discarded
    #      · ON THE WIRE   if  Δ > cushion + delay   (the screening looks at `ora`);
    #      · AT DELIVERY   if  Δ > cushion           (the screening looks at `ora + ritardo`).
    #    ⇒ The window of `scartati_tardivi` is exactly
    #      `cushion < Δ ≤ cushion + delay`, and with no decoding delay it is
    #      EMPTY — which is T3 said in numbers.
    print("\n  ── 5 · the block really too late ──")
    n, i_tardo = 200, 195
    base = _ordinata(n)
    suo_posto = i_tardo * 0.005          # when it should have arrived
    ultimo_arrivo = base[-1][0]
    cusc = AUDIO_CUSCINO_MS / 1000.0
    # 5a · Δ = 300 ms > cushion 250 and delay 0 ⇒ it passed ALREADY ON THE WIRE.
    tardo = [(suo_posto + 0.300, i_tardo * PCM_PASSO_US)]
    assert tardo[0][0] > ultimo_arrivo    # it must be the last to arrive
    av, uv = _giro("vecchia", base + tardo)
    an, un = _giro("nuova", base + tardo)
    caso(f"5a · Δ = 300 ms > cushion {AUDIO_CUSCINO_MS} ⇒ the place passed "
         "ON THE WIRE, and the new one DISCARDS it",
         (an.scartati_vecchi == 1 and an.fuori_ordine == 0
          and an.consegnati == n and un == [i * PCM_PASSO_US for i in range(n)]
          and av.scartati_vecchi == 1 and av.consegnati == n),
         "new: vecchi 1 · fuori 0 · consegnati 200, and the late one is NOT "
         "in the output — old: vecchi 1 · consegnati 200",
         {"vecchia": _conti(av), "nuova": _conti(an)})
    # 5b · Δ = 280 ms: it lies in the window `250 < Δ ≤ 250+50` ⇒ it passes the wire and
    #      loses its place during the 50 ms of declared decoding.
    dec = 0.050
    delta = cusc + dec / 2                # 275 ms: in the middle of the window
    quasi = [(suo_posto + delta, i_tardo * PCM_PASSO_US)]
    assert quasi[0][0] > ultimo_arrivo
    an2, un2 = _giro("nuova", base + quasi, ritardo_decodifica_s=dec)
    av2, uv2 = _giro("vecchia", base + quasi, ritardo_decodifica_s=dec)
    caso(f"5b · Δ = {delta * 1000:.0f} ms, that is inside the window "
         f"({AUDIO_CUSCINO_MS} < Δ ≤ {AUDIO_CUSCINO_MS + dec * 1000:.0f}) ⇒ "
         "`scartati_tardivi`",
         (an2.scartati_tardivi == 1 and an2.fuori_ordine == 1
          and an2.consegnati == n and an2.riarmi == 0
          and av2.consegnati == n and av2.scartati_vecchi == 1),
         "new: tardivi 1 · fuori 1 (the wire let it through) · "
         "consegnati 200 · riarmi 0 (⛔ the anchor is NOT touched for an "
         "overtaken one: a rearm would cost 250 ms of delay for a 5 ms "
         "block) — old: vecchi 1 · consegnati 200",
         {"vecchia": _conti(av2), "nuova": _conti(an2)})
    # 5c · and the counter-check: the cure is NOT «I keep everything».
    an3, un3 = _giro("nuova", _riordinata(840, 3))
    caso("5c · ⭐ the counter-check: on the reorder the new one keeps 840/840, on the "
         "late one it throws away 1 ⇒ it is not «I keep everything»",
         an3.consegnati == 840 and an.consegnati == n and an.scartati_vecchi == 1,
         "the same rule, two opposite outcomes on the two cases (⛔ if it threw away zero "
         "in both it would be the removal of a check)",
         {"riordino": an3.consegnati, "tardivo_scartati": an.scartati_vecchi})

    # ── 6 · the regression: the default has NOT changed ────────────────────
    print("\n  ── 6 · the old rule against the code of before ──")
    banchi_prova = {
        "in order": _ordinata(840),
        "reordered by 3": _riordinata(840, 3),
        "with duplicates": _con_doppioni(840, 10),
        "with holes": _con_buchi(840, 7),
        "mixed": _riordinata(400, 2) + _con_doppioni(200, 5) + _con_buchi(200, 9),
    }
    guasti = []
    for nome, arrivi in banchi_prova.items():
        v, u = _giro("vecchia", arrivi)
        ric, vecchi, usciti = _vecchio_letterale([i for _q, i in arrivi])
        if (v.ricevuti, v.scartati_vecchi, u) != (ric, vecchi, usciti):
            guasti.append(f"{nome}: new ({v.ricevuti}, {v.scartati_vecchi}, "
                          f"{len(u)} out) against old ({ric}, {vecchi}, "
                          f"{len(usciti)} out)")
    caso("6 · ⛔⛔ `--audio-regola vecchia` == the code of 22 August, to the "
         "letter, on 5 sequences",
         not guasti,
         "ricevuti, vecchi and the LIST of outputs identical in all five "
         "(⛔ if not, every number already measured by the benches stops being "
         "comparable)",
         {"guasti": guasti or "none",
          "predefinito": REGOLA_AUDIO,
          "predefinito_del_vaglio": VaglioAudio().regola})
    caso("6-bis · the DEFAULT is still `vecchia` in both places",
         REGOLA_AUDIO == "vecchia" and VaglioAudio().regola == "vecchia",
         "the module variable and the constructor both say «vecchia»",
         {"modulo": REGOLA_AUDIO, "costruttore": VaglioAudio().regola})

    rossi = [e for e in esiti if e["passa"] is False]
    muti = [e for e in esiti if e["passa"] is None]
    print(f"\n== {len(esiti)} cases · {len(rossi)} red · {len(muti)} «not "
          f"judged»")
    for e in rossi:
        print(f"   ⛔ {e['caso']}")
        print(f"      expected {e['perche']}")
        print(f"      seen     {e['numeri']}")
    if not rossi:
        print("== ⭐ THE SCREENING DOES WHAT THE PAGE DOES, AND THE DEFAULT HAS NOT "
              "CHANGED")
    return 1 if rossi else 0


def parola_dagli_argomenti(a):
    """The password: from `--parola-file` if present, from `--parola` otherwise.

    ⛔ And the three ways of failing are told apart: «cannot be read», «is readable by
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
        print("     COMMAND LINE: it sits in `/proc/<pid>/cmdline` and anyone who")
        print("     runs `ps` on this machine sees it.  The round goes on — the caller")
        print("     has not been cured — but it is not a private round.")
        print("     ⭐ The cure: `--parola-file <0600 file>`, as in B10.")
    return a.parola


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="the RCP handshake, from the client side")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7447)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="prova")
    # ⛔ D12: the path that does NOT go through `ps`.  It wins over `--parola` if both
    #    are there — a file written on purpose is always more recent than a
    #    default.
    p.add_argument("--parola-file", default="",
                   help="0600 file holding only the password (⭐ D12: this way "
                        "it does not end up in `ps`)")
    p.add_argument("--larghezza", type=int, default=1920)
    p.add_argument("--altezza", type=int, default=1080)
    p.add_argument("--disposizione", default="it")
    p.add_argument("--registra")
    # ⭐ THE CANVAS PATH — sub-phase 6.6.
    #
    # ⛔ `--adatta LxH` or `LxH@S`: sends `ADATTA_TELA` and waits for the `TELA`
    #    that §7.1 requires.  Repeatable, and with `@S` it waits S seconds BEFORE
    #    sending it — ⭐ so the same option covers the two scenes of phase
    #    6: the request **at attach** (`DECISIONI.md` §5.0-sexies, the client
    #    asks for the canvas of its own window by itself) and the **live
    #    resize** with the session started.
    p.add_argument("--adatta", action="append", default=[], metavar="LxH[@S]",
                   help="ADATTA_TELA (0x000B), repeatable; @S = seconds of "
                        "waiting before sending it")
    p.add_argument("--vista", metavar="LxH",
                   help="VISTA (0x0008) after attach — ⚠ §7.1: it must NOT "
                        "change the canvas")
    # ⭐⛔ THE GRACE SECOND OF §7.1 — 22 August 2026.
    #
    # ⛔ The delay is passed in SECONDS and has no default: the rule lives on
    #    a boundary, and a value chosen by the program instead of by the bench
    #    would be a boundary chosen by someone who does not declare why.
    p.add_argument("--puntatore-vecchia", type=float, default=None,
                   metavar="RITARDO",
                   help="§7.1: sends a PUNTATORE to the LAST PIXEL of the "
                        "PREVIOUS canvas, RITARDO seconds after the TELA(ADATTATA).  "
                        "⚠ The time is the CLIENT's: the "
                        "SERVER's interval is LONGER, so stay away from the "
                        "second on both sides")
    p.add_argument("--chiave-dopo", type=float, default=0, metavar="SECONDI",
                   help="after the PUNTATORE, wait SECONDI and send a "
                        "RICHIEDI_CHIAVE: it serves to let a frame through "
                        "on a still desktop, so that the `input` field of §6.2 "
                        "can say whether the input was INJECTED.  ⚠ Not "
                        "sent if the session has already dropped")
    # ⚠ The cap is NOT an RCP rule: §7.1 requires the answer, not a
    #   time.  It serves not to reproduce the symptom we want to measure.
    p.add_argument("--attesa-tela", type=float, default=5.0,
                   help="how long to wait for a TELA before declaring the "
                        "silence (⚠ it is not a rule of RCP.md)")
    # ═══ THE AUDIO — phase 7 ══════════════════════════════════════════════
    p.add_argument("--video-scrivi", default="",
                   help="where to write the frames taken FROM THE WIRE, just as "
                        "they are — to give them to a third decoder and separate "
                        "our stream from the browser's")
    p.add_argument("--video-codec", default="h264",
                   help="what to declare in `video.codec` (§4.3).  "
                        "⭐ The default is **what Firefox declares**: "
                        "`pagina.html` sends only the codecs that have PAINTED the "
                        "probe, and there HEVC does not paint.  ⛔ `hevc` redoes the "
                        "old yardstick (until 23 August 2026), and the two "
                        "sets of numbers are NOT comparable: `fasi/09` §14.1")
    p.add_argument("--video-profondita", default="8,10",
                   help="what to declare in `video.profondita` (§4.3)")
    p.add_argument("--audio-codec", default="opus,pcm",
                   help="what to declare in `audio.codec` (§4.3).  "
                        "⛔ `pcm` alone is legitimate and is the positive "
                        "control of Opus, not a workaround")
    # ⛔⛔ THE DEFAULT IS `vecchia`, AND IT DOES NOT CHANGE WITHOUT THE USER.
    #     `01-b3-cliente.py` is used by dozens of already-measured benches: with the
    #     new rule as the default, every number already written would stop
    #     being comparable — and the «before / after the cure» comparison would be
    #     exactly what gets lost.
    p.add_argument("--audio-regola", default="vecchia",
                   choices=list(VaglioAudio.REGOLE),
                   help="`vecchia` = §6.3 as the code read it until 22 "
                        "August 2026 (behind ⇒ thrown away); `nuova` = the reorder "
                        "cure of `src/pagina.html` (behind ⇒ thrown "
                        "away ONLY if its place has already passed).  "
                        "⛔ The default is `vecchia` on purpose")
    p.add_argument("--audio-passo-us", type=int, default=0,
                   help="how long a block lasts, in us.  0 = I derive it from the "
                        "PCM payload (⚠ for Opus I cannot decode: without "
                        "this the count of `mancati` stays OFF)")
    p.add_argument("--audio-decodifica-ms", type=float, default=0.0,
                   help="the time we pretend to spend decoding.  "
                        "⚠ At 0 `scartati_tardivi` is not a measurement: it is a "
                        "blind zero (T3)")
    p.add_argument("--certifica", action="store_true",
                   help="⭐ the self-test of the audio screening: it does NOT touch the "
                        "network and the test machine is not needed")
    p.add_argument("--audio-scrivi", default="",
                   help="where to write the received audio blocks, in JSONL — "
                        "the judge of `07-b42` reads this")
    # ═══ THE CLIPBOARD — phase 7, §7.4 ════════════════════════════════════
    p.add_argument("--appunti-copia", default="",
                   help="announce this text to the server (direction device → "
                        "session) and then stay to serve it when it asks")
    p.add_argument("--appunti-attendi", type=float, default=0,
                   help="wait up to N seconds for an announcement from the server, "
                        "ask for it, and write the text that arrives (direction session → "
                        "device)")
    p.add_argument("--appunti-scrivi", default="",
                   help="where to write the clipboard outcome, in JSON — the "
                        "bench `07-b45` reads this")
    p.add_argument("--resta", type=float, default=0)
    # ⭐ Every how many seconds to make oneself heard (0 = never, and it is the default:
    #    keeping quiet is what is needed to measure the silence clock).
    p.add_argument("--vivo", type=float, default=0)
    p.add_argument("--segnale",
                   help="file to write when the session is open")
    # ⭐ The click that gives focus — see `manda_pulsante()`.
    p.add_argument("--clic", default="", metavar="X,Y",
                   help="after `--clic-dopo` seconds, moves the pointer there and "
                        "does a left click: it serves to give FOCUS to a "
                        "window of the remote desktop (without it, on GNOME the "
                        "session clipboard cannot be touched)")
    p.add_argument("--clic-dopo", type=float, default=10.0,
                   help="how long to wait before the click, because the window "
                        "must already be there")
    p.add_argument("--clic-ogni", type=float, default=0.0,
                   help="every how many seconds to REDO the click (0 = once "
                        "only).  ⛔ Needed when the windows to focus "
                        "are more than one, one after the other: focus goes to "
                        "the one that is there at that moment")
    a = p.parse_args()

    # ⭐ `--certifica` exits HERE: it does not touch the network, does not ask for the
    #    password and does not want the test machine.
    if a.certifica:
        sys.exit(certifica())

    if AIOQUIC:
        print(f"   ⛔ without `aioquic` this client cannot attach to "
              f"anything: {AIOQUIC}")
        print("      ⭐ run it INSIDE the container (`enter.sh`), or ask for "
              "`--certifica`, which does not touch the network.")
        sys.exit(2)

    # ⛔ The three audio choices become module variables because
    #    `create_protocol=Cliente` passes no arguments to the constructor.
    #    ⚠ This block runs at module level: the assignment is already
    #    global, and `Cliente.__init__` reads these three lines.
    REGOLA_AUDIO = a.audio_regola
    PASSO_AUDIO_US = a.audio_passo_us
    DECODIFICA_AUDIO_S = a.audio_decodifica_ms / 1000.0
    if REGOLA_AUDIO != "vecchia":
        # ⛔ AND IT IS SAID, loudly: a round with the new rule is NOT comparable
        #    with the numbers of the benches of before, and whoever reads the log afterwards must
        #    know it without having to find the command line again.
        print(f"   ⚠ `--audio-regola {REGOLA_AUDIO}`: this round does NOT use the "
              "rule with which the benches of before were measured")

    a.parola = parola_dagli_argomenti(a)

    def misura(testo, dove):
        """`LxH` or `LxH@S`.  ⛔ A crooked argument is reported, not guessed.

        ⚠ A bench that accepted `1264-800` interpreting it as best it could would give
          a size different from the one the launcher believes they asked for, and
          the number would end up in a report: the form of error **E2**.
        """
        quando = 0.0
        if "@" in testo:
            testo, _, s = testo.partition("@")
            try:
                quando = float(s)
            except ValueError:
                print(f"   ⛔ {dove}: «{s}» is not a number of seconds")
                sys.exit(2)
        parti = testo.lower().split("x")
        if len(parti) != 2 or not all(x.isdigit() for x in parti):
            print(f"   ⛔ {dove}: «{testo}» does not have the form LxH (e.g. 1264x800)")
            sys.exit(2)
        return int(parti[0]), int(parti[1]), quando

    a.adatta = [misura(x, "--adatta") for x in a.adatta]
    a.vista = misura(a.vista, "--vista")[:2] if a.vista else None
    try:
        sys.exit(asyncio.run(principale(a)))
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
