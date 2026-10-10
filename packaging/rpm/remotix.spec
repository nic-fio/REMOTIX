# remotix.spec — the native REMOTIX package for the .rpm family.
#
#   Fedora 44 · Alma 10 (Rocky/RHEL 10 compatibili) · openSUSE Tumbleweed · Leap 16
#
# ⭐ ONE spec with %%if branches, as Cockpit does (`tools/cockpit.spec`):
#    0%%{?fedora} · 0%%{?rhel} · 0%%{?suse_version}.  `fasi/17-l-installatore.md`
#    §6.1-§6.4.  It is built INSIDE the container of each target
#    (`src/costruzione/Contenitore.<target>`) with `packaging/rpm/costruisci-rpm.sh`.
#
# ⭐ The libraries are computed by rpmbuild reading the binary (the automatic «Requires»
#    by soname: libva, libopus, libssl, libpam, libpipewire,
#    libei, …): this is the
#    cure of `LEZIONI.md` §2.5-bis.  Below, only what rpm CANNOT see is written
#    BY HAND, because it is loaded or executed at run time: the
#    compositor for XFCE/LXQt, wlr-randr, Xwayland, the Plasma wallpaper, the
#    VA-API drivers.  (OpenSSL >= 3.5 it sees on its own: `libssl.so.3(OPENSSL_3.5.0)`.)
#
# ⭐ `DECISIONI.md` §10.12 — the package ships only INERT pieces (program,
#    page, disabled unit, PAM, /etc/remotix, the belts OFF in
#    /usr/share/remotix/cinture/, the firewalld definition).  It neither enables nor starts the service, and touches no groups, belts or
#    firewall: the engine mounts them, with consent and in its log (R40).
#    ⛔ No guard that prevents the service from starting (no
#    ExecCondition, no ConditionPathExists on a mark): there are TWO ways,
#    the installer or the source by hand; `remotix stato` will only say, for
#    information, whether the installation is certified.
#
# ⛔ Never in the package (§6.4, R14): test users, the benches' `sudoers.d`,
#    `gpu-udev.sh`, `riavvia-*.sh`, `ld.so.conf.d`, `provisiona.sh`.
# ⛔ The package NEVER pulls in a desktop (`DECISIONI.md` §10.7: without a
#    desktop the engine installs it): dependencies tied to a desktop are
#    CONDITIONAL, `(X if <desktop session>)`.
# ⛔ The package NEVER adds repositories (RPM Fusion, Packman, EPEL): §4.2
#    rule 2 and D5.  The installation engine will do it, with consent.

%global ngtcp2_ver  1.25.0
%global nghttp3_ver 1.18.0

# openSUSE keeps the packages' PAM files in /usr/lib/pam.d (§4.3)
%if 0%{?suse_version}
%{!?_pam_vendordir: %global _pam_vendordir %{_prefix}/lib/pam.d}
%global pamdir      %{_pam_vendordir}
%global pamsorgente remotix.pam.suse
%else
%global pamdir      %{_sysconfdir}/pam.d
%global pamsorgente remotix.pam.fedora
%endif

Name:           remotix
# Version and release are given by the release command (packaging/rilascio.sh) through
# costruisci-rpm.sh: RX_VERSIONE (--define "rx_versione X.Y.Z") and RX_REVISIONE
# (--define "rx_rilascio N"); defaults 0.17.0 and 1.
Version:        %{?rx_versione}%{!?rx_versione:0.17.0}
Release:        %{?rx_rilascio}%{!?rx_rilascio:1}%{?dist}
Summary:        This machine's desktop in the browser
# Our own text, not a standard one (DECISIONI §10.39): free for personal and non-profit use,
# source readable, no modifications, no redistribution. Its text is LICENSE.md.
License:        LicenseRef-REMOTIX
URL:            https://github.com/nic-fio/REMOTIX
# An archive of src/, banchi/rcp/ (the twin copy that `make` compares) and
# packaging/rpm/, made by `costruisci-rpm.sh`.
Source0:        %{name}-%{version}.tar.gz

ExclusiveArch:  x86_64

