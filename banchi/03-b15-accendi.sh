#!/bin/bash
#
# 03-b15-accendi.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore,
# e **DA ROOT**.  Accende il prodotto dello STEP 3 della fase 3 sulla **7603**.
#
#   sudo bash /media/REMOTIX/src/03-b15-accendi.sh stato
#   sudo bash /media/REMOTIX/src/03-b15-accendi.sh accendi
#   sudo bash /media/REMOTIX/src/03-b15-accendi.sh spegni
#   sudo bash /media/REMOTIX/src/03-b15-accendi.sh riaccendi
#   sudo bash /media/REMOTIX/src/03-b15-accendi.sh registro [quante]
#
# ===========================================================================
# ⛔ IL PERIMETRO, E PERCHE' E' TUTTO PROPRIO
#
# `FASI.md` §03-movimento: «ogni step ha porta, file di ban e socket propri: in
# fase 3 i banchi girano in parallelo per davvero, e due banchi che condividono
# un ban-file si fermano a vicenda».
#
#   porta      7603      (step 3 · gli altri step hanno 7601, 7602, 7604, 7605)
#   albero     /media/REMOTIX/src/03-b15-src/src      — una COPIA, mai il
#                                                       prodotto di casa
#   lavoro     /media/REMOTIX/tmp/03-b15             — ban, socket, certificati,
#                                                      registro, pid, rilievo
#
# ⛔ LE TRE PORTE CHE NON SI TOCCANO: **7448** (prodotto di casa), **7501**
#    (bersaglio di P5) e soprattutto **7561**, che e' quella che l'utente apre
#    ed e' il bersaglio del metro.  ⇒ Si CONTANO prima e dopo, e se una cambia
#    lo si dice.  ⚠ E se `ss` non c'e', si dichiara «NON GUARDATE»: che non e'
#    «libere» (`LEZIONI.md` §1.9).
#
# ⛔ DA ROOT, e non e' una comodita': il palco appartiene all'UTENTE.  Root
#    verifica con PAM la parola di chiunque e per ogni utente ammesso genera un
#    figlio che gira come lui e che il bus di sessione ce l'ha.  Un server
#    acceso come `nicfio` mostrerebbe il desktop di `nicfio` a chiunque entri —
#    e' il difetto misurato il 12 agosto 2026 (invariante I3).
set -uo pipefail

IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7603}
D=${D:-/media/REMOTIX/src/03-b15-src/src}
LAV=${LAV:-/media/REMOTIX/tmp/03-b15}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
RILIEVO=$LAV/rilievo
CERT=$LAV/certificati
BAN=$LAV/ban
SOCK=$LAV/comando.sock
LOG=$LAV/registro.log
PIDF=$LAV/pid

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ⛔ Le porte dei vicini si CONTANO, e «non guardate» non e' «libere».
vicini()
{
	if ! command -v ss >/dev/null; then
		printf 'porte dei vicini: ⛔ NON GUARDATE (manca «ss») — e questo non e'"'"' «libere»'
		return
	fi
	printf 'porte dei vicini: '
	for p in 7448 7501 7561; do
		n=$(ss -tuln 2>/dev/null | grep -c ":$p\b")
		printf '%s=%s ' "$p" "$n"
	done
}

impronta() { sha256sum "$1" 2>/dev/null | cut -c1-16; }

mio_pid()
{
	[ -f "$PIDF" ] || return 1
	p=$(cat "$PIDF" 2>/dev/null)
	[ -n "$p" ] && [ -d "/proc/$p" ] || return 1
	printf '%s' "$p"
}

