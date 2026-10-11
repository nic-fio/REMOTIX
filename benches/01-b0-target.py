#!/usr/bin/env python3
"""01-b0-target.py — ⛔ THE LOG OF EVERY RUN, AND THE LINE THAT SAYS WHAT
IT MEASURED AGAINST.

The Python twin of `01-b0-target.sh`: that one chooses and turns on the
target, this one **writes** it.  B5, B6, B7 and B8 include it.

===========================================================================
⛔ WHY IT EXISTS, AND IT IS NOT A CONVENIENCE

*"A log that does not say which server it measured against lines up numbers
of two different things"* — and it is the form of error this project pays for
most often, because it has no symptom: the numbers are all good, one by one.

⛔ And the concrete case is already on disk.  `benches/prodotto/b8-samples.jsonl` and
   `b8-facts.jsonl` are the samples of the second fixed taken against the
   **product** on the night of 10 Aug 2026; `b8-facts.jsonl` in
   `/media/REMOTIX/src/` are those taken against the **graft**.  They have the
   same name, the same shape, the same fields — and no line, in either
   of the two, says which server answered.  Whoever put them together to have
   "more samples" would compute the median of two different populations believing
   they were reducing the noise.

⭐ Hence the three things this file imposes, and that no bench can forget:

  1. **every** line carries `bersaglio`, `porta` and `giro`;
  2. the first line of every round is a `giro` record that also carries
     the **fingerprint seen** — that is, what the server's log says it
     is, not what the bench declared (`LESSONS.md` §1.9,
     corollary 5);
  3. it is written and **synced** line by line: a file written and closed is
     a fact, a line in a buffer is a hope about the moment in which
     someone will see it (§1.9, seventh guise — and that guise has already accused
     the right code in this phase).

===========================================================================
⛔ AND THE TARGET IS NOT A LABEL: IT IS A SET OF FACTS

`PROFILO` holds the **known** differences between the two servers, measured by reading
the code on 11 Aug 2026.  A bench reads them from here instead of discovering them anew,
and above all instead of **not** discovering them and giving red.
"""
import json
import os
import time

