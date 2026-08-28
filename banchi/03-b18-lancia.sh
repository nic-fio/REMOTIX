#!/bin/bash
#
# 03-b18-lancia.sh — ⛔ GIRA SU CHUWI.  Il banco del CREDITO (§2.3) e il caso
# «credito» di 03-b15, sulla porta **7612** e su una COPIA del prodotto.
#
#   bash banchi/03-b18-lancia.sh certifica    ⭐ gira QUI, senza rete e senza server
#   bash banchi/03-b18-lancia.sh porte        conta 7448 · 7501 · 7561 e i vicini
#   bash banchi/03-b18-lancia.sh porta        copia src/ e i banchi sulla macchina
#   bash banchi/03-b18-lancia.sh costruisci   `make` dentro il contenitore
#   bash banchi/03-b18-lancia.sh terreno      la parola di prova, 0600
#   bash banchi/03-b18-lancia.sh accendi      il server DA ROOT sulla 7612
#   bash banchi/03-b18-lancia.sh scena-avvia  ⛔ A SESSIONE APERTA, mai prima
#   bash banchi/03-b18-lancia.sh b15 [caso]   03-b15-movimento.py
#   bash banchi/03-b18-lancia.sh b18 [caso]   03-b18-credito.py
#   bash banchi/03-b18-lancia.sh cura         03-b18b-cura.py (V1..V4)
#   bash banchi/03-b18-lancia.sh guasta <ago> ⛔ l'ago nella COPIA
#   bash banchi/03-b18-lancia.sh risana <ago>
#   bash banchi/03-b18-lancia.sh registro [quante]
#   bash banchi/03-b18-lancia.sh spegni
#
# ===========================================================================
# ⛔ IL PERIMETRO, E PERCHE' E' TUTTO PROPRIO
#
# `FASI.md` §03-movimento: «ogni step ha porta, file di ban e socket propri: in
# fase 3 i banchi girano in parallelo per davvero, e due banchi che condividono
# un ban-file si fermano a vicenda».
#
#   porta      7612                              (⛔ 7603 e 7605 e 7615 sono di
#                                                 altri gruppi e girano ADESSO)
#   albero     /media/REMOTIX/src/03-b18-src     una COPIA: l'ago si pianta qui
#   banchi     /media/REMOTIX/src/03-b18/        i miei, in una cartella mia
#   lavoro     /media/REMOTIX/tmp/03-b18         ban, socket, certificati,
#                                                registro, pid, rilievo
#   scena      remotix-03-b18                    ⛔ il nome della memoria
#                                                condivisa e' PROPRIO: due scene
#                                                con lo stesso nome si pestano
#
# ⛔ LE TRE PORTE CHE NON SI TOCCANO: **7448**, **7501** e soprattutto **7561**,
#    quella che l'utente apre.  ⇒ Si CONTANO prima e dopo, e non si toccano.
#
# ⛔ E SI DIPENDE INVECE DI RISCRIVERE (`CODER.md` §4.1): chi accende il server e
#    la scena e' `03-b15-accendi.sh`, che prende gia' porta, albero, cartella di
#    lavoro e scena dall'ambiente.  ⚠ Le variabili si passano con `env` DENTRO
#    `sudo`, e non come `sudo VAR=val`: con `env_reset` sudo rifiuta la seconda
#    forma, e il messaggio arriva su stderr dove nessuno lo guarda.
#
# ⛔ NIENTE `set -e`: si contano i rossi e si va avanti, cosi' alla fine c'e' un
#    denominatore.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
RADICE=$(cd -- "$QUI/.." && pwd)
SSHPW="$RADICE/fondamenta/strumenti/sshpw.py"

FUORI=/media/REMOTIX/src
DENTRO=/srv/src
MIO=$FUORI/03-b18
MIO_DENTRO=$DENTRO/03-b18
ALBERO=$FUORI/03-b18-src
ALBERO_DENTRO=$DENTRO/03-b18-src
PORTA=7612
LAV=/media/REMOTIX/tmp/03-b18
LAV_DENTRO=/srv/remotix/tmp/03-b18
SCENA_LAV=$FUORI/03-b18-scena
SCENA_LAV_DENTRO=$DENTRO/03-b18-scena
SCENA_SHM=remotix-03-b18
UTENTE=${UTENTE:-nicfio}
ACCENDI=$FUORI/03-b18/03-b15-accendi.sh

# L'ambiente che `03-b15-accendi.sh` legge.  ⛔ In una riga sola e citata una
# volta: un elenco ripetuto in sei posti diverge al primo cambiamento.
AMB="PORTA=$PORTA D=$ALBERO/src LAV=$LAV SCENA_LAV=$SCENA_LAV SCENA_SHM=$SCENA_SHM"

