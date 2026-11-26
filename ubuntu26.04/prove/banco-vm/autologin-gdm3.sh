# guest: autog.sh on|off <user> [norestart]   (TEST-BENCH ONLY: gdm3 autologin, a deterministic LOCAL login; restarts gdm3)
# Ubuntu: /etc/gdm3/custom.conf (section [daemon]); the session is the user's default (`ubuntu`).  Our own backup .rxbak is put back by `off`.
# ⚠ A hypothesis to check in the VM: that gdm3 reads custom.conf this way and starts the `ubuntu` session.
[ "$(hostname)" = rx-ubuntu ] || exit 9
f=/etc/gdm3/custom.conf
if [ "$1" = on ]; then
	grep -q '^\[daemon\]' $f || exit 9
	[ -f $f.rxbak ] || cp -p $f $f.rxbak
	sed -i '/^AutomaticLogin/d;/^\[daemon\]/a AutomaticLoginEnable=True\nAutomaticLogin='"$2" $f
else
	[ -f $f.rxbak ] && cp -p $f.rxbak $f && rm -f $f.rxbak
fi
grep -E '^AutomaticLogin' $f 2>/dev/null | tr '\n' ' '; echo
[ "$3" = norestart ] && exit 0; systemctl reset-failed gdm3 2>/dev/null; systemctl restart gdm3
