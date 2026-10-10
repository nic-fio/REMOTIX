#!/usr/bin/env python3
"""01-b8-cronometro.py — ⛔ B8: the fixed second, and THE BAN OF THE ADDRESS.

    python3 01-b8-cronometro.py --prediction
    python3 01-b8-cronometro.py --samples --block 3 --lap ...
    python3 01-b8-cronometro.py --ban before  --lap ...    (one life of the server)
    python3 01-b8-cronometro.py --ban after   --lap ...    (after the restart)
    python3 01-b8-cronometro.py --verdict --lap ...

⚠ It runs INSIDE the container: `aioquic` lives there.  It is driven by `01-b8-lancia.sh`.

===========================================================================
⛔ REWRITTEN ON 11 AUG 2026, AND WHAT FELL MUST BE KNOWN BY READING HERE

`DECISIONI.md` §1.9 replaced the shape of the limitation: **three failed
authentications from the same address within five minutes, and that address is
out for twelve hours**.  With it, these fall from this file:

  · the **two counters** (one per user name, one per address).  **Only one**
    remains, on the address: ⛔ three different names count **three**;
  · the check *«four failed · one succeeded · another four»*: after the third
    failed **there is no fifth attempt**;
  · ⛔ and **the twelve lives of the server**.  The old choreography turned the
    process off and on again at every block because that was the only way to
    reset the counters: *«`rcp_reset_session_log()` exists but nobody
    calls it — there is no message, signal or option that reaches it»*.
    ⭐ Now **there is**: the unblock command of §4.4-bis, which on 11 August was
    born on the host side.  The lives of the server are **two**, and the second
    exists for one reason only — proving that the ban survives the restart.

===========================================================================
⛔ WHAT IT MEASURES, IN TWO PARTS THAT DO NOT MIX

**1. The fixed second, and the three medians** — unchanged in substance.  §4.4
forbids distinguishing in the **reason** between «user does not exist» and
«wrong password»; §4.4-bis imposes a **fixed delay of one second** so that that
distinction cannot be read with the **stopwatch**.  ⛔ And the criterion is NOT
«≥ 1 s»: `pam_authenticate(); sleep(1); reply();` gives 1.001 · 1.050 · 1.300 s
in the three cases — three green lines, and the distinction readable exactly as
before (finding R3.2).  The criterion is **of a different shape**: the three
medians must differ **less than the noise of the measurement**.

**2. The ban** — new.  Three failed with **three different names**, then the
fourth attempt **with the RIGHT password** that MUST be refused with
`TOO_MANY_ATTEMPTS`; plus the three checks that say *no*; plus the page that
loads anyway and says how many hours are left; plus the unblock command.

===========================================================================
⛔ HOW THIS BENCH GETS ITS SAMPLES, AND WHY THE CHOICE MUST BE DECLARED

`FASI.md` §01-filo-nudo B8 says it in one line: *«the samples now cost: three
per address, then the ban.  The medians want many samples per case, so the
bench must **vary the source address** or **unblock between one block and the
next** — ⛔ and **declare which of the two it does**, because they change what
the measurement is measuring»*.

⭐ **This bench does the SECOND, and uses the first only as a margin.**

  · a **block** is the sequence between two unblocks.  Inside a block the bench
    brings at most **two** failures per address — ⛔ **one below the
    threshold**, and the count is done **without counting the reset on success**:
    if one day the reset stopped working, the balance would hold anyway and the
    bench would still measure PAM.  A balance that rests on the rule being
    tested is not a balance;
  · the failures alternate between **two source addresses** (`127.0.0.1` and
    `192.168.0.2`, which the same machine reaches because the server is running
    on `0.0.0.0`): it doubles the margin and ⛔ **it shows in the server log**,
    which writes `da=<address>:<port>` — the denominator read where the thing
    happens, not in our intention (`LEZIONI.md` §1.9);
  · between one block and the next, `01-b8-lancia.sh` calls the **unblock
    command** on both addresses, ⛔ **and prints it**.

⛔ **WHAT THIS CHOICE CHANGES, SAID INSTEAD OF HIDDEN.**  The samples are taken
   **always with the count below threshold**, so the three medians measure PAM
   plus the fixed delay and **never** the road of the immediate refusal.  It is
   what is needed — the three medians speak of what PAM lets leak — ⚠ but it
   means that this part of the bench **proves nothing about the ban**: the ban
   is proved by part 2, where nobody unblocks anything.

⛔ **AND NOBODY UNBLOCKS INSIDE THE BAN RUN** (B0.3: *«never inside the B8 run,
   or B8 no longer proves anything»*).  The unblocks of this bench are in three
   places only, and all three are declared:

     1. **before** starting, to start from a known state (B0.1);
     2. **between one block and the next** of the samples, and never inside the ban run;
     3. **at the end**, where the unblock is not a tool but **the thing proved**.

===========================================================================
⛔ THE THREE GUARDS AGAINST THE LIMITER, AND NONE TRUSTS THE OTHERS

  a. **the balance**: two failures per address per block, threshold three;
  b. **the plan is verified BEFORE running it**: `simulate()` is a model of the
     new §4.4-bis — threshold 3, sliding window of 5 minutes, key on the address
     only, reset on success, unblock that resets everything — and says
     **attempt by attempt** what should arrive.  `verify_plan()` **does not
     start** a block the model sees overflowing.  A comment saying «we stay
     below threshold» is not a check: this is;
  c. ⛔ **and on the wire every single answer is looked at**: a sample that comes
     back `REJECTED(TOO_MANY_ATTEMPTS)` **does not enter the medians**, it is
     counted separately and **takes the green away**.  It is the check that does
     not depend on any arithmetic of ours.

===========================================================================
⛔ THE RULE BY WHICH TWO MEDIANS ARE DECIDED TO BE «INDISTINGUISHABLE»

For every pair of cases: the **difference of the medians** and its 95 %
interval by **resampling** (bootstrap, 2000 repetitions, fixed seed so that two
runs on the same data give the same verdict).

  | the interval | the verdict |
  |---|---|
  | does **not** contain zero | ⛔ **THEY ARE DISTINGUISHABLE** |
  | contains zero, half-width ≤ WANTED_RESOLUTION | ⭐ **indistinguishable**, and it says how far one looked |
  | contains zero, half-width larger | ⚠ **SUSPENDED**: I did not look enough |

⭐ Looking **less** widens the interval and leads to *suspended*, not to green:
   it is the only shape of rule that cannot be satisfied by measuring less.

===========================================================================
⚠ THE `[?]` THIS BENCH HAS ALREADY FOUND, AND THAT THE BAN DOES NOT CLOSE

`[M]` 10 Aug 2026: the median of the refused was **2636 ms**, where §4.4-bis
wants ~1000.  ⛔ What governs the times is not our delay: it is **PAM**
(`pam_faildelay` in the stack of `/etc/pam.d/login` delays the FAILURES by ~3 s,
with libpam's randomisation).  As long as that delay is not constant, the
fixed second **does not hide what it declares it hides**.  The ban is a
different property and **does not close it**.

===========================================================================
⚠ TWO POINTS WHERE THE DOCUMENTS ALLOWED TWO READINGS, AND THE CHOICE MADE

  1. §4.4-bis: *«the refusal of a banned address **does not go through the
     fixed second** … it is decided **before CREDENTIALS**»*.  ⛔ `banchi/rcp/rcp.c`
     decides it **after** having received `CREDENTIALS` (it cannot do otherwise:
     the control channel is the only thing it sees) and makes it go **through
     the fixed delay anyway**.  ⭐ And it must be so, or the bench could not
     exist: B8 demands `TOO_MANY_ATTEMPTS` **inside a `REJECTED`** (§4.4, finding
     R1.18), and a refusal decided before `CREDENTIALS` would have no
     `REJECTED` to send.  Here the time of the refusal is **measured and
     printed**, and it makes neither red nor green: it is a defect of the
     document, not of the code;
  2. §4.4-bis: *«the page is served anyway»* does not say **with which HTTP
     status**.  The host answers **200**, and the reason is in its comment: with
     a 4xx an intermediary or the browser may replace the body, and the
     sentence the user MUST read would disappear.  Here **200** is demanded;
  3. ⭐ **and the most important of the three**: `FASI.md` §01-filo-nudo B8 asks
     for *«the THREE medians indistinguishable»*, and §4.4-bis wants the fixed
     delay *«even when the answer is ADMITTED»*.  ⚠ But what §4.4 **forbids**
     letting be known is one thing only — **whether a user name exists** — while
     «admitted» against «refused» the wire says by itself: they are two
     **different messages**.  ⛔ The three pairs are not worth the same, and this
     bench runs all three **counting them separately**:

       `nonexistent − wrong` that separates   ⇒ ⛔ FULL RED: it is the
                                                    separation §4.4 forbids;
       the other two that separate                ⇒ an outcome of its own (5),
                                                    with the culprit named.

     ⚠ The convenient reading is not chosen and nothing is kept quiet: both are
       run and it is said **which number belongs to which**.  ⛔ And `[M]` 11 Aug
       2026 the pair that carries the secret does **not** separate (−56 ms,
       interval [−569; +442]) while the other two separate by ~2 seconds: the
       fixed delay does what it must, and what moves the other two is PAM.
"""
import argparse
import asyncio
import importlib.util
import json
import os
import pwd
import random
import re
import socket
import ssl
import statistics
import sys
import time

from aioquic.asyncio import connect
from aioquic.h3.connection import H3_ALPN
from aioquic.quic.configuration import QuicConfiguration

HERE = os.path.dirname(os.path.abspath(__file__))


# ── The facts recorded before the English rename (DECISIONI §10.38: banchi/prodotto/b8-*.jsonl,
#    re-read by --verdict --lap) keep the Italian words.  The first
#    tuple is protected (english-migration/protetti.tsv), the second is renamed with the code: after
#    the rename OLD_SPELLING maps every old word to the code's own, before it is empty.
_OLD_WORDS = (
    "giro", "tipo", "etichetta", "indirizzo", "esito", "dettaglio", "bannato", "restano_ms",
    "minuti", "frase", "errore", "atteso_bannato", "nome", "messaggio", "blocco", "ordine",
    "caso", "classe", "atteso_motivo", "stato-iniziale", "NON-BANNATO", "pagina", "AMMESSO",
    "misurato", "controllo", "atteso", "RESPINTO", "campione", "inesistente", "sbagliata",
    "limitatore", "TOLTO",
)  # end of the old words
_WORDS_NOW = (
    "lap", "kind", "label", "address", "outcome", "detail", "banned", "remain_ms",
    "minutes", "sentence", "failure", "expected_banned", "label_name", "message", "block", "order",
    "case_v", "cls_name", "expected_reason", "initial-state", "NOT-BANNED", "page_v", "ADMITTED",
    "measured", "check", "expected_val", "REJECTED", "sample", "nonexistent", "wrong",
    "limiter", "REMOVED",
)
OLD_SPELLING = {a: b for a, b in zip(_OLD_WORDS, _WORDS_NOW) if a != b}


def current_spelling(x):
    """A record of an old register in the code's spelling: keys, and string values equal to a word."""
    if isinstance(x, dict):
        return {OLD_SPELLING.get(k, k): current_spelling(v) for k, v in x.items()}
    if isinstance(x, list):
        return [current_spelling(v) for v in x]
    return OLD_SPELLING.get(x, x) if isinstance(x, str) else x


