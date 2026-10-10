#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-d006 — THE CLEAN MEASUREMENT OF D-006: the audio gaps counted by the PAGE, without an ear

    python3 15-d006-misura.py --scatola lxqt --browser firefox --quale f013 [--video-worker]
                              [--finestra-s 60] [--guasto] [--evidenze DIR]
    python3 15-d006-misura.py --certifica

WHY IT EXISTS.  D-006 (Firefox + video: sound gaps) was seen ONLY with
the «ear» of `15-g4-comune.py`, which replaces `AudioContext` and
`AudioNode.prototype.connect`, puts an `AnalyserNode` (FFT 8192) in the path
and reads it every 100 ms from the main thread.  The user says that in real use
the audio has never given problems ⇒ before curing the product we measure WITHOUT
touching anything of the page.

THE MEASUREMENT.  No ear, no replaced nodes, no injected timers.
  We read the counts the page keeps BY ITSELF (`audio_conti()`, two readings:
  start and end of the window, one line of script each) and take their
  differences:
    · riarmi   ⭐ the metric: every re-arm is a gap of AT LEAST 250 ms (the cushion
               starts over, `suona()` in src/pagina.html);
    · tirate, tagliati, scartati_pieno, scartati_tardivi, mancati: alongside;
    · udibile_stima = Δusciti × 20 ms / duration.  ⚠ LOWER BOUND on Firefox:
      `tagliati`/`usciti` are judged with `currentTime`, which is stale there, and
      a block that finished by itself can count as cut.
  And the SERVER's CPU in the same window (`/proc/stat` every second, all the
  cpus: mean, p95, the busiest core), and — if the bench runs on the server — the
  hungriest processes at mid window.  It is the datum for hypothesis (b): CPU
  contention between the browser and the session doing video.

THE COMBINATIONS (one at a time: each one is a launch):
    --quale f012   the tone of F-012 (pw-play, 440 Hz), NO video
    --quale f013   the video of F-013 (ffplay 1280x720, 660 Hz), WITHOUT photos
    --video-worker the page with `#video=worker`: decoding and drawing of the video
                   in the worker (switch already in the product, off by default).
                   The bench VERIFIES inside the page that the worker is on.

JUDGMENT (for the suite register; it is a measurement, the table counts more):
    PASS  Δriarmi = 0 and Δscartati_pieno = 0 in the window
    FAIL  at least one re-arm (= at least one 250 ms gap)
    BLOCKED  audio context never «running», worker requested and not on, etc.

FAULT (--guasto, same session): the PAGE's main thread is stopped
  for 400 ms every 2 s (an injected busy loop: more than the cushion) for 20 s
  ⇒ the same measurement must count re-arms (>= 3).  If it does not count them, the measurement is
  blind and the healthy one is worth nothing.

OUTPUT: besides the SUITE lines, a line `MISURA {...}` with all the numbers
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

QUI = os.path.dirname(os.path.abspath(__file__))


def _modulo(nome, file):
    s = _iu.spec_from_file_location(nome, os.path.join(QUI, file))
    m = _iu.module_from_spec(s)
    s.loader.exec_module(m)
    return m


G4 = _modulo("g4", "15-g4-comune.py")
F12 = _modulo("f012", "15-f012-audio.py")
F13 = _modulo("f013", "15-f013-video.py")

FUNZIONI = ("D-006",)
BLOCCO_S = 0.020           # one audio block = 20 ms (RCP §6.3)
CUSCINO_S = 0.250          # AUDIO_CUSCINO_MS: the minimum gap of a re-arm
CONTI = ("ricevuti", "suonati", "riarmi", "tirate", "tagliati", "usciti", "sospesi",
         "scartati_pieno", "scartati_tardivi", "scartati_vecchi", "mancati", "salti_suono")
GUASTO_S = 20.0


