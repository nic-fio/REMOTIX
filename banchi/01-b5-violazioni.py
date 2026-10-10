#!/usr/bin/env python3
"""01-b5-violazioni.py — ⛔ B5: strictness towards the server, tested by violating it.

    python3 01-b5-violazioni.py --indirizzo 192.168.0.2 --porta 7447
    python3 01-b5-violazioni.py --solo tela-1921          (a single case)
    python3 01-b5-violazioni.py --elenco                  (the predictions, without measuring)

⚠ It runs INSIDE the container: aioquic lives there.

===========================================================================
⛔ WHY THIS BENCH EXISTS

`RCP.md` §3 is the **strictness rule**: what is not understood is not ignored,
the connection drops, with the reason.  ⭐ But a strictness rule **is not tested
by doing the right things**: a server that checks nothing passes all the B3
benches and falls only the day someone sends it a crooked byte — and that day
there is no bench watching.

⛔ *A bench that does not try to violate the protocol does not test the protocol.*

===========================================================================
⛔ THE FIVE THINGS EVERY CASE VERIFIES, AND THE LAST TWO GET FORGOTTEN

  1. ⛔ **that the violation REALLY left.**  A case whose *preparation* fails —
     the fixed `ATTACCA` refused, the `ECCOMI` that does not arrive — has tested
     nothing, and as long as the reason was scraped from the exception text it
     became **green** precisely because of that (finding R7.1).  Here every
     case carries `provocato`, and without it it is red;
  2. **the right reason**, read FROM THE RECEIVING SIDE (§8.1) — not from the
     server log, which is the same hand that wrote the code, and ⛔ **not from
     the text of an exception**: `raccogli` takes it from a message that arrived
     on the wire, or does not take it;
  3. ⛔ **in which MESSAGE** it arrived.  §11 says it in full:
     `CREDENZIALI_ERRATE` and `TROPPI_TENTATIVI` travel in `RESPINTO`, all the
     others in `CONGEDO`, and §4.4 forbids sending both.  They are **two
     different state machines** — after `RESPINTO` the client cannot retry —
     and counting them under the same label is form E3 (finding R7.9);
  4. **the two roads of §3.1**, and ⛔ **they are not optional in the same way**:
     **point 2** (the `CONGEDO`) is conditional — *«if the control channel is
     still usable»* — **point 3** (the reason code in the closing of the
     WebTransport session) is an **unconditional MUST**, and it is the one §3.1
     calls *«the one that saves the diagnoses»*.
     ⚠ Finding R3.3 said that always demanding both would give red on the
     right code: it holds for point 2, **not** for point 3, and having swapped
     them had made optional precisely the last foothold (finding R7.3).
     Here point 3 is **counted**, with its denominator, instead of being
     printed;
  5. ⛔ **and that the server is still there afterwards** (B0.5).  A server
     killed by the kernel *«drops the connection»* exactly like one that says
     farewell — and it takes away **all the other users' sessions**.  After every
     case a new connection is opened and it gets as far as `ECCOMI`: it is the
     half of the bench nobody writes, and it is the one that tells strictness
     from collapse.

===========================================================================
⭐ AND THE CASES THAT MUST PASS

The cases with `atteso = None` are ⭐ **expected greens**, and they are not
filler: they are the control that says *no* to «this server closes everything».

  nome-con-trattino-basso    `video.misura_massima`: the `_` is LAWFUL (§4.3)
  capacita-sconosciuta       a NAME that does not exist is ignored (§3, exception 1)
  hevc-e-vp9                 an unknown entry INSIDE a list is DISCARDED
  vista-300x801              the view does not have the canvas constraints (§7.1, R4.10)
  vista-1x1                  likewise, at the limit
  disposizione-con-variante  `de(neo)`: the variant in parentheses is lawful
  banco-spento               ⛔ `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)`, not
                             a closing and not a silence (§7.5 rule 2)
  banco-ritardo-20000        `RITARDO_FUORI_LIMITI`, and the session STAYS OPEN

⛔ **AND HOW MANY THERE ARE IS NOT WRITTEN HERE.**  The number is counted by
`conta()` and printed by `--elenco` and by the final line, each with its
denominator.  A number written by hand in a comment is the number nobody
recomputes: finding R7.14 found **three** of them — «five cases in here»,
«thirty-five greens out of thirty-five», «44 violations out of 44» — and **none
of the three matched the file**.  ⚠ The third, what is more, counted among the
violations also the cases that MUST pass, on which «the right reason every
time» is false by construction: on those no reason must arrive.

===========================================================================
⛔ WHAT THIS BENCH DOES NOT TEST, AND IT MUST BE SAID — finding R7.8

`RCP.md` §3 declares **five** exceptions to the strictness rule and says that
«outside this list none are invented».  Here **one** is tested: the first, with
`capacita-sconosciuta` and `hevc-e-vp9`.  The other four are **tolerances** —
places where the server MUST *not* close — and a server that closed at every
surprise would pass this bench in full.

| exception of §3 | the missing case | why it is not here |
|---|---|---|
| 2 (§6.3) | a 4-byte datagram, or one with `tipo` != `0x0401`, is **discarded** | audio does not exist before **phase 7** |
| 3 (§7.1) | the **grace second** on the old coordinates after `TELA(ADATTATA)` | `ADATTA_TELA` and input do not exist before **phase 6** |
| 4 (§7.1) | a size **out of bounds** in `ADATTA_TELA` → `TELA(RIFIUTATA, MISURA_FUORI_LIMITI)` **with the session still open** | ⭐ **no longer true since 15 Aug 2026**: `ADATTA_TELA` is served, and the case is tested by `banchi/04-b31-tela.c` (cases 5 and 17). ⚠ And the example that was here — `1921×1081` — **was wrong**: it is WITHIN the limits of §4.5 and odd, so it is truncated to `1920×1080` and granted. Out of bounds is, for example, `1600×230` (the minimum height is 240) |
| 5 (§5.2, §7.4) | two `RICHIEDI_CHIAVE` less than 200 ms apart: the second **may be ignored** | `RICHIEDI_CHIAVE` does not exist before **phase 3** |

⚠ **Writing them here today would give red on a message nobody has written
yet**, that is on a rule the server never had the chance to apply — the
defect `01-b5-lancia.sh` declares it fears for the graft.  They go into the
benches of phases 3, 6 and 7, and this table is the place to pick them up
from.
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

# ⛔ The B3 client is IMPORTED, not copied.  Inside it is the line that
#    prevents it from handing the control-channel events to aioquic's HTTP/3
#    layer — without which the connection dies at the hand of the CLIENT (10
#    Aug 2026), and a diverging copy would bring that defect back in here
#    disguised as a server defect.
_spec = importlib.util.spec_from_file_location(
    "b3cliente", os.path.join(QUI, "01-b3-cliente.py"))
b3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(b3)

# ⛔ And the TARGET's profile, for the same reason: the differences between the
#    two servers are in a single file, and four benches read them instead of
#    discovering them all over again — or, worse, not discovering them and
#    giving red.
_spec_b0 = importlib.util.spec_from_file_location(
    "b0bersaglio", os.path.join(QUI, "01-b0-bersaglio.py"))
b0 = importlib.util.module_from_spec(_spec_b0)
_spec_b0.loader.exec_module(b0)

s, inquadra, MOTIVI = b3.s, b3.inquadra, b3.MOTIVI

ERRORE_PROTOCOLLO = 0x0B
NIENTE_IN_COMUNE = 0x09
VERSIONE_INCOMPATIBILE = 0x0A
SESSIONE_NON_SERVIBILE = 0x0E
TROPPI_TENTATIVI = 0x08
CREDENZIALI_ERRATE = 0x07
CONGEDO, RESPINTO, BANCO_ESITO = 0x000C, 0x0005, 0x0010

# ⛔ IN WHICH MESSAGE THE REASON MUST ARRIVE — `RCP.md` §11, line «the
#    farewell»: «`CREDENZIALI_ERRATE` and `TROPPI_TENTATIVI` travel in
#    `RESPINTO`», all the others in `CONGEDO`, and §4.4 forbids following
#    `RESPINTO` with a `CONGEDO`.  ⚠ It is not a formality: after `RESPINTO` the
#    client MUST NOT retry on the same connection (§4.4), after a `CONGEDO` the
#    connection is simply over — two different state machines under the same
#    number (finding R7.9).
PORTATORE = {CREDENZIALI_ERRATE: "RESPINTO", TROPPI_TENTATIVI: "RESPINTO"}


class Cliente(b3.Cliente):
    """The B3 client, plus what is needed to violate (§2.5)."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        # ⛔ THE STREAMS THIS BENCH OPENS, and they must be kept away from
        #    aioquic's HTTP/3 layer: see `quic_event_received`.
        self.miei_stream = set()
        self.eco = {}

    def apri_uni(self):
        # aioquic writes by itself the header of the WebTransport
        # unidirectional stream: the type 0x54 and the session identifier.
        s_id = self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=True)
        self.miei_stream.add(s_id)
        return s_id

    def apri_bidi(self):
        s_id = self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=False)
        self.miei_stream.add(s_id)
        return s_id

    def manda_su(self, stream, dati, fine=False):
        self._quic.send_stream_data(stream, dati, end_stream=fine)
        self.transmit()

    def quic_event_received(self, event):
        # ⛔⭐ WHAT COMES BACK ON THE STREAMS WE OPENED MUST NOT BE GIVEN TO
        #     AIOQUIC — and it is a defect OF THE BENCH, measured `[M]` on 10
        #     Aug 2026 on the server log.
        #
        #     The case `secondo-bidirezionale` gave «chiusura-wt=(absent)»
        #     while the server did everything right.  The log, at lines
        #     32355-32359 of `b5-server.log`:
        #
        #       REMOTIX B5: ⛔ two bidirectional streams from the client inside
        #                     the session: control is 4, and 8 is one too many
        #       REMOTIX B3: congedo motivo=0x0b …
        #       REMOTIX B3: session closure DEFERRED, code 0x0b
        #                   (queued: 1; keep-alive at 100 ms …)
        #       frm tx … STREAM id=0x4 len=71   ← the CONGEDO
        #       frm tx … STREAM id=0x8 len=30   ← B2's echo on the extra stream
        #       frm rx … CONNECTION_CLOSE error_code=0x105
        #                reason=[DATA frame is not allowed in this state]
        #       ngtcp2_conn_read_pkt: ERR_DRAINING
        #
        # ⛔ The `CONNECTION_CLOSE` is RECEIVED by the server: it is the CLIENT
        #    that leaves, one packet after the `CONGEDO` and half a second
        #    before the five passes let the capsule mature.  Code 0x105 is
        #    aioquic's `H3_FRAME_UNEXPECTED`: the 30 bytes that came back on
        #    stream 8 ended up in `self._http.handle_event`, which knows nothing
        #    of a WebTransport stream opened by us and reads them as a `DATA`
        #    frame on a request stream.  ⚠ It is the same asymmetry already
        #    measured in `01-b3-cliente.py` — aioquic 1.2 can CREATE a
        #    WebTransport stream and cannot RECOGNISE it when it answers us —
        #    cured there for the control channel and never for the streams B5
        #    opens.
        #
        # ⭐ So the bench was measuring its own hurry, not the server: a real
        #    browser hands those bytes to the page and stays connected.
        #    Here they are discarded, DECLARING THEM (§3: no silent tolerance).
        if (type(event).__name__ == "StreamDataReceived"
                and event.stream_id in self.miei_stream):
            if event.data and event.stream_id not in self.eco:
                self.eco[event.stream_id] = len(event.data)
                print(f"   [wt]   ⚠ {len(event.data)} bytes came back from the server "
                      f"on stream {event.stream_id}, the one opened to "
                      f"violate: it is B2's echo on the bytes already in flight while "
                      f"the session drops.  The bench discards them without giving them "
                      f"to aioquic's HTTP/3 layer, which would kill the "
                      f"connection with 0x105 before the closing capsule")
            return
        super().quic_event_received(event)


