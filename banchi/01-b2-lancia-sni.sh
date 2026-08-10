#!/bin/bash
#
# 01-b2-lancia-sni.sh — gira SUL SERVER, fuori dal contenitore, e conduce
#                       l'intera prova SNI di B2.
#
#   bash /media/REMOTIX/src/01-b2-lancia-sni.sh costruisci
#   bash /media/REMOTIX/src/01-b2-lancia-sni.sh misura
#
# ---------------------------------------------------------------------------
# PERCHE' UN FILE INVECE DI UNA RIGA DI COMANDO
#
# ⛔ Il 9 agosto 2026 una diagnosi a mano e' passata per TRE shell annidate
#    (locale -> ssh -> enter.sh -> chroot) e si e' rotta sulle virgolette,
#    restituendo un «No such file or directory» che sembrava un fatto sul
#    codice.  La regola della fase 0 vale qui: le righe di comando si mettono
#    in un file, non si ricordano.
#
# ⚠ E i processi si fermano per PID, mai con `pkill -f`: il 9 agosto `pkill -f`
#   ha ucciso DUE VOLTE il processo che lo stava eseguendo, perche' il modello
#   compariva anche nella sua riga di comando.  Qui ogni server scrive il
#   proprio PID in un file, e si ferma quello.
#
# ⚠ Il chroot NON e' uno spazio di nomi separato: i PID di dentro sono PID
#   dell'ospite, e i file di /srv/src sono gli stessi di /media/REMOTIX/src.
#   E' per questo che il PID scritto dentro si legge da fuori.
# ---------------------------------------------------------------------------
set -uo pipefail

ENTRA=/media/REMOTIX/enter.sh
FUORI=/media/REMOTIX/src                 # come si vede dall'ospite
DENTRO=/srv/src                          # come si vede dal contenitore
CERT=/media/REMOTIX/b2-certificati       # dentro il contenitore

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

AZIONE=${1:-misura}
IND=${2:-192.168.0.2}

if [ "$AZIONE" = costruisci ]; then
	log "Costruzione del bersaglio ngtcp2 (dentro il contenitore, da root)"
	bash "$ENTRA" --root "bash $DENTRO/01-b2-sni-ngtcp2.sh"
	STATO=$?
	inf "lo script di costruzione e' uscito con $STATO"
	exit "$STATO"
fi
if [ "$AZIONE" != misura ]; then
	ko "azione sconosciuta: $AZIONE  (costruisci | misura)"
	exit 2
fi

NGTCP2="$DENTRO/b2/ngtcp2/build/examples/bsslserver"
LSQUIC="$DENTRO/b2/lsquic/build/bin/b2_wt_server"

porta_libera()
{
	# ⛔ IL CONTROLLO CHE IL 10 AGOSTO 2026 MANCAVA, e che e' costato la prima
	#    esecuzione: DUE server della sessione del 9 agosto erano ancora vivi —
	#    l'aioquic di controllo su 7447 e `b2_wt_server` su 7448, otto ore dopo
	#    — e tenevano le porte.  `bsslserver` ha scritto «Could not bind» ed e'
	#    morto, e la sonda avrebbe letto quel silenzio come «ngtcp2 rifiuta».
	#
	# ⚠ Cioe': il rischio non era un rosso, era un rosso ATTRIBUITO ALLA
	#   LIBRERIA.  Il rootfs del server e' in RAM e non si riavvia mai, quindi
	#   «lo avevo fermato» non e' un'informazione: si guarda.
	local porta=$1
	local chi
	chi=$(bash "$ENTRA" --root "ss -ulnp | grep ':$porta '")
	if [ -n "$chi" ]; then
		ko "la porta $porta e' GIA' occupata — la misura non parte:"
		printf '%s\n' "$chi" | sed 's/^/        /'
		ko "fermalo per PID (mai con pkill -f) e rilancia"
		return 1
	fi
	inf "porta $porta libera"
	return 0
}

