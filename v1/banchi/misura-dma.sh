#!/bin/bash
# Confronto sul DESKTOP VERO fra il percorso in memoria e quello a copia zero.
# Stessa scena: la si muove battendo tasti dal client, come in fase 4.
set -u
BASE=/media/REMOTIX
vm()  { bash "$BASE/vm.sh" ssh "$@" </dev/null; }
cnt() { bash "$BASE/enter.sh" "$@"; }

giro() { # $1 = 0|1 (copia zero)   $2 = etichetta
    local dma="$1" etichetta="$2" t0 t1 tick0 tick1 f0 f1
    vm "printf 'REMOTIX_OPZIONI=--registro diagnostica --senza-autenticazione\nREMOTIX_DMABUF=$dma\n' \
        | sudo tee /etc/default/remotix >/dev/null; rm -f ~/remotix.log; \
        sudo systemctl restart remotix; sleep 3" >/dev/null
    cnt "bash /srv/remotix/tmp/banco-b/fase9-client.sh AVC420 fase9-$etichetta.log" >/dev/null
    sleep 3
    read -r tick0 f0 <<<"$(vm "P=\$(systemctl show -p MainPID --value remotix.service); \
        T=\$(awk '{print \$14+\$15}' /proc/\$P/stat); \
        F=\$(grep -F 'rete: RTT' ~/remotix.log | tail -1 | grep -oE 'spediti [0-9]+' | grep -oE '[0-9]+'); \
        echo \"\${T:-0} \${F:-0}\"" | tr -d '\r' | tail -1)"
    t0=$(date +%s)
    cnt "export DISPLAY=:112; xdotool search --name REMOTIXFASE9 windowactivate --sync 2>/dev/null; \
         xdotool key super; sleep 1; \
         for i in \$(seq 1 30); do xdotool type --delay 25 'remotix fase nove'; \
             xdotool key BackSpace BackSpace BackSpace BackSpace; done" >/dev/null
    t1=$(date +%s)
    read -r tick1 f1 <<<"$(vm "P=\$(systemctl show -p MainPID --value remotix.service); \
        T=\$(awk '{print \$14+\$15}' /proc/\$P/stat); \
        F=\$(grep -F 'rete: RTT' ~/remotix.log | tail -1 | grep -oE 'spediti [0-9]+' | grep -oE '[0-9]+'); \
        echo \"\${T:-0} \${F:-0}\"" | tr -d '\r' | tail -1)"
    local dt=$(( t1 - t0 )) dtick=$(( tick1 - tick0 )) df=$(( f1 - f0 ))
    [ "$dt" -lt 1 ] && dt=1
    [ "$df" -lt 1 ] && df=1
    printf '  %-12s %2ds  fotogrammi %4d  %2d/s  CPU %3d centesimi di core  %3d ms di CPU per fotogramma\n' \
        "$etichetta" "$dt" "$df" "$(( df / dt ))" "$(( dtick * 100 / 100 * 100 / dt ))" "$(( dtick * 10 / df ))"
    vm "grep -F 'tempo per fotogramma' ~/remotix.log | tail -1" | sed 's/^/      /'
    cnt "bash /srv/remotix/tmp/banco-b/fase9-chiudi.sh" >/dev/null
}

echo "== desktop vero, scena mossa dagli stessi tasti =="
giro 0 in-memoria
giro 1 copia-zero
vm "printf 'REMOTIX_OPZIONI=--registro diagnostica\n' | sudo tee /etc/default/remotix >/dev/null; \
    sudo systemctl restart remotix" >/dev/null
echo "  (servizio rimesso com'era)"
