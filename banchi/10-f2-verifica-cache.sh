#!/bin/bash
# ===========================================================================
# 10-f2-verifica-cache.sh — ⛔ IL PREDICATO NUOVO DI `src/provisiona.sh`,
# provato da solo sui MIEI utenti.
#
# ⛔ PERCHE' NON SI PROVA CHIAMANDO `provisiona.sh`: quel programma lavora su
#    `prova` e `prova2`, che non sono miei.  L'isolamento e' la regola che fa
#    fallire tutte le altre se la si rompe ⇒ qui il predicato e' TRASCRITTO
#    LETTERALMENTE e messo alla prova su `provanic2` / `provanic3`.
#    ⚠ Se un giorno cambia la', cambia anche qui, o i due si mentono.
#
#   uso:  10-f2-verifica-cache.sh <UTENTE>
#   esce 0 verde · 1 rosso
# ===========================================================================
set -uo pipefail

n=${1:?serve un utente}

if [ -L "/home/$n/.cache" ]; then
	echo "   ⛔ NO  $n ha ~/.cache come COLLEGAMENTO a $(readlink "/home/$n/.cache"): il browser non fara' il profilo"
	exit 1
elif su -s /bin/sh -c "mkdir -p /home/$n/.cache/.prova-remotix && rmdir /home/$n/.cache/.prova-remotix" "$n" 2>/dev/null; then
	echo "   ⭐ OK  $n puo' scrivere nella sua ~/.cache (il profilo del browser ci sta)"
	exit 0
else
	echo "   ⛔ NO  $n NON puo' scrivere nella sua ~/.cache: il browser dira' «Profile Missing»"
	exit 1
fi
