#!/bin/bash
# prepara-server.sh - re-create the REMOTIX-UBUNTU dev tools after a reboot (rootfs is RAM).
# Run as the normal user (nicfio); root steps go through `echo | sudo -S`. Idempotent.
set -euo pipefail
export LC_ALL=C DEBIAN_FRONTEND=noninteractive

BASE=/media/REMOTIX-UBUNTU
# podman storage: SHARED with the Debian work. The server's podman (user and root) already keeps all images
# (Debian and Ubuntu: build image and boxes) under /media/REMOTIX-DEBIAN/podman. This script must not move it or
# create another one (the existing images would become invisible), and must not need the Debian script to run first.
# So the podman config files below are only written if absent, with that same path; if present they are left alone.
# The Debian script writes the same content, so running both, in any order, they do not clash.
PODMAN_BASE=/media/REMOTIX-DEBIAN
ME=$(id -un); MYUID=$(id -u)
HOME_DIR=$(getent passwd "$ME" | cut -d: -f6)
RT=/run/user/$MYUID
FAILS=0

ok() { echo "OK   $*"; }
ko() { echo "FAIL $*"; FAILS=$((FAILS+1)); }
# step <description> <command...>: run, print one OK/FAIL line, never abort
step() { local d=$1; shift; if "$@" >/tmp/prepara-step.$$ 2>&1; then ok "$d"; else ko "$d"; sed 's/^/     /' /tmp/prepara-step.$$ | tail -5; fi; rm -f /tmp/prepara-step.$$; }
S() { echo | sudo -S -p "" "$@"; }

[ "$MYUID" -ne 0 ] || { echo "run as the normal user, not root"; exit 1; }

# 1. hostname in /etc/hosts (silences sudo "unable to resolve host")
fix_hosts() {
    local hn; hn=$(hostname)
    if grep -Eq "(^|[[:space:]])${hn}([[:space:]]|\$)" /etc/hosts; then return 0; fi
    S bash -c '[ -z "$(tail -c1 /etc/hosts)" ] || echo >> /etc/hosts; printf "127.0.1.1\t%s\n" "$1" >> /etc/hosts' _ "$hn"
}
step "hostname in /etc/hosts" fix_hosts

# 2. work folders on the persistent disk
mk_dirs() {
    S mkdir -p "$BASE"/{albero,pacchetti,prove,vm,log,lavoro}
    S chown "$ME:$ME" "$BASE" "$BASE"/{albero,pacchetti,prove,vm,log,lavoro}
    # shared podman storage and temp folder (same as the Debian work; mkdir -p, never removes anything)
    S mkdir -p "$PODMAN_BASE"/{podman/root,podman/user,tmp}
    S chown "$ME:$ME" "$PODMAN_BASE" "$PODMAN_BASE"/{tmp,podman/user}
}
step "folders under $BASE (and shared podman storage under $PODMAN_BASE)" mk_dirs

