#!/usr/bin/env python3
"""01-b6-tetti.py — ⛔ B6: the three caps of the handshake, measured BY KEEPING QUIET.

    python3 01-b6-tetti.py --fase sani --idle 120000 --tetti-codice CIAO=5000,CREDENZIALI=60000,ATTACCA=10000
    python3 01-b6-tetti.py --fase ping --idle 15000
    python3 01-b6-tetti.py --elenco            (the predictions, without measuring)

⚠ It runs INSIDE the container: aioquic lives there.  It is started and launched
  by `01-b6-lancia.sh`, which is also the only place where the transport
  inactivity cap is chosen — and this file never presumes it: it has it
  stated, prints it, and builds the diagnoses on it.

===========================================================================
⛔ WHAT IT MEASURES, IN ONE USER'S LINE

*«How long it takes to tell you it did not make it, instead of staying there
hanging.»*  `RCP.md` §4.6 puts three caps on the handshake because *«a
connection that stops halfway through the handshake holds a place and declares
it to nobody»*.  This bench does exactly that: it stops halfway and keeps
quiet, three times, at three different points.

| From | To | Cap (§4.6) |
|---|---|---|
| the start (⚠ and WHICH start is the `[?]` question R3.27, see below) | `CIAO` | **5 s** |
| `ECCOMI` sent | `CREDENZIALI` | **60 s** |
| `AMMESSO` sent | `ATTACCA` | **10 s** |

⛔ Once a cap has expired the server **MUST** take leave with `TEMPO_SCADUTO`
   `0x0D` (§8.2), by the two roads of §3.1 — the `CONGEDO` on the control
   channel and the reason code in the closing of the WebTransport session.

===========================================================================
⛔ THE SCENE IS DECLARED, AND IT IS SILENCE

`LEZIONI.md` §1.1 asks for a declared scene, always the same.  Here the scene
**is the client's silence**: after the message that brings the handshake to
the state to measure, this program **sends not one more byte of RCP** until the
end of the window.

⚠ And what passes on the wire anyway — acknowledgements, transport PINGs, the
  keep-alive the server arms — **is not the scene**: it is the transport, and
  `RCP.md` §4.6 names it on purpose as the cure that keeps the connection alive
  while the user types.  It is neither switched off nor counted.

===========================================================================
⛔ THE FIRST DEFENDANT IS THE BENCH: THE FOUR CERTIFICATIONS, BEFORE MEASURING

`REVIEWER.md` §1.2 and `CODER.md` §3.3.  A cap is measured **by waiting for
nothing to happen**, and a measurement made of waits is the one that goes wrong
most easily: if the tool cannot read a `CONGEDO`, every cap comes out «never
expired» and the bench prints three reds against a server doing its job.

  cert-giro-completo   ⭐ the tool can get to the end of a handshake that
                       succeeds.  ⛔ And it is also the check of the INITIAL
                       STATE (B0.1/B0.3): if `TROPPI_TENTATIVI` arrives here,
                       the address is inside the §4.4-bis window left by
                       another bench, and every red that follows would be a
                       false red.  The bench stops and says so, instead of
                       measuring;
  cert-cronometro      ⭐ the stopwatch can measure a KNOWN wait on the wire:
                       the fixed second of §4.4-bis, which B3 measured
                       1074-1085 ms `[M]`.  Whoever cannot see a second that is
                       surely there cannot say anything about five;
  cert-congedo-noto    ⛔ **the certification that counts**: a KNOWN and
                       IMMEDIATE farewell is provoked — `CIAO(versione = 2)` on
                       `/rcp/1`, which §2.2 requires to be rejected with
                       `VERSIONE_INCOMPATIBILE` `0x0A` (B5: 36 out of 36) — and
                       it is verified that the reader sees it **by both roads
                       of §3.1**.  Without it, «no farewell arrived» stays
                       ambiguous between «the server did not send it» and «I
                       cannot read it»;
  cert-morte-silenziosa ⛔ only in the `ping` phase: the tool can see a
                       connection that dies **without a reason**, and can call
                       it by its name.  It is the diagnosis §4.6 asks to be able
                       to produce — *«a death at 30 s without a reason is the
                       missing PING»* — and a bench that has never produced it
                       has no right whatsoever to write it.

⛔ If a certification does not pass, the caps are NOT measured: it exits 4.  A
   negative outcome with an uncertified tool is not a measurement.

===========================================================================
⛔ THE CHECK THAT SAYS NO: «NOT BEFORE» IS HALF OF THE REQUIREMENT

A cap has two halves, and the second one nobody writes: *not after* — which is
the case everybody tests — and ⛔ *not before*.  A server that took leave
**immediately** with `TEMPO_SCADUTO` would give `TEMPO_SCADUTO` in all three
cases, and a bench that looks only at the reason would promote it with full
marks.

For every cap there is therefore a `-presto` case: one waits **70 %** of the
cap in silence and **then** sends the expected message, which **MUST** be
served.  They are the ⭐ expected greens of this bench, and there are three.

===========================================================================
⛔ THE TRAP OF THIS BENCH: WHO CLOSES, THE PROTOCOL OR THE TRANSPORT?

`RCP.md` §4.6 says it in full: the 60 seconds of the password were
**unreachable**, because at the thirtieth QUIC's idle timeout triggers and the
connection dies **silently, without a reason**.  The cure is the server's —
the **transport PINGs** — and without it the bench would measure 30 where the
document says 60, blaming the bench.

⛔ Hence **two phases, and the second is the one that tests something**:

  `--fase sani`  the transport cap is raised to **120 s**, above all three
                 protocol caps: here the numbers read clean, because only RCP
                 can be the one closing.
                 ⚠ But with 120 s **even a server that sends no PING** would
                 give 60 s: this phase alone would bless the violation that
                 §4.6 exists to cure — `LEZIONI.md` §1.3.

  `--fase ping`  ⭐ the transport cap is lowered **BELOW** the protocol cap
                 (15 s against 60 s).  If the server keeps the connection alive
                 with PINGs, `TEMPO_SCADUTO` arrives **all the same at 60 s**,
                 after having crossed the transport cap four times.  If it does
                 not send them, the connection dies at **15 s without a
                 reason** — and it is precisely the signature §4.6 describes,
                 with a number that cannot be confused with any of the three
                 caps.
                 ⛔ And in the same phase, on the same server, `cert-morte-
                 silenziosa` **produces the death at 15 s on purpose**: the two
                 lines together say that the survival of the other is not
                 luck.

⚠ **And the transport cap is not decided by the server alone.**  RFC 9000
  §10.1: the **minimum of the two announced values** holds, and `aioquic` by
  itself announces 60 s — that is exactly the cap this bench must measure.
  Here the client configuration raises it to `IDLE_NOSTRO` on purpose, so that
  the minimum of the two is never ours; and the value that counts is **read
  from the peer** with B2's probe (`01-b6-lancia.sh` does it), not presumed.

===========================================================================
⛔ WHERE THE STOPWATCH OF THE FIRST CAP STARTS — the `[?]` R3.27, and this bench
   is the place where it gets resolved

§4.6 says *«TLS handshake finished → `CIAO` received: 5 s»*.  ⛔ But in
WebTransport the HTTP/3 **connection** and the **session** are two separate
things, and between the two instants at least one network round trip passes:
the browser may have established the connection long before the page calls the
API.  If the server starts the stopwatch where the document says and the bench
measures it from the opening of the session, the difference reads as **a wrong
cap**.

Three cases separate them, and each prints a number instead of an opinion:

  ciao-tetto              the normal case: session, control channel,
                          silence.  The expected number is 5 s from here;
  ciao-senza-controllo    ⛔ session open and **control channel never
                          opened**.  To the letter of §4.6 the cap has already
                          started (TLS finished a while ago) and at 5 s it
                          must be over.  If nothing happens, the stopwatch
                          **does not start from TLS**;
  ciao-sessione-tardiva   ⛔ the worst case of R3.27: TLS is finished, one
                          waits `RITARDO_SESSIONE` seconds **without opening
                          the session**, then opens it and keeps quiet.  If the
                          cap started from TLS, the budget would be **already
                          consumed** and the farewell would arrive immediately;
                          if it starts from the session, it arrives 5 s after
                          the opening.

⛔ The verdict of these three is not «passes/does not pass» but **an answer**,
   and the answer is compared by the bench (B0.4): if the stopwatch starts from
   the session, §4.6 line 1 **says something the code does not do**, and the
   cure is in the document — «it changes by one word», as the phase declares
   it.  In that case the bench exits **3**, which is not the server's red.

===========================================================================
⛔ AND THE THREE NUMBERS THIS BENCH COMPARES, WHICH ARE THREE AND NOT TWO

  the DOCUMENT   `RCP.md` §4.6 — written below in `TETTI_DOC`, by hand, and
                 it is the arbiter: `RCP.md` is the arbiter of the wire;
  the CODE       the `#define TETTO_*` of `banchi/rcp/rcp.c`, read from the
                 source and passed by `01-b6-lancia.sh` with `--tetti-codice`;
  the MEASUREMENT  what arrives on the wire.

⛔ **And here there is a dated fact that concerns this bench.**  On 10 Aug
   2026, finding R9.9, `TETTO_ATTACCA` was brought from **60 000 to 10 000
   ms** on the sole reading of §4.6, **without anybody measuring it** — and the
   comment in the code declares it: *«no bench saw it: B6 is not written
   yet»*.  This bench is **the first witness of that number**.  Hence the rule
   of this file: the three numbers are printed **all three**, always, and if
   they do not agree the bench says so instead of adapting to one of the two.

===========================================================================
⛔ WHAT THIS BENCH DOES NOT TEST, AND IT MUST BE SAID

  · the cap is **not** tested on a real client (browser): the page has no way
    of «keeping quiet on command», and the bench measures the SERVER.  That the
    browser sees the same thing is `[?]`, and it is up to B11;
  · the three caps are tested **one per connection**: that an expired cap
    leaves no aftermath on a following connection is covered by B0.5, here, but
    the case of two caps in the **same** connection does not exist — the state
    machine of §4 does not go back there;
  · `rcp_azzera_registro_sessioni()` exists for the bench ⛔ **but has no
    caller** reachable from here: it is not grafted at any point of the
    server.  The state between one phase and the next is reset **by restarting
    the server**, and `01-b6-lancia.sh` does it.  Declared, because whoever
    reads the line in `rcp.h` believes the bench uses it.
"""
import argparse
import asyncio
import importlib.util
import os
import ssl
import struct
import sys

