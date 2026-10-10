#!/bin/bash
# 19-f018-prova.sh — ONE F-018 test (reattach at a different size) on rete11-lxqt
# on the Radeon, with the chosen binary and route, and the count of the card's
# page faults before and after (diagnosis of the FAIL of round 19-radeon).
#
#   (on the server, as nicfio)  bash 19-f018-prova.sh <md5-of-the-binary> <scheda|vaapi|vulkan> <label>
#
# The binary is /media/REMOTIX/rete11/prodotto/remotix.<md5>; the route is
# the server's --codifica option (restarted by hand with the same line as
# 11-accendi.sh server, plus --codifica).  It leaves /media/REMOTIX/rete11/prodotto/remotix
# = the chosen binary: the caller puts it back afterwards.
set -u
MD5=$1; STRADA=$2; ETI=$3
D=${REMOTIX_D:-lxqt}; case $D in gnome) PORTA=8511;; kde) PORTA=8512;; xfce) PORTA=8513;; *) PORTA=8514;; esac
R=/media/REMOTIX/rete11
PAROLA=$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh")
S() { printf '%s\n' "$PAROLA" | sudo -S -p '' "$@"; }
cd $R || exit 2
cp "prodotto/remotix.$MD5" prodotto/remotix || exit 2
echo "binary $(md5sum prodotto/remotix | cut -c1-8) · route $STRADA · $(date +%T)"
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
	for _ in $(seq 1 40); do S podman exec rete11-$D grep -q 'ready: https' /var/lib/rete11/registro.log 2>/dev/null && break; sleep 0.5; done
fi
echo "routes at startup: $(S podman exec rete11-$D sh -c "grep -a -o 'route [a-z]* (requested «[a-z]*»)' /var/lib/rete11/registro.log | sort | uniq -c | tr '\n' ';'")"
PF0=$(S journalctl -k --no-pager 2>/dev/null | grep -c 'page fault')
RS0=$(S journalctl -k --no-pager 2>/dev/null | grep -c 'GPU reset begin')
EV=/media/REMOTIX/misure/fase15/giro19-diagnosi/$ETI
mkdir -p "$EV"
export XDG_RUNTIME_DIR=/run/user/$(id -u)
bash /media/REMOTIX/src/controllo/banchi/15-suite/15-una.sh 15-f018-riattacco-a-misura-diversa.py --scatola $D --browser firefox --guasto --evidenze "$EV" > "$EV/uscita.log" 2>&1
echo "code of the test: $?"
grep -a '^SUITE' "$EV/uscita.log" | python3 -c '
import sys, json
for r in sys.stdin:
    j = json.loads(r[6:]); print("  ", j["funzione"], j["passata"], j["esito"], "·", (j.get("ragione") or "")[:150])'
PF1=$(S journalctl -k --no-pager 2>/dev/null | grep -c 'page fault')
RS1=$(S journalctl -k --no-pager 2>/dev/null | grep -c 'GPU reset begin')
echo "page faults of the card: $((PF1 - PF0)) · resets: $((RS1 - RS0))"
echo "in the box's log: $(S podman exec rete11-$D sh -c "grep -a -c 'DEVICE_LOST' /var/lib/rete11/registro.log") DEVICE_LOST · canvases: $(S podman exec rete11-$D sh -c "grep -a -o 'new canvas [0-9x]*: reopened' /var/lib/rete11/registro.log | tr '\n' ';'")"
S podman exec rete11-$D sh -c "grep -a -E '⛔.*(encod|decod|Vulkan|VA-API|vaapi|stage .* has gone)' /var/lib/rete11/registro.log | grep -a -v 'nobody tells it' | cut -c1-200 | head -6"
