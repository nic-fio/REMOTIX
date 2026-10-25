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
# ⭐ A line «??» is a check that could not be made (no card group, no cgroup scope for the desktop, no stand-in logind): it NEVER makes
#   the run green — the mode exits 3, or red.  LIVE_SKIP="l2,stage,logind" (a comma list) skips those checks ON PURPOSE and the run
#   says so.  l2: the card's groups; stage: fiona's desktop (a writable cgroup); logind: the stand-in on the system bus.
set -u
# ⛔ 24 Oct 2026: it rewrites /etc/passwd and PAM — refused outside a container.
[ -e /run/.containerenv ] || [ -e /.dockerenv ] || { echo "not in a container: refused (it rewrites /etc/passwd and PAM)"; exit 3; }
# ⭐ Both modes, one after the other: the root side without and WITH --journal (RX_LIVE_JOURNAL=1,
#   the package units' shape — 676af717: under --journal the network side's fork wrote into the
#   root channel).  LIVE_MODE=plain|journal runs one only.
# ⭐ 1.6 (R8 B): four modes — plain, journal (a stand-in journald; the _PID of the network side's lines), nologind (no
#   /run/systemd/sessions: the list is «could not look», nothing blocks) and rootdeath (the root side killed with -9: the network side
#   sees the EOF on its channel).
if [ -z "${LIVE_MODE:-}" ]; then
	LIVE_MODE=plain sh "$0"; r1=$?
	LIVE_MODE=journal sh "$0"; r2=$?
	LIVE_MODE=nologind sh "$0"; r3=$?
	LIVE_MODE=rootdeath sh "$0"; r4=$?
	echo "── live: plain $( [ $r1 = 0 ] && echo GREEN || echo RED) · journal $( [ $r2 = 0 ] && echo GREEN || echo RED) · nologind $( [ $r3 = 0 ] && echo GREEN || echo RED) · rootdeath $( [ $r4 = 0 ] && echo GREEN || echo RED)"
	[ $r1 = 0 ] && [ $r2 = 0 ] && [ $r3 = 0 ] && [ $r4 = 0 ] && { echo GREEN; exit 0; }
	{ [ $r1 = 1 ] || [ $r2 = 1 ] || [ $r3 = 1 ] || [ $r4 = 1 ]; } && { echo RED; exit 1; }
	exit 3
fi
[ "$LIVE_MODE" = journal ] && export RX_LIVE_JOURNAL=1 || export RX_LIVE_JOURNAL=0
# «??»: a check that could not be made is not a pass (see the header)
unk=0
unk_line() {
	case ",${LIVE_SKIP:-}," in
		*",$1,"*) echo "-- skipped on purpose (LIVE_SKIP has $1): $2" ;;
		*) echo "?? $2"; unk=1 ;;
	esac
}
# the network side's environment is an allow-list: only REMOTIX_* crosses
export RX_LIVE_MODE=$LIVE_MODE REMOTIX_LIVE_MODE=$LIVE_MODE REMOTIX_LIVE_JOURNAL=$RX_LIVE_JOURNAL
echo "── mode: $LIVE_MODE"
cd /albero/src || exit 3
[ "$(id -u)" = 0 ] || { echo "needs root (a privileged container)"; exit 3; }
make TWIN=none -j2 >/tmp/rx-make.log 2>&1 || { tail -20 /tmp/rx-make.log; exit 3; }
PK="gio-2.0 libpipewire-0.3 libdrm libva libva-drm vulkan opus libei-1.0 xkbcommon wayland-client gbm"
gcc -std=gnu11 -Wall -Wextra -I. $(pkg-config --cflags $PK) -o /tmp/rx-live-bin \
	../benches/02-rootside-live-test.c $(ls *.o | grep -v -e '^main.o$' -e '^walls.o$') \
	-lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm -lz \
	$(pkg-config --libs $PK) -ldl || exit 3
chmod 755 /tmp/rx-live-bin
# ⭐ 1.6 (R8 B): network_side_born_right() of main.c, case by case (main.c included, its main() renamed)
gcc -std=gnu11 -Wall -Wextra -Wno-unused-function -D_GNU_SOURCE -I. $(pkg-config --cflags $PK) -o /tmp/rx-bornright \
	../benches/02-bornright-test.c $(ls *.o | grep -v -e '^main.o$' -e '^walls.o$') \
	-lngtcp2_crypto_ossl -lngtcp2 -lnghttp3 -lssl -lcrypto -lpam -lm -lz \
	$(pkg-config --libs $PK) -ldl || rm -f /tmp/rx-bornright

for u in rxnet anna bruno carla dario elena fiona; do id "$u" >/dev/null 2>&1 || useradd -M -s /bin/sh "$u" || exit 3; done
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

