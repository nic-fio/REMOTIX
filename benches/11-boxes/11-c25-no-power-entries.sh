#!/bin/bash
# ===========================================================================
# 11-c25 — ⭐⭐ «NO POWER OFF, RESTART, SUSPEND IN THE MENU; LOG OUT STAYS»
#   (DECISIONS.md §10.49, 11 Oct 2026)
#
#   bash 11-c25-no-power-entries.sh [TREE] [all|gnome|kde|xfce|lxqt]
#   bash 11-c25-no-power-entries.sh --fetch DIR   the desktop libraries this
#        machine lacks, downloaded and unpacked in DIR (apt-get download +
#        dpkg-deb -x, as a user: nothing installed); then REMOTIX_C25_ROOT=DIR
#   exit 0 green · 1 red · 3 «I could not look» (for at least one desktop)
#
# what must be true   : where the machine ALLOWS powering off and suspending
#                       (logind «yes», as on the director's tablet), the desktop
#                       code that decides the entries, started the way the
#                       product starts the desktop, finds them NOT available —
#                       and an act typed in the session (`systemctl poweroff`)
#                       does not even reach logind
# where it starts from: a private system bus where `11-fake-logind.py` owns
#                       login1 and says «yes»; the probe is started through the
#                       TREE's `remotix --internal-bus-filter` (the product's start
#                       line, src/session.c `bus_filter_command()`) — a tree that
#                       does not have it starts the probe directly, as it
#                       started the desktop
# what it looks at    : per desktop, the object its menu reads:
#     gnome  a real gnome-shell --headless: SystemActions canPowerOff, canRestart,
#            canSuspend, canLogout (a bench-only probe extension); its
#            gnome-session is the fake's, computing CanShutdown as gnome-session
#            48 does, and through the same filter
#     kde    libkworkspace6's SessionManagement (the object of Kickoff, Kicker and
#            the log-out screen), through its QML module and the `qml` tool
#     xfce   libxfce4util's XfceSystemd — the very calls of xfce4-session's
#            log-out dialog (`xfsm-shutdown.c`, `xfsm-logout-dialog.c:263-288`)
#     lxqt   liblxqt's LXQt::Power — what lxqt-leave and the panel's Leave menu ask
# how I know it gives red: on 5b4165d (rc-0.19.0, no filter) every desktop says
#                       RED: the entries are available, and PowerOff reaches logind
#
# ⚠ XFCE's log-out dialog ALWAYS draws Restart and Shut Down (no key, no
#   `Show…` for them): with the filter they are GREY and refused, not gone.
#   The panel's action button and Suspend/Hibernate are removed by the session's
#   settings (src/session.c, ACTIONS_TO_REMOVE, ShowSuspend…).  ⇒ For XFCE green
#   means «grey and refused», and it is said in the line.
# ⚠ LXQt and XFCE: «Log Out» does not come from logind (lxqt-session,
#   xfce4-session): it is not judged here.
# ⛔ Needs no root, touches nothing outside its own temporary folder.
# ===========================================================================
HERE=$(cd "$(dirname "$0")" && pwd)

if [ "${1:-}" = "--fetch" ]; then
	D=${2:?a folder}; mkdir -p "$D/debs" && cd "$D/debs" || exit 3
	apt-get download qml-qt6 libxfce4util7 gir1.2-libxfce4util-1.0 libqt6xdg4 \
		libqt6xdgiconloader4 liblxqt2 || exit 3
	for d in *.deb; do dpkg-deb -x "$d" "$D"; done
	echo "· unpacked in $D: REMOTIX_C25_ROOT=$D bash $0"
	exit 0
fi

TREE=${1:-$(cd "$HERE/../.." && pwd)}
WHICH=${2:-all}
case "$WHICH" in all) WHICH="gnome kde xfce lxqt" ;; esac
T=$(mktemp -d /tmp/c25.XXXXXX) || exit 3
PIDS=()
finish() { for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done; wait 2>/dev/null; rm -rf -- "$T"; }
trap finish EXIT
mkdir -p "$T/run" "$T/config" "$T/home" "$T/data/gnome-shell/extensions/remotix-probe@bench" && chmod 700 "$T/run"

if grep -q BUSFILTER_ARG "$TREE/src/main.c" 2>/dev/null && [ -x "$TREE/src/remotix" ]; then
	echo "· the tree has the system bus filter: the probes start through it"
	THROUGH="$TREE/src/remotix --internal-bus-filter $T/run/system-bus --"
else
	echo "· the tree has NO system bus filter: the probes start directly, as its desktops did"
	THROUGH=""
fi

