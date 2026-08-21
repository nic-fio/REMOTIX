#!/usr/bin/env python3
"""06-b33-risveglio-guasti.py — ⛔ I GUASTI INNESTATI del banco di §7.1.

    python3 06-b33-risveglio-guasti.py --elenco
    python3 06-b33-risveglio-guasti.py --albero /media/REMOTIX/src/06-i-src \\
        --guasto RG1

⛔ Si innesta in una COPIA dell'albero, mai nell'originale: chi chiama salva i
   file sani PRIMA e li rimette DOPO (`06-b33-risveglio-certifica.sh`).

===========================================================================
⛔ PERCHE' QUESTO FILE ESISTE, E PERCHE' NON BASTAVA `06-b33-guasti.py`
===========================================================================

`06-b33-guasti.py` innesta guasti in `input.c` e li giudica con la scena del
**ridimensionamento**.  ⛔ Dal 21 agosto 2026 quella scena non basta piu', e per
una ragione che va scritta perche' nessuno la riscopra:

  ⭐ La cura di `figlio.c:3964` rilascia tutto **prima** di
    `cattura_ridimensiona()`.  ⇒ In quella scena, col prodotto SANO, non c'e'
    piu' niente di premuto al momento del ricambio: `segna_orfani()` **non viene
    chiamata affatto**, e il guasto G3 — che la toglie — non cambia una virgola.
    `[M]` Certificazione del 21 agosto: G3 innestato accende **zero** casi.

⇒ La scena in cui gli orfani nascono davvero e' quella di **questo** banco: un
  pulsante tenuto giu' durante un `cattura_risveglia()`, che la cura di `:3964`
  non copre (§7.1).  ⭐ Il controllo positivo di G3 vive qui, ed e' `RG2`.

===========================================================================
⛔ I GUASTI, E IL CASO CHE CIASCUNO DEVE CAMBIARE
===========================================================================

⚠ E qui non si chiede «quale caso diventa ROSSO», ma **quali verdetti
  CAMBIANO** rispetto al giro sano.  La ragione e' che gli attesi di questo
  banco hanno tre colori: togliendo la cura «C» i casi T3 e T4 non diventano
  rossi, tornano `DIFETTO_VIVO` — che e' il colore giusto per un difetto
  misurato, e un confronto che guardasse solo il rosso non li vedrebbe.

  RG1  «la cura C non scatta»            ⇒ T3 e T4 tornano DIFETTO_VIVO
  RG2  «gli orfani dei PULSANTI non si segnano»  ⇒ T1 T3 T4 T7
       ⭐ e' l'ex G3, che in `06-b33` non e' piu' certificabile
  RG3  ⛔ NON-GUASTO MISURATO: «il riattacco non chiude il descrittore vecchio»
       ⇒ **nessun caso cambia**, e la scoperta vale piu' del guasto
  RG4  ⛔ SECONDO NON-GUASTO MISURATO: «non si manda il distacco a libei»
       ⇒ **nessun caso cambia** — e insieme a RG3 dice la cosa vera
  RG5  «ne' distacco ne' chiusura: il contesto vecchio resta vivo»
       ⇒ T3 T4 T5 T7.  ⭐ e' il guasto che chiude la domanda

===========================================================================
⛔⛔ E UNA MIA SPIEGAZIONE E' STATA SMENTITA DALLA MISURA — 21 agosto 2026
===========================================================================

Avevo scritto, e il coordinatore l'aveva presa come specifica, che *«la cura non
puo' stare in `input.c`, perche' finche' il descrittore messo da parte da
`mutter.c` resta aperto il socket e' ancora connesso e Mutter non vede nessun
distacco»*.  ⛔ **RG3 la smentisce**: tolto il `close()`, la guarigione funziona
lo stesso e **nessun caso cambia**.

⛔⛔ E LA MIA SECONDA SPIEGAZIONE E' STATA SMENTITA A SUA VOLTA.  Avevo detto:
     *«allora e' `ei_disconnect()` che manda il distacco come messaggio di
     protocollo»*, e avevo scritto RG4 per provarlo.  ⛔ `[M]` **Anche RG4 non
     cambia niente.**

⇒ ⭐ **Le due strade sono RIDONDANTI, e ciascuna basta da sola**:
     · `ei_disconnect()` manda il distacco di protocollo;
     · `ei_unref()` + il `close()` di `mutter.c` chiudono l'ultimo descrittore
       del socket, e Mutter vede l'EOF.
   ⇒ Togliendone UNA la guarigione regge (RG3, RG4).  `RG5` le toglie
     **tutt'e due** ed e' l'unico guasto che la rompe.

⚠ La lezione, e vale piu' della meccanica: **due ipotesi consecutive, tutt'e due
  plausibili, tutt'e due smentite dal guasto innestato.**  Nessuna delle due
  sarebbe stata scoperta rileggendo il codice — e la prima era gia' scritta in
  `mutter.h` come se fosse un fatto (`CODER.md` §4.6: `[R]` non e' `[M]`).

⭐ `mutter_eis_riattacca()` resta necessaria comunque, e questo NON e' stato
  smentito: dopo il distacco il descrittore messo da parte e' morto, e uno NUOVO
  lo puo' chiedere solo chi ha il bus e il percorso della sessione.
"""
import argparse
import os
import sys

