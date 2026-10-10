#!/bin/bash
# 19-scatole-scheda.sh — rebuilds the 4 rete11-* boxes from scratch on the chosen card
# (phase 19, anti-regression net: Intel round = VA-API, Radeon round = Vulkan).
#
#   (on the server, as nicfio)  bash 19-scatole-scheda.sh intel|amd [gnome kde xfce lxqt]
#
# Like 15-rifai-scatole.sh (accendi → prodotto → server for each box), plus
# REMOTIX_SCHEDA passed to `11-accendi.sh accendi` through sudo (phase 16 §11:
# `--scheda amd` = the Radeon RX 6800 mapped inside as card0/renderD128).
set -u
SCHEDA=${1:?usage: 19-scatole-scheda.sh intel|amd [desktop...]}
shift
DESKTOP=${*:-gnome kde xfce lxqt}
cd /media/REMOTIX/rete11 || exit 2
PAROLA=${REMOTIX_PAROLA_SUDO:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}
esito=0
# ⛔ The shared memory (`shm`) of every box is mounted ALSO inside devroot
#    (/media/REMOTIX is attached there with propagation): `[M]` 3 Oct 2026, the
#    Intel → Radeon switch failed on all 4 («unlinkat …/userdata/shm:
#    device or resource busy») and the boxes stayed off.  The devroot copies are
#    unmounted first; podman removes the real ones.
for m in $(mount | awk '$3 ~ /devroot\/srv\/remotix\/contenitori\/storage\/overlay-containers\/.*\/userdata\/shm$/ {print $3}'); do
	printf '%s\n' "$PAROLA" | sudo -S -p '' umount "$m" && echo "   unmounted the copy in devroot: ${m##*overlay-containers/}"
done
for d in $DESKTOP; do
	echo "=== $d $SCHEDA $(date +%T)"
	for passo in accendi prodotto server; do
		if ! printf '%s\n' "$PAROLA" | sudo -S -p '' env REMOTIX_SCHEDA="$SCHEDA" bash 11-accendi.sh "$passo" "$d" >"/tmp/rifai-$SCHEDA-$d-$passo.log" 2>&1; then
			echo "⛔ $d $passo failed: $(tail -2 "/tmp/rifai-$SCHEDA-$d-$passo.log" | tr '\n' ' ')"
			esito=1
		else
			echo "   $passo: $(grep -a -E 'card:|listens' "/tmp/rifai-$SCHEDA-$d-$passo.log" | tail -1)"
		fi
	done
done
echo "END $(date +%T) · binary $(md5sum prodotto/remotix | cut -c1-8) · page $(md5sum prodotto/pagina.html | cut -c1-8)"
exit $esito
