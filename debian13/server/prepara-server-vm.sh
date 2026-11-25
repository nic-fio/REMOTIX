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

if [ "$FAILS" -eq 0 ]; then echo "ALL OK"; else echo "$FAILS step(s) FAILED"; exit 1; fi
