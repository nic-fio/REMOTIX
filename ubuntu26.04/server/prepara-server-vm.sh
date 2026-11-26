#!/bin/bash
# prepara-server-vm.sh - put back on the dev server (Debian 13, rootfs in RAM, emptied at every reboot) what the Ubuntu 26.04 test VMs (vm-radeon.sh in this
# folder) and the browser tests (prove/) need.  No podman, no containers.  Run as the normal user; root steps go through `echo | sudo -S`.
# What it does, one OK/FAIL line per step (idempotent, nothing is ever removed; a failed step never blocks the others):
#   work folders under /media/REMOTIX-UBUNTU; apt packages (QEMU/KVM, OVMF, disk tools, xorriso/genisoimage/openssl for the autoinstall, the test browsers
#   chromium + firefox-esr, labwc, python3-pil, libavcodec, PipeWire); /etc/modprobe.d/remotix-vfio.conf; modules loop, squashfs, vfio-pci; ACL on /dev/kvm;
#   /run/user/<uid>; a PipeWire-pulse sound server with a null sink; inotify limits; and the server side of the Radeon protection: kernel log on disk
#   (line by line), vfio-pci with disable_idle_d3=1, power/control=on for the card and its PCI bridges.
set -uo pipefail
export LC_ALL=C DEBIAN_FRONTEND=noninteractive
BASE=/media/REMOTIX-UBUNTU
ME=$(id -un); MYUID=$(id -u)
FAILS=0
ok() { echo "OK   $*"; }
ko() { echo "FAIL $*"; FAILS=$((FAILS+1)); }
step() { local d=$1 t; shift; t=$(mktemp); if "$@" >"$t" 2>&1; then ok "$d"; else ko "$d"; sed 's/^/     /' "$t" | tail -5; fi; rm -f "$t"; }
# stepv: like step, but the lines the step printed are shown also when it succeeds (the values read back)
stepv() { local d=$1 t; shift; t=$(mktemp); if "$@" >"$t" 2>&1; then ok "$d"; else ko "$d"; fi; sed 's/^/     /' "$t" | tail -20; rm -f "$t"; }
S() { echo | sudo -S -p "" "$@"; }
[ "$MYUID" -ne 0 ] || { echo "run as the normal user, not root"; exit 1; }

# 1. hostname in /etc/hosts (silences sudo "unable to resolve host")
fix_hosts() {
    local hn; hn=$(hostname)
    grep -Eq "(^|[[:space:]])${hn}([[:space:]]|\$)" /etc/hosts && return 0
    S bash -c '[ -z "$(tail -c1 /etc/hosts)" ] || echo >> /etc/hosts; printf "127.0.1.1\t%s\n" "$1" >> /etc/hosts' _ "$hn"
}
step "hostname in /etc/hosts" fix_hosts

# 2. work folders on the persistent disk (mkdir -p only)
mk_dirs() {
    S mkdir -p "$BASE"/{vm-radeon,tmp,log/server}
    S chown "$ME:$ME" "$BASE" "$BASE"/{vm-radeon,tmp,log,log/server}
}
step "folders under $BASE" mk_dirs

