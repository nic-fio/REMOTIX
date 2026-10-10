#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===========================================================================
16-salita — A CLIMB IN RUNGS OF PHASE 16 (fasi/16-stress-e-capacita.md §6)
===========================================================================

    (on the server, as nicfio — the client browsers run there, §2)
    python3 16-salita.py --scatola gnome --campagna intel-4k-gnome --misura 4k
    python3 16-salita.py --scatola lxqt --campagna taratura --misura 4k --prova
    python3 16-salita.py ... --secco              # the plan, without doing anything
    python3 16-salita.py --scatola kde --campagna amd-4k-kde --scheda amd   # §11, the Radeon

    options:  --gradini 1,4,8,12,16  --minuti 10  --minuti-ultimo 30
              --controllo-min 2  --seme-base 1600  --fps-video F  --video URL
              --tetto 17  --porte-base 9900  --prova (§13.3: 1,2,4 of 5 min)
              --scheda intel|amd  (the card of the BOX, default intel)

THE CARD (§11, two campaigns)
  --scheda passes REMOTIX_SCHEDA to `11-accendi.sh accendi`: ONE card only
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
  1. rebuilds the box FROM SCRATCH (11-accendi.sh accendi · prodotto · server, like
     15-rifai-scatole.sh) with the server on at `--tetto` sessions
     (REMOTIX_TETTO_SESSIONI, see 11-accendi.sh) and LOOKS in the log that the
     cap has come into force;
  2. for every rung: turns on the compositors needed (16-compositori.sh),
     brings in the missing actors (16-attore.py, one process per user,
     independent: seed = seme-base + N, porte-base + 10·N, its labwc) —
     one after the other, each when the previous one has the first frame
     (§6: this way birth under load is measured) —, 16-risorse.py for the whole
     level, the minutes of the level at steady work; `--anticipo-foto-s`
     (30) BEFORE the last `--controllo-min` minutes SIGUSR1 to the actors (the
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
  4. the last rung lasts `--minuti-ultimo` (memory leaks, §6);
  5. at the end: actors stopped (SIGTERM: they clean up by themselves), c16* tenants
     cleaned up anyway, compositors off, the server put back with the default
     cap (unless --lascia-tetto).

THE EVIDENCE (§10) in /media/REMOTIX/misure/fase16/<campagna>/:
    stato.json              the current point, for the coordinator
    salita.jsonl            one row per level (meta + class)
    salita.log              what comes out here, with the times
    attori-<k>/utente-NN/   what the actors write (k: one per clean box)
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

--sistema xrdp (fasi/20-le-prestazioni.md §7, 9 Oct 2026) — the SAME climb against xrdp:
  the box is `rete11-<desktop>-xrdp` (Contenitore.xrdp), and before turning it on
  EVERY rete11-*-xrdp is turned off and port 3389 is required free (`--network=host`: one port
  only for the host; on 9 Oct a box left on answered in place of the
  others); xrdp and xrdp-sesman are turned on with Debian's files AS THEY ARE; the clients are
  16-attore-rdp.py in the Xvfb of 16-compositori-rdp.sh; the short check is
  16-attore-rdp.py --controllo (§7.3, reduced); server.log = the new lines of
  /var/log/xrdp.log and xrdp-sesman.log; livello.json carries the package versions in
  place of commit and binary; 16-classifica.py --sistema xrdp.  No session
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

QUI = os.path.dirname(os.path.abspath(__file__))
BANCHI = os.path.dirname(QUI)
RETE11 = os.environ.get("REMOTIX_RETE11", "/media/REMOTIX/rete11")
MISURE = os.environ.get("REMOTIX_MISURE_16", "/media/REMOTIX/misure/fase16")
PRODOTTO16 = os.environ.get("REMOTIX_PRODOTTO_16", "/media/REMOTIX/src/16-prodotto")
PORTE = {"gnome": 8511, "kde": 8512, "xfce": 8513, "lxqt": 8514}
MISURE_SCHERMO = {"4k": (3840, 2160), "3k": (3200, 1800), "2k": (2560, 1440),
                  "fhd": (1920, 1080)}
SCHEDE_NOTE = {"8086:4680": "Intel UHD 770 (i5-13500T)", "1002:73bf": "AMD Radeon RX 6800"}
CLASSI = ("GREEN", "DEGRADED", "FAIL")
UID = os.getuid()
RUN = "/run/user/%d" % UID
COMPOSITORI = os.path.join(RUN, "16-compositori")
INQUILINO_16 = re.compile(r"^c16[0-9]+u[0-9]+$")
COMPOSITORI_RDP = os.path.join(RUN, "16-compositori-rdp")
GUARDIA_MEM_MB = 3 * 1024           # §7.7: below it, the level is closed
GUARDIA_PSI_FULL = 20.0             # §7.7: «full avg10» beyond it, the level is closed
PACCHETTI_XRDP = ("xrdp", "xorgxrdp", "pipewire-module-xrdp", "xserver-xorg-core", "xfwm4", "openbox",
                  "kwin-x11", "gnome-session-xsession", "firefox-esr", "mesa-va-drivers")
PACCHETTI_OSPITE_XRDP = ("freerdp3-x11", "xvfb", "python3-xlib", "x11-utils", "python3-pil")
AMBIENTE_BROWSER = {
    "XDG_RUNTIME_DIR": RUN, "REMOTIX_SCHERMO_ANNIDATO": "1", "REMOTIX_SUL_SERVER": "1",
    "MOZ_ENABLE_WAYLAND": "1",
    "REMOTIX_CHROME_OPZIONI": "--ozone-platform=wayland --disable-backgrounding-occluded-windows "
                              "--disable-renderer-backgrounding --disable-background-timer-throttling"}

_stampa = threading.Lock()
_log_file = None


def ora():
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def dice(msg):
    riga = "[%s] %s" % (time.strftime("%H:%M:%S"), msg)
    with _stampa:
        print(riga, flush=True)
        if _log_file:
            _log_file.write(riga + "\n")
            _log_file.flush()


def _parola_sudo():
    """The server's sudo password: from REMOTIX_PAROLA_SUDO, or from the «pass:» line of
    ~/SERVER.ssh. ⛔ Never written in the benches: they are in the repository."""
    p = os.environ.get("REMOTIX_PAROLA_SUDO")
    if p is None:
        try:
            for r in open(os.path.expanduser("~/SERVER.ssh")):
                if r.startswith("pass:"):
                    p = r.split(":", 1)[1].strip()
                    break
        except OSError:
            pass
    return (p or "") + "\n"


def sudo(comando, secondi=300):
    try:
        r = subprocess.run(["sudo", "-S", "-p", "", "sh", "-c", comando], input=_parola_sudo(),
                           capture_output=True, text=True, errors="replace", timeout=secondi)
    except subprocess.TimeoutExpired:
        return None, "(no answer in %d s)" % secondi
    return r.returncode, (r.stdout + r.stderr).strip()


def _q(s):
    return "'" + s.replace("'", "'\"'\"'") + "'"


def nella_scatola(d, comando, secondi=120):
    return sudo("podman exec rete11-%s sh -c %s" % (d, _q(comando)), secondi)


def scrivi_json(p, dati):
    with open(p + ".tmp", "w", encoding="utf-8") as f:
        json.dump(dati, f, ensure_ascii=False, indent=1)
    os.replace(p + ".tmp", p)


def md5_8(p, quanti=8):
    try:
        h = hashlib.md5()
        with open(p, "rb") as f:
            for b in iter(lambda: f.read(1 << 20), b""):
                h.update(b)
        return h.hexdigest()[:quanti]
    except OSError:
        return "?"


def comando(argv, secondi=30):
    try:
        r = subprocess.run(argv, capture_output=True, text=True, errors="replace",
                           timeout=secondi)
        return (r.stdout + r.stderr).strip()
    except Exception as e:                       # noqa: BLE001
        return "? (%s)" % e


# ═══════════════════════════════════════════════════════════════════════════
#  THE MACHINE: what is measured (§10, in every row)
# ═══════════════════════════════════════════════════════════════════════════
def schede():
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
        out.append({"scheda": SCHEDE_NOTE.get(idn, idn), "id": idn, "driver": drv, "pci": pci})
    return out


def meta_macchina(o):
    m = {"kernel": os.uname().release,
         "cpu": next((r.split(":", 1)[1].strip() for r in open("/proc/cpuinfo")
                      if r.startswith("model name")), "?"),
         "schede": schede(),
         "prodotto_binario": md5_8(os.path.join(RETE11, "prodotto", "remotix")),
         "prodotto_pagina": md5_8(os.path.join(RETE11, "prodotto", "pagina.html")),
         "firefox": comando(["firefox", "--version"]),
         "chrome": comando(["google-chrome", "--version"])}
    try:
        m["commit_banchi"] = open(os.path.join(BANCHI, "..", "VERSIONE")).read().strip()
    except OSError:
        m["commit_banchi"] = "?"
    try:
        m["scheda_compositori"] = open(os.path.join(COMPOSITORI, "render")).read().strip()
    except OSError:
        m["scheda_compositori"] = "?"
    # ⭐ the PRODUCT's commit: /media/REMOTIX/src/16-prodotto/VERSIONE, valid only if
    #   the binary there is THE SAME as rete11/prodotto (whole md5)
    m["commit_prodotto"] = None
    b = os.path.join(PRODOTTO16, "src", "remotix")
    if os.path.exists(b) and md5_8(b, 32) == md5_8(os.path.join(RETE11, "prodotto", "remotix"), 32):
        try:
            m["commit_prodotto"] = open(os.path.join(PRODOTTO16, "VERSIONE")).read().strip()
        except OSError:
            pass
    # ⭐ phase 20: the label beside the binary, «<commit> <md5 at 8>», written when it is
    #   copied into rete11/prodotto; valid only if the md5 is still that of the binary
    if not m["commit_prodotto"]:
        try:
            commit, md5 = open(os.path.join(RETE11, "prodotto", "VERSIONE")).read().split()[:2]
            if md5 == md5_8(os.path.join(RETE11, "prodotto", "remotix"), 32)[:8]:
                m["commit_prodotto"] = commit
        except (OSError, ValueError):
            pass
    return m


DRIVER_SCHEDA = {"intel": ("i915", "xe"), "amd": ("amdgpu",)}


def scheda_di(quale):
    """The `intel` or `amd` card (dict of schede()) and its render node, by
    PCI address (like 11-accendi.sh).  (card, node) or (None, None)."""
    for s in schede():
        if s["driver"] in DRIVER_SCHEDA[quale]:
            p = os.path.realpath("/dev/dri/by-path/pci-%s-render" % s["pci"])
            if os.path.exists(p):
                return s, p
    return None, None


def render_intel():
    """The render node of the integrated Intel, by PCI address (like 11-accendi.sh)."""
    s, p = scheda_di("intel")
    return (p, s["pci"]) if s else (None, None)


def scheda_giusta(o, d):
    """⛔ «Written is not in force»: the renderD128 INSIDE the box must be
    the same device (major:minor) as the node of the card asked for.  (ok, reason)"""
    s, nodo = scheda_di(o.scheda)
    if not s:
        return False, "on the host I cannot find the card «%s» (driver %s)" % (
            o.scheda, "/".join(DRIVER_SCHEDA[o.scheda]))
    st = os.stat(nodo)
    fuori = "%x:%x" % (os.major(st.st_rdev), os.minor(st.st_rdev))
    _c, t = nella_scatola(d, "stat -c %t:%T /dev/dri/renderD128", 60)
    dentro = (t or "").strip().splitlines()[-1:] or ["?"]
    if dentro[0] != fuori:
        return False, "the box's renderD128 (%s) is NOT %s (%s, %s = %s)" % (
            dentro[0], s["scheda"], s["pci"], nodo, fuori)
    dice("   ⭐ card of the box: %s [%s] %s = renderD128 inside" % (
        s["scheda"], s["driver"], s["pci"]))
    return True, ""


def ambiente_browser(s):
    """The environment of the client browsers (actors and check).  ⭐ Chrome is pinned
    to the Intel (--render-node-override): renderD128/129 swap between two boots,
    and the server also has the RX 6800.  Firefox follows the labwc (which is on the Intel)."""
    amb = dict(os.environ, WAYLAND_DISPLAY=s, **AMBIENTE_BROWSER)
    nodo, _pci = render_intel()
    if nodo:
        amb["REMOTIX_16_CHROME_IN_PIU"] = "--render-node-override=%s" % nodo
        amb["REMOTIX_CHROME_OPZIONI"] += " --render-node-override=%s" % nodo
    return amb


def ambiente_rdp(d):
    """The environment of the xrdp clients: their Xvfb, no Wayland."""
    amb = dict(os.environ, DISPLAY=d, XDG_RUNTIME_DIR=RUN, REMOTIX_SUL_SERVER="1")
    amb.pop("WAYLAND_DISPLAY", None)
    return amb


def browser_fuori_scheda(dirliv):
    """From the resources series: the processes of the client browsers (enclosures `browser`
    and `labwc_cliente`) that draw on a card that is NOT the Intel."""
    _n, pci = render_intel()
    fuori, visti = {}, 0
    try:
        for r in open(os.path.join(dirliv, "risorse.jsonl"), encoding="utf-8", errors="replace"):
            try:
                d = json.loads(r)
            except ValueError:
                continue
            for p in d.get("processi_gpu") or []:
                if p.get("recinto") not in ("browser", "labwc_cliente"):
                    continue
                visti += 1
                if pci and p.get("pdev") and p["pdev"] != pci:
                    k = "%s@%s" % (p.get("comm"), p["pdev"])
                    fuori[k] = fuori.get(k, 0) + 1
    except OSError:
        return None
    return {"campioni_browser": visti, "fuori_intel": fuori, "intel": pci}


def meta_scatola(d):
    """Inside the box: binary and page IN USE, the card it sees, the drivers."""
    v = {}
    _c, t = nella_scatola(d, "md5sum /opt/remotix/remotix /opt/remotix/pagina.html; "
                             "echo @@; ls /dev/dri; echo @@; dpkg-query -W -f "
                             "'${Package}=${Version}\\n' intel-media-va-driver "
                             "intel-media-va-driver-non-free mesa-va-drivers libva2 "
                             "libgl1-mesa-dri 2>/dev/null; echo @@; "
                             "systemctl show -p ExecStart --value rete11-server 2>/dev/null "
                             "| tr ' ' '\\n' | grep -A1 -E '^--(tetto-sessioni|journal)' "
                             "| tr '\\n' ' '; echo @@; vainfo --display drm --device "
                             "/dev/dri/renderD128 2>&1 | grep -m1 'Driver version'; echo @@; "
                             "grep -a -o 'HEVC: .*H.264: scheda [^,]*, software OpenH264 [^ ]*' "
                             "/var/lib/rete11/registro.log 2>/dev/null | tail -1", 60)
    parti = (t or "").split("@@")
    while len(parti) < 6:
        parti.append("")
    for riga in parti[0].splitlines():
        p = riga.split()
        if len(p) == 2:
            v["binario" if p[1].endswith("remotix") else "pagina"] = p[0][:8]
    v["dri_nella_scatola"] = parti[1].split()
    v["driver_video"] = [x for x in parti[2].split() if "=" in x and not x.endswith("=")]
    v["opzioni_server"] = parti[3].strip()
    v["journal"] = "--journal" in parti[3]
    # ⭐ the VA provider the box sees on ITS renderD128 (iHD or radeonsi)
    v["driver_va"] = parti[4].split(":", 1)[-1].strip() or "?"
    # ⭐ phase 18: what the product MEASURED at startup (the ECCOMI line):
    #   «H.264: scheda si' (…), software OpenH264 si'» in hardware; with --senza-scheda
    #   «H.264: scheda no (…), software OpenH264 si'» — this way the level declares the route
    v["codifica_video"] = parti[5].strip() or "?"
    return v


# ═══════════════════════════════════════════════════════════════════════════
#  THE EMPTY SERVER (§6.1, §13.0)
# ═══════════════════════════════════════════════════════════════════════════
def scatole_accese():
    c, t = sudo("podman ps --format '{{.Names}}'", 60)
    return [x for x in (t or "").split() if x.startswith("rete11-")]


def perche_non_vuoto(d):
    guai = []
    for s in scatole_accese():
        _c, t = sudo("podman exec %s awk -F: '$1 ~ /^c16[0-9]+u[0-9]+$/ {print $1}' /etc/passwd"
                     % s, 60)
        if t.strip():
            guai.append("in %s there are phase 16 tenants: %s" % (s, " ".join(t.split())))
    if "rete11-%s" % d in scatole_accese():
        _c, t = nella_scatola(d, "loginctl list-users --no-legend 2>/dev/null | awk '{print $2}'")
        chi = [u for u in (t or "").split() if u and u not in ("root",)]
        if chi:
            guai.append("in rete11-%s there are sessions: %s" % (d, " ".join(chi)))
    me = os.getpid()
    t = comando(["pgrep", "-u", str(UID), "-af",
                 "marionette|remote-debugging-port|16-attore|16-controllo-corto|xfreerdp3"])
    browser = [r for r in t.splitlines() if r.strip() and not r.startswith("%d " % me)
               and "pgrep" not in r]
    if browser:
        guai.append("%d bench browser/actor processes alive (e.g. %s)" % (
            len(browser), browser[0][:120]))
    return guai


# ═══════════════════════════════════════════════════════════════════════════
#  THE BOX
# ═══════════════════════════════════════════════════════════════════════════
def rifai_scatola(o, d, tetto, dove):
    """accendi · prodotto · server, like 15-rifai-scatole.sh.  (ok, reason)"""
    for passo in ("accendi", "prodotto", "server"):
        amb = "env REMOTIX_TETTO_SESSIONI=%d " % tetto if (passo == "server" and tetto) else ""
        if passo == "accendi":
            amb = "env REMOTIX_SCHEDA=%s " % o.scheda
        t0 = time.time()
        c, t = sudo("cd %s && %sbash 11-accendi.sh %s %s" % (RETE11, amb, passo, d), 900)
        # ⛔ [M] 26 Sep 00:35: the bisection rebuilds the box in the folder of a
        #    level that does not exist yet ⇒ FileNotFoundError and climb crashed
        os.makedirs(dove, exist_ok=True)
        with open(os.path.join(dove, "scatola-%s.log" % passo), "a") as f:
            f.write("=== %s\n%s\n" % (ora(), t))
        ultima = [x for x in (t or "").splitlines() if x.strip()][-1:] or [""]
        dice("   box %s: code %s in %.0f s · %s" % (passo, c, time.time() - t0,
                                                     re.sub(r"\x1b\[[0-9;]*m", "", ultima[0])[:120]))
        if c != 0:
            return False, "11-accendi.sh %s %s failed (code %s): %s" % (
                passo, d, c, re.sub(r"\x1b\[[0-9;]*m", "", " ".join((t or "").splitlines()[-3:]))[:300])
        # ⭐ phase 18, --senza-scheda: BEFORE turning on the server the box's VA driver
        #   is hidden (iHD_drv_video.so renamed), as in the software smoke round
        #   (fasi/18 §4): the child composes the environment from scratch and LIBVA_DRIVER_NAME is not enough.
        #   The compositor keeps drawing on the card (Mesa iris): it is only the
        #   encoding that drops to OpenH264, which is the product's route without a driver.
        if passo == "prodotto" and getattr(o, "senza_scheda", False):
            c2, t2 = nella_scatola(d, "cd /usr/lib/x86_64-linux-gnu/dri && mv iHD_drv_video.so "
                                      "iHD_drv_video.so.nascosto && ls iHD_drv_video.so* ")
            dice("   box VA driver hidden: code %s · %s" % (c2, (t2 or "").strip()[:80]))
            if c2 != 0 or "iHD_drv_video.so.nascosto" not in (t2 or ""):
                return False, "I could not hide iHD_drv_video.so in the box: %s" % t2
        # ⭐ phase 20, --mesa-vulkan-deb: BEFORE turning on the server another
        #   mesa-vulkan-drivers is installed in the box (the Debian 13 backport), to see whether the Radeon's
        #   A3 defect disappears with RADV >= 25.1, which translates `ULTRA_LOW_LATENCY` to the firmware
        #   (~/Documenti/AMD §5-ter). We require dpkg to state the package version.
        if passo == "prodotto" and getattr(o, "mesa_vulkan_deb", ""):
            deb = o.mesa_vulkan_deb
            c2, t2 = sudo("podman cp %s rete11-%s:/tmp/mesa-vulkan.deb" % (_q(deb), d), 120)
            if c2 == 0:
                c2, t2 = nella_scatola(d, "dpkg -i /tmp/mesa-vulkan.deb >/dev/null 2>&1; "
                                          "dpkg-query -W -f '${Version}' mesa-vulkan-drivers", 300)
            atteso = re.sub(r"^.*mesa-vulkan-drivers_([^_]+)_.*$", r"\1", os.path.basename(deb))
            dice("   box mesa-vulkan-drivers: code %s · %s" % (c2, (t2 or "").strip()[:80]))
            if c2 != 0 or (t2 or "").strip() != atteso:
                return False, "mesa-vulkan-drivers %s not installed in the box: %s" % (atteso, t2)
    ok, perche = scheda_giusta(o, d)
    if not ok:
        return False, perche
    if getattr(o, "senza_scheda", False):
        cv = meta_scatola(d).get("codifica_video", "")
        if "H.264: scheda no (" not in cv or "software OpenH264 si'" not in cv:
            return False, "the server does not declare H.264 encoding in software (it says «%s»)" % cv
        dice("   ⭐ encoding declared by the product: %s" % cv)
    if tetto:
        v = tetto_in_vigore(d)
        if v != tetto:
            return False, "the server does not say «ADMINISTRATIVE session cap: **%d**» " \
                          "(it says %s)" % (tetto, v)
        dice("   ⭐ session cap in force: %d" % v)
    return True, ""


def tetto_in_vigore(d):
    # ⚠ BOTH forms of the product's line: the old (Italian) binary and the new (English) one
    _c, t = nella_scatola(d, "{ cat /var/lib/rete11/registro.log 2>/dev/null; journalctl -u "
                             "rete11-server -b --no-pager -o cat 2>/dev/null; } | grep -a -E "
                             "'tetto AMMINISTRATIVO delle sessioni|ADMINISTRATIVE session cap' | tail -1", 60)
    m = re.search(r"(?:sessioni|session cap): \*\*(\d+)\*\*", t or "")
    return int(m.group(1)) if m else None


def meta_scatola_xrdp(d):
    """Inside the xrdp box: the versions, the card, and whether the xrdp configuration is
    the package's (dpkg --verify: no line = files intact)."""
    v = {"binario": None, "pagina": None, "opzioni_server": "Debian 13 xrdp, package configuration",
         "codifica_video": "RemoteFX on the processor (Debian's xrdp without H.264)"}
    _c, t = nella_scatola(d, "dpkg-query -W -f '${Package}=${Version}\\n' %s 2>/dev/null; echo @@; "
                             "ls /dev/dri; echo @@; dpkg --verify xrdp xorgxrdp 2>&1 | grep -v '^$' "
                             "| head -5; echo @@; vainfo --display drm --device /dev/dri/renderD128 2>&1 "
                             "| grep -m1 'Driver version'" % " ".join(PACCHETTI_XRDP), 60)
    parti = (t or "").split("@@") + ["", "", "", ""]
    v["pacchetti"] = dict(x.split("=", 1) for x in parti[0].split() if "=" in x)
    v["dri_nella_scatola"] = parti[1].split()
    v["xrdp_configurazione"] = "the package's (dpkg --verify clean)" if not parti[2].strip() \
        else "⚠ MODIFIED: " + " | ".join(parti[2].strip().splitlines())
    v["driver_va"] = parti[3].split(":", 1)[-1].strip() or "?"
    v["driver_video"] = ["%s=%s" % kv for kv in sorted(v["pacchetti"].items())
                         if kv[0] in ("mesa-va-drivers",)]
    t = comando(["dpkg-query", "-W", "-f", "${Package}=${Version}\n"] + list(PACCHETTI_OSPITE_XRDP))
    v["pacchetti_ospite"] = dict(x.split("=", 1) for x in t.split() if "=" in x)
    return v


def ospite_pronto_xrdp():
    """⚠ The host's root is in RAM: after a reboot the client packages are no longer
    there.  They are checked, and if missing they are installed (declared).  (ok, reason)"""
    t = comando(["dpkg-query", "-W", "-f", "${Package} ${db:Status-Status}\n"] + list(PACCHETTI_OSPITE_XRDP))
    mancano = [p for p in PACCHETTI_OSPITE_XRDP if "%s installed" % p not in t]
    if not mancano:
        return True, ""
    dice("   ⚠ on the host %s are missing: installing them" % " ".join(mancano))
    c, t = sudo("DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends %s"
                % " ".join(mancano), 900)
    if c != 0:
        return False, "client packages not installed on the host: %s" % (t or "")[-300:]
    return True, ""


def proteggi_ssh():
    """§7.7: if the kernel has to kill something, NOT sshd (without it, the machine stays
    unreachable and a reboot loses key and provisioning).  At once on the live
    processes, and a drop-in in /run for an sshd restart (it disappears on reboot, like everything)."""
    c, t = sudo("for p in $(pgrep -x 'sshd|sshd-session'); do echo -900 > /proc/$p/oom_score_adj; done; "
                "mkdir -p /run/systemd/system/ssh.service.d && printf '[Service]\\nOOMScoreAdjust=-900\\n' "
                "> /run/systemd/system/ssh.service.d/remotix-oom.conf && systemctl daemon-reload && "
                "for p in $(pgrep -x 'sshd|sshd-session'); do cat /proc/$p/oom_score_adj; done | sort | uniq -c", 60)
    dice("   sshd protected from the kernel (oom_score_adj): %s" % " · ".join((t or "?").split("\n"))[:120])


def rifai_scatola_xrdp(o, d, dove):
    """The xrdp box from scratch: the other xrdp ones off, 3389 free, accendi, xrdp
    on, the card checked.  (ok, reason)"""
    os.makedirs(dove, exist_ok=True)
    for s in scatole_accese():
        if s.endswith("-xrdp"):
            c, t = sudo("podman rm -f -t 10 %s" % s, 120)
            dice("   turned off %s (3389 is one per host): code %s" % (s, c))
    t = comando(["ss", "-ltnH", "sport = :3389"])
    if t.strip():
        return False, "the host's port 3389 is taken: %s" % t.strip()[:160]
    ok, perche = ospite_pronto_xrdp()
    if not ok:
        return False, perche
    t0 = time.time()
    c, t = sudo("cd %s && env REMOTIX_SCHEDA=%s bash 11-accendi.sh accendi %s" % (RETE11, o.scheda, d), 900)
    with open(os.path.join(dove, "scatola-accendi.log"), "a") as f:
        f.write("=== %s\n%s\n" % (ora(), t))
    ultima = [x for x in (t or "").splitlines() if x.strip()][-1:] or [""]
    dice("   box accendi %s: code %s in %.0f s · %s" % (d, c, time.time() - t0,
                                                         re.sub(r"\x1b\[[0-9;]*m", "", ultima[0])[:120]))
    if c != 0:
        return False, "11-accendi.sh accendi %s failed (code %s): %s" % (
            d, c, re.sub(r"\x1b\[[0-9;]*m", "", " ".join((t or "").splitlines()[-3:]))[:300])
    c, t = nella_scatola(d, "systemctl start xrdp-sesman xrdp && for i in $(seq 1 60); do "
                            "ss -ltnH 'sport = :3389' | grep -q . && { systemctl is-active xrdp xrdp-sesman "
                            "| tr '\\n' ' '; exit 0; }; sleep 0.25; done; systemctl status xrdp --no-pager "
                            "| tail -5; exit 1", 120)
    dice("   xrdp on: code %s · %s" % (c, (t or "").strip()[:100]))
    if c != 0:
        return False, "xrdp is not listening on 3389 in the box: %s" % (t or "")[-300:]
    return scheda_giusta(o, d)


class Guardia(threading.Thread):
    """§7.7: every 2 s MemAvailable and the memory pressure; `motivo` when it trips."""

    def __init__(self):
        super().__init__(daemon=True)
        self.motivo = None
        self.ultima = {}
        self.vivo = True

    @staticmethod
    def leggi():
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
    def giudica(mem, psi):
        if mem is not None and mem < GUARDIA_MEM_MB:
            return "available memory %d MB < %d MB" % (mem, GUARDIA_MEM_MB)
        if psi is not None and psi > GUARDIA_PSI_FULL:
            return "memory pressure full avg10 %.1f %% > %.0f %%" % (psi, GUARDIA_PSI_FULL)
        return None

    def run(self):
        while self.vivo:
            mem, psi = self.leggi()
            self.ultima = {"mem_disponibile_mb": mem, "psi_full_avg10": psi}
            m = self.giudica(mem, psi)
            if m and not self.motivo:
                self.motivo = m
                dice("⛔ HOST GUARD (§7.7): %s — closing the level" % m)
            time.sleep(2)

    def riarma(self, attesa_s=180):
        """Before a level: wait for the memory to have come back (at most `attesa_s`)."""
        fine = time.time() + attesa_s
        while time.time() < fine and self.giudica(*self.leggi()):
            time.sleep(5)
        self.motivo = None
        return self.giudica(*self.leggi())


SGOMBERO_16 = r"""
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


def sgombera_16(d):
    """The c16* tenants out of the box (the line of 15-giro.py, only ours)."""
    _c, t = nella_scatola(d, SGOMBERO_16, 300)
    n = len([r for r in (t or "").splitlines() if r.startswith("cleared")])
    if n:
        dice("   cleared %d leftover c16 tenants" % n)


# ═══════════════════════════════════════════════════════════════════════════
#  THE COMPOSITORS
# ═══════════════════════════════════════════════════════════════════════════
SISTEMA = {"xrdp": False}


def compositori(azione, *arg):
    prog = "16-compositori-rdp.sh" if SISTEMA["xrdp"] else "16-compositori.sh"
    r = subprocess.run(["bash", os.path.join(QUI, prog), azione] + list(arg),
                       capture_output=True, text=True, errors="replace", timeout=300)
    return r.returncode, r.stdout + r.stderr


def display_di(n):
    """xrdp: the display of this user's Xvfb (16-compositori-rdp.sh), if alive."""
    try:
        d = open(os.path.join(COMPOSITORI_RDP, "u%02d" % n)).read().strip()
    except OSError:
        return None
    return d if d.startswith(":") and os.path.exists("/tmp/.X11-unix/X%s" % d[1:]) else None


def socket_di(n):
    if SISTEMA["xrdp"]:
        return display_di(n)
    try:
        s = open(os.path.join(COMPOSITORI, "u%02d" % n)).read().strip()
    except OSError:
        return None
    return s if s and os.path.exists(os.path.join(RUN, s)) else None


# ═══════════════════════════════════════════════════════════════════════════
#  THE ACTORS
# ═══════════════════════════════════════════════════════════════════════════
class Attore:
    def __init__(self, o, n, livello, cartella):
        self.o, self.n, self.livello, self.cartella = o, n, livello, cartella
        self.dir_utente = os.path.join(cartella, "utente-%02d" % n)
        self.proc = None
        self.partito = None
        self.nato = None
        self.morto_annotato = False

    def avvia(self):
        s = socket_di(self.n)
        if not s:
            raise RuntimeError("the compositor u%02d is not there" % self.n)
        largo, alto = self.o.largo, self.o.alto
        cmd = [sys.executable, self.o.prog_attore, "--scatola", self.o.scatola,
               "--utente", str(self.n), "--display" if SISTEMA["xrdp"] else "--wayland", s,
               "--dir", self.cartella,
               "--seme", str(self.o.seme_base + self.n), "--largo", str(largo),
               "--alto", str(alto), "--porte-base", str(self.o.porte_base + 10 * self.n)]
        if self.o.video:
            cmd += ["--video", self.o.video]
        amb = ambiente_browser(s) if not SISTEMA["xrdp"] else ambiente_rdp(s)
        os.makedirs(self.dir_utente, exist_ok=True)
        self.log = open(os.path.join(self.cartella, "utente-%02d.log" % self.n), "a")
        self.log.write("=== %s %s\n" % (ora(), " ".join(cmd)))
        self.log.flush()
        self.proc = subprocess.Popen(cmd, stdout=self.log, stderr=subprocess.STDOUT,
                                     env=amb, cwd=QUI, start_new_session=True)
        self.partito = time.time()
        return s

    def vivo(self):
        return self.proc is not None and self.proc.poll() is None

    def e_nato(self):
        if self.nato is None and os.path.exists(os.path.join(self.dir_utente, "nascita.json")):
            self.nato = time.time()
        return self.nato is not None

    def segnale(self, sig):
        if self.vivo():
            try:
                os.kill(self.proc.pid, sig)
            except OSError:
                pass

    def uccidi(self):
        if self.proc is not None:
            try:
                os.killpg(self.proc.pid, signal.SIGKILL)
            except OSError:
                pass


# ═══════════════════════════════════════════════════════════════════════════
#  THE CLIMB
# ═══════════════════════════════════════════════════════════════════════════
class Salita:
    def __init__(self, o):
        self.o = o
        self.base = os.path.join(MISURE, o.campagna)
        self.attori = {}                 # n -> Attore
        self.giro_attori = 0             # one attori-<k> folder per clean box
        self.cartella_attori = None
        self.storia = []
        self.livelli_fatti = 0
        self.fermati = False
        self.stato = {"campagna": o.campagna, "scatola": o.scatola, "misura": o.misura,
                      "gradini": o.gradini, "pid": os.getpid(), "inizio": ora(),
                      "fase": "preparo", "gradino": None, "livello_dir": None,
                      "utenti_vivi": 0, "utenti_attesi": 0, "classe_ultimo": None,
                      "storia": self.storia, "prova": o.prova}
        self.meta = {}
        self.guardia = None
        self.ospite = None               # §7.7: the reason, if the guard tripped in the level
        if o.guardia:
            self.guardia = Guardia()
            self.guardia.start()

    # -- the state for the coordinator ---------------------------------------
    def aggiorna(self, **k):
        self.stato.update(k)
        self.stato["utenti_vivi"] = sum(1 for a in self.attori.values() if a.vivo())
        self.stato["aggiornato"] = ora()
        try:
            scrivi_json(os.path.join(self.base, "stato.json"), self.stato)
        except OSError as e:
            dice("⚠ stato.json not written: %s" % e)

    def nuova_cartella_attori(self):
        self.giro_attori += 1
        self.cartella_attori = os.path.join(self.base, "attori-%d" % self.giro_attori)
        os.makedirs(self.cartella_attori, exist_ok=True)

    # -- the pieces -----------------------------------------------------------
    def ferma_attori(self):
        vivi = [a for a in self.attori.values() if a.vivo()]
        if vivi:
            dice("   stopping %d actors (SIGTERM: they clean up by themselves)" % len(vivi))
        for a in vivi:
            a.segnale(signal.SIGTERM)
        fine = time.time() + self.o.attesa_uscita_s
        while time.time() < fine and any(a.vivo() for a in vivi):
            time.sleep(1)
        duri = [a for a in vivi if a.vivo()]
        if duri:
            dice("   ⚠ %d actors did not exit in %d s: SIGKILL to the group (%s)" % (
                len(duri), self.o.attesa_uscita_s, ", ".join("u%02d" % a.n for a in duri)))
        for a in self.attori.values():
            if a.vivo():
                a.uccidi()
        self.attori = {}

    def scatola_pulita(self, dove):
        """Actors out, tenants out, box rebuilt with the cap.  (ok, reason)"""
        self.aggiorna(fase="rifaccio la scatola")
        self.ferma_attori()
        if self.o.non_rifare:
            dice("⚠ --non-rifare: the box is NOT rebuilt (only tests of the setup)")
            sgombera_16(self.o.cont)
            ok, perche = True, ""
        elif SISTEMA["xrdp"]:
            ok, perche = rifai_scatola_xrdp(self.o, self.o.cont, dove)
        else:
            ok, perche = rifai_scatola(self.o, self.o.scatola, self.o.tetto, dove)
        if ok and SISTEMA["xrdp"]:
            self.meta_scatola = meta_scatola_xrdp(self.o.cont)
            dice("   box: %s · xrdp %s · configuration %s · dri %s · VA %s" % (
                self.o.cont, self.meta_scatola["pacchetti"].get("xrdp"),
                self.meta_scatola.get("xrdp_configurazione"),
                ",".join(self.meta_scatola.get("dri_nella_scatola", [])), self.meta_scatola.get("driver_va")))
        elif ok:
            self.meta_scatola = meta_scatola(self.o.scatola)
            dice("   box: binary %s · page %s · %s · dri %s · VA %s · %s" % (
                self.meta_scatola.get("binario"), self.meta_scatola.get("pagina"),
                self.meta_scatola.get("opzioni_server") or "(default options)",
                ",".join(self.meta_scatola.get("dri_nella_scatola", [])),
                self.meta_scatola.get("driver_va"), self.meta_scatola.get("codifica_video")))
        self.nuova_cartella_attori()
        return ok, perche

    def entrano(self, n_fino, livello):
        """The missing actors up to `n_fino`, one after the other: the next one
        when the previous one has the first frame (nascita.json)."""
        c, t = compositori("accendi", str(n_fino), self.o.misura)
        if c != 0:
            dice("⛔ compositors: %s" % " | ".join(t.splitlines()[-3:]))
            return False, "the compositors do not turn on: %s" % t.strip().splitlines()[-1:]
        nuovi = [n for n in range(1, n_fino + 1) if n not in self.attori]
        for n in nuovi:
            if self.fermati:
                return False, "stopped from outside"
            if self.guardia and self.guardia.motivo:
                self.ospite = self.guardia.motivo
                return False, "host resources: %s" % self.guardia.motivo
            a = Attore(self.o, n, livello, self.cartella_attori)
            try:
                s = a.avvia()
            except Exception as e:               # noqa: BLE001
                return False, "actor %d does not start: %s" % (n, e)
            self.attori[n] = a
            dice("   + user %02d (pid %d, %s, seed %d, ports %d)" % (
                n, a.proc.pid, s, self.o.seme_base + n, self.o.porte_base + 10 * n))
            self.aggiorna(fase="entrano gli utenti", utenti_attesi=n_fino)
            fine = time.time() + self.o.attesa_nascita_s
            while time.time() < fine and a.vivo() and not a.e_nato() and not self.fermati \
                    and not (self.guardia and self.guardia.motivo):
                time.sleep(0.5)
            if a.e_nato():
                dice("     user %02d born in %.1f s" % (n, a.nato - a.partito))
            elif not a.vivo():
                dice("   ⛔ user %02d DEAD before being born (code %s): going on, "
                     "the classification will tell" % (n, a.proc.returncode))
            else:
                dice("   ⚠ user %02d has no first frame in %d s: the next one "
                     "comes in anyway" % (n, self.o.attesa_nascita_s))
        return True, ""

    def controllo_corto(self, livello, dirliv):
        browser = ("firefox", "chrome")[self.livelli_fatti % 2]
        s = socket_di(0)
        if not s:
            dice("   ⚠ the check's compositor u00 is not there")
            return None
        cmd = [sys.executable, self.o.prog_controllo, "--scatola", self.o.scatola,
               "--livello", str(livello), "--dir", dirliv, "--browser", browser,
               "--porte-base", str(self.o.porte_base), "--largo", str(self.o.largo),
               "--alto", str(self.o.alto)]
        if SISTEMA["xrdp"]:
            browser = "freerdp"
            cmd += ["--controllo", "--display", s, "--seme", str(self.o.seme_base + 99)]
            amb = ambiente_rdp(s)
        else:
            amb = ambiente_browser(s)
        dice("   short check: %s on %s" % (browser, s))
        with open(os.path.join(dirliv, "controllo-corto.log"), "w") as log:
            try:
                p = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, env=amb, cwd=QUI,
                                     start_new_session=True)
                # ⭐ not a blind wait() of 600 s: at SIGTERM (stopped from outside) the
                #   check stops at once and the climb goes to clean up
                limite = time.time() + self.o.tetto_controllo_s
                c = None
                while True:
                    try:
                        c = p.wait(timeout=1)
                        break
                    except subprocess.TimeoutExpired:
                        pass
                    if self.fermati or time.time() >= limite:
                        dice("   ⛔ short check %s: stopped" % (
                            "interrupted (stopped from outside)" if self.fermati
                            else "beyond %d s" % self.o.tetto_controllo_s))
                        ferma_gruppo(p)
                        c = None
                        break
            except Exception as e:               # noqa: BLE001
                dice("   ⛔ short check not launched: %s" % e)
                return None
        esito = None
        try:
            esito = json.load(open(os.path.join(dirliv, "controllo-corto.json"))).get("esito")
        except (OSError, ValueError):
            pass
        dice("   short check: %s (code %s)" % (esito, c))
        return esito

    def foto_prima_della_finestra(self, inizio_controllo, eventi):
        """SIGUSR1 to all the live actors, then wait for each one to have written
        its photo (a foto-* file or the «foto» event, even failed) — at most
        `tetto_foto_s`.  Returns the summary for livello.json."""
        vivi = [a for a in self.attori.values() if a.vivo()]
        t = time.time()
        self.aggiorna(fase="foto")
        dice("   SIGUSR1 to %d actors (full photo), %.0f s before the window" % (
            len(vivi), inizio_controllo - t))
        for a in vivi:
            a.segnale(signal.SIGUSR1)
        fatte = set()
        limite = t + self.o.tetto_foto_s
        while not self.fermati:
            for a in vivi:
                if a.n not in fatte and foto_scritta(a.dir_utente, t):
                    fatte.add(a.n)
            if len(fatte) == len(vivi) or time.time() >= limite:
                break
            time.sleep(1)
        mancano = sorted(a.n for a in vivi if a.n not in fatte)
        dice("   photos written: %d/%d in %.0f s%s" % (
            len(fatte), len(vivi), time.time() - t,
            (" · ⚠ missing %s" % mancano) if mancano else ""))
        if mancano:
            eventi.append({"t": ora(), "evento": "foto mancanti", "utenti": mancano})
        self.aggiorna(fase="lavoro")
        return {"t": iso(t), "t_s": round(t, 3), "attesi": sorted(a.n for a in vivi),
                "fatte": sorted(fatte), "durata_s": round(time.time() - t, 1)}

    def taglia_attori(self, dirliv, t0, t1):
        """The actors' series inside [t0, t1], in the level folder.
        ⛔ nascita.json ONLY if the user is NEW in this level (started in the
        level, or the birth written in the level): the births of the earlier rungs
        have already been judged there, and here they are not re-judged."""
        for a in self.attori.values():
            src = a.dir_utente
            dst = os.path.join(dirliv, "utente-%02d" % a.n)
            os.makedirs(dst, exist_ok=True)
            if not os.path.isdir(src):
                continue
            for nome in os.listdir(src):
                p = os.path.join(src, nome)
                if not os.path.isfile(p):
                    continue
                q = os.path.join(dst, nome)
                if nome.endswith(".jsonl"):
                    taglia_jsonl(p, q, t0, t1)
                elif nome == "nascita.json":
                    if nascita_del_livello(a.partito, os.path.getmtime(p), t0):
                        try:
                            os.link(p, q)
                        except OSError:
                            shutil.copy2(p, q)
                elif os.path.getmtime(p) >= t0 - 1:
                    try:
                        os.link(p, q)
                    except OSError:
                        shutil.copy2(p, q)

    def registro_server_xrdp(self, dirliv, segno, t0, t1):
        """xrdp: server.log = the NEW lines of xrdp.log and xrdp-sesman.log from the mark."""
        d = self.o.cont
        seg = segno or {}
        parti = []
        for nome in ("xrdp.log", "xrdp-sesman.log"):
            _c, t = nella_scatola(d, "tail -n +%d /var/log/%s 2>/dev/null" % (seg.get(nome, 0) + 1, nome), 300)
            parti.append("== /var/log/%s\n%s" % (nome, t or ""))
        open(os.path.join(dirliv, "server.log"), "w").write("\n".join(parti) + "\n")
        da, a = "@%d" % int(t0), "@%d" % int(t1 + 1)
        _c, t = nella_scatola(d, "journalctl -p err -o json --since %s --until %s --no-pager 2>/dev/null "
                                 "| tail -n 200000" % (da, a), 300)
        open(os.path.join(dirliv, "journal-err.jsonl"), "w").write(
            "\n".join(r for r in (t or "").splitlines() if r.startswith("{")) + "\n")
        _c, t = nella_scatola(d, "journalctl -u xrdp -u xrdp-sesman --since %s --until %s --no-pager "
                                 "-o short-iso-precise 2>&1 | tail -n 500000" % (da, a), 300)
        open(os.path.join(dirliv, "journal-server.log"), "w").write(t or "")
        _c, t = nella_scatola(d, "journalctl --since %s --until %s --no-pager "
                                 "-o short-iso-precise 2>&1 | tail -n 500000" % (da, a), 300)
        open(os.path.join(dirliv, "journal-scatola.log"), "w").write(t or "")
        return ["server.log", "journal-err.jsonl", "journal-server.log", "journal-scatola.log"]

    def registro_server(self, dirliv, segno, t0, t1):
        if SISTEMA["xrdp"]:
            return self.registro_server_xrdp(dirliv, segno, t0, t1)
        d = self.o.scatola
        files = []
        if segno is not None:
            # ⭐ «server.log»: the name 16-classifica.py reads
            _c, t = nella_scatola(d, "tail -n +%d /var/lib/rete11/registro.log" % (segno + 1), 300)
            open(os.path.join(dirliv, "server.log"), "w").write(t or "")
            files.append("server.log")
        da, a = "@%d" % int(t0), "@%d" % int(t1 + 1)
        # ⭐ the product's errors in the journal (--journal): the schema of 16-classifica.py
        _c, t = nella_scatola(d, "journalctl -t remotix -p err -o json --since %s --until %s "
                                 "--no-pager 2>/dev/null | tail -n 200000" % (da, a), 300)
        open(os.path.join(dirliv, "journal-err.jsonl"), "w").write(
            "\n".join(r for r in (t or "").splitlines() if r.startswith("{")) + "\n")
        files.append("journal-err.jsonl")
        _c, t = nella_scatola(d, "journalctl -u rete11-server --since %s --until %s --no-pager "
                                 "-o short-iso-precise 2>&1 | tail -n 500000" % (da, a), 300)
        open(os.path.join(dirliv, "journal-server.log"), "w").write(t or "")
        files.append("journal-server.log")
        _c, t = nella_scatola(d, "journalctl --since %s --until %s --no-pager "
                                 "-o short-iso-precise 2>&1 | tail -n 500000" % (da, a), 300)
        open(os.path.join(dirliv, "journal-scatola.log"), "w").write(t or "")
        files.append("journal-scatola.log")
        return files

    def classifica(self, dirliv, livello):
        cmd = [sys.executable, self.o.prog_classifica, "--livello-dir", dirliv,
               "--campagna", self.o.campagna, "--livello", str(livello),
               "--finestra-s", str(int(self.o.controllo_min * 60)), "--json"]
        if self.o.fps_video:
            cmd += ["--fps-video", str(self.o.fps_video)]
        if SISTEMA["xrdp"]:
            cmd += ["--sistema", "xrdp"]
        if self.o.prova:
            cmd.append("--secco")            # §13.3: the test climb does not count
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, errors="replace", timeout=900,
                               cwd=QUI)
            uscita, codice = r.stdout + r.stderr, r.returncode
        except Exception as e:                   # noqa: BLE001
            uscita, codice = "classification not launched: %s" % e, None
        open(os.path.join(dirliv, "classifica.log"), "w").write(uscita)
        return leggi_classe(uscita, codice)

    # -- ONE LEVEL -------------------------------------------------------------
    def livello(self, n, minuti, nome, tipo):
        """Brings the climb to `n` users and does the level.  Returns (class, signif, dirliv)."""
        o = self.o
        dirliv = os.path.join(self.base, nome)
        os.makedirs(dirliv, exist_ok=True)
        dice("══ %s: %d users, %s min (%s) ══" % (nome, n, minuti, tipo))
        self.aggiorna(fase="livello", gradino=n, livello_dir=dirliv, tipo_livello=tipo)
        t_inizio = time.time()
        if self.guardia:
            ancora = self.guardia.riarma()
            if ancora:
                dice("⚠ the guard still says «%s» after the wait: the level starts anyway" % ancora)
        self.ospite = None
        if SISTEMA["xrdp"]:
            _c, t = nella_scatola(o.cont, "for f in xrdp.log xrdp-sesman.log; do echo $f $(wc -l < "
                                          "/var/log/$f 2>/dev/null || echo 0); done", 60)
            segno = {}
            for r in (t or "").splitlines():
                p_ = r.split()
                if len(p_) == 2 and p_[1].isdigit():
                    segno[p_[0]] = int(p_[1])
        else:
            _c, t = nella_scatola(o.scatola, "wc -l < /var/lib/rete11/registro.log 2>/dev/null", 60)
            try:
                segno = int((t or "").split()[-1])
            except (ValueError, IndexError):
                segno = None
        # ⛔ 16-risorse.py runs as ROOT (the tenants' smaps_rollup and fdinfo):
        #   sudo -S, the password on stdin; sudo passes the SIGTERM to the child.
        cmd_r = [sys.executable, o.prog_risorse, "--scatola", o.cont, "--dir", dirliv]
        if SISTEMA["xrdp"]:
            cmd_r += ["--sistema", "xrdp", "--segni-browser", "remotix-rdp-"]
        if not o.risorse_senza_root:
            cmd_r = ["sudo", "-S", "-p", ""] + cmd_r
        risorse = subprocess.Popen(
            cmd_r, stdin=subprocess.PIPE, text=True,
            stdout=open(os.path.join(dirliv, "risorse.log"), "w"), stderr=subprocess.STDOUT,
            cwd=QUI, start_new_session=True)
        try:
            risorse.stdin.write("" if o.risorse_senza_root else _parola_sudo())
            risorse.stdin.close()
        except OSError:
            pass
        eventi = []
        entrata_ok, perche_entrata = self.entrano(n, n)
        entrati = sorted(a.n for a in self.attori.values() if a.proc is not None)
        nati = sorted(a.n for a in self.attori.values() if a.nato)
        if not entrata_ok and self.ospite:
            for a in self.attori.values():
                a.segnale(signal.SIGTERM)
        if not entrata_ok:
            # ⛔ compositor or actor that does not start: the level is NOT good
            #   (class «?», which stops the climb like an unreadable class)
            eventi.append({"t": ora(), "evento": "entrata fallita", "ragione": perche_entrata,
                           "attesi": n, "entrati": len(entrati), "nati": len(nati)})
            dice("⛔ ENTRY FAILED (%d entered of %d, %d born): %s — the level will be «?»" % (
                len(entrati), n, len(nati), perche_entrata))
        t_lavoro = time.time()
        fine = t_lavoro + minuti * 60
        inizio_controllo = fine - o.controllo_min * 60
        # ⭐ the full photo (SIGUSR1) BEFORE the judgement window: Chrome
        #   Page.captureScreenshot in 4K stops drawing, and inside the window
        #   it would dirty it.  It is sent `anticipo_foto_s` before and the window
        #   starts only when the photos are written (if they are late, window and
        #   end of the level slip together: the window stays whole and clean).
        ora_foto = inizio_controllo - o.anticipo_foto_s
        if entrata_ok:
            dice("   all inside (%.0f s after the start of the level): work until %s" % (
                t_lavoro - t_inizio, time.strftime("%H:%M:%S", time.localtime(fine))))
        self.aggiorna(fase="lavoro", fine_prevista=datetime.datetime.fromtimestamp(
            fine).astimezone().isoformat(timespec="seconds"))
        esito_controllo = None
        fatto_controllo = False
        foto = None                      # {"t": sent, "attesi": [...], "fatte": [...]}
        while not self.fermati and entrata_ok:
            if self.guardia and self.guardia.motivo:
                self.ospite = self.guardia.motivo
                eventi.append({"t": ora(), "evento": "guardia dell'ospite", "ragione": self.ospite,
                               "misura": dict(self.guardia.ultima)})
                for a in self.attori.values():
                    a.segnale(signal.SIGTERM)          # out at once: the clients free the memory
                break
            adesso = time.time()
            for a in self.attori.values():
                if not a.vivo() and not a.morto_annotato:
                    a.morto_annotato = True
                    eventi.append({"t": ora(), "evento": "attore morto", "utente": a.n,
                                   "codice": a.proc.returncode})
                    dice("   ⛔ user %02d exited (code %s)" % (a.n, a.proc.returncode))
            if foto is None and adesso >= ora_foto:
                foto = self.foto_prima_della_finestra(inizio_controllo, eventi)
                adesso = time.time()
                if adesso > inizio_controllo:
                    ritardo = adesso - inizio_controllo
                    inizio_controllo, fine = adesso, fine + ritardo
                    dice("   the window starts %.0f s later (slow photos): end at %s" % (
                        ritardo, time.strftime("%H:%M:%S", time.localtime(fine))))
                    self.aggiorna(fine_prevista=datetime.datetime.fromtimestamp(
                        fine).astimezone().isoformat(timespec="seconds"))
                continue
            if foto is not None and not fatto_controllo and adesso >= inizio_controllo:
                fatto_controllo = True
                self.aggiorna(fase="controllo")
                if not o.senza_controllo:
                    esito_controllo = self.controllo_corto(n, dirliv)
                self.aggiorna(fase="lavoro")
                continue
            if adesso >= fine and fatto_controllo:
                break
            prossimo = ora_foto if foto is None else (inizio_controllo if not fatto_controllo
                                                       else fine)
            time.sleep(min(2 if self.guardia else 5, max(0.5, prossimo - adesso)))
        t_fine = time.time()
        self.aggiorna(fase="registro")
        risorse.send_signal(signal.SIGTERM)
        try:
            risorse.wait(timeout=30)
        except subprocess.TimeoutExpired:
            sudo("pkill -KILL -f %s" % _q("[1]6-risorse.py --scatola %s --dir %s" % (
                o.cont, dirliv)), 30)
        files = self.registro_server(dirliv, segno, t_inizio, t_fine)
        schede_b = browser_fuori_scheda(dirliv)
        if schede_b and schede_b["fuori_intel"]:
            dice("   ⛔ client browser on a card that is not the Intel: %s" % schede_b["fuori_intel"])
            eventi.append({"t": ora(), "evento": "browser fuori dalla Intel",
                           "dettaglio": schede_b["fuori_intel"]})
        self.taglia_attori(dirliv, t_inizio, t_fine)
        riga = dict(self.meta, **{
            "campagna": o.campagna, "livello": n, "nome": nome, "tipo": tipo,
            "desktop": o.scatola, "misura": o.misura, "largo": o.largo, "alto": o.alto,
            "tetto_sessioni": o.tetto, "minuti": minuti, "controllo_min": o.controllo_min,
            "inizio": iso(t_inizio), "inizio_t": round(t_inizio, 3),
            "inizio_lavoro": iso(t_lavoro), "fine": round(t_fine, 3), "fine_iso": iso(t_fine),
            "durata_s": round(t_fine - t_inizio), "durata_lavoro_s": round(t_fine - t_lavoro),
            "utenti": [{"utente": a.n, "profilo": "ABCD"[(a.n - 1) % 4],
                        "browser": "freerdp" if SISTEMA["xrdp"] else ("firefox" if a.n % 2 else "chrome"),
                        "nuovo": bool(a.nato and a.nato >= t_inizio) or a.partito >= t_inizio}
                       for _k, a in sorted(self.attori.items())],
            "vivi_alla_fine": sorted(
                a.n for a in self.attori.values() if a.vivo()),
            "nati_nel_livello": sorted(a.n for a in self.attori.values()
                                       if a.nato and a.nato >= t_inizio),
            "nascite_s": {"%02d" % a.n: round(a.nato - a.partito, 1) for a in
                          self.attori.values() if a.nato and a.nato >= t_inizio},
            "seme_base": o.seme_base, "video": o.video, "fps_video": o.fps_video,
            "controllo_corto": esito_controllo, "registro_server": files,
            "entrata_ok": entrata_ok, "entrata_ragione": perche_entrata or None,
            "attesi": n, "entrati": entrati, "nati_alla_partenza": nati,
            "foto_piena": foto, "inizio_finestra": iso(inizio_controllo),
            "inizio_finestra_t": round(inizio_controllo, 3),
            "schede_browser": schede_b,
            "eventi": eventi, "attori_da": self.cartella_attori, "prova": o.prova,
            "sistema": o.sistema, "ospite_esaurito": self.ospite,
            "guardia": dict(self.guardia.ultima) if self.guardia else None})
        ms = getattr(self, "meta_scatola", {})
        riga.update({"scatola_" + k: v for k, v in ms.items()})
        # ⭐ the fields of §10 with the names 16-classifica.py reads (BASE)
        # ⭐ the SERVER's card (the one in the box, --scheda), not always the
        #   Intel: in the AMD campaign it is the RX 6800.  The client browsers stay
        #   on the Intel and `scheda_browser` says so.
        srv = [s for s in self.meta.get("schede", []) if s["driver"] in DRIVER_SCHEDA[o.scheda]]
        intel = [s for s in self.meta.get("schede", []) if s["driver"] in DRIVER_SCHEDA["intel"]]
        riga.update(scheda=(srv or [{}])[0].get("scheda", "?"),
                    scheda_quale=o.scheda, scheda_pci=(srv or [{}])[0].get("pci"),
                    scheda_browser=(intel or [{}])[0].get("scheda", "?"),
                    driver=" ".join([(srv or [{}])[0].get("driver", "?")]
                                    + ms.get("driver_video", [])),
                    commit=self.meta.get("commit_prodotto") or
                    "benches %s" % self.meta.get("commit_banchi"), binario=ms.get("binario"),
                    pagina=ms.get("pagina"), nucleo=self.meta.get("kernel"))
        if SISTEMA["xrdp"]:
            pk = ms.get("pacchetti") or {}
            riga.update(commit="xrdp %s · xorgxrdp %s · freerdp %s" % (
                pk.get("xrdp"), pk.get("xorgxrdp"), (ms.get("pacchetti_ospite") or {}).get("freerdp3-x11")),
                tetto_sessioni=None, scheda_browser="none (FreeRDP decodes on the processor)")
        scrivi_json(os.path.join(dirliv, "livello.json"), riga)
        if self.fermati:
            # ⛔ a level interrupted from outside is not classified: it did not last
            riga["interrotto"] = True
            scrivi_json(os.path.join(dirliv, "livello.json"), riga)
            classe, signif, perche_c = "INTERROTTO", False, "stopped from outside (signal)"
        else:
            self.aggiorna(fase="classifico")
            classe, signif, perche_c = self.classifica(dirliv, n)
            if not entrata_ok:
                # ⛔ what the classification says stays in its log, but the
                #   level is not the one asked for: it is not good
                perche_c = "ENTRY FAILED (%d entered of %d): %s · the classification said %s" % (
                    len(entrati), n, perche_entrata, classe)
                classe, signif = "?", False
        if self.ospite and not self.fermati:
            # ⛔ §7.7: the level closed by the guard is a declared BREAK
            perche_c = "⛔ HOST RESOURCES (§7.7): %s · the classification said %s — %s" % (
                self.ospite, classe, perche_c[:200])
            classe, signif = "FAIL", True
        self.livelli_fatti += 1
        riga.update(classe=classe, significativo=signif, ragione_classe=perche_c)
        with open(os.path.join(self.base, "salita.jsonl"), "a", encoding="utf-8") as f:
            fcntl.flock(f, fcntl.LOCK_EX)
            f.write(json.dumps(riga, ensure_ascii=False) + "\n")
        self.storia.append({"livello": n, "nome": nome, "tipo": tipo, "classe": classe,
                            "significativo": signif, "dir": dirliv})
        self.aggiorna(classe_ultimo=classe)
        dice("   ▶ %s: %s%s — %s" % (nome, classe, " (significant)" if signif else "",
                                     perche_c[:200]))
        return classe, signif, dirliv

    # -- THE WHOLE CLIMB -------------------------------------------------------
    def corri(self):
        o = self.o
        self.meta = meta_macchina(o)
        dice("⭐ CLIMB %s · %s · %s (%dx%d) · rungs %s · %s min (last %s) · cap %d%s" % (
            o.campagna, o.scatola, o.misura, o.largo, o.alto, ",".join(map(str, o.gradini)),
            o.minuti, o.minuti_ultimo, o.tetto, " · TEST (does not count)" if o.prova else ""))
        dice("   card of the box: %s · %s" % (o.scheda, "SYSTEM xrdp, FreeRDP clients on the processor"
                                              if SISTEMA["xrdp"] else "client browsers on the Intel"))
        if SISTEMA["xrdp"]:
            proteggi_ssh()
        dice("   product commit: %s" % (self.meta["commit_prodotto"] or
                                       "? (16-prodotto absent or different binary)"))
        dice("   kernel %s · %s · binary %s · page %s · benches %s" % (
            self.meta["kernel"], " + ".join("%s [%s]" % (s["scheda"], s["driver"])
                                            for s in self.meta["schede"]),
            self.meta["prodotto_binario"], self.meta["prodotto_pagina"],
            self.meta["commit_banchi"]))
        ok, perche = self.scatola_pulita(self.base)
        if not ok:
            return self.blocca(perche)
        ultimo_buono, rotto = 0, None
        for i, n in enumerate(o.gradini):
            if self.fermati:
                break
            minuti = o.minuti_ultimo if i == len(o.gradini) - 1 else o.minuti
            classe, signif, _d = self.livello(n, minuti, "livello-%02d" % n, "gradino")
            if self.fermati:
                break
            if cattivo(classe, signif) and self.ospite:
                rotto = n
                dice("⛔ %d users: closed by the host guard (%s) — break, without repeating "
                     "(§7.7)" % (n, self.ospite))
                break
            if cattivo(classe, signif):
                dice("⚠ %d users: %s — REPEATED under the same conditions (§14), from a clean "
                     "box" % (n, classe))
                ok, perche = self.scatola_pulita(os.path.join(self.base, "livello-%02d" % n))
                if not ok:
                    return self.blocca(perche)
                classe2, signif2, _d = self.livello(n, minuti, "livello-%02d-ripetizione" % n,
                                                    "ripetizione")
                if self.fermati:
                    break
                if cattivo(classe2, signif2):
                    rotto = n
                    dice("⛔ confirmed: %d users %s twice" % (n, classe2))
                    break
                dice("   the repetition says %s: not confirmed, climbing" % classe2)
            ultimo_buono = n
        if rotto is not None and not self.fermati:
            ultimo_buono, rotto = self.ricerca(ultimo_buono, rotto)
        self.aggiorna(fase="fine", ultimo_buono=ultimo_buono, rottura=rotto)
        dice("⏹ END: last good level %s · break %s%s" % (
            ultimo_buono, rotto, " · ⚠ STOPPED FROM OUTSIDE" if self.fermati else ""))
        if self.fermati:
            return 3
        return 0 if rotto is None else 1

    def ricerca(self, buono, rotto):
        """The bisection (§6): every level from a clean box with its N users."""
        while rotto - buono > 1 and not self.fermati:
            n = (buono + rotto) // 2
            dice("🔎 bisection between %d (good) and %d (broken): %d users" % (buono, rotto, n))
            self.aggiorna(fase="ricerca", ricerca=[buono, rotto])
            ok, perche = self.scatola_pulita(os.path.join(self.base, "livello-%02d" % n))
            if not ok:
                self.blocca(perche)
                break
            classe, signif, _d = self.livello(n, self.o.minuti, "livello-%02d" % n, "ricerca")
            if self.fermati:
                break
            if cattivo(classe, signif):
                rotto = n
            else:
                buono = n
        return buono, rotto

    def blocca(self, perche):
        dice("⛔ BLOCKED: %s" % perche)
        self.aggiorna(fase="BLOCKED", ragione=perche)
        return 3

    def sgombera_tutto(self):
        o = self.o
        self.aggiorna(fase="sgombero")
        self.ferma_attori()
        try:
            sgombera_16(o.cont)
        except Exception as e:                   # noqa: BLE001
            dice("⚠ clean-up: %s" % e)
        c, t = compositori("spegni")
        dice("   compositors off (%d)" % t.count("switched off"))
        if self.guardia:
            self.guardia.vivo = False
        if SISTEMA["xrdp"]:
            # the xrdp box is turned off: it frees 3389 and the memory for whoever comes next
            c, t = sudo("podman rm -f -t 10 rete11-%s" % o.cont, 120)
            dice("   box rete11-%s off (code %s)" % (o.cont, c))
            return
        if not o.lascia_tetto and o.tetto and not o.non_rifare:
            c, t = sudo("cd %s && bash 11-accendi.sh server %s" % (RETE11, o.scatola), 300)
            dice("   server put back with the default cap (code %s, cap %s)" % (
                c, tetto_in_vigore(o.scatola)))


