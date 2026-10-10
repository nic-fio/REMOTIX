#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-d006 — THE CLEAN MEASUREMENT OF D-006: the audio gaps counted by the PAGE, without an ear

    python3 15-d006-misura.py --container_box lxqt --browser firefox --which f013 [--video-worker]
                              [--window-s 60] [--fault] [--evidence DIR]
    python3 15-d006-misura.py --certify

WHY IT EXISTS.  D-006 (Firefox + video: sound gaps) was seen ONLY with
the «ear» of `15-g4-comune.py`, which replaces `AudioContext` and
`AudioNode.prototype.connect`, puts an `AnalyserNode` (FFT 8192) in the path
and reads it every 100 ms from the main thread.  The user says that in real use
the audio has never given problems ⇒ before curing the product we measure WITHOUT
touching anything of the page.

THE MEASUREMENT.  No ear, no replaced nodes, no injected timers.
  We read the counts the page keeps BY ITSELF (`audio_counts()`, two readings:
  start and end of the window, one line of script each) and take their
  differences:
    · rearms   ⭐ the metric: every re-arm is a gap of AT LEAST 250 ms (the cushion
               starts over, `plays()` in src/pagina.html);
    · pulled, cut, discarded_full, discarded_late, missed: alongside;
    · udibile_stima = Δexited × 20 ms / duration.  ⚠ LOWER BOUND on Firefox:
      `cut`/`exited` are judged with `currentTime`, which is stale there, and
      a block that finished by itself can count as cut.
  And the SERVER's CPU in the same window (`/proc/stat` every second, all the
  cpus: mean, p95, the busiest core), and — if the bench runs on the server — the
  hungriest processes at mid window.  It is the datum for hypothesis (b): CPU
  contention between the browser and the session doing video.

THE COMBINATIONS (one at a time: each one is a launch):
    --which f012   the tone of F-012 (pw-play, 440 Hz), NO video
    --which f013   the video of F-013 (ffplay 1280x720, 660 Hz), WITHOUT photos
    --video-worker the page with `#video=worker`: decoding and drawing of the video
                   in the worker (switch already in the product, off by default).
                   The bench VERIFIES inside the page that the worker is on.

JUDGMENT (for the suite register; it is a measurement, the table counts more):
    PASS  Δrearms = 0 and Δdiscarded_full = 0 in the window
    FAIL  at least one re-arm (= at least one 250 ms gap)
    BLOCKED  audio context never «running», worker requested and not on, etc.

FAULT (--fault, same session): the PAGE's main thread is stopped
  for 400 ms every 2 s (an injected busy loop: more than the cushion) for 20 s
  ⇒ the same measurement must count re-arms (>= 3).  If it does not count them, the measurement is
  blind and the healthy one is worth nothing.

