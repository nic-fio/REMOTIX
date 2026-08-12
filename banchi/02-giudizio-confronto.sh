#!/bin/bash
#
# 02-giudizio-confronto.sh — F2.6 (a): IL BANCO DEL CONFRONTO DEI PIXEL.
#
#   bash banchi/02-giudizio-confronto.sh sano        un giro sano sulla catena finta
#   bash banchi/02-giudizio-confronto.sh certifica   ⛔ sano → i nove guasti → risanato
#   bash banchi/02-giudizio-confronto.sh certifica riga    un guasto solo
#   bash banchi/02-giudizio-confronto.sh giudica --cattura … --pagina …
#                                                   il giro VERO, sui file di F2.2/F2.5
#
# ⚠ GIRA SU CHUWI, e non tocca NIC-OS.  Non apre nessuna porta: qui non c'e'
#   filo, ci sono file.  (La porta 7516 e' della sonda, `02-giudizio-telefono.sh`.)
#
# ---------------------------------------------------------------------------
# ⛔ PERCHE' ESISTE, E QUALE MISURA SBAGLIATA IMPEDISCE
#
# `PIANO.md` fase 2 chiede *«il fotogramma decodificato confrontato con quello
# catturato.  Non "il programma non e' crollato": **i pixel**»*.  La misura
# sbagliata che questo banco impedisce e' quella che verrebbe naturale:
#
#     «ho aperto la pagina, si vede il desktop, la fase e' chiusa»
#
# ⛔ Sotto quella frase ci stanno **nove guasti diversi**, e quattro di essi
#    non muovono il PSNR di un decimo di dB.  L'elenco per esteso, con chi li
#    prende, sta in `02-giudizio-guasti.py --elenco`, e questo banco lo
#    innesta uno per uno.
#
# ---------------------------------------------------------------------------
# ⛔ LA CATENA FINTA, DICHIARATA — e che cosa questo banco NON misura
#
# Alla data in cui e' scritto (12 agosto 2026) F2.2 (la cattura), F2.3 (la
# codifica) e F2.5 (la pagina) **non esistono ancora**: e' il giro del banco
# prima del prodotto (`MANDATO-12-agosto-fase2.md` §1).  Quindi in modo `sano`
# e `certifica` la catena e' finta, e lo si scrive invece di lasciarlo capire:
#
#     cattura       = la MIRA di `02-giudizio-mira.py` (invece del buffer di Mutter)
#     flusso        = `libx265` Main10, tutto-intra          (invece di `hevc_vaapi`)
#     riferimento   = `ffmpeg` che decodifica lo stesso flusso a 16 bit
#     pagina        = lo stesso flusso decodificato a **RGB 8 bit**
#                     (invece della tela della pagina riletta con getImageData)
#
# ⛔ Da cui, dichiarato: **questo giro certifica LO STRUMENTO, non il prodotto.**
#    Nessun numero che esce di qui e' una misura della fase 2.  Il modo
#    `giudica` e' quello che punta il metro sui file veri, e quel giorno la
#    riga della catena qui sopra si riscrive con i nomi veri.
#
# ⚠ E c'e' una cosa che la catena finta fa **meglio** del vero, e va detta:
#   il «riferimento» e la «pagina» qui vengono dallo stesso decodificatore.
#   Nel giro vero vengono da due decodificatori diversi — ffmpeg e il browser
#   — ed e' proprio li' che il confronto vale (`PIANO.md` §0.4: due programmi
#   scritti dalla stessa mano che vanno d'accordo non confermano niente).
#   Sulla catena finta M1 e' quasi regalato; sul vero e' lo strumento centrale.
#
# ---------------------------------------------------------------------------
# ⛔ IL CONTROLLO POSITIVO, E SONO TRE — in coda a OGNI esecuzione
#
#   1. il metro se ne fa uno da solo, dentro (`C2`): a ogni giro si innesta in
#      memoria uno scorrimento di una riga, un blocco azzerato e i piani
#      scambiati, e se non li boccia si dichiara **rotto** invece di dare un
#      verdetto.  Uno strumento certificato ieri, su file cambiati stanotte,
#      oggi non e' certificato;
#   2. ⛔ **il flusso e' davvero Main10 a 10 bit?**  Si legge con `ffprobe`, e
#      se fosse a 8 bit tutta la certificazione di M7 varrebbe zero: si
#      starebbe misurando la profondita' di un flusso che non ce l'ha, e il
#      verde sarebbe della forma piu' vuota che ci sia;
#   3. ⛔ **il canale di lettura**: ogni ingresso del metro viene stampato con
#      dimensione e impronta, e due ingressi con la stessa impronta fermano il
#      giro.  Confrontare un file con se stesso da' PSNR infinito — ed e' un
#      errore che si fa da soli, scrivendo due volte lo stesso nome sulla riga
#      di comando.  E' la forma del controllo n. 4 di `01-s1b-eccezione.sh`:
#      dimostrare che «NO» vuol dire «non e' arrivato» e non «non ho potuto
#      guardare».
#
# ---------------------------------------------------------------------------
# ⛔ ZERO E FALLIMENTO SONO DUE COSE DIVERSE (`REVIEWER.md` §1 punto 4)
#
# Il metro ha **quattro** stati d'uscita, non due: 0 promosso · 1 bocciato ·
# 2 NON MISURATO · 3 metro rotto.  Questo script li tiene distinti fino in
# fondo, e la certificazione di un guasto pretende **1**: un guasto che facesse
# uscire 2 (ingresso mancante) o 3 (metro rotto) **non certifica niente**, ed e'
# la trappola n.1 di `01-b12-guasti.py` — il rosso per la ragione sbagliata.
# ⛔ E niente `2>/dev/null` in tutto il file: la richiesta di parola d'ordine e
#    l'errore vivono la' dentro.
# ---------------------------------------------------------------------------
set -uo pipefail

