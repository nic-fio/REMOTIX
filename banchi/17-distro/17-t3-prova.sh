#!/bin/bash
#
# 17-t3-prova.sh — fase 17, T3: il pacchetto NATIVO su una VM «cliente», R4 R5 R6 in piccolo.
#
#   (sul server, come nicfio)
#   sg kvm -c 'bash 17-t3-prova.sh <macchina> <file.deb>'
#     es.  bash 17-t3-prova.sh debian13-gnome /media/REMOTIX/vm17/t3/remotix_…+deb13_amd64.deb
#
# Il copione di §7.3, senza l'installatore (che e' di T4-T5): solo il gestore di
# pacchetti.
#   0. torna alla foto «cliente» e accende;
#   1. una persona sulla macchina, `prova`, GIA' nel gruppo del nodo cardN (di
#      solito `video`): e' il caso R33 — il purge non deve toglierla da li';
#   2. impronta «prima» (17-t3-impronta.sh);
#   3. `apt-get install ./remotix_….deb` e NIENT'ALTRO a mano (R4); impronta;
#   4. un browser vero entra e deve vedere il desktop (17-t1c-guarda.sh, Chrome,
#      127.0.0.1); impronta;
#   5. reinstallazione (`--reinstall`): impronta, dev'essere uguale a quella del
#      punto 4 (R5);
#   6. `apt-get purge remotix`: impronta; poi `apt-get autoremove --purge`:
#      impronta.  I confronti con «prima» si CLASSIFICANO a mano (DIRETTA,
#      INDIRETTA, PREESISTENTE: fasi/17 §6.6.4) nel rapporto;
#   7. spegne e torna alla foto «cliente».
# Evidenze in $T3/esiti/<macchina>/.
# ⚠ Una VM sola (fasi/17 §7.1): la macchina si spegne anche se la prova cade.
set -uo pipefail
m=${1:?macchina}; DEB=${2:?file .deb}
R=/media/REMOTIX/vm17
T3=${T3:-$R/t3}
QUI=$(cd "$(dirname "$0")" && pwd)
E=$T3/esiti/$m
V="bash $R/17-vm.sh"
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}

case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;; *) echo "solo famiglia .deb: $m"; exit 2;;
esac
case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PSSH=$((2300 + 10 * n + k)); PRX=$((7500 + 10 * n + k))
O="-i $R/ssh/id_ed25519 -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
vm() { $V ssh "$m" "$@"; }
impronta() { vm 'sudo bash -s' <"$QUI/17-t3-impronta.sh" >"$E/impronta-$1.txt" 2>"$E/impronta-$1.err"
             echo "   impronta «$1»: $(wc -l <"$E/impronta-$1.txt") righe"; }
fine() { echo "==> spengo e torno a «cliente»"; $V ferma "$m" >/dev/null 2>&1; $V torna "$m" cliente >/dev/null 2>&1; }
trap fine EXIT

mkdir -p "$E"; rm -f "$E"/*
# ⛔ Una macchina gia' accesa e' di qualcun altro: non la si spegne, ci si ferma.
if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then
	trap - EXIT; echo "⛔ $m e' gia' accesa: la usa qualcun altro"; exit 2
fi
[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { trap - EXIT; echo "⛔ gia' 4 VM accese"; exit 2; }
echo "==> $m: foto «cliente», accensione"
$V torna "$m" cliente || exit 1
$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }

echo "==> la persona «prova», gia' nel gruppo del nodo card (R33)"
vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
G=\$(for x in /dev/dri/card[0-9]*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u | head -1)
[ -n \"\$G\" ] && sudo gpasswd -a prova \"\$G\" >/dev/null
ls -l /dev/dri/; id prova; id nicfio" | tee "$E/persone-prima.txt"
impronta prima

echo "==> apt-get install ./$(basename "$DEB")"
# shellcheck disable=SC2086
scp -q $O -P "$PSSH" "$DEB" nicfio@localhost:/tmp/ || exit 1
D=/tmp/$(basename "$DEB")
vm "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y $D" >"$E/installa.log" 2>&1
echo "   uscita $? — $(grep -E '^[0-9]+ (upgraded|aggiornati)' "$E/installa.log")"
grep -E '^remotix:' "$E/installa.log" | sed 's/^/   /'
vm "systemctl is-active remotix; sudo cat /var/lib/remotix/modifiche.log; id prova; id nicfio
sudo ls -l /var/lib/remotix /var/lib/remotix/certificati
sudo journalctl -u remotix -o cat --no-pager | grep -E 'pronto|PAM|certificat' | head -8
sudo -u prova env -i LD_TRACE_LOADED_OBJECTS=1 /usr/libexec/remotix/remotix | grep -c 'not found'" \
	>"$E/stato-installato.txt" 2>&1
sed 's/^/   /' "$E/stato-installato.txt"
impronta installato

echo "==> il browser vero (Chrome) su 127.0.0.1:$PRX"
T1C=$R/t1c bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser.log" 2>&1
echo "   uscita $? — $(grep -E '^T1C ' "$E/browser.log" | cut -c1-300)"
vm "sudo journalctl -u remotix -o cat --no-pager | tail -40" >"$E/journal-browser.txt" 2>&1
impronta browser

echo "==> reinstallazione (R5)"
vm "sudo DEBIAN_FRONTEND=noninteractive apt-get install -y --reinstall $D" >"$E/reinstalla.log" 2>&1
echo "   uscita $?"
impronta reinstallato
diff "$E/impronta-browser.txt" "$E/impronta-reinstallato.txt" >"$E/diff-R5.txt"
echo "   R5: $(grep -c '^[<>]' "$E/diff-R5.txt") righe diverse fra «browser» e «reinstallato»"

echo "==> apt-get purge remotix (R6)"
vm "sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y remotix" >"$E/purge.log" 2>&1
echo "   uscita $?"; grep -E '^remotix:' "$E/purge.log" | sed 's/^/   /'
vm "id prova; id nicfio; ls -la /var/lib/remotix /etc/remotix 2>&1" | tee "$E/persone-dopo.txt" | sed 's/^/   /'
impronta purge
vm "sudo DEBIAN_FRONTEND=noninteractive apt-get autoremove --purge -y" >"$E/autoremove.log" 2>&1
impronta autoremove
for x in installato purge autoremove; do
	diff "$E/impronta-prima.txt" "$E/impronta-$x.txt" >"$E/diff-prima-$x.txt"
	echo "   prima → $x: $(grep -c '^[<>]' "$E/diff-prima-$x.txt") righe diverse"
done
