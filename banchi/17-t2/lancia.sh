#!/bin/sh
# lancia.sh DESKTOP ESPERIMENTI... — sul server, nell'ambiente di 15-una.sh
cd /media/REMOTIX/tmp/t2 || exit 1
u=$(id -u); D=$1
W=$(cat /run/user/$u/15-compositori/$D)
exec env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$W REMOTIX_SCHERMO_ANNIDATO=1 REMOTIX_SUL_SERVER=1 REMOTIX_CHROME_OPZIONI="--ozone-platform=wayland" MOZ_ENABLE_WAYLAND=1 python3 -u t2-misura.py "$@"
