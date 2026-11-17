#!/bin/bash
# headless-wayland.sh - a headless labwc (no screen, software rendering) to run the test browsers in.
#   start <dir>   prints the Wayland socket name on stdout, writes <dir>/labwc.pid
#   stop <dir>
# <dir> is a private XDG_RUNTIME_DIR (mode 700) so that nothing else shares the compositor.
set -u
case "${1:-}" in
start)
	D=$2; mkdir -p "$D"; chmod 700 "$D"
	env -u WAYLAND_DISPLAY -u DISPLAY XDG_RUNTIME_DIR="$D" WLR_BACKENDS=headless WLR_RENDERER=pixman \
		WLR_LIBINPUT_NO_DEVICES=1 setsid labwc </dev/null >"$D/labwc.log" 2>&1 &
	echo $! >"$D/labwc.pid"
	for _ in $(seq 1 40); do
		s=$(ls "$D" | grep -E '^wayland-[0-9]+$' | head -1)
		[ -n "$s" ] && break; sleep 0.25
	done
	[ -n "${s:-}" ] || { echo "labwc did not open a socket: $(tail -3 "$D/labwc.log")" >&2; exit 1; }
	out=$(WAYLAND_DISPLAY=$s XDG_RUNTIME_DIR=$D wlr-randr 2>/dev/null | awk 'NR==1{print $1}')
	WAYLAND_DISPLAY=$s XDG_RUNTIME_DIR=$D wlr-randr --output "$out" --custom-mode 1600x1000 >/dev/null 2>&1 || true
	echo "$s" ;;
stop)
	[ -f "$2/labwc.pid" ] && kill "$(cat "$2/labwc.pid")" 2>/dev/null; true ;;
*) echo "usage: $0 start|stop <dir>"; exit 2 ;;
esac
