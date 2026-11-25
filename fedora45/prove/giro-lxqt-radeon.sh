#!/bin/sh
# giro-lxqt-radeon.sh - the checks of the remote lxqt desktop WITH the Radeon (run 22 Nov 2026, results in docs/REGISTRO-problemi.md F22).
# Run ON THE DEV SERVER, from prove/, with the VM `lxqt` switched on WITH the card (vm-radeon.sh accendi lxqt), the package installed, the service enabled
# and the port opened as the administrator does (F20):  firewall-cmd --permanent --add-service=remotix && firewall-cmd --reload     (in the guest)
# The user lc1 must exist for prelocal.sh.  Not part of all.sh.
set -u
export RX_BANCO=vm
B=lxqt
for c in "check-base.py --browser chrome" check-input.py check-lifecycle.py check-clipboard.py check-audio.py check-desktop.py; do
  echo "== ${c%% *}"; python3 $c --box $B 2>&1 | grep -E "^(PASS|FAIL|BLOCKED)"
done
echo "== check-resize (10 re-attaches at other sizes, a terminal open)"; python3 check-resize.py --box $B --rounds 10 | grep -E "^(PASS|FAIL|RESULT)"
echo "== check-exit (terminate-session, service restart, close and wait 20 s)"; python3 check-exit.py --box $B | grep -E "^(PASS|FAIL|RESULT)"
for t in 1 2a 2b 3; do echo "== prelocal $t"; sh prelocal.sh $B $t; done
echo "== AVC at the end:  box.sh ssh $B 'ausearch -m avc -ts boot </dev/null'"
