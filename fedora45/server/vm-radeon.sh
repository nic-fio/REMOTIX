#!/bin/bash
# vm-radeon.sh - real-system test VMs for Fedora 45 (live ISO installed "for real", UEFI, KVM), the server's Radeon passed through (vfio-pci) on demand.
# Usage: vm-radeon.sh crea|accendi|spegni|ssh|stato|prova-avvio <gnome|kde|xfce|lxqt|costruzione> [cmd...]   (costruzione: RPM build VM, virtual only, ssh 2355)
#        vm-radeon.sh accendi <name> virtuale              (no Radeon: virtual video card, same ports)
#        vm-radeon.sh schermo <name> <file.png>            (screendump of a VM started with "virtuale")
#        vm-radeon.sh tasti <name> <key> [key...]          (QEMU sendkey names: ret, tab, ctrl-alt-f2, shift-a ...)
#        vm-radeon.sh scrivi <name> <text>                 (types the text through sendkey; "\n" in the text = Enter)
#        vm-radeon.sh istantanea|ripristina <name> <label> (qcow2 snapshot of the disk; VM must be off)
#   crea      builds the disk from the ISO the way Anaconda's "live image" payload installs it (see build_fedora below), then boots it ONCE with a
#             virtual video card so that the SELinux relabel (/.autorelabel) and the first-boot UEFI entry happen, checks it and powers it off.
#   accendi   Radeon (03:00.0 + 03:00.1 bound to vfio-pci) as the only video card, serial console in serial.log, no autologin.
#   accendi <name> virtuale   no Radeon, virtio-vga, no window; stays on until spegni.  Several virtual VMs may run together; the Radeon only in one.
#   prova-avvio  boot check WITHOUT the Radeon (virtual card, ssh on port+100, no REMOTIX forward): prints facts, then powers off (--resta: leave it on)
#   spegni    poweroff via ssh (then ACPI powerdown, then kill as a declared last resort), wait for the process to be really gone, and only then
#             give the Radeon back to the host (03:00.1 -> snd_hda_intel; 03:00.0 stays driverless as at boot) - only if THIS VM held it
#   istantanea  qemu-img snapshot -c (VM off).   ripristina  qemu-img snapshot -a: the CURRENT disk state is discarded (VM off, explicit command only)
# The Radeon is ONE: accendi refuses if any VM under $ROOT, or ANY other qemu of the server (e.g. the Ubuntu bench), already has it; gpu_take/gpu_give too.
# Everything lives in /media/REMOTIX-FEDORA/vm-radeon/<desktop>/: disk.qcow2, OVMF_VARS.fd, vmkey, vm.pid, serial.log, monitor.sock.
# Host ports (LAN-reachable): ssh 2351-2354 -> guest 22; REMOTIX 8851-8854 tcp+udp -> guest 7447.  Login: prova / prova2 (password prova2026, prova is in wheel), or key vmkey.
# Deletes nothing of anyone's: crea refuses to touch an existing disk.  The ONLY files this script removes or overwrites are its own:
#   build/disk.raw (crea's temporary raw image: removed after the qcow2 exists, or as a leftover of a failed crea before a new build, only if nothing is
#   mounted under build/ and no loop device uses it), build/rsync.log and disk.qcow2.new (rewritten by a new crea after a failed one; disk.qcow2 itself never),
#   schermo.png (schermo's temporary), serial.log (emptied at every start), vm.pid and monitor.sock (rewritten by qemu at every start).
# Never touches /media/DOWNLOAD (the ISOs are only mounted read-only).  Kills a VM only as a declared last resort in spegni.  Must run as a user that can sudo.
set -euo pipefail
SELF=$(readlink -f "$0")
ROOT=/media/REMOTIX-FEDORA/vm-radeon
ISODIR=/media/DOWNLOAD
GPU=0000:03:00.0 GPUA=0000:03:00.1
CPUS=4 MEM=${RX_VM_MEM:-5G} DISKSZ=40G
CODE=/usr/share/OVMF/OVMF_CODE_4M.fd VARS0=/usr/share/OVMF/OVMF_VARS_4M.fd
USAGE="usage: $0 crea|accendi|spegni|ssh|stato|prova-avvio gnome|kde|xfce|lxqt|costruzione [cmd|virtuale]; $0 schermo <name> <file.png>; $0 tasti <name> <key>...; $0 scrivi <name> <text>; $0 istantanea|ripristina <name> <label>"

