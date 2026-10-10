#!/bin/bash
#
# 17-t3-impronta-arch.sh — phase 17, T3: the fingerprint of a machine, to compare
# before installation and after uninstallation (R5, R6, R33).
#
#   (INSIDE the VM, as root)   bash 17-t3-impronta-arch.sh > impronta.txt
#
# One line per fact, sorted, comparable with `diff`:
#   F <path> <mode> <user> <group> <sha256|size>                files of /etc, /usr, /var/lib, /opt
#   L <path> -> <target>                                        links
#   D <path> <mode> <user> <group>                              folders
#   G <group>:<gid>:<members>                                   /etc/group
#   U <user>:<uid>:<shell>                                      /etc/passwd
#   S <unit> <state>                                            system units
#   P <package> <version> <esplicito|dipendenza>                packages
#   H <path>                                                    under /home (names only)
#
# ⚠ /etc and the configuration folders of systemd, polkit, PAM with content
#   (sha256); the rest of /usr with size only: it is the difference in files,
#   not bytes, that matters for R6.  Left out: folders that change by themselves
#   (pacman cache, journal; the pacman databases are already covered by P).
set -u
export LC_ALL=C
{
	find /etc /usr /var/lib /opt -xdev \
		\( -path /var/lib/pacman -o -path /var/lib/systemd/coredump -o -path /var/lib/systemd/timers \
		   -o -path /var/lib/systemd/random-seed -o -path /var/lib/systemd/catalog -o -path /var/lib/NetworkManager \
		   -o -path /var/lib/dhcpcd -o -path /var/lib/logrotate.status -o -path /var/lib/sddm \
		   -o -path /var/lib/lightdm -o -path /var/lib/upower -o -path /var/lib/systemd/backlight \
		   -o -path /etc/ld.so.cache -o -path /var/lib/systemd/ephemeral-trees -o -path /var/lib/cloud \
		   -o -path /var/lib/private -o -path /var/lib/colord -o -path /var/lib/geoclue -o -path /var/lib/AccountsService \
		   -o -path /etc/pacman.d/gnupg -o -path /usr/share/mime -o -path /usr/share/icons -o -path /usr/lib/modules \
		\) -prune -o \
		\( -type d -printf 'D %p %m %u %g\n' \) -o \
		\( -type l -printf 'L %p -> %l\n' \) -o \
		\( -type f \( -path '/etc/*' -o -path '/usr/lib/systemd/*' -o -path '/usr/share/polkit-1/*' \
		   -o -path '/usr/lib/tmpfiles.d/*' -o -path '/usr/share/applications/*' -o -path '/var/lib/remotix/*' \) \
		   -exec sh -c 'for f; do printf "F %s %s\n" "$(stat -c "%n %a %U %G" "$f")" "$(sha256sum <"$f" | cut -c1-16)"; done' _ {} + \) -o \
		\( -type f -printf 'F %p %m %u %g %s\n' \)
	getent group | awk -F: '{ print "G " $1 ":" $3 ":" $4 }'
	getent passwd | awk -F: '{ print "U " $1 ":" $3 ":" $7 }'
	systemctl list-unit-files --type=service,socket,timer,path --no-legend --no-pager \
		| awk '{ print "S " $1 " " $2 }'
	pacman -Qe | awk '{ print "P " $1 " " $2 " esplicito" }'
	pacman -Qd | awk '{ print "P " $1 " " $2 " dipendenza" }'
	find /home -xdev -printf 'H %p\n' 2>/dev/null
} | sort