# the libraries this machine lacks, if unpacked with --fetch
R=${REMOTIX_C25_ROOT:-}
if [ -n "$R" ]; then
	export LD_LIBRARY_PATH="$R/usr/lib/x86_64-linux-gnu${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
	export GI_TYPELIB_PATH="$R/usr/lib/x86_64-linux-gnu/girepository-1.0"
	export PATH="$R/usr/lib/qt6/bin:$PATH"
fi
export PATH="/usr/lib/qt6/bin:$PATH"

# --- the probes -------------------------------------------------------------
cat > "$T/data/gnome-shell/extensions/remotix-probe@bench/metadata.json" <<'EOF'
{"uuid": "remotix-probe@bench", "name": "c25 probe", "description": "bench only",
 "shell-version": ["45", "46", "47", "48", "49", "50"]}
EOF
cat > "$T/data/gnome-shell/extensions/remotix-probe@bench/extension.js" <<'EOF'
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as SystemActions from 'resource:///org/gnome/shell/misc/systemActions.js';
export default class Probe extends Extension {
    enable() { global.context.unsafe_mode = true; globalThis.c25 = SystemActions.getDefault(); }
    disable() {}
}
EOF
cat > "$T/kde.qml" <<'EOF'
import QtQuick
import org.kde.plasma.private.sessions
Item {
    SessionManagement { id: sm }
    Timer { interval: 3000; running: true; onTriggered: {
        console.log("C25 " + JSON.stringify([sm.canShutdown, sm.canReboot, sm.canSuspend,
                                             sm.canHibernate, sm.canLogout])); Qt.quit() } }
}
EOF
cat > "$T/xfce.py" <<'EOF'
import gi
gi.require_version("Libxfce4util", "1.0")
from gi.repository import Libxfce4util as X
s = X.Systemd.get()
r = {}
for m in ("can_reboot", "can_power_off", "can_suspend", "can_hibernate"):
    ok, can, auth = getattr(s, m)()
    r[m] = (ok, can, auth)
# xfsm-logout-dialog.c: Restart/Shut Down sensitive = can && auth; Suspend/Hibernate drawn = can
print("C25 " + str([r["can_reboot"][1] and r["can_reboot"][2],
                    r["can_power_off"][1] and r["can_power_off"][2],
                    r["can_suspend"][1], r["can_hibernate"][1]]).lower().replace(" ", ""),
      "raw", r)
EOF
cat > "$T/lxqt.py" <<'EOF'
import ctypes
G = ctypes.RTLD_GLOBAL
core = ctypes.CDLL("libQt6Core.so.6", mode=G)
lx = ctypes.CDLL("liblxqt.so.2", mode=G)
argc = ctypes.c_int(1)
argv = (ctypes.c_char_p * 2)(b"c25", None)
app = ctypes.create_string_buffer(4096)
core._ZN16QCoreApplicationC1ERiPPci(app, ctypes.byref(argc), argv, 0x060800)
power = ctypes.create_string_buffer(4096)
lx._ZN4LXQt5PowerC1EbP7QObject(power, ctypes.c_bool(True), None)   # as lxqt-leave
ask = lambda sym: bool(getattr(lx, sym)(power) & 0xff)
r = [ask("_ZNK4LXQt5Power11canShutdownEv"), ask("_ZNK4LXQt5Power9canRebootEv"),
     ask("_ZNK4LXQt5Power10canSuspendEv"), ask("_ZNK4LXQt5Power12canHibernateEv")]
print("C25 " + str(r).lower().replace(" ", ""))
EOF

# --- the private system bus and the fake logind -----------------------------
dbus-daemon --config-file=/usr/share/dbus-1/session.conf --address="unix:path=$T/system" \
	--nofork --nopidfile >/dev/null 2>&1 & PIDS+=($!)
for i in $(seq 50); do [ -S "$T/system" ] && break; sleep 0.1; done
python3 "$HERE/11-fake-logind.py" --login1 "unix:path=$T/system" > "$T/fake.log" 2>&1 & PIDS+=($!)
for i in $(seq 50); do grep -q ready "$T/fake.log" && break; sleep 0.1; done
grep -q ready "$T/fake.log" || { echo "3 — the fake logind did not start"; cat "$T/fake.log"; exit 3; }

# ⛔⛔ The environment is set BEFORE the session bus is born: the services it activates
#     (dconf-service above all) take ITS environment, not the script's.  `[M]` 11 Oct
#     2026, first version: the exports were inside, and dconf-service wrote the
#     bench's keys into the REAL ~/.config/dconf/user of whoever ran it.
export T HERE THROUGH HOME=$T/home XDG_RUNTIME_DIR=$T/run XDG_CONFIG_HOME=$T/config \
	XDG_DATA_HOME=$T/data XDG_CACHE_HOME=$T/cache XDG_STATE_HOME=$T/state \
	DBUS_SYSTEM_BUS_ADDRESS=unix:path=$T/system GSETTINGS_BACKEND=dconf
