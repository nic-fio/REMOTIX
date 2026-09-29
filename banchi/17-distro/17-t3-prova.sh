#!/bin/bash
#
# 17-t3-prova.sh — fase 17, T3: il pacchetto NATIVO su una VM «cliente», R4 R5 R6 in piccolo.
#
#   (sul server, come nicfio)
#   sg kvm -c 'bash 17-t3-prova.sh <macchina> <file.deb>'
#     es.  bash 17-t3-prova.sh debian13-gnome /media/REMOTIX/vm17/t3/remotix_…+deb13_amd64.deb
#
# Il copione di §7.3, senza l'installatore (che e' di T4-T5): il gestore di
# pacchetti, e i «passi del motore» fatti A MANO e dichiarati come tali.
# ⛔ DECISIONI §10.12: il pacchetto porta solo pezzi INERTI (R40).
#   0. torna alla foto «cliente» e accende;
#   1. una persona sulla macchina, `prova`, GIA' nel gruppo del nodo cardN (di
#      solito `video`): cosi' si vede se qualcuno la tocca;
#   2. impronta «prima» (17-t3-impronta.sh);
#   3. `apt-get install ./remotix_….deb` e NIENT'ALTRO (R4); impronta.  R40:
#      servizio non abilitato ne' attivo, niente in ascolto sulla 7447, gruppi
#      e cinture in vigore invariati;
#   4. R40: `systemctl start remotix` deve RIFIUTARE con RX-INST-001;
#   5. ⚠ I PASSI DEL MOTORE, A MANO (sono di T4-T5, qui solo per far vedere il
#      desktop): `prova` nei gruppi dei nodi, le tre cinture copiate da
#      /usr/share/remotix/cinture/ in /etc/{polkit-1/rules.d,systemd/logind.conf.d,
#      systemd/sleep.conf.d}/, la marca /var/lib/remotix/installazione-confermata,
#      `systemctl enable --now remotix`;
#   6. un browser vero entra e deve vedere il desktop (17-t1c-guarda.sh, Chrome,
#      127.0.0.1); impronta;
#   7. reinstallazione (`--reinstall`): impronta uguale a quella del punto 6 (R5);
#   8. i passi del motore DISFATTI a mano, poi `apt-get purge remotix`: impronta;
#      poi `apt-get autoremove --purge`: impronta.  I confronti con «prima» si
#      CLASSIFICANO nel rapporto (DIRETTA, INDIRETTA, PREESISTENTE: §6.6.4);
#   9. spegne e torna alla foto «cliente».
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
vm "echo abilitato: \$(systemctl is-enabled remotix 2>&1); echo attivo: \$(systemctl is-active remotix 2>&1)
echo in ascolto sulla 7447: \$(sudo ss -Htulpn | grep -c ':7447 ')
id prova; id nicfio
systemd-analyze cat-config systemd/logind.conf | grep -c '^HandlePowerKey=ignore' | sed 's/^/cintura tasti in vigore: /'
systemd-analyze cat-config systemd/sleep.conf | grep -c '^AllowSuspend=no' | sed 's/^/cintura sospensione in vigore: /'
ls /etc/polkit-1/rules.d /usr/share/polkit-1/rules.d | grep -c remotix | sed 's/^/regola polkit in vigore: /'
sudo ls -la /var/lib/remotix
sudo -u prova env -i LD_TRACE_LOADED_OBJECTS=1 /usr/libexec/remotix/remotix | grep -c 'not found' | sed 's/^/librerie mancanti (da prova, ambiente vuoto): /'" \
	>"$E/R40-installato.txt" 2>&1
sed 's/^/   /' "$E/R40-installato.txt"
impronta installato

