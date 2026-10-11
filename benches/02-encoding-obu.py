#!/usr/bin/env python3
"""02-encoding-obu.py — the SHAPE of the AV1 stream, read on the bytes.

    python3 02-encoding-obu.py --dump   <file.obu>
    python3 02-encoding-obu.py --verify <file.obu> [--expected-keys N]
    python3 02-encoding-obu.py --mangle  <file.obu> <modo> <uscita>
                               modes: senza-sequenza | byte-girato | troncato

===========================================================================
⛔ WHY IT EXISTS — the second codec is a DECISION OF THE USER, not an extra

`DECISIONS.md` §1.13, 12 Aug 2026: HEVC **with a negotiated fallback**.  The
fallback is **AV1**, and the reason is a number — `[M]` F2.5, four cells out of
four (Chrome and Firefox, with GPU and without), at 8 **and** at 10 bits, ⛔ and **with
`prefer-software`**, while HEVC fills only one.

⇒ A bench that measured only HEVC would measure **the codec that on three devices
  out of four does not reach the pixel**.  This file is the twin of
  `02-encoding-nal.py` for the other codec.

===========================================================================
⛔ WHAT CHANGES COMPARED TO ANNEX-B, AND WHAT DOES NOT

**The shape changes**: no start codes, no VPS/SPS/PPS.  An AV1 stream
is a succession of **OBUs**, each with its own size, grouped in
temporal units.  ⭐ And there is no `hvcC` to defend against: AV1 takes the
temporal units as they are — *«one seam fewer»* (`DECISIONS.md`
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
  `src/encoder.c` does (`read_av1_sequence`).  ⭐ That reader is not a luxury:
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

NAMES = {
    1: "SEQUENCE_HEADER", 2: "TEMPORAL_DELIMITER", 3: "FRAME_HEADER",
    4: "TILE_GROUP", 5: "METADATA", 6: "FRAME", 7: "REDUNDANT_FRAME_HEADER",
    15: "PADDING",
}


def leb128(data, i):
    v = 0
    for k in range(8):
        if i >= len(data):
            return v, i
        b = data[i]
        i += 1
        v |= (b & 0x7F) << (7 * k)
        if not (b & 0x80):
            break
    return v, i


def dump(fpath):
    """⛔ It walks over the OBUs with THEIR size, not by eye.

    A reader that looked for a byte pattern (like the start codes of
    Annex-B) would find matches **inside the entropy data**, and would say it had
    seen OBUs that do not exist.  The `obu_has_size_field` field exists on purpose, and
    a stream that does not have it is declared instead of guessed.
    """
    data = open(fpath, "rb").read()
    if not data:
        raise SystemExit(f"⛔ {fpath} is empty: zero bytes is not a stream")
    obu = []
    i = 0
    while i < len(data):
        start = i
        head = data[i]
        i += 1
        if head & 0x80:
            raise SystemExit(f"⛔ obu_forbidden_bit at 1 at offset {start}: "
                             f"it is not an AV1 stream (or it does not start from an OBU)")
        kind = (head >> 3) & 0xF
        extension = (head >> 2) & 1
        has_size = (head >> 1) & 1
        if extension:
            i += 1
        if has_size:
            trim, i = leb128(data, i)
        else:
            trim = len(data) - i
        if i + trim > len(data):
            trim = len(data) - i
        load = data[i:i + trim]

        entry = {"offset": start, "type": kind, "name": NAMES.get(kind, f"kind{kind}"),
                "byte": trim, "has_size": bool(has_size)}
        if kind in (OBU_FRAME, OBU_FRAME_HEADER) and load:
            first = load[0]
            show_existing = (first >> 7) & 1
            if show_existing:
                entry["key"] = False
            else:
                entry["key"] = ((first >> 5) & 3) == 0  # frame_type 0 = KEY_FRAME
        obu.append(entry)
        i += trim
        if i <= start:
            break
    return {"file": os.path.basename(fpath), "byte_totali": len(data), "obu": obu}


def verify(fpath, expected_keys):
    e = dump(fpath)
    obu = e["obu"]
    faults = []

    if not obu:
        faults.append("⛔ no OBU found: it is not an AV1 stream")

    types = [o["type"] for o in obu]
    if OBU_SEQUENCE_HEADER not in types:
        faults.append("⛔ no SEQUENCE_HEADER: the stream does not carry with it what "
                      "is needed to configure the decoder")

    # ⛔ The first frame must be a KEYFRAME (RCP.md §5.2, and `VideoDecoder`
    #    after `configure()` requires a `key` chunk or raises DataError).
    frames = [o for o in obu if o["type"] in (OBU_FRAME, OBU_FRAME_HEADER)]
    if not frames:
        faults.append("⛔ no frame: the stream carries no pixels")
    elif not frames[0].get("key"):
        faults.append("⛔ the FIRST frame is not a keyframe")

    # ⛔ And the half that gets forgotten: the sequence in front of EVERY keyframe.
    groups = 0
    sequence_seen = False
    for o in obu:
        if o["type"] == OBU_SEQUENCE_HEADER:
            sequence_seen = True
        elif o["type"] in (OBU_FRAME, OBU_FRAME_HEADER):
            if o.get("key") and sequence_seen:
                groups += 1
            sequence_seen = False
    if groups < expected_keys:
        faults.append(f"⛔ the SEQUENCE_HEADER precedes {groups} keyframes and should have "
                      f"preceded {expected_keys}: a client connecting later "
                      f"would receive a naked keyframe")

    outcome = {
        "file": e["file"], "byte_totali": e["byte_totali"], "obu_totali": len(obu),
        "sequenza": [o["name"] for o in obu[:12]],
        "sequenze_prima_di_una_chiave": groups,
        "expected_keys": expected_keys,
        "primo_fotogramma_e_chiave": bool(frames) and bool(frames[0].get("key")),
        "va_bene": not faults,
        "faults": faults,
    }
    print(json.dumps(outcome, ensure_ascii=False, indent=2))
    return 0 if not faults else 1


def mangle(fpath, mode, out_path):
    """⛔ A BENCH THAT HAS NEVER SEEN A REFUSAL CANNOT SEE ONE.

    The three modes are the exact twins of those of `02-encoding-nal.py`, and the
    first is the most important: `senza-sequenza` is what would happen if one
    day someone switched on `GLOBAL_HEADER` on AV1 too, that is the defect
    D1 exists not to make.

    ⚠ And the point where the byte is flipped is NOT a detail: `[M]` 12 Aug
      2026 on HEVC, flipping byte 24 of a NAL still fell into the slice HEADER
      and the decoded frame came back **identical bit for bit**.
      Here it goes in at 2 % of the body of the first frame, for the same reason.
    """
    data = bytearray(open(fpath, "rb").read())
    e = dump(fpath)
    obu = e["obu"]
    if not obu:
        raise SystemExit("⛔ a stream that could not be read is not mangled")

    if mode == "senza-sequenza":
        report = bytearray()
        for k, o in enumerate(obu):
            if o["type"] == OBU_SEQUENCE_HEADER:
                continue
            fine = obu[k + 1]["offset"] if k + 1 < len(obu) else len(data)
            report += data[o["offset"]:fine]
        note = "SEQUENCE_HEADER removed, frames left"
    elif mode == "byte-girato":
        first = next((o for o in obu if o["type"] in (OBU_FRAME, OBU_TILE_GROUP)), None)
        if first is None:
            raise SystemExit("⛔ no frame to mangle")
        body = first["offset"] + (first["byte"] // 50)
        dove = min(body + 64, first["offset"] + first["byte"] - 1)
        data[dove] ^= 0xFF
        report = data
        note = f"one byte inverted at offset {dove}, inside the body of the first frame"
    elif mode == "troncato":
        cut = int(len(data) * 0.60)
        report = data[:cut]
        note = f"cut at {cut} bytes out of {len(data)} (60 %)"
    else:
        raise SystemExit(f"⛔ unknown mode: {mode}")

    with open(out_path, "wb") as f:
        f.write(bytes(report))
    print(json.dumps({"mode": mode, "note": note, "exit": out_path,
                      "byte": len(report)}, ensure_ascii=False))
    return 0


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--dump")
    p.add_argument("--verify")
    p.add_argument("--expected-keys", type=int, default=1)
    p.add_argument("--mangle", nargs=3, metavar=("FILE", "MODE", "OUTPUT"))
    a = p.parse_args()
    if a.dump:
        print(json.dumps(dump(a.dump), ensure_ascii=False, indent=2))
        return 0
    if a.verify:
        return verify(a.verify, a.expected_keys)
    if a.mangle:
        return mangle(*a.mangle)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
