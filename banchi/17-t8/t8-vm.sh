#!/bin/bash
#
# ⛔ STORIA (10 ott 2026, DECISIONI §10.36): questo banco prova un installatore che non c'è più —
#   piano/approva/applica separati, archivio firmato e install.sh, archivi di terzi, firewall e
#   cinture messi dal motore, file di risposte. Oggi: un .run, `install` con la domanda [y/N], e
#   REMOTIX che non modifica il sistema. Resta come storia delle prove del 29 set - 1 ott 2026; il giro
#   vero è banchi/17-distro/17-t10.sh. Non si lancia.
#
# t8-vm.sh — fase 17, T8: REMOTIX dall'ARCHIVIO firmato, su una VM «cliente», un passo per chiamata.
#
#   (sul server, come nicfio)   sg kvm -c 'bash t8-vm.sh <macchina> <passo> [argomenti]'
#
#   accendi                 foto «cliente», accensione; la persona «prova» già nel gruppo del nodo
#   terzi                   R18: un archivio DI TERZI già configurato (chiave sua, pacchetto suo)
#   impronta <nome>         l'impronta della macchina (17-t3-impronta*.sh) e dei depositi (R18)
#   motore                  il motore scaricato DALL'ARCHIVIO (come fa install.sh) e il suo sha256
#   installa [canale]       verifica → piano --installa --archivio → approva → applica
#   script                  come l'amministratore: install.sh e il suo sha256 dall'archivio, il
#                           controllo (sha256sum -c), poi `sh install.sh --archivio … --risposte …`
#   aggiorna                l'aggiornamento DEL SISTEMA (apt-get upgrade · dnf upgrade): REMOTIX
#                           viene con lui (DECISIONI §10.23); il giornale di remotix.service
#   disinstalla             disinstalla --purge → applica, e che cosa resta di REMOTIX
#   stato                   versioni, servizio, operazioni, certificato, catalogo
#   collega                 un Chrome vero entra e RESTA collegato (t8-browser.py) — in secondo piano
#   via                     il browser collegato ricarica e rientra: deve rivedere il desktop
#   palco                   i processi del desktop di «prova» (pid): prima e dopo devono combaciare
#   motore-cmd "<arg>"      remotix-install <arg> nella VM (da root)
#   spegni                  spegne e torna a «cliente»
#
# L'archivio sta in /media/REMOTIX/vm17/archivio/, servito su 127.0.0.1:8717 (dalla VM: 10.0.2.2);
# un altro con ARCH=http://10.0.2.2:<porta> (t8-porta.sh con DOVE e PORTA).
# ⛔ Al massimo 2 VM di questo banco e 4 in tutto; non spegne una macchina già accesa da altri.
# Evidenze in /media/REMOTIX/vm17/t8/esiti/<macchina>/.
set -uo pipefail
m=${1:?macchina}; passo=${2:?passo}; shift 2
R=/media/REMOTIX/vm17
T8=${T8:-$R/t8}
QUI=$(cd "$(dirname "$0")" && pwd)
E=$T8/esiti/$m
V="bash $R/17-vm.sh"
ARCH=${ARCH:-http://10.0.2.2:8717}
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
IMPRONTA=17-t3-impronta.sh
case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;;
fedora44-*) n=3; IMPRONTA=17-t3-impronta-rpm.sh;;
arch-*) n=4; IMPRONTA=17-t3-impronta-arch.sh;;
*) echo "macchina sconosciuta: $m"; exit 2;;
esac
k=0; case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
PSSH=$((2300 + 10 * n + k)); PRX=$((7500 + 10 * n + k))
mkdir -p "$E"
vm() { $V ssh "$m" "$@"; }
t() { date +%H:%M:%S; }

case $passo in
accendi)
	if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m è già accesa"; exit 2; fi
	[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ già 4 VM accese"; exit 2; }
	rm -rf "$E"; mkdir -p "$E"
	$V torna "$m" cliente >/dev/null || exit 1
	$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
	vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
G=\$(for x in /dev/dri/card[0-9]*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u | head -1)
[ -n \"\$G\" ] && sudo gpasswd -a prova \"\$G\" >/dev/null
id prova; curl -s -o /dev/null -w 'archivio: HTTP %{http_code}\n' $ARCH/chiavi/LEGGIMI" | tee "$E/accendi.txt"
	;;
terzi)
	# R18: un archivio di terzi configurato PRIMA di REMOTIX (servito dallo stesso server, con la
	# sua chiave); dopo l'installazione i suoi file e la sua chiave devono essere identici
	case $n in
	1) vm "sudo install -d -m 755 /etc/apt/keyrings
