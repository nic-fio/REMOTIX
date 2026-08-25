#!/bin/bash
# ===========================================================================
# 10-f2-dentro.sh — esegue un comando DENTRO la sessione remota di un utente,
# nei DUE modi in cui un programma ci puo' finire.  ⛔ Sono due modi diversi e
# la differenza fra loro e' meta' della diagnosi.
#
#   10-f2-dentro.sh <UTENTE> composto  <comando...>
#       ⚠ l'ambiente si compone da ZERO, una variabile per volta
#         (`CODER.md` §4.5).  E' come i banchi hanno sempre lanciato le cose.
#         ⛔ Non e' come GNOME lancia un'applicazione dal menu.
#
#   10-f2-dentro.sh <UTENTE> menu      <comando...>
#       ⭐ passa dal GESTORE D'UTENTE (`systemd-run --user --scope`), che porta
#         l'ambiente che `gnome-session` gli ha IMPORTATO — cioe' esattamente
#         quel che riceve un'applicazione avviata dal menu di GNOME.
#         ⛔ Se un programma va in un modo e non nell'altro, il difetto e'
#            nell'ambiente e non nel programma: ed e' una risposta, non un
#            impiccio.
#
#   10-f2-dentro.sh <UTENTE> ambiente
#       stampa l'ambiente che il gestore d'utente ha importato.
#
# ⛔ Da root, sulla macchina di prova.
# ===========================================================================
set -uo pipefail

# ⚠ Niente apostrofi dentro `${…:?…}`: li' bash sta gia' analizzando una
#   espansione, e un apostrofo apre una quotatura che non si chiude piu'.
U=${1:?serve un utente}
MODO=${2:?serve il modo: composto | menu | ambiente}
shift 2

UID_U=$(id -u "$U") || exit 2
RUN="/run/user/$UID_U"

case "$MODO" in
composto)
	exec setpriv --reuid="$UID_U" --regid="$UID_U" --init-groups \
		env -i HOME="/home/$U" USER="$U" LOGNAME="$U" LANG=C.UTF-8 \
		PATH=/usr/local/bin:/usr/bin:/bin \
		XDG_RUNTIME_DIR="$RUN" \
		WAYLAND_DISPLAY=wayland-0 \
		GDK_BACKEND=wayland \
		DBUS_SESSION_BUS_ADDRESS="unix:path=$RUN/bus" \
		"$@"
	;;
menu)
	# ⭐ UN SERVIZIO del gestore d'utente, non uno «scope».
	#
	# ⛔ `--scope` NON serve: con lo scope il processo lo forca `systemd-run`
	#    stesso e si porta dietro l'ambiente di ROOT — cioe' proprio quel che
	#    si voleva evitare.  ⚠ E in piu' `--pipe` non e' compatibile con
	#    `--scope`, che e' come ce ne si e' accorti.
	# ⭐ Con `--service-type=exec` a lanciare e' **il gestore d'utente**, e il
	#    processo nasce con l'ambiente che `gnome-session` gli ha IMPORTATO:
	#    e' quel che riceve un'applicazione avviata dal menu di GNOME.
	# ⚠ L'uscita finisce in un file scritto DAL GESTORE, cioe' dall'utente.
	exec systemd-run --user --machine="$U@" --quiet --collect --wait \
		--service-type=exec \
		-p StandardOutput=append:"${F2_USCITA:-/tmp/f2-menu.log}" \
		-p StandardError=append:"${F2_USCITA:-/tmp/f2-menu.log}" \
		--unit="f2-$(date +%s%N)" -- "$@"
	;;
ambiente)
	# ⭐ L'ambiente che il gestore d'utente ha importato: e' il confronto fra
	#    «composto» e «menu», e la differenza fra i due e' meta' della diagnosi.
	exec systemctl --user --machine="$U@" show-environment
	;;
*)
	echo "⛔ modo sconosciuto: $MODO" >&2
	exit 2
	;;
esac