from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration
from aioquic.asyncio import connect

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ The B3 client is IMPORTED, not copied — as B5 does.  Inside it is the line
#    that prevents it from handing the control-channel events to aioquic's
#    HTTP/3 layer (without which the connection dies at the hand of the
#    CLIENT), the reader of the closing capsule of §3.1 point 3, and the
#    recording of §11.1.  A diverging copy would bring back here the defects
#    already paid for there, disguised as server defects.
_spec = importlib.util.spec_from_file_location(
    "b3cliente", os.path.join(QUI, "01-b3-cliente.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)

# ⛔ And the TARGET's profile: the differences between the two servers in a single file.
_spec_b0 = importlib.util.spec_from_file_location(
    "b0bersaglio", os.path.join(QUI, "01-b0-bersaglio.py"))
b0 = importlib.util.module_from_spec(_spec_b0)
_spec_b0.loader.exec_module(b0)

s, inquadra, MOTIVI = b3.s, b3.inquadra, b3.MOTIVI

TEMPO_SCADUTO = 0x0D
VERSIONE_INCOMPATIBILE = 0x0A
TROPPI_TENTATIVI = 0x08
CONGEDO, RESPINTO = 0x000C, 0x0005

# ⛔ THE THREE CAPS AS THE DOCUMENT WRITES THEM — `RCP.md` §4.6, table.
#    They are not read from the code: the code is the defendant.  The code's
#    value arrives separately, with `--tetti-codice`, and the two are compared.
TETTI_DOC = {"CIAO": 5000, "CREDENZIALI": 60000, "ATTACCA": 10000,
             # ⭐ The line §4.6 did not have, ✅ decided by the user on 11 Aug
             #    2026 (`DECISIONI.md` §7.17): from the opening of the
             #    WebTransport SESSION to the opening of the control CHANNEL, 5 s.
             # ⛔ This bench asked for it: it was the one saying «NOTHING
             #    happened in 20 s», and for four days that number was an
             #    answer without a rule to judge it against.
             # ⚠ The document/code comparison for this line is NOT done: the
             #   code's value is in `src/webtransport.c`
             #   (`WT_TETTO_CANALE_NS`) and not among the `#define TETTO_*` of
             #   `rcp.c` that the launcher knows how to read.  The bench declares
             #   it instead of keeping quiet — «they did not tell me» is not «they match».
             "CANALE": 5000}

# ⚠ The tolerance, and why it is asymmetric.
#
#    The bench's stopwatch starts from the instant it **reads** the message
#    that brings to the state (or **sends** the channel header), and the
#    server's from the instant it sent it: between the two there is half a
#    network round trip, so the measurement may come out a touch **shorter**
#    than the cap.  On the other side the server evaluates the caps at the pace
#    at which it goes through its write path, so it may come out longer.
#
# ⛔ And it stays very wide compared with what it must tell apart: 5 from 30, 10
#    from 60, 60 from 15.  A tolerance that does not separate the numbers in play
#    is not a tolerance, it is a blessing.
TOLL_GIU, TOLL_SU = 1000, 2500

# ⛔ THE INACTIVITY CAP WE ANNOUNCE, AND WHY IT IS NOT ALWAYS THE SAME.  It is
#    our half of the rule «the cap is read from the peer, not presumed», and
#    they are two opposite needs in two different phases.
#
#  · «sani» phase: it must be **well above** all the protocol caps, or we would
#    be the ones closing.  ⚠ aioquic's default is 60 s, that is exactly the §4.6
#    cap to be measured: leaving it would be measuring our own clock believing
#    we are measuring its;
#
#  · «ping» phase: it must be **slightly above** the server's, and the reason is
#    a fact of the transport that blinds whoever does not know it.  ⛔ **A death
#    from inactivity does NOT send a `CONNECTION_CLOSE`** (RFC 9000 §10.1:
#    whoever times out from inactivity discards the state and keeps quiet).  If
#    the server stopped keeping the connection alive, **nothing** would arrive
#    from the wire: the only way to see that death is for OUR clock to expire
#    too.  With ours slightly above its, the death — if there is one — is seen a
#    few seconds later; and if the PINGs are there, every PING resets it and the
#    60 s are measured anyway.
#    ⚠ And if `aioquic` used the minimum of the two instead of its own, it
#      would be seen even earlier: in both cases it is seen, and that is why it
#      is slightly above and not well above.
IDLE_SANI = 180.0
IDLE_PING_MARGINE = 5.0

# How long one waits before opening the session, in `ciao-sessione-tardiva`.
# ⚠ It MUST be longer than the `CIAO` cap, or the case separates nothing.
RITARDO_SESSIONE = 8.0

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"


def adesso():
    return asyncio.get_event_loop().time()


# ===========================================================================
class Attesa:
    """What happened while we kept quiet — from the receiving side.

    ⛔ The outcomes are FIVE and they have five names, because «nothing
       arrived» and «everything died» are opposite diagnoses that look the same
       if one prints a `yes`/`no` (`LEZIONI.md` §1.9, form E8).
    """

    def __init__(self, nome):
        self.nome = nome
        # ⛔ The half that gets forgotten: did the case GET to the state it
        #    wanted to measure?  A case that stops in the preparation — an
        #    `ECCOMI` that does not arrive, the credentials refused — has tested
        #    nothing, and without this mark it would count as a server red.
        #    It is B5's `provocato` (finding R7.1) applied to the caps.
        self.pronto = False
        self.fase = "opening"
        self.esito = "niente"      # congedo · morte-silenziosa · sessione-chiusa
        #                            · canale-chiuso · niente · errore
        self.motivo = None         # read from a CONGEDO/RESPINTO on the wire
        self.tipo_motivo = None
        self.dettaglio = ""
        self.codice_wt = None      # §3.1 point 3
        self.ms = None             # how long it took, from the reference
        self.riferimento = ""      # FROM WHAT one counts — always printed
        self.errore = None

    def __str__(self):
        p = [f"from «{self.riferimento}»"] if self.riferimento else []
        if not self.pronto:
            p.append(f"⛔ NEVER GOT to the state to measure (stopped in "
                     f"«{self.fase}»)")
        p.append(f"esito={self.esito}")
        if self.ms is not None:
            p.append(f"{self.ms / 1000:.2f} s")
        if self.motivo is not None:
            p.append(f"motivo={self.motivo:#04x}="
                     f"{MOTIVI.get(self.motivo, '?')} in {self.tipo_motivo}")
        p.append("chiusura-wt=" + ("(absent)" if self.codice_wt is None
                                   else f"{self.codice_wt:#04x}"))
        if self.errore:
            p.append(f"errore={self.errore}")
        return "  ".join(p)


async def ascolta(cli, t0, riferimento, finestra, es, grazia=1.5):
    """Keeps quiet and watches, until the farewell or the end of the window.

    ⛔ **It is the only place where `es.motivo` and `es.ms` are written**, and it
       writes them from what arrived on the wire: §8.1 wants the farewell
       verified from the receiving side, never from the log of whoever sends it.

    ⚠ It polls with a short loop instead of waiting for a single event: the
      events we care about are of two kinds — a message on the control channel
      and the **death of the connection** — and waiting for only one would make
      the other invisible until the window expires, that is it would turn a
      death at 15 s into a «nothing for 75 s».
    """
    es.riferimento = riferimento
    scadenza = t0 + finestra
    while adesso() < scadenza:
        try:
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=0.02)
        except asyncio.TimeoutError:
            # ⛔ No message: did something drop in the meantime?
            if cli.caduta is not None and es.motivo is None:
                es.ms = (adesso() - t0) * 1000
                es.esito = _classifica(cli)
                break
            continue
        if m is None:
            # the control channel or the connection has closed
            if es.motivo is None:
                es.ms = (adesso() - t0) * 1000
                es.esito = _classifica(cli)
            break
        tipo, corpo, _ = m
        if tipo not in (CONGEDO, RESPINTO):
            # ⚠ A message that has nothing to do with it is a fact, not noise:
            #   §4.2 provides for nothing on the control channel while the
            #   server waits, and whoever sends one is doing something else.
            es.errore = (f"unexpected message while we kept quiet: {tipo:#06x} "
                         f"({len(corpo)} bytes)")
            continue
        es.ms = (adesso() - t0) * 1000
        es.esito = "congedo"
        es.tipo_motivo = "CONGEDO" if tipo == CONGEDO else "RESPINTO"
        # ⛔ An EMPTY body is not «no reason»: §7.1 wants `u8 motivo` and
        #    §3.1 forbids code 0.  With `corpo[0] if corpo else None` a server
        #    that closes BADLY would be easier to let through than one that
        #    closes well (it is B5's finding R7.2).
        if not corpo:
            es.errore = (f"{es.tipo_motivo} with an EMPTY body: §7.1 wants "
                         "at least the reason byte")
            break
        es.motivo = corpo[0]
        if tipo == CONGEDO and len(corpo) >= 3:
            n = struct.unpack("!H", corpo[1:3])[0]
            es.dettaglio = corpo[3:3 + n].decode("utf-8", "replace")
        break
    else:
        # ⛔ The window has expired.  «Nothing» is an outcome, and it wants its
        #    number: without it, the line «nothing happened» does not say for
        #    how long nothing happened — that is it does not say the
        #    denominator of the wait (`LEZIONI.md` §1.9, fourth rule).
        es.ms = (adesso() - t0) * 1000
        if cli.caduta is not None and es.motivo is None:
            es.esito = _classifica(cli)

    # ⛔ §3.1 POINT 3, AND WHY ONE WAITS A LITTLE.
    #    The `CONGEDO` travels on the control channel, the reason code inside
    #    the capsule that closes the session: two different roads, two
    #    different instants.  Reading the second at the exact instant of the
    #    first would measure our hurry.  ⚠ The window is declared and bounded:
    #    if it expires, the value stays `None` and the verdict counts it as missed.
    if es.motivo is not None or es.errore is not None:
        fine = adesso() + grazia
        while (cli.codice_chiusura is None and not cli.finito
               and adesso() < fine):
            await asyncio.sleep(0.02)
    es.codice_wt = cli.codice_chiusura
    return es


def _classifica(cli):
    """⛔ How it died: the name, not a `no`.

    They are the three defendants §4.6 asks to separate, and they have three
    different names because they lead to three different places: the transport
    cap (the missing PINGs), the session closed without a farewell (§3.1 point 2
    not done), the channel closed dry.
    """
    c = cli.caduta or ""
    if cli.codice_chiusura is not None:
        return "sessione-chiusa"
    if c.startswith("connection TERMINATED"):
        return "morte-silenziosa"
    if "session" in c:
        return "sessione-chiusa"
    if "control channel" in c:
        return "canale-chiuso"
    return "niente"


# ===========================================================================
async def apri(a, percorso="/rcp/1"):
    """Connection + WebTransport session.  ⚠ NOT the control channel."""
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536,
                             idle_timeout=a.idle_nostro)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    gestore = connect(a.indirizzo, a.porta, configuration=conf,
                      create_protocol=b3.Cliente)
    cli = await gestore.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    cli.apri_sessione(autorita, percorso)
    stato = await asyncio.wait_for(cli.accettata, timeout=8)
    return gestore, cli, stato


