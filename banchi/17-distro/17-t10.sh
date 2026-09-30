#!/bin/bash
#
# 17-t10.sh — fase 17, T10: il giro INTERO di §7.3 su una macchina della matrice, dall'archivio di
# un rilascio vero (packaging/rilascio.sh), con install.sh come lo userebbe l'amministratore.
#
#   (sul server, come nicfio)   sg kvm -c 'bash 17-t10.sh <macchina> [cliente|iso]'
#     es. bash 17-t10.sh fedora44-kde            (foto «cliente», la macchina <distro>-<desktop>)
#         bash 17-t10.sh debian13-gnome iso      (foto «iso», la macchina <distro>-<desktop>-iso)
#
# Il copione (fasi/17 §7.3), un passo dopo l'altro, e ogni passo con la sua evidenza:
#   0. foto; accensione; la persona «prova» (già nel gruppo del nodo card: R33), la sua chiave ssh;
#   1. impronta «prima» (17-t3-impronta*.sh della famiglia);
#   2. INSTALLA come l'amministratore: install.sh e il suo sha256 dall'archivio, `sha256sum -c`,
#      poi `sh install.sh --archivio … --risposte …` (senza domande: consensi D5 e D6 nel file);
#      ⇒ operazione CONFERMATA (o A CONDIZIONI, dichiarate), `remotix-install certifica`, il
#      servizio in ascolto; librerie viste con l'uid di «prova» (R4);
#   3. un browser VERO (Chrome) entra e vede il desktop (17-t1c-guarda.sh, Full HD, ripiego software);
#   4. RIAVVIO vero della macchina (boot_id), e si rientra col browser (R15);
#   5. AGGIORNA a N+1: l'archivio della macchina passa a quello con N+1 (il collegamento simbolico
#      t10/arch/<macchina>), un browser resta collegato (t8-browser.py) e l'AGGIORNAMENTO DEL
#      SISTEMA (apt-get upgrade · dnf upgrade · zypper up · pacman -Syu) porta REMOTIX a N+1
#      (DECISIONI §10.23, R39); il palco (pid) prima e dopo deve combaciare (R7), il browser rientra
#      e rivede il desktop (R10), la versione è N+1, certifica di nuovo;
#   6. DISINSTALLA (--purge) con una sessione ssh di «prova» che scrive l'ora ogni secondo (R43);
#      impronta «dopo» e confronto con «prima» (R6): si guardano solo le righe che nominano
#      REMOTIX e i gruppi di «prova»;
#   7. spegne e rimette la foto (anche se la prova cade).
# Esito: una riga `T10 <macchina> <stato> PASS|FAIL passi…` in fondo a esiti/<m>/esito.txt e in
# t10/giro.log. Evidenze in /media/REMOTIX/vm17/t10/esiti/<macchina>[-iso]/.
#
# L'archivio: /media/REMOTIX/vm17/t10/archivio-N e archivio-N1 (i due rilasci), serviti da UN
# http.server su 127.0.0.1:8737 dalla cartella t10/arch/, dove <macchina> è un collegamento
# simbolico a uno dei due: dalla VM http://10.0.2.2:8737/<macchina>/ — così ogni macchina vede
# il suo archivio, e il passo 5 lo fa «crescere» da N a N+1 senza toccare le altre.
# ⛔ Al massimo 4 VM accese in tutto; non tocca una macchina già accesa da altri. Ogni macchina ha
#   il SUO labwc per il browser (T1C=t10/t1c/<macchina>): quattro giri insieme non si coprono.
set -uo pipefail
m0=${1:?macchina}; stato=${2:-cliente}
case $stato in cliente) m=$m0; foto=cliente ;; iso) m=$m0-iso; foto=iso ;; *) echo "stato: cliente | iso"; exit 2 ;; esac
R=/media/REMOTIX/vm17
T10=${T10:-$R/t10}
E=$T10/esiti/$m
V="bash $R/17-vm.sh"
PORTA_ARCH=${PORTA_ARCH:-8737}
ARCH=http://10.0.2.2:$PORTA_ARCH/$m
PAROLA=${REMOTIX_PAROLA_PROVA:-prova2026}
IMPRONTA=17-t3-impronta.sh; FAM=debian
case $m0 in
debian13-*) n=1;; ubuntu2604-*) n=2;;
fedora44-*) n=3; IMPRONTA=17-t3-impronta-rpm.sh; FAM=fedora;;
arch-*) n=4; IMPRONTA=17-t3-impronta-arch.sh; FAM=arch;;
tumbleweed-*) n=5; IMPRONTA=17-t3-impronta-rpm.sh; FAM=suse;;
leap16-*) n=6; IMPRONTA=17-t3-impronta-rpm.sh; FAM=suse;;
alma10-*) n=7; IMPRONTA=17-t3-impronta-rpm.sh; FAM=fedora;;
*) echo "macchina sconosciuta: $m0"; exit 2;;
esac
k=0; case ${m0#*-} in gnome) k=1;; kde) k=2;; xfce) k=3;; lxqt) k=4;; esac
[ "$stato" = iso ] && k=5
PSSH=$((2300 + 10 * n + k)); PRX=$((7500 + 10 * n + k))
CH=$R/ssh/id_ed25519
O="-i $CH -o BatchMode=yes -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR"
vm() { $V ssh "$m" "$@"; }
t() { date -u +%H:%M:%S; }
say() { printf '%s %s\n' "$(t)" "$*" | tee -a "$E/giro.log"; }
PASSI=""
esito_passo() { PASSI="$PASSI $1=$2"; say "   ⇒ $1: $2"; }
impronta() { vm 'sudo bash -s' <"$R/t4/$IMPRONTA" >"$E/impronta-$1.txt" 2>"$E/impronta-$1.err"
             say "   impronta «$1»: $(wc -l <"$E/impronta-$1.txt") righe"; }
FINALE=FAIL
fine() {
	[ -n "${OROLOGIO:-}" ] && kill "$OROLOGIO" 2>/dev/null
	[ -n "${BROWSER:-}" ] && kill "$BROWSER" 2>/dev/null
	# il labwc di questa macchina
	[ -f "$T1C/labwc.pid" ] && kill "$(cat "$T1C/labwc.pid")" 2>/dev/null
	say "==> spengo e rimetto la foto «$foto»"
	$V ferma "$m" >/dev/null 2>&1; $V torna "$m" "$foto" >/dev/null 2>&1
	# la macchina torna a vedere l'archivio N (per un giro successivo)
	ln -sfn "$T10/archivio-N" "$T10/arch/$m"
	riga="T10 $m $stato $FINALE$PASSI"
	echo "$riga" | tee -a "$E/esito.txt" >>"$T10/giro.log"
	echo "$riga"
}

rm -rf "$E"; mkdir -p "$E" "$T10/arch" "$T10/t1c"; : >"$E/giro.log"
T1C=$T10/t1c/$m; mkdir -p "$T1C"
if pgrep -f "qemu-system.*-name rx-$m " >/dev/null; then echo "⛔ $m e' gia' accesa: la usa qualcun altro"; exit 2; fi
[ "$(pgrep -c '^qemu-system')" -lt 4 ] || { echo "⛔ gia' 4 VM accese"; exit 2; }
[ -d "$T10/archivio-N" ] && [ -d "$T10/archivio-N1" ] || { echo "⛔ mancano $T10/archivio-N e archivio-N1"; exit 2; }
ln -sfn "$T10/archivio-N" "$T10/arch/$m"
trap fine EXIT

say "==> 0. $m: foto «$foto», accensione (ssh :$PSSH, REMOTIX :$PRX, archivio $ARCH)"
$V torna "$m" "$foto" >/dev/null || exit 1
$V avvia "$m" >"$E/avvia.log" 2>&1 || { tail -5 "$E/avvia.log"; exit 1; }
vm "id -u prova >/dev/null 2>&1 || sudo useradd -m -s /bin/bash prova
echo 'prova:$PAROLA' | sudo chpasswd
G=\$(for x in /dev/dri/card[0-9]*; do [ -e \$x ] && getent group \$(stat -c %g \$x) | cut -d: -f1; done | sort -u | head -1)
[ -n \"\$G\" ] && sudo gpasswd -a prova \"\$G\" >/dev/null
sudo install -d -m 700 -o prova -g prova ~prova/.ssh
sudo install -m 600 -o prova -g prova ~/.ssh/authorized_keys ~prova/.ssh/authorized_keys
. /etc/os-release; echo \"\$PRETTY_NAME · \$(uname -r) · selinux: \$(getenforce 2>/dev/null || echo -)\"
ls -l /dev/dri/ | grep -c card; id prova
curl -s -m 8 -o /dev/null -w 'archivio: HTTP %{http_code}\n' $ARCH/install.sh.sha256 || echo 'archivio: NON raggiungibile'" >"$E/macchina.txt" 2>&1
sed 's/^/   /' "$E/macchina.txt" | tee -a "$E/giro.log"
grep -q 'HTTP 200' "$E/macchina.txt" || { say "⛔ l'archivio non si raggiunge dalla VM"; exit 1; }

say "==> 1. impronta «prima»"
impronta prima
vm "id prova" >"$E/gruppi-prima.txt"

say "==> 2. installa come l'amministratore: install.sh + sha256, --risposte"
vm "printf 'formato = remotix-risposte/1\nlingua = it\nutenti = prova\nconsenso.firewall = si\nconsenso.deposito.epel = si\nconsenso.deposito.openh264 = si\nconsenso.deposito.packman = si\nconsenso.deposito.rpmfusion = si\n' | sudo tee /root/risposte.conf >/dev/null
cd /tmp && rm -f install.sh install.sh.sha256 && curl -sf $ARCH/install.sh -o install.sh && curl -sf $ARCH/install.sh.sha256 -o install.sh.sha256
sha256sum -c install.sh.sha256 && grep -E '^SHA256_MOTORE=' install.sh | cut -c1-40" >"$E/installa.txt" 2>&1
say "   $(grep -E 'install.sh: ' "$E/installa.txt" | head -1)"
T0=$(date +%s)
vm "cd /tmp && sudo sh install.sh --archivio $ARCH --risposte /root/risposte.conf --lingua it" >>"$E/installa.txt" 2>&1
u=$?
OP=$(grep -E '^operazione ' "$E/installa.txt" | tail -1)
say "   install.sh: uscita $u in $(( $(date +%s) - T0 )) s — $OP"
grep -E 'FALLITA|BLOCCATA|RIFIUTATA|RX-|superflue|mancanti|C-' "$E/installa.txt" | head -12 | cut -c1-240 | sed 's/^/   /' | tee -a "$E/giro.log"
vm "echo \"pacchetti: \$( (dpkg-query -W -f='\${Package}=\${Version} ' remotix remotix-install remotix-archive-keyring 2>/dev/null; rpm -q remotix remotix-install remotix-selinux 2>/dev/null; pacman -Q remotix remotix-install 2>/dev/null) | tr '\n' ' ')\"
echo \"servizio: \$(systemctl is-enabled remotix 2>&1) \$(systemctl is-active remotix 2>&1) · pid \$(systemctl show -p MainPID --value remotix) · in ascolto 7447: \$(sudo ss -Htulpn | grep -c ':7447 ')\"
id prova
B=\$(ls /usr/libexec/remotix/remotix /usr/lib/remotix/remotix 2>/dev/null | head -1); echo \"R4 librerie non trovate (uid prova): \$(sudo -u prova ldd \$B 2>&1 | grep -c 'not found') · libav nel binario: \$(ldd \$B | grep -c 'libav\|libswscale')\"
echo --- certifica:; sudo /usr/bin/remotix-install certifica --lingua it 2>&1; echo \"certifica: uscita \$?\"
echo --- registro d avvio:; sudo journalctl -u remotix.service --no-pager -b 2>/dev/null | grep -aE 'codec offerti|OpenH264|pronto|RX-|⛔' | tail -6 | cut -c1-200" >"$E/installato.txt" 2>&1
sed 's/^/   /' "$E/installato.txt" | tee -a "$E/giro.log" >/dev/null
grep -E 'pacchetti:|servizio:|R4 |Certificazione|certifica: uscita|codec offerti' "$E/installato.txt" | cut -c1-200 | sed 's/^/   /' | tee -a "$E/giro.log"
# nella VM non c'è la scheda: la certificazione attesa è A_CONDIZIONI con la sola C-RIPIEGO (R35),
# oppure VERDE; ogni controllo PASS
certifica_va() { grep -q 'Certificazione dell' "$1" && ! grep -qE '^  (FAIL|UNKNOWN) ' "$1" && ! { grep -E '^  C-' "$1" | grep -vq 'C-RIPIEGO'; }; }
if [ $u = 0 ] && echo "$OP" | grep -qE 'CONFERMATA' && certifica_va "$E/installato.txt" && grep -q 'servizio: enabled active' "$E/installato.txt" && grep -q 'in ascolto 7447: [1-9]' "$E/installato.txt" && grep -q 'non trovate (uid prova): 0' "$E/installato.txt"; then
	esito_passo installa PASS
else
	esito_passo installa FAIL; exit 1
fi

say "==> 3. il browser vero (Chrome) su 127.0.0.1:$PRX"
T1C=$T1C T1C_EVIDENZE=$E/browser-1 bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser-1.log" 2>&1
say "   uscita $? — $(grep -E '^T1C ' "$E/browser-1.log" | cut -c1-300)"
if grep -E '^T1C ' "$E/browser-1.log" | grep -q '"esito": *"PASS"'; then esito_passo browser PASS; else esito_passo browser FAIL; vm "sudo journalctl -u remotix --no-pager -b | tail -40" >"$E/journal-browser-1.txt" 2>&1; exit 1; fi

say "==> 4. riavvio vero della macchina (R15), e si rientra"
RX_VM_RIAVVIA_S=${RX_VM_RIAVVIA_S:-600} $V riavvia "$m" >"$E/riavvia.log" 2>&1 || { tail -3 "$E/riavvia.log" | tee -a "$E/giro.log"; esito_passo riavvio FAIL; exit 1; }
vm "echo \"servizio: \$(systemctl is-active remotix 2>&1) · in ascolto 7447: \$(sudo ss -Htulpn | grep -c ':7447 ')\"" | tee -a "$E/giro.log"
T1C=$T1C T1C_EVIDENZE=$E/browser-2 bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser-2.log" 2>&1
say "   uscita $? — $(grep -E '^T1C ' "$E/browser-2.log" | cut -c1-300)"
if grep -E '^T1C ' "$E/browser-2.log" | grep -q '"esito": *"PASS"'; then esito_passo riavvio PASS; else esito_passo riavvio FAIL; vm "sudo journalctl -u remotix --no-pager -b | tail -40" >"$E/journal-browser-2.txt" 2>&1; exit 1; fi

say "==> 5. aggiorna a N+1: l'archivio cresce, un browser resta collegato, l'aggiornamento DEL SISTEMA"
ln -sfn "$T10/archivio-N1" "$T10/arch/$m"
rm -rf "$E/browser-agg"; mkdir -p "$E/browser-agg"
T1C=$T1C T1C_PROGRAMMA=$R/t8/t8-browser.py T1C_EVIDENZE=$E/browser-agg \
	setsid nohup bash "$R/t1c/17-t1c-guarda.sh" "$m" "$PRX" chrome >"$E/browser-agg.log" 2>&1 </dev/null &
BROWSER=$!
for _ in $(seq 1 150); do [ -f "$E/browser-agg/pronto" ] && break; grep -q '^T8 ' "$E/browser-agg.log" && break; sleep 1; done
if [ -f "$E/browser-agg/pronto" ]; then say "   collegato: il desktop si vede"; else say "   ⛔ il browser non si collega: $(tail -2 "$E/browser-agg.log" | cut -c1-200)"; esito_passo aggiorna FAIL; exit 1; fi
palco() { vm "for p in gnome-shell kwin_wayland plasmashell labwc xfce4-session lxqt-session; do for x in \$(pgrep -u prova -x \$p); do echo \"\$p \$x\"; done; done | sort"; }
palco >"$E/palco-prima.txt"
say "   palco prima: $(tr '\n' ' ' <"$E/palco-prima.txt")"
case $FAM in
debian) AGG="sudo apt-get update -q && sudo DEBIAN_FRONTEND=noninteractive apt-get upgrade -y -q" ;;
fedora) AGG="sudo dnf upgrade -y --refresh" ;;
suse)   AGG="sudo zypper --non-interactive refresh && sudo zypper --non-interactive up" ;;
arch)   AGG="sudo pacman -Syu --noconfirm" ;;
esac
T0=$(date +%s)
vm "$AGG; echo \"aggiornamento: uscita \$?\"
echo --- remotix.service dal journal:
sudo journalctl -u remotix.service --since @$T0 --no-pager -o short-unix 2>/dev/null | grep -aE 'RITROVAT|pronto|Stopp|Start|Reload|RX-' | tail -12 | cut -c1-200" >"$E/aggiorna.txt" 2>&1
say "   aggiornamento del sistema in $(( $(date +%s) - T0 )) s: $(grep -E 'aggiornamento: uscita' "$E/aggiorna.txt")"
grep -aE 'remotix|RITROVAT' "$E/aggiorna.txt" | tail -8 | cut -c1-200 | sed 's/^/   /' | tee -a "$E/giro.log"
palco >"$E/palco-dopo.txt"
say "   palco dopo:  $(tr '\n' ' ' <"$E/palco-dopo.txt")"
touch "$E/browser-agg/via"
for _ in $(seq 1 300); do grep -q '^T8 ' "$E/browser-agg.log" && break; sleep 1; done
BROWSER=
say "   $(grep '^T8 ' "$E/browser-agg.log" | cut -c1-400)"
vm "echo \"pacchetti: \$( (dpkg-query -W -f='\${Package}=\${Version} ' remotix remotix-install 2>/dev/null; rpm -q remotix remotix-install 2>/dev/null; pacman -Q remotix remotix-install 2>/dev/null) | tr '\n' ' ')\"
echo \"servizio: \$(systemctl is-active remotix 2>&1) · pid \$(systemctl show -p MainPID --value remotix)\"
sudo /usr/bin/remotix-install versione; sudo /usr/bin/remotix-install stato --lingua it 2>&1 | head -12
sudo sh -c '/usr/bin/remotix-install certifica --lingua it >/tmp/c.txt 2>&1'; echo \"certifica: uscita \$?\"; sudo cat /tmp/c.txt" >"$E/aggiornato.txt" 2>&1
grep -E 'pacchetti:|servizio:|Certificazione|certifica: uscita' "$E/aggiornato.txt" | cut -c1-200 | sed 's/^/   /' | tee -a "$E/giro.log"
if grep -q 'aggiornamento: uscita 0' "$E/aggiorna.txt" && grep -E '^T8 ' "$E/browser-agg.log" | grep -q '"esito": *"PASS"' && cmp -s "$E/palco-prima.txt" "$E/palco-dopo.txt" && [ -s "$E/palco-prima.txt" ] && grep -q "pacchetti:.*${VERSIONE_N1:-NON_DATA}" "$E/aggiornato.txt" && certifica_va "$E/aggiornato.txt"; then
	esito_passo aggiorna PASS
