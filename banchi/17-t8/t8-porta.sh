#!/usr/bin/env bash
#
# ⛔ STORIA (10 ott 2026, DECISIONI §10.36): questo banco prova un installatore che non c'è più —
#   piano/approva/applica separati, archivio firmato e install.sh, archivi di terzi, firewall e
#   cinture messi dal motore, file di risposte. Oggi: un .run, `install` con la domanda [y/N], e
#   REMOTIX che non modifica il sistema. Resta come storia delle prove del 29 set - 1 ott 2026; il giro
#   vero è banchi/17-distro/17-t10.sh. Non si lancia.
# t8-porta.sh — porta sul server l'archivio di prova e il banco di T8, e accende i due server HTTP.
#
#   (sul portatile)   [DOVE=nome PORTA=n] bash banchi/17-t8/t8-porta.sh [archivio] [terzi]
#
#   /media/REMOTIX/vm17/$DOVE/     l'archivio di REMOTIX (DOVE=archivio), su 127.0.0.1:$PORTA (8717;
#                                  dalla VM: 10.0.2.2:$PORTA). Un archivio SUO (per esempio quello di
#                                  packaging/rilascio.sh: DOVE=rilascio PORTA=8737) non tocca quello
#                                  di T8, che altri banchi usano
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
DOVE=${DOVE:-archivio}
PORTA=${PORTA:-8717}
tar -C "$A" -cf - . | ssh -o BatchMode=yes $S "rm -rf $V/$DOVE.nuovo && mkdir -p $V/$DOVE.nuovo $V/t8 && tar -C $V/$DOVE.nuovo -xf - && rm -rf $V/$DOVE && mv $V/$DOVE.nuovo $V/$DOVE"
if [ -d "$TZ_" ]; then
	tar -C "$TZ_" -cf - . | ssh -o BatchMode=yes $S "rm -rf $V/terzi && mkdir -p $V/terzi && tar -C $V/terzi -xf -"
fi
scp -q "$QUI/t8-vm.sh" "$QUI/t8-browser.py" $S:$V/t8/
scp -q "$ALBERO/banchi/17-distro/17-t1c-guarda.sh" $S:$V/t1c/
# ⚠ due ssh separati: pkill -f nella stessa riga di chi accende trova la shell di ssh e la uccide;
#   [h] evita che trovi sé stesso
ssh -o BatchMode=yes $S "pkill -f '[h]ttp.server $PORTA '; pkill -f '[h]ttp.server 8719 '" 2>&1 | grep -v tput || true
ssh -o BatchMode=yes $S "
for p in $PORTA:$V/$DOVE 8719:$V/terzi; do
	n=\${p%%:*}; d=\${p#*:}
	[ -d \$d ] && (setsid nohup python3 -m http.server \$n --bind 127.0.0.1 --directory \$d >$V/t8/http-\$n.log 2>&1 </dev/null &)
done
sleep 1
curl -s -o /dev/null -w 'archivio ($DOVE): %{http_code}\n' http://127.0.0.1:$PORTA/chiavi/LEGGIMI
curl -s -o /dev/null -w 'terzi: %{http_code}\n' http://127.0.0.1:8719/terzi.asc" 2>&1 | grep -v tput
