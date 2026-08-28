#!/bin/bash
# Lancia un giro del banco b16 sulla COPIA in albero e SEGNA il codice d'uscita.
#   uso: gira.sh <nome-giro>
set -u
NOME="$1"
cd /home/nicfio/b16-albero
export TMPDIR=/home/nicfio/b16-albero/tmp
python3 -u banchi/03-b16-dipinti.py \
    --porta 7615 --diagnosi 9615 --schermo :89 \
    > "uscite/${NOME}.txt" 2>&1
C=$?
echo "$C" > "uscite/${NOME}.codice"
echo "giro ${NOME}: codice d'uscita ${C}"
