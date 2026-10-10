#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-attore — A SIMULATED USER of phase 16 (fasi/16-stress-e-capacita.md §4, §5, §7)

    python3 16-attore.py --container_box gnome|kde|xfce|lxqt --username N (1..16) \\
        --wayland wayland-K --dir DIR --seed S \\
        [--largo 3840 --alto 2160] [--base-ports P] [--video URL] [--host 192.168.0.2]
    python3 16-attore.py --certify

Runs ON THE SERVER as nicfio (it is nicfio who sets up the environment of the 15 benches: labwc
`--wayland`, local `sudo podman exec`).  One process = one person:

  browser   odd N Firefox (Marionette, port P), even N Chrome (CDP, port P+1)
  profile   N%4: 1 A browsing · 2 B file manager · 3 C terminal · 0 D 4K video
  tenant    c16<NNN>u<N> (e.g. c16001u1), random password, created here and CLEARED
            always on exit (normal end, SIGTERM, SIGINT, exception).
            ⛔ One single access attempt, with the right password: never a ban.

  1. creates the tenant, turns on the browser in its labwc, prepares the home;
  2. ENTERS: measures access (submit → «Admitted») and first frame (submit →
     `painted > 0`), then checks that the desktop is not degenerate ⇒ nascita.json;
  3. launches the profile's application INSIDE the session (16-lavori.py);
  4. works in a loop until SIGTERM, with REAL input from the browser and the rhythm
     drawn from random.Random(«seed:user») — repeatable across campaigns.

  DIR/utente-NN/stato.jsonl   ONLY state rows, every 5 s, in the schema of
                              16-classifica.py: t, profile_v, tenant, counts
                              (cumulative: delivered painted salt holes tard
                              received_n played BUCHI missed), diary (the page's
                              «audio: …» line AS IT IS), lap
                              (REMOTIX.lap: seen_items, samples), input
                              [{ok, latenza_ms, action}], blocco_max_ms, work,
                              drop, errors; and also diario_letto, delta,
                              acts, checks, dettagli_lavoro, events
  DIR/utente-NN/eventi.jsonl  start, birth, application, picture, failure, fine
  DIR/utente-NN/nascita.json  {access_ms, primo_fotogramma_ms (times in ms
                              from the epoch), nascita_ms (the duration), outcome "ok"|…}
  SIGUSR1                     full photo of the canvas in DIR/utente-NN/picture-<t>.png
  on exit                     console-<browser>.txt and registro-pagina.txt

Exit code: 0 stopped by SIGTERM/SIGINT after having worked · 1 the access or
the start did not succeed · 2 bench error.
"""
import argparse
import importlib.util as _iu
import io
import json
import math
import os
import random
import re
import secrets
import signal
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
BENCHES = os.path.dirname(HERE)
SUITE = os.path.join(BENCHES, "15-suite")
DESKTOP = ("gnome", "kde", "xfce", "lxqt")


def _load(label_name, file):
    s = _iu.spec_from_file_location(label_name, file)
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


L = _load("lavori16", os.path.join(HERE, "16-lavori.py"))


# ═══════════════════════════════════════════════════════════════════════════
#  THE RHYTHM — one person, repeatable (pure function)
# ═══════════════════════════════════════════════════════════════════════════
class Rate:
    """Pauses, choices and typing speed of ONE person.  ⭐ Everything from
    `random.Random("remotix16:<seed>:<username>")`: the same climb redone
    (Intel/Radeon) has the same choices in the same order; different users
    have different rhythms even with the same seed."""

    def __init__(self, seed, username, source=None):
        self.r = source or random.Random("remotix16:%s:%d" % (seed, username))
        self.base_ms = self.r.uniform(110, 240)        # the person's mean keystroke
        self.slowness = self.r.uniform(0.7, 1.5)       # scale of their pauses

    def keystroke_ms(self):
        v = self.r.lognormvariate(math.log(self.base_ms), 0.35)
        if self.r.random() < 0.04:
            v += self.r.uniform(300, 900)              # a hesitation
        return max(40.0, min(1500.0, v))

    def hold_ms(self):
        return self.r.uniform(35, 95)

    def pause_s(self, kind="brief"):
        if kind == "gesture":
            v = self.r.uniform(0.15, 0.6)
        elif kind == "leggere":
            v = self.r.uniform(5.0, 18.0) * self.slowness
        else:
            v = self.r.lognormvariate(math.log(2.0), 0.5) * self.slowness
        return max(0.1, min(30.0, v))

    def choose(self, entries, weights=None):
        return self.r.choices(list(entries), weights)[0]

    def whole(self, a, b):
        return self.r.randint(a, b)

    def uniform(self, a, b):
        return self.r.uniform(a, b)

    def probable(self, p):
        return self.r.random() < p

    def digits(self, n):
        return "".join(str(self.r.randint(0, 9)) for _ in range(n))


def fingerprint(rate, n=300):
    """The sequence of `n` draws of all kinds (for the certification)."""
    out = []
    for i in range(n):
        out += [round(rate.keystroke_ms(), 6), round(rate.pause_s(("gesture", "brief", "leggere")[i % 3]), 6),
                rate.choose("abcd", (1, 2, 3, 4)), rate.whole(1, 99), rate.digits(2)]
    return out


def repeatable(factory, n=300):
    """⭐ Do two rhythms from the same factory give the same sequence?"""
    return fingerprint(factory(), n) == fingerprint(factory(), n)


# ═══════════════════════════════════════════════════════════════════════════
#  THE PAGE'S DIARY — the «audio: …» line the page sends every 5 s
#  (src/pagina.html ~6970), read as it is (pure function)
# ═══════════════════════════════════════════════════════════════════════════
# names of the audio half (before « | ») and of the page half (after)
_AUDIO = {"received_n": "received_n", "played": "played", "BUCHI": "BUCHI", "stale": "stale",
          "late": "late", "outside": "audio_fuori_ordine", "rec": "recovered",
          "dup": "duplicates", "filled": "filled", "errors": "audio_errori", "missed": "missed",
          "times": "missed_times", "exited": "audio_usciti", "cut": "cut",
          "pending": "pending", "jumps": "sound_jumps", "risv": "wakeups", "queue": "queue_ms"}
_PAGE = {"keys": "keys", "painted": "painted", "outside": "video_fuori", "inside": "video_dentro",
           "dec_queue": "dec_queue", "bmp": "bmp", "salt": "salt", "holes": "holes", "ord": "ord",
           "mis": "mis", "tard": "tard", "err": "err", "voff": "voff", "AV": "AV_ms"}


def _whole(t):
    m = re.match(r"^([+-]?\d+)", t or "")
    return int(m.group(1)) if m else None


def read_diary_line(row):
    """⭐ The diary line ⇒ dict.  A field that is not there stays None («not
    read»), NEVER zero: an invented zero is a false green."""
    if not row or not row.startswith("audio: "):
        return None
    audio, _, page_v = row[len("audio: "):].partition(" | ")
    d = {v: None for v in list(_AUDIO.values()) + list(_PAGE.values())}
    d.update({"video_consegnati": None, "video_dipinti": None, "display_screen": None, "focus": None,
              "classic": None, "ctx": None})
    for part, table in ((audio, _AUDIO), (page_v, _PAGE)):
        p = part.split()
        for i in range(len(p) - 1):
            if p[i] in table and d[table[p[i]]] is None:
                d[table[p[i]]] = _whole(p[i + 1])
    p = page_v.split()
    for i in range(len(p) - 1):
        if p[i] == "video" and "→" in p[i + 1]:
            a, _, b = p[i + 1].partition("→")
            d["video_consegnati"], d["video_dipinti"] = _whole(a), _whole(b)
        elif p[i] in ("display_screen", "focus", "classic"):
            d[p[i]] = p[i + 1]
    pa = audio.split()
    for i in range(len(pa) - 1):
        if pa[i] == "ctx":
            d["ctx"] = pa[i + 1]
    return d


def differences(before, after, names):
    """The growths of the counters between two readings.  ⚠ A counter that DROPS (the
    page reloaded, the session reborn) is not a negative growth: it is
    «reset», and its delta is None."""
    out, zeroed = {}, []
    for n in names:
        a, b = (before or {}).get(n), (after or {}).get(n)
        if a is None or b is None:
            out[n] = None
        elif b < a:
            out[n] = None
            zeroed.append(n)
        else:
            out[n] = b - a
    return out, zeroed


JS_DIARY = r"""
const da = arguments[0] || 0;
const R = window.REMOTIX, s = R && R.display_screen, reg = document.getElementById('logbook');
const t = reg ? reg.textContent : '';
const i = t.lastIndexOf('audio: received_n');
let row = null;
if (i >= 0) { const j = t.indexOf('\n', i); row = j < 0 ? t.slice(i) : t.slice(i, j); }
const new_ones = (da <= t.length ? t.slice(da) : t).split('\n')
  .filter(r => r.indexOf('⛔') >= 0 || r.indexOf('MEASURE') === 0).slice(-20).map(r => r.slice(0, 300));
