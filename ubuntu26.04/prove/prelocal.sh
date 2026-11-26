#!/bin/sh
# prelocal.sh BOX 1|2a|2b|3   BOX = gnome | kde | xfce | lxqt - «the local login closes the remote desktop» on gdm3 / sddm / lightdm / sddm (Ubuntu 26.04 VMs:
# ubuntu, kubuntu, xubuntu, lubuntu).  ⛔ NOT with the Radeon passed to the VM: restarting the display manager there froze the whole server (see COME-SI-LANCIA.md).
# Run ON THE DEV SERVER (the prove/ folder is PROVE_DIR, default /media/REMOTIX-UBUNTU/tmp/prove-run/prove), with the VM switched on, the package installed and the service enabled; user lc1 must exist.
#   1  remote desktop open -> local autologin of lc1 -> the remote closes, the local desktop stays
#   2a the same, but the remote leader is killed with SIGKILL first (orphan)      2b the same, but the service is restarted first
#   3  local session active -> a remote login of the same user is refused ("already signed in locally")
# (the autologin is a TEST-BENCH file written by banco-vm/autologin-gdm3.sh|autologin-lightdm.sh|autologin-sddm.sh; the DM is restarted: on sddm `systemctl reset-failed` first.)
BOX=$1; T=$2
cd ${PROVE_DIR:-/media/REMOTIX-UBUNTU/tmp/prove-run/prove}
case $BOX in gnome) AUTO=banco-vm/autologin-gdm3.sh; SH=gnome-shell; DM=gdm3 ;; xfce) AUTO=banco-vm/autologin-lightdm.sh; SH=xfce4-panel; DM=lightdm ;; lxqt) AUTO=banco-vm/autologin-sddm.sh; SH=lxqt-panel; DM=sddm ;; kde) AUTO=banco-vm/autologin-sddm.sh; SH=plasmashell; DM=sddm ;; *) echo "usage: $0 gnome|kde|xfce|lxqt 1|2a|2b|3"; exit 2 ;; esac
export RX_BANCO=vm
G() { timeout 150 banco-vm/box.sh ssh $BOX "$@" </dev/null; }
GS() { timeout 150 banco-vm/box.sh ssh $BOX "$@"; }
DMRESTART="systemctl reset-failed $DM 2>/dev/null; systemctl restart $DM"
GS "bash -s off x" < $AUTO >/dev/null 2>&1; sleep 8
G "loginctl terminate-user lc1 2>/dev/null; true"; sleep 3
if [ "$T" = 3 ]; then
  GS "bash -s on lc1" < $AUTO >/dev/null 2>&1; sleep 30
  echo "local session of lc1: $(G "loginctl list-sessions --no-legend | awk '\$3==\"lc1\" && \$4==\"seat0\"{print \$1, \$5, \$6}'"); shell: $(G "pgrep -u lc1 -c -x $SH")"
  RX_KEEP=1 RX_BOX=$BOX RX_USER=lc1 RX_PASS=lc1pass2026 timeout 170 python3 hold.py 5 > ../hold3-$BOX.log 2>&1; echo "hold rc=$?"
  grep -v tput ../hold3-$BOX.log | tail -3 | cut -c1-300
  echo "after: remotix sessions of lc1: $(G "loginctl list-sessions --no-legend | awk '\$3==\"lc1\" && \$7==\"remotix\"' | wc -l"); local sessions: $(G "loginctl list-sessions --no-legend | awk '\$3==\"lc1\" && \$4==\"seat0\"' | wc -l"); shell alive: $(G "pgrep -u lc1 -c -x $SH")"
  exit 0
fi
rm -f /tmp/hold-ready
RX_BOX=$BOX RX_USER=lc1 RX_PASS=lc1pass2026 nohup python3 hold.py 400 > ../hold-$BOX.log 2>&1 </dev/null &
for i in $(seq 1 70); do [ -f /tmp/hold-ready ] && break; sleep 2; done
echo "remote open: $(grep -c 'desktop ok' ../hold-$BOX.log); $(grep -h 'login:' ../hold-$BOX.log | cut -c1-90)"
echo "remote leader/desktop before: $(G "pgrep -u lc1 -c -x labwc") labwc, shell $(G "pgrep -u lc1 -c -x $SH")"
case $T in
 1) GS "bash -s on lc1" < $AUTO >/dev/null 2>&1 ;;
 2a) GS "bash -s on lc1 norestart" < $AUTO >/dev/null 2>&1; G "p=\$(ps -eo pid,user:8,comm | awk '\$2==\"lc1\" && \$3==\"remotix\"{print \$1}' | head -1); echo \"kill -9 of the remote leader \$p\"; kill -9 \$p; $DMRESTART" ;;
 2b) GS "bash -s on lc1 norestart" < $AUTO >/dev/null 2>&1; G "systemctl restart remotix; echo restarted-service; $DMRESTART" ;;
esac
G "for i in \$(seq 1 40); do line=''; for s in \$(loginctl list-sessions --no-legend | awk '\$3==\"lc1\"{print \$1}'); do line=\"\$line [\$s \$(loginctl show-session \$s -p Service -p Seat -p State --value | tr '\n' '/')]\"; done; echo \"t+\${i}s:\${line:- none}\"; sleep 1; done" | awk 'NR<=3 || NR==6 || NR==10 || NR==40'
G "echo local shell: \$(pgrep -u lc1 -c -x $SH), labwc left: \$(pgrep -u lc1 -c -x labwc); journalctl -b --no-pager --since -70sec | grep -E 'HELD|farewell|already running' | cut -c1-200 | tail -4"
sleep 25
G "echo 40 s later: local sessions \$(loginctl list-sessions --no-legend | awk '\$3==\"lc1\" && \$4==\"seat0\"' | wc -l), shell \$(pgrep -u lc1 -c -x $SH)"
GS "bash -s off x" < $AUTO >/dev/null 2>&1
