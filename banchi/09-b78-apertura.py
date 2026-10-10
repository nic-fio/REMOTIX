#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b78-apertura — HOW LONG A SESSION TAKES TO OPEN, WHEN THE NETWORK LOSES.

⛔⭐ WHY IT EXISTS.  `banchi/07-b64-rete.py`, profile `7-perdita-10`, carries a
    `[M]` written as an **outcome**, not as a fault:

        «10 %: `[M]` the session does not open at all in 25 s»

    That line was never explained, and `DECISIONI.md` §3.1 point 4
    reopens it: *«a QUIC handshake has the PTO precisely to resend what
    gets lost, and twenty-five seconds do not look like loss, they look like
    something that does not retry»*.

⭐ AND A YES/NO CANNOT ANSWER.  `07-b64` at that step looks at a single
   number — `ricevuti == 0` — and from it one cannot tell «it did not open»
   from «it opened and the audio did not arrive» from «the client gave up».
   ⇒ Here the **opening time** is measured, in steps, and split by **phases**:
   a curve tells what kind of phenomenon it is; a yes/no does not.

═══════════════════════════════════════════════════════════════════════════
THE PREDICTIONS — WRITTEN BEFORE RUNNING (`LEZIONI.md` §1.11)
═══════════════════════════════════════════════════════════════════════════

The facts read in the code, before any measurement:

  `[R]` `banchi/01-b3-cliente.py:1222`  `wait_connected()` has **8 s**, not 25.
  `[R]` `banchi/01-b3-cliente.py:1224`  `cli.accettata` has **8 s**.
  `[R]` `banchi/01-b3-cliente.py:1250`  `ECCOMI` has 10 s (default of
        `attendi`), `:1266` `AMMESSO` 20 s, `:1284` `SESSIONE` 10 s.
  `[R]` `banchi/07-b64-rete.py`  `--secondi` (default 25) is `--resta`, that is
        **how long the session stays open AFTER having opened**; the ssh
        ceiling is `secondi + 180`.  ⇒ ⛔ **«in 25 s» was never the
        time granted to the handshake.**
  `[R]` `src/trasporto.c:544`  `ngtcp2_settings_default()` and no line
        of ours touches `handshake_timeout` ⇒ it stays `UINT64_MAX`, that is
        **no ceiling on the handshake on the server side**;
        `initial_rtt` = 333 ms (`NGTCP2_DEFAULT_INITIAL_RTT`).
  `[R]` `src/trasporto.c:590`  `max_idle_timeout` = 30 000 ms.
  `[R]` `src/main.c:1379,1429`  the loop rearms on `trasporto_attesa_ms()`
        (ceiling 1000 ms) and calls `trasporto_scaduti()` →
        `ngtcp2_conn_handle_expiry()`.  ⇒ the server **has** a clock to
        retry, and is not awake only when packets arrive.
  `[R]` `src/trasporto.c:434`  **no GSO**: one packet per `sendto`.  ⇒
        `netem` drops single QUIC packets, not bunches.
  `[R]` `src/rcp.c:925-927`  `SOGLIA 3`, `FINESTRA` 5 min, `BAN_DURATA` 12 h —
        and the count moves **only** on a PAM verdict for `CREDENZIALI`.
        A handshake that does not finish never gets there.
  `[R]` `banchi/07-b64-rete.py` `guasta()`  puts **two** `u32` filters, `sport`
        and `dport`: on `lo` every packet crosses the qdisc **once
        only**, but the outbound one crosses it with `dport` and the return with `sport`
        ⇒ **the loss is paid in both directions**: per round trip `1-(1-p)²`, that is
        **19 %** when `p` = 10 %.