OUTPUT: besides the SUITE lines, a line `MEASURE {...}` with all the numbers
(box, browser, scene, worker, delta, cpu), to be pasted into the table.
"""
import importlib.util as _iu
import json
import os
import subprocess
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import suite as S                                                     # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def _module(label_name, file):
    s = _iu.spec_from_file_location(label_name, os.path.join(HERE, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


G4 = _module("g4", "15-g4-comune.py")
F12 = _module("f012", "15-f012-audio.py")
F13 = _module("f013", "15-f013-video.py")

FUNCTIONS = ("D-006",)
BLOCK_S = 0.020           # one audio block = 20 ms (RCP §6.3)
CUSHION_S = 0.250          # AUDIO_CUSHION_MS: the minimum gap of a re-arm
COUNTS = ("received_n", "played", "rearms", "pulled", "cut", "exited", "pending",
         "discarded_full", "discarded_late", "discarded_old", "missed", "sound_jumps")
FAULT_S = 20.0


def extra(a):
    a.add_argument("--which", choices=("f012", "f013"), default="f013",
                   help="the scene: f012 tone without video, f013 video (⚠ not `--scene`: suite.py rewrites it)")
    a.add_argument("--video-worker", action="store_true")
    a.add_argument("--pcm", action="store_true",
                   help="audio in PCM instead of Opus: the bench makes the page say that the engine "
                        "does not decode Opus (no AudioDecoder in the audio path)")
    a.add_argument("--nnn", default="906",
                   help="the three digits of the tenant c15<nnn>u<n> (agents in parallel: different)")
    a.add_argument("--window-s", type=float, default=60.0)
    a.add_argument("--settle-s", type=float, default=5.0,
                   help="wait after the wake-up, before the window")


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def delta(c0, c1, ms0, ms1, block_s=BLOCK_S):
    """The counts of the window: differences + estimates.  `ms` = performance.now().
    ⚠ `block_s`: 20 ms for Opus, 5 ms for PCM (`[M]` 200 blocks/s)."""
    d = {k: (c1.get(k) or 0) - (c0.get(k) or 0) for k in COUNTS}
    duration = max(1e-3, (ms1 - ms0) / 1000.0)
    d["duration_s"] = round(duration, 1)
    d["udibile_stima_pct"] = round(min(100.0, 100.0 * d["exited"] * block_s / duration), 1)
    d["silenzio_minimo_s"] = round(d["rearms"] * CUSHION_S, 2)
    d["context"] = c1.get("context")
    d["orologio_stantio_ms"] = c1.get("orologio_stantio_ms")   # only if the page carries it
    return d


def cpu_da_stat(line_list):
    """From the readings of `grep ^cpu /proc/stat` (blocks separated by '---'):
    {mean, p95, max} of the total and the busiest core (mean), in %."""
    blocks, cur = [], {}
    for r in line_list:
        r = r.strip()
        if r == "---":
            if cur:
                blocks.append(cur)
            cur = {}
            continue
        p = r.split()
        if not p or not p[0].startswith("cpu"):
            continue
        v = [int(x) for x in p[1:]]
        idle = v[3] + (v[4] if len(v) > 4 else 0)
        cur[p[0]] = (sum(v[:8]), idle)
    if cur:
        blocks.append(cur)
    if len(blocks) < 2:
        return None
    tot, core = [], {}
    for a, b in zip(blocks, blocks[1:]):
        for label_name in b:
            if label_name not in a:
                continue
            dt = b[label_name][0] - a[label_name][0]
            di = b[label_name][1] - a[label_name][1]
            if dt <= 0:
                continue
            busy = 100.0 * (dt - di) / dt
            if label_name == "cpu":
                tot.append(busy)
            else:
                core.setdefault(label_name, []).append(busy)
    if not tot:
        return None
    s = sorted(tot)
    means = {k: sum(v) / len(v) for k, v in core.items() if v}
    hot = max(means.items(), key=lambda kv: kv[1]) if means else (None, None)
    return {"samples": len(tot), "media": round(sum(tot) / len(tot), 1),
            "p95": round(s[min(len(s) - 1, int(0.95 * len(s)))], 1), "max": round(s[-1], 1),
            "core_piu_carico": hot[0], "core_piu_carico_media": round(hot[1] or 0, 1),
            "core": len(means)}


def judge(d):
    if d.get("context") != "running":
        return "BLOCKED", "the audio context is not «running» at the end of the window (%s)" % d.get("context")
    if d["received_n"] <= 0:
        return "BLOCKED", "no audio block received in the window"
    if d["rearms"] == 0 and d["discarded_full"] == 0:
        return "PASS", ("no gap: re-arms 0 in %.0f s (pulled %d, cut %d, estimated audible "
                        ">= %.1f%%)" % (d["duration_s"], d["pulled"], d["cut"],
                                        d["udibile_stima_pct"]))
    return "FAIL", ("%d re-arms in %.0f s = at least %.2f s of silence (pulled %d, cut %d, "
                    "full %d, estimated audible >= %.1f%%)"
                    % (d["rearms"], d["duration_s"], d["silenzio_minimo_s"], d["pulled"],
                       d["cut"], d["discarded_full"], d["udibile_stima_pct"]))


def certify():
    ok = True

    def chk(label_name, cond):
        nonlocal ok
        print("   %s %s" % ("⭐" if cond else "⛔", label_name))
        ok = ok and cond
    c0 = {k: 0 for k in COUNTS}
    c0.update(received_n=100, played=90, exited=80, context="running")
    healthy = dict(c0, received_n=3100, played=3090, exited=3080, context="running")
    d = delta(c0, healthy, 1000.0, 61000.0)
    e, _ = judge(d)
    chk("healthy: 60 s, 3000 blocks out, 0 re-arms ⇒ PASS, audible 100%", e == "PASS"
        and d["udibile_stima_pct"] == 100.0 and d["duration_s"] == 60.0)
    broken = dict(healthy, rearms=7, pulled=90, cut=200, exited=2700)
    d = delta(c0, broken, 1000.0, 61000.0)
    e, r = judge(d)
    chk("7 re-arms ⇒ FAIL, minimum silence 1.75 s (%s)" % r, e == "FAIL"
        and d["silenzio_minimo_s"] == 1.75)
    full = dict(healthy, discarded_full=1)
    chk("an overflow without re-arms ⇒ FAIL", judge(delta(c0, full, 0, 60000))[0] == "FAIL")
    mute = dict(healthy, context="suspended")
    chk("context suspended ⇒ BLOCKED", judge(delta(c0, mute, 0, 60000))[0] == "BLOCKED")
    blank = dict(c0)
    chk("no block ⇒ BLOCKED", judge(delta(c0, blank, 0, 60000))[0] == "BLOCKED")
    # the CPU: two cores, three readings 1 s apart; cpu0 at 100 %, cpu1 at 0 %
    st = ["cpu  0 0 0 0 0 0 0 0", "cpu0 0 0 0 0 0 0 0 0", "cpu1 0 0 0 0 0 0 0 0", "---",
          "cpu  100 0 0 100 0 0 0 0", "cpu0 100 0 0 0 0 0 0 0", "cpu1 0 0 0 100 0 0 0 0", "---",
          "cpu  200 0 0 200 0 0 0 0", "cpu0 200 0 0 0 0 0 0 0", "cpu1 0 0 0 200 0 0 0 0"]
    c = cpu_da_stat(st)
    chk("cpu: mean 50%%, busiest core cpu0 at 100%% (%s)" % c,
        c and c["media"] == 50.0 and c["core_piu_carico"] == "cpu0"
        and c["core_piu_carico_media"] == 100.0 and c["samples"] == 2)
    chk("cpu: a single reading ⇒ no number", cpu_da_stat(st[:3]) is None)
    print("⭐ certified" if ok else "⛔ NOT certified")
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE SERVER'S CPU, during the window
# ═══════════════════════════════════════════════════════════════════════════
ON_SERVER = os.environ.get("REMOTIX_ON_SERVER") == "1"


class Cpu:
    """`grep ^cpu /proc/stat` every second.  ⭐ On the server it is read LOCALLY (the
    browser runs there); otherwise inside the box, where `/proc/stat` is the
    host's (podman does not isolate it)."""

    def __init__(self, sc, seconds):
        self.sc, self.seconds, self.line_list, self.ps = sc, seconds, [], ""
        self._t = None

    def _local(self):
        fine = time.time() + self.seconds
        meta = time.time() + self.seconds / 2
        while time.time() < fine:
            try:
                with open("/proc/stat") as f:
                    self.line_list += [r for r in f if r.startswith("cpu")] + ["---"]
            except OSError:
                return
            if self.ps == "" and time.time() >= meta:
                try:
                    self.ps = subprocess.run(
                        ["ps", "-eo", "pcpu,rss,comm", "--sort=-pcpu"], capture_output=True,
                        text=True, timeout=10).stdout.splitlines()[:15]
                except Exception as e:           # noqa: BLE001
                    self.ps = ["(ps: %s)" % e]
            time.sleep(1.0)

    def _box(self):
        n = int(self.seconds)
        _c, t = self.sc.inside("for i in $(seq %d); do grep ^cpu /proc/stat; echo ---; sleep 1; "
                               "done" % n, n + 60)
        self.line_list = (t or "").splitlines()

    def turn_on(self):
        self._t = threading.Thread(target=self._local if ON_SERVER else self._box,
                                   daemon=True)
        self._t.start()

    def read_it(self):
        if self._t:
            self._t.join(timeout=90)
        return cpu_da_stat(self.line_list), self.ps


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def page_counts(g):
    return G4.in_page(g, "(function(){ return { now: performance.now(),"
                           " counts: (typeof audio_counts === 'function') ? audio_counts() : null,"
                           " worker: (typeof VW !== 'undefined') && VW !== null }; })()")


