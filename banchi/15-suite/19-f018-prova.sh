#!/bin/bash
# 19-f018-prova.sh — UNA prova F-018 (riattacco a misura diversa) su rete11-lxqt
# sulla Radeon, con il binario e la strada scelti, e il conto dei page fault
# della scheda prima e dopo (diagnosi del FAIL del giro 19-radeon).
#
#   (sul server, come nicfio)  bash 19-f018-prova.sh <md5-del-binario> <scheda|vaapi|vulkan> <etichetta>
#
# Il binario e' /media/REMOTIX/rete11/prodotto/remotix.<md5>; la strada e'
# l'opzione --codifica del server (riacceso a mano con la stessa riga di
# 11-accendi.sh server, piu' --codifica).  Lascia /media/REMOTIX/rete11/prodotto/remotix
# = il binario scelto: chi chiama lo rimette a posto dopo.
set -u
MD5=$1; STRADA=$2; ETI=$3
D=${REMOTIX_D:-lxqt}; case $D in gnome) PORTA=8511;; kde) PORTA=8512;; xfce) PORTA=8513;; *) PORTA=8514;; esac
R=/media/REMOTIX/rete11
PAROLA=$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh")
S() { printf '%s\n' "$PAROLA" | sudo -S -p '' "$@"; }
cd $R || exit 2
cp "prodotto/remotix.$MD5" prodotto/remotix || exit 2
echo "binario $(md5sum prodotto/remotix | cut -c1-8) · strada $STRADA · $(date +%T)"
S env REMOTIX_SCHEDA=amd bash 11-accendi.sh prodotto $D >/tmp/f018-$ETI-prodotto.log 2>&1 || { echo "⛔ prodotto"; tail -3 /tmp/f018-$ETI-prodotto.log; exit 2; }
S env REMOTIX_SCHEDA=amd bash 11-accendi.sh server $D >/tmp/f018-$ETI-server.log 2>&1 || { echo "⛔ server"; tail -3 /tmp/f018-$ETI-server.log; exit 2; }
if [ "$STRADA" != scheda ]; then
	S podman exec rete11-$D sh -c "
		systemctl stop rete11-server 2>/dev/null; systemctl reset-failed rete11-server 2>/dev/null
		rm -f /var/lib/rete11/registro.log
		systemd-run --unit=rete11-server --working-directory=/opt/remotix \
			--property=StandardOutput=append:/var/lib/rete11/registro.log \
			--property=StandardError=append:/var/lib/rete11/registro.log \
			--property=KillMode=mixed \
			/opt/remotix/remotix --indirizzo 0.0.0.0 --nome 127.0.0.1 --porta $PORTA \
			--certificati /var/lib/rete11/certificati --pagina /opt/remotix/pagina.html \
			--ban-file /var/lib/rete11/ban --comando-socket /var/lib/rete11/comando.sock \
			--rilievo /var/lib/rete11/rilievo --parlantina --journal --codifica $STRADA
	" >/dev/null 2>&1
	for _ in $(seq 1 40); do S podman exec rete11-$D grep -q 'pronto: https' /var/lib/rete11/registro.log 2>/dev/null && break; sleep 0.5; done
fi
echo "strade all'avvio: $(S podman exec rete11-$D sh -c "grep -a -o 'strada [a-z]* (chiesta «[a-z]*»)' /var/lib/rete11/registro.log | sort | uniq -c | tr '\n' ';'")"
PF0=$(S journalctl -k --no-pager 2>/dev/null | grep -c 'page fault')
RS0=$(S journalctl -k --no-pager 2>/dev/null | grep -c 'GPU reset begin')
EV=/media/REMOTIX/misure/fase15/giro19-diagnosi/$ETI
mkdir -p "$EV"
export XDG_RUNTIME_DIR=/run/user/$(id -u)
bash /media/REMOTIX/src/controllo/banchi/15-suite/15-una.sh 15-f018-riattacco-a-misura-diversa.py --scatola $D --browser firefox --guasto --evidenze "$EV" > "$EV/uscita.log" 2>&1
echo "codice della prova: $?"
grep -a '^SUITE' "$EV/uscita.log" | python3 -c '
import sys, json
for r in sys.stdin:
    j = json.loads(r[6:]); print("  ", j["funzione"], j["passata"], j["esito"], "·", (j.get("ragione") or "")[:150])'
PF1=$(S journalctl -k --no-pager 2>/dev/null | grep -c 'page fault')
RS1=$(S journalctl -k --no-pager 2>/dev/null | grep -c 'GPU reset begin')
echo "page fault della scheda: $((PF1 - PF0)) · reset: $((RS1 - RS0))"
echo "nel registro della scatola: $(S podman exec rete11-$D sh -c "grep -a -c 'DEVICE_LOST' /var/lib/rete11/registro.log") DEVICE_LOST · tele: $(S podman exec rete11-$D sh -c "grep -a -o 'tela nuova [0-9x]*: riaperto' /var/lib/rete11/registro.log | tr '\n' ';'")"
S podman exec rete11-$D sh -c "grep -a -E '⛔.*(codific|Vulkan|VA-API|vaapi|palco .* se n)' /var/lib/rete11/registro.log | grep -a -v 'nessuno gli dice' | cut -c1-200 | head -6"
