#!/usr/bin/env bash
# ===========================================================================
# 10-d1-lancia — LA CAMPAGNA DEL BUDGET (incarico 10-D1)
#
#   porta 8250 · utenti CONDIVISI provamt1…provamt11 · albero 10d1-src
#   lavoro /media/REMOTIX/tmp/10d1 · unita' remotix-8250 · lucchetto `10-d1`
#
# ═══════════════════════════════════════════════════════════════════════════
# ⭐⭐ LA CAMPAGNA E' IL ROSSO PRIMA E IL VERDE DOPO — quattro giri, non uno
# ═══════════════════════════════════════════════════════════════════════════
#
#  1. ⛔ **IL ROSSO** · scena `satura`, budget **SPENTO**: la salita satura, e
#     `[M]` §S.2 dice che cosa deve succedere — l'ottavo entra con `negati 0` e
#     tutti vanno a ~1,5 fot/s.  ⇒ Il banco `10-b92` da' **rosso**, ed e' il
#     rosso che si vuole vedere.
#  2. ⭐ **IL VERDE** · stessa scena, stesso banco, stessi predicati, budget
#     **ACCESO** al numero misurato (`[M]` 480 Mpixel/s, §6.9): qualcuno riceve
#     `CONGEDO 0x06 BUDGET_PIENO` **prima del dirupo**, e ⛔ chi e' dentro NON
#     peggiora.  ⚠ `10-b92` non conosce il budget: per lui una sessione
#     rifiutata e' un rosso.  ⇒ Il verde si legge **appaiando le due colonne
#     dei gradini che TUTT'E DUE i giri hanno fatto**, e il rifiuto si legge
#     nel registro del server.  E' scritto qui perche' non venga scambiato per
#     un banco che passa.
#  3. ⭐⭐ **LA PROVA CHE VALE DOPPIO** · scena `ferma`, **dieci** sessioni,
#     budget ACCESO: `[M]` §6.16 una ferma costa **0,01 %**, e ⛔ un budget che
#     rifiutasse dieci inquilini che non costano niente sbaglierebbe **quanto**
#     uno che ammette l'ottavo che fa crollare tutto.  ⇒ Qui il banco deve
#     essere **verde pieno**: dieci dentro, `negati 0`.
#  4. ⛔ **IL CONTROLLO NEGATIVO** · si rispegne il budget e si rifa' il passo
#     1 corto: il rosso deve **tornare**.  Se non torna, non si stava
#     misurando la cura.
#
# ⛔ Ogni giro e' preceduto da `banchi/10-b0-terreno.sh` con `LUCCHETTO_MIO=1`.
#
# Uso:
#     bash banchi/10-d1-lancia.sh              tutta la campagna
#     bash banchi/10-d1-lancia.sh rosso|verde|ferme|negativo
#     bash banchi/10-d1-lancia.sh porta        solo sorgenti + compila
# ===========================================================================
set -uo pipefail
QUI=$(cd "$(dirname "$0")/.." && pwd)

export MACCHINA=${MACCHINA:-nicfio@192.168.0.2}
export PAROLA_SUDO=${PAROLA_SUDO:-nicfio}
export IND=${IND:-192.168.0.2}
export PORTA=${PORTA:-8250}
export ALBERO=${ALBERO:-/media/REMOTIX/src/10d1-src}
export LAV=${LAV:-/media/REMOTIX/tmp/10d1}
export DENTRO_ALB=${DENTRO_ALB:-/srv/src/10d1-src}
export DENTRO_LAV=${DENTRO_LAV:-/srv/remotix/tmp/10d1}
export UNITA=${UNITA:-remotix-$PORTA}
export LUCCHETTO=${LUCCHETTO:-/media/REMOTIX/tmp/.lucchetto-gpu.d}
export IO_SONO=${IO_SONO:-10-d1}
export FUORI=${FUORI:-/tmp/10-d1}
export PAROLA_UTENTE=${PAROLA_UTENTE:-mt-dieci-2026}
export LUCCHETTO_ESTERNO=1
export SCENA_BIN=${SCENA_BIN:-/media/REMOTIX/src/04-b30-scena-lav/04-b30-scena}

