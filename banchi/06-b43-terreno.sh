#!/bin/bash
#
# 06-b43-terreno.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore e
# **DA ROOT**.  Il terreno del banco `06-b43` — *quanto si tiene il posto*.
#
#   sudo bash .../06-b43-terreno.sh utente            provar7 (uid 1018)
#   sudo bash .../06-b43-terreno.sh sessione          GNOME headless
#   sudo bash .../06-b43-terreno.sh accendi [opz...]  il server sulla 7801
#   sudo bash .../06-b43-terreno.sh spegni
#   sudo bash .../06-b43-terreno.sh stato
#   sudo bash .../06-b43-terreno.sh registro [n]
#   sudo bash .../06-b43-terreno.sh orologi           ⭐ i tetti IN VIGORE
#   sudo bash .../06-b43-terreno.sh figlio            il pid del figlio, o niente
#   sudo bash .../06-b43-terreno.sh posti             i posti occupati adesso
#   sudo bash .../06-b43-terreno.sh pulisci
#
# ===========================================================================
# ⛔ L'ISOLAMENTO — cinque cose proprie, e nessuna e' pignoleria
# ===========================================================================
#
# Porta **7801**, utente **provar7**, ban-file, socket di comando e albero
# propri.  ⛔ Il ban di §4.4-bis e' per INDIRIZZO e dura 12 ore: un banco che
# lo facesse scattare metterebbe fuori uso **tutti** gli altri, perche' otto
# agenti partono dallo stesso indirizzo.  ⛔ **7700**, **7730**, **7781** e
# l'utente **`prova`** NON SI TOCCANO.
#
# ===========================================================================
# ⭐ E IL SERVER PARTE COME UNITA' DI SISTEMA, non da questa ssh
# ===========================================================================
#
# `setsid` stacca dal terminale ma **non** dalla sessione di logind: da dentro
# una sessione ssh `pam_systemd` non ne crea una seconda per il figlio, e il
# sintomo e' «il desktop non parte».  E' la trappola 4 di `riavvia-7700.sh`,
# misurata il 16 agosto 2026.  ⇒ `systemd-run`, in `system.slice`, ⛔ **e si
# verifica dopo** che il cgroup non contenga `user@` ne' `session-`.
#
# ===========================================================================
# ⭐⭐ `orologi` — E PERCHE' E' UN COMANDO E NON UN COMMENTO
# ===========================================================================
#
# `SPECIFICHE.md` §5.3 promette che *«il valore in vigore si scrive nel
# registro all'avvio»*, e `main.c:1020` lo fa.  ⛔ Questo banco misura un
# **tetto**: leggerne il valore nel sorgente invece che dal processo vivo
# sarebbe la trappola **E1** — *«scritto non e' in vigore»* — commessa
# esattamente sul numero che si sta misurando.
#
# `[M]` 22 agosto 2026, la riga che il server ha scritto sulla 7801:
#
#   ⭐ §5.3, i tre orologi in vigore: silenzio del client 30 s (fisso) ·
#     inattivita' dell'utente 1800 s · ⛔ abbandono della sessione 3600 s
#
# ⛔⛔ E LA PAROLA CHE CONTA E' **«(fisso)»**: dei tre orologi di §5.3, il
#      primo — quello che questo banco misura — **non e' parametrizzabile**.
#      `SILENZIO` e' un `#define` in `rcp.c` e `IDLE_MS` un `#define` in
#      `trasporto.c`, tutt'e due 30 000 ms.  ⇒ Il consiglio *«usa gli orologi
#      accorciati invece di aspettare»* **non si applica a questo tetto**: qui
#      si aspettano i trenta secondi veri, ogni volta.  ⚠ E va bene cosi', sono
#      trenta secondi; ⛔ ma chi legge `riavvia-7700.sh` e crede che
#      `--inattivita-s` accorci *«l'orologio del silenzio»* sta accorciando
#      **l'altro**, quello da trenta MINUTI, e misurerebbe una cosa per l'altra.
#
# ⭐ `--inattivita-s` serve lo stesso, e a questo banco serve **come controllo
#    positivo**: e' l'unico modo di far liberare il posto a un'ora DIVERSA da
#    30 s, cioe' di dimostrare che i 30 s non sono un artefatto dello
#    strumento.  Vedi `06-b43-lancia.sh`.
set -uo pipefail

