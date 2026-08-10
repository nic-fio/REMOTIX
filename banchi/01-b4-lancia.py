#!/usr/bin/env python3
"""01-b4-lancia.py — B4: il validatore contro le registrazioni, RIGENERATE ADESSO.

    python3 01-b4-lancia.py [cartella]

⛔ Confronta l'ATTESO con il MISURATO **il banco, non chi guarda** (regola
   B0.4).  E l'atteso non e' «rosso»: e' **quale uscita**, **quale byte** e
   **quale regola**.

---------------------------------------------------------------------------
⛔ LE REGISTRAZIONI SI RIGENERANO, NON SI TROVANO

*10 agosto 2026, rilievo R7.13.*  Questo programma leggeva `manifesto.json` e i
`.rcpreg` da una cartella **senza mai rigenerarli**: non eseguiva
`01-b4-registrazioni.py`, non ne confrontava l'impronta, non guardava le date.
Certificava il validatore contro i file che trovava.

⚠ Il difetto non era che fossero vecchi — oggi coincidono — e' che **niente lo
  impediva**: si cambiava lo scostamento atteso di un caso e il banco stampava
  «e' certificato», perche' leggeva il manifesto del giro precedente.  L'ATTESO
  che `01-b4-registrazioni.py` chiama *«scritto qui e non nella testa di chi
  guarda»* era scritto in un file che nessuno legava al programma che lo aveva
  prodotto.

⭐ Adesso il primo passo di questo banco e' **eseguire il programma che le
   costruisce**, nella cartella che poi legge.

---------------------------------------------------------------------------
⭐ LE QUATTRO COSE CHE QUESTO BANCO ESISTE PER DISTINGUERE

  1. un validatore che **boccia tutto** — lo prende la registrazione conforme,
     che DEVE essere accettata;
  2. un validatore che da' **rosso sul byte sbagliato** — lo prende il
     confronto degli scostamenti, e in particolare la registrazione col
     riempimento, dove un validatore che non conosce §6.0 legge di traverso il
     messaggio successivo e accusa quello;
  3. ⛔ un validatore che confonde **«il file e' rotto»** con **«il filo non e'
     conforme»** — lo prendono le registrazioni ad uscita 2, che prima non
     esistevano: l'esito che il validatore dichiara essere la ragione per cui
     gli esiti non sono due **non era mai stato osservato** (R7.13);
  4. ⛔ un validatore che dichiara conforme una registrazione in cui **non ha
     giudicato niente** — lo prende quella ad uscita 3.

⛔ **E la copertura si stampa per esito, con il denominatore.**  «13 su 13» non
   dice quali dei quattro esiti sono stati esercitati, e un esito senza
   nemmeno una registrazione e' un ramo di codice che nessuno ha mai fatto
   girare.
"""
import json
import os
import re
import subprocess
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
VALIDATORE = os.path.join(QUI, "01-b4-validatore.py")
COSTRUTTORE = os.path.join(QUI, "01-b4-registrazioni.py")

ESITI = {0: "conforme", 1: "non-conforme", 2: "registrazione-rotta",
         3: "niente-da-giudicare"}


def rigenera(dove):
    """⛔ Il manifesto e i `.rcpreg` li produce ADESSO chi li sa produrre."""
    print(f"== 1. le registrazioni si rigenerano in {dove}/\n")
    p = subprocess.run([sys.executable, COSTRUTTORE, dove],
                       capture_output=True, text=True)
    for riga in (p.stdout + p.stderr).strip().splitlines():
        print(f"   | {riga}")
    print()
    if p.returncode != 0:
        print(f"   ⛔ 01-b4-registrazioni.py e' uscito {p.returncode}: senza le")
        print("      registrazioni non c'e' niente da certificare, e ⛔ NON si")
        print("      ripiega su quelle che eventualmente stanno su disco")
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
        # ⛔ E8 anche qui: «il manifesto non si legge» non e' «zero voci».
        print(f"   ⛔ il manifesto non si legge: {e}")
        return 2

    print(f"== 2. il validatore del filo contro {len(manifesto)} registrazioni\n")
    buoni = 0
    # ⛔ La copertura per esito, calcolata: quante ne PRETENDONO ciascuno, e
    #    quante ne hanno davvero ottenuto quello giusto.
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
            note.append(f"attesa uscita {atteso_uscita} "
                        f"({ESITI[atteso_uscita]}), avuta {uscita} "
                        f"({ESITI.get(uscita, '?')})")
        elif atteso_uscita == 1:
            # ⛔ Il byte e la regola si confrontano SOLO quando l'uscita e'
            #    quella giusta.  Prima si cercava «byte N nel file» anche su
            #    un'uscita 1 arrivata per tutt'altra ragione — per esempio un
            #    `FileNotFoundError` — e il banco riportava «atteso il byte
            #    508, accusato None», cioe' un rosso sul BYTE invece che sul
            #    FILE, che e' proprio la distinzione per cui esiste (R7.5).
            m = re.search(r"byte (\d+) nel file", testo)
            visto = int(m.group(1)) if m else None
            if visto != voce["byte"]:
                ok = False
                note.append(f"atteso il byte {voce['byte']}, accusato {visto}")
            if voce["regola"] not in testo:
                ok = False
                note.append(f"attesa la regola {voce['regola']}")

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

    print(f"\n== 3. Esito")
    print(f"   {buoni} su {len(manifesto)}")
    # ⛔ Il denominatore del verdetto: se le registrazioni fossero zero, «tutte
    #    passano» sarebbe vero e vuoto (LEZIONI.md §1.9, punto 6).
    if not manifesto:
        print("   ⛔ nessuna registrazione: non c'e' niente da approvare")
        return 2

    # ⛔ E il denominatore PER ESITO: un esito senza nemmeno una registrazione
    #    e' un ramo che nessuno ha mai fatto girare, e il validatore lo
    #    dichiara come la ragione per cui gli esiti non sono due.
    print("\n   la copertura dei quattro esiti del validatore:")
    scoperti = 0
    for u in sorted(ESITI):
        buoni_u, tot_u = copertura[u]
        if tot_u == 0:
            scoperti += 1
            print(f"     uscita {u} = {ESITI[u]:<20s} ⛔ NESSUNA registrazione "
                  f"la esercita")
        else:
            print(f"     uscita {u} = {ESITI[u]:<20s} {buoni_u} su {tot_u}")
    if scoperti:
        print(f"   ⛔ {scoperti} esiti su {len(ESITI)} senza controllo positivo:")
        print("      su quei rami «non ho trovato niente» non vuol dire niente")
        return 1

    if buoni == len(manifesto):
        print(f"\n   ⭐ il validatore accusa ciascun guasto sul byte giusto,")
        print(f"      accetta la conforme, e distingue i quattro esiti.")
        print(f"      E' certificato — su {len(manifesto)} registrazioni "
              f"rigenerate adesso.")
        return 0
    print("   ⛔ il validatore NON e' certificato: vedi sopra")
    return 1


if __name__ == "__main__":
    sys.exit(main())
