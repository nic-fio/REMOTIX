#!/bin/bash
# 04-b23-lancia.sh — ⛔ B23: il filo del canale di input (`RCP.md` §7.3).
#
#     bash banchi/04-b23-lancia.sh
#     bash banchi/04-b23-lancia.sh --senza-certificazione   (piu' svelto)
#
# ===========================================================================
# ⛔ L'ORDINE E' UNA MISURA, e va letto: prima si certifica il banco, poi lo si
#    crede.
#
#    `CODER.md` §3.3: «accerta che il banco sappia produrre il risultato atteso
#    PRIMA di puntarlo sull'incognita».  ⛔ E §3.4, che e' il rovescio piu'
#    insidioso perche' il banco e' verde: «un banco che NON riproduce non e' una
#    prova di correttezza».
#
#    ⇒ Qui il giro e' TRE cose in quest'ordine:
#      1. il GEMELLO combacia?  Senza, il costruttore si ferma per tutti e dieci
#         gli anelli, e non e' un problema di questo banco solo.  ⭐ E a
#         guardarlo non e' piu' questo file: e' la maglia C10 della rete di
#         sicurezza (vedi il riquadro sotto);
#      2. la CERTIFICAZIONE — dodici guasti innestati, uno per giro, e ciascuno
#         deve far diventare B23 rosso esattamente dove dichiarato;
#      3. e solo allora il giro vero.
#
# ===========================================================================
# ⛔ LE USCITE DI QUESTO BANCO — e la terza e' nuova
#
#   0  ⭐ B23 passa, ed e' certificato
#   1  ⛔ B23 NON passa: un giudizio, e si ripara
#   2  ⛔ ci si ferma prima di cominciare: il gemello DIVERGE, oppure C10 non ha
#      potuto nemmeno girare.  ⚠ Non e' un verdetto sul canale di input: e' il
#      terreno di B23 che non regge, perche' girerebbe su un protocollo che non
#      e' quello di `src/`
#   3  ⛔ le prove sono passate, ma **il gemello non l'ho potuto guardare**
#      (§4.5 della fase 11).  ⛔ NON e' un rosso e ⛔ non si rimette in coda —
#      ma non e' nemmeno un «passa», o sarebbe un verde che non ha guardato
#      niente (`LEZIONI.md` §1.47)
#
# ===========================================================================
# ⚠ QUESTO BANCO NON APRE NESSUNA PORTA, e va detto perche' e' un'eccezione.
#
# Le porte 7621-7625 sono di A3 e restano libere: B23 gira **in processo**, e
# non c'e' niente da mettere in rete.  ⛔ La ragione e' dichiarata e non e' una
# comodita': `src/webtransport.c` oggi i byte del canale di input li SCARTA
# (`G_UNI_OK`, e la riga di registro lo dice), e quel file non e' di questo
# anello.  La cucitura si chiede al coordinatore — vedi
# `fasi/rapporti/F4-A3-filo-input.md`.
#
# ⚠ E siccome non apre porte, non fa scattare nessun ban di §4.4-bis e non ha
#   bisogno ne' di un `--ban-file` suo ne' di un `--comando-socket`: gli altri
#   nove anelli non se ne accorgono nemmeno.
set -u

QUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RADICE="$(cd "$QUI/.." && pwd)"
USCITA="${USCITA:-/tmp/b23}"
CERTIFICA=1
[ "${1:-}" = "--senza-certificazione" ] && CERTIFICA=0

VERDE=$'\033[32m'; ROSSO=$'\033[31m'; GIALLO=$'\033[33m'; GRIGIO=$'\033[0m'
mkdir -p "$USCITA"
GUASTI=0

# ===========================================================================
# ⭐⭐ IL GEMELLO NON SI GUARDA PIU' A MANO: lo guarda C10
# ===========================================================================
#
# ⛔ Qui c'era `for f in rcp.c rcp.h autenticazione.c`, cioe' l'elenco dei
#    gemelli RICOPIATO dentro questo file.  ⚠ Ed e' la forma esatta di
#    `LEZIONI.md` §1.47: nasce un quarto file gemello, nessuno tocca quella
#    riga, e questo banco continua a dire ✅ avendo guardato tre file su
#    quattro — ⛔ con la stessa faccia di quando li guardava tutti.
#
# ⇒ ⭐ `banchi/11-scatole/11-c10-le-copie-gemelle.py` fa le tre cose che qui non
#   si facevano: **LEGGE** `GEMELLATI` da `src/Makefile` invece di ricopiarlo,
#   confronta **byte per byte**, e si accorge di un gemello di fatto che
#   **nessuno ha dichiarato**.  Gira ovunque, senza contenitore e senza essere
#   amministratore, in una frazione di secondo.
#
# ===========================================================================
# ⛔⛔ E LA CHIAMATA STA FUORI DALLA CERTIFICAZIONE, di proposito
# ===========================================================================
#
# Il passo 2 innesta guasti dentro `banchi/rcp/rcp.c` **apposta**, uno per giro.
# ⛔ C10 chiamata li' in mezzo darebbe rosso su un guasto **voluto**: un rosso
#    che nessuno puo' far diventare verde, cioe' `LEZIONI.md` §1.49 — rumore, e
#    non prudenza.  ⇒ Chi lo vede due volte spegne il controllo.
#
# ⭐ I due soli momenti in cui quel file e' garantito intatto sono **PRIMA**
#   della certificazione e **DOPO** che e' tornata (il guasto vive dentro
#   `04-b23-guasti.py` e viene rimesso a posto in un `finally`), ed e'
#   esattamente li' che C10 gira: due chiamate, e in mezzo nessuna.
# ===========================================================================
C10="$RADICE/banchi/11-scatole/11-c10-le-copie-gemelle.py"
GEMELLO_NON_GUARDATO=0

