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
PRODOTTO = os.path.join(QUI, "..", "src", "codificatore.c")

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
    # ═══════════════════════════════════════════════════════════════════════
    # ⭐ C e D SONO DI UNA SPECIE DIVERSA: il guasto sta nel PRODOTTO
    #
    # A e B certificano che il banco sappia diventare rosso quando si rompe LUI.
    # ⛔ Non dicono niente su un'altra domanda, che dal 12 agosto 2026 esiste
    #    perche' il prodotto esiste: **questo banco sa vedere un difetto del
    #    CODIFICATORE?**  Un banco che non l'ha mai visto non lo vede.
    #
    # ⚠ E hanno un passo in piu': dopo l'innesto il prodotto **va ricostruito**,
    #   o si misurerebbe il binario di prima.  ⛔ Il banco non si fida che
    #   qualcuno se lo ricordi: il passo 1 confronta le date e si ferma con
    #   uscita 2 — «non ho potuto guardare» — se il sorgente e' piu' nuovo
    #   dell'attrezzo.  E' la lezione della sera del 12 agosto: *«il prodotto sul
    #   server non era il prodotto che avevamo scritto»*.
    "C": {
        "sigla": "F2.3-C",
        "organo": "i parameter set davanti a OGNI chiave, nel PRODOTTO",
        "titolo": "il prodotto smette di ripetere VPS/SPS/PPS: stanno solo in testa",
        "file": PRODOTTO,
        "appiglio": '"repeat-headers=1:"',
        "sostituto": '"repeat-headers=0:"  /* GUASTO F2.3-C */',
        "comando": ("bash banchi/02-codifica-costruisci.sh && "
                    "CODIFICATORE=prodotto bash banchi/02-codifica-lancia.sh"),
        "dimostra":
            "⛔ E' il difetto che v1 aveva gia' comprato una volta "
            "(`v1/remotix-c/src/codificatore.c:268-272`), ed e' quello che nessun "
            "giro a UN fotogramma puo' vedere: con una chiave sola i parameter "
            "set ci sono per forza.  ⭐ Il passo 6 ne codifica TRE, e li' i gruppi "
            "cadono da 3 a 1.  ⚠ Il sintomo vero, in fase 3, sarebbe «schermo "
            "nero CON i fotogrammi che arrivano» in un client che si collega a "
            "meta' — e non nominerebbe ne' i parameter set ne' il codificatore.  "
            "⭐⭐ E l'innesto ha insegnato una cosa che non era stata prevista: con "
            "`repeat-headers=0` x265 toglie i parameter set **anche dalla PRIMA "
            "chiave** (finirebbero in `extradata`, cioe' fuori dal flusso) — e a "
            "diventare rosso e' la GUARDIA DEL PRODOTTO, non il passo 6: il "
            "fotogramma non parte affatto.  ⇒ Il difetto di v1 oggi non "
            "arriverebbe sul filo.",
        "marca": "chiave senza VPS+SPS+PPS davanti",
        "atteso_sano": 0,
        "atteso_guasto": 1,
        "riferimento": "RCP.md §5.2 · S2-decodifica.md §3.5 · "
                       "v1 src/codificatore.c:268-272 · F2-3-codifica.md §3.2",
    },
    "D": {
        "sigla": "F2.3-D",
        "organo": "i fotogrammi B DECISI e non ereditati",
        "titolo": "il prodotto lascia a x265 il suo `bframes=4`",
        "file": PRODOTTO,
        # ⚠ L'appiglio NON e' `bframes=0`, ed e' la seconda cosa che l'innesto
        #   ha insegnato: le opzioni di x265 si applicano in ORDINE, e l'ultima
        #   vince.  Scrivendo `bframes=4` nel primo punto, il `rc-lookahead=0`
        #   che viene dopo restava in vigore e x265 **si rifiutava di aprirsi**
        #   — cioe' il guasto non innestava l'organo che doveva innestare.
        "appiglio": '"rc-lookahead=0:frame-threads=1:"',
        "sostituto": '"rc-lookahead=20:frame-threads=1:bframes=4:"  /* GUASTO F2.3-D */',
        "comando": ("bash banchi/02-codifica-costruisci.sh && "
                    "CODIFICATORE=prodotto bash banchi/02-codifica-lancia.sh"),
        "dimostra":
            "⛔ x265 fa `bframes=4` **di suo**, e nessuno glielo ha chiesto: ogni "
            "fotogramma B costringe ad attendere il successivo, cioe' un "
            "fotogramma di RITARDO in piu' contro i 50 ms di `SPECIFICHE.md` "
            "§3.2.  ⚠ E' E2 **al contrario**: non un ripiego non dichiarato, ma "
            "un DEFAULT non dichiarato — e non si vede in nessun pixel.  ⭐ Lo "
            "vede il passo 3b, leggendo la confessione che x265 scrive nel "
            "flusso: `bframes=4` invece di 0.  ⚠ E l'innesto porta con se' "
            "`rc-lookahead=20`, perche' `[M]` x265 **non si apre** con "
            "`rc-lookahead=0` e `bframes=4` insieme (*«Lookahead depth must be "
            "greater than the max consecutive bframe count»*): le due manopole "
            "della bassa latenza sono legate, e va saputo prima di toccarne una.",
        "marca": "non ereditati: 4 ⛔ ATTESO 0",
        "atteso_sano": 0,
        "atteso_guasto": 1,
        "riferimento": "SPECIFICHE.md §3.2 · CODER.md §1-bis, §3.9 · "
                       "REVIEWER.md §2 E2 · v1 src/codificatore.c:241",
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
        print(f"│  comando          {g.get('comando', 'bash banchi/02-codifica-lancia.sh')}")
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
