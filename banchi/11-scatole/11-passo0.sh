#!/bin/bash
# ===========================================================================
# 11-passo0.sh — ⛔⛔ IL PASSO 0 DELLA FASE 11
#
#   «Dentro un contenitore, il pezzo di sistema che tiene il conto di chi e'
#    collegato si comporta come sulla macchina vera?»
#
#   Si esegue DENTRO la scatola, da amministratore:
#       podman exec -it rete11-gnome bash /passo0/11-passo0.sh
# ===========================================================================
#
# ⛔ PERCHE' ESISTE, e perche' viene PRIMA di qualunque scatola definitiva
#
# Il prodotto si appoggia parecchio a `systemd`/`logind`: il linger, la
# sessione d'utente, il guardiano che chiude le sessioni morte.  Se qui dentro
# quel pezzo si comporta diversamente, ⛔ **l'intero strato dei contenitori
# diventa un simulacro** — cioe' la peggiore forma di sicurezza, quella falsa.
#
# ⇒ Su questo convergono TUTT'E DUE i revisori esterni del 25 agosto 2026, ed e'
#   il rilievo piu' grave dei due giri.  `fasi/11-la-rete-di-sicurezza.md` §3.5.
#
# ---------------------------------------------------------------------------
# ⚠⚠ QUEL CHE QUESTO BANCO **NON** E', e va letto prima dei suoi esiti
#
# ⛔ **Non prova il prodotto.**  Prova l'AMBIENTE.  Il prodotto non e' ancora
#    in questa scatola, e non serve che ci sia: la domanda del passo 0 e' se la
#    scatola sappia ospitare le condizioni in cui il prodotto vive.
#
# ⛔ E in particolare, il punto 7 accende il compositore con `--virtual-monitor`,
#    ⚠ che e' **il contrario** di come lo accende il prodotto (`sessione.c:735`,
#    dove quella riga e' stata TOLTA il 14 agosto 2026 con una misura sotto).
#    ⇒ Qui serve a chiedere *«un compositore Wayland riesce a vivere in questa
#      scatola e a servire un cliente?»*.  ⛔ **Non** a chiedere *«la sessione di
#      REMOTIX nasce col monitor?»*, che e' la domanda del collaudo A e vuole il
#      prodotto dentro.  Confondere le due sarebbe rispondere a quella comoda.
#
# ---------------------------------------------------------------------------
# GLI ESITI — la regola di §4.5 del documento di fase
#
#   0  ⭐ ho guardato, e la scatola regge
#   1  ho guardato, e la scatola NON regge          ⇒ il disegno va cambiato
#   3  ⛔ NON HO POTUTO GUARDARE — e non e' un rosso
#
# ⛔ «Non ho potuto guardare» e «e' rotto» non hanno la stessa faccia, e non
#    devono averla: `LEZIONI.md` §1.9, e la regola «None non e' zero».
# ===========================================================================
set -uo pipefail

UTENTE=provanic
UID_UTENTE=4011
VERDE=0; ROSSO=0; NONSO=0

blu()  { printf '\n\033[1;34m=== %s\033[0m\n' "$*"; }
si()   { printf '  \033[1;32mSI \033[0m %s\n' "$*"; VERDE=$((VERDE+1)); }
no()   { printf '  \033[1;31mNO \033[0m %s\n' "$*"; ROSSO=$((ROSSO+1)); }
boh()  { printf '  \033[1;33m?  \033[0m %s\n' "$*"; NONSO=$((NONSO+1)); }
nota() { printf '       %s\n' "$*"; }

come_lui() { runuser -u "$UTENTE" -- "$@"; }

# ---------------------------------------------------------------------------
# ⭐⭐ L'ADATTATORE — la risposta a «come si resta ciechi al desktop»
#
# Questo banco non sa che desktop ha davanti, e non deve saperlo.  Ogni scatola
# porta allo STESSO percorso un file che dice come si avvia il suo compositore.
# ⇒ La lista delle prove resta UNA; il «come» sta sotto (`fasi/11…` §3.7).
# ---------------------------------------------------------------------------
ADATTATORE=/usr/local/lib/rete11/adattatore.sh
if [ -r "$ADATTATORE" ]; then
	. "$ADATTATORE"
	DESK=$(adattatore_nome)
else
	DESK="(nessun adattatore: $ADATTATORE non c'e')"
fi

printf '\033[1m PASSO 0 — la scatola regge il sistema?\033[0m\n'
printf ' desktop: %s\n' "$DESK"
printf ' scatola: %s · nucleo: %s · %s\n' \
       "$(. /etc/os-release 2>/dev/null; echo "${PRETTY_NAME:-ignota}")" \
       "$(uname -r)" "$(date -u '+%Y-%m-%d %H:%M:%S UTC')"

