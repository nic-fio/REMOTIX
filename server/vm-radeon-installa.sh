#!/bin/bash
# vm-radeon-installa.sh <ubuntu|kubuntu|xubuntu|lubuntu> <package.deb> [snapshot-label] - install a REMOTIX .deb in one VM as the administrator would
# (apt-get install ./x.deb, systemctl enable --now remotix), WITHOUT the Radeon and WITHOUT opening any session; report what came in and how the
# service started; orderly poweroff; snapshot (default label: 'uniO<n>' taken from the file name, else 'installato').  Repeatable with another .deb:
# the label must be new (istantanea refuses an existing one).  Memory for the VM: RX_VM_MEM (default 4G here).  Output: this script's stdout
# (use /media/REMOTIX-UBUNTU/log/vm-radeon-installa-<name>.log).  Nothing is restored or deleted.
set -uo pipefail
NAME=${1:?usage: $0 ubuntu|kubuntu|xubuntu|lubuntu package.deb [label]}; DEB=${2:?package.deb}
R=/media/REMOTIX-UBUNTU/vm-radeon V=$R/vm-radeon.sh PASS=prova2026
case $NAME in ubuntu) P=2441;; kubuntu) P=2442;; xubuntu) P=2443;; lubuntu) P=2444;; *) echo "bad name"; exit 2;; esac
[ -f "$DEB" ] || { echo "no such file: $DEB"; exit 2; }
LABEL=${3:-$(basename "$DEB" | grep -oE 'unione[0-9]+' | head -1)}; LABEL=${LABEL:-installato}
export RX_VM_MEM=${RX_VM_MEM:-4G}
S() { ssh -i "$R/$NAME/vmkey" -p $P -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=5 prova@127.0.0.1 "$@"; }
SU() { S "echo $PASS | sudo -S -p '' env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a $*"; }
echo "=== $NAME: package $(basename "$DEB") sha256 $(sha256sum "$DEB" | cut -d' ' -f1), VM memory $RX_VM_MEM"
for i in $(seq 120); do "$V" prova-avvio "$NAME" --resta && break; echo "(lock busy or start failed, retry $i)"; sleep 20; done
S true || { echo "FAIL: VM not reachable"; exit 1; }
echo "kernel: $(S uname -r)"
scp -q -i "$R/$NAME/vmkey" -P $P -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR "$DEB" prova@127.0.0.1:/tmp/remotix.deb || { echo "FAIL: scp"; exit 1; }
S "ls /dev/dri; dpkg -l 2>/dev/null | grep -E '^ii +(labwc|dconf-cli|remotix) ' | cut -c1-80" 
echo "=== apt-get install --reinstall ./remotix.deb (same version over an older build needs --reinstall; on a clean VM it is a plain install)"
S "echo $PASS | sudo -S -p '' env DEBIAN_FRONTEND=noninteractive NEEDRESTART_MODE=a apt-get install -y --reinstall /tmp/remotix.deb" 2>&1 | tail -40
S "dpkg -s remotix >/dev/null 2>&1" || { echo "FAIL: remotix is not installed (see the apt lines above); VM left running, nothing restored"; exit 1; }
echo "=== systemctl enable --now remotix"
SU systemctl enable --now remotix 2>&1 | tail -3
MARK=$(S "date '+%Y-%m-%d %H:%M:%S'"); SU systemctl restart remotix   # a fresh start of the NEW binary; the journal below is read from MARK on
sleep 8
echo "=== installed as dependencies (last apt transaction)"
S "grep -E '^(Start-Date|Commandline|Install):' /var/log/apt/history.log | tail -3 | cut -c1-2500"
echo "=== package relations"
S "dpkg -s remotix | grep -E '^(Version|Depends|Recommends|Suggests):' | cut -c1-600; for p in labwc dconf-cli; do echo -n \"\$p: \"; dpkg -s \$p 2>/dev/null | grep -E '^Status' || echo not installed; done"
echo "=== service and journal"
S "systemctl is-active remotix; systemctl is-enabled remotix"
S "journalctl -u remotix --since \"$MARK\" --no-pager | grep -E 'walls in force|§5.1|⚠|⛔|D-015|logind unreachable|dconf' | cut -c1-330 | head -25"
echo "=== aa-status | grep remotix"; S "echo $PASS | sudo -S -p '' aa-status 2>&1 | grep -i remotix"
echo "=== port 7447 in the VM"; S "ss -tlnu | grep 7447"
echo "=== /etc/remotix"; S "ls -la /etc/remotix 2>&1; ls /etc/remotix/* 2>/dev/null | head -20"
echo "=== /etc/dconf/db/remotix*"; S "ls -la /etc/dconf/db/ 2>&1 | head; ls -la /etc/dconf/db/remotix* /etc/dconf/profile 2>&1 | head -12"
echo "=== installed version"; S "dpkg -s remotix | grep -E '^Version'; sha256sum /usr/libexec/remotix/remotix | cut -c1-16"
echo "=== poweroff"
# the lock may be held for a moment by another agent's start/stop: retry, and report only what really happened
for i in $(seq 60); do "$V" spegni "$NAME" && [ "$("$V" stato "$NAME" | head -1)" = stopped ] && break; sleep 15; done
[ "$("$V" stato "$NAME" | head -1)" = stopped ] || { echo "FAIL: VM $NAME is still running; no snapshot taken"; exit 1; }
for i in $(seq 60); do "$V" istantanea "$NAME" "$LABEL" | tee /tmp/rx-snap-$NAME.out; grep -q "created" /tmp/rx-snap-$NAME.out && break; sleep 15; done
grep -q "created" /tmp/rx-snap-$NAME.out || { echo "FAIL: snapshot $LABEL not created"; exit 1; }
echo "=== $NAME done (snapshot $LABEL)"
