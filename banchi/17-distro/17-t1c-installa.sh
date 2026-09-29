#!/bin/bash
#
# 17-t1c-installa.sh — fase 17, tappa T1c: REMOTIX installato A MANO in una VM
# di `17-vm.sh`, famiglia per famiglia, e acceso come servizio sulla 7447.
#
#   (sul server, come nicfio)
#   bash 17-t1c-installa.sh <macchina> <bersaglio> [prodotto|diag]
#     <macchina>   debian13-gnome, ubuntu2604-gnome, fedora44-gnome, arch-kde, …
#     <bersaglio>  la cartella del binario in $T1C/bin/ (debian13, ubuntu2604,
#                  fedora44, arch, tumbleweed, leap16, alma10)
#     diag         il binario di DIAGNOSI in $T1C/diag/<bersaglio>: lo stesso
#                  sorgente con -DCOPIA_ZERO=0 (vedi sotto).  ⛔ NON e' il prodotto.
#
# ⭐ Non e' l'installatore (T4-T5): e' la LISTA dei passi a mano che il prodotto
#    portato vuole, scritta in un posto solo, e che la T3 trasforma nelle
#    dipendenze dei pacchetti.  Ogni `case` qui sotto e' una riga di §13.2.
# ⛔ NON si usa `src/provisiona.sh`: e' un allestitore DA BANCO (§4.4) e, fuori
#    da Debian, rompe in silenzio — installa sempre `remotix.pam` (Debian,
#    `@include`) in /etc/pam.d, e la sua verifica guarda solo che ci sia
#    «pam_systemd», quindi dice «⭐ la macchina e' nello stato che il prodotto
#    si aspetta» su Fedora e Arch dove nessuno entrerebbe.  `[M]` 29 set.
#
# ⚠ Il binario di diagnosi: nelle VM la scheda e' `virtio_gpu` senza 3D e
#   Mutter/KWin rendono in software.  Il prodotto chiede per primo la strada
#   della SCHEDA (DMA-BUF con modificatore obbligatorio, `cattura.c:1487`), il
#   compositore non ha modificatori da offrire, la negoziazione PipeWire muore
#   con «no more input formats» e il ripiego sulla MEMORIA scatta solo DOPO un
#   fotogramma (`figlio.c:5362`) — che non arriva mai.  `[M]` 29 set, uguale
#   su Debian 13 (GNOME 48), Ubuntu 26.04 (GNOME 50) e Arch (KDE).  Col
#   binario di diagnosi (memoria da subito) il resto della catena si prova.
set -euo pipefail
m=${1:?macchina}; b=${2:?bersaglio}; q=${3:-prodotto}
R=/media/REMOTIX/vm17
T1C=${T1C:-$R/t1c}
VM="bash $R/17-vm.sh ssh $m"
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}

case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;; fedora44-*) n=3;; arch-*) n=4;;
tumbleweed-*) n=5;; leap16-*) n=6;; alma10-*) n=7;; *) echo "macchina sconosciuta: $m"; exit 2;;
esac
case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PORTA_SSH=$((2300 + 10 * n + k))
O="-i $R/ssh/id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
if [ "$q" = diag ]; then BIN=$T1C/diag/$b/remotix; else BIN=$T1C/bin/$b/remotix; fi

echo "==> $m: copio binario ($q), pagina e file di sistema"
$VM 'mkdir -p /tmp/t1c'
# shellcheck disable=SC2086
scp -q $O -P "$PORTA_SSH" "$BIN" "$T1C/pagina.html" "$T1C"/remotix.pam* \
	"$T1C/remotix-niente-spegnimento.rules" "$T1C/remotix-tasti.conf" nicfio@localhost:/tmp/t1c/

# ── 1. le dipendenze di esecuzione, famiglia per famiglia ─────────────────────
echo "==> $m: dipendenze di esecuzione"
case $m in
debian13-*)
	: ;;   # il gruppo del desktop porta gia' libavcodec61 (con libx264), pipewire, libei
ubuntu2604-*)
	# ubuntu-desktop non porta libavcodec; e il GNOME «vanilla» (sessione `gnome`,
	# che REMOTIX avvia) sta nel pacchetto gnome-session (§4.6, D8)
	$VM 'sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q libavcodec62 libswscale9 libavutil60 gnome-session' ;;
fedora44-*)
	: ;;   # il gruppo Workstation porta gia' libavcodec-free (SENZA libx264/libx265)
alma10-*)
	# ffmpeg-free sta in EPEL 10 (con CRB), non in AppStream
	$VM 'sudo dnf -y -q install epel-release && sudo dnf config-manager --set-enabled crb && sudo dnf -y -q install libavcodec-free libavutil-free libswscale-free' ;;
arch-*)
	: ;;
tumbleweed-*)
	$VM 'sudo zypper -n install libavcodec63 libavutil61 libswscale10' ;;
