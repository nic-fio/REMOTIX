#!/bin/bash
#
# 02-figlio-accendi.sh — ⛔ GIRA SUL SERVER (NIC-OS), **FUORI** dal contenitore,
# e **DA ROOT**.  Accende il prodotto di `DECISIONI.md` §1.10-bis sulla **7571**.
#
#   sudo bash /media/REMOTIX/src/02-figlio-accendi.sh stato
#   sudo bash /media/REMOTIX/src/02-figlio-accendi.sh bus
#   sudo bash /media/REMOTIX/src/02-figlio-accendi.sh accendi
#   sudo bash /media/REMOTIX/src/02-figlio-accendi.sh spegni
#   sudo bash /media/REMOTIX/src/02-figlio-accendi.sh riaccendi
#   sudo bash /media/REMOTIX/src/02-figlio-accendi.sh guasto <uid|cieco|via>
#
# ===========================================================================
# ⛔⭐ PERCHE' DA ROOT, ED E' TUTTO IL MANDATO IN UNA RIGA
#
# `02-montaggio-accendi.sh` accende il server come **nicfio** (uid 1000), e lo
# dichiara: *«e' l'uid che possiede il bus di sessione e il socket di
# PipeWire»*.  ⛔ Quel server mostra a chiunque entri il desktop di `nicfio` —
# anche a chi entra come `prova` — perche' il palco e' del PROCESSO.
#
# ⭐ Questo lo accende da **root**, che e' il regime vero: root verifica con PAM
#    la parola di chiunque, e per ogni utente ammesso genera un **figlio** che
#    gira come lui e che il bus ce l'ha.  ⇒ Quel che si vede nella scheda e' il
#    desktop **di chi e' entrato**, e non piu' quello di chi ha acceso.
#
# ⚠ E la conseguenza va detta PRIMA, o si giudica la scena invece del prodotto:
#   entrando come `prova` (uid 1001, che su questa macchina non ha mai fatto
#   login) **non si vede niente**, e non e' un difetto — e' la misura.  `prova`
#   non ha `/run/user/1001`, quindi non ha ne' bus ne' PipeWire, quindi non ha
#   un palco.  ⛔ Il server di prima gli mostrava il desktop di un altro.
#
# ===========================================================================
# ⛔ LA PORTA E' LA 7571, E LE ALTRE TRE NON SI TOCCANO
#
# 7448 (prodotto di casa), 7501 (bersaglio di P5) e ⛔ **7561 (dove l'utente sta
# guardando il proprio desktop)** si CONTANO prima e dopo, e devono restare come
# sono.  ⚠ Ban, socket del comando, certificati e registro sono PROPRI: due
# server che condividessero il file dei ban si bannerebbero a vicenda.
set -uo pipefail

IND=${IND:-192.168.0.2}
PORTA=${PORTA:-7571}
D=${D:-/media/REMOTIX/src/02-figlio-src/src}
LAV=${LAV:-/media/REMOTIX/tmp/02-figlio}
LIBS=${LIBS:-/media/REMOTIX/src/b2/ngtcp2/build/lib:/media/REMOTIX/src/b2/ngtcp2/build/crypto/ossl:/media/REMOTIX/src/b2/prefisso/lib}
# ⛔ La cartella del rilievo la scrive **il figlio**, cioe' l'utente: se fosse
#    di root il rilievo non uscirebbe, e il registro lo direbbe.  Si fa `0777`
#    con lo sticky, come /tmp, invece di indovinare quale utente entrera'.
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

impronta() { sha256sum "$1" 2>/dev/null | cut -c1-16; }

mio_pid()
{
	local p
	if [ -f "$PIDF" ]; then
		p=$(cat "$PIDF" 2>/dev/null)
		[ -n "$p" ] && [ -d "/proc/$p" ] && { echo "$p"; return 0; }
	fi
	p=$(pgrep -f "remotix .*--porta $PORTA" | head -1)
	[ -n "$p" ] && { echo "$p"; return 0; }
	return 1
}

# ⛔ Le tre porte che NON sono mie si contano prima e dopo: se calano, il giro
#    ha fatto un danno, e un danno che nessuno conta non e' successo.
vicini()
{
	local a b c
	a=$(ss -tuln 2>/dev/null | grep -c ':7448\b')
	b=$(ss -tuln 2>/dev/null | grep -c ':7501\b')
	c=$(ss -tuln 2>/dev/null | grep -c ':7561\b')
	printf '7448: %s · 7501: %s · 7561: %s ascoltatori\n' "$a" "$b" "$c"
}

