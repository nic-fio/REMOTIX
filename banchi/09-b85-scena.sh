#!/bin/sh
# 09-b85-scena.sh — la claquette dentro la sessione catturata, e il suo spegni.
#
#   env LAV=… UID_B=1073 UTENTE=provanr10 FILM=/…/x.mp4 sh 09-b85-scena.sh accendi
#   env UID_B=1073 sh 09-b85-scena.sh spegni
#
# ⛔ E' UN FILE, e non una riga dentro `root("… &")`.  Pagato dal banco
#    dell'audio il 23 agosto 2026 (`09-b74-ff.sh`:6-24): con `sudo bash -c '…
#    &'` la bash esce nello stesso istante, sudo esce dietro, ssh chiude la
#    sessione e il processo muore **prima che `setsid` lo abbia staccato**.  Il
#    sintomo era «il lettore non parte», e l'imputato sbagliato era il lettore.
#
# ⛔ E SI SCENDE ALL'UID DELL'UTENTE con `setpriv`: solo lui puo' parlare col
#    suo compositore.  `env -i` e poi il quartetto — `XDG_RUNTIME_DIR`,
#    `WAYLAND_DISPLAY`, `HOME`, `PATH`.  ⚠ Nessun `DISPLAY`: la sessione e'
#    Wayland pura.
set -u
LAV=${LAV:-/media/REMOTIX/tmp/09nr10}
UID_B=${UID_B:-1073}
UTENTE=${UTENTE:-provanr10}
FILM=${FILM:-}
LOG=${LOG:-/tmp/b85-scena.log}

case "${1:-}" in
spegni)
	pkill -u "$UID_B" -x mpv
	pkill -u "$UID_B" -f 'b85-scena'
	sleep 0.5
	printf 'SCENA SPENTA (restano: %s)\n' "$(pgrep -u "$UID_B" -x mpv | tr '\n' ' ')"
	exit 0 ;;
accendi) ;;
*) printf 'uso: accendi | spegni\n'; exit 2 ;;
esac

[ -s "$FILM" ] || { printf '⛔ il film «%s» non c%s e\n' "$FILM" "'"; exit 2; }
rm -f "$LOG"

# ⭐ `--audio-device=pipewire/remotix`: il pozzo che il figlio di REMOTIX crea
#    quando un client si attacca (I4).  ⛔ Senza il bersaglio esplicito mpv
#    finisce sul pozzo predefinito, che NON e' quello catturato: si misurerebbe
#    silenzio, e «silenzio» ha la stessa faccia di «l'audio non arriva».
# ⭐ `--video-sync=audio` e' il predefinito e si LASCIA: e' quel che fa un
#    lettore vero.  ⚠ Vuol dire che lo sfalso di mpv entra nella misura, e si
#    dichiara — la sottrazione fra due film con sfalso NOTO lo elide.
# ⛔ `--no-config`: sulla macchina di prova non c'e' nessun `mpv.conf`, ma un
#    file comparso un altro giorno cambierebbe la misura senza dirlo.
setsid nohup setpriv --reuid="$UID_B" --regid="$UID_B" --init-groups \
	env -i HOME="/home/$UTENTE" USER="$UTENTE" LANG=C.UTF-8 \
	PATH=/usr/local/bin:/usr/bin:/bin \
	XDG_RUNTIME_DIR="/run/user/$UID_B" WAYLAND_DISPLAY=wayland-0 \
	mpv --no-config --fullscreen --loop-file=inf \
	    --no-osc --osd-level=0 --no-input-default-bindings \
	    --audio-device=pipewire/remotix \
	    --keep-open=no --really-quiet=no \
	    "$FILM" >>"$LOG" 2>&1 &

i=0
while [ $i -lt 40 ]; do
	if pgrep -u "$UID_B" -x mpv >/dev/null 2>&1; then
		sleep 2
		# ⛔ «il processo c'e'» NON e' «il film suona»: si guarda il registro
		#    di mpv, che dice se ha aperto il video e l'audio.
		printf 'SCENA ACCESA pid=%s\n' "$(pgrep -u "$UID_B" -x mpv | head -1)"
		tail -12 "$LOG"
		exit 0
	fi
	i=$((i + 1)); sleep 0.25
done
printf '⛔ mpv NON e%s partito\n' "'"
tail -25 "$LOG"
exit 2