BuildRequires:  gcc
BuildRequires:  make
BuildRequires:  pkgconfig
BuildRequires:  systemd-rpm-macros
BuildRequires:  pam-devel
BuildRequires:  pkgconfig(openssl) >= 3.5.0
BuildRequires:  pkgconfig(gio-2.0) >= 2.80
BuildRequires:  pkgconfig(libpipewire-0.3) >= 0.3.48
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(libva)
BuildRequires:  pkgconfig(libva-drm)
# ⭐ Phase 18 (`fasi/18-senza-ffmpeg.md`): no ffmpeg; libopus (the audio).
# ⛔ Phase 19 (1 Oct 2026, `DECISIONI.md` §10.27): OpenH264 and SVT-AV1, the software
#   fallback, are OUT — and with them the Cisco OpenH264 repository.
BuildRequires:  pkgconfig(opus)
# ⛔ no libyuv: the colour conversion is ours (`src/colori709.c`, fasi/18 §1);
#   removed on 30 Sep (T10).
BuildRequires:  pkgconfig(libei-1.0) >= 1.1.0
BuildRequires:  pkgconfig(xkbcommon)
BuildRequires:  pkgconfig(wayland-client)
BuildRequires:  pkgconfig(wayland-scanner)
BuildRequires:  pkgconfig(gbm)
# ⭐ Phase 19: Vulkan Video (src/vulkanvideo.c) — only the loader and the headers
#   (vulkan-loader-devel; `[M]` 1 Oct 2026: 1.4.328 on Alma 10 AppStream, 1.4.341
#   on Fedora 44).  The minimum 1.3.274 is the Makefile's.
BuildRequires:  pkgconfig(vulkan) >= 1.3.274
# ⚠ ngtcp2 >= 1.25.0 and nghttp3: they are NOT a BuildRequires, because almost no
#   distribution has them (§6.3).  The container builds them, STATIC ONLY, in
#   /usr/local/lib (`src/costruzione/quic-statiche.sh`); %%build checks that they are
#   there and that the version is the one declared below.
# ⭐ D2 CLOSED (`DECISIONI.md` §10.6): ngtcp2 and nghttp3 INSIDE the binary, with the
#   security updates on us — whatever is missing or too
#   old REMOTIX brings, except patented codecs and desktops.
Provides:       bundled(ngtcp2) = %{ngtcp2_ver}
Provides:       bundled(nghttp3) = %{nghttp3_ver}

# ⭐ SELinux (T6, `DECISIONI.md` §10.18): the REMOTIX PAM is sshd's, with
#    `pam_selinux`; the transition to the user's context is allowed by the REMOTIX
#    module, in the remotix-selinux subpackage (like cockpit-ws-selinux).  The package
#    manager pulls it in ONLY where the «targeted» policy exists: Fedora,
#    Alma, openSUSE (Tumbleweed and Leap 16 are enforcing by default).
%global selinuxtype targeted
BuildRequires:  selinux-policy-devel
BuildRequires:  bzip2
Requires:       (%{name}-selinux = %{version}-%{release} if selinux-policy-%{selinuxtype})

# The PipeWire DAEMON + wireplumber: GNOME/KDE video capture goes through PipeWire
# (mutter/kwin screencast) and so does the audio of EVERY desktop (suono.c); rpm sees the LIBRARY
# (libpipewire) but not the daemon.  The desktop groups bring it, but minimal installations
# do not (T10, 30 Sep: openSUSE GNOME from the Minimal-VM image WITHOUT pipewire ⇒ mutter does not
# reach the screencast, «Error connecting to the screencast service», and the desktop never arrives).
Requires:       pipewire
Requires:       wireplumber

%if 0%{?fedora} || 0%{?rhel}
# The firewalld service is DEFINED in the firewalld-filesystem directory (no
# daemon, no rules): opening it belongs to the engine, with consent (D6).
Requires:       firewalld-filesystem
%endif

