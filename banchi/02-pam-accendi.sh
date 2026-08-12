#!/bin/bash
#
# 02-pam-accendi.sh — ⛔ GIRA DENTRO IL CONTENITORE.  Accende IL BERSAGLIO DI
# QUESTO BANCO: una copia del prodotto sulla porta 7531, con ban, socket,
# certificati, registro e file del pid tutti suoi.
#
#   bash /srv/src/02-pam-accendi.sh copia     rifa' la copia e la ricostruisce
#   bash /srv/src/02-pam-accendi.sh accendi
#   bash /srv/src/02-pam-accendi.sh spegni
#   bash /srv/src/02-pam-accendi.sh registro  stampa il registro del bersaglio
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' UN BERSAGLIO MIO E NON QUELLO DI CASA
#
# Su NIC-OS, il 12 agosto 2026, girano gia': la **7448** (il prodotto di casa),
# la **7501** e la **7522** (i bersagli di P5, di un altro giro).  ⛔ Sono
# accesi apposta e non si toccano.  ⚠ E la regola «un banco in parallelo ha
# porta, ban-file e socket PROPRI» non e' zelo: il conto dei tentativi di
# §4.4-bis e' **per indirizzo**, e tutti i banchi di questa macchina partono
# dallo stesso indirizzo — chi si divide un ban-file con un altro giro mette
# fuori per dodici ore anche lui.
#
# ⭐ Il perimetro sta in UNA variabile (`PREFISSO`), come in `01-p5-accendi.sh`:
#    cosi' non se ne puo' dimenticare un pezzo.  E' la cura nata il 12 agosto
#    2026 quando ban, socket, registro, certificato e **file del pid** erano
#    scritti in chiaro, e un secondo bersaglio avrebbe cancellato quelli del
#    primo — compreso il `.pid`, cioe' `spegni` avrebbe ammazzato il processo
#    sbagliato.
#
# ---------------------------------------------------------------------------
# ⛔ IL GUASTO SI INNESTA NELLA COPIA, MAI NEL PRODOTTO DI CASA
#
# La certificazione di questo banco vuole il giro `sano -> guasto -> risanato`,
# e il guasto e' **la cura tolta**: il gancio asincrono non collegato, cioe'
# esattamente lo stato del server prima del 12 agosto 2026.  ⛔ Innestarlo nel
# prodotto di `/srv/src/remotix` lo metterebbe sotto i piedi di chiunque altro
# lo stia usando.
#
# ⛔ B0.7: MARCATORI, NON `sleep`.  «Il processo e' vivo» e «la porta risponde»
#    sono due fatti diversi, e alla misura serve il secondo.
set -uo pipefail

SORG=${SORG:-/srv/src/02-pam-src}
D=${D:-/srv/src/02-pam-bersaglio}
GEMELLO=${GEMELLO:-/srv/src/rcp}
TMP=/srv/src/tmp
PORTA=${PORTA:-7531}
IND=${IND:-192.168.0.2}
PREFISSO=${PREFISSO:-pam2-7531}

CERT=$TMP/$PREFISSO-cert
BAN=$TMP/$PREFISSO-ban
SOCK=$TMP/$PREFISSO.sock
LOG=$TMP/$PREFISSO.log
PIDF=$TMP/$PREFISSO.pid

mkdir -p "$TMP"

case "${1:-accendi}" in
spegni)
	if [ -f "$PIDF" ]; then
		pid=$(cat "$PIDF")
		# ⛔ Per PID e solo il proprio: `pkill -f remotix` porterebbe via la
		#    7448, la 7501 e la 7522, che sono di altri.
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
registro)
	[ -f "$LOG" ] || { echo "NO  ⛔ $LOG non c'e'"; exit 2; }
	cat "$LOG"
	exit 0 ;;
