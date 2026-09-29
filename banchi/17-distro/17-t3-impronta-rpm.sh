#!/bin/bash
#
# 17-t3-impronta-rpm.sh — fase 17, T3, linea C: l'impronta di una macchina della
# famiglia .rpm (Fedora, Alma, Tumbleweed, Leap), per confrontare prima
# dell'installazione e dopo la disinstallazione (R5, R6, R33).
#
#   (DENTRO la VM, da root)   bash 17-t3-impronta-rpm.sh > impronta.txt
#
# Lo stesso formato di `17-t3-impronta.sh` (linea Arch), una riga per fatto:
#   F <percorso> <modo> <utente> <gruppo> <sha256|dimensione>   file
#   L <percorso> -> <destinazione>                              collegamenti
#   D <percorso> <modo> <utente> <gruppo>                       cartelle
#   G <gruppo>:<gid>:<membri>      U <utente>:<uid>:<shell>
#   S <unita'> <stato>             P <pacchetto> <versione> <user|dependency|…>
#   Z <percorso> <contesto SELinux>   solo per i nostri percorsi
#   W <firewalld: servizi e porte della zona predefinita, permanenti>
#   H <percorso>                   sotto /home (solo i nomi)
# Fuori: i database dei gestori di pacchetti (li dice gia' P) e le cartelle
# che cambiano da sole.
set -u
export LC_ALL=C
{
	find /etc /usr /var/lib /opt -xdev \
		\( -path /var/lib/rpm -o -path /usr/lib/sysimage/rpm -o -path /var/lib/dnf -o -path /usr/lib/sysimage/libdnf5 \
		   -o -path /var/lib/zypp -o -path /var/lib/PackageKit -o -path /var/lib/systemd/coredump \
		   -o -path /var/lib/systemd/timers -o -path /var/lib/systemd/random-seed -o -path /var/lib/systemd/catalog \
		   -o -path /var/lib/NetworkManager -o -path /var/lib/sss -o -path /var/lib/gdm -o -path /var/lib/sddm \
		   -o -path /var/lib/upower -o -path /var/lib/systemd/backlight -o -path /etc/ld.so.cache \
		   -o -path /var/lib/systemd/ephemeral-trees -o -path /var/lib/cloud -o -path /var/lib/private \
		   -o -path /var/lib/colord -o -path /var/lib/geoclue -o -path /var/lib/AccountsService \
		   -o -path /var/lib/fwupd -o -path /var/lib/flatpak -o -path /var/lib/chrony -o -path /var/lib/rsyslog \
		   -o -path /var/lib/lastlog -o -path /var/lib/wtmpdb -o -path /var/lib/systemd/pstore \
		   -o -path /var/lib/selinux/targeted/active -o -path /usr/share/mime -o -path /usr/share/icons \
		   -o -path /usr/lib/modules -o -path /var/lib/logrotate -o -path /var/lib/plymouth \
		   -o -path /var/lib/systemd/linger -o -path /var/lib/authselect -o -path /var/lib/boltd \
		   -o -path /var/lib/pipewire -o -path /var/lib/polkit-1 -o -path /var/lib/rpm-state \
		\) -prune -o \
		\( -type d -printf 'D %p %m %u %g\n' \) -o \
		\( -type l -printf 'L %p -> %l\n' \) -o \
		\( -type f \( -path '/etc/*' -o -path '/usr/lib/systemd/*' -o -path '/usr/share/polkit-1/*' \
		   -o -path '/usr/lib/tmpfiles.d/*' -o -path '/usr/share/applications/*' -o -path '/var/lib/remotix/*' \
		   -o -path '/usr/lib/pam.d/*' -o -path '/usr/lib/firewalld/*' \) \
		   -exec sh -c 'for f; do printf "F %s %s\n" "$(stat -c "%n %a %U %G" "$f")" "$(sha256sum <"$f" | cut -c1-16)"; done' _ {} + \) -o \
		\( -type f -printf 'F %p %m %u %g %s\n' \)
	getent group | awk -F: '{ print "G " $1 ":" $3 ":" $4 }'
	getent passwd | awk -F: '{ print "U " $1 ":" $3 ":" $7 }'
	systemctl list-unit-files --type=service,socket,timer,path --no-legend --no-pager \
		| awk '{ print "S " $1 " " $2 }'
	if command -v dnf >/dev/null; then
		dnf -q repoquery --installed --qf '%{name} %{version}-%{release} %{reason}\n' 2>/dev/null \
			| awk '{ print "P " $0 }'
	else
		rpm -qa --qf '%{NAME} %{VERSION}-%{RELEASE}\n' | while read -r n v; do
			grep -qx "$n" /var/lib/zypp/AutoInstalled 2>/dev/null && r=dependency || r=user
			echo "P $n $v $r"
		done
	fi
	for p in /usr/libexec/remotix /usr/share/remotix /etc/remotix /var/lib/remotix /etc/pam.d/remotix \
	         /usr/lib/pam.d/remotix /usr/lib/systemd/system/remotix.service; do
		[ -e "$p" ] && command -v ls >/dev/null && ls -dZ "$p" 2>/dev/null | awk '{ print "Z " $2 " " $1 }'
	done
	if command -v firewall-cmd >/dev/null && systemctl -q is-active firewalld; then
		firewall-cmd --permanent --list-services | tr ' ' '\n' | awk 'NF { print "W servizio " $1 }'
		firewall-cmd --permanent --list-ports | tr ' ' '\n' | awk 'NF { print "W porta " $1 }'
	fi
	find /home -xdev -printf 'H %p\n' 2>/dev/null
} | sort
