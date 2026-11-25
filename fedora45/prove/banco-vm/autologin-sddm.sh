# guest: autos.sh on|off <user>   (TEST-BENCH ONLY: sddm autologin, a deterministic LOCAL login; restarts sddm)
[ "$(hostname)" = rx-lxqt ] || exit 9
f=/etc/sddm.conf.d/99-remotix-bench.conf
if [ "$1" = on ]; then mkdir -p /etc/sddm.conf.d; printf '[Autologin]\nUser=%s\nSession=lxqt-wayland\nRelogin=false\n' "$2" > $f; else rm -f $f; fi
cat $f 2>/dev/null | tr '\n' ' '; echo
[ "$3" = norestart ] && exit 0; systemctl reset-failed sddm 2>/dev/null; systemctl restart sddm
