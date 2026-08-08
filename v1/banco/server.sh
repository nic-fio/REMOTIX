#!/bin/bash
#
# server.sh — guida la macchina di runtime, che adesso E' il server.
#
#   server.sh copia [file]   porta il binario compilato in ~ e riavvia
#   server.sh avvia          accende il servizio
#   server.sh ferma          lo spegne
#   server.sh stato          e' vivo?  e la sessione grafica?
#   server.sh registro [n]   le ultime n righe
#   server.sh opzioni <...>  riscrive /etc/default/remotix e riavvia
#
# Gemello di `vm.sh`, con gli stessi verbi: i banchi non devono imparare due
# vocabolari.  Quel che manca e' `ssh`, perche' non c'e' piu' nessun altrove
# dove entrare — ed e' esattamente il punto del trasloco.
set -u
BASE=/media/REMOTIX
BINARIO="$BASE/src/remotix-c/build/src/remotix"
CASA="$HOME"

case "${1:-stato}" in
copia)
    SORGENTE="${2:-$BINARIO}"
    [ -x "$SORGENTE" ] || { echo "manca $SORGENTE: compilalo con enter.sh"; exit 1; }
    sudo systemctl stop remotix.service
    cp -f "$SORGENTE" "$CASA/remotix"
    chmod +x "$CASA/remotix"
    sudo systemctl start remotix.service
    sleep 2
    systemctl is-active --quiet remotix.service && echo "copiato e riavviato" || echo "copiato, ma il servizio NON e' partito"
    ;;
avvia)   sudo systemctl start remotix.service; sleep 2; systemctl is-active remotix.service ;;
ferma)   sudo systemctl stop remotix.service; echo fermato ;;
stato)
    echo "servizio:  $(systemctl is-active remotix.service)"
    # La porta si LEGGE da chi ascolta, non si da' per scontata: `opzioni
    # --porta N` la sposta, e un controllo inchiodato al 3389 direbbe «spento»
    # su un server sanissimo — la diagnosi sbagliata di §8.6 di REFERENCE.md.
    ASCOLTO=$(ss -ltnp 2>/dev/null | awk '/"remotix"/{sub(/.*:/, "", $4); print $4}' | tr '\n' ' ')
    echo "porta:     ${ASCOLTO:-nessuna }in ascolto"
    echo "sessione:  $(pgrep -c gnome-shell) gnome-shell"
    echo "schede:    $(ls /dev/dri 2>/dev/null | tr '\n' ' ')"
    ;;
registro) tail -n "${2:-40}" "$CASA/remotix.log" ;;
opzioni)
    shift
    printf 'REMOTIX_OPZIONI=%s\n' "$*" | sudo tee /etc/default/remotix >/dev/null
    sudo systemctl restart remotix.service; sleep 2
    systemctl is-active --quiet remotix.service && echo "opzioni: $*" || echo "NON riavviato"
    ;;
*) echo "comandi: copia | avvia | ferma | stato | registro [n] | opzioni <...>"; exit 1 ;;
esac