QUI=$(cd "$(dirname "$0")" && pwd)
LARG=${LARG:-1920}
ALT=${ALT:-1080}
# ⛔ QP 40 NON e' una scelta di qualita': e' la scelta che mette la perdita del
#    codificatore abbastanza SOPRA il rumore della tela a 8 bit perche' M2
#    abbia senso.  Misurato il 12 agosto 2026 sulla mira: a QP 20 il
#    riferimento dista 60,4 dB dalla cattura e la tela ne introduce 55,6 — la
#    codifica perde MENO della tela, e M2 si dichiara non applicabile.  A QP 40
#    i due numeri sono 42,2 e 56,8: 14,5 dB di margine, e M2 misura il client.
QP=${QP:-40}
LAV=${LAV:-/tmp/remotix-f26-$USER}
ESITI=$QUI/02-giudizio-esiti.jsonl

VERDE='\033[1;32m'; ROSSO='\033[1;31m'; GIALLO='\033[1;33m'; GRIGIO='\033[0m'
log()  { printf '\n\033[1m== %s\033[0m\n' "$*"; }
ok()   { printf "    ${VERDE}OK${GRIGIO}  %s\n" "$*"; }
ko()   { printf "    ${ROSSO}NO${GRIGIO}  %s\n" "$*"; }
inf()  { printf '    --  %s\n' "$*"; }