const c = s && s.counts;
const e = document.getElementById('outcome');
const G = R && R.lap;
const lap = G && G.samples ? { seen_items: G.seen_items, samples: G.samples.map(x => Math.round(x * 10) / 10) } : null;
const dt = window.__C16 ? window.__C16.t.splice(0) : null;
const gt = window.__C16 && window.__C16.g ? window.__C16.g.splice(0) : null;
return { row: row, lung: t.length, lap: lap, painted_t: dt, gesti_t: gt, new_ones: new_ones, session_v: !!(s && s.session_v),
  display_screen: document.body ? (document.body.dataset.display_screen || null) : null,
  focus: document.hasFocus(), is_visible: document.visibilityState,
  outcome: e ? e.textContent.slice(0, 200) : null, esito_classe: e ? e.className : null,
  counts: c ? { painted: c.painted, delivered: c.delivered, skipped_queue: c.skipped_queue,
               holes: c.holes, keys_requested: c.keys_requested, belated: c.belated,
               discarded_order: c.discarded_order, discarded_measure: c.discarded_measure,
               exited: c.exited } : null };
"""
COUNTS_DELTA = ("delivered", "painted", "salt", "holes", "tard", "keys_requested",
               "received_n", "played", "BUCHI", "missed")

# ⭐ The paint probe: in the REAL page, every 10 ms it looks at `counts.painted`
#   and notes the time (Date.now: the same clock as the actor, same machine)
#   of every change.  JS_DIARY takes them and empties them every 5 s.
PAINT_PROBE = r"""
(function () {
  if (window.__C16) return;
  const C = window.__C16 = { t: [], g: [], last: null };
  /* ⭐ The time of the GESTURES as the page receives them (same clock as the paints):
     `key_times` rebuilt it from the return of Marionette, and a held-back
     chain put the key AFTER its own echo (fasi/20 §3-bis.2).
     In capture on window: it arrives before any handler of the page. */
  const g = function (kind) {
    return function (e) {
      C.g.push([Date.now(), kind, kind === 'k' ? String(e.key) : '']);
      if (C.g.length > 20000) C.g.splice(0, 5000);
    };
  };
  window.addEventListener('keydown', g('k'), true);
  window.addEventListener('pointerdown', g('p'), true);
  window.addEventListener('wheel', g('w'), { capture: true, passive: true });
  setInterval(function () {
    const s = window.REMOTIX && window.REMOTIX.display_screen;
    const d = s && s.counts ? s.counts.painted : null;
    if (d === null || d === C.last) return;
    if (C.last !== null) { C.t.push(Date.now()); if (C.t.length > 20000) C.t.splice(0, 5000); }
    C.last = d;
  }, 10);
})();
"""


def counts_ranking(c, diary):
    """⭐ The CUMULATIVE counters with the names 16-classifica.py reads: from the
    page (`REMOTIX.display_screen.counts`) and, for the audio, from the diary line.
    Only those that are there: a None here would make the classifier believe
    it had read it."""
    out = {}
    c = c or {}
    for my, its in (("delivered", "delivered"), ("painted", "painted"), ("salt", "skipped_queue"),
                     ("holes", "holes"), ("tard", "belated"), ("keys_requested", "keys_requested")):
        if c.get(its) is not None:
            out[my] = c[its]
    d = diary or {}
    for k in ("received_n", "played", "BUCHI", "missed"):
        if d.get(k) is not None:
            out[k] = d[k]
    for my, its in (("delivered", "video_consegnati"), ("painted", "video_dipinti"),
                     ("salt", "salt"), ("holes", "holes"), ("tard", "tard")):
        if my not in out and d.get(its) is not None:
            out[my] = d[its]
    return out


JS_ROUND = r"""
const G = window.REMOTIX && window.REMOTIX.lap;
return G && G.samples ? { seen_items: G.seen_items, samples: G.samples.map(x => Math.round(x * 10) / 10) } : null;
"""


def new_samples(before, after):
    """⭐ The ROUND samples arrived between two readings of `REMOTIX.lap`
    ({seen_items, samples: the last 200}): the last `after.seen_items − before.seen_items`.
    Taken ONLY around typing with immediate echo, they are the delay of the
    PRODUCT (the character appears at once), without the reaction time
    of the application (a page loading, a window opening).
    ⚠ If more arrived than the list holds, those
    that are there are taken; a missed reading ⇒ no sample (never invented)."""
    if not before or not after or after.get("samples") is None:
        return []
    n = (after.get("seen_items") or 0) - (before.get("seen_items") or 0)
    if n <= 0:
        return []
    return list(after["samples"])[-n:]


def pulse_waits(pulses, painted_t, now, cap_s=5.0):
    """⭐ For every impulse (an input that MUST change the image), the wait
    until the first paint AFTER it.  ⇒ (waits in s, impulses still open).
    An impulse without a paint for more than `cap_s` is closed with the wait so
    far (it is a freeze, it is not thrown away)."""
    waits, opened = [], []
    pt = sorted(painted_t)
    for e in sorted(pulses):
        after = next((x for x in pt if x > e), None)
        if after is not None:
            waits.append(after - e)
        elif now - e > cap_s:
            waits.append(now - e)
        else:
            opened.append(e)
    return waits, opened


def longest_pause(painted_t, da, a):
    """⭐ The longest still of the image in [da, a] (video: it must always
    change), edges included: from the last paint before `da`, up to `a`."""
    pt = sorted(painted_t)
    before = [x for x in pt if x <= da]
    points = ([before[-1]] if before else [da]) + [x for x in pt if da < x <= a] + [a]
    return max((y - x for x, y in zip(points, points[1:])), default=a - da)


CAP_DEGENERATE_S = 15      # §9: the desktop not degenerate within 15 s of access (FAIL beyond)


def outcome_birth(green_v, red):
    """(outcome, note) of nascita.json from the judgement of the desktop.  ⭐ Only a RED
    (still degenerate at the cap) is «degenerate»; a judgement that could not be
    given (blind photo) is NOT a defect of the product: «ok», with the note."""
    if green_v:
        return "ok", None
    if red:
        return "degenerate", None
    return "ok", "desktop not measured (the photo could not be judged)"


def works_after_birth(birth):
    """⭐ The actor works if it has the first frame (the session is there), even
    with a degenerate or unchecked desktop: the load is not removed."""
    return bool(birth.get("primo_fotogramma_ms")) and "rifiut" not in str(birth.get("outcome"))


def key_times(t_return, durations_ms):
    """⭐ The time of every key of a Marionette chain, derived from the RETURN of
    `PerformActions` (which returns when the last pause is over): key i was
    pressed `sum(durations[i:])` before.  ⛔ With the time taken BEFORE the
    call, Marionette's delay under load ended up in the «freeze»."""
    out, rest = [], sum(durations_ms) / 1000.0
    for d in durations_ms:
        out.append(t_return - rest)
        rest -= d / 1000.0
    return out


def gesture_matches(expected_val, received_one):
    """The gesture typed by the actor and the one received by the page are the
    same kind; for a printable character also the same key (an Enter,
    a Tab, a special key: the kind is enough, the names change between engines)."""
    kind, key = expected_val
    if received_one[1] != kind:
        return False
    printable = lambda t: len(t) == 1 and t.isprintable() and not t.isspace()  # noqa: E731
    if kind == "k" and key and printable(key):
        return received_one[2] == key
    if kind == "k":
        # a special key is not confused with a letter typed without a wait before it
        return not printable(received_one[2] or "")
    return True


def align_pulses(pending, gestures, tolerance_s=0.25, behind_s=10.0):
    """⭐ The TRUE time of the impulses: for every impulse of the actor (estimated time,
    gesture), in order, the first still-free gesture of the same kind that the
    page received no later than `tolerance_s` after the estimate.  ⇒ the times to
    use (the page's, or the estimate if the page did not see it: a
    gesture that does not arrive stays an impulse, and if the image does not change it is a
    real freeze).  `gestures`: [[ms, kind, key], …] from the probe.
    ⚠ The estimate of `key_times` is never BEFORE the real gesture: a chain
    held back by Marionette moves FORWARD all the keys typed before
    the stop, until beyond their echo, and the wait became that of the
    next paint (the blinking cursor: ~1.1 s, fasi/20 §3-bis.2)."""
    gs = sorted(((g[0] / 1000.0, g[1], g[2] if len(g) > 2 else "") for g in (gestures or [])),
                key=lambda g: g[0])
    out, j = [], 0
    for estimate, gesture in pending:
        k = j
        while k < len(gs) and not (estimate - behind_s <= gs[k][0] <= estimate + tolerance_s
                                   and gesture_matches(gesture, gs[k])):
            if gs[k][0] > estimate + tolerance_s:
                k = len(gs)
                break
            k += 1
        if gesture is not None and k < len(gs):
            out.append(gs[k][0])
            j = k + 1
        else:
            out.append(estimate)
    return out


