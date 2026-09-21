#!/bin/bash
#
# 13-w3-input-wlr.sh — costruisce e fa girare `13-w3-input-wlr.c` contro un
# labwc headless PRIVATO (runtime dir propria: non tocca il desktop di chi lo
# lancia, e non tocca la macchina di prova).
#
#   bash banchi/13-w3-input-wlr.sh [tutto|taglio|caduta|scorciatoia]
#
# ⚠ Vuole sull'host: labwc, wayland-scanner, gcc, e gli -dev di wayland-client,
#   xkbcommon, libei, glib (su Trixie ci sono tutti).
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
SRC=$QUI/../src
SCENA=${1:-tutto}
LAV=$(mktemp -d "${TMPDIR:-/tmp}/13-w3.XXXXXX")
cd "$LAV" || exit 2

for p in virtual-keyboard-unstable-v1 wlr-virtual-pointer-unstable-v1; do
	wayland-scanner client-header "$SRC/protocolli/$p.xml" "$p-client-protocol.h" || exit 2
	wayland-scanner private-code "$SRC/protocolli/$p.xml" "$p-protocol.c" || exit 2
done
X=/usr/share/wayland-protocols/stable/xdg-shell/xdg-shell.xml
wayland-scanner client-header $X xdg-shell-client-protocol.h || exit 2
wayland-scanner private-code $X xdg-shell-protocol.c || exit 2
gcc -O1 -g -Wall -I. -o testimone "$QUI/06-b33-testimone.c" xdg-shell-protocol.c \
	$(pkg-config --cflags --libs wayland-client) || exit 2
gcc -O1 -g -Wall -Wextra -Wno-unused-parameter -D_GNU_SOURCE -I. -I"$SRC" -o driver \
	"$QUI/13-w3-input-wlr.c" "$SRC/input.c" "$SRC/wlr_input.c" "$SRC/tastiera.c" \
	"$SRC/registro.c" virtual-keyboard-unstable-v1-protocol.c \
	wlr-virtual-pointer-unstable-v1-protocol.c \
	$(pkg-config --cflags --libs wayland-client xkbcommon libei-1.0 gio-2.0) || exit 2

mkdir -m700 run; mkdir -p cfg/labwc home; : > cfg/labwc/autostart
BASE=(env -i HOME=$LAV/home XDG_RUNTIME_DIR=$LAV/run PATH=/usr/bin:/bin XDG_CONFIG_HOME=$LAV/cfg)
LABWC=("${BASE[@]}" WLR_BACKENDS=headless WLR_HEADLESS_OUTPUTS=1 WLR_RENDERER=pixman
       WLR_LIBINPUT_NO_DEVICES=1 XKB_DEFAULT_LAYOUT=it labwc -C "$LAV/cfg/labwc")
"${LABWC[@]}" > labwc.log 2>&1 &
LPID=$!
for _ in $(seq 50); do [ -S run/wayland-0 ] && break; sleep 0.1; done
"${BASE[@]}" WAYLAND_DISPLAY=wayland-0 ./testimone --misura 1280x720 > testimone.log 2>&1 &
TPID=$!
sleep 1
if [ "$SCENA" = caduta ]; then
	# ⚠ uccide labwc e lo fa ripartire: il testimone muore con lui
	"${BASE[@]}" ./driver caduta > driver.log 2>&1 &
	DPID=$!
	sleep 2
	kill $LPID; wait $LPID 2>/dev/null
	"${LABWC[@]}" > labwc2.log 2>&1 &
	LPID=$!
	wait $DPID
else
	"${BASE[@]}" ./driver "$SCENA" > driver.log 2>&1
fi
sleep 0.5
kill $TPID $LPID 2>/dev/null
wait 2>/dev/null
echo "----- driver";    cat driver.log
echo "----- testimone"; cat testimone.log
echo "(cartella di lavoro: $LAV)"