def iso(t):
    return datetime.datetime.fromtimestamp(t).astimezone().isoformat(timespec="seconds")


def cattivo(classe, signif):
    """§6: FAIL or significant DEGRADED stop the climb.  A class that could not
    be read stops it too: no blind climbing."""
    return classe not in ("GREEN", "DEGRADED") or (classe == "DEGRADED" and signif)


def leggi_classe(uscita, codice):
    """(class, significant, reason) from the output of 16-classifica.py: the LAST
    JSON line with «classe» (and «significativo»), or the last word GREEN /
    DEGRADED / FAIL; otherwise «?» (and the climb stops)."""
    righe = []
    for riga in uscita.splitlines():
        riga = riga.strip()
        i = riga.find("{")
        if i < 0:
            continue
        try:
            d = json.loads(riga[i:])
        except ValueError:
            continue
        if isinstance(d, dict) and str(d.get("classe") or "").upper() in CLASSI:
            righe.append(d)
    # ⭐ the `"tipo": "livello"` line (16-classifica.py --json), otherwise the last one
    for d in [r for r in righe if r.get("tipo") == "livello"][-1:] or righe[-1:]:
        return (str(d["classe"]).upper(), bool(d.get("significativo")),
                str(d.get("ragione") or "")[:400])
    parole = re.findall(r"\b(GREEN|DEGRADED|FAIL)\b", uscita)
    if parole:
        c = parole[-1]
        # ⚠ both forms: the old (Italian) 16-classifica.py and the new (English) one
        return c, bool(re.search(r"(?<!non )(?<!not )(?:significativo|significant)", uscita, re.I)) \
            and c == "DEGRADED", \
            "(read from the word, code %s)" % codice
    if codice in (0, 1, 3):                     # 16-classifica.py: GREEN 0, FAIL 1, DEGRADED 3
        return {0: "GREEN", 1: "FAIL", 3: "DEGRADED"}[codice], codice == 3, \
            "(from the exit code %s: DEGRADED counted as significant)" % codice
    return "?", False, "16-classifica did not say a class (code %s): %s" % (
        codice, " | ".join(uscita.strip().splitlines()[-3:])[:300])


