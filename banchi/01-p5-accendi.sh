#!/bin/bash
#
# 01-p5-accendi.sh — ⛔ GIRA DENTRO IL CONTENITORE.  Accende il bersaglio di P5:
# una COPIA del prodotto sulla porta 7501, che serve LA PROPRIA pagina.
#
#   bash /srv/src/01-p5-accendi.sh copia     rifa' la copia e la ricostruisce
#   bash /srv/src/01-p5-accendi.sh accendi
#   bash /srv/src/01-p5-accendi.sh spegni
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE — LA RICETTA ERA UN COMMENTO, E UN COMMENTO NON SI ESEGUE
#
# `01-b12-guasti.py`, voce P5, portava questa scena scritta a parole dentro la
# sua nota: copia, costruisci, accendi sulla 7501 con ban e socket propri.  ⚠ Una
# ricetta in prosa la ricopia a mano chi la usa, e ⛔ la prima volta che l'ho
# fatto io — la tarda serata dell'11 agosto 2026 — l'ho sbagliata in due modi che
# un file non avrebbe sbagliato:
#
#   1. il server e' stato acceso da una cartella qualunque, e ha scritto
#      «⛔ non apro pagina.html: No such file or directory».  ⭐ Il prodotto
#      cerca la sua pagina ACCANTO A SE': si accende da dentro la sua cartella,
#      e cosi' quel che P5 misura e' la pagina del PRODOTTO — non una copia
#      che le somiglia (`--pagina` qui NON si usa, ed e' la differenza con
#      `01-p5-ff-accendi.sh`, che invece deve servirne una strumentata);
#   2. `&` dentro tre livelli di virgolette (`ssh` → `enter.sh` → `bash -c`) non
#      arriva dove sembra.  ⭐ Un file non ha livelli di virgolette.
#
# ⛔ IL PERIMETRO: la porta (`PORTA`) piu' i cinque file che portano il
#    **prefisso** (`PREFISSO`, predefinito `sera-p15`) — ban, socket,
#    certificati, registro e file del pid.  ⚠ La 7448 ha un server vivo che non
#    e' di questo giro, la 7447 e' l'innesto di B2, la 7511 e' il banco del
#    congedo, e la 7501 e' il bersaglio di P5 gia' acceso.
#
#   ⭐ UN SECONDO BERSAGLIO, ACCANTO A QUELLO CHE C'E' GIA' (12 agosto 2026):
#
#       PREFISSO=p5r-7522 PORTA=7522 D=/srv/src/01-p5-copia-7522 \
#         bash /srv/src/01-p5-accendi.sh accendi
#
#      ⛔ Il prefisso NON e' facoltativo quando si cambia porta: senza, i due
#         bersagli si dividono lo stesso ban, lo stesso socket e lo stesso file
#         del pid — cioe' `spegni` ammazzerebbe quello sbagliato.
#
# ⛔ E IL GUASTO SI INNESTA NELLA COPIA, MAI NEL PRODOTTO DI CASA: P5 vuole il
#    server RIACCESO fra un passo e l'altro, e riaccendere il prodotto di casa
#    con un guasto dentro lo metterebbe sotto i piedi di chiunque altro lo
#    usasse.  E' la stessa ragione scritta nella voce P5 del catalogo.
#
# ⛔ B0.7: MARCATORI, NON `sleep`.  «Il processo e' vivo» e «la porta risponde»
#    sono due fatti diversi, e alla misura serve il secondo.
set -uo pipefail

PROD=${PROD:-/srv/src/remotix}
D=${D:-/srv/src/01-b12-copie/p5-remotix}
GEMELLO=${GEMELLO:-/srv/src/rcp}
TMP=/srv/src/tmp
PORTA=${PORTA:-7501}
IND=${IND:-192.168.0.2}

