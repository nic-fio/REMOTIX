#!/bin/bash
# Mette un file negli appunti del CLIENT.  $1 = tipo X, $2 = file
set -u
pkill -x xclip 2>/dev/null
setsid nohup env DISPLAY=:110 xclip -selection clipboard -t "$1" -i "$2" >/dev/null 2>&1 &
sleep 2
echo "   il client tiene ($1)"
