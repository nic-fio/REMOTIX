#!/usr/bin/env python3
"""02-pam-fermo.py — ⛔ HOW LONG WHOEVER IS **NOT** AUTHENTICATING STANDS STILL.

    python3 02-pam-fermo.py --porta 7531 --parola-file F --giri 5

===========================================================================
⛔ WHY THIS BENCH EXISTS, AND WHY ONE ALREADY WRITTEN WAS NOT ENOUGH

`DECISIONI.md` §1.10, 11 Aug 2026, from the user: the PAM check blocks
the server's single `poll` loop, and it is cured **before phase 2**.  ⛔ And the
line that orders this file is the last one of that decision:

    «The property to prove is NOT "PAM still works": it is "while one is
     authenticating, the others do not notice" — and today there is no
     bench that looks at it.  Without that bench the cure is a hope.»

⛔ **B8 cannot do it, and it is not an oversight of its own**: B8 times the answer
   to `CREDENZIALI`, that is **the time of whoever is getting in**.  That number is governed
   by PAM (`[M]` 11 Aug: +1034 ms beyond the fixed second on the rejected ones,
   the signature of `pam_faildelay`) and ⭐ **after the cure it must stay what it
   is**.  Whoever measured only that would see a successful cure as a
   failure, or — worse — would see nothing and call the hope
   green.

⇒ Here **the other number** is measured: how long whoever has already
  authenticated, or whoever is doing something else entirely, stands still WHILE a third party presents
  wrong credentials (the slow case, the one with `pam_faildelay`).

===========================================================================
⛔ THE SCENE, DECLARED — three connections, and each has a job

    A   «already inside»    full handshake up to `SESSIONE`, user
                            `prova`.  ⭐ **It is the ruler**: once attached it sends
                            `BANCO_MARCA` (§7.5) every 50 ms and times the
                            `BANCO_ESITO` that comes back.  It is the only
                            request/response pair RCP grants an
                            ACTIVE session in phase 1 — from phase 2 a frame
                            will take its place, and the number will mean the
                            same thing: **how long the screen of whoever is
                            already working stands still**;

    C   «the slow case»     opens, reaches `attesa-credenziali`, and sends
                            `CREDENZIALI` with the **WRONG** password.  ⛔ The
                            reason of the `RESPINTO` is read and required to be
                            `0x07 CREDENZIALI_ERRATE`: a `0x08
                            TROPPI_TENTATIVI` means the address was
                            banned and ⛔ **PAM was not even
                            queried** — that is the sample would measure a
                            server that did not do the slow thing.  That
                            sample is THROWN AWAY, and the reason is said;

    B   «the second one     is born the instant C sends `CREDENZIALI`, and
        doing the handshake» times **from zero to `ECCOMI`**.  It is the second
                            ruler, the one the mandate names first:
                            any user who opens the page while
                            another gets the password wrong.

⛔ **The denominator that makes everything readable**: before the window,
   20 marks are timed on a quiet loop.  ⭐ If the quiet median were not
   small, the ruler would be broken and there would be nothing to
   compare — and the bench says so instead of dividing by a number it has not
   looked at (`LEZIONI.md` §1.9: a denominator is read where the thing happens).

===========================================================================
⭐ THE POSITIVE CONTROL, AND HERE IT IS STRONGER THAN USUAL

«Can the tool find something that is surely there?»  ⛔ Yes, and it is **the round
of BEFORE**: the phase 1 server has the blocking, measured, and this bench
**must see it**.  A «before» round that did not find the pause would not prove
that the server is healthy: it would prove that this file cannot measure — and
any green «after» would be the worst of proofs (`CODER.md` §4.6).

⇒ **The expectation, written before the round** (and repeated by `--previsione`):

  | | BEFORE (phase 1) | AFTER (the cure) |
  |---|---|---|
  | the peak of the mark during the window | ⛔ **≥ 900 ms**, and close to the time PAM takes (1.0-2.2 s) | ⭐ **< 150 ms**, that is the order of magnitude of the quiet loop |
  | A's stalled time (sum of the excesses) | ⛔ ≈ the duration of PAM | ⭐ ≈ 0 |
  | B's handshake | ⛔ **≥ 900 ms** | ⭐ **< 300 ms** |
  | ⚠ C's time (whoever authenticates) | 1.0-2.2 s | ⭐ **THE SAME**, and that is fine |

⛔ **And the opposite case, that is what a cure that does NOT work would look like**:
   the peak of the mark stays ≥ 900 ms and B's handshake stays ≥ 900 ms,
   **while C's time does not change** — that is exactly the same
   picture as the «before», with the new code inside.  ⭐ It is the case that
   `--guasto` of `02-pam-lancia.sh` injects on purpose, and that this bench MUST
   colour red.

===========================================================================
⛔ WHAT THIS BENCH DOES **NOT** MEASURE, so that nobody appropriates it

  · the fixed second of §4.4-bis and the address ban: they are **B8's**, and
    this file does not judge them.  ⚠ It only OBSERVES them as much as needed to
    throw away the dirty samples (reason `0x08`);
  · the correctness of PAM: if `prova` does not get in, this bench stops and says
    so — ⛔ it does not go on measuring a scene in which A is not inside, which
    would give a green number because there was nothing to block (E1).

===========================================================================
⛔ ZERO AND FAILURE ARE TWO DIFFERENT THINGS (`REVIEWER.md` §1 point 4)

Every outcome carries `valido: true//false` and, when it is false, **why**.  A
round that could not measure does not write «0 ms»: it writes that it did not measure.
"""
import argparse
import asyncio
import json
import os
import socket
import ssl
import statistics
import struct
import sys
import time
from contextlib import AsyncExitStack

