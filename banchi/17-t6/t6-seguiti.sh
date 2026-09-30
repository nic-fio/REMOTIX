#!/bin/bash
# t6-seguiti.sh <macchina> <cartella pacchetti> [opzioni] — punto 1 (PAM_RHOST) e 3 (livello) su una VM, dalla foto «cliente»
m=$1; P=$2; opz=${3:-}; foto=${FOTO:-cliente}; cd /media/REMOTIX/vm17/t6  # pacchetti in t6/pacchetti-seguiti/<bersaglio>; FOTO=iso e PRIMA="<comando da root>" nell ambiente
r() { bash t6-vm.sh "$m" "$@" 2>&1 | grep -v tput; }
r accendi "$foto" || exit 1
r motore $P/* >/dev/null
r installa "$opz"
[ -n "${PRIMA:-}" ] && r cmd "$PRIMA"
r faillock reset >/dev/null
r entra prova "" giusta | grep -v giornale
r entra prova sbagliata sbagliata1 | grep -v giornale
r ban-via >/dev/null
r entra prova sbagliata sbagliata2 | grep -v giornale
r ban-via >/dev/null
echo "== faillock"; r faillock
echo "== giornale"; r cmd 'journalctl -b --no-pager -o cat | grep -aE "remotix:auth|pam_faillock|SELinux: il desktop" | tail -6'
echo "== sessione"; r sessione
r avc
r faillock reset >/dev/null
r spegni "$foto"