curl -s http://10.0.2.2:8719/terzi.asc -o /tmp/terzi.asc
sudo install -m 644 /tmp/terzi.asc /etc/apt/keyrings/terzi.asc
printf 'Types: deb\nURIs: http://10.0.2.2:8719/deb\nSuites: terzi\nComponents: main\nSigned-By: /etc/apt/keyrings/terzi.asc\n' | sudo tee /etc/apt/sources.list.d/terzi.sources >/dev/null
sudo apt-get update 2>&1 | tail -2; sudo apt-get install -y terzi-prova 2>&1 | tail -1; dpkg -l terzi-prova | tail -1" ;;
	3) vm "curl -s http://10.0.2.2:8719/terzi.asc | sudo tee /etc/pki/rpm-gpg/RPM-GPG-KEY-terzi >/dev/null
printf '[terzi]\nname=terzi\nbaseurl=http://10.0.2.2:8719/rpm/\nenabled=1\ngpgcheck=1\nrepo_gpgcheck=1\ngpgkey=file:///etc/pki/rpm-gpg/RPM-GPG-KEY-terzi\n' | sudo tee /etc/yum.repos.d/terzi.repo >/dev/null
sudo dnf install -y terzi-prova 2>&1 | tail -2; rpm -q terzi-prova" ;;
	*) echo "terzi: solo debian13 e fedora44"; exit 2 ;;
	esac 2>&1 | tee "$E/terzi.txt"
	;;
impronta)
	nome=${1:?nome}
	vm 'sudo bash -s' <"$R/t4/$IMPRONTA" >"$E/impronta-$nome.txt" 2>"$E/impronta-$nome.err"
	vm "sudo sh -c 'for f in /etc/apt/sources.list.d/* /etc/apt/keyrings/* /etc/apt/trusted.gpg.d/* /etc/apt/preferences.d/* /usr/share/keyrings/* /etc/yum.repos.d/* /etc/pki/rpm-gpg/* /etc/pacman.conf; do [ -f \$f ] && sha256sum \$f; done 2>/dev/null; ls -la /etc/apt/trusted.gpg.d 2>/dev/null; rpm -q gpg-pubkey 2>/dev/null; pacman-key --list-keys 2>/dev/null | grep -c ^pub'" >"$E/depositi-$nome.txt" 2>&1
	echo "   impronta «$nome»: $(wc -l <"$E/impronta-$nome.txt") righe; depositi: $(wc -l <"$E/depositi-$nome.txt") righe"
	;;
motore)
	vm "cd /tmp && curl -sf $ARCH/engine/remotix-install -o remotix-install && curl -sf $ARCH/engine/remotix-install.sha256 -o remotix-install.sha256
sha256sum -c remotix-install.sha256; echo \"sha256: uscita \$?\"
sudo install -m 755 /tmp/remotix-install /root/remotix-install
sudo /root/remotix-install version" | tee "$E/motore.txt"
	;;
script)
	# le risposte: la persona «prova» nei gruppi della scheda; firewall e RPM Fusion col consenso (D5,
	# D6: il motore annota quelli che su questa macchina non servono)
	vm "printf 'format = remotix-answers/2\nusers = prova\nconsent.firewall = yes\n' | sudo tee /root/risposte.conf >/dev/null
[ -e /etc/fedora-release ] && echo 'consent.repo.rpmfusion = yes' | sudo tee -a /root/risposte.conf >/dev/null
cd /tmp && curl -sf $ARCH/install.sh -o install.sh && curl -sf $ARCH/install.sh.sha256 -o install.sh.sha256
sha256sum -c install.sh.sha256 && grep -E '^SHA256_MOTORE=' install.sh" >"$E/script.txt" 2>&1
	echo "   install.sh: $(grep -E 'install.sh: ' "$E/script.txt")"
	T0=$(date +%s)
	vm "cd /tmp && sudo sh install.sh --archive $ARCH --answers /root/risposte.conf" >>"$E/script.txt" 2>&1
	echo "   install.sh --answers: uscita $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operation |Engine VERIFIED' "$E/script.txt" | tr '\n' ' ')"
	grep -E 'FALLITA|BLOCCATA|RX-' "$E/script.txt" | head -8 | sed 's/^/   /'
	;;
aggiorna)
	T0=$(date +%s)
	vm "if command -v apt-get >/dev/null; then sudo apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -q; else sudo dnf upgrade -y --refresh; fi
echo \"uscita: \$?\"
echo --- remotix.service:
sudo journalctl -u remotix.service --since @$T0 --no-pager -o short-unix | grep -aE 'RITROVAT|pronto|avvio|Stopp|Start' | tail -12" >"$E/aggiorna-$(t).txt" 2>&1
	echo "   aggiornamento del sistema in $(( $(date +%s) - T0 )) s: $(grep -cE '^(Setting up|Configurazione di|  Upgrading|  Aggiornamento|  Upgraded)' "$E"/aggiorna-*.txt | tail -1) righe di pacchetti"
	grep -aE 'remotix|installazione certificata|versioni di REMOTIX|RX-|uscita:|RITROVAT' "$E"/aggiorna-*.txt | tail -16 | cut -c1-220 | sed 's/^/   /'
	;;
