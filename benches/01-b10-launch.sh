#!/bin/bash
# ⭐ 1.5 (split on by default as root): this bench starts the product as container root and measures it as ONE process, as before; RX_SPLIT_OPT="" (set,
#    empty) lets the product split — then the container needs the user remotix and CAP_SYS_ADMIN for the walls: the live split proofs do that.
SPLITOPT=${RX_SPLIT_OPT---no-split}
# 01-b10-launch.sh <product> [out] — B10 (01-b10-flood.py) against a REAL server, on the test server,
# OUTSIDE the safety-net boxes: two private podman containers sharing ONE private network namespace.
#
#   <product>  a product folder as rete11/prodotto is laid out: remotix, page.html, lib/ (the
#              ngtcp2/nghttp3 it was linked with — server-product.sh copies them out of
#              remotix-costruzione).  The PAM file and the bench come from THIS script's tree
#              (../src/remotix.pam, ./01-b10-flood.py).
#   [out]      the folder for server.log, b10.jsonl, client.log (default ./b10-<time>)
#
# ⭐ The scene — NO podman network, nothing on the host's network: ONE private network namespace.
#   · rxb10-server: the product in the safety net's IMAGE (default localhost/rete11/xfce:p0, a container
#     of its own, never the box: it has the VA-API drivers remotix-costruzione lacks) with --network none
#     (a namespace of its own with only `lo`), --address :: (one socket for both families), port
#     7451, SMALL caps by default (--max-pending 16 --max-pending-per-address 4 --max-pending-per-48 8; B10_PENDING / B10_ADDRESS / B10_48 change them), the
#     product's Debian PAM file, a user made for the run, and the card ($CARD).  So the session child
#     (dropped to that user) can really start: the product's ngtcp2/nghttp3 libs — including
#     libngtcp2_crypto_ossl.so.0 — go into /usr/local/lib + ldconfig (LD_LIBRARY_PATH alone does not
#     reach the child), and the user is added to the card's group (gid 991 in the image, no named
#     group there).  A right password then reaches a REAL ADMITTED (the image has XFCE + labwc, so a
#     headless session comes up); B10 needs that verdict;
#   · rxb10-client: an image with python3 + aioquic (default the safety net's IMAGE
#     localhost/rete11/xfce:p0 — a container of its own, never the box) that JOINS the server's
#     namespace (--network container:rxb10-server).  The flood's sources: IPv4 127.0.0.100-139 (all
#     of 127/8 is local, no setup) and, with CAP_NET_ADMIN in that namespace only, 20 IPv6 addresses
#     in 10 /64s of fd5a:f100:d000::/48 put on its `lo`.  They vanish with the containers.
#   ⛔ Bounded: --cpus 2 --memory 2g each, nice 19 inside.
# Needs: `sudo -n podman` (or run as root).  Exit: the bench's (0 pass · 1 fail · 2 blind), 3 = the
# scene did not start.
set -u
BENCHES=$(dirname "$(readlink -f "$0")")
PAM=$BENCHES/../src/remotix.pam
SRV=rxb10-server-$$
CLI=rxb10-client-$$
IMG_SRV=${B10_SERVER_IMAGE:-localhost/rete11/xfce:p0}
IMG_CLI=${B10_CLIENT_IMAGE:-localhost/rete11/xfce:p0}
PORT=7451
# ⚠ The card: without it the server has no codec, and every HELLO ends in NOTHING_IN_COMMON (0x09)
#   before any login can be tried.  The admitted user's session child needs it too (it is in the
#   card's group), so a real ADMITTED is reached.
CARD=${B10_CARD:-/dev/dri/renderD128}
# ⭐ The caps under test: SMALL by default (16 / 4 / 8: quick, and the numbers are ours); the DEFAULTS of the product are
#   128 / 8 / 32 and can be tried live with B10_PENDING=128 B10_ADDRESS=8 B10_48=32.  Without the variables nothing changes.
#   B10_FLOOD_GAP  seconds a flood worker waits between two births (the server limits new handshakes to 4 a second per address, burst 16:
#                  the default 0.2-0.5 s is faster, and the excess is refused for RATE; see --flood-gap of 01-b10-flood.py)
#   B10_NFLOOD   flood addresses (default: enough for 1.5 workers per pending place, at least 10: 10 for 16/4, 24 for 128/8)
#   B10_CLIENT_MEM  the memory of the client container (default 2g; 4g for the defaults: ~190 aioquic connections)
#   B10_DRYRUN=1 prints the plan (caps, sources, /64s, workers, memory) and exits, touching no container.
PEND=${B10_PENDING:-16}; ADDR=${B10_ADDRESS:-4}; P48=${B10_48:-8}
for v in "$PEND" "$ADDR" "$P48" "${B10_NFLOOD:-1}"; do
	case "$v" in ''|*[!0-9]*) echo "b10: caps and B10_NFLOOD must be positive integers (got '$v')"; exit 3 ;; esac
	[ "$((10#$v))" -gt 0 ] || { echo "b10: caps and B10_NFLOOD must be positive integers (got '$v')"; exit 3; }
