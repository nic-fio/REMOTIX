#!/bin/bash
#
# 17-t10-giro.sh — phase 17, T10: the 17-t10.sh round on several machines, FOUR at a time (§7.1).
#
#   (on the server, as nicfio)   VERSIONE_N1=0.18.1-2 bash 17-t10-giro.sh <macchina>[:iso] …
#     e.g. bash 17-t10-giro.sh debian13-gnome debian13-gnome:iso fedora44-kde arch-lxqt
#     without arguments: the whole matrix (26 «cliente» + 6 «iso»)
#
# Every machine writes into t10/esiti/<m>/ and one line into t10/giro.log; the summary at the bottom here.
# The two releases: t10/run-N.run and run-N1.run (packaging/rilascio.sh), with their .sha256 (17-t10.sh).
# ⚠ 10 Oct 2026 (DECISIONI §10.36, phase 19): REMOTIX wants a card that encodes; in a VM the
#   preflight check refuses it (RX-GPU-*): the real round is done in a BOX with the server's card
#   (<macchina>:scatola), and the boxes for all the combinations are still to be prepared.
set -uo pipefail
T10=${T10:-/media/REMOTIX/vm17/t10}
P=${PARALLELE:-4}
export VERSIONE_N1=${VERSIONE_N1:?the N+1 version, for example 0.18.1-2}
MATRICE="debian13-gnome debian13-kde debian13-xfce debian13-lxqt
ubuntu2604-gnome ubuntu2604-kde ubuntu2604-xfce ubuntu2604-lxqt
fedora44-gnome fedora44-kde fedora44-xfce fedora44-lxqt
arch-gnome arch-kde arch-xfce arch-lxqt
tumbleweed-gnome tumbleweed-kde tumbleweed-xfce tumbleweed-lxqt
leap16-gnome leap16-kde leap16-xfce leap16-lxqt
alma10-gnome alma10-kde
debian13-gnome:iso ubuntu2604-gnome:iso fedora44-gnome:iso arch-kde:iso tumbleweed-kde:iso alma10-gnome:iso"
[ $# -gt 0 ] && MATRICE="$*"
mkdir -p "$T10/esiti"
T0=$(date +%s)
echo "== T10 round $(date -u +%FT%TZ), $P at a time: $(echo $MATRICE | wc -w) machines" | tee -a "$T10/giro.log"
# shellcheck disable=SC2086
printf '%s\n' $MATRICE | xargs -P "$P" -I{} bash -c '
	x={}; m=${x%%:*}; s=${x#*:}; [ "$s" = "$x" ] && s=cliente
	nome=$m; [ "$s" = iso ] && nome=$m-iso; [ "$s" = scatola ] && nome=$m-scatola
	bash '"$T10"'/17-t10.sh "$m" "$s" >'"$T10"'/esiti/"$nome".log 2>&1
	tail -1 '"$T10"'/esiti/"$nome".log' 2>/dev/null
echo "== end in $(( ($(date +%s) - T0) / 60 )) min" | tee -a "$T10/giro.log"
