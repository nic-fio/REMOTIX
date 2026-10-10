#!/bin/bash
#
# t6-giro.sh — phase 17, T6: the whole round on ONE machine, from snapshot to snapshot.
#
#   (on the server, as nicfio)   sg kvm -c 'bash t6-giro.sh <machine> <snapshot> <target> "<plan options>" [faillock-on] [faillock-off]'
#   e.g.  bash t6-giro.sh alma10-gnome-iso iso alma10 "--apri-firewall --deposito epel,rpmfusion" \
#            "authselect enable-feature with-faillock" "authselect disable-feature with-faillock"
#
#   0. (PRIMA="<command>" in the environment: a root command right after power-on, e.g. ufw on)
#   1. power on from the snapshot; the firewall BEFORE (zone, rules, files in /etc/firewalld/zones and sha256)
#   2. the engine installs the packages of pacchetti/<target> (one transaction: remotix and, where present,
#      remotix-selinux) with the given plan; the firewall AFTER
#   3. R19/R20: Chrome enters (new session), re-enters (resume), the service restarted with the desktop alive and
#      re-enter, wrong password, root; the logind sessions (Class, Remote) and the contexts; the SELinux
#      denials since the start of point 3
#   4. R20 faillock (if the command that turns it on is given): three errors from REMOTIX ⇒ the account locked for
#      ssh too; `faillock --reset` ⇒ both can get in again
#   5. uninstall --purge; the firewall AFTER UNINSTALLATION; the denials of the whole round
#   6. power off and back to the snapshot
# Evidence in /media/REMOTIX/vm17/t6/esiti/<machine>/ (giro.txt is the summary).
set -uo pipefail
m=${1:?macchina}; foto=${2:?foto}; b=${3:?bersaglio}; opz=${4:-}; fl_on=${5:-}; fl_off=${6:-}
T6=/media/REMOTIX/vm17/t6
E=$T6/esiti/$m
P=$T6/pacchetti/$b
r() { bash "$T6/t6-vm.sh" "$m" "$@" 2>&1 | grep -v tput; }
fine() { r spegni "$foto"; }

r accendi "$foto" || exit 1
trap fine EXIT
exec > >(tee "$E/giro.txt") 2>&1
echo "== $m ($foto), packages of $b: $(ls "$P" | tr '\n' ' ')"
[ -n "${PRIMA:-}" ] && { echo "== 0. before: $PRIMA"; r cmd "$PRIMA"; }
echo "== 1. the firewall before"; r firewall | grep -vE '^(totale|d[rwx-]{9})'
echo "== 2. install"
f=(); for x in "$P"/*; do case $x in *debug*) ;; *) f+=("$x");; esac; done
r motore "${f[@]}" >/dev/null
r installa "$opz"
echo "== the firewall after installation"; r firewall | grep -vE '^(totale|d[rwx-]{9})'
INIZIO=$(r cmd "date +%T" | tail -1)
echo "== 3. R19/R20 (VM time: $INIZIO)"
r entra prova "" prima | grep -v journal
r entra prova "" seconda | grep -v journal
r cmd "systemctl restart remotix; sleep 3; systemctl is-active remotix"
r entra prova "" dopo-riavvio | grep -v journal
r entra prova sbagliata sbagliata
r ban-via >/dev/null
r entra root "" root
r ban-via >/dev/null
r sessione
r avc "$INIZIO"
if [ -n "$fl_on" ]; then
	echo "== 4. R20 faillock: $fl_on"
	r cmd "$fl_on"
	r faillock reset >/dev/null
	for i in 1 2 3; do r entra prova sbagliata sbagliata$i | grep -v journal; r ban-via >/dev/null; done
	r faillock
	echo "-- the RIGHT password, from REMOTIX and from ssh:"
	r entra prova "" chiuso
	r ssh-parola
	r ban-via >/dev/null
	echo "-- faillock --reset, and again:"
	r faillock reset | tail -2
	r entra prova "" sbloccato | grep -v journal
	r ssh-parola
	[ -n "$fl_off" ] && r cmd "$fl_off"
fi
echo "== 5. uninstall"
r disinstalla
echo "== the firewall after uninstallation"; r firewall | grep -vE '^(totale|d[rwx-]{9})'
echo "== the SELinux denials of the whole round"
r avc "$INIZIO"
