#!/usr/bin/env bash
# t8-porta.sh — porta sul server l'archivio di prova e il banco di T8, e accende i due server HTTP.
#
#   (sul portatile)   bash banchi/17-t8/t8-porta.sh [archivio] [terzi]
#
#   /media/REMOTIX/vm17/archivio/  l'archivio di REMOTIX, su 127.0.0.1:8717 (dalla VM: 10.0.2.2:8717)
#   /media/REMOTIX/vm17/terzi/     l'archivio DI TERZI di R18, su 127.0.0.1:8719
#   /media/REMOTIX/vm17/t8/        t8-vm.sh, t8-browser.py; t1c/17-t1c-guarda.sh aggiornato
# ⚠ Sul portatile non c'è rsync: tar via ssh. Il server HTTP è python3 -m http.server (solo lettura).
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
A=${1:-$ALBERO/costruzione-uscita/archivio}
TZ_=${2:-$ALBERO/costruzione-uscita/t8-terzi/terzi}
S=nicfio@192.168.0.2
V=/media/REMOTIX/vm17
tar -C "$A" -cf - . | ssh -o BatchMode=yes $S "rm -rf $V/archivio.nuovo && mkdir -p $V/archivio.nuovo $V/t8 && tar -C $V/archivio.nuovo -xf - && rm -rf $V/archivio && mv $V/archivio.nuovo $V/archivio"
if [ -d "$TZ_" ]; then
	tar -C "$TZ_" -cf - . | ssh -o BatchMode=yes $S "rm -rf $V/terzi && mkdir -p $V/terzi && tar -C $V/terzi -xf -"
fi
scp -q "$QUI/t8-vm.sh" "$QUI/t8-browser.py" $S:$V/t8/
scp -q "$ALBERO/banchi/17-distro/17-t1c-guarda.sh" $S:$V/t1c/
ssh -o BatchMode=yes $S "
for p in 8717:$V/archivio 8719:$V/terzi; do
	n=\${p%%:*}; d=\${p#*:}
	pgrep -f \"http.server \$n \" >/dev/null && pkill -f \"http.server \$n \"
	[ -d \$d ] && (setsid nohup python3 -m http.server \$n --bind 127.0.0.1 --directory \$d >$V/t8/http-\$n.log 2>&1 </dev/null &)
done
sleep 1
curl -s -o /dev/null -w 'archivio: %{http_code}\n' http://127.0.0.1:8717/chiavi/LEGGIMI
curl -s -o /dev/null -w 'terzi: %{http_code}\n' http://127.0.0.1:8719/terzi.asc" 2>&1 | grep -v tput
