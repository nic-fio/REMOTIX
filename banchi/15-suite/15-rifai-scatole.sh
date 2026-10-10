#!/bin/bash
# 15-rifai-scatole.sh — rebuilds FROM SCRATCH the rete11-* boxes before a round of the suite.
#
#   (on the server, as nicfio)  bash 15-rifai-scatole.sh [gnome kde xfce lxqt]
#
# ⛔ It destroys and recreates the containers: every session open inside (even the user's
#    `nictest`) dies.  It is launched only with the user's go-ahead (fasi/15 «How it is
#    run»; permission given on 25 Sep 2026, rule in .claude/settings.local.json).
# For each desktop, one box at a time (the card's padlock):
#   turn_on  = NEW container from the image
#   product = binary and page from /media/REMOTIX/rete11/prodotto
#   server   = the product's server on its port
set -u
DESKTOP=${*:-gnome kde xfce lxqt}
cd /media/REMOTIX/rete11 || exit 2
outcome=0
for d in $DESKTOP; do
	echo "=== $d $(date +%T)"
	for step in turn_on prodotto server; do
		if ! printf '%s\n' "${REMOTIX_SUDO_PASSWORD:-$(awk '/^pass:/{print $2; exit}' "$HOME/SERVER.ssh" 2>/dev/null)}" | sudo -S -p '' bash 11-accendi.sh "$step" "$d" >"/tmp/redo-$d-$step.log" 2>&1; then
			echo "⛔ $d $step failed: $(tail -2 "/tmp/redo-$d-$step.log" | tr '\n' ' ')"
			outcome=1
		else
			echo "   $step: $(grep -a -E '⭐|✅|ok|listens' "/tmp/redo-$d-$step.log" | tail -1)"
		fi
	done
done
echo "END $(date +%T) · binary $(md5sum prodotto/remotix | cut -c1-8) · page $(md5sum prodotto/pagina.html | cut -c1-8)"
exit $outcome
