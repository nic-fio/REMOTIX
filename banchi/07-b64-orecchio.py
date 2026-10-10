#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b64-orecchio — THE JUDGE THAT HEARS THE CRACKLES.

⛔ `07-b42` can tell whether what arrives is **a tone** (frequency, amplitude,
   purity).  ⚠ It cannot tell whether that tone has a **gap** inside: half a second
   of signal skipped in the middle of eight seconds moves the purity by a trifle, and
   the verdict stays green.  ⇒ It is exactly the defect R26 describes —
   *«audio that crackles when the desktop works»* — and no tool of the
   project could see it.

⭐ HOW A CRACKLE IS HEARD, and it is not a count.

   A pure sine obeys an EXACT second-order recurrence:

        x[n] = 2·cos(ω)·x[n-1] − x[n-2]          ω = 2π·f/48000

   ⇒ The **residual** r[n] = x[n] − 2cos(ω)x[n-1] + x[n-2] is zero on a perfect
   tone, and is nonzero **only** where the waveform breaks: a phase jump
   (samples lost and stitched back), a silence that begins, a zero fill.
   ⛔ It does not count blocks and does not count bytes: it looks at the SAMPLES, which is rule
   (a) of `07-b43` and the first row of `LEZIONI.md` §2.2.

   ⚠ 16-bit quantisation noise gives |r| of a few LSB — with amplitude
   0.5 (peak 16383) that is ~0.00025 of the amplitude.  The threshold is at **0.02**,
   eighty times above: it does not fire on noise, and it fires on a phase jump
   of little more than one degree.

⛔ AND THE POSITIVE CONTROL LIVES INSIDE THIS FILE (`--certifica`): we build
   a perfect tone, remove 137 samples from the middle, and demand that
   the judge sees **that** gap and **only** that.  A judge that cannot
   see the defect it looks for has no right to green (`PIANO.md` §0.3.4).

Usage:
    python3 07-b64-orecchio.py --certifica
    python3 07-b64-orecchio.py giro.jsonl [--rif giro.rif.wav] [--hz 440]
