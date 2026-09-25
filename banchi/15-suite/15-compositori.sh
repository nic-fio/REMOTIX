#!/bin/bash
# 15-compositori.sh — UN labwc senza schermo PER DESKTOP, per i browser del giro.
#
#   (sul server, come nicfio)  bash 15-compositori.sh accendi|spegni|stato
#
# ⛔ Perche': coi quattro desktop in parallelo nello STESSO labwc, le finestre di
#    Chrome si coprono a vicenda, e una finestra di Chrome coperta non ridipinge:
#    `Page.captureScreenshot` resta appeso (misurato dai gruppi G2 e G8, 25 set
#    2026: una foto appesa 17 minuti, tre corse finite a 900 s).  Firefox si
#    fotografa anche coperto, Chrome no.  ⇒ Ogni desktop ha il suo compositore,
#    e nel suo compositore c'e' un browser alla volta.
#
# Il socket di ciascuno si scrive in $XDG_RUNTIME_DIR/15-compositori/<desktop>;
# 15-giro.py lo legge e lo passa come WAYLAND_DISPLAY.  3840x2160, come le
# specifiche (4K).
set -u
R=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
C="$R/15-compositori"
DESKTOP="gnome kde xfce lxqt"
mkdir -p "$C"

accendi() {
	for d in $DESKTOP; do
		if [ -f "$C/$d.pid" ] && kill -0 "$(cat "$C/$d.pid")" 2>/dev/null; then
			echo "$d: gia' acceso su $(cat "$C/$d")"; continue
		fi
		prima=$(ls "$R" | grep -E '^wayland-[0-9]+$' | sort)
		env -u WAYLAND_DISPLAY -u DISPLAY WLR_BACKENDS=headless WLR_LIBINPUT_NO_DEVICES=1 \
			WLR_RENDER_DRM_DEVICE=/dev/dri/renderD128 XDG_RUNTIME_DIR="$R" \
			setsid labwc </dev/null >"$C/$d.log" 2>&1 &
		echo $! >"$C/$d.pid"
		nuovo=""
		for _ in $(seq 1 40); do
			nuovo=$(comm -13 <(echo "$prima") <(ls "$R" | grep -E '^wayland-[0-9]+$' | sort) | head -1)
			[ -n "$nuovo" ] && break
			sleep 0.25
		done
		if [ -z "$nuovo" ]; then echo "$d: ⛔ labwc non ha aperto un socket"; continue; fi
		echo "$nuovo" >"$C/$d"
		sleep 0.5
		uscita=$(WAYLAND_DISPLAY=$nuovo wlr-randr 2>/dev/null | awk 'NR==1{print $1}')
		WAYLAND_DISPLAY=$nuovo wlr-randr --output "$uscita" --custom-mode 3840x2160 2>&1
		echo "$d: ⭐ $nuovo ($uscita 3840x2160), pid $(cat "$C/$d.pid")"
	done
}

spegni() {
	for d in $DESKTOP; do
		[ -f "$C/$d.pid" ] && kill "$(cat "$C/$d.pid")" 2>/dev/null
		rm -f "$C/$d" "$C/$d.pid"
		echo "$d: spento"
	done
}

stato() {
	for d in $DESKTOP; do
		if [ -f "$C/$d.pid" ] && kill -0 "$(cat "$C/$d.pid")" 2>/dev/null; then
			echo "$d: acceso su $(cat "$C/$d") — $(WAYLAND_DISPLAY=$(cat "$C/$d") wlr-randr 2>/dev/null | grep -m1 current)"
		else
			echo "$d: spento"
		fi
	done
}

case "${1:-stato}" in
accendi) accendi ;; spegni) spegni ;; stato) stato ;;
*) echo "uso: $0 accendi|spegni|stato"; exit 2 ;;
esac