# ---------------------------------------------------------------------------
# The bodies, written by hand because they go crooked on purpose.
def capacita(voci, versione=1):
    out = struct.pack("!HH", versione, len(voci))
    for n, v in voci:
        out += s(n) + s(v)
    return out


BUONE = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
         ("audio.codec", "opus,pcm"), ("client.nome", "banco-b5 0.1.0")]

# ⛔ `BUONE` without `client.nome`, for the cases that must violate **a single
#    rule** on that name.  `BUONE + [("client.nome", ...)]` carries `client.nome`
#    TWICE, and §4.3 gives two distinct reasons to close — the duplicate and
#    the value — so a server that implemented only the first gave green
#    without ever having looked at the length of a value (finding R7.6).
SENZA_NOME = [v for v in BUONE if v[0] != "client.nome"]


def ciao(voci=None, versione=1):
    return inquadra(0x0001, capacita(BUONE if voci is None else voci, versione))


def attacca(tl=1920, ta=1080, vl=1920, va=1080, disp="it"):
    return inquadra(0x0006, struct.pack("!IIII", tl, ta, vl, va) + s(disp))


def banco_marca(id_=1, colore=0x00FF0000, ritardo=0):
    return inquadra(0x000F, struct.pack("!III", id_, colore, ritardo))


async def banco_esito(cli, es, id_, esito, motivo):
    """⛔ §7.5: `BANCO_ESITO` is verified FIELD BY FIELD.

    A server that answered `BANCO_ESITO(ACCETTATA)` with the function off
    would pass a bench that only looks at «an answer arrived and the session
    holds» — and it would paint little squares on someone's desktop.
    """
    nome, corpo, _ = await b3.attendi(cli, None, attesa=6)
    if nome != "0x0010":
        raise RuntimeError(f"expected BANCO_ESITO, arrived {nome}")
    if len(corpo) < 14:
        raise RuntimeError(f"BANCO_ESITO of {len(corpo)} bytes: §7.5 wants 14")
    v_id, v_esito, v_motivo = struct.unpack("!IBB", corpo[:6])
    v_istante = struct.unpack("!Q", corpo[6:14])[0]
    es.banco = f"id={v_id} esito={v_esito} motivo={v_motivo} istante={v_istante}"
    if (v_id, v_esito, v_motivo) != (id_, esito, motivo):
        raise RuntimeError(
            f"BANCO_ESITO {es.banco}, expected id={id_} esito={esito} "
            f"motivo={motivo}")
    # ⛔ «`istante`: 0 if refused, and it is the only meaning of *absent*
    #    for this field» (§7.5, §6.0).
    if v_esito == 2 and v_istante != 0:
        raise RuntimeError(f"refused, but `istante` is {v_istante} and not 0")


