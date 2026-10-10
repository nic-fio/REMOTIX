#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c19 — ⭐⭐ «AT THE END OF THE RUN NO TENANT OF THE NET SURVIVES»
===========================================================================

    python3 11-c19-la-scatola-resta-pulita.py
    python3 11-c19-la-scatola-resta-pulita.py --lascia-un-inquilino
    python3 11-c19-la-scatola-resta-pulita.py --lascia-una-casa
    python3 11-c19-la-scatola-resta-pulita.py --anche-lo-sporco
    python3 11-c19-la-scatola-resta-pulita.py --certifica

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
    how I know it can give red: `--lascia-un-inquilino` (a user of the net
                                alive, with their home and a process of theirs) ·
                                `--lascia-una-casa` (⭐ only the home, the user
                                not: the leftover no `pgrep` sees)

---------------------------------------------------------------------------
⛔⛔ WHY IT EXISTS — 23 September 2026, `fasi/13-xfce.md` «What remains»
---------------------------------------------------------------------------

The clear-out already exists (`11-gancio.sh`, `sgombera_inquilini`, 22 Sep 2026):
after every mesh the hook goes over the net's name space and removes
users, homes, failed `user@` units and `/tmp` orphans.  ⭐ What was missing
is the **VERDICT**: today `bilancio_dopo` writes *«the BOX got dirty»*
as an `inf` line, annotated `riuscita=true`.

⇒ ⛔ **The net can leave twenty tenants inside a box and declare itself
  green all the same.**  This mesh is the line that says no.

⚠ And it is not a textbook case: `[M]` 22 Sep 2026, after `--famiglia tutto`,
  22-24 live tenants in each of the three boxes, with their `/home`, plus
  failed `user@…` units and orphans in `/tmp`.  ⇒ And what accumulates BREAKS
  the meshes: the bisection of 21 Sep 2026 (C17 red on gnome and kde)
  showed that the state accumulated by the box makes the product be accused of
  a red that is not its own.

---------------------------------------------------------------------------
⛔⛔⛔ THE PITFALL, AND IT IS CALLED `nictest` — declared because it is the only thing
      that, done wrong, would turn this mesh into a generator of false reds
---------------------------------------------------------------------------

`11-accendi.sh bilancio` counts tenants **by uid**:

    getent passwd | awk -F: '$3 >= 1000 && $3 < 60000 && $1 != "provanic"'

⇒ ⛔ It excludes **only** `provanic`.  For that count `nictest` — the user of the
  manual tests, who **is in the boxes on purpose** and must stay there — is a
  tenant, and a mesh built on that count would say red every time
  the user has a session open.  ⚠ A false red, in a safety net,
  always ends the same way: the net gets switched off by whoever works.

⭐⭐ THE CURE: **count by NAME, not by uid** — and the name is the one the
    hook itself uses to clear out (`sgombera_inquilini`):

        ^c[0-9]+b?u[0-9]+$        c1u1 · c3u2 · c8bu5 · c17u931 · c20u407

  ⇒ It is the **net's name space**: whoever is inside it is the net's stuff and
    must be removed; whoever is outside is not mine to judge.  `nictest`, `provanic`,
    `root` and all system users do not fall into it **by shape**,
    not by a list of exceptions someone will have to remember to update.

⚠ And there is the price, declared: a bench that names its tenant **outside**
  the name space (`[M]` 23 Sep 2026, in gnome: `corrx1`, `corrx2` of
  `12-client-veri.py`; and the old `13-w4` called it `w4u$$`) ⛔ is not
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
     (`LEZIONI.md` §1.49).
   ⭐ And whoever wants to measure it that day asks for it by name: `--anche-lo-sporco`
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
#    `11-gancio.sh` (`sgombera_inquilini`) uses to clear out.
#    ⛔ If the two diverge, the hook removes one thing and this mesh
#      judges another: see `LEZIONI.md` §1.46.
MODELLO = re.compile(r"^c[0-9]+b?u[0-9]+$")

# ⚠ The service users who are in the boxes ON PURPOSE.  ⛔ It is not the
#   rule — the rule is the pattern above, and they do not fall into it
#   by shape.  This list only serves to PRINT them, so whoever reads sees that
#   the distinction was made and not forgotten.
DI_SERVIZIO = {
    "provanic": "the benches' test user (the recipe puts it there)",
    "nictest":  "⭐ the user of the MANUAL tests: it is in the boxes on purpose, "
                "and this mesh neither touches nor counts it",
}


