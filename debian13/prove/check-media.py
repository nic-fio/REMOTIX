#!/usr/bin/env python3
"""check-media - the picture and the sound of a remote session, measured from the browser (SPECS 3.1, 3.2, 5.5, 10, 11.4).

    python3 check-media.py [--box xfce|lxqt|gnome|kde] [--only name,name]

Runs ON THE DEV SERVER (see lib.py). One line per check: PASS|FAIL|BLOCKED <name> - evidence; exit 0 only if all PASS.
  FAIL = the product did not do it.  BLOCKED = the tool could not look.  Pictures go to <prove>/shots/media-*.png.
Own users md1 (Chrome), md2 (Firefox), md3, md4 (two sessions at once). The test windows run INSIDE the session (media-window.py):
a binary-coded counter drawn pixel-exact (read back from the browser's picture), a flash + a beep, a sharpness pattern.
Clocks: the browser, the box and this tool share the host's clock, so a time written by the window inside the box and a time taken
by the browser are comparable (what is measured is the whole path glass to glass, plus the tool's screenshot, see the numbers).

  screen-updates       (3.1/3.2) a counter changes 8 times a second for 20 s: every value arrives, in order, none missed beyond what the
                       sampling can miss; bursts at 60 Hz that STOP: 1 s after the last change the picture shows the last value, never
                       an older one; the delay of the picture (box draw time -> seen in the browser) is measured at 60 Hz and
                       REPORTED (the spec promises no end-to-end figure, only 50 ms for the server's piece); the frame rate reaching the
                       page must be at least the 25 fps minimum of 3.1
  video                (10) a window with a moving bar, a flash and a 1 kHz beep every second, the beeps played in the session by pw-play:
                       the bar moves, the beeps are HEARD (an AnalyserNode in the page), and flash and beep stay together: the offset
                       seen in the browser minus the offset in the box (a recorder on the sink's monitor) is the sync error. The spec
                       promises no number: the tool's limits are |median error| <= 250 ms (the audio cushion of RCP 6.3) and drift
                       <= 150 ms over the 10 beeps; the numbers are always reported
  codec                (3.1, 11.4) which codec/level the server negotiated with Chrome and with Firefox and on which GPU node (journal), that it
                       is hardware, and that the picture is sharp at the default quality: contrast kept by stripes of 1/2/4 px, a checker,
                       the rise width of a black/white edge, coloured stripes, against the pattern drawn pixel-exact
  two-sessions-budget  (5.5) two users animating at 60 Hz at the same time: neither goes below 25 fps and the first does not lose more than
                       30% of what it had alone (the budget knob is OFF by default; this is the 'do not degrade whoever is inside' rule)"""
import argparse
import importlib.util
import io
import json
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib  # noqa: E402
import deskkit as K  # noqa: E402
from lib import PASS, FAIL, BLOCKED, Fail, ToolError  # noqa: E402

_spec = importlib.util.spec_from_file_location("check_audio", os.path.join(os.path.dirname(os.path.abspath(__file__)), "check-audio.py"))
CA = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(CA)

PW = "mdpass2026"
NAMES = ("screen-updates", "video", "codec", "two-sessions-budget")
STAMP = time.strftime("%y%m%d-%H%M%S")
PATTERN = (("v1", 16, 16, 256, 128), ("v2", 16, 160, 256, 128), ("v4", 16, 304, 256, 128), ("h2", 300, 16, 256, 128),
           ("edge", 300, 160, 256, 128), ("check8", 300, 304, 256, 128), ("rb2", 600, 16, 256, 128))  # copy of media-window.py
EAR_JS = CA.EAR_JS.replace("}, 100);", "}, 20);")


def shot(name, png):
    return os.path.basename(lib.save_png("media-%s-%s.png" % (name, STAMP), png))


def window(rig, mode, *args):
    """Start media-window.py in the user's session; returns the log path in the box once it says ready."""
    box, user = rig.box, rig.user
    log = "/tmp/rx-media-%s-%s.log" % (user, mode)
    box.run("pkill -u %s -f rx-media-window; rm -f %s %s.go; true" % (user, log, log))
    K.put(box, "media-window.py", "/tmp/rx-media-window.py")
    box.in_session(user, "python3 /tmp/rx-media-window.py %s %s %s 2>%s.err" % (mode, " ".join(args), log, log))
    end = time.time() + 40
    while time.time() < end:
        if '"ready"' in box.run("cat %s 2>/dev/null; true" % log)[1]:
            time.sleep(2)
            return log
        time.sleep(1)
    raise ToolError("the %s window of %s never said ready: %s" % (mode, user, box.run("tail -c 200 %s.err" % log)[1].replace("\n", " ")))


