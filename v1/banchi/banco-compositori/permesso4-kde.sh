#!/bin/bash
#
# permesso4-kde.sh — quarto giro, senza i tre errori di banco del terzo:
#   · nessun `2>/dev/null` su sudo (fase 1 di PIANO.md): qui NON si usa sudo affatto
#   · `pgrep/pkill` ancorati con -x (fase 3), mai -f su un pattern che sta nella
#     riga di comando di questo stesso script
#   · solo opzioni vere di `misura-cattura`: --nodo --larghezza --altezza --fps
#
# Due domande:
#
#  (a) M1 — perche' il `.desktop` non autorizza.  Lo dice KWin stesso, nella
#      categoria KWIN_UTILS (`kwin/src/utils/serviceutils.h:40,46`), con due righe
#      che hanno cure opposte:
#         «Could not find the desktop file for <exe>»  → KService non associa
#         «Interfaces found for <exe> : ()»            → associa, campo vuoto
#
#  (b) M3a/M3b — GPU o software, senza sudo.  Il kernel nega /proc/<pid>/fd e
#      /maps perche' /usr/bin/kwin_wayland porta l'xattr `security.capability`
#      (verificato il 7 ago 2026): un binario con file capabilities e' non
#      dumpable.  Una COPIA del binario perde l'xattr, quindi la copia e'
#      leggibile dall'utente che la lancia.  Stesso codice, stesse librerie.
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
NODO="$QUI/nodo-kwin"
EXE=$(readlink -f "$NODO")
LOG=/tmp/kde-p4; rm -rf "$LOG"; mkdir -p "$LOG"

export LANG=C.UTF-8 LC_ALL=C.UTF-8
[ -n "${XDG_RUNTIME_DIR:-}" ] && [ -d "${XDG_RUNTIME_DIR:-}" ] || {
    export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"; }
[ -S "/run/user/$(id -u)/bus" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM

SOCK=wayland-kde
avvia() {   # $1 = etichetta, $2 = binario, resto = ambiente
    local nome="$1" bin="$2"; shift 2
    rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
    env "$@" QT_LOGGING_RULES='KWIN_UTILS.debug=true;kwin_core.debug=true' \
        "$bin" --virtual --width 1280 --height 720 --no-lockscreen --socket="$SOCK" \
        > "$LOG/$nome.log" 2>&1 &
    PID=$!
    local i
    for i in $(seq 40); do [ -S "$XDG_RUNTIME_DIR/$SOCK" ] && break; sleep 0.25; done
    sleep 2.5
    kill -0 "$PID" 2>/dev/null || { echo "   ⛔ non partito:"; tail -6 "$LOG/$nome.log" | sed 's/^/      /'; return 1; }
}
ferma() { kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null; }
verdetto() {
    if WAYLAND_DISPLAY="$SOCK" "$NODO" --elenca 2>&1 | grep -qi zkde_screencast
    then echo "✅ ANNUNCIATO"; else echo "⛔ negato"; fi
}

echo "== quel che KWin ha davanti:  exe cliente = $EXE"
echo "== il .desktop di sistema:"; sed -n '1,9p' /usr/share/applications/remotix-banco.desktop 2>&1 | sed 's/^/   /'
echo "== XDG_DATA_DIRS = ${XDG_DATA_DIRS:-(vuota → /usr/local/share:/usr/share)}"
echo

echo "=================== (a) M1: KWin dice perche' ==================="
if avvia a-permesso /usr/bin/kwin_wayland; then
    echo -n "   verdetto: "; verdetto
    echo "   righe di KWIN_UTILS / serviceutils:"
    grep -aiE 'could not find the desktop|interfaces found|wayland-interfaces|not in ' \
         "$LOG/a-permesso.log" | head -6 | sed 's/^/      /'
    echo "   (se qui sopra non c'e' nulla, KWin non ha nemmeno interrogato KService:"
    echo "    vuol dire che il filtro non e' arrivato al campo — grep di riserva:)"
    grep -aiE 'screencast|permission|denied|sycoca|kservice' "$LOG/a-permesso.log" | head -5 | sed 's/^/      /'
    ferma
fi

echo
echo "=================== (b) M3: GPU o software, senza sudo ==================="
cp /usr/bin/kwin_wayland "$QUI/kwin-nocap"
chmod +x "$QUI/kwin-nocap"
echo -n "   xattr della copia (deve essere vuota): "
python3 -c "import os,sys; print(os.listxattr(sys.argv[1]))" "$QUI/kwin-nocap"
if avvia b-nocap "$QUI/kwin-nocap" KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 \
        QT_PLUGIN_PATH=/usr/lib/x86_64-linux-gnu/qt6/plugins; then
    echo "   pid $PID (copia senza capabilities)"
    echo -n "   M3a nodi DRM aperti: "
    ls -l "/proc/$PID/fd" | grep -oE '/dev/dri/[a-zA-Z0-9]+' | sort -u | tr '\n' ' '; echo
    echo -n "   M3b rendering caricato: "
    grep -oE '[a-z0-9_]+_dri\.so|libgbm\.so[0-9.]*|libEGL[^ ]*\.so[0-9.]*|libgallium[^ ]*|llvmpipe' \
         "/proc/$PID/maps" | sort -u | tr '\n' ' '; echo
    echo -n "   M3b-bis (se la lettura fosse negata, qui l'errore): "
    head -1 "/proc/$PID/maps" >/dev/null && echo "lettura di /proc OK" || echo "NEGATA"
    echo -n "   verdetto permesso su questa copia: "; verdetto

    echo "   M3d il flusso:"
    WAYLAND_DISPLAY="$SOCK" "$NODO" --virtuale 1280x720 > "$LOG/nodo.log" 2>&1 &
    NP=$!; sleep 3
    NODE=$(grep -aoE '\b[0-9]{2,}\b' "$LOG/nodo.log" | head -1)
    echo "      nodo PipeWire: ${NODE:-nessuno}"; sed -n '1,3p' "$LOG/nodo.log" | sed 's/^/      | /'
    if [ -n "${NODE:-}" ]; then
        timeout 20 "$QUI/misura-cattura" --nodo "$NODE" --larghezza 1280 --altezza 720 --fps 60 \
            > "$LOG/mis.log" 2>&1
        grep -aiE 'tipo|fotogramm|fps|danno|disegno|dmabuf|memfd|buffer' "$LOG/mis.log" | head -8 | sed 's/^/      /'
    fi
    kill $NP 2>/dev/null
    ferma
    rm -f "$QUI/kwin-nocap"
fi

echo
pkill -x kwin_wayland; pkill -x kwin-nocap; pkill -x nodo-kwin; pkill -x misura-cattura
sleep 0.5
echo "residui kwin: $(pgrep -xc kwin_wayland 2>/dev/null || echo 0) / nocap: $(pgrep -xc kwin-nocap 2>/dev/null || echo 0)"
echo "fine. registri in $LOG"
