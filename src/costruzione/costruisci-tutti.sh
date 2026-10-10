#!/usr/bin/env bash
# costruisci-tutti.sh — builds REMOTIX for one target, for some, or for all.
#
#     src/costruzione/costruisci-tutti.sh                 # all
#     src/costruzione/costruisci-tutti.sh fedora44 arch   # only these
#
# For each target (fasi/17-l-installatore.md §6.2):
#   1. the image `localhost/remotix-costruzione-<target>` from Contenitore.<target>
#      (the first time a few minutes: nghttp3 and ngtcp2 are built static in it);
#   2. a COPY of the tree (src/ and banchi/rcp/) in $CACHE/albero-<target>:
#      `make` writes .o files and the binary next to the sources, and eight targets on the
#      same src/ would tread on each other's toes — and would dirty the src/remotix
#      of whoever is working;
#   3. `make pulisci tutto` inside the container;
#   4. in the output folder $USCITA/<target>/:
#        remotix          the binary (if it compiles)
#        immagine.log     the log of the image build
#        compilazione.log the make log
#        versioni.txt     OpenSSL, opus, libva, libei, pipewire, glib found
#        ldd.txt          `ldd remotix` INSIDE the target's container
#        esito.txt        one line: compiles yes/no, ldd clean yes/no
#
# ⚠ No /tmp: on the laptop it is almost full.  podman's TMPDIR and copies
#   of the tree live in $CACHE (default $USCITA/.lavoro, on disk):
#   on this laptop ~/.cache is a link to /tmp.
set -uo pipefail

QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
USCITA=${USCITA:-$ALBERO/costruzione-uscita}
CACHE=${CACHE:-$USCITA/.lavoro}
TUTTI=(debian13 ubuntu2604 ubuntu2404 fedora44 alma10 arch tumbleweed leap16)

command -v podman >/dev/null 2>&1 || { echo "⛔ podman is not there"; exit 2; }
mkdir -p "$CACHE/tmp" "$USCITA"
export TMPDIR="$CACHE/tmp"

if [ $# -eq 0 ] || [ "$1" = tutti ]; then set -- "${TUTTI[@]}"; fi

costruisci_uno()
{
	local b=$1 imm="localhost/remotix-costruzione-$1" u="$USCITA/$1" copia="$CACHE/albero-$1"
	local compila=no ldd_ok=- nota=""

	[ -f "$QUI/Contenitore.$b" ] || { echo "⛔ $b: Contenitore.$b is missing"; return 2; }
	rm -rf "$u"; mkdir -p "$u"
	printf '== %s: image\n' "$b"
	if ! podman build -t "$imm" -f "$QUI/Contenitore.$b" "$QUI" >"$u/immagine.log" 2>&1; then
		echo "$b compila=no immagine=NO (see immagine.log)" | tee "$u/esito.txt"
		return 1
	fi

	podman run --rm "$imm" sh -c '
		for m in openssl opus libva libei-1.0 libpipewire-0.3 glib-2.0; do
			printf "%-18s %s\n" "$m" "$(pkg-config --modversion $m 2>&1)"
		done
		printf "%-18s %s\n" gcc "$(cc -dumpfullversion 2>&1)"
		printf "%-18s %s\n" ngtcp2 "$(pkg-config --modversion libngtcp2 2>&1) (ours, static)"
		printf "%-18s %s\n" nghttp3 "$(pkg-config --modversion libnghttp3 2>&1) (ours, static)"
	' >"$u/versioni.txt" 2>&1

	printf '== %s: build\n' "$b"
	rm -rf "$copia"; mkdir -p "$copia/banchi"
	cp -a "$ALBERO/src" "$copia/src"
	cp -a "$ALBERO/banchi/rcp" "$copia/banchi/rcp"
	rm -f "$copia/src/remotix" "$copia/src"/*.o
	podman run --rm --userns=keep-id -v "$copia:/albero" -w /albero/src "$imm" \
		sh -c 'make pulisci >/dev/null && make tutto' >"$u/compilazione.log" 2>&1
	if [ -x "$copia/src/remotix" ]; then
		compila=si
		cp "$copia/src/remotix" "$u/remotix"
		podman run --rm -v "$u:/u:ro" "$imm" ldd /u/remotix >"$u/ldd.txt" 2>&1
		ldd_ok=si
		grep -q 'not found' "$u/ldd.txt" && { ldd_ok=no; nota="$nota librerie-mancanti"; }
		grep -qE 'ngtcp2|nghttp3' "$u/ldd.txt" && { ldd_ok=no; nota="$nota ngtcp2/nghttp3-dinamiche"; }
		# ⛔ phase 18: ffmpeg must NOT appear — neither linked nor in a symbol
		grep -qE 'libav|libswscale|libx26[45]' "$u/ldd.txt" && { ldd_ok=no; nota="$nota ffmpeg-collegato"; }
		# ⛔ phase 19: nor the software fallback
		grep -qiE 'openh264|SvtAv1' "$u/ldd.txt" && { ldd_ok=no; nota="$nota ripiego-software-collegato"; }
	else
		nota=" errors: $(grep -cE 'error:|Error [0-9]' "$u/compilazione.log") lines (see compilazione.log)"
	fi
	echo "$b compila=$compila ldd-pulito=$ldd_ok$nota" | tee "$u/esito.txt"
	[ $compila = si ] && [ $ldd_ok = si ]
}

stato=0
for b in "$@"; do costruisci_uno "$b" || stato=1; done
printf '\n== summary (%s)\n' "$USCITA"
for b in "$@"; do cat "$USCITA/$b/esito.txt" 2>/dev/null || echo "$b (no outcome)"; done
exit $stato