def nascita_del_livello(partito, mtime_nascita, t0):
    """⭐ The nascita.json belongs to the level that starts at `t0` if the actor
    started in the level, or if the birth was written in the level."""
    return (partito is not None and partito >= t0) or mtime_nascita >= t0 - 1


def foto_scritta(dir_utente, dopo):
    """Is the photo asked for at `dopo` there?  A new foto-* file, or the «foto» event
    (even failed: the actor has finished trying) in eventi.jsonl."""
    try:
        for nome in os.listdir(dir_utente):
            if nome.startswith("foto-") and os.path.getmtime(os.path.join(dir_utente, nome)) >= dopo:
                return True
    except OSError:
        return False
    try:
        with open(os.path.join(dir_utente, "eventi.jsonl"), encoding="utf-8",
                  errors="replace") as f:
            for riga in f:
                if '"foto"' not in riga:
                    continue
                try:
                    d = json.loads(riga)
                except ValueError:
                    continue
                if d.get("evento") == "foto" and (d.get("t") or 0) >= dopo:
                    return True
    except OSError:
        pass
    return False


def ferma_gruppo(p, grazia=20):
    """SIGTERM to the group of `p` (the check cleans up its session), then
    SIGKILL if it does not exit in `grazia` s."""
    try:
        os.killpg(p.pid, signal.SIGTERM)
    except OSError:
        pass
    try:
        p.wait(timeout=grazia)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(p.pid, signal.SIGKILL)
        except OSError:
            pass
        p.wait()


