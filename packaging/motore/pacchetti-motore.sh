#!/usr/bin/env bash
# pacchetti-motore.sh — the ENGINE packages, for the single REMOTIX package (the .run).
#
#     RX_VERSION=X.Y.Z RX_REVISION=R packaging/motore/pacchetti-motore.sh [output]
#                                                  (default costruzione-uscita/motore)
#
# Called by the release command (packaging/rilascio.sh), AFTER building the static engine
# with the release version (installatore/costruisci.sh with RX_VERSION). The engine is
# packaged as it is, for the three families:
#   · remotix-install_<V>-<R>_amd64.deb           (dpkg-deb: no library to compute)
#   · remotix-install-<V>-<R>.x86_64.rpm          (rpmbuild in the fedora:44 container)
#   · remotix-install-<V>-<R>-x86_64.pkg.tar.zst  (makepkg in the Arch container)
# The catalogue lives inside the engine (DECISIONI §10.21). The package stays on the machine after
# installation (status, uninstall); at every version change the scripts call
# `remotix-install post-upgrade`. No repository key: the repository no longer exists (§10.36).
#
# Environment: RX_VERSION (mandatory: the engine's version must match it), RX_REVISION (1), ENGINE
# (installatore/out_dir/remotix-install).
# ⚠ No /tmp: on the laptop it is almost full.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
U=${1:-$TREE/costruzione-uscita/motore}
V=${RX_VERSION:?RX_VERSION: the release version}
R=${RX_REVISION:-1}
ENGINE=${ENGINE:-$TREE/installatore/out_dir/remotix-install}
M=$TREE/packaging/motore
mkdir -p "$U"
L=$U/.work; rm -rf "$L"; mkdir -p "$L"
export TMPDIR=$L

vm=$("$ENGINE" version | awk '{print $1}')
[ "$vm" = "$V" ] || { echo "⛔ the engine $ENGINE says $vm, the release is $V"; exit 1; }
cp "$ENGINE" "$L/remotix-install"
cp "$M/README" "$TREE/THIRD-PARTY-LICENSES" "$TREE/LICENSE.md" "$L/"
echo "== the engine $V-$R ($(sha256sum "$L/remotix-install" | cut -c1-16)…)"

echo "== engine .deb"
D=$L/deb; mkdir -p "$D/DEBIAN" "$D/usr/bin" "$D/usr/share/remotix-install"
install -m 755 "$L/remotix-install" "$D/usr/bin/"
install -m 644 "$L/README" "$D/usr/share/remotix-install/"
install -D -m 644 "$L/THIRD-PARTY-LICENSES" "$D/usr/share/doc/remotix-install/THIRD-PARTY-LICENSES"
# the licence (DECISIONI §10.39) in the Debian place, DEP-5 like the product's debian/copyright
{
	cat <<EOF
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: remotix-install
Upstream-Contact: Nicola Fiorillo <remotix@nicfio.it>
Source: https://remotix.nicfio.it
Comment: The licences of the third-party components incorporated in the engine
 (Go modules, Go runtime), with their full texts:
 /usr/share/doc/remotix-install/THIRD-PARTY-LICENSES.

Files: *
Copyright: 2026 Nicola Fiorillo
License: LicenseRef-REMOTIX
EOF
	sed -e 's/^$/./' -e 's/^/ /' "$L/LICENSE.md"
} >"$L/copyright"
install -m 644 "$L/copyright" "$D/usr/share/doc/remotix-install/"
cat >"$D/DEBIAN/control" <<EOF
Package: remotix-install
Version: $V-$R
Architecture: amd64
Maintainer: nicfio <nicfio@gmail.com>
Section: admin
Priority: optional
Depends: systemd
Description: the REMOTIX installation engine
 Installs, checks, certifies and uninstalls REMOTIX. It carries inside it the
 catalogue of supported combinations, which is updated with this package.
 REMOTIX updates with the system (apt upgrade): no timer.
EOF
cat >"$D/DEBIAN/postinst" <<'EOF'
#!/bin/sh
# after an upgrade: the engine records the versions and says whether the installation is still certified
# (DECISIONI §10.12 point 4, §10.23). It never makes apt fail.
set -e
if [ "$1" = configure ] && [ -n "${2:-}" ]; then
	/usr/bin/remotix-install post-upgrade || true
fi
exit 0
EOF
chmod 755 "$D/DEBIAN/postinst"
SOURCE_DATE_EPOCH=$(git -C "$TREE" log -1 --format=%ct) \
	dpkg-deb --root-owner-group -Zxz --build "$D" "$U/remotix-install_${V}-${R}_amd64.deb" >/dev/null

echo "== engine .rpm (fedora:44)"
P=$L/rpm; mkdir -p "$P/SOURCES" "$P/SPECS"
cp "$L/remotix-install" "$L/README" "$L/THIRD-PARTY-LICENSES" "$L/LICENSE.md" "$P/SOURCES/"
cp "$M/remotix-install.spec" "$P/SPECS/"
podman run --rm -v "$P:/work:Z" registry.fedoraproject.org/fedora:44 sh -c "
	dnf -y -q install rpm-build systemd-rpm-macros >/dev/null 2>&1
	rpmbuild -bb --define '_topdir /work' --define 'rx_version $V' --define 'rx_release $R' /work/SPECS/remotix-install.spec" >"$U/rpmbuild.log" 2>&1 \
	|| { tail -20 "$U/rpmbuild.log"; exit 1; }
cp "$P"/RPMS/x86_64/remotix-install-*.rpm "$U/"

echo "== engine Arch package"
A=$L/arch; mkdir -p "$A"
cp "$L/remotix-install" "$L/README" "$L/THIRD-PARTY-LICENSES" "$L/LICENSE.md" "$M/PKGBUILD" "$M/remotix-install.install" "$A/"
podman run --rm --userns=keep-id -v "$A:/pkg" -w /pkg -e HOME=/pkg -e RX_VERSION="$V" -e RX_RELEASE="$R" \
	-e SOURCE_DATE_EPOCH="$(git -C "$TREE" log -1 --format=%ct)" localhost/remotix-costruzione-arch \
	makepkg -f --noconfirm --nodeps >"$U/makepkg.log" 2>&1 || { tail -20 "$U/makepkg.log"; exit 1; }
cp "$A"/remotix-install-*-x86_64.pkg.tar.zst "$U/"

ls -l "$U"
