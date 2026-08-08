#!/bin/bash
#
# Prova della fase 9: l'accelerazione hardware.
#
#   bash /media/REMOTIX/src/remotix-c/prove/fase9.sh base    prende la LINEA DI BASE
#   bash /media/REMOTIX/src/remotix-c/prove/fase9.sh dopo    rimisura e confronta
#   bash /media/REMOTIX/src/remotix-c/prove/fase9.sh gpu     accerta che la GPU sia nella VM
#   bash /media/REMOTIX/src/remotix-c/prove/fase9.sh confronto   le tre strade, una dopo l'altra
#   bash /media/REMOTIX/src/remotix-c/prove/fase9.sh copia-zero  la cattura senza copie, sul
#                                                               desktop vero, e il ritorno in
#                                                               memoria per chi i pixel li vuole li'
#
# ⚠ QUESTO BANCO NON PROVA CHE QUALCOSA FUNZIONI: MISURA QUANTO COSTA.
#
#   La fase 9 promette «a parita' di scena, il consumo di CPU crolla».  Una
#   frase del genere non si collauda con un controllo verde o rosso: si collauda
#   con due numeri presi nelle stesse condizioni, prima e dopo.  Per questo il
#   modo «base» non fallisce mai — scrive una scheda su disco — e il modo «dopo»
#   e' l'unico che boccia, confrontandosi con quella scheda.
#
# ⚠ SI USA LA SCENA SINTETICA, COME IN FASE 7, E PER LA STESSA RAGIONE.
#
#   Quel che si misura e' il costo del CODIFICATORE, e serve un produttore che
#   non si fermi mai: un desktop vero e fermo non manda niente, e un desktop
#   vero e vivo (un video, una pagina che scorre) cambia da un giro all'altro,
#   quindi «a parita' di scena» sarebbe falso.  La scena sintetica disegna la
#   stessa cosa trenta volte al secondo per sempre.
#
#   Il prezzo, ed e' dichiarato: il numero comprende anche il disegno della
#   scena, che c'e' prima e dopo.  Non e' il costo del solo codificatore, e' il
#   costo del server a parita' di tutto il resto — che e' la grandezza di cui
#   parla il piano.
#
# ⚠ SI MISURANO ENTRAMBI I CODEC, E IL SECONDO NON DEVE CAMBIARE.
#
#   L'accelerazione tocca AVC420, cioe' Windows e Linux.  Android riceve
#   RemoteFX Progressive, che e' un codec a wavelet e resta in CPU: non esiste
#   un encoder wavelet in GPU.  Misurarlo serve a due cose: dire quanto vale
#   davvero il guadagno sul parco client, e accorgersi se la fase 9 avesse
#   rallentato il percorso che non doveva toccare.
#
# ⚠ LE REGOLE DI BANCO GIA' PAGATE, che valgono anche qui:
#   - `ssh` senza `</dev/null` eredita lo standard input dello script e la
#     sessione remota non torna (fase 4);
#   - l'uscita di `enter.sh` non si mette mai in una pipe: `sudo` chiede la
#     password e chi la deve dare resta appeso in silenzio (fase 1);
#   - `pkill -f` si ancora con `^`, o uccide la shell che lo esegue (fase 3);
#   - alla fine il servizio della VM si rimette come lo si e' trovato, con PAM e
#     senza scena sintetica: una prova che lascia la macchina muta costa una
#     diagnosi ogni volta (§8.6 di REFERENCE.md).
set -u

BASE=/media/REMOTIX
BIN_LOCALE="$BASE/src/remotix-c/build/src/remotix"
PORTA=3389
DISPLAY_CLI=:112
BANCO=/srv/remotix/tmp/banco-b
BANCO_FUORI=/media/REMOTIX/tmp/banco-b
SCHEDE="$BASE/tmp/fase9-misure"

# La misura del desktop.  E' quella del carico di riferimento della fase 8 —
# RDM a 2560x984 — perche' e' l'unica misura di cui esista gia' un «prima»
# osservato su una sessione vera.
MISURA=${MISURA:-2560x984}
# Quanto dura una finestra di misura.  Venti secondi: sotto, il ritmo del
# regolatore e le sonde di rete pesano troppo sul conto; sopra, non si impara
# niente di nuovo.
FINESTRA=${FINESTRA:-20}
# Quanto si aspetta dopo il collegamento prima di cominciare a contare.  Il
# primo fotogramma e' un keyframe, la negoziazione EGFX costa, e il regolatore
# parte con la soglia al minimo: contare li' misurerebbe l'avvio, non il regime.
SCALDA=${SCALDA:-6}

# Da dove si comanda la macchina di runtime: dal 6 agosto 2026 e' il server
# stesso (§6.2 di SPECIFICA.md).  `RUNTIME=vm` riporta i banchi sulla VM.
. "$(dirname "$0")/runtime.sh"
cnt() { bash "$BASE/enter.sh" "$@"; }

titolo() { printf '\n\033[1;34m==> %s\033[0m\n' "$*"; }
ok()     { printf '    \033[1;32mOK\033[0m    %s\n' "$*"; }
ko()     { printf '    \033[1;31mNO\033[0m    %s\n' "$*"; GUASTI=$((GUASTI+1)); }
inf()    { printf '    --    %s\n' "$*"; }
GUASTI=0