case "${1:-stato}" in
stato)
	log "Il server del figlio, sulla $PORTA"
	inf "$(vicini)"
	if ! pid=$(mio_pid); then
		ko "nessun server sulla $PORTA"
		[ -x "$D/remotix" ] && inf "sul disco: $(impronta "$D/remotix")…"
		exit 1
	fi
	inf "pid $pid, utente $(ps -o user= -p "$pid" 2>/dev/null | tr -d ' ')"
	inf "in esecuzione: $(impronta "/proc/$pid/exe")  ·  sul disco: $(impronta "$D/remotix")"
	log "⭐ I figli vivi adesso (chiesti a /proc, non dedotti)"
	# ⛔ Si cercano per il loro `argv[0]`, che e' `remotix-figlio` e lo scrive
	#    `figli_assicura()`: `pgrep remotix` prenderebbe anche i server degli
	#    altri banchi, e un banco che conta i processi di qualcun altro misura
	#    la macchina, non il prodotto.
	trovati=0
	for f in $(pgrep -P "$pid" 2>/dev/null); do
		riga=$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)
		case "$riga" in
		*--figlio-interno*)
			u=$(awk '/^Uid:/{print $2" "$3" "$4" "$5}' "/proc/$f/status" 2>/dev/null)
			g=$(awk '/^Gid:/{print $2" "$3" "$4" "$5}' "/proc/$f/status" 2>/dev/null)
			inf "figlio pid $f · Uid: $u · Gid: $g · «$riga»"
			trovati=$((trovati+1)) ;;
		esac
	done
	[ "$trovati" -eq 0 ] && inf "nessun figlio (nessuno e' ancora entrato)"
	exit 0 ;;

bus)
	# ⛔⭐ IL CONTROLLO CHE REGGE TUTTO IL MANDATO, RIMISURATO ADESSO.
	#     `P2-6-montaggio.md` §5.4 l'ha misurato una volta; qui si rifa' ogni
	#     giro, perche' una misura di ieri non e' una misura di oggi.
	#     ⭐ E sono DUE: il negativo (root non ci arriva) e il positivo (l'utente
	#     si') — senza il secondo, il primo direbbe solo «gdbus non funziona».
	log "root ⟷ il bus di sessione di uid 1000"
	if sudo -n env XDG_RUNTIME_DIR=/run/user/1000 \
	        DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
	        gdbus call --session --dest org.freedesktop.DBus \
	        --object-path /org/freedesktop/DBus \
	        --method org.freedesktop.DBus.GetId >/dev/null 2>&1; then
		ko "⛔ root CI ARRIVA: la misura su cui poggia §1.10-bis non regge piu'"
		ko "   su questa macchina.  ⚠ Non e' un rosso del prodotto: e' un fatto"
		ko "   del sistema che va riportato al coordinatore."
		esito_bus=1
	else
		ok "⛔ root NON si collega al bus di sessione di uid 1000 (atteso)"
		esito_bus=0
	fi
	log "uid 1000 ⟷ lo stesso bus — il controllo POSITIVO"
	if setpriv --reuid=1000 --regid=1000 --init-groups \
	        env XDG_RUNTIME_DIR=/run/user/1000 \
	        DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/1000/bus \
	        gdbus call --session --dest org.freedesktop.DBus \
	        --object-path /org/freedesktop/DBus \
	        --method org.freedesktop.DBus.GetId >/dev/null 2>&1; then
		ok "⭐ uid 1000 CI ARRIVA: lo strumento sa trovare un bus che c'e'"
	else
		ko "⛔ nemmeno uid 1000 ci arriva: lo strumento non sa vedere quel che"
		ko "   c'e' di sicuro, quindi il «no» di root qui sopra non prova niente"
		esito_bus=2
	fi
	exit "$esito_bus" ;;

