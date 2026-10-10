#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c12 — ⭐⭐ «THE HOOK IS ALIVE» — the mesh that looks at THE NET
===========================================================================

    python3 11-c12-il-gancio-e-vivo.py
    python3 11-c12-il-gancio-e-vivo.py --certifica
    python3 11-c12-il-gancio-e-vivo.py --giorni 3

⛔ This mesh **does not test the product**.  It does not even test the net: it tests
   that the net **is still running**.

---------------------------------------------------------------------------
⛔⛔ THE FAULT IT CATCHES — *the hook switched off silently*
---------------------------------------------------------------------------

`fasi/11…` §4.2 calls it by its full name: ⛔ **«the way these
nets die»**.

And it is worth saying how it really dies, because it does not die with an error:

  · someone redoes the repository, and git's hooks folder **is not copied**;
  · someone has a bad day, comments out the line and forgets;
  · the hook is there, it is installed, ⛔ **and it has not run for three weeks** because the
    installed file points to a path that no longer exists.

⇒ ⭐ In all three cases the net **looks exactly the same as before**:
  the files are there, the meshes are written, `--certifica` passes.  ⛔ And nothing
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
   of those that never give red.  The hook can run `--secco`, that is say
   what it would do without doing it.  ⛔ If a dry run counted as a trace,
   **one `--secco` would be enough to make this mesh say «the hook is alive» for
   a week** — while nothing runs.  ⇒ The lines with `"secco": true` are
   thrown away, and ⭐ **that case is inside `--certifica`**: it is proven, not promised.

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

QUI = os.path.dirname(os.path.abspath(__file__))

# ⛔ The paths are DECLARED here: the hook is «defined by path, not
#    by good will» (§5.1), and this mesh looks at exactly that
#    path — not one it goes looking for.
GANCIO = os.path.join(QUI, "11-gancio.sh")
REGISTRO = os.path.join(QUI, "11-gancio-registro.jsonl")

GIORNI_PREDEFINITI = 7


def leggi_il_registro(percorso):
    """Returns (giri, guaio).

    ⛔ And the cases are THREE, not two, and that is the whole difference:
       (None, "assente")     the file is not there ⇒ ⛔ it is a RED: never ran
       (None, "illeggibile") it is there and does not open ⇒ «I could not look»
       ([...], None)         the runs, in order of writing
    """
    if not os.path.exists(percorso):
        return None, "assente"
    try:
        with open(percorso, "r", errors="replace") as f:
            righe = f.read().splitlines()
    except OSError:
        return None, "illeggibile"
    giri = []
    storte = 0
    for r in righe:
        r = r.strip()
        if not r:
            continue
        try:
            giri.append(json.loads(r))
        except ValueError:
            storte += 1
    # ⚠ Some malformed line happens (a run interrupted half-way through writing) and it is not
    #   a fault.  ⛔ ALL malformed instead means I am not reading a
    #   log: it is «I could not look», not «it never ran».
    if not giri and storte:
        return None, "illeggibile"
    return giri, None


