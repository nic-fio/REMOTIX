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

# ---------------------------------------------------------------------------
# ⛔ LA PAROLA D'ORDINE NON PASSA PIU' DALLA RIGA DI COMANDO — difetto **D12**,
#    curato il 12 agosto 2026.  `python3` e' un PROCESSO: la parola stava nel
#    suo `argv`, cioe' in `/proc/<pid>/cmdline`, leggibile da chiunque.
#
# ⭐ La strada e' quella gia' in casa (`banchi/01-b10-lancia.sh`): file `0600`
#    scritto con `printf` — un **builtin**, quindi nemmeno la scrittura passa
#    per un processo con la parola in `argv` — passato come `--parola-file`, e
#    cancellato con una `trap`.  Nel `cmdline` finisce il PERCORSO.
#
# ⚠ Le parole SBAGLIATE restano dove stanno: non sono il segreto di nessuno, e
#   due strade per la stessa cosa sarebbero la forma **E2**.  Qui pero' comprano
#   qualcosa — la scena e' «tre tentativi falliti» — quindi si dichiarano.
PAROLA=${PAROLA:-parola-di-prova}
PAROLA_FILE=/srv/src/tmp/prodotto-filo-parola

ripulisci_parola() { rm -f "$PAROLA_FILE"; }
trap ripulisci_parola EXIT

# ⛔ `umask` IN UNA SOTTOSHELL: nudo resterebbe addosso a tutto quel che segue.
mkdir -p /srv/src/tmp \
  && ( umask 077; : > "$PAROLA_FILE" ) \
  && chmod 600 "$PAROLA_FILE" \
  || { ko "⛔ non si scrive $PAROLA_FILE"; exit 2; }
printf '%s\n' "$PAROLA" > "$PAROLA_FILE"

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

giro() # $1 = etichetta, $2 = utente  (⛔ D12: la parola dal file)
{
  rm -f "/srv/src/filo-$1.rcpreg"
  timeout 40 python3 /srv/src/01-b3-cliente.py --indirizzo "$IND" --porta "$PORTA" \
    --utente "$2" --parola-file "$PAROLA_FILE" --registra "/srv/src/filo-$1.rcpreg"
  echo "    uscita cliente «$1»: $?"
}

log "PRIMA connessione — il cliente di prova di B3 (aioquic), che legge solo RCP.md"
giro uno prova

log "L'arbitro di B4 giudica i byte della prima"
timeout 60 python3 /srv/src/01-b4-validatore.py /srv/src/filo-uno.rcpreg
echo "    uscita validatore: $?"

log "SECONDA connessione, dopo che la prima si e' chiusa (LEZIONI 2.1)"
giro due prova
timeout 60 python3 /srv/src/01-b4-validatore.py /srv/src/filo-due.rcpreg
echo "    uscita validatore: $?"

log "Il registro del server"
cat "$REG"

log "Si spegne"
kill -TERM "$PID"; sleep 1
[ -d "/proc/$PID" ] && { kill -KILL "$PID"; ko "TERM non e' bastato"; } || ok "fermato"
rm -f "$PIDFILE"
