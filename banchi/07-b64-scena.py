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
    python3 07-b64-scena.py giro --nome 1-fermo --carico no  --rt come-sta
    python3 07-b64-scena.py giro --nome 2-lavora --carico si --rt come-sta
    python3 07-b64-scena.py giro --nome 3-lavora-rt --carico si --rt si
    python3 07-b64-scena.py fotografia        # only the threads, no scene
"""
import argparse, json, os, signal, subprocess, sys, time

UTENTE = os.environ.get("UTENTE", "provar7")
UID_B = int(os.environ.get("UID_B", "1018"))
PORTA = int(os.environ.get("PORTA", "7801"))
IND = os.environ.get("IND", "192.168.0.2")
LAV = os.environ.get("LAV", "/media/REMOTIX/tmp/07-r")
ALB = os.environ.get("ALBERO", "/media/REMOTIX/src/07-r-src")
DENTRO_ALB = os.environ.get("DENTRO_ALB", "/srv/src/07-r-src")
DENTRO_LAV = os.environ.get("DENTRO_LAV", "/srv/remotix/tmp/07-r")
SINK = os.environ.get("SINK", "remotix")
SCENA_BIN = os.environ.get("SCENA_BIN", "/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena")

POLITICA = {0: "normale", 1: "FIFO", 2: "RR", 3: "batch", 5: "idle", 6: "deadline"}
HZ_TICK = os.sysconf("SC_CLK_TCK")


# ── the session's environment, built from scratch (CODER.md §4.5) ──────────
def come_utente(cmd, **kw):
    base = ["setpriv", "--reuid=%d" % UID_B, "--regid=%d" % UID_B, "--init-groups",
            "env", "-i",
            "HOME=/home/%s" % UTENTE, "USER=%s" % UTENTE, "LANG=C.UTF-8",
            "PATH=/usr/local/bin:/usr/bin:/bin",
            "XDG_RUNTIME_DIR=/run/user/%d" % UID_B,
            "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/%d/bus" % UID_B,
            "XDG_CURRENT_DESKTOP=GNOME", "XDG_SESSION_DESKTOP=gnome",
            "XDG_SESSION_TYPE=wayland"]
    return base + cmd


def esegui(cmd, tetto=20):
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=tetto)
        return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")
    except subprocess.TimeoutExpired:
        return 124, "", "⛔ timed out after %d s" % tetto


# ── /proc: the policy, the priority and THE WAIT IN THE QUEUE ──────────────
def thread_stat(pid, tid):
    try:
        d = open("/proc/%d/task/%d/stat" % (pid, tid)).read()
    except Exception:
        return None
    a = d.index("("); b = d.rindex(")")
    nome = d[a + 1:b]
    c = d[b + 2:].split()
    utime, stime = int(c[11]), int(c[12])
    rtprio, policy = int(c[37]), int(c[38])
    # ⭐ schedstat: [time on the CPU ns, WAIT IN THE QUEUE ns, how many timeslices]
    attesa = eseguiti = 0
    try:
        s = open("/proc/%d/task/%d/schedstat" % (pid, tid)).read().split()
        attesa, eseguiti = int(s[1]), int(s[2])
    except Exception:
        pass
    return {"nome": nome, "tid": tid, "cpu_tick": utime + stime,
            "rtprio": rtprio, "policy": policy,
            "politica": POLITICA.get(policy, str(policy)),
            "attesa_ns": attesa, "quanti": eseguiti}


def limite_rt(pid):
    try:
        for r in open("/proc/%d/limits" % pid):
            if "realtime priority" in r.lower():
                return r.split()[3]
    except Exception:
        pass
    return "?"


def processi_interessanti():
    """The session's child, the user's PipeWire daemons, the player and
       the referee.  ⛔ And the SERVER, which is the one carrying the rlimit."""
    fuori = []
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
        mio = (uid == UID_B) or ("remotix" in comm and (str(PORTA) in cmd or UTENTE in cmd))
        if mio:
            fuori.append((p, uid, comm, cmd[:120]))
    return fuori


def fotografia():
    """Who has real time and who does not — the snapshot of R26, in full."""
    r = []
    for p, uid, comm, cmd in sorted(processi_interessanti()):
        v = {"pid": p, "uid": uid, "comm": comm, "cmdline": cmd,
             "rlimit_rtprio": limite_rt(p), "thread": []}
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
def grafo():
    rc, out, err = esegui(come_utente(["pw-dump"]), 25)
    if rc != 0 or not out.strip():
        return {"errore": "pw-dump produced nothing (rc %d): %s" % (rc, err[:200])}
    try:
        d = json.loads(out)
    except Exception as e:
        return {"errore": "pw-dump unreadable: %s" % e}
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
def tono(hz, secondi, ampiezza=0.5):
    import math, struct, wave
    f = os.path.join(LAV, "tono-%d.wav" % hz)
    if os.path.exists(f) and os.path.getsize(f) >= 48000 * secondi * 4:
        return f
    w = wave.open(f, "wb"); w.setnchannels(2); w.setsampwidth(2); w.setframerate(48000)
    d = bytearray()
    for n in range(48000 * secondi):
        v = int(ampiezza * math.sin(2 * math.pi * hz * n / 48000) * 32767)
        d += struct.pack("<hh", v, v)
    w.writeframes(bytes(d)); w.close()
    os.chmod(f, 0o644)
    return f


# ── the load: the desktop that WORKS ───────────────────────────────────────
def monitor_catturato():
    """⛔ The monitor name is NOT written by hand: MY product's log
       says it.  A scene started «somewhere» does not load the stage."""
    try:
        testo = open(os.path.join(LAV, "registro.log"), errors="replace").read()
    except Exception:
        return None
    # ⛔ The form is the one of `04-b32-terreno.sh`, and it is not reinvented: the
    #    log writes `monitor «Meta-0»`.  ⚠ The first draft looked for any
    #    word with a dash and a number and found nothing: the
    #    «the desktop works» run ran WITHOUT the scene, and said so only in
    #    a JSON field nobody looked at.
    import re
    m = [x for x in re.findall(r"monitor \u00ab([^\u00bb]*)\u00bb", testo) if x]
    return m[-1] if m else None


def monitor_atteso(tetto_s=25.0):
    """⛔ THE MONITOR NAME IS WAITED FOR — and the first draft did not.

       `[M]` 21 August 2026: the log writes «monitor «Meta-0»» ~2.9 s after
       the session opens, and M3 (the tone playing) comes earlier.  ⇒ Whoever
       reads the log at M3 does not find the name, the scene does not start, and the run
       is called «the desktop works» all the same.  ⚠ In yesterday's runs the defect
       could NOT be seen because the log still contained the line of the previous
       session: that is, it worked for a wrong reason, and that is the worst
       form — a bench that stops working when you clean it."""
    fine = time.time() + tetto_s
    while time.time() < fine:
        u = monitor_catturato()
        if u:
            return u
        time.sleep(0.5)
    return None


def carico_accendi(quanti):
    """⛔ Two loads, and they are two different things:
         · the SCENE, which makes the child's capture and encoder work —
           it is the one R26 names;
         · the BURNERS, which take the CPU away from everyone — it is the condition in which
           a priority is good for something.
       ⚠ We declare which of the two started: if the scene does not start, the run
         stays valid but is NO longer «the desktop works», and it is something else."""
    stato = {"scena": None, "bruciatori": 0, "scena_perche_no": None}
    usc = monitor_atteso()
    if os.access(SCENA_BIN, os.X_OK) and usc:
        log = open(os.path.join(LAV, "scena.log"), "ab")
        p = subprocess.Popen(
            come_utente(["env", "WAYLAND_DISPLAY=wayland-0", SCENA_BIN,
                         "--uscita", usc, "--movimento", "barra",
                         "--shm", "/07-b64-scena", "--giro", "b64"]),
            stdout=log, stderr=log)
        time.sleep(1.0)
        vivo = subprocess.run(["pgrep", "-u", str(UID_B), "-f", "04-b30-scena --uscita"],
                              capture_output=True).stdout.decode().split()
        stato["scena"] = usc if vivo else None
        if not vivo:
            stato["scena_perche_no"] = "the scene started and died at once (see scena.log)"
        stato["_p"] = p
    else:
        stato["scena_perche_no"] = ("the binary %s is not executable" % SCENA_BIN
                                    if not os.access(SCENA_BIN, os.X_OK)
                                    else "I do not know which monitor my child captures")
    bruc = []
    for _ in range(quanti):
        bruc.append(subprocess.Popen(
            come_utente(["python3", "-c", "\nwhile True: pass\n"]),
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL))
    stato["bruciatori"] = len(bruc)
    stato["_bruc"] = bruc
    return stato


def carico_spegni(stato):
    for p in stato.get("_bruc", []):
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
def stringi_su_un_core(cpu):
    fatti = []
    for v in fotografia():
        if v["comm"] in ("remotix", "pipewire", "pipewire-pulse", "wireplumber",
                         "pw-play", "pw-record", "04-b30-scena") and v["uid"] != 0:
            rc, _, err = esegui(["taskset", "-acp", str(cpu), str(v["pid"])], 5)
            fatti.append("%s[%d] rc=%d" % (v["comm"], v["pid"], rc))
    return fatti


def allarga(cpu_tutti):
    fatti = []
    for v in fotografia():
        if v["uid"] != 0:
            esegui(["taskset", "-acp", cpu_tutti, str(v["pid"])], 5)
            fatti.append(v["comm"])
    return fatti


# ── real time, given by hand — ⭐ it is the A/B of R26 ─────────────────────
def rt_applica(prio):
    """⛔ We do not «configure PipeWire»: the policy of the LIVE threads is moved with
       `chrt`, so that between the two runs ONE thing only changes.  ⚠ And we record who
       was moved and who refused."""
    fatti, falliti = [], []
    for v in fotografia():
        for t in v["thread"]:
            if "data-loop" in t["nome"] or "pw-data" in t["nome"]:
                rc, _, err = esegui(["chrt", "-f", "-p", str(prio), str(t["tid"])], 5)
                (fatti if rc == 0 else falliti).append(
                    "%s/%s[%d]%s" % (v["comm"], t["nome"], t["tid"],
                                     "" if rc == 0 else " ⛔ " + err.strip()[:60]))
    return {"promossi": fatti, "falliti": falliti, "prio": prio}


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
def nice_applica(livello):
    fatti, falliti = [], []
    for v in fotografia():
        if v["uid"] == 0:
            continue
        for t in v["thread"]:
            if ("data-loop" in t["nome"] or v["comm"] in ("pw-play", "pw-record")
                    or (v["comm"] in ("pipewire", "pipewire-pulse", "wireplumber")
                        and t["tid"] == v["pid"])):
                rc, _, err = esegui(["renice", "-n", str(livello), "-p", str(t["tid"])], 5)
                (fatti if rc == 0 else falliti).append(
                    "%s/%s[%d]%s" % (v["comm"], t["nome"], t["tid"],
                                     "" if rc == 0 else " NO " + err.strip()[:50]))
    return {"livello": livello, "fatti": fatti, "falliti": falliti}


def rt_rimetti():
    fatti = []
    for v in fotografia():
        for t in v["thread"]:
            if t["policy"] != 0 and ("data-loop" in t["nome"] or "pw-data" in t["nome"]):
                rc, _, _ = esegui(["chrt", "-o", "-p", "0", str(t["tid"])], 5)
                fatti.append("%s[%d] rc=%d" % (t["nome"], t["tid"], rc))
    return fatti


# ═══════════════════════════════════════════════════════════════════════════
def giro(a):
    esiti = {"nome": a.nome, "porta": PORTA, "utente": UTENTE,
             "ora_macchina": time.strftime("%Y-%m-%d %H:%M:%S"),
             "carico_chiesto": a.carico, "rt_chiesto": a.rt}
    base = os.path.join(LAV, a.nome)
    # ⚠ What is left from the previous run is EMPTIED (LEZIONI.md §2.3-quinquies).
    for e in (".jsonl", ".segnale", ".txt", ".rif.wav", ".esito.json"):
        try: os.remove(base + e)
        except Exception: pass

    esiti["carico_prima"] = open("/proc/loadavg").read().split()[:3]

    # ── the client starts first: it is the one that opens the session ──────
    # ⭐ `--codec opus` serves the mandate on datagrams: Opus is what runs
    #    in real sessions, and it costs 1/13 of PCM's bandwidth.  ⚠ The ear
    #    judge cannot decode it — with Opus the TRANSPORT is counted,
    #    and we declare it instead of pretending to have listened.
    cmd = ("python3 -u %s/banchi/01-b3-cliente.py --indirizzo %s --porta %d "
           "--utente %s --parola-file %s/parola --audio-codec %s "
           "--audio-scrivi %s/%s.jsonl --segnale %s/%s.segnale "
           "%s --resta %d"
           % (DENTRO_ALB, IND, PORTA, UTENTE, DENTRO_LAV, a.codec,
              DENTRO_LAV, a.nome, DENTRO_LAV, a.nome,
              # ⛔ WITHOUT `--adatta` THE VIDEO DOES NOT START, and the run would measure
              #    the audio alone calling it «audio against video».  §6.6: the
              #    server sends frames after the `ADATTA_TELA`, which the page
              #    sends by itself and the test client does not.
              ("--adatta %s --video-scrivi %s/%s.265" % (a.tela, DENTRO_LAV, a.nome)
               if a.video == "si" else ""),
              a.secondi))
    fcli = open(base + ".txt", "wb")
    cli = subprocess.Popen(["bash", "/media/REMOTIX/enter.sh", "--root", cmd],
                           stdout=fcli, stderr=fcli)
    t0 = time.time()

    # M1 · the client opened the session (a file written and closed is a fact)
    while time.time() - t0 < 90 and not os.path.exists(base + ".segnale"):
        if cli.poll() is not None:
            break
        time.sleep(0.2)
    esiti["M1_sessione_aperta"] = os.path.exists(base + ".segnale")
    esiti["M1_dopo_s"] = round(time.time() - t0, 2)
    if not esiti["M1_sessione_aperta"]:
        esiti["errore"] = ("⛔ M1 did not arrive: the client did not open the "
                           "session.  ⚠ It is NOT «the audio does not arrive»: it is «the "
                           "scene was not set up»")
        try: cli.kill()
        except Exception: pass
        cli.wait()
        fcli.close()
        esiti["cliente_coda"] = open(base + ".txt", errors="replace").read()[-1500:]
        json.dump(esiti, open(base + ".esito.json", "w"), ensure_ascii=False, indent=1)
        print(json.dumps(esiti, ensure_ascii=False, indent=1))
        return 2

    # M2 · the sink exists in the graph
    g = {}
    for _ in range(60):
        g = grafo()
        if g.get("sink_id"):
            break
        time.sleep(0.4)
    esiti["M2_grafo"] = g

    # ── the independent referee: a second capture of the same monitor ──────
    rif = None
    # ⛔ The referee's folder is ITS OWN: `pw-record` runs as the session's user,
    #    and on $LAV (root 755) it cannot create anything.  ⚠ The symptom was
    #    "Permission denied" inside a stderr file nobody looked at, and the
    #    run was left without a referee without saying so.
    dir_rif = os.path.join(LAV, "rif")
    os.makedirs(dir_rif, exist_ok=True)
    os.chown(dir_rif, UID_B, UID_B)
    rifwav = os.path.join(dir_rif, a.nome + ".rif.wav")
    if g.get("sink_id"):
        rif = subprocess.Popen(
            come_utente(["pw-record", "--target", str(g["sink_id"]),
                         "--rate", "48000", "--channels", "2", "--format", "s16",
                         rifwav]),
            stdout=subprocess.DEVNULL, stderr=open(base + ".rif.txt", "wb"))

    # M3 · the tone REALLY plays inside the sink (the graph says so, not pw-play)
    f = tono(a.hz, a.secondi + 30)
    play = subprocess.Popen(come_utente(["pw-play", "--target", SINK, f]),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    leg = 0
    for _ in range(50):
        gg = grafo()
        leg = gg.get("legami_in_ingresso", 0)
        if leg > 0:
            break
        time.sleep(0.3)
    esiti["M3_legami_in_ingresso"] = leg
    esiti["M3_il_tono_suona"] = leg > 0

    # ── real time, and the threads BEFORE ──────────────────────────────────
    esiti["fotografia_prima"] = fotografia()
    if a.nice is not None:
        esiti["nice_applicato"] = nice_applica(a.nice)
    if a.rt == "si":
        esiti["rt_applicato"] = rt_applica(a.prio)
    elif a.rt == "no":
        esiti["rt_applicato"] = {"nota": "put back to normal policy"}
        rt_rimetti()

    # ── the load ───────────────────────────────────────────────────────────
    car = {"scena": None, "bruciatori": 0}
    if a.carico == "si":
        car = carico_accendi(a.bruciatori)
    esiti["carico"] = {k: v for k, v in car.items() if not k.startswith("_")}
    if a.cpu >= 0:
        time.sleep(1.0)
        esiti["stretti_su_core"] = {"cpu": a.cpu, "chi": stringi_su_un_core(a.cpu)}

    # ── the sampling, one second at a time ─────────────────────────────────
    campioni = []
    prima = {}
    tprima = time.time()
    while cli.poll() is None and time.time() - t0 < a.secondi + 40:
        time.sleep(1.0)
        adesso = time.time()
        dt = adesso - tprima
        riga = {"t": round(adesso - t0, 1), "carico": open("/proc/loadavg").read().split()[0],
                "thread": []}
        dopo = {}
        for v in fotografia():
            for t in v["thread"]:
                k = (v["pid"], t["tid"])
                dopo[k] = (t["cpu_tick"], t["attesa_ns"], t["quanti"])
                p = prima.get(k)
                if p is None:
                    continue
                cpu = (t["cpu_tick"] - p[0]) / HZ_TICK / dt * 100.0
                att = (t["attesa_ns"] - p[1]) / 1e6           # ms waited in the queue
                qua = t["quanti"] - p[2]
                # ⛔ The threads of the AUDIO PATH are ALWAYS written, even at
                #    zero: they are the ones R26 talks about, and with the threshold alone
                #    they vanished precisely when they were quiet — that is the case
                #    that serves as comparison (`CODER.md` §3.10).
                sempre = any(k in t["nome"] for k in
                             ("data-loop", "pw-data", "remotix-suono", "module-rt")) \
                    or v["comm"] in ("remotix", "pipewire", "pipewire-pulse",
                                     "wireplumber", "pw-play", "pw-record")
                if sempre or cpu >= 3.0 or att >= 1.0:
                    riga["thread"].append({
                        "chi": "%s/%s[%d]" % (v["comm"], t["nome"], t["tid"]),
                        "cpu_pc": round(cpu, 1), "attesa_ms": round(att, 2),
                        "quanti": qua, "politica": t["politica"], "prio": t["rtprio"],
                        "attesa_per_quanto_us": round(att * 1000.0 / qua, 1) if qua else None})
        prima = dopo
        tprima = adesso
        campioni.append(riga)
    esiti["campioni"] = campioni
    esiti["fotografia_dopo"] = fotografia()
    esiti["carico_dopo"] = open("/proc/loadavg").read().split()[:3]

    # ── everything is taken down, and we CHECK the scene is silent ─────────
    try: cli.wait(timeout=30)
    except Exception:
        cli.kill(); cli.wait()
    fcli.close()
    esiti["cliente_uscita"] = cli.returncode
    for p in (play, rif):
        if p is not None:
            try:
                p.send_signal(signal.SIGINT); p.wait(timeout=5)
            except Exception:
                try: p.kill()
                except Exception: pass
    subprocess.run(["pkill", "-u", str(UID_B), "-x", "pw-play"], capture_output=True)
    subprocess.run(["pkill", "-u", str(UID_B), "-x", "pw-record"], capture_output=True)
    carico_spegni(car)
    if a.cpu >= 0:
        # ⛔ IT IS PUT BACK AS IT WAS, and declared: a session left on a single
        #    core would be an invisible state inherited by the next run.
        esiti["allargati_di_nuovo"] = allarga(a.cpu_tutti)
    if a.nice is not None:
        esiti["nice_rimesso"] = nice_applica(0)
    if a.rt == "si":
        esiti["rt_rimesso"] = rt_rimetti()
    # ⛔ «I killed» is not «nobody is playing any more»: the graph says so.
    for _ in range(20):
        gg = grafo()
        if gg.get("legami_in_ingresso", 1) == 0:
            break
        time.sleep(0.3)
    esiti["scena_zittita"] = gg.get("legami_in_ingresso", None) == 0

    esiti["cliente_coda"] = open(base + ".txt", errors="replace").read()[-2500:]
    try:
        esiti["registro_audio"] = [r.strip() for r in
                                   open(os.path.join(LAV, "registro.log"), errors="replace")
                                   if "audio" in r or "R26" in r or "RTPRIO" in r
                                   or "overflow" in r or "datagram" in r
                                   or "cwnd_left" in r][-40:]
    except Exception:
        pass
    json.dump(esiti, open(base + ".esito.json", "w"), ensure_ascii=False, indent=1)
    print("⭐ run «%s» finished — %s.esito.json · %s blocks in the JSONL"
          % (a.nome, base,
             sum(1 for _ in open(base + ".jsonl")) if os.path.exists(base + ".jsonl") else 0))
    return 0


def principale():
    p = argparse.ArgumentParser()
    s = p.add_subparsers(dest="passo", required=True)
    g = s.add_parser("giro")
    g.add_argument("--nome", required=True)
    g.add_argument("--carico", choices=["si", "no"], default="no")
    g.add_argument("--rt", choices=["si", "no", "come-sta"], default="come-sta")
    g.add_argument("--prio", type=int, default=20)
    g.add_argument("--bruciatori", type=int, default=int(os.environ.get("BRUCIATORI", "20")))
    g.add_argument("--hz", type=int, default=440)
    g.add_argument("--secondi", type=int, default=30)
    g.add_argument("--video", default="si", choices=["si", "no"],
                   help="the client asks for the canvas, so the video FLOWS")
    g.add_argument("--tela", default="1920x1080")
    g.add_argument("--codec", default="pcm", choices=["pcm", "opus"],
                   help="what the client declares in audio.codec")
    g.add_argument("--nice", type=int, default=None,
                   help="makes the audio path more or less nice (renice)")
    g.add_argument("--cpu", type=int, default=-1,
                   help="squeezes the whole audio path onto THIS core (-1 = no)")
    g.add_argument("--cpu-tutti", default="0-%d" % (os.cpu_count() - 1),
                   help="what the affinity is put back to at the end")
    s.add_parser("fotografia")
    s.add_parser("grafo")
    a = p.parse_args()
    if os.geteuid() != 0:
        print("⛔ must be run AS ROOT", file=sys.stderr); return 2

    os.makedirs(LAV, exist_ok=True)
    if a.passo == "fotografia":
        print(json.dumps(fotografia(), ensure_ascii=False, indent=1)); return 0
    if a.passo == "grafo":
        print(json.dumps(grafo(), ensure_ascii=False, indent=1)); return 0
    return giro(a)


if __name__ == "__main__":
    sys.exit(principale())