def taglia_jsonl(src, dst, t0, t1):
    """The rows of `src` with the instant inside [t0, t1]; the rows without a readable
    instant all pass."""
    chiavi = ("t", "ts", "tempo", "epoch", "quando", "ora", "istante", "orario")
    with open(src, encoding="utf-8", errors="replace") as f, \
            open(dst, "w", encoding="utf-8") as g:
        for riga in f:
            try:
                d = json.loads(riga)
            except ValueError:
                continue
            t = None
            for k in chiavi:
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
                g.write(riga)


# ═══════════════════════════════════════════════════════════════════════════

# ⛔ THE BOXES BELONG TO ONE BENCH AT A TIME (29 Sep 2026, «user unknown» of phase 16):
#   the hook (even the pre-push one, by itself) clears ALL the tenants
#   `c<n>u<n>` before every mesh ⇒ a push during a round deleted the tenants
#   born 7 s earlier (`[M]` 04:28, 04:40, 04:42 of 29 Sep = the 4 FAIL and 36 BLOCKED).
#   The same lock in 15-giro.py, 16-salita.py and 11-gancio.sh; whoever is launched by
#   one of them inherits REMOTIX_SCATOLE_TENUTE and does not take it again.
#   ⚠ NOT in /run/lock: the folder is «sticky» and with fs.protected_regular root does not
#   reopen the file created by nicfio (and the hook says «held» about free boxes, `[M]`).
SERRATURA_SCATOLE = "/media/REMOTIX/rete11/.scatole.lock"