# ---------------------------------------------------------------------------
blu "0. Il primo processo e' «systemd»?  (se no, il resto non ha senso)"
# ---------------------------------------------------------------------------
PRIMO=$(ps -p 1 -o comm= 2>/dev/null || echo '')
if [ "$PRIMO" = "systemd" ]; then
	si "il processo 1 e' systemd"
else
	no "il processo 1 e' «$PRIMO»: questa scatola non puo' rispondere alla domanda"
	nota "⇒ mi fermo: senza systemd i punti 1-6 non sono nemmeno ponibili"
	exit 1
fi

# ⛔ `is-system-running` ESCE 1 quando lo stato e' «degraded», e con `pipefail`
#    l'`if` lo leggeva come «non lo so».  ⇒ Si cattura il TESTO e si giudica
#    quello: lo stato d'uscita qui non e' il giudizio, e' un dettaglio.
#    `[M]` 25 agosto 2026, difetto di questo banco al primo giro.
STATO_SIS=$(systemctl is-system-running 2>&1 | head -1)
case "$STATO_SIS" in
  running)
	si "il sistema e' partito (running)" ;;
  degraded)
	si "il sistema e' partito, con unita' fallite (degraded)"
	nota "⚠ le unita' fallite, che vanno guardate una per una:"
	systemctl --failed --no-legend --plain 2>/dev/null | head -8 | sed 's/^/       ⚠ /' ;;
  starting)
	boh "il sistema sta ancora partendo: troppo presto per giudicare" ;;
  *)
	boh "stato non leggibile: $STATO_SIS" ;;
esac

# ---------------------------------------------------------------------------
blu "1. La sessione d'utente ESISTE, ed e' di un tipo che il prodotto riconosce?"
# ---------------------------------------------------------------------------
if ! command -v loginctl >/dev/null 2>&1; then
	boh "«loginctl» non c'e' nella scatola: non posso guardare"
elif ! systemctl is-active systemd-logind >/dev/null 2>&1; then
	no "systemd-logind NON e' attivo: $(systemctl is-active systemd-logind 2>&1)"
	nota "⇒ e' proprio il pezzo su cui il prodotto si appoggia"
	systemctl status systemd-logind --no-pager -l 2>&1 | tail -6 | sed 's/^/       /'
else
	si "systemd-logind e' attivo"
	# ⛔⛔ E QUI SI PREPARA PRIMA DI GUARDARE, perche' e' quel che fa il PRODOTTO.
	#     Al primo giro questo punto giudicava mentre il gestore d'utente era
	#     ancora «activating», e dava un rosso che diceva «la scatola non regge»
	#     quando la verita' era «non avevo ancora chiesto niente».
	#     ⇒ `[M]` 25 agosto 2026, secondo difetto di questo banco.
	#     ⚠ Preparare non e' barare: il prodotto accende il linger e avvia il
	#       gestore d'utente da se'.  Barare sarebbe **saltare** la verifica.
	loginctl enable-linger "$UTENTE" 2>/dev/null
	systemctl start "user@${UID_UTENTE}.service" 2>/dev/null
	for _ in $(seq 1 30); do
		loginctl show-user "$UTENTE" >/dev/null 2>&1 && break
		sleep 0.5
	done
	# ⛔ Non basta che il servizio giri: deve saper APRIRE una sessione.
	#    Si prova ad aprirne una vera con un login non interattivo.
	if come_lui true 2>/dev/null; then
		SES=$(loginctl list-sessions --no-legend 2>/dev/null | wc -l)
		nota "sessioni aperte adesso: $SES"
		if loginctl show-user "$UTENTE" >/dev/null 2>&1; then
			si "logind conosce l'utente «$UTENTE»"
			loginctl show-user "$UTENTE" -p State -p Linger -p RuntimePath 2>/dev/null \
				| sed 's/^/       /'
		else
			no "logind NON conosce l'utente «$UTENTE»: $(loginctl show-user "$UTENTE" 2>&1 | head -1)"
			nota "⛔ e' questo il punto in cui la scatola smette di rappresentare il prodotto"
		fi
	else
		boh "non riesco nemmeno a eseguire un comando come «$UTENTE»"
	fi
fi

# ---------------------------------------------------------------------------
blu "2. Il LINGER: i servizi dell'utente vivono senza che nessuno abbia fatto login?"
# ---------------------------------------------------------------------------
if loginctl enable-linger "$UTENTE" 2>/dev/null; then
	if [ "$(loginctl show-user "$UTENTE" -p Linger --value 2>/dev/null)" = "yes" ]; then
		si "il linger si accende e resta acceso"
	else
		no "il comando passa ma il linger NON risulta acceso"
	fi
