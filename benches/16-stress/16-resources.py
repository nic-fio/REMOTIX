#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
16-resources — THE RESOURCE SAMPLER, ON THE SERVER (phase 16, §7 and §10)

    (on the server, as root)  python3 16-resources.py --box kde --dir DIR [--interval 1]
                                                [--duration S] [--pss-every 5]
                                                [--browser-marks remotix-ff-,remotix-cr-]
    python3 16-resources.py --certify          (no server: FAKE /proc and /sys)

Writes DIR/resources.jsonl, ONE JSON row per second, until it receives SIGTERM
(or SIGINT, or --duration expires).  The first row is the header (`"type":
"header"`: machine, cards, box); the others are samples.

⛔ It must run as ROOT (sudo): `smaps_rollup` and `fdinfo` of the processes of the
   tenants and of root cannot be read by another user.  Without root the
   sampler does NOT pretend: the enclosures it cannot read are reported in `avvisi`.

THE THREE ENCLOSURES (§7) — how they are found, and why this way
----------------------------------------------------------------------------
`[M]` 25 Sep 2026, kde box with a live session: the box's cgroups do NOT
coincide with the enclosures.  The parent `remotix` is in
  /machine.slice/libpod-<id>.scope/container/system.slice/rete11-server.service
but the per-session CHILD (`remotix`, the tenant's uid) is in the tenant's
logind scope (`…/user.slice/user-4013.slice/session-c5.scope`), together
with the session; and the applications launched by the benches with `podman exec … runuser`
end up in `…/container/init.scope`.  ⇒ the enclosure is decided PROCESS BY
PROCESS, and the cgroup serves to say «inside the box» and to count the total:

  remotix   inside the box, and: in the cgroup `rete11-server.service`, OR its
            executable is called `remotix` (the per-session children).
            `per_inquilino` = the children, per tenant; `padre` = the rest.
  sessioni  inside the box, uid >= 1000 (and not 65534), and not `remotix`:
            compositor, applications, pipewire, dbus… — `per_inquilino` with the
            name read from the BOX's /etc/passwd.
  browser   outside the box: every process whose command line carries a
            MARK of the benches' profiles (`remotix-ff-` Firefox/Marionette,
            `remotix-cr-` Chrome/CDP: `12-real-clients.py` and `07-b46`) and ALL
            its descendants (Firefox's content processes do not carry the
            profile on the command line: their parent does).  ⭐ It is the most
            reliable way without touching the actor: the profile is made by the
            bench, a user's Firefox does not have it.  (If the actor launched
            each browser with `systemd-run --user --scope --unit=r16-browser-NN`
            the enclosure would also be a cgroup: here adding the mark is enough.)
  ⭐ --system xrdp (phases/20 §7.4): the box is `rete11-<desktop>-xrdp`; the enclosure
            `remotix` is xrdp (executables xrdp, xrdp-sesman, xrdp-sesexec, xrdp-chansrv, or
            the units xrdp.service / xrdp-sesman.service) — HERE RemoteFX is compressed;
            `sessioni` includes each tenant's Xorg (xorgxrdp, the capture);
            `browser` are the xfreerdp3 (mark `remotix-rdp-`); `labwc_cliente` also
            the Xvfb.  `remotix_pid` is the xrdp daemon (the parent of the connections).
            ⛔ The two divisions are not compared enclosure by enclosure: the comparison is
            made on the box's TOTALS.
  + apart, and NOT enclosures: `altro_scatola` (the box's root processes
    that are not remotix: systemd, journald, logind…) and `labwc_cliente` (the
    browsers' screenless compositors, benches' user, on the host).

⚠ THE CPU OF SHORT PROCESSES.  An `ls` typed in the terminal is born and dies between
  two samples: the per-process reading does not see it.  ⇒ `sessioni.cpu_core` is
  taken from the box's cgroup (exact) MINUS remotix and `altro_scatola`
  (long processes, exact per process); `sessioni.cpu_non_attribuita` is the
  part that no live tenant carries (the processes that died in between).  The
  browser has no cgroup of its own: its processes are long, and the loss is stated.

THE GRAPHICS CARD — from the kernel, per process (`/proc/<pid>/fdinfo`)
----------------------------------------------------------------------------
GENERIC keys of the DRM standard (Documentation/gpu/drm-usage-stats):
  drm-engine-<engine>: <ns> ns        busy time, cumulative ⇒ Δns/Δt = usage
  drm-engine-capacity-<engine>: <n>   engines of that class ⇒ divide by n
  drm-cycles-<m> / drm-total-cycles-<m>   (xe) ⇒ Δcycles/Δtotal
  drm-total-/drm-resident-<region>, drm-memory-<region>: <n> [KiB|MiB]
  drm-client-id, drm-pdev             a client open on several fds or inherited
                                      by a child is counted ONCE
Intel i915: render · copy · video (capacity 2) · video-enhance, regions
system0/stolen-system0.  AMD amdgpu: gfx · compute · enc · dec (and dma/jpeg),
regions vram/gtt/cpu (or `drm-memory-vram` on old kernels).  The CATEGORIES
(`disegno`, `video`, `video_enhance`, `copia`, `calcolo`) are decided from the name.
⭐ `intel_gpu_top` is NOT needed: fdinfo already gives the usage per engine and per process, and
  the frequency, the throttling and the power come from sysfs (below).
  ⚠ What fdinfo does not see: the kernel's work without a client (screen
  scan-out), and the last piece of a client closed between two samples.
  The sum per card is «sum of the clients», not the hardware counter.

Per card (sysfs): i915 `gt_cur_freq_mhz`, `gt_act_freq_mhz`,
`gt/gt0/throttle_reason_*` (throttling: the active reasons); amdgpu
`gpu_busy_percent`, `mem_info_vram_used/total`, hwmon (temperatures, sclk,
power).  Temperature of the Intel iGPU: it has NO sensor of its own ⇒ the
CPU package is recorded (coretemp, same die), declared as such.
Power: RAPL `package` and `uncore` (= the iGPU) from powercap.

THE ROW (sample):
  {"type":"sample","t":<epoch>,"time":"…","dt_s":1.0,"box":"kde",
   "machine":{"cpu_core","cpu_pct","load":[1,5,15],"processes","thread",
               "mem_total_mb","mem_available_mb","mem_used_mb"},
   "box_cg":{"cpu_core","mem_mb","anon_mb","pids"},
   "enclosures":{"remotix":{…,"parent":{…},"per_tenant":{nome:{…}}},
              "sessions":{…,"cpu_unattributed","per_tenant":{nome:{…}}},
              "browser":{…,"per_browser":[{"pid","type","profile",…}]},
              "other_box":{…},"labwc_client":{…}},
     where {…} = {"cpu_core","processes","thread","rss_mb","pss_mb",
                 "gpu":{categoria:%},"gpu_mem_mb"}
   "gpu":{"<pdev>":{"card","driver","engines":{nome:%},"categories":{…},
                    "freq_mhz","freq_cur_mhz","temp_c","temp_source","power_w",
                    "strozzatura":[…],"busy_pct","vram_used_mb"}},
   "gpu_processes":[{"pid","comm","recinto","tenant","pdev","engines":{…}}],
   "remotix_pid":n, "warnings":[…], "misuratore":{"cpu_core","ms"}}
  `pss_mb`: PSS from smaps_rollup, each process re-read every --pss-every seconds
  in rotation (the cost is spread out), and immediately at first sight.
