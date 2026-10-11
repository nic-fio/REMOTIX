#!/bin/bash
# ===========================================================================
# 11-c25 — ⭐⭐ «NO POWER OFF, RESTART, SUSPEND IN THE MENU; LOG OUT STAYS»
#   (DECISIONS.md §10.49, 11 Oct 2026)
#
#   bash 11-c25-no-power-entries.sh [TREE]     TREE = the REMOTIX tree (default: this one)
#   exit 0 green · 1 red · 3 «I could not look»
#
# what must be true   : in a GNOME Shell where the machine ALLOWS powering off
#                       and suspending (logind «yes», gnome-session CanShutdown
#                       true — as on the director's tablet), the REMOTIX session
#                       has canPowerOff, canRestart, canSuspend FALSE and
#                       canLogout TRUE
# where it starts from: a real gnome-shell (--headless), as the user, on two
#                       PRIVATE buses: the system one holds `11-fake-logind.py`
#                       (login1 says «yes» and refuses the acts), the session one
#                       its gnome-session (CanShutdown true).  The dconf is a
#                       throw-away one; the settings are the session's: what the
#                       product writes (`gnome_power_entries()`, src/session.c):
#                       always-show-log-out, and the extension of the TREE added
#                       to `enabled-extensions`
# what it looks at    : the Shell's own SystemActions (the object the menu reads),
#                       through a probe extension that exists only here
# how I know it gives red: on 5b4165d (rc-0.19.0, without the extension) it
#                       says RED: power-off, restart and suspend are available
#
# ⛔⛔ WHY THIS CHECK EXISTS: the boxes answered «no»/«na» (polkit belts of §4.7
#     inside, and a container is not a seat), so every desktop hid the entries by
#     itself and the net was green with the defect inside.  The fake logind is what
#     makes the box answer like the real machine.
# ⚠ GNOME only.  KDE, XFCE, LXQt: see §10.49 — what is not covered is declared there.
# ⛔ Needs no root, touches nothing outside its own temporary folder.
# ===========================================================================
HERE=$(cd "$(dirname "$0")" && pwd)
TREE=${1:-$(cd "$HERE/../.." && pwd)}
EXT=remotix-session@remotix

command -v gnome-shell >/dev/null || { echo "3 — gnome-shell is not here: I could not look"; exit 3; }
T=$(mktemp -d /tmp/c25.XXXXXX) || exit 3
PIDS=()
finish() { for p in "${PIDS[@]}"; do kill "$p" 2>/dev/null; done; wait 2>/dev/null; rm -rf -- "$T"; }
trap finish EXIT

mkdir -p "$T/run" "$T/config" "$T/data/gnome-shell/extensions/remotix-probe@bench" && chmod 700 "$T/run"
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
ENABLED="'remotix-probe@bench'"
if [ -f "$TREE/src/gnome-extension/$EXT/metadata.json" ]; then
	cp -r "$TREE/src/gnome-extension/$EXT" "$T/data/gnome-shell/extensions/"
	ENABLED="$ENABLED, '$EXT'"
	echo "· the tree has $EXT: enabled as the product does"
else
	echo "· the tree has NO $EXT"
fi

dbus-daemon --config-file=/usr/share/dbus-1/session.conf --address="unix:path=$T/system" \
	--nofork --nopidfile >/dev/null 2>&1 & PIDS+=($!)

# ⛔⛔ The environment is set BEFORE the bus is born: the services it activates
#     (dconf-service above all) take ITS environment, not the script's.  `[M]` 11 Oct
#     2026, first version: the exports were inside, and dconf-service wrote the
#     bench's keys into the REAL ~/.config/dconf/user of whoever ran it.
export T ENABLED HERE HOME=$T/home XDG_RUNTIME_DIR=$T/run XDG_CONFIG_HOME=$T/config \
	XDG_DATA_HOME=$T/data XDG_CACHE_HOME=$T/cache XDG_STATE_HOME=$T/state \
	DBUS_SYSTEM_BUS_ADDRESS=unix:path=$T/system GSETTINGS_BACKEND=dconf
unset WAYLAND_DISPLAY DISPLAY DCONF_PROFILE
mkdir -p "$HOME"
dbus-run-session -- bash -c '
	for i in $(seq 50); do [ -S "$T/system" ] && break; sleep 0.1; done
	python3 "$HERE/11-fake-logind.py" --system-bus "$DBUS_SYSTEM_BUS_ADDRESS" \
		--session-bus "$DBUS_SESSION_BUS_ADDRESS" > "$T/fake.log" 2>&1 &
	fake=$!
	for i in $(seq 50); do grep -q ready "$T/fake.log" && break; sleep 0.1; done
	grep -q ready "$T/fake.log" || { echo "3 — the fake logind did not start"; cat "$T/fake.log"; exit 3; }
	gsettings set org.gnome.shell always-show-log-out true
	gsettings set org.gnome.shell enabled-extensions "[$ENABLED]"
	gnome-shell --headless --wayland --no-x11 --virtual-monitor 1280x720 > "$T/shell.log" 2>&1 &
	shell=$!
	r=""
	for i in $(seq 60); do
		sleep 1
		r=$(gdbus call --session -d org.gnome.Shell -o /org/gnome/Shell -m org.gnome.Shell.Eval \
			"[c25.canPowerOff, c25.canRestart, c25.canSuspend, c25.canLogout]" 2>/dev/null)
		case "$r" in *"true, '\''["*) [ "$i" -ge 8 ] && break ;; esac
	done
	kill $shell $fake 2>/dev/null; wait $shell $fake 2>/dev/null
	echo "· the Shell says [power-off, restart, suspend, log-out] = ${r:-nothing}"
	grep -c "fake: org.freedesktop.login1.Manager.CanSuspend" "$T/fake.log" | sed "s/^/· login1 CanSuspend asked: /"
	grep -c "fake: org.gnome.SessionManager.CanShutdown" "$T/fake.log" | sed "s/^/· gnome-session CanShutdown asked: /"
	grep -a "REMOTIX" "$T/shell.log" | sed "s/^/· shell: /"
	case "$r" in
	*"[false,false,false,true]"*) echo "GREEN — no Power Off, Restart, Suspend; «Log Out…» there"; exit 0 ;;
	*"true, '\''["*) echo "RED — an entry that must not be there IS there (or «Log Out…» is missing)"; exit 1 ;;
	*) echo "3 — the Shell did not answer: I could not look"; grep -aiE "xtension|unsafe|JS ERROR" "$T/shell.log" | tail -20; exit 3 ;;
	esac
'