# (file, descrizione, casi che devono CAMBIARE, cerca, sostituisci)
GUASTI = {
    # ⛔ RG1 — la cura «C» esiste ma non viene mai chiamata.  E' il controllo
    #    positivo della cura stessa: se togliendola il banco resta verde, il
    #    verde non era della cura.
    "RG1": (
        "src/input.c",
        "la cura «C» non scatta: `guarisci()` non viene mai chiamata",
        "T3 T4",
        """	if (in->guarigione_dovuta && !in->caduto)
		guarisci(in);""",
        """	/* guasto RG1 innestato: la cura «C» non scatta */
	(void) guarisci;""",
    ),
    # ⛔ RG2 — l'ex G3, spostato nella scena dove gli orfani nascono davvero.
    #    ⚠ Tocca SOLO i pulsanti: nella scena si tiene giu' anche il Ctrl, e la
    #      chiamata dei TASTI resta — quindi la guarigione scatta lo stesso e
    #      T3/T4 NON cambiano.  ⭐ E' voluto: cosi' il guasto e' chirurgico e
    #      accende un caso solo, e il confronto per uguaglianza lo pretende.
    "RG2": (
        "src/input.c",
        "gli orfani dei PULSANTI non si segnano: il registro torna a dire «fatto»",
        # ⛔ L'ATTESO E' STATO CORRETTO DALLA MISURA, non il verdetto — 21 ago
        #    2026.  Avevo dichiarato «solo T1», ragionando che il Ctrl tenuto giu'
        #    avrebbe fatto scattare `segna_orfani()` dei TASTI e quindi la
        #    guarigione.  ⛔ Falso, ed e' `[M]`: al cambio di viewport la tastiera
        #    **non ricambia** (`remove_viewport_devices` guarda solo TOUCH e
        #    POINTER_ABSOLUTE), quindi `dispositivo_tolto()` non viene mai
        #    chiamata per lei e i suoi orfani non si segnano mai.  ⇒ In questa
        #    scena la bandiera della guarigione dipende **solo dai pulsanti**.
        "T1 T3 T4 T7",
        """		segna_orfani(in, in->bottoni, in->bottoni_orfani, MAX_BOTTONE, in->quanti_bottoni,
		             "pulsanti");""",
        """		/* guasto RG2 innestato: gli orfani dei pulsanti non si segnano */""",
    ),
    # ⛔⛔ RG3 — IL NON-GUASTO MISURATO, e la scoperta vale piu' del guasto.
    #
    #      L'avevo dichiarato «il piu' prezioso dei tre», con questa ragione:
    #      *«`input_apri()` fa un `dup` del descrittore che `mutter.c` tiene da
    #      parte, e finche' QUELLO resta aperto il socket e' ancora connesso ⇒
    #      Mutter non vede nessun distacco»*.  E avevo scritto accanto: *«se
    #      questo guasto non cambiasse niente, vorrebbe dire che la chiusura non
    #      serve»*.
    #
    # ⛔ `[M]` 21 agosto 2026: **non cambia niente**.  ⇒ La mia spiegazione era
    #    sbagliata, e la riga sopra e' l'unica ragione per cui lo so.
    #
    # ⭐ Il distacco lo manda `ei_disconnect()` come messaggio di protocollo, e
    #   Mutter esegue `meta_eis_client_disconnect()` senza aspettare l'EOF del
    #   socket.  Lo prova RG4.
    #
    # ⚠ Il guasto RESTA nell'elenco con l'atteso «nessuno», come G1 in
    #   `06-b33-guasti.py`: un non-guasto misurato e' informazione, e toglierlo
    #   farebbe riscoprire la stessa ipotesi sbagliata fra un mese.
    "RG3": (
        "src/mutter.c",
        "NON-GUASTO MISURATO: il riattacco non chiude il descrittore vecchio",
        "",
        """	if (sessione->eis >= 0)
	{
		close(sessione->eis);""",
        """	if (sessione->eis >= 0)
	{
		/* guasto RG3 innestato: NON si chiude */""",
    ),
    # ⛔⛔ RG4 — IL SECONDO NON-GUASTO MISURATO.
    #
    #      Nato perche' RG3 aveva smentito la prima spiegazione, e serviva sapere
    #      quale fosse quella giusta.  Avevo dichiarato «T3 T4», convinto che il
    #      distacco fosse il messaggio di protocollo di `ei_disconnect()`.
    #      ⛔ `[M]` 21 agosto 2026: **non cambia niente nemmeno lui**.
    #
    # ⇒ ⭐ Le due strade sono RIDONDANTI: `ei_disconnect()` manda il distacco, e
    #     `ei_unref()` + il `close()` di `mutter.c` fanno vedere a Mutter l'EOF
    #     del socket.  Ciascuna basta da sola — ed e' `RG5` a provarlo,
    #     togliendole tutt'e due.
    "RG4": (
        "src/input.c",
        "SECONDO NON-GUASTO MISURATO: non si manda il distacco a libei",
        "",
        """	ei_disconnect(in->ei);
	ei_unref(in->ei);""",
        """	/* guasto RG4 innestato: niente distacco, si molla e basta */
	ei_unref(in->ei);""",
    ),
    # ⛔⛔ RG5 — IL GUASTO CHE CHIUDE LA DOMANDA.  Toglie **tutt'e due** le
    #      strade: niente distacco di protocollo E niente chiusura del contesto
    #      (quindi il `dup` di `libei` resta aperto, e il socket non muore
    #      nemmeno quando `mutter.c` chiude il suo).
    #
    # ⇒ Se questo NON rompesse la guarigione, vorrebbe dire che il posto si
    #   sblocca per una terza ragione che non abbiamo ancora capito — e allora
    #   la cura «C» sarebbe un verde di cui non conosciamo la causa.
    #
    # ⚠ Il contesto vecchio viene abbandonato (perdita di memoria e di un
    #   descrittore): e' un guasto, non una proposta.
    "RG5": (
        "src/input.c",
        "ne' distacco ne' chiusura: il contesto vecchio resta vivo e connesso",
        # ⛔ L'ATTESO E' STATO CORRETTO DALLA MISURA — avevo dichiarato «T3 T4», e
        #    cambia anche **T5** (il rilascio del Ctrl).  ⚠ La ragione regge e
        #    vale la pena scriverla, perche' distingue RG5 da RG2:
        #      · in RG2 la guarigione NON scatta, quindi la tastiera non ricambia
        #        mai (non e' un dispositivo di viewport) e il suo rilascio arriva
        #        ⇒ T5 resta verde;
        #      · in RG5 la guarigione SCATTA — nasce un contesto nuovo con una
        #        tastiera nuova — ⛔ ma il vecchio canale non muore, quindi
        #        `drop_device()` non gira: il Ctrl resta giu' sul dispositivo
        #        vecchio e il rilascio sul nuovo lo ingoia `handle_key`.
        #    ⭐ E' la stessa forma del pulsante, sulla tastiera: la prima volta
        #      che questo progetto la vede accadere davvero.
        "T3 T4 T5 T7",
        """	ei_disconnect(in->ei);
	ei_unref(in->ei);
	in->ei = NULL;""",
        """	/* guasto RG5 innestato: il contesto vecchio resta VIVO e connesso */
	in->ei = NULL;""",
    ),
}