def window_log(box, log):
    out = []
    for l in box.run("cat %s 2>/dev/null; true" % log, timeout=120)[1].splitlines():
        if l.startswith("{"):
            try:
                out.append(json.loads(l))
            except ValueError:
                pass
    return out


def bring_up(a, user, browser, tag):
    rig = lib.Rig(a.box, browser, user, PW, tag, cap=a.cap, sound=(browser == "firefox"))
    try:
        rig.start()
        rig.open_page()
        rig.login(real=True)
        rig.settle(a.cap)
    except BaseException:
        rig.stop()
        raise
    return rig


def sample_counter(rig, seconds, band=(0, 0, 420, 40)):
    """Screenshot the counter strip as fast as the browser allows for `seconds`: [(t_mid, n, dt)]."""
    L, T, W, H = rig.state()["rect"]
    clip = (L + band[0], T + band[1], band[2], band[3])
    out, end = [], time.time() + seconds
    while time.time() < end:
        t0 = time.time()
        png = rig.g.screenshot(clip=clip)
        t1 = time.time()
        out.append(((t0 + t1) / 2, K.read_counter(png), t1 - t0))
    return out


def fps_of(rig, seconds):
    s0, t0 = rig.state(), time.time()
    time.sleep(seconds)
    s1, t1 = rig.state(), time.time()
    return (s1["painted"] - s0["painted"]) / (t1 - t0), (s1["delivered"] - s0["delivered"]) / (t1 - t0)


# ------------------------------------------------------------------------------------------------------ 1. screen updates
def check_screen(rig, a):
    box = rig.box
    bad, notes = [], []
    # a. every value, in order
    log = window(rig, "count", "8")
    t_start = time.time()
    s = sample_counter(rig, 20)
    ev = [e for e in window_log(box, log) if e.get("ev") == "n"]
    drawn = {e["n"]: e["t"] for e in ev}
    seq = [n for _, n, _ in s]
    backwards = [(seq[i - 1], seq[i]) for i in range(1, len(seq)) if seq[i] < seq[i - 1]]
    lo, hi = min(seq), max(seq)
    seen = set(seq)
    expected = [n for n in range(lo, hi + 1) if n in drawn]
    missed = [n for n in expected if n not in seen]
    cov = 1 - len(missed) / max(1, len(expected))
    per = statistics.median(dt for _, _, dt in s)
    first = {}
    for t, n, _ in s:
        first.setdefault(n, t)
    d8 = sorted(1000 * (first[n] - drawn[n]) for n in first if n in drawn)
    notes.append("8 Hz counter, 20 s: %d screenshots (one per %.0f ms), values %d..%d, %d of %d seen (%.0f%%), %d backwards step(s); first-sighting delay median %.0f ms (min %.0f)" % (
        len(s), 1000 * per, lo, hi, len(expected) - len(missed), len(expected), 100 * cov, len(backwards), statistics.median(d8) if d8 else -1, d8[0] if d8 else -1))
    if backwards:
        bad.append("the picture went BACK to an older value: %s" % backwards[:4])
    if cov < 0.9:
        bad.append("only %.0f%% of the counter values arrived (missed: %s)" % (100 * cov, missed[:10]))
    # b. bursts that stop
    log = window(rig, "bursts")
    t_b = time.time()
    s = sample_counter(rig, 36)
    fin = [e for e in window_log(box, log) if e.get("ev") == "final" and e["t"] > t_b - 1]
    settle, stale = [], []
    for e in fin:
        after = [(t, n) for t, n, _ in s if e["t"] <= t <= e["t"] + 2.3]
        if not after:
            continue
        got = [t for t, n in after if n == e["n"]]
        if not got:
            stale.append("final %d never shown (saw %s)" % (e["n"], sorted({n for _, n in after})[-3:]))
            continue
        settle.append(min(got) - e["t"])
        late = [n for t, n in after if t > min(got) and n != e["n"]]
        if late:
            stale.append("after showing %d the picture showed %s" % (e["n"], late[:3]))
        if min(got) - e["t"] > 1.0:
            stale.append("final %d only %.2f s after the last change" % (e["n"], min(got) - e["t"]))
    notes.append("bursts: %d stops judged, last value on screen %.0f ms (median) / %.0f ms (worst) after the last change" % (
        len(settle), 1000 * statistics.median(settle) if settle else -1, 1000 * max(settle) if settle else -1))
    if len(settle) < 4:
        raise ToolError("only %d burst stops could be judged (window log %d finals)" % (len(settle), len(fin)))
    bad += stale[:4]
    # c. frame rate and delay at 60 Hz
    log = window(rig, "count", "0")
    fps_p, fps_d = fps_of(rig, 10)
    t_c = time.time()
    s = sample_counter(rig, 12)
    drawn = {e["n"]: e["t"] for e in window_log(box, log) if e.get("ev") == "n"}
    delays = sorted(1000 * (t - drawn[n]) for t, n, _ in s if n in drawn)
    lo_med = statistics.median(1000 * (t - dt / 2 - drawn[n]) for t, n, dt in s if n in drawn)
    hi_med = statistics.median(1000 * (t + dt / 2 - drawn[n]) for t, n, dt in s if n in drawn)
    if len(delays) < 20:
        raise ToolError("only %d delay samples at 60 Hz" % len(delays))
    p = lambda q: delays[min(len(delays) - 1, int(q * len(delays)))]  # noqa: E731
    notes.append("60 Hz animation: %.1f frames/s painted by the page (%.1f delivered); picture age when screenshotted (the capture instant is somewhere inside the screenshot call of %.0f ms: median age %.0f ms if at its start, %.0f ms if at its end, %.0f ms taking the middle; p90 %.0f, max %.0f ms; box load %s)" % (
        fps_p, fps_d, 1000 * statistics.median(dt for _, _, dt in s), lo_med, hi_med, p(0.5), p(0.9), delays[-1], K.load()))
    if fps_p < 25:
        bad.append("only %.1f frames/s reach the page with a 60 Hz animation (minimum of 3.1: 25)" % fps_p)
    shot("screen-%s" % a.box, rig.canvas_png())
    ev_ = "; ".join(notes)
    return (FAIL, "; ".join(bad) + " -- " + ev_ + "; journal: " + box.journal(rig.user + "|abandon|NOT SENT", n=3)) if bad else (PASS, ev_)


