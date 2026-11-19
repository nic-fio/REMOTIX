#!/bin/bash
# vm-radeon-controllo.sh <ubuntu|kubuntu|xubuntu|lubuntu> [--ripristina <label>] - short check of one VM WITH the Radeon:
# accendi (timed), Radeon/amdgpu/render node, remotix journal (walls, §5.1, encoder, no "CANNOT ENCODE"), display manager and greeter, ONE login as prova2
# (vm-radeon-login-test.py, picture saved in log/consegna/<name>.png), logout check, new warnings during the login, spegni (timed), optionally
# ripristina <label> (--ripristina implies the spegni first).  Without --ripristina the VM is left ON (no spegni).  Output: stdout (log in /media/REMOTIX-UBUNTU/log/consegna/).  Nothing is deleted.
set -uo pipefail
NAME=${1:?usage: $0 ubuntu|kubuntu|xubuntu|lubuntu [--ripristina label]}; LABEL=
[ "${2:-}" = --ripristina ] && LABEL=${3:?label}
R=/media/REMOTIX-UBUNTU/vm-radeon V=$R/vm-radeon.sh PASS=prova2026 OUT=/media/REMOTIX-UBUNTU/log/consegna
case $NAME in ubuntu) P=2341;; kubuntu) P=2342;; xubuntu) P=2343;; lubuntu) P=2344;; *) echo bad name; exit 2;; esac
S() { ssh -i "$R/$NAME/vmkey" -p $P -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -o ConnectTimeout=5 prova@127.0.0.1 "$@"; }
retry() { local i; for i in $(seq 60); do "$@" > /tmp/rx-ctl-$NAME.out 2>&1; local rc=$?; if grep -q "holds the lock" /tmp/rx-ctl-$NAME.out; then sleep 15; continue; fi; cat /tmp/rx-ctl-$NAME.out; return $rc; done; echo "lock busy for too long"; return 1; }
echo "=== $NAME: accendi"; SECONDS=0; retry "$V" accendi "$NAME"; echo "accendi took ${SECONDS}s"
S true || { echo "FAIL: no ssh"; exit 1; }
echo "=== in the VM"
S "uname -r; lspci -nnk | grep -A3 -E 'VGA|Display'; ls /dev/dri; echo -n 'display-manager: '; systemctl is-active display-manager; readlink /etc/systemd/system/display-manager.service; echo 'sessions:'; loginctl list-sessions --no-legend"
sleep 20
echo "=== remotix journal at start"
S "journalctl -b -u remotix --no-pager | grep -E 'walls in force|§5.1, the WATCHED|VULKAN VIDEO route|encoder [0-9] OPENED|VA-API|video.codec offered|CANNOT ENCODE' | cut -c1-300 | head -12; echo -n 'CANNOT ENCODE lines: '; journalctl -b -u remotix --no-pager | grep -c 'CANNOT ENCODE'"
echo "sessions before login:"; S "loginctl list-sessions --no-legend"
MARK=$(S "date '+%Y-%m-%d %H:%M:%S'")
echo "=== login as prova2"
python3 -I "$R/vm-radeon-login-test.py" "$NAME" --user prova2 --png "$OUT/$NAME.png" 2>&1 | grep -vE "^page log tail" | cut -c1-300; echo "login test exit: ${PIPESTATUS[0]}"
sleep 5
echo "=== after the test (browser closed)"; S "loginctl list-sessions --no-legend; ps -u prova2 -o pid,comm | head -8"
echo "=== new warnings during the login"
S "journalctl -u remotix --since \"$MARK\" --no-pager | grep -E '⚠|⛔' | cut -c1-260 | head -15"
S "journalctl -u remotix --since \"$MARK\" --no-pager > /tmp/rx-j.txt; echo $PASS | sudo -S -p '' cp /tmp/rx-j.txt /tmp/rx-j2.txt" >/dev/null 2>&1
S "journalctl -u remotix -b --no-pager" > "$OUT/journal-remotix-$NAME.txt" 2>&1
echo "=== logout: terminate-user prova2 only if sessions remain after 15 s"
sleep 15; N=$(S "loginctl list-sessions --no-legend | grep -c prova2"); echo "prova2 sessions left: $N"
if [ "$N" != 0 ]; then S "echo $PASS | sudo -S -p '' loginctl terminate-user prova2"; sleep 6; echo "after terminate-user:"; S "loginctl list-sessions --no-legend; ps -u prova2 -o pid,comm | head -5"; fi
if [ -z "$LABEL" ]; then echo "VM $NAME left ON (no --ripristina given: no spegni)"; echo "=== $NAME controllo done"; exit 0; fi
echo "=== spegni"; SECONDS=0; retry "$V" spegni "$NAME"; echo "spegni took ${SECONDS}s"
if [ -n "$LABEL" ]; then echo "=== ripristina $LABEL"; retry "$V" ripristina "$NAME" "$LABEL"; fi
echo "=== $NAME controllo done"