unset WAYLAND_DISPLAY DISPLAY DCONF_PROFILE

OUT=0
verdict() {  # desktop, what was read, green pattern, note
	case "$2" in
	"$3") echo "  $1: GREEN — $4" ;;
	*"C25 ["*) echo "  $1: RED — an entry that must not be there IS there ($2)"; [ $OUT -lt 1 ] && OUT=1 ;;
	*) echo "  $1: 3 — I could not look (${2:-nothing read})"; OUT=3 ;;
	esac
}

for d in $WHICH; do
	case "$d" in
	gnome)
		command -v gnome-shell >/dev/null || { verdict gnome "gnome-shell missing" x; continue; }
		# ⭐ ONE filter for the whole scene, as one per session in the product:
		#    the fake gnome-session and the Shell are both behind it
		r=$(dbus-run-session -- $THROUGH bash -c '
			python3 "$HERE/11-fake-logind.py" --gnome-session "$DBUS_SESSION_BUS_ADDRESS" > "$T/fake-gs.log" 2>&1 &
			for i in $(seq 50); do grep -q ready "$T/fake-gs.log" && break; sleep 0.1; done
			gsettings set org.gnome.shell always-show-log-out true
			gsettings set org.gnome.shell enabled-extensions "[\"remotix-probe@bench\"]"
			gnome-shell --headless --wayland --no-x11 --virtual-monitor 1280x720 > "$T/shell.log" 2>&1 &
			r=""
			for i in $(seq 60); do
				sleep 1
				r=$(gdbus call --session -d org.gnome.Shell -o /org/gnome/Shell -m org.gnome.Shell.Eval \
					"[c25.canPowerOff, c25.canRestart, c25.canSuspend, c25.canLogout]" 2>/dev/null)
				case "$r" in *"true, '\''["*) [ "$i" -ge 8 ] && break ;; esac
			done
			pkill -P $$ 2>/dev/null
			echo "$r" | sed -n "s/.*'\''\(\[.*\]\)'\''.*/C25 \1/p"')
		grep -a "heard from login1" "$T/fake-gs.log" | tail -1 | sed "s/^/  gnome · /"
		verdict gnome "$r" "C25 [false,false,false,true]" "no Power Off, Restart, Suspend; «Log Out…» there" ;;
	kde)
		[ -d /usr/lib/x86_64-linux-gnu/qt6/qml/org/kde/plasma/private/sessions ] && command -v qml >/dev/null \
			|| { verdict kde "libkworkspace6 QML module or qml tool missing" x; continue; }
		r=$(QT_QPA_PLATFORM=offscreen dbus-run-session -- $THROUGH qml "$T/kde.qml" 2>&1 | grep -ao "C25 .*" | tail -1)
		verdict kde "$r" "C25 [false,false,false,false,true]" "no Shut Down, Restart, Suspend, Hibernate; «Log Out» there" ;;
	xfce)
		r=$(dbus-run-session -- $THROUGH python3 "$T/xfce.py" 2>&1 | grep -a "^C25" | tail -1)
		echo "  xfce · ${r#* raw }"
		verdict xfce "${r%% raw*}" "C25 [false,false,false,false]" "log-out dialog: Restart and Shut Down GREY (always drawn), no Suspend, Hibernate" ;;
	lxqt)
		r=$(dbus-run-session -- $THROUGH python3 "$T/lxqt.py" 2>&1 | grep -a "^C25" | tail -1)
		verdict lxqt "$r" "C25 [false,false,false,false]" "no Shutdown, Reboot, Suspend, Hibernate (Leave menu hides, lxqt-leave greys)" ;;
	esac
done

# --- the act: `systemctl poweroff` typed in the session -----------------------
before=$(grep -c "Manager.PowerOff" "$T/fake.log")
s=$(dbus-run-session -- $THROUGH bash -c 'systemctl poweroff 2>&1; echo "exit $?"' | tail -2 | tr '\n' ' ')
after=$(grep -c "Manager.PowerOff" "$T/fake.log")
if [ "$after" -gt "$before" ]; then
	echo "  act: RED — systemctl poweroff REACHED logind ($s)"; [ $OUT -lt 1 ] && OUT=1
elif echo "$s" | grep -q "exit [1-9]"; then
	echo "  act: GREEN — systemctl poweroff refused before logind ($s)"
else
	echo "  act: 3 — systemctl did not say ($s)"; OUT=3
fi
case $OUT in 0) echo "GREEN" ;; 1) echo "RED" ;; *) echo "3 — I could not look somewhere" ;; esac
exit $OUT