MODO=${1:-base}
mkdir -p "$SCHEDE" "$BANCO_FUORI"

# ===========================================================================
# Gli script che girano DENTRO il contenitore: il client di prova.
# ===========================================================================
# Lo schermo dell'Xvfb e' piu' grande della finestra chiesta: xfreerdp3 apre una
# finestra della misura richiesta e, se non ci sta, la ridimensiona da se' —
# cioe' cambierebbe la misura che si sta misurando, e in silenzio.
cat > "$BANCO_FUORI/fase9-client.sh" <<CLIENT
#!/bin/bash
# \$1 = codec (AVC420 | RFX)   \$2 = nome del registro del client
set -u
pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
Xvfb $DISPLAY_CLI -screen 0 3000x1400x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
cd $BANCO || exit 1
rm -f "\$2"
setsid nohup env DISPLAY=$DISPLAY_CLI xfreerdp3 /v:127.0.0.1:$PORTA /gfx:\$1 \\
    /cert:ignore /sec:tls /u:prova /p:prova /size:$MISURA \\
    /title:REMOTIXFASE9 /log-level:INFO >"\$2" 2>&1 </dev/null &
sleep 5
pgrep -x xfreerdp3 >/dev/null && echo "   client collegato in \$1" || echo "   client NON partito"
CLIENT

cat > "$BANCO_FUORI/fase9-chiudi.sh" <<CHIUDI
#!/bin/bash
set -u
pkill -x xfreerdp3 2>/dev/null
pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null
sleep 1
echo "   banco del contenitore sgombrato"
CHIUDI

# ===========================================================================
# Le funzioni di misura.
# ===========================================================================

# Il tempo di CPU dell'intero processo, in tick, e i fotogrammi spediti.
#
# ⛔ I campi 14 e 15 di /proc/PID/stat sono la somma di TUTTI i thread del
#    gruppo, non del solo principale.  E' quello che serve: il codificatore, la
#    cattura e il ciclo della connessione stanno su thread diversi, e un conto
#    che ne guardasse uno solo direbbe che la fase 9 non ha cambiato niente.
campione() { # -> "tick fotogrammi"
    vm "PID=\$(systemctl show -p MainPID --value remotix.service); \
        [ \"\$PID\" = 0 ] && { echo '0 0'; exit 0; }; \
        T=\$(awk '{print \$14+\$15}' /proc/\$PID/stat); \
        F=\$(grep -F 'rete: RTT' ~/remotix.log | tail -1 \
            | grep -oE 'spediti [0-9]+' | grep -oE '[0-9]+'); \
        echo \"\${T:-0} \${F:-0}\"" 2>/dev/null | tr -d '\r' | tail -1
}

# I tre thread che consumano di piu', con il nome che si sono dati.  Non e' un
# controllo: e' l'informazione che dice DOVE va la CPU, ed e' quella che
# distinguera' «il codificatore e' passato in GPU» da «il conto totale e' calato
# per un altro motivo».
thread_grossi() {
    vm "PID=\$(systemctl show -p MainPID --value remotix.service); \
        [ \"\$PID\" = 0 ] && exit 0; \
        for t in /proc/\$PID/task/*; do \
            awk '{n=\$2; gsub(/[()]/,\"\",n); print \$14+\$15, n}' \$t/stat; \
        done | sort -rn | head -3" 2>/dev/null | tr -d '\r'
}

avvia_server_vm() { # $1 = opzioni in piu' per REMOTIX
    vm "printf 'REMOTIX_OPZIONI=--registro diagnostica --senza-autenticazione --immagine-di-prova $1\n' \
        | sudo tee /etc/default/remotix >/dev/null; rm -f ~/remotix.log; \
        sudo systemctl restart remotix.service; sleep 3; \
        systemctl is-active --quiet remotix.service && echo VIVO" | grep -q VIVO
}

