#!/bin/bash
# misura-marca.sh — innesta un guasto, lancia il banco catturando TUTTO,
# poi lo toglie E RICOSTRUISCE (R12-A.6: sorgente sano e binario bugiardo
# e' peggio di tutt'e due guasti).
set -uo pipefail
SIGLA=$1; shift
COMANDO="$*"
E=/media/REMOTIX/enter.sh
D=/srv/src
ripulisci() {
  bash $E --root "python3 $D/01-b12-guasti.py --togli $SIGLA" >/dev/null 2>&1
  bash $E --root "ninja -C $D/b2/ngtcp2/build bsslserver" >/dev/null 2>&1
  echo "== ripulito e ricostruito"
}
trap ripulisci EXIT
bash $E --root "python3 $D/01-b12-guasti.py --applica $SIGLA" 2>&1 | tail -2
bash $E --root "ninja -C $D/b2/ngtcp2/build bsslserver" >/dev/null 2>&1 || { echo "⛔ compilazione fallita"; exit 3; }
bash $E --root "nohup env LD_LIBRARY_PATH=$D/b2/ngtcp2/build/lib $D/b2/ngtcp2/build/examples/bsslserver --timeout=120s 0.0.0.0 7447 /media/REMOTIX/b2-certificati/sessione.key /media/REMOTIX/b2-certificati/sessione.pem < /dev/null > $D/mm.log 2>&1 & echo \$! > $D/mm.pid"
sleep 2
PID=$(cat /media/REMOTIX/src/mm.pid)
bash $E --root "$COMANDO > $D/mm-uscita.txt 2>&1"
echo "USCITA-BANCO=$?"
bash $E --root "kill $PID" >/dev/null 2>&1