"""
import argparse, base64, json, math, os, struct, sys, wave

FREQUENZA = 48000
CANALI = 2
PASSO_PCM_US = 5000          # §5.3: the PCM block is 5 ms
SOGLIA = 0.02                # fraction of the peak amplitude

# ⛔⛔ THE MINIMUM PEAK, AND IT IS THE CURE FOR FINDING R7 — 22 August 2026.
#
#      The line was `picco = max(abs(x) ...) or 1.0`, and on samples that were **all
#      zero** the peak became **1.0**: the threshold dropped to 0.02, the residuals
#      were zero, and the judge answered `scoppiettii 0`.
#      ⇒ **The ear judge gave top marks to silence**, which is
#      the error form this phase exists not to commit
#      (`LEZIONI.md` §2.2: the bench stayed green while the audio was broken).
#
# ⭐ The cure is not a smarter `or`: it is that below a certain signal the judge
#    **refuses to judge**.  The quantisation residual of a 16-bit signal
#    is ~4 LSB; for the threshold (2 % of the peak) to sit above that noise
#    a peak of at least ~400 is needed.  Below it, the detector can no longer tell
#    nothing from nothing, and saying so is the only honest answer (`CODER.md` §3.10).
PICCO_MINIMO = 400           # ~1.2 % of 16-bit full scale

# ⛔⛔⛔ THE BLIND GAP, AND IT IS DECLARED HERE BECAUSE IT CANNOT BE REMOVED.
#
#       A cut of N samples stitches back **in phase** — that is, invisible to the
#       residual — when N x f / 48000 is a whole number of cycles.  With the
#       tone at **440 Hz** and PCM blocks of **240 samples** (5 ms):
#
#           1200 samples = 5 blocks = **11.000 exact cycles** → invisible
#           2400 samples = 10 blocks = 22.000 cycles          → invisible
#           1201 samples                = 11.009 cycles       → seen
#
#       `[M]` 22 August 2026, reproduced on yesterday's judge: 25 ms and 50 ms of
#       vanished audio give **scoppiettii 0**.
#
# ⭐ It is not cured inside the detector — on a perfect sine that cut **leaves
#    no trace in the samples**, and no algorithm can see it.  It is cured
#    with a SECOND LEG that does not look at the waveform but at the **count**: the
#    samples arrived against those expected.  ⇒ `scoppiettii()` accepts
#    `attesi`, and the combined verdict looks at both.
#
# ⭐⭐ AND FOR FUTURE SCENES THERE IS A CURE THAT COSTS ONE DIGIT: a tone that
#     never comes to a whole number with the block.  At **443 Hz** a cut of k blocks
#     is 2.215 k cycles, and the first whole number comes at **200 blocks = 1 second**
#     instead of five.  ⚠ The 440 stays as long as the old measurements serve for
#     comparison: changing it now would make yesterday's numbers incomparable.
BLOCCO_PCM_CAMPIONI = 240    # 5 ms on one channel


# ══════════════════════════════════════════════════════════════════════════
def residui(campioni, hz):
    """The second-order recurrence.  Returns the residual, sample by sample."""
    w = 2.0 * math.cos(2.0 * math.pi * hz / FREQUENZA)
    fuori = [0.0, 0.0]
    for n in range(2, len(campioni)):
        fuori.append(campioni[n] - w * campioni[n - 1] + campioni[n - 2])
    return fuori


def scoppiettii(campioni, hz, soglia=SOGLIA, attesi=None):
    """⛔ The events, not the samples: a tear lasts a few samples and
       would count for three or four.  What lies within 5 ms is grouped.

    ⛔ `attesi` is the SECOND LEG (R7): how many samples there should have
       been.  The residual does not see a cut that is a multiple of 1200 samples; the
       count does.  ⚠ If it is not passed, the judgement holds only for what the
       waveform can tell, and this outcome declares it."""
    if len(campioni) < 64:
        return {"esito": "NIENTE DA GIUDICARE", "campioni": len(campioni)}
    picco = max(abs(x) for x in campioni)
    if picco < PICCO_MINIMO:
        # ⛔ R7: here `scoppiettii 0` used to come out, that is top marks.
        return {"esito": "SILENZIO O QUASI — NON GIUDICO",
                "perche": "peak %d below the minimum of %d: the detector's "
                          "threshold would end up below the quantisation "
                          "noise, and every answer would be made up"
                          % (picco, PICCO_MINIMO),
                "campioni": len(campioni), "picco": picco}
    r = residui(campioni, hz)
    lim = soglia * picco
    eventi, ultimo = [], None
    for n, v in enumerate(r):
        if abs(v) > lim:
            if ultimo is not None and n - ultimo["fine"] <= 240:
                ultimo["fine"] = n
                ultimo["salto"] = max(ultimo["salto"], abs(v) / picco)
            else:
                ultimo = {"campione": n, "fine": n, "ms": round(n * 1000.0 / FREQUENZA, 1),
                          "salto": abs(v) / picco}
                eventi.append(ultimo)
    for e in eventi:
        e["salto"] = round(e["salto"], 4)
        del e["fine"]
    # ⭐ The typical residual, which tells whether the threshold is far or stuck close
    ordinati = sorted(abs(v) for v in r)
    # ⭐ THE SECOND LEG: the count, which sees what the residual cannot.
    manca = None
    cieco = None
    if attesi:
        manca = int(attesi) - len(campioni)
        if manca > 0:
            # ⚠ And we say whether that gap would have been invisible to the residual: it is
            #   the information that explains a «zero crackles» next to a
            #   real shortfall, instead of letting them contradict each other in silence.
            cieco = abs(manca * hz / FREQUENZA
                        - round(manca * hz / FREQUENZA)) < 0.01
    return {"esito": "GIUDICATO", "campioni": len(campioni),
            "campioni_attesi": attesi,
            "campioni_mancanti": manca,
            "ammanco_invisibile_al_residuo": cieco,
            "picco": round(picco, 1),
            "residuo_mediano_rel": round(ordinati[len(ordinati) // 2] / picco, 6),
            "residuo_99_rel": round(ordinati[int(len(ordinati) * 0.99)] / picco, 6),
            "soglia_rel": soglia,
            "scoppiettii": len(eventi),
            "al_secondo": round(len(eventi) / (len(campioni) / FREQUENZA), 3),
            "dove": eventi[:40]}


# ══════════════════════════════════════════════════════════════════════════
def da_jsonl(percorso):
    """The client's PCM blocks → the samples of the left channel, and the GAPS
       declared by the `istante` (§6.3: the server's clock, not ours)."""
    campioni, istanti = [], []
    for r in open(percorso):
        r = r.strip()
        if not r:
            continue
        d = json.loads(r)
        if d.get("codec") != 2:
            continue                       # ⛔ PCM only: Opus is judged by the browser
        b = base64.b64decode(d["byte"])
        n = len(b) // (2 * CANALI)
        v = struct.unpack("<%dh" % (n * CANALI), b[:n * CANALI * 2])
        campioni.extend(v[0::CANALI])
        istanti.append(d["istante"])
    buchi = []
    for i in range(1, len(istanti)):
        dt = istanti[i] - istanti[i - 1]
        if dt != PASSO_PCM_US:
            buchi.append({"blocco": i, "passo_us": dt})
    durata_dichiarata = (istanti[-1] - istanti[0] + PASSO_PCM_US) / 1e6 if istanti else 0.0
    return {"campioni": campioni, "blocchi": len(istanti), "buchi_istante": buchi,
            "durata_dichiarata_s": round(durata_dichiarata, 3),
            "durata_campioni_s": round(len(campioni) / FREQUENZA, 3)}


def da_wav(percorso):
    w = wave.open(percorso, "rb")
    n = w.getnframes(); ch = w.getnchannels()
    d = w.readframes(n)
    v = struct.unpack("<%dh" % (len(d) // 2), d)
    return {"campioni": list(v[0::ch]), "blocchi": None, "buchi_istante": [],
            "durata_dichiarata_s": round(n / w.getframerate(), 3),
            "durata_campioni_s": round(n / w.getframerate(), 3)}


# ══════════════════════════════════════════════════════════════════════════
def giudizio_completo(dati, hz, finestra_s):
    """⛔ The Goertzel window must be a WHOLE number of seconds, or the
       judge of `07-b42` fails a perfect tone (§2.1, the box)."""
    c = dati["campioni"]
    r = {"blocchi": dati["blocchi"],
         "durata_dichiarata_s": dati["durata_dichiarata_s"],
         "durata_campioni_s": dati["durata_campioni_s"],
         "buchi_istante": len(dati["buchi_istante"]),
         "buchi_istante_dove": dati["buchi_istante"][:20]}
    # ⭐ The drift: how many samples are MISSING relative to the declared time.  If the
    #    graph skips a cycle, the samples do not arrive at all and the `istante`
    #    do not notice — this number does.
    if dati["durata_dichiarata_s"]:
        atteso = dati["durata_dichiarata_s"] * FREQUENZA
        r["campioni_mancanti"] = int(atteso - len(c))
        r["resa_campioni"] = round(len(c) / atteso, 5) if atteso else None
    # ⛔ `attesi` comes from the server's `istante` (§6.3), not from our
    #    clock: it is the only number that says how many samples there should have been.
    attesi = (int(round(dati["durata_dichiarata_s"] * FREQUENZA))
              if dati["durata_dichiarata_s"] else None)
    r.update({"scoppiettii": scoppiettii(c, hz, attesi=attesi)})
    # The certified judge of 07-b42, on a whole window in the middle.
    n = finestra_s * FREQUENZA
    if len(c) >= n:
        i = (len(c) - n) // 2
        qui = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, qui)
        import importlib.util
        sp = importlib.util.spec_from_file_location(
            "g42", os.path.join(qui, "07-b42-giudice.py"))
        g42 = importlib.util.module_from_spec(sp); sp.loader.exec_module(g42)
        r["tono"] = g42.giudica([x / 32768.0 for x in c[i:i + n]])
    else:
        r["tono"] = {"esito": "NIENTE DA GIUDICARE",
                     "perche": "less than %d s of samples" % finestra_s}
    return r


# ══════════════════════════════════════════════════════════════════════════
def certifica(hz=440):
    """⛔ The positive control, and now there are SEVEN cases.

    ⛔⛔ The two that were missing were found by the reviewer (R7), not me, and they are
         exactly the two that made a false green credible:

           · **silence**, which got top marks;
           · **the 1200-sample cut**, invisible to the residual because it is
             a whole number of cycles (exactly 11.000 at 440 Hz).

    ⭐ And the blind case is NOT declared green because the residual is quiet: it is
       declared green only if the SECOND LEG — the sample count — sees
       it.  A bench that cannot see the defect it looks for has no right to
       green (`PIANO.md` §0.3.4), and a bench that can see it only with another
       tool must say which.
    """
    import random
    amp = 0.5 * 32767

    def seno(n0, n, f=hz):
        return [int(amp * math.sin(2 * math.pi * f * (n0 + k) / FREQUENZA))
                for k in range(n)]

    sano = seno(0, FREQUENZA * 4)
    casi = []

    def taglia(quanti):
        return sano[:FREQUENZA * 2] + seno(FREQUENZA * 2 + quanti,
                                           FREQUENZA * 2 - quanti)

    #  (name, samples, expected, expected crackles, who must see it)
    casi.append(("0-healthy — a perfect 4 s tone", sano, None, 0, "nobody: it is healthy"))
    casi.append(("1-gap — 137 samples (2.9 ms) removed and stitched back",
                 taglia(137), None, 1, "the residual"))
    casi.append(("2-silence in the middle — 10 ms of zeros",
                 sano[:FREQUENZA * 2] + [0] * 480 + sano[FREQUENZA * 2 + 480:],
                 None, 2, "the residual"))

    random.seed(7)
    posti = sorted(random.sample(range(FREQUENZA // 2, FREQUENZA * 7 // 2), 10))
    tanti, prima, salto = [], 0, 0
    for p in posti:
        tanti += seno(prima + salto, p - prima)
        prima, salto = p, salto + 61
    tanti += seno(prima + salto, len(sano) - prima)
    casi.append(("3-ten tears of 61 samples", tanti, None, 10, "the residual"))

    # ⛔ R7a — SILENCE.  It used to give `scoppiettii 0`, that is top marks.
    casi.append(("4-⛔ R7a: four seconds of ZEROS", [0] * (FREQUENZA * 4),
                 None, "SILENZIO O QUASI — NON GIUDICO", "the refusal"))

    # ⛔ R7b — THE BLIND GAP.  The residual does not see it and cannot see it: 1200
    #    samples are exactly 11.000 cycles.  THE COUNT must see it.
    casi.append(("5-⛔ R7b: 1200 samples removed (25 ms = 11.000 cycles)",
                 taglia(1200), FREQUENZA * 4, 0, "⭐ the COUNT (1200 missing)"))
    casi.append(("6-⛔ R7b: 2400 samples removed (50 ms = 22.000 cycles)",
                 taglia(2400), FREQUENZA * 4, 0, "⭐ the COUNT (2400 missing)"))

    print("⭐ CERTIFICATION OF THE JUDGE — the expected outcome is written FIRST\n")
    verde = True
    for nome, c, attesi, atteso, chi in casi:
        e = scoppiettii(c, hz, attesi=attesi)
        if isinstance(atteso, str):
            visto = e.get("esito")
            buono = visto.startswith(atteso[:12])
        else:
            visto = e.get("scoppiettii")
            buono = (visto == atteso)
            # ⛔ And for the two blind cases it is not enough for green that the residual
            #    is quiet: the count MUST say how much is missing, or the bench is blind.
            if attesi is not None:
                manca = e.get("campioni_mancanti")
                if not manca or manca != attesi - len(c):
                    buono = False
                    visto = "%s (count: %s)" % (visto, manca)
                else:
                    visto = "%s, and the count sees %d missing (invisible to the "\
                            "residual: %s)" % (visto, manca,
                                              e.get("ammanco_invisibile_al_residuo"))
        verde = verde and buono
        print("  %-52s expected %-6s · %s\n      %s  who sees it: %s"
              % (nome, atteso, visto, "OK" if buono else "⛔ NO", chi))
    print()
    # ⭐ And the control of the CONTROL: at 443 Hz the blind gap is gone.
    #    ⚠ It is not a cure to apply today (it would make yesterday's measurements
    #    incomparable): it is the proof that the diagnosis of the blind gap is right.
    rotto443 = ([int(amp * math.sin(2 * math.pi * 443 * k / FREQUENZA))
                 for k in range(FREQUENZA * 2)]
                + [int(amp * math.sin(2 * math.pi * 443 * (k + FREQUENZA * 2 + 1200)
                                      / FREQUENZA))
                   for k in range(FREQUENZA * 2 - 1200)])
    e443 = scoppiettii(rotto443, 443)
    ok443 = e443.get("scoppiettii") == 1
    verde = verde and ok443
    print("  %-52s expected %-6s · %s  %s"
          % ("7-⭐ the same cut at 443 Hz (11.075 cycles)", 1,
             e443.get("scoppiettii"), "OK" if ok443 else "⛔ NO"))
    print("      ⇒ the blind gap belongs to the TONE, not to the detector: at 443 Hz it disappears")
    print()
    if verde:
        print("⭐ seven cases out of seven: the judge can see the defect it looks for,")
        print("   and where it CANNOT see it, it says which other tool sees it.")
    else:
        print("⛔ THE JUDGE IS BLIND: none of its greens is to be believed.")
    return 0 if verde else 3


def principale():
    p = argparse.ArgumentParser()
    p.add_argument("jsonl", nargs="?")
    p.add_argument("--rif", default="", help="the wav of the independent referee (pw-record)")
    p.add_argument("--hz", type=int, default=440)
    p.add_argument("--finestra", type=int, default=1)
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()
    if a.certifica:
        return certifica(a.hz)
    if not a.jsonl:
        print("⛔ the JSONL is needed, or --certifica", file=sys.stderr); return 2
    fuori = {"file": a.jsonl}
    if not os.path.exists(a.jsonl) or os.path.getsize(a.jsonl) == 0:
        # ⛔ CODER.md §3.10: «I read nothing» is an outcome of ITS OWN, not a zero.
        fuori["esito"] = "NIENTE DA GIUDICARE — the JSONL is missing or empty"
        print(json.dumps(fuori, ensure_ascii=False, indent=1)); return 2
    fuori["nostro"] = giudizio_completo(da_jsonl(a.jsonl), a.hz, a.finestra)
    if a.rif and os.path.exists(a.rif) and os.path.getsize(a.rif) > 1000:
        fuori["arbitro_pw_record"] = giudizio_completo(da_wav(a.rif), a.hz, a.finestra)
    elif a.rif:
        fuori["arbitro_pw_record"] = "NIENTE DA GIUDICARE — the wav is missing or empty"
    print(json.dumps(fuori, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(principale())
