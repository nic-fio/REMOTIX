#!/bin/bash
#
# 04-b20-stacco.sh — ⛔ GIRA SUL SERVER (NIC-OS), FUORI dal contenitore, DA ROOT.
# La scena intera di `SPECIFICHE.md` §5.2 / invariante **I4**, dall'inizio alla
# fine e **due volte di fila**.
#
#   sudo bash .../04-b20-stacco.sh giro
#
# ⭐ Sta in un file solo, e non e' pigrizia: la scena alterna misure sull'HOST
#    (i monitor, i processi) e un client DENTRO il contenitore (dove sta
#    `aioquic`), e spezzarla in dodici chiamate da CHUWI vorrebbe dire dodici
#    strette di mano in mezzo alla misura.  ⛔ Da root, `enter.sh` si chiama da
#    qui: `sudo -n` per root e' un salto a vuoto.
#
# ===========================================================================
# ⛔ I SETTE PASSI, e sono quelli chiesti — non a pezzi
# ===========================================================================
#   1. il client si attacca, e il desktop si vede
#   2. ⭐ una finestra che lavora DA SOLA e che si accorgerebbe di perdere lo
#      schermo: scrive l'ora sullo schermo **e su un file**
#   3. il client si stacca
#   4. ⛔ con NESSUNO collegato: quanti monitor, il processo e' vivo, il
#      registro della Shell dice qualcosa
#   5. si ASPETTA — minuti, non istanti: un difetto che scatta al primo giro
#      d'orologio non si vede in tre secondi
#   6. ⭐ ci si riattacca, e si guarda se si ritrova **la stessa finestra con
#      l'ora andata avanti** — non una nuova, non uno schermo vuoto
#   7. ⛔ e poi una SECONDA volta di fila (`LEZIONI.md` §2.3-ter: un banco che
#      passa solo da macchina pulita non e' un banco, e' una dimostrazione)
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
UTENTE=${UTENTE:-provaa1}
UID_B=${UID_B:-1002}
PAROLA=${PAROLA:-provaa1-2026}
PORTA=${PORTA:-7601}
LAV=${LAV:-/media/REMOTIX/tmp/04-b20}
DENTRO=${DENTRO:-/srv/remotix/tmp/04-b20}
BANCHI_DENTRO=${BANCHI_DENTRO:-/srv/src/04-a1-src/banchi}
ATTESA_LUNGA=${ATTESA_LUNGA:-240}     # ⛔ i minuti del passo 5
ENTRA=/media/REMOTIX/enter.sh

log() { printf '\n\033[1m======== %s\033[0m\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

P="bash $QUI/04-b20-persistenza.sh"

dentro() { bash "$ENTRA" --root "$1"; }

# ⛔ Il client si attacca e poi SE NE VA: e' lo stacco vero, la stessa strada
#    della scheda che si chiude.  ⚠ In primo piano, perche' il momento in cui
#    finisce **e'** il momento dello stacco, e dedurlo da un `sleep` vorrebbe
#    dire misurare l'orologio invece della sessione.
client() {
	local et=$1 quanto=$2
	dentro "cd $BANCHI_DENTRO && python3 02-filo-cliente.py --porta $PORTA \
--utente $UTENTE --parola-file $DENTRO/parola --larghezza 1920 --altezza 1080 \
--attesa $quanto --registra $DENTRO/$et.rcpreg 2>&1 | tail -6"
}

giudica() {
	local et=$1
	dentro "cd $BANCHI_DENTRO && python3 04-b20-desktop-vero.py \
--registrazione $DENTRO/$et.rcpreg --lavoro $DENTRO --etichetta $et \
--scena 'persistenza: finestra che scrive l ora, stacco e riattacco' \
--esiti $DENTRO/04-b20-esiti.jsonl 2>&1 | tail -9"
}

[ "$(id -u)" -eq 0 ] || { echo "⛔ va lanciato DA ROOT"; exit 2; }
printf '%s' "$PAROLA" > "$LAV/parola"; chmod 600 "$LAV/parola"

log "PASSO 2 — la finestra che lavora da sola"
$P scena || exit 3
PID_PRIMA=$(pgrep -u "$UID_B" -f 'banco-A1-orologio' | head -1)
RIGHE_PRIMA=$(wc -l < "/run/user/$UID_B/banco-A1-orologio.log")
inf "⭐ il pid dell'orologio ADESSO e' $PID_PRIMA — se alla fine e' un altro,"
inf "   quella non e' «la stessa finestra», e' una finestra nuova"

log "PASSO 1 — il client si attacca (e resta 45 s)"
client attacco-1 45 &
CLIENT=$!
sleep 22

log "⭐ I CONTROLLI POSITIVI — adesso, che un client E' attaccato"
$P controllo
ESITO_CONTROLLO=$?
$P guarda attaccato-1

wait $CLIENT
log "PASSO 3 — il client se n'e' andato"

log "PASSO 4 — subito dopo lo stacco, con NESSUNO collegato"
sleep 3
$P guarda subito-dopo-stacco-1

log "PASSO 5 — si aspetta $ATTESA_LUNGA s con nessuno collegato"
sleep "$ATTESA_LUNGA"
$P guarda dopo-attesa-1

log "PASSO 6 — ci si riattacca, e si guarda che cosa si ritrova"
client riattacco-1 25
giudica riattacco-1
$P guarda riattaccato-1

log "PASSO 7 — ⛔ E LA SECONDA VOLTA DI FILA"
sleep 3
$P guarda subito-dopo-stacco-2
sleep "$ATTESA_LUNGA"
$P guarda dopo-attesa-2
client riattacco-2 25
giudica riattacco-2
$P guarda riattaccato-2

log "IL CONFRONTO CHE CHIUDE"
PID_DOPO=$(pgrep -u "$UID_B" -f 'banco-A1-orologio' | head -1)
RIGHE_DOPO=$(wc -l < "/run/user/$UID_B/banco-A1-orologio.log")
inf "orologio: pid $PID_PRIMA all'inizio, pid ${PID_DOPO:-⛔ MORTO} alla fine"
inf "righe scritte: $RIGHE_PRIMA all'inizio, $RIGHE_DOPO alla fine"
if [ "$PID_PRIMA" = "${PID_DOPO:-}" ] && [ "$RIGHE_DOPO" -gt "$RIGHE_PRIMA" ]; then
	printf '    \033[1;32m⭐ E'"'"' LA STESSA FINESTRA, E HA CONTINUATO A LAVORARE\033[0m\n'
else
	printf '    \033[1;31m⛔ NON e'"'"' la stessa finestra, o si e'"'"' fermata\033[0m\n'
fi
[ "$ESITO_CONTROLLO" -eq 0 ] || printf '    \033[1;31m⛔ e i controlli positivi NON reggevano: il resto vale poco\033[0m\n'
inf "esiti: $LAV/04-b20-persistenza.jsonl"
exit 0
