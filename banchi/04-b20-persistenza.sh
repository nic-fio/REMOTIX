#!/bin/bash
#
# 04-b20-persistenza.sh — ⛔ GIRA SUL SERVER (NIC-OS), FUORI dal contenitore e
# DA ROOT.  La seconda domanda di A1: **che cosa succede allo schermo quando il
# client si stacca**, adesso che l'unico monitor della sessione e' il suo.
#
#   sudo bash .../04-b20-persistenza.sh prepara    registro della Shell + scena
#   sudo bash .../04-b20-persistenza.sh controllo  ⭐ i due controlli POSITIVI
#   sudo bash .../04-b20-persistenza.sh guarda <etichetta>
#   sudo bash .../04-b20-persistenza.sh scena-via
#
# ===========================================================================
# ⛔ LA TESI DA REFUTARE, e si parte dall'ipotesi che sia falsa
# ===========================================================================
#
#   «Con la cura, un client che si stacca porta via l'unico monitor della
#    sessione: da quel momento la sessione sopravvive **senza avere dove
#    disegnare**, e le applicazioni aperte se ne accorgono.»
#
# ⛔ Perche' pesa: `SPECIFICHE.md` §5.2 e l'invariante **I4** promettono che *il
#    palco appartiene alla sessione, non alla connessione*; e `PIANO.md` (fase 5)
#    registra che in v1 questo caso mandava **`libmutter` in asserzione fallita**,
#    con le applicazioni che perdevano la connessione Wayland.  ⇒ E' il difetto
#    che rende la sessione inutilizzabile **dal secondo attacco in poi**.
#
# ⚠ E la domanda che c'era prima — «va bene che la sessione nasca nera?» — non
#   esiste: la sessione nasce quando qualcuno si collega.  ⭐ Il caso vero e'
#   questo, ed e' l'altro capo.
#
# ===========================================================================
# ⛔ DUE ESITI CHE NON SONO LO STESSO — e solo il primo e' un difetto
# ===========================================================================
#
#   A. **il monitor e' SPARITO**       `GetCurrentState` → 0 monitor
#      ⇒ la sessione non ha dove disegnare, e le applicazioni se ne accorgono
#   B. **il monitor c'e', e nessuno lo cattura**   → 1 «Virtual remote monitor»
#      ⇒ il palco e' rimasto in piedi: e' I4 mantenuta, e NON e' un difetto
#
# ⛔ Un banco che stampasse solo «tutto bene» non li distinguerebbe: qui si
#    stampa **il conteggio e i nomi**, sempre.
#
# ===========================================================================
# ⛔ «VUOTO» E «NON HO SAPUTO GUARDARE» HANNO LA STESSA FACCIA
# ===========================================================================
#
# Da cui `controllo`, che si fa **prima** di credere a `guarda`:
#   · lo strumento sa vedere un monitor che c'e' di sicuro?
#   · lo strumento sa dire che un'applicazione e' MORTA davvero?
# Se uno dei due non risponde, il verdetto di `guarda` non vale niente.
set -uo pipefail

UTENTE=${UTENTE:-provaa1}
UID_B=${UID_B:-1002}
UNITA=org.gnome.Shell@wayland.service
PORTA=${PORTA:-7601}
LAV=${LAV:-/media/REMOTIX/tmp/04-b20}
ESITI=$LAV/04-b20-persistenza.jsonl
RT=/run/user/$UID_B
OROLOGIO=$RT/banco-A1-orologio.log
MUTTERLOG=$RT/mutter.log

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

come_utente() {
	setpriv --reuid="$UID_B" --regid="$UID_B" --init-groups \
		env -i HOME="/home/$UTENTE" USER="$UTENTE" SHELL= LANG=C.UTF-8 \
		PATH=/usr/local/bin:/usr/bin:/bin \
		XDG_RUNTIME_DIR="$RT" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=$RT/bus" \
		XDG_CURRENT_DESKTOP=GNOME XDG_SESSION_DESKTOP=gnome \
		XDG_SESSION_TYPE=wayland "$@"
}

