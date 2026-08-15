#!/bin/bash
#
# 05-b1-certifica.sh — ⛔ IL BANCO SI CERTIFICA PRIMA DI ESSERE CREDUTO.
#
#   sudo bash 05-b1-certifica.sh
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE'
#
# `fasi/README.md` regola 4: *«il banco si certifica prima di essere creduto»*.
# Un banco verde puo' esserlo per due ragioni opposte — perche' il codice e'
# giusto, o perche' il banco non guarda.  ⇒ Si rompe il codice **di proposito**,
# in un punto noto, e si pretende che il banco diventi rosso **in quel caso li'**
# e non in un altro.
#
# ⭐ E il controllo e' su QUALE caso e' rosso, non su «e' rosso»: e' la forma di
#    `banchi/04-b31-certifica.sh`, che il mandato della fase 5 indica come
#    modello.
#
# ---------------------------------------------------------------------------
# I GUASTI INNESTATI, e il caso che ciascuno deve far cadere
#
#   | guasto                                  | caso atteso rosso |
#   |-----------------------------------------|-------------------|
#   | 1. il SEAT non si guarda piu'            | 2 4 5 6 (la NOSTRA conta come locale, in ogni scena in cui e' viva) |
#   | 2. l'UTENTE non si guarda piu'           | 5 6    (la locale di un altro conta, e resta viva anche al 6) |
#   | 3. il TIPO grafico non si guarda piu'    | 6      (la consolle di TESTO conta)  |
#
# ⭐⭐ E DUE DI QUESTE TRE RIGHE LE HA SCRITTE LA CERTIFICAZIONE, non chi ha
#     scritto il banco — 15 agosto 2026:
#
#   · il guasto 1 doveva far cadere «il caso 2», e fa cadere **2, 4, 5 e 6**:
#     giusto cosi', perche' la sessione «come la nostra» resta viva per tutto il
#     banco.  ⇒ L'attesa era piu' stretta della verita';
#   · il guasto 3 non faceva cadere **NIENTE**, ⇒ ⛔ nessun caso esercitava il
#     controllo sul tipo grafico.  Il caso 6 e' nato da li'.
#
# ⚠ Il guasto 1 e' il piu' importante: e' esattamente il difetto che il prodotto
#   avrebbe avuto scrivendo il criterio «ovvio» su `Remote` invece che sul seat.
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
SORGENTE="$QUI/../src/sentinella.c"
SALVA="/tmp/05-b1-sentinella.c.originale"
ENTRA=/media/REMOTIX/enter.sh
BINARIO="$QUI/05-b1-sentinella"
UTENTE=${1:-prova}
ALTRO=${2:-prova2}

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

[ "$(id -u)" -eq 0 ] || { echo "⛔ vuole root: crea sessioni logind"; exit 2; }

costruisci()
{
	bash "$ENTRA" --root "cd /srv/src/04-vero-src/banchi && cc -O2 -g -std=gnu11 \
	    -Wall -Wextra \$(pkg-config --cflags gio-2.0) -o 05-b1-sentinella \
	    05-b1-sentinella.c ../src/sentinella.c ../src/registro.c \
	    \$(pkg-config --libs gio-2.0) -lpam" >/dev/null 2>&1
}

# Restituisce l'elenco dei casi rossi, separati da spazi.
gira()
{
	local unita="cert-$RANDOM"
	systemd-run --quiet --wait --collect --unit="$unita" \
	    --property=StandardOutput=journal "$BINARIO" "$UTENTE" "$ALTRO" >/dev/null 2>&1
	journalctl -u "$unita" --no-pager -o cat 2>/dev/null \
	    | awk '/^caso /{n=$2; sub(/[^0-9]/,"",n)} /⛔ ROSSO/{printf "%s ", n}'
}

cp "$SORGENTE" "$SALVA"
ripristina() { cp "$SALVA" "$SORGENTE"; costruisci; }
trap ripristina EXIT

echo "== controllo positivo: il banco sano deve essere VERDE =="
costruisci
ROSSI=$(gira)
if [ -z "$ROSSI" ]; then
	ok "nessun caso rosso col codice sano"
else
	ko "⛔ il codice sano da' rossi ($ROSSI): la certificazione non puo' cominciare"
	exit 1
fi

esito=0
innesta() # $1 numero  $2 descrizione  $3 sed-espressione  $4 caso atteso rosso
{
	echo
	echo "== guasto $1: $2 =="
	cp "$SALVA" "$SORGENTE"
	sed -i "$3" "$SORGENTE"
	if ! grep -q 'GUASTO-INNESTATO' "$SORGENTE"; then
		ko "⛔ il guasto NON e' entrato nel sorgente: sed non ha morso"
		esito=1
		return
	fi
	costruisci
	local rossi
	rossi=$(gira)
	inf "casi rossi: ${rossi:-nessuno}"
	if [ "$(echo $rossi)" = "$4" ]; then
		ok "rosso esattamente il caso $4, come atteso"
	else
		ko "⛔ atteso rosso il caso $4, avuti «${rossi:-nessuno}»"
		esito=1
	fi
}

# ⚠ Ogni guasto si innesta su UNA riga, riconosciuta per intero: `sed` non
#   prende i ritorni a capo, e un'espressione che morde a meta' produrrebbe un
#   sorgente che non compila — cioe' un rosso che non e' quello cercato.
innesta 1 "il SEAT non si guarda piu'" \
	's@^\t\tif (!seat || !\*seat)$@\t\tif (0) /* GUASTO-INNESTATO */@' "2 4 5 6"

innesta 2 "l'UTENTE non si guarda piu'" \
	's@^\t\tif (g_strcmp0(nome, utente) != 0)$@\t\tif (0) /* GUASTO-INNESTATO */@' "5 6"

innesta 3 "il TIPO grafico non si guarda piu'" \
	's@^\tif (!grafica)$@\tif (0) /* GUASTO-INNESTATO */@' 6

echo
if [ "$esito" -eq 0 ]; then
	echo "⭐ CERTIFICATO: ogni guasto fa cadere il caso che deve cadere."
else
	echo "⛔ NON certificato: leggi sopra."
fi
exit "$esito"
