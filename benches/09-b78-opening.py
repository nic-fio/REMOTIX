#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b78-opening — HOW LONG A SESSION TAKES TO OPEN, WHEN THE NETWORK LOSES.

⛔⭐ WHY IT EXISTS.  `benches/07-b64-rete.py`, profile `7-loss-10`, carries a
    `[M]` written as an **outcome**, not as a fault:

        «10 %: `[M]` the session does not open at all in 25 s»

    That line was never explained, and `DECISIONS.md` §3.1 point 4
    reopens it: *«a QUIC handshake has the PTO precisely to resend what
    gets lost, and twenty-five seconds do not look like loss, they look like
    something that does not retry»*.

⭐ AND A YES/NO CANNOT ANSWER.  `07-b64` at that step looks at a single
   number — `ricevuti == 0` — and from it one cannot tell «it did not open»
   from «it opened and the audio did not arrive» from «the client gave up».
   ⇒ Here the **opening time** is measured, in steps, and split by **phases**:
   a curve tells what kind of phenomenon it is; a yes/no does not.

═══════════════════════════════════════════════════════════════════════════
THE PREDICTIONS — WRITTEN BEFORE RUNNING (`LESSONS.md` §1.11)
═══════════════════════════════════════════════════════════════════════════

The facts read in the code, before any measurement:

  `[R]` `benches/01-b3-client.py:1222`  `wait_connected()` has **8 s**, not 25.
  `[R]` `benches/01-b3-client.py:1224`  `cli.accettata` has **8 s**.
  `[R]` `benches/01-b3-client.py:1250`  `HERE_I_AM` has 10 s (default of
        `attendi`), `:1266` `ADMITTED` 20 s, `:1284` `SESSION` 10 s.
  `[R]` `benches/07-b64-rete.py`  `--seconds` (default 25) is `--stay`, that is
        **how long the session stays open AFTER having opened**; the ssh
        ceiling is `secondi + 180`.  ⇒ ⛔ **«in 25 s» was never the
        time granted to the handshake.**
  `[R]` `src/transport.c:544`  `ngtcp2_settings_default()` and no line
        of ours touches `handshake_timeout` ⇒ it stays `UINT64_MAX`, that is
        **no ceiling on the handshake on the server side**;
        `initial_rtt` = 333 ms (`NGTCP2_DEFAULT_INITIAL_RTT`).
  `[R]` `src/transport.c:590`  `max_idle_timeout` = 30 000 ms.
  `[R]` `src/main.c:1379,1429`  the loop rearms on `transport_wait_ms()`
        (ceiling 1000 ms) and calls `transport_expired()` →
        `ngtcp2_conn_handle_expiry()`.  ⇒ the server **has** a clock to
        retry, and is not awake only when packets arrive.
  `[R]` `src/transport.c:434`  **no GSO**: one packet per `sendto`.  ⇒
        `netem` drops single QUIC packets, not bunches.
  `[R]` `src/rcp.c:925-927`  `THRESHOLD 3`, `WINDOW` 5 min, `BAN_DURATION` 12 h —
        and the count moves **only** on a PAM verdict for `CREDENTIALS`.
        A handshake that does not finish never gets there.
  `[R]` `benches/07-b64-rete.py` `guasta()`  puts **two** `u32` filters, `sport`
        and `dport`: on `lo` every packet crosses the qdisc **once
        only**, but the outbound one crosses it with `dport` and the return with `sport`
        ⇒ **the loss is paid in both directions**: per round trip `1-(1-p)²`, that is
        **19 %** when `p` = 10 %.

Hence the five predictions, one per hypothesis, and falsifiable:

  (a) **it is the client giving up.**  ⇒ With a wide ceiling (60 s per phase)
      the session opens at 10 % loss, and the **median** opening
      time is **below 3 s**; and at least one run in twenty exceeds the 8 s
      of `01-b3-client.py:1222` — that is, the ceiling is the defect.
  (b) **it is the ban of §4.4-bis.**  ⇒ In the server log
      «BANNATO» / `TOO_MANY_ATTEMPTS` appears, and the **clean** step run
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

