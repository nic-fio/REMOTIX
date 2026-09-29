#!/bin/bash
#
# 17-t4-motore.sh — fase 17, T4-T5: il giro COMPLETO del motore su una VM «cliente».
#
#   (sul server, come nicfio)
#   sg kvm -c 'bash 17-t4-motore.sh <macchina> <remotix-install> <pacchetto>'
#     es. bash 17-t4-motore.sh debian13-gnome $T4/remotix-install $T4/remotix_…+deb13_amd64.deb
#
# Il copione di §7.3 col MOTORE al posto dei passi a mano di T3 (17-t3-prova.sh):
#   0. foto «cliente», accensione; la persona «prova», GIA' nel gruppo del nodo card (R33);
#   1. impronta «prima» (17-t3-impronta.sh);
#   2. remotix-install verifica; piano --installa --pacchetto; approva; applica: il motore fa
#      installare il pacchetto al gestore (insieme risolto, dalla cache), iscrive ai gruppi, accende
#      le cinture, accende il servizio via D-Bus, e verifica; impronta «installato»;
#   3. un browser VERO entra e vede il desktop (17-t1c-guarda.sh, Chrome);
#   4. R43: «prova» apre anche una sessione ssh con un processo che scrive l'ora ogni secondo;
#   5. remotix-install disinstalla --purge; approva; applica: le sessioni REMOTIX si chiudono (solo
#      quelle), si ripercorre il registro; impronta «disinstallato» e confronto con «prima»;
#      il processo della sessione ssh deve essere ancora vivo;
#   6. spegne e torna a «cliente» (anche se la prova cade).
# Evidenze in $T4/esiti/<macchina>/.
set -uo pipefail
m=${1:?macchina}; MOT=${2:?remotix-install}; PKG=${3:?pacchetto}
R=/media/REMOTIX/vm17
T4=${T4:-$R/t4}
QUI=$(cd "$(dirname "$0")" && pwd)
E=$T4/esiti/$m
V="bash $R/17-vm.sh"
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
# la famiglia decide l'impronta; PIANO_OPZ aggiunge al piano (es. --deposito packman su openSUSE)
IMPRONTA=17-t3-impronta.sh
case $m in
debian13|debian13-*) n=1;; ubuntu2604|ubuntu2604-*) n=2;;
fedora44|fedora44-*) n=3; IMPRONTA=17-t3-impronta-rpm.sh;;
arch|arch-*) n=4; IMPRONTA=17-t3-impronta-arch.sh;;
tumbleweed|tumbleweed-*) n=5; IMPRONTA=17-t3-impronta-rpm.sh;;
leap16|leap16-*) n=6; IMPRONTA=17-t3-impronta-rpm.sh;;
alma10|alma10-*) n=7; IMPRONTA=17-t3-impronta-rpm.sh;;
*) echo "macchina sconosciuta: $m"; exit 2;;
esac
PIANO_OPZ=${PIANO_OPZ:-}
k=0  # la macchina «nuda», senza desktop: R38, il motore lo installa (DESKTOP=lxqt … nell'ambiente)
case $m in *-*) case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac ;; esac
DESKTOP=${DESKTOP:-}
PSSH=$((2300 + 10 * n + k)); PRX=$((7500 + 10 * n + k))
CH=$R/ssh/id_ed25519
O="-i $CH -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
vm() { $V ssh "$m" "$@"; }
impronta() { vm 'sudo bash -s' <"$QUI/$IMPRONTA" >"$E/impronta-$1.txt" 2>"$E/impronta-$1.err"
             echo "   impronta «$1»: $(wc -l <"$E/impronta-$1.txt") righe"; }
# la macchina «nuda» non ha la foto «cliente»: si rifà dall'immagine (azzera), prima e dopo
torna() { if [ "$k" = 0 ]; then $V azzera "$m"; else $V torna "$m" cliente; fi; }
fine() { [ -n "${OROLOGIO:-}" ] && kill "$OROLOGIO" 2>/dev/null
         echo "==> spengo e torno com'era"; $V ferma "$m" >/dev/null 2>&1; torna >/dev/null 2>&1; }

