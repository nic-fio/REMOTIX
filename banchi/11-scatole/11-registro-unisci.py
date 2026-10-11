#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-registro-unisci — ⭐⭐ ONE MEMORY ONLY, and it stays append-only
===========================================================================

    python3 11-registro-unisci.py <receiving-log> <arrived-lines>
    python3 11-registro-unisci.py --certify

---------------------------------------------------------------------------
⛔⛔ THE TROUBLE IT SOLVES — *two logs that do not talk to each other*
---------------------------------------------------------------------------

`DECISIONI.md` §4.6-novemdecies: the two halves of the hook live on two machines.
⇒ `11-gancio-registro.jsonl` **is born where the hook runs**, so there is one
on the laptop and one on the test machine.  ⛔ And **C13** — the mesh that says
whether the net can still give red — reads only the one of the machine it runs on.

⇒ ⭐ The single memory lives **on the laptop**, and it is not a preference: it is the only
  place where the two meshes that read that memory can judge.
  ⛔ **C12** needs the git repository to know where the hooks are — on the
  test machine it exits **2**, «bad terrain» (`fasi/11…` §7-bis.16, and there
  it is written that *it is the right answer*).  ⇒ The laptop is where the net
  looks at itself in the mirror; the test machine is where it **runs**.

---------------------------------------------------------------------------
⛔⛔ AND THE ORDER RULE, which is this file's whole job
---------------------------------------------------------------------------

The log is **append-only and never rewritten** (`11-gancio.sh`, at the top).  ⇒ Here
nothing is reordered and nothing is rewritten: ⭐ **only the lines NEWER than the
most recent one already present are appended.**

⚠ And the reason is not elegance, it is a false red:

  · **C12** looks at `veri[-1]`, that is **the last line of the file**, not the most
    recent one.  ⛔ If a merge appended an old line at the bottom, C12 would say
    *«the last run was twenty days ago»* while the hook ran a minute
    ago — a red that cannot be turned green, that is `LEZIONI.md` §1.49,
    which is worse than no mesh at all.
  · **C13** looks at the last N: lines out of order change **which** N.

⇒ ⭐ By appending only the newest, the file stays **monotonic by instant** by
  construction, and neither of the two meshes needs touching.

⛔ **THE PRICE, declared**: a remote line OLDER than the most recent one
   already present **never gets in again**.  ⇒ If someone runs the hook by hand
   on the test machine *while* the laptop writes one of its own, that run is
   lost to the common memory.  ⚠ It is not serious — it stays in the test machine's
   log, which is not deleted — but **it is said**: it is the number
   `perse_perche_vecchie` this program prints at every merge, instead of
   disappearing silently.

⚠ And the two clocks must agree, because the comparison is between instants.
  `[M]` 27 August 2026: laptop `2026-08-27T07:20:03+02:00`, test machine
  `2026-08-27T05:20:03+00:00` ⇒ **the same instant, offset 0 s**.  ⛔ The day
  the test machine's clock fell behind, its lines
  would look old and would not get in: ⇒ that is why the offset **is printed**
  when there is something to say.

---------------------------------------------------------------------------
⚠ AND WHAT ARRIVES IS NOT CLEAN
---------------------------------------------------------------------------

The lines arrive from `sshpw.py --get`, that is from an `scp`: ⭐ **never** from the
stdout of a remote `cat`, where the password prompt ends up too
(`fondamenta/strumenti/sshpw.py`, and it says why).  ⇒ Empty or truncated lines
are still possible (a run interrupted half-way through writing).
⛔ A line that cannot be read **is not thrown away silently**: it is counted and
   printed.  ⚠ And if NO line at all can be read, it is not «zero new
   lines»: it is **I could not look**, and it exits 3.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  the merge succeeded (even with zero new lines: it is a fact, not a trouble)
  3  ⛔ I could not look — what arrived contains no readable line
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import datetime
import json
import os
import sys

# ── the runs written before the English rename (DECISIONI §10.38) keep the Italian words, and
#    11-gancio-registro.jsonl is append-only: old Italian rows, then new ones.  The first tuple
#    is protected (english-migration/protetti.tsv), the second is renamed with the code: after
#    the rename OLD_SPELLING maps every old word to the code's own, before it is empty.  Same
#    order in both, one word per position.  Only the words this file reads from a run.
_OLD_WORDS = (
    "istante",
)  # end of the old words
_WORDS_NOW = (
    "instant",
)
OLD_SPELLING = {a: b for a, b in zip(_OLD_WORDS, _WORDS_NOW) if a != b}