1. The opening time up to `ADMITTED` (QUIC handshake + extended CONNECT
   + `HELLO/HERE_I_AM` + `CREDENTIALS/ADMITTED`), 10 runs per step, the
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
      `01-b3-client.py:1222`: hypothesis (a) does not hold either.
   ⛔ The ban never fired (ban-file empty, no «BANNATO» in the
      log): hypothesis (b) is refuted.
   ⛔ `tc -s qdisc` says the qdisc is ONE and is crossed **one
      packet at a time**: hypothesis (d) («applied twice») is refuted.
      ⚠ It remains true that the two filters take both DIRECTIONS, so a network
        round trip pays `1-(1-p)²`; but a datagram, which goes one way only, pays `p`.

2. The exact form of `07-b64` — the real client, PCM, with the tone on,
   `--stay 20` — at **10 %**:

       SESSION open: True
       [audio] received **3235** · 3 105 600 bytes · codec 2
       SERVER: sent 3607 · dropped 0 · **refused 391** · deferred 293 718
       judgement: resa_campioni **0.810** · purity 0.182 · scoppiettii 19.1/s

   ⇒ 3235/3607 = **89.7 % arrived on the wire**, which is exactly the 10 %
     removed once.  ⚠ And `resa_campioni` drops to 0.810 because it also
     includes the **391 blocks the server NEVER sent** (congestion
     window closed): «lost on the wire» and «never sent» are two facts, and
     the yield adds them up.

3. ⛔⛔ **WHY THE BENCH SAID THE OPPOSITE.**  The predicate of that step
   is `a_non_si_apre(n) = (n["received"] == 0)`, and `01-b3-client.py` prints
   `[audio] ricevuti 0` **even from the `except` branch** (`:1286`), before
   re-raising.  ⇒ **Any** way of failing — a `FAREWELL`, an expired
   ceiling, a `NameError` in the bench — produces «ricevuti 0» and passes that
   step as GREEN.  It is a predicate that cannot give red, that is the form
   of `LESSONS.md` §1.9: it did not measure «it does not open», it measured «I did not
   receive», and the two look the same.
   `[M]` checked by running the real client **without a tone**: `SESSION=True` at
   every run, `[audio] ricevuti 0` at every run, at 1 % as at 10 %.

4. ⭐⭐ **AND BEHIND IT THERE IS A FACT OF THE PRODUCT, and it is on the phase's target.**
   The only way in which, under loss, an opening really fails is:
   `ATTACH` → `FAREWELL(0x0F) ALREADY_ACTIVE_REMOTELY`, that is **the slot of the
   previous session is still taken**.  `[M]` in the first scale run:
   5/10 at 10 %, 0/10 at 15 %, with the log saying
   *«slot DENIED to provanr3 … it is held by another client of this same
   user (taken: 1)»*.

   ⛔ And the count closes **without any `netem`**, because a **lost**
      goodbye and a goodbye **never said** are the same fact for the server:
      the client is killed with `-9` and we measure from when the slot is free
      again.  `[M]` 23 August 2026:

          + 1.6 s  FAREWELL 0x0F      + 17.3 s  FAREWELL 0x0F
          + 4.2 s  FAREWELL 0x0F      + 19.9 s  FAREWELL 0x0F
          + 6.8 s  FAREWELL 0x0F      + 22.5 s  FAREWELL 0x0F
          + 9.5 s  FAREWELL 0x0F      + 25.2 s  FAREWELL 0x0F
          +12.1 s  FAREWELL 0x0F      + 27.9 s  FAREWELL 0x0F
          +14.7 s  FAREWELL 0x0F      **+30.5 s  OPEN**

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
   `benches/09-lock.py` is taken, **short** leases are granted, and it is released in a
   `finally` — there are other agents queued.
⛔ The detached guardian removes the qdisc even if this script dies.

Usage (from the laptop):
    python3 benches/09-b78-opening.py ladder   [--rounds 10] [--until wt]
    python3 benches/09-b78-opening.py one-way              # hypothesis (d)
    python3 benches/09-b78-opening.py restore
    python3 benches/09-b78-opening.py status

Usage (INSIDE the test machine's container — `ladder` calls it):
    python3 benches/09-b78-opening.py inside --port 7932 --rounds 10 ...
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))

