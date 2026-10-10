#!/bin/bash
#
# 04-in8-costruisci.sh — ⛔ RUNS INSIDE THE CONTAINER.  Builds the two benches
# of the F4-IN-8 study («which size does Mutter accept»).
#
# ⛔ It exists because of the house rule «a file has no levels of quoting»: a
#    `$(pkg-config …)` written inside `ssh → enter.sh → bash -c` is expanded by
#    the WRONG shell — the host's, where `pkg-config` is not there.
#
#   1. copy `04-in8-misura.c` and `04-in8-parita.c` into /media/REMOTIX/src/08-misura/
#   2. sudo -S -p 'Password:' bash /media/REMOTIX/enter.sh "bash /srv/src/08-misura/04-in8-costruisci.sh"
#   3. and then they are LAUNCHED ON THE HOST, not in the container: they want the
#      session bus and the PipeWire socket of the user who owns the GNOME session.
#
#        XDG_RUNTIME_DIR=/run/user/1000 \
#        DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
#        ./gauge 2133 772 1601 903 5
#
# ⛔⛔ AND A SIZE ABOVE 16384 IN EITHER OF THE TWO DIMENSIONS **KILLS
#     GNOME-SHELL** (`[M]` 14 Aug 2026, see `F4-IN-8`): do not try it on a
#     session someone needs.
set -uo pipefail
HERE=/srv/src/08-misura

rm -f "$HERE/gauge" "$HERE/parita"
cc -O2 -Wall -o "$HERE/gauge" "$HERE/04-in8-misura.c" \
   $(pkg-config --cflags --libs gio-2.0 libpipewire-0.3) 2>&1 | tail -30
cc -O2 -Wall -o "$HERE/parita" "$HERE/04-in8-parita.c" \
   $(pkg-config --cflags --libs libavcodec libavutil) 2>&1 | tail -30
ls -la "$HERE/gauge" "$HERE/parita" 2>/dev/null || echo "⛔ NOT built"