else
	esito_passo aggiorna FAIL
	AGG_FAIL=1
fi

say "==> 6. disinstalla --purge, con una sessione ssh di «prova» che scrive l'ora (R43)"
# shellcheck disable=SC2086
ssh $O -p "$PSSH" prova@localhost 'while :; do date +%s >> ~/orologio.txt; sleep 1; done' &
OROLOGIO=$!
sleep 4
vm "loginctl list-sessions --no-legend" >"$E/sessioni-prima.txt" 2>&1
T0=$(date +%s)
vm "sudo sh -c '/usr/bin/remotix-install disinstalla --purge --uscita /root/d.json --lingua it >/tmp/d.txt 2>&1' && sudo /usr/bin/remotix-install applica /root/d.json --approva --lingua it" >"$E/disinstalla.txt" 2>&1
u=$?
OPD=$(grep -E '^operazione ' "$E/disinstalla.txt" | tail -1)
say "   disinstalla: uscita $u in $(( $(date +%s) - T0 )) s — $OPD"
grep -E 'FALLITA|BLOCCATA|RX-' "$E/disinstalla.txt" | head -6 | cut -c1-240 | sed 's/^/   /' | tee -a "$E/giro.log"
sleep 3
vm "a=\$(sudo tail -1 ~prova/orologio.txt); sleep 3; b=\$(sudo tail -1 ~prova/orologio.txt); echo \"R43 orologio ssh: \$a → \$b\"
echo \"sessioni: \$(loginctl list-sessions --no-legend | grep -c prova) di prova · desktop di prova: \$(pgrep -u prova -c -x 'gnome-shell|kwin_wayland|labwc|plasmashell|lxqt-panel|xfce4-panel')\"
echo \"pacchetti rimasti: \$( (dpkg-query -W -f='\${Package} ' 'remotix*' 2>/dev/null; rpm -qa 'remotix*' 2>/dev/null; pacman -Qq 2>/dev/null | grep remotix) | tr '\n' ' ')\"
echo \"servizio: \$(systemctl is-active remotix 2>&1) · in ascolto 7447: \$(sudo ss -Htulpn | grep -c ':7447 ') · /var/lib/remotix: \$(sudo ls -A /var/lib/remotix 2>&1 | tr '\n' ' ')\"
echo \"archivi: \$(ls /etc/apt/sources.list.d /etc/yum.repos.d /etc/zypp/repos.d 2>/dev/null | grep -ci remotix) · pacman.conf: \$(grep -c remotix /etc/pacman.conf 2>/dev/null)\"
id prova" >"$E/dopo.txt" 2>&1
sed 's/^/   /' "$E/dopo.txt" | tee -a "$E/giro.log"
kill "$OROLOGIO" 2>/dev/null; OROLOGIO=
vm "sudo rm -f ~prova/orologio.txt"
impronta dopo
diff "$E/impronta-prima.txt" "$E/impronta-dopo.txt" >"$E/diff-R6.txt"
# R6: le righe DIRETTE di REMOTIX rimaste; i gruppi di «prova» come prima (R33); il resto (cache,
# ore delle cartelle, copie di gpasswd) si legge nel diff e si dichiara.
# ⛔ Escluso `/var/lib/remotix` (la STORIA del motore: la cartella `piani`/`operazioni` dell'operazione
#    di disinstallazione IN CORSO non si può togliere mentre gira — residuo DIRETTO atteso, come in T5,
#    §13.1 riga 56c93d3; `--purge` toglie il resto). Un residuo remotix FUORI di lì è un vero rosso.
#    Escluso anche `~/.local/state/remotix/sessione.log` (il registro della sessione dell'utente:
#    DIRETTA, ma la sua rimozione è una DECISIONE APERTA dell'utente, §13.1 ⚠ punto 2 di 165906c).
grep -E '^[<>]' "$E/diff-R6.txt" | grep -i 'remotix' | grep -vE 'journal|/var/cache|/var/log|/var/lib/remotix|state/remotix' >"$E/diff-R6-remotix.txt"
# i residui DOCUMENTATI (storia del motore, registro di sessione): si dichiarano, non fanno rosso
grep -E '^[<>]' "$E/diff-R6.txt" | grep -iE '/var/lib/remotix|state/remotix' >"$E/diff-R6-attesi.txt" || true
G1=$(sed 's/.*groups=//' "$E/gruppi-prima.txt"); G2=$(grep '^uid=' "$E/dopo.txt" | sed 's/.*groups=//')
say "   R6: $(grep -c '^[<>]' "$E/diff-R6.txt") righe diverse, di cui $(wc -l <"$E/diff-R6-remotix.txt") residui remotix NON attesi, $(wc -l <"$E/diff-R6-attesi.txt") attesi (storia/sessione); gruppi di prova prima «$G1» dopo «$G2»"
a=$(grep 'R43 orologio' "$E/dopo.txt" | sed 's/.*: //'); a1=${a%% →*}; a2=${a##*→ }
if [ $u = 0 ] && echo "$OPD" | grep -q 'CONFERMATA' && [ -z "$(grep 'pacchetti rimasti:' "$E/dopo.txt" | cut -d: -f2 | tr -d ' ')" ] && [ "$a1" != "$a2" ] && grep -q 'desktop di prova: 0' "$E/dopo.txt" && [ "$G1" = "$G2" ] && [ ! -s "$E/diff-R6-remotix.txt" ]; then
	esito_passo disinstalla PASS
else
	esito_passo disinstalla FAIL
	DIS_FAIL=1
fi
[ -z "${AGG_FAIL:-}${DIS_FAIL:-}" ] && FINALE=PASS
exit 0
