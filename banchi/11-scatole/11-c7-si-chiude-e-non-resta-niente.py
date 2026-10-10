#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c7 — ⭐⭐ «EVERYTHING CLOSES, AND NOTHING REMAINS»
===========================================================================

    python3 11-c7-si-chiude-e-non-resta-niente.py --porta 8513
    python3 11-c7-si-chiude-e-non-resta-niente.py --porta 8513 --solo-distacco
    python3 11-c7-si-chiude-e-non-resta-niente.py --porta 8513 --lascia-un-processo
    python3 11-c7-si-chiude-e-non-resta-niente.py --certifica

Line C7 of `fasi/11-la-rete-di-sicurezza.md` §4.1:

    what must be true         : everything closes, and nothing remains
    where it starts from      : after a FINISHED session
    what it looks at          : orphan processes, sockets, locks, ⭐ the
                                graphics card back at rest
    how I know it can say red : a process is left on purpose ⇒ red

⭐ C7 judges **leftovers**, not pixels.  ⇒ It is not stopped by the open defect
   of phase 10 (`[M]` ten new GNOME sessions out of ten are born blind,
   §7-bis.13): it does not need something to be SEEN, it needs something to have been
   **put down on the floor** and then removed.
⛔ But the session must really START, or this mesh becomes the defect
   §1.44 — *«the predicate that could not give red»*: a session that is not
   born leaves nothing, and «nothing remains» would be green forever.
   ⇒ See «THE GUARD THAT HOLDS EVERYTHING UP», further below.

---------------------------------------------------------------------------
⛔⛔ THE MOST IMPORTANT THING OF THIS MESH: «FINISHED» DOES NOT MEAN «DETACHED»
---------------------------------------------------------------------------

The project's invariant **I4** says that **the stage belongs to the SESSION
and survives the disconnection**.  ⇒ ⛔ A client that goes away **must not**
trigger C7.  A naive draft — *«the client detaches, now nothing
must remain»* — would be **red at every round on a healthy product**, i.e.
the defect §1.49: *a red that cannot be made green is worse than
no mesh*, and it ends up switched off by whoever works.

⭐ **How they are told apart, and they are told apart with a GESTURE, not with an opinion:**

    the CLIENT detaches    the QUIC wire drops.  ⭐ The tenant's child
                           stays alive, its `/run/user/<uid>` stays, its
                           `loginctl` session stays.  `[M]` 26 Aug 2026,
                           XFCE box: after the detach the tenant still had
                           **8 processes** and **8 entries** in
                           `XDG_RUNTIME_DIR`.  And the product log
                           says it in its own words:
                             «the frame loop turns OFF: nobody is watching
                              any more, and the stage stays up (I4)»

    the session is CLOSED  ⭐ the gesture is `loginctl terminate-user <chi>` —
                           i.e. what happens when the tenant LEAVES.
                           ⛔ It is not a convenient choice: the product **does not
                           have** a «close the session» command (the command
                           socket serves the ban, `src/comando.c`), so the
                           end of a session, today, is the end of the
                           `logind` session.  If one day the product
                           has one, THIS line changes and not the rest.

⇒ ⭐ **A normal round judges TWO things, and they are two distinct judgements:**

    1. the detach did NOT take away the stage    ⭐ the «remotix» CHILD is
                                                 still among the tenant's
                                                 processes
    2. the closing did NOT leave anything        (before = after)

⚠ And (1) is really falsifiable: if the stage disappeared with the detach, this
  mesh says **red of a different kind** and names it.  ⛔ Staying silent
  there would mean that (2) becomes green **because there was nothing to
  close** — which is the most convenient lie of this whole mesh.

⛔⛔ AND (1) HAS ALREADY LIED ONCE, ⚠ and it is written here because it is the
    most serious defect this mesh has had.  Until **27 August
    2026** the question was not *«is the child still there?»* but *«did
    SOMETHING change between the start and the detach?»* — and after a detach something
    always changes that **is not the product**: `user@<uid>.service` is
    `active`, the `loginctl` sessions are 2, `/run/user/<uid>` has its
    sockets.  ⇒ The predicate could not fail (`LEZIONI.md` §1.44), and with
    the real fingerprint **without `remotix`** — i.e. with I4 broken — the mesh
    answered `(0, 'regge')` in both the ways the hook runs
    it.  ⛔⛔ **C7 said GREEN on a broken I4**, and these very lines
    promised the opposite.
  ⭐ And the certification could not catch it: the synthetic case used
    `staccato = vuota`, a **totally** empty fingerprint — the shape the
    author had imagined, not the shape the fault would have.  ⇒ Now
    there is `SENZA_FIGLIO`, which is `VIVA` with `remotix` removed and nothing else.

---------------------------------------------------------------------------
⭐ WHAT GOES INTO THE FINGERPRINT — and what does NOT, declared
---------------------------------------------------------------------------

