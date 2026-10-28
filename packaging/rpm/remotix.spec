# remotix.spec — the native REMOTIX package for the .rpm family.
#
#   Fedora 44 · Alma 10 (Rocky/RHEL 10 compatibili) · openSUSE Tumbleweed · Leap 16
#
# ⭐ ONE spec with %%if branches, as Cockpit does (`tools/cockpit.spec`):
#    0%%{?fedora} · 0%%{?rhel} · 0%%{?suse_version}.  `phases/17-the-installer.md`
#    §6.1-§6.4.  It is built INSIDE the container of each target
#    (`src/build-targets/Containerfile.<target>`) with `packaging/rpm/build-rpm.sh`.
#
# ⭐ The libraries are computed by rpmbuild reading the binary (the automatic «Requires»
#    by soname: libva, libopus, libssl, libpam, libpipewire,
#    libei, …): this is the
#    cure of `LESSONS.md` §2.5-bis.  Below, only what rpm CANNOT see is written
#    BY HAND, because it is loaded or executed at run time: the
#    compositor for XFCE/LXQt, wlr-randr, Xwayland, the Plasma wallpaper, the
#    VA-API drivers.  (OpenSSL >= 3.5 it sees on its own: `libssl.so.3(OPENSSL_3.5.0)`.)
#
# ⭐ `DECISIONS.md` §10.12 — the package ships only INERT pieces (program,
#    page, disabled unit, PAM, /etc/remotix, the belts OFF in
#    /usr/share/remotix/belts/, the firewalld definition).  It neither enables nor starts the service, and touches no groups, belts or
#    firewall: the engine adds the groups, with consent and in its log (R40); the
#    belts and the firewall are the administrator's (DECISIONS §10.36).
#    ⛔ No guard that prevents the service from starting (no
#    ExecCondition, no ConditionPathExists on a mark): there are TWO ways,
#    the installer or the source by hand; `remotix state` will only say, for
#    information, whether the installation is certified.
#
# ⛔ Never in the package (§6.4, R14): test users, the benches' `sudoers.d`,
#    `gpu-udev.sh`, `restart-*.sh`, `ld.so.conf.d`, `provision.sh`.
# ⛔ The package NEVER pulls in a desktop (`DECISIONS.md` §10.7: without a
#    desktop the engine installs it): dependencies tied to a desktop are
#    CONDITIONAL, `(X if <desktop session>)`.
# ⛔ The package NEVER adds repositories (RPM Fusion, Packman, EPEL): §4.2
#    rule 2 and D5.  The installation engine will do it, with consent.

# ⭐ DECISIONS-11.md §11.50, PHASE F — the network side's user, directories, unit, SELinux domain and the 1.0 → 1.5 move.
#    ⭐ ON by default (decided 25 Oct 2026): `rpmbuild --without split` (build-rpm.sh: RX_SPLIT=0) builds the single-process package.
%bcond_without split

