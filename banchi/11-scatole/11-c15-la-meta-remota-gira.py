#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c15 — ⭐⭐ «THE REMOTE HALF REALLY RUNS» — the mesh that looks at THE NET
===========================================================================

    python3 11-c15-la-meta-remota-gira.py
    python3 11-c15-la-meta-remota-gira.py --certify
    python3 11-c15-la-meta-remota-gira.py --last 40 --days 3

⛔ Like C11-C14, this mesh **does not test the product**.  It does not even test the
   net: it tests that the half of the net **that counts** is still running.

---------------------------------------------------------------------------
⛔⛔ THE FAULT IT CATCHES — *C12, moved by one machine*
---------------------------------------------------------------------------

Since `DECISIONI.md` §4.6-novemdecies the hook has **two halves on two machines**:
it **decides** on the laptop (where the git repository is) and **runs** on the
test machine (where the boxes and the graphics card are).

⇒ ⛔⛔ And since that day there is a hole that none of the four meshes of the net
  can see: **if the test machine were switched off for ever, C12 and C13
  would stay GREEN.**

Here is how, step by step, and it is not a hypothesis — they are lines that are in
today's log:

  · the `pre-push` calls `remoto`; the remote half does not answer and counts as **3**
    («I could not look»), and ⭐ **by declared choice it does not block the push**;
  · the laptop half runs anyway: C10, C12, C13 and ⭐ C10's injected
    fault, `[M]` one second in all;
  · **C12** looks at the last non-dry run and finds it from a minute ago ⇒ green:
    *«the hook is alive»*.  ⚠ And it tells the truth;
  · **C13** finds, in that run, an injected fault **seen** — C10's one,
    which runs on the repository and does not need any box ⇒ green: *«the net
    can still give red»*.  ⚠ And it tells the truth too.

⇒ ⛔⛔ **Both tell the truth, and together they tell a lie**: the meshes
  that look at the product — those that start a session inside a
  box — ⛔ **might not have run for weeks, and no red line would
  say so.**  ⚠ It is exactly the fault C12 exists to catch — *«the
  hook switched off silently»*, `fasi/11…` §4.2 — except that the hook is not
  switched off: it is **halved**.

⭐ And §5.2 already had the right rule and nobody enforcing it:

      *«the single 3 is neutral; ⛔ a FREQUENT 3 is a fault of the bench, not
        an outcome.»*

⇒ ⭐⭐ **C15 is the mesh that turns «a frequent 3» into a red line.**
  Today's 3 blocks nothing (and must not: a hook that stops the work
  because a second machine does not answer is a hook that someone
  uninstalls).  ⛔ Eight days of 3 in a row are something else, and from here on
  they have a colour.

---------------------------------------------------------------------------
⭐⭐ HOW A RUN «EXECUTED ON THE BOXES» IS RECOGNISED — ⛔ and not by the name
    of the machine
---------------------------------------------------------------------------

The temptation was to read the `dove` field (the `hostname`) and look for the one of the
test machine.  ⛔ **Discarded**, and for two reasons that are the same:

  1. it would be a name pinned inside a mesh — the day the test machine
     changes name, or a second one appears, C15 would say red for ever:
     `LEZIONI.md` §1.49, *«a red that cannot be turned green is worse
     than no mesh»*;
  2. ⛔ and above all **it would not measure the right thing**: that a line was
     written on that machine does not say that something was *measured* there.

⇒ ⭐ The sign is taken **inside the run**, and it is a property that cannot be
  faked: **a mesh that needs a box, and that reached a
  JUDGEMENT** (outcome 0 or 1, not 3).

⛔ And the «not 3» is half of this mesh's job.  `[M]` from today's
   log: **C11 exits 0 where the boxes are (26 Aug 2026, 11 s) and 3 where they
   are not** (four runs on the laptop, 0-1 s).  ⇒ A judgement from C11 is a proof
   that the boxes were there; a 3 from C11 is the proof of the contrary.

---------------------------------------------------------------------------
⛔ AND «THE REMOTE HALF IS GREEN» DOES NOT COUNT — the nearest trap
---------------------------------------------------------------------------

`11-gancio.sh` writes in every `remote` run an annotation called **«la
meta remota»**, with outcome 0 when the delegation worked.  ⚠ It looks made
on purpose for this mesh, ⛔ **and it is not**:

`[M]` log line of 27 August 2026, 07:30 — `"dry": true`, and inside
`{"name":"la meta remota","outcome":0,…,"note":"la meta' remota e' verde"}`.
⇒ ⛔ **A DRY run in which the delegation went well and nothing was
  measured.**  That annotation says that ssh and systemd
  worked, not that a box started.

