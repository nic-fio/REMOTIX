#!/usr/bin/env bash
# costruisci.sh — the REMOTIX Arch package, from the repository, in the container.
#
#     packaging/arch/costruisci.sh [commit]        (default: HEAD)
#
# 0. First: the Arch, .deb and .rpm units (and defaults) are equivalent.
# 1. PKGBUILD, remotix.install and the tarball (src/, banchi/rcp/, packaging/arch/)
#    come out of the SAME commit (`git archive`): what is not committed does not
#    get in, and the package says which commit it comes from (sorgente.txt).
# 2. makepkg inside `localhost/remotix-costruzione-arch`
#    (src/costruzione/Contenitore.arch; built by costruisci-tutti.sh arch),
#    as a user, without -s: the build dependencies are already there.
# 3. namcap on PKGBUILD and package, in a throwaway container (namcap.txt).
# 4. R14: the package's file list against the bench blacklist.
#
# Output in $OUTPUT (default costruzione-uscita/pacchetto-arch, ignored
# by git).  ⚠ No /tmp: on the laptop it is almost full.
set -euo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
COMMIT=$(git -C "$TREE" rev-parse "${1:-HEAD}")
OUTPUT=${OUTPUT:-$TREE/costruzione-uscita/pacchetto-arch}
IMAGE=${IMAGE:-localhost/remotix-costruzione-arch}
WORKDIR="$OUTPUT/.lavoro"
PKGVER=$(git -C "$TREE" show "$COMMIT:packaging/arch/PKGBUILD" | sed -n 's/^pkgver=//p')
# the release (packaging/rilascio.sh): RX_VERSION = pkgver, RX_REVISION = pkgrel
PKGVER=${RX_VERSION:-$PKGVER}

echo "== the three units: equivalent?"
# ⭐ The Arch unit once set the port with `Environment=` and read no
#   EnvironmentFile: the engine's /etc/remotix/remotix.conf.d/port.conf was ignored
#   and an install with a non-default port rolled back (0.18.0-1).  The three
#   families' units and defaults must stay the same apart from the DOCUMENTED
#   differences, which are normalised here:
#   · the binary's folder: /usr/lib/remotix (Arch) vs /usr/libexec/remotix;
#   · the .deb launches through `/bin/sh -c 'exec …'` with `$$` escapes (the
#     .rpm and Arch directly, for SELinux and for uniformity);
#   · `RestartPreventExitStatus=78`: .deb only.
#   Read from the SAME commit as the package.
unit() {   # the significant lines of a unit, normalised
	git -C "$TREE" show "$COMMIT:$1" | sed -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' \
		-e '/^RestartPreventExitStatus=78$/d' \
		-e "s|^ExecStart=/bin/sh -c 'exec \(.*\)'\$|ExecStart=\1|" \
		-e 's|"\$\${REMOTIX_PORT}"|${REMOTIX_PORT}|' -e 's|\$\${REMOTIX_OPTIONS}|$REMOTIX_OPTIONS|' \
		-e 's|/usr/lib/remotix/|/usr/libexec/remotix/|g'
}
default() {   # the variables of the defaults file
	git -C "$TREE" show "$COMMIT:$1" | sed -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d'
}
for f in debian rpm; do
	diff <(unit packaging/arch/remotix.service) <(unit packaging/$f/remotix.service) \
		|| { echo "⛔ packaging/arch/remotix.service and packaging/$f/remotix.service differ (above)"; exit 1; }
	diff <(default packaging/arch/remotix.conf) <(default packaging/$f/remotix.conf) \
		|| { echo "⛔ packaging/arch/remotix.conf and packaging/$f/remotix.conf differ (above)"; exit 1; }
done
echo "units and defaults equivalent (arch = debian = rpm, documented differences aside)"

rm -rf "$WORKDIR"; mkdir -p "$WORKDIR/tmp"
export TMPDIR="$WORKDIR/tmp"

git -C "$TREE" archive "$COMMIT" packaging/arch/PKGBUILD packaging/arch/remotix.install \
	| tar -x -C "$WORKDIR" --strip-components=2
# T8: RX_REVISION = the pkgrel of a maintenance release (a rebuild)
[ -n "${RX_REVISION:-}" ] && sed -i "s/^pkgrel=.*/pkgrel=$RX_REVISION/" "$WORKDIR/PKGBUILD"
sed -i "s/^pkgver=.*/pkgver=$PKGVER/" "$WORKDIR/PKGBUILD"
git -C "$TREE" archive --format=tar.gz --prefix="remotix-$PKGVER/" \
	-o "$WORKDIR/remotix-$PKGVER.tar.gz" "$COMMIT" src banchi/rcp packaging/arch THIRD-PARTY-LICENSES LICENSE.md
{
	echo "commit $COMMIT"
	echo "tarball $(sha256sum "$WORKDIR/remotix-$PKGVER.tar.gz" | cut -d' ' -f1)  remotix-$PKGVER.tar.gz"
	echo "immagine $(podman image inspect -f '{{.Id}}' "$IMAGE" | cut -c1-12)"
} >"$WORKDIR/sorgente.txt"

echo "== makepkg ($COMMIT)"
# R23: SOURCE_DATE_EPOCH = the commit date.  `[M]` 29 Sep: without it, two
# builds give the same binary (same sha256) and packages that differ
# only in `builddate` in .PKGINFO/.BUILDINFO and the dates in .MTREE.
SDE=$(git -C "$TREE" log -1 --format=%ct "$COMMIT")
podman run --rm --userns=keep-id -v "$WORKDIR:/pkg" -w /pkg -e HOME=/pkg/tmp \
	-e SOURCE_DATE_EPOCH="$SDE" "$IMAGE" \
	makepkg -f --noconfirm >"$WORKDIR/makepkg.log" 2>&1 \
	|| { tail -30 "$WORKDIR/makepkg.log"; echo "⛔ makepkg failed (see $WORKDIR/makepkg.log)"; exit 1; }
PKG=$(cd "$WORKDIR" && ls remotix-"$PKGVER"-*-x86_64.pkg.tar.zst)

echo "== namcap"
podman run --rm -v "$WORKDIR:/pkg:ro" "$IMAGE" sh -c \
	"pacman -Sy --noconfirm --needed namcap >/dev/null 2>&1 && cd /pkg && echo '# PKGBUILD' && namcap PKGBUILD; echo '# $PKG' && namcap -i $PKG" \
	>"$WORKDIR/namcap.txt" 2>&1 || true

echo "== R14: bench files in the package?"
tar -tf "$WORKDIR/$PKG" >"$WORKDIR/elenco.txt"
if grep -E 'provisiona|gpu-udev|riavvia-|sudoers|ld\.so\.conf|banchi|/opt/' "$WORKDIR/elenco.txt"; then
	echo "⛔ R14 RED"; exit 1
fi
echo "R14 green: $(grep -vc '/$' "$WORKDIR/elenco.txt") entries, none on the blacklist"

mkdir -p "$OUTPUT"
cp "$WORKDIR/$PKG" "$WORKDIR/sorgente.txt" "$WORKDIR/namcap.txt" "$WORKDIR/makepkg.log" "$WORKDIR/elenco.txt" "$OUTPUT/"
tar -xOf "$WORKDIR/$PKG" .PKGINFO >"$OUTPUT/PKGINFO.txt"
echo "== ready: $OUTPUT/$PKG"
cat "$OUTPUT/namcap.txt"