class Fine(Exception):
    """SIGTERM / SIGINT: work stops and the tenant is cleared."""


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION — the pure functions, with INJECTED FAULTS
# ═══════════════════════════════════════════════════════════════════════════
LINE_EXAMPLE = ("audio: received_n 1200 played 1188 BUCHI 2 stale 3 late 0 outside 5 rec 1 "
                "dup 0 filled 0 errors 0 missed 7 times 3 exited 1180 cut 0 pending 0 "
                "jumps 0 risv 1 queue 270ms dec wasm 55/210us usc 12ms aoff 40 ctx running"
                " | keys 88 last KeyA classic si display_screen lit painted 5000 video "
                "5210→5000 outside 5100 inside 110 dec_queue 2 bmp 0 salt 90 holes 1 ord 0 mis 0 "
                "tard 0 err 0 voff 33 AV +7ms focus si")


def certify():
    troubles = []

    def prova(what, real, det=""):
        print("   %s %s%s" % ("⭐ ok " if real else "⛔ NO ", what, (" — " + det) if det else ""))
        if not real:
            troubles.append(what)

    print("── the rhythm")
    prova("same seed and user ⇒ same sequence", repeatable(lambda: Rate("s1", 3)))
    prova("different users ⇒ different sequences",
          fingerprint(Rate("s1", 3)) != fingerprint(Rate("s1", 4)))
    prova("different seeds ⇒ different sequences",
          fingerprint(Rate("s1", 3)) != fingerprint(Rate("s2", 3)))
    # ⛔ FAULT: a rhythm without a seed (from the clock) must turn out NOT repeatable
    prova("FAULT seen: rhythm without seed ⇒ not repeatable",
          not repeatable(lambda: Rate("s1", 3, source=random.Random())))
    r = Rate("s1", 5)
    b = [r.keystroke_ms() for _ in range(3000)]
    media = sum(b) / len(b)
    prova("keystrokes between 40 and 1500 ms, human mean (80-400 ms)",
          min(b) >= 40 and max(b) <= 1500 and 80 <= media <= 400, "mean %.0f ms" % media)
    pp = {k: [r.pause_s(k) for _ in range(500)] for k in ("gesture", "brief", "leggere")}
    prova("pauses: gesture < brief < leggere (on average)",
          sum(pp["gesture"]) < sum(pp["brief"]) < sum(pp["leggere"]),
          " ".join("%s %.1f s" % (k, sum(v) / len(v)) for k, v in pp.items()))
    bases = {round(Rate("s1", n).base_ms) for n in range(1, 17)}
    prova("16 people, 16 different speeds", len(bases) == 16, str(sorted(bases)))

    print("── the page's diary")
    d = read_diary_line(LINE_EXAMPLE)
    prova("sample line read", d is not None)
    expected_val = {"received_n": 1200, "played": 1188, "BUCHI": 2, "missed": 7, "missed_times": 3,
              "audio_fuori_ordine": 5, "video_fuori": 5100, "video_consegnati": 5210,
              "video_dipinti": 5000, "salt": 90, "holes": 1, "painted": 5000, "queue_ms": 270,
              "keys": 88, "AV_ms": 7, "focus": "si", "display_screen": "lit", "ctx": "running"}
    wrong = {k: (d or {}).get(k) for k, v in expected_val.items() if (d or {}).get(k) != v}
    prova("every field at its value (the two «outside» NOT confused)", not wrong, str(wrong))
    # ⛔ FAULT: the line without BUCHI ⇒ BUCHI None (not read), never 0
    g = read_diary_line(LINE_EXAMPLE.replace(" BUCHI 2", ""))
    prova("FAULT seen: BUCHI removed from the line ⇒ None, not zero", g and g["BUCHI"] is None,
          "BUCHI=%r" % (g or {}).get("BUCHI"))
    # ⛔ FAULT: BUCHI changed ⇒ the value read changes
    g = read_diary_line(LINE_EXAMPLE.replace(" BUCHI 2", " BUCHI 41"))
    prova("FAULT seen: BUCHI 41 ⇒ read 41", g and g["BUCHI"] == 41)
    g = read_diary_line(LINE_EXAMPLE.split(" | ")[0])
    prova("FAULT seen: without the page half ⇒ video None", g and g["video_dipinti"] is None
          and g["salt"] is None)
    prova("a line about something else ⇒ None", read_diary_line("MEASURE something") is None)
    dd, az = differences({"painted": 100, "holes": 1}, {"painted": 160, "holes": 1},
                        ("painted", "holes", "salt"))
    prova("differences: growth and missing field", dd == {"painted": 60, "holes": 0, "salt": None}
          and not az, str(dd))
    # ⛔ FAULT: the reloaded page resets the counters ⇒ «reset», not a negative delta
    dd, az = differences({"painted": 900}, {"painted": 12}, ("painted",))
    prova("FAULT seen: counter that drops ⇒ reset, delta None",
          dd["painted"] is None and az == ["painted"])

    print("── the counters for the classifier")
    cc = counts_ranking({"delivered": 10, "painted": 9, "skipped_queue": 1, "holes": 0,
                           "belated": 0, "keys_requested": 2}, d)
    prova("classifier names, audio from the diary", cc == {
        "delivered": 10, "painted": 9, "salt": 1, "holes": 0, "tard": 0, "keys_requested": 2,
        "received_n": 1200, "played": 1188, "BUCHI": 2, "missed": 7}, str(cc))
    cc = counts_ranking(None, None)
    prova("FAULT seen: no page ⇒ no counter (not zeros)", cc == {}, str(cc))
    cc = counts_ranking(None, d)
    prova("without direct counters ⇒ from the diary (video X→Y)", cc.get("delivered") == 5210
          and cc.get("painted") == 5000, str(cc))

    print("── the echo round (typing only)")
    g0 = {"seen_items": 10, "samples": [30.0] * 10}
    g1 = {"seen_items": 11, "samples": [30.0] * 10 + [1136.0]}            # a click that loads a page
    g2 = {"seen_items": 16, "samples": [30.0] * 10 + [1136.0] + [41.0, 38.5, 44.0, 40.2, 39.9]}
    echo = new_samples(g1, g2)                                      # around the typing only
    prova("the 5 samples of the typing, and only those", echo == [41.0, 38.5, 44.0, 40.2, 39.9],
          str(echo))
    # ⛔ FAULT: the difference taken from the start (before the click) carries in the 1136
    overall = new_samples(g0, g2)
    prova("FAULT seen: without the reading before the typing the loading click gets in",
          1136.0 in overall and 1136.0 not in echo, str(overall))
    prova("missed reading ⇒ no sample", new_samples(None, g2) == []
          and new_samples(g2, g2) == [])
    g3 = {"seen_items": 500, "samples": [float(i) for i in range(200)]}
    prova("more samples than the list ⇒ those that are there", len(new_samples(g0, g3)) == 200)

    print("── the freeze of the image")
    at, ap = pulse_waits([10.0, 12.0, 19.5], [10.2, 10.25, 13.5], 20.0)
    prova("waits: 0.2 s and 1.5 s, the last still open",
          [round(x, 2) for x in at] == [0.2, 1.5] and ap == [19.5], "%s %s" % (at, ap))
    # ⛔ FAULT: the image no longer changes after the input ⇒ the wait becomes a freeze
    at, ap = pulse_waits([10.0], [9.0], 16.0)
    prova("FAULT seen: no paint after the input ⇒ freeze of 6 s", at == [6.0] and not ap,
          str(at))
    pl = longest_pause([x / 30.0 for x in range(0, 300)], 2.0, 9.9)
    prova("video at 30 per second ⇒ still of ~33 ms", 0.03 <= pl <= 0.04, "%.3f s" % pl)
    hole = [x / 30.0 for x in range(0, 300) if not 150 <= x < 210]
    pl = longest_pause(hole, 2.0, 9.9)
    # ⛔ FAULT: 2 s without frames in the middle of the video ⇒ seen
    prova("FAULT seen: 2 s without frames ⇒ still of 2 s", 1.9 <= pl <= 2.1, "%.3f s" % pl)
    pl = longest_pause([1.0, 1.1], 2.0, 7.0)
    prova("FAULT seen: video stuck since before the window ⇒ whole still", pl >= 5.9,
          "%.1f s" % pl)

    print("── the input checks")
    st = "ls -la ~/prova16 #k3\nfind /usr/share -name '*.png' | head -n 60 #k4\n"
    prova("history: the exact line is there", L.history_contains(st, "ls -la ~/prova16 #k3"))
    # ⛔ FAULT seen on 27 Sep (LXQt): Del + Enter never deleted — the
    #   pcmanfm-qt dialog has «No» as default.  ⇒ Shift+Del and «y».
    pc = {s: L.delete_plan(s) for s in ("gnome", "kde", "xfce", "lxqt")}
    prova("FAULT seen: on LXQt deletion is Shift+Del and the answer «y», never Enter",
          pc["lxqt"][:3] == (["Shift"], "Delete", "y") and pc["lxqt"][4] is True, str(pc["lxqt"]))
    prova("on the other desktops Del, and Enter only if needed",
          all(pc[s] == ([], "Delete", "Enter", 2.5, False) for s in ("gnome", "kde", "xfce")))
    # ⛔ FAULT: a character lost on the way ⇒ KO
    prova("FAULT seen: a lost character ⇒ KO",
          not L.history_contains(st, "ls -la ~/prova16 #k4")
          and not L.history_contains("ls -la ~/prova1 #k3\n", "ls -la ~/prova16 #k3"))
    # ⛔ FAULT seen on 27 Sep (LXQt): qterminal without SHELL opened dash ⇒ the
    #   bash history was never written, «first line NOT arrived» three times
    ps = ("263 255 lxqt-session\n900 263 qterminal\n905 900 dash\n910 263 pcmanfm-qt\n"
          "1000 263 gnome-terminal-\n1001 1000 bash\n")
    prova("FAULT seen: under qterminal there is dash, and it shows",
          L.shell_below(ps, "qterminal") == ["dash"], str(L.shell_below(ps, "qterminal")))
    prova("under gnome-terminal-server (name cut at 15) there is bash",
          L.shell_below(ps, "gnome-terminal") == ["bash"])
    prova("terminal absent ⇒ no shell, not an error",
          L.shell_below(ps, "konsole") == [] and L.shell_below("", "qterminal") == []
          and L.shell_below("crooked line\n", "qterminal") == [])
    prova("on LXQt qterminal is launched with explicit bash",
          L.APP["lxqt"]["term"][0] == "qterminal -e bash")
    q = L.read_notebook("1727.500 load testo 0 9000\n1727.900 scroll testo 1200 9000\n"
                         "broken\n1728.1 video yt t=12.40 state=1 q=hd2160 levels=hd2160,hd1440\n")
    prova("notebook: three good lines, the broken one discarded", len(q) == 3 and q[1][1] == "scroll"
          and q[1][2] == ["testo", "1200", "9000"], str(q))
    v = L.read_video(q[2][2])
    prova("video: t, state, quality", v.get("t") == 12.4 and v.get("state") == 1
          and v.get("q") == "hd2160", str(v))
    prova("video source: YouTube and file", L.video_source("https://www.youtube.com/watch?v=LXb3EKWsInQ")
          == ("yt", "LXb3EKWsInQ") and L.video_source("file:///rete11/v.mp4") == ("file", "/rete11/v.mp4")
          and L.video_source("ftp://x")[0] is None)

    print("── the text field of the local page (A)")
    page_map = L.pages_a()
    prova("the A pages do not take the focus away from the field by themselves",
          not any(L.field_left_alone(h) for h in page_map.values()))
    prova("the field is left with Esc and it says so («leave»)",
          all("'Escape'" in page_map[n + ".html"] and "send_it('leave '" in page_map[n + ".html"]
              for n in L.PAGES_A))
    # ⛔ FAULT: the earlier page (blur at 1.5 s from the last key) ⇒ seen
    old = page_map["testo.html"].replace(
        "tN = setTimeout(", "tB = setTimeout(() => remark.blur(), 1500); tN = setTimeout(")
    prova("FAULT seen: the timed blur in the page ⇒ recognised",
          L.field_left_alone(old))
    e_ok = (1727.5, "testo", ["testo", "alpha_ch", "net", "server"])
    prova("typed phrase = phrase in the field ⇒ ok", L.sentence_in_field(e_ok, "alpha_ch net server"))
    # ⛔ FAULT: the letters after a long pause ended up outside the field ⇒ KO
    e_ko = (1727.5, "testo", ["testo", "alpha_ch", "re"])
    prova("FAULT seen: lost letters ⇒ KO", not L.sentence_in_field(e_ko, "alpha_ch net server"))

    print("── the time of the gestures (from the return of the call)")
    ore = key_times(100.0, [200, 300, 500])
    prova("three keys of 200/300/500 ms returned at 100 s ⇒ 99.0 / 99.2 / 99.5",
          [round(x, 3) for x in ore] == [99.0, 99.2, 99.5], str(ore))
    # ⛔ FAULT: Marionette 2 s late: the paint of the key arrives at
    #   100.05 s; with the time SCHEDULED from the departure (97.0) the freeze is ~3 s,
    #   with the time from the return it is ~0.55 s
    scheduled = [97.0, 97.2, 97.5]
    at_old, _ = pulse_waits(scheduled[:1], [100.05], 101.0)
    at_new, _ = pulse_waits(ore[:1], [100.05], 101.0)
    prova("FAULT seen: Marionette's delay does NOT end up in the freeze",
          at_old[0] > 2.5 and at_new[0] < 1.2,
          "before %.2f s, now %.2f s" % (at_old[0], at_new[0]))

    print("── the time of the gestures (from the page)")
    # ⛔ FAULT seen on 7 Oct (fasi/20 §3-bis.2, intel-f20-fhd-xfce): Marionette holds back
    #   the chain 1.0 s AFTER the last key.  Real keys at 100.0/100.2/100.5, echo painted
    #   30 ms after each, the blinking cursor at 102.0; the chain returns at 102.0
    #   instead of 101.0 ⇒ the estimate puts every key 1 s after its echo.
    genuine = [100.0, 100.2, 100.5]
    painted = [100.03, 100.23, 100.53, 102.0]
    stime = key_times(102.0, [200, 300, 500])
    at_stime, _ = pulse_waits(stime, painted, 103.0)
    gestures = [[int(x * 1000), "k", c] for x, c in zip(genuine, "abc")]
    aligned = align_pulses([(t, ("k", c)) for t, c in zip(stime, "abc")], gestures)
    at_page, _ = pulse_waits(aligned, painted, 103.0)
    prova("FAULT seen: with the held-back Marionette estimate the freeze is ~1 s",
          max(at_stime) > 0.9, "%.2f s" % max(at_stime))
    prova("with the page's time Marionette's delay does NOT become a freeze",
          max(at_page) < 0.05 and [round(x, 3) for x in aligned] == genuine,
          "%.3f s, times %s" % (max(at_page), aligned))
    # a key the page never received stays an impulse (at the estimated time) ⇒ real freeze
    lost = align_pulses([(t, ("k", c)) for t, c in zip(stime, "abc")], gestures[:2])
    at_lost, ap_lost = pulse_waits(lost, painted[:2], 108.0)
    prova("FAULT seen: a key that never reached the page stays a freeze",
          lost[2] == stime[2] and max(at_lost) > 5.0, "%s %s" % (at_lost, ap_lost))
    al = align_pulses([(10.0, ("k", "x")), (10.3, ("k", "")), (10.6, ("p", "")), (10.9, ("w", ""))],
                         [[9800, "k", "y"], [9850, "k", "x"], [10100, "k", "Enter"],
                          [10400, "p", ""], [10700, "w", ""], [10750, "w", ""]])
    prova("every gesture with its kind and, for a character, with its key",
          [round(x, 2) for x in al] == [9.85, 10.1, 10.4, 10.7], str(al))
    prova("no probe ⇒ the earlier estimates", align_pulses([(5.0, ("k", "a"))], None) == [5.0])
    prova("an expected Enter does not take the letters typed without a wait before it",
          align_pulses([(10.5, ("k", ""))], [[10000, "k", "l"], [10100, "k", "s"],
                                                [10200, "k", "Enter"]]) == [10.2])
    prova("a gesture from well BEFORE the estimate is not its own",
          align_pulses([(50.0, ("k", "a"))], [[20000, "k", "a"]]) == [50.0])
    prova("a gesture well AFTER the estimate is not its own",
          align_pulses([(5.0, ("k", "a"))], [[9000, "k", "a"]]) == [5.0])

    print("── the birth")
    prova("green desktop ⇒ ok", outcome_birth(True, False) == ("ok", None))
    prova("degenerate at the cap ⇒ «degenerate»", outcome_birth(False, True)[0] == "degenerate")
    es, remark = outcome_birth(False, False)
    prova("not checked ⇒ ok with the note «not measured»", es == "ok" and "not measured" in remark)
    prova("the degenerate cap is the FAIL threshold of §9 (15 s)", CAP_DEGENERATE_S == 15)
    prova("with the first frame the actor WORKS (even degenerate)",
          works_after_birth({"primo_fotogramma_ms": 1, "outcome": "degenerate"})
          and works_after_birth({"primo_fotogramma_ms": 1, "outcome": "ok"}))
    # ⛔ FAULT: without first frame, or refused ⇒ does not work (it is not in session)
    prova("FAULT seen: no frame or refusal ⇒ does not work",
          not works_after_birth({"primo_fotogramma_ms": None, "outcome": "nessun_fotogramma"})
          and not works_after_birth({"outcome": "refusal"}))

    print("── the window in the photo")
    try:
        from PIL import Image, ImageDraw
        a = Image.new("RGB", (960, 540), (0, 0, 0))
        ImageDraw.Draw(a).rectangle([880, 0, 930, 12], fill=(200, 200, 200))    # clock
        b = a.copy()
        dr = ImageDraw.Draw(b)
        dr.rectangle([880, 0, 930, 12], fill=(90, 90, 90))                       # the clock changes
        dr.rectangle([200, 100, 700, 420], outline=(220, 220, 220), width=3)     # dark window
        dr.rectangle([200, 100, 700, 130], fill=(60, 60, 200))                   # its title bar
        dr.text((220, 200), "user@host:~$ ls", fill=(200, 200, 200))
        r = L.window_rect(a, b)
        prova("dark window on black background found (%s)" % (r,), r is not None and
              abs(r[0] - 200) <= 16 and abs(r[1] - 100) <= 16 and abs(r[2] - 700) <= 16
              and abs(r[3] - 420) <= 16)
        c = a.copy()
        ImageDraw.Draw(c).rectangle([880, 0, 930, 12], fill=(90, 90, 90))
        # ⛔ FAULT: only the clock changes ⇒ no window
        prova("FAULT seen: only the clock changes ⇒ no window",
              L.window_rect(a, c) is None)
    except ImportError:
        prova("PIL is there", False)

    print("── users, profiles, browsers")
    prof = "".join(L.profile_of(n) for n in range(1, 17))
    prova("profiles 1..16 = ABCD×4", prof == "ABCD" * 4, prof)
    br = [L.browser_di(n) for n in range(1, 17)]
    prova("odd Firefox, even Chrome", all(b == ("firefox" if n % 2 else "chrome")
                                             for n, b in zip(range(1, 17), br)))
    sg = re.compile(r"^c[0-9]+b?u[0-9]+$")
    names = [L.tenant_of(n) for n in range(1, 17)]
    prova("tenants recognised by the clean-up and all different",
          all(sg.match(x) for x in names) and len(set(names)) == 16, "%s … %s" % (names[0], names[-1]))
    ports = {L.internal_port(d, n) for d in DESKTOP for n in range(1, 17)}
    prova("internal ports all different (4 desktops × 16)", len(ports) == 64)
    print("⛔ CERTIFICATION FAILED (%d)" % len(troubles) if troubles else "⭐ CERTIFIED")
    return 1 if troubles else 0


