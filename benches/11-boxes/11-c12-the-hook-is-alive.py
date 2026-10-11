#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c12 — ⭐⭐ «THE HOOK IS ALIVE» — the mesh that looks at THE NET
===========================================================================

    python3 11-c12-the-hook-is-alive.py
    python3 11-c12-the-hook-is-alive.py --certify
    python3 11-c12-the-hook-is-alive.py --days 3

⛔ This mesh **does not test the product**.  It does not even test the net: it tests
   that the net **is still running**.

---------------------------------------------------------------------------
⛔⛔ THE FAULT IT CATCHES — *the hook switched off silently*
---------------------------------------------------------------------------

`phases/11…` §4.2 calls it by its full name: ⛔ **«the way these
nets die»**.

And it is worth saying how it really dies, because it does not die with an error:

  · someone redoes the repository, and git's hooks folder **is not copied**;
  · someone has a bad day, comments out the line and forgets;
  · the hook is there, it is installed, ⛔ **and it has not run for three weeks** because the
    installed file points to a path that no longer exists.

⇒ ⭐ In all three cases the net **looks exactly the same as before**:
  the files are there, the meshes are written, `--certify` passes.  ⛔ And nothing
  runs any more.

---------------------------------------------------------------------------
⭐ THE FIVE THINGS IT LOOKS AT — and none is «the file is there» and that is all
---------------------------------------------------------------------------

  1  the hook **exists** at the declared path
  2  the hook can be **executed**
  3  it is **installed** as a git hook — ⛔ and the installed file NAMES the
     hook: an installed hook that points elsewhere is worse than none
  4  there is a **trace** that it ran: the log exists and has at least one run
  5  ⛔⛔ and the last run is **NOT a dry run**

⚠⚠ The fifth deserves two lines, because without it this mesh would be one
   of those that never give red.  The hook can run `--dry-run`, that is say
   what it would do without doing it.  ⛔ If a dry run counted as a trace,
   **one `--dry-run` would be enough to make this mesh say «the hook is alive» for
   a week** — while nothing runs.  ⇒ The lines with `"dry": true` are
   thrown away, and ⭐ **that case is inside `--certify`**: it is proven, not promised.

---------------------------------------------------------------------------
⚠ THE THRESHOLD, declared and printed in every outcome
---------------------------------------------------------------------------

`[?]` **7 days.**  ⛔ It is chosen, not measured: nobody has yet observed
how often this repository is touched.  ⇒ It must be replaced with an `[M]` as soon as
the log has enough lines to say how often the hook really
fires.  ⚠ Until then, a red on this threshold must be **read** before
being believed.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ the hook is there, it is installed, and it really ran recently
  1  ⛔ one of the five things does not hold ⇒ red
  3  ⛔ I could not look — the log is there but cannot be read
     (⛔ and it is NOT a red: «the log is not there» instead **is**, because
      it means the hook has never run)
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))

# ⛔ The paths are DECLARED here: the hook is «defined by path, not
#    by good will» (§5.1), and this mesh looks at exactly that
#    path — not one it goes looking for.
HOOK = os.path.join(HERE, "11-hook.sh")
LOG = os.path.join(HERE, "11-gancio-registro.jsonl")

# ── the runs written before the English rename (DECISIONI §10.38) keep the Italian words, and
#    11-gancio-registro.jsonl is append-only: old Italian rows, then new ones.  The first tuple
#    is protected (english-migration/protetti.tsv), the second is renamed with the code: after
#    the rename OLD_SPELLING maps every old word to the code's own, before it is empty.  Same
#    order in both, one word per position.  Only the words this file reads from a run.
_OLD_WORDS = (
    "istante", "secco",
)  # end of the old words
_WORDS_NOW = (
    "instant", "dry",
)
OLD_SPELLING = {a: b for a, b in zip(_OLD_WORDS, _WORDS_NOW) if a != b}


def current_spelling(x):
    """A record of an old register in the code's spelling: keys, and string values equal to a word."""
    if isinstance(x, dict):
        return {OLD_SPELLING.get(k, k): current_spelling(v) for k, v in x.items()}
    if isinstance(x, list):
        return [current_spelling(v) for v in x]
    return OLD_SPELLING.get(x, x) if isinstance(x, str) else x