⇒ ⭐ C15 **ignores it completely**, and that case is inside `--certify`.

---------------------------------------------------------------------------
⭐ THE THREE QUESTIONS — and only two judge
---------------------------------------------------------------------------

  1 ⭐ **In the window is there at least one run executed on the boxes?**
      ⇒ otherwise RED.  It is the question this mesh exists for.

  2 ⭐ **Did that run start the product inside a box, or did it stop at
      the zero-cost ones?**
      ⇒ otherwise RED.  ⚠ The boxes can answer `dpkg` (C11) and
        be the shadow of themselves: if nobody starts a session inside them,
        the graphics card — ⛔ the reason boxes are used and not
        virtual machines (D1) — has not been touched by anybody.

  3 ⚠ **How many boxes answered?**  ⛔ **It is PRINTED, not judged**, and the
      reason must be written or someone will turn it into a red: the fast
      family looks at **GNOME only by declared choice** (`11-gancio.sh`,
      `for d in gnome`).  ⇒ Demanding four boxes would mean a
      perpetual red for a decision taken on purpose: `LEZIONI.md` §1.49.
      ⚠ Here it said *«today the product can start only one desktop»*:
      ⛔ it is no longer true — `[R]` 21 Sep 2026 it starts three (gnome, kde,
      xfce; `11-capacita-del-prodotto.sh`).  ⭐ The count stays information
      anyway, for the reason above: the fast family looks at gnome and
      that is all.  Making it a judgement is a decision, and it has not been taken.

---------------------------------------------------------------------------
⚠⚠ THE YARDSTICK, and **where it comes from** — ⛔ neither of the two numbers is mine
---------------------------------------------------------------------------

    window     `[R]` **last 20 real runs** — taken from C13 (`DEFAULT_LAST_N`)
    threshold  `[R]` **7 days**            — taken from C12 (`DEFAULT_DAYS`)

⭐ **I did not choose them different on purpose, and the two reasons are different.**

  · The **window** is C13's because C13 and C15 read **the same
    memory** and must look at **the same slice**.  ⛔ Two different windows
    would mean two meshes talking about two different «nows», and nobody
    reading would know which of the two is looking at the present.
  · The **threshold** is C12's because ⭐ **the fault is the same, moved
    by one machine**.  ⛔ Two different thresholds for the same fault would
    mean that at least one of the two is arbitrary.

⛔⛔ **And at the origin both are `[?]`, and it must be said instead of inherited
    silently.**  C12 writes it about itself: *«chosen, not measured: nobody has yet
    observed how often this repository is touched»*.  ⇒ By inheriting the
    numbers I also inherit the question mark.

⇒ ⭐ **The measurement that would be needed, and that today is NOT there**: how often the test
  machine is really run.  `[M]` today's log has **24
  lines** and **only one** run executed on the boxes (26 August 2026, 21:12 UTC).
  ⛔ **A sample of one is not a rate**, and a round number pulled out of it
  would be a `[?]` disguised as an `[M]`.  ⇒ The threshold stays `[?]` until the
  log has enough runs on the boxes to count **how often
  they arrive**; that day it is replaced, and this line tells whoever does it what
  they must count.

⭐ And the count-based window has a property worth writing down: **the more
  one pushes, the sooner it shouts.**  Every push with the laptop alone uses up one slot of the
  twenty; twenty pushes without the boxes and C15 is red, whether in a day or a
  month.  ⛔ But on its own it is not enough — if nobody pushes any more, the window does not
  advance and C15 would stay green for ever: ⇒ **that is why the questions are
  two, by counts AND by days**, and it is not belt and braces.

---------------------------------------------------------------------------
⛔ WHERE THIS MESH MAKES SENSE — and where it exits **2** instead of lying
---------------------------------------------------------------------------

C15 reads **the merged memory**, and the merged memory lives **on the laptop**
(`11-registro-unisci.py`, and it says why).

⛔⛔ On the test machine the log contains **only that machine's
    runs** — that is **all** runs executed on the boxes.  ⇒ There C15 would be
    green whatever happens: **a predicate that cannot fail**,
    `LEZIONI.md` §1.44, and moreover inside the mesh that serves to prevent it.

⇒ ⭐ So C15 asks the same thing C12 asks: **is there a git repository?**
  If there is not, it exits **2** — *«the terrain does not hold»* — instead of giving a green
  that has looked at nothing.  ⚠ It is the same answer C12 gives on the
  test machine, and §7-bis.16 writes that **it is the right answer**.