Hence the five predictions, one per hypothesis, and falsifiable:

  (a) **it is the client giving up.**  ⇒ With a wide ceiling (60 s per phase)
      the session opens at 10 % loss, and the **median** opening
      time is **below 3 s**; and at least one run in twenty exceeds the 8 s
      of `01-b3-cliente.py:1222` — that is, the ceiling is the defect.
  (b) **it is the ban of §4.4-bis.**  ⇒ In the server log
      «BANNATO» / `TROPPI_TENTATIVI` appears, and the **clean** step run
      RIGHT AFTER a bad step fails too.
  (c) **it is ngtcp2 not retrying.**  ⇒ The opening time at 10 % is
      **flat and very long** (tens of seconds, every run), and the `tcpdump`
      trace shows the client insisting while **nothing comes out any more**
      from the server.
  (d) **it is `netem` applying twice.**  ⇒ `tc -s qdisc` counts
      `dropped/Sent` ≈ `p` (not `2p`) on the single qdisc, but the packets
      **counted are those of both directions**; and removing the `sport` filter
      (outbound only) the opening time drops clearly.
  (e) **it really is the loss.**  ⇒ The opening time grows **smoothly** with the
      steps, and the jumps sit on the PTO scale: before the first RTT
      sample the PTO is `2 × 333 ms` and doubles (0.67 · 1.33 · 2.67 · 5.33 s);
      after the first sample, on `lo`, the RTT is ~0.1 ms and the PTO collapses to
      a few tens of ms.  ⇒ to reach **25 s** four initial flights
      lost in a row would be needed, which at 10 % is worth `1e-4`.

⛔ And the bench's predicate is written here, FIRST: **at 10 % loss, over
   ten runs, at least nine must open the session, and the median opening
   time must stay below 5 s.**  If it passes, the `[M]` of `07-b64` was
   a bench defect.  If it does not pass, the `[M]` stands and the curve will say
   why.

═══════════════════════════════════════════════════════════════════════════
WHAT CAME OUT — `[M]` 23 August 2026, port 7932, Intel UHD 730
═══════════════════════════════════════════════════════════════════════════

⭐⭐ **THE `[M]` OF `07-b64` IS FALSE AS WRITTEN: at 10 % loss the
    session DOES OPEN, and it takes little more than a second.**

1. The opening time up to `AMMESSO` (QUIC handshake + extended CONNECT
   + `CIAO/ECCOMI` + `CREDENZIALI/AMMESSO`), 10 runs per step, the
   loss **read** from `tc -s qdisc`, not deduced:

   | loss requested | true loss | opened | QUIC median | total median | total max |
   |---|---|---|---|---|---|
   |  0 %  |  —      | 10/10 |   7.8 ms |  1014 ms | 1116 ms |
   |  5 %  |  8.2 %  | 10/10 |   7.8 ms |  1078 ms | 1318 ms |
   | 10 %  |  9.5 %  | 10/10 |  10.9 ms |  1103 ms | 1219 ms |
   | 15 %  | 15.2 %  | 10/10 | 111.5 ms |  1281 ms | 1708 ms |
   | 25 %  | 24.3 %  | 10/10 | 211.9 ms |  1299 ms | 1738 ms |

   ⚠ The second seen in «total» **is not the network**: it is the fixed
     delay of §4.4-bis.  ⇒ The network costs, from 0 to 25 %, **285 ms**.
   ⭐ And the handshake maxima sit at 212 and 613 ms, that is **one and
      two PTOs** of aioquic (0.2 s and 0.2+0.4 s): ⇒ **it retries, and one sees the
      pace at which it retries.**  Hypothesis (c) is refuted by these numbers.
   ⛔ **Zero runs out of seventy** exceeded the 8 s of
      `01-b3-cliente.py:1222`: hypothesis (a) does not hold either.
   ⛔ The ban never fired (ban-file empty, no «BANNATO» in the
      log): hypothesis (b) is refuted.
   ⛔ `tc -s qdisc` says the qdisc is ONE and is crossed **one
      packet at a time**: hypothesis (d) («applied twice») is refuted.
      ⚠ It remains true that the two filters take both DIRECTIONS, so a network
        round trip pays `1-(1-p)²`; but a datagram, which goes one way only, pays `p`.

2. The exact form of `07-b64` — the real client, PCM, with the tone on,
   `--resta 20` — at **10 %**:

       SESSIONE open: True
       [audio] received **3235** · 3 105 600 bytes · codec 2
       SERVER: sent 3607 · dropped 0 · **refused 391** · deferred 293 718
       judgement: resa_campioni **0.810** · purity 0.182 · scoppiettii 19.1/s

   ⇒ 3235/3607 = **89.7 % arrived on the wire**, which is exactly the 10 %
     removed once.  ⚠ And `resa_campioni` drops to 0.810 because it also
     includes the **391 blocks the server NEVER sent** (congestion
     window closed): «lost on the wire» and «never sent» are two facts, and
     the yield adds them up.

