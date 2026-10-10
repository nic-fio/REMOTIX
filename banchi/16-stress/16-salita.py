#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
16-salita — A CLIMB IN RUNGS OF PHASE 16 (fasi/16-stress-e-capacita.md §6)
===========================================================================

    (on the server, as nicfio — the client browsers run there, §2)
    python3 16-salita.py --container_box gnome --campaign intel-4k-gnome --gauge 4k
    python3 16-salita.py --container_box lxqt --campaign calibration --gauge 4k --prova
    python3 16-salita.py ... --dry              # the plan, without doing anything
    python3 16-salita.py --container_box kde --campaign amd-4k-kde --gpu_card amd   # §11, the Radeon

    options:  --rungs 1,4,8,12,16  --minutes 10  --last-rung-minutes 30
              --check-min 2  --base-seed 1600  --fps-video F  --video URL
              --ceiling 17  --base-ports 9900  --prova (§13.3: 1,2,4 of 5 min)
              --gpu_card intel|amd  (the card of the BOX, default intel)

THE CARD (§11, two campaigns)
  --gpu_card passes REMOTIX_CARD to `11-accendi.sh turn_on`: ONE card only
  goes into the box, the Intel UHD 770 or the RX 6800, always as
  card0/renderD128.  ⭐ The client browsers (the labwc of 16-compositori.sh and
  Chrome with --render-node-override) stay on the INTEL in both
  campaigns: the client weighs the same, and the Intel/Radeon comparison measures only
  the server.  ⚠ The price, declared: in the Intel campaign client and server
  compete for the same iGPU, in the AMD one they do not — the Radeon's advantage
  also includes «the iGPU is no longer shared».  It is the right question (how much
  the SERVER holds on that card), but it must be written beside the comparison;
  to separate it, the level records `processi_gpu` per card (16-risorse).
  After the rebuild we LOOK that the box's renderD128 is really
  the card asked for (same device number): otherwise, BLOCKED.

WHAT IT DOES
  0. checks that the server is EMPTY: no c16* tenant, no bench
     browser, no session in the box, no other climb — otherwise it
     stops BLOCKED with the reason (code 3);
  1. rebuilds the box FROM SCRATCH (11-accendi.sh turn_on · product · server, like
     15-rifai-scatole.sh) with the server on at `--ceiling` sessions
     (REMOTIX_SESSION_CAP, see 11-accendi.sh) and LOOKS in the log that the
     cap has come into force;
  2. for every rung: turns on the compositors needed (16-compositori.sh),
     brings in the missing actors (16-attore.py, one process per user,
     independent: seed = base-seed + N, base-ports + 10·N, its labwc) —
     one after the other, each when the previous one has the first frame
     (§6: this way birth under load is measured) —, 16-risorse.py for the whole
     level, the minutes of the level at steady work; `--photo-lead-s`
     (30) BEFORE the last `--check-min` minutes SIGUSR1 to the actors (the
     full photo of every canvas) and we wait for the photos to be written: the
     judgement window starts afterwards (if they are late, it slips with the end of the
     level); in the window the short check (16-controllo-corto.py, a
     session of its own, browser alternating between levels; at SIGTERM it stops
     at once); then the server log cut on the
     level, the actors' series cut on the level, livello.json, and
     16-classifica.py;
     ⛔ If the ENTRY fails (compositor or actor that does not start) the level
     is «?» (not good: it stops the climb like an unreadable class), with
     the event and how many entered in livello.json.
     ⭐ nascita.json goes into the level only for the NEW users of the level.
  3. the no-continuation rule (§6, §14): FAIL or significant DEGRADED ⇒
     the level is REPEATED once under the same conditions (clean box,
     the same N users with their seeds); if it is confirmed ⇒ the BISECTION
     between the last good rung and the broken one, every level from a clean box,
     until the precise border is known to one user; then it stops;
  4. the last rung lasts `--last-rung-minutes` (memory leaks, §6);
  5. at the end: actors stopped (SIGTERM: they clean up by themselves), c16* tenants
     cleaned up anyway, compositors off, the server put back with the default
     cap (unless --leave-cap).