PORTA=${PORTA:-7801}
IND=${IND:-192.168.0.2}
UTENTE=${UTENTE:-provar7}
UID_B=${UID_B:-1018}
PAROLA=${PAROLA:-provar7-2026}
D=${D:-/media/REMOTIX/src/06-b7-src/src}
LAV=${LAV:-/media/REMOTIX/tmp/06-b7}
B2=${B2:-/media/REMOTIX/src/b2}
LIBS=${LIBS:-$B2/ngtcp2/build/lib:$B2/ngtcp2/build/crypto/ossl:$B2/prefisso/lib}
UNITA_G=org.gnome.Shell@wayland.service
UNITA=remotix-$PORTA

CERT=$LAV/certificati
BAN=$LAV/ban
SOCK=$LAV/comando.sock
LOG=$LAV/registro.log
RILIEVO=$LAV/rilievo
PAR=$LAV/parola

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

# ═══════════════════════════════════════════════════════════════════════════
# ⭐ I GRUPPI DELLA SCHEDA SI DANNO IN UN POSTO SOLO — `attrezzi-gruppi-scheda.sh`
#
# ⛔ Qui c'era `usermod -aG render,video` (o niente affatto), coi NOMI
#    INCHIODATI e senza rileggere: due difetti in una riga sola.  La ragione
#    per cui la cura sta in un file a parte, e i numeri che la giustificano,
#    stanno nel riquadro in testa a quel file — ⛔ non si ricopiano qui, o
#    diventano dieci posti da cui divergere (`LEZIONI.md` §1.47).
# ═══════════════════════════════════════════════════════════════════════════
GRUPPI_SCHEDA_SH=${GRUPPI_SCHEDA_SH:-$(cd "$(dirname "$0")" && pwd)/attrezzi-gruppi-scheda.sh}
[ -f "$GRUPPI_SCHEDA_SH" ] || { ko "⛔ manca $GRUPPI_SCHEDA_SH: senza, l'inquilino nascerebbe CIECO"; exit 2; }
. "$GRUPPI_SCHEDA_SH"


# ⛔ Le porte che NON sono mie: si CONTANO prima e dopo, non si toccano.
vicini() {
	local r=""
	for p in 7700 7730 7771 7781 7791 7792; do
		r="$r$p:$(ss -uln 2>/dev/null | grep -c ":$p\b") "
	done
	printf '%s— ascoltatori NON miei · carico %s\n' \
		"$r" "$(uptime | sed 's/.*average: //')"
}

come_utente() {
	setpriv --reuid="$UID_B" --regid="$UID_B" --init-groups \
		env -i \
		HOME="/home/$UTENTE" USER="$UTENTE" SHELL= LANG=C.UTF-8 \
		PATH=/usr/local/bin:/usr/bin:/bin \
		XDG_RUNTIME_DIR="/run/user/$UID_B" \
		DBUS_SESSION_BUS_ADDRESS="unix:path=/run/user/$UID_B/bus" \
		XDG_CURRENT_DESKTOP=GNOME XDG_SESSION_DESKTOP=gnome \
		XDG_SESSION_TYPE=wayland \
		"$@"
}

mio_pid() {
	local p
	p=$(systemctl show -p MainPID --value "$UNITA.service" 2>/dev/null)
	[ -n "$p" ] && [ "$p" != "0" ] && [ -d "/proc/$p" ] && { echo "$p"; return 0; }
	return 1
}