def wait_for(g, cond, cap_s):
    fine = time.time() + cap_s
    r = None
    while time.time() < fine:
        r = page_counts(g)
        if r and cond(r):
            return True, r
        time.sleep(0.5)
    return False, r


def win(s, o, seconds):
    block = 0.005 if getattr(o, "pcm", False) else BLOCK_S
    """(delta, cpu, ps) over `seconds`, two readings of `audio_counts()`."""
    cpu = Cpu(s.sc, seconds)
    r0 = page_counts(s.g)
    cpu.turn_on()
    time.sleep(seconds)
    r1 = page_counts(s.g)
    c, ps = cpu.read_it()
    if not r0 or not r1 or not r0.get("counts") or not r1.get("counts"):
        raise S.Blocked("audio_counts() cannot be read from the page (%r / %r)" % (r0, r1))
    return delta(r0["counts"], r1["counts"], r0["now"], r1["now"], block), c, ps, r1


# ⛔ The fault: a busy loop IN THE PAGE, 400 ms every 2 s — the main
#   thread stopped beyond the cushion.  Only the bench puts it, only in the fault.
JS_FAULT = ("window.__c15d006 = setInterval(function(){ const f = performance.now() + 400;"
             " while (performance.now() < f) {} }, 2000);")
JS_FAULT_OFF = "clearInterval(window.__c15d006);"


