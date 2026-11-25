#!/bin/bash
# vm-radeon.sh - real-system test VMs for Debian 13 "trixie" (the live ISO's system installed "for real" on a virtual disk, UEFI, KVM), the server's Radeon passed through (vfio-pci) on demand.
# Usage: vm-radeon.sh crea|accendi|spegni|ssh|stato|prova-avvio <gnome|kde|xfce|lxqt> [cmd...]
#        vm-radeon.sh accendi <name> virtuale              (no Radeon: virtual video card, same ports)
#        vm-radeon.sh schermo <name> <file.png>            (screendump of a VM started with "virtuale")
#        vm-radeon.sh tasti <name> <key> [key...]          (QEMU sendkey names: ret, tab, ctrl-alt-f2, shift-a ...)
#        vm-radeon.sh scrivi <name> <text>                 (types the text through sendkey; "\n" in the text = Enter)
#        vm-radeon.sh istantanea|ripristina <name> <label> (qcow2 snapshot of the disk; VM must be off)
#   crea      builds the disk from the ISO's live/filesystem.squashfs the way Calamares installs it (see build_debian below), with the kernel of the
#             distribution (never the host's), then boots it ONCE with a virtual video card, checks it and powers it off.
#   accendi   Radeon (03:00.0 + 03:00.1 bound to vfio-pci) as the only video card, 12G of RAM, serial console in serial.log, no autologin.
#   accendi <name> virtuale   no Radeon, virtio-vga, 5G, no window; stays on until spegni.  Several virtual VMs may run together; the Radeon only in one.
#   prova-avvio  boot check WITHOUT the Radeon (virtual card, ssh on port+100, no REMOTIX forward): prints facts, then powers off (--resta: leave it on)
#   spegni    poweroff via ssh (then ACPI powerdown, then kill as a declared last resort), wait for the process to be really gone, and only then
#             give the Radeon back to the host (03:00.1 -> snd_hda_intel; 03:00.0 stays driverless as at boot) - only if THIS VM held it
#   istantanea  qemu-img snapshot -c (VM off).   ripristina  qemu-img snapshot -a: the CURRENT disk state is discarded (VM off, explicit command only)
# The Radeon is ONE for the whole server: accendi refuses if any VM under $ROOT, or ANY other qemu of the server (Fedora or Ubuntu bench), already has it;
# gpu_take/gpu_give check it too, and stato shows it.
# Everything lives in /media/REMOTIX-DEBIAN/vm-radeon/<desktop>/: disk.qcow2, OVMF_VARS.fd, vmkey, vm.pid, serial.log, monitor.sock.
# Host ports (LAN-reachable): ssh 2361-2364 -> guest 22; REMOTIX 8861-8864 tcp+udp -> guest 7447 (gnome, kde, xfce, lxqt in this order).
# Login: prova / prova2 (password prova2026, prova is in sudo), or key vmkey.  Clean machines: NO REMOTIX inside.
# Deletes nothing of anyone's: crea refuses to touch an existing disk.  The ONLY files this script removes or overwrites are its own:
#   build/disk.raw (crea's temporary raw image: removed after the qcow2 exists, or as a leftover of a failed crea before a new build, only if nothing is
#   mounted under build/ and no loop device uses it), build/ (its mount points, rmdir only), disk.qcow2.new (rewritten by a new crea after a failed one;
#   disk.qcow2 itself never), schermo.png (schermo's temporary), serial.log (emptied at every start), vm.pid and monitor.sock (rewritten by qemu at every start).
# Never touches /media/DOWNLOAD (the ISOs are only mounted read-only).  Kills a VM only as a declared last resort in spegni.  Must run as a user that can sudo.
set -euo pipefail
SELF=$(readlink -f "$0")
ROOT=/media/REMOTIX-DEBIAN/vm-radeon
ISODIR=/media/DOWNLOAD
GPU=0000:03:00.0 GPUA=0000:03:00.1
CPUS=4 MEM=${RX_VM_MEM:-5G} DISKSZ=40G
CODE=/usr/share/OVMF/OVMF_CODE_4M.fd VARS0=/usr/share/OVMF/OVMF_VARS_4M.fd
USAGE="usage: $0 crea|accendi|spegni|ssh|stato|prova-avvio gnome|kde|xfce|lxqt [cmd|virtuale]; $0 schermo <name> <file.png>; $0 tasti <name> <key>...; $0 scrivi <name> <text>; $0 istantanea|ripristina <name> <label>"

