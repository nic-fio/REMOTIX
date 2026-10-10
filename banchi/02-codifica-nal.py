#!/usr/bin/env python3
"""02-codifica-nal.py — the SHAPE of the HEVC stream, read on the bytes.

    python3 02-codifica-nal.py --elenca   <file.hevc>
    python3 02-codifica-nal.py --verifica <file.hevc> [--idr-attesi N]
    python3 02-codifica-nal.py --storpia  <file.hevc> <modo> <uscita>
                               modes: senza-parametri | byte-girato | troncato

===========================================================================
⛔ WHY IT EXISTS — the shape of the stream is a DECISION, not a detail

The browser's `VideoDecoder` accepts **two alternative and exclusive formats**, and
they are not interchangeable (`web/rapporti/S2-decodifica.md` §3.5, `[S]` from the
W3C HEVC registration):

  **hevc**   — with a `description` (an `HEVCDecoderConfigurationRecord`,
               the `hvcC`), and the NALs preceded by a **length** prefix;
  **annexb** — without `description`, and the NALs separated by **start codes**
               `00 00 01`.  Here the `key` chunk must carry **also all the
               parameter sets** needed to decode it.

⭐ **F2.3 chooses Annex-B without `description`.**  The reasons are in the
report (`fasi/rapporti/F2-3-codifica.md` §3); what concerns this file is
the **verifiable consequence**: if Annex-B is sent, then the first chunk
must contain, in this order and before any picture data,
**VPS (32), SPS (33), PPS (34)** and then an **IDR (19 or 20)** picture.

⛔ And this is checked on the BYTES, not on the label we put on it.
Chromium does exactly the same thing and does not trust our label:
`video_decoder.cc:206-214` calls `media::mp4::HEVC::AnalyzeAnnexB()` after every
`configure()`/`flush()`, and if the chunk marked `key` does not contain an IDR with its
parameter sets it **refuses**, with a message that names our exact
possible error: *«A key frame is required after configure() or flush(). If
you're using HEVC formatted H.265 you must fill out the description field»*
(`S2-decodifica.md` §3.6, `[R]`).

⇒ ⭐ This file is **the piece of Chromium we can run at home**.
   If we get the shape wrong, it finds out here instead of in phase 2.5, where the symptom
   would be «the page stays black» and the search would start from the wrong place.

===========================================================================
⛔ AND THE HALF THAT GETS FORGOTTEN: THE PARAMETER SETS IN FRONT OF **EVERY** IDR

A single frame has them necessarily.  The trouble comes when the IDRs are many
(phase 3) and the parameter sets sit **only** at the head of the stream: a client that
connects later, or restarts from a `flush()`, receives a **naked** IDR and decodes
nothing.  The symptom is a black screen **with the frames
arriving** — the same symptom v1's `codificatore.c` had already paid for
once, and that is why v1 forbids `AV_CODEC_FLAG_GLOBAL_HEADER` with a comment
at `src/codificatore.c:268-272`.

⇒ `--verifica --idr-attesi N` requires **N VPS+SPS+PPS groups**, not one.

===========================================================================
⛔ AND `--storpia`: A BENCH THAT HAS NEVER SEEN A REFUSAL CANNOT SEE ONE

`REVIEWER.md` §1 point 5 and `CODER.md` §3.10.  A round in which everything passes does not
prove that the bench can reject: it only proves that it did not reject.  The
three modes below are the three ways a stream can be broken **without
ceasing to look like a stream**:

  `senza-parametri` — VPS/SPS/PPS removed, the IDR left.  ⭐ It is the mode that
      corresponds to the real error we are trying not to make: it is what
      happens if one day someone switched on `GLOBAL_HEADER`.  The
      independent decoder **must** produce **zero** frames;
  `byte-girato` — one byte of the first slice inverted.  The decoder must
      **protest**, or deliver pixels different from the source;
  `troncato` — the stream cut at 60 %.  Fewer frames, or an error.

⚠ None of the three breaks the syntax of the start codes: if it did, it
  would be proving that ffmpeg can recognise a file that is not a file, which
  is not the same thing and serves nobody.
"""

import argparse
import json
import os
import sys

# The NAL types we care about (H.265, ISO/IEC 23008-2 table 7-1).
NOMI = {
    19: "IDR_W_RADL", 20: "IDR_N_LP", 21: "CRA_NUT",
    32: "VPS", 33: "SPS", 34: "PPS", 35: "AUD", 36: "EOS", 37: "EOB",
    38: "FD", 39: "PREFIX_SEI", 40: "SUFFIX_SEI",
    0: "TRAIL_N", 1: "TRAIL_R",
}
PARAMETRI = (32, 33, 34)
IDR = (19, 20)
VCL_MASSIMO = 31          # types 0..31 are picture data (VCL)