spegni)
	log "Spengo"
	inf "$(vicini)"
	if ! pid=$(mio_pid); then ok "non c'era niente acceso sulla $PORTA"; exit 0; fi
	# ⛔ Si contano i figli PRIMA di spegnere, per poter dire dopo se sono
	#    morti con lui: «il padre e' spento» e «i figli sono spenti» sono due
	#    fatti diversi, e il secondo e' quello che conta (nessun orfano
	#    attaccato al monitor virtuale di un utente).
	#
	# ⛔⛔ E SI PRENDONO I **PID**, NON IL LORO NUMERO — cura del 13 agosto 2026.
	#
	#    La riga di prima contava, dopo lo spegnimento,
	#    `pgrep -f -- "--figlio-interno" | wc -l`: cioe' **i figli di TUTTI**.
	#    ⇒ due difetti in una riga sola, opposti fra loro:
	#      · un altro banco con un figlio vivo faceva uscire questo ROSSO con
	#        zero orfani propri — un'accusa al prodotto che era del vicino;
	#      · e non sapeva dire se l'orfano fosse suo, quindi nemmeno il rosso
	#        vero avrebbe detto di chi era.
	#    ⚠ E si accende **solo quando due banchi girano in parallelo**, che e'
	#      quel che la fase 3 fa di mestiere: fino a ieri era un difetto
	#      addormentato.
	#
	#    ⭐ La cura non e' un `pgrep` piu' furbo — un filtro sulla riga di
	#      comando resterebbe una deduzione.  Si CHIEDE al nucleo chi sono i
	#      propri figli **prima** di uccidere il padre, si tiene l'elenco dei
	#      pid, e dopo si guarda **quell'elenco** (`LEZIONI.md` §1.6: non si
	#      deduce, si chiede).
	#    ⚠ Un pid puo' essere riciclato dal nucleo fra il prima e il dopo: per
	#      questo non basta che `/proc/$f` esista — si ricontrolla che la riga
	#      di comando sia ancora quella di un figlio nostro.
	miei_figli=""
	prima=0
	for f in $(pgrep -P "$pid" 2>/dev/null); do
		riga=$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)
		case "$riga" in
		*--figlio-interno*) miei_figli="$miei_figli $f"; prima=$((prima+1)) ;;
		esac
	done
	kill "$pid" 2>/dev/null
	g=0
	while [ -d "/proc/$pid" ] && [ "$g" -lt 30 ]; do sleep 0.5; g=$((g+1)); done
	[ -d "/proc/$pid" ] && { ko "il pid $pid non e' morto"; exit 3; }
	rm -f "$PIDF"

	restano=0
	orfani=""
	for f in $miei_figli; do
		riga=$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null) || continue
		case "$riga" in
		*--figlio-interno*) restano=$((restano+1)); orfani="$orfani $f" ;;
		esac
	done
	ok "spento (pid $pid, aveva $prima figli MIEI)"
	if [ "$restano" -eq 0 ]; then
		ok "⭐ e NESSUN figlio MIO e' rimasto orfano"
	else
		ko "⛔ $restano figli MIEI sono ancora vivi:$orfani — sono orfani"
		ko "   attaccati al monitor virtuale di qualcuno"
		for f in $orfani; do
			printf '        %s  %s\n' "$f" "$(tr '\0' ' ' < "/proc/$f/cmdline" 2>/dev/null)"
		done
	fi
	# ⚠ I figli DEGLI ALTRI si contano lo stesso, e si stampano come contorno:
	#   servono a capire la macchina, e ⛔ NON entrano nel verdetto.  Confonderli
	#   con i propri e' esattamente il difetto curato qui sopra.
	altrui=$(( $(pgrep -f -- "--figlio-interno" 2>/dev/null | wc -l) ))
	inf "sulla macchina restano $altrui processi «--figlio-interno» in tutto"\
	    "(miei: $restano · di altri banchi: $((altrui - restano))) — ⚠ contorno, non verdetto"
	inf "$(vicini)"
	[ "$restano" -eq 0 ] || exit 4
	exit 0 ;;