# a process by its name, whoever's it is, as the container sees it (a zombie is counted: `Z`)
count_comm() { n=0; for c in /proc/[0-9]*/comm; do [ "$(cat "$c" 2>/dev/null)" = "$1" ] && n=$((n + 1)); done; echo $n; }
zombies() { n=0; for s in /proc/[0-9]*/status; do grep -q '^State:[[:space:]]*Z' "$s" 2>/dev/null && n=$((n + 1)); done; echo $n; }

# ⭐ 1.6 (R8 B): the two short modes
if [ "$LIVE_MODE" = nologind ] || [ "$LIVE_MODE" = rootdeath ]; then
	[ "$LIVE_MODE" = nologind ] && rm -rf /run/systemd/sessions
	/tmp/rx-live-bin > /tmp/rx-live/root.log 2>&1 &
	ROOT=$!
	red=0
	want=GREEN; [ "$LIVE_MODE" = rootdeath ] && want=ATTACHED
	i=0; while ! grep -q "^$want" /tmp/rx-live/net.txt 2>/dev/null && [ $i -lt 120 ]; do sleep 0.5; i=$((i + 1)); done
	grep -q "^$want" /tmp/rx-live/net.txt 2>/dev/null || { echo "NO the network side never wrote $want"; red=1; }
	cat /tmp/rx-live/net.txt 2>/dev/null
	if [ "$LIVE_MODE" = nologind ]; then
		grep -q '^NO ' /tmp/rx-live/net.txt && red=1
		grep -q 'could not look for live REMOTIX desktops' /tmp/rx-live/root.log || { echo "NO the root side did not say «could not look»"; red=1; }
		T0=$(date +%s); kill -TERM $ROOT; wait $ROOT; RC=$?; T1=$(date +%s)
		[ "$RC" = 0 ] && [ $((T1 - T0)) -le 6 ] || { echo "NO the root side stopped with $RC in $((T1 - T0)) s"; red=1; }
	else
		echo "── ps outside (the container's view) before the root side dies"
		ps -eo pid,ppid,user,stat,comm | grep -E 'PID|rx-live-bin'
		kill -KILL $ROOT; wait $ROOT 2>/dev/null
		i=0; while ! grep -q '^ROOT_EOF ' /tmp/rx-live/net.txt && [ $i -lt 50 ]; do sleep 0.2; i=$((i + 1)); done
		grep -q '^ROOT_EOF ' /tmp/rx-live/net.txt || { echo "NO the network side did not see the EOF of the dead root side"; red=1; }
		grep '^ROOT_EOF' /tmp/rx-live/net.txt
		sleep 1
		[ "$(count_comm rx-live-bin)" = 0 ] || { echo "NO a process of the live binary is still there after the root side's death"; ps -eo pid,ppid,user,stat,comm | grep rx-live-bin; red=1; }
	fi
	[ "$(zombies)" = 0 ] || { echo "NO $(zombies) zombie(s) left"; red=1; }
	echo "── mode $LIVE_MODE: $( [ $red = 0 ] && echo GREEN || echo RED)"
	exit $red
fi

# ⭐ 1.6 (R8 B): the stand-ins for logind (the system bus) and, in journal mode, for journald
export REMOTIX_LIVE_LOGIND=0
/tmp/rx-live-bin --logind > /tmp/rx-live/logind.log 2>&1 &
LG=$!
i=0; while [ ! -S /run/dbus/system_bus_socket ] && [ $i -lt 20 ]; do sleep 0.25; i=$((i + 1)); done
[ -S /run/dbus/system_bus_socket ] && export REMOTIX_LIVE_LOGIND=1
JD=
if [ "$LIVE_MODE" = journal ]; then
	/tmp/rx-live-bin --journald > /tmp/rx-live/journald.log 2>&1 &
	JD=$!
	i=0; while [ ! -S /run/systemd/journal/socket ] && [ $i -lt 20 ]; do sleep 0.25; i=$((i + 1)); done