"""
import argparse
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time

CLK = os.sysconf("SC_CLK_TCK")
PAGE_KB = os.sysconf("SC_PAGE_SIZE") // 1024
BROWSER_MARKS = ("remotix-ff-", "remotix-cr-")
XRDP_EXE = ("xrdp", "xrdp-sesman", "xrdp-sesexec", "xrdp-chansrv")
ENCLOSURES = ("remotix", "sessions", "browser")
EXTRA = ("other_box", "labwc_client")


# ─────────────────────────────── fdinfo ────────────────────────────────────
def unit(v):
    """'123 KiB' → bytes.  Without a unit they are bytes (the standard)."""
    p = v.split()
    try:
        n = float(p[0])
    except (ValueError, IndexError):
        return None
    u = p[1] if len(p) > 1 else ""
    return n * {"": 1, "KiB": 1024, "MiB": 1024 ** 2, "GiB": 1024 ** 3}.get(u, 1)


def read_fdinfo(text):
    """The `drm-*` block of an fdinfo, in a simple dictionary:
    {driver, pdev, client, motori{nome:ns}, capacita{nome:n}, cicli{nome:c},
     cicli_tot{nome:c}, memoria{regione:byte}}   — None if it is not DRM."""
    d = {"engines": {}, "capacita": {}, "cicli": {}, "cicli_tot": {}, "memory": {},
         "driver": None, "pdev": None, "client": None}
    seen = False
    for line in text.splitlines():
        if not line.startswith("drm-"):
            continue
        k, _, v = line.partition(":")
        v = v.strip()
        seen = True
        if k == "drm-driver":
            d["driver"] = v
        elif k == "drm-pdev":
            d["pdev"] = v
        elif k == "drm-client-id":
            d["client"] = v
        elif k.startswith("drm-engine-capacity-"):
            try:
                d["capacita"][k[len("drm-engine-capacity-"):]] = int(v)
            except ValueError:
                pass
        elif k.startswith("drm-engine-"):
            try:
                d["engines"][k[len("drm-engine-"):]] = int(v.split()[0])
            except (ValueError, IndexError):
                pass
        elif k.startswith("drm-total-cycles-"):
            try:
                d["cicli_tot"][k[len("drm-total-cycles-"):]] = int(v.split()[0])
            except (ValueError, IndexError):
                pass
        elif k.startswith("drm-cycles-"):
            try:
                d["cicli"][k[len("drm-cycles-"):]] = int(v.split()[0])
            except (ValueError, IndexError):
                pass
        elif k.startswith("drm-resident-") or k.startswith("drm-memory-"):
            # ⚠ `resident` and not `total`: `total` also counts what is only
            #   reserved.  `drm-memory-*` is the old form (amdgpu).
            reg = k.split("-", 2)[2]
            b = unit(v)
            if b is not None:
                d["memory"][reg] = d["memory"].get(reg, 0) + b
    return d if seen and d["driver"] else None


def category(engine):
    m = engine.lower()
    if "enhance" in m or m.startswith("vecs"):
        return "video_enhance"
    if m in ("render", "gfx", "rcs") or m.startswith("rcs") or m.startswith("gfx"):
        return "draw"
    if (m.startswith("video") or m.startswith("vcs") or m in ("enc", "dec", "jpeg")
            or m.startswith("vcn") or m.startswith("uvd") or m.startswith("vce")
            or m.startswith("enc") or m.startswith("dec")):
        return "video"
    if m in ("copy", "dma", "sdma") or m.startswith("bcs") or m.startswith("sdma"):
        return "copy"
    if m.startswith("compute") or m.startswith("ccs"):
        return "compute"
    return m


def use_client(before, now, dt_ns):
    """Usage % per engine of ONE client between two readings.  Normalised on the
    capacity (i915 video: 2 engines ⇒ 100 % = both full)."""
    out = {}
    if before is None or dt_ns <= 0:
        return out
    for m, ns in now["engines"].items():
        p = before["engines"].get(m)
        if p is None or ns < p:            # new or reset counter: nothing
            continue
        cap = max(1, now["capacita"].get(m, 1))
        out[m] = 100.0 * (ns - p) / dt_ns / cap
    for m, c in now["cicli"].items():
        p, tp, t = before["cicli"].get(m), before["cicli_tot"].get(m), now["cicli_tot"].get(m)
        if None in (p, tp, t) or t <= tp or c < p:
            continue
        cap = max(1, now["capacita"].get(m, 1))
        out[m] = 100.0 * (c - p) / (t - tp) / cap
    return out


# ─────────────────────────────── /proc ─────────────────────────────────────
def read_file(p, dflt=None):
    try:
        with open(p, "r", errors="replace") as f:
            return f.read()
    except OSError:
        return dflt


def stat_pid(proc, pid):
    s = read_file("%s/%d/stat" % (proc, pid))
    if not s:
        return None
    i = s.rfind(")")
    comm = s[s.find("(") + 1:i]
    r = s[i + 2:].split()
    try:
        return {"comm": comm, "ppid": int(r[1]), "cpu": int(r[11]) + int(r[12]),
                "thread": int(r[17]), "startup": int(r[19]), "rss_kb": int(r[21]) * PAGE_KB}
    except (IndexError, ValueError):
        return None


def pss_kb(proc, pid):
    s = read_file("%s/%d/smaps_rollup" % (proc, pid))
    if not s:
        return None
    m = re.search(r"^Pss:\s+(\d+)\s*kB", s, re.M)
    return int(m.group(1)) if m else None


class Sampler:
    def __init__(self, box, proc="/proc", sys_="/sys", container=None,
                 clock=time.monotonic, browser_marks=BROWSER_MARKS,
                 pss_every=5, discover=True, system="remotix"):
        self.box = box
        self.system = system
        self.proc, self.sys = proc, sys_
        self.cgroot = sys_ + "/fs/cgroup"
        self.clock = clock
        self.marks = tuple(s for s in browser_marks if s)
        self.pss_every = max(1, int(pss_every))
        self.cont = container or (self.discover_container() if discover else None)
        self.round_id = 0
        self.t_before = None
        self.cpu_before = {}            # (pid, start) → ticks
        self.cpu_mac_before = None
        self.cg_before = None
        self.pss = {}                  # (pid, start) → kB
        self.info = {}                 # (pid, start) → {cg, cmd, exe, uid}
        self.drm_fd = {}               # (pid, start) → [fd, …]
        self.drm_eta = {}              # (pid, start) → round of the last scan
        self.drm_before = {}            # client key → reading
        self.rapl_before = {}
        self.passwd = {}
        self.passwd_round = -99
        self.ncpu = os.cpu_count() or 1
        self.io_before = None

    # ── the box ──
    def discover_container(self):
        name = "rete11-" + self.box
        try:
            o = subprocess.run(["podman", "inspect", name, "--format",
                                "{{.State.Pid}} {{.State.CgroupPath}} {{.Id}}"],
                               capture_output=True, text=True, timeout=20)
            pid, cg, ident = o.stdout.split()
            return {"name": name, "pid": int(pid), "cgroup": cg, "id": ident[:12]}
        except (OSError, ValueError, subprocess.SubprocessError):
            return None

    def box_names(self):
        if self.round_id - self.passwd_round < 10 and self.passwd:
            return self.passwd
        self.passwd_round = self.round_id
        s = read_file("%s/%d/root/etc/passwd" % (self.proc, self.cont["pid"])) if self.cont else None
        if s:
            self.passwd = {}
            for r in s.splitlines():
                p = r.split(":")
                if len(p) > 2 and p[2].isdigit():
                    self.passwd[int(p[2])] = p[0]
        return self.passwd

    # ── identity of a process (read once, re-checked every 10 rounds) ──
    def identity(self, pid, key):
        i = self.info.get(key)
        if i and self.round_id - i["round_id"] < 10:
            return i
        cg = (read_file("%s/%d/cgroup" % (self.proc, pid)) or "").strip()
        cg = cg.split("::", 1)[1] if "::" in cg else cg
        if i is None:
            cmd = (read_file("%s/%d/cmdline" % (self.proc, pid)) or "").replace("\0", " ")
            try:
                exe = os.path.basename(os.readlink("%s/%d/exe" % (self.proc, pid)))
            except OSError:
                exe = None
            i = {"cmd": cmd, "exe": exe}
        # ⛔ The REAL uid from `status`, not the owner of /proc/<pid>: `[M]` 25 Sep,
        #   remotix's child is non-«dumpable» and its folder in /proc
        #   appears owned by ROOT — it ended up in the parent instead of the tenant.  And it is
        #   re-read every 10 rounds: the child is born root and then drops its privileges.
        m = re.search(r"^Uid:\s+(\d+)", read_file("%s/%d/status" % (self.proc, pid)) or "", re.M)
        i["uid"] = int(m.group(1)) if m else i.get("uid", -1)
        i["cg"], i["round_id"] = cg, self.round_id
        self.info[key] = i
        return i

    def fd_drm(self, pid, key):
        if key in self.drm_fd and self.round_id - self.drm_eta.get(key, -99) < 10:
            return self.drm_fd[key]
        fds = []
        base = "%s/%d/fd" % (self.proc, pid)
        try:
            for e in os.scandir(base):
                try:
                    if os.readlink(e.path).startswith("/dev/dri/"):
                        fds.append(e.name)
                except OSError:
                    pass
        except OSError:
            pass
        self.drm_fd[key], self.drm_eta[key] = fds, self.round_id
        return fds

    # ── /sys ──
    def cg_box(self):
        if not self.cont:
            return None
        b = self.cgroot + self.cont["cgroup"]
        s = read_file(b + "/cpu.stat")
        if s is None:
            return None
        u = re.search(r"usage_usec (\d+)", s)
        m = read_file(b + "/memory.current")
        ms = read_file(b + "/memory.stat") or ""
        a = re.search(r"^anon (\d+)", ms, re.M)
        pc = read_file(b + "/pids.current")
        return {"usec": int(u.group(1)) if u else None,
                "mem": int(m) if m and m.strip().isdigit() else None,
                "anon": int(a.group(1)) if a else None,
                "pids": int(pc) if pc and pc.strip().isdigit() else None}

    def cards(self, dt):
        out = {}
        base = self.sys + "/class/drm"
        try:
            names = sorted(n for n in os.listdir(base) if re.match(r"^card\d+$", n))
        except OSError:
            names = []
        for n in names:
            d = base + "/" + n
            try:
                pdev = os.path.basename(os.path.realpath(d + "/device"))
                drv = os.path.basename(os.path.realpath(d + "/device/driver"))
            except OSError:
                continue
            s = {"card": n, "driver": drv}

            def num(p, factor=1.0):
                v = read_file(p)
                try:
                    return round(float(v.strip()) * factor, 1)
                except (AttributeError, ValueError):
                    return None
            if drv in ("i915", "xe"):
                s["freq_mhz"] = num(d + "/gt_cur_freq_mhz")
                s["freq_cur_mhz"] = num(d + "/gt_act_freq_mhz")
                if s["freq_mhz"] is None:
                    s["freq_mhz"] = num(d + "/gt/gt0/rps_cur_freq_mhz")
                    s["freq_cur_mhz"] = num(d + "/gt/gt0/rps_act_freq_mhz")
                reasons = []
                for p in sorted(_glob(d + "/gt/gt0", "throttle_reason_")):
                    r = os.path.basename(p)[len("throttle_reason_"):]
                    if r != "status" and (read_file(p) or "0").strip() not in ("0", ""):
                        reasons.append(r)
                s["strozzatura"] = reasons
                t, source = self.temp_cpu()
                s["temp_c"], s["temp_source"] = t, source
            elif drv == "amdgpu":
                s["busy_pct"] = num(d + "/device/gpu_busy_percent")
                s["vram_used_mb"] = num(d + "/device/mem_info_vram_used", 1 / 2 ** 20)
                s["vram_total_mb"] = num(d + "/device/mem_info_vram_total", 1 / 2 ** 20)
                for h in _glob(d + "/device/hwmon", "hwmon"):
                    s["temp_c"] = num(h + "/temp1_input", 0.001)
                    s["temp_giunzione_c"] = num(h + "/temp2_input", 0.001)
                    s["temp_source"] = "amdgpu hwmon (edge/junction)"
                    s["freq_mhz"] = num(h + "/freq1_input", 1e-6)
                    p = num(h + "/power1_average", 1e-6)
                    s["power_w"] = p if p is not None else num(h + "/power1_input", 1e-6)
                    break
                sc = read_file(d + "/device/pp_dpm_sclk") or ""
                m = re.search(r"(\d+)Mhz \*", sc)
                if m:
                    s["freq_cur_mhz"] = float(m.group(1))
            out[pdev] = s
        # the RAPL power (Intel): package and uncore (= the integrated graphics)
        for p in _glob(self.sys + "/class/powercap", "intel-rapl:"):
            name = (read_file(p + "/name") or "").strip()
            e = read_file(p + "/energy_uj")
            if not e or not name:
                continue
            e = int(e)
            pr = self.rapl_before.get(name)
            self.rapl_before[name] = e
            if pr is not None and dt > 0 and e >= pr:
                w = round((e - pr) / 1e6 / dt, 2)
                for s in out.values():
                    if s["driver"] in ("i915", "xe"):
                        if name == "uncore":
                            s["power_w"] = w
                        elif name == "package-0":
                            s["package_power_w"] = w
        return out

    def temp_cpu(self):
        for h in _glob(self.sys + "/class/hwmon", "hwmon"):
            if (read_file(h + "/name") or "").strip() == "coretemp":
                v = read_file(h + "/temp1_input")
                try:
                    return round(int(v) / 1000, 1), "coretemp CPU package (the iGPU has no sensor of its own)"
                except (TypeError, ValueError):
                    pass
        return None, None

    # ── one sample ──
    def sample(self):
        t0cpu = time.process_time()
        t0 = self.clock()
        dt = (t0 - self.t_before) if self.t_before is not None else None
        self.round_id += 1
        warnings = []
        if self.cont is None:
            warnings.append("⛔ box rete11-%s NOT found (podman inspect): enclosures remotix and "
                          "sessioni not measurable" % self.box)
        pref = self.cont["cgroup"] if self.cont else None
        names = self.box_names() if self.cont else {}

        # 1. all the processes
        procs = {}
        for n in os.listdir(self.proc):
            if not n.isdigit():
                continue
            pid = int(n)
            s = stat_pid(self.proc, pid)
            if s:
                procs[pid] = s
        # 2. the browsers: roots with the mark and their descendants
        children = {}
        for pid, s in procs.items():
            children.setdefault(s["ppid"], []).append(pid)
        rec = {}
        browser_roots = {}
        for pid, s in procs.items():
            ch = (pid, s["startup"])
            i = self.identity(pid, ch)
            s["i"] = i
            s["ch"] = ch
            inside = bool(pref) and (i["cg"] == pref or i["cg"].startswith(pref + "/"))
            s["inside"] = inside
            if inside and self.system == "xrdp":
                if (i["exe"] in XRDP_EXE or (i["exe"] is None and s["comm"] in XRDP_EXE)
                        or "/xrdp.service" in i["cg"] or "/xrdp-sesman.service" in i["cg"]):
                    rec[pid] = "remotix"
                elif i["uid"] >= 1000 and i["uid"] != 65534:
                    rec[pid] = "sessions"
                else:
                    rec[pid] = "other_box"
            elif inside:
                if (i["cg"].endswith("/rete11-server.service")
                        or "/rete11-server.service/" in i["cg"]
                        or i["exe"] == "remotix" or (i["exe"] is None and s["comm"] == "remotix")):
                    rec[pid] = "remotix"
                elif i["uid"] >= 1000 and i["uid"] != 65534:
                    rec[pid] = "sessions"
                else:
                    rec[pid] = "other_box"
            elif self.marks and any(g in i["cmd"] for g in self.marks):
                browser_roots[pid] = "chrome" if "remotix-cr-" in i["cmd"] else (
                    "firefox" if "remotix-ff-" in i["cmd"] else (
                        "freerdp" if "remotix-rdp-" in i["cmd"] else "browser"))
        # the descendants (one level at a time: the root wins over a child with the mark)
        root_of = {}
        stack = [(r, r) for r in browser_roots
                if procs[r]["ppid"] not in browser_roots and not _ancestor_in(procs, r, browser_roots)]
        while stack:
            pid, r = stack.pop()
            if pid in root_of:
                continue
            root_of[pid] = r
            rec[pid] = "browser"
            for c in children.get(pid, []):
                if not procs[c]["inside"]:
                    stack.append((c, r))
        for pid, s in procs.items():
            if pid not in rec and not s["inside"] and s["comm"] in ("labwc", "Xvfb") \
                    and s["i"]["uid"] >= 1000:
                rec[pid] = "labwc_client"

        # 3. CPU, memory, graphics fds per process
        tot = {k: _empty() for k in ENCLOSURES + EXTRA}
        per_in = {"remotix": {}, "sessions": {}}
        per_br = {}
        parent = _empty()
        new_cpu = {}
        for pid, s in procs.items():
            ch = s["ch"]
            new_cpu[ch] = s["cpu"]
            r = rec.get(pid)
            if r is None:
                continue
            d_cpu = 0.0
            if dt and ch in self.cpu_before:
                d_cpu = max(0, s["cpu"] - self.cpu_before[ch]) / CLK / dt
            if ch not in self.pss or (pid + self.round_id) % self.pss_every == 0:
                v = pss_kb(self.proc, pid)
                if v is not None:
                    self.pss[ch] = v
            pss = self.pss.get(ch)
            s["d_cpu"] = d_cpu
            entry = [tot[r]]
            if r in ("remotix", "sessions"):
                u = s["i"]["uid"]
                name = names.get(u, "uid%d" % u)
                if r == "remotix" and u < 1000:
                    entry.append(parent)
                else:
                    entry.append(per_in[r].setdefault(name, _empty(uid=u)))
                s["tenant"] = name if (u >= 1000 and u != 65534) else None
            elif r == "browser":
                rd = root_of[pid]
                entry.append(per_br.setdefault(rd, _empty(pid=rd, type=browser_roots[rd],
                                                         profile=_profile(procs[rd]["i"]["cmd"]))))
            for v in entry:
                v["cpu_core"] += d_cpu
                v["processes"] += 1
                v["thread"] += s["thread"]
                v["rss_mb"] += s["rss_kb"] / 1024
                if pss is None:
                    v["pss_missing"] += 1
                else:
                    v["pss_mb"] += pss / 1024
        self.cpu_before = new_cpu
        living = set(new_cpu)
        for dct in (self.pss, self.info, self.drm_fd, self.drm_eta):
            for k in [k for k in dct if k not in living]:
                del dct[k]

        # 4. the graphics card, per client (deduplicated) and per process
        dt_ns = dt * 1e9 if dt else 0
        seen_items = {}
        proc_gpu = {}
        for pid in sorted(procs):
            s = procs[pid]
            if not (s["inside"] or pid in rec):
                continue
            for fd in self.fd_drm(pid, s["ch"]):
                txt = read_file("%s/%d/fdinfo/%s" % (self.proc, pid, fd))
                d = read_fdinfo(txt or "")
                if not d:
                    continue
                k = (d["pdev"], d["client"]) if d["client"] else (pid, s["startup"], fd)
                if k in seen_items:
                    continue                  # the same client: once only
                seen_items[k] = (pid, d)
        gpu_cards = {}
        new_drm = {}
        for k, (pid, d) in seen_items.items():
            new_drm[k] = d
            usage = use_client(self.drm_before.get(k), d, dt_ns)
            s = procs[pid]
            r = rec.get(pid, "other_box" if s["inside"] else None)
            scr = gpu_cards.setdefault(d["pdev"], {"engines": {}, "memoria_mb": {}, "client": 0})
            scr["client"] += 1
            for m, p in usage.items():
                scr["engines"][m] = scr["engines"].get(m, 0) + p
            for reg, b in d["memory"].items():
                scr["memoria_mb"][reg] = scr["memoria_mb"].get(reg, 0) + b / 2 ** 20
            mem_mb = sum(d["memory"].values()) / 2 ** 20
            if r:
                dest = [tot[r]]
                if r in ("remotix", "sessions"):
                    u = s["i"]["uid"]
                    name = names.get(u, "uid%d" % u)
                    dest.append(parent if (r == "remotix" and u < 1000)
                                else per_in[r].setdefault(name, _empty(uid=u)))
                elif r == "browser":
                    dest.append(per_br[root_of[pid]])
                for v in dest:
                    for m, p in usage.items():
                        c = category(m)
                        v["gpu"][c] = v["gpu"].get(c, 0) + p
                    v["gpu_mem_mb"] += mem_mb
            if any(p >= 0.05 for p in usage.values()):
                pg = proc_gpu.setdefault((pid, d["pdev"]), {
                    "pid": pid, "comm": s["comm"], "recinto": r,
                    "tenant": s.get("tenant"), "pdev": d["pdev"], "engines": {}})
                for m, p in usage.items():
                    pg["engines"][m] = pg["engines"].get(m, 0) + p
        proc_gpu = [dict(v, engines={m: round(p, 2) for m, p in v["engines"].items() if p >= 0.05})
                    for _, v in sorted(proc_gpu.items())]
        self.drm_before = new_drm

        # 5. machine, box, cards
        st = (read_file(self.proc + "/stat") or "cpu 0 0 0 0").splitlines()[0].split()[1:]
        st = [int(x) for x in st[:8]]
        occ, tut = sum(st) - st[3] - st[4], sum(st)
        mac = {"cpu_core": None, "cpu_pct": None}
        if self.cpu_mac_before and tut > self.cpu_mac_before[1]:
            f = (occ - self.cpu_mac_before[0]) / (tut - self.cpu_mac_before[1])
            mac["cpu_pct"] = round(100 * f, 1)
            mac["cpu_core"] = round(f * self.ncpu, 2)
        self.cpu_mac_before = (occ, tut)
        la = (read_file(self.proc + "/loadavg") or "0 0 0 0/0 0").split()
        mac["load"] = [float(x) for x in la[:3]]
        mac["processes"] = len(procs)
        mac["thread"] = sum(s["thread"] for s in procs.values())
        mi = read_file(self.proc + "/meminfo") or ""
        mt = re.search(r"MemTotal:\s+(\d+)", mi)
        ma = re.search(r"MemAvailable:\s+(\d+)", mi)
        if mt and ma:
            mac["mem_total_mb"] = round(int(mt.group(1)) / 1024)
            mac["mem_available_mb"] = round(int(ma.group(1)) / 1024)
            mac["mem_used_mb"] = mac["mem_total_mb"] - mac["mem_available_mb"]
        cg = self.cg_box()
        box_stats = None
        if cg:
            box_stats = {"mem_mb": round(cg["mem"] / 2 ** 20, 1) if cg["mem"] is not None else None,
                    "anon_mb": round(cg["anon"] / 2 ** 20, 1) if cg["anon"] is not None else None,
                    "pids": cg["pids"], "cpu_core": None}
            if dt and self.cg_before and cg["usec"] is not None and self.cg_before["usec"] is not None:
                box_stats["cpu_core"] = round(max(0, cg["usec"] - self.cg_before["usec"]) / 1e6 / dt, 3)
        self.cg_before = cg
        # the exact CPU of the sessions: the cgroup minus the others' long processes
        if box_stats and box_stats["cpu_core"] is not None:
            sess = box_stats["cpu_core"] - tot["remotix"]["cpu_core"] - tot["other_box"]["cpu_core"]
            attr = tot["sessions"]["cpu_core"]
            tot["sessions"]["cpu_core_processes"] = attr
            tot["sessions"]["cpu_core"] = max(sess, attr)
            tot["sessions"]["cpu_unattributed"] = max(0.0, sess - attr)
        g = self.cards(dt or 0)
        for pdev, scr in gpu_cards.items():
            s = g.setdefault(pdev, {"card": None, "driver": None})
            s["engines"] = {m: round(p, 2) for m, p in sorted(scr["engines"].items())}
            cats = {}
            for m, p in scr["engines"].items():
                c = category(m)
                cats[c] = cats.get(c, 0) + p
            s["categories"] = {c: round(p, 2) for c, p in sorted(cats.items())}
            s["client_memory_mb"] = {r: round(v, 1) for r, v in scr["memoria_mb"].items()}
            s["client"] = scr["client"]

        # 6. empty enclosures are STATED (an empty enclosure is not a healthy enclosure)
        for r in ENCLOSURES:
            if tot[r]["processes"] == 0:
                warnings.append("⚠ enclosure %s EMPTY: no process found" % r)
        if self.system != "xrdp" and self.cont and tot["remotix"]["processes"] and not parent["processes"]:
            warnings.append("⚠ remotix: no process in the cgroup rete11-server.service (the parent?)")
        if self.system == "xrdp":
            pids_rx = sorted(p for p, r in rec.items() if r == "remotix" and procs[p]["comm"] == "xrdp"
                             and procs.get(procs[p]["ppid"], {}).get("comm") != "xrdp")
        else:
            pids_rx = sorted(p for p, r in rec.items() if r == "remotix"
                             and "rete11-server.service" in procs[p]["i"]["cg"]
                             and rec.get(procs[p]["ppid"]) != "remotix")
        if any(v["pss_missing"] for v in tot.values()):
            warnings.append("⚠ PSS unreadable for %d processes (not root?)"
                          % sum(v["pss_missing"] for v in tot.values()))

        rec_out = {}
        for r in ENCLOSURES + EXTRA:
            rec_out[r] = _clean(tot[r])
        rec_out["remotix"]["parent"] = _clean(parent)
        for r in ("remotix", "sessions"):
            rec_out[r]["per_tenant"] = {n: _clean(v) for n, v in sorted(per_in[r].items())}
        rec_out["browser"]["per_browser"] = [_clean(v) for _, v in sorted(per_br.items())]

        self.t_before = t0
        line = {"type": "sample", "t": round(time.time(), 3),
                "time": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "dt_s": round(dt, 3) if dt else None, "box": self.box,
                "machine": mac, "box_cg": box_stats, "enclosures": rec_out, "gpu": g,
                "gpu_processes": proc_gpu, "remotix_pid": pids_rx[0] if pids_rx else None,
                "warnings": warnings,
                "misuratore": {"ms": round((self.clock() - t0) * 1000, 1),
                               "cpu_s": round(time.process_time() - t0cpu, 4)}}
        return line

    def header(self):
        ci = read_file(self.proc + "/cpuinfo") or ""
        m = re.search(r"model name\s*:\s*(.+)", ci)
        return {"type": "header", "t": round(time.time(), 3),
                "time": time.strftime("%Y-%m-%dT%H:%M:%S"), "box": self.box,
                "container": self.cont, "cpu": m.group(1).strip() if m else None,
                "ncpu": self.ncpu, "kernel": os.uname().release,
                "cards": {p: {"card": s["card"], "driver": s["driver"]}
                           for p, s in self.cards(0).items()},
                "browser_signs": list(self.marks), "pss_every_s": self.pss_every,
                "euid": os.geteuid()}


def _ancestor_in(procs, pid, together):
    seen = set()
    p = procs[pid]["ppid"]
    while p in procs and p not in seen and p > 1:
        if p in together:
            return True
        seen.add(p)
        p = procs[p]["ppid"]
    return False


def _profile(cmd):
    m = re.search(r"(/[^ ]*remotix-(?:ff|cr)-[^ /]*)", cmd)
    return m.group(1) if m else None


def _glob(d, prefix):
    try:
        return [d + "/" + n for n in sorted(os.listdir(d)) if n.startswith(prefix)]
    except OSError:
        return []


def _empty(**extra):
    v = {"cpu_core": 0.0, "processes": 0, "thread": 0, "rss_mb": 0.0, "pss_mb": 0.0,
         "pss_missing": 0, "gpu": {}, "gpu_mem_mb": 0.0}
    v.update(extra)
    return v


def _clean(v):
    o = dict(v)
    for k in ("cpu_core", "cpu_core_processes", "cpu_unattributed"):
        if k in o and o[k] is not None:
            o[k] = round(o[k], 3)
    for k in ("rss_mb", "pss_mb", "gpu_mem_mb"):
        o[k] = round(o[k], 1)
    o["gpu"] = {c: round(p, 2) for c, p in sorted(o["gpu"].items())}
    if not o.get("pss_missing"):
        o.pop("pss_missing", None)
    return o


# ─────────────────────────────── loop ──────────────────────────────────────
def runs(o):
    os.makedirs(o.dir, exist_ok=True)
    c = Sampler(o.box, browser_marks=o.browser_marks.split(","), pss_every=o.pss_every,
                     system=o.system)
    stopped = {"yes": False}

    def halt(*_):
        stopped["yes"] = True
    signal.signal(signal.SIGTERM, halt)
    signal.signal(signal.SIGINT, halt)
    out = open(os.path.join(o.dir, "resources.jsonl"), "a", encoding="utf-8")
    out.write(json.dumps(c.header(), ensure_ascii=False) + "\n")
    out.flush()
    fine = time.monotonic() + o.duration if o.duration else None
    upcoming = time.monotonic()
    c.sample()                       # the first one serves only as «before»
    while not stopped["yes"]:
        upcoming += o.interval
        time.sleep(max(0.0, upcoming - time.monotonic()))
        if stopped["yes"]:
            break
        r = c.sample()
        out.write(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n")
        out.flush()
        if fine and time.monotonic() >= fine:
            break
        if time.monotonic() - upcoming > 5 * o.interval:
            upcoming = time.monotonic()     # we fell behind: no catching up
    out.close()
    return 0


# ─────────────────────────────── certify ─────────────────────────────────
FDI_I915 = """pos:\t0
flags:\t02100002
drm-driver:\ti915
drm-client-id:\t{cid}
drm-pdev:\t0000:00:02.0
drm-total-system0:\t{mem} KiB
drm-resident-system0:\t{mem} KiB
drm-engine-render:\t{r} ns
drm-engine-copy:\t0 ns
drm-engine-video:\t{v} ns
drm-engine-capacity-video:\t2
drm-engine-video-enhance:\t0 ns
"""
FDI_AMD = """drm-driver:\tamdgpu
drm-client-id:\t{cid}
drm-pdev:\t0000:03:00.0
drm-memory-vram:\t{vram} KiB
drm-memory-gtt:\t0 KiB
drm-engine-gfx:\t{g} ns
drm-engine-enc:\t{e} ns
drm-engine-dec:\t0 ns
"""
FDI_XE = """drm-driver:\txe
drm-client-id:\t{cid}
drm-pdev:\t0000:00:02.0
drm-cycles-rcs:\t{c}
drm-total-cycles-rcs:\t{t}
"""


class Fake:
    """A fake /proc and /sys in a folder: the processes are written, two
    samples are taken with a fake clock, and the number is checked."""

    def __init__(self):
        self.d = tempfile.mkdtemp(prefix="16-risorse-cert-")
        self.proc = self.d + "/proc"
        self.sys = self.d + "/sys"
        self.t = 1000.0
        os.makedirs(self.proc)
        os.makedirs(self.sys + "/fs/cgroup/machine.slice/libpod-x.scope")
        os.makedirs(self.sys + "/class/drm")
        self.machine_stat(0, 0)
        with open(self.proc + "/loadavg", "w") as f:
            f.write("1.00 0.50 0.25 2/300 999\n")
        with open(self.proc + "/meminfo", "w") as f:
            f.write("MemTotal: 32000000 kB\nMemAvailable: 16000000 kB\n")
        self.cg(0)

    def cg(self, usec):
        b = self.sys + "/fs/cgroup/machine.slice/libpod-x.scope"
        with open(b + "/cpu.stat", "w") as f:
            f.write("usage_usec %d\n" % usec)
        with open(b + "/memory.current", "w") as f:
            f.write("1048576000\n")

    def machine_stat(self, occ, idle):
        with open(self.proc + "/stat", "w") as f:
            f.write("cpu %d 0 0 %d 0 0 0 0 0 0\n" % (occ, idle))

    def process(self, pid, comm, uid, cg, ppid=1, cpu=0, cmd="", exe=None, pss=1024,
                 fdinfo=None):
        p = "%s/%d" % (self.proc, pid)
        os.makedirs(p + "/fd", exist_ok=True)
        os.makedirs(p + "/fdinfo", exist_ok=True)
        with open(p + "/stat", "w") as f:
            f.write("%d (%s) S %d 0 0 0 0 0 0 0 0 0 %d 0 0 0 20 0 3 0 777 0 2560 0 0\n"
                    % (pid, comm, ppid, cpu))
        with open(p + "/cgroup", "w") as f:
            f.write("0::%s\n" % cg)
        with open(p + "/status", "w") as f:
            f.write("Name:\t%s\nUid:\t%d\t%d\t%d\t%d\n" % (comm, uid, uid, uid, uid))
        with open(p + "/cmdline", "w") as f:
            f.write(cmd.replace(" ", "\0"))
        with open(p + "/smaps_rollup", "w") as f:
            f.write("Rss: 9999 kB\nPss: %d kB\n" % pss)
        if exe and not os.path.lexists(p + "/exe"):
            os.symlink("/opt/remotix/" + exe, p + "/exe")
        # ⚠ the folder's owner stays OURS (like a non-«dumpable» process,
        #   which in /proc appears owned by root): the uid is read from status.
        for fd, txt in (fdinfo or {}).items():
            if not os.path.lexists(p + "/fd/" + fd):
                os.symlink("/dev/dri/renderD128", p + "/fd/" + fd)
            with open(p + "/fdinfo/" + fd, "w") as f:
                f.write(txt)

    def remove(self, pid):
        shutil.rmtree("%s/%d" % (self.proc, pid), ignore_errors=True)

    def clock(self):
        return self.t


def certify():
    outcomes = []

    def look(name, ok, detail):
        outcomes.append(ok)
        print("  %s %s — %s" % ("PASS" if ok else "FAIL", name, detail))

    CGC = "/machine.slice/libpod-x.scope"
    SRV = CGC + "/container/system.slice/rete11-server.service"
    SESS = CGC + "/container/user.slice/user-4013.slice/session-c5.scope"
    GUEST = "/user.slice/user-1000.slice/session-1.scope"

    def fresh():
        return Fake()

    def sampler_obj(F, **kw):
        c = Sampler("kde", proc=F.proc, sys_=F.sys, clock=F.clock,
                         container={"name": "rete11-kde", "pid": 1, "cgroup": CGC, "id": "x"},
                         **kw)
        c._restore = lambda: None
        return c

    print("16-resources --certify  (fake /proc and /sys, fake clock)")
    # ── 1. i915: render 250 ms over 1 s ⇒ 25 %; video 1 s on two engines ⇒ 50 % ──
    F = fresh()
    F.machine_stat(0, 0)
    F.process(10, "remotix", 0, SRV, cmd="/opt/remotix/remotix --port 8512", exe="remotix")
    F.process(20, "remotix", 4013, SESS, ppid=10, exe="remotix",
               fdinfo={"7": FDI_I915.format(cid=5, mem=2048, r=0, v=0)})
    F.process(21, "kwin_wayland", 4013, SESS, exe="kwin_wayland",
               fdinfo={"9": FDI_I915.format(cid=6, mem=1024, r=0, v=0)})
    F.process(30, "firefox", 1000, GUEST, cmd="firefox --profile /tmp/remotix-ff-abc", exe="firefox")
    F.process(31, "Web Content", 1000, GUEST, ppid=30, cmd="firefox -contentproc 7", exe="firefox")
    F.process(40, "firefox", 1000, GUEST, cmd="firefox --profile /home/nicfio/.mozilla/x", exe="firefox")
    c = sampler_obj(F)
    c.sample()
    F.t += 1.0
    F.machine_stat(1000, 1000)
    F.cg(2_000_000)
    F.process(10, "remotix", 0, SRV, cpu=50, exe="remotix")
    F.process(20, "remotix", 4013, SESS, ppid=10, cpu=100, exe="remotix",
               fdinfo={"7": FDI_I915.format(cid=5, mem=2048, r=0, v=1_000_000_000)})
    F.process(21, "kwin_wayland", 4013, SESS, cpu=20, exe="kwin_wayland",
               fdinfo={"9": FDI_I915.format(cid=6, mem=1024, r=250_000_000, v=0)})
    r = c.sample()
    c._restore()
    rx, se, br = r["enclosures"]["remotix"], r["enclosures"]["sessions"], r["enclosures"]["browser"]
    look("fdinfo i915, video on 2 engines", abs(rx["gpu"].get("video", -1) - 50.0) < 0.01,
           "remotix video %s %% (expected 50: 1 s busy over 1 s, capacity 2)" % rx["gpu"].get("video"))
    look("fdinfo i915, drawing", abs(se["gpu"].get("draw", -1) - 25.0) < 0.01,
           "sessioni drawing %s %% (expected 25)" % se["gpu"].get("draw"))
    look("graphics memory per client", abs(rx["gpu_mem_mb"] - 2.0) < 0.01,
           "remotix %s MB (expected 2: 2048 KiB resident)" % rx["gpu_mem_mb"])
    look("the three enclosures", (rx["processes"], se["processes"], br["processes"]) == (2, 1, 2),
           "remotix %d (parent + child) · sessioni %d · browser %d (the user's Firefox "
           "WITHOUT a mark stays out)" % (rx["processes"], se["processes"], br["processes"]))
    look("per tenant", "uid4013" in rx["per_tenant"] and "uid4013" in se["per_tenant"],
           "remotix's child and session attributed to tenant 4013")
    look("CPU per process", abs(rx["cpu_core"] - 150 / CLK) < 1e-3,
           "remotix %.3f cores (expected %.3f: 150 ticks in 1 s)" % (rx["cpu_core"], 150 / CLK))
    look("CPU of the sessions from the cgroup (short processes)",
           abs(se["cpu_core"] - (2.0 - 150 / CLK)) < 1e-3
           and abs(se["cpu_unattributed"] - (2.0 - 170 / CLK)) < 1e-3,
           "sessioni %.3f cores = box 2.000 − remotix; unattributed %.3f (what the "
           "cgroup saw and no live process carries: the short processes)"
           % (se["cpu_core"], se["cpu_unattributed"]))
    look("machine", r["machine"]["cpu_pct"] == 50.0, "cpu %s %% (expected 50)" % r["machine"]["cpu_pct"])
    look("PSS", abs(se["pss_mb"] - 1.0) < 0.01, "sessioni %s MB (expected 1)" % se["pss_mb"])
    look("no warning when the enclosures are full", not r["warnings"], str(r["warnings"]))
    look("the pid of the remotix parent", r["remotix_pid"] == 10, "remotix_pid %s (expected 10)" % r["remotix_pid"])
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 2. FAULT: the same client on two fds and two processes ⇒ once only ──
    F = fresh()
    txt0 = FDI_I915.format(cid=9, mem=0, r=0, v=0)
    txt1 = FDI_I915.format(cid=9, mem=0, r=500_000_000, v=0)
    F.process(10, "remotix", 0, SRV, exe="remotix")
    F.process(20, "labwc", 4013, SESS, fdinfo={"5": txt0, "6": txt0})
    F.process(21, "child", 4013, SESS, ppid=20, fdinfo={"5": txt0})
    F.process(30, "chrome", 1000, GUEST, cmd="chrome --user-data-dir=/tmp/remotix-cr-1")
    c = sampler_obj(F)
    c.sample()
    F.t += 1.0
    F.process(20, "labwc", 4013, SESS, fdinfo={"5": txt1, "6": txt1})
    F.process(21, "child", 4013, SESS, ppid=20, fdinfo={"5": txt1})
    r = c.sample()
    c._restore()
    v = r["enclosures"]["sessions"]["gpu"].get("draw")
    look("duplicated client counted ONCE", v is not None and abs(v - 50.0) < 0.01,
           "drawing %s %% (expected 50; counted three times it would give 150)" % v)
    look("Chrome browser recognised from the profile",
           r["enclosures"]["browser"]["per_browser"][:1] and
           r["enclosures"]["browser"]["per_browser"][0]["type"] == "chrome", "")
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 3. amdgpu and xe: different key names, same categories ──
    F = fresh()
    F.process(10, "remotix", 0, SRV, exe="remotix",
               fdinfo={"7": FDI_AMD.format(cid=1, vram=4096, g=0, e=0),
                       "8": FDI_XE.format(cid=2, c=0, t=1000)})
    F.process(20, "kwin", 4013, SESS)
    F.process(30, "firefox", 1000, GUEST, cmd="firefox --profile /tmp/remotix-ff-z")
    c = sampler_obj(F)
    c.sample()
    F.t += 2.0
    F.process(10, "remotix", 0, SRV, exe="remotix",
               fdinfo={"7": FDI_AMD.format(cid=1, vram=4096, g=500_000_000, e=1_000_000_000),
                       "8": FDI_XE.format(cid=2, c=300, t=2000)})
    r = c.sample()
    c._restore()
    g = r["enclosures"]["remotix"]["gpu"]
    look("amdgpu gfx/enc + xe cycles",
           abs(g.get("draw", -1) - (25.0 + 30.0)) < 0.01 and abs(g.get("video", -1) - 50.0) < 0.01,
           "drawing %s %% (expected 25 gfx + 30 xe rcs) · video %s %% (expected 50 enc)"
           % (g.get("draw"), g.get("video")))
    look("VRAM amdgpu (drm-memory-vram)", abs(r["enclosures"]["remotix"]["gpu_mem_mb"] - 4.0) < 0.01,
           "%s MB (expected 4)" % r["enclosures"]["remotix"]["gpu_mem_mb"])
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 4. FAULT: a counter that does not advance ⇒ 0 %, never the last value ──
    F = fresh()
    t = FDI_I915.format(cid=3, mem=0, r=7_000_000_000, v=0)
    F.process(10, "remotix", 0, SRV, exe="remotix", fdinfo={"7": t})
    F.process(20, "kwin", 4013, SESS)
    F.process(30, "firefox", 1000, GUEST, cmd="firefox --profile /tmp/remotix-ff-z")
    c = sampler_obj(F)
    c.sample()
    F.t += 1.0
    r = c.sample()
    c._restore()
    look("idle engine ⇒ 0 %", r["enclosures"]["remotix"]["gpu"].get("draw") == 0.0,
           "drawing %s %%" % r["enclosures"]["remotix"]["gpu"].get("draw"))
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 5. FAULT: a reused pid (same number, other start) gives no jumps ──
    F = fresh()
    F.process(10, "remotix", 0, SRV, exe="remotix", cpu=100000)
    F.process(20, "kwin", 4013, SESS)
    F.process(30, "firefox", 1000, GUEST, cmd="firefox --profile /tmp/remotix-ff-z")
    c = sampler_obj(F)
    c.sample()
    F.t += 1.0
    F.remove(10)
    F.process(10, "remotix", 0, SRV, exe="remotix", cpu=100500)
    with open(F.proc + "/10/stat") as f:
        s = f.read().replace(" 777 ", " 888 ")
    with open(F.proc + "/10/stat", "w") as f:
        f.write(s)
    r = c.sample()
    c._restore()
    look("reused pid: no negative or giant CPU", r["enclosures"]["remotix"]["cpu_core"] == 0.0,
           "remotix %s cores (the new process starts from zero; mistaken for the old one it would give 5)" % r["enclosures"]["remotix"]["cpu_core"])
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 6. FAULT: empty enclosures are REPORTED ──
    F = fresh()
    F.process(20, "kwin", 4013, SESS)
    c = sampler_obj(F)
    c.sample()
    F.t += 1.0
    r = c.sample()
    c._restore()
    a = " | ".join(r["warnings"])
    look("empty remotix enclosure reported", "enclosure remotix EMPTY" in a, a)
    look("empty browser enclosure reported", "enclosure browser EMPTY" in a, "")
    look("full sessioni enclosure NOT reported", "sessioni EMPTY" not in a, "")
    shutil.rmtree(F.d, ignore_errors=True)

    # ── 7. FAULT: the box that is not there ──
    c = Sampler("nessuna", proc=F.proc if os.path.isdir(F.proc) else "/proc",
                     container=None, discover=False)
    r = c.sample()
    look("missing box reported", any("NOT found" in x for x in r["warnings"]),
           r["warnings"][0] if r["warnings"] else "")

    n = len(outcomes)
    ok = sum(outcomes)
    print("CERTIFICATION %s — %d of %d" % ("PASS" if ok == n else "FAIL", ok, n))
    return 0 if ok == n else 1


def main():
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--box", choices=("gnome", "kde", "xfce", "lxqt", "gnome-xrdp", "kde-xrdp",
                                         "xfce-xrdp", "lxqt-xrdp"))
    a.add_argument("--system", choices=("remotix", "xrdp"), default="remotix",
                   help="xrdp: the «remotix» enclosure is xrdp (phases/20 §7.4)")
    a.add_argument("--dir")
    a.add_argument("--interval", type=float, default=1.0)
    a.add_argument("--duration", type=float, default=0)
    a.add_argument("--pss-every", type=int, default=5)
    a.add_argument("--browser-marks", default=",".join(BROWSER_MARKS))
    a.add_argument("--certify", action="store_true")
    o = a.parse_args()
    if o.certify:
        return certify()
    if not o.box or not o.dir:
        a.error("--box and --dir are needed (or --certify)")
    if os.geteuid() != 0:
        print("⚠ 16-resources is not running as root: PSS and fdinfo of the other users will be "
              "unreadable (and it will say so in `warnings`)", file=sys.stderr)
    return runs(o)


if __name__ == "__main__":
    sys.exit(main())