# ---------------------------------------------------------------------------
class Esito:
    """What happened, from the receiving side."""

    def __init__(self):
        self.motivo = None        # from the CONGEDO / RESPINTO — NEVER deduced
        self.tipo_motivo = None   # ⛔ IN WHICH message it arrived (§11, §4.4)
        self.dettaglio = ""
        self.codice_wt = None     # from the closing of the session (§3.1 point 3)
        self.stato_http = None    # for the path case
        self.messaggi = []        # the types that arrived, in order
        self.viva = False         # the session is still open at the end
        # ⛔ Did the violation really leave?  See point 1 of the docstring:
        #    without this mark a case that falls in the PREPARATION counts as
        #    green (finding R7.1).
        self.provocato = False
        self.fase = "opening"     # where it stopped, if it stopped
        self.errore = None

    def __str__(self):
        p = []
        if self.stato_http and self.stato_http != "200":
            p.append(f":status={self.stato_http}")
        if not self.provocato:
            p.append(f"⛔ violation NEVER SENT (stopped in «{self.fase}»)")
        if self.motivo is not None:
            p.append(f"motivo={self.motivo:#04x}={MOTIVI.get(self.motivo, '?')}"
                     f" in {self.tipo_motivo}")
        elif self.tipo_motivo is not None:
            p.append(f"{self.tipo_motivo} without a readable reason")
        p.append("chiusura-wt=" + ("(absent)" if self.codice_wt is None
                                   else f"{self.codice_wt:#04x}"))
        if self.viva:
            p.append("session ALIVE")
        if self.errore:
            p.append(f"errore={self.errore}")
        return "  ".join(p) if p else "nothing"


async def raccogli(cli, es, attesa, grazia=1.5):
    """Waits for the farewell, or for the end of the wait if the session holds.

    ⛔ **This is the only place where `es.motivo` is written**, and it writes it
       from a message that arrived on the wire (§8.1: from the receiving side).
    """
    scadenza = asyncio.get_event_loop().time() + attesa
    while True:
        resta = scadenza - asyncio.get_event_loop().time()
        if resta <= 0:
            break
        try:
            m = await asyncio.wait_for(cli.messaggi.get(), timeout=resta)
        except asyncio.TimeoutError:
            break
        if m is None:
            break
        tipo, corpo, _ = m
        es.messaggi.append(tipo)
        if tipo in (CONGEDO, RESPINTO):
            # ⛔ It remembers WHICH of the two, because §4.4 and §11 tell them
            #    apart and the verdict asks for it (finding R7.9).
            es.tipo_motivo = "CONGEDO" if tipo == CONGEDO else "RESPINTO"
            # ⛔ And an EMPTY body is not «no reason»: §7.1 wants `u8
            #    motivo` (plus `stringa dettaglio` in the `CONGEDO`) and §3.1
            #    forbids code 0.  With `corpo[0] if corpo else None` a server that
            #    closes BADLY was easier to let through than one that closes
            #    well, because it left `motivo = None` (finding R7.2).
            if not corpo:
                es.errore = (f"{es.tipo_motivo} with an EMPTY body: §7.1 wants "
                             "at least the reason byte")
                break
            es.motivo = corpo[0]
            if tipo == CONGEDO and len(corpo) >= 3:
                n = struct.unpack("!H", corpo[1:3])[0]
                es.dettaglio = corpo[3:3 + n].decode("utf-8", "replace")
            break
        if tipo == BANCO_ESITO:
            break
    # ⛔ §3.1 POINT 3, AND WHY ONE WAITS.
    #
    #    The `CONGEDO` travels on the control channel, the closing of the
    #    session is a capsule on the session stream: they are two different
    #    roads and they arrive at two different moments.  Reading
    #    `codice_chiusura` at the exact instant the `CONGEDO` was read would
    #    measure «the second road did not arrive» every time the server sends
    #    it a millisecond later — that is it would measure our hurry.
    #    ⚠ The window is DECLARED and bounded: if it expires, the value stays
    #      `None` and the verdict counts it as missed, it does not hide it.
    if es.motivo is not None or es.errore is not None:
        fine = asyncio.get_event_loop().time() + grazia
        while (cli.codice_chiusura is None and not cli.finito
               and asyncio.get_event_loop().time() < fine):
            await asyncio.sleep(0.02)
    es.codice_wt = cli.codice_chiusura
    # ⛔ «Alive» means alive.  Before, it was enough that no reason had
    #    arrived, and a server that sent `ECCOMI` and then CLOSED the session
    #    without a farewell gave the line «the session holds» while it was dead
    #    (finding R7.2): the WebTransport closing and the `FIN` on the control
    #    channel enter the judgement, not only the printout.
    es.viva = (not cli.finito and es.motivo is None
               and es.codice_wt is None and es.errore is None)


async def apri(a, percorso="/rcp/1"):
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{a.indirizzo}:{a.porta}"
    gestore = connect(a.indirizzo, a.porta, configuration=conf,
                      create_protocol=Cliente)
    cli = await gestore.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    cli.apri_sessione(autorita, percorso)
    stato = await asyncio.wait_for(cli.accettata, timeout=8)
    return gestore, cli, stato


async def fino_a_eccomi(cli, corpo=None):
    cli.apri_controllo()
    cli.manda(corpo if corpo is not None else ciao())
    return await b3.attendi(cli, "ECCOMI")


async def fino_ad_ammesso(cli, a):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0003, s(a.utente) + s(a.parola)))
    return await b3.attendi(cli, "AMMESSO", attesa=20)


async def fino_a_sessione(cli, a):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca())
    return await b3.attendi(cli, "SESSIONE")


# ===========================================================================
# THE CASES.  ⛔ Each declares its EXPECTATION before measuring (§1.11): the
#             «expected» column is a PREDICTION written in the file, not a
#             comment on the result.
# ===========================================================================
CASI = []


def caso(nome, atteso, spiega, dove="prima"):
    def dec(f):
        CASI.append((nome, atteso, spiega, dove, f))
        return f
    return dec


# ── The framing (§6.1) ─────────────────────────────────────────────────────
@caso("tipo-sconosciuto", ERRORE_PROTOCOLLO,
      "a type that does not exist on the control channel: §3 forbids ignoring it")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x00FF, b""))


@caso("tipo-del-server", ERRORE_PROTOCOLLO,
      "ECCOMI sent BY THE CLIENT: known type, wrong direction (§7.1)")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0002, capacita(BUONE)))


