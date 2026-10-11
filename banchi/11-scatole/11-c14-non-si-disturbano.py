#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c14 — ⭐⭐ «THE BOXES DO NOT DISTURB EACH OTHER» — the mesh that looks at THE NET
===========================================================================

    python3 11-c14-non-si-disturbano.py
    python3 11-c14-non-si-disturbano.py --ports-only
    python3 11-c14-non-si-disturbano.py --certify

⛔ Like C11, this mesh **does not test the product**: it tests that the net is worth
   something.  ⭐ And it tests something the phase document so far only
   ASSERTED.

`fasi/11…` §3.4 says the four boxes can run **together**, and it
builds the work plan on it (*«luckily this time development
should be fast because the containers can all four
be active at the same time»*, the user's words).
⇒ ⛔ **An assertion a plan rests on, and that nobody had measured.**
  §4.2: *«§3.4 ASSERTS it; this MEASURES it»*.

---------------------------------------------------------------------------
⭐ THE EXACT QUESTION, and the two parts it splits into
---------------------------------------------------------------------------

    *do the same tests, alone and in parallel, give the same outcome?*

  PART 1 · THE PORTS      ⛔ the declared price of `--network=host`
  PART 2 · THE OUTCOME    ⭐ the same test, alone against in parallel

### PART 1 — and why it is the first

`11-accendi.sh` carries a price written down, with a reference to this mesh inside:

    --network=host   ⚠ it is NOT a choice: `netavark` on this machine cannot
                     apply the network rules.  ⛔ And it has a PRICE:
                     four boxes started together SHARE the host's
                     ports, so each will have to have ITS OWN port —
                     or they will step on each other's toes in a way that looks like a
                     fault of the product.  ⇒ To be reviewed when C14 is done.

⇒ ⭐ **Here we are.**  And the way to measure it is not reading `11-accendi.sh` — that
  is *«written»*, not *«in force»* (E1).  The four servers are started
  **together** and we look at who really listens, and where.

⛔ And the REVERSE is tested too: two boxes on the **same** port.  If
   that does NOT fail, then the separation by port is not a separation,
   and the price was written wrong.

### PART 2 — the same test, alone against in parallel

**C8's test A** is used (`--no-session`), and the choice has three reasons:

  · ⭐ it is the only product mesh that today JUDGES in all four
    boxes: it does not go through the product, so the open defect of phase 10
    §7.4 (`[M]` ten new GNOME sessions out of ten are born blind) does not
    stop it;
  · ⭐⭐ with the injected fault (`--no-fix`) its outcome carries **a
    green AND a red** — `1 si' · 1 no` — that is it is a fingerprint that breaks
    in two different ways.  ⛔ A test that always and only says «green» would be
    a blunt yardstick: if it broke in parallel, how would it say so?
  · it makes the box **really** work: it creates two users, starts a
    browser twice, decodes two images.  ⇒ If the boxes disturb each other, it is
    exactly under this load that it must come out.

---------------------------------------------------------------------------
⛔⛔ THE TWO TRAPS, declared before the numbers
---------------------------------------------------------------------------

1. ⛔ **«?» equal to «?» PASSES the comparison** (`LEZIONI.md` §1.47).  If a
   box answers neither alone nor in parallel, its two fingerprints are
   equal — and a naive comparison would say **green** without having looked at
   anything.  ⇒ Here a box without a fingerprint is **«not judged»**, never
   «equal».

2. ⚠ **The first start of Firefox is slower than the others.**  If one measured
   «alone» first and «together» second, the parallel would start with the
   host's memory already warm ⇒ ⛔ a comparison rigged **in favour** of the
   parallel, that is precisely in the direction in which this mesh could go wrong.
   ⇒ A **warm-up run** is done and THROWN AWAY, and it is declared.

---------------------------------------------------------------------------
⚠ AND TIME IS NOT A VERDICT
---------------------------------------------------------------------------

The parallel **will slow down**: four boxes on a single machine share
the same graphics card and the same processors.  ⛔ **A slowdown is not
a disturbance**, and calling it red would make this mesh red for nothing — that is
it would get it switched off (§1.3).

⇒ ⭐ Time is MEASURED and PRINTED anyway, because it serves whoever writes the
  hook: §5.1 gives it a ceiling of **3 minutes** for the fast family, and
  that ceiling is respected **by cutting tests**, not by raising it.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ alone and in parallel give the same outcome, and the ports do not clash
  1  ⛔ at least one box changes outcome, or two clash on a port ⇒ red
  3  ⛔ I could not look (podman is not there, fewer than two boxes
     gave a fingerprint) — ⛔ and it is NOT a red
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import re
import shlex
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor

# ---------------------------------------------------------------------------
# ⛔ THE THRESHOLDS AND NUMBERS DECLARED HERE, and printed in every outcome: «they do not
#    disturb each other» is a verdict, and a verdict without its yardstick is an opinion.
# ---------------------------------------------------------------------------
DESKTOP = ("gnome", "kde", "xfce", "lxqt")

# ⚠ The ports are NOT invented here: they are the ones `11-accendi.sh` assigns, and
#   this mesh copies them in order to CHECK them.  ⛔ If one day they diverge,
#   the port check would look at ports nobody uses — and that is why
#   test 1.1 checks that the server said it listens exactly there.
PORT = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}

