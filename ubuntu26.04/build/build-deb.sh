#!/usr/bin/env bash
# build-deb.sh — builds REMOTIX's .deb for Ubuntu 26.04 (resolute), inside a podman container.
#
#     build/build-deb.sh
#     OUTPUT=/some/dir RX_VERSION=1.0.0 RX_REVISION=1 build/build-deb.sh
#     TWICE=1 build/build-deb.sh          # builds a second time and checks the .deb is byte-identical
#
# Environment (all optional):
#   OUTPUT        where the results go                     (default /media/REMOTIX-UBUNTU/pacchetti)
#   WORK          scratch space (copies of the tree)       (default $OUTPUT/.work)
#   RX_VERSION    upstream version                         (default 1.2.0~dev)
#   RX_REVISION   Package revision                        (default 1)
#   SOURCE_DATE_EPOCH  build date, for a reproducible .deb (default: the newest mtime in src/ and debian/)
#   TWICE=1       second build + byte comparison
#
# Needs only: podman, network (the image build clones ngtcp2/nghttp3 from GitHub and fetches labwc/wlroots, sha256-checked;
# dpkg-buildpackage itself needs none).
# It does NOT need git, Go, benches/ or the old repository.
#
# What it does:
#   1. builds the image localhost/remotix-ubuntu-build from build/Containerfile (Ubuntu 26.04 with universe, static ngtcp2/nghttp3,
#      the labwc/wlroots tarballs);
#   2. makes a COPY of the tree (src/, debian/, build/labwc-ospite/ as labwc-ospite/, LICENSE.md, THIRD-PARTY-LICENSES) in $WORK and writes debian/changelog and
#      appends LICENSE.md to debian/copyright (debian/copyright's last line is «License: LicenseRef-REMOTIX»);
#   3. runs `dpkg-buildpackage -b` in the container, then lintian;
#   4. checks on the FINISHED package (results in controlli.txt, one line each, SI/NO; any NO fails the script):
#        R13  the bench function is NOT in the binary extracted from the .deb and IS in an rcp.o built with BENCH_ON 1
#             (the positive control: without it "not found" could mean "cannot search"); the unit passes no bench option;
#        R14  no bench file in the package's file list;
#        R4   `ldd` of the binary: nothing "not found", no dynamic ngtcp2/nghttp3; and of OUR labwc: nothing "not found", no libwlroots;
#        R23  (TWICE=1) two clean builds give the same bytes.
# The corresponding source of OUR labwc (GPL-2.0: it must be published with the package) is saved as $OUTPUT/remotix-<version>-labwc-source.tar.gz (+ .sha256):
# the two upstream tarballs from the image (sha256 as in VERSIONS), the patch, the recipe (VERSIONS, fetch.sh, build.sh).
# Output in $OUTPUT/: the .deb, the .buildinfo, costruzione.log, immagine.log, lintian.txt, controlli.txt, elenco.txt.
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/.." && pwd)
OUTPUT=${OUTPUT:-/media/REMOTIX-UBUNTU/pacchetti}
WORK=${WORK:-$OUTPUT/.work}
IMAGE=${IMAGE:-localhost/remotix-ubuntu-build}
VERSION_UP=${RX_VERSION:-1.2.0~dev}
REVISION=${RX_REVISION:-1}

command -v podman >/dev/null 2>&1 || { echo "podman is not there" >&2; exit 2; }
mkdir -p "$OUTPUT" "$WORK/tmp" || exit 2
export TMPDIR="$WORK/tmp"   # never /tmp (RAM-only machines)

# the build date: fixed by the caller, or derived from the files (same source, same package)
if [ -z "${SOURCE_DATE_EPOCH:-}" ]; then
	SOURCE_DATE_EPOCH=$(find "$TREE/src" "$TREE/debian" "$TREE/build/labwc-ospite" "$TREE/LICENSE.md" "$TREE/THIRD-PARTY-LICENSES" -type f -printf '%T@\n' | sort -n | tail -1 | cut -d. -f1)
