#!/bin/bash
#
# 00-sessione-gnome.sh — avvia una sessione GNOME senza monitor, e VERIFICA che
# sia headless invece di sperarlo.
#
#   bash 00-sessione-gnome.sh avvia    compone l'ambiente e fa partire la sessione
#   bash 00-sessione-gnome.sh stato    c'e'? ed e' headless?
#   bash 00-sessione-gnome.sh ferma    la chiude
#
# ---------------------------------------------------------------------------
# PERCHE' ESISTE, VISTO CHE IL PRODOTTO SAPRA' FARLO DA SE'
#
# Alla fase 0 il prodotto non c'e' ancora, e il controllo positivo dell'intero
# progetto — i ~37 fotogrammi di Mutter — vuole una sessione viva.  Questo banco
# fa il minimo per averla, con la stessa ricetta che `v1/remotix-c/src/sessione.c`
# usa nel prodotto: l'ambiente si COMPONE da zero, una variabile per volta.
#
# ---------------------------------------------------------------------------
# ⛔ LA VERIFICA CHE E' IL MOTIVO VERO DI QUESTO FILE
#
# Su GNOME, entrando nel dialogo di sblocco, Mutter chiude cattura, controllo e
# input e RIFIUTA di ricrearli.  L'unica eccezione e' `is_headless()`.
#
# E noi siamo headless PER ACCIDENTE: Mutter ci si mette da solo quando la
# sessione logind a cui si aggancia non ha un seat
# (`meta-backend-native.c:759-764`, letto il 9 agosto 2026).  Nessuna nostra riga
# lo chiede.  `DECISIONI.md` §4.3-bis dice che questo va trattato come un
# REQUISITO: si dichiara, si verifica dopo l'avvio, e se manca si fallisce
# dichiarandolo.
#
# ⭐ Il segnale osservabile e' una frase di Mutter stesso — «No seat assigned,
#    running headlessly» — cioe' si CHIEDE al componente invece di dedurre
#    (`LEZIONI.md` §1.6 e §1.11 regola 2).  Guardare «ha aperto un render node»
#    o «la sessione c'e'» sarebbe la forma d'errore E1: necessario preso per
#    sufficiente.
#
# ---------------------------------------------------------------------------
set -uo pipefail

UID_UTENTE=$(id -u)
RUNTIME=${XDG_RUNTIME_DIR:-/run/user/$UID_UTENTE}
REGISTRO=$RUNTIME/remotix-sessione.log
REGISTRO_SHELL=$RUNTIME/mutter.log
COMANDO="exec gnome-session --session=gnome"

# ---------------------------------------------------------------------------
# ⛔ DOVE FINISCE QUEL CHE MUTTER DICE, E PERCHE' NON E' DOVE SEMBRA
#
# `gnome-session` NON lancia gnome-shell: fa partire l'unita' d'utente
# `org.gnome.Shell@wayland.service`.  Quindi la Shell non eredita la nostra
# redirezione, e i suoi messaggi vanno al journal — cioe' altrove.
#
# ⛔ E su questa macchina il journal non e' una strada: `journalctl --user`
#    risponde «No journal files were found» (il rootfs vive in RAM).  Al primo
#    giro, il 9 agosto 2026, ha risposto peggio — «insufficient permissions» —
#    e un `grep` che non trovava niente sarebbe passato per «Mutter non l'ha
#    detto».  Lettura NEGATA che sembra lettura VUOTA: `LEZIONI.md` §1.9.
#
# ⭐ La cura non chiede root: l'unita' e' d'UTENTE, quindi un drop-in in
#    ~/.config/systemd/user vince su quello di sistema, e possiamo mandare
#    l'uscita della Shell in un file nostro.
# ---------------------------------------------------------------------------
registro_shell()
{
	local cartella=$HOME/.config/systemd/user/org.gnome.Shell@wayland.service.d

	mkdir -p "$cartella"
	cat >"$cartella/00-registro.conf" <<CONF
[Service]
StandardOutput=append:$REGISTRO_SHELL
StandardError=append:$REGISTRO_SHELL
CONF
	systemctl --user daemon-reload
}

# ---------------------------------------------------------------------------
# L'ambiente, composto da zero.
#
# ⛔ SHELL VUOTA, e non e' pignoleria: `gnome-session.in:3-14` si RI-ESEGUE
#    dentro una shell di login se `$SHELL` sta in /etc/shells — cioe' si
#    riporta dentro `~/.profile` e tutto quel che c'e' scritto li'.  E' la
#    trappola di `LEZIONI.md` §5 e sta in `STUDI.md` §gnome §3.1.
#
# ⛔ XDG_SESSION_TYPE=wayland SERVE: l'unita' della Shell porta
#    `ConditionEnvironment=XDG_SESSION_TYPE=wayland`, e senza il compositore non
#    viene avviato affatto — la sessione parte monca e nessuno spiega perche'.
# ---------------------------------------------------------------------------
ambiente()
{
	printf '%s\n' \
	    "HOME=$HOME" \
	    "USER=$(id -un)" \
	    "PATH=/usr/local/bin:/usr/bin:/bin" \
	    "SHELL=" \
	    "LANG=C.UTF-8" \
	    "XDG_RUNTIME_DIR=/run/user/$UID_UTENTE" \
	    "DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/$UID_UTENTE/bus" \
	    "XDG_CURRENT_DESKTOP=GNOME" \
	    "XDG_SESSION_DESKTOP=gnome" \
	    "XDG_SESSION_TYPE=wayland"
}

