#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
11-c5 — ⭐⭐ «THE SOUND IS THERE AND IT IS NOT SILENCE»
===========================================================================

    python3 11-c5-il-suono-non-e-silenzio.py --porta 8512
    python3 11-c5-il-suono-non-e-silenzio.py --porta 8512 --senza-sorgente
    python3 11-c5-il-suono-non-e-silenzio.py --certifica

It is line **C5** of `fasi/11-la-rete-di-sicurezza.md` §4.1:

    what must be true         : the sound is there and it is not silence
    where it starts from      : ⛔ a NEW session (a tenant never used)
    what it looks at          : ⭐ the BYTES that arrive at the client, and that they
                                are not silence
    how I know it can say red : the source is removed ⇒ red

---------------------------------------------------------------------------
⭐⭐ WHY THIS MESH SEES SOMETHING WHILE THE OTHERS ARE BLIND
---------------------------------------------------------------------------

`fasi/11…` §6 and §7-bis.13: `[M]` **ten new GNOME sessions out of ten are born
without a monitor**, ⇒ C2, C3, C4, C6 and half B of C8 **have nothing to
look at**, because they look at a pixel through the product.

⭐ C5 judges **bytes**, not pixels — and the bytes of the sound do not go through the
  compositor.  ⛔ **But it was not taken for granted: it was measured.**

  `[M]` 26 August 2026, box `rete11-kde`, port 8512, tenant `c5u1`:
  the product log says for that same session

      figlio [c5u1] ⛔ no virtual monitor to capture … monitor «»
                    (0 before, 0 after), 0x0

  i.e. **the session was BLIND** — ⇒ and in the very same round the client
  received **13 753 PCM blocks, 13 202 880 bytes, purity 1.0000**.

  ⭐ And there is a second measured fact that makes C5 **faster** than all the
    others: the «remotix» sink appears in the tenant's PipeWire after **3
    seconds**, while the graphical stage wants ~13 when it manages.

  ⇒ **C5 is today the only mesh that goes through the product from top to bottom and
    still has something to judge.**

---------------------------------------------------------------------------
⛔⛔ WHAT «SILENCE» IS, WITH A NUMBER — and the number is CALIBRATED
---------------------------------------------------------------------------

⛔ *«Some bytes arrived»* **is not a proof that there is sound**: a
   stream of zeros is bytes that arrive and it is perfect silence.  ⇒ A
   measure of **energy** is needed, and a **declared threshold**.

**The yardstick**: the client is asked for the **PCM** codec (`--audio-codec pcm`, which
§4.3 of the protocol imposes as «base always available»), ⇒ the payload of the
datagram is **s16 little-endian, 48 000 Hz, 2 channels, 240 frames = 480
samples = 960 bytes per block, 5 ms** (`src/audio.h`: `AUDIO_BLOCCO_PCM`,
`AUDIO_FREQUENZA`, `AUDIO_CANALI`).  ⭐ On those samples the **RMS** is computed,
in units of full scale 32767.

⚠ And PCM is asked for on purpose: with Opus the payload is compressed and to measure
  the energy a decoder inside the bench would be needed.  ⛔ A bench that
  carries a decoder inside it is a bench that can go wrong by itself.

**The three numbers of the verdict**, each one with its own reason:

    SOGLIA_RMS   = 328 of 32767  ⇒ 1.0 % of full scale, i.e. −40 dBFS
    MIN_BLOCCHI  = 200           ⇒ 1 second of sound (5 ms per block)
    MIN_FRAZIONE = 0.50          ⇒ half of the blocks must be above threshold

⭐⭐ **THE CALIBRATION — `[M]` 26 August 2026, `rete11-kde`, port 8512, SIX
    real sessions.**  ⛔ The threshold is not invented: it was **searched for**
    by running the real mesh at different amplitudes, until it was seen where
    the border lies.

  | the source (440 Hz wave)     | RMS measured | in dBFS | times threshold | verdict  |
  |------------------------------|--------------|---------|-----------------|----------|
  | amplitude **1.0** (default)  | **23 169.3** |  −3.0  | **70.6 ×**  | ⭐ GREEN |
  | amplitude 0.5                |   11 582.7   |  −9.0   | 35.3 ×      | GREEN |
  | amplitude **0.02**           |      463.1   | −37.0   | **1.41 ×**  | ⭐ GREEN — the nearest real point from above |
  | amplitude **0.01**           |      231.2   | −43.0   | **0.71 ×**  | ⛔ RED — the nearest real point from below |
  | amplitude 0.001              |       22.6   | −63.2   | 0.07 ×      | ⛔ RED |
  | ⛔ **no source**              |      —       |   —     |      —      | ⛔ RED: **zero blocks**, NOTHING arrives |

⭐ **The border was CROSSED in both directions on real data**, not
  deduced: between 0.01 and 0.02 of amplitude the mesh changes verdict, and the threshold
  falls where the document says it falls (amplitude 0.0142 = 1.42 % of full
  scale).  ⇒ It is not a threshold that «has never given red in its life»
  (`LEZIONI.md` §1.47).

⚠ **And the path is TRANSPARENT**, measured and not assumed: RMS measured /
  RMS expected = 23 169.3 / 23 170 = **1.0000**.  ⇒ What `pw-play` puts in the
  sink arrives at the client **at the same level**, and the product's count
  confirms it from the other end of the wire (`PEAK 32767 of 32767`).

⛔⛔ **AND HERE THE BENCH HAS ALREADY LIED ONCE, before being written.**
  The exploratory probe made the wave with `ffmpeg -f lavfi -i sine=…` and measured
  **RMS 2 047.5, PEAK 2 896** — i.e. *«the path attenuates by 21 dB»*.  ⛔ It was
  false: it was **the generator** attenuating, not the path.  ⇒ A threshold calibrated on
  that number would have been **ten times too low**, and nobody would have
  noticed until it stopped giving red.
  ⭐ **It is the reason why this file writes the wave**: an amplitude that
    depends on the semantics of someone else's generator is a threshold that
    moves without saying so.

⇒ ⭐ And for the same reason the mesh **always prints the margin**: the day
  that path stopped being transparent, it would be seen **before**
  it becomes a false red, instead of after.

⛔ AND WHAT THE THRESHOLD IS **NOT**: it is not a judgement on how loud the
   user's sound is.  It is the line that separates *«the tone I put in
   passed»* from *«a stream of near-zeros arrives»*.  ⚠ The fine quality of the sound
   is the user's judgement (I8), and §6 puts it **outside** the net.

---------------------------------------------------------------------------
⭐ WHERE THE SOUND COMES FROM — and there is nothing to add to the recipe
---------------------------------------------------------------------------

The product **makes its own sink by itself**: `src/suono.c` creates in the tenant's
PipeWire a `support.null-audio-sink` called **`remotix`** and captures
its monitor.  ⇒ ⭐ To make sound it is enough to **play inside that sink**.

`[M]` 26 August 2026, inside `rete11-kde`, already present and verified **before**
writing this mesh (E1: the recipe is not inspected, one tries to do the
thing):

    /usr/bin/pw-play   pipewire-bin 1.4.2-1     ⭐ plays the tone
    /usr/bin/pw-cli    pipewire-bin 1.4.2-1     ⭐ says whether the sink is there
    /usr/sbin/runuser  util-linux               becomes the tenant

⛔ **Nothing needs to be added to the four recipes**, and it is not a detail:
   a mesh that asks for a new package forces rebuilding the four
   boxes, i.e. calling C11 (the alignment) into question again.

⚠ And the wave is **not** made by `ffmpeg`, which is there too: this mesh writes it, in
  Python, sample by sample.  ⭐ So **the amplitude is a number of this
  file** and not the semantics of someone else's filter — which is exactly what
  a calibrated threshold needs.