log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()   { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

fuori()  { timeout 900 python3 "$SSHPW" "$1"; }
dentro() { timeout 900 python3 "$SSHPW" "bash /media/REMOTIX/enter.sh --root \"$1\""; }
metti()  { timeout 300 python3 "$SSHPW" --put "$1" "$2"; }
# ⛔ Da root, sull'HOST (non nel contenitore): il palco appartiene all'utente e
#    il server deve poter fare `setpriv` verso di lui.
root()   { fuori "sudo -S -p 'Password sudo: ' env $AMB bash $ACCENDI $*"; }

AZIONE=${1:-}

case "$AZIONE" in
certifica)
	# ⛔ Gira QUI, su CHUWI, senza rete e senza server: e' la ragione per cui i
	#    controlli dei due banchi sono funzioni pure sul verbale.
	e=0
	log "03-b15-movimento.py --certifica"
	python3 "$QUI/03-b15-movimento.py" --certifica || e=$((e+1))
	log "03-b18-credito.py --certifica"
	python3 "$QUI/03-b18-credito.py" --certifica || e=$((e+1))
	exit "$e" ;;

aghi)
	python3 "$QUI/03-b18-innesta.py" --elenco
	exit 0 ;;

porte)
	log "Le porte, contate — 7448 · 7501 · 7561 NON si toccano"
	fuori "ss -tuln | grep -E ':(7448|7501|7561|76[0-9][0-9])\b' | sort"
	exit 0 ;;

porta)
	log "1. I sorgenti del prodotto, in un albero MIO (una COPIA)"
	# ⛔ La cartella si CANCELLA prima di ricopiarla: un file di ieri rimasto
	#    li' dentro risponde «esisto» come uno di adesso.  ⚠ E su CHUWI `rsync`
	#    non c'e' — misurato, non supposto.
	fuori "rm -rf $ALBERO/src $ALBERO/banchi && mkdir -p $ALBERO/src $ALBERO/banchi/rcp $MIO && mkdir -p $LAV" \
		|| { ko "non ho potuto rifare $ALBERO"; exit 2; }
	tar czf /tmp/03-b18-src.tgz -C "$RADICE" src banchi/rcp || { ko "tar fallito"; exit 2; }
	metti /tmp/03-b18-src.tgz "$ALBERO/src.tgz" || { ko "scp fallito"; exit 2; }
	fuori "cd $ALBERO && tar xzf src.tgz && ls src/rcp.c banchi/rcp/rcp.c" \
		|| { ko "l'albero non si e' srotolato"; exit 2; }
	bash "$0" banchi
	exit $? ;;

banchi)
	log "I banchi, in una cartella MIA"
	# ⛔ Nella stessa cartella, perche' i banchi caricano i fratelli con
	#    `os.path.join(QUI, ...)`.  ⚠ E in una cartella mia e non accanto a
	#    quelli degli altri gruppi: in fase 3 i banchi girano davvero in
	#    parallelo, e sovrascrivere il file di un altro mentre lo sta girando
	#    e' un rosso che nessuno saprebbe attribuire.
	for f in 03-b15-movimento.py 03-b18-credito.py 03-b18b-cura.py \
	         03-b18-innesta.py 03-b15-accendi.sh 01-b3-cliente.py \
	         02-filo-fotogramma.py 03-scena.c; do
		metti "$QUI/$f" "$MIO/$f" || { ko "scp di $f fallito"; exit 2; }
	done
	ok "otto file → $MIO/"
	exit 0 ;;

costruisci)
	log "make, dentro il contenitore, nell'albero 03-b18-src"
	# ⛔ `costruisci.sh` butta il binario vecchio PRIMA di costruire, confronta
	#    `rcp.c` con la copia gemella e verifica le marche dentro il binario:
	#    «c'e'» diventa «e' di adesso».  ⚠ E i gemelli si confrontano ANCHE col
	#    guasto innestato, perche' l'ago si pianta in tutt'e due.
	dentro "cd $ALBERO_DENTRO/src && bash costruisci.sh"
	exit $? ;;

