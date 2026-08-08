#!/bin/bash
set -u
B=/media/REMOTIX
vm() { bash $B/vm.sh ssh "$@" </dev/null; }
vm "printf 'REMOTIX_OPZIONI=--registro diagnostica --senza-autenticazione --immagine-di-prova\n' | sudo tee /etc/default/remotix >/dev/null; rm -f ~/remotix.log; sudo systemctl restart remotix.service; sleep 3" >/dev/null 2>&1
bash $B/enter.sh "bash /srv/remotix/tmp/banco-b/fase7-client.sh 3389 f7s-cli.log" >/dev/null 2>&1
sleep 8
vm "sudo systemd-run --on-active=90 --unit=f7s-sblocca /usr/sbin/tc qdisc del dev enp0s2 root" >/dev/null 2>&1
vm "sudo /usr/sbin/tc qdisc replace dev enp0s2 root netem delay 120ms rate 250kbit" >/dev/null 2>&1
sleep 22
echo "=== ultime 14 righe di rete ==="
vm "grep -E 'rete: RTT|non risponde piu|strozzo|riprendo' ~/remotix.log | tail -14"
echo "=== avvisi ==="
vm "grep -c 'non risponde piu' ~/remotix.log"
vm "sudo /usr/sbin/tc qdisc del dev enp0s2 root 2>/dev/null; printf 'REMOTIX_OPZIONI=--registro diagnostica\n' | sudo tee /etc/default/remotix >/dev/null; sudo systemctl restart remotix.service" >/dev/null 2>&1
bash $B/enter.sh "bash /srv/remotix/tmp/banco-b/fase7-chiudi.sh" >/dev/null 2>&1
