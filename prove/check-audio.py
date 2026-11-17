#!/usr/bin/env python3
"""check-audio - a 440 Hz tone played in the user's session is HEARD in the browser (SPECS section 10), Chrome and Firefox.

    python3 check-audio.py [--box xfce|lxqt|gnome|kde] [--browser chrome|firefox] [--firefox-autoplay-pref] [--js-login]

Runs ON THE DEV SERVER. One line: PASS|FAIL|BLOCKED audio-<box>-<browser> - evidence; exit 0 only if PASS.
  FAIL = the product did not do it (also: page or login refused).   BLOCKED = the tool could not look.
Its own user ac1 is made in the box. Firefox needs a PulseAudio-compatible server: the host's (server/prepara-server.sh).
The ear: an AnalyserNode inserted in the page between the blocks the page schedules and the AudioDestinationNode (what goes
to the loudspeaker), RMS and peak frequency every 100 ms, only counted while the AudioContext is `running` (adapted from the
old bench 15-g4-common.py). The login is done with REAL input (click, type, Enter), as a person does. Stages:
  A  the tone is heard with no gesture other than the login;  B  after one REAL click on the canvas;
  --firefox-autoplay-pref (Firefox only) is a DIAGNOSIS run: media.autoplay.default=0, a preference a real user does not have,
  to tell a product that never starts audio from a browser policy. Reported separately, never counted as the product's PASS.
PASS when A or B is audible at 440 Hz; the stage and the context states are always printed."""
import argparse
import json
import math
import os
import struct
import sys
import tempfile
import time
import wave

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
from lib import PASS, FAIL, BLOCKED, Fail, ToolError  # noqa: E402

USER, PASSWORD = "ac1", "acpass7391"
TONE_HZ = 440
EAR_JS = r"""
(function () {
  if (window.__ear) return;
  const O = window.__ear = { s: [], ctxs: [], err: [] };
  const orig = AudioNode.prototype.connect;
  function an_of(ctx) {
    if (ctx.__an) return ctx.__an;
    const an = ctx.createAnalyser(); an.fftSize = 8192; an.smoothingTimeConstant = 0;
    orig.call(an, ctx.destination);
    ctx.__an = an; ctx.__td = new Float32Array(an.fftSize); ctx.__fd = new Float32Array(an.frequencyBinCount);
    O.ctxs.push(ctx); return an;
  }
  const C0 = window.__AC0 = window.AudioContext;
  window.AudioContext = function () { const c = new C0(...arguments); try { an_of(c); } catch (e) { O.err.push(String(e)); } return c; };
  window.AudioContext.prototype = C0.prototype;
  AudioNode.prototype.connect = function (d) {
    try {
      if (d instanceof AudioDestinationNode && !(this instanceof AnalyserNode)) {
        const r = Array.prototype.slice.call(arguments, 1); orig.apply(this, [an_of(d.context)].concat(r)); return d;
      }
    } catch (e) { O.err.push(String(e)); }
    return orig.apply(this, arguments);
  };
  setInterval(function () {
    const ctx = O.ctxs.length ? O.ctxs[O.ctxs.length - 1] : null;
    const c = { t: performance.now(), state: ctx ? ctx.state : "none", rms: null, hz: null };
    if (ctx && ctx.state === "running") {
      const an = ctx.__an, td = ctx.__td, fd = ctx.__fd; an.getFloatTimeDomainData(td);
      let s = 0; for (let i = 0; i < td.length; i++) s += td[i] * td[i]; c.rms = Math.sqrt(s / td.length);
      an.getFloatFrequencyData(fd); const step = ctx.sampleRate / an.fftSize; let k = -1, m = -Infinity;
      for (let i = Math.ceil(30 / step); i < fd.length - 1; i++) if (fd[i] > m) { m = fd[i]; k = i; }
      if (k > 0 && isFinite(m)) { const a = fd[k - 1], b = fd[k], d = fd[k + 1], den = a - 2 * b + d;
        c.hz = (k + ((isFinite(a) && isFinite(d) && den !== 0) ? 0.5 * (a - d) / den : 0)) * step; }
    }
    O.s.push(c); if (O.s.length > 4000) O.s.splice(0, 1000);
  }, 100);
})();
"""


