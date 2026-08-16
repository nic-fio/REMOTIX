#!/bin/bash
#
# 01-b2-lancia-wt.sh — gira SUL SERVER, e misura il server minimo di B2.
#
#   bash /media/REMOTIX/src/01-b2-lancia-wt.sh
#
# ---------------------------------------------------------------------------
# CHE COSA MISURA
#
# `FASI.md` §01-filo-nudo, gruppo 2: **una sessione WebTransport su `/rcp/1`,
# e un byte che torna**.  Qui la si prova senza browser, col cliente di prova
# — che e' necessario e NON sufficiente (`LEZIONI.md`: e' E10, la prova verde
# sul client sbagliato).  Il browser viene dopo, e con la pagina.
#
# ⛔ E CON IL CONTROLLO CHE DICE NO, che nelle due revisioni del 9 agosto
#    cadeva ogni volta: `RCP.md` §2.2 impone che il server **NON DEVE**
#    accettare una sessione su un percorso diverso, e che il rifiuto sia
#    **404** (rilievo R1.24).  Un banco che prova solo il percorso giusto non
#    distingue «il server controlla il percorso» da «il server accetta
#    qualunque cosa».
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati
SERVER="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ⚠ Tre azioni, e servono perche' la misura col BROWSER ha bisogno che il
#   server resti in piedi mentre la conduce un altro script, sull'altra
#   macchina.  «misura» accende, prova col cliente di prova e spegne.
AZIONE=${1:-misura}
IND=${2:-192.168.0.2}
PORTA=${3:-7447}
# ⚠ Le opzioni in piu' del server: servono a B3, che alza `max_idle_timeout` a
#   120 s per distinguere «il server sa che una sessione e' staccata» da «QUIC
#   ha chiuso da se'» (rilievo R3.19).
# ⛔ `shift 3` con MENO di tre argomenti non sposta niente e non fallisce in
#    modo utile: `$*` restava «accendi», il server riceveva il nome
#    dell'azione come opzione e moriva con «port: invalid port number».
#    Visto il 10 agosto 2026 — e il sintomo era un cliente che «non si
#    collega», cioe' il rosso di nuovo sull'imputato sbagliato.
if [ $# -gt 3 ]; then
	shift 3
	OPZIONI="$*"
else
	OPZIONI=""
fi

# ---------------------------------------------------------------------------
# ⛔ FERMARE PER PID VUOL DIRE PRIMA GUARDARE CHE PID E' — rilievo R8.13.
#
# Il file del PID puo' essere di ieri: lo cancella solo chi ferma per bene, e
# un'esecuzione interrotta lo lascia li'.  Il rootfs del server vive in RAM e si
# riavvia, mentre `/media/REMOTIX/src` sopravvive: al riavvio i PID ripartono
# dal basso e quel numero indica **un processo di sistema**.  ⛔ Poi si faceva
# `kill` da root dentro il contenitore, con `|| true` a nascondere anche
# l'errore.
#
# ⭐ La cura costa una lettura: `/proc/<pid>/comm` dice il nome del programma, e
#    `enter.sh` usa `chroot` e non uno spazio dei nomi dei PID — i numeri sono
#    gli stessi da tutt'e due i lati, quindi si legge da qui senza sudo.
# ⚠ E dopo il `kill` si CONTROLLA che sia morto, prima di buttare il file:
#    cancellarlo prima e' perdere l'unico appiglio che si aveva.
ferma_per_pid() # $1 = file del PID, $2 = nome atteso del programma
{
	local file=$1 atteso=$2 p="" comm=""
	[ -f "$file" ] && p=$(cat "$file" 2>/dev/null)
	if [ -z "$p" ]; then
		printf '    --  nessun server da fermare\n'
		return 0
	fi
	if [ ! -d "/proc/$p" ]; then
		printf "    --  il PID %s non esiste piu': butto il file\n" "$p"
		rm -f "$file"
		return 0
	fi
	comm=$(cat "/proc/$p/comm" 2>/dev/null)
	if [ "$comm" != "$atteso" ]; then
		ko "⛔ il PID $p adesso e' «$comm», non «$atteso»: NON lo ammazzo."
		ko "   Il file $file e' di un'esecuzione precedente, e i PID si"
		ko "   riusano.  Lo butto e basta — guarda tu che cos'e' quel processo."
		rm -f "$file"
		return 1
	fi
	bash "$ENTRA" --root "kill $p"
	local esito=$?
	if [ "$esito" -ne 0 ]; then
		ko "il kill del PID $p ($comm) e' fallito (uscita $esito)"
		return 1
	fi
	# ⚠ Un `kill` riuscito e' un segnale consegnato, non un processo morto.
	local n=0
	while [ -d "/proc/$p" ] && [ "$n" -lt 10 ]; do
		sleep 1
		n=$((n + 1))
	done
	if [ -d "/proc/$p" ]; then
		ko "il PID $p ($comm) e' ancora vivo dopo $n secondi: non butto il file"
		return 1
	fi
	rm -f "$file"
	printf '    --  fermato il server (PID %s, %s)\n' "$p" "$comm"
	return 0
}

if [ "$AZIONE" = spegni ]; then
	ferma_per_pid "$FUORI/b2-wt.pid" "$(basename "$SERVER")"
	exit $?
fi
if [ "$AZIONE" != misura ] && [ "$AZIONE" != accendi ]; then
	ko "azione sconosciuta: $AZIONE  (misura | accendi | spegni)"
	exit 2
fi

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

# ---------------------------------------------------------------------------
# ⛔ «PORTA LIBERA» E «NON HO POTUTO GUARDARE» NON SONO LA STESSA COSA — R8.15.
#
# `CHI=$(bash enter.sh --root "ss | grep …")` cattura solo lo standard output, e
# QUATTRO esiti diversi danno la stessa stringa vuota: `enter.sh` fallito su un
# mount o su una credenziale scaduta, `ss` assente nel chroot, `grep` che non
# trova, e la porta davvero libera.  ⛔ Il banco leggeva «non ho potuto
# guardare» come «non c'e' niente», lanciava un secondo server sopra il primo, e
# il rosso che seguiva arrivava su un imputato sbagliato.  E' la stessa forma che
# questo file combatte poco piu' sotto scegliendo `/proc` invece di `kill -0`.
#
# ⭐ La cura: l'elenco si scrive in un FILE, e la redirezione sta dentro le
#    virgolette del comando remoto — mai attorno a `enter.sh`, che se ne
#    porterebbe via la richiesta di password di sudo.  Poi si guardano tre cose
#    distinte: lo stato di `enter.sh`, lo stato di `ss`, e il contenuto.
#
# Esce 0 = occupata · 1 = libera · 2 = non ho potuto guardare.
guarda_porta() # $1 = porta
{
	local p=$1
	rm -f "$FUORI/b2-porte.txt" "$FUORI/b2-porte.stato"
	bash "$ENTRA" --root \
		"ss -ulnp > $DENTRO/b2-porte.txt 2>&1; echo \$? > $DENTRO/b2-porte.stato"
	local entrata=$?
	if [ "$entrata" -ne 0 ]; then
		ko "non si e' potuto guardare le porte: enter.sh e' uscito $entrata"
		return 2
	fi
	if [ ! -f "$FUORI/b2-porte.stato" ] || [ ! -f "$FUORI/b2-porte.txt" ]; then
		ko "non si e' potuto guardare le porte: l'elenco non e' stato scritto"
		return 2
	fi
	local stato_ss
	stato_ss=$(cat "$FUORI/b2-porte.stato")
	if [ "$stato_ss" != 0 ]; then
		ko "«ss» dentro il contenitore e' uscito $stato_ss:"
		sed 's/^/        /' "$FUORI/b2-porte.txt"
		return 2
	fi
	grep ":$p " "$FUORI/b2-porte.txt" | sed 's/^/        /' && return 0
	return 1
}

log "La porta"
guarda_porta "$PORTA"
LIBERA=$?
if [ "$LIBERA" -eq 2 ]; then
	exit 3
fi
if [ "$LIBERA" -eq 0 ]; then
	ko "la porta $PORTA e' gia' occupata (l'elenco e' qui sopra)"
	ko "fermalo per PID (mai con pkill -f) e rilancia"
	exit 3
fi
ok "porta $PORTA libera"

# ---------------------------------------------------------------------------
log "Il server minimo (l'esempio di ngtcp2 con lo strato WebTransport innestato)"
rm -f "$FUORI/b2-wt.log" "$FUORI/b2-wt.pid"
bash "$ENTRA" --root \
	"nohup env LD_LIBRARY_PATH=$LIBS $SERVER $OPZIONI $IND $PORTA $CERT/sessione.key $CERT/sessione.pem < /dev/null > $DENTRO/b2-wt.log 2>&1 & echo \$! > $DENTRO/b2-wt.pid"
sleep 2
PID=$(cat "$FUORI/b2-wt.pid" 2>/dev/null)
# ⛔ `/proc`, non `kill -0`: il server e' di root e questo script no — e da
#    utente normale `kill -0` risponde «operazione non permessa», cioe' un
#    errore, non «non esiste» (10 agosto 2026).
if [ -z "$PID" ] || [ ! -d "/proc/$PID" ]; then
	ko "il server non e' partito.  Il registro dice:"
	sed 's/^/        /' "$FUORI/b2-wt.log"
	exit 4
fi
# ⛔ «IN ASCOLTO» VUOL DIRE «SU QUESTA PORTA» — rilievo R8.14.
#
#    `grep 'pid=$PID,'` e' vero per QUALUNQUE porta UDP tenuta da quel
#    processo: un server che ignorasse i suoi argomenti posizionali e si legasse
#    alla propria porta predefinita passava il controllo, e il banco stampava
#    «in ascolto» su un fatto falso.  E' il necessario preso per sufficiente
#    (E1), proprio nel file che racconta il difetto degli argomenti storti.
guarda_porta "$PORTA"
TIENE=$?
if [ "$TIENE" -eq 2 ]; then
	exit 4
fi
if [ "$TIENE" -ne 0 ] || ! grep ":$PORTA " "$FUORI/b2-porte.txt" | grep -q "pid=$PID,"; then
	ko "il server e' vivo ma NON tiene la porta $PORTA (l'elenco e' qui sopra)"
	sed 's/^/        /' "$FUORI/b2-wt.log"
	exit 4
fi
ok "in ascolto sulla porta $PORTA, PID $PID"
inf "quel che ha detto all'avvio:"
grep "REMOTIX B2" "$FUORI/b2-wt.log" | head -4 | sed 's/^/        /'

fermare() {
	# ⚠ Stessa strada dello spegnimento: si guarda che PID sia, e si controlla
	#   che sia morto prima di buttare il file (R8.13).
	ferma_per_pid "$FUORI/b2-wt.pid" "$(basename "$SERVER")"
}

if [ "$AZIONE" = accendi ]; then
	ok "il server resta acceso: fermalo con «01-b2-lancia-wt.sh spegni»"
	inf "l'impronta del certificato della sessione, per la pagina:"
	bash "$ENTRA" --root \
		"openssl x509 -in $CERT/sessione.pem -outform der | openssl dgst -sha256 -binary | base64 -w0" \
		| tail -1 | sed 's/^/        /'
	exit 0
fi

# ---------------------------------------------------------------------------
log "1. Il percorso GIUSTO — /rcp/1"
inf "atteso: :status 200, e i byte tornano identici"
bash "$ENTRA" --root \
	"python3 $DENTRO/01-b2-cliente-aioquic.py https://$IND:$PORTA/rcp/1"
ESITO_SI=$?
inf "cliente di prova: uscita $ESITO_SI"

# ---------------------------------------------------------------------------
log "2. ⛔ Il percorso SBAGLIATO — /rcp/9, il controllo che dice NO"
inf "atteso: 404.  RCP.md §2.2: un percorso sconosciuto si rifiuta, e"
inf "        il rilievo R1.24 ha scelto 404 fra i tre stati che erano leciti."
# ⛔ Il numero si passa al cliente e il confronto lo fa lui — rilievo R8.8.
#    Prima si teneva solo «uscita diversa da zero», e un timeout della CONNECT,
#    l'UDP filtrato o un server gia' morto davano lo stesso verde: il controllo
#    che dice NO non distingueva il rifiuto dal fallimento.  Adesso l'atteso e'
#    **404**, cioe' quel che il documento chiede, e ogni altro esito e' rosso.
bash "$ENTRA" --root \
	"python3 $DENTRO/01-b2-cliente-aioquic.py https://$IND:$PORTA/rcp/9 404"
ESITO_NO=$?
inf "cliente di prova: uscita $ESITO_NO (atteso: 0, cioe' «rifiutato con 404»)"

# ---------------------------------------------------------------------------
log "Che cosa ha visto il server"
grep "REMOTIX B2" "$FUORI/b2-wt.log" | sed 's/^/        /'

fermare

log "Esito"
BENE=0
if [ "$ESITO_SI" -eq 0 ]; then
	ok "/rcp/1: sessione aperta e byte tornati"
else
	ko "/rcp/1: NON ha funzionato (uscita $ESITO_SI)"
	BENE=1
fi
if [ "$ESITO_NO" -eq 0 ]; then
	ok "/rcp/9: RIFIUTATO con 404, come impone §2.2"
else
	ko "⛔ /rcp/9 NON e' stato rifiutato con 404 (uscita $ESITO_NO):"
	ko "   o il server lo accetta — e allora e' una violazione di RCP.md"
	ko "   §2.2 — o il rifiuto e' arrivato con un altro stato, o la prova"
	ko "   non e' nemmeno partita.  Il registro qui sopra dice quale."
	BENE=1
fi
inf "il registro completo resta in $FUORI/b2-wt.log"
exit "$BENE"
