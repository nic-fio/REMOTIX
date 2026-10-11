#!/bin/bash
# 15-one.sh — runs ONE test of the suite with the real browsers, ON THE SERVER.
#
#   (on the server, as nicfio)  bash 15-one.sh 15-f001-login-and-first-image.py --box gnome --browser firefox --fault
#   (from the tablet)           bash benches/15-suite/15-one.sh --remote 15-f001-… --box gnome …
#
# The environment is that of 11-hook.sh RUN_C21: nicfio's headless labwc
# at 3840x2160 on wayland-0, real windows.
HERE=$(cd "$(dirname "$0")" && pwd)
if [ "${1:-}" = "--remote" ]; then
	shift
	ssh -o BatchMode=yes nicfio@192.168.0.2 \
		"bash ${REMOTIX_CHECK_DIR:-/media/REMOTIX/src/controllo}/benches/15-suite/15-one.sh $*" 2>&1 \
		| grep --line-buffered -v '^tput'
	exit "${PIPESTATUS[0]}"
fi
u=$(id -u)
exec env XDG_RUNTIME_DIR="/run/user/$u" \
	WAYLAND_DISPLAY="${REMOTIX_REAL_WAYLAND:-wayland-0}" \
	REMOTIX_NESTED_SCREEN=1 REMOTIX_ON_SERVER=1 \
	REMOTIX_CHROME_OPTIONS="--ozone-platform=wayland --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-timer-throttling" MOZ_ENABLE_WAYLAND=1 \
	python3 "$HERE/$1" "${@:2}"
