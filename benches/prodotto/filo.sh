#!/bin/bash
# filo.sh — the RCP handshake against OUR server, inside the container.
set -uo pipefail
D=/srv/src/remotix
IND=192.168.0.2
PORTA=${1:-7448}
REG=/srv/src/remotix-filo.log
PIDFILE=/srv/src/remotix.pid
ok() { printf '    OK  %s\n' "$*"; }
ko() { printf '    NO  %s\n' "$*"; }
log(){ printf '\n== %s\n' "$*"; }

# ---------------------------------------------------------------------------
# ⛔ THE PASSWORD NO LONGER GOES THROUGH THE COMMAND LINE — defect **D12**,
#    cured on 12 Aug 2026.  `python3` is a PROCESS: the password sat in its
#    `argv`, that is in `/proc/<pid>/cmdline`, readable by anyone.
#
# ⭐ The way is the one already in the house (`banchi/01-b10-lancia.sh`): a `0600`
#    file written with `printf` — a **builtin**, so not even the write goes
#    through a process with the password in `argv` — passed as `--parola-file`,
#    and deleted with a `trap`.  What ends up in `cmdline` is the PATH.
#
# ⚠ The WRONG passwords stay where they are: they are nobody's secret, and two
#   ways for the same thing would be form **E2**.  Here, though, they buy
#   something — the scene is "three failed attempts" — so they are declared.
PAROLA=${PAROLA:-parola-di-prova}
PAROLA_FILE=/srv/src/tmp/prodotto-filo-parola

ripulisci_parola() { rm -f "$PAROLA_FILE"; }
trap ripulisci_parola EXIT

# ⛔ `umask` IN A SUBSHELL: bare, it would stick to everything that follows.
mkdir -p /srv/src/tmp \
  && ( umask 077; : > "$PAROLA_FILE" ) \
  && chmod 600 "$PAROLA_FILE" \
  || { ko "⛔ cannot write $PAROLA_FILE"; exit 2; }
printf '%s\n' "$PAROLA" > "$PAROLA_FILE"

# ⛔ No `pkill -f`: it is stopped by pid, and only ours.
if [ -f "$PIDFILE" ]; then
  V=$(cat "$PIDFILE")
  if [ -d "/proc/$V" ]; then kill -TERM "$V" 2>/dev/null; sleep 1; fi
  rm -f "$PIDFILE"
fi

rm -f "$REG"
log "Starting OUR server on $PORTA"
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
  --certificati /srv/src/remotix-cert --pagina "$D/pagina.html" \
  --ban /srv/src/remotix-ban >"$REG" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
sleep 2
[ -d "/proc/$PID" ] || { ko "died at once"; cat "$REG"; exit 2; }
ok "pid $PID"

giro() # $1 = label, $2 = user  (⛔ D12: the password from the file)
{
  rm -f "/srv/src/filo-$1.rcpreg"
  timeout 40 python3 /srv/src/01-b3-cliente.py --indirizzo "$IND" --porta "$PORTA" \
    --utente "$2" --parola-file "$PAROLA_FILE" --registra "/srv/src/filo-$1.rcpreg"
  echo "    client exit «$1»: $?"
}

log "FIRST connection — the B3 test client (aioquic), which reads only RCP.md"
giro uno prova

log "The B4 arbiter judges the bytes of the first"
timeout 60 python3 /srv/src/01-b4-validatore.py /srv/src/filo-uno.rcpreg
echo "    validator exit: $?"

log "SECOND connection, after the first has closed (LEZIONI 2.1)"
giro due prova
timeout 60 python3 /srv/src/01-b4-validatore.py /srv/src/filo-due.rcpreg
echo "    validator exit: $?"

log "The server log"
cat "$REG"

log "Stopping"
kill -TERM "$PID"; sleep 1
[ -d "/proc/$PID" ] && { kill -KILL "$PID"; ko "TERM was not enough"; } || ok "stopped"
rm -f "$PIDFILE"
