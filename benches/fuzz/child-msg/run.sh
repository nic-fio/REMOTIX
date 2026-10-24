#!/bin/bash
# run.sh — runs the `child-msg` fuzz harness (built by build.sh) for a limited time, ONE process, at `nice -n 19`.
#   bash benches/fuzz/child-msg/run.sh [--seconds 60] [--build-dir DIR] [--out DIR] [--force]
# ⛔ It refuses to start (exit 5) unless `preflight.sh perf` (no --ripara) says OK.  --force skips the check.
# It writes its own «inizio» / «fine» lines in the shared diary (project remotix-15, «fuzzing: …»).
# A crash is saved as OUT/crash-* (libFuzzer -artifact_prefix); exit code 0 = no crash, 1 = crash saved, 4 = nothing to run.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SECONDS_MAX=60; BUILD=/media/REMOTIX-15/misure/fuzz/child-msg-build; OUT=""; FORCE=0
SHARE=${SHARE:-/media/server-share.txt}; IMAGE=${IMAGE:-localhost/remotix-fuzz}
while [ $# -gt 0 ]; do
	case "$1" in
	--seconds)   SECONDS_MAX=${2:-}; shift 2 ;;
	--build-dir) BUILD=${2:-}; shift 2 ;;
	--out)       OUT=${2:-}; shift 2 ;;
	--force)     FORCE=1; shift ;;
	*) echo "unknown argument: $1" >&2; exit 2 ;;
	esac
done
case "$SECONDS_MAX" in ''|*[!0-9]*|0) echo "--seconds wants a positive integer" >&2; exit 2 ;; esac
[ -x "$BUILD/bin/child-msg" ] || { echo "⛔ $BUILD/bin/child-msg is not there: run build.sh first" >&2; exit 4; }
[ -n "$OUT" ] || OUT=/media/REMOTIX-15/misure/fuzz/child-msg-$(date +%Y-%m-%d_%H%M)

# ⛔ It refuses to start unless the server is quiet: the perf profile of preflight.sh (no test, no chain, no open «inizio»
#    of another project in the shared diary, memory, boxes on the Intel).  No --ripara: it only looks.  --force skips it.
if [ "$FORCE" = 0 ]; then
	bash /media/REMOTIX-15/lavori/notti/preflight.sh perf --scheda intel --desktop gnome > /media/REMOTIX-15/tmp/p1b-child-msg-preflight.log 2>&1
	if [ $? -ne 0 ]; then
		echo "⛔ preflight (perf) is KO — not starting (exit 5):" >&2
		grep -E "^KO|PREFLIGHT" /media/REMOTIX-15/tmp/p1b-child-msg-preflight.log >&2
		exit 5
	fi
fi
mkdir -p "$OUT/corpus" || exit 2
cp "$BUILD"/seeds/child-msg/* "$OUT/corpus/" 2>/dev/null
INIZIO=$(date -u "+%F %H:%M"); COSA="fuzzing: child-msg (messaggi del figlio), 1 processo, ${SECONDS_MAX} s"
printf "%s | remotix-15 | inizio | %s | 1 core | 1 GB | %s s |\n" "$INIZIO" "$COSA" "$SECONDS_MAX" >> "$SHARE" 2>/dev/null
end() { printf "%s | remotix-15 | fine | [inizio %s] %s | - | - | -\n" "$(date -u "+%F %H:%M")" "$INIZIO" "$COSA" >> "$SHARE" 2>/dev/null; }
trap end EXIT
trap 'exit 130' INT TERM HUP
echo "== child-msg, ${SECONDS_MAX} s, output $OUT"
nice -n 19 ionice -c3 podman run --rm --cpus=1 --userns=keep-id -v "$BUILD:/build:ro" -v "$OUT:/out" -w /out "$IMAGE" \
	/build/bin/child-msg -max_total_time="$SECONDS_MAX" -artifact_prefix=/out/crash- -dict=/build/child-msg.dict \
	-rss_limit_mb=2048 -malloc_limit_mb=24 -print_final_stats=1 /out/corpus > "$OUT/run.log" 2>&1
rc=$?
tail -n 12 "$OUT/run.log"
ls "$OUT"/crash-* >/dev/null 2>&1 && { echo "⛔ a crash was saved: $(ls "$OUT"/crash-* | head -3 | tr '\n' ' ')"; exit 1; }
[ "$rc" -eq 0 ] || { echo "⛔ libFuzzer exited with $rc (see $OUT/run.log)"; exit 1; }
echo "⭐ no crash in ${SECONDS_MAX} s"