avvia()
{
	# $1 = etichetta (nome del file di registro e del PID), $2.. = comando
	local et=$1; shift
	rm -f "$FUORI/b2-sni-$et.log" "$FUORI/b2-sni-$et.pid"
	# ⚠ `< /dev/null`: senza, il processo staccato tiene aperto il terminale
	#   di ssh e la sessione remota non finisce piu' — la prima esecuzione del
	#   10 agosto e' rimasta appesa per questo, non per un difetto del server.
	#
	# ⛔ E `nohup` invece di `setsid`, per una ragione che e' costata la terza
	#    esecuzione: `setsid` FORCA, quindi `$!` e' il PID di setsid — che esce
	#    subito — e non quello del server.  Il banco ha dichiarato MORTI due
	#    server che erano vivi, e `lsquic` lo smentiva tre righe sotto con un
	#    «in ascolto» stampato nel suo stesso registro.
	#    ⚠ E' un FALSO ROSSO su un controllo di sanita', cioe' la forma piu'
	#      insidiosa: avrebbe fermato la misura invece di falsarla, ma se
	#      avesse riguardato una sola delle due candidate l'avrebbe eliminata.
	bash "$ENTRA" --root \
		"nohup $* < /dev/null > $DENTRO/b2-sni-$et.log 2>&1 & echo \$! > $DENTRO/b2-sni-$et.pid"
	sleep 2
	local p=""
	[ -f "$FUORI/b2-sni-$et.pid" ] && p=$(cat "$FUORI/b2-sni-$et.pid")
	if [ -z "$p" ]; then
		ko "$et: nessun PID scritto — non e' partito niente"
		return 1
	fi
	# ⛔ Due controlli, non uno, e il secondo e' quello che conta: «il processo
	#    e' vivo» non e' «il processo ASCOLTA».  Un server che parte e non
	#    riesce a legarsi alla porta e' vivo per un istante, e alla sonda fa lo
	#    stesso effetto di una libreria che rifiuta.
	# ⛔ `[ -d /proc/$p ]` e NON `kill -0`.  Quarta esecuzione del 10 agosto
	#    2026, e il difetto e' esemplare: il server gira come ROOT dentro il
	#    contenitore, questo script gira come utente normale sull'ospite, e
	#    `kill -0` su un processo altrui restituisce «operazione non
	#    permessa» — cioe' un errore — non «non esiste».
	#    ⚠ Il banco leggeva un PERMESSO NEGATO come una MORTE, e dichiarava
	#      morti due server che stavano ascoltando.  /proc lo sanno tutti.
	if [ ! -d "/proc/$p" ]; then
		ko "$et e' MORTO subito dopo l'avvio (PID $p).  Il registro dice:"
		sed 's/^/        /' "$FUORI/b2-sni-$et.log"
		return 1
	fi
	local ascolto
	ascolto=$(bash "$ENTRA" --root "ss -ulnp | grep 'pid=$p,'")
	if [ -z "$ascolto" ]; then
		ko "$et (PID $p) e' vivo ma NON tiene nessuna porta UDP:"
		sed 's/^/        /' "$FUORI/b2-sni-$et.log"
		return 1
	fi
	ok "$et in ascolto, PID $p"
	printf '%s\n' "$ascolto" | sed 's/^/        /'
	if [ -s "$FUORI/b2-sni-$et.log" ]; then
		inf "primo respiro:"
		head -4 "$FUORI/b2-sni-$et.log" | sed 's/^/        /'
	fi
	return 0
}

ferma()
{
	local et=$1 p=""
	[ -f "$FUORI/b2-sni-$et.pid" ] && p=$(cat "$FUORI/b2-sni-$et.pid")
	if [ -n "$p" ]; then
		bash "$ENTRA" --root "kill $p || true"
		inf "fermato $et (PID $p)"
	fi
	rm -f "$FUORI/b2-sni-$et.pid"
}

