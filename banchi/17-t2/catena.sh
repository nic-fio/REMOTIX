#!/bin/sh
# catena.sh DIR — the journal lines that tell the end, from the action onwards
cd /media/REMOTIX/tmp/t2/$1 || exit 1
T=$(sed -n 3p azione.txt | cut -c8-15)
echo "action: $(head -1 azione.txt) at $(sed -n 3p azione.txt)"
awk -v t="$T" '$3>=t' journal.txt | grep -E "Stopping rete11|rete11-server.service|shut down|the parent closed|dismantling|exiting|Session c[0-9]+|Removed session|Stopped|Stopping|session closed|Deactivated|Failed|Killing|killed|code=|terminat" | grep -vE "the rate|loop:|GET /|says:|run-p|session-c[0-9]+\.scope: Deactivated|o-bridge|sd-pam" | head -${2:-25} | cut -c1-260
echo "-- recorded deaths (excluding sleep and bench commands):"
grep MORTO vita.txt | grep -vE " sleep | sh +/init.scope| systemctl | date | cat | grep | ps | awk | head | pgrep | tail | python3 | journalctl | loginctl | id | cut | sort | runuser| podman" | head -${3:-20} | cut -c1-150