# how long one run of the test is waited for (one only, not all)
CAP_TEST_S = 600
# how long a server is waited for to say it is ready
CAP_SERVER_S = 40
# ⚠ the hook's ceiling, which this mesh does not enforce: it only MEASURES it
CAP_HOOK_S = 180
# ⚠ the ceiling C8 gives itself for one snapshot: it is copied here ONLY to be able to tell
#   the reader where the fixed wait in the times with the injected fault comes from.
#   ⛔ This mesh does not impose it: C8 imposes it, and it is its option
#   `--wait-shot`.
CAP_SHOT_C8_S = 120


# ═══════════════════════════════════════════════════════════════════════════
# THE TOOLS — ⛔ and no nested `sh -c` (`LEZIONI.md` §1.46)
# ═══════════════════════════════════════════════════════════════════════════
def podman(*call_args, cap=120):
    """Calls podman by path, and returns (code, output).

    ⛔ A command nested inside three levels of quotes can get lost along
       the way, **run nothing and return 0** — that is a green with
       no measurement under it.  ⇒ Here the program is called, not a shell.
    """
    try:
        p = subprocess.run(["podman", *call_args], capture_output=True,
                           text=True, timeout=cap)
    except (OSError, subprocess.TimeoutExpired):
        return None, ""
    return p.returncode, (p.stdout or "") + (p.stderr or "")


def inside(box, *command, cap=120):
    """Runs a program INSIDE the box, by absolute path."""
    return podman("exec", box, *command, cap=cap)


def enabled(box):
    c, out = podman("inspect", "-f", "{{.State.Running}}", box, cap=60)
    return c == 0 and out.strip() == "true"


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE FINGERPRINT OF A RUN — what is compared, exactly
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔ The text C8 prints is NOT compared: it would change the fingerprint at every
#    retouch of a sentence, and the mesh would turn red for nothing.
# ⭐ The COUNTS and the EXIT CODE are compared: they are the judgement, and the
#    judgement is what must stay the same.
LINE_A = re.compile(
    r"A · the browser renders the page\s*:\s*(\d+) yes · ⛔ (\d+) no · (\d+) not judged")


def fingerprint(text, code):
    """From the log of a C8 run it extracts the fingerprint of its JUDGEMENT.

    ⛔ Returns **`None`** if the run produced no summary line —
       and `None` is not a fingerprint: it is *«I did not look»*.  ⚠ A run that
       printed nothing is NOT a successful run (`LEZIONI.md` §1.46).
    """
    if not text:
        return None
    m = LINE_A.search(text)
    if not m:
        return None
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), code)


def report_it(imp):
    if imp is None:
        return "I do not know"
    return "%d yes %d no %d unj · exit %s" % imp


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE JUDGE — and the two traps it must dodge
# ═══════════════════════════════════════════════════════════════════════════
def judge(sole, together, how_many_in_parallel=None):
    """Compares the «alone» and «in parallel» fingerprints, box by box.

    Returns:
      `None`   ⛔ I could not look
      list     the boxes that CHANGED outcome (empty = none changed)

    ⛔⛔ `how_many_in_parallel` is how many boxes **TOOK PART** in the run
       together, not how many answered — and the difference is substantial.
       `[M]` The first draft counted those that had answered, and the
       certification rejected it: ⚠ **a box that runs and does not manage to
       report is still occupying the machine.**  ⇒ The load is there all the
       same, and throwing away the others' judgement would be throwing away a
       real measurement.

    The two conditions under which no judgement is made:
      · **fewer than two boxes in the parallel** ⇒ with only one the word
        «parallel» means nothing (same reason why C11 refuses
        to call a single box «aligned»);
      · **no comparable box** ⇒ there is nothing to compare.

    ⛔⛔ And the trap of `LEZIONI.md` §1.47: a box that answered
       **neither alone nor in parallel** has two equal `None`s — and a naive
       comparison would say «equal».  ⇒ Here it is not equal: it is **not judged**, and
       it enters neither among the greens nor among the reds.
    """
    names = sorted(set(sole) | set(together))
    if how_many_in_parallel is None:
        how_many_in_parallel = len(together)
    judgeable = [n for n in names
                   if sole.get(n) is not None and together.get(n) is not None]
    if how_many_in_parallel < 2 or not judgeable:
        return None
    return [n for n in judgeable if sole[n] != together[n]]


