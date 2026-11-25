# guest: autos.sh on|off <user> [norestart]   (TEST-BENCH ONLY: sddm autologin, a deterministic LOCAL login; restarts sddm)
# KDE: Session=plasma (Wayland, the sddm default of Debian 13); LXQt: Session=lxqt (X11 + xfwm4: Debian has no LXQt Wayland session)
case "$(hostname)" in rx-deb-kde) S=plasma ;; rx-deb-lxqt) S=lxqt ;; *) exit 9 ;; esac
f=/etc/sddm.conf.d/99-remotix-bench.conf
if [ "$1" = on ]; then mkdir -p /etc/sddm.conf.d; printf '[Autologin]\nUser=%s\nSession=%s\nRelogin=false\n' "$2" "$S" > $f; else rm -f $f; fi
cat $f 2>/dev/null | tr '\n' ' '; echo
[ "$3" = norestart ] && exit 0; systemctl reset-failed sddm 2>/dev/null; systemctl restart sddm