# ---------------------------------------------------------------------------
# La catena finta: mira → flusso → riferimento → pagina
# ---------------------------------------------------------------------------
prepara()
{
	local giro=$1
	mkdir -p "$LAV"
	python3 "$QUI/02-giudizio-mira.py" --giro "$giro" --cartella "$LAV" \
		--larghezza "$LARG" --altezza "$ALT" >/dev/null
	local stato=$?
	if [ $stato -ne 0 ]; then
		ko "la mira del giro «$giro» non e' stata costruita (stato $stato)"
		return 2
	fi

	# ⛔ `-color_range pc` e il VUI: si dichiara la gamma PIENA sia in ingresso
	#    sia in uscita.  Senza, il decodificatore INDOVINA, e l'indovinato
	#    sbagliato e' esattamente il guasto «gamma» che questo banco innesta —
	#    cioe' si starebbe certificando M5 contro un difetto che il banco si
	#    e' fatto da solo.  Il VUI e' anche la cucitura che F2.3 deve chiudere.
	ffmpeg -hide_banner -loglevel error -y \
		-f rawvideo -pix_fmt rgb48le -s "${LARG}x${ALT}" -r 25 \
		-i "$LAV/mira-$giro.rgb48" -frames:v 1 \
		-c:v libx265 -pix_fmt yuv420p10le -color_range pc \
		-colorspace bt709 -color_primaries bt709 -color_trc bt709 \
		-x265-params "keyint=1:qp=$QP:annexb=1:log-level=warning:range=full:colorprim=bt709:transfer=bt709:colormatrix=bt709:info=0" \
		-f hevc "$LAV/flusso-$giro.h265"
	if [ $? -ne 0 ] || [ ! -s "$LAV/flusso-$giro.h265" ]; then
		ko "la codifica non ha prodotto un flusso"
		return 2
	fi

	ffmpeg -hide_banner -loglevel error -y -f hevc -i "$LAV/flusso-$giro.h265" \
		-frames:v 1 -vf "scale=in_range=full:out_range=full" \
		-pix_fmt rgb48le -f rawvideo "$LAV/rif-$giro.rgb48"   || return 2
	ffmpeg -hide_banner -loglevel error -y -f hevc -i "$LAV/flusso-$giro.h265" \
		-frames:v 1 -vf "scale=in_range=full:out_range=full" \
		-pix_fmt rgb24 -f rawvideo "$LAV/pag-$giro.rgb24"     || return 2
	# ⛔ E il piano Y a 10 bit COSI' COM'E' USCITO dal decodificatore, senza
	#    passare per l'RGB: M7 legge i due bit bassi, e la conversione di
	#    colore li rimescola.  Chiedere la profondita' a un file RGB e' come
	#    chiedere l'ora a un orologio gia' riportato indietro.
	ffmpeg -hide_banner -loglevel error -y -f hevc -i "$LAV/flusso-$giro.h265" \
		-frames:v 1 -pix_fmt yuv420p10le -f rawvideo "$LAV/rif-$giro.yuv" || return 2

	# ⛔ LA DICHIARAZIONE DEL COLORE — cucitura di F2.3, e questo banco la
	#    scrive con quel che ha CHIESTO a ffmpeg, riga per riga.  Dichiarare
	#    quel che si e' chiesto non prova che sia stato fatto: quello lo
	#    verifica M5 sui pixel (`LEZIONI.md` §1.11 punto 2).
	# ⚠ La cattura e' **RGB e non ha matrice** — e' quel che F2.2 ha misurato
	#   su Mutter (BGRx).  La matrice la sceglie chi converte, cioe' la
	#   codifica, e chi legge deve leggere con la stessa.
	cat > "$LAV/colore-$giro.json" <<'JSON'
{
  "cattura":     {"spazio": "RGB", "matrice": "nessuna", "gamma": "piena"},
  "codifica":    {"matrice": "bt709", "gamma": "piena", "primarie": "bt709"},
  "riferimento": {"matrice": "bt709", "gamma": "piena", "primarie": "bt709"},
  "pagina":      {"matrice": "bt709", "gamma": "piena", "primarie": "bt709"}
}
JSON
	# ⛔ E LA DICHIARAZIONE DEL FILO — cucitura di F2.4.  Sulla catena finta
	#    non c'e' filo: il FIN e' vero per costruzione e nessun RESET esiste.
	#    Si scrive lo stesso, perche' un campo assente e un campo falso non
	#    devono avere lo stesso aspetto.
	cat > "$LAV/identita-$giro.json" <<JSON
{"giro": null, "fin_ricevuto": true, "reset_ricevuto": false, "dipinto": true,
 "nota": "catena finta: nessun filo, il FIN e' vero per costruzione"}
JSON
	return 0
}