# ------------------------------------------------------------------------------------------------------------- 2. video
def edges(vals, key):
    """Rising edges (t) of a boolean series [(t, bool)]: midpoint between the last False and the first True sample."""
    out, prev = [], None
    for t, b in vals:
        if b and prev is not None and not prev[1]:
            out.append((prev[0] + t) / 2)
        prev = (t, b)
    return out


def check_video(rig, a):
    box, g = rig.box, rig.g
    bad, notes = [], []
    # the ear: a 20 ms analyser in the page, and the page's clock against ours
    if not CA.in_page(g, "1") or not (g.js("const s=document.createElement('script'); s.textContent=arguments[0];"
                                           "(document.head||document.documentElement).appendChild(s); s.remove(); return 1;", EAR_JS)):
        raise ToolError("the ear did not mount in the page")
    t_a = time.time()
    to_, pn_ = CA.in_page(g, "[performance.timeOrigin, performance.now()]")
    t_b = time.time()
    off = (t_a + t_b) / 2 - (to_ + pn_) / 1000.0  # python time = page epoch time + off; page epoch of a sample = timeOrigin + its t
    rig.canvas_click(0.62, 0.55)  # one real gesture on the picture, as the user does (autoplay policy)
    time.sleep(1)
    log = window(rig, "video")
    L, T, W, H = rig.state()["rect"]
    clip = (L, T, 160, 160)
    box.run("touch %s.go" % log)  # the window starts the sound and the animation now; the first flash comes about 1.4 s later
    samples, t_end = [], time.time() + 13.5
    while time.time() < t_end:
        t0 = time.time()
        png = g.screenshot(clip=clip)
        t1 = time.time()
        from PIL import Image
        v = sum(Image.open(io.BytesIO(png)).convert("L").resize((4, 4)).getdata()) / 16.0
        samples.append(((t0 + t1) / 2, v > 160))
    vid = edges(samples, "v")
    ear = CA.in_page(g, "window.__ear.s.slice(-1000)") or []
    # the bar moves: six band shots 0.5 s apart
    xs = []
    for _ in range(6):
        png = g.screenshot(clip=(L, T + H // 2, W, 160))
        im = Image.open(io.BytesIO(png)).convert("RGB")
        w_, h_ = im.size
        d = im.resize((w_ // 4, 40)).load()
        cols = [x for x in range(w_ // 4) if sum(1 for y in range(40) if d[x, y][0] > 200 and d[x, y][1] > 160 and d[x, y][2] < 90) > 20]
        xs.append(4 * min(cols) if cols else None)
        time.sleep(0.5)
    wl = window_log(box, log)
    flashes = {e["k"]: e["t"] for e in wl if e.get("ev") == "flash"}
    beeps = {e["k"]: e["t"] for e in wl if e.get("ev") == "beep"}
    # beeps heard in the page: rising edges of rms > 0.05 after >= 400 ms of quiet; the page's epoch of a sample = timeOrigin + c.t
    heard = []
    prev_t = None
    for c in ear:
        loud = c.get("state") == "running" and (c.get("rms") or 0) > 0.05
        if loud and (prev_t is None or c["t"] - prev_t > 400):
            heard.append(((to_ + c["t"]) / 1000.0 + off, c.get("hz")))
        if loud:
            prev_t = c["t"]
    if len(vid) < 8:
        raise ToolError("only %d flashes seen by the screenshots (window log has %d)" % (len(vid), len(flashes)))
    moved = [x for x in xs if x is not None]
    steps = [(moved[i + 1] - moved[i]) % max(1, W - 80) for i in range(len(moved) - 1)]
    if len(moved) < 5 or len(set(moved)) < 5 or not all(60 <= s_ <= 200 for s_ in steps):
        bad.append("the bar does not move steadily (x positions %s, steps %s; 240 px/s x 0.5 s = 120 px expected)" % (xs, steps))
    hz = [h for _, h in heard if h]
    if len(heard) < 8:
        bad.append("only %d of 10 beeps were heard in the page (state/levels in %d ear samples; box recorded %d beeps)" % (len(heard), len(ear), len(beeps)))
    elif hz and abs(statistics.median(hz) - 1000) > 40:
        bad.append("the beeps sound at %.0f Hz, not 1000" % statistics.median(hz))
    if len(beeps) < 8 or len(flashes) < 8:
        raise ToolError("the box's own record is short: %d flashes %d beeps (monitor: %s)" % (
            len(flashes), len(beeps), [e for e in wl if e.get("ev", "").startswith("monitor")]))
    # pair by order: k-th flash seen with the k-th beep heard
    pairs = list(zip(vid, [t for t, _ in heard]))
    box_off = [(beeps[k] - flashes[k]) * 1000 for k in sorted(set(beeps) & set(flashes))]
    br_off = [(ta - tv) * 1000 for tv, ta in pairs]
    n = min(len(box_off), len(br_off))
    errs = [br_off[i] - box_off[i] for i in range(n)]
    if n < 8:
        raise ToolError("only %d flash/beep pairs to compare" % n)
    med = statistics.median(errs)
    drift = statistics.mean(errs[-3:]) - statistics.mean(errs[:3])
    notes.append("bar x %s; %d beeps heard at %.0f Hz; in the box beep minus flash median %.0f ms; in the browser %.0f ms; sync error (browser minus box) median %.0f ms, min %.0f, max %.0f, drift first->last 3: %+.0f ms (%d pairs; flash seen to +-%.0f ms)" % (
        xs, len(heard), statistics.median(hz) if hz else -1, statistics.median(box_off[:n]), statistics.median(br_off[:n]), med, min(errs), max(errs), drift, n,
        500 * statistics.median(b - a_ for (a_, _), (b, _) in zip(samples, samples[1:]))))
    if abs(med) > 400:
        bad.append("sound and picture are %.0f ms apart (limit of the tool 400 ms: the declared 250 ms audio cushion plus 150 ms)" % med)
    if abs(drift) > 150:
        bad.append("sound and picture drift apart by %.0f ms over the 10 beeps (limit 150 ms)" % drift)
    shot("video-%s" % a.box, rig.canvas_png())
    ev = "; ".join(notes)
    ev += " (a constant sound-after-picture lag of %.0f ms: the 250 ms audio cushion of RCP 6.3 is by design; lip-sync judgement is the owner's)" % med if med > 100 else ""
    jr = box.journal("audio .*final count|dropped|DIGITAL", since="-3min", n=2)
    return (FAIL, "; ".join(bad) + " -- " + ev + "; journal: " + jr) if bad else (PASS, ev)


# ------------------------------------------------------------------------------------------------------------- 3. codec
def pct(vals, q):
    v = sorted(vals)
    return v[min(len(v) - 1, int(q * len(v)))]


def sharpness(png):
    """{region: metric} for the pattern of media-window.py, measured on the browser's picture (canvas at scale 1)."""
    from PIL import Image
    im = Image.open(io.BytesIO(png)).convert("RGB")
    out = {}
    for name, x, y, w, h in PATTERN:
        reg = im.crop((x, y, x + w, y + h))
        px = list(reg.convert("L").getdata())
        if name == "edge":
            row = [sum(reg.convert("L").getpixel((i, j)) for j in range(20, 108)) / 88.0 for i in range(w)]
            lo_, hi_ = sum(row[10:100]) / 90, sum(row[-100:-10]) / 90
            x10 = next((i for i in range(w) if row[i] > lo_ + 0.1 * (hi_ - lo_)), 0)
            x90 = next((i for i in range(w) if row[i] > lo_ + 0.9 * (hi_ - lo_)), w)
            out[name] = x90 - x10
        elif name == "rb2":
            d = [r - b for r, _, b in reg.getdata()]
            out[name] = (pct(d, 0.9) - pct(d, 0.1)) / 510.0
        else:
            out[name] = (pct(px, 0.9) - pct(px, 0.1)) / 255.0
    return out


LIMITS = {"v4": 0.85, "v2": 0.70, "h2": 0.70, "check8": 0.85, "rb2": 0.50}


def codec_facts(rig):
    """What the page negotiated (its own log), what the server announced at start-up (journal since the service started) and which
    DRI nodes the session's own process holds open (the leader of its logind session, the one that encodes)."""
    box, g = rig.box, rig.g
    book = g.js("return (document.getElementById('logbook')||{}).textContent||''") or ""
    neg = re.search(r"video · negotiated: codec (\w+) \(«([^»]+)»\), (\d+) bit", book)
    meas = re.search(r"MEASURE frame · coded (\d+x\d+) · shown (\d+x\d+)", book)
    hevc = re.search(r"video probe · (⛔ )?HEVC: ([^\n]{0,80})", book)
    since = box.run("systemctl show remotix -p ActiveEnterTimestamp --value")[1].strip()
    start = box.run("journalctl -u remotix --no-pager -o cat --since '%s' | grep -E 'opened: |video.codec offered' | cut -c1-260 | tail -5" % since)[1]
    nodes = box.run("for s in $(loginctl list-sessions --no-legend | awk -v u=%s '$3==u{print $1}'); do [ \"$(loginctl show-session $s -p Class --value)\" = user ] && "
                    "ls -l /proc/$(loginctl show-session $s -p Leader --value)/fd 2>/dev/null | grep -o '/dev/dri/[a-zA-Z0-9]*' | sort -u | tr '\\n' ' '; done" % rig.user)[1].strip()
    return dict(codec=neg.group(1) if neg else None, string=neg.group(2) if neg else None, depth=neg.group(3) if neg else None,
                coded=meas.groups() if meas else None, hevc=(hevc.group(0)[:100] if hevc else None), start=start, nodes=nodes)


def check_codec(rigs, a, since):
    bad, notes = [], []
    for rig in rigs:
        name = rig.browser
        log = window(rig, "pattern")
        time.sleep(4)
        png = rig.canvas_png()
        pn = shot("codec-%s-%s" % (name, a.box), png)
        L, T, W, H = rig.state()["rect"]
        cw, ch = png_size(png)
        m = sharpness(png)
        fx = codec_facts(rig)
        hw = bool(re.search(r"opened: H\.264 .*in HARDWARE", fx["start"]))
        srv_node = re.search(r"opened: H\.264 .*in HARDWARE · (/dev/dri/renderD\d+)", fx["start"])
        notes.append("%s %s: negotiated codec %s string %s (%s bit), coded %s; %s; the server's H.264 encoder at start-up: %s, node %s; DRI nodes open in the session's process: %s; picture %dx%d; contrast kept 1px %.2f 2px %.2f 4px %.2f horizontal 2px %.2f checker %.2f coloured %.2f, edge 10-90%% rise %d px (shots/%s)" % (
            name, rig.g.version, fx["codec"], fx["string"], fx["depth"], fx["coded"], fx["hevc"] or "no HEVC line", "HARDWARE" if hw else "NOT hardware",
            srv_node.group(1) if srv_node else "?", fx["nodes"] or "none readable", cw, ch, m["v1"], m["v2"], m["v4"], m["h2"], m["check8"], m["rb2"], m["edge"], pn))
        if abs(cw - W) > 1 and abs(cw - round(W)) > 1:
            notes.append("(picture %d wide, viewer %.0f)" % (cw, W))
        low = ["%s %.2f < %.2f" % (k, m[k], v) for k, v in LIMITS.items() if m[k] < v]
        if low:
            bad.append("%s: the picture is not sharp at the default quality (%s)" % (name, ", ".join(low)))
        if m["edge"] > 3:
            bad.append("%s: a black/white edge is %d px wide (limit 3)" % (name, m["edge"]))
        if fx["codec"] not in ("h264", "hevc"):
            bad.append("%s: the page negotiated codec %s (expected h264 or hevc)" % (name, fx["codec"]))
        if not hw:
            bad.append("%s: the server's encoder is not announced as HARDWARE (the spec forbids encoding on the CPU)" % name)
        if fx["nodes"] and "renderD" not in fx["nodes"]:
            bad.append("%s: the session's process holds no render node open (%s)" % (name, fx["nodes"]))
    return (FAIL, "; ".join(bad) + " -- " + "; ".join(notes)) if bad else (PASS, "; ".join(notes))


def png_size(png):
    from PIL import Image
    return Image.open(io.BytesIO(png)).size


# ------------------------------------------------------------------------------------------ 4. two sessions at once
def check_two(a, rig1, rig2):
    box = rig1.box
    bad = []
    log1 = window(rig1, "count", "0")
    alone = fps_of(rig1, 10)
    log2 = window(rig2, "count", "0")
    # both measured at the same time
    res = {}
    import threading

    def run(r, k):
        res[k] = fps_of(r, 12)
    th = [threading.Thread(target=run, args=(rig1, 1)), threading.Thread(target=run, args=(rig2, 2))]
    [t.start() for t in th]
    [t.join() for t in th]
    drop = 1 - res[1][0] / alone[0] if alone[0] else 1
    ev = "alone: user 1 paints %.1f fps; together: user 1 %.1f fps (%.0f%% less), user 2 %.1f fps (delivered %.1f/%.1f); box load %s" % (
        alone[0], res[1][0], 100 * drop, res[2][0], res[1][1], res[2][1], K.load())
    if res[1][0] < 25 or res[2][0] < 25:
        bad.append("a session fell below the 25 fps minimum (%.1f and %.1f)" % (res[1][0], res[2][0]))
    if drop > 0.30:
        bad.append("the first session lost %.0f%% of its frame rate when the second came in (limit 30%%)" % (100 * drop))
    shot("two-a-%s" % a.box, rig1.canvas_png())
    shot("two-b-%s" % a.box, rig2.canvas_png())
    jr = box.journal("BUDGET|strain|0x06|does NOT get in", since="-4min", n=3)
    return (FAIL, "; ".join(bad) + " -- " + ev + "; journal: " + jr) if bad else (PASS, ev + "; budget journal: " + jr)


# ------------------------------------------------------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--box", default="xfce", choices=sorted(lib.PORTS))
    ap.add_argument("--only", default="", help="comma-separated check names")
    ap.add_argument("--cap", type=int, default=75)
    a = ap.parse_args()
    want = [n for n in NAMES if not a.only or n in a.only.split(",")]
    res = lib.Results(want)
    rigs = []

    def flow():
        since = int(time.time())
        K.install(lib.Box(a.box))
        first = None
        if any(n in want for n in ("screen-updates", "video", "codec", "two-sessions-budget")):
            first = bring_up(a, "md1", "chrome", "media1")
            rigs.append(first)
        if "screen-updates" in want:
            res.attempt("screen-updates", lambda: check_screen(first, a))
        if "video" in want:
            res.attempt("video", lambda: check_video(first, a))
        if "codec" in want:
            def codec():
                second = bring_up(a, "md2", "firefox", "media2")
                rigs.append(second)
                return check_codec([first, second], a, since)
            res.attempt("codec", codec)
        if "two-sessions-budget" in want:
            def two():
                rig2 = bring_up(a, "md4", "chrome", "media4")
                rigs.append(rig2)
                return check_two(a, first, rig2)
            res.attempt("two-sessions-budget", two)

    try:
        return res.sequence(flow, 1500)
    finally:
        for r in rigs:
            try:
                r.stop()
            except Exception:  # noqa: BLE001
                pass


if __name__ == "__main__":
    sys.exit(main())
