#!/bin/bash
#
# misure6-kde.sh — le prestazioni della cattura **sulla Intel integrata**, che è la
# GPU scelta dall'utente l'8 agosto 2026.  I numeri di R32 e quelli del 7 agosto
# sono della Radeon: qui si rifanno dove conta.
#
# La Radeon si nasconde al solo compositore con un namespace di monti privato
# (nessun cambiamento al sistema).  La scena e il misuratore stanno fuori: il
# cliente prende la GPU che il compositore annuncia nel dmabuf, cioè la Intel.
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
NODO="$QUI/nodo-kwin"; MIS="$QUI/misura-cattura"
LOG=/tmp/kde-m6; rm -rf "$LOG"; mkdir -p "$LOG"
export LANG=C.UTF-8 LC_ALL=C.UTF-8 XDG_MENU_PREFIX=plasma-
[ -n "${XDG_RUNTIME_DIR:-}" ] && [ -d "${XDG_RUNTIME_DIR:-}" ] || {
    export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"; }
BUS="unix:path=/run/user/$(id -u)/bus"
SOCK=wayland-kde
U=$(id -u); G=$(id -g)
: > /tmp/nodo-negato; chmod 000 /tmp/nodo-negato

echo "== una richiesta di password sola =="
sudo -S -p 'Password: ' -v; echo "   validato: $?"

# $1 = larghezza  $2 = altezza  $3 = secondi di vita del compositore
avvia_intel() {
    rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
    sudo unshare --mount --propagation private bash -c "
        mount --bind /tmp/nodo-negato /dev/dri/renderD129
        setpriv --reuid $U --regid $G --init-groups \
          env LANG=C.UTF-8 XDG_MENU_PREFIX=plasma- HOME=$HOME PATH=/usr/bin:/bin \
              XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS=$BUS \
          kwin_wayland --virtual --width $1 --height $2 --no-lockscreen --socket=$SOCK \
          > $LOG/kwin-$1x$2.log 2>&1 &
        K=\$!
        for i in \$(seq 40); do [ -S $XDG_RUNTIME_DIR/$SOCK ] && break; sleep 0.25; done
        sleep $3
        kill \$K 2>/dev/null; wait 2>/dev/null" &
    NSPID=$!
    sleep 5
}

GEOMETRIE=${GEOMETRIE:-"1280 720|1920 1080"}
IFS='|' read -ra ELENCO <<< "$GEOMETRIE"
for geom in "${ELENCO[@]}"; do
    set -- $geom
    W=$1; H=$2
    echo
    echo "################ ${W}x${H} sulla Intel ################"
    avvia_intel "$W" "$H" 46
    echo -n "   renderer: "
    gdbus call --session --dest org.kde.KWin --object-path /KWin \
        --method org.kde.KWin.supportInformation 2>/dev/null \
        | grep -aoE 'OpenGL renderer string: [^\\]*' | head -1
    SCENA=$(command -v weston-simple-egl || true)
    if [ -n "$SCENA" ]; then
        WAYLAND_DISPLAY="$SOCK" "$SCENA" > "$LOG/scena-$W.log" 2>&1 &
        SP=$!; sleep 2
        echo "   scena in movimento avviata"
    else SP=; echo "   ⚠ nessuna scena: i fotogrammi saranno 0"; fi

    WAYLAND_DISPLAY="$SOCK" "$NODO" > "$LOG/nodo-$W.log" 2>&1 &
    NP=$!; sleep 2
    NODE=$(grep -aoE 'nodo PipeWire [0-9]+' "$LOG/nodo-$W.log" | grep -oE '[0-9]+$' | head -1)
    echo "   nodo PipeWire: ${NODE:-nessuno}"
    if [ -n "${NODE:-}" ]; then
        for modo in "--dmabuf" ""; do
            etichetta=$([ -n "$modo" ] && echo "DMA-BUF" || echo "memoria")
            timeout 30 "$MIS" --nodo "$NODE" --larghezza "$W" --altezza "$H" --fps 60 --durata 10 $modo \
                > "$LOG/mis-$W-$etichetta.log" 2>&1
            echo "   ---- $etichetta:"
            grep -aiE 'fotogrammi [0-9]|danno:|salti|intervalli|p50|mediana' "$LOG/mis-$W-$etichetta.log" \
                | head -4 | sed 's/^/         /'
        done
    fi
    [ -n "${SP:-}" ] && kill $SP 2>/dev/null
    kill $NP 2>/dev/null
    wait $NSPID 2>/dev/null
    sleep 1
done

rm -f /tmp/nodo-negato
sudo pkill -x kwin_wayland 2>/dev/null
pkill -x nodo-kwin 2>/dev/null; pkill -x misura-cattura 2>/dev/null
sleep 0.5
echo
echo "residui: kwin=$(pgrep -xc kwin_wayland || true)"
echo "montaggi residui: $(grep -c nodo-negato /proc/mounts || true)"
echo "fine. registri in $LOG"