# ⛔⭐ LA SCENA E' QUELLA DELLO STEP 2, E NON SE NE SCRIVE UN'ALTRA.
#
#     `03-scena.c` esiste gia', e ⭐ **ha esattamente la cosa che a questo step
#     serve**: `--uscita <nome>`, cioe' «chiedi il monitor per nome invece di
#     lasciarlo scegliere al compositore».  Il suo commento dice perche': *«sul
#     palco della fase 3 ce ne sono due (quello del prodotto e quello del
#     banco), e una scena finita sul monitor sbagliato e' un rosso puntato
#     sull'imputato sbagliato»*.  Si dipende, non si riscrive (`CODER.md` §4.1).
#
# ⛔ E SI COSTRUISCE DENTRO IL CONTENITORE, dove stanno `gcc`, `pkg-config` e
#    `wayland-scanner`; QUI, sull'host, si ESEGUE soltanto — perche' il socket
#    `wayland-0` sta sull'host e dentro il contenitore non e' montato.  `[M]` 13
#    agosto 2026: sull'host `gcc` non c'e' affatto.  E' lo stesso taglio del
#    prodotto: si costruisce di la', si accende di qua.
SCENA_LAV=${SCENA_LAV:-/media/REMOTIX/src/03-b15-scena}
# ⚠ Il sorgente ha DUE nomi, come tutto il resto: `/media/REMOTIX/src` sull'host
#   e `/srv/src` dentro il contenitore.  Si dichiarano tutt'e due invece di
#   ricavare l'uno dall'altro con una sostituzione — un percorso indovinato un
#   giorno cambia.
SCENA_C=${SCENA_C:-/media/REMOTIX/src/03-scena.c}
# ⛔ Il nome della memoria condivisa della scena e' PROPRIO, come la porta e il
#    ban-file.  ⚠ In fase 3 i banchi girano in parallelo per davvero: due scene
#    che aprissero lo stesso `/dev/shm/<nome>` si pesterebbero i buffer a
#    vicenda, e il sintomo sarebbe «i fotogrammi di un altro banco» — cioe' una
#    misura attribuita all'imputato sbagliato, che e' il difetto piu' caro di
#    questa fase.  ⇒ Chi riusa questo file dichiara il suo.
SCENA_SHM=${SCENA_SHM:-remotix-03-b15}

case "${1:-accendi}" in
scena-costruisci)
	# ⛔⭐ QUESTO RAMO GIRA **DENTRO IL CONTENITORE**, e ci arriva perche' e' un
	#     FILE: `ssh → enter.sh → bash -c` sono tre livelli di virgolette, e la
	#     prima stesura ci ha infilato dentro un `$(pkg-config …)` che non e'
	#     arrivato — `[M]` 13 agosto 2026, e il sintomo era «undefined reference
	#     to wl_output_interface», cioe' una riga di link a cui mancavano le
	#     librerie senza che niente lo dicesse.  ⭐ Un file non ha livelli di
	#     virgolette (`FASI.md` §00-ambiente B3.3).
	log "Costruisco la scena dello step 2 (il sorgente NON si tocca)"
	[ -f "$SCENA_C" ] || { ko "⛔ $SCENA_C non c'e': va portato con «porta»"; exit 2; }
	for c in gcc pkg-config wayland-scanner; do
		command -v "$c" >/dev/null || { ko "⛔ «$c» non c'e': questo ramo va girato DENTRO il contenitore"; exit 2; }
	done
	proto=/usr/share/wayland-protocols
	xdg=$proto/stable/xdg-shell/xdg-shell.xml
	pres=$proto/stable/presentation-time/presentation-time.xml
	for f in "$xdg" "$pres"; do
		[ -s "$f" ] || { ko "⛔ manca «$f»"; exit 2; }
	done
	mkdir -p "$SCENA_LAV" || { ko "⛔ non ho potuto fare $SCENA_LAV"; exit 2; }
	cd "$SCENA_LAV" || exit 2
	wayland-scanner client-header "$xdg"  xdg-shell-client-protocol.h || exit 3
	wayland-scanner private-code  "$xdg"  xdg-shell-protocol.c || exit 3
	wayland-scanner client-header "$pres" presentation-time-client-protocol.h || exit 3
	wayland-scanner private-code  "$pres" presentation-time-protocol.c || exit 3
	CF=$(pkg-config --cflags wayland-client) || { ko "⛔ pkg-config --cflags"; exit 3; }
	LB=$(pkg-config --libs wayland-client) || { ko "⛔ pkg-config --libs"; exit 3; }
	[ -n "$LB" ] || { ko "⛔ pkg-config non ha dato nessuna libreria: NON compilo a meta'"; exit 3; }
	inf "librerie: $LB"
	# shellcheck disable=SC2086
	gcc -O2 -Wall -Wextra -o 03-scena "$SCENA_C" \
	    xdg-shell-protocol.c presentation-time-protocol.c -I. $CF $LB -lrt \
		|| { ko "⛔ la scena non si e' compilata"; exit 3; }
	chmod 755 "$SCENA_LAV" 03-scena
	ok "⭐ scena costruita: $SCENA_LAV/03-scena"
	exit 0 ;;