# ═══════════════════════════════════════════════════════════════════════════
#  THE ENVIRONMENT — before importing the suite (it reads REMOTIX_ON_SERVER at import)
# ═══════════════════════════════════════════════════════════════════════════
def environment(o):
    u = os.getuid()
    os.environ.update({
        "XDG_RUNTIME_DIR": "/run/user/%d" % u,
        "WAYLAND_DISPLAY": o.wayland,
        "REMOTIX_NESTED_SCREEN": "1",
        "REMOTIX_ON_SERVER": "1",
        "MOZ_ENABLE_WAYLAND": "1",
        "REMOTIX_CHROME_OPTIONS": "--ozone-platform=wayland --disable-backgrounding-occluded-windows "
                                  "--disable-renderer-backgrounding --disable-background-timer-throttling "
                                  # ⭐ the extra options of the climb (e.g. --render-node-override)
                                  + os.environ.get("REMOTIX_16_CHROME_EXTRA", ""),
    })
    os.environ["REMOTIX_CHROME_OPTIONS"] = os.environ["REMOTIX_CHROME_OPTIONS"].strip()
    os.environ.pop("DISPLAY", None)


def call_args():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--certify", action="store_true")
    a.add_argument("--container_box", choices=DESKTOP)
    a.add_argument("--username", type=int)
    a.add_argument("--wayland", help="the socket of this user's labwc (wayland-K)")
    a.add_argument("--dir", help="the folder of the climb's evidence")
    a.add_argument("--seed", default="0")
    a.add_argument("--largo", type=int, default=3840)
    a.add_argument("--alto", type=int, default=2160)
    a.add_argument("--base-ports", type=int, default=0,
                   help="Firefox P, Chrome P+1 (by default 9700 + 4·N)")
    a.add_argument("--video", default="",
                   help="D users: YouTube URL, or a file (path INSIDE the box, /rete11/…)")
    a.add_argument("--host", default="192.168.0.2")
    a.add_argument("--cap-s", type=int, default=60, help="cap of the access and of the first frame")
    o = a.parse_args()
    if o.certify:
        return o
    for k in ("container_box", "username", "wayland", "dir"):
        if getattr(o, k) in (None, ""):
            a.error("--%s is needed" % k)
    if not 1 <= o.username <= 99:
        a.error("--username between 1 and 16 (up to 99 for overload)")
    if not o.base_ports:
        o.base_ports = 9700 + 4 * o.username
    return o


