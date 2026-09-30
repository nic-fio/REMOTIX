#!/bin/sh
# t10-gruppi — allinea i gruppi `video` e `render` della scatola ai gruppi dei NODI dell'ospite
# (card0, renderD128). Sulla macchina vera i nodi nascono coi gruppi locali (udev); in una scatola
# entrano coi numeri dell'ospite, e senza questo passo nessun gruppo della scatola li possiede —
# e l'installatore, che legge i gruppi DAI NODI (DECISIONI §7.21), non saprebbe a chi iscrivere.
# Stessa logica di banchi/11-scatole (rete11-allinea-gruppi), senza gli inquilini: l'utente lo fa
# il banco.
set -eu
allinea() {  # allinea <nodo> <gruppo>
	N=$1; GR=$2
	[ -e "$N" ] || { echo "t10: $N non c'e', la scheda non e' entrata"; return 0; }
	G=$(stat -c %g "$N")
	A=$(getent group "$G" | cut -d: -f1 || true)
	if [ "$A" = "$GR" ]; then echo "t10: $GR e' gia' $G"; return 0; fi
	if [ -n "$A" ]; then
		groupmod -g "1$G" "$A" || true
		find / -xdev -gid "$G" -exec chgrp "1$G" {} + 2>/dev/null || true
		echo "t10: i file del gruppo $A hanno seguito il gruppo a 1$G"
	fi
	groupmod -g "$G" "$GR" 2>/dev/null || groupadd -g "$G" "$GR"
	echo "t10: $GR allineato a $G (era di ${A:-nessuno})"
}
allinea /dev/dri/card0 video
allinea /dev/dri/renderD128 render