# Una finestra di misura completa, per un codec.  Scrive una riga di scheda.
misura_codec() { # $1 = AVC420|RFX   $2 = etichetta della scheda   $3 = codificatore (facoltativo)
    local codec="$1" etichetta="$2" quale="${3:-}"
    local t0 t1 tick0 tick1 fot0 fot1 dt dtick dfot centesimi fps cpu_per_fot clk opzioni=""

    [ -n "$quale" ] && opzioni="--codificatore $quale"
    avvia_server_vm "$opzioni" || { ko "REMOTIX non e' partito nella VM"; return 1; }
    cnt "bash $BANCO/fase9-client.sh $codec fase9-$codec.log"

    inf "scaldo per $SCALDA secondi, poi conto per $FINESTRA"
    sleep "$SCALDA"

    t0=$(date +%s); read -r tick0 fot0 <<<"$(campione)"
    sleep "$FINESTRA"
    t1=$(date +%s); read -r tick1 fot1 <<<"$(campione)"

    dt=$(( t1 - t0 ))
    dtick=$(( tick1 - tick0 ))
    dfot=$(( fot1 - fot0 ))
    clk=$(vm "getconf CLK_TCK" | tr -d '\r' | tail -1)
    clk=${clk:-100}

    if [ "$dfot" -le 0 ]; then
        ko "$codec: nessun fotogramma spedito nella finestra — la misura non misura niente"
        cnt "bash $BANCO/fase9-chiudi.sh"
        return 1
    fi

    # Centesimi di core: il tempo di CPU consumato diviso il tempo trascorso.
    # Su quattro vCPU, 400 significa la macchina intera.
    centesimi=$(( dtick * 100 / clk * 100 / dt ))
    fps=$(( dfot * 10 / dt ))                      # decimi di fotogramma al secondo
    cpu_per_fot=$(( dtick * 1000 / clk / dfot ))   # millisecondi di CPU per fotogramma

    printf '%s\n' "codec=$codec codificatore=${quale:-auto} misura=$MISURA finestra=${dt}s \
fotogrammi=$dfot fps=$((fps/10)).$((fps%10)) cpu_centesimi_di_core=$centesimi \
cpu_ms_per_fotogramma=$cpu_per_fot" | tr -s ' ' >> "$SCHEDE/$etichetta.txt"

    ok "$codec/${quale:-auto}: $((fps/10)).$((fps%10)) fotogrammi/s, CPU $((centesimi/100)),$(printf '%02d' $((centesimi%100))) core, $cpu_per_fot ms di CPU per fotogramma"
    # ⛔ Non basta CHIEDERE un codificatore: bisogna leggere quale si e' aperto.
    #    Un ripiego silenzioso darebbe due misure diverse sotto la stessa
    #    etichetta, che e' peggio di non misurare — per questo il codice non
    #    ripiega quando il nome e' esplicito, e per questo il banco lo verifica
    #    lo stesso.
    STRADA=$(vm "grep -F 'codificatore:' ~/remotix.log | tail -1 | sed 's/.*codificatore: //'" | tr -d '\r' | tail -1)
    inf "strada presa: ${STRADA:-non dichiarata}"
    inf "thread piu' grossi (tick, nome):"
    thread_grossi | while read -r riga; do inf "    $riga"; done

    cnt "bash $BANCO/fase9-chiudi.sh"
    return 0
}

ripristina() {
    vm "printf 'REMOTIX_OPZIONI=--registro diagnostica\n' | sudo tee /etc/default/remotix >/dev/null; \
        sudo systemctl restart remotix.service; sleep 2; \
        systemctl is-active --quiet remotix.service && echo RIPRISTINATO" 2>&1 \
        | grep -q RIPRISTINATO \
        && inf "servizio rimesso in piedi con PAM e senza scena sintetica" \
        || inf "ATTENZIONE: il servizio nella VM non e' ripartito"
}

# ===========================================================================
# L'ambiente, che va scritto accanto ai numeri.
# ===========================================================================
# Un numero senza la macchina su cui e' stato preso non e' confrontabile con
# niente: §8.6-bis di REFERENCE.md esiste per questo.
scheda_ambiente() { # $1 = etichetta
    {
        echo "# scheda presa il $(date '+%Y-%m-%d %H:%M:%S')"
        echo "vcpu=$(vm 'nproc' | tr -d '\r' | tail -1)"
        echo "kernel=$(vm 'uname -r' | tr -d '\r' | tail -1)"
        echo "gpu=$(vm 'ls /dev/dri 2>/dev/null | tr "\n" " " || echo assente' | tr -d '\r' | tail -1)"
        echo "vainfo=$(vm 'command -v vainfo >/dev/null && vainfo 2>/dev/null | grep -c EncSlice || echo 0' | tr -d '\r' | tail -1)"
        echo "remotix=$(vm '~/remotix --versione 2>/dev/null | head -1' | tr -d '\r' | tail -1)"
    } > "$SCHEDE/$1.txt"
}

[ -x "$BIN_LOCALE" ] || { echo "manca $BIN_LOCALE: costruiscilo prima"; exit 1; }
bash "$BASE/enter.sh" true || exit 1

# ===========================================================================
case "$MODO" in
base|dopo)
# ===========================================================================
titolo "Fase 9 — misura «$MODO»: quanto costa il server a parita' di scena"

vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
copia "$BIN_LOCALE" >/dev/null || exit 1

scheda_ambiente "$MODO"
inf "ambiente: $(tr '\n' ' ' < "$SCHEDE/$MODO.txt")"

titolo "1. AVC420 — il percorso che la fase 9 accelera"
misura_codec AVC420 "$MODO" "${CODIFICATORE:-}"

titolo "2. RemoteFX Progressive — il percorso di Android, che resta in CPU"
misura_codec RFX "$MODO"

titolo "Riepilogo"
ripristina
inf "scheda scritta in $SCHEDE/$MODO.txt"
cat "$SCHEDE/$MODO.txt" | sed 's/^/    /'

