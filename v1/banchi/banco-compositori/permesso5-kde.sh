#!/bin/bash
#
# permesso5-kde.sh — quinto giro.  Il quarto ha stabilito la causa di M1:
#   «KWIN_UTILS: Could not find the desktop file for <exe>»
# cioe' KApplicationTrader non associa il `.desktop` all'eseguibile.  Restano due
# spiegazioni, con cure opposte:
#   (i)  il file non e' nell'indice sycoca
#   (ii) e' nell'indice ma la query lo scarta (p.es. NoDisplay, oppure l'Exec
#        non passa da QProcess::splitCommand come ci aspettiamo)
#
# Qui si prova a SPOSTARE il risultato: piu' varianti del file, un solo KWin
# acceso, e dopo ogni `kbuildsycoca6` una nuova domanda al filtro (ogni cliente
# nuovo rifa' la query).  La variante che fa sparire quella riga e' la risposta.
#
# E poi M3a/M3b con UN SOLO sudo, con la richiesta di password esplicita e lo
# stderr NON soppresso (fase 1 di PIANO.md: se si sopprime, resta appeso).
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
NODO="$QUI/nodo-kwin"
EXE=$(readlink -f "$NODO")
APP="$HOME/.local/share/applications"
LOG=/tmp/kde-p5; rm -rf "$LOG"; mkdir -p "$LOG"; mkdir -p "$APP"

export LANG=C.UTF-8 LC_ALL=C.UTF-8
[ -n "${XDG_RUNTIME_DIR:-}" ] && [ -d "${XDG_RUNTIME_DIR:-}" ] || {
    export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"; }
[ -S "/run/user/$(id -u)/bus" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM
SOCK=wayland-kde
D="$APP/remotix-banco.desktop"

echo "== strumenti di diagnosi disponibili in kbuildsycoca6:"
kbuildsycoca6 --help 2>&1 | grep -aiE 'track|menutest|global|help|incremental' | sed 's/^/   /'

avvia() {   # $1 etichetta, resto ambiente
    local nome="$1"; shift
    rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
    env "$@" QT_LOGGING_RULES='KWIN_UTILS.debug=true;kwin_core.debug=true' \
        /usr/bin/kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen \
        --socket="$SOCK" > "$LOG/$nome.log" 2>&1 &
    PID=$!
    local i; for i in $(seq 40); do [ -S "$XDG_RUNTIME_DIR/$SOCK" ] && break; sleep 0.25; done
    sleep 2.5
    kill -0 "$PID" 2>/dev/null || { echo "   ⛔ KWin non partito:"; tail -5 "$LOG/$nome.log" | sed 's/^/      /'; return 1; }
}

prova() {   # $1 = etichetta della variante
    kbuildsycoca6 --noincremental > "$LOG/syco-$1.log" 2>&1
    sleep 1
    local esito righe
    if WAYLAND_DISPLAY="$SOCK" "$NODO" --elenca 2>&1 | grep -qi zkde_screencast
    then esito="✅ ANNUNCIATO"; else esito="⛔ negato"; fi
    # l'ultima riga di KWIN_UTILS dice se il file e' stato trovato o no
    righe=$(grep -ac 'Could not find the desktop file' "$LOG/$AVVIO.log")
    printf '   %-46s %-14s  (righe «not found» finora: %s)\n' "$1" "$esito" "$righe"
}

echo
echo "=================== (a) quale forma del .desktop entra ==================="
AVVIO=a; avvia a || exit 1
echo "   KWin acceso (pid $PID), senza scorciatoie. Ogni riga = una variante:"

cat > "$D" <<EOF
[Desktop Entry]
Type=Application
Name=REMOTIX banco
NoDisplay=true
Terminal=false
Exec=$EXE
X-KDE-Wayland-Interfaces=zkde_screencast_unstable_v1
EOF
prova "1 come krdp (NoDisplay=true)"

sed -i '/^NoDisplay/d' "$D"
prova "2 senza NoDisplay"

printf 'Icon=preferences-system\nCategories=Utility;\n' >> "$D"
prova "3 + Icon + Categories"

sed -i "s|^Exec=.*|Exec=\"$EXE\"|" "$D"
prova "4 Exec fra virgolette"

sed -i "s|^Exec=.*|Exec=$EXE --elenca|" "$D"
prova "5 Exec con un argomento"

# e la controprova: un .desktop il cui Exec e' un binario di sistema qualunque
cat > "$APP/remotix-prova-cat.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=prova cat
Terminal=true
Exec=/usr/bin/cat
EOF
kbuildsycoca6 --noincremental >/dev/null 2>&1; sleep 1
echo "   controprova indipendente da KWin: KService vede i nostri due file?"
echo -n "     "; ls -1 "$APP" | sed 's/^/       /' | tr '\n' ' '; echo

echo "   tutte le righe di KWIN_UTILS del giro:"
grep -a 'KWIN_UTILS' "$LOG/a.log" | sort -u | head -4 | sed 's/^/      /'
kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null

echo
echo "=================== (b) M3a/M3b — un solo sudo, prompt esplicito ==================="
AVVIO=b; avvia b KWIN_WAYLAND_NO_PERMISSION_CHECKS=1 || exit 1
echo "   pid del compositore: $PID"
echo "   (segue la richiesta di password: serve perche' kwin_wayland porta"
echo "    l'xattr security.capability ed e' quindi non dumpable)"
sudo -S -p 'Password: ' bash -c "
    echo -n '   M3a nodi DRM aperti: '
    ls -l /proc/$PID/fd | grep -oE '/dev/dri/[a-zA-Z0-9]+' | sort -u | tr '\n' ' '; echo
    echo -n '   M3b rendering caricato: '
    grep -oE '[a-z0-9_]+_dri\.so|libgbm\.so[0-9.]*|libEGL[^ ]*so[0-9.]*|libgallium[^ ]*|llvmpipe|libva[^ ]*so[0-9.]*' /proc/$PID/maps | sort -u | tr '\n' ' '; echo
    echo -n '   M3b-bis nome del nodo di rendering: '
    ls -l /proc/$PID/fd 2>/dev/null | grep -oE 'renderD[0-9]+|card[0-9]+' | sort -u | tr '\n' ' '; echo
"
echo
echo "   M3d — il tipo di buffer del flusso:"
WAYLAND_DISPLAY="$SOCK" "$NODO" --virtuale 1280x720 > "$LOG/nodo.log" 2>&1 &
NP=$!; sleep 3
NODE=$(grep -aoE '\b[0-9]{2,}\b' "$LOG/nodo.log" | head -1)
echo "      nodo PipeWire: ${NODE:-nessuno}"
sed -n '1,3p' "$LOG/nodo.log" | sed 's/^/      | /'
if [ -n "${NODE:-}" ]; then
    timeout 20 "$QUI/misura-cattura" --nodo "$NODE" --larghezza 1280 --altezza 720 --fps 60 \
        > "$LOG/mis.log" 2>&1
    grep -aiE 'tipo|fotogramm|fps|danno|disegno|dmabuf|memfd|buffer|modificatore' "$LOG/mis.log" \
        | head -10 | sed 's/^/      /'
fi
kill $NP 2>/dev/null
kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null

rm -f "$APP/remotix-prova-cat.desktop"
pkill -x kwin_wayland; pkill -x nodo-kwin; pkill -x misura-cattura
sleep 0.5
echo
echo "residui: kwin=$(pgrep -xc kwin_wayland || true) nodo=$(pgrep -xc nodo-kwin || true)"
echo "fine. registri in $LOG"
