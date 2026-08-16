#!/bin/bash
#
# 02-cattura-certifica.sh — gira SUL SERVER.  ⛔ La certificazione del banco di
# F2.2 col modello di B12: sano N → guasto M → risanato N, con i numeri attesi
# **scritti prima del giro**.
#
#   bash /media/REMOTIX/src/02-cattura-certifica.sh            giro sano + i quattro guasti
#   bash /media/REMOTIX/src/02-cattura-certifica.sh PREFISSO   riusa un giro sano gia' fatto
#
# ===========================================================================
# ⛔ PERCHE' ESISTE, E PERCHE' NELLO STESSO GIRO DI CHI SCRIVE IL BANCO
#
# ⭐ La regola nata l'11 agosto 2026: *chi scrive un banco lo certifica nello
#    stesso giro*, o il conto non cala mai.  E `PIANO.md` §0.3 punto 4: ogni
#    fase, prima di dichiarare un numero, dimostra che il suo banco sa vedere il
#    difetto che cerca.
#
# ⛔ E per F2.2 la domanda non e' accademica.  Il difetto che questo banco esiste
#    per vedere e' **un fotogramma nero e valido**: un buffer della misura
#    giusta, con lo stride giusto, il danno giusto, la sequenza giusta — e
#    dentro il nulla.  ⛔ E' il guasto peggiore di questa sotto-fase perche' ogni
#    altro strumento del progetto lo promuoverebbe: `misura-cattura` della fase 0
#    conterebbe 36 fotogrammi al secondo e non guarderebbe dentro nemmeno uno.
#
# ⇒ Un banco che non sa distinguere un fotogramma nero da uno pieno **darebbe
#   fiducia**, ed e' precisamente il caso che `REVIEWER.md` §1 chiama il
#   peggiore: *«un difetto nel banco non lo trova niente, e avvelena ogni misura
#   successiva perche' da' fiducia»*.
#
# ===========================================================================
# ⛔ IL GUASTO SI INNESTA NEI PIXEL, E NON TOCCA NE' IL PRODUTTORE NE' IL GIUDICE
#
# E' la ragione per cui il produttore (`02-cattura-fotogramma.c`) e il giudice
# (`02-cattura-giudica.py`) sono due programmi separati: fra i due c'e' un file,
# e in quel file si puo' mettere quel che si vuole.  ⭐ Nessuna ricompilazione,
# nessuna riga cambiata, nessun `git`.  Il guasto e' il **dato**, che e' il modo
# piu' onesto di guastare un giudice.
#
# ⛔ E SEMPRE SU UNA COPIA, con l'originale tenuto da parte e l'impronta accanto
#    — come `01-b12-guasti.py`, che il file da guastare non lo tocca mai.
#
# ===========================================================================
# ⛔ GLI ATTESI, SCRITTI PRIMA DEL GIRO (B0.4)
#
#   il giro SANO esce 0 (VERDE) — e non e' un atteso allargato: il fotogramma
#   c'e', e' 1920×1080 come chiesto, e contiene la scena «bandiera».
#   ⚠ Se il giro sano NON uscisse 0, la certificazione **si ferma**: non si
#     innesta un guasto su un banco gia' rosso, perche' il rosso di dopo non
#     direbbe niente (`FASI.md` §00-ambiente, e la lezione di B13).
#
#   | # | il guasto innestato nel .raw   | atteso | marca PRETESA           | marca VIETATA |
#   |---|-------------------------------|--------|-------------------------|---------------|
#   | G1| nero pieno, stessi byte       |   1    | FOTOGRAMMA NERO         | —             |
#   | G2| grigio uniforme, stessi byte  |   1    | SCENA NON RICONOSCIUTA  | FOTOGRAMMA NERO |
#   | G3| ultimi byte tagliati          |   1    | BYTE NON TORNANO        | —             |
#   | G4| il «primo» copiato sul «regime»|  1    | IL BUFFER NON E' CAMBIATO| FOTOGRAMMA NERO |
#
#   e il RISANATO torna 0 dopo ciascuno.
#
# ⭐ LE DUE COLONNE «PRETESA» E «VIETATA» SONO LA META' CHE CONTA, e senza la
#    seconda questa certificazione sarebbe una recita:
#
#   - **G2** e' il guasto che distingue un giudice da un misuratore di
#     luminosita'.  Un grigio uniforme non e' nero: chiamarlo nero vorrebbe dire
#     sbagliare la diagnosi peggiore proprio nel caso in cui serve, e la cura
#     verrebbe cercata dalla parte sbagliata — la stessa mezza giornata che
#     `PIANO.md` racconta per la sessione nera;
#   - **G4** e' il guasto della trappola 8 di `LEZIONI.md` §4: *«l'ultimo
#     fotogramma va conservato e rispedito, o chi si collega a un desktop fermo
#     resta al nero»*.  Un buffer vecchio rispedito e' un fotogramma
#     perfettamente valido, non nero, con la scena dentro — ⛔ **verde su ogni
#     controllo che guardi un fotogramma solo**.  Si vede solo confrontandone
#     due, ed e' per questo che il produttore ne prende due.
#
# ⛔ E un guasto che NON e' in questa tabella, dichiarato invece che taciuto:
#    **il buffer della scheda sbagliata** (`LEZIONI.md` §4 trappola 6, due GPU
#    su questa macchina).  Non e' innestabile qui e questo banco non lo
#    vedrebbe: sulla strada della memoria i pixel arrivano comunque.  Resta una
#    `[?]` del rapporto, non una cosa che questo verde assolve.
#
# ===========================================================================
set -uo pipefail