3. ⛔⛔ **WHY THE BENCH SAID THE OPPOSITE.**  The predicate of that step
   is `a_non_si_apre(n) = (n["ricevuti"] == 0)`, and `01-b3-cliente.py` prints
   `[audio] ricevuti 0` **even from the `except` branch** (`:1286`), before
   re-raising.  ⇒ **Any** way of failing — a `CONGEDO`, an expired
   ceiling, a `NameError` in the bench — produces «ricevuti 0» and passes that
   step as GREEN.  It is a predicate that cannot give red, that is the form
   of `LEZIONI.md` §1.9: it did not measure «it does not open», it measured «I did not
   receive», and the two look the same.
   `[M]` checked by running the real client **without a tone**: `SESSIONE=True` at
   every run, `[audio] ricevuti 0` at every run, at 1 % as at 10 %.

4. ⭐⭐ **AND BEHIND IT THERE IS A FACT OF THE PRODUCT, and it is on the phase's target.**
   The only way in which, under loss, an opening really fails is:
   `ATTACCA` → `CONGEDO(0x0F) GIA_ATTIVA_REMOTA`, that is **the slot of the
   previous session is still taken**.  `[M]` in the first scale run:
   5/10 at 10 %, 0/10 at 15 %, with the log saying
   *«slot DENIED to provanr3 … it is held by another client of this same
   user (taken: 1)»*.

   ⛔ And the count closes **without any `netem`**, because a **lost**
      goodbye and a goodbye **never said** are the same fact for the server:
      the client is killed with `-9` and we measure from when the slot is free
      again.  `[M]` 23 August 2026:

          + 1.6 s  CONGEDO 0x0F      + 17.3 s  CONGEDO 0x0F
          + 4.2 s  CONGEDO 0x0F      + 19.9 s  CONGEDO 0x0F
          + 6.8 s  CONGEDO 0x0F      + 22.5 s  CONGEDO 0x0F
          + 9.5 s  CONGEDO 0x0F      + 25.2 s  CONGEDO 0x0F
          +12.1 s  CONGEDO 0x0F      + 27.9 s  CONGEDO 0x0F
          +14.7 s  CONGEDO 0x0F      **+30.5 s  OPEN**

      ⇒ **30.5 s of lock**, that is `SILENZIO` (`src/rcp.c:263`, 30 000 ms)
        plus the loop.  Eleven refusals in a row, and the sentence the client
        builds from it — «you already have an active session elsewhere» — **is false**
        for the user: that session is theirs, and it is dead.
      ⚠ The box of `src/rcp.c:229-233` says the silence clock
        *«is the rule that makes the case "the phone died in a tunnel
        and now I cannot get back in" disappear»*.  ⛔ It does not make it disappear: it makes it **last thirty
        seconds**, and packet loss is what makes it ordinary.

═══════════════════════════════════════════════════════════════════════════
ISOLATION — ⛔ and for a bench that touches the network it counts double
═══════════════════════════════════════════════════════════════════════════

  port **7932** · user **provanr3** (uid 1032) ·
  tree `/media/REMOTIX/src/09nr3-src` · work `/media/REMOTIX/tmp/09nr3` ·
  unit `remotix-7932.service`, its own ban-file and socket.

⛔ `enp7s0` (ssh and the user's 7730) **is never touched**: the fault sits on
   `lo`, with two `u32` filters on port 7932 **only**.
⛔ Ports **7900, 7910, 7920** are already measured terms of comparison: they are
   counted and not touched.
⛔ The `netem` on `lo` is **only one per machine**: the lock of
   `banchi/09-lucchetto.py` is taken, **short** leases are granted, and it is released in a
   `finally` — there are other agents queued.
⛔ The detached guardian removes the qdisc even if this script dies.

Usage (from the laptop):
    python3 banchi/09-b78-apertura.py scala   [--giri 10] [--fino wt]
    python3 banchi/09-b78-apertura.py un-verso              # hypothesis (d)
    python3 banchi/09-b78-apertura.py rimetti
    python3 banchi/09-b78-apertura.py stato

Usage (INSIDE the test machine's container — `scala` calls it):
    python3 banchi/09-b78-apertura.py dentro --porta 7932 --giri 10 ...
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))

MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
PAROLA_SUDO = os.environ.get("PAROLA_SUDO", "nicfio")
IND = os.environ.get("IND", "192.168.0.2")
PORTA = int(os.environ.get("PORTA", "7932"))
UTENTE = os.environ.get("UTENTE", "provanr3")
UID_B = int(os.environ.get("UID_B", "1032"))
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/09nr3-src")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/09nr3")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/09nr3-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/09nr3")
FUORI = os.environ.get("FUORI", os.path.join(
    "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX",
    "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/09nr3"))

VIETATA = "enp7s0"        # ssh and the user's 7730 go through it
DEV = "lo"
VICINE = ("7700", "7730", "7900", "7910", "7920")

# The steps.  ⭐ We do not start from 10 %: a scale tells what kind of
#   phenomenon it is, a single point does not.
GRADINI = [0, 1, 3, 5, 8, 10, 15]


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT RUNS INSIDE THE CONTAINER — measures ONE opening at a time
# ═══════════════════════════════════════════════════════════════════════════

def dentro(a):
    """⛔ The phases are timed ONE BY ONE, and with a **wide** ceiling: the
       narrow ceiling is precisely suspect (a), and a bench that repeats it
       cannot see it.
       ⭐ And we record WHERE it stopped, not only that it did not open:
          «QUIC did not shake hands» and «the desktop was not born» are two
          opposite diagnoses, and a boolean confuses them."""
    import asyncio, ssl, struct
    spec = importlib.util.spec_from_file_location(
        "b3", os.path.join(QUI, "01-b3-cliente.py"))
    b3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b3)

    from aioquic.asyncio.client import connect
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.h3.connection import H3_ALPN

    parola = open(a.parola_file).read().strip()
    autorita = "%s:%d" % (a.indirizzo, a.porta)

    async def un_giro():
        t = {}
        fermo = "prima-di-tutto"
        t0 = time.monotonic()

        def segna(nome):
            t[nome] = round((time.monotonic() - t0) * 1000, 1)

        conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                                 max_datagram_frame_size=65536)
        conf.verify_mode = ssl.CERT_NONE
        try:
            async with connect(a.indirizzo, a.porta, configuration=conf,
                               create_protocol=b3.Cliente) as cli:
                fermo = "quic"
                await asyncio.wait_for(cli.wait_connected(), timeout=a.tetto)
                segna("quic")
                if a.fino == "quic":
                    return t, "aperta", None
                fermo = "wt"
                cli.apri_sessione(autorita, a.percorso)
                stato = await asyncio.wait_for(cli.accettata, timeout=a.tetto)
                segna("wt")
                if stato != "200":
                    return t, "respinta", ":status = %s" % stato
                if a.fino == "wt":
                    return t, "aperta", None
                reg = b3.Registratore()
                reg.stream = cli.apri_controllo()
                cli.reg = reg
                fermo = "eccomi"
                cli.manda(b3.inquadra(b3.T["CIAO"], b3.corpo_ciao("pcm", "h264", "8,10")))
                await b3.attendi(cli, "ECCOMI", attesa=a.tetto)
                segna("eccomi")
                fermo = "ammesso"
                cli.manda(b3.inquadra(b3.T["CREDENZIALI"],
                                      b3.s(a.utente) + b3.s(parola)))
                await b3.attendi(cli, "AMMESSO", attesa=a.tetto)
                segna("ammesso")
                if a.fino == "ammesso":
                    return t, "aperta", None
                fermo = "sessione"
                cli.manda(b3.inquadra(
                    b3.T["ATTACCA"],
                    struct.pack("!IIII", 1920, 1080, 1920, 1080) + b3.s("it")))
                await b3.attendi(cli, "SESSIONE", attesa=a.tetto)
                segna("sessione")
                return t, "aperta", None
        except asyncio.TimeoutError:
            return t, "scaduta", "ceiling of %g s expired in phase «%s»" % (a.tetto, fermo)
        except Exception as e:
            return t, "rotta", "%s in phase «%s»: %s" % (type(e).__name__, fermo, e)

    async def tutti():
        for i in range(a.giri):
            t, esito, perche = await un_giro()
            riga = {"giro": i, "tempi_ms": t, "esito": esito, "perche": perche}
            # ⛔⭐ THE DENIED SLOT IS TIMED, not counted.
            #
            #   `GIA_ATTIVA_REMOTA` means «your slot is still taken
            #   by YOUR previous session»: it is a state that PASSES, and a
            #   yes/no makes it look like a permanent fault.  ⇒ We retry
            #   until the slot frees up, and the number that comes out is **how long
            #   the lock lasts** — which is what the user suffers.
            if a.riprova_0f and esito == "rotta" and "0x0f" in (perche or ""):
                t_1 = time.monotonic()
                while time.monotonic() - t_1 < a.riprova_0f:
                    await asyncio.sleep(1.0)
                    t2, e2, p2 = await un_giro()
                    if e2 == "aperta":
                        riga["esito"] = "aperta-dopo-attesa"
                        riga["attesa_posto_ms"] = round(
                            (time.monotonic() - t_1) * 1000, 1)
                        riga["tempi_ms"] = t2
                        break
                    if not (e2 == "rotta" and "0x0f" in (p2 or "")):
                        riga["perche"] = p2
                        break
                else:
                    riga["attesa_posto_ms"] = -1   # ⛔ never freed within the ceiling
            print("APERTURA " + json.dumps(riga, ensure_ascii=False), flush=True)
            if a.pausa:
                await asyncio.sleep(a.pausa)

    asyncio.get_event_loop().run_until_complete(tutti())
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT RUNS ON THE LAPTOP
# ═══════════════════════════════════════════════════════════════════════════

