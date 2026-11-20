#!/bin/bash
# vm.sh - the real-system test VM (Ubuntu 26.04 server cloud image, KVM) on the dev server.  Usage: vm.sh start|stop|ssh [cmd...]|status
# Everything lives in this script's folder (/media/REMOTIX-UBUNTU/vm): image, disk, seed, key, pidfile, serial log.
# virtio-vga gives the guest a /dev/dri/renderD128 (the package's preinst refuses to install without a render node); VA-API encoding does not work on it.
# Host ports: ssh 2301 -> guest 22; REMOTIX tcp+udp 8901 -> guest 7447.  Login: user prova / password prova (sudo), or key vmkey.
set -euo pipefail
D=$(cd "$(dirname "$0")" && pwd)
IMG=$D/ubuntu-26.04-server-cloudimg-amd64.img DISK=$D/disk.qcow2 SEED=$D/seed.iso PID=$D/vm.pid
SSHP=2301 RXP=8901
sshv() { ssh -i "$D/vmkey" -p $SSHP -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=5 prova@127.0.0.1 "$@"; }
running() { [ -f "$PID" ] && kill -0 "$(cat "$PID")" 2>/dev/null; }
case "${1:-}" in
start)
  running && { echo "already running (pid $(cat "$PID"))"; exit 0; }
  if [ ! -f "$DISK" ]; then
    cp "$IMG" "$DISK"; qemu-img resize -q "$DISK" 20G
    T=$(mktemp -d)
    printf 'instance-id: remotix-vm\nlocal-hostname: rxvm\n' > "$T/meta-data"
    cat > "$T/user-data" <<U
#cloud-config
users:
  - name: prova
    sudo: ALL=(ALL) NOPASSWD:ALL
    shell: /bin/bash
    lock_passwd: false
    plain_text_passwd: prova
    ssh_authorized_keys:
      - $(cat "$D/vmkey.pub")
ssh_pwauth: true
U
    genisoimage -quiet -output "$SEED" -volid cidata -joliet -rock "$T/user-data" "$T/meta-data"; rm -rf "$T"
  fi
  qemu-system-x86_64 -enable-kvm -cpu host -smp 4 -m 4096 -display none -serial file:"$D/serial.log" \
    -drive file="$DISK",if=virtio,format=qcow2 -drive file="$SEED",if=virtio,format=raw,readonly=on \
    -netdev user,id=n0,hostfwd=tcp:127.0.0.1:$SSHP-:22,hostfwd=tcp:127.0.0.1:$RXP-:7447,hostfwd=udp:127.0.0.1:$RXP-:7447 \
    -device virtio-net-pci,netdev=n0 -device virtio-rng-pci -device virtio-vga -daemonize -pidfile "$PID"
  for i in $(seq 90); do sshv true 2>/dev/null && { echo "up (ssh -p $SSHP)"; exit 0; }; sleep 2; done
  echo "started but ssh not answering yet"; exit 1;;
stop)
  running || { echo "not running"; exit 0; }
  sshv 'sudo systemctl poweroff' 2>/dev/null || true
  for i in $(seq 30); do running || { echo stopped; exit 0; }; sleep 1; done
  kill "$(cat "$PID")"; echo "killed";;
ssh) shift; sshv "$@";;
status) running && echo "running pid $(cat "$PID")" || echo stopped;;
*) echo "usage: $0 start|stop|ssh [cmd]|status"; exit 2;;
esac