# desktop table: iso, ssh port, REMOTIX port, expected display manager (only reported, never configured)
case "${2:-}" in
gnome) ISO=$ISODIR/debian-live-13.8.0-amd64-gnome.iso SSHP=2361 RXP=8861 DM=gdm3;;
kde)   ISO=$ISODIR/debian-live-13.8.0-amd64-kde.iso   SSHP=2362 RXP=8862 DM=sddm;;
xfce)  ISO=$ISODIR/debian-live-13.8.0-amd64-xfce.iso  SSHP=2363 RXP=8863 DM=lightdm;;
lxqt)  ISO=$ISODIR/debian-live-13.8.0-amd64-lxqt.iso  SSHP=2364 RXP=8864 DM=sddm;;
*) echo "$USAGE"; exit 2;;
esac
NAME=$2
D=$ROOT/$NAME
DISK=$D/disk.qcow2 VARS=$D/OVMF_VARS.fd PID=$D/vm.pid SER=$D/serial.log MON=$D/monitor.sock
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
lock_wait() { mkdir -p "$ROOT"; exec 9>"$ROOT/.lock"; flock -w 2400 9 || die "the lock stayed taken for 40 min: the disk is built, only the first boot is missing (run prova-avvio $NAME, then the grub step by hand: vm-radeon.sh ssh $NAME \"echo $PASS | sudo -S grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=debian && echo $PASS | sudo -S update-grub\")"; }
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

# gpu_user: any qemu of the server (this bench or not, e.g. the Ubuntu bench) that has the Radeon in its command line: prints its pid and name
gpu_user() { ps -eo pid=,args= | grep -E "qemu-system.*host=$GPU" | grep -v grep | cut -c1-80 || true; }
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
# wait_ssh <n>: up to n*3 s for ssh as prova
wait_ssh() { local i; for i in $(seq "$1"); do sshv true 2>/dev/null && return 0; sleep 3; done; return 1; }


