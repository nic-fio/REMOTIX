#!/bin/bash
#
# 06-b33-risveglio-certifica.sh — ⛔⛔ IL CONTROLLO POSITIVO del banco di §7.1.
#
#   ⚠ GIRA SUL SERVER (192.168.0.2), come utente `nicfio`, NON da root.
#
#   bash 06-b33-risveglio-certifica.sh <file-parola-sudo> [RG1 RG2 RG3 RG4 RG5]
#
# ===========================================================================
# ⛔ CHE COSA CERTIFICA, E PERCHE' NON CONFRONTA I ROSSI
# ===========================================================================
#
# `06-b33-certifica.sh` confronta l'insieme dei casi **rossi**.  ⛔ Qui non si
# puo': gli attesi di questo banco hanno **tre colori**, e i due casi che
# contano — T3 e T4 — col difetto vivo non diventano rossi, diventano
# `DIFETTO_VIVO`, che e' il colore giusto per un difetto misurato.  ⇒ Un
# confronto sui rossi non li vedrebbe cambiare, e ogni guasto passerebbe.
#
# ⇒ Si confronta **la mappa dei verdetti** — caso per caso, colore per colore —
#   fra il giro sano e il giro guasto, e si pretende che siano cambiati
#   **esattamente** i casi dichiarati in `06-b33-risveglio-guasti.py`.
#
# ⭐ E' piu' forte del confronto sui rossi anche per un'altra ragione: vede pure
#   i casi che diventano **piu' verdi**, che sono il sintomo di un guasto che
#   non e' quello che si credeva.
#
# ===========================================================================
# ⛔⛔ E QUESTO BANCO HA GIA' SMENTITO DUE MIE SPIEGAZIONI — 21 agosto 2026
# ===========================================================================
#
# Avevo dichiarato RG3 «il guasto che vale piu' di tutti», con questa ragione:
# *«toglie il `close()` del descrittore vecchio, quindi Mutter non vede nessun
# distacco e il desktop resta bloccato»*.  ⛔ `[M]` Non cambia niente.
# Allora avevo scritto RG4: *«e allora e' `ei_disconnect()` che manda il
# distacco»*.  ⛔ `[M]` Non cambia niente nemmeno lui.
#
# ⇒ ⭐ Le due strade sono **ridondanti**, e ciascuna basta da sola.  Solo `RG5`,
#     che le toglie **tutt'e due**, rompe la guarigione.
#
# ⚠ E la lezione conta piu' della meccanica: **due ipotesi consecutive, tutt'e
#   due plausibili, tutt'e due smentite da un guasto innestato.**  Nessuna delle
#   due si sarebbe scoperta rileggendo il codice, e la prima era gia' scritta in
#   `mutter.h` come se fosse un fatto.  ⇒ E' `PIANO.md` §0.4 punto 2 preso alla
#   lettera: si prova a rompere, non a confermare.
set -uo pipefail

QUI=$(cd -- "$(dirname -- "$0")" && pwd)
PAROLA_SUDO=${1:?serve il file 0600 con la parola di sudo}
shift
GUASTI=${*:-RG1 RG2 RG3 RG4 RG5}

SRC=${SRC:-/media/REMOTIX/src/06-i-src}
LAV=${LAV:-/media/REMOTIX/tmp/06-i}
ESITI=$LAV/06-b33-risveglio-esiti.jsonl
SANI=$LAV/sani-risveglio

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; ESITO=1; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ESITO=0

[ -r "$PAROLA_SUDO" ] || { printf '⛔ %s non si legge\n' "$PAROLA_SUDO"; exit 2; }
sudo_mio() { printf '%s\n' "$(cat "$PAROLA_SUDO")" | sudo -S -p 'Password: ' "$@"; }
dentro()   { printf '%s\n' "$(cat "$PAROLA_SUDO")" | sudo -S -p 'Password: ' \
                 bash /media/REMOTIX/enter.sh --root "$@"; }

costruisci() {
	# ⛔ Si guarda l'ESITO del costruttore, non la presenza del file: un binario
	#    di ieri risponde «si'» a *esiste?* come uno di adesso.
	dentro "bash /srv/src/06-i-src/banchi/06-b33-risveglio-costruisci.sh" \
		> "$LAV/costr-$1.log" 2>&1
}

giro() { # $1 = etichetta
	# ⛔ L'etichetta la decide il lanciatore («s2-tenuto»), quindi qui si legge
	#    l'ULTIMA riga con quell'etichetta: e' il giro appena fatto.
	bash "$QUI/06-b33-risveglio.sh" "$PAROLA_SUDO" tenuto > "$LAV/giro-$1.log" 2>&1
	inf "giro $1: $(grep -acE 'OK|NO|DIFETTO|NON_IN_SCENA' "$LAV/giro-$1.log") righe di verdetto"
}

