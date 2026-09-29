#!/bin/bash
#
# 17-t3-pacchetto.sh — fase 17, T3: il PACCHETTO NATIVO provato in una VM
# «cliente» di 17-vm.sh (per ora Arch: `pacman`).  Un passo per chiamata, cosi'
# ogni esito si legge prima di andare avanti.
#
#   (sul server, come nicfio; la VM accesa con 17-vm.sh avvia)
#   bash 17-t3-pacchetto.sh <macchina> prepara            utente `prova` (gia' in `video`: R33)
#   bash 17-t3-pacchetto.sh <macchina> impronta <nome>    $T3/<macchina>/impronta-<nome>.txt
#   bash 17-t3-pacchetto.sh <macchina> installa <pkg>     copia e `pacman -U`, NIENT'ALTRO (R4)
#   bash 17-t3-pacchetto.sh <macchina> accendi            `systemctl enable --now` (il gesto del motore)
#   bash 17-t3-pacchetto.sh <macchina> togli              `pacman -Rns remotix`
#   bash 17-t3-pacchetto.sh <macchina> confronta <a> <b>  diff delle due impronte
#
# ⭐ «prepara» e' la scena, non l'installazione: una persona con la parola
#    d'ordine per entrare dal browser, e gia' in `video` PRIMA — cosi' la prova
#    vede se la disinstallazione toglie un gruppo che c'era (R33, ⛔ non deve).
# ⛔ Fra «impronta prima» e «installa» non si tocca niente a mano: e' R4.
set -euo pipefail
m=${1:?macchina}; passo=${2:?passo}
R=/media/REMOTIX/vm17
T3=${T3:-$R/t3}
QUI=$(cd "$(dirname "$0")" && pwd)
VM() { bash "$R/17-vm.sh" ssh "$m" "$@"; }
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
mkdir -p "$T3/$m"

case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;; fedora44-*) n=3;; arch-*) n=4;;
tumbleweed-*) n=5;; leap16-*) n=6;; alma10-*) n=7;; *) echo "macchina sconosciuta: $m"; exit 2;;
esac
case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PORTA_SSH=$((2300 + 10 * n + k))
O="-i $R/ssh/id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"

case $passo in
prepara)
	VM "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
sudo gpasswd -a prova video >/dev/null
id prova" ;;
impronta)
	nome=${3:?nome}
	# shellcheck disable=SC2086
	scp -q $O -P "$PORTA_SSH" "$QUI/17-t3-impronta-arch.sh" nicfio@localhost:/var/tmp/
	VM 'sudo bash /var/tmp/17-t3-impronta-arch.sh' >"$T3/$m/impronta-$nome.txt"
	VM 'rm -f /var/tmp/17-t3-impronta-arch.sh'
	wc -l "$T3/$m/impronta-$nome.txt" ;;
installa)
	pkg=${3:?pacchetto}
	# shellcheck disable=SC2086
	scp -q $O -P "$PORTA_SSH" "$pkg" nicfio@localhost:/var/tmp/
	b=$(basename "$pkg")
	VM "sudo pacman -U --noconfirm /var/tmp/$b; e=\$?; rm -f /var/tmp/$b; exit \$e" 2>&1 | tee "$T3/$m/installa-$(date +%H%M%S).log" ;;
accendi)
	VM 'sudo systemctl enable --now remotix.service && sleep 3 && systemctl is-active remotix.service
sudo journalctl -u remotix.service -o cat --no-pager | grep -E "pronto:|PAM|KWin|desktop di questa" | tail -5' ;;
togli)
	VM 'sudo pacman -Rns --noconfirm remotix' 2>&1 | tee "$T3/$m/togli-$(date +%H%M%S).log" ;;
confronta)
	a=${3:?a}; b=${4:?b}
	diff "$T3/$m/impronta-$a.txt" "$T3/$m/impronta-$b.txt" >"$T3/$m/diff-$a-$b.txt" || true
	grep -c '^[<>]' "$T3/$m/diff-$a-$b.txt" || true
	echo "$T3/$m/diff-$a-$b.txt" ;;
*) echo "passo sconosciuto: $passo"; exit 2 ;;
esac
