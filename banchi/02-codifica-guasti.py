#!/usr/bin/env python3
"""02-codifica-guasti.py — ⛔ i guasti che certificano il banco di F2.3.

    python3 02-codifica-guasti.py --elenco
    python3 02-codifica-guasti.py --verifica A       l'appiglio c'e' ed e' UNICO?
    python3 02-codifica-guasti.py --applica  A       innesta
    python3 02-codifica-guasti.py --togli    A       toglie, e RIVERIFICA l'impronta
    python3 02-codifica-guasti.py --catalogo         la riga per il catalogo (§3.3)

===========================================================================
⛔ PERCHE' ESISTE

⭐ La regola nata l'11 agosto 2026: **chi scrive un banco lo certifica nello
stesso giro**, o il conto non cala mai (`MANDATO-12-agosto-fase2.md` §3.3).
E `PIANO.md` §0.3 regola 4, con la frase di `01-b12-guasti.py`:

    ⛔ *«Un banco che non e' mai diventato rosso non e' pulito: e' NON
       CERTIFICATO.»*

Il giro e' **sano → guasto → risanato**, tre esecuzioni e non una: «e'
diventato rosso» non vuol dire niente se non era verde prima.

===========================================================================
⛔ PERCHE' QUESTI DUE GUASTI E NON ALTRI

Un guasto certifica **un organo**.  Il banco di F2.3 ne ha due che, se
smettessero di funzionare, lo lascerebbero **verde e inutile** — e sono
esattamente i due che nessun'altra prova coprirebbe:

  **A — l'organo dei 10 bit.**  E' l'unico controllo di tutto il progetto che
  distingua «10 bit veri» da «10 bit dichiarati».  ⛔ Se smettesse di
  funzionare, ogni giro futuro direbbe «Main10» di una catena a 8 bit, e
  `SPECIFICHE.md` §3.1 verrebbe dichiarato raggiunto senza esserlo.
  ⚠ E il guasto e' costruito perche' **l'etichetta resti onesta**: `ffprobe`
  continua a dire «Main 10» e ha ragione — e' la catena a consegnare 8 bit.
  Un banco che si fermasse a `ffprobe` resterebbe **verde**, ed e' precisamente
  la forma **E1** di `REVIEWER.md` §2.

  **B — l'organo del rifiuto.**  Un controllo negativo che non innesta niente
  passa da solo.  ⛔ Se `--storpia` producesse una copia intatta, il banco
  direbbe «tre storpiature rifiutate» avendone rifiutate zero — che e' la
  trappola n.2 di `01-b12-guasti.py`, *«il guasto che non e' stato
  innestato»*, applicata al controllo negativo stesso.

===========================================================================
⛔ LA MARCA, E LA META' CHE SI DIMENTICA

`01-b12-guasti.py` trappola n.1: un guasto che rompesse il banco in modo
generico lo farebbe diventare rosso **per la ragione sbagliata**, e
certificherebbe zero.  Da cui ogni guasto qui dichiara la **frase** che
l'uscita rossa deve contenere, e ⛔ **la frase non deve comparire nel giro
sano**: una marca che compare in tutt'e due i giri non e' una marca.
"""

import argparse
import hashlib
import json
import os
import sys

QUI = os.path.dirname(os.path.abspath(__file__))
LANCIA = os.path.join(QUI, "02-codifica-lancia.sh")
NAL = os.path.join(QUI, "02-codifica-nal.py")

GUASTI = {
    "A": {
        "sigla": "F2.3-A",
        "organo": "la prova dei 10 bit veri",
        "titolo": "la catena consegna 8 bit al codificatore, e l'etichetta resta ONESTA",
        "file": LANCIA,
        "appiglio": 'SORGENTE_VERA="$LAV/sorgente-10bit.yuv"',
        "sostituto": 'SORGENTE_VERA="$LAV/sorgente-8in10.yuv"  # GUASTO F2.3-A',
        "dimostra":
            "⛔ Il codificatore E' Main10 e non mente: `ffprobe` legge «Main 10» "
            "e `yuv420p10le` dall'SPS, e ha ragione.  E' la CATENA a consegnargli "
            "8 bit.  Il fotogramma decodificato viene BENE, e nessun occhio lo "
            "distingue dal vero.  ⭐ Solo il conteggio dei livelli sulla rampa "
            "cade da 877 a 220 e la frazione di multipli di 4 sale da ~0,25 a "
            "1,000.  Un banco che si fermasse all'etichetta resterebbe verde e "
            "scriverebbe «10 bit» nel rapporto della fase 2.",
        "marca": "10 BIT DICHIARATI MA NON VERI",
        "atteso_sano": 0,
        "atteso_guasto": 1,
        "riferimento": "SPECIFICHE.md §3.1 · DECISIONI.md §2.2, §2.3-bis · "
                       "LEZIONI.md §1.11 · REVIEWER.md §2 E1",
    },
    "B": {
        "sigla": "F2.3-B",
        "organo": "il controllo negativo — «questo banco sa vedere un rifiuto?»",
        "titolo": "`--storpia` non storpia: consegna una copia intatta",
        "file": NAL,
        "appiglio": "        dati[dove] ^= 0xFF",
        "sostituto": "        dati[dove] ^= 0x00  # GUASTO F2.3-B",
        "dimostra":
            "⛔ Il controllo negativo in coda esiste per dimostrare che il banco "
            "sa BOCCIARE.  Con questo guasto la storpiatura «byte-girato» non "
            "tocca piu' niente: il flusso resta valido, il lettore indipendente "
            "consegna il fotogramma buono, e il banco deve accorgersi che la "
            "prova non ha morso.  ⭐ Un banco che contasse le storpiature "
            "*tentate* invece di quelle *rifiutate* direbbe «3 su 3» avendone "
            "rifiutate 2.  ⚠ E il guasto e' scelto sull'unico dei tre modi che "
            "il 12 agosto 2026 e' gia' passato inosservato una volta per davvero.",
        "marca": "NON SA VEDERE UN RIFIUTO",
        "atteso_sano": 0,
        "atteso_guasto": 1,
        "riferimento": "REVIEWER.md §1 punto 5 · CODER.md §3.10 · "
                       "01-b12-guasti.py trappola n.2",
    },
}


