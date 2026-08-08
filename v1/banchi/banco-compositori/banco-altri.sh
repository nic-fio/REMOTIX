#!/bin/bash
#
# banco-altri.sh — la stessa misura, sugli altri due compositori.
#
# La scena e' la stessa di Mutter (weston-simple-egl a schermo intero, opaco,
# sincronizzato al ridisegno) e la macchina e' la stessa nello stesso minuto:
# e' l'unico modo in cui i tre numeri si possono mettere accanto.
#
# ⚠ Quel che NON e' uguale, e va detto leggendo la tabella:
#   - Mutter e KWin SPINGONO i fotogrammi (PipeWire); wlroots li fa TIRARE
#     (`wlr-screencopy`), un giro di socket per fotogramma;
#   - Mutter senza monitor disegna sulla GPU, KWin col backend virtuale disegna
#     in SOFTWARE (misurato: zero nodi DRM aperti, nessuna libreria GL caricata),
#     sway senza monitor disegna sulla GPU.
#
set -uo pipefail

QUI=/media/REMOTIX/tmp/banco-compositori
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

MISURE=(1920x1080 2560x1440 3840x2160)
DURATA=${1:-12}

spegni() { pkill -x kwin_wayland 2>/dev/null; pkill -x sway 2>/dev/null; pkill -x labwc 2>/dev/null; sleep 2; }

cella_kwin()
{
	local w=$1 h=$2 extra=${3:-}
	local nk s n

	pkill -x kwin_wayland 2>/dev/null; sleep 2
	nohup setsid env KWIN_COMPOSE=O2 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 \
	    kwin_wayland --virtual --width "$w" --height "$h" --no-lockscreen \
	    --socket=wayland-kwin >"$QUI/kwin.log" 2>&1 </dev/null &
	sleep 9

	WAYLAND_DISPLAY=wayland-kwin "$QUI/nodo-kwin" >"$QUI/nodo.txt" 2>"$QUI/nodo.log" &
	nk=$!
	sleep 3
	n=$(cat "$QUI/nodo.txt" 2>/dev/null)
	if [ -z "$n" ]; then
		echo "# KWin ${w}x${h}: nessun nodo — $(tail -1 "$QUI/nodo.log")"
		kill $nk 2>/dev/null
		return
	fi

	WAYLAND_DISPLAY=wayland-kwin stdbuf -oL weston-simple-egl -f -o >"$QUI/s-kwin.log" 2>&1 &
	s=$!
	sleep 2
	"$QUI/misura-cattura" --nodo "$n" --larghezza "$w" --altezza "$h" --fps 60 \
	    --durata "$DURATA" --scarto 5 $extra \
	    --etichetta "kwin-${w}x${h}-${extra:+dmabuf}${extra:-memoria}" 2>>"$QUI/altri.log" |
	    grep '^RIGA'
	echo "# client su KWin ${w}x${h}: $(grep -o '[0-9.]* fps' "$QUI/s-kwin.log" | tail -1)"
	kill $s $nk 2>/dev/null
	sleep 1
}

cella_wlroots()
{
	local compositore=$1 w=$2 h=$3
	local s socket

	pkill -x sway 2>/dev/null; pkill -x labwc 2>/dev/null; sleep 2
	printf 'output HEADLESS-1 mode %sx%s\n' "$w" "$h" > "$QUI/sway.conf"

	case $compositore in
	sway)
		nohup setsid env WLR_BACKENDS=headless WLR_HEADLESS_OUTPUTS=1 XDG_CURRENT_DESKTOP=sway \
		    sway -c "$QUI/sway.conf" >"$QUI/sway.log" 2>&1 </dev/null &
		;;
	labwc)
		nohup setsid env WLR_BACKENDS=headless WLR_HEADLESS_OUTPUTS=1 \
		    labwc >"$QUI/labwc.log" 2>&1 </dev/null &
		;;
	esac
	sleep 7

	socket=$(ls -t /run/user/1000/wayland-* 2>/dev/null | grep -v lock | grep -v kwin | grep -v wayland-0 | head -1)
	socket=$(basename "$socket")
	[ -z "$socket" ] && { echo "# $compositore ${w}x${h}: nessun socket"; return; }

	WAYLAND_DISPLAY=$socket stdbuf -oL weston-simple-egl -f -o >"$QUI/s-wlr.log" 2>&1 &
	s=$!
	sleep 2
	WAYLAND_DISPLAY=$socket "$QUI/misura-wlroots" --durata "$DURATA" --scarto 5 \
	    --etichetta "$compositore-${w}x${h}-shm" 2>>"$QUI/altri.log" | grep '^RIGA'
	echo "# client su $compositore ${w}x${h}: $(grep -o '[0-9.]* fps' "$QUI/s-wlr.log" | tail -1)"
	kill $s 2>/dev/null
	sleep 1
}

echo "# etichetta misura colore fps_dichiarato strada tipo fps_misurati fotogrammi secondi buffer danno_pieno danno_parziale danno_assente salti fence min p50 p95 max"
for m in "${MISURE[@]}"; do
	cella_kwin "${m%x*}" "${m#*x}"
done
cella_kwin 1920 1080 --dmabuf
for m in "${MISURE[@]}"; do
	cella_wlroots sway "${m%x*}" "${m#*x}"
done
cella_wlroots labwc 1920 1080
spegni
