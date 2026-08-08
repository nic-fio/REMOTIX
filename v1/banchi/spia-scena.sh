#!/bin/bash
# Una scena il cui ORDINE si legge a macchina: lo schermo si riempie di grigi
# via via piu' chiari (colori 232..255 del terminale, che sono una rampa).
# Se un fotogramma consegnato e' piu' SCURO del precedente, viene dal passato.
export XDG_RUNTIME_DIR=/run/user/1000
export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus
export WAYLAND_DISPLAY=wayland-0
pkill -f 'while true; do date' 2>/dev/null
pkill -x gnome-terminal-server 2>/dev/null
sleep 1
setsid nohup gnome-terminal --full-screen -- bash -c \
    'while true; do for i in $(seq 232 255); do printf "\033[48;5;%dm\033[2J" "$i"; sleep 0.12; done; done' \
    >/dev/null 2>&1 &
sleep 4
pgrep -x gnome-terminal-server >/dev/null && echo "scena a rampa avviata" || echo "terminale NON partito"