MACHINE = os.environ.get("MACHINE", "nicfio@192.168.0.2")
SUDO_PASSWORD = os.environ.get("SUDO_PASSWORD", "nicfio")
ADDR = os.environ.get("ADDR", "192.168.0.2")
PORT = int(os.environ.get("PORT", "7932"))
ACCOUNT = os.environ.get("ACCOUNT", "provanr3")
UID_B = int(os.environ.get("UID_B", "1032"))
TREE_DIR = os.environ.get("TREE", "/media/REMOTIX/src/09nr3-src")
WORKDIR = os.environ.get("WORKDIR", "/media/REMOTIX/tmp/09nr3")
INSIDE_TREE = os.environ.get("INSIDE_TREE", "/srv/src/09nr3-src")
INSIDE_WORK = os.environ.get("INSIDE_WORK", "/srv/remotix/tmp/09nr3")
OUT = os.environ.get("OUT", os.path.join(
    "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX",
    "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad/09nr3"))

VIETATA = "enp7s0"        # ssh and the user's 7730 go through it
DEV = "lo"
NEARBY_PORTS = ("7700", "7730", "7900", "7910", "7920")

# The steps.  ⭐ We do not start from 10 %: a scale tells what kind of
#   phenomenon it is, a single point does not.
RUNGS = [0, 1, 3, 5, 8, 10, 15]


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT RUNS INSIDE THE CONTAINER — measures ONE opening at a time
# ═══════════════════════════════════════════════════════════════════════════

def inside(a):
    """⛔ The phases are timed ONE BY ONE, and with a **wide** ceiling: the
       narrow ceiling is precisely suspect (a), and a bench that repeats it
       cannot see it.
       ⭐ And we record WHERE it stopped, not only that it did not open:
          «QUIC did not shake hands» and «the desktop was not born» are two
          opposite diagnoses, and a boolean confuses them."""
    import asyncio, ssl, struct
    spec = importlib.util.spec_from_file_location(
        "b3", os.path.join(HERE, "01-b3-client.py"))
    b3 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(b3)

    from aioquic.asyncio.client import connect
    from aioquic.quic.configuration import QuicConfiguration
    from aioquic.h3.connection import H3_ALPN

    password = open(a.password_file).read().strip()
    authority = "%s:%d" % (a.address, a.port)

    async def one_round():
        t = {}
        stopped = "prima-di-tutto"
        t0 = time.monotonic()

        def mark(name):
            t[name] = round((time.monotonic() - t0) * 1000, 1)

        conf = QuicConfiguration(is_client=True, alpn_protocols=H3_ALPN,
                                 max_datagram_frame_size=65536)
        conf.verify_mode = ssl.CERT_NONE
        try:
            async with connect(a.address, a.port, configuration=conf,
                               create_protocol=b3.Client) as cli:
                stopped = "quic"
                await asyncio.wait_for(cli.wait_connected(), timeout=a.cap)
                mark("quic")
                if a.until == "quic":
                    return t, "is_open", None
                stopped = "wt"
                cli.open_session(authority, a.path)
                status = await asyncio.wait_for(cli.accepted, timeout=a.cap)
                mark("wt")
                if status != "200":
                    return t, "respinta", ":status = %s" % status
                if a.until == "wt":
                    return t, "is_open", None
                reg = b3.Recorder()
                reg.stream = cli.open_control()
                cli.reg = reg
                stopped = "eccomi"
                cli.send_msg(b3.wrap(b3.T["HELLO"], b3.body_hello("pcm", "h264", "8,10")))
                await b3.should_wait(cli, "HERE_I_AM", wait=a.cap)
                mark("eccomi")
                stopped = "ammesso"
                cli.send_msg(b3.wrap(b3.T["CREDENTIALS"],
                                      b3.s(a.user) + b3.s(password)))
                await b3.should_wait(cli, "ADMITTED", wait=a.cap)
                mark("ammesso")
                if a.until == "admitted":
                    return t, "is_open", None
                stopped = "session"
                cli.send_msg(b3.wrap(
                    b3.T["ATTACH"],
                    struct.pack("!IIII", 1920, 1080, 1920, 1080) + b3.s("it")))
                await b3.should_wait(cli, "SESSION", wait=a.cap)
                mark("session")
                return t, "is_open", None
        except asyncio.TimeoutError:
            return t, "scaduta", "ceiling of %g s expired in phase «%s»" % (a.cap, stopped)
        except Exception as e:
            return t, "rotta", "%s in phase «%s»: %s" % (type(e).__name__, stopped, e)

    async def all_items():
        for i in range(a.rounds):
            t, outcome, why = await one_round()
            line = {"round": i, "tempi_ms": t, "outcome": outcome, "why": why}
            # ⛔⭐ THE DENIED SLOT IS TIMED, not counted.
            #
            #   `ALREADY_ACTIVE_REMOTELY` means «your slot is still taken
            #   by YOUR previous session»: it is a state that PASSES, and a
            #   yes/no makes it look like a permanent fault.  ⇒ We retry
            #   until the slot frees up, and the number that comes out is **how long
            #   the lock lasts** — which is what the user suffers.
            if a.retry_0f and outcome == "rotta" and "0x0f" in (why or ""):
                t_1 = time.monotonic()
                while time.monotonic() - t_1 < a.retry_0f:
                    await asyncio.sleep(1.0)
                    t2, e2, p2 = await one_round()
                    if e2 == "is_open":
                        line["outcome"] = "aperta-dopo-attesa"
                        line["attesa_posto_ms"] = round(
                            (time.monotonic() - t_1) * 1000, 1)
                        line["tempi_ms"] = t2
                        break
                    if not (e2 == "rotta" and "0x0f" in (p2 or "")):
                        line["why"] = p2
                        break
                else:
                    line["attesa_posto_ms"] = -1   # ⛔ never freed within the ceiling
            print("APERTURA " + json.dumps(line, ensure_ascii=False), flush=True)
            if a.pause:
                await asyncio.sleep(a.pause)

    asyncio.get_event_loop().run_until_complete(all_items())
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT RUNS ON THE LAPTOP
# ═══════════════════════════════════════════════════════════════════════════

