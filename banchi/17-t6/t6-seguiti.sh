#!/bin/bash
# t6-seguiti.sh <machine> <packages folder> [options] — point 1 (PAM_RHOST) and 3 (level) on a VM, from the "client" snapshot
m=$1; P=$2; opt=${3:-}; picture=${PHOTO:-client}; cd /media/REMOTIX/vm17/t6  # packages in t6/pacchetti-seguiti/<target>; PHOTO=iso and BEFORE="<root command>" in the environment
r() { bash t6-vm.sh "$m" "$@" 2>&1 | grep -v tput; }
r turn_on "$picture" || exit 1
r motore $P/* >/dev/null
r install "$opt"
[ -n "${BEFORE:-}" ] && r cmd "$BEFORE"
r faillock reset >/dev/null
r enter prova "" giusta | grep -v journal
r enter prova wrong sbagliata1 | grep -v journal
r ban-via >/dev/null
r enter prova wrong sbagliata2 | grep -v journal
r ban-via >/dev/null
echo "== faillock"; r faillock
echo "== journal"; r cmd 'journalctl -b --no-pager -o cat | grep -aE "remotix:auth|pam_faillock|SELinux: the desktop" | tail -6'
echo "== session"; r session_v
r avc
r faillock reset >/dev/null
r turn_off "$picture"
