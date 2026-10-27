#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
30-perf — THE SMALL PERFORMANCE BENCH (REMOTIX 1.5, step 1; PIANO.md)

    python3 30-perf.py --box xfce --browser chrome --steps 1,2,4,8 --minutes 5 --out DIR [--dry-run]  (see --help)

Run ON THE SERVER, as nicfio.  Per step N: N tenants, N browsers (one headless labwc each, on the CLIENT card),
the same light scene in every session (6 rectangles, fixed seed, + a 1 ms counter in F-003's cells).  One CSV
row per step, per metric min/mean/median/p90/max; the .txt report says how each is computed.
--box-card {intel,amd} (default intel) = the card the boxes are on (11-start.sh with REMOTIX_CARD=...); the clients go on the
other one unless --client-card says otherwise.  Which GPU columns mean what, per card of the BOXES:
  intel : gpu_render / gpu_video / gpu_videoenh = intel_gpu_top (Render/3D, Video, VideoEnhance engine busy %)
  amd   : gpu_render   = /sys/class/drm/cardN/device/gpu_busy_percent of the Radeon (whole GFX pipe, every ~2 s)
          gpu_video    = VCN encoder + decoder busy %, from the fdinfo of the processes (drm-engine-enc*/dec* delta ns
                         / wall ns, summed over the live clients of the card; may exceed 100 with several VCN instances;
                         a process that exits during the step loses its last interval: slight under-estimate)
          gpu_videoenh = empty (no such engine on the Radeon)
  client_gpu_busy (card of the CLIENTS): amd = gpu_busy_percent of the Radeon; intel = Render/3D busy % of the Intel
                         (intel_gpu_top; the Intel has no gpu_busy_percent).  Empty if neither applies.
Output names: intel keeps perf-<box>-<browser>-WxH.*; amd adds «-amd» (perf-<box>-<browser>-WxH-amd.*).
--scene {heavy,text} (default heavy = the scene above, the worst case: the whole 3K screen redrawn at 60 fps).
  text = a 1200x900 «window» of text scrolling at a constant speed (CSS transform, text repeated), the rest of the screen still
  and uniform; the 1 ms counter is the same (same cells, same place).  Names get «-text» after the card suffix
  (perf-<box>-<browser>-WxH[-amd]-text.*) and the csv has a last column «scene» (heavy | text).
Exit: 0 ok · 1 error · 2 CSV already in --out · 3 server not empty · 4 memory guard (< 6 GB)
"""
import argparse
import atexit
import base64
import contextlib
import csv
import io
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import types

os.environ.setdefault("REMOTIX_ON_SERVER", "1")      # before importing suite: local `sudo podman`
SUITE = os.environ.get("REMOTIX_SUITE") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "15-suite")
BOXES = ("gnome", "kde", "xfce", "lxqt")
MIN_AVAIL_KB = 6 * 1024 * 1024
SAMPLE_S, PHOTO_S = 5, 1
FIRST_IMG_S = 180        # max wait for the first readable image of a session (s)
KEEPALIVE_S = 240        # a real mouse move this often: REMOTIX detaches a session after 30 min without input (rcp.h §5.3)
                         #   and ends it 60 min later — the endurance run (27 Oct 2026) measured nothing after minute 30
SEED, N_RECTS, BOX_CARD, DRIVER = 1527, 6, "intel", {"intel": "i915", "amd": "amdgpu"}   # light scene; boxes on BOX_CARD
DELTA = {"chrome": [32, 129], "firefox": [0, 0]}       # outer - inner window size, calibrated live
SCENE = "heavy"                                      # --scene: heavy (6 rectangles, whole screen) | text (scrolling window)
S = F3 = None                                        # suite, 15-f003 (loaded by load())
CLEAN, PROFILES, _lock = [], [], threading.Lock()     # undo list; browser profiles WE created
STOP = threading.Event()         # memory stop: every measuring thread must end (set by guard())
MAIN_DONE = threading.Event()    # the main thread has recorded the stop and is leaving
STATE, OUT_LOCK = {}, threading.Lock()     # o / stem / lines / n / flags shared with guard() for the emergency write
RC_MEM = 4                       # exit code: stopped for lack of memory (the chain reads it); 1 = step failed, 2 = csv exists, 3 = server not empty
CLEAN_S = 90                     # max seconds for ONE clean-up action
# ⭐ 26 Oct 2026, the endurance and disturbed-network runs of 1.5 (PIANO-durata-rete):
#   REMOTIX_PERF_NETEM="loss 3%"  a netem on lo for the UDP of the box's port ONLY (both directions: a delay counts twice in
#                                 the RTT), so the local LLMs and the rest of the server are not disturbed; on before the
#                                 sessions open, off at every clean-up and at exit;
#   REMOTIX_PERF_SERIES=1         per step, <stem>-<n>u.series.json: per sample and per user the server's memory and open
#                                 files, and the painted counter every 5 s (the .csv keeps only the summaries).
NETEM = os.environ.get("REMOTIX_PERF_NETEM", "").strip()
SERIES = os.environ.get("REMOTIX_PERF_SERIES") == "1"


class MemoryStop(Exception):
    pass


def bounded(fn, secs):
    """Run fn() with a time limit: a stuck action is abandoned (daemon thread) so the next ones still run."""
    err = []

    def work():
        try:
            fn()
        except BaseException as e:               # noqa: BLE001
            err.append(e)
    t = threading.Thread(target=work, daemon=True)
    t.start()
    t.join(secs)
    if t.is_alive():
        print("   ⚠ clean-up: %s still running after %d s: abandoned, going on" % (getattr(fn, "__name__", fn), secs), flush=True)
    elif err:
        raise err[0]


def cleanup():
    """Every registered undo, whatever happens: signals ignored meanwhile (main thread), a failing undo
    (BaseException) or a closed terminal (SIGHUP) do not stop the next ones."""
    sigs = (signal.SIGINT, signal.SIGTERM, signal.SIGHUP) if threading.current_thread() is threading.main_thread() else ()
    old = [signal.signal(sg, signal.SIG_IGN) for sg in sigs]
    with _lock:
        STATE["cleaning"] = True
        while CLEAN:
            try:
                print("   cleaning up (%d left)" % len(CLEAN), flush=True)
                STATE["clean_t"] = time.time()           # progress mark for guard(): before and after each action
                bounded(CLEAN.pop(), CLEAN_S)
                STATE["clean_t"] = time.time()
            except BaseException as e:               # noqa: BLE001
                try:
                    print("   ⚠ clean-up: %r" % e, flush=True)
                except OSError:
                    pass
        STATE["cleaning"] = False
    for sg, h in zip(sigs, old):
        signal.signal(sg, h)


def kill_ours():       # TERM then KILL to the descendants of THIS process (browsers, labwc); rm the profiles WE created
    for sig in ("-15", "-9"):      # TERM first: labwc removes its socket, a KILLed one leaves it stale
        kids = {}
        for d in os.listdir("/proc"):
            try:
                kids.setdefault(int(open("/proc/%s/stat" % d).read().rsplit(")", 1)[1].split()[1]), []).append(int(d))
            except (OSError, ValueError, IndexError):
                pass
        todo = [os.getpid()]
        while todo:
            for c in kids.get(todo.pop(), []):
                todo.append(c)
                subprocess.run(["kill", sig, str(c)], capture_output=True)
        time.sleep(2)
    mon_sweep()        # GPU monitors last (found by tag even if their sudo is already dead): browsers and labwc first
    [shutil.rmtree(d, ignore_errors=True) for d in PROFILES]


def tc(*argv, check=True):
    r = subprocess.run(["sudo", "-S", "-p", "", "tc", *argv], input=S._sudo_password(), capture_output=True, text=True)
    if check and r.returncode != 0:
        raise RuntimeError("tc %s: %s" % (" ".join(argv), r.stderr.strip()[-200:]))
    return r


def netem_off():
    tc("qdisc", "del", "dev", "lo", "root", check=False)      # nothing there: harmless error


def netem_on(port):
    """prio with 4 bands, everything in band 4 (untouched); the box's UDP port, both directions, in band 1 with the netem."""
    netem_off()
    tc("qdisc", "add", "dev", "lo", "root", "handle", "1:", "prio", "bands", "4", "priomap", *["3"] * 16)
    tc("qdisc", "add", "dev", "lo", "parent", "1:1", "handle", "10:", "netem", *NETEM.split(), "limit", "100000")
    for d in ("dport", "sport"):
        tc("filter", "add", "dev", "lo", "parent", "1:", "protocol", "ip", "prio", "1", "u32",
           "match", "ip", "protocol", "17", "0xff", "match", "ip", d, str(port), "0xffff", "flowid", "1:1")
    print("   netem on lo, UDP port %d: %s" % (port, NETEM), flush=True)


def dump_series(stem, n, users, samples, recs):
    """The raw story of one step, compact: what the .csv averages away (a leak is a slope, not a mean)."""
    rows = []
    for b in samples:
        per = {}
        for pid, (u, comm, _t1, r1) in b["p"].items():
            if u in users:
                e = per.setdefault(u, [0.0, 0.0, 0])
                e[1] += r1 / 1048576.0
                if comm == "remotix":
                    e[0] += r1 / 1048576.0
                    e[2] += b.get("fd", {}).get(pid, 0)
        rows.append({"t": round(b["t"], 1),
                     "u": {u: [round(x, 1) if isinstance(x, float) else x for x in per.get(u, [0.0, 0.0, 0])] for u in users}})
    painted = [[[round(t, 1), c] for t, c in r["series"][::5]] for r in recs]
    with open("%s-%du.series.json" % (stem, n), "w") as f:
        json.dump({"users": users, "columns": ["srv_rss_mb", "ses_rss_mb", "srv_fd"], "samples": rows,
                   "painted": painted, "netem": NETEM}, f)


def meminfo_kb():
    return next(int(r.split()[1]) for r in open("/proc/meminfo") if r.startswith("MemAvailable:"))


def guard():
    """Memory watchdog. It does NOT clean up itself (it used to hold _lock while the measuring threads kept running):
    it sets STOP, the main thread stops the threads, cleans up (each action time-limited) and records the step as
    «fermato: memoria». Only if neither the main thread nor its clean-up advance for CLEAN_S+30 s does guard() write the outputs and exit."""
    while True:
        time.sleep(2)
        if meminfo_kb() < MIN_AVAIL_KB:
            STATE["mem_mb"] = meminfo_kb() // 1024
            print("⛔ MemAvailable under 6 GB: stop and clean up", flush=True)
            STOP.set()
            stop_t = time.time()
            while not MAIN_DONE.wait(5):                  # the clean-up may be slow but ADVANCING: wait while it advances
                if time.time() - max(stop_t, STATE.get("clean_t", 0)) > CLEAN_S + 30:
                    break
            else:
                return
            print("⛔ no progress for %d s after the memory stop: emergency write and exit" % (CLEAN_S + 30), flush=True)
            try:
                if "o" in STATE:
                    record_stop(STATE["o"], STATE["stem"], STATE["lines"], STATE.get("n"))
                    write_txt(STATE["o"], STATE["stem"], STATE["lines"], RC_MEM)
            except BaseException as e:               # noqa: BLE001
                print("   ⚠ emergency write: %r" % e, flush=True)
            try:
                if not STATE.get("cleaning"):                # a clean-up under way is not disturbed (podman exec of clear_out)
                    bounded(kill_ours, 60)
                bounded(cleanup, 300)
            finally:
                os._exit(RC_MEM)


def load():
    global S, F3
    sys.path.insert(0, SUITE)
    S = __import__("suite")
    F3 = S._load("f003", os.path.join(SUITE, "15-f003-the-screen-updates.py"))


def host_pgrep(pattern):
    mine, p = {os.getpid()}, os.getpid()             # not me, not my parents (ssh, bash -c)
    while p > 1:
        mine.add(p := int(open("/proc/%d/stat" % p).read().rsplit(")", 1)[1].split()[1]))
    r = subprocess.run(["pgrep", "-af", pattern], capture_output=True, text=True)
    return [x[:100] for x in r.stdout.splitlines() if int(x.split()[0]) not in mine]


def precheck():
    why = []
    for pat in ("15-round", r"giro[0-9a-z_-]*\.sh", r"^python3 [^ ]*30-perf\.py", "16-stress", "remotix-cr-|remotix-ff-"):
        why += ["bench in progress (%s): %s" % (pat, x) for x in host_pgrep(pat)[:3]]
    up = subprocess.run(["sudo", "-S", "-p", "", "podman", "ps", "--format", "{{.Names}}"], input=S._sudo_password(),
                        text=True, capture_output=True).stdout.split()
    on = [b for b in BOXES if "rete11-" + b in up]
    print("   boxes checked: %s · stopped (empty, not checked): %s" % (" ".join(on), " ".join(set(BOXES) - set(on))))
    for b in on:
        c, t = S.C20V.Box(b).inside("getent passwd | cut -d: -f1 | grep -E '^c[0-9]+b?u[0-9]+$'; "
                                    "pgrep -a -f '[f]irefox-esr|[s]ervitore[.]py' | cut -c1-90; true", 60)
        why += ["box %s: %s" % (b, x) for x in ([t] if c is None else t.splitlines()) if x.strip()]
    if meminfo_kb() < MIN_AVAIL_KB + 2 * 1024 * 1024:
        why.append("MemAvailable only %d MB" % (meminfo_kb() // 1024))
    return why


def render_node(card):
    return next("/dev/dri/" + d for d in sorted(os.listdir("/sys/class/drm")) if d.startswith("renderD") and
                os.path.basename(os.path.realpath("/sys/class/drm/%s/device/driver" % d)) == DRIVER[card])


def start_compositor(R):
    sockets = lambda: {x for x in os.listdir(R) if re.match(r"^wayland-[0-9]+$", x)}   # noqa: E731
    before = sockets()
    env = {k: v for k, v in os.environ.items() if k not in ("WAYLAND_DISPLAY", "DISPLAY")}
    env.update(WLR_BACKENDS="headless", WLR_LIBINPUT_NO_DEVICES="1", XDG_RUNTIME_DIR=R,
               WLR_RENDER_DRM_DEVICE=os.environ["PERF_CLIENT_NODE"])
    p = subprocess.Popen(["labwc"], env=env, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.STDOUT, start_new_session=True)
    CLEAN.append(lambda: (p.terminate(), p.wait(10)))      # registered before the sessions: runs after
    for _ in range(40):
        time.sleep(0.25)
        if sockets() - before:
            break
    assert sockets() - before, "labwc did not open a socket"
    e = dict(env, WAYLAND_DISPLAY=sorted(sockets() - before)[0])
    randr = lambda *a: subprocess.run(["wlr-randr", *a], env=e, capture_output=True, text=True).stdout  # noqa: E731
    for _ in range(3):
        time.sleep(0.5)
        randr("--output", randr().split()[0], "--custom-mode", "3840x2160")
        if re.search(r"3840x2160 px.*current", randr()):
            return e["WAYLAND_DISPLAY"]
    raise RuntimeError("the compositor did not take 3840x2160")


TEXT_JS = r"""
var W0=innerWidth,H0=innerHeight;
document.body.style.cssText='margin:0;background:#000;overflow:hidden';
function rng(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
var r=rng(@SEED@),LH=28,NL=48,SPEED=120,words='server remote desktop frame encoder window session screen latency browser stream canvas pixel codec kernel buffer packet client render texture cursor'.split(' ');
var box=document.createElement('div'),inner=document.createElement('div');
box.style.cssText='position:fixed;left:40px;top:40px;width:1200px;height:min(900px,calc(60vh - 40px));overflow:hidden;background:#f4f4f0';
inner.style.cssText='will-change:transform;font:18px/'+LH+'px sans-serif;color:#111;white-space:nowrap;padding-left:16px';
var html='';
for(var j=0;j<2;j++)for(var i=0;i<NL;i++){var rr=rng(@SEED@+i),l=[];for(var k=0;k<14;k++)l.push(words[Math.floor(rr()*words.length)]);html+='<div style="height:'+LH+'px">'+l.join(' ')+'</div>'}
inner.innerHTML=html;box.appendChild(inner);document.body.appendChild(box);
var st=document.createElement('style');
st.textContent='@keyframes sc{from{transform:translateY(0)}to{transform:translateY(-'+(LH*NL)+'px)}}';
document.head.appendChild(st);
inner.style.animation='sc '+(LH*NL/SPEED)+'s linear infinite';
var C=document.createElement('canvas'),X=C.getContext('2d');
C.style.cssText='position:fixed;left:0;top:'+(@Y0@*H0)+'px';document.body.appendChild(C);
function draw(){
 var W=innerWidth,H=innerHeight,CH=Math.round(@CH@*H);
 if(C.width!==W||C.height!==CH){C.width=W;C.height=CH;C.style.top=(@Y0@*H)+'px'}X.fillStyle='#000';X.fillRect(0,0,W,CH);
 var n=Date.now()%@MODULE@,b=[1,0],p=0;
 for(var k=@BIT@-1;k>=0;k--){var v=(n>>k)&1;b.push(v);p^=v}b.push(p);
 for(var i=0;i<b.length;i++){X.fillStyle=b[i]?'#fff':'#000';X.fillRect((@X0@+i*@STEP@)*W,0,@CW@*W,CH)}}
setInterval(draw,16);
"""


def scene_page():
    js = TEXT_JS if SCENE == "text" else r"""
var C=document.createElement('canvas'),X=C.getContext('2d'),R=[],t0=performance.now();
document.body.style.cssText='margin:0;background:#000;overflow:hidden';C.style.cssText='position:fixed;left:0;top:0';document.body.appendChild(C);
function rng(a){return function(){a|=0;a=a+0x6D2B79F5|0;var t=Math.imul(a^a>>>15,1|a);t=t+Math.imul(t^t>>>7,61|t)^t;return((t^t>>>14)>>>0)/4294967296}}
var r=rng(@SEED@);
for(var i=0;i<@NR@;i++)R.push({w:80+r()*220,h:80+r()*160,x:r(),y:r(),vx:(r()*2-1)*900,vy:(r()*2-1)*600,c:'hsl('+Math.floor(r()*360)+',90%,55%)'});
function bounce(p,v,t,m){m=Math.max(m,1);var L=2*m,q=((p*m+v*t)%L+L)%L;return q>m?L-q:q}
function draw(){
 var W=innerWidth,H=innerHeight,t=(performance.now()-t0)/1000;
 if(C.width!==W||C.height!==H){C.width=W;C.height=H}X.fillStyle='#000';X.fillRect(0,0,W,H);
 R.forEach(function(q){X.fillStyle=q.c;X.fillRect(bounce(q.x,q.vx,t,W-q.w),bounce(q.y,q.vy,t,.6*H-q.h),q.w,q.h)});
 var n=Date.now()%@MODULE@,b=[1,0],p=0;
 for(var k=@BIT@-1;k>=0;k--){var v=(n>>k)&1;b.push(v);p^=v}b.push(p);
 for(var i=0;i<b.length;i++){X.fillStyle=b[i]?'#fff':'#000';X.fillRect((@X0@+i*@STEP@)*W,@Y0@*H,@CW@*W,@CH@*H)}}
setInterval(draw,16);
"""
    for k, v in (("SEED", SEED), ("NR", N_RECTS), ("MODULE", F3.MODULE),
                 ("BIT", F3.BIT), ("X0", F3.CELL_X0), ("STEP", F3.CELL_STEP), ("Y0", F3.CELL_Y0),
                 ("CW", F3.CELL_W), ("CH", F3.CELL_H)):
        js = js.replace("@%s@" % k, str(v))
    return "<!doctype html><meta charset=utf-8><title>REMOTIX perf</title><body><script>%s</script>" % js


def start_scene(s):
    b = lambda t: base64.b64encode(t.encode()).decode()          # noqa: E731
    return s.sc.inside(
        "set -e; h=/home/%(c)s; mkdir -p $h/.perf-p; echo %(pg)s | base64 -d > $h/perf.html; "
        "echo %(pf)s | base64 -d > $h/.perf-p/user.js; chown -R %(c)s: $h/.perf-p $h/perf.html; "
        "set +e; u=$(id -u %(c)s); d=$(ls /run/user/$u 2>/dev/null | grep -E '^wayland-[0-9]+$' "
        "| head -1); [ -n \"$d\" ] || { echo 'no wayland socket'; exit 2; }; "
        "setsid runuser -u %(c)s -- env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$d "
        "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$u/bus MOZ_ENABLE_WAYLAND=1 "
        "XDG_SESSION_TYPE=wayland HOME=/home/%(c)s firefox-esr --no-remote --new-instance "
        "--kiosk --profile $h/.perf-p file://$h/perf.html < /dev/null > $h/.perf-ff.log 2>&1 & "
        "echo started" % {"c": s.chi, "pg": b(scene_page()), "pf": b(S.C21.PREFERENCES)}, 60)


def make_session_class(size):
    class PS(S.Session):
        def turn_on_browser(self):
            W, H = size
            old = list(S.VERI.WINDOW)
            try:
                for attempt in range(3):
                    dx, dy = DELTA[self.o.browser]
                    if self.o.browser == "chrome":
                        S.VERI.WINDOW[:] = [W + dx, H + dy]
                        self.o.width = 0
                    else:
                        self.o.width, self.o.height = W + dx, H + dy
                    super().turn_on_browser()
                    iw, ih = self.g.js("return [innerWidth, innerHeight]")
                    if (iw, ih) == (W, H) or attempt == 2:
                        return
                    DELTA[self.o.browser] = [dx + W - iw, dy + H - ih]
                    self.turn_off_browser()
            except BaseException:
                self.turn_off_browser()
                raise
            finally:
                S.VERI.WINDOW[:] = old
    return PS


FUTURE_TOL_MS = 100       # a counter «drawn in the future» by less than this is clock/timing jitter, not an age


def age_ms(n, t):
    # ms since the scene drew counter value n (1 ms steps, 12 bits: wraps every 4.096 s), seen at epoch-ms t.
    # Range [-FUTURE_TOL_MS, MODULE - FUTURE_TOL_MS): an age beyond 4096 ms cannot be told from a younger one.
    # (Until 23 Oct 2026 the range was [-2048, 2048): every true age between 2048 and 4096 ms came out as age - 4096,
    #  i.e. about -2000 ms, and was averaged in with the good ones.)
    k = (int(t) - n) % F3.MODULE
    return k - (F3.MODULE if k >= F3.MODULE - FUTURE_TOL_MS else 0) + (t - int(t))


def photo_delay(s, rec=None):
    # age_ms at the middle of the capture; Chrome photographs only the counter strip, Firefox the canvas
    from PIL import Image
    t0 = time.time() * 1000.0
    if hasattr(s.g, "cdp"):
        r = s.g.js("const b=document.getElementById('viewer').getBoundingClientRect();"
                   "return [b.left,b.top,b.width,b.height];")
        shot = s.g.cdp.call("Page.captureScreenshot", format="png", clip={
            "x": r[0], "y": r[1] + F3.CELL_Y0 * r[3], "width": r[2], "height": F3.CELL_H * r[3], "scale": 1})
        png, rect = base64.b64decode(shot["data"]), [0, -F3.CELL_Y0 * r[3], r[2] - 1, (1 - F3.CELL_Y0) * r[3] - 1]
    else:
        png, rect = S.C21.full_photo(s.g), None
    tm = (t0 + time.time() * 1000.0) / 2
    if not png:
        return None
    im = Image.open(io.BytesIO(png)).convert("RGB")
    n, _m = F3.read_counter(im, rect or [0, 0, im.size[0] - 1, im.size[1] - 1])
    if rec is not None:
        rec["bytes"] += len(png)
        rec["cost"].append(time.time() * 1000.0 - t0)
    return None if n is None else age_ms(n, tm)


def client_loop(s, t_end, rec):
    nxt, bad = time.time(), 0
    # only the long runs (the endurance): the 5-minute A/B stay identical to the bench their 1.0 references were measured with
    nudge, side = (time.time() + KEEPALIVE_S) if t_end - time.time() > 25 * 60 else float("inf"), 0
    while time.time() < t_end and not STOP.is_set():
        t = time.time()
        if s.g is None:                              # browser already closed by the clean-up: nothing to measure
            break
        try:
            rec["series"].append((t, s.g.js("return REMOTIX.viewer.counts.painted;")))
            if t >= nxt:
                nxt = t + PHOTO_S
                rec["delays"].append(photo_delay(s, rec))
            if t >= nudge:                           # the user is there: a small real move in the middle of the canvas
                nudge, side = t + KEEPALIVE_S, side ^ 1
                geo = s.geometry() or {}
                if not geo.get("tl"):
                    raise RuntimeError("keep-alive: the canvas geometry is not readable")
                s.g.move_to(*S.C21.desktop_to_glass(geo, geo["tl"] * (0.49 + 0.02 * side), geo["ta"] * 0.5))
                rec["nudges"] += 1
            bad = 0
        except Exception as e:                       # noqa: BLE001
            rec["errors"] += 1
            bad += 1
            if bad <= 3 or bad % 10 == 0:
                print("   ⚠ %s: %s%s" % (s.chi, str(e)[:100], " (%d in a row)" % bad if bad > 1 else ""), flush=True)
            STOP.wait(min(10.0, 0.5 * bad))          # repeated error: pause, growing, never spin
        STOP.wait(max(0.0, t + 1.0 - time.time()))
    if rec["nudges"]:
        print("   %s: %d keep-alive mouse moves (one every %d s)" % (s.chi, rec["nudges"], KEEPALIVE_S), flush=True)


SAMPLER = r"""
import os, json, time, pwd
pg = os.sysconf("SC_PAGE_SIZE"); out = {}
for p in os.listdir("/proc"):
    try:
        st = open("/proc/%s/stat" % p).read(); r = st.rindex(")"); f = st[r + 2:].split()
        out[p] = [pwd.getpwuid(os.stat("/proc/" + p).st_uid).pw_name, st[st.index("(") + 1:r], int(f[11]) + int(f[12]), int(f[21]) * pg]
    except Exception: pass
cpu = [int(l.split()[1]) for l in open("/sys/fs/cgroup/cpu.stat") if l.startswith("usage_usec")][0]
# memory.current = anonymous + page cache + kernel (slab, stacks, page tables) + tmpfs.  The CACHE depends on what the box read
# before this run (it is not freed without pressure), so it is recorded apart: memory.stat of the same cgroup, same instant.
ms = {}
try:
    for l in open("/sys/fs/cgroup/memory.stat"):
        k, v = l.split()
        if k in ("anon", "file", "shmem", "kernel", "kernel_stack", "pagetables", "slab", "slab_reclaimable", "slab_unreclaimable", "file_mapped"):
            ms[k] = int(v)
except Exception:
    ms = {}      # unreadable or in an unexpected shape: no memory.stat for this sample, box_mem is still recorded
fd = {}          # open files of the server processes (comm remotix): a leak shows here before it shows in memory
for p, v in out.items():
    if v[1] == "remotix":
        try:
            fd[p] = len(os.listdir("/proc/%s/fd" % p))
        except Exception: pass
print(json.dumps({"t": time.time(), "p": out, "fd": fd, "cpu_us": cpu, "mem": int(open("/sys/fs/cgroup/memory.current").read()), "ms": ms}))
"""


def igt_start(card="intel"):
    f = tempfile.TemporaryFile("w+")
    tag, argv = tagged(["intel_gpu_top", "-J", "-s", "2000", "-d", "drm:" + render_node(card)])
    p = subprocess.Popen(["sudo", "-S", "-p", "", *argv], stdin=subprocess.PIPE, stdout=f,
                         stderr=subprocess.DEVNULL, text=True)
    p.tag = tag
    CLEAN.append(lambda: igt_kill(p))                  # registered BEFORE anything else can fail: no orphan monitor
    p.stdin.write(S._sudo_password()), p.stdin.flush()
    time.sleep(3)
    assert p.poll() is None, "intel_gpu_top did not start (sudo? PMU?)"
    return p, f


MON_TAGS = []      # argv[0] tags of the root monitors (intel_gpu_top, AMDMON) WE started


def tagged(argv):
    """(tag, argv') : argv' runs argv with argv[0] = a tag unique to this process and start (bash `exec -a`), so the monitor
    can be found whatever the chain sudo -> (sudo monitor) -> command and whenever it is asked to stop (mon_kill)."""
    if not MON_TAGS:
        atexit.register(mon_sweep)
    tag = "perf-mon-%d-%d" % (os.getpid(), len(MON_TAGS))
    MON_TAGS.append(tag)
    return tag, ["bash", "-c", 'exec -a "$0" "$@"', tag, *argv]


def mon_alive(tag):
    return subprocess.run(["pgrep", "-f", "^%s( |$)" % tag], capture_output=True).returncode == 0


def mon_kill(tag, secs=5):
    """Signal (INT, then KILL) only the processes whose command line STARTS with our tag; wait (bounded) until none is left."""
    for sig in ("-INT", "-KILL"):
        if not mon_alive(tag):
            return
        try:
            pw = S._sudo_password()
        except Exception:                              # noqa: BLE001  (suite not loaded / no password file): try without
            pw = ""
        try:
            subprocess.run(["sudo", "-S", "-p", "", "pkill", sig, "-f", "^%s( |$)" % tag], input=pw,
                           text=True, capture_output=True, timeout=30)
        except (OSError, subprocess.TimeoutExpired):
            pass
        t_end = time.time() + secs
        while mon_alive(tag) and time.time() < t_end:
            time.sleep(0.2)
    if mon_alive(tag):
        print("   ⚠ monitor %s still alive after INT and KILL" % tag, flush=True)


def mon_sweep():
    for tag in MON_TAGS:
        mon_kill(tag, 3)


def igt_kill(p):
    mon_kill(p.tag)
    try:
        p.wait(5)                                      # the sudo wrapper ends with its command
    except subprocess.TimeoutExpired:
        p.kill()


def igt_stop(h):
    igt_kill(h[0])
    h[0].wait(20)
    text = (h[1].seek(0), h[1].read())[1]
    g = {k: [float(x) for x in re.findall(r'"%s": \{\s*"busy": ([0-9.]+)' % k, text)[1:]]
         for k in ("Render/3D", "Video", "VideoEnhance")}
    if not g["Render/3D"]:
        raise RuntimeError("intel_gpu_top gave no samples: the GPU columns would be empty, step FAILED")
    return g


AMDMON = r"""
import glob, json, os, re, sys, time
import signal
signal.signal(signal.SIGINT, signal.SIG_DFL)      # started in background, SIGINT arrives ignored: igt_kill sends INT
node = os.environ["PERF_AMD_NODE"]                     # /dev/dri/renderDxxx of the Radeon
pci = os.path.basename(os.path.realpath("/sys/class/drm/%s/device" % os.path.basename(node)))
busy = "/sys/class/drm/%s/device/gpu_busy_percent" % os.path.basename(node)
prev, t0 = {}, time.time()
while True:
    cur, vid = {}, 0.0
    for f in glob.glob("/proc/[0-9]*/fdinfo/*"):
        try:
            if not os.readlink(f.replace("fdinfo", "fd")).startswith("/dev/dri/"):
                continue
            t = open(f).read()
        except OSError:
            continue
        if "drm-driver:\tamdgpu" not in t or ("drm-pdev:\t" + pci) not in t:
            continue
        cid = re.search(r"drm-client-id:\s*(\d+)", t)
        ns = sum(int(x) for x in re.findall(r"^drm-engine-(?:enc|dec)\w*:\s*(\d+) ns", t, re.M))
        if cid:
            cur[cid.group(1)] = ns     # client-id is unique per open file: an fd inherited by several processes counts once
    now = time.time()
    d = sum(max(0, ns - prev[k]) for k, ns in cur.items() if k in prev)
    print(json.dumps({"busy": int(open(busy).read()), "vcn": round(100.0 * d / 1e9 / (now - t0), 2)}), flush=True)
    prev, t0 = cur, now
    time.sleep(2)
"""


def amd_start():
    f = tempfile.TemporaryFile("w+")
    tag, argv = tagged(["python3", "-c", AMDMON])
    p = subprocess.Popen(["sudo", "-S", "-p", "", "env", "PERF_AMD_NODE=" + render_node("amd"), *argv],
                         stdin=subprocess.PIPE, stdout=f, stderr=subprocess.DEVNULL, text=True)
    p.tag = tag
    CLEAN.append(lambda: igt_kill(p))                  # registered BEFORE anything else can fail
    p.stdin.write(S._sudo_password()), p.stdin.flush()
    time.sleep(4)
    assert p.poll() is None, "the Radeon monitor did not start (sudo? gpu_busy_percent?)"
    return p, f


def amd_stop(h):
    igt_kill(h[0])                                    # SIGINT to the python child of `sudo env`
    h[0].wait(20)
    rows = [json.loads(l) for l in (h[1].seek(0), h[1].read())[1].splitlines() if l.startswith("{")][1:]
    if not rows:
        raise RuntimeError("the Radeon monitor gave no samples: the GPU columns would be empty, step FAILED")
    return {"Render/3D": [float(r["busy"]) for r in rows], "Video": [r["vcn"] for r in rows], "VideoEnhance": []}


def gpu_start(o):
    """Monitors of the GPU columns: the BOXES' card (box) and, if different and Intel, the CLIENTS' (cli)."""
    h = {"box": igt_start("intel") if o.box_card == "intel" else amd_start(), "cli": None}
    if o.client_card == "intel" and o.box_card != "intel":
        h["cli"] = igt_start("intel")
    return h


def gpu_stop(o, h):
    g = (igt_stop if o.box_card == "intel" else amd_stop)(h["box"])
    g["client"] = None                                 # None = keep gpu_busy_percent of the client card (amd)
    if o.client_card == "intel":                       # the Intel has no gpu_busy_percent: its Render/3D engine
        g["client"] = (igt_stop(h["cli"]) if h["cli"] else g)["Render/3D"]
    return g


def host_sample():
    cb = os.environ["PERF_CLIENT_NODE"].replace("/dev/dri", "/sys/class/drm") + "/device/gpu_busy_percent"
    cpu = [int(x) for x in open("/proc/stat").readline().split()[1:]]
    return {"cpu": [sum(cpu), cpu[3] + cpu[4]], "avail_kb": meminfo_kb(),
            "cbusy": int(open(cb).read()) if os.path.exists(cb) else None,
            "lo": int(next(l for l in open("/proc/net/dev") if l.strip().startswith("lo:")).split()[9])}


def sampler(box, out, done):
    bad = 0
    while not done.is_set() and not STOP.is_set():
        t0 = time.time()
        c, t = box.inside("python3 /tmp/perf-sample.py", 30)
        try:
            out.append(dict(json.loads(t.splitlines()[-1]), h=host_sample()))
            bad = 0
        except (ValueError, IndexError):
            bad += 1
            if bad <= 3 or bad % 10 == 0:
                print("   ⚠ sample lost (%d in a row): %s" % (bad, (t or "")[-100:]), flush=True)
            done.wait(min(10.0, 0.5 * bad))              # repeated error: growing pause, never spin
        done.wait(max(0.0, SAMPLE_S - (time.time() - t0)))


def mm(xs):
    xs = sorted(x for x in xs if x is not None)
    return [round(x, 1) for x in (xs[0], sum(xs) / len(xs), xs[len(xs) // 2], xs[int(0.9 * (len(xs) - 1))],
                                  xs[-1])] if xs else [""] * 5


def server_stats(samples, users, ovh):
    """{name: [values]}: CPU in % of one core, memory in MB, one value per (interval, session)."""
    v = {k: [] for k in ("srv_cpu", "ses_cpu", "srv_rss", "ses_rss", "box_cpu", "box_mem", "box_work", "box_cache",
                         "host_cpu", "host_avail", "client_gpu_busy", "banda_stima_kbps")}
    for a, b in zip(samples, samples[1:]):
        dt = b["t"] - a["t"]
        cpu, rss = {}, {}
        for pid, (u, comm, t1, r1) in b["p"].items():
            for k in [k for k in ("ses", "srv") if u in users and (k == "ses" or comm == "remotix")]:
                rss[k, u] = rss.get((k, u), 0) + r1 / 1048576.0
                if pid in a["p"]:
                    cpu[k, u] = cpu.get((k, u), 0) + (t1 - a["p"][pid][2]) / dt     # ticks/s = % of a core
        for k in ("srv", "ses"):
            v[k + "_cpu"] += [cpu.get((k, u), 0.0) for u in users]
            v[k + "_rss"] += [rss.get((k, u), 0.0) for u in users]
        v["box_cpu"].append((b["cpu_us"] - a["cpu_us"]) / 1e4 / dt)
        v["box_mem"].append(b["mem"] / 1048576.0)
        # the MEMORY THE LOAD NEEDS, without the file cache: anon + tmpfs (shmem) + kernel memory that is not reclaimable
        # (kernel = stacks + page tables + slab; the reclaimable slab is a cache like the page cache).  `ms` absent (old
        # sampler / old kernel): empty, so the comparison falls back to box_mem and SAYS so.
        ms = b.get("ms") or {}
        if "anon" in ms:
            kern = ms.get("kernel", ms.get("kernel_stack", 0) + ms.get("pagetables", 0) + ms.get("slab", 0))
            work = ms["anon"] + ms.get("shmem", 0) + kern - ms.get("slab_reclaimable", 0)
            v["box_work"].append(work / 1048576.0)
            v["box_cache"].append(max(0, ms.get("file", 0) - ms.get("shmem", 0) + ms.get("slab_reclaimable", 0)) / 1048576.0)
        ha, hb = a["h"], b["h"]
        dtot = hb["cpu"][0] - ha["cpu"][0]
        v["host_cpu"].append(100.0 * (dtot - hb["cpu"][1] + ha["cpu"][1]) / dtot if dtot else None)
        v["host_avail"].append(hb["avail_kb"] / 1024.0)
        v["client_gpu_busy"].append(hb["cbusy"])
        v["banda_stima_kbps"].append(max(0.0, (hb["lo"] - ha["lo"]) * 8 / 1000.0 / dt / len(users) - ovh))
    return v


def run_step(o, n):
    box, PS = S.C20V.Box(o.box), make_session_class(o.size)
    sessions, samples, done = [], [], threading.Event()
    stack = contextlib.ExitStack()
    try:
        if "ok" not in (box.inside("echo %s | base64 -d > /tmp/perf-sample.py; echo ok"
                                   % base64.b64encode(SAMPLER.encode()).decode(), 30)[1] or ""):
            raise RuntimeError("the sampler does not install in the box")
        if NETEM:
            CLEAN.append(netem_off)
            netem_on(S.PORTS[o.box])
        comps = [start_compositor(os.environ["XDG_RUNTIME_DIR"]) for _ in range(n)]
        CLEAN.append(kill_ours)
        CLEAN.append(stack.close)
        for i in range(n):
            if STOP.is_set():
                raise MemoryStop()
            os.environ["WAYLAND_DISPLAY"] = comps[i]
            oi = types.SimpleNamespace(**dict(vars(o), base_port=o.base_port + 10 * i))
            s = PS(oi, "9%02d" % i, types.SimpleNamespace(version=""))
            CLEAN.append(lambda s=s: s.sc.clear_out(s.chi))     # the tenant also if its start fails halfway
            sessions.append(stack.enter_context(s))
            ok, m = s.enter()
            if not ok:
                raise RuntimeError("session %d (%s): %s" % (i, s.chi, m))
            c, t = start_scene(s)
            if c != 0:
                raise RuntimeError("session %d: the scene does not start: %s" % (i, t[-150:]))
            print("   session %d/%d up: %s" % (i + 1, n, s.chi), flush=True)
        first, retried = [], 0                       # seconds to the first readable image, per session; retries done
        for s in sessions:                           # the scene is seen, with a readable counter
            t_wait, geo = time.time(), {}
            for attempt in (1, 2):                   # one NEW attempt (scene restarted) before declaring the step failed
                for _ in range(FIRST_IMG_S // 2):
                    if STOP.is_set():
                        raise MemoryStop()
                    geo = s.geometry() or {}
                    if photo_delay(s) is not None:
                        break
                    S.C21.wake(s.g, geo)             # GNOME is born in the overview (scene = a thumbnail): a real ESC
                    time.sleep(2)
                else:
                    open(os.path.join(o.out, "unreadable-%s-try%d.png" % (s.chi, attempt)), "wb").write(S.C21.full_photo(s.g) or b"")
                    _c, lg = s.sc.inside("tail -n 6 /home/%s/.perf-ff.log; pgrep -u %s -c firefox-esr" % (s.chi, s.chi), 30)
                    if attempt == 2:
                        raise RuntimeError("%s: the scene's counter is not readable after %d s and a new attempt (canvas %sx%s): %s"
                                           % (s.chi, FIRST_IMG_S, geo.get("tl"), geo.get("ta"), lg[-300:]))
                    print("   ⚠ %s: scene not readable after %d s: new attempt" % (s.chi, FIRST_IMG_S), flush=True)
                    retried += 1
                    s.sc.inside("pkill -u %s firefox-esr; for i in $(seq 10); do pgrep -u %s firefox-esr >/dev/null || break; sleep 1; done; "
                                "pkill -KILL -u %s firefox-esr; sleep 1; true" % (s.chi, s.chi, s.chi), 30)   # the profile must be free
                    c, t = start_scene(s)
                    if c != 0:
                        raise RuntimeError("session %s: the scene does not restart: %s" % (s.chi, t[-150:]))
                    continue
                break
            first.append(round(time.time() - t_wait, 1))
        o.step_info = [("first_img_s_max", max(first)), ("scene_retries", retried)]
        canvas = [geo.get("tl"), geo.get("ta")]
        STOP.wait(o.warmup)
        igt = gpu_start(o)
        t_end = time.time() + o.minutes * 60
        smp = threading.Thread(target=sampler, args=(box, samples, done), daemon=True)
        recs = [{"series": [], "delays": [], "errors": 0, "bytes": 0, "cost": [], "nudges": 0} for _ in sessions]
        th = [threading.Thread(target=client_loop, args=(s, t_end, r), daemon=True) for s, r in zip(sessions, recs)]
        for t in [smp] + th:
            t.start()
        stop_at = None
        for t in th:
            while t.is_alive():
                t.join(1)
                if STOP.is_set():                    # the threads see STOP; do not wait for ever for a stuck one
                    stop_at = stop_at or time.time()
                    if time.time() - stop_at > 60:
                        break
        done.set()
        smp.join(40)
        if STOP.is_set():
            raise MemoryStop()
        return n, canvas, [s.chi for s in sessions], samples, recs, gpu_stop(o, igt)
    finally:
        done.set()
        STATE["clean_t"] = time.time()                # guard: the clean-up starts now
        if STOP.is_set():
            bounded(kill_ours, 60)                   # memory stop, wherever it caught us: browsers and labwc first, then the rest
        cleanup()


AGE_WRAP_WARN_MS = 3500      # an age this close to the counter's wrap (4096) may hide an older one
PHOTO_SLOW_MS = 2000         # a photo this slow cannot be placed in time: the age is uncertain by about half of it
STAT_NAMES = ("srv_cpu", "ses_cpu", "srv_rss", "ses_rss", "box_cpu", "box_mem", "box_work", "box_cache", "host_cpu", "host_avail",
              "gpu_render", "gpu_video", "gpu_videoenh", "client_gpu_busy", "fps", "age_ms", "photo_ms", "banda_stima_kbps")
COLS = (["users", "box", "browser", "window", "canvas", "minutes", "samples"]
        + ["%s_%s" % (n, k) for n in STAT_NAMES for k in ("min", "mean", "median", "p90", "max")]
        + ["age_photos", "age_unreadable", "age_future", "age_over_half", "age_unreliable", "client_errors",
           "first_img_s_max", "scene_retries", "client_limited", "status", "scene"])


def client_limited(m):
    """1 if the CLIENTS' card is (nearly) saturated: client_gpu_busy mean > 90 or p90 > 95 (m = [min, mean, median, p90, max])."""
    return int(m[1] != "" and (m[1] > 90 or m[3] > 95))


def step_row(o, n, canvas, users, samples, recs, igt):
    # bytes: the loopback counter of the host (client and server share it) minus our own photos (+1/3 base64)
    v = server_stats(samples, users, sum(r["bytes"] for r in recs) * 1.34 * 8 / 1000.0
                     / (samples[-1]["t"] - samples[0]["t"]) / len(users))
    dl = [d for r in recs for d in r["delays"]]
    ages = [max(0.0, d) for d in dl if d is not None]      # -FUTURE_TOL_MS <= d < 0: jitter, reported as 0 and kept (age_future counts them)
    fps = [(r["series"][i + 5][1] - r["series"][i][1]) / (r["series"][i + 5][0] - r["series"][i][0])
           for r in recs for i in range(0, len(r["series"]) - 5, 5)]                    # 5 s windows
    if igt["client"] is not None:                      # clients on the Intel: its engine, not an absent sysfs file
        v["client_gpu_busy"] = igt["client"]
    v.update(fps=fps, age_ms=ages, gpu_render=igt["Render/3D"], gpu_video=igt["Video"], gpu_videoenh=igt["VideoEnhance"], photo_ms=[x for r in recs for x in r["cost"]])
    row = [("users", n), ("box", o.box), ("browser", o.browser), ("window", "%dx%d" % o.size),
           ("canvas", "%sx%s" % tuple(canvas)), ("minutes", o.minutes), ("samples", len(samples))]
    for name in STAT_NAMES:
        row += [("%s_%s" % (name, k), x) for k, x in zip(("min", "mean", "median", "p90", "max"), mm(v[name]))]
    unreliable = int((bool(ages) and max(ages) >= AGE_WRAP_WARN_MS) or max(v["photo_ms"] or [0]) > PHOTO_SLOW_MS)
    return row + [("age_photos", len(ages)), ("age_unreadable", dl.count(None)),
                  ("age_future", sum(1 for d in dl if d is not None and d < 0)),
                  ("age_over_half", sum(1 for d in ages if d > F3.MODULE / 2)), ("age_unreliable", unreliable),
                  ("client_errors", sum(r["errors"] for r in recs))] + list(o.step_info) + [
                  ("client_limited", client_limited(mm(v["client_gpu_busy"]))), ("status", "measured"), ("scene", SCENE)]


GPU_DOC = {"intel": "gpu_* = intel_gpu_top engine busy % (Render = scene + desktop, Video = encoding)",
           "amd": "gpu_render = Radeon gpu_busy_percent (whole GFX pipe), gpu_video = VCN encoder+decoder busy % "
                  "(from the processes' fdinfo, summed), gpu_videoenh = empty"}
CLI_DOC = {"amd": "client card gpu_busy_percent (Radeon, empty if none)",
           "intel": "client card = Intel Render/3D engine busy % (intel_gpu_top)"}


def record_stop(o, stem, lines, n):
    """The memory stop as a step of its own: «fermato: memoria» in the .txt line and in the .csv (status column)."""
    with OUT_LOCK:
        if STATE.get("stop_done"):
            return
        STATE["stop_done"] = True
        mb = STATE.get("mem_mb", meminfo_kb() // 1024)
        lines.append("%s user(s): FERMATO: MEMORIA (MemAvailable %d MB, under %d MB): step NOT measured, no data from it"
                     % (n, mb, MIN_AVAIL_KB // 1024))
        row = {"users": n, "box": o.box, "browser": o.browser, "window": "%dx%d" % o.size, "minutes": o.minutes,
               "host_avail_min": mb, "status": "fermato: memoria", "scene": SCENE}
        names = COLS
        if os.path.exists(stem + ".csv"):
            names = open(stem + ".csv").readline().rstrip("\r\n").split(",")
        with open(stem + ".csv", "a", newline="") as f:
            w = csv.writer(f)
            if names is COLS:
                w.writerow(names)
            w.writerow([row.get(c, "") for c in names])        # host_avail_min = MemAvailable (MB) at the stop


def write_txt(o, stem, lines, code):
    with OUT_LOCK:
        done, STATE["txt_done"] = STATE.get("txt_done"), True
    if done:
        return
    with open(stem + ".txt", "w") as f:
        f.write("30-perf %s · %s · %s · window %dx%d · %.1f min/step + %d s warm-up · BOXES ON %s · client card %s%s\n%s\n\n"
                "srv = tenant's `remotix` processes, ses = all its processes, box_* = box cgroup, CPU %% of a core "
                "(/proc, every %d s); %s; client_gpu_busy = %s; fps = frames painted (5 s "
                "windows); age_ms = 1 ms counter of the scene, photo every ~%s s; banda_stima = ESTIMATE: host "
                "loopback bytes / users - photos; first_img_s_max = seconds the slowest session took to show its first "
                "readable image (max wait %d s), scene_retries = sessions whose scene had to be restarted once; client_limited = 1 (LIMITATO DAI CLIENT) "
                "when client_gpu_busy mean > 90 or p90 > 95: the CLIENTS' card is saturated, so that step describes the clients "
                "and not the server.\n"
                "age_ms: 12-bit counter, 1 ms steps, wraps every 4096 ms: ages are in [-100, 3996) ms and an age above 4096 ms cannot be told from a younger one; "
                "age_future = readings drawn \"after\" the photo (jitter, counted as 0), age_over_half = ages above 2048 ms, age_unreliable = 1 when an age is >= 3500 ms "
                "or a photo took > 2000 ms (the age is then NOT to be trusted); photo_ms = time of each photo. Before 23 Oct 2026 ages above 2048 ms came out negative.\n"
                "status = measured | fermato: memoria (MemAvailable under 6 GB: the step was cut, no data); exit code 0 ok, 1 a step FAILED, 2 csv exists, 3 server not empty, 4 = stopped for memory.\n"
                "The number of users the box sustains refers to THIS scene "
                "(scene %s, N_RECTS=%d); the scene weighs on Render.\n"
                % (time.strftime("%Y-%m-%d %H:%M:%SZ", time.gmtime()), o.box, o.browser, o.size[0], o.size[1],
                   o.minutes, o.warmup, o.box_card.upper(), o.client_card,
                   " · Firefox client decodes in SOFTWARE (VA-API off)" if o.browser == "firefox" and o.client_card == "amd" else "",
                   "\n".join(lines), SAMPLE_S, GPU_DOC[o.box_card],
                   CLI_DOC[o.client_card], PHOTO_S, FIRST_IMG_S, SCENE, N_RECTS))



def main():
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--box", choices=BOXES, required=True)
    a.add_argument("--browser", choices=("chrome", "firefox"), required=True)
    a.add_argument("--steps", default="1,2,4,8")
    a.add_argument("--minutes", type=float, default=5)
    a.add_argument("--warmup", type=int, default=30)
    a.add_argument("--size", default="2896x1620")      # canvas comes out 2880x1616 (16-px steps)
    a.add_argument("--box-card", choices=DRIVER, default="intel", help="card the boxes are on (default intel)")
    a.add_argument("--client-card", choices=DRIVER, default=None, help="default: the other card than --box-card")
    a.add_argument("--scene", choices=("heavy", "text"), default="heavy", dest="scene_kind",
                   help="heavy (default): 6 rectangles, whole screen at 60 fps; text: scrolling 1200x900 text window")
    a.add_argument("--out", required=True)
    a.add_argument("--base-port", type=int, default=3300)
    a.add_argument("--dry-run", action="store_true")
    o = a.parse_args()
    global BOX_CARD, SCENE
    BOX_CARD, SCENE = o.box_card, o.scene_kind
    o.client_card = o.client_card or ("amd" if o.box_card == "intel" else "intel")
    o.steps = [int(x) for x in o.steps.split(",")]
    o.size = tuple(int(x) for x in o.size.split("x"))
    os.environ["PERF_CLIENT_NODE"] = render_node(o.client_card)
    if o.dry_run:
        print("PLAN", vars(o), "client node", os.environ["PERF_CLIENT_NODE"], "box card", o.box_card, "scene", o.scene_kind, "scene rects", N_RECTS)
        return 0
    stem = os.path.join(o.out, "perf-%s-%s-%dx%d%s" % (o.box, o.browser, o.size[0], o.size[1],
                                                                 ("" if o.box_card == "intel" else "-" + o.box_card) + ("" if o.scene_kind == "heavy" else "-" + o.scene_kind)))
    if os.path.exists(stem + ".csv"):
        print("⛔ %s.csv already exists: use another --out" % stem)
        return 2
    print("⚠ client card = box card: the GPU columns include the clients") if o.client_card == o.box_card else None
    load()
    why = precheck()
    if why:
        print("⛔ the server is not empty:\n  " + "\n  ".join(why))
        return 3
    os.makedirs(o.out, exist_ok=True)
    os.environ.update(XDG_RUNTIME_DIR="/run/user/%d" % os.getuid(), MOZ_ENABLE_WAYLAND="1",
                      REMOTIX_NESTED_SCREEN="1", REMOTIX_CHROME_OPTIONS="--ozone-platform=wayland "
                      "--disable-backgrounding-occluded-windows --disable-renderer-backgrounding "
                      "--disable-background-timer-throttling --render-node-override=" + os.environ["PERF_CLIENT_NODE"],
                      MOZ_DRM_DEVICE=os.environ["PERF_CLIENT_NODE"])
    if o.browser == "firefox" and o.client_card == "amd":     # Firefox client on the Radeon: VA-API fails with no fallback
        # (EncodingError, page 0x09): force software decoding (libavcodec), the same road as the Intel client
        pf = json.loads(os.environ.get("REMOTIX_FF_PREFS") or "{}")
        pf.update({"media.hardware-video-decoding.enabled": False, "media.ffmpeg.vaapi.enabled": False})
        os.environ["REMOTIX_FF_PREFS"] = json.dumps(pf)           # read by 07-b46-marionette.py for the client profile
    o.host, o.port, o.visible, o.cap_s, o.evidence, o.fault = "192.168.0.2", 0, True, 45, "", False
    o.url = "https://%s:%d/" % (o.host, S.PORTS[o.box])
    o.scene, o.continuity_s, o.log_cmd, o.leave_running, o.save, o.width, o.height = "alive", 8, "", False, "", *o.size
    for sg in (signal.SIGTERM, signal.SIGHUP):
        signal.signal(sg, lambda *_: sys.exit(130))
    mkdtemp = tempfile.mkdtemp                       # the drivers' profiles are recorded: only those are removed
    tempfile.mkdtemp = lambda *a, **k: PROFILES.append(mkdtemp(*a, **k)) or PROFILES[-1]
    lines = []
    STATE.update(o=o, stem=stem, lines=lines, n=None)
    threading.Thread(target=guard, daemon=True).start()
    code = 0
    for n in o.steps:
        STATE["n"] = n
        print("══ step %d user(s) ══" % n, flush=True)
        if STOP.is_set():
            record_stop(o, stem, lines, n)
            code = RC_MEM
            break
        try:
            res = run_step(o, n)
            row = step_row(o, *res)
        except MemoryStop:
            record_stop(o, stem, lines, n)
            code = RC_MEM
            break
        except Exception as e:                       # noqa: BLE001
            if STOP.is_set():                        # the failure is a consequence of the memory stop
                record_stop(o, stem, lines, n)
                code = RC_MEM
                break
            lines.append("%d user(s): FAILED: %s" % (n, e))
            code = 1
            break
        new = not os.path.exists(stem + ".csv")
        with open(stem + ".csv", "a", newline="") as f:
            (w := csv.writer(f)).writerows(([[k for k, _x in row]] if new else []) + [[x for _k, x in row]])
        if SERIES:                                   # after the .csv: a failing dump must not cost the step's row
            try:
                dump_series(stem, n, res[2], res[3], res[4])
            except Exception as e:                   # noqa: BLE001
                print("   ⚠ series not written: %r" % e, flush=True)
        d = dict(row)
        lines.append("%d user(s): " % n + " · ".join("%s=%s" % (k, x) for k, x in row[7:] if k.endswith(("_mean", "_p90", "photos", "unreadable", "first_img_s_max", "scene_retries", "client_limited", "age_future", "age_over_half", "age_unreliable")))
                     + ("  ⚠ LIMITED BY THE CLIENTS (LIMITATO DAI CLIENT)" if dict(row)["client_limited"] else ""))
    if NETEM:
        netem_off()
        lines.append("netem (lo, UDP port %d, both directions): %s" % (S.PORTS[o.box], NETEM))
    write_txt(o, stem, lines, code)
    MAIN_DONE.set()
    print("\n".join(lines) + "\n⭐ %s.csv / .txt · code %d" % (stem, code))
    return code


if __name__ == "__main__":
    sys.exit(main())