# ⛔ IL NUMERO DEL BUDGET, E DA DOVE VIENE — `[M]` §6.9: **479,8 Mpixel/s**, il
#    massimo lavoro CONSEGNATO che questa macchina ha mostrato (culmine al
#    sesto gradino della salita satura, i5-13500T · Intel UHD 730 `renderD128`,
#    1080p H.264, cure della fase 9 accese).  ⭐ Si arrotonda a 480 e lo si
#    scrive qui, perche' un numero passato a mano su una riga di comando e'
#    un numero che nessuno sa piu' da dove venga.
# ⛔⛔ E NON SI AUTO-TARA: il prodotto non lo deduce, glielo diamo noi — che e'
#      precisamente quel che `--budget-mpixel-s` pretende da chi lo batte.
export BUDGET=${BUDGET:-480}
export RISERVA=${RISERVA:-0.5}
mkdir -p "$FUORI"

log() { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()  { printf '    \033[1;32mOK\033[0m  %s\n' "$*"; }
ko()  { printf '    \033[1;31mNO\033[0m  %s\n' "$*"; }
inf() { printf '    --  %s\n' "$*"; }

CORRIDORE="$QUI/banchi/10-b9d-corri-al-lucchetto.sh"
PY_LUC="$QUI/banchi/09-lucchetto.py"

# ⛔⛔ La corsa si corre SULLA MACCHINA, passo 0,5 s: `prendi()` ritenta ogni
#    5 s, e il lucchetto non e' una coda — e' una corsa (§7.3).  Chi ritenta
#    fitto vince quasi sempre, e `10-b9d` ha gia' misurato 47 ms dal rilascio.
prendi_lucchetto() {
	local secondi=$1 b64 uscita
	[ -f "$CORRIDORE" ] || { ko "⛔ il corridore non c'e': NON misuro"; return 2; }
	b64=$(base64 -w0 "$CORRIDORE")
	ssh -o BatchMode=yes "$MACCHINA" \
	  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c '
	     mkdir -p $LAV && printf %s $b64 | base64 -d > $LAV/corri.sh
	     chmod +x $LAV/corri.sh'" >/dev/null 2>&1 || {
		ko "⛔ il corridore non e' arrivato: NON misuro"; return 2; }
	uscita=$(ssh -o BatchMode=yes -o ServerAliveInterval=30 -o ServerAliveCountMax=1000 \
	  "$MACCHINA" "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' \
	   $LAV/corri.sh '$LUCCHETTO' '$IO_SONO' $secondi 21600 0.5" 2>&1 | grep -v '^tput')
	printf '%s\n' "$uscita" | sed 's/^/    --  /'
	case "$uscita" in
	PRESO*|SCASSINO*) return 0 ;;
	MIO*)
		# ⛔ «Il lucchetto porta gia' il mio nome»: `prendi()` aspetterebbe SE
		#    STESSO (§7.3).  Lo si adotta solo se non c'e' un altro mio
		#    corridore vivo, o due giri userebbero la GPU insieme a nome mio.
		if [ "$(ssh -o BatchMode=yes "$MACCHINA" \
		        "pgrep -f '[c]orri.sh .* $IO_SONO ' | wc -l" 2>/dev/null)" != "0" ]; then
			ko "⛔ lucchetto a nome mio E un altro mio corridore vivo: NON misuro"
			return 2
		fi
		inf "⭐ il lucchetto porta gia' il mio nome e nessun altro corridore mio e' vivo: lo ADOTTO"
		return 0 ;;
	*) ko "⛔ non ho il lucchetto: $uscita"; return 2 ;;
	esac
}
molla_lucchetto() {
	python3 -c "
import importlib.util, os
os.environ['LUCCHETTO'] = '$LUCCHETTO'
spec = importlib.util.spec_from_file_location('luc', '$PY_LUC')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.molla('$IO_SONO')
"
}