# desktop table: iso, ssh port, REMOTIX port, expected display manager (only reported, never configured)
case "${2:-}" in
gnome) ISO=$ISODIR/Fedora-Gnome-Live-45-1.4.x86_64.iso      SSHP=2351 RXP=8851 DM=gdm;;
kde)   ISO=$ISODIR/Fedora-KDE-Desktop-Live-45-1.4.x86_64.iso SSHP=2352 RXP=8852 DM=plasmalogin;;
xfce)  ISO=$ISODIR/Fedora-Xfce-Live-45-1.4.x86_64.iso        SSHP=2353 RXP=8853 DM=lightdm;;
lxqt)  ISO=$ISODIR/Fedora-LXQt-Live-45-1.4.x86_64.iso        SSHP=2354 RXP=8854 DM=sddm;;
# costruzione: the fifth VM, only to build REMOTIX's RPM (Xfce image, same build as the others); never with the Radeon, no REMOTIX port forward, 8 CPUs, 6G
costruzione) ISO=$ISODIR/Fedora-Xfce-Live-45-1.4.x86_64.iso SSHP=2355 RXP=0 DM=lightdm FWD="" CPUS=8 MEM=${RX_VM_MEM:-6G};;
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
lock_wait() { mkdir -p "$ROOT"; exec 9>"$ROOT/.lock"; flock -w 2400 9 || die "the lock stayed taken for 40 min: the disk is built, only the first boot is missing (run prova-avvio $NAME)"; }
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

