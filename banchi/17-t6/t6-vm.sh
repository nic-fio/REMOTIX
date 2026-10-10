#!/bin/bash
#
# t6-vm.sh — fase 17, T6: PAM (R20), SELinux (R19) e firewall su una VM, un passo per chiamata.
#
#   (sul server, come nicfio)   sg kvm -c 'bash t6-vm.sh <macchina> <passo> [argomenti]'
#
#   accendi <foto>            foto «iso» o «cliente», accensione; la persona «prova» con la sua parola
#   motore <file…>            il motore (/media/REMOTIX/vm17/t6/remotix-install) e i pacchetti nella VM
#   installa "<opzioni>"      verifica → piano --installa --pacchetto <i file portati> <opzioni> →
#                             approva → applica
#   entra [utente] [parola]   un Chrome vero entra (17-t1c-guarda.sh); con utente/parola diversi: il
#                             rifiuto atteso
#   sessione                  le sessioni logind di «prova»: Class, Remote, Service, Type; e i contesti
#                             SELinux del servizio e del palco
#   avc [dal]                 i rifiuti SELinux dall'accensione (o da «dal», hh:mm:ss): ausearch e giornale
#   modulo <file.pp>          un modulo SELinux compilato a parte al posto di quello del pacchetto
#   ban-via                   il ban di REMOTIX tolto (servizio fermo, file via, servizio acceso)
#   faillock [reset]          lo stato di faillock di «prova» (e lo sblocco, come per ssh)
#   firewall                  firewalld: la zona, i servizi, le porte, i file in /etc/firewalld/zones
#   ssh-parola [parola]       ssh di «prova» con la parola d'ordine: il confronto con sshd (faillock)
#   disinstalla               disinstalla --purge, approva, applica
#   cmd "<comando>"           un comando da root nella VM
#   spegni <foto>             spegne e torna alla foto
#
# ⛔ Al massimo 2 VM di questo banco e 4 in tutto; non spegne una macchina accesa da altri.
# Evidenze in /media/REMOTIX/vm17/t6/esiti/<macchina>/.
set -uo pipefail
m=${1:?macchina}; passo=${2:?passo}; shift 2
R=/media/REMOTIX/vm17
T6=$R/t6
E=$T6/esiti/$m
# ⚠ una copia di 17-vm.sh in t6/ (RX_VM): quello comune lo cambiano altri banchi mentre questo gira
# (`[M]` 30 set: «syntax error» a meta' giro)
V="bash ${RX_VM:-$R/17-vm.sh}"
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
case $m in
debian13-*) n=1;; ubuntu2604-*) n=2;; fedora44-*) n=3;; arch-*) n=4;;
tumbleweed-*) n=5;; leap16-*) n=6;; alma10-*) n=7;;
*) echo "macchina sconosciuta: $m"; exit 2;;
esac
k=0; case ${m#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
case $m in *-iso) k=5;; esac
PSSH=$((2300 + 10 * n + k)); PRX=$((7500 + 10 * n + k))
CH=$R/ssh/id_ed25519
O="-i $CH -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
mkdir -p "$E"
vm() { $V ssh "$m" "$@"; }
t() { date +%H:%M:%S; }

case $passo in
accendi)
	foto=${1:?foto}
	if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m è già accesa"; exit 2; fi
	[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ già 4 VM accese"; exit 2; }
	rm -rf "$E"; mkdir -p "$E"
	$V torna "$m" "$foto" >/dev/null || exit 1
	$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail "$E/avvia.log"; exit 1; }
	vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
echo \"prova: \$(id prova)\"; echo \"selinux: \$(getenforce 2>/dev/null || echo assente)\"; date +%T" | tee "$E/accendi.txt"
	vm "date +%T" >"$E/ora-accensione.txt"
	;;
motore)
	# shellcheck disable=SC2086
	scp -q $O -P "$PSSH" "$T6/remotix-install" "$@" nicfio@localhost:/tmp/ || exit 1
	vm "sudo install -m 755 /tmp/remotix-install /root/remotix-install; ls -la /tmp/*.rpm /tmp/*.deb /tmp/*.zst 2>/dev/null"
	f=""; for x in "$@"; do f="$f${f:+,}/tmp/$(basename "$x")"; done
	echo "$f" >"$E/pacchetti.txt"
	;;
