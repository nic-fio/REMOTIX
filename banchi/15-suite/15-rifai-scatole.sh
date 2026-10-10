#!/bin/bash
# 15-rifai-scatole.sh — rebuilds FROM SCRATCH the rete11-* boxes before a round of the suite.
#
#   (on the server, as nicfio)  bash 15-rifai-scatole.sh [gnome kde xfce lxqt]
#
# ⛔ It destroys and recreates the containers: every session open inside (even the user's
#    `nictest`) dies.  It is launched only with the user's go-ahead (fasi/15 «How it is
#    run»; permission given on 25 Sep 2026, rule in .claude/settings.local.json).
# For each desktop, one box at a time (the card's padlock):
#   accendi  = NEW container from the image
#   prodotto = binary and page from /media/REMOTIX/rete11/prodotto
#   server   = the product's server on its port
set -u
DESKTOP=${*:-gnome kde xfce lxqt}
cd /media/REMOTIX/rete11 || exit 2
esito=0
for d in $DESKTOP; do
	echo "=== $d $(date +%T)"
	for passo in accendi prodotto server; do
		if ! printf '%s\n' "${REMOTIX_PAROLA_SUDO:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' bash 11-accendi.sh "$passo" "$d" >"/tmp/rifai-$d-$passo.log" 2>&1; then
			echo "⛔ $d $passo failed: $(tail -2 "/tmp/rifai-$d-$passo.log" | tr '\n' ' ')"
			esito=1
		else
			echo "   $passo: $(grep -a -E '⭐|✅|ok|listens' "/tmp/rifai-$d-$passo.log" | tail -1)"
		fi
	done
done
echo "END $(date +%T) · binary $(md5sum prodotto/remotix | cut -c1-8) · page $(md5sum prodotto/pagina.html | cut -c1-8)"
exit $esito