# ⛔⭐ IL PREFISSO — cura del 12 agosto 2026, e nasce da un difetto che stava
#     per essere commesso invece che da uno gia' pagato.
#
# `PORTA` e `D` erano gia' regolabili, ⛔ ma il ban, il socket, il registro, il
# certificato e il **file del pid** erano scritti `sera-p15` in chiaro.  ⇒ Un
# secondo bersaglio acceso su un'altra porta con questo stesso script avrebbe:
#
#   · cancellato `sera-p15-ban` e `sera-p15.sock` del bersaglio gia' vivo
#     (li' sotto c'e' un `rm -f` nel passo «accendi»);
#   · **sovrascritto `sera-p15.pid`**, e allora `spegni` avrebbe ammazzato il
#     processo sbagliato — o nessuno, lasciando il primo bersaglio vivo e senza
#     nessun file che dica qual era il suo pid.
#
# ⚠ E' esattamente la regola «un banco in parallelo ha porta, ban-file e socket
#   PROPRI»: qui il perimetro sta in UNA variabile, cosi' non se ne puo'
#   dimenticare un pezzo.  Il predefinito non cambia: chi lanciava prima misura
#   quel che misurava.
PREFISSO=${PREFISSO:-sera-p15}

CERT=$TMP/$PREFISSO-cert
BAN=$TMP/$PREFISSO-ban
SOCK=$TMP/$PREFISSO.sock
LOG=$TMP/$PREFISSO-browser.log
PIDF=$TMP/$PREFISSO.pid

mkdir -p "$TMP"

case "${1:-accendi}" in
spegni)
	if [ -f "$PIDF" ]; then
		pid=$(cat "$PIDF")
		# ⛔ Per PID e solo il proprio: `pkill -f remotix` porterebbe via anche
		#    il server della 7448 e quelli degli altri banchi.
		kill "$pid" 2>/dev/null
		g=0
		while [ -d "/proc/$pid" ] && [ "$g" -lt 20 ]; do sleep 0.5; g=$((g+1)); done
		[ -d "/proc/$pid" ] && printf 'NO  il pid %s non e\x27 morto\n' "$pid" \
		                    || printf 'OK  spento (pid %s)\n' "$pid"
		rm -f "$PIDF"
	else
		printf -- '--  nessun %s: non c\x27era niente di mio acceso\n' "$PIDF"
	fi
	rm -f "$SOCK"
	exit 0 ;;