%if 0%{?fedora}
# XFCE and LXQt run under labwc (REMOTIX starts it; no default group brings it,
# §4.6).  xfce4-session 4.20 is X11: under labwc it needs Xwayland.  XFCE and LXQt: the
# monitor measurement goes through wlr-randr (`primario_misurato()`, XFCE too since 5 Oct).  CONDITIONAL dependencies:
# only if that desktop is present.
Requires:       (labwc if xfce4-session)
Requires:       (labwc if lxqt-session)
Requires:       (wlr-randr if lxqt-session)
Requires:       (wlr-randr if xfce4-session)
# Xwayland under labwc for X11 applications (XFCE 4.20 AND the LXQt panel/config):
# without it, labwc «cannot create xwayland server» and the X11 panel does not start (T10, 30 Sep:
# leap16-lxqt).  Tied to labwc, not to a desktop: it holds for XFCE and LXQt.
Requires:       (xorg-x11-server-Xwayland if labwc)
# labwc DIES without a scalable font (labwc #2525: with bitmap fonts only
# the title bar comes out 1.4 million pixels tall and `buffer.c:90`
# aborts).  On Fedora the desktop groups bring one, but a machine with
# labwc and no default desktop does not: the distribution's default sans.
Requires:       (default-fonts-core-sans if labwc)
# The VA-API drivers: loaded with dlopen, rpm does not see them.  On Fedora the
# Mesa driver (AMD, virtio) is in mesa-dri-drivers, the free Intel one in
# libva-intel-media-driver.  ⚠ NEITHER encodes H.264 by default (§4.2;
# `[M]` 30 Sep from the binaries, phase 18): RPM Fusion is needed (mesa-va-drivers-freeworld,
# free / intel-media-driver, NONFREE), which the package does NOT add (D5).
# Recommends: on a machine without an Intel GPU the Intel driver is not needed, and whoever
# removes them must not break the package.
Recommends:     mesa-dri-drivers
Recommends:     (libva-intel-media-driver or intel-media-driver)
# ⭐ Phase 19: the Mesa VULKAN drivers (RADV for AMD: the Vulkan Video path, which
#   the product tries BEFORE VA-API).  The loader (vulkan-loader, libvulkan.so.1)
#   rpm computes from the binary.  NVIDIA: the ICD comes with the proprietary driver.
Recommends:     mesa-vulkan-drivers
%endif

%if 0%{?rhel}
# ⛔ Phase 19: here were svt-av1-libs (EPEL 10) and openh264 (Cisco repository for
#   EPEL 10), the software fallback — out.
# ⛔ No labwc/XFCE/LXQt in RHEL/EPEL 10 (§3): no dependency to write.
# ⛔ RHEL 10 Mesa has no VA-API and EPEL lacks the Intel driver (§4.2): GPU
#   encoding exists only with third-party repositories.
%endif

%if 0%{?suse_version}
Requires:       (labwc if xfce4-session)
Requires:       (labwc if lxqt-session)
Requires:       (wlr-randr if lxqt-session)
Requires:       (wlr-randr if xfce4-session)
# Xwayland under labwc for X11 applications (XFCE 4.20 AND the LXQt panel/config):
# without it, labwc «cannot create xwayland server» and the X11 panel does not start (T10, 30 Sep:
# leap16-lxqt from the Minimal-VM image).  Tied to labwc, not to a desktop.
Requires:       (xwayland if labwc)
# ⛔ labwc DIES without a scalable font (labwc #2525, `buffer.c:90`): the
# openSUSE LXQt group brings `google-droid-fonts` only as RECOMMENDED, and
# on installations without recommends it is missing.  Any one of the scalable sans.
Requires:       ((google-droid-fonts or dejavu-fonts or google-noto-sans-fonts or liberation-fonts) if labwc)
# `[M]` T1 (§11.1 D): without breeze6-wallpapers plasmashell does not find the wallpaper and
# shows neither desktop nor panel (black canvas).  On installations without
# «recommends» (the Minimal image, `solver.onlyRequires`) the KDE group does not bring it.
Requires:       (breeze6-wallpapers if plasma6-workspace)
# VA-API drivers (dlopen).  Phase 18 (`[M]` 30 Sep, from the binaries): the official
# Intel driver encodes H.264; the official Mesa lacks h264/h265 ⇒ with an AMD
# GPU the Packman one is needed (Mesa-dri, Mesa-libva).  The package does NOT add
# Packman (D5).
Recommends:     Mesa-libva
Recommends:     intel-media-driver
%endif

%description
REMOTIX brings this machine's desktop (GNOME, KDE Plasma, XFCE, LXQt) into
a browser, with WebTransport and H.264 video encoded on the graphics card.
Every user of the machine logs in with their own password; root does not.

⚠ H.264 encoding on the graphics card uses the distribution's drivers: on Fedora
and Alma RPM Fusion is needed, on openSUSE with an AMD card Packman, which this
package does not add.  Without a card able to encode, REMOTIX does not
encode: there is no software fallback.

