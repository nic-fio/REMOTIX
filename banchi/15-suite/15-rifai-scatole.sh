#!/bin/bash
# 15-rifai-scatole.sh — rifà DA ZERO le scatole rete11-* prima di un giro della suite.
#
#   (sul server, come nicfio)  bash 15-rifai-scatole.sh [gnome kde xfce lxqt]
#
# ⛔ Distrugge e ricrea i contenitori: ogni sessione aperta dentro (anche `nictest`
#    dell'utente) muore.  Si lancia solo col via dell'utente (fasi/15 «Come si
#    esegue»; permesso dato il 25 set 2026, regola in .claude/settings.local.json).
# Per ogni desktop, una scatola alla volta (il lucchetto della scheda):
#   accendi  = contenitore NUOVO dall'immagine
#   prodotto = binario e pagina di /media/REMOTIX/rete11/prodotto
#   server   = il server del prodotto sulla sua porta
set -u
DESKTOP=${*:-gnome kde xfce lxqt}
cd /media/REMOTIX/rete11 || exit 2
esito=0
for d in $DESKTOP; do
	echo "=== $d $(date +%T)"
	for passo in accendi prodotto server; do
		if ! printf 'nicfio\n' | sudo -S -p '' bash 11-accendi.sh "$passo" "$d" >"/tmp/rifai-$d-$passo.log" 2>&1; then
			echo "⛔ $d $passo non riuscito: $(tail -2 "/tmp/rifai-$d-$passo.log" | tr '\n' ' ')"
			esito=1
		else
			echo "   $passo: $(grep -a -E '⭐|✅|ok|ascolta' "/tmp/rifai-$d-$passo.log" | tail -1)"
		fi
	done
done
echo "FINE $(date +%T) · binario $(md5sum prodotto/remotix | cut -c1-8) · pagina $(md5sum prodotto/pagina.html | cut -c1-8)"
exit $esito
