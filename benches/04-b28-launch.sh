#!/bin/bash
#
# 04-b28-launch.sh — the bench for TOUCH MODE (link A8 of phase 4).
#
#   bash benches/04-b28-launch.sh              certifies the judge, then runs
#   bash benches/04-b28-launch.sh --certify-only
#
# ---------------------------------------------------------------------------
# ⚠ THE SCENE, DECLARED — and it is verified from the other end, not here
#
# The browser opens on the user's REAL desktop.  ⛔ It is not moved to a
# fake screen to make the numbers add up: what the scene really was is
# written by the collector in every line of `04-b28-outcomes.jsonl`, read
# from the environment and from the browser's `userAgent` — not from this
# header, which would go stale in silence.
#
# ⛔ AND TOUCH IS DECLARED BY THE BENCH: `Emulation.setTouchEmulationEnabled`.
#    ⚠ What comes out of it is the EMULATION, not a finger (`LESSONS.md` §1.11):
#      from here come the boundaries of the RECOGNISER — which are deterministic —
#      and **no number on how a real hand behaves**.  The judgement on the
#      gestures stays with Nic, with a finger.
#
# ⛔ PORTS 7671-7675, and they are mine (mandate A8):
#     7671  the bench's server (serves `src/page.html` and collects the bytes)
#     7672  Chrome's debugging port
#   7448 · 7501 · 7561 · 7571 are not touched, nor the ports of the other links.
#
# ⛔ AND THE CHROME PROFILE IS NEW AND ITS OWN: a profile shared with the
#    user's session would bring in their tabs, their extensions and their
#    permission state — that is, a scene that changes from one run to the next.
# ---------------------------------------------------------------------------
set -u

HERE="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(dirname "$HERE")"
PORT=7671
DIAGNOSIS=7672
PROFILE="/tmp/04-b28-profilo"
LOG="$HERE/04-b28-register.jsonl"

cd "$ROOT" || exit 2

echo "══ 1. THE JUDGE IS CERTIFIED BEFORE THE MEASUREMENT (CODER.md §3.3) ══"
python3 "$HERE/04-b28-gestures.py" --certify
CERT=$?
if [ "$CERT" -ne 0 ]; then
  echo "⛔ the judge is not certified: nothing is measured."
  exit 3
fi
if [ "${1:-}" = "--certify-only" ]; then exit 0; fi

echo
echo "══ 2. THE SCENE ══"
echo "  user          $(id -un) (uid $(id -u))"
echo "  session       XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-?} "\
"WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-?} DISPLAY=${DISPLAY:-?}"
echo "  browser       $(google-chrome --version 2>&1)"
echo "  ⚠ the window opens on the REAL desktop, and touch is DECLARED by the"
echo "    bench (CDP): what is measured are the boundaries of the recogniser."

for p in "$PORT" "$DIAGNOSIS"; do
  if ss -ltn 2>/dev/null | grep -q ":$p "; then
    echo "⛔ port $p is already taken: I stop instead of measuring"
    echo "   someone else's page."
    exit 4
  fi
done

rm -rf "$PROFILE"
mkdir -p "$PROFILE"

echo
echo "══ 3. CHROME ══"
google-chrome \
  --user-data-dir="$PROFILE" \
  --remote-debugging-port="$DIAGNOSIS" \
  --remote-allow-origins='*' \
  --no-first-run --no-default-browser-check \
  --disable-features=Translate,MediaRouter \
  --window-size=1500,900 \
  "about:blank" >"$PROFILE/chrome.log" 2>&1 &
CHROME=$!
echo "  chrome pid $CHROME, debugging on $DIAGNOSIS, profile $PROFILE"

# ⛔ The coup de grâce is registered: if the bench dies, the window does not stay
#    open on the user's desktop.
trap 'kill "$CHROME" 2>/dev/null; wait "$CHROME" 2>/dev/null' EXIT

sleep 3

echo
echo "══ 4. THE MEASUREMENT ══"
python3 "$HERE/04-b28-gestures.py" --run --port "$PORT" \
        --diagnosis "$DIAGNOSIS" --log "$LOG"
OUTCOME=$?

echo
echo "══ 5. WHERE TO RECHECK ══"
echo "  outcomes  $HERE/04-b28-outcomes.jsonl"
echo "  log       $LOG   (the bytes, in hexadecimal, gesture by gesture)"
echo "  rejudge   python3 benches/04-b28-gestures.py --verdict $LOG"
exit "$OUTCOME"
