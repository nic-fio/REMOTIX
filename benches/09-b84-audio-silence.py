#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
09-b84-audio-silence — ⛔⭐⭐ WHAT AUDIO COSTS WHEN THERE IS NO AUDIO.

═══ THE FACT IT IS BORN FROM, AND THE FIRST THING IT REFUTED ═══════════════

The mandate said: *«on a bad network a third of the audio never reaches the
wire»*, `[M]` `09-b77` on `bad-home`, **1 823 blocks refused out of ~5 000**;
and *«an idle session costs 2 463 kbit/s of PCM audio»*, `[M]` `09-b81`.

⛔⛔ **BOTH THOSE NUMBERS ARE IN PCM, AND PCM IS NOT WHAT THE PRODUCT
     NEGOTIATES.**  `[R]` The benches FORCE it on the test client:
     `09-b68:191`, `09-b70:1890`, `09-b71:144`, `09-b77:978`, `09-b81:2294`
     all pass `--audio-codec pcm`.  ⭐ And the log of the user's REAL
     session (port 7920, `/media/REMOTIX/tmp/09c/registro.log`) says
     the opposite, four times out of four:

         negoziato video.codec=hevc video.depth=8 audio.codec=opus
         ⭐ FASE 7: canale audio ACCESO … — codec 1 (Opus)

     ⇒ The 36 % and the 2 463 kbit/s are properties of **a bench
     configuration**, not of the product.  `[R]` `page.html:4727` asks
     `AudioDecoder.isConfigSupported` and declares `opus,pcm` when the engine
     answers yes; PCM stays the base of §4.3 for whoever does not have it.

═══ ⭐⭐⭐ AND WHAT IS REALLY THERE IS MORE SERIOUS, NOT LESS ═══════════════