# ⛔ CONTROLLO POSITIVO 2 — il flusso e' davvero a 10 bit?
controllo_flusso()
{
	local f=$1
	local px prof
	px=$(ffprobe -hide_banner -v error -select_streams v:0 \
		-show_entries stream=pix_fmt -of csv=p=0 "$f")
	prof=$(ffprobe -hide_banner -v error -select_streams v:0 \
		-show_entries stream=profile -of csv=p=0 "$f")
	if [ -z "$px" ]; then
		ko "ffprobe non ha detto NIENTE sul formato dei pixel."
		ko "   ⛔ Vuoto e «a 8 bit» hanno lo stesso aspetto: qui ci si ferma."
		return 2
	fi
	case "$px" in
	*10le|*10be)
		ok "il flusso e' $px, profilo «$prof» — M7 ha qualcosa da misurare" ;;
	*)
		ko "il flusso e' $px (profilo «$prof»), NON e' a 10 bit."
		ko "   ⛔ Certificare M7 su un flusso a 8 bit vorrebbe dire misurare la"
		ko "      profondita' di una cosa che non ce l'ha: verde vuoto."
		return 1 ;;
	esac
	return 0
}

# ---------------------------------------------------------------------------
# ⛔⭐ PERCHE' QUI NON C'E' PIU' UNA `metro()` CHE INOLTRA `"$@"` — lacuna L3,
#     curata il 12 agosto 2026.
#
# C'era, e faceva una riga sola: `python3 "$QUI/02-giudizio-metro.py" "$@"`.
# Comoda da scrivere, e ⛔ **invisibile a ogni controllo statico**: il metro
# pretende `--scena --cattura --riferimento --pagina`, e nessun file del
# deposito diceva che cosa ci fosse dentro quel `"$@"`.  `01-b0-chiamate.py`
# la dichiarava IGNOTA — non un rosso e non un verde — cioe' **fuori
# sorveglianza**, ed e' la cucitura gia' pagata due volte:
#
#   `[M]` 10 agosto 2026 · `01-b2-sonda-trasporto.py` guadagna `--bersaglio`
#         obbligatorio e `01-b6-lancia.sh` resta indietro: **B6 rosso**, di un
#         banco sano.
#   `[M]` 11 agosto 2026 · la stessa cosa su B7, da `01-b12-lancia.sh`.
#
# ⇒ Ogni chiamata al metro, in questo file, e' adesso una **riga di comando
#   piatta**: il nome di ogni opzione e' scritto per esteso, e le variabili
#   stanno solo dove argparse aspetta un VALORE.  Se domani il metro guadagna
#   un obbligatorio, il controllo lo vede da qui invece di lasciarlo scoprire
#   a un rosso.
#
# ⚠ E il ramo `giudica` — quello che riceve gli argomenti dall'utente — non li
#   inoltra piu' alla cieca: li legge lui, uno per uno (`leggi_opzioni_giudica`),
#   e i quattro obbligatori li **pretende qui**, con un messaggio che dice
#   quale manca.  Prima quel controllo esisteva solo dentro argparse, e da
#   fuori aveva la faccia di «il metro e' rotto».
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
giro_sano()
{
	local etichetta=${1:-sano}
	log "1. La catena finta — mira → libx265 Main10 → riferimento → pagina"
	prepara g0 || return 2
	prepara g1 || return 2
	inf "scena: mira-remotix-f2.6 ${LARG}x${ALT}, QP $QP, rumore seminato sul giro"
	inf "il giro g0 serve come CATTURA PRECEDENTE: senza, M6 non esiste"

	log "2. ⛔ Controllo positivo — il flusso e' davvero Main10 a 10 bit?"
	controllo_flusso "$LAV/flusso-g1.h265" || return 2

	log "3. Il metro, sul giro sano"
	python3 "$QUI/02-giudizio-metro.py" --scena "$LAV/mira-g1.json" \
		--cattura "$LAV/mira-g1.rgb48" \
		--riferimento "$LAV/rif-g1.rgb48" \
		--pagina "$LAV/pag-g1.rgb24" \
		--cattura-precedente "$LAV/mira-g0.rgb48" \
		--riferimento-10 "$LAV/rif-g1.yuv" \
		--colore "$LAV/colore-g1.json" \
		--identita-pagina "$LAV/identita-g1.json" \
		--giro "$etichetta" --esiti "$ESITI"
	return $?
}

