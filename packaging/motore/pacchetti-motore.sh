#!/usr/bin/env bash
# pacchetti-motore.sh — the ENGINE packages, for the single REMOTIX package (the .run).
#
#     RX_VERSIONE=X.Y.Z RX_REVISIONE=R packaging/motore/pacchetti-motore.sh [output]
#                                                  (default costruzione-uscita/motore)
#
# Called by the release command (packaging/rilascio.sh), AFTER building the static engine
# with the release version (installatore/costruisci.sh with RX_VERSIONE). The engine is
# packaged as it is, for the three families:
#   · remotix-install_<V>-<R>_amd64.deb           (dpkg-deb: no library to compute)
#   · remotix-install-<V>-<R>.x86_64.rpm          (rpmbuild in the fedora:44 container)
#   · remotix-install-<V>-<R>-x86_64.pkg.tar.zst  (makepkg in the Arch container)
# The catalogue lives inside the engine (DECISIONI §10.21). The package stays on the machine after
# installation (status, uninstall); at every version change the scripts call
# `remotix-install post-upgrade`. No repository key: the repository no longer exists (§10.36).
#
# Environment: RX_VERSIONE (mandatory: the engine's version must match it), RX_REVISIONE (1), MOTORE
# (installatore/uscita/remotix-install).
# ⚠ No /tmp: on the laptop it is almost full.
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
U=${1:-$ALBERO/costruzione-uscita/motore}
V=${RX_VERSIONE:?RX_VERSIONE: the release version}
R=${RX_REVISIONE:-1}
MOTORE=${MOTORE:-$ALBERO/installatore/uscita/remotix-install}
M=$ALBERO/packaging/motore
mkdir -p "$U"
L=$U/.lavoro; rm -rf "$L"; mkdir -p "$L"
export TMPDIR=$L

vm=$("$MOTORE" version | awk '{print $1}')
[ "$vm" = "$V" ] || { echo "⛔ the engine $MOTORE says $vm, the release is $V"; exit 1; }
cp "$MOTORE" "$L/remotix-install"
cp "$M/README" "$ALBERO/THIRD-PARTY-LICENSES" "$L/"
echo "== the engine $V-$R ($(sha256sum "$L/remotix-install" | cut -c1-16)…)"

echo "== engine .deb"
D=$L/deb; mkdir -p "$D/DEBIAN" "$D/usr/bin" "$D/usr/share/remotix-install"
install -m 755 "$L/remotix-install" "$D/usr/bin/"
install -m 644 "$L/README" "$D/usr/share/remotix-install/"
install -D -m 644 "$L/THIRD-PARTY-LICENSES" "$D/usr/share/doc/remotix-install/THIRD-PARTY-LICENSES"
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
SOURCE_DATE_EPOCH=$(git -C "$ALBERO" log -1 --format=%ct) \
	dpkg-deb --root-owner-group -Zxz --build "$D" "$U/remotix-install_${V}-${R}_amd64.deb" >/dev/null

echo "== engine .rpm (fedora:44)"
P=$L/rpm; mkdir -p "$P/SOURCES" "$P/SPECS"
cp "$L/remotix-install" "$L/README" "$L/THIRD-PARTY-LICENSES" "$P/SOURCES/"
cp "$M/remotix-install.spec" "$P/SPECS/"
podman run --rm -v "$P:/lavoro:Z" registry.fedoraproject.org/fedora:44 sh -c "
	dnf -y -q install rpm-build systemd-rpm-macros >/dev/null 2>&1
	rpmbuild -bb --define '_topdir /lavoro' --define 'rx_versione $V' --define 'rx_rilascio $R' /lavoro/SPECS/remotix-install.spec" >"$U/rpmbuild.log" 2>&1 \
	|| { tail -20 "$U/rpmbuild.log"; exit 1; }
cp "$P"/RPMS/x86_64/remotix-install-*.rpm "$U/"

echo "== engine Arch package"
A=$L/arch; mkdir -p "$A"
cp "$L/remotix-install" "$L/README" "$L/THIRD-PARTY-LICENSES" "$M/PKGBUILD" "$M/remotix-install.install" "$A/"
podman run --rm --userns=keep-id -v "$A:/pkg" -w /pkg -e HOME=/pkg -e RX_VERSIONE="$V" -e RX_RILASCIO="$R" \
	-e SOURCE_DATE_EPOCH="$(git -C "$ALBERO" log -1 --format=%ct)" localhost/remotix-costruzione-arch \
	makepkg -f --noconfirm --nodeps >"$U/makepkg.log" 2>&1 || { tail -20 "$U/makepkg.log"; exit 1; }
cp "$A"/remotix-install-*-x86_64.pkg.tar.zst "$U/"

ls -l "$U"