def rem(comando, tetto=300):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACCHINA, comando],
                       capture_output=True, timeout=tetto)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(comando, tetto=300):
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (PAROLA_SUDO, comando),
               tetto)


def qdisc(stat=False):
    return root("/usr/sbin/tc %s qdisc show dev %s" % ("-s" if stat else "", DEV))[1]


GUARDIANO = LAV + "/.guardiano-b78.pid"


def guardiano_arma(secondi):
    guardiano_disarma()
    root('bash -c "setsid sh -c \'sleep %d; /usr/sbin/tc qdisc del dev %s root\' '
         '>/dev/null 2>&1 & echo \\$! > %s"' % (secondi, DEV, GUARDIANO))
    rc, out, _ = root("cat %s 2>/dev/null" % GUARDIANO)
    print("   OK  guardian armed for %d s (pid %s): the network goes back as it was "
          "EVEN if I die" % (secondi, out.strip() or "?"))


def guardiano_disarma():
    rc, out, _ = root("cat %s 2>/dev/null || true" % GUARDIANO)
    p = out.strip()
    if p.isdigit():
        root("kill -TERM -%s 2>/dev/null; kill -TERM %s 2>/dev/null; true" % (p, p))
    root("rm -f %s; true" % GUARDIANO)


def rimetti(dillo=True, disarma=True):
    """⛔⭐ `disarma` is NOT a convenience.  The «0 %» step removes the
       qdisc like all the others, and if removing it also disarmed the
       guardian, the run would go on **without a safety net**: from there
       on a death of the script would leave the machine with `netem` on it, and
       the next bench would attribute a fault of mine to the product.
       ⚠ `banchi/07-b64-rete.py` has this form: its profile `0-liscio`
         calls `rimetti(False)`, which disarms the guardian armed two lines
         earlier — and the seven profiles after it run uncovered."""
    if disarma:
        guardiano_disarma()
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
    q = qdisc()
    ok = "netem" not in q
    if dillo:
        print("   %s the qdisc of «%s» is now: %s"
              % ("OK " if ok else "NO ", DEV, q.strip() or "(none)"))
        print("   --  %s (ssh + 7730): %s"
              % (VIETATA, root("/usr/sbin/tc qdisc show dev %s"
                               % VIETATA)[1].split("\n")[0]))
    return ok


