#!/bin/bash
#
# Entra nel contenitore di sviluppo REMOTIX.
#
#   bash /media/REMOTIX/enter.sh            apre una shell interattiva
#   bash /media/REMOTIX/enter.sh <comando>  esegue un comando e esce
#   bash /media/REMOTIX/enter.sh --root ... come sopra, ma da amministratore
#
# La modalita' --root serve per le operazioni di manutenzione (installare
# pacchetti) e per accedere ai nodi GPU: l'utente esterno non appartiene ai
# gruppi video e render del sistema host, e non li si vuole modificare.
#
# I sorgenti sono in /srv/src; il progetto in C sta in /srv/src/remotix-c.
#
# La password di sudo puo' essere digitata, oppure fornita da standard input:
#   printf '%s\n' "$PASSWORD" | bash /media/REMOTIX/enter.sh "ninja -C $REMOTIX_BUILD"
#
set -euo pipefail

DEVROOT=/media/REMOTIX/devroot

# Acquisisce le credenziali una volta sola. Con -S le legge da standard input
# se ce ne sono, altrimenti le chiede a terminale.
if ! sudo -n true 2>/dev/null; then
    # La richiesta NON va lasciata vuota: chi fornisce la password da standard
    # input (script, automazioni) non avrebbe nulla da riconoscere e resterebbe
    # in attesa per sempre, senza che compaia alcun messaggio.
    sudo -v -S -p 'Password sudo: '
fi

sudo mkdir -p "$DEVROOT"/{proc,sys,dev,srv/src,srv/remotix}
mountpoint -q "$DEVROOT/proc"        || sudo mount -t proc proc  "$DEVROOT/proc"
# I --rbind vanno resi slave: senza, un umount ricorsivo qui dentro si propaga
# all'originale e smonta /dev/pts DEL SERVER, che resta senza pseudo-terminali
# e non fa piu' entrare nessuno in SSH ("PTY allocation request failed").
mountpoint -q "$DEVROOT/sys"         || { sudo mount --rbind /sys "$DEVROOT/sys"
                                           sudo mount --make-rslave "$DEVROOT/sys"; }
mountpoint -q "$DEVROOT/dev"         || { sudo mount --rbind /dev "$DEVROOT/dev"
                                           sudo mount --make-rslave "$DEVROOT/dev"; }
mountpoint -q "$DEVROOT/srv/src"     || sudo mount --bind /media/REMOTIX/src     "$DEVROOT/srv/src"
mountpoint -q "$DEVROOT/srv/remotix" || sudo mount --bind /media/REMOTIX    "$DEVROOT/srv/remotix"
sudo cp -f /etc/resolv.conf "$DEVROOT/etc/resolv.conf"

AS_ROOT=no
if [ "${1:-}" = "--root" ]; then AS_ROOT=yes; shift; fi

if [ $# -eq 0 ]; then
    set -- /bin/bash -l
else
    set -- /bin/bash -lc "$*"
fi

# NB: niente "exec". Sostituendo il processo si perderebbe l'associazione
# delle credenziali sudo gia' validate, e in assenza di terminale la
# password verrebbe richiesta di nuovo senza poter essere letta.
if [ "$AS_ROOT" = yes ]; then
    sudo chroot "$DEVROOT" /usr/bin/env -i \
        PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        HOME=/root USER=root TERM="${TERM:-xterm}" LC_ALL=C.UTF-8 \
        "$@"
else
    sudo chroot "$DEVROOT" /usr/bin/env -i \
        PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin \
        HOME=/home/dev USER=dev TERM="${TERM:-xterm}" LC_ALL=C.UTF-8 \
        setpriv --reuid=1000 --regid=1000 --init-groups \
        "$@"
fi
