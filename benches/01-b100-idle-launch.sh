#!/bin/bash
# ⭐ 1.5 (split on by default as root): this bench starts the product as container root and measures it as ONE process, as before; RX_SPLIT_OPT="" (set,
#    empty) lets the product split — then the container needs the user remotix and CAP_SYS_ADMIN for the walls: the live split proofs do that.
SPLITOPT=${RX_SPLIT_OPT---no-split}
# 01-b100-idle-launch.sh <product> [out] — B100 (01-b100-idle.py) against a REAL server, OUTSIDE the
# safety-net boxes: two private podman containers sharing ONE private network namespace (exactly
# 01-b10-launch.sh's scene), run TWICE with two pairs of short clocks:
#
#   phase A  --inactivity-s ${B100_INACTIVITY_A:-20} --abandon-s ${B100_ABANDON_A:-40}, cases a,b,c
#            (page messages only · a gesture every 5 s · the line dark 25 s, then back)
#   phase F  --inactivity-s ${B100_INACTIVITY_F:-40} --abandon-s 0, case f (the tab frozen, QUIC
#            alive: the inactivity ceiling LONGER than rcp.c's 30 s SILENCE, the product's order)
#   (B100_PHASES="A" or "F" runs one only.)
#
#   <product>  a product folder as rete11/prodotto is laid out: remotix, page.html, lib/.
#   [out]      the folder for A/ and F/: server.log, b100.jsonl, client.log (default ./b100-<time>)
#
# ⭐ The scene (as 01-b10-launch.sh): NO podman network, ONE private namespace.
#   · rxb100-server (NO --decoder-pace: it does not exist in 1.5, so PACE is left out of case a): the product in the
#     boxes' IMAGE (default localhost/rete11/xfce:p0), --network
#     none, --address :: port 7451, the product's libs into /usr/local/lib, one run user PER CASE
#     (rxidle<case>, the same password) in the card's group, the card ($CARD): a right password
#     reaches a REAL ADMITTED and SESSION.  ⚠ No system bus in there: the child stays «without a
#     stage» (no compositor), which these clocks do not need — they are rcp.c's and main.c's.
#   · rxb100-client: python3 + aioquic (the same image) joining the server's namespace; each case
#     from its own 127.0.0.x (all of 127/8 is local).
#   ⛔ Bounded: --cpus 2 --memory 2g each, nice 19 inside.
# Needs: `sudo -n podman` (or run as root).  Exit: the worst phase's (0 pass · 1 fail · 2 blind),
# 3 = a scene did not start.
set -u
PROD=$(readlink -f "${1:?product folder}")
OUT=${2:-b100-$(date +%Y%m%d-%H%M%S)}
BENCHES=$(dirname "$(readlink -f "$0")")
PAM=$BENCHES/../src/remotix.pam
IMG_SRV=${B100_SERVER_IMAGE:-localhost/rete11/xfce:p0}
IMG_CLI=${B100_CLIENT_IMAGE:-localhost/rete11/xfce:p0}
PORT=7451
CARD=${B100_CARD:-/dev/dri/renderD128}
PHASES=${B100_PHASES:-A F}
P() { if [ "$(id -u)" = 0 ]; then podman "$@"; else sudo -n podman "$@"; fi; }

for f in "$PROD/remotix" "$PROD/page.html" "$PAM" "$BENCHES/01-b100-idle.py" "$BENCHES/01-b3-client.py"; do
	[ -f "$f" ] || { echo "b100: missing $f"; exit 3; }
done
ls "$PROD"/lib/libngtcp2.so.* >/dev/null 2>&1 || { echo "b100: no ngtcp2 in $PROD/lib"; exit 3; }
mkdir -p "$OUT" || exit 3
OUT=$(readlink -f "$OUT")
SRV= CLI=
cleanup() { [ -n "$CLI" ] && P rm -f -t 3 "$CLI" >/dev/null 2>&1; [ -n "$SRV" ] && P rm -f -t 3 "$SRV" >/dev/null 2>&1; }
trap cleanup EXIT

