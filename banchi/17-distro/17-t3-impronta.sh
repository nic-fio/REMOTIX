#!/bin/bash
#
# 17-t3-impronta.sh — fase 17, T3: l'impronta di una macchina, per confrontare
# prima dell'installazione e dopo la disinstallazione (R5, R6, R33).
#
#   (DENTRO la VM, da root)   bash 17-t3-impronta.sh > impronta.txt
#
# Una riga per fatto, ordinata, confrontabile con `diff`:
#   F <percorso> <modo> <utente> <gruppo> <sha256|dimensione>   file di /etc, /usr, /var/lib, /opt
#   L <percorso> -> <destinazione>                              collegamenti
#   D <percorso> <modo> <utente> <gruppo>                       cartelle
#   G <gruppo>:<gid>:<membri>                                   /etc/group
#   U <utente>:<uid>:<shell>                                    /etc/passwd
#   S <unita'> <stato>                                          unita' di sistema
#   P <pacchetto> <versione> <esplicito|dipendenza>             pacchetti
#   H <percorso>                                                sotto /home (solo i nomi)
#
# ⚠ /etc e le cartelle di configurazione di systemd, polkit, PAM col contenuto
#   (sha256); il resto di /usr con la sola dimensione: e' la differenza di file,
#   non di byte, che conta per R6.  Fuori: le cartelle che cambiano da sole
#   (cache di pacman, journal, i database di pacman li dice gia' P).
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
