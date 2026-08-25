#!/bin/bash
# ===========================================================================
# 10-f2-prepara.sh — prepara l'albero e la cartella di lavoro dell'incarico F2.
#
# ⛔ Gira da root SULLA MACCHINA DI PROVA.  Non tocca niente che non sia
#    `10f2-src` e `/media/REMOTIX/tmp/10f2`: l'isolamento e' la regola che fa
#    fallire tutte le altre se la si rompe.
# ===========================================================================
set -eu

ALBERO=/media/REMOTIX/src/10f2-src
LAV=/media/REMOTIX/tmp/10f2
SORGENTE=/media/REMOTIX/src/10fin-src

if [ ! -d "$ALBERO" ]; then
	cp -a "$SORGENTE" "$ALBERO"
fi
mkdir -p "$LAV" "$LAV/rilievo"
chmod 1777 "$LAV/rilievo"
if [ ! -d "$LAV/certificati" ]; then
	cp -a /media/REMOTIX/tmp/10nic/certificati "$LAV/certificati"
fi
printf 'remotix' > "$LAV/parola"
chmod 600 "$LAV/parola"

echo "albero: $(ls -la "$ALBERO/src/remotix")"
echo "lavoro: $(ls "$LAV" | tr '\n' ' ')"