`[M]` 24 August 2026, REMEASURED with the bench on **a single binary** (port 7981,
binary md5 `6ec170c0…`, 25 s per arm; the first measurement was of 23-24 August
on 7972 with two binaries, and the numbers match).  Session with **Opus**
negotiated and desktop **still** (`sound.c`: `PICCO 0 su 32767`, that is DIGITAL
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
    fills it is `wt_write()`, which asks for
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

⭐ `DECISIONS.md` §3.1-septies removed that `-D`: the cure is born **ON** in the
   product and is turned off with **`--no-audio-silence`**, which is a command
   line option.

⇒ **The two arms are the SAME IDENTICAL BINARY**, and the only thing that changes is the
  server's command line:

      ON       (no option — it is the product that ships)
      OFF      --no-audio-silence

⛔⭐ **ONE SUSPECT LESS, and it is written because it is a gain of method, not
    a simplification.**  Before, if the two arms had given equal numbers,
    there were two explanations: «the cure is not needed» or «the two binaries were not
    the ones I thought».  Now there is only one.  ⚠ And the md5 is printed all the same, at
    every run: it serves to say WHICH product I measured, no longer to tell the
    arms apart.

⛔⛔ AND WHAT TELLS THE ARMS APART NOW IS **ONLY THE PRODUCT'S LOG** —
    `a_fix_has_spoken()`, which demands `cura_dichiarata` «spenta» in one and
    «accesa» in the other.  With two binaries that predicate was an extra belt;
    with a single binary it is **the only one**, and without it two identical runs with
    the name of two would be indistinguishable from a cure that is not needed.
    ⚠ `LESSONS.md` E1: «written is not in force».

═══ ⭐ THE QUANTITIES, AND THE ONE THAT COUNTS IS NOT «HOW MANY I THROW AWAY» ══

  1. **`kbit_s`** — the bytes ngtcp2 declares sent, from the product's `quic-net`
     line.  ⛔ It is not an estimate of mine: it is the transport's counter.
  2. **`pkt_s`** and **`dgram_s`** — packets and datagrams per second.  ⭐ Their
     ratio is the proof of the padding: 50 datagrams in 51 packets means
     «one packet per block».
  3. **`copertura`** — how much of the timeline really received
     samples, counted by `09-b77.scaletta()` on the PCM blocks.  ⭐ It is the
     quantity on which the cure can do harm: if it silenced sound, it would drop.
  4. **`purezza_tono`** — the judge of `07-b42` via `09-b77.purezza_tono()`.

═══ ⛔ AND ON A BAD NETWORK THE CODEC IS NOT ENOUGH — the prediction that did NOT hold ══

`[M]` 24 August 2026, `bad-home` (40±20 ms, 2 % loss), scene with the tone,
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
    python3 benches/09-b84-audio-silence.py --certify    # ⛔ first of all
    python3 benches/09-b84-audio-silence.py terrain
    python3 benches/09-b84-audio-silence.py build     # THE binary (one)
    python3 benches/09-b84-audio-silence.py mute  [--seconds 25]
    python3 benches/09-b84-audio-silence.py tone  [--seconds 25]
    python3 benches/09-b84-audio-silence.py cost [--seconds 25]
    python3 benches/09-b84-audio-silence.py squeeze [--profile bad-home]
    python3 benches/09-b84-audio-silence.py all
"""
import argparse, importlib.util, json, os, re, subprocess, sys, time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

# ═══════════════════════════════════════════════════════════════════════════
# ⛔ ISOLATION, and it is written BEFORE importing anything: the modules
#    underneath read the environment at import time, not at call time
#    (`LESSONS.md` §1.26).
# ═══════════════════════════════════════════════════════════════════════════
PORT = int(os.environ.get("PORT", "7972"))
ACCOUNT = os.environ.get("ACCOUNT", "provanr9")
UID_B = int(os.environ.get("UID_B", "1072"))
TREE_DIR = os.environ.get("TREE", "/media/REMOTIX/src/09nr9-src")
WORKDIR = os.environ.get("WORKDIR", "/media/REMOTIX/tmp/09nr9")
INSIDE_TREE = os.environ.get("INSIDE_TREE", "/srv/src/09nr9-src")
INSIDE_WORK = os.environ.get("INSIDE_WORK", "/srv/remotix/tmp/09nr9")
UNIT = os.environ.get("UNIT", "remotix-%d" % PORT)
USER_PASSWORD = os.environ.get("USER_PASSWORD", "nr9-audio-2026")
MACHINE = os.environ.get("MACHINE", "nicfio@192.168.0.2")
ADDR = os.environ.get("ADDR", "192.168.0.2")
OUT = os.environ.get("OUT", os.path.join(
    "/tmp/claude-1000/-home-nicfio-Documenti-REMOTIX/"
    "b62d7177-9fdd-47c7-8aa1-567c8b13accf/scratchpad", "b84"))

# ⛔ The ports that are NOT mine.  They are counted, not touched.
FORBIDDEN = ("7900", "7910", "7920", "7971")
FORBIDDEN_IFACE = "enp7s0"

for k, v in (("PORT", str(PORT)), ("ACCOUNT", ACCOUNT), ("UID_B", str(UID_B)),
             ("TREE", TREE_DIR), ("WORKDIR", WORKDIR), ("INSIDE_TREE", INSIDE_TREE),
             ("INSIDE_WORK", INSIDE_WORK), ("OUT", OUT), ("ADDR", ADDR),
             ("MACHINE", MACHINE), ("USER_PASSWORD", USER_PASSWORD)):
    os.environ[k] = v
os.makedirs(OUT, exist_ok=True)


def _load(name, file_):
    sp = importlib.util.spec_from_file_location(name, os.path.join(HERE, file_))
    m = importlib.util.module_from_spec(sp)
    sp.loader.exec_module(m)
    return m


# ⛔ `09-b77` is NOT touched: it is IMPORTED.  It has the tone, the samples judge,
#    the `netem` profiles and 52 green `--certify` cases — rewriting one
#    line of it would mean having two judges that can diverge.
B77 = _load("b77", "09-b77-audio-reorder.py")
NETWORK = B77.NETWORK            # root(), broken(), tone_turn_on/turn_off, guardiano_*
LOCK = B77.LOCK

CHI = "09-b84"
# ⛔ ONE binary only, and it is the product's: the arms are made with
#    `SERVER_OPTIONS` (⇒ the header, «one suspect less»).
BINARY = "%s/src/remotix" % TREE_DIR
# ⭐ The command line of each arm, and the ON arm has none.
OPTIONS = {"enabled": "", "spenta": "--no-audio-silence"}


def log(t):  print("\n\033[1m== %s\033[0m" % t)
def ok(t):   print("    \033[1;32mOK\033[0m  %s" % t)
def ko(t):   print("    \033[1;31mNO\033[0m  %s" % t)
def dub(t):  print("    \033[1;33m??\033[0m  %s" % t)
def inf(t):  print("    --  %s" % t)


# ═══════════════════════════════════════════════════════════════════════════
# THE PREDICATES — WRITTEN FIRST, AND THEY ARE FUNCTIONS, NOT PROSE
#
# ⛔ R13: an expectation in prose stays true «on reading» whatever number comes out.  Here
#    every expectation is `(s, a) -> (passes, why)` — `s` are the numbers of the arm
#    with the cure OFF, `a` those with the cure ON — and `passes=None` means
#    «I refuse to judge», which is an outcome of ITS OWN and not a green.
# ═══════════════════════════════════════════════════════════════════════════
def _p(cond, why):
    return (bool(cond), why)


def _mute(why):
    return (None, why)


def _c(n, key):
    """The value, or `None` if it was not read.  ⛔ `None` is not zero."""
    if not isinstance(n, dict):
        return None
    return n.get(key)


def a_fill_is_there(min_kbit=400.0, max_load_kbit=5.0):
    """⭐ THE FACT, measured with the OFF arm — which is today's product.

    ⛔ It is also the bench's POSITIVE CONTROL: if the padding does not come out here,
       the stimulus does not stimulate (the desktop was playing, or the session had no
       audio) and the ON arm would prove nothing."""
    def f(s, a):
        k = _c(s, "kbit_s")
        c = _c(s, "load_kbit_s")
        if k is None or c is None:
            return _mute("I did not read kbit_s (%s) or carico_kbit_s (%s)" % (k, c))
        return _p(k >= min_kbit and c <= max_load_kbit,
                  "cure OFF: %.1f kbit/s on the wire for %.2f kbit/s of payload "
                  "(expected >= %.0f and <= %.1f)" % (k, c, min_kbit, max_load_kbit))
    return f


def a_fix_trims(factor=8.0):
    """⭐ THE PREDICTION THAT CAN FALL: bandwidth drops by at least `factor`."""
    def f(s, a):
        ks, ka = _c(s, "kbit_s"), _c(a, "kbit_s")
        if ks is None or ka is None:
            return _mute("kbit_s: off=%s on=%s" % (ks, ka))
        if ka <= 0:
            return _p(True, "cure ON: 0 kbit/s (off %.1f)" % ks)
        return _p(ks / ka >= factor,
                  "%.1f → %.1f kbit/s = %.1f× (expected >= %.0f×)"
                  % (ks, ka, ks / ka, factor))
    return f


def a_datagrams_disappear(cap_s=2.0):
    """⭐ And it shows at the OTHER end: the client no longer receives blocks."""
    def f(s, a):
        ds, da = _c(s, "dgram_s"), _c(a, "dgram_s")
        if ds is None or da is None:
            return _mute("dgram_s: off=%s on=%s" % (ds, da))
        return _p(ds >= 40.0 and da <= cap_s,
                  "datagrams per second: %.1f → %.1f (expected >= 40 and <= %.1f)"
                  % (ds, da, cap_s))
    return f


def a_fix_has_spoken():
    """⛔ «I turned it on» is not «it did it»: the PRODUCT's log must say
       that the cure is on AND that it silenced some blocks.  ⚠ Without that, a wrong
       binary would give two identical runs with the name of two."""
    def f(s, a):
        if _c(a, "declared_fix") != "enabled":
            return _p(False, "the log of the ON arm declares «%s»"
                             % _c(a, "declared_fix"))
        if _c(s, "declared_fix") != "spenta":
            return _p(False, "the log of the OFF arm declares «%s»"
                             % _c(s, "declared_fix"))
        t = _c(a, "silenced")
        if t is None:
            return _mute("the log does not carry the digital silence line")
        return _p(t > 0, "blocks silenced by the ON arm: %s (expected > 0)" % t)
    return f


def a_sound_is_untouched(tolerance=0.02):
    """⛔⛔ THE CHECK WORTH MORE THAN ALL: on the scene with the TONE the cure must
        change NOTHING — the tone is never digital zero.

    ⚠ If this says red, the cure eats sound and does not go out the door."""
    def f(s, a):
        cs, ca = _c(s, "coverage"), _c(a, "coverage")
        ps, pa = _c(s, "tone_purity"), _c(a, "tone_purity")
        if cs is None or ca is None:
            return _mute("coverage: off=%s on=%s" % (cs, ca))
        if abs(cs - ca) > tolerance:
            return _p(False, "coverage %.4f → %.4f: the cure removed sound"
                             % (cs, ca))
        if ps is None or pa is None:
            return _p(True, "coverage %.4f ≈ %.4f (the tone was not judged)"
                            % (cs, ca))
        return _p(abs(ps - pa) <= tolerance * 5,
                  "coverage %.4f ≈ %.4f · tone %.3f ≈ %.3f" % (cs, ca, ps, pa))
    return f


def a_with_tone_only_first_is_silent(cap=2):
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
        t = _c(a, "silenced")
        e = _c(a, "entrati_cod")
        if t is None:
            return _mute("the log does not carry the cure's count at closing")
        return _p(t <= cap,
                  "blocks silenced with the tone on: %s out of %s in "
                  "(expected <= %d: only those preceding the first samples)"
                  % (t, e, cap))
    return f


def a_price_is_declared():
    """⚠ IT IS NEITHER A GREEN NOR A RED: it is the price, and it is written.

    A wanted gap has, on the receiving side, the same face as a loss:
    the client's `missed` grow.  ⛔ Declaring it here is what prevents
    someone tomorrow from reading that number as a network fault."""
    def f(s, a):
        return _mute("PRICE: `missed` %s → %s.  A silenced block leaves the "
                     "same `instant` jump as a lost one: the number does not "
                     "tell the two apart, and from today it must be read knowing it"
                     % (_c(s, "missed"), _c(a, "missed")))
    return f


def a_opus_costs_less_than_pcm(factor=10.0):
    """⭐ THE REFUTATION, in one number: the audio payload in PCM against Opus.

    ⛔ The PAYLOAD (the bytes of §6.3) is compared, not the bytes on the wire: on the wire the
       padding evens them out, and that is exactly the defect this bench
       found — confusing the two would say «PCM and Opus cost the same»."""
    def f(p, o):
        cp, co = _c(p, "load_kbit_s"), _c(o, "load_kbit_s")
        if cp is None or co is None or co <= 0:
            return _mute("load_kbit_s: pcm=%s opus=%s" % (cp, co))
        return _p(cp / co >= factor,
                  "audio payload: PCM %.1f kbit/s against Opus %.2f = %.0f× "
                  "(expected >= %.0f×)" % (cp, co, cp / co, factor))
    return f


def a_pcm_gets_refused(minimum=100):
    """⛔ THE POSITIVE CONTROL OF THE NARROW NETWORK: with PCM the refusal is there.

    ⚠ If PCM does not get refused, the profile does not bite and the comparison with
      Opus proves nothing — it would be the same run twice."""
    def f(p, o):
        r = _c(p, "server_refused")
        if r is None:
            return _mute("the log does not carry the server's refused count")
        return _p(r >= minimum,
                  "PCM: %s blocks refused by ngtcp2 (expected >= %d)" % (r, minimum))
    return f


def a_opus_holds_where_pcm_gives_way(cap_permille=20):
    """⭐ THE PREDICTION: on the SAME `netem`, Opus gets refused in a
       negligible fraction of what PCM gets refused.

    ⛔⛔ AND THE PREDICTION **DID NOT HOLD** — `[M]` 24 August 2026, `bad-home`,
        scene with the tone, 25 s per codec, same `netem` for both:

          PCM   3 135 sent · 1 880 refused = **375‰**
          Opus  1 127 sent ·   126 refused = **101‰**

        ⇒ Opus divides the refusal by **3.7**, it does not remove it.  The 20‰ boundary
        was mine and the measurement refuted it: **it is left where it is** and the
        red is written, instead of moving it until it passes (`LESSONS.md` §2.3).
        ⚠ The fact that remains: even with a tenth of the bytes the window closes
        all the same, so the codec **is not the cure of the refusal** — it is the cure
        of the cost.  The cure of the refusal, if there is one, lies in the transport."""
    def f(p, o):
        rp, sp = _c(p, "server_refused"), _c(p, "shipped_server")
        ro, so = _c(o, "server_refused"), _c(o, "shipped_server")
        if None in (rp, sp, ro, so) or (sp + rp) <= 0 or (so + ro) <= 0:
            return _mute("server counts: pcm=%s/%s opus=%s/%s" % (rp, sp, ro, so))
        fp = 1000.0 * rp / (sp + rp)
        fo = 1000.0 * ro / (so + ro)
        return _p(fo <= cap_permille,
                  "refused: PCM %.0f‰ against Opus %.0f‰ (expected Opus <= %d‰)"
                  % (fp, fo, cap_permille))
    return f


def a_coverage_rises(gain=0.10):
    """⭐⭐ THE QUANTITY THAT COUNTS — how much of the PRODUCED audio really arrives.

    ⛔⭐ AND IT IS NOT THE SAMPLES' `coverage`, and the reason is that that one is
        computed only on PCM (`09-b77.scaletta()` skips the blocks that are not
        codec 2, and this bench has no Opus decoder).  Comparing the
        PCM samples' coverage with **nothing** would give «not judged»
        precisely on the mandate's question.

    ⭐ `copertura_filo` = **blocks the network delivered to the client** divided by
       **blocks the server produced** (sent + refused + dropped).
       ⚠ The network's loss is in there too, and it is declared: the two arms
       sit under the SAME `netem`, so the difference between them still belongs to
       whoever gets refused — but the number alone does not separate the two causes.
       ⛔ For that there is `a_opus_holds_where_pcm_gives_way`, which looks at the
       refusals only; this one looks at what reaches the ear."""
    def f(p, o):
        cp, co = _c(p, "wire_coverage"), _c(o, "wire_coverage")
        if cp is None or co is None:
            return _mute("wire_coverage: pcm=%s opus=%s" % (cp, co))
        return _p(co - cp >= gain,
                  "wire coverage: PCM %.4f → Opus %.4f (+%.4f, expected >= +%.2f)"
                  % (cp, co, co - cp, gain))
    return f


# ═══════════════════════════════════════════════════════════════════════════
# THE HALF THAT TALKS TO THE TEST MACHINE
# ═══════════════════════════════════════════════════════════════════════════
def root(command, cap=300):
    return NETWORK.root(command, cap)


def log_line_list():
    rc, out, _ = root("wc -l < %s/registro.log 2>/dev/null || echo 0" % WORKDIR)
    try:
        return int(out.strip())
    except Exception:
        return 0


R_NETWORK = re.compile(
    r"quic-net \S+ since_ms=(\d+).*?sent=(\d+) sent_d=(\d+) "
    r"bytes_sent=(\d+).*?dgram_ok=(\d+)")


def round_network(line0):
    """⭐ THE BYTES ON THE WIRE ARE TOLD BY THE PRODUCT, not an estimate of mine.

    The `quic-net` line carries `bytes_sent` (cumulative per connection) and
    `since_ms` (the TRUE interval between one line and the next).  ⇒ The bandwidth is the
    difference between the first and the last line of the window, divided by the sum
    of the `since_ms` — not by the time I believed I had waited.

    ⛔ And it is read only from `riga0` on, so it belongs to THIS run.
    ⚠ Fewer than three lines: `None` is returned, not zero (`CODER.md` §3.10)."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                      "'quic-net '" % (line0 + 1, WORKDIR))
    lines = []
    for r in out.split("\n"):
        m = R_NETWORK.search(r)
        if m:
            lines.append(tuple(int(x) for x in m.groups()))
    if len(lines) < 3:
        return {"outcome": "NOTHING TO READ — %d «quic-net» lines in this "
                         "run (3 are needed)" % len(lines), "lines": len(lines)}
    # ⛔ The FIRST line is discarded: its `since_ms` also covers the start of the
    #    connection, and the start is not the steady state I want to measure.
    ms = sum(r[0] for r in lines[1:])
    if ms <= 0:
        return {"outcome": "sum of since_ms is zero", "lines": len(lines)}
    return {
        "lines": len(lines),
        "seconds": round(ms / 1000.0, 2),
        "pkt_s": round((lines[-1][1] - lines[0][1]) * 1000.0 / ms, 2),
        "kbit_s": round((lines[-1][3] - lines[0][3]) * 8.0 / ms, 2),
        "dgram_s": round((lines[-1][4] - lines[0][4]) * 1000.0 / ms, 2),
        "byte_per_pkt": (None if lines[-1][1] == lines[0][1] else
                         round((lines[-1][3] - lines[0][3]) /
                               float(lines[-1][1] - lines[0][1]), 1)),
    }


def server_counts(line0):
    """⛔ «The network lost it» and «the server never sent it» give the same
       number on the client's side.  Here the SERVER's count is read."""
    rc, out, _ = root("tail -n +%d %s/registro.log | grep -a 'audio of .*final "
                      "count' | tail -1" % (line0 + 1, WORKDIR))
    r = out.strip()
    if not r:
        return {"outcome": "NOTHING TO READ — no «final count»"}
    m = re.search(r"(\d+) blocks sent, (\d+) dropped.*?(\d+) refused.*?"
                  r"(\d+) DEFERRED", r)
    if not m:
        return {"outcome": "line found but unreadable", "line": r[:160]}
    c = re.search(r"codec (\d+)\s*$", r)
    return {"sent": int(m.group(1)), "dropped": int(m.group(2)),
            "refused": int(m.group(3)), "rimandati": int(m.group(4)),
            "codec": (int(c.group(1)) if c else None)}


def log_fix(line0):
    """⛔ THE SWITCH IS READ FROM THE PRODUCT'S LOG, not from what I
       believe I turned on.  ⚠ `audio.c` writes the line even when the cure
       is OFF, on purpose: «the cure is not there» and «the cure is there and did
       nothing» must have two different faces (`CODER.md` §3.10)."""
    rc, out, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                      "'digital silence cure' | tail -1" % (line0 + 1, WORKDIR))
    details = out.strip()
    # ⛔⛔ AND THE WHOLE SENTENCE IS SEARCHED, NOT THE WORD — `[M]` 24 August 2026, and
    #     this bench would have fallen for it.  Since 24 August the line of the OFF
    #     arm contains *«⚠ And it is NOT the default: since 24 August it is born
    #     ON»*: an `if "ON" in details` would have read **on** on an
    #     OFF arm, that is it would have declared in force the opposite of
    #     what was in force — and `a_fix_has_spoken()`, which is the ONLY
    #     belt left now that the binaries are just one, would have given green to
    #     two wrong arms.
    # ⇒ It is anchored to the two sentences the product writes to SAY the state, and not
    #   to a word that also appears in the explanation (`audio.c:212`).
    state = None
    if "OFF by hand" in details:
        state = "spenta"
    elif "⭐ ON" in details:
        state = "enabled"
    # ⛔ THE EXACT COUNT IS THE ONE AT CLOSING, not the one of the line
    #    inside: that one comes out at the first block and then one every thousand, so it says
    #    «at least N».  ⚠ Reading that one and calling it `silenced` would be a number
    #    that looks measured — `[M]` 24 August 2026: 1 249 blocks silenced
    #    printed «1000».
    rc, out2, _ = root("tail -n +%d %s/registro.log 2>/dev/null | grep -a "
                       "'silence cure count' | tail -1" % (line0 + 1, WORKDIR))
    m = re.search(r"(\d+) blocks muted of (\d+) in, (\d+) out", out2)
    return {"declared_fix": state,
            "silenced": (int(m.group(1)) if m else None),
            "entrati_cod": (int(m.group(2)) if m else None),
            "usciti_cod": (int(m.group(3)) if m else None),
            "line": details[:120]}


