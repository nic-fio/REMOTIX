#!/bin/bash
#
# misure-kde.sh — le misure che aprono la fase 11, sul banco.  Vedi `kde.md` §14.
#
#   bash /media/REMOTIX/tmp/banco-compositori/misure-kde.sh
#
# Che cosa risponde, in un solo avvio di KWin — sono domande indipendenti, che
# non si falsano a vicenda (`kde.md` §14, in fondo):
#
#   M1  il nostro file `.desktop` autorizza la cattura?  (senza la scorciatoia
#       KWIN_WAYLAND_NO_PERMISSION_CHECKS, che e' quella con cui abbiamo
#       misurato il 7 agosto)
#   M3  KWin senza monitor compone in GPU o in software?  Con le due prove che
#       NON dipendono da quel che KWin dichiara: i nodi DRM che ha aperto, il
#       global `zwp_linux_dmabuf_v1` (che nasce solo dal backend EGL) e il tipo
#       di buffer che il flusso di cattura riesce a offrire
#   M5  `connectToEIS` risponde a un processo qualunque del bus di sessione?
#
# ⚠ NON tocca il servizio dell'utente: usa un socket Wayland suo
#   (`wayland-kde`), nessuna porta RDP, e ferma KWin alla fine.
#
set -u

QUI=/media/REMOTIX/tmp/banco-compositori
NODO="$QUI/nodo-kwin"
MIS="$QUI/misura-cattura"
LOG=/tmp/kde-misure
mkdir -p "$LOG"

echo "=================== stato di partenza ==================="
echo "kwin_wayland: $(kwin_wayland --version 2>&1 | head -1)"
echo "gruppi di questa sessione: $(id -nG)"
echo "  (se manca 'render' il compositore non aprira' il nodo di rendering:"
echo "   i gruppi supplementari di una sessione viva non cambiano — §8.6-ter)"

# --- XDG_RUNTIME_DIR: obbligatorio, o il wrapper di KWin fa qFatal ------------
if [ -z "${XDG_RUNTIME_DIR:-}" ] || [ ! -d "${XDG_RUNTIME_DIR:-}" ]; then
    export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"
    mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"
    echo "XDG_RUNTIME_DIR non c'era: uso $XDG_RUNTIME_DIR"
fi

# --- M1, prima meta': il file .desktop che ci autorizza ----------------------
# Exec= deve essere il percorso CANONICO del binario che apre il socket
# (`kde.md` §3.3), e il file va dove guarda KWin.
APP="$HOME/.local/share/applications"
mkdir -p "$APP"
EXE=$(readlink -f "$NODO")
cat > "$APP/remotix-banco.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=REMOTIX banco
NoDisplay=true
Terminal=false
Exec=$EXE
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1
EOF
echo "desktop installato: Exec=$EXE"

# --- un bus di sessione, che serve a M5 --------------------------------------
if [ -S "/run/user/$(id -u)/bus" ]; then
    export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
    echo "bus di sessione: quello d'utente"
else
    eval "$(dbus-launch --sh-syntax)"
    echo "bus di sessione: privato (dbus-launch)"
fi

# --- KWin, SENZA la scorciatoia dei permessi ---------------------------------
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM   # o KWin sceglie il backend sbagliato
SOCK=wayland-kde
rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
kwin_wayland --virtual --width 1920 --height 1080 --no-lockscreen \
    --socket="$SOCK" > "$LOG/kwin.log" 2>&1 &
KPID=$!
for _ in $(seq 40); do [ -S "$XDG_RUNTIME_DIR/$SOCK" ] && break; sleep 0.25; done
sleep 1.5   # la cache dei .desktop di KWin si ricostruisce entro ~1,5 s
if ! kill -0 "$KPID" 2>/dev/null; then
    echo "⛔ KWin non e' partito. Registro:"; tail -15 "$LOG/kwin.log"; exit 1
fi
export WAYLAND_DISPLAY="$SOCK"
echo "kwin avviato: pid=$KPID socket=$SOCK"
echo

echo "=================== M3 — GPU o software? ==================="
echo -n "M3a nodi DRM aperti da KWin: "
ls -l "/proc/$KPID/fd" 2>/dev/null | grep -o 'dri/[a-zA-Z0-9]*' | sort -u | tr '\n' ' '
echo
echo -n "M3b librerie di rendering caricate: "
grep -oE 'lib(EGL|gbm|GLX)[^ ]*\.so|iris_dri|radeonsi_dri|swrast_dri|llvmpipe' \
     "/proc/$KPID/maps" 2>/dev/null | sort -u | tr '\n' ' '
echo
echo -n "M3c global zwp_linux_dmabuf_v1 (nasce solo dal backend EGL): "
if command -v wayland-info >/dev/null; then
    wayland-info 2>/dev/null | grep -c 'zwp_linux_dmabuf_v1'
else
    echo "wayland-info assente"
fi

echo
echo "=================== M1 — il permesso ==================="
echo "protocolli annunciati che ci interessano:"
"$NODO" --elenca 2>&1 | grep -iE 'zkde_screencast|fake_input|keystate|data_control|dmabuf' \
    | sed 's/^/   /' || echo "   (nessuno)"
echo -n "verdetto M1: "
if "$NODO" --elenca 2>&1 | grep -qi zkde_screencast; then
    echo "✅ ANNUNCIATO con il solo .desktop — il cancello si apre come previsto"
else
    echo "⛔ NON annunciato: il .desktop non ha autorizzato"
fi

echo
echo "=================== M5 — connectToEIS ==================="
gdbus call --session --dest org.kde.KWin \
    --object-path /org/kde/KWin/EIS/RemoteDesktop \
    --interface org.kde.KWin.EIS.RemoteDesktop \
    --method connectToEIS 7 2>&1 | head -3

echo
echo "=================== M3d — il tipo di buffer ==================="
# La prova che non dipende da quel che KWin dichiara: se il flusso offre
# DMA-BUF, il compositore sta componendo su GPU con EGL/gbm.
"$NODO" --virtuale 1920x1080 > "$LOG/nodo.log" 2>&1 &
NPID=$!
sleep 3
NODE=$(grep -oE 'nodo (PipeWire )?[0-9]+' "$LOG/nodo.log" | grep -oE '[0-9]+' | head -1)
echo "nodo PipeWire annunciato: ${NODE:-nessuno}"
if [ -n "${NODE:-}" ] && [ -x "$MIS" ]; then
    timeout 12 "$MIS" --nodo "$NODE" --secondi 6 2>&1 | \
        grep -aiE 'tipo|fotogrammi|danno|buffer|fps|disegno' | head -8
else
    echo "salto la misura del flusso: manca il nodo o misura-cattura"
    tail -5 "$LOG/nodo.log"
fi
kill $NPID 2>/dev/null

echo
echo "=================== registro di KWin ==================="
grep -aiE 'drm|gbm|opengl|qpainter|compositing|render node|failed|not supported' \
     "$LOG/kwin.log" | head -12
echo "(registro completo: $LOG/kwin.log)"

kill "$KPID" 2>/dev/null
wait "$KPID" 2>/dev/null
echo
echo "banco chiuso: nessun compositore residuo, nessuna porta toccata."
