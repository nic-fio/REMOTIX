#!/bin/bash
# 16-campagna.sh — the TWO campaigns of phase 16 in a row, by themselves, on the server (§11).
#
#   (on the server, as nicfio)
#   sudo systemd-run --unit=r16-coda --uid=nicfio -E XDG_RUNTIME_DIR=/run/user/1000 \
#        -p TimeoutStopSec=1200 -p KillMode=mixed -p OOMPolicy=continue \
#        bash /media/REMOTIX/src/controllo/banchi/16-stress/16-campagna.sh intel-b amd
#
# Every argument is a campaign label: the name of the climbs and of the logs
# (`<label>-<size>-<desktop>`, `coda-<label>.log`).  A label that starts
# with «amd» turns on the Radeon (`--scheda amd`), the others stay on the Intel.
# ⭐ «intel-b»: the Intel campaign REDONE with the product of 26 Sep (binary 45d048c8,
#   page fb9a18f3 — WebGL, DECISIONI §9.4); the night one («intel») stays in the
#   log as the «before».
# The SIGTERM (systemctl stop) is passed to the queue in progress, which passes it to the climb.
# ⭐ fasi/20 §7.0: REMOTIX_16_SISTEMA=xrdp ⇒ every climb with `--sistema xrdp` (the comparison
#   with xrdp: campaigns intel-x20 amd-x20, unit r20-xrdp, with -p OOMScoreAdjust=-900);
#   the queue receives how many desktops remain after it, for the estimate of the hours.
set -u
QUI=$(cd "$(dirname "$0")" && pwd)
M=/media/REMOTIX/misure/fase16
figlio=""; ferma=0
trap 'ferma=1; [ -n "$figlio" ] && kill -TERM "$figlio"' TERM INT
TUTTE=$#; I=0
for etichetta in "$@"; do
	I=$((I + 1))
	[ "$ferma" = 1 ] && break
	[ -e "$M/FERMA" ] && break
	extra=""
	case "$etichetta" in amd*) extra="--scheda amd" ;; esac
	[ "${REMOTIX_16_SISTEMA:-}" = xrdp ] && extra="$extra --sistema xrdp"
	echo "$(date '+%F %T') ▶ campaign $etichetta ($extra)" >> "$M/campagna.log"
	REMOTIX_16_IN_PIU="$extra" REMOTIX_16_DESKTOP_DOPO=$(( (TUTTE - I) * 4 )) \
		bash "$QUI/16-coda.sh" "$etichetta" gnome kde xfce lxqt &
	figlio=$!
	wait "$figlio"; while kill -0 "$figlio" 2>/dev/null; do wait "$figlio"; done
	figlio=""
	echo "$(date '+%F %T') ⏹ campaign $etichetta finished" >> "$M/campagna.log"
done