def guasta(perdita_pc, un_verso=False):
    """⛔ The fault, and ONLY on my port.  `un_verso` removes the
       `sport` filter: it is the control of hypothesis (d)."""
    if perdita_pc <= 0:
        rimetti(False, disarma=False)
        return True, "(no fault)"
    passi = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem loss %g%%"
        % (DEV, perdita_pc),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip dport %d 0xffff flowid 1:4"
        % (DEV, PORTA),
    ]
    if not un_verso:
        passi.append(
            "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
            "match ip protocol 17 0xff match ip sport %d 0xffff flowid 1:4"
            % (DEV, PORTA))
    for c in passi:
        rc, out, err = root(c)
        if rc != 0 and "del dev" not in c:
            rimetti()
            return False, "⛔ tc refused «%s»: %s" % (c[-60:], err[:200])
    return True, qdisc().strip()


def netem_conti():
    """⛔ The loss `netem` REALLY applied, read — not deduced."""
    out = qdisc(stat=True)
    dentro_netem = False
    for riga in out.split("\n"):
        if riga.startswith("qdisc netem"):
            dentro_netem = True
            continue
        if dentro_netem and "Sent" in riga:
            m = re.search(r"Sent (\d+) bytes (\d+) pkt \(dropped (\d+)", riga)
            if m:
                sped, pkt, but = int(m.group(1)), int(m.group(2)), int(m.group(3))
                tot = pkt + but
                return {"pkt_passati": pkt, "pkt_buttati": but,
                        "frazione_vera": round(but / tot, 4) if tot else None}
            break
        if dentro_netem and riga.startswith("qdisc"):
            break
    return {"pkt_passati": None, "pkt_buttati": None, "frazione_vera": None}


