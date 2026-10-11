#!/bin/bash
#
# t6-round.sh — phase 17, T6: the whole round on ONE machine, from snapshot to snapshot.
#
#   (on the server, as nicfio)   sg kvm -c 'bash t6-round.sh <machine> <snapshot> <target> "<plan options>" [faillock-on] [faillock-off]'
#   e.g.  bash t6-round.sh alma10-gnome-iso iso alma10 "--apri-firewall --deposito epel,rpmfusion" \
#            "authselect enable-feature with-faillock" "authselect disable-feature with-faillock"
#
#   0. (BEFORE="<command>" in the environment: a root command right after power-on, e.g. ufw on)
#   1. power on from the snapshot; the firewall BEFORE (zone, rules, files in /etc/firewalld/zones and sha256)
#   2. the engine installs the packages of packets/<target> (one transaction: remotix and, where present,
#      remotix-selinux) with the given plan; the firewall AFTER
#   3. R19/R20: Chrome enters (new session), re-enters (resume), the service restarted with the desktop alive and
#      re-enter, wrong password, root; the logind sessions (Class, Remote) and the contexts; the SELinux
#      denials since the start of point 3
#   4. R20 faillock (if the command that turns it on is given): three errors from REMOTIX ⇒ the account locked for
#      ssh too; `faillock --reset` ⇒ both can get in again
#   5. uninstall --purge; the firewall AFTER UNINSTALLATION; the denials of the whole round
#   6. power off and back to the snapshot
# Evidence in /media/REMOTIX/vm17/t6/outcomes/<machine>/ (giro.txt is the summary).
set -uo pipefail
m=${1:?machine}; photo=${2:?photo}; b=${3:?target}; opt=${4:-}; fl_on=${5:-}; fl_off=${6:-}
T6=/media/REMOTIX/vm17/t6
E=$T6/esiti/$m
P=$T6/pacchetti/$b
r() { bash "$T6/t6-vm.sh" "$m" "$@" 2>&1 | grep -v tput; }
fine() { r stop "$photo"; }

r start "$photo" || exit 1
trap fine EXIT
exec > >(tee "$E/giro.txt") 2>&1
echo "== $m ($photo), packages of $b: $(ls "$P" | tr '\n' ' ')"
[ -n "${BEFORE:-}" ] && { echo "== 0. before: $BEFORE"; r cmd "$BEFORE"; }
echo "== 1. the firewall before"; r firewall | grep -vE '^(totale|d[rwx-]{9})'
echo "== 2. install"
f=(); for x in "$P"/*; do case $x in *debug*) ;; *) f+=("$x");; esac; done
r engine "${f[@]}" >/dev/null
r install "$opt"
echo "== the firewall after installation"; r firewall | grep -vE '^(totale|d[rwx-]{9})'
START=$(r cmd "date +%T" | tail -1)
echo "== 3. R19/R20 (VM time: $START)"
r enter prova "" prima | grep -v journal
r enter prova "" seconda | grep -v journal
r cmd "systemctl restart remotix; sleep 3; systemctl is-active remotix"
r enter prova "" dopo-riavvio | grep -v journal
r enter prova sbagliata sbagliata
r unban >/dev/null
r enter root "" root
r unban >/dev/null
r session
r avc "$START"
if [ -n "$fl_on" ]; then
	echo "== 4. R20 faillock: $fl_on"
	r cmd "$fl_on"
	r faillock reset >/dev/null
	for i in 1 2 3; do r enter prova sbagliata sbagliata$i | grep -v journal; r unban >/dev/null; done
	r faillock
	echo "-- the RIGHT password, from REMOTIX and from ssh:"
	r enter prova "" chiuso
	r ssh-password
	r unban >/dev/null
	echo "-- faillock --reset, and again:"
	r faillock reset | tail -2
	r enter prova "" sbloccato | grep -v journal
	r ssh-password
	[ -n "$fl_off" ] && r cmd "$fl_off"
fi
echo "== 5. uninstall"
r uninstall
echo "== the firewall after uninstallation"; r firewall | grep -vE '^(totale|d[rwx-]{9})'
echo "== the SELinux denials of the whole round"
r avc "$START"
