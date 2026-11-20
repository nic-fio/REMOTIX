#!/bin/sh
#
# set-dm.sh <package> — Debian/Ubuntu family: registers the display manager the way its postinst does on
# a real machine, which in a container build does NOT happen (16 Nov 2026, phase B: after task-gnome-desktop
# neither /etc/X11/default-display-manager nor display-manager.service existed):
#   · /etc/X11/default-display-manager holds the path of the manager;
#   · the manager's unit is enabled (its [Install] Alias creates /etc/systemd/system/display-manager.service).
# It FAILS if the registration is not there at the end: nothing here weakens box-identity.sh, which reads the
# same two places and runs after this.
set -eu
DM=${1:?display manager package}
BIN=/usr/sbin/$DM
[ -x "$BIN" ] || BIN=$(command -v "$DM") || { echo "set-dm: $DM is not installed" >&2; exit 1; }
mkdir -p /etc/X11
printf '%s\n' "$BIN" > /etc/X11/default-display-manager
unit=""
for u in "$DM" gdm gdm3; do
	[ "$u" = "$DM" ] || [ "$DM" = gdm3 ] || continue
	# `systemctl cat` can fail in a container build (no running systemd): look for the unit file on disk too
	if systemctl cat "$u.service" >/dev/null 2>&1 \
		|| [ -f "/usr/lib/systemd/system/$u.service" ] || [ -f "/lib/systemd/system/$u.service" ]; then
		unit=$u; break
	fi
done
[ -n "$unit" ] || { echo "set-dm: no systemd unit for $DM" >&2; exit 1; }
systemctl enable "$unit.service" || true
if [ ! -e /etc/systemd/system/display-manager.service ]; then
	# the unit has no Alias (or enable did not follow it): the link a real postinst/`enable` leaves
	# in a container build systemd is not running: `show` may fail, so look for the unit file on disk too
	frag=$(systemctl show -p FragmentPath --value "$unit.service" 2>/dev/null) || frag=""
	if [ -z "$frag" ]; then
		for d in /usr/lib/systemd/system /lib/systemd/system; do
			[ -f "$d/$unit.service" ] && { frag=$d/$unit.service; break; }
		done
	fi
	[ -n "$frag" ] && ln -sf "$frag" /etc/systemd/system/display-manager.service
fi
[ -s /etc/X11/default-display-manager ] && [ -e /etc/systemd/system/display-manager.service ] \
	|| { echo "set-dm: $DM is not registered after all" >&2; exit 1; }
echo "set-dm: $DM registered ($BIN, unit $unit.service)"