# build_debian (runs as root, via the hidden subcommand _build): the disk, the way Calamares installs a Debian live ISO.
# What the ISO's own installer (calamares-settings-debian 13, /etc/calamares in the image) does and is reproduced here: unpackfs of
# live/filesystem.squashfs, fstab with UUIDs, hostname, machine-id, locale/keyboard/timezone, users, removal of the live packages (live-*, calamares*),
# initramfs, grub-efi.  The kernel is the one inside the image (linux-image-amd64 of trixie), then updated by apt.
# DEVIATIONS (deliberate, owner's brief): users prova/prova2 with a fixed password and an ssh key; root has no password; openssh-server added; kernel command
# line has console=tty0 console=ttyS0,115200; GPT with a 512M EFI partition + one ext4 root (no swap); NVRAM of the server never written; the VM's own OVMF_VARS.fd gets a
# boot entry at first boot (the chroot installs grub with --no-nvram and --removable, first_boot runs grub-install again inside the VM); GRUB_DISABLE_OS_PROBER=true (the chroot sees
# the SERVER's /dev); the system is brought up to date (apt full-upgrade) and has the AMD firmware (firmware-amd-graphics, non-free-firmware).
build_debian() {
  B=$D/build RAW=$D/build/disk.raw
  mkdir -p "$B/root" "$B/iso" "$B/sq"; T=$B/root ISOM=$B/iso SQ=$B/sq; LOOPE= LOOPR=
  cleanup() {
    set +e; cd /
    local m l i
    for m in "$T/sys/firmware/efi/efivars" "$T$RAW" "$T/run" "$T/dev/pts" "$T/dev" "$T/proc" "$T/sys" "$T/boot/efi" "$T" "$SQ" "$ISOM"; do
      for i in $(seq 20); do mountpoint -q "$m" || break; umount "$m" 2>/dev/null || sleep 1; done
      mountpoint -q "$m" && echo "WARNING: $m is still mounted"
    done
    for l in ${LOOPE:-} ${LOOPR:-}; do losetup -d "$l"; done
  }
  if mount | grep -F " $B/" >/dev/null; then die "something under $B is still mounted (a failed crea?): not touching $RAW, look at it by hand"; fi
  [ -z "$(losetup -j "$RAW" 2>/dev/null)" ] || die "a loop device still uses $RAW: not touching it, look at it by hand"
  trap cleanup EXIT
  rm -f "$RAW"
  truncate -s $DISKSZ "$RAW"
  sgdisk -o -n1:0:+512M -t1:ef00 -c1:EFI -n2:0:0 -t2:8300 -c2:root "$RAW" >/dev/null
  # this server gives no partition nodes for loop devices: one loop device per partition, by offset (no udev, no partx)
  po() { sgdisk -i "$1" "$RAW" | awk -v k="$2" '$0 ~ k {print $3}'; }   # po <part> <"First sector"|"Last sector">
  lo() { losetup --find --show -o $(($(po $1 "First sector")*512)) --sizelimit $((($(po $1 "Last sector")-$(po $1 "First sector")+1)*512)) "$RAW"; }
  LOOPE=$(lo 1); LOOPR=$(lo 2)
  mkfs.vfat -F32 -n EFI "$LOOPE" >/dev/null; mkfs.ext4 -q -L rx-root "$LOOPR"
  mount "$LOOPR" "$T"; mkdir -p "$T/boot/efi"; mount "$LOOPE" "$T/boot/efi"
  mount -o loop,ro "$ISO" "$ISOM"
  [ -f "$ISOM/live/filesystem.squashfs" ] || die "no live/filesystem.squashfs in $ISO"
  mount -t squashfs -o loop,ro "$ISOM/live/filesystem.squashfs" "$SQ"
  echo "[$(date +%T)] unpacking the image (rsync) ..."
  rsync -aHAX --numeric-ids --exclude='/boot/efi/*' "$SQ/" "$T/" > "$B/rsync.log" 2>&1 || { tail -20 "$B/rsync.log"; die "rsync of the image failed (log: $B/rsync.log)"; }
  umount "$SQ"
  mkdir -p "$T/dev" "$T/proc" "$T/sys" "$T/run" "$T/tmp" "$T/root"
  # the image is untrusted for what is written from OUTSIDE the chroot: these must be real directories / files, not symlinks to the server
  for m in dev proc sys run tmp root etc/resolv.conf; do [ ! -L "$T/$m" ] || die "$T/$m in the image is a symlink: stopping"; done
  KVER=$(ls "$T/lib/modules" | sort -V | tail -1); echo "kernel in the image: $KVER"
  [ -e "$T/boot/vmlinuz-$KVER" ] || die "no /boot/vmlinuz-$KVER in the image"
  UUR=$(blkid -s UUID -o value "$LOOPR"); UUE=$(blkid -s UUID -o value "$LOOPE")
  install -d -m 700 "$T/root/.rxbuild"
  cp "$D/vmkey.pub" "$T/root/.rxbuild/vmkey.pub"
  printf 'UUR=%s\nUUE=%s\nNAME=%s\nPASS=%s\n' "$UUR" "$UUE" "$NAME" "$PASS" > "$T/root/.rxbuild/env"
  # DNS for apt inside the chroot: the host's non-loopback name servers (the image's resolv.conf is an empty plain file; NetworkManager rewrites it)
  { grep -E '^nameserver +[0-9a-f.:]+' /etc/resolv.conf | grep -vE '127\.|::1' || echo "nameserver 1.1.1.1"; } > "$T/etc/resolv.conf"
  # chroot mounts as Calamares' mount module has them (no efivars: the server's NVRAM is never touched)
  mount --bind /dev "$T/dev"; mount -t devpts devpts "$T/dev/pts"; mount -t proc proc "$T/proc"; mount -t sysfs sys "$T/sys"; mount -t tmpfs tmpfs "$T/run"
  # grub-probe (update-grub) needs the backing file of the loop device to exist at the same path INSIDE the chroot: the raw image is bind-mounted there
  # (empty placeholder file; removed after the stage).  grub-install may also mount efivarfs under /sys: unmounted first in cleanup (NVRAM never written: --no-nvram).
  mkdir -p "$T$B"; : > "$T$RAW"; mount --bind "$RAW" "$T$RAW"
  # (every write into the image's /etc, /usr, /var, /boot is made by the stage below, INSIDE the chroot: an absolute symlink in the image can never point at the server)
  cat > "$T/root/.rxbuild/stage.sh" <<'S'
set -eu
export DEBIAN_FRONTEND=noninteractive LC_ALL=C
. /root/.rxbuild/env
log() { echo "[chroot $(date +%T)] $*"; }
printf 'UUID=%s / ext4 errors=remount-ro 0 1\nUUID=%s /boot/efi vfat umask=0077 0 1\n' "$UUR" "$UUE" > /etc/fstab
# --- localization, keyboard, network name (same values as the Fedora VMs: en_US.UTF-8, "us" pc105, Europe/Rome)
echo "rx-deb-$NAME" > /etc/hostname
sed -i '/^127\.0\.1\.1/d' /etc/hosts; echo "127.0.1.1 rx-deb-$NAME" >> /etc/hosts
printf 'LANG=en_US.UTF-8\n' > /etc/default/locale
echo Europe/Rome > /etc/timezone; ln -sf /usr/share/zoneinfo/Europe/Rome /etc/localtime
printf 'XKBMODEL="pc105"\nXKBLAYOUT="us"\nXKBVARIANT=""\nXKBOPTIONS=""\n\nBACKSPACE="guess"\n' > /etc/default/keyboard
[ -e /etc/locale.gen ] && sed -i 's/^# *\(en_US.UTF-8 UTF-8\)/\1/' /etc/locale.gen && locale-gen en_US.UTF-8 >/dev/null 2>&1 || true
rm -f /etc/machine-id; systemd-machine-id-setup; mkdir -p /var/lib/dbus; ln -sf /etc/machine-id /var/lib/dbus/machine-id
printf '#!/bin/sh\nexit 101\n' > /usr/sbin/policy-rc.d; chmod +x /usr/sbin/policy-rc.d   # no services started in the chroot; removed at the end
# --- the installer's own removals (calamares-settings-debian packages.conf): the live system and the installer
P=$(dpkg-query -W -f '${Package}\n' | grep -E '^live-|^calamares|^libcalamares' || true)
if [ -n "$P" ]; then log "purging: $(echo $P)"; apt-get -q -y --purge remove $P; fi
# --- apt sources: the image has a "file:/run/live/medium" line (live medium) and a src line: replaced by the plain archives, with non-free-firmware
cat > /etc/apt/sources.list <<'A'
deb http://deb.debian.org/debian trixie main non-free-firmware
deb http://deb.debian.org/debian trixie-updates main non-free-firmware
deb http://security.debian.org/debian-security trixie-security main non-free-firmware
A
log "apt update + installs"
apt-get -q update
apt-get -q -y install sudo openssh-server firmware-amd-graphics grub-efi-amd64 shim-signed
log "apt full-upgrade"
apt-get -q -y full-upgrade
# --- users: Debian's usual desktop groups; sudo for prova only; root keeps no password
G=""; for g in cdrom floppy audio dip video plugdev users netdev bluetooth lpadmin scanner; do getent group $g >/dev/null && G="$G,$g"; done; G=${G#,}
useradd -m -s /bin/bash -G "$G,sudo" -c prova prova
useradd -m -s /bin/bash -G "$G" -c prova2 prova2
echo "prova:$PASS" | chpasswd; echo "prova2:$PASS" | chpasswd
install -d -m 700 -o prova -g prova /home/prova/.ssh
install -m 600 -o prova -g prova /root/.rxbuild/vmkey.pub /home/prova/.ssh/authorized_keys
systemctl enable ssh.service
# --- bootloader: serial console too; no os-prober; initramfs for THIS root, then grub without NVRAM writes
mkdir -p /etc/default/grub.d
printf 'GRUB_CMDLINE_LINUX="$GRUB_CMDLINE_LINUX console=tty0 console=ttyS0,115200"\nGRUB_DISABLE_OS_PROBER=true\n' > /etc/default/grub.d/99-vm-serial.cfg
update-initramfs -u -k all
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=debian --no-nvram
grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=debian --no-nvram --removable
# grub-probe in this chroot (loop device with an offset, no partition nodes) cannot tell grub which disk it is on: the EFI stubs and a first grub.cfg are
# written here from the UUIDs, and first_boot runs grub-install + update-grub INSIDE the running VM, where the disk is a real one
KV=$(ls /boot/vmlinuz-* | sort -V | tail -1); KV=${KV#/boot/vmlinuz-}
for d in /boot/efi/EFI/debian /boot/efi/EFI/BOOT; do
  mkdir -p $d
  printf 'search.fs_uuid %s root\nset prefix=($root)/boot/grub\nconfigfile $prefix/grub.cfg\n' "$UUR" > $d/grub.cfg
done
printf "set default=0\nset timeout=5\nmenuentry 'Debian GNU/Linux' {\n  search --no-floppy --fs-uuid --set=root %s\n  linux /boot/vmlinuz-%s root=UUID=%s ro quiet console=tty0 console=ttyS0,115200\n  initrd /boot/initrd.img-%s\n}\n" "$UUR" "$KV" "$UUR" "$KV" > /boot/grub/grub.cfg
apt-get clean
: > /etc/resolv.conf; rm -f /usr/sbin/policy-rc.d
log "stage done"
S
  echo "[$(date +%T)] chroot stage ..."
  chroot "$T" /bin/bash /root/.rxbuild/stage.sh
  rm -rf "$T/root/.rxbuild"
  umount "$T/sys/firmware/efi/efivars" 2>/dev/null || true; umount "$T$RAW"; rm -f "$T$RAW"; rmdir "$T$B" "$T$D" "$T$ROOT" "$T/media/REMOTIX-DEBIAN" 2>/dev/null || true
  # checks before the disk is declared good
  grep -q "root=UUID=$UUR" "$T/boot/grub/grub.cfg" || die "grub.cfg does not boot root=UUID=$UUR"
  ls "$T"/boot/vmlinuz-* "$T"/boot/initrd.img-* | sed 's/^/    /'
  [ -e "$T/boot/efi/EFI/BOOT/BOOTX64.EFI" ] || die "no fallback EFI loader (EFI/BOOT/BOOTX64.EFI)"
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
  rmdir "$T" "$ISOM" "$SQ" "$B" 2>/dev/null || true
  echo "disk built: $DISK"
}

# first_boot: crea's last step.  One boot WITHOUT the Radeon (virtual card; ssh on SSHP+100), checked, then powered off.  Caller holds the lock.
first_boot() {
  running && die "VM $NAME is running already: not starting a second qemu on its disk"
  SSHP=$((SSHP+100)); FWD=""
  sx sh -c ': > "$1"' _ "$SER"
  sx qemu-system-x86_64 $(base_args) -device virtio-vga 9>&- || die "qemu did not start for the first boot"
  sx chmod 644 "$SER" "$PID" 2>/dev/null || true
  running || die "qemu is not running after the start (see $SER)"
  echo "[$(date +%T)] first boot ..."
  wait_ssh 100 || { echo "first boot: ssh not answering in 5 min (see $SER): VM left running, look at it; the grub step by hand: $0 ssh $NAME \"echo $PASS | sudo -S grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=debian && echo $PASS | sudo -S update-grub\""; exit 1; }
  local st
  st=$(sshv "timeout 300 systemctl is-system-running --wait" 2>&1 || true)
  echo "first boot: is-system-running=$st  display-manager: $(sshv "readlink /etc/systemd/system/display-manager.service; systemctl is-active $DM" 2>&1 | tr '\n' ' ')"
  # the real grub configuration, made where the disk is a real one (this writes only the VM's own OVMF_VARS.fd): checked
  echo "first boot: grub: $(sshv "echo $PASS | sudo -S -p '' sh -c 'grub-install --target=x86_64-efi --efi-directory=/boot/efi --bootloader-id=debian >/dev/null 2>&1 && update-grub >/dev/null 2>&1; echo update-grub rc=\$?; grep -c root=UUID /boot/grub/grub.cfg'" 2>&1 | tr '\n' ' ')"
  stop_vm; echo "first boot: VM stopped"
  echo "first boot done"
}

case "${1:-}" in
_build) [ "$(id -u)" = 0 ] || die "_build is internal (called by crea as root)"
  [ -f "$DISK" ] && die "disk exists ($DISK): not touching it"
  build_debian;;
crea)
  lock
  [ -f "$DISK" ] && die "disk exists ($DISK): not touching it"
  [ -f "$ISO" ] || die "missing $ISO"
  mkdir -p "$D"; cd "$D"
  # per-VM lock: two crea of DIFFERENT VMs may build at the same time; the global lock is only held for the checks and for the first boot
  exec 8>"$D/.crea.lock"; flock -n 8 || die "crea of $NAME is already running"
  exec 9>&-
  [ -f vmkey ] || ssh-keygen -q -t ed25519 -N "" -f vmkey
  [ -f "$VARS" ] || cp $VARS0 "$VARS"
  T0=$(date +%s)
  echo "[$(date +%T)] building $NAME from $ISO (log: this output) ..."
  sx env "$SELF" _build $NAME 8>&-
  echo "[$(date +%T)] build took $(( $(date +%s)-T0 )) s"
  lock_wait
  first_boot
  echo "crea $NAME finished in $(( $(date +%s)-T0 )) s: next, accendi $NAME [virtuale]";;
