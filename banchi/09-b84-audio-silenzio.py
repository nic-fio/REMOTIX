#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b84-audio-silenzio — ⛔⭐⭐ WHAT AUDIO COSTS WHEN THERE IS NO AUDIO.

═══ THE FACT IT IS BORN FROM, AND THE FIRST THING IT REFUTED ═══════════════

The mandate said: *«on a bad network a third of the audio never reaches the
wire»*, `[M]` `09-b77` on `casa-cattiva`, **1 823 blocks refused out of ~5 000**;
and *«an idle session costs 2 463 kbit/s of PCM audio»*, `[M]` `09-b81`.

⛔⛔ **BOTH THOSE NUMBERS ARE IN PCM, AND PCM IS NOT WHAT THE PRODUCT
     NEGOTIATES.**  `[R]` The benches FORCE it on the test client:
     `09-b68:191`, `09-b70:1890`, `09-b71:144`, `09-b77:978`, `09-b81:2294`
     all pass `--audio-codec pcm`.  ⭐ And the log of the user's REAL
     session (port 7920, `/media/REMOTIX/tmp/09c/registro.log`) says
     the opposite, four times out of four:

         negoziato video.codec=hevc video.profondita=8 audio.codec=opus
         ⭐ FASE 7: canale audio ACCESO … — codec 1 (Opus)

     ⇒ The 36 % and the 2 463 kbit/s are properties of **a bench
     configuration**, not of the product.  `[R]` `pagina.html:4727` asks
     `AudioDecoder.isConfigSupported` and declares `opus,pcm` when the engine
     answers yes; PCM stays the base of §4.3 for whoever does not have it.

═══ ⭐⭐⭐ AND WHAT IS REALLY THERE IS MORE SERIOUS, NOT LESS ═══════════════

`[M]` 24 August 2026, REMEASURED with the bench on **a single binary** (port 7981,
binary md5 `6ec170c0…`, 25 s per arm; the first measurement was of 23-24 August
on 7972 with two binaries, and the numbers match).  Session with **Opus**
negotiated and desktop **still** (`suono.c`: `PICCO 0 su 32767`, that is DIGITAL
silence):

  arm     | on the wire   | packets/s   | datagram/s | bytes/packet   | payload
  --------|---------------|-------------|------------|----------------|--------
  OFF     | 557.5 kbit/s  |  48.4       |  48.0      | 1 441          | 1.18 kbit/s
  ON      |   5.7 kbit/s  |   0.5       |   0.0      |  —             | 0.00 kbit/s
                                                              ⇒ **97.3 times**

⇒ **99.8 % of that traffic is padding.**  Every block of silence takes
a WHOLE 1 441-byte packet for 3 bytes of payload.  ⛔ And that
packet is paid for by the **same congestion window as the video**: `[M]` on the
real session the window is 2 888 - 5 704 bytes, that is **two or three
packets**, and the audio asks for fifty a second to say nothing.

⛔⛔ AND HERE THERE WAS A DEDUCED CAUSE, AND IT WAS WRONG.  This line said
    *«because `webtransport.c:1613` writes the datagram with
    `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING`»*.  ⇒ Tried on 24 August: with that
    flag **never** requested the packet stays at 1 441 bytes all the same.  `[R]` What
    fills it is `wt_scrivi()`, which asks for
    `NGTCP2_WRITE_STREAM_FLAG_PADDING` at every stream write and closes the
    packet the datagram had left open.  ⚠ The number was measured,
    the cause was not: ⇒ §PADDING at the bottom of this file, with the table.

⭐ And the cure does NOT touch the sound, measured paired on the scene with the 440 Hz tone
   (PCM, judge of `07-b42`): coverage **1.0000 → 1.0000**, tone purity
   **1.000 → 1.000**, blocks silenced **1 out of 5 002** — and that one is the first
   block of the session, which precedes the first samples of the tone.

⚠ THE PRICE, and it is written: on a scene with sound the client's `mancati` may
  rise (⇒ `[M]` 0 → 2 on the first measurement; 0 → 0 on the remeasurement of 24 August).
  A WANTED gap leaves the same `istante` jump as a lost one, and that
  counter does not tell the two apart.

⭐ THE CURE IS IN `src/audio.c`, AND IT IS BORN OFF (I6): a block in which ALL the
   samples are exactly zero does not become a datagram.  §6.3 puts
   the `istante` inside every block and the receiver puts them back in their absolute
   place ⇒ **a block not sent is a gap, and a gap is silence** —
   which is what that block contained.  It is not an approximation.

⛔ AND THE HALF OF THE CURE THIS BENCH HAD ASKED OF `src/webtransport.c` WAS
   TRIED ON 24 AUGUST 2026 AND **IS NOT DONE**: ⇒ §PADDING, at the bottom of
   this file, with the table and the why.

═══ ⭐⭐⭐ SINCE 24 AUGUST 2026 THE ARMS ARE **A SINGLE BINARY**, AND THE COMPARISON
    HAS BECOME STRONGER ═══════════════════════════════════════════════════

Until 23 August the switch was a COMPILE-TIME one (`-DAUDIO_SILENZIO_PREDEFINITO=1`)
and this bench built **two binaries** from the same tree, with a single `-D` of
difference.  It was the best that could be done then, and it must be said that it was not
free: **two binaries are two suspects**.  Two builds can
diverge because of an `INC` read wrongly, an object left behind, a `make` that
did not redo what I thought — and the difference between the two arms would have
ended up in the wrong column without a red line anywhere.  ⚠ The
bench could only check that the `md5` were DIFFERENT: it could say «they are not
the same file», not «they differ by what I think».

⭐ `DECISIONI.md` §3.1-septies removed that `-D`: the cure is born **ON** in the
   product and is turned off with **`--niente-audio-silenzio`**, which is a command
   line option.

⇒ **The two arms are the SAME IDENTICAL BINARY**, and the only thing that changes is the
  server's command line:

      ON       (no option — it is the product that ships)
      OFF      --niente-audio-silenzio

⛔⭐ **ONE SUSPECT LESS, and it is written because it is a gain of method, not
    a simplification.**  Before, if the two arms had given equal numbers,
    there were two explanations: «the cure is not needed» or «the two binaries were not
    the ones I thought».  Now there is only one.  ⚠ And the md5 is printed all the same, at
    every run: it serves to say WHICH product I measured, no longer to tell the
    arms apart.

⛔⛔ AND WHAT TELLS THE ARMS APART NOW IS **ONLY THE PRODUCT'S LOG** —
    `a_la_cura_ha_parlato()`, which demands `cura_dichiarata` «spenta» in one and
    «accesa» in the other.  With two binaries that predicate was an extra belt;
    with a single binary it is **the only one**, and without it two identical runs with
    the name of two would be indistinguishable from a cure that is not needed.
    ⚠ `LEZIONI.md` E1: «written is not in force».

═══ ⭐ THE QUANTITIES, AND THE ONE THAT COUNTS IS NOT «HOW MANY I THROW AWAY» ══

  1. **`kbit_s`** — the bytes ngtcp2 declares sent, from the product's `rete-quic`
     line.  ⛔ It is not an estimate of mine: it is the transport's counter.
  2. **`pkt_s`** and **`dgram_s`** — packets and datagrams per second.  ⭐ Their
     ratio is the proof of the padding: 50 datagrams in 51 packets means
     «one packet per block».
  3. **`copertura`** — how much of the timeline really received
     samples, counted by `09-b77.scaletta()` on the PCM blocks.  ⭐ It is the
     quantity on which the cure can do harm: if it silenced sound, it would drop.
  4. **`purezza_tono`** — the judge of `07-b42` via `09-b77.purezza_tono()`.