TO_READ = {
    "on_wire":   r"on wire\s+(\d+)",
    "received":   r"·\s*received\s+(\d+)\s*·",
    "delivered": r"delivered\s+(\d+)",
    "missed":    r"missed\s+(\d+)",
    "load":     r"·\s*(\d+)\s+bytes of payload",
    "codec_cli":  r"bytes of payload\s*·\s*codec\s+(\d+)",
}


def _num(text, name):
    """⛔ The LAST occurrence — the counts line comes after all the others — and
       a `None` means «I did not read it», not «zero»."""
    found = None
    for m in re.finditer(TO_READ[name], text):
        found = int(m.group(1))
    return found


# ═══════════════════════════════════════════════════════════════════════════
# THE TWO BINARIES, AND THE SERVER THAT RESTARTS ON ONE OR THE OTHER
# ═══════════════════════════════════════════════════════════════════════════
def md5(fpath):
    rc, out, _ = root("md5sum %s 2>/dev/null | cut -d' ' -f1" % fpath)
    s = out.strip()
    return s if len(s) == 32 else None


def build():
    """⛔ THE BINARY — one only, and it is the product's.

    ⭐ Since 24 August 2026 there is nothing to build twice any more: the `-D`
       `AUDIO_SILENZIO_PREDEFINITO` was removed and the arms are made with
       `--no-audio-silence` (⇒ the header).  ⚠ Here it is built and its md5
       is DECLARED: it no longer serves to tell two arms apart, it serves to say
       which product I measured.
    ⛔ The sources must already be in the tree: whoever brings them is the ground
       (`09-b79-terrain.sh ship` or `07-b64-terreno.sh ship`), and this bench
       does not keep a second copy of them."""
    log("THE BINARY — one only, and it is the product")
    rc, out, err = root(
        "bash /media/REMOTIX/enter.sh --root 'DEPS_PREFIX=/srv/src/b2/prefisso "
        "NGTCP2=/srv/src/b2/ngtcp2 NGHTTP3=/srv/src/b2/nghttp3 "
        "bash %s/src/build.sh 2>&1 | tail -6'" % INSIDE_TREE, 1200)
    for r in (out + err).splitlines()[-6:]:
        inf(r.strip()[:150])
    m = md5(BINARY)
    if not m:
        ko("⛔ the binary is not there: %s" % BINARY)
        return False
    ok("binary md5 %s" % m)
    # ⛔⭐ AND WE CHECK THAT IT CARRIES THE SWITCH.  A binary from before
    #    24 August is born with the cure OFF and REFUSES `--no-audio-silence`:
    #    it would give «the server does not start» on the OFF arm, and an ON arm
    #    that is not on.
    rc, out, _ = root("grep -qa -- --no-audio-silence %s && echo si || "
                      "echo no" % BINARY)
    if "yes" not in out:
        ko("⛔⛔ `--no-audio-silence` is NOT in this binary: it is from before "
           "24 August 2026, and the two arms would both be «spenta»")
        return False
    ok("`--no-audio-silence` is in the binary")
    return True


