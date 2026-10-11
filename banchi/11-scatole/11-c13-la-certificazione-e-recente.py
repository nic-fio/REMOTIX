#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c13 — ⭐⭐ «THE CERTIFICATION IS RECENT» — the mesh that looks at THE NET
===========================================================================

    python3 11-c13-la-certificazione-e-recente.py
    python3 11-c13-la-certificazione-e-recente.py --certify
    python3 11-c13-la-certificazione-e-recente.py --last 40

---------------------------------------------------------------------------
⛔⛔ THE FAULT IT CATCHES — and `fasi/11…` §4.2 says it better than I would
---------------------------------------------------------------------------

  ⛔ *«a net that is no longer able to give red LOOKS EXACTLY LIKE
       a net that finds nothing.»*

⚠ And it is the hardest fault to see in the whole phase, because **it has no
  symptoms**.  All green, every day, for weeks.  ⇒ And the difference between
  *«there is nothing wrong»* and *«I no longer look»* cannot be read from outside: it
  can be read **only** by injecting a fault and demanding that it be seen.

⭐ §3.6 declares it as part of the net, not as a courtesy:
  ⛔ *«every test of the list has, mandatorily, its injected fault, and
     that case must be run, NOT IMAGINED»* — and ⇒ *«the log of what
     was injected, when, and with what outcome, is part of the net (C13)»*.

---------------------------------------------------------------------------
⭐ WHAT IT LOOKS AT — and the three outcomes it can tell apart
---------------------------------------------------------------------------

It reads the hook's log and, in the last **N real runs**, looks for **at least one
mesh** that carries both things:

    "fault_grafted": true    ⇒ a fault was injected into it
    "saw_the_fault": true  ⇒ and it SAW it

⛔⛔ AND THE TWO THINGS MUST BE IN THE SAME MESH, not in the same run.
   ⚠ If *«in this run there was an injected fault AND someone gave
     red»* were enough, the red could come from **another mesh** — for example from
     C1, which really has a real fault — ⇒ and this mesh would say *«the
     net can give red»* having looked at a test that has nothing to do with it.
     ⛔ It would be a check that cannot give red: the error shape of
     `LEZIONI.md` §1.44.

⚠ And the field is called `ha_visto_il_guasto` and not `esito` for a reason: on an
  injected run **the outcome reads the other way round** (C8 `--no-fix` exits **0**
  when the fault was seen).  ⭐ That inversion lives in one place only —
  inside the hook — and here there is no need to know it.

The three distinct cases, and they really are three different things:

  ⛔ **nothing ever injected**   the net runs and nobody puts it to the test
  ⛔⛔ **injected and NOT seen**  the worst case: the net had a fault
                                under its nose and said green
  ⭐ **injected and seen**       the net is still able to give red

---------------------------------------------------------------------------
⚠ THE YARDSTICK, declared and printed in every outcome
---------------------------------------------------------------------------

  `[?]` **last 20 real runs.**  ⛔ Chosen, not measured.
  ⚠ DRY runs (`--dry-run`) do not count: a run that executed nothing
    cannot have seen anything.

⛔ And the criterion is **by COUNTS, not by days** — because that is how §4.2 asks for it
   (*«in the last N runs»*).  ⚠ It has a declared hole: if the hook ran once
   a month, «the last twenty runs» would cover two years.  ⇒ The age
   of the last certification is **always printed**, and with `--days N` it becomes
   a judgement too.  ⭐ Off by default: this mesh does what the
   document asks of it, and does not invent policy on its own.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ in the last N runs a fault was injected and IT WAS SEEN
  1  ⛔ no fault injected, or injected and not seen ⇒ red
  3  ⛔ I could not look — no real run to examine, or the log
     cannot be read.  ⛔ And it is NOT a red: that the hook has never
     run is said by **C12**, and two meshes giving red for the same fact
     make what happened once look twice as serious
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import json
import os
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
    "istante", "secco", "maglie", "guasto_innestato", "nome",
    "ha_visto_il_guasto",
)  # end of the old words
_WORDS_NOW = (
    "instant", "dry", "meshes", "fault_grafted", "name",
    "saw_the_fault",
)
OLD_SPELLING = {a: b for a, b in zip(_OLD_WORDS, _WORDS_NOW) if a != b}


def current_spelling(x):
    """A record of an old register in the code's spelling: keys, and string values equal to a word."""
    if isinstance(x, dict):
        return {OLD_SPELLING.get(k, k): current_spelling(v) for k, v in x.items()}
    if isinstance(x, list):
        return [current_spelling(v) for v in x]
    return OLD_SPELLING.get(x, x) if isinstance(x, str) else x


