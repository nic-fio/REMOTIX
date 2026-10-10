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
#   2. the ENGINE: the tests (installatore/costruisci.sh prove, all green), then the static
#      build with the release version; the catalogue is inside (DECISIONI §10.21);
#   3. the PRODUCT packages for the three families: .deb (Debian 13, Ubuntu 26.04:
#      src/costruzione/costruisci-deb.sh), .rpm (Fedora 44, Alma 10, Tumbleweed, Leap 16:
#      packaging/rpm/costruisci-rpm.sh), Arch (packaging/arch/costruisci.sh);
#   4. the ENGINE packages (packaging/motore/pacchetti-motore.sh): it stays on the machine
#      (status, uninstall, post-upgrade);
#   5. the .RUN: the installatore/run.sh header (with the version and the payload's sha256 written
#      inside) and below it the tar.gz with the engine, LICENSE.md, THIRD-PARTY-LICENSES and packages/<target>/
#      (product + engine for each distribution); next to it its .sha256, to be published on the website.
#
# Environment:
#   BERSAGLI   which ones (default: debian13 ubuntu2604 fedora44 alma10 tumbleweed leap16 arch)
#   USCITA     where the .run goes (default costruzione-uscita/rilasci)
#   RX_SPORCO=1  for testing only: accepts a tree with uncommitted changes (the packages say so)
# ⚠ No /tmp: on the laptop it is nearly full; everything under costruzione-uscita/.
# THIRD-PARTY-LICENSES (LICENSE.md §8): the licence texts of the third-party components incorporated
#    in the packages and in the engine. Every package carries it, and the .run next to the engine; step 2
#    stops if it does not name, at the version that goes in, every Go module linked into the engine,
#    the Go toolchain, ngtcp2, nghttp3 and libopus.
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/.." && pwd)
INST=$ALBERO/installatore

VERSIONE=${1:-}
if ! [[ $VERSIONE =~ ^([0-9]+\.[0-9]+\.[0-9]+)-([0-9]+)$ ]]; then
	sed -n '2,6p' "$0"; exit 2
fi
V=${BASH_REMATCH[1]} R=${BASH_REMATCH[2]}
BERSAGLI=${BERSAGLI:-debian13 ubuntu2604 fedora44 alma10 tumbleweed leap16 arch}
USCITA=${USCITA:-$ALBERO/costruzione-uscita/rilasci}
LAV=$ALBERO/costruzione-uscita/rilascio-$VERSIONE
# the containers (rpm) leave files owned by another uid of the user namespace: they are removed from inside it
podman unshare rm -rf "$LAV"; mkdir -p "$LAV/tmp"
export TMPDIR=$LAV/tmp
REG=$LAV/rilascio.log
passo() { printf '\n== %s\n' "$*" | tee -a "$REG"; }
RUN=$USCITA/remotix-$VERSIONE.run

passo "1. the tree ($VERSIONE, targets: $BERSAGLI)"
COMMIT=$(git -C "$ALBERO" rev-parse HEAD)
SPORCO=$(git -C "$ALBERO" status --porcelain -- src packaging installatore banchi/rcp THIRD-PARTY-LICENSES LICENSE.md)
if [ -n "$SPORCO" ]; then
	[ "${RX_SPORCO:-}" = 1 ] || { echo "⛔ uncommitted changes:"; echo "$SPORCO"; exit 1; }
	echo "⚠ RX_SPORCO=1: tree with uncommitted changes (for testing only)" | tee -a "$REG"
fi
echo "commit $COMMIT" | tee -a "$REG"
# ⛔ the same version is never published twice with different content: a new revision is needed
[ ! -e "$RUN" ] || { echo "⛔ $RUN already exists: a new revision is needed"; exit 1; }

passo "2. the engine: tests and build ($V)"
"$INST/costruisci.sh" prove >"$LAV/prove-motore.log" 2>&1 || { tail -30 "$LAV/prove-motore.log"; echo "⛔ the engine tests"; exit 1; }
if grep -qE '^(FAIL|gofmt:)' "$LAV/prove-motore.log"; then tail -30 "$LAV/prove-motore.log"; echo "⛔ the engine tests"; exit 1; fi
grep -E '^ok ' "$LAV/prove-motore.log" | tee -a "$REG"
RX_VERSIONE=$V "$INST/costruisci.sh" >>"$REG" 2>&1
mkdir -p "$LAV/motore-bin"
cp "$INST/uscita/remotix-install" "$LAV/motore-bin/"
[ "$("$LAV/motore-bin/remotix-install" version | awk '{print $1}')" = "$V" ] || { echo "⛔ the engine does not report $V"; exit 1; }
"$LAV/motore-bin/remotix-install" catalog | head -1 | tee -a "$REG"
TPL=$ALBERO/THIRD-PARTY-LICENSES
{
	"$INST/costruisci.sh" go list -deps -f '{{with .Module}}{{if not .Main}}{{.Path}} {{.Version}}{{end}}{{end}}' ./cmd/remotix-install
	"$INST/costruisci.sh" go env GOVERSION | sed 's/^go\(.*\)/Go \1 (standard library and runtime)/'
	sed -n 's/^NGTCP2_VER=${NGTCP2_VER:-v\(.*\)}$/ngtcp2 \1/p; s/^NGHTTP3_VER=${NGHTTP3_VER:-v\(.*\)}$/nghttp3 \1/p' \
		"$ALBERO/src/costruzione/quic-statiche.sh"
	sed -n 's/^OPUS_VER=/libopus /p' "$ALBERO/src/opus-wasm/costruisci.sh"
} | sort -u | while read -r c; do
	grep -qxF "== $c" "$TPL" || { echo "⛔ THIRD-PARTY-LICENSES does not name «$c»"; exit 1; }