%global ngtcp2_ver  1.25.0
%global nghttp3_ver 1.18.0
# ⭐ PIANO «Correzione B»: OUR labwc, to host the nested KWin >= 6.5 — Fedora 44, RHEL / Alma 10 and
#   Tumbleweed (not Leap 16: KWin 6.4).  labwc and wlroots (static, patched) as in
#   packaging/labwc-ospite/VERSIONS (%%build stops if they differ).  On Alma it REPLACES the
#   labwc 0.8.4 of DECISIONI §10.43.
%global labwc_ver    0.9.3
%global wlroots_ver  0.19.2
%if 0%{?fedora} || 0%{?rhel} || 0%{?suse_version} >= 1699
%global labwc_ospite 1
%endif

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
# Version and release are given by the release command (packaging/release.sh) through
# build-rpm.sh: RX_VERSION (--define "rx_version X.Y.Z") and RX_REVISION
# (--define "rx_release N"); defaults 1.0.0 and 1.
Version:        %{?rx_version}%{!?rx_version:1.0.0}
Release:        %{?rx_release}%{!?rx_release:1}%{?dist}
Summary:        This machine's desktop in the browser
# Our own text, not a standard one (DECISIONI §10.39): free for personal and non-profit use,
# source readable, no modifications, no redistribution. Its text is LICENSE.md.
%if 0%{?labwc_ospite}
# ⭐ The package also carries OUR labwc (/usr/lib/remotix/labwc), a separate program under its own
#   licence (GPL-2.0-only; two files LGPL-2.0-or-later) with wlroots (MIT) linked in statically;
#   REMOTIX's terms do not apply to it (LICENSE.md §8).
License:        LicenseRef-REMOTIX AND GPL-2.0-only AND LGPL-2.0-or-later AND MIT
%else
License:        LicenseRef-REMOTIX
%endif
URL:            https://github.com/nic-fio/REMOTIX
# An archive of src/, benches/rcp/ (the twin copy that `make` compares) and
# packaging/rpm/, made by `build-rpm.sh`.
Source0:        %{name}-%{version}.tar.gz
%if 0%{?labwc_ospite}
# ⭐ OUR labwc: the two upstream tarballs, unmodified, pinned and verified by packaging/labwc-ospite/
#   (fetch.sh, VERSIONS; the patch and build.sh are in Source0); the source rpm carries them.
Source1:        https://github.com/labwc/labwc/archive/refs/tags/%{labwc_ver}.tar.gz#/labwc-%{labwc_ver}.tar.gz
Source2:        https://gitlab.freedesktop.org/wlroots/wlroots/-/releases/%{wlroots_ver}/downloads/wlroots-%{wlroots_ver}.tar.gz
%endif

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
# ⭐ Phase 18 (`phases/18-without-ffmpeg.md`): no ffmpeg; libopus (the audio).
# ⛔ Phase 19 (1 Oct 2026, `DECISIONS.md` §10.27): OpenH264 and SVT-AV1, the software
#   fallback, are OUT — and with them the Cisco OpenH264 repository.
BuildRequires:  pkgconfig(opus)
# ⭐ 15 Oct 2026 (`DECISIONS-11.md` §11.44): zlib, the login page sent gzip-compressed.
#   (Fedora/Alma: zlib-ng-compat-devel; openSUSE: zlib-devel.)
BuildRequires:  pkgconfig(zlib)
# ⛔ no libyuv: the colour conversion is ours (`src/colors709.c`, phases/18 §1);
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
%if 0%{?labwc_ospite}
# ⭐ OUR labwc (packaging/labwc-ospite/build.sh): what labwc 0.9.3 needs, minus what the options
#   switch off (Xwayland/xcb, SVG, icons/libsfdo, man pages), plus what wlroots 0.19.2 needs for
#   the drm + libinput backends and the gles2/pixman renderers.  wlroots is built from the
#   tarball, static: NO BuildRequires on the distribution's wlroots.
BuildRequires:  meson >= 0.59.0
BuildRequires:  patch
BuildRequires:  pkgconfig(hwdata)
BuildRequires:  pkgconfig(wayland-server)
BuildRequires:  pkgconfig(wayland-protocols)
BuildRequires:  pkgconfig(cairo)
BuildRequires:  pkgconfig(glib-2.0)
BuildRequires:  pkgconfig(pangocairo)
BuildRequires:  pkgconfig(libinput) >= 1.14
BuildRequires:  pkgconfig(libxml-2.0)
BuildRequires:  pkgconfig(pixman-1)
BuildRequires:  pkgconfig(libpng16)
BuildRequires:  pkgconfig(libdrm)
BuildRequires:  pkgconfig(egl)
BuildRequires:  pkgconfig(glesv2)
BuildRequires:  pkgconfig(libseat)
BuildRequires:  pkgconfig(libudev)
BuildRequires:  pkgconfig(libdisplay-info)
BuildRequires:  pkgconfig(xkbcommon)
%endif
# ⚠ ngtcp2 >= 1.25.0 and nghttp3: they are NOT a BuildRequires, because almost no
#   distribution has them (§6.3).  The container builds them, STATIC ONLY, in
#   /usr/local/lib (`src/build-targets/quic-static.sh`); %%build checks that they are
#   there and that the version is the one declared below.
# ⭐ D2 CLOSED (`DECISIONS.md` §10.6): ngtcp2 and nghttp3 INSIDE the binary, with the
#   security updates on us — whatever is missing or too
#   old REMOTIX brings, except patented codecs and desktops.
Provides:       bundled(ngtcp2) = %{ngtcp2_ver}
Provides:       bundled(nghttp3) = %{nghttp3_ver}

