#!/usr/bin/env bash
# t6-porta.sh — porta sul server il banco di T6, il motore e i pacchetti.
#
#   (sul portatile)   bash banchi/17-t6/t6-porta.sh [cartella-pacchetti]
#
#   /media/REMOTIX/vm17/t6/              t6-vm.sh, t6-leggi-pam.sh, 17-t1c-guarda.sh (con T1C_UTENTE),
#                                        17-t1c-browser.py, remotix-install
#   /media/REMOTIX/vm17/t6/pacchetti/    i pacchetti (.rpm, .deb, .pkg.tar.zst), una cartella per bersaglio
set -euo pipefail
QUI=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
ALBERO=$(cd "$QUI/../.." && pwd)
P=${1:-$ALBERO/costruzione-uscita}
S=nicfio@192.168.0.2
T=/media/REMOTIX/vm17/t6
ssh -o BatchMode=yes $S "mkdir -p $T/pacchetti" 2>&1 | grep -v tput || true
scp -q "$QUI/t6-vm.sh" "$QUI/t6-leggi-pam.sh" "$ALBERO/banchi/17-distro/17-t1c-guarda.sh" \
	"$ALBERO/banchi/17-distro/17-t1c-browser.py" "$ALBERO/installatore/uscita/remotix-install" $S:$T/
shopt -s nullglob
for d in "$P"/rpm/* "$P"/deb-* "$P"/pacchetto-arch; do
	[ -d "$d" ] || continue
	b=$(basename "$d"); b=${b#deb-}; b=${b/pacchetto-arch/arch}
	x=("$d"/*.rpm "$d"/*.deb "$d"/*.pkg.tar.zst)
	[ ${#x[@]} -gt 0 ] || continue
	ssh -o BatchMode=yes $S "rm -rf $T/pacchetti/$b && mkdir -p $T/pacchetti/$b" 2>&1 | grep -v tput || true
	for f in "$d"/*.rpm "$d"/*.deb "$d"/*.pkg.tar.zst; do
		case $f in *debuginfo*|*debugsource*|*.src.rpm|*dbgsym*|*'*'*) continue ;; esac
		scp -q "$f" $S:$T/pacchetti/$b/
	done
	echo "$b: $(ssh -o BatchMode=yes $S "ls $T/pacchetti/$b" 2>/dev/null | grep -v tput | tr '\n' ' ')"
done
