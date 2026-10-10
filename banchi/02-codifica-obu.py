#!/usr/bin/env python3
"""02-codifica-obu.py — the SHAPE of the AV1 stream, read on the bytes.

    python3 02-codifica-obu.py --elenca   <file.obu>
    python3 02-codifica-obu.py --verifica <file.obu> [--chiavi-attese N]
    python3 02-codifica-obu.py --storpia  <file.obu> <modo> <uscita>
                               modes: senza-sequenza | byte-girato | troncato

===========================================================================
⛔ WHY IT EXISTS — the second codec is a DECISION OF THE USER, not an extra

`DECISIONI.md` §1.13, 12 Aug 2026: HEVC **with a negotiated fallback**.  The
fallback is **AV1**, and the reason is a number — `[M]` F2.5, four cells out of
four (Chrome and Firefox, with GPU and without), at 8 **and** at 10 bits, ⛔ and **with
`prefer-software`**, while HEVC fills only one.

⇒ A bench that measured only HEVC would measure **the codec that on three devices
  out of four does not reach the pixel**.  This file is the twin of
  `02-codifica-nal.py` for the other codec.

===========================================================================
⛔ WHAT CHANGES COMPARED TO ANNEX-B, AND WHAT DOES NOT

**The shape changes**: no start codes, no VPS/SPS/PPS.  An AV1 stream
is a succession of **OBUs**, each with its own size, grouped in
temporal units.  ⭐ And there is no `hvcC` to defend against: AV1 takes the
temporal units as they are — *«one seam fewer»* (`DECISIONI.md`
§1.13).

**The half that gets forgotten does not change**: the **sequence header OBU** must sit
in front of **every** keyframe, exactly like the parameter sets in front of
every IDR.  If it sits only at the head of the stream, a client that connects later receives
a naked keyframe and the symptom is a black screen **with the frames arriving**.

===========================================================================
⚠ AND SOMETHING AV1 DOES NOT HAVE, AND IT MUST BE KNOWN BEFOREHAND

⛔ **SVT-AV1 writes no confession in the stream.**  x265 puts a
user-data PREFIX_SEI there with the version, `bitdepth=`, `annexb`, `bframes=` — and
it is the **second witness** on which `F2-3-codifica.md` §3.4 bases the check of
E2.  `[M]` 12 Aug 2026: in a libsvtav1 stream that string **is not there**.

⇒ On AV1 the independent witnesses would be **only one** (`ffprobe`), if the
  product did not read the **sequence header OBU by itself** — which is what
  `src/codificatore.c` does (`leggi_sequenza_av1`).  ⭐ That reader is not a luxury:
  on AV1 it is the only second witness there is, and it does not cost a byte on the wire.
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
    """⛔ It walks over the OBUs with THEIR size, not by eye.

    A reader that looked for a byte pattern (like the start codes of
    Annex-B) would find matches **inside the entropy data**, and would say it had
    seen OBUs that do not exist.  The `obu_has_size_field` field exists on purpose, and
    a stream that does not have it is declared instead of guessed.
    """
    dati = open(percorso, "rb").read()
    if not dati:
        raise SystemExit(f"⛔ {percorso} is empty: zero bytes is not a stream")
    obu = []
    i = 0
    while i < len(dati):
        inizio = i
        testa = dati[i]
        i += 1
        if testa & 0x80:
            raise SystemExit(f"⛔ obu_forbidden_bit at 1 at offset {inizio}: "
                             f"it is not an AV1 stream (or it does not start from an OBU)")
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
        guasti.append("⛔ no OBU found: it is not an AV1 stream")

    tipi = [o["tipo"] for o in obu]
    if OBU_SEQUENCE_HEADER not in tipi:
        guasti.append("⛔ no SEQUENCE_HEADER: the stream does not carry with it what "
                      "is needed to configure the decoder")

    # ⛔ The first frame must be a KEYFRAME (RCP.md §5.2, and `VideoDecoder`
    #    after `configure()` requires a `key` chunk or raises DataError).
    fotogrammi = [o for o in obu if o["tipo"] in (OBU_FRAME, OBU_FRAME_HEADER)]
    if not fotogrammi:
        guasti.append("⛔ no frame: the stream carries no pixels")
    elif not fotogrammi[0].get("chiave"):
        guasti.append("⛔ the FIRST frame is not a keyframe")

    # ⛔ And the half that gets forgotten: the sequence in front of EVERY keyframe.
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
        guasti.append(f"⛔ the SEQUENCE_HEADER precedes {gruppi} keyframes and should have "
                      f"preceded {chiavi_attese}: a client connecting later "
                      f"would receive a naked keyframe")

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
    """⛔ A BENCH THAT HAS NEVER SEEN A REFUSAL CANNOT SEE ONE.

    The three modes are the exact twins of those of `02-codifica-nal.py`, and the
    first is the most important: `senza-sequenza` is what would happen if one
    day someone switched on `GLOBAL_HEADER` on AV1 too, that is the defect
    D1 exists not to make.

    ⚠ And the point where the byte is flipped is NOT a detail: `[M]` 12 Aug
      2026 on HEVC, flipping byte 24 of a NAL still fell into the slice HEADER
      and the decoded frame came back **identical bit for bit**.
      Here it goes in at 2 % of the body of the first frame, for the same reason.
    """
    dati = bytearray(open(percorso, "rb").read())
    e = elenca(percorso)
    obu = e["obu"]
    if not obu:
        raise SystemExit("⛔ a stream that could not be read is not mangled")

    if modo == "senza-sequenza":
        fuori = bytearray()
        for k, o in enumerate(obu):
            if o["tipo"] == OBU_SEQUENCE_HEADER:
                continue
            fine = obu[k + 1]["offset"] if k + 1 < len(obu) else len(dati)
            fuori += dati[o["offset"]:fine]
        nota = "SEQUENCE_HEADER removed, frames left"
    elif modo == "byte-girato":
        primo = next((o for o in obu if o["tipo"] in (OBU_FRAME, OBU_TILE_GROUP)), None)
        if primo is None:
            raise SystemExit("⛔ no frame to mangle")
        corpo = primo["offset"] + (primo["byte"] // 50)
        dove = min(corpo + 64, primo["offset"] + primo["byte"] - 1)
        dati[dove] ^= 0xFF
        fuori = dati
        nota = f"one byte inverted at offset {dove}, inside the body of the first frame"
    elif modo == "troncato":
        taglio = int(len(dati) * 0.60)
        fuori = dati[:taglio]
        nota = f"cut at {taglio} bytes out of {len(dati)} (60 %)"
    else:
        raise SystemExit(f"⛔ unknown mode: {modo}")

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