# la mappa «caso → esito» dell'ultimo giro, letta dagli ESITI e non dallo schermo
mappa() { python3 - "$ESITI" <<'EOF'
import json, sys
righe = [json.loads(x) for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
for r in reversed(righe):
    if r["etichetta"] == "s2-tenuto":
        print(" ".join("%s=%s" % (c["caso"].split()[0], c["esito"]) for c in r["casi"]))
        break
EOF
}

# i casi il cui verdetto e' CAMBIATO fra due mappe
cambiati() { python3 - "$1" "$2" <<'EOF'
import sys
a = dict(x.split("=") for x in sys.argv[1].split())
b = dict(x.split("=") for x in sys.argv[2].split())
fuori = []
for k in sorted(set(a) | set(b)):
    if a.get(k) != b.get(k):
        fuori.append(k)
print(" ".join(fuori))
EOF
}

mkdir -p "$SANI"

log "0. Le copie SANE dei due file che i guasti toccano"
for f in input.c mutter.c; do
	cp "$SRC/src/$f" "$SANI/$f" || { ko "non ho fatto la copia di $f"; exit 2; }
	inf "$f salvato ($(wc -l < "$SANI/$f") righe)"
done
risana() { for f in input.c mutter.c; do cp "$SANI/$f" "$SRC/src/$f"; done; }

log "1. Il giro SANO — ⛔ e se questo non e' verde non si certifica niente"
costruisci sano || { ko "⛔ il sano non compila"; tail -5 "$LAV/costr-sano.log"; exit 3; }
giro sano
SANA=$(mappa)
inf "mappa sana: $SANA"
case "$SANA" in
*=NO*) ko "⛔ il giro SANO ha dei rossi: il banco non e' certificabile"; exit 3 ;;
*DIFETTO_VIVO*) ko "⛔ il giro SANO ha ancora dei DIFETTO_VIVO: le cure «A» e «C»"
                ko "   non sono dentro, oppure non funzionano.  Non si certifica"; exit 3 ;;
"") ko "⛔ nessun esito «s2-tenuto» negli esiti: il giro non ha nemmeno girato"; exit 3 ;;
*) ok "il giro sano e' tutto verde" ;;
esac

for G in $GUASTI; do
	ATTESO=$(python3 "$QUI/06-b33-risveglio-guasti.py" --elenco \
		| grep -A1 "^$G " | sed -n 's/.*devono CAMBIARE: //p')
	FILE=$(python3 "$QUI/06-b33-risveglio-guasti.py" --elenco \
		| grep "^$G " | sed -n 's/.*\[\(.*\)\]/\1/p')
	log "2.$G — devono cambiare: $ATTESO   (in $FILE)"
	risana
	if ! python3 "$QUI/06-b33-risveglio-guasti.py" --albero "$SRC" --guasto "$G"; then
		ko "⛔ $G non si e' innestato: NON e' «il guasto non fa niente»"
		continue
	fi
	if ! costruisci "$G"; then
		ko "⛔ $G non compila:"; tail -6 "$LAV/costr-$G.log" | sed 's/^/        /'
		continue
	fi
	giro "$G"
	GUASTA=$(mappa)
	inf "mappa guasta: $GUASTA"
	OTT=$(cambiati "$SANA" "$GUASTA")
	inf "casi cambiati: ${OTT:-nessuno}"
	# ⛔ UGUAGLIANZA DELL'INSIEME, non appartenenza: un guasto che cambiasse
	#    TUTTO conterrebbe per forza il caso dichiarato, e passerebbe.
	# ⛔ «nessuno» e' un atteso, non un caso da cercare: e' l'insieme VUOTO.
	#    ⚠ Senza questa riga il confronto cercava un caso di nome «nessuno» e
	#      dichiarava rosso un non-guasto che aveva fatto esattamente quel che
	#      doveva — difetto del banco, 21 ago 2026.
	[ "$ATTESO" = nessuno ] && ATTESO=""
	A=$(printf '%s\n' $ATTESO | sort | tr '\n' ' ')
	B=$(printf '%s\n' $OTT | sort | tr '\n' ' ')
	if [ "$A" = "$B" ]; then
		ok "⭐ $G ha cambiato ESATTAMENTE i casi dichiarati ($ATTESO)"
	else
		ko "⛔ $G doveva cambiare «${A% }» e ha cambiato «${B:-nulla}»."
		ko "   ⚠ O il guasto non e' quello che credo, o il banco non sa vederlo,"
		ko "   o ne vede piu' di uno: si corregge l'ATTESO con la ragione scritta"
		ko "   accanto, non il verdetto"
	fi
done

log "3. Si rimettono i file SANI e si ricostruisce"
risana
if costruisci risana; then
	ok "risanato e ricostruito"
else
	ko "⛔ il risanamento NON ha ricostruito: l'albero resta GUASTO"
fi
giro risanato
RIS=$(mappa)
inf "mappa risanata: $RIS"
[ "$RIS" = "$SANA" ] && ok "il giro risanato e' identico al sano" \
	|| ko "⛔ il risanato NON e' tornato come il sano: $RIS"

log "Esito"
inf "esiti: $ESITI"
exit $ESITO