fi
export SOURCE_DATE_EPOCH
DATE_RFC=$(date -R -u -d "@$SOURCE_DATE_EPOCH")
VERSION="$VERSION_UP-$REVISION+ubuntu26.04"

prepare_copy() {  # prepare_copy <folder>
	local c=$1
	rm -rf "$c"; mkdir -p "$c/remotix"
	cp -a "$TREE/src" "$c/remotix/src"
	cp -a "$TREE/debian" "$c/remotix/debian"
	# OUR labwc: the recipe and the patch (the tarballs are in the image, /usr/local/src/labwc-sources)
	cp -a "$HERE/labwc-ospite" "$c/remotix/labwc-ospite"
	cp "$TREE/THIRD-PARTY-LICENSES" "$c/remotix/"
	# the licence text goes into debian/copyright, as «License: LicenseRef-REMOTIX» continuation lines (« .» = empty line)
	sed -e 's/^$/./' -e 's/^/ /' "$TREE/LICENSE.md" >>"$c/remotix/debian/copyright"
	# leftovers of a local build must not enter the package
	rm -f "$c/remotix/src/remotix" "$c/remotix/src"/*.o "$c/remotix/src"/*-protocol.c "$c/remotix/src"/*-client-protocol.h
	cat >"$c/remotix/debian/changelog" <<EOF
remotix ($VERSION) resolute; urgency=medium

  * Ubuntu 26.04 build.

 -- nicfio <remotix@nicfio.it>  $DATE_RFC
EOF
}

build_in() {  # build_in <copy> <log>
	podman run --rm --userns=keep-id \
		-e DEB_BUILD_OPTIONS -e SOURCE_DATE_EPOCH \
		-v "$1:/lavoro" -w /lavoro/remotix "$IMAGE" \
		sh -c 'dpkg-buildpackage -b -us -uc' >"$2" 2>&1
}

c1=$WORK/a c2=$WORK/b
outcome=0

echo "== image"
podman build -t "$IMAGE" -f "$HERE/Containerfile" "$HERE" >"$OUTPUT/immagine.log" 2>&1 \
	|| { echo "image build failed (see $OUTPUT/immagine.log)" >&2; exit 1; }

echo "== package $VERSION"
prepare_copy "$c1"
if ! build_in "$c1" "$OUTPUT/costruzione.log"; then
	echo "dpkg-buildpackage failed (see $OUTPUT/costruzione.log)" >&2; tail -20 "$OUTPUT/costruzione.log" >&2
	exit 1
fi
deb=$(cd "$c1" && ls remotix_*.deb | head -1)
[ -n "$deb" ] || { echo "no .deb produced" >&2; exit 1; }
cp "$c1/$deb" "$c1"/remotix_*.buildinfo "$OUTPUT/"
echo "   $deb"

echo "== lintian and checks"
podman run --rm -v "$OUTPUT:/u:ro" "$IMAGE" lintian -I --pedantic --no-tag-display-limit "/u/$deb" >"$OUTPUT/lintian.txt" 2>&1
# R13 positive control: rcp.o built with BENCH_ON 1, same flags as the Makefile
rm -rf "$c1/positivo"; cp -a "$c1/remotix/src" "$c1/positivo"
sed -i 's/^#define BENCH_ON 0$/#define BENCH_ON 1/' "$c1/positivo/rcp.c"
podman run --rm --userns=keep-id -v "$c1:/lavoro" -w /lavoro/positivo "$IMAGE" \
	sh -c 'make TWIN=none BENCH=1 rcp.o >/dev/null 2>&1' >/dev/null 2>&1
podman run --rm -v "$OUTPUT:/u:ro" -v "$c1:/c:ro" "$IMAGE" sh -c '
	set -u
	d=$(mktemp -d); dpkg-deb -x /u/'"$deb"' "$d"
	bin=$d/usr/libexec/remotix/remotix
	frase="the BENCH FUNCTION is ON"
	n=$(strings "$bin" | grep -c "$frase")
	p=$(strings /c/positivo/rcp.o 2>/dev/null | grep -c "$frase")
	[ "$n" = 0 ] && [ "$p" -ge 1 ] && r=SI || r=NO
	echo "R13 banco-nel-binario $r (package: $n, positive control rcp.o with BENCH_ON 1: $p)"
	o=$(grep "^ExecStart" $d/usr/lib/systemd/system/remotix.service | \
	     grep -oE -- "--(survey|command-socket|audio-test|verbose)" | sort -u | tr "\n" " ")
	[ -z "$o" ] && echo "R13 opzioni-di-banco-nell-unita SI (none)" \
	            || echo "R13 opzioni-di-banco-nell-unita NO ($o)"
	nere=$(dpkg-deb -c /u/'"$deb"' | awk "{print \$NF}" | \
	       grep -E "/test|sudoers|gpu-udev|restart-|ld\.so\.conf|provision|benches|/opt/|\.pem$|\.key$" || true)
	[ -z "$nere" ] && echo "R14 file-del-banco SI (none)" \
	               || echo "R14 file-del-banco NO: $nere"
	l=$(ldd "$bin")
	if printf "%s\n" "$l" | grep -q "not found"; then echo "R4 ldd NO (not found)";
	elif printf "%s\n" "$l" | grep -qE "ngtcp2|nghttp3"; then echo "R4 ldd NO (dynamic ngtcp2/nghttp3)";
	else echo "R4 ldd SI ($(printf "%s\n" "$l" | wc -l) libraries, none missing)"; fi
	lw=$d/usr/libexec/remotix/labwc
	if [ ! -x "$lw" ]; then echo "R4 ldd-labwc NO (usr/libexec/remotix/labwc is not in the package)";
	else ll=$(ldd "$lw")
		if printf "%s\n" "$ll" | grep -q "not found"; then echo "R4 ldd-labwc NO (not found)";
		elif printf "%s\n" "$ll" | grep -q wlroots; then echo "R4 ldd-labwc NO (a libwlroots is linked)";
		else echo "R4 ldd-labwc SI (no libwlroots, none missing; $("$lw" --version | head -1))"; fi
	fi
	echo "Depends:    $(dpkg-deb -f /u/'"$deb"' Depends)"
	echo "Recommends: $(dpkg-deb -f /u/'"$deb"' Recommends)"
	echo "Static:     $(dpkg-deb -f /u/'"$deb"' Static-Built-Using)"
	echo "Conffiles:"; dpkg-deb --ctrl-tarfile /u/'"$deb"' | tar -xO ./conffiles | sed "s/^/  /"
' >"$OUTPUT/controlli.txt" 2>&1
# the corresponding source of OUR labwc, to be published with the package (LICENSE.md section 8)
src=$WORK/labwc-source/remotix-$VERSION_UP-labwc-source
rm -rf "$WORK/labwc-source"; mkdir -p "$src"
cp -a "$HERE/labwc-ospite/." "$src/"
lsrc=remotix-$VERSION_UP-labwc-source.tar.gz
lok=SI; lwhy=
podman run --rm --userns=keep-id -v "$src:/o" "$IMAGE" sh -c 'cp /usr/local/src/labwc-sources/*.tar.gz /o/' || { lok=NO; lwhy="copy of the tarballs from the image failed"; }
# the two tarballs must be there and match the sha256 of VERSIONS (fetch.sh checks without downloading when the files exist)
if [ "$lok" = SI ]; then
	"$HERE/labwc-ospite/fetch.sh" "$src" >/dev/null 2>&1 || { lok=NO; lwhy="tarballs missing or sha256 differs from VERSIONS"; }
fi
if [ "$lok" = SI ]; then
	# deterministic: fixed order, owner, mtime, no write bit for group/others, no name/date in the gzip header
	tar -C "$WORK/labwc-source" --sort=name --owner=0 --group=0 --numeric-owner --mode=go-w --mtime="@$SOURCE_DATE_EPOCH" \
		-cf - "remotix-$VERSION_UP-labwc-source" | gzip -n >"$OUTPUT/$lsrc" \
		&& [ "${PIPESTATUS[0]}" = 0 ] || { lok=NO; lwhy="tar of the sources failed"; }
fi
if [ "$lok" = SI ]; then
	n=$(tar tzf "$OUTPUT/$lsrc" | grep -cE '/(labwc-[0-9.]+\.tar\.gz|wlroots-[0-9.]+\.tar\.gz|wlroots-[0-9.]+-remotix-presented-root\.patch|VERSIONS|fetch\.sh|build\.sh|README)$')
	[ "$n" = 7 ] || { lok=NO; lwhy="the archive has $n of the 7 expected files"; }
fi
if [ "$lok" = SI ]; then
	(cd "$OUTPUT" && sha256sum "$lsrc" >"$lsrc.sha256")
	echo "labwc-source SI ($lsrc, $(cut -c1-16 <"$OUTPUT/$lsrc.sha256")..., 7 files, tarballs verified against VERSIONS)" >>"$OUTPUT/controlli.txt"
else
	rm -f "$OUTPUT/$lsrc" "$OUTPUT/$lsrc.sha256"
	echo "labwc-source NO ($lwhy)" >>"$OUTPUT/controlli.txt"
fi
dpkg-deb -c "$OUTPUT/$deb" >"$OUTPUT/elenco.txt" 2>/dev/null \
	|| podman run --rm -v "$OUTPUT:/u:ro" "$IMAGE" dpkg-deb -c "/u/$deb" >"$OUTPUT/elenco.txt"

if [ "${TWICE:-0}" = 1 ]; then
	echo "== second build (R23)"
	prepare_copy "$c2"
	if build_in "$c2" "$OUTPUT/costruzione-2.log"; then
		if cmp -s "$c1/$deb" "$c2/$deb"; then
			echo "R23 riproducibile SI ($(sha256sum <"$OUTPUT/$deb" | cut -c1-16)... identical in two clean copies)" >>"$OUTPUT/controlli.txt"
		else
			echo "R23 riproducibile NO (the two .deb files differ)" >>"$OUTPUT/controlli.txt"
			cp "$c2/$deb" "$OUTPUT/seconda-$deb"
		fi
	else
		echo "R23 riproducibile NO (second build failed)" >>"$OUTPUT/controlli.txt"
	fi
fi

if [ "${TWICE:-0}" = 1 ] && [ "$lok" = SI ]; then
	# the source archive too: a fresh copy of the recipe, the same two tarballs, tarred again
	rm -rf "$WORK/labwc-source-2"; mkdir -p "$WORK/labwc-source-2/remotix-$VERSION_UP-labwc-source"
	cp -a "$HERE/labwc-ospite/." "$WORK/labwc-source-2/remotix-$VERSION_UP-labwc-source/"
	cp -p "$src"/labwc-*.tar.gz "$src"/wlroots-*.tar.gz "$WORK/labwc-source-2/remotix-$VERSION_UP-labwc-source/"
	tar -C "$WORK/labwc-source-2" --sort=name --owner=0 --group=0 --numeric-owner --mode=go-w --mtime="@$SOURCE_DATE_EPOCH" \
		-cf - "remotix-$VERSION_UP-labwc-source" | gzip -n >"$WORK/labwc-source-2.tar.gz"
	if cmp -s "$WORK/labwc-source-2.tar.gz" "$OUTPUT/$lsrc"; then
		echo "R23 labwc-source-riproducibile SI (same .sha256 twice)" >>"$OUTPUT/controlli.txt"
	else
		echo "R23 labwc-source-riproducibile NO (the two source archives differ)" >>"$OUTPUT/controlli.txt"
	fi
fi

grep -q ' NO' "$OUTPUT/controlli.txt" && outcome=1
sed 's/^/   /' "$OUTPUT/controlli.txt"
printf '   lintian: E=%s W=%s\n' "$(grep -c '^E: ' "$OUTPUT/lintian.txt")" "$(grep -c '^W: ' "$OUTPUT/lintian.txt")"
exit $outcome
