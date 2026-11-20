#!/bin/sh
#
# box-identity.sh — the IDENTITY CHECK of a bench box (BOX-01, STO-01, STO-04).
#
#   box-identity.sh <os-id> <version-prefix|-> <desktop> [sss|-]
#
# Run INSIDE the box (or in a throw-away container of its image), as root, and ONLY reading files:
#   · at build time:   RUN sh /usr/local/sbin/t17-identity …     (a wrong image does not get built)
#   · at every `boot` and `reboot` of 17-box.sh: `podman exec -i <box> sh -s -- … < box-identity.sh`
#     (a wrong box does not start)
#   · on demand: `17-box.sh identity <m>`
#
# It answers four questions, all read from the system (nothing about the distribution is
# written here except what the caller passes):
#   1. the distribution: os-release ID (and VERSION_ID, if a prefix is given) is the expected one;
#   2. the desktop: a session file of the desktop AND its main program are installed;
#   3. the display manager: the one the machine REGISTERS (what the product reads, session.c
#      active_display_manager(): /etc/X11/default-display-manager, then the target of
#      /etc/systemd/system/display-manager.service) is the one of that desktop, and the two
#      sources do not contradict each other;
#   4. the default session: if the active lightdm / sddm DECLARES one (`user-session`,
#      `[Autologin] Session`), it belongs to the desktop. No declaration is fine (Debian).
# With `sss`: sssd is in nsswitch.conf (passwd, group), enabled, and active if systemd is running.
# Besides: the tools the bench itself uses (STO-04). A missing tool is NOT a mismatch of the
# machine: it is NOT-VERIFIABLE (exit 3), because the product would be judged by the box.
#
# ⚠ Ubuntu flavours that are not GNOME (kde, xfce, lxqt) must NOT have gnome-shell, gdm3 or the `ubuntu`
#   session, as an installation from the flavour's ISO (decision of 16 Nov 2026; the recipe pins them
#   at -1): their presence is a MISMATCH. Sessions of other desktops elsewhere are only listed.
# ⚠ Default session with no declaration: the fallbacks are read (Debian/Ubuntu x-session-manager
#   alternative, openSUSE displaymanager). With no declaration, no fallback and sessions of another desktop
#   installed, the default is UNDECIDABLE: NOT-VERIFIABLE, never green.
#
# Exit: 0 identity ok · 1 mismatch · 3 NOT-VERIFIABLE (a bench tool is missing, or the default session is undecidable).
# The last line is IDENTITY OK, IDENTITY MISMATCH or IDENTITY NOT-VERIFIABLE.
OSID=${1:?os id}; VER=${2:--}; DE=${3:?desktop}; SSS=${4:--}
bad=0; missing=""; undecided=0

say()  { printf 'identity: %s\n' "$*"; }
good() { say "ok  $*"; }
fail() { say "NO  $*"; bad=1; }

osr() {  # osr <key>: a value of os-release
	( . /etc/os-release 2>/dev/null || . /usr/lib/os-release 2>/dev/null; eval "printf '%s' \"\${$1:-}\"" )
}

# the desktop a session name belongs to (the same order as session.c desktop_of_session_name():
# xubuntu, lubuntu and kubuntu contain «ubuntu», so they are asked first)
desktop_of() {
	n=$(printf '%s' "$1" | tr 'A-Z' 'a-z')
	case $n in
	*xfce*|*xubuntu*) echo xfce ;;
	*lxqt*|*lubuntu*) echo lxqt ;;
	*plasma*|*kde*|*kubuntu*) echo kde ;;
	*gnome*|*ubuntu*) echo gnome ;;
	*) echo none ;;
	esac
}

# last value of <key> in the files, in reading order, optional section (sed range) in $3
conf_value() {  # conf_value <key> <section|-> files…
	k=$1; sec=$2; shift 2
	for f in "$@"; do
		[ -f "$f" ] || continue
		if [ "$sec" = - ]; then
			sed -n "s/^[[:space:]]*$k[[:space:]]*=[[:space:]]*//p" "$f"
		else
			sed -n "/^\[$sec\]/,/^\[/{s/^[[:space:]]*$k[[:space:]]*=[[:space:]]*//p}" "$f"
		fi
	done | tail -n 1
}

# 1. distribution ---------------------------------------------------------------------------
id=$(osr ID); vid=$(osr VERSION_ID)
if [ "$id" = "$OSID" ]; then good "distribution: ID=$id"; else fail "distribution: ID=\"$id\", expected \"$OSID\""; fi
if [ "$VER" != - ]; then
	case $vid in
	"$VER"|"$VER".*) good "version: VERSION_ID=$vid (expected $VER)" ;;
	*) fail "version: VERSION_ID=\"$vid\", expected \"$VER\"" ;;
	esac