leap16-*)
	$VM 'sudo zypper -n install libavcodec61 libavutil59 libswscale8 libpipewire-0_3-0 libva2 libei1' ;;
esac
# firewalld: ACCESO dopo il gruppo del desktop su Fedora/Alma (zona public, porta chiusa)
$VM 'if systemctl is-active -q firewalld; then sudo firewall-cmd -q --permanent --add-port=7447/tcp --add-port=7447/udp && sudo firewall-cmd -q --reload; fi'
case $m in
*-xfce|*-lxqt)
	case $m in
	debian13-*|ubuntu2604-*) $VM 'sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -q labwc' ;;
	fedora44-*) $VM 'sudo dnf -y -q install labwc' ;;
	arch-*) $VM 'sudo pacman -S --noconfirm --needed labwc' ;;
	# ⚠ xfce4-session 4.20 e' X11: sotto labwc vuole Xwayland, e il pattern xfce
	#   di Leap 16 non lo porta (`[M]` 29 set: «Cannot find Xwayland binary»)
	tumbleweed-*|leap16-*) $VM 'sudo zypper -n install labwc xwayland' ;;
	esac ;;
esac
MANCANO=$($VM "ldd /tmp/t1c/remotix | grep 'not found' || true")
if [ -n "$MANCANO" ]; then echo "⛔ librerie mancanti:"; echo "$MANCANO"; exit 1; fi

# ── 2. il prodotto, il file PAM della famiglia, gli utenti negati ─────────────
echo "==> $m: prodotto e PAM"
case $m in
debian13-*|ubuntu2604-*) PAM=remotix.pam;        DOVE=/etc/pam.d/remotix ;;
fedora44-*|alma10-*)     PAM=remotix.pam.fedora; DOVE=/etc/pam.d/remotix ;;
arch-*)                  PAM=remotix.pam.arch;   DOVE=/etc/pam.d/remotix ;;
tumbleweed-*|leap16-*)   PAM=remotix.pam.suse;   DOVE=/usr/lib/pam.d/remotix ;;
esac
$VM "sudo systemctl stop remotix-t1c 2>/dev/null; sudo loginctl terminate-user prova 2>/dev/null; true
sudo install -D -m 755 /tmp/t1c/remotix /opt/remotix/remotix
sudo install -D -m 644 /tmp/t1c/pagina.html /opt/remotix/pagina.html
sudo install -D -m 644 /tmp/t1c/$PAM $DOVE
[ -f /etc/remotix/utenti-negati ] || { sudo install -D -m 644 /dev/null /etc/remotix/utenti-negati; echo root | sudo tee /etc/remotix/utenti-negati >/dev/null; }
command -v restorecon >/dev/null && sudo restorecon -R /opt/remotix /etc/remotix $DOVE || true"

# ── 3. polkit, logind, sleep: le tre cinture di provisiona.sh §3 ─────────────
echo "==> $m: polkit, logind, sleep"
$VM 'sudo install -D -m 644 /tmp/t1c/remotix-niente-spegnimento.rules /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules
sudo install -D -m 644 /tmp/t1c/remotix-tasti.conf /etc/systemd/logind.conf.d/remotix-tasti.conf
sudo mkdir -p /etc/systemd/sleep.conf.d
printf "[Sleep]\nAllowSuspend=no\nAllowHibernation=no\nAllowSuspendThenHibernate=no\nAllowHybridSleep=no\n" | sudo tee /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf >/dev/null
sudo systemctl restart polkit 2>/dev/null || true
sudo systemctl reload systemd-logind 2>/dev/null || true'

# ── 4. l'utente di prova, nei gruppi LETTI DAI NODI della scheda ─────────────
echo "==> $m: utente di prova"
$VM "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
G=\$(for x in /dev/dri/card* /dev/dri/renderD*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u | paste -sd,)
[ -n \"\$G\" ] && sudo usermod -aG \"\$G\" prova
sudo loginctl enable-linger prova
id prova"

# ── 5. il servizio: unita' transitoria di sistema, come src/riavvia-7900.sh ──
echo "==> $m: REMOTIX come servizio sulla 7447"
$VM 'sudo mkdir -p /var/lib/remotix
sudo systemd-run --unit=remotix-t1c --collect --working-directory=/opt/remotix \
  --property=KillMode=mixed --property=LimitRTPRIO=20 --property=LimitNICE=-11 \
  /opt/remotix/remotix --indirizzo 0.0.0.0 --nome localhost --porta 7447 \
  --certificati /var/lib/remotix/certificati --pagina /opt/remotix/pagina.html \
  --ban-file /var/lib/remotix/ban >/dev/null
sleep 2; systemctl is-active remotix-t1c; sudo journalctl -u remotix-t1c -o cat --no-pager | grep -E "pronto:|PAM" | tail -2'
