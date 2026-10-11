#!/bin/bash
# 19-scatole-scheda.sh — rebuilds the 4 rete11-* boxes from scratch on the chosen card
# (phase 19, anti-regression net: Intel round = VA-API, Radeon round = Vulkan).
#
#   (on the server, as nicfio)  bash 19-scatole-scheda.sh intel|amd [gnome kde xfce lxqt]
#
# Like 15-rifai-scatole.sh (start → product → server for each box), plus
# REMOTIX_CARD passed to `11-accendi.sh start` through sudo (phase 16 §11:
# `--card amd` = the Radeon RX 6800 mapped inside as card0/renderD128).
set -u
GPU=${1:?usage: 19-scatole-scheda.sh intel|amd [desktop...]}
shift
DESKTOP=${*:-gnome kde xfce lxqt}
cd /media/REMOTIX/rete11 || exit 2
PASSWORD=${REMOTIX_SUDO_PASSWORD:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}
outcome=0
# ⛔ The shared memory (`shm`) of every box is mounted ALSO inside devroot
#    (/media/REMOTIX is attached there with propagation): `[M]` 3 Oct 2026, the
#    Intel → Radeon switch failed on all 4 («unlinkat …/userdata/shm:
#    device or resource busy») and the boxes stayed off.  The devroot copies are
#    unmounted first; podman removes the real ones.
for m in $(mount | awk '$3 ~ /devroot\/srv\/remotix\/contenitori\/storage\/overlay-containers\/.*\/userdata\/shm$/ {print $3}'); do
	printf '%s\n' "$PASSWORD" | sudo -S -p '' umount "$m" && echo "   unmounted the copy in devroot: ${m##*overlay-containers/}"
done
for d in $DESKTOP; do
	echo "=== $d $GPU $(date +%T)"
	for step in accendi prodotto server; do
		if ! printf '%s\n' "$PASSWORD" | sudo -S -p '' env REMOTIX_CARD="$GPU" bash 11-accendi.sh "$step" "$d" >"/tmp/rifai-$GPU-$d-$step.log" 2>&1; then
			echo "⛔ $d $step failed: $(tail -2 "/tmp/rifai-$GPU-$d-$step.log" | tr '\n' ' ')"
			outcome=1
		else
			echo "   $step: $(grep -a -E 'card:|listens' "/tmp/rifai-$GPU-$d-$step.log" | tail -1)"
		fi
	done
done
echo "END $(date +%T) · binary $(md5sum prodotto/remotix | cut -c1-8) · page $(md5sum prodotto/pagina.html | cut -c1-8)"
exit $outcome
