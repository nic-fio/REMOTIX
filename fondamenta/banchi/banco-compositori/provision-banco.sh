#!/bin/bash
#
# provision-banco.sh — rimette in piedi il banco dei compositori dopo un riavvio.
#
# Il rootfs del server vive in RAM e si azzera a ogni riavvio: `/media` resta,
# tutto il resto no.  Questo script reinstalla i pacchetti che il banco dei
# compositori usa, e ricompila i suoi tre programmi.  Va eseguito DOPO
# `provision-server.sh`, che è quello che rimette in piedi il prodotto.
#
#   bash /media/REMOTIX/tmp/banco-compositori/provision-banco.sh
#
# ⚠ NON serve al prodotto.  Serve a MISURARE, e i pacchetti che installa —
#   KDE, sway, labwc — sono compositori concorrenti: stanno qui perché il banco
#   li mette accanto a GNOME nello stesso minuto, che è l'unico modo in cui i
#   loro numeri si possono confrontare (`REFERENCE.md` R32).
#
set -euo pipefail

QUI=/media/REMOTIX/tmp/banco-compositori

# --- i pacchetti, divisi per che cosa servono -----------------------------
SCENE=(weston glmark2-wayland mpv ffmpeg)          # le scene dichiarate
CLIENT=(freerdp3-x11 xvfb)                          # il client di prova
COMPOSITORI=(kwin-wayland kwin-common sway labwc)   # i termini di paragone
PROTOCOLLI=(plasma-wayland-protocols libwayland-dev wayland-protocols)

# ⛔ Le credenziali si prendono UNA VOLTA, e con `-S`.
#
#    `provision-server.sh` lo fa dalla prima riga; questo no, e il 9 agosto 2026 —
#    al primo riavvio vero del server — si e' fermato subito con «sudo: a terminal
#    is required».  Due script di ripristino della stessa macchina che trattano
#    `sudo` in due modi diversi: quello che funziona da solo e quello che pretende
#    un terminale.  La richiesta NON va lasciata vuota, o chi fornisce la parola
#    d'ordine da standard input non ha niente da riconoscere e aspetta per sempre.
if ! sudo -n true 2>/dev/null; then
    sudo -v -S -p 'Password sudo: '
fi

echo "==> pacchetti del banco"
sudo apt-get update -qq
sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
    "${SCENE[@]}" "${CLIENT[@]}" "${COMPOSITORI[@]}" "${PROTOCOLLI[@]}"

echo "==> i tre programmi del banco"
# Si compilano nel contenitore, come tutto il resto del progetto, e girano qui:
# il contenitore e il server condividono la distribuzione.
cp -f /usr/share/plasma-wayland-protocols/zkde-screencast-unstable-v1.xml "$QUI/"
wayland-scanner client-header "$QUI/zkde-screencast-unstable-v1.xml" \
    "$QUI/zkde-screencast-unstable-v1-client-protocol.h"
wayland-scanner private-code "$QUI/zkde-screencast-unstable-v1.xml" \
    "$QUI/zkde-screencast-unstable-v1-protocol.c"

# L'XML di wlr-screencopy non è pacchettizzato in Debian: sta nel sorgente di
# wlroots, che resta estratto qui accanto proprio per non doverlo riscaricare.
if [ ! -f "$QUI/wlr-screencopy-unstable-v1-protocol.c" ]; then
    X=$(find "$QUI" -maxdepth 3 -name 'wlr-screencopy-unstable-v1.xml' | head -1)
    [ -n "$X" ] || { echo "manca l'XML di wlr-screencopy: vedi LEZIONI.md §3"; exit 1; }
    wayland-scanner client-header "$X" "$QUI/wlr-screencopy-unstable-v1-client-protocol.h"
    wayland-scanner private-code "$X" "$QUI/wlr-screencopy-unstable-v1-protocol.c"
fi

bash /media/REMOTIX/enter.sh "cd /srv/remotix/tmp/banco-compositori && \
    gcc -O2 -Wall -o misura-cattura misura-cattura.c \
        \$(pkg-config --cflags --libs libpipewire-0.3 gio-2.0 libdrm) && \
    gcc -O2 -Wall -o nodo-kwin nodo-kwin.c zkde-screencast-unstable-v1-protocol.c \
        \$(pkg-config --cflags --libs wayland-client) && \
    gcc -O2 -Wall -o nodo-portale nodo-portale.c \$(pkg-config --cflags --libs gio-2.0) && \
    gcc -O2 -Wall -D_GNU_SOURCE -o misura-wlroots misura-wlroots.c \
        wlr-screencopy-unstable-v1-protocol.c \$(pkg-config --cflags --libs wayland-client)"

echo "==> le scene video"
bash "$QUI/banco.sh" prepara >/dev/null

echo
echo "banco pronto:"
ls -1 "$QUI"/{misura-cattura,nodo-kwin,nodo-portale,misura-wlroots} 2>&1
echo
echo "  bash banco.sh mutter          la tabella di Mutter"
echo "  bash banco-altri.sh           KWin e wlroots"
echo "  bash banco-catena.sh 20       la catena intera fino al client"
