#!/bin/sh
cd /media/REMOTIX/tmp/t2 || exit 1
for r in gnome-ferma kde-ferma xfce-ferma lxqt-ferma gnome-uccidi-padre kde-uccidi-padre xfce-uccidi-padre lxqt-uccidi-padre gnome-uccidi-figlio lxqt-uccidi-figlio; do
  A=$(sed -n 3p $r/azione.txt | cut -c8-19)
  PF=$(sed -n 2p $r/azione.txt)
  p=$(echo $PF | awk '{print $2}'); f=$(echo $PF | awk '{print $4}')
  mp=$(grep " MORTO  *$p " $r/vita.txt | head -1 | cut -c1-12)
  mf=$(grep " MORTO  *$f " $r/vita.txt | head -1 | cut -c1-12)
  # deaths of the user's processes (uid 4013) other than sleep/child/short commands
  mu=$(grep " MORTO " $r/vita.txt | grep "uid=4013" | grep -vE " sleep | $f |systemd-stdio|sd-pam|gnome-control-c|kioworker" | awk -v a="$A" '$1>=a' | wc -l)
  comp_prima=$(sed -n '/### processes of the user/,$p' $r/prima.txt | grep -E " (gnome-shell|kwin_wayland|labwc) " | awk '{print $5":"$1}' | tr '\n' ' ')
  comp_ri=$(sed -n '/### processes of the user/,$p' $r/riattacco.txt | grep -E " (gnome-shell|kwin_wayland|labwc) " | awk '{print $5":"$1}' | tr '\n' ' ')
  ult=$(tail -n1 $r/ore.txt 2>/dev/null | cut -c1-12)
  echo "$r | action $A | parent $p dead $mp | child $f dead $mf | other user deaths after the action: $mu | compositor before $comp_prima| at reattach $comp_ri| last terminal beat $(grep -A3 terminale $r/ore.txt | tail -1 | cut -c1-12)"
done