def turn_on(arm):
    """⛔ The server restarts on the ONE binary, with the arm's command
       line.  ⚠ And the state of the cure is not checked here: the check is
       `LESSONS.md` E1 and is done AFTERWARDS, on the product's log
       (`log_fix()` + `a_fix_has_spoken()`) — «I wrote it on the
       command line» is not «it is in force», and it is the only belt left since
       the binary has been just one."""
    m = md5(BINARY)
    if m is None:
        ko("⛔ the binary is not there (%s): «build»" % BINARY)

        return None
    subprocess.run(["bash", os.path.join(HERE, "07-b64-terreno.sh"), "start"],
                   capture_output=True, timeout=300,
                   env=dict(os.environ, UNIT=UNIT,
                            SERVER_OPTIONS=OPTIONS[arm]))
    for _ in range(50):
        rc2, o, _ = root("ss -uln 2>/dev/null | grep -c ':%d '" % PORT)
        if o.strip() not in ("", "0"):
            break
        time.sleep(0.2)
    return m


def cur_round(arm, scene, codec, seconds):
    """One run: arm (spenta|accesa) · scene (mute|tone) · codec (pcm|opus)."""
    name = "%s-%s-%s" % (arm, scene, codec)
    j_out = os.path.join(OUT, name + ".jsonl")
    binary = turn_on(arm)
    if binary is None:
        return {"outcome": "the binary of arm «%s» did not get in place" % arm}

    if scene == "tone":
        # ⛔⭐ AND THE ORDER IS NOT A DETAIL — `[M]` 24 August 2026, first run
        #     with the tone: the «remotix» sink is created by the CHILD, and the child is born
        #     when a client comes in.  On a freshly restarted server
        #     `pw-play --target remotix` binds to NOTHING, and the bench
        #     would have measured silence calling it network.  ⇒ First a short
        #     session that brings the stage to life (I4: it outlives it), then the tone.
        if not NETWORK.trigger_session():
            return {"outcome": "⛔ the session does not open: there is no sink to "
                             "play into"}
        if not NETWORK.tone_turn_on():
            return {"outcome": "⛔ the tone does NOT play in the session: a judge "
                             "reading silence would blame the network"}
    else:
        NETWORK.tone_turn_off()

    line0 = log_line_list()
    t0 = time.time()
    # ⛔⭐ AND `opus` ALONE CANNOT BE DECLARED — `[M]` 24 August 2026, first
    #    run: `farewell reason=0x09 detail=the client does not declare pcm
    #    in audio.codec`.  §4.3 mandates `pcm` on BOTH sides and `rcp.c:2229` enforces
    #    it.  ⇒ To get Opus one declares **`opus,pcm`**, and the server
    #    picks the first in the client's order of preference.
    #    ⚠ Asking for «opus only» does not give a run without PCM: it gives a run without
    #      ANYTHING, and its zeros would have looked like a measurement.
    requested = "opus,pcm" if codec == "opus" else "pcm"
    inside = ("python3 -u %s/benches/01-b3-client.py --address %s --port %d "
              "--user %s --password-file %s/parola --audio-codec %s "
              "--audio-out %s/b84-%s.jsonl --stay %d"
              % (INSIDE_TREE, ADDR, PORT, ACCOUNT, INSIDE_WORK, requested,
                 INSIDE_WORK, name, seconds))
    rc, out, err = root("bash /media/REMOTIX/enter.sh --root '%s'" % inside,
                        seconds + 240)
    output = out + err
    open(os.path.join(OUT, name + ".txt"), "w").write(output)
    subprocess.run("ssh -o BatchMode=yes %s \"printf '%%s\\n' '%s' | sudo -S -p '' "
                   "cat %s/b84-%s.jsonl\" > %s"
                   % (MACHINE, NETWORK.SUDO_PASSWORD, WORKDIR, name, j_out),
                   shell=True)
    if scene == "tone":
        NETWORK.tone_turn_off()

    rq = round_network(line0)
    sv = server_counts(line0)
    cu = log_fix(line0)
    n = {"arm": arm, "scene": scene, "codec": codec, "binary": binary,
         "seconds": round(time.time() - t0, 1),
         "on_wire": _num(output, "on_wire"),
         "received": _num(output, "received"),
         "delivered": _num(output, "delivered"),
         "missed": _num(output, "missed"),
         "load": _num(output, "load"),
         "codec_cli": _num(output, "codec_cli"),
         "shipped_server": sv.get("sent"),
         "server_refused": sv.get("refused"),
         "buttati_server": sv.get("dropped"),
         "rimandati_server": sv.get("rimandati"),
         "codec_server": sv.get("codec"),
         "server": sv, "network": rq}
    n.update({k: rq.get(k) for k in ("pkt_s", "kbit_s", "dgram_s", "byte_per_pkt")})
    n.update({k: cu.get(k) for k in ("declared_fix", "silenced",
                                     "entrati_cod", "usciti_cod")})
    # ⭐ The TRUE audio payload: the bytes of §6.3 the client counted,
    #   over the run's time.  ⛔ It is not `kbit_s`: that is the wire, padding
    #   included, and it is precisely the difference between the two that this bench measures.
    if n["load"] is not None and rq.get("seconds"):
        n["load_kbit_s"] = round(n["load"] * 8.0 / 1000.0 / rq["seconds"], 3)
    else:
        n["load_kbit_s"] = None
    # ⭐⭐ THE WIRE COVERAGE — how much of what is produced arrives, and it holds for
    #    BOTH codecs.  ⛔ `products` is the SERVER's count (sent +
    #    refused + dropped): «I never put it on the wire» and «the network
    #    lost it» both end up in here, and it is on purpose — the question is
    #    how much arrives, not whose fault it is.
    if None not in (n["shipped_server"], n["server_refused"],
                    n["buttati_server"], n["on_wire"]):
        products = (n["shipped_server"] + n["server_refused"] +
                    n["buttati_server"])
        n["prodotti_server"] = products
        n["wire_coverage"] = (round(n["on_wire"] / float(products), 4)
                               if products > 0 else None)
    else:
        n["prodotti_server"] = None
        n["wire_coverage"] = None
    # ⭐ The second leg, from the SAMPLES: only PCM is judged this way
    #   (`09-b77.ladder()` skips the blocks that are not codec 2).
    sc = B77.ladder(j_out) if codec == "pcm" else {
        "outcome": "NOT JUDGED — Opus samples cannot be read without "
                 "decoding them, and this bench has no decoder"}
    n["ladder"] = sc
    n["coverage"] = sc.get("coverage")
    n["tone_purity"] = sc.get("tone_purity")
    n["blocks"] = sc.get("blocks")
    # ⛔⛔ AND THE CODEC MUST BE THE ONE I ASKED FOR, SAID BY THE SERVER.
    #     «I declared it» is not «it chose it» (`LESSONS.md` E1): §4.3 makes
    #     the SERVER choose within the intersection, and an «opus» run that ended up in
    #     PCM would be the same run twice with the name of two.
    expected = 1 if codec == "opus" else 2
    if n["codec_server"] is not None and n["codec_server"] != expected:
        n["outcome"] = ("⛔⛔ I ASKED FOR «%s» (codec %d) AND THE SERVER NEGOTIATED "
                      "codec %d" % (codec, expected, n["codec_server"]))
    return n


