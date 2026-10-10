#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c1 — ⭐⭐ THE FIRST MESH OF THE NET: «the session is born and is SEEN»
===========================================================================

    python3 11-c1-nasce-e-si-vede.py --giri 8
    python3 11-c1-nasce-e-si-vede.py --certifica

⛔ It is also ACCEPTANCE TEST A of phase 11: pointed at the code of 25
   August 2026, this mesh must turn RED on the «session that is born
   blind» — without anyone having told it where to look.

---------------------------------------------------------------------------
⛔⛔ WHY IT RUNS SEVERAL TIMES, and not just once

`fasi/10-multi-tenant-e-il-budget.md` §7.4: the fault is **INTERMITTENT**.
`[M]` 25 August 2026, on the real machine:

    user          succeeded  failed
    provanic3         2          6
    provanic4         0         98
    provanic5         0         55

⇒ ⛔ **A single test is not a test**: on `provanic3` it would have said green two
   times out of eight.  ⭐ It is `LEZIONI.md` §1.32 — *«it happens sometimes» often means
   «it always happens, it is just waiting for the moment»*.

---------------------------------------------------------------------------
⭐ WHAT IT LOOKS AT — and where it starts from

  where it starts: ⛔ FROM ZERO, and «from zero» here means **a NEW USER** at
                  every round, not a new attach.
                  ⚠⚠ And the reason is invariant I4: the stage belongs to the
                  SESSION, not to the connection, and **it survives detach**.
                  ⇒ Re-attaching with the same user does NOT make anything be born:
                  it finds the stage of the previous round, already alive and already
                  with its monitor.  ⛔ A bench like that would say green eight times
                  while looking at **a single birth** — which is literally
                  the method error for which the fault stayed invisible
                  for days (`LEZIONI.md` §1.39).
                  ⭐ And it is also the way the fault showed itself on the
                  iron: NEW users, `provanic4/5/6`, 0 succeeded out of 98/55/50.
  what it looks at: ⛔ NOT the process count, which said «1» both with the
                  window and without.  It looks at **whether the monitor was BORN**, and
                  asks two independent witnesses (below).

---------------------------------------------------------------------------
⛔⛔⛔ THE BIGGEST DEFECT THIS MESH HAS EVER HAD — 27 August 2026

⚠ It sits at the top because it is the kind of defect that repeats, and because for
  days it held five tests still and postponed a whole phase.

⛔⛔ **C1 could not say green, and had never said it.**  The two lines it
    judged on were both wrong, and in the worst way:

  1. ⛔ it read `sessione [chi] ⛔ ZERO MONITOR` as **proof of blindness**.
     `[R]` The product writes it in the **mandatory step of a SUCCESSFUL
     birth** (`src/sessione.c:345-348`): since 14 August *«zero monitors of
     its own»* is the **intended** state, and the monitor is mounted by CAPTURE, later.
     ⇒ The line C1 read as the fault was the line of health.
  2. ⛔ and the green branch asked for `sessione [chi] monitor N/N: connettore`,
     `[R]` which **never appears** in a healthy birth: `sessione_stato()` is
     no longer called after the stage is taken.  `[M]` 27 Aug 2026, in
     the whole log of the cured box: **0 times**.

⇒ ⭐⭐ **A red that cannot be made green** — `LEZIONI.md` §1.49
  in its worst form.  And the verdict was never «C1 is wrong»: it
  was *«the session is born blind»*, for days, on five tests.

⛔⛔ AND THE CERTIFICATION COULD NOT CATCH IT, because **it imposed the defect
    as a requirement**: its two «healthy» cases used exactly the line the
    product does not write.  ⇒ It passed, and it passed because the judge was broken.
  ⭐ The cure is not only the new judgement: it is that there is now **a
    certification case that starts from a HEALTHY log and ends GREEN**.  A judge
    that has no green case is not a strict judge: it is a broken judge, and
    nobody notices until someone tries to make it pass.

---------------------------------------------------------------------------
⭐⭐ THE THREE WITNESSES — two judge, one is printed

  ⭐ A · `cattura [chi] negotiated format: WxH …`     (`src/cattura.c:686`)
        It is **the instant the monitor is born**: the `wl_output` appears only
        when a PipeWire consumer hooks onto the stream.  `[M]` 27 Aug
        2026, cured GNOME box: **1.105 s · 0.998 s · 0.957 s** from the
        «session opened» line, and it appears **8 times** in the whole log.

  ⭐ B · `⭐ the stage of «chi»: … monitor «Meta-0» (0 before, 1 after), 1920x1080 …`
        (`src/figlio.c:1826`, written by the PARENT).  ⛔ It counts as a witness only
        if it says **both** things: that a monitor is there (**M ≥ 1**) **and** at
        what size.  ⚠ `monitor «» (0 before, 2 after), 0x0` — the famous «third
        state» of 25 August — is not a monitor: it is a count with nothing
        underneath, and it is exactly the number that for months was read as
        «two monitors appeared».

  ⚠ C · `figlio [chi] loop: N frames delivered` — ⛔ **it is printed and NOT
        judged**, and the reason is §1.45: nobody has ever measured how long
        that line takes to appear after the birth.  ⇒ Putting it in the
        verdict would mean calibrating a ceiling in the dark.  ⭐ When it is missing with
        a monitor born, a FINDING is printed — so it is seen, and the day
        someone measures it, it can be promoted.

⭐ And the two that judge are INDEPENDENT for real: A is written by the CHILD, B
  is written by the PARENT.  ⇒ The day one of the two lines changes form, C1
  does not go blind on its own — the other one remains, and the count says so.

⛔⛔ AND ONE LINE IS DISCARDED, by name: the stage lines that end with
    *«— waiting for the client's canvas»*.  `[M]` On that branch (`src/figlio.c:5287`)
    the product sent the parent a structure **never initialised** ⇒ the
    counts in there are garbage, and they unmasked themselves
    (`stride 306537694`).  ⚠ The cure has been in the product since 27 August, ⛔ but the
    cured binary is not yet in the boxes.  ⇒ Until it is, they are
    discarded — and ⭐ COUNTED and PRINTED, because a silent exclusion is
    an exclusion nobody notices.

⚠ And here the yardstick is the PRODUCT LOG, not an image — ⛔ and this is
  a declared limit, not a detail: the product could say «monitor
  1/1» and deliver black pixels.  ⭐ The mesh that looks at the pixels is C2, and it wants
  the witness; this one looks at the BIRTH, which is the layer below.
  ⇒ `fasi/11-la-rete-di-sicurezza.md` §6, «what the net does not catch».

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)

  0  ⭐ I looked: all rounds were born with a monitor
  1  I looked: AT LEAST ONE was born blind          ⇒ red
  3  ⛔ I could not look (the server was not there, the client did not start,
     the log could not be read) — ⛔ and it is NOT a red
  2  the terrain does not hold / wrong usage