THE EVIDENCE (§10) in /media/REMOTIX/misure/fase16/<campaign>/:
    stato.json              the current point, for the coordinator
    salita.jsonl            one row per level (meta + class)
    salita.log              what comes out here, with the times
    actors-<k>/utente-NN/   what the actors write (k: one per clean box)
    livello-NN[-ripetizione]/
        livello.json        meta: campaign, level, users, times, commit,
                            binary, page, kernel, cards, size, cap…
        utente-NN/          stato.jsonl CUT on the level, nascita.json,
                            photos and other files of the actor born in the level
        risorse.jsonl       16-risorse.py
        controllo-corto.json, controllo-corto/
        server.log (the product's registro.log, from the mark) · journal-err.jsonl
        (journalctl -t remotix -p err -o json) · journal-server.log
        (journalctl -u rete11-server) · journal-scatola.log (the whole journal)
        classifica.log      the output of 16-classifica.py

⛔ The thresholds belong to 16-classifica.py (§9, frozen): nothing is judged here,
   we read the class it says.

--system_wide xrdp (fasi/20-le-prestazioni.md §7, 9 Oct 2026) — the SAME climb against xrdp:
  the box is `rete11-<desktop>-xrdp` (Contenitore.xrdp), and before turning it on
  EVERY rete11-*-xrdp is turned off and port 3389 is required free (`--network=host`: one port
  only for the host; on 9 Oct a box left on answered in place of the
  others); xrdp and xrdp-sesman are turned on with Debian's files AS THEY ARE; the clients are
  16-attore-rdp.py in the Xvfb of 16-compositori-rdp.sh; the short check is
  16-attore-rdp.py --check (§7.3, reduced); server.log = the new lines of
  /var/log/xrdp.log and xrdp-sesman.log; livello.json carries the package versions in
  place of commit and binary; 16-classifica.py --system_wide xrdp.  No session
  cap (xrdp has no cap of ours).
  ⛔ §7.7, THE SERVER MUST NOT LOCK UP: the GUARD reads MemAvailable and
  /proc/pressure/memory every 2 s; below 3 GiB free or with «full avg10» above 20 the level is
  closed AT ONCE (SIGTERM to the actors) as FAIL «host resources», without repetition
  (repeating it would mean putting the server back on the edge).  sshd gets
  oom_score_adj −900 (and a drop-in in /run), the clients +800.
"""
import argparse
import datetime
import fcntl
import glob
import hashlib
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
BENCHES = os.path.dirname(HERE)
NETWORK11 = os.environ.get("REMOTIX_NETWORK11", "/media/REMOTIX/rete11")
MEASURES = os.environ.get("REMOTIX_MEASURES_16", "/media/REMOTIX/misure/fase16")
PRODUCT16 = os.environ.get("REMOTIX_PRODUCT_16", "/media/REMOTIX/src/16-prodotto")
PORTS = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}
SCREEN_SIZES = {"4k": (3840, 2160), "3k": (3200, 1800), "2k": (2560, 1440),
                  "fhd": (1920, 1080)}
KNOWN_CARDS = {"8086:4680": "Intel UHD 770 (i5-13500T)", "1002:73bf": "AMD Radeon RX 6800"}
CLASSES = ("GREEN", "DEGRADED", "FAIL")
UID = os.getuid()
RUN = "/run/user/%d" % UID
COMPOSITORS = os.path.join(RUN, "16-compositori")
TENANT_16 = re.compile(r"^c16[0-9]+u[0-9]+$")
COMPOSITORS_RDP = os.path.join(RUN, "16-compositori-rdp")
GUARD_MEM_MB = 3 * 1024           # §7.7: below it, the level is closed
GUARD_PSI_FULL = 20.0             # §7.7: «full avg10» beyond it, the level is closed
XRDP_PACKAGES = ("xrdp", "xorgxrdp", "pipewire-module-xrdp", "xserver-xorg-core", "xfwm4", "openbox",
                  "kwin-x11", "gnome-session-xsession", "firefox-esr", "mesa-va-drivers")
GUEST_XRDP_PACKAGES = ("freerdp3-x11", "xvfb", "python3-xlib", "x11-utils", "python3-pil")
BROWSER_ENV = {
    "XDG_RUNTIME_DIR": RUN, "REMOTIX_NESTED_SCREEN": "1", "REMOTIX_ON_SERVER": "1",
    "MOZ_ENABLE_WAYLAND": "1",
    "REMOTIX_CHROME_OPTIONS": "--ozone-platform=wayland --disable-backgrounding-occluded-windows "
                              "--disable-renderer-backgrounding --disable-background-timer-throttling"}

_print = threading.Lock()
_log_file = None


def now():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def says(msg):
    row = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with _print:
        print(row, flush=True)
        if _log_file:
            _log_file.write(row + "\n")
            _log_file.flush()


def _sudo_password():
    """The server's sudo password: from REMOTIX_SUDO_PASSWORD, or from the «pass:» line of
    ~/SERVER.ssh. ⛔ Never written in the benches: they are in the repository."""
    p = os.environ.get("REMOTIX_SUDO_PASSWORD")
    if p is None:
        try:
            for r in open(os.path.expanduser("~/SERVER.ssh")):
                if r.startswith("pass:"):
                    p = r.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    return (p or "") + "\n"


def sudo(command, seconds=300):
    try:
        r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", command], input=_sudo_password(),
                           capture_output=True, text=True, errors="replace", timeout=seconds)
    except subprocess.TimeoutExpired:
        return None, "(no answer in %d s)" % seconds
    return r.returncode, (r.stdout + r.stderr).strip()


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


def in_box(d, command, seconds=120):
    return sudo("podman exec rete11-%s sh -c %s" % (d, _q(command)), seconds)


def write_json(p, data_v):
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(data_v, f, ensure_ascii=False, indent=1)
    os.replace(p + ".tmp", p)


def md5_8(p, how_many=8):
    try:
        h = hashlib.md5()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()[:how_many]
    except OSError:
        return "?"


def command(argv, seconds=30):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, errors="replace",
                           timeout=seconds)
        return (r.stdout + r.stderr).strip()
    except Exception as e:                       # noqa: BLE001
        return "? (%s)" % e


# ═══════════════════════════════════════════════════════════════════════════
#  THE MACHINE: what is measured (§10, in every row)
# ═══════════════════════════════════════════════════════════════════════════
def cards():
    out = []
    for c in sorted(glob.glob("/sys/class/drm/card[0-9]")):
        try:
            v = open(c + "/device/vendor").read().strip().replace("0x", "")
            dv = open(c + "/device/device").read().strip().replace("0x", "")
            drv = os.path.basename(os.path.realpath(c + "/device/driver"))
        except OSError:
            continue
        pci = os.path.basename(os.path.realpath(c + "/device"))
        idn = "%s:%s" % (v, dv)
        out.append({"gpu_card": KNOWN_CARDS.get(idn, idn), "id": idn, "driver": drv, "pci": pci})
    return out


def meta_machine(o):
    m = {"kernel": os.uname().release,
         "cpu": next((r.split(":", 1)[1].strip() for r in open("/proc/cpuinfo")
                      if r.startswith("model name")), "?"),
         "cards": cards(),
         "prodotto_binario": md5_8(os.path.join(NETWORK11, "product", "remotix")),
         "prodotto_pagina": md5_8(os.path.join(NETWORK11, "product", "pagina.html")),
         "firefox": command(["firefox", "--version"]),
         "chrome": command(["google-chrome", "--version"])}
    try:
        m["commit_banchi"] = open(os.path.join(BENCHES, "..", "VER")).read().strip()
    except OSError:
        m["commit_banchi"] = "?"
    try:
        m["scheda_compositori"] = open(os.path.join(COMPOSITORS, "render")).read().strip()
    except OSError:
        m["scheda_compositori"] = "?"
    # ⭐ the PRODUCT's commit: /media/REMOTIX/src/16-prodotto/VERSIONE, valid only if
    #   the binary there is THE SAME as rete11/prodotto (whole md5)
    m["commit_prodotto"] = None
    b = os.path.join(PRODUCT16, "src", "remotix")
    if os.path.exists(b) and md5_8(b, 32) == md5_8(os.path.join(NETWORK11, "product", "remotix"), 32):
        try:
            m["commit_prodotto"] = open(os.path.join(PRODUCT16, "VER")).read().strip()
        except OSError:
            pass
    # ⭐ phase 20: the label beside the binary, «<commit> <md5 at 8>», written when it is
    #   copied into rete11/prodotto; valid only if the md5 is still that of the binary
    if not m["commit_prodotto"]:
        try:
            commit, md5 = open(os.path.join(NETWORK11, "product", "VER")).read().split()[:2]
            if md5 == md5_8(os.path.join(NETWORK11, "product", "remotix"), 32)[:8]:
                m["commit_prodotto"] = commit
        except (OSError, ValueError):
            pass
    return m


CARD_DRIVER = {"intel": ("i915", "xe"), "amd": ("amdgpu",)}


def card_of(which):
    """The `intel` or `amd` card (dict of cards()) and its render node, by
    PCI address (like 11-accendi.sh).  (card, node) or (None, None)."""
    for s in cards():
        if s["driver"] in CARD_DRIVER[which]:
            p = os.path.realpath("/dev/dri/by-path/pci-%s-render" % s["pci"])
            if os.path.exists(p):
                return s, p
    return None, None


def render_intel():
    """The render node of the integrated Intel, by PCI address (like 11-accendi.sh)."""
    s, p = card_of("intel")
    return (p, s["pci"]) if s else (None, None)


def right_card(o, d):
    """⛔ «Written is not in force»: the renderD128 INSIDE the box must be
    the same device (major:minor) as the node of the card asked for.  (ok, reason)"""
    s, node = card_of(o.gpu_card)
    if not s:
        return False, "on the host I cannot find the card «%s» (driver %s)" % (
            o.gpu_card, "/".join(CARD_DRIVER[o.gpu_card]))
    st = os.stat(node)
    outside = "%x:%x" % (os.major(st.st_rdev), os.minor(st.st_rdev))
    _c, t = in_box(d, "stat -c %t:%T /dev/dri/renderD128", 60)
    inside = (t or "").strip().splitlines()[-1:] or ["?"]
    if inside[0] != outside:
        return False, "the box's renderD128 (%s) is NOT %s (%s, %s = %s)" % (
            inside[0], s["gpu_card"], s["pci"], node, outside)
    says("   ⭐ card of the box: %s [%s] %s = renderD128 inside" % (
        s["gpu_card"], s["driver"], s["pci"]))
    return True, ""


def browser_env(s):
    """The environment of the client browsers (actors and check).  ⭐ Chrome is pinned
    to the Intel (--render-node-override): renderD128/129 swap between two boots,
    and the server also has the RX 6800.  Firefox follows the labwc (which is on the Intel)."""
    amb = dict(os.environ, WAYLAND_DISPLAY=s, **BROWSER_ENV)
    node, _pci = render_intel()
    if node:
        amb["REMOTIX_16_CHROME_EXTRA"] = "--render-node-override=%s" % node
        amb["REMOTIX_CHROME_OPTIONS"] += " --render-node-override=%s" % node
    return amb


def rdp_environment(d):
    """The environment of the xrdp clients: their Xvfb, no Wayland."""
    amb = dict(os.environ, DISPLAY=d, XDG_RUNTIME_DIR=RUN, REMOTIX_ON_SERVER="1")
    amb.pop("WAYLAND_DISPLAY", None)
    return amb


def browser_out_card(level_path):
    """From the resources series: the processes of the client browsers (enclosures `browser`
    and `labwc_client`) that draw on a card that is NOT the Intel."""
    _n, pci = render_intel()
    outside, seen_items = {}, 0
    try:
        for r in open(os.path.join(level_path, "risorse.jsonl"), encoding="utf-8", errors="replace"):
            try:
                d = json.loads(r)
            except ValueError:
                continue
            for p in d.get("processi_gpu") or []:
                if p.get("recinto") not in ("browser", "labwc_client"):
                    continue
                seen_items += 1
                if pci and p.get("pdev") and p["pdev"] != pci:
                    k = "%s@%s" % (p.get("comm"), p["pdev"])
                    outside[k] = outside.get(k, 0) + 1
    except OSError:
        return None
    return {"campioni_browser": seen_items, "fuori_intel": outside, "intel": pci}


def meta_box(d):
    """Inside the box: binary and page IN USE, the card it sees, the drivers."""
    v = {}
    _c, t = in_box(d, "md5sum /opt/remotix/remotix /opt/remotix/pagina.html; "
                             "echo @@; ls /dev/dri; echo @@; dpkg-query -W -f "
                             "'${Package}=${Version}\\n' intel-media-va-driver "
                             "intel-media-va-driver-non-free mesa-va-drivers libva2 "
                             "libgl1-mesa-dri 2>/dev/null; echo @@; "
                             "systemctl show -p ExecStart --value rete11-server 2>/dev/null "
                             "| tr ' ' '\\n' | grep -A1 -E '^--(session-cap|journal)' "
                             "| tr '\\n' ' '; echo @@; vainfo --display drm --device "
                             "/dev/dri/renderD128 2>&1 | grep -m1 'Driver version'; echo @@; "
                             "grep -a -o -E 'HEVC: .*H.264: gpu_card [^,]*, software OpenH264 [^ ]*"
                             "|card .* HEVC: .* H.264: .*' "
                             "/var/lib/rete11/registro.log 2>/dev/null | tail -1", 60)
    parts = (t or "").split("@@")
    while len(parts) < 6:
        parts.append("")
    for row in parts[0].splitlines():
        p = row.split()
        if len(p) == 2:
            v["binary" if p[1].endswith("remotix") else "page_v"] = p[0][:8]
    v["dri_nella_scatola"] = parts[1].split()
    v["driver_video"] = [x for x in parts[2].split() if "=" in x and not x.endswith("=")]
    v["opzioni_server"] = parts[3].strip()
    v["journal"] = "--journal" in parts[3]
    # ⭐ the VA provider the box sees on ITS renderD128 (iHD or radeonsi)
    v["driver_va"] = parts[4].split(":", 1)[-1].strip() or "?"
    # ⭐ phase 18: what the product MEASURED at startup (the HERE_I_AM line).  BOTH forms:
    #   today's binary (phase 19, §10.27, card only) writes
    #   «card N (route requested «…») — HEVC: yes via …|NO (…) · H.264: yes via …|NO (…)»;
    #   a phase 18 binary (Italian, with OpenH264) wrote «HEVC: … H.264: scheda no (…),
    #   software OpenH264 si'» — this way the level declares the route
    v["codifica_video"] = parts[5].strip() or "?"
    return v


# ═══════════════════════════════════════════════════════════════════════════
#  THE EMPTY SERVER (§6.1, §13.0)
# ═══════════════════════════════════════════════════════════════════════════
def boxes_on():
    c, t = sudo("podman ps --format '{{.Names}}'", 60)
    return [x for x in (t or "").split() if x.startswith("rete11-")]


def why_not_empty(d):
    troubles = []
    for s in boxes_on():
        _c, t = sudo("podman exec %s awk -F: '$1 ~ /^c16[0-9]+u[0-9]+$/ {print $1}' /etc/passwd"
                     % s, 60)
        if t.strip():
            troubles.append("in %s there are phase 16 tenants: %s" % (s, " ".join(t.split())))
    if "rete11-%s" % d in boxes_on():
        _c, t = in_box(d, "loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'")
        chi = [u for u in (t or "").split() if u and u not in ("root",)]
        if chi:
            troubles.append("in rete11-%s there are sessions: %s" % (d, " ".join(chi)))
    me = os.getpid()
    t = command(["pgrep", "-u", str(UID), "-af",
                 "marionette|remote-debugging-port|16-attore|16-controllo-corto|xfreerdp3"])
    browser = [r for r in t.splitlines() if r.strip() and not r.startswith("%d " % me)
               and "pgrep" not in r]
    if browser:
        troubles.append("%d bench browser/actor processes alive (e.g. %s)" % (
            len(browser), browser[0][:120]))
    return troubles


# ═══════════════════════════════════════════════════════════════════════════
#  THE BOX
# ═══════════════════════════════════════════════════════════════════════════
def redo_box(o, d, ceiling, dove):
    """turn_on · product · server, like 15-rifai-scatole.sh.  (ok, reason)"""
    for step in ("turn_on", "product", "server"):
        amb = "env REMOTIX_SESSION_CAP=%d " % ceiling if (step == "server" and ceiling) else ""
        if step == "turn_on":
            amb = "env REMOTIX_CARD=%s " % o.gpu_card
        t0 = time.time()
        c, t = sudo("cd %s && %sbash 11-accendi.sh %s %s" % (NETWORK11, amb, step, d), 900)
        # ⛔ [M] 26 Sep 00:35: the bisection rebuilds the box in the folder of a
        #    level that does not exist yet ⇒ FileNotFoundError and climb crashed
        os.makedirs(dove, exist_ok=True)
        with open(os.path.join(dove, "container_box-%s.log" % step), "a") as f:
            f.write("=== %s\n%s\n" % (now(), t))
        latest = [x for x in (t or "").splitlines() if x.strip()][-1:] or [""]
        says("   box %s: code %s in %.0f s · %s" % (step, c, time.time() - t0,
                                                     re.sub(r"\x1b\[[0-9;]*m", "", latest[0])[:120]))
        if c != 0:
            return False, "11-accendi.sh %s %s failed (code %s): %s" % (
                step, d, c, re.sub(r"\x1b\[[0-9;]*m", "", " ".join((t or "").splitlines()[-3:]))[:300])
        # ⭐ phase 18, --no-card: BEFORE turning on the server the box's VA driver
        #   is hidden (iHD_drv_video.so renamed), as in the software smoke round
        #   (fasi/18 §4): the child composes the environment from scratch and LIBVA_DRIVER_NAME is not enough.
        #   The compositor keeps drawing on the card (Mesa iris): it is only the
        #   encoding that drops to OpenH264, which is the product's route without a driver.
        if step == "product" and getattr(o, "no_card", False):
            c2, t2 = in_box(d, "cd /usr/lib/x86_64-linux-gnu/dri && mv iHD_drv_video.so "
                                      "iHD_drv_video.so.hidden && ls iHD_drv_video.so* ")
            says("   box VA driver hidden: code %s · %s" % (c2, (t2 or "").strip()[:80]))
            if c2 != 0 or "iHD_drv_video.so.hidden" not in (t2 or ""):
                return False, "I could not hide iHD_drv_video.so in the box: %s" % t2
        # ⭐ phase 20, --mesa-vulkan-deb: BEFORE turning on the server another
        #   mesa-vulkan-drivers is installed in the box (the Debian 13 backport), to see whether the Radeon's
        #   A3 defect disappears with RADV >= 25.1, which translates `ULTRA_LOW_LATENCY` to the firmware
        #   (~/Documenti/AMD §5-ter). We require dpkg to state the package version.
        if step == "product" and getattr(o, "mesa_vulkan_deb", ""):
            deb = o.mesa_vulkan_deb
            c2, t2 = sudo("podman cp %s rete11-%s:/tmp/mesa-vulkan.deb" % (_q(deb), d), 120)
            if c2 == 0:
                c2, t2 = in_box(d, "dpkg -i /tmp/mesa-vulkan.deb >/dev/null 2>&1; "
                                          "dpkg-query -W -f '${Version}' mesa-vulkan-drivers", 300)
            expected_val = re.sub(r"^.*mesa-vulkan-drivers_([^_]+)_.*$", r"\1", os.path.basename(deb))
            says("   box mesa-vulkan-drivers: code %s · %s" % (c2, (t2 or "").strip()[:80]))
            if c2 != 0 or (t2 or "").strip() != expected_val:
                return False, "mesa-vulkan-drivers %s not installed in the box: %s" % (expected_val, t2)
    ok, reason_text = right_card(o, d)
    if not ok:
        return False, reason_text
    if getattr(o, "no_card", False):
        cv = meta_box(d).get("codifica_video", "")
        # ⛔ phase 19 (§10.27): the product has NO software encoder any more.  Only a
        #   phase 18 binary in the box (old Italian line) can still climb without a card;
        #   today's binary declares «H.264: NO (…)» and offers no codec at all.
        if "H.264: scheda no (" not in cv or "software OpenH264 si'" not in cv:
            if " H.264: NO (" in cv:
                return False, "--no-card has nothing to measure: since phase 19 (§10.27) the " \
                              "product has no software encoder, and without the card it offers " \
                              "no codec (it says «%s»)" % cv
            return False, "the server does not declare H.264 encoding in software (it says «%s»)" % cv
        says("   ⭐ encoding declared by the product: %s" % cv)
    if ceiling:
        v = cap_in_effect(d)
        if v != ceiling:
            return False, "the server does not say «ADMINISTRATIVE session cap: **%d**» " \
                          "(it says %s)" % (ceiling, v)
        says("   ⭐ session cap in force: %d" % v)
    return True, ""


def cap_in_effect(d):
    # ⚠ BOTH forms of the product's line: the old (Italian) binary and the new (English) one
    _c, t = in_box(d, "{ cat /var/lib/rete11/registro.log 2>/dev/null; journalctl -u "
                             "rete11-server -b --no-pager -o cat 2>/dev/null; } | grep -a -E "
                             "'tetto AMMINISTRATIVO delle sessioni|ADMINISTRATIVE session cap' | tail -1", 60)
    m = re.search(r"(?:sessioni|session cap): \*\*(\d+)\*\*", t or "")
    return int(m.group(1)) if m else None


def meta_box_xrdp(d):
    """Inside the xrdp box: the versions, the card, and whether the xrdp configuration is
    the package's (dpkg --verify: no line = files intact)."""
    v = {"binary": None, "page_v": None, "opzioni_server": "Debian 13 xrdp, package configuration",
         "codifica_video": "RemoteFX on the processor (Debian's xrdp without H.264)"}
    _c, t = in_box(d, "dpkg-query -W -f '${Package}=${Version}\\n' %s 2>/dev/null; echo @@; "
                             "ls /dev/dri; echo @@; dpkg --verify xrdp xorgxrdp 2>&1 | grep -v '^$' "
                             "| head -5; echo @@; vainfo --display drm --device /dev/dri/renderD128 2>&1 "
                             "| grep -m1 'Driver version'" % " ".join(XRDP_PACKAGES), 60)
    parts = (t or "").split("@@") + ["", "", "", ""]
    v["packets"] = dict(x.split("=", 1) for x in parts[0].split() if "=" in x)
    v["dri_nella_scatola"] = parts[1].split()
    v["xrdp_configurazione"] = "the package's (dpkg --verify clean)" if not parts[2].strip() \
        else "⚠ MODIFIED: " + " | ".join(parts[2].strip().splitlines())
    v["driver_va"] = parts[3].split(":", 1)[-1].strip() or "?"
    v["driver_video"] = ["%s=%s" % kv for kv in sorted(v["packets"].items())
                         if kv[0] in ("mesa-va-drivers",)]
    t = command(["dpkg-query", "-W", "-f", "${Package}=${Version}\n"] + list(GUEST_XRDP_PACKAGES))
    v["pacchetti_ospite"] = dict(x.split("=", 1) for x in t.split() if "=" in x)
    return v


def xrdp_guest_ready():
    """⚠ The host's root is in RAM: after a reboot the client packages are no longer
    there.  They are checked, and if missing they are installed (declared).  (ok, reason)"""
    t = command(["dpkg-query", "-W", "-f", "${Package} ${db:Status-Status}\n"] + list(GUEST_XRDP_PACKAGES))
    missing = [p for p in GUEST_XRDP_PACKAGES if "%s installed" % p not in t]
    if not missing:
        return True, ""
    says("   ⚠ on the host %s are missing: installing them" % " ".join(missing))
    c, t = sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends %s"
                % " ".join(missing), 900)
    if c != 0:
        return False, "client packages not installed on the host: %s" % (t or "")[-300:]
    return True, ""