guasta|risana)
	AGO=${2:-}
	[ -n "$AGO" ] || { ko "uso: $0 $AZIONE <ago>   (elenco: $0 aghi)"; exit 2; }
	TOGLI=""
	[ "$AZIONE" = risana ] && TOGLI=--togli
	log "L'ago «$AGO» nella COPIA — mai nel prodotto di casa"
	dentro "python3 $MIO_DENTRO/03-b18-innesta.py --albero $ALBERO_DENTRO --ago $AGO $TOGLI" \
		|| { ko "l'ago non e' stato $( [ "$AZIONE" = guasta ] && echo innestato || echo tolto )"; exit 3; }
	bash "$0" costruisci || { ko "⛔ non si e' ricostruito: il binario NON e' di adesso"; exit 3; }
	bash "$0" riaccendi || exit 3
	exit 0 ;;

stato-ago)
	dentro "python3 $MIO_DENTRO/03-b18-innesta.py --albero $ALBERO_DENTRO --stato"
	exit $? ;;

terreno)
	log "La parola d'ordine, in un file 0600 (difetto D12)"
	PW=$(sed -n 's/^pass[[:space:]]*:[[:space:]]*//p' "$HOME/SERVER.ssh" 2>/dev/null)
	[ -n "$PW" ] || { ko "⛔ non ho letto la parola da ~/SERVER.ssh"; exit 2; }
	umask 077
	printf '%s' "$PW" > /tmp/03-b18-parola
	fuori "mkdir -p $MIO/tmp" || exit 2
	metti /tmp/03-b18-parola "$MIO/tmp/parola" || exit 2
	rm -f /tmp/03-b18-parola
	fuori "chmod 600 $MIO/tmp/parola && ls -l $MIO/tmp/parola"
	ok "la parola e' sulla macchina, 0600, e mai in un argv"
	exit 0 ;;

scena-costruisci)
	log "La scena dello step 2, costruita DENTRO il contenitore"
	dentro "SCENA_LAV=$SCENA_LAV_DENTRO SCENA_C=$MIO_DENTRO/03-scena.c bash $MIO_DENTRO/03-b15-accendi.sh scena-costruisci"
	exit $? ;;

accendi|riaccendi|spegni|stato|scena-avvia|scena-ferma|scena-conta|scena-uscite)
	log "$AZIONE — porta $PORTA, lavoro $LAV"
	root "$AZIONE ${2:-}"
	exit $? ;;

registro)
	root "registro ${2:-60}"
	exit $? ;;

credito)
	# ⭐ Le righe che decidono §2.3, senza doverle cercare a mano.
	fuori "sudo -S -p 'Password sudo: ' grep -a -E '§2.3|mancanza di posto|streams_uni|stream uni' $LAV/registro.log | tail -${2:-30}"
	exit $? ;;

