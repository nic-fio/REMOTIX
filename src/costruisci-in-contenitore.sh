#!/bin/bash
#
# costruisci-in-contenitore.sh — ⭐ THE ANSWER TO THE QUESTION "HOW IS IT BUILT"
#
#   bash src/costruisci-in-contenitore.sh              builds `src/remotix`
#   bash src/costruisci-in-contenitore.sh dipendenze   only says what is there
#   bash src/costruisci-in-contenitore.sh pulisci      throws away the objects
#   bash src/costruisci-in-contenitore.sh <other>      passes it to `make`
#
# ---------------------------------------------------------------------------
# ⛔ THE BLOCK THIS FILE BREAKS, and the date
#
# `fasi/rapporti/F4-IN-12-mandato-prossima-sessione.md` §3, 14 August 2026:
# *"I could not build the C.  And until it builds, every new line
# is code nobody has ever seen run.  ⇒ The first question for the
# next session is for the user: how is this project built?"*
#
# ⭐ The answer did not need the user, and it is not `/media/REMOTIX`:
#    **`podman` as a user, the tree mounted inside, the binary that comes out here.**
#    No `sudo` on the host — one is root only **inside** the container,
#    which is the only place where `apt` is needed.
#
# ⛔ And the container is NOT the test machine's: that one has `gcc` but
#    does not see `/media/REMOTIX`, and the `/srv/src` it shows is not the
#    host's — the three dead ends are listed in `src/Contenitore`.
#
# ---------------------------------------------------------------------------
# ⚠ THE MOUNT IS THE WHOLE TREE, not `src/`, and the reason is the `Makefile`:
#   the `impronte` target compares `src/rcp.c` with `../banchi/rcp/rcp.c` and
#   REFUSES to compile if it does not find it (finding R12.3).  ⛔ Mounting only
#   `src/` the twin copy would vanish, and the `Makefile` would say — rightly —
#   "I could not look".
#
# ⚠ `:Z` is NOT used: on this machine SELinux does not label, and `:Z`
#   would rewrite the labels of the user's source tree.
set -uo pipefail

ALBERO=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
IMMAGINE=${IMMAGINE:-localhost/remotix-costruzione}
AZIONE=${1:-tutto}

if ! command -v podman >/dev/null 2>&1; then
	printf '⛔ podman is not there%s: and the container is the only way that builds.\n' ""
	exit 2
fi

# ⛔ The image is CHECKED, and its absence is not a fault to be guessed:
#    it is a line that says the command to type.
if ! podman image exists "$IMMAGINE"; then
	printf '⛔ image «%s» is not there yet.  It is built once only:\n\n' "$IMMAGINE"
	printf '    podman build -t remotix-costruzione -f %s/src/Contenitore %s/src\n\n' \
	       "$ALBERO" "$ALBERO"
	printf '   (~4 minutes: nghttp3 and ngtcp2 are built from source inside it,\n'
	printf '    because%s Debian packages are 1.8 and 1.11 and the\n' ""
	printf '    ngtcp2_crypto_ossl bridge is NOT in the packages at all.)\n'
	exit 3
fi

# ⛔ `--userns=keep-id`: the files that come out must be the USER's, not a
#    remapped uid's.  Without it, `src/remotix` is born owned by a user that
#    does not exist on the host, and the next `git status` shows a tree that
#    cannot be touched any more without `sudo` — that is tonight's block, moved.
printf '== build inside «%s» — tree %s\n' "$IMMAGINE" "$ALBERO"
podman run --rm \
	--userns=keep-id \
	-v "$ALBERO:/albero" \
	-w /albero/src \
	"$IMMAGINE" \
	make "$AZIONE"
uscita=$?

if [ $uscita -eq 0 ] && [ "$AZIONE" = tutto ]; then
	if [ -x "$ALBERO/src/remotix" ]; then
		printf '\n⭐ built: %s\n' "$ALBERO/src/remotix"
		ls -l "$ALBERO/src/remotix"
	fi

	# ⛔⛔⭐ AND THE `rcp.c` BENCH RUNS HERE, at every build — 16 August 2026.
	#
	#   `[M]` `banchi/04-b31-tela.c` — 19 cases, the strongest bench we have
	#   on the most delicate module — stayed **11 of 18, red, for a whole
	#   day** without anybody noticing.  Not because it was hard
	#   to launch: because **nobody launched it**.
	#
	# ⚠ And the cure is NOT a launcher: of benches that judge themselves and
	#   run without a machine there is ONE, and a script to launch one is
	#   bureaucracy by another name — the user's words, "if the points do not
	#   touch the product it is just bureaucratic noise".
	#
	# ⇒ The cure is that it runs BY ITSELF, where one passes anyway: two seconds, and whoever
	#   compiles need remember nothing.  ⛔ And it does not stop the build: the
	#   binary is there and may be useful — but the red shows, and it is the only thing
	#   that was needed.
	if command -v gcc >/dev/null 2>&1 \
	   && [ -f "$ALBERO/banchi/04-b31-tela.c" ] && [ -f "$ALBERO/src/rcp.c" ]; then
		B=$(mktemp -u /tmp/04-b31.XXXXXX)
		if gcc -O1 -std=gnu11 -w -D_GNU_SOURCE -o "$B" \
		       "$ALBERO/banchi/04-b31-tela.c" "$ALBERO/src/rcp.c" 2>/dev/null; then
			if RIGA=$("$B" 2>&1 | grep -a passati); then
				case "$RIGA" in
				*"falliti 0"*) printf '⭐ 04-b31 (the canvas, %s):%s\n' \
				                      "$(echo "$RIGA" | tr -s ' ')" '' ;;
				*)             printf '\n⛔ 04-b31 IS RED:%s\n' "$RIGA"
				               printf '   rerun it with:  gcc -O1 -std=gnu11 -w -D_GNU_SOURCE \\\n'
				               printf '        -o /tmp/b31 banchi/04-b31-tela.c src/rcp.c && /tmp/b31\n' ;;
				esac
			fi
			rm -f "$B"
		fi
	fi
fi
exit $uscita