ammazza-aiutante)
	# ⛔⭐ STA IN UN FILE, E NON DENTRO TRE LIVELLI DI VIRGOLETTE — 12 agosto
	#     2026, e la lezione era gia' scritta in `01-p5-accendi.sh`: «un file
	#     non ha livelli di virgolette».  ⚠ Scritto dentro `ssh → enter.sh →
	#     bash -c`, questo pezzo e' morto su un `$(...)`  — e il guaio non e'
	#     stato l'errore: e' stato che il caso «l'aiutante e' morto» e' girato
	#     lo stesso, su un aiutante VIVO, e ha dato un rosso a un server sano.
	#
	# ⛔ E il pid si legge dal registro DI QUESTO bersaglio: un `pgrep` su
	#    «remotix» troverebbe anche la 7448, la 7501 e la 7522, che sono di
	#    altri.  ⚠ «l'ho ammazzato» e «ne ho ammazzato uno» sono due fatti
	#    diversi.
	[ -f "$LOG" ] || { echo "NO  ⛔ $LOG non c'e': non ho ammazzato niente"; exit 2; }
	p=$(sed -n 's/.*aiutante di PAM acceso: pid \([0-9]*\).*/\1/p' "$LOG" | tail -1)
	if [ -z "$p" ]; then
		echo "NO  ⛔ nessun pid dell'aiutante nel registro: non e' «e' morto»,"
		echo "    e' «non e' mai nato», e sono due cose diverse."
		exit 2
	fi
	# ⛔⭐ «VIVO» E «ZOMBIE» NON SONO LA STESSA COSA, E IN /proc SI ASSOMIGLIANO
	#     — 12 agosto 2026, e questo controllo ha gia' dato un NO sbagliato.
	#
	# `[ -d /proc/$p ]` risponde «si'» anche a un processo gia' morto che il
	# padre non ha ancora raccolto.  ⛔ Il banco ha detto «l'aiutante e' ancora
	# vivo dopo SIGKILL» mentre era morto da un secondo, e la diagnosi puntava
	# sul prodotto.  ⭐ Lo stato vero sta nel terzo campo di /proc/<pid>/stat:
	# `Z` e' uno zombie, cioe' morto.
	vivo() # $1 = pid.  0 = vivo davvero, 1 = morto (assente o zombie)
	{
		[ -r "/proc/$1/stat" ] || return 1
		s=$(awk '{print $3}' "/proc/$1/stat" 2>/dev/null)
		[ "$s" = Z ] && return 1
		return 0
	}
	if ! vivo "$p"; then
		echo "NO  ⛔ il pid $p non e' vivo GIA' ADESSO: il caso che segue"
		echo "    misurerebbe una scena che non ho preparato io."
		exit 2
	fi
	kill -9 "$p"
	sleep 1
	if vivo "$p"; then
		echo "NO  ⛔ il pid $p e' ancora VIVO dopo SIGKILL (stato $(awk '{print $3}' "/proc/$p/stat"))"
		exit 3
	fi
	echo "OK  aiutante $p ammazzato con SIGKILL: non ha potuto scrivere niente,"
	echo "    e nessun gestore ha potuto rispondere al posto suo"
	exit 0 ;;
copia)
	[ -d "$SORG" ] || { echo "NO  ⛔ $SORG non c'e'"; exit 2; }
	# ⛔ La copia si rifa' da zero: una copia vecchia risponde «esisto» come
	#    una di adesso (LEZIONI.md §1.9 punto 8).
	rm -rf "$D"
	mkdir -p "$(dirname "$D")"
	cp -a "$SORG" "$D"
	rm -f "$D"/*.o "$D/remotix"
	printf -- '--  copia: %s → %s\n' "$SORG" "$D"
	GEMELLO="$GEMELLO" bash "$D/costruisci.sh" || exit 3
	exit 0 ;;
guasto)
	# ⛔⭐ IL GUASTO E' LA CURA TOLTA, E NON UN DIFETTO INVENTATO — 12 agosto
	#     2026.  E' la forma migliore che un guasto da innesto possa avere: lo
	#     stato del server PRIMA di §1.10, cioe' un difetto che e' davvero
	#     esistito e che e' davvero stato misurato (`[M]` B8, 11 agosto:
	#     1,0-2,2 s per tentativo).
	#
	# ⛔ Che cosa dimostra: che `02-pam-fermo.py` **sa vedere** il blocco.  Un
	#    banco che restasse verde con questo guasto dentro non proverebbe che
	#    la cura funziona — proverebbe che il righello e' cieco, e ogni verde
	#    successivo sarebbe la peggiore delle prove (`CODER.md` §4.6).
	#
	# ⚠ Si innesta nella COPIA (`$D`), mai nel prodotto di `/srv/src/remotix`,
	#   che e' di chiunque altro lo stia usando.
	[ -f "$D/webtransport.c" ] || { echo "NO  ⛔ $D/webtransport.c non c'e'"; exit 2; }
	python3 - "$D/webtransport.c" <<'FINE'
import sys
p = sys.argv[1]
t = open(p).read()
appiglio = "\tif (w->aiuto)\n\t\tg.chiedi_verifica = gancio_chiedi;\n"
if t.count(appiglio) != 1:
    print("NO  \u26d4 l'appiglio non e' unico (%d volte): non innesto niente"
          % t.count(appiglio))
    sys.exit(2)
guasto = ("\t/* REMOTIX 02-PAM GUASTO \u2014 il gancio asincrono NON collegato,\n"
          "\t * cioe' il server com'era prima di DECISIONI.md \u00a71.10.  rcp.c\n"
          "\t * ripieghera' sulla verifica SINCRONA e il filo si fermera'.\n"
          "\t * Se 02-pam-fermo.py resta verde con questo dentro, e' cieco. */\n")