%package selinux
Summary:        The REMOTIX SELinux module
BuildArch:      noarch
Requires(post): selinux-policy-%{selinuxtype}
Requires(post): selinux-policy-base
Requires(post): libselinux-utils
Requires(post): policycoreutils

%description selinux
The SELinux module of the REMOTIX service: the remotix_t domain, port 7447
(remotix_port_t) and the transition to the user's context when the session
opens, as for sshd.

%prep
%autosetup -n %{name}-%{version}

%build
# ⛔ The static ngtcp2/nghttp3 must be present, and of the declared version:
#    a binary with an ngtcp2 different from the one in `Provides: bundled(...)`
#    would be an SBOM that lies (R24).
for l in libngtcp2 libngtcp2_crypto_ossl libnghttp3; do
    pkg-config --exists $l || { echo "⛔ $l: missing (it is built in the containers of src/costruzione/)"; exit 1; }
done
test "$(pkg-config --modversion libngtcp2)"  = %{ngtcp2_ver}  || { echo "⛔ ngtcp2 $(pkg-config --modversion libngtcp2), declared %{ngtcp2_ver}"; exit 1; }
test "$(pkg-config --modversion libnghttp3)" = %{nghttp3_ver} || { echo "⛔ nghttp3 $(pkg-config --modversion libnghttp3), declared %{nghttp3_ver}"; exit 1; }
# The distribution's flags (FORTIFY, PIE, stack protection, …) IN THE ENVIRONMENT:
# the Makefile has `CFLAGS ?=` and then `CFLAGS +=`.  Passed on the make command
# line they would override the `+=` too (and the library headers would vanish).
cd src
export CFLAGS="%{optflags} -std=gnu11 -Wall -Wextra -Wno-unused-parameter"
export LDFLAGS="%{?build_ldflags}"
%if 0%{?suse_version}
# openSUSE: %%{optflags} does not ask for PIE (rpmlint: position-independent-executable-suggested)
CFLAGS="$CFLAGS -fPIE"; LDFLAGS="$LDFLAGS -pie"
%endif
make pulisci >/dev/null
make %{?_smp_mflags} tutto
cd ..

# The SELinux module, with the policy interfaces of THIS distribution.
# ⚠ `--define "rx_selinux_permissivo 1"` (costruisci-rpm.sh: RX_SELINUX_PERMISSIVO=1)
#   builds the module with the domain in «permissive»: to MEASURE the denials of a
#   whole session in a single run.  ⛔ Never in a published package.
cd packaging/rpm/selinux
%{?rx_selinux_permissivo:echo 'permissive remotix_t;' >> remotix.te}
make -f %{_datadir}/selinux/devel/Makefile remotix.pp
bzip2 -9 remotix.pp
cd ../../..

%install
install -D -m 0755 src/remotix %{buildroot}%{_libexecdir}/remotix/remotix
install -D -m 0644 src/pagina.html %{buildroot}%{_datadir}/remotix/pagina.html
# The DEFAULTS (port, options): owned by the package, an upgrade rewrites them.
# The administrator's choices in /etc/remotix/remotix.conf.d/*.conf (they win).
install -D -m 0644 packaging/rpm/remotix.conf %{buildroot}%{_datadir}/remotix/remotix.conf
# R24 (T8): the versions of the LINKED static libraries (pkg-config in the build
# container), for the archive SBOM.
printf '{"formato":"remotix-incorporate/1","ngtcp2":"%s","nghttp3":"%s","fonte":"pkg-config of the linked .a files"}\n' \
    "$(pkg-config --modversion libngtcp2)" "$(pkg-config --modversion libnghttp3)" \
    > %{buildroot}%{_datadir}/remotix/incorporate.json
install -D -m 0644 packaging/rpm/remotix.service %{buildroot}%{_unitdir}/remotix.service
install -D -m 0644 packaging/rpm/remotix.tmpfiles %{buildroot}%{_tmpfilesdir}/remotix.conf
install -D -m 0644 src/%{pamsorgente} %{buildroot}%{pamdir}/remotix