---------------------------------------------------------------------------
⛔ WHAT C15 DOES **NOT** LOOK AT — or someone will trust it too much
---------------------------------------------------------------------------

  · ⛔ **It does not say the hook started by itself.**  A run launched by hand
    on the test machine counts exactly like one started by the `pre-push`.
    ⚠ And rightly so: the boxes ran.  ⭐ That an installed hook is what makes them start
    is said by **C12**, and it is good that one mesh only says it.
  · ⛔ **It does not say the meshes gave green.**  A red C1 is a run
    executed on the boxes as much as a green one — indeed, it is the best proof
    that the box was there.  ⭐ The colour of the meshes is their business.
  · ⛔ **It does not say the TRANSPORT works.**  If the test machine runs and
    `merge_logs` does not bring the lines back, for C15 it is identical to a machine
    switched off.  ⚠ It is not a defect: it is the definition — *a run the common memory
    knows nothing about is not a run, for anyone reading that memory.*
    ⭐ The hook already shouts that case by itself (*«the run over there really
    happened, but here nothing would be known of it»*).
  · ⛔ **It does not say the boxes are on the OTHER machine.**  C15 asks that
    a mesh that wants a box has judged; ⚠ if one day the boxes
    ran on the laptop, C15 would be green — ⭐ and it would be right: the
    boxes would have run.  ⛔ What would be lost is the *second
    machine*, and at that point it is the hook's design that has changed, not
    this mesh that is wrong.
  · ⛔ **It does not look at which boxes.**  See question 3: the count is printed.
  · ⛔ **It does not know whether the boxes were the right ones** (aligned, rebuilt
    secretly): that is **C11**.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ in the window the boxes ran, recently, and with the real load
  1  ⛔ one of the two judging questions does not hold ⇒ red
  3  ⛔ I could not look — the log cannot be read, or there is
     no real run to examine.  ⛔ And it is NOT a red: that the hook
     does not run **at all** is said by C12, and two meshes giving red for the
     same fact make what happened once look twice as serious
  2  the terrain does not hold (⛔ it is not the machine of the merged memory), or the usage
     is wrong
===========================================================================
"""
import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "11-gancio-registro.jsonl")

# ── the runs written before the English rename (DECISIONI §10.38) keep the Italian words, and
#    11-gancio-registro.jsonl is append-only: old Italian rows, then new ones.  The first tuple
#    is protected (english-migration/protetti.tsv), the second is renamed with the code: after
#    the rename OLD_SPELLING maps every old word to the code's own, before it is empty.  Same
#    order in both, one word per position.  Only the words this file reads from a run.
_OLD_WORDS = (
    "istante", "secco", "maglie", "esito", "nome", "passo0",
    "dove",
)  # end of the old words
_WORDS_NOW = (
    "instant", "dry", "meshes", "outcome", "name", "passo0",
    "where",
)
OLD_SPELLING = {a: b for a, b in zip(_OLD_WORDS, _WORDS_NOW) if a != b}


def current_spelling(x):
    """A record of an old register in the code's spelling: keys, and string values equal to a word."""
    if isinstance(x, dict):
        return {OLD_SPELLING.get(k, k): current_spelling(v) for k, v in x.items()}
    if isinstance(x, list):
        return [current_spelling(v) for v in x]
    return OLD_SPELLING.get(x, x) if isinstance(x, str) else x


def spellings(word):
    """The word and its old spellings, for prefixes of mesh names («passo0(kde)»)."""
    return (word,) + tuple(a for a, b in OLD_SPELLING.items() if b == word)


# ⛔ The two numbers are NOT mine: they come from C12 and from C13, and above it is written
#    why they are the same and not two new ones.  ⚠ At the origin they are `[?]`.
DEFAULT_LAST_N = 20   # `[R]` C13, `DEFAULT_LAST_N`
DEFAULT_DAYS = 7    # `[R]` C12, `DEFAULT_DAYS`

# ---------------------------------------------------------------------------
# ⭐⭐ THE TWO LISTS, and the difference between them is the whole second question.
#
# ⛔ They are HERE, declared, instead of being guessed by a rule: a
#    new mesh that wants the box and does not enter this list does not make
#    C15 red — it makes it **blind**, and that is worse.  ⚠ Whoever
#    adds a mesh to the net adds a line here, and the comment next to it
#    says how to decide which of the two it goes in.
# ---------------------------------------------------------------------------

# ⭐ «Without a running box it cannot reach a judgement.»
#    ⇒ A 0 or 1 of theirs in the log **is the proof that the boxes were there.**
WANT_BOX = {
    "step0",  # `[R]` validates the ENVIRONMENT inside the box (11-accendi.sh step0)
    "c1",      # `[R]` the session is born and shows
    "c5",      # `[R]` the sound is not silence
    "c7",      # `[R]` it closes and nothing remains
    "c8",      # `[R]` the second tenant opens the browser
    "c9",      # `[R]` the log says WHOM it is talking about
    "c11",     # `[R]` queries the four boxes with dpkg — `[M]` 0 where they
               #       are, 3 where they are not (log 26-27 Aug 2026)
    "c14",     # `[R]` starts the four boxes TOGETHER
}

