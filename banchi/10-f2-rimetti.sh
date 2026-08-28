#!/bin/bash
# ===========================================================================
# 10-f2-rimetti.sh — ⛔ LA MACCHINA SI LASCIA COME LA SI E' TROVATA, e lo si
# VERIFICA invece di dichiararlo a memoria.
#
# ⚠ Tocca SOLO quel che e' di F2: la porta 8420, l'unita' `remotix-8420`, gli
#   utenti `provanic2` e `provanic3`, il lucchetto a nome `10-f2`.
#   ⛔ `provanic1` e' di F1 e non si tocca; la 8400 e' del coordinamento.
#
# ⭐ E la cura di `~/.cache` NON si disfa: e' quella che fa funzionare il
#    browser, ed e' quel che `src/provisiona.sh` adesso mette da se'.
# ===========================================================================
set -uo pipefail

echo "== spengo quel che e' mio =="
pkill -9 -u provanic2 -f 'firefox-es[r]' 2>/dev/null
pkill -9 -u provanic3 -f 'firefox-es[r]' 2>/dev/null
pkill -9 -u provanic2 -f 'gnome-termina[l]' 2>/dev/null
pkill -f '10-b9d-corri-al-lucchett[o]' 2>/dev/null
systemctl stop remotix-8420.service 2>/dev/null
systemctl reset-failed remotix-8420.service 2>/dev/null
loginctl terminate-user provanic2 2>/dev/null
loginctl terminate-user provanic3 2>/dev/null

# ⭐ Il lucchetto si molla SOLO se porta il mio nome: scassinare quello di un
#    altro e' il modo piu' rapido di falsare la misura di qualcun altro.
L=/media/REMOTIX/tmp/.lucchetto-gpu.d
if [ -f "$L/chi" ] && grep -q ' 10-f2$' "$L/chi"; then
	rm -f "$L/chi"; rmdir "$L" 2>/dev/null
	echo "   ⭐ lucchetto mollato (era mio)"
else
	echo "   -- lucchetto: $(cat "$L/chi" 2>/dev/null || echo libero) — non lo tocco"
fi

sleep 3
echo
echo "== la verifica, guardando e non ricordando =="
echo "porte 7xxx/8xxx in ascolto:"
ss -uln 2>/dev/null | grep -E ':(7|8)[0-9]{3} ' | sed 's/^/   /' || echo "   (nessuna)"
echo "processi remotix:"
pgrep -a remotix | cut -c1-110 | sed 's/^/   /' || echo "   (nessuno)"
echo "netem su lo e enp7s0:"
tc qdisc show dev lo 2>/dev/null | sed 's/^/   lo: /'
tc qdisc show dev enp7s0 2>/dev/null | sed 's/^/   enp7s0: /'
echo "i miei utenti:"
for u in provanic2 provanic3; do
	echo "   $u: $(pgrep -u "$u" -c . 2>/dev/null || echo 0) processi · .cache = $(readlink "/home/$u/.cache" 2>/dev/null || echo 'cartella vera')"
done
