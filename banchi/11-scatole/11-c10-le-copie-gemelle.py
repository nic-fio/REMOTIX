#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c10 — ⭐ «THE TWO TWIN COPIES OF THE PROTOCOL MATCH»
===========================================================================

    python3 11-c10-le-copie-gemelle.py
    python3 11-c10-le-copie-gemelle.py --radice /other/repository
    python3 11-c10-le-copie-gemelle.py --certifica

⭐ **It is the only mesh of the list that does not need a box.**  It
   starts nothing, does not ask for the graphics card, does not want podman: it reads
   FILES.  ⇒ It runs on the laptop, on the test machine, inside a box,
   inside a hook — `fasi/11…` §4.1, column «where it runs»: **anywhere**.
   ⚠ And it runs **before compiling**, which is the other half of the C10 row: it is
     exactly the moment when the defect can still be stopped at zero
     cost.

---------------------------------------------------------------------------
⭐ WHY TWO COPIES EXIST — and it is not an oversight to clean up
---------------------------------------------------------------------------

`rcp.c`, `rcp.h` and `autenticazione.c` live in **two folders** of this
repository, and they are there **on purpose**:

  `src/`         the module mounted on the **product server**
  `banchi/rcp/`  the same module mounted on the **graft inside the ngtcp2
                 example** (`bsslserver`), which is the bench with which the protocol
                 was tested on bare QUIC

⇒ ⭐ **They are the same module mounted on two hosts** — `src/Makefile`, box
  «THE THREE COPIES THAT MUST BE ONE» (finding R12.3, night of 10 August
  2026), and `DECISIONI.md` §1.12 box «the mute slot», where the cell of
  `RCP.md` §0-bis declares that the two copies are **identical byte for byte**.

⛔ **And until that night they were identical BY LUCK, not by construction**:
   no file of the repository compared them.  The concrete case nobody
   would have seen, written in the Makefile: `BAN_DURATA` in `src/rcp.c` is changed
   from twelve hours to one.  The product bans for one hour; `01-b6-lancia.sh` stays
   green because it compares `banchi/rcp/` with the copy compiled inside
   `examples/`; B8 stays green because it starts `bsslserver`.
   ⇒ ⛔ **The defect changes the colour of nothing.**

---------------------------------------------------------------------------
⛔⛔ WHAT MUST MATCH — **the whole file, byte for byte**
---------------------------------------------------------------------------

⚠ This is the real decision of this mesh, and it could not be taken
  by reading a comment («written is not in force», E1): a plain `diff` on two
  legitimately different files would give **red for ever**, and a perpetual red
  is not caution, it is noise (`LEZIONI.md` §1.49).

⭐ So it was **looked at before being declared**.  `[M]` 26 August
  2026, on this repository:

      rcp.c              identical  md5 8ddf04859e60…   7 691 lines
      rcp.h              identical  md5 432d06e909c7…   1 297 lines
      autenticazione.c   identical  md5 86451cd1c8bb…     202 lines

  ⇒ There is **no** legitimately different point between the two copies: it is not
    a «client copy» against a «server copy», it is **the same
    file**.  ⭐ So the yardstick is the strictest possible — **byte for
    byte** — and it can be because today it is green: the counter-proof of §1.49
    («try to make it turn green») is already done, and it is the real run.

---------------------------------------------------------------------------
⭐⭐ AND WHAT THIS MESH ADDS TO WHAT WAS ALREADY THERE
---------------------------------------------------------------------------

The comparison **was already there**, in two places, and the C10 row says so: *«it is already
there, and only needs hooking up»*.  ⛔ But the two places that existed both have the
same hole, and it is not the comparison:

  `src/Makefile`, target `impronte`
      ⭐ stops the build if they diverge, and prints the `diff`.
      ⛔ But it wants `make`, a compiler, `pkg-config`, ngtcp2 and the libraries
        of phase 4: it runs **where one compiles**, not anywhere.

  `banchi/04-b23-lancia.sh`, first block
      does the same comparison in bash.
      ⛔ But it keeps **its own** copy of the list, pinned in the `for`:
        `for f in rcp.c rcp.h autenticazione.c`.  ⇒ Two lists in two files
        that can drift apart without anyone noticing.

⛔⛔ **AND THE COMMON HOLE: neither of the two notices a NEW PAIR.**

    The list of twins is `GEMELLATI` inside `src/Makefile`, and it is three names
    written by hand.  The day a fourth twin file is born — say
    `ban.c` in `src/` and in `banchi/rcp/` — and nobody touches that line:

      · the Makefile compares the usual three and says **OK**
      · `04-b23` compares the usual three and says **✅**
      · ⛔ **the fourth diverges for months, and it is red nowhere**

    ⇒ ⭐⭐ It is **exactly** `LEZIONI.md` §1.47: a green check that has not
      looked at anything, with the same face as when it really looked.

