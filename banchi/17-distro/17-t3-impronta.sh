#!/bin/bash
# 17-t3-impronta.sh — l'impronta di una VM «cliente» per R5 e R6 (fasi/17 §7.3, §8).
#
#   (dentro la VM, da root)  bash 17-t3-impronta.sh > impronta.txt
#   di solito:  bash 17-vm.sh ssh <m> 'sudo bash -s' < 17-t3-impronta.sh > <nome>.txt
#
# Una riga per fatto, ordinate, con la SEZIONE in testa: cosi' `diff` fra due
# impronte dice che cosa e' cambiato e dove.  Sezioni:
#   F  i file di /etc (sha256), /usr (dimensione e data: il contenuto lo fissa il
#      pacchetto), /var/lib/remotix, /run/remotix, /var/lib/systemd/deb-systemd-*
#   G  i gruppi e i loro membri · P  i conti · U  le unita' e il loro stato
#   K  i pacchetti (versione, stato) · M  quelli installati a mano (apt-mark)
#   C  la configurazione IN VIGORE di logind e sleep (non solo i file)
#   W  firewall (nft)
# ⚠ Fuori per scelta: /var/log, le cache di apt, /var/lib/dpkg (se ne guarda
#   l'effetto nelle sezioni K e M), /etc/ld.so.cache (la rifa ldconfig).
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
if command -v nft >/dev/null; then nft list ruleset 2>/dev/null | sed 's/^/W /'; fi
true