# ═══════════════════════════════════════════════════════════════════════════
#  THE ACTOR
# ═══════════════════════════════════════════════════════════════════════════
class Actor:
    def __init__(self, o, S, G2):
        self.o, self.S, self.G2 = o, S, G2
        self.C21 = S.C21
        self.n = o.username
        self.profile_v = L.profile_of(self.n)
        self.browser = L.browser_di(self.n)
        self.chi = L.tenant_of(self.n)
        self.password = "c16-" + secrets.token_hex(8)
        self.internal_port = L.internal_port(o.container_box, self.n)
        self.rate = Rate(o.seed, self.n)
        self.folder = os.path.join(o.dir, "username-%02d" % self.n)
        os.makedirs(self.folder, exist_ok=True)
        self.f_state = open(os.path.join(self.folder, "stato.jsonl"), "a", buffering=1)
        self.f_events = open(os.path.join(self.folder, "eventi.jsonl"), "a", buffering=1)
        self.events_window = []
        self.errors_window = []
        self.round_echo_window = []
        self.pulses = []
        self.pending_pulses = []       # (estimated time, gesture): the page tells the true time
        self.painted_t = []
        self.entered = False
        self.muted = 0
        self.s = self.sc = self.g = None
        self.geo = None
        self.desktop = (o.largo, o.alto)
        self.hands = None
        self.work = None
        self.want_photo = False
        self.n_stopped = False
        self.next_state = 0.0
        self.acts = {}
        self.done_window = 0
        self.checks = {"ok": 0, "ko": 0}
        self.ver_window = []
        self.reg_da = 0
        self.prev = None                   # (time, counters, diary) of the previous row
        self.photo_size = None

    # -- the rows --------------------------------------------------------------
    #  stato.jsonl: ONLY the state rows (every 5 s), in the schema that
    #  16-classifica.py reads; the events go into eventi.jsonl AND into the next state
    #  row (field `events`), so they are not lost and do not dirty the windows.
    def _head(self, event):
        return {"t": round(time.time(), 3), "username": self.n, "profile_v": self.profile_v,
                "browser": self.browser, "version_v": getattr(self, "outcomes", None)
                and self.outcomes.version_v, "tenant": self.chi, "event": event}

    def row(self, event, **fields):
        r = self._head(event)
        r.pop("event")
        r.update(fields)
        self.f_state.write(json.dumps(r, ensure_ascii=False) + "\n")

    def event(self, kind, **fields):
        r = self._head(kind)
        r.update(fields)
        self.f_events.write(json.dumps(r, ensure_ascii=False) + "\n")
        self.events_window.append(r)
        print("   [%02d %s] %s %s" % (self.n, self.profile_v, kind,
                                    json.dumps(fields, ensure_ascii=False)[:240]), flush=True)

    def tally(self, action):
        self.acts[action] = self.acts.get(action, 0) + 1
        self.done_window += 1

    def verify(self, action, ok, lat_ms, det=""):
        self.tally(action)
        self.checks["ok" if ok else "ko"] += 1
        v = {"action": action, "ok": bool(ok),
             "latenza_ms": None if lat_ms is None else round(lat_ms), "det": det}
        self.ver_window.append(v)
        if not ok:
            print("   [%02d %s] ⚠ input NOT verified: %s" % (self.n, self.profile_v, v), flush=True)

    def pulse(self, t, gesture=None):
        """An input that MUST change the image (a typed character, an Enter
        in the terminal, a click on a link, a notch that scrolls).
        `gesture` (kind, key): ("k", character), ("p", "") click, ("w", "") notch;
        with it the page decides the time (`align_pulses`), `t` is the estimate."""
        self.pending_pulses.append((t, gesture))

    # -- the heart: signals, photos, state ------------------------------------
    def heart(self):
        """⭐ The SAFE point: here (and only here) the SIGTERM becomes `Fine`.
        ⛔ `[M]` 25 Sep 2026: interrupted in the middle of a call, Marionette
        was left with the pending answer and the next call read that one —
        the page's log on exit was no longer saved."""
        if self.n_stopped:
            raise Fine("signal")
        if self.want_photo:
            self.want_photo = False
            self.fires()
        if time.time() >= self.next_state:
            self.is_late = time.time() - self.next_state if self.next_state else 0.0
            self.write_state()
            # ⚠ the next one in 5 s FROM NOW, not on the grid: after a late
            #   row, a second one 0.7 s apart would be for the
            #   classifier «5 s without frames» (`[M]` 25 Sep, user D)
            self.next_state = time.time() + 5.0

    def sleeps(self, seconds):
        fine = time.time() + max(0.0, seconds)
        while True:
            self.heart()
            rest = fine - time.time()
            if rest <= 0:
                return
            time.sleep(min(0.25, rest))

    def arm_probe(self):
        """The paint probe in the page (every 10 ms: the time of every change)."""
        try:
            with self.G2.ceiling(20, "the probe"):
                self.g.js(self.S.REAL._inject(PAINT_PROBE))
            return True
        except Exception as e:                   # noqa: BLE001
            self.event("failure", body_text="paint probe not armed: %s" % str(e)[:200])
            return False

    def write_state(self):
        if self.g is None:
            return
        try:
            with self.G2.ceiling(20, "the diary"):
                p = self.g.js(JS_DIARY, self.reg_da) or {}
        except Exception as e:                   # noqa: BLE001
            p = {"failure": str(e)[:200]}
        now = time.time()
        line_d = p.get("row")
        diary = read_diary_line(line_d)
        counts = counts_ranking(p.get("counts"), diary)
        errors = []
        if p.get("failure"):
            errors.append("the page does not answer the bench: " + p["failure"])
            self.muted += 1
        else:
            self.muted = 0
        # ⭐ the drop: after entry the page is no longer in session
        drop = bool(self.entered and not p.get("failure") and not p.get("session_v"))
        if drop:
            errors.append("the page is no longer in session (screen %s, outcome «%s»)"
                          % (p.get("display_screen"), p.get("outcome")))
        # ⭐ the longest freeze: from the paint times and the impulses
        pt = [x / 1000.0 for x in (p.get("painted_t") or [])]
        self.painted_t = [x for x in self.painted_t if x > now - 30] + pt
        # ⭐ the impulses at the time the PAGE received the gesture
        aligned_pulses = align_pulses(self.pending_pulses, p.get("gesti_t"))
        from_page = sum(1 for a, (st, _g) in zip(aligned_pulses, self.pending_pulses) if a != st)
        total_pulses = len(self.pending_pulses)
        self.pulses += aligned_pulses
        self.pending_pulses = []
        block, work = None, False
        if self.profile_v == "D":
            if self.video_in_progress():
                block = longest_pause(self.painted_t, self.prev[0] if self.prev else now - 5, now)
                work = True
        else:
            waits, self.pulses = pulse_waits(self.pulses, self.painted_t, now)
            if waits:
                block, work = max(waits), True
        fields = {"counts": counts, "diary": line_d, "diario_letto": diary,
                 "lap": p.get("lap"), "giro_eco": self.round_echo_window,
                 "input": self.ver_window,
                 "blocco_max_ms": None if block is None else round(block * 1000),
                 "work": work, "impulsi_pagina": [from_page, total_pulses],
                 "drop": drop, "errors": errors + self.errors_window,
                 "session_v": p.get("session_v"), "display_screen": p.get("display_screen"),
                 "focus": p.get("focus"), "is_visible": p.get("is_visible")}
        if self.prev:
            dt = now - self.prev[0]
            dc, az = differences(self.prev[1], counts, COUNTS_DELTA)
            fields["delta"] = dict(dc, s=round(dt, 2))
            if dc.get("painted") is not None and dt > 0:
                fields["dipinti_s"] = round(dc["painted"] / dt, 2)
            if az:
                fields["zeroed"] = az
        self.prev = (now, counts)
        if p.get("new_ones"):
            fields["pagina"] = p["new_ones"]
        if isinstance(p.get("lung"), int):
            self.reg_da = p["lung"]
        # ⚠ how late this row arrived (a long gesture holds it back)
        fields["in_ritardo_s"] = round(getattr(self, "is_late", 0.0), 2)
        fields.update({"acts": dict(self.acts), "azioni_finestra": self.done_window,
                      "checks": dict(self.checks)})
        if self.work is not None:
            try:
                fields["dettagli_lavoro"] = self.work.extra()
            except Exception as e:               # noqa: BLE001
                fields["dettagli_lavoro"] = {"failure": str(e)[:200]}
        if self.events_window:
            fields["events"] = self.events_window
        self.done_window = 0
        self.ver_window = []
        self.errors_window = []
        self.events_window = []
        self.round_echo_window = []
        self.row("state", **fields)

    def video_in_progress(self):
        v = getattr(self.work, "last_video", None) or {}
        return self.entered and v.get("state") == 1

    # -- the photos -------------------------------------------------------------
    def png(self):
        self.G2.front(self.g)
        with self.G2.ceiling(30, "the photo"):
            return self.C21.full_photo(self.g)

    def fires(self):
        t = time.time()
        try:
            png = self.png()
        except Exception as e:                   # noqa: BLE001
            self.event("picture", ok=False, reason_text=str(e)[:200])
            return
        if not png:
            self.event("picture", ok=False, reason_text="the canvas cannot be photographed")
            return
        f = os.path.join(self.folder, "picture-%d.png" % int(t * 1000))
        with open(f, "wb") as h:
            h.write(png)
        self.event("picture", ok=True, file=f, ms=round((time.time() - t) * 1000))

    def photo_pil(self):
        from PIL import Image
        try:
            png = self.png()
        except Exception:                        # noqa: BLE001
            return None
        if not png:
            return None
        im = Image.open(io.BytesIO(png)).convert("RGB")
        self.photo_size = im.size
        return im

    def photo_to_desktop(self, r):
        if not r or not self.photo_size or not self.geo:
            return None
        pw, ph = self.photo_size
        x0, y0 = self.C21.from_photo_to_desktop(self.geo, pw, ph, r[0], r[1])
        x1, y1 = self.C21.from_photo_to_desktop(self.geo, pw, ph, r[2], r[3])
        tl, ta = self.desktop
        return (max(0, x0), max(0, y0), min(tl, x1), min(ta, y1))

    def internal_preferences(self):
        return self.C21.PREFERENCES

    # -- the access ------------------------------------------------------------
    def enter(self):
        s, REAL = self.s, self.S.REAL
        n = {"tenant": self.chi, "browser": self.browser, "version_v": self.outcomes.version_v,
             "container_box": self.o.container_box, "gauge": [self.o.largo, self.o.alto]}
        ok, m = s.pr.open_it()
        if not ok:
            n.update(outcome="pagina_non_aperta", motivo="the page does not open: " + m)
            return n
        t0 = time.time()
        r = s.g.js(REAL.JS_ENTER, self.chi, self.password)
        if r != "mandato":
            n.update(outcome="modulo_non_compilato", motivo="the form cannot be filled in: %s" % r)
            return n
        admitted = first = None
        st = {}
        while time.time() < t0 + self.o.cap_s:
            st = s.pr.state()
            now = time.time()
            # ⚠ both forms of the page's outcome: the old (Italian) page of the running
            #   campaign and the new (English) one
            if admitted is None and st.get("sessione") and st.get("esito_classe") == "bene" \
                    and (st.get("esito") or "").startswith(("Ammesso", "Admitted")):
                admitted = now
            if st.get("esito_classe") == "male" and st.get("outcome"):
                n.update(outcome="refusal", motivo="refusal: «%s»" % st["outcome"],
                         access_ms=round(t0 * 1000))
                return n
            if (st.get("painted") or 0) > 0:
                first = now
                admitted = admitted or now
                break
            if self.n_stopped:
                raise Fine("signal")
            time.sleep(0.1)
        # ⭐ in the schema of 16-classifica: times in ms from the epoch, and the duration separately
        n["access_ms"] = round(t0 * 1000)
        n["ammesso_ms"] = round(admitted * 1000) if admitted else None
        n["primo_fotogramma_ms"] = round(first * 1000) if first else None
        n["nascita_ms"] = round((first - t0) * 1000) if first else None
        n["ammissione_ms"] = round((admitted - t0) * 1000) if admitted else None
        if not first:
            n.update(outcome="nessun_fotogramma", motivo="no frame in %d s (outcome «%s»)"
                     % (self.o.cap_s, st.get("outcome")))
            return n
        # ⚠ the «not degenerate» judgement photographs up to the cap: `[M]` 25 Sep,
        #   xfce has a BLACK background and waited 60 s for it ⇒ short cap, and the
        #   dark but alive desktop is recognised by `desktop_dark_but_alive`.
        # ⛔ The cap is the FAIL threshold of §9: «degenere» only if it STILL is at
        #   15 s from ACCESS (not 8 s from the first frame: under load the
        #   Plasma splash lasts longer, and it is not a broken desktop).  If the
        #   first frame arrives already beyond, one last look of 3 s.
        ceiling, self.o.cap_s = self.o.cap_s, max(3, int(math.ceil(
            t0 + CAP_DEGENERATE_S - time.time())))
        try:
            e, m, st2 = s.pr.first_frame()
        finally:
            self.o.cap_s = ceiling
        e, m = self.S.C20V.desktop_dark_but_alive(e, m, st2)
        n["desktop_vivo_ms"] = round((time.time() - t0) * 1000)
        n["outcome"], remark = outcome_birth(e == self.S.GREEN, e == self.S.RED)
        if remark:
            n["remark"] = remark
        n["motivo"] = m
        return n

    # -- everything -------------------------------------------------------------
    def run_loop(self):
        o, S = self.o, self.S
        self.outcomes = S.Outcomes(o)
        S.TENANT_PATTERN = re.compile(r"^c16[0-9]{3}u[0-9]+$")
        self.s = S.Session(o, "%03d" % self.n, self.outcomes, chi=self.chi, password=self.password)
        self.sc = self.s.sc
        self.event("start", tenant=self.chi, container_box=o.container_box, wayland=o.wayland,
                    base_ports=o.base_ports, seed=o.seed, internal_port=self.internal_port,
                    gauge=[o.largo, o.alto], video=o.video or None, pid=os.getpid())
        code_v = 2
        try:
            self.s.__enter__()                   # creates the tenant, turns on the browser
            self.g = self.s.g
            self.work = L.JOBS[self.profile_v](self)
            self.work.prepare()
            birth = self.enter()
            with open(os.path.join(self.folder, "nascita.json"), "w") as f:
                json.dump(birth, f, ensure_ascii=False, indent=1)
            self.event("birth", **birth)
            if not works_after_birth(birth):
                code_v = 1
                self.wait_end("access failed")
                return code_v
            # ⭐ a «degenerate» or unchecked desktop does have the frames: the
            #   session is there and the actor WORKS — the load is not removed (the
            #   birth is judged by the classification, from nascita.json)
            self.entered = True
            self.arm_probe()
            self.geo = self.s.geometry()
            self.desktop = (self.geo["tl"], self.geo["ta"])
            self.hands = Hands(self)
            print("   [%02d] wake-up: %s" % (self.n, self.C21.wake(self.g, self.geo)), flush=True)
            # ⭐ THE WELCOME CLICK, on an empty spot of the desktop, before any
            #   application: it is the user gesture that wakes up the page's
            #   audio.  ⛔ `[M]` 25 Sep, user D without it: 6090 blocks received,
            #   0 played, `ctx suspended` (the access is a form filled in by the
            #   bench, not a gesture; the wake-up's ESC does not activate).
            self.sleeps(1.0)
            self.hands.click(self.desktop[0] * 0.55, self.desktop[1] * 0.55)
            self.sleeps(1.0)
            code_v = 0
            for prova in range(3):
                ok, m = self.work.start()
                self.event("application", ok=ok, body_text=m, attempt=prova + 1)
                if ok:
                    break
                self.sleeps(10)
            else:
                code_v = 1
                self.wait_end("the application does not start")
                return code_v
            errors = 0
            while True:
                try:
                    t_step = time.time()
                    self.work.step()
                    if time.time() - t_step > 45 and self.profile_v != "D":
                        print("   [%02d] ⚠ a step of %.0f s" % (self.n, time.time() - t_step),
                              flush=True)
                    errors = 0
                except Fine:
                    raise
                except Exception as e:           # noqa: BLE001
                    errors += 1
                    self.errors_window.append("%r" % e)
                    self.event("failure", body_text="%r" % e, dove=traceback.format_exc()[-600:],
                                in_a_row=errors)
                    self.sleeps(min(30, 2 * errors))
        except Fine:
            pass
        except Exception as e:                   # noqa: BLE001
            self.event("failure", body_text="%r" % e, dove=traceback.format_exc()[-800:], fatal=True)
            code_v = 2
        finally:
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            self.shut()
        return code_v

    def wait_end(self, reason_text):
        """⚠ A user that did not manage to enter stays available
        (state, photo) until the orchestrator stops it: it does not disappear."""
        self.event("waiting", reason_text=reason_text)
        while True:
            self.sleeps(5)

    def shut(self):
        try:
            if self.g is not None:
                try:
                    self.write_state()
                except Exception:                # noqa: BLE001
                    pass
                try:
                    with self.G2.ceiling(20, "the page's log"):
                        reg = self.g.js("const r=document.getElementById('logbook');"
                                        "return r ? r.textContent : '';") or ""
                    with open(os.path.join(self.folder, "registro-pagina.txt"), "w") as f:
                        f.write(reg)
                except Exception:                # noqa: BLE001
                    pass
                try:
                    self.s.save_console()
                except Exception:                # noqa: BLE001
                    pass
        finally:
            try:
                self.s.__exit__(None, None, None)     # closes the browser and CLEARS
            except Exception as e:               # noqa: BLE001
                print("   ⚠ exit: %s" % e, flush=True)
            _c, t = self.sc.inside("id %s >/dev/null 2>&1 && echo RESTA || echo via" % self.chi, 30)
            self.event("fine", cleared=(t or "").strip().endswith("via"), acts=self.acts,
                        checks=self.checks)
            self.f_state.close()
            self.f_events.close()


