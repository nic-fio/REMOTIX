#!/bin/bash
# vm-radeon.sh - real-system test VMs for Ubuntu 26.04 (desktop ISO installed for real, UEFI, KVM) with the server's Radeon passed through (vfio-pci) on demand.
# Usage: vm-radeon.sh crea|accendi|spegni|ssh|stato|prova-avvio <ubuntu|kubuntu|xubuntu|lubuntu|costruzione> [cmd...]
#        (ubuntu: autoinstall; the others: built from the ISO squashfs; costruzione: .deb build VM, Xubuntu image, virtual only, ssh 2345)
#        vm-radeon.sh accendi <name> virtuale              (no Radeon: virtual video card, same ports)
#        vm-radeon.sh schermo <name> <file.png>            (screendump of a VM started with "virtuale")
#        vm-radeon.sh tasti <name> <key> [key...]          (QEMU sendkey names: ret, tab, ctrl-alt-f2, shift-a ...)
#        vm-radeon.sh scrivi <name> <text>                 (types the text through sendkey; "\n" in the text = Enter)
#        vm-radeon.sh istantanea|ripristina <name> <label> (qcow2 snapshot of the disk; VM must be off)
#   crea    unattended install from the desktop ISO (autoinstall), with a temporary virtual video card; the VM powers itself off at the end
#   crea    (kubuntu, xubuntu, lubuntu, costruzione: Calamares ISOs; xubuntu: its live kernel crashes the autoinstall) builds the disk from the ISO's squashfs layers the way
#           Calamares would (unpackfs, fstab, users, bootloader from the ISO pool, initramfs): GPT + EFI partition, Ubuntu kernel of the ISO, hostname, empty machine-id,
#           users, ssh key.  Every disk gets amdgpu.runpm=0 on its kernel command line (/etc/default/grub.d/zz-remotix-banco.cfg).  Then one virtual first boot checks it.
#   accendi Radeon (03:00.0 + 03:00.1 bound to vfio-pci) as the only video card, 12G of RAM, serial console in serial.log, no autologin.  PROTECTED, see below.
#   accendi <name> virtuale   no Radeon, virtio-vga, 5G, no window; stays on until spegni.  Several virtual VMs may run together; the Radeon only in one.
#   prova-avvio  boot check WITHOUT the Radeon (virtual card, ssh on port+100, no REMOTIX forward): prints facts, then powers off (--resta: leave it on)
#   spegni  poweroff via ssh (then ACPI powerdown, then kill as a declared last resort), wait for the process to be really gone, and only then
#           give the Radeon back to the host (03:00.1 -> snd_hda_intel; 03:00.0 stays driverless as at boot) - only if THIS VM held it
#   istantanea  qemu-img snapshot -c (VM off).   ripristina  qemu-img snapshot -a: the CURRENT disk state is discarded (VM off, explicit command only)
# RADEON PROTECTION (structural; on 26 Nov 2026 the whole server froze 4 times because a guest amdgpu kept suspending/resuming the passed-through card):
#   1. crea puts amdgpu.runpm=0 on the guest's kernel command line.
#   2. accendi WITH the Radeon first needs the file $D/runpm.ok, written only after /proc/cmdline of that VM, booted WITHOUT the Radeon, showed amdgpu.runpm=0.
#      The marker is good for ONE boot: every start of the VM by this script (virtual, Radeon, prova-avvio, crea) deletes it, so each accendi with the Radeon has a fresh proof.
#      No marker: accendi does the whole check itself (virtual boot, apply the parameter if missing, reboot, re-check, marker, power off); if it cannot get the
#      proof it dies and the card is NOT given.  crea and ripristina delete the marker.  There is no option to skip this.
#   3. Right after the Radeon boot, /sys/module/amdgpu/parameters/runpm must be 0 and /proc/cmdline must have the parameter: else the VM is powered off at once,
#      the card is given back and the marker is deleted.  (If ssh does not answer at all the VM is NOT powered off: see the comment in accendi.)
# The Radeon is ONE for the whole server: accendi refuses if any VM under $ROOT, or ANY other qemu of the server (Fedora or Debian bench), already has it;
# gpu_take/gpu_give check it too, and stato shows it.
# Everything lives in /media/REMOTIX-UBUNTU/vm-radeon/<desktop>/: disk.qcow2, OVMF_VARS.fd, seed.iso, vmkey, vm.pid, serial.log, monitor.sock, runpm.ok.
# Host ports (LAN-reachable): ssh -> guest 22; REMOTIX tcp+udp -> guest 7447.  Login: prova / prova2 (password prova2026, prova has sudo), or key vmkey.
# Deletes nothing of anyone's: crea refuses to touch an existing disk.  The ONLY files this script removes are its own: crea's temporary raw image (build/disk.raw, after the
# qcow2 exists), runpm.ok, schermo.png (schermo's temporary).  Kills a VM only as a declared last resort in spegni.  Never touches /media/DOWNLOAD (the ISOs are only
# mounted read-only).  Must run as a user that can sudo (qemu and vfio need root).
set -euo pipefail
SELF=$(readlink -f "$0")
ROOT=/media/REMOTIX-UBUNTU/vm-radeon
ISODIR=/media/DOWNLOAD
GPU=0000:03:00.0 GPUA=0000:03:00.1
CPUS=4 MEM=${RX_VM_MEM:-5G} DISKSZ=40G
CODE=/usr/share/OVMF/OVMF_CODE_4M.fd VARS0=/usr/share/OVMF/OVMF_VARS_4M.fd
RUNPM=amdgpu.runpm=0
USAGE="usage: $0 crea|accendi|spegni|ssh|stato|prova-avvio ubuntu|kubuntu|xubuntu|lubuntu|costruzione [cmd|virtuale]; $0 schermo <name> <file.png>; $0 tasti <name> <key>...; $0 scrivi <name> <text>; $0 istantanea|ripristina <name> <label>"