if [ "$MODO" = dopo ] && [ -f "$SCHEDE/base.txt" ]; then
    titolo "Il confronto: prima e dopo"
    for c in AVC420 RFX; do
        P=$(grep -h "codec=$c " "$SCHEDE/base.txt" | tail -1 \
            | grep -oE 'cpu_centesimi_di_core=[0-9]+' | grep -oE '[0-9]+')
        D=$(grep -h "codec=$c " "$SCHEDE/dopo.txt" | tail -1 \
            | grep -oE 'cpu_centesimi_di_core=[0-9]+' | grep -oE '[0-9]+')
        if [ -z "${P:-}" ] || [ -z "${D:-}" ]; then
            ko "$c: manca uno dei due termini di paragone"
            continue
        fi
        inf "$c: CPU $((P/100)),$(printf '%02d' $((P%100))) core → $((D/100)),$(printf '%02d' $((D%100))) core"
        if [ "$c" = AVC420 ]; then
            # Il numero che il piano chiede: «il consumo di CPU crolla».  Meno
            # trenta per cento e' la soglia sotto la quale il guadagno non vale
            # una fase — e va detto, non nascosto in un pareggio.
            if [ "$D" -lt $(( P * 70 / 100 )) ]; then
                ok "AVC420: il consumo di CPU e' calato di almeno il 30%"
            else
                ko "AVC420: il consumo non e' calato abbastanza ($P → $D centesimi di core)"
            fi
        else
            # Il percorso che non si doveva toccare: che sia rimasto uguale e'
            # un controllo di non regressione, non un guadagno.
            if [ "$D" -le $(( P * 120 / 100 )) ]; then
                ok "RFX Progressive: invariato, come atteso (non si accelera in GPU)"
            else
                ko "RFX Progressive: e' PEGGIORATO ($P → $D centesimi di core)"
            fi
        fi
    done
fi
;;

# ===========================================================================
gpu)
# ===========================================================================
titolo "Fase 9 — la GPU e' arrivata dentro la VM?"

# Tre domande in fila, e ognuna esclude una causa diversa: il dispositivo
# c'e'? il driver del kernel lo ha preso? VA-API ci sa CODIFICARE?
#
# La terza non e' una formalita': un nodo /dev/dri che esiste e un driver che
# si carica non dicono niente sull'encoder — su una scheda senza motore di
# codifica, o con il driver sbagliato, vainfo elenca solo profili di decodifica
# e la fase 9 non avrebbe dove appoggiarsi.
NODI=$(vm 'ls /dev/dri 2>/dev/null | tr "\n" " "' | tr -d '\r' | tail -1)
if printf '%s' "$NODI" | grep -q renderD; then
    ok "la VM ha un nodo di rendering: $NODI"
else
    ko "nessun nodo di rendering nella VM (/dev/dri: ${NODI:-vuoto})"
fi

DRV=$(vm 'for d in /sys/class/drm/card*/device/driver; do readlink -f $d 2>/dev/null | xargs -r basename; done | sort -u | tr "\n" " "' | tr -d '\r' | tail -1)
inf "driver DRM nella VM: ${DRV:-nessuno}"

# ⛔ SI INTERROGA OGNI NODO, NON «IL» NODO.
#
#    `vainfo` senza argomenti prende il primo che trova, e il primo qui e'
#    virtio-gpu — che non codifica niente e risponde «init failed». Chi si
#    fermasse a quella riga concluderebbe che il passthrough non ha funzionato,
#    mentre la scheda buona e' il nodo dopo. Costato un controllo rosso il
#    6 agosto, con la GPU gia' in funzione.
ENC=$(vm 'for n in /dev/dri/renderD*; do
              r=$(vainfo --display drm --device $n 2>/dev/null | grep -E "H264(High|Main).*Enc" | head -2)
              [ -n "$r" ] && echo "$n: $(echo $r | tr -s " ")"
          done' | tr -d '\r')
if [ -n "$ENC" ]; then
    ok "VA-API sa codificare H.264:"
    printf '%s\n' "$ENC" | while read -r r; do inf "    $r"; done
    # L'entrypoint conta: le Intel recenti offrono solo la variante a basso
    # consumo (VDEnc). Un codificatore che chiedesse quella classica troverebbe
    # «unsupported entrypoint» e ripiegherebbe in CPU senza dirlo forte.
    printf '%s' "$ENC" | grep -q EncSliceLP \
        && inf "entrypoint a basso consumo (EncSliceLP): il codificatore va aperto con low_power"
else
    ko "nessun nodo offre entrypoint di codifica H.264"
    inf "$(vm 'for n in /dev/dri/renderD*; do echo "$n: $(vainfo --display drm --device $n 2>&1 | grep -E "Driver version|error" | head -1)"; done' | tr -d '\r')"
fi

COD=$(vm 'command -v ffmpeg >/dev/null 2>&1 && ffmpeg -hide_banner -encoders 2>/dev/null | grep -E "h264_(vaapi|qsv|nvenc)|libx264" | tr -s " "' | tr -d '\r')
if [ -n "$COD" ]; then
    ok "codificatori disponibili a libavcodec nella VM:"
    printf '%s\n' "$COD" | while read -r r; do inf "    $r"; done
else
    inf "ffmpeg non e' nella VM: il controllo dei codificatori si fara' dal registro di REMOTIX"
fi
;;

# ===========================================================================
confronto)
# ===========================================================================
# Il confronto che la fase 9 deve consegnare: la stessa scena, la stessa
# misura, la stessa macchina, e tre strade diverse per arrivare in fondo.
#
# `freerdp` e' il «prima» — il percorso delle fasi 2-8, che chiama
# `avc420_compress`; `libx264` e' lo stesso lavoro fatto da noi in CPU, e serve
# a separare «abbiamo cambiato libreria» da «abbiamo tolto la codifica dalla
# CPU»; `h264_vaapi` e' il «dopo».  Senza quello di mezzo, un guadagno si
# potrebbe attribuire alla GPU quando invece viene da un'altra impostazione.
titolo "Fase 9 — confronto fra le tre strade, a parita' di scena"

vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
copia "$BIN_LOCALE" >/dev/null || exit 1

