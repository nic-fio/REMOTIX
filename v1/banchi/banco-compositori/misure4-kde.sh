#!/bin/bash
#
# misure4-kde.sh — chiude M3 e M4 con la prova DIRETTA, invece che per indizi.
#
# Il giro precedente ha mostrato che le nostre due prove strutturali non bastano:
#   · `zwp_linux_dmabuf_v1` annunciato ⇒ backend EGL, ma **non** ⇒ GPU vera:
#     con LIBGL_ALWAYS_SOFTWARE=1 KWin dice «OpenGL successfully initialized» e
#     annuncia il dmabuf comunque (mentre con KWIN_COMPOSE=Q il dmabuf spariva:
#     quindi la prova vale per «EGL sì/no», non per «GPU sì/no»).
#   · resta da vedere se llvmpipe apre comunque un render node — se sì, anche
#     «renderD aperto» non distingue.
#
# La prova diretta è la stringa del renderer OpenGL, e KWin la regala:
#   gdbus call --session --dest org.kde.KWin --object-path /KWin \
#              --method org.kde.KWin.supportInformation
#
# Un solo `sudo -v` in testa (una richiesta di password sola, stderr NON soppresso),
# poi le letture di /proc non ne chiedono più.
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
NODO="$QUI/nodo-kwin"
LOG=/tmp/kde-m4; rm -rf "$LOG"; mkdir -p "$LOG"

export LANG=C.UTF-8 LC_ALL=C.UTF-8 XDG_MENU_PREFIX=plasma-
[ -n "${XDG_RUNTIME_DIR:-}" ] && [ -d "${XDG_RUNTIME_DIR:-}" ] || {
    export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"; }
[ -S "/run/user/$(id -u)/bus" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM
SOCK=wayland-kde

echo "== una sola richiesta di password, per le letture di /proc =="
sudo -S -p 'Password: ' -v
echo "   sudo validato: $?"

giro() {  # $1 = etichetta, resto = ambiente
    local nome="$1"; shift
    rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
    env "$@" kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen \
        --socket="$SOCK" > "$LOG/$nome.log" 2>&1 &
    local pid=$!
    local i; for i in $(seq 40); do [ -S "$XDG_RUNTIME_DIR/$SOCK" ] && break; sleep 0.25; done
    sleep 3
    if ! kill -0 "$pid" 2>/dev/null; then
        echo "   ⛔ USCITO. ultime righe:"; tail -3 "$LOG/$nome.log" | sed 's/^/      /'; return
    fi
    echo "   pid $pid"
    # 1. la prova diretta: che renderer sta usando, secondo KWin stesso
    gdbus call --session --dest org.kde.KWin --object-path /KWin \
        --method org.kde.KWin.supportInformation > "$LOG/$nome.info" 2>&1
    echo -n "      renderer OpenGL : "
    grep -aoE 'OpenGL (vendor|renderer|version) string: [^\\]*' "$LOG/$nome.info" \
        | sed 's/OpenGL //' | tr '\n' '|' ; echo
    echo -n "      compositing     : "
    grep -aoE 'Compositing Type: [A-Za-z]+|Compositing: [A-Za-z]+' "$LOG/$nome.info" | head -1; echo
    # 2. i nodi DRM: llvmpipe ne apre o no?
    echo -n "      nodi DRM aperti : "
    sudo ls -l "/proc/$pid/fd" | grep -oE '/dev/dri/[a-zA-Z0-9]+' | sort -u | tr '\n' ' '; echo
    echo -n "      dmabuf annunciato: "
    WAYLAND_DISPLAY="$SOCK" "$NODO" --elenca 2>&1 | grep -c 'zwp_linux_dmabuf_v1' || true
    kill "$pid" 2>/dev/null; wait "$pid" 2>/dev/null
}

echo
echo "############ M3 definitiva + M4: tre ambienti, la stessa domanda ############"
echo "--- A: ambiente sano (è la configurazione che misuriamo di solito)"
giro sano
echo "--- B: LIBGL_ALWAYS_SOFTWARE=1 + KWIN_COMPOSE=O2 (software travestito da OpenGL)"
giro software LIBGL_ALWAYS_SOFTWARE=1 KWIN_COMPOSE=O2
echo "--- C: KWIN_COMPOSE=Q (QPainter chiesto: il controllo negativo)"
giro qpainter KWIN_COMPOSE=Q

echo
echo "############ M8 — la cattura dipende dal VT? ############"
echo "(con --virtual non c'è nessun VT in mezzo; qui si verifica invece di dedurlo)"
rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen --socket="$SOCK" \
    > "$LOG/m8.log" 2>&1 &
K=$!
for i in $(seq 40); do [ -S "$XDG_RUNTIME_DIR/$SOCK" ] && break; sleep 0.25; done
sleep 2.5
echo -n "   tty/console aperte dal compositore: "
sudo ls -l "/proc/$K/fd" | grep -oE '/dev/(tty[0-9]*|console|vcs[a0-9]*)' | sort -u | tr '\n' ' '
echo "(vuoto = nessun legame col VT)"
echo -n "   VT attivo adesso: "; cat /sys/class/tty/tty0/active
echo -n "   sessione logind del compositore ha un VT? "
sudo grep -aE '^(Vt|Seat)' /proc/$K/environ 2>/dev/null | head -2; loginctl show-session $XDG_SESSION_ID -p VTNr -p Seat 2>&1 | tr '\n' ' '; echo
echo "   cambio VT con l'ioctl VT_ACTIVATE (kbd/chvt non è installato), e ritorno:"
WAYLAND_DISPLAY="$SOCK" "$NODO" > "$LOG/m8-nodo.log" 2>&1 &
NP=$!; sleep 2
NODE=$(grep -aoE 'nodo PipeWire [0-9]+' "$LOG/m8-nodo.log" | grep -oE '[0-9]+$' | head -1)
echo "      nodo PipeWire prima: ${NODE:-nessuno}"
sudo python3 -c '
import fcntl, os, time
VT_ACTIVATE, VT_WAITACTIVE = 0x5606, 0x5607
fd = os.open("/dev/tty0", os.O_RDWR)
for vt in (2, 1):
    fcntl.ioctl(fd, VT_ACTIVATE, vt); fcntl.ioctl(fd, VT_WAITACTIVE, vt)
    print("      VT attivo ->", open("/sys/class/tty/tty0/active").read().strip())
    time.sleep(1)
'
echo -n "      il compositore è ancora vivo: "; kill -0 $K 2>/dev/null && echo "sì ✅" || echo "NO ⛔"
echo -n "      il flusso è ancora vivo:     "; kill -0 $NP 2>/dev/null && echo "sì ✅" || echo "NO ⛔"
echo -n "      il protocollo risponde ancora: "
WAYLAND_DISPLAY="$SOCK" "$NODO" --elenca 2>&1 | grep -c zkde_screencast || true
kill $NP $K 2>/dev/null; wait 2>/dev/null

pkill -x kwin_wayland; pkill -x nodo-kwin; sleep 0.5
echo
echo "residui: kwin=$(pgrep -xc kwin_wayland || true)"
echo "VT attivo alla fine: $(cat /sys/class/tty/tty0/active)"
echo "fine. registri in $LOG"
