#!/usr/bin/env bash
# ===========================================================================
# 09-b82-mostra — FA COMPARIRE UNA FINESTRA SULLO SCHERMO CHE REMOTIX CATTURA,
#                 e poi **lo verifica** invece di dichiararlo.
#
#   sudo bash 09-b82-mostra.sh <utente> <comando...>
#   sudo bash 09-b82-mostra.sh --stato  <utente>
#   sudo bash 09-b82-mostra.sh --ferma  <utente> [unita']
#
#   sudo bash 09-b82-mostra.sh provanr7 mpv --fullscreen --loop /qualche/film.mp4
#
# ---------------------------------------------------------------------------
# ⛔⭐⭐ PERCHE' ESISTE — 24 agosto 2026, e il difetto che cura non e' tecnico.
#
# Per tre volte in due giorni un banco si e' fermato su «l'applicazione parte e
# resta viva, ma il desktop catturato non cambia».  ⛔ E ogni volta il verdetto
# era stato preso dalla cosa sbagliata: **«il processo c'e'»**.
#
# ⚠ «Il processo c'e'» non dice NIENTE su dove sta la sua finestra.  Un `mpv`
#   vivo, un `firefox` vivo e un `mpv` che dipinge davvero sul nostro monitor
#   virtuale hanno **la stessa identica faccia** in `ps`.  E' la forma E8 di
#   `LEZIONI.md` §1.9: «non l'ha fatto» e «non me l'ha detto» si assomigliano.
#
# ⇒ Questo strumento fa DUE cose, e la seconda vale piu' della prima:
#     1. lancia il comando **dentro la sessione dell'utente**, nel posto esatto
#        in cui ci finirebbe se lo si fosse scelto dal menu;
#     2. ⭐ **conta i fotogrammi che il server ha spedito** prima e dopo, e da'
#        il verdetto su quel numero.  Un desktop fermo ne spedisce 0 o 1 ogni
#        8 secondi; una finestra che cambia ne spedisce centinaia.
#
# ---------------------------------------------------------------------------
# ⭐⭐ IL METRO, MISURATO OGGI SUL BANCO 7970 (`[M]` 24 agosto 2026, tela
#     2544x926, utente `provanr7`, finestre di 8 s):
#
#       desktop fermo, niente aperto ........   0-1 fotogrammi ·  238-283 byte
#       bandiera-1920x1080.mp4 (tinte piatte)   321 fotogrammi ·      268 byte
#       film-grana.webm .....................   226 fotogrammi ·   18 600 byte
#       duro.mp4 ............................   240 fotogrammi ·   37 081 byte
#
# ⛔⭐ E QUI C'E' UNA CORREZIONE CHE COSTA CARA SE NON SI LEGGE: **il verdetto
#     e' il CONTO, non i byte.**  La bandiera a schermo intero e' una finestra
#     viva, che si muove a 40 fotogrammi al secondo — e i suoi fotogrammi
#     pesano **268 byte**, cioe' esattamente quanto quelli di un desktop fermo.
#     ⚠ Chi avesse guardato solo la misura in byte avrebbe scritto «la finestra
#       non c'e'» su una finestra che c'era, e per intero.
#     ⇒ I byte dicono QUANTO cambia; il conto dice SE cambia.  Il verdetto e'
#       il secondo, e i byte si stampano accanto come sfumatura.
#
# ---------------------------------------------------------------------------
# ⛔ LE TRE GUARDIE, e ognuna e' un'ipotesi che il 24 agosto e' stata esclusa
#    misurandola — restano perche' escludere non e' «non puo' tornare»:
#
#   G1 · **un compositore solo.**  Se per quell'utente girasse piu' di un
#        `gnome-shell`, `WAYLAND_DISPLAY=wayland-0` andrebbe a uno dei due e la
#        cattura all'altro, e nessuna riga lo direbbe.
#   G2 · **un monitor solo, e nostro.**  `mutter.c:340` lo scrive gia' forte:
#        su GNOME barra e dock stanno **solo sul monitor primario**, e una
#        finestra a schermo intero sull'altro monitor non arriva a chi guarda.
#        Zero monitor e' il caso peggiore: la sessione «viva, completa e NERA».
#   G3 · **l'ambiente si LEGGE, non si inventa.**  Il gestore d'utente di
#        systemd ha gia' dentro quel che GNOME ci ha messo — `WAYLAND_DISPLAY`,
#        `XDG_CURRENT_DESKTOP`, `XDG_SESSION_TYPE`, il bus — perche' e' li' che
#        gnome-shell le scrive all'avvio.  ⇒ `systemd-run --user` le eredita
#        **tutte**, ed e' esattamente la strada del menu (le applicazioni del
#        menu nascono in `app.slice`, in uno scope di quel gestore).
#        ⚠ `sudo -u … env WAYLAND_DISPLAY=…` funziona lo stesso `[M]`, ma da'
#          all'applicazione un ambiente monco: niente bus, niente tema, niente
#          lingua.  Si usa per DIAGNOSI (`--minimo`), non per far vedere.
#
# ⚠ Le guardie NON fermano: dicono e proseguono.  Un banco che si rifiuta di
#   partire su un avviso non produce il numero che serviva a decidere.
# ===========================================================================
set -uo pipefail