═══ ⛔ AND ON A BAD NETWORK THE CODEC IS NOT ENOUGH — the prediction that did NOT hold ══

`[M]` 24 August 2026, `casa-cattiva` (40±20 ms, 2 % loss), scene with the tone,
25 s per codec, **same `netem` for both**, cure OFF:

  codec | on the wire   | sent    | refused   | ‰ refused   | wire COVERAGE
  ------|---------------|---------|-----------|-------------|-------------------
  PCM   | 1 024.5 kbit/s|  3 135  | **1 880** | **375‰**    | **0.6088**
  Opus  |   366.3 kbit/s|  1 127  |   **126** | **101‰**    | **0.8803**

⭐ The quantity that counts rises: **coverage 0.61 → 0.88**, that is +27 points of
   audio that really reaches the ear, on the same network.
⛔ But the predicate asked for «Opus below 20‰» and gave **RED**: Opus divides the
   refusal by 3.7, **it does not remove it**.  ⇒ The codec is the cure of the COST, not of the
   refusal: even with a tenth of the bytes the window closes all the same.
   The boundary stays where it is and the red stays written.

Usage (from the laptop):
    python3 banchi/09-b84-audio-silenzio.py --certifica    # ⛔ first of all
    python3 banchi/09-b84-audio-silenzio.py terreno
    python3 banchi/09-b84-audio-silenzio.py costruisci     # THE binary (one)
    python3 banchi/09-b84-audio-silenzio.py muto  [--secondi 25]
    python3 banchi/09-b84-audio-silenzio.py tono  [--secondi 25]
    python3 banchi/09-b84-audio-silenzio.py costo [--secondi 25]
    python3 banchi/09-b84-audio-silenzio.py stretta [--profilo casa-cattiva]
    python3 banchi/09-b84-audio-silenzio.py tutto
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

QUI = os.path.dirname(os.path.abspath(__file__))
RADICE = os.path.dirname(QUI)

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ ISOLATION, and it is written BEFORE importing anything: the modules
#    underneath read the environment at import time, not at call time
#    (`LEZIONI.md` §1.26).
# ═══════════════════════════════════════════════════════════════════════════
PORTA = int(os.environ.get("PORTA", "7972"))
UTENTE = os.environ.get("UTENTE", "provanr9")
UID_B = int(os.environ.get("UID_B", "1072"))
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/09nr9-src")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/09nr9")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/09nr9-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/09nr9")
UNITA = os.environ.get("UNITA", "remotix-%d" % PORTA)
PAROLA_UTENTE = os.environ.get("PAROLA_UTENTE", "nr9-audio-2026")
MACCHINA = os.environ.get("MACCHINA", "nicfio@192.168.0.2")
IND = os.environ.get("IND", "192.168.0.2")
FUORI = os.environ.get("FUORI", os.path.join(
    "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
    "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad", "b84"))

# ⛔ The ports that are NOT mine.  They are counted, not touched.
VIETATE = ("7900", "7910", "7920", "7971")
VIETATA_IFACE = "enp7s0"

for k, v in (("PORTA", str(PORTA)), ("UTENTE", UTENTE), ("UID_B", str(UID_B)),
             ("ALBERO", ALB), ("LAV", LAV), ("DENTRO_ALB", DENTRO_ALB),
             ("DENTRO_LAV", DENTRO_LAV), ("FUORI", FUORI), ("IND", IND),
             ("MACCHINA", MACCHINA), ("PAROLA_UTENTE", PAROLA_UTENTE)):
    os.environ[k] = v
os.makedirs(FUORI, exist_ok=True)


def _carica(nome, file_):
    sp = importlib.util.spec_from_file_location(nome, os.path.join(QUI, file_))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


# ⛔ `09-b77` is NOT touched: it is IMPORTED.  It has the tone, the samples judge,
#    the `netem` profiles and 52 green `--certifica` cases — rewriting one
#    line of it would mean having two judges that can diverge.
B77 = _carica("b77", "09-b77-audio-riordino.py")
RETE = B77.RETE            # root(), guasta(), tono_accendi/spegni, guardiano_*
LUCCHETTO = B77.LUCCHETTO

CHI = "09-b84"
# ⛔ ONE binary only, and it is the product's: the arms are made with
#    `OPZIONI_SERVER` (⇒ the header, «one suspect less»).
BINARIO = "%s/src/remotix" % ALB
# ⭐ The command line of each arm, and the ON arm has none.
OPZIONI = {"accesa": "", "spenta": "--niente-audio-silenzio"}


def log(t):  print("\n\033[1m== %s\033[0m" % t)
def ok(t):   print("    \033[1;32mOK\033[0m  %s" % t)
def ko(t):   print("    \033[1;31mNO\033[0m  %s" % t)
def dub(t):  print("    \033[1;33m??\033[0m  %s" % t)
def inf(t):  print("    --  %s" % t)


# ═══════════════════════════════════════════════════════════════════════════
# THE PREDICATES — WRITTEN FIRST, AND THEY ARE FUNCTIONS, NOT PROSE
#
# ⛔ R13: an expectation in prose stays true «on reading» whatever number comes out.  Here
#    every expectation is `(s, a) -> (passa, perche)` — `s` are the numbers of the arm
#    with the cure OFF, `a` those with the cure ON — and `passa=None` means
#    «I refuse to judge», which is an outcome of ITS OWN and not a green.
# ═══════════════════════════════════════════════════════════════════════════
def _p(cond, perche):
    return (bool(cond), perche)


def _muto(perche):
    return (None, perche)


def _c(n, chiave):
    """The value, or `None` if it was not read.  ⛔ `None` is not zero."""
    if not isinstance(n, dict):
        return None
    return n.get(chiave)


def a_il_riempimento_c_e(min_kbit=400.0, max_carico_kbit=5.0):
    """⭐ THE FACT, measured with the OFF arm — which is today's product.

    ⛔ It is also the bench's POSITIVE CONTROL: if the padding does not come out here,
       the stimulus does not stimulate (the desktop was playing, or the session had no
       audio) and the ON arm would prove nothing."""
    def f(s, a):
        k = _c(s, "kbit_s")
        c = _c(s, "carico_kbit_s")
        if k is None or c is None:
            return _muto("I did not read kbit_s (%s) or carico_kbit_s (%s)" % (k, c))
        return _p(k >= min_kbit and c <= max_carico_kbit,
                  "cure OFF: %.1f kbit/s on the wire for %.2f kbit/s of payload "
                  "(expected >= %.0f and <= %.1f)" % (k, c, min_kbit, max_carico_kbit))
    return f


def a_la_cura_taglia(fattore=8.0):
    """⭐ THE PREDICTION THAT CAN FALL: bandwidth drops by at least `fattore`."""
    def f(s, a):
        ks, ka = _c(s, "kbit_s"), _c(a, "kbit_s")
        if ks is None or ka is None:
            return _muto("kbit_s: off=%s on=%s" % (ks, ka))
        if ka <= 0:
            return _p(True, "cure ON: 0 kbit/s (off %.1f)" % ks)
        return _p(ks / ka >= fattore,
                  "%.1f → %.1f kbit/s = %.1f× (expected >= %.0f×)"
                  % (ks, ka, ks / ka, fattore))
    return f