stato_grezzo() {
	come_utente busctl --user call org.gnome.Mutter.DisplayConfig \
		/org/gnome/Mutter/DisplayConfig org.gnome.Mutter.DisplayConfig \
		GetCurrentState 2>&1
}

# ⛔ Tre esiti, non due: il numero, i nomi, e «non ho potuto chiedere».
#
# ⛔⛔ E SI DIVIDE PER DUE, e non e' una furbizia: `GetCurrentState` elenca ogni
#     schermo **due volte** — una nell'array dei monitor e una in quello dei
#     monitor LOGICI.  `[M]` 14 agosto 2026: la prima stesura di questa funzione
#     non divideva, e ha scritto **«monitor: 2»** su una sessione che ne aveva
#     **uno**.  ⚠ Ha sbagliato nella direzione che rassicura — «ce n'e' piu' di
#     quanti credessi» — cioe' quella che non si vede.  Le due righe di
#     `04-b20-persistenza.jsonl` scritte alle 07:37 portano ancora il numero
#     doppio, e restano li' come sono: i NOMI accanto permettono di ricavare il
#     vero, e cancellarle sarebbe cancellare la prova dell'errore.
monitor_conta() {
	local r n
	r=$(stato_grezzo)
	case "$r" in
	*MetaVendor*|*layout-mode*) ;;
	*)  echo "IGNOTO"; return 2 ;;
	esac
	n=$(printf '%s' "$r" | tr ' ' '\n' | grep -c '^"Meta-[0-9]*"$')
	echo $((n / 2))
}

monitor_nomi() {
	stato_grezzo | tr ' ' '\n' \
		| grep -E '^"(Meta-[0-9]+|MetaVirtualMonitor|Virtual)' | tr '\n' ' '
}

# Il ciclo che scrive l'ora: vivo?  e da quanto?  ⛔ L'eta' serve a distinguere
# «e' la stessa finestra di prima» da «ne e' nata un'altra».
orologio_pid()  { pgrep -u "$UID_B" -f 'banco-A1-orologio' | head -1; }
orologio_eta()  { local p; p=$(orologio_pid); [ -n "$p" ] && ps -o etimes= -p "$p" | tr -d ' '; }

case "${1:-guarda}" in
prepara)
	log "1. Il registro della Shell in un file — o le asserzioni non le legge nessuno"
	# ⛔ `gnome-session` NON lancia `gnome-shell`: fa partire l'unita' d'utente,
	#    quindi i messaggi di Mutter non ereditano la nostra redirezione e vanno
	#    al journal.  ⚠ E su questa macchina il journal non e' una strada (il
	#    rootfs vive in RAM).  ⇒ Un drop-in che li manda in un file NOSTRO: e'
	#    la stessa cura di `banchi/00-sessione-gnome.sh`.
	# ⚠ `00-` apposta: non deve mai vincere sul `zz-` del prodotto, che decide
	#   l'ExecStart.  Qui si tocca solo dove va a finire l'uscita.
	D="$RT/systemd/user.control/$UNITA.d"
	install -d -o "$UID_B" -g "$UID_B" -m 700 "$D" || exit 2
	printf '[Service]\nStandardOutput=append:%s\nStandardError=append:%s\n' \
		"$MUTTERLOG" "$MUTTERLOG" > "$D/00-registro.conf"
	chown "$UID_B:$UID_B" "$D/00-registro.conf"
	: > "$MUTTERLOG"; chown "$UID_B:$UID_B" "$MUTTERLOG"
	come_utente systemctl --user daemon-reload
	ok "il registro della Shell andra' in $MUTTERLOG"
	inf "⚠ vale dalla PROSSIMA nascita della sessione: il drop-in non riscrive"
	inf "   l'uscita di un processo gia' partito"
	exit 0 ;;