def body_el(o, E):
    if o.video_worker:
        o.url = o.url.split("#")[0] + "#video=worker"
    sess = S.Session(o, o.nnn, E)
    G4.robust(sess.sc)
    with sess as s:
        ok, m = s.pr.open_it()
        if not ok:
            raise S.Blocked("the page does not open: " + m)
        if o.pcm:
            # ⚠ BENCH ONLY: before login (the negotiation is at connection),
            #   `isConfigSupported` says «no» to Opus ⇒ the page declares «pcm» and the
            #   server sends PCM.  It removes `AudioDecoder` from the audio path.
            #   ⭐ D-006 cure: and also the page's wasm decoder must not
            #   start (WebAssembly.instantiate refuses), or the page declares Opus.
            s.g.js(G4._inject("if (window.AudioDecoder) AudioDecoder.isConfigSupported ="
                               " async function () { return { supported: false }; };"
                               " if (window.WebAssembly) WebAssembly.instantiate ="
                               " function () { return Promise.reject(new Error('bench: PCM')); };"))
        ok, m = s.enter(open_it=False)            # ⭐ WITHOUT ear
        if not ok:
            raise S.Blocked(m)
        r = page_counts(s.g) or {}
        if o.video_worker and not r.get("worker"):
            raise S.Blocked("#video=worker requested but in the page the worker is off (%r)" % r)
        if o.which == "f012":
            ok, m = F12.prepare_tone_ffmpeg(s)
            if not ok:
                raise S.Blocked("the tone does not get ready: " + m)
            c, t = F12.plays(s)
            if c != 0:
                raise S.Blocked("pw-play does not start: " + t[-200:])
            spot = (0.62, 0.55)
        else:
            ok, m = F13.prepare_video(s)
            if not ok:
                raise S.Blocked("the video is not generated: " + m)
            c, t = F13.turn_on_video(s)
            if c != 0:
                raise S.Blocked("ffplay does not start: " + t[-200:])
            spot = (0.97, 0.5)                # right edge: outside the video window
        note = ["scene %s%s%s" % (o.which, " · #video=worker (on)" if o.video_worker else "",
                                  " · PCM" if o.pcm else "")]
        ok, r = wait_for(s.g, lambda x: (x.get("counts") or {}).get("context") not in
                        (None, "(none)"), 30)
        if not ok:
            raise S.Blocked("the page did not create an AudioContext in 30 s (%r)" % r)
        note.append(G4.real_click(s, *spot))
        ok, r = wait_for(s.g, lambda x: (x.get("counts") or {}).get("context") == "running", 10)
        if not ok:
            raise S.Blocked("the audio context does not wake up at the click (%r)" % (r or {}).get("counts"))
        if o.pcm and (r.get("counts") or {}).get("codec") != 2:
            raise S.Blocked("PCM requested but the page receives codec %r"
                             % (r.get("counts") or {}).get("codec"))
        time.sleep(o.settle_s)
        sign = s.log_mark()
        d, cpu, ps, r1 = win(s, o, o.window_s)
        e, rationale = judge(d)
        cf = r1.get("counts") or {}
        #   ⭐ who decodes the Opus (wasm since the D-006 cure, AudioDecoder before)
        note.append("decoder %s (%s/%s us mean/max)" % (
            cf.get("decoder", "(old page: AudioDecoder)"),
            cf.get("avg_dec_us"), cf.get("dec_us_max")))
        gauge = {"container_box": o.container_box, "browser": o.browser, "version_v": E.version_v,
                  "scene": o.which, "worker": bool(o.video_worker), "pcm": bool(o.pcm), "delta": d, "cpu": cpu,
                  "conti_fine": r1.get("counts")}
        print("MEASURE " + json.dumps(gauge, ensure_ascii=False), flush=True)
        ev = [G4.save_json(o, "d006-misura-%s-%s-%s%s.json" % (
            o.container_box, o.browser, o.which, ("-worker" if o.video_worker else "") + ("-pcm" if o.pcm else "")),
            dict(gauge, ps=ps)),
              s.save_text("server-d006.txt", s.log_from(sign) if sign else []),
              s.save_console()]
        E.put("D-006", e, rationale,
                expected_val="re-arms 0 in %.0f s, without ear (page counts)" % o.window_s,
                observed="; ".join(note) + " · cpu %s" % cpu, evidence=[p for p in ev if p],
                numbers=gauge)

        if o.fault:
            s.g.js(G4._inject(JS_FAULT))
            try:
                dg, _c, _p, _r = win(s, o, FAULT_S)
            finally:
                s.g.js(G4._inject(JS_FAULT_OFF))
            seen_v = dg["rearms"] >= 3
            E.fault("D-006", seen_v, "page main thread stopped 400 ms every 2 s for "
                     "%.0f s ⇒ re-arms %d (expected >= 3), pulled %d"
                     % (FAULT_S, dg["rearms"], dg["pulled"]), numbers={"delta": dg})


if __name__ == "__main__":
    sys.exit(S.execute(__doc__, FUNCTIONS, body_el, certify, extra))