mkdir -p "$E"; rm -f "$E"/*
if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m e' gia' accesa: la usa qualcun altro"; exit 2; fi
[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ gia' 4 VM accese"; exit 2; }
trap fine EXIT
echo "==> $m: foto «cliente», accensione"
torna || exit 1
$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }

echo "==> la persona «prova», gia' nel gruppo del nodo card (R33); la sua chiave ssh per R43"
vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
G=\$(for x in /dev/dri/card[0-9]*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u | head -1)
[ -n \"\$G\" ] && sudo gpasswd -a prova \"\$G\" >/dev/null
sudo install -d -m 700 -o prova -g prova ~prova/.ssh
sudo install -m 600 -o prova -g prova ~/.ssh/authorized_keys ~prova/.ssh/authorized_keys
ls -l /dev/dri/; id prova" | tee "$E/persone-prima.txt"
impronta prima

echo "==> il motore e il pacchetto nella VM"
# shellcheck disable=SC2086
scp -q $O -P "$PSSH" "$MOT" "$PKG" nicfio@localhost:/tmp/ || exit 1
D=/tmp/$(basename "$PKG")
vm "sudo install -m 755 /tmp/remotix-install /root/remotix-install"

echo "==> 2. verifica, piano, approva, applica (da root)"
vm "sudo /root/remotix-install verifica --lingua it" >"$E/verifica.txt" 2>&1; echo "   verifica: uscita $?"
vm "cd /tmp && sudo /root/remotix-install piano --installa --pacchetto $D --utente prova $PIANO_OPZ --uscita /root/piano.json --lingua it" >"$E/piano.txt" 2>&1
echo "   piano: uscita $? — $(grep -c '^[0-9]*\. ' "$E/piano.txt") passi"
vm "sudo /root/remotix-install approva /root/piano.json ${DESKTOP:+--desktop $DESKTOP} --lingua it" >>"$E/piano.txt" 2>&1
[ -n "$DESKTOP" ] && vm "echo bersaglio: \$(systemctl get-default); echo display manager: \$(systemctl is-enabled display-manager.service 2>&1) \$(systemctl is-active display-manager.service 2>&1)" | sed 's/^/   prima: /' 
T0=$(date +%s)
vm "sudo /root/remotix-install applica /root/piano.json --senza-firma --lingua it" >"$E/applica.txt" 2>&1
echo "   applica: uscita $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operazione ' "$E/applica.txt")"
vm "echo servizio: \$(systemctl is-enabled remotix) \$(systemctl is-active remotix)
echo bersaglio: \$(systemctl get-default); for u in gdm3 sddm lightdm display-manager; do echo \"\$u: \$(systemctl is-enabled \$u.service 2>&1) \$(systemctl is-active \$u.service 2>&1)\"; done; ls /usr/sbin/policy-rc.d 2>&1
echo in ascolto sulla 7447: \$(sudo ss -Htulpn | grep -c ':7447 ')
id prova
systemd-analyze cat-config systemd/logind.conf | grep -c '^HandlePowerKey=ignore' | sed 's/^/cintura tasti in vigore: /'
sudo cat /var/lib/remotix/installazione.json
sudo sh -c 'cat /var/lib/remotix/operazioni/*/certificato.txt'
sudo sh -c 'grep -h COMANDO /var/lib/remotix/operazioni/*/registro.jsonl' | sed 's/.*dettaglio\":\"//; s/\"}//'" >"$E/installato.txt" 2>&1
sed 's/^/   /' "$E/installato.txt" | head -60
impronta installato

echo "==> 2b. certifica (sola lettura) sulla macchina sana"
vm "sudo /root/remotix-install certifica --lingua it; echo uscita \$?" >"$E/certifica.txt" 2>&1
sed 's/^/   /' "$E/certifica.txt" | grep -E 'Certificazione|uscita|FAIL|UNKNOWN|C-'
if [ -n "${R29:-}" ]; then
	echo "==> R29: la certificazione su una macchina guasta apposta non dice mai VERDE"
	# tutto in UN sudo: una pila PAM rotta romperebbe anche i sudo successivi
	vm "sudo bash -s" >"$E/r29.txt" 2>&1 <<'R29'
L=$(ls /usr/lib/x86_64-linux-gnu/libx264.so.* /usr/lib64/libx264.so.* /usr/lib/libx264.so.* 2>/dev/null | head -1)
P=$(ls /etc/pam.d/remotix /usr/lib/pam.d/remotix 2>/dev/null | head -1)
c() { /root/remotix-install certifica --lingua it | grep -E "Certificazione|$1"; }
echo "-- guasto 1: la pila PAM di REMOTIX nomina un modulo che non c'è"; cp -a $P /root/pam-via; echo "auth required pam_non_esiste.so" >> $P; c pam-risolta; cp -a /root/pam-via $P
echo "-- guasto 2: niente libx264 ($L) e niente VA-API: la codifica non riesce"; mv $L /root/x264-via; c codifica; mv /root/x264-via $L
echo "-- guasto 3: il servizio spento da altri"; systemctl stop remotix; c servizio; systemctl start remotix; sleep 3
echo "-- di nuovo com'era"; c Certificazione
R29

	sed 's/^/   /' "$E/r29.txt"
