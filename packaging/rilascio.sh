#!/usr/bin/env bash
# rilascio.sh — THE REMOTIX release command: for every version, a single one.
#
#     packaging/rilascio.sh X.Y.Z-R          for example  packaging/rilascio.sh 0.17.0-7
#
# X.Y.Z is the REMOTIX version, R the package revision (a rebuild: 0.17.0-7 → 0.17.0-8).
# The same version goes to everything: remotix and remotix-install (the engine, which states it with `version`).
# The product ships as ONE file, remotix-X.Y.Z-R.run (the single package, DECISIONI §10.36):
# no repository to add to the system, no keys. What it does, in order, stopping at the
# first error:
#   1. the tree is that of a commit (no uncommitted changes in src/, packaging/,
#      installatore/, banchi/rcp/): the packages say which commit they come from;
#   2. the ENGINE: the tests (installatore/costruisci.sh test, all green), then the static
#      build with the release version; the catalogue is inside (DECISIONI §10.21);
#   3. the PRODUCT packages for the three families: .deb (Debian 13, Ubuntu 26.04:
#      src/costruzione/costruisci-deb.sh), .rpm (Fedora 44, Alma 10, Tumbleweed, Leap 16:
#      packaging/rpm/costruisci-rpm.sh), Arch (packaging/arch/costruisci.sh);
#   4. the ENGINE packages (packaging/motore/pacchetti-motore.sh): it stays on the machine
#      (status, uninstall, post-upgrade);
#   5. the .RUN: the installatore/run.sh header (with the version and the payload's sha256 written
#      inside) and below it the tar.gz with the engine, LICENSE.md, THIRD-PARTY-LICENSES and packages/<target>/
#      (product + engine for each distribution); next to it its .sha256, to be published on the website.
#      ⭐ DECISIONI §10.43 (GPL-2.0): the Alma package carries OUR labwc; its exact corresponding source
#      (the upstream tarball, unmodified, and the recipe: packaging/rpm/labwc/ and remotix.spec) goes
#      INSIDE the .run (source/labwc/) and NEXT TO it, remotix-X.Y.Z-R-labwc-source.tar.gz (+ .sha256),
#      to be published with every release.
#
# Environment:
#   TARGETS   which ones (default: debian13 ubuntu2604 fedora44 alma10 tumbleweed leap16 arch)
#   OUTPUT     where the .run goes (default costruzione-uscita/rilasci)
#   RX_DIRTY=1  for testing only: accepts a tree with uncommitted changes (the packages say so)
# ⚠ No /tmp: on the laptop it is nearly full; everything under costruzione-uscita/.
# THIRD-PARTY-LICENSES (LICENSE.md §8): the licence texts of the third-party components incorporated
#    in the packages and in the engine. Every package carries it, and the .run next to the engine; step 2
#    stops if it does not name, at the version that goes in, every Go module linked into the engine,
#    the Go toolchain, ngtcp2, nghttp3 and libopus.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/.." && pwd)
INST=$TREE/installatore

VERSION=${1:-}
if ! [[ $VERSION =~ ^([0-9]+\.[0-9]+\.[0-9]+)-([0-9]+)$ ]]; then
	sed -n '2,6p' "$0"; exit 2
fi
V=${BASH_REMATCH[1]} R=${BASH_REMATCH[2]}
TARGETS=${TARGETS:-debian13 ubuntu2604 fedora44 alma10 tumbleweed leap16 arch}
OUTPUT=${OUTPUT:-$TREE/costruzione-uscita/rilasci}
WORKDIR=$TREE/costruzione-uscita/rilascio-$VERSION
# the containers (rpm) leave files owned by another uid of the user namespace: they are removed from inside it
podman unshare rm -rf "$WORKDIR"; mkdir -p "$WORKDIR/tmp"
export TMPDIR=$WORKDIR/tmp
REG=$WORKDIR/rilascio.log
step() { printf '\n== %s\n' "$*" | tee -a "$REG"; }
RUN=$OUTPUT/remotix-$VERSION.run

step "1. the tree ($VERSION, targets: $TARGETS)"
COMMIT=$(git -C "$TREE" rev-parse HEAD)
DIRTY=$(git -C "$TREE" status --porcelain -- src packaging installatore banchi/rcp THIRD-PARTY-LICENSES LICENSE.md)
if [ -n "$DIRTY" ]; then
	[ "${RX_DIRTY:-}" = 1 ] || { echo "⛔ uncommitted changes:"; echo "$DIRTY"; exit 1; }
	echo "⚠ RX_DIRTY=1: tree with uncommitted changes (for testing only)" | tee -a "$REG"