scena)
	# ⭐ LA FINESTRA CHE LAVORA DA SOLA, e che si accorgerebbe di perdere lo
	#    schermo.  ⛔ Scrive l'ora in DUE posti, e non e' un doppione:
	#      · sullo SCHERMO, perche' e' quel che l'utente deve ritrovare;
	#      · in un FILE, perche' con nessuno collegato lo schermo non si puo'
	#        guardare — e senza il file «l'applicazione e' andata avanti» e
	#        «non ho potuto vederlo» avrebbero la stessa faccia.
	log "La scena persistente: una finestra che scrive l'ora, sullo schermo e su file"
	come_utente pkill -f 'banco-A1-orologio' >/dev/null 2>&1
	sleep 1
	: > "$OROLOGIO"; chown "$UID_B:$UID_B" "$OROLOGIO"
	come_utente setsid --fork gnome-terminal --title=banco-A1-orologio -- \
		bash -c "while true; do d=\$(date +%H:%M:%S.%3N); echo \"banco-A1-orologio \$d\"; echo \"\$d\" >> $OROLOGIO; sleep 0.2; done" \
		>/dev/null 2>&1
	sleep 6
	p=$(orologio_pid)
	if [ -n "$p" ] && [ -s "$OROLOGIO" ]; then
		ok "accesa: pid $p, il file cresce (ultima riga $(tail -1 "$OROLOGIO"))"
	else
		ko "⛔ la scena NON si e' accesa: quel che segue misurerebbe un fermo"
		exit 3
	fi
	exit 0 ;;

scena-via)
	come_utente pkill -f 'banco-A1-orologio' >/dev/null 2>&1
	ok "scena spenta"
	exit 0 ;;

controllo)
	# ===================================================================
	# ⭐ I DUE CONTROLLI POSITIVI — si fanno PRIMA di credere a `guarda`
	# ===================================================================
	log "⭐ Controllo 1: lo strumento sa vedere un monitor che c'e' di sicuro?"
	n=$(monitor_conta)
	inf "GetCurrentState dice: $n — nomi: $(monitor_nomi)"
	if [ "$n" = "IGNOTO" ]; then
		ko "⛔ non ho potuto CHIEDERE: da qui in poi «zero monitor» non vorrebbe"
		ko "   dire niente.  Esco 2, non verde."
		exit 2
	fi
	if [ "$n" -ge 1 ]; then
		ok "⭐ vede $n monitor: lo strumento sa trovare quel che c'e'"
		c1=0
	else
		ko "⚠ adesso i monitor sono ZERO: questo controllo va rifatto CON un"
		ko "   client attaccato, o non prova niente"
		c1=1
	fi

	log "⭐ Controllo 2: lo strumento sa dire che un'applicazione e' MORTA?"
	# ⛔ Un'esca con lo stesso nome del vero orologio, cosi' si prova ESATTAMENTE
	#    lo strumento che si usera' dopo — non uno che gli somiglia.
	come_utente setsid --fork bash -c 'exec -a banco-A1-orologio-esca sleep 300' \
		>/dev/null 2>&1
	sleep 2
	e=$(pgrep -u "$UID_B" -f 'banco-A1-orologio-esca' | head -1)
	if [ -z "$e" ]; then
		ko "⛔ l'esca non e' partita: il controllo 2 non prova niente"
		exit 2
	fi
	ok "l'esca c'e' (pid $e) e lo strumento la vede"
	kill -9 "$e" 2>/dev/null; sleep 2
	if pgrep -u "$UID_B" -f 'banco-A1-orologio-esca' >/dev/null 2>&1; then
		ko "⛔ l'esca e' stata uccisa e lo strumento la vede ANCORA VIVA:"
		ko "   «l'applicazione e' viva» non vorrebbe dire niente"
		exit 2
	fi
	ok "⭐ uccisa, lo strumento dice che e' morta: sa distinguere vivo da morto"
	exit "$c1" ;;