# desktop table: iso, ssh port, REMOTIX port
case "${2:-}" in
ubuntu)  ISO=$ISODIR/ubuntu-26.04.1-desktop-amd64.iso SSHP=2341 RXP=8841 KIND=autoinstall;;
kubuntu) ISO=$ISODIR/kubuntu-26.04.1-desktop-amd64.iso SSHP=2342 RXP=8842 KIND=squashfs LAYERS="casper/filesystem.squashfs";;
xubuntu) ISO=$ISODIR/xubuntu-26.04.1-desktop-amd64.iso SSHP=2343 RXP=8843 KIND=squashfs LAYERS="casper/minimal.squashfs casper/minimal.standard.squashfs";;
lubuntu) ISO=$ISODIR/lubuntu-26.04.1-desktop-amd64.iso SSHP=2344 RXP=8844 KIND=squashfs LAYERS="casper/minimal.squashfs casper/minimal.standard.squashfs";;
# costruzione: the fifth VM, only to build REMOTIX's .deb (Xubuntu image, built exactly like xubuntu); never with the Radeon, no REMOTIX port forward, 8 CPUs, 6G
costruzione) ISO=$ISODIR/xubuntu-26.04.1-desktop-amd64.iso SSHP=2345 RXP=0 KIND=squashfs LAYERS="casper/minimal.squashfs casper/minimal.standard.squashfs" FWD="" CPUS=8 MEM=${RX_VM_MEM:-6G};;
*) echo "$USAGE"; exit 2;;
esac
NAME=$2
HN=rx-$NAME; [ "$NAME" != costruzione ] || HN=rx-ub-costruzione
D=$ROOT/$NAME
DISK=$D/disk.qcow2 VARS=$D/OVMF_VARS.fd SEED=$D/seed.iso PID=$D/vm.pid SER=$D/serial.log MON=$D/monitor.sock MARK=$D/runpm.ok
PASS=prova2026
sx() { if [ "$(id -u)" = 0 ]; then "$@"; else echo | sudo -S -p "" "$@"; fi; }
sx true || { echo "sudo does not work: refusing to guess whether a VM is running"; exit 1; }
sshv() { ssh -i "$D/vmkey" -p $SSHP -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=5 prova@127.0.0.1 "$@"; }
die() { echo "$*"; exit 1; }
# alive <name>: the pid file of that VM names a live qemu that has THAT VM's disk (pid and socket files on /media outlive a server reboot,
# so a stale pid never counts).  Sets CMD to the command line.  Nothing is killed or deleted here.
alive() {
  local p
  [ -e "$ROOT/$1/vm.pid" ] || return 1
  p=$(cat "$ROOT/$1/vm.pid" 2>/dev/null || sx cat "$ROOT/$1/vm.pid" 2>/dev/null) || return 1   # readable without sudo once chmod 644 (see below)
  [[ $p =~ ^[0-9]+$ ]] || return 1
  [ -r /proc/$p/cmdline ] || return 1
  CMD=$(tr '\0' ' ' < /proc/$p/cmdline) || return 1
  case $CMD in *qemu-system*"file=$ROOT/$1/disk.qcow2,"*) PIDV=$p; return 0;; esac
  return 1
}
running() { alive "$NAME"; }
# gpu_owner: name of the VM that holds the Radeon (a live qemu with the vfio hostdev), if any
gpu_owner() {
  local dd n
  for dd in "$ROOT"/*/; do
    n=$(basename "$dd")
    if alive "$n"; then case $CMD in *"host=$GPU"*) echo "$n"; return 0;; esac; fi
  done
  return 0
}
lock() { mkdir -p "$ROOT"; exec 9>"$ROOT/.lock"; flock -n 9 || die "another vm-radeon.sh holds the lock: a VM is being started or stopped (or checked at the end of crea): try again later"; }
# lock_wait: like lock, but waits (up to 40 min) for the other vm-radeon.sh to finish: for crea, after a long build
lock_wait() { mkdir -p "$ROOT"; exec 9>"$ROOT/.lock"; flock -w 2400 9 || die "the lock stayed taken for 40 min: the disk is built, only the first-boot check is missing (run: $0 prova-avvio $NAME)"; }
# mon <command...>: send monitor commands (HMP) on the VM's socket, one after the other, 0.4 s apart (a sendkey holds each key 0.1 s, so QEMU's key
# queue never builds up), 1.2 s extra after every 16 commands, the monitor's replies are read away, and it returns 1.2 s after the last command: only
# then QEMU has finished typing.  (perl-base has no Time::HiRes: nap uses select; perl's own "sleep" would truncate 0.4 to 0.)
MONPL='use IO::Socket::UNIX; sub nap { select(undef,undef,undef,$_[0]) }
my $s=IO::Socket::UNIX->new(Peer=>shift @ARGV) or die "cannot connect to the monitor: $!"; $s->blocking(0); nap(.3);
my $n=0; sub drain { my $b; 1 while sysread($s,$b,65536) }
for my $c (@ARGV) { print $s "$c\n"; $s->flush; nap(.4); drain(); nap(1.2) if ++$n % 16 == 0 } nap(1.2); drain();'
mon() { sx perl -e "$MONPL" "$MON" "$@"; }
sysw() { sx sh -c 'echo "$1" > "$2"' _ "$2" "$1" 2>/dev/null || true; }   # sysfs writes: an unbind of an already-free device is not an error
drv() { basename "$(readlink /sys/bus/pci/devices/$1/driver 2>/dev/null)" 2>/dev/null || true; }
# wait_gone <n>: up to n*2 s for this VM's qemu to be really gone
wait_gone() { local i; for i in $(seq "$1"); do running || return 0; sleep 2; done; return 1; }
# wait_ssh <n>: up to n*3 s for ssh as prova
wait_ssh() { local i; for i in $(seq "$1"); do sshv true 2>/dev/null && return 0; sleep 3; done; return 1; }

# stop_vm: ssh poweroff, then ACPI powerdown, then kill as a declared last resort; returns only when the process is really gone (else dies)
stop_vm() {
  local p=$PIDV q
  # a VM started by prova-avvio or crea answers on another ssh port: take it from its own command line
  q=$(grep -oE 'hostfwd=tcp:0\.0\.0\.0:[0-9]+-:22' <<<"$CMD" | grep -oE ':[0-9]+-' | tr -dc 0-9 || true)
  [ -z "$q" ] || SSHP=$q
  sshv "echo $PASS | sudo -S -p '' systemctl poweroff" 2>/dev/null || true
  if ! wait_gone 30; then
    echo "no answer to ssh poweroff: sending ACPI powerdown"; mon system_powerdown || true
    if ! wait_gone 30; then
      echo "STILL RUNNING: killing qemu (pid $p) as a last resort"
      sx kill "$p" || true
      wait_gone 15 || die "qemu (pid $p) did not die: Radeon NOT touched, look at it by hand"
    fi
  fi
}

# gpu_user: any qemu of the server (this bench or not, e.g. the Debian bench) that has the Radeon in its command line: prints its pid and name
gpu_user() { ps -eo pid=,args= | grep -E "qemu-system.*host=$GPU" | grep -v grep | cut -c1-80 || true; }
# pci_chain <bdf>: the device and the PCI bridges above it up to the root port, read from sysfs (never typed by hand)
pci_chain() {
  local p; p=$(readlink -f /sys/bus/pci/devices/$1 2>/dev/null) || return 0
  tr '/' '\n' <<<"${p#/sys/devices/}" | grep -E '^[0-9a-f]{4}:[0-9a-f]{2}:[0-9a-f]{2}\.[0-7]$' || true
}
# host side of the protection: no runtime power management on the Radeon, its audio function and the bridges above them (set again after every rebind)
gpu_pm_on() { local d; for d in $(pci_chain $GPU) $GPUA; do sysw /sys/bus/pci/devices/$d/power/control on; done; }
# bind both Radeon functions to vfio-pci (03:00.1 is first taken away from snd_hda_intel).  Callers have already checked that no VM of this bench holds it.
gpu_take() {
  local u; u=$(gpu_user); [ -z "$u" ] || die "the Radeon is in use by another qemu of the server ($u): not touching it"
  sx modprobe vfio-pci
  for d in $GPUA $GPU; do
    sysw /sys/bus/pci/devices/$d/driver_override vfio-pci
    [ -e /sys/bus/pci/devices/$d/driver ] && sysw /sys/bus/pci/devices/$d/driver/unbind $d
    sysw /sys/bus/pci/drivers_probe $d
  done
  for d in $GPU $GPUA; do
    [ "$(drv $d)" = vfio-pci ] || die "FAIL: $d not on vfio-pci"
  done
  gpu_pm_on
}
# give them back: audio function to snd_hda_intel, the GPU itself stays without a driver (amdgpu is blacklisted on this server)
gpu_give() {
  local u; u=$(gpu_user); [ -z "$u" ] || die "the Radeon is in use by another qemu of the server ($u): not touching it"
  for d in $GPU $GPUA; do
    [ -e /sys/bus/pci/devices/$d/driver ] && sysw /sys/bus/pci/devices/$d/driver/unbind $d
    sysw /sys/bus/pci/devices/$d/driver_override ""
  done
  sysw /sys/bus/pci/devices/$GPUA/driver_override snd_hda_intel
  sysw /sys/bus/pci/drivers_probe $GPUA
  sysw /sys/bus/pci/devices/$GPUA/driver_override ""
  gpu_pm_on
  [ -d /sys/bus/pci/devices/$GPU ] && echo "$GPU present, driver: $(drv $GPU | grep . || echo none)" || echo "WARNING: $GPU is gone"
  echo "$GPUA driver: $(drv $GPUA | grep . || echo none)"
  [ "$(drv $GPUA)" = snd_hda_intel ] || echo "WARNING: $GPUA is not on snd_hda_intel"
}
# common qemu parts: q35, UEFI, KVM, NAT with LAN-visible forwards, no desktop display
base_args() {
  echo -enable-kvm -machine q35,accel=kvm -cpu host -smp $CPUS -m ${MEMV:-$MEM} -vga none -display none -monitor unix:"$MON",server,nowait \
    -serial file:"$SER" -drive if=pflash,format=raw,unit=0,readonly=on,file=$CODE -drive if=pflash,format=raw,unit=1,file="$VARS" \
    -drive file="$DISK",if=virtio,format=qcow2 \
    -netdev user,id=n0,hostfwd=tcp:0.0.0.0:$SSHP-:22${FWD-,hostfwd=tcp:0.0.0.0:$RXP-:7447,hostfwd=udp:0.0.0.0:$RXP-:7447} \
    -device virtio-net-pci,netdev=n0 -device virtio-rng-pci -daemonize -pidfile "$PID"
}
# start_virtual: the VM WITHOUT the Radeon (virtio-vga, no window); the caller sets SSHP/FWD/MEMV/CPUS first if it wants other values
start_virtual() {
  sx rm -f "$MARK"   # the proof is good for ONE boot: any start of the VM voids it (ensure_runpm writes it again after its own boot, while the VM runs)
  sx sh -c ': > "$1"' _ "$SER"
  sx qemu-system-x86_64 $(base_args) -device virtio-vga 9>&- 8>&- || die "qemu did not start"
  sx chmod 644 "$SER" "$PID" 2>/dev/null || true
}

# ---- Radeon protection (see the header) ----
cmdline_ok() { sshv "grep -qwF '$RUNPM' /proc/cmdline" 2>/dev/null; }
# apply_runpm: inside the VM, write the grub.d snippet and regenerate grub.cfg; if this grub does not pick the snippet up, edit /etc/default/grub (backup first)
apply_runpm() {
  local sc
  sc=$(cat <<'V'
set -eu
mkdir -p /etc/default/grub.d
printf 'GRUB_CMDLINE_LINUX="$GRUB_CMDLINE_LINUX amdgpu.runpm=0"\n' > /etc/default/grub.d/zz-remotix-banco.cfg
update-grub
if ! grep -q 'amdgpu.runpm=0' /boot/grub/grub.cfg; then
  [ -e /etc/default/grub.remotix-orig ] || cp -p /etc/default/grub /etc/default/grub.remotix-orig
  sed -i 's/^GRUB_CMDLINE_LINUX="\(.*\)"/GRUB_CMDLINE_LINUX="\1 amdgpu.runpm=0"/' /etc/default/grub
  update-grub
fi
grep -q 'amdgpu.runpm=0' /boot/grub/grub.cfg
V
)
  sshv "echo $(printf '%s\n' "$sc" | base64 -w0) | base64 -d > /tmp/rx-runpm.sh; echo $PASS | sudo -S -p '' bash /tmp/rx-runpm.sh; r=\$?; rm -f /tmp/rx-runpm.sh; exit \$r"
}
# stop_if_running: stop_vm only if this VM's qemu is alive (sets CMD/PIDV)
stop_if_running() { if running; then stop_vm; fi; }
# ensure_runpm: the proof that this VM's guest has amdgpu.runpm=0.  Marker present: nothing to do.  Else: virtual boot, check, apply+reboot+re-check if needed,
# write the marker, power off.  Any failure: die, the Radeon is never given.  Caller holds the lock and has checked that the VM is off.
ensure_runpm() {
  local bid nb i
  echo "runpm check: booting $NAME WITHOUT the Radeon to look at /proc/cmdline (the proof is always made fresh) ..."
  start_virtual; running || die "runpm check: qemu is not running after the start (see $SER): Radeon NOT given"
  wait_ssh 100 || { stop_if_running; die "runpm check: ssh not answering in 5 min (see $SER): no proof, Radeon NOT given"; }
  if ! cmdline_ok; then
    echo "runpm check: $RUNPM is missing: applying it inside the VM and rebooting it"
    bid=$(sshv "cat /proc/sys/kernel/random/boot_id" 2>/dev/null || true)
    apply_runpm || { stop_if_running; die "runpm check: could not apply $RUNPM in the VM: Radeon NOT given"; }
    sshv "echo $PASS | sudo -S -p '' systemctl reboot" 2>/dev/null || true
    for i in $(seq 60); do   # wait for a NEW boot (boot_id changes), up to 3 min
      sleep 3; nb=$(sshv "cat /proc/sys/kernel/random/boot_id" 2>/dev/null || true)
      [ -n "$nb" ] && [ "$nb" != "$bid" ] && break
    done
    [ -n "$nb" ] && [ "$nb" != "$bid" ] || { stop_if_running; die "runpm check: the VM did not come back after the reboot (see $SER): Radeon NOT given"; }
  fi
  cmdline_ok || { stop_if_running; die "runpm check: /proc/cmdline of $NAME still lacks $RUNPM: Radeon NOT given"; }
  sx sh -c 'printf "%s\n" "$1" > "$2"' _ "$(date '+%F %T') $(sshv 'uname -r; cat /proc/cmdline' 2>/dev/null | tr '\n' ' ')" "$MARK"
  echo "runpm check: OK, $RUNPM seen in /proc/cmdline; marker written"
  stop_if_running
}
# radeon_check: after the Radeon boot (ssh answers): the module parameter and the command line must both say runpm off.  The parameter may take a few seconds
# to appear; the command line is read up to 3 times (a hiccup of ssh must not power off a healthy VM).
radeon_check() {
  local i v= c=
  for i in $(seq 10); do v=$(sshv "cat /sys/module/amdgpu/parameters/runpm 2>/dev/null" 2>/dev/null || true); [ -n "$v" ] && break; sleep 3; done
  for i in 1 2 3; do cmdline_ok && { c=1; break; }; sleep 2; done
  if [ "$v" = 0 ] && [ -n "$c" ]; then echo "protection verified in the running VM: amdgpu runpm=$v, $RUNPM in /proc/cmdline"; return 0; fi
  echo "PROTECTION MISSING in the running VM: amdgpu runpm='${v:-not readable}', cmdline $([ -n "$c" ] && echo has || echo LACKS) $RUNPM"
  return 1
}
# radeon_guard: radeon_check, and if it fails: marker deleted, VM powered off at once, card given back, die.  The VM must be running with the Radeon and ssh must answer.
radeon_guard() {
  radeon_check && return 0
  sx rm -f "$MARK"
  echo "powering the VM off at once and giving the Radeon back"
  stop_if_running; gpu_give
  die "Radeon protection missing: VM stopped, card returned, marker deleted"
}

# build_squashfs (runs as root, via the hidden subcommand _build): disk from the ISO's squashfs layers, the way Calamares does it
build_squashfs() {
  local UUR UUE KVER l   # (the rest is global: the EXIT trap needs it)
  B=$D/build RAW=$D/build/disk.raw n=0 LOOPE= LOOPR=
  mkdir -p "$B/root" "$B/iso"; T=$B/root ISOM=$B/iso
  cleanup() {
    set +e; cd /
    for m in "$T/cdrom" "$T/run" "$T/dev/pts" "$T/dev" "$T/proc" "$T/sys" "$T/boot/efi" "$T" $(seq -f "$B/sq%g" $n -1 1) "$ISOM"; do mountpoint -q "$m" && umount "$m"; done
    for l in ${LOOPE:-} ${LOOPR:-}; do losetup -d "$l"; done
  }
  trap cleanup EXIT
  truncate -s $DISKSZ "$RAW"
  sgdisk -o -n1:0:+512M -t1:ef00 -c1:EFI -n2:0:0 -t2:8300 -c2:root "$RAW" >/dev/null
  # this server gives no partition nodes for loop devices: one loop device per partition, by offset (no udev, no partx)
  po() { sgdisk -i "$1" "$RAW" | awk -v k="$2" '$0 ~ k {print $3}'; }   # po <part> <"First sector"|"Last sector">
  E1=$(po 1 "First sector"); E2=$(po 1 "Last sector"); R1=$(po 2 "First sector"); R2=$(po 2 "Last sector")
  LOOPE=$(losetup --find --show -o $((E1*512)) --sizelimit $(((E2-E1+1)*512)) "$RAW")
  LOOPR=$(losetup --find --show -o $((R1*512)) --sizelimit $(((R2-R1+1)*512)) "$RAW")
  mkfs.vfat -F32 -n EFI "$LOOPE" >/dev/null; mkfs.ext4 -q -L rx-root "$LOOPR"
  mount "$LOOPR" "$T"; mkdir -p "$T/boot/efi"; mount "$LOOPE" "$T/boot/efi"
  mount -o loop,ro "$ISO" "$ISOM"
  for l in $LAYERS; do   # unpackfs: the layers one over the other, as the installer unpacks them
    n=$((n+1)); mkdir -p "$B/sq$n"; mount -t squashfs -o loop,ro "$ISOM/$l" "$B/sq$n"
    echo "[$(date +%T)] unpacking $l ..."; rsync -aHAX --numeric-ids --exclude='/boot/efi/*' "$B/sq$n/" "$T/"
    umount "$B/sq$n"
  done
  n=0
  KVER=$(ls "$T/lib/modules" | sort -V | tail -1); echo "kernel in the image: $KVER"
  # shellprocess before_bootloader_kerncopy: the ISO's kernel goes to /boot (only if it is the one the image has modules for)
  if cmp -s "$ISOM/casper/vmlinuz" "$T/boot/vmlinuz-$KVER"; then echo "ISO kernel = vmlinuz-$KVER of the image"; else echo "WARNING: casper/vmlinuz differs from vmlinuz-$KVER of the image: using the image's"; fi
  UUR=$(blkid -s UUID -o value "$LOOPR") UUE=$(blkid -s UUID -o value "$LOOPE")
  install -d -m 700 "$T/root/.rxbuild"
  # chroot mounts as Calamares' mount module does (no efivars: the server's NVRAM is never touched), plus the ISO as /cdrom
  mount --bind /dev "$T/dev"; mount -t devpts devpts "$T/dev/pts"; mount -t proc proc "$T/proc"; mount -t sysfs sys "$T/sys"
  mount -t tmpfs tmpfs "$T/run"; mkdir -p "$T/run/systemd/resolve"; cp /etc/resolv.conf "$T/run/systemd/resolve/stub-resolv.conf"
  mkdir -p "$T/cdrom"; mount --bind "$ISOM" "$T/cdrom"
  # (every write into the image's /etc, /usr, /var is made by the stage below, INSIDE the chroot: an absolute symlink in the image can never point at the server)
  cat > "$T/root/.rxbuild/stage.sh" <<S
set -eu
export DEBIAN_FRONTEND=noninteractive LC_ALL=C
printf 'UUID=%s / ext4 defaults 0 1\nUUID=%s /boot/efi vfat umask=0077 0 1\n' '$UUR' '$UUE' > /etc/fstab
echo '$HN' > /etc/hostname
sed -i '/^127\.0\.1\.1/d' /etc/hosts; echo '127.0.1.1 $HN' >> /etc/hosts
: > /etc/machine-id; mkdir -p /var/lib/dbus; ln -sf /etc/machine-id /var/lib/dbus/machine-id   # machineid: new id at first boot
printf 'LANG=en_US.UTF-8\n' > /etc/default/locale; echo Europe/Rome > /etc/timezone; ln -sf /usr/share/zoneinfo/Europe/Rome /etc/localtime
mkdir -p /etc/default/grub.d
printf 'GRUB_CMDLINE_LINUX="\$GRUB_CMDLINE_LINUX console=tty0 console=ttyS0,115200"\nGRUB_DISABLE_OS_PROBER=true\n' > /etc/default/grub.d/99-vm-serial.cfg
# Radeon protection (point 1): the guest's amdgpu never uses runtime power management
printf 'GRUB_CMDLINE_LINUX="\$GRUB_CMDLINE_LINUX $RUNPM"\n' > /etc/default/grub.d/zz-remotix-banco.cfg
printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d; chmod +x /usr/sbin/policy-rc.d   # no services started in the chroot; removed at the end
mkdir -p /tmp/cdsrc; cp /etc/apt/sources.list.d/cdrom.sources /tmp/cdsrc/
# users: the groups Calamares' users.conf gives (sudo for prova only)
G="adm,cdrom,dip,plugdev"; getent group lpadmin >/dev/null && G="\$G,lpadmin"
useradd -m -s /bin/bash -G "\$G,sudo" -c prova prova
useradd -m -s /bin/bash -G "\$G" -c prova2 prova2
echo 'prova:$PASS' | chpasswd; echo 'prova2:$PASS' | chpasswd
install -d -m 700 -o prova -g prova /home/prova/.ssh
echo '$(cat "$D/vmkey.pub")' > /home/prova/.ssh/authorized_keys; chown prova:prova /home/prova/.ssh/authorized_keys; chmod 600 /home/prova/.ssh/authorized_keys
# the installer's own removals (packages.conf of the ISO)
$RMCMD
# bootloader packages from the ISO pool, as before_bootloader_context does
apt-get -o Dir::Etc::sourceparts=/tmp/cdsrc update -qq
apt-get install -y -qq --no-upgrade -o Acquire::gpgv::Options::=--ignore-time-conflict grub-efi-amd64-signed shim-signed
rm -f /etc/apt/sources.list.d/cdrom.sources                      # rmcdrom
# the network (not in the ISO): ssh
apt-get update -qq
apt-get install -y -qq --no-upgrade openssh-server
# initramfs for THIS root (fstab is in place), then the bootloader without NVRAM writes
for d in /lib/modules/*; do v=\${d##*/}; if [ -e /boot/initrd.img-\$v ]; then update-initramfs -u -k \$v; else update-initramfs -c -k \$v; fi; done
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu --no-nvram
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=ubuntu --no-nvram --removable
update-grub
# if this grub did not read grub.d, put the parameter in /etc/default/grub (backup first)
grep -q '$RUNPM' /boot/grub/grub.cfg || { cp -p /etc/default/grub /etc/default/grub.remotix-orig; sed -i 's/^GRUB_CMDLINE_LINUX="\(.*\)"/GRUB_CMDLINE_LINUX="\1 $RUNPM"/' /etc/default/grub; update-grub; }
(locale-gen en_US.UTF-8 >/dev/null 2>&1 || true)
apt-get clean
rm -f /usr/sbin/policy-rc.d; rm -rf /tmp/cdsrc
S
  echo "[$(date +%T)] chroot stage ..."
  chroot "$T" /bin/bash /root/.rxbuild/stage.sh
  rm -rf "$T/root/.rxbuild"; rmdir "$T/cdrom" 2>/dev/null || true
  grep -q "root=UUID=$UUR" "$T/boot/grub/grub.cfg" || { echo "grub.cfg does not boot root=UUID=$UUR"; exit 1; }
  grep -q "$RUNPM" "$T/boot/grub/grub.cfg" || { echo "grub.cfg lacks $RUNPM"; exit 1; }
  cleanup; trap - EXIT; LOOPE= LOOPR=; set -e   # cleanup turned errexit off: back on, and the unmounts are CHECKED
  mountpoint -q "$T" && die "$T is still mounted: stopping, everything left as it is"
  if mount | grep -F " $B/" >/dev/null; then die "something under $B is still mounted: stopping, everything left as it is"; fi
  [ -z "$(losetup -j "$RAW")" ] || die "a loop device is still attached to $RAW: stopping, everything left as it is"
  echo "[$(date +%T)] converting to qcow2 ..."
  qemu-img convert -O qcow2 "$RAW" "$DISK.new" || die "qemu-img convert failed: $RAW and $DISK.new left as they are"
  mv -n "$DISK.new" "$DISK"
  [ -f "$DISK.new" ] && die "disk appeared meanwhile: $DISK.new kept, $RAW kept"
  [ -f "$DISK" ] || die "$DISK does not exist: $RAW kept"
  chown --reference="$D" "$DISK" "$VARS" 2>/dev/null || true
  rm -f "$RAW"   # the only thing this script deletes: its own temporary raw image, and only now that $DISK exists
  rmdir "$B/root" "$B/iso" "$B" 2>/dev/null || true
  echo "disk built: $DISK"
}

