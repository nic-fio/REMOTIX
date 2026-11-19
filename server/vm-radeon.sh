#!/bin/bash
# vm-radeon.sh - real-system test VMs (desktop ISO installed for real, UEFI, KVM) with the server's Radeon passed through (vfio-pci).
# Usage: vm-radeon.sh crea|accendi|spegni|ssh|stato <ubuntu|kubuntu|xubuntu|lubuntu> [cmd...]   (ubuntu: autoinstall; the others: built from the ISO squashfs)
#        vm-radeon.sh istantanea|ripristina <name> <label>      (qcow2 snapshot of the disk; VM must be off)
#   crea    unattended install from the desktop ISO (autoinstall), with a temporary virtual video card; the VM powers itself off at the end
#   accendi bind the Radeon (03:00.0 + 03:00.1) to vfio-pci and start the VM: Radeon only, serial console in serial.log, no autologin
#   crea    (kubuntu, lubuntu: Calamares ISOs; xubuntu: its live kernel crashes the autoinstall) builds the disk from the ISO's squashfs layers the way Calamares would (unpackfs, fstab,
#           users, bootloader from the ISO pool, initramfs): GPT + EFI partition, Ubuntu kernel of the ISO, hostname, empty machine-id, users, ssh key
#   prova-avvio  boot check WITHOUT the Radeon (virtual card, 6 GB, ssh on port+100, no REMOTIX forward): prints facts, then powers off
#   spegni  poweroff via ssh (then ACPI powerdown, then kill as a declared last resort), wait for the process to be really gone, and only then
#           give the Radeon back to the host (03:00.1 -> snd_hda_intel; 03:00.0 stays driverless as at boot)
#   istantanea  qemu-img snapshot -c (VM off).   ripristina  qemu-img snapshot -a: the CURRENT disk state is discarded (VM off, explicit command only)
# The Radeon is ONE: accendi refuses if another VM under $ROOT already holds it.
# Everything lives in /media/REMOTIX-UBUNTU/vm-radeon/<desktop>/: disk.qcow2, OVMF_VARS.fd, seed.iso, vmkey, vm.pid, serial.log, monitor.sock.
# Host ports (LAN-reachable): ssh -> guest 22; REMOTIX tcp+udp -> guest 7447.  Login: prova / prova2 (password prova2026, prova has sudo), or key vmkey.
# Deletes nothing of anyone's: crea refuses to touch an existing disk; the ONLY thing removed is crea's own temporary raw image (build/disk.raw), after the qcow2 exists.  Kills a VM only as a declared last resort in spegni.  Must run as a user that can sudo (qemu and vfio need root).
set -euo pipefail
SELF=$(readlink -f "$0")
ROOT=/media/REMOTIX-UBUNTU/vm-radeon
ISODIR=/media/DOWNLOAD
GPU=0000:03:00.0 GPUA=0000:03:00.1
CPUS=8 MEM=12G DISKSZ=40G
CODE=/usr/share/OVMF/OVMF_CODE_4M.fd VARS0=/usr/share/OVMF/OVMF_VARS_4M.fd