def a_i_datagram_spariscono(tetto_s=2.0):
    """⭐ And it shows at the OTHER end: the client no longer receives blocks."""
    def f(s, a):
        ds, da = _c(s, "dgram_s"), _c(a, "dgram_s")
        if ds is None or da is None:
            return _muto("dgram_s: off=%s on=%s" % (ds, da))
        return _p(ds >= 40.0 and da <= tetto_s,
                  "datagrams per second: %.1f → %.1f (expected >= 40 and <= %.1f)"
                  % (ds, da, tetto_s))
    return f


def a_la_cura_ha_parlato():
    """⛔ «I turned it on» is not «it did it»: the PRODUCT's log must say
       that the cure is on AND that it silenced some blocks.  ⚠ Without that, a wrong
       binary would give two identical runs with the name of two."""
    def f(s, a):
        if _c(a, "cura_dichiarata") != "accesa":
            return _p(False, "the log of the ON arm declares «%s»"
                             % _c(a, "cura_dichiarata"))
        if _c(s, "cura_dichiarata") != "spenta":
            return _p(False, "the log of the OFF arm declares «%s»"
                             % _c(s, "cura_dichiarata"))
        t = _c(a, "taciuti")
        if t is None:
            return _muto("the log does not carry the digital silence line")
        return _p(t > 0, "blocks silenced by the ON arm: %s (expected > 0)" % t)
    return f


def a_il_suono_non_si_tocca(tolleranza=0.02):
    """⛔⛔ THE CHECK WORTH MORE THAN ALL: on the scene with the TONE the cure must
        change NOTHING — the tone is never digital zero.

    ⚠ If this says red, the cure eats sound and does not go out the door."""
    def f(s, a):
        cs, ca = _c(s, "copertura"), _c(a, "copertura")
        ps, pa = _c(s, "purezza_tono"), _c(a, "purezza_tono")
        if cs is None or ca is None:
            return _muto("coverage: off=%s on=%s" % (cs, ca))
        if abs(cs - ca) > tolleranza:
            return _p(False, "coverage %.4f → %.4f: the cure removed sound"
                             % (cs, ca))
        if ps is None or pa is None:
            return _p(True, "coverage %.4f ≈ %.4f (the tone was not judged)"
                            % (cs, ca))
        return _p(abs(ps - pa) <= tolleranza * 5,
                  "coverage %.4f ≈ %.4f · tone %.3f ≈ %.3f" % (cs, ca, ps, pa))
    return f


def a_col_tono_tace_solo_il_primo(tetto=2):
    """⛔ THE DIRECT COUNTER-PROOF: with the tone on the cure must not bite.

    ⛔⭐ AND THE BOUNDARY IS NOT ZERO, AND IT IS A MEASUREMENT THAT CORRECTED THE BENCH —
        `[M]` 24 August 2026.  The predicate asked for `taciuti == 0` and gave
        RED with `taciuti = 1`.  The log says which:

          09:10:25.701  ⭐ PCM opened …
          09:10:25.731  ⭐ DIGITAL silence: 1 blocks not sent of 1 in

        ⇒ It is the **first block of the session**, thirty milliseconds after the
        encoder opened and before the tone's samples had
        crossed PipeWire.  ⚠ It is not the cure eating sound: it is that
        at the start there is no sound yet.
    ⛔ The boundary stays TIGHT (2 out of ~5 000) on purpose: if the cure started to
       really silence, this predicate would see it at once."""
    def f(s, a):
        t = _c(a, "taciuti")
        e = _c(a, "entrati_cod")
        if t is None:
            return _muto("the log does not carry the cure's count at closing")
        return _p(t <= tetto,
                  "blocks silenced with the tone on: %s out of %s in "
                  "(expected <= %d: only those preceding the first samples)"
                  % (t, e, tetto))
    return f


def a_il_prezzo_si_dichiara():
    """⚠ IT IS NEITHER A GREEN NOR A RED: it is the price, and it is written.

    A wanted gap has, on the receiving side, the same face as a loss:
    the client's `mancati` grow.  ⛔ Declaring it here is what prevents
    someone tomorrow from reading that number as a network fault."""
    def f(s, a):
        return _muto("PRICE: `mancati` %s → %s.  A silenced block leaves the "
                     "same `istante` jump as a lost one: the number does not "
                     "tell the two apart, and from today it must be read knowing it"
                     % (_c(s, "mancati"), _c(a, "mancati")))
    return f


def a_opus_costa_meno_del_pcm(fattore=10.0):
    """⭐ THE REFUTATION, in one number: the audio payload in PCM against Opus.

    ⛔ The PAYLOAD (the bytes of §6.3) is compared, not the bytes on the wire: on the wire the
       padding evens them out, and that is exactly the defect this bench
       found — confusing the two would say «PCM and Opus cost the same»."""
    def f(p, o):
        cp, co = _c(p, "carico_kbit_s"), _c(o, "carico_kbit_s")
        if cp is None or co is None or co <= 0:
            return _muto("carico_kbit_s: pcm=%s opus=%s" % (cp, co))
        return _p(cp / co >= fattore,
                  "audio payload: PCM %.1f kbit/s against Opus %.2f = %.0f× "
                  "(expected >= %.0f×)" % (cp, co, cp / co, fattore))
    return f


def a_il_pcm_si_fa_rifiutare(minimo=100):
    """⛔ THE POSITIVE CONTROL OF THE NARROW NETWORK: with PCM the refusal is there.

    ⚠ If PCM does not get refused, the profile does not bite and the comparison with
      Opus proves nothing — it would be the same run twice."""
    def f(p, o):
        r = _c(p, "rifiutati_server")
        if r is None:
            return _muto("the log does not carry the server's refused count")
        return _p(r >= minimo,
                  "PCM: %s blocks refused by ngtcp2 (expected >= %d)" % (r, minimo))
    return f


def a_opus_regge_dove_il_pcm_cede(tetto_permille=20):
    """⭐ THE PREDICTION: on the SAME `netem`, Opus gets refused in a
       negligible fraction of what PCM gets refused.

    ⛔⛔ AND THE PREDICTION **DID NOT HOLD** — `[M]` 24 August 2026, `casa-cattiva`,
        scene with the tone, 25 s per codec, same `netem` for both:

          PCM   3 135 sent · 1 880 refused = **375‰**
          Opus  1 127 sent ·   126 refused = **101‰**

        ⇒ Opus divides the refusal by **3.7**, it does not remove it.  The 20‰ boundary
        was mine and the measurement refuted it: **it is left where it is** and the
        red is written, instead of moving it until it passes (`LEZIONI.md` §2.3).
        ⚠ The fact that remains: even with a tenth of the bytes the window closes
        all the same, so the codec **is not the cure of the refusal** — it is the cure
        of the cost.  The cure of the refusal, if there is one, lies in the transport."""
    def f(p, o):
        rp, sp = _c(p, "rifiutati_server"), _c(p, "spediti_server")
        ro, so = _c(o, "rifiutati_server"), _c(o, "spediti_server")
        if None in (rp, sp, ro, so) or (sp + rp) <= 0 or (so + ro) <= 0:
            return _muto("server counts: pcm=%s/%s opus=%s/%s" % (rp, sp, ro, so))
        fp = 1000.0 * rp / (sp + rp)
        fo = 1000.0 * ro / (so + ro)
        return _p(fo <= tetto_permille,
                  "refused: PCM %.0f‰ against Opus %.0f‰ (expected Opus <= %d‰)"
                  % (fp, fo, tetto_permille))
    return f