def extra(a):
    a.add_argument("--quale", choices=("f012", "f013"), default="f013",
                   help="the scene: f012 tone without video, f013 video (⚠ not `--scena`: suite.py rewrites it)")
    a.add_argument("--video-worker", action="store_true")
    a.add_argument("--pcm", action="store_true",
                   help="audio in PCM instead of Opus: the bench makes the page say that the engine "
                        "does not decode Opus (no AudioDecoder in the audio path)")
    a.add_argument("--nnn", default="906",
                   help="the three digits of the tenant c15<nnn>u<n> (agents in parallel: different)")
    a.add_argument("--finestra-s", type=float, default=60.0)
    a.add_argument("--assesta-s", type=float, default=5.0,
                   help="wait after the wake-up, before the window")


# ═══════════════════════════════════════════════════════════════════════════
#  THE PURE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════
def delta(c0, c1, ms0, ms1, blocco_s=BLOCCO_S):
    """The counts of the window: differences + estimates.  `ms` = performance.now().
    ⚠ `blocco_s`: 20 ms for Opus, 5 ms for PCM (`[M]` 200 blocks/s)."""
    d = {k: (c1.get(k) or 0) - (c0.get(k) or 0) for k in CONTI}
    durata = max(1e-3, (ms1 - ms0) / 1000.0)
    d["durata_s"] = round(durata, 1)
    d["udibile_stima_pct"] = round(min(100.0, 100.0 * d["usciti"] * blocco_s / durata), 1)
    d["silenzio_minimo_s"] = round(d["riarmi"] * CUSCINO_S, 2)
    d["contesto"] = c1.get("contesto")
    d["orologio_stantio_ms"] = c1.get("orologio_stantio_ms")   # only if the page carries it
    return d


def cpu_da_stat(righe):
    """From the readings of `grep ^cpu /proc/stat` (blocks separated by '---'):
    {mean, p95, max} of the total and the busiest core (mean), in %."""
    blocchi, cur = [], {}
    for r in righe:
        r = r.strip()
        if r == "---":
            if cur:
                blocchi.append(cur)
            cur = {}
            continue
        p = r.split()
        if not p or not p[0].startswith("cpu"):
            continue
        v = [int(x) for x in p[1:]]
        idle = v[3] + (v[4] if len(v) > 4 else 0)
        cur[p[0]] = (sum(v[:8]), idle)
    if cur:
        blocchi.append(cur)
    if len(blocchi) < 2:
        return None
    tot, core = [], {}
    for a, b in zip(blocchi, blocchi[1:]):
        for nome in b:
            if nome not in a:
                continue
            dt = b[nome][0] - a[nome][0]
            di = b[nome][1] - a[nome][1]
            if dt <= 0:
                continue
            busy = 100.0 * (dt - di) / dt
            if nome == "cpu":
                tot.append(busy)
            else:
                core.setdefault(nome, []).append(busy)
    if not tot:
        return None
    s = sorted(tot)
    medie = {k: sum(v) / len(v) for k, v in core.items() if v}
    caldo = max(medie.items(), key=lambda kv: kv[1]) if medie else (None, None)
    return {"campioni": len(tot), "media": round(sum(tot) / len(tot), 1),
            "p95": round(s[min(len(s) - 1, int(0.95 * len(s)))], 1), "max": round(s[-1], 1),
            "core_piu_carico": caldo[0], "core_piu_carico_media": round(caldo[1] or 0, 1),
            "core": len(medie)}


def giudica(d):
    if d.get("contesto") != "running":
        return "BLOCKED", "the audio context is not «running» at the end of the window (%s)" % d.get("contesto")
    if d["ricevuti"] <= 0:
        return "BLOCKED", "no audio block received in the window"
    if d["riarmi"] == 0 and d["scartati_pieno"] == 0:
        return "PASS", ("no gap: re-arms 0 in %.0f s (tirate %d, tagliati %d, estimated audible "
                        ">= %.1f%%)" % (d["durata_s"], d["tirate"], d["tagliati"],
                                        d["udibile_stima_pct"]))
    return "FAIL", ("%d re-arms in %.0f s = at least %.2f s of silence (tirate %d, tagliati %d, "
                    "full %d, estimated audible >= %.1f%%)"
                    % (d["riarmi"], d["durata_s"], d["silenzio_minimo_s"], d["tirate"],
                       d["tagliati"], d["scartati_pieno"], d["udibile_stima_pct"]))


