#!/bin/bash
# headless-multi.sh - like headless-wayland.sh (start|stop <dir>) but the pid written is labwc's own, so `stop` really
# stops it (headless-wayland.sh writes the pid of the setsid wrapper and leaks the compositor), and `stop` removes <dir>.
set -u
case "${1:-}" in
start)
	D=$2; mkdir -p "$D"; chmod 700 "$D"
	# labwc starts Xwayland and dies when the shared server has no X display number free at that instant: try again
	for try in 1 2 3 4 5 6; do
		rm -f "$D"/wayland-*
		( exec env -u WAYLAND_DISPLAY -u DISPLAY XDG_RUNTIME_DIR="$D" WLR_BACKENDS=headless WLR_RENDERER=pixman \
			WLR_LIBINPUT_NO_DEVICES=1 labwc </dev/null >"$D/labwc.log" 2>&1 ) &
		echo $! >"$D/labwc.pid"
		for _ in $(seq 1 24); do
			s=$(ls "$D" | grep -E '^wayland-[0-9]+$' | head -1)
			[ -n "$s" ] && break; sleep 0.25
		done
		[ -n "${s:-}" ] && break
		kill "$(cat "$D/labwc.pid")" 2>/dev/null; sleep $((try * 2))
	done
	[ -n "${s:-}" ] || { echo "labwc did not open a socket: $(tail -3 "$D/labwc.log")" >&2; exit 1; }
	out=$(WAYLAND_DISPLAY=$s XDG_RUNTIME_DIR=$D wlr-randr 2>/dev/null | awk 'NR==1{print $1}')
	WAYLAND_DISPLAY=$s XDG_RUNTIME_DIR=$D wlr-randr --output "$out" --custom-mode 1600x1000 >/dev/null 2>&1 || true
	echo "$s" ;;
stop)
	if [ -f "$2/labwc.pid" ]; then kill "$(cat "$2/labwc.pid")" 2>/dev/null; sleep 1; kill -9 "$(cat "$2/labwc.pid")" 2>/dev/null; fi
	rm -rf "$2"; true ;;
*) echo "usage: $0 start|stop <dir>"; exit 2 ;;
esac