installa)
	opz=${1:-}
	f=$(cat "$E/pacchetti.txt")
	vm "sudo /root/remotix-install check" >"$E/verifica.txt" 2>&1; echo "   verifica: uscita $?"
	grep -E 'RX-(PAM|SELINUX|FW)' "$E/verifica.txt" | head -8 | sed 's/^/   /'
	vm "cd /tmp && sudo /root/remotix-install plan --install --package $f --users prova $opz --output /root/piano.json" >"$E/piano.txt" 2>&1
	echo "   piano: uscita $? — $(grep -c '^[0-9]*\. ' "$E/piano.txt") passi"
	vm "sudo /root/remotix-install approve /root/piano.json" >>"$E/piano.txt" 2>&1
	T0=$(date +%s)
	vm "sudo /root/remotix-install apply /root/piano.json" >"$E/applica.txt" 2>&1
	echo "   applica: uscita $? in $(( $(date +%s) - T0 )) s — $(grep -E '^operation ' "$E/applica.txt")"
	grep -E 'FALLITA|BLOCCATA|RX-' "$E/applica.txt" | head -8 | sed 's/^/   /'
	vm "echo servizio: \$(systemctl is-enabled remotix) \$(systemctl is-active remotix); sudo ss -Htulpn | grep ':7447 '; ps -eZ 2>/dev/null | grep -E ' remotix$' ; ls -Z /usr/libexec/remotix/remotix /usr/lib/remotix/remotix 2>/dev/null; sudo semodule -l 2>/dev/null | grep remotix; rpm -q remotix remotix-selinux 2>/dev/null" | tee "$E/installato.txt" | sed 's/^/   /'
	;;
entra)
	u=${1:-prova}; p=${2:-$PAROLA}; tag=${3:-$u}
	cp -f "$T6/17-t1c-browser.py" "$T6/t1c-browser.py" 2>/dev/null
	T1C=$R/t1c T1C_UTENTE=$u REMOTIX_PAROLA_PROVA=$p T1C_EVIDENZE=$E/entra-$tag \
		bash "$T6/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/entra-$tag.log" 2>&1
	echo "   entra $u: uscita $? — $(grep -E '^T1C ' "$E/entra-$tag.log" | python3 -c 'import sys,json; r=json.loads(sys.stdin.read()[4:]); print(r.get("esito"), "|", r.get("ragione","")[:160], "|", r.get("entra","")[:120])' 2>/dev/null)"
	vm "sudo journalctl -t remotix --since '-3min' --no-pager -o cat | grep -aiE 'ammess|rifiut|pam|ban|negat' | tail -4" | cut -c1-240 | sed 's/^/   giornale: /'
	;;
sessione)
	vm "for s in \$(loginctl list-sessions --no-legend | awk '{print \$1}'); do echo \"\$s \$(loginctl show-session \$s -p Name -p Class -p Type -p Remote -p RemoteHost -p Service -p State | tr '\n' ' ')\"; done
ps -eZ 2>/dev/null | grep -E ' (remotix|gnome-shell|kwin_wayland|plasmashell|labwc)$' | sort -u -k4
sudo ls -Z /var/lib/remotix /run/remotix 2>/dev/null | head -12" | tee "$E/sessione-$(t).txt" | sed 's/^/   /'
	;;
avc)
	# ⚠ sulle macchine senza auditd (Fedora e Alma dall'ISO: `[M]` ausearch «no matches») i rifiuti
	#   stanno nel giornale (_TRANSPORT=audit): si leggono tutti e due
	dal=${1:-$(cat "$E/ora-accensione.txt" 2>/dev/null)}
	f=$E/avc-$(t).txt
	# ⚠ `[M]` su Alma `ausearch -ts` non trova i rifiuti che audit.log ha: si legge il file, col
	#   tempo di ogni riga (audit(EPOCA…)), e il giornale per le macchine senza auditd
	echo "$dal" >"$E/avc-dal.txt"
	vm "sudo sh -c 's=\$(date -d \"${dal:-today 00:00}\" +%s); (cat /var/log/audit/audit.log 2>/dev/null | awk -v s=\$s \"{ if (match(\\\$0, /audit\\\\([0-9]+/)) { e = substr(\\\$0, RSTART + 6, RLENGTH - 6); if (e + 0 >= s) print } }\"; journalctl -b --no-pager -o cat --since \"${dal:-today}\" _TRANSPORT=audit 2>/dev/null) | grep -aE \"avc: +denied|SELINUX_ERR\" | sort -u'" >"$f"
	sed -E 's/.*(avc: +denied +\{[^}]*\} for) +pid=[0-9]+ (comm="[^"]*").*(scontext=[^ ]*) (tcontext=[^ ]*) (tclass=[^ ]*) (permissive=[01]).*/\1 \2 \3 \4 \5 \6/' "$f" | sort | uniq -c | sort -rn | cut -c1-230
	echo "   rifiuti (tutti): $(grep -c 'denied' "$f") — legati a remotix: $(grep -c remotix "$f")  ($f)"
	;;
