#!/bin/bash
#
# 01-b3-quinto-giro.sh — ⚠ gira SULLA MACCHINA DI CHI GUARDA: i browser stanno qui.
#
#   bash banchi/01-b3-quinto-giro.sh
#
#   ⛔ la 3ª connessione con il certificato di sessione RUOTATO A MANO.
#
# ---------------------------------------------------------------------------
# CHE COSA PROVA
#
# `RCP.md` §4.1-bis: il certificato della **sessione** dura meno di quattordici
# giorni e ruota da se'; la sua impronta viaggia dentro la pagina.  Se la
# pagina la tenesse scritta dentro, alla prima rotazione smetterebbe di
# collegarsi — e il sintomo sarebbe *«non si collega piu' e non dice perche'»*,
# due settimane dopo la consegna.
#
# Il giro, in tre tempi:
#
#   1. si legge l'impronta CORRENTE                      (la vecchia)
#   2. si RUOTA il certificato e si riavvia il server     (la nuova)
#   3. ⭐ la pagina ritira l'impronta nuova e si collega
#   4. ⛔ e con la VECCHIA la sessione NON si apre
#
# ⛔ Il quarto tempo e' quello che rende vero il terzo.  Senza, «funziona con
#    l'impronta nuova» e' compatibile con **un browser che non guarda affatto
#    l'impronta** — e allora il modello di fiducia di §4.1-bis non sarebbe
#    provato da nessuna parte.
#
# ---------------------------------------------------------------------------
# ⚠ E QUEL CHE QUESTO GIRO NON PROVA, DETTO QUI
#
# La rotazione **automatica** a quattordici giorni.  Cambiare la chiave a mano
# prova che la pagina sa ritirare l'impronta; che il server rigeneri **prima**
# della scadenza resta senza banco, e il suo sintomo arriva due settimane dopo
# la consegna.  Sta scritto in `FASI.md` §01-filo-nudo, B3.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
RADICE=$(dirname "$QUI")
SSH="python3 $RADICE/fondamenta/strumenti/sshpw.py"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

ESITO=0

# ---------------------------------------------------------------------------
log "1. L'impronta di adesso — quella che diventera' vecchia"
$SSH "bash /media/REMOTIX/src/01-b2-lancia-wt.sh spegni" >/dev/null 2>&1
VECCHIA=$($SSH "bash /media/REMOTIX/enter.sh --root \"openssl x509 -in /media/REMOTIX/b2-certificati/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0\"" | grep -oE '[A-Za-z0-9+/]{43}=' | tail -1)
if [ ${#VECCHIA} -ne 44 ]; then
	ko "non ho l'impronta vecchia (${#VECCHIA} caratteri)"
	exit 3
fi
ok "vecchia: $VECCHIA"

# ---------------------------------------------------------------------------
log "2. La rotazione, a mano"
inf "si rigenerano i due certificati di RCP.md §4.1-bis"
$SSH "bash /media/REMOTIX/enter.sh --root \"bash /srv/src/01-b2-certificati.sh 192.168.0.2\"" \
	| grep -E "OK|NO" | sed 's/^/        /'
NUOVA=$($SSH "bash /media/REMOTIX/enter.sh --root \"openssl x509 -in /media/REMOTIX/b2-certificati/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0\"" | grep -oE '[A-Za-z0-9+/]{43}=' | tail -1)
if [ ${#NUOVA} -ne 44 ]; then
	ko "non ho l'impronta nuova"
	exit 3
fi
ok "nuova:   $NUOVA"
# ⛔ Il controllo che la rotazione sia AVVENUTA: due impronte uguali vorrebbero
#    dire che i certificati non sono cambiati, e i due tempi che seguono
#    proverebbero l'opposto di quel che dicono.
if [ "$VECCHIA" = "$NUOVA" ]; then
	ko "⛔ le due impronte sono UGUALI: il certificato non e' ruotato,"
	ko "   e il resto di questo giro non proverebbe niente"
	exit 4
fi
ok "⭐ le due impronte sono diverse: la rotazione c'e' stata"

# ---------------------------------------------------------------------------
log "3. ⭐ La pagina ritira l'impronta NUOVA e si collega"
inf "il conduttore della sonda legge l'impronta dal server, non da un file"
if ATTESO=APERTA bash "$QUI/01-b2-lancia-sonda.sh"; then
	ok "⭐ i due motori aprono la sessione con il certificato ruotato"
else
	ko "⛔ la sessione NON si apre dopo la rotazione"
	ESITO=1
fi

# ---------------------------------------------------------------------------
log "4. ⛔ E con l'impronta VECCHIA la sessione NON si apre"
inf "e' il controllo che rende vero il tempo 3: senza, «funziona con la nuova»"
inf "e' compatibile con un browser che l'impronta non la guarda affatto"
if IMPRONTA_FORZATA="$VECCHIA" ATTESO=NON-APERTA bash "$QUI/01-b2-lancia-sonda.sh"; then
	ok "⭐ rifiutata: il browser CONFRONTA l'impronta"
else
	ko "⛔ con l'impronta vecchia la sessione si e' aperta lo stesso, oppure"
	ko "   il motore non ha registrato: in tutt'e due i casi §4.1-bis non e'"
	ko "   provata"
	ESITO=1
fi

log "Esito"
if [ "$ESITO" -eq 0 ]; then
	ok "⭐ B3, quinto giro: la pagina ritira l'impronta corrente, e la vecchia"
	ok "   non vale piu'"
else
	ko "⛔ qualcosa non passa"
fi
inf "⚠ e la rotazione AUTOMATICA a quattordici giorni resta senza banco"
exit "$ESITO"