async def solo_connessione(a):
    """Only QUIC + TLS: no WebTransport session, no channel.

    It is needed by `cert-morte-silenziosa`: it is the connection that **nobody**
    keeps alive, so the one the transport cap MUST take away.
    """
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536,
                             idle_timeout=a.idle_nostro)
    conf.verify_mode = ssl.CERT_NONE
    gestore = connect(a.indirizzo, a.porta, configuration=conf,
                      create_protocol=b3.Cliente)
    cli = await gestore.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    return gestore, cli


def apri_controllo(cli):
    """Opens the control channel AND PUTS IT ON THE WIRE, without sending anything on it.

    ⛔ The `transmit()` is not a formality: `create_webtransport_stream` only
       queues the stream header, and without a write pass those bytes **do not
       leave**.  The server would see no stream, would not call `rcp_avvia`,
       and the stopwatch of the first cap would not start at all: the bench
       would measure its own output queue and blame the server.
    """
    sid = cli.apri_controllo()
    cli.transmit()
    return sid


def ciao_buono(versione=1):
    voci = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
            ("audio.codec", "opus,pcm"), ("client.nome", "banco-b6 0.1.0")]
    corpo = struct.pack("!HH", versione, len(voci))
    for n, v in voci:
        corpo += s(n) + s(v)
    return inquadra(0x0001, corpo)


def credenziali(a):
    return inquadra(0x0003, s(a.utente) + s(a.parola))


def attacca():
    return inquadra(0x0006, struct.pack("!IIII", 1920, 1080, 1920, 1080)
                    + s("it"))


# ===========================================================================
# THE CASES.  ⛔ Each declares its PREDICTION before measuring: the «expected»
#             column is in the file, not in the comment on the result.
# ===========================================================================
CASI = []


def caso(nome, fase, tetto, atteso, spiega):
    """`tetto` = key of TETTI_DOC or None · `atteso` = reason or None (⭐ must
    pass) or "risposta" (⛔ it is not a pass/fail: it is an open question to
    which this case answers with a number)."""
    def dec(f):
        CASI.append({"nome": nome, "fase": fase, "tetto": tetto,
                     "atteso": atteso, "spiega": spiega, "f": f})
        return f
    return dec


# ── The three caps ──────────────────────────────────────────────────────────
@caso("ciao-tetto", "sani", "CIAO", TEMPO_SCADUTO,
      "control channel open and no CIAO: §4.6 line 1, 5 s")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"extended CONNECT :status={stato}"
            return es
        apri_controllo(cli)
        t0 = adesso()
        es.pronto, es.fase = True, "channel open, silence"
        await ascolta(cli, t0, "opening of the control channel",
                      TETTI_DOC["CIAO"] / 1000 + 15, es)
    finally:
        await gestore.__aexit__(None, None, None)
    return es


@caso("credenziali-tetto", "sani", "CREDENZIALI", TEMPO_SCADUTO,
      "ECCOMI received and no CREDENZIALI: §4.6 line 2, 60 s")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"extended CONNECT :status={stato}"
            return es
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        t0 = adesso()
        es.pronto, es.fase = True, "ECCOMI read, silence"
        await ascolta(cli, t0, "ECCOMI read",
                      TETTI_DOC["CREDENZIALI"] / 1000 + 15, es)
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        es.errore = f"{type(e).__name__}: {e}"
    finally:
        await gestore.__aexit__(None, None, None)
    return es


@caso("attacca-tetto", "sani", "ATTACCA", TEMPO_SCADUTO,
      "⛔ AMMESSO received and no ATTACCA: §4.6 line 3, 10 s — and it is the "
      "number changed on 10 Aug 2026 without anybody measuring it")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"extended CONNECT :status={stato}"
            return es
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        es.fase = "CREDENZIALI sent"
        cli.manda(credenziali(a))
        # ⚠ `attesa=20`: the fixed second of §4.4-bis is in between, and PAM.
        await b3.attendi(cli, "AMMESSO", attesa=20)
        t0 = adesso()
        es.pronto, es.fase = True, "AMMESSO read, silence"
        await ascolta(cli, t0, "AMMESSO read",
                      TETTI_DOC["ATTACCA"] / 1000 + 15, es)
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
    finally:
        await gestore.__aexit__(None, None, None)
    return es


# ── ⭐ The three checks that say NO: the cap does not trigger BEFORE ─────────
@caso("ciao-presto", "sani", "CIAO", None,
      "⭐ keep quiet for 70 % of the cap and THEN send CIAO: ECCOMI MUST arrive")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"extended CONNECT :status={stato}"
            return es
        apri_controllo(cli)
        await asyncio.sleep(TETTI_DOC["CIAO"] * 0.7 / 1000)
        es.pronto, es.fase = True, "CIAO sent late"
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        es.esito = "servito"
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
        es.esito = "rifiutato"
        es.codice_wt = cli.codice_chiusura
    finally:
        await gestore.__aexit__(None, None, None)
    return es


@caso("credenziali-presto", "sani", "CREDENZIALI", None,
      "⭐ keep quiet for 70 % of the 60 s and THEN send the CREDENZIALI: AMMESSO "
      "MUST arrive — and it is also the proof that the PINGs hold 42 s")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"extended CONNECT :status={stato}"
            return es
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        await asyncio.sleep(TETTI_DOC["CREDENZIALI"] * 0.7 / 1000)
        es.pronto, es.fase = True, "CREDENZIALI sent late"
        cli.manda(credenziali(a))
        await b3.attendi(cli, "AMMESSO", attesa=20)
        es.esito = "servito"
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
        es.esito = "rifiutato"
        es.codice_wt = cli.codice_chiusura
    finally:
        await gestore.__aexit__(None, None, None)
    return es


@caso("attacca-presto", "sani", "ATTACCA", None,
      "⭐ keep quiet for 70 % of the 10 s and THEN send ATTACCA: SESSIONE MUST "
      "arrive")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"extended CONNECT :status={stato}"
            return es
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        cli.manda(credenziali(a))
        await b3.attendi(cli, "AMMESSO", attesa=20)
        await asyncio.sleep(TETTI_DOC["ATTACCA"] * 0.7 / 1000)
        es.pronto, es.fase = True, "ATTACCA sent late"
        cli.manda(attacca())
        await b3.attendi(cli, "SESSIONE")
        es.esito = "servito"
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
        es.esito = "rifiutato"
        es.codice_wt = cli.codice_chiusura
    finally:
        await gestore.__aexit__(None, None, None)
    return es


