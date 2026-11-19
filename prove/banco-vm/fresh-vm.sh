#!/bin/bash
# fresh-vm.sh <de> - the "fresh box" of prove/fresh.sh, for a VM that STAYS ON (no `ripristina`: it needs the VM off and drops its state).
# DEB=<path> installs that package too (apt --reinstall, as box.sh install does); without DEB the installed package is left as it is.
#
# What fresh.sh got from throwing the container away, and what is done here instead:
#   service and remote desktops   stopped (REMOTIX closes its desktops with the service), started again at the end            = equivalent
#   test users and their homes    the users the checks make (names of lib.sweep: bc lc mu rs ac cb bn dk dkf md in ph pl + digits)
#                                 are logged out and `userdel -r`: NEVER prova, prova2 or any other name                     = equivalent for them
#   the checks' own drop-ins      /etc/remotix/remotix.conf.d/90-resil-clocks.conf 91-ban-command.conf 99-dk-cap.conf removed = equivalent
#   the ban state                 /var/lib/remotix/net/ban, if not empty, is renamed ban.fresh-<time> (kept, not deleted)    = equivalent
#   the box's extra tools         what boxes/Containerfile added (python3-gi gir1.2-gtk-4.0 libglib2.0-bin openssl wl-clipboard
#                                 openssh-client, pipewire tools; pcmanfm-qt on lxqt) are installed with apt IF missing; on KDE the
#                                 Welcome Center autostart is hidden in /etc/skel (new users only), as the Containerfile did
#   The clean-up is CHECKED: a test user, a process of theirs or the service still there after it = FAIL (exit 1). apt is first
#   simulated (-s): if it would UPGRADE or remove a package that is already there, nothing is installed and it is a FAIL (the owner
#   decides); the packages really installed are listed in the output (fresh.out). is NOT installed (it would take over awk).
#   The bench key of the VM (vmkey.pub) is put in /root/.ssh/authorized_keys the first time (box.sh rootkey, through prova + sudo) and STAYS there.
#   NOT equivalent: the rest of the disk stays as it was (files in /tmp, /var, journal, accounts of the owner such as prova and
#   prova2, packages added by hand, snap state, anything an earlier run left outside the list above). A real reboot-to-clean
#   is `vm-radeon.sh spegni` + `ripristina`, which the owner decides.
#   NOT done on a VM (the container needed them): power.sh (a real /sys/power), set-dm.sh and box-identity.sh (a real installed system;
#   here only a light identity check: Ubuntu 26.04 and the display manager of that desktop), the key and GPU-group set-up of common.sh.
set -eo pipefail
DE=${1:-}; HERE=$(cd "$(dirname "$0")" && pwd); B=$HERE/box.sh
case $DE in gnome|kde|xfce|lxqt) ;; *) echo "usage: $0 gnome|kde|xfce|lxqt"; exit 2 ;; esac
DEB=${DEB:-}
[ -z "$DEB" ] || [ -f "$DEB" ] || { echo "FAIL no package: $DEB"; exit 1; }
RK=$($B rootkey "$DE" 2>&1) || { echo "FAIL the bench cannot get into the VM of $DE as root: $RK (is the VM on? vm-radeon.sh accendi <name>; prova + sudo must work)"; exit 1; }
case $RK in *installed*) echo "NOTE $RK (/root/.ssh/authorized_keys of the VM keeps the bench key)" ;; esac
$B ssh "$DE" true >/dev/null 2>&1 || { echo "FAIL the VM of $DE does not answer as root over ssh"; exit 1; }
if [ -n "$DEB" ]; then echo "package $DEB"; $B install "$DE" "$DEB" | tail -1; fi
$B ssh "$DE" "bash -s -- $DE" <<'REMOTE'
set -u
DE=$1
echo "identity: $(. /etc/os-release; echo "$ID $VERSION_ID"), display manager $(basename "$(cat /etc/X11/default-display-manager 2>/dev/null)")"
. /etc/os-release
case $DE in gnome) WANT=gdm3 ;; kde|lxqt) WANT=sddm ;; xfce) WANT=lightdm ;; esac
[ "$ID" = ubuntu ] && [ "${VERSION_ID#26.04}" != "$VERSION_ID" ] || { echo "FAIL this is not Ubuntu 26.04"; exit 1; }
[ "$(basename "$(cat /etc/X11/default-display-manager 2>/dev/null)")" = "$WANT" ] || { echo "FAIL the display manager of $DE should be $WANT"; exit 1; }
systemctl is-active display-manager >/dev/null 2>&1 || echo "NOTE the display manager is not active"
# 1. the service stops: REMOTIX closes its desktops with it
systemctl stop remotix >/dev/null 2>&1
case $(systemctl is-active remotix) in active|activating|deactivating) { echo "FAIL the service remotix did not stop"; exit 1; } ;; esac
# 2. test users: sessions ended, then removed (names as lib.sweep; never prova/prova2)
T=$(getent passwd | awk -F: '$3>=1000{print $1}' | grep -E '^(bc|lc|mu|rs|ac|cb|bn|dkf?|md|in|ph|pl)[0-9]+$' || true)
for u in $T; do pkill -u "$u" -f rx-window; loginctl terminate-user "$u" 2>/dev/null; done
for i in $(seq 30); do
	left=; for u in $T; do [ -n "$(pgrep -u "$u" | head -1)" ] && left="$left $u"; done
	[ -z "$left" ] && break; [ "$i" = 15 ] && pkill -KILL -u "$(echo $left | tr ' ' ,)"; sleep 1
