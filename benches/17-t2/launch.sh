#!/bin/sh
# launch.sh DESKTOP EXPERIMENTS... — on the server, in the environment of 15-one.sh
cd /media/REMOTIX/tmp/t2 || exit 1
u=$(id -u); D=$1
W=$(cat /run/user/$u/15-compositori/$D)
exec env XDG_RUNTIME_DIR=/run/user/$u WAYLAND_DISPLAY=$W REMOTIX_NESTED_SCREEN=1 REMOTIX_ON_SERVER=1 REMOTIX_CHROME_OPTIONS="--ozone-platform=wayland" MOZ_ENABLE_WAYLAND=1 python3 -u t2-measure.py "$@"
