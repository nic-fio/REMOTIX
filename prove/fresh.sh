#!/bin/bash
# fresh.sh <de> - a fresh box with the package installed and the service enabled (reset, install, enable).
# DEB=<path> picks the package (default: the newest remotix_*.deb under /media/REMOTIX-UBUNTU/pacchetti).
set -eo pipefail
DE=$1; HERE=$(cd "$(dirname "$0")" && pwd); BOXES=$HERE/boxes; [ -d "$BOXES" ] || BOXES=$HERE/../boxes; B=$BOXES/box.sh
[ "${RX_BANCO:-}" = vm ] && exec "$HERE/banco-vm/fresh-vm.sh" "$DE"  # VMs: a clean state inside the running VM, DEB passes through
DEB=${DEB:-$(ls -t /media/REMOTIX-UBUNTU/pacchetti/remotix_*.deb /media/REMOTIX-UBUNTU/pacchetti/fix*/remotix_*.deb 2>/dev/null | head -1)}
[ -f "$DEB" ] || { echo "FAIL no package: $DEB"; exit 1; }
echo "package $DEB"
$B reset "$DE" | tail -1
$B install "$DE" "$DEB" | tail -1
$B ssh "$DE" "systemctl enable --now remotix >/dev/null 2>&1; sleep 4; systemctl is-active remotix"