# ⛔ Una funzione sola, e non due chiamate ricopiate: tradurre gli esiti di C10
#    in quelli di B23 e' una REGOLA, e una regola scritta in due posti e'
#    precisamente il difetto che questo blocco e' stato riscritto per togliere.
#    $1 = a che punto del giro siamo, per chi legge il registro.
chiama_c10() {
	local e
	if [ ! -f "$C10" ]; then
		# ⛔ La maglia che non c'e' NON e' un verde: e' un «non ho potuto
		#    guardare».  ⚠ Il modo piu' silenzioso di spegnere un controllo e'
		#    spostare il file che lo esegue.
		echo "   ${GIALLO}⛔ la maglia C10 non c'e': $C10${GRIGIO}"
		GEMELLO_NON_GUARDATO=1
		return 3
	fi
	# ⚠ `--radice` esplicita: C10 da sola chiederebbe a git dove sta il
	#   deposito, e i due banchi devono parlare dello STESSO deposito invece di
	#   dedurlo ciascuno per conto suo.
	python3 "$C10" --radice "$RADICE" 2>&1 | sed 's/^/   /'
	e=${PIPESTATUS[0]}
	case "$e" in
	0)	return 0 ;;
	1)	return 1 ;;
	3)	# ⛔ §4.5 della fase 11: il `3` **non e' un rosso**.  «Non ho trovato
		#    differenze» e «non ho potuto guardare» hanno la stessa faccia, e
		#    B23 non deve prendere il secondo per il primo.
		echo "   ${GIALLO}⚠ $1: non ho potuto guardare il gemello (esito 3)${GRIGIO}"
		echo "      ⛔ non e' un rosso, e non si rimette in coda (§4.5) — ma il"
		echo "        verdetto finale di B23 non potra' dire «il gemello combacia»"
		GEMELLO_NON_GUARDATO=1
		return 3 ;;
	*)	echo "   ${ROSSO}⛔ $1: C10 non ha potuto girare affatto (uscita $e)${GRIGIO}"
		GEMELLO_NON_GUARDATO=1
		return 2 ;;
	esac
}

echo "== ⛔ 1. IL GEMELLO — \`src/\` e \`banchi/rcp/\` devono combaciare"
echo "      (lo giudica C10, che l'elenco lo LEGGE da \`src/Makefile\`; lo stesso"
echo "       elenco ferma anche la costruzione, bersaglio \`impronte\`)"
chiama_c10 "prima della certificazione"
case "$?" in
0)	;;
1)	echo "   ${ROSSO}⛔ ci si ferma qui: un gemello mezzo ferma TUTTI gli anelli${GRIGIO}"
	echo "      ⚠ e il verde di B23 non direbbe niente sul prodotto: girerebbe su"
	echo "        un protocollo che non e' quello di \`src/\`"
	exit 2 ;;
3)	# ⛔ Si PROSEGUE: un `3` non ferma il giro, perche' non e' un giudizio
	#    negativo sul canale di input — che e' l'incognita di questo banco.
	#    ⭐ Il conto si tira alla fine, dove il verdetto viene degradato a 3.
	: ;;
*)	echo "   ${ROSSO}⛔ ci si ferma qui: senza C10 non so nemmeno se il banco e"
	echo "      il prodotto parlino lo stesso protocollo${GRIGIO}"
	exit 2 ;;
esac