# ═══════════════════════════════════════════════════════════════════════════
#  THE HANDS — REAL input from the browser, coordinates of the remote DESKTOP
# ═══════════════════════════════════════════════════════════════════════════
class Hands:
    def __init__(self, expect):
        self.a = expect
        self.G2 = expect.G2
        self.pos = None

    @property
    def g(self):
        return self.a.g

    def glass(self, X, Y):
        tl, ta = self.a.desktop
        X, Y = max(1, min(tl - 2, X)), max(1, min(ta - 2, Y))
        return self.a.C21.desktop_to_glass(self.a.geo, X, Y)

    def _path(self, X, Y):
        """The pointer gets there in steps, not all at once."""
        vx, vy = self.glass(X, Y)
        R = self.a.rate
        steps = []
        if self.pos:
            n = R.whole(3, 8)
            for i in range(1, n):
                f = i / float(n)
                steps += [("move_to", self.pos[0] + (vx - self.pos[0]) * f,
                           self.pos[1] + (vy - self.pos[1]) * f), ("pause_v", R.whole(12, 30))]
        steps += [("move_to", vx, vy), ("pause_v", R.whole(60, 180))]
        self.pos = (vx, vy)
        return steps

    def move_to(self, X, Y):
        self.G2.mouse(self.g, self._path(X, Y))
        return time.time()

    # ⭐ Every gesture returns the time of the decisive event (the press, the first
    #   notch, the key), derived from the RETURN of the call to the browser minus the
    #   pauses scheduled AFTER it.  ⛔ `[M]` 25 Sep: the time after the
    #   call, without removing the pauses, put the bash history 200 ms
    #   «before» the Enter; ⛔ review 25 Sep: the time BEFORE the call
    #   put Marionette/CDP's delay under load (and the bringToFront)
    #   in the product's «freeze».
    def _wd(self, acts):
        """Marionette: PerformActions ⇒ the time of its RETURN (before the
        ReleaseActions, which has nothing to do with the gesture)."""
        self.g.m.call("WebDriver:PerformActions", {"actions": acts})
        t = time.time()
        self.g.m.call("WebDriver:ReleaseActions")
        return t

    def click(self, X, Y, button_code=0, expected_val=False):
        R = self.a.rate
        self.G2.mouse(self.g, self._path(X, Y))
        pause_v = R.whole(50, 120)
        if hasattr(self.g, "cdp"):
            self.G2.mouse(self.g, [("move_to",) + tuple(self.pos), ("down", button_code, 1),
                                   ("pause_v", pause_v), ("su", button_code, 1)])
            t = time.time() - pause_v / 1000.0
        else:
            x, y = int(round(self.pos[0])), int(round(self.pos[1]))
            t = self._wd([{"type": "pointer", "id": "topo", "parameters": {"pointerType": "mouse"},
                           "actions": [{"type": "pointerMove", "x": x, "y": y, "origin": "viewport",
                                        "duration": 0},
                                       {"type": "pointerDown", "button": button_code},
                                       {"type": "pause", "duration": pause_v},
                                       {"type": "pointerUp", "button": button_code}]}])
            t -= pause_v / 1000.0
        if expected_val:
            self.a.pulse(t, ("p", ""))
        self.a.tally("clic_mouse")
        return t

    def scroll_wheel(self, X, Y, ticks, expected_val=False):
        """`ticks` > 0 down, < 0 up; one notch = 120 (a real wheel)."""
        self.move_to(X, Y)
        vx, vy = self.pos
        R = self.a.rate
        dy = 120 if ticks > 0 else -120
        t = None
        if hasattr(self.g, "cdp"):
            self.G2.front(self.g)
            with self.G2.ceiling(60, "the wheel"):
                for _ in range(abs(ticks)):
                    self.g.cdp.call("Input.dispatchMouseEvent", type="mouseWheel", x=vx, y=vy,
                                      deltaX=0, deltaY=dy)
                    t = t or time.time()             # the first notch, at the return
                    time.sleep(R.whole(40, 160) / 1000.0)
        else:
            az, pause = [], 0
            for _ in range(abs(ticks)):
                p = R.whole(40, 160)
                pause += p
                az += [{"type": "scroll", "x": int(vx), "y": int(vy), "deltaX": 0, "deltaY": dy,
                        "origin": "viewport", "duration": 0},
                       {"type": "pause", "duration": p}]
            t = self._wd([{"type": "wheel", "id": "scroll_wheel", "actions": az}]) - pause / 1000.0
        t = t or time.time()
        if expected_val:
            self.a.pulse(t, ("w", ""))
        self.a.tally("ticks")
        return t

    def press(self, label_name, expected_val=False):
        """One key: down, pause, up, pause (like `G2.keys`)."""
        P = self.G2.PAUSE_MS
        v = self.G2.SPECIAL[label_name][3] if label_name in self.G2.SPECIAL else label_name
        if hasattr(self.g, "cdp") or v is None:
            self.G2.keys(self.g, self.G2.press(label_name))
            t = time.time() - 2 * P / 1000.0
        else:
            t = self._wd([{"type": "key", "id": "keyboard", "actions": [
                {"type": "keyDown", "value": v}, {"type": "pause", "duration": P},
                {"type": "keyUp", "value": v}, {"type": "pause", "duration": P}]}]) - 2 * P / 1000.0
        if expected_val:
            self.a.pulse(t, ("k", ""))
        return t

    def combo(self, mod, key):
        steps = self.G2.press(key)
        for m in reversed(mod):
            steps = self.G2.clr(m, steps)
        t = time.time()
        self.G2.keys(self.g, steps)
        return t

    def lap(self):
        try:
            with self.G2.ceiling(15, "the round"):
                return self.g.js(JS_ROUND)
        except Exception:                        # noqa: BLE001
            return None

    def beat(self, body_text, expected_val=True, echo=False):
        """Every character a real key, with the person's rhythm.  `expected_val`: every
        character must appear (echo) ⇒ it is an impulse for the freeze.  `echo`:
        the character appears AT ONCE (terminal, text field) ⇒ the round samples
        arrived during the typing go into `giro_eco`."""
        g_before = self.lap() if echo else None
        self._beat(body_text, expected_val)
        fine = time.time()
        if echo:
            time.sleep(0.4)                      # the echo of the last characters
            self.a.round_echo_window += new_samples(g_before, self.lap())
        return fine

    def _beat(self, body_text, expected_val):
        R = self.a.rate
        times = [(R.hold_ms(), R.keystroke_ms()) for _ in body_text]
        # ⚠ in pieces of ~1.5 s, with the heart in between: a long line typed in a
        #   single chain held back the state row up to 10 s (`[M]` 25 Sep)
        pieces, piece, dur = [], [], 0.0
        for c, tb in zip(body_text, times):
            piece.append((c, tb))
            dur += max(tb) / 1000.0
            if dur >= 1.5:
                pieces.append(piece)
                piece, dur = [], 0.0
        if piece:
            pieces.append(piece)
        for i, pz in enumerate(pieces):
            if i:
                self.a.heart()
            if hasattr(self.g, "cdp"):
                self.G2.front(self.g)
                with self.G2.ceiling(30, "the typing"):
                    for c, (ten, bat) in pz:
                        cd, vk = self.G2.code_of(c)
                        self.g.cdp.call("Input.dispatchKeyEvent", type="keyDown", key=c, code=cd,
                                          windowsVirtualKeyCode=vk, text=c, unmodifiedText=c)
                        if expected_val:
                            self.a.pulse(time.time(), ("k", c))     # estimate: at the RETURN of the keyDown
                        time.sleep(ten / 1000.0)
                        self.g.cdp.call("Input.dispatchKeyEvent", type="keyUp", key=c, code=cd,
                                          windowsVirtualKeyCode=vk)
                        time.sleep(max(0.0, bat - ten) / 1000.0)
            else:
                az, durations = [], []
                for c, (ten, bat) in pz:
                    az += [{"type": "keyDown", "value": c}, {"type": "pause", "duration": int(ten)},
                           {"type": "keyUp", "value": c},
                           {"type": "pause", "duration": int(max(0, bat - ten))}]
                    durations.append(int(ten) + int(max(0, bat - ten)))
                # ⭐ the time of every key from the RETURN of the chain (key_times), not
                #   scheduled from the departure: Marionette's delay is not a freeze
                t_ret = self._wd([{"type": "key", "id": "keyboard", "actions": az}])
                if expected_val:
                    for k, (c, _tb) in zip(key_times(t_ret, durations), pz):
                        self.a.pulse(k, ("k", c))
        self.a.tally("keys")
        return time.time()


