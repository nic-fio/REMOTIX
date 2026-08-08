#!/bin/bash
#
# gpu-udev.sh — la regola che esclude una GPU dal servizio, per id PCI.
#
# ⛔ SERVE PERCHE' CON `--virtual` NON ESISTE ALCUNA LEVA.  `findRenderDevice()`
#    di KWin prende la PRIMA scheda che si apre e non guarda nessuna variabile:
#    `KWIN_DRM_DEVICES` vale solo per il backend `drm` (`kde.md` §5.6).  L'unico
#    modo di sceglierne una e' rendere l'altra non apribile.
#
# ⛔ E LA VIA OVVIA E' UNA TRAPPOLA: `InaccessiblePaths=` nell'unita' del
#    compositore da' la scheda giusta e CHIUDE IL CANCELLO DELLA CATTURA —
#    0 righe di registro sui permessi contro 13 (`kde.md` §3.3-bis).  Si passa
#    dai permessi del NODO, che e' quel che fa questa regola.
#
# ⚠ E PER ID PCI, NON PER NUMERO DI NODO: `renderD128` e `renderD129` si possono
#   scambiare fra un avvio e l'altro; l'indirizzo PCI no.
#
# ⚠⚠ IL PREZZO, che va detto prima e non dopo: negare il nodo coi permessi lo
#    nega a TUTTA LA SESSIONE DELL'UTENTE, non solo al compositore.  Se un
#    giorno servisse quella scheda per altro — un gioco, un transcodificatore —
#    smetterebbe di funzionare, e nessuno collegherebbe la cosa a questo file.
#
#   uso:  sudo bash gpu-udev.sh 0000:03:00.0     ← l'indirizzo da ESCLUDERE
#         sudo bash gpu-udev.sh --togli
set -eu

REGOLA=/etc/udev/rules.d/99-remotix-gpu.rules

if [ "${1:-}" = "--togli" ]; then
    rm -f "$REGOLA"
    udevadm control --reload-rules && udevadm trigger --subsystem-match=drm
    echo "regola tolta: tutte le schede tornano al gruppo render"
    exit 0
fi

PCI=${1:-}
[ -n "$PCI" ] || { echo "manca l'id PCI da escludere (es. 0000:03:00.0)"; exit 1; }

NODO=$(readlink -f "/dev/dri/by-path/pci-$PCI-render" 2>/dev/null || true)
[ -n "$NODO" ] || { echo "nessun nodo di rendering all'indirizzo $PCI"; exit 1; }
echo "escludo $PCI (oggi e' $NODO)"

cat > "$REGOLA" <<CONF
# REMOTIX — questa scheda non va usata dal compositore della sessione remota.
#
# Il gruppo «remotix-nogpu» non ha membri: il nodo resta li', leggibile da root,
# e l'utente del servizio non lo apre.  KWin allora passa alla scheda dopo.
#
# ⚠ Vale per TUTTA la sessione dell'utente, non solo per il compositore.
KERNEL=="renderD*", SUBSYSTEM=="drm", ENV{ID_PATH}=="pci-$PCI", GROUP="remotix-nogpu", MODE="0660"
CONF

getent group remotix-nogpu >/dev/null || groupadd --system remotix-nogpu
udevadm control --reload-rules
udevadm trigger --subsystem-match=drm
sleep 1
echo "adesso: $(ls -l "$NODO")"
echo
echo "⚠ per tornare indietro:  sudo bash $0 --togli"
