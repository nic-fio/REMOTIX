# remotix.spec — the REMOTIX RPM for Fedora 45 (translation of ../ubuntu26.04/debian/).
#
# Built on the `costruzione` VM by build/build-rpm.sh (no containers).  Static ngtcp2 1.25.0 and nghttp3 1.18.0 live in
# /usr/local (build/quic-static.sh), not in the BuildRequires: same rule as the Debian package (D2 closed).
# OUR patched labwc of Ubuntu is NOT built nor shipped here (decision D2: KDE will use KWin alone).
#
# The PAM service file (src/remotix.pam) is Fedora's sshd stack; the SELinux module (selinux/remotix.*) gives the server's ROOT side its own
# domain (remotix_t: PAM, the birth of the desktops) so that pam_selinux can hand the user's context to the desktop (step 2), and the NETWORK
# side a narrow domain of its own (remotix_net_t, step 5: the «wall», the twin of Debian's AppArmor profile remotix_network).
# The hook of the LOCAL login (a local graphical login closes the user's remote desktop first; Debian: a pam-auth-update profile) is put
# in the PAM stacks of the login screens by /usr/libexec/remotix/remotix-pam-hook (src/remotix-pam-hook), which never touches what
# authselect generates: applied by %%post, re-applied by the triggers whenever the login screen's package is installed or updated and by
# ExecStartPre of the service, removed by %%preun.  Active: gdm, plasmalogin (KDE) and lightdm (XFCE) and sddm (LXQt).
# The video codecs are NOT dependencies (decision D1): the administrator installs them (RPM Fusion).

%global debug_package %{nil}
# rpm 6 turns /usr/lib/sysusers.d/*.conf into user()/group() Provides and creates the account BEFORE the package's own %%pre.  Here the
# %%pre must see whether an account named remotix was on the machine before the package (and keep it at removal), so that automation is
# switched off and %%post runs systemd-sysusers by itself, as Debian's postinst does.
%global __sysusers_path ^$
%global rxlibexec %{_libexecdir}/remotix

Name:           remotix
Version:        1.2.0
Release:        1%{?dist}
Summary:        Linux desktop in the browser, for several users
License:        LicenseRef-REMOTIX AND MIT
URL:            https://remotix.nicfio.it
Source0:        remotix-%{version}.tar.gz
Source1:        remotix.service
Source2:        remotix.sysusers
Source3:        remotix.tmpfiles
Source4:        remotix.conf
Source5:        denied-users
Source6:        remotix-no-suspend.conf
Source7:        needrestart.conf
Source8:        remotix.firewalld.xml
Source9:        org.kde.remotix.desktop

ExclusiveArch:  x86_64 aarch64

# Build: the libraries of the Debian Build-Depends, with Fedora names.  ngtcp2/nghttp3: static, in /usr/local (see above).
# OpenSSL: the system's openssl-devel (4.0); no fallback to openssl3.
BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconf-pkg-config
BuildRequires:  openssl-devel
BuildRequires:  pam-devel
BuildRequires:  libselinux-devel
BuildRequires:  glib2-devel >= 2.80
BuildRequires:  pipewire-devel
BuildRequires:  libdrm-devel
BuildRequires:  libva-devel
BuildRequires:  opus-devel
BuildRequires:  zlib-devel
BuildRequires:  libei-devel >= 1.3.901
BuildRequires:  libxkbcommon-devel
BuildRequires:  mesa-libgbm-devel
BuildRequires:  wayland-devel
BuildRequires:  vulkan-headers
BuildRequires:  vulkan-loader-devel
BuildRequires:  systemd-rpm-macros
BuildRequires:  systemd
BuildRequires:  bzip2
%{?selinux_requires}

# Run time: the libraries are found by rpm itself from the binary.  The others are what the binary uses and rpm does NOT see
# (same list as Debian's Depends): the PAM modules of the stack (pam_systemd, pam_listfile...), usermod/gpasswd/userdel,
# loginctl and systemctl --user, the systemd user bus, the PipeWire daemon + wireplumber (capture of GNOME/KDE and the audio of EVERY desktop).
Requires:       pam
Requires:       gawk
Requires:       systemd-pam
Requires:       shadow-utils
Requires:       systemd
Requires:       dbus-broker
Requires:       pipewire
Requires:       wireplumber
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
# gpasswd (%%preun), userdel/groupdel (%%postun); runuser (%%postun, the users' homes)
Requires(preun): shadow-utils
Requires(postun): shadow-utils
Requires(postun): util-linux-core