def giudica(stato, giorni):
    """Given the state, says what does NOT hold.

    `stato` is a dictionary:
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
    if stato.get("guaio") == "illeggibile":
        return None

    guai = []
    if not stato.get("c_e"):
        guai.append("the hook is not at the declared path")
        # ⛔ And we return at once: without the file, «not executable» and «not
        #    installed» are consequences, not extra faults.  A list that
        #    counts the same fault three times makes what is simple look serious,
        #    and vice versa.
        return guai
    if not stato.get("eseguibile"):
        guai.append("the hook is there but cannot be executed")
    if not stato.get("installato"):
        guai.append("the hook is NOT installed among git's hooks: "
                    "nobody will start it")

    giri = stato.get("giri")
    if giri is None or not giri:
        guai.append("no trace: the hook has NEVER run")
        return guai

    # ⛔⛔ AND HERE THE DRY RUNS ARE THROWN AWAY.  A `--secco` is not a run: if it
    #    counted, this mesh would say «alive» while nothing runs.
    veri = [g for g in giri if not g.get("secco")]
    if not veri:
        guai.append("there are %d runs, ⛔ but they are ALL dry (--secco): "
                    "the hook has never measured anything" % len(giri))
        return guai

    ultimo = veri[-1]
    quando = ultimo.get("istante")
    eta = eta_in_giorni(quando, stato.get("adesso"))
    if eta is None:
        # ⚠ An instant that cannot be read is not «old»: it is «I do not
        #   know».  ⛔ And here we choose to say it as a fault of the LOG, not
        #   as a dead hook — because it is not the same thing.
        guai.append("the last run does not carry a readable instant (%r): "
                    "the log is malformed" % (quando,))
    elif eta > giorni:
        guai.append("the last real run is from %.1f days ago, and the declared "
                    "threshold is %d" % (eta, giorni))
    return guai


def eta_in_giorni(istante, adesso):
    """⛔ Returns `None` if it cannot tell — never zero, never an invented number."""
    if not istante or adesso is None:
        return None
    try:
        import datetime
        t = datetime.datetime.fromisoformat(istante)
        if t.tzinfo is None:
            t = t.astimezone()
        return (adesso - t.timestamp()) / 86400.0
    except (ValueError, TypeError, OverflowError):
        return None


def ganci_installati():
    """Which git hooks NAME our hook.

    ⛔ It is not enough that the `pre-push` file exists: it must be OURS.  Someone
       else's hook with the same name would make this mesh say «installed»
       while the net does not start.
    """
    try:
        p = subprocess.run(["git", "-C", QUI, "rev-parse", "--git-path", "hooks"],
                           capture_output=True, text=True, timeout=30)
    # ⛔ `subprocess.TimeoutExpired` does NOT descend from `OSError`: without naming it,
    #    a `git` that hangs produced a traceback ⇒ Python exited **1** ⇒ the
    #    hook read RED on a fault of the BENCH (`LEZIONI.md` §1.51).
    #    It is the same cure C10 already has in `radice_del_deposito()`.
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    cartella = p.stdout.strip()
    # ⛔⛔ AND HERE THERE WAS A DEFECT THAT WOULD HAVE MADE THIS MESH USELESS FOR
    #    EVER — `[M]` 26 August 2026, caught by the test bench.
    #
    # `git --git-path` returns a path **relative to the folder given to `-C`**,
    # not to the root of the repository: from `banchi/11-scatole` it answers
    # `../../.git/hooks`.  ⚠ The first draft glued it to the ROOT, and out came
    # a path that does not exist ⇒ ⛔ **«the hook is NOT installed»,
    # always, whatever one did.**
    # ⇒ And a red that cannot be turned green is worse than no
    #   mesh: §1.3 — «a net that gives red for nothing gets switched off by whoever
    #   works».
    if not os.path.isabs(cartella):
        cartella = os.path.normpath(os.path.join(QUI, cartella))
    trovati = []
    for quale in ("pre-commit", "pre-push"):
        d = os.path.join(cartella, quale)
        if not os.path.isfile(d):
            continue
        try:
            with open(d, "r", errors="replace") as f:
                testo = f.read()
        except OSError:
            continue
        if "11-gancio.sh" in testo:
            trovati.append((quale, d, os.access(d, os.X_OK)))
    return trovati


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⛔ We prove that the judge CAN give red, green, and «I do not know»."""
    import datetime
    adesso = time.time()

    def istante(giorni_fa):
        t = datetime.datetime.now().astimezone() - datetime.timedelta(days=giorni_fa)
        return t.isoformat()

    def sano(**cambia):
        s = {"c_e": True, "eseguibile": True, "installato": [("pre-push", "/x", True)],
             "giri": [{"istante": istante(0.5), "secco": False}],
             "guaio": None, "adesso": adesso}
        s.update(cambia)
        return s

    casi = [
        ("the hook is there, it is installed, and it ran yesterday",
         sano(), 0),
        ("⛔ the hook is not there",
         sano(c_e=False, eseguibile=False, installato=[]), 1),
        ("⛔ it is there but is not executable",
         sano(eseguibile=False), 1),
        ("⛔⛔ it is there and it ran, but it is NOT installed — the hook switched off silently",
         sano(installato=[]), 1),
        ("⛔ no log: it has never run",
         sano(giri=None, guaio="assente"), 1),
        ("⛔ empty log: it has never run",
         sano(giri=[]), 1),
        # ⭐⭐ THE CASE THAT MATTERS MOST: the trace is there but does not count.
        ("⭐⭐ the only run is DRY (--secco) ⇒ it must give RED",
         sano(giri=[{"istante": istante(0.1), "secco": True}]), 1),
        ("⭐ a dry run AFTER a real and recent one ⇒ stays GREEN",
         sano(giri=[{"istante": istante(0.5), "secco": False},
                    {"istante": istante(0.1), "secco": True}]), 0),
        ("⛔ the last real run is from twenty days ago (threshold 7)",
         sano(giri=[{"istante": istante(20), "secco": False}]), 1),
        ("⚠ the instant cannot be read: it is the log that is malformed",
         sano(giri=[{"istante": "yesterday morning", "secco": False}]), 1),
        # ⛔ And the third outcome, which is not a red.
        ("⛔ the log is there and cannot be read ⇒ «I do not know», not red",
         sano(guaio="illeggibile"), None),
    ]

    print("== certification of the C12 judge ==")
    print("   threshold in force: %d days · and dry runs do NOT count"
          % GIORNI_PREDEFINITI)
    guai = 0
    for nome, stato, atteso in casi:
        r = giudica(stato, GIORNI_PREDEFINITI)
        # expected: 0 = green · 1 = at least one fault · None = I do not know
        if atteso is None:
            ottenuto = None
        else:
            ottenuto = 0 if (r is not None and not r) else (1 if r else 0)
            if r is None:
                ottenuto = None
        ok = ottenuto == atteso
        print("  %s  %-62s  ⇒ %s (expected %s)"
              % ("OK " if ok else "NO ", nome,
                 "I do not know" if ottenuto is None
                 else ("green" if ottenuto == 0 else "RED"),
                 "I do not know" if atteso is None
                 else ("green" if atteso == 0 else "RED")))
        if not ok:
            guai += 1
            print("        (the judge said: %r)" % (r,))

    print()
    if guai:
        print("⛔ the judge is NOT reliable: %d wrong cases" % guai)
        return 1
    print("⭐ the judge sees the dead hook, sees the disconnected hook,")
    print("   ⭐⭐ and ⛔ is NOT fooled by a dry run")
    print("⚠ and this certification covers THE JUDGEMENT, not the hook: that the")
    print("  hook really runs the meshes is told by C13, not by me")
    return 0