done
# 10# : "08" is a decimal here, not an invalid octal
PEND=$((10#$PEND)); ADDR=$((10#$ADDR)); P48=$((10#$P48))
[ -z "${B10_NFLOOD:-}" ] || B10_NFLOOD=$((10#$B10_NFLOOD))
NFLOOD=${B10_NFLOOD:-$(( (3 * PEND + 2 * ADDR - 1) / (2 * ADDR) ))}
[ -n "${B10_NFLOOD:-}" ] || [ "$NFLOOD" -ge 10 ] || NFLOOD=10
NV6=$(( P48 / 2 + 1 )); [ "$NV6" -ge 10 ] || NV6=10          # the /64s put on `lo`: the bench uses indexes 1 .. cap-48/2+1 (hex)
NV4=$(( NFLOOD + 4 )); [ "$NV4" -ge 40 ] || NV4=40            # IPv4 sources 127.0.0.100 ...: 4 + n-flood needed
# the IPv4 sources are 127.0.0.100 ... 127.0.0.(99 + NV4): the last octet must stay <= 255
[ $(( 99 + NV4 )) -le 255 ] || { echo "b10: B10_NFLOOD=$NFLOOD needs $NV4 IPv4 sources: 127.0.0.100-127.0.0.$(( 99 + NV4 )) is past .255 (at most $(( 255 - 99 - 4 )) flood addresses)"; exit 3; }
V4RANGE=127.0.0.100-127.0.0.$(( 99 + NV4 ))
CLIMEM=${B10_CLIENT_MEM:-2g}
case "$CLIMEM" in ''|*[!0-9kmg]*|*[kmg]*[0-9]*|*[kmg][kmg]*) echo "b10: B10_CLIENT_MEM must be <number>[kmg] (got '$CLIMEM')"; exit 3 ;; esac
case "$CLIMEM" in [0-9]*) ;; *) echo "b10: B10_CLIENT_MEM must be <number>[kmg] (got '$CLIMEM')"; exit 3 ;; esac
CAPS="--max-pending $PEND --max-pending-per-address $ADDR --max-pending-per-48 $P48"
# the bench's own check of the combination (no network, no aioquic): leave BEFORE starting any container
python3 "$BENCHES/01-b10-flood.py" --plan --cap-pending "$PEND" --cap-address "$ADDR" --cap-48 "$P48" --n-flood "$NFLOOD" \
	--v4-given "$NV4" --v6-64s-given "$NV6" || { echo "b10: the combination has problems (above): not starting"; exit 3; }
if [ "${B10_DRYRUN:-0}" = 1 ]; then
	echo "b10 plan: caps $PEND/$ADDR/$P48 · flood $NFLOOD addresses x $ADDR workers = $((NFLOOD * ADDR)) (places: $PEND) · IPv4 $V4RANGE ($NV4) · IPv6 /64s on lo: $NV6 (x2 addresses) · client memory $CLIMEM"
	exit 0
fi
PROD=$(readlink -f "${1:?product folder}")
OUT=${2:-b10-$(date +%Y%m%d-%H%M%S)}
P() { if [ "$(id -u)" = 0 ]; then podman "$@"; else sudo -n podman "$@"; fi; }

for f in "$PROD/remotix" "$PROD/page.html" "$PAM" "$BENCHES/01-b10-flood.py"; do
	[ -f "$f" ] || { echo "b10: missing $f"; exit 3; }
done
ls "$PROD"/lib/libngtcp2.so.* >/dev/null 2>&1 || { echo "b10: no ngtcp2 in $PROD/lib"; exit 3; }
mkdir -p "$OUT" || exit 3
OUT=$(readlink -f "$OUT")
cp "$PAM" "$OUT/remotix.pam"
PW=$(head -c 18 /dev/urandom | base64 | tr -d '/+=')
echo "$PW" > "$OUT/password"; chmod 644 "$OUT/password"

# ⚠ One at a time, the client FIRST: it lives in the server's namespace, and a single `rm` of both
#   leaves the server running («dependent containers», measured 15 Oct).
cleanup() { P rm -f -t 3 $CLI >/dev/null 2>&1; P rm -f -t 3 $SRV >/dev/null 2>&1; }
trap cleanup EXIT
P run -d --name $SRV --cpus 2 --memory 2g --network none --device "$CARD" --stop-signal TERM \
	-v "$PROD:/prod:ro" -v "$OUT:/flood" -e LD_LIBRARY_PATH=/prod/lib \
	--entrypoint sh "$IMG_SRV" -c "
	useradd -m rxflood -s /bin/sh && echo \"rxflood:\$(cat /flood/password)\" | chpasswd &&
	cp /prod/lib/*.so* /usr/local/lib/ && ldconfig &&
	CARD_GID=\$(stat -c %g $CARD) &&
	{ getent group \$CARD_GID >/dev/null || groupadd -g \$CARD_GID rxrender; } &&
	usermod -aG \$(getent group \$CARD_GID | cut -d: -f1) rxflood &&
	cp /flood/remotix.pam /etc/pam.d/remotix && mkdir -p /etc/remotix &&
	echo root > /etc/remotix/denied-users && chmod 644 /etc/remotix/denied-users &&
	ND=/flood && RD=/flood && NETA= && exec nice -n 19 /prod/remotix --address :: $SPLITOPT --name 127.0.0.1 --port $PORT \
	  --certificates \$ND/cert --page /prod/page.html --ban-file \$ND/ban \
	  --command-socket \$RD/cmd.sock \$NETA --verbose $CAPS > /flood/server.log 2>&1" >/dev/null || exit 3
for _ in $(seq 60); do
	grep -q "⭐ ready: https://" "$OUT/server.log" 2>/dev/null && break
	[ "$(P inspect -f '{{.State.Running}}' $SRV 2>/dev/null)" = true ] || break
	sleep 0.5
done
grep -q "⭐ ready: https://" "$OUT/server.log" 2>/dev/null || {
	echo "b10: the server did not say ready"; tail -20 "$OUT/server.log"; exit 3; }
echo "b10: server ready (md5 $(md5sum "$PROD/remotix" | cut -c1-8)), caps: $CAPS"

V6=fd5a:f100:d000
P run --name $CLI --cpus 2 --memory "$CLIMEM" --cap-add NET_ADMIN \
	--network container:$SRV \
	-v "$BENCHES:/benches:ro" -v "$OUT:/flood" --entrypoint sh "$IMG_CLI" -c "
	for i in \$(seq 1 $NV6); do
	  n=\$(printf %x \$i)
	  ip -6 addr add $V6:\$n::10/48 dev lo nodad && ip -6 addr add $V6:\$n::11/48 dev lo nodad || exit 3
	done
	exec nice -n 19 python3 -u /benches/01-b10-flood.py --address 127.0.0.1 --address6 ::1 --port $PORT \
	  --user rxflood --password-file /flood/password --v4-sources $V4RANGE \
	  --legit-source 127.0.0.50 --v6-prefix $V6 --cap-pending $PEND --cap-address $ADDR --cap-48 $P48 --n-flood $NFLOOD \
	  ${B10_FLOOD_GAP:+--flood-gap $B10_FLOOD_GAP} --server-log /flood/server.log --output /flood/b10.jsonl" 2>&1 | tee "$OUT/client.log"
rc=${PIPESTATUS[0]}
echo "b10: exit $rc — $OUT"
exit $rc