def tieni_le_scatole(chi):
    """None if the boxes are ours (the lock stays taken until exit),
    otherwise the sentence that says who holds them."""
    if os.environ.get("REMOTIX_SCATOLE_TENUTE"):
        return None
    fd = os.open(SERRATURA_SCATOLE, os.O_RDWR | os.O_CREAT, 0o666)
    try:
        os.fchmod(fd, 0o666)
    except OSError:
        pass
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        try:
            tiene = os.pread(fd, 200, 0).decode(errors="replace").strip()
        except OSError:
            tiene = ""
        os.close(fd)
        return "the boxes are already held by another bench (%s)" % (tiene or "?")
    os.ftruncate(fd, 0)
    os.pwrite(fd, ("%s pid %d" % (chi, os.getpid())).encode(), 0)
    os.environ["REMOTIX_SCATOLE_TENUTE"] = chi
    globals()["_fd_scatole"] = fd
    return None


def main():
    global _log_file
    a = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument("--scatola", required=True, choices=sorted(PORTE))
    a.add_argument("--campagna", required=True)
    a.add_argument("--misura", default="4k", choices=sorted(MISURE_SCHERMO))
    a.add_argument("--gradini", default="1,4,8,12,16")
    a.add_argument("--minuti", type=float, default=10)
    a.add_argument("--minuti-ultimo", type=float, default=30)
    a.add_argument("--controllo-min", type=float, default=2)
    a.add_argument("--seme-base", type=int, default=1600)
    a.add_argument("--fps-video", type=float, default=0)
    a.add_argument("--video", default="")
    a.add_argument("--tetto", type=int, default=0,
                   help="the server's session cap (default: highest rung + 1, "
                        "for the short check)")
    a.add_argument("--porte-base", type=int, default=9900)
    a.add_argument("--scheda", default="intel", choices=sorted(DRIVER_SCHEDA),
                   help="the card of the BOX (REMOTIX_SCHEDA of 11-accendi.sh); the "
                        "client browsers stay on the Intel")
    a.add_argument("--prova", action="store_true",
                   help="test climb §13.3: rungs 1,2,4 of 5 minutes; does not count")
    a.add_argument("--senza-scheda", action="store_true",
                   help="phase 18: encoding WITHOUT a card (OpenH264) — in the rebuilt box "
                        "iHD_drv_video.so is hidden before turning on the server, and we "
                        "require the log to say «H.264: scheda no, software OpenH264 si'»")
    a.add_argument("--mesa-vulkan-deb", default="",
                   help="phase 20: a mesa-vulkan-drivers_*.deb to install in the box "
                        "before the server (the backport for the Radeon, defect A3)")
    a.add_argument("--sistema", choices=("remotix", "xrdp"), default="remotix",
                   help="xrdp: the same climb against Debian 13's xrdp (fasi/20 §7)")
    a.add_argument("--guardia", action="store_true",
                   help="the host guard of fasi/20 §7.7 (always on with --sistema xrdp)")
    a.add_argument("--secco", action="store_true", help="prints the plan and that's all")
    a.add_argument("--attesa-nascita-s", type=int, default=180)
    a.add_argument("--attesa-uscita-s", type=int, default=120)
    a.add_argument("--tetto-controllo-s", type=int, default=600)
    a.add_argument("--anticipo-foto-s", type=int, default=30,
                   help="the full photo (SIGUSR1) how many s BEFORE the judgement window")
    a.add_argument("--tetto-foto-s", type=int, default=90,
                   help="how long the photos are waited for before the window")
    a.add_argument("--lascia-tetto", action="store_true")
    # ⚠ only to test the setup, never in a campaign:
    a.add_argument("--anche-se-non-vuoto", action="store_true")
    a.add_argument("--non-rifare", action="store_true")
    a.add_argument("--senza-controllo", action="store_true")
    a.add_argument("--risorse-senza-root", action="store_true",
                   help="16-risorse.py as nicfio (the fakes): without root, PSS and fdinfo are not read")
    a.add_argument("--programmi", default=QUI,
                   help="the folder of 16-attore/16-risorse/16-classifica (the fakes: finti/)")
    o = a.parse_args()
    if o.prova:
        if "--gradini" not in sys.argv:
            o.gradini = "1,2,4"
        # ⛔ [M] 6 Oct (phase 20 tuning): 3 min = 1 of settling + 2 of short
        #    check ⇒ the memory stretch is EMPTY, «NOT MEASURED» ⇒ DEGRADED at the first
        #    rung.  And at 4 min the series has 60 points in 59 s: 16-classifica wants
        #    more than 60 s ⇒ still NOT MEASURED.  5 min leave 2 min of memory.
        if "--minuti" not in sys.argv:
            o.minuti = 5
        if "--minuti-ultimo" not in sys.argv:
            o.minuti_ultimo = 5
        if not o.campagna.startswith("prova-"):
            o.campagna = "prova-" + o.campagna
    o.gradini = [int(x) for x in str(o.gradini).split(",") if x.strip()]
    if o.gradini != sorted(set(o.gradini)) or not o.gradini or o.gradini[0] < 1:
        a.error("--gradini: increasing numbers from 1 upwards")
    if o.controllo_min > min(o.minuti, o.minuti_ultimo):
        a.error("--controllo-min longer than the level")
    # the memory stretch (16-classifica): after 60 s of settling, before the check
    if min(o.minuti, o.minuti_ultimo) * 60 - o.controllo_min * 60 - 60 < 90:
        a.error("levels too short: at least --controllo-min + 2.5 minutes are needed "
                "(1 of settling, and the memory wants more than 60 s of series)")
    o.tetto = o.tetto or (max(o.gradini) + 1)
    SISTEMA["xrdp"] = o.sistema == "xrdp"
    o.cont = o.scatola + "-xrdp" if SISTEMA["xrdp"] else o.scatola
    o.guardia = o.guardia or SISTEMA["xrdp"]
    o.largo, o.alto = MISURE_SCHERMO[o.misura]
    prog = os.path.abspath(o.programmi)
    o.prog_attore = os.path.join(prog, "16-attore.py")
    o.prog_risorse = os.path.join(prog, "16-risorse.py")
    o.prog_classifica = os.path.join(prog, "16-classifica.py")
    o.prog_controllo = os.path.join(QUI, "16-controllo-corto.py")
    if SISTEMA["xrdp"]:
        o.prog_attore = os.path.join(prog, "16-attore-rdp.py")
        o.prog_controllo = os.path.join(QUI, "16-attore-rdp.py")
    if o.secco:
        tot = sum(o.minuti for _ in o.gradini[:-1]) + o.minuti_ultimo
        print("plan: %s · card %s · %s · rungs %s · %s min + last %s ≈ %.0f min of work (+ births, "
              "checks, log) · cap %d · ports %d-%d · programs %s" % (
                  o.campagna, o.scheda, o.scatola, o.gradini, o.minuti, o.minuti_ultimo, tot, o.tetto,
                  o.porte_base, o.porte_base + 10 * max(o.gradini) + 9, prog))
        for p in (o.prog_attore, o.prog_risorse, o.prog_classifica, o.prog_controllo):
            print("  %s %s" % ("✓" if os.path.exists(p) else "✗ MISSING", p))
        return 0
    for p in (o.prog_attore, o.prog_risorse, o.prog_classifica, o.prog_controllo):
        if not os.path.exists(p):
            print("⛔ %s is missing" % p)
            return 3
    base = os.path.join(MISURE, o.campagna)
    if glob.glob(os.path.join(base, "livello-*")):
        print("⛔ the campaign %s already has levels in %s: the evidence is not touched (§14). "
              "Another name." % (o.campagna, base))
        return 3
    os.makedirs(base, exist_ok=True)
    _log_file = open(os.path.join(base, "salita.log"), "a", encoding="utf-8")
    # ⛔ ONE climb at a time on the server
    serratura = open(os.path.join(RUN, "16-salita.lock"), "w")
    try:
        fcntl.flock(serratura, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        dice("⛔ BLOCKED: there is already another climb in progress on this server")
        return 3
    guaio = tieni_le_scatole("16-salita %s" % o.campagna)
    if guaio:
        dice("⛔ BLOCKED: %s" % guaio)
        return 3
    sal = Salita(o)
    guai = perche_non_vuoto(o.cont)
    # ⚠ [M] 26 Sep, 00:01: the previous climb had just cleaned up and the tenant's
    #   session was still closing (logind) 6 s later ⇒ false BLOCKED.  Whoever
    #   is closing is waited for up to 120 s; whoever is left after that is a non-empty server.
    for _ in range(12):
        if not guai:
            break
        time.sleep(10)
        guai = perche_non_vuoto(o.cont)
    if guai:
        sal.stato["server_non_vuoto"] = guai
        if not o.anche_se_non_vuoto:
            return sal.blocca("the server is not empty: " + " · ".join(guai))
        dice("⚠ the server is NOT empty (--anche-se-non-vuoto, test of the setup): " +
             " · ".join(guai))

    def fermati(sig, _f):
        dice("⚠ signal %d: stopping and cleaning up" % sig)
        sal.fermati = True
    signal.signal(signal.SIGTERM, fermati)
    signal.signal(signal.SIGINT, fermati)
    codice = 3
    try:
        codice = sal.corri()
    except Exception as e:                       # noqa: BLE001
        import traceback
        dice("⛔ the climb crashed: %r\n%s" % (e, traceback.format_exc()))
        sal.aggiorna(fase="caduta", ragione=repr(e))
    finally:
        sal.sgombera_tutto()
        if sal.stato.get("fase") not in ("BLOCKED", "caduta"):
            sal.aggiorna(fase="finita" if not sal.fermati else "fermata")
        dice("end · %s" % json.dumps(sal.storia, ensure_ascii=False))
    return codice


if __name__ == "__main__":
    sys.exit(main())
