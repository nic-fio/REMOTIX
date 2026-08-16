#!/bin/bash
#
# 03-b17-accendi.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore,
# e **DA ROOT**.  Accende il palco dello STEP 5 della fase 3: l'anello del
# ritardo.
#
#   sudo bash /media/REMOTIX/src/03-b17-accendi.sh stato
#   sudo bash /media/REMOTIX/src/03-b17-accendi.sh accendi
#   sudo bash /media/REMOTIX/src/03-b17-accendi.sh ponte-accendi
#   sudo bash /media/REMOTIX/src/03-b17-accendi.sh scena-costruisci   (⛔ DENTRO il contenitore)
#   sudo bash /media/REMOTIX/src/03-b17-accendi.sh scena-avvia [monitor]
#   sudo bash /media/REMOTIX/src/03-b17-accendi.sh scena-conta
#   sudo bash /media/REMOTIX/src/03-b17-accendi.sh scena-ferma
#   sudo bash /media/REMOTIX/src/03-b17-accendi.sh spegni | riaccendi | registro
#
# ===========================================================================
# ⛔ IL PERIMETRO, E PERCHE' E' TUTTO PROPRIO
#
# `FASI.md` §03-movimento: «ogni step ha porta, file di ban e socket propri».
#
#   7605   ⭐ la porta che il BROWSER apre — ed e' il PONTE, non il prodotto
#   7615      il prodotto vero, dietro il ponte, in ascolto su 0.0.0.0
#   7616      l'ancora dell'orologio — ⛔ NON passa dal ritardatore, ed e' il
#             motivo per cui P1 puo' salire di N invece che di N/2
#   albero    /media/REMOTIX/src/03-b17-src/src   — una COPIA, mai il prodotto
#   lavoro    /media/REMOTIX/tmp/03-b17           — ban, socket, certificati,
#                                                   registro, pid, rilievo
#
# ⛔ LE TRE PORTE CHE NON SI TOCCANO: **7448** (prodotto di casa), **7501**
#    (bersaglio di P5 della fase 1) e soprattutto **7561**, che e' quella che
#    l'utente apre.  ⇒ Si CONTANO prima e dopo.  ⚠ E se `ss` non c'e' si
#    dichiara «NON GUARDATE», che non e' «libere» (`LEZIONI.md` §1.9).
# ⚠ E la **7603** e' dello step 3, lasciata accesa apposta: si legge, non si
#   tocca.
#
# ⛔⭐ PERCHE' IL BROWSER APRE IL PONTE E NON IL PRODOTTO
#
#    Il controllo P1 di `STUDI.md` §web §6.3 chiede che «il server ritardi di N ms
#    noti e la mediana salga di esattamente N».  ⛔ Il prodotto **non sa
#    farlo**: `RCP.md` §7.5 prevede `BANCO_MARCA(ritardo_ms)`, ma
#    `src/rcp.c:53` ha `BANCO_ACCESO 0` e il ramo ACCETTATA
#    (`src/rcp.c:2498-2504`) e' uno stub che non aspetta e non dipinge.
#    ⇒ Il ritardo noto lo inietta il ponte, FUORI dal prodotto, e cosi' il
#    binario misurato e' **esattamente quello che si consegna**.
#
#    ⚠ E la pagina apre WebTransport verso `location.host`
#    (`src/pagina.html:2015`): se la pagina arrivasse dalla 7615, il video
#    andrebbe alla 7615 e il ritardatore non vedrebbe un byte — banco verde,
#    zero misurato.  ⇒ Il ponte fa TCP **e** UDP sulla stessa porta.
#
# ⛔ DA ROOT, e non e' una comodita': il palco appartiene all'UTENTE
#    (invariante I3).
set -uo pipefail

IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7605}          # quella che il browser apre — il PONTE
PORTA_DENTRO=${PORTA_DENTRO:-7615}
PORTA_ANCORA=${PORTA_ANCORA:-7616}
D=${D:-/media/REMOTIX/src/03-b17-src/src}
LAV=${LAV:-/media/REMOTIX/tmp/03-b17}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
RILIEVO=$LAV/rilievo
CERT=$LAV/certificati
BAN=$LAV/ban
SOCK=$LAV/comando.sock
LOG=$LAV/registro.log
PIDF=$LAV/pid
PONTE=${PONTE:-/media/REMOTIX/src/03-b17-ponte.py}
PONTE_PIDF=$LAV/ponte.pid
PONTE_LOG=$LAV/ponte.log
COMANDO=$LAV/comando
VERBALE_PONTE=$LAV/ponte.json
SCENA_LAV=${SCENA_LAV:-/media/REMOTIX/src/03-b17-scena}
SCENA_C=${SCENA_C:-/media/REMOTIX/src/03-scena.c}
SHM=${SHM:-remotix-03-b17}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

vicini()
{
	if ! command -v ss >/dev/null; then
		printf 'porte dei vicini: ⛔ NON GUARDATE (manca «ss») — e questo non e'"'"' «libere»'
		return
	fi
	printf 'porte dei vicini: '
	for p in 7448 7501 7561 7603; do
		n=$(ss -tuln 2>/dev/null | grep -c ":$p\b")
		printf '%s=%s ' "$p" "$n"
	done
}

impronta() { sha256sum "$1" 2>/dev/null | cut -c1-16; }

vivo() { [ -f "$1" ] && p=$(cat "$1" 2>/dev/null) && [ -n "$p" ] && [ -d "/proc/$p" ] && printf '%s' "$p"; }

case "${1:-accendi}" in
scena-costruisci)
	# ⛔ GIRA **DENTRO IL CONTENITORE**: sull'host `gcc` non c'e'.  ⚠ E la scena
	#    NON si riscrive: e' quella dello step 2, che ha gia' `--uscita <nome>`
	#    e la marca a 144 bit certificata (`CODER.md` §4.1 — si dipende).
	log "Costruisco la scena dello step 2 (il sorgente NON si tocca)"
	[ -f "$SCENA_C" ] || { ko "⛔ $SCENA_C non c'e'"; exit 2; }
	for c in gcc pkg-config wayland-scanner; do
		command -v "$c" >/dev/null || { ko "⛔ «$c» non c'e': questo ramo va girato DENTRO il contenitore"; exit 2; }
	done
	proto=/usr/share/wayland-protocols
	xdg=$proto/stable/xdg-shell/xdg-shell.xml
	pres=$proto/stable/presentation-time/presentation-time.xml
	for f in "$xdg" "$pres"; do [ -s "$f" ] || { ko "⛔ manca «$f»"; exit 2; }; done
	mkdir -p "$SCENA_LAV" || exit 2
	cd "$SCENA_LAV" || exit 2
	wayland-scanner client-header "$xdg"  xdg-shell-client-protocol.h || exit 3
	wayland-scanner private-code  "$xdg"  xdg-shell-protocol.c || exit 3
	wayland-scanner client-header "$pres" presentation-time-client-protocol.h || exit 3
	wayland-scanner private-code  "$pres" presentation-time-protocol.c || exit 3
	CF=$(pkg-config --cflags wayland-client) || exit 3
	LB=$(pkg-config --libs wayland-client) || exit 3
	[ -n "$LB" ] || { ko "⛔ pkg-config non ha dato nessuna libreria: NON compilo a meta'"; exit 3; }
	# shellcheck disable=SC2086
	gcc -O2 -Wall -Wextra -o 03-scena "$SCENA_C" \
	    xdg-shell-protocol.c presentation-time-protocol.c -I. $CF $LB -lrt \
		|| { ko "⛔ la scena non si e' compilata"; exit 3; }
	chmod 755 "$SCENA_LAV" 03-scena
	ok "⭐ scena costruita: $SCENA_LAV/03-scena"
	exit 0 ;;

scena-uscite)
	[ -x "$SCENA_LAV/03-scena" ] || { ko "⛔ la scena non e' costruita"; exit 2; }
	setpriv --reuid=1000 --regid=1000 --init-groups \
		env XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 \
		    HOME=/home/nicfio USER=nicfio "$SCENA_LAV/03-scena" --uscite
	exit $? ;;