SECONDI=${SECONDI:-8}
SOGLIA=${SOGLIA:-10}     # fotogrammi nella finestra sotto i quali si dice «no»
REGISTRO=${REGISTRO:-}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
avv() { printf '    \033[1;33m⚠\033[0m   %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { ko "⛔ va eseguito DA ROOT (deve scendere all'utente)"; exit 2; }

MODO=mostra
case "${1:-}" in
--stato)  MODO=stato;  shift ;;
--ferma)  MODO=ferma;  shift ;;
--minimo) MODO=minimo; shift ;;
esac
UTENTE=${1:-}
[ -n "$UTENTE" ] || { ko "⛔ manca l'utente"; exit 2; }
shift
UID_U=$(id -u "$UTENTE" 2>/dev/null) || { ko "⛔ l'utente «$UTENTE» non c'e'"; exit 2; }
RD=/run/user/$UID_U

# ⛔ `env -u` e non `sudo -u`: si scende con `setpriv`, che non porta con se'
#    nessuna riga di `sudoers` e nessun ambiente ereditato per sbaglio.
comeutente() {
	setpriv --reuid="$UID_U" --regid="$UID_U" --init-groups --inh-caps=-all \
		env XDG_RUNTIME_DIR="$RD" \
		    DBUS_SESSION_BUS_ADDRESS="unix:path=$RD/bus" "$@"
}

