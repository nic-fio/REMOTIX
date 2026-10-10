#!/bin/bash
#
# t6-leggi-pam.sh — phase 17, T6: a machine's PAM stacks for the stock remote login (sshd),
# with SELinux, firewall and faillock, to compare them line by line with src/remotix.pam*.
#
#   (on the server)   sg kvm -c 'bash t6-leggi-pam.sh <machine> <snapshot>'
#
# Starts from the snapshot, reads, powers off and goes back to the snapshot. Output in /media/REMOTIX/vm17/t6/pam/<machine>.txt
set -uo pipefail
m=${1:?machine}; foto=${2:?photo}
R=/media/REMOTIX/vm17; V="bash $R/17-vm.sh"; O=$R/t6/pam
mkdir -p "$O"
if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m is already running"; exit 2; fi
[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ 4 VMs already running"; exit 2; }
$V torna "$m" "$foto" >/dev/null || exit 1
$V avvia "$m" >"$O/$m-avvia.log" 2>&1 || { echo "⛔ avvia"; tail -3 "$O/$m-avvia.log"; $V ferma "$m" >/dev/null 2>&1; exit 1; }
$V ssh "$m" 'sudo bash -s' >"$O/$m.txt" 2>&1 <<'DENTRO'
grep ^PRETTY /etc/os-release
for d in /etc/pam.d /usr/lib/pam.d /usr/etc/pam.d; do [ -d $d ] && echo "$d: $(ls $d | tr '\n' ' ')"; done
for n in sshd cockpit system-remote-login system-login system-auth password-auth postlogin \
	common-auth common-account common-password common-session common-session-nonlogin \
	common-session-noninteractive other; do
	for d in /etc/pam.d /usr/lib/pam.d /usr/etc/pam.d; do
		[ -f $d/$n ] && { echo "=== $d/$n $(readlink $d/$n)"; grep -v '^[[:space:]]*#' $d/$n | grep -v '^[[:space:]]*$'; }
	done
done
echo "=== selinux: $(getenforce 2>/dev/null) $(rpm -q selinux-policy-targeted selinux-policy-targeted-gaming 2>/dev/null | tr '\n' ' ')"
ls -Z /usr/sbin/sshd 2>/dev/null; ps -eZ 2>/dev/null | grep -m2 -E 'sshd'
id -Z 2>/dev/null
echo "=== firewall: firewalld=$(systemctl is-active firewalld 2>/dev/null) ufw=$(systemctl is-active ufw 2>/dev/null)"
firewall-cmd --get-default-zone 2>/dev/null && firewall-cmd --list-all 2>/dev/null | grep -E 'services|ports'
echo "zones in /etc: $(ls /etc/firewalld/zones/ 2>/dev/null | tr '\n' ' ')"
ufw status 2>/dev/null | head -3; ls /etc/ufw/applications.d 2>/dev/null | tr '\n' ' '; echo
echo "=== faillock.conf:"; grep -E '^[[:space:]]*[a-z]' /etc/security/faillock.conf 2>/dev/null
echo "=== sshd_config:"; grep -rihE '^[[:space:]]*(PermitRootLogin|UsePAM|KbdInteractiveAuthentication|PasswordAuthentication)' /etc/ssh/sshd_config /etc/ssh/sshd_config.d/ /usr/etc/ssh/sshd_config /usr/etc/ssh/sshd_config.d/ /usr/lib/ssh/ 2>/dev/null
echo "=== authselect: $(authselect current 2>/dev/null | tr '\n' ' ')"
DENTRO
$V ferma "$m" >/dev/null 2>&1; $V torna "$m" "$foto" >/dev/null 2>&1
echo "$m ($foto): $(wc -l <"$O/$m.txt") lines"