# ===========================================================================
# ⛔ THE KNOWN DIFFERENCES, WRITTEN BEFORE MEASURING.
#
# Every line has the file and the reason next to it: whoever found it false must be
# able to trace back in a minute to where we read it.
# ===========================================================================
PROFILE = {
    "innesto": {
        "port": 7447,
        "eseguibile": "bsslserver (ngtcp2 example + the two grafts)",
        # ⛔ B7: `RCP_SERVER_CLOSING` (0x0C) cannot be produced.
        #    `01-b3-graft-rcp.py` has no shutdown path —
        #    grep: zero occurrences — so the reasons that can be provoked are SEVEN.
        "spegnimento": False,
        "motivi_provocabili": 7,
        # Where a shutdown path can live on this target.
        "sorgenti_spegnimento": ("rcp/rcp.c", "01-b3-graft-rcp.py"),
        # ⭐ The transport idle cap can be chosen (`--timeout=Ns`).
        "idle_scelta": True,
        "idle_lungo": 120000,
        "idle_corto": 15000,
        # The startup lines about the ban, for B8.
        "r_ban_caricati": "bans loaded:",
        "r_ban_illeggibile": "COULD NOT READ the ban file",
        "r_pagina": "TCP page at",
        # If the ban file exists and cannot be read, this server starts all the same
        # and writes so.
        "ban_illeggibile_parte": True,
        # The fingerprint of every line of its log.
        "impronta": r"REMOTIX B[35]:",
        "check": "REMOTIX B3",
        # ⛔⭐ THE B2 ECHO, and this line exists because of a trap already paid for
        #     TWICE.  The minimal server of B2 **sends back** the bytes
        #     received on the streams the client opens — it is the "byte that comes back"
        #     of group 2 of `PHASES.md` §01-filo-nudo.  A tool that waits for
        #     that echo stays hung against the product, which has no echo,
        #     and the red that came out of it on 10 Aug 2026 was diagnosed
        #     for hours as a "certificate defect".
        "eco": True,
        # ⛔⭐ THE CAP OF §7.17 — WebTransport session open and control
        #     channel never opened, 5 s — THIS SERVER DOES NOT HAVE IT.
        #
        # `[M]` 11 Aug 2026, measured by B6 in a certification round:
        # `ciao-senza-controllo` stays hung **20 s without anything happening**.
        # ⭐ And the bench was right: the cure of §7.17 is `WT_CAP_CHANNEL_NS`
        # in `src/webtransport.c`, that is in the PRODUCT.  The graft is the ngtcp2
        # example with the grafts on top, and it has no WebTransport layer of its
        # own — that cap has no place to live.
        # ⚠ It is the same shape as `spegnimento`: a property that exists on one
        #   target only, declared instead of discovered at every round.
        # ⛔ Without this line B6 cannot be CERTIFIED: the healthy round exits 1,
        #   and a bench that does not start from green proves nothing with the fault.
        "tetto_canale": False,
    },
    "product": {
        "port": 7448,
        "eseguibile": "remotix (src/)",
        # ⭐ `src/main.c` dismisses all sessions with `SERVER_CLOSING`
        #    before exiting, and waits up to two seconds for the bytes to leave:
        #    reason 0x0C CAN be provoked, and the provocable ones become EIGHT.
        "spegnimento": True,
        "motivi_provocabili": 8,
        # ⛔ And we do NOT search in `rcp.c`: `rcp.c` is identical in the two servers and does not
        #    know a process exists.  The path lives in `main.c`,
        #    `transport.c` (`transport_dismiss_all`) and `webtransport.c`
        #    (`wt_dismiss`).  A denominator is read where the thing happens.
        "sorgenti_spegnimento": ("remotix/rcp.c", "remotix/main.c",
                                 "remotix/transport.c", "remotix/webtransport.c"),
        # ⛔ `#define IDLE_MS 30000` in `src/transport.c`, and no option
        #    touches it (no `getenv` in all of `src/`).
        "idle_scelta": False,
        "idle_lungo": 30000,
        "idle_corto": 30000,
        "r_ban_caricati": "addresses loaded",
        "r_ban_illeggibile": "exists and could NOT be read",
        "r_pagina": "listening over TCP on",
        # ⛔⭐ AND HERE THE TWO SERVERS DO THE OPPOSITE: the product REFUSES to
        #     start (`src/main.c`), because "it is not "zero bans", it is the
        #     protection of §4.4-bis turned off".
        "ban_illeggibile_parte": False,
        "impronta": r"^\d\d:\d\d:\d\d\.\d\d\d (startup|quic|wt|rcp|page|cert) ",
        "check": "REMOTIX — phase 1, the bare wire",
        # ⛔ NO ECHO.  `src/webtransport.c`, `discard_extra_stream()`:
        #    "the bytes of a stream too many are thrown away, and NOT sent
        #    back".  ⚠ None of the four benches must **wait** for bytes
        #    coming back on a stream it opened itself: whoever did would stay
        #    hung, and the diagnosis would land on anything except on
        #    this line.  B5 meets it and already tolerates it (it discards the echo without
        #    waiting for it): here it is declared, because a tolerated absence and
        #    an absence that never happened must not look the same.
        "eco": False,
        # ⭐ `WT_CAP_CHANNEL_NS` in `src/webtransport.c`, armed
        #    at the opening of the session (`cb_end_headers`) and
        #    enforced in `wt_beat`.  `DECISIONS.md` §7.17.
        "tetto_canale": True,
    },
}


# ⛔ And the verdict on the echo is not a note: it is a number the bench compares.
def expected_echo(target):
    """How many streams must bring bytes back from the server.  0 on the product."""
    return profile(target)["eco"]


def profile(name):
    """⛔ An unknown target does not fall back on «innesto»: it stops.

    ⚠ `check` is in the grammar (`--target {innesto,prodotto,
      check}`, the same as the transport probe) and **not** in this
      table: for B5, B6, B7 and B8 the server faulty on purpose towards the wire
      does not exist yet.  ⛔ Letting it fall onto «innesto» would give a GREEN of the
      healthy case in place of a check that must turn red, which is worse than
      an absent check.
    """
    if name == "check":
        raise SystemExit(
            "⛔ target «controllo»: the grammar provides for it, these four "
            "benches do not have it yet.  It would be the server FAULTY ON "
            "PURPOSE, the one against which the bench must turn red "
            "(LESSONS.md §1.2); today it exists only towards the page "
            "(01-b11-graft-faults.py), not towards the wire.")
    if name not in PROFILE:
        raise SystemExit(
            f"⛔ unknown target «{name}»: the values are "
            f"{', '.join(PROFILE)} and «controllo».  Not falling back on any — "
            f"I would measure one server while declaring another.")
    return PROFILE[name]


