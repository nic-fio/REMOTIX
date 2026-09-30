#!/bin/bash
#
# 17-t1c-guarda.sh — fase 17, T1c: un Chrome VERO sul server entra nella VM e
# guarda il desktop (`17-t1c-browser.py`), in un labwc senza schermo SUO.
#
#   (sul server, come nicfio)  bash 17-t1c-guarda.sh <macchina> <porta-inoltrata> [chrome|firefox]
#   es.  bash 17-t1c-guarda.sh debian13-gnome 7511
#   T1C_PROGRAMMA / T1C_EVIDENZE: un altro programma con le stesse opzioni (T8: t8-browser.py, che
#   resta collegato durante l'aggiornamento) e un'altra cartella delle evidenze.
#
# ⚠ 127.0.0.1 e non «localhost»: l'inoltro UDP di QEMU ascolta solo in IPv4, e
#   Chrome manda il QUIC a ::1 ⇒ `QUIC_PACKET_WRITE_ERROR -102` e «Opening
#   handshake failed» mentre la pagina (TCP) si apre lo stesso.  `[M]` 29 set.
# ⚠ Il labwc e' SUO (non quelli di 15-compositori.sh, che servono alla suite)
#   e rende sull'INTEGRATA Intel: la Radeon non si tocca.
# ⚠ Un browser alla volta nel labwc: una finestra di Chrome coperta non si
#   fotografa (15-compositori.sh).
set -u
m=${1:?macchina}; p=${2:?porta}; b=${3:-chrome}
QUI=$(cd "$(dirname "$0")" && pwd)
T1C=${T1C:-/media/REMOTIX/vm17/t1c}
R=/run/user/$(id -u)
mkdir -p "$T1C"

if ! { [ -f "$T1C/labwc.pid" ] && kill -0 "$(cat "$T1C/labwc.pid")" 2>/dev/null; }; then
	INTEL=""
	for r in /sys/class/drm/renderD*; do
		[ "$(basename "$(readlink -f "$r/device/driver")")" = i915 ] && INTEL=/dev/dri/$(basename "$r")
	done
	[ -n "$INTEL" ] || { echo "⛔ nessun nodo Intel: non accendo labwc sulla scheda sbagliata"; exit 2; }
	prima=$(ls "$R" | grep -E '^wayland-[0-9]+$' | sort)
	env -u WAYLAND_DISPLAY -u DISPLAY WLR_BACKENDS=headless WLR_LIBINPUT_NO_DEVICES=1 \
		WLR_RENDER_DRM_DEVICE="$INTEL" XDG_RUNTIME_DIR="$R" setsid labwc </dev/null >"$T1C/labwc.log" 2>&1 &
	echo $! >"$T1C/labwc.pid"
	n=""
	for _ in $(seq 1 40); do
		n=$(comm -13 <(echo "$prima") <(ls "$R" | grep -E '^wayland-[0-9]+$' | sort) | head -1)
		[ -n "$n" ] && break; sleep 0.25
	done
	[ -n "$n" ] || { echo "⛔ labwc non ha aperto un socket"; exit 2; }
	echo "$n" >"$T1C/labwc.sock"; sleep 0.5
	u=$(WAYLAND_DISPLAY=$n wlr-randr | awk 'NR==1{print $1}')
	WAYLAND_DISPLAY=$n wlr-randr --output "$u" --custom-mode 2560x1440
fi

exec env XDG_RUNTIME_DIR="$R" WAYLAND_DISPLAY="$(cat "$T1C/labwc.sock")" MOZ_ENABLE_WAYLAND=1 \
	REMOTIX_CHROME_OPZIONI="--ozone-platform=wayland --disable-backgrounding-occluded-windows --disable-renderer-backgrounding --disable-background-timer-throttling" \
	python3 "${T1C_PROGRAMMA:-$QUI/17-t1c-browser.py}" --banchi "${REMOTIX_BANCHI:-/media/REMOTIX/src/controllo/banchi}" \
	--host 127.0.0.1 --porta "$p" --utente "${T1C_UTENTE:-prova}" --parola "${REMOTIX_PAROLA_PROVA:-prova2026}" \
	--browser "$b" --evidenze "${T1C_EVIDENZE:-$T1C/esiti/$m-$b}" --porte-base $((3200 + p % 100 * 2))