# ⛔ Il figlio di QUESTO server: fra i figli del MIO pid.  Un `pgrep -f` globale
#    prenderebbe i figli degli altri sette banchi che girano adesso.
mio_figlio() {
	local s f
	s=$(mio_pid) || return 1
	for f in $(pgrep -P "$s" 2>/dev/null); do
		[ -r "/proc/$f/cmdline" ] || continue
		case "$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)" in
		*--figlio-interno*) echo "$f"; return 0 ;;
		esac
	done
	return 1
}

[ "$(id -u)" -eq 0 ] || { ko "⛔ va lanciato DA ROOT"; exit 2; }
mkdir -p "$LAV"

case "${1:-stato}" in
utente)
	log "L'utente del banco 06-b43: $UTENTE (uid $UID_B)"
	inf "$(vicini)"
	if id "$UTENTE" >/dev/null 2>&1; then
		ok "c'e' gia' — non lo rifaccio (una sessione per utente, I2)"
	else
		useradd -m -u "$UID_B" -s /bin/bash "$UTENTE" || {
			ko "⛔ useradd non e' riuscito"; exit 2; }
		ok "creato"
	fi
	printf '%s:%s\n' "$UTENTE" "$PAROLA" | chpasswd || {
		ko "⛔ la parola d'ordine non e' stata posta: PAM dira' sempre di no"
		exit 2; }
	ok "parola d'ordine posta"
	# ⛔ La parola in un file 0600, mai in `argv`: `python3` e' un processo, e
	#    la sua riga di comando la legge chiunque (D12).
	printf '%s' "$PAROLA" > "$PAR"; chmod 600 "$PAR"
	ok "parola in $PAR (0600)"
	# ⛔ Qui c'erano i due nomi INCHIODATI, e un `usermod` fallito non fermava
	#    niente: il banco tirava dritto e misurava una sessione cieca.
	gruppi_scheda_dai_a "$UTENTE" || exit 3
	inf "gruppi: $(id -nG "$UTENTE")"
	loginctl enable-linger "$UTENTE" || { ko "⛔ enable-linger fallito"; exit 2; }
	ok "linger acceso"
	exit 0 ;;

sessione)
	log "La sessione GNOME di $UTENTE — headless, senza --virtual-monitor"
	inf "$(vicini)"
	id "$UTENTE" >/dev/null 2>&1 || { ko "⛔ l'utente non c'e': fai «utente»"; exit 2; }

	DIR="/run/user/$UID_B/systemd/user.control/$UNITA_G.d"
	FILE="$DIR/zz-senza-monitor.conf"
	install -d -o "$UID_B" -g "$UID_B" -m 700 "$DIR" || { ko "⛔ non ho fatto $DIR"; exit 2; }
	printf '[Service]\nExecStart=\nExecStart=/usr/bin/gnome-shell --headless --no-x11\n' > "$FILE"
	chown "$UID_B:$UID_B" "$FILE"

	if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1; then
		ok "c'e' gia' una sessione viva — non la rifaccio"
		exit 0
	fi
	come_utente systemctl --user daemon-reload || { ko "⛔ daemon-reload"; exit 2; }
	come_utente systemctl --user reset-failed >/dev/null 2>&1
	come_utente systemctl --user start pipewire.socket pipewire-pulse.socket >/dev/null 2>&1
	come_utente systemctl --user start pipewire.service wireplumber.service >/dev/null 2>&1
	come_utente systemctl --user is-active pipewire.service >/dev/null 2>&1 \
		&& ok "PipeWire e' vivo" || ko "⚠ PipeWire NON e' vivo"
	# ⛔ SCRITTO NON E' IN VIGORE (E1): si rilegge dal gestore.
	VIG=$(come_utente systemctl --user show -p ExecStart --value "$UNITA_G")
	inf "ExecStart in vigore: $VIG"
	case "$VIG" in *--no-x11*) ok "c'e' «--no-x11»" ;;
		*) ko "⛔ «--no-x11» NON c'e'"; exit 3 ;; esac
	case "$VIG" in *--virtual-monitor*)
		ko "⛔ c'e' ancora «--virtual-monitor»"; exit 3 ;;
		*) ok "e NON c'e' «--virtual-monitor»" ;; esac

	come_utente setsid --fork sh -c \
		"exec >>/run/user/$UID_B/remotix-sessione.log 2>&1; exec gnome-session --session=gnome"
	g=0
	while [ $g -lt 120 ]; do
		if pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 \
		   && come_utente busctl --user list 2>/dev/null | grep -q org.gnome.Shell; then
			break
		fi
		sleep 0.5; g=$((g+1))
	done
	pgrep -u "$UID_B" -x gnome-shell >/dev/null 2>&1 || {
		ko "⛔ la sessione non e' partita in $((g/2)) s"
		tail -20 "/run/user/$UID_B/remotix-sessione.log" 2>&1 | sed 's/^/        /'
		exit 3; }
	ok "sessione viva dopo $((g/2)) s"
	exit 0 ;;