# ═══════════════════════════════════════════════════════════════════════════
# IL REGISTRO DEL SERVER — si TROVA, non si chiede
#
# ⭐ Si parte dal figlio: e' l'unico processo che porta il nome dell'utente in
#    `/proc/<pid>/cmdline`.  Da li' si sale al padre, dal padre si legge il
#    cgroup (che e' il nome dell'unita' systemd) e dall'unita' si chiede a
#    systemd dove manda lo `StandardOutput`.  ⛔ Nessun percorso indovinato.
# ═══════════════════════════════════════════════════════════════════════════
trova_registro() {
	local figlio padre dove
	[ -n "$REGISTRO" ] && { printf '%s' "$REGISTRO"; return 0; }
	figlio=$(pgrep -u "$UTENTE" -f -- "--figlio-interno $UTENTE " | head -1)
	[ -n "$figlio" ] || return 1
	padre=$(awk '/^PPid:/{print $2}' "/proc/$figlio/status" 2>/dev/null)
	[ -n "$padre" ] || return 1
	# ⛔⭐ E si legge `/proc/<padre>/fd/1`, NON `systemctl show -p StandardOutput`.
	#     `[M]` 24 agosto 2026: con `StandardOutput=append:/…/registro.log`
	#     systemd risponde **`append`** e basta — il percorso non lo pubblica da
	#     nessuna parte.  ⚠ Ed e' la forma peggiore: la risposta arriva, non e'
	#     un errore, e non contiene quel che serve.  Il descrittore aperto dal
	#     processo vivo, invece, e' il file VERO in cui sta scrivendo adesso.
	dove=$(readlink -f "/proc/$padre/fd/1" 2>/dev/null)
	case "$dove" in /*) [ -r "$dove" ] && { printf '%s' "$dove"; return 0; } ;; esac
	return 1
}

# ⭐ IL METRO: quanti fotogrammi il server ha spedito nella finestra, e quanto
#    pesavano.  ⛔ La riga di `rcp.c` e' l'unica che dice **byte davvero
#    spediti**; i contatori del figlio dicono «consegnati dal palco», che e'
#    un'altra cosa e non prova che siano usciti.
conta() { grep -c 'SPEDITO' "$1" 2>/dev/null || echo 0; }
# ⭐ Il battito di chi guarda: una riga al secondo per connessione viva (G4).
guarda() { grep -c 'rete-quic' "$1" 2>/dev/null || echo 0; }
byte_di() { # $1 registro, $2 quanti in coda
	[ "$2" -gt 0 ] || { printf 'nessuno'; return; }
	grep 'SPEDITO' "$1" | tail -n "$2" | grep -oE '[0-9]+ byte di dati' | grep -oE '^[0-9]+' | \
		awk '{s+=$1; if($1>m)m=$1; n++} END{if(n)printf "media %d byte, max %d, %d in tutto", s/n, m, s; else printf "nessuno"}'
}

# ═══════════════════════════════════════════════════════════════════════════
# LE TRE GUARDIE
# ═══════════════════════════════════════════════════════════════════════════
guardie() {
	log "Le guardie della sessione di «$UTENTE» (uid $UID_U)"

	# G1 — un compositore solo
	local quanti
	quanti=$(pgrep -u "$UTENTE" -c -x gnome-shell 2>/dev/null || echo 0)
	if   [ "$quanti" -eq 1 ]; then ok "G1 · un solo compositore ($(pgrep -u "$UTENTE" -x gnome-shell | tr '\n' ' '))"
	elif [ "$quanti" -eq 0 ]; then ko "G1 · ⛔ NESSUN compositore: la sessione grafica non c'e'"
	else ko "G1 · ⛔⛔ $quanti COMPOSITORI per lo stesso utente: «wayland-0» e' di UNO solo, e la cattura potrebbe stare sull'altro"; fi

	# ⚠ E il socket: la sua DATA dice a quale compositore appartiene.
	if [ -S "$RD/wayland-0" ]; then
		ok "G1 · socket $RD/wayland-0 del $(stat -c '%y' "$RD/wayland-0" | cut -d. -f1)"
	else
		ko "G1 · ⛔ $RD/wayland-0 NON c'e'"
	fi

	# G2 — un monitor solo, e nostro
	local stato nomi n
	stato=$(comeutente gdbus call --session \
		-d org.gnome.Mutter.DisplayConfig -o /org/gnome/Mutter/DisplayConfig \
		-m org.gnome.Mutter.DisplayConfig.GetCurrentState 2>&1)
	# ⛔ `grep -oc` NON conta le occorrenze, conta le RIGHE — e `GetCurrentState`
	#    risponde su UNA riga sola: avrebbe detto «1 monitor» anche con cinque.
	#    ⚠ E ogni connettore compare DUE volte (monitor fisici e monitor
	#      logici), quindi si contano i nomi DISTINTI.
	nomi=$(printf '%s' "$stato" | grep -oE "'Meta-[0-9]+', '[^']*', '[^']*'" | sort -u)
	n=$(printf '%s' "$nomi" | grep -c . || true)
	nomi=$(printf '%s' "$nomi" | sed "s/^'\([^']*\)'.*, '\([^']*\)'$/\1 («\2»)/" | tr '\n' '|')
	case "$stato" in
	*"was not provided"*|*Error*)
		ko "G2 · ⛔ DisplayConfig non risponde: non so quanti monitor ci sono, e non dico zero" ;;
	*)
		if   [ "${n:-0}" -eq 0 ]; then
			ko "G2 · ⛔⛔ ZERO MONITOR — la sessione «viva, completa e NERA» (STUDI.md §gnome §3.1): una finestra qui non ha dove andare.  Cura: attaccare un cliente, che e' quel che monta il monitor virtuale"
		elif [ "${n:-0}" -eq 1 ]; then
			ok "G2 · un monitor solo — «${nomi%|}»"
			case "$nomi" in *remote*) ok "G2 · ed e' il NOSTRO («Virtual remote monitor»)" ;;
			                *) avv "G2 · ⚠ ma NON si chiama «Virtual remote monitor»: non e' quello di RecordVirtual" ;; esac
		else
			ko "G2 · ⛔⛔ $n MONITOR (${nomi%|}) — su GNOME barra e dock stanno SOLO sul PRIMARIO: una finestra a schermo intero puo' finire su quello che NON catturiamo, con tutti i contatori verdi (mutter.c:340)"
		fi ;;
	esac

	# G3 — l'ambiente del gestore d'utente, LETTO
	local amb
	amb=$(comeutente systemctl --user show-environment 2>/dev/null)
	local mancanti=""
	for v in WAYLAND_DISPLAY XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS XDG_CURRENT_DESKTOP XDG_SESSION_TYPE; do
		printf '%s\n' "$amb" | grep -q "^$v=" || mancanti="$mancanti $v"
	done
	if [ -z "$mancanti" ]; then
		ok "G3 · il gestore d'utente ha l'ambiente pieno ($(printf '%s\n' "$amb" | grep '^WAYLAND_DISPLAY='))"
	else
		ko "G3 · ⛔ al gestore d'utente MANCANO:$mancanti — un'applicazione lanciata di li' nascerebbe cieca"
	fi
}

case "$MODO" in
stato)
	guardie
	log "Le unita' che questo strumento ha acceso"
	comeutente systemctl --user list-units 'mostra-*' --all --no-legend 2>/dev/null | sed 's/^/    /'
	exit 0 ;;
ferma)
	U=${1:-}
	if [ -n "$U" ]; then
		comeutente systemctl --user stop "$U" 2>&1 | sed 's/^/    /'
		ok "fermata $U"
	else
		for u in $(comeutente systemctl --user list-units 'mostra-*' --all --no-legend 2>/dev/null | awk '{print $1}'); do
			comeutente systemctl --user stop "$u" 2>/dev/null; ok "fermata $u"
		done
	fi
	exit 0 ;;
esac

[ $# -gt 0 ] || { ko "⛔ manca il comando da mostrare"; exit 2; }

guardie

# ═══════════════════════════════════════════════════════════════════════════
# IL FONDO — si misura PRIMA, sempre
#
# ⛔ Senza il fondo il numero di dopo non vuol dire niente: una sessione che
#    sta gia' dipingendo (una notifica, un cursore che lampeggia) darebbe
#    «verde» a un comando che non ha aperto niente.
# ═══════════════════════════════════════════════════════════════════════════
REG=$(trova_registro) || REG=""
log "Il metro"
if [ -z "$REG" ] || [ ! -r "$REG" ]; then
	avv "⚠ il registro del server non si trova (dai REGISTRO=/…/registro.log): NIENTE VERDETTO, lancio e basta"
	REG=""
else
	inf "registro: $REG"
	P0=$(conta "$REG"); Q0=$(guarda "$REG"); sleep "$SECONDI"
	P1=$(conta "$REG"); Q1=$(guarda "$REG"); FONDO=$((P1-P0))
	inf "fondo: $FONDO fotogrammi in $SECONDI s · $(byte_di "$REG" "$FONDO")"
	# ═══════════════════════════════════════════════════════════════════════
	# G4 · ⛔⭐⭐ C'E' QUALCUNO CHE GUARDA?  E questa guardia e' nata da un
	#      rosso su codice giusto, `[M]` 24 agosto 2026, 09:10.
	#
	# ⛔ Senza nessun cliente attaccato il server non spedisce NIENTE — e il
	#    verdetto diceva «la finestra non arriva sullo schermo» su un `mpv` che
	#    stava dipingendo benissimo (581 MB, 7,6 s di CPU, il palco montato).
	#    ⚠ E' esattamente il difetto che questo strumento esiste per NON fare:
	#      un numero giusto letto in una scena in cui non vuol dire niente.
	#
	# ⭐ Il segno di vita di chi guarda e' la riga `wt rete-quic`, che esce
	#    circa una volta al secondo per ogni connessione viva.  Zero righe in
	#    otto secondi = non c'e' nessuno, e allora NON si da' nessun verdetto.
	# ═══════════════════════════════════════════════════════════════════════
	if [ $((Q1-Q0)) -eq 0 ]; then
		ko "G4 · ⛔⛔ NESSUN CLIENTE ATTACCATO (zero righe «rete-quic» in $SECONDI s)"
		inf "      il server non spedisce a nessuno ⇒ il conto dei fotogrammi sarebbe zero"
		inf "      QUALUNQUE cosa faccia la finestra.  Attacca un cliente e ripeti."
		REG=""   # ⇒ si lancia lo stesso, ma senza verdetto
	else
		ok "G4 · c'e' chi guarda: $((Q1-Q0)) battiti «rete-quic» in $SECONDI s"
		[ "$FONDO" -ge "$SOGLIA" ] && avv "⚠ il fondo e' gia' sopra la soglia ($SOGLIA): qualcosa dipinge gia', e il verdetto varra' meno"
	fi
fi

# ═══════════════════════════════════════════════════════════════════════════
# IL LANCIO — dentro il gestore d'utente, che e' la strada del menu
# ═══════════════════════════════════════════════════════════════════════════
UNITA=${UNITA:-mostra-$$}
log "Lancio «$*» come $UTENTE, dentro la sessione"
if [ "$MODO" = minimo ]; then
	# ⚠ La strada MONCA, apposta: serve a confrontare, non a mostrare.
	avv "⚠ --minimo: ambiente ridotto a XDG_RUNTIME_DIR + WAYLAND_DISPLAY (diagnosi, non uso)"
	setpriv --reuid="$UID_U" --regid="$UID_U" --init-groups --inh-caps=-all \
		env -i HOME="$(getent passwd "$UTENTE" | cut -d: -f6)" USER="$UTENTE" LOGNAME="$UTENTE" \
		    PATH=/usr/local/bin:/usr/bin:/bin XDG_RUNTIME_DIR="$RD" WAYLAND_DISPLAY=wayland-0 \
		    "$@" </dev/null >/dev/null 2>&1 &
	inf "pid $!"
else
	comeutente systemd-run --user --unit="$UNITA" --collect \
		--description="09-b82-mostra: $*" "$@" 2>&1 | sed 's/^/    /'
fi

# ═══════════════════════════════════════════════════════════════════════════
# IL VERDETTO — e non e' «il processo c'e'»
# ═══════════════════════════════════════════════════════════════════════════
log "Il verdetto"
if [ -z "$REG" ]; then
	avv "senza registro non do verdetti: guarda tu i fotogrammi"
	exit 0
fi
sleep 3   # ⚠ il tempo che l'applicazione apra la finestra, non che «parta»
D0=$(conta "$REG"); sleep "$SECONDI"; D1=$(conta "$REG"); DOPO=$((D1-D0))
inf "dopo:  $DOPO fotogrammi in $SECONDI s · $(byte_di "$REG" "$DOPO")"
inf "prima: $FONDO fotogrammi"
if [ "$DOPO" -ge "$SOGLIA" ] && [ "$DOPO" -gt $((FONDO * 3)) ]; then
	ok "⭐ LA FINESTRA E' SULLO SCHERMO CHE REMOTIX CATTURA — $DOPO fotogrammi contro $FONDO di fondo"
	printf '    --  per fermarla: bash %s --ferma %s %s\n' "$0" "$UTENTE" "$UNITA"
	exit 0
else
	ko "⛔ LA FINESTRA **NON** ARRIVA SULLO SCHERMO CATTURATO — $DOPO fotogrammi contro $FONDO di fondo"
	inf "e adesso si guarda, in quest'ordine:"
	inf "  1. il processo e' vivo?  ⚠ se si', «vivo» non e' «visibile» — e' proprio il caso che questo strumento esiste per smascherare"
	comeutente systemctl --user status "$UNITA" --no-pager -n 15 2>/dev/null | sed 's/^/        /'
	inf "  2. le guardie qui sopra: zero monitor, o piu' di uno, spiegano tutto"
	inf "  3. se le guardie sono verdi e il processo e' vivo, il difetto e' DELL'APPLICAZIONE"
	inf "     ([M] 24 ago 2026: firefox-esr 140.14 si pianta all'avvio su questa macchina"
	inf "      anche in --headless e anche fuori da REMOTIX ⇒ non e' nostro)"
	exit 1
fi