def line(n):
    def q(x, f="%s"):
        return "-" if x is None else (f % x)
    return ("%-7s %-5s %-5s | wire %s kbit/s · %s pkt/s · %s dgram/s · %s B/pkt "
            "| payload %s kbit/s (%s bytes) | srv %s sent %s refused | "
            "cure %s silenced %s | WIRE.COV %s (cov %s tone %s) | miss %s"
            % (n.get("arm"), n.get("scene"), n.get("codec"),
               q(n.get("kbit_s"), "%.1f"), q(n.get("pkt_s"), "%.1f"),
               q(n.get("dgram_s"), "%.1f"), q(n.get("byte_per_pkt"), "%.0f"),
               q(n.get("load_kbit_s"), "%.2f"), q(n.get("load")),
               q(n.get("shipped_server")), q(n.get("server_refused")),
               q(n.get("declared_fix")), q(n.get("silenced")),
               q(n.get("wire_coverage"), "%.4f"),
               q(n.get("coverage"), "%.4f"), q(n.get("tone_purity"), "%.3f"),
               q(n.get("missed"))))


def judge(title, expected, s, a):
    log(title)
    inf(line(s)); inf(line(a))
    greens = rossi = silent = 0
    for f in expected:
        passes, why = f(s, a)
        if passes is True:
            ok(why); greens += 1
        elif passes is False:
            ko(why); rossi += 1
        else:
            dub(why); silent += 1
    return greens, rossi, silent