⭐ So this mesh does **three things**, and the third is the reason why it is worth
  writing it instead of just hooking up the Makefile:

  1. it **compares** the declared copies, byte for byte;
  2. ⛔ it **does not keep a list of its own**: it **READS** `GEMELLATI` from `src/Makefile`.
     ⚠ A list copied here would have been the **third**, and the third copy of
       a list is the third place it can diverge from.  ⛔ And if it cannot
       read it **it does not fall back on a pinned list**: it says «I could not
       look» — a fallback list silently replacing the real one
       is the most convenient lie this mesh could tell;
  3. ⭐ it **checks that the list COVERS the folder**: every source that lives in
     `banchi/rcp/` **and also** in `src/` is a de facto twin, and if it is not
     declared in `GEMELLATI` this mesh gives **red** — even if the three
     declared ones match perfectly.

---------------------------------------------------------------------------
⛔ WHAT C10 DOES **NOT** LOOK AT — or someone will trust it too much
---------------------------------------------------------------------------

  · ⛔ **whether `rcp.c` is RIGHT.**  C10 says the two copies agree,
    not that they are right.  Two identical copies of the same defect pass;
  · ⛔ **the binary.**  C10 runs BEFORE compiling: it does not know whether the `remotix` that
    is running somewhere was built from these files.  ⇒ That is
    target **C11** (`md5` of the binary, the same in all the boxes);
  · **the working copies outside the repository**: `src/rcp-gemello`, `/srv/src/rcp`
    on the test machine, and the copy grafted inside ngtcp2's `examples/`.
    They are **destinations**, not twins of the repository: `src/costruisci.sh` chooses
    which to use, and this mesh only looks at the pair that is in git;
  · **the other «twins» of the project that are not code**: the twin table
    of `SPECIFICHE.md` §8.1, and the **deployed** copies that `11-accendi.sh` puts
    inside the boxes (`prodotto/pagina.html`, `prodotto/remotix`).  ⚠ Those
    are destinations of a copy, not a module mounted on two hosts — and who
    looks at them is **C11**, with the binary's `md5`;
  · **the files of `banchi/rcp/` that have no sibling in `src/`.**  Today there are
    none; if there were, C10 **names** them and ⛔ does not judge them: a file
    that lives in one place only has nobody to match, and calling it
    red would be a red that cannot be turned green (§1.49).

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ the twin copies match, and the list covers the whole folder
  1  ⛔ RED: at least one pair diverges, **or** a de facto twin is not
     declared in `GEMELLATI` (that is nobody is looking at it)
  3  ⛔ I could not look: `GEMELLATI` unreadable or empty, the twin folder
     is not there, a declared file is missing on one side
     — ⛔ **and it is not a red**
  2  the terrain does not hold, or the usage is wrong — ⭐ and this also covers **«this
     machine is not the repository»** (the test machine: no git, no
     `src/Makefile`).  ⛔ It is not a 3: a 3 says «I should have looked and did not
     manage to», and here there is nothing to look at by construction.
     ⇒ It is the same thing C12, C15 and C16 say in the same place.