else
	no "non si riesce ad accendere il linger: $(loginctl enable-linger "$UTENTE" 2>&1 | head -1)"
	nota "⛔ senza linger la sessione grafica non sopravvive al distacco del client"
fi

if systemctl is-active "user@${UID_UTENTE}.service" >/dev/null 2>&1; then
	si "il gestore d'utente («user@${UID_UTENTE}») e' vivo senza nessun login interattivo"
else
	STATO=$(systemctl is-active "user@${UID_UTENTE}.service" 2>&1)
	if systemctl start "user@${UID_UTENTE}.service" 2>/dev/null; then
		si "il gestore d'utente si avvia a richiesta (era «$STATO»)"
	else
		no "il gestore d'utente non parte: era «$STATO»"
		systemctl status "user@${UID_UTENTE}.service" --no-pager -l 2>&1 | tail -6 | sed 's/^/       /'
	fi
fi

# ---------------------------------------------------------------------------
blu "3. Dentro la sessione d'utente si riesce a far partire un servizio?"
# ---------------------------------------------------------------------------
# ⚠ Il prodotto parte cosi': un'unita' d'utente, non un processo staccato.
#   Qui si prova il MECCANISMO con un'unita' finta, perche' il prodotto in
#   questa scatola non c'e' ancora.
if come_lui env XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
        systemd-run --user --quiet --unit=passo0-prova \
        --property=Type=oneshot /bin/true 2>/dev/null; then
	si "un'unita' d'utente si avvia da dentro la sessione"
	come_lui env XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
	        systemctl --user reset-failed passo0-prova 2>/dev/null || true
else
	no "non si riesce ad avviare un'unita' d'utente"
	nota "⛔ e' il modo in cui il prodotto avvia la sessione grafica"
	come_lui env XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
	        systemd-run --user --unit=passo0-prova --property=Type=oneshot /bin/true 2>&1 \
	        | tail -4 | sed 's/^/       /'
fi

# ---------------------------------------------------------------------------
blu "4. Quando la sessione finisce, i processi MUOIONO davvero?"
# ---------------------------------------------------------------------------
# ⛔ La forma del guasto che si teme: un contenitore in cui i processi restano
#    vivi dopo la chiusura ⇒ la prova C7 («non resta niente») sarebbe verde qui
#    e rossa sulla macchina vera, o viceversa.
if come_lui env XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
        systemd-run --user --quiet --unit=passo0-dorme sleep 300 2>/dev/null; then
	sleep 1
	PID=$(pgrep -u "$UTENTE" -f 'slee[p] 300' | head -1)
	if [ -n "$PID" ]; then
		nota "il figlio finto e' vivo (pid $PID); ora si chiude la sessione dell'utente"
		loginctl terminate-user "$UTENTE" 2>/dev/null || \
			come_lui env XDG_RUNTIME_DIR="/run/user/$UID_UTENTE" \
			        systemctl --user stop passo0-dorme 2>/dev/null
		sleep 2
		if pgrep -u "$UTENTE" -f 'slee[p] 300' >/dev/null 2>&1; then
			no "il figlio e' SOPRAVVISSUTO alla chiusura della sessione"
			nota "⛔ qui la scatola si comporta diversamente dalla macchina vera"
		else
			si "il figlio e' morto con la sessione, e non e' restato niente"
		fi
	else
		boh "non ho visto nascere il figlio finto: non posso giudicare"
	fi
else
	boh "non sono riuscito ad avviare il figlio finto: non posso giudicare"
fi

# ---------------------------------------------------------------------------
# ⛔⛔ E ADESSO SI RIMETTE IN PIEDI QUEL CHE IL PUNTO 4 HA APPENA BUTTATO GIU'.
#
# `[M]` 25 agosto 2026, primo giro vero di questo banco — ⭐ e il difetto era
# del BANCO, non della scatola.  Il punto 4 chiude la sessione dell'utente per
# vedere se i figli muoiono; ⛔ chiudendola porta via anche `/run/user/4011`,
# e i punti 5, 6 e 7 — che vengono dopo — trovavano il campo sgombro e davano
# **TRE ROSSI FALSI**.
#
# ⚠ E' la forma di §1.29 girata al contrario: non «silenzio invece di rosso»,
#   ma **rosso invece di niente** — e costa uguale, perche' una rete che da'
#   rossi a vuoto viene spenta da chi lavora (`fasi/11…` §4.3).
#
# ⇒ Chi prova la chiusura ha il dovere di RIAPRIRE, e di verificare che la
#   riapertura sia riuscita prima di lasciar giudicare gli altri.
# ---------------------------------------------------------------------------
loginctl enable-linger "$UTENTE" 2>/dev/null
systemctl start "user@${UID_UTENTE}.service" 2>/dev/null
RIPRESO=0
for _ in $(seq 1 30); do
	if [ -S "/run/user/$UID_UTENTE/bus" ]; then RIPRESO=1; break; fi
	sleep 0.5