fi
echo "commit $COMMIT" | tee -a "$REG"
# ⛔ the same version is never published twice with different content: a new revision is needed
[ ! -e "$RUN" ] || { echo "⛔ $RUN already exists: a new revision is needed"; exit 1; }

step "2. the engine: tests and build ($V)"
"$INST/costruisci.sh" test >"$WORKDIR/prove-motore.log" 2>&1 || { tail -30 "$WORKDIR/prove-motore.log"; echo "⛔ the engine tests"; exit 1; }
if grep -qE '^(FAIL|gofmt:)' "$WORKDIR/prove-motore.log"; then tail -30 "$WORKDIR/prove-motore.log"; echo "⛔ the engine tests"; exit 1; fi
grep -E '^ok ' "$WORKDIR/prove-motore.log" | tee -a "$REG"
RX_VERSION=$V "$INST/costruisci.sh" >>"$REG" 2>&1
mkdir -p "$WORKDIR/motore-bin"
cp "$INST/uscita/remotix-install" "$WORKDIR/motore-bin/"
[ "$("$WORKDIR/motore-bin/remotix-install" version | awk '{print $1}')" = "$V" ] || { echo "⛔ the engine does not report $V"; exit 1; }
"$WORKDIR/motore-bin/remotix-install" catalog | head -1 | tee -a "$REG"
TPL=$TREE/THIRD-PARTY-LICENSES
{
	"$INST/costruisci.sh" go list -deps -f '{{with .Module}}{{if not .Main}}{{.Path}} {{.Version}}{{end}}{{end}}' ./cmd/remotix-install
	"$INST/costruisci.sh" go env GOVERSION | sed 's/^go\(.*\)/Go \1 (standard library and runtime)/'
	sed -n 's/^NGTCP2_VER=${NGTCP2_VER:-v\(.*\)}$/ngtcp2 \1/p; s/^NGHTTP3_VER=${NGHTTP3_VER:-v\(.*\)}$/nghttp3 \1/p' \
		"$TREE/src/costruzione/quic-statiche.sh"
	sed -n 's/^OPUS_VER=/libopus /p' "$TREE/src/opus-wasm/costruisci.sh"
	awk '$1 == "labwc" { print $1, $2 }' "$TREE/packaging/rpm/labwc/VERSIONI"
} | sort -u | while read -r c; do
	grep -qxF "== $c" "$TPL" || { echo "⛔ THIRD-PARTY-LICENSES does not name «$c»"; exit 1; }
done

step "3. the product packages"
P=$WORKDIR/prodotto
deb=() rpm=() arch=0
for b in $TARGETS; do
	case $b in
	debian13 | ubuntu2604) deb+=("$b") ;;
	fedora44 | alma10 | tumbleweed | leap16) rpm+=("$b") ;;
	arch) arch=1 ;;
	*) echo "⛔ unknown target: $b"; exit 2 ;;
	esac