def protect_ssh():
    """§7.7: if the kernel has to kill something, NOT sshd (without it, the machine stays
    unreachable and a reboot loses key and provisioning).  At once on the live
    processes, and a drop-in in /run for an sshd restart (it disappears on reboot, like everything)."""
    c, t = sudo("for p in $(pgrep -x 'sshd|sshd-session'); do echo -900 > /proc/$p/oom_score_adj; done; "
                "mkdir -p /run/systemd/system/ssh.service.d && printf '[Service]\\nOOMScoreAdjust=-900\\n' "
                "> /run/systemd/system/ssh.service.d/remotix-oom.conf && systemctl daemon-reload && "
                "for p in $(pgrep -x 'sshd|sshd-session'); do cat /proc/$p/oom_score_adj; done | sort | uniq -c", 60)
    says("   sshd protected from the kernel (oom_score_adj): %s" % " · ".join((t or "?").split("\n"))[:120])


def redo_box_xrdp(o, d, dove):
    """The xrdp box from scratch: the other xrdp ones off, 3389 free, turn_on, xrdp
    on, the card checked.  (ok, reason)"""
    os.makedirs(dove, exist_ok=True)
    for s in boxes_on():
        if s.endswith("-xrdp"):
            c, t = sudo("podman rm -f -t 10 %s" % s, 120)
            says("   turned off %s (3389 is one per host): code %s" % (s, c))
    t = command(["ss", "-ltnH", "sport = :3389"])
    if t.strip():
        return False, "the host's port 3389 is taken: %s" % t.strip()[:160]
    ok, reason_text = xrdp_guest_ready()
    if not ok:
        return False, reason_text
    t0 = time.time()
    c, t = sudo("cd %s && env REMOTIX_CARD=%s bash 11-accendi.sh turn_on %s" % (NETWORK11, o.gpu_card, d), 900)
    with open(os.path.join(dove, "scatola-accendi.log"), "a") as f:
        f.write("=== %s\n%s\n" % (now(), t))
    latest = [x for x in (t or "").splitlines() if x.strip()][-1:] or [""]
    says("   box turn_on %s: code %s in %.0f s · %s" % (d, c, time.time() - t0,
                                                         re.sub(r"\x1b\[[0-9;]*m", "", latest[0])[:120]))
    if c != 0:
        return False, "11-accendi.sh turn_on %s failed (code %s): %s" % (
            d, c, re.sub(r"\x1b\[[0-9;]*m", "", " ".join((t or "").splitlines()[-3:]))[:300])
    c, t = in_box(d, "systemctl start xrdp-sesman xrdp && for i in $(seq 1 60); do "
                            "ss -ltnH 'sport = :3389' | grep -q . && { systemctl is-active xrdp xrdp-sesman "
                            "| tr '\\n' ' '; exit 0; }; sleep 0.25; done; systemctl status xrdp --no-pager "
                            "| tail -5; exit 1", 120)
    says("   xrdp on: code %s · %s" % (c, (t or "").strip()[:100]))
    if c != 0:
        return False, "xrdp is not listening on 3389 in the box: %s" % (t or "")[-300:]
    return right_card(o, d)


