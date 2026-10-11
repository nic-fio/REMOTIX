#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c19 — ⭐⭐ «AT THE END OF THE RUN NO TENANT OF THE NET SURVIVES»
===========================================================================

    python3 11-c19-the-box-stays-clean.py
    python3 11-c19-the-box-stays-clean.py --leave-a-tenant
    python3 11-c19-the-box-stays-clean.py --leave-a-home
    python3 11-c19-the-box-stays-clean.py --dirty-too
    python3 11-c19-the-box-stays-clean.py --certify

    what must be true         : when the net has finished working in a
                                box, **nobody from the net stays
                                inside**: no live tenant, no
                                home of theirs, no process of theirs
    where it starts from      : from the box AS IT IS — ⛔ this mesh
                                prepares nothing and cleans nothing before
                                looking.  ⭐ It is the only one of the list that
                                judges **the work of the others**
    what it looks at          : three facts, each with its own name
      U  users      `/etc/passwd` has no name of the net's
                    name space
      C  homes      `/home` has no folder with those names (⛔ the
                    `userdel` without `-r`, which removes the user and leaves the home)
      P  processes  no process runs on behalf of one of those names
    how I know it can give red: `--leave-a-tenant` (a user of the net
                                alive, with their home and a process of theirs) ·
                                `--leave-a-home` (⭐ only the home, the user
                                not: the leftover no `pgrep` sees)

---------------------------------------------------------------------------
⛔⛔ WHY IT EXISTS — 23 September 2026, `phases/13-xfce.md` «What remains»
---------------------------------------------------------------------------

The clear-out already exists (`11-hook.sh`, `clear_out_tenants`, 22 Sep 2026):
after every mesh the hook goes over the net's name space and removes
users, homes, failed `user@` units and `/tmp` orphans.  ⭐ What was missing
is the **VERDICT**: today `balance_after` writes *«the BOX got dirty»*
as an `inf` line, annotated `succeeded=true`.

⇒ ⛔ **The net can leave twenty tenants inside a box and declare itself
  green all the same.**  This mesh is the line that says no.

⚠ And it is not a textbook case: `[M]` 22 Sep 2026, after `--family all`,
  22-24 live tenants in each of the three boxes, with their `/home`, plus
  failed `user@…` units and orphans in `/tmp`.  ⇒ And what accumulates BREAKS
  the meshes: the bisection of 21 Sep 2026 (C17 red on gnome and kde)
  showed that the state accumulated by the box makes the product be accused of
  a red that is not its own.

---------------------------------------------------------------------------
⛔⛔⛔ THE PITFALL, AND IT IS CALLED `nictest` — declared because it is the only thing
      that, done wrong, would turn this mesh into a generator of false reds
---------------------------------------------------------------------------

`11-start.sh balance` counts tenants **by uid**:

    getent passwd | awk -F: '$3 >= 1000 && $3 < 60000 && $1 != "provanic"'

⇒ ⛔ It excludes **only** `provanic`.  For that count `nictest` — the user of the
  manual tests, who **is in the boxes on purpose** and must stay there — is a
  tenant, and a mesh built on that count would say red every time
  the user has a session open.  ⚠ A false red, in a safety net,
  always ends the same way: the net gets switched off by whoever works.

⭐⭐ THE CURE: **count by NAME, not by uid** — and the name is the one the
    hook itself uses to clear out (`clear_out_tenants`):

        ^c[0-9]+b?u[0-9]+$        c1u1 · c3u2 · c8bu5 · c17u931 · c20u407

  ⇒ It is the **net's name space**: whoever is inside it is the net's stuff and
    must be removed; whoever is outside is not mine to judge.  `nictest`, `provanic`,
    `root` and all system users do not fall into it **by shape**,
    not by a list of exceptions someone will have to remember to update.

⚠ And there is the price, declared: a bench that names its tenant **outside**
  the name space (`[M]` 23 Sep 2026, in gnome: `corrx1`, `corrx2` of
  `12-real-clients.py`; and the old `13-w4` called it `w4u$$`) ⛔ is not
  seen by this mesh **and is not cleared out by the hook**: they are the same
  gap, not two.  ⇒ Here they are PRINTED as a finding, so whoever reads sees them,
  ⛔ and it is closed at the root by giving new benches a name of the net — it is the
  reason C20 names its tenant `c20u<n>`.

---------------------------------------------------------------------------
⭐ WHAT IT JUDGES AND WHAT NOT, and why the boundary is there
---------------------------------------------------------------------------

⭐ **VERDICT** on the three facts U · C · P: they are *«a tenant of the net
   survives»*, that is the exact sentence this mesh carries in its name.