viva()
{
	pgrep -u "$UID_UTENTE" -x gnome-shell >/dev/null 2>&1
}

# ---------------------------------------------------------------------------
# ⛔ SI FERMA L'UNITA' E SI ASPETTA CHE SIA INATTIVA — non si uccide e riparte.
#
# `LEZIONI.md` §2.3-ter, pagata su Plasma l'8 agosto 2026 e ripagata qui il 9
# su GNOME: fra «ho ucciso il processo» e «il gestore di servizi lo sa» c'e' un
# intervallo, e un banco che riparte dentro quell'intervallo si comporta in modo
# diverso dalla prima esecuzione.
#
# ⭐ Su GNOME il sintomo e' peggiore che su KDE, perche' NON C'E' UN ERRORE: al
#    primo giro `pkill gnome-session` ha lasciato `gnome-session-manager@gnome`
#    ATTIVA con la Shell morta, e il riavvio non ha fatto niente affatto — la
#    sessione risultava «gia' avviata» a un gestore che non aveva piu' un
#    compositore.  Quaranta secondi di attesa e nessuna riga che dicesse perche'.
# ---------------------------------------------------------------------------
# ⛔ E IL CONGEDO E' `Logout(2)`, non `systemctl --user stop`.
#
#    Provato il 9 agosto 2026: fermare `gnome-session.target` lascia
#    `gnome-session-manager@gnome.service` ATTIVA — `gnome-session` non esce dopo
#    aver avviato il target, apre un fifo e dorme, uscendo a sessione smontata
#    (`STUDI.md` §gnome §3.2).  `Logout(1)` non basta: mostra il dialogo se esiste un
#    inibitore, e in una sessione non presidiata non lo vede nessuno.
ferma_e_aspetta()
{
	local scadenza=$((SECONDS + ${1:-45}))
	local stato

	gdbus call --session -d org.gnome.SessionManager -o /org/gnome/SessionManager \
	    -m org.gnome.SessionManager.Logout 2 >/dev/null 2>&1

	while [ $SECONDS -lt $scadenza ]; do
		stato=$(systemctl --user is-active gnome-session-manager@gnome.service)
		# ⛔ SI ASPETTA `inactive`, NON «diverso da active».
		#
		#    `is-active` passa per `deactivating`, che non e' `active` — e una
		#    guardia scritta come `!= active` lascia ripartire il banco DENTRO
		#    l'intervallo di smontaggio, cioe' esattamente il difetto che questa
		#    funzione esiste per togliere.  Misurato il 9 agosto: la condizione
		#    sbagliata si sbloccava dopo mezzo secondo, con systemd ancora al
		#    lavoro.
		case "$stato" in
		inactive|failed|unknown)
			if ! viva; then
				# Le unita' fallite restano fallite e bloccano il giro dopo.
				systemctl --user reset-failed 2>/dev/null
				return 0
			fi
			;;
		esac
		sleep 0.5
	done
	return 1
}

# ⛔ Non si aspetta un silenzio: si aspetta un EVENTO, con un tetto dichiarato.
attendi()
{
	local scadenza=$((SECONDS + ${1:-40}))

	while [ $SECONDS -lt $scadenza ]; do
		if viva && busctl --user list 2>/dev/null | grep -q org.gnome.Shell; then
			return 0
		fi
		sleep 0.5
	done
	return 1
}