# ── ⛔ Where the stopwatch of the first cap starts — the `[?]` R3.27 ────────
@caso("ciao-senza-controllo", "sani", "CANALE", TEMPO_SCADUTO,
      "⛔ session open and control channel NEVER opened: §4.6 line 4, 5 s "
      "(DECISIONI.md §7.17).  ⚠ And the CONGEDO here is NOT enforceable: the channel "
      "does not exist, so the reason can arrive ONLY in the closing code "
      "of the session — it is the condition decided in §7.15 the same day")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"extended CONNECT :status={stato}"
            return es
        t0 = adesso()
        es.pronto, es.fase = True, "session open, no channel"
        await ascolta(cli, t0, "opening of the WebTransport session",
                      TETTI_DOC["CIAO"] / 1000 + 15, es)
    finally:
        await gestore.__aexit__(None, None, None)
    return es


@caso("ciao-sessione-tardiva", "sani", "CIAO", TEMPO_SCADUTO,
      "⛔ the worst case of R3.27: TLS finished, one waits, THEN the "
      "session is opened.  Immediate farewell = the budget was already consumed "
      "(stopwatch from TLS); farewell 5 s later = stopwatch from the session")
async def _(a, es):
    gestore, cli = await solo_connessione(a)
    try:
        # ⛔ One waits WITH THE CONNECTION OPEN and without opening the session:
        #    it is exactly the browser that established HTTP/3 long before the
        #    page calls the WebTransport API.
        await asyncio.sleep(RITARDO_SESSIONE)
        if cli.caduta is not None:
            es.fase = (f"the connection dropped during the wait: "
                       f"{cli.caduta}")
            return es
        cli.apri_sessione(f"{a.indirizzo}:{a.porta}", "/rcp/1")
        stato = await asyncio.wait_for(cli.accettata, timeout=8)
        if stato != "200":
            es.fase = f"extended CONNECT :status={stato}"
            return es
        apri_controllo(cli)
        t0 = adesso()
        es.pronto = True
        es.fase = f"channel opened {RITARDO_SESSIONE:.0f} s after TLS"
        await ascolta(cli, t0, f"channel opened {RITARDO_SESSIONE:.0f} s after "
                               f"the end of TLS",
                      TETTI_DOC["CIAO"] / 1000 + 15, es)
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
    finally:
        await gestore.__aexit__(None, None, None)
    return es


# ── ⭐ The phase that tests the transport PINGs (§4.6, box R1.8) ────────────
@caso("credenziali-tetto-sotto-il-trasporto", "ping", "CREDENZIALI",
      TEMPO_SCADUTO,
      "⭐ the same 60 s cap, but with a SHORTER TRANSPORT cap: if "
      "TEMPO_SCADUTO arrives at 60 s the PINGs of §4.6 are there; if it dies at "
      "the transport cap WITHOUT a reason, they are missing")
async def _(a, es):
    gestore, cli, stato = await apri(a)
    try:
        if stato != "200":
            es.fase = f"extended CONNECT :status={stato}"
            return es
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        t0 = adesso()
        es.pronto, es.fase = True, "ECCOMI read, silence under a short cap"
        await ascolta(cli, t0, "ECCOMI read",
                      TETTI_DOC["CREDENZIALI"] / 1000 + 15, es)
    except Exception as e:  # noqa: BLE001
        es.errore = f"{type(e).__name__}: {e}"
    finally:
        await gestore.__aexit__(None, None, None)
    return es


# ===========================================================================
# THE CERTIFICATIONS.  ⛔ They run BEFORE the cases, and if they fail the cases do not run.
# ===========================================================================
async def cert_giro_completo(a):
    """⭐ The tool can get to the end — and the initial state is clean.

    ⛔ It also counts as B0.1/B0.3: `TROPPI_TENTATIVI` here means the address
       is inside the §4.4-bis window left by another bench (B5 leaves it on
       purpose, B8 too), and every red that follows would be a false red —
       precisely the one B0.3 exists to prevent.

    Returns (ok, text, blocked, ms_of_the_fixed_second).
    """
    # ⛔ «The connection does not even open» is also an outcome of this
    #    certification, and it has its own diagnosis: without this branch the
    #    bench died with a Python traceback, which is the worst way of saying
    #    «the server is not there» — and it prints no denominator.
    try:
        gestore, cli, stato = await apri(a)
    except Exception as e:  # noqa: BLE001
        return False, f"the session does not open: {type(e).__name__}: {e}", False, None
    ms = None
    try:
        if stato != "200":
            return False, f"extended CONNECT :status={stato}", False, None
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI")
        t0 = adesso()
        cli.manda(credenziali(a))
        try:
            await b3.attendi(cli, "AMMESSO", attesa=20)
        except RuntimeError as e:
            testo = str(e)
            # ⛔ «It does not get in» has more than one cause, and the bench must
            #    name ONE only when it knows which: the §4.4-bis block has a
            #    proper name and a different cure (waiting), and confusing it
            #    with «the server is broken» sends one looking in the wrong place.
            return False, testo, "TROPPI_TENTATIVI" in testo, None
        ms = (adesso() - t0) * 1000
        cli.manda(attacca())
        await b3.attendi(cli, "SESSIONE")
        return True, "CIAO → ECCOMI → CREDENZIALI → AMMESSO → ATTACCA → SESSIONE", False, ms
    except Exception as e:  # noqa: BLE001
        testo = f"{type(e).__name__}: {e}"
        # ⚠ The §4.4-bis block can also arrive by roads that are not the
        #   `RESPINTO` above: the name is looked at anyway, because the cure
        #   is different (waiting) and the wrong diagnosis sends one looking in
        #   the wrong place — `LEZIONI.md` §1.6.
        return False, testo, "TROPPI_TENTATIVI" in testo, ms
    finally:
        await gestore.__aexit__(None, None, None)


async def cert_congedo_noto(a):
    """⛔ The certification that counts: a KNOWN, immediate farewell, read by
    both roads of §3.1.

    `CIAO(versione = 2)` on `/rcp/1` → `VERSIONE_INCOMPATIBILE` `0x0A` (§2.2,
    and B5 measures it 36 out of 36).  ⭐ If this passes, «no farewell arrived»
    in the cap cases means **that the server did not send it**, and not that
    this program cannot read it.

    Returns (ok, text, seconds).
    """
    es = Attesa("cert-congedo-noto")
    try:
        gestore, cli, stato = await apri(a)
    except Exception as e:  # noqa: BLE001
        return False, f"the session does not open: {type(e).__name__}: {e}", None
    try:
        if stato != "200":
            return False, f"extended CONNECT :status={stato}", None
        apri_controllo(cli)
        t0 = adesso()
        cli.manda(ciao_buono(versione=2))
        await ascolta(cli, t0, "CIAO(versione = 2) sent", 8.0, es)
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}", None
    finally:
        await gestore.__aexit__(None, None, None)
    ok = (es.motivo == VERSIONE_INCOMPATIBILE
          and es.tipo_motivo == "CONGEDO"
          and es.codice_wt == VERSIONE_INCOMPATIBILE)
    return ok, str(es), es.ms


async def cert_morte_silenziosa(a, idle_ms):
    """⛔ The tool can see — and NAME — a death without a reason.

    A lone QUIC connection, without a session and without a channel: nobody keeps
    it alive, so the transport cap **MUST** take it away, and the line that comes
    out must be `morte-silenziosa` — not `congedo`, not `niente`.

    ⭐ It is the negative twin of `credenziali-tetto-sotto-il-trasporto`: on the
       same server and under the same cap, one connection dies and the other
       does not.  Without this line, «it survived» would not prove that
       someone was keeping it alive.
    """
    es = Attesa("cert-morte-silenziosa")
    try:
        gestore, cli = await solo_connessione(a)
    except Exception as e:  # noqa: BLE001
        return False, f"the connection does not open: {type(e).__name__}: {e}", None
    try:
        t0 = adesso()
        es.pronto = True
        await ascolta(cli, t0, "end of TLS", idle_ms / 1000 + 15, es)
    finally:
        await gestore.__aexit__(None, None, None)
    ok = es.esito == "morte-silenziosa" and es.motivo is None
    return ok, str(es), es.ms


async def ancora_vivo(a):
    """⛔ B0.5, after every case: is the server still there?

    «The connection always drops» is satisfied also by a server killed by the
    kernel, which would take away **all the other users' sessions**.
    It gets as far as `ECCOMI`, which is the first answer the server really
    composes.
    """
    try:
        gestore, cli, stato = await apri(a)
    except Exception as e:  # noqa: BLE001
        return False, f"not even the connection opens: {type(e).__name__}: {e}"
    try:
        if stato != "200":
            return False, f"extended CONNECT :status={stato}"
        apri_controllo(cli)
        cli.manda(ciao_buono())
        await b3.attendi(cli, "ECCOMI", attesa=8)
        return True, "a new connection gets to ECCOMI"
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        await gestore.__aexit__(None, None, None)


# ===========================================================================
def riga(ok, nome, testo):
    print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  "
          f"{nome:34s} {testo}")