# Debian's Recommends (weak dependencies).  The VA / Vulkan video drivers are NOT here (D1: codecs are a requirement the
# administrator meets with RPM Fusion, not a dependency of the package).
#   labwc, wlr-randr, Xwayland: XFCE and LXQt (the compositor REMOTIX starts); dconf: the GNOME session's locks;
#   dejavu: labwc dies without a scalable font.  No desktop is pulled in: the package never installs one by itself.
Recommends:     labwc
Recommends:     dconf
Recommends:     wlr-randr
Recommends:     xorg-x11-server-Xwayland
Recommends:     dejavu-sans-fonts

# Fedora's equivalent of Debian's Static-Built-Using (SBOM): what is linked statically into /usr/libexec/remotix/remotix
Provides:       bundled(ngtcp2) = 1.25.0
Provides:       bundled(nghttp3) = 1.18.0

# the firewalld service definition: firewalld-filesystem owns the directories
BuildRequires:  firewalld-filesystem
Requires:       firewalld-filesystem

%description
REMOTIX shows a user's desktop (GNOME, KDE Plasma, Xfce, LXQt) in a browser, with video and audio over HTTP/3 and WebTransport.
Whoever connects logs in with the machine's user name and password (PAM, service "remotix"; root excluded by
/etc/remotix/denied-users) and finds their own session.

The remotix.service service listens on port 7447 (TCP for the page, UDP for QUIC).  The package installs the service
switched off: the administrator switches it on with `systemctl enable --now remotix`.  The package contains ngtcp2 and
nghttp3, statically linked.  Video is encoded only on the video card: the H.264 driver of the card (on Fedora: RPM Fusion,
mesa-va-drivers-freeworld) is a requirement of the administrator, not a dependency of this package.

%prep
%setup -q

%build
# nothing to configure: `make deps` checks the minimum versions
export LIBRARY_PATH=/usr/local/lib
export PKG_CONFIG_PATH=/usr/local/lib/pkgconfig
make -C src deps TWIN=none
# R24: the linked static libraries are the version declared in Provides: bundled()
test "$(pkg-config --modversion libngtcp2)" = 1.25.0
test "$(pkg-config --modversion libnghttp3)" = 1.18.0
# R13: the package's binary does NOT have the bench feature switched on.
grep -qx '#define BENCH_ON 0' src/rcp.c || { echo "src/rcp.c: BENCH_ON is not 0: not packaging (R13)"; exit 1; }
# The Makefile has `CFLAGS ?= -O2 -g -std=gnu11 <warnings>`: with the distribution's CFLAGS passed here that line no longer
# applies and -std=gnu11 would be lost (gcc 15 defaults to gnu23): so it is passed together with Fedora's flags.
make -C src all TWIN=none CFLAGS="%{optflags} -std=gnu11 -Wall -Wextra -Wno-unused-parameter" LDFLAGS="%{build_ldflags}"

# the SELinux module (policy of the package: the two domains of the server, see selinux/remotix.te)
make -C selinux -f %{_datadir}/selinux/devel/Makefile remotix.pp
bzip2 -9 -f selinux/remotix.pp

%install
B=%{buildroot}
install -D -m 0644 selinux/remotix.pp.bz2      $B%{_datadir}/selinux/packages/remotix.pp.bz2
install -D -m 0755 src/remotix                 $B%{rxlibexec}/remotix
install -D -m 0644 src/page.html               $B%{_datadir}/remotix/page.html
install -D -m 0644 %{SOURCE4}                  $B%{_datadir}/remotix/remotix.conf
# the keyfiles of the GNOME session's rules (value + lock), generated by the binary just built from the SAME table the program
# uses (DCONF_KEYS, session.c): the %%post compiles them into /etc/dconf/db/remotix.
src/remotix --dconf-keyfiles $B%{_datadir}/remotix/dconf/remotix.d
# the versions of the LINKED static libraries, read by pkg-config (the SBOM reads them)
printf '{"format":"remotix-linked/1","ngtcp2":"%%s","nghttp3":"%%s","source":"pkg-config of the linked .a files"}\n' \
  "$(pkg-config --modversion libngtcp2)" "$(pkg-config --modversion libnghttp3)" >$B%{_datadir}/remotix/linked.json
