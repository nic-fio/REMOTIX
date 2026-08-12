#!/bin/bash
# misura-wlroots-prova-L1.sh — ⛔ I DUE INGRESSI CHE FACEVANO USCIRE 0.
#
# Gira su NIC-OS, sull'host, e non tocca ne' la sessione GNOME ne' le porte
# 7448 e 7501 (le conta prima e dopo, e se il numero cambia si vede).
#
# Serve a dimostrare la cura della lacuna L1: fino al 12 agosto 2026
# `misura-wlroots` **ritornava 0 in ogni percorso che arrivasse alla stampa**.
# Qui i due ingressi costruiti passano PRIMA al binario di ieri
# (`misura-wlroots.prima-di-L1`, tenuto da parte come `misura-cattura.prima-di-D7`)
# e POI a quello curato, e i due esiti si leggono uno sotto l'altro:
#
#   caso 1  `--durata 0 --scarto 0`   il formato non fa in tempo a negoziarsi
#           prima: `RIGA … 0x0 … 0.00`  uscita 0
#           dopo:  `GUASTO … nessun formato mai negoziato`  uscita 2
#   caso 2  labwc ucciso al 3° secondo di una cella da 20 s
#           prima: `RIGA … 1280x720 … 0.00`  uscita 0  (185 arrivati e buttati)
#           dopo:  `GUASTO … la connessione al compositore e' caduta durante
#                  la misura`  uscita 2
#
# ⚠ Il controllo positivo di questa cura NON sta qui: sta in
#   `banchi/00-c1-wlroots.sh`, che sullo stesso labwc misura 61,15 fps ed esce
#   0.  Uno strumento che imparasse a dire «no» sempre sarebbe peggiorato, non
#   curato.
set -uo pipefail
QUI=/media/REMOTIX/tmp/banco-compositori
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

pulisci() { pkill -x labwc 2>/dev/null; for _ in $(seq 1 40); do pgrep -x labwc >/dev/null || break; sleep 0.25; done; }
trap pulisci EXIT
pulisci

echo "== le porte da non toccare, PRIMA: $(ss -ltn | grep -cE ':(7448|7501) ')"

PRIMA_SOCKET=$(ls "$XDG_RUNTIME_DIR"/wayland-* 2>/dev/null | grep -v '\.lock$' | sort)
nohup setsid env WLR_BACKENDS=headless WLR_HEADLESS_OUTPUTS=1 labwc >"$QUI/L1-labwc.log" 2>&1 </dev/null &
SOCKET=
for _ in $(seq 1 60); do
	DOPO=$(ls "$XDG_RUNTIME_DIR"/wayland-* 2>/dev/null | grep -v '\.lock$' | sort)
	N=$(comm -13 <(printf '%s\n' "$PRIMA_SOCKET") <(printf '%s\n' "$DOPO") | head -1)
	[ -n "$N" ] && { SOCKET=$(basename "$N"); break; }
	sleep 0.25
done
[ -n "$SOCKET" ] || { echo "⛔ labwc non e' partito"; exit 9; }
echo "  labwc in piedi, socket $SOCKET"
WAYLAND_DISPLAY=$SOCKET stdbuf -oL weston-simple-egl -f -o >"$QUI/L1-scena.log" 2>&1 &
PID_SCENA=$!
sleep 2

giro() # $1 = binario, $2 = etichetta
{
	echo
	echo "  --- $2 : --durata 0 --scarto 0 (il formato non fa in tempo a negoziarsi)"
	WAYLAND_DISPLAY=$SOCKET "$QUI/$1" --durata 0 --scarto 0 --etichetta "L1-caso1"
	echo "      uscita=$?"
}
giro misura-wlroots.prima-di-L1 "PRIMA"
giro misura-wlroots            "DOPO "

# ── Caso 2: il compositore ucciso al terzo secondo di una cella da 20 ────────
caso2() # $1 = binario, $2 = etichetta
{
	echo
	echo "  --- $2 : cella da 20 s, labwc ucciso al terzo secondo"
	pulisci
	nohup setsid env WLR_BACKENDS=headless WLR_HEADLESS_OUTPUTS=1 labwc >"$QUI/L1-labwc.log" 2>&1 </dev/null &
	local s=
	for _ in $(seq 1 60); do
		D=$(ls "$XDG_RUNTIME_DIR"/wayland-* 2>/dev/null | grep -v '\.lock$' | sort)
		N=$(comm -13 <(printf '%s\n' "$PRIMA_SOCKET") <(printf '%s\n' "$D") | head -1)
		[ -n "$N" ] && { s=$(basename "$N"); break; }
		sleep 0.25
	done
	[ -n "$s" ] || { echo "⛔ labwc non e' partito"; return 9; }
	WAYLAND_DISPLAY=$s stdbuf -oL weston-simple-egl -f -o >"$QUI/L1-scena.log" 2>&1 &
	local ps=$!
	sleep 1
	( sleep 3; pkill -x labwc ) &
	WAYLAND_DISPLAY=$s "$QUI/$1" --durata 20 --scarto 5 --etichetta "L1-caso2"
	echo "      uscita=$?"
	kill "$ps" 2>/dev/null
	wait 2>/dev/null
}
caso2 misura-wlroots.prima-di-L1 "PRIMA"
caso2 misura-wlroots            "DOPO "

echo
echo "== le porte da non toccare, DOPO: $(ss -ltn | grep -cE ':(7448|7501) ')"