fi

# 2. desktop installed ----------------------------------------------------------------------
case $DE in
gnome) PATS="gnome ubuntu";    PROGS="gnome-shell" ;;
kde)   PATS="plasma";          PROGS="plasmashell" ;;
xfce)  PATS="xfce";            PROGS="xfce4-session" ;;
lxqt)  PATS="lxqt";            PROGS="startlxqt lxqt-session" ;;
*) fail "desktop: \"$DE\" is not gnome|kde|xfce|lxqt"; PATS=""; PROGS="" ;;
esac
own=""; foreign=""
for d in /usr/share/wayland-sessions /usr/share/xsessions /usr/local/share/wayland-sessions /usr/local/share/xsessions; do
	[ -d "$d" ] || continue
	for f in "$d"/*.desktop; do
		[ -e "$f" ] || continue
		s=$(basename "$f" .desktop); w=$(desktop_of "$s")
		if [ "$w" = "$DE" ]; then own="$own $s"
		elif [ "$w" != none ]; then foreign="$foreign $s"; fi
	done
done
if [ -n "$own" ]; then good "desktop: session files of $DE:$own"; else fail "desktop: no session file of $DE (looked for $PATS) in */wayland-sessions, */xsessions"; fi
found=""
for p in $PROGS; do command -v "$p" >/dev/null 2>&1 && found="$found $p"; done
if [ -n "$found" ]; then good "desktop: program of $DE:$found"; else fail "desktop: none of the programs of $DE is installed ($PROGS)"; fi
[ -z "$foreign" ] || say "info sessions of other desktops installed (not a mismatch):$foreign"

# 3. display manager --------------------------------------------------------------------------
norm() { case $1 in gdm3) echo gdm ;; *) echo "$1" ;; esac; }
dm_a=""; dm_b=""
[ -s /etc/X11/default-display-manager ] && dm_a=$(norm "$(basename "$(head -n 1 /etc/X11/default-display-manager)")")
if [ -L /etc/systemd/system/display-manager.service ]; then
	dm_b=$(basename "$(readlink /etc/systemd/system/display-manager.service)" .service); dm_b=$(norm "$dm_b")
fi
# openSUSE: display-manager.service -> display-manager-legacy.service, which starts the manager named by
# DISPLAYMANAGER in /etc/sysconfig/displaymanager (or the default-displaymanager alternative). The link
# alone does not say WHICH one: the effective manager is read from that mechanism, and it must exist as a unit.
if [ "$dm_b" = display-manager-legacy ]; then
	sd=$(sed -n 's/^DISPLAYMANAGER=//p' /etc/sysconfig/displaymanager 2>/dev/null | tail -n 1 | tr -d "\" '")
	al=""; [ -e /etc/alternatives/default-displaymanager ] && al=$(basename "$(readlink -f /etc/alternatives/default-displaymanager)")
	eff=$(norm "$(printf '%s' "${sd:-$al}" | tr 'A-Z' 'a-z')")
	unit_ok=""
	if [ -n "$eff" ]; then
		for u in "$eff" "${eff}3"; do
			# `systemctl cat` does not work in a container build: the unit file on disk counts too
			if systemctl cat "$u.service" >/dev/null 2>&1; then unit_ok=1; break; fi
			for d in /usr/lib/systemd/system /lib/systemd/system /etc/systemd/system; do
				[ -f "$d/$u.service" ] && { unit_ok=1; break 2; }
			done
		done
	fi
	if [ -n "$unit_ok" ]; then
		say "info display-manager.service is the legacy wrapper; DISPLAYMANAGER=\"$sd\" alternative=\"$al\" => $eff"
		dm_b=$eff
	else
		say "NO  display manager: legacy wrapper, but DISPLAYMANAGER=\"$sd\" / alternative=\"$al\" name no installed manager"
		dm_b=""
	fi