# ---------------------------------------------------------------------------
# ⛔ LA CERTIFICAZIONE: sano N → guasto M → risanato N
# ---------------------------------------------------------------------------
certifica()
{
	local solo=${1:-}
	local elenco
	elenco=$(python3 - <<'PY'
import json, importlib.util, os, sys
spec = importlib.util.spec_from_file_location(
    "g", os.path.join(os.environ["QUI"], "02-giudizio-guasti.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
print(" ".join(m.GUASTI.keys()))
PY
)
	[ -z "$elenco" ] && { ko "l'elenco dei guasti non si legge"; return 3; }
	[ -n "$solo" ] && elenco=$solo

	log "0. Il giro SANO di partenza — ⛔ «e' diventato rosso» non vuol dire"
	log "   niente se non era verde prima"
	giro_sano "certifica-sano-prima"
	local s=$?
	if [ $s -ne 0 ]; then
		ko "il giro sano non e' PROMOSSO (stato $s): la certificazione si ferma."
		ko "   ⛔ Un metro gia' rosso certificherebbe qualunque guasto, e per la"
		ko "      ragione sbagliata — trappola n.1 di 01-b12-guasti.py."
		return 3
	fi
	ok "sano = PROMOSSO (stato 0)"

	local passati=0 falliti=0 righe=""
	for g in $elenco; do
		log "GUASTO «$g»"
		python3 "$QUI/02-giudizio-guasti.py" --elenco | grep -A2 "^.\[1m$g " | sed 's/^/    /'

		local CAT="$LAV/mira-g1.rgb48"
		local PAG="$LAV/pag-g1.rgb24"
		local RIF10="$LAV/rif-g1.yuv"
		local COL="$LAV/colore-g1.json"
		local IDE="$LAV/identita-g1.json"
		local out="$LAV/guasto-$g.rgb24"

		case "$g" in
		nero-doppio)
			# ⛔ il guasto va innestato su TUTT'E DUE: e' il caso in cui la
			#    somiglianza e' PERFETTA e solo M-V puo' dire di no.
			python3 "$QUI/02-giudizio-guasti.py" --applica nero \
				--dentro "$PAG" --fuori "$out" --scena "$LAV/mira-g1.json" || return 3
			python3 "$QUI/02-giudizio-guasti.py" --applica nero \
				--dentro "$CAT" --fuori "$LAV/guasto-cattura-nera.rgb48" \
				--scena "$LAV/mira-g1.json" || return 3
			CAT="$LAV/guasto-cattura-nera.rgb48"
			;;
		matrice)
			# ⛔ il guasto sta nella DICHIARAZIONE, non nei pixel
			sed 's/"pagina":      {"matrice": "bt709"/"pagina":      {"matrice": "bt601"/' \
				"$LAV/colore-g1.json" > "$LAV/colore-guasto.json" || return 3
			COL="$LAV/colore-guasto.json"
			cp "$PAG" "$out"
			;;
		dopo-reset)
			# ⛔ i pixel sono PERFETTI: e' l'identita' del fotogramma a essere
			#    sbagliata, ed e' invisibile a M0..M7 per costruzione
			printf '%s\n' '{"giro": null, "fin_ricevuto": true, "reset_ricevuto": true, "dipinto": true}' \
				> "$LAV/identita-guasto.json" || return 3
			IDE="$LAV/identita-guasto.json"
			cp "$PAG" "$out"
			;;
		precedente)
			python3 "$QUI/02-giudizio-guasti.py" --applica precedente \
				--dentro "$PAG" --altro "$LAV/pag-g0.rgb24" --fuori "$out" \
				--scena "$LAV/mira-g1.json" || return 3
			;;
		otto-bit)
			# ⛔ La profondita' non vive sulla tela a 8 bit: il troncamento si
			#    innesta sul RIFERIMENTO A 10 BIT, che e' il solo posto dove la
			#    domanda ha ancora una risposta.  Innestarlo sulla pagina e
			#    aspettarsi che il metro se ne accorga sarebbe chiedere allo
			#    strumento di vedere una cosa che a 8 bit **non c'e' piu'**.
			python3 "$QUI/02-giudizio-guasti.py" --applica otto-bit \
				--dentro "$RIF10" --fuori "$LAV/guasto-rif10-8bit.yuv" \
				--scena "$LAV/mira-g1.json" || return 3
			RIF10="$LAV/guasto-rif10-8bit.yuv"
			cp "$PAG" "$out"
			;;
		*)
			python3 "$QUI/02-giudizio-guasti.py" --applica "$g" \
				--dentro "$PAG" --fuori "$out" --scena "$LAV/mira-g1.json" || return 3
			;;
		esac

		python3 "$QUI/02-giudizio-metro.py" --scena "$LAV/mira-g1.json" --cattura "$CAT" \
			--riferimento "$LAV/rif-g1.rgb48" --pagina "$out" \
			--cattura-precedente "$LAV/mira-g0.rgb48" \
			--riferimento-10 "$RIF10" --colore "$COL" --identita-pagina "$IDE" \
			--giro "certifica-guasto-$g" --esiti "$ESITI"
		local sg=$?

		# ⛔ L'atteso non e' «diverso da 0»: e' **1**, e con la MARCA giusta.
		# ⛔ L'atteso di «nero-doppio» e' **2**, non 1, ed e' la cosa piu'
		#    importante di questa tabella: quando anche la CATTURA e' nera il
		#    metro non ha piu' un ingresso da giudicare, e deve dire «non ho
		#    potuto guardare» — non «bocciato».  Un metro che bocciasse
		#    starebbe accusando il client di un difetto della SESSIONE.
		#    Tutti gli altri, pagina morta con cattura viva compresa, sono 1.
		local atteso=1
		local a2
		a2=$(python3 -c "import importlib.util,os;s=importlib.util.spec_from_file_location('g',os.environ['QUI']+'/02-giudizio-guasti.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(m.GUASTI['$g'].get('stato',1))")
		[ -n "$a2" ] && atteso=$a2
		if [ $sg -eq $atteso ]; then
			local marca
			marca=$(python3 - "$ESITI" "$g" <<'PY'
import json,sys
ultima=None
for r in open(sys.argv[1]):
    d=json.loads(r)
    if d.get("giro")=="certifica-guasto-"+sys.argv[2]: ultima=d
if not ultima: print("SENZA-RIGA"); raise SystemExit
b=ultima.get("bocciati") or []
if ultima.get("esito")=="non-misurato": b=["M-V/"+str(ultima.get("ragione"))[:40]]
print(",".join(b) or "NESSUNO")
PY
)
			ok "stato $sg (atteso $atteso) · marca: $marca"
			passati=$((passati+1))
			righe="$righe\n    $g: stato $sg, $marca"
		else
			ko "stato $sg, atteso $atteso — ⛔ NON CERTIFICA."
			case $sg in
			0) ko "   il metro ha PROMOSSO un guasto: e' un buco del metro" ;;
			2) ko "   «non misurato» non e' «bocciato»: manca un ingresso" ;;
			3) ko "   il metro si e' dichiarato rotto: rosso della ragione sbagliata" ;;
			esac
			falliti=$((falliti+1))
			righe="$righe\n    $g: ⛔ stato $sg invece di $atteso"
		fi
	done

	log "RISANATO — ⛔ il terzo giro, quello che ci si dimentica"
	inf "senza, «il metro vede il guasto» e «il metro e' rimasto rotto» hanno"
	inf "lo stesso aspetto"
	giro_sano "certifica-sano-dopo"
	s=$?
	if [ $s -ne 0 ]; then
		ko "il metro NON e' tornato verde (stato $s): la certificazione non vale"
		return 3
	fi
	ok "risanato = PROMOSSO (stato 0)"

	log "IL CONTO"
	printf "$righe\n"
	if [ $falliti -eq 0 ]; then
		ok "$passati guasti su $((passati+falliti)): il metro li boccia tutti,"
		ok "   e sano → guasto → risanato ha chiuso il cerchio."
		return 0
	fi
	ko "$falliti guasti su $((passati+falliti)) NON certificano il metro"
	return 1
}