# phase <name> <inactivity-s> <abandon-s> <cases> <seconds ceiling>
phase() {
	local name=$1 ina=$2 aba=$3 cases=$4 ceil=$5 d="$OUT/$1" users="" u rc
	mkdir -p "$d" || return 3
	cp "$PAM" "$d/remotix.pam"
	head -c 18 /dev/urandom | base64 | tr -d '/+=' > "$d/password"; chmod 644 "$d/password"
	for u in ${cases//,/ }; do users="$users rxidle$u"; done
	SRV=rxb100-server-$name-$$; CLI=rxb100-client-$name-$$
	P run -d --name "$SRV" --cpus 2 --memory 2g --network none --device "$CARD" --stop-signal TERM \
		-v "$PROD:/prod:ro" -v "$d:/idle" -e LD_LIBRARY_PATH=/prod/lib \
		--entrypoint sh "$IMG_SRV" -c "
		CARD_GID=\$(stat -c %g $CARD) &&
		{ getent group \$CARD_GID >/dev/null || groupadd -g \$CARD_GID rxrender; } &&
		for u in $users; do useradd -m \$u -s /bin/sh && echo \"\$u:\$(cat /idle/password)\" | chpasswd &&
		  usermod -aG \$(getent group \$CARD_GID | cut -d: -f1) \$u || exit 1; done &&
		cp /prod/lib/*.so* /usr/local/lib/ && ldconfig &&
		cp /idle/remotix.pam /etc/pam.d/remotix && mkdir -p /etc/remotix &&
		echo root > /etc/remotix/denied-users && chmod 644 /etc/remotix/denied-users &&
		exec nice -n 19 /prod/remotix --address :: $SPLITOPT --name 127.0.0.1 --port $PORT \
		  --certificates /idle/cert --page /prod/page.html --ban-file /idle/ban \
		  --command-socket /idle/cmd.sock --inactivity-s $ina --abandon-s $aba \
		  --verbose > /idle/server.log 2>&1" >/dev/null || return 3
	for _ in $(seq 60); do
		grep -q "⭐ ready: https://" "$d/server.log" 2>/dev/null && break
		[ "$(P inspect -f '{{.State.Running}}' "$SRV" 2>/dev/null)" = true ] || break
		sleep 0.5
	done
	grep -q "⭐ ready: https://" "$d/server.log" 2>/dev/null || {
		echo "b100 $name: the server did not say ready"; tail -20 "$d/server.log"; return 3; }
	echo "b100 $name: server ready (md5 $(md5sum "$PROD/remotix" | cut -c1-8)), --inactivity-s $ina --abandon-s $aba, cases $cases"
	P run -d --name "$CLI" --cpus 2 --memory 2g --network container:"$SRV" \
		-v "$BENCHES:/benches:ro" -v "$d:/idle" --entrypoint sh "$IMG_CLI" -c "
		exec nice -n 19 python3 -u /benches/01-b100-idle.py --address 127.0.0.1 --port $PORT \
		  --user-prefix rxidle --password-file /idle/password --cases $cases \
		  --inactivity-s $ina --abandon-s $aba \
		  --server-log /idle/server.log --output /idle/b100.jsonl > /idle/client.log 2>&1" >/dev/null || return 3
	P wait --condition=stopped "$CLI" >/dev/null 2>&1 &
	local w=$!
	for _ in $(seq "$ceil"); do kill -0 $w 2>/dev/null || break; sleep 1; done
	rc=$(P inspect -f '{{.State.ExitCode}}' "$CLI" 2>/dev/null)
	grep -E '"type": "(check|end)"' "$d/b100.jsonl" 2>/dev/null | cut -c1-300
	cleanup; SRV= CLI=
	echo "b100 $name: exit ${rc:-?} — $d"
	return "${rc:-3}"
}

worst=0
for ph in $PHASES; do
	case $ph in
	A) phase A "${B100_INACTIVITY_A:-20}" "${B100_ABANDON_A:-40}" a,b,c 180 ;;
	F) phase F "${B100_INACTIVITY_F:-40}" 0 f 120 ;;
	*) echo "b100: unknown phase $ph"; exit 3 ;;
	esac
	rc=$?
	[ $rc -gt $worst ] && worst=$rc
done
echo "b100: exit $worst — $OUT"
exit $worst