accendi)
  lock
  if running; then   # already on: say whether it is in the mode asked for; nothing is changed either way
    case $CMD in *"host=$GPU"*) HAVE=radeon;; *) HAVE=virtual;; esac
    if [ "${3:-}" = virtuale ]; then WANT=virtual; else WANT=radeon; fi
    if [ "$HAVE" = "$WANT" ]; then
      [ "$HAVE" = radeon ] && echo "already running with the Radeon (pid $PIDV)" || echo "already running, virtual (pid $PIDV)"; exit 0
    fi
    die "running in the other mode ($HAVE, you asked for $WANT; pid $PIDV): spegni first"
  fi
  [ -f "$DISK" ] || die "no disk: run crea first"
  if [ "${3:-}" = virtuale ]; then
    # no Radeon: virtio-vga, no window; the monitor allows screendump and sendkey (schermo, tasti)
    sx sh -c ': > "$1"' _ "$SER"
    sx qemu-system-x86_64 $(base_args) -device virtio-vga 9>&- || die "qemu did not start"
    sx chmod 644 "$SER" "$PID" 2>/dev/null || true
    wait_ssh 120 && { echo "up, virtual video (ssh -p $SSHP; REMOTIX https://<server>:$RXP)"; exit 0; }
    echo "started but ssh not answering yet (see $SER)"; exit 1
  fi
  OWN=$(gpu_owner)
  [ -z "$OWN" ] || die "Radeon in use by VM $OWN: stop it first (or start this one with: $0 accendi $NAME virtuale)"
  [ -d /sys/bus/pci/devices/$GPU ] || die "$GPU not present"
  gpu_take
  MEMV=${RX_VM_MEM:-12G}   # the Radeon VM gets 12G (virtual ones 5G)
  sx sh -c ': > "$1"' _ "$SER"
  # Radeon as the only video card: on a root port, both functions, with its own ROM
  if ! sx qemu-system-x86_64 $(base_args) -device pcie-root-port,id=rp1,chassis=1,slot=1 \
      -device vfio-pci,host=$GPU,bus=rp1,addr=0.0,multifunction=on -device vfio-pci,host=$GPUA,bus=rp1,addr=0.1 9>&-; then
    echo "qemu did not start: giving the Radeon back"; gpu_give; exit 1
  fi
  sx chmod 644 "$SER" "$PID" 2>/dev/null || true
  wait_ssh 120 && { echo "up (ssh -p $SSHP; REMOTIX https://<server>:$RXP)"; exit 0; }
  echo "started but ssh not answering yet (see $SER)"; exit 1;;
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
  # boot check WITHOUT the Radeon: virtual video card, 4 CPUs, ssh on SSHP+100, no REMOTIX forward.  Not the final configuration.
  lock
  running && die "VM $NAME is running already"
  [ -f "$DISK" ] || die "no disk: run crea first"
  SSHP=$((SSHP+100)); FWD=""
  sx sh -c ': > "$1"' _ "$SER"
  sx qemu-system-x86_64 $(base_args) -device virtio-vga 9>&- || die "qemu did not start"
  sx chmod 644 "$SER" "$PID" 2>/dev/null || true
  wait_ssh 100 || true
  running || die "qemu is not running (see $SER)"
  sshv true 2>/dev/null || { echo "ssh not answering in 300 s (see $SER): stopping the VM"; stop_vm; exit 1; }
  if [ "${3:-}" = --resta ]; then echo "VM $NAME left running without the Radeon: ssh -p $SSHP (key $D/vmkey); stop it with: $0 spegni $NAME"; exit 0; fi
  sleep 20   # let the display manager come up
  sshv "echo -n 'uname -r: '; uname -r; echo -n 'display-manager ($DM): '; systemctl is-active $DM; readlink /etc/systemd/system/display-manager.service; echo -n 'is-system-running: '; systemctl is-system-running; echo 'failed units:'; systemctl --failed --no-legend; echo 'loginctl list-sessions:'; loginctl list-sessions --no-legend; echo -n 'hostname: '; hostname; echo -n 'machine-id: '; cat /etc/machine-id; getent passwd prova prova2 | cut -d: -f1,6; id prova; id prova2; echo $PASS | sudo -S -p '' id -un; ls /dev/dri; echo 'versions:'; dpkg-query -W -f '\${Package} \${Version}\n' linux-image-amd64 systemd gnome-shell plasma-desktop xfce4-session lxqt-session labwc gdm3 sddm lightdm firmware-amd-graphics 2>/dev/null | grep -v ' \$'; echo 'labwc in the repositories:'; apt-cache policy labwc | head -3; echo 'lsmod amdgpu:'; lsmod | grep -c '^amdgpu' || true; echo 'archive reachable:'; curl -sI -m 15 http://deb.debian.org/debian/dists/trixie/Release | head -1" || true
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
    qemu-img snapshot -a "$3" "$DISK" && echo "restored '$3' (OVMF_VARS.fd is not part of the snapshot)"
  fi;;
stato) if running; then echo "running pid $PIDV"; else echo stopped; [ -e "$PID" ] && echo "(stale pid file ignored)"; fi
  echo "Radeon held by VM: $(gpu_owner | grep . || echo none)"
  echo "qemu of the server with the Radeon (any bench): $(gpu_user | grep . || echo none)"
  for d in $GPU $GPUA; do echo "$d: $(drv $d)"; done;;
*) echo "$USAGE"; exit 2;;
esac
