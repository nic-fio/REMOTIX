#!/bin/bash
#
# 17-t3-impronta-rpm.sh — phase 17, T3, line C: the fingerprint of a machine of the
# .rpm family (Fedora, Alma, Tumbleweed, Leap), to compare before
# installation and after uninstallation (R5, R6, R33).
#
#   (INSIDE the VM, as root)   bash 17-t3-impronta-rpm.sh > impronta.txt
#
# The same format as `17-t3-impronta.sh` (Arch line), one line per fact:
#   F <path> <mode> <user> <group> <sha256|size>                files
#   L <path> -> <target>                                        links
#   D <path> <mode> <user> <group>                              folders
#   G <group>:<gid>:<members>      U <user>:<uid>:<shell>
#   S <unit> <state>               P <package> <version> <user|dependency|…>
#   Z <path> <SELinux context>     only for our paths
#   W <firewalld: services and ports of the default zone, permanent>
#   H <path>                       under /home (names only)
# Left out: the package managers' databases (already covered by P) and the folders
# that change by themselves.
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