install -d -m 0755 $B%{_sysconfdir}/remotix/remotix.conf.d
install -D -m 0644 src/remotix.pam             $B%{_sysconfdir}/pam.d/remotix
install -D -m 0644 %{SOURCE5}                  $B%{_sysconfdir}/remotix/denied-users
# firewalld: the «remotix» service (7447 TCP and UDP), DEFINED and not opened
install -D -m 0644 %{SOURCE8}                  $B%{_prefix}/lib/firewalld/services/remotix.xml
install -D -m 0644 %{SOURCE9}                  $B%{_datadir}/applications/org.kde.remotix.desktop
install -D -m 0644 src/remotix-no-poweroff.rules      $B%{_datadir}/polkit-1/rules.d/50-remotix-no-poweroff.rules
install -D -m 0644 src/remotix-remote-sessions.rules  $B%{_datadir}/polkit-1/rules.d/40-remotix-remote-sessions.rules
install -D -m 0755 src/remotix-polkit-seated   $B%{rxlibexec}/remotix-polkit-seated
# the hook of the local login and the script that puts its line into the PAM stacks of the login screens
install -D -m 0755 src/remotix-local-login     $B%{rxlibexec}/remotix-local-login
install -D -m 0755 src/remotix-pam-hook        $B%{rxlibexec}/remotix-pam-hook
# the two belts left SWITCHED OFF
install -D -m 0644 src/remotix-power-keys.conf $B%{_datadir}/remotix/belts/remotix-power-keys.conf
install -D -m 0644 %{SOURCE6}                  $B%{_datadir}/remotix/belts/remotix-no-suspend.conf
install -D -m 0644 %{SOURCE2}                  $B%{_sysusersdir}/remotix.conf
install -D -m 0644 %{SOURCE3}                  $B%{_tmpfilesdir}/remotix.conf
install -D -m 0644 %{SOURCE1}                  $B%{_unitdir}/remotix.service
# needrestart (if it is ever installed): never restart remotix.service by itself
install -D -m 0644 %{SOURCE7}                  $B%{_sysconfdir}/needrestart/conf.d/remotix.conf

%pre
# Two checks (the same as Debian's preinst).  $1: 1 = first installation, 2 = upgrade.
#  - a NEW installation is refused when the machine has no DRM render node (REMOTIX encodes only on the card);
#  - REFUSE if an account named «remotix» already exists and is a PERSON's (or root's); REMEMBER that the account was on the machine
#    BEFORE the package (net-user-preexisting), so that removal never deletes it.
if [ "$1" -eq 1 ]; then
	found=
	for n in /sys/class/drm/renderD*; do
		[ -e "$n" ] && found=1 && break
	done
	if [ -z "$found" ]; then
		echo "remotix: this machine has no video card REMOTIX can use (no DRM render node: nothing named renderD* in /sys/class/drm)." >&2
		echo "remotix: REMOTIX encodes the desktop only on the video card (Intel, AMD or NVIDIA with its driver): it is not installed." >&2
		exit 1
	fi
