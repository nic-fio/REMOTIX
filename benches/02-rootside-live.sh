#!/bin/sh
# 02-rootside-live.sh — the root side LIVE (DECISIONS §11.50), see 02-rootside-live-test.c.
#
# On the server, from the tree root (a `git archive` of the branch):
#   sudo -n podman run --rm --privileged --network=none -v "$PWD:/albero" -w /albero \
#       localhost/remotix-costruzione sh benches/02-rootside-live.sh
#
# ⚠ It CHANGES the container's users and PAM (rxnet, anna, bruno, /etc/pam.d/remotix):
#   only in a throw-away container, never on a machine.
# Exit status: 0 green, 1 red, 3 could not look.
set -u
# ⛔ 24 Oct 2026: it rewrites /etc/passwd and PAM — refused outside a container.
[ -e /run/.containerenv ] || [ -e /.dockerenv ] || { echo "not in a container: refused (it rewrites /etc/passwd and PAM)"; exit 3; }
# ⭐ Both modes, one after the other: the root side without and WITH --journal (RX_LIVE_JOURNAL=1,
#   the package units' shape — 676af717: under --journal the network side's fork wrote into the
#   root channel).  LIVE_MODE=plain|journal runs one only.
if [ -z "${LIVE_MODE:-}" ]; then
	LIVE_MODE=plain sh "$0"; r1=$?
	LIVE_MODE=journal sh "$0"; r2=$?
	echo "── live: plain $( [ $r1 = 0 ] && echo GREEN || echo RED) · journal $( [ $r2 = 0 ] && echo GREEN || echo RED)"
	[ $r1 = 0 ] && [ $r2 = 0 ] && { echo GREEN; exit 0; }
	[ $r1 = 1 ] || [ $r2 = 1 ] && { echo RED; exit 1; }
	exit 3
fi
[ "$LIVE_MODE" = journal ] && export RX_LIVE_JOURNAL=1 || export RX_LIVE_JOURNAL=0
echo "── mode: $LIVE_MODE"
cd /albero/src || exit 3
[ "$(id -u)" = 0 ] || { echo "needs root (a privileged container)"; exit 3; }
make TWIN=none -j6 >/tmp/rx-make.log 2>&1 || { tail -20 /tmp/rx-make.log; exit 3; }
PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon wayland-client gbm"
gcc -std=gnu11 -Wall -Wextra -I. $(pkg-config --cflags $PK) -o /tmp/rx-live-bin \
	../benches/02-rootside-live-test.c $(ls *.o | grep -v -e '^main.o$' -e '^walls.o$') \
	-lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm -lz \
	$(pkg-config --libs $PK) -ldl || exit 3
chmod 755 /tmp/rx-live-bin

for u in rxnet anna bruno carla dario elena; do id "$u" >/dev/null 2>&1 || useradd -M -s /bin/sh "$u" || exit 3; done
# carla: a live REMOTIX session as logind writes it (CLOSE_ORPHAN's condition, finding 1)
mkdir -p /run/systemd/sessions || exit 3
printf 'UID=%s\nUSER=carla\nSTATE=active\nSERVICE=remotix\n' "$(id -u carla)" > /run/systemd/sessions/c77
# finding 9: two files that are bruno's, and that a chunked reader took for elena's — a
# 255-byte line whose tail reads «UID=elena», and a second UID= after the first
pad=$(awk 'BEGIN { for (i = 0; i < 247; i++) printf "x" }')
printf 'UID=%s\nDESKTOP=%sUID=%s\nSTATE=active\nSERVICE=remotix\n' "$(id -u bruno)" "$pad" "$(id -u elena)" \
	> /run/systemd/sessions/c78
printf 'UID=%s\nUID=%s\nSTATE=active\nSERVICE=remotix\n' "$(id -u bruno)" "$(id -u elena)" \
	> /run/systemd/sessions/c79
# the card's groups by number (the boxes name them; this image does not): the first
# birth then really runs usermod — the cost the SPAWN wait measures
for n in /dev/dri/renderD*; do
	[ -e "$n" ] || continue
	g=$(stat -c %g "$n")
	getent group "$g" >/dev/null || groupadd -g "$g" "rxcard$g"