fi

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
# ⭐ 1.6 (R8 B): kill -9 of the network side ALONE (the third), the root side stays: a fourth is born, and finds the desktops again
NP=$(grep -o 'network side started: pid [0-9]*' /tmp/rx-live/root.log | tail -1 | grep -o '[0-9]*$')
echo "── ps outside (the container's view) with the third network side up"
ps -eo pid,ppid,user,stat,comm | grep -E 'PID|rx-live-bin|rx-leftover|rx-stage'
PSOUT=$(ps -o user= -p "$NP" 2>/dev/null | tr -d ' ')
[ -n "$NP" ] && kill -KILL "$NP"
i=0; while [ ! -f /tmp/rx-live/restarted3.txt ] && [ $i -lt 90 ]; do sleep 0.5; i=$((i + 1)); done
sleep 0.5
T0=$(date +%s)
kill -TERM $ROOT
wait $ROOT
RC=$?
T1=$(date +%s)
[ -n "$JD" ] && kill $JD 2>/dev/null
kill $LG 2>/dev/null
sleep 1

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
# review 2, L1, 1.6 (R8 B): the second network side's forked leftover is gone — the kernel kills it with the namespace's PID 1 (the
# sweep of the root side is only a net now); it is found by its NAME from outside the namespace (its pid there means nothing here)
[ -f /tmp/rx-live/leftover.pid ] || { echo "NO the leftover was never started"; red=1; }
[ "$(count_comm rx-leftover)" = 0 ] || { echo "NO the leftover of the dead network side is still alive"; red=1; }
# ⭐ 1.6 (R8 B)
echo "── 1.6 R8 B"
echo "outside: the third network side was pid ${NP:-?}, user ${PSOUT:-?}; inside it is pid 1 (net.txt INSIDE line)"
[ "${PSOUT:-}" = rxnet ] && [ "${NP:-1}" != 1 ] || { echo "NO ps from outside does not show the network side as rxnet with a pid other than 1"; red=1; }
grep -q '^INSIDE pid=1 procs=1 $' /tmp/rx-live/net.txt || { echo "NO the network side did not see itself as the only process"; red=1; }
if grep -q '^STAGE ok' /tmp/rx-live/stage.txt 2>/dev/null; then
	grep -q '^FOUND_AGAIN_AFTER_RESTART n=1 user=fiona' /tmp/rx-live/restarted.txt || { echo "NO the restarted network side did not find fiona's desktop again"; red=1; }
	grep -q '^GONE_SEEN=1 user=fiona' /tmp/rx-live/restarted.txt || { echo "NO FOUND_GONE for fiona did not arrive"; red=1; }
	grep -q '^FOUND3 n=0' /tmp/rx-live/restarted2.txt || { echo "NO the third network side was told of a desktop that is gone"; red=1; }
	grep -q '^FOUND4 n=0' /tmp/rx-live/restarted3.txt || { echo "NO the fourth network side was told of a desktop that is gone"; red=1; }
else
	unk_line stage "no scope for fiona's desktop in this container ($(cat /tmp/rx-live/stage.txt 2>/dev/null)): FOUND_AGAIN across the restart could not look"
fi
grep -q 'RESTARTED3 uid=[1-9][0-9]* attached=1' /tmp/rx-live/restarted3.txt 2>/dev/null || { echo "NO after the kill -9 of the network side alone, no fourth one attached"; red=1; }
grep -q 'will be started again' /tmp/rx-live/root.log || { echo "NO the root side did not restart"; red=1; }
if [ "$REMOTIX_LIVE_LOGIND" = 1 ]; then
	grep -q 'sentinel_local(anna)' /tmp/rx-live/net.txt && ! grep -q '^NO sentinel' /tmp/rx-live/net.txt || { echo "NO the sentinel over the bus"; red=1; }
else
	unk_line logind "the stand-in logind did not start: the sentinel could not look"
fi
if [ "$LIVE_MODE" = journal ]; then
	NP1=$(grep -o 'network side started: pid [0-9]*' /tmp/rx-live/root.log | head -1 | grep -o '[0-9]*$')
	echo "journald saw: $(grep -c . /tmp/rx-live/journal.txt 2>/dev/null) line(s); the first network side was pid ${NP1:-?}"
	grep 'LIVE-NET-JOURNAL-MARK' /tmp/rx-live/journal.txt 2>/dev/null | head -2
	{ [ -n "$NP1" ] && grep -q "^pid=$NP1 .*LIVE-NET-JOURNAL-MARK" /tmp/rx-live/journal.txt 2>/dev/null; } \
		|| { echo "NO the network side's journal line did not arrive with its real pid ($NP1), the _PID journald records"; red=1; }
	grep -q '^pid=1 ' /tmp/rx-live/journal.txt 2>/dev/null && { echo "NO a line with pid 1: the pid was not translated"; red=1; }