# first_boot: crea's last step.  One boot WITHOUT the Radeon (virtual card; ssh on SSHP+100), checked, then powered off.  It does NOT write the marker
# (only accendi does, after its own look at /proc/cmdline).  Caller holds the lock.
first_boot() {
  running && die "VM $NAME is running already: not starting a second qemu on its disk"
  SSHP=$((SSHP+100)); FWD=""
  start_virtual
  running || die "qemu is not running after the start (see $SER)"
  echo "[$(date +%T)] first boot ..."
  wait_ssh 100 || { echo "first boot: ssh not answering in 5 min (see $SER): VM left running, look at it"; exit 1; }
  local st
  st=$(sshv "timeout 300 systemctl is-system-running --wait" 2>&1 || true)
  echo "first boot: is-system-running=$st  uname -r: $(sshv 'uname -r' 2>&1)  hostname: $(sshv hostname 2>&1)"
  if cmdline_ok; then echo "first boot: cmdline has $RUNPM: yes"; else echo "first boot: cmdline has $RUNPM: NO"; stop_vm; die "crea FAILED: the disk of $NAME boots without $RUNPM (see /etc/default/grub.d in the image)"; fi
  stop_vm; echo "first boot: VM stopped"
}

case "${1:-}" in
_build) [ "$(id -u)" = 0 ] && [ -n "${RMCMD+x}" ] || die "_build is internal (called by crea as root with RMCMD set)"
  [ -f "$DISK" ] && die "disk exists ($DISK): not touching it"
  build_squashfs;;
