#!/bin/bash
# ===========================================================================
# 10-f2-testimone.sh — ⭐⭐ L'IMMAGINE DEL DESKTOP REMOTO, presa DAL FILO.
#
# ⛔ PERCHE' ESISTE.  Fino al 25 agosto 2026 nessuno aveva mai visto l'immagine
#    del desktop della sessione remota: si erano provate quattro strade — lo
#    scatto del figlio, la fotografia dello schermo (GNOME non la concede), la
#    tela letta dalla pagina, il conteggio dei fotogrammi — e ⛔ nessuna aveva
#    dato il quadro.  ⇒ Ogni giudizio sul browser era un'opinione.
#
# ⭐ LA STRADA CHE FUNZIONA ERA GIA' NEL CLIENTE DI PROVA: `--video-scrivi`
#    scrive i fotogrammi **cosi' come sono presi dal filo**, per darli a un
#    decodificatore terzo.  ⇒ `ffmpeg` li decodifica e ne escono dei PNG.
#    ⛔ E' il testimone piu' onesto che ci sia: non e' quel che il compositore
#       dice di avere in scena, e' **quel che arriva all'utente**.
#
#   uso:  10-f2-testimone.sh <UTENTE> <SECONDI> <CARTELLA_ESITO> [PORTA]
#
#   lascia in CARTELLA_ESITO:
#     video.h264      il flusso preso dal filo
#     scatto-NNN.png  i fotogrammi decodificati
#     cliente.log     quel che il cliente ha detto
#
# ⛔ Il cliente gira DENTRO il contenitore (`enter.sh`): fuori non c'e'
#    `aioquic`.  Dentro, `/media/REMOTIX` si vede come `/srv/remotix`.
# ⛔ E la parola d'ordine passa da `--parola-file`, non dalla riga di comando
#    (rilievo D12: `argv` lo legge chiunque faccia `ps`).
# ===========================================================================
set -uo pipefail

U=${1:?serve un utente}
SEC=${2:?servono i secondi}
ESITO=${3:?serve la cartella dove lasciare gli scatti}
PORTA=${4:-8420}

LAV=/media/REMOTIX/tmp/10f2
DENTRO_LAV=/srv/remotix/tmp/10f2
mkdir -p "$ESITO"
rm -f "$ESITO"/scatto-*.png "$ESITO/video.h264"
# ⚠ Dentro `enter.sh` (senza `--root`) si gira come l'utente di fuori, non come
#   root: se la cartella resta di root il cliente prende i fotogrammi e poi non
#   li sa scrivere — e il file mancante direbbe «il server non manda video» su
#   un server che lo manda.  ⇒ La cartella e la parola sono sue.
chown -R nicfio:nicfio "$ESITO"

REL=${ESITO#/media/REMOTIX/}
DENTRO_ESITO="/srv/remotix/$REL"

printf '%s\n' nicfio | bash /media/REMOTIX/enter.sh \
	"cd /srv/src/10f2-src/banchi && timeout $((SEC + 60)) python3 -u 01-b3-cliente.py \
	   --indirizzo 192.168.0.2 --porta $PORTA --utente $U \
	   --parola-file $DENTRO_LAV/parola \
	   --larghezza 1500 --altezza 864 --resta $SEC \
	   --video-scrivi $DENTRO_ESITO/video.h264" \
	>"$ESITO/cliente.log" 2>&1
ESC=$?

if [ ! -s "$ESITO/video.h264" ]; then
	# ⛔ `None` non e' zero: «non ho preso video» non e' «il desktop e' nero».
	echo "⛔ NON MISURATO: nessun video preso dal filo (uscita cliente $ESC)"
	tail -20 "$ESITO/cliente.log"
	exit 1
fi

# ⚠ `-vsync 0` e non un campionamento a tempo: si vuole OGNI fotogramma che il
#   server ha davvero mandato, non uno ricostruito da `ffmpeg` a ritmo fisso.
ffmpeg -hide_banner -loglevel error -f h264 -i "$ESITO/video.h264" \
	-vsync 0 "$ESITO/scatto-%03d.png" </dev/null
N=$(ls "$ESITO"/scatto-*.png 2>/dev/null | wc -l)
echo "⭐ $N scatti da $(stat -c %s "$ESITO/video.h264") byte di flusso (uscita cliente $ESC)"
grep -E '\[vid\]|SESSIONE|AMMESSO|attaccato' "$ESITO/cliente.log" | sed 's/^/   /'