# ═══════════════════════════════════════════════════════════════════════════
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--gancio", default=GANCIO)
    p.add_argument("--registro", default=REGISTRO)
    p.add_argument("--giorni", type=int, default=GIORNI_PREDEFINITI,
                   help="for how many days at most the hook may not have "
                        "run. `[?]` chosen, not measured")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    installati = ganci_installati()
    if installati is None:
        print("⛔ I am not inside a git repository: I do not even know where")
        print("   to look for the hooks")
        print("   ⇒ the terrain does not hold")
        sys.exit(2)

    giri, guaio = leggi_il_registro(a.registro)
    stato = {
        "c_e": os.path.isfile(a.gancio),
        # ⚠ «executable» here means two things together: the bit on the file OR
        #   the possibility of reading it (the project calls it with `bash …`).
        #   ⛔ What MUST have the bit is the file installed inside `.git`,
        #   and that is looked at separately, below.
        "eseguibile": os.access(a.gancio, os.X_OK) or os.access(a.gancio, os.R_OK),
        "installato": installati,
        "giri": giri,
        "guaio": guaio,
        "adesso": time.time(),
    }

    print("== C12 — is the hook alive? ==")
    print("   ⛔ the fault it looks for: the hook switched off silently — the way")
    print("      these nets die (§4.2)")
    print("   declared threshold: last run within %d days  `[?]`" % a.giorni)
    print("   ⛔ and DRY runs (--secco) do not count as a trace\n")

    print("   hook        : %s  %s" % (a.gancio, "is there" if stato["c_e"] else "⛔ IS NOT THERE"))
    if installati:
        for quale, dove, esec in installati:
            print("   installed   : %-11s %s%s"
                  % (quale, dove, "" if esec else "  ⛔ not executable"))
    else:
        print("   installed   : ⛔ nowhere")
    if guaio == "assente":
        print("   log         : ⛔ IS NOT THERE — the hook has never run")
    elif guaio == "illeggibile":
        print("   log         : ⚠ it is there and cannot be read")
    else:
        veri = [g for g in giri if not g.get("secco")]
        print("   log         : %d runs (%d real, %d dry)"
              % (len(giri), len(veri), len(giri) - len(veri)))
        if veri:
            eta = eta_in_giorni(veri[-1].get("istante"), stato["adesso"])
            print("   last run    : %s  (%s)"
                  % (veri[-1].get("istante"),
                     "age unknown" if eta is None else "%.1f days ago" % eta))
    print()

    r = giudica(stato, a.giorni)
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
          % a.giorni)
    print("⚠ and this mesh says the hook RUNS, ⛔ not that the net can")
    print("  still give red: that is C13.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