# ⭐ SELinux (T6, `DECISIONS.md` §10.18): the REMOTIX PAM is sshd's, with
#    `pam_selinux`; the transition to the user's context is allowed by the REMOTIX
#    module, in the remotix-selinux subpackage (like cockpit-ws-selinux).  The package
#    manager pulls it in ONLY where the «targeted» policy exists: Fedora,
#    Alma, openSUSE (Tumbleweed and Leap 16 are enforcing by default).
%global selinuxtype targeted
%if %{with split}
# the system user `remotix` (remotix.sysusers), created in %%pre — before rpm lays the files it owns.  openSUSE: its own
# macros (sysuser-tools); Fedora/Alma: systemd-sysusers from %%pre.
%if 0%{?suse_version}
BuildRequires:  sysuser-tools
%sysusers_requires
%else
Requires(pre):  /usr/bin/systemd-sysusers
%endif
%endif
BuildRequires:  selinux-policy-devel
BuildRequires:  bzip2
Requires:       (%{name}-selinux = %{version}-%{release} if selinux-policy-%{selinuxtype})

# The PipeWire DAEMON + wireplumber: GNOME/KDE video capture goes through PipeWire
# (mutter/kwin screencast) and so does the audio of EVERY desktop (sound.c); rpm sees the LIBRARY
# (libpipewire) but not the daemon.  The desktop groups bring it, but minimal installations
# do not (T10, 30 Sep: openSUSE GNOME from the Minimal-VM image WITHOUT pipewire ⇒ mutter does not
# reach the screencast, «Error connecting to the screencast service», and the desktop never arrives).
Requires:       pipewire
Requires:       wireplumber

%if 0%{?fedora} || 0%{?rhel}
# The firewalld service is DEFINED in the firewalld-filesystem directory (no
# daemon, no rules): opening it belongs to the administrator (DECISIONS §10.36).
Requires:       firewalld-filesystem
%endif

%if 0%{?fedora}
# XFCE and LXQt run under labwc (REMOTIX starts it; no default group brings it,
# §4.6).  xfce4-session 4.20 is X11: under labwc it needs Xwayland.  XFCE and LXQt: the
# monitor measurement goes through wlr-randr (`measured_primary()`, XFCE too since 5 Oct).  CONDITIONAL dependencies:
# only if that desktop is present.
Requires:       (labwc if xfce4-session)
Requires:       (labwc if lxqt-session)
# ⭐ 11 Oct 2026 (DECISIONI §10.40): KWin is born nested in a screenless labwc,
# so the KDE desktop takes the window's size at reattach.
Requires:       (labwc if plasma-workspace)
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
# ⭐ For KDE the package carries OUR labwc, /usr/lib/remotix/labwc (wlroots linked in statically:
#   no dependency on EPEL's wlroots; rpm computes the sonames of the other libraries).
#   ⇒ KDE resizes at reattach here too (DECISIONI §10.40): Alma is no longer an exception.
# ⛔ RHEL 10 Mesa has no VA-API and EPEL lacks the Intel driver (§4.2): GPU
#   encoding exists only with third-party repositories.
%endif