guasto)
	# ⛔⭐ IL GUASTO E' UN FIGLIO CHE GIRA COME L'UTENTE SBAGLIATO, e si innesta
	#     nella COPIA dei sorgenti, mai nel prodotto di casa.  ⭐ Si risana
	#     ricopiando i sorgenti veri (`02-figlio-lancia.sh porta`).
	#
	#     Sono DUE, e vanno insieme, perche' i muri sono due e indipendenti:
	#
	#       `uid`    salta il `setuid()`: il figlio resta root.  ⛔ Deve
	#                accorgersene DA SE' — `getresuid()` dopo l'`exec` — e
	#                uscire 42 senza toccare niente;
	#       `cieco`  salta il `setuid()` **e** il controllo del figlio.  ⛔ Qui
	#                l'unico muro che resta e' il PADRE, che legge le
	#                credenziali timbrate dal nucleo su ogni messaggio e
	#                abbatte il figlio.  ⚠ Senza questo secondo caso, «il padre
	#                controlla a ogni messaggio» sarebbe una riga di codice che
	#                nessuno ha mai visto mordere.
	F=$D/figlio.c
	case "${2:-}" in
	uid)
		log "Innesto: il figlio NON scende all'utente"
		sed -i 's|^\tif (setuid(pw->pw_uid) != 0)$|\tif (0 \&\& setuid(pw->pw_uid) != 0) /* GUASTO INNESTATO */|' "$F" \
			&& grep -q 'GUASTO INNESTATO' "$F" \
			&& { ok "innestato in $F"; exit 0; }
		ko "⛔ il guasto NON si e' innestato: la riga non e' quella che credevo."
		ko "   ⚠ Un guasto che non si innesta e un banco verde hanno la stessa"
		ko "   faccia, e questo esce 2 invece di far credere di aver misurato."
		exit 2 ;;
	cieco)
		log "Innesto: il figlio non scende E non se ne accorge"
		# ⛔ Due sed, e ciascuno su UNA riga sola: un guasto che deve rompere un
		#    `if` su due righe si innesta a meta' e non compila — e «non
		#    compila» e «il guasto non morde» hanno la stessa faccia per chi
		#    guarda solo lo stato d'uscita.
		sed -i 's|^\tif (setuid(pw->pw_uid) != 0)$|\tif (0 \&\& setuid(pw->pw_uid) != 0) /* GUASTO INNESTATO */|' "$F"
		# ⛔ E SONO TRE, non uno: lo stesso controllo (`getresuid`) vive PRIMA
		#    dell'`exec` (uscite 35 e 36) e DOPO (uscita 42).  ⚠ Togliendone uno
		#    solo, il figlio si ferma comunque al primo — e il muro del PADRE,
		#    che e' quello che questo caso esiste per provare, non morde mai.
		#    `[M]` 12 agosto 2026: e' precisamente quel che e' successo al primo
		#    giro, e il caso sarebbe stato «verde» senza aver provato niente.
		sed -i 's|^\t\t_exit(35);$|\t\t(void)0; /* GUASTO CIECO: prima dell'"'"'exec */|' "$F"
		sed -i 's|^\t\t_exit(36);$|\t\t(void)0; /* GUASTO CIECO: prima dell'"'"'exec */|' "$F"
		sed -i 's|^\t\t_exit(42);$|\t\t(void)0; /* GUASTO CIECO: dopo l'"'"'exec */|' "$F"
		if grep -q 'GUASTO INNESTATO' "$F" && [ "$(grep -c 'GUASTO CIECO' "$F")" -eq 3 ]; then
			ok "innestati tutt'e due in $F"
			grep -n 'GUASTO' "$F" | sed 's/^/        /'
			exit 0
		fi
		ko "⛔ i quattro guasti non si sono innestati tutti: esco 2, non verde"
		exit 2 ;;
	via)
		if grep -q 'GUASTO' "$F"; then
			ko "⛔ ci sono ancora guasti in $F: si risana ricopiando i sorgenti"
			grep -n 'GUASTO' "$F" | sed 's/^/        /'
			exit 1
		fi
		ok "nessun guasto in $F"
		exit 0 ;;
	*) echo "uso: $0 guasto <uid|cieco|via>"; exit 2 ;;
	esac ;;

accendi) ;;
riaccendi) bash "$0" spegni || exit 3 ;;
*) echo "uso: $0 [stato|bus|accendi|spegni|riaccendi|guasto ...]"; exit 2 ;;
esac