crea)
  lock
  [ -f "$DISK" ] && die "disk exists ($DISK): not touching it"
  [ -f "$ISO" ] || die "missing $ISO"
  mkdir -p "$D"; cd "$D"
  # per-VM lock: two crea of DIFFERENT VMs may build at the same time; the global lock is only held for the checks and for the first boot
  exec 8>"$D/.crea.lock"; flock -n 8 || die "crea of $NAME is already running"
  exec 9>&-
  [ -f vmkey ] || ssh-keygen -q -t ed25519 -N "" -f vmkey
  sx rm -f "$MARK"   # a new disk has no proof yet
  T0=$(date +%s)
  if [ "$KIND" = squashfs ]; then
    case $NAME in
      kubuntu) RMCMD="apt-get -q -y --purge remove \$(dpkg-query -W -f '\${Package}\\n' | grep -E '^live|^(calamares-settings-kubuntu|calamares-settings-ubuntu-common|calamares-settings-ubuntu-common-data|calamares|calamares-data|libcalamaresui3.3|cifs-utils|kubuntu-installer-prompt)\$')";;
      *) RMCMD=true;;   # lubuntu, xubuntu, costruzione: nothing to remove (the installer lives in the live layer / in a snap, not in the unpacked layers)
    esac
    [ -f "$VARS" ] || cp $VARS0 "$VARS"
    echo "[$(date +%T)] building $NAME from the squashfs of $ISO (log: this output) ..."
    sx env RMCMD="$RMCMD" "$SELF" _build $NAME 8>&-
    echo "[$(date +%T)] build took $(( $(date +%s)-T0 )) s"
  else
    xorriso -osirrox on -indev "$ISO" -extract /casper/vmlinuz "$D/vmlinuz" -extract /casper/initrd "$D/initrd" 2>&1 | grep -iE "error|fail|cannot" || true
    [ -s "$D/vmlinuz" ] && [ -s "$D/initrd" ] || die "could not extract kernel/initrd from $ISO (casper/vmlinuz, casper/initrd)"
    HASH=$(openssl passwd -6 "$PASS")
    # the two grub.d snippets travel as base64: they contain a literal $GRUB_CMDLINE_LINUX that no shell between here and the guest may expand
    B64RP=$(printf 'GRUB_CMDLINE_LINUX="$GRUB_CMDLINE_LINUX %s"\n' "$RUNPM" | base64 -w0)
    B64SER=$(printf 'GRUB_CMDLINE_LINUX="$GRUB_CMDLINE_LINUX console=tty0 console=ttyS0,115200"\n' | base64 -w0)
    T=$(mktemp -d)
    printf 'instance-id: remotix-%s\nlocal-hostname: %s\n' "$NAME" "$HN" > "$T/meta-data"
    cat > "$T/user-data" <<U
