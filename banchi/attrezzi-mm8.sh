#!/bin/bash
set -uo pipefail
E=/media/REMOTIX/enter.sh; D=/srv/src
C="python3 -u $D/01-b8-cronometro.py --bersaglio innesto --porta 7447 --indirizzi 127.0.0.1,192.168.0.2 --utente prova --parola parola-di-prova"
ripulisci() {
  bash $E --root "python3 $D/01-b12-guasti.py --togli B8" >/dev/null 2>&1
  bash $E --root "ninja -C $D/b2/ngtcp2/build bsslserver" >/dev/null 2>&1
  echo "== ripulito e ricostruito"
}
trap ripulisci EXIT
bash $E --root "python3 $D/01-b12-guasti.py --applica B8" 2>&1 | tail -1
bash $E --root "ninja -C $D/b2/ngtcp2/build bsslserver" >/dev/null 2>&1 || { echo "compilazione fallita"; exit 3; }
bash $E --root "nohup env LD_LIBRARY_PATH=$D/b2/ngtcp2/build/lib $D/b2/ngtcp2/build/examples/bsslserver --timeout=120s 0.0.0.0 7447 /media/REMOTIX/b2-certificati/sessione.key /media/REMOTIX/b2-certificati/sessione.pem < /dev/null > $D/mm.log 2>&1 & echo \$! > $D/mm.pid"
sleep 2
PID=$(cat /media/REMOTIX/src/mm.pid)
bash $E --root "rm -f $D/mm8.jsonl; $C --campioni --blocco 1 --giro mm8 --uscita $D/mm8.jsonl > $D/mm-uscita.txt 2>&1"
echo "CAMPIONI=$?"
bash $E --root "$C --verdetto --giro mm8 --uscita $D/mm8.jsonl >> $D/mm-uscita.txt 2>&1"
echo "VERDETTO=$?"
bash $E --root "kill $PID" >/dev/null 2>&1