done

passo "3. the product packages"
P=$LAV/prodotto
deb=() rpm=() arch=0
for b in $BERSAGLI; do
	case $b in
	debian13 | ubuntu2604) deb+=("$b") ;;
	fedora44 | alma10 | tumbleweed | leap16) rpm+=("$b") ;;
	arch) arch=1 ;;
	*) echo "⛔ unknown target: $b"; exit 2 ;;
	esac
done
if [ ${#deb[@]} -gt 0 ]; then
	USCITA=$P CACHE=$LAV/cache RX_VERSIONE=$V RX_REVISIONE=$R "$ALBERO/src/costruzione/costruisci-deb.sh" "${deb[@]}" >>"$REG" 2>&1 ||
		{ tail -30 "$REG"; echo "⛔ .deb"; exit 1; }
fi
if [ ${#rpm[@]} -gt 0 ]; then
	USCITA=$P CACHE=$LAV/cache RX_VERSIONE=$V RX_REVISIONE=$R "$ALBERO/packaging/rpm/costruisci-rpm.sh" "${rpm[@]}" >>"$REG" 2>&1 ||
		{ tail -30 "$REG"; echo "⛔ .rpm"; exit 1; }
	for b in "${rpm[@]}"; do grep -q ' pacchetto=si ' "$P/rpm/$b/esito.txt" || { cat "$P/rpm/$b/esito.txt"; exit 1; }; done
fi
if [ $arch = 1 ]; then
	USCITA=$P/arch RX_VERSIONE=$V RX_REVISIONE=$R "$ALBERO/packaging/arch/costruisci.sh" >>"$REG" 2>&1 ||
		{ tail -30 "$REG"; echo "⛔ Arch"; exit 1; }
fi
find "$P" -maxdepth 3 \( -name 'remotix_*.deb' -o -name 'remotix-*.rpm' -o -name 'remotix-*.pkg.tar.zst' \) ! -name '*.src.rpm' ! -name '*-debug*' ! -path '*/.lavoro/*' ! -name 'seconda-*' -printf '   %P\n' | sort | tee -a "$REG"

passo "4. the engine packages"
M=$LAV/motore
RX_VERSIONE=$V RX_REVISIONE=$R MOTORE=$LAV/motore-bin/remotix-install \
	"$ALBERO/packaging/motore/pacchetti-motore.sh" "$M" >>"$REG" 2>&1 || { tail -20 "$REG"; exit 1; }

passo "5. the .run ($RUN)"
C=$LAV/carico
mkdir -p "$C/packages"
cp "$LAV/motore-bin/remotix-install" "$ALBERO/LICENSE.md" "$TPL" "$C/"
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
(cd "$C" && find . -type f | sort | sed 's|^\./|   |') | tee -a "$REG"
tar --sort=name --owner=0 --group=0 --numeric-owner --mtime="@$(git -C "$ALBERO" log -1 --format=%ct)" \
	-C "$C" -cf - . | gzip -n -9 >"$LAV/carico.tar.gz"
SHA_CARICO=$(sha256sum "$LAV/carico.tar.gz" | cut -d' ' -f1)
mkdir -p "$USCITA"
sed -e "s/^VERSIONE=''\$/VERSIONE='$VERSIONE'/" -e "s/^PAYLOAD_SHA256=''\$/PAYLOAD_SHA256='$SHA_CARICO'/" \
	"$INST/run.sh" >"$RUN.parziale"
grep -q "^PAYLOAD_SHA256='$SHA_CARICO'\$" "$RUN.parziale" || { echo "⛔ the header did not take the sha256"; exit 1; }
cat "$LAV/carico.tar.gz" >>"$RUN.parziale"
mv "$RUN.parziale" "$RUN"
(cd "$USCITA" && sha256sum "$(basename "$RUN")" >"$(basename "$RUN").sha256")
sh "$RUN" version | tee -a "$REG"

passo "6. the summary"
printf '%s %s commit %s bersagli %s sha256 %s\n' "$VERSIONE" "$(date -u +%FT%TZ)" "$COMMIT" \
	"$(echo $BERSAGLI | tr ' ' ',')" "$(cut -d' ' -f1 "$RUN.sha256")" >>"$USCITA/RELEASES.txt"
cat <<EOF | tee -a "$REG"
REMOTIX $VERSIONE — ready: $RUN ($(du -h "$RUN" | cut -f1))
  sha256 (to be published on the website, over HTTPS, next to the file):
      $(cut -d' ' -f1 "$RUN.sha256")
  install with:  sudo sh $(basename "$RUN")
  the release log: $REG
EOF
