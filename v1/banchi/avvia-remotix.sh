#!/bin/bash
# Avvia REMOTIX nella VM, come servizio di SISTEMA.
#   bash avvia-remotix.sh            con autenticazione PAM
#   bash avvia-remotix.sh --aperto   senza autenticazione (solo per il banco)
#
# ⛔ Il servizio vive in `system.slice`, fuori dall'albero dell'utente, e non e'
#    un dettaglio di comodita': l'uscita di GNOME finisce con `exit.target` sul
#    gestore utente, che ferma `user@1000.service` per intero.  Qualunque cosa
#    stia sotto quel ramo — scope della sessione SSH, `app.slice`,
#    `background.slice` — muore col logout.  Misurato tutte e tre.
set -u

EXTRA=""
[ "${1:-}" = "--aperto" ] && EXTRA="--senza-autenticazione"

printf 'REMOTIX_OPZIONI=--registro %s %s\n' "${REMOTIX_REGISTRO:-diagnostica}" "$EXTRA" \
    | sudo tee /etc/default/remotix >/dev/null
rm -f "$HOME/remotix.log"
sudo systemctl restart remotix.service

sleep 3
if systemctl is-active --quiet remotix.service; then
    echo "REMOTIX in esecuzione (pid $(pgrep -x remotix)) ${EXTRA:-con PAM}, in system.slice"
    ss -ltn | grep 3389 || echo "ATTENZIONE: non ascolta sulla 3389"
else
    echo "REMOTIX non e' partito:"; sudo systemctl status remotix.service --no-pager | tail -12; exit 1
fi