DEFAULT_DAYS = 7


def read_log(fpath):
    """Returns (giri, guaio).

    ⛔ And the cases are THREE, not two, and that is the whole difference:
       (None, "assente")     the file is not there ⇒ ⛔ it is a RED: never ran
       (None, "illeggibile") it is there and does not open ⇒ «I could not look»
       ([...], None)         the runs, in order of writing
    """
    if not os.path.exists(fpath):
        return None, "assente"
    try:
        with open(fpath, "r", errors="replace") as f:
            lines = f.read().splitlines()
    except OSError:
        return None, "illeggibile"
    rounds = []
    skewed = 0
    for r in lines:
        r = r.strip()
        if not r:
            continue
        try:
            rounds.append(current_spelling(json.loads(r)))
        except ValueError:
            skewed += 1
    # ⚠ Some malformed line happens (a run interrupted half-way through writing) and it is not
    #   a fault.  ⛔ ALL malformed instead means I am not reading a
    #   log: it is «I could not look», not «it never ran».
    if not rounds and skewed:
        return None, "illeggibile"
    return rounds, None


def judge(state, days):
    """Given the state, says what does NOT hold.

    `state` is a dictionary:
       c_e            the hook file exists
       eseguibile     it can be executed
       installato     the list of git hooks that NAME our hook
       giri           the list of runs read from the log, or None
       guaio          «assente» · «illeggibile» · None
       adesso         the instant, in seconds

    ⛔ Returns `None` for «I could not look», and a LIST (possibly empty)
       when it looked.  ⚠ `None` is not the empty list: «I did not look» and
       «I looked and everything is fine» are two different things, and this project has
       already paid for confusing them.
    """
    if state.get("trouble") == "illeggibile":
        return None

    troubles = []
    if not state.get("c_e"):
        troubles.append("the hook is not at the declared path")
        # ⛔ And we return at once: without the file, «not executable» and «not
        #    installed» are consequences, not extra faults.  A list that
        #    counts the same fault three times makes what is simple look serious,
        #    and vice versa.
        return troubles
    if not state.get("executable"):
        troubles.append("the hook is there but cannot be executed")
    if not state.get("installed"):
        troubles.append("the hook is NOT installed among git's hooks: "
                    "nobody will start it")

    rounds = state.get("rounds")
    if rounds is None or not rounds:
        troubles.append("no trace: the hook has NEVER run")
        return troubles

    # ⛔⛔ AND HERE THE DRY RUNS ARE THROWN AWAY.  A `--dry-run` is not a run: if it
    #    counted, this mesh would say «alive» while nothing runs.
    genuine = [g for g in rounds if not g.get("dry")]
    if not genuine:
        troubles.append("there are %d runs, ⛔ but they are ALL dry (--dry-run): "
                    "the hook has never measured anything" % len(rounds))
        return troubles

    last = genuine[-1]
    when = last.get("instant")
    eta = age_in_days(when, state.get("t_now"))
    if eta is None:
        # ⚠ An instant that cannot be read is not «old»: it is «I do not
        #   know».  ⛔ And here we choose to say it as a fault of the LOG, not
        #   as a dead hook — because it is not the same thing.
        troubles.append("the last run does not carry a readable instant (%r): "
                    "the log is malformed" % (when,))
    elif eta > days:
        troubles.append("the last real run is from %.1f days ago, and the declared "
                    "threshold is %d" % (eta, days))
    return troubles


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


