#!/bin/bash
# ===========================================================================
# 10-f2-panoramica.sh — ⛔ IL DESKTOP REMOTO NASCE DENTRO LA «PANORAMICA» DI
# GNOME, e ci resta finche' nessuno lo tocca.
#
# ⭐ COME SI E' VISTO: negli scatti del testimone (`10-f2-scena.sh`) il quadro
#    porta sempre la barra di ricerca «Type to search», il molo in basso e
#    l'anteprima dell'altro spazio di lavoro a destra ⇒ e' la **panoramica
#    delle Attivita'**, non il desktop.  ⚠ La finestra del programma c'e' e
#    disegna: e' *dentro* l'anteprima.
#
# ⛔ PERCHE' IMPORTA: per chi guarda, un desktop che non esce mai dalla
#    panoramica e una finestra che non si riesce a raggiungere hanno la stessa
#    faccia — *«non funziona»*.
#
# ⭐ CHE COSA MISURA QUESTO FILE: se **una attivazione** la fa sparire.  Se si',
#    la panoramica se ne va al primo clic dell'utente e non e' un difetto; se
#    no, e' un difetto e va curato da noi.
#    ⚠ Si usa `org.gnome.Shell.FocusApp`, che e' quel che la Shell fa quando si
#      clicca l'icona nel molo: non e' un clic vero, ⛔ ma e' la stessa strada.
#
#   uso:  10-f2-panoramica.sh <UTENTE> <APP.desktop>
# ===========================================================================
set -uo pipefail

U=${1:?serve un utente}
APP=${2:-firefox-esr.desktop}

sleep 22
bash /media/REMOTIX/tmp/10f2/10-f2-dentro.sh "$U" composto \
	/usr/bin/gdbus call --session --dest org.gnome.Shell \
	--object-path /org/gnome/Shell --method org.gnome.Shell.FocusApp "$APP"
echo "attivazione chiesta per $APP"