DEFAULT_LAST_N = 20


def read_log(fpath):
    """Returns (giri, guaio) — ⛔ and the cases are three, as in C12.

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
            rounds.append(current_spelling(json.loads(r)))
        except ValueError:
            skewed += 1
    if not rounds and skewed:
        return None, "illeggibile"
    return rounds, None


def judge(rounds, last_n):
    """Says whether the net is still able to give red.

    ⛔ Returns `None` for «I could not look» (no real run to look at),
       otherwise a dictionary:

         esaminati       how many real runs it looked at
         innestati       how many meshes had a fault injected
         viste           how many of those SAW it
         mancate         the list (run, mesh) of those that did NOT see it
         ultima          the run in which the last certification succeeded
    """
    if rounds is None:
        return None
    # ⛔ Dry runs are thrown away BEFORE counting the last N: counting them
    #    would mean that twenty `--dry-run` in a row push out of the window
    #    the last real certification, and the mesh turns red for nothing.
    genuine = [g for g in rounds if not g.get("dry")]
    if not genuine:
        return None
    chunk = genuine[-last_n:]

    grafted = 0
    views = 0
    missed = []
    latest = None
    for g in chunk:
        for m in g.get("meshes") or []:
            if not m.get("fault_grafted"):
                continue
            grafted += 1
            # ⛔ The key must be there AND be true.  ⚠ An ABSENT key is not
            #   «seen»: it is a log older than the field, that is «I do not
            #   know» — and here it counts as «not seen», because a certification
            #   whose outcome is unknown certifies nothing.
            if m.get("saw_the_fault") is True:
                views += 1
                latest = g
            else:
                missed.append((g.get("instant"), m.get("name"),
                                m.get("saw_the_fault")))
    return {"esaminati": len(chunk), "grafted": grafted, "views": views,
            "missed": missed, "latest": latest, "totals": len(genuine),
            "a_vuoto": len(rounds) - len(genuine)}


def age_in_days(instant, t_now):
    """⛔ Returns `None` if it cannot tell — never zero, never an invented number."""
    if not instant:
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
def certify():
    """⛔ We prove that the judge CAN give red, green, and «I do not know»."""

    def cur_round(meshes, dry=False, instant="2026-08-26T05:00:00+02:00"):
        return {"instant": instant, "dry": dry, "meshes": meshes}

    def m(name, fault=False, seen=None, outcome=0):
        d = {"name": name, "outcome": outcome, "fault_grafted": fault}
        if seen is not None:
            d["saw_the_fault"] = seen
        return d

    cases = [
        ("⭐ a fault injected, and the net SAW it",
         [cur_round([m("C1"), m("C8 fault", fault=True, seen=True)])], "green"),

        ("⛔ twenty runs and no fault ever injected",
         [cur_round([m("C1"), m("C11")]) for _ in range(20)], "RED"),

        ("⛔⛔ injected and NOT seen — the worst case",
         [cur_round([m("C8 fault", fault=True, seen=False, outcome=1)])], "RED"),

        # ⭐⭐ THE CASE THAT HOLDS UP THE WHOLE MESH.
        ("⭐⭐ red from ANOTHER mesh certifies nothing",
         [cur_round([m("C1", outcome=1),
                m("C8 fault", fault=True, seen=False, outcome=1)])], "RED"),

        ("⚠ injected, and nothing is known of its outcome (field absent)",
         [cur_round([m("C8 fault", fault=True)])], "RED"),

        ("one successful certification among twenty normal runs ⇒ green",
         [cur_round([m("C1")]) for _ in range(19)]
         + [cur_round([m("C8 fault", fault=True, seen=True)])], "green"),

        ("⛔ the certification slid OUT of the window of twenty",
         [cur_round([m("C8 fault", fault=True, seen=True)])]
         + [cur_round([m("C1")]) for _ in range(20)], "RED"),

        # ⛔ And dry runs must not push out a real certification.
        ("⭐ twenty DRY runs do not push out the real certification",
         [cur_round([m("C8 fault", fault=True, seen=True)])]
         + [cur_round([m("C1")], dry=True) for _ in range(20)], "green"),

        ("⛔ all the runs are dry ⇒ «I do not know», not red",
         [cur_round([m("C8 fault", fault=True, seen=True)], dry=True)], "non lo so"),

        ("⛔ no run ⇒ «I do not know» — that it has never run is said by C12",
         [], "non lo so"),

        ("⛔ unreadable log ⇒ «I do not know», not red",
         None, "non lo so"),
    ]

    print("== certification of the C13 judge ==")
    print("   window in force: last %d REAL runs · dry runs do not count"
          % DEFAULT_LAST_N)
    troubles = 0
    for name, rounds, expected in cases:
        r = judge(rounds, DEFAULT_LAST_N)
        if r is None:
            obtained = "non lo so"
        elif r["views"] >= 1:
            obtained = "green"
        else:
            obtained = "RED"
        ok = obtained == expected
        print("  %s  %-58s  ⇒ %-9s (expected %s)"
              % ("OK " if ok else "NO ", name, obtained, expected))
        if not ok:
            troubles += 1
            print("        (the judge said: %r)" % (r,))

    print()
    if troubles:
        print("⛔ the judge is NOT reliable: %d wrong cases" % troubles)
        return 1
    print("⭐ the judge tells apart the three things that count: never injected ·")
    print("   injected and not seen · injected and seen")
    print("⭐⭐ and ⛔ it does NOT let itself be certified by a red coming from another mesh")
    print("⚠ and this certification covers THE JUDGEMENT, not the injected faults:")
    print("  that they are the RIGHT ones is decided by §3.6, not by me")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--log", default=LOG)
    p.add_argument("--last", type=int, default=DEFAULT_LAST_N,
                   help="how many real runs to look back. `[?]` chosen, not measured")
    p.add_argument("--days", type=int, default=0,
                   help="⚠ if > 0, the age of the last certification becomes "
                        "a JUDGEMENT too. Off by default: §4.2 asks for a "
                        "criterion by counts, not by days")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()

    if a.certify:
        sys.exit(certify())

    rounds, trouble = read_log(a.log)

    print("== C13 — is the certification recent? ==")
    print("   ⛔ the fault it looks for: a net that is no longer able to give")
    print("      red LOOKS THE SAME as a net that finds nothing")
    print("   yardstick: last %d REAL runs  `[?]`  ·  dry runs do not count"
          % a.last)
    if a.days:
        print("   ⚠ and in addition: the last certification within %d days" % a.days)
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

    r = judge(rounds, a.last)
    if r is None:
        print("⛔ no REAL run to look at (%d lines, all dry or none)"
              % len(rounds or []))
        print("   ⇒ I could not look — ⛔ and it is NOT a red")
        return 3

    print("   runs in the log   : %d real, %d dry" % (r["totals"], r["a_vuoto"]))
    print("   looked at         : the last %d" % r["esaminati"])
    print("   injected faults   : %d" % r["grafted"])
    print("   ⭐ seen            : %d" % r["views"])
    t_now = time.time()
    if r["latest"]:
        eta = age_in_days(r["latest"].get("instant"), t_now)
        print("   last successful   : %s  (%s)"
              % (r["latest"].get("instant"),
                 "age unknown" if eta is None else "%.1f days ago" % eta))
    print()

    if r["missed"]:
        print("⛔⛔ AND THESE MESHES HAD A FAULT UNDER THEIR NOSE AND DID NOT")
        print("    SEE IT:")
        for when, name, seen in r["missed"]:
            print("   · %s  ·  %s  (saw_the_fault=%r)" % (when, name, seen))
        print()

    if r["views"] >= 1:
        old = False
        if a.days and r["latest"]:
            eta = age_in_days(r["latest"].get("instant"), t_now)
            if eta is not None and eta > a.days:
                old = True
                print("⛔ RED — the last successful certification is from %.1f days"
                      " ago, and the threshold asked is %d" % (eta, a.days))
        if not old:
            print("⭐ in the last %d runs a fault was injected and IT WAS"
                  " SEEN %d times" % (r["esaminati"], r["views"]))
            print("⚠ and this says the net can still give red ON THE FAULTS IT")
            print("  KNOWS. ⛔ §3.6: the injected faults are faults already known, and")
            print("  every new desktop must come in with **a fault of its own**.")
            if r["missed"]:
                print("⚠ ⛔ but above there is a list of MISSED certifications: they must")
                print("  be looked at, even if this mesh is green.")
            return 0
        return 1

    if r["grafted"] == 0:
        print("⛔⛔ RED — in the last %d runs **no fault was ever"
              " injected**." % r["esaminati"])
        print("   ⇒ the net runs, and nobody puts it to the test. ⛔ From outside it is")
        print("     indistinguishable from a net that works perfectly.")
        print("   ⚠ And the cure is not touching this mesh: it is running the")
        print("     `overall` family, which has the injected fault inside it.")
        return 1

    print("⛔⛔ RED — %d faults were injected and **none was seen**."
          % r["grafted"])
    print("   ⇒ ⛔ it is the worst case of the three: the net is no longer able to")
    print("     give red, and it keeps saying green with the same face.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
