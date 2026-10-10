#!/bin/bash
# lancia.sh — a REAL BROWSER against the server of src/.  It runs ON THE HOST (the
# browser is there), the server runs in the container.
set -uo pipefail
QUI=$(cd -- "$(dirname -- "$0")" && pwd)
IND=${1:-192.168.0.2}
PORTA=${2:-7448}
# ⛔ The collector's port is a PARAMETER — 11 Aug 2026, evening.  It was
#    fixed at 8898, and two probe rounds on the same machine took the port
#    from each other: the second died with "collector dead", which looks
#    exactly like "the probe cannot start".  They are two different things.
RACC=${3:-8898}
ok() { printf '    OK  %s\n' "$*"; }
ko() { printf '    NO  %s\n' "$*"; }
log(){ printf '\n== %s\n' "$*"; }

command -v firefox >/dev/null || { ko "firefox is not there"; exit 2; }
command -v xvfb-run >/dev/null || { ko "xvfb-run is not there"; exit 2; }
firefox --version

log "The fingerprint is asked OF THE SERVER, not guessed"
IMP=$(curl -sk "https://$IND:$PORTA/impronta" | python3 -c 'import json,sys;print(json.load(sys.stdin)["impronta"])')
[ -n "$IMP" ] || { ko "no fingerprint from https://$IND:$PORTA/impronta"; exit 2; }
echo "    fingerprint: $IMP"

rm -f "$QUI/esiti.jsonl"
python3 "$QUI/racc.py" $RACC > "$QUI/racc.log" 2>&1 &
PR=$!
sleep 1
[ -d "/proc/$PR" ] || { ko "collector dead"; cat "$QUI/racc.log"; exit 2; }
ok "collector on 127.0.0.1:$RACC"

# ---------------------------------------------------------------------------
# ⛔ WHO IS STILL USING THIS PROFILE — read from `/proc`, PID by PID.
#
#    ⛔ Not `pkill -f`: that one picks by itself whom to kill, and would take
#       the browser of another round (the project rule: stop BY PID).
#    ⭐ The criterion is the profile path, which exists only for this round,
#       and it is compared with the WHOLE argument (`grep -x`): "/…/prof-ammesso"
#       and "/…/prof-ammesso-vecchio" are two different things.
chi_usa_il_profilo() # $1 = profile
{
  local d
  for d in /proc/[0-9]*; do
    [ -r "$d/cmdline" ] || continue
    if tr '\0' '\n' < "$d/cmdline" 2>/dev/null | grep -qxF -- "$1"; then
      printf '%s\n' "${d#/proc/}"
    fi
  done
}

# ⛔⭐ AND THAT THE D12 CURE HAS CLOSED IS NOT BELIEVED: IT IS CHECKED IN `ps`.
#
# `LEZIONI.md` §1.9: "I did not find it" and "I did not look" look the same,
# and the proof here is an **ABSENCE** — which can only be shown with a
# denominator beside it saying "the tool, at that instant, was looking".
# ⇒ The second needle is the PROFILE PATH, which is surely in `argv`
#   (`--profile "$prof"`): if that disappeared too, the password's zero
#   would mean "I did not look" and not "it was not there".
#
# ⛔ AND THE GUARD MUST NOT CREATE THE DEFECT IT LOOKS FOR: `ps` is read into a
#    variable and the comparison is done by **bash**.  A `grep "$parola"` would
#    put the password in the `argv` of `grep`, and the guard would be the leak.
guardia_ps() # $1 = needle that must NOT appear · $2 = needle that MUST appear
{
  local i righe uno=0 due=0
  for i in $(seq 1 40); do
    righe=$(ps -ww -eo args)
    [ -n "$1" ] && case "$righe" in *"$1"*) uno=$((uno + 1)) ;; esac
    [ -n "$2" ] && case "$righe" in *"$2"*) due=$((due + 1)) ;; esac
    sleep 0.25
  done
  printf '%s %s\n' "$uno" "$due" > "$QUI/guardia-ps"
}

