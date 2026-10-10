#!/bin/sh
# riavvia-7900.sh — THE PHASE 9 SERVER, on port 7900.
#
# ⭐ It is `riavvia-7700.sh` with four names changed, and the four names are the
#    point: port, work folder, tree and unit are ALL its own.
#
#      port        7900          (7700 = old bench, 7730 = the user, 7790 = phase 8)
#      work        /media/REMOTIX/tmp/09
#      tree        /media/REMOTIX/src/09-src/src
#      unit        remotix-7900.service
#
# ⛔ WHY 7700 IS NOT REUSED: two benches on the same machine falsify each other
#    silently (`LEZIONI.md` §1.26) — and they do not give a red, they give **a
#    plausible number**.  Phase 9 measures the rate and the bandwidth: it is the phase that
#    defect would ruin the most.  ⇒ port, ban-file and socket of its own.
#
# ⚠ Everything else — the four traps, the checks — is that of
#   `riavvia-7700.sh`, line by line, and the full comment is there.
#
# Restarts the test server on port 7900 with the page that is now on
# disk.  ⛔ The page is read ONCE at startup (pagina.c:627): without this
# restart, a new page on disk reaches nobody.
#
#   bash riavvia-7900.sh [extra options for the server]
#
# ⭐ The extra options go at the end of the fixed ones, and that is what makes
#    the long ceilings of §5.3 testable WITHOUT waiting for them:
#
#      bash riavvia-7900.sh --inattivita-s 10
#
#    exercises the thirty-minute clock in ten seconds.  ⛔ And the value IN
#    FORCE is written by the server at startup, so one does not test a ceiling believing
#    one is testing another — and it is also the only way to check the default
#    number without keeping a machine busy for half an hour.
#
# ---------------------------------------------------------------------------
# ⛔⛔ THIS FILE LIVED ONLY ON THE TEST MACHINE, and it is not a detail.
#
# `[M]` 16 August 2026: the script that STARTS the product was not in the repository.
# ⇒ Its traps were written only inside itself, no review had
# ever seen them, and the fourth — the one below — cost a good hour of
# diagnosis on a defect that `SESSIONE.md` had already written at point **A6**.
# ⚠ A tool outside the repository is a tool nobody rereads.
#
# ---------------------------------------------------------------------------
# ⛔⛔ FOUR TRAPS, all measured, all with the same symptom for whoever
#      tests — "I cannot connect" / "the desktop does not start" — and the cause minutes
#      earlier.
#
#   1. THE ENVIRONMENT.  The binary has NO RPATH: without `LD_LIBRARY_PATH` it takes the
#      system `ngtcp2`, starts very well, serves the page very well, and then
#      ABORTS at the first one who connects with «ngtcp2_settingslen_version:
#      Unreachable».  ⇒ The environment is set and CHECKED BEFORE stopping
#      the one that is there: better no restart than no server.
#
#   2. THE TERMINAL.  `sudo` with `use_pty` kills everything left in its
#      pseudo-terminal when the command ends, and `nohup` is NOT enough because
#      it blocks SIGHUP and not this.
#
#   3. THE CHECK THAT DOES NOT CHECK.  `ldd.txt` in the work folder is NOT
#      rewritten at every start: reading it after the restart gives the answer
#      of last time.  ⇒ The libraries are read from `/proc/PID/maps`, that is
#      from what the LIVE process has really opened.
#
#   4. ⛔⭐⭐ THE SESSION OF WHOEVER LAUNCHES IT — «A6» of `SESSIONE.md`, and the cure
#      of trap 2 HID it.
#
#      `setsid` detaches from the **terminal**; ⛔ it does NOT detach from the **logind
#      session**.  The process stays in the cgroup of the session of whoever gave the
#      command — typically an ssh session — and from there `pam_systemd`, when
#      the child opens its PAM session, **sees that the caller is already in
#      a session, does not create a second one and does not say so**.
#
#      `[M]` 16 August 2026, after a restart given via ssh: `loginctl` showed
#      NO session for `prova`, `/run/user/1001` did not exist, and
#      the log repeated *«I do NOT have the session bus: Could not connect: No
#      such file or directory»* — that is eight bench rounds failed out of eight, and
#      the face of the defect was "the desktop does not start".
#
#      ⭐ The cure is to start the server WHERE IT WOULD BE IN PRODUCTION: a system
#         unit.  `systemd-run` makes a transient one, in `system.slice`,
#         outside any user session.  ⚠ And it is CHECKED afterwards (E1: "written is
#         not in force"): the cgroup of the live process must not contain
#         `user@` nor `session-`.
set -e
LAV=/media/REMOTIX/tmp/09
SRC=/media/REMOTIX/src/09-src/src
B2=/media/REMOTIX/src/b2
UNITA=remotix-7900

mkdir -p "$LAV"

LD_LIBRARY_PATH="$B2/ngtcp2/build/lib:$B2/prefisso/lib${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export LD_LIBRARY_PATH

MANCA=$(ldd "$SRC/remotix" | grep -E 'ngtcp2|nghttp3' | grep -vc "$B2" || true)
if [ "$MANCA" != "0" ]; then
  echo "⛔ NOT starting: ngtcp2/nghttp3 would not come from $B2 —"
  ldd "$SRC/remotix" | grep -E 'ngtcp2|nghttp3'
  exit 1