def certifica():
    ok = True

    def chk(nome, cond):
        nonlocal ok
        print("   %s %s" % ("⭐" if cond else "⛔", nome))
        ok = ok and cond
    c0 = {k: 0 for k in CONTI}
    c0.update(ricevuti=100, suonati=90, usciti=80, contesto="running")
    sano = dict(c0, ricevuti=3100, suonati=3090, usciti=3080, contesto="running")
    d = delta(c0, sano, 1000.0, 61000.0)
    e, _ = giudica(d)
    chk("healthy: 60 s, 3000 blocks out, 0 re-arms ⇒ PASS, audible 100%", e == "PASS"
        and d["udibile_stima_pct"] == 100.0 and d["durata_s"] == 60.0)
    rotto = dict(sano, riarmi=7, tirate=90, tagliati=200, usciti=2700)
    d = delta(c0, rotto, 1000.0, 61000.0)
    e, r = giudica(d)
    chk("7 re-arms ⇒ FAIL, minimum silence 1.75 s (%s)" % r, e == "FAIL"
        and d["silenzio_minimo_s"] == 1.75)
    pieno = dict(sano, scartati_pieno=1)
    chk("an overflow without re-arms ⇒ FAIL", giudica(delta(c0, pieno, 0, 60000))[0] == "FAIL")
    muto = dict(sano, contesto="suspended")
    chk("context suspended ⇒ BLOCKED", giudica(delta(c0, muto, 0, 60000))[0] == "BLOCKED")
    vuoto = dict(c0)
    chk("no block ⇒ BLOCKED", giudica(delta(c0, vuoto, 0, 60000))[0] == "BLOCKED")
    # the CPU: two cores, three readings 1 s apart; cpu0 at 100 %, cpu1 at 0 %
    st = ["cpu  0 0 0 0 0 0 0 0", "cpu0 0 0 0 0 0 0 0 0", "cpu1 0 0 0 0 0 0 0 0", "---",
          "cpu  100 0 0 100 0 0 0 0", "cpu0 100 0 0 0 0 0 0 0", "cpu1 0 0 0 100 0 0 0 0", "---",
          "cpu  200 0 0 200 0 0 0 0", "cpu0 200 0 0 0 0 0 0 0", "cpu1 0 0 0 200 0 0 0 0"]
    c = cpu_da_stat(st)
    chk("cpu: mean 50%%, busiest core cpu0 at 100%% (%s)" % c,
        c and c["media"] == 50.0 and c["core_piu_carico"] == "cpu0"
        and c["core_piu_carico_media"] == 100.0 and c["campioni"] == 2)
    chk("cpu: a single reading ⇒ no number", cpu_da_stat(st[:3]) is None)
    print("⭐ certified" if ok else "⛔ NOT certified")
    return 0 if ok else 1


# ═══════════════════════════════════════════════════════════════════════════
#  THE SERVER'S CPU, during the window
# ═══════════════════════════════════════════════════════════════════════════
SUL_SERVER = os.environ.get("REMOTIX_SUL_SERVER") == "1"