def main():
    p = argparse.ArgumentParser(description="06-b33 §7.1 — i guasti innestati")
    p.add_argument("--elenco", action="store_true")
    p.add_argument("--albero", default="")
    p.add_argument("--guasto", default="")
    a = p.parse_args()

    if a.elenco:
        for nome, (f, desc, casi, _c, _s) in GUASTI.items():
            print("%s  %s  [%s]" % (nome, desc, f))
            print("    ⇒ devono CAMBIARE: %s" % (casi or "nessuno"))
        return 0

    if not a.albero or not a.guasto:
        print("⛔ servono --albero e --guasto (oppure --elenco)", file=sys.stderr)
        return 2
    if a.guasto not in GUASTI:
        print("⛔ guasto ignoto: %s" % a.guasto, file=sys.stderr)
        return 2

    rel, _desc, _casi, cerca, sost = GUASTI[a.guasto]
    percorso = os.path.join(a.albero, rel)
    with open(percorso, encoding="utf-8") as f:
        testo = f.read()

    # ⛔ SI CONTA, e una sola occorrenza e' un requisito: un'ancora che compare
    #    due volte innesterebbe due guasti, e uno dei due nessuno lo sa.
    quante = testo.count(cerca)
    if quante != 1:
        print("⛔ l'ancora di %s compare %d volte in %s (ne serve UNA): il guasto NON "
              "si innesta, e questo NON e' «il guasto non fa niente»"
              % (a.guasto, quante, rel), file=sys.stderr)
        return 3

    with open(percorso, "w", encoding="utf-8") as f:
        f.write(testo.replace(cerca, sost, 1))
    print("⭐ %s innestato in %s" % (a.guasto, rel))
    return 0


if __name__ == "__main__":
    sys.exit(main())
