#!/bin/bash
# ===========================================================================
# 10-f2-scena.sh — ⭐⭐ LA SCENA CHE RISPONDE ALLA DOMANDA DEL REGISTA:
# «nel desktop remoto il browser si apre e si usa, si' o no?»
#
#   10-f2-scena.sh <UTENTE> <MODO> <PROGRAMMA...>
#
#   MODO = composto | menu | niente
#          `composto`  ambiente montato da zero (come i banchi hanno sempre
#                      fatto — `CODER.md` §4.5)
#          `menu`      dal gestore d'utente, cioe' come GNOME lancia dal menu
#          `niente`    non lancia niente: e' il CONTROLLO NEGATIVO, il desktop
#                      da solo
#
# ⛔⛔ LA REGOLA CHE IL COORDINAMENTO HA PAGATO, e che questa scena rispetta:
#     **il cliente resta attaccato per TUTTA la prova**.  Senza cliente Mutter
#     non consegna niente, il contatore dei fotogrammi resta fermo, e si
#     concluderebbe «il browser non disegna» per una ragione che non c'entra
#     col browser.  ⇒ Qui il cliente parte PRIMA del programma e muore DOPO.
#
# ⭐ E si guarda l'immagine, non il conteggio: `10-f2-testimone.sh` scrive i
#    PNG di quel che e' passato sul filo.  Una prova cieca in questo progetto
#    vale zero.
#
# variabili: SEC (def. 45) quanto resta attaccato il cliente
#            RITARDO (def. 8) dopo quanti secondi si lancia il programma
#            ESITO (def. /media/REMOTIX/tmp/10f2/scena)
#            PORTA (def. 8420)
# ===========================================================================
set -uo pipefail

U=${1:?serve un utente}
MODO=${2:?serve un modo}
shift 2

SEC=${SEC:-45}
RITARDO=${RITARDO:-8}
ESITO=${ESITO:-/media/REMOTIX/tmp/10f2/scena}
PORTA=${PORTA:-8420}
LAV=/media/REMOTIX/tmp/10f2
UID_U=$(id -u "$U") || exit 2

mkdir -p "$ESITO"
rm -f "$ESITO"/scatto-*.png "$ESITO/video.h264" "$ESITO/programma.log" \
      "$ESITO/globali-prima.json" "$ESITO/globali-dopo.json"
chown -R nicfio:nicfio "$ESITO"

REL=${ESITO#/media/REMOTIX/}
DENTRO_ESITO="/srv/remotix/$REL"

# ── 1. che cosa vede un client Wayland PRIMA ────────────────────────────────
bash /media/REMOTIX/tmp/10f2/10-f2-dentro.sh "$U" composto \
	/usr/bin/python3 "$LAV/10-f2-globali.py" --taratura --json \
	>"$ESITO/globali-prima.json" 2>&1

# ── 2. il cliente parte e RESTA ATTACCATO per tutta la prova ────────────────
printf '%s\n' nicfio | bash /media/REMOTIX/enter.sh \
	"cd /srv/src/10f2-src/banchi && timeout $((SEC + 60)) python3 -u 01-b3-cliente.py \
	   --indirizzo 192.168.0.2 --porta $PORTA --utente $U \
	   --parola-file /srv/remotix/tmp/10f2/parola \
	   --larghezza 1500 --altezza 864 --resta $SEC \
	   --video-scrivi $DENTRO_ESITO/video.h264" \
	>"$ESITO/cliente.log" 2>&1 &
PID_CLIENTE=$!

# ⚠ Si aspetta che la sessione sia DAVVERO su: il cliente scrive «SESSIONE»
#   quando il palco c'e'.  Lanciare il programma prima vorrebbe dire misurare
#   una corsa invece del browser.
i=0
while [ $i -lt 400 ]; do
	grep -q '⭐ SESSIONE' "$ESITO/cliente.log" 2>/dev/null && break
	i=$((i + 1)); sleep 0.1
done
if ! grep -q '⭐ SESSIONE' "$ESITO/cliente.log" 2>/dev/null; then
	echo "⛔ NON MISURO: la sessione non e' salita in 40 s"
	tail -10 "$ESITO/cliente.log"; kill $PID_CLIENTE 2>/dev/null; exit 1
fi
echo "⭐ sessione su; aspetto $RITARDO s prima di lanciare"
sleep "$RITARDO"

# ── 3. il programma ─────────────────────────────────────────────────────────
if [ "$MODO" != niente ]; then
	setsid bash /media/REMOTIX/tmp/10f2/10-f2-dentro.sh "$U" "$MODO" "$@" \
		>"$ESITO/programma.log" 2>&1 &
	PID_PROG=$!
	echo "⭐ lanciato ($MODO): $*"
else
	echo "⭐ CONTROLLO NEGATIVO: non lancio niente"
fi

# ── 4. si aspetta che il cliente finisca la sua finestra ────────────────────
wait $PID_CLIENTE
ESC=$?

# ── 5. che cosa vede un client Wayland DOPO ─────────────────────────────────
bash /media/REMOTIX/tmp/10f2/10-f2-dentro.sh "$U" composto \
	/usr/bin/python3 "$LAV/10-f2-globali.py" --taratura --json \
	>"$ESITO/globali-dopo.json" 2>&1

# ── 6. quanti processi del programma sono vivi ──────────────────────────────
if [ "$MODO" != niente ]; then
	echo "processi vivi dell'utente:"
	ps -u "$U" -o pid,etime,comm --no-headers | sed 's/^/   /' | head -30
fi

# ── 7. l'immagine ───────────────────────────────────────────────────────────
if [ ! -s "$ESITO/video.h264" ]; then
	echo "⛔ NON MISURATO: nessun video preso dal filo (uscita cliente $ESC)"
	tail -20 "$ESITO/cliente.log"; exit 1
fi
ffmpeg -hide_banner -loglevel error -f h264 -i "$ESITO/video.h264" \
	-vsync 0 "$ESITO/scatto-%03d.png" </dev/null
N=$(ls "$ESITO"/scatto-*.png 2>/dev/null | wc -l)
echo "⭐ $N scatti da $(stat -c %s "$ESITO/video.h264") byte (uscita cliente $ESC)"
grep -E '\[vid\]|SESSIONE|AMMESSO|attaccato|caduta' "$ESITO/cliente.log" | sed 's/^/   /'
