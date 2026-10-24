#!/bin/bash
# run.sh — runs the `quic-conn` fuzz harness (built by build.sh) for a limited time, ONE process, at `nice -n 19`.
#   bash benches/fuzz/quic-conn/run.sh [--seconds 60] [--build-dir DIR] [--out DIR] [--force]
# ⛔ It refuses to start (exit 5) if the server is measuring (30-perf running, or an open «inizio» in /media/server-share.txt
#    that says MISURA / VALIDAZIONE / 30-perf): same criterion as run-fuzz.sh of lavori/fuzz.  --force skips the check.
# It writes its own «inizio» / «fine» lines in the shared diary (project remotix-15, «fuzzing: …»).
# A crash is saved as OUT/crash-* (libFuzzer -artifact_prefix); exit code 0 = no crash, 1 = crash saved, 4 = nothing to run.
set -uo pipefail
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
SECONDS_MAX=60; BUILD=/media/REMOTIX-15/misure/fuzz/quic-conn-build; OUT=""; FORCE=0
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
[ -x "$BUILD/bin/quic-conn" ] || { echo "⛔ $BUILD/bin/quic-conn is not there: run build.sh first" >&2; exit 4; }
[ -n "$OUT" ] || OUT=/media/REMOTIX-15/misure/fuzz/quic-conn-$(date +%Y-%m-%d_%H%M)

measuring() {
	local found
	found=$(pgrep -af 'benches/30-perf|30-perf\.py' | grep -v "quic-conn/run.sh" | grep -v "^$$ " | head -n 1)
	if [ -n "$found" ]; then echo "process running: $found"; return 0; fi
	local pid cwd
	for pid in $(pgrep -x 'python3?' 2>/dev/null); do
		[ "$pid" = "$$" ] && continue
		cwd=$(readlink "/proc/$pid/cwd" 2>/dev/null) || continue
		case "$cwd" in */benches/30-perf*) echo "python process $pid with cwd $cwd"; return 0 ;; esac
	done
	[ -r "$SHARE" ] || return 1
	local now open
	now=$(date +%s)
	# open «inizio» lines, as «epoch|line»; awk only parses, the age is judged below
	open=$(awk -F'|' '
		function trim(x) { gsub(/^[ \t]+|[ \t]+$/, "", x); return x }
		{
			when = trim($1); proj = trim($2); kind = tolower(trim($3)); desc = trim($4)
			split(desc, w, /[ ,:]+/); first = tolower(w[1])
			if (kind == "inizio") {
				n[proj]++; k = proj SUBSEP n[proj]
				L[k] = $0; F[k] = first; D[k] = desc; W[k] = when; O[k] = 1
			} else if (kind == "fine") {
				if (match(desc, /^\[inizio [0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9] [0-9][0-9]:[0-9][0-9]\]/)) {
					stamp = substr(desc, 9, 16)
					for (i = 1; i <= n[proj]; i++) if (W[proj SUBSEP i] == stamp) O[proj SUBSEP i] = 0
				} else {
					cnt = 0; hit = 0
					for (i = 1; i <= n[proj]; i++) {
						k = proj SUBSEP i
						if (O[k] && F[k] == first) { cnt++; hit = i }
					}
					if (cnt == 1) O[proj SUBSEP hit] = 0
				}
			}
		}
		END { for (k in O) if (O[k] && D[k] ~ /[Mm][Ii][Ss][Uu][Rr][Aa]|[Vv][Aa][Ll][Ii][Dd][Aa][Zz][Ii][Oo][Nn][Ee]|30-perf/) print W[k] "|" L[k] }
	' "$SHARE")
	local line when ts
	while IFS= read -r line; do
		[ -n "$line" ] || continue
		when=${line%%|*}
		ts=$(date -d "$when" +%s 2>/dev/null) || continue
		if [ $(( now - ts )) -lt 172800 ]; then
			echo "open «inizio» in $SHARE: ${line#*|}"
			return 0
		fi
	done <<<"$open"
	return 1
}

if [ "$FORCE" = 0 ] && why=$(measuring); then
	echo "⛔ the server is measuring — $why" >&2
	echo "   not starting (exit 5).  --force skips this check, only if you really mean it." >&2
	exit 5
fi
mkdir -p "$OUT/corpus" || exit 2
cp "$BUILD"/seeds/quic-conn/* "$OUT/corpus/" 2>/dev/null
INIZIO=$(date -u "+%F %H:%M"); COSA="fuzzing: quic-conn (limiti di connessione), 1 processo, ${SECONDS_MAX} s"
printf "%s | remotix-15 | inizio | %s | 1 core | 1 GB | %s s |\n" "$INIZIO" "$COSA" "$SECONDS_MAX" >> "$SHARE" 2>/dev/null
end() { printf "%s | remotix-15 | fine | [inizio %s] %s | - | - | -\n" "$(date -u "+%F %H:%M")" "$INIZIO" "$COSA" >> "$SHARE" 2>/dev/null; }
trap end EXIT
trap 'exit 130' INT TERM HUP
echo "== quic-conn, ${SECONDS_MAX} s, output $OUT"
nice -n 19 ionice -c3 podman run --rm --cpus=1 --userns=keep-id -v "$BUILD:/build:ro" -v "$OUT:/out" -w /out "$IMAGE" \
	/build/bin/quic-conn -max_total_time="$SECONDS_MAX" -artifact_prefix=/out/crash- -dict=/build/quic-conn.dict \
	-rss_limit_mb=2048 -print_final_stats=1 /out/corpus > "$OUT/run.log" 2>&1
rc=$?
tail -n 12 "$OUT/run.log"
ls "$OUT"/crash-* >/dev/null 2>&1 && { echo "⛔ a crash was saved: $(ls "$OUT"/crash-* | head -3 | tr '\n' ' ')"; exit 1; }
[ "$rc" -eq 0 ] || { echo "⛔ libFuzzer exited with $rc (see $OUT/run.log)"; exit 1; }
echo "⭐ no crash in ${SECONDS_MAX} s"