# ═══════════════════════════════════════════════════════════════════════════
# THE GROUND
# ═══════════════════════════════════════════════════════════════════════════
def terrain_check():
    log("THE GROUND — port %d · user %s (uid %d) · tree %s"
        % (PORT, ACCOUNT, UID_B, TREE_DIR))
    troubles = []
    rc, out, _ = root("id %s >/dev/null 2>&1 && echo si || echo no" % ACCOUNT)
    if "yes" not in out:
        troubles.append("the user «%s» does not exist" % ACCOUNT)
    rc, out, _ = root("test -s %s/parola && echo si || echo no" % WORKDIR)
    if "yes" not in out:
        troubles.append("%s/parola (0600) is missing: D12 forbids the password in argv" % WORKDIR)
    if not md5(BINARY):
        troubles.append("the binary is missing (%s): «build»" % BINARY)
    tally = []
    for p in FORBIDDEN:
        rc, o, _ = root("ss -uln 2>/dev/null | grep -c ':%s ' || true" % p)
        tally.append("%s:%s" % (p, o.strip()))
    inf("FORBIDDEN ports (counted, not touched): %s" % " ".join(tally))
    rc, out, _ = root("/usr/sbin/tc qdisc show dev %s" % FORBIDDEN_IFACE)
    inf("%s — NOT touched: %s" % (FORBIDDEN_IFACE, out.strip().split("\n")[0]))
    for g in troubles:
        ko(g)
    if not troubles:
        ok("the ground is there, and it is mine")
    return not troubles


# ═══════════════════════════════════════════════════════════════════════════
# ⛔ THE CERTIFICATION — the bench must be able to give RED
#
# ⛔⛔ A bench that has never given red is not a tool: it is a hope
#      with some numbers next to it.  Here every predicate is called on
#      FABRICATED numbers, and the outcome it must give is demanded.
# ═══════════════════════════════════════════════════════════════════════════
def _n(**kw):
    return dict(kw)


