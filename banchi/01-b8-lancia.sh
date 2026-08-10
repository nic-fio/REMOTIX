#!/bin/bash
#
# 01-b8-lancia.sh — gira SUL SERVER.  B8: il secondo fisso, e le tre mediane.
#
#   bash /media/REMOTIX/src/01-b8-lancia.sh              10 blocchi = 30 campioni per caso
#   bash /media/REMOTIX/src/01-b8-lancia.sh 4            un giro corto, per provare il banco
#   bash /media/REMOTIX/src/01-b8-lancia.sh previsione   che cosa mi aspetto, senza misurare
#
# ---------------------------------------------------------------------------
# ⛔ CHE COSA MISURA — e la spiegazione lunga sta in `01-b8-cronometro.py`
#
# `RCP.md` §4.4 vieta di distinguere nel MOTIVO fra «utente inesistente» e
# «parola sbagliata».  §4.4-bis impone il **ritardo fisso di un secondo** perche'
# quella distinzione non si legga col **cronometro**.  ⭐ E' una proprieta' di
# sicurezza che nessun altro banco vede, e una regressione che la togliesse non
# farebbe fallire niente.
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' IL SERVER SI SPEGNE E RIACCENDE A OGNI BLOCCO
#
# I due contatori di §4.4-bis sopravvivono a tutto tranne che al processo: dopo
# cinque fallimenti il server risponde `TROPPI_TENTATIVI` **senza interrogare
# PAM**, cioe' per una strada diversa con un tempo diverso — e un banco che non
# se ne accorgesse **misurerebbe il limitatore credendo di misurare PAM**.
#
# `rcp_azzera_registro_sessioni()` esiste in `banchi/rcp/rcp.c` per il banco, ma
# ⛔ **non la chiama nessuno**: non c'e' messaggio, segnale o opzione che ci
# arrivi.  Quindi l'unico modo di ripartire da contatori azzerati — e di poterlo
# DICHIARARE, come vuole B0.1 — e' un processo nuovo.  Ogni blocco e' una vita
# del server, e dentro una vita il banco resta sotto soglia per costruzione.
#
# ⚠ E il prezzo si paga in chiaro: un processo nuovo ha le cache fredde, quindi
#   i primi tre tentativi di ogni blocco sono una **scaldata** e si scartano —
#   ma si stampano lo stesso (forma E9).
#
# ---------------------------------------------------------------------------
# ⛔ E PERCHE' IL SERVER SI ACCENDE SU 0.0.0.0
#
# §4.4-bis conta i fallimenti **anche per indirizzo di provenienza**, e un
# successo azzera solo il contatore **del nome** (`azzera_tentativi(s->utente)`).
# Il controllo «4 falliti · un successo · altri 4» condotto da un indirizzo solo
# riceverebbe `TROPPI_TENTATIVI` all'ottavo **anche su un server che azzera
# perfettamente**: e' B0.3, e la cura che B0.3 prescrive e' **cambiare indirizzo
# di provenienza**.  Su `0.0.0.0` la stessa macchina raggiunge il server come
# `127.0.0.1` e come `192.168.0.2`: due chiavi diverse, quattro fallimenti
# ciascuna, e l'unico contatore che puo' parlare e' quello per nome.
#
# ⛔ Nessuna redirezione ATTORNO a `enter.sh` (si porterebbe via la richiesta di
#    password di sudo) e nessuna sottoshell in secondo piano: la regola del 10
#    agosto 2026, pagata quattro volte.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
WT="$FUORI/01-b2-lancia-wt.sh"
SORG=$DENTRO/b2/ngtcp2/examples/http3_server_proto_codec.cc
SERVER=$DENTRO/b2/ngtcp2/build/examples/bsslserver
PORTA=7447
LEGAME=0.0.0.0
INDIRIZZI=127.0.0.1,192.168.0.2
PER_CASO=3          # campioni tenuti per caso in ogni vita del server

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-10}

# ---------------------------------------------------------------------------
log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

if [ "$AZIONE" = previsione ]; then
	bash "$ENTRA" --root "python3 $DENTRO/01-b8-cronometro.py --previsione"
	exit 0
fi
case "$AZIONE" in
	''|*[!0-9]*)
		ko "argomento sconosciuto: «$AZIONE»  (un numero di blocchi | previsione)"
		exit 2 ;;
esac
BLOCCHI=$AZIONE
if [ "$BLOCCHI" -lt 1 ]; then
	ko "zero blocchi: non c'e' niente da misurare, e non e' «tutto passato»"
	exit 2
fi

