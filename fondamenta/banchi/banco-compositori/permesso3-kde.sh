#!/bin/bash
# permesso3-kde.sh — quarto giro. Due domande sole:
#   (a) KService associa il nostro .desktop all'eseguibile?  Lo dice la categoria
#       KWIN_UTILS (`kwin/src/utils/serviceutils.h:40,46`), non kwin_core.
#   (b) M3a/M3b: i nodi DRM e le librerie del compositore, letti con sudo perche'
#       il kernel nasconde /proc di un altro processo a questo utente.
set -u
QUI=/media/REMOTIX/tmp/banco-compositori; NODO="$QUI/nodo-kwin"
LOG=/tmp/kde-p3; mkdir -p "$LOG"
export LANG=C.UTF-8 LC_ALL=C.UTF-8
[ -n "${XDG_RUNTIME_DIR:-}" ] || { export XDG_RUNTIME_DIR=/tmp/xdg-$(id -u); mkdir -p $XDG_RUNTIME_DIR; chmod 700 $XDG_RUNTIME_DIR; }
[ -S /run/user/$(id -u)/bus ] && export DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$(id -u)/bus
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM

echo "== cache sycoca presenti (una per locale!):"; ls -la ~/.cache/ksycoca6* 2>&1 | sed 's/^/   /'
echo "== il nostro file di sistema:"; grep -H . /usr/share/applications/remotix-banco.desktop 2>&1 | tail -3 | sed 's/^/   /'

avvia() { # $1 = etichetta, $2... = env
    rm -f $XDG_RUNTIME_DIR/wayland-kde{,.lock}
    env "${@:2}" QT_LOGGING_RULES='KWIN_UTILS.debug=true;kwin_core.debug=true' \
        kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen --socket=wayland-kde \
        > "$LOG/$1.log" 2>&1 &
    KP=$!
    for _ in $(seq 40); do [ -S $XDG_RUNTIME_DIR/wayland-kde ] && break; sleep 0.25; done; sleep 3
}

echo
echo "=== (a) il permesso, con KWIN_UTILS acceso ==="
avvia normale
WAYLAND_DISPLAY=wayland-kde "$NODO" --elenca > "$LOG/elenco.txt" 2>&1
grep -qi zkde_screencast "$LOG/elenco.txt" && echo "   verdetto: ✅ ANNUNCIATO" || echo "   verdetto: ⛔ negato"
echo "   KWIN_UTILS dice:"
grep -aiE 'KWIN_UTILS|could not find the desktop|interfaces found' "$LOG/normale.log" | tail -4 | sed 's/^/      /'
kill $KP 2>/dev/null; wait 2>/dev/null

echo
echo "=== (b) M3a/M3b sul compositore, con la scorciatoia (giro certificato) ==="
avvia certificato KWIN_WAYLAND_NO_PERMISSION_CHECKS=1
VERO=$(pgrep -nf 'kwin_wayland --virtual')
echo "   pid: $VERO"
echo -n "   M3a nodi DRM aperti: "
sudo -S -p 'Password: ' ls -l /proc/$VERO/fd 2>/dev/null | grep -oE '/dev/dri/[a-zA-Z0-9]+' | sort -u | tr '\n' ' '; echo
echo -n "   M3b rendering: "
sudo -S -p 'Password: ' grep -oE '[a-z_]+_dri\.so|libgbm\.so[^ ]*|libEGL[^ ]*so[^ ]*|llvmpipe' /proc/$VERO/maps 2>/dev/null | sort -u | tr '\n' ' '; echo
echo "   M3d il flusso:"
WAYLAND_DISPLAY=wayland-kde "$NODO" --virtuale 1280x720 > "$LOG/nodo.log" 2>&1 &
NP=$!; sleep 3
NODE=$(grep -aoE '\b[0-9]{2,}\b' "$LOG/nodo.log" | head -1)
echo "      nodo PipeWire: ${NODE:-nessuno}"
[ -n "${NODE:-}" ] && timeout 15 "$QUI/misura-cattura" --nodo "$NODE" --larghezza 1280 --altezza 720 --fps 60 2>&1 | grep -aiE 'tipo|fotogramm|fps|danno|disegno|dmabuf|memfd' | head -6 | sed 's/^/      /'
kill $NP $KP 2>/dev/null; wait 2>/dev/null
echo "fine."
