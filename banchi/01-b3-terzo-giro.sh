#!/bin/bash
#
# 01-b3-terzo-giro.sh — ⚠ gira DENTRO il contenitore, chiamato da
#                       01-b3-lancia.sh con una sola riga.
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' UN FILE A PARTE
#
# Il terzo giro di B3 vuole due clienti contemporanei: uno che resta attaccato
# e uno che arriva dopo.  Scriverlo dal di fuori significa una sottoshell in
# secondo piano, o una sostituzione di comando, attorno a `enter.sh` — e
# tutt'e due si portano via la richiesta di password di sudo, lasciando lo
# script ad aspettare una domanda che nessuno vede.  Il 10 agosto 2026 e'
# successo tre volte in un giorno, in tre vesti diverse.
#
# ⭐ Qui dentro non c'e' nessun sudo e nessuna shell annidata: due processi e
#    due file.
#
# ---------------------------------------------------------------------------
# CHE COSA PROVA, E LA META' CHE SI DIMENTICA
#
#   - la SECONDA connessione dev'essere rifiutata con GIA_ATTIVA_REMOTA (0x0F)
#   - ⛔ e la PRIMA deve SOPRAVVIVERE: «chi viene rifiutato e' chi arriva, non
#     chi c'era».  Un server che spodestasse il primo darebbe alla seconda
#     esattamente lo stesso rosso, ed e' il comportamento opposto.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=/srv/src
IND=${1:-192.168.0.2}
PORTA=${2:-7447}
UTENTE=prova
PAROLA=parola-di-prova

ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

rm -f "$QUI/b3-viva.log" "$QUI/b3-terza.log"

python3 "$QUI/01-b3-cliente.py" --indirizzo "$IND" --porta "$PORTA" \
	--utente "$UTENTE" --parola "$PAROLA" \
	--registra "$QUI/b3-viva.rcpreg" --resta 12 > "$QUI/b3-viva.log" 2>&1 &
PRIMA=$!

# Si aspetta che la PRIMA sia davvero attaccata, non un tempo fisso: «ho
# aspettato abbastanza» e «e' attaccata» sono due cose diverse.
ATTACCATA=no
for _ in $(seq 1 15); do
	if grep -q "SESSIONE" "$QUI/b3-viva.log" 2>/dev/null; then
		ATTACCATA=si
		break
	fi
	sleep 1
done
if [ "$ATTACCATA" != si ]; then
	ko "la prima non si e' attaccata: il terzo giro non prova niente"
	sed 's/^/        /' "$QUI/b3-viva.log"
	kill "$PRIMA" 2>/dev/null
	exit 3
fi
ok "la prima e' attaccata"

inf "adesso arriva la seconda"
python3 "$QUI/01-b3-cliente.py" --indirizzo "$IND" --porta "$PORTA" \
	--utente "$UTENTE" --parola "$PAROLA" \
	--registra "$QUI/b3-terza.rcpreg" > "$QUI/b3-terza.log" 2>&1
SECONDA=$?
tail -4 "$QUI/b3-terza.log" | sed 's/^/        /'

ESITO=0
if grep -q "GIA_ATTIVA_REMOTA" "$QUI/b3-terza.log"; then
	ok "⭐ la seconda e' rifiutata con GIA_ATTIVA_REMOTA (0x0F), uscita $SECONDA"
else
	ko "⛔ la seconda NON e' stata rifiutata con 0x0F (uscita $SECONDA)"
	ESITO=1
fi

wait "$PRIMA"
VIVA=$?
if [ "$VIVA" -eq 0 ]; then
	ok "⭐ e la PRIMA e' sopravvissuta: nessun client vivo viene spodestato"
else
	ko "⛔ la prima e' MORTA (uscita $VIVA): il server ha spodestato chi c'era"
	tail -5 "$QUI/b3-viva.log" | sed 's/^/        /'
	ESITO=1
fi
exit "$ESITO"