open(p, "w").write(t.replace(appiglio, guasto, 1))
print("OK  guasto innestato: il gancio asincrono non e' piu' collegato")
FINE
	[ $? -eq 0 ] || exit 3
	GEMELLO="$GEMELLO" bash "$D/costruisci.sh" >/dev/null 2>&1 \
		|| { echo "NO  ⛔ la ricostruzione col guasto e' fallita"; exit 3; }
	# ⛔ E si CONTROLLA che il guasto sia nel binario, non solo nel sorgente:
	#    «l'ho scritto» e «e' dentro quel che gira» sono due fatti diversi, ed
	#    e' il difetto con cui B11 ha acceso il server sano credendolo guasto.
	if grep -a -F -q "REMOTIX 02-PAM GUASTO" "$D/webtransport.c" \
	   && ! grep -a -F -q "g.chiedi_verifica = gancio_chiedi" "$D/webtransport.c"; then
		echo "OK  ⛔ ricostruito CON il guasto: $(sha256sum "$D/remotix" | cut -c1-16)…"
	else
		echo "NO  ⛔ il guasto non e' dove doveva essere"
		exit 3
	fi
	exit 0 ;;
accendi) TIENI_BAN=0 ;;
riaccendi)
	# ⛔⭐ E QUESTO PASSO ESISTE PER UN ROSSO CHE IL BANCO SI ERA DATO DA SE'
	#     — 12 agosto 2026, e il primo imputato era il banco (`REVIEWER.md` §1).
	#
	# `accendi` cancella il file dei ban, ed e' giusto: un giro deve partire da
	# uno stato NOTO, e un ban ereditato dal giro prima farebbe misurare
	# `TROPPI_TENTATIVI` dove si voleva misurare PAM.  ⛔ Ma il caso
	# «il ban sopravvive al riavvio» (invariante **I7**) si prova SPEGNENDO E
	# RIACCENDENDO, e con quel `rm` diceva sempre di no — **rosso pieno su un
	# prodotto che il ban lo conserva**.
	#
	# ⚠ E' la forma di `LEZIONI.md` §1.9: il banco misurava la propria gamba e
	#   la diagnosi puntava sul server.  ⭐ Adesso i due passi sono due, e il
	#   nome dice quale stato si sta chiedendo.
	TIENI_BAN=1 ;;
*) echo "uso: $0 [copia|guasto|accendi|riaccendi|spegni|registro|ammazza-aiutante]"; exit 2 ;;
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
[ -f "$D/pagina.html" ] || { echo "NO  ⛔ $D/pagina.html non c'e': il server non servirebbe niente"; exit 2; }
echo "--  binario  : $(sha256sum "$D/remotix" | cut -c1-16)…  $(stat -c '%y' "$D/remotix")"

# ⛔ E PRIMA DI CANCELLARE QUALCOSA, SI GUARDA SE E' DI QUALCUN ALTRO CHE VIVE.
if [ -f "$PIDF" ] && [ -d "/proc/$(cat "$PIDF" 2>/dev/null)" ]; then
	echo "NO  ⛔ «$PIDF» dice pid $(cat "$PIDF"), ed e' VIVO: un altro bersaglio"
	echo "    con questo stesso prefisso («$PREFISSO») e' gia' acceso."
	exit 2
fi
if [ "${TIENI_BAN:-0}" = 1 ]; then
	rm -f "$LOG" "$PIDF" "$SOCK"
	echo "--  ⚠ il file dei ban NON si cancella: e' il passo «riaccendi», e"
	echo "    quel file E' la cosa da provare (I7, §4.4-bis)"
	[ -f "$BAN" ] && echo "--  ban prima del riavvio: $(wc -l < "$BAN") righe in $BAN" \
	              || echo "--  ⛔ $BAN NON C'E': non e' «zero ban», e' «non c'era niente da conservare»"
else
	rm -f "$LOG" "$PIDF" "$SOCK" "$BAN" "$BAN.nuovo"
fi
mkdir -p "$CERT"
# ⭐ Si accende DA DENTRO la sua cartella: il prodotto cerca `pagina.html`
#    accanto a se'.
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
	echo "    §2.4 ne vuole DUE — UDP per RCP, TCP per la pagina."
	sed 's/^/        /' "$LOG"
	exit 3
fi
# ⛔ E il servizio PAM si guarda nel REGISTRO del server, non a memoria: senza
#    /etc/pam.d/remotix ogni parola giusta viene rifiutata, e questo banco
#    misurerebbe una scena in cui NESSUNO entra — cioe' un numero verde perche'
#    non c'era niente da bloccare.
if grep -q "NON C'E'" "$LOG"; then
	echo "NO  ⛔ il server dice che /etc/pam.d/remotix non c'e': ogni parola"
	echo "    giusta verrebbe rifiutata, e la scena di questo banco non esiste."
	exit 3
fi
echo "OK  acceso, pid $pid, $righe ascoltatori su :$PORTA dopo $((g/2)) s d'attesa"
echo "--  registro: $LOG · ban: $BAN · socket: $SOCK"