modulo)
	# il modulo SELinux (un .pp compilato a parte) messo al posto di quello del pacchetto, e il
	# servizio riacceso: per provare una regola in secondi, prima di ricostruire il pacchetto
	scp -q $O -P "$PSSH" "${1:?file.pp}" nicfio@localhost:/tmp/remotix.pp || exit 1
	vm "sudo semodule -X 200 -i /tmp/remotix.pp && sudo systemctl restart remotix && sleep 1 && ps -eZ | grep -E ' remotix$' | head -2; sudo semodule -l | grep remotix | tr '\n' ' '; echo"
	;;
ban-via)
	vm "sudo systemctl stop remotix; sudo rm -f /var/lib/remotix/ban; sudo systemctl start remotix; sleep 2; systemctl is-active remotix"
	;;
faillock)
	vm "sudo faillock --user prova; ${1:+sudo faillock --user prova --reset; echo sbloccato; sudo faillock --user prova}" | tee -a "$E/faillock.txt"
	;;
firewall)
	vm "sudo sh -c 'z=\$(firewall-cmd --get-default-zone); echo zona \$z; echo vive: \$(firewall-cmd --zone=\$z --list-services) / \$(firewall-cmd --zone=\$z --list-ports); echo permanenti: \$(firewall-cmd --permanent --zone=\$z --list-services) / \$(firewall-cmd --permanent --zone=\$z --list-ports); firewall-cmd --info-service=remotix 2>&1 | head -3; ls -la --time-style=+%T /etc/firewalld/zones/; for f in /etc/firewalld/zones/*; do sha256sum \$f; done 2>/dev/null; ufw status 2>/dev/null | grep -vE \"^\$\"; ufw show added 2>/dev/null | grep allow'" | tee "$E/firewall-$(t).txt"
	;;
ssh-parola)
	# ssh CON LA PAROLA D'ORDINE (niente chiave), per confrontare con REMOTIX: stessa pila, stesso conto
	# (faillock). SSH_ASKPASS_REQUIRE=force: la parola la da' un programmino, senza terminale.
	a=$(mktemp); printf '#!/bin/sh\necho "%s"\n' "${1:-$PAROLA}" >"$a"; chmod 700 "$a"
	SSH_ASKPASS=$a SSH_ASKPASS_REQUIRE=force DISPLAY=: setsid -w ssh -o BatchMode=no -o PubkeyAuthentication=no \
		-o PreferredAuthentications=password,keyboard-interactive -o NumberOfPasswordPrompts=1 \
		-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -p "$PSSH" prova@localhost 'echo ssh: dentro come $(id -un)' </dev/null 2>&1 | tail -2
	echo "   ssh con la parola: uscita ${PIPESTATUS[0]}"; rm -f "$a"
	;;
disinstalla)
	vm "sudo /root/remotix-install uninstall --purge --output /root/disinstalla.json" >"$E/disinstalla-piano.txt" 2>&1
	vm "sudo /root/remotix-install approve /root/disinstalla.json" >>"$E/disinstalla-piano.txt" 2>&1
	vm "sudo /root/remotix-install apply /root/disinstalla.json" >"$E/disinstalla.txt" 2>&1
	echo "   disinstalla: uscita $? — $(grep -E '^operation ' "$E/disinstalla.txt")"
	grep -E 'FALLITA|BLOCCATA|RX-' "$E/disinstalla.txt" | head -6 | sed 's/^/   /'
	vm "rpm -q remotix remotix-selinux 2>/dev/null; sudo semodule -l 2>/dev/null | grep -c remotix | sed 's/^/moduli remotix: /'; systemctl is-active remotix 2>&1"
	;;
cmd)
	vm "sudo sh -c '$*'" 2>&1 | tee -a "$E/comandi.txt"
	;;
spegni)
	foto=${1:?foto}
	$V ferma "$m" >/dev/null 2>&1; $V torna "$m" "$foto" >/dev/null 2>&1; echo "   $m spenta, tornata a «$foto»"
	;;
*) sed -n 3,24p "$0"; exit 2 ;;
esac