# ⛔ THE IMPORT IS INSIDE A `try`, AND NOT OUT OF LENIENCY — `--previsione` must
#    be able to run on the documents machine, where `aioquic` is not there.  ⚠ But
#    «the library is not there» does NOT become «the round went fine»: without `aioquic`
#    any real round stops with a message that names the library,
#    instead of a traceback that names a random line.
try:
    from aioquic.asyncio import connect
    from aioquic.asyncio.protocol import QuicConnectionProtocol
    from aioquic.h3.connection import H3_ALPN, H3Connection
    from aioquic.h3.events import HeadersReceived
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.quic.events import QuicEvent
    AIOQUIC = None
except ImportError as _e:            # noqa: N816
    AIOQUIC = str(_e)
    QuicConnectionProtocol = object
    QuicEvent = object

T = {"CIAO": 0x0001, "ECCOMI": 0x0002, "CREDENZIALI": 0x0003, "AMMESSO": 0x0004,
     "RESPINTO": 0x0005, "ATTACCA": 0x0006, "SESSIONE": 0x0007, "CONGEDO": 0x000C,
     "BANCO_MARCA": 0x000F, "BANCO_ESITO": 0x0010}
NOME = {v: k for k, v in T.items()}
MOTIVI = {0x01: "CHIUSO_DALL_UTENTE", 0x07: "CREDENZIALI_ERRATE",
          0x08: "TROPPI_TENTATIVI", 0x09: "NIENTE_IN_COMUNE",
          0x0A: "VERSIONE_INCOMPATIBILE", 0x0B: "ERRORE_PROTOCOLLO",
          0x0C: "SERVER_IN_CHIUSURA", 0x0D: "TEMPO_SCADUTO",
          0x0E: "SESSIONE_NON_SERVIBILE", 0x0F: "GIA_ATTIVA_REMOTA"}

# ⛔ The thresholds sit HERE, at the top and with a name, so that the expectation
#    is not adjusted once the round is over.  They are those written in the box above.
PICCO_BLOCCATO_MS = 900.0   # above: the loop stopped (the «before»)
PICCO_LIBERO_MS = 150.0     # below: the loop did not stop (the «after»)
STRETTA_LIBERA_MS = 300.0
BASE_MAX_MS = 60.0          # the quiet loop: above, the ruler is broken