The fingerprint is taken **per TENANT**, never globally: phase 10 §7.3, where a
global `pkill -f` risked killing the work of another test in
progress.  ⇒ Everything that follows is filtered by `uid`.

  ⭐ JUDGED (before and after must match)

    the tenant's processes      the sorted NAMES, ⛔ not the process numbers:
                                a different pid is not a leftover.
                                `[M]` 26 Aug 2026, during: `(sd-pam) ·
                                dbus-daemon · pipewire · pipewire ·
                                pipewire-pulse · remotix · systemd ·
                                wireplumber`
    sockets and files in        `/run/user/<uid>`: the sorted names.
    XDG_RUNTIME_DIR             `[M]` during: `bus · dbus-1 · pipewire-0 ·
                                pipewire-0-manager · pulse · systemd` + the
                                locks
    ⭐ locks                     the `*.lock` inside `XDG_RUNTIME_DIR` (put there by
                                PipeWire).  ⚠ They are a subset of the entry
                                above, and it is intended: they are counted **separately**
                                because line C7 names them, and an entry
                                named by the document that disappears inside
                                another is an entry nobody checks any more
    `loginctl` sessions         HOW MANY the tenant has, not which: the
                                identifiers change at every round
                                (`c85`, `c86`…) and comparing them would always give
                                red.  `[M]` during: **2** (`user` +
                                `manager`)
    user units                  `user@<uid>.service` and
                                `user-runtime-dir@<uid>.service`, the state in
                                force read with `is-active`
    ⭐ /dev/dri                  how many processes **of the tenant** hold
                                a descriptor open on the card.  ⇒ It is
                                *«the graphics card back at rest»* of
                                line C7

  ⚠ PRINTED AND NOT JUDGED — ⛔ and the reason matters

    the home                    a session WRITES in its own home
                                (`.config`, `.cache`, `.local`), and it is its
                                job.  `[M]` 26 Aug 2026: the home goes from
                                **4** to **8** entries in a round.  ⇒ Putting it among
                                the judged would mean a red at every
                                round on a healthy product: §1.49.
                                ⭐ The product does not promise to delete the
                                home, it promises not to leave **live stuff**.
    what it wrote in            same reason, and one more: on the real machine
    `/tmp`                      `~/.cache` **is a link to /tmp**
                                (the owner's choice, `DECISIONI.md`
                                §4.6-undecies).  ⇒ Judging `/tmp` would
                                mean judging the home by another road.

  ⛔ AND THE BACKGROUND NOISE, declared instead of removed on the sly:

    · the fingerprint is **per uid**, and the tenant is created NEW at every round
      ⇒ everything that belongs to others (the server, the other benches, the
        box's system) never enters the comparison;
    · the **total** number of processes with the card open is printed and ⛔ NOT
      judged: inside the box there could be another bench at work,
      and a global comparison is exactly the defect of phase 10 §7.3.

---------------------------------------------------------------------------
⛔⛔ THE GUARD THAT HOLDS EVERYTHING UP — and there are THREE, in order
---------------------------------------------------------------------------

Without these, «nothing remains» is green even when nothing happened
(§1.44), and the green has no measurement underneath (§1.46).

  1. ⛔ **The field must be free BEFORE.**  If the starting fingerprint is not
     empty, the tenant carries a leftover of someone else (or of this
     bench of yesterday: §1.39 «from zero also includes from zero with respect to
     myself»).  ⇒ Outcome **2**, bad terrain — and ⛔ the session is **not**
     accused of a leftover that was already there.
  2. ⛔ **The client must have been ADMITTED.**  If not: outcome **3**, I could not
     look.  ⚠ Like C1, the reason is carried next to the symptom: `[M]`
     26 Aug 2026 five rounds of C1 said «NON-AMMESSO» and the real cause was
     the missing `aioquic`.
  3. ⛔ **The log must say that the child WAS BORN.**  «Admitted» and «the
     session started» are two questions, and it is the same distinction that
     `sessione.h` makes between *«is it alive?»* and *«does it have a monitor?»*.  If the log does not
     name the child of this tenant: outcome **3**.

⚠ And a fourth, which is the forgotten half of §1.49: **we wait for the EVENT**.
  After the closing we look until the field is free again, up to a
  DECLARED time (`--attesa-chiusura`), and ⭐ **we print how long it took**.  A
  slow but complete closing is green; ⛔ a clock ceiling would have called it
  red.  `[M]` 26 Aug 2026, XFCE box, real round: **1.13 s**.

---------------------------------------------------------------------------
⛔ THE GRAFTED FAULT — `--lascia-un-processo`
---------------------------------------------------------------------------

§3.6: *«every test of the list has, mandatorily, its grafted fault, and
that case must be run, not imagined»*.

Before closing, a process of the tenant is left on purpose **outside the
user's systemd slice**:

    setsid runuser -u <chi> -- sleep N

⭐ And the shape is not random: it is **the same** as the product's real child —
  a process that runs as the tenant but hangs from the server, not from its
  session (`[M]` `pid 12113 remotix, ppid 10575, uid c7u1`).  ⇒ I.e. we
  graft the class of orphan this product can really leave, not
  a convenient orphan.
`[M]` 26 Aug 2026, measured before writing this mesh: `terminate-user`
does **not** take it away ⇒ it remains, ⇒ red.

---------------------------------------------------------------------------
⛔ WHAT C7 DOES **NOT** LOOK AT — or someone will trust it too much
---------------------------------------------------------------------------

  · **the pixels**: C7 opens no image.  A black session leaves the
    same leftovers as a healthy session ⇒ C7 says green on both.  That
    question belongs to C1 and C2.
  · **the memory**: opening and closing a hundred sessions and looking whether the server
    grows is a long-duration test, ⛔ another trade (§6).
  · **the leftovers INSIDE the server**: a slot not freed, a structure not
    freed, a descriptor the PARENT does not close.  C7 looks **on the floor**
    (processes, sockets, units, card), not inside the server's process.
  · **the home and /tmp**: measured, printed, ⛔ not judged (see above).
  · **the box**: C7 closes a SESSION, not the container.  That the
    container does not shut down by itself is a nearby and different question, and it is
    treated in this mesh's report, not in here.
  · ⚠ **the other boxes**: this mesh works inside the one it runs in, and
    creates and deletes the tenant by name.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ I looked: the detach left the stage standing, and the closing
     left nothing
  1  ⛔ I looked and it does NOT hold ⇒ red.  Two kinds, and they are named:
       (a) the closing left leftovers
       (b) the detach took the stage away (I4)
  3  ⛔ I could not look: the client was not admitted, the child was not
     born, or no entry of the fingerprint could answer — ⛔ and it is NOT
     a red
  2  the terrain does not hold: the field was not free before starting
===========================================================================
"""
import argparse
import importlib.util
import os
import pwd
import re
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ «WAS THE CLIENT ADMITTED?» — ⛔ THE PREDICATE IS IMPORTED, NOT
#     REWRITTEN.  Its home is `11-c1-nasce-e-si-vede.py`, and there is ONE (§1.47).
#
# ⛔ Until 27 August 2026 there was `"AMMESSO" in uscita` here, ⭐ and it could not
#    say no: `[R]` `01-b3-cliente.py` prints that word also in the **two
#    refusal messages** — «CONGEDO instead of AMMESSO: reason …» (:1315) and
#    «expected AMMESSO, arrived …» (:1322) — and prints them on **stdout**, which
#    is exactly where it looked.  ⇒ A predicate that cannot fail,
#    `LEZIONI.md` §1.44: the mesh believed it had got in **even when it had been
#    turned away**, and then judged the darkness that followed as a defect of the
#    product.
# ⚠ It was in FIVE meshes with the same line.  ⇒ Curing it five times would have
#   been creating five places to diverge from again (§1.47): it lives in C1, and
#   the other four import it from there.
# ⛔ And if it cannot be imported we exit **3** and say so, ⇒ ⛔ we do not
#   silently fall back on the poor predicate — which is the defect itself.
# ═══════════════════════════════════════════════════════════════════════════
_QUI_C1 = os.path.dirname(os.path.abspath(__file__))
_C1 = None


def _carica_c1():
    """⛔ It is a LOADER, not a judge: it finds the file, it decides nothing.

    ⚠ It is looked for next to me (inside the box everything is in `/opt/remotix`) and
      one level up, as C2, C3 and C6 do with their imported judges.
    """
    for p in (os.path.join(_QUI_C1, "11-c1-nasce-e-si-vede.py"),
              os.path.join(os.path.dirname(_QUI_C1), "11-scatole",
                           "11-c1-nasce-e-si-vede.py")):
        if not os.path.exists(p):
            continue
        spec = importlib.util.spec_from_file_location("c1_ammissione", p)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        # ⛔ We VERIFY that what is needed is there, instead of trusting the name
        #    of the file (`CODER.md` §3.9).
        if not callable(getattr(m, "e_stato_ammesso", None)):
            return None
        if not callable(getattr(m, "certifica_ammissione", None)):
            return None
        # ⭐ And from C1 also comes the guarantee of the card's groups: same
        #    reason, same single place (§1.47).
        for mestiere in ("garantisci_i_gruppi", "verdetto_gruppi",
                         "certifica_gruppi"):
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_dell_ammissione():
    global _C1
    if _C1 is None:
        _C1 = _carica_c1()
    if _C1 is None:
        print("⛔ I cannot find `11-c1-nasce-e-si-vede.py` next to me, and from there")
        print("   comes the predicate «was the client ADMITTED?» — which lives")
        print("   in one place only on purpose (§1.47).")
        print("⇒ I could not look — ⛔ and it is NOT a red (§4.5).")
        sys.exit(3)
    return _C1


def e_stato_ammesso(coda):
    """⭐ `True` admitted · `False` **TURNED AWAY** · `None` said nothing.

    ⛔ `False` is not a product red: a client turned away is a client
       turned away, and the caller exits **3**.
    """
    return casa_dell_ammissione().e_stato_ammesso(coda)


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ THE CARD'S GROUPS — ⛔ and this too lives in one place only (C1).

    Returns `(esito, perche)`: `0` = the tenant sees and it can be measured,
    `3` = ⛔ it is NOT measured.

    ⛔ Until 27 August 2026 this mesh created the tenant with
       `usermod -aG video,render` **and did not read back**: two nailed-down names (which
       belong to ONE distribution) and no verification.  ⭐ `[M]` without the groups
       of the `/dev/dri` nodes the session is born BLIND — 0 of 4, never in 90 s, zero
       frames — and this mesh would have measured the darkness calling it
       a product defect (`fasi/10-…` §7.4).
    ⭐ The work is done by `attrezzi-gruppi-scheda.sh`, which reads the gids from the NODES and
       reads back comparing the numbers.  ⛔ No copy of it is made here (§1.47).
    """
    return casa_dell_ammissione().garantisci_i_gruppi(chi, prefisso)

# ---------------------------------------------------------------------------
# ⛔ THE ENTRIES ARE DECLARED HERE and printed in every outcome: «nothing remains»
#    is a verdict, and a verdict without its yardstick is an opinion (C11).
# ---------------------------------------------------------------------------
PROCESSI = "the tenant's processes"
RUNTIME = "sockets and files in XDG_RUNTIME_DIR"
LUCCHETTI = "locks (*.lock)"
SESSIONI = "loginctl sessions"
UNITA = "user units"
SCHEDA = "descriptors on /dev/dri"
HOME = "the home"
TEMPORANEI = "what it wrote in /tmp"

GIUDICATE = (PROCESSI, RUNTIME, LUCCHETTI, SESSIONI, UNITA, SCHEDA)
STAMPATE = (HOME, TEMPORANEI)

# ⛔ The value that means «empty» — and it is not `None`.  `None` means «I could not
#    look», and the two things must not have the same face.
VUOTO = "(nothing)"

# ⭐⭐ THE CHILD'S NAME — and it is the entry on which the whole JUDGEMENT 1 rests.
#
# ⛔⛔ 27 Aug 2026, a real defect of THIS mesh, found by an agent sent
#     to refute it: JUDGEMENT 1 asked *«did SOMETHING change between the
#     start and the detach?»* instead of *«is the product's child still
#     there?»*.  ⚠ And after a detach SOMETHING always changes that is not the
#     product — `user@<uid>.service` is `active`, the `loginctl` sessions
#     are 2, `/run/user/<uid>` has its sockets.  ⇒ The predicate could not
#     fail (`LEZIONI.md` §1.44): calling `giudica` with the real fingerprint
#     **without `remotix`** — i.e. with I4 broken — the mesh answered
#     `(0, 'regge')` in both the ways the hook runs it.
#     ⛔ C7 said GREEN on a broken I4.
#
# ⇒ The right question is by NAME, and the name is the one the child carries in
#   `/proc/<pid>/comm`.  `[M]` 26 Aug 2026, XFCE box, with a live session:
#   `(sd-pam) · dbus-daemon · pipewire · pipewire · pipewire-pulse · remotix ·
#   systemd · wireplumber` — ⭐ and it is the `remotix` in the middle, the tenant's
#   child (`[M]` `pid 12113 remotix, ppid 10575, uid c7u1`).
NOME_FIGLIO = "remotix"

# ⛔ The process the GRAFTED FAULT leaves on the floor — see
#    `--lascia-un-processo`.  It serves to distinguish «the injection bit» from
#    «there was already a leftover of its own» (§1.52, the same cure C9 already has).
NOME_INIETTATO = "sleep"

FIRMA_FIGLIO = re.compile(r"figlio\s+\[(?P<chi>[^\]]+)\]")


def nomi_processi(valore):
    """The names of the processes fingerprint, one by one.

    ⛔ The comparison is by WHOLE name: a `remotix-cliente` is not the child,
       and a substring would let it pass.  ⚠ `None` and `VUOTO` give the
       empty list, and the caller tells the two cases apart by itself.
    """
    if valore is None or valore == VUOTO:
        return []
    return [n.strip() for n in valore.split("·")]


# ---------------------------------------------------------------------------
# COLLECTING THE FINGERPRINT
# ---------------------------------------------------------------------------
def corri(argv, tempo=30):
    """Runs and returns (code, output).  ⛔ No `sh -c` in the middle where it can be
       avoided: `LEZIONI.md` §1.46."""
    try:
        p = subprocess.run(argv, capture_output=True, text=True, timeout=tempo)
        return p.returncode, (p.stdout or "")
    except (OSError, subprocess.SubprocessError):
        return None, ""


def uid_di(chi):
    try:
        return pwd.getpwnam(chi).pw_uid
    except KeyError:
        return None


def processi_di(uid):
    """The NAMES of the tenant's processes, sorted.  ⛔ Not the pids.

    `/proc` is read instead of calling `ps`: ⭐ so the same pass gives
    also the descriptors on the card, and the system is not asked twice for a
    photograph that changes in the meantime.
    Returns `(nomi, quanti_con_la_scheda, pid)` — ⛔ or `(None, None, None)` if
    `/proc` could not be read.
    """
    try:
        elenco = os.listdir("/proc")
    except OSError:
        return None, None, None
    nomi, schede, pid = [], 0, []
    for voce in elenco:
        if not voce.isdigit():
            continue
        try:
            if os.stat("/proc/%s" % voce).st_uid != uid:
                continue
        except OSError:
            continue
        try:
            with open("/proc/%s/comm" % voce) as f:
                nomi.append(f.read().strip())
        except OSError:
            continue
        pid.append(voce)
        if descrittori_scheda("/proc/%s/fd" % voce):
            schede += 1
    return sorted(nomi), schede, pid


def descrittori_scheda(cartella):
    """How many descriptors of that process point to `/dev/dri`."""
    quanti = 0
    try:
        for fd in os.listdir(cartella):
            try:
                if os.readlink(os.path.join(cartella, fd)).startswith("/dev/dri"):
                    quanti += 1
            except OSError:
                continue
    except OSError:
        return 0
    return quanti


def schede_in_tutto():
    """⚠ It is PRINTED and not judged: a global comparison would step on the toes of
       another bench working in the same box (phase 10 §7.3)."""
    try:
        elenco = os.listdir("/proc")
    except OSError:
        return None
    return sum(1 for v in elenco
               if v.isdigit() and descrittori_scheda("/proc/%s/fd" % v))


def voci_cartella(percorso):
    try:
        return sorted(os.listdir(percorso))
    except FileNotFoundError:
        return []
    except OSError:
        return None


def conta_file(percorso):
    quanti = 0
    for radice, cartelle, file in os.walk(percorso, onerror=lambda e: None):
        quanti += len(cartelle) + len(file)
        if quanti > 5000:
            return quanti
    return quanti


def file_di_uid(percorso, uid, tetto=2000):
    """How many files of that uid there are under `percorso`. ⚠ Only for printing."""
    quanti = 0
    for radice, cartelle, file in os.walk(percorso, onerror=lambda e: None):
        for nome in cartelle + file:
            try:
                if os.lstat(os.path.join(radice, nome)).st_uid == uid:
                    quanti += 1
            except OSError:
                continue
            if quanti > tetto:
                return quanti
    return quanti


def raccogli(chi):
    """The tenant's fingerprint: {entry: value-as-string}.

    ⛔ An entry is `None` **only** when it could not be looked at; «there is
       nothing» is `VUOTO`.  ⚠ It is lesson §1.47 applied before the comparison:
       two `None` are not «equal», they are **mute**.
    """
    uid = uid_di(chi)
    if uid is None:
        return None
    d = {"_uid": uid}

    nomi, schede, _pid = processi_di(uid)
    d[PROCESSI] = None if nomi is None else (
        " · ".join(nomi) if nomi else VUOTO)
    d[SCHEDA] = None if schede is None else (
        "%d processes" % schede if schede else VUOTO)

    rtd = "/run/user/%d" % uid
    voci = voci_cartella(rtd)
    if voci is None:
        d[RUNTIME] = None
        d[LUCCHETTI] = None
    else:
        d[RUNTIME] = " · ".join(voci) if voci else VUOTO
        lucchetti = [v for v in voci if v.endswith(".lock")]
        d[LUCCHETTI] = " · ".join(lucchetti) if lucchetti else VUOTO

    codice, uscita = corri(["loginctl", "list-sessions", "--no-legend"])
    if codice is None:
        d[SESSIONI] = None
    else:
        # ⚠ They are counted, not listed: the identifiers change at every
        #   round and comparing them would always give red (§1.49).
        quante = sum(1 for riga in uscita.splitlines()
                     if len(riga.split()) > 2 and riga.split()[2] == chi)
        d[SESSIONI] = "%d" % quante if quante else VUOTO

    stati = []
    for unita in ("user@%d.service" % uid, "user-runtime-dir@%d.service" % uid):
        codice, uscita = corri(["systemctl", "is-active", unita])
        stati.append(None if codice is None else (uscita.strip() or "?"))
    if any(s is None for s in stati):
        d[UNITA] = None
    else:
        # ⭐ «inactive» and «failed» are both «not running», and a user
        #   manager that failed is NOT a leftover: it is a unit that is off.
        #   ⛔ If they were told apart, the first round would dirty the second.
        pulito = [("off" if s in ("inactive", "failed") else s) for s in stati]
        d[UNITA] = VUOTO if all(s == "off" for s in pulito) else " · ".join(pulito)

    d[HOME] = "%d entries" % conta_file("/home/%s" % chi)
    d[TEMPORANEI] = "%d entries" % file_di_uid("/tmp", uid)
    d["_schede in tutto"] = schede_in_tutto()
    return d


# ---------------------------------------------------------------------------
# THE JUDGE — ⭐ it is a PURE function, so `--certifica` can test it without
#              touching anything.
# ---------------------------------------------------------------------------
def differenze(a, b):
    """The judged entries in which `a` and `b` do not say the same thing.

    Returns `(diverse, mute)`: ⛔ an entry that one of the two could not
    answer is **mute**, and it does not enter the comparison — because `None == None`
    would pass without having looked at anything (`LEZIONI.md` §1.47).
    """
    diverse, mute = [], []
    for voce in GIUDICATE:
        va, vb = a.get(voce), b.get(voce)
        if va is None or vb is None:
            mute.append(voce)
            continue
        if va != vb:
            diverse.append((voce, va, vb))
    return diverse, mute


def giudica(prima, staccato, dopo, solo_distacco=False,
            ammesso=True, figlio_nato=True):
    """⭐ The judgement, all in here and without touching the world.

    Returns `(esito, specie, motivi)`.  `specie` is a word for whoever reads:
    «leftovers», «stage gone», «field occupied», «I do not know», «holds».
    """
    # ⛔ GUARD 1 — the field must be free BEFORE.
    sporco = [(v, prima.get(v)) for v in GIUDICATE
              if prima.get(v) not in (None, VUOTO)]
    if sporco:
        return 2, "field occupied", [
            "the STARTING fingerprint was not empty: %s"
            % ", ".join("%s = %s" % (v, x) for v, x in sporco),
            "⛔ and a leftover that was already there is not charged to the session",
        ]

    # ⛔ GUARD 2 — the client must have been admitted.
    # ⭐ THREE states, and the two «no»s both lead to 3 but with different words:
    #   `False` = turned away by the server, `None` = it said nothing.
    if ammesso is not True:
        return 3, "I do not know", [
            "the client was TURNED AWAY by the server" if ammesso is False
            else "the client said nothing: I do not know whether it got in",
            "⇒ there is no session whose leftovers to judge, ⛔ and a "
            "client turned away is not a broken product"]

    # ⛔ GUARD 3 — the log must say that the child was born.
    if not figlio_nato:
        return 3, "I do not know", ["the log does not name any child of this "
                                    "tenant: the session did not really start"]

    # ⛔ GUARD 4 — if NO entry can answer we do not judge.
    _d, mute = differenze(prima, staccato)
    if len(mute) == len(GIUDICATE):
        return 3, "I do not know", ["no entry of the fingerprint could "
                                    "answer: I looked at nothing"]

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ JUDGEMENT 1 — the detach must NOT have taken away the stage (I4).
    #
    # ⛔⛔ AND THE QUESTION IS «IS THE CHILD STILL THERE?», not «did something change?».
    #     See `NOME_FIGLIO` at the top: until 27 Aug 2026 there was only the
    #     generic comparison here, and it was satisfied by `systemd` — not by the product.
    # ═══════════════════════════════════════════════════════════════════════
    vive, _m = differenze(prima, staccato)
    if not vive:
        return 1, "stage gone", [
            "after the client's DETACH nothing of the tenant remained,",
            "and the fingerprint went back identical to the starting one.",
            "⛔ I4 says that the stage belongs to the SESSION and survives the",
            "   detach ⇒ either I4 is broken, or this mesh is looking at the wrong",
            "   thing.  ⚠ In both cases keeping quiet would be worse: the",
            "   closing would come out green because there was nothing left to",
            "   close.",
        ]

    # ⛔ And before saying «the child is not there» one must have been able to look at the
    #    processes: `None` is not «not there» (§4.5, question 8).
    processi_staccato = staccato.get(PROCESSI)
    if processi_staccato is None:
        return 3, "I do not know", [
            "after the detach the fingerprint could not say WHICH processes",
            "the tenant had ⇒ I cannot say whether the child is still there.",
            "⛔ And «I do not know» is not a green: I4 stays unverified.",
        ]
    if NOME_FIGLIO not in nomi_processi(processi_staccato):
        return 1, "stage gone", [
            "after the client's DETACH the «%s» child is NO LONGER among the"
            % NOME_FIGLIO,
            "tenant's processes: %s" % processi_staccato,
            "⛔ I4 says that the stage belongs to the SESSION and survives the",
            "   detach: here it died with the wire ⇒ it is a regression of I4.",
            "⚠ And the rest of the fingerprint changed anyway (%d entries): it is"
            % len(vive),
            "   `systemd` keeping its stuff standing, ⛔ not the product —",
            "   and it is precisely the way in which this judgement kept quiet before",
            "   27 Aug 2026.",
        ]

    if solo_distacco:
        return 0, "holds", [
            "the client detached and the «%s» CHILD is still alive "
            "(%d entries still different from the start)" % (NOME_FIGLIO, len(vive)),
            "⭐ and this is NOT a red: it is I4 doing its job",
        ]

    # ⭐ JUDGEMENT 2 — the closing must not have left anything.
    # ⛔ And if the final fingerprint could not be read at all, we do not judge:
    #    without this line `differenze(prima, None)` made a traceback ⇒ Python
    #    exited **1** ⇒ the hook read RED on a fault of the bench (§1.51).
    if dopo is None:
        return 3, "I do not know", [
            "after the closing the fingerprint could not be read at all:",
            "⛔ I cannot say whether something remained — and it is not a green.",
        ]
    residui, _m2 = differenze(prima, dopo)
    if residui:
        return 1, "leftovers", [
            "the session was CLOSED and %d entries did not go back as before:"
            % len(residui)]
    return 0, "holds", [
        "the detach left the «%s» child standing (%d entries different "
        "from the start), and the closing put all the %d judged entries back "
        "as it had found them" % (NOME_FIGLIO, len(vive), len(GIUDICATE))]


def guasto_visto(prima, dopo, nome=NOME_INIETTATO):
    """⛔⛔ §1.52 — with the grafted fault the COLOUR of the verdict is not enough.

    ⚠ A red is a red, but *«the fault was seen»* is another thing:
      it means that **the injection bit**.  If one day the closing
      left a leftover of its own, a simple «red ⇒ seen» would say that the net
      can say red having seen a defect of the PRODUCT — and the certification
      of the net would rest on that defect.
    ⇒ It is demanded that among the leftovers there is precisely the injected process.
       ⭐ It is the same cure C9 already has (`LEZIONI.md` §1.52).
    """
    if dopo is None:
        return False
    for voce, _va, vb in differenze(prima, dopo)[0]:
        if voce == PROCESSI and nome in nomi_processi(vb):
            return True
    return False


# ---------------------------------------------------------------------------
# ⛔ THE CERTIFICATION — synthetic cases, and the judge does not touch the world.
# ---------------------------------------------------------------------------
def _impronta(**cambi):
    d = {v: VUOTO for v in GIUDICATE}
    d.update({HOME: "5 entries", TEMPORANEI: "0 entries"})
    d.update(cambi)
    return d


VIVA = _impronta(**{
    PROCESSI: "dbus-daemon · pipewire · remotix · systemd",
    RUNTIME: "bus · pipewire-0 · pipewire-0.lock · systemd",
    LUCCHETTI: "pipewire-0.lock",
    SESSIONI: "2",
    UNITA: "active · active",
    HOME: "9 entries",
})

# ⛔⛔ THE REAL SHAPE OF THE I4 REGRESSION, and it is the reason for the cure of
#     27 Aug 2026: the product's child dies with the wire, ⚠ and **everything else
#     stays standing** because it is `systemd`'s and `logind`'s stuff — the user
#     manager, the two sessions, the sockets in `/run/user/<uid>`.
# ⇒ It is identical to `VIVA` with `remotix` removed.  Nothing else.
SENZA_FIGLIO = _impronta(**{
    PROCESSI: "dbus-daemon · pipewire · systemd",
    RUNTIME: "bus · pipewire-0 · pipewire-0.lock · systemd",
    LUCCHETTI: "pipewire-0.lock",
    SESSIONI: "2",
    UNITA: "active · active",
    HOME: "9 entries",
})


def certifica():
    """⛔ It proves that the judge can say green, red and «I do not know».

    ⚠ And it declares what it covers: the **decision**, i.e. the comparison between
      three fingerprints and the four guards.  ⛔ It does NOT cover the COLLECTION
      of the fingerprint — that `/proc` is read well, that `loginctl` answers.
      That part is certified only by running it on real data, and it is the
      round with the grafted fault.  ⇒ A certification that declares itself wider
      than it is is worth less than no certification (C1).
    """
    vuota = _impronta()
    casi = [
        ("⭐ the healthy round: it opens, detaches, closes, nothing remains",
         dict(prima=vuota, staccato=VIVA, dopo=vuota), (0, "holds")),

        ("⛔ THE GRAFTED FAULT: a process of the tenant remains",
         dict(prima=vuota, staccato=VIVA,
              dopo=_impronta(**{PROCESSI: "sleep", HOME: "9 entries"})),
         (1, "leftovers")),

        ("⛔ the socket in XDG_RUNTIME_DIR was not removed",
         dict(prima=vuota, staccato=VIVA,
              dopo=_impronta(**{RUNTIME: "bus · pipewire-0"})),
         (1, "leftovers")),

        ("⛔ a PipeWire lock left on the floor",
         dict(prima=vuota, staccato=VIVA,
              dopo=_impronta(**{RUNTIME: "pipewire-0.lock",
                                LUCCHETTI: "pipewire-0.lock"})),
         (1, "leftovers")),

        ("⛔ ⭐ the graphics card did NOT go back to rest",
         dict(prima=vuota, staccato=VIVA,
              dopo=_impronta(**{PROCESSI: "remotix", SCHEDA: "1 processes"})),
         (1, "leftovers")),

        ("⛔ the loginctl session stayed open",
         dict(prima=vuota, staccato=VIVA, dopo=_impronta(**{SESSIONI: "1"})),
         (1, "leftovers")),

        # ⭐⭐ THE CASE THIS MESH EXISTS NOT TO GET WRONG (I4).
        ("⭐ it only detaches: the stage stays ⇒ ⛔ it is NOT a red",
         dict(prima=vuota, staccato=VIVA, dopo=None, solo_distacco=True),
         (0, "holds")),

        ("⛔ the detach took away the stage ⇒ red of its own kind",
         dict(prima=vuota, staccato=vuota, dopo=vuota), (1, "stage gone")),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ THE CASES THAT WERE MISSING BEFORE TODAY — and they are the ones that would have caught
        #     the defect of 27 Aug 2026 (see `NOME_FIGLIO` at the top).
        #
        # ⚠ The case above uses `staccato=vuota`: a TOTALLY empty
        #   fingerprint, i.e. the shape the author had imagined.  ⛔ But the
        #   shape the fault would really have is another: the child dies
        #   with the wire and **everything else stays standing**, because that rest
        #   is `systemd`'s.  ⇒ Before this cure, these three cases
        #   answered `(0, 'regge')`: C7 said GREEN on a broken I4.
        # ═══════════════════════════════════════════════════════════════════
        ("⛔⛔ the CHILD dies with the detach and systemd stays ⇒ RED (I4)",
         dict(prima=vuota, staccato=SENZA_FIGLIO, dopo=vuota),
         (1, "stage gone")),

        ("⛔⛔ …and it says so also with the detach only (the hook's other mode)",
         dict(prima=vuota, staccato=SENZA_FIGLIO, dopo=None,
              solo_distacco=True), (1, "stage gone")),

        ("⛔ a process that RESEMBLES the child is not the child",
         dict(prima=vuota, staccato=_impronta(**{
             PROCESSI: "dbus-daemon · remotix-cliente · systemd",
             RUNTIME: "bus · pipewire-0 · systemd", SESSIONI: "2",
             UNITA: "active · active", HOME: "9 entries"}), dopo=vuota),
         (1, "stage gone")),

        # ⛔ `None` is not «not there»: if `/proc` could not be read one cannot
        #    say that the child died — and one cannot even say that it is
        #    alive.  ⚠ The other entries speak, so GUARD 4 does not fire.
        ("⛔ the processes could not be read ⇒ «I do not know», ⛔ NEVER green",
         dict(prima=vuota, staccato=_impronta(**{
             PROCESSI: None, RUNTIME: "bus · pipewire-0 · systemd",
             SESSIONI: "2", UNITA: "active · active", HOME: "9 entries"}),
              dopo=vuota), (3, "I do not know")),

        # ⚠ The declared noise: the home grows, and it is its job.
        ("⚠ the home grew and /tmp too ⇒ ⛔ it is NOT a leftover",
         dict(prima=vuota, staccato=VIVA,
              dopo=_impronta(**{HOME: "41 entries", TEMPORANEI: "12 entries"})),
         (0, "holds")),

        ("⛔ the field was NOT free before starting ⇒ terrain",
         dict(prima=_impronta(**{PROCESSI: "sleep"}), staccato=VIVA, dopo=vuota),
         (2, "field occupied")),

        ("⛔ the client was TURNED AWAY ⇒ I do not know, and it is NOT a red",
         dict(prima=vuota, staccato=vuota, dopo=vuota, ammesso=False),
         (3, "I do not know")),

        # ⭐ The THIRD state, which before 27 Aug 2026 could not arrive
        #   here: the client said nothing.  ⛔ This too is a 3.
        ("⚠ the client said NOTHING (None) ⇒ I do not know, not a red",
         dict(prima=vuota, staccato=vuota, dopo=vuota, ammesso=None),
         (3, "I do not know")),

        ("⛔ admitted but the child was not born ⇒ I do not know",
         dict(prima=vuota, staccato=vuota, dopo=vuota, figlio_nato=False),
         (3, "I do not know")),

        # ⛔ The final fingerprint could not be read ⇒ «I do not know», and ⛔ not
        #    a traceback the hook would read as a product red.
        ("⛔ the fingerprint AFTER CLOSING could not be read ⇒ «I do not know»",
         dict(prima=vuota, staccato=VIVA, dopo=None), (3, "I do not know")),

        # ⛔ §1.47: «I do not know» equal to «I do not know» WOULD PASS the comparison.
        ("⛔ no entry can answer ⇒ I do not know, ⛔ never green",
         dict(prima={v: None for v in GIUDICATE},
              staccato={v: None for v in GIUDICATE},
              dopo={v: None for v in GIUDICATE}), (3, "I do not know")),
    ]

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ THE SECOND HALF — «was the fault seen?» is not «is the verdict
    #    red?» (§1.52).  ⛔ This too was not there before 27 Aug 2026.
    # ═══════════════════════════════════════════════════════════════════════
    casi_guasto = [
        ("⭐ among the leftovers there is precisely the injected `sleep` ⇒ SEEN",
         dict(prima=vuota, dopo=_impronta(**{PROCESSI: "sleep"})), True),

        ("⛔ a leftover is there, but it is NOT the injected one ⇒ it is NOT «seen»",
         dict(prima=vuota, dopo=_impronta(**{RUNTIME: "bus · pipewire-0"})),
         False),

        ("⛔⛔ a `remotix` left on the floor is a defect of the PRODUCT,",
         dict(prima=vuota, dopo=_impronta(**{PROCESSI: "remotix"})), False),

        ("⛔ the final fingerprint could not be read ⇒ it is NOT «seen»",
         dict(prima=vuota, dopo=None), False),

        ("⛔ nothing remained ⇒ it is NOT «seen»",
         dict(prima=vuota, dopo=vuota), False),
    ]

    print("== certification of C7's judge ==")
    print("   ⛔ it covers the DECISION, not the collection of the fingerprint (see the top)\n")
    guai = 0
    for nome, arg, atteso in casi:
        esito, specie, _motivi = giudica(**arg)
        ok = (esito, specie) == atteso
        print("  %s  %-62s  outcome=%s (%s)   expected %s (%s)"
              % ("OK " if ok else "NO ", nome, esito, specie,
                 atteso[0], atteso[1]))
        if not ok:
            guai += 1
    print()
    print("   ⛔ and the grafted fault is read on the DIFFERENCE, not on the colour:")
    for nome, arg, atteso in casi_guasto:
        avuto = guasto_visto(**arg)
        ok = avuto is atteso
        print("  %s  %-62s  seen=%-5s  expected %s"
              % ("OK " if ok else "NO ", nome, avuto, atteso))
        if not ok:
            guai += 1
    # ⭐⭐ THE ADMISSION CASES — ⛔ the ones that were not there before today.
    #    The predicate lives in C1 and is certified with C1's cases: ⛔ a copy
    #    of the cases here would be a second place to diverge from (§1.47).
    print()
    guai_amm, quanti_amm = casa_dell_ammissione().certifica_ammissione("C7")
    guai += guai_amm

    # ⭐⭐ AND THE CARD GROUPS CASES — ⛔ the other case that was missing:
    #    a tenant without the groups of the nodes ⇒ «I could not look», ⛔
    #    never red.  They live in C1 with the step they certify.
    print()
    guai_gr, quanti_gr = casa_dell_ammissione().certifica_gruppi("C7")
    guai += guai_gr

    quanti = len(casi) + len(casi_guasto) + quanti_amm + quanti_gr
    print()
    if guai:
        print("⛔ the judge is NOT reliable: %d cases out of %d wrong"
              % (guai, quanti))
        return 1
    print("⭐ %d cases out of %d: the judge sees the leftover, ⛔ does not call a"
          % (quanti, quanti))
    print("   DETACH a leftover, ⛔ notices if the CHILD dies with the detach (I4), and does not")
    print("   say green when it has looked at nothing.")
    return 0


# ---------------------------------------------------------------------------
def stampa_impronta(titolo, d):
    print("   %s" % titolo)
    for voce in GIUDICATE:
        v = d.get(voce)
        print("     %-34s %s" % (voce, "⛔ unknown" if v is None else v))
    for voce in STAMPATE:
        print("     %-34s %s   ⚠ printed, NOT judged" % (voce, d.get(voce)))
    print("     %-34s %s   ⚠ printed, NOT judged"
          % ("processes with /dev/dri, in all", d.get("_schede in tutto")))
    print()


def leggi(percorso):
    try:
        with open(percorso, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return None


def sgombera(chi, cancella=True):
    """⭐ The BENCH's cleanup, which ⛔ is not the test.

    The tenant of THIS round is closed **by name**, never a global pattern
    (phase 10 §7.3).  ⚠ And it is done in a `finally`: a bench that leaves its
    leftovers makes the next bench red, and that red is not the product's.
    """
    corri(["loginctl", "terminate-user", chi], tempo=30)
    time.sleep(1.0)
    corri(["pkill", "-KILL", "-u", chi], tempo=30)
    time.sleep(0.5)
    if cancella:
        corri(["userdel", "-r", chi], tempo=60)
        corri(["rm", "-rf", "/home/%s" % chi], tempo=30)


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente", default="c7u1",
                   help="the test tenant: it is created NEW and deleted")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--registro", default="/var/lib/rete11/registro.log")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--resta", type=float, default=20.0,
                   help="how long the client stays attached")
    p.add_argument("--attesa-palco", type=float, default=45.0,
                   help="how long to wait for the log to name the child. "
                        "Expired: «I do not know», ⛔ NEVER green")
    p.add_argument("--attesa-chiusura", type=float, default=45.0,
                   help="how long to wait for the field to be free again AFTER the "
                        "closing. ⛔ We wait for the EVENT, and we print how long "
                        "it took: a slow but complete closing is green")
    p.add_argument("--solo-distacco", action="store_true",
                   help="⭐ the client goes away and the session does NOT close: "
                        "it must stay GREEN (I4)")
    p.add_argument("--lascia-un-processo", action="store_true",
                   help="⛔ the grafted fault: before closing a process of the tenant "
                        "is left on purpose ⇒ it must give red")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if os.geteuid() != 0:
        print("⛔ it must be run as administrator: it creates and deletes a tenant")
        sys.exit(2)
    if not os.path.exists(a.cliente):
        print("⛔ I cannot find the test client: %s" % a.cliente)
        print("   ⇒ I could not look")
        sys.exit(3)
    if leggi(a.registro) is None:
        print("⛔ I cannot read the server log: %s" % a.registro)
        print("   ⇒ I could not look")
        sys.exit(3)

    chi = a.utente
    print("== C7 — everything closes, and nothing remains ==")
    print("   tenant «%s» · port %d" % (chi, a.porta))
    print("   mode: %s" % (
        "⭐ DETACH ONLY — the client goes away and the session does NOT close: "
        "it must stay GREEN (I4)" if a.solo_distacco else
        "⛔ GRAFTED FAULT — a process is left on purpose: it must give RED"
        if a.lascia_un_processo else "normal round: it opens, detaches, closes"))
    print()

    # ⛔ IT IS DELETED BEFORE CREATING IT: «from zero» also includes «from zero
    #    with respect to myself of yesterday» (`LEZIONI.md` §1.39, and the real defect
    #    found in C1 on 26 Aug 2026).
    sgombera(chi)
    # ⛔ The card's groups are no longer inside the `useradd`: they are given by
    #    the tool, which READS them from the `/dev/dri` nodes and then READS BACK.
    fatto = subprocess.run(
        ["/bin/sh", "-c",
         "useradd -m -s /bin/bash %s && "
         "printf '%s:%s\n' | chpasswd" % (chi, chi, a.parola)],
        capture_output=True, text=True)
    if fatto.returncode != 0:
        print("⛔ I could not create «%s»: %s"
              % (chi, fatto.stderr.strip()[:120]))
        print("   ⇒ I could not look")
        sys.exit(3)
    # ⛔⛔ AND WITHOUT THE CARD'S GROUPS WE DO NOT MEASURE: `[M]` the session is born
    #     blind, and the «leftovers» of a session never born say nothing.
    e_gr, perche_gr = garantisci_i_gruppi(chi)
    if e_gr != 0:
        # ⭐ The tool's outcome is propagated, not a nailed-down 3: «I could not
        #   look» (3) and «wrong usage» (2) have different names.
        print("   %s" % perche_gr)
        print("   ⇒ I do not measure — ⛔ and it is NOT a red (§4.5): outcome %d" % e_gr)
        sys.exit(e_gr)

    esito = 3
    try:
        prima = raccogli(chi)
        if prima is None:
            print("⛔ the tenant «%s» does not exist: ⇒ I could not look" % chi)
            sys.exit(3)
        stampa_impronta("FINGERPRINT BEFORE — the field must be free:", prima)

        # -------------------------------------------------------------------
        # We mark where we are in the log BEFORE opening, so the judgement
        # looks only at the slice of THIS round (like C1).
        segno = len(leggi(a.registro) or "")

        print("   the client attaches and stays %.0f s…" % a.resta)
        tetto_cliente = max(90, a.resta * 4)
        try:
            r = subprocess.run(
                ["python3", a.cliente,
                 "--indirizzo", a.indirizzo, "--porta", str(a.porta),
                 "--utente", chi, "--parola", a.parola, "--resta", str(a.resta)],
                capture_output=True, text=True, timeout=tetto_cliente)
            uscita, errore = (r.stdout or ""), (r.stderr or "")
        except subprocess.TimeoutExpired:
            # ⛔⛔ §1.51 — WITHOUT THIS `except` THE BENCH ACCUSED THE PRODUCT.
            #    `subprocess.TimeoutExpired` does not descend from `OSError` and the
            #    `try` of this block has only a `finally`: a traceback here
            #    made Python exit **1**, ⇒ the hook read **NON REGGE**,
            #    ⇒ §5.2 sent someone to repair a fault that was not the product's.
            #    ⭐ C9 already caught the same thing; C7 did not (27 Aug 2026).
            print("   ⛔ the TEST CLIENT did not come back within %.0f s: it got"
                  % tetto_cliente)
            print("      stuck itself, and this is a fault of the BENCH.")
            print("   ⇒ I could not look — ⛔ and it is NOT a red of the "
                  "product (§4.5, §1.51)")
            sys.exit(3)
        # ⛔ NOT `"AMMESSO" in uscita`: the word is also in the two refusals, and
        #    it arrives on stdout — see `e_stato_ammesso()` at the top.
        ammesso = e_stato_ammesso(uscita + errore)
        if ammesso is not True:
            # ⛔ «Not admitted» on its own is a silence: the REASON is carried
            #    next to the symptom (C1's lesson, 26 Aug 2026).
            coda = uscita + errore
            motivo = "?"
            for riga in reversed(coda.strip().splitlines()):
                riga = riga.strip()
                if riga and not riga.startswith("=="):
                    motivo = riga[:90]
                    break
            # ⭐ The two «no»s are said by name (§1.44: mixing them is half the
            #   defect).  ⚠ Both lead to **3** in GUARD 2 of
            #   `giudica_residui()`: a client turned away is not a broken
            #   product.
            print("   ⛔ %s: %s"
                  % ("the client was TURNED AWAY by the server"
                     if ammesso is False else
                     "the client said NOTHING", motivo))

        # ⛔ We wait for the EVENT — the log naming the child — not
        #    the clock.  `[M]` 26 Aug 2026 in C1: with a fixed wait of 1.5 s
        #    six rounds out of six said «I do not know» because the stage is born in ~13 s.
        figlio_nato = False
        scadenza = time.time() + a.attesa_palco
        while time.time() < scadenza:
            fetta = (leggi(a.registro) or "")[segno:]
            if any(m.group("chi") == chi for m in FIRMA_FIGLIO.finditer(fetta)):
                figlio_nato = True
                break
            time.sleep(0.5)
        print("   the child in the log: %s"
              % ("⭐ born" if figlio_nato else "⛔ never named"))

        staccato = raccogli(chi)
        stampa_impronta("FINGERPRINT AFTER THE DETACH — ⭐ here the stage MUST "
                        "still be standing (I4):", staccato)

        dopo = staccato
        secondi_chiusura = None
        if not a.solo_distacco:
            if a.lascia_un_processo:
                # ⛔ THE GRAFTED FAULT, and it has the shape of the real child:
                #    a process that runs as the tenant but hangs from the server,
                #    not from its systemd slice ⇒ `terminate-user` does not
                #    take it away (`[M]` 26 Aug 2026, measured before writing).
                subprocess.Popen(
                    ["/usr/sbin/runuser", "-u", chi, "--", "/bin/sleep", "300"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, start_new_session=True)
                time.sleep(1.5)
                print("   ⛔ grafted fault: a `sleep` of «%s» left "
                      "outside its systemd slice\n" % chi)

            print("   the session is CLOSED: loginctl terminate-user %s" % chi)
            partenza = time.time()
            corri(["loginctl", "terminate-user", chi], tempo=60)
            # ⭐ We wait for the EVENT, and we print how long it took.  A
            #   slow but complete closing is GREEN: a clock ceiling
            #   would have called it red (§1.49).
            scadenza = time.time() + a.attesa_chiusura
            tornato = False
            while time.time() < scadenza:
                dopo = raccogli(chi)
                if dopo is not None and not differenze(prima, dopo)[0]:
                    tornato = True
                    break
                time.sleep(0.5)
            secondi_chiusura = time.time() - partenza
            # ⛔⛔ AND THE MESSAGE IS BUILT BY READING BACK THE RESULT, not by
            #    copying the intention (`LEZIONI.md` §1.48: *«a success message
            #    that repeats the intention is not a verification, it is an
            #    echo»*).  `[M]` 26 Aug 2026, first round with the grafted fault:
            #    here it said **«the field took 45.48 s to go back
            #    as before»** ⛔ and the field had not gone back at all — the
            #    ceiling had expired.  ⚠ The verdict was right anyway (red),
            #    but the line above the verdict said something false, and it is
            #    exactly the kind of line that then sends someone to calibrate in the dark.
            if tornato:
                print("   ⭐ the field WENT BACK as before in %.2f s "
                      "(declared ceiling: %.0f s)\n"
                      % (secondi_chiusura, a.attesa_chiusura))
            else:
                print("   ⛔ the field did NOT go back as before within the declared "
                      "ceiling of %.0f s\n" % a.attesa_chiusura)
            stampa_impronta("FINGERPRINT AFTER THE CLOSING — here nothing must "
                            "remain:", dopo)

        esito, specie, motivi = giudica(
            prima, staccato, dopo, solo_distacco=a.solo_distacco,
            ammesso=ammesso, figlio_nato=figlio_nato)

        # ⛔ §1.47: the mute entries are declared, or they pass the comparison without
        #    having looked at anything.
        _d, mute = differenze(prima, dopo if dopo is not None else staccato)
        # ⚠ And an entry that says VUOTO in all three fingerprints is «equal»
        #   without ever having spoken: on the XFCE box it is the case of
        #   `/dev/dri`, because without a compositor nobody opens the card.
        immobili = [v for v in GIUDICATE
                    if prima.get(v) == VUOTO and staccato.get(v) == VUOTO]
        if mute:
            print("⚠ ⛔ %d entries the fingerprint could not answer — and"
                  % len(mute))
            print("   «I do not know» equal to «I do not know» WOULD PASS the comparison:")
            for v in mute:
                print("     · %s" % v)
            print()
        if immobili:
            print("⚠ %d entries stayed EMPTY even with a live session: they"
                  % len(immobili))
            print("   passed the comparison ⛔ without ever having had anything to say:")
            for v in immobili:
                print("     · %s" % v)
            print("   ⇒ on this box it holds for the graphics card until the")
            print("     session mounts a compositor (§7-bis.13).\n")

        if esito == 1 and specie == "leftovers":
            residui, _ = differenze(prima, dopo)
            print("⛔⛔ RED — %s" % motivi[0])
            for voce, va, vb in residui:
                print("   · %-34s before: %s" % (voce, va))
                print("     %-34s after : %s" % ("", vb))
            print()
            print("   ⇒ the session ended and the machine did not go back as")
            print("     it found it: ⛔ the next tenant starts on an occupied")
            print("     field, and the fault will show up elsewhere.")
        elif esito == 1:
            print("⛔⛔ RED (kind: %s)" % specie)
            for riga in motivi:
                print("   %s" % riga)
        elif esito == 0:
            print("⭐ GREEN — %s" % motivi[0])
            for riga in motivi[1:]:
                print("   %s" % riga)
            if secondi_chiusura is not None:
                print("   ⚠ and it took %.2f s: it is a MEASUREMENT, not a ceiling"
                      % secondi_chiusura)
        elif esito == 2:
            print("⛔ BAD TERRAIN (outcome 2)")
            for riga in motivi:
                print("   %s" % riga)
        else:
            print("⚠ NOT JUDGING (outcome 3)")
            for riga in motivi:
                print("   %s" % riga)
            print("   ⛔ And this is not a green: it is an outcome of its own (§4.5).")

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ WITH THE GRAFTED FAULT THE OUTCOME IS READ BACKWARDS, and it is not a
        #     whim: it is the hook's convention, written in `11-gancio.sh`
        #     inside `esegui_maglia` — *«a mesh with the grafted fault exits 0
        #     when the fault WAS SEEN»*.  ⇒ The hook derives from it
        #     `ha_visto_il_guasto`, and ⭐ **it is that key that keeps
        #     C13 alive** (*«the certification is recent»*).
        # ⚠ If C7 exited 1 with the fault seen, the hook would write
        #   `ha_visto_il_guasto: false` ⛔ and C13 would say that the net can no longer
        #   say red precisely in the round in which it gave the red.
        # ⛔ And ONLY 0 and 1 are inverted: 2 and 3 are not judgements, and an «I did
        #   not look» turned upside down would become an invented green.
        # ═══════════════════════════════════════════════════════════════════
        if a.lascia_un_processo and esito in (0, 1):
            print()
            # ⛔⛔ AND THE COLOUR IS NOT ENOUGH — §1.52, and it is the cure of 27 Aug 2026.
            #     A red is a red, but «the fault was seen» means
            #     that the INJECTION bit: it is demanded that among the leftovers there is
            #     precisely the `sleep` (see `guasto_visto`).
            morso = guasto_visto(prima, dopo)
            if esito == 1 and morso:
                print("⭐ THE GRAFTED FAULT WAS SEEN ⇒ this mesh CAN "
                      "say red")
                print("   ⭐ and the leftover is precisely the injected `%s`, not a "
                      "defect that was already there (§1.52)" % NOME_INIETTATO)
                print("   ⚠ and that is why it exits **0**: with the grafted fault the outcome "
                      "is read backwards (convention of 11-gancio.sh)")
                esito = 0
            elif esito == 1:
                print("⛔⛔ RED, but NOT because of the fault: among the leftovers there is")
                print("    not the `%s` I had injected." % NOME_INIETTATO)
                print("    ⇒ either `terminate-user` took it away, or the red")
                print("      comes from a defect of the PRODUCT — and certifying the")
                print("      net on a defect of the product is §1.52.")
                esito = 1
            else:
                print("⛔⛔ THE GRAFTED FAULT WAS NOT SEEN: a process was left "
                      "on purpose and the fingerprint came back clean.")
                print("    ⇒ either `terminate-user` took it away, or this "
                      "mesh does not look in the right place — ⛔ and in both")
                print("      cases it cannot be trusted (`LEZIONI.md` §1.44).")
                esito = 1
    finally:
        # ⛔ Whoever opens, closes (`LEZIONI.md` §9-ter): even with the grafted fault,
        #    and even if the judgement went badly.
        sgombera(chi)
    sys.exit(esito)


if __name__ == "__main__":
    main()
