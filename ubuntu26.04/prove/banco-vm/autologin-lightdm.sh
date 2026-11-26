# guest: autox.sh on|off <user>   (TEST-BENCH ONLY: lightdm autologin, a deterministic LOCAL login; restarts lightdm)
# Xubuntu: session `xubuntu` (/usr/share/xsessions/xubuntu.desktop).  ⚠ A hypothesis to check in the VM (`ls /usr/share/xsessions`).
[ "$(hostname)" = rx-xubuntu ] || exit 9
f=/etc/lightdm/lightdm.conf.d/99-remotix-bench.conf
if [ "$1" = on ]; then mkdir -p /etc/lightdm/lightdm.conf.d; printf '[Seat:*]\nautologin-user=%s\nautologin-session=xubuntu\n' "$2" > $f; else rm -f $f; fi
cat $f 2>/dev/null | tr '\n' ' '; echo
[ "$3" = norestart ] || systemctl restart lightdm