class Cpu:
    """`grep ^cpu /proc/stat` every second.  ⭐ On the server it is read LOCALLY (the
    browser runs there); otherwise inside the box, where `/proc/stat` is the
    host's (podman does not isolate it)."""

    def __init__(self, sc, secondi):
        self.sc, self.secondi, self.righe, self.ps = sc, secondi, [], ""
        self._t = None

    def _locale(self):
        fine = time.time() + self.secondi
        meta = time.time() + self.secondi / 2
        while time.time() < fine:
            try:
                with open("/proc/stat") as f:
                    self.righe += [r for r in f if r.startswith("cpu")] + ["---"]
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

    def _scatola(self):
        n = int(self.secondi)
        _c, t = self.sc.dentro("for i in $(seq %d); do grep ^cpu /proc/stat; echo ---; sleep 1; "
                               "done" % n, n + 60)
        self.righe = (t or "").splitlines()

    def accendi(self):
        self._t = threading.Thread(target=self._locale if SUL_SERVER else self._scatola,
                                   daemon=True)
        self._t.start()

    def leggi(self):
        if self._t:
            self._t.join(timeout=90)
        return cpu_da_stat(self.righe), self.ps


# ═══════════════════════════════════════════════════════════════════════════
#  THE TEST
# ═══════════════════════════════════════════════════════════════════════════
def conti_pagina(g):
    return G4.in_pagina(g, "(function(){ return { ora: performance.now(),"
                           " conti: (typeof audio_conti === 'function') ? audio_conti() : null,"
                           " worker: (typeof VW !== 'undefined') && VW !== null }; })()")


def aspetta(g, cond, tetto_s):
    fine = time.time() + tetto_s
    r = None
    while time.time() < fine:
        r = conti_pagina(g)
        if r and cond(r):
            return True, r
        time.sleep(0.5)
    return False, r


def finestra(s, o, secondi):
    blocco = 0.005 if getattr(o, "pcm", False) else BLOCCO_S
    """(delta, cpu, ps) over `secondi`, two readings of `audio_conti()`."""
    cpu = Cpu(s.sc, secondi)
    r0 = conti_pagina(s.g)
    cpu.accendi()
    time.sleep(secondi)
    r1 = conti_pagina(s.g)
    c, ps = cpu.leggi()
    if not r0 or not r1 or not r0.get("conti") or not r1.get("conti"):
        raise S.Bloccata("audio_conti() cannot be read from the page (%r / %r)" % (r0, r1))
    return delta(r0["conti"], r1["conti"], r0["ora"], r1["ora"], blocco), c, ps, r1


# ⛔ The fault: a busy loop IN THE PAGE, 400 ms every 2 s — the main
#   thread stopped beyond the cushion.  Only the bench puts it, only in the fault.
JS_GUASTO = ("window.__c15d006 = setInterval(function(){ const f = performance.now() + 400;"
             " while (performance.now() < f) {} }, 2000);")
JS_GUASTO_VIA = "clearInterval(window.__c15d006);"


