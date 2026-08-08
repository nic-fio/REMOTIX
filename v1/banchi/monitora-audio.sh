#!/bin/bash
#
# monitora-audio.sh — campiona, dentro la VM, i segnali che dicono DOVE si perde
# il suono mentre qualcuno sta davvero usando la sessione.
#
#   bash monitora-audio.sh <secondi> <file>
#
# ⛔ LA MISURA CHE NON DIPENDE DAL CONTENUTO.
#
#    Con un tono si contano gli strappi nell'onda; con un video no, perche' un
#    salto puo' essere musica.  Ma il CONTEGGIO DEI FOTOGRAMMI si conta sempre:
#    a 44 100 Hz, cinque secondi di sessione devono consegnare 220 500
#    fotogrammi fra spediti e taciuti.  Se ne arrivano meno, li ha persi la
#    CATTURA — e non c'e' forma d'onda da interpretare.
#
#    Gli altri due segnali servono a dire perche':
#      - «ERR» di pw-top e' il contatore degli xrun del grafo audio;
#      - la coda di REMOTIX dice se e' il ciclo a non svuotare.
set -u
SECONDI=${1:-120}
FUORI=${2:-/tmp/monitor-audio.txt}
export XDG_RUNTIME_DIR=/run/user/1000

: > "$FUORI"
FINE=$(( $(date +%s) + SECONDI ))

#
# ⛔ E LA MISURA DELL'ALTRO CAPO, che su Android e' l'unica che abbiamo.
#
#    Su RDM non c'e' un registro del client da leggere.  Ma i blocchi spediti e
#    i blocchi RISCONTRATI stanno gia' nella nostra riga di diagnostica: se il
#    client ne riscontra meno di quanti gliene mandiamo, li sta buttando lui —
#    ed e' la stessa cosa che il registro di FreeRDP dice a parole con «Buffer
#    overrun ... dropping».
printf 'istante | fotogrammi catturati | blocchi sped/risc | in coda | ERR | carico\n' >> "$FUORI"

while [ "$(date +%s)" -lt "$FINE" ]; do
    RIGA=$(grep -F 'audio:' ~/remotix.log 2>/dev/null | tail -1)
    SPED=$(printf '%s' "$RIGA" | grep -oE 'audio: [0-9]+' | grep -oE '[0-9]+')
    TAC=$(printf '%s' "$RIGA" | grep -oE '[0-9]+ di silenzio' | grep -oE '^[0-9]+')
    BLK=$(printf '%s' "$RIGA" | grep -oE 'in [0-9]+ blocchi spediti' | grep -oE '[0-9]+')
    RIS=$(printf '%s' "$RIGA" | grep -oE '[0-9]+ blocchi riscontrati' | grep -oE '^[0-9]+')
    CODA=$(printf '%s' "$RIGA" | grep -oE 'in coda [0-9]+' | grep -oE '[0-9]+')
    # Gli xrun di TUTTO il grafo: la colonna ERR, sommata.
    ERR=$(timeout 3 pw-top -b -n 1 2>/dev/null | awk 'NR>1 {s+=$9} END {print s+0}')
    CAR=$(cut -d' ' -f1 /proc/loadavg)
    printf '%s | %s | %s/%s | %s | %s | %s\n' "$(date +%H:%M:%S)" \
        "$(( ${SPED:-0} + ${TAC:-0} ))" "${BLK:-?}" "${RIS:-?}" "${CODA:-?}" "${ERR:-?}" "$CAR" \
        >> "$FUORI"
    sleep 2
done
echo "fine" >> "$FUORI"
