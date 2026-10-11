#!/bin/bash
#
# build-in-container.sh — ⭐ THE ANSWER TO THE QUESTION "HOW IS IT BUILT"
#
#   bash src/build-in-container.sh              builds `src/remotix`
#   bash src/build-in-container.sh deps   only says what is there
#   bash src/build-in-container.sh clean      throws away the objects
#   bash src/build-in-container.sh <other>      passes it to `make`
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
#    host's — the three dead ends are listed in `src/Containerfile`.
#
# ---------------------------------------------------------------------------
# ⚠ THE MOUNT IS THE WHOLE TREE, not `src/`, and the reason is the `Makefile`:
#   the `fingerprints` target compares `src/rcp.c` with `../benches/rcp/rcp.c` and
#   REFUSES to compile if it does not find it (finding R12.3).  ⛔ Mounting only
#   `src/` the twin copy would vanish, and the `Makefile` would say — rightly —
#   "I could not look".
#
# ⚠ `:Z` is NOT used: on this machine SELinux does not label, and `:Z`
#   would rewrite the labels of the user's source tree.
set -uo pipefail

TREE=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
IMAGE=${IMAGE:-localhost/remotix-costruzione}
ACTION=${1:-all}

if ! command -v podman >/dev/null 2>&1; then
	printf '⛔ podman is not there%s: and the container is the only way that builds.\n' ""
	exit 2
fi

# ⛔ The image is CHECKED, and its absence is not a fault to be guessed:
#    it is a line that says the command to type.
if ! podman image exists "$IMAGE"; then
	printf '⛔ image «%s» is not there yet.  It is built once only:\n\n' "$IMAGE"
	printf '    podman build -t remotix-costruzione -f %s/src/Containerfile %s/src\n\n' \
	       "$TREE" "$TREE"
	printf '   (~4 minutes: nghttp3 and ngtcp2 are built from source inside it,\n'
	printf '    because%s Debian packages are 1.8 and 1.11 and the\n' ""
	printf '    ngtcp2_crypto_ossl bridge is NOT in the packages at all.)\n'
	exit 3
fi

# ⛔ `--userns=keep-id`: the files that come out must be the USER's, not a
#    remapped uid's.  Without it, `src/remotix` is born owned by a user that
#    does not exist on the host, and the next `git status` shows a tree that
#    cannot be touched any more without `sudo` — that is tonight's block, moved.
printf '== build inside «%s» — tree %s\n' "$IMAGE" "$TREE"
podman run --rm \
	--userns=keep-id \
	-v "$TREE:/albero" \
	-w /albero/src \
	"$IMAGE" \
	make "$ACTION"
output=$?

if [ $output -eq 0 ] && [ "$ACTION" = all ]; then
	if [ -x "$TREE/src/remotix" ]; then
		printf '\n⭐ built: %s\n' "$TREE/src/remotix"
		ls -l "$TREE/src/remotix"
	fi

	# ⛔⛔⭐ AND THE `rcp.c` BENCH RUNS HERE, at every build — 16 August 2026.
	#
	#   `[M]` `benches/04-b31-canvas.c` — 19 cases (20 since 11 Oct 2026), the strongest bench we have
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
	# ⛔ 11 Oct 2026: it runs INSIDE the build image, like everything else here.
	#   It used to need `gcc` on the host, and the host that builds (the server)
	#   has none: the bench was skipped in silence.  And since 7e15ae5 (bench
	#   translated to English) it grepped the Italian line «passed … failed 0»,
	#   which no longer exists.  Meanwhile 04-b31 was red, 17 of 19, from 22 Sep
	#   (0b84a5b, a product rule the bench had not followed), and no alarm fired.
	#   ⇒ A line that is not found is now a red too, not a silence.
	if [ -f "$TREE/benches/04-b31-canvas.c" ] && [ -f "$TREE/src/rcp.c" ]; then
		LINE=$(podman run --rm --userns=keep-id -v "$TREE:/albero" -w /albero \
		        "$IMAGE" sh -c 'gcc -O1 -std=gnu11 -w -D_GNU_SOURCE -o /tmp/b31 \
		            benches/04-b31-canvas.c src/rcp.c && /tmp/b31' 2>&1 \
		       | grep -a 'passed [0-9]*, failed')
		case "$LINE" in
		*"failed 0"*) printf '⭐ 04-b31 (the canvas, %s)\n' "$(echo $LINE)" ;;
		*)            printf '\n⛔ 04-b31 IS RED:%s\n' "${LINE:- it did not build or did not print its total line}"
		              printf '   rerun it with:  gcc -O1 -std=gnu11 -w -D_GNU_SOURCE \\\n'
		              printf '        -o /tmp/b31 benches/04-b31-canvas.c src/rcp.c && /tmp/b31\n' ;;
		esac
	fi
fi
exit $output