# ---------------------------------------------------------------------------
# ⛔ LO STATO INIZIALE SI DICHIARA E SI VERIFICA — B0.1, e i file si buttano
#    PRIMA.  Il validatore di B4 ha gia' dichiarato «conforme» una registrazione
#    rimasta li' dal giro precedente: un verde da un file stantio e' il piu'
#    caro di tutti.  ⭐ E ogni riga porta il numero del GIRO, cosi' il verdetto
#    puo' rifiutarsi di giudicare un file che non e' di questo giro.
log "1. Lo stato iniziale"
GIRO=$(date +%Y%m%d-%H%M%S)
rm -f "$FUORI/b8-campioni.jsonl" "$FUORI/b8-server.log" "$FUORI/b8-stato.txt"
inf "giro: $GIRO"
inf "blocchi: $BLOCCHI  ·  campioni tenuti per caso: $((BLOCCHI * PER_CASO))"
inf "⚠ ogni blocco e' una vita del server: $((BLOCCHI + 2)) accensioni in tutto"
# ⚠ Il conto e' grezzo apposta: 11 tentativi per blocco, ciascuno almeno il
#   secondo fisso, piu' l'accensione.  Serve a sapere se si sta avviando una
#   cosa da cinque minuti o da un'ora, non a essere esatto.
inf "⚠ durata dell'ordine di $(( (BLOCCHI + 2) * 25 / 60 ))–$(( (BLOCCHI + 2) * 45 / 60 )) minuti"
inf "⚠ e fa $((BLOCCHI * 4 + 8)) autenticazioni FALLITE sull'utente di prova: se un"
inf "  giorno la pila PAM avesse un pam_faillock, quell'utente si bloccherebbe"

# ⛔ CHE SERVER E' QUELLO CHE STO PER ACCENDERE.
#    B8 non ricostruisce niente (lo fa B5): ma un binario senza l'innesto di RCP
#    non risponderebbe a `CIAO`, e il sintomo sarebbe «il banco dei tempi non
#    misura niente» invece di «il server e' un altro».  Si guardano tre cose e
#    si stampano: l'innesto nel sorgente, la data del sorgente, la data del
#    binario.  ⚠ Un binario piu' VECCHIO del sorgente innestato e' un binario
#    che quell'innesto non ce l'ha.
bash "$ENTRA" --root \
	"{ grep -c 'REMOTIX B3' $SORG; stat -c %Y $SORG; stat -c %Y $SERVER; stat -c %y $SERVER; } > $DENTRO/b8-stato.txt 2>&1"
if [ ! -f "$FUORI/b8-stato.txt" ]; then
	ko "non ho potuto guardare lo stato del server: il file non e' stato scritto"
	exit 2
fi
INNESTO=$(sed -n 1p "$FUORI/b8-stato.txt")
T_SORG=$(sed -n 2p "$FUORI/b8-stato.txt")
T_BIN=$(sed -n 3p "$FUORI/b8-stato.txt")
QUANDO=$(sed -n 4p "$FUORI/b8-stato.txt")
case "$INNESTO" in
	''|*[!0-9]*) ko "non ho potuto contare l'innesto di RCP nel sorgente:"
	             sed 's/^/        /' "$FUORI/b8-stato.txt"; exit 2 ;;
esac
if [ "$INNESTO" -lt 3 ]; then
	ko "⛔ l'innesto di RCP NON e' nel sorgente ($INNESTO righe «REMOTIX B3»)"
	ko "   questo server non parla RCP: rilancia 01-b5-lancia.sh, che ricostruisce"
	exit 3
fi
ok "l'innesto di RCP e' nel sorgente ($INNESTO righe) · binario del $QUANDO"
if [ "$T_BIN" -lt "$T_SORG" ]; then
	ko "⛔ il binario e' PIU' VECCHIO del sorgente innestato: dentro non c'e'"
	ko "   quel che si legge nel .cc.  Ricostruisci prima di misurare."
	exit 3
fi

# ---------------------------------------------------------------------------
# ⛔ E la previsione si stampa PRIMA dei numeri, o non e' una previsione.
log "2. Che cosa mi aspetto, prima di misurare"
bash "$ENTRA" --root "python3 $DENTRO/01-b8-cronometro.py --previsione"

# ---------------------------------------------------------------------------
# Una vita del server: accendi, misura, spegni, e porta via il registro.
# ⛔ Il registro si accumula perche' `01-b2-lancia-wt.sh accendi` lo azzera a
#    ogni accensione: senza la copia, il verdetto leggerebbe il registro
#    dell'ultimo blocco e lo chiamerebbe «il registro del giro».
UNA_VITA() # $1 = descrizione, $2.. = argomenti del cronometro
{
	local che=$1; shift
	bash "$WT" accendi "$LEGAME" "$PORTA"
	if [ $? -ne 0 ]; then
		ko "il server non si e' acceso per «$che»"
		return 4
	fi
	local pid
	pid=$(cat "$FUORI/b2-wt.pid" 2>/dev/null)
	bash "$ENTRA" --root "python3 -u $DENTRO/01-b8-cronometro.py \
		--porta $PORTA --indirizzi $INDIRIZZI --giro $GIRO \
		--uscita $DENTRO/b8-campioni.jsonl $*"
	local esito=$?
	# ⛔ B0.5: dopo aver misurato, il server dev'essere ancora li'.  Un server
	#    morto a meta' blocco lascia campioni «lenti» che sono solo connessioni
	#    fallite, e la diagnosi partirebbe da PAM.
	if [ -n "$pid" ] && [ -d "/proc/$pid" ]; then
		ok "il server e' ancora vivo dopo «$che» (PID $pid)"
	else
		ko "⛔ IL SERVER E' MORTO durante «$che»"
		esito=4
	fi
	printf '\n===== %s =====\n' "$che" >> "$FUORI/b8-server.log"
	if [ -f "$FUORI/b2-wt.log" ]; then
		cat "$FUORI/b2-wt.log" >> "$FUORI/b8-server.log"
	else
		printf '(nessun registro per questo blocco)\n' >> "$FUORI/b8-server.log"
	fi
	bash "$WT" spegni
	return $esito
}

