#!/bin/sh
#
# ⛔ HISTORY (10 Oct 2026, DECISIONI §10.36): it uses the plan/approve/apply commands and the engine's
#   trial plan, which no longer exist on the command line. The same actions (D-Bus, gpasswd) are tested by
#   go test and the real run (banchi/17-distro/17-t10.sh). Do not launch it.
# Brings the freshly built engine to the server and launches a run in a VM (a single VM, ours):
#   prove/sul-server.sh debian <macchina> <pacchetto.deb>   → banchi/17-distro/17-t4-motore.sh
#   prove/sul-server.sh alma   <macchina>                   → banchi/17-distro/17-t4-alma.sh
set -eu
qui=$(cd "$(dirname "$0")/.." && pwd)
S=nicfio@192.168.0.2
T4=/media/REMOTIX/vm17/t4
"$qui/costruisci.sh" >/dev/null
ssh -o BatchMode=yes $S "mkdir -p $T4"
scp -q "$qui/uscita/remotix-install" "$qui/../banchi/17-distro/17-t4-motore.sh" "$qui/../banchi/17-distro/17-t4-alma.sh" \
	"$qui/../banchi/17-distro/17-t3-impronta.sh" "$qui/../banchi/17-distro/17-t3-impronta-rpm.sh" \
	"$qui/../banchi/17-distro/17-t3-impronta-arch.sh" $S:$T4/
case $1 in
debian)
	scp -q "$3" $S:$T4/
	ssh -o BatchMode=yes $S "cd $T4 && DESKTOP=${DESKTOP:-} R29=${R29:-} PIANO_OPZ='${PIANO_OPZ:-}' sg kvm -c 'bash 17-t4-motore.sh $2 $T4/remotix-install $T4/$(basename "$3")'" 2>&1 | grep -v tput ;;
alma)
	ssh -o BatchMode=yes $S "cd $T4 && sg kvm -c 'bash 17-t4-alma.sh $2 $T4/remotix-install'" 2>&1 | grep -v tput ;;
esac