%if 0%{?suse_version}
Requires:       (labwc if xfce4-session)
Requires:       (labwc if lxqt-session)
# ⭐ 11 Oct 2026 (DECISIONI §10.40): KWin nested in a screenless labwc.
Requires:       (labwc if plasma6-workspace)
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
    pkg-config --exists $l || { echo "⛔ $l: missing (it is built in the containers of src/build-targets/)"; exit 1; }
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
make clean >/dev/null
%if 0%{?labwc_ospite}
# ⭐ kwin.c execs OUR labwc at this exact path (build-time choice, not a switch)
make %{?_smp_mflags} all LABWC=%{_prefix}/lib/remotix/labwc
%else
make %{?_smp_mflags} all
%endif
cd ..

%if 0%{?labwc_ospite}
# ⭐ OUR labwc: labwc %%{labwc_ver} + wlroots %%{wlroots_ver} (patched, static), from Source1/Source2 by
#    packaging/labwc-ospite/build.sh (which checks the sha256 of both against VERSIONS and applies the
#    patch).  Distribution flags, PIE.
test "$(awk '$1 == "labwc" { print $2 }' packaging/labwc-ospite/VERSIONS)" = %{labwc_ver} || \
    { echo "⛔ packaging/labwc-ospite/VERSIONS: labwc is not %{labwc_ver}"; exit 1; }
test "$(awk '$1 == "wlroots" { print $2 }' packaging/labwc-ospite/VERSIONS)" = %{wlroots_ver} || \
    { echo "⛔ packaging/labwc-ospite/VERSIONS: wlroots is not %{wlroots_ver}"; exit 1; }
CFLAGS="%{optflags}" LDFLAGS="%{?build_ldflags}" JOBS=%{?_smp_build_ncpus}%{!?_smp_build_ncpus:2} \
    BUILD_DIR=$PWD/labwc-build packaging/labwc-ospite/build.sh "$(dirname %{SOURCE1})" $PWD/labwc-root
# no libwlroots: it is inside
if ldd labwc-root/usr/lib/remotix/labwc | grep -q wlroots; then echo "⛔ our labwc is linked to a libwlroots"; exit 1; fi
%endif

# The SELinux module, with the policy interfaces of THIS distribution.
# ⚠ `--define "rx_selinux_permissive 1"` (build-rpm.sh: RX_SELINUX_PERMISSIVE=1)
#   builds the module with the domain in «permissive»: to MEASURE the denials of a
#   whole session in a single run.  ⛔ Never in a published package.
cd packaging/rpm/selinux
%if %{with split}
# PHASE F: the module with the network side's domain (remotix_net_t) and the net/ labels
cp remotix.te.split remotix.te
cp remotix.fc.split remotix.fc
%{?rx_selinux_permissive:printf 'permissive remotix_t;\npermissive remotix_net_t;\n' >> remotix.te}
%else
%{?rx_selinux_permissive:echo 'permissive remotix_t;' >> remotix.te}
%endif
make -f %{_datadir}/selinux/devel/Makefile remotix.pp
bzip2 -9 remotix.pp
cd ../../..

%install
install -D -m 0755 src/remotix %{buildroot}%{_libexecdir}/remotix/remotix
%if 0%{?labwc_ospite}
# ⛔ our labwc, private: not on PATH, no clash with the distribution's labwc
install -D -m 0755 labwc-root/usr/lib/remotix/labwc %{buildroot}%{_prefix}/lib/remotix/labwc
%endif
install -D -m 0644 src/page.html %{buildroot}%{_datadir}/remotix/page.html
# The DEFAULTS (port, options): owned by the package, an upgrade rewrites them.
# The administrator's choices in /etc/remotix/remotix.conf.d/*.conf (they win).
install -D -m 0644 packaging/rpm/remotix.conf %{buildroot}%{_datadir}/remotix/remotix.conf
# R24 (T8): the versions of the LINKED static libraries (pkg-config in the build
# container), for the archive SBOM.
printf '{"format":"remotix-linked/1","ngtcp2":"%s","nghttp3":"%s","source":"pkg-config of the linked .a files"}\n' \
    "$(pkg-config --modversion libngtcp2)" "$(pkg-config --modversion libnghttp3)" \
    > %{buildroot}%{_datadir}/remotix/linked.json
