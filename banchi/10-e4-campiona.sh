#!/usr/bin/env bash
# 10-e4-campiona — ⭐ IL COSTO DEL REGISTRO, campionato ACCANTO alla salita.
#
# ⛔ Perche' esiste: C4 allunga OGNI riga del registro, e `[M]` §5.2 lo ha
#    misurato a QUATTRO sessioni (+5,4 % di byte, righe/s invariate).  A undici
#    quel costo si moltiplica, e la domanda 3 dell'incarico E4 e' se il ritmo o
#    il ritardo ne risentano.
#
# ⭐ E NON SERVE NESSUN PONTE FRA OROLOGI: ogni campione porta accanto **quanti
#    clienti MIEI sono vivi**, cioe' a che gradino sta la salita.
#
# ⛔ E i modelli sono spezzati da una classe di caratteri: senza, `pgrep -f`
#    combacia con la PROPRIA riga di comando e conta sempre uno in piu' (§7.3).
# ⛔ E `pgrep -c` STAMPA «0» **e** esce 1: un `|| echo 0` in coda ne stampa DUE.
#    ⚠ Il primo giro e' morto proprio li', in silenzio.
#
# uso (DA ROOT, sulla macchina): 10-e4-campiona.sh <registro> <fuori> <passo_s>
set -u
REG=${1:?serve il registro}
FUORI=${2:?serve il file di uscita}
PASSO=${3:-5}
printf 'epoch\tore\tbyte\tclienti\tpalchi\n' > "$FUORI"
while :; do
	b=$(stat -c %s "$REG" 2>/dev/null); b=${b:--1}
	c=$(pgrep -c -f -- '--giornale .*10e[4]/giornale' 2>/dev/null); c=${c:-0}
	# ⛔ SOLO i miei uid: un modello globale conterebbe i palchi di un altro.
	p=0
	for u in 1110 1111 1112 1113 1114 1115 1116 1117 1118 1119 1120; do
		n=$(pgrep -u "$u" -c -x gnome-shell 2>/dev/null); n=${n:-0}
		p=$(( p + n ))
	done
	printf '%s\t%s\t%s\t%s\t%s\n' "$(date +%s)" "$(date +%H:%M:%S)" "$b" "$c" "$p" >> "$FUORI"
	sleep "$PASSO"
done