---------------------------------------------------------------------------
⛔⛔ THREE DISTINCT OUTCOMES, AND NOT TWO — §4.5, and the defect of `LEZIONI.md` §1.49
---------------------------------------------------------------------------

⭐ *«NOTHING arrived»* and *«I could not open the session»*
  have the same symptom — an empty blocks file — **and they are two
  opposite things**.  ⇒ The mesh separates them **before** looking at the blocks:

  · the client was not ADMITTED               ⇒ **3**, I could not look
  · the tenant's PipeWire does not answer     ⇒ **3**, the terrain does not speak
  · PipeWire answers and the «remotix» sink is NOT there
                                              ⇒ ⛔ **1**, RED: the product
                                                 did not open the sound path
  · the sink is there, the source plays, and not one block arrives
                                              ⇒ ⛔ **1**, RED: the sound is not there
  · blocks arrive but the energy is below threshold
                                              ⇒ ⛔ **1**, RED: it is silence
  · the negotiated codec is not PCM           ⇒ **3**: I cannot measure the energy

---------------------------------------------------------------------------
⛔ THE GRAFTED FAULT — `--senza-sorgente`, and it must be run
---------------------------------------------------------------------------

`--senza-sorgente` does everything **except** playing the tone.  ⇒ The session delivers
digital silence, and the cure of `src/audio.c` (on since 24 August 2026) **does not
send the all-zero blocks**: ⇒ nothing arrives at the client.

⭐ With the grafted fault **the outcome is read backwards**: here green is a
  red.  If C5 said green without a source, ⛔ it would not be looking at the sound
  — it would be looking at something else, and it could not be trusted.

⚠ `[M]` It was run, not imagined: the numbers are in the mesh's
  report (§7-bis of the phase document).

