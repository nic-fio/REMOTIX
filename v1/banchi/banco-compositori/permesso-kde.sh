#!/bin/bash
#
# permesso-kde.sh — perche' il `.desktop` non autorizza la cattura, e quale forma
# la autorizza.  Vedi `kde.md` §3.  Secondo giro: il primo ha detto «non
# annunciato», e prima di crederci si CERTIFICA il banco (`LEZIONI.md` §1.2).
#
# Ogni prova e' un avvio di KWin e una domanda sola:
#
#   0  con KWIN_WAYLAND_NO_PERMISSION_CHECKS=1   → il banco sa vedere il protocollo?
#   1  .desktop in ~/.local/share, NoDisplay=true, dopo kbuildsycoca6
#   2  .desktop senza NoDisplay
#   3  .desktop in /usr/share/applications (dove sta quello del portale)
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
NODO="$QUI/nodo-kwin"
EXE=$(readlink -f "$NODO")
LOG=/tmp/kde-permesso; mkdir -p "$LOG"

export LANG=C.UTF-8 LC_ALL=C.UTF-8
[ -n "${XDG_RUNTIME_DIR:-}" ] || { export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"; }
[ -S "/run/user/$(id -u)/bus" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM

scrivi_desktop() {   # $1 = percorso, $2 = "nodisplay" | "visibile"
    local dove="$1" nd="$2"
    mkdir -p "$(dirname "$dove")" 2>/dev/null
    {
        echo "[Desktop Entry]"
        echo "Type=Application"
        echo "Name=REMOTIX banco"
        [ "$nd" = nodisplay ] && echo "NoDisplay=true"
        echo "Terminal=false"
        echo "Exec=$EXE"
        echo "X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1"
    } > "$dove"
}

prova() {   # $1 = etichetta, $2 = attesa in s, resto = ambiente
    local nome="$1" attesa="$2"; shift 2
    rm -f "$XDG_RUNTIME_DIR/wayland-kde" "$XDG_RUNTIME_DIR/wayland-kde.lock"
    env "$@" kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen \
        --socket=wayland-kde > "$LOG/$nome.log" 2>&1 &
    local pid=$!
    for _ in $(seq 40); do [ -S "$XDG_RUNTIME_DIR/wayland-kde" ] && break; sleep 0.25; done
    sleep "$attesa"
    local esito="KWIN NON PARTITO"
    if kill -0 "$pid" 2>/dev/null; then
        if WAYLAND_DISPLAY=wayland-kde "$NODO" --elenca 2>&1 | grep -qi zkde_screencast; then
            esito="✅ ANNUNCIATO"
        else
            esito="⛔ negato"
        fi
    fi
    printf '%-56s %s\n' "$nome" "$esito"
    # dalla prova certificata si prendono anche le altre misure
    if [ "$nome" = "0-certificazione (NO_PERMISSION_CHECKS)" ] && kill -0 "$pid" 2>/dev/null; then
        local vero
        vero=$(pgrep -f 'kwin_wayland --virtual' | head -1)
        echo "   ---- misure prese sul giro certificato (pid $vero) ----"
        echo -n "   M3a nodi DRM aperti: "
        ls -l "/proc/$vero/fd" 2>/dev/null | grep -oE 'dri/[a-zA-Z0-9]+' | sort -u | tr '\n' ' '; echo
        echo -n "   M3b rendering caricato: "
        grep -oE 'iris_dri|radeonsi_dri|swrast_dri|llvmpipe|libgbm[^ ]*so|libEGL[^ ]*so' \
             "/proc/$vero/maps" 2>/dev/null | sort -u | tr '\n' ' '; echo
        echo -n "   M5 connectToEIS(7): "
        gdbus call --session --dest org.kde.KWin --object-path /org/kde/KWin/EIS/RemoteDesktop \
            --method org.kde.KWin.EIS.RemoteDesktop.connectToEIS 7 2>&1 | head -1
        echo "   M3d tipo di buffer del flusso:"
        WAYLAND_DISPLAY=wayland-kde "$NODO" --virtuale 1280x720 > "$LOG/nodo.log" 2>&1 &
        local npid=$!; sleep 3
        local nodo; nodo=$(grep -aoE '\b[0-9]{2,}\b' "$LOG/nodo.log" | head -1)
        echo "      nodo PipeWire: ${nodo:-nessuno} $(head -2 "$LOG/nodo.log" | tr '\n' ' ')"
        if [ -n "${nodo:-}" ]; then
            timeout 12 "$QUI/misura-cattura" --nodo "$nodo" --secondi 5 2>&1 | \
                grep -aiE 'tipo|fotogrammi|fps|danno|disegno' | sed 's/^/      /' | head -6
        fi
        kill $npid 2>/dev/null
    fi
    kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
}

echo "== esiste la cache dei .desktop?"
ls -la ~/.cache/ksycoca* /var/cache/ksycoca* 2>/dev/null | head -3 || echo "   nessuna cache ksycoca"
command -v kbuildsycoca6 >/dev/null && echo "   kbuildsycoca6: c'e'" || echo "   kbuildsycoca6: ASSENTE (pacchetto kservice non installato)"
echo

rm -f ~/.local/share/applications/remotix-banco.desktop
prova "0-certificazione (NO_PERMISSION_CHECKS)" 2 KWIN_WAYLAND_NO_PERMISSION_CHECKS=1

scrivi_desktop ~/.local/share/applications/remotix-banco.desktop nodisplay
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 --noincremental >/dev/null 2>&1
prova "1-.desktop utente, NoDisplay, dopo kbuildsycoca6" 3

scrivi_desktop ~/.local/share/applications/remotix-banco.desktop visibile
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 --noincremental >/dev/null 2>&1
prova "2-.desktop utente, senza NoDisplay" 3

rm -f ~/.local/share/applications/remotix-banco.desktop
sudo -S -p 'Password: ' cp /dev/stdin /usr/share/applications/remotix-banco.desktop <<EOF
[Desktop Entry]
Type=Application
Name=REMOTIX banco
NoDisplay=true
Terminal=false
Exec=$EXE
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1
EOF
command -v kbuildsycoca6 >/dev/null && kbuildsycoca6 --noincremental >/dev/null 2>&1
prova "3-.desktop di sistema in /usr/share/applications" 3

echo
echo "== registro del giro 3, righe sui permessi:"
grep -aiE 'wayland-interfaces|not in|denied|permission|screencast' "$LOG/3-"*.log 2>/dev/null | head -5
echo "(registri in $LOG)"