⚠ **FINDING, not verdict** (printed with the numbers, ⛔ it does not make red):
     · the failed `user@N.service` units whose uid no longer has a name
     · the ownerless `/tmp` entries
     · the `logind` sessions without a user
   ⇒ They are **the tenants' rubbish, not the tenants**.  Making them a red
     would mean that one file forgotten in `/tmp` by a bench of
     another phase is enough to keep the net red for ever — and a perpetual red
     is not a mesh, it is a switch someone will turn off
     (`LESSONS.md` §1.49).
   ⭐ And whoever wants to measure it that day asks for it by name: `--dirty-too`
     promotes the finding to a verdict.  ⛔ The net does NOT pass it.

Outcomes: 0 green · 1 red · 3 I could not look (⛔ it is NOT a red).
⛔ With an injected fault it reads THE OTHER WAY ROUND: 0 = the fault was SEEN.
"""
import argparse
import os
import random
import re
import subprocess
import sys
import time

# ⭐⭐ THE NET'S NAME SPACE, in one place only — and it is THE SAME one that
#    `11-hook.sh` (`clear_out_tenants`) uses to clear out.
#    ⛔ If the two diverge, the hook removes one thing and this mesh
#      judges another: see `LESSONS.md` §1.46.
MODEL = re.compile(r"^c[0-9]+b?u[0-9]+$")

# ⚠ The service users who are in the boxes ON PURPOSE.  ⛔ It is not the
#   rule — the rule is the pattern above, and they do not fall into it
#   by shape.  This list only serves to PRINT them, so whoever reads sees that
#   the distinction was made and not forgotten.
SERVICE_PROCESSES = {
    "provanic": "the benches' test user (the recipe puts it there)",
    "nictest":  "⭐ the user of the MANUAL tests: it is in the boxes on purpose, "
                "and this mesh neither touches nor counts it",
}


def run_loop(argv, time_limit=30):
    """A command, or `None` if it did not answer.  ⛔ It never raises."""
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=time_limit)
    except (subprocess.TimeoutExpired, OSError):
        return None


def shell(line, time_limit=30):
    try:
        return subprocess.run(["/bin/sh", "-c", line], capture_output=True,
                              text=True, timeout=time_limit)
    except (subprocess.TimeoutExpired, OSError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE FACTS — they are read from the machine, and each returns `None` when it
#   could not be read.  ⛔ `None` is not «empty»: empty is a green, `None`
#   is an «I could not look».
# ═══════════════════════════════════════════════════════════════════════════
def all_users():
    """[(name, uid)] of `/etc/passwd`, or `None`."""
    r = run_loop(["getent", "passwd"], 20)
    if r is None or r.returncode != 0:
        return None
    report = []
    for line in (r.stdout or "").splitlines():
        pieces = line.split(":")
        if len(pieces) < 3:
            continue
        try:
            report.append((pieces[0], int(pieces[2])))
        except ValueError:
            continue
    return report


def case_in(folder="/home"):
    """The names of the folders of `/home`, or `None`."""
    try:
        return sorted(os.listdir(folder))
    except OSError:
        return None


def processes_of(names):
    """{name: [pid…]} for the given names.  ⛔ It asks `pgrep -u`, which looks at
       the REAL uid: ⚠ a `pkill -f` on the name would also catch the shell that
       is running it (`LESSONS.md`, 22 Sep 2026: the shell was killing
       itself), and here nothing needs killing — it needs COUNTING."""
    report = {}
    for n in names:
        r = run_loop(["pgrep", "-u", n], 15)
        if r is None:
            continue
        pid = [x for x in (r.stdout or "").split() if x.isdigit()]
        if pid:
            report[n] = pid
    return report


def box_dirt(known):
    """⚠ FINDING: the rubbish, not the tenants.  `known` = the uids that in
       `/etc/passwd` still have a name."""
    unit, orphans, sessions = [], [], []
    r = run_loop(["systemctl", "--failed", "--no-legend", "--plain"], 30)
    if r is not None:
        for line in (r.stdout or "").splitlines():
            m = re.match(r"^\s*user@(\d+)\.service", line)
            if m and int(m.group(1)) not in known:
                unit.append(m.group(1))
    r = shell("find /tmp -mindepth 1 -maxdepth 1 -nouser 2>/dev/null", 30)
    if r is not None:
        orphans = [x for x in (r.stdout or "").splitlines() if x.strip()]
    r = run_loop(["loginctl", "list-sessions", "--no-legend"], 20)
    if r is not None:
        for line in (r.stdout or "").splitlines():
            pieces = line.split()
            if len(pieces) >= 3 and pieces[1].isdigit() and int(pieces[1]) not in known:
                sessions.append(pieces[0])
    return unit, orphans, sessions


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE JUDGEMENT — a PURE function: no file reading, no command.
#   ⇒ `--certify` goes through it without touching either the machine or the product.
# ═══════════════════════════════════════════════════════════════════════════
def judgment(users, case, processes, dirty=None):
    """⭐ (esito, U, C, P, perche) from the FACTS already gathered.

    `users` [(name, uid)] of the whole machine · `case` the names in `/home` ·
    `processes` {name: [pid…]} · `dirty` (units, orphans, sessions) or
    `None` when the dirt does NOT enter the verdict (the net's mode).
    """
    if users is None or case is None:
        return 3, "?", "?", "?", ("I could not read %s: without it I do not "
                                  "know who stayed inside"
                                  % ("/etc/passwd" if users is None else "/home"))

    net_users = sorted(n for n, _ in users if MODEL.match(n))
    case_network = sorted(n for n in case if MODEL.match(n))
    net_procs = sorted(n for n in processes if MODEL.match(n))

    accusations = []
    if net_users:
        accusations.append("in /etc/passwd %d tenants of the net survive: %s"
                      % (len(net_users), " ".join(net_users)))
    if case_network:
        accusations.append("in /home %d homes of the net remain: %s"
                      % (len(case_network), " ".join(case_network)))
    if net_procs:
        accusations.append("processes of %s are still running"
                      % ", ".join("%s (%d)" % (n, len(processes[n]))
                                  for n in net_procs))
    # ⚠ The dirt enters ONLY if the caller asked for it (`--dirty-too`).
    if dirty is not None:
        unit, orphans, sessions = dirty
        if unit:
            accusations.append("%d failed user@ units no longer with a user: %s"
                          % (len(unit), " ".join(unit[:8])))
        if orphans:
            accusations.append("%d ownerless /tmp entries: %s"
                          % (len(orphans), " ".join(orphans[:5])))
        if sessions:
            accusations.append("%d logind sessions without a user" % len(sessions))

    u = "NO" if net_users else "SI"
    c = "NO" if case_network else "SI"
    p = "NO" if net_procs else "SI"
    if accusations:
        return 1, u, c, p, "; ".join(accusations)
    return 0, u, c, p, ("nobody from the net stayed inside: 0 tenants, "
                        "0 homes, 0 processes")


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE INJECTED FAULTS — they are injected into the BOX, and always removed.
#
# ⭐ They carry a name of the net's name space on purpose: if this run
#   dies half-way, the hook clears them out by itself at the next mesh.  ⛔ A bench
#   that leaves leftovers while measuring leftovers would be a joke.
# ═══════════════════════════════════════════════════════════════════════════
def graft_tenant(chi):
    """⛔ A LIVE tenant of the net: user + home + a process of theirs."""
    r = run_loop(["useradd", "-m", "-s", "/bin/bash", chi], 60)
    if r is None or r.returncode != 0:
        return False, "useradd did not succeed"
    # ⚠ `setsid` and stdin on /dev/null, like C3's scene: a child left
    #   in the terminal's process group ends up stopped in `T`.
    shell("setsid runuser -u %s -- sleep 600 < /dev/null > /dev/null 2>&1 &"
           % chi, 20)
    for _ in range(20):
        r = run_loop(["pgrep", "-u", chi], 10)
        if r is not None and r.returncode == 0:
            return True, ""
        time.sleep(0.25)
    return True, "⚠ the user is there but their process was not seen"


def graft_home(chi):
    """⛔ ONLY the home: the user not.  It is the `userdel` without `-r`, that is the
       leftover no `pgrep` and no `getent passwd` see."""
    try:
        os.makedirs(os.path.join("/home", chi), exist_ok=True)
        with open(os.path.join("/home", chi, ".c19"), "w") as f:
            f.write("leftover injected by C19\n")
        return True, ""
    except OSError as e:
        return False, "I could not make /home/%s: %s" % (chi, e)


def remove_fault(chi):
    """⭐ Always, and without asking."""
    run_loop(["loginctl", "terminate-user", chi], 20)
    run_loop(["pkill", "-KILL", "-u", chi], 10)
    time.sleep(0.3)
    run_loop(["userdel", "-r", chi], 30)
    shell("rm -rf /home/%s" % chi, 20)


# ═══════════════════════════════════════════════════════════════════════════
def certify():
    """⛔ Can the mesh give red, and can it NOT give it? It is tested on the JUDGEMENT."""
    troubles = 0
    system_wide = [("root", 0), ("daemon", 1), ("systemd-network", 998)]
    service = [("provanic", 4011), ("nictest", 4012)]
    cases = [
        ("⭐ clean box (only provanic and nictest are there) ⇒ GREEN",
         (system_wide + service, ["provanic", "nictest", "lost+found"], {}, None), 0),
        ("⛔ a tenant of the net survives ⇒ RED",
         (system_wide + service + [("c3u2", 4013)],
          ["provanic", "nictest", "c3u2"], {"c3u2": ["991"]}, None), 1),
        ("⛔ the user is gone but the HOME is not (userdel without -r) ⇒ RED",
         (system_wide + service, ["provanic", "nictest", "c8bu5"], {}, None), 1),
        ("⛔ user and home gone, a PROCESS of theirs is alive ⇒ RED",
         (system_wide + service, ["provanic", "nictest"], {"c17u931": ["4"]}, None), 1),
        ("⛔ twenty tenants of the net, like on 22 Sep ⇒ RED",
         (system_wide + service + [("c%du1" % i, 4020 + i) for i in range(20)],
          ["provanic", "nictest"], {}, None), 1),
        ("⭐⭐ nictest alive, with its home AND a process of its own ⇒ GREEN "
         "(⛔ the pitfall: `bilancio` would count it)",
         (system_wide + service, ["provanic", "nictest"],
          {"nictest": ["101", "102", "103"]}, None), 0),
        ("⭐ provanic with its home and its processes ⇒ GREEN",
         (system_wide + service, ["provanic", "nictest"],
          {"provanic": ["77"]}, None), 0),
        ("⚠ a user OUTSIDE the name space (corrx1) ⇒ GREEN: "
         "not mine to judge, it is printed and that is all",
         (system_wide + service + [("corrx1", 4013)],
          ["provanic", "nictest", "corrx1"], {"corrx1": ["55"]}, None), 0),
        ("⚠ only DIRT (failed units and /tmp orphans) ⇒ GREEN: "
         "it is rubbish, not a tenant",
         (system_wide + service, ["provanic", "nictest"], {}, None), 0),
        ("⭐ the same dirt, but asked for with the verdict (--dirty-too) ⇒ RED",
         (system_wide + service, ["provanic", "nictest"], {},
          (["4023", "4024"], ["/tmp/mozilla"], [])), 1),
        ("⚠ /etc/passwd cannot be read ⇒ 3, ⛔ never a red",
         (None, ["provanic"], {}, None), 3),
        ("⚠ /home cannot be read ⇒ 3, ⛔ never a red",
         (system_wide + service, None, {}, None), 3),
    ]
    print("== C19 — certification of the judgement (⛔ without touching the box)")
    for name, call_args, expected in cases:
        e = judgment(*call_args)[0]
        if e != expected:
            troubles += 1
        print("  %s %-78s outcome %s (expected %s)"
              % ("OK " if e == expected else "NO ", name, e, expected))

    # ⭐ And the pattern is tested by NAME, not by trust: it is the only thing that
    #   separates a tenant of the net from `nictest`.
    name_cases = [("c1u1", True), ("c3u2", True), ("c8bu5", True),
                  ("c17u931", True), ("c20u407", True), ("c19u100", True),
                  ("nictest", False), ("provanic", False), ("root", False),
                  ("corrx1", False), ("w4u12345", False), ("ki9", False),
                  ("c1u1x", False), ("xc1u1", False)]
    for name, expected in name_cases:
        got = bool(MODEL.match(name))
        if got != expected:
            troubles += 1
        print("  %s the net's name space: %-12s ⇒ %s (expected %s)"
              % ("OK " if got == expected else "NO ", name,
                 "the net's" if got else "not mine",
                 "the net's" if expected else "not mine"))
    print()
    if troubles:
        print("⛔ %d cases of the judgement do NOT give what they must" % troubles)
        return 1
    print("⭐ the judgement gives green, red and «I do not know» where it must — and ⭐ "
          "`nictest` with its home, its processes and its\n   session "
          "stays a GREEN, which is the only way for this mesh to be "
          "useful instead of a nuisance")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--port", type=int, default=0,
                   help="⚠ not needed: this mesh does not talk to the product. "
                        "It is there because the hook calls all the meshes the "
                        "same way")
    p.add_argument("--leave-a-tenant", action="store_true",
                   help="⛔ THE INJECTED FAULT: a live user of the net, "
                        "with their home and a process of theirs")
    p.add_argument("--leave-a-home", action="store_true",
                   help="⛔ THE INJECTED FAULT, the other one: ONLY the home, "
                        "the user not (the `userdel` without `-r`)")
    p.add_argument("--dirty-too", action="store_true",
                   help="⚠ promotes to VERDICT the failed units and the orphans "
                        "of /tmp.  ⛔ The net does not pass it: see at the top")
    p.add_argument("--homes", default="/home")
    p.add_argument("--certify", action="store_true")
    a = p.parse_args()

    if a.certify:
        return certify()
    if os.geteuid() != 0:
        print("⛔ it wants the administrator (it reads everyone's units and "
              "processes) ⇒ I could not look")
        return 3

    grafted = ""
    if a.leave_a_tenant:
        grafted = " ⛔ INJECTED FAULT: --leave-a-tenant"
    elif a.leave_a_home:
        grafted = " ⛔ INJECTED FAULT: --leave-a-home"
    chi = "c19u%d" % random.randint(100, 999)
    print("== C19 — at the end of the run no tenant of the net survives%s"
          % grafted)

    fault_who = None
    try:
        if a.leave_a_tenant or a.leave_a_home:
            fault_who = chi
            remove_fault(chi)
            if a.leave_a_tenant:
                completed, note = graft_tenant(chi)
            else:
                completed, note = graft_home(chi)
            if not completed:
                print("   ⛔ I could not inject the fault (%s) ⇒ I could "
                      "not look" % note)
                return 3
            print("   ⛔ injected: %s%s" % (chi, (" — " + note) if note else ""))

        users = all_users()
        case = case_in(a.homes)
        if users is None or case is None:
            outcome, u, c, pf, why = judgment(users, case, {}, None)
            print("   ⚠ %s" % why)
            return 3

        net_users = sorted(n for n, _ in users if MODEL.match(n))
        processes = processes_of(net_users + sorted(SERVICE_PROCESSES))
        known = set(uid for _, uid in users)
        dirty = box_dirt(known)

        # ── what I do NOT count, printed: the distinction shows ──
        report = sorted(n for n, uid in users
                       if 1000 <= uid < 60000 and not MODEL.match(n)
                       and n not in SERVICE_PROCESSES)
        for n in sorted(SERVICE_PROCESSES):
            if any(x == n for x, _ in users):
                print("   ⭐ I do NOT count it: «%s» — %s%s"
                      % (n, SERVICE_PROCESSES[n],
                         (" (now it has %d processes)" % len(processes[n]))
                         if n in processes else ""))
        if report:
            print("   ⚠ FINDING: %d users outside the net's name "
                  "space, which neither I nor the hook\n      touch: %s  ⇒ the "
                  "bench that made them should give them a name of the net"
                  % (len(report), " ".join(report)))

        outcome, u, c, pf, why = judgment(
            users, case, processes, dirty if a.dirty_too else None)

        print("   U %-3s C %-3s P %-3s" % (u, c, pf))
        unit, orphans, sessions = dirty
        print("   %s failed user@ units without a user: %d · ownerless /tmp "
              "entries: %d · orphan sessions: %d"
              % ("⭐ VERDICT (--dirty-too):" if a.dirty_too
                 else "⚠ FINDING, not verdict:", len(unit), len(orphans),
                 len(sessions)))

        print()
        if a.leave_a_tenant or a.leave_a_home:
            # ⛔ The other way round, and it is said out loud: here 0 is the good news.
            if outcome == 1:
                print("⭐ THE INJECTED FAULT WAS SEEN — this mesh CAN "
                      "give red,\n   ⭐ and for the right reason: %s" % why)
                return 0
            if outcome == 3:
                print("⚠ with the injected fault I could NOT look: %s\n"
                      "   ⇒ outcome 3, not a green" % why)
                return 3
            print("⛔⛔ THE INJECTED FAULT WAS NOT SEEN: «%s» was inside "
                  "the box\n   and the mesh said green all the same." % chi)
            return 1
        if outcome == 0:
            print("⭐ GREEN — %s" % why)
        elif outcome == 1:
            print("⛔⛔ RED — %s" % why)
            print("   ⇒ the net worked in this box and did not "
                  "clear out: see `clear_out_tenants`\n     in "
                  "`11-hook.sh`, and the bench that created these names")
        else:
            print("⚠ I could not look — %s" % why)
        return outcome
    finally:
        if fault_who:
            remove_fault(fault_who)
            print("   ⭐ the injected fault was removed: «%s» is no longer there"
                  % fault_who)


if __name__ == "__main__":
    sys.exit(main())
