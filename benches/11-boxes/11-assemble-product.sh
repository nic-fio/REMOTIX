#!/bin/bash
#
# 11-assemble-product.sh — ⭐ BUILDS THE FOLDER THE BOXES TAKE THE PRODUCT FROM
#
#   bash benches/11-boxes/11-assemble-product.sh            everything
#   bash benches/11-boxes/11-assemble-product.sh firefox    only the Firefox .deb
#
# ---------------------------------------------------------------------------
# WHY IT EXISTS
#
# `11-start.sh product` copies into each box what it finds in `/rete11/` —
# that is, in the folder `11-start.sh` itself sits in, mounted read-only:
#
#   rete11/prodotto/remotix            the binary
#   rete11/prodotto/page.html          the page
#   rete11/prodotto/remotix.pam        the PAM chain
#   rete11/prodotto/remotix-no-poweroff.rules, remotix-power-keys.conf
#   rete11/prodotto/01-b3-client.py    the test client
#   rete11/prodotto/lib/               ngtcp2, nghttp3, ... the ones the binary runs with
#   rete11/11-*, adapter.*, Containerfile.*, clipboard-gtk.py, 10-f1-witness.py,
#   rete11/tools-card-groups.sh        the benches the box runs, FLAT
#
# On the 1.0 server all that had been put there by hand, by earlier sessions,
# and was lost when the server was reinstalled (October 2026).  This script
# makes it again, from the repository, and can be run as many times as wanted.
#
# ⛔ IT DOES NOT COMPILE.  One binary, compiled once, copied identical into all
#    the boxes (see `product` in `11-start.sh`): the build is
#    `bash src/build-in-container.sh`, and this script only USES its result.
#    If the binary or the build image is missing it says so and stops (exit 3):
#    it never guesses and never builds on the quiet.
#
# ⚠ The libraries are taken from the BUILD IMAGE, not from the host's `/lib`:
#    `[M]` 26 August 2026 (see `product` in `11-start.sh`), same name `so.16`
#    and a different thing — the server dies at the first client.
#
# ⭐ The Firefox .deb (the box's Firefox is the HOST's one, recipe block 4-ter)
#    goes to `cache/apt-host/`: first `apt-get download` of the pinned version,
#    and if the Debian archive no longer has it (the point releases replace each
#    other), the exact file from snapshot.debian.org, checked by its SHA-1.
# ---------------------------------------------------------------------------
set -uo pipefail

HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
TREE=$(cd "$HERE/../.." && pwd)
BASE=${REMOTIX_BASE:-/media/REMOTIX-15}
DEST=${REMOTIX_RETE11:-$BASE/rete11}
CACHE_HOST=${REMOTIX_CACHE_HOST:-$BASE/cache/apt-host}
IMAGE=${IMAGE:-localhost/remotix-costruzione}
ACTION=${1:-all}

FF_VERSION=${FF_VERSION:-140.16.0esr-1~deb13u1}
FF_DEB="firefox-esr_${FF_VERSION}_amd64.deb"
# The file as snapshot.debian.org knows it (only for the pinned version).
FF_SHA1=15ff34b5e34e83cd1c27448c6eb80226e955168f

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }

# ---------------------------------------------------------------------------
# The Firefox .deb
# ---------------------------------------------------------------------------
firefox_deb()
{
	log "Firefox ESR $FF_VERSION in $CACHE_HOST"
	mkdir -p "$CACHE_HOST" || return 1
	if [ -f "$CACHE_HOST/$FF_DEB" ]; then
		ok "$FF_DEB is already there"
		return 0
	fi
	# 1. the archive (apt-get download needs no root; it writes in the cwd)
	if (cd "$CACHE_HOST" && apt-get download "firefox-esr=$FF_VERSION") >/dev/null 2>&1 \
	   && [ -f "$CACHE_HOST/$FF_DEB" ]; then
		ok "$FF_DEB downloaded with apt-get"
		return 0
	fi
	# 2. the snapshot, by the SHA-1 of the file
	inf "the archive does not have $FF_VERSION any more: trying snapshot.debian.org"
	if [ "$FF_VERSION" != "140.16.0esr-1~deb13u1" ]; then
		ko "no SHA-1 known for $FF_VERSION: pass the .deb in $CACHE_HOST by hand"
		return 1
	fi
	if curl -fsSL -o "$CACHE_HOST/$FF_DEB.part" "https://snapshot.debian.org/file/$FF_SHA1" \
	   && [ "$(sha1sum "$CACHE_HOST/$FF_DEB.part" | cut -d' ' -f1)" = "$FF_SHA1" ]; then
		mv "$CACHE_HOST/$FF_DEB.part" "$CACHE_HOST/$FF_DEB"
		ok "$FF_DEB downloaded from snapshot (SHA-1 checked)"
		return 0
	fi
	rm -f "$CACHE_HOST/$FF_DEB.part"
	ko "I could not get $FF_DEB (neither from the archive nor from snapshot)"
	return 1
}