fi
entry=$(getent passwd remotix || true)
if [ -n "$entry" ]; then
	uid=$(echo "$entry" | cut -d: -f3)
	gid=$(echo "$entry" | cut -d: -f4)
	home=$(echo "$entry" | cut -d: -f6)
	shell=$(echo "$entry" | cut -d: -f7)
	umin=$(sed -n 's/^UID_MIN[[:space:]]\{1,\}\([0-9]\{1,\}\).*/\1/p' /etc/login.defs 2>/dev/null | head -n 1)
	[ -n "$umin" ] || umin=1000
	why=
	{ [ "$uid" -eq 0 ] || [ "$gid" -eq 0 ]; } && why="$why uid $uid gid $gid (root's);"
	{ [ "$uid" -ge "$umin" ] && [ "$uid" -lt 60000 ]; } && why="$why uid $uid >= UID_MIN $umin;"
	case "$shell" in
	""|*/nologin|*/false) ;;
	*) why="$why login shell $shell;" ;;
	esac
	case "$home" in
	/home/*|/root|/root/*|/var/home/*) why="$why home $home;" ;;
	esac
	if [ -n "$why" ]; then
		echo "remotix: an account named «remotix» already exists and is a person's:$why" >&2
		echo "remotix: the network side would run as that account. Rename it (usermod -l NEWNAME remotix) or remove it, then install again." >&2
		exit 1
	fi
	# first installation only: the system user was there before our sysusers file
	if [ "$1" -eq 1 ] && [ ! -e /usr/lib/sysusers.d/remotix.conf ]; then
		install -d -m 0755 /var/lib/remotix
		echo "the account remotix was on the machine before the package" >/var/lib/remotix/net-user-preexisting
	fi
fi
# only now (an installation refused above must leave nothing behind in /var/lib/rpm-state)
%selinux_relabel_pre -s targeted
exit 0

%post
# The package switches nothing on: the service is enabled by the administrator (the Fedora preset is `disable *`);
# the firewall and the two belts left OFF in /usr/share/remotix/belts/ are the administrator's; the polkit rules are active.
# On upgrade %%systemd_postun_with_restart restarts the service ONLY if it was running; the desktops stay alive.
#
# The SELinux module first (the server's binary takes the type remotix_exec_t, the file contexts are applied by the relabel below).
%selinux_modules_install -s targeted %{_datadir}/selinux/packages/remotix.pp.bz2
%selinux_relabel_post -s targeted
# The macro above never fails the install (`|| :`).  Said CLEARLY if the module did not get in (like Debian's postinst: a warning, never a failure).
if selinuxenabled && ! semodule -l 2>/dev/null | grep -q '^remotix[[:space:]]*$\|^remotix[[:space:]]'; then
	echo "remotix: ⚠ the SELinux module «remotix» is NOT loaded (semodule -l does not list it): the server will not run in its own domain and the network side without its SELinux wall.  Try: sudo semodule -X 200 -i /usr/share/selinux/packages/remotix.pp.bz2" >&2
fi
# The system user remotix, then the directories (tmpfiles), BEFORE anything can start the new server.  A failure is said, never makes dnf fail.
systemd-sysusers remotix.conf || echo "remotix: ⚠ systemd-sysusers remotix.conf failed" >&2
systemd-tmpfiles --create remotix.conf || echo "remotix: ⚠ systemd-tmpfiles --create remotix.conf failed" >&2

# The locks of the GNOME remote session are the SYSTEM dconf database /etc/dconf/db/remotix, compiled HERE from the keyfiles the
# package ships.  Compiled to a temporary file and RENAMED: programs of a living session may have the old one open.  Without `dconf`
# (only a weak dependency) or if it fails: said, never makes dnf fail; the program then runs its declared fallback.
if command -v dconf >/dev/null 2>&1 && [ -d /usr/share/remotix/dconf/remotix.d ]; then
	install -d -m 0755 /etc/dconf/db
	rx_db_tmp=/etc/dconf/db/remotix.new.$$
	if dconf compile "$rx_db_tmp" /usr/share/remotix/dconf/remotix.d && chmod 0644 "$rx_db_tmp" && mv -f "$rx_db_tmp" /etc/dconf/db/remotix; then
		:
	else
		rm -f "$rx_db_tmp"
		echo "remotix: ⚠ /etc/dconf/db/remotix could not be compiled: the GNOME remote session will use its fallback (it is said in the log)" >&2
	fi
else
	echo "remotix: ⚠ dconf not found: /etc/dconf/db/remotix not made; the GNOME remote session will use its fallback" >&2
fi

# The files the package does not ship but the service or this scriptlet makes (tmpfiles, dconf compile) get their types from the module's file contexts: an
# upgrade from a package without the wall finds them labelled var_lib_t / var_run_t / etc_t.  restorecon on these paths only, never fails the install.
restorecon -R /var/lib/remotix /run/remotix /etc/dconf/db/remotix >/dev/null 2>&1 || :
# The hook of the LOCAL login: its line goes into the PAM stacks of the login screens (Debian: pam-auth-update).  Never fails the installation.
/usr/libexec/remotix/remotix-pam-hook apply || echo "remotix: ⚠ the hook of the local login could not be fully applied (see above): a local login may not close the user's remote desktop first" >&2

# A card that is there (%%pre checked the render node) but cannot encode — said HERE, once, with the product's own test
# (exit 0 = it encodes, 3 = no card can encode, 1 = it opens and produces nothing).  First installation only; never makes dnf fail.
if [ "$1" -eq 1 ] && [ -x /usr/libexec/remotix/remotix ]; then
	if ! timeout 30 /usr/libexec/remotix/remotix --encoding-test h264 >/dev/null 2>&1; then
		echo "remotix: ⚠ the video card of this machine did not encode a test frame (H.264): REMOTIX will not show any desktop until it can." >&2
		echo "remotix:   on Fedora the H.264 driver is not in the base repositories: enable RPM Fusion (free) and install mesa-va-drivers-freeworld" >&2
		echo "remotix:   (NVIDIA: its proprietary driver), then: sudo /usr/libexec/remotix/remotix --encoding-test h264" >&2
	fi
fi

# labwc is only a weak dependency (a GNOME-only machine does not need it), so `--setopt=install_weak_deps=False` leaves it out; on a
# machine whose desktop is XFCE or LXQt (and not GNOME or Plasma) no desktop could then be born.  Said HERE; never makes dnf fail.
if ! command -v labwc >/dev/null 2>&1 &&
	{ command -v xfce4-session >/dev/null 2>&1 || command -v lxqt-session >/dev/null 2>&1; } &&
	! command -v gnome-shell >/dev/null 2>&1 && ! command -v startplasma-wayland >/dev/null 2>&1; then
	echo "remotix: ⚠ the package labwc is not installed (it is only a weak dependency): the XFCE/LXQt desktop of this machine cannot start in REMOTIX." >&2
	echo "remotix:   install it: sudo dnf install labwc" >&2
fi
# The firewalld service definition (/usr/lib/firewalld/services/remotix.xml) is known to the RUNNING firewalld only after a reload: without it
# `firewall-cmd --permanent --add-service=remotix` answers INVALID_SERVICE right after the install (F20).  The standard macro of the Fedora packages that ship
# a service definition.  It opens NOTHING (D5: the administrator opens the port); a reload also forgets rules added at run time only.
%firewalld_reload
%systemd_post remotix.service
exit 0

%preun
# Only on removal ($1 = 0), not on upgrade.
if [ "$1" -eq 0 ]; then
	# Close the REMOTIX sessions.  Only the logind sessions of the PAM service «remotix» — never the whole user.
	# The sessions are ended FIRST, with the service still running (the child alive, the session's scope in place: logind stops it,
	# the child sees the order and cleans up); then the service is stopped; then the sweep is repeated for whatever the service's stop
	# left in an abandoned scope.  What survives SIGTERM is killed (SIGKILL on the scope unit) after a bounded wait — never a
	# process outside a REMOTIX session's scope.
	remotix_sessions() {
		for id in $(loginctl list-sessions --no-legend 2>/dev/null | awk '{print $1}'); do
			[ "$(loginctl show-session "$id" -p Service --value 2>/dev/null || true)" = remotix ] || continue
			# a REMOTIX session is seatless; a seated one is never ours, whatever its Service says
			[ -z "$(loginctl show-session "$id" -p Seat --value 2>/dev/null || true)" ] || continue
			echo "$id"
		done
	}
	remotix_scope_alive() { systemctl is-active --quiet "session-$1.scope" 2>/dev/null; }
	remotix_close_sessions() {
		ids=$(remotix_sessions)
		[ -n "$ids" ] || return 0
		for id in $ids; do
			rx_users="$rx_users $(loginctl show-session "$id" -p Name --value 2>/dev/null || true)"
			remotix_scope_alive "$id" && loginctl terminate-session "$id" >/dev/null 2>&1 || true
		done
		# SIGTERM first (logind did it): up to 15 s for the desktop to go by itself
		n=0
		while [ "$n" -lt 15 ]; do
			alive=
			for id in $ids; do remotix_scope_alive "$id" && alive=1; done
			[ -n "$alive" ] || break
			sleep 1
			n=$((n + 1))
		done
		# what ignored it: SIGKILL to the scope of THAT session (and to nothing else), then up to 5 s
		for id in $ids; do
			remotix_scope_alive "$id" || continue
			echo "remotix: ⚠ the desktop of session $id did not end within 15 s: killed" >&2
			systemctl kill --kill-whom=all --signal=SIGKILL "session-$id.scope" >/dev/null 2>&1 || true
		done
		n=0
		while [ "$n" -lt 5 ]; do
			alive=
			for id in $ids; do remotix_scope_alive "$id" && alive=1; done
			[ -n "$alive" ] || break
			sleep 1
			n=$((n + 1))
		done
	}
	rx_users=
	if [ -d /run/systemd/system ] && command -v loginctl >/dev/null 2>&1; then
		remotix_close_sessions
	fi
	# Stopped here (if running) and not left to the macro below: the order matters (sessions first, service, sessions again).
	if [ -d /run/systemd/system ]; then
		systemctl stop remotix.service >/dev/null 2>&1 || true
	fi
	# the local-login line goes out of the PAM stacks only NOW, with the service stopped: with the service running, its ExecStartPre
	# would put it back if the service restarted meanwhile.  A failure is said, never makes rpm fail.
	/usr/libexec/remotix/remotix-pam-hook remove || echo "remotix: ⚠ the PAM hook could not be fully removed: check /etc/pam.d/gdm-*, plasmalogin*, lightdm* and sddm*" >&2
	if [ -d /run/systemd/system ] && command -v loginctl >/dev/null 2>&1; then
		# the service is down: a session whose child went with it left its scope abandoned — the second sweep
		remotix_close_sessions
		# then, if the person has no OTHER graphical session (a desktop at the machine), the desktop that lives in their user manager is stopped
		for u in $(printf '%%s\n' $rx_users | sort -u); do
			[ -n "$u" ] || continue
			other=
			for id in $(loginctl list-sessions --no-legend 2>/dev/null | awk '{print $1}'); do
				[ "$(loginctl show-session "$id" -p Name --value 2>/dev/null || true)" = "$u" ] || continue
				[ "$(loginctl show-session "$id" -p Service --value 2>/dev/null || true)" = remotix ] && continue
				case "$(loginctl show-session "$id" -p Type --value 2>/dev/null || true)" in
				x11|wayland|mir) other=1 ;;
				esac
			done
			[ -n "$other" ] || systemctl --user -M "$u@" stop graphical-session.target >/dev/null 2>&1 || true
		done
	fi
	# remove-membership: the card-group enrolments the product made at a user's first connection
	# (/var/lib/remotix/group-enrollments.jsonl) are undone with gpasswd -d.  The record must be a regular file owned by root.
	if [ -f /var/lib/remotix/group-enrollments.jsonl ] && [ ! -L /var/lib/remotix/group-enrollments.jsonl ] \
	   && [ "$(stat -c %%u /var/lib/remotix/group-enrollments.jsonl)" = 0 ]; then
		sed -n 's/.*"user":"\([^"]*\)".*"group":"\([^"]*\)".*/\1 \2/p' /var/lib/remotix/group-enrollments.jsonl | sort -u |
		while read -r u g; do
			case "$u$g" in *[!A-Za-z0-9._-]*|"") continue ;; esac
			gpasswd -d "$u" "$g" >/dev/null 2>&1 || true
		done
	fi
	# The ACL the server puts on /dev/dri/renderD* for a user's private group (card grants) are taken back HERE, with the service
	# already stopped and BEFORE the record (/var/lib/remotix/render-grants, deleted in %%postun) and the binary go.  A failure is said,
	# leaves the marker %%postun reads (the record is then kept), and never makes rpm fail.
	if [ -x /usr/libexec/remotix/remotix ]; then
		rm -f /run/remotix/render-grants-kept
		if ! /usr/libexec/remotix/remotix --drop-render-grants; then
			echo "remotix: ⚠ the card grants (ACL on /dev/dri/renderD*) could not all be taken back: they vanish at the next boot" >&2
			install -d -m 0755 /run/remotix 2>/dev/null && : > /run/remotix/render-grants-kept
		fi
	fi