def certify():
    outcomes = []

    def test_case(title, f, s, a, expected):
        passes, why = f(s, a)
        all_ok = (passes is expected) if expected is None else (passes == expected)
        outcomes.append(all_ok)
        (ok if all_ok else ko)("%s → %s  [%s]"
                             % (title, {True: "GREEN", False: "RED",
                                         None: "NOT JUDGED"}[passes], why))

    log("1 · `a_fill_is_there` — the positive control of the fact")
    f = a_fill_is_there()
    test_case("589 kbit/s for 1.2 kbit/s of payload", f,
         _n(kbit_s=589.0, load_kbit_s=1.2), {}, True)
    test_case("⛔ 40 kbit/s: the padding is NOT there", f,
         _n(kbit_s=40.0, load_kbit_s=1.2), {}, False)
    test_case("⛔ 589 kbit/s but 300 of payload: something is playing", f,
         _n(kbit_s=589.0, load_kbit_s=300.0), {}, False)
    test_case("⚠ kbit_s not read", f, _n(kbit_s=None, load_kbit_s=1.2), {}, None)

    log("2 · `a_fix_trims` — and it is not content with an improvement")
    f = a_fix_trims(8.0)
    test_case("589 → 12 kbit/s (49×)", f, _n(kbit_s=589.0), _n(kbit_s=12.0), True)
    test_case("⛔ 589 → 200 kbit/s (2.9×): better, but it is not the cure", f,
         _n(kbit_s=589.0), _n(kbit_s=200.0), False)
    test_case("589 → 0 kbit/s", f, _n(kbit_s=589.0), _n(kbit_s=0.0), True)
    test_case("⚠ one end is missing", f, _n(kbit_s=589.0), _n(kbit_s=None), None)

    log("3 · `a_datagrams_disappear` — the other end of the wire")
    f = a_datagrams_disappear()
    test_case("50 → 0 datagram/s", f, _n(dgram_s=50.0), _n(dgram_s=0.0), True)
    test_case("⛔ 50 → 30: the cure did not bite", f,
         _n(dgram_s=50.0), _n(dgram_s=30.0), False)
    test_case("⛔ 5 → 0: there was no audio to begin with", f,
         _n(dgram_s=5.0), _n(dgram_s=0.0), False)

    log("4 · `a_fix_has_spoken` — «I turned it on» is not «it did it»")
    f = a_fix_has_spoken()
    test_case("spenta/accesa, 1249 silenced", f,
         _n(declared_fix="spenta"), _n(declared_fix="enabled", silenced=1249), True)
    # ⛔⛔ AND SINCE 24 AUGUST 2026 THIS CASE IS THE MOST IMPORTANT OF THE FOUR:
    #     the two arms ARE the same binary by construction, so «two identical
    #     runs with the name of two» is no longer a build accident —
    #     it is what happens if `--no-audio-silence` does not reach the server.
    #     ⇒ This predicate is the only thing that tells it apart from «the cure is not
    #     needed», which is the opposite conclusion.
    test_case("⛔ both arms declare «spenta»: the option did not arrive", f,
         _n(declared_fix="spenta"), _n(declared_fix="spenta", silenced=0), False)
    test_case("⛔ accesa but zero silenced", f,
         _n(declared_fix="spenta"), _n(declared_fix="enabled", silenced=0), False)
    test_case("⚠ the log does not have the line", f,
         _n(declared_fix="spenta"), _n(declared_fix="enabled", silenced=None), None)

    log("5 · ⛔⛔ `a_sound_is_untouched` — the predicate that protects the user")
    f = a_sound_is_untouched()
    test_case("coverage 0.998 → 0.997, tone 1.00 → 1.00", f,
         _n(coverage=0.998, tone_purity=1.0),
         _n(coverage=0.997, tone_purity=1.0), True)
    test_case("⛔ coverage 0.998 → 0.700: the cure eats sound", f,
         _n(coverage=0.998, tone_purity=1.0),
         _n(coverage=0.700, tone_purity=0.9), False)
    test_case("⛔ same coverage but the tone collapses", f,
         _n(coverage=0.998, tone_purity=1.0),
         _n(coverage=0.998, tone_purity=0.5), False)

    log("6 · `a_with_tone_only_first_is_silent` — is the scene the one I think?")
    f = a_with_tone_only_first_is_silent()
    test_case("with the tone, zero silenced", f, {}, _n(silenced=0), True)
    test_case("⛔ with the tone, 300 silenced: the scene has gaps of digital zero", f,
         {}, _n(silenced=300), False)

    log("7 · `a_opus_costs_less_than_pcm` — the refutation, in one number")
    f = a_opus_costs_less_than_pcm(10.0)
    test_case("PCM 1555 against Opus 1.2 kbit/s", f,
         _n(load_kbit_s=1555.0), _n(load_kbit_s=1.2), True)
    test_case("⛔ PCM 1555 against Opus 500: it is not a factor of ten", f,
         _n(load_kbit_s=1555.0), _n(load_kbit_s=500.0), False)

    log("8 · `a_pcm_gets_refused` — the positive control of the network")
    f = a_pcm_gets_refused(100)
    test_case("1823 refused", f, _n(server_refused=1823), {}, True)
    test_case("⛔ 4 refused: the profile does not bite", f, _n(server_refused=4), {}, False)
    test_case("⚠ count not read", f, _n(server_refused=None), {}, None)

    log("9 · `a_opus_holds_where_pcm_gives_way`")
    f = a_opus_holds_where_pcm_gives_way(20)
    test_case("PCM 366‰ against Opus 2‰", f,
         _n(server_refused=1823, shipped_server=3160),
         _n(server_refused=2, shipped_server=1240), True)
    test_case("⛔ Opus 120‰: it does not hold", f,
         _n(server_refused=1823, shipped_server=3160),
         _n(server_refused=150, shipped_server=1100), False)

    log("10 · ⭐⭐ `a_coverage_rises` — the quantity that counts")
    f = a_coverage_rises(0.10)
    test_case("0.63 → 0.99", f, _n(wire_coverage=0.6264),
         _n(wire_coverage=0.99), True)
    test_case("⛔ 0.63 → 0.66: within the noise", f,
         _n(wire_coverage=0.6264), _n(wire_coverage=0.66), False)
    test_case("⚠ one of the two was not judged", f,
         _n(wire_coverage=0.6264), _n(wire_coverage=None), None)

    log("11 · ⚠ `a_price_is_declared` — it is not a green and not a red")
    f = a_price_is_declared()
    test_case("the price is always written", f, _n(missed=0), _n(missed=1200), None)

    log("OUTCOME OF THE CERTIFICATION")
    if all(outcomes):
        ok("%d cases out of %d: the predicates can give green, red and «I do not judge»"
           % (sum(outcomes), len(outcomes)))
        return True
    ko("%d cases out of %d did NOT give the expected outcome: the bench is not a "
       "tool as long as this line is red" % (len(outcomes) - sum(outcomes), len(outcomes)))
    return False