def unjudged(sole, together):
    names = sorted(set(sole) | set(together))
    return [n for n in names
            if sole.get(n) is None or together.get(n) is None]


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CERTIFICATION — we prove that the judge CAN give red
# ═══════════════════════════════════════════════════════════════════════════
def certify():
    """⚠ And we declare what it covers and what not.

    IT COVERS: the comparison between fingerprints — that a difference is seen, that
    equality is green, ⛔ that a silent box is «I do not know» and not
    «equal», and that a single box does not pass for a parallel.
    ⛔ IT DOES NOT COVER: that the boxes really disturb each other.  That is said by the
    run on the real thing, and the ports test in part 1.
    """
    U = (2, 0, 0, 0)          # the outcome with the cure:   2 yes, 0 no
    G = (1, 1, 0, 0)          # the outcome with the fault:  1 yes, 1 no
    cases = [
        ("two boxes, same outcome alone and together",
         {"a": G, "b": G}, {"a": G, "b": G}, 0),
        ("⭐ one box changes outcome in parallel",
         {"a": G, "b": G}, {"a": G, "b": U}, 1),
        ("both change",
         {"a": G, "b": G}, {"a": U, "b": U}, 2),
        ("⛔ only the exit CODE changes: it is a different judgement",
         {"a": G, "b": G}, {"a": G, "b": (1, 1, 0, 1)}, 1),
        ("one box did not answer ALONE ⇒ not judged, not equal",
         {"a": G, "b": None}, {"a": G, "b": G}, 0),
        ("⭐ a single comparable one IS ENOUGH: the other made load all the same",
         {"a": G, "b": None, "c": None}, {"a": G, "b": None, "c": None}, 0),
        ("⛔ and if that comparable one CHANGES, it is red even so",
         {"a": G, "b": None}, {"a": U, "b": None}, 1),
        ("⛔ a single box is not a parallel",
         {"a": G}, {"a": G}, None),
        ("⛔ no box answered ⇒ nothing to compare",
         {"a": None, "b": None}, {"a": None, "b": None}, None),
        ("three agreeing and one silent: the three are judged",
         {"a": G, "b": G, "c": G, "d": None},
         {"a": G, "b": G, "c": G, "d": None}, 0),
    ]
    print("== certification of the C14 judge ==")
    print("   fingerprint = (how many yes, how many no, how many not judged, exit code)")
    print("   ⛔ and a run without a summary line is NOT a fingerprint: it is «I do not know»\n")
    troubles = 0
    for name, sole, ins, expected in cases:
        r = judge(sole, ins)
        got_n = None if r is None else len(r)
        ok = got_n == expected
        print("  %s  %-62s  changed=%s (expected %s)"
              % ("OK " if ok else "NO ", name,
                 "I do not know" if got_n is None else got_n,
                 "I do not know" if expected is None else expected))
        if not ok:
            troubles += 1

    # ⛔ And the fingerprint reader is certified separately: it is the one that decides whether
    #    a run «spoke».  A reader that returned (0,0,0) instead of None
    #    on a silent log would turn «I did not look» into «zero», which is
    #    wound number one of this project.
    print()
    readings = [
        ("a real summary",
         "  A · the browser renders the page      : 1 yes · ⛔ 1 no · 0 not judged\n",
         0, (1, 1, 0, 0)),
        ("a summary with some not judged",
         "  A · the browser renders the page      : 0 yes · ⛔ 0 no · 2 not judged\n",
         3, (0, 0, 2, 3)),
        ("⛔ SILENT log ⇒ None, not (0,0,0)", "", 0, None),
        ("⛔ log that talks about something else ⇒ None",
         "podman: command not found\n", 127, None),
        ("⚠ the B line alone is not enough: A is looked at",
         "  B · and the page shows FROM THE CLIENT: 0 yes · ⛔ 0 no · 2 not judged\n",
         0, None),
    ]
    for name, text, code, expected in readings:
        got = fingerprint(text, code)
        ok = got == expected
        print("  %s  %-62s  read=%s" % ("OK " if ok else "NO ", name, report_it(got)))
        if not ok:
            troubles += 1

    print()
    if troubles:
        print("⛔ the judge is NOT reliable: %d wrong cases" % troubles)
        return 1
    print("⭐ the judge sees the change of outcome, says green when there is none,")
    print("   ⛔ and does not mistake «I did not look» for «equal»")
    print("⚠ and this certification covers THE COMPARISON, not the boxes (see above)")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
# PART 1 — THE PORTS: the price of `--network=host`, put to the test
# ═══════════════════════════════════════════════════════════════════════════
def turn_off_server(box):
    inside(box, "/usr/bin/systemctl", "stop", "rete11-server", cap=90)
    inside(box, "/usr/bin/systemctl", "reset-failed", "rete11-server", cap=60)
    inside(box, "/bin/rm", "-f", "/var/lib/rete11/registro.log", cap=60)


def turn_on_server(box, port):
    """Starts the server inside the box on the given port.

    ⛔ The line is the one of `11-accendi.sh server`, copied piece by piece
       as ARGUMENTS: no shell in between.
    """
    turn_off_server(box)
    inside(box, "/bin/mkdir", "-p", "/var/lib/rete11/certificati",
           "/var/lib/rete11/rilievo", cap=60)
    return inside(
        box, "/usr/bin/systemd-run", "--unit=rete11-server",
        "--working-directory=/opt/remotix",
        "--property=StandardOutput=append:/var/lib/rete11/registro.log",
        "--property=StandardError=append:/var/lib/rete11/registro.log",
        "--property=KillMode=mixed",
        "/opt/remotix/remotix", "--address", "0.0.0.0", "--name", "127.0.0.1",
        "--port", str(port),
        "--certificates", "/var/lib/rete11/certificati",
        "--page", "/opt/remotix/pagina.html",
        "--ban-file", "/var/lib/rete11/ban",
        "--command-socket", "/var/lib/rete11/command.sock",
        "--survey", "/var/lib/rete11/rilievo", "--verbose", cap=90)


