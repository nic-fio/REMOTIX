#!/bin/bash
# filo.sh — la stretta di mano RCP contro il server NOSTRO, dentro il contenitore.
set -uo pipefail
D=/srv/src/remotix
IND=192.168.0.2
PORTA=${1:-7448}
REG=/srv/src/remotix-filo.log
PIDFILE=/srv/src/remotix.pid
ok() { printf '    OK  %s\n' "$*"; }
ko() { printf '    NO  %s\n' "$*"; }
log(){ printf '\n== %s\n' "$*"; }

# ⛔ Niente `pkill -f`: si spegne per pid, e solo il nostro.
if [ -f "$PIDFILE" ]; then
  V=$(cat "$PIDFILE")
  if [ -d "/proc/$V" ]; then kill -TERM "$V" 2>/dev/null; sleep 1; fi
  rm -f "$PIDFILE"
fi

rm -f "$REG"
log "Si accende il server NOSTRO sulla $PORTA"
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
  --certificati /srv/src/remotix-cert --pagina "$D/pagina.html" \
  --ban /srv/src/remotix-ban >"$REG" 2>&1 &
PID=$!
echo "$PID" > "$PIDFILE"
sleep 2
[ -d "/proc/$PID" ] || { ko "morto subito"; cat "$REG"; exit 2; }
ok "pid $PID"

giro() # $1 = etichetta, $2 = utente, $3 = parola
{
  rm -f "/srv/src/filo-$1.rcpreg"
  timeout 40 python3 /srv/src/01-b3-cliente.py --indirizzo "$IND" --porta "$PORTA" \
    --utente "$2" --parola "$3" --registra "/srv/src/filo-$1.rcpreg"
  echo "    uscita cliente «$1»: $?"
}

log "PRIMA connessione — il cliente di prova di B3 (aioquic), che legge solo RCP.md"
giro uno prova parola-di-prova

log "L'arbitro di B4 giudica i byte della prima"
timeout 60 python3 /srv/src/01-b4-validatore.py /srv/src/filo-uno.rcpreg
echo "    uscita validatore: $?"

log "SECONDA connessione, dopo che la prima si e' chiusa (LEZIONI 2.1)"
giro due prova parola-di-prova
timeout 60 python3 /srv/src/01-b4-validatore.py /srv/src/filo-due.rcpreg
echo "    uscita validatore: $?"

log "Il registro del server"
cat "$REG"

log "Si spegne"
kill -TERM "$PID"; sleep 1
[ -d "/proc/$PID" ] && { kill -KILL "$PID"; ko "TERM non e' bastato"; } || ok "fermato"
rm -f "$PIDFILE"