# /etc/remotix: who is excluded (the PAM has onerr=fail: without the file nobody
# gets in, so the file comes with the package and is left alone if changed), and the
# directory of the administrator's choices (empty: the format belongs to the engine, T4).
install -d -m 0755 %{buildroot}%{_sysconfdir}/remotix/remotix.conf.d
printf 'root\n' > %{buildroot}%{_sysconfdir}/remotix/utenti-negati
chmod 0644 %{buildroot}%{_sysconfdir}/remotix/utenti-negati

# The KWin capture permission (`zkde_screencast_unstable_v1`): KWin looks for it in
# XDG_DATA_DIRS.  ⚠ Today the program ALSO writes it, as root, while running
# (`src/kwin.c:48`, `kwin_scrivi_permesso()`): the content here is byte-for-byte
# identical to what it would write, so it does not rewrite it.  ⇒ To be changed in the C
# (§4.4): at run time only the check (`kwin.c:342`).  Not changed in T3.
install -D -m 0644 packaging/rpm/org.kde.remotix.desktop %{buildroot}%{_datadir}/applications/org.kde.remotix.desktop

# ⭐ `DECISIONI.md` §10.12 — the installer is the only way: the three belts of
#   §4.7 (no power-off, no suspend, the keys do not power off) arrive
#   OFF, outside the paths polkit and systemd read.  The engine mounts them,
#   with consent (D4 open: always, or the administrator's choice?) and in its
#   log; the paths they will go to are the VENDOR ones
#   (/usr/share/polkit-1/rules.d/50-…, /usr/lib/systemd/{logind,sleep}.conf.d/),
#   never /etc: an administrator's file with the same name in /etc wins (R34).
install -D -m 0644 src/remotix-niente-spegnimento.rules %{buildroot}%{_datadir}/remotix/cinture/50-remotix-niente-spegnimento.rules
install -D -m 0644 src/remotix-tasti.conf %{buildroot}%{_datadir}/remotix/cinture/remotix-tasti.conf
install -D -m 0644 packaging/rpm/remotix-niente-sospensione.conf %{buildroot}%{_datadir}/remotix/cinture/remotix-niente-sospensione.conf

# firewalld: the «remotix» service DEFINED, not opened (D6, §10.12): the file
# makes a name known to firewalld and changes no zone.  Opening it
# (`firewall-cmd --permanent --add-service=remotix`) belongs to the engine, with consent.
install -D -m 0644 packaging/rpm/remotix-firewalld.xml %{buildroot}%{_prefix}/lib/firewalld/services/remotix.xml

# remotix-selinux: the module (the domain) and the port (portcon, in CIL)
install -D -m 0644 packaging/rpm/selinux/remotix.pp.bz2 %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/remotix.pp.bz2
install -D -m 0644 packaging/rpm/selinux/remotix_porta.cil %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/remotix_porta.cil

# The files the service generates by itself: declared %%ghost, so rpm knows them
# and uninstallation removes them (DIRECT origin, §6.6.4).  `[M]` T3 on
# Tumbleweed: without the two `.nostro` (the marks of `certificati.c:317,320`)
# /var/lib/remotix remained after `zypper remove`.
install -d -m 0700 %{buildroot}%{_sharedstatedir}/remotix/certificati
for f in pagina.pem pagina.key pagina.nostro sessione.pem sessione.key sessione.nostro; do
    touch %{buildroot}%{_sharedstatedir}/remotix/certificati/$f
done
touch %{buildroot}%{_sharedstatedir}/remotix/ban %{buildroot}%{_sharedstatedir}/remotix/ban.nuovo

# ⭐ `DECISIONI.md` §10.12 — the scriptlets switch NOTHING on (R40):
#   · no %%systemd_post / %%service_add_post: they would apply the machine's
#     «preset», and with an «enable *» preset the service would enable itself.
#     Switching on (`systemctl enable --now`) belongs to the engine;
#   · no GPU groups: the engine adds them (`aggiungi-utente-a-gruppo`),
#     with its log;
#   · no belts, no firewall, no `systemctl reload systemd-logind`.
#   systemd rereads new units by itself (systemd's file triggers).

%post
# Only the /var/lib/remotix directory (0700), which rpm already creates with %%dir: inert.
%tmpfiles_create remotix.conf

%preun
# On uninstallation: if the engine had switched it on, it is stopped and disabled
# (nothing stays enabled pointing to a file that no longer exists).
%if 0%{?suse_version}
%service_del_preun remotix.service
%else
%systemd_preun remotix.service
%endif

