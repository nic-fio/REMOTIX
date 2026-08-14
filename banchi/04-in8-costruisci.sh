#!/bin/bash
#
# 04-in8-costruisci.sh — ⛔ GIRA DENTRO IL CONTENITORE.  Costruisce i due banchi
# dello studio F4-IN-8 («che misura accetta Mutter»).
#
# ⛔ Esiste per la regola di casa «un file non ha livelli di virgolette»: un
#    `$(pkg-config …)` scritto dentro `ssh → enter.sh → bash -c` lo espande la
#    shell SBAGLIATA — quella dell'host, dove `pkg-config` non c'e'.
#
#   1. copiare `04-in8-misura.c` e `04-in8-parita.c` in /media/REMOTIX/src/08-misura/
#   2. sudo -S -p 'Password:' bash /media/REMOTIX/enter.sh "bash /srv/src/08-misura/04-in8-costruisci.sh"
#   3. e poi si LANCIANO SULL'HOST, non nel contenitore: vogliono il bus di
#      sessione e il socket PipeWire dell'utente che ha la sessione GNOME.
#
#        XDG_RUNTIME_DIR=/run/user/1000 \
#        DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
#        ./misura 2133 772 1601 903 5
#
# ⛔⛔ E UNA MISURA SOPRA 16384 IN UNA QUALSIASI DELLE DUE DIMENSIONI **UCCIDE
#     GNOME-SHELL** (`[M]` 14 agosto 2026, vedi `F4-IN-8`): non provarla su una
#     sessione che serve a qualcuno.
set -uo pipefail
QUI=/srv/src/08-misura

rm -f "$QUI/misura" "$QUI/parita"
cc -O2 -Wall -o "$QUI/misura" "$QUI/04-in8-misura.c" \
   $(pkg-config --cflags --libs gio-2.0 libpipewire-0.3) 2>&1 | tail -30
cc -O2 -Wall -o "$QUI/parita" "$QUI/04-in8-parita.c" \
   $(pkg-config --cflags --libs libavcodec libavutil) 2>&1 | tail -30
ls -la "$QUI/misura" "$QUI/parita" 2>/dev/null || echo "⛔ NON costruiti"
