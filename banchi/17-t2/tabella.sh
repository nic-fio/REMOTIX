#!/bin/sh
cd /media/REMOTIX/tmp/t2 || exit 1
for r in gnome-ferma kde-ferma xfce-ferma lxqt-ferma gnome-uccidi-padre kde-uccidi-padre xfce-uccidi-padre lxqt-uccidi-padre gnome-uccidi-figlio lxqt-uccidi-figlio; do
  A=$(sed -n 3p $r/azione.txt | cut -c8-19)
  PF=$(sed -n 2p $r/azione.txt)
  p=$(echo $PF | awk '{print $2}'); f=$(echo $PF | awk '{print $4}')
  mp=$(grep " MORTO  *$p " $r/vita.txt | head -1 | cut -c1-12)
  mf=$(grep " MORTO  *$f " $r/vita.txt | head -1 | cut -c1-12)
  # morti di processi dell'utente (uid 4013) che non siano sleep/figlio/comandi brevi
  mu=$(grep " MORTO " $r/vita.txt | grep "uid=4013" | grep -vE " sleep | $f |systemd-stdio|sd-pam|gnome-control-c|kioworker" | awk -v a="$A" '$1>=a' | wc -l)
  comp_prima=$(sed -n '/### processi dell/,$p' $r/prima.txt | grep -E " (gnome-shell|kwin_wayland|labwc) " | awk '{print $5":"$1}' | tr '\n' ' ')
  comp_ri=$(sed -n '/### processi dell/,$p' $r/riattacco.txt | grep -E " (gnome-shell|kwin_wayland|labwc) " | awk '{print $5":"$1}' | tr '\n' ' ')
  ult=$(tail -n1 $r/ore.txt 2>/dev/null | cut -c1-12)
  echo "$r | azione $A | padre $p morto $mp | figlio $f morto $mf | altre morti utente dopo l'azione: $mu | compositore prima $comp_prima| al riattacco $comp_ri| ultimo battito terminale $(grep -A3 terminale $r/ore.txt | tail -1 | cut -c1-12)"
done