terreno() {
	CHI="$IO_SONO" LUCCHETTO_MIO=1 PORTA="$PORTA" UTENTE=provamt1 \
	ALBERO="$ALBERO" LAV="$LAV" PALCO_AMMESSO="${1:-0}" \
		bash "$QUI/banchi/10-b0-terreno.sh"
}

# ⛔ Un giro = spegni · accendi col budget scelto · salita · leggi il registro.
#    ⚠ Il server si RIACCENDE fra un braccio e l'altro perche' il budget e' una
#      opzione della riga d'avvio: e' l'unica strada (`CODER.md` §2-bis), e
#      cambiare braccio senza riaccendere vorrebbe dire misurare due bracci
#      sullo stesso processo, cioe' non misurare niente.
giro() {  # $1 etichetta  $2 opzioni server  $3 scena  $4 quanti  $5 durata
	local et=$1 opz=$2 scena=$3 quanti=$4 durata=$5 rc
	log "$et"
	inf "opzioni del server: «${opz:-nessuna}»  ·  scena $scena  ·  $quanti gradini  ·  ${durata}s"
	bash "$QUI/banchi/10-d1-terreno.sh" spegni >/dev/null 2>&1
	bash "$QUI/banchi/10-d1-terreno.sh" sgombra >/dev/null 2>&1
	OPZIONI_SERVER="$opz" bash "$QUI/banchi/10-d1-terreno.sh" accendi || return 2
	bash "$QUI/banchi/10-d1-terreno.sh" avvio
	QUANTI="$quanti" python3 -u "$QUI/banchi/10-b92-dieci.py" salita \
		--scena "$scena" --quanti "$quanti" --durata "$durata"
	rc=$?
	log "$et — ⛔ I NEGATI, letti nel registro del server"
	ssh -o BatchMode=yes "$MACCHINA" \
	  "printf '%s\n' '$PAROLA_SUDO' | sudo -S -p '' bash -c \"
	    echo -n 'righe 0x06 BUDGET_PIENO: '; grep -ac 'BUDGET_PIENO' $LAV/registro.log
	    grep -a 'budget' $LAV/registro.log | grep -a 'NON entra' | tail -5
	    grep -a 'congedati' $LAV/registro.log | tail -5\"" 2>&1 | grep -v '^tput'
	cp -f /tmp/10-b92/*.json* "$FUORI/" 2>/dev/null
	for f in "$FUORI"/*.json*; do
		[ -e "$f" ] || continue
		mv -f "$f" "${f%.*}-$(printf '%s' "$et" | tr -cd 'a-z')".${f##*.} 2>/dev/null
	done
	bash "$QUI/banchi/10-d1-terreno.sh" spegni >/dev/null 2>&1
	return $rc
}

PASSO=${1:-tutto}

if [ "$PASSO" = porta ]; then
	exec bash "$QUI/banchi/10-d1-terreno.sh" porta
fi

log "⛔ PRIMA LA CERTIFICAZIONE DEL BANCO IMPORTATO — 10-b92 sa dare rosso?"
python3 -u "$QUI/banchi/10-b92-dieci.py" --certifica >"$FUORI/certifica.txt" 2>&1
CRC=$?
tail -3 "$FUORI/certifica.txt" | sed 's/^/    /'
[ $CRC -eq 0 ] || { ko "⛔ 10-b92 --certifica non passa: NON MISURO"; exit 2; }
ok "10-b92 --certifica: passa"

log "⛔⛔ IL LUCCHETTO DELLA GPU — e si aspetta davvero il proprio turno"
prendi_lucchetto 7200 || { ko "⛔ senza lucchetto NON misuro"; exit 2; }
trap 'molla_lucchetto' EXIT

log "⛔ I PALCHI ORFANI, PRIMA DI TOCCARE GLI UTENTI CONDIVISI"
bash "$QUI/banchi/10-d1-terreno.sh" stato || {
	inf "⚠ il terreno dei dieci non regge: SGOMBRO e riguardo"
	bash "$QUI/banchi/10-d1-terreno.sh" sgombra
	bash "$QUI/banchi/10-d1-terreno.sh" stato || {
		ko "⛔ nemmeno dopo lo sgombero: NON misuro"; exit 2; }
}

# ⛔ La parola d'ordine si rifa' DENTRO la finestra del lucchetto: gli utenti
#    sono condivisi e `07-b64-terreno.sh utente` la riscrive a ogni chiamata —
#    l'ultimo che chiama vince, e ogni respinto consuma uno dei tre tentativi
#    del ban per INDIRIZZO, che dura dodici ore e ferma ogni altro agente.
log "⛔ RIFACCIO LA PAROLA DEGLI UNDICI UTENTI CONDIVISI — dentro il lucchetto"
bash "$QUI/banchi/10-d1-terreno.sh" utenti >"$FUORI/utenti.txt" 2>&1 \
	&& ok "parola rifatta per provamt1…11" \
	|| { ko "⛔ non ho potuto rifare la parola: NON misuro"; tail -20 "$FUORI/utenti.txt"; exit 2; }

terreno || { ko "⛔ il terreno della fase non regge: NON misuro"; exit 2; }

ACCESO="--budget-mpixel-s $BUDGET --riserva $RISERVA"
QUANTI_SATURA=${QUANTI_SATURA:-8}
DURATA=${DURATA:-30}

case "$PASSO" in
# ⭐ IL CONTROLLO POSITIVO, e costa trenta secondi: col budget messo **sotto**
#    il caso peggiore di UNA sola 1080p (82,0 Mpixel/s) dev'essere rifiutata
#    **la prima**.  ⛔ Serve perche' un `0x06` che non parte e un `0x06` che
#    parte al momento giusto hanno la stessa faccia finche' non se ne e' visto
#    almeno uno: qui la strada dal verdetto al filo si prova per intero, e senza
#    accendere nemmeno un desktop (il palco non nasce).
filo)    giro "filo"     "--budget-mpixel-s 40 --riserva $RISERVA" satura 1 10; exit $? ;;
rosso)   giro "rosso"    ""        satura "$QUANTI_SATURA" "$DURATA"; exit $? ;;
verde)   giro "verde"    "$ACCESO" satura "$QUANTI_SATURA" "$DURATA"; exit $? ;;
ferme)   giro "ferme"    "$ACCESO" ferma  10                "$DURATA"; exit $? ;;
negativo) giro "negativo" ""       satura "$QUANTI_SATURA" "$DURATA"; exit $? ;;
esac

giro "filo" "--budget-mpixel-s 40 --riserva $RISERVA" satura 1 10; P=$?
giro "rosso" ""        satura "$QUANTI_SATURA" "$DURATA"; R=$?
giro "verde" "$ACCESO" satura "$QUANTI_SATURA" "$DURATA"; V=$?
giro "ferme" "$ACCESO" ferma  10                "$DURATA"; F=$?
giro "negativo" ""     satura "$QUANTI_SATURA" "$DURATA"; N=$?

log "IL CONFRONTO"
inf "0 · filo      (budget 40, una sola)    uscita $P  ⛔ diverso da 0 = il 0x06 e' partito"
inf "1 · rosso     (budget SPENTO, satura)  uscita $R"
inf "2 · verde     (budget $BUDGET, satura)   uscita $V"
inf "3 · ferme     (budget $BUDGET, 10 ferme) uscita $F  ⭐ 0 e' quel che deve essere"
inf "4 · negativo  (budget SPENTO, satura)  uscita $N  ⛔ diverso da 0 = il rosso e' tornato"
molla_lucchetto; trap - EXIT
bash "$QUI/banchi/10-d1-terreno.sh" sgombra
bash "$QUI/banchi/10-d1-terreno.sh" spegni
exit 0
