#!/bin/bash
#
# 01-b2-lancia-impostazioni.sh — gira SUL SERVER.  Chiede alle due candidate,
#                                sul filo, se dichiarano WebTransport.
#
#   bash /media/REMOTIX/src/01-b2-lancia-impostazioni.sh
#
# ---------------------------------------------------------------------------
# ⛔ LA REGOLA NATA DALLE 333 RIGHE DI LSQUIC
#
# Si prova per prima **la cosa che puo' uccidere la candidata**, prima di
# scrivere il collante.  Per l'SNI e' costata una connessione e ha eliminato
# `lsquic`; qui la domanda e': **il server riesce a DICHIARARE WebTransport?**
# Senza quella dichiarazione un browser non apre la sessione, e non c'e' riga
# di codice nostro che rimedi — quel frame lo scrive la libreria.
#
# ⭐ E il controllo positivo e' `ngtcp2` col nostro strato innestato: li' le
#    due dichiarazioni CI SONO.  Se la sonda non le vedesse nemmeno li', il
#    verdetto non sarebbe sulle librerie: sarebbe sulla sonda.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src
DENTRO=/srv/src
CERT=/media/REMOTIX/b2-certificati
NGTCP2="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
LIBS="$DENTRO/b2/ngtcp2/build/lib"
QUICHE="$DENTRO/b2/quiche/quiche/examples/http3-server"
DIRQ="$CERT/quiche"
IND=${1:-192.168.0.2}

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

log "Credenziali per il contenitore"
bash "$ENTRA" --root "true" || { ko "non si entra nel contenitore"; exit 2; }
ok "sudo validato"

# ⛔ L'ELENCO DELLE PORTE SI SCRIVE IN UN FILE, E LO STATO SI GUARDA — R8.15.
#
# `chi=$(bash enter.sh --root "ss | grep …")` prende solo lo standard output, e
# «la porta e' libera» diventava indistinguibile da «enter.sh e' fallito», «ss
# non c'e' nel chroot» e «grep non ha trovato».  Il caso concreto: si smonta
# `devroot/proc`, il banco dichiara la porta libera, ci lancia sopra un secondo
# server, e il rosso che segue arriva su un imputato sbagliato.
#
# ⚠ La redirezione sta DENTRO le virgolette del comando remoto: attorno a
#   `enter.sh` si porterebbe via la richiesta di password di sudo.
# Esce 0 = elenco letto · 2 = non ho potuto guardare.
leggi_porte()
{
	rm -f "$FUORI/b2-imp-porte.txt" "$FUORI/b2-imp-porte.stato"
	bash "$ENTRA" --root \
		"ss -ulnp > $DENTRO/b2-imp-porte.txt 2>&1; echo \$? > $DENTRO/b2-imp-porte.stato"
	local entrata=$?
	if [ "$entrata" -ne 0 ]; then
		ko "non si e' potuto guardare le porte: enter.sh e' uscito $entrata"
		return 2
	fi
	if [ ! -f "$FUORI/b2-imp-porte.stato" ] || [ ! -f "$FUORI/b2-imp-porte.txt" ]; then
		ko "non si e' potuto guardare le porte: l'elenco non e' stato scritto"
		return 2
	fi
	local stato_ss
	stato_ss=$(cat "$FUORI/b2-imp-porte.stato")
	if [ "$stato_ss" != 0 ]; then
		ko "«ss» dentro il contenitore e' uscito $stato_ss:"
		sed 's/^/        /' "$FUORI/b2-imp-porte.txt"
		return 2
	fi
	return 0
}

porta_libera()
{
	local p=$1
	leggi_porte || return 2
	if grep -q ":$p " "$FUORI/b2-imp-porte.txt"; then
		ko "la porta $p e' gia' occupata:"
		grep ":$p " "$FUORI/b2-imp-porte.txt" | sed 's/^/        /'
		return 1
	fi
	inf "porta $p libera"
	return 0
}

avvia()
{
	local et=$1 porta=$2; shift 2
	rm -f "$FUORI/b2-imp-$et.log" "$FUORI/b2-imp-$et.pid"
	bash "$ENTRA" --root \
		"nohup $* < /dev/null > $DENTRO/b2-imp-$et.log 2>&1 & echo \$! > $DENTRO/b2-imp-$et.pid"
	sleep 2
	local p=""
	[ -f "$FUORI/b2-imp-$et.pid" ] && p=$(cat "$FUORI/b2-imp-$et.pid")
	# ⚠ /proc e non `kill -0`: il server e' di root e questo script no.
	if [ -z "$p" ] || [ ! -d "/proc/$p" ]; then
		ko "$et non e' partito.  Il registro dice:"
		sed 's/^/        /' "$FUORI/b2-imp-$et.log"
		return 1
	fi
	# ⛔ «IN ASCOLTO» VUOL DIRE «SULLA PORTA SU CUI ANDRA' LA SONDA» — R8.14.
	#
	#    `grep 'pid=$p,'` era vero per qualunque porta UDP di quel processo: un
	#    server che ignorasse i suoi argomenti posizionali e si legasse alla sua
	#    porta predefinita passava, e la riga «$et in ascolto» affermava un
	#    fatto che il banco non aveva verificato.  ⚠ Dove pesa: la gamba
	#    `quiche` di DECISIONI.md §6.4 lancia l'esempio altrui con due argomenti
	#    posizionali, ed e' esattamente questo il controllo che li verifica.
	leggi_porte || return 1
	if ! grep ":$porta " "$FUORI/b2-imp-porte.txt" | grep -q "pid=$p,"; then
		ko "$et e' vivo ma NON tiene la porta $porta:"
		grep ":$porta " "$FUORI/b2-imp-porte.txt" | sed 's/^/        /'
		sed 's/^/        /' "$FUORI/b2-imp-$et.log"
		return 1
	fi
	ok "$et in ascolto sulla porta $porta, PID $p"
	return 0
}