def corri(argv, tempo=30):
    """A command, or `None` if it did not answer.  ⛔ It never raises."""
    try:
        return subprocess.run(argv, capture_output=True, text=True, timeout=tempo)
    except (subprocess.TimeoutExpired, OSError):
        return None


def guscio(riga, tempo=30):
    try:
        return subprocess.run(["/bin/sh", "-c", riga], capture_output=True,
                              text=True, timeout=tempo)
    except (subprocess.TimeoutExpired, OSError):
        return None


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE FACTS — they are read from the machine, and each returns `None` when it
#   could not be read.  ⛔ `None` is not «empty»: empty is a green, `None`
#   is an «I could not look».
# ═══════════════════════════════════════════════════════════════════════════
def tutti_gli_utenti():
    """[(name, uid)] of `/etc/passwd`, or `None`."""
    r = corri(["getent", "passwd"], 20)
    if r is None or r.returncode != 0:
        return None
    fuori = []
    for riga in (r.stdout or "").splitlines():
        pezzi = riga.split(":")
        if len(pezzi) < 3:
            continue
        try:
            fuori.append((pezzi[0], int(pezzi[2])))
        except ValueError:
            continue
    return fuori


def case_in(cartella="/home"):
    """The names of the folders of `/home`, or `None`."""
    try:
        return sorted(os.listdir(cartella))
    except OSError:
        return None


def processi_di(nomi):
    """{name: [pid…]} for the given names.  ⛔ It asks `pgrep -u`, which looks at
       the REAL uid: ⚠ a `pkill -f` on the name would also catch the shell that
       is running it (`LEZIONI.md`, 22 Sep 2026: the shell was killing
       itself), and here nothing needs killing — it needs COUNTING."""
    fuori = {}
    for n in nomi:
        r = corri(["pgrep", "-u", n], 15)
        if r is None:
            continue
        pid = [x for x in (r.stdout or "").split() if x.isdigit()]
        if pid:
            fuori[n] = pid
    return fuori


def sporco_della_scatola(noti):
    """⚠ FINDING: the rubbish, not the tenants.  `noti` = the uids that in
       `/etc/passwd` still have a name."""
    unita, orfani, sessioni = [], [], []
    r = corri(["systemctl", "--failed", "--no-legend", "--plain"], 30)
    if r is not None:
        for riga in (r.stdout or "").splitlines():
            m = re.match(r"^\s*user@(\d+)\.service", riga)
            if m and int(m.group(1)) not in noti:
                unita.append(m.group(1))
    r = guscio("find /tmp -mindepth 1 -maxdepth 1 -nouser 2>/dev/null", 30)
    if r is not None:
        orfani = [x for x in (r.stdout or "").splitlines() if x.strip()]
    r = corri(["loginctl", "list-sessions", "--no-legend"], 20)
    if r is not None:
        for riga in (r.stdout or "").splitlines():
            pezzi = riga.split()
            if len(pezzi) >= 3 and pezzi[1].isdigit() and int(pezzi[1]) not in noti:
                sessioni.append(pezzi[0])
    return unita, orfani, sessioni