install -D -m 0644 packaging/rpm/remotix.service %{buildroot}%{_unitdir}/remotix.service
install -D -m 0644 packaging/rpm/remotix.tmpfiles %{buildroot}%{_tmpfilesdir}/remotix.conf
%if %{with split}
# PHASE F (§11.50): the split's unit and directories replace the two above; the user and the 1.0 → 1.5 move come with it
install -D -m 0644 packaging/rpm/remotix.service.split %{buildroot}%{_unitdir}/remotix.service
install -D -m 0644 packaging/rpm/remotix.tmpfiles.split %{buildroot}%{_tmpfilesdir}/remotix.conf
install -D -m 0755 packaging/rpm/remotix-net-move %{buildroot}%{_libexecdir}/remotix/remotix-net-move
install -D -m 0644 packaging/rpm/remotix.sysusers %{buildroot}%{_sysusersdir}/remotix.conf
%if 0%{?suse_version}
# openSUSE's way for a system user (sysuser-tools): remotix.pre, used by %%pre -f
%sysusers_generate_pre packaging/rpm/remotix.sysusers remotix remotix.conf
%endif
%endif
install -D -m 0644 src/%{pamsorgente} %{buildroot}%{pamdir}/remotix

# /etc/remotix: who is excluded (the PAM has onerr=fail: without the file nobody
# gets in, so the file comes with the package and is left alone if changed), and the
# directory of the administrator's choices (empty: the format belongs to the engine, T4).
install -d -m 0755 %{buildroot}%{_sysconfdir}/remotix/remotix.conf.d
printf 'root\n' > %{buildroot}%{_sysconfdir}/remotix/denied-users
chmod 0644 %{buildroot}%{_sysconfdir}/remotix/denied-users

# The KWin capture permission (`zkde_screencast_unstable_v1`): KWin looks for it in
# XDG_DATA_DIRS.  The package ships it and the program only checks it at start-up
# (`src/kwin.c`, `kwin_check_permission()`, codes RX-KDE-001..003): it never writes it.
# The content is byte-for-byte identical to the .deb one (Arch's differs only in Exec=).
install -D -m 0644 packaging/rpm/org.kde.remotix.desktop %{buildroot}%{_datadir}/applications/org.kde.remotix.desktop

# ⭐ `DECISIONS.md` §10.12 — the installer is the only way: the three belts of
#   §4.7 (no power-off, no suspend, the keys do not power off) arrive
#   OFF, outside the paths polkit and systemd read.  The engine does NOT mount
#   them (DECISIONS §10.36): the administrator does, if wanted; the paths they would go to are the VENDOR ones
#   (/usr/share/polkit-1/rules.d/50-…, /usr/lib/systemd/{logind,sleep}.conf.d/),
#   never /etc: an administrator's file with the same name in /etc wins (R34).
install -D -m 0644 src/remotix-no-poweroff.rules %{buildroot}%{_datadir}/polkit-1/rules.d/50-remotix-no-poweroff.rules
install -D -m 0644 src/remotix-power-keys.conf %{buildroot}%{_datadir}/remotix/belts/remotix-power-keys.conf
install -D -m 0644 packaging/rpm/remotix-no-suspend.conf %{buildroot}%{_datadir}/remotix/belts/remotix-no-suspend.conf

# firewalld: the «remotix» service DEFINED, not opened (D6, §10.12): the file
# makes a name known to firewalld and changes no zone.  Opening it
# (`firewall-cmd --permanent --add-service=remotix`) belongs to the administrator (DECISIONS §10.36).
install -D -m 0644 packaging/rpm/remotix-firewalld.xml %{buildroot}%{_prefix}/lib/firewalld/services/remotix.xml