# 3. packages for the VMs: QEMU/KVM + qcow2 tools, UEFI firmware, partitioning/filesystems/copy tools for building the disk from the ISO's squashfs,
#    xorriso (kernel/initrd out of the ISO) + genisoimage (cloud-init seed) + openssl (password hash) for the Ubuntu autoinstall
VM_PKGS=(qemu-system-x86 qemu-utils ovmf gdisk dosfstools e2fsprogs rsync perl openssh-client util-linux acl xorriso genisoimage openssl)
inst_vm_pkgs() {
    local missing=() p
    for p in "${VM_PKGS[@]}"; do dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p"); done
    [ ${#missing[@]} -eq 0 ] && return 0
    S apt-get update -qq
    S apt-get install -y -qq --no-install-recommends "${missing[@]}"
}
step "apt packages: ${VM_PKGS[*]}" inst_vm_pkgs

# 4. kernel modules: the ISO's root image is squashfs, mounted through a loop device
step "modprobe loop squashfs" S modprobe -a loop squashfs
# the vfio-pci option goes into modprobe.d BEFORE the first modprobe of vfio-pci, so that a load made by anyone (also vm-radeon.sh) gets disable_idle_d3=1.
# VFIO_CONF_NEW=1 when this run created the file: a module loaded earlier cannot have read it (see step 9c, which also reloads when the parameter does not read Y).
VFIO_CONF=/etc/modprobe.d/remotix-vfio.conf VFIO_CONF_NEW=
vfio_conf() {
    if [ -f "$VFIO_CONF" ] && grep -qx 'options vfio-pci disable_idle_d3=1' "$VFIO_CONF"; then echo "$VFIO_CONF already there"; return 0; fi
    S sh -c 'echo "options vfio-pci disable_idle_d3=1" > "$1"' _ "$VFIO_CONF" && VFIO_CONF_NEW=1
    grep -qx 'options vfio-pci disable_idle_d3=1' "$VFIO_CONF"
}
step "$VFIO_CONF (options vfio-pci disable_idle_d3=1)" vfio_conf
step "modprobe vfio-pci" S modprobe vfio-pci

# 5. /dev/kvm usable by this user (ACL lasts until reboot)
kvm_acl() { [ -w /dev/kvm ] || S setfacl -m "u:$ME:rw" /dev/kvm; }
step "/dev/kvm usable by $ME" kvm_acl

# 6. packages for prove/ (taken from the Fedora script; NO podman): the real browsers (Chromium = the Chrome
#    engine, Firefox ESR), a headless Wayland compositor to run them in (labwc + wlr-randr), python3 + PIL to drive them and judge the pictures,
#    libavcodec for H.264 in Firefox, and a sound server (Firefox starts no AudioContext without a PulseAudio-compatible one)
HOME_DIR=$(getent passwd "$ME" | cut -d: -f6)
RT=/run/user/$MYUID
BROWSER_PKGS=(chromium firefox-esr labwc wlr-randr python3 python3-pil libavcodec61 fonts-dejavu-core pipewire pipewire-pulse wireplumber pulseaudio-utils openssh-client)
inst_browser_pkgs() {
    local missing=() p
    for p in "${BROWSER_PKGS[@]}"; do dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p"); done
    [ ${#missing[@]} -eq 0 ] && return 0
    S apt-get update -qq
    S apt-get install -y -qq --no-install-recommends "${missing[@]}"
}
step "apt packages for prove/: ${BROWSER_PKGS[*]}" inst_browser_pkgs

# 7. runtime dir (no systemd user session here) and the sound server for the test browsers: PipeWire + pipewire-pulse + WirePlumber for this
#    user, started by hand, with one null sink; the socket is $RT/pulse/native, which prove/lib.py gives to Firefox.  Idempotent.
mk_rt() { S install -d -m 700 -o "$ME" -g "$ME" "$RT"; }
step "$RT (mode 700)" mk_rt
sound_up() {
    local c="$HOME_DIR/.config/pipewire/pipewire-pulse.conf.d" i
    mkdir -p "$c"
    printf '%s\n' 'pulse.cmd = [ { cmd = "load-module" args = "module-null-sink sink_name=rx_null" flags = [ ] } ]' > "$c/null-sink.conf"
    if ! env XDG_RUNTIME_DIR="$RT" PULSE_SERVER="unix:$RT/pulse/native" pactl info 2>/dev/null | grep -q 'Default Sink: rx_null'; then
        [ -f "$RT/rx-sound.pids" ] && kill $(cat "$RT/rx-sound.pids") 2>/dev/null; : > "$RT/rx-sound.pids"
        sleep 1
        for daemon in pipewire pipewire-pulse wireplumber; do
            XDG_RUNTIME_DIR="$RT" setsid nohup "$daemon" </dev/null >"/tmp/rx-$daemon.log" 2>&1 &
            echo $! >> "$RT/rx-sound.pids"
            sleep 1
        done
    fi
    for i in 1 2 3 4 5 6 7 8 9 10; do
        env XDG_RUNTIME_DIR="$RT" PULSE_SERVER="unix:$RT/pulse/native" pactl info 2>/dev/null | grep -q 'Default Sink: rx_null' && return 0
        sleep 1
    done
    tail -3 /tmp/rx-pipewire-pulse.log /tmp/rx-wireplumber.log 2>&1
    return 1
}
step "sound server (PipeWire-pulse, null sink) on $RT/pulse/native" sound_up

# 8. inotify limits (several compositors and browsers of one uid)
step "inotify limits" S sysctl -q -w fs.inotify.max_user_instances=8192 fs.inotify.max_user_watches=1048576

# 9. server-side protection of the Radeon (the VM script has its own, in the guest).  Every step is tolerant: a failure is a FAIL line, the others still run.
GPU=0000:03:00.0 GPUA=0000:03:00.1
# 9a. kernel log on disk, LINE BY LINE (a freeze loses the in-RAM log, and in a total freeze the last lines are the ones that matter): dmesg -wT through
#     stdbuf -oL into a tiny python3 writer that appends every line with O_APPEND|O_DSYNC (written through to the disk at once; dd was tried and holds
#     the data back in 512-byte blocks).  The launcher script rx-dmesg-logger.sh is written into the log folder (it is this script's own file, rewritten
#     only if its text changed); one log file per start; pid file + launcher name in the command line = no duplicates; setsid = survives the end of ssh.
#     Loggers of the earlier versions (bare "dmesg -wT"; dmesg into dd) are stopped, with their process group, and replaced.
dmesg_log() {
    local pf="$BASE/log/server/dmesg.pid" lg="$BASE/log/server/rx-dmesg-logger.sh" p f t want
    mkdir -p "$BASE/log/server" || return 1
    want=$(cat <<'L'
#!/bin/bash
# rx-dmesg-logger.sh <logfile>: kernel log of the server, line by line, to disk (started by prepara-server-vm.sh, as root)
stdbuf -oL dmesg -wT | python3 -c 'import os,sys
fd=os.open(sys.argv[1],os.O_WRONLY|os.O_APPEND|os.O_CREAT|os.O_DSYNC,0o644)
for l in sys.stdin.buffer: os.write(fd,l)' "$1"
L
)
    [ "$(cat "$lg" 2>/dev/null)" = "$want" ] || printf '%s\n' "$want" > "$lg" || return 1
    p=$(cat "$pf" 2>/dev/null || true)
    if [[ $p =~ ^[0-9]+$ ]] && [ -r /proc/$p/cmdline ]; then
        if tr '\0' ' ' < /proc/$p/cmdline | grep -q 'rx-dmesg-logger.sh'; then echo "logger already running (pid $p)"
        elif tr '\0' ' ' < /proc/$p/cmdline | grep -qE '^dmesg -wT|rx-dmesg-logger'; then echo "replacing an older logger (pid $p, its whole process group)"; S kill -- "-$p"; p=; sleep 1
        else p=; fi
    else p=; fi
    if [ -z "$p" ]; then
        f="$BASE/log/server/dmesg-$(date +%Y%m%d-%H%M%S).log"
        S bash -c 'setsid nohup bash "$1" "$2" >/dev/null 2>&1 < /dev/null & echo $! > "$3"' _ "$lg" "$f" "$pf"
        sleep 1; p=$(cat "$pf"); [ -r /proc/$p/cmdline ] || { echo "logger did not start"; return 1; }
        echo "logger started (pid $p), file $f"
    fi
    # proof that lines arrive on disk at once: a line of ours through /dev/kmsg must be in the newest log file within 5 s
    t="remotix prepara-server-vm logger check $(date +%s%N)"
    S sh -c 'echo "$1" > /dev/kmsg' _ "$t"
    f=$(ls -t "$BASE"/log/server/dmesg-*.log | head -1)
    for p in $(seq 30); do grep -q "$t" "$f" && { echo "check line found in $f after $p s"; return 0; }; sleep 1; done
    echo "check line NOT found in $f"; return 1
}
stepv "kernel log on disk, line by line: $BASE/log/server/dmesg-*.log" dmesg_log
# 9c. vfio-pci with disable_idle_d3=1.  The value is read when the module loads (modprobe.d, step 4) and when a device is bound.  A module loaded BEFORE the
#     option file existed is unloaded and loaded again, only if nothing uses it: no qemu has the card, module use count 0 (modprobe -r refuses otherwise).
#     Devices that were on vfio-pci are put back on it.  Not possible = FAIL.
vfio_d3() {
    local f=/sys/module/vfio_pci/parameters/disable_idle_d3 d keep=() u reload=
    # reload when the option file is new, or when the parameter does not read Y (only if nobody uses the card, below)
    if [ -d /sys/module/vfio_pci ] && { [ -n "$VFIO_CONF_NEW" ] || [ "$(cat "$f" 2>/dev/null)" != Y ]; }; then
        reload=1
        u=$(ps -eo args= | grep -E "qemu-system.*host=$GPU" | grep -v grep || true)
        [ -z "$u" ] || { echo "a qemu has the card: not reloading vfio-pci"; return 1; }
        [ "$(cat /sys/module/vfio_pci/refcnt 2>/dev/null)" = 0 ] || { echo "vfio-pci is in use (refcnt $(cat /sys/module/vfio_pci/refcnt)): not reloading"; return 1; }
        for d in $GPU $GPUA; do [ "$(basename "$(readlink /sys/bus/pci/devices/$d/driver 2>/dev/null)" 2>/dev/null)" = vfio-pci ] && keep+=("$d"); done
        S modprobe -r vfio-pci || { echo "modprobe -r vfio-pci failed"; return 1; }
    fi
    [ -d /sys/module/vfio_pci ] || S modprobe vfio-pci || { echo "modprobe vfio-pci failed"; return 1; }
    for d in "${keep[@]}"; do   # back on vfio-pci as they were (override only for the probe, then cleared)
        S sh -c 'echo vfio-pci > "$1/driver_override"; echo "$2" > /sys/bus/pci/drivers_probe; echo > "$1/driver_override"' _ /sys/bus/pci/devices/$d "$d"
    done
    if [ -n "$reload" ]; then echo "vfio-pci reloaded with the option file; devices put back on vfio-pci: ${keep[*]:-none}"; else echo "option file already there and the parameter reads Y: module not reloaded"; fi
    [ -e "$f" ] || { echo "no $f"; return 1; }
    echo "$f = $(cat "$f")"
    for d in $GPU $GPUA; do echo "$d driver: $(basename "$(readlink /sys/bus/pci/devices/$d/driver 2>/dev/null)" 2>/dev/null || echo none)"; done
    [ "$(cat "$f")" = Y ]
}
stepv "vfio-pci disable_idle_d3=1 (loaded with the option)" vfio_d3
# 9b. power/control=on for the Radeon, its audio function and every PCI bridge above them (found in sysfs, not typed by hand); after 9c, which rebinds
pm_on() {
    local d p rc=0 chain
    p=$(readlink -f /sys/bus/pci/devices/$GPU) || { echo "$GPU not found"; return 1; }
    chain=$(tr '/' '\n' <<<"${p#/sys/devices/}" | grep -E '^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$')
    for d in $chain $GPUA; do
        S sh -c 'echo on > "$1"' _ /sys/bus/pci/devices/$d/power/control || { echo "cannot write $d"; rc=1; }
        echo "$d power/control=$(cat /sys/bus/pci/devices/$d/power/control 2>/dev/null)"
        [ "$(cat /sys/bus/pci/devices/$d/power/control 2>/dev/null)" = on ] || rc=1
    done
    return $rc
}
stepv "power/control=on: Radeon, audio, bridges above" pm_on

if [ "$FAILS" -eq 0 ]; then echo "ALL OK"; else echo "$FAILS step(s) FAILED"; exit 1; fi