---------------------------------------------------------------------------
⛔ WHAT C5 DOES **NOT** LOOK AT — declared, or someone will trust it too much
---------------------------------------------------------------------------

  · ⛔ **it does not look at a pixel.**  A blind session passes it GREEN, and that is
    right: that is C1.  ⚠ ⇒ C5 green **does not mean «the session
    is fine»**, it means «the sound path is open».
  · ⛔ **it does not judge the quality of the sound**: neither fidelity, nor distortion, nor
    synchronisation with the video (I8, the user's judgement; §6 of the phase).
  · ⛔ **it does not judge the latency** nor the jitter: the client can count them, this
    mesh does not read them.
  · ⛔ **it does not look at Opus**, which is the codec the real browser negotiates: here
    PCM is asked for to be able to measure the energy without a decoder.
    ⚠ ⇒ A fault that hit **only** the Opus branch, C5 would not see.
  · ⛔ **it is not an intermittency test**: it opens **one** session, not ten.
    If the birth of the sink became sporadic, ⇒ it is C1 that counts the rounds.
  · ⛔ **it does not prove that the sound is the RIGHT one**: it proves there is energy, not
    that it is the wave we played.  ⚠ Any noise would pass.

---------------------------------------------------------------------------
THE OUTCOMES (§4.5 of the phase document)
---------------------------------------------------------------------------

  0  ⭐ I looked: the sound arrives and it is not silence
  1  ⛔ I looked and it does NOT hold ⇒ red
  3  ⛔ I could not look — ⛔ and it is NOT a red
  2  the terrain does not hold, or the usage is wrong
===========================================================================
"""
import argparse
import importlib.util
import base64
import json
import math
import os
import struct
import subprocess
import sys
import time

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ «WAS THE CLIENT ADMITTED?» — ⛔ THE PREDICATE IS IMPORTED, NOT
#     REWRITTEN.  Its home is `11-c1-nasce-e-si-vede.py`, and there is ONE (§1.47).
#
# ⛔ Until 27 August 2026 there was `"AMMESSO" in uscita` here, ⭐ and it could not
#    say no: `[R]` `01-b3-cliente.py` prints that word also in the **two
#    refusal messages** — «CONGEDO instead of AMMESSO: reason …» (:1315) and
#    «expected AMMESSO, arrived …» (:1322) — and prints them on **stdout**, which
#    is exactly where it looked.  ⇒ A predicate that cannot fail,
#    `LEZIONI.md` §1.44: the mesh believed it had got in **even when it had been
#    turned away**, and then judged the darkness that followed as a defect of the
#    product.
# ⚠ It was in FIVE meshes with the same line.  ⇒ Curing it five times would have
#   been creating five places to diverge from again (§1.47): it lives in C1, and
#   the other four import it from there.
# ⛔ And if it cannot be imported we exit **3** and say so, ⇒ ⛔ we do not
#   silently fall back on the poor predicate — which is the defect itself.
# ═══════════════════════════════════════════════════════════════════════════
_QUI_C1 = os.path.dirname(os.path.abspath(__file__))
_C1 = None


def _carica_c1():
    """⛔ It is a LOADER, not a judge: it finds the file, it decides nothing.

    ⚠ It is looked for next to me (inside the box everything is in `/opt/remotix`) and
      one level up, as C2, C3 and C6 do with their imported judges.
    """
    for p in (os.path.join(_QUI_C1, "11-c1-nasce-e-si-vede.py"),
              os.path.join(os.path.dirname(_QUI_C1), "11-scatole",
                           "11-c1-nasce-e-si-vede.py")):
        if not os.path.exists(p):
            continue
        spec = importlib.util.spec_from_file_location("c1_ammissione", p)
        m = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(m)
        except Exception:
            return None
        # ⛔ We VERIFY that what is needed is there, instead of trusting the name
        #    of the file (`CODER.md` §3.9).
        if not callable(getattr(m, "e_stato_ammesso", None)):
            return None
        if not callable(getattr(m, "certifica_ammissione", None)):
            return None
        # ⭐ And from C1 also comes the guarantee of the card's groups: same
        #    reason, same single place (§1.47).
        for mestiere in ("garantisci_i_gruppi", "verdetto_gruppi",
                         "certifica_gruppi"):
            if not callable(getattr(m, mestiere, None)):
                return None
        return m
    return None


def casa_dell_ammissione():
    global _C1
    if _C1 is None:
        _C1 = _carica_c1()
    if _C1 is None:
        print("⛔ I cannot find `11-c1-nasce-e-si-vede.py` next to me, and from there")
        print("   comes the predicate «was the client ADMITTED?» — which lives")
        print("   in one place only on purpose (§1.47).")
        print("⇒ I could not look — ⛔ and it is NOT a red (§4.5).")
        sys.exit(3)
    return _C1


def e_stato_ammesso(coda):
    """⭐ `True` admitted · `False` **TURNED AWAY** · `None` said nothing.

    ⛔ `False` is not a product red: a client turned away is a client
       turned away, and the caller exits **3**.
    """
    return casa_dell_ammissione().e_stato_ammesso(coda)


def garantisci_i_gruppi(chi, prefisso="   "):
    """⭐⭐ THE CARD'S GROUPS — ⛔ and this too lives in one place only (C1).

    Returns `(esito, perche)`: `0` = the tenant sees and it can be measured,
    `3` = ⛔ it is NOT measured.

    ⛔ Until 27 August 2026 this mesh created the tenant with
       `usermod -aG video,render` **and did not read back**: two nailed-down names (which
       belong to ONE distribution) and no verification.  ⭐ `[M]` without the groups
       of the `/dev/dri` nodes the session is born BLIND — 0 of 4, never in 90 s, zero
       frames — and this mesh would have measured the darkness calling it
       a product defect (`fasi/10-…` §7.4).
    ⭐ The work is done by `attrezzi-gruppi-scheda.sh`, which reads the gids from the NODES and
       reads back comparing the numbers.  ⛔ No copy of it is made here (§1.47).
    """
    return casa_dell_ammissione().garantisci_i_gruppi(chi, prefisso)

# ---------------------------------------------------------------------------
# ⛔ THE YARDSTICK, DECLARED HERE AND PRINTED AT EVERY ROUND.  A verdict without its
#    yardstick is an opinion (§4.2 of the phase).
# ---------------------------------------------------------------------------
FONDO_SCALA = 32767.0

# 1.0 % of full scale = −40 dBFS.  ⭐ CALIBRATED on six real sessions (the table
# at the top): the default tone sits **70.6 times above** it, and the border was
# crossed in both directions between amplitude 0.01 (red) and 0.02
# (green).  ⛔ It is not a number that has never given red in its life.
SOGLIA_RMS = 328.0

# 200 blocks of 5 ms = 1 second of sound.  ⛔ A single block is not a stream:
# it could be a click in the middle of nothing.
MIN_BLOCCHI = 200

# ⛔ Half of the blocks must be above threshold.  Without this, a loud tone for
#    a tenth of the time and zeros for the rest would have the global RMS in order.
#
# ⚠⚠ AND IT MUST BE SAID THAT TODAY THIS CRITERION IS ALMOST BLIND ON THE REAL PATH, as
#    C5 says the other things it does not look at: `src/audio.c` (`audio_taci_silenzio`,
#    on by default) **does not send the mute blocks**, so the holes
#    do not reach the client and do not enter the denominator.  ⇒ On real data
#    `frazione` is ~1.0 **by construction**, and for `A TRATTI` to fire
#    a near-silent but not exactly null stream would be needed — which the
#    `SILENZIO` criterion catches first.
#    ⇒ It is neither a false red nor a false green: it is a criterion
#      certified on synthetic cases that the product structures itself never to
#      produce.  ⭐ It stays to defend the day that cure were switched off (a
#      server started with `--niente-audio-silenzio`), and it stays to defend the
#      HEAD of the wave — the seconds between the admission and the appearance of the sink, which
#      no margin covers (see `--resta` further below).
MIN_FRAZIONE = 0.50

# The format of the PCM payload — `src/audio.h`.
PCM_CODEC = 2
PCM_FREQUENZA = 48000
PCM_CANALI = 2
PCM_FOTOGRAMMI = 240          # 5 ms
PCM_BYTE_BLOCCO = PCM_FOTOGRAMMI * PCM_CANALI * 2   # = 960

# The sink the product creates by itself — `src/suono.c`, `NOME_SINK`.
NOME_SINK = "remotix"

# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ THE BIRTH CEILING — and it is a MEASUREMENT, not a round number (§1.45).
#
# ⛔ The «remotix» sink cannot appear before the SESSION is born: it is taken care
#    of by `src/suono.c` inside the session.  ⇒ C5's ceiling is the ceiling
#    of the birth, and it is the same number as C1 (`TETTO_NASCITA` there).
#
# `[M]` 27 August 2026, **cured** GNOME box, three new sessions: the
# `negotiated format` — the instant the monitor is born — arrives in
#
#     1.105 s        0.998 s        0.957 s        ⇒ maximum **1.105 s**
#
# and the sink is seen in `[M]` **3 s** (measurement of 26 Aug, healthy boxes).
#
# ⛔⛔ AND THIS LINE HAS ALREADY CARRIED A WRONG NUMBER, FOR HALF A DAY:
#     **152 s**, calibrated on a delay of ~97 s that **was not the product's**.
#     `[M]` It was a fault of the BOX: §6 of the recipe moved the
#     `polkitd` group from 991 to 1991 to give 991 to `render`, and `groupmod -g` does not
#     carry the files along ⇒ `polkitd` could no longer read
#     `/etc/polkit-1/rules.d`, died, and `gnome-shell` took four
#     25 s timeouts.  ⇒ ⚠ A ceiling of 152 s on a phenomenon of 1.1 s is
#     **a hundred times** the phenomenon: ⛔ a ceiling like that does not protect, it **hides**
#     — once expired it has nothing more to say, and in the meantime it has paid
#     a hundred and fifty seconds for every round that goes wrong.
#   ⭐ The lesson, and it is worth more than the number: **before calibrating a ceiling on a
#     measurement, look whether that measurement is the product's or the bench's.**
#
# ⭐ THE MARGIN, AND WHERE IT COMES FROM — and it is not the margin of today's
#   spread (0.957-1.105 s, 15 %), which would be a margin measured on a
#   single machine at rest:
#
#     · the healthy phenomenon, today               `[M]`  1.105 s
#     · the sink, on the healthy boxes              `[M]`  3 s
#     · ⚠ the slowest birth EVER measured in
#       this project (26 Aug, loaded box)           `[M]` ~13 s
#     · the margin declared on THAT one             **× 2**
#                                                   ⇒ **26 s**
#
#   ⇒ 26 s are **8.7 times** the measured sink and **twice** the worst ever
#     seen.  ⚠ The margin sits on the worst on purpose: the box can be
#     loaded, and the real machine has an **integrated Intel UHD 730**.
TETTO_NASCITA = 26.0

# ⭐ And the actual MEASURING WINDOW, i.e. how much sound one wants to have
#   in hand after the sink has been seen.  ⚠ 25 s = ~5 000 blocks of 5 ms:
#   it is the population the threshold is calibrated on (`[M]` ~4 878 blocks on the
#   healthy boxes) and **25 times** `MIN_BLOCCHI`.
FINESTRA_MISURA = 25.0


# ---------------------------------------------------------------------------
# ⭐⭐ THE JUDGE — and it lives on its own, without network, without box, without session.
#
# ⛔ It is the part `--certifica` puts to the test.  It takes a list of
#    blocks `(codec, carico)` and returns a verdict:
#      True  = there is sound and it is not silence
#      False = ⛔ red
#      None  = ⛔ I do not know — and ⛔ `None` is NOT zero (§4.5)
# ---------------------------------------------------------------------------
def giudica(blocchi, soglia=SOGLIA_RMS, min_blocchi=MIN_BLOCCHI,
            min_frazione=MIN_FRAZIONE):
    m = {"blocchi": None, "byte": 0, "codec": None, "campioni": 0,
         "rms": None, "picco": None, "sopra": None, "frazione": None,
         "motivo": None}

    if blocchi is None:
        m["motivo"] = "I could not read the blocks"
        return None, m

    m["blocchi"] = len(blocchi)
    m["byte"] = sum(len(c) for _, c in blocchi)

    # ⛔ BEFORE anything else: «nothing arrived» is a RED, not an
    #    «I do not know».  Whoever gets here has already had the session and the sink: if
    #    with the source on not one block arrives, the sound is NOT THERE.
    if not blocchi:
        m["motivo"] = "NIENTE: not a single audio block arrived"
        return False, m

    codec = set(c for c, _ in blocchi)
    if len(codec) != 1:
        m["codec"] = sorted(codec)
        m["motivo"] = ("the codec CHANGES in mid-session (%s): I do not know on which "
                       "format to measure the energy" % sorted(codec))
        return None, m
    m["codec"] = codec.pop()
    if m["codec"] != PCM_CODEC:
        m["motivo"] = ("the negotiated codec is %d, not PCM (%d): the energy would "
                       "be measured only by decoding, and this bench does not "
                       "decode" % (m["codec"], PCM_CODEC))
        return None, m

    # ⛔ A payload of odd length is not s16: no guessing.
    if any(len(c) % 2 for _, c in blocchi):
        m["motivo"] = "at least one payload has ODD length: it is not s16"
        return None, m

    somma = 0
    campioni = 0
    picco = 0
    sopra = 0
    for _, carico in blocchi:
        n = len(carico) // 2
        if n == 0:
            continue
        v = struct.unpack("<%dh" % n, carico)
        s = 0
        for x in v:
            s += x * x
            if x < 0:
                x = -x
            if x > picco:
                picco = x
        somma += s
        campioni += n
        if math.sqrt(s / n) >= soglia:
            sopra += 1

    if campioni == 0:
        m["motivo"] = "%d blocks arrived and ZERO samples" % len(blocchi)
        return None, m

    m["campioni"] = campioni
    m["rms"] = math.sqrt(somma / campioni)
    m["picco"] = picco
    m["sopra"] = sopra
    m["frazione"] = sopra / float(len(blocchi))

    # ⚠ The order of the three checks is that of the report one wants to read:
    #   first «how much», then «how loud», then «for how long».
    if len(blocchi) < min_blocchi:
        m["motivo"] = ("POCHI: %d blocks of %d expected at minimum (%d ms of "
                       "sound): it is not a stream"
                       % (len(blocchi), min_blocchi, len(blocchi) * 5))
        return False, m
    if m["rms"] < soglia:
        m["motivo"] = ("SILENZIO: RMS %.1f below the threshold %.0f (%.4f %% of "
                       "full scale): bytes arrive, but they are not sound"
                       % (m["rms"], soglia, 100 * m["rms"] / FONDO_SCALA))
        return False, m
    if m["frazione"] < min_frazione:
        m["motivo"] = ("A TRATTI: only %d blocks out of %d (%.0f %%) are above "
                       "threshold: the sound comes in bursts"
                       % (sopra, len(blocchi), 100 * m["frazione"]))
        return False, m

    m["motivo"] = ("RMS %.1f = %.2f times the threshold" % (m["rms"], m["rms"] / soglia))
    return True, m


def guasto_visto(verdetto, m):
    """⛔⛔ §1.52 — «the fault was seen» is NOT «the verdict is red».

    ⚠ C5 on GNOME is red on its own (`[M]` 41 blocks instead of ~4 878,
      reason `POCHI`).  ⇒ A predicate that looked only at the colour would say
      «seen» even if the injection had bitten nothing, and the
      net's certification would rest on a defect of the product.
    ⭐ TWO things are demanded: the red **and** the measurable difference — without
      source **ZERO** blocks must arrive, not «few».
    ⛔ `None` is not zero: if it could not be judged, nothing was
       seen (§4.5).
    """
    return verdetto is False and m.get("blocchi") == 0


def in_db(v):
    """dBFS, and ⛔ `None` for «I do not know»: a zero here would be a lie."""
    if v is None or v <= 0:
        return None
    return 20.0 * math.log10(v / FONDO_SCALA)


def riga_misure(m):
    def q(x, f="%.1f"):
        return "unknown" if x is None else (f % x)
    db = in_db(m["rms"])
    return ("blocks %s · bytes %d · codec %s · RMS %s (%s %% f.s., %s dBFS) · "
            "PEAK %s · above threshold %s/%s (%s %%)"
            % (q(m["blocchi"], "%d"), m["byte"], m["codec"],
               q(m["rms"]),
               "?" if m["rms"] is None else "%.4f" % (100 * m["rms"] / FONDO_SCALA),
               "?" if db is None else "%.1f" % db,
               q(m["picco"], "%d"), q(m["sopra"], "%d"), q(m["blocchi"], "%d"),
               "?" if m["frazione"] is None else "%.0f" % (100 * m["frazione"])))


# ---------------------------------------------------------------------------
# The test wave — written here, sample by sample.
# ---------------------------------------------------------------------------
def scrivi_onda(percorso, secondi, ampiezza, hertz=440.0):
    """A WAV s16le 48 kHz stereo with a sine wave.

    ⚠ It is written by hand instead of calling `ffmpeg` for one reason only, and it is not
      elegance: ⭐ **the amplitude must be a number of this file**.  A
      threshold calibrated on an amplitude that depends on the semantics of
      someone else's filter is a threshold that moves without anyone knowing.
    """
    picco = int(ampiezza * 32767)
    passo = 2.0 * math.pi * hertz / PCM_FREQUENZA
    # ⭐ ONE SECOND is built and repeated, and it is not only to be quick:
    #   at 440 Hz a second contains 440 WHOLE cycles, ⇒ the joint is exact and
    #   does not produce the click a cut in mid-wave would leave.
    #   ⚠ With a non-integer `--hertz` the joint is no longer exact: it is a
    #     declared sound defect, and it does not touch the energy measurement.
    uno = []
    for i in range(PCM_FREQUENZA):
        v = int(round(picco * math.sin(passo * i)))
        v = 32767 if v > 32767 else (-32768 if v < -32768 else v)
        uno.append(v)
        uno.append(v)
    secondo = struct.pack("<%dh" % len(uno), *uno)
    corpo = secondo * max(1, int(round(secondi)))
    with open(percorso, "wb") as f:
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + len(corpo)))
        f.write(b"WAVEfmt ")
        f.write(struct.pack("<IHHIIHH", 16, 1, PCM_CANALI, PCM_FREQUENZA,
                            PCM_FREQUENZA * PCM_CANALI * 2, PCM_CANALI * 2, 16))
        f.write(b"data")
        f.write(struct.pack("<I", len(corpo)))
        f.write(corpo)
    os.chmod(percorso, 0o644)
    return picco


def leggi_blocchi(percorso):
    """⛔ Returns `None` if the file could not be read, `[]` if it is empty.
       They are two different things and must not have the same face."""
    if not os.path.exists(percorso):
        return None
    fuori = []
    try:
        with open(percorso, "r") as f:
            for riga in f:
                riga = riga.strip()
                if not riga:
                    continue
                d = json.loads(riga)
                fuori.append((d["codec"], base64.b64decode(d["byte"])))
    except (OSError, ValueError, KeyError):
        return None
    return fuori


# ---------------------------------------------------------------------------
# ⛔ NO NESTED `sh -c` — `LEZIONI.md` §1.46.  Every command is an array, and
#    programs are called by path.
# ---------------------------------------------------------------------------
def esegui(comando, tetto=30):
    try:
        return subprocess.run(comando, capture_output=True, text=True, timeout=tetto)
    except (OSError, subprocess.TimeoutExpired):
        return None


def come(chi, uid, resto, tetto=30):
    """Runs `resto` **as the tenant**, with its `XDG_RUNTIME_DIR`."""
    return esegui(["runuser", "-u", chi, "--", "env",
                   "XDG_RUNTIME_DIR=/run/user/%d" % uid] + resto, tetto=tetto)


def sink_c_e(chi, uid):
    """Returns True / False / ⛔ None if PipeWire did not answer at all.

    ⭐ And the three values are three different outcomes further on: «does not answer» is the
      terrain (3), «answers and the sink is not there» is a product red (1).
    """
    p = come(chi, uid, ["pw-cli", "ls", "Node"], tetto=20)
    if p is None or p.returncode != 0 or not p.stdout.strip():
        return None
    nome = classe = None
    for riga in p.stdout.splitlines():
        r = riga.strip()
        if r.startswith("id ") and ", type " in r:
            nome = classe = None
            continue
        if r.startswith("node.name"):
            nome = r.split("=", 1)[1].strip().strip('"')
        elif r.startswith("media.class"):
            classe = r.split("=", 1)[1].strip().strip('"')
        # ⛔ It is not enough that the name appears: there are TWO «remotix» nodes — the sink
        #    and the stream that captures it.  ⭐ The one needed is the SINK.
        if nome == NOME_SINK and classe == "Audio/Sink":
            return True
    return False


def sgombra(chi, attesa=45.0):
    """⭐ Always and only one's OWN tenant, by name: never a global pattern.
       (phase 10 §7.3: a global `pkill -f` risked killing the work
       of another test that was measuring.)

    ⛔⛔ AND WE WAIT FOR THE EVENT, NOT FOR THE CLOCK.  `loginctl terminate-user` and
        `pkill` return AT ONCE: whoever restarted after half a second would recreate
        the tenant while the previous one is still dying.  ⚠ It is exactly
        the defect that made C1 say «I do not know» five times out of ten
        (`fasi/11…` §7-bis.13).  ⇒ Returns True if the field is REALLY free.
    """
    esegui(["loginctl", "terminate-user", chi], tetto=20)
    time.sleep(1.0)
    esegui(["pkill", "-KILL", "-u", chi], tetto=20)
    scadenza = time.time() + attesa
    while time.time() < scadenza:
        viva = esegui(["loginctl", "show-user", chi], tetto=15)
        proc = esegui(["pgrep", "-u", chi], tetto=15)
        if (viva is not None and viva.returncode != 0) and \
           (proc is not None and proc.returncode != 0):
            return True
        time.sleep(0.5)
    return False


# ---------------------------------------------------------------------------
def certifica():
    """⛔ The grafted fault in the laboratory: it proves that the judge can say
       GREEN, can say RED, and can say «I do not know».

    ⚠ And it declares what it covers and what it does not.
      COVERS: the measurement of the energy and the three criteria — that a stream of zeros is
      red, that few blocks are red, that sound in bursts is red,
      that a tone at HALF the real level stays GREEN, and that what is not
      PCM returns «I do not know» instead of zero.
      ⛔ DOES NOT COVER: that the session is born, that the sink opens, that `pw-play`
      plays.  ⇒ That is covered by the real round, and its grafted fault is
      `--senza-sorgente`.
    """
    def onda(ampiezza, quanti, hertz=440.0):
        fuori = []
        passo = 2.0 * math.pi * hertz / PCM_FREQUENZA
        i = 0
        for _ in range(quanti):
            b = bytearray()
            for _k in range(PCM_FOTOGRAMMI):
                v = int(round(ampiezza * 32767 * math.sin(passo * i)))
                b += struct.pack("<hh", v, v)
                i += 1
            fuori.append((PCM_CODEC, bytes(b)))
        return fuori

    def zeri(quanti):
        return [(PCM_CODEC, b"\x00" * PCM_BYTE_BLOCCO) for _ in range(quanti)]

    # ⭐ The amplitudes are NOT invented: they are the same that ran on
    #   real sessions (the calibration table, at the top).  ⇒ The
    #   certification and the real round speak of the same yardstick.
    VERO = 1.0

    casi = [
        # (name, blocks, expected, piece of the expected reason)
        ("the default tone (amplitude 1.0)", onda(VERO, 1000), True, "RMS"),
        # ⛔⛔ The case that keeps the threshold HONEST — the equivalent of C1's «shifted
        #    colours» (§4.1): the nearest real point from ABOVE must
        #    stay green, or the threshold is too tight and in two weeks
        #    the net gets thrown away.  `[M]` at 0.02 the wire gave RMS 463.1.
        ("⭐ amplitude 0.02 — the nearest real point from ABOVE: MUST stay GREEN",
         onda(0.02, 1000), True, "RMS"),
        # ⛔ And the nearest real point from BELOW: `[M]` at 0.01 the wire gave
        #    RMS 231.2, and the real mesh said RED.  ⇒ The border is
        #    crossed in both directions.
        ("⛔ amplitude 0.01 — the nearest real point from BELOW",
         onda(0.01, 1000), False, "SILENZIO"),
        ("⛔ NOTHING arrived", [], False, "NIENTE"),
        # ⭐⭐ THE CASE THAT JUSTIFIES THE WHOLE ENERGY MEASUREMENT: bytes that
        #    arrive, and they are silence.  A judge that counted the bytes
        #    would say green here.
        ("⛔ 4 000 blocks of ZEROS — bytes that arrive and it is silence",
         zeri(4000), False, "SILENZIO"),
        ("⛔ near-silence (amplitude 0.001)", onda(0.001, 1000), False, "SILENZIO"),
        ("⛔ only 50 blocks of full tone", onda(VERO, 50), False, "POCHI"),
        # ⛔ Global RMS in order (the tone is loud), but the sound is there for a
        #    quarter of the time: without the third criterion this would pass.
        ("⛔ tone for a quarter of the time, zeros for the rest",
         onda(VERO, 1000) + zeri(3000), False, "A TRATTI"),
        ("Opus codec ⇒ I do not know", [(1, b"\x00" * 100)] * 400, None, "not PCM"),
        ("codec that CHANGES ⇒ I do not know",
         onda(VERO, 200) + [(1, b"\x00" * 100)] * 200, None, "CHANGES"),
        ("payload of odd length ⇒ I do not know",
         [(PCM_CODEC, b"\x00" * 961)] * 400, None, "ODD"),
        ("the blocks file could not be read ⇒ I do not know", None, None, "I could not"),
    ]

    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ THE SECOND HALF — «was the fault seen?» (§1.52).
    #
    # ⛔ It was not there before 27 Aug 2026, and it is the case that would have caught the
    #    defect: the TWO populations measured on GNOME — 41 blocks with the
    #    normal round, 0 with the grafted fault — are both RED, ⇒ a
    #    predicate that looks at the colour confuses them.
    # ⚠ 41 is measured: `[M]` §7-bis.18, GNOME box, against ~4 878 elsewhere.
    # ═══════════════════════════════════════════════════════════════════════
    casi_guasto = [
        ("⭐ without source: ZERO blocks ⇒ the fault WAS SEEN", [], True),

        ("⛔⛔ GNOME's 41 LOUD blocks: red for POCHI ⇒ ⛔ NOT «seen»",
         onda(VERO, 41), False),

        ("⛔ 4 000 blocks of zeros: red for SILENZIO ⇒ ⛔ NOT «seen»",
         zeri(4000), False),

        ("⛔ the healthy round is green ⇒ ⛔ NOT «seen»", onda(VERO, 1000), False),

        ("⛔ «I do not know» is not «seen» (§4.5)", None, False),
    ]

    print("== certification of C5's judge ==")
    print("   the yardstick: RMS threshold %.0f of %.0f (%.1f %% f.s., %.0f dBFS) · "
          "at least %d blocks · at least %.0f %% above threshold"
          % (SOGLIA_RMS, FONDO_SCALA, 100 * SOGLIA_RMS / FONDO_SCALA,
             in_db(SOGLIA_RMS), MIN_BLOCCHI, 100 * MIN_FRAZIONE))
    print()
    guai = 0
    for nome, blocchi, atteso, pezzo in casi:
        v, m = giudica(blocchi)
        bene = (v is atteso) and (pezzo in (m["motivo"] or ""))
        print("  %s  %-52s  verdict=%-5s (expected %-5s)  %s"
              % ("OK " if bene else "NO ", nome, v, atteso,
               (m["motivo"] or "")[:72]))
        if not bene:
            guai += 1
    print()
    print("  ⛔ and the grafted fault is read on the DIFFERENCE, not on the colour:")
    for nome, blocchi, atteso in casi_guasto:
        v, m = giudica(blocchi)
        avuto = guasto_visto(v, m)
        bene = avuto is atteso
        print("  %s  %-52s  seen=%-5s (expected %-5s)  %s"
              % ("OK " if bene else "NO ", nome, avuto, atteso,
                 (m["motivo"] or "")[:40]))
        if not bene:
            guai += 1
    # ═══════════════════════════════════════════════════════════════════════
    # ⭐⭐ AND THE CEILING IS CERTIFIED LIKE A THRESHOLD — ⛔ or it is a number that
    #     nobody checks any more (`LEZIONI.md` §1.45).  ⚠ It was not there before
    #     27 Aug 2026.
    # ⚠ And the margin sits on the WORST ever measured, not on today's
    #   spread: three measurements on a machine at rest say nothing about a
    #   loaded box.  ⇒ See `TETTO_NASCITA` at the top.
    # ⛔ And there is a second demand, and it is the one C5 had got wrong: the
    #   client must STILL BE ATTACHED when the sink appears.
    # ═══════════════════════════════════════════════════════════════════════
    MISURE_SANE = (1.105, 0.998, 0.957)   # `[M]` 27 Aug 2026, cured box
    SINK_MISURATO = 3.0                   # `[M]` 26 Aug 2026, healthy boxes
    PEGGIORE_MAI_VISTA = 13.0             # `[M]` 26 Aug 2026, loaded box
    MARGINE = 2.0
    serve = PEGGIORE_MAI_VISTA * MARGINE
    tetto_ok = TETTO_NASCITA >= serve
    resta_ok = (TETTO_NASCITA + FINESTRA_MISURA) >= TETTO_NASCITA + 1.0
    if not tetto_ok or not resta_ok:
        guai += 1
    print()
    print("  %s  the ceiling covers the slowest birth EVER measured: "
          "%.0f s × %.0f = %.0f s ⇒ TETTO_NASCITA %.0f s"
          % ("OK " if tetto_ok else "NO ", PEGGIORE_MAI_VISTA, MARGINE,
             serve, TETTO_NASCITA))
    print("      ⇒ and that is %.1f times the measured sink (%.0f s) and %.0f times "
          "today's healthy phenomenon (%.3f s)"
          % (TETTO_NASCITA / SINK_MISURATO, SINK_MISURATO,
             TETTO_NASCITA / max(MISURE_SANE), max(MISURE_SANE)))
    print("  %s  the client stays attached %.0f s = ceiling %.0f + measuring "
          "window %.0f ⇒ it is still there when the sink appears"
          % ("OK " if resta_ok else "NO ", TETTO_NASCITA + FINESTRA_MISURA,
             TETTO_NASCITA, FINESTRA_MISURA))

    # ⭐⭐ THE ADMISSION CASES — ⛔ the ones that were not there before today.
    #    The predicate lives in C1 and is certified with C1's cases: ⛔ a
    #    copy of the cases here would be a second place to diverge from (§1.47).
    print()
    guai_amm, quanti_amm = casa_dell_ammissione().certifica_ammissione("C5")
    guai += guai_amm

    # ⭐⭐ AND THE CARD GROUPS CASES — ⛔ the other case that was missing:
    #    a tenant without the groups of the nodes ⇒ «I could not look», ⛔
    #    never red.  They live in C1 with the step they certify.
    print()
    guai_gr, quanti_gr = casa_dell_ammissione().certifica_gruppi("C5")
    guai += guai_gr

    # ⚠ `+ 2` and not `+ 1`: the checks printed above are TWO (the ceiling and
    #   the attach time).  ⛔ The count said 1 from the day the
    #   second was born, ⇒ the mesh declared one case fewer than those
    #   it really did — a count that does not add up is a count that cannot
    #   be quoted.
    quanti = len(casi) + len(casi_guasto) + quanti_amm + quanti_gr + 2
    print()
    if guai:
        print("⛔ the judge is NOT reliable: %d cases out of %d wrong"
              % (guai, quanti))
        return 1
    print("⭐ %d cases out of %d: the judge can say GREEN, can say RED and can say "
          "«I do not know»" % (quanti, quanti))
    print("⛔ and it can distinguish «the injection bit» from «I was already red» (§1.52)")
    print("⚠ and this certification covers the MEASUREMENT, not the session: that "
          "is covered by the real round with `--senza-sorgente`")
    return 0


# ---------------------------------------------------------------------------
def main():
    p = argparse.ArgumentParser()
    p.add_argument("--utente", default="c5u1",
                   help="⛔ a NEW tenant: it is deleted and recreated at every "
                        "round. «From zero» includes «from zero with respect to myself "
                        "of yesterday» (LEZIONI.md, C1's cure)")
    p.add_argument("--parola", default="provanic2026")
    p.add_argument("--porta", type=int, default=8512)
    p.add_argument("--indirizzo", default="127.0.0.1")
    p.add_argument("--cliente", default="/opt/remotix/01-b3-cliente.py")
    p.add_argument("--registro", default="/var/lib/rete11/registro.log")
    p.add_argument("--resta", type=float, default=TETTO_NASCITA + FINESTRA_MISURA,
                   help="how long the client stays attached collecting sound. "
                        "⭐ = TETTO_NASCITA (26 s) + FINESTRA_MISURA (25 s) = "
                        "51 s: the sink cannot appear before the session "
                        "is born, and the client must STILL BE ATTACHED "
                        "when it appears — `[M]` it is the reason for the 41 blocks "
                        "instead of ~4 878, the client had already gone away")
    p.add_argument("--ampiezza", type=float, default=1.0,
                   help="amplitude of the wave, 0..1 of full scale. ⭐ It serves the "
                        "CALIBRATION: it is with this that the two "
                        "populations written at the top were measured")
    p.add_argument("--hertz", type=float, default=440.0)
    p.add_argument("--senza-sorgente", action="store_true",
                   help="⛔ THE GRAFTED FAULT: nothing is played. The outcome is "
                        "read BACKWARDS — here green is a red")
    p.add_argument("--attesa-ammesso", type=float, default=45.0,
                   help="how long to wait for the client to say AMMESSO. "
                        "Expired: «I could not look», NEVER green. "
                        "⚠ It stays 45 s on purpose: the ADMISSION is the RCP "
                        "handshake and comes BEFORE the session — the delay "
                        "of the stage (26 s) is covered by `--attesa-sink`, not "
                        "this. ⛔ Confusing them would mean waiting for the "
                        "stage in the wrong window")
    p.add_argument("--attesa-sink", type=float, default=TETTO_NASCITA,
                   help="how long to wait for the «remotix» sink to appear. "
                        "⭐ = TETTO_NASCITA: `[M]` the sink is seen in 3 s and the "
                        "session is born in 1.105 s on the cured box; 26 s "
                        "are the slowest birth ever measured (13 s) × 2 — "
                        "see TETTO_NASCITA at the top")
    p.add_argument("--certifica", action="store_true")
    a = p.parse_args()

    if a.certifica:
        return certifica()

    # ═══ THE TERRAIN — and every missing piece is an «I do not know», never a green ══
    if os.geteuid() != 0:
        print("⛔ it must be run as administrator inside the box (it creates a user)")
        return 2
    if not os.path.exists(a.cliente):
        print("⛔ I cannot find the test client: %s" % a.cliente)
        print("   ⇒ I could not look")
        return 3
    for arnese in ("/usr/bin/pw-play", "/usr/bin/pw-cli"):
        if not os.path.exists(arnese):
            print("⛔ %s is missing (package `pipewire-bin`): without it, I can neither "
                  "make sound nor see the sink" % arnese)
            print("   ⇒ I could not look")
            return 3

    print("== C5 — the sound is there and it is not silence ==")
    print("   NEW tenant «%s» · port %d · I stay attached %.0f s"
          % (a.utente, a.porta, a.resta))
    print("   the yardstick: RMS threshold %.0f of %.0f (%.1f %% f.s., %.0f dBFS) · "
          "at least %d blocks · at least %.0f %% above threshold"
          % (SOGLIA_RMS, FONDO_SCALA, 100 * SOGLIA_RMS / FONDO_SCALA,
             in_db(SOGLIA_RMS), MIN_BLOCCHI, 100 * MIN_FRAZIONE))
    if a.senza_sorgente:
        print("   ⛔⛔ GRAFTED FAULT: the source is NOT switched on. "
              "The outcome is read backwards.")
    else:
        print("   the source: wave at %.0f Hz, amplitude %.4f, played inside the "
              "product's «%s» sink" % (a.hertz, a.ampiezza, NOME_SINK))
    print()

    chi = a.utente
    blocchi_file = "/tmp/c5-%s-blocchi.jsonl" % chi
    cliente_log = "/tmp/c5-%s-cliente.log" % chi
    onda_file = "/tmp/c5-%s-onda.wav" % chi
    tono = None
    esito = 3

    try:
        # ═══ THE TENANT — it is DELETED before creating it ═════════════════
        # ⛔ «From zero» includes «from zero with respect to myself of yesterday»: an
        #    `id -u X || useradd X` would make the tenant new only the FIRST
        #    time this bench runs in its life.
        if not sgombra(chi):
            print("  ⚠ «%s» of the previous round did not go away: the field "
                  "is not free, and I say so instead of pretending nothing happened" % chi)
        esegui(["/bin/sh", "-c",
                "userdel -r %s 2>/dev/null; rm -rf /home/%s" % (chi, chi)],
               tetto=60)
        # ⛔ The card's groups are no longer in here: `usermod -aG
        #    video,render` nailed down two names and did not read back.  They are given by
        #    the tool, below, which READS them from the nodes and then VERIFIES.
        f = esegui(["/bin/sh", "-c",
                    "useradd -m -s /bin/bash %s "
                    "&& printf '%s:%s\n' | chpasswd" % (chi, chi, a.parola)],
                   tetto=60)
        if f is None or f.returncode != 0:
            print("⛔ I could not create the tenant «%s»: %s"
                  % (chi, (f.stderr.strip()[:120] if f else "the command did not start")))
            print("   ⇒ I could not look")
            return 3
        # ⛔⛔ AND WITHOUT THE CARD'S GROUPS WE DO NOT MEASURE: `[M]` the session
        #     is born blind (0 of 4), and C5 would measure the sound of a desktop
        #     that does not exist.  ⇒ 3, ⛔ never red (§1.51).
        e_gr, perche_gr = garantisci_i_gruppi(chi, prefisso="  ")
        if e_gr != 0:
            # ⭐ The tool's outcome is propagated, not a nailed-down 3: «I could not
            #   look» (3) and «wrong usage» (2) have different names.
            print("  %s" % perche_gr)
            print("  ⇒ I do not measure — ⛔ and it is NOT a red (§4.5): outcome %d"
                  % e_gr)
            return e_gr
        # ⛔ `esegui` returns `None` on expiry: without this guard it was an
        #    `AttributeError` ⇒ traceback ⇒ Python exits **1** ⇒ the hook reads
        #    RED, and it would be a fault of the BENCH accusing the product
        #    (`LEZIONI.md` §1.51).  ⚠ Low probability, wrong shape.
        letto = esegui(["id", "-u", chi])
        if letto is None or letto.returncode != 0 or not letto.stdout.strip():
            print("⛔ I created «%s» but I cannot read its uid: it is the "
                  "BENCH that does not answer, not the product" % chi)
            print("   ⇒ I could not look")
            return 3
        uid = int(letto.stdout.strip())
        print("  tenant «%s» created, uid %d" % (chi, uid))

        # ═══ THE WAVE — and it is rewritten at every round ═════════════════
        for vecchio in (blocchi_file, cliente_log, onda_file):
            try:
                os.unlink(vecchio)
            except OSError:
                pass
        if not a.senza_sorgente:
            # ⚠ Longer than needed, and the margin is declared: the
            #   tone starts when the sink is seen and must last beyond the end
            #   of the client.  ⛔ If it ended earlier, the tail of the round would be
            #   silence and the fraction would collapse — a red of the BENCH, not of the
            #   product (`LEZIONI.md` §1.45).
            # ⚠ And this margin protects the TAIL, not the HEAD: between
            #   the admission and the appearance of the sink there are seconds of silence
            #   inside the client's window (up to ~3 s, and more if the box is loaded), and no
            #   margin covers them.  ⇒ Today they do not bite because `src/audio.c` does not
            #   send the mute blocks — see `MIN_FRAZIONE` at the top.  ⛔ It is
            #   a dependency between this mesh and an option of the product, and
            #   it is written here instead of being discovered on the day of the red.
            durata = a.resta + 15.0
            picco = scrivi_onda(onda_file, durata, a.ampiezza, a.hertz)
            print("  wave written: %.0f s at %.0f Hz, peak at the source %d of "
                  "32767 (%s)" % (durata, a.hertz, picco, onda_file))

        # ═══ THE CLIENT — PCM is asked for, or the energy cannot be measured ══
        with open(cliente_log, "w") as reg:
            cli = subprocess.Popen(
                ["python3", "-u", a.cliente,
                 "--indirizzo", a.indirizzo, "--porta", str(a.porta),
                 "--utente", chi, "--parola", a.parola,
                 "--audio-codec", "pcm",
                 "--audio-scrivi", blocchi_file,
                 "--resta", str(a.resta)],
                stdout=reg, stderr=subprocess.STDOUT)

        # ⛔ We wait for the «AMMESSO» EVENT, not for the clock.
        # ⛔⛔ And we wait for the LINE, not the word: `"AMMESSO" in …` would be
        #     true also on the two REFUSAL messages ⇒ this loop would have
        #     exited **at once and happy** precisely when the server had
        #     turned the client away (§1.44).  See `e_stato_ammesso()` at the top.
        # ⭐ The loop exits only on `True`.  ⚠ `False` is NOT an exit
        #   condition: in the first tenths of a second the client has already printed
        #   «→ CIAO» and has not been admitted yet — it would be an early
        #   exit on a session that is still being born.  ⇒ Whoever exits
        #   early on the refusal is the client itself, which dies (`sys.exit(2)`),
        #   and the `cli.poll()` below catches it.
        ammesso = None
        scadenza = time.time() + a.attesa_ammesso
        while time.time() < scadenza:
            try:
                with open(cliente_log, "r", errors="replace") as h:
                    ammesso = e_stato_ammesso(h.read())
                    if ammesso is True:
                        break
            except OSError:
                pass
            if cli.poll() is not None:
                break
            time.sleep(0.5)
        if ammesso is not True:
            # ⛔ «Not admitted» on its own is a silence: the REASON is carried
            #    next to the symptom (C1's cure).
            motivo = "?"
            try:
                with open(cliente_log, "r", errors="replace") as h:
                    for riga in reversed(h.read().strip().splitlines()):
                        riga = riga.strip()
                        if riga and not riga.startswith("=="):
                            motivo = riga[:100]
                            break
            except OSError:
                pass
            # ⭐ And the two «no»s are said by name: «turned away» and «silent» are not
            #   the same thing, and mixing them is half the defect of §1.44.
            print("  ⛔ %s in %.0f s — why: %s"
                  % ("the client was TURNED AWAY by the server"
                     if ammesso is False
                     else "the client said NOTHING",
                     a.attesa_ammesso, motivo))
            print("\n  ⚠ NOT JUDGING: I did not open the session, so I have no "
                  "way of saying whether the sound would have been there.")
            print("     ⛔ And this is NOT a red: it is outcome 3 (§4.5).")
            return 3
        print("  the client was ADMITTED")

        # ═══ THE SINK — and the three cases are three different outcomes ═══
        #
        # ⛔⛔ AND WE REMEMBER WHETHER PIPEWIRE ANSWERED AT LEAST ONCE, not only
        #     the LAST answer.  ⚠ Until 27 Aug 2026 `visto` was
        #     overwritten at every round, and `sink_c_e` returns `None` when
        #     PipeWire does not answer — which in the first seconds necessarily
        #     happens, because `/run/user/<uid>` is not there yet.  ⇒ The outcome was
        #     decided by the last shot:
        #       · it answers «no sink» for the whole wait and at the last is silent
        #         ⇒ **3** instead of **1** (a product red lost);
        #       · it is dead for the whole wait and answers at the last
        #         ⇒ **1** instead of **3** (a red INVENTED on the product).
        #     ⛔ They are the two outcomes this mesh declares it keeps separate
        #     on purpose (see the top).
        visto = None
        ha_risposto = False
        t0 = time.time()
        scadenza = t0 + a.attesa_sink
        while time.time() < scadenza:
            visto = sink_c_e(chi, uid)
            if visto is not None:
                ha_risposto = True
            if visto:
                break
            time.sleep(1.0)
        if not ha_risposto:
            print("  ⛔ the PipeWire of «%s» did not answer EVEN ONCE "
                  "in %.0f s" % (chi, a.attesa_sink))
            print("\n  ⚠ NOT JUDGING: it is the terrain that does not speak, not the "
                  "product.  ⛔ And it is not a red (§4.5).")
            return 3
        if not visto:
            print("  ⛔ PipeWire answered (at least once), and the «%s» sink "
                  "is NOT there after %.0f s" % (NOME_SINK, a.attesa_sink))
            print("\n  ⛔⛔ RED — the product did not open the sound path.")
            print("     ⇒ `src/suono.c` creates a `support.null-audio-sink` "
                  "called «%s»: it is not there." % NOME_SINK)
            return 1
        print("  ⭐ the «%s» sink is there after %.0f s" % (NOME_SINK, time.time() - t0))

        # ═══ THE SOURCE ═══════════════════════════════════════════════════
        if a.senza_sorgente:
            print("  ⛔ GRAFTED FAULT: I play nothing")
        else:
            tono = subprocess.Popen(
                ["runuser", "-u", chi, "--", "env",
                 "XDG_RUNTIME_DIR=/run/user/%d" % uid,
                 "pw-play", "--target=%s" % NOME_SINK, onda_file],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("  the source plays (pw-play on «%s»)" % NOME_SINK)

        # ⛔ The ceiling governs the WAIT FOR THE CLIENT, not the work: if the client
        #    has already written its blocks, they are judged anyway — the
        #    RESULT is judged, not the exit code (`LEZIONI.md` §1.50).
        try:
            cli.wait(timeout=a.resta * 3 + 60)
        except subprocess.TimeoutExpired:
            print("  ⚠ the client did not exit by itself: I close it and look at "
                  "what it wrote")
            cli.kill()
            cli.wait(timeout=30)

        # ═══ THE JUDGEMENT ════════════════════════════════════════════════
        blocchi = leggi_blocchi(blocchi_file)
        verdetto, m = giudica(blocchi)
        print()
        print("  %s" % riga_misure(m))
        # ⭐ The second witness: what the PRODUCT says it sent.
        #   ⚠ It is PRINTED and not judged — it is a comparison for whoever diagnoses,
        #     not a criterion.
        for riga in coda_registro(a.registro, chi):
            print("  [log] %s" % riga)
        print("  ⇒ %s" % (m["motivo"] or "—"))

        # ═══ And the margin, which is ALWAYS printed ══════════════════════
        if m["rms"]:
            print("  margin on the threshold: %.2f times (%.1f dB) — ⚠ and it is always "
                  "printed: it is the number that warns BEFORE the threshold becomes "
                  "a false red" % (m["rms"] / SOGLIA_RMS,
                                   in_db(m["rms"]) - in_db(SOGLIA_RMS)))

        print()
        # ═══ And with the grafted fault the outcome is read BACKWARDS ══════
        if a.senza_sorgente:
            # ═══════════════════════════════════════════════════════════════
            # ⛔⛔ AND THE COLOUR OF THE VERDICT IS NOT ENOUGH — `LEZIONI.md` §1.52.
            #
            # ⚠ Until 27 Aug 2026 the only predicate here was `verdetto is
            #   False`.  ⛔ But C5 on GNOME is red **on its own**: `[M]`
            #   §7-bis.18, **41 blocks** arrive instead of ~4 878 ⇒ reason
            #   `POCHI`.  And without source **0** arrive ⇒ reason `NIENTE`.
            #   ⇒ Both `False`, ⇒ it exited **0**, ⇒ the hook wrote
            #   `ha_visto_il_guasto: true` **without ever having compared 41 with
            #   0**.  ⛔ The net's certification rested on a defect
            #   of the product, which is §1.52 word for word.
            #
            # ⭐ The cure is the same C9 already has: TWO things are demanded —
            #   the red verdict **and** a measurable difference.  Here the
            #   difference is the count of blocks: without source **ZERO** must
            #   arrive.  ⛔ And it is not a gratuitous demand: the silence cure
            #   of `src/audio.c` (`audio_taci_silenzio`, on by
            #   default) does NOT send the mute blocks — so «no
            #   source» really means «no block».
            # ═══════════════════════════════════════════════════════════════
            quanti = m["blocchi"]
            if guasto_visto(verdetto, m):
                print("⭐ THE GRAFTED FAULT WAS SEEN: without source not a single "
                      "block arrives (%s)" % (m["motivo"] or "")[:60])
                print("   ⇒ this mesh CAN say red on real data, ⭐ and the "
                      "red comes FROM THE FAULT: 0 blocks, not «few».")
                return 0
            if verdetto is False:
                print("⛔⛔ RED, but NOT because of the fault: without source "
                      "%s blocks arrived anyway." % quanti)
                print("    ⇒ %s" % (m["motivo"] or ""))
                print("    ⛔ C5 was ALREADY red on its own, and the injection did not")
                print("      remove anything: saying «the fault was seen»")
                print("      would certify the net on a defect of the PRODUCT")
                print("      (`LEZIONI.md` §1.52).")
                return 1
            if verdetto is None:
                print("⛔ I could not judge: I cannot say whether the fault "
                      "would have been seen")
                return 3
            print("⛔⛔ THE GRAFTED FAULT WAS NOT SEEN: without source "
                  "C5 says GREEN anyway.")
            print("    ⇒ either the sound arrives from somewhere else, or this mesh "
                  "does not look in the right place — and in both cases it cannot "
                  "be trusted.")
            return 1

        if verdetto is None:
            print("  ⚠ NOT JUDGING — %s" % (m["motivo"] or ""))
            print("     ⛔ And this is not a green: it is an outcome of its own (§4.5).")
            return 3
        if verdetto is False:
            print("  ⛔⛔ RED — the sound is not there, or it is silence.")
            print("     %s" % (m["motivo"] or ""))
            return 1
        print("  ⭐ GREEN — the sound arrives at the client and it is NOT silence.")
        print("     ⚠ And C5 green does not mean «the session is fine»: C5 does not "
              "look at a pixel (see the top).")
        return 0

    finally:
        if tono is not None and tono.poll() is None:
            tono.kill()
        sgombra(chi)


def coda_registro(percorso, chi):
    """The PRODUCT's lines about this tenant — ⭐ a second witness.

    ⛔ They are PRINTED and not judged: they are the count of whoever sends, and C5
       judges what ARRIVES.  ⚠ Having both side by side is what makes one
       understand, on the day of the red, on which side of the wire the fault lies.
    """
    fuori = []
    try:
        with open(percorso, "r", errors="replace") as f:
            testo = f.read()
    except OSError:
        return ["⚠ the server log could not be read: %s" % percorso]
    for riga in testo.splitlines():
        if "[%s]" % chi not in riga:
            continue
        if "PEAK" in riga or "silence cure" in riga or "final count" in riga:
            fuori.append(riga.strip()[:200])
    if not fuori:
        return ["⚠ the server log says nothing about «%s»: ⛔ it is not "
                "a zero, it is a silence" % chi]
    return fuori[-3:]


if __name__ == "__main__":
    sys.exit(main())