# desktop table: iso, ssh port, REMOTIX port
case "${2:-}" in
ubuntu)  ISO=$ISODIR/ubuntu-26.04-desktop-amd64.iso SSHP=2341 RXP=8841 KIND=autoinstall;;
kubuntu) ISO=$ISODIR/kubuntu-26.04.1-desktop-amd64.iso SSHP=2342 RXP=8842 KIND=squashfs LAYERS="casper/filesystem.squashfs";;
xubuntu) ISO=$ISODIR/xubuntu-26.04-desktop-amd64.iso SSHP=2343 RXP=8843 KIND=squashfs LAYERS="casper/minimal.squashfs casper/minimal.standard.squashfs";;
lubuntu) ISO=$ISODIR/lubuntu-26.04-desktop-amd64.iso SSHP=2344 RXP=8844 KIND=squashfs LAYERS="casper/minimal.squashfs casper/minimal.standard.squashfs";;
*) echo "usage: $0 crea|accendi|spegni|ssh|stato|prova-avvio ubuntu|kubuntu|xubuntu|lubuntu [cmd]; $0 istantanea|ripristina <name> <label>"; exit 2;;
esac
NAME=$2
D=$ROOT/$NAME
DISK=$D/disk.qcow2 VARS=$D/OVMF_VARS.fd SEED=$D/seed.iso PID=$D/vm.pid SER=$D/serial.log MON=$D/monitor.sock
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
lock() { mkdir -p "$ROOT"; exec 9>"$ROOT/.lock"; flock -n 9 || die "another vm-radeon.sh holds the lock: a VM is being started or stopped, or a disk is being built or installed (crea can take 10 minutes): try again later"; }
mon() { sx python3 -c 'import socket,sys,time;s=socket.socket(socket.AF_UNIX);s.connect(sys.argv[1]);time.sleep(.3);s.sendall((sys.argv[2]+"\n").encode());time.sleep(1.5)' "$MON" "$1"; }
sysw() { sx sh -c 'echo "$1" > "$2"' _ "$2" "$1" 2>/dev/null || true; }   # sysfs writes: an unbind of an already-free device is not an error
drv() { basename "$(readlink /sys/bus/pci/devices/$1/driver 2>/dev/null)" 2>/dev/null || true; }
# wait_gone <n>: up to n*2 s for this VM's qemu to be really gone
wait_gone() { local i; for i in $(seq "$1"); do running || return 0; sleep 2; done; return 1; }

# stop_vm: ssh poweroff, then ACPI powerdown, then kill as a declared last resort; returns only when the process is really gone (else dies)
stop_vm() {
  local p=$PIDV q
  # a VM started by prova-avvio answers on another ssh port: take it from its own command line
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

# bind both Radeon functions to vfio-pci (03:00.1 is first taken away from snd_hda_intel).  Callers have already checked that no VM holds it.
gpu_take() {
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
    echo "unpacking $l ..."; rsync -aHAX --numeric-ids --exclude='/boot/efi/*' "$B/sq$n/" "$T/"
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
echo 'rx-$NAME' > /etc/hostname
sed -i '/^127\.0\.1\.1/d' /etc/hosts; echo '127.0.1.1 rx-$NAME' >> /etc/hosts
: > /etc/machine-id; mkdir -p /var/lib/dbus; ln -sf /etc/machine-id /var/lib/dbus/machine-id   # machineid: new id at first boot
printf 'LANG=en_US.UTF-8\n' > /etc/default/locale; echo Europe/Rome > /etc/timezone; ln -sf /usr/share/zoneinfo/Europe/Rome /etc/localtime
mkdir -p /etc/default/grub.d
printf 'GRUB_CMDLINE_LINUX="\$GRUB_CMDLINE_LINUX console=tty0 console=ttyS0,115200"\nGRUB_DISABLE_OS_PROBER=true\n' > /etc/default/grub.d/99-vm-serial.cfg
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
(locale-gen en_US.UTF-8 >/dev/null 2>&1 || true)
apt-get clean
rm -f /usr/sbin/policy-rc.d; rm -rf /tmp/cdsrc
S
  echo "chroot stage ..."
  chroot "$T" /bin/bash /root/.rxbuild/stage.sh
  rm -rf "$T/root/.rxbuild"; rmdir "$T/cdrom" 2>/dev/null || true
  grep -q "root=UUID=$UUR" "$T/boot/grub/grub.cfg" || { echo "grub.cfg does not boot root=UUID=$UUR"; exit 1; }
  cleanup; trap - EXIT; LOOPE= LOOPR=; set -e   # cleanup turned errexit off: back on, and the unmounts are CHECKED
  mountpoint -q "$T" && die "$T is still mounted: stopping, everything left as it is"
  if mount | grep -F " $B/" >/dev/null; then die "something under $B is still mounted: stopping, everything left as it is"; fi
  [ -z "$(losetup -j "$RAW")" ] || die "a loop device is still attached to $RAW: stopping, everything left as it is"
  echo "converting to qcow2 ..."
  qemu-img convert -O qcow2 "$RAW" "$DISK.new" || die "qemu-img convert failed: $RAW and $DISK.new left as they are"
  mv -n "$DISK.new" "$DISK"
  [ -f "$DISK.new" ] && die "disk appeared meanwhile: $DISK.new kept, $RAW kept"
  [ -f "$DISK" ] || die "$DISK does not exist: $RAW kept"
  chown --reference="$D" "$DISK" "$VARS" 2>/dev/null || true
  rm -f "$RAW"   # the only thing this script deletes: its own temporary raw image, and only now that $DISK exists
  rmdir "$B/root" "$B/iso" "$B" 2>/dev/null || true
  echo "disk built: $DISK"
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
  [ -f vmkey ] || ssh-keygen -q -t ed25519 -N "" -f vmkey
  if [ "$KIND" = squashfs ]; then
    case $NAME in
      kubuntu) RMCMD="apt-get -q -y --purge remove \$(dpkg-query -W -f '\${Package}\\n' | grep -E '^live|^(calamares-settings-kubuntu|calamares-settings-ubuntu-common|calamares-settings-ubuntu-common-data|calamares|calamares-data|libcalamaresui3.3|cifs-utils|kubuntu-installer-prompt)\$')";;
      *) RMCMD=true;;   # lubuntu, xubuntu: nothing to remove (the installer lives in the live layer / in a snap, not in the unpacked layers)
    esac
    [ -f "$VARS" ] || cp $VARS0 "$VARS"
    echo "building $NAME from the squashfs of $ISO (log: this output) ..."
    sx env RMCMD="$RMCMD" "$SELF" _build $NAME
    exit $?
  fi
  xorriso -osirrox on -indev "$ISO" -extract /casper/vmlinuz "$D/vmlinuz" -extract /casper/initrd "$D/initrd" 2>&1 | grep -iE "error|fail|cannot" || true
  [ -s "$D/vmlinuz" ] && [ -s "$D/initrd" ] || die "could not extract kernel/initrd from $ISO (casper/vmlinuz, casper/initrd)"
  HASH=$(openssl passwd -6 "$PASS")
  T=$(mktemp -d)
  printf 'instance-id: remotix-%s\nlocal-hostname: rx-%s\n' "$NAME" "$NAME" > "$T/meta-data"
  cat > "$T/user-data" <<U
