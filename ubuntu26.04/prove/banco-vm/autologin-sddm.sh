# guest: autos.sh on|off <user> [norestart]   (TEST-BENCH ONLY: sddm autologin, a deterministic LOCAL login; restarts sddm)
# Kubuntu: Session=plasma (Wayland, the sddm default); Lubuntu: Session=Lubuntu (X11 + openbox: the xsession file is Lubuntu.desktop).
# ⚠ The session names are HYPOTHESES for Ubuntu 26.04: check `ls /usr/share/wayland-sessions /usr/share/xsessions` in the VM before the first run.
case "$(hostname)" in rx-kubuntu) S=plasma ;; rx-lubuntu) S=Lubuntu ;; *) exit 9 ;; esac
f=/etc/sddm.conf.d/99-remotix-bench.conf
if [ "$1" = on ]; then mkdir -p /etc/sddm.conf.d; printf '[Autologin]\nUser=%s\nSession=%s\nRelogin=false\n' "$2" "$S" > $f; else rm -f $f; fi
cat $f 2>/dev/null | tr '\n' ' '; echo
[ "$3" = norestart ] && exit 0; systemctl reset-failed sddm 2>/dev/null; systemctl restart sddm