done
if [ "$RIPRESO" = 1 ]; then
	nota "⭐ sessione rimessa in piedi dopo la prova della chiusura"
else
	boh "⛔ NON sono riuscito a rimettere in piedi la sessione dopo il punto 4"
	nota "⚠ i punti 5, 6 e 7 qui sotto girerebbero sul campo sgombro: NON li giudico"
	printf '\n  \033[1;33mmi fermo qui\033[0m — meglio «non lo so» che tre rossi falsi.\n'
	exit 3
fi

# ---------------------------------------------------------------------------
blu "5. La cartella privata dell'utente c'e', e' SUA, ed e' scrivibile?"
# ---------------------------------------------------------------------------
RTD="/run/user/$UID_UTENTE"
if [ -d "$RTD" ]; then
	PROP=$(stat -c '%U %a' "$RTD" 2>/dev/null)
	if come_lui test -w "$RTD"; then
		si "$RTD esiste, e' scrivibile dall'utente ($PROP)"
	else
		no "$RTD esiste ma l'utente NON ci puo' scrivere ($PROP)"
	fi
	# ⛔ E non dev'essere la stessa di un'altra scatola: si guarda che sia un
	#    montaggio DI QUESTO contenitore, non un pezzo dell'ospite passato dentro.
	# ⚠ `findmnt` qui dentro torna vuoto (il montaggio lo ha fatto logind dopo
	#   l'avvio del contenitore, e la tabella che vede non lo elenca): si chiede
	#   il TIPO al kernel, che risponde sempre.  `[M]` 25 agosto 2026.
	TIPO_RTD=$(stat -fc %T "$RTD" 2>/dev/null)
	if [ "$TIPO_RTD" = tmpfs ]; then
		si "ed e' una cartella di questa scatola (tmpfs), non un pezzo dell'ospite"
	else
		no "NON e' una tmpfs di questa scatola, e' «$TIPO_RTD»"
		nota "⛔ due scatole che condividessero questa cartella si pesterebbero i piedi"
	fi
else
	no "$RTD non esiste: senza, nessun socket di sessione nasce"
fi

# ---------------------------------------------------------------------------
blu "6. Il canale di messaggi della sessione c'e', e il desktop lo vede?"
# ---------------------------------------------------------------------------
if [ -S "$RTD/bus" ]; then
	si "il canale della sessione c'e' ($RTD/bus)"
	if come_lui env XDG_RUNTIME_DIR="$RTD" \
	        DBUS_SESSION_BUS_ADDRESS="unix:path=$RTD/bus" \
	        busctl --user list --no-legend >/dev/null 2>&1; then
		si "e ci si riesce a parlare"
	else
		no "c'e' il socket ma non risponde"
	fi
else
	no "il canale della sessione NON c'e' ($RTD/bus)"
	nota "⛔ senza, gnome-session non parte e il prodotto non ha con chi parlare"
fi

# ---------------------------------------------------------------------------
blu "7. Un compositore Wayland vive qui dentro, e serve un cliente?"
# ---------------------------------------------------------------------------
# ⚠⚠ Vedi il riquadro in testa: qui si usa `--virtual-monitor`, che il prodotto
#    NON usa.  La domanda e' sull'AMBIENTE, non sul prodotto.
if ! command -v adattatore_avvia >/dev/null 2>&1 && ! type adattatore_avvia >/dev/null 2>&1; then
	boh "non c'e' l'adattatore di questa scatola: non so come si avvia il compositore"
