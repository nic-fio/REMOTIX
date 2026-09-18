#!/bin/bash
# PROVA I1 (fase 12): un cliente vero entra con un utente NUOVO; la sessione Plasma nasce?
U=${1:-ki1}; PORTA=${2:-8512}; REG=/var/lib/rete11/registro.log
userdel -r $U >/dev/null 2>&1
useradd -m -s /bin/bash $U && printf '%s:provanic2026\n' $U | chpasswd && usermod -aG video,render $U
SEGNO=$(wc -l < $REG)
T0=$(date +%s.%N)
python3 /opt/remotix/01-b3-cliente.py --indirizzo 127.0.0.1 --porta $PORTA --utente $U --parola provanic2026 --resta 25 > /tmp/cliente-$U.log 2>&1 &
CL=$!
NATO=""
for i in $(seq 104); do
  if pgrep -u $U -x plasmashell >/dev/null; then NATO=$(python3 -c "import time;print(round(time.time()-$T0,2))"); break; fi
  sleep 0.25
done
echo "plasmashell di $U: ${NATO:-MAI entro 26 s}"
sleep 3
R=/run/user/$(id -u $U)
echo "--- kwin:"; ps -u $U -o args | grep -E "^/usr/bin/kwin_wayland " | cut -c1-120
echo "--- plasma vivi: $(ps -u $U -o comm= | grep -cE 'plasmashell|ksmserver|kwin_wayland|kded6')  (plasmashell ksmserver kwin_wayland kded6)"
S=$(ls $R 2>/dev/null | grep -E '^wayland-[0-9]+$' | head -1)
echo "--- wl_output su $S: $(runuser -u $U -- env XDG_RUNTIME_DIR=$R WAYLAND_DISPLAY=$S wayland-info 2>/dev/null | grep -c "interface: 'wl_output'")"
runuser -u $U -- env XDG_RUNTIME_DIR=$R WAYLAND_DISPLAY=$S wayland-info 2>/dev/null | grep -A10 "interface: 'wl_output'" | grep -E "name:|width:" | head -4
echo "--- sessioni plasma nate (startplasma-wayland): $(pgrep -u $U -c -x startplasma-way)"
wait $CL; echo "--- cliente uscito: $?  ($(grep -c AMMESSO /tmp/cliente-$U.log) righe AMMESSO)"
echo "--- registro [$U] (sessione/figlio, prime righe utili):"
tail -n +$((SEGNO+1)) $REG | grep "\[$U\]" | grep -E "sessione|figlio" | grep -vE "riprovo|dettaglio" | cut -c1-230 | head -25
echo "--- chiusura"; T1=$(date +%s%N); loginctl terminate-user $U; for i in $(seq 60); do pgrep -u $U >/dev/null || break; sleep 0.5; done
echo "processi dopo terminate: $(pgrep -u $U | wc -l) in $(( ($(date +%s%N)-T1)/1000000 )) ms; /run/user: $(ls -d $R 2>/dev/null || echo sparita)"
