#!/usr/bin/env bash
# costruisci-deb.sh — REMOTIX's .deb package, inside the target's container.
#
#     src/costruzione/costruisci-deb.sh debian13            # one
#     src/costruzione/costruisci-deb.sh debian13 ubuntu2604 # both
#     DUE=1 src/costruzione/costruisci-deb.sh debian13      # and test R23
#
# For each target (fasi/17-l-installatore.md §6.1-§6.4, step T3):
#   1. the image localhost/remotix-costruzione-<target> (Contenitore.<target>,
#      with the .deb tools layer at the end);
#   2. a COPY of the tree: src/, banchi/rcp/ (the twin the Makefile
#      compares) and packaging/debian/ as debian/; debian/changelog is WRITTEN
#      here, with the version and date of the commit (the date becomes
#      SOURCE_DATE_EPOCH: same source, same package — R23);
#   3. `dpkg-buildpackage -b` in the container, then lintian;
#   4. the checks on the FINISHED package, not on the tree:
#        R13  the bench function is not in the binary extracted from the .deb, and
#             is in an rcp.o built with BANCO_ACCESO 1 (the positive
#             control: without it, "not found" could mean "I cannot search");
#             and the unit passes no bench options;
#        R14  no bench file in the package's file list;
#        R4   `ldd` of the extracted binary in the container: no "not found",
#             no dynamic ngtcp2/nghttp3;
#        R23  with DUE=1 a second build in a second clean copy:
#             the .deb must be identical byte for byte.
#
# Output in $USCITA/deb-<target>/: the .deb, the .buildinfo, costruzione.log,
# lintian.txt, controlli.txt (one line per check, SI/NO).
# ⚠ No /tmp (on the laptop it is almost full): everything under $CACHE.
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
USCITA=${USCITA:-$ALBERO/costruzione-uscita}
CACHE=${CACHE:-$USCITA/.lavoro}
command -v podman >/dev/null 2>&1 || { echo "⛔ podman is not there"; exit 2; }
mkdir -p "$CACHE/tmp" "$USCITA"
export TMPDIR="$CACHE/tmp"
[ $# -gt 0 ] || set -- debian13 ubuntu2604

HASH=$(git -C "$ALBERO" rev-parse --short=7 HEAD)
DATA_R=$(git -C "$ALBERO" log -1 --format=%cD HEAD)
GIORNO=$(git -C "$ALBERO" log -1 --date=format:%Y%m%d --format=%cd HEAD)
SPORCO=""
if [ -n "$(git -C "$ALBERO" status --porcelain -- src packaging banchi/rcp THIRD-PARTY-LICENSES)" ]; then
	SPORCO=".modificato"
	echo "⚠ the tree has uncommitted changes in src/ packaging/ banchi/rcp/:"
	echo "  the version carries «$SPORCO» and the package does NOT match $HASH"
fi

prepara_copia() {  # prepara_copia <cartella> <bersaglio>
	local c=$1 b=$2 suff dist
	case $b in
	debian13)   suff=+deb13;       dist=trixie ;;
	ubuntu2604) suff=+ubuntu26.04; dist=resolute ;;
	*) echo "⛔ $b: not a .deb target"; return 2 ;;
	esac
	rm -rf "$c"; mkdir -p "$c/remotix/banchi"
	cp -a "$ALBERO/src" "$c/remotix/src"
	cp -a "$ALBERO/banchi/rcp" "$c/remotix/banchi/rcp"
	cp -a "$ALBERO/packaging/debian" "$c/remotix/debian"
	cp "$ALBERO/THIRD-PARTY-LICENSES" "$c/remotix/"
	rm -f "$c/remotix/src/remotix" "$c/remotix/src"/*.o \
	      "$c/remotix/src"/*-protocol.c "$c/remotix/src"/*-client-protocol.h
	# T8: RX_VERSIONE and RX_REVISIONE give the version of an archive RELEASE
	#     (0.17.0-2+deb13: the revision grows at every maintenance rebuild);
	#     without them, the test one with the commit, as in T3.
	if [ -n "${RX_VERSIONE:-}" ]; then
		VERSIONE="$RX_VERSIONE$SPORCO-${RX_REVISIONE:-1}$suff"
	else
		VERSIONE="0.17.0~git$GIORNO.$HASH$SPORCO-1$suff"
	fi
	cat >"$c/remotix/debian/changelog" <<EOF
remotix ($VERSIONE) $dist; urgency=medium

  * Built from $HASH$SPORCO (phase 17, T3).

 -- nicfio <nicfio@gmail.com>  $DATA_R
EOF
}

costruisci_in() {  # costruisci_in <copia> <immagine> <log>
	podman run --rm --userns=keep-id -v "$1:/lavoro" -w /lavoro/remotix "$2" \
		sh -c 'dpkg-buildpackage -b -us -uc' >"$3" 2>&1
}

uno() {
	local b=$1 imm="localhost/remotix-costruzione-$1" u="$USCITA/deb-$1"
	local c1="$CACHE/deb-$1-a" c2="$CACHE/deb-$1-b" deb esito=0
	rm -rf "$u"; mkdir -p "$u"
	printf '== %s: image\n' "$b"
	podman build -t "$imm" -f "$QUI/Contenitore.$b" "$QUI" >"$u/immagine.log" 2>&1 \
		|| { echo "⛔ $b: image (see $u/immagine.log)"; return 1; }

	printf '== %s: package\n' "$b"
	prepara_copia "$c1" "$b" || return 1
	if ! costruisci_in "$c1" "$imm" "$u/costruzione.log"; then
		echo "⛔ $b: dpkg-buildpackage failed (see $u/costruzione.log)"; tail -20 "$u/costruzione.log"
		return 1
	fi
	deb=$(cd "$c1" && ls remotix_*.deb | head -1)
	cp "$c1/$deb" "$c1"/remotix_*.buildinfo "$u/"
	echo "   $deb"

	printf '== %s: lintian and checks\n' "$b"
	podman run --rm -v "$u:/u:ro" "$imm" lintian -I --pedantic --no-tag-display-limit "/u/$deb" \
		>"$u/lintian.txt" 2>&1
	# R13 positive: rcp.o with BANCO_ACCESO 1, same flags as the Makefile
	rm -rf "$c1/positivo"; cp -a "$c1/remotix/src" "$c1/positivo"
	sed -i 's/^#define BANCO_ACCESO 0$/#define BANCO_ACCESO 1/' "$c1/positivo/rcp.c"
	podman run --rm --userns=keep-id -v "$c1:/lavoro" -w /lavoro/positivo "$imm" \
		sh -c 'make GEMELLO=nessuno rcp.o >/dev/null 2>&1' >/dev/null 2>&1
	podman run --rm -v "$u:/u:ro" -v "$c1:/c:ro" "$imm" sh -c '
		set -u
		d=$(mktemp -d); dpkg-deb -x /u/'"$deb"' "$d"
		bin=$d/usr/libexec/remotix/remotix
		frase="FUNZIONE DI BANCO e'"'"' ACCESA"
		n=$(strings "$bin" | grep -c "$frase")
		p=$(strings /c/positivo/rcp.o 2>/dev/null | grep -c "$frase")
		[ "$n" = 0 ] && [ "$p" -ge 1 ] && r=SI || r=NO
		echo "R13 banco-nel-binario $r (package: $n, positive control rcp.o with BANCO_ACCESO 1: $p)"
		o=$(grep "^ExecStart" $d/usr/lib/systemd/system/remotix.service | \
		     grep -oE -- "--(rilievo|comando-socket|audio-prova|parlantina|sblocca)" | sort -u | tr "\n" " ")
		[ -z "$o" ] && echo "R13 opzioni-di-banco-nell-unita SI (none)" \
		            || echo "R13 opzioni-di-banco-nell-unita NO ($o)"
		nere=$(dpkg-deb -c /u/'"$deb"' | awk "{print \$NF}" | \
		       grep -E "prova|sudoers|gpu-udev|riavvia-|ld\.so\.conf|provisiona|banchi|/opt/|\.pem$|\.key$" || true)
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

	if [ "${DUE:-0}" = 1 ]; then
		printf '== %s: second build (R23)\n' "$b"
		prepara_copia "$c2" "$b" || return 1
		if costruisci_in "$c2" "$imm" "$u/costruzione-2.log"; then
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
	grep -q ' NO' "$u/controlli.txt" && esito=1
	sed 's/^/   /' "$u/controlli.txt"
	printf '   lintian: %s\n' "$(grep -cE '^[EWIP]: ' "$u/lintian.txt") lines (E=$(grep -c '^E: ' "$u/lintian.txt") W=$(grep -c '^W: ' "$u/lintian.txt"))"
	return $esito
}

stato=0
for b in "$@"; do uno "$b" || stato=1; done
exit $stato