===========================================================================
"""
import argparse
import os
import re
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE SIGNATURES, taken LITERALLY from the product log.
#
# ⛔ We do not look for a word inside a text (`CODER.md` §3.3-bis, corollary 3:
#    «ACCESA» is true also in «nasce accesa, ed e' spenta»).  We look for whole
#    lines, anchored, and the tenant's name is COMPARED, not contained.
#
# ⛔⛔⛔ AND THESE SIGNATURES WERE REDONE FROM SCRATCH ON 27 AUGUST 2026, because
#       the old ones made C1 say something false.  The story is at the top
#       of the file, under «THE BIGGEST DEFECT THIS MESH HAS EVER HAD».
# ═══════════════════════════════════════════════════════════════════════════

# ⭐⭐ WITNESS A — `src/cattura.c:686`.  It is **the instant the monitor
#     is born**: the `wl_output` appears only when a PipeWire consumer
#     hooks onto the stream, ⇒ this line cannot be written without a monitor.
#     `[M]` 27 Aug 2026, cured GNOME box: it appears **8 times**, at
#     1.105 s · 0.998 s · 0.957 s from the «session opened» line.
FIRMA_FORMATO = re.compile(
    r"cattura +\[(?P<chi>[^\]]+)\] negotiated format: (?P<l>\d+)x(?P<a>\d+)")

# ⭐⭐ WITNESS B — `src/figlio.c:1826`, the line the PARENT writes when the
#     child sends it `MSG_PALCO`.  ⚠ The identity is in the BODY («%s») and not
#     in the brackets, because the parent writes it: it is the same reason why
#     C9 keeps those lines out of the mandatory set.
#     `[M]` 27 Aug 2026, cured box: `monitor «Meta-0» (0 before, 1 after),
#     1920x1080`.
FIRMA_PALCO = re.compile(
    r"the stage of «(?P<chi>[^»]+)»:.*?monitor «(?P<nome>[^»]*)» "
    r"\((?P<prima>\d+) before, (?P<dopo>\d+) after\), (?P<l>\d+)x(?P<a>\d+) stride")

# ⛔⛔ THE TRAP, AND IT IS MEASURED — `src/figlio.c:5287`.
#
# On the «waiting for the client's canvas» branch the product sent the parent a
# structure **never initialised**: field by field, the stack memory as
# the previous call had left it.  ⇒ The counts of THOSE lines are
# garbage, and they unmasked themselves (`stride 306537694`).
# ⚠ `[M]` 27 Aug 2026 the cure is in the product (the `memset` moved up before
#   every exit path), ⛔ **but the cured binary is not yet in the boxes**.
# ⇒ Until it is, those lines are DISCARDED by name — and ⭐ COUNTED and
#   PRINTED: an exclusion that cannot be seen is an exclusion nobody
#   notices.
CODA_SPAZZATURA = "waiting for the client's canvas"

# ⭐ WITNESS C — the frames delivered.  ⚠ It is printed and NOT judged:
#   see «the three witnesses» at the top of the file, where the reason is.
FIRMA_FOTOGRAMMI = re.compile(
    r"figlio +\[(?P<chi>[^\]]+)\] loop: (?P<n>\d+) frames delivered")

# ⚠⚠ AND THIS IS NO LONGER A PROOF OF BLINDNESS — `src/sessione.c:345-348`.
#
# ⛔⛔ Until 27 August 2026 it was **the red** of this mesh.  `[R]` The
#     product writes it in the mandatory step of a **SUCCESSFUL** birth:
#     since 14 August *«zero monitors of its own»* is the **intended** state, and the monitor
#     is mounted by CAPTURE, later.  ⇒ It is counted and printed — because it is the line
#     that for months was read backwards, and seeing it counted with zero
#     judgements is what prevents falling into it again — ⛔ but it decides nothing.
FIRMA_ZERO_MONITOR = re.compile(
    r"sessione \[(?P<chi>[^\]]+)\] .*ZERO MONITOR")


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⛔ «WAS THE CLIENT ADMITTED?» — ⭐ AND THIS IS THE HOME, FOR EVERYONE.
#
# ⛔ The word «AMMESSO» inside the client's output is NOT the admission.
#    `[R]` `01-b3-cliente.py` writes it in **three** cases, and two are refusals —
#    and all three end up on **stdout**, because the refusal goes through the
#    handler at the end of the file (`01-b3-cliente.py:2560`), which *prints* the error:
#
#      · admitted  `01-b3-cliente.py:1615`
#            «   AMMESSO after 1023 ms   ⭐ the fixed second is there»
#      · REFUSAL 1 `01-b3-cliente.py:1315-1317` (`CONGEDO` in its place)
#            «   ⛔ RuntimeError: CONGEDO instead of AMMESSO: reason 0x03 = …»
#      · REFUSAL 2 `01-b3-cliente.py:1322` (another message arrived)
#            «   ⛔ RuntimeError: expected AMMESSO, arrived CONGEDO»
#
# ⇒ ⛔ `"AMMESSO" in uscita` is **TRUE IN ALL THREE**: it is a predicate that cannot
#   say no, i.e. `LEZIONI.md` §1.44 — ⛔ and precisely in the case it
#   exists to catch.  ⚠ A mesh like that believes it got in **even
#   when it was turned away**, then looks at the darkness that follows and calls it
#   a product defect: a credentials refusal came out as *«no
#   frame arrived from the wire»* — an accusation against the wire.
#
# ⭐ The true signature is a WHOLE LINE — `^\s*AMMESSO after ` — and ⛔ it is not a
#   sixth solution: it is **the same** one the refutation agent put in
#   `11-c2-…py:311` and `11-c3-…py:331` on 27 August 2026.
#
# ⭐⭐ AND IT LIVES IN ONE PLACE ONLY — §1.47.  Five copies of the same line are
#     five places to diverge from again.  ⇒ C5, C6, C7 and C9
#     **import it from here** and do not rewrite it; if they cannot import it
#     they exit **3** and say so, ⛔ instead of silently falling back on the
#     poor predicate.
#     ⚠ Why in C1 and not in a new file: `11-accendi.sh` copies into the
#       box the files **one by one, by name** (lines 258-274), and a new file
#       would not be copied ⇒ the five meshes would exit 3 in every
#       box.  ⭐ C1 is already copied into all of them, and «a mesh that imports from
#       another mesh» is already the shape of the project (C2 and C3 import
#       `giudica()` from `10-f1-testimone.py` and `frazione_del_colore()` from C8).
# ═══════════════════════════════════════════════════════════════════════════
FIRMA_AMMESSO = re.compile(r"^\s*AMMESSO after ", re.M)


def e_stato_ammesso(coda):
    """⛔ THREE states, and the third is not a no.

    `True`  — the admission line is there.
    `False` — the client spoke, and that line is not there: **it is a
              refusal**, ⛔ not a broken product ⇒ the caller exits **3**.
    `None`  — the client said nothing at all: I do not know.
    """
    if not coda or not coda.strip():
        return None
    return bool(FIRMA_AMMESSO.search(coda))


def certifica_ammissione(sigla):
    """⭐ The admission cases, the same for all the meshes that use it.

    ⛔ It lives here with the predicate: a certification that sits far from the thing
       certified is a certification that one day no longer follows the thing.
    Returns `(guai, quanti)`.
    """
    casi = [
        ("⭐ the REAL admission line ⇒ True",
         "   → CIAO\n   ← ECCOMI\n"
         "   AMMESSO after 1023 ms   ⭐ the fixed second is there\n", True),
        ("⭐ admitted but under the second (§4.4-bis violated) ⇒ stays True",
         "   AMMESSO after 4 ms   ⛔ LESS THAN ONE SECOND: §4.4-bis violated\n",
         True),
        ("⛔ REFUSAL 1 «CONGEDO instead of AMMESSO» — the word is there ⇒ False",
         "   → CREDENZIALI\n"
         "   ⛔ RuntimeError: CONGEDO instead of AMMESSO: reason 0x03 = "
         "wrong credentials\n", False),
        ("⛔ REFUSAL 2 «expected AMMESSO, arrived …» — likewise ⇒ False",
         "   ⛔ RuntimeError: expected AMMESSO, arrived CONGEDO\n", False),
        ("⛔ «waiting for AMMESSO»: waiting for it is not having it ⇒ False",
         "   [reg] waiting for AMMESSO\n", False),
        ("⛔ «AMMESSO» stuck to something else is not the line ⇒ False",
         "   NON-AMMESSO after 12 ms\n", False),
        ("⚠ the client said NOTHING ⇒ None, and it is not a «no»",
         "", None),
        ("⚠ only spaces ⇒ None", "   \n\n  ", None),
        ("⚠ `leggi()` failed (None) ⇒ None", None, None),
    ]
    guai = 0
    print("  ── «AMMESSO» is a LINE, not a word (§1.44) "
          "— C1's predicate, imported by %s" % sigla)
    for nome, testo, atteso in casi:
        avuto = e_stato_ammesso(testo)
        ok = avuto is atteso
        if not ok:
            guai += 1
        print("  %s  %-62s  %-5s (expected %s)"
              % ("OK " if ok else "NO ", nome[:62], avuto, atteso))
    return guai, len(casi)


# ═══════════════════════════════════════════════════════════════════════════
# ⛔⛔⭐ THE CARD'S GROUPS — ⭐ AND THIS IS THE HOME, FOR ALL FIVE.
#
# ⛔ It is the other face of the same defect as «AMMESSO»: not a check that
#    cannot fail, but **a condition that is not guaranteed** and that
#    nobody notices.  ⇒ The mesh measures a BLIND session and calls it
#    a product defect.
#
# ⭐ `fasi/10-…` §7.4 — «the session is born blind», the oldest defect of the
#    project — was closed on 27 August 2026, and the cause is exactly
#    this: the tenant not in the groups of the `/dev/dri` nodes.
#
#      | tenants WITH the two groups | `[M]` **17 of 17** see, in ~2 s       |
#      | WITHOUT                     | `[M]` **0 of 4**, never in 90 s, 0 fr.|
#      | ⭐ counter-test             | groups given to the same ⇒ **2.04 s** |
#
# ⛔⛔ AND IN HERE THERE WERE TWO HOLES, both measurable in the code:
#   1. `[R]` the `--riusa-utente` branch **skipped entirely** the groups
#      step: a diagnosis round could measure a blind tenant;
#   2. `[R]` the branch that creates nailed down `usermod -aG video,render` **and did not
#      read back**: `video` and `render` are the names of THIS distribution, and
#      a successful `usermod` does not mean «it is in there» (⛔ E1, «written is not
#      in force»).  ⚠ The same hole was in C5, C6, C7 and C9.
#
# ⭐⭐ THE TOOL ALREADY EXISTS AND IS NOT REWRITTEN — `banchi/attrezzi-gruppi-scheda.sh`
#     (§1.47).  It reads the gid from every `card*`/`renderD*` with `stat -c %g`, asks
#     `getent` for the name, puts the tenant in and **reads back comparing the
#     numbers**.  ⛔ That is why there is no group name and no number here.
# ⛔ And if the tool is not found we do NOT invent a copy and do NOT try to
#    guess with `video,render`: we exit **3** and say which line is missing.
# ═══════════════════════════════════════════════════════════════════════════
NOME_ATTREZZO_GRUPPI = "attrezzi-gruppi-scheda.sh"

# ⭐ The tool's codes, taken from its box (`gruppi_scheda_dai_a`).
#    ⛔ None of them is **1**: a blind tenant is not a broken product.
CODICI_GRUPPI = {
    0: (0, "⭐ the tenant is in the groups of the card's nodes: it can see"),
    # ⚠ `2` is the tool saying «must be run AS ROOT»: it is not the product and
    #   not the tenant, it is the USAGE ⇒ outcome **2**, which has its own name.
    2: (2, "⛔ the groups tool must be run AS ROOT, and this bench does not "
           "run as root: it is wrong usage, not a defect"),
    3: (3, "⛔ it is NOT in the groups of the /dev/dri nodes: its session would be born "
           "BLIND (`[M]` 0 of 4), and this bench would measure the darkness"),
    4: (3, "⛔ the groups were written JUST NOW but the tenant already had "
           "live processes: written yes, IN FORCE NO — the running session "
           "is still blind"),
    5: (3, "⛔ a gid of the nodes has no name in /etc/group: the tenant "
           "cannot join it"),
}


def verdetto_gruppi(codice):
    """⭐ From the tool's code to the outcome of §4.5.  Returns `(esito, perche)`.

    ⛔ `0` means «it can be measured», not «green».  ⛔ And there is no branch
       that gives **1**: a blind tenant is a fault of the BENCH (§1.51),
       and blaming the product for it is exactly the error that postponed a phase.
    """
    if codice in CODICI_GRUPPI:
        return CODICI_GRUPPI[codice]
    return 3, ("⛔ the groups tool exited with a code I do not "
               "know (%s): I cannot tell whether the tenant sees" % codice)


def trova_attrezzo_gruppi():
    """⛔ The path of the tool, or `None`.  It is a FINDER, not a judge.

    ⚠ The places: next to me (inside the box everything is in `/opt/remotix`), one
      level up (in the repository it is `banchi/`), and `/rete11`, which is the repository
      mounted read-only inside the box.
    """
    qui = os.path.dirname(os.path.abspath(__file__))
    for base in (qui, os.path.dirname(qui), "/opt/remotix", "/rete11",
                 os.path.join("/rete11", "..")):
        p = os.path.join(base, NOME_ATTREZZO_GRUPPI)
        if os.path.exists(p):
            return p
    return None


def garantisci_i_gruppi(chi, prefisso="       "):
    """⭐⭐ Puts the tenant in the card's groups and VERIFIES it is there.

    Returns `(esito, perche)`: `0` = it can be measured, `3` = ⛔ it is not measured.
    ⚠ It prints what the tool says, because an exclusion that cannot be seen is
      an exclusion nobody notices.
    """
    attrezzo = trova_attrezzo_gruppi()
    if attrezzo is None:
        print("%s⛔⛔ I cannot find `%s`, and without it I cannot GUARANTEE that"
              % (prefisso, NOME_ATTREZZO_GRUPPI))
        print("%s    «%s» sees the card." % (prefisso, chi))
        print("%s    ⛔ And I do not rewrite it here: ten copies of the same"
              % prefisso)
        print("%s    line are ten places to diverge from (§1.47), and"
              % prefisso)
        print("%s    `video,render` are the names of ONE distribution."
              % prefisso)
        print("%s    ⭐ The cure, a line in `11-accendi.sh` next to the other"
              % prefisso)
        print("%s    `cp` lines of the «product» step:" % prefisso)
        print("%s        cp /rete11/%s /opt/remotix/"
              % (prefisso, NOME_ATTREZZO_GRUPPI))
        print("%s    ⚠ and for `/rete11` to have it, a `cp` from the repository"
              % prefisso)
        print("%s    into `banchi/11-scatole/` — or the mount of"
              % prefisso)
        print("%s    `banchi/` instead of `banchi/11-scatole/`." % prefisso)
        return 3, "the card groups tool is missing"
    r = subprocess.run(["bash", attrezzo, chi], capture_output=True, text=True)
    for riga in (r.stdout or "").splitlines():
        if riga.strip():
            print(riga.rstrip())
    esito, perche = verdetto_gruppi(r.returncode)
    if esito != 0:
        for riga in (r.stderr or "").strip().splitlines()[-3:]:
            print("%s%s" % (prefisso, riga.strip()[:100]))
    return esito, perche


def certifica_gruppi(sigla):
    """⭐ The card groups cases, the same for all the meshes.

    ⛔ The case that matters: a tenant **without** the groups ⇒ the mesh says
       «I could not look» (**3**), ⛔ **never red** — a blind tenant
       is not a broken product (§1.51).
    Returns `(guai, quanti)`.
    """
    casi = [
        ("⭐ the tool says 0 (it really is in there) ⇒ we measure", 0, 0),
        ("⛔⛔ NOT in the groups of the nodes ⇒ 3, ⛔ AND NEVER 1 (the real case)", 3, 3),
        ("⚠ the tool says «as root» ⇒ 2, wrong usage and it has its own name",
         2, 2),
        ("⛔ groups WRITTEN but not in force (processes already alive) ⇒ 3", 4, 3),
        ("⛔ a gid of the nodes with no name in /etc/group ⇒ 3", 5, 3),
        ("⚠ a code I do not know ⇒ 3, ⛔ no guessing", 7, 3),
        ("⚠ `bash` did not find the tool (127) ⇒ 3", 127, 3),
        ("⚠ the tool killed by a signal (-9) ⇒ 3", -9, 3),
    ]
    guai = 0
    print("  ── the card's groups: ⛔ without them, the session is born BLIND "
          "(`[M]` 0 of 4) — C1's step, imported by %s" % sigla)
    for nome, codice, atteso in casi:
        e, perche = verdetto_gruppi(codice)
        ok = (e == atteso) and e != 1
        if not ok:
            guai += 1
        print("  %s  %-62s  outcome %d (expected %d)"
              % ("OK " if ok else "NO ", nome[:62], e, atteso))
    # ⛔⛔ AND THE GUARD THAT KEEPS THE TABLE HONEST: no code, not even one
    #     never seen, must be able to give **1**.  ⚠ Without this line the table
    #     above would test only the codes I wrote myself.
    rossi = [c for c in list(range(-32, 256)) if verdetto_gruppi(c)[0] == 1]
    ok = not rossi
    if not ok:
        guai += 1
    print("  %s  ⛔⛔ NO code between -32 and 255 gives RED (a blind "
          "tenant is not a broken product)" % ("OK " if ok else "NO "))
    return guai, len(casi) + 1


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE WAITING CEILING — and it is a MEASUREMENT, not a round number (§1.45).
#
# `[M]` **27 August 2026, CURED GNOME box**, three new sessions: the
# `negotiated format` arrives in
#
#         1.105 s        0.998 s        0.957 s        ⇒ maximum **1.105 s**
#
# ⛔⛔ AND BEFORE TODAY THIS NUMBER WAS 152 s, for a measurement that was not the
#     product's.  `[M]` The ~97 seconds of delay were a fault of the BOX:
#     §6 of the recipe moved the `polkitd` group from 991 to 1991 to give
#     991 to `render`, and `groupmod -g` **does not carry the files along** ⇒ `polkitd`
#     could no longer read `/etc/polkit-1/rules.d`, died, and `gnome-shell`
#     took four 25 s timeouts.  ⇒ ⚠ A ceiling calibrated on that number
#     would have been **a hundred times** the real phenomenon: ⛔ a ceiling like that does not
#     protect, it **hides** — once expired it has nothing more to say.
#
# ⭐ THE MARGIN, AND WHERE IT COMES FROM — and it is not the margin of today's
#   spread (0.957-1.105 s, 15 %), which would be a margin measured on a
#   single machine at rest:
#
#     · the healthy phenomenon, today               `[M]`  1.105 s
#     · ⚠ the slowest birth EVER measured in
#       this project — 26 Aug 2026, loaded
#       box, and it is the line that sits in the body
#       of `main()` below                           `[M]` ~13 s
#     · the margin declared on THAT one             **× 2**
#                                                   ⇒ **26 s**
#
#   ⇒ 26 s are **24 times** the healthy phenomenon and **twice** the worst ever
#     seen.  ⚠ The margin sits on the worst on purpose: the box can be
#     loaded, and the real machine has an **integrated Intel UHD 730**, not a
#     powerful card.  ⛔ Tightening down to 1 s would mean calibrating on the
#     machine at rest and calling «blind» the machine under load.
#
# ⚠ AND THE COST: `[S]` a healthy round costs ~30 s (20 s of `--resta` + ~1 s
#   of waiting + the cleanup), a BLIND round costs the whole ceiling, ~55 s.
#   ⇒ `COSTO_C1_GIRO = 74` in the hook stays **prudent** and covers both:
#   it must not be changed, and the two rounds of the fast family (148 s) fit
#   again within the 180 s.
TETTO_NASCITA = 26.0


def leggi(percorso):
    try:
        with open(percorso, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return None


class Nascita(object):
    """The facts of ONE birth, read from the log slice of that round.

    ⛔ `None` means «I did not see it», never zero: they are two different facts and
       must not have the same face (§4.5, question 8).
    """

    def __init__(self):
        self.nominato = False       # the log talks about this tenant
        self.formato = None         # ⭐ witness A: (width, height)
        self.monitor_dopo = None    # ⭐ witness B: the M of «(N before, M after)»
        self.monitor_nome = None
        self.monitor_misura = None  # the size declared by the stage line
        self.fotogrammi = None      # ⚠ witness C: printed, NOT judged
        self.palchi_scartati = 0    # ⛔ the «waiting for the canvas» lines: counted
        self.zero_monitor = 0       # ⚠ counted and printed, NOT judged


def leggi_nascita(testo, chi):
    """⭐ The judge, and it touches nothing: it is certified by calling it.

    ⛔ Returns `None` if there is nothing to look at — and `None` is not «blind».
    """
    if not testo:
        return None
    n = Nascita()
    marca, virgolette = "[%s]" % chi, "«%s»" % chi

    for riga in testo.splitlines():
        # ⚠ Homonymy is closed off with the delimiters: «c1u1» is not inside
        #   «c1u10», and `[c1u1]` is not inside `[c1u10]`.
        if marca in riga or virgolette in riga:
            n.nominato = True

        m = FIRMA_FORMATO.search(riga)
        if m and m.group("chi") == chi:
            n.formato = (int(m.group("l")), int(m.group("a")))

        m = FIRMA_PALCO.search(riga)
        if m and m.group("chi") == chi:
            # ⛔⛔ THE TRAP: on that branch the counts are garbage.
            #    ⭐ It is discarded, COUNTED and will be said out loud.
            if CODA_SPAZZATURA in riga:
                n.palchi_scartati += 1
            else:
                n.monitor_dopo = int(m.group("dopo"))
                n.monitor_nome = m.group("nome")
                n.monitor_misura = (int(m.group("l")), int(m.group("a")))

        m = FIRMA_FOTOGRAMMI.search(riga)
        if m and m.group("chi") == chi:
            n.fotogrammi = int(m.group("n"))

        m = FIRMA_ZERO_MONITOR.search(riga)
        if m and m.group("chi") == chi:
            n.zero_monitor += 1
    return n


def monitor_nato(n):
    """⭐ The two witnesses of the monitor, and ONE is enough — but they are independent.

    ⚠ Independent for real: one is written by the CHILD (`cattura.c`), the other
      by the PARENT (`figlio.c`).  ⇒ The day one of the two lines changed
      form, C1 would not go blind: the other would remain, and the printed
      count would say only one of them is speaking.
    Returns the list of the witnesses that spoke.
    """
    if n is None:
        return []
    testimoni = []
    if n.formato is not None and n.formato[0] > 0 and n.formato[1] > 0:
        testimoni.append("negotiated format %dx%d" % n.formato)
    # ⛔ And the stage counts as a witness only if it says both things: that a
    #    monitor is there (M ≥ 1) **and** at what size.  ⚠ `monitor «» (0 before, 2
    #    after), 0x0` — the real line of 25 August — is not a monitor: it is a
    #    count with nothing underneath, and it is exactly the line that for months
    #    was read as «two monitors appeared».
    if (n.monitor_dopo is not None and n.monitor_dopo >= 1
            and n.monitor_misura is not None
            and n.monitor_misura[0] > 0 and n.monitor_misura[1] > 0):
        testimoni.append("stage: monitor «%s» (%d after) %dx%d"
                         % (n.monitor_nome, n.monitor_dopo,
                            n.monitor_misura[0], n.monitor_misura[1]))
    return testimoni


def verdetto_giro(n):
    """From the facts to the STATE of the round.  ⛔ Three, and they are three different things:

      «NATA»       ⭐ the monitor is there, and at least one witness says so
      «CIECA»      ⛔ the session started and the monitor was NOT born  ⇒ red
      «NON-LO-SO»  ⛔ the log does not talk about this tenant: I looked at
                   nothing — ⛔ and it is NOT a red (§4.5)
    """
    testimoni = monitor_nato(n)
    if testimoni:
        return "NATA", " · ".join(testimoni)
    if n is None:
        return "NON-LO-SO", "the log slice is empty"
    if not n.nominato:
        return "NON-LO-SO", ("the log does not name «this» tenant in the "
                             "slice: the session did not really start")
    return "CIECA", ("the session started and NEITHER of the two witnesses of the "
                     "monitor spoke")


# ---------------------------------------------------------------------------
# ⭐⭐ THE CERTIFICATION — and the first line of the list is the most important.
#
# ⛔⛔ UNTIL 27 AUGUST 2026 THERE WAS NOT A SINGLE CASE HERE THAT ENDED GREEN
#     STARTING FROM A HEALTHY LOG.  ⚠ The two cases «healthy session» and «blind after
#     mounting» used the line `sessione [chi] monitor N/N: connettore`,
#     ⛔ which the product **never** writes in a successful birth — and so
#     the certification **imposed the defect as a requirement**: it passed, and
#     it passed precisely because the judge was wrong.
# ⇒ ⭐ It is `LEZIONI.md` §1.49 in its worst form, and it is the reason why
#   the defect stayed standing: **a judge that has no green case is not
#   a strict judge, it is a broken judge.**
# ---------------------------------------------------------------------------

# ⭐ THE HEALTHY LOG, transcribed from the cured GNOME box (`[M]` 27 Aug
#   2026).  ⛔ It is not invented: they are the lines the product really writes,
#   in the order it writes them.
#   ⚠ And `⛔ ZERO MONITOR` is in there too, on purpose: in a SUCCESSFUL birth
#     that line is there, and it is the mandatory step in which the session does not
#     yet have monitors of its own.  ⇒ If someone one day put it back among the
#     reds, this case would turn red and say so.
#   (10 Oct 2026: the lines follow the English text of the product, `english-migration/`.)
SANO = (
    "20:07:42.262 rcp     [c1u1] admitted utente=c1u1 da=[127.0.0.1]:58048\n"
    "20:07:43.100 figlio  [c1u1] entering the stage mounting (canvas 1920x1080): "
    "telling the parent to wait\n"
    "20:07:43.910 sessione [c1u1] ⛔ ZERO MONITORS, and the session is alive: it is the "
    "«alive, complete and BLACK» session of STUDI.md §gnome §3.1 — there is nothing "
    "to capture\n"
    "20:07:44.367 cattura [c1u1] negotiated format: 1920x1080 BGRx (8 bits per "
    "channel), modifier 0x0\n"
    "20:07:44.402 figlio  ⭐ the stage of «c1u1»: bus OPEN, session 1, grab 1, "
    "monitor «Meta-0» (0 before, 1 after), 1920x1080 stride 7680 at 32 bits, "
    "1 streams delivering\n"
    "20:07:45.100 figlio  [c1u1] loop: 37 frames delivered (1 keyframes)\n")

# ⛔ THE LOG OF THE REAL FAULT — the lines of 25 August 2026, transcribed from
#    `fasi/10-multi-tenant-e-il-budget.md` §7.4 and from `fasi/11…` §7-bis.
#    ⚠ `(0 before, 2 after)` is the famous «third state»: ⛔ a count with
#      nothing underneath (`0x0`), which for months was read as «two monitors».
CIECO = (
    "22:42:14.100 rcp     [c1u1] admitted utente=c1u1 da=[127.0.0.1]:58048\n"
    "22:42:15.826 sessione [c1u1] ⛔ ZERO MONITORS, and the session is alive: it is the "
    "«alive, complete and BLACK» session of STUDI.md §gnome §3.1\n"
    "22:42:18.145 figlio  ⛔ the stage of «c1u1»: bus OPEN, session 1, grab 0, "
    "monitor «» (0 before, 2 after), 0x0 stride 0 at 0 bits, 0 streams delivering\n")


def certifica():
    """⛔ It proves that the judge can say GREEN, RED and «I do not know».

    ⚠ And it declares what it covers and what it does not.
      COVERS: **the reading of the log and the rule** — that the two witnesses of the
      monitor are recognised, that the garbage line is discarded,
      that «⛔ ZERO MONITOR» decides nothing, and ⭐ that a HEALTHY log
      ends GREEN.
      ⛔ DOES NOT COVER: that the log tells the truth about the pixels.  That is C2, and
      it wants the witness.
      ⇒ A certification that declares itself wider than it is is worth less
        than no certification.
    """
    casi = [
        # (name, text, who, expected state, extra check or None)

        # ═══════════════════════════════════════════════════════════════════
        # ⭐⭐⭐ THE CASE THAT DID NOT EXIST, AND IT IS THE ONE THAT MATTERS: a
        #      HEALTHY log must end GREEN.  ⛔ Without it the green of this
        #      mesh was unreachable and nobody noticed.
        # ═══════════════════════════════════════════════════════════════════
        ("⭐⭐ THE HEALTHY LOG ENDS GREEN (the case that was missing)",
         SANO, "c1u1", "NATA",
         lambda n: n.formato == (1920, 1080) and n.monitor_dopo == 1
                   and n.monitor_misura == (1920, 1080) and n.fotogrammi == 37),

        # ⭐ And the two witnesses are INDEPENDENT: one is enough, and it is tested
        #   by removing the other.  ⇒ The day one of the two lines changes
        #   form, C1 does not go blind on its own.
        ("⭐ with ONLY `negotiated format` (no stage line) ⇒ GREEN",
         "20:07:43.100 figlio  [c1u1] entering the stage mounting\n"
         "20:07:44.367 cattura [c1u1] negotiated format: 1920x1080 BGRx\n",
         "c1u1", "NATA", lambda n: n.monitor_dopo is None),

        ("⭐ with ONLY the stage line (no `negotiated format`) ⇒ GREEN",
         "20:07:43.100 figlio  [c1u1] entering the stage mounting\n"
         "20:07:44.402 figlio  ⭐ the stage of «c1u1»: monitor «Meta-0» "
         "(0 before, 1 after), 1920x1080 stride 7680 at 32 bits, 1 streams\n",
         "c1u1", "NATA", lambda n: n.formato is None),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔ AND THE RED — which is still the real fault of 25 August.
        # ═══════════════════════════════════════════════════════════════════
        ("⛔ the REAL fault of 25 August ⇒ CIECA",
         CIECO, "c1u1", "CIECA",
         lambda n: n.monitor_dopo == 2 and n.monitor_misura == (0, 0)
                   and n.zero_monitor == 1),

        # ⭐ The half that gets forgotten (§1.49): with the fault removed, it is GREEN again.
        #   ⛔ It is the same tenant and the same log shape.
        ("⭐ and with the fault removed it is GREEN again — the counter-test of §1.49",
         SANO, "c1u1", "NATA", None),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ «⛔ ZERO MONITOR» NO LONGER DECIDES ANYTHING — and it is the defect
        #     in person.  ⚠ The healthy log has it inside (see `SANO`): if
        #     it became a red again, the first case of the list would fail.
        #     ⇒ Here the pure case is tested: ONLY that line, and nothing else.
        # ═══════════════════════════════════════════════════════════════════
        ("⭐⭐ «ZERO MONITOR» + `negotiated format` ⇒ GREEN (it was the red!)",
         "20:07:43.910 sessione [c1u1] ⛔ ZERO MONITORS, and the session is alive\n"
         "20:07:44.367 cattura [c1u1] negotiated format: 1920x1080 BGRx\n",
         "c1u1", "NATA", lambda n: n.zero_monitor == 1),

        # ⚠ And the other direction: on its own that line is not a WITNESS of the
        #   monitor — it neither denies nor affirms it.  ⇒ Here the round stays CIECA
        #   because neither of the two witnesses spoke, ⛔ not because it
        #   says «ZERO MONITOR».
        ("⛔ «ZERO MONITOR» alone is not a WITNESS ⇒ stays CIECA",
         "20:07:43.910 sessione [c1u1] ⛔ ZERO MONITORS, and the session is alive\n",
         "c1u1", "CIECA", lambda n: n.zero_monitor == 1),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ THE MEASURED TRAP: the stage line that ends with
        #     «— waiting for the client's canvas» carries GARBAGE counts.
        #     ⚠ `stride 306537694` is the real number that unmasked itself.
        # ═══════════════════════════════════════════════════════════════════
        ("⛔⛔ the «waiting for the canvas» line is DISCARDED (counts are garbage)",
         "20:07:43.100 figlio  [c1u1] entering the stage mounting\n"
         "20:07:43.200 figlio  ⛔ the stage of «c1u1»: monitor «\x01\x02» "
         "(0 before, 3 after), 1440x900 stride 306537694 at 32 bits, 0 streams "
         "delivering — waiting for the client's canvas\n",
         "c1u1", "CIECA",
         lambda n: n.palchi_scartati == 1 and n.monitor_dopo is None),

        ("⭐ …and the GOOD line arriving after the discarded one still counts",
         "20:07:43.200 figlio  ⛔ the stage of «c1u1»: monitor «x» (0 before, "
         "3 after), 1440x900 stride 306537694 at 32 bits, 0 streams delivering "
         "— waiting for the client's canvas\n"
         "20:07:44.402 figlio  ⭐ the stage of «c1u1»: monitor «Meta-0» "
         "(0 before, 1 after), 1920x1080 stride 7680 at 32 bits, 1 streams\n",
         "c1u1", "NATA", lambda n: n.palchi_scartati == 1),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔ «I COULD NOT LOOK» — and it is not a red (§4.5).
        # ═══════════════════════════════════════════════════════════════════
        ("⛔ silent log ⇒ «I do not know», ⛔ NOT blind",
         "20:07:42.000 avvio   ⭐ ready: https://…\n", "c1u1", "NON-LO-SO",
         lambda n: not n.nominato),

        ("⛔ the slice is EMPTY ⇒ «I do not know», and the judge returns None",
         "", "c1u1", "NON-LO-SO", None),

        # ⚠ Homonymy, in both directions: «c1u1» is not «c1u10», nor the
        #   reverse.  ⛔ An `in` without delimiters would have swapped the two.
        ("⚠ the log talks about ANOTHER tenant ⇒ «I do not know»",
         SANO.replace("c1u1", "c1u2"), "c1u1", "NON-LO-SO",
         lambda n: not n.nominato),

        ("⚠ «c1u1» is not confused with «c1u10» (homonymy is closed off)",
         SANO.replace("c1u1", "c1u10"), "c1u1", "NON-LO-SO",
         lambda n: not n.nominato),

        # ⛔ A monitor «born» at size zero was not born: it is a count with
        #    nothing underneath.  ⚠ It is the heart of the red of 25 August, isolated.
        ("⛔ «(0 before, 1 after), 0x0» is NOT a monitor ⇒ CIECA",
         "20:07:43.100 figlio  [c1u1] entering the stage mounting\n"
         "20:07:44.402 figlio  ⛔ the stage of «c1u1»: monitor «» (0 before, "
         "1 after), 0x0 stride 0 at 0 bits, 0 streams\n",
         "c1u1", "CIECA", lambda n: n.monitor_dopo == 1),

        # ⚠ The frames are READ and do not decide: it is tested that a monitor
        #   born without frames stays GREEN, and that the count is visible.
        ("⚠ monitor born and ZERO frames ⇒ GREEN (the frames do not judge)",
         "20:07:44.367 cattura [c1u1] negotiated format: 1920x1080 BGRx\n"
         "20:07:45.100 figlio  [c1u1] loop: 0 frames delivered (0 keyframes)\n",
         "c1u1", "NATA", lambda n: n.fotogrammi == 0),
    ]

    print("== certification of C1's judge ==")
    print("   ⛔ it covers THE READING AND THE RULE, not the pixels (see the top)\n")
    guai = 0
    for nome, testo, chi, atteso, extra in casi:
        n = leggi_nascita(testo, chi)
        stato, perche = verdetto_giro(n)
        ok = (stato == atteso) and (extra is None or (n is not None and extra(n)))
        print("  %s  %-62s  %-10s (expected %s)"
              % ("OK " if ok else "NO ", nome[:62], stato, atteso))
        if not ok:
            guai += 1
            print("        ⛔ why: %s" % perche)

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ AND THE CEILING IS CERTIFIED LIKE A THRESHOLD — ⛔ or it is a number that
    #     nobody checks any more (`LEZIONI.md` §1.45).
    #
    # ⚠ And the margin sits on the WORST ever measured, not on today's
    #   spread: the spread of three measurements on a machine at rest says
    #   nothing about a loaded box.  ⇒ See `TETTO_NASCITA` at the top.
    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE ADMISSION CASES — ⛔ the ones that were not there before today.
    #    The predicate lives in this file and serves four other meshes: it is
    #    certified here, once, for all.
    print()
    guai_amm, quanti_amm = certifica_ammissione("C1")
    guai += guai_amm

    # ⭐⭐ AND THE CARD GROUPS CASES — ⛔ the other case that was missing.
    print()
    guai_gr, quanti_gr = certifica_gruppi("C1")
    guai += guai_gr

    MISURE_SANE = (1.105, 0.998, 0.957)   # `[M]` 27 Aug 2026, cured box
    PEGGIORE_MAI_VISTA = 13.0             # `[M]` 26 Aug 2026, loaded box
    MARGINE = 2.0
    serve = PEGGIORE_MAI_VISTA * MARGINE
    tetto_ok = TETTO_NASCITA >= serve
    if not tetto_ok:
        guai += 1
    print()
    print("  %s  the ceiling covers the slowest birth EVER measured: "
          "%.0f s × %.0f = %.0f s ⇒ ceiling %.0f s"
          % ("OK " if tetto_ok else "NO ", PEGGIORE_MAI_VISTA, MARGINE,
             serve, TETTO_NASCITA))
    print("      ⇒ and that is %.0f times today's healthy phenomenon (%.3f s)"
          % (TETTO_NASCITA / max(MISURE_SANE), max(MISURE_SANE)))

    quanti = len(casi) + quanti_amm + quanti_gr + 1
    print()
    if guai:
        print("⛔ the judge is NOT reliable: %d cases out of %d wrong"
              % (guai, quanti))
        return 1
    print("⭐ %d cases out of %d: the judge can say GREEN, can say RED and can say"
          % (quanti, quanti))
    print("   «I do not know» — ⭐ and **green is reachable**, which is the thing")
    print("   this certification did not test and should have tested.")
    print("⚠ and it covers the READING, not the pixels (see the top)")
    return 0


# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--giri", type=int, default=8,
                   help="how many NEW sessions to open (the fault is intermittent)")
    p.add_argument("--utente-base", default="c1u",
                   help="at every round «<base><n>» is created: a NEW user, "
                        "because re-attaching does not make anything be born (I4)")
    p.add_argument("--riusa-utente", default="",
                   help="⛔ for diagnosis only: a single user for all rounds. "
                        "It is NOT the test — it finds the stage already alive")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8511)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--registro", default="/var/lib/rete11/registro.log")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--resta", type=float, default=20.0)
    p.add_argument("--attesa-palco", type=float, default=TETTO_NASCITA,
                   help="how long to wait for one of the two witnesses of the "
                        "monitor to speak. ⭐ 26 s = the slowest birth EVER "
                        "measured (13 s, 26 Aug) × 2, i.e. 24 times "
                        "today's healthy phenomenon (1.105 s) — see TETTO_NASCITA "
                        "at the top. ⛔ Expired is NOT a green: it is «blind» if "
                        "the session had started, «I do not know» if it had not")
    p.add_argument("--attesa-sgombero", type=float, default=45.0,
                   help="how long to wait for the tenant of the previous round "
                        "to be REALLY gone. ⛔ Without it, the next round starts on a "
                        "field still occupied and does not judge")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        sys.exit(certifica())

    if not os.path.exists(a.cliente):
        print("⛔ I cannot find the test client: %s" % a.cliente)
        print("   ⇒ I could not look")
        sys.exit(3)
    if leggi(a.registro) is None:
        print("⛔ I cannot read the server log: %s" % a.registro)
        print("   ⇒ I could not look")
        sys.exit(3)

    print("== C1 — the session is born and is seen ==")
    print("   %d rounds · %s · port %d"
          % (a.giri,
             ("⛔ ONE SINGLE user «%s» (diagnosis, it is NOT the test)" % a.riusa_utente)
             if a.riusa_utente else
             ("a NEW USER at every round: «%s1»…«%s%d»"
              % (a.utente_base, a.utente_base, a.giri)),
             a.porta))
    print("   ⛔ the fault is intermittent: a single round would not be a test\n")

    esiti = []
    creati = []
    for giro in range(1, a.giri + 1):
        # ⛔ The NEW user is created here, and created the way the
        #    machine would create it: `useradd -m`, the card's two groups, the password.
        #    ⚠ If this part fails the outcome is «I do not know», NEVER green.
        #
        # ⛔⛔ AND IT IS DELETED BEFORE CREATING IT — `[M]` 26 August 2026, and this
        #    line is worth more than it looks.
        #    The first draft did `id -u X || useradd X`: i.e. ⇒ **the user
        #    was NEW only the FIRST time this bench ran in its
        #    life.**  From the second round on it found «c1u1» as it had been left —
        #    and with it its leftovers.
        #    `[M]` The symptom: the hook ran C1 twice in a row, and
        #    the second time the first round said **«I do not know»** instead of
        #    judging.  ⛔ Not a red: one judgement fewer, which is the silent
        #    way in which a test stops being useful.
        #    ⚠ It is the same form of error as C8 with the `/tmp/mozilla` left over from the
        #      previous round: ⭐ **«from zero» also includes «from zero with respect to
        #      myself of yesterday»**.
        if a.riusa_utente:
            chi = a.riusa_utente
        else:
            chi = "%s%d" % (a.utente_base, giro)
            subprocess.run(
                ["/bin/sh", "-c",
                 "loginctl terminate-user %s 2>/dev/null; "
                 "pkill -KILL -u %s 2>/dev/null; "
                 "userdel -r %s 2>/dev/null; rm -rf /home/%s"
                 % (chi, chi, chi, chi)],
                capture_output=True, text=True)
            # ⛔ And the card's groups are NO LONGER in here: they are given by
            #    the tool, which READS them from the nodes and then READS BACK (see
            #    the top).  ⚠ `usermod -aG video,render` nailed down two names and
            #    verified nothing.
            fatto = subprocess.run(
                ["/bin/sh", "-c",
                 "useradd -m -s /bin/bash %s && "
                 "printf '%s:%s\n' | chpasswd" % (chi, chi, a.parola)],
                capture_output=True, text=True)
            if fatto.returncode != 0:
                print("  round %2d/%d  ?    I could not create «%s»: %s"
                      % (giro, a.giri, chi, fatto.stderr.strip()[:80]))
                esiti.append(("NON-LO-SO", None))
                continue
            creati.append(chi)

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ THE CARD'S GROUPS — ⭐ ON BOTH BRANCHES, reuse included.
        #
        # ⛔ Until 27 August 2026 the `--riusa-utente` branch skipped this
        #    step: ⇒ a diagnosis round could measure a BLIND tenant and
        #    call it a product defect.  ⚠ And the other branch gave them to nailed-down
        #    names without reading back, which is the same thing on a smaller scale.
        # ⭐ The step sits HERE, outside the `if`, so there is no branch in which to
        #    forget it again.
        # ⛔ And if it cannot be guaranteed, the round does NOT measure: «I do not know», ⛔ never
        #    red — a blind tenant is a fault of the bench (§1.51).
        # ═══════════════════════════════════════════════════════════════════
        e_gr, perche_gr = garantisci_i_gruppi(chi)
        if e_gr != 0:
            print("  round %2d/%d  ?    «%s» is not in a condition to see"
                  % (giro, a.giri, chi))
            print("       %s" % perche_gr)
            esiti.append(("NON-LO-SO", None))
            continue

        # ⛔ We mark WHERE we are in the log BEFORE opening, so the judgement
        #    looks only at the slice of THIS round.  A bench that read the whole
        #    file would read the previous rounds — and it really happened in
        #    this project (phase 9: a bench read the numbers of the bench before).
        prima = leggi(a.registro)
        segno = len(prima) if prima is not None else 0

        r = subprocess.run(
            ["python3", a.cliente,
             "--indirizzo", a.indirizzo, "--porta", str(a.porta),
             "--utente", chi, "--parola", a.parola,
             "--resta", str(a.resta)],
            capture_output=True, text=True, timeout=max(60, a.resta * 4))
        # ⛔ NOT `"AMMESSO" in r.stdout`: the word is also in the TWO refusals,
        #    and it arrives on stdout — see `e_stato_ammesso()` at the top.
        #    `[M]` 26 Aug 2026 it is exactly this mesh that paid the bill:
        #    five rounds said «NON-AMMESSO» and nobody knew why.
        # ⭐ Three states, and they are kept separate all the way.
        ammesso = e_stato_ammesso((r.stdout or "") + (r.stderr or ""))

        # ⛔⛔ WE WAIT FOR THE EVENT, NOT FOR THE CLOCK.
        #
        # `[M]` 26 August 2026: with a fixed wait of 1.5 s **six rounds out of six**
        # said «I do not know» — not because something was broken, but because
        # the stage is born in ~13 s and the bench looked after 1.5.
        # ⇒ ⛔ A clock deadline is a deadline that fires whenever it happens.
        #
        # ⭐⭐ AND WE LEAVE THE LOOP ONLY ON GREEN — 27 Aug 2026.
        #   ⛔ «Blind» is not something that is seen: it is something that is NOT
        #   seen, and to say «I did not see it» one must have waited the whole
        #   declared time.  ⚠ The old loop left also on red, and on
        #   a red that was the wrong line — i.e. it left at once and judged
        #   a session that was still being born.
        n = None
        istante = None
        scadenza = time.time() + a.attesa_palco
        partenza_attesa = time.time()
        while time.time() < scadenza:
            dopo = leggi(a.registro)
            fetta = dopo[segno:] if dopo is not None else None
            n = leggi_nascita(fetta, chi)
            if monitor_nato(n):
                istante = time.time() - partenza_attesa
                break
            time.sleep(0.5)

        stato, perche = verdetto_giro(n)
        fot = None if n is None else n.fotogrammi

        if ammesso is not True:
            # ⛔ «Not admitted» on its own is a silence: it hides three different
            #    things — the client did not start, the server refused,
            #    the wire was not there.  `[M]` 26 August 2026: five rounds
            #    said «NON-AMMESSO» and the real cause was that the box
            #    was missing `aioquic`, i.e. the client could not even
            #    try.  ⇒ The REASON is carried next to the symptom.
            coda = (r.stdout or "") + (r.stderr or "")
            motivo = "?"
            for riga in reversed(coda.strip().splitlines()):
                riga = riga.strip()
                if riga and not riga.startswith("=="):
                    motivo = riga[:70]
                    break
            # ⭐ And the two «no»s are said by name: «turned away» and «did not speak»
            #   are not the same thing, and mixing them is what made the
            #   five rounds of 26 August silent.  ⚠ Both count among the NOT
            #   JUDGED (outcome 3): ⛔ a client turned away is not a broken
            #   product, and a silent client is not a judgement.
            stato = "NON-AMMESSO" if ammesso is False else "NON-LO-SO"
            perche = motivo
            faccia = "?"
            print("       ⛔ %s — why: %s"
                  % ("TURNED AWAY by the server (not a product red)"
                     if ammesso is False
                     else "the client said NOTHING", motivo))
        elif stato == "NATA":
            faccia = "YES"
        elif stato == "CIECA":
            faccia = "NO"
        else:
            faccia = "?"
        esiti.append((stato, fot))
        print("  round %2d/%d  %-3s  %-10s  frames: %-9s %s"
              % (giro, a.giri, faccia, stato,
                 "unknown" if fot is None else fot,
                 ("in %.3f s" % istante) if istante is not None else ""))
        # ⭐ And the WITNESS is named, green or red: a verdict without
        #   its yardstick is an opinion (C11).
        print("       %s" % perche)
        if n is not None:
            if n.palchi_scartati:
                print("       ⚠ %d stage lines DISCARDED («%s»): their "
                      "counts are garbage" % (n.palchi_scartati,
                                              CODA_SPAZZATURA))
            if n.zero_monitor:
                print("       ⚠ «⛔ ZERO MONITOR» ×%d — ⭐ and it is NOT a red: it is "
                      "the mandatory step of a successful birth"
                      % n.zero_monitor)
            if stato == "NATA" and not n.fotogrammi:
                print("       ⚠ FINDING, not verdict: the monitor was born and the "
                      "frames are %s — ⛔ this mesh does not judge them "
                      "(see the top)"
                      % ("zero" if n.fotogrammi == 0 else "unknown"))

        # ⛔⛔ AND NOW WE CLEAN UP, or the next round no longer starts from zero.
        #
        # `[M]` 26 August 2026, first real round of this mesh: without this
        # piece, the six rounds left **six live sessions** retrying
        # all together (I4: the stage survives detach), and from the second round
        # on the compositor no longer answered ⇒ ⛔ **five «I do not know» out of
        # six**.  ⚠ They were not reds — the bench had the decency not to
        # judge — but a test that does not judge is useless.
        #
        # ⭐ And the cleanup is of ONE'S OWN folder only: the user of THIS round
        #   is closed, by name, never a global pattern (phase 10 §7.3, where
        #   a global `pkill -f` risked killing the work of another
        #   test that was measuring).
        if not a.riusa_utente:
            subprocess.run(["loginctl", "terminate-user", chi],
                           capture_output=True, text=True)
            time.sleep(1.0)
            subprocess.run(["pkill", "-KILL", "-u", chi],
                           capture_output=True, text=True)
            # ⛔⛔ AND NOW WE WAIT FOR IT TO BE REALLY GONE, not half a
            #    second by the clock.
            #
            # `[M]` 26 August 2026, ten rounds: ⛔ **`? NO ? NO ? NO ? NO ? NO`**
            # — a PERFECT alternation between «I do not know» and «blind».  ⚠ A perfect
            # alternation is not chance: it is **a state that survives the round**.
            # ⇒ The hypothesis that explains it: the cleanup returns AT ONCE, and the next round
            #   starts while the previous one is still dying — the new
            #   compositor cannot even be born, and the log says neither
            #   «monitor» nor «blind» ⇒ «I do not know».  The round after that finds
            #   the field free and judges.
            # ⛔ And a test that judges HALF the time is worth half.
            #   ⭐ We wait for the EVENT — the user no longer having either session
            #   or processes — and if it does not go away within the declared time, ⚠ we
            #   SAY SO, instead of starting anyway pretending not to know.
            scadenza = time.time() + a.attesa_sgombero
            libero = False
            while time.time() < scadenza:
                viva = subprocess.run(["loginctl", "show-user", chi],
                                      capture_output=True, text=True).returncode == 0
                proc = subprocess.run(["pgrep", "-u", chi],
                                      capture_output=True, text=True).returncode == 0
                if not viva and not proc:
                    libero = True
                    break
                time.sleep(0.5)
            if not libero:
                print("       ⚠ «%s» did not go away in %.0f s: the next round "
                      "does NOT start from a free field" % (chi, a.attesa_sgombero))

    print()
    ciechi = sum(1 for s, _ in esiti if s == "CIECA")
    ignoti = sum(1 for s, _ in esiti if s in ("NON-LO-SO", "NON-AMMESSO"))
    sani = sum(1 for s, _ in esiti if s == "NATA")
    print("  born with a monitor: %d   ⛔ BLIND: %d   not judged: %d"
          % (sani, ciechi, ignoti))
    print("  ⭐ the yardstick: the monitor was born if at least one of the two")
    print("     witnesses says so — `cattura … negotiated format: WxH` (src/cattura.c)")
    print("     or `the stage of «chi»: … monitor «N» (x before, M after), WxH`")
    print("     with M ≥ 1 and a real size (src/figlio.c).")
    print("  ⛔ and «⛔ ZERO MONITOR» is NOT a witness: it is the mandatory")
    print("     step of a successful birth (src/sessione.c:345).")

    # ⛔⛔ AND THE GUARD OF §1.44: zero rounds judged is not a green.
    #     ⚠ Without it, `--giri 0` — or eight rounds all «not admitted» — would exit
    #     **0** having looked at nothing, with the face they have when they look.
    if sani == 0 and ciechi == 0:
        print("\n  ⚠ NOT JUDGING — no round looked at a birth.")
        print("     ⛔ And this is not a green: it is an outcome of its own (§4.5, §1.44).")
        sys.exit(3)

    if ciechi:
        print("\n  ⛔⛔ RED — %d sessions out of %d were born BLIND." % (ciechi, len(esiti)))
        print("     No application can open a window on those sessions.")
        sys.exit(1)
    if ignoti:
        print("\n  ⚠ NOT JUDGING — %d rounds did not speak." % ignoti)
        print("     ⛔ And this is not a green: it is an outcome of its own (§4.5).")
        sys.exit(3)
    print("\n  ⭐ GREEN — all %d sessions were born with a monitor." % len(esiti))
    sys.exit(0)


if __name__ == "__main__":
    main()
