#!/bin/bash
# 17-t3-impronta.sh — the fingerprint of a "customer" VM for R5 and R6 (fasi/17 §7.3, §8).
#
#   (inside the VM, as root)  bash 17-t3-impronta.sh > impronta.txt
#   usually:  bash 17-vm.sh ssh <m> 'sudo bash -s' < 17-t3-impronta.sh > <name>.txt
#
# One line per fact, sorted, with the SECTION first: so `diff` between two
# fingerprints says what changed and where.  Sections:
#   F  the files of /etc (sha256), /usr (size and date: the content is fixed by the
#      package), /var/lib/remotix, /run/remotix, /var/lib/systemd/deb-systemd-*
#   G  groups and their members · P  accounts · U  units and their state
#   K  packages (version, state) · M  those installed by hand (apt-mark)
#   C  the configuration IN FORCE for logind and sleep (not just the files)
#   S  listening ports (ss) · W  firewall (nft)
# ⚠ Left out by choice: /var/log, the apt caches, /var/lib/dpkg (its
#   effect is looked at in sections K and M), /etc/ld.so.cache (ldconfig rebuilds it).
set -u
export LC_ALL=C

find /etc -xdev \( -path /etc/ld.so.cache \) -prune -o -printf '%p\t%y\t%m\t%u\t%g\t%l\n' 2>/dev/null |
while IFS=$'\t' read -r p y m u g l; do
	if [ "$y" = f ]; then h=$(sha256sum "$p" 2>/dev/null | cut -c1-16); else h=$l; fi
	printf 'F %s %s %s %s:%s %s\n' "$p" "$y" "$m" "$u" "$g" "$h"
done
find /usr -xdev -printf 'F %p %y %m %u:%g %s %TY%Tm%Td%TH%TM%TS %l\n' 2>/dev/null | sed 's/\.[0-9]* / /'
for d in /var/lib/remotix /run/remotix /var/lib/systemd/deb-systemd-helper-enabled \
         /var/lib/systemd/deb-systemd-user-helper-enabled /var/lib/systemd/deb-systemd-helper-masked; do
	[ -e "$d" ] && find "$d" -printf 'F %p %y %m %u:%g %l\n'
done
getent group  | sort | sed 's/^/G /'
getent passwd | sort | sed 's/^/P /'
systemctl list-unit-files --no-legend --no-pager 2>/dev/null | awk '{print "U", $1, $2}' | sort
dpkg-query -W -f='K ${Package}:${Architecture} ${Version} ${db:Status-Abbrev}\n' | sort
apt-mark showmanual 2>/dev/null | sort | sed 's/^/M /'
systemd-analyze cat-config systemd/logind.conf 2>/dev/null | grep -vE '^(#|$)' | sed 's/^/C logind /'
systemd-analyze cat-config systemd/sleep.conf  2>/dev/null | grep -vE '^(#|$)' | sed 's/^/C sleep /'
ss -Htlnu 2>/dev/null | awk '{print "S", $1, $5}' | sort -u
if command -v nft >/dev/null; then nft list ruleset 2>/dev/null | sed 's/^/W /'; fi
true
