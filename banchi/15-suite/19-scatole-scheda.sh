#!/bin/bash
# 19-scatole-scheda.sh — rifà le 4 scatole rete11-* da zero sulla scheda scelta
# (fase 19, rete anti-regressione: giro Intel = VA-API, giro Radeon = Vulkan).
#
#   (sul server, come nicfio)  bash 19-scatole-scheda.sh intel|amd [gnome kde xfce lxqt]
#
# Come 15-rifai-scatole.sh (accendi → prodotto → server per ogni scatola), con in
# più REMOTIX_SCHEDA passata a `11-accendi.sh accendi` attraverso sudo (fase 16 §11:
# `--scheda amd` = la Radeon RX 6800 mappata dentro come card0/renderD128).
set -u
SCHEDA=${1:?uso: 19-scatole-scheda.sh intel|amd [desktop...]}
shift
DESKTOP=${*:-gnome kde xfce lxqt}
cd /media/REMOTIX/rete11 || exit 2
PAROLA=${REMOTIX_PAROLA_SUDO:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}
esito=0
# ⛔ La memoria condivisa (`shm`) di ogni scatola si monta ANCHE dentro devroot
#    (/media/REMOTIX vi e' agganciata con propagazione): `[M]` 3 ott 2026, il
#    passaggio Intel → Radeon falliva su tutti e 4 («unlinkat …/userdata/shm:
#    device or resource busy») e le scatole restavano spente.  Si sganciano
#    prima le copie di devroot; quelle vere le toglie podman.
for m in $(mount | awk '$3 ~ /devroot\/srv\/remotix\/contenitori\/storage\/overlay-containers\/.*\/userdata\/shm$/ {print $3}'); do
	printf '%s\n' "$PAROLA" | sudo -S -p '' umount "$m" && echo "   sganciata la copia in devroot: ${m##*overlay-containers/}"
done
for d in $DESKTOP; do
	echo "=== $d $SCHEDA $(date +%T)"
	for passo in accendi prodotto server; do
		if ! printf '%s\n' "$PAROLA" | sudo -S -p '' env REMOTIX_SCHEDA="$SCHEDA" bash 11-accendi.sh "$passo" "$d" >"/tmp/rifai-$SCHEDA-$d-$passo.log" 2>&1; then
			echo "⛔ $d $passo non riuscito: $(tail -2 "/tmp/rifai-$SCHEDA-$d-$passo.log" | tr '\n' ' ')"
			esito=1
		else
			echo "   $passo: $(grep -a -E 'scheda:|ascolta' "/tmp/rifai-$SCHEDA-$d-$passo.log" | tail -1)"
		fi
	done
done
echo "FINE $(date +%T) · binario $(md5sum prodotto/remotix | cut -c1-8) · pagina $(md5sum prodotto/pagina.html | cut -c1-8)"
exit $esito
