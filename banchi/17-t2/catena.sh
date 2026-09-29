#!/bin/sh
# catena.sh DIR — le righe del journal che raccontano la fine, dall'azione in poi
cd /media/REMOTIX/tmp/t2/$1 || exit 1
T=$(sed -n 3p azione.txt | cut -c8-15)
echo "azione: $(head -1 azione.txt) alle $(sed -n 3p azione.txt)"
awk -v t="$T" '$3>=t' journal.txt | grep -E "Stopping rete11|rete11-server.service|spento|il padre ha chiuso|smonto|esco|Session c[0-9]+|Removed session|Stopped|Stopping|session closed|Deactivated|Failed|Killing|killed|code=|terminat" | grep -vE "ritmo|ciclo:|GET /|dice:|run-p|session-c[0-9]+\.scope: Deactivated|o-bridge|sd-pam" | head -${2:-25} | cut -c1-260
echo "-- morti registrate (esclusi sleep e comandi del banco):"
grep MORTO vita.txt | grep -vE " sleep | sh +/init.scope| systemctl | date | cat | grep | ps | awk | head | pgrep | tail | python3 | journalctl | loginctl | id | cut | sort | runuser| podman" | head -${3:-20} | cut -c1-150