else
	rm -f /tmp/passo0-shell.log
	SHELLPID=$(adattatore_avvia "$RTD" /tmp/passo0-shell.log)
	# Si aspetta il socket, non un tempo fisso: un'attesa a orologio e' una
	# scadenza che scatta quando capita (`LEZIONI.md`, la regola del battito).
	SOCK=''
	for _ in $(seq 1 40); do
		SOCK=$(come_lui sh -c "ls $RTD/wayland-* 2>/dev/null | grep -v lock | head -1" 2>/dev/null)
		[ -n "$SOCK" ] && break
		sleep 0.5
	done
	if [ -z "$SOCK" ]; then
		no "il compositore non ha aperto nessun socket in 20 s"
		tail -12 /tmp/passo0-shell.log 2>/dev/null | sed 's/^/       /'
	else
		si "il compositore e' vivo e ha aperto $(basename "$SOCK")"
		DISP=$(basename "$SOCK")
		# ⭐ IL METRO DEL GUASTO DEL 25 AGOSTO: quante uscite ANNUNCIA.
		if command -v wayland-info >/dev/null 2>&1; then
			USCITE=$(come_lui env XDG_RUNTIME_DIR="$RTD" WAYLAND_DISPLAY="$DISP" \
			        wayland-info 2>/dev/null | grep -c 'interface:.*wl_output' || echo 0)
			if [ "${USCITE:-0}" -gt 0 ]; then
				si "e ANNUNCIA $USCITE uscita/e — un cliente puo' aprire una finestra"
			else
				no "⛔ ANNUNCIA ZERO uscite: e' la forma del guasto del 25 agosto"
				nota "⚠ qui pero' il monitor gliel'ho chiesto io: se e' zero, e' della scatola"
			fi
		else
			boh "«wayland-info» non c'e': non posso contare le uscite"
		fi
		# Un cliente vero che disegna.
		if command -v weston-simple-shm >/dev/null 2>&1; then
			come_lui env XDG_RUNTIME_DIR="$RTD" WAYLAND_DISPLAY="$DISP" \
			        weston-simple-shm >/tmp/passo0-cliente.log 2>&1 &
			CLPID=$!
			sleep 3
			if kill -0 "$CLPID" 2>/dev/null; then
				si "un cliente Wayland vero si e' attaccato e sta disegnando"
				kill "$CLPID" 2>/dev/null
			else
				no "il cliente Wayland e' morto subito"
				tail -6 /tmp/passo0-cliente.log 2>/dev/null | sed 's/^/       /'
			fi
		else
			boh "non ho un cliente Wayland minimo nella scatola"
		fi
	fi
	kill "$SHELLPID" 2>/dev/null
	wait "$SHELLPID" 2>/dev/null
fi

# ---------------------------------------------------------------------------
blu "8. La scheda grafica e il codificatore in hardware si raggiungono?"
# ---------------------------------------------------------------------------
if [ ! -e /dev/dri/renderD128 ]; then
	no "/dev/dri/renderD128 non e' nella scatola: la scheda non e' entrata"
else
	si "/dev/dri/renderD128 c'e'"
	if come_lui test -r /dev/dri/renderD128 && come_lui test -w /dev/dri/renderD128; then
		si "e l'utente ci puo' leggere e scrivere"
	else
		no "c'e' ma l'utente NON ci puo' scrivere ($(stat -c '%U:%G %a' /dev/dri/renderD128))"
		nota "⛔ e' il gruppo «render»: senza, si codifica in software e i numeri cambiano"
	fi
	if command -v vainfo >/dev/null 2>&1; then
		VA=$(come_lui env LIBVA_DRIVER_NAME=iHD vainfo --display drm --device /dev/dri/renderD128 2>&1)
		if echo "$VA" | grep -q 'VAProfileH264'; then
			si "il codificatore in hardware risponde ($(echo "$VA" | grep -m1 'Driver version' | sed 's/^ *//'))"
			nota "profili di codifica H.264 trovati: $(echo "$VA" | grep -c 'VAProfileH264.*Enc')"
		else
			no "il codificatore in hardware non risponde"
			echo "$VA" | tail -6 | sed 's/^/       /'
		fi
	else
		boh "«vainfo» non c'e' nella scatola"
	fi
fi

# ---------------------------------------------------------------------------
printf '\n\033[1m=========================  IL VERDETTO  =========================\033[0m\n'
printf '  regge: %d   non regge: %d   non ho potuto guardare: %d\n' "$VERDE" "$ROSSO" "$NONSO"
if [ "$ROSSO" -gt 0 ]; then
	printf '  \033[1;31m⛔ LA SCATOLA NON REGGE\033[0m — le prove che dipendono da quel che\n'
	printf '     non regge restano sulla macchina vera, e si scrive quali.\n'
	exit 1
elif [ "$NONSO" -gt 0 ]; then
	printf '  \033[1;33m⚠ NON GIUDICO\033[0m — %d cose non le ho potute guardare.\n' "$NONSO"
	printf '     %s\n' "⛔ E questo NON e un verde: e un esito suo (§4.5)."
	exit 3
else
	printf '  \033[1;32m⭐ LA SCATOLA REGGE\033[0m su tutti i punti che il prodotto usa.\n'
	exit 0
fi