#cloud-config
autoinstall:
  version: 1
  locale: en_US.UTF-8
  keyboard: {layout: us}
  timezone: Europe/Rome
  identity: {hostname: $HN, username: prova, password: "$HASH", realname: prova}
  storage: {layout: {name: direct}}
  refresh-installer: {update: false}
  updates: security
  shutdown: poweroff
  late-commands:
    - curtin in-target --target=/target -- apt-get install -y openssh-server
    - curtin in-target --target=/target -- sh -c "useradd -m -s /bin/bash -c prova2 prova2 && echo 'prova2:$PASS' | chpasswd"
    - curtin in-target --target=/target -- sh -c "install -d -m 700 -o prova -g prova /home/prova/.ssh && echo '$(cat vmkey.pub)' > /home/prova/.ssh/authorized_keys && chown prova:prova /home/prova/.ssh/authorized_keys && chmod 600 /home/prova/.ssh/authorized_keys"
    - curtin in-target --target=/target -- sh -c "mkdir -p /etc/default/grub.d && echo $B64RP | base64 -d > /etc/default/grub.d/zz-remotix-banco.cfg && echo $B64SER | base64 -d > /etc/default/grub.d/99-vm-serial.cfg && update-grub"
    - curtin in-target --target=/target -- grep -q $RUNPM /boot/grub/grub.cfg