def in_page(g, expr):
    """Evaluate `expr` in the REAL page (a <script>, not the driver's sandbox), value back through a DOM attribute."""
    body = ("(function(){let v;try{v=(function(){return (%s);})();}catch(e){v={err:String(e)};}"
            "document.documentElement.setAttribute('data-ac',JSON.stringify(v));})();" % expr)
    g.js("document.documentElement.removeAttribute('data-ac'); return 1;")
    g.js("const s=document.createElement('script'); s.textContent=arguments[0];"
         "(document.head||document.documentElement).appendChild(s); s.remove(); return 1;", body)
    t = g.js("return document.documentElement.getAttribute('data-ac');")
    return json.loads(t) if t else None


def mount_ear(g):
    in_page(g, "1")
    g.js("const s=document.createElement('script'); s.textContent=arguments[0];"
         "(document.head||document.documentElement).appendChild(s); s.remove(); return 1;", EAR_JS)
    return bool(in_page(g, "!!window.__ear"))


def snapshot(g):
    return in_page(g, "{now:performance.now(), n:window.__ear.ctxs.length, err:window.__ear.err.slice(0,3),"
                      " st:window.__ear.ctxs.length?window.__ear.ctxs[window.__ear.ctxs.length-1].state:null,"
                      " counts:(typeof audio_counts==='function')?audio_counts():null, s:window.__ear.s.slice(-60)}") or {}