%postun
# On upgrade: `try-restart`, that is ONLY if it was already running (T2, §5.2, T7:
# the desktops survive, the new service finds them again, whoever is connected
# reattaches).  REMOTIX upgrades with the system (DECISIONI §10.23): dnf upgrade,
# zypper up.
%if 0%{?suse_version}
%service_del_postun remotix.service
%else
%systemd_postun_with_restart remotix.service
%endif

%posttrans
# After the transaction (remotix-install is in place too): the engine
# records the versions and says whether the installation is still certified
# (DECISIONI §10.12 point 4, §10.23).  ⛔ It never makes the transaction fail.
if [ -x /usr/bin/remotix-install ]; then
	/usr/bin/remotix-install post-upgrade || :
fi

%files
%license LICENSE.md
%license THIRD-PARTY-LICENSES
%dir %{_libexecdir}/remotix
%{_libexecdir}/remotix/remotix
%dir %{_datadir}/remotix
%{_datadir}/remotix/pagina.html
%{_datadir}/remotix/remotix.conf
%{_datadir}/remotix/incorporate.json
%dir %{_datadir}/remotix/cinture
%{_datadir}/remotix/cinture/50-remotix-niente-spegnimento.rules
%{_datadir}/remotix/cinture/remotix-tasti.conf
%{_datadir}/remotix/cinture/remotix-niente-sospensione.conf
%{_unitdir}/remotix.service
%{_tmpfilesdir}/remotix.conf
%if 0%{?suse_version}
# /usr/lib/pam.d belongs to the vendor: the administrator changes it with their own
# /etc/pam.d/remotix, which wins.  No %%config.
%{pamdir}/remotix
%else
%config(noreplace) %{pamdir}/remotix
%endif
%dir %{_sysconfdir}/remotix
%dir %{_sysconfdir}/remotix/remotix.conf.d
%config(noreplace) %{_sysconfdir}/remotix/utenti-negati
%{_datadir}/applications/org.kde.remotix.desktop
%if 0%{?suse_version}
%dir %{_prefix}/lib/firewalld
%dir %{_prefix}/lib/firewalld/services
%endif
%{_prefix}/lib/firewalld/services/remotix.xml
%ghost %dir %attr(0700,root,root) /run/remotix
%dir %attr(0700,root,root) %{_sharedstatedir}/remotix
%dir %attr(0700,root,root) %{_sharedstatedir}/remotix/certificati
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificati/pagina.pem
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/certificati/pagina.key
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificati/sessione.pem
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/certificati/sessione.key
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificati/pagina.nostro
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificati/sessione.nostro
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/ban
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/ban.nuovo

# ⭐ remotix-selinux: the scriptlets are the policy's (like cockpit-ws-selinux).
#   The module is just loaded: it switches nothing on (R40).  The relabelling
#   happens in %%posttrans, when the remotix files are in place too (in the same
#   transaction rpm writes them with the labels from BEFORE the module).
%pre selinux
%selinux_relabel_pre -s %{selinuxtype}

%post selinux
%selinux_modules_install -s %{selinuxtype} %{_datadir}/selinux/packages/%{selinuxtype}/remotix.pp.bz2 %{_datadir}/selinux/packages/%{selinuxtype}/remotix_porta.cil

%postun selinux
%selinux_modules_uninstall -s %{selinuxtype} remotix_porta remotix

%posttrans selinux
%selinux_relabel_post -s %{selinuxtype}

%files selinux
%{_datadir}/selinux/packages/%{selinuxtype}/remotix.pp.bz2
%{_datadir}/selinux/packages/%{selinuxtype}/remotix_porta.cil
%ghost %verify(not md5 size mode mtime) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/remotix
%ghost %verify(not md5 size mode mtime) %{_sharedstatedir}/selinux/%{selinuxtype}/active/modules/200/remotix_porta

%changelog
* Wed Sep 30 2026 nicfio <nicfio@gmail.com> - 0.17.0-1
- Phase 17, T6: the sshd PAM (D3), the remotix-selinux subpackage.
* Tue Sep 29 2026 nicfio <nicfio@gmail.com> - 0.17.0-1
- Phase 17, T3: the first native package for Fedora, Alma, Tumbleweed and Leap.
