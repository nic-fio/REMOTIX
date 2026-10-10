#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
07-b64-scena — ONE RUN OF R26, on the test machine, AS ROOT.

⛔ What it measures, and why looking at thread policies is not enough:
   R26 says that PipeWire's `data-loop`, without `SCHED_FIFO`, «collects the
   samples at normal priority while in the same process the video encoder
   takes a core».  ⚠ The thread's policy is half of the sentence:
   the other half is **how long that thread waited for the CPU**, and it is in
   `/proc/<pid>/task/<tid>/schedstat`, second field — nanoseconds spent in
   the run queue (`run_delay`).  ⇒ Here both are read, every second.

⛔ And the verdict is NOT given by this file: it sets up the scene and collects.
   The judgement belongs to `07-b64-orecchio.py`, which LISTENS to the samples (rule (a)
   of `07-b43`: we listen, we do not count blocks).

⭐ THE INDEPENDENT REFEREE: inside the session a `pw-record` also runs on the
   monitor of the same sink.  If a gap appears in both captures, it
   was born **before** REMOTIX (in the player or in the graph); if it appears only in
   ours, it is ours.  ⚠ It is not a perfect referee — `pw-record` has its own
   `data-loop`, subject to the same defect — but it separates the two biggest
   suspects, and without it they cannot be separated at all.

Usage (as root, on the test machine):
    python3 07-b64-scena.py lap --label_name 1-fermo --load no  --rt come-sta
    python3 07-b64-scena.py lap --label_name 2-lavora --load si --rt come-sta
    python3 07-b64-scena.py lap --label_name 3-lavora-rt --load si --rt si
    python3 07-b64-scena.py snapshot        # only the threads, no scene