# ═══════════════════════════════════════════════════════════════════════════
# ⭐ THE JUDGEMENT — a PURE function: no file reading, no command.
#   ⇒ `--certifica` goes through it without touching either the machine or the product.
# ═══════════════════════════════════════════════════════════════════════════
def giudizio(utenti, case, processi, sporco=None):
    """⭐ (esito, U, C, P, perche) from the FACTS already gathered.

    `utenti` [(name, uid)] of the whole machine · `case` the names in `/home` ·
    `processi` {name: [pid…]} · `sporco` (units, orphans, sessions) or
    `None` when the dirt does NOT enter the verdict (the net's mode).
    """
    if utenti is None or case is None:
        return 3, "?", "?", "?", ("I could not read %s: without it I do not "
                                  "know who stayed inside"
                                  % ("/etc/passwd" if utenti is None else "/home"))

    della_rete = sorted(n for n, _ in utenti if MODELLO.match(n))
    case_rete = sorted(n for n in case if MODELLO.match(n))
    proc_rete = sorted(n for n in processi if MODELLO.match(n))

    accuse = []
    if della_rete:
        accuse.append("in /etc/passwd %d tenants of the net survive: %s"
                      % (len(della_rete), " ".join(della_rete)))
    if case_rete:
        accuse.append("in /home %d homes of the net remain: %s"
                      % (len(case_rete), " ".join(case_rete)))
    if proc_rete:
        accuse.append("processes of %s are still running"
                      % ", ".join("%s (%d)" % (n, len(processi[n]))
                                  for n in proc_rete))
    # ⚠ The dirt enters ONLY if the caller asked for it (`--anche-lo-sporco`).
    if sporco is not None:
        unita, orfani, sessioni = sporco
        if unita:
            accuse.append("%d failed user@ units no longer with a user: %s"
                          % (len(unita), " ".join(unita[:8])))
        if orfani:
            accuse.append("%d ownerless /tmp entries: %s"
                          % (len(orfani), " ".join(orfani[:5])))
        if sessioni:
            accuse.append("%d logind sessions without a user" % len(sessioni))

    u = "NO" if della_rete else "SI"
    c = "NO" if case_rete else "SI"
    p = "NO" if proc_rete else "SI"
    if accuse:
        return 1, u, c, p, "; ".join(accuse)
    return 0, u, c, p, ("nobody from the net stayed inside: 0 tenants, "
                        "0 homes, 0 processes")


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔ THE INJECTED FAULTS — they are injected into the BOX, and always removed.
#
# ⭐ They carry a name of the net's name space on purpose: if this run
#   dies half-way, the hook clears them out by itself at the next mesh.  ⛔ A bench
#   that leaves leftovers while measuring leftovers would be a joke.
# ═══════════════════════════════════════════════════════════════════════════
def innesta_un_inquilino(chi):
    """⛔ A LIVE tenant of the net: user + home + a process of theirs."""
    r = corri(["useradd", "-m", "-s", "/bin/bash", chi], 60)
    if r is None or r.returncode != 0:
        return False, "useradd did not succeed"
    # ⚠ `setsid` and stdin on /dev/null, like C3's scene: a child left
    #   in the terminal's process group ends up stopped in `T`.
    guscio("setsid runuser -u %s -- sleep 600 < /dev/null > /dev/null 2>&1 &"
           % chi, 20)
    for _ in range(20):
        r = corri(["pgrep", "-u", chi], 10)
        if r is not None and r.returncode == 0:
            return True, ""
        time.sleep(0.25)
    return True, "⚠ the user is there but their process was not seen"


def innesta_una_casa(chi):
    """⛔ ONLY the home: the user not.  It is the `userdel` without `-r`, that is the
       leftover no `pgrep` and no `getent passwd` see."""
    try:
        os.makedirs(os.path.join("/home", chi), exist_ok=True)
        with open(os.path.join("/home", chi, ".c19"), "w") as f:
            f.write("leftover injected by C19\n")
        return True, ""
    except OSError as e:
        return False, "I could not make /home/%s: %s" % (chi, e)


def togli_il_guasto(chi):
    """⭐ Always, and without asking."""
    corri(["loginctl", "terminate-user", chi], 20)
    corri(["pkill", "-KILL", "-u", chi], 10)
    time.sleep(0.3)
    corri(["userdel", "-r", chi], 30)
    guscio("rm -rf /home/%s" % chi, 20)