@caso("lunghezza-in-piu", ERRORE_PROTOCOLLO,
      "a good CIAO with four bytes of padding at the end (§6.0: no "
      "padding)")
async def _(cli, a, es):
    corpo = capacita(BUONE) + b"\x00\x00\x00\x00"
    cli.apri_controllo()
    cli.manda(inquadra(0x0001, corpo))


@caso("lunghezza-in-meno", ERRORE_PROTOCOLLO,
      "a length shorter than the fields the type expects")
async def _(cli, a, es):
    corpo = capacita(BUONE)
    cli.apri_controllo()
    # half the body is declared, and only those bytes are sent: the list of
    # capabilities is truncated halfway through a string
    cli.manda(struct.pack("!HI", 0x0001, len(corpo) // 2) + corpo[:len(corpo) // 2])


@caso("lunghezza-4gib", ERRORE_PROTOCOLLO,
      "⛔ an announced length of 4 GiB: §6.1 forbids allocating before "
      "checking, and a server killed by the kernel «drops the connection» "
      "all the same — taking away everyone else's sessions (R3.3)")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(struct.pack("!HI", 0x0001, 0xFFFFFFFF))


@caso("lunghezza-oltre-1mib", ERRORE_PROTOCOLLO,
      "a message announcing more than 1 MiB (§6.1)")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(struct.pack("!HI", 0x0001, 2 * 1024 * 1024))


@caso("stato-sbagliato", ERRORE_PROTOCOLLO,
      "CREDENZIALI as the first message, before CIAO")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(inquadra(0x0003, s(a.utente) + s(a.parola)))


@caso("ciao-due-volte", ERRORE_PROTOCOLLO,
      "a second CIAO after ECCOMI: the same message, the wrong state")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(ciao())


# ── The version (§2.4, §9) ─────────────────────────────────────────────────
@caso("versione-2", VERSIONE_INCOMPATIBILE,
      "⛔ CIAO(versione=2) on /rcp/1: §2.4 says the two MUST coincide. "
      "⚠ §9 alone would say ECCOMI(1) — it is a contradiction of RCP.md")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(versione=2))


@caso("versione-0", VERSIONE_INCOMPATIBILE,
      "CIAO(versione=0) on /rcp/1: on the other side of the same boundary")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(versione=0))


# ── The capabilities (§4.3) ────────────────────────────────────────────────
@caso("nome-maiuscolo", ERRORE_PROTOCOLLO,
      "a capability name with capitals: §4.3 allows a-z 0-9 . _")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("Video.Codec", "hevc")]))


@caso("nome-65-byte", ERRORE_PROTOCOLLO,
      "a 65-byte name: the limit of §4.3 is 64")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("x" * 65, "si")]))


@caso("nome-con-trattino-basso", None,
      "⭐ `video.misura_massima`: the underscore is LAWFUL, and it is the "
      "contradiction the B4 validator found in §4.3 on 10 August")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("video.misura_massima", "3840x2160")]))
    await b3.attendi(cli, "ECCOMI")


@caso("valore-vuoto", ERRORE_PROTOCOLLO,
      "an empty value: «whoever has nothing to say does not send the capability».  "
      "⛔ ONE violation only: `client.nome` appears once and that is it")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(SENZA_NOME + [("client.nome", "")]))


@caso("valore-257-byte", ERRORE_PROTOCOLLO,
      "a 257-byte value: the limit of §4.3 is 256.  ⛔ ONE violation "
      "only, for the same reason as the case above")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(SENZA_NOME + [("client.nome", "x" * 257)]))


@caso("capacita-ripetuta", ERRORE_PROTOCOLLO,
      "`video.codec` twice: «the last one wins» and «the first one wins» are two "
      "implementations of the same document")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("video.codec", "av1")]))


@caso("capacita-del-lato-sbagliato", ERRORE_PROTOCOLLO,
      "`banco.marca` sent BY THE CLIENT: §4.3 declares it the server's, and the "
      "name is known — the exception for unknown names does not cover it")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("banco.marca", "si")]))


@caso("capacita-sconosciuta", None,
      "⭐ a NAME that does not exist: it is ignored and one carries on — exception 1 of §3")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao(BUONE + [("questa.non.esiste", "boh")]))
    await b3.attendi(cli, "ECCOMI")


@caso("solo-vp9", NIENTE_IN_COMUNE,
      "`video.codec = vp9` and nothing else: it did not misspell, it has nothing "
      "to talk about — and the reason is NOT ERRORE_PROTOCOLLO")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao([("video.codec", "vp9"), ("video.profondita", "8"),
                    ("audio.codec", "pcm")]))


@caso("hevc-e-vp9", None,
      "⭐ `video.codec = hevc,vp9`: `hevc` is read and one carries on, and the "
      "DISCARD is written in the server log (§4.3)")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao([("video.codec", "hevc,vp9"), ("video.profondita", "8"),
                    ("audio.codec", "pcm")]))
    await b3.attendi(cli, "ECCOMI")


@caso("senza-pcm", NIENTE_IN_COMUNE,
      "`audio.codec = opus` without `pcm`: §4.3 requires it of both, and whoever "
      "does not declare it takes leave with NIENTE_IN_COMUNE — not with ERRORE_PROTOCOLLO")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao([("video.codec", "hevc"), ("video.profondita", "8"),
                    ("audio.codec", "opus")]))


@caso("senza-8", NIENTE_IN_COMUNE,
      "`video.profondita = 10` without `8`: likewise")
async def _(cli, a, es):
    cli.apri_controllo()
    cli.manda(ciao([("video.codec", "hevc"), ("video.profondita", "10"),
                    ("audio.codec", "pcm")]))


# ── The credentials (§4.4) ─────────────────────────────────────────────────
@caso("utente-vuoto", ERRORE_PROTOCOLLO,
      "⛔ zero-byte user: legal for §6.0, out of range for §4.4 — and "
      "without this check an attacker moves no counter")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0003, s("") + s(a.parola)))


@caso("parola-vuota", ERRORE_PROTOCOLLO,
      "zero-byte password: likewise")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0003, s(a.utente) + s("")))


@caso("utente-257-byte", ERRORE_PROTOCOLLO,
      "257-byte user: the limit of §4.4 is 256")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0003, s("u" * 257) + s(a.parola)))


@caso("parola-1025-byte", ERRORE_PROTOCOLLO,
      "1025-byte password: the limit of §4.4 is 1024")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(0x0003, s(a.utente) + s("p" * 1025)))


@caso("credenziali-due-volte", ERRORE_PROTOCOLLO,
      "§4.4: a single attempt per connection")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(inquadra(0x0003, s(a.utente) + s(a.parola)))


# ── ATTACCA (§4.5, §7.1) ───────────────────────────────────────────────────
@caso("tela-1921x1080", ERRORE_PROTOCOLLO,
      "odd canvas: the encoder would round it silently — two different sizes "
      "under the same label, error form E2")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(tl=1921))


@caso("tela-319x240", ERRORE_PROTOCOLLO, "canvas below the minimum of §4.5")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(tl=319, ta=240))