# ---------------------------------------------------------------------------
# ⛔ IL GIRO VERO — e qui gli argomenti arrivano da FUORI.
#
# Li si legge uno per uno e si ricostruisce una riga di comando **piatta**,
# invece di inoltrare `"$@"`.  Costa venti righe e compra due cose:
#
#   1. i quattro obbligatori li pretende QUESTO file, con il nome di quello che
#      manca.  Prima li pretendeva solo argparse, e da fuori il rifiuto aveva
#      la faccia di «il metro e' rotto» — che e' la trappola n.1 di
#      `01-b12-guasti.py`, il rosso per la ragione sbagliata;
#   2. la chiamata torna **giudicabile** da `01-b0-chiamate.py`: il nome di
#      ogni opzione e' letterale in questo file, e le variabili stanno solo
#      dove argparse aspetta un valore.
#
# ⚠ E un'opzione che il metro non conosce si ferma qui, non la' dentro: era il
#   `--sorgente` dell'11 agosto 2026, che non esisteva piu' e che nessuno
#   guardava.
# ⛔ Un valore MANCANTE e un valore VUOTO non sono la stessa cosa: `--pagina`
#   senza niente dietro non diventa `--pagina ""`, si ferma.  E' la forma E8
#   applicata alla riga di comando.
# ---------------------------------------------------------------------------
giudica_veri()
{
	local G_SCENA= G_CATTURA= G_RIFERIMENTO= G_PAGINA=
	local G_PRECEDENTE= G_RIF10= G_PROFONDITA= G_COLORE= G_IDENTITA=
	local G_SCENA_NOME=mira-remotix-f2.6
	local G_GIRO=giudica-$(date +%H%M%S)
	local G_FRESCHEZZA=si manca=0

	while [ $# -gt 0 ]; do
		if [ "$1" = "--senza-freschezza" ]; then
			G_FRESCHEZZA=no; shift; continue
		fi
		case "$1" in
		--*) ;;
		*) ko "⛔ argomento senza opzione davanti: «$1»"; return 2;;
		esac
		if [ $# -lt 2 ]; then
			ko "⛔ l'opzione «$1» e' rimasta senza valore."
			ko "   ⚠ e un valore mancante non e' un valore vuoto: qui ci si ferma"
			ko "     invece di passare al metro una stringa che nessuno ha scritto."
			return 2
		fi
		case "$1" in
		--scena)                  G_SCENA=$2;;
		--cattura)                G_CATTURA=$2;;
		--riferimento)            G_RIFERIMENTO=$2;;
		--pagina)                 G_PAGINA=$2;;
		--cattura-precedente)     G_PRECEDENTE=$2;;
		--riferimento-10)         G_RIF10=$2;;
		--profondita-dispositivo) G_PROFONDITA=$2;;
		--colore)                 G_COLORE=$2;;
		--identita-pagina)        G_IDENTITA=$2;;
		--giro)                   G_GIRO=$2;;
		--scena-nome)             G_SCENA_NOME=$2;;
		*)
			ko "⛔ opzione che il metro non conosce: «$1»"
			inf "ammesse: --scena --cattura --riferimento --pagina"
			inf "         --cattura-precedente --riferimento-10"
			inf "         --profondita-dispositivo --colore --identita-pagina"
			inf "         --giro --scena-nome --senza-freschezza"
			return 2;;
		esac
		shift 2
	done

	# ⛔ I QUATTRO CHE IL METRO PRETENDE, pretesi qui e per nome.
	[ -n "$G_SCENA" ]       || { ko "⛔ manca --scena (il JSON della mira)"; manca=1; }
	[ -n "$G_CATTURA" ]     || { ko "⛔ manca --cattura"; manca=1; }
	[ -n "$G_RIFERIMENTO" ] || { ko "⛔ manca --riferimento"; manca=1; }
	[ -n "$G_PAGINA" ]      || { ko "⛔ manca --pagina"; manca=1; }
	if [ "$manca" -ne 0 ]; then
		ko "   ⛔ stato 2: NON MISURATO.  Non e' un bocciato e non e' un metro"
		ko "      rotto: e' una riga di comando incompleta, e si dice cosi'."
		return 2
	fi

	# ⚠ Le facoltative si passano SEMPRE, anche vuote: `02-giudizio-metro.py`
	#   legge una stringa vuota come «non passato» e lo stampa nel canale di
	#   lettura (C1), cosi' un ingresso che non c'e' **si vede** invece di
	#   sparire dalla riga di comando.
	# ⚠ Le due rese sono la stessa riga meno un interruttore: `--senza-freschezza`
	#   non ha un valore da portare, e una variabile che lo contenesse tornerebbe
	#   a essere il buco che questa funzione chiude.
	if [ "$G_FRESCHEZZA" = no ]; then
		python3 "$QUI/02-giudizio-metro.py" --esiti "$ESITI" \
			--scena "$G_SCENA" --cattura "$G_CATTURA" \
			--riferimento "$G_RIFERIMENTO" --pagina "$G_PAGINA" \
			--cattura-precedente "$G_PRECEDENTE" \
			--riferimento-10 "$G_RIF10" \
			--profondita-dispositivo "$G_PROFONDITA" \
			--colore "$G_COLORE" --identita-pagina "$G_IDENTITA" \
			--giro "$G_GIRO" --scena-nome "$G_SCENA_NOME" \
			--senza-freschezza
		return $?
	fi
	python3 "$QUI/02-giudizio-metro.py" --esiti "$ESITI" \
		--scena "$G_SCENA" --cattura "$G_CATTURA" \
		--riferimento "$G_RIFERIMENTO" --pagina "$G_PAGINA" \
		--cattura-precedente "$G_PRECEDENTE" \
		--riferimento-10 "$G_RIF10" \
		--profondita-dispositivo "$G_PROFONDITA" \
		--colore "$G_COLORE" --identita-pagina "$G_IDENTITA" \
		--giro "$G_GIRO" --scena-nome "$G_SCENA_NOME"
	return $?
}

