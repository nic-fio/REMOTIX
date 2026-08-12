#!/usr/bin/env python3
"""02-codifica-obu.py — la FORMA del flusso AV1, letta sui byte.

    python3 02-codifica-obu.py --elenca   <file.obu>
    python3 02-codifica-obu.py --verifica <file.obu> [--chiavi-attese N]
    python3 02-codifica-obu.py --storpia  <file.obu> <modo> <uscita>
                               modi: senza-sequenza | byte-girato | troncato

===========================================================================
⛔ PERCHE' ESISTE — il secondo codec e' una DECISIONE DELL'UTENTE, non un di piu'

`DECISIONI.md` §1.13, 12 agosto 2026: HEVC **con un ripiego negoziato**.  Il
ripiego e' **AV1**, e la ragione e' un numero — `[M]` F2.5, quattro caselle su
quattro (Chrome e Firefox, con GPU e senza), a 8 **e** a 10 bit, ⛔ e **con
`prefer-software`**, mentre HEVC ne riempie una sola.

⇒ Un banco che misurasse solo HEVC misurerebbe **il codec che su tre dispositivi
  su quattro non arriva al pixel**.  Questo file e' il gemello di
  `02-codifica-nal.py` per l'altro codec.

===========================================================================
⛔ CHE COSA CAMBIA RISPETTO AD ANNEX-B, E CHE COSA NO

**Cambia la forma**: niente codici di inizio, niente VPS/SPS/PPS.  Un flusso AV1
e' una successione di **OBU**, ciascuno con la propria taglia, raggruppati in
unita' temporali.  ⭐ E non c'e' nessun `hvcC` da cui difendersi: AV1 prende le
unita' temporali cosi' come sono — *«una cucitura in meno»* (`DECISIONI.md`
§1.13).

**Non cambia la meta' che si dimentica**: la **sequence header OBU** deve stare
davanti a **ogni** fotogramma chiave, esattamente come i parameter set davanti a
ogni IDR.  Se sta solo in testa al flusso, un client che si collega dopo riceve
una chiave nuda e il sintomo e' schermo nero **con i fotogrammi che arrivano**.

===========================================================================
⚠ E UNA COSA CHE AV1 NON HA, E VA SAPUTA PRIMA

⛔ **SVT-AV1 non scrive nessuna confessione nel flusso.**  x265 ci mette un
PREFIX_SEI di user data con la versione, `bitdepth=`, `annexb`, `bframes=` — ed
e' il **secondo testimone** su cui `F2-3-codifica.md` §3.4 fonda la verifica di
E2.  `[M]` 12 agosto 2026: in un flusso di libsvtav1 quella stringa **non c'e'**.

⇒ Su AV1 i testimoni indipendenti sarebbero **uno solo** (`ffprobe`), se il
  prodotto non leggesse la **sequence header OBU da se'** — che e' quel che fa
  `src/codificatore.c` (`leggi_sequenza_av1`).  ⭐ Quel lettore non e' un lusso:
  su AV1 e' l'unico secondo testimone che esista, e non costa un byte sul filo.
"""

import argparse
import json
import os
import sys

OBU_SEQUENCE_HEADER = 1
OBU_TEMPORAL_DELIMITER = 2
OBU_FRAME_HEADER = 3
OBU_TILE_GROUP = 4
OBU_METADATA = 5
OBU_FRAME = 6
OBU_REDUNDANT_FRAME_HEADER = 7
OBU_PADDING = 15

NOMI = {
    1: "SEQUENCE_HEADER", 2: "TEMPORAL_DELIMITER", 3: "FRAME_HEADER",
    4: "TILE_GROUP", 5: "METADATA", 6: "FRAME", 7: "REDUNDANT_FRAME_HEADER",
    15: "PADDING",
}


def leb128(dati, i):
    v = 0
    for k in range(8):
        if i >= len(dati):
            return v, i
        b = dati[i]
        i += 1
        v |= (b & 0x7F) << (7 * k)
        if not (b & 0x80):
            break
    return v, i


def elenca(percorso):
    """⛔ Si cammina sugli OBU con la LORO taglia, non a occhio.

    Un lettore che cercasse un motivo di byte (come i codici di inizio di
    Annex-B) troverebbe riscontri **dentro i dati entropici**, e direbbe di aver
    visto OBU che non esistono.  Il campo `obu_has_size_field` esiste apposta, e
    un flusso che non ce l'ha si dichiara invece di indovinarlo.
    """
    dati = open(percorso, "rb").read()
    if not dati:
        raise SystemExit(f"⛔ {percorso} e' vuoto: zero byte non e' un flusso")
    obu = []
    i = 0
    while i < len(dati):
        inizio = i
        testa = dati[i]
        i += 1
        if testa & 0x80:
            raise SystemExit(f"⛔ obu_forbidden_bit a 1 all'offset {inizio}: "
                             f"non e' un flusso AV1 (o non comincia da un OBU)")
        tipo = (testa >> 3) & 0xF
        estensione = (testa >> 2) & 1
        ha_taglia = (testa >> 1) & 1
        if estensione:
            i += 1
        if ha_taglia:
            taglia, i = leb128(dati, i)
        else:
            taglia = len(dati) - i
        if i + taglia > len(dati):
            taglia = len(dati) - i
        carico = dati[i:i + taglia]

        voce = {"offset": inizio, "tipo": tipo, "nome": NOMI.get(tipo, f"tipo{tipo}"),
                "byte": taglia, "ha_taglia": bool(ha_taglia)}
        if tipo in (OBU_FRAME, OBU_FRAME_HEADER) and carico:
            primo = carico[0]
            mostra_esistente = (primo >> 7) & 1
            if mostra_esistente:
                voce["chiave"] = False
            else:
                voce["chiave"] = ((primo >> 5) & 3) == 0  # frame_type 0 = KEY_FRAME
        obu.append(voce)
        i += taglia
        if i <= inizio:
            break
    return {"file": os.path.basename(percorso), "byte_totali": len(dati), "obu": obu}