def rem(command, cap=300):
    p = subprocess.run(["ssh", "-o", "BatchMode=yes", MACHINE, command],
                       capture_output=True, timeout=cap)
    return (p.returncode, p.stdout.decode("utf-8", "replace"),
            p.stderr.decode("utf-8", "replace"))


def root(command, cap=300):
    return rem("printf '%%s\\n' '%s' | sudo -S -p '' %s" % (SUDO_PASSWORD, command),
               cap)


def qdisc(stat=False):
    return root("/usr/sbin/tc %s qdisc show dev %s" % ("-s" if stat else "", DEV))[1]


GUARDIAN = WORKDIR + "/.guardiano-b78.pid"


def guardian_arm(seconds):
    guardian_disarm()
    root('bash -c "setsid sh -c \'sleep %d; /usr/sbin/tc qdisc del dev %s root\' '
         '>/dev/null 2>&1 & echo \\$! > %s"' % (seconds, DEV, GUARDIAN))
    rc, out, _ = root("cat %s 2>/dev/null" % GUARDIAN)
    print("   OK  guardian armed for %d s (pid %s): the network goes back as it was "
          "EVEN if I die" % (seconds, out.strip() or "?"))


def guardian_disarm():
    rc, out, _ = root("cat %s 2>/dev/null || true" % GUARDIAN)
    p = out.strip()
    if p.isdigit():
        root("kill -TERM -%s 2>/dev/null; kill -TERM %s 2>/dev/null; true" % (p, p))
    root("rm -f %s; true" % GUARDIAN)