QUI=${QUI:-/media/REMOTIX/tmp/02-cattura}
SRC=${SRC:-/media/REMOTIX/src}
GIUDICE=$SRC/02-cattura-giudica.py
LANCIA=$SRC/02-cattura-lancia.sh
SCENA=${SCENA:-bandiera}
mkdir -p "$QUI" || { echo "⛔ non riesco a creare $QUI" >&2; exit 2; }
REGISTRO=$QUI/certificazione-$(date -u +%Y%m%d-%H%M%S).log

ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }
log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }

ATTESO_SANO=0

# ---------------------------------------------------------------------------
#  L'innesto: sempre su una copia, con l'impronta di prima e di dopo
# ---------------------------------------------------------------------------
innesta()
{
	local che=$1 regime=$2 primo=$3
	python3 - "$che" "$regime" "$primo" <<'FINE'
import os, sys
che, regime, primo = sys.argv[1:4]
n = os.path.getsize(regime)
if che == "nero":
    dati = bytes(n)
elif che == "grigio":
    # ⛔ Non un grigio qualunque: BGRx con B=G=R=128 e x=255, cioe' un
    #    fotogramma perfettamente valido e perfettamente inutile.
    dati = bytes([128, 128, 128, 255]) * (n // 4) + bytes(n % 4)
elif che == "troncato":
    dati = open(regime, "rb").read()[: n - 40000]
elif che == "copia":
    dati = open(primo, "rb").read()
    if len(dati) > n:
        dati = dati[:n]
    elif len(dati) < n:
        dati = dati + bytes(n - len(dati))
else:
    print("guasto sconosciuto:", che, file=sys.stderr)
    sys.exit(2)
open(regime, "wb").write(dati)
print("    --  innestato «%s»: %d byte (erano %d)" % (che, len(dati), n))
FINE
	return $?
}

impronta() { sha256sum "$1" | cut -d' ' -f1; }

# ---------------------------------------------------------------------------
#  Un giro del giudice, e il confronto con l'atteso scritto prima
# ---------------------------------------------------------------------------
giudica()
{
	local prefisso=$1 dove=$2
	python3 -u "$GIUDICE" --manifesto "$prefisso.json" --scena "$SCENA" \
	        --json "$dove.json" > "$dove.log" 2>&1
	return $?
}

marche_di()
{
	# ⛔ Solo le marche ROSSE: un avviso sul fotogramma `primo` — dove la scena
	#    non c'e' ancora — non e' un rilievo, e contarlo qui farebbe passare per
	#    «il guasto e' stato visto» un rumore che c'era anche nel giro sano.
	python3 -c '
import json, sys
v = json.load(open(sys.argv[1]))
m = [r["marca"] for f in v.get("fotogrammi", {}).values()
     for r in f.get("rilievi", []) if r.get("rosso", True)]
m += [r["marca"] for r in v.get("confronto_primo_regime", {}).get("rilievi", [])]
print(" ".join(sorted(set(m))))' "$1"
}

verifica()
{
	local nome=$1 uscita=$2 atteso=$3 marche=$4 pretesa=$5 vietata=$6
	local buono=si
	if [ "$uscita" != "$atteso" ]; then
		ko "$nome: uscita $uscita, atteso $atteso"; buono=
	fi
	if [ -n "$pretesa" ] && [[ "$marche" != *"$pretesa"* ]]; then
		ko "$nome: manca la marca PRETESA «$pretesa» — trovate: ${marche:-nessuna}"; buono=
	fi
	if [ -n "$vietata" ] && [[ "$marche" == *"$vietata"* ]]; then
		ko "$nome: c'e' la marca VIETATA «$vietata» — il giudice sbaglia diagnosi"; buono=
	fi
	if [ -n "$buono" ]; then
		ok "$nome: uscita $uscita come atteso, marche: ${marche:-nessuna}"
		return 0
	fi
	return 1
}

# ===========================================================================
{
log "0. LO STATO INIZIALE — si dichiara e si verifica (B0.1)"
for f in "$GIUDICE" "$LANCIA"; do
	if [ ! -r "$f" ]; then ko "⛔ non si legge: $f"; exit 2; fi
done
ok "i due file del banco si leggono"

log "0-bis. IL GIUDICE PRIMA DI TUTTO: passa il proprio controllo positivo?"
inf "⛔ Non si certifica un banco con uno strumento non certificato: sarebbe misurare"
inf "   con un metro di cui non si e' mai controllata la scala (LEZIONI.md §1.2)."
python3 -u "$GIUDICE" --solo-controllo-positivo
if [ $? -ne 0 ]; then
	ko "⛔ il giudice NON e' certificato: la certificazione si ferma qui"
	exit 2
fi
ok "il giudice trova la bandiera, chiama nero il nero, e NON chiama nero il grigio"

# ---------------------------------------------------------------------------
log "1. IL GIRO SANO — e l'atteso e' $ATTESO_SANO, scritto prima"
PREFISSO=${1:-}
if [ -z "$PREFISSO" ]; then
	inf "nessun prefisso dato: faccio un giro vero con $LANCIA"
	SCENA=$SCENA bash "$LANCIA" misura
	U_LANCIA=$?
	inf "il giro sano e' uscito con $U_LANCIA"
	# ⛔ L'uscita non basta: serve il PREFISSO del giro, e lo si prende dal file
	#    piu' recente invece di indovinarlo.  ⚠ E la lista si costruisce con un
	#    glob, non con `ls` dentro una pipe: «nessun file» e «ls e' fallito»
	#    hanno lo stesso aspetto in una catena di `|`, ed e' la voce 3 di
	#    `FASI.md` §00-ambiente — «nessuna riga trovata» era una lettura negata.
	CANDIDATI=()
	for m in "$QUI"/giro-*.json; do
		case "$m" in *-verdetto.json) continue ;; esac
		[ -f "$m" ] && CANDIDATI+=("$m")
	done
	if [ ${#CANDIDATI[@]} -eq 0 ]; then
		ko "⛔ nessun manifesto in $QUI: il giro sano non ha prodotto niente."
		inf "⚠ Non e' «il banco e' rotto»: e' «non c'e' stato nessun giro»."
		exit 2
	fi
	PREFISSO=$(ls -t "${CANDIDATI[@]}" | head -1)
	PREFISSO=${PREFISSO%.json}
fi
if [ -z "$PREFISSO" ] || [ ! -f "$PREFISSO.json" ]; then
	ko "⛔ non trovo il manifesto del giro sano ($PREFISSO.json)"
	exit 2
fi
ok "giro sano: $PREFISSO"

REGIME=$PREFISSO-regime.raw
PRIMO=$PREFISSO-primo.raw
if [ ! -f "$REGIME" ] || [ ! -f "$PRIMO" ]; then
	ko "⛔ mancano i due .raw del giro sano: non c'e' niente da guastare"
	inf "⚠ e questo NON e' un banco rotto: e' un giro che non ha preso fotogrammi."
	exit 2
fi

# ⛔ L'ORIGINALE SI METTE DA PARTE PRIMA DI TOCCARLO, con l'impronta accanto.
ORIGINALE=$QUI/originale-regime.raw
cp -f "$REGIME" "$ORIGINALE" || exit 2
IMP_ORIG=$(impronta "$ORIGINALE")
inf "originale messo da parte: $ORIGINALE"
inf "impronta: $IMP_ORIG"

giudica "$PREFISSO" "$QUI/cert-sano"; U_SANO=$?
M_SANO=$(marche_di "$QUI/cert-sano.json")
verifica "sano" "$U_SANO" "$ATTESO_SANO" "$M_SANO" "" ""
if [ $? -ne 0 ]; then
	ko "⛔ IL GIRO SANO NON E' SANO: la certificazione si ferma."
	inf "Innestare un guasto su un banco gia' rosso darebbe un rosso che non dice niente."
	inf "Il registro del giudice:"
	sed 's/^/       /' "$QUI/cert-sano.log"
	cp -f "$ORIGINALE" "$REGIME"
	exit 2
fi

# ---------------------------------------------------------------------------
FALLITI=0
#      nome        atteso  marca PRETESA               marca VIETATA
GUASTI=(
	"nero|1|FOTOGRAMMA NERO|"
	"grigio|1|SCENA NON RICONOSCIUTA|FOTOGRAMMA NERO"
	"troncato|1|BYTE NON TORNANO|"
	"copia|1|IL BUFFER NON E' CAMBIATO|FOTOGRAMMA NERO"
)
for voce in "${GUASTI[@]}"; do
	IFS='|' read -r NOME ATT PRETESA VIETATA <<< "$voce"

	log "2. GUASTO «$NOME» — atteso $ATT, marca pretesa «$PRETESA», vietata «${VIETATA:-nessuna}»"
	cp -f "$ORIGINALE" "$REGIME" || exit 2
	innesta "$NOME" "$REGIME" "$PRIMO" || { ko "innesto fallito"; FALLITI=$((FALLITI+1)); continue; }
	inf "impronta dopo l'innesto: $(impronta "$REGIME")"

	giudica "$PREFISSO" "$QUI/cert-guasto-$NOME"; U=$?
	M=$(marche_di "$QUI/cert-guasto-$NOME.json")
	verifica "guasto/$NOME" "$U" "$ATT" "$M" "$PRETESA" "$VIETATA" || FALLITI=$((FALLITI+1))

	log "3. RISANATO dopo «$NOME» — atteso $ATTESO_SANO"
	cp -f "$ORIGINALE" "$REGIME" || exit 2
	IMP=$(impronta "$REGIME")
	if [ "$IMP" != "$IMP_ORIG" ]; then
		ko "⛔ il risanamento non ha rimesso il file com'era: $IMP ≠ $IMP_ORIG"
		FALLITI=$((FALLITI+1))
	else
		ok "l'impronta e' tornata quella di prima: $IMP"
	fi
	giudica "$PREFISSO" "$QUI/cert-risano-$NOME"; U=$?
	M=$(marche_di "$QUI/cert-risano-$NOME.json")
	verifica "risanato/$NOME" "$U" "$ATTESO_SANO" "$M" "" "" || FALLITI=$((FALLITI+1))
done

# ---------------------------------------------------------------------------
log "4. IL VERDETTO DELLA CERTIFICAZIONE"
cp -f "$ORIGINALE" "$REGIME"
if [ $FALLITI -eq 0 ]; then
	ok "⭐ IL BANCO F2.2 E' CERTIFICATO: sano $ATTESO_SANO → quattro guasti → risanato $ATTESO_SANO"
	inf "⚠ E questo non dice che il banco sia giusto: dice che sa vedere QUESTI quattro"
	inf "  difetti. «Non ho trovato niente» non e' «e' giusto» (REVIEWER.md §0)."
	ESITO=0
else
	ko "⛔ LA CERTIFICAZIONE NON PASSA: $FALLITI verifiche fallite."
	inf "Finche' non passa, nessun numero di questo banco vale."
	ESITO=1
fi
inf "il registro completo di questo giro: $REGISTRO"

# Il catalogo, nella forma di 01-b12-guasti.py, stampato qui perche' resti
# accanto ai numeri invece che in un documento a parte.
cat <<FINE

  LA RIGA PER IL CATALOGO DELLE CERTIFICAZIONI
  ────────────────────────────────────────────────────────────────────────
  nome            F2.2 — la cattura (il fotogramma nero e valido)
  comando         bash /media/REMOTIX/src/02-cattura-certifica.sh
  atteso sano     0  (VERDE: un fotogramma 1920×1080 che contiene la scena)
  guasti          nero · grigio · troncato · copia — innestati nel .raw, mai
                  nel codice, sempre su una copia con l'originale da parte
  atteso guasto   1  ciascuno, con la marca pretesa E quella vietata
  atteso risanato 0  dopo ognuno, con l'impronta tornata quella di prima
  costa           copia-di-file (nessuna ricompilazione)
  riferimento     fasi/rapporti/F2-2-cattura.md · STUDI.md §gnome §3.1 §13 M9 ·
                  LEZIONI.md §1.9 §4 trappola 8 · REVIEWER.md §1 punto 4, E1

FINE
exit $ESITO
} 2>&1 | tee "$REGISTRO"
exit "${PIPESTATUS[0]}"
