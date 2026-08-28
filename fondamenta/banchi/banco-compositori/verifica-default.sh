#!/bin/bash
#
# verifica-default.sh — il 60 e' nel programma: fa davvero effetto?
#
# Rimette /etc/default/remotix com'era (senza `--fotogrammi`), distribuisce il
# binario nuovo, e misura la catena intera con la SOLA configurazione
# predefinita.  Se il numero e' quello di ieri sera con `--fotogrammi 60`
# scritto a mano, il valore e' passato nel codice davvero.
#
set -uo pipefail

QUI=/media/REMOTIX/tmp/banco-compositori
FIFO=$QUI/.credenziale
DISPLAY_CLI=:120

export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus

printf 'Password: ' >&2
read -r PW
[ -n "$PW" ] || { echo "# nessuna credenziale"; exit 1; }

pulisci()
{
	pkill -f weston-simple-egl 2>/dev/null
	pkill -x xfreerdp3 2>/dev/null
	pkill -f "^Xvfb $DISPLAY_CLI" 2>/dev/null
	rm -f "$FIFO"
}
trap pulisci EXIT

# 1. la configurazione torna quella di sempre: nessun --fotogrammi
printf 'REMOTIX_OPZIONI=--registro diagnostica --porta 3392\nREMOTIX_DMABUF=0\n' |
    sudo tee /etc/default/remotix >/dev/null

# 2. il binario nuovo
bash /media/REMOTIX/server.sh copia >/dev/null 2>&1
sleep 4
rm -f ~/remotix.log
sudo systemctl restart remotix.service
sleep 4
echo "# riga di comando: $(ps -o args= -p "$(systemctl show -p MainPID --value remotix.service)")"

# 3. un client vero, credenziale su FIFO
rm -f "$FIFO"; mkfifo -m 600 "$FIFO"
( printf '\n%s\n' "$PW" > "$FIFO" ) &
pgrep -f "^Xvfb $DISPLAY_CLI" >/dev/null || {
	setsid nohup Xvfb "$DISPLAY_CLI" -screen 0 2400x1400x24 -nolisten tcp >/dev/null 2>&1 </dev/null &
	sleep 3
}
setsid nohup env DISPLAY=$DISPLAY_CLI xfreerdp3 /v:127.0.0.1:3392 /gfx:avc420 \
    /cert:ignore /sec:tls "/u:$(id -un)" /from-stdin /size:1920x1080 \
    /log-level:WARN <"$FIFO" >"$QUI/verifica-client.log" 2>&1 &
sleep 12
pgrep -x xfreerdp3 >/dev/null && echo "#   client collegato" || { echo "#   CLIENT NON PARTITO"; exit 1; }

for i in $(seq 1 20); do pgrep -x gnome-shell >/dev/null && break; sleep 1; done
sleep 3
setsid nohup env WAYLAND_DISPLAY=wayland-0 weston-simple-egl -f -o \
    >"$QUI/verifica-scena.log" 2>&1 </dev/null &
sleep 5

leggi() { grep -F 'rete: RTT' ~/remotix.log | tail -1 | grep -oE 'spediti [0-9]+' | grep -oE '[0-9]+'; }
a=$(leggi); t0=$(date +%s)
sleep 20
b=$(leggi); t1=$(date +%s)
dt=$(( t1 - t0 )); [ "$dt" -lt 1 ] && dt=1
df=$(( ${b:-0} - ${a:-0} ))
printf 'PREDEFINITO\t1920x1080\tfotogrammi=%s\tsecondi=%s\tfps=%s.%s\n' \
    "$df" "$dt" $(( df * 10 / dt / 10 )) $(( df * 10 / dt % 10 ))
