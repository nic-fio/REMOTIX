#!/bin/sh
#
# 11-box-power.sh — INSIDE a bench box (a container), as root: the box answers about sleep
# as a real machine does, so that it is the PRODUCT's polkit rule that is tested.
#
#   in the box:    sh /rete11/11-box-power.sh           (11-start.sh, 11-two-cards.sh)
#   from outside:  podman exec -i <box> sh < 11-box-power.sh        (17-distro/boxes/17-box.sh)
#
# `[M]` 14 Nov 2026, Ubuntu 26.04 (systemd 259): in a container /sys is read-only, and logind,
# asked CanSuspend / CanHibernate / CanHybridSleep, answers «Call failed: Read-only file
# system» — it checks that /sys/power/state can be written BEFORE asking polkit.  Until
# that day the Debian and openSUSE boxes answered «no» only because the BENCH had put
# /etc/systemd/sleep.conf.d/remotix-no-suspend.conf in force — a file the package carries
# switched off (DECISIONS §10.12, §10.36): F-029 was judging the bench's file, not the rule
# `50-remotix-no-poweroff.rules`, the one belt the package installs active.
#
# ⭐ THE CURE, the same on every distribution: a tmpfs COPY of /sys/power is mounted over
#    it and logind is restarted (it lives in its own mount namespace: it sees the new mount
#    only when it is born again).  logind then finds «state» writable, asks polkit, and the
#    answer is the rule's: «no» to the tenant, «yes» to root.
# ⛔ The real /sys/power is NOT touched and stays read-only underneath: whatever is written in
#    the box lands in the copy, and nobody can put the server to sleep from a box.
# ⚠ The mount lives as long as the container runs: after a restart of the box this script is
#   run again (17-box.sh does it at `boot` and `reboot`; 11-start.sh every time it puts the
#   product inside).
# ⚠ WHAT IT DOES EVERY TIME, also where «state» is already writable (a box already set up; a
#   real machine or a VM, where it is not meant to be run): it REMOVES the old file of the
#   bench /etc/systemd/sleep.conf.d/remotix-no-suspend.conf and RESTARTS systemd-logind (which
#   re-reads sleep.conf.d and sees the mount).  Only the MOUNT is skipped when «state» is
#   writable.  ⇒ Do not run it on a machine where the administrator switched that belt on.
# ⚠ Hibernate and hybrid sleep answer «na» in a box without swap, as on a real machine
#   without swap: there the rule is not reached.
# ⭐ EXIT STATUS (BOX-12): 0 only if logind answered CanSuspend with a value; 1 if the tmpfs cannot be mounted
#   or if the answer is an error. The old script said OK whatever happened.
# The old file of the bench is always removed (a box born before 14 Nov 2026 has it).
rm -f /etc/systemd/sleep.conf.d/remotix-no-suspend.conf
rmdir /etc/systemd/sleep.conf.d 2>/dev/null
[ -d /sys/power ] || { echo "box-power: no /sys/power here, nothing to do"; exit 0; }
if [ -w /sys/power/state ]; then
	echo "box-power: /sys/power/state is writable already"
else
	d=$(mktemp -d /run/box-power.XXXXXX) || exit 1
	for f in /sys/power/*; do
		[ -f "$f" ] && cat "$f" > "$d/${f##*/}" 2>/dev/null
	done
	mount -t tmpfs -o mode=755,size=256k tmpfs /sys/power || { echo "box-power: ⛔ cannot mount the copy over /sys/power"; rm -rf "$d"; exit 1; }
	cp "$d"/* /sys/power/ && chmod 644 /sys/power/*
	rm -rf "$d"
	echo "box-power: a tmpfs copy of /sys/power is mounted ($(ls /sys/power | wc -l) files)"
fi
systemctl restart systemd-logind >/dev/null 2>&1 || echo "box-power: ⛔ systemd-logind did not restart"
sleep 1
ans=$(busctl call org.freedesktop.login1 /org/freedesktop/login1 org.freedesktop.login1.Manager CanSuspend 2>&1 | tail -n 1)
printf 'box-power: logind, asked by root: CanSuspend=%s\n' "$ans"
# BOX-12 (Phase A, 16 Nov 2026): the LAST LINE above is the answer, and the exit status says whether there is one.
# Anything but a value of CanSuspend (`s "yes"`, `s "no"`, `s "challenge"`, `s "na"`) — «Read-only file system»,
# a bus error, nothing — is a FAILURE: the caller (17-box.sh `power`) refuses the box.
case $ans in
's "yes"'|'s "no"'|'s "challenge"'|'s "na"') exit 0 ;;
*) exit 1 ;;
esac
