#!/bin/bash
#
# REMOTIX - misura di calibrazione della qualita' video
# ======================================================
#
# Produce brevi filmati della stessa scena a risoluzioni diverse, tutti
# limitati alla stessa banda, per stabilire a occhio dove sta la soglia
# dell'accettabile. Il risultato fissa i punti di lavoro dell'adattamento
# automatico alla banda.
#
# Si esegue DENTRO il contenitore di sviluppo, come amministratore, perche'
# serve accedere ai nodi GPU:
#
#   bash /media/REMOTIX/enter.sh --root "bash /srv/remotix/calibrazione.sh"
#
#
# CRITERIO DELLA PROVA
# --------------------
# Ogni scena viene generata alla risoluzione NATIVA di destinazione, con i
# caratteri scalati in proporzione. Non si genera a 4K per poi rimpicciolire:
# un desktop che gira a 1080p disegna il testo con meno pixel per lettera, ed
# e' esattamente quella la perdita che si vuole giudicare.
#
# Le tre scene coprono i tre regimi che contano, e sono tutte rappresentative
# di un desktop vero. Si e' scartato l'uso di generatori sintetici: comprimono
# in modo diverso dal contenuto reale e falserebbero il giudizio.
#
#   A  documento          schermo quasi fermo, molto testo, cursore lampeggiante
#   B  scorrimento        lettura di una pagina: tutto lo schermo cambia
#   C  scorrimento veloce il caso peggiore realistico di un desktop
#
set -euo pipefail
export LC_ALL=C

OUT=/srv/remotix/calibrazione
DEV=/dev/dri/renderD128        # Intel iHD
BITRATE=10M
DURATA=8
FPS=30
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf

log() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }

mkdir -p "$OUT"
rm -f "$OUT"/*.mp4

[ -f "$FONT" ] || { echo "font assente: $FONT" >&2; exit 1; }
[ -c "$DEV" ]  || { echo "nodo GPU assente: $DEV" >&2; exit 1; }

# testo di riempimento, simile a una pagina di documentazione
TESTO=/tmp/pagina.txt
cat > "$TESTO" <<'TXT'
REMOTIX - server RDP per Linux
La qualita' percepita di un desktop remoto non dipende solo dalla banda
disponibile, ma da come quella banda viene spesa. Uno schermo fermo consuma
quasi nulla: si trasmettono soltanto le porzioni che cambiano. Uno schermo in
movimento pieno, al contrario, obbliga a ricodificare ogni fotogramma per
intero, ed e' li' che il limite si fa sentire.
Questa pagina serve a giudicare la nitidezza del testo. Le lettere piccole
sono la prova piu' severa per un codificatore video, perche' i bordi netti
sono proprio cio' che la compressione tende ad ammorbidire per primo. Il
sottocampionamento della crominanza, in particolare, riduce la risoluzione
del colore a meta': il testo nero su bianco ne soffre poco, quello colorato
molto di piu'.
Guardando questi filmati a schermo intero, la domanda a cui rispondere e'
semplice: a quale risoluzione il testo resta comodo da leggere, e dove invece
comincia a sfaldarsi. Quel confine e' il punto di lavoro che cerchiamo.
TXT

# ---------------------------------------------------------------------------
# genera_scena <scena> <larghezza> <altezza> <scala-carattere>
# ---------------------------------------------------------------------------
codifica() {
    local nome="$1" w="$2" h="$3" fs="$4" filtro="$5"
    local file="$OUT/${nome}_${h}p.mp4"
    # -t vincola SEMPRE la durata: alcuni filtri sono sorgenti infinite e
    # senza questo limite il file cresce senza fermarsi.
    ffmpeg -hide_banner -loglevel error -y \
        -vaapi_device "$DEV" \
        -f lavfi -i "color=c=0xf8f8f8:s=${w}x${h}:r=$FPS:d=$DURATA" \
        -vf "${filtro},format=nv12,hwupload" \
        -c:v h264_vaapi -profile:v high \
        -b:v "$BITRATE" -maxrate "$BITRATE" -bufsize 2M \
        -g $((FPS * 2)) -t "$DURATA" \
        "$file"
    ok "$(basename "$file")  ($(du -h "$file" | cut -f1))"
}

# ---------------------------------------------------------------------------
for res in "3840 2160 28" "2560 1440 19" "1920 1080 14"; do
    set -- $res
    W=$1 H=$2 FS=$3
    M=$((W / 32))          # margine proporzionale

    log "Risoluzione ${W}x${H}"

    # A - documento quasi fermo, con cursore lampeggiante
    codifica "A-documento" "$W" "$H" "$FS" \
"drawtext=fontfile=$FONT:textfile=$TESTO:fontsize=$FS:fontcolor=0x1a1a1a:x=$M:y=$M:line_spacing=$((FS/2)),\
drawtext=fontfile=$FONT:text='|':fontsize=$FS:fontcolor=0x0060c0:x=$((M+FS*20)):y=$((M+FS*30)):enable='lt(mod(t\,1)\,0.5)'"

    # B - la stessa pagina che scorre: cambia tutto lo schermo
    codifica "B-scorrimento" "$W" "$H" "$FS" \
"drawtext=fontfile=$FONT:textfile=$TESTO:fontsize=$FS:fontcolor=0x1a1a1a:x=$M:y=h-t*$((H/4)):line_spacing=$((FS/2))"

    # C - scorrimento veloce: il caso peggiore realistico di un desktop
    codifica "C-scorrimento-veloce" "$W" "$H" "$FS" \
"drawtext=fontfile=$FONT:textfile=$TESTO:fontsize=$FS:fontcolor=0x1a1a1a:x=$M:y=h-t*$H:line_spacing=$((FS/2))"
done

# ---------------------------------------------------------------------------
# Confronto hardware / software: la stessa scena, stessa banda, encoder x264.
# Serve perche' lo sviluppo parte in software, e conviene sapere quanto si
# perde o si guadagna rispetto alla GPU.
# ---------------------------------------------------------------------------
log "Confronto software (x264) a 4K"
ffmpeg -hide_banner -loglevel error -y \
    -f lavfi -i "color=c=0xf8f8f8:s=3840x2160:r=$FPS:d=$DURATA" \
    -vf "drawtext=fontfile=$FONT:textfile=$TESTO:fontsize=28:fontcolor=0x1a1a1a:x=120:y=h-t*540:line_spacing=14" \
    -c:v libx264 -preset veryfast -tune zerolatency \
    -b:v "$BITRATE" -maxrate "$BITRATE" -bufsize 2M -g $((FPS * 2)) \
    "$OUT/B-scorrimento_2160p_x264.mp4"
ok "B-scorrimento_2160p_x264.mp4  ($(du -h "$OUT/B-scorrimento_2160p_x264.mp4" | cut -f1))"

log "Fatto"
ls -1sh "$OUT"/*.mp4 | sed 's/^/    /'
printf '\n    Tutti i filmati sono limitati a %s. Vanno guardati A SCHERMO INTERO:\n' "$BITRATE"
printf '    e'\'' cosi'\'' che li vedresti in una sessione remota.\n\n'