===========================================================================
"""
import argparse
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tempfile

# ⛔ THE TWO PATHS, declared here and printed in every outcome: «they match» is
#    a verdict, and a verdict without its yardstick is an opinion.
CASA = "src"
GEMELLA = "banchi/rcp"
MAKEFILE = "src/Makefile"

# ⚠ Which files of the twin folder are CODE, that is which can be
#   a twin.  ⛔ The list is declared instead of deduced: a `README.md`
#   put one day in `banchi/rcp/` must not become a perpetual red.
SUFFISSI_SORGENTE = (".c", ".h")


# ---------------------------------------------------------------------------
def senza_commento(riga):
    """⛔⛔ In a Makefile a `#` opens a comment up to the end of the line.

    ⚠ A real defect of this mesh, found on 27 Aug 2026 by an agent
      sent to refute it.  Without this line:

        GEMELLATI := rcp.c rcp.h autenticazione.c  # i tre di sempre
        ⇒ list: ['rcp.c','rcp.h','autenticazione.c','#','i','tre','di','sempre']
        ⇒ outcome 3, ⛔ **and for ever** — which is §1.49 with an air of caution,
          and the mesh itself says further down that *«a repeated 3 is not an
          outcome: it is a fault of the bench»*.

    ⛔⛔ And there is a second direction, worse: if the comment NAMES a file
        (`# e un giorno ban.c`), that name entered the list **as
        declared** ⇒ the guard *«it is a twin nobody is looking at»*
        no longer fired.  ⇒ C10's most precious red — the one that
        nobody else here gave — went out with one character.
    """
    return riga.split("#", 1)[0]


def elenco_dichiarato(percorso_makefile):
    """⭐ Reads `GEMELLATI` from `src/Makefile`.

    ⛔ Returns `None` if it did not find it, and ⛔ **does not fall back on a pinned
       list**: «I did not read the list» and «the list is the usual one»
       are two different facts, and the second with the air of the first is a
       check switched off that looks switched on (`src/Makefile`, R12.3).
    ⚠ And `None` is not the empty list: the empty list means «the Makefile
      declares zero twins», which is yet another fact — and it would pass the
      comparison without having looked at anything (`LEZIONI.md` §1.47).
    """
    try:
        with open(percorso_makefile, "r", encoding="utf-8", errors="replace") as f:
            testo = f.read()
    except OSError:
        return None
    # ⚠ The ASSIGNMENTS are taken, not any line that names the
    #   variable: `$(GEMELLATI)` also appears in the body of the rule.
    #
    # ⛔ And ALL of them are taken, `+=` included.  ⚠ The first draft of this
    #    mesh stopped at the first one: the day someone had
    #    added a fourth twin with `GEMELLATI += ban.c`, C10 would not have
    #    seen it in the list and would have accused it of **not being
    #    declared** ⇒ a false red on a correct declaration, that is
    #    the error shape of `LEZIONI.md` §1.49.
    #
    # ⛔ And the lines are STITCHED BACK if they end with a backslash: a
    #    list split over two lines is perfectly normal in a Makefile, and
    #    reading only its first half would have the same effect as above.
    #
    # ⛔⛔ AND THE TRAILING COMMENT IS CUT — a real defect, found on 27 Aug
    #    2026 (see `senza_commento`).  ⚠ The certification had the case of the
    #    WHOLE-line comment and not the TRAILING one, which is the most
    #    normal thing in the world inside a Makefile.
    righe = []
    continua = False
    for riga in testo.splitlines():
        if continua:
            righe[-1] += " " + senza_commento(riga).rstrip()
        elif re.match(r"^GEMELLATI\s*[:?+]?=", riga):
            righe.append(senza_commento(riga).rstrip())
        else:
            continua = False
            continue
        continua = righe[-1].endswith("\\")
        if continua:
            righe[-1] = righe[-1][:-1]
    if not righe:
        return None
    nomi = []
    for riga in righe:
        for n in riga.split("=", 1)[1].split():
            if n not in nomi:
                nomi.append(n)
    return nomi


def leggi(percorso):
    try:
        with open(percorso, "rb") as f:
            return f.read()
    except OSError:
        return None


def impronta(percorso):
    """⚠ The fingerprint serves to PRINT, not to judge: the comparison is made
       on the bytes (see `guarda`).  ⛔ «byte for byte» must be true
       literally, not «equal up to a fingerprint»."""
    dati = leggi(percorso)
    return None if dati is None else hashlib.md5(dati).hexdigest()


# ---------------------------------------------------------------------------
def guarda(radice):
    """Gathers the FACTS.  ⛔ It does not judge: judging is another job, and
       keeping them separate is what allows certifying the judge on
       synthetic cases without touching the real files."""
    f = {
        "radice": radice,
        "makefile": os.path.join(radice, MAKEFILE),
        "casa": os.path.join(radice, CASA),
        "gemella": os.path.join(radice, GEMELLA),
    }
    f["elenco"] = elenco_dichiarato(f["makefile"])
    f["gemella_c_e"] = os.path.isdir(f["gemella"])
    f["casa_c_e"] = os.path.isdir(f["casa"])

    # ⭐ The declared pairs, one by one.
    f["coppie"] = []
    for nome in (f["elenco"] or []):
        a = os.path.join(f["casa"], nome)
        b = os.path.join(f["gemella"], nome)
        ci_a, ci_b = os.path.isfile(a), os.path.isfile(b)
        if not ci_a and not ci_b:
            stato = "mancano-tutt-e-due"
        elif not ci_a:
            stato = "manca-in-src"
        elif not ci_b:
            stato = "manca-nel-gemello"
        else:
            # ⛔ Byte for byte, and literally: the BYTES are compared, not the
            #    lines and not even the fingerprints.  A file that differs only by
            #    a line ending is a different file, and the compiler knows it even
            #    if `diff` in certain modes does not show it.
            da, db = leggi(a), leggi(b)
            stato = "identici" if (da is not None and da == db) else "divergono"
        f["coppie"].append({"nome": nome, "stato": stato,
                            "md5": impronta(a) or impronta(b)})

    # ⭐⭐ AND NOW THE PART NOBODY DID: does the list cover the folder?
    f["non_dichiarati"] = []   # it is in both folders, but not in GEMELLATI
    f["solo_nel_banco"] = []   # it is only in `banchi/rcp/`: it has no twin
    f["estranei"] = []         # it is not a source: it is named and not judged
    if f["gemella_c_e"]:
        for nome in sorted(os.listdir(f["gemella"])):
            if not os.path.isfile(os.path.join(f["gemella"], nome)):
                continue
            if not nome.endswith(SUFFISSI_SORGENTE):
                f["estranei"].append(nome)
                continue
            if f["elenco"] is not None and nome in f["elenco"]:
                continue
            if os.path.isfile(os.path.join(f["casa"], nome)):
                f["non_dichiarati"].append(nome)
            else:
                f["solo_nel_banco"].append(nome)
    return f


# ---------------------------------------------------------------------------
def giudica(f):
    """From the facts to the verdict.  Returns `(esito, motivi)`.

    ⛔ The order is not a detail: a RED found is a judgement already given,
       and it is not watered down into «I could not look» because ANOTHER file
       was missing.  ⇒ first the red, then the 3, then the green.
    """
    motivi = []

    # ── 3 · there is nothing to compare, and it must be said ───────────────
    if f["elenco"] is None:
        return 3, ["⛔ I did not read `GEMELLATI` from %s: I do not know what should "
                   "match" % MAKEFILE]
    if not f["elenco"]:
        return 3, ["⛔ `GEMELLATI` is EMPTY: zero pairs to compare — and "
                   "«zero differences on zero pairs» would be a green that has not "
                   "looked at anything (LEZIONI.md §1.47)"]
    if not f["gemella_c_e"]:
        return 3, ["⛔ the twin folder «%s» IS NOT THERE: it is not «the copies "
                   "match», it is «I could not look»" % GEMELLA]
    if not f["casa_c_e"]:
        return 3, ["⛔ the folder «%s» IS NOT THERE" % CASA]

    # ── 1 · the reds ───────────────────────────────────────────────────────
    divergono = [c["nome"] for c in f["coppie"] if c["stato"] == "divergono"]
    for nome in divergono:
        motivi.append("⛔ %s DIVERGES between %s/ and %s/" % (nome, CASA, GEMELLA))
    for nome in f["non_dichiarati"]:
        motivi.append("⛔ «%s» is in both folders but is NOT in "
                      "`GEMELLATI`: it is a twin nobody is looking at"
                      % nome)
    if divergono or f["non_dichiarati"]:
        return 1, motivi

    # ── 3 · I looked, and a piece could not speak ──────────────────────────
    mancanti = [c for c in f["coppie"] if c["stato"] != "identici"]
    if mancanti:
        for c in mancanti:
            motivi.append("⛔ %s: %s" % (c["nome"], c["stato"].replace("-", " ")))
        motivi.append("⇒ «I found no differences» and «I could not look» "
                      "have the same face: this is the second")
        return 3, motivi

    # ── 0 ──────────────────────────────────────────────────────────────────
    return 0, ["⭐ the %d declared pairs match byte for byte, and "
               "the list covers the whole twin folder" % len(f["coppie"])]


# ---------------------------------------------------------------------------
# ⭐ THE CERTIFICATION — §3.6: «every test has its injected fault, and that
#    case must be run, not imagined».
#
# ⛔ And it is done on SYNTHETIC copies in a temporary folder: the real files of the
#    repository are not touched even for an instant.  ⚠ A bench that injects a
#    fault into the real files is a bench that, if it dies half-way, leaves the repository
#    broken — and the fault looks like the product's.
# ---------------------------------------------------------------------------
MAKEFILE_FINTO = (
    "# Synthetic Makefile of the C10 certification\n"
    "SORGENTI := main.c rcp.c\n"
    "GEMELLATI := rcp.c rcp.h autenticazione.c\n"
    "tutto: impronte\n"
    "\t@echo $(GEMELLATI)\n"
)


def scena(dove, elenco_makefile=MAKEFILE_FINTO, contenuti=None, gemello=None):
    """Builds a fake repository: `src/`, `banchi/rcp/`, `src/Makefile`."""
    contenuti = contenuti or {"rcp.c": b"protocollo\n",
                              "rcp.h": b"intestazioni\n",
                              "autenticazione.c": b"pam\n"}
    gemello = contenuti if gemello is None else gemello
    os.makedirs(os.path.join(dove, CASA), exist_ok=True)
    if gemello is not False:
        os.makedirs(os.path.join(dove, GEMELLA), exist_ok=True)
    if elenco_makefile is not None:
        with open(os.path.join(dove, MAKEFILE), "wb") as f:
            f.write(elenco_makefile.encode("utf-8"))
    for nome, dati in contenuti.items():
        with open(os.path.join(dove, CASA, nome), "wb") as f:
            f.write(dati)
    if gemello is not False:
        for nome, dati in gemello.items():
            with open(os.path.join(dove, GEMELLA, nome), "wb") as f:
                f.write(dati)
    return dove


def certifica():
    sano = {"rcp.c": b"protocollo\n", "rcp.h": b"intestazioni\n",
            "autenticazione.c": b"pam\n"}
    # ⛔ One BYTE, not one line: if the judge only took the big
    #    differences, the tuning of `BAN_DURATA` from 12 to 1 would escape it.
    un_byte = dict(sano, **{"rcp.c": b"protocollo\r\n"})
    senza_uno = {k: v for k, v in sano.items() if k != "rcp.h"}
    quarto_uguale = dict(sano, **{"ban.c": b"ban\n"})
    quarto_diverso_src = dict(sano, **{"ban.c": b"ban DODICI ore\n"})
    quarto_diverso_gem = dict(sano, **{"ban.c": b"ban UNA ora\n"})

    casi = [
        # (name, how the scene is built, expected outcome)
        ("the three copies are identical ⇒ GREEN",
         dict(contenuti=sano), 0),

        ("⛔ ONE BYTE changed in a copy ⇒ RED",
         dict(contenuti=sano, gemello=un_byte), 1),

        ("⛔ and the counter-proof of §1.49: byte removed, back to GREEN",
         dict(contenuti=sano, gemello=sano), 0),

        ("⛔ a twin copy is MISSING ⇒ 3, I could not look",
         dict(contenuti=sano, gemello=senza_uno), 3),

        ("⛔ the twin folder is not there at all ⇒ 3",
         dict(contenuti=sano, gemello=False), 3),

        ("⛔ `GEMELLATI` unreadable (no Makefile) ⇒ 3",
         dict(contenuti=sano, elenco_makefile=None), 3),

        ("⛔ `GEMELLATI` EMPTY ⇒ 3 — zero pairs is not a green",
         dict(contenuti=sano,
              elenco_makefile="GEMELLATI :=\n"), 3),

        ("⭐⭐ a FOURTH undeclared twin, and IDENTICAL ⇒ RED all the same",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale), 1),

        ("⭐⭐ …and indeed here it is DIFFERENT: it was red because nobody watched it",
         dict(contenuti=quarto_diverso_src, gemello=quarto_diverso_gem), 1),

        ("⚠ a file only in the bench (no sibling in src/) is NOT a red",
         dict(contenuti=sano,
              gemello=dict(sano, **{"innesto-solo-banco.c": b"x\n"})), 0),

        ("⚠ a non-source file in banchi/rcp/ is NOT a red",
         dict(contenuti=sano,
              gemello=dict(sano, **{"APPUNTI.md": b"note\n"})), 0),

        # ⛔ THE TWO CASES THAT CATCH A DEFECT OF THIS MESH ITSELF, not of the
        #    product: a fourth twin DECLARED in a way the first
        #    draft could not read ⇒ it would have accused it of not being
        #    declared.  ⭐ A false red on a correct declaration is
        #    exactly §1.49, and here it is injected and tested.
        ("⛔ declared with `GEMELLATI += ban.c` ⇒ GREEN, not a false red",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale,
              elenco_makefile="GEMELLATI := rcp.c rcp.h autenticazione.c\n"
                              "GEMELLATI += ban.c\n"), 0),

        ("⛔ declared on TWO lines with the backslash ⇒ GREEN",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale,
              elenco_makefile="GEMELLATI := rcp.c rcp.h \\\n"
                              "             autenticazione.c ban.c\n"), 0),

        ("⛔ …and with the backslash the fourth DIVERGES ⇒ RED all the same",
         dict(contenuti=quarto_diverso_src, gemello=quarto_diverso_gem,
              elenco_makefile="GEMELLATI := rcp.c rcp.h \\\n"
                              "             autenticazione.c ban.c\n"), 1),

        ("⚠ a COMMENT line that names GEMELLATI is not a declaration",
         dict(contenuti=sano,
              elenco_makefile="# GEMELLATI := tutto quel che vuoi\n"
                              "GEMELLATI := rcp.c rcp.h autenticazione.c\n"), 0),

        # ═══════════════════════════════════════════════════════════════════
        # ⛔⛔ THE CASES THAT WERE NOT THERE TODAY — 27 Aug 2026.  ⚠ The case above
        #     has the WHOLE-line comment; ⛔ the TRAILING one is the most
        #     normal thing in the world, and it was not certified.  `[D]` Before the cure
        #     the first of these three gave **3 for ever** and the second
        #     **switched off C10's most precious red**.
        # ═══════════════════════════════════════════════════════════════════
        ("⛔⛔ a TRAILING `#` on the line does not poison the list ⇒ GREEN",
         dict(contenuti=sano,
              elenco_makefile="GEMELLATI := rcp.c rcp.h autenticazione.c"
                              "  # i tre di sempre\n"), 0),

        ("⛔⛔ a comment that NAMES a file does NOT declare it ⇒ RED",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale,
              elenco_makefile="GEMELLATI := rcp.c rcp.h autenticazione.c"
                              "  # e un giorno ban.c\n"), 1),

        ("⛔ and the trailing comment on a line STITCHED with the backslash",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale,
              elenco_makefile="GEMELLATI := rcp.c rcp.h \\\n"
                              "             autenticazione.c ban.c  # i quattro\n"),
         0),
    ]

    print("== certification of the C10 judge ==")
    print("   ⛔ on SYNTHETIC copies in a temporary folder: the real files")
    print("      of the repository are not touched.\n")
    guai = 0
    for nome, come, atteso in casi:
        dove = tempfile.mkdtemp(prefix="c10-cert-")
        try:
            scena(dove, **come)
            esito, motivi = giudica(guarda(dove))
        finally:
            shutil.rmtree(dove, ignore_errors=True)
        bene = esito == atteso
        if not bene:
            guai += 1
        print("  %s %-62s  outcome=%s (expected %s)"
              % ("OK " if bene else "NO ", nome, esito, atteso))
        if not bene:
            for m in motivi:
                print("        %s" % m)

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE SECOND HALF — and the INJECTED FAULT is certified too.
    #
    # ⛔ Before 27 Aug 2026 `--guasto-innestato` ran once only, on the
    #    real repository, and it was not certified in any way: the
    #    certification covered `giudica` and nothing else.  ⇒ The fact that
    #    the injection did not look at the scene BEFORE breaking it could not
    #    come out here.
    # ⚠ Now `innesta_e_giudica` takes any folder, ⇒ it is tested
    #   with the synthetic scenes like everything else.
    # ═══════════════════════════════════════════════════════════════════════
    casi_guasto = [
        ("⭐ GREEN scene ⇒ the byte bites ⇒ 0 (the fault was seen)",
         dict(contenuti=sano), 0),

        # ⛔⛔ THE CASE THAT WOULD HAVE CAUGHT THE DEFECT: the scene is already red —
        #     that is the two `rcp.c` diverge, which is **the defect C10
        #     exists for**.  Before the cure here it came out **0**, ⇒ the hook
        #     wrote `ha_visto_il_guasto: true` on a red of the PRODUCT.
        ("⛔⛔ scene ALREADY red (the copies diverge) ⇒ 3, ⛔ NOT 0",
         dict(contenuti=sano, gemello=un_byte), 3),

        ("⛔⛔ already red because of an undeclared twin ⇒ 3, ⛔ NOT 0",
         dict(contenuti=quarto_uguale, gemello=quarto_uguale), 3),

        ("⛔ a twin copy is missing (outcome 3 already before) ⇒ 3",
         dict(contenuti=sano, gemello=senza_uno), 3),

        ("⛔ `GEMELLATI` unreadable ⇒ 3: there is nothing to inject",
         dict(contenuti=sano, elenco_makefile=None), 3),
    ]
    print()
    print("  ⛔ and the injected fault is judged BEFORE being injected (§1.52):")
    for nome, come, atteso in casi_guasto:
        dove = tempfile.mkdtemp(prefix="c10-cert-guasto-")
        try:
            scena(dove, **come)
            esito, righe = innesta_e_giudica(dove)
        finally:
            shutil.rmtree(dove, ignore_errors=True)
        bene = esito == atteso
        if not bene:
            guai += 1
        print("  %s %-62s  outcome=%s (expected %s)"
              % ("OK " if bene else "NO ", nome, esito, atteso))
        if not bene:
            for r in righe:
                print("        %s" % r)

    quanti = len(casi) + len(casi_guasto)
    print()
    print("  %d cases out of %d" % (quanti - guai, quanti))
    if guai:
        print("⛔ the judge is NOT reliable: %d wrong cases" % guai)
        return 1
    print("⭐ the judge can say GREEN, can say RED, and can say «I do not know» —")
    print("   ⛔ and it can give red even to a twin nobody had declared,")
    print("   which is the only thing nobody did here (LEZIONI.md §1.47).")
    print("⛔ And the injected fault is not certified on a scene that is already red.")
    return 0


# ---------------------------------------------------------------------------
def git_dice_la_radice(qui):
    """⭐ The root according to git, or None if git cannot answer."""
    try:
        p = subprocess.run(["git", "-C", qui, "rev-parse", "--show-toplevel"],
                           capture_output=True, text=True, timeout=30)
        if p.returncode == 0 and p.stdout.strip():
            return p.stdout.strip()
    # ⛔ `subprocess.TimeoutExpired` does NOT descend from `OSError`: without naming it,
    #    a `git` that hangs produced a traceback ⇒ Python exited **1** ⇒ the
    #    hook read RED on a fault of the bench (`LEZIONI.md` §1.51).
    except (OSError, subprocess.SubprocessError):
        pass
    return None


def radice_del_deposito(qui):
    """⚠ Git is asked, and if git is not there we go up two folders — this
       file lives in `banchi/11-scatole/`.  ⛔ It is not a silent fallback: the
       chosen path is PRINTED, and if the folders are not there the outcome is 3."""
    return git_dice_la_radice(qui) or os.path.abspath(
        os.path.join(qui, "..", ".."))


# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE TERRAIN — «is this machine the repository?», and it is asked FIRST.
#
# ⛔ 23 Sep 2026, and the whole net brought it out: on the test machine
#    C10 exited **3, «I could not look»** — the mesh appeared among
#    those that DID NOT LOOK, next to a real fault, and whoever read
#    had to guess that there was nothing to look at there by construction.
#    `[M]` The repository on that machine is not there at all: no `src/`,
#    no `banchi/rcp/`, and the guessed root came out as `/media`.
#
# ⭐ The three sisters that live the same life — C12, C15, C16 — have always said it
#   the right way: *«I am not inside a git repository ⇒ the terrain does not
#   hold»*, and they exit **2**.  ⇒ C10 was the only one left behind, and now
#   it says the same thing in the same way (`DECISIONI.md` §4.6-novemdecies:
#   deciding needs the repository, running needs the boxes).
#
# ⛔⛔ AND THE DISTINCTION THAT MUST NOT BE LOST: the **2** is given ONLY when git cannot
#     say where the repository is **and** in the guessed place there is no
#     `Makefile`.  If git answers — that is on the laptop — an unreadable `GEMELLATI`
#     stays a **3**: there it is a real fault, and it is what the 3
#     serves to shout.  ⇒ This silences no defect: it only moves
#     the case in which there is, by construction, nothing to look at.
# ═══════════════════════════════════════════════════════════════════════════
def qui_c_e_il_deposito(qui, radice):
    """⭐ (it is there, why) — and the «why» is what gets printed."""
    if git_dice_la_radice(qui):
        return True, ""
    if os.path.isfile(os.path.join(radice, MAKEFILE)):
        # ⚠ A repository without `.git` (a copy, an unpacked archive) is
        #   a repository all the same: what counts is that there is something to look at.
        return True, ""
    return False, ("I am not inside a git repository, and in «%s» there is "
                   "not even %s" % (radice, MAKEFILE))


# ---------------------------------------------------------------------------
# ⭐⭐ THE INJECTED FAULT, and it runs in the HOOK — not only in the certification
#
# ⛔ The certification proves the judge can say red; ⭐ this proves
#    that **the net in service** can still say it, and it is another question (C13).
#
# ⚠ The half of the hook that lives on the laptop runs C10, C12 and C13 — and
#   ⛔ none of the three injects a fault.  ⇒ Without this mode, C13 on
#   that half COULD NEVER turn green: it would say for ever «no
#   fault was ever injected», which from outside looks like a broken net.
#
# ⭐ And it is injected into the REAL files, copied to a temporary folder: it is the case
#   that counts (the synthetic ones are already done by `--certifica`), and ⛔ the repository files
#   are not touched even for an instant.
#
# ⛔ The hook's convention reads THE OTHER WAY ROUND: here `0` means «the
#    fault WAS SEEN».  ⇒ `esegui_maglia … true …` writes in the log
#    `ha_visto_il_guasto`, and C13 reads that.
#
# ⛔⛔ AND THE SCENE IS JUDGED **BEFORE** BREAKING IT — §1.52, cure of 27 Aug
#     2026.  ⚠ Until that day there was no `giudica` here before
#     the injection: if `src/rcp.c` and `banchi/rcp/rcp.c` already diverged —
#     ⛔ that is **exactly the defect C10 exists for** — the temporary
#     copy would be born already red, the changed byte would add
#     nothing, and C10 would exit **0** ⇒ the hook would write
#     `ha_visto_il_guasto: true`.
# ⇒ ⭐ The day it bites is **precisely the day of the red**: the run
#   in which C10 finally catches the defect is also the run in which its
#   injected fault would stop meaning anything.  ⛔ The net would
#   certify itself on a defect of the product.
# ---------------------------------------------------------------------------
def innesta_e_giudica(dove):
    """⭐ The injected fault, and ⛔ **it runs on any scene**.

    ⚠ It is written this way on purpose: by taking the folder as an argument, this
      piece can be certified on synthetic scenes instead of being tested
      once only on the real repository.  ⇒ It is how `--certifica` tests the
      judge: by calling it.

    Returns `(esito, righe)`.  ⛔ It reads THE OTHER WAY ROUND: `0` = the fault was
    seen.  `3` = I could not inject anything.
    """
    righe = []
    f = guarda(dove)
    if f["elenco"] is None or not f["elenco"]:
        return 3, ["⛔ I did not read `GEMELLATI`: I cannot even inject "
                   "the fault ⇒ I could not look"]

    # ⛔⛔ FIRST THE JUDGEMENT, THEN THE FAULT (§1.52).
    prima, motivi_prima = giudica(f)
    if prima != 0:
        righe.append("⛔⛔ the scene was ALREADY red BEFORE the fault (outcome %d):"
                     % prima)
        righe += ["   " + m for m in motivi_prima]
        righe.append("⇒ a fault injected into a scene already red "
                     "proves nothing: the red would have been there anyway.")
        righe.append("⛔ And this is NOT «the fault was not seen»: it is")
        righe.append("  «I could not inject anything» ⇒ outcome 3 (§1.52).")
        return 3, righe
    righe.append("⭐ the scene was GREEN before the fault: the injection has something "
                 "to bite")

    # ⛔ ONE BYTE, not one line: if the judge only took the big
    #    differences, a shifted constant would escape it.
    bersaglio = os.path.join(dove, GEMELLA, f["elenco"][0])
    if not os.path.isfile(bersaglio):
        righe.append("⛔ the twin copy of «%s» is not there: I have no target "
                     "to break ⇒ I could not look" % f["elenco"][0])
        return 3, righe
    dati = bytearray(leggi(bersaglio) or b"")
    if not dati:
        righe.append("⛔ the twin copy is empty: I have no target")
        return 3, righe
    meta = len(dati) // 2
    dati[meta] = (dati[meta] + 1) % 256
    with open(bersaglio, "wb") as h:
        h.write(bytes(dati))
    righe.append("fault: one byte changed in %s/%s (position %d of %d)"
                 % (GEMELLA, f["elenco"][0], meta, len(dati)))

    dopo, motivi = giudica(guarda(dove))
    righe += ["   " + m for m in motivi]
    if dopo == 1:
        righe.append("⭐ THE FAULT WAS SEEN — C10 can still give red,")
        righe.append("  ⭐ and the red comes FROM THE FAULT: before it was green (§1.52).")
        return 0, righe
    righe.append("⛔⛔ THE FAULT WAS **NOT** SEEN (the mesh said %d)."
                 % dopo)
    righe.append("⇒ C10 is no longer able to give red, and a mesh like that")
    righe.append("  looks the same as one that finds nothing.")
    return 1, righe


def guasto_innestato(radice):
    import shutil
    import tempfile

    print("== C10 — THE INJECTED FAULT (§3.6) ==")
    print("   ⛔ it reads THE OTHER WAY ROUND: 0 = the red was SEEN\n")

    vero = guarda(radice)
    if vero["elenco"] is None or not vero["elenco"]:
        print("⛔ I did not read `GEMELLATI` from the real repository: I cannot")
        print("   even inject the fault ⇒ I could not look")
        return 3

    dove = tempfile.mkdtemp(prefix="c10-guasto-")
    try:
        os.makedirs(os.path.join(dove, CASA))
        os.makedirs(os.path.join(dove, GEMELLA))
        shutil.copy2(os.path.join(radice, MAKEFILE), os.path.join(dove, MAKEFILE))
        # ⛔ The WHOLE twin folder is copied, not only the declared ones: the
        #    third question of C10 is «does the list cover the folder?», and copying
        #    only the declared ones the scene would be green by construction ⇒ the
        #    «before» judgement would have nothing to judge.
        for nome in sorted(os.listdir(os.path.join(radice, GEMELLA))):
            for cartella in (CASA, GEMELLA):
                a = os.path.join(radice, cartella, nome)
                if os.path.isfile(a):
                    shutil.copy2(a, os.path.join(dove, cartella, nome))
        for nome in vero["elenco"]:
            for cartella in (CASA, GEMELLA):
                a = os.path.join(radice, cartella, nome)
                if os.path.isfile(a) and not os.path.isfile(
                        os.path.join(dove, cartella, nome)):
                    shutil.copy2(a, os.path.join(dove, cartella, nome))

        esito, righe = innesta_e_giudica(dove)
        for r in righe:
            print("   %s" % r)
        return esito
    finally:
        shutil.rmtree(dove, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(
        description="C10 — the two twin copies of the protocol match")
    p.add_argument("--radice", default=None,
                   help="the root of the repository (default: the one of this file)")
    p.add_argument("--certifica", action="store_true",
                   help="proves that the judge can give green, red and «I do not know»")
    p.add_argument("--guasto-innestato", action="store_true",
                   help="⛔ injects a fault into the REAL copied files and demands "
                        "red — the outcome reads the other way round (0 = seen)")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    qui = os.path.dirname(os.path.abspath(__file__))
    radice = a.radice or radice_del_deposito(qui)

    # ⭐⭐ THE TERRAIN FIRST OF ALL — and ⛔ `--radice` overrides it on purpose: whoever
    #    passes it is saying where to look, and if they are wrong they must see a 3.
    if not a.radice:
        c_e, perche = qui_c_e_il_deposito(qui, radice)
        if not c_e:
            print("⛔ %s." % perche)
            print("   ⇒ if this is the test machine, the two twin copies")
            print("     are NOT HERE: there is nothing to compare, and")
            print("     it is not «I could not look» — it is «this question")
            print("     is not asked here».")
            print("   ⭐ The repository lives on the laptop, and that is where it must run")
            print("     (DECISIONI.md §4.6-novemdecies).")
            print("   ⇒ the terrain does not hold")
            return 2

    if a.guasto_innestato:
        return guasto_innestato(radice)

    print("== C10 — do the two twin copies of the protocol match? ==")
    print("   repository: %s" % radice)
    print("   the two   : %s/  and  %s/" % (CASA, GEMELLA))
    print("   the list  : `GEMELLATI` READ from %s — ⛔ not copied here" % MAKEFILE)
    print("   yardstick : ⛔ **the whole file, byte for byte** — and it is not an")
    print("              excess: the two copies are the same module mounted on")
    print("              two hosts, not two variants (src/Makefile, R12.3)\n")

    f = guarda(radice)

    if f["elenco"] is None:
        print("   ⛔ `GEMELLATI` not read.")
    else:
        print("   declared pairs: %d  ⇒  %s"
              % (len(f["elenco"]), " ".join(f["elenco"]) or "(none)"))
    print()

    # ⭐ The table is ALWAYS printed, green or red: it is what must be looked at, and
    #   whoever reads must be able to see it without relaunching anything.
    if f["coppie"]:
        largh = max(len(c["nome"]) for c in f["coppie"])
        for c in f["coppie"]:
            segno = {"identici": "  ", "divergono": "⛔"}.get(c["stato"], "⚠ ")
            print(" %s %-*s  %-18s  md5 %s"
                  % (segno, largh, c["nome"], c["stato"],
                     (c["md5"] or "?")[:12]))
        print()

    # ⛔⛔ AND HERE THE PART NOBODY DID: does the list cover the folder?
    if f["gemella_c_e"]:
        print("   ⭐ and does the list cover the whole twin folder?")
        if f["non_dichiarati"]:
            for n in f["non_dichiarati"]:
                print("     ⛔ %s — it is in both, and it is NOT declared" % n)
        else:
            print("     OK  no source of %s/ was left out of `GEMELLATI`"
                  % GEMELLA)
        for n in f["solo_nel_banco"]:
            print("     ⚠  %s — it is ONLY in the bench: it has no twin, I do not "
                  "judge it" % n)
        for n in f["estranei"]:
            print("     ⚠  %s — it is not a source (%s): I do not judge it"
                  % (n, "/".join(SUFFISSI_SORGENTE)))
        print()

    esito, motivi = giudica(f)
    for m in motivi:
        print("   %s" % m)
    print()

    if esito == 0:
        print("⭐ GREEN — and it is worth saying what it does NOT mean: that `rcp.c`")
        print("   is right.  ⛔ Two identical copies of the same defect pass")
        print("   through here without making noise.")
    elif esito == 1:
        print("⛔⛔ RED — §5.2: it is repaired BEFORE going on.")
        print("   ⇒ As long as it is like this, the product's protocol and the")
        print("     benches' are TWO, and every bench that says green on the graft")
        print("     is saying nothing about the product.")
    elif esito == 3:
        print("⛔ I COULD NOT LOOK (outcome 3) — ⛔ and it is not a red (§4.5).")
        print("   ⚠ And a repeated 3 is not an outcome: it is a fault of the bench.")
    return esito


if __name__ == "__main__":
    sys.exit(main())