echo "==> R40: systemctl start remotix, senza installatore"
vm "sudo systemctl start remotix; echo uscita \$?; sleep 3; echo attivo: \$(systemctl is-active remotix)
echo in ascolto sulla 7447: \$(sudo ss -Htulpn | grep -c ':7447 ')
sudo journalctl -u remotix -o cat --no-pager | grep -E 'RX-INST|Failed|exit' | tail -4
echo avvii: \$(systemctl show remotix -p NRestarts --value) ripartenze
sudo systemctl reset-failed remotix" >"$E/R40-start.txt" 2>&1
sed 's/^/   /' "$E/R40-start.txt"

echo "==> ⚠ I PASSI DEL MOTORE, fatti A MANO (T4-T5): gruppi, cinture, marca, enable --now"
vm "G=\$(for x in /dev/dri/card[0-9]* /dev/dri/renderD[0-9]*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u)
for g in \$G; do id -nG prova | tr ' ' '\\n' | grep -qx \$g || { sudo gpasswd -a prova \$g >/dev/null; echo \"gruppo: prova + \$g\"; }; done
for d in /etc/polkit-1/rules.d /etc/systemd/logind.conf.d /etc/systemd/sleep.conf.d; do [ -d \$d ] || echo \"cartella nuova: \$d\"; done
sudo install -D -m 644 /usr/share/remotix/cinture/50-remotix-niente-spegnimento.rules /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules
sudo install -D -m 644 /usr/share/remotix/cinture/remotix-tasti.conf /etc/systemd/logind.conf.d/remotix-tasti.conf
sudo install -D -m 644 /usr/share/remotix/cinture/remotix-niente-sospensione.conf /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf
sudo systemctl reload systemd-logind; echo cinture: 3 file in /etc
sudo touch /var/lib/remotix/installazione-confermata; echo marca: installazione-confermata
sudo systemctl enable --now remotix 2>&1 | tail -1; sleep 2; echo attivo: \$(systemctl is-active remotix)
echo in ascolto sulla 7447: \$(sudo ss -Htulpn | grep -c ':7447 ')" >"$E/passi-motore.txt" 2>&1
sed 's/^/   /' "$E/passi-motore.txt"
impronta motore

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

echo "==> ⚠ i passi del motore DISFATTI a mano, poi apt-get purge remotix (R6)"
NUOVE=$(sed -n 's/^cartella nuova: //p' "$E/passi-motore.txt" | tr '\n' ' ')
vm "sudo systemctl disable --now remotix 2>&1 | tail -1
sudo rm -f /etc/polkit-1/rules.d/50-remotix-niente-spegnimento.rules /etc/systemd/logind.conf.d/remotix-tasti.conf /etc/systemd/sleep.conf.d/remotix-niente-sospensione.conf
for d in $NUOVE; do sudo rmdir \$d && echo tolta la cartella \$d; done
sudo systemctl reload systemd-logind
sudo rm -f /var/lib/remotix/installazione-confermata" >"$E/passi-disfatti.txt" 2>&1
for g in $(sed -n 's/^gruppo: prova + //p' "$E/passi-motore.txt"); do vm "sudo gpasswd -d prova $g >/dev/null && echo 'disfatto: prova - $g'"; done >>"$E/passi-disfatti.txt" 2>&1
sed 's/^/   /' "$E/passi-disfatti.txt"
vm "sudo DEBIAN_FRONTEND=noninteractive apt-get purge -y remotix" >"$E/purge.log" 2>&1
echo "   uscita $?"; grep -E '^remotix:' "$E/purge.log" | sed 's/^/   /'
vm "id prova; id nicfio; ls -la /var/lib/remotix /etc/remotix 2>&1" | tee "$E/persone-dopo.txt" | sed 's/^/   /'
impronta purge
vm "sudo DEBIAN_FRONTEND=noninteractive apt-get autoremove --purge -y" >"$E/autoremove.log" 2>&1
impronta autoremove
for x in installato motore purge autoremove; do
	diff "$E/impronta-prima.txt" "$E/impronta-$x.txt" >"$E/diff-prima-$x.txt"
	echo "   prima → $x: $(grep -c '^[<>]' "$E/diff-prima-$x.txt") righe diverse"
done