fi

# ── what is there is stopped, in both the ways it may have been started ──
systemctl stop "$UNITA.service" 2>/dev/null || true
systemctl reset-failed "$UNITA.service" 2>/dev/null || true
if [ -f "$LAV/pid" ]; then
  VECCHIO=$(cat "$LAV/pid")
  if kill -0 "$VECCHIO" 2>/dev/null; then
    echo "stopping server $VECCHIO (old-style start)"
    kill "$VECCHIO"
    i=0
    while kill -0 "$VECCHIO" 2>/dev/null && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.1; done
    kill -0 "$VECCHIO" 2>/dev/null && { echo "it does not stop: forcing it"; kill -9 "$VECCHIO"; sleep 1; }
  fi
fi
# ⚠ And we wait for the port to really free up: `[M]` 16 August, a start
#   right after got «⛔ cannot bind to 0.0.0.0:7900 over UDP: Address
#   already in use» and the new server died without anyone looking.
i=0
while ss -uln 2>/dev/null | grep -q ':7900 ' && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.2; done

# ── ⭐ started as a SYSTEM UNIT, outside any user session ────────────────────
systemd-run \
  --unit="$UNITA" --collect --description="REMOTIX, port 7900 bench — phase 9" \
  --working-directory="$SRC" \
  --setenv=LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
  --property=StandardOutput=append:"$LAV/registro.log" \
  --property=StandardError=append:"$LAV/registro.log" \
  --property=KillMode=mixed \
  --property=LimitRTPRIO=20 \
  --property=LimitNICE=-11 \
  "$SRC/remotix" \
  --indirizzo 0.0.0.0 --nome 192.168.0.2 --porta 7900 \
  --certificati "$LAV/certificati" \
  --pagina "$SRC/pagina.html" \
  --ban-file "$LAV/ban" \
  --comando-socket "$LAV/comando.sock" \
  --rilievo "$LAV/rilievo" \
  --parlantina "$@" >/dev/null

i=0
NUOVO=""
while [ $i -lt 50 ]; do
  NUOVO=$(systemctl show -p MainPID --value "$UNITA.service" 2>/dev/null || echo 0)
  [ -n "$NUOVO" ] && [ "$NUOVO" != "0" ] && break
  i=$((i+1)); sleep 0.1
done
if [ -z "$NUOVO" ] || [ "$NUOVO" = "0" ]; then
  echo "⛔ the server did not start — the last lines of the log:"
  tail -15 "$LAV/registro.log"
  exit 1
fi
echo "$NUOVO" > "$LAV/pid"
echo "server $NUOVO, unit $UNITA.service"

# ── ⭐ THE CHECKS, and they are two different facts ──────────────────────────
#
# ⛔⭐ AND WE WAIT FOR THE LIST TO BE THERE, instead of just reading it.
#
# `[M]` 16 August 2026: this check printed an **empty** list and
# right below «⭐ they are those of /media/REMOTIX/src/b2» — that is it gave the OK
# without having looked at anything.  ⇒ Between `systemd-run` returning the `MainPID` and the
# dynamic loader having finished mapping some milliseconds pass, and in
# that window `/proc/PID/maps` does not yet have the libraries.
# ⚠ It is the nastiest form of the defect: not a test red by mistake, but a
#   GREEN test that examined nothing — "empty" and "right" with the same
#   face, `LEZIONI.md` §1.9.
echo "libraries the LIVE process has really opened:"
i=0
LIBS=""
while [ $i -lt 50 ]; do
  LIBS=$(grep -oE '/[^ ]*(libngtcp2|libnghttp3)[^ ]*' "/proc/$NUOVO/maps" 2>/dev/null | sort -u)
  # ⛔ BOTH: only one would mean the loader is half way.
  if echo "$LIBS" | grep -q libngtcp2 && echo "$LIBS" | grep -q libnghttp3; then
    break
  fi
  i=$((i+1)); sleep 0.1
done
echo "$LIBS" | sed 's/^/    /'
if ! echo "$LIBS" | grep -q libngtcp2 || ! echo "$LIBS" | grep -q libnghttp3; then
  echo "⛔ I do NOT see them mapped after 5 s: the process is not the one I think"
  exit 1
fi
if echo "$LIBS" | grep -qv "$B2"; then
  echo "⛔ they are NOT those of $B2"
  exit 1
fi
echo "⭐ they are those of $B2: testing can start"

# ⛔ A6: the server must not be inside ANY user session, or its children
#    will be born without runtime, without bus and without desktop.
CG=$(cat "/proc/$NUOVO/cgroup" 2>/dev/null || echo "")
case "$CG" in
  *user@*|*session-*)
    echo "⛔⛔ THE SERVER IS INSIDE A USER SESSION (A6 of SESSIONE.md):"
    echo "    $CG"
    echo "    ⇒ pam_systemd will not create the children's session, and the desktop will not start."
    exit 1
    ;;
  *)
    echo "⭐ VERIFIED: the server is outside any user session ($CG)"
    ;;
esac
