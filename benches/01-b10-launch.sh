#!/bin/bash
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
#     7451, SMALL caps (--max-pending 16 --max-pending-per-address 4 --max-pending-per-48 8), the
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
PROD=$(readlink -f "${1:?product folder}")
OUT=${2:-b10-$(date +%Y%m%d-%H%M%S)}
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
CAPS="--max-pending 16 --max-pending-per-address 4 --max-pending-per-48 8"
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
	ND=/flood && RD=/flood && NETA= && exec nice -n 19 /prod/remotix --address :: --name 127.0.0.1 --port $PORT \
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
P run --name $CLI --cpus 2 --memory 2g --cap-add NET_ADMIN \
	--network container:$SRV \
	-v "$BENCHES:/benches:ro" -v "$OUT:/flood" --entrypoint sh "$IMG_CLI" -c "
	for n in 1 2 3 4 5 6 7 8 9 a; do
	  ip -6 addr add $V6:\$n::10/48 dev lo nodad && ip -6 addr add $V6:\$n::11/48 dev lo nodad || exit 3
	done
	exec nice -n 19 python3 -u /benches/01-b10-flood.py --address 127.0.0.1 --address6 ::1 --port $PORT \
	  --user rxflood --password-file /flood/password --v4-sources 127.0.0.100-127.0.0.139 \
	  --legit-source 127.0.0.50 --v6-prefix $V6 --cap-pending 16 --cap-address 4 --cap-48 8 \
	  --server-log /flood/server.log --output /flood/b10.jsonl" 2>&1 | tee "$OUT/client.log"
rc=${PIPESTATUS[0]}
echo "b10: exit $rc — $OUT"
exit $rc