def s(t):
    b = t.encode("utf-8") if isinstance(t, str) else t
    return struct.pack("!H", len(b)) + b


def inquadra(tipo, corpo):
    return struct.pack("!HI", tipo, len(corpo)) + corpo


def corpo_ciao():
    voci = [("video.codec", "hevc,av1"), ("video.profondita", "8,10"),
            ("audio.codec", "opus,pcm"), ("video.livello", "5.1"),
            ("video.misura_massima", "3840x2160"), ("appunti.testo", "si"),
            ("input.tocco", "no"), ("client.nome", "02-pam-fermo 0.1.0")]
    out = struct.pack("!HH", 1, len(voci))
    for n, v in voci:
        out += s(n) + s(v)
    return out


class Caduta(RuntimeError):
    pass


class Cliente(QuicConnectionProtocol):
    """⚠ Written looking at `RCP.md`, not `src/rcp.c`: two programs that
    agree because the same hand wrote them confirm nothing
    (`PIANO.md` §1.1).  ⛔ What is copied here from `01-b3-cliente.py` are the
    TWO `aioquic` traps already paid for on 10 Aug 2026, and they are copied
    on purpose: do not pass the WebTransport stream events to its H3 layer,
    and do not read `0` as «no stream»."""

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        self._http = H3Connection(self._quic, enable_webtransport=True)
        self.accettata = asyncio.get_event_loop().create_future()
        self.sessione = None
        self.controllo = None
        self.arrivati = bytearray()
        self.messaggi = asyncio.Queue()
        self.caduta = None

    def _cade(self, perche):
        if self.caduta is None:
            self.caduta = perche
            self.messaggi.put_nowait(None)

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
        self.controllo = self._http.create_webtransport_stream(
            self.sessione, is_unidirectional=False)
        return self.controllo

    def manda(self, dati):
        self._quic.send_stream_data(self.controllo, dati, end_stream=False)
        self.transmit()

    def quic_event_received(self, event: QuicEvent) -> None:
        nome = type(event).__name__
        if nome == "ConnectionTerminated":
            self._cade(f"connection TERMINATED: code "
                       f"{getattr(event, 'error_code', '?')}")
            return
        if nome == "StreamDataReceived" and event.stream_id == self.controllo:
            # ⛔ And it is NOT passed to aioquic's H3 layer: it would read it as a
            #    DATA frame and kill the connection (`[M]` 10 Aug 2026).
            self.arrivati += event.data
            while len(self.arrivati) >= 6:
                tipo, lung = struct.unpack("!HI", self.arrivati[:6])
                if len(self.arrivati) < 6 + lung:
                    break
                corpo = bytes(self.arrivati[6:6 + lung])
                del self.arrivati[:6 + lung]
                self.messaggi.put_nowait((tipo, corpo))
            if event.end_stream:
                self._cade("the control channel closed")
            return
        if nome == "StreamDataReceived" and event.stream_id == self.sessione:
            if event.end_stream:
                self._cade("the WebTransport session closed")
        for ev in self._http.handle_event(event):
            if isinstance(ev, HeadersReceived) and not self.accettata.done():
                self.accettata.set_result(
                    dict(ev.headers).get(b":status", b"?").decode())


async def attendi(cli, quale, attesa=25.0):
    """Waits for ONE message and requires it to be that one. Returns (name, body).

    ⛔ A `CONGEDO` or a `RESPINTO` are not «another message»: they are the
       measurement, and must be named with their reason or the diagnosis points at
       nothing."""
    m = await asyncio.wait_for(cli.messaggi.get(), timeout=attesa)
    if m is None:
        raise Caduta(f"the session dropped: {cli.caduta}")
    tipo, corpo = m
    nome = NOME.get(tipo, f"{tipo:#06x}")
    if quale and nome != quale:
        motivo = corpo[0] if corpo else 0
        if nome in ("CONGEDO", "RESPINTO"):
            raise Caduta(f"{nome} instead of {quale}: reason {motivo:#04x} = "
                         f"{MOTIVI.get(motivo, '?')}")
        raise Caduta(f"expected {quale}, got {nome}")
    return nome, corpo