rm -f "$SCHEDE/confronto.txt"
scheda_ambiente confronto
inf "ambiente: $(tr '\n' ' ' < "$SCHEDE/confronto.txt")"

for QUALE in freerdp libx264 h264_vaapi; do
    titolo "AVC420 con $QUALE"
    misura_codec AVC420 confronto "$QUALE"
done

titolo "RemoteFX Progressive (il percorso di Android: non si accelera)"
misura_codec RFX confronto

titolo "Riepilogo"
ripristina
printf '\n'
grep -h '^codec=' "$SCHEDE/confronto.txt" | while read -r r; do inf "$r"; done

# Il giudizio, e non e' una formalita': il piano promette «a parita' di scena,
# il consumo di CPU crolla».  Meno trenta per cento e' la soglia sotto la quale
# il guadagno non varrebbe una fase.
P=$(grep -h 'codificatore=freerdp' "$SCHEDE/confronto.txt" | tail -1 \
    | grep -oE 'cpu_centesimi_di_core=[0-9]+' | grep -oE '[0-9]+')
D=$(grep -h 'codificatore=h264_vaapi' "$SCHEDE/confronto.txt" | tail -1 \
    | grep -oE 'cpu_centesimi_di_core=[0-9]+' | grep -oE '[0-9]+')
if [ -n "${P:-}" ] && [ -n "${D:-}" ]; then
    inf "AVC420: CPU $((P/100)),$(printf '%02d' $((P%100))) core in CPU → $((D/100)),$(printf '%02d' $((D%100))) core in GPU"
    if [ "$D" -lt $(( P * 70 / 100 )) ]; then
        ok "il consumo di CPU e' calato di almeno il 30%"
    else
        ko "il consumo non e' calato abbastanza: $P → $D centesimi di core"
    fi
else
    ko "manca uno dei due termini di paragone"
fi
;;

# ===========================================================================
copia-zero)
# ===========================================================================
# La cattura a copia zero: quanto vale, e che non rompe il percorso di Android.
#
# ⚠ QUI LA SCENA SINTETICA NON SERVE, ed e' l'unico modo di questo banco in cui
#   e' cosi'.  La scena la disegniamo noi in memoria: un caricamento sulla
#   scheda lo pagherebbe sempre, quindi misurarla direbbe zero sul pezzo che
#   questa parte della fase 9 toglie.  Serve il DESKTOP VERO, dove i pixel
#   arrivano gia' dal compositore, e serve mosso — un desktop fermo non manda
#   niente (R9).  Lo si muove battendo tasti dal client, come in fase 4.
#
# ⚠ E QUI I CONTROLLI SONO VERDI O ROSSI, al contrario del resto del banco.
#   La misura del guadagno e' solo meta' del lavoro; l'altra meta' e' che il
#   palco sappia TORNARE IN MEMORIA quando si collega un client che i pixel li
#   vuole in CPU.  Quello non e' un numero: o funziona o e' schermo fermo, e
#   schermo fermo e' esattamente cio' che non da' errore.
titolo "Fase 9 — la cattura a copia zero, sul desktop vero"

vm "sudo systemctl stop remotix.service 2>/dev/null; sleep 1" >/dev/null 2>&1
copia "$BIN_LOCALE" >/dev/null || exit 1

MISURA_VERA=${MISURA_VERA:-1600x900}

# Il client sul desktop vero: come quello della scena sintetica, ma il server
# non ha `--immagine-di-prova`.
cat > "$BANCO_FUORI/fase9-vero.sh" <<VERO
#!/bin/bash
# \$1 = codec (AVC420 | RFX)   \$2 = nome del registro del client
set -u
pkill -x xfreerdp3 2>/dev/null
pkill -f '^Xvfb $DISPLAY_CLI' 2>/dev/null; sleep 1
Xvfb $DISPLAY_CLI -screen 0 3000x1400x24 -nolisten tcp >/dev/null 2>&1 &
sleep 2
cd $BANCO || exit 1
rm -f "\$2"
# `/dynamic-resolution` serve alla sezione 5: senza, trascinare la finestra non
# manda alcun MONITOR_LAYOUT e il ridimensionamento non si puo' nemmeno provare.
# Alle altre sezioni non cambia niente, perche' la finestra non si tocca.
setsid nohup env DISPLAY=$DISPLAY_CLI xfreerdp3 /v:127.0.0.1:$PORTA /gfx:\$1 \\
    /cert:ignore /sec:tls /u:prova /p:prova /size:$MISURA_VERA /dynamic-resolution \\
    /title:REMOTIXFASE9 /log-level:INFO >"\$2" 2>&1 </dev/null &
sleep 8
pgrep -x xfreerdp3 >/dev/null && echo "   client collegato in \$1" || echo "   client NON partito"
VERO

