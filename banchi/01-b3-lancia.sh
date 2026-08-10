#!/bin/bash
#
# 01-b3-lancia.sh — gira SUL SERVER.  B3: la stretta di mano su DUE
#                   connessioni, mai una.
#
#   bash /media/REMOTIX/src/01-b3-lancia.sh
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' DUE, E PERCHE' LA SECONDA E' IL BANCO VERO
#
# `LEZIONI.md` §2.1: in v1 un certificato condiviso uccideva il server **alla
# seconda** connessione, e una prova a collegamento singolo **resta verde per
# sempre**.  Se la seconda fallisce dove la prima e' passata, il difetto e' del
# server — e questa e' l'unica prova che lo dice.
#
# I tre giri:
#
#   1. la prima connessione, fino a SESSIONE
#   2. la seconda DOPO che la prima si e' chiusa — ⛔ identica alla prima
#   3. la seconda MENTRE la prima e' viva — CONGEDO(GIA_ATTIVA_REMOTA = 0x0F)
#      verso CHI ARRIVA, e ⛔ si controlla QUALE delle due sopravvive
#
# ⚠ Il terzo giro e' l'invariante I2 di `SPECIFICHE.md` alla lettera, ed e' la
#   sola prova che distingue «il server rifiuta il secondo» da «il server si
#   fa spodestare»: sono due comportamenti opposti e danno lo stesso rosso a
#   chi guarda solo il nuovo arrivato.
#
# ⛔ E ogni traccia passa dal VALIDATORE di B4: e' l'arbitro, e non si
#    collauda il server contro il client.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
IND=${1:-192.168.0.2}
PORTA=${2:-7447}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

UTENTE=prova
PAROLA=parola-di-prova
BENE=0

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

cliente() # $1 = etichetta, $2.. = opzioni in piu'
{
	local et=$1; shift
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b3-cliente.py --indirizzo $IND --porta $PORTA --utente $UTENTE --parola $PAROLA --registra $DENTRO/b3-$et.rcpreg $*"
}

valida() # $1 = etichetta
{
	local et=$1
	bash "$ENTRA" --root "python3 $DENTRO/01-b4-validatore.py $DENTRO/b3-$et.rcpreg" \
		| tail -3 | sed 's/^/        /'
}

# ---------------------------------------------------------------------------
log "1. La prima connessione"
inf "atteso: stretta di mano completa fino a SESSIONE"
cliente uno
E1=$?
inf "uscita $E1"
[ "$E1" -eq 0 ] || BENE=1
inf "e il validatore di B4 dice:"
valida uno

# ---------------------------------------------------------------------------
log "2. ⛔ La SECONDA, dopo che la prima si e' chiusa"
inf "atteso: IDENTICA alla prima.  Se fallisce qui dove la prima e' passata,"
inf "        il difetto e' del server — ed e' quel che uccise v1."
cliente due
E2=$?
inf "uscita $E2"
[ "$E2" -eq 0 ] || BENE=1
inf "e il validatore di B4 dice:"
valida due

# ---------------------------------------------------------------------------
log "3. ⛔ La seconda MENTRE la prima e' viva — GIA_ATTIVA_REMOTA"
inf "atteso: CONGEDO(0x0F) verso CHI ARRIVA, e la prima che sopravvive"
# ⛔ Il terzo giro sta in un file suo, che gira DENTRO il contenitore.
#    Scriverlo da qui vorrebbe dire una sottoshell in secondo piano attorno a
#    `enter.sh`, e quella si porta via la richiesta di password di sudo: lo
#    script resta ad aspettare una domanda che nessuno vede.  Succeso tre
#    volte il 10 agosto 2026, in tre vesti diverse.
bash "$ENTRA" --root "bash $DENTRO/01-b3-terzo-giro.sh $IND $PORTA"
E3=$?
inf "terzo giro: uscita $E3"
[ "$E3" -eq 0 ] || BENE=1
inf "e il validatore di B4 sulle due tracce del terzo giro:"
valida viva

# ---------------------------------------------------------------------------
log "Esito"
inf "1ª connessione        : $([ "$E1" -eq 0 ] && echo passa || echo NON passa)"
inf "2ª dopo la chiusura   : $([ "$E2" -eq 0 ] && echo passa || echo NON passa)"
inf "2ª mentre la 1ª vive  : $([ "${E3:-9}" -eq 0 ] && echo passa || echo NON passa)"
if [ "$BENE" -eq 0 ]; then
	ok "⭐ B3: tre giri su tre"
else
	ko "⛔ B3: qualcosa non passa"
fi
exit "$BENE"