scena-avvia)
	# ⛔⭐ LA SCENA DEVE STARE SUL MONITOR CHE SI STA CATTURANDO, e il nome NON
	#     si scrive a mano.
	#
	#     ⚠ Il mandato di questo step diceva «si accende con
	#       `03-scena --uscita Meta-3`».  ⛔ **«Meta-3» e' un nome che non
	#       appartiene a noi**: e' quello che Mutter assegna al monitor
	#       virtuale, e su questa macchina i monitor virtuali sono PIU' D'UNO —
	#       quello del prodotto dell'utente sulla 7561, quello dello step 3
	#       sulla 7603, e il nostro.  Scriverlo a mano vuol dire, un giorno su
	#       tre, mettere la scena sul palco di un altro banco: `[M]` 13 agosto
	#       2026, una scena finita sul monitor sbagliato ha prodotto **zero
	#       fotogrammi per dieci secondi con la catena perfettamente
	#       funzionante**.
	#
	#     ⇒ Il nome lo dice il REGISTRO DEL NOSTRO SERVER, che l'ha chiesto a
	#       Mutter.  Se il registro non lo nomina, NON si accende niente: uno
	#       zero raccolto su un palco indovinato accuserebbe il prodotto invece
	#       della scena.
	USCITA=${2:-}
	[ -S /run/user/1000/wayland-0 ] || { ko "⛔ /run/user/1000/wayland-0 non c'e'"; exit 2; }
	[ -x "$SCENA_LAV/03-scena" ] || { ko "⛔ la scena non e' costruita: «scena-costruisci»"; exit 2; }
	if [ -z "$USCITA" ]; then
		USCITA=$(grep -ao 'monitor «[^»]*»' "$LOG" 2>/dev/null | tail -1 | sed 's/monitor «//; s/»//')
	fi
	if [ -z "$USCITA" ] || [ "$USCITA" = "(non l'ho saputo dire)" ]; then
		ko "⛔ non so su quale monitor sta il palco del MIO prodotto: il mio"
		ko "   registro ($LOG) non lo nomina.  ⚠ Non accendo la scena «da"
		ko "   qualche parte»: sarebbe uno zero puntato sull'imputato sbagliato."
		inf "   ⇒ Serve che qualcuno sia ENTRATO nella sessione: il monitor"
		inf "     virtuale nasce col figlio, non con il server."
		exit 2
	fi
	inf "il palco del MIO prodotto e' il monitor «$USCITA» (letto dal registro, non dedotto)"
	if p=$(vivo "$LAV/scena.pid"); then ok "la scena e' gia' viva (pid $p)"; exit 0; fi
	mkdir -p "$LAV"; : >> "$LAV/scena.log"; chmod 666 "$LAV/scena.log"
	# ⛔ `stdbuf -oL`: senza, il conteggio che la scena stampa da se' resta nel
	#    buffer e «viva ma non disegna» diventa indistinguibile da «disegna a
	#    60 al secondo».
	setpriv --reuid=1000 --regid=1000 --init-groups \
		env XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 \
		    HOME=/home/nicfio USER=nicfio \
		    DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
		nohup stdbuf -oL -eL "$SCENA_LAV/03-scena" --uscita "$USCITA" \
		    --movimento barra --danno preciso --shm "$SHM" \
		    --giro "b17-$(date +%H%M%S)" --loquace \
		    >> "$LAV/scena.log" 2>&1 &
	pid=$!
	echo "$pid" > "$LAV/scena.pid"
	g=0
	while [ "$g" -lt 60 ]; do
		[ -d "/proc/$pid" ] || break
		grep -qE 'disegn|frame|uscita' "$LAV/scena.log" 2>/dev/null && break
		sleep 0.25; g=$((g+1))
	done
	if [ ! -d "/proc/$pid" ]; then
		ko "⛔ la scena e' morta subito:"; tail -20 "$LAV/scena.log" | sed 's/^/        /'; exit 3
	fi
	if grep -qE 'disegn|frame|uscita' "$LAV/scena.log" 2>/dev/null; then
		ok "⭐ scena viva sul monitor «$USCITA» (pid $pid)"
		tail -6 "$LAV/scena.log" | sed 's/^/        /'
	else
		ko "⛔ la scena e' viva ma non ha stampato un conteggio: NON dico che"
		ko "   sta disegnando («vivo» non e' «disegna», LEZIONI.md §1.9)"
		exit 3
	fi
	exit 0 ;;