def wait_ready(box, cap=CAP_SERVER_S):
    """⛔ «On» means SOMEONE LISTENING, not «the process exists».

    Lesson of phase 10 §1.36: a server with a live process and nobody
    listening passed for on.  ⇒ We wait for the line that says so, and if it does not
    arrive we return the REASON, not a silence.
    """
    expiry = time.time() + cap
    while time.time() < expiry:
        c, out = inside(box, "/bin/grep", "-c", "ready: https",
                        "/var/lib/rete11/registro.log", cap=60)
        if c == 0 and out.strip().isdigit() and int(out.strip()) > 0:
            return True, ""
        time.sleep(1.0)
    _c, queue = inside(box, "/usr/bin/tail", "-4",
                      "/var/lib/rete11/registro.log", cap=60)
    return False, (queue or "(empty log)").strip().replace("\n", " ")[:200]


def bind_refusal(box, port):
    """⛔ The REASON why the server did not start, not only the fact.

    ⚠⚠ And this function was born from a finding about myself.  The first draft
       of 1.3 was content with *«the intruder did not say it was ready within
       20 seconds»* — ⛔ which is **weak**: a slow server, or one stopped for
       any other reason, would have produced the same silence, and the bench
       would have written «⭐ the separation works» **with no measurement
       under it**.  ⇒ It is the error shape of `LEZIONI.md` §1.46, seen from the
       side of the green.

    ⭐ Now TWO things are demanded together:
       · the server unit must be in `failed` — not «starting»;
       · in the log there must be the line that says **why**:
         `[M]` `⛔ cannot bind to 0.0.0.0:8511 over UDP: Address already in use`.

    Returns (stato, riga) where `stato` is:
       "rifiutato"  ⭐ it stopped AND said the port was taken
       "still"      ⚠ it stopped, but for a reason that is not the port
       "vivo"       ⛔ it did not stop at all
    """
    _c, active = inside(box, "/usr/bin/systemctl", "is-active",
                        "rete11-server", cap=60)
    _c2, queue = inside(box, "/bin/grep", "-F", "cannot bind to",
                       "/var/lib/rete11/registro.log", cap=60)
    line = (queue or "").strip().splitlines()
    line = line[-1].strip() if line else ""
    busy = ("Address already in use" in line) and (":%d" % port in line)
    if (active or "").strip() not in ("failed", "inactive"):
        return "vivo", line
    return ("rifiutato" if busy else "still"), line


def who_listens(box, port):
    """Who holds the port, seen FROM INSIDE this box.

    ⭐ With `--network=host` the boxes share the host's network, so
      `ss` inside a box sees ALL the host's ports.  ⛔ But it can resolve the
      process name only for the processes of its OWN tree:
      for the others it sees the socket and not the owner.
    ⇒ It is exactly the discriminant needed: *«is this port MINE?»*
    """
    c, out = inside(box, "/usr/bin/ss", "-ltnp", "sport", "=", ":%d" % port,
                    cap=60)
    if c != 0:
        return None
    lines = [r for r in out.splitlines() if ":%d" % port in r]
    if not lines:
        return "none"
    return "mine" if "users:((" in lines[0] else "someone else's"


# ═══════════════════════════════════════════════════════════════════════════
# PART 2 — THE TEST, alone and in parallel
# ═══════════════════════════════════════════════════════════════════════════
def one_round(box, a, fault=None):
    """One run of C8's test A inside a box. Returns (fingerprint, seconds)."""
    t0 = time.time()
    if fault is None:
        fault = a.fault
    call_args = ["python3", "-u", a.test, "--no-session",
                 "--page", a.page]
    if fault:
        call_args.append("--no-fix")
    # ⭐ And arguments can be passed to the test, ⛔ and it serves one thing only:
    #    **trying to refute itself**.  See `--pass-args` further down.
    call_args.extend(shlex.split(a.pass_args))
    c, out = inside(box, *call_args, cap=a.test_cap)
    return fingerprint(out, c), time.time() - t0


def solo_round(boxes, a, fault=None):
    """One box at a time. ⛔ It is the starting line: if this does not speak,
       there is nothing to compare."""
    outcomes, times = {}, {}
    for s in boxes:
        imp, sec = one_round(s, a, fault)
        outcomes[s], times[s] = imp, sec
        print("     %-14s  %-34s  %6.1f s" % (s, report_it(imp), sec))
    return outcomes, times


def round_together(boxes, a, fault=None):
    """All together, really: they are launched and then waited for.

    ⚠ `ThreadPoolExecutor` with as many slots as there are boxes: if it had
      fewer, the last ones would start **after** the first ones — and it would not be a
      parallel, it would be a queue with an ambitious name.
    """
    outcomes, times = {}, {}
    with ThreadPoolExecutor(max_workers=len(boxes)) as pool:
        future = {s: pool.submit(one_round, s, a, fault) for s in boxes}
        for s in boxes:
            imp, sec = future[s].result()
            outcomes[s], times[s] = imp, sec
    for s in boxes:
        print("     %-14s  %-34s  %6.1f s" % (s, report_it(outcomes[s]), times[s]))
    return outcomes, times