# --- accendi ---------------------------------------------------------------
log "0. Il terreno, dichiarato prima di toccarlo"
inf "$(vicini)"
[ "$(id -u)" -eq 0 ] || { ko "⛔ questo va lanciato DA ROOT: e' tutto il punto"; exit 2; }
[ -x "$D/remotix" ] || { ko "⛔ $D/remotix non c'e'"; exit 2; }
[ -f "$D/pagina.html" ] || { ko "⛔ $D/pagina.html non c'e'"; exit 2; }
inf "binario: $D/remotix  ($(impronta "$D/remotix")…)"
if grep -q 'GUASTO' "$D/figlio.c" 2>/dev/null; then
	inf "⚠ ATTENZIONE: nei sorgenti c'e' un GUASTO innestato —"
	grep -n 'GUASTO' "$D/figlio.c" | sed 's/^/        /'
fi

command -v ss >/dev/null || { ko "⛔ «ss» non c'e': non ho guardato la porta"; exit 2; }
n=$(ss -tuln 2>/dev/null | grep -c ":$PORTA\b")
[ "$n" -eq 0 ] || { ko "⛔ la porta $PORTA e' gia' occupata ($n righe)"; exit 2; }

mkdir -p "$CERT" "$RILIEVO" || { ko "⛔ non ho potuto preparare $LAV"; exit 2; }
chmod 1777 "$RILIEVO"
inf "il rilievo e' $RILIEVO, modo 1777: ci scrive IL FIGLIO, cioe' l'utente"

log "1. Le librerie: quelle costruite, non quelle dei pacchetti"
export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
if ! ldd "$D/remotix" > "$LAV/ldd.txt" 2>&1; then
	ko "⛔ ldd non ha finito: non dico che le librerie ci sono"; exit 2
fi
grep -q 'not found' "$LAV/ldd.txt" && { ko "⛔ manca una libreria:";
	grep 'not found' "$LAV/ldd.txt" | sed 's/^/        /'; exit 2; }
for l in libngtcp2 libnghttp3; do
	riga=$(grep -m1 "$l" "$LAV/ldd.txt")
	case "$riga" in
	*/media/REMOTIX/src/b2/*) ok "$l ← $(printf '%s' "$riga" | sed 's/^[[:space:]]*//')" ;;
	*)  ko "⛔ $l NON viene dall'albero costruito: stesso soname, altra libreria"
	    exit 2 ;;
	esac
done

log "2. Il servizio PAM sull'host"
[ -f /etc/pam.d/remotix ] || { ko "⛔ /etc/pam.d/remotix NON C'E': PAM ripiega su"
	ko "   «other» = pam_deny, e OGNI parola giusta sara' rifiutata"; exit 2; }
ok "/etc/pam.d/remotix c'e'"

log "3. Il palco che i figli troveranno — e di CHI e'"
for u in 1000 1001; do
	if [ -S "/run/user/$u/bus" ]; then
		ok "uid $u: /run/user/$u/bus c'e' — un figlio a questo uid avra' il bus"
	else
		inf "⚠ uid $u: /run/user/$u/bus NON c'e' — un figlio a questo uid"
		inf "   nascera', lo DIRA', e restera' senza palco (non e' un difetto:"
		inf "   e' un utente che non ha mai fatto login su questa macchina)"
	fi
done

log "4. Accendo — DA ROOT, sulla $PORTA"
# ⛔ Il registro si apre IN CODA, mai troncato.
# ⛔ `--parlantina` acceso: il ricontrollo periodico dell'identita' dei figli
#    scrive li', e senza non si vedrebbe (`figlio.h`, `figli_ricontrolla`).
nohup "$D/remotix" --indirizzo 0.0.0.0 --nome "$IND" --porta "$PORTA" \
      --certificati "$CERT" --pagina "$D/pagina.html" \
      --ban-file "$BAN" --comando-socket "$SOCK" \
      --rilievo "$RILIEVO" --parlantina \
      >> "$LOG" 2>&1 &
pid=$!
echo "$pid" > "$PIDF"

# ⛔ Marcatori, non `sleep`.  ⚠ E qui l'accensione e' PIU' VELOCE di quella del
#   montaggio: il padre non cattura piu' niente (§1.10-bis), quindi non aspetta
#   ne' i 5 s della cattura ne' le due codifiche.
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

log "5. Che cosa ha detto all'avvio — e questa e' la misura, non l'accensione"
grep -E '^[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3} (avvio|figlio|video) ' "$LOG" \
	| tail -12 | sed 's/^/        /'
inf "$(vicini)"
exec bash "$0" stato