scena-conta)
	# ⛔ Quanto disegna il CLIENT: e' il controllo che dice se il tetto e' del
	#    compositore o della scena (`LEZIONI.md` §1.1, seconda meta').
	[ -f "$LAV/scena.log" ] || { ko "⛔ nessun registro della scena: non ho guardato"; exit 2; }
	if p=$(vivo "$LAV/scena.pid"); then ok "scena viva, pid $p"; else ko "⛔ la scena NON e' viva"; fi
	tail -8 "$LAV/scena.log"
	exit 0 ;;

scena-ferma)
	if p=$(vivo "$LAV/scena.pid"); then
		kill "$p" 2>/dev/null
		g=0; while [ -d "/proc/$p" ] && [ "$g" -lt 20 ]; do sleep 0.25; g=$((g+1)); done
		[ -d "/proc/$p" ] && ko "⛔ la scena (pid $p) non e' morta" || ok "scena ferma (pid $p)"
		rm -f "$LAV/scena.pid"
	else
		inf "nessuna scena mia accesa"
	fi
	exit 0 ;;

ponte-accendi)
	log "Il PONTE: $PORTA (tcp+udp) -> $PORTA_DENTRO, ancora su $PORTA_ANCORA"
	[ -f "$PONTE" ] || { ko "⛔ $PONTE non c'e'"; exit 2; }
	if p=$(vivo "$PONTE_PIDF"); then ok "il ponte e' gia' vivo (pid $p)"; exit 0; fi
	command -v ss >/dev/null || { ko "⛔ «ss» non c'e': non chiamo libera una porta che non ho guardato"; exit 2; }
	for p in "$PORTA" "$PORTA_ANCORA"; do
		n=$(ss -tuln 2>/dev/null | grep -c ":$p\b")
		[ "$n" -eq 0 ] || { ko "⛔ la porta $p e' gia' occupata ($n righe): non e' mia, non la tocco"; ss -tuln | grep ":$p\b"; exit 2; }
	done
	mkdir -p "$LAV"
	[ -f "$COMANDO" ] || printf 'ritardo_ms=0\nfuori_ordine=0\ngiro=-\n' > "$COMANDO"
	chmod 666 "$COMANDO"
	nohup python3 "$PONTE" --fuori "$PORTA" --dentro "$PORTA_DENTRO" \
	      --orologio "$PORTA_ANCORA" --comando "$COMANDO" \
	      --verbale "$VERBALE_PONTE" >> "$PONTE_LOG" 2>&1 &
	echo $! > "$PONTE_PIDF"
	g=0
	while [ "$g" -lt 40 ]; do
		[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")" -ge 2 ] && break
		sleep 0.25; g=$((g+1))
	done
	righe=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
	[ "$righe" -ge 2 ] || { ko "⛔ il ponte non ascolta in due (tcp+udp): $righe righe"
		tail -10 "$PONTE_LOG" | sed 's/^/        /'; exit 3; }
	ok "ponte acceso (pid $(cat "$PONTE_PIDF")), $righe ascoltatori su :$PORTA"
	ok "ancora su :$PORTA_ANCORA — ⛔ e NON passa dal ritardatore"
	exit 0 ;;

ponte-ferma)
	if p=$(vivo "$PONTE_PIDF"); then
		kill "$p" 2>/dev/null; sleep 0.5
		[ -d "/proc/$p" ] && kill -9 "$p" 2>/dev/null
		ok "ponte fermo (pid $p)"; rm -f "$PONTE_PIDF"
	else inf "nessun ponte mio acceso"; fi
	exit 0 ;;