# ═══════════════════════════════════════════════════════════════════════════
def certifica():
    """⛔ Can the mesh give red, and can it NOT give it? It is tested on the JUDGEMENT."""
    guai = 0
    sistema = [("root", 0), ("daemon", 1), ("systemd-network", 998)]
    servizio = [("provanic", 4011), ("nictest", 4012)]
    casi = [
        ("⭐ clean box (only provanic and nictest are there) ⇒ GREEN",
         (sistema + servizio, ["provanic", "nictest", "lost+found"], {}, None), 0),
        ("⛔ a tenant of the net survives ⇒ RED",
         (sistema + servizio + [("c3u2", 4013)],
          ["provanic", "nictest", "c3u2"], {"c3u2": ["991"]}, None), 1),
        ("⛔ the user is gone but the HOME is not (userdel without -r) ⇒ RED",
         (sistema + servizio, ["provanic", "nictest", "c8bu5"], {}, None), 1),
        ("⛔ user and home gone, a PROCESS of theirs is alive ⇒ RED",
         (sistema + servizio, ["provanic", "nictest"], {"c17u931": ["4"]}, None), 1),
        ("⛔ twenty tenants of the net, like on 22 Sep ⇒ RED",
         (sistema + servizio + [("c%du1" % i, 4020 + i) for i in range(20)],
          ["provanic", "nictest"], {}, None), 1),
        ("⭐⭐ nictest alive, with its home AND a process of its own ⇒ GREEN "
         "(⛔ the pitfall: `bilancio` would count it)",
         (sistema + servizio, ["provanic", "nictest"],
          {"nictest": ["101", "102", "103"]}, None), 0),
        ("⭐ provanic with its home and its processes ⇒ GREEN",
         (sistema + servizio, ["provanic", "nictest"],
          {"provanic": ["77"]}, None), 0),
        ("⚠ a user OUTSIDE the name space (corrx1) ⇒ GREEN: "
         "not mine to judge, it is printed and that is all",
         (sistema + servizio + [("corrx1", 4013)],
          ["provanic", "nictest", "corrx1"], {"corrx1": ["55"]}, None), 0),
        ("⚠ only DIRT (failed units and /tmp orphans) ⇒ GREEN: "
         "it is rubbish, not a tenant",
         (sistema + servizio, ["provanic", "nictest"], {}, None), 0),
        ("⭐ the same dirt, but asked for with the verdict (--anche-lo-sporco) ⇒ RED",
         (sistema + servizio, ["provanic", "nictest"], {},
          (["4023", "4024"], ["/tmp/mozilla"], [])), 1),
        ("⚠ /etc/passwd cannot be read ⇒ 3, ⛔ never a red",
         (None, ["provanic"], {}, None), 3),
        ("⚠ /home cannot be read ⇒ 3, ⛔ never a red",
         (sistema + servizio, None, {}, None), 3),
    ]
    print("== C19 — certification of the judgement (⛔ without touching the box)")
    for nome, argomenti, atteso in casi:
        e = giudizio(*argomenti)[0]
        if e != atteso:
            guai += 1
        print("  %s %-78s outcome %s (expected %s)"
              % ("OK " if e == atteso else "NO ", nome, e, atteso))

    # ⭐ And the pattern is tested by NAME, not by trust: it is the only thing that
    #   separates a tenant of the net from `nictest`.
    prove_nome = [("c1u1", True), ("c3u2", True), ("c8bu5", True),
                  ("c17u931", True), ("c20u407", True), ("c19u100", True),
                  ("nictest", False), ("provanic", False), ("root", False),
                  ("corrx1", False), ("w4u12345", False), ("ki9", False),
                  ("c1u1x", False), ("xc1u1", False)]
    for nome, atteso in prove_nome:
        avuto = bool(MODELLO.match(nome))
        if avuto != atteso:
            guai += 1
        print("  %s the net's name space: %-12s ⇒ %s (expected %s)"
              % ("OK " if avuto == atteso else "NO ", nome,
                 "the net's" if avuto else "not mine",
                 "the net's" if atteso else "not mine"))
    print()
    if guai:
        print("⛔ %d cases of the judgement do NOT give what they must" % guai)
        return 1
    print("⭐ the judgement gives green, red and «I do not know» where it must — and ⭐ "
          "`nictest` with its home, its processes and its\n   session "
          "stays a GREEN, which is the only way for this mesh to be "
          "useful instead of a nuisance")
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--porta", type=int, default=0,
                   help="⚠ not needed: this mesh does not talk to the product. "
                        "It is there because the hook calls all the meshes the "
                        "same way")
    p.add_argument("--lascia-un-inquilino", action="store_true",
                   help="⛔ THE INJECTED FAULT: a live user of the net, "
                        "with their home and a process of theirs")
    p.add_argument("--lascia-una-casa", action="store_true",
                   help="⛔ THE INJECTED FAULT, the other one: ONLY the home, "
                        "the user not (the `userdel` without `-r`)")
    p.add_argument("--anche-lo-sporco", action="store_true",
                   help="⚠ promotes to VERDICT the failed units and the orphans "
                        "of /tmp.  ⛔ The net does not pass it: see at the top")
    p.add_argument("--case", default="/home")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()
    if os.geteuid() != 0:
        print("⛔ it wants the administrator (it reads everyone's units and "
              "processes) ⇒ I could not look")
        return 3

    innestato = ""
    if a.lascia_un_inquilino:
        innestato = " ⛔ INJECTED FAULT: --lascia-un-inquilino"
    elif a.lascia_una_casa:
        innestato = " ⛔ INJECTED FAULT: --lascia-una-casa"
    chi = "c19u%d" % random.randint(100, 999)
    print("== C19 — at the end of the run no tenant of the net survives%s"
          % innestato)

    guasto_chi = None
    try:
        if a.lascia_un_inquilino or a.lascia_una_casa:
            guasto_chi = chi
            togli_il_guasto(chi)
            if a.lascia_un_inquilino:
                fatto, nota = innesta_un_inquilino(chi)
            else:
                fatto, nota = innesta_una_casa(chi)
            if not fatto:
                print("   ⛔ I could not inject the fault (%s) ⇒ I could "
                      "not look" % nota)
                return 3
            print("   ⛔ injected: %s%s" % (chi, (" — " + nota) if nota else ""))

        utenti = tutti_gli_utenti()
        case = case_in(a.case)
        if utenti is None or case is None:
            esito, u, c, pf, perche = giudizio(utenti, case, {}, None)
            print("   ⚠ %s" % perche)
            return 3

        della_rete = sorted(n for n, _ in utenti if MODELLO.match(n))
        processi = processi_di(della_rete + sorted(DI_SERVIZIO))
        noti = set(uid for _, uid in utenti)
        sporco = sporco_della_scatola(noti)

        # ── what I do NOT count, printed: the distinction shows ──
        fuori = sorted(n for n, uid in utenti
                       if 1000 <= uid < 60000 and not MODELLO.match(n)
                       and n not in DI_SERVIZIO)
        for n in sorted(DI_SERVIZIO):
            if any(x == n for x, _ in utenti):
                print("   ⭐ I do NOT count it: «%s» — %s%s"
                      % (n, DI_SERVIZIO[n],
                         (" (now it has %d processes)" % len(processi[n]))
                         if n in processi else ""))
        if fuori:
            print("   ⚠ FINDING: %d users outside the net's name "
                  "space, which neither I nor the hook\n      touch: %s  ⇒ the "
                  "bench that made them should give them a name of the net"
                  % (len(fuori), " ".join(fuori)))

        esito, u, c, pf, perche = giudizio(
            utenti, case, processi, sporco if a.anche_lo_sporco else None)

        print("   U %-3s C %-3s P %-3s" % (u, c, pf))
        unita, orfani, sessioni = sporco
        print("   %s failed user@ units without a user: %d · ownerless /tmp "
              "entries: %d · orphan sessions: %d"
              % ("⭐ VERDICT (--anche-lo-sporco):" if a.anche_lo_sporco
                 else "⚠ FINDING, not verdict:", len(unita), len(orfani),
                 len(sessioni)))

        print()
        if a.lascia_un_inquilino or a.lascia_una_casa:
            # ⛔ The other way round, and it is said out loud: here 0 is the good news.
            if esito == 1:
                print("⭐ THE INJECTED FAULT WAS SEEN — this mesh CAN "
                      "give red,\n   ⭐ and for the right reason: %s" % perche)
                return 0
            if esito == 3:
                print("⚠ with the injected fault I could NOT look: %s\n"
                      "   ⇒ outcome 3, not a green" % perche)
                return 3
            print("⛔⛔ THE INJECTED FAULT WAS NOT SEEN: «%s» was inside "
                  "the box\n   and the mesh said green all the same." % chi)
            return 1
        if esito == 0:
            print("⭐ GREEN — %s" % perche)
        elif esito == 1:
            print("⛔⛔ RED — %s" % perche)
            print("   ⇒ the net worked in this box and did not "
                  "clear out: see `sgombera_inquilini`\n     in "
                  "`11-gancio.sh`, and the bench that created these names")
        else:
            print("⚠ I could not look — %s" % perche)
        return esito
    finally:
        if guasto_chi:
            togli_il_guasto(guasto_chi)
            print("   ⭐ the injected fault was removed: «%s» is no longer there"
                  % guasto_chi)


if __name__ == "__main__":
    sys.exit(main())
