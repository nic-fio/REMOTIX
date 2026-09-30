#!/bin/bash
#
# t6-giro.sh — fase 17, T6: il giro intero su UNA macchina, dalla foto alla foto.
#
#   (sul server, come nicfio)   sg kvm -c 'bash t6-giro.sh <macchina> <foto> <bersaglio> "<opzioni del piano>" [faillock-accendi] [faillock-spegni]'
#   es.  bash t6-giro.sh alma10-gnome-iso iso alma10 "--apri-firewall --deposito epel,rpmfusion" \
#            "authselect enable-feature with-faillock" "authselect disable-feature with-faillock"
#
#   0. (PRIMA="<comando>" nell'ambiente: un comando da root appena accesa, es. ufw acceso)
#   1. accensione dalla foto; il firewall PRIMA (zona, regole, file in /etc/firewalld/zones e sha256)
#   2. il motore installa i pacchetti di pacchetti/<bersaglio> (una transazione: remotix e, dove c'è,
#      remotix-selinux) col piano dato; il firewall DOPO
#   3. R19/R20: Chrome entra (sessione nuova), rientra (ripresa), il servizio riacceso a desktop vivo e
#      si rientra, parola sbagliata, root; le sessioni logind (Class, Remote) e i contesti; i rifiuti
#      SELinux dall'inizio del punto 3
#   4. R20 faillock (se dato il comando che lo accende): tre errori da REMOTIX ⇒ il conto chiuso anche
#      per ssh; `faillock --reset` ⇒ si rientra da tutti e due
#   5. disinstalla --purge; il firewall DOPO LA DISINSTALLAZIONE; i rifiuti di tutto il giro
#   6. spegne e torna alla foto
# Evidenze in /media/REMOTIX/vm17/t6/esiti/<macchina>/ (giro.txt è il riassunto).
set -uo pipefail
m=${1:?macchina}; foto=${2:?foto}; b=${3:?bersaglio}; opz=${4:-}; fl_on=${5:-}; fl_off=${6:-}
T6=/media/REMOTIX/vm17/t6
E=$T6/esiti/$m
P=$T6/pacchetti/$b
r() { bash "$T6/t6-vm.sh" "$m" "$@" 2>&1 | grep -v tput; }
fine() { r spegni "$foto"; }

r accendi "$foto" || exit 1
trap fine EXIT
exec > >(tee "$E/giro.txt") 2>&1
echo "== $m ($foto), pacchetti di $b: $(ls "$P" | tr '\n' ' ')"
[ -n "${PRIMA:-}" ] && { echo "== 0. prima: $PRIMA"; r cmd "$PRIMA"; }
echo "== 1. il firewall prima"; r firewall | grep -vE '^(totale|d[rwx-]{9})'
echo "== 2. installa"
f=(); for x in "$P"/*; do case $x in *debug*) ;; *) f+=("$x");; esac; done
r motore "${f[@]}" >/dev/null
r installa "$opz"
echo "== il firewall dopo l'installazione"; r firewall | grep -vE '^(totale|d[rwx-]{9})'
INIZIO=$(r cmd "date +%T" | tail -1)
echo "== 3. R19/R20 (ora della VM: $INIZIO)"
r entra prova "" prima | grep -v giornale
r entra prova "" seconda | grep -v giornale
r cmd "systemctl restart remotix; sleep 3; systemctl is-active remotix"
r entra prova "" dopo-riavvio | grep -v giornale
r entra prova sbagliata sbagliata
r ban-via >/dev/null
r entra root "" root
r ban-via >/dev/null
r sessione
r avc "$INIZIO"
if [ -n "$fl_on" ]; then
	echo "== 4. R20 faillock: $fl_on"
	r cmd "$fl_on"
	r faillock reset >/dev/null
	for i in 1 2 3; do r entra prova sbagliata sbagliata$i | grep -v giornale; r ban-via >/dev/null; done
	r faillock
	echo "-- la parola GIUSTA, da REMOTIX e da ssh:"
	r entra prova "" chiuso
	r ssh-parola
	r ban-via >/dev/null
	echo "-- faillock --reset, e di nuovo:"
	r faillock reset | tail -2
	r entra prova "" sbloccato | grep -v giornale
	r ssh-parola
	[ -n "$fl_off" ] && r cmd "$fl_off"
fi
echo "== 5. disinstalla"
r disinstalla
echo "== il firewall dopo la disinstallazione"; r firewall | grep -vE '^(totale|d[rwx-]{9})'
echo "== i rifiuti SELinux di tutto il giro"
r avc "$INIZIO"