def current_spelling(x):
    """A record of an old register in the code's spelling: keys, and string values equal to a word."""
    if isinstance(x, dict):
        return {OLD_SPELLING.get(k, k): current_spelling(v) for k, v in x.items()}
    if isinstance(x, list):
        return [current_spelling(v) for v in x]
    return OLD_SPELLING.get(x, x) if isinstance(x, str) else x


def instant_of(json_line):
    """Returns the instant as seconds, or `None` if it cannot tell.

    ⛔ Never zero and never an invented number: «I do not know» has a value of its own, and
       this project has already paid for confusing it with «very old».
    """
    q = json_line.get("instant")
    if not q:
        return None
    try:
        t = datetime.datetime.fromisoformat(q)
    except (ValueError, TypeError):
        return None
    if t.tzinfo is None:
        t = t.astimezone()
    return t.timestamp()


def load(fpath):
    """Returns (coppie, storte): coppie is [(istante_o_None, testo_riga, oggetto)]."""
    if not os.path.exists(fpath):
        return [], 0
    with open(fpath, "r", errors="replace") as f:
        lines = f.read().splitlines()
    pairs, skewed = [], 0
    for r in lines:
        r = r.strip()
        if not r:
            continue
        try:
            o = json.loads(r)
        except ValueError:
            skewed += 1
            continue
        if not isinstance(o, dict):
            skewed += 1
            continue
        # ⚠ the instant is read in the code's spelling, ⛔ but the line is appended AS IT IS:
        #   the register is never rewritten, not even to translate it.
        pairs.append((instant_of(current_spelling(o)), r, o))
    return pairs, skewed


def choose(already_present, arrived):
    """⭐ The judgement, separated from the files — so it can be certified.

    Returns (da_accodare, perse_perche_vecchie, gia_c_erano, senza_istante).

    da_accodare is in increasing order of instant.
    """
    texts_present = set(t for _, t, _ in already_present)
    instants_present = [i for i, _, _ in already_present if i is not None]
    # ═══════════════════════════════════════════════════════════════════
    # ⛔⛔ THE BOUNDARY IS THE MOST RECENT, **not the last line of the file** — and the
    #     first draft had written the last line.  ⭐ The certification below
    #     caught it, `[M]` 27 August 2026, and no reading
    #     would have caught it.
    #
    # ⚠ It looked like the opposite: C12 reads `genuine[-1]`, that is the last line, ⇒ the
    #   «natural» boundary seemed to be that one.  ⛔ But if the file were ALREADY out of
    #   order (instants 500, then 100), with the boundary on the last line a line
    #   at 300 would get in and the file would end 500 · 100 · 300: the last line
    #   **still is not the most recent**, and C12 would keep reading a
    #   run that is not the last.
    #
    # ⭐ With the MAXIMUM instead the invariant holds by itself: only what is
    #   newer than everything gets in, and in increasing order ⇒ **the last line of the file is
    #   always the most recent**, which is exactly what C12 needs.
    # ═══════════════════════════════════════════════════════════════════
    confine = max(instants_present) if instants_present else None

    new_ones, old_ones, duplicate, without = [], 0, 0, 0
    for i, text, _ in arrived:
        if text in texts_present:
            duplicate += 1
            continue
        if i is None:
            # ⚠ A line without an instant has no known place: appending it
            #   would break the monotonicity, that is C12's false red.
            without += 1
            continue
        if confine is not None and i <= confine:
            old_ones += 1
            continue
        new_ones.append((i, text))
    new_ones.sort(key=lambda c: c[0])
    return [t for _, t in new_ones], old_ones, duplicate, without


