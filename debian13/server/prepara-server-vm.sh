#!/bin/bash
# prepara-server-vm.sh - put back on the dev server (Debian 13, rootfs in RAM, emptied at every reboot) ONLY what the Debian 13 test VMs
# (vm-radeon.sh in this folder) need.  No podman, no containers.  Run as the normal user; root steps go through `echo | sudo -S`.
# Idempotent: one OK/FAIL line per step.  Nothing is ever removed.
set -uo pipefail
export LC_ALL=C DEBIAN_FRONTEND=noninteractive
BASE=/media/REMOTIX-DEBIAN
ME=$(id -un); MYUID=$(id -u)
FAILS=0
ok() { echo "OK   $*"; }
ko() { echo "FAIL $*"; FAILS=$((FAILS+1)); }
step() { local d=$1 t; shift; t=$(mktemp); if "$@" >"$t" 2>&1; then ok "$d"; else ko "$d"; sed 's/^/     /' "$t" | tail -5; fi; rm -f "$t"; }
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
    S mkdir -p "$BASE"/{vm-radeon,tmp}
    S chown "$ME:$ME" "$BASE" "$BASE"/{vm-radeon,tmp}
}
step "folders under $BASE" mk_dirs

# 3. packages for the VMs: QEMU/KVM + qcow2 tools, UEFI firmware, partitioning/filesystems/copy tools for building the disk from the ISO's squashfs
VM_PKGS=(qemu-system-x86 qemu-utils ovmf gdisk dosfstools e2fsprogs rsync perl openssh-client util-linux acl)
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

if [ "$FAILS" -eq 0 ]; then echo "ALL OK"; else echo "$FAILS step(s) FAILED"; exit 1; fi