accendi)
	shift
	log "Il server del banco 06-b43, sulla $PORTA — opzioni in piu': $*"
	inf "$(vicini)"
	[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
	[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix non c'e'"; exit 2; }
	export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
	# ⛔ Trappola 1 di `riavvia-7700.sh`: senza questo controllo il binario
	#    prende la ngtcp2 di sistema, parte benissimo e ABORTA al primo che si
	#    collega.  Si verifica PRIMA di fermare quel che c'e'.
	MANCA=$(ldd "$D/remotix" | grep -E 'ngtcp2|nghttp3' | grep -vc "$B2" || true)
	if [ "$MANCA" != "0" ]; then
		ko "⛔ NON parto: ngtcp2/nghttp3 non verrebbero da $B2 —"
		ldd "$D/remotix" | grep -E 'ngtcp2|nghttp3' | sed 's/^/        /'
		exit 2
	fi
	# ⛔⛔⭐ NON SI SPEGNE UN SERVER CHE NON E' MIO — `[M]` 22 agosto 2026, e la
	#      lezione l'ho pagata dal lato della vittima.
	#
	#      Il nome dell'unita' e' `remotix-<porta>`, cioe' **derivato dalla sola
	#      porta**, e il modello (`07-b41-accendi.sh`) fa `systemctl stop
	#      remotix-<porta>` senza guardare di chi sia.  ⇒ Due agenti che non
	#      sono d'accordo su chi possiede una porta **si ammazzano a vicenda in
	#      silenzio**, e chi resta a terra vede «il mio server e' morto a meta'
	#      misura» — un rosso che non e' del prodotto.
	#
	# `[M]` Alle 06:17:38 del 22 agosto 2026 l'unita' `remotix-7801.service`,
	#       mia, e' stata fermata e rimpiazzata da *«REMOTIX_V2, banco 07-b64
	#       (A8)»*: una misura da trenta minuti troncata a 745 s, ⛔ e la mia
	#       sonda che ha continuato a bussare **al server dell'altro** con
	#       credenziali che lui rifiutava — quindici autenticazioni fallite, e
	#       il ban di §4.4-bis per INDIRIZZO scattato nel SUO ban-file
	#       (`/media/REMOTIX/tmp/07-r/ban`, `[192.168.0.2]` per 12 ore).
	#       ⚠ Il danno vero non e' stato al mio banco: e' stato al suo.
	#
	# ⇒ Qui si guarda la DESCRIZIONE dell'unita' prima di toccarla, e se non e'
	#   la mia ci si ferma invece di spegnerla.
	VECCHIA=$(systemctl show -p Description --value "$UNITA.service" 2>/dev/null)
	if [ -n "$VECCHIA" ] && [ "$VECCHIA" != "${UNITA}.service" ]; then
		case "$VECCHIA" in
		*06-b43*) inf "sulla $PORTA c'e' il MIO server ($VECCHIA): lo rifaccio" ;;
		*)
			ko "⛔⛔ SULLA $PORTA C'E' IL SERVER DI QUALCUN ALTRO:"
			ko "     «$VECCHIA»"
			ko "   ⇒ NON lo spengo.  Cambia porta, o mettiti d'accordo con chi"
			ko "     ce l'ha: spegnerlo troncherebbe la sua misura e la mia"
			ko "     sonda finirebbe a bussare al suo server (§4.4-bis: il ban"
			ko "     e' per INDIRIZZO, e l'indirizzo e' lo stesso per tutti)."
			exit 3 ;;
		esac
	fi
	systemctl stop "$UNITA.service" 2>/dev/null
	systemctl reset-failed "$UNITA.service" 2>/dev/null
	i=0
	while ss -uln 2>/dev/null | grep -q ":$PORTA " && [ $i -lt 50 ]; do i=$((i+1)); sleep 0.2; done
	# ⛔ E se la porta resta occupata da qualcosa che NON e' un'unita' mia, ci si
	#    ferma: legarsi fallirebbe e il server morirebbe senza che nessuno guardi
	#    (la trappola gia' scritta in `riavvia-7700.sh`).
	if ss -uln 2>/dev/null | grep -q ":$PORTA "; then
		ko "⛔ la $PORTA e' ancora occupata da qualcosa che non e' mio: NON parto"
		ss -ulnp 2>/dev/null | grep ":$PORTA " | sed 's/^/        /'
		exit 3
	fi
	mkdir -p "$CERT" "$RILIEVO"; chmod 1777 "$RILIEVO"
	: > "$LOG"

	# ⛔ `--parlantina`: il figlio senza tace IN SILENZIO, e l'assenza di una
	#    riga non e' la prova che il ramo non e' scattato.
	systemd-run \
		--unit="$UNITA" --collect --description="REMOTIX_V2, banco 06-b43 (i tetti)" \
		--working-directory="$D" \
		--setenv=LD_LIBRARY_PATH="$LD_LIBRARY_PATH" \
		--property=StandardOutput=append:"$LOG" \
		--property=StandardError=append:"$LOG" \
		--property=KillMode=mixed \
		--property=LimitRTPRIO=20 \
		--property=LimitNICE=-11 \
		"$D/remotix" \
		--indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
		--certificati "$CERT" --pagina "$D/pagina.html" \
		--ban-file "$BAN" --comando-socket "$SOCK" \
		--rilievo "$RILIEVO" --parlantina "$@" >/dev/null || {
			ko "⛔ systemd-run non e' riuscito"; exit 3; }

	i=0; PID=0
	while [ $i -lt 60 ]; do
		PID=$(systemctl show -p MainPID --value "$UNITA.service" 2>/dev/null || echo 0)
		[ -n "$PID" ] && [ "$PID" != "0" ] && break
		i=$((i+1)); sleep 0.1
	done
	[ "$PID" != "0" ] && [ -n "$PID" ] || {
		ko "⛔ il server non e' partito:"; tail -20 "$LOG" | sed 's/^/        /'; exit 3; }
	ok "acceso, pid $PID, unita' $UNITA.service"

	# ⛔ A6: fuori da ogni sessione utente, o il figlio nascera' senza runtime.
	CG=$(cat "/proc/$PID/cgroup" 2>/dev/null || echo "")
	case "$CG" in
	*user@*|*session-*) ko "⛔⛔ IL SERVER STA DENTRO UNA SESSIONE UTENTE: $CG"; exit 3 ;;
	*) ok "fuori da ogni sessione utente ($CG)" ;;
	esac
	sleep 1
	bash "$0" orologi
	inf "$(vicini)"
	exit 0 ;;