@caso("tela-7682x4320", ERRORE_PROTOCOLLO, "canvas above the maximum of §4.5")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(tl=7682, ta=4320))


@caso("vista-300x801", None,
      "⭐ MUST PASS: §7.1 says the view does not have the canvas constraints — "
      "«any size from 1x1 up is legal, odd included» (R1.17)")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(vl=300, va=801))
    await b3.attendi(cli, "SESSIONE")


@caso("vista-1x1", None,
      "⭐ MUST PASS: the lower limit declared by §7.1, to the letter")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(vl=1, va=1))
    await b3.attendi(cli, "SESSIONE")


@caso("disposizione-malformata", ERRORE_PROTOCOLLO,
      "`it!!` is not an XKB name: it misspelled")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(disp="it!!"))


@caso("disposizione-sconosciuta", SESSIONE_NON_SERVIBILE,
      "⛔ `zz` is WELL FORMED and the machine does not have it: §4.5 wants TWO "
      "different faults, and the detail MUST be in the body (§8.2)")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(disp="zz"))


@caso("disposizione-con-variante", None,
      "⭐ `de(neo)`: the form with the variant in parentheses is lawful (§4.5)")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(attacca(disp="de(neo)"))
    await b3.attendi(cli, "SESSIONE")


# ── The bench function (§7.5) ──────────────────────────────────────────────
@caso("banco-spento", None,
      "⛔ `BANCO_MARCA` with the function off: there MUST arrive "
      "`BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` — not a silence and not a "
      "closing.  It is the DEFAULT state of every server")
async def _(cli, a, es):
    await fino_a_sessione(cli, a)
    cli.manda(banco_marca(id_=1, ritardo=0))
    await banco_esito(cli, es, id_=1, esito=2, motivo=1)  # RIFIUTATA, SPENTA


@caso("banco-ritardo-20000", None,
      "`ritardo_ms = 20000`: `RITARDO_FUORI_LIMITI`, and ⛔ **not** "
      "ERRORE_PROTOCOLLO — dropping the session of the bench being calibrated "
      "is the bad idea §7.1 avoids for out-of-bounds sizes")
async def _(cli, a, es):
    await fino_a_sessione(cli, a)
    cli.manda(banco_marca(id_=7, ritardo=20000))
    await banco_esito(cli, es, id_=7, esito=2, motivo=2)  # RIFIUTATA, RITARDO


@caso("banco-id-zero", ERRORE_PROTOCOLLO,
      "`id = 0`, which §7.5 declares reserved.  ⚠ The document does not say the outcome: "
      "here the drop is chosen, because it is a malformed message and not a "
      "wrong bench parameter")
async def _(cli, a, es):
    await fino_a_sessione(cli, a)
    cli.manda(banco_marca(id_=0))


@caso("banco-prima-di-sessione", ERRORE_PROTOCOLLO,
      "`BANCO_MARCA` before `SESSIONE`: there is no frame to "
      "paint on")
async def _(cli, a, es):
    await fino_ad_ammesso(cli, a)
    cli.manda(banco_marca())


# ── The streams (§2.5) ─────────────────────────────────────────────────────
#
# ⛔ IN HERE THE PAYLOAD IS WELL FORMED ON PURPOSE, and it is not a detail.
#
#    The violation these four cases test is **the stream**: how many there
#    are, in which direction the channel goes, on which kind of stream it lives.
#    If a crooked message is also put inside — a `CIAO` with a zero-byte body,
#    a `tipo` that does not exist — a server that does not count the streams
#    takes leave all the same, for the other reason, and the case is **green
#    without having tested anything** (finding R7.7).  Every payload below is
#    legal *in itself* and in the state in which it is sent: the only crooked
#    thing is the stream.
@caso("secondo-bidirezionale", ERRORE_PROTOCOLLO,
      "⛔ «the client MUST NOT open bidirectional streams beyond 0»: the "
      "control channel is ONE ONLY for the whole session.  The payload is "
      "a well-formed CREDENZIALI, which after ECCOMI is the right message: "
      "the only violation is the extra stream")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    altro = cli.apri_bidi()
    cli.manda_su(altro, inquadra(0x0003, s(a.utente) + s(a.parola)))


@caso("uni-controllo", ERRORE_PROTOCOLLO,
      "the CONTROL channel (high byte 0x00) on a unidirectional stream: "
      "«control lives only on stream 0» (§2.5).  ⚠ CREDENZIALI and not "
      "CIAO: a second CIAO would also be a wrong state, that is a "
      "second reason to take leave")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    u = cli.apri_uni()
    cli.manda_su(u, inquadra(0x0003, s(a.utente) + s(a.parola)))


@caso("uni-video", ERRORE_PROTOCOLLO,
      "the VIDEO channel (0x03) FROM THE CLIENT: wrong direction — video goes from "
      "server to client (§2.5).  ⛔ `0x0301` = key frame, which §6.2 "
      "declares LEGAL: with `0x0300` the only applicable rule was «other "
      "values: ERRORE_PROTOCOLLO», and the direction was never put to the test")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    u = cli.apri_uni()
    # the exact 28-byte header of §6.2: type, codec, width, height,
    # number, instant, input — all values within the limits
    cli.manda_su(u, struct.pack("!HHIIIQI", 0x0301, 1, 1920, 1080, 1, 0, 0))


@caso("uni-audio", ERRORE_PROTOCOLLO,
      "the AUDIO channel (0x04) on a STREAM: audio lives only on datagrams "
      "(§2.5, §6.3).  The payload is the well-formed header of §6.3 — "
      "`tipo = 0x0401`, `codec = 2` (PCM): the only violation is the stream")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    u = cli.apri_uni()
    cli.manda_su(u, struct.pack("!HHQ", 0x0401, 2, 0))


@caso("uni-byte-alto-ignoto", ERRORE_PROTOCOLLO,
      "a high byte that is none of the five of §2.5")
async def _(cli, a, es):
    await fino_a_eccomi(cli)
    u = cli.apri_uni()
    cli.manda_su(u, struct.pack("!HI", 0x0900, 0))