# remotix-selinux: the module (the domain) and the port (portcon, in CIL)
install -D -m 0644 packaging/rpm/selinux/remotix.pp.bz2 %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/remotix.pp.bz2
install -D -m 0644 packaging/rpm/selinux/remotix_portcon.cil %{buildroot}%{_datadir}/selinux/packages/%{selinuxtype}/remotix_porta.cil

# The files the service generates by itself: declared %%ghost, so rpm knows them
# and uninstallation removes them (DIRECT origin, §6.6.4).  `[M]` T3 on
# Tumbleweed: without the two `.ours` (the marks of `certificates.c:317,320`)
# /var/lib/remotix remained after `zypper remove`.  ⭐ 1.5: `quic-secret` too (the QUIC
# Retry/Stateless-Reset secret, written at every start by transport_keep_secret(),
# transport.c) and `log-secret` (the key of the log tags of unknown user names, made by
# rcp.c next to it, 0600): `[M]` T10 on 15 Oct 2026 fedora44/alma10/tumbleweed/leap16 found
# quic-secret left behind, with certificates/ and /var/lib/remotix, after `uninstall --purge`.
%if %{with split}
# PHASE F (§11.50): they live in net/, the network side's, owned by remotix
install -d -m 0700 %{buildroot}%{_sharedstatedir}/remotix/net/certificates
for f in page.pem page.key page.ours session.pem session.key session.ours quic-secret log-secret log-secret.new; do
    touch %{buildroot}%{_sharedstatedir}/remotix/net/certificates/$f
done
touch %{buildroot}%{_sharedstatedir}/remotix/net/ban %{buildroot}%{_sharedstatedir}/remotix/net/ban.new
%else
install -d -m 0700 %{buildroot}%{_sharedstatedir}/remotix/certificates
for f in page.pem page.key page.ours session.pem session.key session.ours quic-secret log-secret log-secret.new; do
    touch %{buildroot}%{_sharedstatedir}/remotix/certificates/$f
done
touch %{buildroot}%{_sharedstatedir}/remotix/ban %{buildroot}%{_sharedstatedir}/remotix/ban.new
%endif
# 1.5 (DECISIONS-11 §11.4): the record of the card grants (render_grant.c) and its temporary file
touch %{buildroot}%{_sharedstatedir}/remotix/render-grants %{buildroot}%{_sharedstatedir}/remotix/render-grants.new

# ⭐ `DECISIONS.md` §10.12 — the scriptlets switch NOTHING on (R40):
#   · no %%systemd_post / %%service_add_post: they would apply the machine's
#     «preset», and with an «enable *» preset the service would enable itself.
#     Switching on (`systemctl enable --now`) belongs to the engine;
#   · no GPU groups: the engine adds them (`aggiungi-utente-a-gruppo`),
#     with its log;
#   · no belts, no firewall, no `systemctl reload systemd-logind`.
#   systemd rereads new units by itself (systemd's file triggers).

%if %{with split}
%if 0%{?suse_version}
%pre -f remotix.pre
%else
%pre
# PHASE F (§11.50): the system user, before the files it owns are laid down.
echo 'u remotix - "REMOTIX network side" / /usr/sbin/nologin' | \
	systemd-sysusers --replace=%{_sysusersdir}/remotix.conf - || :
%endif
%endif

%post
# ⭐ PHASE F (§11.50) — the 1.0 → 1.5 move of certificates/ and ban into /var/lib/remotix/net, given to remotix, BEFORE the
#   tmpfiles line and the %%postun try-restart.  INERT unless the package carries remotix-net-move (a `--with split` build).
#   ⛔ A failure is said, never fails the transaction.
if [ -x %{_libexecdir}/remotix/remotix-net-move ]; then
    %{_libexecdir}/remotix/remotix-net-move || echo "remotix: ⚠ the move into /var/lib/remotix/net is incomplete" >&2
