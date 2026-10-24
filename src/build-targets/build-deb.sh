#!/usr/bin/env bash
# build-deb.sh — REMOTIX's .deb package, inside the target's container.
#
#     src/build-targets/build-deb.sh debian13            # one
#     src/build-targets/build-deb.sh debian13 ubuntu2604 # both
#     TWICE=1 src/build-targets/build-deb.sh debian13      # and test R23
#
# For each target (phases/17-the-installer.md §6.1-§6.4, step T3):
#   1. the image localhost/remotix-costruzione-<target> (Containerfile.<target>,
#      with the .deb tools layer at the end);
#   2. a COPY of the tree: src/, benches/rcp/ (the twin the Makefile
#      compares) and packaging/debian/ as debian/; debian/changelog is WRITTEN
#      here, with the version and date of the commit (the date becomes
#      SOURCE_DATE_EPOCH: same source, same package — R23);
#   3. `dpkg-buildpackage -b` in the container, then lintian;
#   4. the checks on the FINISHED package, not on the tree:
#        R13  the bench function is not in the binary extracted from the .deb, and
#             is in an rcp.o built with BENCH_ON 1 (the positive
#             control: without it, "not found" could mean "I cannot search");
#             and the unit passes no bench options;
#        R14  no bench file in the package's file list;
#        R4   `ldd` of the extracted binary in the container: no "not found",
#             no dynamic ngtcp2/nghttp3;
#        R23  with TWICE=1 a second build in a second clean copy:
#             the .deb must be identical byte for byte.
#
# Output in $OUTPUT/deb-<target>/: the .deb, the .buildinfo, costruzione.log,
# lintian.txt, controlli.txt (one line per check, SI/NO).
# ⚠ No /tmp (on the laptop it is almost full): everything under $CACHE.
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
OUTPUT=${OUTPUT:-$TREE/costruzione-uscita}
CACHE=${CACHE:-$OUTPUT/.lavoro}
command -v podman >/dev/null 2>&1 || { echo "⛔ podman is not there"; exit 2; }
mkdir -p "$CACHE/tmp" "$OUTPUT"
export TMPDIR="$CACHE/tmp"
[ $# -gt 0 ] || set -- debian13 ubuntu2604

HASH=$(git -C "$TREE" rev-parse --short=7 HEAD)
DATA_R=$(git -C "$TREE" log -1 --format=%cD HEAD)
DAY=$(git -C "$TREE" log -1 --date=format:%Y%m%d --format=%cd HEAD)
DIRTY=""
if [ -n "$(git -C "$TREE" status --porcelain -- src packaging benches/rcp THIRD-PARTY-LICENSES LICENSE.md)" ]; then
	DIRTY=".modificato"
	echo "⚠ the tree has uncommitted changes in src/ packaging/ benches/rcp/:"
	echo "  the version carries «$DIRTY» and the package does NOT match $HASH"
fi

prepare_copy() {  # prepare_copy <folder> <target>
	local c=$1 b=$2 ver_suffix dist
	case $b in
	debian13)   ver_suffix=+deb13;       dist=trixie ;;
	ubuntu2604) ver_suffix=+ubuntu26.04; dist=resolute ;;
	*) echo "⛔ $b: not a .deb target"; return 2 ;;
	esac
	rm -rf "$c"; mkdir -p "$c/remotix/benches"
	cp -a "$TREE/src" "$c/remotix/src"
	cp -a "$TREE/benches/rcp" "$c/remotix/benches/rcp"
	cp -a "$TREE/packaging/debian" "$c/remotix/debian"
	cp "$TREE/THIRD-PARTY-LICENSES" "$c/remotix/"
	# the licence text (DECISIONI §10.39) goes into debian/copyright, whose last line is
	#   «License: LicenseRef-REMOTIX»: DEP-5 continuation lines, « .» for an empty one
	sed -e 's/^$/./' -e 's/^/ /' "$TREE/LICENSE.md" >>"$c/remotix/debian/copyright"
	rm -f "$c/remotix/src/remotix" "$c/remotix/src"/*.o \
	      "$c/remotix/src"/*-protocol.c "$c/remotix/src"/*-client-protocol.h
	# T8: RX_VERSION and RX_REVISION give the version of an archive RELEASE
	#     (0.17.0-2+deb13: the revision grows at every maintenance rebuild);
	#     without them, the test one with the commit, as in T3.
	if [ -n "${RX_VERSION:-}" ]; then
		VERSION="$RX_VERSION$DIRTY-${RX_REVISION:-1}$ver_suffix"
	else
		VERSION="0.17.0~git$DAY.$HASH$DIRTY-1$ver_suffix"
	fi
	cat >"$c/remotix/debian/changelog" <<EOF
remotix ($VERSION) $dist; urgency=medium

  * Built from $HASH$DIRTY (phase 17, T3).

 -- nicfio <nicfio@gmail.com>  $DATA_R
EOF
}

build_in() {  # build_in <copied> <bitmap> <log>
	podman run --rm --userns=keep-id -v "$1:/lavoro" -w /lavoro/remotix "$2" \
		sh -c 'dpkg-buildpackage -b -us -uc' >"$3" 2>&1
}

uno() {
	local b=$1 imm="localhost/remotix-costruzione-$1" u="$OUTPUT/deb-$1"
	local c1="$CACHE/deb-$1-a" c2="$CACHE/deb-$1-b" deb outcome=0
	rm -rf "$u"; mkdir -p "$u"
	printf '== %s: image\n' "$b"
	podman build -t "$imm" -f "$HERE/Containerfile.$b" "$HERE" >"$u/immagine.log" 2>&1 \
		|| { echo "⛔ $b: image (see $u/immagine.log)"; return 1; }

	printf '== %s: package\n' "$b"
	prepare_copy "$c1" "$b" || return 1
	if ! build_in "$c1" "$imm" "$u/costruzione.log"; then
		echo "⛔ $b: dpkg-buildpackage failed (see $u/costruzione.log)"; tail -20 "$u/costruzione.log"
		return 1
	fi
	deb=$(cd "$c1" && ls remotix_*.deb | head -1)
	cp "$c1/$deb" "$c1"/remotix_*.buildinfo "$u/"
	echo "   $deb"

	printf '== %s: lintian and checks\n' "$b"
	podman run --rm -v "$u:/u:ro" "$imm" lintian -I --pedantic --no-tag-display-limit "/u/$deb" \
		>"$u/lintian.txt" 2>&1
	# R13 positive: rcp.o with BENCH_ON 1, same flags as the Makefile
	rm -rf "$c1/positivo"; cp -a "$c1/remotix/src" "$c1/positivo"
	sed -i 's/^#define BENCH_ON 0$/#define BENCH_ON 1/' "$c1/positivo/rcp.c"
	podman run --rm --userns=keep-id -v "$c1:/lavoro" -w /lavoro/positivo "$imm" \
		sh -c 'make TWIN=none BENCH=1 rcp.o >/dev/null 2>&1' >/dev/null 2>&1
	podman run --rm -v "$u:/u:ro" -v "$c1:/c:ro" "$imm" sh -c '
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
		echo "Depends:    $(dpkg-deb -f /u/'"$deb"' Depends)"
		echo "Recommends: $(dpkg-deb -f /u/'"$deb"' Recommends)"
		echo "Static:     $(dpkg-deb -f /u/'"$deb"' Static-Built-Using)"
		echo "Conffiles:"; dpkg-deb --ctrl-tarfile /u/'"$deb"' | tar -xO ./conffiles | sed "s/^/  /"
	' >"$u/controlli.txt" 2>&1
	dpkg-deb -c "$u/$deb" >"$u/elenco.txt"

	if [ "${TWICE:-0}" = 1 ]; then
		printf '== %s: second build (R23)\n' "$b"
		prepare_copy "$c2" "$b" || return 1
		if build_in "$c2" "$imm" "$u/costruzione-2.log"; then
			if cmp -s "$c1/$deb" "$c2/$deb"; then
				echo "R23 riproducibile SI ($(sha256sum <"$u/$deb" | cut -c1-16)… identical in two clean copies)" >>"$u/controlli.txt"
			else
				echo "R23 riproducibile NO (the two .deb files differ)" >>"$u/controlli.txt"
				cp "$c2/$deb" "$u/seconda-$deb"
			fi
		else
			echo "R23 riproducibile NO (second build failed)" >>"$u/controlli.txt"
		fi
	fi
	grep -q ' NO' "$u/controlli.txt" && outcome=1
	sed 's/^/   /' "$u/controlli.txt"
	printf '   lintian: %s\n' "$(grep -cE '^[EWIP]: ' "$u/lintian.txt") lines (E=$(grep -c '^E: ' "$u/lintian.txt") W=$(grep -c '^W: ' "$u/lintian.txt"))"
	return $outcome
}

state=0
for b in "$@"; do uno "$b" || state=1; done
exit $state