async def apri(pila, indirizzo, porta, percorso):
    """Opens QUIC + the WebTransport session + the control channel."""
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{indirizzo}:{porta}"
    cli = await pila.enter_async_context(
        connect(indirizzo, porta, configuration=conf, create_protocol=Cliente))
    await asyncio.wait_for(cli.wait_connected(), timeout=10)
    cli.apri_sessione(autorita, percorso)
    stato = await asyncio.wait_for(cli.accettata, timeout=10)
    if stato != "200":
        raise Caduta(f"the extended CONNECT answered {stato}, not 200")
    cli.apri_controllo()
    return cli


async def fino_a_eccomi(cli):
    cli.manda(inquadra(T["CIAO"], corpo_ciao()))
    await attendi(cli, "ECCOMI")


async def fino_a_sessione(cli, utente, parola, larghezza=1920, altezza=1080):
    await fino_a_eccomi(cli)
    cli.manda(inquadra(T["CREDENZIALI"], s(utente) + s(parola)))
    t0 = time.monotonic()
    await attendi(cli, "AMMESSO", attesa=30)
    ms_ammesso = (time.monotonic() - t0) * 1000
    cli.manda(inquadra(T["ATTACCA"],
                       struct.pack("!IIII", larghezza, altezza, larghezza,
                                   altezza) + s("it")))
    await attendi(cli, "SESSIONE")
    return ms_ammesso


# ---------------------------------------------------------------------------
# ⛔ THE RULER: `BANCO_MARCA` -> `BANCO_ESITO`, and the return is timed.
#
# §7.5 rule 2: with the bench function OFF the server MUST answer
# `BANCO_ESITO(RIFIUTATA, FUNZIONE_SPENTA)` — «it must not stay silent and must not
# close».  ⭐ That is what makes this message a usable ruler: the
# answer always arrives, does not change state, and paints nothing on anybody's
# desktop (the function is off, invariant I6).
async def sonda(cli, periodo, ferma, campioni):
    n = 0
    while not ferma.is_set():
        n += 1
        t0 = time.monotonic()
        cli.manda(inquadra(T["BANCO_MARCA"], struct.pack("!III", n, 0x00FF00FF, 0)))
        try:
            _, corpo = await attendi(cli, "BANCO_ESITO", attesa=30)
        except (Caduta, asyncio.TimeoutError) as e:
            campioni.append({"n": n, "t0": t0, "ms": None, "caduta": str(e)})
            return
        t1 = time.monotonic()
        # ⛔ It is checked that the outcome is OF THE MARK SENT: a ruler that
        #    paired an answer with the wrong stopwatch would measure
        #    real numbers of another question.
        eco = struct.unpack("!I", corpo[:4])[0] if len(corpo) >= 4 else 0
        campioni.append({"n": n, "t0": t0, "ms": (t1 - t0) * 1000,
                         "eco": eco, "combacia": eco == n})
        resto = periodo - (t1 - t0)
        if resto > 0:
            await asyncio.sleep(resto)


async def stretta_cronometrata(pila, indirizzo, porta, percorso, fuori):
    """Connection B: from zero to `ECCOMI`, timed."""
    t0 = time.monotonic()
    try:
        cli = await apri(pila, indirizzo, porta, percorso)
        await fino_a_eccomi(cli)
        fuori["ms"] = (time.monotonic() - t0) * 1000
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        fuori["ms"] = None
        fuori["caduta"] = f"{type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
def sblocca(percorso, indirizzo):
    """§4.4-bis, the unblock command. ⛔ And it is always DECLARED: «the ban did not
    trigger» and «someone removed it» look the same (rule B0.3).

    ⚠ Here the unblock is never a tool to let a measurement pass: this
      bench does NOT test the ban.  It serves to bring the address to a KNOWN state
      before starting, and not to leave the field dirty for whoever comes next."""
    if not percorso:
        return "no socket declared: I did NOT unblock, and it is not «it was free»"
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(5)
        c.connect(percorso)
        c.sendall(f"SBLOCCA {indirizzo}\n".encode())
        r = c.recv(256).decode(errors="replace").strip()
        c.close()
        return r or "(empty answer)"
    except OSError as e:
        return f"⛔ I talked to nobody: {e}"


