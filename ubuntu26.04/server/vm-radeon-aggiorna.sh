#!/bin/bash
# vm-radeon-aggiorna.sh <kubuntu|xubuntu|lubuntu> - update one VM as a user would after installing, WITHOUT the Radeon:
# boot with a virtual card (prova-avvio --resta), apt full-upgrade + snap refresh, reboot, check (as prova-avvio does), orderly poweroff, snapshot 'aggiornato'.
# Long output goes to /media/REMOTIX-UBUNTU/log/vm-radeon-aggiorna-<name>.log (this script's own stdout).  Nothing is restored or deleted here.
set -uo pipefail
NAME=${1:?usage: $0 kubuntu|xubuntu|lubuntu}
R=/media/REMOTIX-UBUNTU/vm-radeon V=$R/vm-radeon.sh PASS=prova2026
case $NAME in kubuntu) P=2442;; xubuntu) P=2443;; lubuntu) P=2444;; *) echo "bad name"; exit 2;; esac
S() { ssh -i "$R/$NAME/vmkey" -p $P -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=5 prova@127.0.0.1 "$@"; }
SU() { S "echo $PASS | sudo -S -p '' env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a $*"; }
echo "=== $NAME: start without the Radeon"
for i in $(seq 120); do "$V" prova-avvio "$NAME" --resta && break; echo "(lock busy or start failed, retry $i)"; sleep 20; done
S true || { echo "VM not reachable"; exit 1; }
BEFORE=$(S uname -r); echo "kernel before: $BEFORE"
echo "=== apt update + full-upgrade"
SU apt-get update 2>&1 | tail -3
SU apt-get -y -o Dpkg::Options::=--force-confold -o Dpkg::Options::=--force-confdef full-upgrade 2>&1 | tail -25
echo "=== snap refresh"
SU snap refresh 2>&1 | tail -15
echo "=== reboot"
S "echo $PASS | sudo -S -p '' systemctl reboot" 2>/dev/null
sleep 40
for i in $(seq 100); do S true 2>/dev/null && break; sleep 3; done
S true || { echo "FAIL: no ssh after the reboot (see $R/$NAME/serial.log); VM left running, nothing restored"; exit 1; }
sleep 25
echo "kernel before: $BEFORE"
S "echo -n 'kernel after: '; uname -r; echo -n 'display-manager: '; systemctl is-active display-manager; readlink /etc/systemd/system/display-manager.service; echo 'loginctl list-sessions:'; loginctl list-sessions --no-legend; echo 'aa-status:'; echo $PASS | sudo -S -p '' aa-status 2>&1 | head -3; echo 'snap list:'; snap list 2>&1 | head -25; echo -n 'hostname: '; hostname; getent passwd prova prova2 | cut -d: -f1,6; ls /dev/dri; echo 'apt upgradable after:'; apt list --upgradable 2>/dev/null | tail -n +2 | wc -l; echo 'failed units:'; systemctl --failed --no-legend | head"
echo "=== poweroff"
"$V" spegni "$NAME"
"$V" istantanea "$NAME" aggiornato
echo "=== $NAME done"