# ═══════════════════════════════════════════════════════════════════════════
# THE MEASUREMENTS
# ═══════════════════════════════════════════════════════════════════════════
def measure_mute(seconds):
    log("SCENE «MUTO» — desktop still, Opus negotiated, cure off against on")
    inf("⛔ it is the product's NORMAL scene: `[M]` on the user's real session "
        "the datagram payload is 3 bytes, that is digital silence")
    s = cur_round("spenta", "mute", "opus", seconds)
    a = cur_round("enabled", "mute", "opus", seconds)
    v, r, m = judge("THE VERDICT — silent scene",
                      [a_fill_is_there(), a_fix_trims(8.0),
                       a_datagrams_disappear(), a_fix_has_spoken(),
                       a_price_is_declared()], s, a)
    return {"scene": "mute", "spenta": s, "enabled": a,
            "greens": v, "rossi": r, "silent": m}


def measure_tone(seconds):
    log("SCENE «TONO» — 440 Hz in the sink, PCM (for the samples judge)")
    inf("⛔ it is the CONTROL that protects the user: with the tone on the cure must "
        "silence nothing, and the coverage must not move")
    s = cur_round("spenta", "tone", "pcm", seconds)
    a = cur_round("enabled", "tone", "pcm", seconds)
    v, r, m = judge("THE VERDICT — scene with the tone",
                      [a_sound_is_untouched(), a_with_tone_only_first_is_silent()],
                      s, a)
    return {"scene": "tone", "spenta": s, "enabled": a,
            "greens": v, "rossi": r, "silent": m}


def measure_cost(seconds):
    log("THE COST OF THE TWO CODECS — PCM against Opus, same scene, cure OFF")
    inf("⭐ it is the refutation: the 2 463 kbit/s of `09-b81` and the 36 % of `09-b77` "
        "are PCM numbers, and the product negotiates Opus")
    p = cur_round("spenta", "mute", "pcm", seconds)
    o = cur_round("spenta", "mute", "opus", seconds)
    v, r, m = judge("THE VERDICT — what the audio costs",
                      [a_opus_costs_less_than_pcm(10.0)], p, o)
    return {"scene": "cost", "pcm": p, "opus": o, "greens": v, "rossi": r, "silent": m}


def measure_tight(profile_name, seconds):
    """⛔ HERE THE NETWORK IS BROKEN: lock, `lo` only, filters on my
       port only, detached guardian, and everything released in a `finally`."""
    prof = None
    for p in B77.PROFILES:
        if p[0] == profile_name:
            prof = p
    if prof is None:
        ko("the profile «%s» is not in 09-b77" % profile_name)
        return None
    log("THE NARROW NETWORK — profile «%s», PCM against Opus, cure OFF" % profile_name)
    inf("⛔ both runs under the SAME `netem`, set once and "
        "left standing: only the codec changes")
    LOCK.take(CHI, seconds=900, wait=3600)
    try:
        NETWORK.guardian_arm(900)
        NETWORK.broken(prof[1])
        # ⛔ SCENE WITH THE TONE, not silent: the question is what happens
        #    to REAL audio when the window narrows.  On a silent scene
        #    PCM would send 192 blocks of zeros a second and the comparison
        #    would measure the cost of silence, which is something else.
        p = cur_round("spenta", "tone", "pcm", seconds)
        o = cur_round("spenta", "tone", "opus", seconds)
    finally:
        try:
            NETWORK.restore()
        except Exception as e:
            ko("⛔ the `netem` was not removed: %s" % e)
        try:
            NETWORK.guardian_disarm()
        except Exception:
            pass
        LOCK.release(CHI)
    v, r, m = judge("THE VERDICT — who holds when the window narrows",
                      [a_pcm_gets_refused(100),
                       a_opus_holds_where_pcm_gives_way(20),
                       a_coverage_rises(0.10)], p, o)
    return {"scene": "stretta-%s" % profile_name, "pcm": p, "opus": o,
            "greens": v, "rossi": r, "silent": m}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("step", nargs="?", default="status",
                    choices=("status", "terrain", "build", "mute", "tone",
                             "cost", "squeeze", "all"))
    ap.add_argument("--seconds", type=int, default=25)
    ap.add_argument("--profile", default="bad-home")
    ap.add_argument("--certify", action="store_true")
    a = ap.parse_args()

    if a.certify:
        sys.exit(0 if certify() else 1)

    if a.step == "status":
        terrain_check()
        return
    if a.step == "terrain":
        sys.exit(0 if terrain_check() else 2)
    if a.step == "build":
        sys.exit(0 if build() else 2)

    if not terrain_check():
        ko("⛔ I do NOT measure on a ground that is not mine")
        sys.exit(2)

    report = []
    if a.step in ("mute", "all"):
        report.append(measure_mute(a.seconds))
    if a.step in ("tone", "all"):
        report.append(measure_tone(a.seconds))
    if a.step in ("cost", "all"):
        report.append(measure_cost(a.seconds))
    if a.step in ("squeeze", "all"):
        r = measure_tight(a.profile, a.seconds)
        if r:
            report.append(r)

    fpath = os.path.join(OUT, "esiti.json")
    with open(fpath, "w") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    log("THE VERDICT OF THE WHOLE BENCH")
    V = sum(x["greens"] for x in report)
    R = sum(x["rossi"] for x in report)
    M = sum(x["silent"] for x in report)
    inf("the numbers in full: %s" % fpath)
    (ok if R == 0 else ko)("%d green · %d red · %d not judged" % (V, R, M))
    sys.exit(0 if R == 0 else 1)


# ═══════════════════════════════════════════════════════════════════════════
# §PADDING — ⛔⛔⛔ THE HALF OF THE CURE THIS BENCH HAD ASKED FOR WAS
#            TRIED ON 24 AUGUST 2026, **IS NOT DONE**, AND MY DIAGNOSIS WAS
#            WRONG.  It is left written in full: it is the part that teaches.
#
# ⛔ WHAT I HAD WRITTEN HERE: that the 557 kbit/s of an idle session were
#    padding requested by `dgram_write_one()` with
#    `NGTCP2_WRITE_DATAGRAM_FLAG_PADDING` (`src/webtransport.c:1613` and `:1647`),
#    and that it was enough to make that flag conditional on there being a batch to
#    compose.  ⚠ It was a DEDUCTION — I had the number (48.0 datagrams in 48.4
#    packets of 1 441 bytes) and I had stuck next to it a cause that
#    nobody had measured (`LESSONS.md` §1.9).
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
# ⭐⭐⭐ AND IT IS KNOWN WHO FILLS IT — `[R]`: `wt_write()` asks for
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
    main()