copia)
	# ⛔ La copia si rifa' da zero: una copia vecchia risponde «esisto» come una
	#    di adesso (LEZIONI.md §1.9 punto 8).
	[ -d "$PROD" ] || { echo "NO  ⛔ $PROD non c'e'"; exit 2; }
	rm -rf "$D"
	mkdir -p "$(dirname "$D")"
	cp -a "$PROD" "$D"
	rm -f "$D"/*.o "$D/remotix"
	printf -- '--  copia: %s → %s\n' "$PROD" "$D"
	GEMELLO="$GEMELLO" bash "$D/costruisci.sh" || exit 3
	exit 0 ;;
svuota-registro)
	# ⛔⭐ SI RIFIUTA SE IL SERVER E' VIVO, e questa riga costa una spiegazione
	#     perche' e' costata un ROSSO FALSO — notte fra l'11 e il 12 agosto 2026.
	#
	# `: > file` su un registro che un processo tiene APERTO non lo azzera: il
	# file diventa lungo zero, ma il processo conserva il suo offset, e alla
	# prima riga che scrive il kernel riempie di NUL tutto quel che sta prima.
	# `[M]` il registro di P5 si e' ritrovato con **37.120 byte NUL in testa**.
	#
	# ⛔ E il danno non e' l'estetica del file: `grep` che incontra un NUL
	#    smette di stampare le righe e dice «binary file matches» — ⛔ **con lo
	#    stesso stato d'uscita 0**.  Il banco ha letto «NON LETTO» dove c'era
	#    scritto il nostro indirizzo, e ha sbloccato IL SERVER invece di noi,
	#    ricevendo il NON-BANNATO che quell'indirizzo dara' per sempre.
	#
	# ⭐ Il registro si azzera dove si azzera davvero: nel passo «accendi», che
	#    lo cancella mentre nessuno lo tiene aperto.
	if [ -f "$PIDF" ] && [ -d "/proc/$(cat "$PIDF" 2>/dev/null)" ]; then
		printf 'NO  ⛔ il server (pid %s) e\x27 vivo e tiene aperto questo registro:\n' "$(cat "$PIDF")"
		printf '    troncarlo adesso non lo azzera, ci scava dentro un buco di NUL\n'
		printf '    che acceca ogni «grep» del banco.  Spegni prima, o riaccendi:\n'
		printf '      bash %s spegni  &&  bash %s accendi\n' "$0" "$0"
		exit 2
	fi
	: > "$LOG"
	printf 'OK  registro azzerato: %s  (nessun processo lo teneva aperto)\n' "$LOG"
	exit 0 ;;
accendi) ;;
*) echo "uso: $0 [copia|accendi|spegni|svuota-registro]"; exit 2 ;;
esac

command -v ss >/dev/null || { echo "NO  ⛔ «ss» non c'e': non ho guardato la porta, e non la chiamo libera"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$n" -ne 0 ]; then
	echo "NO  ⛔ la porta $PORTA e' gia' occupata ($n righe): non e' mia, non la tocco"
	ss -tuln | grep ":$PORTA\b"
	exit 2
fi
echo "OK  porta $PORTA libera (ss ha guardato e ha stampato $n righe su di lei)"

[ -x "$D/remotix" ] || { echo "NO  ⛔ $D/remotix non c'e' o non e' eseguibile — manca il passo «copia»"; exit 2; }
# ⛔ E LA PAGINA DEVE STARE ACCANTO AL BINARIO, perche' e' li' che il prodotto la
#    cerca — ed e' quella che P5 deve misurare.
[ -f "$D/pagina.html" ] || { echo "NO  ⛔ $D/pagina.html non c'e': il server non servirebbe niente"; exit 2; }
echo "--  binario  : $(sha256sum "$D/remotix" | cut -c1-16)…  $(stat -c '%y' "$D/remotix")"
echo "--  pagina   : $D/pagina.html  ($(sha256sum "$D/pagina.html" | cut -c1-16)…, $(stat -c%s "$D/pagina.html") byte)"

# ⛔ E PRIMA DI CANCELLARE QUALCOSA, SI GUARDA SE E' DI QUALCUN ALTRO CHE VIVE.
#    Un `rm` sul socket e sul ban di un bersaglio acceso non da' nessun errore e
#    lo lascia senza il comando di sblocco di §4.4-bis, in silenzio.
if [ -f "$PIDF" ] && [ -d "/proc/$(cat "$PIDF" 2>/dev/null)" ]; then
	echo "NO  ⛔ «$PIDF» dice pid $(cat "$PIDF"), ed e' VIVO: un altro bersaglio"
	echo "    con questo stesso prefisso («$PREFISSO») e' gia' acceso.  Non gli"
	echo "    cancello ban e socket sotto i piedi.  ⇒ Spegnilo, o usa un PREFISSO"
	echo "    tuo:  PREFISSO=… PORTA=… bash $0 accendi"
	exit 2
fi
rm -f "$LOG" "$PIDF" "$SOCK" "$BAN" "$BAN.nuovo"
mkdir -p "$CERT"
# ⭐ Si accende DA DENTRO la sua cartella: il prodotto cerca `pagina.html`
#    accanto a se', e nessun `--pagina` gli dice dove guardare.
cd "$D" || exit 3
nohup ./remotix --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
      --certificati "$CERT" \
      --ban-file "$BAN" --comando-socket "$SOCK" --parlantina \
      > "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

g=0
while [ "$g" -lt 60 ]; do
	[ -d "/proc/$pid" ] || break
	[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")" -ge 2 ] && break
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	echo "NO  ⛔ il server e' morto subito.  Il registro dice:"
	sed 's/^/        /' "$LOG"
	exit 3
fi
righe=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
if [ "$righe" -lt 2 ]; then
	echo "NO  ⛔ il processo $pid e' vivo ma su :$PORTA ci sono $righe ascoltatori."
	echo "    §2.4 ne vuole DUE — UDP per RCP, TCP per la pagina — e P5 li usa"
	echo "    tutt'e due: senza il TCP la pagina non arriva al browser."
	sed 's/^/        /' "$LOG"
	exit 3
fi
# ⛔ E la pagina si CHIEDE, invece di dedurla dagli ascoltatori: un ascoltatore
#    aperto e una pagina servita sono due fatti diversi.
if grep -q "non apro pagina.html" "$LOG"; then
	echo "NO  ⛔ il server non ha trovato la sua pagina: si e' acceso dalla"
	echo "    cartella sbagliata, e P5 misurerebbe un 404 al posto del prodotto."
	exit 3
fi
echo "OK  acceso, pid $pid, $righe ascoltatori su :$PORTA dopo $((g/2)) s d'attesa"
echo "--  registro: $LOG · ban: $BAN · socket: $SOCK"