# La scena mossa: gli stessi tasti, ogni volta.  «A parita' di scena» qui
# significa questo, e per questo i tasti non cambiano fra un giro e l'altro.
cat > "$BANCO_FUORI/fase9-muovi.sh" <<MUOVI
#!/bin/bash
# \$1 = quante raffiche
#
# ⛔ IL FUOCO SI DA' CON \`windowfocus\`, NON CON \`windowactivate\`.
#
#    \`windowactivate\` parla al gestore di finestre via EWMH, e qui un gestore
#    di finestre non c'e': fallisce in silenzio, i tasti vanno al fuoco corrente
#    — che dopo un \`windowsize\` non e' piu' la nostra finestra — e la scena non
#    si muove.  Il banco allora conta zero fotogrammi e accusa il prodotto di
#    avere lo schermo fermo.  Costato un controllo rosso il 6 agosto, con il
#    codice giusto.  \`windowfocus\` usa \`XSetInputFocus\` e non chiede permesso
#    a nessuno; il puntatore dentro la finestra chiude il caso.
set -u
export DISPLAY=$DISPLAY_CLI
ID=\$(xdotool search --name REMOTIXFASE9 | head -1)
if [ -z "\$ID" ]; then
    echo "   NESSUNA FINESTRA: la scena non si muovera'"
    exit 1
fi
xdotool windowfocus --sync "\$ID" 2>/dev/null
xdotool mousemove --window "\$ID" 60 60 2>/dev/null
xdotool key super; sleep 1
for i in \$(seq 1 \$1); do
    xdotool type --delay 25 'remotix fase nove'
    xdotool key BackSpace BackSpace BackSpace BackSpace
done
echo "   scena mossa (\$1 raffiche)"
MUOVI

# Avvia il server sul DESKTOP VERO, con la strada dei pixel scelta.
avvia_desktop_vero() { # $1 = 0|1 copia zero   $2 = opzioni in piu'
    vm "printf 'REMOTIX_OPZIONI=--registro diagnostica --senza-autenticazione $2\nREMOTIX_DMABUF=$1\n' \
        | sudo tee /etc/default/remotix >/dev/null; rm -f ~/remotix.log; \
        sudo systemctl restart remotix.service; sleep 4; \
        systemctl is-active --quiet remotix.service && echo VIVO" | grep -q VIVO
}

# ⛔ IL PATTERN SI ESPANDE QUI, NON DI LA'.
#
#    Scritto `\"\$1\"` il dollaro arriva intatto alla shell remota, dove `$1`
#    non esiste: `grep -E ''` trova TUTTO, e ogni controllo diventa verde o
#    rosso a caso — qui fu rosso, e per un attimo sembrava un difetto del
#    prodotto.  E' l'altra faccia della regola gia' scritta in fase 4: una prova
#    che boccia il codice giusto costa quanto una che promuove quello sbagliato.
registro() { # $1 = pattern
    vm "grep -E '$1' ~/remotix.log | tail -6" 2>/dev/null | tr -d '\r'
}

# Un giro completo: si collega, si muove la scena, si contano CPU e fotogrammi.
giro_vero() { # $1 = 0|1 copia zero   $2 = etichetta
    local dma="$1" etichetta="$2"
    local t0 t1 tick0 tick1 fot0 fot1 dt dtick dfot clk centesimi cpu_per_fot

    avvia_desktop_vero "$dma" "" || { ko "$etichetta: REMOTIX non e' partito"; return 1; }
    cnt "bash $BANCO/fase9-vero.sh AVC420 fase9-vero-$etichetta.log"
    sleep 3

    t0=$(date +%s); read -r tick0 fot0 <<<"$(campione)"
    cnt "bash $BANCO/fase9-muovi.sh 30"
    t1=$(date +%s); read -r tick1 fot1 <<<"$(campione)"

    dt=$(( t1 - t0 )); [ "$dt" -lt 1 ] && dt=1
    dtick=$(( tick1 - tick0 ))
    dfot=$(( fot1 - fot0 ))
    clk=$(vm "getconf CLK_TCK" | tr -d '\r' | tail -1); clk=${clk:-100}

    if [ "$dfot" -le 0 ]; then
        ko "$etichetta: nessun fotogramma spedito — la misura non misura niente"
        cnt "bash $BANCO/fase9-chiudi.sh"
        return 1
    fi

    centesimi=$(( dtick * 100 / clk * 100 / dt ))
    cpu_per_fot=$(( dtick * 1000 / clk / dfot ))
    printf 'strada=%s durata=%ss fotogrammi=%s cpu_centesimi_di_core=%s cpu_ms_per_fotogramma=%s\n' \
        "$etichetta" "$dt" "$dfot" "$centesimi" "$cpu_per_fot" >> "$SCHEDE/copia-zero.txt"

    ok "$etichetta: $dfot fotogrammi in ${dt}s, CPU $((centesimi/100)),$(printf '%02d' $((centesimi%100))) core, $cpu_per_fot ms di CPU per fotogramma"
    registro 'i fotogrammi arrivano come' | tail -1 | sed 's/^/    --    /'
    cnt "bash $BANCO/fase9-chiudi.sh"
    return 0
}

rm -f "$SCHEDE/copia-zero.txt"
scheda_ambiente copia-zero
inf "ambiente: $(tr '\n' ' ' < "$SCHEDE/copia-zero.txt")"
rm -f "$SCHEDE/copia-zero.txt"

titolo "1. Quanto costa un fotogramma, per le due strade"
giro_vero 0 in-memoria
giro_vero 1 copia-zero

M=$(grep -h 'strada=in-memoria' "$SCHEDE/copia-zero.txt" 2>/dev/null | tail -1 \
    | grep -oE 'cpu_ms_per_fotogramma=[0-9]+' | grep -oE '[0-9]+')
Z=$(grep -h 'strada=copia-zero' "$SCHEDE/copia-zero.txt" 2>/dev/null | tail -1 \
    | grep -oE 'cpu_ms_per_fotogramma=[0-9]+' | grep -oE '[0-9]+')