def installed_hooks():
    """Which git hooks NAME our hook.

    ⛔ It is not enough that the `pre-push` file exists: it must be OURS.  Someone
       else's hook with the same name would make this mesh say «installed»
       while the net does not start.
    """
    try:
        p = subprocess.run(["git", "-C", HERE, "rev-parse", "--git-path", "hooks"],
                           capture_output=True, text=True, timeout=30)
    # ⛔ `subprocess.TimeoutExpired` does NOT descend from `OSError`: without naming it,
    #    a `git` that hangs produced a traceback ⇒ Python exited **1** ⇒ the
    #    hook read RED on a fault of the BENCH (`LESSONS.md` §1.51).
    #    It is the same cure C10 already has in `repo_root()`.
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    folder = p.stdout.strip()
    # ⛔⛔ AND HERE THERE WAS A DEFECT THAT WOULD HAVE MADE THIS MESH USELESS FOR
    #    EVER — `[M]` 26 August 2026, caught by the test bench.
    #
    # `git --git-path` returns a path **relative to the folder given to `-C`**,
    # not to the root of the repository: from `benches/11-boxes` it answers
    # `../../.git/hooks`.  ⚠ The first draft glued it to the ROOT, and out came
    # a path that does not exist ⇒ ⛔ **«the hook is NOT installed»,
    # always, whatever one did.**
    # ⇒ And a red that cannot be turned green is worse than no
    #   mesh: §1.3 — «a net that gives red for nothing gets switched off by whoever
    #   works».
    if not os.path.isabs(folder):
        folder = os.path.normpath(os.path.join(HERE, folder))
    matches = []
    for which in ("pre-commit", "pre-push"):
        d = os.path.join(folder, which)
        if not os.path.isfile(d):
            continue
        try:
            with open(d, "r", errors="replace") as f:
                text = f.read()
        except OSError:
            continue
        if "11-hook.sh" in text:
            matches.append((which, d, os.access(d, os.X_OK)))
    return matches