scena-uscite)
	# ⛔ Quali monitor il compositore offre, chiesti a LUI e non dedotti.  ⚠ Il
	#    monitor del PRODOTTO nasce quando nasce il figlio: se qui non compare,
	#    il server non e' acceso o nessuno e' ancora entrato — e sono due fatti
	#    diversi da «non c'e' nessun monitor».
	[ -x "$SCENA_LAV/03-scena" ] || { ko "⛔ la scena non e' costruita"; exit 2; }
	setpriv --reuid=1000 --regid=1000 --init-groups \
		env XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 \
		    HOME=/home/nicfio USER=nicfio \
		"$SCENA_LAV/03-scena" --uscite
	exit $? ;;

scena-avvia)
	# ⛔⭐ LA SCENA, DICHIARATA — `LEZIONI.md` §1.1, e senza di essa questo banco
	#     NON MISURA NIENTE.
	#
	#     «Un compositore Wayland consegna un fotogramma solo quando qualcosa
	#     cambia.  Ne discende che qualunque misura di fotogrammi al secondo
	#     dipende dalla scena tanto quanto dal compositore, e che una misura
	#     senza la scena dichiarata NON E' UNA MISURA.»  `[M]` 13 agosto 2026:
	#     il primo giro dal vivo di questo banco ha contato **zero fotogrammi**
	#     su un desktop fermo, e la catena funzionava perfettamente.
	#
	# ⛔ E QUESTA SCENA NON E' QUELLA DELLO STEP 2, ed e' una differenza di
	#    sostanza, non di file.  La scena dello step 2 gira su un **Mutter
	#    headless tutto suo** (`WAYLAND_DISPLAY=remotix-scena-7602`): il palco
	#    di questo step cattura via `org.gnome.Mutter.ScreenCast` sul **bus di
	#    sessione dell'utente**, cioe' il `gnome-shell` vero — e su quello la
	#    scena dello step 2 non si vede.  ⇒ Serve un movimento **su
	#    `wayland-0`**, e non c'e' modo di prenderlo in prestito.
	#
	# ⚠ E IL PREZZO SI DICHIARA: questa e' una finestra sul desktop
	#   dell'utente.  ⭐ Per questo NON e' a schermo intero — `LEZIONI.md` §1.1
	#   la vorrebbe `-f -o`, e qui si rinuncia deliberatamente al «-f»: una
	#   finestra piccola cambia una parte dello schermo invece di tutto, il che
	#   **abbassa** il conto dei fotogrammi (meno danno da dichiarare) ma non
	#   copre lo schermo a chi ci sta lavorando.  ⛔ E' un compromesso, ed e'
	#   scritto qui perche' chi legge il numero sappia da dove viene.
	#
	# ⭐ E SI CONTA QUANTO DISEGNA IL CLIENT (la seconda meta' di §1.1, quella
	#    che si dimentica): `weston-simple-egl` stampa da se' «N frames in M
	#    seconds: X fps» sul suo registro, ed e' il controllo che dice se il
	#    tetto e' del compositore o della scena.
	USCITA=${2:-}
	[ -S /run/user/1000/wayland-0 ] || { ko "⛔ /run/user/1000/wayland-0 non c'e': niente scena"; exit 2; }
	[ -x "$SCENA_LAV/03-scena" ] || { ko "⛔ la scena non e' costruita: «scena-costruisci»"; exit 2; }
	# ⛔⭐ E IL MONITOR SI CHIEDE PER NOME.  Il palco del prodotto e' un monitor
	#     VIRTUALE che il figlio monta con `RecordVirtual` (`mutter.c`): sul
	#     `wayland-0` dell'utente ce ne sono due, il suo schermo vero e il
	#     nostro.  `[M]` 13 agosto 2026: la prima scena di questo banco e'
	#     finita sullo schermo VERO e la cattura ha contato **zero fotogrammi
	#     per dieci secondi** con la catena perfettamente funzionante — un rosso
	#     puntato sull'imputato sbagliato, che e' il difetto che il commento di
	#     `03-scena.c` nomina parola per parola.
	if [ -z "$USCITA" ]; then
		# Il nome lo dice il REGISTRO DEL SERVER, che l'ha chiesto a Mutter.
		USCITA=$(grep -o 'monitor «[^»]*»' "$LOG" 2>/dev/null | tail -1 | sed 's/monitor «//; s/»//')
	fi
	if [ -z "$USCITA" ] || [ "$USCITA" = "(non l'ho saputo dire)" ]; then
		ko "⛔ non so su quale monitor sta il palco del prodotto: il registro non"
		ko "   lo nomina.  ⚠ Accendere la scena «da qualche parte» produrrebbe"
		ko "   uno zero che accusa il prodotto invece della scena — e NON lo faccio."
		exit 2
	fi
	inf "il palco del prodotto e' il monitor «$USCITA» (letto dal registro, non dedotto)"
	if [ -f "$LAV/scena.pid" ] && [ -d "/proc/$(cat "$LAV/scena.pid" 2>/dev/null)" ]; then
		ok "la scena e' gia' viva (pid $(cat "$LAV/scena.pid"))"
		exit 0
	fi
	mkdir -p "$LAV"
	: > "$LAV/scena.log"
	chmod 666 "$LAV/scena.log"
	# ⛔⭐ E `stdbuf -oL` NON E' UN ORPELLO — `[M]` 13 agosto 2026, primo giro.
	#
	#     Senza, il conteggio che il client stampa da se' finisce in un buffer a
	#     blocchi (stdout rediretto su un file non e' un terminale) e **non
	#     compare** finche' il processo non muore.  ⇒ Il marcatore «sta
	#     disegnando» non maturava mai, e il banco diceva «viva ma non disegna»
	#     di una scena che disegnava a 60 al secondo.  ⚠ E' la forma «vuoto e
	#     proibito hanno la stessa faccia» spostata sul buffer della libc.
	#
	# ⛔ E `HOME` va dato: senza, `setpriv` lascia quello di root e mesa scrive
	#    «Failed to create /root/.cache» — una scena che parte ma senza cache
	#    degli shader, cioe' una misura diversa sotto la stessa etichetta.
	setpriv --reuid=1000 --regid=1000 --init-groups \
		env XDG_RUNTIME_DIR=/run/user/1000 WAYLAND_DISPLAY=wayland-0 \
		    HOME=/home/nicfio USER=nicfio \
		    DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
		nohup stdbuf -oL -eL "$SCENA_LAV/03-scena" --uscita "$USCITA" \
		    --movimento pieno --danno pieno --shm "$SCENA_SHM" --loquace \
		    >> "$LAV/scena.log" 2>&1 &
	pid=$!
	echo "$pid" > "$LAV/scena.pid"
	# ⛔ Marcatore, non `sleep`: «il processo e' vivo» e «sta disegnando» sono
	#    due fatti diversi, e alla misura serve il secondo.  Si aspetta la prima
	#    riga di conteggio che il client stampa da se'.
	# ⚠ 15 s: `weston-simple-egl` stampa il suo conteggio ogni 5 secondi, e il
	#   primo puo' cadere subito dopo l'avvio.
	g=0
	while [ "$g" -lt 60 ]; do
		[ -d "/proc/$pid" ] || break
		grep -qE 'disegn|frame|uscita' "$LAV/scena.log" 2>/dev/null && break
		sleep 0.25; g=$((g+1))
	done
	if [ ! -d "/proc/$pid" ]; then
		ko "⛔ la scena e' morta subito:"
		sed 's/^/        /' "$LAV/scena.log"
		exit 3
	fi
	if grep -qE 'disegn|frame|uscita' "$LAV/scena.log" 2>/dev/null; then
		ok "⭐ scena viva sul monitor «$USCITA» (pid $pid)"
		tail -6 "$LAV/scena.log" | sed 's/^/        /'
	else
		ko "⛔ la scena e' viva ma non ha ancora stampato un conteggio: NON dico"
		ko "   che sta disegnando (LEZIONI.md §1.9 — «vivo» non e' «disegna»)"
		exit 3
	fi
	exit 0 ;;