if [ -n "${M:-}" ] && [ -n "${Z:-}" ] && [ "$M" -gt 0 ]; then
    inf "costo per fotogramma: $M ms → $Z ms di CPU"
    # La soglia e' larga apposta.  La misura a mano del 6 agosto diceva 25 → 7 ms,
    # cioe' meno settantadue per cento; chiedere meno quaranta lascia spazio a una
    # macchina piu' carica senza accettare un pareggio travestito da guadagno.
    if [ "$Z" -lt $(( M * 60 / 100 )) ]; then
        ok "la copia zero toglie almeno il 40% del costo per fotogramma"
    else
        ko "la copia zero non ha tolto abbastanza: $M → $Z ms per fotogramma"
    fi
else
    ko "manca uno dei due termini di paragone"
fi

# ===========================================================================
titolo "2. Il palco torna in memoria per chi i pixel li vuole in CPU"
# ===========================================================================
# ⛔ E' IL CONTROLLO CHE GUARDA LA STRADA DI ANDROID.
#
#    Il palco che lavora sulla scheda non ha pixel in memoria; RemoteFX
#    Progressive — l'unico codec che RDM decodifica (§1.4 di REFERENCE.md) — li
#    vuole li'.  Senza il ritorno in memoria un client Android collegato con la
#    copia zero accesa non vede NIENTE, e non un errore: uno schermo fermo, che
#    e' indistinguibile da un desktop che non cambia.
#
#    Qui lo prova `xfreerdp3 /gfx:RFX`, che chiede lo stesso codec.  Non
#    sostituisce la prova su RDM — quella dice che l'immagine e' GIUSTA, e la
#    puo' dare solo un occhio — ma boccia la regressione che un occhio non
#    guarderebbe mai due volte.

avvia_desktop_vero 1 "" || ko "REMOTIX non e' partito con la copia zero"

cnt "bash $BANCO/fase9-vero.sh RFX fase9-vero-rfx.log"
cnt "bash $BANCO/fase9-muovi.sh 8"
sleep 2
read -r _ FOT_RFX <<<"$(campione)"

if registro 'porto la cattura in memoria' | grep -q 'in memoria'; then
    ok "il palco e' tornato in memoria per il client RemoteFX Progressive"
else
    ko "il palco NON e' tornato in memoria: quel client sta guardando uno schermo fermo"
fi
if registro 'i fotogrammi arrivano come' | tail -1 | grep -q 'MemFd\|MemPtr'; then
    ok "i fotogrammi arrivano davvero in memoria dopo il cambio di strada"
else
    ko "dopo il cambio la cattura consegna ancora DMA-BUF"
fi
if registro 'nessun fotogramma .* dopo il cambio di strada' | grep -q 'nessun fotogramma'; then
    ko "nessun fotogramma e' arrivato per la strada nuova: il client vedra' l'immagine vecchia"
else
    ok "il primo fotogramma della strada nuova e' arrivato"
fi
if [ "${FOT_RFX:-0}" -gt 3 ]; then
    ok "il client RemoteFX Progressive riceve fotogrammi: $FOT_RFX spediti"
else
    ko "al client RemoteFX Progressive sono arrivati $FOT_RFX fotogrammi: e' lo schermo fermo"
fi

# ===========================================================================
titolo "3. E ci torna sulla scheda quando quel client se ne va"
# ===========================================================================
# La strada si rende a chi viene dopo.  Senza questo, il primo client Android
# della sessione spegnerebbe la copia zero per tutti quelli che vengono dopo —
# e nessuno se ne accorgerebbe, perche' funzionerebbe tutto, solo piu' piano.
cnt "bash $BANCO/fase9-chiudi.sh"
sleep 2
cnt "bash $BANCO/fase9-vero.sh AVC420 fase9-vero-ritorno.log"
cnt "bash $BANCO/fase9-muovi.sh 8"
sleep 2
read -r _ FOT_AVC <<<"$(campione)"

if registro 'porto la cattura sulla scheda' | grep -q 'sulla scheda'; then
    ok "il palco e' tornato sulla scheda quando il client se n'e' andato"
else
    ko "il palco e' rimasto in memoria: la copia zero e' spenta per il resto della sessione"
fi
if registro 'codificatore:' | tail -1 | grep -q 'copia zero'; then
    ok "il codificatore si e' riaperto sulle superfici del palco"
else
    ko "il codificatore non lavora sulle superfici: $(registro 'codificatore:' | tail -1)"
fi
# Il conto dei fotogrammi e' di QUESTA connessione — `Rete` nasce e muore con
# lei — quindi si guarda un numero, non una differenza con il giro di prima.
if [ "${FOT_AVC:-0}" -gt 3 ]; then
    ok "il client AVC420 riceve fotogrammi dopo il ritorno sulla scheda: $FOT_AVC spediti"
else
    ko "al client AVC420 sono arrivati $FOT_AVC fotogrammi dopo il ritorno sulla scheda"
fi

