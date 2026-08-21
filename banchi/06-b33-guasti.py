#!/usr/bin/env python3
"""06-b33-guasti.py — ⛔⛔ IL CONTROLLO POSITIVO: si innesta un guasto in una
COPIA di `input.c` e si pretende che diventi rosso **il caso dichiarato**.

    python3 06-b33-guasti.py --elenco
    python3 06-b33-guasti.py --file .../src/input.c --guasto G1
    python3 06-b33-guasti.py --file .../src/input.c --guasto nessuno   (rimette)

===========================================================================
⛔ PERCHE' NON BASTA «CHE DIVENTI ROSSO QUALCOSA»
===========================================================================

`CODER.md` §3.3, §3.4 e §3.10: un banco che nasce verde non ha mai visto il
difetto, e un banco che diventa rosso **da un'altra parte** dice solo che il
guasto ha rotto qualcosa — non che il controllo che ci interessa sappia
vedere.  ⇒ Ogni guasto porta scritto **quale caso** deve accendere, e il
lanciatore confronta quello e non il totale.

⚠ `04-b31-certifica.sh` ha pagato due volte questa regola il 15 agosto 2026:
  l'atteso di G1 dichiarava dieci casi rossi e ne ha accesi sei, e G9 restava
  verde perche' un SECONDO controllo mascherava il guasto innestato nel primo.
  ⇒ Quando l'atteso non torna si corregge **l'atteso**, con la ragione scritta
  accanto — non il verdetto.

===========================================================================
⛔ I GUASTI, E IL CASO CHE CIASCUNO DEVE ACCENDERE
===========================================================================

  G1  «tengo il puntatore VECCHIO»   ⇒ C2 (nessun puntatore dopo il riattacco)
  G2  «la regione si legge una volta sola»  ⇒ C2 (regione mai nota ⇒ -1)
  G3  «gli orfani non si segnano»    ⇒ ⛔ NON PIU' CERTIFICABILE QUI dal 21
      agosto 2026 (vedi il riquadro sotto): il suo controllo positivo vive in
      `06-b33-risveglio.sh tenuto`, caso T1
  G4  «il ricambio si conta solo sull'aggiunta»  ⇒ C6 (ricambi = 0)
  G5  «la tastiera si riaggancia ma non si riattiva»  ⇒ C3 e C4
"""
import argparse
import sys

