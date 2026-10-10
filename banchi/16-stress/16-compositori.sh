#!/bin/bash
# 16-compositori.sh — ONE headless labwc PER USER of the climb (phase 16).
#
#   (on the server, as nicfio)
#   bash 16-compositori.sh accendi N MISURA    u00 (the short check) + u01…uNN
#   bash 16-compositori.sh spegni              all those of this file
#   bash 16-compositori.sh stato
#
#   MISURA = 4k (3840x2160) · 3k (3200x1800) · 2k (2560x1440) · fhd (1920x1080)
#            (fasi/16-stress-e-capacita.md §8), or WIDTHxHEIGHT
#
# ⛔ Why one per user (fasi/16 §4): a Chrome window COVERED by
#    another stops drawing (`[M]` phase 15, G2/G8: photos hung up to 17
#    min) ⇒ with 16 4K windows in the same compositor we would measure that.
#    Every browser has its own compositor, and in its compositor it is alone.
#
# The socket of each is written in $XDG_RUNTIME_DIR/16-compositori/uNN;
# 16-salita.py reads it and passes it to the actor (--wayland) and to the short check.
# `u00` belongs to the SHORT CHECK (§7), which comes in and leaves at every level.
#
# ⛔ It does NOT touch the labwc of 15-compositori.sh (others use them): it only knows the
#    pids written in ITS folder.  «accendi» is repeatable: those already
#    on stay (the rungs climb without switching anyone off), the size is
#    set again if it changed.
set -u
R=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
C="$R/16-compositori"
mkdir -p "$C"

# ⚠ THE COMPOSITORS' CARD: `renderD128`/`renderD129` swap between two
#   boots (11-accendi.sh, «the Radeon inside DOES NOT EXIST»), and since 25 Sep the
#   server also has the RX 6800.  ⇒ The integrated Intel is found by PCI
#   ADDRESS (driver i915/xe), as 11-accendi.sh does; REMOTIX_16_RENDER chooses it
#   from outside (the Radeon campaign).  It is written in $C/render.
render_intel() {
	for K in /sys/class/drm/card[0-9]*; do
		case "$K" in *-*) continue ;; esac
		[ -e "$K/device/driver" ] || continue
		case "$(basename "$(readlink -f "$K/device/driver")")" in i915|xe) ;; *) continue ;; esac
		readlink -f "/dev/dri/by-path/pci-$(basename "$(readlink -f "$K/device")")-render" 2>/dev/null
		return
	done
}
RENDER=${REMOTIX_16_RENDER:-$(render_intel)}
[ -e "${RENDER:-/nessuno}" ] || RENDER=/dev/dri/renderD128

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

vivo() { [ -f "$C/$1.pid" ] && kill -0 "$(cat "$C/$1.pid")" 2>/dev/null && [ -S "$R/$(cat "$C/$1" 2>/dev/null)" ]; }

uscita_di() { WAYLAND_DISPLAY=$1 wlr-randr 2>/dev/null | awk 'NR==1{print $1}'; }

metti_misura() {  # socket WxH
	local u
	u=$(uscita_di "$1")
	[ -n "$u" ] || { echo "no output"; return 1; }
	WAYLAND_DISPLAY=$1 wlr-randr --output "$u" --custom-mode "$2" 2>&1
}

misura_di() {  # socket ⇒ current WxH
	WAYLAND_DISPLAY=$1 wlr-randr 2>/dev/null | awk '/current/{print $1; exit}'
}

accendi_uno() {  # uNN WxH
	local n=$1 m=$2 prima nuovo
	if vivo "$n"; then
		s=$(cat "$C/$n")
		if [ "$(misura_di "$s")" != "$m" ]; then
			metti_misura "$s" "$m" >/dev/null
			echo "$n: already on at $s, size set again to $m ($(misura_di "$s"))"
		else
			echo "$n: already on at $s ($m)"
		fi
		return 0
	fi
	rm -f "$C/$n" "$C/$n.pid"
	prima=$(ls "$R" | grep -E '^wayland-[0-9]+$' | sort)
	env -u WAYLAND_DISPLAY -u DISPLAY WLR_BACKENDS=headless WLR_LIBINPUT_NO_DEVICES=1 \
		WLR_RENDER_DRM_DEVICE=$RENDER XDG_RUNTIME_DIR="$R" \
		setsid labwc </dev/null >"$C/$n.log" 2>&1 &
	echo $! >"$C/$n.pid"
	nuovo=""
	for _ in $(seq 1 60); do
		# ⭐ the socket of ITS pid (ss -xlp): if another labwc is born at the
		#   same instant (other agents, 15-compositori) the difference would be wrong
		nuovo=$(ss -xlpn 2>/dev/null | grep "pid=$(cat "$C/$n.pid")," \
			| grep -oE "$R/wayland-[0-9]+" | head -1 | xargs -r basename)
		[ -n "$nuovo" ] || nuovo=$(comm -13 <(echo "$prima") \
			<(ls "$R" | grep -E '^wayland-[0-9]+$' | sort) | head -1)
		[ -n "$nuovo" ] && break
		sleep 0.25
	done
	if [ -z "$nuovo" ]; then
		echo "$n: ⛔ labwc did not open a socket ($(tail -2 "$C/$n.log" | tr '\n' ' '))"
		kill "$(cat "$C/$n.pid")" 2>/dev/null
		rm -f "$C/$n.pid"
		return 1
	fi
	echo "$nuovo" >"$C/$n"
	echo "$RENDER" >"$C/render"
	for _ in $(seq 1 20); do [ -n "$(uscita_di "$nuovo")" ] && break; sleep 0.25; done
	metti_misura "$nuovo" "$m" >/dev/null
	if [ "$(misura_di "$nuovo")" != "$m" ]; then
		echo "$n: ⛔ $nuovo on but the size is «$(misura_di "$nuovo")» and not $m"
		return 1
	fi
	echo "$n: ⭐ $nuovo ($m), pid $(cat "$C/$n.pid")"
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
	echo "on: $quanti · compositors' card: $(cat "$C/render" 2>/dev/null || echo "$RENDER")"
}

case "${1:-stato}" in
accendi) accendi "${2:-}" "${3:-4k}" ;;
spegni) spegni ;;
stato) stato ;;
*) echo "usage: $0 accendi N MISURA | spegni | stato"; exit 2 ;;
esac