def a_la_copertura_risale(guadagno=0.10):
    """⭐⭐ THE QUANTITY THAT COUNTS — how much of the PRODUCED audio really arrives.

    ⛔⭐ AND IT IS NOT THE SAMPLES' `copertura`, and the reason is that that one is
        computed only on PCM (`09-b77.scaletta()` skips the blocks that are not
        codec 2, and this bench has no Opus decoder).  Comparing the
        PCM samples' coverage with **nothing** would give «not judged»
        precisely on the mandate's question.

    ⭐ `copertura_filo` = **blocks the network delivered to the client** divided by
       **blocks the server produced** (sent + refused + dropped).
       ⚠ The network's loss is in there too, and it is declared: the two arms
       sit under the SAME `netem`, so the difference between them still belongs to
       whoever gets refused — but the number alone does not separate the two causes.
       ⛔ For that there is `a_opus_regge_dove_il_pcm_cede`, which looks at the
       refusals only; this one looks at what reaches the ear."""
    def f(p, o):
        cp, co = _c(p, "copertura_filo"), _c(o, "copertura_filo")
        if cp is None or co is None:
            return _muto("copertura_filo: pcm=%s opus=%s" % (cp, co))
        return _p(co - cp >= guadagno,
                  "wire coverage: PCM %.4f → Opus %.4f (+%.4f, expected >= +%.2f)"
                  % (cp, co, co - cp, guadagno))
    return f


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT TALKS TO THE TEST MACHINE
# ═══════════════════════════════════════════════════════════════════════════
def root(comando, tetto=300):
    return RETE.root(comando, tetto)


def righe_registro():
    rc, out, _ = root("wc -l < %s/registro.log 2>/dev/null || echo 0" % LAV)
    try:
        return int(out.strip())
    except Exception:
        return 0


R_RETE = re.compile(
    r"rete-quic \S+ da_ms=(\d+).*?spediti=(\d+) spediti_d=(\d+) "
    r"byte_spediti=(\d+).*?dgram_ok=(\d+)")


def rete_del_giro(riga0):
    """⭐ THE BYTES ON THE WIRE ARE TOLD BY THE PRODUCT, not an estimate of mine.

    The `rete-quic` line carries `byte_spediti` (cumulative per connection) and
    `da_ms` (the TRUE interval between one line and the next).  ⇒ The bandwidth is the
    difference between the first and the last line of the window, divided by the sum
    of the `da_ms` — not by the time I believed I had waited.

    ⛔ And it is read only from `riga0` on, so it belongs to THIS run.
    ⚠ Fewer than three lines: `None` is returned, not zero (`CODER.md` §3.10)."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                      "'rete-quic '" % (riga0 + 1, LAV))
    righe = []
    for r in out.split("\n"):
        m = R_RETE.search(r)
        if m:
            righe.append(tuple(int(x) for x in m.groups()))
    if len(righe) < 3:
        return {"esito": "NIENTE DA LEGGERE — %d «rete-quic» lines in this "
                         "run (3 are needed)" % len(righe), "righe": len(righe)}
    # ⛔ The FIRST line is discarded: its `da_ms` also covers the start of the
    #    connection, and the start is not the steady state I want to measure.
    ms = sum(r[0] for r in righe[1:])
    if ms <= 0:
        return {"esito": "sum of da_ms is zero", "righe": len(righe)}
    return {
        "righe": len(righe),
        "secondi": round(ms / 1000.0, 2),
        "pkt_s": round((righe[-1][1] - righe[0][1]) * 1000.0 / ms, 2),
        "kbit_s": round((righe[-1][3] - righe[0][3]) * 8.0 / ms, 2),
        "dgram_s": round((righe[-1][4] - righe[0][4]) * 1000.0 / ms, 2),
        "byte_per_pkt": (None if righe[-1][1] == righe[0][1] else
                         round((righe[-1][3] - righe[0][3]) /
                               float(righe[-1][1] - righe[0][1]), 1)),
    }


def conti_del_server(riga0):
    """⛔ «The network lost it» and «the server never sent it» give the same
       number on the client's side.  Here the SERVER's count is read."""
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio of .*final "
                      "count' | tail -1" % (riga0 + 1, LAV))
    r = out.strip()
    if not r:
        return {"esito": "NIENTE DA LEGGERE — no «final count»"}
    m = re.search(r"(\d+) blocks sent, (\d+) dropped.*?(\d+) refused.*?"
                  r"(\d+) DEFERRED", r)
    if not m:
        return {"esito": "line found but unreadable", "riga": r[:160]}
    c = re.search(r"codec (\d+)\s*$", r)
    return {"spediti": int(m.group(1)), "buttati": int(m.group(2)),
            "rifiutati": int(m.group(3)), "rimandati": int(m.group(4)),
            "codec": (int(c.group(1)) if c else None)}


def cura_del_registro(riga0):
    """⛔ THE SWITCH IS READ FROM THE PRODUCT'S LOG, not from what I
       believe I turned on.  ⚠ `audio.c` writes the line even when the cure
       is OFF, on purpose: «the cure is not there» and «the cure is there and did
       nothing» must have two different faces (`CODER.md` §3.10)."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                      "'digital silence cure' | tail -1" % (riga0 + 1, LAV))
    dett = out.strip()
    # ⛔⛔ AND THE WHOLE SENTENCE IS SEARCHED, NOT THE WORD — `[M]` 24 August 2026, and
    #     this bench would have fallen for it.  Since 24 August the line of the OFF
    #     arm contains *«⚠ And it is NOT the default: since 24 August it is born
    #     ON»*: an `if "ON" in dett` would have read **on** on an
    #     OFF arm, that is it would have declared in force the opposite of
    #     what was in force — and `a_la_cura_ha_parlato()`, which is the ONLY
    #     belt left now that the binaries are just one, would have given green to
    #     two wrong arms.
    # ⇒ It is anchored to the two sentences the product writes to SAY the state, and not
    #   to a word that also appears in the explanation (`audio.c:212`).
    stato = None
    if "OFF by hand" in dett:
        stato = "spenta"
    elif "⭐ ON" in dett:
        stato = "accesa"
    # ⛔ THE EXACT COUNT IS THE ONE AT CLOSING, not the one of the line
    #    inside: that one comes out at the first block and then one every thousand, so it says
    #    «at least N».  ⚠ Reading that one and calling it `taciuti` would be a number
    #    that looks measured — `[M]` 24 August 2026: 1 249 blocks silenced
    #    printed «1000».
    rc, out2, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                       "'silence cure count' | tail -1" % (riga0 + 1, LAV))
    m = re.search(r"(\d+) blocks muted of (\d+) in, (\d+) out", out2)
    return {"cura_dichiarata": stato,
            "taciuti": (int(m.group(1)) if m else None),
            "entrati_cod": (int(m.group(2)) if m else None),
            "usciti_cod": (int(m.group(3)) if m else None),
            "riga": dett[:120]}


DA_LEGGERE = {
    "sul_filo":   r"on wire\s+(\d+)",
    "ricevuti":   r"·\s*received\s+(\d+)\s*·",
    "consegnati": r"delivered\s+(\d+)",
    "mancati":    r"missed\s+(\d+)",
    "carico":     r"·\s*(\d+)\s+bytes of payload",
    "codec_cli":  r"bytes of payload\s*·\s*codec\s+(\d+)",
}


