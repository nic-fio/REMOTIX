#!/usr/bin/env bash
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): this bench tests an installer that no longer exists —
#   separate plan/approve/apply, signed archive and install.sh, third-party repositories, firewall and
#   belts set by the engine, answer files. Today: one .run, `install` with the [y/N] question, and
#   REMOTIX that does not modify the system. It stays as the history of the tests of 29 Sep - 1 Oct 2026; the real
#   run is banchi/17-distro/17-t10.sh. It is not launched.
# t6-porta.sh — brings the T6 bench, the engine and the packages to the server.
#
#   (on the laptop)   bash banchi/17-t6/t6-porta.sh [packages-folder]
#
#   /media/REMOTIX/vm17/t6/              t6-vm.sh, t6-leggi-pam.sh, 17-t1c-guarda.sh (with T1C_UTENTE),
#                                        17-t1c-browser.py, remotix-install
#   /media/REMOTIX/vm17/t6/pacchetti/    the packages (.rpm, .deb, .pkg.tar.zst), one folder per target
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