# ===========================================================================
async def gira_caso(a, nome, atteso, spiega, f):
    es = Esito()
    gestore = None
    try:
        gestore, cli, stato = await apri(a)
        es.stato_http = stato
        if stato != "200":
            es.errore = f"the extended CONNECT answered {stato}"
            return es
        es.fase = "preparation+violation"
        await f(cli, a, es)
        # ⛔ HERE, AND NOT BEFORE.  All the cases with an `atteso` end with
        #    sending the crooked byte and wait for nothing afterwards: if `f`
        #    returns, the violation really left.  If instead it stopped earlier —
        #    the fixed `ATTACCA` refused, the `ECCOMI` that does not arrive, PAM
        #    saying no — the case tested nothing and `provocato` stays false,
        #    which is what the verdict looks at (finding R7.1).
        es.provocato = True
        es.fase = "collection"
        # ⚠ On the cases that MUST pass one waits anyway: «it did not drop
        #   immediately» is not «it did not drop».
        await raccogli(cli, es, attesa=3.0 if atteso is None else 12.0)
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        es.errore = f"{type(e).__name__}: {e}"
        # ⛔ AND THE REASON IS NOT SCRAPED FROM THE EXCEPTION TEXT.
        #
        #    Here there was a loop over `MOTIVI` that looked for the name of a
        #    §8.2 reason inside `str(e)` and took it as «reason arrived».  The
        #    defect: `b3.attendi` raises `RuntimeError("CONGEDO invece di
        #    SESSIONE: motivo 0x0b = ERRORE_PROTOCOLLO")` even when what drops
        #    is the PREPARATION — and that string contains exactly the name of
        #    the expected reason.  R7.1 counted **twelve** that could be green
        #    with the crooked byte never sent, and ⚠ **it closed in on
        #    itself**: the more broken the server was upstream, the more those
        #    cases became green (finding R7.1, forms E6 and E7).
        #
        # ⭐ The reason is read by `raccogli`, from a message that arrived on the
        #    wire.  The exception text stays what it is: a diagnosis to print,
        #    not a verdict.
    finally:
        if gestore is not None:
            try:
                await gestore.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
    return es


async def il_percorso(a):
    """⛔ §2.2: a WebTransport session on a different path is a 404.

    It stands apart because it is not an RCP violation: it is §3 applied **to
    the first byte**, before RCP begins — and in fact there is no CONGEDO to
    wait for, because there is no control channel.
    """
    fuori = []
    for percorso, atteso in (("/rcp/2", "404"), ("/", "404"),
                             ("/rcp/1", "200")):
        gestore = None
        try:
            gestore, cli, stato = await apri(a, percorso)
        except Exception as e:  # noqa: BLE001
            stato = f"error {type(e).__name__}"
        finally:
            if gestore is not None:
                try:
                    await gestore.__aexit__(None, None, None)
                except Exception:  # noqa: BLE001
                    pass
        fuori.append((percorso, atteso, stato, stato == atteso))
    return fuori


async def ancora_vivo(a):
    """⛔ B0.5 — the half nobody writes.

    It is not enough that the connection dropped: **it must be the connection
    that dropped, not the server**.  Here a new connection is opened and it
    gets as far as `ECCOMI`.
    ⚠ Not as far as `SESSIONE`: it would cost the fixed second of §4.4-bis at
      every case, that is forty seconds of bench for a property the full run
      at the end verifies once and well.
    """
    gestore = None
    try:
        gestore, cli, stato = await apri(a)
        if stato != "200":
            return False, f":status {stato}"
        await fino_a_eccomi(cli)
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        if gestore is not None:
            try:
                await gestore.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass


async def giro_completo(a):
    """The good handshake, whole: the check that says the server did not stay
    standing but useless."""
    gestore = None
    try:
        gestore, cli, stato = await apri(a)
        if stato != "200":
            return False, f":status {stato}"
        await fino_a_sessione(cli, a)
        return True, ""
    except Exception as e:  # noqa: BLE001
        return False, f"{type(e).__name__}: {e}"
    finally:
        if gestore is not None:
            try:
                await gestore.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass


async def limitatore(a):
    """⛔ §4.4-bis, and the two halves that get forgotten.

    a) MALFORMED messages move no counter: six out-of-range `CREDENZIALI`,
       and then a good one that MUST pass;
    b) the **per-address** counter really exists: six failed attempts with
       SIX DIFFERENT NAMES from the same address, and the seventh — again a new
       name — must receive `TROPPI_TENTATIVI`.

    ⚠ **Prediction written before measuring**: (b) will be RED.  The key of
      the per-address counter is the `provenienza`, which contains **the port** —
      and with a single attempt per connection (§4.4) the port changes every
      time, so that counter is always 1 and never blocks anyone.  It is the
      worst shape: code present, that looks right, and that does
      nothing.
    """
    fuori = {}
    # (a) six malformed, then a good one
    for i in range(6):
        gestore, cli, _ = await apri(a)
        try:
            await fino_a_eccomi(cli)
            cli.manda(inquadra(0x0003, s("") + s("x")))
            await asyncio.sleep(0.2)
        except Exception:  # noqa: BLE001
            pass
        finally:
            await gestore.__aexit__(None, None, None)
    ok, perche = await giro_completo(a)
    fuori["malformati-non-contano"] = (ok, perche)

    # (b) seven failed with SEVEN DIFFERENT NAMES, from the same address
    motivi = []
    for i in range(7):
        gestore, cli, _ = await apri(a)
        es = Esito()
        try:
            await fino_a_eccomi(cli)
            cli.manda(inquadra(0x0003, s(f"nessuno{i}") + s("sbagliata")))
            # ⚠ The answer is AWAITED instead of sleeping for a time chosen by
            #   eye: PAM has its own delay on failures, and a `sleep` that is
            #   too short would measure a counter that has not been
            #   incremented yet.
            await raccogli(cli, es, attesa=15)
        except Exception:  # noqa: BLE001
            pass
        finally:
            await gestore.__aexit__(None, None, None)
        motivi.append(es.motivo)
    # The first five are CREDENZIALI_ERRATE; from the sixth on the threshold of
    # §4.4-bis has passed, and the PER-ADDRESS counter must speak.
    fuori["contatore-per-indirizzo"] = (
        motivi[-1] == TROPPI_TENTATIVI,
        "reasons: " + " ".join(
            MOTIVI.get(m, str(m)) if m is not None else "-" for m in motivi))

    # ⛔ AND THE CHECK THAT TELLS A COUNTER FROM A BLOCK: now the RIGHT
    #    password, from the same address, MUST receive TROPPI_TENTATIVI all
    #    the same.  A server that counted without blocking would give the same
    #    line as above and let in anyone who guessed at the sixth try.
    gestore, cli, _ = await apri(a)
    es = Esito()
    try:
        await fino_a_eccomi(cli)
        cli.manda(inquadra(0x0003, s(a.utente) + s(a.parola)))
        await raccogli(cli, es, attesa=15)
    except Exception:  # noqa: BLE001
        pass
    finally:
        await gestore.__aexit__(None, None, None)
    fuori["blocca-anche-la-parola-giusta"] = (
        es.motivo == TROPPI_TENTATIVI,
        f"with the GOOD credentials: {MOTIVI.get(es.motivo, es.motivo)}")
    return fuori