def riga_gialla(nome, testo):
    """⚠ For the ANSWERS: they are not pass/fail, they are numbers."""
    print(f"    {GIALLO}??{GRIGIO}  {nome:34s} {testo}")


def dentro_tolleranza(ms, tetto_ms):
    return tetto_ms - TOLL_GIU <= ms <= tetto_ms + TOLL_SU


def leggi_tetti_codice(testo):
    """`CIAO=5000,CREDENZIALI=60000,ATTACCA=10000` → dictionary.

    ⛔ And «they did not tell me» is not «they match»: if the parameter is
       missing, the document/code comparison **is not done** and it is declared
       that it was not done.  A comparison skipped silently is worse than a
       failed comparison (`LEZIONI.md` §1.9: the denominator, not only the result).
    """
    fuori = {}
    for pezzo in (testo or "").split(","):
        pezzo = pezzo.strip()
        if not pezzo:
            continue
        if "=" not in pezzo:
            raise SystemExit(f"⛔ --tetti-codice: «{pezzo}» does not have the form NAME=value")
        n, v = pezzo.split("=", 1)
        fuori[n.strip().upper()] = int(v.strip())
    return fuori


async def principale(a):
    tetti_codice = leggi_tetti_codice(a.tetti_codice)
    # ⛔ Our inactivity cap depends on the phase — see the box next to
    #    IDLE_SANI: in the «ping» phase it is the only way we have to SEE a
    #    death from inactivity, which sends nothing on the wire.
    a.idle_nostro = (IDLE_SANI if a.fase == "sani"
                     else a.idle / 1000 + IDLE_PING_MARGINE)

    if a.elenco:
        print(f"== B6 — the three caps of the handshake (RCP.md §4.6)")
        print(f"   {len(CASI)} cases in two phases.  Every line is a PREDICTION\n")
        for c in CASI:
            if c["atteso"] is None:
                att = "⭐ MUST PASS (the cap does not trigger before)"
            elif c["atteso"] == "risposta":
                att = "⛔ ANSWER TO AN OPEN QUESTION (no pass/fail)"
            else:
                att = (f"{c['atteso']:#04x} {MOTIVI.get(c['atteso'], '?')} at "
                       f"{TETTI_DOC[c['tetto']] / 1000:.0f} s")
            print(f"  [{c['fase']:4s}] {c['nome']:36s} {att}")
            print(f"  {'':43s} {c['spiega']}")
        print("\n  And first of all: cert-giro-completo · cert-cronometro ·")
        print("  cert-congedo-noto · cert-morte-silenziosa (only phase «ping»)")
        return 0

    casi = [c for c in CASI if c["fase"] == a.fase
            and (not a.solo or a.solo in c["nome"])]

    # ⛔⭐ THE CAP OF §7.17 DOES NOT EXIST ON BOTH TARGETS, and it is declared
    #     instead of discovered at every run — finding R12-A.35, 11 Aug 2026.
    #
    # `[M]`: against the GRAFT the case `ciao-senza-controllo` stays hanging **20 s
    # without anything happening**, and B6 exits 1.  ⭐ And it is right: the cure of
    # §7.17 is `WT_TETTO_CANALE_NS` in `src/webtransport.c`, that is in the product.
    # The graft is the ngtcp2 example and does not have a WebTransport layer of
    # its own — that cap has no place to live.
    #
    # ⚠ It is the same shape as `server-in-chiusura` in B7, and it is treated the
    #   same way: the case is removed AND IT IS SAID, instead of letting one
    #   believe that numerator and denominator are the usual ones.
    # ⛔ Without it, B6 cannot be CERTIFIED against the graft: the healthy run
    #   does not start from green, and a bench already red with the fault is a
    #   tautology.
    if not b0.profilo(a.bersaglio).get("tetto_canale", True):
        tolti = [c["nome"] for c in casi if c["tetto"] == "CANALE"]
        casi = [c for c in casi if c["tetto"] != "CANALE"]
        if tolti:
            print(f"    {GIALLO}⚠ REMOVED on «{a.bersaglio}»: {', '.join(tolti)}"
                  f"{GRIGIO}")
            print(f"       ⛔ The cap of §7.17 (session open, channel never "
                  f"opened) belongs to the PRODUCT:")
            print(f"       `WT_TETTO_CANALE_NS` is in `src/webtransport.c`, and "
                  f"this target does not")
            print(f"       have a WebTransport layer of its own to put it in.")
            print(f"       ⚠ It is not «passed»: it is NOT TESTED here, and the "
                  f"denominator says so.")

    # ⛔ ZERO CASES IS NOT «ALL PASSED» — the lesson of R7.15 on B5.  A typo in
    #    the filter must not have the colour of green.
    if not casi:
        print(f"    {ROSSO}⛔ phase «{a.fase}» + filter «{a.solo}»: ZERO cases "
              f"selected out of {len(CASI)}{GRIGIO}")
        print("       This is NOT a green.  The names are read with --elenco.")
        return 2

    print(f"== B6 — the three caps of the handshake · phase «{a.fase}»")
    print(f"   {len(casi)} cases out of {len(CASI)} selected")
    print(f"   the scene: the client KEEPS QUIET — no RCP byte after the message "
          f"that brings to the state.")
    print(f"   Acknowledgements and transport PINGs are not the scene, and are "
          f"declared (§4.6).")
    # ⛔ THE RUN'S LOG — and for B6 it is not an extra: until 11 Aug 2026
    #    **no B6 `.jsonl` existed**.  Its three numbers — 5.0 · 60.1 · 10.0 s —
    #    lived only on screen and in `README.md`, the scene of that run could
    #    not be reconstructed, and those numbers cannot be re-verified by
    #    anyone.
    a.reg = b0.Registro(a.uscita, a.bersaglio, a.porta, a.giro or None,
                        a.md5 or None)
    prof = a.reg.profilo
    # ⛔⭐ AND B6'S BIGGEST DIFFERENCE BETWEEN THE TWO TARGETS IS DECLARED HERE.
    #
    #     B6's two phases exist because the TRANSPORT cap can be moved: 120 s
    #     above all three protocol caps («sani», where only RCP can be the one
    #     closing) and 15 s below the 60 s of the credentials («ping», where one
    #     sees whether the PINGs of §4.6 hold).
    #
    #  ⛔ ON THE PRODUCT THAT CAP DOES NOT MOVE: `#define IDLE_MS 30000` in
    #     `src/trasporto.c`, and no option touches it (no `getenv` in all of
    #     `src/`).  The two phases therefore run against **the same** cap, and
    #     the consequences are two and opposite:
    #
    #       · CIAO (5 s) and ATTACCA (10 s) stay clean: 30 > 10, only RCP can be
    #         the one closing, and the two numbers read as before;
    #       · ⛔ CREDENZIALI (60 s) is NO longer clean in the «sani» phase: 30 < 60,
    #         so that case measures **the same thing** as the case of the
    #         «ping» phase.  ⚠ Counting them as two independent confirmations
    #         would be counting the same measurement twice, which is the inflated
    #         denominator shape of `LEZIONI.md` §1.9 rule 4.
    a.fasi_indipendenti = prof["idle_lungo"] != prof["idle_corto"]
    a.reg.apri_giro(
        "B6", "the client KEEPS QUIET: no RCP byte after the message that brings "
              "to the state.  Acknowledgements and transport PINGs are not the scene, "
              "and are declared (§4.6)",
        extra={"fase": a.fase, "idle_chiesto": a.idle,
               "idle_nostro_ms": int(a.idle_nostro * 1000),
               "casi": len(casi), "casi_totali": len(CASI),
               "tetti_documento": dict(TETTI_DOC),
               "tetti_codice": tetti_codice,
               "fasi_indipendenti": a.fasi_indipendenti})
    print(f"   ⛔ TARGET: {a.bersaglio} · port {a.porta} · binary md5 "
          f"{(a.md5 or 'unknown')[:12]}…")
    print(f"   this run's log: {a.uscita or '⛔ NONE'}")
    if not a.fasi_indipendenti:
        print(f"   {GIALLO}⛔ ON THIS TARGET THE TWO PHASES ARE NOT "
              f"INDEPENDENT{GRIGIO}")
        print(f"      The transport cap does not move ({prof['idle_lungo']}"
              f" ms, IDLE_MS in src/trasporto.c),")
        print(f"      so «credenziali-tetto» (phase sani) and "
              f"«credenziali-tetto-sotto-il-trasporto» (phase ping)")
        print(f"      measure THE SAME THING: 30 s of transport under 60 s of "
              f"protocol.")
        print(f"      ⚠ CIAO (5 s) and ATTACCA (10 s) stay clean — 30 > 10.")
        print(f"      ⛔ Counting them as two confirmations would be counting the "
              f"same measurement twice.")
    print(f"   transport inactivity cap in force, READ FROM THE PEER: "
          f"{a.idle} ms")
    print(f"   inactivity cap announced by us: "
          f"{a.idle_nostro * 1000:.0f} ms — ⛔ and aioquic's default "
          f"would be 60 000 ms,")
    print(f"   that is exactly the cap to measure: here it is chosen on purpose "
          f"(see IDLE_SANI in the file)\n")

    # ── THE THREE NUMBERS, BEFORE MEASURING ────────────────────────────────
    print("   ⛔ the three numbers this bench compares:")
    disaccordo_doc_codice = []
    for n in ("CIAO", "CREDENZIALI", "ATTACCA"):
        c = tetti_codice.get(n)
        if c is None:
            print(f"      {n:12s} document {TETTI_DOC[n]:6d} ms · code "
                  f"{GIALLO}not declared{GRIGIO} (--tetti-codice missing: "
                  f"the comparison is NOT done)")
        elif c != TETTI_DOC[n]:
            print(f"      {n:12s} document {TETTI_DOC[n]:6d} ms · code "
                  f"{ROSSO}{c} ms — ⛔ THEY DO NOT MATCH{GRIGIO}")
            disaccordo_doc_codice.append(n)
        else:
            print(f"      {n:12s} document {TETTI_DOC[n]:6d} ms · code "
                  f"{c} ms · they match")
    if "ATTACCA" in tetti_codice:
        print(f"      ⚠ `TETTO_ATTACCA` was brought from 60 000 to 10 000 ms "
              f"on 10 Aug 2026 (R9.9)")
        print(f"        on the sole reading of §4.6, without measurement: this bench "
              f"is its first witness")
    print()

    conti = {
        "certifications of the tool": [0, 0],
        "caps expired with TEMPO_SCADUTO": [0, 0],
        "caps expired IN THE RIGHT TIME (§4.6)": [0, 0],
        "§3.1 point 3 — 0x0D in the WT closing": [0, 0],
        "⭐ the cap does NOT trigger before": [0, 0],
        "B0.5 — the server still alive after every case": [0, 0],
        "⛔ document and code agree": [0, 0],
    }
    for n in ("CIAO", "CREDENZIALI", "ATTACCA"):
        if n in tetti_codice:
            conti["⛔ document and code agree"][1] += 1
            conti["⛔ document and code agree"][0] += int(
                tetti_codice[n] == TETTI_DOC[n])

    guasti, risposte = 0, []

    # ── THE CERTIFICATIONS ─────────────────────────────────────────────────
    print("== ⛔ The certifications of the tool, BEFORE measuring")
    print("   (REVIEWER.md §1.2: a negative outcome with an uncertified "
          "tool is ambiguous)")

    ok, testo, bloccato, ms_fisso = await cert_giro_completo(a)
    conti["certifications of the tool"][1] += 1
    conti["certifications of the tool"][0] += int(ok)
    riga(ok, "cert-giro-completo", testo)
    if bloccato:
        print(f"\n    {ROSSO}⛔ THE ADDRESS IS BANNED (§4.4-bis) — B0.3{GRIGIO}")
        print("       Three failed authentications from this address, and")
        print("       another bench (B5, B8) did them shortly before: the ban lasts")
        print("       ⛔ TWELVE HOURS, not thirty seconds.")
        print("       ⛔ It is not a defect of the caps, and it is precisely the")
        print("          false red B0.3 exists to prevent.")
        print("       ⛔ The cures, and now there are TWO — ⚠ this line said that")
        print("          the first «does not exist»: it was true when it was")
        print("          written and stopped being so within an hour,")
        print("          that is it was form E5 (a fact that was a deduction")
        print("          never re-verified):")
        print("          · ⭐ the unblock command of §4.4-bis EXISTS:")
        print("            `01-b8-sblocca.py` speaks a 0600 Unix socket and says")
        print("            TOLTO / NON-BANNATO / «I talked to nobody».")
        print("            `01-b6-lancia.sh` calls it BEFORE the run, and")
        print("            declares it (B0.3);")
        print("          · **restarting the server** — ⛔ and on this target")
        print("            it is NO LONGER ENOUGH: the product's ban is on FILE and")
        print("            survives the restart (invariant I7).  Restarting")
        print("            resets the count in memory, not the ban on disk.")
        print("       ⚠ So if this line lights up against the product, the")
        print("         ban comes from the file — and B6's file is thrown away by the launch")
        print("         script at the start: look at who else writes there.")
        return 5
    if not ok:
        print(f"\n    {ROSSO}⛔ the tool does not get to the end of a handshake "
              f"that succeeds: the caps are not measured{GRIGIO}")
        return 4

    # ⭐ The stopwatch, on a KNOWN wait: the fixed second of §4.4-bis.
    ok_cr = ms_fisso is not None and 1000 <= ms_fisso <= 3000
    conti["certifications of the tool"][1] += 1
    conti["certifications of the tool"][0] += int(ok_cr)
    riga(ok_cr, "cert-cronometro",
         (f"the fixed second of §4.4-bis measured {ms_fisso:.0f} ms "
          f"(B3: 1074-1085 ms)" if ms_fisso is not None
          else "⛔ not measured: without a known wait the stopwatch is not "
               "certified"))
    if not ok_cr:
        guasti += 1

    ok_cn, testo_cn, ms_cn = await cert_congedo_noto(a)
    conti["certifications of the tool"][1] += 1
    conti["certifications of the tool"][0] += int(ok_cn)
    riga(ok_cn, "cert-congedo-noto", testo_cn)
    if not ok_cn:
        print(f"\n    {ROSSO}⛔ the tool cannot read a KNOWN farewell "
              f"by the two roads of §3.1{GRIGIO}")
        print("       Every «no farewell arrived» that follows would be")
        print("       ambiguous between the server and the bench: it is not measured.")
        return 4

    if a.fase == "ping":
        ok_ms, testo_ms, ms_ms = await cert_morte_silenziosa(a, a.idle)
        conti["certifications of the tool"][1] += 1
        conti["certifications of the tool"][0] += int(ok_ms)
        riga(ok_ms, "cert-morte-silenziosa", testo_ms)
        if ms_ms is not None:
            print(f"        ⚠ dead after {ms_ms / 1000:.1f} s, and the transport "
                  f"cap is {a.idle / 1000:.0f} s")
        if not ok_ms:
            print(f"\n    {ROSSO}⛔ the tool cannot see a death without a "
                  f"reason: the diagnosis «the PINGs are missing» cannot be produced"
                  f"{GRIGIO}")
            return 4

    # ── THE CASES ──────────────────────────────────────────────────────────
    print(f"\n== The cases")
    for c in casi:
        es = Attesa(c["nome"])
        try:
            await c["f"](a, es)
        except Exception as e:  # noqa: BLE001 — the error type IS the measurement
            es.errore = f"{type(e).__name__}: {e}"

        tetto_ms = TETTI_DOC[c["tetto"]] if c["tetto"] else None

        if c["atteso"] is None:
            # ⭐ The check that says NO: the cap does not trigger before.
            conti["⭐ the cap does NOT trigger before"][1] += 1
            ok = es.pronto and es.esito == "servito" and es.errore is None
            conti["⭐ the cap does NOT trigger before"][0] += int(ok)
            riga(ok, c["nome"],
                 (f"served after {tetto_ms * 0.7 / 1000:.1f} s of silence "
                  f"(cap {tetto_ms / 1000:.0f} s)") if ok else str(es))
            if not ok:
                guasti += 1
                print(f"        expected: ⭐ no drop — {c['spiega']}")

        elif c["atteso"] == "risposta":
            # ⛔ It is not a pass/fail: it is an open question, and the
            #    answer is a number.  The comparison is done by the bench (B0.4),
            #    but the verdict is on a line of its own.
            if not es.pronto:
                riga(False, c["nome"], str(es))
                guasti += 1
                print(f"        ⛔ the case never got to the state it "
                      f"had to measure: it is not a failed test, it is a "
                      f"test not done")
            else:
                # ⛔ «Something happened» has TWO roads, and in one of these
                #    cases the first does not exist: without a control channel
                #    the `CONGEDO` has nowhere to go (§3.1 point 2 is precisely
                #    conditional on that), and what remains is the closing of
                #    the session with the reason code (§3.1 point 3).  Counting
                #    only the `CONGEDO` would give «nothing happened» to a server
                #    that did all it could do.
                per_congedo = es.esito == "congedo" and es.motivo is not None
                per_chiusura = es.codice_wt is not None
                motivo_visto = es.motivo if per_congedo else es.codice_wt
                strada = ("CONGEDO" if per_congedo else
                          "session closing" if per_chiusura else "")
                if (per_congedo or per_chiusura) and es.ms is not None:
                    if motivo_visto != TEMPO_SCADUTO:
                        risp = (f"⛔ {motivo_visto:#04x}="
                                f"{MOTIVI.get(motivo_visto, '?')} arrived instead of "
                                f"TEMPO_SCADUTO, after {es.ms / 1000:.2f} s: "
                                f"it is not a cap, it is something else")
                        verso = "?"
                        guasti += 1
                    elif es.ms < 1500:
                        risp = (f"the stopwatch starts from the END OF TLS: "
                                f"TEMPO_SCADUTO by {strada} after "
                                f"{es.ms / 1000:.2f} s, that is with the budget already "
                                f"consumed")
                        verso = "TLS"
                    else:
                        risp = (f"the stopwatch starts from the OPENING (session or "
                                f"channel): TEMPO_SCADUTO by {strada} after "
                                f"{es.ms / 1000:.2f} s")
                        verso = "APERTURA"
                elif es.esito == "niente":
                    risp = (f"⛔ NOTHING happened in "
                            f"{es.ms / 1000:.0f} s: in this state the "
                            f"stopwatch does not start at all, and the connection "
                            f"stays there hanging")
                    verso = "MAI"
                # ⛔ THE SILENT DEATH IS A SERVER RED, NOT AN ANSWER ABOUT THE
                #    DOCUMENT — finding R12-A.25.
                #
                #    Until 11 Aug 2026 `esito == "morte-silenziosa"` — which
                #    is **the exact signature of the missing PING**, the one
                #    the «ping» phase exists for — fell into the `else` below,
                #    did not increment `guasti`, ended up in `risposte` with
                #    `verso="?"`, and then `fuori_dal_documento` collected it
                #    and the script exited **3**, printing «the caps behave as
                #    the CODE says, but §4.6 says something else … the cure is
                #    in RCP.md, not in the server».  ⛔ That is, the symptom that
                #    accuses the SERVER was handed over as proof that the
                #    DOCUMENT is wrong: the red sent off to look where there is
                #    nothing.  The yellow branch of the bench below (lines
                #    1190-1195) already said it well for the other cases; here not.
                elif es.esito == "morte-silenziosa":
                    risp = (f"⛔ DIED WITHOUT A REASON after "
                            f"{es.ms / 1000:.1f} s, and the transport cap "
                            f"is {a.idle / 1000:.0f} s: it is the signature §4.6 "
                            f"describes — the transport PINGs are not there, and "
                            f"QUIC is the one closing.  ⛔ The cure is IN THE SERVER")
                    verso = "SERVER"
                else:
                    # ⛔ AND WHAT THE BENCH COULD NOT CLASSIFY HAS A NAME OF ITS
                    #    OWN, and it is not an answer.  An outcome without a name
                    #    handed over as «a number to bring into the documents» is
                    #    an «I do not know» disguised as a measurement: the branch
                    #    that decides between «cure in the document» and «cure in
                    #    the server» cannot be the one without an «I do not know».
                    risp = (f"⛔ outcome the bench CANNOT CLASSIFY: {es}. "
                            f"It is not an answer to §4.6, and it is not a server "
                            f"red: it is a measurement to redo")
                    verso = "NON-SO"
                # ⛔ AND THE THREE THINGS ARE PRINTED IN THREE DIFFERENT WAYS,
                #    because they are three: a server red is a red (`riga`), an
                #    answer is yellow (`riga_gialla`), an «I do not know» is
                #    yellow but **does not go among the answers**.
                if verso == "SERVER":
                    guasti += 1
                    riga(False, c["nome"], risp)
                else:
                    riga_gialla(c["nome"], risp)
                risposte.append((c["nome"], verso, risp))

        else:
            # The real caps.
            #
            # ⛔⭐ AND A LINE IN WHICH THE FAREWELL IS NOT ENFORCEABLE — §4.6 line 4.
            #
            #     The «CANALE» cap expires when the control channel was never
            #     opened: ⛔ there is nowhere to send a `CONGEDO`, and
            #     `DECISIONI.md` §7.15 — decided on 11 Aug 2026 — says that
            #     there the obligation FALLS.  Demanding it here would mean
            #     giving red to a server that does exactly what the document
            #     requires of it, which is the most expensive defect shape of
            #     this project (finding R3.3, already paid for on B5 and B11).
            #
            # ⭐ What stays enforceable is the SECOND road of §3.1 point 3
            #    — the reason in the session closing code — and it is checked
            #    below by `ok_wt`, with no discounts.  ⚠ That is, this case does
            #    not test less: it tests the road that the decisions of 11
            #    August make the only one that always arrives.
            congedo_esigibile = c["tetto"] != "CANALE"
            conti["caps expired with TEMPO_SCADUTO"][1] += 1
            if congedo_esigibile:
                ok_motivo = (es.motivo == c["atteso"]
                             and es.tipo_motivo == "CONGEDO")
            else:
                ok_motivo = es.codice_wt == c["atteso"]
            if not es.pronto:
                ok_motivo = False
            conti["caps expired with TEMPO_SCADUTO"][0] += int(ok_motivo)

            conti["caps expired IN THE RIGHT TIME (§4.6)"][1] += 1
            # ⛔ «In the right time» holds only on a CONGEDO: the wait window
            #    lasts longer than the cap, so a «nothing» carries with it a big
            #    number that is not an expiry time.  Without this condition a
            #    case in which nothing happens could fall inside the tolerance
            #    of ANOTHER cap and print a green — form E8, «nothing» taking
            #    on the look of a datum.
            # ⚠ And with the channel never opened the outcome is NOT «congedo»:
            #   it is «sessione-chiusa», which here is the right thing and not a
            #   fallback.
            esiti_buoni = ("congedo",) if congedo_esigibile \
                else ("congedo", "sessione-chiusa")
            ok_tempo = (es.esito in esiti_buoni and es.ms is not None
                        and es.pronto and dentro_tolleranza(es.ms, tetto_ms))
            conti["caps expired IN THE RIGHT TIME (§4.6)"][0] += int(ok_tempo)

            conti["§3.1 point 3 — 0x0D in the WT closing"][1] += 1
            ok_wt = es.codice_wt == c["atteso"]
            conti["§3.1 point 3 — 0x0D in the WT closing"][0] += int(ok_wt)

            ok = ok_motivo and ok_tempo and ok_wt
            riga(ok, c["nome"], str(es))
            if not ok:
                guasti += 1
                print(f"        expected: {c['atteso']:#04x} "
                      f"{MOTIVI.get(c['atteso'], '?')} at "
                      f"{tetto_ms / 1000:.0f} s "
                      f"(tolerance -{TOLL_GIU / 1000:.1f} / "
                      f"+{TOLL_SU / 1000:.1f} s)")
                print(f"        {c['spiega']}")
                if not es.pronto:
                    print(f"        ⛔ and the case NEVER GOT to the state "
                          f"to measure: it is not a failed test, it is a test "
                          f"not done")
                elif es.esito == "morte-silenziosa":
                    print(f"        ⛔ DIED WITHOUT A REASON after "
                          f"{es.ms / 1000:.1f} s, and the transport cap is "
                          f"{a.idle / 1000:.0f} s:")
                    print(f"           it is the signature §4.6 describes — the "
                          f"transport PINGs are not there, and QUIC is the one closing")
                elif es.esito == "niente":
                    print(f"        ⛔ NOTHING HAPPENED for "
                          f"{es.ms / 1000 if es.ms else 0:.0f} s: the cap did not "
                          f"expire, and the connection stays there hanging")
                elif es.ms is not None and not ok_tempo:
                    altri = [n for n, v in TETTI_DOC.items()
                             if dentro_tolleranza(es.ms, v)]
                    if altri:
                        print(f"        ⚠ the {es.ms / 1000:.1f} s measured "
                              f"match instead the cap of «{altri[0]}» "
                              f"({TETTI_DOC[altri[0]] / 1000:.0f} s):")
                        print(f"           it is the shape of the defect copied "
                              f"from the previous line (R9.9)")
            if es.dettaglio:
                print(f"        detail from the body: «{es.dettaglio}»")

        # ⛔ The fact goes into the log, and it carries the target: a number
        #    without the name of the server that produced it is a number of two
        #    different things put in a row.
        a.reg.scrivi({"tipo": "caso", "nome": c["nome"], "fase": c["fase"],
                      "tetto": c["tetto"], "atteso": c["atteso"],
                      "ms": es.ms, "esito": es.esito, "motivo": es.motivo,
                      "tipo_motivo": es.tipo_motivo, "codice_wt": es.codice_wt,
                      "pronto": es.pronto, "fase_raggiunta": es.fase,
                      "errore": es.errore,
                      "tetto_documento_ms": tetto_ms,
                      # ⛔ And the line says whether this measurement was CLEAN: on
                      #    the product the credentials case in the «sani» phase is
                      #    not, because the transport cap is below.
                      "pulita": bool(a.fasi_indipendenti
                                     or c["tetto"] != "CREDENZIALI")})

        # ⛔ B0.5, after EVERY case.
        conti["B0.5 — the server still alive after every case"][1] += 1
        vivo, perche = await ancora_vivo(a)
        conti["B0.5 — the server still alive after every case"][0] += int(vivo)
        if not vivo:
            riga(False, "", f"⛔ THE SERVER NO LONGER ANSWERS after "
                            f"«{c['nome']}»: {perche}")
            guasti += 1
            print(f"\n    {ROSSO}⛔ the bench stops: without a server there "
                  f"is nothing to measure{GRIGIO}")
            break

    # ── THE OUTCOME ────────────────────────────────────────────────────────
    print()
    print("    == what this run really looked at")
    for che, (buoni, tot) in conti.items():
        if tot == 0:
            # ⛔ A zero denominator is DECLARED: «nobody looked» and «all
            #    passed» look the same if one keeps quiet.
            print(f"    --  {che:46s} no case triggered it")
            continue
        col = VERDE if buoni == tot else ROSSO
        print(f"    {col}{buoni:3d} out of {tot:3d}{GRIGIO}  {che}")

    # ⛔ AND THE ANSWERS ARE SEPARATED FROM THE «I DO NOT KNOW» — finding R12-A.25.
    #    An outcome the bench could not classify is not «a number to bring into
    #    the documents»: it is a measurement to redo, and printing it in the same
    #    list as the answers made it weigh like an answer.
    non_classificati = [r for r in risposte if r[1] == "NON-SO"]
    risposte_vere = [r for r in risposte if r[1] not in ("NON-SO", "SERVER")]
    if risposte_vere:
        print()
        print("    == ⛔ the open questions this run has ANSWERED")
        print("       (they are not pass/fail: they are numbers to bring into the "
               "documents)")
        for nome, verso, risp in risposte_vere:
            print(f"    ??  {nome:34s} {risp}")
    if non_classificati:
        print()
        print(f"    == ⛔ and {len(non_classificati)} cases the bench COULD NOT "
              f"CLASSIFY")
        print("       ⚠ They do not go among the answers: an «I do not know» handed over "
              "as an answer")
        print("         would send the cure to the wrong place.")
        for nome, _, risp in non_classificati:
            print(f"    ?!  {nome:34s} {risp}")

    # ⛔ THREE DIFFERENT OUTCOMES, BECAUSE THEY ARE THREE DIFFERENT THINGS — and it
    #    is the point of this bench.
    #
    #      1  the SERVER does not respect §4.6;
    #      3  the server does what the CODE says, but the DOCUMENT says
    #         something else: the cure is in the document;
    #      0  document, code and wire say the same thing.
    print()
    # ⛔ And the verdict goes into the log with the target inside, or in six months
    #    «the three caps expire with the right reason» will not say on which
    #    server.  ⚠ It is exactly what happened to the three numbers of 10 August
    #    — 5.0 · 60.1 · 10.0 s — which have no log and cannot be re-verified.
    a.reg.scrivi({"tipo": "verdetto", "fase": a.fase, "guasti": guasti,
                  "risposte": [[n_, v_, r_] for n_, v_, r_ in risposte],
                  "fasi_indipendenti": a.fasi_indipendenti,
                  "conti": {k: v for k, v in conti.items()}})
    print(f"    --  {a.reg.riassunto()}")
    if guasti:
        print(f"    {ROSSO}⛔ B6 «{a.fase}» against «{a.bersaglio}»: {guasti} "
              f"points do not pass{GRIGIO}")
        return 1

    # ⛔ AND THE LIST IS BY ALLOWED NAMES, NOT BY EXCLUSION — finding R12-A.25.
    #    It was `[r for r in risposte if r[1] != "TLS"]`: any new `verso`
    #    — including the `"?"` the bench put when it had not understood —
    #    automatically ended up among the proofs that the DOCUMENT is wrong.  A
    #    list by exclusion grows by itself every time someone adds a case, and
    #    in the direction that accuses the document.
    fuori_dal_documento = [r for r in risposte if r[1] in ("APERTURA", "MAI")]
    if disaccordo_doc_codice:
        print(f"    {ROSSO}⛔ B6 «{a.fase}»: the wire behaves well, but "
              f"DOCUMENT and CODE do not say the same number{GRIGIO}")
        for n in disaccordo_doc_codice:
            print(f"       {n}: §4.6 says {TETTI_DOC[n]} ms, "
                  f"`banchi/rcp/rcp.c` says {tetti_codice[n]} ms")
        print("       ⛔ The cure is not choosing: it is that one of the two gets "
              "updated, with the date and the source (CODER.md §5).")
        return 3
    if fuori_dal_documento:
        print(f"    {GIALLO}⛔ B6 «{a.fase}»: the caps behave as the "
              f"CODE says, but §4.6 line 1 says something else{GRIGIO}")
        for nome, verso, risp in fuori_dal_documento:
            print(f"       {nome}: {risp}")
        print("       §4.6 says «TLS handshake finished», and the stopwatch "
              "starts from another instant.")
        print("       ⛔ It is the `[?]` R3.27, and now it has a measurement: «§4.6 "
              "changes by one word»,")
        print("          or the stopwatch changes instant.  It is not the server's "
              "red.")

        # ⛔ AND THE TWO ANSWERS ARE NOT THE SAME, AND THE SECOND IS MORE SERIOUS.
        #
        #    «APERTURA» says which word to change.  «MAI» says that **changing
        #    the word is not enough**: if the stopwatch starts from the opening of
        #    the channel, an open WebTransport session and a channel never opened
        #    have NO cap on them — that is precisely the connection that §4.6
        #    exists not to leave hanging, surviving the cure.  A bench that
        #    printed a single line for the two answers would hand over the easy
        #    half.
        mai = [r for r in risposte if r[1] == "MAI"]
        if mai:
            print()
            print(f"    {ROSSO}⛔ AND THE SECOND ANSWER, WHICH CHANGING THE WORD "
                  f"DOES NOT CLOSE{GRIGIO}")
            for nome, _, risp in mai:
                print(f"       {nome}: {risp}")
            print("       If the stopwatch starts from the opening of the CHANNEL, whoever")
            print("       opens the session and never opens the channel has no")
            print("       cap on them: it is the connection that «holds a")
            print("       place and declares it to nobody» (§4.6, first line")
            print("       of the box), alive and without expiry.")
            print("       ⛔ §4.6 has no line for this state: the table")
            print("          starts from «CIAO received», and before the CIAO there is")
            print("          a state in which the server counts nothing.")
        return 3
    # ⛔ AND THE «I DO NOT KNOW» HAS AN OUTCOME OF ITS OWN, 6 — finding R12-A.25.
    #    It is not 1 («the server is wrong») and it is not 3 («the document is
    #    wrong»): they are the two things between which the bench could not
    #    choose, and choosing one at random is the red sent where there is nothing.
    if non_classificati:
        print(f"    {GIALLO}⛔ B6 «{a.fase}»: {len(non_classificati)} cases "
              f"produced an outcome the bench cannot classify"
              f"{GRIGIO}")
        print("       It is not a server red and it is not a document "
              "red: it is a")
        print("       measurement to redo, and as long as it stays so B6 has not "
              "answered R3.27.")
        return 6
    print(f"    {VERDE}⭐ B6 «{a.fase}» passes, and the numbers above say on "
          f"what{GRIGIO}")
    return 0


# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD MUST NOT GO THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 Aug 2026.
#
# ⛔ `--parola` ends up in the process `argv`, that is in `/proc/<pid>/cmdline`,
#    which on Linux is **readable by anyone**: a `ps` launched by another user
#    during the run prints it in full.
#
# ⭐ The good road already existed in the house and this is its extension, not a
#    second way: `01-b10-secondo-utente.py` takes `--parola-file`, a `0600` file
#    that the launcher writes with `printf` — a shell **builtin**, so not even
#    the writing goes through a process with the password in `argv` — and
#    deletes with a `trap`.
#
# ⚠ And `--parola` was NOT removed, and not out of laziness: some callers not
#   yet cured still pass it, and breaking them **silently** would be worse than
#   the defect.  ⛔ But the fallback is DECLARED (`CODER.md` §4.2): a silent
#   fallback produces two behaviours under the same label, which is form
#   **E2** — and here the two behaviours are «the secret is protected» and
#   «the secret is public».  ⇒ whoever passes `--parola` gets told.
#
# ⚠ And the warning looks at `sys.argv`, not at the value: the default written
#   in the code is in no command line, and telling it otherwise would be an
#   alarm one learns to ignore.
def parola_dagli_argomenti(a):
    """The password: from `--parola-file` if present, from `--parola` otherwise.

    ⛔ And the three ways of failing are told apart: «cannot be read», «is
    readable by others» and «is empty» have three different cures, and an empty
    file is NOT an empty password — it is «the launcher did not write it»
    (`LEZIONI.md` §1.9).
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
        print("     COMMAND LINE: it is in `/proc/<pid>/cmdline` and anyone who")
        print("     runs `ps` on this machine sees it.  The run goes on — the caller")
        print("     has not been cured — but it is not a private run.")
        print("     ⭐ The cure: `--parola-file <0600 file>`, as in B10.")
    return a.parola


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="B6 — the three caps of the handshake (RCP.md §4.6)")
    p.add_argument("--indirizzo", default="192.168.0.2")
    # ⛔ No default that names a target: 7447 is the graft and 7448
    #    the product.  It is passed by `01-b0-bersaglio.sh`.
    p.add_argument("--porta", type=int, default=0)
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="parola-di-prova")
    # ⛔ D12: the road that does NOT go through `ps`.  It wins over `--parola` if
    #    both are there — a file written on purpose is always more recent than a
    #    default.
    p.add_argument("--parola-file", default="",
                   help="0600 file with only the password (⭐ D12: this way "
                        "it does not end up in `ps`)")
    p.add_argument("--fase", default="sani", choices=["sani", "ping"],
                   help="sani = wide transport · ping = transport shorter "
                        "than the protocol cap")
    p.add_argument("--idle", type=int, default=120000,
                   help="the transport inactivity cap IN FORCE, read "
                        "from the peer by 01-b6-lancia.sh — needed for the diagnoses")
    p.add_argument("--tetti-codice", default="",
                   help="CIAO=5000,CREDENZIALI=60000,ATTACCA=10000 — the "
                        "#define read from banchi/rcp/rcp.c")
    p.add_argument("--solo", default="",
                   help="run only the cases that contain this")
    b0.aggiungi_argomenti(p)
    p.add_argument("--elenco", action="store_true",
                   help="print the predictions without measuring")
    a = p.parse_args()
    a.parola = parola_dagli_argomenti(a)
    sys.exit(asyncio.run(principale(a)))
