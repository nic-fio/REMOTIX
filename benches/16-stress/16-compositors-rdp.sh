#!/bin/bash
# 16-compositors-rdp.sh — ONE FAKE SCREEN (Xvfb) PER USER of the xrdp climb (phases/20 §7.1).
#
#   (on the server, as nicfio)
#   bash 16-compositors-rdp.sh start N MISURA    u00 (the short check) + u01…uNN
#   bash 16-compositors-rdp.sh stop              all those of this file
#   bash 16-compositors-rdp.sh status
#
#   MISURA = 4k · 3k · 2k · fhd (as 16-compositors.sh), or WIDTHxHEIGHT
#
# ⭐ It is the twin of 16-compositors.sh for the comparison with xrdp: instead of the headless
#    labwc (where the browser runs) an Xvfb, where xfreerdp3 runs full screen.
#    Each one its own, for the same reason: a client covered by another stops
#    drawing.  The display of each (":2NN") is written in
#    $XDG_RUNTIME_DIR/16-compositors-rdp/uNN; 16-climb.py --system xrdp reads it and
#    passes it to the actor (--display).
# ⛔ phases/20 §7.7: the Xvfb are born with oom_score_adj 800 — if the kernel has to kill
#    something, it kills a client (a red rung), not sshd nor the queue.
# ⚠ The screen is 24 bit, the same size as the remote desktop: FreeRDP full
#    screen asks the server for a desktop as big as the Xvfb, and the photo is 1:1.
set -u
R=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
C="$R/16-compositors-rdp"
mkdir -p "$C"
BASE_DISPLAY=${REMOTIX_16_DISPLAY_BASE:-200}

measure() {
	case "$1" in
	4k|4K) echo 3840x2160 ;;
	3k|3K) echo 3200x1800 ;;
	2k|2K) echo 2560x1440 ;;
	fhd|FHD|fullhd) echo 1920x1080 ;;
	[0-9]*x[0-9]*) echo "$1" ;;
	*) return 1 ;;
	esac
}

alive() { [ -f "$C/$1.pid" ] && kill -0 "$(cat "$C/$1.pid")" 2>/dev/null; }

size_of() {  # :N ⇒ WIDTHxHEIGHT
	DISPLAY=$1 xdpyinfo 2>/dev/null | awk '/dimensions:/{print $2; exit}'
}

turn_on_one() {  # uNN WxH
	local n=$1 m=$2 k d
	k=$((10#${n#u}))
	d=":$((BASE_DISPLAY + k))"
	if alive "$n"; then
		if [ "$(size_of "$d")" = "$m" ]; then
			echo "$n: already on at $d ($m)"
			return 0
		fi
		# ⚠ Xvfb does not change size: it is switched off and on again
		kill "$(cat "$C/$n.pid")" 2>/dev/null
		sleep 0.5
	fi
	rm -f "$C/$n" "$C/$n.pid" "/tmp/.X11-unix/X${d#:}" "/tmp/.X${d#:}-lock" 2>/dev/null
	setsid Xvfb "$d" -screen 0 "${m}x24" -nolisten tcp -noreset </dev/null >"$C/$n.log" 2>&1 &
	echo $! >"$C/$n.pid"
	echo 800 >"/proc/$(cat "$C/$n.pid")/oom_score_adj" 2>/dev/null
	for _ in $(seq 1 40); do
		[ "$(size_of "$d")" = "$m" ] && break
		sleep 0.25
	done
	if [ "$(size_of "$d")" != "$m" ]; then
		echo "$n: ⛔ Xvfb $d does not answer at $m ($(tail -2 "$C/$n.log" | tr '\n' ' '))"
		kill "$(cat "$C/$n.pid")" 2>/dev/null
		rm -f "$C/$n.pid"
		return 1
	fi
	echo "$d" >"$C/$n"
	echo "$n: ⭐ Xvfb $d ($m), pid $(cat "$C/$n.pid")"
}

start() {
	local N=${1:-} M
	case "$N" in ''|*[!0-9]*) echo "usage: $0 start N MISURA"; exit 2 ;; esac
	M=$(measure "${2:-4k}") || { echo "unknown size: ${2:-}"; exit 2; }
	outcome=0
	for i in $(seq 0 "$N"); do
		turn_on_one "$(printf 'u%02d' "$i")" "$M" || outcome=1
	done
	return $outcome
}

stop() {
	for f in "$C"/u[0-9][0-9].pid; do
		[ -e "$f" ] || continue
		n=$(basename "$f" .pid)
		kill "$(cat "$f")" 2>/dev/null
		rm -f "$C/$n" "$f"
		echo "$n: switched off"
	done
	true
}

status() {
	local amount=0
	for f in "$C"/u[0-9][0-9]; do
		[ -e "$f" ] || continue
		n=$(basename "$f")
		if alive "$n"; then
			echo "$n: on at $(cat "$f") — $(size_of "$(cat "$f")")"
			amount=$((amount + 1))
		else
			echo "$n: ⚠ off (the file is left)"
		fi
	done
	echo "on: $amount"
}

case "${1:-status}" in
start) start "${2:-}" "${3:-4k}" ;;
stop) stop ;;
status) status ;;
*) echo "usage: $0 start N MISURA | stop | status"; exit 2 ;;
esac