fi
dm=${dm_a:-$dm_b}
# kde: the KDE display manager that is installed, sddm or plasmalogin (Fedora 44, EPEL 10 on Alma: the group
# brings plasma-login-manager); the rest is one name. Nothing else is accepted for kde
case $DE in
gnome) WANT="gdm" ;;
kde)   WANT="sddm plasmalogin" ;;
xfce)  WANT="lightdm" ;;
lxqt)  WANT="sddm" ;;
*)     WANT="" ;;
esac
okdm=0; for w in $WANT; do [ "$dm" = "$w" ] && okdm=1; done
if [ "$okdm" = 1 ]; then good "display manager: active is \"$dm\" (default-display-manager=\"${dm_a:--}\", display-manager.service=\"${dm_b:--}\")"
else fail "display manager: active is \"${dm:-none}\" (default-display-manager=\"${dm_a:--}\", display-manager.service=\"${dm_b:--}\"), expected: $WANT"; fi
if [ -n "$dm_a" ] && [ -n "$dm_b" ] && [ "$dm_a" != "$dm_b" ]; then
	fail "display manager: the two registrations disagree (default-display-manager=$dm_a, display-manager.service=$dm_b)"
fi

# Ubuntu flavours without GNOME (decision of 16 Nov 2026)
if [ "$OSID" = ubuntu ] && [ "$DE" != gnome ]; then
	if command -v gnome-shell >/dev/null 2>&1; then fail "ubuntu $DE: gnome-shell is installed (it must not be, as from the flavour's ISO)"; else good "ubuntu $DE: no gnome-shell"; fi
	if dpkg -s gdm3 2>/dev/null | grep -q '^Status: install ok installed'; then fail "ubuntu $DE: gdm3 is installed"; else good "ubuntu $DE: no gdm3"; fi
	case " $foreign " in *" ubuntu "*|*" ubuntu-xorg "*|*" ubuntu-wayland "*) fail "ubuntu $DE: the session \"ubuntu\" is installed" ;; esac
fi
# openSUSE: the display manager through its own mechanism too
case $OSID in
opensuse*)
	sd=""
	[ -r /etc/sysconfig/displaymanager ] && sd=$(sed -n 's/^DISPLAYMANAGER=//p' /etc/sysconfig/displaymanager | tail -n 1 | tr -d "\" '")
	al=""; [ -e /etc/alternatives/default-displaymanager ] && al=$(basename "$(readlink -f /etc/alternatives/default-displaymanager)")
	for v in "$sd" "$al"; do
		[ -n "$v" ] || continue
		v=$(norm "$(echo "$v" | tr 'A-Z' 'a-z')")
		if [ "$v" = "$dm" ]; then good "openSUSE display manager mechanism says \"$v\""; else fail "openSUSE display manager mechanism says \"$v\" (sysconfig=\"$sd\", alternatives=\"$al\"), the registered one is \"$dm\""; fi
	done ;;
esac

# sddm and plasmalogin: the default session is `DefaultSession` of [General] (a name or a full path
# to a .desktop), the last value in the order the manager reads the files (alphabetical in each folder, folders
# in the order given, so /etc beats /usr/lib); only without it, `Session` of [Autologin] (what Kubuntu declares).
# The value is reduced to a name by the caller.
sddm_session() {
	v=$(conf_value DefaultSession General "$@")
	[ -n "$v" ] || v=$(conf_value Session Autologin "$@")
	printf '%s' "$v"
}