def impronta(percorso):
    with open(percorso, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def conta(g):
    with open(g["file"], encoding="utf-8") as f:
        testo = f.read()
    return testo.count(g["appiglio"]), testo.count(g["sostituto"])


def verifica(sigla):
    """⛔ L'appiglio si conta PRIMA, e dev'essere esattamente UNO.

    Un appiglio che non si trova lascia il codice sano, il banco resta verde, e
    chi legge conclude «il banco non vede il guasto» — l'accusa esattamente
    opposta.  Un appiglio che si trova due volte innesta due guasti, e il rosso
    non si sa piu' di chi sia.
    """
    g = GUASTI[sigla]
    n_app, n_sos = conta(g)
    va = n_app == 1 and n_sos == 0
    print(json.dumps({"sigla": g["sigla"], "file": os.path.basename(g["file"]),
                      "appigli_trovati": n_app, "guasti_gia_dentro": n_sos,
                      "innestabile": va}, ensure_ascii=False))
    return 0 if va else 1


def applica(sigla):
    g = GUASTI[sigla]
    n_app, n_sos = conta(g)
    if n_sos:
        print(f"⛔ {g['sigla']} e' GIA' innestato: non se ne innestano due")
        return 1
    if n_app != 1:
        print(f"⛔ appigli trovati: {n_app}, e ne serve esattamente 1")
        return 1
    prima = impronta(g["file"])
    with open(g["file"], encoding="utf-8") as f:
        testo = f.read()
    with open(g["file"] + ".sano", "w", encoding="utf-8") as f:
        f.write(testo)
    with open(g["file"], "w", encoding="utf-8") as f:
        f.write(testo.replace(g["appiglio"], g["sostituto"], 1))
    print(json.dumps({"innestato": g["sigla"], "file": g["file"],
                      "impronta_sana": prima,
                      "marca_attesa_nel_rosso": g["marca"],
                      "uscita_attesa": g["atteso_guasto"]}, ensure_ascii=False))
    return 0


def togli(sigla):
    """⛔ Non ci si fida di aver tolto: si RIVERIFICA l'impronta byte per byte.

    Trappola n.3 di `01-b12-guasti.py`: un guasto che sopravvive avvelena ogni
    misura successiva, e nessuno sapra' che c'era.
    """
    g = GUASTI[sigla]
    copia = g["file"] + ".sano"
    if not os.path.exists(copia):
        print(f"⛔ manca {copia}: non so a che cosa riportarlo")
        return 2
    atteso = impronta(copia)
    with open(copia, encoding="utf-8") as f:
        testo = f.read()
    with open(g["file"], "w", encoding="utf-8") as f:
        f.write(testo)
    adesso = impronta(g["file"])
    n_app, n_sos = conta(g)
    pulito = adesso == atteso and n_sos == 0 and n_app == 1
    if pulito:
        os.remove(copia)
    print(json.dumps({"tolto": g["sigla"], "impronta": adesso[:16] + "…",
                      "combacia": adesso == atteso, "guasti_rimasti": n_sos,
                      "risanato": pulito}, ensure_ascii=False))
    return 0 if pulito else 1


def catalogo():
    """⛔ La riga per il catalogo delle certificazioni (mandato §3.3).

    Nella forma di `01-b12-guasti.py`: nome, comando, atteso sano, guasto da
    innestare, atteso guasto.
    """
    for k, g in GUASTI.items():
        print(f"┌── {g['sigla']} — {g['organo']}")
        print(f"│  banco            02-codifica-lancia.sh")
        print(f"│  comando          bash banchi/02-codifica-lancia.sh")
        print(f"│  ⛔ ATTESO SANO    uscita {g['atteso_sano']} · «VERDE» · e la marca "
              f"«{g['marca']}» NON compare")
        print(f"│  guasto            {g['titolo']}")
        print(f"│    file            {os.path.basename(g['file'])}")
        print(f"│    si sostituisce  {g['appiglio']}")
        print(f"│    con             {g['sostituto']}")
        print(f"│  ⛔ ATTESO GUASTO  uscita {g['atteso_guasto']} · «ROSSO» · e l'uscita "
              f"CONTIENE «{g['marca']}»")
        print(f"│  dimostra          {g['dimostra']}")
        print(f"└  riferimento       {g['riferimento']}")
        print()
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--elenco", action="store_true")
    p.add_argument("--catalogo", action="store_true")
    p.add_argument("--verifica")
    p.add_argument("--applica")
    p.add_argument("--togli")
    a = p.parse_args()
    if a.catalogo:
        return catalogo()
    if a.elenco:
        for k, g in GUASTI.items():
            print(f"{k}  {g['sigla']:10s} {g['organo']}")
            print(f"   marca: «{g['marca']}»  ·  sano {g['atteso_sano']} → "
                  f"guasto {g['atteso_guasto']}")
        return 0
    for azione, fn in (("verifica", verifica), ("applica", applica), ("togli", togli)):
        v = getattr(a, azione)
        if v:
            if v not in GUASTI:
                print(f"⛔ guasto sconosciuto: {v}.  Ci sono: {', '.join(GUASTI)}")
                return 2
            return fn(v)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
