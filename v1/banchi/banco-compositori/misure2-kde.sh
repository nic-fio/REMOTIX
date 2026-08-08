#!/bin/bash
#
# misure2-kde.sh — le misure «leggere» che restano: M4, M3d, M7, M11.
# Vedi `kde.md` §14.  Regole di banco già pagate e rispettate qui:
#   · `pkill`/`pgrep` ancorati con -x, mai -f
#   · nessun `2>/dev/null` su sudo
#   · solo opzioni VERE: nodo-kwin {--elenca | --virtuale W H}  (due argomenti!)
#     misura-cattura {--nodo N --larghezza W --altezza H --fps N --durata S --dmabuf}
#   · XDG_MENU_PREFIX=plasma-, o il permesso della cattura non funziona (§3.3-bis)
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
NODO="$QUI/nodo-kwin"; MIS="$QUI/misura-cattura"
LOG=/tmp/kde-m2; rm -rf "$LOG"; mkdir -p "$LOG"

export LANG=C.UTF-8 LC_ALL=C.UTF-8 XDG_MENU_PREFIX=plasma-
[ -n "${XDG_RUNTIME_DIR:-}" ] && [ -d "${XDG_RUNTIME_DIR:-}" ] || {
    export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"; }
[ -S "/run/user/$(id -u)/bus" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM
SOCK=wayland-kde
PID=

avvia() {   # $1 = etichetta, resto = ambiente
    local nome="$1"; shift
    rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
    env "$@" QT_LOGGING_RULES='kwin_core.debug=true;kwin_opengl.debug=true;kwin_scene_opengl.debug=true' \
        kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen --socket="$SOCK" \
        > "$LOG/$nome.log" 2>&1 &
    PID=$!
    local i; for i in $(seq 40); do [ -S "$XDG_RUNTIME_DIR/$SOCK" ] && break; sleep 0.25; done
    sleep 2.5
    kill -0 "$PID" 2>/dev/null
}
ferma() { [ -n "$PID" ] && kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null; PID=; }
dmabuf_c() { WAYLAND_DISPLAY="$SOCK" "$NODO" --elenca 2>/dev/null | grep -ci 'zwp_linux_dmabuf_v1' || true; }
renderer() { grep -aioE 'llvmpipe[^"]*|Mesa Intel[^"]*|AMD [A-Za-z0-9 ()]*|softpipe|zink[^"]*' "$LOG/$1.log" | sort -u | head -2 | tr '\n' '|'; }

echo "############ M4 — KWIN_COMPOSE=O2 protegge davvero? ############"
echo "(la lezione 1.8: un componente che può decidere da sé va costretto E verificato)"
printf '%-42s %-14s %-8s %s\n' "giro" "KWin" "dmabuf" "renderer secondo KWin"

for g in 1 2 3; do
  case $g in
    1) nome="1-O2, ambiente sano";        env2=(KWIN_COMPOSE=O2) ;;
    2) nome="2-O2 + OpenGL reso IMPOSSIBILE"; env2=(KWIN_COMPOSE=O2
           __EGL_VENDOR_LIBRARY_DIRS=/nonexistent LIBGL_DRIVERS_PATH=/nonexistent
           MESA_LOADER_DRIVER_OVERRIDE=nonexistent GALLIUM_DRIVER=nonexistent) ;;
    3) nome="3-LIBGL_ALWAYS_SOFTWARE=1";  env2=(LIBGL_ALWAYS_SOFTWARE=1) ;;
  esac
  if avvia "m4-$g" "${env2[@]}"; then
      printf '%-42s %-14s %-8s %s\n' "$nome" "PARTITO" "$(dmabuf_c)" "$(renderer m4-$g)"
      ferma
  else
      printf '%-42s %-14s %-8s %s\n' "$nome" "USCITO" "-" "$(tail -2 "$LOG/m4-$g.log" | tr '\n' ' ' | cut -c1-70)"
  fi
done
echo "   lettura: se il giro 2 dice PARTITO, KWIN_COMPOSE=O2 è INERTE (§5.4 confermata)."
echo "   e se il giro 3 dice llvmpipe CON dmabuf presente, allora «dmabuf ⇒ EGL» ma NON ⇒ GPU vera."

echo
echo "############ il giro buono, per M3d + M7 + M11 ############"
if avvia buono KWIN_COMPOSE=O2; then
echo "   KWin pid $PID"

echo
echo "== M11 — misure assurde a stream_virtual_output (e KWin deve sopravvivere) =="
for m in "0 0" "-1 -1" "16384 16384" "1 1" "99999 99999"; do
    set -- $m
    r=$(WAYLAND_DISPLAY="$SOCK" timeout 8 "$NODO" --virtuale "$1" "$2" 2>&1 | head -2 | tr '\n' ' ')
    printf '   %-14s → %s\n' "$1x$2" "${r:0:90}"
    kill -0 "$PID" 2>/dev/null || { echo "   ⛔⛔ KWIN È MORTO su $1x$2"; break; }
done
echo -n "   KWin è ancora vivo dopo tutte: "; kill -0 "$PID" 2>/dev/null && echo "sì ✅" || echo "NO ⛔"

echo
echo "== M7a — stream_virtual_output con --virtual: fallisce come dice §8.1? =="
WAYLAND_DISPLAY="$SOCK" timeout 8 "$NODO" --virtuale 1920 1080 2>&1 | head -4 | sed 's/^/      /'

echo
echo "== M7b — quanto costa mettere in piedi un flusso (il buco del «chiudi e rifai») =="
for giro in 1 2 3; do
    T0=$(date +%s%N)
    WAYLAND_DISPLAY="$SOCK" "$NODO" > "$LOG/n$giro.log" 2>&1 &
    NP=$!
    for i in $(seq 100); do grep -qa 'nodo PipeWire' "$LOG/n$giro.log" && break; sleep 0.05; done
    T1=$(date +%s%N)
    NODE=$(grep -aoE 'nodo PipeWire [0-9]+' "$LOG/n$giro.log" | grep -oE '[0-9]+$' | head -1)
    printf '   giro %s: protocollo→nodo PipeWire = %s ms   (nodo %s)\n' \
        "$giro" "$(( (T1-T0)/1000000 ))" "${NODE:-nessuno}"
    if [ "$giro" = 1 ] && [ -n "${NODE:-}" ]; then
        echo
        echo "== M3d — il tipo di buffer, CHIEDENDO DMA-BUF (--dmabuf) =="
        timeout 25 "$MIS" --nodo "$NODE" --larghezza 1280 --altezza 720 --fps 60 --durata 6 --dmabuf \
            > "$LOG/m3d.log" 2>&1
        grep -aiE 'formato negoziato|tipo|fotogramm|danno|disegno|fps|modificatore' "$LOG/m3d.log" | head -8 | sed 's/^/      /'
        echo "   e la controprova, SENZA --dmabuf:"
        timeout 25 "$MIS" --nodo "$NODE" --larghezza 1280 --altezza 720 --fps 60 --durata 4 \
            > "$LOG/m3d-mem.log" 2>&1
        grep -aiE 'formato negoziato' "$LOG/m3d-mem.log" | head -2 | sed 's/^/      /'
        echo
    fi
    kill $NP 2>/dev/null; wait $NP 2>/dev/null
    sleep 0.5
done
ferma
fi

pkill -x kwin_wayland; pkill -x nodo-kwin; pkill -x misura-cattura; sleep 0.5
echo
echo "residui: kwin=$(pgrep -xc kwin_wayland || true) nodo=$(pgrep -xc nodo-kwin || true)"
echo "fine. registri in $LOG"