orologi)
	# ⭐ I TETTI IN VIGORE, LETTI DAL PROCESSO CHE GIRA — non dal sorgente.
	if ! grep -q 'i tre orologi in vigore' "$LOG" 2>/dev/null; then
		ko "⛔ il server non ha scritto la riga dei tre orologi: o non e' "
		ko "   partito, o questa versione non la scrive (E1 al contrario)"
		exit 3
	fi
	grep -h 'i tre orologi in vigore' "$LOG" | tail -1 | sed 's/^/    ⭐ /'
	exit 0 ;;

posti)
	# ⛔ I posti si contano da quel che il server SCRIVE, non da quel che
	#    crediamo: ogni presa e ogni rilascio lascia «occupati adesso: N».
	printf 'ULTIMA_RIGA_POSTI %s\n' \
		"$(grep -h 'occupati adesso\|posti occupati adesso' "$LOG" 2>/dev/null | tail -1)"
	printf 'STACCATI_PER_SILENZIO %s\n' \
		"$(grep -c 'STACCATO per silenzio' "$LOG" 2>/dev/null || echo 0)"
	exit 0 ;;

figlio)
	if f=$(mio_figlio); then
		printf 'FIGLIO %s eta=%s\n' "$f" "$(ps -o etimes= -p "$f" 2>/dev/null | tr -d ' ')"
	else
		printf 'FIGLIO nessuno\n'
	fi
	printf 'GNOMESHELL %s\n' "$(pgrep -u "$UID_B" -x gnome-shell | tr '\n' ' ')"
	printf 'CARICO %s\n' "$(uptime | sed 's/.*average: //')"
	exit 0 ;;