def _num(testo, nome):
    """⛔ The LAST occurrence — the counts line comes after all the others — and
       a `None` means «I did not read it», not «zero»."""
    trovato = None
    for m in re.finditer(DA_LEGGERE[nome], testo):
        trovato = int(m.group(1))
    return trovato


# ═══════════════════════════════════════════════════════════════════════════
# THE TWO BINARIES, AND THE SERVER THAT RESTARTS ON ONE OR THE OTHER
# ═══════════════════════════════════════════════════════════════════════════
def md5(percorso):
    rc, out, _ = root("md5sum %s 2>/dev/null | cut -d' ' -f1" % percorso)
    s = out.strip()
    return s if len(s) == 32 else None


def costruisci():
    """⛔ THE BINARY — one only, and it is the product's.

    ⭐ Since 24 August 2026 there is nothing to build twice any more: the `-D`
       `AUDIO_SILENZIO_PREDEFINITO` was removed and the arms are made with
       `--niente-audio-silenzio` (⇒ the header).  ⚠ Here it is built and its md5
       is DECLARED: it no longer serves to tell two arms apart, it serves to say
       which product I measured.
    ⛔ The sources must already be in the tree: whoever brings them is the ground
       (`09-b79-terreno.sh porta` or `07-b64-terreno.sh porta`), and this bench
       does not keep a second copy of them."""
    log("THE BINARY — one only, and it is the product")
    rc, out, err = root(
        "bash /media/REMOTIX/enter.sh --root 'PREFISSO=/srv/src/b2/prefisso "
        "NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 "
        "bash %s/src/costruisci.sh 2>&1 | tail -6'" % DENTRO_ALB, 1200)
    for r in (out + err).splitlines()[-6:]:
        inf(r.strip()[:150])
    m = md5(BINARIO)
    if not m:
        ko("⛔ the binary is not there: %s" % BINARIO)
        return False
    ok("binary md5 %s" % m)
    # ⛔⭐ AND WE CHECK THAT IT CARRIES THE SWITCH.  A binary from before
    #    24 August is born with the cure OFF and REFUSES `--niente-audio-silenzio`:
    #    it would give «the server does not start» on the OFF arm, and an ON arm
    #    that is not on.
    rc, out, _ = root("grep -qa -- --niente-audio-silenzio %s && echo si || "
                      "echo no" % BINARIO)
    if "si" not in out:
        ko("⛔⛔ `--niente-audio-silenzio` is NOT in this binary: it is from before "
           "24 August 2026, and the two arms would both be «spenta»")
        return False
    ok("`--niente-audio-silenzio` is in the binary")
    return True


def accendi(braccio):
    """⛔ The server restarts on the ONE binary, with the arm's command
       line.  ⚠ And the state of the cure is not checked here: the check is
       `LEZIONI.md` E1 and is done AFTERWARDS, on the product's log
       (`cura_del_registro()` + `a_la_cura_ha_parlato()`) — «I wrote it on the
       command line» is not «it is in force», and it is the only belt left since
       the binary has been just one."""
    m = md5(BINARIO)
    if m is None:
        ko("⛔ the binary is not there (%s): «costruisci»" % BINARIO)

        return None
    subprocess.run(["bash", os.path.join(QUI, "07-b64-terreno.sh"), "accendi"],
                   capture_output=True, timeout=300,
                   env=dict(os.environ, UNITA=UNITA,
                            OPZIONI_SERVER=OPZIONI[braccio]))
    for _ in range(50):
        rc2, o, _ = root("ss -uln 2>/dev/null | grep -c ':%d '" % PORTA)
        if o.strip() not in ("", "0"):
            break
        time.sleep(0.2)
    return m


def giro(braccio, scena, codec, secondi):
    """One run: arm (spenta|accesa) · scene (muto|tono) · codec (pcm|opus)."""
    nome = "%s-%s-%s" % (braccio, scena, codec)
    j_fuori = os.path.join(FUORI, nome + ".jsonl")
    binario = accendi(braccio)
    if binario is None:
        return {"esito": "the binary of arm «%s» did not get in place" % braccio}

    if scena == "tono":
        # ⛔⭐ AND THE ORDER IS NOT A DETAIL — `[M]` 24 August 2026, first run
        #     with the tone: the «remotix» sink is created by the CHILD, and the child is born
        #     when a client comes in.  On a freshly restarted server
        #     `pw-play --target remotix` binds to NOTHING, and the bench
        #     would have measured silence calling it network.  ⇒ First a short
        #     session that brings the stage to life (I4: it outlives it), then the tone.
        if not RETE.innesca_sessione():
            return {"esito": "⛔ the session does not open: there is no sink to "
                             "play into"}
        if not RETE.tono_accendi():
            return {"esito": "⛔ the tone does NOT play in the session: a judge "
                             "reading silence would blame the network"}
    else:
        RETE.tono_spegni()

    riga0 = righe_registro()
    t0 = time.time()
    # ⛔⭐ AND `opus` ALONE CANNOT BE DECLARED — `[M]` 24 August 2026, first
    #    run: `congedo motivo=0x09 dettaglio=il client non dichiara pcm in
    #    audio.codec`.  §4.3 mandates `pcm` on BOTH sides and `rcp.c:2229` enforces
    #    it.  ⇒ To get Opus one declares **`opus,pcm`**, and the server
    #    picks the first in the client's order of preference.
    #    ⚠ Asking for «opus only» does not give a run without PCM: it gives a run without
    #      ANYTHING, and its zeros would have looked like a measurement.
    chiesto = "opus,pcm" if codec == "opus" else "pcm"
    dentro = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
              "--utente %s --parola-file %s/parola --audio-codec %s "
              "--audio-scrivi %s/b84-%s.jsonl --resta %d"
              % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, chiesto,
                 DENTRO_LAV, nome, secondi))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % dentro,
                        secondi + 240)
    uscita = out + err
    open(os.path.join(FUORI, nome + ".txt"), "w").write(uscita)
    subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                   "cat %s/b84-%s.jsonl\" > %s"
                   % (MACCHINA, RETE.PAROLA_SUDO, LAV, nome, j_fuori),
                   shell=True)
    if scena == "tono":
        RETE.tono_spegni()

    rq = rete_del_giro(riga0)
    sv = conti_del_server(riga0)
    cu = cura_del_registro(riga0)
    n = {"braccio": braccio, "scena": scena, "codec": codec, "binario": binario,
         "secondi": round(time.time() - t0, 1),
         "sul_filo": _num(uscita, "sul_filo"),
         "ricevuti": _num(uscita, "ricevuti"),
         "consegnati": _num(uscita, "consegnati"),
         "mancati": _num(uscita, "mancati"),
         "carico": _num(uscita, "carico"),
         "codec_cli": _num(uscita, "codec_cli"),
         "spediti_server": sv.get("spediti"),
         "rifiutati_server": sv.get("rifiutati"),
         "buttati_server": sv.get("buttati"),
         "rimandati_server": sv.get("rimandati"),
         "codec_server": sv.get("codec"),
         "server": sv, "rete": rq}
    n.update({k: rq.get(k) for k in ("pkt_s", "kbit_s", "dgram_s", "byte_per_pkt")})
    n.update({k: cu.get(k) for k in ("cura_dichiarata", "taciuti",
                                     "entrati_cod", "usciti_cod")})
    # ⭐ The TRUE audio payload: the bytes of §6.3 the client counted,
    #   over the run's time.  ⛔ It is not `kbit_s`: that is the wire, padding
    #   included, and it is precisely the difference between the two that this bench measures.
    if n["carico"] is not None and rq.get("secondi"):
        n["carico_kbit_s"] = round(n["carico"] * 8.0 / 1000.0 / rq["secondi"], 3)
    else:
        n["carico_kbit_s"] = None
    # ⭐⭐ THE WIRE COVERAGE — how much of what is produced arrives, and it holds for
    #    BOTH codecs.  ⛔ `prodotti` is the SERVER's count (sent +
    #    refused + dropped): «I never put it on the wire» and «the network
    #    lost it» both end up in here, and it is on purpose — the question is
    #    how much arrives, not whose fault it is.
    if None not in (n["spediti_server"], n["rifiutati_server"],
                    n["buttati_server"], n["sul_filo"]):
        prodotti = (n["spediti_server"] + n["rifiutati_server"] +
                    n["buttati_server"])
        n["prodotti_server"] = prodotti
        n["copertura_filo"] = (round(n["sul_filo"] / float(prodotti), 4)
                               if prodotti > 0 else None)
    else:
        n["prodotti_server"] = None
        n["copertura_filo"] = None
    # ⭐ The second leg, from the SAMPLES: only PCM is judged this way
    #   (`09-b77.scaletta()` skips the blocks that are not codec 2).
    sc = B77.scaletta(j_fuori) if codec == "pcm" else {
        "esito": "NON GIUDICATO — Opus samples cannot be read without "
                 "decoding them, and this bench has no decoder"}
    n["scaletta"] = sc
    n["copertura"] = sc.get("copertura")
    n["purezza_tono"] = sc.get("purezza_tono")
    n["blocchi"] = sc.get("blocchi")
    # ⛔⛔ AND THE CODEC MUST BE THE ONE I ASKED FOR, SAID BY THE SERVER.
    #     «I declared it» is not «it chose it» (`LEZIONI.md` E1): §4.3 makes
    #     the SERVER choose within the intersection, and an «opus» run that ended up in
    #     PCM would be the same run twice with the name of two.
    atteso = 1 if codec == "opus" else 2
    if n["codec_server"] is not None and n["codec_server"] != atteso:
        n["esito"] = ("⛔⛔ I ASKED FOR «%s» (codec %d) AND THE SERVER NEGOTIATED "
                      "codec %d" % (codec, atteso, n["codec_server"]))
    return n


