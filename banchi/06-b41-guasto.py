#!/usr/bin/env python3
"""06-b41-guasto.py — innesta in una COPIA il guasto «senza la cura di 6.4».

    python3 06-b41-guasto.py <rcp.c sano> <rcp.c da scrivere>
    python3 06-b41-guasto.py --controllo     ⭐ prova l'innesto su un finto

⛔ IL CONTROLLO POSITIVO DELLA MISURA, e il 17 agosto NON HA RESO.
   `fasi/06 §4.8`: togliendo la cura di 6.4 le richieste incatenate danno
   **ancora 0 su 18** a macchina ferma.  ⇒ Se sotto contesa GPU il guasto
   torna a mordere, si sa finalmente **che cosa tiene quella scena**; se non
   morde nemmeno li', il 4/18 del 16 agosto ha un'altra causa e va detto.

⛔⛔ L'ANCORA E' TESTO, NON UN NUMERO DI RIGA — `fasi/06 §5.2`, difetto n° 1:
    `04-b31-certifica.sh` aveva l'ancora del guasto G8 **scaduta** da un
    giorno (una funzione nuova si era interposta), e *il piu' grave dei dodici
    guasti non si innestava piu'*.  Il certificatore lo diceva con `??`, e
    nessuno lo lanciava.  ⇒ Qui l'innesto **pretende** di trovare l'ancora
    **una volta sola** e muore se non la trova.

LA CURA CHE SI TOGLIE
    `rcp.c`, in `rcp_tela_richiama()`: quando il palco se ne va per conto suo
    e c'e' una `ADATTA_TELA` **in volo**, il server richiama il palco alla
    misura **in volo** invece che alla tela in vigore.  Senza, il fondo di
    §7.1 scade e l'utente si vede rifiutare con `NON_ORA` una richiesta che
    stava per riuscire.
"""
import sys

ANCORA = """	uint32_t verso_l = s->tela_volo ? s->tela_volo_l : s->tela_l;
	uint32_t verso_a = s->tela_volo ? s->tela_volo_a : s->tela_a;"""

GUASTO = """	/* ⛔ GUASTO INNESTATO DA 06-b41-guasto.py — la cura di 6.4 TOLTA.
	 *    Si richiama sempre la tela in vigore, come prima della cura: una
	 *    `ADATTA_TELA` in volo viene condannata al `NON_ORA`. */
	uint32_t verso_l = s->tela_l;
	uint32_t verso_a = s->tela_a;"""


def innesta(testo):
    n = testo.count(ANCORA)
    if n != 1:
        raise SystemExit(
            f"⛔ ANCORA SCADUTA: trovata {n} volte invece di 1.\n"
            f"   ⚠ Non si innesta «a occhio»: senza l'ancora il guasto NON"
            f" c'e',\n     e il banco resterebbe verde per costruzione"
            f" (fasi/06 §5.2 n° 1).\n"
            f"   Il testo cercato e':\n{ANCORA}")
    return testo.replace(ANCORA, GUASTO)


def controllo():
    print("⭐ CONTROLLO POSITIVO DELL'INNESTO\n")
    guai = []
    finto = "prima\n" + ANCORA + "\ndopo\n"
    fuori = innesta(finto)
    for nome, cond in [
        ("l'ancora sparisce", ANCORA not in fuori),
        ("il guasto compare", "GUASTO INNESTATO" in fuori),
        ("verso_l non guarda piu' tela_volo",
         "verso_l = s->tela_l;" in fuori and "tela_volo_l : s->tela_l" not in fuori),
        ("il resto del file resta", "prima" in fuori and "dopo" in fuori),
    ]:
        print(f"    {'OK ' if cond else '⛔ '} {nome}")
        if not cond:
            guai.append(nome)
    # ⛔ E il veleno: su un file SENZA l'ancora l'innesto deve MORIRE, non
    #    restituire il file intatto con l'aria di aver fatto qualcosa.
    try:
        innesta("un file che non c'entra niente\n")
        print("    ⛔  su un file senza ancora NON e' morto: l'innesto potrebbe"
              " passare inosservato")
        guai.append("innesto silenzioso")
    except SystemExit:
        print("    OK  su un file senza ancora MUORE (ancora scaduta dichiarata)")
    # ⛔ E su un file con DUE ancore pure: due punti da curare, uno solo curato.
    try:
        innesta(ANCORA + "\n" + ANCORA + "\n")
        print("    ⛔  con DUE ancore non e' morto")
        guai.append("ancora doppia")
    except SystemExit:
        print("    OK  con DUE ancore MUORE (non si innesta a metà)")
    print()
    if guai:
        print(f"⛔ CONTROLLO FALLITO: {guai}")
        return 1
    print("⭐ CONTROLLO SUPERATO")
    return 0


if __name__ == "__main__":
    if "--controllo" in sys.argv:
        sys.exit(controllo())
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sorgente, destinazione = sys.argv[1], sys.argv[2]
    if sorgente == destinazione:
        sys.exit("⛔ il guasto si innesta in una COPIA, mai sul sano")
    testo = open(sorgente, encoding="utf-8").read()
    fuori = innesta(testo)
    open(destinazione, "w", encoding="utf-8").write(fuori)
    print(f"⭐ innestato: {sorgente} → {destinazione} "
          f"({len(testo)} → {len(fuori)} byte)")