def ping(percorso):
    """⛔ The denominator of the unblock (rule B0.3): without it, «there was no ban»
    and «the unblock never reached anybody» look the same."""
    if not percorso:
        return "—"
    try:
        c = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        c.settimeout(5)
        c.connect(percorso)
        c.sendall(b"PING\n")
        r = c.recv(64).decode(errors="replace").strip()
        c.close()
        return r or "(empty)"
    except OSError as e:
        return f"⛔ {e}"


# ---------------------------------------------------------------------------
async def un_giro(a, parola, n):
    esito = {"giro": n, "valido": False, "perche": None}
    async with AsyncExitStack() as pila:
        # ── A: already inside ─────────────────────────────────────────────
        A = await apri(pila, a.indirizzo, a.porta, a.percorso)
        esito["ms_ammesso_A"] = await fino_a_sessione(A, a.utente, parola)

        campioni = []
        ferma = asyncio.Event()
        righello = asyncio.create_task(sonda(A, a.periodo, ferma, campioni))

        # ── the quiet loop: the denominator ───────────────────────────────
        await asyncio.sleep(a.tranquillo)
        base = [c["ms"] for c in campioni if c.get("ms") is not None]
        if len(base) < 5:
            ferma.set()
            await righello
            esito["perche"] = (f"only {len(base)} marks on a quiet loop: the "
                               f"ruler measured nothing")
            return esito
        esito["base_mediana_ms"] = statistics.median(base)
        esito["base_n"] = len(base)
        quante_prima = len(campioni)

        # ── C: the wrong credentials, and B at the same instant ───────────
        C = await apri(pila, a.indirizzo, a.porta, a.percorso)
        await fino_a_eccomi(C)

        b_fuori = {}
        t_cred = time.monotonic()
        C.manda(inquadra(T["CREDENZIALI"], s(a.utente_cattivo) + s(a.parola_cattiva)))
        seconda = asyncio.create_task(
            stretta_cronometrata(pila, a.indirizzo, a.porta, a.percorso, b_fuori))

        try:
            nome_C, corpo = await attendi(C, None, attesa=40)
            t_resp = time.monotonic()
        except (Caduta, asyncio.TimeoutError) as e:
            ferma.set()
            await righello
            await seconda
            esito["perche"] = f"C received no answer: {e}"
            return esito
        await seconda

        motivo = corpo[0] if corpo else 0
        esito["risposta_C"] = nome_C
        esito["motivo_C"] = motivo
        esito["motivo_C_nome"] = MOTIVI.get(motivo, "?")
        esito["ms_C"] = (t_resp - t_cred) * 1000

        # ── the tail: probing goes on after the window ────────────────────
        await asyncio.sleep(a.coda)
        ferma.set()
        await righello

        # ⛔ THE DIRTY SAMPLE IS THROWN AWAY, AND THE REASON IS SAID.
        if nome_C != "RESPINTO":
            esito["perche"] = (
                f"to wrong CREDENZIALI the server answered «{nome_C}», not "
                f"RESPINTO: the scene is not the declared one")
            return esito
        if motivo != 0x07:
            esito["perche"] = (
                f"the RESPINTO carries {motivo:#04x} = {MOTIVI.get(motivo, '?')}, "
                f"not 0x07 CREDENZIALI_ERRATE: ⛔ with {MOTIVI.get(motivo, '?')} "
                f"the server refuses WITHOUT querying PAM (§4.4-bis), that is the "
                f"slow thing did not happen and there was nothing to block")
            return esito

        # ── the count ─────────────────────────────────────────────────────
        # The window: the marks SENT between the `CREDENZIALI` and the `RESPINTO`.
        dentro = [c for c in campioni[quante_prima:]
                  if c.get("ms") is not None and t_cred <= c["t0"] <= t_resp]
        # ⚠ And also the mark sent BEFORE and returned AFTER: it is precisely the one
        #   the blocking eats, and excluding it would mean measuring everything
        #   except the fact (`LEZIONI.md` §1.9).
        a_cavallo = [c for c in campioni
                     if c.get("ms") is not None and c["t0"] < t_cred
                     and c["t0"] + c["ms"] / 1000 > t_cred]
        finestra = a_cavallo + dentro
        if not finestra:
            esito["perche"] = ("no mark was sent inside the window: the "
                               "window lasted "
                               f"{esito['ms_C']:.0f} ms and the period is "
                               f"{a.periodo * 1000:.0f} ms")
            return esito

        picco = max(c["ms"] for c in finestra)
        fermo = sum(max(0.0, c["ms"] - esito["base_mediana_ms"]) for c in finestra)
        esito.update({
            "valido": True,
            "n_finestra": len(finestra),
            "picco_ms": picco,
            "fermo_ms": fermo,
            "ms_stretta_B": b_fuori.get("ms"),
            "caduta_B": b_fuori.get("caduta"),
            "marche_scombinate": sum(1 for c in campioni
                                     if c.get("combacia") is False),
        })
        return esito


