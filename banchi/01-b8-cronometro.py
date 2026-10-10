#!/usr/bin/env python3
"""01-b8-cronometro.py — ⛔ B8: the fixed second, and THE BAN OF THE ADDRESS.

    python3 01-b8-cronometro.py --previsione
    python3 01-b8-cronometro.py --campioni --blocco 3 --giro ...
    python3 01-b8-cronometro.py --ban prima  --giro ...    (one life of the server)
    python3 01-b8-cronometro.py --ban dopo   --giro ...    (after the restart)
    python3 01-b8-cronometro.py --verdetto --giro ...

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
    reset the counters: *«`rcp_azzera_registro_sessioni()` exists but nobody
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
«≥ 1 s»: `pam_authenticate(); sleep(1); rispondi();` gives 1.001 · 1.050 · 1.300 s
in the three cases — three green lines, and the distinction readable exactly as
before (finding R3.2).  The criterion is **of a different shape**: the three
medians must differ **less than the noise of the measurement**.

**2. The ban** — new.  Three failed with **three different names**, then the
fourth attempt **with the RIGHT password** that MUST be refused with
`TROPPI_TENTATIVI`; plus the three checks that say *no*; plus the page that
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
    which writes `da=<indirizzo>:<porta>` — the denominator read where the thing
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
  b. **the plan is verified BEFORE running it**: `simula()` is a model of the
     new §4.4-bis — threshold 3, sliding window of 5 minutes, key on the address
     only, reset on success, unblock that resets everything — and says
     **attempt by attempt** what should arrive.  `verifica_piano()` **does not
     start** a block the model sees overflowing.  A comment saying «we stay
     below threshold» is not a check: this is;
  c. ⛔ **and on the wire every single answer is looked at**: a sample that comes
     back `RESPINTO(TROPPI_TENTATIVI)` **does not enter the medians**, it is
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
  | contains zero, half-width ≤ RISOLUZIONE_VOLUTA | ⭐ **indistinguishable**, and it says how far one looked |
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
     fixed second** … it is decided **before CREDENZIALI**»*.  ⛔ `banchi/rcp/rcp.c`
     decides it **after** having received `CREDENZIALI` (it cannot do otherwise:
     the control channel is the only thing it sees) and makes it go **through
     the fixed delay anyway**.  ⭐ And it must be so, or the bench could not
     exist: B8 demands `TROPPI_TENTATIVI` **inside a `RESPINTO`** (§4.4, finding
     R1.18), and a refusal decided before `CREDENZIALI` would have no
     `RESPINTO` to send.  Here the time of the refusal is **measured and
     printed**, and it makes neither red nor green: it is a defect of the
     document, not of the code;
  2. §4.4-bis: *«the page is served anyway»* does not say **with which HTTP
     status**.  The host answers **200**, and the reason is in its comment: with
     a 4xx an intermediary or the browser may replace the body, and the
     sentence the user MUST read would disappear.  Here **200** is demanded;
  3. ⭐ **and the most important of the three**: `FASI.md` §01-filo-nudo B8 asks
     for *«the THREE medians indistinguishable»*, and §4.4-bis wants the fixed
     delay *«even when the answer is AMMESSO»*.  ⚠ But what §4.4 **forbids**
     letting be known is one thing only — **whether a user name exists** — while
     «admitted» against «refused» the wire says by itself: they are two
     **different messages**.  ⛔ The three pairs are not worth the same, and this
     bench runs all three **counting them separately**:

       `inesistente − sbagliata` that separates   ⇒ ⛔ FULL RED: it is the
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

QUI = os.path.dirname(os.path.abspath(__file__))


def _importa(nome, file):
    spec = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ⛔ The B3 test client is IMPORTED, not copied: inside it is the line that
#    prevents it from handing the control-channel events to aioquic's HTTP/3
#    layer — without which the connection dies at the hand of the CLIENT, and
#    here the symptom would be «the server does not answer in time».
b3 = _importa("b3cliente", "01-b3-cliente.py")
# ⛔ And the unblock command too: if this file rewrote it for itself, B0.3
#    would have two unblock commands and nobody would know which one ran.
cmd = _importa("b8sblocca", "01-b8-sblocca.py")
# ⛔ And the TARGET's profile: the differences between the two servers in a single file.
b0 = _importa("b0bersaglio", "01-b0-bersaglio.py")

inquadra, s_str, MOTIVI = b3.inquadra, b3.s, b3.MOTIVI
T_CREDENZIALI = 0x0003
CREDENZIALI_ERRATE, TROPPI_TENTATIVI = 0x07, 0x08

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"

# ── The numbers of the rule, all in one place and all declared ───────────────
# `RCP.md` §4.4-bis, the user's shape of 10 Aug 2026.
SOGLIA = 3                 # three failed authentications from the same address
FINESTRA_MIN = 5           # ...within five minutes (SLIDING window)
BAN_ORE = 12               # ...and that address is out for twelve hours
BILANCIO = 2               # ⛔ one BELOW the threshold, per address and per block
RITARDO_FISSO = 1000.0     # §4.4-bis: no answer to CREDENZIALI before 1 s
RISOLUZIONE_VOLUTA = 50.0  # ms — the separation the phase document names
MINIMO_CAMPIONI = 10       # below this one does not judge: one says «suspended»
RIPETIZIONI = 2000         # bootstrap resamplings
SEME = 20260811            # ⛔ fixed: two verdicts on the same data coincide
# ⛔ THE TWO MARGINS NEEDED TO NAME A DEFENDANT, and they are here because a
#    number chosen inside an `if` is a number nobody compares.
#    · `MARGINE_IMPUTATO`  how long the server must have waited BEYOND the fixed
#      second for one to be able to say «what governed was not our delay».
#      Below this threshold the fixed second covered everything, and whoever
#      delayed left no trace at the point where the server measures.
#    · `MARGINE_CRONOMETRI`  by how much the CLIENT's stopwatch may be below
#      the SERVER's before the difference stops being network noise.
#      ⛔ The client measures an interval that CONTAINS the server's (it starts
#      before sending and ends after receiving): it can only be larger.  If it
#      is smaller, it is not the server that is strange — it is the bench's
#      stopwatch that is not timing what it declares.
MARGINE_IMPUTATO = 200.0
MARGINE_CRONOMETRI = 100.0

CASI = ("inesistente", "sbagliata", "giusta")
ATTESO = {"inesistente": ("RESPINTO", CREDENZIALI_ERRATE),
          "sbagliata": ("RESPINTO", CREDENZIALI_ERRATE),
          "giusta": ("AMMESSO", None)}

# The six permutations of the triplet.  ⛔ The order ROTATES: if one case always
#    sat right after the unblock and another always at the end, any drift inside
#    the block would end up **in the medians** disguised as a difference between
#    the cases.
ROTAZIONI = [("inesistente", "sbagliata", "giusta"),
             ("sbagliata", "giusta", "inesistente"),
             ("giusta", "inesistente", "sbagliata"),
             ("inesistente", "giusta", "sbagliata"),
             ("sbagliata", "inesistente", "giusta"),
             ("giusta", "sbagliata", "inesistente")]

# ⛔ THE THREE NAMES OF THE BAN RUN — and they MUST be different.
#    `FASI.md` §01-filo-nudo B8: «with the same name three times, a server that
#    still had the per-NAME counter of the old shape would give green: the bench
#    would prove the wrong rule.  It is the same shape with which B5 found the
#    counter keyed on the port».
#    ⭐ And the three are not even of the same KIND: two names that do not exist
#       and a wrong password on the real user.  §4.4-bis counts the two things as
#       one — «the count does not know whether the name did not exist or the
#       password was wrong» — and this is the way to prove it instead of believing it.
NOMI_DEL_BAN = ("nessuno-b8-uno", "<utente>", "nessuno-b8-tre")


# ===========================================================================
# The wire
# ===========================================================================
async def apri(indirizzo, porta, percorso="/rcp/1"):
    """A new connection, and the WebTransport session on `/rcp/1`.

    ⚠ One per attempt, and it is not a choice: §4.4 allows **a single attempt
      per connection**."""
    conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                             max_datagram_frame_size=65536)
    conf.verify_mode = ssl.CERT_NONE
    autorita = f"{indirizzo}:{porta}"
    gestore = connect(indirizzo, porta, configuration=conf,
                      create_protocol=b3.Cliente)
    cli = await gestore.__aenter__()
    await asyncio.wait_for(cli.wait_connected(), timeout=8)
    cli.apri_sessione(autorita, percorso)
    stato = await asyncio.wait_for(cli.accettata, timeout=8)
    return gestore, cli, stato


async def un_tentativo(indirizzo, porta, nome, parola, attesa_chiusura=4.0):
    """One attempt: `CREDENZIALI` leaving, the answer arriving, the milliseconds.

    ⛔ WHAT IS INSIDE THE STOPWATCH, AND WHAT IS NOT.  Inside: the trip of
       `CREDENZIALI`, the server's work (ban guard, PAM, fixed delay) and the
       trip of the answer.  Outside: the QUIC/TLS handshake, the opening of the
       session, `CIAO`/`ECCOMI`.

    ⚠ The network round trip is inside and is not removed — but it is **the same
      for all three cases**, on the same path: it can move the three medians
      together, not separate them.  It is the reason the criterion is a DIFFERENCE.

    ⛔ AND THE CLOSING OF THE SESSION IS ALSO WAITED FOR, which is the **second
       road of §3.1 point 3** and the only thing that answers *«and the tab
       already open?»* of B8.  ⚠ It does not arrive together with the
       `RESPINTO`: the host defers it by five passes of the write loop — half a
       second — on purpose, because a browser that processes the capsule before
       the bytes of the stream would throw away the `RESPINTO` (defect found by
       B11).  Closing right after the answer would mean declaring «no closing
       code» on a code that was arriving.

    ⛔ The password ends up in no file (B13.2): only the **name** and the time
       come out of here."""
    fuori = {"indirizzo": indirizzo, "nome": nome, "ms": None,
             "messaggio": None, "motivo": None, "chiusura": None,
             "esito": "errore", "errore": ""}
    gestore = None
    try:
        gestore, cli, stato = await apri(indirizzo, porta)
        if stato != "200":
            fuori["errore"] = f"the session did not open: :status={stato}"
            return fuori
        cli.apri_controllo()
        cli.manda(inquadra(b3.T["CIAO"], b3.corpo_ciao()))
        await b3.attendi(cli, "ECCOMI", attesa=10)
        corpo = s_str(nome) + s_str(parola)
        t0 = time.perf_counter()
        cli.manda(inquadra(T_CREDENZIALI, corpo))
        # ⛔ `quale=None`: ANY answer is accepted and classified afterwards.
        #    Demanding `AMMESSO` would raise an exception on the cases that must
        #    be refused — that is the bench would not have the time of the cases
        #    it cares most about.
        nome_msg, corpo_r, _ = await b3.attendi(cli, None, attesa=30)
        fuori["ms"] = (time.perf_counter() - t0) * 1000.0
        fuori["messaggio"] = nome_msg
        if nome_msg == "RESPINTO":
            fuori["motivo"] = corpo_r[0] if corpo_r else None
            # ⚠ Only after a RESPINTO: after an AMMESSO the session stays alive and
            #   waiting here would mean waiting four seconds for nothing for every
            #   «giusta» sample — that is a third of the bench.
            try:
                await asyncio.wait_for(cli.caduto.wait(), timeout=attesa_chiusura)
            except asyncio.TimeoutError:
                pass
            fuori["chiusura"] = cli.codice_chiusura
        fuori["esito"] = "misurato"
    except Exception as e:  # noqa: BLE001 — the error type IS the measurement
        fuori["errore"] = f"{type(e).__name__}: {e}"
    finally:
        if gestore is not None:
            try:
                await gestore.__aexit__(None, None, None)
            except Exception:  # noqa: BLE001
                pass
    return fuori


def classifica(rec, caso):
    """⛔ The third guard: what REALLY arrived.

    A `TROPPI_TENTATIVI` is not a sample of «wrong password»: it is another road
    inside the server — **it does not even go through PAM** — and putting it in
    the same median would mean mixing two populations under the same label
    (form E2)."""
    if rec["esito"] == "errore":
        return "errore"
    msg, motivo = ATTESO[caso]
    if rec["messaggio"] == "RESPINTO" and rec["motivo"] == TROPPI_TENTATIVI:
        return "limitatore"
    if rec["messaggio"] != msg:
        return "inatteso"
    if motivo is not None and rec["motivo"] != motivo:
        return "inatteso"
    return "atteso"


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
#    The three markers looked for below — `data-bannato="(si|no)"`,
#    `data-restano-ms="(\d+)"` and the exact substring `attempts exhausted` —
#    are produced **only by the graft**, `01-b3-rcp-innesta.py:1105-1139`.  ⛔ The
#    product server in `src/` says the same thing in another way:
#
#      · `src/pagina.c:257-262` writes «I tentativi di accesso da questo
#        indirizzo sono **esauriti**.  Riprova fra %llu ore e %llu minuti…» —
#        seven words in between, so the substring looked for here is NOT there;
#      · the remaining milliseconds **do not appear at all** in the served
#        document: the product already formats them into hours and minutes and
#        throws away the rest;
#      · `data-bannato` and `data-restano-ms` appear **zero times** in
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
def _chiedi_pagina(indirizzo, porta, attesa, tls):
    """A single request, in the requested dialect.  (raw, error)."""
    nudo = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    nudo.settimeout(attesa)
    s = None
    try:
        nudo.connect((indirizzo, porta))
        if tls:
            # ⭐ What does NOT change: the source address is still chosen by the
            #    kernel.  `wrap_socket` wraps the connection already open, it does
            #    not open another one.
            conf = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            conf.check_hostname = False
            conf.verify_mode = ssl.CERT_NONE  # the certificate is judged by B3
            s = conf.wrap_socket(nudo, server_hostname=indirizzo)
        else:
            s = nudo
        s.settimeout(attesa)
        s.sendall(f"GET / HTTP/1.1\r\nHost: {indirizzo}:{porta}\r\n"
                  f"Connection: close\r\n\r\n".encode())
        pezzi = []
        while True:
            d = s.recv(65536)
            if not d:
                break
            pezzi.append(d)
        return b"".join(pezzi), ""
    except OSError as e:
        # ⛔ And this is an outcome, not an absence: §4.4-bis forbids «a network
        #    error, a silence».  Whoever reads this field must be able to tell
        #    «the page says I am not banned» from «I talked to nobody» — they
        #    are the same face only for whoever does not look.
        return b"", f"{type(e).__name__}: {e}"
    finally:
        try:
            (s or nudo).close()
        except OSError:
            pass


def leggi_pagina(indirizzo, porta, attesa=5.0, tls=True):
    """Asks for the page over TCP **from that address**, and reads what it says.

    ⛔ The source address is not declared: the kernel chooses it, and it is that
       of the interface one goes out through.  Asking `127.0.0.1` one arrives as
       `127.0.0.1`; asking `192.168.0.2` one arrives as `192.168.0.2`.  ⭐ And the
       server writes in the log **from which** address it received: the
       denominator is read where the thing happens."""
    fuori = {"indirizzo": indirizzo, "stato": None, "bannato": None,
             "restano_ms": None, "ore": None, "minuti": None,
             "frase": False, "byte": 0, "errore": "", "tls": tls}
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
    grezzo, errore = _chiedi_pagina(indirizzo, porta, attesa, tls)
    if errore:
        altro, err2 = _chiedi_pagina(indirizzo, porta, attesa, not tls)
        if not err2 and altro:
            fuori["errore"] = (
                f"⛔ THE DIALECT IS THE OTHER ONE: asked in "
                f"{'TLS' if tls else 'plain'} it gave «{errore}», and in "
                f"{'plain' if tls else 'TLS'} it answers ({len(altro)} bytes). "
                f"It is not «the page does not answer»: it is the target declared "
                f"wrongly, and the three page checks below would speak "
                f"of the bench and not of the server")
        else:
            fuori["errore"] = errore
        return fuori
    fuori["byte"] = len(grezzo)
    testo = grezzo.decode("utf-8", errors="replace")
    prima = testo.split("\r\n", 1)[0]
    m = re.match(r"HTTP/1\.[01] (\d{3})", prima)
    fuori["stato"] = int(m.group(1)) if m else None
    corpo = testo.split("\r\n\r\n", 1)[1] if "\r\n\r\n" in testo else testo
    m = re.search(r'data-bannato="(si|no)"', corpo)
    if m:
        fuori["bannato"] = (m.group(1) == "si")
    m = re.search(r'data-restano-ms="(\d+)"', corpo)
    if m:
        fuori["restano_ms"] = int(m.group(1))
    m = re.search(r'id="ore">(\d+)<', corpo)
    if m:
        fuori["ore"] = int(m.group(1))
    m = re.search(r'id="minuti">(\d+)<', corpo)
    if m:
        fuori["minuti"] = int(m.group(1))
    fuori["frase"] = "attempts exhausted" in corpo
    return fuori


# ===========================================================================
# ⛔ THE MODEL OF §4.4-bis, APPLIED TO THE PLAN BEFORE THE WIRE
# ===========================================================================
def simula(passi):
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
    falliti, bannati, picco, esiti = {}, set(), {}, []
    for p in passi:
        ind = p["indirizzo"]
        if p.get("azione") == "sblocca":
            # ⛔ The unblock resets the WHOLE entry — ban and count — because it
            #    is what `rcp_sblocca()` does: `memset` of the entry.
            #
            # ⛔ AND UNTIL 11 AUG 2026 THIS LINE WAS A BELIEF (finding A22): on
            #    an address NOT banned the unblock answers «NON-BANNATO», and
            #    whether it reset the count anyway nobody verified — while the
            #    whole sampling strategy («unblock between one block and the
            #    next») rests on it.
            #    ⭐ Now it is measured, and not from here: `01-b8-prova-ban.c`
            #    section 5 fails twice, calls `rcp_sblocca()` on an address that
            #    is NOT banned, and verifies that the third failure does not make
            #    the ban trigger.
            # ⚠ And the symptom of the opposite case (§1.11), if one day it came
            #   back: the failures would pile up between the blocks, and the
            #   samples would start coming back `limitatore` — the verdict says
            #   it, and it is the first of the four causes it prints.
            falliti[ind] = 0
            bannati.discard(ind)
            esiti.append(("SBLOCCA", None, ""))
            continue
        if ind in bannati:
            esiti.append(("RESPINTO", TROPPI_TENTATIVI, "bannato"))
            continue
        if p["caso"] == "giusta":
            falliti[ind] = 0
            esiti.append(("AMMESSO", None, ""))
            continue
        falliti[ind] = falliti.get(ind, 0) + 1
        picco[ind] = max(picco.get(ind, 0), falliti[ind])
        # ⛔ The third failed one still receives `CREDENZIALI_ERRATE` — it is the
        #    one that MAKES the ban trigger, not the first that suffers it.
        #    Whoever expected the refusal already at the third would look for a
        #    defect that is not there.
        esiti.append(("RESPINTO", CREDENZIALI_ERRATE, ""))
        if falliti[ind] >= SOGLIA:
            bannati.add(ind)
    return esiti, picco


def verifica_piano(passi, modo):
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
    esiti, picco = simula(passi)
    bloccati = [i + 1 for i, (_m, mo, _c) in enumerate(esiti)
                if mo == TROPPI_TENTATIVI]
    righe = [f"peak of the failures per address: "
             f"{ {k: v for k, v in sorted(picco.items())} or 'none' }",
             f"attempts the model sees blocked: {bloccati or 'none'}"]
    if modo == "sotto-soglia":
        ok = not bloccati and max(picco.values(), default=0) <= BILANCIO
        righe.append(f"expected: none blocked, and peak ≤ {BILANCIO} "
                     f"(threshold {SOGLIA})")
    elif modo == "banna-al-4":
        ok = bloccati == [4]
        righe.append("expected: ONLY the fourth blocked — the first three go "
                     "through PAM, and the third is the one that MAKES the ban trigger")
    elif modo == "non-banna":
        ok = (not bloccati) and max(picco.values(), default=0) >= 2
        righe.append("expected: none blocked, and at least one address at 2 "
                     "failures (if it did not get there, the check would be "
                     "green by construction)")
    else:
        ok, _ = False, righe.append(f"unknown mode: {modo}")
    return ok, esiti, righe


# ===========================================================================
# The plans
# ===========================================================================
def piano_campioni(k, per_caso, indirizzi, utente, inesistente):
    """A block: `per_caso` triplets, with the failures alternating between the addresses.

    ⛔ The addresses alternate **between the FAILURES**, not between the steps: only
       the failures move the count of §4.4-bis, and alternating on all the steps
       would leave the alternation at the mercy of where the success falls.

    ⚠ The rotation starts from `k`, so no case stays tied to an address: if one
      day the two paths had different times, the difference would spread over
      all three medians instead of separating one of them."""
    passi, falliti = [], 0
    for g in range(per_caso):
        for caso in ROTAZIONI[(k + g) % len(ROTAZIONI)]:
            ind = indirizzi[(falliti + k) % len(indirizzi)]
            if caso != "giusta":
                falliti += 1
            passi.append({"caso": caso, "indirizzo": ind,
                          "nome": inesistente if caso == "inesistente" else utente,
                          "scaldata": k == 0})
    return passi


def piano_ban(indirizzi, utente, nomi):
    """⛔ THE BAN RUN: three failed with THREE DIFFERENT NAMES, then the RIGHT password.

    ⭐ The fourth attempt **has the right password** and must be refused anyway:
       *«it is the line that tells a ban from a counter, and it is also the
       symptom the user will see — I typed it right and it does not let me in —
       so it is intended and must be tested, not avoided»* (`FASI.md` §01-filo-nudo B8).

    ⛔ All four from the SAME address: the count is per address, and alternating
       here would mean never reaching three."""
    a = indirizzi[0]
    passi = [{"caso": "inesistente", "indirizzo": a, "nome": nomi[0],
              "scaldata": False},
             {"caso": "sbagliata", "indirizzo": a, "nome": utente,
              "scaldata": False},
             {"caso": "inesistente", "indirizzo": a, "nome": nomi[2],
              "scaldata": False},
             # ⛔ the fourth: the RIGHT password
             {"caso": "giusta", "indirizzo": a, "nome": utente,
              "scaldata": False}]
    return passi


def piano_azzeramento(indirizzi, utente, inesistente):
    """⭐ THE CHECK THAT SAYS NO: 2 failed · 1 succeeded · 2 failed.

    *«If the success did not reset, the second block would already have
    triggered»* (`FASI.md` §01-filo-nudo B8).  ⛔ Counting all the failures, the
    **third** — that is the first after the success — would be the one that makes
    the ban trigger on a server that does not reset.

    ⚠ It runs on the SECOND address, and it is not a detail: the first is about
      to be banned, and a check that says «it is not banned» conducted on the
      address that will be banned right after would be unreadable."""
    b = indirizzi[1]
    return [{"caso": "sbagliata", "indirizzo": b, "nome": utente, "scaldata": False},
            {"caso": "inesistente", "indirizzo": b, "nome": inesistente, "scaldata": False},
            {"caso": "giusta", "indirizzo": b, "nome": utente, "scaldata": False},
            {"caso": "sbagliata", "indirizzo": b, "nome": utente, "scaldata": False},
            {"caso": "inesistente", "indirizzo": b, "nome": inesistente, "scaldata": False}]


# ===========================================================================
# The execution
# ===========================================================================
# ⛔ THE TARGET GOES INTO EVERY LINE, and this variable puts it there instead of
#    the twenty points that call `scrivi()`.  ⚠ The concrete case is already on
#    disk: `banchi/prodotto/b8-campioni.jsonl` are the samples of the fixed second
#    taken against the PRODUCT on the night of 10 August, and `/media/REMOTIX/src/
#    b8-fatti.jsonl` those taken against the GRAFT.  Same name, same shape,
#    same fields — and no line, in either of the two, says which server
#    answered.  Whoever put them together «to have more samples» would compute
#    the median of two different populations believing they are reducing the noise.
BERSAGLIO = {"bersaglio": "non dichiarato", "porta": None, "md5": "ignota"}

# ⛔ The lines the log reader looks for, and they are WRITTEN DIFFERENTLY in the two
#    servers: `principale()` fills them from the target's profile.  ⚠ The values
#    below are the graft's and serve only so that the module can be imported: if
#    these stayed against the product, the reader would say «the server said
#    nothing about the ban» on a server that does say it.
R_BAN = {"caricati": "bans loaded:",
         "illeggibile": "COULD NOT READ the ban file",
         "pagina": "TCP page at"}

# ===========================================================================
# ⛔⭐ HOW A PAM VERDICT IS READ IN THE LOG — and why NOT FROM THE END
# ===========================================================================
# *Defect paid for on 12 Aug 2026, and this bench stayed **blind** for a whole
#  recertification run without saying a word.*
#
# ⛔ WHAT HAPPENED.  Here there was:
#
#      ultimo_pam = "ammesso" if riga.rstrip().endswith("ammesso") else "respinto"
#
#    and the line of `rcp.c` really ended with the verdict's word.  Then the cure
#    of `DECISIONI.md` §1.10 (PAM off the single thread) appended to its tail
#    the explanation of the fallback:
#
#      PAM ha risposto: ammesso  ⚠ (per via SINCRONA: nessun gancio asincrono
#      collegato — il filo e' rimasto fermo)
#
#    ⇒ `endswith("ammesso")` became **always false**, every answer ended up among
#    the refused — **52 lines, 0 admitted** — `imputato_dei_tempi()` could no
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
#    `re.search(r"(-?\d+) indirizzi caricati", …)` ten lines further down in this
#    very file): one anchors to the **stable piece** of the line — the name of
#    the fact and the word that qualifies it — and leaves free **everything that
#    comes after**.  An explanation appended at the tail, another emoji, a second
#    field: none of these touches it.
#
# ⚠ And `[^:]*` between «answered» and the colon is not a whim: the cure of §1.10
#   wrote a SECOND form of the same line, for the asynchronous road —
#   `rcp.c:2636`, «PAM ha risposto (pratica 7): ammesso  ⭐ …» — which the graft
#   today does not travel but the product will.  An anchor that demanded the
#   colon right after «answered» would be blind to that one, and the blindness
#   would arrive **the day the bench is pointed at the product**.
R_PAM = re.compile(r"PAM answered\b[^:]*:\s*(admitted|refused)\b")
# ⛔ And the line is recognised BEFORE knowing how to read it: «it is not a PAM
#    line» and «it is a PAM line I cannot read» are two different facts, and the
#    second is the one that today cost a run.
R_PAM_RIGA = "PAM answered"

# ⛔ How many lines are needed for «all in the same box» to be an accusation and
#    not a chance: below this threshold it is just said.  ⚠ The real run carries
#    about fifty.
SOGLIA_MONOCATEGORIA = 5


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
def tutto_in_una_casella(che_cosa, caselle, minimo=SOGLIA_MONOCATEGORIA):
    """(suspicious, lines) — suspicious=True when ONE single box is inhabited.

    `caselle` is {name: how many}.  ⛔ It does not judge the facts: it judges
    **whoever put them in the boxes**, which is the only defendant no other check
    of this file looks at."""
    tot = sum(caselle.values())
    conto = " · ".join(f"{k}: {v}" for k, v in caselle.items())
    if tot == 0:
        return False, [f"⚠ {che_cosa}: NO fact to classify ({conto}) — "
                       f"and «no fact» is not «all the same»"]
    abitate = [k for k, v in caselle.items() if v]
    if len(abitate) > 1 or tot < minimo:
        return False, [f"⚠ {che_cosa}: {conto} (out of {tot})"]
    return True, [
        f"⛔ {che_cosa}: EVERYTHING IN ONE SINGLE BOX — {conto} (out of {tot}), and "
        f"the only inhabited one is «{abitate[0]}»",
        f"⛔ a classifier that out of {tot} facts puts **not even one** "
        f"in the other {len(caselle) - 1} boxes is almost always wrong: "
        f"the first defendant is the BENCH, not the server (`REVIEWER.md` §1)",
        f"⛔ and it is form E8 — «empty» and «forbidden» look the same — "
        f"applied to a counter: «the facts are all the same» and «I can no longer "
        f"read the facts» here have the same face",
        f"⚠ to look at first: the anchor with which the log line is "
        f"read.  On 12 Aug 2026 an explanation appended at the tail of "
        f"«PAM ha risposto: ammesso» was enough to put 52 out of 52 in the "
        f"wrong box, and B8 went from 5 to 1 on a healthy product",
    ]


def scrivi(uscita, rec):
    """One line per fact, written and **synced** right away.

    ⚠ A file written and closed is a fact; a line in a buffer is a hope about
      the moment someone will see it (`LEZIONI.md` §1.9, seventh guise) — and
      this process dies and is reborn at every phase."""
    fuori = dict(BERSAGLIO)
    fuori.update(rec)
    with open(uscita, "a") as f:
        f.write(json.dumps(fuori, ensure_ascii=False) + "\n")
        f.flush()
        os.fsync(f.fileno())


def esistenza(nome, deve_esistere):
    """⛔ «User does not exist» is VERIFIED, not assumed.

    If the name we believe nonexistent were a real user, «inesistente» and
    «sbagliata» would be **the same case** measured twice, and the two medians
    would coincide by construction: the emptiest green of all."""
    try:
        pwd.getpwnam(nome)
        c_e = True
    except KeyError:
        c_e = False
    return c_e == deve_esistere, c_e


async def prova_indirizzi(indirizzi, porta):
    """⛔ Can the bench talk from BOTH addresses? — it is asked first.

    ⚠ It gets to `ECCOMI` and closes: no `CREDENZIALI`, so **no count moves**
      and no place is taken.  It is a check that costs nothing to the balance of
      §4.4-bis."""
    for ind in indirizzi:
        gestore = None
        try:
            gestore, cli, stato = await apri(ind, porta)
            if stato != "200":
                raise RuntimeError(f":status={stato}")
            cli.apri_controllo()
            cli.manda(inquadra(b3.T["CIAO"], b3.corpo_ciao()))
            await b3.attendi(cli, "ECCOMI", attesa=10)
        except Exception as e:  # noqa: BLE001
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ from «{ind}» one does not get to ECCOMI: "
                  f"{type(e).__name__}: {e}")
            print(f"        the server must be running on 0.0.0.0 and answering "
                  f"on both addresses, or the balance of §4.4-bis does not "
                  f"have the margin it declares (B0.3)")
            return False
        finally:
            if gestore is not None:
                try:
                    await gestore.__aexit__(None, None, None)
                except Exception:  # noqa: BLE001
                    pass
    print(f"    {VERDE}OK{GRIGIO}  the server answers on both "
          f"addresses: {', '.join(indirizzi)}  (up to ECCOMI, without touching "
          f"any count)")
    return True


async def esegui(a, passi, tipo, etichetta, modo, confronta_modello=True):
    """Runs an already verified plan, and writes one record per attempt.

    ⚠ `confronta_modello=False` for the only case in which the model **cannot**
      know the answer: the attempt after the server restart, where the ban
      arrives from DISK and not from the failures of this run.  Demanding there
      agreement with the model would give red on the right code, and the red
      would end up on the wrong defendant — which is the defect `LEZIONI.md`
      §1.9 calls the seventh guise."""
    ok, esiti, righe = verifica_piano(passi, modo)
    print(f"    -- plan of «{etichetta}»: {len(passi)} attempts, mode «{modo}» "
          f"(threshold {SOGLIA}, balance {BILANCIO}, window {FINESTRA_MIN} min)")
    for r in righe:
        print(f"       {r}")
    if not ok:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ the plan does not do what it must: it does not start. "
              f"A plan that overflows would measure the ban believing it measures PAM; "
              f"one that does not ban where it must would make the check blind")
        return 2
    for i, p in enumerate(passi, 1):
        parola = a.parola if p["caso"] == "giusta" else a.sbagliata
        atteso_msg, atteso_motivo, _perche = esiti[i - 1]
        rec = await un_tentativo(p["indirizzo"], a.porta, p["nome"], parola)
        rec.update({"giro": a.giro, "tipo": tipo, "etichetta": etichetta,
                    "blocco": a.blocco, "ordine": i, "caso": p["caso"],
                    "scaldata": p["scaldata"],
                    "classe": classifica(rec, p["caso"]),
                    # ⭐ the model's expectation travels with the attempt: the
                    #    verdict compares it with what arrived, one by one,
                    #    instead of looking only at the total.
                    "atteso_modello": atteso_msg,
                    "atteso_motivo": atteso_motivo})
        scrivi(a.uscita, rec)
        ms = "  —  " if rec["ms"] is None else f"{rec['ms']:8.1f}"
        motivo = MOTIVI.get(rec["motivo"], "") if rec["motivo"] is not None else ""
        atteso = MOTIVI.get(atteso_motivo, atteso_msg)
        chiude = "" if rec["chiusura"] is None else \
            f"chiusura={MOTIVI.get(rec['chiusura'], hex(rec['chiusura']))}"
        if not confronta_modello:
            concorda = "⚠ the model does not judge here (the ban comes from disk)"
        elif rec["messaggio"] == atteso_msg and rec["motivo"] == atteso_motivo:
            concorda = ""
        else:
            concorda = f"⛔ the model said {atteso}"
        marca = "warm-up" if p["scaldata"] else ""
        print(f"       {i:2d}. {p['caso']:12s} {p['indirizzo']:13s} "
              f"{p['nome']:16s} {ms} ms  "
              f"{rec['messaggio'] or rec['errore']:10s} {motivo:18s} "
              f"{rec['classe']:10s} {chiude} {marca} {concorda}")
    return 0


def pagina_in_tls(a):
    """⛔ In which language the ban page speaks, on THIS target.

    innesto   in plain text — `01-b3-rcp-innesta.py` writes `HTTP/1.1 200 OK` on a
              bare fd, and in the whole file there is not one TLS line;
    prodotto  in TLS — `SPECIFICHE.md` §11.5, and `01-p1-prodotto.sh`
              queries it with `curl -k https://`.

    ⚠ AND THE RIGHT PLACE FOR THIS LINE IS NOT HERE: it is the shared profile
      (`01-b0-bersaglio.py`), next to the other differences between the two
      servers — the start-up line about the ban, the page format, the
      inactivity cap.  It is written here because on the evening of 11 Aug 2026
      three other benches are using the profile, and a new key is added when
      nobody else is inside.  ⛔ As long as it is here, it is a fifth copy of a
      difference — that is exactly the shape R12C.5 has already made us pay
      for: it is read from the profile as soon as the key exists."""
    return bool(a.prof.get("pagina_tls", a.bersaglio == "prodotto"))


def guarda_pagina(a, indirizzo, etichetta, atteso_bannato):
    """The page, read and WRITTEN in the facts file — and compared right away."""
    rec = leggi_pagina(indirizzo, a.porta, tls=pagina_in_tls(a))
    rec.update({"giro": a.giro, "tipo": "pagina", "etichetta": etichetta,
                "atteso_bannato": atteso_bannato})
    scrivi(a.uscita, rec)
    if rec["errore"]:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ the page from «{indirizzo}» did not "
              f"load: {rec['errore']}")
        print(f"        §4.4-bis: «not a network error, not a silence» — and "
              f"a silence is exactly what I have just received")
        return rec
    quanto = "" if rec["ore"] is None else f" · {rec['ore']}h {rec['minuti']}m left"
    print(f"    -- page from {indirizzo:13s} → HTTP {rec['stato']} · "
          f"bannato={rec['bannato']} (expected {atteso_bannato}) · "
          f"«attempts exhausted» {'present' if rec['frase'] else 'ABSENT'}"
          f"{quanto} · {rec['byte']} bytes")
    return rec


def sblocca_e_dichiara(a, indirizzi, perche, pretendi=None):
    """⛔ Every unblock is declared — B0.3: «or *the ban did not trigger* and
    *someone removed it* look the same»."""
    esiti = []
    for ind in indirizzi:
        esito, dettaglio = cmd.sblocca(a.comando, ind)
        rec = {"giro": a.giro, "tipo": "sblocco", "etichetta": perche,
               "indirizzo": ind, "esito": esito, "dettaglio": dettaglio,
               "preteso": pretendi}
        scrivi(a.uscita, rec)
        colore = ROSSO if esito is None else GRIGIO
        print(f"    {colore}--{GRIGIO}  unblock «{ind}» ({perche}): "
              f"{esito or '⛔ I DID NOT TALK TO THE COMMAND'} — {dettaglio}")
        esiti.append(esito)
    return esiti


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


def intervallo_differenza(xa, xb):
    """The 95 % interval of the difference between the two medians, by resampling.

    ⭐ The seed is fixed: two runs of the verdict on the same samples must give
       the **same** line, or the bench itself becomes a source of noise."""
    r = random.Random(SEME)
    na, nb = len(xa), len(xb)
    diff = []
    for _ in range(RIPETIZIONI):
        ca = [xa[r.randrange(na)] for _ in range(na)]
        cb = [xb[r.randrange(nb)] for _ in range(nb)]
        diff.append(statistics.median(ca) - statistics.median(cb))
    diff.sort()
    lo = diff[int(0.025 * RIPETIZIONI)]
    hi = diff[min(RIPETIZIONI - 1, int(0.975 * RIPETIZIONI))]
    return lo, hi


# ===========================================================================
# The server log: the second witness, and it is NOT the arbiter
# ===========================================================================
def leggi_registro(percorso):
    """What the SERVER says — to separate the defendants, not to judge.

    ⛔ It is not the arbiter: the time that counts is the one read from the
       receiving side, and the log is the same hand that wrote the code.  It
       serves to distinguish «what governed was the fixed delay» from «what
       governed was PAM», and to say how many server lives and which addresses
       there really were.

    ⚠ If the log is not there or says nothing, nothing is invented: it is declared.
      «Empty» and «not read» are two different facts."""
    if not percorso or not os.path.exists(percorso):
        return None, "the server log was not read (missing file)"
    d = {"fissi": [], "ammessi": [], "respinti": [], "senza_pam": [],
         "indirizzi": set(),
         "avvii": [], "ban": [], "sbloccati": [], "non_bannati": [],
         "pagine": [], "carichi": [], "illeggibili": 0, "vite": 0,
         # ⛔ The three boxes of the CLASSIFIER, counted separately from the medians:
         #    they serve to judge whoever reads, not what was read.
         "pam": {"admitted": 0, "refused": 0, "illeggibile": 0},
         "pam_esempi": []}
    ultimo_pam = None
    try:
        with open(percorso, errors="replace") as f:
            for riga in f:
                if R_PAM_RIGA in riga:
                    # ⛔ The anchor is on the STABLE piece, not on the end of the
                    #    line: what comes after the verdict's word belongs to
                    #    whoever writes the log, and it changes (12 Aug 2026).
                    m = R_PAM.search(riga)
                    if m:
                        ultimo_pam = m.group(1)
                        d["pam"][ultimo_pam] += 1
                    else:
                        # ⛔ AND HERE ONE DOES NOT FALL BACK ON «refused».  Until 12
                        #    Aug 2026 an unreadable line and a refused one were the
                        #    same fact — E8 — and this `None` is the cure: a verdict
                        #    that was not understood enters neither of the two
                        #    medians, and it is counted.
                        ultimo_pam = None
                        d["pam"]["illeggibile"] += 1
                        if len(d["pam_esempi"]) < 3:
                            d["pam_esempi"].append(riga.strip()[:150])
                elif "the fixed second has passed" in riga:
                    # ⚠ Here too the anchor is the stable piece — «(N ms)» —
                    #   and not «what comes after the first parenthesis».
                    m = re.search(r"\((-?\d+) ms\)", riga)
                    if not m:
                        continue
                    n = int(m.group(1))
                    d["fissi"].append(n)
                    if ultimo_pam == "admitted":
                        d["ammessi"].append(n)
                    elif ultimo_pam == "refused":
                        d["respinti"].append(n)
                    else:
                        d["senza_pam"].append(n)
                elif " da=" in riga and ("respinto motivo" in riga or "admitted utente" in riga):
                    # ⛔ AND NOT EVEN THIS ONE IS READ FROM THE END.  It was
                    #    `riga.rsplit(" da=", 1)[1].strip().rsplit(":", 1)[0]`,
                    #    that is «the address is the last thing on the line»: the
                    #    same anchor that today blinded the PAM verdict, on a line
                    #    that `rcp.c:979` and `rcp.c:2700` may lengthen tomorrow as
                    #    they lengthened that one.  ⇒ The `da=` field is taken and
                    #    it stops at the first space.
                    m = re.search(r"\bda=(\S+)", riga)
                    if m:
                        d["indirizzi"].add(m.group(1).rsplit(":", 1)[0])
                elif R_BAN["caricati"] in riga:
                    d["vite"] += 1
                    # ⛔⭐ AND THE START-UP LINE IS WRITTEN DIFFERENTLY IN THE TWO SERVERS.
                    #
                    #     innesto   «REMOTIX B3: bans loaded: N»
                    #               (logs saved before 10 Oct 2026:
                    #               «ban caricati: N», still read)
                    #     prodotto  «HH:MM:SS.mmm avvio  ban: <file>, N
                    #               addresses loaded»
                    #
                    #  ⚠ Looking for the graft's form against the product would
                    #    have given «vite = 0» and «the server said NOTHING about
                    #    the ban at start-up»: a full red on a server that does
                    #    write that line, and the red would have ended up on the
                    #    wrong defendant.
                    m = re.search(r"(-?\d+) addresses loaded", riga) or \
                        re.search(r"(?:bans loaded|ban caricati): (-?\d+)", riga)
                    d["carichi"].append(int(m.group(1)) if m else None)
                    d["avvii"].append(riga.strip())
                elif R_BAN["illeggibile"] in riga:
                    d["vite"] += 1
                    d["illeggibili"] += 1
                    d["avvii"].append(riga.strip())
                elif "BANNED address" in riga and "UNBLOCKED" not in riga:
                    d["ban"].append(riga.strip())
                elif "UNBLOCKED on command" in riga:
                    d["sbloccati"].append(riga.strip())
                elif "it was NOT banned, I removed nothing" in riga:
                    d["non_bannati"].append(riga.strip())
                elif R_BAN["pagina"] in riga:
                    d["pagine"].append(riga.strip())
    except OSError as e:
        return None, f"the server log cannot be read: {e}"
    d["indirizzi"] = sorted(d["indirizzi"])
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
#    `AMMESSO` — a slow `getpwnam`, a synchronous write — and PAM is left to
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
def imputato_dei_tempi(serie, reg):
    """(name, lines) with name in «PAM» · «NOSTRO» · None (not measured)."""
    righe = []
    if reg is None:
        return None, ["⛔ the server log was not read: NO "
                      "defendant can be named, and naming one anyway "
                      "would be the seventh guise of `LEZIONI.md` §1.9"]
    resp = statistics.median(reg["respinti"]) if reg["respinti"] else None
    amm = statistics.median(reg["ammessi"]) if reg["ammessi"] else None
    if resp is None or amm is None:
        # ⛔ AND HERE IT ALSO SAYS WHY — 12 Aug 2026.  Until this morning this
        #    line stopped at «the log does not carry the two medians», which
        #    reads as *«the server did not write them»*.  ⛔ But the case that
        #    really showed up is the other one — **it wrote them, and it is I who
        #    can no longer read them** — and the two look the same (E8).  Whoever
        #    reads the verdict must find the first defendant here.
        righe = [f"⛔ the log does not carry the two medians that are needed "
                 f"(refused: {len(reg['respinti'])} lines · admitted: "
                 f"{len(reg['ammessi'])} lines): without both one cannot "
                 f"tell «PAM delays the failures» from «the delay is "
                 f"ours», and nobody is named"]
        _, righe_cieco = tutto_in_una_casella(
            "and the classification that fills them", reg["pam"])
        righe += righe_cieco
        return None, righe
    med = {c: statistics.median(serie[c]) for c in CASI if serie[c]}
    if not med:
        return None, ["⛔ no series of samples: there is no "
                      "separation to attribute"]
    lento = max(med, key=med.get)
    oltre_r, oltre_a = resp - RITARDO_FISSO, amm - RITARDO_FISSO
    righe.append(f"what the SERVER declares it waited beyond the "
                 f"fixed second: refused {oltre_r:+.0f} ms · admitted "
                 f"{oltre_a:+.0f} ms  (margin {MARGINE_IMPUTATO:.0f} ms)")
    righe.append(f"the slowest case on the WIRE: «{lento}» "
                 f"({med[lento]:.0f} ms)  ·  " +
                 " · ".join(f"{c} {med[c]:.0f}" for c in CASI if c in med))
    if oltre_r >= MARGINE_IMPUTATO and (resp - amm) >= MARGINE_IMPUTATO \
            and lento != "giusta":
        righe.append("⇒ ⛔ WHAT GOVERNS THE TIMES IS **PAM**: the server "
                     "waited beyond the fixed second ONLY on the failures, "
                     "which is the signature of `pam_faildelay`, and the slow "
                     "case on the wire is a refused one.  The cure is in "
                     "`banchi/rcp/autenticazione.c` and in the PAM stack, not in "
                     "`rcp.c`")
        return "PAM", righe
    if lento == "giusta" or (oltre_a - oltre_r) >= MARGINE_IMPUTATO:
        righe.append("⇒ ⛔ THE DEFENDANT IS NOT PAM: the slow path is that "
                     "of the AMMESSO, where `pam_faildelay` has no say — "
                     "`pam_faildelay` delays the FAILURES.  The delay is "
                     "OURS, and it is looked for on the path leading to `AMMESSO` "
                     "(rcp.c: `S_ATTESA_VERDETTO` → `T_AMMESSO`), not in the "
                     "PAM stack")
        return "NOSTRO", righe
    if oltre_r < MARGINE_IMPUTATO and oltre_a < MARGINE_IMPUTATO:
        righe.append("⇒ ⛔ THE DEFENDANT IS NOT PAM: the server declares it "
                     "answered almost right after the fixed second in both "
                     "directions — that is the fixed delay covered everything and "
                     "PAM delayed nothing — and the medians separate "
                     "ALL THE SAME.  The time is lost OUTSIDE the point where the "
                     "server measures it: our path, or the network")
        return "NOSTRO", righe
    righe.append("⇒ ⚠ THE NUMBERS DO NOT SEPARATE THE TWO DEFENDANTS: the log says "
                 "that someone waited beyond the fixed second, but not in the "
                 "direction that tells PAM from our path.  Nobody is "
                 "named — «I do not know» is an outcome, «it is PAM» said out "
                 "of habit is not")
    return None, righe


# ===========================================================================
# The verdict
# ===========================================================================
def _serie(campioni, caso):
    return [r["ms"] for r in campioni
            if r["caso"] == caso and not r["scaldata"] and r["classe"] == "atteso"]


def verdetto(a):
    if not os.path.exists(a.uscita):
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ there is nothing to judge: "
              f"{a.uscita} does not exist")
        return 2
    dati = []
    with open(a.uscita) as f:
        for riga in f:
            riga = riga.strip()
            if riga:
                dati.append(json.loads(riga))
    # ⛔ A file from ANOTHER run is not an empty file, and it is not this run.
    estranei = [r for r in dati if r.get("giro") != a.giro]
    if estranei:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ {len(estranei)} lines out of {len(dati)} are "
              f"from another run: I do not judge a stale file")
        return 2
    if not dati:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ the file is there and it is empty: no facts")
        return 2

    # ⛔ TWO COUNTERS, AND IT IS NOT LENIENCY — it is `LEZIONI.md` §1.11 and the
    #    rule of the «four outcomes, not two».
    #
    #    `guasti` counts what this bench has the right to call a defect of OURS.
    #    `guasti_mediane` counts the only thing §4.4-bis had already declared
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
    guasti, guasti_mediane, sospeso = 0, 0, False
    campioni = [r for r in dati if r["tipo"] == "campione"]
    tentativi = [r for r in dati if r["tipo"] in ("campione", "ban", "controllo")]
    pagine = [r for r in dati if r["tipo"] == "pagina"]
    sblocchi = [r for r in dati if r["tipo"] == "sblocco"]
    blocchi = sorted({r["blocco"] for r in campioni})

    # ── 0. the denominators ─────────────────────────────────────────────────
    print()
    print("    == THE DENOMINATORS — on what this run looked")
    print(f"    --  facts recorded: {len(dati)}  (attempts {len(tentativi)} · "
          f"page readings {len(pagine)} · unblocks {len(sblocchi)})")
    print(f"    --  blocks of samples: {len(blocchi)}  "
          f"(between one block and the next one unblocks, and it is declared)")
    # ⛔ And a verdict has a denominator: how many things it approved
    #    (`LEZIONI.md` §1.9 rule 6).  If it is zero no outcome is given.
    if not tentativi:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ ZERO attempts: «all those tested "
              f"went well» is true even when the tested are zero")
        return 2

    serie = {}
    for caso in CASI:
        del_caso = [r for r in campioni if r["caso"] == caso]
        scaldate = [r for r in del_caso if r["scaldata"]]
        tenuti = [r for r in del_caso if not r["scaldata"]]
        buoni = [r for r in tenuti if r["classe"] == "atteso"]
        serie[caso] = [r["ms"] for r in buoni]
        limitati = [r for r in tenuti if r["classe"] == "limitatore"]
        inattesi = [r for r in tenuti if r["classe"] == "inatteso"]
        errori = [r for r in tenuti if r["classe"] == "errore"]
        per_ind = {}
        for r in buoni:
            per_ind[r["indirizzo"]] = per_ind.get(r["indirizzo"], 0) + 1
        print(f"    --  {caso:12s} kept {len(buoni):3d} out of {len(tenuti):3d} · "
              f"discarded as warm-up {len(scaldate)} · "
              f"⛔ ban answers {len(limitati)} · unexpected {len(inattesi)} · "
              f"errors {len(errori)} · addresses {per_ind}")
        if limitati:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ {len(limitati)} samples of «{caso}» "
                  f"received TROPPI_TENTATIVI: the balance of §4.4-bis did not "
                  f"hold, and those times are the BAN's, not PAM's")
            print(f"        ⚠ four causes, and they must be separated: (1) the unblock "
                  f"between the blocks did not work; (2) the plan really overflows; "
                  f"(3) a previous block left some failures; "
                  f"(4) the server counts more than §4.4-bis says")
            guasti += 1
        if inattesi or errori:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ «{caso}»: {len(inattesi)} unexpected "
                  f"answers and {len(errori)} errors — a case that does not receive "
                  f"what it must is not a sample of that case")
            for r in (inattesi + errori)[:3]:
                print(f"        {r['messaggio'] or ''} {r['errore']}")
            guasti += 1

    # ── 1. the fixed second ─────────────────────────────────────────────────
    print()
    print(f"    == ⛔ First criterion: no PAM answer before "
          f"{RITARDO_FISSO:.0f} ms (§4.4-bis)")
    da_pam = [r for r in tentativi if r["classe"] == "atteso" and r["ms"] is not None]
    sotto = [r for r in da_pam if r["ms"] < RITARDO_FISSO]
    print(f"    --  looked at {len(da_pam)} answers (samples, warm-ups and ban "
          f"run together: the fixed delay holds for ALL of them, «even when the "
          f"answer is AMMESSO»)")
    if not da_pam:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ no answer to look at")
        guasti += 1
    elif sotto:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ {len(sotto)} responses below the second. "
              f"The fastest: {min(r['ms'] for r in sotto):.1f} ms")
        for r in sotto[:5]:
            print(f"        {r['caso']:12s} {r['messaggio']} {r['ms']:.1f} ms")
        guasti += 1
    else:
        print(f"    {VERDE}OK{GRIGIO}  {len(da_pam)} out of {len(da_pam)} ≥ "
              f"{RITARDO_FISSO:.0f} ms — the fastest: "
              f"{min(r['ms'] for r in da_pam):.1f} ms")
    # ⚠ And the ban's refusal is measured SEPARATELY, and it makes neither red nor green.
    #   §4.4-bis says that «the refusal of a banned address does not go through the
    #   fixed second»; `rcp.c` makes it go through anyway, because it decides AFTER
    #   having received `CREDENZIALI` — which is the only road that leaves it a
    #   `RESPINTO` to send, that is what B8 demands.  Two readings, and the
    #   difference is measured instead of judged.
    del_ban = [r["ms"] for r in tentativi
               if r["classe"] == "limitatore" and r["ms"] is not None]
    if del_ban:
        print(f"    --  ⚠ and the TROPPI_TENTATIVI answers (which do not go through PAM): "
              f"n={len(del_ban)}  median {statistics.median(del_ban):.1f} ms  "
              f"min {min(del_ban):.1f} ms")
        print(f"        §4.4-bis says this refusal «does not go through the fixed "
              f"second»; rcp.c makes it go through.  The number is here, and it is not an "
              f"outcome: it is a defect of the document to be closed in one direction or "
              f"the other")
    else:
        print(f"    --  ⛔ no TROPPI_TENTATIVI answer in the whole run: the "
              f"ban run below cannot have passed")

    # ── 2. the three medians ────────────────────────────────────────────────
    print()
    print("    == ⛔ Second criterion: the three medians, and whether they separate")
    for caso in CASI:
        x = serie[caso]
        if not x:
            print(f"    --  {caso:12s} n=0 — no samples")
            continue
        print(f"    --  {caso:12s} n={len(x):3d}  min {min(x):8.1f}  "
              f"p25 {quantile(x, .25):8.1f}  median {statistics.median(x):8.1f}  "
              f"p75 {quantile(x, .75):8.1f}  max {max(x):8.1f}  "
              f"MAD {mad(x):6.1f}   (ms)")

    magri = [c for c in CASI if len(serie[c]) < MINIMO_CAMPIONI]
    if magri:
        print(f"    {GIALLO}??{GRIGIO}  ⚠ fewer than {MINIMO_CAMPIONI} samples for "
              f"{', '.join(magri)}: the verdict on the medians is SUSPENDED, not green")
        sospeso = True

    print()
    print("    difference of the medians, with the 95 % interval that contains it:")
    for u, v in (("inesistente", "sbagliata"), ("inesistente", "giusta"),
                 ("sbagliata", "giusta")):
        xa, xb = serie[u], serie[v]
        if len(xa) < 3 or len(xb) < 3:
            print(f"    {GIALLO}??{GRIGIO}  {u} − {v}: insufficient samples "
                  f"({len(xa)} and {len(xb)})")
            sospeso = True
            continue
        d = statistics.median(xa) - statistics.median(xb)
        lo, hi = intervallo_differenza(xa, xb)
        risoluzione = (hi - lo) / 2.0
        contiene_zero = lo <= 0.0 <= hi
        n_ora = min(len(xa), len(xb))
        n_serve = int(n_ora * (risoluzione / RISOLUZIONE_VOLUTA) ** 2) + 1
        marca = f"{ROSSO}DISTINGUISHABLE{GRIGIO}" if not contiene_zero else (
            f"{VERDE}indistinguishable{GRIGIO}" if risoluzione <= RISOLUZIONE_VOLUTA
            else f"{GIALLO}SUSPENDED{GRIGIO}")
        segreto = (u, v) == ("inesistente", "sbagliata")
        nota = "  ⚠ THIS is the pair that tells the user names" if segreto \
            else "  (⚠ this pair carries no secret: see below)"
        print(f"      {u:12s} − {v:12s} {d:+9.1f} ms   "
              f"[{lo:+8.1f}; {hi:+8.1f}]   resolution ±{risoluzione:.1f} ms   "
              f"{marca}{nota}")
        if not contiene_zero:
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
            #       they are two different MESSAGES, `AMMESSO` and `RESPINTO`.  A
            #       stopwatch that separates them adds nothing to what the client
            #       already reads in the message.
            #
            # ⭐ So: the pair «inesistente − sbagliata» that separates is a defect
            #    of OURS and goes into full red.  The other two that separate go
            #    into their own counter, which leads to a different outcome with
            #    the culprit named.  ⚠ The convenient reading is not chosen and
            #    nothing is kept quiet: both are run and it is said which number
            #    belongs to which.
            if segreto:
                print(f"           ⛔ AND THIS IS THE SEPARATION §4.4 FORBIDS: "
                      f"with the stopwatch one reads whether a user name exists, which is "
                      f"exactly the thing the ban on the reason exists to "
                      f"hide")
                guasti += 1
            else:
                print(f"           ⚠ this separation says NOTHING the "
                      f"wire does not already say: «admitted» and «refused» are two "
                      f"different MESSAGES (§4.4).  It counts anyway — "
                      f"`FASI.md` §01-filo-nudo B8 asks for the THREE medians "
                      f"indistinguishable — but in its own counter, and with the culprit "
                      f"named at the end")
                guasti_mediane += 1
        elif risoluzione > RISOLUZIONE_VOLUTA:
            print(f"           ⚠ to get to ±{RISOLUZIONE_VOLUTA:.0f} ms with "
                  f"this noise ~{n_serve} samples per case would be needed "
                  f"(now {n_ora})")
            sospeso = True

    # ── 3. the ban run ──────────────────────────────────────────────────────
    print()
    print("    == ⛔ The ban: three failed with THREE DIFFERENT NAMES, then the RIGHT password")
    giro = sorted([r for r in dati if r["tipo"] == "ban"], key=lambda r: r["ordine"])
    if len(giro) != 4:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ the ban run has {len(giro)} attempts "
              f"instead of 4: it is not the sequence §4.4-bis describes")
        guasti += 1
    else:
        def nomina(msg, motivo):
            return MOTIVI.get(motivo, str(motivo)) if motivo is not None else (msg or "errore")
        print(f"        names:    " + " ".join(f"{r['nome']:18s}" for r in giro))
        print(f"        model:    " + " ".join(
            f"{nomina(r['atteso_modello'], r['atteso_motivo']):18s}" for r in giro))
        print(f"        on wire:  " + " ".join(
            f"{nomina(r['messaggio'], r['motivo']):18s}" for r in giro))
        # ⛔ THE THREE NAMES MUST BE DIFFERENT, and the bench compares it.
        nomi = [r["nome"] for r in giro[:3]]
        if len(set(nomi)) != 3:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the three names are not different ({nomi}): "
                  f"with the same name three times a server with the old per-NAME "
                  f"counter would give green, and the bench would prove the wrong "
                  f"rule")
            guasti += 1
        else:
            print(f"    {VERDE}OK{GRIGIO}  the three names are different: the count "
                  f"looks at the address and not at the name (`DECISIONI.md` §1.9)")
        divergenti = [r["ordine"] for r in giro
                      if r["messaggio"] != r["atteso_modello"]
                      or r["motivo"] != r["atteso_motivo"]]
        if divergenti:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the wire and the model of §4.4-bis "
                  f"split at attempts {divergenti}")
            guasti += 1
        quarto = giro[3]
        if quarto["motivo"] == TROPPI_TENTATIVI:
            print(f"    {VERDE}OK{GRIGIO}  ⭐ the FOURTH attempt had the RIGHT "
                  f"password and was refused anyway, with "
                  f"TROPPI_TENTATIVI: it is the line that tells a ban from a "
                  f"counter")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the fourth attempt — RIGHT password — "
                  f"received {nomina(quarto['messaggio'], quarto['motivo'])} "
                  f"instead of TROPPI_TENTATIVI")
            print(f"        ⚠ and if it is AMMESSO, the ban did not trigger: look at the "
                  f"server log below, line «BANNED address»")
            guasti += 1
        # ⛔ And the tab already open: the reason travels ALSO in the session
        #    closing code (§3.1 point 3, §4.4-bis point 2), and it is verified
        #    FROM THE RECEIVING SIDE.
        if quarto.get("chiusura") == TROPPI_TENTATIVI:
            print(f"    {VERDE}OK{GRIGIO}  ⭐ and the WebTransport session "
                  f"closed with TROPPI_TENTATIVI in the application error "
                  f"code — read from the receiving side (§3.1 point 3)")
        else:
            c = quarto.get("chiusura")
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the session closing code "
                  f"is {MOTIVI.get(c, c)}, not TROPPI_TENTATIVI: the tab already "
                  f"open — the one that does not reload the page — would stay "
                  f"waiting (§4.4-bis point 2)")
            guasti += 1

    # ── 4. the three checks that say NO ─────────────────────────────────────
    print()
    print("    == ⭐ The three checks that say NO")

    # 4a. another address gets in right away
    altro = [r for r in dati if r["tipo"] == "controllo"
             and r["etichetta"] == "altro-indirizzo"]
    if not altro:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ the check «another address gets "
              f"in» is missing: without it, «the fourth is refused» is compatible with a "
              f"server that stopped working")
        guasti += 1
    elif all(r["messaggio"] == "AMMESSO" for r in altro):
        print(f"    {VERDE}OK{GRIGIO}  1. ANOTHER address gets in right away with the "
              f"good credentials ({len(altro)} attempts): the server has not "
              f"stopped working, and the count is per address")
    else:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ 1. the other address does NOT get in: "
              f"{[r['messaggio'] for r in altro]}")
        print(f"        ⚠ four causes: (1) the ban is not per address — the "
              f"defect; (2) that address has a count of its own open; (3) PAM does not "
              f"allow verifying that user; (4) the user does not exist or "
              f"has no password")
        guasti += 1

    # 4b. the reset
    azz = sorted([r for r in dati if r["tipo"] == "controllo"
                  and r["etichetta"] == "azzeramento"], key=lambda r: r["ordine"])
    if len(azz) != 5:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ 2. the reset check has "
              f"{len(azz)} attempts instead of 5")
        guasti += 1
    else:
        motivi = [r["motivo"] for r in azz]
        bloccati = [r["ordine"] for r in azz if r["motivo"] == TROPPI_TENTATIVI]
        if not bloccati and azz[2]["messaggio"] == "AMMESSO":
            print(f"    {VERDE}OK{GRIGIO}  2. two failed · ONE SUCCEEDED · two "
                  f"failed: no block.  If the success did not reset, the "
                  f"third failed one would have made the ban trigger")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ 2. the reset did not happen "
                  f"(blocked: {bloccati or 'none'}; the third step "
                  f"received {azz[2]['messaggio']})")
            guasti += 1
        # ⛔ And the check of the check: the page must say that address is NOT
        #    banned.  Without it, «no block» would be compatible with a server
        #    that banned and does not say so.
        dopo = [r for r in pagine if r["etichetta"] == "azzeramento-dopo"]
        if dopo and dopo[0].get("bannato") is False:
            print(f"        ⭐ and the page confirms it from outside: that address "
                  f"is not banned (the count is {len([m for m in motivi if m == CREDENZIALI_ERRATE])} "
                  f"out of {SOGLIA})")
        elif dopo:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ but the page says bannato="
                  f"{dopo[0].get('bannato')}: the wire and the page do not agree")
            guasti += 1

    # 4c. persistence
    print()
    prima = [r for r in pagine if r["etichetta"] == "bannato-prima"]
    dopo = [r for r in pagine if r["etichetta"] == "bannato-dopo-riavvio"]
    filo_dopo = [r for r in dati if r["tipo"] == "controllo"
                 and r["etichetta"] == "dopo-riavvio"]
    if not prima or not dopo:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ 3. persistence was not proved "
              f"(page before: {len(prima)}, after the restart: {len(dopo)}): "
              f"without it, the ban may live in memory and a package update "
              f"gives three attempts to anyone — invariant I7")
        guasti += 1
    elif dopo[0].get("bannato") is True and filo_dopo and \
            all(r["motivo"] == TROPPI_TENTATIVI for r in filo_dopo):
        print(f"    {VERDE}OK{GRIGIO}  3. the ban SURVIVES the restart of the "
              f"server: after the second start the page still says it, and "
              f"on the wire the attempt with the right password still receives "
              f"TROPPI_TENTATIVI")
    else:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ 3. after the restart the address is no "
              f"longer banned: page bannato={dopo[0].get('bannato')}, on the wire "
              f"{[MOTIVI.get(r['motivo'], r['messaggio']) for r in filo_dopo]}")
        guasti += 1

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
    print(f"    --  ⛔ the three markers looked for here (`data-bannato`, "
          f"`data-restano-ms`, «attempts exhausted») are produced ONLY by the graft "
          f"of `01-b3-rcp-innesta.py`.  The product server in `src/` writes "
          f"the same thing in a format without a field in common: pointing "
          f"this bench there, these three lines would become red ON A "
          f"SERVER THAT DOES BAN")
    if not pagine:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ no reading of the page: point 1 "
              f"of §4.4-bis was not proved at all")
        guasti += 1
    for r in pagine:
        atteso = r["atteso_bannato"]
        buona = (not r["errore"] and r["stato"] == 200
                 and r["bannato"] is atteso
                 and (r["frase"] if atteso else not r["frase"]))
        if atteso and buona:
            buona = r["ore"] is not None
        segno = f"{VERDE}OK{GRIGIO}" if buona else f"{ROSSO}NO{GRIGIO}"
        print(f"    {segno}  {r['etichetta']:22s} from {r['indirizzo']:13s} → "
              f"HTTP {r['stato']} · bannato={r['bannato']} (expected {atteso}) · "
              f"frase={r['frase']} · ore={r['ore']} minuti={r['minuti']}"
              f"{' · ⛔ ' + r['errore'] if r['errore'] else ''}")
        if not buona:
            guasti += 1
    bannate = [r for r in pagine if r["atteso_bannato"] and r["ore"] is not None]
    if bannate:
        ore = bannate[0]["ore"]
        # ⚠ The hours left must be PLAUSIBLE: 12 right after the ban.  A
        #   «0 hours left» or a «4 billion left» would say that the page's clock
        #   is not the session's — the easiest defect to make and the hardest
        #   to see.
        if 1 <= ore <= BAN_ORE:
            print(f"    {VERDE}OK{GRIGIO}  and the hours left are plausible "
                  f"({ore} out of {BAN_ORE}): the page's clock is the "
                  f"session's")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the page says {ore} hours are left, "
                  f"and the ban lasts {BAN_ORE}: the two clocks are not the same")
            guasti += 1

    # ── 6. the unblock — and it is tested AT THE END ────────────────────────
    print()
    print("    == ⛔ The unblock command, tested AT THE END (B0.3)")
    finali = [r for r in sblocchi if r["etichetta"].startswith("prova-")]
    if not finali:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ the unblock was not tested on a real "
              f"ban: «removed» and «was not there» were not told apart")
        guasti += 1
    for r in finali:
        buono = r["esito"] == r["preteso"]
        segno = f"{VERDE}OK{GRIGIO}" if buono else f"{ROSSO}NO{GRIGIO}"
        print(f"    {segno}  {r['etichetta']:22s} «{r['indirizzo']}» → "
              f"{r['esito']} (expected {r['preteso']})")
        if not buono:
            guasti += 1
    dopo_sblocco = [r for r in dati if r["tipo"] == "controllo"
                    and r["etichetta"] == "dopo-sblocco"]
    if dopo_sblocco and all(r["messaggio"] == "AMMESSO" for r in dopo_sblocco):
        print(f"    {VERDE}OK{GRIGIO}  ⭐ and after the unblock that address GETS IN: "
              f"the unblock did not only change an answer, it put the "
              f"address back inside")
    else:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ after the unblock the address does not get in "
              f"({[r['messaggio'] for r in dopo_sblocco] or 'not tested'})")
        guasti += 1

    # ── 7. the second witness ───────────────────────────────────────────────
    print()
    print("    == ⚠ The server log — diagnosis and denominator, NOT arbiter")
    reg, perche = leggi_registro(a.registro)
    if reg is None:
        print(f"    --  {perche}")
        # ⛔ It is not the arbiter, but without it two checks above do not have
        #    their denominator: it is said, instead of pretending nothing.
        print(f"    {GIALLO}??{GRIGIO}  ⚠ without the log I cannot say how many "
              f"server lives there were nor how many bans it loaded: the "
              f"verdict on persistence is worth less than it seems")
        sospeso = True
    else:
        def med(x):
            return f"{statistics.median(x):.0f} ms" if x else "— (no lines)"
        print(f"    --  server lives in the log: {reg['vite']}  "
              f"(expected 2: one for the samples and the ban, one for persistence)")
        for r in reg["avvii"]:
            print(f"        {r}")
        print(f"    --  «the fixed second has passed»: n={len(reg['fissi'])}  "
              f"median {med(reg['fissi'])}  "
              f"(admitted {med(reg['ammessi'])} out of {len(reg['ammessi'])} · "
              f"refused {med(reg['respinti'])} out of {len(reg['respinti'])} · "
              f"without a readable verdict: {len(reg['senza_pam'])})")
        # ── ⛔ THE BLIND BENCH MUST SHOW — 12 Aug 2026 ───────────────────────
        #
        # ⛔ The recertification run counted **52 lines and 0 admitted** and
        #    the bench said nothing: it only stopped being able to name the
        #    defendant, and the outcome went from 5 to 1 on a healthy product.
        #    These lines are the check that was missing, and it is a check on the
        #    BENCH, not on the server (`REVIEWER.md` §1).
        cieco, righe_cieco = tutto_in_una_casella(
            "the classification of the PAM answers in the log", reg["pam"])
        for r in righe_cieco:
            print(f"    --  {r}")
        for r in reg["pam_esempi"]:
            print(f"        line I could not read: {r}")
        if cieco:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ THE JUDGE IS BLIND: as long as this "
                  f"line is red no median above counts, because it is not "
                  f"certain it is the median of what it declares to be")
            guasti += 1
        elif reg["pam"]["illeggibile"]:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ {reg['pam']['illeggibile']} lines "
                  f"«{R_PAM_RIGA}» could not be read: the anchor "
                  f"«{R_PAM.pattern}» no longer finds the verdict, and a verdict "
                  f"not read is NOT a refused one (E8)")
            guasti += 1
        if reg["senza_pam"]:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ {len(reg['senza_pam'])} samples of the "
                  f"fixed second have no PAM verdict before them: they "
                  f"enter neither of the two medians, and before 12 Aug "
                  f"2026 they would all have ended up among the REFUSED silently")
            guasti += 1
        print(f"    --  if that number is ~{RITARDO_FISSO:.0f} ms what governed "
              f"was the FIXED DELAY; if it is much higher what governed "
              f"was PAM, and a separation between the medians would be PAM's")
        print(f"    --  source addresses seen BY THE SERVER: {reg['indirizzi']}")
        print(f"    --  «BANNED» lines: {len(reg['ban'])} · «UNBLOCKED on "
              f"command»: {len(reg['sbloccati'])} · «was NOT banned»: "
              f"{len(reg['non_bannati'])} · pages served: {len(reg['pagine'])}")
        if len(reg["indirizzi"]) < 2:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the server saw ONE SINGLE address: "
                  f"the margin of the balance was not there, and the checks that "
                  f"separate the two addresses are not valid (B0.3)")
            guasti += 1
        if reg["vite"] < 2:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the log sees {reg['vite']} lives "
                  f"of the server: persistence is proved with a RESTART, and here "
                  f"there was none")
            guasti += 1
        elif reg["carichi"] and reg["carichi"][-1] == 1:
            print(f"    {VERDE}OK{GRIGIO}  ⭐ and the second start declares «bans "
                  f"loaded: 1»: the ban came back from disk, not from memory")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the second start declares bans "
                  f"loaded = {reg['carichi'][-1] if reg['carichi'] else 'nothing'}, "
                  f"expected 1")
            guasti += 1
        if reg["illeggibili"]:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ {reg['illeggibili']} starts could not "
                  f"read the ban file")
            guasti += 1
        # ⛔ And every unblock is written in the log (§4.4-bis): the bench
        #    compares it with the number of unblocks it ASKED for, or «it wrote it»
        #    stays a hope.
        chiesti = [r for r in sblocchi if r["esito"] is not None]
        scritti = len(reg["sbloccati"]) + len(reg["non_bannati"])
        if scritti >= len(chiesti) and chiesti:
            print(f"    {VERDE}OK{GRIGIO}  ⭐ every unblock ended up in the log: "
                  f"{len(chiesti)} asked for, {scritti} lines written "
                  f"({len(reg['sbloccati'])} «removed» + {len(reg['non_bannati'])} "
                  f"«was not banned»)")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ unblocks asked for {len(chiesti)}, "
                  f"lines in the log {scritti}: «every unblock is written in the "
                  f"log, or a removed ban and a ban that never triggered have the "
                  f"same look» (§4.4-bis)")
            guasti += 1

    # ── 7-bis. ⛔ THE TWO STOPWATCHES, and they must agree ───────────────────
    #
    # ⛔ Finding A19: the certification of this bench breaks the FACTS ALREADY
    #    RECORDED, so it certifies the JUDGE and not the ACQUISITION.  A `t0`
    #    moved to a point that keeps the numbers plausible would be seen by none
    #    of the faults built by hand.  ⭐ This line is the check the acquisition
    #    lacks: the SERVER times the same fact on its own, and the two numbers
    #    have a mandatory direction.
    #
    #    The client starts BEFORE sending `CREDENZIALI` and stops AFTER having
    #    read the answer; the server starts when `CREDENZIALI` arrives and stops
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
        if med_cli >= med_srv - MARGINE_CRONOMETRI:
            print(f"    {VERDE}OK{GRIGIO}  the client's stopwatch contains "
                  f"the server's, as it must: what the bench measures is "
                  f"the interval it declares to measure")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ THE TWO STOPWATCHES DO NOT AGREE: the "
                  f"client says {med_cli:.0f} ms where the server declares "
                  f"{med_srv:.0f}, and the client's interval CONTAINS that "
                  f"of the server — it cannot be shorter")
            print(f"        ⛔ The first suspicion is on the bench, not on the server "
                  f"(`LEZIONI.md` §1.9 point 3): `t0` of `un_tentativo()` "
                  f"times less than what its docstring declares, and "
                  f"all the medians above are of another interval")
            guasti += 1

    # ── 7-ter. ⛔ WHO GOVERNS THE TIMES, measured ────────────────────────────
    imputato, righe_imputato = None, []
    if guasti_mediane:
        print()
        print("    == ⛔ The medians separate: WHO separates them — and it is measured "
              "(A18)")
        imputato, righe_imputato = imputato_dei_tempi(serie, reg)
        for r in righe_imputato:
            print(f"    --  {r}")
        if imputato == "NOSTRO":
            # ⛔ And then it is NOT the `[?]` already declared by §4.4-bis: it is a
            #    defect of ours, and it goes into the counter of the real reds.
            #    Keeping it in the medians counter would mean granting to a delay
            #    we wrote ourselves the leniency written for PAM.
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the separation is NOT the one "
                  f"§4.4-bis has already declared `[?]`: it is a delay of ours, and "
                  f"it counts as a full red")
            guasti += 1
        elif imputato is None:
            print(f"    {GIALLO}??{GRIGIO}  ⚠ the defendant was not measured: "
                  f"the verdict will say THAT the medians separate and not BY WHOM, "
                  f"which is less than before and more true")

    # ── The outcome ─────────────────────────────────────────────────────────
    print()
    print(f"    == The outcome, and its denominator: {len(tentativi)} attempts, "
          f"{len(pagine)} pages, {len(sblocchi)} unblocks")
    if guasti:
        print(f"    {ROSSO}⛔ B8: {guasti} "
              f"{'point does not pass' if guasti == 1 else 'points do not pass'}{GRIGIO}")
        if guasti_mediane:
            print(f"    ⚠ and {guasti_mediane} pairs of medians separate, and "
                  f"the defendant is «{imputato or 'NOT MEASURED'}»:")
            for r in righe_imputato:
                print(f"       {r}")
            if imputato != "NOSTRO":
                print(f"    ⚠ look at the medians AFTER having cured the {guasti} "
                      f"points above")
        return 1
    if guasti_mediane:
        # ⛔ THE FIFTH OUTCOME, and it is born from a measurement, not from leniency —
        #    and since tonight the defendant is named by `imputato_dei_tempi()`,
        #    which READS it in the numbers, instead of a constant sentence (A18).
        print(f"    {ROSSO}⛔ B8: {guasti_mediane} pairs of medians DO SEPARATE "
              f"— «the three medians indistinguishable» of `FASI.md` §01-filo-nudo B8 "
              f"is not satisfied{GRIGIO}")
        print(f"    ⭐ but the pair that carries the SECRET — «inesistente − "
              f"sbagliata», the only one that would say whether a user name exists — does "
              f"NOT separate: what §4.4 forbids is not readable with the stopwatch")
        print(f"    ⭐ and the ban passes in full: it triggers at the third, refuses the "
              f"fourth with the right password, survives the restart, says it "
              f"in the page, and the unblock removes it")
        for r in righe_imputato:
            print(f"    ⚠ {r}")
        if imputato == "PAM":
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
    if sospeso:
        print(f"    {GIALLO}⚠ B8 SUSPENDED: the ban passes, but what I looked at "
              f"on the medians is not enough to call them «indistinguishable»{GRIGIO}")
        print(f"    ⚠ «I did not see a difference» and «there is no difference» "
              f"are two different things: run again with more blocks")
        return 3
    print(f"    {VERDE}⭐ B8 passes: every PAM answer ≥ {RITARDO_FISSO:.0f} ms, "
          f"the three medians do not separate beyond the noise, the ban triggers at the "
          f"third and refuses the fourth with the right password, survives the "
          f"restart, says it in the page, and the unblock removes it{GRIGIO}")
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
def _prima(dati, **cerca):
    for r in dati:
        if all(r.get(k) == v for k, v in cerca.items()):
            return r
    return None


def _guasti_possibili():
    """(name, function that breaks ONE thing, sentence the verdict MUST say)."""
    def quarto_ammesso(d, reg):
        r = [x for x in d if x.get("tipo") == "ban"]
        r[-1]["messaggio"], r[-1]["motivo"] = "AMMESSO", None
        return d, reg

    def nomi_uguali(d, reg):
        for x in d:
            if x.get("tipo") == "ban":
                x["nome"] = "sempre-lo-stesso"
        return d, reg

    def troppo_veloce(d, reg):
        r = _prima(d, tipo="campione", classe="atteso")
        r["ms"] = 900.0
        return d, reg

    def nomi_a_tempo(d, reg):
        # ⛔ The fault this bench exists to find: «user does not exist» answers
        #    systematically before «wrong password», and with the stopwatch one
        #    reads whether a user name exists.  ⚠ Two seconds are coarse on
        #    purpose: if the bench did not see even THIS, it would see nothing.
        for x in d:
            if x.get("tipo") == "campione" and x.get("caso") == "inesistente" \
                    and x.get("ms"):
                x["ms"] += 2000.0
        return d, reg

    def pagina_bugiarda(d, reg):
        r = _prima(d, tipo="pagina", etichetta="bannato-prima")
        r["bannato"] = False
        return d, reg

    def pagina_muta(d, reg):
        r = _prima(d, tipo="pagina", etichetta="bannato-prima")
        r["frase"] = False
        return d, reg

    def chiusura_storta(d, reg):
        r = [x for x in d if x.get("tipo") == "ban"]
        r[-1]["chiusura"] = CREDENZIALI_ERRATE
        return d, reg

    def altro_fuori(d, reg):
        r = _prima(d, tipo="controllo", etichetta="altro-indirizzo")
        r["messaggio"], r["motivo"] = "RESPINTO", TROPPI_TENTATIVI
        return d, reg

    def niente_azzeramento(d, reg):
        r = [x for x in d if x.get("etichetta") == "azzeramento"]
        r[-1]["motivo"], r[-1]["messaggio"] = TROPPI_TENTATIVI, "RESPINTO"
        return d, reg

    def sblocco_cieco(d, reg):
        r = _prima(d, tipo="sblocco", etichetta="prova-tolto")
        r["esito"] = "NON-BANNATO"
        return d, reg

    def niente_persistenza(d, reg):
        return [x for x in d
                if x.get("etichetta") != "bannato-dopo-riavvio"], reg

    def registro_smemorato(d, reg):
        return d, [r.replace("bans loaded: 1", "bans loaded: 0")
                    .replace("ban caricati: 1", "ban caricati: 0") for r in reg]

    def imputato_nostro(d, reg):
        # ⛔ The fault that certifies the cure of A18: the delay is put on the
        #    path of the AMMESSO — where `pam_faildelay` has no say — and the
        #    server log keeps saying that the fixed second covered everything.
        #    The verdict MUST stop accusing PAM.
        for x in d:
            if x.get("tipo") == "campione" and x.get("caso") == "giusta" \
                    and x.get("ms"):
                x["ms"] += 2000.0
        fuori = []
        for r in reg:
            if "the fixed second has passed" in r:
                fuori.append("the fixed second has passed (1005 ms)\n")
            else:
                fuori.append(r)
        return d, fuori

    def cronometro_scollato(d, reg):
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

    def pam_illeggibile(d, reg):
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

    def pam_tutti_respinti(d, reg):
        # ⛔ The same blindness without the «unreadable» box: the classifier
        #    reads perfectly well, and puts **everything** on the same side.  It is
        #    the exact snapshot of 12 August — «52 lines, 0 admitted» — and the
        #    bench must shout in this form too, or the alarm would be looking at
        #    the anchor instead of the counter.
        return d, [re.sub(r"(PAM answered\b[^:]*:\s*)admitted",
                          r"\1refused", r) for r in reg]

    def nessun_tentativo(d, reg):
        # ⛔ The file is NOT empty: the pages and the unblocks stay, and every
        #    attempt disappears.  It is the most insidious form of green — «all
        #    those tested went well» is true even when the tested are zero
        #    (`LEZIONI.md` §1.9 rule 6) — and an empty file would prove it more
        #    weakly, because anyone notices an empty file.
        return [x for x in d
                if x.get("tipo") not in ("campione", "ban", "controllo")], reg

    return [
        ("the fourth attempt, with the RIGHT password, is AMMESSO",
         quarto_ammesso, "the fourth attempt — RIGHT password —"),
        ("the three names of the ban run are THE SAME",
         nomi_uguali, "the three names are not different"),
        ("a PAM answer arrives at 900 ms",
         troppo_veloce, "responses below the second"),
        ("⛔ «user does not exist» answers 2 s before «wrong password»",
         nomi_a_tempo, "THE SEPARATION §4.4 FORBIDS"),
        ("the page of a banned address says «you are not banned»",
         pagina_bugiarda, "bannato=False (expected True)"),
        ("the banned page does not contain «attempts exhausted»",
         pagina_muta, "expected True) · frase=False"),
        ("the session closes with a code other than TROPPI_TENTATIVI",
         chiusura_storta, "the session closing code"),
        ("the other address does NOT get in",
         altro_fuori, "the other address does NOT get in"),
        ("the success does not reset the count",
         niente_azzeramento, "the reset did not happen"),
        ("the unblock answers «it was not banned» on a real ban",
         sblocco_cieco, "NON-BANNATO (expected TOLTO)"),
        ("persistence was not proved (the page after the restart is missing)",
         niente_persistenza, "persistence was not proved"),
        ("the second start declares «bans loaded: 0»",
         registro_smemorato, "the second start declares bans loaded"),
        ("⛔ ZERO attempts: «all those tested went well» on zero tested",
         nessun_tentativo, "ZERO attempts"),
        ("⛔ the delay is OURS, on the path of the AMMESSO, and PAM answers in "
         "5 ms (A18: the verdict must stop accusing PAM)",
         imputato_nostro, "THE DEFENDANT IS NOT PAM"),
        ("⛔ the CLIENT's stopwatch measures less than the SERVER's "
         "(A19: `t0` moved to a point that keeps the numbers plausible)",
         cronometro_scollato, "THE TWO STOPWATCHES DO NOT AGREE"),
        ("⛔ the PAM line changes shape and the verdict can no longer be read "
         "(12 Aug 2026: the bench gone blind without saying so)",
         pam_illeggibile, "EVERYTHING IN ONE SINGLE BOX"),
        ("⛔ every PAM answer ends up among the REFUSED — «52 lines, 0 "
         "admitted» — and the classifier reads perfectly well",
         pam_tutti_respinti, "EVERYTHING IN ONE SINGLE BOX"),
    ]


def certifica(a):
    import copy as _copy
    import io
    import contextlib

    if not os.path.exists(a.uscita):
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ there is no run to break: "
              f"{a.uscita} does not exist.  The certification is done **on the facts of "
              f"a real run**, or it breaks a file nobody produced")
        return 2
    with open(a.uscita) as f:
        sani = [json.loads(r) for r in f if r.strip()]
    reg_sano = []
    if a.registro and os.path.exists(a.registro):
        with open(a.registro, errors="replace") as f:
            reg_sano = f.readlines()

    tmp_u = a.uscita + ".guasto"
    tmp_r = (a.registro or "/tmp/b8-reg") + ".guasto"

    def gira(dati, reg):
        with open(tmp_u, "w") as f:
            for r in dati:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        with open(tmp_r, "w") as f:
            f.writelines(reg)
        b = argparse.Namespace(**vars(a))
        b.uscita, b.registro = tmp_u, tmp_r
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            esito = verdetto(b)
        return esito, buf.getvalue()

    print()
    print("    == ⛔ THE CERTIFICATION: the fault is built and the red is demanded")
    # ⛔ AND IT IS DECLARED WHAT THIS CERTIFICATION DOES **NOT** CERTIFY — A19.
    #    Whoever reads a verdict reads the verdict, not the comments of the file:
    #    without these three lines, «certified» reads as «B8 is certified», and
    #    what is certified is half of B8.
    print("    --  ⛔ WHAT THIS LINE CERTIFIES: the JUDGE.  The faults are "
          "built on the FACTS ALREADY RECORDED, so they prove that "
          "`verdetto()` can see a crooked fact, not that the facts were "
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
    esito_sano, testo_sano = gira(sani, reg_sano)
    print(f"    --  the HEALTHY run, as it is: outcome {esito_sano} "
          f"({'green' if esito_sano == 0 else 'suspended' if esito_sano == 3 else 'red'})")
    print(f"    --  facts being broken: {len(sani)} · log lines: "
          f"{len(reg_sano)}")

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
    falliti_ancora = 0
    def _allunga_pam(r):
        # the cure of `DECISIONI.md` §1.10, as it really arrived
        if R_PAM_RIGA in r:
            return r.rstrip("\n") + ("  ⚠ (SYNCHRONOUSLY: no asynchronous "
                                     "hook connected — the thread "
                                     "stood still)\n")
        return r

    def _pratica_pam(r):
        # the SECOND form of the line, which the product already writes (rcp.c:2636)
        if R_PAM_RIGA in r:
            return r.replace("PAM answered:",
                             "PAM answered (request 7):", 1)
        return r

    def _allunga_da(r):
        # the address stops being the last thing on the line
        if " da=" in r and ("respinto motivo" in r or "admitted utente" in r):
            return r.rstrip("\n") + " · request=7 · via=async\n"
        return r

    ancore = [
        ("an explanation appended at the tail of «PAM answered: …» "
         "(the cure of §1.10, the real one)", _allunga_pam),
        ("one more field BEFORE the colon: «PAM answered (request 7): "
         "admitted» (rcp.c:2636, the asynchronous road)", _pratica_pam),
        ("the address is no longer the last thing on the line «respinto "
         "motivo=… da=…»", _allunga_da),
    ]
    print()
    print("    == ⭐ THE POSITIVE CONTROL OF THE ANCHOR: the log gets longer, "
          "and the verdict must NOT change")
    for nome, cambia in ancore:
        esito_a, testo_a = gira(sani, [cambia(r) for r in reg_sano])
        cieco = "EVERYTHING IN ONE SINGLE BOX" in testo_a
        buono = esito_a == esito_sano and not cieco
        segno = f"{VERDE}OK{GRIGIO}" if buono else f"{ROSSO}NO{GRIGIO}"
        perche = ""
        if cieco:
            perche = ("  ⛔ and the judge went blind: the anchor went back "
                      "to depending on what comes AFTER")
        elif not buono:
            perche = (f"  ⛔ the outcome changed from {esito_sano} to {esito_a}: "
                      f"the log reader depends on what is "
                      f"appended to its tail")
        print(f"    {segno}  {nome}{perche}")
        if not buono:
            falliti_ancora += 1
    print(f"    --  ⚠ and this check does not prove the bench is right: "
          f"it proves that it **withstands an addition**.  The red is proved by the faults "
          f"below")

    prove = _guasti_possibili()
    print(f"    --  faults built by hand: {len(prove)}  ⛔ and this is the "
          f"denominator: a list of OKs without it is not a measurement")
    falliti = 0
    for nome, rompi, frase in prove:
        dati, reg = rompi(_copy.deepcopy(sani), list(reg_sano))
        esito, testo = gira(dati, reg)
        vede = frase in testo
        # ⛔ and the second half of the criterion: the healthy verdict must NOT
        #    already say it, or this line does not prove the fault was seen.
        gia = frase in testo_sano
        # ⛔ And the outcome must be a REAL RED (1) or «nothing to judge» (2),
        #    not the 5 of the medians: if «different from zero» were enough, a run
        #    in which PAM dominates would satisfy this line **without the fault
        #    having been seen**, and the certification would say «I see
        #    everything» looking at an outcome that was already there.
        buono = vede and esito in (1, 2) and not gia
        segno = f"{VERDE}OK{GRIGIO}" if buono else f"{ROSSO}NO{GRIGIO}"
        perche = ""
        if gia:
            perche = "  ⛔ but the HEALTHY run already said it: it proves nothing"
        elif not vede:
            perche = f"  ⛔ the verdict did NOT say «{frase}» (outcome {esito})"
        elif esito not in (1, 2):
            perche = f"  ⛔ it says it, but the outcome is {esito} and not a real red"
        print(f"    {segno}  {nome}{perche}")
        if not buono:
            falliti += 1

    for p in (tmp_u, tmp_r):
        try:
            os.remove(p)
        except OSError:
            pass

    print()
    if falliti_ancora:
        print(f"    {ROSSO}⛔ THE CERTIFICATION DOES NOT PASS: {falliti_ancora} "
              f"lengthenings of the log out of {len(ancore)} change the verdict."
              f"{GRIGIO}")
        print(f"    ⚠ It is the defect of 12 Aug 2026, alive: the bench reads a "
              f"line of the server anchoring itself to what today sits at its end, and "
              f"the next addition blinds it again")
        return 1
    if falliti:
        print(f"    {ROSSO}⛔ THE CERTIFICATION DOES NOT PASS: {falliti} faults out of "
              f"{len(prove)} do not make the bench turn red.{GRIGIO}")
        print(f"    ⚠ As long as this line is red, a green of B8 means "
              f"nothing: a bench that does not reproduce is not a proof of "
              f"correctness (`LEZIONI.md` §1.3)")
        return 1
    print(f"    {VERDE}⭐ THE JUDGE of B8 is certified: all {len(prove)} "
          f"faults built by hand make it turn red, each at its own "
          f"point — and the {len(ancore)} lengthenings of the log do NOT change it"
          f"{GRIGIO}")
    print(f"    ⚠ and it is NOT «B8 is certified»: the acquisition of the times stays "
          f"covered by a single fault (the two stopwatches).  The three lines at "
          f"the top say what was left out")
    return 0


def previsione(a):
    print("== B8 — what is measured, and what I expect BEFORE measuring")
    print()
    print("  PART 1 — the fixed second and the three medians")
    print("    inesistente  a user that does NOT exist (verified with getpwnam)")
    print("    sbagliata    the real user, wrong password")
    print("    giusta       the real user, right password  → AMMESSO")
    print("    ⚠ the pair «inesistente − sbagliata» is the one that, if it separates,")
    print("      gives away the user names to whoever times it.")
    print()
    print("  PART 2 — the ban (RCP.md §4.4-bis, DECISIONI.md §1.9)")
    print(f"    {SOGLIA} failed authentications from the same address within")
    print(f"    {FINESTRA_MIN} minutes ⇒ that address is out for {BAN_ORE} hours.")
    print()
    print("  The expected, written here before the numbers:")
    print(f"    1. every PAM answer to CREDENZIALI ≥ {RITARDO_FISSO:.0f} ms;")
    print("    2. the three medians indistinguishable according to the interval rule;")
    print("    3. the first three failed — WITH THREE DIFFERENT NAMES — receive")
    print("       CREDENZIALI_ERRATE, and the third makes the ban trigger;")
    print("    4. ⛔ the FOURTH attempt has the RIGHT password and receives")
    print("       TROPPI_TENTATIVI, inside a RESPINTO and not inside a CONGEDO,")
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
    print(f"  The numbers of the rule: threshold {SOGLIA} failures per address,")
    print(f"  balance {BILANCIO} per block, wanted resolution "
          f"±{RISOLUZIONE_VOLUTA:.0f} ms, minimum {MINIMO_CAMPIONI} samples per")
    print(f"  case, bootstrap {RIPETIZIONI} repetitions, seed {SEME}.")
    return 0


# ===========================================================================
# The phases
# ===========================================================================
async def fase_campioni(a):
    inesistente = f"nessuno-b8-{a.blocco}"
    if not await controlla_utenti(a, inesistente):
        return 2
    if not await prova_indirizzi(a.indirizzi, a.porta):
        return 2
    passi = piano_campioni(a.blocco, a.per_caso, a.indirizzi, a.utente, inesistente)
    return await esegui(a, passi, "campione", f"blocco {a.blocco}", "sotto-soglia")


async def fase_ban_prima(a):
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
    inesistente = "nessuno-b8-ban"
    if not await controlla_utenti(a, inesistente, *[n for n in NOMI_DEL_BAN
                                                    if n != "<utente>"]):
        return 2

    print()
    print("    == ⭐ Check that says NO no.2: 2 failed · 1 succeeded · 2 failed")
    passi = piano_azzeramento(a.indirizzi, a.utente, inesistente)
    e = await esegui(a, passi, "controllo", "azzeramento", "non-banna")
    if e:
        return e
    guarda_pagina(a, a.indirizzi[1], "azzeramento-dopo", False)

    print()
    print("    == ⛔ The ban run — three different names, then the RIGHT password")
    nomi = tuple(a.utente if n == "<utente>" else n for n in NOMI_DEL_BAN)
    passi = piano_ban(a.indirizzi, a.utente, nomi)
    e = await esegui(a, passi, "ban", "ban", "banna-al-4")
    if e:
        return e

    print()
    print("    == ⭐ Check that says NO no.1: ANOTHER address gets in right away")
    passi = [{"caso": "giusta", "indirizzo": a.indirizzi[1], "nome": a.utente,
              "scaldata": False}]
    e = await esegui(a, passi, "controllo", "altro-indirizzo", "sotto-soglia")
    if e:
        return e

    print()
    print("    == ⛔ What the user sees, now")
    guarda_pagina(a, a.indirizzi[0], "bannato-prima", True)
    guarda_pagina(a, a.indirizzi[1], "non-bannato-prima", False)
    return 0


async def fase_ban_dopo(a):
    """⭐ After the restart: persistence, and then the unblock — which is tested at the end."""
    print()
    print("    == ⭐ Check that says NO no.3: the ban survives the RESTART")
    guarda_pagina(a, a.indirizzi[0], "bannato-dopo-riavvio", True)
    guarda_pagina(a, a.indirizzi[1], "non-bannato-dopo-riavvio", False)
    passi = [{"caso": "giusta", "indirizzo": a.indirizzi[0], "nome": a.utente,
              "scaldata": False}]
    # ⚠ The model would say AMMESSO — it does not know the ban came back from disk —
    #   and demanding it here would give red on the right code.  The comparison is
    #   done by the verdict, which knows we are after a restart.
    e = await esegui(a, passi, "controllo", "dopo-riavvio", "sotto-soglia",
                     confronta_modello=False)
    if e:
        return e

    print()
    print("    == ⛔ AND NOW the unblock, which so far has touched nothing")
    sblocca_e_dichiara(a, [a.indirizzi[0]], "prova-tolto", pretendi="TOLTO")
    guarda_pagina(a, a.indirizzi[0], "dopo-sblocco", False)
    sblocca_e_dichiara(a, [a.indirizzi[0]], "prova-non-bannato",
                       pretendi="NON-BANNATO")
    passi = [{"caso": "giusta", "indirizzo": a.indirizzi[0], "nome": a.utente,
              "scaldata": False}]
    return await esegui(a, passi, "controllo", "dopo-sblocco", "sotto-soglia")


async def controlla_utenti(a, *inesistenti):
    """⛔ The initial state is declared and VERIFIED (B0.1)."""
    ok = True
    for nome, deve, che in [(a.utente, True, "the real user")] + \
            [(n, False, "a nonexistent name") for n in inesistenti]:
        buono, c_e = esistenza(nome, deve)
        stato = "exists" if c_e else "does not exist"
        if buono:
            print(f"    {VERDE}OK{GRIGIO}  {che} «{nome}»: {stato}, as it must")
        else:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ {che} «{nome}»: {stato} — the "
                  f"opposite of what this bench assumes")
            ok = False
    return ok


def principale():
    p = argparse.ArgumentParser(
        description="B8 — the fixed second, the three medians and the ban of the address")
    # ⛔ No default that names a target: 7447 is the graft and 7448 the
    #    product, and a default here would mean that «--bersaglio prodotto»
    #    without «--porta» measures the graft while declaring the product.
    p.add_argument("--porta", type=int, required=True)
    p.add_argument("--indirizzi", default="127.0.0.1,192.168.0.2",
                   help="⛔ two: they double the margin of the balance and "
                        "show in the server log")
    p.add_argument("--utente", default="prova")
    # ⛔ `parola-di-prova`, and the story of this line is worth the comment.
    #
    #    Until 11 Aug 2026 here it said `prova`, and ⛔ **no authentication of
    #    this bench ever succeeded**: `01-b3-lancia.sh`, `01-b6-lancia.sh` and
    #    `01-b7-lancia.sh` all three use `PAROLA=parola-di-prova`.  The «giusta»
    #    case received `CREDENZIALI_ERRATE` like the other two, that is ⛔ **the
    #    three cases were two**, and the third median was a copy of the second.
    #
    # ⚠ And the defect had no symptom of its own: the bench said «unexpected
    #   answers», which reads as a server fault.  ⭐ From today there is the
    #   positive control in `--stato-iniziale` — *«can this tool produce an
    #   AMMESSO?»* — which is `LEZIONI.md` §1.9 rule 2 applied to the bench
    #   instead of to the measurement, and it costs one attempt.
    p.add_argument("--parola", default="parola-di-prova")
    # ⛔ D12: the road that does NOT go through `ps`.  It wins over `--parola` if
    #    both are there — a file written on purpose is always more recent than a
    #    default.
    p.add_argument("--parola-file", default="",
                   help="0600 file with only the password (⭐ D12: this way "
                        "it does not end up in `ps`)")
    p.add_argument("--sbagliata", default="questa-non-e-la-parola-di-nessuno")
    p.add_argument("--comando", default="/srv/src/b8-comando.sock",
                   help="the socket of the unblock command of §4.4-bis")
    p.add_argument("--blocco", type=int, default=0)
    p.add_argument("--per-caso", type=int, default=2,
                   help="triplets per block.  ⛔ 2 keeps the failures at two per "
                        "address, that is ONE below the threshold")
    p.add_argument("--campioni", action="store_true")
    p.add_argument("--ban", choices=("prima", "dopo"))
    p.add_argument("--sblocca", default="",
                   help="unblock these addresses (comma-separated) and declare it")
    p.add_argument("--perche", default="fra-i-blocchi")
    p.add_argument("--stato-iniziale", action="store_true")
    p.add_argument("--verdetto", action="store_true")
    p.add_argument("--certifica", action="store_true",
                   help="⛔ builds one fault at a time in the facts of a real "
                        "run and demands that the bench turn red at THAT point")
    p.add_argument("--previsione", action="store_true")
    # ⛔ `--giro` likewise: the shared profile declares it (see the note below).
    # ⛔ `--uscita` is NOT declared here: the shared target profile declares it,
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
    p.add_argument("--registro", default="")
    # ⛔ The same four arguments as B5, B6 and B7 — mandatory target without a
    #    default, output, run, md5 of the binary.
    b0.aggiungi_argomenti(p)
    a = p.parse_args()
    a.parola = parola_dagli_argomenti(a)
    a.indirizzi = [x for x in a.indirizzi.split(",") if x]
    a.prof = b0.profilo(a.bersaglio)
    # ⛔ And from here on EVERY log line carries the target, the port and the md5
    #    fingerprint of the measured binary.
    BERSAGLIO.update({"bersaglio": a.bersaglio, "porta": a.porta,
                      "md5": a.md5 or "ignota"})
    R_BAN.update({"caricati": a.prof["r_ban_caricati"],
                  "illeggibile": a.prof["r_ban_illeggibile"],
                  "pagina": a.prof["r_pagina"]})

    if a.previsione:
        return previsione(a)
    if a.certifica:
        return certifica(a)
    if a.verdetto:
        return verdetto(a)
    if len(a.indirizzi) < 2:
        print(f"    {ROSSO}NO{GRIGIO}  ⛔ TWO source addresses are needed")
        return 2

    # ⛔ AND THE OPENING LINE OF THE RUN — which says against what one measures, and
    #    what this target does differently.
    scrivi(a.uscita, {"giro": a.giro, "tipo": "giro", "banco": "B8",
                      "eseguibile": a.prof["eseguibile"],
                      "indirizzi": a.indirizzi,
                      # ⛔ The difference that changes the MEANING of a red:
                      #    if the ban file is there and cannot be read, the product
                      #    REFUSES to start (src/main.c: «it is not "zero bans",
                      #    it is the protection of §4.4-bis switched off.  One does
                      #    not start.»), while the graft starts and writes it.  ⚠ On
                      #    this target that case is not observed as a log line:
                      #    it is observed as «the server did not start».
                      "ban_illeggibile_parte": a.prof["ban_illeggibile_parte"],
                      "righe_cercate": dict(R_BAN)})

    if a.stato_iniziale:
        # ⛔ B0.1: it is declared AND verified from which state one starts.  Here
        #    the state that counts is threefold: the unblock command exists, the
        #    two addresses are not banned, and the page can say no.
        vivo, che = cmd.ping(a.comando)
        if not vivo:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the unblock command does not answer: "
                  f"{che}")
            print(f"        without it, this bench can neither start from a "
                  f"known state nor put the machine back in order — and every "
                  f"following bench would stay out for {BAN_ORE} hours (B0.3)")
            return 2
        print(f"    {VERDE}OK{GRIGIO}  the unblock command answers ({che})")
        sblocca_e_dichiara(a, a.indirizzi, "stato-iniziale")
        tutte = True
        for ind in a.indirizzi:
            r = guarda_pagina(a, ind, "stato-iniziale", False)
            if r["errore"] or r["bannato"] is not False:
                tutte = False
        if not tutte:
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the initial state is not the "
                  f"declared one: someone is already banned, or the page does not "
                  f"answer")
            return 2
        print(f"    {VERDE}OK{GRIGIO}  ⭐ and the page CAN SAY NO: without this "
              f"line, «attempts exhausted» later would be compatible with "
              f"a page that always says it")

        # ⛔ THE POSITIVE CONTROL ON THE TOOL — `LEZIONI.md` §1.9 rule 2:
        #    *«every measurement wants a positive control, on the same tool —
        #    can this tool find something that is surely there?»*
        #
        #    Here the question is: **can this bench produce an AMMESSO?**  If it
        #    cannot — wrong password, user without password, PAM that does not
        #    talk to it — the «giusta» case receives `CREDENZIALI_ERRATE` like
        #    the other two, ⛔ **the three cases become two**, and the pair
        #    «sbagliata − giusta» would be indistinguishable **by construction**:
        #    the emptiest green this bench can print.
        #
        # ⚠ And it costs an attempt that consumes nothing: a SUCCESSFUL
        #   authentication resets the count of that address (§4.4-bis), so it
        #   leaves the machine cleaner than it found it.
        r = asyncio.run(un_tentativo(a.indirizzi[0], a.porta, a.utente, a.parola))
        rec = dict(r)
        rec.update({"giro": a.giro, "tipo": "controllo",
                    "etichetta": "so-fare-un-ammesso", "blocco": 0, "ordine": 1,
                    "caso": "giusta", "scaldata": True,
                    "classe": classifica(r, "giusta"),
                    "atteso_modello": "AMMESSO", "atteso_motivo": None})
        scrivi(a.uscita, rec)
        if rec["messaggio"] != "AMMESSO":
            print(f"    {ROSSO}NO{GRIGIO}  ⛔ the positive control does NOT pass: with "
                  f"the user «{a.utente}» and the password this bench believes "
                  f"right the server answers "
                  f"{rec['messaggio'] or rec['errore']} "
                  f"{MOTIVI.get(rec['motivo'], '')}")
            print(f"        ⛔ without an AMMESSO the three cases are TWO, and «the three "
                  f"medians do not separate» would be true by construction.  "
                  f"Look at the password (the other benches use "
                  f"«parola-di-prova»), not at the server")
            return 2
        print(f"    {VERDE}OK{GRIGIO}  ⭐ and this bench CAN produce an AMMESSO "
              f"({rec['ms']:.0f} ms): the three cases really are three")
        return 0

    if a.sblocca:
        sblocca_e_dichiara(a, [x for x in a.sblocca.split(",") if x], a.perche)
        return 0

    if a.campioni:
        return asyncio.run(fase_campioni(a))
    if a.ban == "prima":
        return asyncio.run(fase_ban_prima(a))
    if a.ban == "dopo":
        return asyncio.run(fase_ban_dopo(a))
    print(f"    {ROSSO}NO{GRIGIO}  ⛔ you did not tell me what to do")
    return 2


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
    sys.exit(principale())
