#!/bin/bash
# ===========================================================================
# 10-f2-profilo.sh — ⛔⛔ IL MECCANISMO PER CUI FIREFOX DICE «Profile Missing»
# dentro il desktop remoto, e la sua cura in una riga.
#
# ---------------------------------------------------------------------------
# ⭐ IL MECCANISMO, misurato il 25 agosto 2026
#
#   `/etc/skel/.cache` di questa macchina e' un COLLEGAMENTO a `/tmp`.
#   `src/provisiona.sh:64` crea gli utenti con `useradd -m`, che copia lo
#   scheletro ⇒ **ogni** utente di prova ha `~/.cache -> /tmp`.
#
#   Firefox tiene il profilo «locale» sotto `$HOME/.cache/mozilla`, cioe' qui
#   sotto `/tmp/mozilla`.  ⛔ Il PRIMO utente che apre Firefox crea
#   `/tmp/mozilla` **a modo 0700 e a nome suo**; da quel momento nessun altro
#   utente ci puo' scrivere, la creazione del profilo fallisce, e il browser
#   apre una finestra che dice *«Your Firefox profile cannot be loaded. It may
#   be missing or inaccessible.»* — cioe' **e' inutilizzabile**.
#
#   `[M]` `/tmp/mozilla` era di `prova2`, modo 0700, dal 23 agosto 08:03.
#
# ⇒ ⭐ NON E' UN DIFETTO DI REMOTIX: si riproduce **headless, senza
#      compositore, senza sessione remota, senza il server**.  Ed e' per
#      questo che questo file misura il fuori e il dentro con lo stesso metro.
#
# ---------------------------------------------------------------------------
#   uso:
#     10-f2-profilo.sh <UTENTE> stato       che cosa c'e' adesso
#     10-f2-profilo.sh <UTENTE> rosso       rimette il collegamento (guasto)
#     10-f2-profilo.sh <UTENTE> verde       cache vera dentro casa (cura)
#     10-f2-profilo.sh <UTENTE> prova       ⭐ apre Firefox headless e dice se
#                                           il profilo e' nato: e' il giudizio
#
# ⛔ `prova` esce 0 se il profilo NASCE, 1 se NON nasce, 2 se non ho potuto
#    guardare — `None` non e' zero.
# ===========================================================================
set -uo pipefail

U=${1:?serve un utente}
AZIONE=${2:?serve una azione: stato | rosso | verde | prova}
UID_U=$(id -u "$U") || exit 2
CASA="/home/$U"

case "$AZIONE" in
stato)
	echo "   $CASA/.cache -> $(readlink "$CASA/.cache" 2>/dev/null || echo '(cartella vera)')"
	ls -ld /tmp/mozilla 2>&1 | sed 's/^/   /'
	ls -ld "$CASA/.mozilla/firefox" 2>&1 | sed 's/^/   /'
	if [ -f "$CASA/.mozilla/firefox/profiles.ini" ]; then
		echo "   ⭐ profiles.ini C'E'"
	else
		echo "   ⛔ profiles.ini NON c'e': nessun profilo e' mai nato"
	fi
	;;
rosso)
	# ⛔ Il controllo negativo: si RIMETTE il guasto, e il banco deve tornare
	#    rosso.  Se non ci torna, non stava misurando la cura.
	rm -rf "$CASA/.cache"
	ln -s /tmp "$CASA/.cache"
	chown -h "$UID_U:$UID_U" "$CASA/.cache"
	rm -rf "$CASA/.mozilla"
	echo "   ⛔ rimesso: $CASA/.cache -> /tmp, e .mozilla svuotata"
	;;
verde)
	# ⭐ La cura: una cartella `.cache` VERA dentro casa.  ⚠ Non si tocca
	#   `/tmp/mozilla` di un altro utente: non e' nostro e non si sa chi lo usa.
	rm -rf "$CASA/.cache"
	mkdir -p "$CASA/.cache"
	chown "$UID_U:$UID_U" "$CASA/.cache"
	chmod 700 "$CASA/.cache"
	rm -rf "$CASA/.mozilla"
	echo "   ⭐ curato: $CASA/.cache e' una cartella vera, e .mozilla svuotata"
	;;