def ban_scattato(riga0):
    """⛔ Between one run and the next: or a fault of 10 % is attributed to 15 %."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | "
                      "grep -ac 'BANNED' || true" % (riga0 + 1, LAV))
    n = out.strip()
    rc2, out2, _ = root("test -s %s/ban && cat %s/ban || echo '(empty)'" % (LAV, LAV))
    return (n not in ("", "0")), out2.strip()[:200]


def righe_registro():
    rc, out, _ = root("wc -l < %s/registro.log 2>/dev/null || echo 0" % LAV)
    try:
        return int(out.strip())
    except Exception:
        return 0


def vicine():
    fuori = []
    for p in VICINE:
        rc, o, _ = root("ss -uln 2>/dev/null | grep -c ':%s ' || true" % p)
        fuori.append("%s:%s" % (p, o.strip()))
    return " ".join(fuori)


def spedisci():
    """⛔ This script — and the client it takes the `Cliente` class from —
       must be INSIDE the tree, or the container does not see them.

    ⛔⭐ And `01-b3-cliente.py` IS SENT AGAIN AT EVERY RUN, and its fingerprint is
        printed.  `[M]` 23 August 2026: the copy in the tree had stayed
        one change behind (`REGOLA_AUDIO` did not exist yet) and the
        first run died with a `NameError` in phase «prima-di-tutto» —
        that is, looking like «the session does not open».  ⚠ That file is being
        modified today by another agent: whoever measures must DECLARE which copy
        they measured with, or the number cannot be reproduced."""
    fuori = []
    for f in ("09-b78-apertura.py", "01-b3-cliente.py"):
        p = subprocess.run(
            "cat %s | ssh -o BatchMode=yes %s \"cat > %s/banchi/%s\""
            % (os.path.join(QUI, f), MACCHINA, ALB, f), shell=True,
            capture_output=True)
        if p.returncode != 0:
            return None
        h = subprocess.run(["md5sum", os.path.join(QUI, f)],
                           capture_output=True).stdout.decode().split()[0]
        fuori.append("%s %s" % (h[:8], f))
    return fuori


def misura(giri, fino, tetto, pausa=0.0, riprova=0.0):
    dcmd = ("python3 -u %s/banchi/09-b78-apertura.py dentro "
            "--indirizzo %s --porta %d --utente %s --parola-file %s/parola "
            "--giri %d --fino %s --tetto %g --pausa %g --riprova-0f %g"
            % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, giri, fino, tetto,
               pausa, riprova))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dcmd,
                        int(giri * (tetto + pausa + riprova) + 300))
    righe = []
    for r in (out + err).splitlines():
        if r.startswith("APERTURA "):
            try:
                righe.append(json.loads(r[9:]))
            except Exception:
                pass
    return righe, (out + err)[-800:]


def mediana(v):
    v = sorted(v)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else round((v[n // 2 - 1] + v[n // 2]) / 2, 1)


def riassumi(righe, fino):
    aperte = [r for r in righe if r["esito"].startswith("aperta")]
    subito = [r for r in righe if r["esito"] == "aperta"]
    serrate = [r.get("attesa_posto_ms") for r in righe
               if r.get("attesa_posto_ms") is not None]
    fase = {"quic": "quic", "wt": "wt", "ammesso": "ammesso",
            "sessione": "sessione"}[fino]
    tot = [r["tempi_ms"].get(fase) for r in aperte if r["tempi_ms"].get(fase)]
    quic = [r["tempi_ms"].get("quic") for r in aperte if r["tempi_ms"].get("quic")]
    # ⭐ And the number that accuses or acquits `01-b3-cliente.py`: how many runs
    #    would have broken through its 8 s ceiling on the QUIC handshake.
    oltre8 = len([x for x in quic if x > 8000])
    return {"giri": len(righe), "aperte": len(aperte), "aperte_subito": len(subito),
            "quic_mediana_ms": mediana(quic), "quic_max_ms": max(quic) if quic else None,
            "tot_mediana_ms": mediana(tot), "tot_max_ms": max(tot) if tot else None,
            "quic_oltre_8s": oltre8,
            "posto_serrato_ms": serrate,
            "guai": [r["perche"] for r in righe
                     if not r["esito"].startswith("aperta")][:3]}


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("passo", choices=["scala", "un-verso", "dentro", "rimetti", "stato"])
    p.add_argument("--giri", type=int, default=10)
    p.add_argument("--fino", default="wt", choices=["quic", "wt", "ammesso", "sessione"])
    p.add_argument("--tetto", type=float, default=60.0)
    p.add_argument("--pausa", type=float, default=0.0)
    p.add_argument("--gradini", default="")
    # the arguments of the «dentro» half
    p.add_argument("--indirizzo", default=IND)
    p.add_argument("--porta", type=int, default=PORTA)
    p.add_argument("--percorso", default="/rcp/1")
    p.add_argument("--utente", default=UTENTE)
    p.add_argument("--parola-file", default="")
    p.add_argument("--riprova-0f", type=float, default=0, metavar="SECONDI",
                   help="⭐ after a CONGEDO(0x0F) retry for up to N s and "
                        "time HOW LONG the slot lock lasts")
    a = p.parse_args()

    if a.passo == "dentro":
        return dentro(a)

    os.makedirs(FUORI, exist_ok=True)

    if a.passo in ("rimetti", "stato"):
        print("== the test machine's network")
        print("   --  listeners NOT mine (counted, not touched): %s" % vicine())
        return 0 if rimetti() else 2

    gradini = ([float(x) for x in a.gradini.split(",")] if a.gradini
               else ([0, 10] if a.passo == "un-verso" else GRADINI))
    un_verso = (a.passo == "un-verso")

    print("== 09-b78 · OPENING TIME AGAINST LOSS — port %d" % PORTA)
    print("   ⛔ «%s» (ssh + 7730) is NOT touched; the fault sits on «%s», "
          "filters on %d only" % (VIETATA, DEV, PORTA))
    print("   --  listeners NOT mine: %s" % vicine())
    if un_verso:
        print("   ⭐ ONE DIRECTION ONLY (`dport` only): it is the control of hypothesis (d)")
    print("   --  steps: %s %%   runs: %d   up to: «%s»   ceiling: %g s"
          % (gradini, a.giri, a.fino, a.tetto))

    impronte = spedisci()
    if not impronte:
        print("   NO  the scripts did not arrive in the tree: I do not measure")
        return 2
    print("   --  measured with: %s" % " · ".join(impronte))

    luc = importlib.util.spec_from_file_location(
        "luc", os.path.join(QUI, "09-lucchetto.py"))
    lucchetto = importlib.util.module_from_spec(luc)
    luc.loader.exec_module(lucchetto)

    # ⛔ SHORT lease: there are other agents queued.
    per_gradino = a.giri * ((a.tetto if a.fino != "wt" else 12)
                            + a.pausa + a.riprova_0f) + 60
    affitto = int(min(900, len(gradini) * per_gradino + 120))
    lucchetto.prendi("09-b78", secondi=affitto, attesa=2400)
    esiti = []
    try:
        guardiano_arma(affitto)
        for g in gradini:
            print("\n-- loss %g %%" % g)
            riga0 = righe_registro()
            ok, q = guasta(g, un_verso)
            if not ok:
                print("   ", q)
                break
            print("   tc:", " ".join(q.split("\n")[:3])[:150])
            righe, coda = misura(a.giri, a.fino, a.tetto, a.pausa, a.riprova_0f)
            vero = netem_conti()
            bannato, banfile = ban_scattato(riga0)
            r = riassumi(righe, a.fino)
            r.update({"perdita_chiesta_pc": g, "netem": vero,
                      "ban_scattato": bannato, "ban_file": banfile,
                      "un_verso": un_verso})
            if not righe:
                r["coda"] = coda
            esiti.append(r)
            print("   ", json.dumps(r, ensure_ascii=False))
            if bannato:
                print("   ⛔ THE BAN FIRED: I stop, or I would attribute to the "
                      "next step a fault of this one")
                break
    finally:
        print("\n== ⛔ THE NETWORK IS PUT BACK AS IT WAS")
        rimetti()
        lucchetto.molla("09-b78")

    nome = "apertura-un-verso.json" if un_verso else "apertura-scala.json"
    json.dump(esiti, open(os.path.join(FUORI, nome), "w"),
              ensure_ascii=False, indent=1)

    print("\n== THE TABLE — opening time (up to «%s») against loss" % a.fino)
    print("   %-8s %-9s %-8s %-11s %-11s %-9s %s"
          % ("loss", "netem_true", "now+later/n", "quic_med", "tot_med",
             "tot_max", "over 8 s"))
    for e in esiti:
        print("   %-8s %-9s %-8s %-11s %-11s %-9s %s"
              % ("%g %%" % e["perdita_chiesta_pc"],
                 ("%.1f %%" % (100 * e["netem"]["frazione_vera"]))
                 if e["netem"]["frazione_vera"] is not None else "—",
                 "%d+%d/%d" % (e["aperte_subito"],
                               e["aperte"] - e["aperte_subito"], e["giri"]),
                 e["quic_mediana_ms"], e["tot_mediana_ms"], e["tot_max_ms"],
                 e["quic_oltre_8s"]))

    # ⛔ THE PREDICATE, written in the box at the top BEFORE running.
    dieci = [e for e in esiti if e["perdita_chiesta_pc"] == 10]
    if not dieci:
        print("\n   ⚠  the 10 % step was not measured: no verdict")
        return 2
    e = dieci[0]
    passa = (e["aperte"] >= 0.9 * e["giri"]
             and e["tot_mediana_ms"] is not None and e["tot_mediana_ms"] < 5000)
    print("\n== THE VERDICT ON THE `[M]` OF 07-b64 (`7-perdita-10`)")
    if passa:
        print("   ⭐ at 10 %% the session DOES OPEN: %d/%d, median %.0f ms.  "
              "⇒ The «does not open at all in 25 s» was a bench defect."
              % (e["aperte"], e["giri"], e["tot_mediana_ms"]))
        return 0
    print("   ⛔ at 10 %% the session does NOT open as predicted: %d/%d, "
          "median %s ms ⇒ the `[M]` stands, and the curve says why"

          % (e["aperte"], e["giri"], e["tot_mediana_ms"]))
    return 1


if __name__ == "__main__":
    sys.exit(principale())