if [ "$CERTIFICA" -eq 1 ]; then
	echo
	echo "== ⛔ 2. LA CERTIFICAZIONE — il banco sa vedere il difetto?"
	# ⛔ QUANTI SONO NON STA SCRITTO QUI: il numero lo stampa `04-b23-guasti.py`
	#    dal proprio catalogo.  ⚠ Qui c'era «dodici», ed erano gia' sedici — la
	#    forma esatta del rilievo R7.14: un numero scritto a mano e' il numero che
	#    nessuno ricalcola.
	echo "      ⚠ i guasti del catalogo, innestati in \`banchi/rcp/rcp.c\` uno per"
	echo "        giro e rimessi a posto in un \`finally\`.  Dura qualche minuto."
	python3 "$QUI/04-b23-guasti.py" --uscita "$USCITA" || GUASTI=$((GUASTI + 1))
	# ⛔ E si RIGUARDA il gemello: la certificazione scrive su quel file, e un
	#    ripristino mancato lo scopre questo controllo, non il prossimo che
	#    compila.
	#
	# ⭐ Qui c'era un `diff -q` sul solo `rcp.c`, e C10 e' piu' severa: «la
	#   certificazione tocca un file solo» e' un'affermazione sul catalogo dei
	#   guasti, ⛔ non un fatto verificato — e il giorno in cui un guasto nuovo
	#   toccasse `rcp.h`, quel `diff` non se ne sarebbe accorto.
	# ⚠ E il momento e' quello GIUSTO: `04-b23-guasti.py` e' gia' tornato, cioe'
	#   il suo `finally` ha gia' rimesso a posto il file.  ⇒ Un rosso QUI e' un
	#   rosso vero e non voluto: e' il ripristino che non ha funzionato.
	echo
	echo "   ⛔ e il gemello e' tornato a posto dopo la certificazione?"
	chiama_c10 "dopo la certificazione"
	case "$?" in
	0)	echo "   ${VERDE}⭐ si': il ripristino ha funzionato${GRIGIO}" ;;
	1)	echo "   ${ROSSO}⛔⛔ il gemello NON e' tornato a posto dopo la certificazione${GRIGIO}"
		echo "      ⇒ il deposito e' rimasto GUASTO: si ripara PRIMA di andare avanti,"
		echo "        o il prossimo che compila trovera' un difetto che sembra del prodotto"
		GUASTI=$((GUASTI + 1)) ;;
	*)	# ⛔ 3 e 2 non sono rossi: C10 lo ha gia' detto, e il conto si tira
		#    alla fine.  ⚠ Contarli qui come guasti vorrebbe dire dare a B23
		#    un rosso per un difetto che non e' del canale di input.
		: ;;
	esac
else
	echo
	echo "== ⚠ 2. CERTIFICAZIONE SALTATA (--senza-certificazione)"
	echo "      ⛔ Il verde che segue vale meno: nessuno ha verificato che questo"
	echo "        banco sappia diventare rosso.  Non si chiude una fase cosi'."
fi

echo
echo "== ⭐ 3. IL GIRO VERO"
python3 "$QUI/04-b23-filo-input.py" --uscita "$USCITA" || GUASTI=$((GUASTI + 1))

echo
if [ "$GUASTI" -ne 0 ]; then
	echo "   ${ROSSO}⛔ B23 NON passa${GRIGIO}"
	exit 1
fi
if [ "$GEMELLO_NON_GUARDATO" -ne 0 ]; then
	# ⛔ §4.5 della fase 11: il `3` e' un VERDETTO — «ho misurato, e un pezzo
	#    non ha potuto parlare» — non un rosso, e non un giro da rifare.
	# ⚠ Ma B23 non puo' nemmeno stampare «passa» come se il gemello fosse stato
	#   verificato: sarebbe un verde che non ha guardato niente (`LEZIONI.md`
	#   §1.47), che e' esattamente il difetto per cui questo banco e' stato
	#   riscritto.  ⇒ Le prove sono passate, e lo si dice; il gemello no, e si
	#   dice anche quello.
	echo "   ${GIALLO}⛔ B23: esito 3 — le prove sono passate, ma NON ho potuto"
	echo "      guardare il gemello${GRIGIO}"
	echo "      ⇒ finche' e' cosi', questo verde vale sul BANCO e ⛔ non sul"
	echo "        prodotto: nessuno ha verificato che i due protocolli siano uno"
	echo "   la traccia e il verdetto: $USCITA"
	exit 3
fi
if [ "$CERTIFICA" -eq 1 ]; then
	echo "   ${VERDE}⭐ B23 passa, ed e' certificato${GRIGIO}"
else
	# ⚠ Qui c'era «ed e' certificato» anche con `--senza-certificazione`: la
	#   riga diceva piu' di quel che era stato guardato, ed e' lo stesso genere
	#   di difetto dell'elenco inchiodato di sopra (`LEZIONI.md` §1.47).
	echo "   ${VERDE}⭐ B23 passa${GRIGIO} — ⚠ ma NON e' certificato: la"
	echo "      certificazione e' stata saltata, e nessuno ha verificato che"
	echo "      questo banco sappia ancora diventare rosso"
fi
echo "   la traccia e il verdetto: $USCITA"
exit 0
