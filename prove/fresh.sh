#!/bin/bash
# fresh.sh <de> - a fresh box with the package installed and the service enabled (reset, install, enable).
# DEB=<path> picks the package (default: the newest remotix_*.deb under /media/REMOTIX-DEBIAN/pacchetti).
set -eo pipefail
DE=$1; HERE=$(cd "$(dirname "$0")" && pwd); B=$HERE/boxes/box.sh
DEB=${DEB:-$(ls -t /media/REMOTIX-DEBIAN/pacchetti/remotix_*.deb /media/REMOTIX-DEBIAN/pacchetti/fix*/remotix_*.deb 2>/dev/null | head -1)}
[ -f "$DEB" ] || { echo "FAIL no package: $DEB"; exit 1; }
echo "package $DEB"
$B reset "$DE" | tail -1
$B install "$DE" "$DEB" | tail -1
$B ssh "$DE" "systemctl enable --now remotix >/dev/null 2>&1; sleep 4; systemctl is-active remotix"
