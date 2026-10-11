#!/bin/bash
# ===========================================================================
# 11-c25 — ⭐⭐ «NOBODY BUT ROOT POWERS THE MACHINE OFF: THE POLKIT RULE IS IN
#   THE PACKAGES, ACTIVE» (DECISIONS.md §10.50, which withdrew §10.49's filter)
#
#   bash 11-c25-no-power-entries.sh [DIR]
#        DIR: where the built product packages are (default: the newest
#        costruzione-uscita/rilascio-*/prodotto of the tree)
#   exit 0 green · 1 red · 3 «I could not look»
#
# what must be true   : every product package (deb, rpm, Arch) installs
#                       src/remotix-no-poweroff.rules, byte for byte, as
#                       /usr/share/polkit-1/rules.d/50-remotix-no-poweroff.rules
#                       (polkit's vendor folder: active, owned by the package,
#                       removed with it); no copy left in /usr/share/remotix/belts/;
#                       the other two belts still there, inert.
# what it does not do : run polkit.  The rule's twelve actions and root's
#                       CAP_SYS_BOOT were measured on a real machine (§4.7,
#                       15 Aug 2026); with logind answering «no» the four desktops
#                       hide the entries by themselves (the boxes, §10.49).
# how                 : bsdtar in the Arch build image (it reads .deb, .rpm and
#                       .pkg.tar.zst alike), no network, nothing installed.
# ===========================================================================
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
DIR=${1:-$(ls -d "$TREE"/costruzione-uscita/rilascio-*/prodotto 2>/dev/null | sort -V | tail -1)}
RULE=usr/share/polkit-1/rules.d/50-remotix-no-poweroff.rules
IMG=localhost/remotix-costruzione-arch

[ -n "$DIR" ] && [ -d "$DIR" ] || { echo "3 — I could not look: no package folder ($DIR)"; exit 3; }
command -v podman >/dev/null || { echo "3 — I could not look: podman is not there"; exit 3; }
DIR=$(cd "$DIR" && pwd)

podman run --rm --network none -v "$DIR:/p:ro,Z" -v "$TREE/src/remotix-no-poweroff.rules:/rule:ro,Z" "$IMG" bash -c '
RULE='"$RULE"'
red=0; n=0
list() {   # the paths a package installs
	case "$1" in
	*.deb) m=$(bsdtar -tf "$1" | grep "^data\.tar") && bsdtar -xOf "$1" "$m" | bsdtar -tf - ;;
	*) bsdtar -tf "$1" ;;
	esac | sed "s|^\./||"
}
cat1() {   # one file of a package
	case "$1" in
	*.deb) m=$(bsdtar -tf "$1" | grep "^data\.tar") && bsdtar -xOf "$1" "$m" | bsdtar -xOf - "./$2" ;;
	*.rpm) bsdtar -xOf "$1" "./$2" ;;
	*) bsdtar -xOf "$1" "$2" ;;
	esac
}
while IFS= read -r f; do
	n=$((n + 1)); b=${f#/p/}; l=$(list "$f")
	bad=""
	grep -qx "$RULE" <<<"$l" || bad="$bad, no $RULE"
	grep -q "remotix/belts/50-remotix-no-poweroff.rules" <<<"$l" && bad="$bad, still in belts/"
	for k in remotix-no-suspend.conf remotix-power-keys.conf; do
		grep -qx "usr/share/remotix/belts/$k" <<<"$l" || bad="$bad, no belts/$k"
	done
	[ -z "$bad" ] && { cmp -s <(cat1 "$f" "$RULE") /rule || bad="$bad, the rule differs from src/"; }
	if [ -z "$bad" ]; then echo "  GREEN $b"; else echo "  RED   $b:${bad#,}"; red=1; fi
done < <(find /p \( -name "remotix_*.deb" -o -name "remotix-[0-9]*.rpm" -o -name "remotix-[0-9]*.pkg.tar.zst" \) ! -name "*.src.rpm" ! -path "*/.*" | sort)
[ "$n" -ge 7 ] || { echo "3 — I could not look: $n product packages in the folder, 7 expected"; exit 3; }
[ "$red" = 0 ] && { echo "GREEN — $n packages carry the rule, active"; exit 0; }
echo "RED"; exit 1
'