# ⭐ «It starts the product, or a browser, INSIDE the box.»
#    ⇒ They are the only ones that touch the graphics card and the session, that is the
#      reason the test machine exists (D1).
# ⛔ `passo0` and `c11` stay out on purpose: the first looks at the environment, the
#    second queries the package manager.  ⚠ They are real judgements and count
#    for question 1, ⛔ but a net that does only those has stopped measuring
#    the product without stopping saying green.
STARTS_SESSION = {"c1", "c5", "c7", "c8", "c9", "c14"}

# ⛔ And this is NOT a mesh: it is the delegation's annotation.  It is 0 even in
#    a dry run — `[M]` log of 27 Aug 2026, 07:30.  ⇒ It does not count.
NOT_A_MESH = {"la meta remota"}


def number_of(name):
    """From «C1(gnome)x2» to «c1», from «passo0(kde)» to «passo0».

    ⛔ Returns `None` when it does not recognise a mesh — and `None` is not «no»: it is
       «it is not one of the meshes I know», which for the two lists counts the same.
    """
    if not isinstance(name, str):
        return None
    s = name.strip().lower()
    if s in NOT_A_MESH:
        return None
    if s.startswith(spellings("passo0")):
        return "passo0"
    # ⚠ `\d+` is greedy on purpose: «c10» must be «c10» and not «c1».
    m = re.match(r"^(c\d+)", s)
    return m.group(1) if m else None


def box_of(name):
    """The box name written in brackets, or `None`.

    ⛔ And it is NOT filtered on a list of known desktops: the day a
       new desktop comes in — the case `11-gancio.sh` can recognise by itself — a
       filter would make it invisible precisely here.  ⚠ The price is that a
       bracket put there for another reason would end up in the count; ⭐ and since the count **does not
       judge**, the price is a line printed crooked, not a false red.
    """
    if not isinstance(name, str):
        return None
    m = re.search(r"\(([^)]+)\)", name)
    return m.group(1).strip().lower() if m else None


