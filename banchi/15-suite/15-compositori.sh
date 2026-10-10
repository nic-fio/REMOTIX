#!/bin/bash
# 15-compositori.sh — ONE headless labwc PER DESKTOP, for the browsers of the round.
#
#   (on the server, as nicfio)  bash 15-compositori.sh accendi|spegni|stato
#
# ⛔ Why: with the four desktops in parallel in the SAME labwc, Chrome's windows
#    cover each other, and a covered Chrome window does not repaint:
#    `Page.captureScreenshot` stays hung (measured by groups G2 and G8, 25 Sep
#    2026: one photo hung for 17 minutes, three runs ended at 900 s).  Firefox can be
#    photographed even when covered, Chrome cannot.  ⇒ Each desktop has its own compositor,
#    and in its compositor there is one browser at a time.
#
# The socket of each one is written in $XDG_RUNTIME_DIR/15-compositori/<desktop>;
# 15-giro.py reads it and passes it as WAYLAND_DISPLAY.  3840x2160, like the
# specifications (4K).
set -u
R=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
C="$R/15-compositori"
# ⭐ «comune» = the labwc of the LONG tests (15-giro.py → compositore()): it has its own name, so
#    it does not depend on which socket is born first (1 Oct 2026: after a reboot «wayland-0»
#    was gnome's labwc, and the F-030 of the four desktops ended up under gnome's browser).
DESKTOP="gnome kde xfce lxqt comune"
mkdir -p "$C"

accendi() {
	for d in $DESKTOP; do
		if [ -f "$C/$d.pid" ] && kill -0 "$(cat "$C/$d.pid")" 2>/dev/null; then
			echo "$d: already on at $(cat "$C/$d")"; continue
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
		if [ -z "$nuovo" ]; then echo "$d: ⛔ labwc did not open a socket"; continue; fi
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
		echo "$d: off"
	done
}

stato() {
	for d in $DESKTOP; do
		if [ -f "$C/$d.pid" ] && kill -0 "$(cat "$C/$d.pid")" 2>/dev/null; then
			echo "$d: on at $(cat "$C/$d") — $(WAYLAND_DISPLAY=$(cat "$C/$d") wlr-randr 2>/dev/null | grep -m1 current)"
		else
			echo "$d: off"
		fi
	done
}

case "${1:-stato}" in
accendi) accendi ;; spegni) spegni ;; stato) stato ;;
*) echo "usage: $0 accendi|spegni|stato"; exit 2 ;;
esac