# ---------------------------------------------------------------------------
# ⛔ LE CREDENZIALI SI PRENDONO UNA VOLTA SOLA, E ALLA LUCE.
#
# La seconda esecuzione del 10 agosto 2026 e' rimasta appesa qui, e la causa
# non era il banco: era `>/dev/null 2>&1` messo su una chiamata a `enter.sh`.
# Quella chiamata era la PRIMA della sessione, quindi `sudo -v -S` chiedeva la
# parola d'ordine — e la richiesta finiva nel nulla insieme al resto.  Chi
# guardava vedeva un programma fermo senza nessuna domanda sullo schermo.
#
# ⚠ E' la stessa forma del difetto del 9 agosto: `2>/dev/null` che nasconde
#   l'errore che avrebbe spiegato tutto.  Qui nascondeva una DOMANDA, che e'
#   peggio: un errore nascosto fa sbagliare diagnosi, una domanda nascosta
#   ferma la macchina.
#
# ⛔ Da cui la regola di questo file: le chiamate a `enter.sh` non si zittiscono
#    mai.  E la prima si fa qui, esplicita, cosi' la richiesta arriva quando
#    chi guarda sa perche'.
log "Credenziali per il contenitore"
bash "$ENTRA" --root "true"
if [ $? -ne 0 ]; then
	ko "non si entra nel contenitore: la misura non parte"
	exit 2
fi
ok "sudo validato per questa sessione"

# ---------------------------------------------------------------------------
log "1. ngtcp2 — il bersaglio della prova"
inf "atteso: PASSA senza SNI.  La previsione sta in 01-b2-sonda-sni.py e in"
inf "        DECISIONI.md §6.4, ed e' stata scritta PRIMA di questa esecuzione."
ferma bsslserver
porta_libera 7447 || exit 3
# ⚠ `env LD_LIBRARY_PATH=...`: gli esempi di ngtcp2 si collegano alla libreria
#   CONDIVISA, che nel banco non sta in un percorso di sistema (il perche' e'
#   scritto in 01-b2-sni-ngtcp2.sh).  Senza questa riga il server muore
#   all'avvio, e la sonda leggerebbe quel silenzio come un rifiuto.
if avvia bsslserver "env LD_LIBRARY_PATH=$DENTRO/b2/ngtcp2/build/lib $NGTCP2 $IND 7447 $CERT/sessione.key $CERT/sessione.pem"; then
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b2-sonda-sni.py --indirizzo $IND --porta 7447 --etichetta ngtcp2 --atteso passa --certificato $CERT/sessione.pem"
	ESITO_NG=$?
else
	ESITO_NG=4
fi
inf "sonda ngtcp2: uscita $ESITO_NG"
inf "che cosa ha visto il server (ultime righe del suo registro):"
tail -6 "$FUORI/b2-sni-bsslserver.log" | sed 's/^/        /'
ferma bsslserver

# ---------------------------------------------------------------------------
log "2. lsquic — il CONTROLLO NEGATIVO"
inf "atteso: FALLISCE senza SNI.  Se passasse, il 9 agosto l'abbiamo eliminata"
inf "        a torto — e sarebbe la sonda ad aver trovato un errore NOSTRO."
inf "⭐ e la gamba CON SNI e' l'unica misura nuova su lsquic: «fallisce senza»"
inf "   non e' «riesce con», e finora era stata provata solo la prima meta'."
ferma b2_wt_server
porta_libera 7448 || exit 3
# ⛔ DUE voci nella mappa dei certificati, non una: quella per l'indirizzo e
#    quella per il NOME che usa la gamba di controllo.  Senza la seconda,
#    «con SNI» fallirebbe per il motivo sbagliato — nessun certificato sotto
#    quel nome — e il controllo direbbe «lsquic non funziona nemmeno con
#    l'SNI», che e' falso e chiuderebbe la diagnosi al contrario.
#
# ⚠ E `-L debug`, non `-L info`: la riga «SNI is not set» — l'unico testimone
#   indipendente di che cosa sia arrivato sul filo — esce solo a debug.
if avvia b2_wt_server "$LSQUIC -s $IND:7448 -c $IND,$CERT/sessione.pem,$CERT/sessione.key -c remotix.prova,$CERT/sessione.pem,$CERT/sessione.key -L debug"; then
	bash "$ENTRA" --root \
		"python3 $DENTRO/01-b2-sonda-sni.py --indirizzo $IND --porta 7448 --etichetta lsquic --atteso fallisce --certificato $CERT/sessione.pem"
	ESITO_LS=$?