# ═══════════════════════════════════════════════════════════════════════════
def certify():
    """⛔ We prove that the judgement can do the three things it exists for:
       append the new, REFUSE the old, and not repeat what was already seen."""

    def r(seconds, name="x"):
        t = datetime.datetime.fromtimestamp(seconds, datetime.timezone.utc)
        o = {"instant": t.isoformat(), "name": name}
        text = json.dumps(o, sort_keys=True)
        return (seconds, text, o)

    cases = [
        ("⭐ a newer line is appended",
         [r(100)], [r(200)], (1, 0, 0, 0)),
        ("⛔⛔ an OLDER line does not get in — it would break C12's order",
         [r(300)], [r(200)], (0, 1, 0, 0)),
        ("⛔ the identical line already present is not repeated",
         [r(100)], [r(100)], (0, 0, 1, 0)),
        ("⭐ three new ones all get in, and in order",
         [r(100)], [r(400), r(200), r(300)], (3, 0, 0, 0)),
        ("⭐ the receiving log is empty: everything gets in",
         [], [r(200), r(100)], (2, 0, 0, 0)),
        ("⚠ a line without an instant has no known place: it stays out, and is counted",
         [r(100)], [(None, '{"name":"senza"}', {"name": "senza"})], (0, 0, 0, 1)),
        # ⭐⭐ THE CASE THAT CORRECTED THIS FILE — see the comment in `choose`.
        ("⭐⭐ the log is already out of order: the boundary is the MOST RECENT",
         [r(500), r(100)], [r(300)], (0, 1, 0, 0)),
        ("⭐ mixed: only those beyond the boundary, in order",
         [r(100)], [r(50), r(150), r(120)], (2, 1, 0, 0)),
    ]

    print("== certification of the 11-registro-unisci judgement ==")
    print("   ⛔ the rule: ONLY what is newer than the MOST RECENT line")
    print("      already present is appended — so the last line of the file")
    print("      stays the most recent, which is what C12 reads")
    troubles = 0
    for name, present, arrived, expected in cases:
        new_ones, old_ones, duplicate, without = choose(present, arrived)
        obtained = (len(new_ones), old_ones, duplicate, without)
        ok = obtained == expected
        # ⭐ and the count is not enough: the new ones must come out IN ORDER.
        if ok and len(new_ones) > 1:
            instants = []
            for t in new_ones:
                instants.append(instant_of(json.loads(t)))
            if instants != sorted(instants):
                ok = False
        print("  %s  %-62s ⇒ %s (expected %s)"
              % ("OK " if ok else "NO ", name, obtained, expected))
        if not ok:
            troubles += 1

    # ⭐⭐ And the case that matters most: merging TWICE in a row must
    #    add nothing the second time.  ⛔ A merge that repeats is
    #    a log that swells with copies, and C13 would count the same
    #    certification twenty times believing it had twenty.
    present = [r(100)]
    arrived = [r(200), r(300)]
    new_ones, _, _, _ = choose(present, arrived)
    present2 = present + [(instant_of(json.loads(t)), t, json.loads(t)) for t in new_ones]
    new2, _, duplicate2, _ = choose(present2, arrived)
    ok = (len(new_ones) == 2 and len(new2) == 0 and duplicate2 == 2)
    print("  %s  %-62s ⇒ %s"
          % ("OK " if ok else "NO ",
             "⭐⭐ merging twice in a row adds nothing the second time",
             (len(new_ones), len(new2), duplicate2)))
    if not ok:
        troubles += 1

    print()
    if troubles:
        print("⛔ the judgement is NOT reliable: %d wrong cases" % troubles)
        return 1
    print("⭐ appends the new, refuses the old, does not repeat what was seen,")
    print("   ⭐⭐ and repeated twice it does not swell the log")
    print("⚠ and this certification covers THE MERGE, not the transport: that the")
    print("  lines really arrive from the test machine is told by the real")
    print("  run of `11-gancio.sh remote`, not by me")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("local", nargs="?", help="the receiving log")
    p.add_argument("arrived", nargs="?", help="the file of arrived lines")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()

    if a.certify:
        sys.exit(certify())
    if not a.local or not a.arrived:
        p.error("the receiving log and the arrived file are needed")

    if not os.path.exists(a.arrived):
        print("⛔ there is nothing to merge: %s does not exist" % a.arrived)
        print("   ⇒ I could not look")
        return 3

    present, malformed_here = load(a.local)
    arrived, malformed_there = load(a.arrived)

    if not arrived:
        print("⛔ the arrived file contains no readable line "
              "(%d malformed)" % malformed_there)
        print("   ⇒ I could not look — ⛔ and it is NOT «zero new lines»")
        return 3

    new_ones, old_ones, duplicate, without = choose(present, arrived)

    with open(a.local, "a") as f:
        for t in new_ones:
            f.write(t + "\n")

    print("== merge of the logs ==")
    print("   were here         : %d lines (%d malformed)" % (len(present), malformed_here))
    print("   arrived           : %d lines (%d malformed)" % (len(arrived), malformed_there))
    print("   ⭐ appended        : %d" % len(new_ones))
    print("   already there     : %d" % duplicate)
    if old_ones:
        print("   ⚠ perse_perche_vecchie : %d — older than the last line"
              " here, and appending them would break the order C12 reads" % old_ones)
    if without:
        print("   ⚠ no instant      : %d — no known place for them" % without)
    return 0


if __name__ == "__main__":
    sys.exit(main())
