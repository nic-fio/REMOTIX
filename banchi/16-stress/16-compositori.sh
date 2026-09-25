#!/bin/bash
# 16-compositori.sh — UN labwc senza schermo PER UTENTE della salita (fase 16).
#
#   (sul server, come nicfio)
#   bash 16-compositori.sh accendi N MISURA    u00 (il controllo corto) + u01…uNN
#   bash 16-compositori.sh spegni              tutti quelli di questo file
#   bash 16-compositori.sh stato
#
#   MISURA = 4k (3840x2160) · 3k (3200x1800) · 2k (2560x1440) · fhd (1920x1080)
#            (fasi/16-stress-e-capacita.md §8), oppure LARGOxALTO
#
# ⛔ Perche' uno per utente (fasi/16 §4): una finestra di Chrome COPERTA da
#    un'altra smette di disegnare (`[M]` fase 15, G2/G8: foto appese fino a 17
#    min) ⇒ con 16 finestre 4K nello stesso compositore misureremmo quello.
#    Ogni browser ha il suo compositore, e nel suo compositore e' solo.
#
# Il socket di ciascuno si scrive in $XDG_RUNTIME_DIR/16-compositori/uNN;
# 16-salita.py lo legge e lo passa all'attore (--wayland) e al controllo corto.
# `u00` e' del CONTROLLO CORTO (§7), che entra e se ne va a ogni livello.
#
# ⛔ NON tocca i labwc di 15-compositori.sh (li usano altri): conosce solo i
#    pid scritti nella SUA cartella.  «accendi» e' ripetibile: quelli gia'
#    accesi restano (salgono i gradini senza spegnere nessuno), la misura si
#    rimette se e' cambiata.
set -u
R=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
C="$R/16-compositori"
mkdir -p "$C"

# ⚠ LA SCHEDA DEI COMPOSITORI: `renderD128`/`renderD129` si scambiano fra due
#   avvii (11-accendi.sh, «la Radeon dentro NON ESISTE»), e dal 25 set sul
#   server c'e' anche la RX 6800.  ⇒ La Intel integrata si trova per INDIRIZZO
#   PCI (driver i915/xe), come fa 11-accendi.sh; REMOTIX_16_RENDER la sceglie
#   da fuori (la campagna Radeon).  Si scrive in $C/render.
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
	[ -n "$u" ] || { echo "nessuna uscita"; return 1; }
	WAYLAND_DISPLAY=$1 wlr-randr --output "$u" --custom-mode "$2" 2>&1
}

misura_di() {  # socket ⇒ WxH corrente
	WAYLAND_DISPLAY=$1 wlr-randr 2>/dev/null | awk '/current/{print $1; exit}'
}

accendi_uno() {  # uNN WxH
	local n=$1 m=$2 prima nuovo
	if vivo "$n"; then
		s=$(cat "$C/$n")
		if [ "$(misura_di "$s")" != "$m" ]; then
			metti_misura "$s" "$m" >/dev/null
			echo "$n: gia' acceso su $s, misura rimessa a $m ($(misura_di "$s"))"
		else
			echo "$n: gia' acceso su $s ($m)"
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
		# ⭐ il socket del SUO pid (ss -xlp): se un altro labwc nasce nello
		#   stesso istante (altri agenti, 15-compositori) la differenza sbaglierebbe
		nuovo=$(ss -xlpn 2>/dev/null | grep "pid=$(cat "$C/$n.pid")," \
			| grep -oE "$R/wayland-[0-9]+" | head -1 | xargs -r basename)
		[ -n "$nuovo" ] || nuovo=$(comm -13 <(echo "$prima") \
			<(ls "$R" | grep -E '^wayland-[0-9]+$' | sort) | head -1)
		[ -n "$nuovo" ] && break
		sleep 0.25
	done
	if [ -z "$nuovo" ]; then
		echo "$n: ⛔ labwc non ha aperto un socket ($(tail -2 "$C/$n.log" | tr '\n' ' '))"
		kill "$(cat "$C/$n.pid")" 2>/dev/null
		rm -f "$C/$n.pid"
		return 1
	fi
	echo "$nuovo" >"$C/$n"
	echo "$RENDER" >"$C/render"
	for _ in $(seq 1 20); do [ -n "$(uscita_di "$nuovo")" ] && break; sleep 0.25; done
	metti_misura "$nuovo" "$m" >/dev/null
	if [ "$(misura_di "$nuovo")" != "$m" ]; then
		echo "$n: ⛔ $nuovo acceso ma la misura e' «$(misura_di "$nuovo")» e non $m"
		return 1
	fi
	echo "$n: ⭐ $nuovo ($m), pid $(cat "$C/$n.pid")"
}

accendi() {
	local N=${1:-} M
	case "$N" in ''|*[!0-9]*) echo "uso: $0 accendi N MISURA"; exit 2 ;; esac
	M=$(misura "${2:-4k}") || { echo "misura sconosciuta: ${2:-}"; exit 2; }
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
		echo "$n: spento"
	done
	true
}

stato() {
	local quanti=0
	for f in "$C"/u[0-9][0-9]; do
		[ -e "$f" ] || continue
		n=$(basename "$f")
		if vivo "$n"; then
			echo "$n: acceso su $(cat "$f") — $(misura_di "$(cat "$f")")"
			quanti=$((quanti + 1))
		else
			echo "$n: ⚠ spento (resta il file)"
		fi
	done
	echo "accesi: $quanti · scheda dei compositori: $(cat "$C/render" 2>/dev/null || echo "$RENDER")"
}

case "${1:-stato}" in
accendi) accendi "${2:-}" "${3:-4k}" ;;
spegni) spegni ;;
stato) stato ;;
*) echo "uso: $0 accendi N MISURA | spegni | stato"; exit 2 ;;
esac
