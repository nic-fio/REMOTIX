#!/bin/bash
# 15-g8-server.sh — il SECONDO server del prodotto del gruppo G8, dentro una scatola.
#
#   bash 15-g8-server.sh accendi|spegni|sblocca|stato <gnome|kde|xfce|lxqt>
#
# Stesso binario /opt/remotix/remotix, unita' `rete15-g8`, porta 8621 gnome ·
# 8622 kde · 8623 xfce · 8624 lxqt, e ban-file, socket di comando, rilievo e
# registro SUOI in /var/lib/rete15-g8/ (modello: 11-accendi.sh, caso `server`).
#
# ⛔ Serve a tutto cio' che sbaglia la parola (F-027, F-028, N-1, N-4): tre
#    tentativi falliti bannano 192.168.0.2 per 12 ore, e sul server della
#    scatola (8511-8514) fermerebbero tutta la suite.  Il ban vive nella memoria
#    di QUESTO processo e nel SUO file (/var/lib/rete15-g8/ban): l'85xx non lo
#    vede — `stato` mostra i due file dei ban uno accanto all'altro.
# ⛔ `sblocca` parla al socket di comando (src/comando.c: «SBLOCCA <indirizzo>»).
# ⚠ Spegnere l'unita' chiude le sessioni che vi sono nate (KillMode=mixed):
#    sono solo i nostri inquilini c15027u*.
#
# Dal tablet passa per ssh; sul server (REMOTIX_SUL_SERVER=1 o dall'albero
# /media/REMOTIX/src/controllo) gira direttamente.
QUI=$(cd "$(dirname "$0")" && pwd)
if [ -z "${REMOTIX_SUL_SERVER:-}" ] && [ ! -d /media/REMOTIX/src/controllo ]; then
	ssh -o BatchMode=yes nicfio@192.168.0.2 \
		"REMOTIX_SUL_SERVER=1 bash ${REMOTIX_CONTROLLO:-/media/REMOTIX/src/controllo}/banchi/15-suite/15-g8-server.sh $*" 2>&1 \
		| grep --line-buffered -v '^tput'
	exit "${PIPESTATUS[0]}"
fi
exec python3 "$QUI/15-g8-comune.py" "$@"
