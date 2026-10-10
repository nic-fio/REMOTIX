#!/bin/bash
#
# 04-b28-lancia.sh — the bench for TOUCH MODE (link A8 of phase 4).
#
#   bash banchi/04-b28-lancia.sh              certifies the judge, then runs
#   bash banchi/04-b28-lancia.sh --solo-certifica
#
# ---------------------------------------------------------------------------
# ⚠ THE SCENE, DECLARED — and it is verified from the other end, not here
#
# The browser opens on the user's REAL desktop.  ⛔ It is not moved to a
# fake screen to make the numbers add up: what the scene really was is
# written by the collector in every line of `04-b28-esiti.jsonl`, read
# from the environment and from the browser's `userAgent` — not from this
# header, which would go stale in silence.
#
# ⛔ AND TOUCH IS DECLARED BY THE BENCH: `Emulation.setTouchEmulationEnabled`.
#    ⚠ What comes out of it is the EMULATION, not a finger (`LEZIONI.md` §1.11):
#      from here come the boundaries of the RECOGNISER — which are deterministic —
#      and **no number on how a real hand behaves**.  The judgement on the
#      gestures stays with Nic, with a finger.
#
# ⛔ PORTS 7671-7675, and they are mine (mandate A8):
#     7671  the bench's server (serves `src/pagina.html` and collects the bytes)
#     7672  Chrome's debugging port
#   7448 · 7501 · 7561 · 7571 are not touched, nor the ports of the other links.
#
# ⛔ AND THE CHROME PROFILE IS NEW AND ITS OWN: a profile shared with the
#    user's session would bring in their tabs, their extensions and their
#    permission state — that is, a scene that changes from one run to the next.
# ---------------------------------------------------------------------------
set -u

QUI="$(cd "$(dirname "$0")" && pwd)"
RADICE="$(dirname "$QUI")"
PORTA=7671
DIAGNOSI=7672
PROFILO="/tmp/04-b28-profilo"
REGISTRO="$QUI/04-b28-registro.jsonl"

cd "$RADICE" || exit 2

echo "══ 1. THE JUDGE IS CERTIFIED BEFORE THE MEASUREMENT (CODER.md §3.3) ══"
python3 "$QUI/04-b28-gesti.py" --certifica
CERT=$?
if [ "$CERT" -ne 0 ]; then
  echo "⛔ the judge is not certified: nothing is measured."
  exit 3
fi
if [ "${1:-}" = "--solo-certifica" ]; then exit 0; fi

echo
echo "══ 2. THE SCENE ══"
echo "  user          $(id -un) (uid $(id -u))"
echo "  session       XDG_SESSION_TYPE=${XDG_SESSION_TYPE:-?} "\
"WAYLAND_DISPLAY=${WAYLAND_DISPLAY:-?} DISPLAY=${DISPLAY:-?}"
echo "  browser       $(google-chrome --version 2>&1)"
echo "  ⚠ the window opens on the REAL desktop, and touch is DECLARED by the"
echo "    bench (CDP): what is measured are the boundaries of the recogniser."

for p in "$PORTA" "$DIAGNOSI"; do
  if ss -ltn 2>/dev/null | grep -q ":$p "; then
    echo "⛔ port $p is already taken: I stop instead of measuring"
    echo "   someone else's page."
    exit 4
  fi
done

rm -rf "$PROFILO"
mkdir -p "$PROFILO"

echo
echo "══ 3. CHROME ══"
google-chrome \
  --user-data-dir="$PROFILO" \
  --remote-debugging-port="$DIAGNOSI" \
  --remote-allow-origins='*' \
  --no-first-run --no-default-browser-check \
  --disable-features=Translate,MediaRouter \
  --window-size=1500,900 \
  "about:blank" >"$PROFILO/chrome.log" 2>&1 &
CHROME=$!
echo "  chrome pid $CHROME, debugging on $DIAGNOSI, profile $PROFILO"

# ⛔ The coup de grâce is registered: if the bench dies, the window does not stay
#    open on the user's desktop.
trap 'kill "$CHROME" 2>/dev/null; wait "$CHROME" 2>/dev/null' EXIT

sleep 3

echo
echo "══ 4. THE MEASUREMENT ══"
python3 "$QUI/04-b28-gesti.py" --gira --porta "$PORTA" \
        --diagnosi "$DIAGNOSI" --registro "$REGISTRO"
ESITO=$?

echo
echo "══ 5. WHERE TO RECHECK ══"
echo "  outcomes  $QUI/04-b28-esiti.jsonl"
echo "  log       $REGISTRO   (the bytes, in hexadecimal, gesture by gesture)"
echo "  rejudge   python3 banchi/04-b28-gesti.py --verdetto $REGISTRO"
exit "$ESITO"