def add_arguments(p):
    """⛔ The same four arguments in all four benches, and in one place
    only — so the day one is added it is added once.

    ⛔ `--target` is **mandatory and without default**, and it is the same
       shape with which the transport probe chooses its own: two different
       conventions for the same thing are the defect of the seams.  ⚠ A
       default here would mean that a round can measure the wrong server
       by distraction, and the log would write it as if it were
       the right one.
    """
    p.add_argument("--target", required=True,
                   choices=("graft", "product", "control"),
                   help="⛔ mandatory: which server is measured against")
    p.add_argument("--output", default="",
                   help="the log of the facts of this round (.jsonl)")
    p.add_argument("--round", default="",
                   help="the identifier of the round, the same for all lines")
    p.add_argument("--md5", default="",
                   help="the md5 fingerprint of the measured BINARY, for the log")
    return p


def sources_shutdown(target, inside="/srv/src"):
    """⛔ Where a shutdown path is searched for, for the denominator of B7.

    ⛔⭐ AND IT IS NOT `rcp.c`, which is identical byte for byte in the two servers and does not know
        a process exists: searching there would say "zero" on both
        targets, and it is a denominator read where the thing does NOT happen
        (`LESSONS.md` §1.9, corollary 5).  On the product the path lives in
        `main.c`, `transport.c` and `webtransport.c`.
    """
    return [f"{inside}/{p}" for p in profile(target)["sorgenti_spegnimento"]]


class Log:
    """One line per fact, with the target inside, and synced at once.

    ⚠ An empty `fpath` is NOT a silent error: the bench goes on
      measuring and printing, but `dichiarato_senza_registro` becomes true and whoever
      reads the verdict sees it.  ⛔ An absent log and an empty log must not
      look the same.
    """

    def __init__(self, fpath, target, port, round_id=None, md5=None):
        self.fpath = fpath or ""
        self.target = target
        self.port = port
        self.round_id = round_id or time.strftime("%Y%m%d-%H%M%S")
        # ⛔ The md5 fingerprint of the measured BINARY, not of the source: it is the only
        #    way of knowing, six hours later, whether two rounds measured the same
        #    program.  ⚠ `[M]` 11 Aug 2026: the product binary was
        #    an hour older than the sources, and the log of the last
        #    start carried a wording from two generations before.
        self.md5 = md5 or "unknown"
        self.written = 0
        self.fault = None
        self.profile = profile(target)

    def open_round(self, bench, scene, fingerprint_seen=None, extra=None):
        """⛔ The first line of every round, and it carries the fingerprint SEEN.

        `fingerprint_seen` is what the SERVER's log says it is; if
        it is `None` it means "I did not look at it", which is not "it matches".
        """
        rec = {"type": "round", "bench": bench, "scene": scene,
               "impronta_dichiarata": self.target,
               "fingerprint_seen": fingerprint_seen,
               "eseguibile": self.profile["eseguibile"],
               "spegnimento": self.profile["spegnimento"],
               "idle_scelta": self.profile["idle_scelta"]}
        if extra:
            rec.update(extra)
        return self.write(rec)

    def write(self, rec):
        """⛔ The target, the port and the round go into EVERY line, and this
        function puts them there: a field that four benches must remember to
        add is a field that sooner or later is missing in one of the four."""
        report = {"round": self.round, "target": self.target,
                 "port": self.port, "md5": self.md5, "when": time.time()}
        report.update(rec)
        if not self.fpath:
            self.fault = "no --output: this round leaves no log"
            return False
        try:
            with open(self.fpath, "a") as f:
                f.write(json.dumps(report, ensure_ascii=False) + "\n")
                f.flush()
                os.fsync(f.fileno())
        except OSError as e:
            # ⛔ And it is not kept quiet: a log that cannot be written and one that was not
            #    asked for are two different facts, and the second is the fault of whoever
            #    launches while the first is a disk.
            self.fault = f"the log «{self.fpath}» cannot be written: {e}"
            return False
        self.written += 1
        return True

    def summary(self):
        """The line every bench prints at the end: how many it wrote and where.

        ⛔ With the denominator: "I wrote the log" without a number is
           true even when the lines are zero (`LESSONS.md` §1.9, rule 6 —
           a verdict too has a denominator)."""
        if self.fault:
            return f"⛔ LOG: {self.fault}  ({self.written} lines written)"
        return (f"log of round «{self.round_id}» against «{self.target}»: "
                f"{self.written} lines in {self.fpath}")