fi
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
# ⭐ PHASE F (§11.50): the network side's files go back to the 1.0 paths (`remotix-net-move --back`) on a DOWNGRADE ($1 == 1
#   and the other installed version is LOWER than this one) — never on an upgrade, and ⛔ NOT on the last removal ($1 == 0):
#   `[M]` T10 of 26 Oct 2026 (tumbleweed, leap16, 17-t10 «box»): moved back, certificates/ (private keys included) and ban
#   landed on the 1.0 paths, which a split build does not declare %%ghost, and stayed after `uninstall --purge` — 1.0 removed
#   them (they were its %%ghost).  Left in net/, they are this package's %%ghost and rpm removes them, as 1.0 did.
#   rpm runs the new package's %%post BEFORE this one: for a downgrade that is the 1.0 %%post, which moves nothing.
#   INERT unless the package carries remotix-net-move (a `--with split` build).  ⛔ A failure is said, never fails the
#   transaction.
if [ -x %{_libexecdir}/remotix/remotix-net-move ]; then
    rx_back=
    if [ "$1" -ge 1 ]; then
        rx_other=$(rpm -q --qf '%%{VERSION}-%%{RELEASE}\n' remotix 2>/dev/null | grep -vx '%{version}-%{release}' | head -1)
        if [ -n "$rx_other" ] && [ "$(printf '%%s\n%%s\n' "$rx_other" '%{version}-%{release}' | sort -V | head -1)" = "$rx_other" ]; then
            rx_back=1
        fi
    fi
    if [ -n "$rx_back" ]; then
        %{_libexecdir}/remotix/remotix-net-move --back || echo "remotix: ⚠ the move of /var/lib/remotix/net back is incomplete" >&2
    fi
fi
# ⭐ R-1 of the page audit (25 Oct 2026): on the LAST removal ($1 == 0) the card grants (ACL on /dev/dri/renderD*,
#   DECISIONS-11 §11.4) are taken back with the service already stopped (the macro above), BEFORE the binary and the %%ghost
#   record go.  rpm removes the %%ghost record anyway, so on a failure the ACLs are said to vanish at the next boot.  Never fails
#   the transaction.  Not on upgrade (the new version's start-up sweeps).
# BEGIN drop-render-grants
if [ "$1" -eq 0 ] && [ -x %{_libexecdir}/remotix/remotix ]; then
    %{_libexecdir}/remotix/remotix --drop-render-grants || echo "remotix: ⚠ the card grants (ACL on /dev/dri/renderD*) could not all be taken back: they vanish at the next boot" >&2
fi
# END drop-render-grants

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
# Last removal only ($1 == 0).  The service writes its secrets through a temporary file
# (quic-secret.tmp.<pid>, log-secret.new) and renames it: a crash or a power cut between the
# write and the rename leaves the temporary one, which rpm does not know (the .new is %%ghost,
# the .tmp.<pid> has a name that changes).  Without this, certificates/ and /var/lib/remotix
# would stay.  rmdir only removes a folder that is EMPTY: nothing the administrator put there goes.
if [ "$1" -eq 0 ]; then
    rm -f %{_sharedstatedir}/remotix/certificates/quic-secret.tmp.* %{_sharedstatedir}/remotix/net/certificates/quic-secret.tmp.*
    rmdir %{_sharedstatedir}/remotix/net/certificates %{_sharedstatedir}/remotix/net 2>/dev/null || :
    rmdir %{_sharedstatedir}/remotix/certificates 2>/dev/null || :
    rmdir %{_sharedstatedir}/remotix 2>/dev/null || :
