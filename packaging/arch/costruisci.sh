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
# Output in $USCITA (default costruzione-uscita/pacchetto-arch, ignored
# by git).  ⚠ No /tmp: on the laptop it is almost full.
set -euo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
COMMIT=$(git -C "$ALBERO" rev-parse "${1:-HEAD}")
USCITA=${USCITA:-$ALBERO/costruzione-uscita/pacchetto-arch}
IMM=${IMM:-localhost/remotix-costruzione-arch}
LAV="$USCITA/.lavoro"
PKGVER=$(git -C "$ALBERO" show "$COMMIT:packaging/arch/PKGBUILD" | sed -n 's/^pkgver=//p')
# the release (packaging/rilascio.sh): RX_VERSIONE = pkgver, RX_REVISIONE = pkgrel
PKGVER=${RX_VERSIONE:-$PKGVER}

echo "== the three units: equivalent?"
# ⭐ The Arch unit once set the port with `Environment=` and read no
#   EnvironmentFile: the engine's /etc/remotix/remotix.conf.d/porta.conf was ignored
#   and an install with a non-default port rolled back (0.18.0-1).  The three
#   families' units and defaults must stay the same apart from the DOCUMENTED
#   differences, which are normalised here:
#   · the binary's folder: /usr/lib/remotix (Arch) vs /usr/libexec/remotix;
#   · the .deb launches through `/bin/sh -c 'exec …'` with `$$` escapes (the
#     .rpm and Arch directly, for SELinux and for uniformity);
#   · `RestartPreventExitStatus=78`: .deb only.
#   Read from the SAME commit as the package.
unita() {   # the significant lines of a unit, normalised
	git -C "$ALBERO" show "$COMMIT:$1" | sed -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d' \
		-e '/^RestartPreventExitStatus=78$/d' \
		-e "s|^ExecStart=/bin/sh -c 'exec \(.*\)'\$|ExecStart=\1|" \
		-e 's|"\$\${REMOTIX_PORTA}"|${REMOTIX_PORTA}|' -e 's|\$\${REMOTIX_OPZIONI}|$REMOTIX_OPZIONI|' \
		-e 's|/usr/lib/remotix/|/usr/libexec/remotix/|g'
}
predefiniti() {   # the variables of the defaults file
	git -C "$ALBERO" show "$COMMIT:$1" | sed -e '/^[[:space:]]*#/d' -e '/^[[:space:]]*$/d'
}
for f in debian rpm; do
	diff <(unita packaging/arch/remotix.service) <(unita packaging/$f/remotix.service) \
		|| { echo "⛔ packaging/arch/remotix.service and packaging/$f/remotix.service differ (above)"; exit 1; }
	diff <(predefiniti packaging/arch/remotix.conf) <(predefiniti packaging/$f/remotix.conf) \
		|| { echo "⛔ packaging/arch/remotix.conf and packaging/$f/remotix.conf differ (above)"; exit 1; }
done
echo "units and defaults equivalent (arch = debian = rpm, documented differences aside)"

rm -rf "$LAV"; mkdir -p "$LAV/tmp"
export TMPDIR="$LAV/tmp"

git -C "$ALBERO" archive "$COMMIT" packaging/arch/PKGBUILD packaging/arch/remotix.install \
	| tar -x -C "$LAV" --strip-components=2
# T8: RX_REVISIONE = the pkgrel of a maintenance release (a rebuild)
[ -n "${RX_REVISIONE:-}" ] && sed -i "s/^pkgrel=.*/pkgrel=$RX_REVISIONE/" "$LAV/PKGBUILD"
sed -i "s/^pkgver=.*/pkgver=$PKGVER/" "$LAV/PKGBUILD"
git -C "$ALBERO" archive --format=tar.gz --prefix="remotix-$PKGVER/" \
	-o "$LAV/remotix-$PKGVER.tar.gz" "$COMMIT" src banchi/rcp packaging/arch THIRD-PARTY-LICENSES LICENSE.md
{
	echo "commit $COMMIT"
	echo "tarball $(sha256sum "$LAV/remotix-$PKGVER.tar.gz" | cut -d' ' -f1)  remotix-$PKGVER.tar.gz"
	echo "immagine $(podman image inspect -f '{{.Id}}' "$IMM" | cut -c1-12)"
} >"$LAV/sorgente.txt"

echo "== makepkg ($COMMIT)"
# R23: SOURCE_DATE_EPOCH = the commit date.  `[M]` 29 Sep: without it, two
# builds give the same binary (same sha256) and packages that differ
# only in `builddate` in .PKGINFO/.BUILDINFO and the dates in .MTREE.
SDE=$(git -C "$ALBERO" log -1 --format=%ct "$COMMIT")
podman run --rm --userns=keep-id -v "$LAV:/pkg" -w /pkg -e HOME=/pkg/tmp \
	-e SOURCE_DATE_EPOCH="$SDE" "$IMM" \
	makepkg -f --noconfirm >"$LAV/makepkg.log" 2>&1 \
	|| { tail -30 "$LAV/makepkg.log"; echo "⛔ makepkg failed (see $LAV/makepkg.log)"; exit 1; }
PKG=$(cd "$LAV" && ls remotix-"$PKGVER"-*-x86_64.pkg.tar.zst)

echo "== namcap"
podman run --rm -v "$LAV:/pkg:ro" "$IMM" sh -c \
	"pacman -Sy --noconfirm --needed namcap >/dev/null 2>&1 && cd /pkg && echo '# PKGBUILD' && namcap PKGBUILD; echo '# $PKG' && namcap -i $PKG" \
	>"$LAV/namcap.txt" 2>&1 || true

echo "== R14: bench files in the package?"
tar -tf "$LAV/$PKG" >"$LAV/elenco.txt"
if grep -E 'provisiona|gpu-udev|riavvia-|sudoers|ld\.so\.conf|banchi|/opt/' "$LAV/elenco.txt"; then
	echo "⛔ R14 RED"; exit 1
fi
echo "R14 green: $(grep -vc '/$' "$LAV/elenco.txt") entries, none on the blacklist"

mkdir -p "$USCITA"
cp "$LAV/$PKG" "$LAV/sorgente.txt" "$LAV/namcap.txt" "$LAV/makepkg.log" "$LAV/elenco.txt" "$USCITA/"
tar -xOf "$LAV/$PKG" .PKGINFO >"$USCITA/PKGINFO.txt"
echo "== ready: $USCITA/$PKG"
cat "$USCITA/namcap.txt"