scena-conta)
	# ⛔ Quanto disegna il CLIENT, che e' il controllo che dice se il tetto e'
	#    del compositore o della scena (§1.1, seconda meta').
	if [ ! -f "$LAV/scena.log" ]; then
		ko "⛔ non c'e' nessun registro della scena: non ho guardato, e questo"
		ko "   non e' «la scena non disegna»"
		exit 2
	fi
	tail -8 "$LAV/scena.log"
	exit 0 ;;

scena-ferma)
	if [ -f "$LAV/scena.pid" ]; then
		pid=$(cat "$LAV/scena.pid")
		kill "$pid" 2>/dev/null
		g=0; while [ -d "/proc/$pid" ] && [ "$g" -lt 20 ]; do sleep 0.25; g=$((g+1)); done
		[ -d "/proc/$pid" ] && ko "⛔ la scena (pid $pid) non e' morta" || ok "scena ferma (pid $pid)"
		rm -f "$LAV/scena.pid"
	else
		inf "nessuna scena mia accesa"
	fi
	exit 0 ;;

stato)
	log "Lo stato dello step 3"
	inf "$(vicini)"
	if ! pid=$(mio_pid); then
		inf "non c'e' niente di mio acceso (nessun $PIDF vivo)"
		exit 1
	fi
	ok "acceso: pid $pid, porta $PORTA"
	inf "binario: $D/remotix ($(impronta "$D/remotix")…)"
	# ⛔ I figli si chiedono al NUCLEO e sono i PROPRI: `pgrep -f --figlio-interno`
	#    conterebbe anche quelli degli altri banchi, e in fase 3 gli altri
	#    banchi girano.  E' il difetto gia' nominato in `02-figlio-accendi.sh`.
	trovati=0
	for f in $(pgrep -P "$pid" 2>/dev/null); do
		riga=$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)
		case "$riga" in
		*--figlio-interno*)
			u=$(awk '/^Uid:/{print $2}' "/proc/$f/status" 2>/dev/null)
			inf "figlio pid $f · uid $u · «$riga»"
			trovati=$((trovati+1)) ;;
		esac
	done
	[ "$trovati" -eq 0 ] && inf "nessun figlio (nessuno e' ancora entrato)"
	exit 0 ;;