# ═══════════════════════════════════════════════════════════════════════════
def main():
    o = call_args()
    if o.certify:
        return certify()
    environment(o)
    sys.path.insert(0, SUITE)
    import suite as S                                                 # noqa: E402
    G2 = S._load("g2scena", os.path.join(SUITE, "15-g2-scena.py"))
    # ⭐ the keys the jobs need and that G2's table lacks
    G2.SPECIAL.setdefault("Delete", ("Delete", "Delete", 46, "", 0))
    G2.SPECIAL.setdefault("Home", ("Home", "Home", 36, "", 0))
    G2.SPECIAL.setdefault("PageDown", ("PageDown", "PageDown", 34, "", 0))
    G2.SPECIAL.setdefault("PageUp", ("PageUp", "PageUp", 33, "", 0))
    # the fields that `Session` and the guides of 12-client-veri expect
    o.browser = L.browser_di(o.username)
    o.fault = False
    o.is_visible = True
    o.port = 0
    o.evidence = os.path.join(o.dir, "username-%02d" % o.username)
    o.url = "https://%s:%d/" % (o.host, S.PORTS[o.container_box])
    # ⭐ to measure a route of the page (e.g. «?tela=gl», anomaly A1): it is appended
    #   to the address, and declared in the state; empty = the default page
    if os.environ.get("REMOTIX_16_URL_EXTRA"):
        o.url += os.environ["REMOTIX_16_URL_EXTRA"]
    o.scene, o.continuity_s, o.log_cmd, o.leave_on, o.store = "viva", 8, "", False, ""
    expect = Actor(o, S, G2)

    def _fine(_n, _f):
        expect.n_stopped = True

    def _photo(_n, _f):
        expect.want_photo = True
    signal.signal(signal.SIGTERM, _fine)
    signal.signal(signal.SIGINT, _fine)
    signal.signal(signal.SIGUSR1, _photo)
    print("⭐ actor %02d · %s · profile %s · %s · %s · %s" % (
        o.username, o.container_box, expect.profile_v, o.browser, o.wayland, expect.chi), flush=True)
    return expect.run_loop()


if __name__ == "__main__":
    sys.exit(main())
