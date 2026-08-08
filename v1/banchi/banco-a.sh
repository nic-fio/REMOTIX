#!/bin/bash
#
# Banco per la misura A della fase 0: RDM rende davvero RemoteFX Progressive?
#
# Da eseguire DENTRO la VM di runtime.  La VM non ha accelerazione grafica,
# quindi gnome-remote-desktop non ha VA-API e ripiega su RemoteFX Progressive
# per costruzione (grd-rdp-render-context.c: se non c'e' VAAPI, RFX
# Progressive).  E con RDM ci ripiegherebbe comunque, perche' RDM dichiara
# AVC_DISABLED ovunque.  E' il banco che PIANO.md prescrive.
#
# Avvia una sessione GNOME senza monitor (§5.9-bis di SPECIFICA.md) e ci mette
# dentro grd in modo headless, in ascolto sulla 3389.
set -u

UTENTE=$(id -un)
BASE="$HOME/banco-a"
mkdir -p "$BASE"
cd "$BASE" || exit 1

echo "== 1. gnome-remote-desktop: tolgo la maschera"
sudo systemctl unmask gnome-remote-desktop.service          >/dev/null 2>&1
sudo systemctl --global unmask gnome-remote-desktop.service >/dev/null 2>&1
systemctl --user unmask gnome-remote-desktop-headless.service >/dev/null 2>&1
dpkg -s gnome-remote-desktop >/dev/null 2>&1 || { echo "!! grd non installato"; exit 1; }

echo "== 2. portachiavi (grd tiene le credenziali in libsecret)"
if ! dpkg -s gnome-keyring >/dev/null 2>&1; then
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq gnome-keyring >/dev/null 2>&1
fi
dpkg -s gnome-keyring >/dev/null 2>&1 && echo "   portachiavi presente" || echo "   !! manca"

echo "== 3. certificato TLS autofirmato"
if [ ! -f cert.pem ]; then
    openssl req -x509 -newkey rsa:2048 -nodes -keyout key.pem -out cert.pem \
        -days 30 -subj "/CN=remotix-banco" >/dev/null 2>&1
fi
chmod 600 key.pem; echo "   $(ls cert.pem key.pem | tr '\n' ' ')"

echo "== 4. sessione GNOME senza monitor"
# NB: si guarda il processo, non `busctl --user list`, che elenca anche i nomi
# soltanto ATTIVABILI: org.gnome.Shell compare li' anche a Shell spenta.
if pgrep -u "$UTENTE" gnome-shell >/dev/null; then
    echo "   gia' viva"
else
    # L'ambiente si dichiara PRIMA: l'unita' della Shell porta
    # ConditionEnvironment=XDG_SESSION_TYPE=wayland, e senza quella variabile
    # il compositore non viene avviato affatto (§5.9-bis).
    env -i \
        HOME="$HOME" USER="$UTENTE" LOGNAME="$UTENTE" \
        PATH=/usr/local/bin:/usr/bin:/bin \
        XDG_RUNTIME_DIR="/run/user/$(id -u)" \
        LANG=C.UTF-8 LC_ALL=C.UTF-8 \
        XDG_SESSION_TYPE=wayland XDG_CURRENT_DESKTOP=GNOME XDG_SESSION_DESKTOP=gnome \
        setsid nohup gnome-session --session=gnome >"$BASE/sessione.log" 2>&1 &
    for i in $(seq 1 40); do
        pgrep -u "$UTENTE" gnome-shell >/dev/null && break
        sleep 1
    done
fi
sleep 5
pgrep -u "$UTENTE" gnome-shell >/dev/null && echo "   gnome-shell in esecuzione" \
    || { echo "   !! la Shell non e' partita"; tail -20 "$BASE/sessione.log"; exit 1; }

echo "== 5. Mutter risponde?"
busctl --user call org.gnome.Mutter.ScreenCast /org/gnome/Mutter/ScreenCast \
    org.freedesktop.DBus.Properties Get ss org.gnome.Mutter.ScreenCast Version 2>&1 | head -2

echo "== 6. configuro grd"
grdctl --headless rdp set-tls-cert "$BASE/cert.pem"
grdctl --headless rdp set-tls-key  "$BASE/key.pem"
grdctl --headless rdp set-credentials prova prova 2>&1 | head -3
grdctl --headless rdp disable-view-only
grdctl --headless rdp enable
echo "--- stato:"
grdctl --headless status 2>&1 | head -20

echo "== 7. avvio grd headless"
systemctl --user restart gnome-remote-desktop-headless.service 2>&1 | head -3
sleep 4
systemctl --user is-active gnome-remote-desktop-headless.service
ss -ltn 2>/dev/null | grep -E ":3389|:3390" || echo "   !! nessun ascolto sulla 3389"
