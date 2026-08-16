#!/usr/bin/env python3
"""06-b33-giudice.py — ⛔ IL VERDETTO, e non lo da' chi manda.

    python3 06-b33-giudice.py --visto /media/REMOTIX/tmp/06-i/visto.jsonl \\
        --registro /media/REMOTIX/tmp/06-i/registro.log --da 5 \\
        --modo comanda --etichetta g7 --esiti .../06-b33-esiti.jsonl

⚠ Gira SUL SERVER, fuori dal contenitore, da root (i due file sono di root).
  Non ha nessuna dipendenza oltre alla libreria standard: e' voluto, cosi' il
  giudice si puo' eseguire anche quando il contenitore non c'e'.

===========================================================================
⛔ CHE COSA GIUDICA, E CHE COSA NON PUO' GIUDICARE
===========================================================================

Giudica **quel che una finestra vera dentro la sessione ha ricevuto** — cioe'
`CODER.md` §3.8, il lato che consuma.  ⛔ NON giudica il registro del server come
prova che l'input sia arrivato: quello dice che abbiamo chiamato una funzione.
Il registro si legge solo per le righe che **dichiarano un ripiego**, dove la
domanda e' proprio *«c'e' la riga?»*.

⛔⛔ E NON C'E' NESSUN BROWSER IN QUESTO BANCO, ne' Xvfb.  Il testimone e' una
    finestra Wayland nativa e il cliente e' un QUIC nativo.  ⇒ `LEZIONI.md`
    §1.15 — *su Xvfb `requestAnimationFrame` non gira mai, e in Blink l'evento
    `resize` si consegna dentro il giro di rendering* — **non tocca nessuna
    misura di questo banco**, e per la stessa ragione questo banco **non puo'
    dire niente** sulla scala di disegno, su `pixelated`, ne' sul cammino della
    pagina che segue la finestra: quelli vivono nel browser e sono di 6.5.

===========================================================================
⛔ IL DIFETTO ATTESO NON E' UN VERDE
===========================================================================

Nel modo `tenuto` c'e' un caso il cui esito **giusto oggi e' rosso**: il
rilascio del pulsante dopo il ricambio non arriva, e non e' curabile da
`input.c` (vedi il riquadro in testa a `src/input.c`).  ⇒ Si dichiara
`DIFETTO_VIVO` e non `OK`: un banco che chiamasse «verde» un difetto misurato
sarebbe la cosa che `CODER.md` §4.6 vieta.  ⚠ Il giorno che `figlio.c:3964`
rilascia prima di ridimensionare, quel caso deve diventare `OK` — e se non
diventa, la cura non e' quella che si credeva.
"""
import argparse
import json
import os
import sys

VERDE, ROSSO, GIALLO, GRIGIO = "\033[1;32m", "\033[1;31m", "\033[1;33m", "\033[0m"
BTN_LEFT, KEY_ENTER, KEY_A, KEY_CTRL = 272, 28, 30, 29


def leggi_visto(percorso, da):
    """Le righe del testimone con `n` > `da`.  ⛔ E si tiene il numero: e' il
    denominatore, e senza «zero eventi» e «non ho guardato» sono uguali."""
    fuori = []
    with open(percorso, encoding="utf-8", errors="replace") as f:
        for riga in f:
            riga = riga.strip()
            if not riga.startswith("{"):
                continue
            try:
                d = json.loads(riga)
            except ValueError:
                continue
            if d.get("n", 0) > da:
                fuori.append(d)
    return fuori


def indice(righe, prova):
    for i, d in enumerate(righe):
        if prova(d):
            return i
    return -1


def tasto(righe, codice, premuto, dopo=-1):
    return indice(righe[dopo + 1:], lambda d: d.get("tipo") == "TASTO"
                  and d.get("codice") == codice
                  and d.get("premuto") == premuto)


