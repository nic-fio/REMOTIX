#!/bin/bash
# t6-seguiti.sh <machine> <packages folder> [options] — point 1 (PAM_RHOST) and 3 (level) on a VM, from the "cliente" snapshot
m=$1; P=$2; opz=${3:-}; foto=${FOTO:-cliente}; cd /media/REMOTIX/vm17/t6  # packages in t6/pacchetti-seguiti/<target>; FOTO=iso and PRIMA="<root command>" in the environment
r() { bash t6-vm.sh "$m" "$@" 2>&1 | grep -v tput; }
r accendi "$foto" || exit 1
r motore $P/* >/dev/null
r installa "$opz"
[ -n "${PRIMA:-}" ] && r cmd "$PRIMA"
r faillock reset >/dev/null
r entra prova "" giusta | grep -v journal
r entra prova sbagliata sbagliata1 | grep -v journal
r ban-via >/dev/null
r entra prova sbagliata sbagliata2 | grep -v journal
r ban-via >/dev/null
echo "== faillock"; r faillock
echo "== journal"; r cmd 'journalctl -b --no-pager -o cat | grep -aE "remotix:auth|pam_faillock|SELinux: the desktop" | tail -6'
echo "== session"; r sessione
r avc
r faillock reset >/dev/null
r spegni "$foto"