def previsione():
    print("""
== ⛔ THE EXPECTATION, WRITTEN BEFORE THE ROUND  (02-pam-fermo.py)

   What is measured:  how long whoever is NOT authenticating stands still, while
                      a third party presents WRONG credentials.

   | | BEFORE (phase 1, PAM on the single thread) | AFTER (the cure) |
   |---|---|---|
   | peak of the mark in the window | ⛔ >= %.0f ms   | ⭐ < %.0f ms |
   | A's stalled time (sum excesses)| ⛔ ~ the duration of PAM | ⭐ ~ 0 |
   | B's handshake                  | ⛔ >= %.0f ms   | ⭐ < %.0f ms |
   | ⚠ C's time (who authenticates) | 1000-2200 ms | ⭐ THE SAME |

   ⛔ THE OPPOSITE CASE — what a cure that does NOT work would look like:
      peak and handshake stay >= %.0f ms **while C's time does not change**,
      that is the same picture as the «before» with the new code inside.
      It is what `02-pam-lancia.sh --guasto` injects on purpose.

   ⛔ And if the quiet loop (the base median) were above %.0f ms, the
      ruler is broken and it is NOT divided by: the round is declared invalid.
""" % (PICCO_BLOCCATO_MS, PICCO_LIBERO_MS, PICCO_BLOCCATO_MS,
       STRETTA_LIBERA_MS, PICCO_BLOCCATO_MS, BASE_MAX_MS))