class Guard(threading.Thread):
    """§7.7: every 2 s MemAvailable and the memory pressure; `motivo` when it trips."""

    def __init__(self):
        super().__init__(daemon=True)
        self.motivo = None
        self.latest = {}
        self.alive = True

    @staticmethod
    def read_it():
        mem = psi = None
        try:
            m = re.search(r"MemAvailable:\s+(\d+)", open("/proc/meminfo").read())
            mem = int(m.group(1)) // 1024 if m else None
        except OSError:
            pass
        try:
            m = re.search(r"^full avg10=([\d.]+)", open("/proc/pressure/memory").read(), re.M)
            psi = float(m.group(1)) if m else None
        except OSError:
            pass
        return mem, psi

    @staticmethod
    def judge(mem, psi):
        if mem is not None and mem < GUARD_MEM_MB:
            return "available memory %d MB < %d MB" % (mem, GUARD_MEM_MB)
        if psi is not None and psi > GUARD_PSI_FULL:
            return "memory pressure full avg10 %.1f %% > %.0f %%" % (psi, GUARD_PSI_FULL)
        return None

    def run(self):
        while self.alive:
            mem, psi = self.read_it()
            self.latest = {"mem_disponibile_mb": mem, "psi_full_avg10": psi}
            m = self.judge(mem, psi)
            if m and not self.motivo:
                self.motivo = m
                says("⛔ HOST GUARD (§7.7): %s — closing the level" % m)
            time.sleep(2)

    def rearms(self, wait_s=180):
        """Before a level: wait for the memory to have come back (at most `wait_s`)."""
        fine = time.time() + wait_s
        while time.time() < fine and self.judge(*self.read_it()):
            time.sleep(5)
        self.motivo = None
        return self.judge(*self.read_it())


CLEAROUT_16 = r"""
for u in $(awk -F: '$1 ~ /^c16[0-9]+u[0-9]+$/ {print $1}' /etc/passwd); do
  id=$(id -u "$u" 2>/dev/null)
  m="runuser -u [$(printf %s "$u" | cut -c1)]$(printf %s "$u" | cut -c2-) "
  loginctl terminate-user "$u" >/dev/null 2>&1
  pkill -KILL -f "$m" >/dev/null 2>&1; pkill -KILL -u "$u" >/dev/null 2>&1
  sleep 0.2
  userdel -r "$u" >/dev/null 2>&1 || userdel "$u" >/dev/null 2>&1
  [ -n "$id" ] && systemctl reset-failed "user@$id.service" >/dev/null 2>&1
  [ -n "$id" ] && find /tmp -maxdepth 1 -uid "$id" -exec rm -rf {} + 2>/dev/null
  echo "cleared $u"
done; true
"""


def clear_out_16(d):
    """The c16* tenants out of the box (the line of 15-giro.py, only ours)."""
    _c, t = in_box(d, CLEAROUT_16, 300)
    n = len([r for r in (t or "").splitlines() if r.startswith("cleared")])
    if n:
        says("   cleared %d leftover c16 tenants" % n)


# ═══════════════════════════════════════════════════════════════════════════
#  THE COMPOSITORS
# ═══════════════════════════════════════════════════════════════════════════
SYSTEM = {"xrdp": False}


def compositors(action, *arg):
    prog = "16-compositori-rdp.sh" if SYSTEM["xrdp"] else "16-compositori.sh"
    r = subprocess.run(["bash", os.path.join(HERE, prog), action] + list(arg),
                       capture_output=True, text=True, errors="replace", timeout=300)
    return r.returncode, r.stdout + r.stderr


def display_di(n):
    """xrdp: the display of this user's Xvfb (16-compositori-rdp.sh), if alive."""
    try:
        d = open(os.path.join(COMPOSITORS_RDP, "u%02d" % n)).read().strip()
    except OSError:
        return None
    return d if d.startswith(":") and os.path.exists("/tmp/.X11-unix/X%s" % d[1:]) else None


def socket_di(n):
    if SYSTEM["xrdp"]:
        return display_di(n)
    try:
        s = open(os.path.join(COMPOSITORS, "u%02d" % n)).read().strip()
    except OSError:
        return None
    return s if s and os.path.exists(os.path.join(RUN, s)) else None


# ═══════════════════════════════════════════════════════════════════════════
#  THE ACTORS
# ═══════════════════════════════════════════════════════════════════════════
class Actor:
    def __init__(self, o, n, level, folder):
        self.o, self.n, self.level, self.folder = o, n, level, folder
        self.dir_user = os.path.join(folder, "username-%02d" % n)
        self.proc = None
        self.started = None
        self.born = None
        self.dead_annotated = False

    def start(self):
        s = socket_di(self.n)
        if not s:
            raise RuntimeError("the compositor u%02d is not there" % self.n)
        largo, alto = self.o.largo, self.o.alto
        cmd = [sys.executable, self.o.prog_actor, "--container_box", self.o.container_box,
               "--username", str(self.n), "--display" if SYSTEM["xrdp"] else "--wayland", s,
               "--dir", self.folder,
               "--seed", str(self.o.base_seed + self.n), "--largo", str(largo),
               "--alto", str(alto), "--base-ports", str(self.o.base_ports + 10 * self.n)]
        if self.o.video:
            cmd += ["--video", self.o.video]
        amb = browser_env(s) if not SYSTEM["xrdp"] else rdp_environment(s)
        os.makedirs(self.dir_user, exist_ok=True)
        self.log = open(os.path.join(self.folder, "username-%02d.log" % self.n), "a")
        self.log.write("=== %s %s\n" % (now(), " ".join(cmd)))
        self.log.flush()
        self.proc = subprocess.Popen(cmd, stdout=self.log, stderr=subprocess.STDOUT,
                                     env=amb, cwd=HERE, start_new_session=True)
        self.started = time.time()
        return s

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def is_born(self):
        if self.born is None and os.path.exists(os.path.join(self.dir_user, "nascita.json")):
            self.born = time.time()
        return self.born is not None

    def signal_v(self, sig):
        if self.alive():
            try:
                os.kill(self.proc.pid, sig)
            except OSError:
                pass

    def kill(self):
        if self.proc is not None:
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except OSError:
                pass