disinstalla)
	vm "sudo /usr/bin/remotix-install uninstall --purge --output /root/d.json >/dev/null && sudo /usr/bin/remotix-install apply /root/d.json --approve" >"$E/disinstalla.txt" 2>&1
	echo "   disinstalla: uscita $? — $(grep -E '^operation ' "$E/disinstalla.txt")"
	grep -E 'FALLITA|BLOCCATA|RX-' "$E/disinstalla.txt" | head -6 | sed 's/^/   /'
	vm "echo \"pacchetti rimasti: \$( (dpkg-query -W -f='\${Package} ' 'remotix*' 2>/dev/null; rpm -qa 'remotix*' 2>/dev/null) | tr '\n' ' ')\"
echo \"archivi: \$(ls /etc/apt/sources.list.d /etc/yum.repos.d 2>/dev/null | grep -ci remotix) · servizio: \$(systemctl is-active remotix 2>&1) · /var/lib/remotix: \$(sudo ls /var/lib/remotix 2>&1 | tr '\n' ' ')\"" | tee -a "$E/disinstalla.txt"
	;;
installa)
	canale=${1:-stabile}
	vm "sudo /root/remotix-install check --archive $ARCH --channel $canale" >"$E/verifica.txt" 2>&1; echo "   verifica: uscita $?"
	grep -E '^Fiducia|^Catalogo' "$E/verifica.txt" | sed 's/^/   /'
	vm "cd /tmp && sudo /root/remotix-install plan --install --archive $ARCH --channel $canale --users prova ${PIANO_OPZ:-} --output /root/piano.json" >"$E/piano.txt" 2>&1
	echo "   piano: uscita $? — $(grep -c '^[0-9]*\. ' "$E/piano.txt") passi"
	vm "sudo /root/remotix-install approve /root/piano.json" >>"$E/piano.txt" 2>&1
	T0=$(date +%s)
	vm "sudo /root/remotix-install apply /root/piano.json" >"$E/applica.txt" 2>&1
	echo "   applica: uscita $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operation ' "$E/applica.txt")"
	grep -E 'FALLITA|BLOCCATA|RX-' "$E/applica.txt" | head -8 | sed 's/^/   /'
	;;
stato)
	vm "echo \"pacchetti: \$( (dpkg-query -W -f='\${Package}=\${Version} ' remotix remotix-install remotix-archive-keyring 2>/dev/null; rpm -q remotix remotix-install remotix-selinux 2>/dev/null; pacman -Q remotix remotix-install 2>/dev/null) | tr '\n' ' ')\"
echo \"servizio: \$(systemctl is-enabled remotix) \$(systemctl is-active remotix) · pid \$(systemctl show -p MainPID --value remotix)\"
sudo /usr/bin/remotix-install status
sudo /usr/bin/remotix-install catalog 2>&1 | head -1
sudo /usr/bin/remotix-install certify 2>&1 | head -1
sudo sh -c 'cat /var/lib/remotix/recorded-versions.json 2>/dev/null'; echo" 2>&1 | tee "$E/stato-$(t).txt"
	;;
collega)
	rm -rf "$E/browser"; mkdir -p "$E/browser"
	T1C=$R/t1c T1C_PROGRAMMA=$QUI/t8-browser.py T1C_EVIDENZE=$E/browser \
		setsid nohup bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser.log" 2>&1 </dev/null &
	for _ in $(seq 1 120); do [ -f "$E/browser/pronto" ] && break; grep -q '^T8 ' "$E/browser.log" && break; sleep 1; done
	if [ -f "$E/browser/pronto" ]; then echo "   collegato: il desktop si vede ($(t))"; else echo "   ⛔ non collegato:"; tail -3 "$E/browser.log"; fi
	;;
via)
	touch "$E/browser/via"
	for _ in $(seq 1 240); do grep -q '^T8 ' "$E/browser.log" && break; sleep 1; done
	grep '^T8 ' "$E/browser.log" | cut -c1-700
	;;
palco)
	vm "for p in gnome-shell kwin_wayland plasmashell labwc; do for x in \$(pgrep -u prova -x \$p); do echo \"\$p \$x \$(ps -o lstart= -p \$x)\"; done; done
echo processi di prova: \$(pgrep -u prova | wc -l)
loginctl list-sessions --no-legend | grep prova" | tee "$E/palco-$(t).txt"
	;;
motore-cmd)
	vm "sudo /usr/bin/remotix-install $*" 2>&1 | tee -a "$E/comandi.txt"
	;;
spegni)
	$V ferma "$m" >/dev/null 2>&1; $V torna "$m" cliente >/dev/null 2>&1; echo "   $m spenta, tornata a «cliente»"
	;;
*) sed -n 3,27p "$0"; exit 2 ;;
esac