# (nome, descrizione, caso atteso, cerca, sostituisci)
GUASTI = {
    # ⛔⛔ G1 e G2 SONO STATI CORRETTI DOPO LA PRIMA CERTIFICAZIONE — `[M]` 16
    #     agosto 2026 — e la ragione vale piu' dei due guasti.
    #
    #  · G1 diceva *«tengo il puntatore VECCHIO invece dell'ultimo arrivato»* e
    #    innestava `if (!in->puntatore)` in `dispositivo_aggiunto`.  ⛔ Non e' un
    #    guasto: `dispositivo_tolto` **azzera gia'** `in->puntatore`, e Mutter
    #    manda sempre `DEVICE_REMOVED` **prima** di `DEVICE_ADDED`.  ⇒ Al
    #    momento dell'aggiunta il puntatore e' NULL e il ramo prende il nuovo lo
    #    stesso.  ⭐ Cioe': la robustezza al ricambio **non viene** dal commento
    #    «SI PRENDE SEMPRE L'ULTIMO ARRIVATO», viene dall'azzeramento — e
    #    adesso e' misurato invece che creduto.
    #  · G2 toglieva la rilettura della regione da `DEVICE_ADDED`.  ⛔ Non si
    #    vede: la regione si rilegge in **TRE** posti (`DEVICE_ADDED`,
    #    `DEVICE_RESUMED`, `input_ritela`), e toglierne uno lascia gli altri
    #    due.  ⭐ La ridondanza c'era, ma nessuno l'aveva mai misurata.
    #
    # ⇒ Corretti tutt'e due perche' accendano davvero il caso dichiarato.
    # ⛔⛔ E LA SECONDA STESURA DI G1 NON HA ACCESO C2 NEMMENO LEI — `[M]` 16
    #     agosto 2026, e a questo punto la cosa misurata NON e' piu' il guasto:
    #     e' `input.c`.
    #
    # ⭐⭐ **La robustezza al ricambio del puntatore e' RIDONDANTE**, e adesso e'
    #     misurato: ci sono almeno TRE meccanismi indipendenti —
    #       1. `dispositivo_tolto` azzera `in->puntatore`;
    #       2. `dispositivo_aggiunto` sostituisce comunque l'ultimo arrivato;
    #       3. la regione si rilegge in tre posti.
    #     ⇒ Rompendone **uno solo** il comportamento non cambia: il codice sano
    #     ripara il guasto un istante dopo.  Per far comparire il difetto
    #     bisogna romperli **tutti**, ed e' quel che fa G2.
    #
    # ⚠ E il rovescio si dichiara, perche' e' un limite del banco: nessun caso
    #   di `06-b33` protegge il **singolo** meccanismo.  Il giorno che una
    #   riscrittura «semplifica» togliendone due insieme, il banco lo vede; se
    #   ne togliesse uno, no — e non se ne accorgerebbe nessuno.
    #
    # ⇒ G1 resta nell'elenco come **non-guasto misurato**, e il suo atteso e'
    #   «nessun caso»: e' una misura, non una prova fallita.
    "G1": (
        "NON-GUASTO MISURATO: tengo il puntatore vecchio, e il codice ripara",
        "nessuno",
        """		in->ricambi_puntatore++;
		registro_dice(AREA, "il puntatore e' stato TOLTO dal compositore (ricambio n. %u)",
		              in->ricambi_puntatore);
	}
	if (in->tastiera_dev == dispositivo)""",
        """		in->ricambi_puntatore++;
		/* guasto G1: il puntatore vecchio si rimette, e con lui la sua
		 * regione — e' «resto attaccato a un oggetto morto». */
		in->puntatore = ei_device_ref(dispositivo);
		in->puntatore_attivo = TRUE;
		in->regione_nota = TRUE;
		registro_dice(AREA, "il puntatore e' stato TOLTO dal compositore (ricambio n. %u)",
		              in->ricambi_puntatore);
	}
	if (in->tastiera_dev == dispositivo)""",
    ),
    "G2": (
        "la regione non si rilegge MAI: ne' ADDED, ne' RESUMED, ne' ritela",
        "C2",
        """static void leggi_regione(Input *in, struct ei_device *dispositivo)
{""",
        """static void leggi_regione(Input *in, struct ei_device *dispositivo)
{
	/* guasto G2: la regione si legge una volta sola, all'avvio.  ⛔ E' il
	 * difetto che il riquadro sopra questa funzione descrive: un banco che
	 * legge la regione una volta sola resta VERDE mentre il difetto e' vivo. */
	if (in->ricambi_puntatore)
		return;""",
    ),
    # ⛔⛔ G3 NON SI PUO' PIU' CERTIFICARE IN `06-b33` — `[M]` 21 agosto 2026, e
    #     non e' un difetto del guasto: e' la CURA che gli ha tolto la scena.
    #
    #     `figlio.c:3964` rilascia tutto **prima** di `cattura_ridimensiona()`.
    #     ⇒ Al ricambio non c'e' piu' niente di premuto, `segna_orfani()` non
    #     viene chiamata **nemmeno nel prodotto sano**, e toglierla non cambia
    #     una virgola.  `[M]` Certificazione del 21 agosto: G3 innestato accende
    #     **zero** casi, e i giri sano e risanato in modo `tenuto` sono identici
    #     a lui.
    #
    # ⚠ Fino a oggi lo script diceva lo stesso *«⭐ G3 ha acceso il caso
    #   dichiarato (R1)»*, perche' R1 era rosso anche col prodotto SANO — per la
    #   cura, non per il guasto — e il confronto era per APPARTENENZA.  E' il
    #   rilievo n. 1 della revisione avversariale del 21 agosto.
    #
    # ⭐ E la scena dove `segna_orfani()` gira davvero c'e', ed e' nuova:
    #   `banchi/06-b33-risveglio.sh tenuto` — un pulsante tenuto giu' durante un
    #   `cattura_risveglia()`, che la cura NON copre (§7.1).  Li' il caso T1
    #   legge proprio la riga degli orfani.  ⇒ Il giorno che la seconda porta
    #   sara' curata, anche quella scena perdera' G3, e allora il guasto andra'
    #   spostato su una prova di unita' invece che su una scena.
    "G3": (
        "gli orfani non si segnano: il registro torna a dire «fatto»",
        "nessuno",
        """		segna_orfani(in, in->bottoni, in->bottoni_orfani, MAX_BOTTONE, in->quanti_bottoni,
		             "pulsanti");""",
        """		/* guasto G3 innestato */""",
    ),
    "G4": (
        "il ricambio si conta solo sull'aggiunta (il difetto del 14 agosto)",
        "C6",
        """		in->ricambi_puntatore++;
		registro_dice(AREA, "il puntatore e' stato TOLTO dal compositore (ricambio n. %u)",
		              in->ricambi_puntatore);""",
        """		/* guasto G4 innestato: il contatore guarda solo l'aggiunta */""",
    ),
    "G5": (
        "la tastiera si riaggancia ma non si riattiva",
        "C3",
        """			if (dispositivo == in->tastiera_dev)
				in->tastiera_attiva = TRUE;""",
        """			/* guasto G5 innestato */""",
    ),
}


def main():
    p = argparse.ArgumentParser(description="06-b33 — i guasti innestati")
    p.add_argument("--file", default="")
    p.add_argument("--guasto", default="")
    p.add_argument("--elenco", action="store_true")
    a = p.parse_args()

    if a.elenco or not a.guasto:
        for k, (d, caso, _, _) in ((k, (v[0], v[1], v[2], v[3]))
                                   for k, v in GUASTI.items()):
            print(f"{k}  {d}\n    ⇒ deve accendere: {caso}")
        return 0

    if a.guasto == "nessuno":
        print("nessun guasto: rimetti il file sano dalla copia")
        return 0
    if a.guasto not in GUASTI:
        print(f"⛔ guasto sconosciuto: {a.guasto}")
        return 2

    desc, caso, cerca, metti = GUASTI[a.guasto]
    with open(a.file, encoding="utf-8") as f:
        s = f.read()
    # ⛔ E si conta: `replace` su una stringa assente non da' errore e
    #    lascerebbe il file SANO con l'aria di essere guasto — cioe' il giro
    #    «guasto» resterebbe verde e si concluderebbe che il banco non vede.
    if s.count(cerca) != 1:
        print(f"⛔ {a.guasto}: la stringa da sostituire compare "
              f"{s.count(cerca)} volte, non una.  Non innesto niente: un "
              f"guasto che non si innesta e' peggio di nessun guasto")
        return 3
    with open(a.file, "w", encoding="utf-8") as f:
        f.write(s.replace(cerca, metti))
    print(f"⭐ {a.guasto} innestato: {desc}")
    print(f"   deve accendere il caso {caso}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