def listen(g, seconds):
    """(fraction audible, median Hz of the audible, samples, states seen) over `seconds` of the ear."""
    t0 = in_page(g, "performance.now()")
    time.sleep(seconds)
    s = [c for c in (in_page(g, "window.__ear.s.filter(c=>c.t>=%f)" % t0) or [])]
    aud = [c for c in s if c["state"] == "running" and (c.get("rms") or 0) > 0.01]
    hz = sorted(c["hz"] for c in aud if c.get("hz"))
    states = sorted({c["state"] for c in s})
    return (len(aud) / len(s) if s else 0.0), (hz[len(hz) // 2] if hz else None), len(s), states, \
        max([c.get("rms") or 0 for c in s] or [0])


def verdict(r):
    frac, hz, n, states, peak = r
    return n >= 10 and frac >= 0.8 and hz is not None and abs(hz - TONE_HZ) <= 12


def describe(r):
    frac, hz, n, states, peak = r
    return "audible %.0f%% of %d samples, peak %s Hz, max RMS %.3f, context %s" % (100 * frac, n, "%.0f" % hz if hz else "-", peak, "/".join(states))


def probe(g):
    """Control, independent of the product: a BARE AudioContext created now and read 2 s later (the browser's own verdict for
    this page after the gestures so far), focus/visibility, the user-activation flags, the product's wake-up count and log."""
    in_page(g, "(function(){window.__bare=new window.__AC0(); return 1;})()")
    time.sleep(2)
    r = in_page(g, "(function(){const c=window.__bare; const st=c.state; try{c.close();}catch(e){}"
                   " const k=(typeof audio_counts==='function')?audio_counts():{};"
                   " return {act:[navigator.userActivation.hasBeenActive, navigator.userActivation.isActive], bare:st,"
                   " focus:document.hasFocus(), vis:document.visibilityState, wakeups:k.wakeups, played:k.played,"
                   " ctx:window.__ear.ctxs.length?window.__ear.ctxs[window.__ear.ctxs.length-1].state:null,"
                   " log:(document.getElementById('logbook')||{}).textContent||''};})()") or {}
    lines = [x.strip() for x in r.get("log", "").splitlines() if "audio context" in x.lower() or "woke" in x.lower()]
    return ("activation(hasBeenActive,isActive)=%s, document focus=%s visibility=%s, bare AudioContext (read 2 s after creation): %s, "
            "product context: %s, product wake-ups: %s, played blocks: %s, product log: %s") % (
        r.get("act"), r.get("focus"), r.get("vis"), r.get("bare"), r.get("ctx"), r.get("wakeups"), r.get("played"), " | ".join(lines[-3:])[:260])


def make_tone(path):
    with wave.open(path, "wb") as w:
        w.setnchannels(2), w.setsampwidth(2), w.setframerate(48000)
        w.writeframes(b"".join(struct.pack("<hh", *(2 * [int(16383 * math.sin(2 * math.pi * TONE_HZ * i / 48000))])) for i in range(48000 * 20)))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--browser", default="chrome", choices=("chrome", "firefox"))
    ap.add_argument("--firefox-autoplay-pref", action="store_true", help="DIAGNOSIS: Firefox with media.autoplay.default=0")
    ap.add_argument("--js-login", action="store_true", help="DIAGNOSIS: log in with a synthetic JS submit (no real gesture), as the old bench did")
    ap.add_argument("--cap", type=int, default=60)
    a = ap.parse_args()
    name = "audio-%s-%s%s" % (a.box, a.browser, "-autoplay-pref-DIAGNOSIS" if a.firefox_autoplay_pref else "") + ("-jslogin-DIAGNOSIS" if a.js_login else "")
    res, rig = lib.Results([name]), lib.Rig(a.box, a.browser, USER, PASSWORD, "audio", cap=a.cap, sound=True,
                                prefs={"media.autoplay.default": 0} if a.firefox_autoplay_pref else None)

    def flow():
        ver = rig.start()
        rig.open_page()
        g = rig.g
        if not mount_ear(g):
            raise ToolError("the ear did not mount in the page (CSP or driver)")
        rig.login(real=not a.js_login)
        rig.settle(a.cap)
        wav = os.path.join(tempfile.mkdtemp(prefix="tone-", dir=lib.WORK), "tone.wav")
        make_tone(wav)
        r = lib.subprocess.run([rig.box.sh, "ssh", a.box, "cat > /tmp/rx-tone.wav && chmod 644 /tmp/rx-tone.wav"], stdin=open(wav, "rb"), capture_output=True, timeout=60)
        lib.shutil.rmtree(os.path.dirname(wav), ignore_errors=True)
        if r.returncode:
            raise ToolError("cannot write the tone in the box: %s" % r.stderr[-150:])
        rig.box.in_session(USER, "while true; do pw-play /tmp/rx-tone.wav || sleep 1; done # rx-tone")
        # wait for the page to build its AudioContext (first audio delivery)
        end, snap = time.time() + 30, {}
        while time.time() < end:
            snap = snapshot(g)
            if snap.get("n", 0) > 0:
                break
            time.sleep(0.5)
        if not snap.get("n"):
            pw = rig.box.run("pgrep -u %s -x pw-play | head -1; runuser -u %s -- env XDG_RUNTIME_DIR=/run/user/$(id -u %s) wpctl get-volume @DEFAULT_AUDIO_SINK@ 2>&1 | head -2"
                             % (USER, USER, USER))[1].replace("\n", " ")
            cnt = snap.get("counts") or {}
            raise Fail("%s: a tone plays in the session but the page never created an AudioContext in 30 s (received=%s played=%s; in the box pw-play pid / default sink volume: %s; page log tail: %s)"
                       % (ver, cnt.get("received"), cnt.get("played"), pw, " | ".join((rig.state().get("log") or "").strip().splitlines()[-2:])[:200]))
        born = snap.get("st")
        A = listen(g, 6)
        stages = ["context born %s; A (login gesture only): %s" % (born, describe(A))]
        passed = "A" if verdict(A) else None
        if not passed:
            rig.canvas_click(0.62, 0.55)  # one REAL click on the picture, like the user
            time.sleep(1.5)
            B = listen(g, 6)
            stages.append("B (after a real canvas click): %s" % describe(B))
            passed = "B" if verdict(B) else None
        stages.append("control: " + probe(g))
        ev = "%s: %s; page audio counts %s" % (ver, "; ".join(stages), json.dumps(snapshot(g).get("counts"))[:160])
        res.say(PASS if passed else FAIL, name, ("heard at stage %s - " % passed if passed else "NOT heard - ") + ev)

    try:
        return res.sequence(flow, 420)
    finally:
        rig.stop()
        rig.box.run("pkill -u %s -f rx-tone; pkill -u %s -x pw-play; rm -f /tmp/rx-tone.wav; true" % (USER, USER), timeout=20)


if __name__ == "__main__":
    sys.exit(main())
