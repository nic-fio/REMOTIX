#!/bin/bash
# Mette qualcosa negli appunti del CLIENT.  $1 = tipo, $2 = file
#
# ⚠ `xclip` RESTA IN VITA a tenere la selezione: va staccato, o la sessione che
#   lo ha avviato non si chiude piu' — la stessa regola di fase 5 sul pilotare
#   i due ambienti, qui applicata agli appunti.
set -u
pkill -x xclip 2>/dev/null
setsid nohup env DISPLAY=:110 xclip -selection clipboard -t "$1" -i "$2" >/dev/null 2>&1 &
sleep 2
echo "   il client ha copiato ($1)"