U
    genisoimage -quiet -output "$SEED" -volid cidata -joliet -rock "$T/user-data" "$T/meta-data"; cp "$T/user-data" "$D/user-data.used"; rm -rf "$T"
    echo "[$(date +%T)] installing $NAME (temporary virtual video card; installer console in $SER, up to 60 min) ..."
    # disk and UEFI variables are created last, right before QEMU.  Kernel and initrd come straight from the ISO so that 'autoinstall'
    # can be put on the command line without repacking it.
    qemu-img create -q -f qcow2 "$DISK" $DISKSZ; cp $VARS0 "$VARS"
    MEMV=6G CPUS=8
    sx qemu-system-x86_64 $(base_args) -device virtio-vga -cdrom "$ISO" -drive file="$SEED",if=virtio,format=raw,readonly=on \
      -kernel "$D/vmlinuz" -initrd "$D/initrd" -append "autoinstall quiet splash console=ttyS0,115200 ---" -no-reboot 9>&- 8>&- \
      || die "qemu did not start: an EMPTY disk ($DISK) and $VARS were left behind: remove them by hand before running crea again"
    sx chmod 644 "$SER" "$PID" 2>/dev/null || true
    wait_gone 1800 || die "install still running after 60 min (pid $PIDV): NOT killed; look at $SER, or kill it by hand"
    # the installer powers the VM off only when it succeeded; as a second check the disk must hold an installed system
    SZ=$(stat -c %s "$DISK")
    [ "$SZ" -gt 4000000000 ] || die "VM stopped but the disk is only $SZ bytes: the install did not complete (see $SER)"
    echo "[$(date +%T)] install finished (VM powered off, disk $SZ bytes)"
    unset MEMV; CPUS=4
  fi
  lock_wait
  first_boot
  echo "crea $NAME finished in $(( $(date +%s)-T0 )) s: next, accendi $NAME [virtuale]";;