if [ "$ACTION" = firefox ]; then
	firefox_deb
	exit $?
elif [ "$ACTION" != all ]; then
	echo "usage: $0 [all|firefox]" >&2
	exit 2
fi

# ---------------------------------------------------------------------------
# 1. What is needed and is not made here: the binary and the build image
# ---------------------------------------------------------------------------
log "The compiled product"
if [ ! -x "$TREE/src/remotix" ]; then
	ko "$TREE/src/remotix is not there: this script does not compile."
	printf '       build it first:  bash %s/src/build-in-container.sh\n' "$TREE"
	exit 3
fi
if ! command -v podman >/dev/null 2>&1 || ! podman image exists "$IMAGE" 2>/dev/null; then
	ko "the build image «$IMAGE» is not there (the libraries are taken from it)."
	printf '       build it:  podman build -t remotix-costruzione -f %s/src/Containerfile %s/src\n' "$TREE" "$TREE"
	exit 3
fi
for f in page.html remotix.pam remotix-no-poweroff.rules remotix-power-keys.conf; do
	[ -f "$TREE/src/$f" ] || { ko "$TREE/src/$f is missing from the repository"; exit 3; }
done
for f in 01-b3-client.py 10-f1-witness.py tools-card-groups.sh; do
	[ -f "$TREE/benches/$f" ] || { ko "$TREE/benches/$f is missing from the repository"; exit 3; }
done
ok "binary $(md5sum "$TREE/src/remotix" | cut -c1-8), image $IMAGE"

# ---------------------------------------------------------------------------
# 2. prodotto/
# ---------------------------------------------------------------------------
log "Assembling $DEST/prodotto"
mkdir -p "$DEST/prodotto/lib" || exit 1
# ⛔ The binary is removed before being put back: with a server running on it,
#    `cp` over it answers «Text file busy» (same lesson as `product`).
rm -f "$DEST/prodotto/remotix"
cp "$TREE/src/remotix" "$DEST/prodotto/remotix" || exit 1
for f in page.html remotix.pam remotix-no-poweroff.rules remotix-power-keys.conf; do
	cp "$TREE/src/$f" "$DEST/prodotto/$f" || exit 1
done
cp "$TREE/benches/01-b3-client.py" "$DEST/prodotto/" || exit 1
ok "binary, page, PAM chain, polkit/logind rules, test client"

# The libraries: those the binary resolves INSIDE the build image, under /usr/local
# (ngtcp2, ngtcp2_crypto_ossl, nghttp3).  `cp -L` puts the real file under the name
# the loader asks for (libngtcp2.so.16).  The system ones (openssl, pam, ...) the box has.
rm -f "$DEST"/prodotto/lib/*
podman run --rm --userns=keep-id \
	-v "$TREE:/albero:ro" -v "$DEST/prodotto/lib:/uscita" \
	"$IMAGE" sh -c '
		ldd /albero/src/remotix | awk "/=> \/usr\/local\//{print \$3}" | while read -r l; do
			cp -L "$l" /uscita/
		done
		ls /uscita' >"$DEST/prodotto/.lib-list"
n=$(wc -l <"$DEST/prodotto/.lib-list")
if [ "$n" -lt 3 ]; then
	ko "I expected at least libngtcp2, libngtcp2_crypto_ossl and libnghttp3 in the build image, I found $n:"
	sed 's/^/      /' "$DEST/prodotto/.lib-list"
	exit 3
fi
ok "libraries from the image: $(tr '\n' ' ' <"$DEST/prodotto/.lib-list")"
rm -f "$DEST/prodotto/.lib-list"

# ---------------------------------------------------------------------------
# 3. The benches the boxes run, flat in rete11/ (as `11-start.sh` expects:
#    `$BASE` = the folder of the script, mounted as /rete11)
# ---------------------------------------------------------------------------
log "Benches flat in $DEST"
rsync -a --exclude '*.jsonl' "$HERE"/ "$DEST"/ || exit 1
cp "$TREE/benches/10-f1-witness.py" "$TREE/benches/tools-card-groups.sh" "$DEST"/ || exit 1
ok "$(ls "$HERE" | wc -l) files of benches/11-boxes + 10-f1-witness.py + tools-card-groups.sh"

# ---------------------------------------------------------------------------
# 4. The Firefox .deb (the one the box recipes COPY from `pacchetti/`)
# ---------------------------------------------------------------------------
firefox_deb || exit 1

log "Ready"
inf "prodotto/remotix  $(md5sum "$DEST/prodotto/remotix" | cut -c1-8)  (src/remotix $(md5sum "$TREE/src/remotix" | cut -c1-8))"
inf "prodotto/page.html $(md5sum "$DEST/prodotto/page.html" | cut -c1-8)"
inf "next: sudo bash $DEST/11-start.sh build <desktop>   (only with the server free)"
exit 0