def corpo(o, E):
    if o.video_worker:
        o.url = o.url.split("#")[0] + "#video=worker"
    sess = S.Sessione(o, o.nnn, E)
    G4.robusta(sess.sc)
    with sess as s:
        ok, m = s.pr.apri()
        if not ok:
            raise S.Bloccata("the page does not open: " + m)
        if o.pcm:
            # ⚠ BENCH ONLY: before login (the negotiation is at connection),
            #   `isConfigSupported` says «no» to Opus ⇒ the page declares «pcm» and the
            #   server sends PCM.  It removes `AudioDecoder` from the audio path.
            #   ⭐ D-006 cure: and also the page's wasm decoder must not
            #   start (WebAssembly.instantiate refuses), or the page declares Opus.
            s.g.js(G4._inietta("if (window.AudioDecoder) AudioDecoder.isConfigSupported ="
                               " async function () { return { supported: false }; };"
                               " if (window.WebAssembly) WebAssembly.instantiate ="
                               " function () { return Promise.reject(new Error('bench: PCM')); };"))
        ok, m = s.entra(apri=False)            # ⭐ WITHOUT ear
        if not ok:
            raise S.Bloccata(m)
        r = conti_pagina(s.g) or {}
        if o.video_worker and not r.get("worker"):
            raise S.Bloccata("#video=worker requested but in the page the worker is off (%r)" % r)
        if o.quale == "f012":
            ok, m = F12.prepara_tono_ffmpeg(s)
            if not ok:
                raise S.Bloccata("the tone does not get ready: " + m)
            c, t = F12.suona(s)
            if c != 0:
                raise S.Bloccata("pw-play does not start: " + t[-200:])
            punto = (0.62, 0.55)
        else:
            ok, m = F13.prepara_video(s)
            if not ok:
                raise S.Bloccata("the video is not generated: " + m)
            c, t = F13.accendi_video(s)
            if c != 0:
                raise S.Bloccata("ffplay does not start: " + t[-200:])
            punto = (0.97, 0.5)                # right edge: outside the video window
        note = ["scene %s%s%s" % (o.quale, " · #video=worker (on)" if o.video_worker else "",
                                  " · PCM" if o.pcm else "")]
        ok, r = aspetta(s.g, lambda x: (x.get("conti") or {}).get("contesto") not in
                        (None, "(none)"), 30)
        if not ok:
            raise S.Bloccata("the page did not create an AudioContext in 30 s (%r)" % r)
        note.append(G4.clic_vero(s, *punto))
        ok, r = aspetta(s.g, lambda x: (x.get("conti") or {}).get("contesto") == "running", 10)
        if not ok:
            raise S.Bloccata("the audio context does not wake up at the click (%r)" % (r or {}).get("conti"))
        if o.pcm and (r.get("conti") or {}).get("codec") != 2:
            raise S.Bloccata("PCM requested but the page receives codec %r"
                             % (r.get("conti") or {}).get("codec"))
        time.sleep(o.assesta_s)
        segno = s.segno_registro()
        d, cpu, ps, r1 = finestra(s, o, o.finestra_s)
        e, ragione = giudica(d)
        cf = r1.get("conti") or {}
        #   ⭐ who decodes the Opus (wasm since the D-006 cure, AudioDecoder before)
        note.append("decoder %s (%s/%s us mean/max)" % (
            cf.get("decodificatore", "(old page: AudioDecoder)"),
            cf.get("dec_us_medio"), cf.get("dec_us_max")))
        misura = {"scatola": o.scatola, "browser": o.browser, "versione": E.versione,
                  "scena": o.quale, "worker": bool(o.video_worker), "pcm": bool(o.pcm), "delta": d, "cpu": cpu,
                  "conti_fine": r1.get("conti")}
        print("MISURA " + json.dumps(misura, ensure_ascii=False), flush=True)
        ev = [G4.salva_json(o, "d006-misura-%s-%s-%s%s.json" % (
            o.scatola, o.browser, o.quale, ("-worker" if o.video_worker else "") + ("-pcm" if o.pcm else "")),
            dict(misura, ps=ps)),
              s.salva_testo("server-d006.txt", s.registro_da(segno) if segno else []),
              s.salva_console()]
        E.metti("D-006", e, ragione,
                atteso="re-arms 0 in %.0f s, without ear (page counts)" % o.finestra_s,
                osservato="; ".join(note) + " · cpu %s" % cpu, evidenze=[p for p in ev if p],
                numeri=misura)

        if o.guasto:
            s.g.js(G4._inietta(JS_GUASTO))
            try:
                dg, _c, _p, _r = finestra(s, o, GUASTO_S)
            finally:
                s.g.js(G4._inietta(JS_GUASTO_VIA))
            visto = dg["riarmi"] >= 3
            E.guasto("D-006", visto, "page main thread stopped 400 ms every 2 s for "
                     "%.0f s ⇒ re-arms %d (expected >= 3), tirate %d"
                     % (GUASTO_S, dg["riarmi"], dg["tirate"]), numeri={"delta": dg})


if __name__ == "__main__":
    sys.exit(S.esegui(__doc__, FUNZIONI, corpo, certifica, extra))