def trova_inizi(dati):
    """The offsets of the Annex-B start codes, and their length (3 or 4).

    ⛔ `00 00 01` is told from `00 00 00 01`: both are legal, and a
       parser that knew only one would skip half the NALs **without
       complaining** — that is it would say «this stream has no PPS» of a stream
       that has it.  A false red costs as much as a false green.
    """
    inizi = []
    i, n = 0, len(dati)
    while i + 2 < n:
        if dati[i] == 0 and dati[i + 1] == 0 and dati[i + 2] == 1:
            if i >= 1 and dati[i - 1] == 0:
                inizi.append((i - 1, 4))   # 00 00 00 01
            else:
                inizi.append((i, 3))       # 00 00 01
            i += 3
        else:
            i += 1
    return inizi


def elenca(percorso):
    dati = open(percorso, "rb").read()
    if not dati:
        raise SystemExit(f"⛔ {percorso} is empty: zero bytes is not a stream")
    inizi = trova_inizi(dati)
    nal = []
    for k, (off, lungo) in enumerate(inizi):
        corpo = off + lungo
        fine = inizi[k + 1][0] if k + 1 < len(inizi) else len(dati)
        if corpo >= len(dati):
            continue
        tipo = (dati[corpo] >> 1) & 0x3F
        nal.append({"indice": k, "offset": off, "prefisso": lungo,
                    "tipo": tipo, "nome": NOMI.get(tipo, f"tipo{tipo}"),
                    "byte": fine - corpo})
    return {"file": os.path.basename(percorso), "byte_totali": len(dati),
            "nal": nal}


def verifica(percorso, idr_attesi):
    """⛔ The required shape, and every requirement says WHY."""
    e = elenca(percorso)
    nal = e["nal"]
    tipi = [n["tipo"] for n in nal]
    guasti = []

    if not nal:
        guasti.append("⛔ no NAL found: it is not an Annex-B stream")

    # 1 — the first NAL that is not a delimiter must be the VPS
    utili = [t for t in tipi if t not in (35, 38)]      # without AUD and filler
    if not utili or utili[0] != 32:
        guasti.append(f"⛔ the stream does not start with the VPS (32): it starts with {utili[:4]}")

    # 2 — before the first picture data there must be VPS, SPS, PPS
    prima = []
    for t in tipi:
        if t <= VCL_MASSIMO:
            break
        prima.append(t)
    for atteso in PARAMETRI:
        if atteso not in prima:
            guasti.append(f"⛔ the {NOMI[atteso]} ({atteso}) is missing BEFORE the first "
                          f"picture data: a `key` chunk in Annex-B must carry "
                          f"all the parameter sets (S2-decodifica.md §3.5)")

    # 3 — the first picture data must be an IDR
    vcl = [t for t in tipi if t <= VCL_MASSIMO]
    if not vcl:
        guasti.append("⛔ no picture data: the stream carries no pixels")
    elif vcl[0] not in IDR:
        guasti.append(f"⛔ the FIRST frame is not a keyframe: "
                      f"the first picture NAL is {NOMI.get(vcl[0], vcl[0])}.  "
                      f"`VideoDecoder` after `configure()` requires a `key` chunk "
                      f"or raises DataError (S2-decodifica.md §3.6)")

    # 4 — the parameter sets repeated in front of EVERY IDR
    gruppi = 0
    visti = set()
    for t in tipi:
        if t in PARAMETRI:
            visti.add(t)
        elif t in IDR:
            if visti >= set(PARAMETRI):
                gruppi += 1
            visti = set()
    if gruppi < idr_attesi:
        guasti.append(f"⛔ the parameter sets precede {gruppi} IDRs and should have "
                      f"preceded {idr_attesi}: a client connecting later "
                      f"would receive a naked IDR (v1 src/codificatore.c:268-272)")

    # 5 — no trace of a length prefix instead of the start code
    if len(dati_len := open(percorso, "rb").read(4)) == 4 and dati_len[:3] not in (
            b"\x00\x00\x00", b"\x00\x00\x01"):
        guasti.append("⛔ the first bytes are not a start code: it looks like a "
                      "length-prefixed stream (`hevc`/hvcC format), not Annex-B")

    esito = {
        "file": e["file"], "byte_totali": e["byte_totali"],
        "nal_totali": len(nal),
        "sequenza": [n["nome"] for n in nal[:12]],
        "gruppi_parametri_prima_di_un_IDR": gruppi,
        "idr_attesi": idr_attesi,
        "primo_fotogramma_e_chiave": bool(vcl) and vcl[0] in IDR,
        "annexb": True,
        "va_bene": not guasti,
        "guasti": guasti,
    }
    print(json.dumps(esito, ensure_ascii=False, indent=2))
    return 0 if not guasti else 1