done
if [ ${#deb[@]} -gt 0 ]; then
	OUTPUT=$P CACHE=$WORKDIR/cache RX_VERSION=$V RX_REVISION=$R "$TREE/src/costruzione/costruisci-deb.sh" "${deb[@]}" >>"$REG" 2>&1 ||
		{ tail -30 "$REG"; echo "⛔ .deb"; exit 1; }
fi
if [ ${#rpm[@]} -gt 0 ]; then
	OUTPUT=$P CACHE=$WORKDIR/cache RX_VERSION=$V RX_REVISION=$R "$TREE/packaging/rpm/costruisci-rpm.sh" "${rpm[@]}" >>"$REG" 2>&1 ||
		{ tail -30 "$REG"; echo "⛔ .rpm"; exit 1; }
	for b in "${rpm[@]}"; do grep -q ' pacchetto=si ' "$P/rpm/$b/esito.txt" || { cat "$P/rpm/$b/esito.txt"; exit 1; }; done
fi
if [ $arch = 1 ]; then
	OUTPUT=$P/arch RX_VERSION=$V RX_REVISION=$R "$TREE/packaging/arch/costruisci.sh" >>"$REG" 2>&1 ||
		{ tail -30 "$REG"; echo "⛔ Arch"; exit 1; }
fi
find "$P" -maxdepth 3 \( -name 'remotix_*.deb' -o -name 'remotix-*.rpm' -o -name 'remotix-*.pkg.tar.zst' \) ! -name '*.src.rpm' ! -name '*-debug*' ! -path '*/.lavoro/*' ! -name 'seconda-*' -printf '   %P\n' | sort | tee -a "$REG"

step "4. the engine packages"
M=$WORKDIR/motore
RX_VERSION=$V RX_REVISION=$R ENGINE=$WORKDIR/motore-bin/remotix-install \
	"$TREE/packaging/motore/pacchetti-motore.sh" "$M" >>"$REG" 2>&1 || { tail -20 "$REG"; exit 1; }

step "5. the .run ($RUN)"
C=$WORKDIR/carico
mkdir -p "$C/packages"
cp "$WORKDIR/motore-bin/remotix-install" "$TREE/LICENSE.md" "$TPL" "$C/"
for b in "${deb[@]}"; do
	mkdir -p "$C/packages/$b"
	cp "$P/deb-$b"/remotix_*.deb "$M/remotix-install_${V}-${R}_amd64.deb" "$C/packages/$b/"
done
for b in "${rpm[@]}"; do
	mkdir -p "$C/packages/$b"
	cp $(ls "$P/rpm/$b"/*.rpm | grep -vE '\.src\.rpm$|-debug(info|source)-') "$M"/remotix-install-"$V"-"$R".x86_64.rpm "$C/packages/$b/"
done
if [ $arch = 1 ]; then
	mkdir -p "$C/packages/arch"
	cp "$P/arch"/remotix-"$V"-"$R"-x86_64.pkg.tar.zst "$M"/remotix-install-"$V"-"$R"-x86_64.pkg.tar.zst "$C/packages/arch/"
fi
# ⭐ §10.43: the corresponding source of the labwc inside the Alma package, in the .run and next to it
if [[ " ${rpm[*]} " == *" alma10 "* ]]; then
	SL=$TREE/costruzione-uscita/labwc-sources
	"$TREE/packaging/rpm/labwc/scarica.sh" "$SL" | tee -a "$REG"
	mkdir -p "$C/source/labwc/recipe"
	cp "$SL"/labwc-*.tar.gz "$C/source/labwc/"
	cp "$TREE/packaging/rpm/labwc/VERSIONI" "$TREE/packaging/rpm/labwc/scarica.sh" \
		"$TREE/packaging/rpm/remotix.spec" "$C/source/labwc/recipe/"
	SRC_LABWC=$OUTPUT/remotix-$VERSION-labwc-source.tar.gz
	mkdir -p "$OUTPUT"
	tar --sort=name --owner=0 --group=0 --numeric-owner --mtime="@$(git -C "$TREE" log -1 --format=%ct)" \
		-C "$C/source" -cf - labwc | gzip -n -9 >"$SRC_LABWC"
	(cd "$OUTPUT" && sha256sum "$(basename "$SRC_LABWC")" >"$(basename "$SRC_LABWC").sha256")
fi
(cd "$C" && find . -type f | sort | sed 's|^\./|   |') | tee -a "$REG"
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime="@$(git -C "$TREE" log -1 --format=%ct)" \
	-C "$C" -cf - . | gzip -n -9 >"$WORKDIR/carico.tar.gz"
PAYLOAD_SHA=$(sha256sum "$WORKDIR/carico.tar.gz" | cut -d' ' -f1)
mkdir -p "$OUTPUT"
sed -e "s/^VERSION=''\$/VERSION='$VERSION'/" -e "s/^PAYLOAD_SHA256=''\$/PAYLOAD_SHA256='$PAYLOAD_SHA'/" \
	"$INST/run.sh" >"$RUN.parziale"
grep -q "^PAYLOAD_SHA256='$PAYLOAD_SHA'\$" "$RUN.parziale" || { echo "⛔ the header did not take the sha256"; exit 1; }
cat "$WORKDIR/carico.tar.gz" >>"$RUN.parziale"
mv "$RUN.parziale" "$RUN"
(cd "$OUTPUT" && sha256sum "$(basename "$RUN")" >"$(basename "$RUN").sha256")
sh "$RUN" version | tee -a "$REG"

step "6. the summary"
printf '%s %s commit %s bersagli %s sha256 %s\n' "$VERSION" "$(date -u +%FT%TZ)" "$COMMIT" \
	"$(echo $TARGETS | tr ' ' ',')" "$(cut -d' ' -f1 "$RUN.sha256")" >>"$OUTPUT/RELEASES.txt"
cat <<EOF | tee -a "$REG"
REMOTIX $VERSION — ready: $RUN ($(du -h "$RUN" | cut -f1))
  sha256 (to be published on the website, over HTTPS, next to the file):
      $(cut -d' ' -f1 "$RUN.sha256")
  install with:  sudo sh $(basename "$RUN")
  labwc's source (GPL-2.0, Alma package; publish it with the .run): ${SRC_LABWC:-none}
  the release log: $REG
EOF