def main():
    p = argparse.ArgumentParser(description="06-b33 — il verdetto")
    p.add_argument("--visto", required=True)
    p.add_argument("--registro", required=True)
    p.add_argument("--da", type=int, default=0)
    p.add_argument("--modo", choices=["comanda", "tenuto", "cura"],
                   default="comanda")
    p.add_argument("--etichetta", default="giro")
    p.add_argument("--scena", default="(non dichiarata)")
    p.add_argument("--tela-b", default="1000x640")
    p.add_argument("--esiti", default="")
    a = p.parse_args()

    righe = leggi_visto(a.visto, a.da)
    try:
        with open(a.registro, encoding="utf-8", errors="replace") as f:
            reg = f.read()
    except OSError:
        reg = ""
    bl, ba = (int(x) for x in a.tela_b.lower().split("x"))

    casi = []

    def caso(nome, esito, dettaglio):
        casi.append({"caso": nome, "esito": esito, "dettaglio": dettaglio})

    # ⛔ IL CONTROLLO ZERO: lo strumento ha visto QUALCOSA?  Un giudice che
    #    dicesse «nessun BOTTONE» su un file vuoto accuserebbe il prodotto di
    #    una cosa che non ha fatto (`CODER.md` §3.10, e §3.3 al rovescio).
    if not righe:
        caso("C0 lo strumento ha visto qualcosa", "NO",
             f"ZERO righe del testimone dopo n={a.da}: ⛔ IL BANCO, NON IL "
             f"PRODOTTO — il testimone non era aperto, o non aveva il fuoco")
        stampa(a, casi)
        return 3
    caso("C0 lo strumento ha visto qualcosa", "OK",
         f"{len(righe)} righe dopo n={a.da}")

    # ---- C1: il RITELA, dal lato che riceve -------------------------------
    i_rit = indice(righe, lambda d: d.get("tipo") == "RITELA")
    if i_rit >= 0:
        r = righe[i_rit]
        ok = (r.get("a_l"), r.get("a_a")) == (bl, ba)
        caso("C1 il compositore ha ridimensionato sotto una finestra APERTA",
             "OK" if ok else "NO",
             f"RITELA {r.get('da_l')}x{r.get('da_a')} → "
             f"{r.get('a_l')}x{r.get('a_a')} (atteso …→{bl}x{ba})")
    else:
        caso("C1 il compositore ha ridimensionato sotto una finestra APERTA",
             "NO", "nessuna riga RITELA: la finestra non e' stata "
                   "ridimensionata, quindi i dispositivi non sono ricambiati "
                   "⇒ ⛔ IL BANCO, NON IL PRODOTTO")
        i_rit = -1

    dopo = righe[i_rit + 1:] if i_rit >= 0 else []

    if a.modo in ("comanda", "cura"):
        # ---- C2: il puntatore, alle coordinate ESATTE ---------------------
        # ⛔ Esatte, non «e' arrivato qualcosa»: §7.3 vieta al server di
        #    trasformare le coordinate, e una scala silenziosa e' proprio il
        #    difetto che `input.c` dichiara invece di applicare.
        attesi = [(bl // 4, ba // 4), (bl * 3 // 4, ba * 3 // 4)]
        visti = [(d.get("x"), d.get("y")) for d in dopo
                 if d.get("tipo") in ("PUNTATORE", "PUNTATORE_ENTRA")]
        mancano = [q for q in attesi
                   if not any(abs(vx - q[0]) < 1 and abs(vy - q[1]) < 1
                              for vx, vy in visti)]
        caso("C2 il puntatore arriva DOPO il riattacco, alle coordinate esatte",
             "OK" if not mancano else "NO",
             f"attesi {attesi}, visti {visti}"
             + (f" — MANCANO {mancano}" if mancano else ""))

        # ---- C3: il tasto -------------------------------------------------
        g = tasto(dopo, KEY_ENTER, 1)
        s = tasto(dopo, KEY_ENTER, 0, g) if g >= 0 else -1
        caso("C3 il TASTO arriva DOPO il riattacco (Invio giu' e su)",
             "OK" if g >= 0 and s >= 0 else "NO",
             f"KEY_ENTER giu' {'si' if g >= 0 else 'NO'}, "
             f"su {'si' if s >= 0 else 'NO'}")

        # ---- C4: la LETTERA, cioe' la disposizione riletta -----------------
        g = tasto(dopo, KEY_A, 1)
        caso("C4 la LETTERA «a» esce come posizione 30 (disposizione riletta)",
             "OK" if g >= 0 else "NO",
             "KEY_A visto" if g >= 0 else "nessun KEY_A: la keymap non e' "
                                          "stata riletta, o la lettera non e' "
                                          "producibile")

        # ---- C5: il CLIC --------------------------------------------------
        g = indice(dopo, lambda d: d.get("tipo") == "BOTTONE"
                   and d.get("bottone") == BTN_LEFT and d.get("premuto") == 1)
        s = indice(dopo[g + 1:], lambda d: d.get("tipo") == "BOTTONE"
                   and d.get("bottone") == BTN_LEFT
                   and d.get("premuto") == 0) if g >= 0 else -1
        caso("C5 il CLIC arriva DOPO il riattacco (BTN_LEFT giu' e su)",
             "OK" if g >= 0 and s >= 0 else "NO",
             f"BTN_LEFT giu' {'si' if g >= 0 else 'NO'}, "
             f"su {'si' if s >= 0 else 'NO'}")

    if a.modo == "cura":
        # ⭐ Il rilascio PRIMA del ricambio: e' la cura, simulata dal filo.
        prima = righe[:i_rit] if i_rit >= 0 else righe
        s = indice(prima, lambda d: d.get("tipo") == "BOTTONE"
                   and d.get("bottone") == BTN_LEFT and d.get("premuto") == 0)
        caso("K1 il rilascio PRIMA del ricambio arriva", "OK" if s >= 0 else "NO",
             "BTN_LEFT su visto prima del RITELA" if s >= 0
             else "⛔ non arriva nemmeno prima: la cura proposta non e' quella")

    if a.modo == "tenuto":
        prima = righe[:i_rit] if i_rit >= 0 else righe
        g = indice(prima, lambda d: d.get("tipo") == "BOTTONE"
                   and d.get("bottone") == BTN_LEFT and d.get("premuto") == 1)
        caso("T1 il pulsante era GIU' prima del ricambio",
             "OK" if g >= 0 else "NO",
             "BTN_LEFT giu' visto prima del RITELA" if g >= 0
             else "⛔ IL BANCO: non si e' mai premuto niente, quindi non c'e' "
                  "nessun orfano da misurare")

        s = indice(dopo, lambda d: d.get("tipo") == "BOTTONE"
                   and d.get("bottone") == BTN_LEFT and d.get("premuto") == 0)
        # ⛔ E QUI L'ESITO GIUSTO OGGI E' «DIFETTO_VIVO», non «OK».
        caso("T2 ⛔ il rilascio DOPO il ricambio arriva?",
             "OK" if s >= 0 else "DIFETTO_VIVO",
             "arriva — ⭐ allora `figlio.c:3964` e' stato curato" if s >= 0
             else "NON arriva: il posto conta il pulsante ancora giu' e da "
                  "adesso nessun clic funziona (`meta-seat-impl.c:899-908`)")

        k = indice(dopo, lambda d: d.get("tipo") == "TASTO"
                   and d.get("codice") == KEY_CTRL and d.get("premuto") == 0)
        # ⚠ Controllo INTERNO alla scena: la tastiera non e' un dispositivo di
        #   viewport e non ricambia, quindi il suo rilascio DEVE arrivare.  Se
        #   non arrivasse, la causa sarebbe un'altra e T2 accuserebbe la cosa
        #   sbagliata.
        caso("T3 il rilascio del TASTO invece arriva (la tastiera non ricambia)",
             "OK" if k >= 0 else "NO",
             "Ctrl su visto dopo il RITELA" if k >= 0
             else "⛔ non arriva nemmeno il tasto: la causa NON e' il ricambio "
                  "del puntatore, e T2 sta accusando la cosa sbagliata")

    # ---- le righe che DEVONO esserci nel registro -------------------------
    # ⛔ Qui la domanda e' «c'e' la riga?», che e' l'unica domanda a cui il
    #    registro di chi manda risponda onestamente.
    if a.modo == "tenuto":
        for nome, pezzo in (
                ("R1 il ricambio con qualcosa di premuto e' DICHIARATO",
                 "erano PREMUTI sul dispositivo che il compositore ha appena tolto"),
                ("R2 il rilascio impossibile e' DICHIARATO",
                 "NON PARTE: era premuto su un dispositivo")):
            caso(nome, "OK" if pezzo in reg else "NO",
                 "la riga c'e'" if pezzo in reg
                 else "⛔ la riga NON c'e': il registro dice «fatto» mentre il "
                      "desktop resta bloccato — `CODER.md` §4.6")

    # ---- i ricambi, LETTI e non dedotti -----------------------------------
    rp = reg.count("il puntatore e' stato TOLTO dal compositore")
    rt = reg.count("la tastiera e' stata TOLTA dal compositore")
    caso("C6 il puntatore ricambia, la tastiera NO (al cambio di GEOMETRIA)",
         "OK" if rp >= 1 and rt == 0 else "NO",
         f"ricambi_puntatore={rp} ricambi_tastiera={rt} — atteso ≥1 e 0 "
         f"(`meta-eis-client.c:197-206`: `remove_viewport_devices` guarda solo "
         f"TOUCH e POINTER_ABSOLUTE)")

    return stampa(a, casi)


def stampa(a, casi):
    print(f"\n== 06-b33 · giudizio «{a.etichetta}» · modo {a.modo}")
    print(f"   scena: {a.scena}")
    rossi = 0
    for c in casi:
        col = {"OK": VERDE, "NO": ROSSO, "DIFETTO_VIVO": GIALLO}[c["esito"]]
        print(f"   {col}{c['esito']:12s}{GRIGIO} {c['caso']}")
        print(f"                {c['dettaglio']}")
        if c["esito"] == "NO":
            rossi += 1
    vivi = sum(1 for c in casi if c["esito"] == "DIFETTO_VIVO")
    print(f"\n   {len(casi)} casi · {rossi} rossi · {vivi} difetti vivi "
          f"dichiarati")
    if a.esiti:
        with open(a.esiti, "a", encoding="utf-8") as f:
            f.write(json.dumps({"etichetta": a.etichetta, "modo": a.modo,
                                "scena": a.scena, "casi": casi},
                               ensure_ascii=False) + "\n")
        print(f"   esiti: {a.esiti}")
    return 1 if rossi else 0


if __name__ == "__main__":
    sys.exit(main())