# 3. host packages (minimal: builds happen in containers)
PKGS=(podman uidmap passt slirp4netns fuse-overlayfs crun git rsync curl ca-certificates)
inst_pkgs() {
    local missing=() p
    for p in "${PKGS[@]}"; do dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p"); done
    [ ${#missing[@]} -eq 0 ] && return 0
    S apt-get update -qq
    S apt-get install -y -qq --no-install-recommends "${missing[@]}"
}
step "apt packages: ${PKGS[*]}" inst_pkgs

# 4. runtime dir (no systemd user session here)
mk_rt() { S install -d -m 700 -o "$ME" -g "$ME" "$RT"; }
step "$RT (mode 700)" mk_rt

# 5. podman config: storage on disk (root and user, shared with Debian, see PODMAN_BASE), cgroupfs for the user
write_file() { # $1=dest $2=content $3=root|user
    local dest=$1 content=$2
    # write only if absent: an existing file (the Debian script's, or the owner's) is never replaced
    if [ -f "$dest" ]; then return 0; fi
    if [ "$3" = root ]; then
        S mkdir -p "$(dirname "$dest")"
        local t; t=$(mktemp); printf '%s\n' "$content" > "$t"   # sudo's stdin is taken by the password
        S install -m 644 "$t" "$dest"; rm -f "$t"
    else
        mkdir -p "$(dirname "$dest")"
        printf '%s\n' "$content" > "$dest"
    fi
}
cfg() {
    write_file /etc/containers/storage.conf "$(printf '[storage]\ndriver = "overlay"\nrunroot = "/run/containers/storage"\ngraphroot = "%s/podman/root"' "$PODMAN_BASE")" root
    write_file "$HOME_DIR/.config/containers/storage.conf" "$(printf '[storage]\ndriver = "overlay"\nrunroot = "%s/containers"\ngraphroot = "%s/podman/user"' "$RT" "$PODMAN_BASE")" user
    write_file "$HOME_DIR/.config/containers/containers.conf" "$(printf '[engine]\ncgroup_manager = "cgroupfs"\nevents_logger = "file"\nimage_copy_tmp_dir = "%s/tmp"' "$PODMAN_BASE")" user
    write_file /etc/containers/containers.conf.d/99-remotix.conf "$(printf '[engine]\ncgroup_manager = "cgroupfs"\nevents_logger = "file"\nimage_copy_tmp_dir = "%s/tmp"' "$PODMAN_BASE")" root
}
step "podman config (storage on $PODMAN_BASE/podman, cgroupfs; only if absent)" cfg

# 6. user groups and subuid check
chk_ids() {
    grep -q "^$ME:" /etc/subuid && grep -q "^$ME:" /etc/subgid
}
step "subuid/subgid for $ME" chk_ids

# 7. inotify limits (many containers share one uid)
ino() { S sysctl -q -w fs.inotify.max_user_instances=8192 fs.inotify.max_user_watches=1048576; }
step "inotify limits" ino

# 8. packages for prove/base-check.py: real browsers (Chromium = the Chrome engine, Firefox ESR), a headless
#    Wayland compositor to run them in (labwc + wlr-randr), PIL to judge the pictures, libavcodec for H.264 in Firefox
BROWSER_PKGS=(chromium firefox-esr labwc wlr-randr python3-pil libavcodec61 fonts-dejavu-core)
inst_browser_pkgs() {
    local missing=() p
    for p in "${BROWSER_PKGS[@]}"; do dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p"); done
    [ ${#missing[@]} -eq 0 ] && return 0
    S apt-get update -qq
    S apt-get install -y -qq --no-install-recommends "${missing[@]}"
}
step "apt packages for prove/: ${BROWSER_PKGS[*]}" inst_browser_pkgs

# 9. sound server for the test browsers (prove/): Firefox starts no AudioContext without a PulseAudio-compatible server.
#    PipeWire + pipewire-pulse + WirePlumber for this user, started by hand (no systemd user session here), with one null sink;
#    the socket is $RT/pulse/native, which prove/lib.py gives to Firefox. Idempotent: started only if nothing answers.
SOUND_PKGS=(pipewire pipewire-pulse wireplumber pulseaudio-utils)
inst_sound_pkgs() {
    local missing=() p
    for p in "${SOUND_PKGS[@]}"; do dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p"); done
    [ ${#missing[@]} -eq 0 ] && return 0
    S apt-get update -qq
    S apt-get install -y -qq --no-install-recommends "${missing[@]}"
}
step "apt packages for the sound server: ${SOUND_PKGS[*]}" inst_sound_pkgs
sound_up() {
    local c="$HOME_DIR/.config/pipewire/pipewire-pulse.conf.d" i
    mkdir -p "$c"
    printf '%s\n' 'pulse.cmd = [ { cmd = "load-module" args = "module-null-sink sink_name=rx_null" flags = [ ] } ]' > "$c/null-sink.conf"
    if ! env XDG_RUNTIME_DIR="$RT" PULSE_SERVER="unix:$RT/pulse/native" pactl info 2>/dev/null | grep -q 'Default Sink: rx_null'; then
        # our own pids only (the test boxes' sessions run as the same uid, by name we would kill theirs)
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

# 9b. packages for the real-system VMs (server/vm.sh, server/vm-radeon.sh): QEMU/KVM, qcow2 tools (qemu-img), seed ISO builder (genisoimage),
#     UEFI firmware for vm-radeon.sh (ovmf), kernel/initrd extraction from the desktop ISOs (xorriso), /dev/kvm ACL (acl); disks built from ISO squashfs
#     layers (gdisk, dosfstools, rsync; the kernel mounts squashfs itself).  vm.sh boots with SeaBIOS.
VM_PKGS=(qemu-system-x86 qemu-utils genisoimage acl ovmf xorriso gdisk dosfstools rsync)
inst_vm_pkgs() {
    local missing=() p
    for p in "${VM_PKGS[@]}"; do dpkg -s "$p" >/dev/null 2>&1 || missing+=("$p"); done
    [ ${#missing[@]} -eq 0 ] && return 0
    S apt-get update -qq
    S apt-get install -y -qq --no-install-recommends "${missing[@]}"
}
step "apt packages for the VM: ${VM_PKGS[*]}" inst_vm_pkgs
step "folder $BASE/vm" mkdir -p "$BASE/vm"
kvm_acl() { [ -w /dev/kvm ] || S setfacl -m "u:$ME:rw" /dev/kvm; }   # /dev/kvm is root:kvm; the ACL lasts until reboot
step "/dev/kvm usable by $ME" kvm_acl

# 10. self-check
PU() { env XDG_RUNTIME_DIR="$RT" podman "$@"; }
selfcheck_user() { [ "$(PU run --rm docker.io/library/ubuntu:26.04 cat /etc/os-release)" ]; }
selfcheck_root() { [ "$(S podman run --rm docker.io/library/ubuntu:26.04 cat /etc/os-release)" ]; }
step "self-check rootless: podman run ubuntu:26.04" selfcheck_user
step "self-check root (sudo): podman run ubuntu:26.04" selfcheck_root
echo "graphroot user: $(PU info --format '{{.Store.GraphRoot}}' 2>&1 | tail -1)"
echo "graphroot root: $(S podman info --format '{{.Store.GraphRoot}}' 2>&1 | tail -1)"
echo "ubuntu version (user): $(PU run --rm docker.io/library/ubuntu:26.04 grep ^VERSION= /etc/os-release 2>&1 | tail -1)"

if [ "$FAILS" -eq 0 ]; then echo "ALL OK"; else echo "$FAILS step(s) FAILED"; exit 1; fi