done
n=0; for u in $T; do loginctl disable-linger "$u" 2>/dev/null; userdel -r "$u" >/dev/null 2>&1 && n=$((n+1)) || echo "NOTE could not remove user $u"; done
echo "test users removed: $n"
R=$(getent passwd | cut -d: -f1 | grep -E '^(bc|lc|mu|rs|ac|cb|bn|dkf?|md|in|ph|pl)[0-9]+$' || true)
[ -z "$R" ] || { echo "FAIL test users still there after the clean-up: $(echo $R)"; exit 1; }
for u in $T; do [ -z "$(pgrep -u "$u" 2>/dev/null | head -1)" ] || { echo "FAIL processes of $u still running"; exit 1; }; done
# 3. the checks' own drop-ins and the ban state
for f in 90-resil-clocks 91-ban-command 99-dk-cap; do rm -f "/etc/remotix/remotix.conf.d/$f.conf"; done
B=/var/lib/remotix/net/ban
if [ -s "$B" ]; then mv "$B" "$B.fresh-$(date +%y%m%d-%H%M%S)"; echo "ban state kept as $B.fresh-*"; fi
# 4. the tools the box image had
P="python3 python3-gi gir1.2-gtk-4.0 libglib2.0-bin openssl wl-clipboard openssh-client pipewire-bin procps"
[ "$DE" = lxqt ] && P="$P pcmanfm-qt"
M=; for p in $P; do dpkg-query -W -f='${Status}' "$p" 2>/dev/null | grep -q '^install ok installed' || M="$M $p"; done
if [ -n "$M" ]; then
	echo "missing tools:$M"
	apt-get update -qq </dev/null >/dev/null 2>&1 || echo "NOTE apt-get update failed (the simulation uses the old lists)"
	SIM=$(DEBIAN_FRONTEND=noninteractive apt-get install -s $M </dev/null 2>&1) || { echo "FAIL apt cannot simulate the installation of:$M"; echo "$SIM" | tail -5; exit 1; }
	UP=$(echo "$SIM" | grep -E '^(Inst|Remv) ' | grep -E '^Remv |^Inst [^ ]+ \[' || true)  # `Inst name [old] (new …)` is an upgrade of what is there; a new package has no [old] right after its name
	[ -z "$UP" ] || { echo "FAIL installing$M would upgrade or remove packages already there (owner decides, nothing installed):"; echo "$UP" | head -20; exit 1; }
	echo "to be installed: $(echo "$SIM" | grep '^Inst ' | awk '{print $2}' | tr '\n' ' ')"
	DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $M </dev/null >/dev/null 2>&1 || { echo "FAIL apt could not install:$M"; exit 1; }
	echo "installed: $(echo "$SIM" | grep '^Inst ' | awk '{print $2}' | tr '\n' ' ')"
fi
if [ "$DE" = kde ] && [ ! -e /etc/skel/.config/plasma-welcomerc ]; then
	mkdir -p /etc/skel/.config/autostart
	for f in $(grep -il welcome /etc/xdg/autostart/*.desktop 2>/dev/null); do
		printf '[Desktop Entry]\nType=Application\nName=Welcome\nHidden=true\n' > "/etc/skel/.config/autostart/$(basename "$f")"; done
	printf '[General]\nLastSeenVersion=99.0.0\n' > /etc/skel/.config/plasma-welcomerc
	echo "kde: Welcome Center hidden in /etc/skel by the test bench (stays for users made by hand too)"
fi
# 5. the service up again
systemctl reset-failed remotix >/dev/null 2>&1
systemctl enable remotix >/dev/null 2>&1; systemctl start remotix >/dev/null 2>&1; sleep 4
st=$(systemctl is-active remotix); echo "remotix: $st"
[ "$st" = active ]
REMOTE