# ⛔ SI GUARDA CHE PID SIA, PRIMA DI AMMAZZARLO — rilievo R8.13.
#
# `ferma` gira anche PRIMA di `avvia`, quindi legge un file scritto da
# un'esecuzione precedente — e quel file resta li' se l'esecuzione e' stata
# interrotta.  Il rootfs del server vive in RAM e si riavvia mentre
# `/media/REMOTIX/src` sopravvive: al riavvio i PID ripartono dal basso e quel
# numero indica un processo di sistema, che si ammazzava **da root, dentro il
# chroot**, con `|| true` a nascondere pure l'errore.
#
# ⭐ `/proc/<pid>/comm` dice il nome del programma, e `enter.sh` usa `chroot`,
#    non uno spazio dei nomi dei PID: i numeri sono gli stessi da tutt'e due i
#    lati.  ⚠ L'etichetta E' il nome del programma atteso, e le due chiamate lo
#    rispettano: `bsslserver` e `http3-server`.
ferma()
{
	local et=$1 p="" comm=""
	[ -f "$FUORI/b2-imp-$et.pid" ] && p=$(cat "$FUORI/b2-imp-$et.pid")
	if [ -z "$p" ]; then
		return 0
	fi
	if [ ! -d "/proc/$p" ]; then
		rm -f "$FUORI/b2-imp-$et.pid"
		return 0
	fi
	comm=$(cat "/proc/$p/comm" 2>/dev/null)
	if [ "$comm" != "$et" ]; then
		ko "⛔ il PID $p adesso e' «$comm», non «$et»: NON lo ammazzo."
		ko "   Quel file del PID e' di un'esecuzione precedente."
		rm -f "$FUORI/b2-imp-$et.pid"
		return 1
	fi
	bash "$ENTRA" --root "kill $p"
	local esito=$?
	[ "$esito" -ne 0 ] && ko "il kill del PID $p ($comm) e' fallito (uscita $esito)"
	local n=0
	while [ -d "/proc/$p" ] && [ "$n" -lt 10 ]; do
		sleep 1
		n=$((n + 1))
	done
	[ -d "/proc/$p" ] && ko "il PID $p ($comm) e' ancora vivo dopo $n secondi"
	rm -f "$FUORI/b2-imp-$et.pid"
	return 0
}

# ---------------------------------------------------------------------------
log "1. ⭐ ngtcp2 col nostro strato — IL CONTROLLO POSITIVO"
inf "atteso: DICHIARA.  Se non dichiarasse, la sonda non sa leggere un"
inf "        SETTINGS e nessun numero della gamba 2 varrebbe niente."
ferma bsslserver
porta_libera 7447 || exit 3
if avvia bsslserver 7447 "env LD_LIBRARY_PATH=$LIBS $NGTCP2 $IND 7447 $CERT/sessione.key $CERT/sessione.pem"; then
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b2-sonda-impostazioni.py --indirizzo $IND --porta 7447 --etichetta ngtcp2 --atteso si"
	ESITO_NG=$?
else
	ESITO_NG=4
fi
inf "sonda ngtcp2: uscita $ESITO_NG"
ferma bsslserver

# ---------------------------------------------------------------------------
log "2. quiche, con tutto quel che la sua API C permette"
inf "atteso: NON dichiara.  La previsione e' in 01-b2-quiche-wt-innesta.py,"
inf "        scritta dopo la lettura dell'FFI e PRIMA di questa esecuzione."
# ⚠ Il loro esempio legge ./cert.crt e ./cert.key dalla cartella corrente e
#   NON controlla di averli caricati: senza, parte lo stesso e fallisce ogni
#   stretta di mano.  Si mettono, e si controlla che ci siano.
PREP=$(bash "$ENTRA" --root "mkdir -p $DIRQ; cp -f $CERT/sessione.pem $DIRQ/cert.crt; cp -f $CERT/sessione.key $DIRQ/cert.key; ls $DIRQ")
case "$PREP" in
*cert.crt*) ;;
*) ko "cert.crt non e' finito in $DIRQ"; exit 3 ;;
esac
ferma http3-server
porta_libera 7449 || exit 3
if avvia http3-server 7449 "env -C $DIRQ $QUICHE $IND 7449"; then
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b2-sonda-impostazioni.py --indirizzo $IND --porta 7449 --etichetta quiche --atteso no"
	ESITO_QU=$?
else
	ESITO_QU=4
fi
inf "sonda quiche: uscita $ESITO_QU"
ferma http3-server

# ---------------------------------------------------------------------------
log "Riepilogo"
inf "ngtcp2 (controllo positivo): $([ "${ESITO_NG:-9}" -eq 0 ] && echo 'come atteso' || echo "NON come atteso (${ESITO_NG:-9})")"
inf "quiche:                      $([ "${ESITO_QU:-9}" -eq 0 ] && echo 'come atteso' || echo "NON come atteso (${ESITO_QU:-9})")"
if [ "${ESITO_NG:-9}" -ne 0 ]; then
	ko "⛔ il controllo positivo e' fallito: nessuna riga su §6.4 si scrive da qui"
	exit 5
fi
[ "${ESITO_QU:-9}" -eq 0 ]
exit $?
