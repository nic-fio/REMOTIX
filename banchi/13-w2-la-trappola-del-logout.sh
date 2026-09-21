#!/bin/bash
# ===========================================================================
# 13-w2 — ⛔⛔ LA TRAPPOLA DEL LOGOUT DI XFCE (`STUDI.md` §xfce §9.2, M2)
#
#   bash 13-w2-la-trappola-del-logout.sh                    la prova sana
#   bash 13-w2-la-trappola-del-logout.sh --senza-xfconf     guasto (a)
#   bash 13-w2-la-trappola-del-logout.sh --senza-cinture    guasto (b)
#   bash 13-w2-la-trappola-del-logout.sh --senza-variabile  la misura M2
#   bash 13-w2-la-trappola-del-logout.sh --certifica        il giudice, a secco
#
# ⛔⛔ QUESTO BANCO FA SCATTARE APPOSTA `loginctl terminate-session ''`.
#     ⇒ Questo lanciatore, sull'ospite, fa UNA cosa sola: `podman exec` dentro
#       la scatola `rete11-xfce`.  Non chiama `loginctl`, non uccide niente,
#       non crea utenti: tutto quello succede DENTRO, nel programma Python, che
#       a sua volta si rifiuta di partire se non si trova dentro un contenitore
#       podman (`/run/.containerenv`, `container=podman` nel processo 1) e
#       lanciato per `rete11-xfce` (`RETE11_SCATOLA`).  Due guardie, una per
#       lato: nessuna delle due da sola deve bastare a far danni.
#
# ⚠ Il programma entra per lo stdin (`python3 -`): non dipende da che cosa
#   sia stato copiato in `/opt/remotix` o montato in `/rete11`.  Dentro servono
#   gia' — come per tutte le maglie — il prodotto acceso sulla 8513 e
#   `/opt/remotix/{01-b3-cliente.py,11-c1-nasce-e-si-vede.py}` (li mette
#   `11-accendi.sh accendi xfce`).
#
# ⛔ Si esegue SULLA MACCHINA DI PROVA, da amministratore, a scatola accesa.
#
# ESITI (quelli del programma, passati tali e quali):
#   0 verde — o, col guasto innestato, il guasto e' stato VISTO
#   1 rosso, con la ragione scritta
#   3 non ho potuto guardare, con la ragione scritta — ⛔ non e' un verde
# ===========================================================================
set -uo pipefail

SCATOLA=rete11-xfce
QUI=$(cd "$(dirname "$0")" && pwd)
PROG="$QUI/13-w2-la-trappola-del-logout.py"

if [ ! -f "$PROG" ]; then
	echo "⛔ non trovo $PROG — non ho potuto guardare (esito 3)"
	exit 3
fi

# ⭐ Il giudice a secco non tocca niente, e gira dovunque.
if [ "${1:-}" = "--certifica" ]; then
	exec python3 "$PROG" --certifica
fi

# ⛔ Questo lanciatore sta sull'OSPITE: dentro un contenitore non ha senso,
#    e un `podman` annidato vorrebbe dire non sapere piu' dove si e'.
if [ -e /run/.containerenv ]; then
	echo "⛔ sono gia' dentro un contenitore: questo lanciatore va eseguito"
	echo "   sull'ospite, e da li' entra in $SCATOLA — esito 3"
	exit 3
fi
if ! command -v podman >/dev/null 2>&1; then
	echo "⛔ non c'e' podman: non posso entrare in $SCATOLA — esito 3"
	exit 3
fi
ACCESA=$(podman container inspect -f '{{.State.Running}}' "$SCATOLA" 2>/dev/null)
if [ "$ACCESA" != "true" ]; then
	echo "⛔ la scatola $SCATOLA non e' accesa (o non la vedo: si lancia da"
	echo "   amministratore) — «$ACCESA».  ⇒ bash 11-scatole/11-accendi.sh accendi xfce"
	echo "   esito 3"
	exit 3
fi

# ⛔ NIENTE `sh -c` in mezzo (`11-accendi.sh`, c1: un guscio annidato ha perso
#    le virgolette e ha restituito 0 senza eseguire niente).
podman exec -i -e RETE11_SCATOLA="$SCATOLA" "$SCATOLA" \
	python3 -u - "$@" < "$PROG"
exit $?