# ═══════════════════════════════════════════════════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════
# PART 1-bis — THE GRAPHICS CARD, the only thing they REALLY share
# ═══════════════════════════════════════════════════════════════════════════
#
# ⛔⛔ AND THIS IS THE PART THAT WAS MISSING, and it must be said why it was missing.
#
# Part 2 runs C8's test A, which starts a browser WITHOUT a screen:
# `[M]` its log says `RenderCompositorSWGL`, that is ⛔ **it draws in
# software and does not touch the graphics card**.  ⇒ A parallel that does not touch the
# card cannot say anything about who contends for it.
#
# ⚠ And the real contention — four encoders together on the same node — today
#   **cannot be measured**: it would need a live session per box, and
#   `[M]` ten new GNOME sessions out of ten are born blind (phase 10 §7.4).
#   ⇒ What can be measured now is the layer below, which is anyway
#     the question that would come first: **can four boxes OPEN the
#     encoder at the same instant?**  If even this does not hold, the
#     real contention does not even need to be tested.
def look_card(box):
    """Asks the node how many H.264 encoding profiles it exposes.

    ⛔ Returns `None` if it could not look — and `None` is not zero: *«I did not
       ask»* and *«it answered zero profiles»* are two different faults, and the
       second is much worse than the first.
    """
    c, out = inside(box, "/usr/bin/vainfo", cap=90)
    if c is None or not out:
        return None
    n = len([r for r in out.splitlines()
             if "VAProfileH264" in r and "EncSlice" in r])
    if "Driver version" not in out:
        return None
    return n


def part_card(boxes):
    """Returns (guai, ignoti). ⭐ Alone and together, like everything else."""
    troubles, unknown = [], []
    print("== PART 1-bis — the graphics card, alone and with all %d together =="
          % len(boxes))
    print("   ⛔ it is the ONLY thing the four boxes really share:")
    print("      a single node, `/dev/dri/renderD128`, passed inside all of them")
    print()
    sole = {}
    for s in boxes:
        sole[s] = look_card(s)
    with ThreadPoolExecutor(max_workers=len(boxes)) as pool:
        future = {s: pool.submit(look_card, s) for s in boxes}
        together = {s: future[s].result() for s in boxes}
    for s in boxes:
        q, i = sole[s], together[s]
        sign = "  "
        if q is None or i is None:
            sign = "⚠"
        elif q != i:
            sign = "⛔"
        print("   %s %-14s  alone: %-12s  together: %s"
              % (sign, s,
                 "I do not know" if q is None else "%d profiles" % q,
                 "I do not know" if i is None else "%d profiles" % i))
        if q is None or i is None:
            unknown.append("%s did not say what it sees on the card" % s)
        elif q != i:
            troubles.append("%s sees %d profiles alone and %d with the others on: "
                        "⛔ the card does not hold four boxes together"
                        % (s, q, i))
        elif i == 0:
            # ⛔ Zero profiles in both is not «equal, so fine»:
            #    it is a card that does not encode.  ⚠ Equal to itself and
            #    wrong stays wrong (`LEZIONI.md` §1.47).
            troubles.append("%s sees NO encoding profile, neither alone nor "
                        "together: the comparison is «equal» and the terrain is "
                        "broken" % s)
    return troubles, unknown


