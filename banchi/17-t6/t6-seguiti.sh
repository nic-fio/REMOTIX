#!/bin/bash
# t6-seguiti.sh <machine> <packages folder> [options] — point 1 (PAM_RHOST) and 3 (level) on a VM, from the "client" snapshot
m=$1; P=$2; opt=${3:-}; photo=${SNAPSHOT:-client}; cd /media/REMOTIX/vm17/t6  # packages in t6/pacchetti-seguiti/<target>; SNAPSHOT=iso and BEFORE="<root command>" in the environment
r() { bash t6-vm.sh "$m" "$@" 2>&1 | grep -v tput; }
r start "$photo" || exit 1
r engine $P/* >/dev/null
r install "$opt"
[ -n "${BEFORE:-}" ] && r cmd "$BEFORE"
r faillock reset >/dev/null
r enter prova "" giusta | grep -v journal
r enter prova sbagliata sbagliata1 | grep -v journal
r unban >/dev/null
r enter prova sbagliata sbagliata2 | grep -v journal
r unban >/dev/null
echo "== faillock"; r faillock
echo "== journal"; r cmd 'journalctl -b --no-pager -o cat | grep -aE "remotix:auth|pam_faillock|SELinux: the desktop" | tail -6'
echo "== session"; r session
r avc
r faillock reset >/dev/null
r stop "$photo"