# ---------------------------------------------------------------------------
export QUI
case "${1:-sano}" in
sano)      shift; giro_sano "sano-$(date +%H%M%S)"; s=$?;;
certifica) shift; certifica "${1:-}"; s=$?;;
giudica)   shift
           log "Il giro VERO — il metro sui file di F2.2, F2.3 e F2.5"
           inf "⚠ qui la catena non e' finta: gli argomenti li passa chi chiama,"
           inf "  e questo banco li legge uno per uno invece di inoltrarli"
           giudica_veri "$@"; s=$?;;
elenco)    python3 "$QUI/02-giudizio-guasti.py" --elenco; s=$?;;
catalogo)  python3 "$QUI/02-giudizio-guasti.py" --riga-catalogo; s=$?;;
*)         printf 'uso: %s {sano|certifica [guasto]|giudica …|elenco|catalogo}\n' "$0"; s=2;;
esac

case $s in
0) printf "\n${VERDE}== stato 0 — promosso${GRIGIO}\n" ;;
1) printf "\n${ROSSO}== stato 1 — bocciato${GRIGIO}\n" ;;
2) printf "\n${GIALLO}== stato 2 — NON MISURATO (⛔ non e' un promosso)${GRIGIO}\n" ;;
3) printf "\n${ROSSO}== stato 3 — il metro si e' dichiarato rotto${GRIGIO}\n" ;;
esac
exit $s
