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
SANI=$LAV/sani-risveglio

# ⛔⛔ I PERCORSI DENTRO IL CONTENITORE SI DERIVANO, NON SI SCRIVONO — rilievo R4
#      della revisione avversariale, 22 agosto 2026.
#
#      `enter.sh` mostra `/media/REMOTIX/src` come `/srv/src` e
#      `/media/REMOTIX/tmp` come `/srv/remotix/tmp`.  ⚠ Il nome dell'albero
#      **attraversa il confine del contenitore**, ed e' esattamente il punto in
#      cui `07-b41-accendi.sh` ha gia' pagato: *«con un albero diverso si
#      compilava quello di prima e si accendeva quello nuovo — "ha compilato" e
#      "ha compilato QUELLO GIUSTO" avevano la stessa faccia»*.
#
# ⛔ E si CONTROLLA che l'albero stia dove il contenitore lo sa vedere: un `SRC`
#    fuori da `/media/REMOTIX/src` non si compilerebbe affatto, e il modo
#    peggiore di scoprirlo e' un guasto che «non fa niente».
case "$SRC" in
/media/REMOTIX/src/*) ;;
*) printf '⛔ SRC=%s non sta sotto /media/REMOTIX/src: il contenitore non lo vede,\n' "$SRC"
   printf '   e un guasto innestato li dentro non arriverebbe MAI al binario.\n'
   exit 2 ;;
esac
case "$LAV" in
/media/REMOTIX/tmp/*) ;;
*) printf '⛔ LAV=%s non sta sotto /media/REMOTIX/tmp: il binario uscirebbe da\n' "$LAV"
   printf '   una parte e il terreno lo cercherebbe da un altra.\n'
   exit 2 ;;
esac
DENTRO_SRC=/srv/src/${SRC#/media/REMOTIX/src/}
DENTRO_LAV=/srv/remotix/tmp/${LAV#/media/REMOTIX/tmp/}

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
	#
	# ⛔⛔ E IL PERCORSO SI DERIVA DA `$SRC`, non si scrive a mano — rilievo R4
	#      della revisione avversariale, 22 agosto 2026.
	#
	#      Qui c'era `/srv/src/06-i-src` cablato, mentre il guasto, le copie sane
	#      e il risanamento passavano tutti da `$SRC`.  ⇒ Bastava passare un
	#      `SRC` diverso per **guastare un albero e ricompilarne un altro**: il
	#      guasto non arrivava al binario, RG3 e RG4 (atteso «nessuno») uscivano
	#      verdi **per costruzione**, e il risanato combaciava.  ⚠ E' la stessa
	#      forma che in un altro banco ha gia' prodotto un rosso falso contro il
	#      prodotto.
	#
	# ⚠ Dentro `enter.sh` la cartella `/media/REMOTIX/src` si vede come
	#   `/srv/src` e `/media/REMOTIX/tmp` come `/srv/remotix/tmp`: la traduzione
	#   si fa QUI, una volta sola, e con accanto la ragione.
	dentro "SRC=$DENTRO_SRC/src LAV=$DENTRO_LAV bash $DENTRO_SRC/banchi/06-b33-risveglio-costruisci.sh" \
		> "$LAV/costr-$1.log" 2>&1
}

# ⛔⛔ IL GIRO, E QUEL CHE SUCCEDE SE NON GIRA — rilievo R3, 22 agosto 2026.
#
# Prima questa funzione **buttava l'esito** di `risveglio.sh` e stampava il
# conto delle righe con `inf`, mai con `ko`; e `mappa()` leggeva l'**ultima**
# riga `s2-tenuto` da un file che il giudice apre in **append** e che nessuno
# troncava.
#
# ⇒ Bastava un server acceso sulla porta perche' `iniettore-accendi` rifiutasse,
#   `rimonta` tornasse 3 e `risveglio.sh` uscisse **senza appendere niente**:
#   `SANA` diventava la mappa **verde di ieri**, ogni mappa guasta era la stessa
#   riga, il risanato combaciava ⇒ ⛔ **certificazione verde su zero giri**.
#
# Le due cure, e servono tutt'e due:
#   1. **ogni giro ha un file di esiti SUO**, cancellato prima: se resta vuoto,
#      il giro non ha girato, e non c'e' nessuna riga di ieri da leggere;
#   2. **l'esito di `risveglio.sh` si guarda**.  ⚠ Ma non basta «diverso da
#      zero»: con un guasto innestato i casi rossi ci DEVONO essere, e allora il
#      copione esce 1 legittimamente.  ⇒ Si distingue per codice: **3 = la scena
#      non ha retto** (`rimonta` fallita, testimone non aperto), 0/1 = il giro ha
#      dato un verdetto.
#
# Riempie `MAPPA`; ritorna 1 se il giro non ha girato.
MAPPA=""
giro() { # $1 = etichetta
	local f e
	f=$LAV/esiti-$1.jsonl
	MAPPA=""
	# ⛔ E si CONTROLLA che sia sparito, non si spera: il giudice scrive quel
	#    file **da root**, e se un giorno la cartella non fosse piu' nostra il
	#    `rm` fallirebbe in silenzio ⇒ si leggerebbe di nuovo la riga di ieri,
	#    cioe' esattamente il difetto che questa funzione esiste per chiudere.
	rm -f "$f" 2>/dev/null || sudo_mio rm -f "$f" >/dev/null 2>&1
	if [ -e "$f" ]; then
		ko "⛔ IL BANCO: non riesco a cancellare $f ⇒ leggerei l'esito di IERI"
		return 1
	fi
	ESITI="$f" bash "$QUI/06-b33-risveglio.sh" "$PAROLA_SUDO" tenuto \
		> "$LAV/giro-$1.log" 2>&1
	e=$?
	if [ "$e" -ge 2 ]; then
		ko "⛔ IL BANCO: il giro «$1» non ha retto (uscita $e) — la scena non si e'"
		ko "   montata, e NON c'e' nessun verdetto da confrontare.  Coda:"
		tail -6 "$LAV/giro-$1.log" | sed 's/^/        /'
		return 1
	fi
	if [ ! -s "$f" ]; then
		ko "⛔ IL BANCO: il giro «$1» e' uscito $e ma non ha scritto NESSUN esito"
		ko "   in $f ⇒ il giudice non ha nemmeno parlato"
		return 1
	fi
	MAPPA=$(mappa "$f")
	if [ -z "$MAPPA" ]; then
		ko "⛔ IL BANCO: in $f non c'e' nessuna riga «s2-tenuto»"
		return 1
	fi
	inf "giro $1: $(grep -acE 'OK|NO|DIFETTO|NON_IN_SCENA' "$LAV/giro-$1.log") righe di verdetto"
	return 0
}

# la mappa «caso → esito» del giro indicato — ⛔ dal SUO file, non da un file
# comune in append: vedi il riquadro qui sopra.
mappa() { python3 - "$1" <<'EOF'
import json, sys
try:
    righe = [json.loads(x) for x in open(sys.argv[1], encoding="utf-8") if x.strip()]
except OSError:
    righe = []
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
# ⛔ E se il giro non gira ci si FERMA: senza mappa sana non c'e' niente con cui
#    confrontare, e proseguire vorrebbe dire certificare contro il nulla.
giro sano || { ko "⛔ senza il giro sano non si certifica niente"; exit 3; }
SANA=$MAPPA
inf "mappa sana: $SANA"
case "$SANA" in
*=NO*) ko "⛔ il giro SANO ha dei rossi: il banco non e' certificabile"; exit 3 ;;
*DIFETTO_VIVO*) ko "⛔ il giro SANO ha ancora dei DIFETTO_VIVO: le cure «A» e «C»"
                ko "   non sono dentro, oppure non funzionano.  Non si certifica"; exit 3 ;;
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
	# ⛔ E se il giro guasto non gira, NON si confronta: «non ho guardato» e «il
	#    guasto non fa niente» hanno lo stesso aspetto in una mappa mancante, e
	#    e' proprio il modo in cui questo copione poteva stampare verde a zero
	#    giri (rilievo R3).
	if ! giro "$G"; then
		ko "⛔ $G: il giro non ha girato ⇒ non si puo' dire NIENTE su questo guasto"
		continue
	fi
	GUASTA=$MAPPA
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
if giro risanato; then
	RIS=$MAPPA
	inf "mappa risanata: $RIS"
	[ "$RIS" = "$SANA" ] && ok "il giro risanato e' identico al sano" \
		|| ko "⛔ il risanato NON e' tornato come il sano: $RIS"
else
	ko "⛔ il giro risanato non ha girato: ⚠ NON si puo' dire che l'albero sia"
	ko "   tornato sano, e resta il dubbio che ci sia dentro un guasto"
fi

log "Esito"
inf "esiti: $ESITI"
exit $ESITO