cattura-conta)
	# ⛔⭐ QUANTE VOLTE IL PALCO HA COMINCIATO A CATTURARE, e serve a decidere
	#     QUANDO accendere la scena.
	#
	#     `[M]` 13 agosto 2026: Mutter non manda i *frame callback* a una
	#     superficie che sta su un monitor **che nessuno sta registrando**, e il
	#     palco del prodotto e' un monitor virtuale che si registra solo mentre
	#     una sessione RCP e' attaccata.  ⇒ Una scena accesa PRIMA della
	#     sessione resta viva e non disegna, il banco conta zero fotogrammi e il
	#     rosso finisce sul prodotto.
	#
	# ⛔ E sta QUI, in un file, invece che dentro `ssh → enter.sh → bash -c`:
	#    un file non ha livelli di virgolette (`FASI.md` §00-ambiente B3.3), e la
	#    prima stesura che ci infilava un `grep` con gli spazi contava zero su
	#    un registro che la riga ce l'aveva — cioe' diceva «non e' successo»
	#    dove il vero fatto era «non ho guardato».
	printf 'CONTO=%s\n' "$(grep -ac 'il ciclo dei fotogrammi si ACCENDE' "$LOG" 2>/dev/null)"
	exit 0 ;;

registro)
	QUANTE=${2:-60}
	grep -E '^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} (avvio|figlio|video|rcp|wt) ' \
		"$LOG" 2>/dev/null | tail -"$QUANTE"
	exit 0 ;;

spegni)
	log "Spengo"
	inf "$(vicini)"
	if ! pid=$(mio_pid); then ok "non c'era niente acceso sulla $PORTA"; exit 0; fi
	# ⛔ I pid dei PROPRI figli si prendono PRIMA di uccidere il padre.
	miei=""
	for f in $(pgrep -P "$pid" 2>/dev/null); do
		riga=$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)
		case "$riga" in *--figlio-interno*) miei="$miei $f" ;; esac
	done
	kill "$pid" 2>/dev/null
	g=0
	while [ -d "/proc/$pid" ] && [ "$g" -lt 30 ]; do sleep 0.5; g=$((g+1)); done
	[ -d "/proc/$pid" ] && { ko "il pid $pid non e' morto"; exit 3; }
	rm -f "$PIDF" "$SOCK"
	restano=0
	for f in $miei; do
		riga=$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null) || continue
		case "$riga" in *--figlio-interno*) restano=$((restano+1)) ;; esac
	done
	ok "spento (pid $pid)"
	if [ "$restano" -eq 0 ]; then
		ok "⭐ nessun figlio MIO e' rimasto orfano"
	else
		ko "⛔ $restano figli MIEI sono ancora vivi: orfani attaccati al monitor"
		ko "   virtuale di qualcuno"
	fi
	inf "$(vicini)"
	[ "$restano" -eq 0 ] || exit 4
	exit 0 ;;

accendi) ;;
riaccendi) bash "$0" spegni || exit 3 ;;
*) echo "uso: $0 [stato|accendi|spegni|riaccendi|registro|scena-avvia|scena-conta|scena-ferma]"; exit 2 ;;
esac

