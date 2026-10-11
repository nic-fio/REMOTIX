#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
15-g4-common — THE EAR AND THE EYE OF GROUP G4 (audio and video), phase 15.

Used by `15-f012-audio.py` and `15-f013-video.py`.  Three things:

1. ⭐ THE EAR IN THE PAGE.  The page's sound is born in `src/page.html`
   (`start_audio` → `suona()`): one `AudioBufferSourceNode` per block, connected
   with `s.connect(ctx.destination)`.  The bench replaces, IN THE REAL PAGE
   (script in the DOM, not the driver's sandbox), `AudioNode.prototype.connect`:
   when the destination is the `AudioDestinationNode`, the block goes through an
   `AnalyserNode` that in turn goes to the destination ⇒ the output stays
   identical (the analyser is a pass-through), and the analyser hears EXACTLY
   what goes to the loudspeaker, AFTER the scheduling, the cushion, the cuts.
   Every 100 ms the level (RMS of the time domain) and the peak frequency are read
   (FFT 8192 at 48 kHz, parabolic interpolation), with the state of the context.
   ⛔ A `suspended` context does NOT count as sound: its analyser keeps the last
   frame, and it is marked as «not audible».

2. ⭐ THE SOUND JUDGE (pure, certified): audible fraction, peak frequency
   relative to the expectation, longest gap.

3. ⭐ THE EYE ON THE VIDEO (pure, certified): the video window is found by
   DIFFERENCE between photos (it is the only thing that changes entirely), then for each
   photo: uniform background in a saturated colour (the video is there, no mosaic: tiles
   of another colour beyond those of the target ⇒ red) and difference from the previous
   photo (the image moves; a long freeze ⇒ red).
"""
import base64
import io
import json
import math
import os
import time

# ═══════════════════════════════════════════════════════════════════════════
#  1. THE EAR IN THE PAGE
# ═══════════════════════════════════════════════════════════════════════════
EAR_JS = r"""
(function () {
  if (window.__c15orecchio) return;
  const O = window.__c15orecchio = { campioni: [], contesti: [], agganci: 0, errori: [] };
  const originale = AudioNode.prototype.connect;
  function analizzatore(ctx) {
    if (ctx.__c15an) return ctx.__c15an;
    const an = ctx.createAnalyser();
    an.fftSize = 8192;
    an.smoothingTimeConstant = 0;
    originale.call(an, ctx.destination);
    ctx.__c15an = an;
    ctx.__c15t = new Float32Array(an.fftSize);
    ctx.__c15f = new Float32Array(an.frequencyBinCount);
    O.contesti.push(ctx);
    return an;
  }
  /* ⚠ Also at the context's BIRTH, not only at the first `connect`: with the context
     suspended `suona()` throws the blocks away without connecting them (count `sospesi`), and an
     ear waiting for the `connect` would never see the mute context. */
  const CtxOrig = window.AudioContext;
  if (CtxOrig) {
    const Ctx = function () {
      const c = new CtxOrig(...arguments);
      try { analizzatore(c); } catch (e) { if (O.errori.length < 20) O.errori.push(String(e)); }
      return c;
    };
    Ctx.prototype = CtxOrig.prototype;
    window.AudioContext = Ctx;
  }
  AudioNode.prototype.connect = function (dest) {
    try {
      if (dest instanceof AudioDestinationNode && !(this instanceof AnalyserNode)) {
        O.agganci++;
        const an = analizzatore(dest.context);
        const r = Array.prototype.slice.call(arguments, 1);
        originale.apply(this, [an].concat(r));
        return dest;
      }
    } catch (e) { if (O.errori.length < 20) O.errori.push(String(e)); }
    return originale.apply(this, arguments);
  };
  function campiona() {
    const ctx = O.contesti.length ? O.contesti[O.contesti.length - 1] : null;
    const c = { t: performance.now(), state: ctx ? ctx.state : "none", rms: null,
                hz: null, ct: ctx ? ctx.currentTime : null };
    if (ctx && ctx.state === "running") {
      const an = ctx.__c15an, td = ctx.__c15t, fd = ctx.__c15f;
      an.getFloatTimeDomainData(td);
      let s = 0;
      for (let i = 0; i < td.length; i++) s += td[i] * td[i];
      c.rms = Math.sqrt(s / td.length);
      an.getFloatFrequencyData(fd);
      const passo = ctx.sampleRate / an.fftSize;
      let k = -1, m = -Infinity;
      for (let i = Math.ceil(30 / passo); i < fd.length - 1; i++)
        if (fd[i] > m) { m = fd[i]; k = i; }
      if (k > 0 && isFinite(m)) {
        const a = fd[k - 1], b = fd[k], d = fd[k + 1];
        const den = a - 2 * b + d;
        const p = (isFinite(a) && isFinite(d) && den !== 0) ? 0.5 * (a - d) / den : 0;
        c.hz = (k + p) * passo;
        c.db = m;
      }
    }
    O.campioni.push(c);
    if (O.campioni.length > 4000) O.campioni.splice(0, 1000);
  }
  O.timer = setInterval(campiona, 100);
})();
"""


def _inject(body):
    """A script in the REAL page (not in Marionette's sandbox)."""
    return ("const s = document.createElement('script');"
            "s.textContent = %s;"
            "(document.head || document.documentElement).appendChild(s); s.remove();"
            "return true;" % json.dumps(body))


def in_page(g, js_expr):
    """Evaluates `js_expr` IN THE REAL PAGE and returns the value (via JSON in a
    DOM attribute: Firefox's xrays do not let you see the properties
    written by the page)."""
    body = ("(function(){ let v; try { v = (function(){ return (%s); })(); }"
             " catch (e) { v = { __errore: String(e) }; }"
             " document.documentElement.setAttribute('data-c15g4', JSON.stringify(v));"
             " })();" % js_expr)
    g.js("document.documentElement.removeAttribute('data-c15g4'); return 1;")
    g.js(_inject(body))
    t = g.js("return document.documentElement.getAttribute('data-c15g4');")
    return json.loads(t) if t else None


def put_ear(g):
    """Mounts the ear.  Returns (ok, description)."""
    g.js(_inject(EAR_JS))
    r = in_page(g, "window.__c15orecchio ? { ok: true, ora: performance.now() } : null")
    if not r or not r.get("ok"):
        return False, "the ear did not mount in the page: %r" % (r,)
    return True, "ear mounted"


def now_page(g):
    r = in_page(g, "performance.now()")
    return float(r) if r is not None else None


def read_ear(g, da=0.0, a=None):
    """The samples with `da <= t < a` (page time, ms) and the state."""
    r = in_page(g, (
        "(function(){ const O = window.__c15orecchio; if (!O) return null;"
        " const da = %f, a = %s;"
        " return { ora: performance.now(), agganci: O.agganci, contesti: O.contesti.length,"
        "  errori: O.errori.slice(0, 5),"
        "  conti: (typeof audio_counts === 'function') ? audio_counts() : null,"
        "  campioni: O.campioni.filter(c => c.t >= da && (a === null || c.t < a)) }; })()"
        % (da, "null" if a is None else "%f" % a)))
    return r


def wait_context(g, cap_s=30):
    """Waits for the page to create its `AudioContext` (at the first audio
    delivery).  Returns (context state | None, page counts)."""
    fine = time.time() + cap_s
    r = None
    while time.time() < fine:
        r = in_page(g, "(function(){ const O = window.__c15orecchio;"
                         " return { n: O ? O.contesti.length : -1,"
                         " stato: O && O.contesti.length ? O.contesti[O.contesti.length-1].state : null,"
                         " conti: (typeof audio_counts === 'function') ? audio_counts() : null }; })()")
        if r and r.get("n", 0) > 0:
            return r.get("state"), r.get("counts")
        time.sleep(0.5)
    return None, (r or {}).get("counts")


def real_click(s, fx, fy):
    """⭐ A REAL click on the canvas (trusted browser event), like the user:
    it is the gesture that wakes up the audio.  Returns the description."""
    st = s.state()
    x, y = s.pr.center(st, fx, fy)
    s.g.click(x, y)
    return "real click at (%.0f, %.0f) of the glass" % (x, y)


# ═══════════════════════════════════════════════════════════════════════════
#  2. THE SOUND JUDGE (pure)
# ═══════════════════════════════════════════════════════════════════════════
RMS_THRESHOLD = 0.01          # −40 dBFS: the same as C5 (calibrated on real data)
TOLL_HZ = 12.0             # FFT 8192 @ 48 kHz: 5.9 Hz per bin


def median(v):
    v = sorted(v)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def judge_sound(samples, expected_hz, min_fraction=0.8, max_hole_s=None,
                  min_samples=10, threshold=RMS_THRESHOLD, toll=TOLL_HZ):
    """(outcome 'PASS'|'FAIL'|'BLOCKED', description, numbers).

    Audible = context `running` and RMS > threshold.  PASS if the audible fraction is
    >= `min_fraction`, and among the audible ones the peak frequency is within `toll`
    of the expectation for at least `min_fraction`, and (if requested) no silence
    gap longer than `max_hole_s`."""
    n = len(samples)
    if n < min_samples:
        return "BLOCKED", "only %d samples from the ear (%d needed)" % (n, min_samples), {}
    audible = [c for c in samples if c.get("state") == "running"
               and (c.get("rms") or 0) > threshold]
    pending = sum(1 for c in samples if c.get("state") != "running")
    fr = len(audible) / float(n)
    correct = [c for c in audible if c.get("hz") is not None
              and abs(c["hz"] - expected_hz) <= toll]
    fr_hz = len(correct) / float(len(audible)) if audible else 0.0
    # the longest gap: time between the first and the last sample of a run
    # of NON-audible ones (the gaps in the sampling do not count as silence)
    hole, start, prev = 0.0, None, None
    for c in samples:
        ud = c.get("state") == "running" and (c.get("rms") or 0) > threshold
        if not ud:
            start = c["t"] if start is None else start
            hole = max(hole, (c["t"] - start) / 1000.0 + 0.1)
        else:
            start = None
        prev = c
    rms_med = median([c["rms"] for c in audible]) if audible else 0.0
    hz_med = median([c["hz"] for c in audible if c.get("hz") is not None])
    dur = (samples[-1]["t"] - samples[0]["t"]) / 1000.0 if n > 1 else 0.0
    num = {"samples": n, "duration_s": round(dur, 1), "udibili": round(fr, 3),
           "pending": pending, "rms_mediano": round(rms_med or 0, 4),
           "dbfs": round(20 * math.log10(rms_med), 1) if rms_med else None,
           "hz_mediana": round(hz_med, 1) if hz_med else None,
           "hz_giusti": round(fr_hz, 3), "buco_max_s": round(hole, 2),
           "expected_hz": expected_hz}
    desc = ("%d samples in %.1f s: audible %.0f%% (median RMS %.3f = %s dBFS), median "
            "peak %s Hz (expected %.0f: right %.0f%%), longest gap %.1f s%s"
            % (n, dur, 100 * fr, rms_med or 0, num["dbfs"], num["hz_mediana"], expected_hz,
               100 * fr_hz, hole, (", %d samples with the context NOT running" % pending)
               if pending else ""))
    if pending == n:
        return "FAIL", "the page's audio context is never «running»: " + desc, num
    if fr < min_fraction:
        return "FAIL", "SILENCE (or almost): " + desc, num
    if fr_hz < min_fraction:
        return "FAIL", "there is sound but NOT at the expected frequency: " + desc, num
    if max_hole_s is not None and hole > max_hole_s:
        return "FAIL", "sound with a GAP of %.1f s (cap %.1f): %s" % (hole, max_hole_s, desc), num
    return "PASS", desc, num


def wave_wav(hz, seconds, amplitude=0.5, frequency=48000):
    """A pure tone, stereo s16 — the amplitude is a number of this file (like C5)."""
    import struct
    n = int(seconds * frequency)
    data = bytearray()
    for i in range(n):
        v = int(32767 * amplitude * math.sin(2 * math.pi * hz * i / frequency))
        data += struct.pack("<hh", v, v)
    head = (b"RIFF" + struct.pack("<I", 36 + len(data)) + b"WAVEfmt "
             + struct.pack("<IHHIIHH", 16, 1, 2, frequency, frequency * 4, 4, 16)
             + b"data" + struct.pack("<I", len(data)))
    return head + bytes(data)


# ═══════════════════════════════════════════════════════════════════════════
#  3. THE EYE ON THE VIDEO (pure)
# ═══════════════════════════════════════════════════════════════════════════
def reduced_photo(g, scale_factor=0.5):
    """The canvas photographed and reduced: (PIL RGB | None, png | None, reason)."""
    from PIL import Image
    try:
        _t0 = time.time()
        if hasattr(g, "cdp"):
            r = g.js("const t=document.getElementById('viewer');"
                     "if(!t) return null; const b=t.getBoundingClientRect();"
                     "return [b.left, b.top, b.width, b.height];")
            if not r:
                return None, None, "the canvas is not there"
            # ⚠ `[M]` 24 Sep: with the page STILL (video paused) Chrome waits for a
            #   new frame to photograph and took ~20 s.  A 2 px dot
            #   in a corner, outside the canvas, that changes ⇒ there is always a frame.
            g.js("let d=document.getElementById('c15g4-battito');"
                 "if(!d){d=document.createElement('div');d.id='c15g4-battito';"
                 "d.style.cssText='position:fixed;right:0;bottom:0;width:2px;height:2px;"
                 "pointer-events:none;z-index:2147483647';document.body.appendChild(d);}"
                 "d.style.background=d.style.background==='rgb(1, 1, 1)'?'rgb(2, 2, 2)':'rgb(1, 1, 1)';"
                 "return 1;")
            _t1 = time.time()
            sh = g.cdp.call("Page.captureScreenshot", format="png",
                              clip={"x": r[0], "y": r[1], "width": r[2], "height": r[3],
                                    "scale": scale_factor})
            png = base64.b64decode(sh["data"])
            if os.environ.get("C15G4_TIMES"):
                print("   [times] photo: before %.2f s, capture %.2f s" % (_t1 - _t0, time.time() - _t1),
                      flush=True)
            im = Image.open(io.BytesIO(png)).convert("RGB")
        else:
            png, _p = g.snapshot_canvas()
            if not png:
                return None, None, "the canvas cannot be photographed"
            im = Image.open(io.BytesIO(png)).convert("RGB")
            if scale_factor != 1:
                im = im.resize((max(1, int(im.size[0] * scale_factor)), max(1, int(im.size[1] * scale_factor))))
        return im, png, ""
    except Exception as e:                       # noqa: BLE001
        return None, None, "photo failed: %s" % str(e)[:200]


def _longest_run(values, threshold):
    """(start, end) of the longest contiguous run with value > soglia."""
    best, lung, i0 = (0, -1), 0, None
    for i, v in enumerate(list(values) + [0]):
        if v > threshold:
            i0 = i if i0 is None else i0
        elif i0 is not None:
            if i - i0 > lung:
                best, lung = (i0, i - 1), i - i0
            i0 = None
    return best


def find_video(imgs, threshold=24):
    """⭐ The video window: the pixels that change in ALL the pairs of consecutive
    photos (the video is the only thing that always changes).  Returns
    ((x0, y0, x1, y1) | None, description)."""
    from PIL import ImageChops
    if len(imgs) < 3:
        return None, "three photos are needed"
    mask = None
    for a, b in zip(imgs, imgs[1:]):
        d = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > threshold else 0)
        mask = d if mask is None else ImageChops.darker(mask, d)
    W, H = mask.size
    f = max(1, W // 480)
    small = mask.resize((W // f, H // f)) if f > 1 else mask
    w, h = small.size
    px = small.load()
    clr = [0] * w
    rig = [0] * h
    for y in range(h):
        for x in range(w):
            if px[x, y] > 127:
                clr[x] += 1
                rig[y] += 1
    if max(clr) == 0:
        return None, "no pixel changes in all the photos: the video does not move (or is not there)"
    x0, x1 = _longest_run(clr, 0.15 * max(clr))
    y0, y1 = _longest_run(rig, 0.15 * max(rig))
    if x1 < 0 or y1 < 0:
        return None, "no changing area"
    x0, x1, y0, y1 = x0 * f, (x1 + 1) * f - 1, y0 * f, (y1 + 1) * f - 1
    w, h = W, H
    ww, hh = x1 - x0 + 1, y1 - y0 + 1
    rap = ww / float(hh)
    desc = "changing area %dx%d at (%d,%d) on %dx%d, ratio %.2f" % (ww, hh, x0, y0, w, h, rap)
    if ww < 0.08 * w or hh < 0.08 * h:
        return None, "changing area too small: " + desc
    if not (16 / 9.0 * 0.75 <= rap <= 16 / 9.0 * 1.3):
        return None, "the changing area does not have the shape of the video (16:9): " + desc
    return (x0, y0, x1 + 1, y1 + 1), desc


def crop_box(im, box, margin=0.05):
    x0, y0, x1, y1 = box
    mx, my = (x1 - x0) * margin, (y1 - y0) * margin
    return im.crop((int(x0 + mx), int(y0 + my), int(x1 - mx), int(y1 - my))).resize((160, 90))


def examine_frame(crop):
    """A frame of the video (160x90): (ok, description, numbers).
    The background is ONE saturated colour (rotating hue); the white target covers at
    most ~9 tiles out of 144.  Tiles of a different colour beyond the target ⇒
    mosaic; non-saturated background ⇒ the video is not there (black, grey, desktop)."""
    tiles = []
    px = crop.load()
    for ty in range(9):
        for tx in range(16):
            r = g_ = b = 0
            for y in range(ty * 10, ty * 10 + 10):
                for x in range(tx * 10, tx * 10 + 10):
                    p = px[x, y]
                    r += p[0]
                    g_ += p[1]
                    b += p[2]
            tiles.append((r / 100.0, g_ / 100.0, b / 100.0))
    med = tuple(median([t[i] for t in tiles]) for i in range(3))
    sat = max(med) - min(med)
    diverse = sum(1 for t in tiles
                  if math.sqrt(sum((t[i] - med[i]) ** 2 for i in range(3))) > 60)
    num = {"fondo": [round(v) for v in med], "saturazione": round(sat), "tessere_diverse": diverse}
    if sat < 70:
        return False, "the video's background is not saturated (%s): the video is not seen" % (num["fondo"],), num
    if diverse > 16:
        return False, "MOSAIC: %d tiles out of 144 outside the background colour (the target covers <= 9)" % diverse, num
    if diverse < 1:
        return False, "the target is not there (no tile different from the background)", num
    return True, "background %s, %d different tiles (the target)" % (num["fondo"], diverse), num


def diff_media(a, b):
    from PIL import ImageChops, ImageStat
    return sum(ImageStat.Stat(ImageChops.difference(a, b)).mean) / 3.0


def judge_image(frames, min_ok=0.9, min_changes=0.9, max_block_s=4.0, change_threshold=6.0):
    """quadri: [(t_seconds, crop 160x90)].  (outcome, description, numbers)."""
    n = len(frames)
    if n < 5:
        return "BLOCKED", "only %d photos of the video" % n, {}
    exams = [examine_frame(c) for _t, c in frames]
    ok = sum(1 for e in exams if e[0])
    changes, block, start, block_max = 0, 0.0, None, 0.0
    diffs = []
    for (t0, a), (t1, b) in zip(frames, frames[1:]):
        d = diff_media(a, b)
        diffs.append(round(d, 1))
        if d > change_threshold:
            changes += 1
            start = None
        else:
            start = t0 if start is None else start
            block_max = max(block_max, t1 - start)
    fr_ok = ok / float(n)
    fr_c = changes / float(n - 1)
    dur = frames[-1][0] - frames[0][0]
    first_bad = next((e[1] for e in exams if not e[0]), "")
    num = {"photo": n, "duration_s": round(dur, 1), "quadri_buoni": round(fr_ok, 3),
           "cambi": round(fr_c, 3), "block_max_s": round(block_max, 1),
           "diff_mediana": median(diffs)}
    desc = ("%d photos in %.0f s: good frames %.0f%%, changes between consecutive photos %.0f%% "
            "(median difference %.1f), longest freeze %.1f s"
            % (n, dur, 100 * fr_ok, 100 * fr_c, num["diff_mediana"] or 0, block_max))
    if fr_c < min_changes or block_max > max_block_s:
        return "FAIL", "STILL IMAGE: " + desc, num
    if fr_ok < min_ok:
        return "FAIL", "wrong frames (%s): %s" % (first_bad, desc), num
    return "PASS", desc, num


# ═══════════════════════════════════════════════════════════════════════════
#  THE CERTIFICATION of the pure functions
# ═══════════════════════════════════════════════════════════════════════════
def _synthetic_frame(tint, mx, my, mosaic=False):
    from PIL import Image, ImageDraw
    import colorsys
    r, g, b = colorsys.hsv_to_rgb((tint % 360) / 360.0, 1, 1)
    im = Image.new("RGB", (640, 360), (int(r * 255), int(g * 255), int(b * 255)))
    d = ImageDraw.Draw(im)
    d.rectangle((mx, my, mx + 72, my + 72), fill=(255, 255, 255))
    if mosaic:
        r2, g2, b2 = colorsys.hsv_to_rgb(((tint + 150) % 360) / 360.0, 1, 1)
        for k in range(0, 640, 80):
            d.rectangle((k, 0, k + 40, 120), fill=(int(r2 * 255), int(g2 * 255), int(b2 * 255)))
    return im


def certify_common():
    from PIL import Image
    all_ok = True

    def di(name, ok, desc):
        nonlocal all_ok
        all_ok = all_ok and ok
        print("%s %s — %s" % ("⭐" if ok else "⛔", name, desc))

    def camp(hz, rms, n=60, state="running"):
        return [{"t": i * 100.0, "state": state, "rms": rms, "hz": hz} for i in range(n)]

    e, d, _ = judge_sound(camp(440.3, 0.35), 440)
    di("tone 440 expected 440 ⇒ PASS", e == "PASS", d)
    e, d, _ = judge_sound(camp(440.3, 0.35), 660)
    di("tone 440 expected 660 ⇒ FAIL", e == "FAIL", d)
    e, d, _ = judge_sound(camp(None, 0.0), 440)
    di("silence ⇒ FAIL", e == "FAIL", d)
    e, d, _ = judge_sound(camp(440, 0.35, state="suspended"), 440)
    di("context suspended (old frame) ⇒ FAIL", e == "FAIL", d)
    hole = camp(660, 0.3, 300)
    for c in hole[100:125]:
        c["rms"] = 0.0
    e, d, _ = judge_sound(hole, 660, min_fraction=0.9, max_hole_s=1.0)
    di("gap of 2.5 s over 30 s ⇒ FAIL", e == "FAIL", d)
    e, d, _ = judge_sound(camp(440, 0.35, 3), 440)
    di("three samples ⇒ BLOCKED", e == "BLOCKED", d)
    e, d, _ = judge_sound(camp(440, 0.005), 440)
    di("below threshold (−46 dBFS) ⇒ FAIL", e == "FAIL", d)

    # the video: a grey desktop canvas with the video at (300,200)
    def canvas(q):
        t = Image.new("RGB", (1920, 1080), (40, 44, 52))
        t.paste(q.resize((640, 360)), (300, 200))
        return t
    fotos = [canvas(_synthetic_frame(i * 94, 20 + (i * 97) % 540, 30 + (i * 53) % 260))
             for i in range(12)]
    box, d = find_video(fotos[:4])
    ok = box is not None and abs(box[0] - 300) <= 4 and abs(box[2] - 940) <= 4
    di("the video window is found by difference", ok, "%s · %s" % (box, d))
    if box:
        frames = [(i * 2.0, crop_box(f, box)) for i, f in enumerate(fotos)]
        e, d, _ = judge_image(frames)
        di("moving video ⇒ PASS", e == "PASS", d)
        stopped = [(i * 2.0, frames[3][1]) for i in range(12)]
        e, d, _ = judge_image(stopped)
        di("STILL video ⇒ FAIL", e == "FAIL", d)
        mos = [(i * 2.0, crop_box(canvas(_synthetic_frame(i * 94, 300, 200, mosaic=True)), box))
               for i in range(12)]
        e, d, _ = judge_image(mos)
        di("MOSAIC video ⇒ FAIL", e == "FAIL", d)
        nero = [(i * 2.0, Image.new("RGB", (160, 90), (0, 0, 0))) for i in range(12)]
        e, d, _ = judge_image(nero)
        di("BLACK video ⇒ FAIL", e == "FAIL", d)
    stills = [fotos[0]] * 4
    box, d = find_video(stills)
    di("no moving video ⇒ not found", box is None, d)
    wav = wave_wav(440, 0.1)
    di("the wave: WAV header and length", wav[:4] == b"RIFF" and len(wav) == 44 + 4800 * 4,
       "%d bytes" % len(wav))
    return 0 if all_ok else 1


def save_json(o, name, data):
    if not o.evidence:
        return ""
    p = os.path.join(o.evidence, name)
    with open(p, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return p


# ═══════════════════════════════════════════════════════════════════════════
#  ssh that does not give up at a passing refusal
# ═══════════════════════════════════════════════════════════════════════════
_TRANSIENT = ("Connection closed by", "kex_exchange_identification", "Connection reset by",
               "ssh_exchange_identification")


def robust(sc, attempts=6):
    """⚠ `[M]` 24 Sep 2026, ten agents on the same server: `sshd` refuses
    new connections when too many are negotiating (MaxStartups) ⇒
    «Connection closed by 192.168.0.2 port 22» at random.  Every `Scatola.dentro`
    opens a new connection: here it is RETRIED if the refusal is sshd's
    (no command executed), not if the command failed."""
    if getattr(sc, "_g4_robust", False):
        return sc
    original = sc.inside

    def inside(line, seconds=90):
        c, t = original(line, seconds)
        for k in range(attempts):
            if c == 0 or "@@code=" in (t or "") or not any(p in (t or "") for p in _TRANSIENT):
                break
            time.sleep(1.0 + k)
            c, t = original(line, seconds)
        return c, t
    sc.inside = inside
    sc._g4_robust = True
    return sc


def enter_with_ear(s):
    """The page, the ear BEFORE the login (the audio context can be born
    right after admission, if the session is already playing), then the login."""
    ok, m = s.pr.do_open()
    if not ok:
        return False, "the page does not open: " + m
    ok, m = put_ear(s.g)
    if not ok:
        return False, m
    ok, m = s.enter(do_open=False)
    if not ok:
        return False, "without a session there is nothing to look at: " + m
    return True, m
