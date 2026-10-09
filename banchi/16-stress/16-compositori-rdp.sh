#!/bin/bash
# 16-compositori-rdp.sh — UNO SCHERMO FINTO (Xvfb) PER UTENTE della salita xrdp (fasi/20 §7.1).
#
#   (sul server, come nicfio)
#   bash 16-compositori-rdp.sh accendi N MISURA    u00 (il controllo corto) + u01…uNN
#   bash 16-compositori-rdp.sh spegni              tutti quelli di questo file
#   bash 16-compositori-rdp.sh stato
#
#   MISURA = 4k · 3k · 2k · fhd (come 16-compositori.sh), oppure LARGOxALTO
#
# ⭐ E' il gemello di 16-compositori.sh per il confronto con xrdp: al posto del labwc
#    senza schermo (dove gira il browser) un Xvfb, dove gira xfreerdp3 a tutto schermo.
#    Ognuno il suo, per la stessa ragione: un cliente coperto da un altro smette di
#    disegnare.  Il display di ciascuno (":2NN") si scrive in
#    $XDG_RUNTIME_DIR/16-compositori-rdp/uNN; 16-salita.py --sistema xrdp lo legge e lo
#    passa all'attore (--display).
# ⛔ fasi/20 §7.7: gli Xvfb nascono con oom_score_adj 800 — se il kernel deve uccidere
#    qualcosa, uccide un cliente (un gradino rosso), non sshd ne' la coda.
# ⚠ Lo schermo e' a 24 bit, la stessa misura del desktop remoto: FreeRDP a tutto
#    schermo chiede al server un desktop grande quanto l'Xvfb, e la foto e' 1:1.
set -u
R=${XDG_RUNTIME_DIR:-/run/user/$(id -u)}
C="$R/16-compositori-rdp"
mkdir -p "$C"
BASE_DISPLAY=${REMOTIX_16_DISPLAY_BASE:-200}

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

vivo() { [ -f "$C/$1.pid" ] && kill -0 "$(cat "$C/$1.pid")" 2>/dev/null; }

misura_di() {  # :N ⇒ LARGOxALTO
	DISPLAY=$1 xdpyinfo 2>/dev/null | awk '/dimensions:/{print $2; exit}'
}

accendi_uno() {  # uNN WxH
	local n=$1 m=$2 k d
	k=$((10#${n#u}))
	d=":$((BASE_DISPLAY + k))"
	if vivo "$n"; then
		if [ "$(misura_di "$d")" = "$m" ]; then
			echo "$n: gia' acceso su $d ($m)"
			return 0
		fi
		# ⚠ Xvfb non cambia misura: si spegne e si riaccende
		kill "$(cat "$C/$n.pid")" 2>/dev/null
		sleep 0.5
	fi
	rm -f "$C/$n" "$C/$n.pid" "/tmp/.X11-unix/X${d#:}" "/tmp/.X${d#:}-lock" 2>/dev/null
	setsid Xvfb "$d" -screen 0 "${m}x24" -nolisten tcp -noreset </dev/null >"$C/$n.log" 2>&1 &
	echo $! >"$C/$n.pid"
	echo 800 >"/proc/$(cat "$C/$n.pid")/oom_score_adj" 2>/dev/null
	for _ in $(seq 1 40); do
		[ "$(misura_di "$d")" = "$m" ] && break
		sleep 0.25
	done
	if [ "$(misura_di "$d")" != "$m" ]; then
		echo "$n: ⛔ Xvfb $d non risponde a $m ($(tail -2 "$C/$n.log" | tr '\n' ' '))"
		kill "$(cat "$C/$n.pid")" 2>/dev/null
		rm -f "$C/$n.pid"
		return 1
	fi
	echo "$d" >"$C/$n"
	echo "$n: ⭐ Xvfb $d ($m), pid $(cat "$C/$n.pid")"
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
	echo "accesi: $quanti"
}

case "${1:-stato}" in
accendi) accendi "${2:-}" "${3:-4k}" ;;
spegni) spegni ;;
stato) stato ;;
*) echo "uso: $0 accendi N MISURA | spegni | stato"; exit 2 ;;
esac