done
echo 'anna:anna-pw' | chpasswd || exit 3
echo 'bruno:bruno-pw' | chpasswd || exit 3
echo 'dario:dario-pw' | chpasswd || exit 3
# elena: a passwd entry of 6000 bytes (finding 7: the root side's lookup grows past 4 KiB)
awk -F: -v OFS=: '$1 == "elena" { g = ""; for (i = 0; i < 6000; i++) g = g "x"; $5 = g } { print }' \
	/etc/passwd > /tmp/rx-passwd && cat /tmp/rx-passwd > /etc/passwd || exit 3
printf 'auth required pam_unix.so\naccount required pam_unix.so\nsession optional pam_permit.so\n' \
	> /etc/pam.d/remotix
rm -rf /tmp/rx-live && mkdir -m 1777 /tmp/rx-live
printf '# denied\nbruno\n' > /tmp/rx-live/denied-users

# review 3, F6: the product's root side refuses --certificates/--ban-file outside
# --network-state-dir (a 1.0 drop-in), with the fix in the line — before it binds anything
./remotix --network-user rxnet --name 127.0.0.1 --port 7999 --certificates /etc/rx-certs \
	--ban-file /var/lib/remotix/net/ban > /tmp/rx-live/f6-cert.log 2>&1
F6C=$?
./remotix --network-user rxnet --name 127.0.0.1 --port 7999 --certificates /var/lib/remotix/net/certificates \
	--ban-file /var/lib/remotix/ban > /tmp/rx-live/f6-ban.log 2>&1
F6B=$?

# lane 4's review M4: two variables outside the network side's allow-list, four inside it
RX_LIVE_SECRET=leak HOME_OF_ROOT=/root LANG=C.UTF-8 TZ=UTC REMOTIX_LIVE_SWITCH=1 DBUS_SYSTEM_BUS_ADDRESS=unix:path=/run/dbus/system_bus_socket PATH=/tmp/evil:$PATH \
	/tmp/rx-live-bin > /tmp/rx-live/root.log 2>&1 &
ROOT=$!
i=0
# the third network side (findings 2 and 10: the second closed its channel and ignored
# SIGTERM) and the hung child of dario reaped
while { [ ! -f /tmp/rx-live/restarted2.txt ] || ! grep -q 'child of «dario».*reaped by the root side' /tmp/rx-live/root.log; } \
	&& [ $i -lt 120 ]; do sleep 0.5; i=$((i + 1)); done
sleep 0.5
T0=$(date +%s)
kill -TERM $ROOT
wait $ROOT
RC=$?
T1=$(date +%s)

cat /tmp/rx-live/child-*.txt > /tmp/rx-live/child.txt 2>/dev/null
echo "── the network side's checks"
cat /tmp/rx-live/net.txt
echo "── the child"
cat /tmp/rx-live/child.txt 2>/dev/null || echo "(no child.txt)"
echo "── the restart"
cat /tmp/rx-live/restarted.txt 2>/dev/null || echo "(no restart)"
echo "── the root side's log (grep)"
grep -E 'enrol|ENROLLED|took|ROOT SIDE on|PAM helper started|network side started|broke the closed list|will be started again|child spawned for|reaped by the root side|refused BEFORE PAM|grant is minted|over the root|stopped|walls|did not leave|did not exit|closed its channel' /tmp/rx-live/root.log | cut -c1-220

red=0
grep -q '^NO ' /tmp/rx-live/net.txt && red=1
grep -q '^GREEN' /tmp/rx-live/net.txt || red=1
grep -q 'MALFORMED_SENT' /tmp/rx-live/net.txt || red=1
grep -q 'still alive' /tmp/rx-live/net.txt && red=1
grep -q 'RESTARTED uid=[1-9][0-9]* attached=1' /tmp/rx-live/restarted.txt 2>/dev/null || { echo "NO the network side was not started again"; red=1; }
grep -q -- '--parent-uid' /tmp/rx-live/child.txt 2>/dev/null || { echo "NO the child has no --parent-uid"; red=1; }
anna=$(id -u anna)
grep -q "^uid $anna $anna $anna" /tmp/rx-live/child.txt 2>/dev/null || { echo "NO the child is not anna"; red=1; }
# finding 2: dario's hung child, its network side dead: SIGTERM after the EOF grace, then SIGKILL, reaped
grep -q 'child of «dario».*did not leave within' /tmp/rx-live/root.log || { echo "NO dario's hung child got no SIGTERM after its network side died"; red=1; }
grep -q 'child of «dario».*reaped by the root side: killed by signal 9' /tmp/rx-live/root.log || { echo "NO dario's hung child was not SIGKILLed and reaped"; red=1; }
# finding 10: the second network side closed its channel and ignored SIGTERM: SIGKILL, a third one
grep -q 'closed its channel and did not exit within' /tmp/rx-live/root.log || { echo "NO the network side that ignored SIGTERM was not SIGKILLed"; red=1; }
grep -q 'RESTARTED2 uid=[1-9][0-9]* attached=1' /tmp/rx-live/restarted2.txt 2>/dev/null || { echo "NO no third network side"; red=1; }
# review 3, F6
{ [ "$F6C" != 0 ] && grep -q -- '--certificates /etc/rx-certs is not inside --network-state-dir.*Fix: .*Not starting' /tmp/rx-live/f6-cert.log; } \
	|| { echo "NO --certificates outside net/ was not refused with the fix (exit $F6C)"; cat /tmp/rx-live/f6-cert.log | tail -3; red=1; }
{ [ "$F6B" != 0 ] && grep -q -- '--ban-file /var/lib/remotix/ban is not inside --network-state-dir.*Not starting' /tmp/rx-live/f6-ban.log; } \
	|| { echo "NO --ban-file outside net/ was not refused (exit $F6B)"; tail -3 /tmp/rx-live/f6-ban.log; red=1; }