stato)
	log "Lo stato dello step 5"
	inf "$(vicini)"
	if p=$(vivo "$PIDF"); then ok "prodotto acceso: pid $p, porta $PORTA_DENTRO"
	else ko "il prodotto NON e' acceso"; fi
	if p=$(vivo "$PONTE_PIDF"); then ok "ponte acceso: pid $p, porta $PORTA"
	else ko "il ponte NON e' acceso"; fi
	if p=$(vivo "$LAV/scena.pid"); then ok "scena viva: pid $p"
	else inf "scena: non accesa (⚠ e senza scena questo banco non misura niente)"; fi
	[ -f "$VERBALE_PONTE" ] && { inf "ponte: $(cat "$VERBALE_PONTE")"; }
	[ -f "$COMANDO" ] && { inf "comando: $(tr '\n' ' ' < "$COMANDO")"; }
	inf "riga del pts: $(grep -ao 'MISURATO: il .pts. di Mutter[^\"]*' "$LOG" 2>/dev/null | tail -1 | cut -c1-160)"
	exit 0 ;;

registro)
	tail -"${2:-60}" "$LOG"; exit 0 ;;

palco)
	# ⛔⛔ IL PALCO DEL SERVER, MISURATO — e gira QUI perche' DEVE girare da
	#     ROOT.  Il prodotto e' di root: `ls /proc/<pid>/fd` da utente normale
	#     risponde «Permission denied», e un lettore ingenuo leggerebbe zero
	#     nodi DRM e concluderebbe «codifica in SOFTWARE» — cioe' esattamente
	#     il numero che la corsia E deve misurare, sbagliato al contrario.
	#     ⇒ `LEZIONI.md` §2.0: «non c'e'» e «non ho potuto guardare».
	#
	# ⭐ E la stampa e' JSON su UNA riga, con dentro anche i DENOMINATORI:
	#    quanti processi ho trovato e se li ho potuti guardare.  Zero nodi con
	#    zero processi non e' «software»: e' «non c'era niente da guardare».
	pids=$(pgrep -x remotix 2>/dev/null | tr '\n' ' ')
	n=0; letti=0; negati=0; nodi=""
	for p in $pids; do
		n=$((n+1))
		if elenco=$(ls -l "/proc/$p/fd" 2>/dev/null); then
			letti=$((letti+1))
			trovati=$(printf '%s\n' "$elenco" | grep -o 'renderD[0-9]*' | sort -u | tr '\n' ' ')
			nodi="$nodi $trovati"
		else
			negati=$((negati+1))
		fi
	done
	nodi=$(printf '%s' "$nodi" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ',' | sed 's/,$//')
	# ⚠ E si dice anche CHI SIAMO: un `palco` girato senza sudo e' leggibile
	#   dal verbale invece che indovinabile.
	printf '{"utente":"%s","processi_remotix":%d,"letti":%d,"negati":%d,' \
	       "$(id -un)" "$n" "$letti" "$negati"
	printf '"nodi_di_rendering":['
	primo=1
	IFS=,
	for x in $nodi; do
		[ -z "$x" ] && continue
		[ "$primo" -eq 1 ] || printf ','
		printf '"%s"' "$x"; primo=0
	done
	unset IFS
	printf ']}\n'
	exit 0 ;;

spegni)
	bash "$0" scena-ferma
	bash "$0" ponte-ferma
	if p=$(vivo "$PIDF"); then
		figli=$(pgrep -P "$p" 2>/dev/null | tr '\n' ' ')
		kill "$p" 2>/dev/null
		g=0; while [ -d "/proc/$p" ] && [ "$g" -lt 40 ]; do sleep 0.25; g=$((g+1)); done
		[ -d "/proc/$p" ] && kill -9 "$p" 2>/dev/null
		restano=0
		for f in $figli; do [ -d "/proc/$f" ] && restano=$((restano+1)); done
		ok "prodotto spento (pid $p)"
		[ "$restano" -eq 0 ] && ok "⭐ nessun figlio MIO orfano" \
			|| ko "⛔ $restano figli MIEI ancora vivi"
		rm -f "$PIDF"
	else inf "nessun prodotto mio acceso"; fi
	inf "$(vicini)"
	exit 0 ;;