fi
[ "$(zombies)" = 0 ] || { echo "NO $(zombies) zombie(s) left after the stop"; ps -eo pid,ppid,stat,comm | grep ' Z'; red=1; }
[ "$(count_comm rx-live-bin)" = 0 ] || { echo "NO a process of the live binary survived the stop"; ps -eo pid,ppid,user,stat,comm | grep rx-live-bin; red=1; }
# review 2, L4: the root side writes how long a birth took
grep -q 'the birth for «anna» took [0-9]* ms' /tmp/rx-live/root.log || { echo "NO no birth duration line"; red=1; }
# review 2, M1: a second CLOSE_ORPHAN for carla within 30 s is refused without a birth
grep -q 'CLOSE_ORPHAN for «carla» refused: one was already asked' /tmp/rx-live/root.log || { echo "NO a second CLOSE_ORPHAN for carla was not held"; red=1; }
# R1: right after her child left, the root side's own clock says carla is not abandoned yet
grep -q 'CLOSE_ORPHAN for «carla» refused: uid .* has not been without a client for' /tmp/rx-live/root.log || { echo "NO a CLOSE_ORPHAN for carla right after her child left was not refused TOO_SOON"; red=1; }
# finding 1: the CLOSE_ORPHAN child is born --close-only, the SPAWN child is not
grep -q -- 'argv remotix-child --internal-child carla .* --close-only' /tmp/rx-live/child.txt || { echo "NO carla's CLOSE_ORPHAN child is not --close-only"; red=1; }
grep -- 'argv remotix-child --internal-child anna ' /tmp/rx-live/child.txt | grep -q -- '--close-only' && { echo "NO anna's SPAWN child is --close-only"; red=1; }
# review 2, L2: the close-only birth enrols nobody in the card's groups
if grep -q 'FIRST CONNECTION: «anna»' /tmp/rx-live/root.log; then
	grep -q 'FIRST CONNECTION: «carla»' /tmp/rx-live/root.log && { echo "NO carla's close-only birth enrolled her in the card's groups"; red=1; }
	echo "OK anna (SPAWN) enrolled, carla (CLOSE_ORPHAN) not"
else
	unk_line l2 "no card group in this container: the L2 check could not look"
fi
# finding 3: only SIGPIPE ignored (bit 13 = 0x1000, as 1.0 passed it on), nothing blocked, nothing caught
grep -qx 'SigIgn:[[:space:]]*0000000000001000' /tmp/rx-live/child.txt || { echo "NO the child inherited ignored signals other than SIGPIPE (SIGHUP?)"; red=1; }
grep -qx 'SigBlk:[[:space:]]*0000000000000000' /tmp/rx-live/child.txt || { echo "NO the child was born with signals blocked"; red=1; }
grep -q 'broke the closed list' /tmp/rx-live/root.log || { echo "NO the malformed packet was not seen"; red=1; }
n=$(grep -c "broke the closed list" /tmp/rx-live/root.log); [ "$n" -le 1 ] || { echo "NO the closed list was broken $n times (once is the deliberate malformed packet)"; red=1; }
[ "$RC" = 0 ] || { echo "NO the root side exited $RC after SIGTERM"; red=1; }
[ $((T1 - T0)) -le 6 ] || { echo "NO the root side took $((T1 - T0)) s to stop"; red=1; }
echo "root side stopped in $((T1 - T0)) s, exit $RC"
# ⭐ the net.txt «??» lines of the network side (no desktop of fiona): not a pass either
grep -q '^?? ' /tmp/rx-live/net.txt && unk_line stage "the network side could not look at FOUND_AGAIN (net.txt)"
# ⭐ the final stop: the network sides install their SIGTERM handler as main() does, so the root side's stop must NOT need the SIGKILL
grep -q 'the network side did not stop within' /tmp/rx-live/root.log && { echo "NO the final stop needed the SIGKILL («did not stop within»): a network side left SIGTERM unhandled"; red=1; }
n2=$(grep -c 'closed its channel and did not exit within' /tmp/rx-live/root.log)
[ "$n2" = 1 ] || { echo "NO the SIGKILL of «closed its channel and did not exit within» happened $n2 times (once: the second network side, on purpose)"; red=1; }
# ⭐ the leftover: killed with the namespace, the root side's sweep must NOT have had to
grep -q "were still alive in this root side's cgroup" /tmp/rx-live/root.log && { echo "NO the root side's sweep found a leftover: the PID namespace did not kill it"; red=1; }
# ⭐ network_side_born_right(), the function itself, case by case (02-bornright-test.c)
if [ "$LIVE_MODE" = plain ]; then
	echo "── network_side_born_right()"
	if [ -x /tmp/rx-bornright ]; then
		/tmp/rx-bornright; rcb=$?
		[ "$rcb" = 0 ] || { echo "NO network_side_born_right: exit $rcb"; if [ "$rcb" = 3 ]; then unk=1; else red=1; fi; }
	else
		echo "NO the born-right test was not built"; red=1
	fi
fi
if [ $red = 0 ] && [ $unk = 0 ]; then echo "GREEN"; exit 0; fi
if [ $red = 0 ]; then echo "NOT RUN: a check could not look (see «??» above); LIVE_SKIP names the ones skipped on purpose"; exit 3; fi
echo "RED"; exit 1