# review 2, L1: the second network side's forked leftover is killed before the third starts
grep -q 'were still alive in this root side.s cgroup before the network side' /tmp/rx-live/root.log || { echo "NO the dead network side's leftover was not swept"; red=1; }
lp=$(cat /tmp/rx-live/leftover.pid 2>/dev/null)
[ -n "$lp" ] && { [ ! -d "/proc/$lp" ] || grep -q '^State:[[:space:]]*Z' "/proc/$lp/status"; } || { echo "NO the leftover (pid ${lp:-?}) is still alive"; red=1; }
# review 2, L4: the root side writes how long a birth took
grep -q 'the birth for «anna» took [0-9]* ms' /tmp/rx-live/root.log || { echo "NO no birth duration line"; red=1; }
# review 2, M1: a second CLOSE_ORPHAN for carla within 30 s is refused without a birth
grep -q 'CLOSE_ORPHAN for «carla» refused: one was already asked' /tmp/rx-live/root.log || { echo "NO a second CLOSE_ORPHAN for carla was not held"; red=1; }
# finding 1: the CLOSE_ORPHAN child is born --close-only, the SPAWN child is not
grep -q -- 'argv remotix-child --internal-child carla .* --close-only' /tmp/rx-live/child.txt || { echo "NO carla's CLOSE_ORPHAN child is not --close-only"; red=1; }
grep -- 'argv remotix-child --internal-child anna ' /tmp/rx-live/child.txt | grep -q -- '--close-only' && { echo "NO anna's SPAWN child is --close-only"; red=1; }
# review 2, L2: the close-only birth enrols nobody in the card's groups
if grep -q 'FIRST CONNECTION: «anna»' /tmp/rx-live/root.log; then
	grep -q 'FIRST CONNECTION: «carla»' /tmp/rx-live/root.log && { echo "NO carla's close-only birth enrolled her in the card's groups"; red=1; }
	echo "OK anna (SPAWN) enrolled, carla (CLOSE_ORPHAN) not"
else
	echo "?? no card group in this container: the L2 check could not look"
fi
# finding 3: only SIGPIPE ignored (bit 13 = 0x1000, as 1.0 passed it on), nothing blocked, nothing caught
grep -qx 'SigIgn:[[:space:]]*0000000000001000' /tmp/rx-live/child.txt || { echo "NO the child inherited ignored signals other than SIGPIPE (SIGHUP?)"; red=1; }
grep -qx 'SigBlk:[[:space:]]*0000000000000000' /tmp/rx-live/child.txt || { echo "NO the child was born with signals blocked"; red=1; }
grep -q 'broke the closed list' /tmp/rx-live/root.log || { echo "NO the malformed packet was not seen"; red=1; }
n=$(grep -c "broke the closed list" /tmp/rx-live/root.log); [ "$n" -le 1 ] || { echo "NO the closed list was broken $n times (once is the deliberate malformed packet)"; red=1; }
[ "$RC" = 0 ] || { echo "NO the root side exited $RC after SIGTERM"; red=1; }
[ $((T1 - T0)) -le 6 ] || { echo "NO the root side took $((T1 - T0)) s to stop"; red=1; }
echo "root side stopped in $((T1 - T0)) s, exit $RC"
[ $red = 0 ] && echo "GREEN" || echo "RED"
exit $red