# 4. default session --------------------------------------------------------------------------
decl=""
case $dm in
lightdm) decl=$(conf_value user-session - /usr/share/lightdm/lightdm.conf.d/*.conf /usr/lib/lightdm/lightdm.conf.d/*.conf /etc/xdg/lightdm/lightdm.conf.d/*.conf /etc/lightdm/lightdm.conf.d/*.conf /etc/lightdm/lightdm.conf) ;;
sddm)    decl=$(sddm_session /usr/lib/sddm/sddm.conf.d/*.conf /usr/etc/sddm.conf.d/*.conf /etc/sddm.conf.d/*.conf /etc/sddm.conf) ;;
plasmalogin) decl=$(sddm_session /usr/lib/plasmalogin/plasmalogin.conf.d/*.conf /etc/plasmalogin.conf.d/*.conf /etc/plasmalogin.conf) ;;
gdm)     decl=$(conf_value DefaultSession - /etc/gdm/custom.conf /etc/gdm3/custom.conf /etc/gdm3/daemon.conf) ;;
esac
decl=$(printf '%s' "$decl" | sed 's/[[:space:]]*$//; s|.*/||; s/\.desktop$//')
dsrc="declared by $dm"
if [ -z "$decl" ] && [ -e /etc/alternatives/x-session-manager ]; then
	decl=$(basename "$(readlink -f /etc/alternatives/x-session-manager)"); dsrc="x-session-manager alternative"
fi
if [ -z "$decl" ]; then
	if [ -z "$foreign" ]; then
		good "default session: none declared, and no session of another desktop is installed: it can only be $DE"
	else
		say "NO  default session: none declared (dm \"${dm:-none}\", no x-session-manager) and sessions of other desktops are installed:$foreign: undecidable"
		undecided=1
	fi
else
	w=$(desktop_of "$decl")
	if [ "$decl" = default ]; then
		# openSUSE: «default» is a .desktop kept by the alternatives (default-xsession.desktop,
		# default-waylandsession.desktop): follow the link to the real file and judge THAT (name, then Exec and
		# DesktopNames). Not resolved: undecidable, never ok.
		w=none; res=""
		for f in /etc/alternatives/default-waylandsession.desktop /etc/alternatives/default-xsession.desktop \
			/usr/share/wayland-sessions/default.desktop /usr/share/xsessions/default.desktop; do
			[ -e "$f" ] || continue
			r=$(readlink -f "$f"); b=$(basename "$r" .desktop)
			x=$(desktop_of "$b")
			[ "$x" != none ] || x=$(desktop_of "$(sed -n 's/^\(Exec\|DesktopNames\)=//p' "$r" | tr '\n' ' ')")
			res="$res $f->$b($x)"
			[ "$x" = none ] || { w=$x; break; }
		done
		if [ "$w" = none ]; then
			say "NO  default session: \"default\" ($dsrc) does not resolve to a desktop's session (looked at:${res:- nothing}): undecidable"
			undecided=1; w=skip
		else
			dsrc="$dsrc, «default» resolved:$res"
		fi
	fi
	if [ "$w" = skip ]; then :
	elif [ "$w" = "$DE" ]; then good "default session: \"$decl\" ($dsrc) belongs to $DE"
	else fail "default session: \"$decl\" ($dsrc) belongs to \"$w\", not to $DE"; fi
fi

# sss variant ---------------------------------------------------------------------------------
if [ "$SSS" = sss ]; then
	for db in passwd group; do
		if grep -Eq "^$db:.*[[:space:]]sss([[:space:]]|\$)" /etc/nsswitch.conf; then good "sss: $db in nsswitch.conf has sss"
		else fail "sss: $db line of nsswitch.conf has no sss ($(grep "^$db:" /etc/nsswitch.conf))"; fi
	done
	if [ -d /run/systemd/system ]; then
		st=$(systemctl is-active sssd.service 2>&1 | head -n 1)
		if [ "$st" = active ]; then good "sss: sssd.service active"; else fail "sss: sssd.service is \"$st\""; fi
		# `getent passwd root` proves nothing (root is in /etc/passwd): the user below exists ONLY in sssd
		if getent -s sss passwd t17sssonly >/dev/null 2>&1 && ! grep -q '^t17sssonly:' /etc/passwd; then good "sss: user t17sssonly (only in sssd) is answered by sss"
		else fail "sss: user t17sssonly (only in sssd) is not answered by sss"; fi
	else
		en=$(systemctl is-enabled sssd.service 2>&1 | head -n 1)
		if [ "$en" = enabled ]; then good "sss: sssd.service enabled (not booted: not asked if active)"; else fail "sss: sssd.service is \"$en\""; fi
	fi
fi

# the tools of the bench (STO-04) ----------------------------------------------------------------
TOOLS="python3 gawk openssl ssh scp sudo curl busctl loginctl wl-copy wl-paste gdbus"
[ "$DE" = lxqt ] && TOOLS="$TOOLS pcmanfm-qt"
for t in $TOOLS; do command -v "$t" >/dev/null 2>&1 || missing="$missing $t"; done
# python GObject + the GTK4 typelib: the known test window (F-030 & co) needs them (`[M]` 17 Nov 2026: three desktops BLOCKED without)
if python3 -c 'import gi; gi.require_version("Gtk", "4.0"); from gi.repository import Gtk' >/dev/null 2>&1; then TOOLS="$TOOLS python3-gi+gtk4"
else missing="$missing python3-gi+GTK4-typelib"; fi
if [ -z "$missing" ]; then good "tools of the bench: all there ($TOOLS)"; else say "NO  tools of the bench missing:$missing"; fi

if [ "$bad" = 1 ]; then echo "IDENTITY MISMATCH ($OSID $VER $DE)"; exit 1; fi
if [ -n "$missing" ] || [ "$undecided" = 1 ]; then echo "IDENTITY NOT-VERIFIABLE (missing:${missing:- none}; default session undecided: $undecided)"; exit 3; fi
echo "IDENTITY OK"
exit 0