async def principale(a, parola):
    print(f"== 02-pam-fermo — https://{a.indirizzo}:{a.porta}{a.percorso}"
          f"  ·  {a.giri} rounds  ·  expectation «{a.attesa}»")
    print(f"   PING to the command socket: {ping(a.socket)}")
    print(f"   ⚠ unblock DECLARED, before starting: "
          f"{sblocca(a.socket, a.indirizzo)}")
    print(f"   ⚠ and for the other address this machine sees itself with: "
          f"{sblocca(a.socket, '127.0.0.1')}")

    esiti = []
    for n in range(1, a.giri + 1):
        try:
            e = await un_giro(a, parola, n)
        except Exception as ex:  # noqa: BLE001
            e = {"giro": n, "valido": False,
                 "perche": f"{type(ex).__name__}: {ex}"}
        e["quando"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        e["attesa"] = a.attesa
        e["porta"] = a.porta
        esiti.append(e)
        if e["valido"]:
            b = e["ms_stretta_B"]
            quanto_b = (f"{b:.0f} ms" if b is not None
                        else f"DROPPED ({e.get('caduta_B')})")
            print(f"   round {n}: base {e['base_mediana_ms']:.1f} ms · "
                  f"⛔ peak {e['picco_ms']:.0f} ms · stalled {e['fermo_ms']:.0f} ms · "
                  f"handshake B {quanto_b}")
            print(f"            and whoever was authenticating (C): {e['ms_C']:.0f} ms "
                  f"[{e['motivo_C_nome']}]  ·  A had got in in "
                  f"{e['ms_ammesso_A']:.0f} ms")
        else:
            print(f"   round {n}: ⛔ NOT VALID — {e['perche']}")
        # ⛔ Between one round and the next it is given room to breathe: A detaches and the slot
        #    (§8.2 reason 0x0F, invariant I2) must be free for the next round.
        await asyncio.sleep(1.0)

    buoni = [e for e in esiti if e["valido"]]
    print(f"\n== the count: {len(buoni)} valid rounds out of {len(esiti)}")
    if not buoni:
        print("   ⛔ NOTHING TO CONCLUDE: no valid round.  ⚠ It is not «zero "
              "milliseconds»: it is «I did not measure» (`LEZIONI.md` §1.9).")
        scrivi(a, esiti, None)
        return 3

    picchi = sorted(e["picco_ms"] for e in buoni)
    fermi = sorted(e["fermo_ms"] for e in buoni)
    strette = sorted(e["ms_stretta_B"] for e in buoni
                     if e["ms_stretta_B"] is not None)
    cc = sorted(e["ms_C"] for e in buoni)
    basi = sorted(e["base_mediana_ms"] for e in buoni)
    riassunto = {
        "giri_validi": len(buoni), "giri": len(esiti),
        "base_mediana_ms": statistics.median(basi),
        "picco_mediana_ms": statistics.median(picchi),
        "picco_massimo_ms": picchi[-1],
        "fermo_mediana_ms": statistics.median(fermi),
        "stretta_B_mediana_ms": statistics.median(strette) if strette else None,
        "C_mediana_ms": statistics.median(cc),
        "attesa": a.attesa,
    }
    print(f"   quiet loop (base)            median  {riassunto['base_mediana_ms']:8.1f} ms")
    print(f"   ⛔ peak of the mark          median  {riassunto['picco_mediana_ms']:8.1f} ms"
          f"   (maximum {riassunto['picco_massimo_ms']:.0f})")
    print(f"   ⛔ A's stalled time          median  {riassunto['fermo_mediana_ms']:8.1f} ms")
    if strette:
        print(f"   ⛔ B's handshake             median  {riassunto['stretta_B_mediana_ms']:8.1f} ms")
    print(f"   ⚠ who was authenticating (C) median  {riassunto['C_mediana_ms']:8.1f} ms"
          f"   ← ⭐ this must NOT change")

    # ── the verdict, against the expectation written beforehand ───────────
    verdetto = 0
    if riassunto["base_mediana_ms"] > BASE_MAX_MS:
        print(f"\n   ⛔ THE RULER IS BROKEN: the quiet loop measures "
              f"{riassunto['base_mediana_ms']:.0f} ms, above the {BASE_MAX_MS:.0f} "
              f"expected.  No comparison is readable.")
        verdetto = 3
    elif a.attesa == "bloccato":
        ok = (riassunto["picco_mediana_ms"] >= PICCO_BLOCCATO_MS)
        print(f"\n   {'⭐ OK' if ok else '⛔ NO'}  expected «bloccato»: the peak "
              f"had to be >= {PICCO_BLOCCATO_MS:.0f} ms and it is "
              f"{riassunto['picco_mediana_ms']:.0f}")
        if not ok:
            print("      ⛔ AND IT IS NOT GOOD NEWS: it means this "
                  "bench CANNOT SEE the blocking the server really has.\n"
                  "         A green «after» measured with a blind ruler is "
                  "the worst of proofs (`CODER.md` §4.6).")
        verdetto = 0 if ok else 1
    elif a.attesa == "libero":
        ok = (riassunto["picco_mediana_ms"] < PICCO_LIBERO_MS)
        ok_b = bool(strette) and riassunto["stretta_B_mediana_ms"] < STRETTA_LIBERA_MS
        print(f"\n   {'⭐ OK' if ok else '⛔ NO'}  expected «libero»: the peak "
              f"had to be < {PICCO_LIBERO_MS:.0f} ms and it is "
              f"{riassunto['picco_mediana_ms']:.0f}")
        if strette:
            print(f"   {'⭐ OK' if ok_b else '⛔ NO'}  and B's handshake < "
                  f"{STRETTA_LIBERA_MS:.0f} ms: it is "
                  f"{riassunto['stretta_B_mediana_ms']:.0f}")
        else:
            print("   ⛔ NO  no handshake of B measured: it is not «it was "
                  "fast», it is «I did not measure»")
        verdetto = 0 if (ok and ok_b) else 1
    else:
        print("\n   ⚠ no expectation declared (--attesa): the round measures and does not "
              "judge")

    scrivi(a, esiti, riassunto)
    return verdetto


def scrivi(a, esiti, riassunto):
    if not a.esiti:
        return
    riga = {"quando": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "macchina": os.uname().nodename,
            "scena": {"porta": a.porta, "indirizzo": a.indirizzo,
                      "utente": a.utente, "utente_cattivo": a.utente_cattivo,
                      "periodo_ms": a.periodo * 1000,
                      "tranquillo_s": a.tranquillo, "coda_s": a.coda},
            "attesa": a.attesa, "giri": esiti, "riassunto": riassunto,
            "nota": a.nota}
    with open(a.esiti, "a", encoding="utf-8") as f:
        f.write(json.dumps(riga, ensure_ascii=False) + "\n")
    print(f"   outcomes: {a.esiti}")


def parola_dal_file(percorso):
    """⛔ D12: the password does not go through the command line —
    anyone can read `/proc/<pid>/cmdline`."""
    try:
        modo = os.stat(percorso).st_mode & 0o077
    except OSError as e:
        print(f"   ⛔ the password file «{percorso}» cannot be read: {e}")
        sys.exit(2)
    if modo:
        print(f"   ⚠ «{percorso}» is readable by others (bits {modo:o})")
    with open(percorso, encoding="utf-8") as f:
        parola = f.read().strip("\n")
    if not parola:
        print(f"   ⛔ «{percorso}» is EMPTY: it is not «the password is empty», it is "
              f"«the launcher did not write it»")
        sys.exit(2)
    return parola


if __name__ == "__main__":
    p = argparse.ArgumentParser(
        description="how long whoever is NOT authenticating stands still")
    p.add_argument("--indirizzo", default="192.168.0.2")
    p.add_argument("--porta", type=int, default=7531)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default="prova")
    p.add_argument("--parola-file", default="")
    p.add_argument("--utente-cattivo", default="prova2")
    p.add_argument("--parola-cattiva", default="questa-non-e-la-parola-giusta")
    p.add_argument("--socket", default="")
    p.add_argument("--giri", type=int, default=5)
    p.add_argument("--periodo", type=float, default=0.05,
                   help="how often a mark is sent, in seconds")
    p.add_argument("--tranquillo", type=float, default=1.2,
                   help="how long probing goes on with the loop idle, for the denominator")
    p.add_argument("--coda", type=float, default=0.7)
    p.add_argument("--attesa", choices=["bloccato", "libero", "nessuna"],
                   default="nessuna",
                   help="the expectation, DECLARED BEFORE the round")
    p.add_argument("--esiti", default="")
    p.add_argument("--nota", default="")
    p.add_argument("--previsione", action="store_true")
    a = p.parse_args()
    if a.previsione:
        previsione()
        sys.exit(0)
    if AIOQUIC:
        print(f"   ⛔ «aioquic» is not on this machine ({AIOQUIC}): this "
              f"bench runs INSIDE the NIC-OS container.\n"
              f"      ⚠ It is not «the round went fine»: it is «I did not measure».")
        sys.exit(2)
    if not a.parola_file:
        print("   ⛔ --parola-file is needed (D12: the password does not go through argv)")
        sys.exit(2)
    parola = parola_dal_file(a.parola_file)
    try:
        sys.exit(asyncio.run(principale(a, parola)))
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        print(f"\n   ⛔ {type(e).__name__}: {e}")
        sys.exit(2)