def verifica(percorso, chiavi_attese):
    e = elenca(percorso)
    obu = e["obu"]
    guasti = []

    if not obu:
        guasti.append("⛔ nessun OBU trovato: non e' un flusso AV1")

    tipi = [o["tipo"] for o in obu]
    if OBU_SEQUENCE_HEADER not in tipi:
        guasti.append("⛔ nessuna SEQUENCE_HEADER: il flusso non porta con se' quel "
                      "che serve a configurare il decodificatore")

    # ⛔ Il primo fotogramma dev'essere una CHIAVE (RCP.md §5.2, e `VideoDecoder`
    #    dopo `configure()` pretende un chunk `key` o solleva DataError).
    fotogrammi = [o for o in obu if o["tipo"] in (OBU_FRAME, OBU_FRAME_HEADER)]
    if not fotogrammi:
        guasti.append("⛔ nessun fotogramma: il flusso non porta pixel")
    elif not fotogrammi[0].get("chiave"):
        guasti.append("⛔ il PRIMO fotogramma non e' una chiave")

    # ⛔ E la meta' che si dimentica: la sequenza davanti a OGNI chiave.
    gruppi = 0
    sequenza_vista = False
    for o in obu:
        if o["tipo"] == OBU_SEQUENCE_HEADER:
            sequenza_vista = True
        elif o["tipo"] in (OBU_FRAME, OBU_FRAME_HEADER):
            if o.get("chiave") and sequenza_vista:
                gruppi += 1
            sequenza_vista = False
    if gruppi < chiavi_attese:
        guasti.append(f"⛔ la SEQUENCE_HEADER precede {gruppi} chiavi e ne doveva "
                      f"precedere {chiavi_attese}: un client che si collega dopo "
                      f"riceverebbe una chiave nuda")

    esito = {
        "file": e["file"], "byte_totali": e["byte_totali"], "obu_totali": len(obu),
        "sequenza": [o["nome"] for o in obu[:12]],
        "sequenze_prima_di_una_chiave": gruppi,
        "chiavi_attese": chiavi_attese,
        "primo_fotogramma_e_chiave": bool(fotogrammi) and bool(fotogrammi[0].get("chiave")),
        "va_bene": not guasti,
        "guasti": guasti,
    }
    print(json.dumps(esito, ensure_ascii=False, indent=2))
    return 0 if not guasti else 1


def storpia(percorso, modo, uscita):
    """⛔ UN BANCO CHE NON HA MAI VISTO UN RIFIUTO NON SA VEDERLO.

    I tre modi sono i gemelli esatti di quelli di `02-codifica-nal.py`, e il
    primo e' il piu' importante: `senza-sequenza` e' cosa succederebbe se un
    giorno qualcuno accendesse `GLOBAL_HEADER` anche su AV1, cioe' il difetto
    che D1 esiste per non fare.

    ⚠ E il punto in cui si gira il byte NON e' un dettaglio: `[M]` 12 agosto
      2026 su HEVC, girare il byte 24 di un NAL cadeva ancora nell'INTESTAZIONE
      dello slice e il fotogramma decodificato tornava **identico bit per bit**.
      Qui si entra al 2 % del corpo del primo fotogramma, per la stessa ragione.
    """
    dati = bytearray(open(percorso, "rb").read())
    e = elenca(percorso)
    obu = e["obu"]
    if not obu:
        raise SystemExit("⛔ non si storpia un flusso che non si e' saputo leggere")

    if modo == "senza-sequenza":
        fuori = bytearray()
        for k, o in enumerate(obu):
            if o["tipo"] == OBU_SEQUENCE_HEADER:
                continue
            fine = obu[k + 1]["offset"] if k + 1 < len(obu) else len(dati)
            fuori += dati[o["offset"]:fine]
        nota = "SEQUENCE_HEADER tolta, i fotogrammi lasciati"
    elif modo == "byte-girato":
        primo = next((o for o in obu if o["tipo"] in (OBU_FRAME, OBU_TILE_GROUP)), None)
        if primo is None:
            raise SystemExit("⛔ nessun fotogramma da storpiare")
        corpo = primo["offset"] + (primo["byte"] // 50)
        dove = min(corpo + 64, primo["offset"] + primo["byte"] - 1)
        dati[dove] ^= 0xFF
        fuori = dati
        nota = f"un byte invertito all'offset {dove}, dentro il corpo del primo fotogramma"
    elif modo == "troncato":
        taglio = int(len(dati) * 0.60)
        fuori = dati[:taglio]
        nota = f"tagliato a {taglio} byte su {len(dati)} (60 %)"
    else:
        raise SystemExit(f"⛔ modo sconosciuto: {modo}")

    with open(uscita, "wb") as f:
        f.write(bytes(fuori))
    print(json.dumps({"modo": modo, "nota": nota, "uscita": uscita,
                      "byte": len(fuori)}, ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--elenca")
    p.add_argument("--verifica")
    p.add_argument("--chiavi-attese", type=int, default=1)
    p.add_argument("--storpia", nargs=3, metavar=("FILE", "MODO", "USCITA"))
    a = p.parse_args()
    if a.elenca:
        print(json.dumps(elenca(a.elenca), ensure_ascii=False, indent=2))
        return 0
    if a.verifica:
        return verifica(a.verifica, a.chiavi_attese)
    if a.storpia:
        return storpia(*a.storpia)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