accendi)
  lock
  if running; then   # already on: say whether it is in the mode asked for; nothing is changed either way
    case $CMD in *"host=$GPU"*) HAVE=radeon;; *) HAVE=virtual;; esac
    if [ "${3:-}" = virtuale ]; then WANT=virtual; else WANT=radeon; fi
    if [ "$HAVE" = "$WANT" ]; then
      if [ "$HAVE" = radeon ]; then
        echo "already running with the Radeon (pid $PIDV): checking the protection"
        if wait_ssh 5; then radeon_guard; echo "already running with the Radeon (pid $PIDV), protection verified"; exit 0; fi
        echo "WARNING: $NAME has the Radeon but ssh does not answer: the check of amdgpu runpm could NOT be done (VM left running; spegni $NAME to stop it)"; exit 1
      fi
      echo "already running, virtual (pid $PIDV)"; exit 0
    fi
    die "running in the other mode ($HAVE, you asked for $WANT; pid $PIDV): spegni first"
  fi
  [ -f "$DISK" ] || die "no disk: run crea first"
  if [ "${3:-}" = virtuale ]; then
    # no Radeon: virtio-vga, no window; the monitor allows screendump and sendkey (schermo, tasti)
    start_virtual
    wait_ssh 120 && { echo "up, virtual video (ssh -p $SSHP; REMOTIX https://<server>:$RXP)"; exit 0; }
    echo "started but ssh not answering yet (see $SER)"; exit 1
  fi
  [ "$NAME" != costruzione ] || die "costruzione is the .deb build VM: it never gets the Radeon (use: accendi costruzione virtuale)"
  OWN=$(gpu_owner)
  [ -z "$OWN" ] || die "Radeon in use by VM $OWN: stop it first (or start this one with: $0 accendi $NAME virtuale)"
  [ -d /sys/bus/pci/devices/$GPU ] || die "$GPU not present"
  [ -z "$(gpu_user)" ] || die "the Radeon is in use by another qemu of the server ($(gpu_user)): not touching it"
  ensure_runpm   # protection point 2: no proof, no Radeon (dies if it cannot get the proof)
  # if the script is interrupted (or fails) from gpu_take until qemu is up, the card goes back to the host (armed BEFORE gpu_take); cleared as soon as qemu is up
  GIVE_ON_EXIT=1
  trap '[ -z "${GIVE_ON_EXIT:-}" ] || { echo "stopped before qemu started: giving the Radeon back"; gpu_give; }' EXIT
  trap 'exit 130' INT TERM HUP
  gpu_take
  sx rm -f "$MARK"   # the proof is good for ONE boot (the one ensure_runpm just saw): this boot needs its own check below
  MEMV=${RX_VM_MEM:-12G} CPUS=8   # the Radeon VM gets 12G and 8 CPUs (virtual ones 5G, 4 CPUs)
  sx sh -c ': > "$1"' _ "$SER"
  # Radeon as the only video card: on a root port, both functions, with its own ROM
  if ! sx qemu-system-x86_64 $(base_args) -device pcie-root-port,id=rp1,chassis=1,slot=1 \
      -device vfio-pci,host=$GPU,bus=rp1,addr=0.0,multifunction=on -device vfio-pci,host=$GPUA,bus=rp1,addr=0.1 9>&-; then
    GIVE_ON_EXIT=; echo "qemu did not start: giving the Radeon back"; gpu_give; exit 1
  fi
  GIVE_ON_EXIT=   # qemu is up: from here on only spegni gives the card back
  sx chmod 644 "$SER" "$PID" 2>/dev/null || true
  if wait_ssh 120; then
    # protection point 3: look at the running guest at once; if the protection is not really there, power it off and give the card back
    radeon_guard
    echo "up (ssh -p $SSHP; REMOTIX https://<server>:$RXP)"; exit 0
  fi
  # No ssh within 6 min: NOT powered off on purpose.  The proof ensure_runpm made just before shows that THIS disk boots with $RUNPM, so the card is
  # already protected by what the guest was built with; the cause may be harmless (e.g. a VM handed over with another network setup), and a forced poweroff of a guest that holds the
  # Radeon is itself a risk to the server.  The owner gets a loud warning instead and decides.
  echo "#####################################################################"
  echo "WARNING: $NAME has the Radeon but ssh does not answer (see $SER):"
  echo "the check of amdgpu runpm inside the running VM could NOT be done."
  echo "The VM is left running; look at it, or stop it with: $0 spegni $NAME"
  echo "#####################################################################"
  exit 1;;
spegni)
  lock
  if ! running; then
    OWN=$(gpu_owner)
    [ -z "$OWN" ] || die "VM $NAME is not running; the Radeon is held by VM $OWN: not touching anything"
    echo "not running (no VM holds the Radeon)"; gpu_give; exit 0
  fi
  # only the VM that holds the Radeon gives it back: stopping any other VM must never touch the card
  case $CMD in *"host=$GPU"*) HELD=1;; *) HELD=;; esac
  stop_vm
  if [ -n "$HELD" ]; then gpu_give; else echo "(VM $NAME did not use the Radeon: card not touched)"; fi
  echo stopped;;
