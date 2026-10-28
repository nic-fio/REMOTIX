#!/usr/bin/env bash
# fetch.sh — fetches and VERIFIES the upstream sources of our labwc that hosts KWin
# (PIANO.md «Correzione B»; same idea as the Alma labwc of DECISIONI §10.43).
#
#     packaging/labwc-ospite/fetch.sh DIR
#
# Into DIR (created if missing) the two tarballs named in VERSIONS.  Already there: not fetched
# again, but ALWAYS checked against the sha256 in VERSIONS.  Exit 0 only when both match; then
# DIR + this folder (the patch, build.sh) are the exact corresponding source.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DIR=${1:?usage: fetch.sh DIR}
mkdir -p "$DIR"
while read -r NAME VER FILE SHA URL; do
	if [ ! -s "$DIR/$FILE" ]; then
		echo "   fetching $FILE"
		curl -fsSL --proto '=https' -o "$DIR/$FILE.partial" "$URL"
		chmod 0644 "$DIR/$FILE.partial"
		mv "$DIR/$FILE.partial" "$DIR/$FILE"
	fi
	echo "$SHA  $DIR/$FILE" | sha256sum -c --quiet - || { echo "⛔ $DIR/$FILE: sha256 is not the one in VERSIONS"; exit 1; }
	echo "   $NAME $VER verified in $DIR"
done < <(grep -v '^#' "$HERE/VERSIONS" | grep .)