def riga(n):
    def q(x, f="%s"):
        return "-" if x is None else (f % x)
    return ("%-7s %-5s %-5s | wire %s kbit/s · %s pkt/s · %s dgram/s · %s B/pkt "
            "| payload %s kbit/s (%s bytes) | srv %s sent %s refused | "
            "cure %s silenced %s | WIRE.COV %s (cov %s tone %s) | miss %s"
            % (n.get("braccio"), n.get("scena"), n.get("codec"),
               q(n.get("kbit_s"), "%.1f"), q(n.get("pkt_s"), "%.1f"),
               q(n.get("dgram_s"), "%.1f"), q(n.get("byte_per_pkt"), "%.0f"),
               q(n.get("carico_kbit_s"), "%.2f"), q(n.get("carico")),
               q(n.get("spediti_server")), q(n.get("rifiutati_server")),
               q(n.get("cura_dichiarata")), q(n.get("taciuti")),
               q(n.get("copertura_filo"), "%.4f"),
               q(n.get("copertura"), "%.4f"), q(n.get("purezza_tono"), "%.3f"),
               q(n.get("mancati"))))


def giudica(titolo, atteso, s, a):
    log(titolo)
    inf(riga(s)); inf(riga(a))
    verdi = rossi = muti = 0
    for f in atteso:
        passa, perche = f(s, a)
        if passa is True:
            ok(perche); verdi += 1
        elif passa is False:
            ko(perche); rossi += 1
        else:
            dub(perche); muti += 1
    return verdi, rossi, muti


# ═══════════════════════════════════════════════════════════════════════════
# THE GROUND
# ═══════════════════════════════════════════════════════════════════════════
def terreno_controlla():
    log("THE GROUND — port %d · user %s (uid %d) · tree %s"
        % (PORTA, UTENTE, UID_B, ALB))
    guai = []
    rc, out, _ = root("id %s >/dev/null 2>&1 && echo si || echo no" % UTENTE)
    if "si" not in out:
        guai.append("the user «%s» does not exist" % UTENTE)
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % LAV)
    if "si" not in out:
        guai.append("%s/parola (0600) is missing: D12 forbids the password in argv" % LAV)
    if not md5(BINARIO):
        guai.append("the binary is missing (%s): «costruisci»" % BINARIO)
    conto = []
    for p in VIETATE:
        rc, o, _ = root("ss -uln 2>/dev/null | grep -c ':%s ' || true" % p)
        conto.append("%s:%s" % (p, o.strip()))
    inf("FORBIDDEN ports (counted, not touched): %s" % " ".join(conto))
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % VIETATA_IFACE)
    inf("%s — NOT touched: %s" % (VIETATA_IFACE, out.strip().split("\n")[0]))
    for g in guai:
        ko(g)
    if not guai:
        ok("the ground is there, and it is mine")
    return not guai


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CERTIFICATION — the bench must be able to give RED
#
# ⛔⛔ A bench that has never given red is not a tool: it is a hope
#      with some numbers next to it.  Here every predicate is called on
#      FABRICATED numbers, and the outcome it must give is demanded.
# ═══════════════════════════════════════════════════════════════════════════
def _n(**kw):
    return dict(kw)


