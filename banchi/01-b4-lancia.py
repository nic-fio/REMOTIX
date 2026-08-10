#!/usr/bin/env python3
"""01-b4-lancia.py — B4: il validatore contro le sette registrazioni.

    python3 01-b4-lancia.py [cartella]

⛔ Confronta l'ATTESO con il MISURATO **il banco, non chi guarda** (regola
   B0.4).  E l'atteso non e' «rosso»: e' **quale byte** e **quale regola**.

⭐ Le due cose che questo banco esiste per distinguere:

  1. un validatore che **boccia tutto** — lo prende la registrazione conforme,
     che DEVE essere accettata;
  2. un validatore che da' **rosso sul byte sbagliato** — lo prende il
     confronto degli scostamenti, e in particolare la registrazione col
     riempimento, dove un validatore che non conosce §6.0 legge di traverso il
     messaggio successivo e accusa quello.
"""
import json
import os
import re
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
VALIDATORE = os.path.join(QUI, "01-b4-validatore.py")


def main():
    dove = sys.argv[1] if len(sys.argv) > 1 else os.path.join(QUI, "b4-registrazioni")
    with open(os.path.join(dove, "manifesto.json")) as f:
        manifesto = json.load(f)

    print(f"== B4 — il validatore del filo contro {len(manifesto)} registrazioni\n")
    buoni = 0
    for voce in manifesto:
        percorso = os.path.join(dove, voce["file"])
        p = subprocess.run([sys.executable, VALIDATORE, percorso],
                           capture_output=True, text=True)
        uscita, testo = p.returncode, p.stdout + p.stderr

        atteso_conforme = voce["atteso"] == "conforme"
        ok = True
        note = []

        if atteso_conforme:
            if uscita != 0:
                ok = False
                note.append(f"atteso CONFORME, uscita {uscita}")
        else:
            if uscita != 1:
                ok = False
                note.append(f"attesa uscita 1 (non conforme), avuta {uscita}")
            # ⛔ Il byte, non solo il colore.
            m = re.search(r"byte (\d+) nel file", testo)
            visto = int(m.group(1)) if m else None
            if visto != voce["byte"]:
                ok = False
                note.append(f"atteso il byte {voce['byte']}, accusato {visto}")
            if voce["regola"] not in testo:
                ok = False
                note.append(f"attesa la regola {voce['regola']}")

        segno = "OK " if ok else "NO "
        print(f"   {segno} {voce['file']:<26s} {voce['che']}")
        if not ok:
            for n in note:
                print(f"       ⛔ {n}")
            for riga in testo.strip().splitlines()[-6:]:
                print(f"       | {riga}")
        else:
            buoni += 1

    print(f"\n== Esito")
    print(f"   {buoni} su {len(manifesto)}")
    # ⛔ Il denominatore del verdetto: se le registrazioni fossero zero, «tutte
    #    passano» sarebbe vero e vuoto (LEZIONI.md §1.9, punto 6).
    if not manifesto:
        print("   ⛔ nessuna registrazione: non c'e' niente da approvare")
        return 2
    if buoni == len(manifesto):
        print("   ⭐ il validatore vede i sei guasti, ciascuno sul byte giusto,")
        print("      e accetta la settima.  E' certificato.")
        return 0
    print("   ⛔ il validatore NON e' certificato: vedi sopra")
    return 1


if __name__ == "__main__":
    sys.exit(main())
