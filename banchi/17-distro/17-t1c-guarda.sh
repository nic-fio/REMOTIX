#!/bin/bash
#
# 17-t1c-guarda.sh — phase 17, T1c: a REAL Chrome on the server enters the VM and
# looks at the desktop (`17-t1c-browser.py`), in a headless labwc of ITS OWN.
#
#   (on the server, as nicfio)  bash 17-t1c-guarda.sh <machine> <forwarded-port> [chrome|firefox]
#   e.g.  bash 17-t1c-guarda.sh debian13-gnome 7511
#   T1C_PROGRAMMA / T1C_EVIDENZE: another program with the same options (T8: t8-browser.py, which
#   stays connected during the upgrade) and another evidence folder.
#
# ⚠ 127.0.0.1 and not "localhost": QEMU's UDP forwarding listens only on IPv4, and
#   Chrome sends QUIC to ::1 ⇒ `QUIC_PACKET_WRITE_ERROR -102` and "Opening
#   handshake failed" while the page (TCP) opens anyway.  `[M]` 29 Sep.
# ⚠ The labwc is ITS OWN (not those of 15-compositori.sh, which serve the suite)
#   and renders on the Intel INTEGRATED GPU: the Radeon is not touched.
# ⚠ One browser at a time in the labwc: a covered Chrome window cannot be
#   photographed (15-compositori.sh).
set -u
m=${1:?machine}; p=${2:?port}; b=${3:-chrome}
QUI=$(cd "$(dirname "$0")" && pwd)
T1C=${T1C:-/media/REMOTIX/vm17/t1c}
R=/run/user/$(id -u)
mkdir -p "$T1C"

if ! { [ -f "$T1C/labwc.pid" ] && kill -0 "$(cat "$T1C/labwc.pid")" 2>/dev/null; }; then
	INTEL=""
	for r in /sys/class/drm/renderD*; do
		[ "$(basename "$(readlink -f "$r/device/driver")")" = i915 ] && INTEL=/dev/dri/$(basename "$r")
	done
	[ -n "$INTEL" ] || { echo "⛔ no Intel node: not starting labwc on the wrong GPU"; exit 2; }
	prima=$(ls "$R" | grep -E '^wayland-[0-9]+$' | sort)
	env -u WAYLAND_DISPLAY -u DISPLAY WLR_BACKENDS=headless WLR_LIBINPUT_NO_DEVICES=1 \
		WLR_RENDER_DRM_DEVICE="$INTEL" XDG_RUNTIME_DIR="$R" setsid labwc </dev/null >"$T1C/labwc.log" 2>&1 &
	echo $! >"$T1C/labwc.pid"
	n=""
	for _ in $(seq 1 40); do
		n=$(comm -13 <(echo "$prima") <(ls "$R" | grep -E '^wayland-[0-9]+$' | sort) | head -1)
		[ -n "$n" ] && break; sleep 0.25
	done
	[ -n "$n" ] || { echo "⛔ labwc did not open a socket"; exit 2; }
	echo "$n" >"$T1C/labwc.sock"; sleep 0.5
	u=$(WAYLAND_DISPLAY=$n wlr-randr | awk 'NR==1{print $1}')
	WAYLAND_DISPLAY=$n wlr-randr --output "$u" --custom-mode 2560x1440
fi

exec env XDG_RUNTIME_DIR="$R" WAYLAND_DISPLAY="$(cat "$T1C/labwc.sock")" MOZ_ENABLE_WAYLAND=1 \
	REMOTIX_CHROME_OPZIONI="--ozone-platform=wayland --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-timer-throttling" \
	python3 "${T1C_PROGRAMMA:-$QUI/17-t1c-browser.py}" --banchi "${REMOTIX_BANCHI:-/media/REMOTIX/src/controllo/banchi}" \
	--host 127.0.0.1 --porta "$p" --utente "${T1C_UTENTE:-prova}" --parola "${REMOTIX_PAROLA_PROVA:-prova2026}" \
	--browser "$b" --evidenze "${T1C_EVIDENZE:-$T1C/esiti/$m-$b}" --porte-base $((3200 + p % 100 * 2))