def part_ports(boxes, a):
    """Returns (troubles, unknown) — two lists of sentences, empty if everything holds.

    ⛔ `unknown` is not `troubles`: it is *«I could not look»*, and for §4.5 it is not
       a red — but **it is not a green either**, and that is why it is in
       a list of its own instead of being kept quiet.
    """
    troubles, unknown = [], []
    print("== PART 1 — the ports: the price of `--network=host` ==")
    print("   ⛔ `11-accendi.sh` is not read: the servers are started and we look at")
    print("      who really listens (E1: «written is not in force»)\n")

    # ── 1.1 · the four servers, together, each on its own port ─────────────
    print("   1.1 · the servers started TOGETHER, each on its own port")
    with ThreadPoolExecutor(max_workers=len(boxes)) as pool:
        list(pool.map(lambda s: turn_on_server(s, PORT[s.split("-")[-1]]),
                      boxes))
    ready = {}
    for s in boxes:
        ok, why = wait_ready(s)
        ready[s] = ok
        print("       %-14s port %-5d  %s" % (
            s, PORT[s.split("-")[-1]],
            "⭐ listens" if ok else "⛔ did not say it was ready: %s" % why))
    if not all(ready.values()):
        troubles.append("at least one server could not listen while the "
                    "others were on")

    # ── 1.2 · and every port belongs to WHOM IT SHOULD ────────────────────
    # ⭐ It is not enough that four ports are taken: 8512 must belong to
    #   KDE and not to GNOME.  Otherwise a client that believes it is talking to one
    #   desktop would talk to another — ⛔ and it would be a fault disguised as a
    #   fault of the product.
    print("\n   1.2 · and every port belongs to the right box")
    for s in boxes:
        my = who_listens(s, PORT[s.split("-")[-1]])
        others = [who_listens(s, PORT[t.split("-")[-1]])
                  for t in boxes if t != s]
        ok = (my == "mine") and all(x in ("someone else's", "none", None)
                                    for x in others)
        print("       %-14s its own: %-12s  the others: %s"
              % (s, my, ", ".join(str(x) for x in others)))
        if my != "mine":
            troubles.append("%s does not recognise port %d as its own"
                        % (s, PORT[s.split("-")[-1]]))

    # ── 1.3 · ⛔ THE REVERSE: two boxes on the SAME port ───────────────────
    # ⛔ It is the test that is worth more than the other two: if putting two servers on the
    #   same port did NOT hurt, then «one port per box» would not
    #   separate anything, and the price written in `11-accendi.sh` would be a
    #   reassurance with no measurement under it.
    print("\n   1.3 · ⛔ the reverse: two boxes on the SAME port")
    if len(boxes) < 2:
        print("       ⚠ fewer than two boxes: I cannot test it")
    else:
        victim, intruder = boxes[0], boxes[1]
        contended_port = PORT[victim.split("-")[-1]]
        turn_off_server(intruder)
        turn_on_server(intruder, contended_port)
        ok, _why = wait_ready(intruder, cap=20)
        state, line = bind_refusal(intruder, contended_port)
        if ok or state == "vivo":
            print("       ⛔⛔ %s took %d, which was %s's"
                  % (intruder, contended_port, victim))
            troubles.append("two boxes can take the same port without "
                        "anyone noticing: ⛔ the separation by port "
                        "does NOT separate")
        elif state == "rifiutato":
            print("       ⭐ %s could NOT take %d (%s's), and it"
                  % (intruder, contended_port, victim))
            print("          said WHY:")
            print("          %s" % line[:150])
            print("       ⭐ ⇒ the separation by port is a REAL separation:")
            print("          the price of `--network=host` is written right")
        else:
            # ⛔ It stopped, but not because of the port.  ⚠ Calling it green would be
            #    celebrating a silence: I have no proof that it was the port.
            print("       ⚠ %s did not start, ⛔ but it did NOT say the port was"
                  % intruder)
            print("          taken ⇒ I do not know whether the port stopped it.")
            print("          log: %s" % (line[:150] or "(no «cannot bind to» line)"))
            unknown.append("I have no proof that the port prevents the "
                          "intrusion: the intruder stopped without saying so")
        # ⚠ And things are put back, or part 2 would start from dirty terrain.
        turn_off_server(intruder)
        turn_on_server(intruder, PORT[intruder.split("-")[-1]])
        restored, _ = wait_ready(intruder)
        if not restored:
            unknown.append("after the intrusion test %s did not go back to "
                          "listening on its port" % intruder)
        else:
            print("       ⭐ and %s went back to its port %d"
                  % (intruder, PORT[intruder.split("-")[-1]]))
    return troubles, unknown


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--desktop", default=",".join(DESKTOP))
    p.add_argument("--prefix", default="rete11-")
    p.add_argument("--test",
                   default="/rete11/11-c8-il-secondo-apre-il-browser.py",
                   help="the test that is run alone and in parallel")
    p.add_argument("--page", default="/rete11/11-c8-pagina.html")
    p.add_argument("--fault", action="store_true", default=True,
                   help="uses C8 with the injected fault: ⭐ its outcome carries "
                        "a green AND a red, that is it is a fingerprint that "
                        "can break in two ways")
    p.add_argument("--no-fault", dest="fault", action="store_false")
    p.add_argument("--test-cap", type=int, default=CAP_TEST_S)
    p.add_argument("--no-warmup", action="store_true",
                   help="⛔ skips the run that is thrown away. ⚠ Only for diagnosis: "
                        "without it, the parallel starts with memory already warm")
    # ⚠ ONE STRING ONLY, and not `nargs="*"`: `[M]` with `nargs` argparse
    #   stops at the first argument that starts with `--` and refuses it as its
    #   own.  ⇒ It is passed in quotes and split here.
    p.add_argument("--pass-args", default="", metavar="\"--a 1 --b 2\"",
                   help="⭐ arguments to hand to the test, in quotes. "
                        "⛔ It is not a convenience: it serves to TRY TO REFUTE ITSELF. "
                        "With a tight ceiling (`--pass-args \"--wait-shot 3\"`) "
                        "the contention becomes decisive, and one sees whether this bench "
                        "can notice it")
    p.add_argument("--refute", action="store_true",
                   help="⛔⛔ THE COUNTER-TEST ON REAL DATA: runs the "
                        "parallel with C8's OTHER mode, so the two "
                        "fingerprints must be different. ⭐ This mesh MUST "
                        "turn RED; if it stays green it cannot see a "
                        "change of outcome, and every green of it is worth nothing")
    p.add_argument("--ports-only", action="store_true",
                   help="only the graphics card and the ports, without the long run")
    p.add_argument("--outcome-only", action="store_true")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()

    if a.certify:
        sys.exit(certify())

    try:
        subprocess.run(["podman", "--version"], capture_output=True, timeout=30)
    except OSError:
        print("⛔ podman is not there: ⇒ I could not look")
        sys.exit(3)

    names = [a.prefix + d for d in a.desktop.split(",") if d]
    boxes = [n for n in names if enabled(n)]

    print("== C14 — do the boxes disturb each other? ==")
    print("   ⭐ §3.4 ASSERTS it; this mesh MEASURES it (§4.2)")
    print("   test: %s%s%s" % (
        a.test.split("/")[-1],
        "  --no-fix (injected fault)" if a.fault else "",
        ("  " + a.pass_args) if a.pass_args else ""))
    print("   declared ceilings: one run %d s · a server ready %d s"
          % (a.test_cap, CAP_SERVER_S))
    print("   ⚠ time is NOT a verdict: it is measured and printed, and that is all\n")
    for n in names:
        print("   %-14s %s" % (n, "on" if n in boxes else "⛔ off"))
    print()
    if len(boxes) < 2:
        print("⛔ boxes on: %d — ⭐ and with ONE ONLY the word «parallel»"
              % len(boxes))
        print("   means nothing.  ⇒ I could not look")
        sys.exit(3)

    port_troubles, unknown_ports = [], []
    if not a.outcome_only:
        g1, i1 = part_card(boxes)
        print()
        g2, i2 = part_ports(boxes, a)
        port_troubles, unknown_ports = g1 + g2, i1 + i2
        print()

    if a.ports_only:
        if port_troubles:
            print("⛔⛔ RED — the ports clash:")
            for g in port_troubles:
                print("   · %s" % g)
            return 1
        if unknown_ports:
            print("⛔ I could not look all the way:")
            for g in unknown_ports:
                print("   · %s" % g)
            return 3
        print("⭐ the card holds four boxes together, and the ports do not")
        print("   clash: each belongs to its box, and two cannot")
        print("   take the same one")
        return 0

    # ═══ PART 2 ════════════════════════════════════════════════════════════
    print("== PART 2 — the same test, alone and in parallel ==")
    if not a.no_warmup:
        # ⛔ THE RUN THAT IS THROWN AWAY, and it must be declared why it is thrown away.
        #    The first start of Firefox is slower: without this run, the
        #    parallel would start with the host's memory warm ⇒ ⛔ a
        #    comparison rigged **in favour** of the parallel, that is precisely in the
        #    direction in which this mesh could go wrong.
        print("\n   0 · WARM-UP run, and it is THROWN AWAY")
        print("       (the first start of the browser is slower: without it, the")
        print("        parallel would start with an advantage)")
        t0 = time.time()
        round_together(boxes, a)
        print("       thrown away, %.1f s\n" % (time.time() - t0))

    print("   1 · ALONE, one at a time")
    t0 = time.time()
    sole, times_only = solo_round(boxes, a)
    tot_sole = time.time() - t0
    print("       total: %.1f s\n" % tot_sole)

    print("   2 · TOGETHER, all %d%s"
          % (len(boxes),
             "   ⛔⛔ WITH THE TEST CHANGED ON PURPOSE (--refute)"
             if a.refute else ""))
    t0 = time.time()
    # ⛔⛔ `--refute` MAKES THE TEST CHANGE between the two arrangements.
    #
    # ⭐ It is the counter-test `--certify` CANNOT give: the certification
    #    works on FAKE cases, and proves that the comparison can see a
    #    difference **when it is put in its hands**.  ⛔ It does not prove that the
    #    real chain — `podman exec`, reading the log, the comparison —
    #    can produce a red on REAL data.
    # ⇒ With `--refute` the «together» arrangement runs with C8's other
    #   mode, so the two fingerprints MUST be different and this mesh MUST
    #   turn red.  ⚠ If it stays green, it is not able to see a change of
    #   outcome, and every previous green of it is worth nothing.
    together, times_set = round_together(
        boxes, a, fault=(not a.fault) if a.refute else None)
    tot_ins = time.time() - t0
    print("       total: %.1f s\n" % tot_ins)

    # ── the comparison ────────────────────────────────────────────────────
    print("   ⭐ THE COMPARISON — fingerprint = (yes, no, not judged, exit)")
    print("     %-14s  %-30s  %-30s" % ("box", "alone", "together"))
    for s in boxes:
        eq_sign = (sole.get(s) is not None and together.get(s) is not None
                  and sole[s] == together[s])
        gone_mute = sole.get(s) is None or together.get(s) is None
        sign = "⚠" if gone_mute else ("  " if eq_sign else "⛔")
        print("   %s %-14s  %-30s  %-30s" % (sign, s, report_it(sole.get(s)),
                                             report_it(together.get(s))))
    print()

    # ── the time, which is NOT a verdict ──────────────────────────────────
    print("   ⚠ THE TIME (information, not a verdict)")
    if a.fault:
        # ⛔⛔ AND HERE THE NUMBER MUST BE READ WITH A RESERVATION, or it deceives.
        #
        # `[M]` 26 August 2026, warm-up run: four boxes together
        # took **125,9 · 126,0 · 126,0 · 126,1 s**.  ⚠ Four numbers
        # equal to a tenth are not chance: ⛔ with the injected fault the
        # SECOND tenant does not open the browser, and C8 waits for it for its
        # declared ceiling — which today is **120 s**.
        # ⇒ ⛔ **The time of this run is almost all a FIXED WAIT**, not
        #   work: adding a «×how much it slows down» on top would mean measuring
        #   our own ceiling and calling it contention.
        # ⭐ The clean time is taken with `--no-fault`, where both
        #   tenants succeed and nobody waits for a ceiling.
        print("     ⛔ RESERVATION: with the injected fault the second tenant does NOT open")
        print("        the browser, and C8 waits for it for its ceiling (%d s)."
              % CAP_SHOT_C8_S)
        print("        ⇒ these times are almost all FIXED WAIT, not work.")
        print("        ⭐ The clean time is taken with `--no-fault`.")
    slowest = max((times_set[s] for s in boxes), default=0)
    slowest_alone = max((times_only[s] for s in boxes), default=0)
    for s in boxes:
        q = times_only[s]
        i = times_set[s]
        print("     %-14s  alone %6.1f s   together %6.1f s   %s"
              % (s, q, i, ("×%.2f" % (i / q)) if q > 0 else "?"))
    print("     %-14s  alone %6.1f s   together %6.1f s"
          % ("ALL", tot_sole, tot_ins))
    if tot_ins > 0:
        print("     ⭐ the parallel saves ×%.2f on the total" % (tot_sole / tot_ins))
    print("     ⚠ the slowest in parallel: %.1f s (alone the slowest: %.1f s)"
          % (slowest, slowest_alone))
    # ⚠ And the reference to the hook: it is the only place where this number is needed.
    print("     ⇒ the hook (§5.1) has a ceiling of %d s for the fast family: "
          "this run %s"
          % (CAP_HOOK_S,
             "fits inside it" if slowest <= CAP_HOOK_S else
             "⛔ does NOT fit inside it ⇒ tests are cut, the ceiling is not raised"))
    print()

    # ── the verdict ───────────────────────────────────────────────────────
    r = judge(sole, together, how_many_in_parallel=len(boxes))
    mute = unjudged(sole, together)
    if mute:
        print("⚠ ⛔ %d boxes not judged — and a silent box is NOT «equal»"
              % len(mute))
        for s in mute:
            print("     · %-14s  alone: %-18s  together: %s"
                  % (s, report_it(sole.get(s)), report_it(together.get(s))))
        print("   ⇒ `LEZIONI.md` §1.47: «?» equal to «?» would pass the comparison")
        print("     without having looked at anything.\n")

    if unknown_ports:
        print("⚠ ⛔ and on the ports I could not look all the way:")
        for g in unknown_ports:
            print("     · %s" % g)
        print()
    if r is None:
        print("⛔ there is not enough to compare: either the parallel had fewer")
        print("   than two boxes, or none is comparable.")
        print("   ⇒ I could not look")
        return 3
    if a.refute:
        # ⛔ With the test changed on purpose the outcome READS THE OTHER WAY ROUND: here
        #    green is a failure of the bench.
        print()
        if r:
            print("⭐ THE COUNTER-TEST SUCCEEDED: with the test changed on purpose")
            print("   this mesh turned red on %d boxes out of %d."
                  % (len(r), len(boxes)))
            print("   ⇒ it can see a change of outcome on REAL data, not only in the")
            print("     fake cases of `--certify`")
            return 0
        print("⛔⛔ THE COUNTER-TEST FAILED: the two fingerprints had to be")
        print("    different and this mesh did not notice.")
        print("    ⇒ every previous green of it is worth nothing.")
        return 1
    if r or port_troubles:
        print("⛔⛔ RED — the boxes disturb each other:")
        for s in r:
            print("   · %-14s alone %s   ⇒   together %s"
                  % (s, report_it(sole[s]), report_it(together[s])))
        for g in port_troubles:
            print("   · %s" % g)
        print()
        print("   ⇒ as long as it is like this, ⛔ **running the four boxes together")
        print("     is not a saving: it is a way of getting false numbers**")
        print("     (§3.4, which this mesh exists to put to the test).")
        return 1
    compared = [s for s in boxes if s not in mute]
    print("⭐ the %d compared boxes give THE SAME outcome alone and in parallel,"
          % len(compared))
    print("   and the ports do not clash.")
    if mute:
        # ⛔ AND HERE GREEN IS NOT SAID, and the reason is in §4.5: `3` means
        #    *«I measured, and some piece could not speak»*.  ⚠ Saying
        #    `0` with three boxes out of four silent would pass off a
        #    PARTIAL answer as a full one.
        print("⛔ but %d boxes out of %d did not speak: the answer is PARTIAL."
              % (len(mute), len(boxes)))
        print("   ⇒ I do not judge (§4.5, outcome 3)")
        return 3
    if unknown_ports:
        print("⛔ but on the ports something I could not look at ⇒ I do not judge")
        return 3
    print("⚠ ⇒ §3.4 is no longer an assertion: it is `[M]`.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