b15|b18|cura)
	CASO=${2:-tutti}
	# ⛔⭐ CHE COS'E' IL PRODOTTO ADESSO, CHIESTO E NON RICORDATO.
	#     Un file di esiti che mescola i giri sul prodotto sano e quelli sul
	#     prodotto guasto senza dire quale e' quale mette due cose diverse sotto
	#     la stessa etichetta (forma E2).  ⚠ E si CHIEDE all'albero invece di
	#     dedurlo dall'ultimo comando dato: chi legge questo file domani non ha
	#     modo di sapere che cosa avevo in mente io.
	AGO=$(dentro "python3 $MIO_DENTRO/03-b18-innesta.py --albero $ALBERO_DENTRO --stato" 2>/dev/null \
		| sed -n "s/.*ago «\([a-z0-9]*\)»: INNESTATO.*/\1/p" | paste -sd, -)
	[ -n "$AGO" ] && NOTA="⛔ GUASTO — aghi innestati: $AGO" || NOTA="sano (nessun ago innestato)"
	inf "il prodotto sulla $PORTA e': $NOTA"

	COM=""; ATTESA=""
	case "$AZIONE" in
	b15)  COM="python3 $MIO_DENTRO/03-b15-movimento.py --caso $CASO --nota '$NOTA' --uscita $MIO_DENTRO/03-b15-esiti.jsonl"
	      ATTESA="--attesa ${ATTESA_S:-30}" ;;
	b18)  COM="python3 $MIO_DENTRO/03-b18-credito.py --caso $CASO --nota '$NOTA' --uscita $MIO_DENTRO/03-b18-esiti.jsonl"
	      ATTESA="--attesa ${ATTESA_S:-30}" ;;
	cura) COM="python3 $MIO_DENTRO/03-b18b-cura.py --nota '$NOTA' --uscita $MIO_DENTRO/03-b18b-esiti.jsonl" ;;
	esac
	log "La misura — $AZIONE «$CASO»"

	# ⛔⭐⭐ LA SCENA SI ACCENDE **A SESSIONE APERTA**, E NON PRIMA.  E' la
	#      trappola misurata il 13 agosto 2026, e costa una misura intera.
	#
	#      Un compositore Wayland consegna un fotogramma solo quando qualcosa
	#      cambia — ma Mutter non manda nemmeno i *frame callback* a una
	#      superficie che sta su un monitor **che nessuno sta registrando**.  Il
	#      palco del prodotto e' un monitor VIRTUALE, e lo si registra solo
	#      mentre una sessione RCP e' attaccata.  ⇒ Una scena avviata prima
	#      resta VIVA e non disegna: resta ferma dentro `wl_display_dispatch`,
	#      il banco conta ZERO fotogrammi e il rosso finisce sul prodotto.
	#      `[M]` 13 agosto 2026, ore 15:30: «la scena e' viva ma non ha ancora
	#      stampato un conteggio», e il registro del server diceva 16 attese a
	#      vuoto con «scena ferma».
	#
	# ⭐ Da cui l'ordine: la misura parte PRIMA, in sottofondo; si aspetta il
	#    MARCATORE che il server scrive quando comincia a catturare; e solo
	#    allora si accende la scena.  ⛔ Un marcatore e non uno `sleep`: PAM ci
	#    mette il suo, e un tempo indovinato un giorno non basta.
	bash "$0" scena-ferma >/dev/null 2>&1
	# ⛔ Il conto lo fa uno SCRIPT SUL SERVER (`03-b15-accendi.sh cattura-conta`)
	#    e non una riga annidata dentro `ssh → enter.sh → bash -c`: un file non
	#    ha livelli di virgolette, e un `grep` con gli spazi infilato li' dentro
	#    contava zero su un registro che la riga ce l'aveva — «non ho guardato»
	#    travestito da «non e' successo».  `[M]` 13 agosto 2026, primo giro.
	conta_marca()
	{
		root cattura-conta 2>/dev/null \
			| sed -n 's/.*CONTO=\([0-9][0-9]*\).*/\1/p' | tail -1
	}
	PRIMA=$(conta_marca); PRIMA=${PRIMA:-0}
	inf "il ciclo dei fotogrammi si e' acceso $PRIMA volte finora"

	TRACCIA=$(mktemp -t 03-b18-misura.XXXXXX)
	# ⛔ Dentro il contenitore, perche' aioquic sta li'.  ⚠ `--indirizzo
	#   127.0.0.1`: il server ascolta su 0.0.0.0 e il contenitore condivide la
	#   rete dell'host, quindi il loopback e' lo stesso.
	dentro "$COM --indirizzo 127.0.0.1 --porta $PORTA --utente $UTENTE --parola-file $MIO_DENTRO/tmp/parola --registro $LAV_DENTRO/registro.log $ATTESA ${3:-}" \
		> "$TRACCIA" 2>&1 &
	MISURA=$!

	g=0; acceso=0
	while [ "$g" -lt 20 ]; do
		[ -d "/proc/$MISURA" ] || break
		ADESSO=$(conta_marca); ADESSO=${ADESSO:-0}
		if [ "$ADESSO" -gt "$PRIMA" ]; then acceso=1; break; fi
		g=$((g+1))
	done
	if [ "$acceso" -eq 1 ]; then
		ok "il palco sta catturando: adesso la scena ha senso"
		bash "$0" scena-avvia | tail -3
	else
		ko "⛔ il palco NON ha cominciato a catturare: accendere la scena adesso"
		ko "   produrrebbe uno zero che accusa il prodotto invece della scena."
		ko "   ⚠ La misura prosegue e dira' NON PROVATO — che e' il verdetto vero."
	fi

	wait "$MISURA"; e=$?
	cat "$TRACCIA"
	rm -f "$TRACCIA"
	exit "$e" ;;

esiti)
	fuori "tail -${2:-6} $MIO/03-b18-esiti.jsonl"
	exit $? ;;

prepara)
	falle=0
	for passo in porta costruisci terreno riaccendi scena-costruisci; do
		bash "$0" "$passo" || { ko "il passo «$passo» e' fallito"; exit 3; }
	done
	# ⛔ La scena si accende DOPO il server e DOPO che un utente e' entrato: il
	#    monitor del palco nasce col figlio, e prima non esiste nessun nome da
	#    chiedere.  ⇒ Un primo giro breve fa nascere il figlio, poi la scena.
	bash "$0" b15 movimento "--attesa 3" >/dev/null 2>&1
	bash "$0" scena-avvia || { ko "la scena non si accende: NON misuro"; exit 3; }
	ok "⭐ pronto: server sulla $PORTA, scena viva"
	exit "$falle" ;;

*)
	sed -n '2,28p' "$0"
	exit 2 ;;
esac
