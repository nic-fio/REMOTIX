#!/bin/bash
#
# misure3-kde.sh — chiude M4 e completa M3d, correggendo tre errori di misure2:
#   1. `nodo-kwin` scrive su STDERR: sopprimerlo fa contare «0 dmabuf» quando ce ne
#      sono. È esattamente §1.9 di LEZIONI.md — «una lettura negata non è zero».
#      Qui si tiene 2>&1 e si stampa anche l'elenco, per poterlo verificare a occhio.
#   2. le categorie di registro giuste per la stringa del renderer: `*.debug=true`.
#   3. per rispondere a M4 bisogna rendere OpenGL DAVVERO impossibile, non solo
#      software: si nasconde /dev/dri dentro un namespace di monti privato
#      (senza toccare il sistema, senza root).
#
set -u
QUI=/media/REMOTIX/tmp/banco-compositori
NODO="$QUI/nodo-kwin"; MIS="$QUI/misura-cattura"
LOG=/tmp/kde-m3; rm -rf "$LOG"; mkdir -p "$LOG"

export LANG=C.UTF-8 LC_ALL=C.UTF-8 XDG_MENU_PREFIX=plasma-
[ -n "${XDG_RUNTIME_DIR:-}" ] && [ -d "${XDG_RUNTIME_DIR:-}" ] || {
    export XDG_RUNTIME_DIR="/tmp/xdg-$(id -u)"; mkdir -p "$XDG_RUNTIME_DIR"; chmod 700 "$XDG_RUNTIME_DIR"; }
[ -S "/run/user/$(id -u)/bus" ] && export DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$(id -u)/bus"
unset WAYLAND_DISPLAY DISPLAY QT_QPA_PLATFORM
SOCK=wayland-kde
PID=

avvia() {   # $1 etichetta, resto ambiente
    local nome="$1"; shift
    rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
    env "$@" QT_LOGGING_RULES='*.debug=true' \
        kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen --socket="$SOCK" \
        > "$LOG/$nome.log" 2>&1 &
    PID=$!
    local i; for i in $(seq 40); do [ -S "$XDG_RUNTIME_DIR/$SOCK" ] && break; sleep 0.25; done
    sleep 3
    kill -0 "$PID" 2>/dev/null
}
ferma() { [ -n "$PID" ] && { kill "$PID" 2>/dev/null; wait "$PID" 2>/dev/null; }; PID=; }
# ⚠ 2>&1 e NON 2>/dev/null: nodo-kwin scrive l'elenco su stderr
elenco()  { WAYLAND_DISPLAY="$SOCK" "$NODO" --elenca 2>&1; }
dmabuf_c(){ elenco | grep -ci 'zwp_linux_dmabuf_v1' || true; }
renderer(){ grep -aiE 'renderer|gl_vendor|vendor string|driver:|llvmpipe|softpipe' "$LOG/$1.log" \
            | grep -aivE 'qt.|kwin_libinput' | head -3 | tr '\n' ' | '; }
compose() { grep -aiE 'compositing|qpainter|opengl.*(not|fail)|falling back' "$LOG/$1.log" | head -3 | tr '\n' ' | '; }

echo "== controllo positivo dello strumento (§1.9): l'elenco dei global si legge? =="
echo "   (KWin non è ancora avviato: qui deve dire che non c'è display, non silenzio)"
elenco | head -2 | sed 's/^/      /'

echo
echo "############ M4 — KWIN_COMPOSE=O2 protegge, sì o no? ############"