accendi) ;;
riaccendi) bash "$0" spegni ;;
*) echo "uso: $0 [stato|accendi|spegni|riaccendi|registro|ponte-accendi|ponte-ferma|scena-costruisci|scena-uscite|scena-avvia|scena-conta|scena-ferma]"; exit 2 ;;
esac

# --- accendi ---------------------------------------------------------------
log "0. Il terreno, dichiarato prima di toccarlo"
inf "$(vicini)"
[ "$(id -u)" -eq 0 ] || { ko "⛔ questo va lanciato DA ROOT: il palco e' dell'UTENTE"; exit 2; }
[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html non c'e'"; exit 2; }
inf "binario: $D/remotix ($(impronta "$D/remotix")…, $(stat -c '%y' "$D/remotix"))"
inf "pagina:  $D/pagina.html ($(impronta "$D/pagina.html")…)"

command -v ss >/dev/null || { ko "⛔ «ss» non c'e': non ho guardato la porta, e non la chiamo libera"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA_DENTRO\b")
[ "$n" -eq 0 ] || { ko "⛔ la porta $PORTA_DENTRO e' gia' occupata ($n righe)"; ss -tuln | grep ":$PORTA_DENTRO\b"; exit 2; }
ok "porta $PORTA_DENTRO libera (ss ha guardato e ha stampato $n righe)"

mkdir -p "$CERT" "$RILIEVO" || exit 2
chmod 1777 "$RILIEVO"

log "1. Le librerie: quelle costruite, non quelle dei pacchetti"
export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
ldd "$D/remotix" > "$LAV/ldd.txt" 2>&1 || { ko "⛔ ldd non ha finito"; exit 2; }
grep -q 'not found' "$LAV/ldd.txt" && { ko "⛔ manca una libreria:"; grep 'not found' "$LAV/ldd.txt" | sed 's/^/        /'; exit 2; }
for l in libngtcp2 libnghttp3; do
	riga=$(grep -m1 "$l" "$LAV/ldd.txt")
	case "$riga" in
	*/media/REMOTIX/src/b2/*) ok "$l ← $(printf '%s' "$riga" | sed 's/^[[:space:]]*//')" ;;
	*) ko "⛔ $l NON viene dall'albero costruito: stesso soname, altra libreria"; exit 2 ;;
	esac
done

log "2. Il servizio PAM sull'host"
[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix NON C'E': PAM ripiega su «other» = pam_deny"; exit 2; }
ok "/etc/pam.d/remotix c'e'"

log "3. Accendo il PRODOTTO — DA ROOT, sulla $PORTA_DENTRO (dietro il ponte)"
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA_DENTRO" \
      --certificati "$CERT" --pagina "$D/pagina.html" \
      --ban-file "$BAN" --comando-socket "$SOCK" \
      --rilievo "$RILIEVO" --parlantina \
      >> "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"
g=0
while [ "$g" -lt 60 ]; do
	[ -d "/proc/$pid" ] || break
	[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA_DENTRO\b")" -ge 2 ] && break
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	ko "⛔ il server e' morto subito.  Le ultime righe:"; tail -20 "$LOG" | sed 's/^/        /'; exit 3
fi
righe=$(ss -tuln 2>/dev/null | grep -c ":$PORTA_DENTRO\b")
[ "$righe" -ge 2 ] || { ko "⛔ pid $pid vivo ma $righe ascoltatori: §2.4 ne vuole DUE"; tail -20 "$LOG" | sed 's/^/        /'; exit 3; }
ok "prodotto acceso, pid $pid, $righe ascoltatori su :$PORTA_DENTRO"

log "4. Accendo il PONTE"
bash "$0" ponte-accendi || exit 3

log "5. Che cosa ha detto all'avvio"
tail -12 "$LOG" | sed 's/^/        /'
inf "$(vicini)"
exit 0