fi

echo "==> 3. il browser vero (Chrome) su 127.0.0.1:$PRX"
T1C=$R/t1c bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser.log" 2>&1
echo "   uscita $? — $(grep -E '^T1C ' "$E/browser.log" | cut -c1-300)"

echo "==> 4. R43: una sessione ssh di «prova» con un orologio"
# shellcheck disable=SC2086
ssh $O -p "$PSSH" prova@localhost 'while :; do date +%s >> ~/orologio.txt; sleep 1; done' &
OROLOGIO=$!
sleep 4
vm "loginctl list-sessions --no-legend; for s in \$(loginctl list-sessions --no-legend | awk '{print \$1}'); do echo \"\$s \$(loginctl show-session \$s -p Service -p Name -p State --value | tr '\n' ' ')\"; done
echo processi di prova: \$(pgrep -u prova | wc -l)
ps -o pid,cgroup:70,comm -u prova" >"$E/sessioni-prima.txt" 2>&1
sed 's/^/   /' "$E/sessioni-prima.txt"

echo "==> 5. disinstalla --purge, approva, applica"
vm "sudo /root/remotix-install disinstalla --purge --uscita /root/disinstalla.json --lingua it" >"$E/disinstalla-piano.txt" 2>&1
echo "   piano: uscita $? — $(grep -c '^[0-9]*\. ' "$E/disinstalla-piano.txt") passi"
vm "sudo /root/remotix-install approva /root/disinstalla.json --lingua it" >>"$E/disinstalla-piano.txt" 2>&1
T0=$(date +%s)
vm "sudo /root/remotix-install applica /root/disinstalla.json --senza-firma --lingua it" >"$E/disinstalla.txt" 2>&1
echo "   applica: uscita $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operazione ' "$E/disinstalla.txt")"
sleep 3
vm "for s in \$(loginctl list-sessions --no-legend | awk '{print \$1}'); do echo \"\$s \$(loginctl show-session \$s -p Service -p Name -p State --value | tr '\n' ' ')\"; done
a=\$(sudo tail -1 ~prova/orologio.txt); sleep 3; b=\$(sudo tail -1 ~prova/orologio.txt); echo orologio ssh: \$a → \$b
echo processi di prova: \$(pgrep -u prova | wc -l); echo gnome-shell/kwin/labwc/plasmashell di prova: \$(pgrep -u prova -c -x 'gnome-shell|kwin_wayland|labwc|plasmashell|lxqt-panel|xfce4-panel')
sudo bash -c 'n=0; for p in \$(pgrep -u prova); do grep -q user@ /proc/\$p/cgroup 2>/dev/null && tr \"\\\\0\" \"\\\\n\" < /proc/\$p/environ 2>/dev/null | grep -qE \"^(WAYLAND_)?DISPLAY=\" && n=\$((n+1)); done; echo processi grafici nel gestore d utente: \$n'
ps -o pid,cgroup:70,comm -u prova
echo servizio: \$(systemctl is-enabled remotix 2>&1) \$(systemctl is-active remotix 2>&1)
(dpkg -l remotix 2>/dev/null | tail -1 || true; rpm -q remotix 2>/dev/null; pacman -Q remotix 2>/dev/null); id prova
sudo ls /var/lib/remotix /var/lib/remotix/operazioni; sudo sh -c 'cat /var/lib/remotix/operazioni/*/certificato.txt' | grep -A30 'stato finale: CONFERMATA\$' | tail -30" >"$E/dopo.txt" 2>&1
sed 's/^/   /' "$E/dopo.txt" | head -60
kill "$OROLOGIO" 2>/dev/null; OROLOGIO=
vm "sudo rm -f ~prova/orologio.txt"
impronta disinstallato
diff "$E/impronta-prima.txt" "$E/impronta-disinstallato.txt" >"$E/diff-R6.txt"
echo "   R6: $(grep -c '^[<>]' "$E/diff-R6.txt") righe diverse fra «prima» e «disinstallato» (in $E/diff-R6.txt)"
