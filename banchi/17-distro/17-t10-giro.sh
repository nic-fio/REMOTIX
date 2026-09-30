#!/bin/bash
#
# 17-t10-giro.sh — fase 17, T10: il giro di 17-t10.sh su più macchine, QUATTRO alla volta (§7.1).
#
#   (sul server, come nicfio)   VERSIONE_N1=0.18.1-2 bash 17-t10-giro.sh <macchina>[:iso] …
#     es. bash 17-t10-giro.sh debian13-gnome debian13-gnome:iso fedora44-kde arch-lxqt
#     senza argomenti: tutta la matrice (26 «cliente» + 6 «iso»)
#
# Ogni macchina scrive in t10/esiti/<m>/ e una riga in t10/giro.log; qui in fondo il riepilogo.
set -uo pipefail
T10=${T10:-/media/REMOTIX/vm17/t10}
P=${PARALLELE:-4}
export VERSIONE_N1=${VERSIONE_N1:?la versione N+1, per esempio 0.18.1-2}
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
echo "== giro T10 $(date -u +%FT%TZ), $P alla volta: $(echo $MATRICE | wc -w) macchine" | tee -a "$T10/giro.log"
# shellcheck disable=SC2086
printf '%s\n' $MATRICE | xargs -P "$P" -I{} bash -c '
	x={}; m=${x%%:*}; s=${x#*:}; [ "$s" = "$x" ] && s=cliente
	nome=$m; [ "$s" = iso ] && nome=$m-iso
	bash '"$T10"'/17-t10.sh "$m" "$s" >'"$T10"'/esiti/"$nome".log 2>&1
	tail -1 '"$T10"'/esiti/"$nome".log' 2>/dev/null
echo "== fine in $(( ($(date +%s) - T0) / 60 )) min" | tee -a "$T10/giro.log"
