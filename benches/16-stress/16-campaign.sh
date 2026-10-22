#!/bin/bash
# 16-campaign.sh — the TWO campaigns of phase 16 in a row, by themselves, on the server (§11).
#
#   (on the server, as nicfio)
#   sudo systemd-run --unit=r16-coda --uid=nicfio -E XDG_RUNTIME_DIR=/run/user/1000 \
#        -p TimeoutStopSec=1200 -p KillMode=mixed -p OOMPolicy=continue \
#        bash /media/REMOTIX/src/check/benches/16-stress/16-campaign.sh intel-b amd
#
# Every argument is a campaign label: the name of the climbs and of the logs
# (`<label>-<size>-<desktop>`, `coda-<label>.log`).  A label that starts
# with «amd» turns on the Radeon (`--card amd`), the others stay on the Intel.
# ⭐ «intel-b»: the Intel campaign REDONE with the product of 26 Sep (binary 45d048c8,
#   page fb9a18f3 — WebGL, DECISIONI §9.4); the night one («intel») stays in the
#   log as the «before».
# The SIGTERM (systemctl stop) is passed to the queue in progress, which passes it to the climb.
# ⭐ phases/20 §7.0: REMOTIX_16_SYSTEM=xrdp ⇒ every climb with `--system xrdp` (the comparison
#   with xrdp: campaigns intel-x20 amd-x20, unit r20-xrdp, with -p OOMScoreAdjust=-900);
#   the queue receives how many desktops remain after it, for the estimate of the hours.
set -u
HERE=$(cd "$(dirname "$0")" && pwd)
M=/media/REMOTIX/misure/fase16
child=""; halt=0
trap 'halt=1; [ -n "$child" ] && kill -TERM "$child"' TERM INT
ALL=$#; I=0
for label in "$@"; do
	I=$((I + 1))
	[ "$halt" = 1 ] && break
	[ -e "$M/FERMA" ] && break
	extra=""
	case "$label" in amd*) extra="--card amd" ;; esac
	[ "${REMOTIX_16_SYSTEM:-}" = xrdp ] && extra="$extra --system xrdp"
	echo "$(date '+%F %T') ▶ campaign $label ($extra)" >> "$M/campagna.log"
	REMOTIX_16_EXTRA="$extra" REMOTIX_16_DESKTOPS_AFTER=$(( (ALL - I) * 4 )) \
		bash "$HERE/16-queue.sh" "$label" gnome kde xfce lxqt &
	child=$!
	wait "$child"; while kill -0 "$child" 2>/dev/null; do wait "$child"; done
	child=""
	echo "$(date '+%F %T') ⏹ campaign $label finished" >> "$M/campagna.log"
done