#cloud-config
autoinstall:
  version: 1
  locale: en_US.UTF-8
  keyboard: {layout: us}
  timezone: Europe/Rome
  identity: {hostname: rx-$NAME, username: prova, password: "$HASH", realname: prova}
  storage: {layout: {name: direct}}
  refresh-installer: {update: false}
  updates: security
  shutdown: poweroff
  late-commands:
    - curtin in-target --target=/target -- apt-get install -y openssh-server
    - curtin in-target --target=/target -- sh -c "useradd -m -s /bin/bash -c prova2 prova2 && echo 'prova2:$PASS' | chpasswd"
    - curtin in-target --target=/target -- sh -c "install -d -m 700 -o prova -g prova /home/prova/.ssh && echo '$(cat vmkey.pub)' > /home/prova/.ssh/authorized_keys && chown prova:prova /home/prova/.ssh/authorized_keys && chmod 600 /home/prova/.ssh/authorized_keys"
    - curtin in-target --target=/target -- sh -c "printf 'GRUB_CMDLINE_LINUX=\"\$GRUB_CMDLINE_LINUX console=tty0 console=ttyS0,115200\"\n' > /etc/default/grub.d/99-vm-serial.cfg && update-grub"
U
  genisoimage -quiet -output "$SEED" -volid cidata -joliet -rock "$T/user-data" "$T/meta-data"; cp "$T/user-data" "$D/user-data.used"; rm -rf "$T"
  echo "installing $NAME (temporary virtual video card; installer console in $SER, up to 60 min) ..."
  # disk and UEFI variables are created last, right before QEMU.  Kernel and initrd come straight from the ISO so that 'autoinstall'
  # can be put on the command line without repacking it.
  qemu-img create -q -f qcow2 "$DISK" $DISKSZ; cp $VARS0 "$VARS"
  MEMV=6G
  sx qemu-system-x86_64 $(base_args) -device virtio-vga -cdrom "$ISO" -drive file="$SEED",if=virtio,format=raw,readonly=on \
    -kernel "$D/vmlinuz" -initrd "$D/initrd" -append "autoinstall quiet splash console=ttyS0,115200 ---" -no-reboot 9>&- \
    || die "qemu did not start: an EMPTY disk ($DISK) and $VARS were left behind: remove them by hand before running crea again"
  sx chmod 644 "$SER" "$PID" 2>/dev/null || true
  exec 9>&-   # the lock is only for the start: the installation takes a long time and must not block other VMs
  wait_gone 1800 || die "install still running after 60 min (pid $PIDV): NOT killed; look at $SER, or kill it by hand"
  # the installer powers the VM off only when it succeeded; as a second check the disk must hold an installed system
  SZ=$(stat -c %s "$DISK")
  [ "$SZ" -gt 4000000000 ] || die "VM stopped but the disk is only $SZ bytes: the install did not complete (see $SER)"
  echo "install finished (VM powered off, disk $SZ bytes): next, accendi $NAME";;