else
	ESITO_LS=4
fi
inf "sonda lsquic: uscita $ESITO_LS"

# ---------------------------------------------------------------------------
# ⛔ SU LSQUIC IL VERDETTO NON LO DA' LA SONDA, LO DA' IL SUO REGISTRO.
#
# La sonda vede due connessioni fallite e si rifiuta — giustamente — di
# concludere: da fuori, «fallita» e «fallita» si somigliano.  Ma i due
# fallimenti hanno cause DIVERSE, e la differenza e' esattamente la domanda:
#
#   senza SNI -> «SNI is not set ... fail certificate lookup»  = muore SULL'SNI
#   con SNI   -> «looked up cert for remotix.prova»            = l'SNI e' bastato
#
# ⚠ La seconda connessione poi cade lo stesso, ma PIU' AVANTI e per un'altra
#   ragione (avviso TLS 120, «no suitable application protocol»).  Quella
#   ragione NON e' stata indagata e resta aperta: qui interessa solo che il
#   certificato sia stato trovato, perche' e' il gradino che dipende dall'SNI.
REG_LS="$FUORI/b2-sni-b2_wt_server.log"
SENZA=$(grep -c "SNI is not set" "$REG_LS")
CON=$(grep -c "looked up cert for remotix.prova" "$REG_LS")
inf "righe «SNI is not set»               : $SENZA"
inf "righe «looked up cert for remotix...»: $CON"
if [ "$SENZA" -ge 1 ] && [ "$CON" -ge 1 ]; then
	ok "⭐ la diagnosi del 9 agosto si chiude: senza SNI lsquic non TROVA il"
	ok "   certificato; con l'SNI lo trova.  Il difetto e' l'SNI."
	ESITO_LS=0
else
	ko "⛔ il registro non contiene tutt'e due le righe: la diagnosi resta a meta'"
	ESITO_LS=1
fi

# ⭐ IL TESTIMONE INDIPENDENTE.  Queste righe le scrive un programma che non e'
#    nostro, guardando il filo dall'altro capo: sono l'unica conferma di che
#    cosa sia davvero arrivato nell'estensione `server_name`, e non vengono
#    dalla stessa libreria che l'ha spedita.
inf "che cosa ha visto il server (le righe che nominano SNI o il certificato):"
grep -i "sni\|certificate\|handshake failed\|handshake success" "$FUORI/b2-sni-b2_wt_server.log" | head -12 | sed 's/^/        /'
ferma b2_wt_server

# ---------------------------------------------------------------------------
log "Riepilogo"
inf "ngtcp2: $([ "${ESITO_NG:-9}" -eq 0 ] && echo 'come atteso' || echo "NON come atteso (uscita ${ESITO_NG:-9})")"
inf "lsquic: $([ "${ESITO_LS:-9}" -eq 0 ] && echo 'come atteso' || echo "NON come atteso (uscita ${ESITO_LS:-9})")"
inf "i registri restano in $FUORI/b2-sni-*.log"
if [ "${ESITO_NG:-9}" -eq 0 ] && [ "${ESITO_LS:-9}" -eq 0 ]; then
	exit 0
fi
exit 1