def certifica():
    esiti = []

    def caso(titolo, f, s, a, atteso):
        passa, perche = f(s, a)
        bene = (passa is atteso) if atteso is None else (passa == atteso)
        esiti.append(bene)
        (ok if bene else ko)("%s → %s  [%s]"
                             % (titolo, {True: "VERDE", False: "ROSSO",
                                         None: "NON GIUDICATO"}[passa], perche))

    log("1 · `a_il_riempimento_c_e` — the positive control of the fact")
    f = a_il_riempimento_c_e()
    caso("589 kbit/s for 1.2 kbit/s of payload", f,
         _n(kbit_s=589.0, carico_kbit_s=1.2), {}, True)
    caso("⛔ 40 kbit/s: the padding is NOT there", f,
         _n(kbit_s=40.0, carico_kbit_s=1.2), {}, False)
    caso("⛔ 589 kbit/s but 300 of payload: something is playing", f,
         _n(kbit_s=589.0, carico_kbit_s=300.0), {}, False)
    caso("⚠ kbit_s not read", f, _n(kbit_s=None, carico_kbit_s=1.2), {}, None)

    log("2 · `a_la_cura_taglia` — and it is not content with an improvement")
    f = a_la_cura_taglia(8.0)
    caso("589 → 12 kbit/s (49×)", f, _n(kbit_s=589.0), _n(kbit_s=12.0), True)
    caso("⛔ 589 → 200 kbit/s (2.9×): better, but it is not the cure", f,
         _n(kbit_s=589.0), _n(kbit_s=200.0), False)
    caso("589 → 0 kbit/s", f, _n(kbit_s=589.0), _n(kbit_s=0.0), True)
    caso("⚠ one end is missing", f, _n(kbit_s=589.0), _n(kbit_s=None), None)

    log("3 · `a_i_datagram_spariscono` — the other end of the wire")
    f = a_i_datagram_spariscono()
    caso("50 → 0 datagram/s", f, _n(dgram_s=50.0), _n(dgram_s=0.0), True)
    caso("⛔ 50 → 30: the cure did not bite", f,
         _n(dgram_s=50.0), _n(dgram_s=30.0), False)
    caso("⛔ 5 → 0: there was no audio to begin with", f,
         _n(dgram_s=5.0), _n(dgram_s=0.0), False)

    log("4 · `a_la_cura_ha_parlato` — «I turned it on» is not «it did it»")
    f = a_la_cura_ha_parlato()
    caso("spenta/accesa, 1249 silenced", f,
         _n(cura_dichiarata="spenta"), _n(cura_dichiarata="accesa", taciuti=1249), True)
    # ⛔⛔ AND SINCE 24 AUGUST 2026 THIS CASE IS THE MOST IMPORTANT OF THE FOUR:
    #     the two arms ARE the same binary by construction, so «two identical
    #     runs with the name of two» is no longer a build accident —
    #     it is what happens if `--niente-audio-silenzio` does not reach the server.
    #     ⇒ This predicate is the only thing that tells it apart from «the cure is not
    #     needed», which is the opposite conclusion.
    caso("⛔ both arms declare «spenta»: the option did not arrive", f,
         _n(cura_dichiarata="spenta"), _n(cura_dichiarata="spenta", taciuti=0), False)
    caso("⛔ accesa but zero silenced", f,
         _n(cura_dichiarata="spenta"), _n(cura_dichiarata="accesa", taciuti=0), False)
    caso("⚠ the log does not have the line", f,
         _n(cura_dichiarata="spenta"), _n(cura_dichiarata="accesa", taciuti=None), None)

    log("5 · ⛔⛔ `a_il_suono_non_si_tocca` — the predicate that protects the user")
    f = a_il_suono_non_si_tocca()
    caso("coverage 0.998 → 0.997, tone 1.00 → 1.00", f,
         _n(copertura=0.998, purezza_tono=1.0),
         _n(copertura=0.997, purezza_tono=1.0), True)
    caso("⛔ coverage 0.998 → 0.700: the cure eats sound", f,
         _n(copertura=0.998, purezza_tono=1.0),
         _n(copertura=0.700, purezza_tono=0.9), False)
    caso("⛔ same coverage but the tone collapses", f,
         _n(copertura=0.998, purezza_tono=1.0),
         _n(copertura=0.998, purezza_tono=0.5), False)

    log("6 · `a_col_tono_tace_solo_il_primo` — is the scene the one I think?")
    f = a_col_tono_tace_solo_il_primo()
    caso("with the tone, zero silenced", f, {}, _n(taciuti=0), True)
    caso("⛔ with the tone, 300 silenced: the scene has gaps of digital zero", f,
         {}, _n(taciuti=300), False)

    log("7 · `a_opus_costa_meno_del_pcm` — the refutation, in one number")
    f = a_opus_costa_meno_del_pcm(10.0)
    caso("PCM 1555 against Opus 1.2 kbit/s", f,
         _n(carico_kbit_s=1555.0), _n(carico_kbit_s=1.2), True)
    caso("⛔ PCM 1555 against Opus 500: it is not a factor of ten", f,
         _n(carico_kbit_s=1555.0), _n(carico_kbit_s=500.0), False)

    log("8 · `a_il_pcm_si_fa_rifiutare` — the positive control of the network")
    f = a_il_pcm_si_fa_rifiutare(100)
    caso("1823 refused", f, _n(rifiutati_server=1823), {}, True)
    caso("⛔ 4 refused: the profile does not bite", f, _n(rifiutati_server=4), {}, False)
    caso("⚠ count not read", f, _n(rifiutati_server=None), {}, None)

    log("9 · `a_opus_regge_dove_il_pcm_cede`")
    f = a_opus_regge_dove_il_pcm_cede(20)
    caso("PCM 366‰ against Opus 2‰", f,
         _n(rifiutati_server=1823, spediti_server=3160),
         _n(rifiutati_server=2, spediti_server=1240), True)
    caso("⛔ Opus 120‰: it does not hold", f,
         _n(rifiutati_server=1823, spediti_server=3160),
         _n(rifiutati_server=150, spediti_server=1100), False)

    log("10 · ⭐⭐ `a_la_copertura_risale` — the quantity that counts")
    f = a_la_copertura_risale(0.10)
    caso("0.63 → 0.99", f, _n(copertura_filo=0.6264),
         _n(copertura_filo=0.99), True)
    caso("⛔ 0.63 → 0.66: within the noise", f,
         _n(copertura_filo=0.6264), _n(copertura_filo=0.66), False)
    caso("⚠ one of the two was not judged", f,
         _n(copertura_filo=0.6264), _n(copertura_filo=None), None)

    log("11 · ⚠ `a_il_prezzo_si_dichiara` — it is not a green and not a red")
    f = a_il_prezzo_si_dichiara()
    caso("the price is always written", f, _n(mancati=0), _n(mancati=1200), None)

    log("OUTCOME OF THE CERTIFICATION")
    if all(esiti):
        ok("%d cases out of %d: the predicates can give green, red and «I do not judge»"
           % (sum(esiti), len(esiti)))
        return True
    ko("%d cases out of %d did NOT give the expected outcome: the bench is not a "
       "tool as long as this line is red" % (len(esiti) - sum(esiti), len(esiti)))
    return False


# ═══════════════════════════════════════════════════════════════════════════
# THE MEASUREMENTS
# ═══════════════════════════════════════════════════════════════════════════
def misura_muto(secondi):
    log("SCENE «MUTO» — desktop still, Opus negotiated, cure off against on")
    inf("⛔ it is the product's NORMAL scene: `[M]` on the user's real session "
        "the datagram payload is 3 bytes, that is digital silence")
    s = giro("spenta", "muto", "opus", secondi)
    a = giro("accesa", "muto", "opus", secondi)
    v, r, m = giudica("THE VERDICT — silent scene",
                      [a_il_riempimento_c_e(), a_la_cura_taglia(8.0),
                       a_i_datagram_spariscono(), a_la_cura_ha_parlato(),
                       a_il_prezzo_si_dichiara()], s, a)
    return {"scena": "muto", "spenta": s, "accesa": a,
            "verdi": v, "rossi": r, "muti": m}


def misura_tono(secondi):
    log("SCENE «TONO» — 440 Hz in the sink, PCM (for the samples judge)")
    inf("⛔ it is the CONTROL that protects the user: with the tone on the cure must "
        "silence nothing, and the coverage must not move")
    s = giro("spenta", "tono", "pcm", secondi)
    a = giro("accesa", "tono", "pcm", secondi)
    v, r, m = giudica("THE VERDICT — scene with the tone",
                      [a_il_suono_non_si_tocca(), a_col_tono_tace_solo_il_primo()],
                      s, a)
    return {"scena": "tono", "spenta": s, "accesa": a,
            "verdi": v, "rossi": r, "muti": m}


