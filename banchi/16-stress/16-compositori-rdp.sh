#!/bin/bash
# 16-compositori-rdp.sh — ONE FAKE SCREEN (Xvfb) PER USER of the xrdp climb (fasi/20 §7.1).
#
#   (on the server, as nicfio)
#   bash 16-compositori-rdp.sh accendi N MISURA    u00 (the short check) + u01…uNN
#   bash 16-compositori-rdp.sh spegni              all those of this file
#   bash 16-compositori-rdp.sh stato
#
#   MISURA = 4k · 3k · 2k · fhd (as 16-compositori.sh), or WIDTHxHEIGHT
#
# ⭐ It is the twin of 16-compositori.sh for the comparison with xrdp: instead of the headless
#    labwc (where the browser runs) an Xvfb, where xfreerdp3 runs full screen.
#    Each one its own, for the same reason: a client covered by another stops
#    drawing.  The display of each (":2NN") is written in
#    $XDG_RUNTIME_DIR/16-compositori-rdp/uNN; 16-salita.py --sistema xrdp reads it and
#    passes it to the actor (--display).
# ⛔ fasi/20 §7.7: the Xvfb are born with oom_score_adj 800 — if the kernel has to kill
#    something, it kills a client (a red rung), not sshd nor the queue.
# ⚠ The screen is 24 bit, the same size as the remote desktop: FreeRDP full
#    screen asks the server for a desktop as big as the Xvfb, and the photo is 1:1.
set -u
R=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
C="$R/16-compositori-rdp"
mkdir -p "$C"
BASE_DISPLAY=${REMOTIX_16_DISPLAY_BASE:-200}

misura() {
	case "$1" in
	4k|4K) echo 3840x2160 ;;
	3k|3K) echo 3200x1800 ;;
	2k|2K) echo 2560x1440 ;;
	fhd|FHD|fullhd) echo 1920x1080 ;;
	[0-9]*x[0-9]*) echo "$1" ;;
	*) return 1 ;;
	esac
}

vivo() { [ -f "$C/$1.pid" ] && kill -0 "$(cat "$C/$1.pid")" 2>/dev/null; }

misura_di() {  # :N ⇒ WIDTHxHEIGHT
	DISPLAY=$1 xdpyinfo 2>/dev/null | awk '/dimensions:/{print $2; exit}'
}

accendi_uno() {  # uNN WxH
	local n=$1 m=$2 k d
	k=$((10#${n#u}))
	d=":$((BASE_DISPLAY + k))"
	if vivo "$n"; then
		if [ "$(misura_di "$d")" = "$m" ]; then
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
		[ "$(misura_di "$d")" = "$m" ] && break
		sleep 0.25
	done
	if [ "$(misura_di "$d")" != "$m" ]; then
		echo "$n: ⛔ Xvfb $d does not answer at $m ($(tail -2 "$C/$n.log" | tr '\n' ' '))"
		kill "$(cat "$C/$n.pid")" 2>/dev/null
		rm -f "$C/$n.pid"
		return 1
	fi
	echo "$d" >"$C/$n"
	echo "$n: ⭐ Xvfb $d ($m), pid $(cat "$C/$n.pid")"
}

accendi() {
	local N=${1:-} M
	case "$N" in ''|*[!0-9]*) echo "usage: $0 accendi N MISURA"; exit 2 ;; esac
	M=$(misura "${2:-4k}") || { echo "unknown size: ${2:-}"; exit 2; }
	esito=0
	for i in $(seq 0 "$N"); do
		accendi_uno "$(printf 'u%02d' "$i")" "$M" || esito=1
	done
	return $esito
}

spegni() {
	for f in "$C"/u[0-9][0-9].pid; do
		[ -e "$f" ] || continue
		n=$(basename "$f" .pid)
		kill "$(cat "$f")" 2>/dev/null
		rm -f "$C/$n" "$f"
		echo "$n: switched off"
	done
	true
}

stato() {
	local quanti=0
	for f in "$C"/u[0-9][0-9]; do
		[ -e "$f" ] || continue
		n=$(basename "$f")
		if vivo "$n"; then
			echo "$n: on at $(cat "$f") — $(misura_di "$(cat "$f")")"
			quanti=$((quanti + 1))
		else
			echo "$n: ⚠ off (the file is left)"
		fi
	done
	echo "on: $quanti"
}

case "${1:-stato}" in
accendi) accendi "${2:-}" "${3:-4k}" ;;
spegni) spegni ;;
stato) stato ;;
*) echo "usage: $0 accendi N MISURA | spegni | stato"; exit 2 ;;
esac
