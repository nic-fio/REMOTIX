#!/usr/bin/env python3
"""
07-b42 — the audio judge: it LISTENS, it does not count blocks.

⛔ `LEZIONI.md` §2.2, first row of the table: «the bench counted frames
   sent and blocks acknowledged; the defect changed **the samples** — the audio
   was full-scale noise».  ⇒ Here we measure the SIGNAL:

     hz        the dominant frequency (Goertzel, 1 Hz step)
     rms       the amplitude
     purezza   how much energy sits in the dominant line — ⭐ it is the only number
               that tells a TONE from NOISE, and it is the one the judge
               of the probe `07-b40` has already certified on six cases

⭐ And on top of that it measures something the probe could not: **the rhythm**.  The
   `istante` of §6.3 are the server's clock, so gaps are counted
   where they were born instead of being deduced from silence.

Reads the JSONL that `01-b3-cliente.py --audio-scrivi` produces.

Usage:  python3 07-b42-giudice.py blocchi.jsonl [--hz 440] [--secondi 3]
"""
import argparse
import base64
import json
import math
import sys

FREQUENZA = 48000
CANALI = 2
BLOCCO_US = {1: 20000, 2: 5000}  # Opus 20 ms, PCM 5 ms (§5.3)


def giudica(campioni):
    """The dominant frequency, the amplitude and the purity.

    ⛔ «Nothing to judge» is an outcome of ITS OWN and not a zero: `CODER.md` §3.10.
    """
    m = len(campioni)
    if m == 0:
        return {"esito": "NIENTE DA GIUDICARE", "campioni": 0}
    rms = math.sqrt(sum(x * x for x in campioni) / m)
    picco, hz, somma = 0.0, 0, 0.0
    for f in range(100, 2001):
        w = 2.0 * math.cos(2.0 * math.pi * f / FREQUENZA)
        s1 = s2 = 0.0
        for x in campioni:
            s1, s2 = w * s1 - s2 + x, s1
        p = max(0.0, s1 * s1 + s2 * s2 - w * s1 * s2)
        somma += p
        if p > picco:
            picco, hz = p, f
    return {"esito": "GIUDICATO", "campioni": m, "hz": hz,
            "rms": round(rms, 4),
            "purezza": round(picco / somma, 4) if somma > 0 else None}


def pcm_campioni(dati):
    """s16 LITTLE-endian, interleaved (§5.3) — the left channel is taken.

    ⛔ Little-endian is the only declared exception to network order, and
       reading it big-endian does NOT give an error: it gives full-scale noise.  It is
       case 2 of the positive control of `07-b40`.
    """
    fuori = []
    for i in range(0, len(dati) - 3, 2 * CANALI):
        v = int.from_bytes(dati[i:i + 2], "little", signed=True)
        fuori.append(v / 32768.0)
    return fuori


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--hz", type=int, default=440, help="the expected tone")
    p.add_argument("--tolleranza-hz", type=int, default=2)
    p.add_argument("--purezza-minima", type=float, default=0.80)
    p.add_argument("--secondi", type=float, default=0,
                   help="how many wall-clock seconds the capture lasted: without it, "
                        "the rhythm is not judged (and it SAYS it is not judged)")
    a = p.parse_args()

    blocchi = []
    with open(a.file) as f:
        for riga in f:
            riga = riga.strip()
            if riga:
                blocchi.append(json.loads(riga))

    if not blocchi:
        print("⛔ NOTHING TO JUDGE: the file has no blocks.")
        print("   ⚠ And it is not «the audio does not arrive»: it is «I have nothing")
        print("     to look at».  The two cases have two different outcomes on purpose.")
        return 2

    codec = blocchi[0]["codec"]
    if any(b["codec"] != codec for b in blocchi):
        print("⛔ the codec CHANGES mid-capture: §4.3 negotiates it only once.")
        return 1

    # ── the RHYTHM, from the server's `istante` ─────────────────────────────
    atteso_us = BLOCCO_US.get(codec)
    istanti = [b["istante"] for b in blocchi]
    salti, passi = [], []
    for i in range(1, len(istanti)):
        d = istanti[i] - istanti[i - 1]
        passi.append(d)
        if atteso_us and d != atteso_us:
            salti.append((i, d))
    durata_s = (istanti[-1] - istanti[0] + (atteso_us or 0)) / 1e6

    # ── the CONTENT ─────────────────────────────────────────────────────────
    if codec == 2:
        campioni = []
        for b in blocchi:
            campioni.extend(pcm_campioni(base64.b64decode(b["byte"])))
        # ⚠ 100 ms of start-up discarded: `CODER.md` §3.5, «a sample taken
        #   at startup says nothing about steady state».
        salta = min(4800, len(campioni) // 4)
        g = giudica(campioni[salta:])
    else:
        g = {"esito": "NON GIUDICABILE QUI",
             "perche": "Opus packets are judged by the BROWSER, which has the "
                       "decoder: here they would be judged with a different one "
                       "from the user's (error form E10)"}

    print(f"== 07-b42 · {len(blocchi)} blocks · codec {codec} "
          f"({'Opus' if codec == 1 else 'PCM'})")
    print(f"   duration according to the SERVER: {durata_s:.3f} s")
    if a.secondi:
        resa = durata_s / a.secondi
        print(f"   wall clock: {a.secondi:.3f} s  ⇒  yield {resa * 100:.1f} %")
    else:
        print("   ⚠ the rhythm is NOT judged: `--secondi` is missing, that is how long "
              "the capture lasted")
    print(f"   step between blocks: expected {atteso_us} µs · "
          f"minimum {min(passi) if passi else '-'} · "
          f"maximum {max(passi) if passi else '-'} · off step {len(salti)}")
    if salti[:5]:
        print(f"   the first jumps: {salti[:5]}")
    print(f"   signal judgement: {json.dumps(g, ensure_ascii=False)}")

    # ── the VERDICT, and every red line names its rule ──────────────────────
    rossi = []
    if g["esito"] == "GIUDICATO":
        if abs(g["hz"] - a.hz) > a.tolleranza_hz:
            rossi.append(f"the frequency is {g['hz']} Hz and not {a.hz}: "
                         f"§5.3 mandates 48 000 Hz at both ends")
        if g["purezza"] is None or g["purezza"] < a.purezza_minima:
            rossi.append(f"purity {g['purezza']} below {a.purezza_minima}: "
                         f"it is not a tone, it is noise — the v1 defect")
        if g["rms"] < 0.05:
            rossi.append(f"amplitude {g['rms']}: silence, or lost gain")
    if salti:
        rossi.append(f"{len(salti)} steps off the {atteso_us} µs of §5.3")
    if a.secondi and durata_s / a.secondi < 0.95:
        rossi.append(f"yield {durata_s / a.secondi * 100:.1f} %: the server does NOT "
                     f"produce the audio in real time")

    if rossi:
        print("\n⛔ ROSSO:")
        for r in rossi:
            print(f"   · {r}")
        return 1
    print("\n⭐ VERDE — and it holds for what it looked at: content"
          + (" and rhythm" if a.secondi else ", NOT the rhythm"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