def misura_costo(secondi):
    log("THE COST OF THE TWO CODECS — PCM against Opus, same scene, cure OFF")
    inf("⭐ it is the refutation: the 2 463 kbit/s of `09-b81` and the 36 % of `09-b77` "
        "are PCM numbers, and the product negotiates Opus")
    p = giro("spenta", "muto", "pcm", secondi)
    o = giro("spenta", "muto", "opus", secondi)
    v, r, m = giudica("THE VERDICT — what the audio costs",
                      [a_opus_costa_meno_del_pcm(10.0)], p, o)
    return {"scena": "costo", "pcm": p, "opus": o, "verdi": v, "rossi": r, "muti": m}


def misura_stretta(nome_profilo, secondi):
    """⛔ HERE THE NETWORK IS BROKEN: lock, `lo` only, filters on my
       port only, detached guardian, and everything released in a `finally`."""
    prof = None
    for p in B77.PROFILI:
        if p[0] == nome_profilo:
            prof = p
    if prof is None:
        ko("the profile «%s» is not in 09-b77" % nome_profilo)
        return None
    log("THE NARROW NETWORK — profile «%s», PCM against Opus, cure OFF" % nome_profilo)
    inf("⛔ both runs under the SAME `netem`, set once and "
        "left standing: only the codec changes")
    LUCCHETTO.prendi(CHI, secondi=900, attesa=3600)
    try:
        RETE.guardiano_arma(900)
        RETE.guasta(prof[1])
        # ⛔ SCENE WITH THE TONE, not silent: the question is what happens
        #    to REAL audio when the window narrows.  On a silent scene
        #    PCM would send 192 blocks of zeros a second and the comparison
        #    would measure the cost of silence, which is something else.
        p = giro("spenta", "tono", "pcm", secondi)
        o = giro("spenta", "tono", "opus", secondi)
    finally:
        try:
            RETE.rimetti()
        except Exception as e:
            ko("⛔ the `netem` was not removed: %s" % e)
        try:
            RETE.guardiano_disarma()
        except Exception:
            pass
        LUCCHETTO.molla(CHI)
    v, r, m = giudica("THE VERDICT — who holds when the window narrows",
                      [a_il_pcm_si_fa_rifiutare(100),
                       a_opus_regge_dove_il_pcm_cede(20),
                       a_la_copertura_risale(0.10)], p, o)
    return {"scena": "stretta-%s" % nome_profilo, "pcm": p, "opus": o,
            "verdi": v, "rossi": r, "muti": m}


def principale():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("passo", nargs="?", default="stato",
                    choices=("stato", "terreno", "costruisci", "muto", "tono",
                             "costo", "stretta", "tutto"))
    ap.add_argument("--secondi", type=int, default=25)
    ap.add_argument("--profilo", default="casa-cattiva")
    ap.add_argument("--certifica", action="store_true")
    a = ap.parse_args()

    if a.certifica:
        sys.exit(0 if certifica() else 1)

    if a.passo == "stato":
        terreno_controlla()
        return
    if a.passo == "terreno":
        sys.exit(0 if terreno_controlla() else 2)
    if a.passo == "costruisci":
        sys.exit(0 if costruisci() else 2)

    if not terreno_controlla():
        ko("⛔ I do NOT measure on a ground that is not mine")
        sys.exit(2)

    fuori = []
    if a.passo in ("muto", "tutto"):
        fuori.append(misura_muto(a.secondi))
    if a.passo in ("tono", "tutto"):
        fuori.append(misura_tono(a.secondi))
    if a.passo in ("costo", "tutto"):
        fuori.append(misura_costo(a.secondi))
    if a.passo in ("stretta", "tutto"):
        r = misura_stretta(a.profilo, a.secondi)
        if r:
            fuori.append(r)

    percorso = os.path.join(FUORI, "esiti.json")
    with open(percorso, "w") as f:
        json.dump(fuori, f, indent=1, ensure_ascii=False)
    log("THE VERDICT OF THE WHOLE BENCH")
    V = sum(x["verdi"] for x in fuori)
    R = sum(x["rossi"] for x in fuori)
    M = sum(x["muti"] for x in fuori)
    inf("the numbers in full: %s" % percorso)
    (ok if R == 0 else ko)("%d green · %d red · %d not judged" % (V, R, M))
    sys.exit(0 if R == 0 else 1)


# ═══════════════════════════════════════════════════════════════════════════
# §PADDING — ⛔⛔⛔ THE HALF OF THE CURE THIS BENCH HAD ASKED FOR WAS
#            TRIED ON 24 AUGUST 2026, **IS NOT DONE**, AND MY DIAGNOSIS WAS
#            WRONG.  It is left written in full: it is the part that teaches.
#
# ⛔ WHAT I HAD WRITTEN HERE: that the 557 kbit/s of an idle session were
#    padding requested by `dgram_scrivi_uno()` with
#    `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING` (`src/webtransport.c:1613` and `:1647`),
#    and that it was enough to make that flag conditional on there being a batch to
#    compose.  ⚠ It was a DEDUCTION — I had the number (48.0 datagrams in 48.4
#    packets of 1 441 bytes) and I had stuck next to it a cause that
#    nobody had measured (`LEZIONI.md` §1.9).
#
# ⭐ HOW IT WENT, `[M]` 24 August 2026, bench NR12, port 7981, smooth `lo`,
#    desktop STILL with the tone at 440 Hz, 25 s per run, two runs per arm, and
#    **the same binary except for that line**:
#
#      codec  padding       kbit/s on wire    bytes/packet
#      -----  ------------  ---------------   --------------
#      Opus   always          557.7 / 556.5        1 441
#      Opus   conditional     556.9 / 555.8        1 441
#      Opus   **NEVER**       556.4                1 441
#      PCM    always        2 221.7 / 2 222.0      1 443
#      PCM    conditional   1 988.0 / 1 987.4      1 292
#
# ⛔⛔ **ON OPUS THE GAIN IS ZERO**, and the row that proves it is the third:
#      with `PADDING` **never** requested the packet stays at 1 441 bytes.  ⇒ It was
#      not that flag filling it, and the cure I had asked for here would have
#      changed a line without changing a byte.
#
# ⭐⭐⭐ AND IT IS KNOWN WHO FILLS IT — `[R]`: `wt_scrivi()` asks for
#      **`NGTCP2_WRITE_STREAM_FLAG_PADDING` at EVERY stream write**.
#      When the datagram returns `NGTCP2_ERR_WRITE_MORE` the packet stays
#      OPEN and the stream loop, right after, closes it by filling it.
#      ⇒ The padding of an idle session **does not belong to the datagram: it belongs to the
#      stream**, and whoever wanted to remove it would have to go there.
#
# ⭐ On PCM the condition really bites (−10.5 %), because at 200 blocks a
#    second the datagram CLOSES the packet by itself and the stream loop never
#    runs.  ⚠ But PCM is not what the product negotiates (⇒ the header
#    of this file, four real sessions out of four say `audio.codec=opus`),
#    and the new default — the silence cure ON — with the desktop still
#    removes the datagrams entirely: **0.0 datagrams per second**.
#
# ⇒ ⛔ **IT IS NOT DONE.**  One more condition to maintain inside the most
#      delicate box of `webtransport.c`, for a gain that on the real codec is
#      zero and on the other is worth a tenth of a bandwidth that with the desktop still
#      is not there.  ⚠ The record is in `src/webtransport.c`, in the
#      `MORE`/`PADDING` box, with the numbers above: whoever reconsiders it will find them there
#      before rewriting the line.

# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    principale()
