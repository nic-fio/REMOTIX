#!/bin/bash
# ===========================================================================
# 10-b9d-corri-al-lucchetto — ⛔⛔ LA CORSA AL LUCCHETTO SI CORRE **SULLA
# MACCHINA**, non da qui.
# ===========================================================================
#
# ⛔ PERCHE' ESISTE, e la ragione e' misurata, non temuta.
#
#   `banchi/09-lucchetto.py prendi()` ritenta il `mkdir` ogni **5 secondi**, e
#   ogni tentativo e' un giro di `ssh`.  ⚠ Ma il lucchetto NON E' UNA CODA: e'
#   una CORSA — nessuna prenotazione, nessuna anzianita', vince chi arriva per
#   primo dopo un `molla`.  ⇒ Chi ritenta piu' fitto vince quasi sempre.
#
#   `[M]` 24-25 agosto 2026, questo incarico: con 5 secondi ho perso **cinque
#   passaggi di mano di fila**, 982 giri d'attesa in un turno solo (~82 minuti)
#   senza mai toccare la GPU.  Un altro incarico ha perso allo stesso modo una
#   finestra da 45 minuti.  ⚠ E non e' sfortuna: altri pilota ritentano ogni
#   secondo, e la finestra fra un `rmdir` e il `mkdir` successivo dura quanto il
#   passo del piu' fitto.
#
# ⭐ E IL CICLO STA QUI, sulla macchina di prova, invece che nel pilota: un
#    tentativo via `ssh` costa 100-200 ms di rete e apre una connessione a ogni
#    giro.  Ritentare da fuori ogni mezzo secondo vorrebbe dire duemila
#    connessioni all'ora **e** una finestra vera piu' larga del passo che
#    dichiara.  Qui il passo e' quello scritto, e la connessione e' UNA.
#
# ⛔ NON si tocca `banchi/09-lucchetto.py`: e' di tutti, e cambiargli il passo
#    sotto i piedi cambierebbe il comportamento di ogni altro banco.  Questo
#    file fa **la stessa cosa** — `mkdir` atomico, e dentro un file `chi` con
#    «<scadenza epoch> <nome>» — con lo stesso formato, letto e scritto uguale.
#    ⚠ Se un giorno quel formato cambia, cambia anche qui, o i due si mentono.
#
# ⭐ E LE TRE COSE CHE `prendi()` FA E CHE QUI NON SI PERDONO:
#    · lo SCASSINO di un lucchetto scaduto, **dichiarato** invece che silenzioso;
#    · il rifiuto quando l'attesa finisce, invece di misurare senza;
#    · e in piu' — ⛔ il caso che a `prendi()` manca — «il lucchetto e' GIA' A
#      NOME MIO»: li' `prendi()` aspetta se stesso fino alla scadenza, e questo
#      esce **10** perche' il pilota decida se adottarlo.
#
# uso (da root, sulla macchina):
#   10-b9d-corri-al-lucchetto.sh <POSTO> <CHI> <SECONDI> <ATTESA> [PASSO]
#
# esce 0  PRESO      · 3  SCADUTA (l'attesa e' finita, non ho il lucchetto)
#      10 MIO        · il lucchetto porta gia' il mio nome: decida il pilota
#      2  argomenti sbagliati
# ===========================================================================
set -u

POSTO=${1:?serve la cartella del lucchetto}
CHI=${2:?serve il nome}
SECONDI=${3:?servono i secondi di possesso}
ATTESA=${4:?servono i secondi di attesa}
PASSO=${5:-0.5}

fine=$(( $(date +%s) + ATTESA ))
giri=0

while :; do
	# ⭐ L'ATTO ATOMICO, identico a quello di `09-lucchetto.py`: `mkdir` senza
	#    `-p`.  O riesce (e sono io) o fallisce (e non sono io).  ⚠ Un file
	#    scritto con `>` riesce sempre, anche a due mani, e non e' un lucchetto.
	if mkdir "$POSTO" 2>/dev/null; then
		printf '%s %s\n' "$(( $(date +%s) + SECONDI ))" "$CHI" > "$POSTO/chi"
		printf 'PRESO dopo %d giri da %s s\n' "$giri" "$PASSO"
		exit 0
	fi
	giri=$(( giri + 1 ))

	riga=$(cat "$POSTO/chi" 2>/dev/null)
	scad=${riga%% *}
	altro=${riga#* }
	adesso=$(date +%s)

	# ⛔ Il mio stesso nome: NON lo scassino e non aspetto me stesso — lo dico
	#    al pilota, che sa se un suo processo e' ancora vivo.
	if [ -n "$riga" ] && [ "$altro" = "$CHI" ]; then
		printf 'MIO %s\n' "$riga"
		exit 10
	fi

	# ⛔ Scaduto: si scassina, ma si DICHIARA chi e' stato scassinato.
	#    ⚠ Scassinare in silenzio sarebbe peggio del blocco.
	if [ -n "$scad" ] && [ "$scad" -eq "$scad" ] 2>/dev/null \
	   && [ "$adesso" -gt "$scad" ]; then
		printf 'SCASSINO «%s», scaduto da %d s\n' "$altro" "$(( adesso - scad ))"
		rm -rf "$POSTO"
		continue
	fi

	if [ "$adesso" -ge "$fine" ]; then
		printf 'SCADUTA: e di «%s» e la mia attesa di %d s e finita dopo %d giri\n' \
			"$altro" "$ATTESA" "$giri"
		exit 3
	fi
	sleep "$PASSO"
done
