#!/bin/bash
# 15-una.sh — fa girare UNA prova della suite coi browser veri, SUL SERVER.
#
#   (sul server, come nicfio)  bash 15-una.sh 15-f001-accesso-e-prima-immagine.py --scatola gnome --browser firefox --guasto
#   (dal tablet)               bash banchi/15-suite/15-una.sh --remoto 15-f001-… --scatola gnome …
#
# L'ambiente e' quello di 11-gancio.sh GIRA_C21: il labwc senza schermo di nicfio
# a 3840x2160 su wayland-0, finestre vere.
QUI=$(cd "$(dirname "$0")" && pwd)
if [ "${1:-}" = "--remoto" ]; then
	shift
	ssh -o BatchMode=yes nicfio@192.168.0.2 \
		"bash ${REMOTIX_CONTROLLO:-/media/REMOTIX/src/controllo}/banchi/15-suite/15-una.sh $*" 2>&1 \
		| grep --line-buffered -v '^tput'
	exit "${PIPESTATUS[0]}"
fi
u=$(id -u)
exec env XDG_RUNTIME_DIR="/run/user/$u" \
	WAYLAND_DISPLAY="${REMOTIX_WAYLAND_VERI:-wayland-0}" \
	REMOTIX_SCHERMO_ANNIDATO=1 REMOTIX_SUL_SERVER=1 \
	REMOTIX_CHROME_OPZIONI="--ozone-platform=wayland --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-timer-throttling" MOZ_ENABLE_WAYLAND=1 \
	python3 "$QUI/$1" "${@:2}"
