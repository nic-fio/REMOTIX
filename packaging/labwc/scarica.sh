#!/usr/bin/env bash
# scarica.sh — fetches and VERIFIES the upstream sources of our labwc (DECISIONI §10.43).
#
#     packaging/labwc/scarica.sh DIR
#
# Into DIR (created if missing) the files named in VERSIONI: labwc's and wlroots' tarballs and
# wlroots' signature.  A file already there is not fetched again, but it is ALWAYS checked:
#   · every file against its sha256 in VERSIONI;
#   · wlroots' tarball against its signature, with the key kept here (wlroots-firma.asc), whose
#     fingerprint must be the one VERSIONI pins (Simon Ser, wlroots' release manager; checked on
#     11 Oct 2026 on keys.openpgp.org AND on his gitlab.freedesktop.org profile: the same key).
# labwc signs nothing: its tarball is GitHub's archive of the tag, pinned by sha256 (checked once
# against `git archive` of the tag: identical, §10.43).
# Exit 0 only when everything matches; then DIR is the exact corresponding source of the labwc we
# ship, together with this folder (the recipe).
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
DIR=${1:?usage: scarica.sh DIR}
mkdir -p "$DIR"

while read -r nome ver file sha url; do
	case $nome in '' | '#'*) continue ;; esac
	[ "$nome" = chiave ] && continue
	if [ ! -s "$DIR/$file" ]; then
		echo "   fetching $file"
		curl -fsSL --proto '=https' -o "$DIR/$file.parziale" "$url"
		chmod 0644 "$DIR/$file.parziale"
		mv "$DIR/$file.parziale" "$DIR/$file"
	fi
	echo "$sha  $DIR/$file" | sha256sum -c --quiet - ||
		{ echo "⛔ $DIR/$file: the sha256 is not the one in VERSIONI"; exit 1; }
done <"$QUI/VERSIONI"

IMPRONTA=$(awk '$1 == "chiave" { print $2 }' "$QUI/VERSIONI")
WLR=$(awk '$1 == "wlroots" { print $3 }' "$QUI/VERSIONI")
FIRMA=$(awk '$1 == "wlroots-firma" { print $3 }' "$QUI/VERSIONI")
G=$(mktemp -d "${TMPDIR:-/var/tmp}/remotix-gpg.XXXXXX")
trap 'rm -rf "$G"' EXIT
gpg --batch --quiet --homedir "$G" --import "$QUI/wlroots-firma.asc" 2>/dev/null
gpg --batch --homedir "$G" --with-colons --fingerprint | grep -q "^fpr:::::::::$IMPRONTA:\$" ||
	{ echo "⛔ wlroots-firma.asc is not the key $IMPRONTA"; exit 1; }
gpg --batch --homedir "$G" --status-fd 1 --verify "$DIR/$FIRMA" "$DIR/$WLR" 2>/dev/null |
	grep -q "^\[GNUPG:\] VALIDSIG $IMPRONTA " ||
	{ echo "⛔ $WLR: the signature is not valid for $IMPRONTA"; exit 1; }
echo "   sources verified in $DIR: $(awk '$1 == "labwc" || $1 == "wlroots" { printf "%s %s  ", $1, $2 }' "$QUI/VERSIONI")"