fi
%systemd_preun remotix.service
exit 0

%postun
%selinux_modules_uninstall -s targeted remotix
if [ "$1" -eq 0 ]; then
%selinux_relabel_post -s targeted
fi
%systemd_postun_with_restart remotix.service
# (the definition is gone after a removal: the running firewalld forgets it too)
%firewalld_reload
# Only on removal ($1 = 0).  Debian splits this between `remove` and `purge`; an RPM has no purge, and the owner's rule is that
# uninstalling leaves the system clean, so everything of Debian's purge is done here, too.
if [ "$1" -eq 0 ]; then
	# the record of the card grants is deleted only if %%preun took the grants back (else it still says which are left)
	keep=
	if [ -e /run/remotix/render-grants-kept ]; then
		keep=1
		echo "remotix: /var/lib/remotix/render-grants kept: the card grants could not all be taken back" >&2
	fi
	rm -rf /var/lib/remotix/net /var/lib/remotix/certificates /var/lib/remotix/ban /var/lib/remotix/ban.new /run/remotix
	[ -n "$keep" ] || rm -f /var/lib/remotix/render-grants /var/lib/remotix/render-grants.new
	# Each person's product files in ~/.local/state/remotix/ (session log and the state files the product writes there) and the small
	# dconf database ~/.config/dconf/remotix, removed BY NAME, AS THAT USER (runuser), so a symlink planted in a home cannot make
	# root delete something else.  Never `rm -rf` of a folder in a home.  Homes that are absent or unreachable are skipped in
	# silence.  If the product writes another file there, its name goes into this list.
	if command -v runuser >/dev/null 2>&1; then
		getent passwd | while IFS=: read -r u _ _ _ _ home _; do
			[ -n "$home" ] && [ "$home" != / ] && { [ -d "$home/.local/state/remotix" ] || [ -f "$home/.config/dconf/remotix" ]; } || continue
			runuser -u "$u" -- sh -c 'if cd "$1/.local/state/remotix" 2>/dev/null; then rm -f session.log xfce-chiavi xfce-vecchi-ripristinati lxqt-restored gnome-ripristinato; cd /; rmdir "$1/.local/state/remotix" 2>/dev/null; fi; if [ -f "$1/.config/dconf/remotix" ] && [ ! -L "$1/.config/dconf/remotix" ]; then rm -f "$1/.config/dconf/remotix"; fi; :' sh "$home" </dev/null >/dev/null 2>&1 || true
		done
	fi
	# the system user (unless it pre-existed)
	if [ ! -e /var/lib/remotix/net-user-preexisting ] && entry=$(getent passwd remotix) && [ -n "$entry" ]; then
		uid=$(echo "$entry" | cut -d: -f3)
		if [ "$uid" -gt 0 ] && [ "$uid" -lt 1000 ]; then
			userdel remotix >/dev/null 2>&1 || echo "remotix: ⚠ the system user remotix could not be removed" >&2
			getent group remotix >/dev/null 2>&1 && groupdel remotix >/dev/null 2>&1 || true
		fi
	fi
	rm -f /var/lib/remotix/net-user-preexisting /var/lib/remotix/group-enrollments.jsonl
	rmdir /var/lib/remotix 2>/dev/null || true
	# the module is gone: what is left of ours (the folder kept for a pre-existing user, say) must not keep a type that no longer exists
	[ -d /var/lib/remotix ] && restorecon -R /var/lib/remotix >/dev/null 2>&1 || true
	# the system dconf database of the GNOME remote session (made by %%post, not in the package's file list) leaves with the package
	rm -f /etc/dconf/db/remotix /etc/dconf/db/remotix.new /etc/dconf/db/remotix.new.*
	# what rpm leaves when the administrator edited a %%config file (*.rpmsave), by exact name, and the folders if they are empty
	# (rmdir, never rm -rf: the administrator's own files in /etc/remotix/remotix.conf.d stay, and so does the folder that holds them)
	rm -f /etc/remotix/denied-users.rpmsave /etc/pam.d/remotix.rpmsave /etc/needrestart/conf.d/remotix.conf.rpmsave
	rmdir /etc/remotix/remotix.conf.d /etc/remotix 2>/dev/null || true
	command -v needrestart >/dev/null 2>&1 || rmdir /etc/needrestart/conf.d /etc/needrestart 2>/dev/null || true