# ═══════════════════════════════════════════════════════════════════════════
#  THE CLIMB
# ═══════════════════════════════════════════════════════════════════════════
class Climb:
    def __init__(self, o):
        self.o = o
        self.base = os.path.join(MEASURES, o.campaign)
        self.actors = {}                 # n -> Actor
        self.actors_round = 0             # one actors-<k> folder per clean box
        self.actors_dir = None
        self.history = []
        self.levels_done = 0
        self.n_stopped = False
        self.state = {"campaign": o.campaign, "container_box": o.container_box, "gauge": o.gauge,
                      "rungs": o.rungs, "pid": os.getpid(), "start": now(),
                      "phase": "preparo", "rung": None, "level_dir": None,
                      "utenti_vivi": 0, "expected_users": 0, "class_last": None,
                      "history": self.history, "prova": o.prova}
        self.meta = {}
        self.guard = None
        self.guest = None               # §7.7: the reason, if the guard tripped in the level
        if o.guard:
            self.guard = Guard()
            self.guard.start()

    # -- the state for the coordinator ---------------------------------------
    def do_update(self, **k):
        self.state.update(k)
        self.state["utenti_vivi"] = sum(1 for a in self.actors.values() if a.alive())
        self.state["updated"] = now()
        try:
            write_json(os.path.join(self.base, "stato.json"), self.state)
        except OSError as e:
            says("⚠ stato.json not written: %s" % e)

    def new_actors_folder(self):
        self.actors_round += 1
        self.actors_dir = os.path.join(self.base, "actors-%d" % self.actors_round)
        os.makedirs(self.actors_dir, exist_ok=True)

    # -- the pieces -----------------------------------------------------------
    def stop_actors(self):
        living = [a for a in self.actors.values() if a.alive()]
        if living:
            says("   stopping %d actors (SIGTERM: they clean up by themselves)" % len(living))
        for a in living:
            a.signal_v(signal.SIGTERM)
        fine = time.time() + self.o.wait_exit_s
        while time.time() < fine and any(a.alive() for a in living):
            time.sleep(1)
        hard = [a for a in living if a.alive()]
        if hard:
            says("   ⚠ %d actors did not exit in %d s: SIGKILL to the group (%s)" % (
                len(hard), self.o.wait_exit_s, ", ".join("u%02d" % a.n for a in hard)))
        for a in self.actors.values():
            if a.alive():
                a.kill()
        self.actors = {}

    def clean_box(self, dove):
        """Actors out, tenants out, box rebuilt with the cap.  (ok, reason)"""
        self.do_update(phase="rebuilding the box")
        self.stop_actors()
        if self.o.no_rebuild:
            says("⚠ --no-rebuild: the box is NOT rebuilt (only tests of the setup)")
            clear_out_16(self.o.cont)
            ok, reason_text = True, ""
        elif SYSTEM["xrdp"]:
            ok, reason_text = redo_box_xrdp(self.o, self.o.cont, dove)
        else:
            ok, reason_text = redo_box(self.o, self.o.container_box, self.o.ceiling, dove)
        if ok and SYSTEM["xrdp"]:
            self.meta_box = meta_box_xrdp(self.o.cont)
            says("   box: %s · xrdp %s · configuration %s · dri %s · VA %s" % (
                self.o.cont, self.meta_box["packets"].get("xrdp"),
                self.meta_box.get("xrdp_configurazione"),
                ",".join(self.meta_box.get("dri_nella_scatola", [])), self.meta_box.get("driver_va")))
        elif ok:
            self.meta_box = meta_box(self.o.container_box)
            says("   box: binary %s · page %s · %s · dri %s · VA %s · %s" % (
                self.meta_box.get("binary"), self.meta_box.get("page_v"),
                self.meta_box.get("opzioni_server") or "(default options)",
                ",".join(self.meta_box.get("dri_nella_scatola", [])),
                self.meta_box.get("driver_va"), self.meta_box.get("codifica_video")))
        self.new_actors_folder()
        return ok, reason_text

    def enter(self, n_until, level):
        """The missing actors up to `n_until`, one after the other: the next one
        when the previous one has the first frame (nascita.json)."""
        c, t = compositors("turn_on", str(n_until), self.o.gauge)
        if c != 0:
            says("⛔ compositors: %s" % " | ".join(t.splitlines()[-3:]))
            return False, "the compositors do not turn on: %s" % t.strip().splitlines()[-1:]
        newcomers = [n for n in range(1, n_until + 1) if n not in self.actors]
        for n in newcomers:
            if self.n_stopped:
                return False, "stopped from outside"
            if self.guard and self.guard.motivo:
                self.guest = self.guard.motivo
                return False, "host resources: %s" % self.guard.motivo
            a = Actor(self.o, n, level, self.actors_dir)
            try:
                s = a.start()
            except Exception as e:               # noqa: BLE001
                return False, "actor %d does not start: %s" % (n, e)
            self.actors[n] = a
            says("   + user %02d (pid %d, %s, seed %d, ports %d)" % (
                n, a.proc.pid, s, self.o.base_seed + n, self.o.base_ports + 10 * n))
            self.do_update(phase="users entering", expected_users=n_until)
            fine = time.time() + self.o.wait_birth_s
            while time.time() < fine and a.alive() and not a.is_born() and not self.n_stopped \
                    and not (self.guard and self.guard.motivo):
                time.sleep(0.5)
            if a.is_born():
                says("     user %02d born in %.1f s" % (n, a.born - a.started))
            elif not a.alive():
                says("   ⛔ user %02d DEAD before being born (code %s): going on, "
                     "the classification will tell" % (n, a.proc.returncode))
            else:
                says("   ⚠ user %02d has no first frame in %d s: the next one "
                     "comes in anyway" % (n, self.o.wait_birth_s))
        return True, ""

    def short_check(self, level, level_path):
        browser = ("firefox", "chrome")[self.levels_done % 2]
        s = socket_di(0)
        if not s:
            says("   ⚠ the check's compositor u00 is not there")
            return None
        cmd = [sys.executable, self.o.prog_check, "--container_box", self.o.container_box,
               "--level", str(level), "--dir", level_path, "--browser", browser,
               "--base-ports", str(self.o.base_ports), "--largo", str(self.o.largo),
               "--alto", str(self.o.alto)]
        if SYSTEM["xrdp"]:
            browser = "freerdp"
            cmd += ["--check", "--display", s, "--seed", str(self.o.base_seed + 99)]
            amb = rdp_environment(s)
        else:
            amb = browser_env(s)
        says("   short check: %s on %s" % (browser, s))
        with open(os.path.join(level_path, "controllo-corto.log"), "w") as log:
            try:
                p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=amb, cwd=HERE,
                                     start_new_session=True)
                # ⭐ not a blind wait() of 600 s: at SIGTERM (stopped from outside) the
                #   check stops at once and the climb goes to clean up
                limit = time.time() + self.o.check_cap_s
                c = None
                while True:
                    try:
                        c = p.wait(timeout=1)
                        break
                    except subprocess.TimeoutExpired:
                        pass
                    if self.n_stopped or time.time() >= limit:
                        says("   ⛔ short check %s: stopped" % (
                            "interrupted (stopped from outside)" if self.n_stopped
                            else "beyond %d s" % self.o.check_cap_s))
                        stop_group(p)
                        c = None
                        break
            except Exception as e:               # noqa: BLE001
                says("   ⛔ short check not launched: %s" % e)
                return None
        outcome = None
        try:
            outcome = json.load(open(os.path.join(level_path, "controllo-corto.json"))).get("outcome")
        except (OSError, ValueError):
            pass
        says("   short check: %s (code %s)" % (outcome, c))
        return outcome

    def photo_before_window(self, check_start, events):
        """SIGUSR1 to all the live actors, then wait for each one to have written
        its photo (a picture-* file or the «picture» event, even failed) — at most
        `photo_cap_s`.  Returns the summary for livello.json."""
        living = [a for a in self.actors.values() if a.alive()]
        t = time.time()
        self.do_update(phase="picture")
        says("   SIGUSR1 to %d actors (full photo), %.0f s before the window" % (
            len(living), check_start - t))
        for a in living:
            a.signal_v(signal.SIGUSR1)
        done = set()
        limit = t + self.o.photo_cap_s
        while not self.n_stopped:
            for a in living:
                if a.n not in done and photo_written(a.dir_user, t):
                    done.add(a.n)
            if len(done) == len(living) or time.time() >= limit:
                break
            time.sleep(1)
        missing = sorted(a.n for a in living if a.n not in done)
        says("   photos written: %d/%d in %.0f s%s" % (
            len(done), len(living), time.time() - t,
            (" · ⚠ missing %s" % missing) if missing else ""))
        if missing:
            events.append({"t": now(), "event": "photos missing", "users": missing})
        self.do_update(phase="work")
        return {"t": iso(t), "t_s": round(t, 3), "expected_vals": sorted(a.n for a in living),
                "done": sorted(done), "duration_s": round(time.time() - t, 1)}

    def trim_actors(self, level_path, t0, t1):
        """The actors' series inside [t0, t1], in the level folder.
        ⛔ nascita.json ONLY if the user is NEW in this level (started in the
        level, or the birth written in the level): the births of the earlier rungs
        have already been judged there, and here they are not re-judged."""
        for a in self.actors.values():
            src = a.dir_user
            dst = os.path.join(level_path, "username-%02d" % a.n)
            os.makedirs(dst, exist_ok=True)
            if not os.path.isdir(src):
                continue
            for label_name in os.listdir(src):
                p = os.path.join(src, label_name)
                if not os.path.isfile(p):
                    continue
                q = os.path.join(dst, label_name)
                if label_name.endswith(".jsonl"):
                    trim_jsonl(p, q, t0, t1)
                elif label_name == "nascita.json":
                    if level_birth(a.started, os.path.getmtime(p), t0):
                        try:
                            os.link(p, q)
                        except OSError:
                            shutil.copy2(p, q)
                elif os.path.getmtime(p) >= t0 - 1:
                    try:
                        os.link(p, q)
                    except OSError:
                        shutil.copy2(p, q)

    def log_server_xrdp(self, level_path, sign, t0, t1):
        """xrdp: server.log = the NEW lines of xrdp.log and xrdp-sesman.log from the mark."""
        d = self.o.cont
        seg = sign or {}
        parts = []
        for label_name in ("xrdp.log", "xrdp-sesman.log"):
            _c, t = in_box(d, "tail -n +%d /var/log/%s 2>/dev/null" % (seg.get(label_name, 0) + 1, label_name), 300)
            parts.append("== /var/log/%s\n%s" % (label_name, t or ""))
        open(os.path.join(level_path, "server.log"), "w").write("\n".join(parts) + "\n")
        da, a = "@%d" % int(t0), "@%d" % int(t1 + 1)
        _c, t = in_box(d, "journalctl -p err -o json --since %s --until %s --no-pager 2>/dev/null "
                                 "| tail -n 200000" % (da, a), 300)
        open(os.path.join(level_path, "journal-err.jsonl"), "w").write(
            "\n".join(r for r in (t or "").splitlines() if r.startswith("{")) + "\n")
        _c, t = in_box(d, "journalctl -u xrdp -u xrdp-sesman --since %s --until %s --no-pager "
                                 "-o short-iso-precise 2>&1 | tail -n 500000" % (da, a), 300)
        open(os.path.join(level_path, "journal-server.log"), "w").write(t or "")
        _c, t = in_box(d, "journalctl --since %s --until %s --no-pager "
                                 "-o short-iso-precise 2>&1 | tail -n 500000" % (da, a), 300)
        open(os.path.join(level_path, "journal-scatola.log"), "w").write(t or "")
        return ["server.log", "journal-err.jsonl", "journal-server.log", "journal-scatola.log"]

    def log_server(self, level_path, sign, t0, t1):
        if SYSTEM["xrdp"]:
            return self.log_server_xrdp(level_path, sign, t0, t1)
        d = self.o.container_box
        files = []
        if sign is not None:
            # ⭐ «server.log»: the name 16-classifica.py reads
            _c, t = in_box(d, "tail -n +%d /var/lib/rete11/registro.log" % (sign + 1), 300)
            open(os.path.join(level_path, "server.log"), "w").write(t or "")
            files.append("server.log")
        da, a = "@%d" % int(t0), "@%d" % int(t1 + 1)
        # ⭐ the product's errors in the journal (--journal): the schema of 16-classifica.py
        _c, t = in_box(d, "journalctl -t remotix -p err -o json --since %s --until %s "
                                 "--no-pager 2>/dev/null | tail -n 200000" % (da, a), 300)
        open(os.path.join(level_path, "journal-err.jsonl"), "w").write(
            "\n".join(r for r in (t or "").splitlines() if r.startswith("{")) + "\n")
        files.append("journal-err.jsonl")
        _c, t = in_box(d, "journalctl -u rete11-server --since %s --until %s --no-pager "
                                 "-o short-iso-precise 2>&1 | tail -n 500000" % (da, a), 300)
        open(os.path.join(level_path, "journal-server.log"), "w").write(t or "")
        files.append("journal-server.log")
        _c, t = in_box(d, "journalctl --since %s --until %s --no-pager "
                                 "-o short-iso-precise 2>&1 | tail -n 500000" % (da, a), 300)
        open(os.path.join(level_path, "journal-scatola.log"), "w").write(t or "")
        files.append("journal-scatola.log")
        return files

    def ranking(self, level_path, level):
        cmd = [sys.executable, self.o.prog_ranking, "--level-dir", level_path,
               "--campaign", self.o.campaign, "--level", str(level),
               "--window-s", str(int(self.o.check_min * 60)), "--json"]
        if self.o.fps_video:
            cmd += ["--fps-video", str(self.o.fps_video)]
        if SYSTEM["xrdp"]:
            cmd += ["--system_wide", "xrdp"]
        if self.o.prova:
            cmd.append("--dry")            # §13.3: the test climb does not count
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=900,
                               cwd=HERE)
            out_dir, code_v = r.stdout + r.stderr, r.returncode
        except Exception as e:                   # noqa: BLE001
            out_dir, code_v = "classification not launched: %s" % e, None
        open(os.path.join(level_path, "classifica.log"), "w").write(out_dir)
        return read_class(out_dir, code_v)

    # -- ONE LEVEL -------------------------------------------------------------
    def level(self, n, minutes, label_name, kind):
        """Brings the climb to `n` users and does the level.  Returns (class, signif, level_path)."""
        o = self.o
        level_path = os.path.join(self.base, label_name)
        os.makedirs(level_path, exist_ok=True)
        says("══ %s: %d users, %s min (%s) ══" % (label_name, n, minutes, kind))
        self.do_update(phase="level", rung=n, level_dir=level_path, level_type=kind)
        t_start = time.time()
        if self.guard:
            still = self.guard.rearms()
            if still:
                says("⚠ the guard still says «%s» after the wait: the level starts anyway" % still)
        self.guest = None
        if SYSTEM["xrdp"]:
            _c, t = in_box(o.cont, "for f in xrdp.log xrdp-sesman.log; do echo $f $(wc -l < "
                                          "/var/log/$f 2>/dev/null || echo 0); done", 60)
            sign = {}
            for r in (t or "").splitlines():
                p_ = r.split()
                if len(p_) == 2 and p_[1].isdigit():
                    sign[p_[0]] = int(p_[1])
        else:
            _c, t = in_box(o.container_box, "wc -l < /var/lib/rete11/registro.log 2>/dev/null", 60)
            try:
                sign = int((t or "").split()[-1])
            except (ValueError, IndexError):
                sign = None
        # ⛔ 16-risorse.py runs as ROOT (the tenants' smaps_rollup and fdinfo):
        #   sudo -S, the password on stdin; sudo passes the SIGTERM to the child.
        cmd_r = [sys.executable, o.prog_resources, "--container_box", o.cont, "--dir", level_path]
        if SYSTEM["xrdp"]:
            cmd_r += ["--system_wide", "xrdp", "--browser-marks", "remotix-rdp-"]
        if not o.resources_without_root:
            cmd_r = ["sudo", "-S", "-p", ""] + cmd_r
        resources = subprocess.Popen(
            cmd_r, stdin=subprocess.PIPE, text=True,
            stdout=open(os.path.join(level_path, "risorse.log"), "w"), stderr=subprocess.STDOUT,
            cwd=HERE, start_new_session=True)
        try:
            resources.stdin.write("" if o.resources_without_root else _sudo_password())
            resources.stdin.close()
        except OSError:
            pass
        events = []
        entry_ok, why_entry = self.enter(n, n)
        entered = sorted(a.n for a in self.actors.values() if a.proc is not None)
        born = sorted(a.n for a in self.actors.values() if a.born)
        if not entry_ok and self.guest:
            for a in self.actors.values():
                a.signal_v(signal.SIGTERM)
        if not entry_ok:
            # ⛔ compositor or actor that does not start: the level is NOT good
            #   (class «?», which stops the climb like an unreadable class)
            events.append({"t": now(), "event": "entry failed", "rationale": why_entry,
                           "expected_vals": n, "entered": len(entered), "born": len(born)})
            says("⛔ ENTRY FAILED (%d entered of %d, %d born): %s — the level will be «?»" % (
                len(entered), n, len(born), why_entry))
        t_work = time.time()
        fine = t_work + minutes * 60
        check_start = fine - o.check_min * 60
        # ⭐ the full photo (SIGUSR1) BEFORE the judgement window: Chrome
        #   Page.captureScreenshot in 4K stops drawing, and inside the window
        #   it would dirty it.  It is sent `photo_lead_s` before and the window
        #   starts only when the photos are written (if they are late, window and
        #   end of the level slip together: the window stays whole and clean).
        now_photo = check_start - o.photo_lead_s
        if entry_ok:
            says("   all inside (%.0f s after the start of the level): work until %s" % (
                t_work - t_start, time.strftime("%H:%M:%S", time.localtime(fine))))
        self.do_update(phase="work", expected_end=datetime.datetime.fromtimestamp(
            fine).astimezone().isoformat(timespec="seconds"))
        check_outcome = None
        done_check = False
        picture = None                      # {"t": sent, "expected_vals": [...], "done": [...]}
        while not self.n_stopped and entry_ok:
            if self.guard and self.guard.motivo:
                self.guest = self.guard.motivo
                events.append({"t": now(), "event": "host guard", "rationale": self.guest,
                               "gauge": dict(self.guard.latest)})
                for a in self.actors.values():
                    a.signal_v(signal.SIGTERM)          # out at once: the clients free the memory
                break
            clock = time.time()
            for a in self.actors.values():
                if not a.alive() and not a.dead_annotated:
                    a.dead_annotated = True
                    events.append({"t": now(), "event": "actor dead", "username": a.n,
                                   "code_v": a.proc.returncode})
                    says("   ⛔ user %02d exited (code %s)" % (a.n, a.proc.returncode))
            if picture is None and clock >= now_photo:
                picture = self.photo_before_window(check_start, events)
                clock = time.time()
                if clock > check_start:
                    delay = clock - check_start
                    check_start, fine = clock, fine + delay
                    says("   the window starts %.0f s later (slow photos): end at %s" % (
                        delay, time.strftime("%H:%M:%S", time.localtime(fine))))
                    self.do_update(expected_end=datetime.datetime.fromtimestamp(
                        fine).astimezone().isoformat(timespec="seconds"))
                continue
            if picture is not None and not done_check and clock >= check_start:
                done_check = True
                self.do_update(phase="check")
                if not o.no_check:
                    check_outcome = self.short_check(n, level_path)
                self.do_update(phase="work")
                continue
            if clock >= fine and done_check:
                break
            upcoming = now_photo if picture is None else (check_start if not done_check
                                                       else fine)
            time.sleep(min(2 if self.guard else 5, max(0.5, upcoming - clock)))
        t_fine = time.time()
        self.do_update(phase="registro")
        resources.send_signal(signal.SIGTERM)
        try:
            resources.wait(timeout=30)
        except subprocess.TimeoutExpired:
            sudo("pkill -KILL -f %s" % _q("[1]6-risorse.py --container_box %s --dir %s" % (
                o.cont, level_path)), 30)
        files = self.log_server(level_path, sign, t_start, t_fine)
        cards_b = browser_out_card(level_path)
        if cards_b and cards_b["fuori_intel"]:
            says("   ⛔ client browser on a card that is not the Intel: %s" % cards_b["fuori_intel"])
            events.append({"t": now(), "event": "browser off the Intel",
                           "detail": cards_b["fuori_intel"]})
        self.trim_actors(level_path, t_start, t_fine)
        row = dict(self.meta, **{
            "campaign": o.campaign, "level": n, "label_name": label_name, "kind": kind,
            "desktop": o.container_box, "gauge": o.gauge, "largo": o.largo, "alto": o.alto,
            "session_cap": o.ceiling, "minutes": minutes, "check_min": o.check_min,
            "start": iso(t_start), "inizio_t": round(t_start, 3),
            "inizio_lavoro": iso(t_work), "fine": round(t_fine, 3), "fine_iso": iso(t_fine),
            "duration_s": round(t_fine - t_start), "durata_lavoro_s": round(t_fine - t_work),
            "users": [{"username": a.n, "profile_v": "ABCD"[(a.n - 1) % 4],
                        "browser": "freerdp" if SYSTEM["xrdp"] else ("firefox" if a.n % 2 else "chrome"),
                        "fresh": bool(a.born and a.born >= t_start) or a.started >= t_start}
                       for _k, a in sorted(self.actors.items())],
            "vivi_alla_fine": sorted(
                a.n for a in self.actors.values() if a.alive()),
            "nati_nel_livello": sorted(a.n for a in self.actors.values()
                                       if a.born and a.born >= t_start),
            "nascite_s": {"%02d" % a.n: round(a.born - a.started, 1) for a in
                          self.actors.values() if a.born and a.born >= t_start},
            "base_seed": o.base_seed, "video": o.video, "fps_video": o.fps_video,
            "short_check": check_outcome, "log_server": files,
            "entry_ok": entry_ok, "entrata_ragione": why_entry or None,
            "expected_vals": n, "entered": entered, "nati_alla_partenza": born,
            "full_photo": picture, "window_start": iso(check_start),
            "inizio_finestra_t": round(check_start, 3),
            "schede_browser": cards_b,
            "events": events, "attori_da": self.actors_dir, "prova": o.prova,
            "system_wide": o.system_wide, "ospite_esaurito": self.guest,
            "guard": dict(self.guard.latest) if self.guard else None})
        ms = getattr(self, "meta_box", {})
        row.update({"scatola_" + k: v for k, v in ms.items()})
        # ⭐ the fields of §10 with the names 16-classifica.py reads (BASE)
        # ⭐ the SERVER's card (the one in the box, --gpu_card), not always the
        #   Intel: in the AMD campaign it is the RX 6800.  The client browsers stay
        #   on the Intel and `browser_card` says so.
        srv = [s for s in self.meta.get("cards", []) if s["driver"] in CARD_DRIVER[o.gpu_card]]
        intel = [s for s in self.meta.get("cards", []) if s["driver"] in CARD_DRIVER["intel"]]
        row.update(gpu_card=(srv or [{}])[0].get("gpu_card", "?"),
                    which_card=o.gpu_card, card_pci=(srv or [{}])[0].get("pci"),
                    browser_card=(intel or [{}])[0].get("gpu_card", "?"),
                    driver=" ".join([(srv or [{}])[0].get("driver", "?")]
                                    + ms.get("driver_video", [])),
                    commit=self.meta.get("commit_prodotto") or
                    "benches %s" % self.meta.get("commit_banchi"), binary=ms.get("binary"),
                    page_v=ms.get("page_v"), core=self.meta.get("kernel"))
        if SYSTEM["xrdp"]:
            pk = ms.get("packets") or {}
            row.update(commit="xrdp %s · xorgxrdp %s · freerdp %s" % (
                pk.get("xrdp"), pk.get("xorgxrdp"), (ms.get("pacchetti_ospite") or {}).get("freerdp3-x11")),
                session_cap=None, browser_card="none (FreeRDP decodes on the processor)")
        write_json(os.path.join(level_path, "livello.json"), row)
        if self.n_stopped:
            # ⛔ a level interrupted from outside is not classified: it did not last
            row["interrupted"] = True
            write_json(os.path.join(level_path, "livello.json"), row)
            cls_name, signif, why_c = "INTERROTTO", False, "stopped from outside (signal)"
        else:
            self.do_update(phase="classifico")
            cls_name, signif, why_c = self.ranking(level_path, n)
            if not entry_ok:
                # ⛔ what the classification says stays in its log, but the
                #   level is not the one asked for: it is not good
                why_c = "ENTRY FAILED (%d entered of %d): %s · the classification said %s" % (
                    len(entered), n, why_entry, cls_name)
                cls_name, signif = "?", False
        if self.guest and not self.n_stopped:
            # ⛔ §7.7: the level closed by the guard is a declared BREAK
            why_c = "⛔ HOST RESOURCES (§7.7): %s · the classification said %s — %s" % (
                self.guest, cls_name, why_c[:200])
            cls_name, signif = "FAIL", True
        self.levels_done += 1
        row.update(cls_name=cls_name, significant=signif, reason_class=why_c)
        with open(os.path.join(self.base, "salita.jsonl"), "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
        self.history.append({"level": n, "label_name": label_name, "kind": kind, "cls_name": cls_name,
                            "significant": signif, "dir": level_path})
        self.do_update(class_last=cls_name)
        says("   ▶ %s: %s%s — %s" % (label_name, cls_name, " (significant)" if signif else "",
                                     why_c[:200]))
        return cls_name, signif, level_path

    # -- THE WHOLE CLIMB -------------------------------------------------------
    def run_loop(self):
        o = self.o
        self.meta = meta_machine(o)
        says("⭐ CLIMB %s · %s · %s (%dx%d) · rungs %s · %s min (last %s) · cap %d%s" % (
            o.campaign, o.container_box, o.gauge, o.largo, o.alto, ",".join(map(str, o.rungs)),
            o.minutes, o.last_rung_minutes, o.ceiling, " · TEST (does not count)" if o.prova else ""))
        says("   card of the box: %s · %s" % (o.gpu_card, "SYSTEM xrdp, FreeRDP clients on the processor"
                                              if SYSTEM["xrdp"] else "client browsers on the Intel"))
        if SYSTEM["xrdp"]:
            protect_ssh()
        says("   product commit: %s" % (self.meta["commit_prodotto"] or
                                       "? (16-prodotto absent or different binary)"))
        says("   kernel %s · %s · binary %s · page %s · benches %s" % (
            self.meta["kernel"], " + ".join("%s [%s]" % (s["gpu_card"], s["driver"])
                                            for s in self.meta["cards"]),
            self.meta["prodotto_binario"], self.meta["prodotto_pagina"],
            self.meta["commit_banchi"]))
        ok, reason_text = self.clean_box(self.base)
        if not ok:
            return self.block(reason_text)
        last_good, broken = 0, None
        for i, n in enumerate(o.rungs):
            if self.n_stopped:
                break
            minutes = o.last_rung_minutes if i == len(o.rungs) - 1 else o.minutes
            cls_name, signif, _d = self.level(n, minutes, "level-%02d" % n, "rung")
            if self.n_stopped:
                break
            if bad(cls_name, signif) and self.guest:
                broken = n
                says("⛔ %d users: closed by the host guard (%s) — break, without repeating "
                     "(§7.7)" % (n, self.guest))
                break
            if bad(cls_name, signif):
                says("⚠ %d users: %s — REPEATED under the same conditions (§14), from a clean "
                     "box" % (n, cls_name))
                ok, reason_text = self.clean_box(os.path.join(self.base, "level-%02d" % n))
                if not ok:
                    return self.block(reason_text)
                class2, signif2, _d = self.level(n, minutes, "level-%02d-ripetizione" % n,
                                                    "ripetizione")
                if self.n_stopped:
                    break
                if bad(class2, signif2):
                    broken = n
                    says("⛔ confirmed: %d users %s twice" % (n, class2))
                    break
                says("   the repetition says %s: not confirmed, climbing" % class2)
            last_good = n
        if broken is not None and not self.n_stopped:
            last_good, broken = self.search(last_good, broken)
        self.do_update(phase="fine", last_good=last_good, breakage=broken)
        says("⏹ END: last good level %s · break %s%s" % (
            last_good, broken, " · ⚠ STOPPED FROM OUTSIDE" if self.n_stopped else ""))
        if self.n_stopped:
            return 3
        return 0 if broken is None else 1

    def search(self, good, broken):
        """The bisection (§6): every level from a clean box with its N users."""
        while broken - good > 1 and not self.n_stopped:
            n = (good + broken) // 2
            says("🔎 bisection between %d (good) and %d (broken): %d users" % (good, broken, n))
            self.do_update(phase="search", search=[good, broken])
            ok, reason_text = self.clean_box(os.path.join(self.base, "level-%02d" % n))
            if not ok:
                self.block(reason_text)
                break
            cls_name, signif, _d = self.level(n, self.o.minutes, "level-%02d" % n, "search")
            if self.n_stopped:
                break
            if bad(cls_name, signif):
                broken = n
            else:
                good = n
        return good, broken

    def block(self, reason_text):
        says("⛔ BLOCKED: %s" % reason_text)
        self.do_update(phase="BLOCKED", rationale=reason_text)
        return 3

    def clear_out_all(self):
        o = self.o
        self.do_update(phase="sgombero")
        self.stop_actors()
        try:
            clear_out_16(o.cont)
        except Exception as e:                   # noqa: BLE001
            says("⚠ clean-up: %s" % e)
        c, t = compositors("turn_off")
        says("   compositors off (%d)" % t.count("switched off"))
        if self.guard:
            self.guard.alive = False
        if SYSTEM["xrdp"]:
            # the xrdp box is turned off: it frees 3389 and the memory for whoever comes next
            c, t = sudo("podman rm -f -t 10 rete11-%s" % o.cont, 120)
            says("   box rete11-%s off (code %s)" % (o.cont, c))
            return
        if not o.leave_cap and o.ceiling and not o.no_rebuild:
            c, t = sudo("cd %s && bash 11-accendi.sh server %s" % (NETWORK11, o.container_box), 300)
            says("   server put back with the default cap (code %s, cap %s)" % (
                c, cap_in_effect(o.container_box)))


def iso(t):
    return datetime.datetime.fromtimestamp(t).astimezone().isoformat(timespec="seconds")


def bad(cls_name, signif):
    """§6: FAIL or significant DEGRADED stop the climb.  A class that could not
    be read stops it too: no blind climbing."""
    return cls_name not in ("GREEN", "DEGRADED") or (cls_name == "DEGRADED" and signif)


def read_class(out_dir, code_v):
    """(class, significant, reason) from the output of 16-classifica.py: the LAST
    JSON line with «cls_name» (and «significant»), or the last word GREEN /
    DEGRADED / FAIL; otherwise «?» (and the climb stops)."""
    line_list = []
    for row in out_dir.splitlines():
        row = row.strip()
        i = row.find("{")
        if i < 0:
            continue
        try:
            d = json.loads(row[i:])
        except ValueError:
            continue
        if isinstance(d, dict) and str(d.get("cls_name") or "").upper() in CLASSES:
            line_list.append(d)
    # ⭐ the `"kind": "level"` line (16-classifica.py --json), otherwise the last one
    for d in [r for r in line_list if r.get("kind") == "level"][-1:] or line_list[-1:]:
        return (str(d["cls_name"]).upper(), bool(d.get("significant")),
                str(d.get("rationale") or "")[:400])
    words = re.findall(r"\b(GREEN|DEGRADED|FAIL)\b", out_dir)
    if words:
        c = words[-1]
        # ⚠ both forms: the old (Italian) 16-classifica.py and the new (English) one
        return c, bool(re.search(r"(?<!non )(?<!not )(?:significativo|significant)", out_dir, re.I)) \
            and c == "DEGRADED", \
            "(read from the word, code %s)" % code_v
    if code_v in (0, 1, 3):                     # 16-classifica.py: GREEN 0, FAIL 1, DEGRADED 3
        return {0: "GREEN", 1: "FAIL", 3: "DEGRADED"}[code_v], code_v == 3, \
            "(from the exit code %s: DEGRADED counted as significant)" % code_v
    return "?", False, "16-classifica did not say a class (code %s): %s" % (
        code_v, " | ".join(out_dir.strip().splitlines()[-3:])[:300])


def level_birth(started, mtime_birth, t0):
    """⭐ The nascita.json belongs to the level that starts at `t0` if the actor
    started in the level, or if the birth was written in the level."""
    return (started is not None and started >= t0) or mtime_birth >= t0 - 1


def photo_written(dir_user, after):
    """Is the photo asked for at `after` there?  A new picture-* file, or the «picture» event
    (even failed: the actor has finished trying) in eventi.jsonl."""
    try:
        for label_name in os.listdir(dir_user):
            if label_name.startswith("picture-") and os.path.getmtime(os.path.join(dir_user, label_name)) >= after:
                return True
    except OSError:
        return False
    try:
        with open(os.path.join(dir_user, "eventi.jsonl"), encoding="utf-8",
                  errors="replace") as f:
            for row in f:
                if '"picture"' not in row:
                    continue
                try:
                    d = json.loads(row)
                except ValueError:
                    continue
                if d.get("event") == "picture" and (d.get("t") or 0) >= after:
                    return True
    except OSError:
        pass
    return False


def stop_group(p, grace=20):
    """SIGTERM to the group of `p` (the check cleans up its session), then
    SIGKILL if it does not exit in `grace` s."""
    try:
        os.killpg(p.pid, signal.SIGTERM)
    except OSError:
        pass
    try:
        p.wait(timeout=grace)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
        p.wait()


def trim_jsonl(src, dst, t0, t1):
    """The rows of `src` with the instant inside [t0, t1]; the rows without a readable
    instant all pass."""
    keys = ("t", "ts", "time_limit", "epoch", "when", "now", "instant", "orario")
    with open(src, encoding="utf-8", errors="replace") as f, \
            open(dst, "w", encoding="utf-8") as g:
        for row in f:
            try:
                d = json.loads(row)
            except ValueError:
                continue
            t = None
            for k in keys:
                v = d.get(k) if isinstance(d, dict) else None
                if isinstance(v, (int, float)) and v > 1e9:
                    t = v / 1000.0 if v > 1e12 else float(v)
                    break
                if isinstance(v, str) and len(v) >= 19:
                    try:
                        t = datetime.datetime.fromisoformat(v).timestamp()
                        break
                    except ValueError:
                        pass
            if t is None or t0 - 1 <= t <= t1 + 1:
                g.write(row)


# ═══════════════════════════════════════════════════════════════════════════

# ⛔ THE BOXES BELONG TO ONE BENCH AT A TIME (29 Sep 2026, «user unknown» of phase 16):
#   the hook (even the pre-push one, by itself) clears ALL the tenants
#   `c<n>u<n>` before every mesh ⇒ a push during a round deleted the tenants
#   born 7 s earlier (`[M]` 04:28, 04:40, 04:42 of 29 Sep = the 4 FAIL and 36 BLOCKED).
#   The same lock in 15-giro.py, 16-salita.py and 11-gancio.sh; whoever is launched by
#   one of them inherits REMOTIX_KEPT_BOXES and does not take it again.
#   ⚠ NOT in /run/lock: the folder is «sticky» and with fs.protected_regular root does not
#   reopen the file created by nicfio (and the hook says «held» about free boxes, `[M]`).
BOX_LOCK = "/media/REMOTIX/rete11/.scatole.lock"


def keep_boxes(chi):
    """None if the boxes are ours (the lock stays taken until exit),
    otherwise the sentence that says who holds them."""
    if os.environ.get("REMOTIX_KEPT_BOXES"):
        return None
    fd = os.open(BOX_LOCK, os.O_RDWR | os.O_CREAT, 0o666)
    try:
        os.fchmod(fd, 0o666)
    except OSError:
        pass
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        try:
            holds = os.pread(fd, 200, 0).decode(errors="replace").strip()
        except OSError:
            holds = ""
        os.close(fd)
        return "the boxes are already held by another bench (%s)" % (holds or "?")
    os.ftruncate(fd, 0)
    os.pwrite(fd, ("%s pid %d" % (chi, os.getpid())).encode(), 0)
    os.environ["REMOTIX_KEPT_BOXES"] = chi
    globals()["_fd_scatole"] = fd
    return None


def main():
    global _log_file
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--container_box", required=True, choices=sorted(PORTS))
    a.add_argument("--campaign", required=True)
    a.add_argument("--gauge", default="4k", choices=sorted(SCREEN_SIZES))
    a.add_argument("--rungs", default="1,4,8,12,16")
    a.add_argument("--minutes", type=float, default=10)
    a.add_argument("--last-rung-minutes", type=float, default=30)
    a.add_argument("--check-min", type=float, default=2)
    a.add_argument("--base-seed", type=int, default=1600)
    a.add_argument("--fps-video", type=float, default=0)
    a.add_argument("--video", default="")
    a.add_argument("--ceiling", type=int, default=0,
                   help="the server's session cap (default: highest rung + 1, "
                        "for the short check)")
    a.add_argument("--base-ports", type=int, default=9900)
    a.add_argument("--gpu_card", default="intel", choices=sorted(CARD_DRIVER),
                   help="the card of the BOX (REMOTIX_CARD of 11-accendi.sh); the "
                        "client browsers stay on the Intel")
    a.add_argument("--prova", action="store_true",
                   help="test climb §13.3: rungs 1,2,4 of 5 minutes; does not count")
    a.add_argument("--no-card", action="store_true",
                   help="phase 18: encoding WITHOUT a card (OpenH264) — in the rebuilt box "
                        "iHD_drv_video.so is hidden before turning on the server, and we "
                        "require the log to say «H.264: scheda no, software OpenH264 si'».  "
                        "Only a phase 18 binary can do it: since phase 19 (§10.27) the product "
                        "encodes only on the card, and the climb stops at once")
    a.add_argument("--mesa-vulkan-deb", default="",
                   help="phase 20: a mesa-vulkan-drivers_*.deb to install in the box "
                        "before the server (the backport for the Radeon, defect A3)")
    a.add_argument("--system_wide", choices=("remotix", "xrdp"), default="remotix",
                   help="xrdp: the same climb against Debian 13's xrdp (fasi/20 §7)")
    a.add_argument("--guard", action="store_true",
                   help="the host guard of fasi/20 §7.7 (always on with --system_wide xrdp)")
    a.add_argument("--dry", action="store_true", help="prints the plan and that's all")
    a.add_argument("--wait-birth-s", type=int, default=180)
    a.add_argument("--wait-exit-s", type=int, default=120)
    a.add_argument("--check-cap-s", type=int, default=600)
    a.add_argument("--photo-lead-s", type=int, default=30,
                   help="the full photo (SIGUSR1) how many s BEFORE the judgement window")
    a.add_argument("--photo-cap-s", type=int, default=90,
                   help="how long the photos are waited for before the window")
    a.add_argument("--leave-cap", action="store_true")
    # ⚠ only to test the setup, never in a campaign:
    a.add_argument("--even-if-not-empty", action="store_true")
    a.add_argument("--no-rebuild", action="store_true")
    a.add_argument("--no-check", action="store_true")
    a.add_argument("--resources-without-root", action="store_true",
                   help="16-risorse.py as nicfio (the fakes): without root, PSS and fdinfo are not read")
    a.add_argument("--programs", default=HERE,
                   help="the folder of 16-attore/16-risorse/16-classifica (the fakes: finti/)")
    o = a.parse_args()
    if o.prova:
        if "--rungs" not in sys.argv:
            o.rungs = "1,2,4"
        # ⛔ [M] 6 Oct (phase 20 tuning): 3 min = 1 of settling + 2 of short
        #    check ⇒ the memory stretch is EMPTY, «NOT MEASURED» ⇒ DEGRADED at the first
        #    rung.  And at 4 min the series has 60 points in 59 s: 16-classifica wants
        #    more than 60 s ⇒ still NOT MEASURED.  5 min leave 2 min of memory.
        if "--minutes" not in sys.argv:
            o.minutes = 5
        if "--last-rung-minutes" not in sys.argv:
            o.last_rung_minutes = 5
        if not o.campaign.startswith("prova-"):
            o.campaign = "prova-" + o.campaign
    o.rungs = [int(x) for x in str(o.rungs).split(",") if x.strip()]
    if o.rungs != sorted(set(o.rungs)) or not o.rungs or o.rungs[0] < 1:
        a.error("--rungs: increasing numbers from 1 upwards")
    if o.check_min > min(o.minutes, o.last_rung_minutes):
        a.error("--check-min longer than the level")
    # the memory stretch (16-classifica): after 60 s of settling, before the check
    if min(o.minutes, o.last_rung_minutes) * 60 - o.check_min * 60 - 60 < 90:
        a.error("levels too short: at least --check-min + 2.5 minutes are needed "
                "(1 of settling, and the memory wants more than 60 s of series)")
    o.ceiling = o.ceiling or (max(o.rungs) + 1)
    SYSTEM["xrdp"] = o.system_wide == "xrdp"
    o.cont = o.container_box + "-xrdp" if SYSTEM["xrdp"] else o.container_box
    o.guard = o.guard or SYSTEM["xrdp"]
    o.largo, o.alto = SCREEN_SIZES[o.gauge]
    prog = os.path.abspath(o.programs)
    o.prog_actor = os.path.join(prog, "16-attore.py")
    o.prog_resources = os.path.join(prog, "16-risorse.py")
    o.prog_ranking = os.path.join(prog, "16-classifica.py")
    o.prog_check = os.path.join(HERE, "16-controllo-corto.py")
    if SYSTEM["xrdp"]:
        o.prog_actor = os.path.join(prog, "16-attore-rdp.py")
        o.prog_check = os.path.join(HERE, "16-attore-rdp.py")
    if o.dry:
        tot = sum(o.minutes for _ in o.rungs[:-1]) + o.last_rung_minutes
        print("plan: %s · card %s · %s · rungs %s · %s min + last %s ≈ %.0f min of work (+ births, "
              "checks, log) · cap %d · ports %d-%d · programs %s" % (
                  o.campaign, o.gpu_card, o.container_box, o.rungs, o.minutes, o.last_rung_minutes, tot, o.ceiling,
                  o.base_ports, o.base_ports + 10 * max(o.rungs) + 9, prog))
        for p in (o.prog_actor, o.prog_resources, o.prog_ranking, o.prog_check):
            print("  %s %s" % ("✓" if os.path.exists(p) else "✗ MISSING", p))
        return 0
    for p in (o.prog_actor, o.prog_resources, o.prog_ranking, o.prog_check):
        if not os.path.exists(p):
            print("⛔ %s is missing" % p)
            return 3
    base = os.path.join(MEASURES, o.campaign)
    if glob.glob(os.path.join(base, "level-*")):
        print("⛔ the campaign %s already has levels in %s: the evidence is not touched (§14). "
              "Another name." % (o.campaign, base))
        return 3
    os.makedirs(base, exist_ok=True)
    _log_file = open(os.path.join(base, "salita.log"), "a", encoding="utf-8")
    # ⛔ ONE climb at a time on the server
    lock = open(os.path.join(RUN, "16-salita.lock"), "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        says("⛔ BLOCKED: there is already another climb in progress on this server")
        return 3
    trouble = keep_boxes("16-salita %s" % o.campaign)
    if trouble:
        says("⛔ BLOCKED: %s" % trouble)
        return 3
    sal = Climb(o)
    troubles = why_not_empty(o.cont)
    # ⚠ [M] 26 Sep, 00:01: the previous climb had just cleaned up and the tenant's
    #   session was still closing (logind) 6 s later ⇒ false BLOCKED.  Whoever
    #   is closing is waited for up to 120 s; whoever is left after that is a non-empty server.
    for _ in range(12):
        if not troubles:
            break
        time.sleep(10)
        troubles = why_not_empty(o.cont)
    if troubles:
        sal.state["server_non_vuoto"] = troubles
        if not o.even_if_not_empty:
            return sal.block("the server is not empty: " + " · ".join(troubles))
        says("⚠ the server is NOT empty (--even-if-not-empty, test of the setup): " +
             " · ".join(troubles))

    def n_stopped(sig, _f):
        says("⚠ signal %d: stopping and cleaning up" % sig)
        sal.n_stopped = True
    signal.signal(signal.SIGTERM, n_stopped)
    signal.signal(signal.SIGINT, n_stopped)
    code_v = 3
    try:
        code_v = sal.run_loop()
    except Exception as e:                       # noqa: BLE001
        import traceback
        says("⛔ the climb crashed: %r\n%s" % (e, traceback.format_exc()))
        sal.do_update(phase="drop", rationale=repr(e))
    finally:
        sal.clear_out_all()
        if sal.state.get("phase") not in ("BLOCKED", "drop"):
            sal.do_update(phase="ended" if not sal.n_stopped else "fermata")
        says("end · %s" % json.dumps(sal.history, ensure_ascii=False))
    return code_v


if __name__ == "__main__":
    sys.exit(main())