# ---------------------------------------------------------------------------
# La verifica dell'headless.
#
# Tre esiti distinti, e il terzo e' quello che `LEZIONI.md` §1.9 pretende:
# «vuoto» e «proibito» non devono avere lo stesso aspetto.
# ---------------------------------------------------------------------------
# ---------------------------------------------------------------------------
# ⛔ E LA PROVA HA DUE FACCE, PERCHE' L'HEADLESS SI RAGGIUNGE IN DUE MODI.
#
# Letto in `meta-backend-native.c:748-764` il 9 agosto 2026:
#
#     if (priv->mode == META_BACKEND_NATIVE_MODE_HEADLESS || …)
#       return TRUE;                       ← CHIESTO: esce subito, NESSUN messaggio
#     launcher = meta_launcher_new (…);
#     if (!meta_launcher_get_seat_id (launcher))
#       { priv->mode = HEADLESS;
#         g_message ("No seat assigned, running headlessly"); }   ← SUBITO: lo dice
#
# ⭐ Quindi la frase «No seat assigned» compare SOLO nel percorso accidentale.
#    La prima stesura di questo banco cercava quella — e su una sessione sana,
#    avviata con `--headless` come vuole `DECISIONI.md` §4.3-bis, avrebbe dato
#    ROSSO PER SEMPRE.  E' `LEZIONI.md` §1.11: per ogni prova indiretta va
#    scritto che aspetto avrebbe il caso opposto, o la prova non distingue.
#
# ⚠ E si legge la riga di comando del PROCESSO, non il file di drop-in: che
#   l'opzione sia scritta non e' che sia in vigore (§1.11 di nuovo, e §1.8).
# ---------------------------------------------------------------------------
headless()
{
	local pid cmdline

	pid=$(pgrep -u "$UID_UTENTE" -x gnome-shell | head -1)
	if [ -z "$pid" ]; then
		echo "IGNOTO: non c'e' nessun gnome-shell da interrogare"
		return 2
	fi

	cmdline=$(tr '\0' ' ' <"/proc/$pid/cmdline" 2>/dev/null)
	if [ -z "$cmdline" ]; then
		echo "IGNOTO: non riesco a leggere /proc/$pid/cmdline (lettura negata?)"
		return 2
	fi

	case "$cmdline" in
	*--headless*)
		echo "SI, ed e' CHIESTO: gnome-shell gira con --headless"
		echo "    riga di comando: $cmdline"
		return 0
		;;
	esac

	# Non l'abbiamo chiesto: allora l'unica speranza e' il percorso accidentale,
	# e per saperlo ci vuole il registro.
	if [ ! -s "$REGISTRO_SHELL" ]; then
		echo "IGNOTO: --headless non c'e' nella riga di comando, e il registro di"
		echo "        Mutter e' vuoto ($REGISTRO_SHELL).  Non e' «Mutter non l'ha"
		echo "        detto»: e' «non lo abbiamo sentito»."
		return 2
	fi
	if grep -q "No seat assigned, running headlessly" "$REGISTRO_SHELL"; then
		echo "SI, ma per ACCIDENTE: Mutter dice «No seat assigned, running headlessly»."
		echo "    ⚠ Funziona, ma nessuna nostra riga lo chiede — DECISIONI.md §4.3-bis"
		echo "      dice che va dichiarato, non ereditato dalla mancanza di un seat."
		return 0
	fi

	echo "NO: ne' chiesto ne' accidentale."
	echo "    Con un seat assegnato il blocco schermo REVOCA cattura e input"
	echo "    (STUDI.md §gnome §4, DECISIONI.md §4.3-bis).  Le sessioni logind:"
	loginctl list-sessions --no-legend | sed 's/^/    /'
	return 1
}

case "${1:-stato}" in
avvia)
	# ⛔ «Non c'e' un gnome-shell» non vuol dire «non c'e' una sessione»: il
	#    gestore puo' essere vivo con il compositore morto, e allora il comando
	#    qui sotto non fa niente e nessuno lo dice.  Si parte da pulito.
	if [ "$(systemctl --user is-active gnome-session-manager@gnome.service)" = active ] \
	   && ! viva
	then
		echo "gestore di sessione vivo ma senza compositore: fermo tutto e riparto"
		ferma_e_aspetta || { echo "⛔ non si e' fermata in tempo"; exit 1; }
	fi

	if viva; then
		echo "c'e' gia' una sessione: $(pgrep -u "$UID_UTENTE" -x gnome-shell | tr '\n' ' ')"
	else
		registro_shell
		: >"$REGISTRO"; : >"$REGISTRO_SHELL"
		# `setsid --fork` la stacca dal nostro gruppo di processi: chiudere
		# l'ssh non se la porta via.
		env -i $(ambiente) setsid --fork sh -c "exec >>'$REGISTRO' 2>&1; $COMANDO"
		if ! attendi 40; then
			echo "⛔ la sessione NON e' partita entro 40 s.  Ultime righe:"
			tail -n 25 "$REGISTRO" | sed 's/^/    /'
			exit 1
		fi
		echo "sessione avviata"
	fi
	echo -n "headless? "; headless
	;;
stato)
	if viva; then
		echo "gnome-shell:  $(pgrep -u "$UID_UTENTE" -c -x gnome-shell) processo/i"
	else
		echo "gnome-shell:  nessuno"
	fi
	echo -n "headless?     "; headless
	;;
ferma)
	ferma_e_aspetta && echo "fermata" || { echo "⛔ non si e' fermata in tempo"; exit 1; }
	;;
registro) tail -n "${2:-40}" "$REGISTRO" ;;
*) echo "uso: $0 {avvia|stato|ferma|registro [n]}" >&2; exit 2 ;;
esac