# --- accendi ---------------------------------------------------------------
log "0. Il terreno, dichiarato prima di toccarlo"
inf "$(vicini)"
[ "$(id -u)" -eq 0 ] || { ko "⛔ questo va lanciato DA ROOT: il palco e' dell'UTENTE"; exit 2; }
[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html non c'e'"; exit 2; }
inf "binario: $D/remotix ($(impronta "$D/remotix")…, $(stat -c '%y' "$D/remotix"))"

command -v ss >/dev/null || { ko "⛔ «ss» non c'e': non ho guardato la porta, e non la chiamo libera"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
[ "$n" -eq 0 ] || { ko "⛔ la porta $PORTA e' gia' occupata ($n righe): non e' mia, non la tocco"
	ss -tuln | grep ":$PORTA\b"; exit 2; }
ok "porta $PORTA libera (ss ha guardato e ha stampato $n righe)"

mkdir -p "$CERT" "$RILIEVO" || { ko "⛔ non ho potuto preparare $LAV"; exit 2; }
chmod 1777 "$RILIEVO"

log "1. Le librerie: quelle costruite, non quelle dei pacchetti"
export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if ! ldd "$D/remotix" > "$LAV/ldd.txt" 2>&1; then
	ko "⛔ ldd non ha finito: non dico che le librerie ci sono"; exit 2
fi
grep -q 'not found' "$LAV/ldd.txt" && { ko "⛔ manca una libreria:"
	grep 'not found' "$LAV/ldd.txt" | sed 's/^/        /'; exit 2; }
for l in libngtcp2 libnghttp3; do
	riga=$(grep -m1 "$l" "$LAV/ldd.txt")
	case "$riga" in
	*/media/REMOTIX/src/b2/*) ok "$l ← $(printf '%s' "$riga" | sed 's/^[[:space:]]*//')" ;;
	*)  ko "⛔ $l NON viene dall'albero costruito: stesso soname, altra libreria"; exit 2 ;;
	esac
done

log "2. Il servizio PAM sull'host"
[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix NON C'E': PAM ripiega su"
	ko "   «other» = pam_deny, e OGNI parola giusta sara' rifiutata"; exit 2; }
ok "/etc/pam.d/remotix c'e'"

log "3. Il palco che i figli troveranno"
for u in 1000 1001; do
	if [ -S "/run/user/$u/bus" ]; then
		ok "uid $u: /run/user/$u/bus c'e' — un figlio a questo uid avra' il bus"
	else
		inf "⚠ uid $u: /run/user/$u/bus NON c'e' — un figlio a questo uid nascera',"
		inf "   lo DIRA', e restera' senza palco (non e' un difetto: e' un utente"
		inf "   che non ha mai fatto login su questa macchina)"
	fi
done

log "4. Accendo — DA ROOT, sulla $PORTA"
# ⛔ Il registro si apre IN CODA, mai troncato: `: > file` su un registro che un
#    processo tiene aperto ci scava dentro un buco di NUL, e `grep` che incontra
#    un NUL smette di stampare le righe **con lo stesso stato d'uscita 0**.
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
      --certificati "$CERT" --pagina "$D/pagina.html" \
      --ban-file "$BAN" --comando-socket "$SOCK" \
      --rilievo "$RILIEVO" --parlantina \
      >> "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

# ⛔ Marcatori, non `sleep`: «il processo e' vivo» e «la porta risponde» sono due
#    fatti diversi, e alla misura serve il secondo.
g=0
while [ "$g" -lt 60 ]; do
	[ -d "/proc/$pid" ] || break
	[ "$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")" -ge 2 ] && break
	sleep 0.5; g=$((g+1))
done
if [ ! -d "/proc/$pid" ]; then
	ko "⛔ il server e' morto subito.  Le ultime righe del registro:"
	tail -20 "$LOG" | sed 's/^/        /'
	exit 3
fi
righe=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
[ "$righe" -ge 2 ] || { ko "⛔ pid $pid vivo ma $righe ascoltatori: §2.4 ne vuole DUE"
	tail -20 "$LOG" | sed 's/^/        /'; exit 3; }
ok "acceso, pid $pid, $righe ascoltatori su :$PORTA dopo $((g/2)) s"

log "5. Che cosa ha detto all'avvio"
grep -E '^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} (avvio|figlio|video) ' "$LOG" \
	| tail -10 | sed 's/^/        /'
inf "$(vicini)"
exit 0