accendi)
  lock
  running && { echo "already running (pid $PIDV)"; exit 0; }
  [ -f "$DISK" ] || die "no disk: run crea first"
  OWN=$(gpu_owner)
  [ -z "$OWN" ] || die "Radeon in use by VM $OWN: stop it first"
  [ -d /sys/bus/pci/devices/$GPU ] || die "$GPU not present"
  gpu_take
  sx sh -c ': > "$1"' _ "$SER"
  # Radeon as the only video card: on a root port, both functions, with its own ROM
  if ! sx qemu-system-x86_64 $(base_args) -device pcie-root-port,id=rp1,chassis=1,slot=1 \
      -device vfio-pci,host=$GPU,bus=rp1,addr=0.0,multifunction=on -device vfio-pci,host=$GPUA,bus=rp1,addr=0.1 9>&-; then
    echo "qemu did not start: giving the Radeon back"; gpu_give; exit 1
  fi
  sx chmod 644 "$SER" "$PID" 2>/dev/null || true
  for i in $(seq 120); do sshv true 2>/dev/null && { echo "up (ssh -p $SSHP; REMOTIX https://<server>:$RXP)"; exit 0; }; sleep 3; done
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
  # boot check WITHOUT the Radeon: virtual video card, 6 GB, 4 CPUs, ssh on SSHP+100, no REMOTIX forward.  Not the final configuration.
  lock
  running && die "VM $NAME is running already"
  [ -f "$DISK" ] || die "no disk: run crea first"
  SSHP=$((SSHP+100)); FWD=""; MEMV=${RX_VM_MEM:-6G}; CPUS=4   # RX_VM_MEM: optional memory override (e.g. 4G to run two of these beside the Radeon VM)
  sx sh -c ': > "$1"' _ "$SER"
  sx qemu-system-x86_64 $(base_args) -device virtio-vga 9>&- || die "qemu did not start"
  sx chmod 644 "$SER" "$PID" 2>/dev/null || true
  for i in $(seq 100); do sshv true 2>/dev/null && break; sleep 3; done
  running || die "qemu is not running (see $SER)"
  sshv true 2>/dev/null || { echo "ssh not answering in 300 s (see $SER): stopping the VM"; stop_vm; exit 1; }
  if [ "${3:-}" = --resta ]; then echo "VM $NAME left running without the Radeon: ssh -p $SSHP (key $D/vmkey); stop it with: $0 spegni $NAME"; exit 0; fi
  sleep 20   # let the display manager come up
  sshv "echo -n 'uname -r: '; uname -r; echo -n 'display-manager: '; systemctl is-active display-manager; readlink /etc/systemd/system/display-manager.service; echo 'loginctl list-sessions:'; loginctl list-sessions --no-legend; echo 'aa-status:'; echo $PASS | sudo -S -p '' aa-status 2>&1 | head -3; echo 'snap list:'; snap list 2>&1 | head -20; echo -n 'hostname: '; hostname; echo -n 'machine-id: '; cat /etc/machine-id; getent passwd prova prova2 | cut -d: -f1,6; id prova; ls /dev/dri" || true
  stop_vm; echo "boot check done, VM stopped";;
ssh) shift 2; sshv "$@";;
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
  for d in $GPU $GPUA; do echo "$d: $(drv $d)"; done;;
*) echo "usage: $0 crea|accendi|spegni|ssh|stato|prova-avvio ubuntu|kubuntu|xubuntu|lubuntu [cmd]; $0 istantanea|ripristina <name> <label>"; exit 2;;
esac