giro() # $1 = label, $2 = password
{
  local prof="$QUI/prof-$1"
  rm -rf "$prof"; mkdir -p "$prof"
  local U="http://127.0.0.1:$RACC/sonda-rcp.html?base=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "https://$IND:$PORTA")&impronta=$(python3 -c 'import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=""))' "$IMP")#utente=prova&parola=$2"
  log "round «$1»"
  # ⛔ AND HERE THE ADDRESS IS PRINTED MASKED — R12-A.34, second half.
  #    Moving the password into the fragment takes it out of the HTTP log, but
  #    this line wrote it on the terminal, and the terminal of a round ends up
  #    in a file like everything else.  ⚠ A half cure is worse than none: it
  #    makes you believe the hole is closed.
  echo "    ${U%%#*}#utente=prova&parola=<NOT PRINTED>"

  # ⛔⭐ THE THIRD HALF OF THE FRAGMENT CURE — defect **D12**, 12 Aug
  #     2026, and here the form is DIFFERENT from that of all the other benches.
  #
  # In the others the password was a `--parola` to remove.  ⛔ Here it sits
  # **inside the address**, and the address was given to `firefox` as an
  # argument: it ended up in the `argv` of `setsid`, in that of `xvfb-run` and
  # in that of `firefox`, that is in `/proc/<pid>/cmdline`, which on Linux is
  # readable by anyone.
  #
  # ⚠ And this is the leak the first two halves did NOT touch, and it is the
  #   reason it is worth writing it here: R12-A.34 moved the password from the
  #   query to the fragment — that is, out of the HTTP logs — and took it off
  #   the terminal, and all that time `ps` kept printing it whole.
  #   ⛔ Three cures on the same secret, and the easiest to see was the last.
  #
  # ⭐ THE CURE, and it could not be `--parola-file`: `firefox` does not take
  #    the address from a file.  It does take it, though, from **its own
  #    profile** — `browser.startup.homepage` — and the profile is a folder of
  #    ours, of this round, which this very function throws away and VERIFIES
  #    it threw away.
  #    ⇒ The address goes through `user.js` (0600, in a 0700 folder) and
  #    `firefox` is launched **with no address among its arguments**.
  #
  # ⚠ And it is declared what this cure does NOT buy: the password stays in the
  #   profile, exactly as it already stayed inside `recovery.jsonlz4`.  The
  #   count of dirty files below WILL RISE, and it is right that it rises —
  #   it is the truth that was already being measured before.  What disappears
  #   is `ps`, which was the only place where being on the machine was enough
  #   to look.
  #
  # ⛔ The three extra lines are not ornament: on a NEW profile Firefox would
  #    show the welcome page instead of its own home, and the probe would sit
  #    waiting for an outcome that never arrives — which looks the same as
  #    "the server does not answer".
  ( umask 077
    {
      printf 'user_pref("browser.startup.homepage", "%s");\n' "$U"
      printf 'user_pref("browser.startup.page", 1);\n'
      printf 'user_pref("browser.startup.firstrunSkipsHomepage", false);\n'
      printf 'user_pref("browser.startup.homepage_override.mstone", "ignore");\n'
      printf 'user_pref("browser.aboutwelcome.enabled", false);\n'
      printf 'user_pref("datareporting.policy.dataSubmissionEnabled", false);\n'
      printf 'user_pref("datareporting.policy.firstRunURL", "");\n'
    } > "$prof/user.js" ) || { ko "⛔ cannot write $prof/user.js"; return 2; }
  chmod 700 "$prof"; chmod 600 "$prof/user.js"

  # ⚠ `setsid` puts Firefox and its Xvfb in a group of their own, so the
  #   TERM below can try to take them all at once.  ⛔ But it is an attempt,
  #   not the criterion: the criterion is `/proc`, and the reason is in the
  #   race told further down.
  # ⛔ AND NO ADDRESS AMONG THE ARGUMENTS: it is the D12 cure (above).
  rm -f "$QUI/guardia-ps"
  guardia_ps "$2" "$prof" &
  local pg=$!
  setsid xvfb-run -a firefox --no-remote --profile "$prof" \
      > "$QUI/ff-$1.log" 2>&1 &
  local p=$!
  local i=0
  while [ "$i" -lt 45 ]; do
    [ -s "$QUI/esiti.jsonl" ] && break
    sleep 1; i=$((i+1))
  done

  # ── ⛔ D12: the measurement, with its denominator ───────────────────────────
  wait "$pg" 2>/dev/null
  local vp=0 vf=0
  if [ -r "$QUI/guardia-ps" ]; then
    vp=$(cut -d' ' -f1 "$QUI/guardia-ps"); vf=$(cut -d' ' -f2 "$QUI/guardia-ps")
  fi
  echo "    -- D12/ps: the PASSWORD seen $vp times · the PROFILE (which is in argv)"
  echo "       seen $vf times"
  if [ "${vf:-0}" -lt 1 ]; then
    ko "⚠ I did not see in «ps» even the profile, which was surely in «argv»:"
    ko "  so the password's zero means «I did not look», not «it was not"
    ko "  there».  ⛔ It is not a green, and it is declared."
  elif [ "${vp:-1}" -gt 0 ]; then
    ko "⛔⛔ THE PASSWORD IS STILL IN «ps» ($vp times out of $vf): D12 is NOT closed here"
  else
    ok "⭐ D12 closed by measurement: at the same instant «ps» saw the profile"
    ok "   ($vf times) and did NOT see the password"
  fi

  # ⛔⭐ AND HERE THERE WAS A RACE, AND IT WAS MEASURED — 11 Aug 2026, 12:50 UTC.
  #
  #     `kill "$p"` killed **the leader** — `xvfb-run`, which is a shell
  #     script — and not Firefox, which is its child.  ⛔ The profile was
  #     deleted while Firefox was still alive, and Firefox **rewrote it right
  #     after**: `[M]` profile deleted at 12:49:54,
  #     `sessionstore-backups/recovery.jsonlz4` reappeared at **12:50:10**,
  #     2223 bytes, with the password inside.
  #
  # ⚠ That is, the cure was there, the log said "the profile is thrown away
  #   now", and the secret stayed on disk all the same.  It is the worst form:
  #   a cure that **prints that it worked**.
  #
  # ⛔ AND THE FIRST CURE WAS NOT ENOUGH, AND IT WAS MEASURED TOO: we moved
  #    to `setsid` + `kill -- -$p`, that is to the GROUP, and at 12:51:31 UTC
  #    `recovery.jsonlz4` reappeared all the same (2227 bytes, the password
  #    inside).  ⛔ The reason is that "the group is dead" answered **at once**
  #    — that is, the check was mute — and a mute check is indistinguishable
  #    from a check that passes.
  #
  # ⭐ Hence today's criterion, which does not go through groups: it looks in
  #    `/proc` for WHO still has this profile among its arguments.  The
  #    opposite case has a precise look — the list does not empty, and this
  #    function exits 3 without deleting anything.
  kill -TERM -- "-$p" 2>/dev/null   # the group: we try, we do not trust it
  wait "$p" 2>/dev/null
  local g=0 vivi
  vivi=$(chi_usa_il_profilo "$prof")
  [ -n "$vivi" ] && kill $vivi 2>/dev/null
  while [ "$g" -lt 60 ]; do
    vivi=$(chi_usa_il_profilo "$prof")
    [ -z "$vivi" ] && break
    sleep 0.5; g=$((g+1))
  done
  if [ -n "$vivi" ]; then
    echo "    -- after 30 s of TERM these still use the profile: $(echo $vivi) — KILL"
    kill -KILL $vivi 2>/dev/null
    sleep 1
    vivi=$(chi_usa_il_profilo "$prof")
  fi
  if [ -n "$vivi" ]; then
    ko "⛔ these processes still have the profile open: $(echo $vivi)"
    ko "   NOT deleting: deleting it now would mean having it rewritten"
    return 3
  fi
  echo "    -- browser stopped, and /proc says so: no process has «$prof»"
  echo "       among its arguments any more (waited $(( g / 2 )) s)"

  # ⛔⭐ THE SECOND HALF OF THE FRAGMENT CURE — 11 Aug 2026, evening.
  #
  #     `sonda-rcp.html` declares, in the comment of R12-A.34, that *"the profile
  #     is thrown away at the end of the round (lancia.sh)"*.  ⛔ It was not
  #     true: `lancia.sh` threw the profile away at the START of the round, and
  #     the one of the last round stayed on disk — with the password inside
  #     `sessionstore-backups/recovery.jsonlz4`, because the fragment is part
  #     of the address the browser saves in the session.  ⚠ A cure written in
  #     a comment and not in the code makes you believe the hole is closed: it
  #     is worse than no cure.
  #
  # ⭐ And before throwing it away it is MEASURED, instead of just thrown away:
  #    so what was inside stays written — if one day the fragment stopped
  #    ending up in the saved session, this line would go from N to 0 and we
  #    would know something changed, instead of never knowing.
  local sporchi resta
  sporchi=$(grep -rl --binary-files=text -e "$2" "$prof" 2>/dev/null | wc -l)
  echo "    -- this round's profile held the password in $sporchi files"
  echo "       (the fragment stays in the browser's saved session: it is the"
  echo "        declared limit of the cure).  The profile is thrown away now."
  rm -rf "$prof"
  # ⛔ And the deletion is VERIFIED — TWICE, some time apart.  "It is gone"
  #    looked at in the very instant of deleting is exactly what hid the
  #    race: the first time the check passed, and six seconds later the file
  #    was back.  ⭐ The second look, five seconds later, is the difference
  #    between "I deleted it" and "it stayed deleted".
  sleep 5
  if [ -e "$prof" ]; then
    resta=$(find "$prof" -type f 2>/dev/null | wc -l)
    ko "⛔ the profile $prof CAME BACK ($resta files) 5 s after the deletion:"
    ko "   someone is still writing it, and the cure did not hold"
    grep -rl --binary-files=text -e "$2" "$prof" 2>/dev/null | sed 's/^/        /'
  else
    ok "profile thrown away, and five seconds later the disk still confirms it"
  fi

  if [ ! -s "$QUI/esiti.jsonl" ]; then
    ko "no outcome in $i seconds"
    echo "    -- requests received by the collector: $(grep -c '^request: ' "$QUI/racc.log")"
    tail -6 "$QUI/racc.log" | sed 's/^/        /'
    tail -8 "$QUI/ff-$1.log" | sed 's/^/        /'
    return 1
  fi
  ok "outcome received after $i seconds"
  cat "$QUI/esiti.jsonl" | python3 -c '
import json,sys
for r in sys.stdin:
    d=json.loads(r)
    print("        outcome:", d.get("esito"))
    print("        engine :", (d.get("motore") or "")[:90])
    print("        detail :", d.get("dettaglio"))
    for x in (d.get("righe") or []): print("          .", x)
'
  return 0
}

giro ammesso parola-di-prova; E1=$?
rm -f "$QUI/esiti.jsonl"
giro respinto parola-SBAGLIATA; E2=$?

kill "$PR" 2>/dev/null
log "outcomes: ammesso=$E1 respinto=$E2"