def confessione(percorso):
    """⭐ WHAT THE ENCODER REALLY DID — asked of IT, not deduced.

    `CODER.md` §3.7: *the sender is not deduced, it is asked.*  §3.9: *when a
    component can decide by itself, tell it what to do — and CHECK THAT IT
    OBEYED.*  It is error form **E2** of `REVIEWER.md` §2, and in an
    encoder it is the household one: *«the encoder that falls back to CPU without
    saying so»*.

    ⭐ Here nothing needs deducing, because **x265 writes its own confession
       inside the stream**: a PREFIX_SEI of type 5 (user data unregistered) with
       the version, the bit depth and the COMPLETE list of the options it
       really used — including those nobody asked for.

    The entries this bench reads, and why:

      `bitdepth=10`     ⛔ the REAL depth it worked with, said by itself.
                           `ffprobe` derives it from the SPS, which is a second
                           witness: two independent witnesses, not one;
      `annexb`          ⭐ the SHAPE of the stream, confirmed by the producer;
      `repeat-headers`  ⛔ the parameter sets in front of every IDR (the half that gets
                           forgotten, and that bites in phase 3, not here);
      `bframes=N`       ⚠ what NOBODY asked for and it does anyway.

    ⚠ And the dependency must be declared: this confession exists because x265 has
      `info=1` on by default.  ⛔ The bench keeps it on **on purpose** — it is
      its tool.  If one day the product switched it off to save
      bytes, this check would disappear **silently**: then only
      `ffprobe` would remain, and it must be known beforehand instead of discovered afterwards.
    """
    dati = open(percorso, "rb").read()
    i = dati.find(b"x265 (build")
    if i < 0:
        return {"confessione": False,
                "perche": "no x265 SEI in the stream: either x265 did not make it, "
                          "or `info=0`.  ⛔ Only ffprobe is left as a witness"}
    fine = dati.find(b"\x00", i)
    testo = dati[i:fine if fine > i else i + 4000].decode("ascii", "replace")
    voci = testo.split()
    def dammi(chiave):
        for v in voci:
            if v.startswith(chiave + "="):
                return v.split("=", 1)[1]
        return None
    return {
        "confessione": True,
        "versione": testo.split(" - ")[0],
        "banner_bit": "10bit" if "10bit" in testo.split("options:")[0] else "8bit",
        "bitdepth": dammi("bitdepth"),
        "input_csp": dammi("input-csp"),
        "annexb": " annexb" in testo,
        "repeat_headers": " repeat-headers" in testo,
        "bframes": dammi("bframes"),
        "keyint": dammi("keyint"),
        "lossless": " lossless" in testo,
        "byte_del_sei": (fine - i) if fine > i else None,
    }


def storpia(percorso, modo, uscita):
    dati = bytearray(open(percorso, "rb").read())
    e = elenca(percorso)
    nal = e["nal"]
    if not nal:
        raise SystemExit("⛔ a stream that could not be read is not mangled")

    if modo == "senza-parametri":
        tenuti = bytearray()
        for k, n in enumerate(nal):
            if n["tipo"] in PARAMETRI:
                continue
            fine = nal[k + 1]["offset"] if k + 1 < len(nal) else len(dati)
            tenuti += dati[n["offset"]:fine]
        fuori = tenuti
        nota = "VPS/SPS/PPS removed, picture data left"
    elif modo == "byte-girato":
        primo = next((n for n in nal if n["tipo"] <= VCL_MASSIMO), None)
        if primo is None:
            raise SystemExit("⛔ no picture data to mangle")
        # ⛔ WHERE the byte is flipped is NOT a detail — measured on 12 Aug 2026.
        #
        #    The first draft flipped byte 24 of the NAL.  On a
        #    1920x1080 frame that byte still falls inside the slice HEADER, and
        #    ⛔ **the decoded frame came back IDENTICAL to the source, bit
        #    for bit**, with ffmpeg exiting 0.  The negative control injected
        #    no fault: it is trap no. 2 of `01-b12-guasti.py` — *«the fault
        #    that was not injected leaves the code healthy, the bench stays
        #    green, and whoever reads concludes that the bench does not see the fault»*.
        #
        #    ⭐ Flipping the same byte at **2 % of the body** — that is in the real
        #    entropy data — the differing samples went from **0 to 4,710,663
        #    out of 6,220,800** `[M]`.  ⛔ And ffmpeg exited **0 in both
        #    cases**: the exit status did not tell the two things apart.
        #
        #    ⇒ The NAL header (2 bytes) is skipped and it goes into the body for
        #      2 %, with a floor of 64 bytes for small slices.
        corpo = primo["offset"] + primo["prefisso"] + 2
        dentro = max(64, primo["byte"] // 50)
        dove = min(corpo + dentro, primo["offset"] + primo["prefisso"] + primo["byte"] - 1)
        dati[dove] ^= 0xFF
        fuori = dati
        nota = (f"one byte inverted at offset {dove}, at {100 * dentro / max(1, primo['byte']):.1f} % "
                f"of the body of the first slice ({primo['byte']} bytes long)")
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
    p.add_argument("--confessione")
    p.add_argument("--idr-attesi", type=int, default=1)
    p.add_argument("--storpia", nargs=3, metavar=("FILE", "MODO", "USCITA"))
    a = p.parse_args()
    if a.elenca:
        print(json.dumps(elenca(a.elenca), ensure_ascii=False, indent=2))
        return 0
    if a.confessione:
        c = confessione(a.confessione)
        print(json.dumps(c, ensure_ascii=False))
        return 0 if c.get("confessione") else 1
    if a.verifica:
        return verifica(a.verifica, a.idr_attesi)
    if a.storpia:
        return storpia(*a.storpia)
    p.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
