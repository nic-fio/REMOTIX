#!/bin/sh
# riassunto.sh DIR — the pieces of the stage in prima/dopo/riattacco
cd /media/REMOTIX/tmp/t2/$1 || exit 1
for f in prima.txt dopo.txt riattacco.txt; do
  echo "##### $f"
  sed -n '/### loginctl list-sessions/,/### loginctl show-session/p' $f | grep -v "^###"
  sed -n '/### processes of the user/,$p' $f | awk '{print $1, $5, $6}' | grep -E "remotix|gnome-shell|gnome-session|kwin|plasmashell|startplasma|plasma_session|ksmserver|labwc|xfwm4|xfce4-session|xfce4-panel|xfdesktop|lxqt-session|lxqt-panel|pcmanfm|konsole|xfce4-termina|qterminal|gnome-terminal|systemd|pipewire " | tr '\n' ';'
  echo
done