guarda)
	ET=${2:-senza-nome}
	log "MISURA «$ET» — $(date -u +%H:%M:%SZ)"
	n=$(monitor_conta)
	nomi=$(monitor_nomi)
	p=$(orologio_pid)
	eta=$(orologio_eta)
	ultima=$(tail -1 "$OROLOGIO" 2>/dev/null)
	righe=$(wc -l < "$OROLOGIO" 2>/dev/null || echo 0)
	shell=$(pgrep -u "$UID_B" -x gnome-shell | head -1)
	asser=$(grep -ciE 'assertion|Assertion .* failed|SIGSEGV|core dumped' "$MUTTERLOG" 2>/dev/null || echo 0)
	critici=$(grep -ciE 'CRITICAL|WARNING.*Wayland|disconnect' "$MUTTERLOG" 2>/dev/null || echo 0)
	# ⛔⛔ I CLIENTI SI CHIEDONO AL PRODOTTO, e da `ss` NON SI POSSONO SAPERE.
	#
	#     `[M]` 14 agosto 2026, e sono DUE errori uno sopra l'altro:
	#       1. la prima stesura contava `ss -tn state established | grep 7601`,
	#          cioe' su **TCP**, e il filo e' QUIC: zero sempre;
	#       2. corretto in `ss -uan`, **zero un'altra volta** — e non era un
	#          altro sbaglio di riga: QUIC vive su **un solo socket UDP non
	#          connesso**, quindi `ss` non ha nessuna riga per client.  ⇒ Quel
	#          numero non era scritto male: **non esisteva**.
	#     ⚠ Nessuno dei due entrava nel verdetto, ed e' precisamente per questo
	#       che sarebbero rimasti li' a mentire.
	#
	# ⭐ La cura e' `LEZIONI.md` §1.6: non si deduce, **si chiede al componente**.
	#    Il server scrive «(ne restano N)» a ogni chiusura di connessione.
	clienti=$(grep -o 'ne restano [0-9]*' "$LAV/registro.log" 2>/dev/null \
		| tail -1 | tr -dc '0-9')
	clienti=${clienti:-"?"}

	# ⛔ Il conteggio dei monitor NON basta: si scrive anche di CHE COSA sono,
	#    perche' «uno» puo' essere il nostro o quello di qualcun altro.
	inf "monitor: $n   nomi: ${nomi:-(nessuno)}"
	inf "gnome-shell: ${shell:-⛔ NON C'E'}"
	inf "orologio: pid ${p:-⛔ MORTO}, vivo da ${eta:-?} s, $righe righe, ultima «${ultima:-(niente)}»"
	inf "registro della Shell: $asser righe di asserzione/segnale, $critici critiche"
	inf "connessioni stabilite sulla 7601: $clienti"

	case "$n" in
	IGNOTO) verdetto="NON HO POTUTO GUARDARE" ;;
	0)      verdetto="A: IL MONITOR E' SPARITO" ;;
	*)      case "$nomi" in
		*Virtual*) verdetto="B: IL MONITOR C'E', E NESSUNO LO CATTURA" ;;
		*)         verdetto="B-bis: C'E' UN MONITOR, MA NON E' IL NOSTRO" ;;
		esac ;;
	esac
	printf '    ⇒ \033[1m%s\033[0m\n' "$verdetto"

	printf '{"quando":"%s","banco":"04-b20-persistenza","etichetta":"%s","monitor":"%s","nomi":"%s","shell_pid":"%s","orologio_pid":"%s","orologio_eta_s":"%s","orologio_righe":"%s","orologio_ultima":"%s","asserzioni":"%s","critiche":"%s","clienti_7601":"%s","verdetto":"%s"}\n' \
		"$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$ET" "$n" "$nomi" "${shell:-}" \
		"${p:-}" "${eta:-}" "$righe" "${ultima:-}" "$asser" "$critici" \
		"$clienti" "$verdetto" >> "$ESITI"
	exit 0 ;;

*) sed -n '2,12p' "$0"; exit 2 ;;
esac
