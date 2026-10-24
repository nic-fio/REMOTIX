#!/bin/sh
# 02-net-move-links.sh — remotix-net-move never touches what a link in net/ points to
# (review 3 of the §11.50 split, F1 and F2).
#
# On the server, from the tree root (a `git archive` of the branch):
#   sudo -n podman run --rm --privileged --network=none -v "$PWD:/albero" -w /albero \
#       localhost/remotix-costruzione sh benches/02-net-move-links.sh
#
# ⚠ It CHANGES the container's users and /var/lib/remotix: only in a throw-away container.
# What it plants, as a hijacked old network side (uid remotix) could: in net/ a link to /, a
# link to /etc/shadow named «ban», a 0755 directory, and a symlinked page.key to a file
# remotix cannot read. Then it runs the move (and tmpfiles, if the container has it) and checks
# that /, /etc/shadow and the link targets kept their owner and mode, and that the unreadable
# certificate link is said loudly.
# Exit status: 0 green, 1 red, 3 could not look.
set -u
[ "$(id -u)" = 0 ] || { echo "needs root (a privileged container)"; exit 3; }
M=/albero/packaging/rpm/remotix-net-move
[ -x "$M" ] || chmod +x "$M" 2>/dev/null
id remotix >/dev/null 2>&1 || useradd -r -M -s /usr/sbin/nologin remotix || exit 3
N=/var/lib/remotix/net
rm -rf /var/lib/remotix && install -d -m 0755 /var/lib/remotix && install -d -m 0700 -o remotix -g remotix "$N" || exit 3
install -d -m 0700 -o remotix -g remotix "$N/certificates" || exit 3
ln -s / "$N/root-link"
ln -s /etc/shadow "$N/ban"
install -d -m 0755 -o remotix -g remotix "$N/opendir"
install -d -m 0700 /etc/letsencrypt/live/h && echo k > /etc/letsencrypt/live/h/privkey.pem && chmod 0600 /etc/letsencrypt/live/h/privkey.pem
ln -s /etc/letsencrypt/live/h/privkey.pem "$N/certificates/page.key"
ln -s /etc/letsencrypt/live/h/privkey.pem "$N/certificates/page.pem"

before() { stat -c '%U:%G %a' / /etc /etc/shadow /etc/letsencrypt/live/h/privkey.pem; }
B=$(before)
sh "$M" > /tmp/net-move.out 2>&1
RC=$?
if command -v systemd-tmpfiles >/dev/null 2>&1; then
	systemd-tmpfiles --create /albero/packaging/rpm/remotix.tmpfiles >> /tmp/net-move.out 2>&1
	echo "(systemd-tmpfiles --create run too)"
fi
A=$(before)
cat /tmp/net-move.out
red=0
[ "$RC" = 0 ] || { echo "NO the move exited $RC"; red=1; }
[ "$B" = "$A" ] || { echo "NO a link target changed:"; echo "before: $B"; echo "after:  $A"; red=1; }
[ "$B" = "$A" ] && echo "OK /, /etc, /etc/shadow and the certificate's target kept owner and mode"
grep -q "page.key is a link to .* CANNOT read" /tmp/net-move.out || { echo "NO the unreadable certificate link was not said"; red=1; }
grep -q "page.key is a link to .* CANNOT read" /tmp/net-move.out && echo "OK the unreadable certificate link is said, with the fix"
[ $red = 0 ] && echo GREEN || echo RED
exit $red