fi
exit 0

# The login screen's package may come AFTER us, or be updated: the line is applied again (idempotent; the vendor files are copied afresh).
# %%triggerin runs when gdm is installed or updated (or when we are installed with gdm there), %%triggerpostun after an old gdm has gone.
%triggerin -- gdm
/usr/libexec/remotix/remotix-pam-hook apply gdm || :
%triggerpostun -- gdm
/usr/libexec/remotix/remotix-pam-hook apply gdm || :
# XFCE's login screen: lightdm.  Its PAM files are in /usr/lib/pam.d (the package's own, not config files of /etc): we only make OUR copies in /etc/pam.d.
%triggerin -- lightdm
/usr/libexec/remotix/remotix-pam-hook apply lightdm || :
%triggerpostun -- lightdm
/usr/libexec/remotix/remotix-pam-hook apply lightdm || :
# LXQt's login screen: sddm.  ⚠ Its PAM files (/etc/pam.d/sddm, sddm-autologin, sddm-greeter) are %%config(noreplace) FILES OF THE sddm PACKAGE and we change
# them in place, so for rpm they are «modified by the administrator».  rpm decides what to do with a config file BEFORE any scriptlet or trigger runs (it
# compares the file on disk with the old package's digest), so taking our block out in %%triggerprein is too late for that decision (tried, `[M]` 22 Nov 2026:
# the update wrote .rpmnew and kept the old text; the removal left .rpmsave).  What the hook does (src/remotix-pam-hook, prepare_one / adopt_one):
#   %%triggerprein (before sddm is installed or updated) and %%triggerun (before it is removed; only for a REAL removal, $2 = instances left = 0, not for the old
#   half of an update): `prepare sddm` notes whether the file minus our block is exactly what the package shipped and takes the block out;
#   %%triggerin / %%triggerpostun: `apply sddm` puts the .rpmnew in force (or deletes the .rpmsave) only if its digest proves it is the old vendor text,
#   then adds the block again.  A file the administrator changed gets rpm's normal outcome plus our block.
# The few seconds of an update of sddm WITHOUT the block are accepted (a local login in that window does not close the remote desktop first); an update that
# fails halfway leaves the block out until the next start of the service (ExecStartPre «check» applies it again) or the next %%triggerin.
%triggerprein -- sddm
/usr/libexec/remotix/remotix-pam-hook prepare sddm || :
%triggerun -- sddm
if [ "$2" -eq 0 ]; then /usr/libexec/remotix/remotix-pam-hook prepare sddm || :; fi
%triggerin -- sddm
/usr/libexec/remotix/remotix-pam-hook apply sddm || :
%triggerpostun -- sddm
/usr/libexec/remotix/remotix-pam-hook apply sddm || :
# KDE's login screen on Fedora 45 is plasmalogin, package plasma-login-manager (its PAM files are in /usr/lib/pam.d, like gdm's)
%triggerin -- plasma-login-manager
/usr/libexec/remotix/remotix-pam-hook apply plasmalogin || :
%triggerpostun -- plasma-login-manager
/usr/libexec/remotix/remotix-pam-hook apply plasmalogin || :