VERDE, ROSSO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[0m"


def riga(ok, nome, testo):
    print(f"    {VERDE if ok else ROSSO}{'OK' if ok else 'NO'}{GRIGIO}  "
          f"{nome:26s} {testo}")


def esito_finale(conti, guasti, parziale, reg=None):
    """⛔ Every count with its denominator, and the denominator COMPUTED.

    The old line printed `N su N` — the same expression twice — and only when
    `guasti == 0`, that is it carried no information the colour did not already
    carry (finding R7.14).  ⚠ And a denominator of **zero** is said, not
    hidden: «0 out of 0» is not a green.
    """
    print()
    print("    == what this run really looked at")
    for che, (buoni, tot) in conti.items():
        if tot == 0:
            # ⛔ A zero denominator is DECLARED: «nobody looked» and «all
            #    passed» look the same if one keeps quiet.
            print(f"    --  {che:44s} no case triggered it")
            continue
        col = VERDE if buoni == tot else ROSSO
        print(f"    {col}{buoni:3d} out of {tot:3d}{GRIGIO}  {che}")
    print()
    # ⛔ And the verdict goes into the log with the target inside, or in six
    #    months «B5 passes» will not say against which of the two servers.
    if reg is not None:
        reg.scrivi({"tipo": "verdetto", "guasti": guasti, "parziale": parziale,
                    "conti": {k: v for k, v in conti.items()}})
        print(f"    --  {reg.riassunto()}")
    if guasti:
        print(f"    {ROSSO}⛔ B5: {guasti} points do not pass against "
              f"«{reg.bersaglio if reg else '?'}»{GRIGIO}")
        return 1
    if parziale:
        print(f"    {VERDE}⭐ the selected cases pass{GRIGIO} — ⚠ and this "
              f"is NOT «B5 passes»: the run was partial")
        return 0
    print(f"    {VERDE}⭐ B5 passes against «{reg.bersaglio if reg else '?'}», and the "
          f"numbers above say on what{GRIGIO}")
    print(f"    ⚠ and it is not «B5 passes»: the other target is another program, "
          f"and this run says nothing about it")
    return 0


def conta(casi):
    """⛔ The two numbers, COMPUTED — and they are two, not one.

    «44 violations out of 44» printed the same expression as numerator and as
    denominator, and counted in it also the eight cases that MUST pass, on
    which «the right reason every time» is false by construction (finding
    R7.14).  From here on the number is produced by this function, and no
    comment rewrites it by hand.
    """
    violazioni = sum(1 for c in casi if c[1] is not None)
    return violazioni, len(casi) - violazioni


async def principale(a):
    casi = [c for c in CASI if not a.solo or a.solo in c[0]]
    tot_v, tot_verdi = conta(CASI)
    if a.elenco:
        print(f"== B5: {len(CASI)} cases — {tot_v} violations and {tot_verdi} "
              f"⭐ expected greens.  Every line is a PREDICTION\n")
        for nome, atteso, spiega, dove, _ in CASI:
            att = (f"{atteso:#04x} {MOTIVI.get(atteso, '?')}" if atteso
                   else "⭐ MUST PASS")
            print(f"  {nome:26s} {att}")
            print(f"  {'':26s}   {spiega}")
        return 0

    # ⛔ ZERO CASES IS NOT «ALL PASSED».
    #
    #    `--solo pippo` matched no name, the loop did not run, and the bench
    #    printed «0 violations out of 0» and exited 0: a typo in the filter was
    #    indistinguishable from a green bench (finding R7.15).  ⭐ They are THREE
    #    outcomes — nothing to measure, does not pass, passes — and they want
    #    three different exit codes.
    if not casi:
        print(f"    {ROSSO}⛔ «--solo {a.solo}» selected ZERO cases out of "
              f"{len(CASI)}: there is nothing to measure{GRIGIO}")
        print("       This is NOT a green.  The names are read with --elenco.")
        return 2

    sel_v, sel_verdi = conta(casi)

    # ⛔ THE RUN'S LOG, AND THE FIRST LINE SAYS AGAINST WHAT ONE MEASURES.
    #
    #    Until 11 Aug 2026 B5 had **no** log: it ran, and the output was on
    #    screen.  ⚠ Which means that none of its forty-four outcomes is
    #    re-verifiable today, and that the day two runs say different things
    #    there will be no way of knowing which server answered which.
    a.reg = b0.Registro(a.uscita, a.bersaglio, a.porta, a.giro or None,
                        a.md5 or None)
    prof = a.reg.profilo
    a.reg.apri_giro(
        "B5", "violations sent on a new connection per case; the "
              "server is started by 01-b5-lancia.sh and no moving scene "
              "is needed",
        extra={"casi_selezionati": len(casi), "casi_totali": len(CASI),
               "filtro": a.solo, "violazioni": sel_v, "verdi_attesi": sel_verdi,
               # ⛔ THE ECHO: on the product it is not there, and the difference
               #    is written BEFORE measuring.  `src/webtransport.c`
               #    `scarta_stream_di_troppo()`: «the bytes are thrown away, and
               #    NOT sent back».  ⚠ A bench that waited for it would stay
               #    hanging, and on 10 Aug 2026 that red was diagnosed for
               #    hours as a «certificate defect».  B5 does not wait for it:
               #    it discards it if it arrives, and here declares whether it
               #    was supposed to arrive.
               "eco_attesa": prof["eco"]})
    print(f"== B5 — the violation tests against the server")
    print(f"   ⛔ TARGET: {a.bersaglio} · port {a.porta} · binary md5 "
          f"{(a.md5 or 'unknown')[:12]}…")
    print(f"      {prof['eseguibile']}")
    print(f"   ⚠ B2's echo on the streams opened by the bench: "
          f"{'expected' if prof['eco'] else '⛔ NOT expected on this target'}")
    print(f"   this run's log: {a.uscita or '⛔ NONE'}")
    print(f"   {len(casi)} cases out of {len(CASI)} selected: {sel_v} violations "
          f"and {sel_verdi} ⭐ expected greens")
    print("   ⛔ every case: the violation really sent, the right reason in the "
          "right message,")
    print("      the two roads of §3.1, and the server still alive afterwards\n")
    if a.solo:
        print(f"    ⚠ PARTIAL RUN.  The path (§2.2), the full run and the")
        print(f"      limiter (§4.4-bis) are NOT run: they do not depend on the")
        print(f"      selected cases, and running them here would say «passes» on a")
        print(f"      part of the bench nobody asked to measure.\n")

    # ⛔ EVERY COUNT WITH ITS DENOMINATOR, and the denominators are different
    #    because the measured properties are different.
    conti = {
        "violations with the expected reason": [0, 0],
        "⭐ expected greens, session alive": [0, 0],
        "§3.1 point 3 — reason in the WT closing": [0, 0],
        "§11 — reason in the right message": [0, 0],
    }
    guasti, morto = 0, False
    for nome, atteso, spiega, dove, f in casi:
        es = await gira_caso(a, nome, atteso, spiega, f)
        if atteso is None:
            conti["⭐ expected greens, session alive"][1] += 1
            # ⛔ `viva` was COMPUTED and not looked at: it was enough that no
            #    reason had arrived, so a server that sends ECCOMI and then
            #    closes the WebTransport session gave the line «the session
            #    holds» while the session was dead (finding R7.2).
            ok = es.viva and es.errore is None
            testo = ("the session holds" if ok else str(es))
            conti["⭐ expected greens, session alive"][0] += int(ok)
        else:
            conti["violations with the expected reason"][1] += 1
            atteso_in = PORTATORE.get(atteso, "CONGEDO")
            # §11: «at least one of the two roads» must have carried the reason.
            strade = []
            if es.motivo == atteso and es.tipo_motivo == atteso_in:
                strade.append(atteso_in)
            if es.codice_wt == atteso:
                strade.append("chiusura-WT")
            ok = es.provocato and bool(strade)
            conti["violations with the expected reason"][0] += int(ok)
            testo = str(es)
        riga(ok, nome, testo)
        # ⛔ And the fact goes to the log BEFORE any conclusion: a case that
        #    brings the bench down (the server dying) must have left its own
        #    line, or the log would only tell about the runs that went well.
        a.reg.scrivi({"tipo": "caso", "nome": nome, "esito": bool(ok),
                      "atteso": atteso, "motivo": es.motivo,
                      "tipo_motivo": es.tipo_motivo, "codice_wt": es.codice_wt,
                      "provocato": es.provocato, "fase": es.fase,
                      "errore": es.errore, "dettaglio": es.dettaglio,
                      "viva": es.viva})
        if not ok:
            guasti += 1
            print(f"        expected: "
                  + (f"{atteso:#04x} {MOTIVI.get(atteso, '?')}" if atteso
                     else "⭐ no drop"))
            print(f"        {spiega}")
            if atteso is not None and not es.provocato:
                print(f"        ⛔ and the violation NEVER LEFT: the case "
                      f"stopped in «{es.fase}».  It is not a failed test, "
                      f"it is a test not done")
        if es.dettaglio:
            print(f"        detail from the body: «{es.dettaglio}»")
        if getattr(es, "banco", None):
            print(f"        BANCO_ESITO: {es.banco}")
        if atteso is not None and es.provocato:
            # ⛔ §3.1 POINT 3 IS COUNTED, NOT PRINTED.
            #
            #    Here there was a line that said «the reason arrived via
            #    CONGEDO» even when the second road had not arrived at all —
            #    true, and capable of making one believe the opposite — and
            #    `guasti` was not touched in any of the three branches: R7.3
            #    showed that ALL the violations stayed green with point 3
            #    never implemented.
            #    Point 3 is an **unconditional** MUST: the condition of §3.1
            #    is on point 2, and it is point 3 that the document calls
            #    «the one that saves the diagnoses».
            conti["§3.1 point 3 — reason in the WT closing"][1] += 1
            if es.codice_wt == atteso:
                conti["§3.1 point 3 — reason in the WT closing"][0] += 1
            else:
                guasti += 1
                visto = ("absent" if es.codice_wt is None
                         else f"{es.codice_wt:#04x}")
                riga(False, "", f"   §3.1 point 3 on «{nome}»: the closing "
                                f"of the session carries {visto}, expected "
                                f"{atteso:#04x}")
            # ⛔ AND IN WHICH MESSAGE (§11, §4.4).
            if es.motivo is not None:
                conti["§11 — reason in the right message"][1] += 1
                if es.tipo_motivo == PORTATORE.get(atteso, "CONGEDO"):
                    conti["§11 — reason in the right message"][0] += 1
                else:
                    guasti += 1
                    riga(False, "", f"   §11 on «{nome}»: the reason arrived "
                                    f"in {es.tipo_motivo}, and §11 wants it in "
                                    f"{PORTATORE.get(atteso, 'CONGEDO')} — they are "
                                    f"two different state machines")
        # ⛔ and the server afterwards?
        vivo, perche = await ancora_vivo(a)
        if not vivo:
            riga(False, "", f"⛔ THE SERVER NO LONGER ANSWERS after «{nome}»: {perche}")
            guasti += 1
            morto = True
            break

    if morto:
        print(f"\n    {ROSSO}⛔ the bench stops: without a server there is "
              f"nothing to measure{GRIGIO}")
        # ⚠ And what had been looked at UP TO THERE is printed anyway: a bench
        #   that stops without saying how much it had covered lets one believe
        #   it had covered everything.
        return esito_finale(conti, guasti, parziale=True, reg=a.reg)

    # ⛔ UNDER A FILTER THESE THREE SECTIONS ARE NOT RUN, and it is declared.
    #
    #    They do not depend on the selected cases: running them on a partial
    #    selection passes off as «B5 passes» a measurement nobody asked for —
    #    and in the case of the limiter it blocks the address for thirty seconds
    #    for someone who was only retrying a case.  It is the twin of
    #    R7.15(b), which in the launch script gave red on a rule never triggered.
    if a.solo:
        print(f"\n    ⚠ partial run: path, full run and limiter "
              f"skipped (see above)")
        return esito_finale(conti, guasti, parziale=True, reg=a.reg)

    print("\n== ⛔ The session path (§2.2), which comes before RCP")
    for percorso, atteso, stato, ok in await il_percorso(a):
        riga(ok, percorso, f":status = {stato}   (expected {atteso})")
        if not ok:
            guasti += 1

    # ⛔ THE FULL RUN COMES BEFORE THE LIMITER, and the order is a measurement.
    #
    #    The limiter of §4.4-bis, when it works, **blocks the address** — and
    #    from that moment even the right password receives
    #    TROPPI_TENTATIVI, for a window that starts at thirty seconds.  ⚠ A
    #    bench that put the good handshake AFTER would read that refusal as
    #    «the server is broken», that is it would give red precisely when the
    #    rule works.
    print("\n== ⭐ The good handshake, whole")
    ok, perche = await giro_completo(a)
    riga(ok, "giro-completo", perche or "CIAO → CREDENZIALI → ATTACCA → SESSIONE")
    if not ok:
        guasti += 1

    print("\n== ⛔ The attempt limiter (§4.4-bis) — last, and it says why")
    print(f"   ⚠ and on this target the ban lives in «{a.bersaglio}»: the ban")
    print(f"     file belongs to B5 only, and the final unblock is done by the launch")
    print(f"     script, AFTER this section and declaring it (B0.3)")
    print("   ⚠ from here on this address stays BLOCKED for at least thirty")
    print("     seconds: it is the rule working, not a fault of the bench")
    for nome, (ok, perche) in (await limitatore(a)).items():
        riga(ok, nome, perche)
        if not ok:
            guasti += 1

    return esito_finale(conti, guasti, parziale=False, reg=a.reg)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="B5 — the violations against the server")
    p.add_argument("--indirizzo", default="192.168.0.2")
    # ⛔ The port NO LONGER has a default that names a target: 7447 is the
    #    graft and 7448 the product, and a default here would mean that
    #    `--bersaglio prodotto` without `--porta` measures the graft while
    #    declaring the product.  It is passed by `01-b0-bersaglio.sh`, which is
    #    the only place where the two ports are written.
    p.add_argument("--porta", type=int, required=True)
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola", default="parola-di-prova")
    p.add_argument("--solo", default="", help="run only the cases that contain this")
    p.add_argument("--elenco", action="store_true",
                   help="print the predictions without measuring")
    b0.aggiungi_argomenti(p)
    # ⚠ `--elenco` measures nothing and does not need a port: it is checked
    #   before demanding it, or printing the predictions would require having
    #   already chosen a server.
    import sys as _s
    if "--elenco" in _s.argv:
        for _i, _az in enumerate(p._actions):
            if _az.dest == "porta":
                _az.required = False
    sys.exit(asyncio.run(principale(p.parse_args())))