# build_fedora (runs as root, via the hidden subcommand _build): the disk, the way Anaconda installs a Fedora live ISO.
# What was read in the image (pyanaconda of Fedora 45) and is reproduced here, in Anaconda's order:
#   storage      default Fedora layout: GPT, 600 MiB EFI (vfat, /boot/efi), 1 GiB /boot (ext4), btrfs with subvolumes root and home (zstd:1), no swap (zram)
#   payload      live_os/live_image InstallFromImageTask: rsync -pogAXtlHrDx of the erofs root image (LiveOS/squashfs.img), with Anaconda's excludes
#                (/dev /proc /tmp/* /sys /run, /boot/*rescue*, /boot/loader/, /boot/efi/, /etc/machine-id, /etc/machine-info); /boot/efi copied separately (-rx)
#   rescue       create_rescue_images: new machine-id (systemd-machine-id-setup), then kernel-install add (BLS entry, initramfs, rescue kernel)
#   bootloader   write_defaults (/etc/default/grub), grub2-editenv create, grub2-set-default, menu_auto_hide/boot_success, the EFI stub grub.cfg
#                (what gen_grub_cfgstub writes), create_bls_entries (kernel-install add, grub2-mkconfig), recreate_initrds (depmod + dracut -f)
#   SELinux      labels travel with rsync -X; a real install has labels on everything it creates, here the chroot cannot create labelled files, so
#                setfiles is tried in the chroot AND /.autorelabel is set (relabel at first boot: done by crea, before the first real use)
# Live-only things need no removal: liveuser, the livesys service, the installer icon (liveinst-setup) and initial-setup are created/started only when
# the kernel command line has rd.live.image (livesys.service: ConditionKernelCommandLine=rd.live.image); Anaconda removes nothing either.
# DEVIATIONS from a real installation (all deliberate, owner's brief): users prova/prova2 with a fixed password and an ssh key instead of the installer's user,
# root stays locked (Anaconda default); sshd enabled (Fedora Workstation has it off); hostname rx-<name>; kernel command line has console=tty0
# console=ttyS0,115200; initramfs built NOT host-only with the virtio drivers added (the chroot is not the machine it will run on; Anaconda's
# "image install" mode does the same: dracut -N); no efibootmgr (the server's NVRAM is never touched: shim's fallback creates the entry in the VM's own
# OVMF_VARS.fd at the first boot); /etc/kernel/cmdline of the image (a stale build-machine line) replaced by the right one; kde: /etc/plasma-setup-done
# so that Plasma Setup (the first-boot wizard that creates the user on a real KDE install) does not take the screen; no updates, no extra packages,
# firewall and everything else as the image has it; GRUB_DISABLE_OS_PROBER=true (grub2-mkconfig runs in a chroot that sees the SERVER's /dev: os-prober
# must not list the server's systems); keyboard: vconsole.conf and 00-keyboard.conf as read from pyanaconda (see the stage).
# NOT verified: the exact header comment and key order of the 00-keyboard.conf that systemd-localed writes (taken from the strings of systemd-localed 262,
# not from a run), and whether localed leaves XkbModel out when it is "pc105"; the file is equivalent for Xorg/localectl either way.
build_fedora() {
  B=$D/build RAW=$D/build/disk.raw
  mkdir -p "$B/root" "$B/iso" "$B/sq" "$B/top"; T=$B/root ISOM=$B/iso SQ=$B/sq TOP=$B/top; LOOPE= LOOPB= LOOPR=
  cleanup() {
    set +e; cd /
    local m l
    # (a process of the chroot stage may take a moment to let go of /dev: each unmount is retried for up to 20 s before giving up)
    for m in "$T/run" "$T/dev/pts" "$T/dev" "$T/proc" "$T/sys" "$T/boot/efi" "$T/boot" "$T/home" "$T" "$TOP" "$SQ" "$ISOM"; do
      for i in $(seq 20); do mountpoint -q "$m" || break; umount "$m" 2>/dev/null || sleep 1; done
      mountpoint -q "$m" && echo "WARNING: $m is still mounted"
    done
    for l in ${LOOPE:-} ${LOOPB:-} ${LOOPR:-}; do losetup -d "$l"; done
  }
  # a leftover raw image of an earlier failed crea (this script's own temporary; $DISK does not exist, checked by the caller) is replaced, but only
  # if nothing is mounted under $B and no loop device uses it
  if mount | grep -F " $B/" >/dev/null; then die "something under $B is still mounted (a failed crea?): not touching $RAW, look at it by hand"; fi
  [ -z "$(losetup -j "$RAW" 2>/dev/null)" ] || die "a loop device still uses $RAW: not touching it, look at it by hand"
  trap cleanup EXIT
  rm -f "$RAW"
  truncate -s $DISKSZ "$RAW"
  sgdisk -o -n1:0:+600M -t1:ef00 -c1:"EFI System Partition" -n2:0:+1G -t2:8300 -c2:boot -n3:0:0 -t3:8300 -c3:fedora "$RAW" >/dev/null
  # this server gives no partition nodes for loop devices: one loop device per partition, by offset (no udev, no partx)
  po() { sgdisk -i "$1" "$RAW" | awk -v k="$2" '$0 ~ k {print $3}'; }   # po <part> <"First sector"|"Last sector">
  lo() { losetup --find --show -o $(($(po $1 "First sector")*512)) --sizelimit $((($(po $1 "Last sector")-$(po $1 "First sector")+1)*512)) "$RAW"; }
  LOOPE=$(lo 1); LOOPB=$(lo 2); LOOPR=$(lo 3)
  mkfs.vfat -F32 "$LOOPE" >/dev/null; mkfs.ext4 -q "$LOOPB"; mkfs.btrfs -q -L fedora "$LOOPR"
  mount "$LOOPR" "$TOP"; btrfs -q subvolume create "$TOP/root"; btrfs -q subvolume create "$TOP/home"; umount "$TOP"
  mount -o subvol=root,compress=zstd:1 "$LOOPR" "$T"; mkdir -p "$T/home" "$T/boot"
  mount -o subvol=home,compress=zstd:1 "$LOOPR" "$T/home"
  mount "$LOOPB" "$T/boot"; mkdir -p "$T/boot/efi"; mount -o umask=0077,shortname=winnt "$LOOPE" "$T/boot/efi"
  mount -o loop,ro "$ISO" "$ISOM"
  [ -f "$ISOM/LiveOS/squashfs.img" ] || die "no LiveOS/squashfs.img in $ISO"
  mount -t erofs -o loop,ro "$ISOM/LiveOS/squashfs.img" "$SQ"   # (not squashfs: the Fedora 45 live image is erofs and holds the root directly)
  echo "[$(date +%T)] copying the image (rsync, as Anaconda) ..."
  rsync -pogAXtlHrDx --numeric-ids --stats --exclude /dev/ --exclude /proc/ --exclude '/tmp/*' --exclude /sys/ --exclude /run/ \
    --exclude '/boot/*rescue*' --exclude /boot/loader/ --exclude /boot/efi/ --exclude /etc/machine-id --exclude /etc/machine-info "$SQ/" "$T/" > "$B/rsync.log" 2>&1 \
    || { tail -20 "$B/rsync.log"; die "rsync of the image failed (log: $B/rsync.log)"; }
  grep -E "Number of regular files transferred|Total transferred file size" "$B/rsync.log" || true
  # /boot/efi is a FAT file system: no permissions, owners, xattrs (as Anaconda copies it)
  rsync -rx --exclude /boot/efi/loader/ "$SQ/boot/efi/" "$T/boot/efi/"
  # mount points that Anaconda's excludes leave out (it has them as its own bind mounts)
  mkdir -p "$T/dev" "$T/proc" "$T/sys" "$T/run" "$T/tmp"
  # the image is untrusted for what is written from OUTSIDE the chroot: these directories must be real directories, not symlinks to the server
  for m in dev proc sys run tmp root; do [ -d "$T/$m" ] && [ ! -L "$T/$m" ] || die "$T/$m in the image is not a plain directory: stopping"; done
  chmod 755 "$T/dev" "$T/proc" "$T/sys" "$T/run"; chmod 1777 "$T/tmp"
  KVER=$(ls "$T/usr/lib/modules" | sort -V | tail -1); echo "kernel in the image: $KVER"
  [ -e "$T/usr/lib/modules/$KVER/vmlinuz" ] || die "no kernel under /usr/lib/modules/$KVER in the image"
  UUB=$(blkid -s UUID -o value "$LOOPB"); UUE=$(blkid -s UUID -o value "$LOOPE"); UUR=$(blkid -s UUID -o value "$LOOPR")
  install -d -m 700 "$T/root/.rxbuild"
  cp "$D/vmkey.pub" "$T/root/.rxbuild/vmkey.pub"
  printf 'UUR=%s\nUUB=%s\nUUE=%s\nKVER=%s\nNAME=%s\nPASS=%s\n' "$UUR" "$UUB" "$UUE" "$KVER" "$NAME" "$PASS" > "$T/root/.rxbuild/env"
  # chroot mounts as Anaconda's installation environment has them (no efivars: the server's NVRAM is never touched)
  mount --bind /dev "$T/dev"; mount -t devpts devpts "$T/dev/pts"; mount -t proc proc "$T/proc"; mount -t sysfs sys "$T/sys"
  mount -t tmpfs tmpfs "$T/run"
  # (every write into the image's /etc, /usr, /var, /boot... is made by the stage below, INSIDE the chroot: an absolute symlink in the image can never
  # point at the server.  Made from outside: the mount-point directories above and /root/.rxbuild, after checking they are not symlinks, and rsync itself.)
  cat > "$T/root/.rxbuild/stage.sh" <<'S'
set -eu
export LC_ALL=C
. /root/.rxbuild/env
log() { echo "[chroot $(date +%T)] $*"; }
# --- storage: fstab (as Anaconda writes it)
cat > /etc/fstab <<F
UUID=$UUR /                       btrfs   subvol=root,compress=zstd:1 0 0
UUID=$UUB /boot                   ext4    defaults        1 2
UUID=$UUE          /boot/efi               vfat    umask=0077,shortname=winnt 0 2
UUID=$UUR /home                   btrfs   subvol=home,compress=zstd:1 0 0
F
# --- localization and network name (Anaconda: language, keyboard, timezone, hostname)
echo "rx-$NAME" > /etc/hostname
echo 'LANG=en_US.UTF-8' > /etc/locale.conf
# keyboard, as pyanaconda (modules/localization/installation.py, Fedora 45) writes it for an "us" install:
#  - /etc/vconsole.conf: write_vc_configuration opens it with "w", so ONLY KEYMAP="us" and FONT="eurlatgr" (DEFAULT_VC_FONT) remain: the XKB* lines
#    that the image's own vconsole.conf had (XKBLAYOUT, XKBMODEL, XKBOPTIONS: left there by the live build's localed) are NOT carried over;
#  - /etc/X11/xorg.conf.d/00-keyboard.conf: generated by systemd-localed (SetX11Keyboard layouts="us", model="pc105", variant "", options "")
#    and copied into the target; empty variant/options are not written.  localectl status then shows VC Keymap us, X11 Layout us, X11 Model pc105.
printf 'KEYMAP="us"\nFONT="eurlatgr"\n' > /etc/vconsole.conf
mkdir -p /etc/X11/xorg.conf.d
cat > /etc/X11/xorg.conf.d/00-keyboard.conf <<K
# Written by systemd-localed(8), read by systemd-localed and Xorg. It's
# probably wise not to edit this file manually. Use localectl(1) to
# instruct systemd-localed to update it.
Section "InputClass"
        Identifier "system-keyboard"
        MatchIsKeyboard "on"
        Option "XkbLayout" "us"
        Option "XkbModel" "pc105"
EndSection
K
ln -sf ../usr/share/zoneinfo/Europe/Rome /etc/localtime
# --- users (root stays locked, as Anaconda leaves it without a root password)
useradd -m -G wheel -c prova prova
useradd -m -c prova2 prova2
echo "prova:$PASS" | chpasswd; echo "prova2:$PASS" | chpasswd
install -d -m 700 -o prova -g prova /home/prova/.ssh
install -m 600 -o prova -g prova /root/.rxbuild/vmkey.pub /home/prova/.ssh/authorized_keys
# --- services: sshd on (deviation); KDE: no Plasma Setup wizard (deviation)
systemctl enable sshd.service
[ "$(readlink /etc/systemd/system/display-manager.service)" != /usr/lib/systemd/system/plasmalogin.service ] || touch /etc/plasma-setup-done
# --- machine-id (create_rescue_images), kernel command line, dracut settings for a disk that is not the build machine
systemd-machine-id-setup
MID=$(cat /etc/machine-id)
# (grub2-mkconfig adds rootflags=subvol=root itself for a btrfs root: not repeated in GRUB_CMDLINE_LINUX)
CMDL="rhgb quiet console=tty0 console=ttyS0,115200"
echo "root=UUID=$UUR ro rootflags=subvol=root $CMDL" > /etc/kernel/cmdline
mkdir -p /etc/dracut.conf.d
printf 'hostonly="no"\nadd_drivers+=" virtio_blk virtio_pci virtio_scsi virtio_net btrfs "\n' > /etc/dracut.conf.d/99-rx-vm.conf
# --- bootloader defaults (grub2.py write_defaults) and grubenv
cat > /etc/default/grub <<G
GRUB_TIMEOUT=5
GRUB_DISTRIBUTOR="\$(sed 's, release .*\$,,g' /etc/system-release)"
GRUB_DEFAULT=saved
GRUB_DISABLE_SUBMENU=true
GRUB_TERMINAL_OUTPUT="console"
GRUB_CMDLINE_LINUX="$CMDL"
GRUB_DISABLE_RECOVERY="true"
GRUB_ENABLE_BLSCFG=true
GRUB_DISABLE_OS_PROBER=true
G
# --- BLS entries (create_bls_entries: old ones removed, kernel-install add) and initramfs (recreate_initrds)
rm -f /boot/loader/entries/*.conf
log "kernel-install add $KVER"
kernel-install add "$KVER" "/lib/modules/$KVER/vmlinuz"
log "depmod + dracut -f"
depmod -a "$KVER"
dracut -f "/boot/initramfs-$KVER.img" "$KVER"
rm -f /etc/dracut.conf.d/99-rx-vm.conf
# --- grubenv, default entry, menu_auto_hide (as the Fedora profiles set it), main config, EFI stub (gen_grub_cfgstub)
grub2-editenv - create
grub2-set-default "$MID-$KVER"
grub2-editenv - set menu_auto_hide=1 boot_success=1
log "grub2-mkconfig"
grub2-mkconfig -o /boot/grub2/grub.cfg
cat > /boot/efi/EFI/fedora/grub.cfg <<E
search --no-floppy --root-dev-only --fs-uuid --set=dev $UUB
set prefix=(\$dev)/grub2
export \$prefix
configfile \$prefix/grub.cfg
E
chmod 0600 /boot/efi/EFI/fedora/grub.cfg
# --- SELinux: label what this chroot created (best effort: the kernel here has no SELinux), plus relabel at first boot
touch /.autorelabel
log "setfiles (best effort)"
for m in / /boot /home; do
  setfiles -F -e /proc -e /sys -e /dev -e /run -e /boot/efi /etc/selinux/targeted/contexts/files/file_contexts "$m" 2>&1 | tail -3 || true
done
log "stage done"
S
  echo "[$(date +%T)] chroot stage ..."
  chroot "$T" /bin/bash /root/.rxbuild/stage.sh
  rm -rf "$T/root/.rxbuild"
  # checks before the disk is declared good
  ls "$T"/boot/loader/entries/*.conf >/dev/null || die "no BLS entry was written"
  grep -q "root=UUID=$UUR" "$T/boot/grub2/grub.cfg" "$T"/boot/loader/entries/*"$KVER".conf || die "root=UUID=$UUR is in neither grub.cfg nor the BLS entry"
  [ -s "$T/boot/initramfs-$KVER.img" ] || die "no initramfs-$KVER.img"
  echo "BLS entries:"; sed 's/^/    /' "$T"/boot/loader/entries/*"$KVER".conf
  cleanup; trap - EXIT; LOOPE= LOOPB= LOOPR=; set -e   # cleanup turned errexit off: back on, and the unmounts are CHECKED
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
  rmdir "$T" "$ISOM" "$SQ" "$TOP" "$B" 2>/dev/null || true
  echo "disk built: $DISK"
}

# first_boot: crea's last step.  One boot WITHOUT the Radeon (virtual card; ssh on SSHP+100): shim's fallback creates the UEFI entry (reboot),
# /.autorelabel relabels the disk (reboot), then the system comes up for good.  Checked, then powered off.  Caller holds the lock.
first_boot() {
  running && die "VM $NAME is running already: not starting a second qemu on its disk"
  SSHP=$((SSHP+100)); FWD=""
  sx sh -c ': > "$1"' _ "$SER"
  sx qemu-system-x86_64 $(base_args) -device virtio-vga 9>&- || die "qemu did not start for the first boot"
  sx chmod 644 "$SER" "$PID" 2>/dev/null || true
  running || die "qemu is not running after the start (see $SER)"
  echo "[$(date +%T)] first boot (UEFI entry + SELinux relabel, up to 15 min) ..."
  wait_ssh 300 || { echo "first boot: ssh not answering in 15 min (see $SER): VM left running, look at it"; exit 1; }
  local st enf rl
  st=$(sshv "timeout 300 systemctl is-system-running --wait" 2>&1 || true)
  enf=$(sshv getenforce 2>&1 || true); rl=$(sshv 'test -e /.autorelabel && echo STILL-THERE || echo gone' 2>&1 || true)
  echo "first boot: is-system-running=$st  getenforce=$enf  /.autorelabel $rl"
  stop_vm; echo "first boot: VM stopped"
  [ "$rl" = gone ] || die "FAIL: the SELinux relabel did not happen (/.autorelabel: $rl): the disk is NOT good"
  [ "$enf" = Enforcing ] || die "FAIL: getenforce says '$enf', not Enforcing: the disk is NOT good"
  echo "first boot done"
}

case "${1:-}" in
_build) [ "$(id -u)" = 0 ] || die "_build is internal (called by crea as root)"
  [ -f "$DISK" ] && die "disk exists ($DISK): not touching it"
  build_fedora;;
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
  [ "$NAME" != costruzione ] || die "costruzione is the RPM build VM: it never gets the Radeon (use: accendi costruzione virtuale)"
  OWN=$(gpu_owner)
  [ -z "$OWN" ] || die "Radeon in use by VM $OWN: stop it first (or start this one with: $0 accendi $NAME virtuale)"
  [ -d /sys/bus/pci/devices/$GPU ] || die "$GPU not present"
  gpu_take
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
  sshv "echo -n 'uname -r: '; uname -r; echo -n 'getenforce: '; getenforce; echo -n 'display-manager ($DM): '; systemctl is-active $DM; readlink /etc/systemd/system/display-manager.service; echo -n 'is-system-running: '; systemctl is-system-running; echo 'failed units:'; systemctl --failed --no-legend; echo 'loginctl list-sessions:'; loginctl list-sessions --no-legend; echo -n 'hostname: '; hostname; echo -n 'machine-id: '; cat /etc/machine-id; getent passwd prova prova2 liveuser | cut -d: -f1,6; id prova; echo $PASS | sudo -S -p '' id -un; ls /dev/dri" || true
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