%files
%license LICENSE.md
%doc THIRD-PARTY-LICENSES
%dir %{rxlibexec}
%{rxlibexec}/remotix
%{rxlibexec}/remotix-polkit-seated
%{rxlibexec}/remotix-local-login
%{rxlibexec}/remotix-pam-hook
%dir %{_datadir}/remotix
%{_datadir}/remotix/page.html
%{_datadir}/remotix/remotix.conf
%{_datadir}/remotix/linked.json
%{_datadir}/remotix/dconf
%{_datadir}/remotix/belts
%{_datadir}/selinux/packages/remotix.pp.bz2
%dir %{_sysconfdir}/remotix
%dir %{_sysconfdir}/remotix/remotix.conf.d
%config(noreplace) %{_sysconfdir}/remotix/denied-users
%config(noreplace) %{_sysconfdir}/pam.d/remotix
%dir %{_sysconfdir}/needrestart
%dir %{_sysconfdir}/needrestart/conf.d
%config(noreplace) %{_sysconfdir}/needrestart/conf.d/remotix.conf
%{_prefix}/lib/firewalld/services/remotix.xml
%{_datadir}/applications/org.kde.remotix.desktop
%{_datadir}/polkit-1/rules.d/50-remotix-no-poweroff.rules
%{_datadir}/polkit-1/rules.d/40-remotix-remote-sessions.rules
%{_sysusersdir}/remotix.conf
%{_tmpfilesdir}/remotix.conf
%{_unitdir}/remotix.service

%changelog
* Wed Nov 25 2026 nicfio <remotix@nicfio.it> - 1.2.0-1
- First release for Fedora 45 (GNOME, KDE Plasma, XFCE, LXQt), with its own SELinux module.
- KDE: a local login closes the remote desktop also when a program does not close by itself.

* Sat Nov 21 2026 nicfio <remotix@nicfio.it> - 1.0.1-1
- Fedora 45 build (step 1 of the Fedora plan: the package only).