fi

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
%if 0%{?labwc_ospite}
%dir %{_prefix}/lib/remotix
%{_prefix}/lib/remotix/labwc
%endif
%dir %{_datadir}/remotix
%{_datadir}/remotix/page.html
%{_datadir}/remotix/remotix.conf
%{_datadir}/remotix/linked.json
%dir %{_datadir}/remotix/belts
%{_datadir}/polkit-1/rules.d/50-remotix-no-poweroff.rules
%{_datadir}/remotix/belts/remotix-power-keys.conf
%{_datadir}/remotix/belts/remotix-no-suspend.conf
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
%config(noreplace) %{_sysconfdir}/remotix/denied-users
%{_datadir}/applications/org.kde.remotix.desktop
%if 0%{?suse_version}
%dir %{_prefix}/lib/firewalld
%dir %{_prefix}/lib/firewalld/services
%endif
%{_prefix}/lib/firewalld/services/remotix.xml
%if %{with split}
# ⛔ PHASE F (§11.50): rpm re-applies these owners and modes at EVERY upgrade, so they must be the ones remotix-net-move and
#    tmpfiles set: a root %%attr here would undo the move.  /var/lib/remotix stays root's (0755: remotix reaches net/ through it).
%{_sysusersdir}/remotix.conf
%{_libexecdir}/remotix/remotix-net-move
%ghost %dir %attr(0755,root,root) /run/remotix
%ghost %dir %attr(0700,remotix,remotix) /run/remotix/net
%dir %attr(0755,root,root) %{_sharedstatedir}/remotix
%dir %attr(0700,remotix,remotix) %{_sharedstatedir}/remotix/net
%dir %attr(0700,remotix,remotix) %{_sharedstatedir}/remotix/net/certificates
%ghost %attr(0644,remotix,remotix) %{_sharedstatedir}/remotix/net/certificates/page.pem
%ghost %attr(0600,remotix,remotix) %{_sharedstatedir}/remotix/net/certificates/page.key
%ghost %attr(0644,remotix,remotix) %{_sharedstatedir}/remotix/net/certificates/session.pem
%ghost %attr(0600,remotix,remotix) %{_sharedstatedir}/remotix/net/certificates/session.key
%ghost %attr(0644,remotix,remotix) %{_sharedstatedir}/remotix/net/certificates/page.ours
%ghost %attr(0644,remotix,remotix) %{_sharedstatedir}/remotix/net/certificates/session.ours
%ghost %attr(0600,remotix,remotix) %{_sharedstatedir}/remotix/net/certificates/quic-secret
%ghost %attr(0600,remotix,remotix) %{_sharedstatedir}/remotix/net/certificates/log-secret
%ghost %attr(0600,remotix,remotix) %{_sharedstatedir}/remotix/net/certificates/log-secret.new
%ghost %attr(0600,remotix,remotix) %{_sharedstatedir}/remotix/net/ban
%ghost %attr(0600,remotix,remotix) %{_sharedstatedir}/remotix/net/ban.new
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/render-grants
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/render-grants.new
%else
%ghost %dir %attr(0700,root,root) /run/remotix
%dir %attr(0700,root,root) %{_sharedstatedir}/remotix
%dir %attr(0700,root,root) %{_sharedstatedir}/remotix/certificates
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificates/page.pem
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/certificates/page.key
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificates/session.pem
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/certificates/session.key
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificates/page.ours
%ghost %attr(0644,root,root) %{_sharedstatedir}/remotix/certificates/session.ours
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/certificates/quic-secret
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/certificates/log-secret
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/certificates/log-secret.new
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/ban
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/ban.new
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/render-grants
%ghost %attr(0600,root,root) %{_sharedstatedir}/remotix/render-grants.new
%endif

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
* Sun Oct 11 2026 nicfio <nicfio@gmail.com> - 1.0.0-1
- 1.0.0: first public release.
* Wed Sep 30 2026 nicfio <nicfio@gmail.com> - 0.17.0-1
- Phase 17, T6: the sshd PAM (D3), the remotix-selinux subpackage.
* Tue Sep 29 2026 nicfio <nicfio@gmail.com> - 0.17.0-1
- Phase 17, T3: the first native package for Fedora, Alma, Tumbleweed and Leap.
