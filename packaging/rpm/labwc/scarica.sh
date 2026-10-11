#!/usr/bin/env bash
# scarica.sh — fetches and VERIFIES the upstream source of our labwc for RHEL / Alma 10
# (DECISIONI §10.43).
#
#     packaging/rpm/labwc/scarica.sh DIR
#
# Into DIR (created if missing) the tarball named in VERSIONI.  Already there: not fetched again,
# but ALWAYS checked against the sha256 in VERSIONI (and the sha512 Fedora's dist-git publishes).
# Exit 0 only when it matches; then DIR + this folder are the exact corresponding source.
set -euo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DIR=${1:?usage: scarica.sh DIR}
mkdir -p "$DIR"
read -r _n VER FILE SHA URL < <(awk '$1 == "labwc"' "$HERE/VERSIONI")
SHA512=$(sed -n 's/^#   \([0-9a-f]\{128\}\)$/\1/p' "$HERE/VERSIONI")
if [ ! -s "$DIR/$FILE" ]; then
	echo "   fetching $FILE"
	curl -fsSL --proto '=https' -o "$DIR/$FILE.partial" "$URL"
	chmod 0644 "$DIR/$FILE.partial"
	mv "$DIR/$FILE.partial" "$DIR/$FILE"
fi
echo "$SHA  $DIR/$FILE" | sha256sum -c --quiet - || { echo "⛔ $DIR/$FILE: sha256 is not the one in VERSIONI"; exit 1; }
echo "$SHA512  $DIR/$FILE" | sha512sum -c --quiet - || { echo "⛔ $DIR/$FILE: sha512 is not Fedora's"; exit 1; }
echo "   labwc $VER verified in $DIR"