for g in 1 2 3 4; do
  ns=0
  case $g in
    1) nome="1-O2 ambiente sano (controllo)"; env2=(KWIN_COMPOSE=O2) ;;
    2) nome="2-LIBGL_ALWAYS_SOFTWARE=1";      env2=(KWIN_COMPOSE=O2 LIBGL_ALWAYS_SOFTWARE=1) ;;
    3) nome="3-Q, cioè QPainter chiesto";     env2=(KWIN_COMPOSE=Q) ;;
    4) nome="4-O2 con /dev/dri NASCOSTO";     env2=(KWIN_COMPOSE=O2); ns=1 ;;
  esac
  echo "--- $nome"
  if [ "$ns" = 1 ]; then
      # namespace di monti privato: /dev/dri diventa una tmpfs vuota. Nessun root,
      # nessun effetto fuori da questo processo.
      rm -f "$XDG_RUNTIME_DIR/$SOCK" "$XDG_RUNTIME_DIR/$SOCK.lock"
      unshare --user --map-user=$(id -u) --map-group=$(id -g) --mount \
        bash -c "mount -t tmpfs none /dev/dri 2>&1 | head -2
                 echo \"   /dev/dri dentro il namespace: [\$(ls /dev/dri | tr '\n' ' ')]\"
                 KWIN_COMPOSE=O2 QT_LOGGING_RULES='*.debug=true' \
                 kwin_wayland --virtual --width 1280 --height 720 --no-lockscreen \
                     --socket=$SOCK > $LOG/m4-4.log 2>&1 &
                 K=\$!
                 for i in \$(seq 40); do [ -S $XDG_RUNTIME_DIR/$SOCK ] && break; sleep 0.25; done
                 sleep 3
                 if kill -0 \$K 2>/dev/null; then echo '   esito: PARTITO ⇒ O2 è INERTE'; else echo '   esito: USCITO ⇒ O2 è rispettato'; fi
                 kill \$K 2>/dev/null; wait 2>/dev/null" | sed 's/^/   /'
      echo "   che cosa dice il registro:"
      grep -aiE 'compositing|qpainter|render node|drm node|failed|not supported|falling back' "$LOG/m4-4.log" 2>/dev/null | head -4 | sed 's/^/      /'
  elif avvia "m4-$g" "${env2[@]}"; then
      echo "   esito: PARTITO   dmabuf annunciati: $(dmabuf_c)"
      echo "   renderer : $(renderer m4-$g)"
      echo "   compositing: $(compose m4-$g)"
      ferma
  else
      echo "   esito: USCITO"
      tail -3 "$LOG/m4-$g.log" | sed 's/^/      /'
  fi
done

echo
echo "############ M3d completo — con una scena che si muove ############"
if avvia buono KWIN_COMPOSE=O2; then
  echo "   global che ci interessano (dall'elenco vero, stderr compreso):"
  elenco | grep -iE 'zkde_screencast|dmabuf|fake_input|keystate|data_control' | sed 's/^/      /'

  SCENA=$(command -v weston-simple-egl || echo "")
  if [ -n "$SCENA" ]; then
      WAYLAND_DISPLAY="$SOCK" "$SCENA" > "$LOG/scena.log" 2>&1 &
      SP=$!; sleep 2
      echo "   scena: weston-simple-egl avviata (pid $SP)"
  else
      SP=; echo "   ⚠ weston-simple-egl assente: la scena non si muove, i fotogrammi saranno 0"
  fi

  WAYLAND_DISPLAY="$SOCK" "$NODO" > "$LOG/nodo.log" 2>&1 &
  NP=$!; sleep 2
  NODE=$(grep -aoE 'nodo PipeWire [0-9]+' "$LOG/nodo.log" | grep -oE '[0-9]+$' | head -1)
  echo "   nodo PipeWire: ${NODE:-nessuno}"
  if [ -n "${NODE:-}" ]; then
      for modo in "--dmabuf" ""; do
          echo "   ---- misura $([ -n "$modo" ] && echo 'CHIEDENDO DMA-BUF' || echo 'in memoria'):"
          timeout 30 "$MIS" --nodo "$NODE" --larghezza 1280 --altezza 720 --fps 60 --durata 8 $modo \
              > "$LOG/m3d$modo.log" 2>&1
          grep -aiE '^==|formato negoziato|fotogrammi|danno:|disegno|salti' "$LOG/m3d$modo.log" | head -7 | sed 's/^/      /'
      done
  fi
  [ -n "${SP:-}" ] && kill $SP 2>/dev/null
  kill $NP 2>/dev/null
  ferma
fi

pkill -x kwin_wayland; pkill -x nodo-kwin; pkill -x misura-cattura; pkill -x weston-simple-egl
sleep 0.5
echo
echo "residui: kwin=$(pgrep -xc kwin_wayland || true) nodo=$(pgrep -xc nodo-kwin || true) scena=$(pgrep -xc weston-simple-egl || true)"
echo "fine. registri in $LOG"