# ===========================================================================
titolo "4. Un codificatore in CPU chiede i pixel in CPU anche se il codec e' AVC420"
# ===========================================================================
# ⛔ NON LO DECIDE IL CODEC, LO DECIDE IL CODIFICATORE CHE SI E' APERTO.
#
#    `--codificatore libx264` manda AVC420 ma comprime in CPU, quindi i pixel li
#    vuole in memoria esattamente come RemoteFX Progressive.  Se la richiesta
#    guardasse il codec invece del codificatore, questo caso passerebbe
#    inosservato — ed e' il termine di paragone con cui si misura la fase 9,
#    cioe' il giro che diventerebbe silenziosamente vuoto.
cnt "bash $BANCO/fase9-chiudi.sh"
avvia_desktop_vero 1 "--codificatore libx264" || ko "REMOTIX non e' partito con libx264"
cnt "bash $BANCO/fase9-vero.sh AVC420 fase9-vero-x264.log"
cnt "bash $BANCO/fase9-muovi.sh 8"
sleep 2
read -r _ FOT_X264 <<<"$(campione)"

if registro 'porto la cattura in memoria' | grep -q 'in memoria'; then
    ok "con libx264 il palco e' tornato in memoria, pur essendo AVC420"
else
    ko "con libx264 il palco e' rimasto sulla scheda: il codificatore non trovera' pixel"
fi
if [ "${FOT_X264:-0}" -gt 3 ]; then
    ok "il client riceve fotogrammi con libx264: $FOT_X264 spediti"
else
    ko "con libx264 sono arrivati $FOT_X264 fotogrammi: e' lo schermo fermo"
fi

# ===========================================================================
titolo "5. Il ridimensionamento non deve perdere la copia zero"
# ===========================================================================
# ⛔ IL CONVERTITORE NON SI ADATTA, VA RIFATTO.
#
#    Il suo grafo nasce con dentro la misura del desktop e quella allineata; un
#    ridimensionamento le cambia entrambe.  Chi lo tiene si ritrova superfici
#    della misura di prima, che il codificatore rifiuta — e da lì la copia zero
#    è persa per il resto della sessione, con un avviso che nessuno guarda.
#
#    Trovato dall'utente il 6 agosto **ridimensionando la finestra a video in
#    corso**, cioè facendo la cosa che un banco a misura fissa non fa mai. Il
#    seguito era peggio del primo difetto: il codificatore ripiegava sul
#    CANDIDATO SUCCESSIVO — da `h264_vaapi` a `libx264` — e la sessione passava
#    dalla GPU alla CPU per un ridimensionamento.
cnt "bash $BANCO/fase9-chiudi.sh"
avvia_desktop_vero 1 "" || ko "REMOTIX non e' partito con la copia zero"
cnt "bash $BANCO/fase9-vero.sh AVC420 fase9-vero-ridim.log"

if registro 'codificatore:' | tail -1 | grep -q 'copia zero'; then
    ok "prima del ridimensionamento il codificatore lavora sulle superfici del palco"
else
    ko "non si parte nemmeno a copia zero: $(registro 'codificatore:' | tail -1)"
fi

cnt "export DISPLAY=$DISPLAY_CLI
     ID=\$(xdotool search --name REMOTIXFASE9 | head -1)
     [ -n \"\$ID\" ] && xdotool windowsize \$ID 1280 720 || echo '   nessuna finestra'
     sleep 6
     echo '   finestra portata a 1280x720'"
cnt "bash $BANCO/fase9-muovi.sh 8"
sleep 2
read -r _ FOT_RID <<<"$(campione)"

if registro 'ridimensiono il palco' | grep -q 'ridimensiono il palco'; then
    ok "il palco ha cambiato misura"
else
    ko "il palco non ha cambiato misura: il ridimensionamento non e' arrivato, la prova non prova niente"
fi
if registro 'rifaccio il convertitore|copia zero pronta' | grep -q 'copia zero pronta'; then
    ok "il convertitore e' stato rifatto sulla misura nuova"
else
    ko "il convertitore non e' stato rifatto: le superfici restano della misura di prima"
fi
if registro 'codificatore:' | tail -1 | grep -q 'copia zero'; then
    ok "dopo il ridimensionamento il codificatore lavora ancora sulle superfici"
else
    ko "la copia zero e' andata persa nel ridimensionamento: $(registro 'codificatore:' | tail -1)"
fi
if registro 'superfici del palco sono' | grep -q 'superfici del palco sono'; then
    ko "il codificatore ha trovato superfici della misura sbagliata"
else
    ok "nessuna superficie della misura sbagliata offerta al codificatore"
fi
if [ "${FOT_RID:-0}" -gt 3 ]; then
    ok "il client riceve fotogrammi dopo il ridimensionamento: $FOT_RID spediti"
else
    ko "dopo il ridimensionamento sono arrivati $FOT_RID fotogrammi: e' lo schermo fermo"
fi

cnt "bash $BANCO/fase9-chiudi.sh"
titolo "Riepilogo"
ripristina
[ -f "$SCHEDE/copia-zero.txt" ] && sed 's/^/    /' "$SCHEDE/copia-zero.txt"
;;

*)
    echo "modo sconosciuto: $MODO (base | dopo | gpu | confronto | copia-zero)"; exit 1 ;;
esac

if [ "$GUASTI" -eq 0 ]; then
    printf '\n\033[1;32mFASE 9 (%s): nessun controllo fallito\033[0m\n\n' "$MODO"
else
    printf '\n\033[1;31mFASE 9 (%s): %d controlli falliti\033[0m\n\n' "$MODO" "$GUASTI"
fi
exit $((GUASTI > 0))