# ═══════════════════════════════════════════════════════════════════════════
def certify():
    """⛔ We prove that the judge CAN give red, green, and «I do not know»."""
    import datetime
    t_now = time.time()

    def instant(days_ago):
        t = datetime.datetime.now().astimezone() - datetime.timedelta(days=days_ago)
        return t.isoformat()

    def healthy(**change):
        s = {"c_e": True, "executable": True, "installed": [("pre-push", "/x", True)],
             "rounds": [{"instant": instant(0.5), "dry": False}],
             "trouble": None, "t_now": t_now}
        s.update(change)
        return s

    cases = [
        ("the hook is there, it is installed, and it ran yesterday",
         healthy(), 0),
        ("⛔ the hook is not there",
         healthy(c_e=False, executable=False, installed=[]), 1),
        ("⛔ it is there but is not executable",
         healthy(executable=False), 1),
        ("⛔⛔ it is there and it ran, but it is NOT installed — the hook switched off silently",
         healthy(installed=[]), 1),
        ("⛔ no log: it has never run",
         healthy(rounds=None, trouble="assente"), 1),
        ("⛔ empty log: it has never run",
         healthy(rounds=[]), 1),
        # ⭐⭐ THE CASE THAT MATTERS MOST: the trace is there but does not count.
        ("⭐⭐ the only run is DRY (--dry-run) ⇒ it must give RED",
         healthy(rounds=[{"instant": instant(0.1), "dry": True}]), 1),
        ("⭐ a dry run AFTER a real and recent one ⇒ stays GREEN",
         healthy(rounds=[{"instant": instant(0.5), "dry": False},
                    {"instant": instant(0.1), "dry": True}]), 0),
        ("⛔ the last real run is from twenty days ago (threshold 7)",
         healthy(rounds=[{"instant": instant(20), "dry": False}]), 1),
        ("⚠ the instant cannot be read: it is the log that is malformed",
         healthy(rounds=[{"instant": "yesterday morning", "dry": False}]), 1),
        # ⛔ And the third outcome, which is not a red.
        ("⛔ the log is there and cannot be read ⇒ «I do not know», not red",
         healthy(trouble="illeggibile"), None),
    ]

    print("== certification of the C12 judge ==")
    print("   threshold in force: %d days · and dry runs do NOT count"
          % DEFAULT_DAYS)
    troubles = 0
    for name, state, expected in cases:
        r = judge(state, DEFAULT_DAYS)
        # expected: 0 = green · 1 = at least one fault · None = I do not know
        if expected is None:
            obtained = None
        else:
            obtained = 0 if (r is not None and not r) else (1 if r else 0)
            if r is None:
                obtained = None
        ok = obtained == expected
        print("  %s  %-62s  ⇒ %s (expected %s)"
              % ("OK " if ok else "NO ", name,
                 "I do not know" if obtained is None
                 else ("green" if obtained == 0 else "RED"),
                 "I do not know" if expected is None
                 else ("green" if expected == 0 else "RED")))
        if not ok:
            troubles += 1
            print("        (the judge said: %r)" % (r,))

    print()
    if troubles:
        print("⛔ the judge is NOT reliable: %d wrong cases" % troubles)
        return 1
    print("⭐ the judge sees the dead hook, sees the disconnected hook,")
    print("   ⭐⭐ and ⛔ is NOT fooled by a dry run")
    print("⚠ and this certification covers THE JUDGEMENT, not the hook: that the")
    print("  hook really runs the meshes is told by C13, not by me")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--hook", default=HOOK)
    p.add_argument("--log", default=LOG)
    p.add_argument("--days", type=int, default=DEFAULT_DAYS,
                   help="for how many days at most the hook may not have "
                        "run. `[?]` chosen, not measured")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()

    if a.certify:
        sys.exit(certify())

    installs = installed_hooks()
    if installs is None:
        print("⛔ I am not inside a git repository: I do not even know where")
        print("   to look for the hooks")
        print("   ⇒ the terrain does not hold")
        sys.exit(2)

    rounds, trouble = read_log(a.log)
    state = {
        "c_e": os.path.isfile(a.hook),
        # ⚠ «executable» here means two things together: the bit on the file OR
        #   the possibility of reading it (the project calls it with `bash …`).
        #   ⛔ What MUST have the bit is the file installed inside `.git`,
        #   and that is looked at separately, below.
        "executable": os.access(a.hook, os.X_OK) or os.access(a.hook, os.R_OK),
        "installed": installs,
        "rounds": rounds,
        "trouble": trouble,
        "t_now": time.time(),
    }

    print("== C12 — is the hook alive? ==")
    print("   ⛔ the fault it looks for: the hook switched off silently — the way")
    print("      these nets die (§4.2)")
    print("   declared threshold: last run within %d days  `[?]`" % a.days)
    print("   ⛔ and DRY runs (--dry-run) do not count as a trace\n")

    print("   hook        : %s  %s" % (a.hook, "is there" if state["c_e"] else "⛔ IS NOT THERE"))
    if installs:
        for which, dove, exec_ctx in installs:
            print("   installed   : %-11s %s%s"
                  % (which, dove, "" if exec_ctx else "  ⛔ not executable"))
    else:
        print("   installed   : ⛔ nowhere")
    if trouble == "assente":
        print("   log         : ⛔ IS NOT THERE — the hook has never run")
    elif trouble == "illeggibile":
        print("   log         : ⚠ it is there and cannot be read")
    else:
        genuine = [g for g in rounds if not g.get("dry")]
        print("   log         : %d runs (%d real, %d dry)"
              % (len(rounds), len(genuine), len(rounds) - len(genuine)))
        if genuine:
            eta = age_in_days(genuine[-1].get("instant"), state["t_now"])
            print("   last run    : %s  (%s)"
                  % (genuine[-1].get("instant"),
                     "age unknown" if eta is None else "%.1f days ago" % eta))
    print()

    r = judge(state, a.days)
    if r is None:
        print("⛔ the log is there and cannot be read.")
        print("   ⇒ I could not look — ⛔ and it is NOT a red")
        return 3
    if r:
        print("⛔⛔ RED — the hook is not alive:")
        for g in r:
            print("   · %s" % g)
        print()
        print("   ⇒ ⛔ and as long as it is like this, **all the rest of the net is useless**:")
        print("     the meshes can be perfect, if nobody starts them")
        print("     they catch nothing.")
        return 1
    print("⭐ the hook is there, it is installed, and it really ran within %d days"
          % a.days)
    print("⚠ and this mesh says the hook RUNS, ⛔ not that the net can")
    print("  still give red: that is C13.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