"""
import argparse, json, os, signal, subprocess, sys, time

ACCOUNT = os.environ.get("ACCOUNT", "provar7")
UID_B = int(os.environ.get("UID_B", "1018"))
PORT = int(os.environ.get("PORT", "7801"))
ADDR = os.environ.get("ADDR", "192.168.0.2")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/07-r")
TREE = os.environ.get("TREE", "/media/REMOTIX/src/07-r-src")
INSIDE_TREE = os.environ.get("INSIDE_TREE", "/srv/src/07-r-src")
INSIDE_WORK = os.environ.get("INSIDE_WORK", "/srv/remotix/tmp/07-r")
SINK = os.environ.get("SINK", "remotix")
SCENE_BIN = os.environ.get("SCENE_BIN", "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena")

POLICY = {0: "normale", 1: "FIFO", 2: "RR", 3: "batch", 5: "idle", 6: "deadline"}
HZ_TICK = os.sysconf("SC_CLK_TCK")


# ── the session's environment, built from scratch (CODER.md §4.5) ──────────
def as_user(cmd, **kw):
    base = ["setpriv", "--reuid=%d" % UID_B, "--regid=%d" % UID_B, "--init-groups",
            "env", "-i",
            "HOME=/home/%s" % ACCOUNT, "USER=%s" % ACCOUNT, "LANG=C.UTF-8",
            "PATH=/usr/local/bin:/usr/bin:/bin",
            "XDG_RUNTIME_DIR=/run/user/%d" % UID_B,
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus" % UID_B,
            "XDG_CURRENT_DESKTOP=GNOME", "XDG_SESSION_DESKTOP=gnome",
            "XDG_SESSION_TYPE=wayland"]
    return base + cmd


def execute(cmd, ceiling=20):
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=ceiling)
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 124, "", "⛔ timed out after %d s" % ceiling


# ── /proc: the policy, the priority and THE WAIT IN THE QUEUE ──────────────
def thread_stat(pid, tid):
    try:
        d = open("/proc/%d/task/%d/stat" % (pid, tid)).read()
    except Exception:
        return None
    a = d.index("("); b = d.rindex(")")
    label_name = d[a + 1:b]
    c = d[b + 2:].split()
    utime, stime = int(c[11]), int(c[12])
    rtprio, policy = int(c[37]), int(c[38])
    # ⭐ schedstat: [time on the CPU ns, WAIT IN THE QUEUE ns, how many timeslices]
    wait = executed = 0
    try:
        s = open("/proc/%d/task/%d/schedstat" % (pid, tid)).read().split()
        wait, executed = int(s[1]), int(s[2])
    except Exception:
        pass
    return {"label_name": label_name, "tid": tid, "cpu_tick": utime + stime,
            "rtprio": rtprio, "policy": policy,
            "policy_v": POLICY.get(policy, str(policy)),
            "attesa_ns": wait, "how_many": executed}


def rt_limit(pid):
    try:
        for r in open("/proc/%d/limits" % pid):
            if "realtime priority" in r.lower():
                return r.split()[3]
    except Exception:
        pass
    return "?"


def interesting_processes():
    """The session's child, the user's PipeWire daemons, the player and
       the referee.  ⛔ And the SERVER, which is the one carrying the rlimit."""
    outside = []
    for d in os.listdir("/proc"):
        if not d.isdigit():
            continue
        p = int(d)
        try:
            uid = os.stat("/proc/%d" % p).st_uid
            comm = open("/proc/%d/comm" % p).read().strip()
            cmd = open("/proc/%d/cmdline" % p).read().replace("\0", " ")
        except Exception:
            continue
        my = (uid == UID_B) or ("remotix" in comm and (str(PORT) in cmd or ACCOUNT in cmd))
        if my:
            outside.append((p, uid, comm, cmd[:120]))
    return outside


def snapshot():
    """Who has real time and who does not — the snapshot of R26, in full."""
    r = []
    for p, uid, comm, cmd in sorted(interesting_processes()):
        v = {"pid": p, "uid": uid, "comm": comm, "cmdline": cmd,
             "rlimit_rtprio": rt_limit(p), "thread": []}
        try:
            tids = sorted(int(t) for t in os.listdir("/proc/%d/task" % p))
        except Exception:
            tids = []
        for t in tids:
            s = thread_stat(p, t)
            if s:
                v["thread"].append(s)
        r.append(v)
    return r


# ── the PipeWire graph, read INSIDE the session ────────────────────────────
def graph():
    rc, out, err = execute(as_user(["pw-dump"]), 25)
    if rc != 0 or not out.strip():
        return {"failure": "pw-dump produced nothing (rc %d): %s" % (rc, err[:200])}
    try:
        d = json.loads(out)
    except Exception as e:
        return {"failure": "pw-dump unreadable: %s" % e}
    r = {"sink_id": None, "legami_in_ingresso": 0, "sink_presenti": []}
    for o in d:
        info = o.get("info") or {}
        p = info.get("props") or {}
        if p.get("media.class") == "Audio/Sink":
            r["sink_presenti"].append(p.get("node.name"))
        if p.get("node.name") == SINK and p.get("media.class") == "Audio/Sink":
            r["sink_id"] = o["id"]
            r["monitor_channel_volumes"] = p.get("monitor.channel-volumes")
    for o in d:
        if str(o.get("type", "")).endswith("Link"):
            p = (o.get("info") or {}).get("props") or {}
            if r["sink_id"] is not None and p.get("link.input.node") == r["sink_id"]:
                r["legami_in_ingresso"] += 1
    return r


# ── the tone, written here so the amplitude is KNOWN ───────────────────────
def tone(hz, seconds, amplitude=0.5):
    import math, struct, wave
    f = os.path.join(LAV, "tone-%d.wav" % hz)
    if os.path.exists(f) and os.path.getsize(f) >= 48000 * seconds * 4:
        return f
    w = wave.open(f, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000)
    d = bytearray()
    for n in range(48000 * seconds):
        v = int(amplitude * math.sin(2 * math.pi * hz * n / 48000) * 32767)
        d += struct.pack("<hh", v, v)
    w.writeframes(bytes(d)); w.close()
    os.chmod(f, 0o644)
    return f


# ── the load: the desktop that WORKS ───────────────────────────────────────
def captured_monitor():
    """⛔ The monitor name is NOT written by hand: MY product's log
       says it.  A scene started «somewhere» does not load the stage."""
    try:
        body_text = open(os.path.join(LAV, "registro.log"), errors="replace").read()
    except Exception:
        return None
    # ⛔ The form is the one of `04-b32-terreno.sh`, and it is not reinvented: the
    #    log writes `monitor «Meta-0»`.  ⚠ The first draft looked for any
    #    word with a dash and a number and found nothing: the
    #    «the desktop works» run ran WITHOUT the scene, and said so only in
    #    a JSON field nobody looked at.
    import re
    m = [x for x in re.findall(r"monitor \u00ab([^\u00bb]*)\u00bb", body_text) if x]
    return m[-1] if m else None


def expected_monitor(cap_s=25.0):
    """⛔ THE MONITOR NAME IS WAITED FOR — and the first draft did not.

       `[M]` 21 August 2026: the log writes «monitor «Meta-0»» ~2.9 s after
       the session opens, and M3 (the tone playing) comes earlier.  ⇒ Whoever
       reads the log at M3 does not find the name, the scene does not start, and the run
       is called «the desktop works» all the same.  ⚠ In yesterday's runs the defect
       could NOT be seen because the log still contained the line of the previous
       session: that is, it worked for a wrong reason, and that is the worst
       form — a bench that stops working when you clean it."""
    fine = time.time() + cap_s
    while time.time() < fine:
        u = captured_monitor()
        if u:
            return u
        time.sleep(0.5)
    return None


def load_turn_on(how_many):
    """⛔ Two loads, and they are two different things:
         · the SCENE, which makes the child's capture and encoder work —
           it is the one R26 names;
         · the BURNERS, which take the CPU away from everyone — it is the condition in which
           a priority is good for something.
       ⚠ We declare which of the two started: if the scene does not start, the run
         stays valid but is NO longer «the desktop works», and it is something else."""
    state = {"scene": None, "burners": 0, "scena_perche_no": None}
    usc = expected_monitor()
    if os.access(SCENE_BIN, os.X_OK) and usc:
        log = open(os.path.join(LAV, "scena.log"), "ab")
        p = subprocess.Popen(
            as_user(["env", "WAYLAND_DISPLAY=wayland-0", SCENE_BIN,
                         "--out_dir", usc, "--motion", "bar",
                         "--shm", "/07-b64-scena", "--lap", "b64"]),
            stdout=log, stderr=log)
        time.sleep(1.0)
        alive = subprocess.run(["pgrep", "-u", str(UID_B), "-f", "04-b30-scena --out_dir"],
                              capture_output=True).stdout.decode().split()
        state["scene"] = usc if alive else None
        if not alive:
            state["scena_perche_no"] = "the scene started and died at once (see scena.log)"
        state["_p"] = p
    else:
        state["scena_perche_no"] = ("the binary %s is not executable" % SCENE_BIN
                                    if not os.access(SCENE_BIN, os.X_OK)
                                    else "I do not know which monitor my child captures")
    burn = []
    for _ in range(how_many):
        burn.append(subprocess.Popen(
            as_user(["python3", "-c", "\nwhile True: pass\n"]),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    state["burners"] = len(burn)
    state["_bruc"] = burn
    return state


def load_turn_off(state):
    for p in state.get("_bruc", []):
        try: p.kill()
        except Exception: pass
    subprocess.run(["pkill", "-u", str(UID_B), "-f", "while True: pass"],
                   capture_output=True)
    subprocess.run(["pkill", "-u", str(UID_B), "-f", "04-b30-scena"], capture_output=True)


# ── ⭐⭐ THE REAL BOTTLENECK OF R26: A SINGLE CORE ──────────────────────────
#
# R26 says, word for word: «its `data-loop` stays at normal priority
# **while in the same process the video encoder takes a core for
# tens of milliseconds**».  ⛔ On twenty cores that sentence has no way to
# come true: the audio thread always finds a free core, and indeed at load 25
# its wait in the queue is 6 us over a timeslice of 5.33 ms.
#
# ⇒ To measure R26 one has to **build** the condition it describes: the
#   whole audio path (the child with its encoder, the PipeWire
#   daemons, the player and the referee) is squeezed onto **a single core**.
#
# ⭐ And it has a second merit, which is not secondary: nine other benches work on
#   the machine.  A load that saturates twenty cores would distort their
#   time measurements; this one takes **one**.
def pin_to_one_core(cpu):
    done_ones = []
    for v in snapshot():
        if v["comm"] in ("remotix", "pipewire", "pipewire-pulse", "wireplumber",
                         "pw-play", "pw-record", "04-b30-scena") and v["uid"] != 0:
            rc, _, err = execute(["taskset", "-acp", str(cpu), str(v["pid"])], 5)
            done_ones.append("%s[%d] rc=%d" % (v["comm"], v["pid"], rc))
    return done_ones


def widen(all_cpus):
    done_ones = []
    for v in snapshot():
        if v["uid"] != 0:
            execute(["taskset", "-acp", all_cpus, str(v["pid"])], 5)
            done_ones.append(v["comm"])
    return done_ones


# ── real time, given by hand — ⭐ it is the A/B of R26 ─────────────────────
def rt_apply(prio):
    """⛔ We do not «configure PipeWire»: the policy of the LIVE threads is moved with
       `chrt`, so that between the two runs ONE thing only changes.  ⚠ And we record who
       was moved and who refused."""
    done_ones, failed = [], []
    for v in snapshot():
        for t in v["thread"]:
            if "data-loop" in t["label_name"] or "pw-data" in t["label_name"]:
                rc, _, err = execute(["chrt", "-f", "-p", str(prio), str(t["tid"])], 5)
                (done_ones if rc == 0 else failed).append(
                    "%s/%s[%d]%s" % (v["comm"], t["label_name"], t["tid"],
                                     "" if rc == 0 else " ⛔ " + err.strip()[:60]))
    return {"promossi": done_ones, "failed": failed, "prio": prio}


# ⛔⛔ AND REAL TIME, ON THIS MACHINE, CANNOT BE HAD AT ALL.
#
#     `[M]` 21 August 2026: `chrt -f 10 /bin/true` **fails as root** in
#     any cgroup that is not the root one, and succeeds in the root.  The
#     kernel (7.0, NIC-OS) has `CONFIG_RT_GROUP_SCHED` with unified cgroup v2:
#     every process systemd puts in a slice or a scope — that is every
#     process on the machine — cannot obtain `SCHED_FIFO`, and the refusal
#     comes BEFORE the kernel looks at `RLIMIT_RTPRIO`.
#
# So the A/B of R26 is done with the LEVER THAT WORKS, niceness (`nice`):
#   it is the other half of what the unit grants (`LimitNICE=-11`), and nobody
#   uses it — `[M]` all the threads of the audio path sit at `nice 0`.
def nice_apply(level):
    done_ones, failed = [], []
    for v in snapshot():
        if v["uid"] == 0:
            continue
        for t in v["thread"]:
            if ("data-loop" in t["label_name"] or v["comm"] in ("pw-play", "pw-record")
                    or (v["comm"] in ("pipewire", "pipewire-pulse", "wireplumber")
                        and t["tid"] == v["pid"])):
                rc, _, err = execute(["renice", "-n", str(level), "-p", str(t["tid"])], 5)
                (done_ones if rc == 0 else failed).append(
                    "%s/%s[%d]%s" % (v["comm"], t["label_name"], t["tid"],
                                     "" if rc == 0 else " NO " + err.strip()[:50]))
    return {"level": level, "done_ones": done_ones, "failed": failed}


def rt_restore():
    done_ones = []
    for v in snapshot():
        for t in v["thread"]:
            if t["policy"] != 0 and ("data-loop" in t["label_name"] or "pw-data" in t["label_name"]):
                rc, _, _ = execute(["chrt", "-o", "-p", "0", str(t["tid"])], 5)
                done_ones.append("%s[%d] rc=%d" % (t["label_name"], t["tid"], rc))
    return done_ones


# ═══════════════════════════════════════════════════════════════════════════
def lap(a):
    outcomes = {"label_name": a.label_name, "port": PORT, "username": ACCOUNT,
             "ora_macchina": time.strftime("%Y-%m-%d %H:%M:%S"),
             "carico_chiesto": a.load, "rt_chiesto": a.rt}
    base = os.path.join(LAV, a.label_name)
    # ⚠ What is left from the previous run is EMPTIED (LEZIONI.md §2.3-quinquies).
    for e in (".jsonl", ".signal_v", ".txt", ".rif.wav", ".esito.json"):
        try: os.remove(base + e)
        except Exception: pass

    outcomes["carico_prima"] = open("/proc/loadavg").read().split()[:3]

    # ── the client starts first: it is the one that opens the session ──────
    # ⭐ `--codec opus` serves the mandate on datagrams: Opus is what runs
    #    in real sessions, and it costs 1/13 of PCM's bandwidth.  ⚠ The ear
    #    judge cannot decode it — with Opus the TRANSPORT is counted,
    #    and we declare it instead of pretending to have listened.
    cmd = ("python3 -u %s/banchi/01-b3-cliente.py --address %s --port %d "
           "--username %s --password-file %s/password --audio-codec %s "
           "--audio-write %s/%s.jsonl --signal_v %s/%s.signal_v "
           "%s --stays %d"
           % (INSIDE_TREE, ADDR, PORT, ACCOUNT, INSIDE_WORK, a.codec,
              INSIDE_WORK, a.label_name, INSIDE_WORK, a.label_name,
              # ⛔ WITHOUT `--fit` THE VIDEO DOES NOT START, and the run would measure
              #    the audio alone calling it «audio against video».  §6.6: the
              #    server sends frames after the `FIT_CANVAS`, which the page
              #    sends by itself and the test client does not.
              ("--fit %s --video-write %s/%s.265" % (a.canvas_size, INSIDE_WORK, a.label_name)
               if a.video == "si" else ""),
              a.seconds))
    fcli = open(base + ".txt", "wb")
    cli = subprocess.Popen(["bash", "/media/REMOTIX/enter.sh", "--root", cmd],
                           stdout=fcli, stderr=fcli)
    t0 = time.time()

    # M1 · the client opened the session (a file written and closed is a fact)
    while time.time() - t0 < 90 and not os.path.exists(base + ".signal_v"):
        if cli.poll() is not None:
            break
        time.sleep(0.2)
    outcomes["M1_sessione_aperta"] = os.path.exists(base + ".signal_v")
    outcomes["M1_dopo_s"] = round(time.time() - t0, 2)
    if not outcomes["M1_sessione_aperta"]:
        outcomes["failure"] = ("⛔ M1 did not arrive: the client did not open the "
                           "session.  ⚠ It is NOT «the audio does not arrive»: it is «the "
                           "scene was not set up»")
        try: cli.kill()
        except Exception: pass
        cli.wait()
        fcli.close()
        outcomes["cliente_coda"] = open(base + ".txt", errors="replace").read()[-1500:]
        json.dump(outcomes, open(base + ".esito.json", "w"), ensure_ascii=False, indent=1)
        print(json.dumps(outcomes, ensure_ascii=False, indent=1))
        return 2

    # M2 · the sink exists in the graph
    g = {}
    for _ in range(60):
        g = graph()
        if g.get("sink_id"):
            break
        time.sleep(0.4)
    outcomes["M2_grafo"] = g

    # ── the independent referee: a second capture of the same monitor ──────
    ref = None
    # ⛔ The referee's folder is ITS OWN: `pw-record` runs as the session's user,
    #    and on $LAV (root 755) it cannot create anything.  ⚠ The symptom was
    #    "Permission denied" inside a stderr file nobody looked at, and the
    #    run was left without a referee without saying so.
    dir_ref = os.path.join(LAV, "rif")
    os.makedirs(dir_ref, exist_ok=True)
    os.chown(dir_ref, UID_B, UID_B)
    refwav = os.path.join(dir_ref, a.label_name + ".rif.wav")
    if g.get("sink_id"):
        ref = subprocess.Popen(
            as_user(["pw-record", "--target", str(g["sink_id"]),
                         "--rate", "48000", "--channels", "2", "--format", "s16",
                         refwav]),
            stdout=subprocess.DEVNULL, stderr=open(base + ".rif.txt", "wb"))

    # M3 · the tone REALLY plays inside the sink (the graph says so, not pw-play)
    f = tone(a.hz, a.seconds + 30)
    play = subprocess.Popen(as_user(["pw-play", "--target", SINK, f]),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    leg = 0
    for _ in range(50):
        gg = graph()
        leg = gg.get("legami_in_ingresso", 0)
        if leg > 0:
            break
        time.sleep(0.3)
    outcomes["M3_legami_in_ingresso"] = leg
    outcomes["M3_il_tono_suona"] = leg > 0

    # ── real time, and the threads BEFORE ──────────────────────────────────
    outcomes["fotografia_prima"] = snapshot()
    if a.nice is not None:
        outcomes["nice_applicato"] = nice_apply(a.nice)
    if a.rt == "si":
        outcomes["rt_applicato"] = rt_apply(a.prio)
    elif a.rt == "no":
        outcomes["rt_applicato"] = {"remark": "put back to normal policy"}
        rt_restore()

    # ── the load ───────────────────────────────────────────────────────────
    car = {"scene": None, "burners": 0}
    if a.load == "si":
        car = load_turn_on(a.burners)
    outcomes["load"] = {k: v for k, v in car.items() if not k.startswith("_")}
    if a.cpu >= 0:
        time.sleep(1.0)
        outcomes["stretti_su_core"] = {"cpu": a.cpu, "chi": pin_to_one_core(a.cpu)}

    # ── the sampling, one second at a time ─────────────────────────────────
    samples = []
    before = {}
    t_before = time.time()
    while cli.poll() is None and time.time() - t0 < a.seconds + 40:
        time.sleep(1.0)
        clock = time.time()
        dt = clock - t_before
        row = {"t": round(clock - t0, 1), "load": open("/proc/loadavg").read().split()[0],
                "thread": []}
        after = {}
        for v in snapshot():
            for t in v["thread"]:
                k = (v["pid"], t["tid"])
                after[k] = (t["cpu_tick"], t["attesa_ns"], t["how_many"])
                p = before.get(k)
                if p is None:
                    continue
                cpu = (t["cpu_tick"] - p[0]) / HZ_TICK / dt * 100.0
                expect = (t["attesa_ns"] - p[1]) / 1e6           # ms waited in the queue
                here = t["how_many"] - p[2]
                # ⛔ The threads of the AUDIO PATH are ALWAYS written, even at
                #    zero: they are the ones R26 talks about, and with the threshold alone
                #    they vanished precisely when they were quiet — that is the case
                #    that serves as comparison (`CODER.md` §3.10).
                always = any(k in t["label_name"] for k in
                             ("data-loop", "pw-data", "remotix-suono", "module-rt")) \
                    or v["comm"] in ("remotix", "pipewire", "pipewire-pulse",
                                     "wireplumber", "pw-play", "pw-record")
                if always or cpu >= 3.0 or expect >= 1.0:
                    row["thread"].append({
                        "chi": "%s/%s[%d]" % (v["comm"], t["label_name"], t["tid"]),
                        "cpu_pc": round(cpu, 1), "wait_ms": round(expect, 2),
                        "how_many": here, "policy_v": t["policy_v"], "prio": t["rtprio"],
                        "attesa_per_quanto_us": round(expect * 1000.0 / here, 1) if here else None})
        before = after
        t_before = clock
        samples.append(row)
    outcomes["samples"] = samples
    outcomes["fotografia_dopo"] = snapshot()
    outcomes["carico_dopo"] = open("/proc/loadavg").read().split()[:3]

    # ── everything is taken down, and we CHECK the scene is silent ─────────
    try: cli.wait(timeout=30)
    except Exception:
        cli.kill(); cli.wait()
    fcli.close()
    outcomes["cliente_uscita"] = cli.returncode
    for p in (play, ref):
        if p is not None:
            try:
                p.send_signal(signal.SIGINT); p.wait(timeout=5)
            except Exception:
                try: p.kill()
                except Exception: pass
    subprocess.run(["pkill", "-u", str(UID_B), "-x", "pw-play"], capture_output=True)
    subprocess.run(["pkill", "-u", str(UID_B), "-x", "pw-record"], capture_output=True)
    load_turn_off(car)
    if a.cpu >= 0:
        # ⛔ IT IS PUT BACK AS IT WAS, and declared: a session left on a single
        #    core would be an invisible state inherited by the next run.
        outcomes["allargati_di_nuovo"] = widen(a.all_cpus)
    if a.nice is not None:
        outcomes["nice_rimesso"] = nice_apply(0)
    if a.rt == "si":
        outcomes["rt_rimesso"] = rt_restore()
    # ⛔ «I killed» is not «nobody is playing any more»: the graph says so.
    for _ in range(20):
        gg = graph()
        if gg.get("legami_in_ingresso", 1) == 0:
            break
        time.sleep(0.3)
    outcomes["scena_zittita"] = gg.get("legami_in_ingresso", None) == 0

    outcomes["cliente_coda"] = open(base + ".txt", errors="replace").read()[-2500:]
    try:
        outcomes["registro_audio"] = [r.strip() for r in
                                   open(os.path.join(LAV, "registro.log"), errors="replace")
                                   if "audio" in r or "R26" in r or "RTPRIO" in r
                                   or "overflow" in r or "datagram" in r
                                   or "cwnd_left" in r][-40:]
    except Exception:
        pass
    json.dump(outcomes, open(base + ".esito.json", "w"), ensure_ascii=False, indent=1)
    print("⭐ run «%s» finished — %s.esito.json · %s blocks in the JSONL"
          % (a.label_name, base,
             sum(1 for _ in open(base + ".jsonl")) if os.path.exists(base + ".jsonl") else 0))
    return 0


def primary():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="step", required=True)
    g = s.add_parser("lap")
    g.add_argument("--label_name", required=True)
    g.add_argument("--load", choices=["si", "no"], default="no")
    g.add_argument("--rt", choices=["si", "no", "come-sta"], default="come-sta")
    g.add_argument("--prio", type=int, default=20)
    g.add_argument("--burners", type=int, default=int(os.environ.get("BRUCIATORI", "20")))
    g.add_argument("--hz", type=int, default=440)
    g.add_argument("--seconds", type=int, default=30)
    g.add_argument("--video", default="si", choices=["si", "no"],
                   help="the client asks for the canvas, so the video FLOWS")
    g.add_argument("--canvas_size", default="1920x1080")
    g.add_argument("--codec", default="pcm", choices=["pcm", "opus"],
                   help="what the client declares in audio.codec")
    g.add_argument("--nice", type=int, default=None,
                   help="makes the audio path more or less nice (renice)")
    g.add_argument("--cpu", type=int, default=-1,
                   help="squeezes the whole audio path onto THIS core (-1 = no)")
    g.add_argument("--all-cpus", default="0-%d" % (os.cpu_count() - 1),
                   help="what the affinity is put back to at the end")
    s.add_parser("snapshot")
    s.add_parser("graph")
    a = p.parse_args()
    if os.geteuid() != 0:
        print("⛔ must be run AS ROOT", file=sys.stderr); return 2

    os.makedirs(LAV, exist_ok=True)
    if a.step == "snapshot":
        print(json.dumps(snapshot(), ensure_ascii=False, indent=1)); return 0
    if a.step == "graph":
        print(json.dumps(graph(), ensure_ascii=False, indent=1)); return 0
    return lap(a)


if __name__ == "__main__":
    sys.exit(primary())