# ---------------------------------------------------------------------------
log "3. I campioni — $BLOCCHI vite del server, $PER_CASO campioni per caso ciascuna"
inf "in ogni vita: 3 scaldate (scartate) + $((PER_CASO * 3)) tentativi in terzine ruotate"
b=1
while [ "$b" -le "$BLOCCHI" ]; do
	log "3.$b  blocco $b di $BLOCCHI"
	UNA_VITA "blocco $b" --blocco "$b" --per-caso "$PER_CASO"
	ESITO=$?
	if [ "$ESITO" -eq 2 ]; then
		ko "⛔ il blocco $b non e' partito (piano o stato iniziale): mi fermo"
		ko "   meglio nessun campione che campioni presi fuori dal bilancio"
		exit 2
	fi
	if [ "$ESITO" -ne 0 ]; then
		ko "il blocco $b e' finito male (uscita $ESITO): mi fermo"
		exit "$ESITO"
	fi
	b=$((b + 1))
done

# ---------------------------------------------------------------------------
# ⭐ IL CONTROLLO, IN DUE GAMBE IDENTICHE TRANNE IL QUINTO PASSO.
#    Ciascuna in una vita nuova del server: dentro una gamba i contatori devono
#    partire da zero, o non si sta interrogando l'azzeramento ma la storia.
log "4. ⭐ Il controllo positivo: 4 falliti · un successo · altri 4"
inf "atteso: otto CREDENZIALI_ERRATE, e l'OTTAVO non bloccato (§4.4-bis)"
UNA_VITA "controllo con-successo" --controllo con-successo
ESITO_A=$?

log "5. ⛔ E il controllo che dice NO: la stessa cosa SENZA il successo"
inf "atteso: al SESTO fallito arriva TROPPI_TENTATIVI.  Senza questa gamba,"
inf "        «otto rossi puliti» sarebbe verde anche su un server che non"
inf "        blocca mai — cioe' non proverebbe l'azzeramento (rilievo R3.9)"
UNA_VITA "controllo senza-successo" --controllo senza-successo
ESITO_B=$?

if [ "$ESITO_A" -eq 2 ] || [ "$ESITO_B" -eq 2 ]; then
	ko "⛔ una gamba del controllo non e' partita: il verdetto sarebbe cieco"
	ko "   («non ho niente da misurare» non e' «tutto passato»)"
	exit 2
fi
if [ "$ESITO_A" -ne 0 ] || [ "$ESITO_B" -ne 0 ]; then
	# ⚠ Non si esce: il verdetto guarda i tentativi che ci sono e dira' quale
	#   gamba e' incompleta.  Uscire qui butterebbe via anche i campioni buoni.
	ko "⚠ una gamba del controllo e' finita male (A=$ESITO_A B=$ESITO_B):"
	ko "  il verdetto qui sotto lo dira' tentativo per tentativo"
fi

# ---------------------------------------------------------------------------
log "6. Il verdetto — lo confronta il banco, non chi legge (B0.4)"
bash "$ENTRA" --root "python3 -u $DENTRO/01-b8-cronometro.py --verdetto \
	--giro $GIRO --uscita $DENTRO/b8-campioni.jsonl \
	--registro $DENTRO/b8-server.log"
ESITO=$?

log "Esito"
# ⛔ QUATTRO ESITI, NON DUE.  «Non si separano» e «non ho guardato abbastanza da
#    poterlo dire» sono due fatti con due cure diverse, e dare loro lo stesso
#    colore e' la forma E8 applicata a un verdetto.
case "$ESITO" in
	0) ok "⭐ B8 passa — e le risoluzioni qui sopra dicono fin dove ha guardato" ;;
	3) ko "⚠ B8 SOSPESO: rilancia con piu' blocchi (adesso $BLOCCHI)" ;;
	2) ko "⛔ B8: non c'e' stato niente da giudicare" ;;
	*) ko "⛔ B8: qualcosa non passa" ;;
esac
inf "i campioni, uno per riga: $FUORI/b8-campioni.jsonl"
inf "il registro del server, tutte le vite: $FUORI/b8-server.log"
exit "$ESITO"
