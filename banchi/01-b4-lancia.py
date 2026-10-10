#!/usr/bin/env python3
"""01-b4-lancia.py — B4: the validator against the recordings, REGENERATED NOW.

    python3 01-b4-lancia.py [folder]

⛔ It is **the bench, not whoever is watching**, that compares the EXPECTED with
   the MEASURED (rule B0.4).  And the expected is not «red»: it is **which exit
   code**, **which byte** and **which rule**.

---------------------------------------------------------------------------
⛔ THE RECORDINGS ARE REGENERATED, NOT FOUND

*10 Aug 2026, finding R7.13.*  This program read `manifesto.json` and the
`.rcpreg` files from a folder **without ever regenerating them**: it did not run
`01-b4-registrazioni.py`, did not compare its fingerprint, did not look at the
dates.  It certified the validator against whatever files it found.

⚠ The defect was not that they were old — today they match — it was that
  **nothing prevented it**: one changed the expected offset of a case and the
  bench printed «it is certified», because it read the manifest of the previous
  run.  The EXPECTED that `01-b4-registrazioni.py` calls *«written here and not
  in the head of whoever is watching»* was written in a file that nobody tied to
  the program that had produced it.

⭐ Now the first step of this bench is **running the program that builds
   them**, in the folder it then reads.

---------------------------------------------------------------------------
⭐ THE FOUR THINGS THIS BENCH EXISTS TO TELL APART

  1. a validator that **rejects everything** — caught by the compliant
     recording, which MUST be accepted;
  2. a validator that gives **red on the wrong byte** — caught by the
     comparison of the offsets, and in particular by the recording with
     padding, where a validator that does not know §6.0 misreads the next
     message and accuses that one;
  3. ⛔ a validator that confuses **«the file is broken»** with **«the wire is
     not compliant»** — caught by the recordings with exit code 2, which did
     not exist before: the outcome that the validator declares to be the reason
     the outcomes are not two **had never been observed** (R7.13);
  4. ⛔ a validator that declares compliant a recording in which **it judged
     nothing** — caught by the one with exit code 3.

⛔ **And the coverage is printed per outcome, with the denominator.**  «13 out
   of 13» does not say which of the four outcomes were exercised, and an
   outcome without even one recording is a code branch that nobody has ever
   run.
"""
import json
import os
import re
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
VALIDATORE = os.path.join(QUI, "01-b4-validatore.py")
COSTRUTTORE = os.path.join(QUI, "01-b4-registrazioni.py")

ESITI = {0: "compliant", 1: "non-compliant", 2: "broken-recording",
         3: "nothing-to-judge"}


def rigenera(dove):
    """⛔ The manifest and the `.rcpreg` files are produced NOW by whoever knows how."""
    print(f"== 1. the recordings are regenerated in {dove}/\n")
    p = subprocess.run([sys.executable, COSTRUTTORE, dove],
                       capture_output=True, text=True)
    for riga in (p.stdout + p.stderr).strip().splitlines():
        print(f"   | {riga}")
    print()
    if p.returncode != 0:
        print(f"   ⛔ 01-b4-registrazioni.py exited {p.returncode}: without the")
        print("      recordings there is nothing to certify, and ⛔ we do NOT")
        print("      fall back on whatever may be lying on disk")
        return False
    return True


def main():
    dove = sys.argv[1] if len(sys.argv) > 1 else os.path.join(QUI, "b4-registrazioni")
    if not rigenera(dove):
        return 2
    try:
        with open(os.path.join(dove, "manifesto.json")) as f:
            manifesto = json.load(f)
    except OSError as e:
        # ⛔ E8 here too: «the manifest cannot be read» is not «zero entries».
        print(f"   ⛔ the manifest cannot be read: {e}")
        return 2

    print(f"== 2. the wire validator against {len(manifesto)} recordings\n")
    buoni = 0
    # ⛔ The coverage per outcome, computed: how many DEMAND each one, and
    #    how many actually got the right one.
    copertura = {u: [0, 0] for u in ESITI}
    for voce in manifesto:
        percorso = os.path.join(dove, voce["file"])
        p = subprocess.run([sys.executable, VALIDATORE, percorso],
                           capture_output=True, text=True)
        uscita, testo = p.returncode, p.stdout + p.stderr

        atteso_uscita = voce["uscita"]
        copertura[atteso_uscita][1] += 1
        ok = True
        note = []

        if uscita != atteso_uscita:
            ok = False
            note.append(f"expected exit {atteso_uscita} "
                        f"({ESITI[atteso_uscita]}), got {uscita} "
                        f"({ESITI.get(uscita, '?')})")
        elif atteso_uscita == 1:
            # ⛔ The byte and the rule are compared ONLY when the exit code is
            #    the right one.  Before, «byte N in the file» was searched even
            #    on an exit 1 that came for an entirely different reason — for
            #    example a `FileNotFoundError` — and the bench reported
            #    «expected byte 508, accused None», that is a red on the BYTE
            #    instead of on the FILE, which is exactly the distinction it
            #    exists for (R7.5).
            m = re.search(r"byte (\d+) in the file", testo)
            visto = int(m.group(1)) if m else None
            if visto != voce["byte"]:
                ok = False
                note.append(f"expected byte {voce['byte']}, accused {visto}")
            if voce["regola"] not in testo:
                ok = False
                note.append(f"expected rule {voce['regola']}")

        segno = "OK " if ok else "NO "
        print(f"   {segno} {voce['file']:<28s} {voce['che']}")
        if not ok:
            for n in note:
                print(f"       ⛔ {n}")
            for riga in testo.strip().splitlines()[-6:]:
                print(f"       | {riga}")
        else:
            buoni += 1
            copertura[atteso_uscita][0] += 1

    print(f"\n== 3. Outcome")
    print(f"   {buoni} out of {len(manifesto)}")
    # ⛔ The denominator of the verdict: if the recordings were zero, «all
    #    pass» would be true and empty (LEZIONI.md §1.9, point 6).
    if not manifesto:
        print("   ⛔ no recordings: there is nothing to approve")
        return 2

    # ⛔ And the denominator PER OUTCOME: an outcome without even one recording
    #    is a branch that nobody has ever run, and the validator declares it
    #    as the reason the outcomes are not two.
    print("\n   the coverage of the validator's four outcomes:")
    scoperti = 0
    for u in sorted(ESITI):
        buoni_u, tot_u = copertura[u]
        if tot_u == 0:
            scoperti += 1
            print(f"     exit {u} = {ESITI[u]:<20s} ⛔ NO recording "
                  f"exercises it")
        else:
            print(f"     exit {u} = {ESITI[u]:<20s} {buoni_u} out of {tot_u}")
    if scoperti:
        print(f"   ⛔ {scoperti} outcomes out of {len(ESITI)} without a positive control:")
        print("      on those branches «I found nothing» means nothing")
        return 1

    if buoni == len(manifesto):
        print(f"\n   ⭐ the validator accuses each fault on the right byte,")
        print(f"      accepts the compliant one, and tells the four outcomes apart.")
        print(f"      It is certified — on {len(manifesto)} recordings "
              f"regenerated now.")
        return 0
    print("   ⛔ the validator is NOT certified: see above")
    return 1


if __name__ == "__main__":
    sys.exit(main())