def restore(report_it=True, disarm=True):
    """⛔⭐ `disarm` is NOT a convenience.  The «0 %» step removes the
       qdisc like all the others, and if removing it also disarmed the
       guardian, the run would go on **without a safety net**: from there
       on a death of the script would leave the machine with `netem` on it, and
       the next bench would attribute a fault of mine to the product.
       ⚠ `benches/07-b64-rete.py` has this form: its profile `0-smooth`
         calls `rimetti(False)`, which disarms the guardian armed two lines
         earlier — and the seven profiles after it run uncovered."""
    if disarm:
        guardian_disarm()
    root("/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV)
    q = qdisc()
    ok = "netem" not in q
    if report_it:
        print("   %s the qdisc of «%s» is now: %s"
              % ("OK " if ok else "NO ", DEV, q.strip() or "(none)"))
        print("   --  %s (ssh + 7730): %s"
              % (VIETATA, root("/usr/sbin/tc qdisc show dev %s"
                               % VIETATA)[1].split("\n")[0]))
    return ok


def broken(loss_pc, one_way=False):
    """⛔ The fault, and ONLY on my port.  `one_way` removes the
       `sport` filter: it is the control of hypothesis (d)."""
    if loss_pc <= 0:
        restore(False, disarm=False)
        return True, "(no fault)"
    steps = [
        "/usr/sbin/tc qdisc del dev %s root 2>/dev/null; true" % DEV,
        "/usr/sbin/tc qdisc add dev %s root handle 1: prio bands 4" % DEV,
        "/usr/sbin/tc qdisc add dev %s parent 1:4 handle 40: netem loss %g%%"
        % (DEV, loss_pc),
        "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
        "match ip protocol 17 0xff match ip dport %d 0xffff flowid 1:4"
        % (DEV, PORT),
    ]
    if not one_way:
        steps.append(
            "/usr/sbin/tc filter add dev %s protocol ip parent 1:0 prio 1 u32 "
            "match ip protocol 17 0xff match ip sport %d 0xffff flowid 1:4"
            % (DEV, PORT))
    for c in steps:
        rc, out, err = root(c)
        if rc != 0 and "del dev" not in c:
            restore()
            return False, "⛔ tc refused «%s»: %s" % (c[-60:], err[:200])
    return True, qdisc().strip()


def netem_counts():
    """⛔ The loss `netem` REALLY applied, read — not deduced."""
    out = qdisc(stat=True)
    inside_netem = False
    for line in out.split("\n"):
        if line.startswith("qdisc netem"):
            inside_netem = True
            continue
        if inside_netem and "Sent" in line:
            m = re.search(r"Sent (\d+) bytes (\d+) pkt \(dropped (\d+)", line)
            if m:
                sped, pkt, but = int(m.group(1)), int(m.group(2)), int(m.group(3))
                tot = pkt + but
                return {"pkt_passati": pkt, "pkt_buttati": but,
                        "frazione_vera": round(but / tot, 4) if tot else None}
            break
        if inside_netem and line.startswith("qdisc"):
            break
    return {"pkt_passati": None, "pkt_buttati": None, "frazione_vera": None}


def ban_triggered(line0):
    """⛔ Between one run and the next: or a fault of 10 % is attributed to 15 %."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | "
                      "grep -ac 'BANNED' || true" % (line0 + 1, WORKDIR))
    n = out.strip()
    rc2, out2, _ = root("test -s %s/ban && cat %s/ban || echo '(empty)'" % (WORKDIR, WORKDIR))
    return (n not in ("", "0")), out2.strip()[:200]


def log_line_list():
    rc, out, _ = root("wc -l < %s/registro.log 2>/dev/null || echo 0" % WORKDIR)
    try:
        return int(out.strip())
    except Exception:
        return 0


def near():
    report = []
    for p in NEARBY_PORTS:
        rc, o, _ = root("ss -uln 2>/dev/null | grep -c ':%s ' || true" % p)
        report.append("%s:%s" % (p, o.strip()))
    return " ".join(report)


def ship_sources():
    """⛔ This script — and the client it takes the `Client` class from —
       must be INSIDE the tree, or the container does not see them.

    ⛔⭐ And `01-b3-client.py` IS SENT AGAIN AT EVERY RUN, and its fingerprint is
        printed.  `[M]` 23 August 2026: the copy in the tree had stayed
        one change behind (`AUDIO_RULE` did not exist yet) and the
        first run died with a `NameError` in phase «prima-di-tutto» —
        that is, looking like «the session does not open».  ⚠ That file is being
        modified today by another agent: whoever measures must DECLARE which copy
        they measured with, or the number cannot be reproduced."""
    report = []
    for f in ("09-b78-opening.py", "01-b3-client.py"):
        p = subprocess.run(
            "cat %s | ssh -o BatchMode=yes %s \"cat > %s/benches/%s\""
            % (os.path.join(HERE, f), MACHINE, TREE_DIR, f), shell=True,
            capture_output=True)
        if p.returncode != 0:
            return None
        h = subprocess.run(["md5sum", os.path.join(HERE, f)],
                           capture_output=True).stdout.decode().split()[0]
        report.append("%s %s" % (h[:8], f))
    return report


def measure(rounds, until, cap, delay=0.0, retry=0.0):
    dcmd = ("python3 -u %s/benches/09-b78-opening.py inside "
            "--address %s --port %d --user %s --password-file %s/parola "
            "--rounds %d --until %s --cap %g --pause %g --retry-0f %g"
            % (INSIDE_TREE, ADDR, PORT, ACCOUNT, INSIDE_WORK, rounds, until, cap,
               delay, retry))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dcmd,
                        int(rounds * (cap + delay + retry) + 300))
    lines = []
    for r in (out + err).splitlines():
        if r.startswith("APERTURA "):
            try:
                lines.append(json.loads(r[9:]))
            except Exception:
                pass
    return lines, (out + err)[-800:]


def median(v):
    v = sorted(v)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else round((v[n // 2 - 1] + v[n // 2]) / 2, 1)


def summarize(lines, until):
    opened = [r for r in lines if r["outcome"].startswith("is_open")]
    immediately = [r for r in lines if r["outcome"] == "is_open"]
    tight = [r.get("attesa_posto_ms") for r in lines
               if r.get("attesa_posto_ms") is not None]
    phase = {"quic": "quic", "wt": "wt", "ammesso": "ammesso",
            "session": "session"}[until]
    tot = [r["tempi_ms"].get(phase) for r in opened if r["tempi_ms"].get(phase)]
    quic = [r["tempi_ms"].get("quic") for r in opened if r["tempi_ms"].get("quic")]
    # ⭐ And the number that accuses or acquits `01-b3-client.py`: how many runs
    #    would have broken through its 8 s ceiling on the QUIC handshake.
    beyond8 = len([x for x in quic if x > 8000])
    return {"rounds": len(lines), "aperte": len(opened), "aperte_subito": len(immediately),
            "quic_mediana_ms": median(quic), "quic_max_ms": max(quic) if quic else None,
            "tot_mediana_ms": median(tot), "tot_max_ms": max(tot) if tot else None,
            "quic_oltre_8s": beyond8,
            "posto_serrato_ms": tight,
            "troubles": [r["why"] for r in lines
                     if not r["outcome"].startswith("is_open")][:3]}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("step", choices=["ladder", "one-way", "inside", "restore", "status"])
    p.add_argument("--rounds", type=int, default=10)
    p.add_argument("--until", default="wt", choices=["quic", "wt", "admitted", "session"])
    p.add_argument("--cap", type=float, default=60.0)
    p.add_argument("--pause", type=float, default=0.0)
    p.add_argument("--rungs", default="")
    # the arguments of the «inside» half
    p.add_argument("--address", default=ADDR)
    p.add_argument("--port", type=int, default=PORT)
    p.add_argument("--path", default="/rcp/1")
    p.add_argument("--user", default=ACCOUNT)
    p.add_argument("--password-file", default="")
    p.add_argument("--retry-0f", type=float, default=0, metavar="SECONDS",
                   help="⭐ after a FAREWELL(0x0F) retry for up to N s and "
                        "time HOW LONG the slot lock lasts")
    a = p.parse_args()

    if a.step == "inside":
        return inside(a)

    os.makedirs(OUT, exist_ok=True)

    if a.step in ("restore", "status"):
        print("== the test machine's network")
        print("   --  listeners NOT mine (counted, not touched): %s" % near())
        return 0 if restore() else 2

    rungs = ([float(x) for x in a.rungs.split(",")] if a.rungs
               else ([0, 10] if a.step == "one-way" else RUNGS))
    one_way = (a.step == "one-way")

    print("== 09-b78 · OPENING TIME AGAINST LOSS — port %d" % PORT)
    print("   ⛔ «%s» (ssh + 7730) is NOT touched; the fault sits on «%s», "
          "filters on %d only" % (VIETATA, DEV, PORT))
    print("   --  listeners NOT mine: %s" % near())
    if one_way:
        print("   ⭐ ONE DIRECTION ONLY (`dport` only): it is the control of hypothesis (d)")
    print("   --  steps: %s %%   runs: %d   up to: «%s»   ceiling: %g s"
          % (rungs, a.rounds, a.until, a.cap))

    fingerprints = ship_sources()
    if not fingerprints:
        print("   NO  the scripts did not arrive in the tree: I do not measure")
        return 2
    print("   --  measured with: %s" % " · ".join(fingerprints))

    luc = importlib.util.spec_from_file_location(
        "luc", os.path.join(HERE, "09-lock.py"))
    lock = importlib.util.module_from_spec(luc)
    luc.loader.exec_module(lock)

    # ⛔ SHORT lease: there are other agents queued.
    per_rung = a.rounds * ((a.cap if a.until != "wt" else 12)
                            + a.pause + a.retry_0f) + 60
    lease = int(min(900, len(rungs) * per_rung + 120))
    lock.take("09-b78", seconds=lease, wait=2400)
    outcomes = []
    try:
        guardian_arm(lease)
        for g in rungs:
            print("\n-- loss %g %%" % g)
            line0 = log_line_list()
            ok, q = broken(g, one_way)
            if not ok:
                print("   ", q)
                break
            print("   tc:", " ".join(q.split("\n")[:3])[:150])
            lines, queue = measure(a.rounds, a.until, a.cap, a.pause, a.retry_0f)
            real = netem_counts()
            banned, banfile = ban_triggered(line0)
            r = summarize(lines, a.until)
            r.update({"perdita_chiesta_pc": g, "netem": real,
                      "ban_scattato": banned, "ban_file": banfile,
                      "one_way": one_way})
            if not lines:
                r["queue"] = queue
            outcomes.append(r)
            print("   ", json.dumps(r, ensure_ascii=False))
            if banned:
                print("   ⛔ THE BAN FIRED: I stop, or I would attribute to the "
                      "next step a fault of this one")
                break
    finally:
        print("\n== ⛔ THE NETWORK IS PUT BACK AS IT WAS")
        restore()
        lock.release("09-b78")

    name = "apertura-un-verso.json" if one_way else "apertura-scala.json"
    json.dump(outcomes, open(os.path.join(OUT, name), "w"),
              ensure_ascii=False, indent=1)

    print("\n== THE TABLE — opening time (up to «%s») against loss" % a.until)
    print("   %-8s %-9s %-8s %-11s %-11s %-9s %s"
          % ("loss", "netem_true", "now+later/n", "quic_med", "tot_med",
             "tot_max", "over 8 s"))
    for e in outcomes:
        print("   %-8s %-9s %-8s %-11s %-11s %-9s %s"
              % ("%g %%" % e["perdita_chiesta_pc"],
                 ("%.1f %%" % (100 * e["netem"]["frazione_vera"]))
                 if e["netem"]["frazione_vera"] is not None else "—",
                 "%d+%d/%d" % (e["aperte_subito"],
                               e["aperte"] - e["aperte_subito"], e["rounds"]),
                 e["quic_mediana_ms"], e["tot_mediana_ms"], e["tot_max_ms"],
                 e["quic_oltre_8s"]))

    # ⛔ THE PREDICATE, written in the box at the top BEFORE running.
    ten = [e for e in outcomes if e["perdita_chiesta_pc"] == 10]
    if not ten:
        print("\n   ⚠  the 10 % step was not measured: no verdict")
        return 2
    e = ten[0]
    passes = (e["aperte"] >= 0.9 * e["rounds"]
             and e["tot_mediana_ms"] is not None and e["tot_mediana_ms"] < 5000)
    print("\n== THE VERDICT ON THE `[M]` OF 07-b64 (`7-loss-10`)")
    if passes:
        print("   ⭐ at 10 %% the session DOES OPEN: %d/%d, median %.0f ms.  "
              "⇒ The «does not open at all in 25 s» was a bench defect."
              % (e["aperte"], e["rounds"], e["tot_mediana_ms"]))
        return 0
    print("   ⛔ at 10 %% the session does NOT open as predicted: %d/%d, "
          "median %s ms ⇒ the `[M]` stands, and the curve says why"

          % (e["aperte"], e["rounds"], e["tot_mediana_ms"]))
    return 1


if __name__ == "__main__":
    sys.exit(main())
