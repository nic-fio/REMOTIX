#!/bin/bash
# La scena che il difetto lo provoca davvero: Firefox che si apre e si chiude.
set -u
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
pkill -f 'seq 232' 2>/dev/null
pkill -x gnome-terminal-server 2>/dev/null
sleep 1
setsid nohup firefox >/dev/null 2>&1 &
sleep 12
echo "firefox aperto"