prova)
	# ⛔ Headless e SENZA compositore: se il difetto si vede anche qui, non e'
	#    del desktop remoto.  ⚠ E la fase 9 aveva dichiarato «Firefox non parte
	#    nemmeno fuori da REMOTIX» misurando su una macchina senza sessione
	#    grafica: la' non poteva partire per costruzione.  Qui invece si guarda
	#    UNA COSA SOLA — il profilo nasce, si' o no — che non ha bisogno di uno
	#    schermo.
	rm -f /tmp/10f2-prova-firefox.log
	setpriv --reuid="$UID_U" --regid="$UID_U" --init-groups \
		env -i HOME="$CASA" USER="$U" LANG=C.UTF-8 PATH=/usr/bin:/bin \
		TMPDIR=/tmp MOZ_HEADLESS=1 \
		/usr/bin/firefox-esr --headless about:blank \
		>/tmp/10f2-prova-firefox.log 2>&1 &
	PID=$!
	i=0
	NATO=no
	while [ $i -lt 60 ]; do
		if [ -f "$CASA/.mozilla/firefox/profiles.ini" ]; then NATO=si; break; fi
		kill -0 "$PID" 2>/dev/null || break
		i=$((i + 1)); sleep 0.5
	done
	VIVO=no; kill -0 "$PID" 2>/dev/null && VIVO=si
	kill -9 "$PID" 2>/dev/null; wait "$PID" 2>/dev/null
	pkill -9 -u "$UID_U" -f 'firefox-es[r]' 2>/dev/null
	if [ "$VIVO" = no ] && [ "$NATO" = no ]; then
		# ⚠ Firefox morto prima di poter dire la sua: NON ho potuto guardare.
		echo "   ⛔ NON MISURATO: Firefox e' morto prima di provarci"
		sed 's/^/     /' /tmp/10f2-prova-firefox.log | head -10
		exit 2
	fi
	if [ "$NATO" = si ]; then
		echo "   ⭐ VERDE: il profilo e' NATO — $(sed -n '/^Path=/p' "$CASA/.mozilla/firefox/profiles.ini" | head -2 | tr '\n' ' ')"
		exit 0
	fi
	echo "   ⛔ ROSSO: dopo 30 s nessun profiles.ini — il profilo NON nasce"
	ls -ld /tmp/mozilla 2>&1 | sed 's/^/     /'
	exit 1
	;;
meccanismo)
	# ⭐⭐ IL MECCANISMO NUDO, senza Firefox di mezzo: l'utente prova a scrivere
	#    dove Firefox scriverebbe il profilo locale, e si guarda che cosa dice
	#    il nucleo.  ⛔ Serve perche' «Firefox non crea il profilo» e «l'utente
	#    non puo' scrivere li'» sono due affermazioni diverse, e la seconda si
	#    puo' provare in una riga — senza browser, senza compositore, senza GPU.
	echo "   chi possiede /tmp/mozilla, e con che modo:"
	ls -ld /tmp/mozilla 2>&1 | sed 's/^/     /'
	echo "   $CASA/.cache -> $(readlink "$CASA/.cache" 2>/dev/null || echo '(cartella vera)')"
	echo "   l'utente prova a creare \$HOME/.cache/mozilla/firefox/prova-f2:"
	setpriv --reuid="$UID_U" --regid="$UID_U" --init-groups \
		/bin/mkdir -p "$CASA/.cache/mozilla/firefox/prova-f2" 2>&1 \
		| sed 's/^/     /'
	if setpriv --reuid="$UID_U" --regid="$UID_U" --init-groups \
		/usr/bin/test -d "$CASA/.cache/mozilla/firefox/prova-f2"; then
		echo "     ⭐ RIUSCITO: qui il profilo locale ci puo' stare"
		setpriv --reuid="$UID_U" --regid="$UID_U" --init-groups \
			/bin/rmdir "$CASA/.cache/mozilla/firefox/prova-f2" 2>/dev/null
		exit 0
	fi
	echo "     ⛔ NON RIUSCITO: il profilo locale non ci puo' stare"
	exit 1
	;;
*)
	echo "⛔ azione sconosciuta: $AZIONE" >&2; exit 2 ;;
esac
