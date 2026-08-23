#!/bin/sh
# 09-b74-ff.sh — ⭐ accende **Firefox con Marionette** dentro la sessione di
#                un utente, e aspetta che la porta si apra.
#
# ⛔⛔ ESISTE PER LA TERZA VOLTA PER LA STESSA RAGIONE, e stavolta la ragione
#    e' misurata invece che sospettata — 23 agosto 2026, 14:49.
#
#    `09-b74-audio-firefox.py` lanciava il browser cosi':
#
#      ssh → printf parola | sudo -S bash -c "setsid nohup setpriv … firefox … &"
#
#    ⇒ `bash -c` mette il lavoro in sottofondo e **esce nello stesso istante**;
#      `sudo` esce dietro di lui, `ssh` chiude la sessione, e il processo muore
#      nella corsa prima ancora che `setsid` lo abbia staccato.
#    ⛔ `[M]` il registro del browser — creato PRIMA, con l'uid giusto e i
#      permessi giusti — e' rimasto di **ZERO byte**, e `pgrep firefox` non ha
#      mai trovato niente: ⇒ **non e' Firefox che non apre Marionette, e'
#      Firefox che non parte affatto**.  Per due sere il banco ha accusato il
#      browser di un difetto del suo lanciatore.
#
# ⭐ La cura e' quella che `09-b68-scena.sh` e `09-b72-video.sh` hanno gia'
#    pagato: **un file, non una riga di comando** — e il padre resta vivo
#    (`sleep`/attesa) mentre il figlio si stacca.
#    ⚠ `LEZIONI.md`: un copione lungo si spedisce come FILE, mai su `stdin`.
#
# ⛔ Gira DA ROOT e scende all'uid dell'utente (`setpriv`): solo lui puo'
#    parlare col suo compositore Wayland.
#
#   UID_B=1001 UTENTE=prova PROFILO=/tmp/b74-ff sh 09-b74-ff.sh <url>
#   sh 09-b74-ff.sh -- spegni
set -u
UID_B=${UID_B:-1001}
UTENTE=${UTENTE:-prova}
PROFILO=${PROFILO:-/tmp/b74-ff}
PORTA_M=${PORTA_M:-2829}
LOG=${LOG:-/tmp/b74-ff.log}

if [ "${2:-}" = "spegni" ] || [ "${1:-}" = "spegni" ]; then
	pkill -u "$UID_B" -f firefox 2>/dev/null
	sleep 1
	pkill -9 -u "$UID_B" -f firefox 2>/dev/null
	exit 0
fi

URL=$1

if ! command -v firefox-esr >/dev/null 2>&1; then
	echo "FIREFOX NON PARTITO: firefox-esr non c'e'"
	exit 2
fi
if [ ! -s "$PROFILO/user.js" ]; then
	echo "FIREFOX NON PARTITO: «$PROFILO/user.js» manca o e' VUOTO — e un file"
	echo "  vuoto ha la faccia di un file scritto: Marionette aprirebbe la sua"
	echo "  porta di serie invece della $PORTA_M e il banco direbbe «non ha aperto»"
	exit 3
fi

pkill -u "$UID_B" -f firefox 2>/dev/null
sleep 1
# ⛔⛔ IL `rm -f` PRIMA DEL `>` NON E' PULIZIA: E' L'UNICO MODO DI APRIRLO.
#    `[M]` 23 agosto 2026, 14:52 — questa riga era `: > "$LOG"` e da ROOT dava
#    **«cannot create /tmp/b74-ff.log: Permission denied»**.  La causa e'
#    `fs.protected_regular = 2` (verificato con `sysctl`): in una cartella
#    **sticky** come `/tmp`, nemmeno root puo' aprire in scrittura un file
#    **world-writable** che appartiene a un altro utente — ed e' proprio quel
#    che il giro precedente aveva lasciato li' (`prova`, modo 666).
#    ⭐ Cancellarlo si puo' (e' il permesso della cartella, non del file), e
#      ricrearlo lo rende di root.  ⚠ A Firefox, che gira come `$UTENTE`, il
#      proprietario non serve: il descrittore lo eredita gia' aperto.
rm -f "$LOG"
: > "$LOG" || { echo "FIREFOX NON PARTITO: non riesco a creare «$LOG»"; exit 6; }
chmod 666 "$LOG"

setsid nohup setpriv --reuid="$UID_B" --regid="$UID_B" --init-groups \
	env -i HOME="/home/$UTENTE" USER="$UTENTE" LANG=C.UTF-8 \
	PATH=/usr/local/bin:/usr/bin:/bin \
	XDG_RUNTIME_DIR="/run/user/$UID_B" WAYLAND_DISPLAY=wayland-0 \
	MOZ_ENABLE_WAYLAND=1 GDK_BACKEND=wayland MOZ_MARIONETTE=1 \
	firefox-esr --profile "$PROFILO" --marionette "$URL" \
	>>"$LOG" 2>&1 &

# ⛔ «Il processo esiste» non e' «Marionette ascolta»: si aspetta la PORTA, e
#    se non arriva si dice **che cosa si e' visto** invece di «non ha aperto».
i=0
while [ $i -lt 60 ]; do
	if ss -tln 2>/dev/null | grep -q ":$PORTA_M "; then
		echo "FIREFOX ACCESO — Marionette ascolta sulla $PORTA_M dopo $i s"
		exit 0
	fi
	if [ $i -gt 8 ] && ! pgrep -u "$UID_B" -f firefox >/dev/null 2>&1; then
		echo "FIREFOX MORTO dopo $i s — il suo registro:"
		tail -40 "$LOG"
		exit 4
	fi
	i=$((i + 1))
	sleep 1
done
echo "FIREFOX NON HA APERTO LA $PORTA_M in 60 s — vivo? $(pgrep -u "$UID_B" -f firefox | tr '\n' ' ')"
echo "il suo registro:"
tail -40 "$LOG"
exit 5