def read_log(fpath):
    """Returns (giri, guaio) — ⛔ and the cases are three, as in C12 and C13.

       (None, "assente")     the file is not there
       (None, "illeggibile") it is there and does not open, or it is all malformed
       ([...], None)         the runs, in order of writing
    """
    if not os.path.exists(fpath):
        return None, "assente"
    try:
        with open(fpath, "r", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return None, "illeggibile"
    rounds, skewed = [], 0
    for r in lines:
        r = r.strip()
        if not r:
            continue
        try:
            o = current_spelling(json.loads(r))
        except ValueError:
            skewed += 1
            continue
        if not isinstance(o, dict):
            skewed += 1
            continue
        rounds.append(o)
    if not rounds and skewed:
        return None, "illeggibile"
    return rounds, None


def age_in_days(instant, t_now):
    """⛔ Returns `None` if it cannot tell — never zero, never an invented number."""
    if not instant or t_now is None:
        return None
    try:
        import datetime
        t = datetime.datetime.fromisoformat(instant)
        if t.tzinfo is None:
            t = t.astimezone()
        return (t_now - t.timestamp()) / 86400.0
    except (ValueError, TypeError, OverflowError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
def judge(rounds, last_n, days, t_now):
    """⭐ The judgement, separated from the files — so it can be certified.

    ⛔ Returns `None` for «I could not look» (unreadable log, or
       no real run to examine), otherwise a dictionary containing
       `guai`: a LIST, possibly empty.

    ⚠ `None` is not the empty list.  «I did not look» and «I looked and it holds»
      are two different things, and this project has already paid for confusing
      them.
    """
    if rounds is None:
        return None
    # ⛔ Dry runs are thrown away BEFORE taking the last N — the same
    #    rule as C13, and for the same reason: twenty `--dry-run` in a row
    #    would push out of the window the last real run on the boxes, and
    #    the mesh would turn red for nothing.
    genuine = [g for g in rounds if not g.get("dry")]
    if not genuine:
        return None
    chunk = genuine[-last_n:]

    on_boxes = []      # the runs in which a box mesh HAS JUDGED
    with_load = []         # ... and among those, the ones that started something
    seen_boxes = set()   # ⚠ information, not judgement (question 3)
    machines = set()

    for g in chunk:
        d = g.get("where")
        if d:
            machines.add(d)
        judging, ongoing = [], []
        for m in g.get("meshes") or []:
            # ⛔⛔ AND HERE IS THE HEART: **a 3 is not a judgement.**
            #    A mesh that wanted the box and did not find it writes 3,
            #    and that is exactly the symptom of the switched-off test machine.
            #    ⚠ The -1 of dry runs also falls here, and it is not a duplicate:
            #      it is a second net under the first.
            if m.get("outcome") not in (0, 1):
                continue
            n = number_of(m.get("name"))
            if n is None or n not in WANT_BOX:
                continue
            judging.append(m.get("name"))
            s = box_of(m.get("name"))
            if s:
                seen_boxes.add(s)
            if n in STARTS_SESSION:
                ongoing.append(m.get("name"))
        if judging:
            on_boxes.append((g, judging))
        if ongoing:
            with_load.append((g, ongoing))

    r = {
        "esaminati": len(chunk),
        "totals": len(genuine),
        "a_vuoto": len(rounds) - len(genuine),
        "sulle_scatole": len(on_boxes),
        "col_carico": len(with_load),
        "boxes": sorted(seen_boxes),
        "macchine": sorted(machines),
        "ultimo": on_boxes[-1][0] if on_boxes else None,
        "ultimo_maglie": on_boxes[-1][1] if on_boxes else [],
        "ultimo_carico": with_load[-1][0] if with_load else None,
        "eta": None,
        "troubles": [],
    }

    # ── QUESTION 1 ─────────────────────────────────────────────────────────
    if not on_boxes:
        # ⛔ And we return AT ONCE.  Without a run on the boxes, «it started
        #    nothing» is a consequence, not a second fault: a list that
        #    counts the same fact twice makes what is simple look serious
        #    (the same rule as C12).
        r["troubles"].append(
            "in the last %d real runs ⛔ NONE was executed on the "
            "boxes: no mesh that needs a box reached "
            "a judgement" % len(chunk))
        return r

    # ── and the age of the last one ────────────────────────────────────────
    eta = age_in_days(r["ultimo"].get("instant"), t_now)
    r["eta"] = eta
    if eta is None:
        # ⚠ An instant that cannot be read is not «old»: it is «I do not
        #   know».  ⛔ And it is said as a fault of the LOG, not as a machine
        #   switched off — it is not the same thing, and they are cured in different places.
        r["troubles"].append(
            "the last run on the boxes does not carry a readable instant (%r): "
            "the log is malformed" % (r["ultimo"].get("instant"),))
    elif eta > days:
        r["troubles"].append(
            "the last run on the boxes is from %.1f days ago, and the declared "
            "threshold is %d" % (eta, days))

    # ── QUESTION 2 ─────────────────────────────────────────────────────────
    if not with_load:
        r["troubles"].append(
            "in the window the boxes answered, ⛔ but NOBODY started "
            "the product inside them: only the zero-cost meshes "
            "(the environment, the packages). Nobody touched the "
            "graphics card")
    return r


# ═══════════════════════════════════════════════════════════════════════════
def certify():
    """⛔ We prove that the judge CAN give green, CAN give red, and CAN say
       «I do not know» — and that each of the two questions fires **in both
       directions** (`LEZIONI.md` §1.49: the fault is removed and green is demanded).
    """
    import datetime
    t_now = time.time()

    def instant(days_ago):
        t = datetime.datetime.now().astimezone() - datetime.timedelta(days=days_ago)
        return t.isoformat()

    def cur_round(meshes, dry=False, days_ago=0.5, where="NIC-OS"):
        return {"instant": instant(days_ago), "dry": dry,
                "where": where, "meshes": meshes}

    def m(name, outcome=0):
        return {"name": name, "outcome": outcome, "seconds": 1,
                "fault_grafted": False}

    # ⭐ the «laptop only» run: it is the exact line the log writes
    #   today when the test machine does not answer.
    def portable(days_ago=0.5):
        return cur_round([m("C10"), m("C11", outcome=3), m("C12"), m("C13"),
                     m("C14", outcome=3),
                     {"name": "C10 guasto innestato", "outcome": 0, "seconds": 0,
                      "fault_grafted": True, "saw_the_fault": True}],
                    days_ago=days_ago, where="CHUWI")

    cases = [
        # ── the green, and where it comes from ──────────────────────────────
        ("⭐ a run with C1(gnome) judged and recent",
         [cur_round([m("C10", outcome=3), m("C11"), m("C1(gnome)x2", outcome=1)])],
         "green"),

        ("⭐ a RED C1 is a run on the boxes as much as a green one",
         [cur_round([m("C1(kde)x10", outcome=1)])], "green"),

        # ── ⭐⭐ THE HOLE THIS MESH EXISTS FOR ──────────────────────────────
        ("⛔⛔ twenty runs of the LAPTOP ONLY — C12 and C13 would be green",
         [portable() for _ in range(20)], "RED"),

        ("⛔⛔ «the remote half is green» in a NON-dry run does not count",
         [cur_round([{"name": "la meta remota", "outcome": 0, "seconds": 1,
                 "fault_grafted": False, "note": "la meta' remota e' verde"},
                m("C10")])], "RED"),

        ("⛔ the box meshes are there, but they are ALL outcome 3",
         [cur_round([m("passo0(gnome)", outcome=3), m("C1(gnome)x2", outcome=3),
                m("C11", outcome=3), m("C14", outcome=3)])], "RED"),

        ("⛔ the meshes are there with outcome -1 (dry inside a real run)",
         [cur_round([m("C1(gnome)x2", outcome=-1), m("C11", outcome=-1)])], "RED"),

        # ── QUESTION 2, in both directions ──────────────────────────────────
        ("⛔ the boxes answer (C11) but nobody starts anything inside them",
         [cur_round([m("C11"), m("C12"), m("C13")])], "RED"),

        ("⛔ not even step 0 is enough: it looks at the environment, it does not start",
         [cur_round([m("passo0(kde)"), m("C11")])], "RED"),

        # ⭐⭐ AND THIS IS THE CASE THAT PREVENTS C15 FROM CERTIFYING ITSELF.
        #    ⛔ A mesh that counted itself among the proofs that «the boxes have
        #       run» would be green every time it runs, that is always:
        #       `LEZIONI.md` §1.44 inside the mesh written to prevent it.
        ("⛔⛔ twenty runs of green C15 only: ⭐ it does not certify itself",
         [cur_round([m("C15"), m("C12"), m("C13")]) for _ in range(20)], "RED"),

        ("⭐ C14 instead STARTS the four boxes ⇒ green",
         [cur_round([m("C11"), m("C14")])], "green"),

        ("⭐ passo0 + C5 ⇒ green: one that starts is enough",
         [cur_round([m("passo0(xfce)"), m("C5(xfce)")])], "green"),

        # ── THE THRESHOLD IN DAYS, in both directions ───────────────────────
        ("⛔ the last run on the boxes is from twenty days ago (threshold 7)",
         [cur_round([m("C1(gnome)x2")], days_ago=20)], "RED"),

        ("⭐ … and at 6,5 days it is still GREEN (the direction one forgets)",
         [cur_round([m("C1(gnome)x2")], days_ago=6.5)], "green"),

        ("⚠ the instant cannot be read ⇒ it is the log that is malformed",
         [{"instant": "yesterday morning", "dry": False,
           "meshes": [m("C1(gnome)x2")]}], "RED"),

        # ── THE WINDOW BY COUNTS, in both directions ────────────────────────
        ("⭐ nineteen laptop runs AFTER one on the boxes ⇒ green",
         [cur_round([m("C1(gnome)x2")])] + [portable() for _ in range(19)],
         "green"),

        ("⛔⛔ twenty-one, and the run on the boxes SLIDES OUT of the window",
         [cur_round([m("C1(gnome)x2")])] + [portable() for _ in range(21)],
         "RED"),

        ("⭐ twenty DRY runs do not push out the run on the boxes",
         [cur_round([m("C1(gnome)x2")])]
         + [cur_round([m("C1(gnome)x2")], dry=True) for _ in range(20)], "green"),

        # ── «I DO NOT KNOW», which is not a red ─────────────────────────────
        ("⛔ no real run ⇒ «I do not know» — that the hook does not run is said by C12",
         [cur_round([m("C1(gnome)x2")], dry=True)], "non lo so"),

        ("⛔ no run at all ⇒ «I do not know»", [], "non lo so"),

        ("⛔ unreadable log ⇒ «I do not know», not red", None, "non lo so"),
    ]

    print("== certification of the C15 judge ==")
    print("   yardstick in force: last %d REAL runs `[R]` from C13  ·  last run"
          % DEFAULT_LAST_N)
    print("   on the boxes within %d days `[R]` from C12  ·  ⛔ at the origin `[?]`"
          % DEFAULT_DAYS)
    print("   ⛔ and a run «on the boxes» is a run in which a mesh that wants")
    print("      a box reached a JUDGEMENT (0 or 1), not a 3\n")

    troubles = 0
    for name, rounds, expected in cases:
        r = judge(rounds, DEFAULT_LAST_N, DEFAULT_DAYS, t_now)
        if r is None:
            obtained = "non lo so"
        elif r["troubles"]:
            obtained = "RED"
        else:
            obtained = "green"
        ok = obtained == expected
        print("  %s  %-63s ⇒ %-9s (expected %s)"
              % ("OK " if ok else "NO ", name, obtained, expected))
        if not ok:
            troubles += 1
            print("        (the judge said: %r)" % (r,))

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ AND THE CASE THAT DECLARES A **NON**-JUDGEMENT: the count of the boxes.
    #
    # ⛔ It is needed because it is the easiest thing to turn into a perpetual
    #    red: «they answered in one out of four» looks like a fault, and it is
    #    not — the fast family looks at GNOME only by declared choice.
    # ⇒ Here we DEMAND that a single box stays GREEN, and that the count is
    #   written anyway.  The day someone turned it into a
    #   judgement, this line would turn red and tell them.
    # ═══════════════════════════════════════════════════════════════════════
    print()
    una = judge([cur_round([m("C1(gnome)x2")])],
                  DEFAULT_LAST_N, DEFAULT_DAYS, t_now)
    four = judge([cur_round([m("C1(gnome)x2"), m("C1(kde)x2"),
                             m("C1(xfce)x2"), m("C1(lxqt)x2")])],
                      DEFAULT_LAST_N, DEFAULT_DAYS, t_now)
    ok = (una is not None and not una["troubles"] and una["boxes"] == ["gnome"]
          and four is not None and not four["troubles"]
          and four["boxes"] == ["gnome", "kde", "lxqt", "xfce"])
    print("  %s  %-63s ⇒ %s"
          % ("OK " if ok else "NO ",
             "⭐⭐ ONE single box stays GREEN, and the count is printed anyway",
             "%r against %r" % (una["boxes"] if una else None,
                                four["boxes"] if four else None)))
    if not ok:
        troubles += 1

    print()
    if troubles:
        print("⛔ the judge is NOT reliable: %d wrong cases" % troubles)
        return 1
    print("⭐ the judge sees the test machine switched off while the log")
    print("   fills up with green runs, ⭐⭐ and ⛔ it is NOT fooled either by a")
    print("   «the remote half is green» or by a row of 3s")
    print("⭐ and it fires in BOTH DIRECTIONS: at 20 days red, at 6,5 green; at 21")
    print("   runs out of the window red, at 19 inside green")
    print("⚠ and this certification covers THE JUDGEMENT, not the transport: that the")
    print("  test machine's lines really arrive here is told by")
    print("  `11-registro-unisci.py`, not by me")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def repo_is_here():
    """⭐ The same question as C12, and for the same reason.

    ⛔ It is not pedantry: on the test machine the log contains only the
       runs of that machine — all on the boxes — and C15 would be green
       whatever happens (`LEZIONI.md` §1.44).
    """
    try:
        p = subprocess.run(["git", "-C", HERE, "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=30)
    except OSError:
        return False
    return p.returncode == 0 and bool(p.stdout.strip())


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log", default=LOG)
    p.add_argument("--last", type=int, default=DEFAULT_LAST_N,
                   help="how many real runs to look back. `[R]` C13's "
                        "window, `[?]` at its origin")
    p.add_argument("--days", type=int, default=DEFAULT_DAYS,
                   help="for how many days at most the boxes may not "
                        "have run. `[R]` C12's threshold, `[?]` at its "
                        "origin")
    p.add_argument("--everywhere", action="store_true",
                   help="⛔ do NOT use it to silence a 2: here the log is not "
                        "the merged memory and green would mean "
                        "nothing. It serves to diagnose a log passed with "
                        "--log")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()

    if a.certify:
        sys.exit(certify())

    if not a.everywhere and not repo_is_here():
        print("⛔ I am not inside a git repository.")
        print("   ⇒ if this is the test machine, here the log contains")
        print("     ONLY this machine's runs — that is all runs on the")
        print("     boxes — and this mesh would be green whatever")
        print("     happens: a predicate that cannot fail.")
        print("   ⭐ The merged memory lives on the laptop, and that is where it must run.")
        print("   ⇒ the terrain does not hold")
        sys.exit(2)

    rounds, trouble = read_log(a.log)

    print("== C15 — does the remote half really run? ==")
    print("   ⛔ the fault it looks for: the test machine switched off silently —")
    print("      ⛔⛔ with C12 and C13 staying GREEN, because the laptop")
    print("      half runs anyway and leaves a trace")
    print("   yardstick: last %d REAL runs `[R]` from C13  ·  last run on the"
          % a.last)
    print("          boxes within %d days `[R]` from C12  ·  ⛔ at the origin `[?]`"
          % a.days)
    print("   ⛔ what counts is the JUDGEMENT of a mesh that wants a box (0 or 1),")
    print("      not a 3 and not «the remote half is green»")
    print()

    if trouble == "assente":
        print("⛔ the log is not there: %s" % a.log)
        print("   ⇒ I could not look — ⛔ and it is NOT a red.")
        print("     That the hook has never run is said by C12, and it is right")
        print("     that ONE mesh only says it.")
        return 3
    if trouble == "illeggibile":
        print("⛔ the log is there and cannot be read: %s" % a.log)
        print("   ⇒ I could not look")
        return 3

    r = judge(rounds, a.last, a.days, time.time())
    if r is None:
        print("⛔ no REAL run to look at (%d lines, all dry or none)"
              % len(rounds or []))
        print("   ⇒ I could not look — ⛔ and it is NOT a red")
        return 3

    print("   runs in the log      : %d real, %d dry" % (r["totals"], r["a_vuoto"]))
    print("   looked at            : the last %d" % r["esaminati"])
    # ⚠ The RATIO is printed and ⛔ NOT judged: a threshold like «at least a
    #   third of the runs on the boxes» would be an invented round number, that is
    #   a `[?]` disguised as a yardstick.  ⭐ But whoever reads must see it, because it is
    #   the shape in which the fault announces itself BEFORE turning red.
    print("   ⭐ on the boxes       : %d of %d" % (r["sulle_scatole"], r["esaminati"]))
    print("   ⭐ with the real load : %d of %d  (a session started inside a box)"
          % (r["col_carico"], r["esaminati"]))
    if r["ultimo"] is not None:
        print("   last on the boxes    : %s  (%s)"
              % (r["ultimo"].get("instant"),
                 "age unknown" if r["eta"] is None else "%.1f days ago" % r["eta"]))
        print("     ⇒ reached by       : %s" % ", ".join(r["ultimo_maglie"]))
    if r["ultimo_carico"] is not None:
        print("   last with the load   : %s" % r["ultimo_carico"].get("instant"))
    # ⚠ INFORMATION, not judgement — and the line says so, or someone will
    #   turn it into a perpetual red (see question 3 at the top).
    print("   ⚠ boxes seen         : %d  (%s)"
          % (len(r["boxes"]), ", ".join(r["boxes"]) if r["boxes"] else "none with the name written"))
    print("     ⛔ it is information, NOT a judgement: the fast family looks at")
    print("        GNOME only by declared choice")
    print("   ⚠ machines in the log: %s"
          % (", ".join(r["macchine"]) if r["macchine"] else "none says"))
    print()

    if r["troubles"]:
        print("⛔⛔ RED — the half that counts is not running:")
        for g in r["troubles"]:
            print("   · %s" % g)
        print()
        print("   ⇒ ⛔ and the damage is not that a measurement is missing: it is that **C12 and")
        print("     C13 stay GREEN** while it happens.  The laptop half")
        print("     runs in one second, leaves a trace, and injects C10's fault")
        print("     into it: the net tells itself it is alive.")
        print()
        print("   ⭐ To turn it green again — and it does turn green, it is not a perpetual")
        print("     red:")
        print("       bash 11-gancio.sh remote --family all")
        print("     or, on the test machine:")
        print("       bash 11-gancio.sh run --family works")
        print("   ⚠ If it does not turn green, the fault is in the delegation or in the")
        print("     transport of the log, not in this mesh.")
        return 1

    print("⭐ in the last %d real runs the boxes ran %d times, and %d"
          % (r["esaminati"], r["sulle_scatole"], r["col_carico"]))
    print("   times with the real load — a session started inside a box")
    # ⚠⚠ AND HERE THERE IS A NUMBER, and it must be said that it is there instead of pretending not
    #    (`LEZIONI.md` §1.50: a comment that describes a quantity different from
    #    the one the code governs is a trap).
    #
    #    **Half** — and it governs ONE thing only: whether this line is printed.
    #    ⛔ It does not govern the outcome: below half C15 is green exactly as
    #       above.  ⇒ It is a warning, not a judgement threshold, ⭐ and it does not
    #       need a measurement under it because it decides nothing.
    if r["sulle_scatole"] * 2 <= r["esaminati"]:
        print("⚠ ⛔ and they are **the minority**: %d runs out of %d were executed"
              % (r["esaminati"] - r["sulle_scatole"], r["esaminati"]))
        print("  without touching a box.  ⚠ This is NOT a red — the outcome")
        print("  stays green — ⭐ but it is the shape in which the fault arrives: the")
        print("  laptop half that keeps writing green lines while")
        print("  the other thins out.  ⇒ Only one, then zero.")
    print("⚠ and this mesh says the boxes RUN, ⛔ not that the hook")
    print("  starts them by itself (that is C12), nor that the boxes are")
    print("  the right ones (that is C11).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
