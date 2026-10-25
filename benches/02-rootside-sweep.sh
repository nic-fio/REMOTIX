#!/bin/sh
# 02-rootside-sweep.sh — the sweep of a dead network side's leftovers kills only what lives in
# the root side's OWN cgroup (DECISIONS §11.50; review 2 L1 and its fix, 16 Oct 2026).
#
#   sudo -n podman run --rm --privileged --network=none -v "$PWD:/albero" -w /albero \
#       localhost/remotix-costruzione sh benches/02-rootside-sweep.sh
#
# Two root sides A and B, the SAME network user rxnet, each in a cgroup of its own (as two
# units would be).  A's network side forks a leftover and is killed -9; A starts a new one.
#   1. the leftover was alive after its network side's death (the sweep has work to do);
#   2. A's new network side is up and the leftover is DEAD (the sweep killed it);
#   3. B's network side — same uid, another cgroup — is the SAME process, alive.
# Exit 0 green, 1 red, 3 could not look.
set -u
cd /albero/src || exit 3
[ "$(id -u)" = 0 ] || { echo "needs root (a privileged container)"; exit 3; }
make TWIN=none -j6 >/tmp/rx-make.log 2>&1 || { tail -20 /tmp/rx-make.log; exit 3; }
PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon wayland-client gbm"
gcc -std=gnu11 -Wall -Wextra -I. $(pkg-config --cflags $PK) -o /tmp/rx-sweep-bin \
	../benches/02-rootside-sweep-test.c $(ls *.o | grep -v -e '^main.o$' -e '^walls.o$') \
	-lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm -lz \
	$(pkg-config --libs $PK) -ldl || exit 3
chmod 755 /tmp/rx-sweep-bin
id rxnet >/dev/null 2>&1 || useradd -M -s /bin/sh rxnet || exit 3
rm -rf /tmp/rx-sweep && mkdir -m 1777 /tmp/rx-sweep && : > /tmp/rx-sweep/denied
CG=/sys/fs/cgroup
mkdir -p $CG/rxsweepA $CG/rxsweepB 2>/dev/null
[ -w $CG/rxsweepA/cgroup.procs ] || { echo "no writable cgroup v2 here"; exit 3; }
sh -c "echo \$\$ > $CG/rxsweepA/cgroup.procs; exec /tmp/rx-sweep-bin root A" > /tmp/rx-sweep/A.log 2>&1 &
RA=$!
sh -c "echo \$\$ > $CG/rxsweepB/cgroup.procs; exec /tmp/rx-sweep-bin root B" > /tmp/rx-sweep/B.log 2>&1 &
RB=$!
red=0
ok() { echo "OK  $*"; }
no() { echo "NO  $*"; red=1; }
alive() { [ -n "$1" ] && kill -0 "$1" 2>/dev/null && [ "$(awk '{print $3}' /proc/$1/stat 2>/dev/null)" != Z ]; }
netof() { ls /tmp/rx-sweep/ | sed -n "s/^$1\.net\.//p" | sort -n | tail -1; }
for _ in $(seq 40); do [ -n "$(netof A)" ] && [ -n "$(netof B)" ] && [ -f /tmp/rx-sweep/A.leftover ] && break; sleep 0.25; done
NA=$(netof A); NB=$(netof B); LO=$(cat /tmp/rx-sweep/A.leftover 2>/dev/null)
echo "A root $RA net $NA (leftover $LO) · B root $RB net $NB"
[ -n "$NA" ] && [ -n "$NB" ] && [ -n "$LO" ] || { echo "the two network sides did not start"; tail -5 /tmp/rx-sweep/A.log; kill $RA $RB; exit 3; }
grep -q rxsweepA /proc/$LO/cgroup && grep -q rxsweepB /proc/$NB/cgroup || { echo "the cgroups did not take"; kill $RA $RB; exit 3; }
kill -9 "$NA"
sleep 0.3
alive "$LO" && ok "1. the leftover outlives its network side's death (uid $(stat -c %u /proc/$LO))" \
	|| no "1. the leftover died with its network side: nothing for the sweep to prove"
for _ in $(seq 40); do N2=$(netof A); [ -n "$N2" ] && [ "$N2" != "$NA" ] && break; sleep 0.25; done
sleep 0.3
[ -n "$N2" ] && [ "$N2" != "$NA" ] && alive "$N2" && ok "2a. A started a new network side ($N2)" || no "2a. A has no new network side"
alive "$LO" && no "2b. the leftover $LO is STILL alive after A's restart" || ok "2b. the leftover is dead: swept from A's own cgroup"
alive "$NB" && [ "$(netof B)" = "$NB" ] && ok "3. B's network side (same uid, another cgroup) is untouched: pid $NB alive" \
	|| no "3. B's network side was killed (pid $NB) — the sweep crossed into another server"
grep -a "were still alive in this root side's cgroup" /tmp/rx-sweep/A.log | cut -c1-200
grep -aq "were still alive" /tmp/rx-sweep/B.log && no "B swept something" || ok "B swept nothing"
kill -TERM $RA $RB 2>/dev/null; wait $RA $RB 2>/dev/null
rmdir $CG/rxsweepA $CG/rxsweepB 2>/dev/null
[ $red = 0 ] && echo GREEN || echo RED
exit $red