def _import(label_name, file):
    spec = importlib.util.spec_from_file_location(label_name, os.path.join(HERE, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ⛔ The B3 test client is IMPORTED, not copied: inside it is the line that
#    prevents it from handing the control-channel events to aioquic's HTTP/3
#    layer — without which the connection dies at the hand of the CLIENT, and
#    here the symptom would be «the server does not answer in time».
b3 = _import("b3cliente", "01-b3-cliente.py")
# ⛔ And the unblock command too: if this file rewrote it for itself, B0.3
#    would have two unblock commands and nobody would know which one ran.
cmd = _import("b8sblocca", "01-b8-sblocca.py")
# ⛔ And the TARGET's profile: the differences between the two servers in a single file.
b0 = _import("b0bersaglio", "01-b0-bersaglio.py")

wrap, s_str, REASONS = b3.wrap, b3.s, b3.REASONS
T_CREDENTIALS = 0x0003
WRONG_CREDENTIALS, TOO_MANY_ATTEMPTS = 0x07, 0x08

GREEN, RED, YELLOW, GRAY = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# ── The numbers of the rule, all in one place and all declared ───────────────
# `RCP.md` §4.4-bis, the user's shape of 10 Aug 2026.
THRESHOLD = 3                 # three failed authentications from the same address
WINDOW_MIN = 5           # ...within five minutes (SLIDING window)
BAN_ORE = 12               # ...and that address is out for twelve hours
BALANCE = 2               # ⛔ one BELOW the threshold, per address and per block
FIXED_DELAY = 1000.0     # §4.4-bis: no answer to CREDENTIALS before 1 s
WANTED_RESOLUTION = 50.0  # ms — the separation the phase document names
MIN_SAMPLES = 10       # below this one does not judge: one says «suspended»
REPETITIONS = 2000         # bootstrap resamplings
SEED = 20260811            # ⛔ fixed: two verdicts on the same data coincide
# ⛔ THE TWO MARGINS NEEDED TO NAME A DEFENDANT, and they are here because a
#    number chosen inside an `if` is a number nobody compares.
#    · `BLAME_MARGIN`  how long the server must have waited BEYOND the fixed
#      second for one to be able to say «what governed was not our delay».
#      Below this threshold the fixed second covered everything, and whoever
#      delayed left no trace at the point where the server measures.
#    · `TIMER_MARGIN`  by how much the CLIENT's stopwatch may be below
#      the SERVER's before the difference stops being network noise.
#      ⛔ The client measures an interval that CONTAINS the server's (it starts
#      before sending and ends after receiving): it can only be larger.  If it
#      is smaller, it is not the server that is strange — it is the bench's
#      stopwatch that is not timing what it declares.
BLAME_MARGIN = 200.0
TIMER_MARGIN = 100.0

CASES = ("nonexistent", "wrong", "giusta")
EXPECTED = {"nonexistent": ("REJECTED", WRONG_CREDENTIALS),
          "wrong": ("REJECTED", WRONG_CREDENTIALS),
          "giusta": ("ADMITTED", None)}

# The six permutations of the triplet.  ⛔ The order ROTATES: if one case always
#    sat right after the unblock and another always at the end, any drift inside
#    the block would end up **in the medians** disguised as a difference between
#    the cases.
ROTATIONS = [("nonexistent", "wrong", "giusta"),
             ("wrong", "giusta", "nonexistent"),
             ("giusta", "nonexistent", "wrong"),
             ("nonexistent", "giusta", "wrong"),
             ("wrong", "nonexistent", "giusta"),
             ("giusta", "wrong", "nonexistent")]

# ⛔ THE THREE NAMES OF THE BAN RUN — and they MUST be different.
#    `FASI.md` §01-filo-nudo B8: «with the same name three times, a server that
#    still had the per-NAME counter of the old shape would give green: the bench
#    would prove the wrong rule.  It is the same shape with which B5 found the
#    counter keyed on the port».
#    ⭐ And the three are not even of the same KIND: two names that do not exist
#       and a wrong password on the real user.  §4.4-bis counts the two things as
#       one — «the count does not know whether the name did not exist or the
#       password was wrong» — and this is the way to prove it instead of believing it.
BAN_NAMES = ("nessuno-b8-uno", "<username>", "nessuno-b8-tre")


# ===========================================================================
# The wire
# ===========================================================================
async def open_it(address, port, fpath="/rcp/1"):
    """A new connection, and the WebTransport session on `/rcp/1`.

    ⚠ One per attempt, and it is not a choice: §4.4 allows **a single attempt
      per connection**."""
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    authority = f"{address}:{port}"
    handler = connect(address, port, configuration=conf,
                      create_protocol=b3.Client)
    cli = await handler.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    cli.open_session(authority, fpath)
    state = await asyncio.wait_for(cli.accepted, timeout=8)
    return handler, cli, state


async def attempt(address, port, label_name, password, wait_closing=4.0):
    """One attempt: `CREDENTIALS` leaving, the answer arriving, the milliseconds.

    ⛔ WHAT IS INSIDE THE STOPWATCH, AND WHAT IS NOT.  Inside: the trip of
       `CREDENTIALS`, the server's work (ban guard, PAM, fixed delay) and the
       trip of the answer.  Outside: the QUIC/TLS handshake, the opening of the
       session, `HELLO`/`HERE_I_AM`.

    ⚠ The network round trip is inside and is not removed — but it is **the same
      for all three cases**, on the same path: it can move the three medians
      together, not separate them.  It is the reason the criterion is a DIFFERENCE.

    ⛔ AND THE CLOSING OF THE SESSION IS ALSO WAITED FOR, which is the **second
       road of §3.1 point 3** and the only thing that answers *«and the tab
       already open?»* of B8.  ⚠ It does not arrive together with the
       `REJECTED`: the host defers it by five passes of the write loop — half a
       second — on purpose, because a browser that processes the capsule before
       the bytes of the stream would throw away the `REJECTED` (defect found by
       B11).  Closing right after the answer would mean declaring «no closing
       code» on a code that was arriving.

    ⛔ The password ends up in no file (B13.2): only the **name** and the time
       come out of here."""
    outside = {"address": address, "label_name": label_name, "ms": None,
             "message": None, "motivo": None, "closure": None,
             "outcome": "failure", "failure": ""}
    handler = None
    try:
        handler, cli, state = await open_it(address, port)
        if state != "200":
            outside["failure"] = f"the session did not open: :status={state}"
            return outside
        cli.open_control()
        cli.send_it(wrap(b3.T["HELLO"], b3.body_hello()))
        await b3.should_wait(cli, "HERE_I_AM", wait=10)
        body_el = s_str(label_name) + s_str(password)
        t0 = time.perf_counter()
        cli.send_it(wrap(T_CREDENTIALS, body_el))
        # ⛔ `which=None`: ANY answer is accepted and classified afterwards.
        #    Demanding `ADMITTED` would raise an exception on the cases that must
        #    be refused — that is the bench would not have the time of the cases
        #    it cares most about.
        msg_name, body_r, _ = await b3.should_wait(cli, None, wait=30)
        outside["ms"] = (time.perf_counter() - t0) * 1000.0
        outside["message"] = msg_name
        if msg_name == "REJECTED":
            outside["motivo"] = body_r[0] if body_r else None
            # ⚠ Only after a REJECTED: after an ADMITTED the session stays alive and
            #   waiting here would mean waiting four seconds for nothing for every
            #   «giusta» sample — that is a third of the bench.
            try:
                await asyncio.wait_for(cli.dropped.wait(), timeout=wait_closing)
            except asyncio.TimeoutError:
                pass
            outside["closure"] = cli.close_code
        outside["outcome"] = "measured"
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        outside["failure"] = f"{type(e).__name__}: {e}"
    finally:
        if handler is not None:
            try:
                await handler.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
    return outside


def ranking(rec, case_v):
    """⛔ The third guard: what REALLY arrived.

    A `TOO_MANY_ATTEMPTS` is not a sample of «wrong password»: it is another road
    inside the server — **it does not even go through PAM** — and putting it in
    the same median would mean mixing two populations under the same label
    (form E2)."""
    if rec["outcome"] == "failure":
        return "failure"
    msg, motivo = EXPECTED[case_v]
    if rec["message"] == "REJECTED" and rec["motivo"] == TOO_MANY_ATTEMPTS:
        return "limiter"
    if rec["message"] != msg:
        return "inatteso"
    if motivo is not None and rec["motivo"] != motivo:
        return "inatteso"
    return "expected_val"


# ===========================================================================
# ⛔ THE PAGE OVER TCP — «what the user sees»
# ===========================================================================
# `RCP.md` §4.4-bis, and the reason is the user's: «the page is served anyway,
# and shows the refusal — *attempts exhausted* … whoever was banned by mistake is
# almost always the owner».
#
# ⚠ AND WHAT THIS READING IS **NOT**.  `FASI.md` §01-filo-nudo B8 says «the DOM is
#   read, as for the eight phrases of B7».  Here **the served HTML** is read with
#   a socket, not a DOM built by a browser: it is legitimate because the phrase
#   is written by the server in the body and no script builds it — what the
#   browser would show is exactly this text — ⛔ but it must be said, and it is a
#   `[?]`: it has not been tried with a real browser.
#
# ⛔⭐ AND WHICH SERVER THESE THREE MARKERS SPEAK OF — finding R12.2, lens D of
#    the review of 11 Aug 2026.  It is the most important warning of this part,
#    and it was not there.
#
#    The three markers looked for below — `data-banned="(si|no)"`,
#    `data-remaining-ms="(\d+)"` and the exact substring `attempts exhausted` —
#    are produced **only by the graft**, `01-b3-rcp-innesta.py:1105-1139`.  ⛔ The
#    product server in `src/` says the same thing in another way:
#
#      · `src/pagina.c:257-262` then wrote the notice in Italian, with seven
#        words between «attempts» and «exhausted», so the substring looked for
#        here was NOT there; ⚠ today (`src/pagina.c:403`) it writes «<b>attempts
#        exhausted</b>: three failed login attempts came from this address…»;
#      · the remaining milliseconds **do not appear at all** in the served
#        document: the product already formats them into hours and minutes and
#        throws away the rest;
#      · `data-banned` and `data-remaining-ms` appear **zero times** in
#        `src/pagina.c` and in `src/pagina.html`.
#
# ⛔ CONSEQUENCE, AND IT MUST BE READ BEFORE BELIEVING A RED: the day someone
#    points this bench at the server of `src/`, the three page checks become
#    **red on a server that does ban**, all three together — and the red ends up
#    on the wrong defendant, which is the most expensive defect of this project
#    (`LEZIONI.md` §1.9, seventh guise).
#    ⚠ Before looking in the server, check whether the server is `bsslserver`
#      (the graft) or `remotix` (the product): they are two page formats without
#      a single field in common, and it is error form **E2** — two different
#      measurements under the same label.
#    ⛔ The cure is not here: it is that the two formats become one.  Until they
#      are, this is the line that prevents losing an hour on it.
def _ask_page(address, port, wait, tls):
    """A single request, in the requested dialect.  (raw, error)."""
    bare = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    bare.settimeout(wait)
    s = None
    try:
        bare.connect((address, port))
        if tls:
            # ⭐ What does NOT change: the source address is still chosen by the
            #    kernel.  `wrap_socket` wraps the connection already open, it does
            #    not open another one.
            conf = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            conf.check_hostname = False
            conf.verify_mode = ssl.CERT_NONE  # the certificate is judged by B3
            s = conf.wrap_socket(bare, server_hostname=address)
        else:
            s = bare
        s.settimeout(wait)
        s.sendall(f"GET / HTTP/1.1\r\nHost: {address}:{port}\r\n"
                  f"Connection: close\r\n\r\n".encode())
        pieces = []
        while True:
            d = s.recv(65536)
            if not d:
                break
            pieces.append(d)
        return b"".join(pieces), ""
    except OSError as e:
        # ⛔ And this is an outcome, not an absence: §4.4-bis forbids «a network
        #    error, a silence».  Whoever reads this field must be able to tell
        #    «the page says I am not banned» from «I talked to nobody» — they
        #    are the same face only for whoever does not look.
        return b"", f"{type(e).__name__}: {e}"
    finally:
        try:
            (s or bare).close()
        except OSError:
            pass


def read_page(address, port, wait=5.0, tls=True):
    """Asks for the page over TCP **from that address**, and reads what it says.

    ⛔ The source address is not declared: the kernel chooses it, and it is that
       of the interface one goes out through.  Asking `127.0.0.1` one arrives as
       `127.0.0.1`; asking `192.168.0.2` one arrives as `192.168.0.2`.  ⭐ And the
       server writes in the log **from which** address it received: the
       denominator is read where the thing happens."""
    outside = {"address": address, "state": None, "banned": None,
             "remain_ms": None, "ore": None, "minutes": None,
             "sentence": False, "byte": 0, "failure": "", "tls": tls}
    # ⛔⭐ THE DIALECT OF THE PAGE IS A DIFFERENCE BETWEEN THE TWO SERVERS, and
    #     they are two opposite reds paid for one day apart (11 Aug 2026):
    #
    #       · this function spoke PLAIN HTTP.  Against the graft it worked;
    #         against the PRODUCT the server closed — `ConnectionResetError:
    #         [Errno 104]` from both addresses — because there the TCP port
    #         serves HTTPS (`SPECIFICHE.md` §11.5);
    #       · the cure was to ALWAYS wrap in TLS, and ⛔ it moved the red onto the
    #         other target: `[M]` 11 August evening, against the graft,
    #         `SSLError: [SSL: WRONG_VERSION_NUMBER]` from both addresses —
    #         because `01-b3-rcp-innesta.py` writes the page **in plain text**
    #         (`HTTP/1.1 200 OK` on a bare fd, no TLS line in the whole file).
    #
    # ⚠ In both cases the server was doing the right thing and the bench read a
    #   silence — the seventh guise of `LEZIONI.md` §1.9 — and §4.4-bis forbids
    #   the ban precisely to present itself as «a network error, a silence».
    #
    # ⭐ So the dialect is DECLARED by the caller (from the target), and here there
    #    is the check that says no: if the declared dialect does not answer, the
    #    OTHER one is tried — and if it is the other one that answers, the error
    #    writes it in full, instead of leaving «I talked to nobody».  ⛔ It is the
    #    difference between «the page is not there» and «I am asking for the page
    #    in the wrong language», which without this line look the same.
    raw, failure = _ask_page(address, port, wait, tls)
    if failure:
        other_one, err2 = _ask_page(address, port, wait, not tls)
        if not err2 and other_one:
            outside["failure"] = (
                f"⛔ THE DIALECT IS THE OTHER ONE: asked in "
                f"{'TLS' if tls else 'plain'} it gave «{failure}», and in "
                f"{'plain' if tls else 'TLS'} it answers ({len(other_one)} bytes). "
                f"It is not «the page does not answer»: it is the target declared "
                f"wrongly, and the three page checks below would speak "
                f"of the bench and not of the server")
        else:
            outside["failure"] = failure
        return outside
    outside["byte"] = len(raw)
    body_text = raw.decode("utf-8", errors="replace")
    before = body_text.split("\r\n", 1)[0]
    m = re.match(r"HTTP/1\.[01] (\d{3})", before)
    outside["state"] = int(m.group(1)) if m else None
    body_el = body_text.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in body_text else body_text
    m = re.search(r'data-banned="(si|no)"', body_el)
    if m:
        outside["banned"] = (m.group(1) == "si")
    m = re.search(r'data-remaining-ms="(\d+)"', body_el)
    if m:
        outside["remain_ms"] = int(m.group(1))
    m = re.search(r'id="ore">(\d+)<', body_el)
    if m:
        outside["ore"] = int(m.group(1))
    m = re.search(r'id="minutes">(\d+)<', body_el)
    if m:
        outside["minutes"] = int(m.group(1))
    outside["sentence"] = "attempts exhausted" in body_el
    return outside


# ===========================================================================
# ⛔ THE MODEL OF §4.4-bis, APPLIED TO THE PLAN BEFORE THE WIRE
# ===========================================================================
def simulate(steps):
    """§4.4-bis read as a model, and applied to the plan before running it.

    A single key — **the address** — because the one per user name no longer
    exists (`DECISIONI.md` §1.9).  ⛔ Three different names count three.

    ⚠ The five-minute window is taken here as **always true**: the model assumes
      that all the attempts of a block fit inside it, which is the
      **pessimistic** reading — a longer run would make the ban trigger less,
      never more.  ⭐ It is intended: an optimistic model would let a plan that
      overflows start.

    ⚠ It is a MODEL — my reading of the arbiter, written before measuring —
      not a proof.  It serves two things, and neither of the two is «being
      right»: saying **before** whether the plan stays below threshold, and
      giving every single attempt an expectation instead of an overall one.  If
      the wire refutes it, one of the two is wrong and the bench says **which
      attempt** split them.

    Returns (expected per attempt, peak of the failures per address)."""
    failed, banned_set, peak, outcomes = {}, set(), {}, []
    for p in steps:
        addr = p["address"]
        if p.get("action") == "unblock":
            # ⛔ The unblock resets the WHOLE entry — ban and count — because it
            #    is what `rcp_unblock()` does: `memset` of the entry.
            #
            # ⛔ AND UNTIL 11 AUG 2026 THIS LINE WAS A BELIEF (finding A22): on
            #    an address NOT banned the unblock answers «NON-BANNATO», and
            #    whether it reset the count anyway nobody verified — while the
            #    whole sampling strategy («unblock between one block and the
            #    next») rests on it.
            #    ⭐ Now it is measured, and not from here: `01-b8-prova-ban.c`
            #    section 5 fails twice, calls `rcp_unblock()` on an address that
            #    is NOT banned, and verifies that the third failure does not make
            #    the ban trigger.
            # ⚠ And the symptom of the opposite case (§1.11), if one day it came
            #   back: the failures would pile up between the blocks, and the
            #   samples would start coming back `limiter` — the verdict says
            #   it, and it is the first of the four causes it prints.
            failed[addr] = 0
            banned_set.discard(addr)
            outcomes.append(("UNBLOCK", None, ""))
            continue
        if addr in banned_set:
            outcomes.append(("REJECTED", TOO_MANY_ATTEMPTS, "banned"))
            continue
        if p["case_v"] == "giusta":
            failed[addr] = 0
            outcomes.append(("ADMITTED", None, ""))
            continue
        failed[addr] = failed.get(addr, 0) + 1
        peak[addr] = max(peak.get(addr, 0), failed[addr])
        # ⛔ The third failed one still receives `WRONG_CREDENTIALS` — it is the
        #    one that MAKES the ban trigger, not the first that suffers it.
        #    Whoever expected the refusal already at the third would look for a
        #    defect that is not there.
        outcomes.append(("REJECTED", WRONG_CREDENTIALS, ""))
        if failed[addr] >= THRESHOLD:
            banned_set.add(addr)
    return outcomes, peak


def verify_plan(steps, manner):
    """⛔ The plan is verified BEFORE running it, and if it does not add up one does not start.

    Three modes, because plans are of three natures:

      `sotto-soglia`  no attempt must be blocked, and no address must exceed
                      the BALANCE.  It is the mode of the samples;
      `banna-al-4`    the **fourth** attempt MUST be blocked, and none before:
                      it is the ban run;
      `non-banna`     no attempt blocked **and** at least one address that
                      reaches two failures: it is the reset check, and without
                      the second half it would be satisfied also by a plan that
                      never fails — that is it would prove nothing.
    """
    outcomes, peak = simulate(steps)
    blocked = [i + 1 for i, (_m, mo, _c) in enumerate(outcomes)
                if mo == TOO_MANY_ATTEMPTS]
    line_list = [f"peak of the failures per address: "
             f"{ {k: v for k, v in sorted(peak.items())} or 'none' }",
             f"attempts the model sees blocked: {blocked or 'none'}"]
    if manner == "sotto-soglia":
        ok = not blocked and max(peak.values(), default=0) <= BALANCE
        line_list.append(f"expected: none blocked, and peak ≤ {BALANCE} "
                     f"(threshold {THRESHOLD})")
    elif manner == "banna-al-4":
        ok = blocked == [4]
        line_list.append("expected: ONLY the fourth blocked — the first three go "
                     "through PAM, and the third is the one that MAKES the ban trigger")
    elif manner == "non-banna":
        ok = (not blocked) and max(peak.values(), default=0) >= 2
        line_list.append("expected: none blocked, and at least one address at 2 "
                     "failures (if it did not get there, the check would be "
                     "green by construction)")
    else:
        ok, _ = False, line_list.append(f"unknown mode: {manner}")
    return ok, outcomes, line_list


# ===========================================================================
# The plans
# ===========================================================================
def sample_plan(k, per_case, addresses, username, nonexistent):
    """A block: `per_case` triplets, with the failures alternating between the addresses.

    ⛔ The addresses alternate **between the FAILURES**, not between the steps: only
       the failures move the count of §4.4-bis, and alternating on all the steps
       would leave the alternation at the mercy of where the success falls.

    ⚠ The rotation starts from `k`, so no case stays tied to an address: if one
      day the two paths had different times, the difference would spread over
      all three medians instead of separating one of them."""
    steps, failed = [], 0
    for g in range(per_case):
        for case_v in ROTATIONS[(k + g) % len(ROTATIONS)]:
            addr = addresses[(failed + k) % len(addresses)]
            if case_v != "giusta":
                failed += 1
            steps.append({"case_v": case_v, "address": addr,
                          "label_name": nonexistent if case_v == "nonexistent" else username,
                          "scaldata": k == 0})
    return steps


def piano_ban(addresses, username, names):
    """⛔ THE BAN RUN: three failed with THREE DIFFERENT NAMES, then the RIGHT password.

    ⭐ The fourth attempt **has the right password** and must be refused anyway:
       *«it is the line that tells a ban from a counter, and it is also the
       symptom the user will see — I typed it right and it does not let me in —
       so it is intended and must be tested, not avoided»* (`FASI.md` §01-filo-nudo B8).

    ⛔ All four from the SAME address: the count is per address, and alternating
       here would mean never reaching three."""
    a = addresses[0]
    steps = [{"case_v": "nonexistent", "address": a, "label_name": names[0],
              "scaldata": False},
             {"case_v": "wrong", "address": a, "label_name": username,
              "scaldata": False},
             {"case_v": "nonexistent", "address": a, "label_name": names[2],
              "scaldata": False},
             # ⛔ the fourth: the RIGHT password
             {"case_v": "giusta", "address": a, "label_name": username,
              "scaldata": False}]
    return steps


def reset_plan(addresses, username, nonexistent):
    """⭐ THE CHECK THAT SAYS NO: 2 failed · 1 succeeded · 2 failed.

    *«If the success did not reset, the second block would already have
    triggered»* (`FASI.md` §01-filo-nudo B8).  ⛔ Counting all the failures, the
    **third** — that is the first after the success — would be the one that makes
    the ban trigger on a server that does not reset.

    ⚠ It runs on the SECOND address, and it is not a detail: the first is about
      to be banned, and a check that says «it is not banned» conducted on the
      address that will be banned right after would be unreadable."""
    b = addresses[1]
    return [{"case_v": "wrong", "address": b, "label_name": username, "scaldata": False},
            {"case_v": "nonexistent", "address": b, "label_name": nonexistent, "scaldata": False},
            {"case_v": "giusta", "address": b, "label_name": username, "scaldata": False},
            {"case_v": "wrong", "address": b, "label_name": username, "scaldata": False},
            {"case_v": "nonexistent", "address": b, "label_name": nonexistent, "scaldata": False}]


# ===========================================================================
# The execution
# ===========================================================================
# ⛔ THE TARGET GOES INTO EVERY LINE, and this variable puts it there instead of
#    the twenty points that call `put_out()`.  ⚠ The concrete case is already on
#    disk: `banchi/prodotto/b8-campioni.jsonl` are the samples of the fixed second
#    taken against the PRODUCT on the night of 10 August, and `/media/REMOTIX/src/
#    b8-fatti.jsonl` those taken against the GRAFT.  Same name, same shape,
#    same fields — and no line, in either of the two, says which server
#    answered.  Whoever put them together «to have more samples» would compute
#    the median of two different populations believing they are reducing the noise.
TARGET = {"target": "non claimed", "port": None, "md5": "ignota"}

# ⛔ The lines the log reader looks for, and they are WRITTEN DIFFERENTLY in the two
#    servers: `primary()` fills them from the target's profile.  ⚠ The values
#    below are the graft's and needs only so that the module can be imported: if
#    these stayed against the product, the reader would say «the server said
#    nothing about the ban» on a server that does say it.
R_BAN = {"caricati": "bans loaded:",
         "illeggibile": "COULD NOT READ the ban file",
         "page_v": "TCP page at"}

# ===========================================================================
# ⛔⭐ HOW A PAM VERDICT IS READ IN THE LOG — and why NOT FROM THE END
# ===========================================================================
# *Defect paid for on 12 Aug 2026, and this bench stayed **blind** for a whole
#  recertification run without saying a word.*
#
# ⛔ WHAT HAPPENED.  Here there was:
#
#      last_pam = "admitted" if row.rstrip().endswith("admitted") else "rejected"
#
#    and the line of `rcp.c` really ended with the verdict's word.  Then the cure
#    of `DECISIONI.md` §1.10 (PAM off the single thread) appended to its tail
#    the explanation of the fallback:
#
#      PAM answered: admitted  ⚠ (SYNCHRONOUSLY: no asynchronous hook
#      connected — the thread stood still)
#
#    ⇒ `endswith("admitted")` became **always false**, every answer ended up among
#    the refused — **52 lines, 0 admitted** — `timing_culprit()` could no
#    longer name anyone, and outcome **5** (the leniency written for
#    `pam_faildelay`) no longer applied: B8 gave **1** on a healthy product, with
#    the ban passing in full.
#
# ⛔ THE TWO HALVES OF THE CAUSE, and curing only one brings it back:
#      1. the cure changed a log line that a bench READS;
#      2. the bench was anchored to the **END** of the line — an anchor that
#         **any** addition breaks, and that breaks **silently**.
#
# ⭐ THE SHAPE THAT HOLDS, and it is the one already in the house
#    (`01-p5-registro.py` §«the lines that are counted», and
#    `re.search(r"(-?\d+) addresses caricati", …)` ten lines further down in this
#    very file): one anchors to the **stable piece** of the line — the name of
#    the fact and the word that qualifies it — and leaves free **everything that
#    comes after**.  An explanation appended at the tail, another emoji, a second
#    field: none of these touches it.
#
# ⚠ And `[^:]*` between «answered» and the colon is not a whim: the cure of §1.10
#   wrote a SECOND form of the same line, for the asynchronous road —
#   `rcp.c:2636` (today `rcp.c:7850`), «PAM answered (request 7): admitted  ⭐ …» — which the graft
#   today does not travel but the product will.  An anchor that demanded the
#   colon right after «answered» would be blind to that one, and the blindness
#   would arrive **the day the bench is pointed at the product**.
R_PAM = re.compile(r"PAM answered\b[^:]*:\s*(admitted|refused)\b")
# ⛔ And the line is recognised BEFORE knowing how to read it: «it is not a PAM
#    line» and «it is a PAM line I cannot read» are two different facts, and the
#    second is the one that today cost a run.
R_PAM_LINE = "PAM answered"

# ⛔ How many lines are needed for «all in the same box» to be an accusation and
#    not a chance: below this threshold it is just said.  ⚠ The real run carries
#    about fifty.
SINGLE_CATEGORY_THRESHOLD = 5


# ===========================================================================
# ⛔⭐ THE CLASSIFIER THAT MEASURES ITSELF — E8 applied to a COUNTER
# ===========================================================================
# *Born on 12 Aug 2026, and it counts more than the cure of the anchor above.*
#
# ⛔ The judge counted **52 lines and 0 admitted** without anything shouting.
#    The number was there, it was printed, and it was absurd — and nobody looked
#    at it because no line said it was absurd.
#
# ⛔ It is form **E8** of `REVIEWER.md` §2 — *«empty» and «forbidden» look the
#    same* — moved from reading to **counting**: when a classifier puts
#    **everything** in a single box, «the facts really are all the same» and «I
#    can no longer read the facts» look the same.  And between the two, the
#    second is almost always the true one.
#
# ⭐ THE RULE, and it holds for any counter of this bench: if the boxes are more
#    than one and the facts are enough, **at least two boxes must be
#    inhabited**.  If only one is inhabited, the first defendant is the
#    classifier — `REVIEWER.md` §1: *the bench is the first defendant*.
#
# ⚠ And the three outcomes are three, not two: «no fact» is not «all in the same
#   box», and it is exactly the distinction E8 asks for.
def all_in_cell(topic, cells, minimum=SINGLE_CATEGORY_THRESHOLD):
    """(suspicious, lines) — suspicious=True when ONE single box is inhabited.

    `cells` is {name: how many}.  ⛔ It does not judge the facts: it judges
    **whoever put them in the boxes**, which is the only defendant no other check
    of this file looks at."""
    tot = sum(cells.values())
    count = " · ".join(f"{k}: {v}" for k, v in cells.items())
    if tot == 0:
        return False, [f"⚠ {topic}: NO fact to classify ({count}) — "
                       f"and «no fact» is not «all the same»"]
    occupied = [k for k, v in cells.items() if v]
    if len(occupied) > 1 or tot < minimum:
        return False, [f"⚠ {topic}: {count} (out of {tot})"]
    return True, [
        f"⛔ {topic}: EVERYTHING IN ONE SINGLE BOX — {count} (out of {tot}), and "
        f"the only inhabited one is «{occupied[0]}»",
        f"⛔ a classifier that out of {tot} facts puts **not even one** "
        f"in the other {len(cells) - 1} boxes is almost always wrong: "
        f"the first defendant is the BENCH, not the server (`REVIEWER.md` §1)",
        f"⛔ and it is form E8 — «empty» and «forbidden» look the same — "
        f"applied to a counter: «the facts are all the same» and «I can no longer "
        f"read the facts» here have the same face",
        f"⚠ to look at first: the anchor with which the log line is "
        f"read.  On 12 Aug 2026 an explanation appended at the tail of "
        f"«PAM answered: admitted» was enough to put 52 out of 52 in the "
        f"wrong box, and B8 went from 5 to 1 on a healthy product",
    ]


def put_out(out_dir, rec):
    """One line per fact, written and **synced** right away.

    ⚠ A file written and closed is a fact; a line in a buffer is a hope about
      the moment someone will see it (`LEZIONI.md` §1.9, seventh guise) — and
      this process dies and is reborn at every phase."""
    outside = dict(TARGET)
    outside.update(rec)
    with open(out_dir, "a") as f:
        f.write(json.dumps(outside, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def existence(label_name, must_exist):
    """⛔ «User does not exist» is VERIFIED, not assumed.

    If the name we believe nonexistent were a real user, «nonexistent» and
    «wrong» would be **the same case** measured twice, and the two medians
    would coincide by construction: the emptiest green of all."""
    try:
        pwd.getpwnam(label_name)
        c_e = True
    except KeyError:
        c_e = False
    return c_e == must_exist, c_e


async def test_addresses(addresses, port):
    """⛔ Can the bench talk from BOTH addresses? — it is asked first.

    ⚠ It gets to `HERE_I_AM` and closes: no `CREDENTIALS`, so **no count moves**
      and no place is taken.  It is a check that costs nothing to the balance of
      §4.4-bis."""
    for addr in addresses:
        handler = None
        try:
            handler, cli, state = await open_it(addr, port)
            if state != "200":
                raise RuntimeError(f":status={state}")
            cli.open_control()
            cli.send_it(wrap(b3.T["HELLO"], b3.body_hello()))
            await b3.should_wait(cli, "HERE_I_AM", wait=10)
        except Exception as e:  # noqa: BLE001
            print(f"    {RED}NO{GRAY}  ⛔ from «{addr}» one does not get to HERE_I_AM: "
                  f"{type(e).__name__}: {e}")
            print(f"        the server must be running on 0.0.0.0 and answering "
                  f"on both addresses, or the balance of §4.4-bis does not "
                  f"have the margin it declares (B0.3)")
            return False
        finally:
            if handler is not None:
                try:
                    await handler.__aexit__(None, None, None)
                except Exception:  # noqa: BLE001
                    pass
    print(f"    {GREEN}OK{GRAY}  the server answers on both "
          f"addresses: {', '.join(addresses)}  (up to HERE_I_AM, without touching "
          f"any count)")
    return True


async def execute(a, steps, kind, label, manner, compare_model=True):
    """Runs an already verified plan, and writes one record per attempt.

    ⚠ `compare_model=False` for the only case in which the model **cannot**
      know the answer: the attempt after the server restart, where the ban
      arrives from DISK and not from the failures of this run.  Demanding there
      agreement with the model would give red on the right code, and the red
      would end up on the wrong defendant — which is the defect `LEZIONI.md`
      §1.9 calls the seventh guise."""
    ok, outcomes, line_list = verify_plan(steps, manner)
    print(f"    -- plan of «{label}»: {len(steps)} attempts, mode «{manner}» "
          f"(threshold {THRESHOLD}, balance {BALANCE}, window {WINDOW_MIN} min)")
    for r in line_list:
        print(f"       {r}")
    if not ok:
        print(f"    {RED}NO{GRAY}  ⛔ the plan does not do what it must: it does not start. "
              f"A plan that overflows would measure the ban believing it measures PAM; "
              f"one that does not ban where it must would make the check blind")
        return 2
    for i, p in enumerate(steps, 1):
        password = a.password if p["case_v"] == "giusta" else a.wrong
        expected_msg, expected_reason, _why = outcomes[i - 1]
        rec = await attempt(p["address"], a.port, p["label_name"], password)
        rec.update({"lap": a.lap, "kind": kind, "label": label,
                    "block": a.block, "order": i, "case_v": p["case_v"],
                    "scaldata": p["scaldata"],
                    "cls_name": ranking(rec, p["case_v"]),
                    # ⭐ the model's expectation travels with the attempt: the
                    #    verdict compares it with what arrived, one by one,
                    #    instead of looking only at the total.
                    "atteso_modello": expected_msg,
                    "expected_reason": expected_reason})
        put_out(a.out_dir, rec)
        ms = "  —  " if rec["ms"] is None else f"{rec['ms']:8.1f}"
        motivo = REASONS.get(rec["motivo"], "") if rec["motivo"] is not None else ""
        expected_val = REASONS.get(expected_reason, expected_msg)
        closes = "" if rec["closure"] is None else \
            f"closure={REASONS.get(rec['closure'], hex(rec['closure']))}"
        if not compare_model:
            agrees = "⚠ the model does not judge here (the ban comes from disk)"
        elif rec["message"] == expected_msg and rec["motivo"] == expected_reason:
            agrees = ""
        else:
            agrees = f"⛔ the model said {expected_val}"
        mark = "warm-up" if p["scaldata"] else ""
        print(f"       {i:2d}. {p['case_v']:12s} {p['address']:13s} "
              f"{p['label_name']:16s} {ms} ms  "
              f"{rec['message'] or rec['failure']:10s} {motivo:18s} "
              f"{rec['cls_name']:10s} {closes} {mark} {agrees}")
    return 0


def page_in_tls(a):
    """⛔ In which language the ban page speaks, on THIS target.

    graft   in plain text — `01-b3-rcp-innesta.py` writes `HTTP/1.1 200 OK` on a
              bare fd, and in the whole file there is not one TLS line;
    product  in TLS — `SPECIFICHE.md` §11.5, and `01-p1-prodotto.sh`
              queries it with `curl -k https://`.

    ⚠ AND THE RIGHT PLACE FOR THIS LINE IS NOT HERE: it is the shared profile
      (`01-b0-bersaglio.py`), next to the other differences between the two
      servers — the start-up line about the ban, the page format, the
      inactivity cap.  It is written here because on the evening of 11 Aug 2026
      three other benches are using the profile, and a new key is added when
      nobody else is inside.  ⛔ As long as it is here, it is a fifth copy of a
      difference — that is exactly the shape R12C.5 has already made us pay
      for: it is read from the profile as soon as the key exists."""
    return bool(a.prof.get("pagina_tls", a.target == "product"))


def look_page(a, address, label, expected_banned):
    """The page, read and WRITTEN in the facts file — and compared right away."""
    rec = read_page(address, a.port, tls=page_in_tls(a))
    rec.update({"lap": a.lap, "kind": "page_v", "label": label,
                "expected_banned": expected_banned})
    put_out(a.out_dir, rec)
    if rec["failure"]:
        print(f"    {RED}NO{GRAY}  ⛔ the page from «{address}» did not "
              f"load: {rec['failure']}")
        print(f"        §4.4-bis: «not a network error, not a silence» — and "
              f"a silence is exactly what I have just received")
        return rec
    how_much = "" if rec["ore"] is None else f" · {rec['ore']}h {rec['minutes']}m left"
    print(f"    -- page from {address:13s} → HTTP {rec['state']} · "
          f"banned={rec['banned']} (expected {expected_banned}) · "
          f"«attempts exhausted» {'present' if rec['sentence'] else 'ABSENT'}"
          f"{how_much} · {rec['byte']} bytes")
    return rec


def unblock_and_declare(a, addresses, reason_text, require=None):
    """⛔ Every unblock is declared — B0.3: «or *the ban did not trigger* and
    *someone removed it* look the same»."""
    outcomes = []
    for addr in addresses:
        outcome, detail = cmd.unblock(a.command, addr)
        rec = {"lap": a.lap, "kind": "sblocco", "label": reason_text,
               "address": addr, "outcome": outcome, "detail": detail,
               "preteso": require}
        put_out(a.out_dir, rec)
        color = RED if outcome is None else GRAY
        print(f"    {color}--{GRAY}  unblock «{addr}» ({reason_text}): "
              f"{outcome or '⛔ I DID NOT TALK TO THE COMMAND'} — {detail}")
        outcomes.append(outcome)
    return outcomes


# ===========================================================================
# The statistics
# ===========================================================================
def quantile(xs, q):
    y = sorted(xs)
    if not y:
        return float("nan")
    i = min(len(y) - 1, max(0, int(round(q * (len(y) - 1)))))
    return y[i]


def mad(xs):
    """Median absolute deviation: the dispersion of the median's family."""
    if len(xs) < 2:
        return float("nan")
    m = statistics.median(xs)
    return statistics.median([abs(x - m) for x in xs])


def interval_difference(xa, xb):
    """The 95 % interval of the difference between the two medians, by resampling.

    ⭐ The seed is fixed: two runs of the verdict on the same samples must give
       the **same** line, or the bench itself becomes a source of noise."""
    r = random.Random(SEED)
    na, nb = len(xa), len(xb)
    diff = []
    for _ in range(REPETITIONS):
        ca = [xa[r.randrange(na)] for _ in range(na)]
        cb = [xb[r.randrange(nb)] for _ in range(nb)]
        diff.append(statistics.median(ca) - statistics.median(cb))
    diff.sort()
    lo = diff[int(0.025 * REPETITIONS)]
    hi = diff[min(REPETITIONS - 1, int(0.975 * REPETITIONS))]
    return lo, hi


# ===========================================================================
# The server log: the second witness, and it is NOT the arbiter
# ===========================================================================
def read_log(fpath):
    """What the SERVER says — to separate the defendants, not to judge.

    ⛔ It is not the arbiter: the time that counts is the one read from the
       receiving side, and the log is the same hand that wrote the code.  It
       serves to distinguish «what governed was the fixed delay» from «what
       governed was PAM», and to say how many server lives and which addresses
       there really were.

    ⚠ If the log is not there or says nothing, nothing is invented: it is declared.
      «Empty» and «not read» are two different facts."""
    if not fpath or not os.path.exists(fpath):
        return None, "the server log was not read (missing file)"
    d = {"fissi": [], "allowed": [], "respinti": [], "senza_pam": [],
         "addresses": set(),
         "avvii": [], "ban": [], "sbloccati": [], "non_bannati": [],
         "pages": [], "carichi": [], "unreadable": 0, "vite": 0,
         # ⛔ The three boxes of the CLASSIFIER, counted separately from the medians:
         #    they needs to judge whoever reads, not what was read.
         "pam": {"admitted": 0, "refused": 0, "illeggibile": 0},
         "pam_esempi": []}
    last_pam = None
    try:
        with open(fpath, errors="replace") as f:
            for row in f:
                if R_PAM_LINE in row:
                    # ⛔ The anchor is on the STABLE piece, not on the end of the
                    #    line: what comes after the verdict's word belongs to
                    #    whoever writes the log, and it changes (12 Aug 2026).
                    m = R_PAM.search(row)
                    if m:
                        last_pam = m.group(1)
                        d["pam"][last_pam] += 1
                    else:
                        # ⛔ AND HERE ONE DOES NOT FALL BACK ON «refused».  Until 12
                        #    Aug 2026 an unreadable line and a refused one were the
                        #    same fact — E8 — and this `None` is the cure: a verdict
                        #    that was not understood enters neither of the two
                        #    medians, and it is counted.
                        last_pam = None
                        d["pam"]["illeggibile"] += 1
                        if len(d["pam_esempi"]) < 3:
                            d["pam_esempi"].append(row.strip()[:150])
                elif "the fixed second has passed" in row:
                    # ⚠ Here too the anchor is the stable piece — «(N ms)» —
                    #   and not «what comes after the first parenthesis».
                    m = re.search(r"\((-?\d+) ms\)", row)
                    if not m:
                        continue
                    n = int(m.group(1))
                    d["fissi"].append(n)
                    if last_pam == "admitted":
                        d["allowed"].append(n)
                    elif last_pam == "refused":
                        d["respinti"].append(n)
                    else:
                        d["senza_pam"].append(n)
                elif " da=" in row and ("rejected motivo" in row or "admitted username" in row):
                    # ⛔ AND NOT EVEN THIS ONE IS READ FROM THE END.  It was
                    #    `row.rsplit(" da=", 1)[1].strip().rsplit(":", 1)[0]`,
                    #    that is «the address is the last thing on the line»: the
                    #    same anchor that today blinded the PAM verdict, on a line
                    #    that `rcp.c:979` and `rcp.c:2700` may lengthen tomorrow as
                    #    they lengthened that one.  ⇒ The `da=` field is taken and
                    #    it stops at the first space.
                    m = re.search(r"\bda=(\S+)", row)
                    if m:
                        d["addresses"].add(m.group(1).rsplit(":", 1)[0])
                elif R_BAN["caricati"] in row:
                    d["vite"] += 1
                    # ⛔⭐ AND THE START-UP LINE IS WRITTEN DIFFERENTLY IN THE TWO SERVERS.
                    #
                    #     graft   «REMOTIX B3: bans loaded: N»
                    #               (logs saved before 10 Oct 2026:
                    #               «ban caricati: N», still read)
                    #     product  «HH:MM:SS.mmm avvio  ban: <file>, N
                    #               addresses loaded»
                    #
                    #  ⚠ Looking for the graft's form against the product would
                    #    have given «vite = 0» and «the server said NOTHING about
                    #    the ban at start-up»: a full red on a server that does
                    #    write that line, and the red would have ended up on the
                    #    wrong defendant.
                    m = re.search(r"(-?\d+) addresses loaded", row) or \
                        re.search(r"(?:bans loaded|ban caricati): (-?\d+)", row)
                    d["carichi"].append(int(m.group(1)) if m else None)
                    d["avvii"].append(row.strip())
                elif R_BAN["illeggibile"] in row:
                    d["vite"] += 1
                    d["unreadable"] += 1
                    d["avvii"].append(row.strip())
                elif "BANNED address" in row and "UNBLOCKED" not in row:
                    d["ban"].append(row.strip())
                elif "UNBLOCKED on command" in row:
                    d["sbloccati"].append(row.strip())
                elif "it was NOT banned, I removed nothing" in row:
                    d["non_bannati"].append(row.strip())
                elif R_BAN["page_v"] in row:
                    d["pages"].append(row.strip())
    except OSError as e:
        return None, f"the server log cannot be read: {e}"
    d["addresses"] = sorted(d["addresses"])
    if not d["fissi"] and not d["avvii"]:
        return None, ("the log is there but contains neither «the fixed second "
                      "has passed» lines nor start-up lines: either it is not the "
                      "log of this run, or the server is not the one with RCP grafted")
    return d, ""


# ===========================================================================
# ⛔⭐ WHO GOVERNS THE TIMES — and it is MEASURED, not written in the verdict's text
# ===========================================================================
# *Finding A18 of review R12-A, 11 Aug 2026.*  Until tonight this answer was
# **a constant sentence**: whichever pair of medians separated — and for
# whatever reason — the verdict printed *«what governs the times is PAM, and the
# cure is in `autenticazione.c` and in the PAM stack, not in `rcp.c`»*.  The
# number that should have supported it was computed two lines above and
# **conditioned nothing**; with the log unreadable it became *«after a median
# of None ms … what governs the times is PAM»*.
#
# ⛔ A verdict that always names the same defendant is not diagnosing: it is
#    repeating a belief.  And it is the **seventh guise** of `LEZIONI.md` §1.9
#    — *the red pointed at the wrong defendant* — inside the bench that quotes
#    that lesson: it sends to look in `autenticazione.c` and in the PAM stack
#    anyone who slowed down **our path**, and the more plausible the place the
#    longer one stays there.
#
# ⭐ THE CONCRETE CASE THAT SHOWED IT (`[M]` 11 Aug 2026, reproduced on facts
#    built by hand): two seconds of our own work are put on the path of the
#    `ADMITTED` — a slow `getpwnam`, a synchronous write — and PAM is left to
#    answer in 5 ms.  The server log says «the fixed second has passed» at
#    **1005 ms on the refused and 1010 on the admitted**, that is the fixed delay
#    covered everything and PAM delayed nothing; the pair «sbagliata − giusta»
#    separates by two seconds **because of us**; and the old verdict handed over
#    «it is PAM, the cure is elsewhere».
#
# ⛔ THE RULE, AND IT IS §1.11: for every indirect proof one writes what the
#    opposite case would look like.  Here the two opposite cases have **two
#    different numeric signatures in the server log**, and this function reads them:
#
#      PAM delays the failures    the server waits WELL beyond the fixed second
#      (`pam_faildelay`)          before answering the REFUSED, and little or
#                                 nothing before the ADMITTED  ⇒  refused ≫ 1000
#                                 and refused ≫ admitted, and the slow case on the
#                                 wire is one of the two refused
#      the delay is OURS          the server declares it answered almost right
#                                 after the fixed second (refused ≈ admitted
#                                 ≈ 1000) and the medians separate all the
#                                 same — or it is the ADMITTED that is slow,
#                                 which is the path where PAM has no say
#
# ⛔ And the third outcome is «I do not know», which is what the old verdict did
#    not have: without the log nobody is named.
def timing_culprit(series, reg):
    """(name, lines) with name in «PAM» · «OUR» · None (not measured)."""
    line_list = []
    if reg is None:
        return None, ["⛔ the server log was not read: NO "
                      "defendant can be named, and naming one anyway "
                      "would be the seventh guise of `LEZIONI.md` §1.9"]
    resp = statistics.median(reg["respinti"]) if reg["respinti"] else None
    accepted = statistics.median(reg["allowed"]) if reg["allowed"] else None
    if resp is None or accepted is None:
        # ⛔ AND HERE IT ALSO SAYS WHY — 12 Aug 2026.  Until this morning this
        #    line stopped at «the log does not carry the two medians», which
        #    reads as *«the server did not write them»*.  ⛔ But the case that
        #    really showed up is the other one — **it wrote them, and it is I who
        #    can no longer read them** — and the two look the same (E8).  Whoever
        #    reads the verdict must find the first defendant here.
        line_list = [f"⛔ the log does not carry the two medians that are needed "
                 f"(refused: {len(reg['respinti'])} lines · admitted: "
                 f"{len(reg['allowed'])} lines): without both one cannot "
                 f"tell «PAM delays the failures» from «the delay is "
                 f"ours», and nobody is named"]
        _, blind_lines = all_in_cell(
            "and the classification that fills them", reg["pam"])
        line_list += blind_lines
        return None, line_list
    med = {c: statistics.median(series[c]) for c in CASES if series[c]}
    if not med:
        return None, ["⛔ no series of samples: there is no "
                      "separation to attribute"]
    slow = max(med, key=med.get)
    excess_r, excess_a = resp - FIXED_DELAY, accepted - FIXED_DELAY
    line_list.append(f"what the SERVER declares it waited beyond the "
                 f"fixed second: refused {excess_r:+.0f} ms · admitted "
                 f"{excess_a:+.0f} ms  (margin {BLAME_MARGIN:.0f} ms)")
    line_list.append(f"the slowest case on the WIRE: «{slow}» "
                 f"({med[slow]:.0f} ms)  ·  " +
                 " · ".join(f"{c} {med[c]:.0f}" for c in CASES if c in med))
    if excess_r >= BLAME_MARGIN and (resp - accepted) >= BLAME_MARGIN \
            and slow != "giusta":
        line_list.append("⇒ ⛔ WHAT GOVERNS THE TIMES IS **PAM**: the server "
                     "waited beyond the fixed second ONLY on the failures, "
                     "which is the signature of `pam_faildelay`, and the slow "
                     "case on the wire is a refused one.  The cure is in "
                     "`banchi/rcp/autenticazione.c` and in the PAM stack, not in "
                     "`rcp.c`")
        return "PAM", line_list
    if slow == "giusta" or (excess_a - excess_r) >= BLAME_MARGIN:
        line_list.append("⇒ ⛔ THE DEFENDANT IS NOT PAM: the slow path is that "
                     "of the ADMITTED, where `pam_faildelay` has no say — "
                     "`pam_faildelay` delays the FAILURES.  The delay is "
                     "OURS, and it is looked for on the path leading to `ADMITTED` "
                     "(rcp.c: `S_WAIT_VERDICT` → `T_ADMITTED`), not in the "
                     "PAM stack")
        return "OUR", line_list
    if excess_r < BLAME_MARGIN and excess_a < BLAME_MARGIN:
        line_list.append("⇒ ⛔ THE DEFENDANT IS NOT PAM: the server declares it "
                     "answered almost right after the fixed second in both "
                     "directions — that is the fixed delay covered everything and "
                     "PAM delayed nothing — and the medians separate "
                     "ALL THE SAME.  The time is lost OUTSIDE the point where the "
                     "server measures it: our path, or the network")
        return "OUR", line_list
    line_list.append("⇒ ⚠ THE NUMBERS DO NOT SEPARATE THE TWO DEFENDANTS: the log says "
                 "that someone waited beyond the fixed second, but not in the "
                 "direction that tells PAM from our path.  Nobody is "
                 "named — «I do not know» is an outcome, «it is PAM» said out "
                 "of habit is not")
    return None, line_list


# ===========================================================================
# The verdict
# ===========================================================================
def _serial(samples, case_v):
    return [r["ms"] for r in samples
            if r["case_v"] == case_v and not r["scaldata"] and r["cls_name"] == "expected_val"]


def verdict(a):
    if not os.path.exists(a.out_dir):
        print(f"    {RED}NO{GRAY}  ⛔ there is nothing to judge: "
              f"{a.out_dir} does not exist")
        return 2
    data_v = []
    with open(a.out_dir) as f:
        for row in f:
            row = row.strip()
            if row:
                data_v.append(current_spelling(json.loads(row)))
    # ⛔ A file from ANOTHER run is not an empty file, and it is not this run.
    stray = [r for r in data_v if r.get("lap") != a.lap]
    if stray:
        print(f"    {RED}NO{GRAY}  ⛔ {len(stray)} lines out of {len(data_v)} are "
              f"from another run: I do not judge a stale file")
        return 2
    if not data_v:
        print(f"    {RED}NO{GRAY}  ⛔ the file is there and it is empty: no facts")
        return 2

    # ⛔ TWO COUNTERS, AND IT IS NOT LENIENCY — it is `LEZIONI.md` §1.11 and the
    #    rule of the «four outcomes, not two».
    #
    #    `faults` counts what this bench has the right to call a defect of OURS.
    #    `fault_medians` counts the only thing §4.4-bis had already declared
    #    `[?]` before this bench existed: that what governs the times of the
    #    authentication **is not our delay, it is PAM**.
    #
    # ⛔ And the difference is not cosmetic: if the two things ended up in the same
    #    number, B8 would be **red forever** — and a bench that is always red makes
    #    no regression fail, because nobody looks at it any more.  ⚠ The separation
    #    of the medians stays printed in full, the outcome stays different from
    #    zero, and the culprit is NAMED: what is removed is the confusion between
    #    «the ban does not work» and «PAM delays the failures», which are two
    #    different cures in two different files.
    faults, fault_medians, on_hold = 0, 0, False
    samples = [r for r in data_v if r["kind"] == "sample"]
    attempts = [r for r in data_v if r["kind"] in ("sample", "ban", "check")]
    pages = [r for r in data_v if r["kind"] == "page_v"]
    unblocks = [r for r in data_v if r["kind"] == "sblocco"]
    blocks = sorted({r["block"] for r in samples})

    # ── 0. the denominators ─────────────────────────────────────────────────
    print()
    print("    == THE DENOMINATORS — on what this run looked")
    print(f"    --  facts recorded: {len(data_v)}  (attempts {len(attempts)} · "
          f"page readings {len(pages)} · unblocks {len(unblocks)})")
    print(f"    --  blocks of samples: {len(blocks)}  "
          f"(between one block and the next one unblocks, and it is declared)")
    # ⛔ And a verdict has a denominator: how many things it approved
    #    (`LEZIONI.md` §1.9 rule 6).  If it is zero no outcome is given.
    if not attempts:
        print(f"    {RED}NO{GRAY}  ⛔ ZERO attempts: «all those tested "
              f"went well» is true even when the tested are zero")
        return 2

    series = {}
    for case_v in CASES:
        case_samples = [r for r in samples if r["case_v"] == case_v]
        warmed = [r for r in case_samples if r["scaldata"]]
        kept = [r for r in case_samples if not r["scaldata"]]
        good_n = [r for r in kept if r["cls_name"] == "expected_val"]
        series[case_v] = [r["ms"] for r in good_n]
        limited = [r for r in kept if r["cls_name"] == "limiter"]
        unexpected = [r for r in kept if r["cls_name"] == "inatteso"]
        errors = [r for r in kept if r["cls_name"] == "failure"]
        per_addr = {}
        for r in good_n:
            per_addr[r["address"]] = per_addr.get(r["address"], 0) + 1
        print(f"    --  {case_v:12s} kept {len(good_n):3d} out of {len(kept):3d} · "
              f"discarded as warm-up {len(warmed)} · "
              f"⛔ ban answers {len(limited)} · unexpected {len(unexpected)} · "
              f"errors {len(errors)} · addresses {per_addr}")
        if limited:
            print(f"    {RED}NO{GRAY}  ⛔ {len(limited)} samples of «{case_v}» "
                  f"received TOO_MANY_ATTEMPTS: the balance of §4.4-bis did not "
                  f"hold, and those times are the BAN's, not PAM's")
            print(f"        ⚠ four causes, and they must be separated: (1) the unblock "
                  f"between the blocks did not work; (2) the plan really overflows; "
                  f"(3) a previous block left some failures; "
                  f"(4) the server counts more than §4.4-bis says")
            faults += 1
        if unexpected or errors:
            print(f"    {RED}NO{GRAY}  ⛔ «{case_v}»: {len(unexpected)} unexpected "
                  f"answers and {len(errors)} errors — a case that does not receive "
                  f"what it must is not a sample of that case")
            for r in (unexpected + errors)[:3]:
                print(f"        {r['message'] or ''} {r['failure']}")
            faults += 1

    # ── 1. the fixed second ─────────────────────────────────────────────────
    print()
    print(f"    == ⛔ First criterion: no PAM answer before "
          f"{FIXED_DELAY:.0f} ms (§4.4-bis)")
    da_pam = [r for r in attempts if r["cls_name"] == "expected_val" and r["ms"] is not None]
    below = [r for r in da_pam if r["ms"] < FIXED_DELAY]
    print(f"    --  looked at {len(da_pam)} answers (samples, warm-ups and ban "
          f"run together: the fixed delay holds for ALL of them, «even when the "
          f"answer is ADMITTED»)")
    if not da_pam:
        print(f"    {RED}NO{GRAY}  ⛔ no answer to look at")
        faults += 1
    elif below:
        print(f"    {RED}NO{GRAY}  ⛔ {len(below)} responses below the second. "
              f"The fastest: {min(r['ms'] for r in below):.1f} ms")
        for r in below[:5]:
            print(f"        {r['case_v']:12s} {r['message']} {r['ms']:.1f} ms")
        faults += 1
    else:
        print(f"    {GREEN}OK{GRAY}  {len(da_pam)} out of {len(da_pam)} ≥ "
              f"{FIXED_DELAY:.0f} ms — the fastest: "
              f"{min(r['ms'] for r in da_pam):.1f} ms")
    # ⚠ And the ban's refusal is measured SEPARATELY, and it makes neither red nor green.
    #   §4.4-bis says that «the refusal of a banned address does not go through the
    #   fixed second»; `rcp.c` makes it go through anyway, because it decides AFTER
    #   having received `CREDENTIALS` — which is the only road that leaves it a
    #   `REJECTED` to send, that is what B8 demands.  Two readings, and the
    #   difference is measured instead of judged.
    del_ban = [r["ms"] for r in attempts
               if r["cls_name"] == "limiter" and r["ms"] is not None]
    if del_ban:
        print(f"    --  ⚠ and the TOO_MANY_ATTEMPTS answers (which do not go through PAM): "
              f"n={len(del_ban)}  median {statistics.median(del_ban):.1f} ms  "
              f"min {min(del_ban):.1f} ms")
        print(f"        §4.4-bis says this refusal «does not go through the fixed "
              f"second»; rcp.c makes it go through.  The number is here, and it is not an "
              f"outcome: it is a defect of the document to be closed in one direction or "
              f"the other")
    else:
        print(f"    --  ⛔ no TOO_MANY_ATTEMPTS answer in the whole run: the "
              f"ban run below cannot have passed")

    # ── 2. the three medians ────────────────────────────────────────────────
    print()
    print("    == ⛔ Second criterion: the three medians, and whether they separate")
    for case_v in CASES:
        x = series[case_v]
        if not x:
            print(f"    --  {case_v:12s} n=0 — no samples")
            continue
        print(f"    --  {case_v:12s} n={len(x):3d}  min {min(x):8.1f}  "
              f"p25 {quantile(x, .25):8.1f}  median {statistics.median(x):8.1f}  "
              f"p75 {quantile(x, .75):8.1f}  max {max(x):8.1f}  "
              f"MAD {mad(x):6.1f}   (ms)")

    lean = [c for c in CASES if len(series[c]) < MIN_SAMPLES]
    if lean:
        print(f"    {YELLOW}??{GRAY}  ⚠ fewer than {MIN_SAMPLES} samples for "
              f"{', '.join(lean)}: the verdict on the medians is SUSPENDED, not green")
        on_hold = True

    print()
    print("    difference of the medians, with the 95 % interval that contains it:")
    for u, v in (("nonexistent", "wrong"), ("nonexistent", "giusta"),
                 ("wrong", "giusta")):
        xa, xb = series[u], series[v]
        if len(xa) < 3 or len(xb) < 3:
            print(f"    {YELLOW}??{GRAY}  {u} − {v}: insufficient samples "
                  f"({len(xa)} and {len(xb)})")
            on_hold = True
            continue
        d = statistics.median(xa) - statistics.median(xb)
        lo, hi = interval_difference(xa, xb)
        resolution = (hi - lo) / 2.0
        contains_zero = lo <= 0.0 <= hi
        n_now = min(len(xa), len(xb))
        n_needs = int(n_now * (resolution / WANTED_RESOLUTION) ** 2) + 1
        mark = f"{RED}DISTINGUISHABLE{GRAY}" if not contains_zero else (
            f"{GREEN}indistinguishable{GRAY}" if resolution <= WANTED_RESOLUTION
            else f"{YELLOW}SUSPENDED{GRAY}")
        secret = (u, v) == ("nonexistent", "wrong")
        remark = "  ⚠ THIS is the pair that tells the user names" if secret \
            else "  (⚠ this pair carries no secret: see below)"
        print(f"      {u:12s} − {v:12s} {d:+9.1f} ms   "
              f"[{lo:+8.1f}; {hi:+8.1f}]   resolution ±{resolution:.1f} ms   "
              f"{mark}{remark}")
        if not contains_zero:
            # ⛔⭐ AND HERE THE THREE PAIRS ARE NOT WORTH THE SAME, AND IT IS A POINT
            #    WHERE THE DOCUMENTS ALLOW TWO READINGS.
            #
            #    `FASI.md` §01-filo-nudo B8 asks for **the three medians
            #    indistinguishable**, and §4.4-bis wants the fixed delay «even
            #    when the answer is AMMESSO».  ⚠ But what §4.4 FORBIDS letting be
            #    known is one thing only: whether a user name exists — «the
            #    server MUST NOT distinguish in the reason between user does not
            #    exist and wrong password».
            #
            #    ⛔ «Admitted» against «refused», instead, the wire says by itself:
            #       they are two different MESSAGES, `ADMITTED` and `REJECTED`.  A
            #       stopwatch that separates them adds nothing to what the client
            #       already reads in the message.
            #
            # ⭐ So: the pair «inesistente − sbagliata» that separates is a defect
            #    of OURS and goes into full red.  The other two that separate go
            #    into their own counter, which leads to a different outcome with
            #    the culprit named.  ⚠ The convenient reading is not chosen and
            #    nothing is kept quiet: both are run and it is said which number
            #    belongs to which.
            if secret:
                print(f"           ⛔ AND THIS IS THE SEPARATION §4.4 FORBIDS: "
                      f"with the stopwatch one reads whether a user name exists, which is "
                      f"exactly the thing the ban on the reason exists to "
                      f"hide")
                faults += 1
            else:
                print(f"           ⚠ this separation says NOTHING the "
                      f"wire does not already say: «admitted» and «refused» are two "
                      f"different MESSAGES (§4.4).  It counts anyway — "
                      f"`FASI.md` §01-filo-nudo B8 asks for the THREE medians "
                      f"indistinguishable — but in its own counter, and with the culprit "
                      f"named at the end")
                fault_medians += 1
        elif resolution > WANTED_RESOLUTION:
            print(f"           ⚠ to get to ±{WANTED_RESOLUTION:.0f} ms with "
                  f"this noise ~{n_needs} samples per case would be needed "
                  f"(now {n_now})")
            on_hold = True

    # ── 3. the ban run ──────────────────────────────────────────────────────
    print()
    print("    == ⛔ The ban: three failed with THREE DIFFERENT NAMES, then the RIGHT password")
    lap = sorted([r for r in data_v if r["kind"] == "ban"], key=lambda r: r["order"])
    if len(lap) != 4:
        print(f"    {RED}NO{GRAY}  ⛔ the ban run has {len(lap)} attempts "
              f"instead of 4: it is not the sequence §4.4-bis describes")
        faults += 1
    else:
        def label_of(msg, motivo):
            return REASONS.get(motivo, str(motivo)) if motivo is not None else (msg or "failure")
        print(f"        names:    " + " ".join(f"{r['label_name']:18s}" for r in lap))
        print(f"        model:    " + " ".join(
            f"{label_of(r['atteso_modello'], r['expected_reason']):18s}" for r in lap))
        print(f"        on wire:  " + " ".join(
            f"{label_of(r['message'], r['motivo']):18s}" for r in lap))
        # ⛔ THE THREE NAMES MUST BE DIFFERENT, and the bench compares it.
        names = [r["label_name"] for r in lap[:3]]
        if len(set(names)) != 3:
            print(f"    {RED}NO{GRAY}  ⛔ the three names are not different ({names}): "
                  f"with the same name three times a server with the old per-NAME "
                  f"counter would give green, and the bench would prove the wrong "
                  f"rule")
            faults += 1
        else:
            print(f"    {GREEN}OK{GRAY}  the three names are different: the count "
                  f"looks at the address and not at the name (`DECISIONI.md` §1.9)")
        divergent = [r["order"] for r in lap
                      if r["message"] != r["atteso_modello"]
                      or r["motivo"] != r["expected_reason"]]
        if divergent:
            print(f"    {RED}NO{GRAY}  ⛔ the wire and the model of §4.4-bis "
                  f"split at attempts {divergent}")
            faults += 1
        fourth = lap[3]
        if fourth["motivo"] == TOO_MANY_ATTEMPTS:
            print(f"    {GREEN}OK{GRAY}  ⭐ the FOURTH attempt had the RIGHT "
                  f"password and was refused anyway, with "
                  f"TOO_MANY_ATTEMPTS: it is the line that tells a ban from a "
                  f"counter")
        else:
            print(f"    {RED}NO{GRAY}  ⛔ the fourth attempt — RIGHT password — "
                  f"received {label_of(fourth['message'], fourth['motivo'])} "
                  f"instead of TOO_MANY_ATTEMPTS")
            print(f"        ⚠ and if it is ADMITTED, the ban did not trigger: look at the "
                  f"server log below, line «BANNED address»")
            faults += 1
        # ⛔ And the tab already open: the reason travels ALSO in the session
        #    closing code (§3.1 point 3, §4.4-bis point 2), and it is verified
        #    FROM THE RECEIVING SIDE.
        if fourth.get("closure") == TOO_MANY_ATTEMPTS:
            print(f"    {GREEN}OK{GRAY}  ⭐ and the WebTransport session "
                  f"closed with TOO_MANY_ATTEMPTS in the application error "
                  f"code — read from the receiving side (§3.1 point 3)")
        else:
            c = fourth.get("closure")
            print(f"    {RED}NO{GRAY}  ⛔ the session closing code "
                  f"is {REASONS.get(c, c)}, not TOO_MANY_ATTEMPTS: the tab already "
                  f"open — the one that does not reload the page — would stay "
                  f"waiting (§4.4-bis point 2)")
            faults += 1

    # ── 4. the three checks that say NO ─────────────────────────────────────
    print()
    print("    == ⭐ The three checks that say NO")

    # 4a. another address gets in right away
    other_one = [r for r in data_v if r["kind"] == "check"
             and r["label"] == "altro-indirizzo"]
    if not other_one:
        print(f"    {RED}NO{GRAY}  ⛔ the check «another address gets "
              f"in» is missing: without it, «the fourth is refused» is compatible with a "
              f"server that stopped working")
        faults += 1
    elif all(r["message"] == "ADMITTED" for r in other_one):
        print(f"    {GREEN}OK{GRAY}  1. ANOTHER address gets in right away with the "
              f"good credentials ({len(other_one)} attempts): the server has not "
              f"stopped working, and the count is per address")
    else:
        print(f"    {RED}NO{GRAY}  ⛔ 1. the other address does NOT get in: "
              f"{[r['message'] for r in other_one]}")
        print(f"        ⚠ four causes: (1) the ban is not per address — the "
              f"defect; (2) that address has a count of its own open; (3) PAM does not "
              f"allow verifying that user; (4) the user does not exist or "
              f"has no password")
        faults += 1

    # 4b. the reset
    azz = sorted([r for r in data_v if r["kind"] == "check"
                  and r["label"] == "azzeramento"], key=lambda r: r["order"])
    if len(azz) != 5:
        print(f"    {RED}NO{GRAY}  ⛔ 2. the reset check has "
              f"{len(azz)} attempts instead of 5")
        faults += 1
    else:
        reasons = [r["motivo"] for r in azz]
        blocked = [r["order"] for r in azz if r["motivo"] == TOO_MANY_ATTEMPTS]
        if not blocked and azz[2]["message"] == "ADMITTED":
            print(f"    {GREEN}OK{GRAY}  2. two failed · ONE SUCCEEDED · two "
                  f"failed: no block.  If the success did not reset, the "
                  f"third failed one would have made the ban trigger")
        else:
            print(f"    {RED}NO{GRAY}  ⛔ 2. the reset did not happen "
                  f"(blocked: {blocked or 'none'}; the third step "
                  f"received {azz[2]['message']})")
            faults += 1
        # ⛔ And the check of the check: the page must say that address is NOT
        #    banned.  Without it, «no block» would be compatible with a server
        #    that banned and does not say so.
        after = [r for r in pages if r["label"] == "azzeramento-dopo"]
        if after and after[0].get("banned") is False:
            print(f"        ⭐ and the page confirms it from outside: that address "
                  f"is not banned (the count is {len([m for m in reasons if m == WRONG_CREDENTIALS])} "
                  f"out of {THRESHOLD})")
        elif after:
            print(f"    {RED}NO{GRAY}  ⛔ but the page says banned="
                  f"{after[0].get('banned')}: the wire and the page do not agree")
            faults += 1

    # 4c. persistence
    print()
    before = [r for r in pages if r["label"] == "bannato-prima"]
    after = [r for r in pages if r["label"] == "bannato-dopo-riavvio"]
    wire_after = [r for r in data_v if r["kind"] == "check"
                 and r["label"] == "dopo-riavvio"]
    if not before or not after:
        print(f"    {RED}NO{GRAY}  ⛔ 3. persistence was not proved "
              f"(page before: {len(before)}, after the restart: {len(after)}): "
              f"without it, the ban may live in memory and a package update "
              f"gives three attempts to anyone — invariant I7")
        faults += 1
    elif after[0].get("banned") is True and wire_after and \
            all(r["motivo"] == TOO_MANY_ATTEMPTS for r in wire_after):
        print(f"    {GREEN}OK{GRAY}  3. the ban SURVIVES the restart of the "
              f"server: after the second start the page still says it, and "
              f"on the wire the attempt with the right password still receives "
              f"TOO_MANY_ATTEMPTS")
    else:
        print(f"    {RED}NO{GRAY}  ⛔ 3. after the restart the address is no "
              f"longer banned: page banned={after[0].get('banned')}, on the wire "
              f"{[REASONS.get(r['motivo'], r['message']) for r in wire_after]}")
        faults += 1

    # ── 5. what the user sees ───────────────────────────────────────────────
    print()
    print("    == ⛔ What the user sees: the page loads ANYWAY")
    # ⛔ And it is declared what this reading is NOT, here and not only in the
    #    comments: whoever reads a verdict reads the verdict.
    print(f"    --  `[?]` read with a socket, not with a browser: the phrase is "
          f"written by the server in the body and no script builds it, so "
          f"what a browser would show is this text — ⚠ but a real engine "
          f"has not looked at it, and `FASI.md` §01-filo-nudo B8 asks for the DOM "
          f"«as for the eight phrases of B7»")
    # ⛔ AND WHICH SERVER THESE THREE LINES SPEAK OF — R12.2, and it is printed in the
    #    verdict because whoever reads a verdict reads the verdict.
    print(f"    --  ⛔ the three markers looked for here (`data-banned`, "
          f"`data-remaining-ms`, «attempts exhausted») are produced ONLY by the graft "
          f"of `01-b3-rcp-innesta.py`.  The product server in `src/` writes "
          f"the same thing in a format without a field in common: pointing "
          f"this bench there, these three lines would become red ON A "
          f"SERVER THAT DOES BAN")
    if not pages:
        print(f"    {RED}NO{GRAY}  ⛔ no reading of the page: point 1 "
              f"of §4.4-bis was not proved at all")
        faults += 1
    for r in pages:
        expected_val = r["expected_banned"]
        good_one = (not r["failure"] and r["state"] == 200
                 and r["banned"] is expected_val
                 and (r["sentence"] if expected_val else not r["sentence"]))
        if expected_val and good_one:
            good_one = r["ore"] is not None
        sign = f"{GREEN}OK{GRAY}" if good_one else f"{RED}NO{GRAY}"
        print(f"    {sign}  {r['label']:22s} from {r['address']:13s} → "
              f"HTTP {r['state']} · banned={r['banned']} (expected {expected_val}) · "
              f"sentence={r['sentence']} · ore={r['ore']} minutes={r['minutes']}"
              f"{' · ⛔ ' + r['failure'] if r['failure'] else ''}")
        if not good_one:
            faults += 1
    banned_pages = [r for r in pages if r["expected_banned"] and r["ore"] is not None]
    if banned_pages:
        ore = banned_pages[0]["ore"]
        # ⚠ The hours left must be PLAUSIBLE: 12 right after the ban.  A
        #   «0 hours left» or a «4 billion left» would say that the page's clock
        #   is not the session's — the easiest defect to make and the hardest
        #   to see.
        if 1 <= ore <= BAN_ORE:
            print(f"    {GREEN}OK{GRAY}  and the hours left are plausible "
                  f"({ore} out of {BAN_ORE}): the page's clock is the "
                  f"session's")
        else:
            print(f"    {RED}NO{GRAY}  ⛔ the page says {ore} hours are left, "
                  f"and the ban lasts {BAN_ORE}: the two clocks are not the same")
            faults += 1

    # ── 6. the unblock — and it is tested AT THE END ────────────────────────
    print()
    print("    == ⛔ The unblock command, tested AT THE END (B0.3)")
    final = [r for r in unblocks if r["label"].startswith("prova-")]
    if not final:
        print(f"    {RED}NO{GRAY}  ⛔ the unblock was not tested on a real "
              f"ban: «removed» and «was not there» were not told apart")
        faults += 1
    for r in final:
        good = r["outcome"] == r["preteso"]
        sign = f"{GREEN}OK{GRAY}" if good else f"{RED}NO{GRAY}"
        print(f"    {sign}  {r['label']:22s} «{r['address']}» → "
              f"{r['outcome']} (expected {r['preteso']})")
        if not good:
            faults += 1
    after_unlock = [r for r in data_v if r["kind"] == "check"
                    and r["label"] == "dopo-sblocco"]
    if after_unlock and all(r["message"] == "ADMITTED" for r in after_unlock):
        print(f"    {GREEN}OK{GRAY}  ⭐ and after the unblock that address GETS IN: "
              f"the unblock did not only change an answer, it put the "
              f"address back inside")
    else:
        print(f"    {RED}NO{GRAY}  ⛔ after the unblock the address does not get in "
              f"({[r['message'] for r in after_unlock] or 'not tested'})")
        faults += 1

    # ── 7. the second witness ───────────────────────────────────────────────
    print()
    print("    == ⚠ The server log — diagnosis and denominator, NOT arbiter")
    reg, reason_text = read_log(a.logbook)
    if reg is None:
        print(f"    --  {reason_text}")
        # ⛔ It is not the arbiter, but without it two checks above do not have
        #    their denominator: it is said, instead of pretending nothing.
        print(f"    {YELLOW}??{GRAY}  ⚠ without the log I cannot say how many "
              f"server lives there were nor how many bans it loaded: the "
              f"verdict on persistence is worth less than it seems")
        on_hold = True
    else:
        def med(x):
            return f"{statistics.median(x):.0f} ms" if x else "— (no lines)"
        print(f"    --  server lives in the log: {reg['vite']}  "
              f"(expected 2: one for the samples and the ban, one for persistence)")
        for r in reg["avvii"]:
            print(f"        {r}")
        print(f"    --  «the fixed second has passed»: n={len(reg['fissi'])}  "
              f"median {med(reg['fissi'])}  "
              f"(admitted {med(reg['allowed'])} out of {len(reg['allowed'])} · "
              f"refused {med(reg['respinti'])} out of {len(reg['respinti'])} · "
              f"without a readable verdict: {len(reg['senza_pam'])})")
        # ── ⛔ THE BLIND BENCH MUST SHOW — 12 Aug 2026 ───────────────────────
        #
        # ⛔ The recertification run counted **52 lines and 0 admitted** and
        #    the bench said nothing: it only stopped being able to name the
        #    defendant, and the outcome went from 5 to 1 on a healthy product.
        #    These lines are the check that was missing, and it is a check on the
        #    BENCH, not on the server (`REVIEWER.md` §1).
        blind, blind_lines = all_in_cell(
            "the classification of the PAM answers in the log", reg["pam"])
        for r in blind_lines:
            print(f"    --  {r}")
        for r in reg["pam_esempi"]:
            print(f"        line I could not read: {r}")
        if blind:
            print(f"    {RED}NO{GRAY}  ⛔ THE JUDGE IS BLIND: as long as this "
                  f"line is red no median above counts, because it is not "
                  f"certain it is the median of what it declares to be")
            faults += 1
        elif reg["pam"]["illeggibile"]:
            print(f"    {RED}NO{GRAY}  ⛔ {reg['pam']['illeggibile']} lines "
                  f"«{R_PAM_LINE}» could not be read: the anchor "
                  f"«{R_PAM.pattern}» no longer finds the verdict, and a verdict "
                  f"not read is NOT a refused one (E8)")
            faults += 1
        if reg["senza_pam"]:
            print(f"    {RED}NO{GRAY}  ⛔ {len(reg['senza_pam'])} samples of the "
                  f"fixed second have no PAM verdict before them: they "
                  f"enter neither of the two medians, and before 12 Aug "
                  f"2026 they would all have ended up among the REFUSED silently")
            faults += 1
        print(f"    --  if that number is ~{FIXED_DELAY:.0f} ms what governed "
              f"was the FIXED DELAY; if it is much higher what governed "
              f"was PAM, and a separation between the medians would be PAM's")
        print(f"    --  source addresses seen BY THE SERVER: {reg['addresses']}")
        print(f"    --  «BANNED» lines: {len(reg['ban'])} · «UNBLOCKED on "
              f"command»: {len(reg['sbloccati'])} · «was NOT banned»: "
              f"{len(reg['non_bannati'])} · pages served: {len(reg['pages'])}")
        if len(reg["addresses"]) < 2:
            print(f"    {RED}NO{GRAY}  ⛔ the server saw ONE SINGLE address: "
                  f"the margin of the balance was not there, and the checks that "
                  f"separate the two addresses are not valid (B0.3)")
            faults += 1
        if reg["vite"] < 2:
            print(f"    {RED}NO{GRAY}  ⛔ the log sees {reg['vite']} lives "
                  f"of the server: persistence is proved with a RESTART, and here "
                  f"there was none")
            faults += 1
        elif reg["carichi"] and reg["carichi"][-1] == 1:
            print(f"    {GREEN}OK{GRAY}  ⭐ and the second start declares «bans "
                  f"loaded: 1»: the ban came back from disk, not from memory")
        else:
            print(f"    {RED}NO{GRAY}  ⛔ the second start declares bans "
                  f"loaded = {reg['carichi'][-1] if reg['carichi'] else 'nothing'}, "
                  f"expected 1")
            faults += 1
        if reg["unreadable"]:
            print(f"    {RED}NO{GRAY}  ⛔ {reg['unreadable']} starts could not "
                  f"read the ban file")
            faults += 1
        # ⛔ And every unblock is written in the log (§4.4-bis): the bench
        #    compares it with the number of unblocks it ASKED for, or «it wrote it»
        #    stays a hope.
        asked = [r for r in unblocks if r["outcome"] is not None]
        written = len(reg["sbloccati"]) + len(reg["non_bannati"])
        if written >= len(asked) and asked:
            print(f"    {GREEN}OK{GRAY}  ⭐ every unblock ended up in the log: "
                  f"{len(asked)} asked for, {written} lines written "
                  f"({len(reg['sbloccati'])} «removed» + {len(reg['non_bannati'])} "
                  f"«was not banned»)")
        else:
            print(f"    {RED}NO{GRAY}  ⛔ unblocks asked for {len(asked)}, "
                  f"lines in the log {written}: «every unblock is written in the "
                  f"log, or a removed ban and a ban that never triggered have the "
                  f"same look» (§4.4-bis)")
            faults += 1

    # ── 7-bis. ⛔ THE TWO STOPWATCHES, and they must agree ───────────────────
    #
    # ⛔ Finding A19: the certification of this bench breaks the FACTS ALREADY
    #    RECORDED, so it certifies the JUDGE and not the ACQUISITION.  A `t0`
    #    moved to a point that keeps the numbers plausible would be seen by none
    #    of the faults built by hand.  ⭐ This line is the check the acquisition
    #    lacks: the SERVER times the same fact on its own, and the two numbers
    #    have a mandatory direction.
    #
    #    The client starts BEFORE sending `CREDENTIALS` and stops AFTER having
    #    read the answer; the server starts when `CREDENTIALS` arrives and stops
    #    when it decides.  The client's interval CONTAINS the server's: it can
    #    only be larger.  ⛔ If it is smaller, the bench's stopwatch is not
    #    measuring the interval it declares — and it is a defect OF THE BENCH,
    #    not of the server, which is precisely what `REVIEWER.md` §1 puts first.
    if reg is not None and reg["fissi"] and da_pam:
        print()
        print("    == ⛔ The two stopwatches on the same fact (B0.4: it is printed AND "
              "compared)")
        med_cli = statistics.median([r["ms"] for r in da_pam])
        med_srv = statistics.median(reg["fissi"])
        print(f"    --  client (from the receiving side) {med_cli:.0f} ms  ·  server "
              f"(«the fixed second has passed») {med_srv:.0f} ms  ·  difference "
              f"{med_cli - med_srv:+.0f} ms")
        if med_cli >= med_srv - TIMER_MARGIN:
            print(f"    {GREEN}OK{GRAY}  the client's stopwatch contains "
                  f"the server's, as it must: what the bench measures is "
                  f"the interval it declares to measure")
        else:
            print(f"    {RED}NO{GRAY}  ⛔ THE TWO STOPWATCHES DO NOT AGREE: the "
                  f"client says {med_cli:.0f} ms where the server declares "
                  f"{med_srv:.0f}, and the client's interval CONTAINS that "
                  f"of the server — it cannot be shorter")
            print(f"        ⛔ The first suspicion is on the bench, not on the server "
                  f"(`LEZIONI.md` §1.9 point 3): `t0` of `attempt()` "
                  f"times less than what its docstring declares, and "
                  f"all the medians above are of another interval")
            faults += 1

    # ── 7-ter. ⛔ WHO GOVERNS THE TIMES, measured ────────────────────────────
    culprit, accused_lines = None, []
    if fault_medians:
        print()
        print("    == ⛔ The medians separate: WHO separates them — and it is measured "
              "(A18)")
        culprit, accused_lines = timing_culprit(series, reg)
        for r in accused_lines:
            print(f"    --  {r}")
        if culprit == "OUR":
            # ⛔ And then it is NOT the `[?]` already declared by §4.4-bis: it is a
            #    defect of ours, and it goes into the counter of the real reds.
            #    Keeping it in the medians counter would mean granting to a delay
            #    we wrote ourselves the leniency written for PAM.
            print(f"    {RED}NO{GRAY}  ⛔ the separation is NOT the one "
                  f"§4.4-bis has already declared `[?]`: it is a delay of ours, and "
                  f"it counts as a full red")
            faults += 1
        elif culprit is None:
            print(f"    {YELLOW}??{GRAY}  ⚠ the defendant was not measured: "
                  f"the verdict will say THAT the medians separate and not BY WHOM, "
                  f"which is less than before and more true")

    # ── The outcome ─────────────────────────────────────────────────────────
    print()
    print(f"    == The outcome, and its denominator: {len(attempts)} attempts, "
          f"{len(pages)} pages, {len(unblocks)} unblocks")
    if faults:
        print(f"    {RED}⛔ B8: {faults} "
              f"{'point does not pass' if faults == 1 else 'points do not pass'}{GRAY}")
        if fault_medians:
            print(f"    ⚠ and {fault_medians} pairs of medians separate, and "
                  f"the defendant is «{culprit or 'NOT MEASURED'}»:")
            for r in accused_lines:
                print(f"       {r}")
            if culprit != "OUR":
                print(f"    ⚠ look at the medians AFTER having cured the {faults} "
                      f"points above")
        return 1
    if fault_medians:
        # ⛔ THE FIFTH OUTCOME, and it is born from a measurement, not from leniency —
        #    and since tonight the defendant is named by `timing_culprit()`,
        #    which READS it in the numbers, instead of a constant sentence (A18).
        print(f"    {RED}⛔ B8: {fault_medians} pairs of medians DO SEPARATE "
              f"— «the three medians indistinguishable» of `FASI.md` §01-filo-nudo B8 "
              f"is not satisfied{GRAY}")
        print(f"    ⭐ but the pair that carries the SECRET — «nonexistent − "
              f"wrong», the only one that would say whether a user name exists — does "
              f"NOT separate: what §4.4 forbids is not readable with the stopwatch")
        print(f"    ⭐ and the ban passes in full: it triggers at the third, refuses the "
              f"fourth with the right password, survives the restart, says it "
              f"in the page, and the unblock removes it")
        for r in accused_lines:
            print(f"    ⚠ {r}")
        if culprit == "PAM":
            print(f"    ⚠ It is the `[?]` that §4.4-bis already declared on 10 "
                  f"Aug 2026 and that the ban does NOT close: they are two different "
                  f"properties.  ⛔ This outcome is NOT a green, and it is kept "
                  f"separate from the red above for one reason only — a "
                  f"bench that is always red makes no regression fail, "
                  f"because nobody looks at it any more.")
            return 5
        # ⛔ Without a measured defendant the leniency of the fifth outcome does not
        #    apply: it is written for PAM, and granting it to a delay of unknown
        #    origin would mean acquitting anyone.
        print(f"    ⛔ And the defendant is NOT PAM (or it was not measured): "
              f"outcome 5 — the leniency of the `[?]` already declared — does NOT "
              f"apply, because it is written for `pam_faildelay` and not for "
              f"any delay whatsoever")
        return 1
    if on_hold:
        print(f"    {YELLOW}⚠ B8 SUSPENDED: the ban passes, but what I looked at "
              f"on the medians is not enough to call them «indistinguishable»{GRAY}")
        print(f"    ⚠ «I did not see a difference» and «there is no difference» "
              f"are two different things: run again with more blocks")
        return 3
    print(f"    {GREEN}⭐ B8 passes: every PAM answer ≥ {FIXED_DELAY:.0f} ms, "
          f"the three medians do not separate beyond the noise, the ban triggers at the "
          f"third and refuses the fourth with the right password, survives the "
          f"restart, says it in the page, and the unblock removes it{GRAY}")
    print(f"    ⚠ and it holds as far as one looked: the resolutions are printed "
          f"above, pair by pair")
    return 0


# ===========================================================================
# ⛔⭐ THE CERTIFICATION OF THE BENCH — `LEZIONI.md` §1.2 and §1.3
# ===========================================================================
# *«The bench certifies itself before the measurement»*, and *«a bench that does
# NOT reproduce is not a proof of correctness»*.  Here **one fault at a time is
# built, by hand**, inside the facts the run has just produced, and the verdict is
# required to turn red **at that point** — not generically red.
#
# ⛔ THE CRITERION IS TWOFOLD, AND THE SECOND HALF IS THE ONE THAT COUNTS: the
#    expected sentence must appear in the **broken** verdict and **not** in the
#    healthy one.  A bench already red for another reason would satisfy the
#    first half by itself, and the certification would say «it sees everything»
#    without having seen anything — which is the green-on-an-empty-set shape of
#    `LEZIONI.md` §1.9 rule 6, transferred to the certification.
def _before(data_v, **search):
    for r in data_v:
        if all(r.get(k) == v for k, v in search.items()):
            return r
    return None


def _possible_faults():
    """(name, function that breaks ONE thing, sentence the verdict MUST say)."""
    def fourth_admitted(d, reg):
        r = [x for x in d if x.get("kind") == "ban"]
        r[-1]["message"], r[-1]["motivo"] = "ADMITTED", None
        return d, reg

    def names_equal(d, reg):
        for x in d:
            if x.get("kind") == "ban":
                x["label_name"] = "sempre-lo-stesso"
        return d, reg

    def too_fast(d, reg):
        r = _before(d, kind="sample", cls_name="expected_val")
        r["ms"] = 900.0
        return d, reg

    def timed_names(d, reg):
        # ⛔ The fault this bench exists to find: «user does not exist» answers
        #    systematically before «wrong password», and with the stopwatch one
        #    reads whether a user name exists.  ⚠ Two seconds are coarse on
        #    purpose: if the bench did not see even THIS, it would see nothing.
        for x in d:
            if x.get("kind") == "sample" and x.get("case_v") == "nonexistent" \
                    and x.get("ms"):
                x["ms"] += 2000.0
        return d, reg

    def lying_page(d, reg):
        r = _before(d, kind="page_v", label="bannato-prima")
        r["banned"] = False
        return d, reg

    def page_mute(d, reg):
        r = _before(d, kind="page_v", label="bannato-prima")
        r["sentence"] = False
        return d, reg

    def bad_closing(d, reg):
        r = [x for x in d if x.get("kind") == "ban"]
        r[-1]["closure"] = WRONG_CREDENTIALS
        return d, reg

    def other_out(d, reg):
        r = _before(d, kind="check", label="altro-indirizzo")
        r["message"], r["motivo"] = "REJECTED", TOO_MANY_ATTEMPTS
        return d, reg

    def no_reset(d, reg):
        r = [x for x in d if x.get("label") == "azzeramento"]
        r[-1]["motivo"], r[-1]["message"] = TOO_MANY_ATTEMPTS, "REJECTED"
        return d, reg

    def blind_unlock(d, reg):
        r = _before(d, kind="sblocco", label="prova-tolto")
        r["outcome"] = "NOT-BANNED"
        return d, reg

    def no_persistence(d, reg):
        return [x for x in d
                if x.get("label") != "bannato-dopo-riavvio"], reg

    def log_forgetful(d, reg):
        return d, [r.replace("bans loaded: 1", "bans loaded: 0")
                    .replace("ban caricati: 1", "ban caricati: 0") for r in reg]

    def our_culprit(d, reg):
        # ⛔ The fault that certifies the cure of A18: the delay is put on the
        #    path of the ADMITTED — where `pam_faildelay` has no say — and the
        #    server log keeps saying that the fixed second covered everything.
        #    The verdict MUST stop accusing PAM.
        for x in d:
            if x.get("kind") == "sample" and x.get("case_v") == "giusta" \
                    and x.get("ms"):
                x["ms"] += 2000.0
        outside = []
        for r in reg:
            if "the fixed second has passed" in r:
                outside.append("the fixed second has passed (1005 ms)\n")
            else:
                outside.append(r)
        return d, outside

    def detached_stopwatch(d, reg):
        # ⛔ The fault that certifies the ACQUISITION and not the judge (A19):
        #    `t0` moved to a point that keeps the numbers plausible — here
        #    modelled by halving them — and none of the thirteen faults before
        #    would have noticed.  The second witness would, because the client's
        #    stopwatch cannot be shorter than the server's.
        for x in d:
            if x.get("ms"):
                x["ms"] = x["ms"] / 2.0
        return d, [r if "the fixed second has passed" not in r
                   else "the fixed second has passed (2500 ms)\n" for r in reg]

    def pam_unreadable(d, reg):
        # ⛔ THE FAULT PAID FOR ON 12 AUG 2026, reproduced: the PAM line
        #    changes shape and the bench can no longer read its verdict.  ⚠ The
        #    log is NOT empty and the lines are all there — which is precisely
        #    what makes the defect silent: one keeps counting, one keeps
        #    printing medians, and the number is of something else.
        # ⭐ The verdict must say «EVERYTHING IN ONE SINGLE BOX» and turn red:
        #    without this line the bench would go blind again the next time
        #    someone rewrites that line of `rcp.c`.
        return d, [re.sub(r"(PAM answered\b[^:]*:\s*)(admitted|refused)",
                          r"\1esito-\2", r) for r in reg]

    def pam_all_rejected(d, reg):
        # ⛔ The same blindness without the «unreadable» box: the classifier
        #    reads perfectly well, and puts **everything** on the same side.  It is
        #    the exact snapshot of 12 August — «52 lines, 0 admitted» — and the
        #    bench must shout in this form too, or the alarm would be looking at
        #    the anchor instead of the counter.
        return d, [re.sub(r"(PAM answered\b[^:]*:\s*)admitted",
                          r"\1refused", r) for r in reg]

    def no_attempt(d, reg):
        # ⛔ The file is NOT empty: the pages and the unblocks stay, and every
        #    attempt disappears.  It is the most insidious form of green — «all
        #    those tested went well» is true even when the tested are zero
        #    (`LEZIONI.md` §1.9 rule 6) — and an empty file would prove it more
        #    weakly, because anyone notices an empty file.
        return [x for x in d
                if x.get("kind") not in ("sample", "ban", "check")], reg

    return [
        ("the fourth attempt, with the RIGHT password, is ADMITTED",
         fourth_admitted, "the fourth attempt — RIGHT password —"),
        ("the three names of the ban run are THE SAME",
         names_equal, "the three names are not different"),
        ("a PAM answer arrives at 900 ms",
         too_fast, "responses below the second"),
        ("⛔ «user does not exist» answers 2 s before «wrong password»",
         timed_names, "THE SEPARATION §4.4 FORBIDS"),
        ("the page of a banned address says «you are not banned»",
         lying_page, "banned=False (expected True)"),
        ("the banned page does not contain «attempts exhausted»",
         page_mute, "expected True) · sentence=False"),
        ("the session closes with a code other than TOO_MANY_ATTEMPTS",
         bad_closing, "the session closing code"),
        ("the other address does NOT get in",
         other_out, "the other address does NOT get in"),
        ("the success does not reset the count",
         no_reset, "the reset did not happen"),
        ("the unblock answers «it was not banned» on a real ban",
         blind_unlock, "NOT-BANNED (expected REMOVED)"),
        ("persistence was not proved (the page after the restart is missing)",
         no_persistence, "persistence was not proved"),
        ("the second start declares «bans loaded: 0»",
         log_forgetful, "the second start declares bans loaded"),
        ("⛔ ZERO attempts: «all those tested went well» on zero tested",
         no_attempt, "ZERO attempts"),
        ("⛔ the delay is OURS, on the path of the ADMITTED, and PAM answers in "
         "5 ms (A18: the verdict must stop accusing PAM)",
         our_culprit, "THE DEFENDANT IS NOT PAM"),
        ("⛔ the CLIENT's stopwatch measures less than the SERVER's "
         "(A19: `t0` moved to a point that keeps the numbers plausible)",
         detached_stopwatch, "THE TWO STOPWATCHES DO NOT AGREE"),
        ("⛔ the PAM line changes shape and the verdict can no longer be read "
         "(12 Aug 2026: the bench gone blind without saying so)",
         pam_unreadable, "EVERYTHING IN ONE SINGLE BOX"),
        ("⛔ every PAM answer ends up among the REFUSED — «52 lines, 0 "
         "admitted» — and the classifier reads perfectly well",
         pam_all_rejected, "EVERYTHING IN ONE SINGLE BOX"),
    ]


def certify(a):
    import copy as _copy
    import io
    import contextlib

    if not os.path.exists(a.out_dir):
        print(f"    {RED}NO{GRAY}  ⛔ there is no run to break: "
              f"{a.out_dir} does not exist.  The certification is done **on the facts of "
              f"a real run**, or it breaks a file nobody produced")
        return 2
    with open(a.out_dir) as f:
        healthy_runs = [current_spelling(json.loads(r)) for r in f if r.strip()]
    healthy_log = []
    if a.logbook and os.path.exists(a.logbook):
        with open(a.logbook, errors="replace") as f:
            healthy_log = f.readlines()

    tmp_u = a.out_dir + ".fault"
    tmp_r = (a.logbook or "/tmp/b8-reg") + ".fault"

    def run(data_v, reg):
        with open(tmp_u, "w") as f:
            for r in data_v:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(tmp_r, "w") as f:
            f.writelines(reg)
        b = argparse.Namespace(**vars(a))
        b.out_dir, b.logbook = tmp_u, tmp_r
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            outcome = verdict(b)
        return outcome, buf.getvalue()

    print()
    print("    == ⛔ THE CERTIFICATION: the fault is built and the red is demanded")
    # ⛔ AND IT IS DECLARED WHAT THIS CERTIFICATION DOES **NOT** CERTIFY — A19.
    #    Whoever reads a verdict reads the verdict, not the comments of the file:
    #    without these three lines, «certified» reads as «B8 is certified», and
    #    what is certified is half of B8.
    print("    --  ⛔ WHAT THIS LINE CERTIFIES: the JUDGE.  The faults are "
          "built on the FACTS ALREADY RECORDED, so they prove that "
          "`verdict()` can see a crooked fact, not that the facts were "
          "taken well")
    print("    --  ⛔ WHAT IT DOES NOT CERTIFY: the ACQUISITION.  A `t0` moved "
          "to a point that keeps the numbers plausible, a `RITARDO_CREDENZIALI` "
          "removed from the server, a graft that is not there: none of these lives "
          "in the recorded facts.  ⚠ The only fault that reaches it is "
          "«stopwatch out of step», and it reaches it through the SECOND WITNESS (the "
          "server log), not through the facts")
    print("    --  ⛔ And the fault that would cover the rest — removing "
          "`RITARDO_CREDENZIALI` from the server — is in the catalogue of "
          "`01-b12-guasti.py` and is **catalogued and not run**: it is a hole "
          "of two files by two different hands, and it must be said here because it is here that "
          "the word «certified» is read")
    healthy_outcome, healthy_text = run(healthy_runs, healthy_log)
    print(f"    --  the HEALTHY run, as it is: outcome {healthy_outcome} "
          f"({'green' if healthy_outcome == 0 else 'suspended' if healthy_outcome == 3 else 'red'})")
    print(f"    --  facts being broken: {len(healthy_runs)} · log lines: "
          f"{len(healthy_log)}")

    # ======================================================================
    # ⛔⭐ THE POSITIVE CONTROL OF THE ANCHOR — and it is not a fault, it is its
    #     reverse: here the verdict must NOT change
    # ======================================================================
    # *Born on 12 Aug 2026, from the defect that made this bench blind.*
    #
    # ⛔ The fifteen faults below prove that the judge **can turn red**.  None of
    #    them proves the thing that today cost a run: that the judge **keeps
    #    reading** when whoever writes the log lengthens a line.  A fragile anchor
    #    passes all fifteen — it was fragile and passed them — because a broken
    #    anchor makes the bench red, and the faults ask precisely for red.
    #
    # ⭐ So the opposite is built: the log is lengthened **in the three ways that
    #    have already happened or are about to happen**, and the outcome is
    #    required to stay **identical** to the healthy one.  ⚠ It is the positive
    #    control of `REVIEWER.md` §1 point 5 applied to the log reader: «can the
    #    tool still find what is surely there?»
    still_failed = 0
    def _lengthen_pam(r):
        # the cure of `DECISIONI.md` §1.10, as it really arrived
        if R_PAM_LINE in r:
            return r.rstrip("\n") + ("  ⚠ (SYNCHRONOUSLY: no asynchronous "
                                     "hook connected — the thread "
                                     "stood still)\n")
        return r

    def _case_pam(r):
        # the SECOND form of the line, which the product already writes (rcp.c:2636)
        if R_PAM_LINE in r:
            return r.replace("PAM answered:",
                             "PAM answered (request 7):", 1)
        return r

    def _lengthen_from(r):
        # the address stops being the last thing on the line
        if " da=" in r and ("rejected motivo" in r or "admitted username" in r):
            return r.rstrip("\n") + " · request=7 · via=async\n"
        return r

    anchors = [
        ("an explanation appended at the tail of «PAM answered: …» "
         "(the cure of §1.10, the real one)", _lengthen_pam),
        ("one more field BEFORE the colon: «PAM answered (request 7): "
         "admitted» (rcp.c:2636, the asynchronous road)", _case_pam),
        ("the address is no longer the last thing on the line «rejected "
         "motivo=… da=…»", _lengthen_from),
    ]
    print()
    print("    == ⭐ THE POSITIVE CONTROL OF THE ANCHOR: the log gets longer, "
          "and the verdict must NOT change")
    for label_name, change in anchors:
        outcome_a, text_a = run(healthy_runs, [change(r) for r in healthy_log])
        blind = "EVERYTHING IN ONE SINGLE BOX" in text_a
        good = outcome_a == healthy_outcome and not blind
        sign = f"{GREEN}OK{GRAY}" if good else f"{RED}NO{GRAY}"
        reason_text = ""
        if blind:
            reason_text = ("  ⛔ and the judge went blind: the anchor went back "
                      "to depending on what comes AFTER")
        elif not good:
            reason_text = (f"  ⛔ the outcome changed from {healthy_outcome} to {outcome_a}: "
                      f"the log reader depends on what is "
                      f"appended to its tail")
        print(f"    {sign}  {label_name}{reason_text}")
        if not good:
            still_failed += 1
    print(f"    --  ⚠ and this check does not prove the bench is right: "
          f"it proves that it **withstands an addition**.  The red is proved by the faults "
          f"below")

    prove = _possible_faults()
    print(f"    --  faults built by hand: {len(prove)}  ⛔ and this is the "
          f"denominator: a list of OKs without it is not a measurement")
    failed = 0
    for label_name, break_it, sentence in prove:
        data_v, reg = break_it(_copy.deepcopy(healthy_runs), list(healthy_log))
        outcome, body_text = run(data_v, reg)
        sees = sentence in body_text
        # ⛔ and the second half of the criterion: the healthy verdict must NOT
        #    already say it, or this line does not prove the fault was seen.
        already = sentence in healthy_text
        # ⛔ And the outcome must be a REAL RED (1) or «nothing to judge» (2),
        #    not the 5 of the medians: if «different from zero» were enough, a run
        #    in which PAM dominates would satisfy this line **without the fault
        #    having been seen**, and the certification would say «I see
        #    everything» looking at an outcome that was already there.
        good = sees and outcome in (1, 2) and not already
        sign = f"{GREEN}OK{GRAY}" if good else f"{RED}NO{GRAY}"
        reason_text = ""
        if already:
            reason_text = "  ⛔ but the HEALTHY run already said it: it proves nothing"
        elif not sees:
            reason_text = f"  ⛔ the verdict did NOT say «{sentence}» (outcome {outcome})"
        elif outcome not in (1, 2):
            reason_text = f"  ⛔ it says it, but the outcome is {outcome} and not a real red"
        print(f"    {sign}  {label_name}{reason_text}")
        if not good:
            failed += 1

    for p in (tmp_u, tmp_r):
        try:
            os.remove(p)
        except OSError:
            pass

    print()
    if still_failed:
        print(f"    {RED}⛔ THE CERTIFICATION DOES NOT PASS: {still_failed} "
              f"lengthenings of the log out of {len(anchors)} change the verdict."
              f"{GRAY}")
        print(f"    ⚠ It is the defect of 12 Aug 2026, alive: the bench reads a "
              f"line of the server anchoring itself to what today sits at its end, and "
              f"the next addition blinds it again")
        return 1
    if failed:
        print(f"    {RED}⛔ THE CERTIFICATION DOES NOT PASS: {failed} faults out of "
              f"{len(prove)} do not make the bench turn red.{GRAY}")
        print(f"    ⚠ As long as this line is red, a green of B8 means "
              f"nothing: a bench that does not reproduce is not a proof of "
              f"correctness (`LEZIONI.md` §1.3)")
        return 1
    print(f"    {GREEN}⭐ THE JUDGE of B8 is certified: all {len(prove)} "
          f"faults built by hand make it turn red, each at its own "
          f"point — and the {len(anchors)} lengthenings of the log do NOT change it"
          f"{GRAY}")
    print(f"    ⚠ and it is NOT «B8 is certified»: the acquisition of the times stays "
          f"covered by a single fault (the two stopwatches).  The three lines at "
          f"the top say what was left out")
    return 0


def prediction(a):
    print("== B8 — what is measured, and what I expect BEFORE measuring")
    print()
    print("  PART 1 — the fixed second and the three medians")
    print("    nonexistent  a user that does NOT exist (verified with getpwnam)")
    print("    wrong    the real user, wrong password")
    print("    giusta       the real user, right password  → ADMITTED")
    print("    ⚠ the pair «nonexistent − wrong» is the one that, if it separates,")
    print("      gives away the user names to whoever times it.")
    print()
    print("  PART 2 — the ban (RCP.md §4.4-bis, DECISIONI.md §1.9)")
    print(f"    {THRESHOLD} failed authentications from the same address within")
    print(f"    {WINDOW_MIN} minutes ⇒ that address is out for {BAN_ORE} hours.")
    print()
    print("  The expected, written here before the numbers:")
    print(f"    1. every PAM answer to CREDENTIALS ≥ {FIXED_DELAY:.0f} ms;")
    print("    2. the three medians indistinguishable according to the interval rule;")
    print("    3. the first three failed — WITH THREE DIFFERENT NAMES — receive")
    print("       WRONG_CREDENTIALS, and the third makes the ban trigger;")
    print("    4. ⛔ the FOURTH attempt has the RIGHT password and receives")
    print("       TOO_MANY_ATTEMPTS, inside a REJECTED and not inside a FAREWELL,")
    print("       and the session closes with the same code;")
    print("    5. ANOTHER address gets in right away;")
    print("    6. 2 failed · 1 succeeded · 2 failed do NOT ban;")
    print("    7. the ban survives the server restart (invariant I7);")
    print("    8. the page loads ANYWAY, with HTTP 200, says «attempts")
    print(f"       exhausted» and how many hours are left (~{BAN_ORE});")
    print("    9. the unblock command removes it, writes it in the log, and the")
    print("       second time answers «it was not banned».")
    print("   10. ⛔ and the JUDGE must not be blind: the PAM answers read")
    print("       in the log must fall into AT LEAST TWO boxes.  All in the")
    print("       same one — «52 lines, 0 admitted», 12 Aug 2026 — is not «the")
    print("       facts are all the same»: it is «I can no longer read the facts»,")
    print("       that is form E8 on a counter, and it counts as a red.")
    print()
    print("  `[?]` And the prediction that may make point 2 SUSPENDED, written")
    print("  now so that tomorrow it looks like a prediction and not an excuse:")
    print("    `banchi/rcp/autenticazione.c` uses the PAM service «login», and on")
    print("    Debian `/etc/pam.d/login` carries `pam_faildelay.so delay=3000000`.")
    print("    If that module is in the stack, the FAILURE road waits")
    print("    ~3 s (±25 % for libpam's randomisation) and the SUCCESS road")
    print("    does not: the medians would separate by seconds, and the")
    print("    separation would NOT be the fixed delay's — it would be what")
    print("    PAM adds on top.  ⭐ What tells the two defendants apart is the line")
    print("    «the fixed second has passed (N ms)» of the server log.")
    print("    `[M]` 10 Aug 2026: median 2636 ms on the refused.")
    print()
    print(f"  The numbers of the rule: threshold {THRESHOLD} failures per address,")
    print(f"  balance {BALANCE} per block, wanted resolution "
          f"±{WANTED_RESOLUTION:.0f} ms, minimum {MIN_SAMPLES} samples per")
    print(f"  case, bootstrap {REPETITIONS} repetitions, seed {SEED}.")
    return 0


# ===========================================================================
# The phases
# ===========================================================================
async def phase_samples(a):
    nonexistent = f"nessuno-b8-{a.block}"
    if not await check_users(a, nonexistent):
        return 2
    if not await test_addresses(a.addresses, a.port):
        return 2
    steps = sample_plan(a.block, a.per_case, a.addresses, a.username, nonexistent)
    return await execute(a, steps, "sample", f"block {a.block}", "sotto-soglia")


async def phase_ban_before(a):
    """⛔ The ban run, and NOBODY UNBLOCKS IN HERE (B0.3).

    The order is chosen and it is not indifferent:

      1. the reset check on the SECOND address (which ends at two failures, and
         the page confirms it not banned);
      2. the ban on the FIRST address, with three different names, and the
         fourth with the right password;
      3. the check «another address gets in» — ⛔ **right after** the refusal,
         which is the only place where it answers the question «is the server
         still alive?»;
      4. the two pages.
    """
    nonexistent = "nessuno-b8-ban"
    if not await check_users(a, nonexistent, *[n for n in BAN_NAMES
                                                    if n != "<username>"]):
        return 2

    print()
    print("    == ⭐ Check that says NO no.2: 2 failed · 1 succeeded · 2 failed")
    steps = reset_plan(a.addresses, a.username, nonexistent)
    e = await execute(a, steps, "check", "azzeramento", "non-banna")
    if e:
        return e
    look_page(a, a.addresses[1], "azzeramento-dopo", False)

    print()
    print("    == ⛔ The ban run — three different names, then the RIGHT password")
    names = tuple(a.username if n == "<username>" else n for n in BAN_NAMES)
    steps = piano_ban(a.addresses, a.username, names)
    e = await execute(a, steps, "ban", "ban", "banna-al-4")
    if e:
        return e

    print()
    print("    == ⭐ Check that says NO no.1: ANOTHER address gets in right away")
    steps = [{"case_v": "giusta", "address": a.addresses[1], "label_name": a.username,
              "scaldata": False}]
    e = await execute(a, steps, "check", "altro-indirizzo", "sotto-soglia")
    if e:
        return e

    print()
    print("    == ⛔ What the user sees, now")
    look_page(a, a.addresses[0], "bannato-prima", True)
    look_page(a, a.addresses[1], "non-bannato-prima", False)
    return 0


async def phase_ban_after(a):
    """⭐ After the restart: persistence, and then the unblock — which is tested at the end."""
    print()
    print("    == ⭐ Check that says NO no.3: the ban survives the RESTART")
    look_page(a, a.addresses[0], "bannato-dopo-riavvio", True)
    look_page(a, a.addresses[1], "non-bannato-dopo-riavvio", False)
    steps = [{"case_v": "giusta", "address": a.addresses[0], "label_name": a.username,
              "scaldata": False}]
    # ⚠ The model would say ADMITTED — it does not know the ban came back from disk —
    #   and demanding it here would give red on the right code.  The comparison is
    #   done by the verdict, which knows we are after a restart.
    e = await execute(a, steps, "check", "dopo-riavvio", "sotto-soglia",
                     compare_model=False)
    if e:
        return e

    print()
    print("    == ⛔ AND NOW the unblock, which so far has touched nothing")
    unblock_and_declare(a, [a.addresses[0]], "prova-tolto", require="REMOVED")
    look_page(a, a.addresses[0], "dopo-sblocco", False)
    unblock_and_declare(a, [a.addresses[0]], "prova-non-bannato",
                       require="NOT-BANNED")
    steps = [{"case_v": "giusta", "address": a.addresses[0], "label_name": a.username,
              "scaldata": False}]
    return await execute(a, steps, "check", "dopo-sblocco", "sotto-soglia")


async def check_users(a, *nonexistent_names):
    """⛔ The initial state is declared and VERIFIED (B0.1)."""
    ok = True
    for label_name, must, desc in [(a.username, True, "the real user")] + \
            [(n, False, "a nonexistent name") for n in nonexistent_names]:
        good, c_e = existence(label_name, must)
        state = "exists" if c_e else "does not exist"
        if good:
            print(f"    {GREEN}OK{GRAY}  {desc} «{label_name}»: {state}, as it must")
        else:
            print(f"    {RED}NO{GRAY}  ⛔ {desc} «{label_name}»: {state} — the "
                  f"opposite of what this bench assumes")
            ok = False
    return ok


def primary():
    p = argparse.ArgumentParser(
        description="B8 — the fixed second, the three medians and the ban of the address")
    # ⛔ No default that names a target: 7447 is the graft and 7448 the
    #    product, and a default here would mean that «--bersaglio prodotto»
    #    without «--porta» measures the graft while declaring the product.
    p.add_argument("--port", type=int, required=True)
    p.add_argument("--addresses", default="127.0.0.1,192.168.0.2",
                   help="⛔ two: they double the margin of the balance and "
                        "show in the server log")
    p.add_argument("--username", default="prova")
    # ⛔ `parola-di-prova`, and the story of this line is worth the comment.
    #
    #    Until 11 Aug 2026 here it said `prova`, and ⛔ **no authentication of
    #    this bench ever succeeded**: `01-b3-lancia.sh`, `01-b6-lancia.sh` and
    #    `01-b7-lancia.sh` all three use `PASSWORD=parola-di-prova`.  The «giusta»
    #    case received `WRONG_CREDENTIALS` like the other two, that is ⛔ **the
    #    three cases were two**, and the third median was a copy of the second.
    #
    # ⚠ And the defect had no symptom of its own: the bench said «unexpected
    #   answers», which reads as a server fault.  ⭐ From today there is the
    #   positive control in `--initial-state` — *«can this tool produce an
    #   AMMESSO?»* — which is `LEZIONI.md` §1.9 rule 2 applied to the bench
    #   instead of to the measurement, and it costs one attempt.
    p.add_argument("--password", default="parola-di-prova")
    # ⛔ D12: the road that does NOT go through `ps`.  It wins over `--password` if
    #    both are there — a file written on purpose is always more recent than a
    #    default.
    p.add_argument("--password-file", default="",
                   help="0600 file with only the password (⭐ D12: this way "
                        "it does not end up in `ps`)")
    p.add_argument("--wrong", default="questa-non-e-la-parola-di-nessuno")
    p.add_argument("--command", default="/srv/src/b8-comando.sock",
                   help="the socket of the unblock command of §4.4-bis")
    p.add_argument("--block", type=int, default=0)
    p.add_argument("--per-case", type=int, default=2,
                   help="triplets per block.  ⛔ 2 keeps the failures at two per "
                        "address, that is ONE below the threshold")
    p.add_argument("--samples", action="store_true")
    p.add_argument("--ban", choices=("before", "after"))
    p.add_argument("--unblock", default="",
                   help="unblock these addresses (comma-separated) and declare it")
    p.add_argument("--reason_text", default="fra-i-blocchi")
    p.add_argument("--initial-state", action="store_true")
    p.add_argument("--verdict", action="store_true")
    p.add_argument("--certify", action="store_true",
                   help="⛔ builds one fault at a time in the facts of a real "
                        "run and demands that the bench turn red at THAT point")
    p.add_argument("--prediction", action="store_true")
    # ⛔ `--lap` likewise: the shared profile declares it (see the note below).
    # ⛔ `--out_dir` is NOT declared here: the shared target profile declares it,
    #    `01-b0-bersaglio.py`, a few lines further down.  Declaring it in both
    #    places makes the bench die at start-up with
    #    «conflicting option string: --uscita» — measured on 11 Aug 2026, and
    #    the run stopped BEFORE starting anything.
    # ⚠ It is the seam between two authors of the same day: whoever wrote the
    #   profile did not know B8 already had that argument, and whoever wrote
    #   B8 did not know a profile would arrive.  The default of the time —
    #   `b8-fatti.jsonl`, without the target in the name — is precisely the one
    #   the profile exists to remove: two targets in the same file are two
    #   measurements that cannot be put in a row.
    p.add_argument("--logbook", default="")
    # ⛔ The same four arguments as B5, B6 and B7 — mandatory target without a
    #    default, output, run, md5 of the binary.
    b0.add_arguments(p)
    a = p.parse_args()
    a.password = password_from_args(a)
    a.addresses = [x for x in a.addresses.split(",") if x]
    a.prof = b0.profile_v(a.target)
    # ⛔ And from here on EVERY log line carries the target, the port and the md5
    #    fingerprint of the measured binary.
    TARGET.update({"target": a.target, "port": a.port,
                      "md5": a.md5 or "ignota"})
    R_BAN.update({"caricati": a.prof["r_ban_caricati"],
                  "illeggibile": a.prof["r_ban_illeggibile"],
                  "page_v": a.prof["r_pagina"]})

    if a.prediction:
        return prediction(a)
    if a.certify:
        return certify(a)
    if a.verdict:
        return verdict(a)
    if len(a.addresses) < 2:
        print(f"    {RED}NO{GRAY}  ⛔ TWO source addresses are needed")
        return 2

    # ⛔ AND THE OPENING LINE OF THE RUN — which says against what one measures, and
    #    what this target does differently.
    put_out(a.out_dir, {"lap": a.lap, "kind": "lap", "bench": "B8",
                      "executable": a.prof["executable"],
                      "addresses": a.addresses,
                      # ⛔ The difference that changes the MEANING of a red:
                      #    if the ban file is there and cannot be read, the product
                      #    REFUSES to start (src/main.c: «it is not "zero bans",
                      #    it is the protection of §4.4-bis switched off.  One does
                      #    not start.»), while the graft starts and writes it.  ⚠ On
                      #    this target that case is not observed as a log line:
                      #    it is observed as «the server did not start».
                      "ban_illeggibile_parte": a.prof["ban_illeggibile_parte"],
                      "righe_cercate": dict(R_BAN)})

    if a.initial_state:
        # ⛔ B0.1: it is declared AND verified from which state one starts.  Here
        #    the state that counts is threefold: the unblock command exists, the
        #    two addresses are not banned, and the page can say no.
        alive, desc = cmd.ping(a.command)
        if not alive:
            print(f"    {RED}NO{GRAY}  ⛔ the unblock command does not answer: "
                  f"{desc}")
            print(f"        without it, this bench can neither start from a "
                  f"known state nor put the machine back in order — and every "
                  f"following bench would stay out for {BAN_ORE} hours (B0.3)")
            return 2
        print(f"    {GREEN}OK{GRAY}  the unblock command answers ({desc})")
        unblock_and_declare(a, a.addresses, "initial-state")
        all_of = True
        for addr in a.addresses:
            r = look_page(a, addr, "initial-state", False)
            if r["failure"] or r["banned"] is not False:
                all_of = False
        if not all_of:
            print(f"    {RED}NO{GRAY}  ⛔ the initial state is not the "
                  f"declared one: someone is already banned, or the page does not "
                  f"answer")
            return 2
        print(f"    {GREEN}OK{GRAY}  ⭐ and the page CAN SAY NO: without this "
              f"line, «attempts exhausted» later would be compatible with "
              f"a page that always says it")

        # ⛔ THE POSITIVE CONTROL ON THE TOOL — `LEZIONI.md` §1.9 rule 2:
        #    *«every measurement wants a positive control, on the same tool —
        #    can this tool find something that is surely there?»*
        #
        #    Here the question is: **can this bench produce an ADMITTED?**  If it
        #    cannot — wrong password, user without password, PAM that does not
        #    talk to it — the «giusta» case receives `WRONG_CREDENTIALS` like
        #    the other two, ⛔ **the three cases become two**, and the pair
        #    «sbagliata − giusta» would be indistinguishable **by construction**:
        #    the emptiest green this bench can print.
        #
        # ⚠ And it costs an attempt that consumes nothing: a SUCCESSFUL
        #   authentication resets the count of that address (§4.4-bis), so it
        #   leaves the machine cleaner than it found it.
        r = asyncio.run(attempt(a.addresses[0], a.port, a.username, a.password))
        rec = dict(r)
        rec.update({"lap": a.lap, "kind": "check",
                    "label": "so-fare-un-ammesso", "block": 0, "order": 1,
                    "case_v": "giusta", "scaldata": True,
                    "cls_name": ranking(r, "giusta"),
                    "atteso_modello": "ADMITTED", "expected_reason": None})
        put_out(a.out_dir, rec)
        if rec["message"] != "ADMITTED":
            print(f"    {RED}NO{GRAY}  ⛔ the positive control does NOT pass: with "
                  f"the user «{a.username}» and the password this bench believes "
                  f"right the server answers "
                  f"{rec['message'] or rec['failure']} "
                  f"{REASONS.get(rec['motivo'], '')}")
            print(f"        ⛔ without an ADMITTED the three cases are TWO, and «the three "
                  f"medians do not separate» would be true by construction.  "
                  f"Look at the password (the other benches use "
                  f"«parola-di-prova»), not at the server")
            return 2
        print(f"    {GREEN}OK{GRAY}  ⭐ and this bench CAN produce an ADMITTED "
              f"({rec['ms']:.0f} ms): the three cases really are three")
        return 0

    if a.unblock:
        unblock_and_declare(a, [x for x in a.unblock.split(",") if x], a.reason_text)
        return 0

    if a.samples:
        return asyncio.run(phase_samples(a))
    if a.ban == "before":
        return asyncio.run(phase_ban_before(a))
    if a.ban == "after":
        return asyncio.run(phase_ban_after(a))
    print(f"    {RED}NO{GRAY}  ⛔ you did not tell me what to do")
    return 2


# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD MUST NOT GO THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 Aug 2026.
#
# ⛔ `--password` ends up in the process `argv`, that is in `/proc/<pid>/cmdline`,
#    which on Linux is **readable by anyone**: a `ps` launched by another user
#    during the run prints it in full.
#
# ⭐ The good road already existed in the house and this is its extension, not a
#    second way: `01-b10-secondo-utente.py` takes `--password-file`, a `0600` file
#    that the launcher writes with `printf` — a shell **builtin**, so not even
#    the writing goes through a process with the password in `argv` — and
#    deletes with a `trap`.
#
# ⚠ And `--password` was NOT removed, and not out of laziness: some callers not
#   yet cured still pass it, and breaking them **silently** would be worse than
#   the defect.  ⛔ But the fallback is DECLARED (`CODER.md` §4.2): a silent
#   fallback produces two behaviours under the same label, which is form
#   **E2** — and here the two behaviours are «the secret is protected» and
#   «the secret is public».  ⇒ whoever passes `--password` gets told.
#
# ⚠ And the warning looks at `sys.argv`, not at the value: the default written
#   in the code is in no command line, and telling it otherwise would be an
#   alarm one learns to ignore.
def password_from_args(a):
    """The password: from `--password-file` if present, from `--password` otherwise.

    ⛔ And the three ways of failing are told apart: «cannot be read», «is
    readable by others» and «is empty» have three different cures, and an empty
    file is NOT an empty password — it is «the launcher did not write it»
    (`LEZIONI.md` §1.9).
    """
    fpath = getattr(a, "password_file", "") or ""
    if fpath:
        try:
            manner = os.stat(fpath).st_mode & 0o077
        except OSError as e:
            print(f"   ⛔ the password file «{fpath}» cannot be read: {e}")
            sys.exit(2)
        if manner:
            print(f"   ⚠ «{fpath}» is readable by others (bits {manner:o}): the "
                  f"secret is not protected")
        try:
            with open(fpath, encoding="utf-8") as f:
                password = f.read().strip("\n")
        except OSError as e:
            print(f"   ⛔ the password cannot be read from «{fpath}»: {e}")
            sys.exit(2)
        if not password:
            print(f"   ⛔ the password file «{fpath}» is EMPTY.  It is not")
            print("      «the password is empty»: it is «the launcher did not write it».")
            sys.exit(2)
        return password
    if any(x == "--password" or x.startswith("--password=") for x in sys.argv[1:]):
        print("   ⚠ D12: the password arrived from `--password`, that is from the")
        print("     COMMAND LINE: it is in `/proc/<pid>/cmdline` and anyone who")
        print("     runs `ps` on this machine sees it.  The run goes on — the caller")
        print("     has not been cured — but it is not a private run.")
        print("     ⭐ The cure: `--password-file <0600 file>`, as in B10.")
    return a.password


if __name__ == "__main__":
    sys.exit(primary())