registro)
	tail -n "${2:-120}" "$LOG" 2>/dev/null
	exit 0 ;;

registro-cerca)
	grep -n -- "${2:-STACCATO}" "$LOG" 2>/dev/null | tail -n "${3:-60}"
	exit 0 ;;

spegni)
	log "Spengo la $PORTA"
	miei=""
	if pid=$(mio_pid); then
		for f in $(pgrep -P "$pid" 2>/dev/null); do
			[ -r "/proc/$f/cmdline" ] || continue
			case "$(tr '\0' ' ' < /proc/$f/cmdline 2>/dev/null)" in
			*--figlio-interno*) miei="$miei $f" ;;
			esac
		done
	fi
	systemctl stop "$UNITA.service" 2>/dev/null
	systemctl reset-failed "$UNITA.service" 2>/dev/null
	sleep 1
	restano=""
	for f in $miei; do
		[ -r "/proc/$f/cmdline" ] || continue
		case "$(tr '\0' ' ' < /proc/$f/cmdline 2>/dev/null)" in
		*--figlio-interno*) restano="$restano $f" ;;
		esac
	done
	if [ -z "$restano" ]; then ok "spento, nessun figlio MIO orfano"
	else ko "⛔ figli MIEI orfani:$restano"; for f in $restano; do kill -9 "$f" 2>/dev/null; done; fi
	inf "$(vicini)"
	exit 0 ;;

pulisci)
	log "Tolgo il terreno del banco 06-b43"
	bash "$0" spegni
	come_utente gdbus call --session -d org.gnome.SessionManager \
		-o /org/gnome/SessionManager -m org.gnome.SessionManager.Logout 2 \
		>/dev/null 2>&1
	sleep 3
	loginctl disable-linger "$UTENTE" 2>/dev/null
	pkill -u "$UID_B" 2>/dev/null; sleep 2; pkill -9 -u "$UID_B" 2>/dev/null
	ok "sessione di $UTENTE chiusa (l'utente RESTA: lo creano i mandati)"
	inf "$(vicini)"
	exit 0 ;;

stato|*)
	log "Stato — banco 06-b43, porta $PORTA, utente $UTENTE"
	inf "$(vicini)"
	inf "utente: $(id "$UTENTE" 2>&1)"
	inf "gnome-shell: $(pgrep -u "$UID_B" -x gnome-shell | tr '\n' ' ')"
	if pid=$(mio_pid); then inf "server $PORTA: pid $pid"; else inf "server $PORTA: spento"; fi
	if f=$(mio_figlio); then inf "figlio: $f"; else inf "figlio: nessuno"; fi
	inf "registro: $(stat -c %s "$LOG" 2>/dev/null || echo 0) byte"
	grep -h 'i tre orologi in vigore' "$LOG" 2>/dev/null | tail -1 | sed 's/^/    -- /'
	exit 0 ;;
esac