prova-avvio)   # optional third argument --resta: leave the VM running (ssh on port+100, user prova) instead of checking and stopping it
  # boot check WITHOUT the Radeon: virtual video card, 5G, 4 CPUs, ssh on SSHP+100, no REMOTIX forward.  Not the final configuration.
  lock
  running && die "VM $NAME is running already"
  [ -f "$DISK" ] || die "no disk: run crea first"
  SSHP=$((SSHP+100)); FWD=""
  start_virtual
  wait_ssh 100 || true
  running || die "qemu is not running (see $SER)"
  sshv true 2>/dev/null || { echo "ssh not answering in 300 s (see $SER): stopping the VM"; stop_vm; exit 1; }
  if [ "${3:-}" = --resta ]; then echo "VM $NAME left running without the Radeon: ssh -p $SSHP (key $D/vmkey); stop it with: $0 spegni $NAME"; exit 0; fi
  sleep 20   # let the display manager come up
  sshv "echo -n 'uname -r: '; uname -r; echo -n 'cmdline: '; cat /proc/cmdline; echo -n 'display-manager: '; systemctl is-active display-manager; readlink /etc/systemd/system/display-manager.service; echo 'loginctl list-sessions:'; loginctl list-sessions --no-legend; echo 'aa-status:'; echo $PASS | sudo -S -p '' aa-status 2>&1 | head -3; echo 'snap list:'; snap list 2>&1 | head -20; echo -n 'hostname: '; hostname; echo -n 'machine-id: '; cat /etc/machine-id; getent passwd prova prova2 | cut -d: -f1,6; id prova; ls /dev/dri" || true
  stop_vm; echo "boot check done, VM stopped";;
ssh) shift 2; sshv "$@";;
schermo)   # screendump of a VM that runs with the virtual card
  [ -n "${3:-}" ] || die "usage: $0 schermo $NAME <file.png>"
  running || die "VM $NAME is not running"
  case $CMD in *virtio-vga*) ;; *) die "VM $NAME runs with the Radeon: no virtual screen to dump (start it with: accendi $NAME virtuale)";; esac
  [ -e "$3" ] && die "$3 exists already: not overwriting it"
  sx rm -f "$D/schermo.png"   # schermo's own temporary, left by the previous call
  mon "screendump $D/schermo.png -f png"
  for i in 1 2 3 4 5; do [ -s "$D/schermo.png" ] && break; sleep 1; done
  [ -s "$D/schermo.png" ] || die "no screendump produced"
  sx chmod 644 "$D/schermo.png"; cp "$D/schermo.png" "$3" && echo "saved $3";;
tasti)   # sendkey: each argument is one key combination, in QEMU names
  [ "$#" -ge 3 ] || die "usage: $0 tasti $NAME <key> [key...]   (e.g. ret tab ctrl-alt-f2 shift-a)"
  running || die "VM $NAME is not running"
  shift 2; args=(); for k in "$@"; do args+=("sendkey $k"); done
  mon "${args[@]}";;
scrivi)  # type a text (letters, digits and the usual punctuation; \n = Enter)
  [ -n "${3:-}" ] || die "usage: $0 scrivi $NAME <text>"
  running || die "VM $NAME is not running"
  printf -v TXT '%b' "$3"
  KEYS=$(perl -e '
my %sp=(" "=>"spc","."=>"dot",","=>"comma","-"=>"minus","_"=>"shift-minus","/"=>"slash",":"=>"shift-semicolon",";"=>"semicolon","="=>"equal","+"=>"shift-equal",
"@"=>"shift-2","!"=>"shift-1","#"=>"shift-3","\$"=>"shift-4","%"=>"shift-5","&"=>"shift-7","*"=>"shift-8","("=>"shift-9",")"=>"shift-0","\x27"=>"apostrophe",
"\""=>"shift-apostrophe","<"=>"shift-comma",">"=>"shift-dot","|"=>"shift-backslash","\\"=>"backslash","["=>"bracket_left","]"=>"bracket_right",
"{"=>"shift-bracket_left","}"=>"shift-bracket_right","~"=>"shift-grave_accent","`"=>"grave_accent","?"=>"shift-slash","\n"=>"ret","\t"=>"tab");
for my $c (split //, $ARGV[0]) {
  if (exists $sp{$c}) { print "$sp{$c}\n" }
  elsif ($c =~ /^[a-z0-9]$/) { print "$c\n" }
  elsif ($c =~ /^[A-Z]$/) { print "shift-".lc($c)."\n" }
  else { die "cannot type [$c]\n" }
}' "$TXT") || die "text has a character that cannot be typed"
  args=(); while read -r k; do args+=("sendkey $k"); done <<<"$KEYS"
  mon "${args[@]}";;
istantanea|ripristina)
  [ -n "${3:-}" ] || die "usage: $0 $1 $NAME <label>"
  lock
  running && die "VM $NAME is running: stop it first (snapshots only with the VM off)"
  [ -f "$DISK" ] || die "no disk"
  if [ "$1" = istantanea ]; then
    qemu-img snapshot -l "$DISK" 2>/dev/null | awk -v l="$3" '$2==l{f=1} END{exit !f}' && die "snapshot '$3' exists already"
    qemu-img snapshot -c "$3" "$DISK" && echo "snapshot '$3' created"
  else
    PRE=prima-$(date +%Y%m%d-%H%M%S)
    qemu-img snapshot -c "$PRE" "$DISK" || die "could not save the current state as '$PRE': nothing restored"
    echo "ripristina: current state saved as snapshot '$PRE'"
    echo "ripristina: the CURRENT state of the disk of $NAME is DISCARDED and replaced by snapshot '$3' (it stays only in '$PRE')"
    sx rm -f "$MARK"   # the restored disk may not have the Radeon protection: the proof is void until accendi sees it again
    qemu-img snapshot -a "$3" "$DISK" && echo "restored '$3' (OVMF_VARS.fd is not part of the snapshot; $MARK deleted: the next accendi re-checks $RUNPM)"
  fi;;
stato) if running; then echo "running pid $PIDV"; else echo stopped; [ -e "$PID" ] && echo "(stale pid file ignored)"; fi
  echo "Radeon held by VM: $(gpu_owner | grep . || echo none)"
  echo "qemu of the server with the Radeon (any bench): $(gpu_user | grep . || echo none)"
  for d in $GPU $GPUA; do echo "$d: $(drv $d)"; done
  for n in ubuntu kubuntu xubuntu lubuntu costruzione; do
    if [ -e "$ROOT/$n/runpm.ok" ]; then m="yes ($(head -c 40 "$ROOT/$n/runpm.ok" 2>/dev/null | cut -d' ' -f1,2))"; elif [ -e "$ROOT/$n/disk.qcow2" ]; then m="NO (accendi will check it first)"; else m="no disk"; fi
    echo "runpm marker $n: $m"
  done;;
*) echo "$USAGE"; exit 2;;
esac
